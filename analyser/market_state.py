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
and the current state is written to current.json.

Reads the candle store only; never contacts IG.
"""

from __future__ import annotations

import json
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
        self.folder = Path(settings.market_states.folder) / settings.market.pair

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
        memo = MemoStore(self.store)
        warm, week = self._candles(memo, week_open, as_of)
        if len(week) > self.done:
            feats = compute(warm + week, self.s)[len(warm):]
            for c, f in zip(week[self.done:], feats[self.done:]):
                self._step(memo, f)
            self.done = len(week)
        if self.record:
            self._write()
        return self.machine.now

    def _step(self, store: CandleStore, f: Features) -> StateChange | None:
        from prices.indicators import Band
        c = f.candle
        band = Band(c.start, f.middle, f.upper, f.lower) if f.upper is not None else None
        levels = build(self.s, store, c.start)
        events = self.watcher.on_candle(c, band, levels)
        return self.machine.step(f, events, lambda i: self.watcher.setups[i - 1])

    @property
    def changes(self) -> list[StateChange]:
        return list(self.machine.changes) if self.machine else []

    # ---- records ---------------------------------------------------------------------------

    def recorded(self) -> list[dict]:
        p = self.folder / JOURNAL
        if not p.exists():
            return []
        return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]

    def _write(self) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        have = {(r["time_utc"], r["state"], r["direction"], r.get("trend_type")) for r in self.recorded()}
        new = [ch.as_dict() for ch in self.changes]
        new = [r for r in new if (r["time_utc"], r["state"], r["direction"], r.get("trend_type")) not in have]
        if new:
            with (self.folder / JOURNAL).open("a") as fh:
                for r in new:
                    fh.write(json.dumps(r) + "\n")
                fh.flush()
        now = self.machine.now
        safe_write(self.folder / CURRENT, (json.dumps({
            "state": now.state, "direction": now.direction, "trend_type": now.trend_type,
            "since_utc": now.since.strftime("%Y-%m-%dT%H:%M:%SZ"), "evidence": now.evidence,
            "strategies_allowed": list(now.strategies_allowed)}, indent=1) + "\n").encode())
