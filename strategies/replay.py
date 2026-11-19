"""Runs the strategies over stored candles, as they would have run live,
and turns what they find into ideas (or blocked candidates, with the reason).
Reads the candle store only; never contacts IG; places nothing.

The week is replayed from its open, exactly as the analyser does (so the
market state at each moment is the one the service would have had). At each
5-minute candle:
  * "the current state" is the analyser's state after the previous finished
    candle (the state the strategy would see while this candle forms);
  * each strategy is given the candle; when its entry price is reached, the
    candidate is checked (strategies/common.py: switch, state, direction rule);
  * the first build's bounce (Bollinger bounce 5m), the range trade and the level reversal run their OWN
    rejection watcher with only the rules of design 3.3, 3.4 and 3.6 (design_only); the analyser's watcher is not
    changed;
  * the hourly-pierce Bollinger bounce keeps its own hourly chart (prices/hourly_chart.py), built from the same
    5-minute candles, the warm-up candles included;
  * the session strategies (the Asian range breakout, the session sweep and the
    New York open reversal) keep their own UK-day ranges from the same candles,
    the warm-up candles included.
With stored candles there are no ticks, so an entry is shown at the start of
the candle it was reached in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import Any

from analyser.indicators import last_candles
from analyser.market_state import MemoStore, StateTracker
from analyser.states import CONSOLIDATION, NONE
from config.pairs import check_same_pair
from levels.current import build
from levels.rules import PIVOT
from prices.indicators import Band, ema
from prices.calendar import MarketHours
from prices.store import CandleStore
from rejection.watch import RejectionWatcher
from strategies.bollinger_bounce.strategy import BollingerBounce
from strategies.bollinger_bounce_5m.strategy import candidates as bounce_5m_candidates
from strategies.common import Idea, check
from strategies.ema_pullback.strategy import EmaPullback, HourlyTrendReader
from strategies.range_trade.strategy import candidates as range_candidates
from strategies.slow_grind.strategy import SlowGrind
from strategies.breakout.strategy import Breakout
from strategies.level_reversal.strategy import LevelReversal
from strategies.asian_range_breakout.strategy import AsianRangeBreakout
from strategies.session_sweep.strategy import SessionSweep
from strategies.new_york_open_reversal.strategy import NewYorkOpenReversal

@dataclass
class Replay:
    ideas: list[Idea]
    notes: dict = field(default_factory=dict)                 # strategy -> [(time, direction, text)]
    watcher: Any = None                                       # the strategies' rejection watcher
    states: dict = field(default_factory=dict)                # candle start -> state after that candle


def fork(strategy: Any) -> Any:
    """A copy of a strategy to try a candle on without changing it: its waiting setups are copied; the settings,
    the hourly trend and the finished candles (which never change) are shared."""
    import copy
    from collections import deque
    if hasattr(strategy, "fork"):
        return strategy.fork()
    memo = {id(v): v for v in vars(strategy).values() if not isinstance(v, (list, dict, deque, set))}
    return copy.deepcopy(strategy, memo)


def with_room_to_level(settings: Any, cands: list, levels: Any) -> None:
    """ROOM_TO_LEVEL (owner, approved 19 November 2026): each breakout and Asian range breakout candidate gets the
    nearest daily pivot, R1-R3 or S1-S3 ahead of its entry, from the levels of the candle it opens on (as they stand
    at that candle's start). Recorded whatever the switch; it refuses only while the switch is on."""
    from decimal import Decimal
    from strategies.common import room_to_level_context
    ppp = Decimal(settings.market.points_per_pip)
    for cand in cands:
        cand.context.update(room_to_level_context(cand.strategy, cand.direction, cand.entry_price, levels, ppp))


def _session_candle(strat: Any, c: Any, fast: dict, slow: dict) -> list:
    """A session strategy's candle; the Asian range breakout also gets the 5-minute 8 and 21 EMAs after it (its
    pullback entry, PULLBACK_ENTRY; owner, 19 November 2026)."""
    if isinstance(strat, AsianRangeBreakout):
        return strat.on_candle(c, fast.get(c.start), slow.get(c.start))
    return strat.on_candle(c)


class StrategyRunner:
    """The strategies one finished 5-minute candle at a time, exactly as the replay below runs them (the replay
    is built on it) and as the live service runs them. Give it a StateTracker; after the tracker has taken new
    candles, step() runs the strategies on each of them and returns their ideas (checked: switch, state,
    direction rule), with the candle each came from. A new week starts everything again from its open.
    `hourly_end`: build the hourly trend reader once from the hourly candles up to it (a replay); otherwise it
    is read again for each candle (live).

    `store`: the candle store. Like the analyser (StateTracker.advance), every step() and peek() reads it afresh
    through a new MemoStore, so the strategies always see the latest candles and levels: never a copy kept from
    an earlier call (owner, 11 November 2026: the live strategies had kept the store as it was at start-up, so
    after a restart they never saw a new day's file, nor new candles in a day's file already read)."""

    def __init__(self, settings: Any, store: Any, tracker: Any, hourly_end: datetime | None = None):
        self.s, self.store, self.tracker, self.hourly_end = settings, store, tracker, hourly_end
        self.memo = MemoStore(store)                        # this call's view of the store (renewed every call)
        self.hours = MarketHours(settings.market_hours)
        self.week_open = None
        self.done = 0

    def _fresh(self) -> None:
        """A new view of the candle store for this call, as the analyser takes for each of its calls."""
        self.memo = MemoStore(self.store)

    def _new_week(self) -> None:
        s = self.s
        self.week_open = self.tracker.week_open
        self.warm = last_candles(self.memo, "5m", self.week_open, s.market_states.indicator_warm_up_candles)
        self.week: list = []
        self.done = 0
        self.pivots: dict = {}
        self.grind = SlowGrind(s)
        self.pullback = EmaPullback(s, self._hourly(self.hourly_end or self.week_open))
        self.watcher = RejectionWatcher(s, design_only=True)
        self.breakout = Breakout(s)
        self.reversal = LevelReversal(s)
        self.bounce = BollingerBounce(s)
        self.bounce.warm(self.warm)
        self.sessions = [AsianRangeBreakout(s), SessionSweep(s), NewYorkOpenReversal(s)]
        for x in self.sessions:
            x.warm(self.warm)

    def _hourly(self, end: datetime) -> HourlyTrendReader:
        return HourlyTrendReader(self.s, last_candles(self.memo, "1h", end, self.s.ema_pullback.hourly_history_candles))

    def state_after(self, i: int):
        """The analyser's state after week candle i (before the week's first candle: consolidation)."""
        t = self.week[i].start if i >= 0 else None
        before = [ch for ch in self.tracker.changes if t is not None and ch.time <= t]
        return (SimpleNamespace(state=before[-1].state, direction=before[-1].direction, trend_type=before[-1].trend_type)
                if before else SimpleNamespace(state=CONSOLIDATION, direction=NONE, trend_type=None))

    def pivot_at(self, t: datetime, keep: bool = True):
        """The pivot at t. Kept for a finished candle (step); the live check (keep=False) only reads one already
        kept, so a pivot worked out before that candle's data was all stored is never kept."""
        if t in self.pivots:
            return self.pivots[t]
        got = [lv.price for lv in build(self.s, self.memo, t).levels if lv.type == PIVOT]
        p = got[0] if got else None
        if keep:
            self.pivots[t] = p
        return p

    def peek(self, partial: Any, levels: Any = None) -> list[Idea]:
        """The live check (design 3: a trade opens as soon as the live price reaches its trigger): the strategies'
        COPIES are given the 5-minute candle forming now, as far as it has gone (`partial`), exactly as step()
        gives them a finished one; the ideas whose entry price it has reached are returned (checked, as at
        entry: the state after the last finished candle). Nothing in the strategies changes. `levels`: the levels
        for the forming candle (worked out here if not given)."""
        s, side = self.s, self.s.chart.price
        if self.week_open is None or self.week_open != self.tracker.week_open or not self.week:
            return []
        if partial.start <= self.week[-1].start:
            return []
        if self.waiting_for_finished_candle(partial.start):
            return []
        self._fresh()
        allc = self.warm + self.week + [partial]
        sg_ema = ema(allc, side, s.slow_grind.ema_periods)
        fast, slow = ema(allc, side, s.ema_pullback.fast_ema_periods), ema(allc, side, s.ema_pullback.slow_ema_periods)
        ema100 = ema(self.warm + self.week, side, s.analyser.direction_ema_periods)
        f = self.tracker.history[-1][0]                     # the band as it stood at the last finished candle
        band = Band(partial.start, f.middle, f.upper, f.lower) if f.upper is not None else None
        watcher = fork(self.watcher)
        breakout, grind, pullback, reversal = fork(self.breakout), fork(self.grind), fork(self.pullback), fork(self.reversal)
        bounce = fork(self.bounce)
        sessions = [fork(x) for x in self.sessions]
        lv = levels if levels is not None else build(s, self.memo, partial.start)
        events = watcher.on_candle(partial, band, lv)
        cands = (breakout.on_candle(partial, None, None, fast.get(partial.start), slow.get(partial.start))
                 + grind.on_candle(partial, sg_ema.get(partial.start))
                 + pullback.on_candle(partial, fast.get(partial.start), slow.get(partial.start))
                 + bounce.on_candle(partial) + bounce_5m_candidates(watcher, events)
                 + range_candidates(watcher, events)
                 + reversal.on_candle(partial, watcher, events)
                 + [x for strat in sessions for x in _session_candle(strat, partial, fast, slow)])
        st = self.state_after(len(self.week) - 1)
        e100 = ema100.get(self.week[-1].start)
        with_room_to_level(s, cands, lv)
        return [check(s, s.market.pair, cand, st, self.pivot_at(partial.start, keep=False), e100) for cand in cands]

    def waiting_for_finished_candle(self, start: datetime) -> bool:
        """True while the 5-minute candle before the forming one (starting at `start`) is not yet taken: in the
        market's hours and newer than the last finished candle the strategies have. At each candle's turn the live
        prices of the new candle arrive before IG's finished candle is stored (18 November 2026: a breakout idea at
        15:45:00, before the 15:40 candle was stored at 15:45:00); the strategies' copies would otherwise be given
        the new candle straight after the one before last, missing a candle: a setup already triggered or cancelled
        in it could trigger again. The live check waits (only seconds, normally) until that candle is stored and
        taken; nothing in the strategies' rules changes. A candle IG never sends pauses the live check for one
        candle; the candle-close step still sends what it finds then, as for a gap in the live prices."""
        prev = start - timedelta(minutes=5)
        return self.week[-1].start < prev and self.hours.is_open(prev)

    def step(self) -> list[tuple[Any, Idea]]:
        """Run the strategies on every candle the tracker has taken since the last call: [(candle, idea)]."""
        s, side = self.s, self.s.chart.price
        self._fresh()
        if self.tracker.week_open != self.week_open:
            self._new_week()
        hist = self.tracker.history
        out: list[tuple[Any, Idea]] = []
        for i in range(self.done, len(hist)):
            f = hist[i][0]
            c = f.candle
            self.week.append(c)
            allc = self.warm + self.week
            sg_ema = ema(allc, side, s.slow_grind.ema_periods)
            fast, slow = ema(allc, side, s.ema_pullback.fast_ema_periods), ema(allc, side, s.ema_pullback.slow_ema_periods)
            ema100 = ema(allc, side, s.analyser.direction_ema_periods)
            if self.hourly_end is None:
                self.pullback.hourly = self._hourly(c.end)
            changes = self.tracker.changes
            change_at = {ch.time: (k, ch) for k, ch in enumerate(changes)}
            band = Band(c.start, f.middle, f.upper, f.lower) if f.upper is not None else None
            lv = build(s, self.memo, c.start)
            events = self.watcher.on_candle(c, band, lv)
            kc = change_at.get(c.start)
            since = changes[kc[0] - 1].time if kc and kc[0] > 0 else None
            cands = (self.breakout.on_candle(c, kc[1] if kc else None, since, fast.get(c.start), slow.get(c.start))
                     + self.grind.on_candle(c, sg_ema.get(c.start))
                     + self.pullback.on_candle(c, fast.get(c.start), slow.get(c.start))
                     + self.bounce.on_candle(c) + bounce_5m_candidates(self.watcher, events)
                     + range_candidates(self.watcher, events)
                     + self.reversal.on_candle(c, self.watcher, events)
                     + [x for strat in self.sessions for x in _session_candle(strat, c, fast, slow)])
            if cands:
                st = self.state_after(i - 1)
                e100 = ema100.get(self.week[i - 1].start) if i > 0 else None
                for cand in cands:
                    with_room_to_level(s, [cand], lv)
                    out.append((c, check(s, s.market.pair, cand, st, self.pivot_at(c.start), e100)))
        self.done = len(hist)
        return out


def run(settings: Any, store: CandleStore, start: datetime, end: datetime) -> Replay:
    check_same_pair(settings, store)
    memo = MemoStore(store)
    tracker = StateTracker(settings, memo)
    tracker.replay(end)
    if not tracker.history:
        return Replay([])
    runner = StrategyRunner(settings, memo, tracker, hourly_end=end)
    ideas = [idea for c, idea in runner.step() if start <= c.start < end]
    out = Replay(ideas, states={c.start: runner.state_after(i) for i, c in enumerate(runner.week)})
    out.notes = {"slow grind": runner.grind.notes, "EMA pullback": runner.pullback.notes, "breakout": runner.breakout.notes,
                 "Bollinger bounce": runner.bounce.notes, "Asian range breakout": runner.sessions[0].notes,
                 "session sweep": runner.sessions[1].notes, "New York open reversal": runner.sessions[2].notes}
    out.watcher = runner.watcher
    return out


def replay(settings: Any, store: CandleStore, start: datetime, end: datetime) -> list[Idea]:
    return run(settings, store, start, end).ideas
