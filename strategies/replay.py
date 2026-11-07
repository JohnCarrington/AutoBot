"""Runs the four strategies over stored candles, as they would have run live,
and turns what they find into ideas (or blocked candidates, with the reason).
Reads the candle store only; never contacts IG; places nothing.

The week is replayed from its open, exactly as the analyser does (so the
market state at each moment is the one the service would have had). At each
5-minute candle:
  * "the current state" is the analyser's state after the previous finished
    candle (the state the strategy would see while this candle forms);
  * each strategy is given the candle; when its entry price is reached, the
    candidate is checked (strategies/common.py: switch, state, direction rule);
  * the bounce and range trade run their OWN rejection watcher with only the
    rules of design 3.3 and 3.4 (design_only); the analyser's watcher is not
    changed.
With stored candles there are no ticks, so an entry is shown at the start of
the candle it was reached in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from types import SimpleNamespace
from typing import Any

from analyser.indicators import last_candles
from analyser.market_state import MemoStore, StateTracker
from analyser.states import CONSOLIDATION, NONE
from config.pairs import check_same_pair
from levels.current import build
from levels.rules import PIVOT
from prices.indicators import Band, ema
from prices.store import CandleStore
from rejection.watch import RejectionWatcher
from strategies.bollinger_bounce.strategy import candidates as bounce_candidates
from strategies.common import Idea, check
from strategies.ema_pullback.strategy import EmaPullback, HourlyTrendReader
from strategies.range_trade.strategy import candidates as range_candidates
from strategies.slow_grind.strategy import SlowGrind

@dataclass
class Replay:
    ideas: list[Idea]
    notes: dict = field(default_factory=dict)                 # strategy -> [(time, direction, text)]
    watcher: Any = None                                       # the strategies' rejection watcher
    states: dict = field(default_factory=dict)                # candle start -> state after that candle


def run(settings: Any, store: CandleStore, start: datetime, end: datetime) -> Replay:
    check_same_pair(settings, store)
    memo = MemoStore(store)
    tracker = StateTracker(settings, memo)
    tracker.replay(end)
    hist = tracker.history
    if not hist:
        return Replay([])
    side = settings.chart.price
    week = [h[0].candle for h in hist]
    warm = last_candles(memo, "5m", tracker.week_open, settings.market_states.indicator_warm_up_candles)
    allc = warm + week
    sg, ep = settings.slow_grind, settings.ema_pullback
    sg_ema = ema(allc, side, sg.ema_periods)
    fast, slow = ema(allc, side, ep.fast_ema_periods), ema(allc, side, ep.slow_ema_periods)
    ema100 = ema(allc, side, settings.analyser.direction_ema_periods)
    hourly = HourlyTrendReader(settings, last_candles(memo, "1h", end, ep.hourly_history_candles))
    changes = tracker.changes
    index = {c.start: i for i, c in enumerate(week)}
    pivots: dict = {}

    def state_after(i: int):
        """The analyser's state after week candle i (before the week's first candle: consolidation)."""
        t = week[i].start if i >= 0 else None
        before = [ch for ch in changes if t is not None and ch.time <= t]
        return (SimpleNamespace(state=before[-1].state, direction=before[-1].direction, trend_type=before[-1].trend_type)
                if before else SimpleNamespace(state=CONSOLIDATION, direction=NONE, trend_type=None))

    def pivot_at(t):
        if t not in pivots:
            got = [lv.price for lv in build(settings, memo, t).levels if lv.type == PIVOT]
            pivots[t] = got[0] if got else None
        return pivots[t]

    out = Replay([], states={c.start: state_after(i) for i, c in enumerate(week)})

    grind = SlowGrind(settings)
    pullback = EmaPullback(settings, hourly)
    watcher = RejectionWatcher(settings, design_only=True)
    for i, (f, _state, _direction, _events, _moved, _sp) in enumerate(hist):
        c = f.candle
        band = Band(c.start, f.middle, f.upper, f.lower) if f.upper is not None else None
        events = watcher.on_candle(c, band, build(settings, memo, c.start))
        cands = (grind.on_candle(c, sg_ema.get(c.start))
                 + pullback.on_candle(c, fast.get(c.start), slow.get(c.start))
                 + bounce_candidates(watcher, events) + range_candidates(watcher, events))
        if cands and start <= c.start < end:
            st = state_after(i - 1)
            e100 = ema100.get(week[i - 1].start) if i > 0 else None
            for cand in cands:
                out.ideas.append(check(settings, settings.market.pair, cand, st, pivot_at(c.start), e100))
    out.notes = {"slow grind": grind.notes, "EMA pullback": pullback.notes}
    out.watcher = watcher
    return out


def replay(settings: Any, store: CandleStore, start: datetime, end: datetime) -> list[Idea]:
    return run(settings, store, start, end).ideas
