"""Phase 2 PD-4: the historical lineage map (planner/migrate_lineage.py). Technical tests TM-xx on the compact copies
of the production records of 24-27 November 2026 (tests/stp/fixtures/lifecycle_20261127/migration) and the frozen
candles. Read only; nothing is written outside tmp_path."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone

from planner.migrate_lineage import build
from tests.stp.lifecycle_replay import FIX, fixture_store, settings

UTC = timezone.utc
AS_OF = datetime(2026, 11, 27, 14, 15, tzinfo=UTC)
M = FIX / "migration"


def _build(tmp, planner=M / "planner", orders=M, records=M):
    s = settings(tmp)
    st = fixture_store()
    st.t = AS_OF
    return build(s, st, planner, orders, records, AS_OF)


def test_TM_01_the_map_is_deterministic(tmp_path):
    a, b = _build(tmp_path / "a"), _build(tmp_path / "b")
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_TM_02_every_consumed_key_is_on_its_lineage_and_only_the_repeat_is_an_alias(tmp_path):
    m = _build(tmp_path)
    consumed = {ref: (L, n) for L, r in m["lineages"].items() for n, refs in r["consumed"].items() for ref in refs}
    assert len(consumed) == 9 and m["ambiguous"] == []
    aliases = {k for r in m["lineages"].values() for ks in r["aliases"].values() for k in ks}
    assert "STP-GBPUSD-20261127-1200-57#t1" in aliases
    assert consumed["AB261127120127-5755701a"] == consumed["AB261127065505-8c11a4bc"]        # the same test
    tests = list(consumed.values())
    others = [v for k, v in consumed.items() if k != "AB261127120127-5755701a"]
    assert len(set(others)) == 8 and len(tests) == 9                                         # 8 distinct tests


def test_TM_03_zones_are_never_chained_into_one_lineage(tmp_path):
    m = _build(tmp_path)
    lin = {x["id"]: L for L, r in m["lineages"].items() for x in r["members"]}
    assert lin["STP-GBPUSD-20261126-0400-38"] != lin["STP-GBPUSD-20261126-1400-44"]      # 13093-13103 vs 13115-13124
    for L, r in m["lineages"].items():
        home = r["home_zone"]
        for x in r["members"]:
            same_identity = any(y["identity"] == x["identity"] for y in r["members"] if y["id"] == L)
            overlaps = float(x["zone"]["low"]) < float(home["high"]) and float(home["low"]) < float(x["zone"]["high"])
            assert overlaps or same_identity or x["id"] == L, (L, x["id"])


def test_TM_04_a_key_without_a_rejection_candle_is_reported_not_guessed(tmp_path):
    rec = tmp_path / "rec"
    rec.mkdir()
    rows = [json.loads(x) for x in (M / "trades.jsonl").read_text().splitlines()]
    for r in rows:
        if r["reference"] == "AB261127120127-5755701a":
            r["steps"] = []
    (rec / "trades.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    m = _build(tmp_path / "s", records=rec)
    amb = [a for a in m["ambiguous"] if a["reference"] == "AB261127120127-5755701a"]
    assert amb and "no rejection candle" in amb[0]["why"]
    aliases = {k for r in m["lineages"].values() for ks in r["aliases"].values() for k in ks}
    assert "STP-GBPUSD-20261127-1200-57#t1" not in aliases


def test_TM_05_a_single_tracker_supersession_to_another_place_is_not_a_lineage(tmp_path):
    m = _build(tmp_path)
    lin = {x["id"]: L for L, r in m["lineages"].items() for x in r["members"]}
    # 24 Nov 15:00: the single tracker superseded 1400-21 (13103-13114.1) by 1500-22 (13135.5-13142.1): another place
    assert lin["STP-GBPUSD-20261124-1500-22"] != lin["STP-GBPUSD-20261124-1400-21"]


def test_TM_06_applying_the_map_again_after_a_crash_changes_nothing(tmp_path):
    from planner.opportunities import OpportunityKeeper
    m = _build(tmp_path)
    s = settings(tmp_path / "k")
    d = tmp_path / "k" / "planner" / "GBPUSD"
    d.mkdir(parents=True)
    shutil.copyfile(FIX / "current_20261127_1415.json", d / "current.json")
    (d / "lineage_map.json").write_text(json.dumps(m))
    st = fixture_store()
    st.t = AS_OF
    k = OpportunityKeeper(s, st)
    k._apply_lineage_map(AS_OF)
    first = json.dumps(k.state["lineages"], sort_keys=True)
    k.state.pop("lineage_map_applied")                        # as if the process stopped before its file was saved
    k._apply_lineage_map(AS_OF)
    assert json.dumps(k.state["lineages"], sort_keys=True) == first
