"""Phase 2 WP3 functional regression on the REAL 27 November 2026 outage (owner's approval of 27 November 2026: PD-5).
The production store has no 5-minute candles 12:00, 12:05 and 12:10 (the deployment restart); the 12:00 hourly
candle was built at 13:05 from 9 of 12. IG's own records place price inside STP-GBPUSD-20261127-1200-57's zone
tolerance during the gap (the 12:01:27 entry at bid 13130.5; the owner's close at 12:05:11, IG level 13130.6).

The tracker starts from 1200-57 exactly as production published it at 12:00:03 (state_20261127_1200.json), with its
lineage from the historical lineage map, and runs on the frozen candles and STP's recorded plans to 14:10. No candle is
made up: the recovery part of PD-5 (C) on these real slots waits for IG's own candles (OP-1, the owner's Saturday
maintenance window); its mechanism is covered by TW3-04 to TW3-10. IG is never contacted."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.stp.lifecycle_replay import FIX, fixture_store, replay, settings

UTC = timezone.utc
START = datetime(2026, 11, 27, 12, 0, tzinfo=UTC)
END = datetime(2026, 11, 27, 14, 10, tzinfo=UTC)


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    from planner.migrate_lineage import build
    tmp = tmp_path_factory.mktemp("gap")
    s = settings(tmp)
    store = fixture_store()
    store.t = datetime(2026, 11, 27, 12, 0, 3, tzinfo=UTC)
    m = build(s, store, FIX / "migration" / "planner", FIX / "migration", FIX / "migration", store.t)
    st = json.loads((FIX / "state_20261127_1200.json").read_text())
    d = Path(s.planner.folder) / "GBPUSD"
    d.mkdir(parents=True, exist_ok=True)
    (d / "lineage_map.json").write_text(json.dumps(m))
    # the map is applied at the first run; the 1200-57 record already carries the map's lineage
    # production: the price service stopped at 12:01:58 and its first tracker run after the restart was at 12:20
    out = replay(s, END, store=fixture_store(), ideas=[], start=START, initial=st,
                 down=(datetime(2026, 11, 27, 12, 1, 58, tzinfo=UTC), datetime(2026, 11, 27, 12, 20, tzinfo=UTC)))
    out["settings"] = s
    return out


def _ev(run, oid, kind):
    return [e for e in run["events"] if e.get("id") == oid and e["event"] == kind]


def test_FL_C1_the_real_gap_is_recorded_on_the_opportunity_that_was_live_across_it(run):
    (g,) = _ev(run, "STP-GBPUSD-20261127-1200-57", "data gap")
    assert (g["from_utc"], g["to_utc"]) == ("2026-11-27T12:00:00Z", "2026-11-27T12:15:00Z")


def test_FL_C2_its_ending_after_the_gap_keeps_the_open_gap_for_reconciliation(run):
    (e,) = _ev(run, "STP-GBPUSD-20261127-1200-57", "invalidated")
    assert e["destination_case"] == "after_zone_at_or_before_creation" and e["time_utc"] == "2026-11-27T12:20:00Z"
    snap = run["snapshots"][-1]
    m = next(x for L in snap["lineages"].values() for x in L["members"] if x["id"] == "STP-GBPUSD-20261127-1200-57")
    assert [g["status"] for g in m["data_gaps"]] == ["open"]           # waits for IG's own candles (OP-1)


def test_FL_C3_the_incomplete_12_00_hour_makes_no_new_test_and_does_not_block_the_next_opportunity(run):
    snap = run["snapshots"][-1]
    L = snap["lineages"]["STP-GBPUSD-20261127-0300-56"]
    assert "2026-11-27T12:00:00Z" not in (L["tests"].get("uncertain") or [])   # its stored parts reached the zone
    assert [e for e in L["tests"]["events"] if e[1] == "rearm"] == []            # still test 1 since 02:00
    live = [o for o in snap["opportunities"] if o["status"] in ("WAITING", "ACTIVE")]
    assert all(not o.get("data_gaps") for o in live)                             # created after the gap: unaffected


def test_FL_C4_no_republication_of_the_consumed_test_can_authorise_after_the_gap(run):
    from stp.authorise import authorise
    s = run["settings"]
    snap = run["snapshots"][-1]
    st = fixture_store()
    st.t = END
    i = SimpleNamespace(strategy="Bollinger bounce 5m", direction="buy", time=END, entry_price=D("13127.0"),
                        context={"rejection_candle": "2026-11-27T13:10:00Z"}, steps=[])
    v = authorise(s, st, i, END, SimpleNamespace(state_at=lambda t=None: snap))
    if v.allowed:                                       # a live republication binds: its key is test 1 of 0300-56
        assert v.stp_key == "STP-GBPUSD-20261127-0300-56#t1" and "STP-GBPUSD-20261127-1200-57#t1" in v.signal.split("|")
