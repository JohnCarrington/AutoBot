"""Runs the five market states over the stored candles, for one pair.

START-UP REPLAY: the state machine always starts at the trading week's open
(Sunday 21:00 UK), and its indicators always start from the same fixed point
(market_states.indicator_warm_up_candles 5-minute candles before that open).
So replaying the week up to now gives exactly the state, and exactly the list
of state changes, that a run which never stopped would have (a test checks it).

LIVE: advance(now) takes each new finished 5-minute candle in turn.

RECORDS: with record=True, every state change is appended to
<market_states.folder>/<PAIR>/state_changes.jsonl (time, state, direction,
type of trend, reason and evidence), each change once, even after a restart,
and the current state is written to current.json. The journal stays the live
record in time order: a restart's replay adds only changes newer than its last
line; where the replay calls earlier candles differently (a rule changed), the
differences go to replay_differences_<date>.jsonl, never into the journal.

PROVENANCE (owner's investigation brief, 19 November 2026): every line written from now on says how it was made
and when it was written. "time_utc" stays the event time (the start of the candle the change came from);
"recorded_utc" is the moment the line was written; "run_started_utc" is when that run of the analyser started;
"provenance" is one of:
  * LIVE_DECISION: made by the running analyser from a newly finished candle (not the start-up replay);
  * HISTORICAL_REPLAY: made by the start-up replay for a time the last run was covering live (or when it cannot
    be shown that it was not): worked out afterwards, possibly under newer rules; the live bot did NOT act on it;
  * RECONSTRUCTED: made by the start-up replay for a time after the last run's last live candle (the service
    was stopped then): no live decision existed, so it is filled in from the stored candles.
A line without "provenance" (written before 19 November 2026) is UNKNOWN_LEGACY (provenance_of): never assumed
live. Existing lines are never rewritten or relabelled. current.json carries "live_through_utc", the end of the
last candle taken live, so the next start-up can tell HISTORICAL_REPLAY from RECONSTRUCTED.

Reads the candle store only; never contacts IG.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from analyser.features import Features, compute
from analyser.indicators import last_candles
from analyser.states import MarketState, StateChange, StateMachine
from config.pairs import check_same_pair
from housekeeping.files import safe_write
from levels.current import build
from prices.calendar import MarketHours
from prices.store import CandleStore
from rejection.watch import RejectionWatcher

UTC = timezone.utc
JOURNAL = "state_changes.jsonl"
CURRENT = "current.json"
DIFFERENCES = "replay_differences_{date}.jsonl"
LIVE_DECISION, HISTORICAL_REPLAY, RECONSTRUCTED, UNKNOWN_LEGACY = (
    "LIVE_DECISION", "HISTORICAL_REPLAY", "RECONSTRUCTED", "UNKNOWN_LEGACY")
REPLAY_ONLY = "replayed, not in the live record"
RECORD_ONLY = "in the live record, not replayed"


class MemoStore(CandleStore):
    """The same store, remembering each day's file once read (a stored candle
    never changes; a new one only arrives in a later call, which starts afresh)."""

    def __init__(self, store: CandleStore):
        super().__init__(store.folder, store.compress_after_days, warn=store.warn)
        self._day: dict = {}
        self._days: dict = {}

    def read_day(self, tf, day):
        key = (tf, day)
        if key not in self._day:
            self._day[key] = super().read_day(tf, day)
        return list(self._day[key])

    def days(self, tf):
        if tf not in self._days:
            self._days[tf] = super().days(tf)
        return list(self._days[tf])


class StateTracker:
    def __init__(self, settings: Any, store: CandleStore, record: bool = False):
        check_same_pair(settings, store)
        self.s, self.store, self.record = settings, store, record
        self.hours = MarketHours(settings.market_hours)
        self.week_open: datetime | None = None
        self.machine: StateMachine | None = None
        self.watcher: RejectionWatcher | None = None
        self.done = 0                     # candles of this week already stepped
        self.history: list = []           # (features, state after the candle) for each candle stepped
        # for each candle stepped, as history: {"trend_start", "hourly", "position", "break"} (owner, 18 November
        # 2026: the analyser control, design 2.10; "hourly", "position" and "break" (the standing 5-minute break of
        # the hourly range after the candle's close) only while ANALYSER_USES_HOURLY is on)
        self.extras: list = []
        self.hourly_reader = None
        self.brk = None                  # the standing 5-minute break of the hourly range (analyser.hourly_read)
        self.folder = Path(settings.market_states.folder) / settings.market.pair
        self.clock = lambda: datetime.now(UTC)  # the wall clock, for "recorded_utc" (a test can set it)
        self.run_started: datetime | None = None
        self.live_from = 0                # changes before this index came from the start-up replay
        self.live_through: datetime | None = None     # end of the last candle taken live in this run
        self.prior_live_through: str | None = None    # the last run's, read from current.json at start-up

    # ---- the week and its candles ----------------------------------------------------------

    def _week_of(self, as_of: datetime) -> datetime:
        return self.hours.session(as_of)[0]

    def _candles(self, store: CandleStore, week_open: datetime, as_of: datetime):
        warm = last_candles(store, "5m", week_open, self.s.market_states.indicator_warm_up_candles)
        week = [c for c in store.read_range("5m", week_open, as_of) if c.end <= as_of]
        return warm, week

    # ---- running ---------------------------------------------------------------------------

    def replay(self, as_of: datetime) -> MarketState:
        """Start-up: run the week from its open up to as_of."""
        self.week_open = None
        self.run_started = None                  # a start-up replay: its changes are not live decisions
        return self.advance(as_of)

    def advance(self, as_of: datetime) -> MarketState:
        """Take every finished 5-minute candle up to as_of not yet taken."""
        as_of = as_of.astimezone(UTC)
        week_open = self._week_of(as_of)
        if week_open != self.week_open:          # a new week (or the first call): start fresh
            self.week_open = week_open
            self.machine = StateMachine(self.s, week_open)
            self.watcher = RejectionWatcher(self.s)
            self.done = 0
            self.history = []
            self.extras = []
            self.brk = None
            self.live_from = 0                   # a new week while running: its changes are all live
        memo = MemoStore(self.store)
        warm, week = self._candles(memo, week_open, as_of)
        from analyser.states import switch_on
        if switch_on(self.s, "analyser_uses_hourly"):
            from analyser.hourly_read import HourlyReader
            self.hourly_reader = HourlyReader(self.s, last_candles(memo, "1h", as_of,
                                                                   self.s.hourly_read.history_candles))
        start_up = self.run_started is None
        if start_up:                              # this run's first call: the start-up replay
            self.run_started = self.clock()
            self.prior_live_through = self._prior_live_through() if self.record else None
        if len(week) > self.done:
            feats = compute(warm + week, self.s)[len(warm):]
            for c, f in zip(week[self.done:], feats[self.done:]):
                self._step(memo, f)
            self.done = len(week)
            if not start_up:
                self.live_through = week[-1].end
        if start_up:
            self.live_from = len(self.changes)
        if self.record:
            self._write(as_of)
        return self.machine.now

    def _prior_live_through(self) -> str | None:
        try:
            v = json.loads((self.folder / CURRENT).read_text()).get("live_through_utc")
            return v if isinstance(v, str) else None
        except (OSError, ValueError, AttributeError):
            return None

    def provenance(self, k: int, r: dict) -> str:
        """How the k-th change of this week (r: its as_dict) was made, in this run."""
        if k >= self.live_from:
            return LIVE_DECISION
        if self.prior_live_through is not None and r["time_utc"] >= self.prior_live_through:
            return RECONSTRUCTED
        return HISTORICAL_REPLAY

    def _step(self, store: CandleStore, f: Features) -> StateChange | None:
        from prices.indicators import Band
        c = f.candle
        band = Band(c.start, f.middle, f.upper, f.lower) if f.upper is not None else None
        levels = build(self.s, store, c.start)
        events = self.watcher.on_candle(c, band, levels)
        mc = self.machine
        hr = pos = None
        if self.hourly_reader is not None:                 # ANALYSER_USES_HOURLY (design 2.10)
            from analyser.states import hourly_position
            from analyser.hourly_read import next_break, with_break
            hr = self.hourly_reader.at(c.start)            # the read after the last hourly candle finished by then
            pos = hourly_position(self.s, hr, f.c)
            # a 5-minute close beyond the hourly range counts as the range breaking (owner, 18 November 2026):
            # decided on this candle's close, for the analyser on this candle and the strategies after it
            self.brk = next_break(self.s, hr, self.brk, c.start, f.c)
        mc.hourly, mc.position = (with_break(hr, self.brk) if hr is not None else None), pos
        ch = mc.step(f, events, lambda i: self.watcher.setups[i - 1])
        moved = (mc._pips(mc.extreme, mc.start_price) if mc.extreme is not None and mc.start_price is not None
                 else None)
        self.history.append((f, mc.now.state, mc.now.direction, events, moved, mc.start_price))
        self.extras.append({"trend_start": mc.trend_start, "hourly": hr, "position": pos,
                            "break": self.brk if self.hourly_reader is not None else None})
        return ch

    @property
    def changes(self) -> list[StateChange]:
        return list(self.machine.changes) if self.machine else []

    # ---- records ---------------------------------------------------------------------------

    def recorded(self) -> list[dict]:
        p = self.folder / JOURNAL
        if not p.exists():
            return []
        return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]

    def _write(self, as_of: datetime) -> None:
        """The journal is the live record, kept in time order: only changes newer than its last line are appended.
        A change at or before that time which the record does not have (a restart's replay calling the week
        differently, after a rule changed) goes to replay_differences_<date of the restart>.jsonl instead, with
        each recorded change of the replayed span that the replay no longer makes; each difference once."""
        self.folder.mkdir(parents=True, exist_ok=True)
        rows = self.recorded()
        have = {_key(r) for r in rows}
        last = max((r["time_utc"] for r in rows), default="")
        made = [ch.as_dict() for ch in self.changes]
        new = [(k, r) for k, r in enumerate(made) if _key(r) not in have and r["time_utc"] > last]
        if new:
            recorded = _utc(self.clock())
            with (self.folder / JOURNAL).open("a") as fh:
                for k, r in new:
                    fh.write(json.dumps({**r, "provenance": self.provenance(k, r), "recorded_utc": recorded,
                                         "run_started_utc": _utc(self.run_started)}) + "\n")
                fh.flush()
        self._differences(as_of, rows, made, last)
        now = self.machine.now
        safe_write(self.folder / CURRENT, (json.dumps({
            "state": now.state, "direction": now.direction, "trend_type": now.trend_type,
            "since_utc": now.since.strftime("%Y-%m-%dT%H:%M:%SZ"), "evidence": now.evidence,
            "strategies_allowed": list(now.strategies_allowed),
            "live_through_utc": _utc(self.live_through) if self.live_through else self.prior_live_through,
            **({"hourly_position": self.extras[-1]["position"]} if self.extras and self.extras[-1]["position"]
               else {})}, indent=1) + "\n").encode())

    def _differences(self, as_of: datetime, rows: list[dict], made: list[dict], last: str) -> None:
        week_from = self.week_open.strftime("%Y-%m-%dT%H:%M:%SZ")
        made_keys = {_key(r) for r in made}
        rec_keys = {_key(r) for r in rows}
        diff = [{"difference": REPLAY_ONLY, **r} for r in made if r["time_utc"] <= last and _key(r) not in rec_keys]
        diff += [{"difference": RECORD_ONLY, **r} for r in rows
                 if week_from <= r["time_utc"] <= last and _key(r) not in made_keys]
        if not diff:
            return
        seen = set()
        for p in self.folder.glob(DIFFERENCES.format(date="*")):
            seen |= {(x.get("difference"), *_key(x)) for x in
                     (json.loads(y) for y in p.read_text().splitlines() if y.strip())}
        diff = sorted((d for d in diff if (d["difference"], *_key(d)) not in seen),
                      key=lambda d: (d["time_utc"], d["difference"]))
        if not diff:
            return
        p = self.folder / DIFFERENCES.format(date=as_of.astimezone(UTC).strftime("%Y-%m-%d"))
        with p.open("a") as fh:
            for d in diff:
                fh.write(json.dumps(d) + "\n")
        logging.getLogger("autobot.analyser").warning(
            "[%s] The week's replay differs from the live record in %d state change(s) at or before %s (a rule "
            "changed?); not added to %s, written to %s.", self.s.market.pair, len(diff), last, JOURNAL, p)


def _utc(t: datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def provenance_of(r: dict) -> str:
    """A journal line's provenance: UNKNOWN_LEGACY for a line written before provenance was recorded (never
    assumed to be a live decision)."""
    p = r.get("provenance")
    return p if p in (LIVE_DECISION, HISTORICAL_REPLAY, RECONSTRUCTED) else UNKNOWN_LEGACY


def _key(r: dict) -> tuple:
    return (r["time_utc"], r["state"], r["direction"], r.get("trend_type"))


class StatesUpdater:
    """Called by the price service at start-up and after each new 5-minute
    candle. The first call replays the week from its open (start-up); each
    later call takes the new candles. Every state change is recorded (and
    written to the log). It can never stop the price service: a problem is
    written as a warning."""

    def __init__(self, settings: Any, store: CandleStore, warn: Any = None):
        import logging
        self.log = logging.getLogger("autobot.analyser")
        self.settings, self.store = settings, store
        self.tracker: StateTracker | None = None
        self.pair = settings.market.pair
        self.warn = warn or self.log.warning
        self.started = False

    def __call__(self, now: datetime) -> None:
        try:
            if self.tracker is None:
                self.tracker = StateTracker(self.settings, self.store, record=True)
            before = len(self.tracker.changes) if self.started else 0
            first = not self.started
            state = self.tracker.advance(now)
            self.started = True
        except Exception as e:      # never stop the price service
            self.warn(f"[{self.pair}] Market state not updated ({type(e).__name__}: {e}).")
            return
        kind = f", {state.trend_type}" if state.trend_type else ""
        if first:
            self.log.info("[%s] Market states replayed from the week's open (%s candles): %s (%s%s) since %s; "
                          "%d state change(s) this week, recorded in %s.", self.pair, self.tracker.done, state.state,
                          state.direction, kind, state.since.strftime("%Y-%m-%d %H:%M UTC"),
                          len(self.tracker.changes), self.tracker.folder / JOURNAL)
            return
        for ch in self.tracker.changes[before:]:
            self.log.info("[%s] Market state: %s", self.pair, ch.line())

