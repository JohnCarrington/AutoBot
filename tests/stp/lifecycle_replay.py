"""Deterministic offline replay of STP's lifecycle over the recorded 25-27 November 2026 (Phase 2, owner's approval of
27 November 2026). Read only; IG is never contacted; every file goes to a temporary folder.

  * candles: tests/stp/fixtures/lifecycle_20261127/candles (the production store as it stood at 14:15 UTC on 27 Nov,
    so the 27 Nov 12:00-12:10 five-minute candles are missing, as production saw them). A bigger candle becomes
    visible when the price service built it: a complete one at its end; one missing parts once a later 5-minute candle
    was stored or 300 s had passed (prices/builder.py), so the 27 Nov 12:00 hour appears at 13:05, as it did;
  * plans: STP's own plans (planner.assess.plan_at, unchanged) at every analysis time production recorded, recomputed
    from the same candles (plans.json.gz; 0 differences from the journal's analysis summaries);
  * start: 25 Nov 09:15:03 UTC, the first run of the opportunity tracker in production, which took over the single
    tracker's STP-GBPUSD-20261125-0400-27 (initial_state_20261125_0915.json); ids are numbered on from it, as in
    production;
  * the tracker runs after each 5-minute candle: at production's own recorded analysis time where it re-planned
    (seconds after the hour), otherwise 3 seconds after the candle, as the price service starts it;
  * each STP-authorised trade production recorded (stp_trades.json) is offered again at its own idea time: the STP
    check (stp/authorise.py) against the tracker's file as it stood then, then rule 11 (safety/rules.py) against the
    keys of the trades the replay opened before it. Only those two decide here; every other rule passed in production
    for these trades.
"""

from __future__ import annotations

import gzip
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

UTC = timezone.utc
FIX = Path(__file__).resolve().parent / "fixtures" / "lifecycle_20261127"
START = datetime(2026, 11, 25, 9, 15, tzinfo=UTC)


def plans() -> dict:
    return json.loads(gzip.decompress((FIX / "plans.json.gz").read_bytes()))["plans"]


def trades() -> list[dict]:
    return json.loads((FIX / "stp_trades.json").read_text())


def iso(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse(x: str) -> datetime:
    return datetime.fromisoformat(x.replace("Z", "+00:00"))


class AvailStore:
    """The frozen store as the price service had it at self.t (see the module text)."""

    def __init__(self, base: Any, extra: dict | None = None):
        self.base, self.t = base, START
        self.folder = base.folder
        self.extra = extra or {}                      # tf -> {start: candle}: test-only additions (synthetic)
        self._fives = None

    def _five_ends(self) -> list:
        if self._fives is None:
            days = self.base.days("5m")
            first = datetime.combine(days[0], datetime.min.time(), UTC)
            self._fives = sorted(c.end for c in self.base.read_range("5m", first, datetime(2027, 1, 1, tzinfo=UTC)))
        return self._fives

    def visible_at(self, c: Any) -> datetime:
        if c.timeframe == "5m" or c.expected_parts == 0 or c.parts >= c.expected_parts:
            return c.end
        later = next((e for e in self._five_ends() if e - timedelta(minutes=5) >= c.end), None)
        return min(c.end + timedelta(seconds=300), later) if later else c.end + timedelta(seconds=300)

    def _ok(self, c: Any) -> bool:
        return self.visible_at(c) <= self.t

    def read_range(self, tf: str, start: datetime, end: datetime) -> list:
        got = {c.start: c for c in self.base.read_range(tf, start, end)}
        for s_, c in self.extra.get(tf, {}).items():
            if start <= s_ < end:
                got[s_] = c
        return [c for _, c in sorted(got.items()) if self._ok(c)]

    def days(self, tf: str) -> list:
        return self.base.days(tf)

    def read_day(self, tf: str, day: Any) -> list:
        s_ = datetime.combine(day, datetime.min.time(), UTC)
        return self.read_range(tf, s_, s_ + timedelta(days=1))

    def get(self, tf: str, start: datetime) -> Any:
        c = self.extra.get(tf, {}).get(start) or self.base.get(tf, start)
        return c if c is not None and self._ok(c) else None

    def newest(self, tf: str) -> Any:
        cs = self.read_range(tf, self.t - timedelta(days=14), self.t + timedelta(seconds=1))
        return cs[-1] if cs else None


def fixture_store(extra: dict | None = None) -> AvailStore:
    from prices.store import CandleStore
    return AvailStore(CandleStore(FIX / "candles" / "GBPUSD", 10**6, warn=lambda m: None), extra)


class RecordedPlanner:
    """STP's recorded plan for the asked direction at the analysis time `now` (exactly as production analysed then)."""

    def __init__(self):
        self.p = plans()

    def __call__(self, settings: Any, store: Any, now: datetime, *a: Any, trade: str | None = None) -> Any:
        from tests.technical.test_planner import FakePlan
        at = self.p.get(iso(now))
        if at is None or trade not in at:
            raise AssertionError(f"no recorded plan for {trade} at {iso(now)}: the replay ran a re-plan production "
                                 f"did not")
        return FakePlan(json.loads(json.dumps(at[trade])))


def settings(folder: Path, **sw: bool) -> Any:
    from tests.stp.harness import live_settings
    s = live_settings(folder / "s", stp_opportunities=True, stp_bidirectional=True, stp_authorises_entries=True,
                      **sw)
    from tests.stp.harness import Over
    return Over(s, folder)


def start_state(s: Any) -> None:
    d = Path(s.planner.folder) / s.market.pair
    d.mkdir(parents=True, exist_ok=True)
    (d / "current.json").write_text((FIX / "initial_state_20261125_0915.json").read_text())


def acknowledge(s: Any) -> Callable[[dict, Any, datetime], None]:
    """What the order sender does once IG confirms a trade (orders/executions.py): the acknowledgement, with the STP
    context the authorisation gave the idea, executed at the idea's own time (production's fills came within a second).
    No price, size or result."""
    from orders.executions import ExecutionAcks

    def write(i: dict, v: Any, when: datetime) -> None:
        acks = ExecutionAcks(Path(s.orders.folder) / s.market.pair, lambda: when)
        t = SimpleNamespace(reference=i["reference"], deal_id="", strategy=i["strategy"], direction=i["direction"],
                            opened_at=when, stp={"opportunity": v.opportunity["id"], "lineage": v.lineage, "test": v.test,
                                                 "key": v.stp_key, "keys": list(v.keys)})
        acks.record(t, when, "replay: as IG's deal confirmation ACCEPTED")
    return write


def replay(s: Any, end: datetime, store: AvailStore | None = None, ideas: list[dict] | None = None,
           on_open: Callable[[dict, Any, datetime], None] | None = None, acks: bool = True) -> dict:
    """The tracker after every 5-minute candle from START to `end`, with the recorded STP trades' ideas offered at
    their own times. Returns the tracker's snapshots, its events and each idea's outcome."""
    from orders.sender import OrderSender
    from planner.opportunities import OpportunityKeeper
    from safety.rules import _one_signal
    from stp.authorise import authorise
    store = store or fixture_store()
    start_state(s)
    if on_open is None and acks:
        try:
            on_open = acknowledge(s)
        except ImportError:                     # the code before WP2 has no acknowledgements
            on_open = None
    planner = RecordedPlanner()
    folder = Path(s.planner.folder) / s.market.pair
    recorded = sorted(parse(k) for k in planner.p)
    runs, t = [], START
    while t <= end:
        exact = next((r for r in recorded if t <= r < t + timedelta(minutes=1)), None)
        runs.append(exact or t + timedelta(seconds=3))       # the recorded analysis time where production had one
        t += timedelta(minutes=5)
    ideas = sorted(ideas if ideas is not None else trades(), key=lambda x: x["idea_time"])
    queue = sorted([(r, "run", None) for r in runs] +
                   [(parse(i["idea_time"]), "idea", i) for i in ideas if parse(i["idea_time"]) <= end],
                   key=lambda x: (x[0], x[1] == "idea"))
    snaps: list[dict] = []
    opened: dict[str, Any] = {}
    outcomes = []
    for when, kind, i in queue:
        store.t = when
        if kind == "run":
            OpportunityKeeper(s, store, planner=planner).run(when)
            snaps.append(json.loads((folder / "current.json").read_text()))
            continue
        st = snaps[-1] if snaps else None
        idea = SimpleNamespace(strategy=i["strategy"], direction=i["direction"], time=when,
                               entry_price=Decimal(i["entry_price"]), steps=[],
                               context={"rejection_candle": i["rejection_candle"]} |
                                       ({"signal": i["signal"]} if i.get("signal") else {}))
        v = authorise(s, store, idea, when, SimpleNamespace(state_at=lambda t=None, st=st: st))
        out = {"reference": i["reference"], "idea_time": i["idea_time"], "stp_allowed": v.allowed,
               "reasons": list(v.reasons), "opportunity": (v.opportunity or {}).get("id"), "key": v.stp_key,
               "signal": v.signal, "lineage": getattr(v, "lineage", None), "test": getattr(v, "test", None)}
        if v.allowed:
            used = OrderSender.used_signals(SimpleNamespace(unresolved={}, trades=opened))
            r11 = _one_signal(SimpleNamespace(switches=SimpleNamespace(one_signal_one_trade=True)),
                              SimpleNamespace(context={"signal": v.signal}), used)
            out["rule_11"] = r11
            out["opened"] = not r11
            if not r11:
                opened[i["reference"]] = SimpleNamespace(signal=v.signal, strategy=i["strategy"])
                if on_open is not None:
                    on_open(i, v, when)
        else:
            out["opened"] = False
        outcomes.append(out)
    events = [json.loads(x) for x in (folder / "recommendations.jsonl").read_text().splitlines()]
    issued = {}
    for x in (folder / "issued.jsonl").read_text().splitlines():
        r = json.loads(x)
        issued[r["id"]] = (r["trade"], r["entry_zone"]["low"], r["entry_zone"]["high"])
    return {"snapshots": snaps, "events": events, "outcomes": outcomes, "store": store, "issued": issued}


def lifecycle(events: list[dict]) -> dict[str, list[tuple[str, str]]]:
    out: dict[str, list[tuple[str, str]]] = {}
    for e in events:
        if e.get("id"):
            out.setdefault(e["id"], []).append((e["time_utc"], e["event"]))
    return out


def ended(events: list[dict]) -> dict[str, dict]:
    return {e["id"]: e for e in events if e.get("id") and e["event"] in ("completed", "invalidated", "superseded")}
