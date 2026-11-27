"""Phase 2 independent review findings R1-R4 (owner's brief, 27 November 2026; review of 087b8c3). Offline; nothing
is written outside tmp_path; IG is never contacted.

R1  the acknowledgement file after an interrupted write (a last line with no newline)
R2  a primary destination revised while the opportunity is live: the duplicate rule must use the one achieved
R3  the catch-up's missing-candle check and the most recent finished 5-minute interval
R4  the controlled review of D-R1/D-R2 (fail closed): python -m planner.review, and its guarantees"""

from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal as D
from types import SimpleNamespace

from tests.technical.test_trading import S  # noqa: F401  (orders, records and trade manager folders)
from tests.technical.test_planner import T
from tests.technical.test_stp_integration import (Bi, KS, auth_settings, auth_state, ev, five, hour, ok, opp, opps,
                                                  pd, src, state, store_with)

UTC_NOW = T(2026, 11, 17, 9, 0, 3)


def at(h, m=0, s=0):
    return T(2026, 11, 17, h, m, s)


# ---- R1: acknowledgements after an interrupted write ---------------------------------------------------------------------

def _trade(ref, oid="OPP-1"):
    return SimpleNamespace(reference=ref, deal_id="DIAAAX", strategy="Bollinger bounce 5m", direction="sell",
                           opened_at=at(9, 6), stp={"opportunity": oid, "lineage": oid, "test": 1, "key": f"{oid}#t1",
                                                     "keys": [f"{oid}#t1"]})


def test_TR1_01_an_interrupted_write_then_a_backfill_never_glues_the_acknowledgement_to_the_fragment(tmp_path):
    from orders.executions import FILE, ExecutionAcks, read
    path = tmp_path / FILE
    good = json.dumps({"reference": "AB-1", "opportunity": "OPP-1", "executed_utc": "2026-11-17T09:06:00Z"})
    path.write_text(good[: len(good) // 2])                          # the process stopped mid-write: no newline
    acks = ExecutionAcks(tmp_path, lambda: at(9, 7))                 # the restart: AB-1 is not seen
    assert acks.backfill([_trade("AB-1")]) == 1                      # from the order journal (durable)
    assert [a["reference"] for a in read(path)] == ["AB-1"]
    assert path.read_text().splitlines()[0] == good[: len(good) // 2]   # the fragment kept as evidence


def test_TR1_02_later_executions_and_repeated_restarts_keep_every_acknowledgement_once(tmp_path):
    from orders.executions import FILE, ExecutionAcks, read
    path = tmp_path / FILE
    path.write_text('{"reference": "AB-0", "opp')                    # a damaged last line
    a = ExecutionAcks(tmp_path, lambda: at(9, 7))
    a.record(_trade("AB-1"), at(9, 6), "IG's deal confirmation: ACCEPTED")
    a.record(_trade("AB-2"), at(9, 8), "IG's deal confirmation: ACCEPTED")
    for _ in range(3):                                               # three restarts, each with a backfill
        ExecutionAcks(tmp_path, lambda: at(9, 9)).backfill([_trade("AB-1"), _trade("AB-2")])
    assert [x["reference"] for x in read(path)] == ["AB-1", "AB-2"]
    assert path.read_text().endswith("\n")


def test_TR1_03_the_tracker_takes_the_backfilled_acknowledgement(tmp_path):
    from orders.executions import FILE, ExecutionAcks
    from planner.opportunities import OpportunityKeeper
    from tests.planner_helpers import Over, section
    from tests.technical.test_planner import S as PS
    s = Over(KS(tmp_path), orders=section(PS.orders, folder=tmp_path / "orders"))
    OpportunityKeeper(s, store_with(UTC_NOW), planner=Bi(SELL=[pd()])).run(UTC_NOW)
    oid = opps(tmp_path)[0]["id"]
    folder = tmp_path / "orders" / "GBPUSD"
    folder.mkdir(parents=True)
    (folder / FILE).write_text('{"reference": "AB-1", "oppor')        # interrupted
    ExecutionAcks(folder, lambda: at(9, 7)).backfill([_trade("AB-1", oid)])
    OpportunityKeeper(s, store_with(at(9, 10)), planner=Bi(SELL=[pd()])).run(at(9, 10))
    assert [x["reference"] for x in opps(tmp_path)[0]["executions"]] == ["AB-1"]


def test_TR1_04_the_order_journal_is_kept_whole_through_the_repair(S):
    from orders.executions import FILE, read
    from strategies.common import BOLLINGER_BOUNCE_5M, SELL
    from tests.technical.test_orders import PretendIG, WED, idea, make
    sender, ig, *_ = make(S, PretendIG())
    ctx = {"signal": "OPP-1#t1", "stp": {"opportunity": "OPP-1", "lineage": "OPP-1", "test": 1, "key": "OPP-1#t1",
                                          "keys": ["OPP-1#t1"], "bypass": []}}
    r = sender.place(idea(BOLLINGER_BOUNCE_5M, SELL, t=WED, price="13400.0", context=ctx), calendar=[])
    before = sender.journal.read_text()
    p = sender.folder / FILE
    p.write_text(p.read_text()[:-20])                                # the acknowledgement torn
    again, *_ = make(S, PretendIG(positions=ig.positions))
    assert again.journal.read_text().startswith(before)              # every earlier journal line kept as it was
    assert [a["reference"] for a in read(p)] == [r.reference]        # the backfill replaced what was torn


# ---- R2: a destination revised while live ---------------------------------------------------------------------------------

def _live_then_revised_then_completed(tmp, revised=13175, completes_at=13176):
    """SELL zone 13240-13250, published with primary 13170 (zone 13165-13170), revised at 10:00 to `revised`, reached
    the zone at 09:05 and the revised destination at 10:10."""
    plans = Bi(SELL=[pd(primary=13170), pd(primary=revised), pd(primary=revised)])
    ok(tmp, store_with(UTC_NOW, 13236), plans).run(UTC_NOW)
    ok(tmp, store_with(at(9, 10), 13236), plans).run(at(9, 10))       # Watch & Wait
    hrs = [hour(at(9), 13236, 13237, 13235, 13236)]
    ok(tmp, store_with(at(10, 0, 3), 13236, extra1=hrs), plans).run(at(10, 0, 3))
    o = opps(tmp)[0]
    assert o["destinations"]["primary"]["price"] == str(revised)
    down = [five(at(10, 10), 13236, 13237, completes_at, completes_at + 1)]
    ok(tmp, store_with(at(10, 15), 13236, extra5=down, extra1=hrs), plans).run(at(10, 15))
    assert any(e["event"] == "completed" for e in ev(tmp))
    return plans, down, hrs


def test_TR2_01_the_lineage_records_the_destination_actually_achieved(tmp_path):
    _live_then_revised_then_completed(tmp_path)
    m = next(m for L in state(tmp_path)["lineages"].values() for m in L["members"])
    assert m["primary"] == "13175" and m["primary_zone"] == {"low": "13170", "high": "13175"}


def test_TR2_02_a_republication_overlapping_the_revised_destination_is_withheld(tmp_path):
    plans, down, hrs = _live_then_revised_then_completed(tmp_path)
    plans.plans["SELL"].append(pd(primary=13178))                    # 13173-13178 overlaps 13170-13175 (achieved)
    plans.calls["SELL"] = len(plans.plans["SELL"]) - 1
    ok(tmp_path, store_with(at(11, 0, 3), 13236, extra5=down, extra1=hrs), plans).run(at(11, 0, 3))
    assert opps(tmp_path) == [] and any(e["event"] == "duplicate" for e in ev(tmp_path))


def test_TR2_03_a_republication_toward_a_genuinely_different_destination_is_issued(tmp_path):
    plans, down, hrs = _live_then_revised_then_completed(tmp_path)
    plans.plans["SELL"].append(pd(primary=13169))                    # 13164-13169: overlaps the PUBLISHED 13165-13170
    plans.calls["SELL"] = len(plans.plans["SELL"]) - 1                # but not the achieved 13170-13175
    ok(tmp_path, store_with(at(11, 0, 3), 13236, extra5=down, extra1=hrs), plans).run(at(11, 0, 3))
    assert len(opps(tmp_path)) == 1


def test_TR2_04_after_a_restart_the_achieved_destination_still_decides(tmp_path):
    plans, down, hrs = _live_then_revised_then_completed(tmp_path)
    from planner.opportunities import OpportunityKeeper
    k = OpportunityKeeper(KS(tmp_path), store_with(at(10, 20), 13236, extra5=down, extra1=hrs), planner=plans)
    m = next(m for L in k.state["lineages"].values() for m in L["members"])
    assert m["primary"] == "13175"
    p = pd(primary=13178)
    assert k._duplicate_of(p) == m["id"]


def test_TR2_05_the_migration_takes_a_recorded_destination_change(tmp_path):
    from planner.migrate_lineage import history
    d = tmp_path / "p"
    d.mkdir()
    iss = {"id": "STP-GBPUSD-20261117-0900-1", "trade": "SELL", "created_utc": "2026-11-17T09:00:03Z",
           "identity": ["SELL", []], "entry_zone": {"low": "13240", "high": "13250"},
           "destinations": {"primary": {"price": "13170", "zone": {"low": "13165", "high": "13170"}}}}
    (d / "issued.jsonl").write_text(json.dumps(iss) + "\n")
    evs = [{"time_utc": "2026-11-17T09:00:03Z", "event": "created", "id": iss["id"], "why": "x"},
           {"time_utc": "2026-11-17T10:00:03Z", "event": "changed", "id": iss["id"],
            "why": "re-checked, still supported; changed: primary destination 13170 to 13175; condition A to B"},
           {"time_utc": "2026-11-17T10:15:00Z", "event": "completed", "id": iss["id"], "why": "reached"}]
    (d / "recommendations.jsonl").write_text("".join(json.dumps(e) + "\n" for e in evs))
    (o,) = history(d, "2026-11-17T00:00:00Z")
    assert o["primary"] == "13175" and o["primary_zone"] is None       # the zone of a revision is not recorded


def test_TR2_06_an_achieved_price_without_its_zone_still_matches_a_destination_zone_containing_it(tmp_path):
    from planner.opportunities import OpportunityKeeper
    k = OpportunityKeeper(KS(tmp_path), store_with(UTC_NOW), planner=Bi(SELL=[pd()]))
    p = pd(primary=13170)
    k.state["lineages"] = {"L": {"id": "L", "trade": "SELL", "home_zone": {"low": "13240", "high": "13250"},
                                 "members": [{"id": "L", "identity": ["x"], "zone": {"low": "13240", "high": "13250"},
                                              "primary": "13167", "primary_zone": None, "ended_utc": "2026-11-17T08:00:00Z",
                                              "status": "COMPLETED", "effective_status": "COMPLETED"}],
                                 "tests": {}, "aliases": {}, "consumed": {}}}
    assert k._duplicate_of(p) == "L"                                  # 13167 lies in 13165-13170
    k.state["lineages"]["L"]["members"][0]["primary"] = "13180"
    assert k._duplicate_of(p) is None


# ---- R3: the most recent finished 5-minute interval in the catch-up -----------------------------------------------------

def _store_until(t, drop=()):
    from tests.technical.test_stp_integration import auth_store
    st = auth_store(until=t)
    st.by_tf["5m"] = [c for c in st.by_tf["5m"] if c.start not in drop]
    return st


def _sell_idea(t):
    from tests.technical.test_stp_integration import REJ_SELL
    return SimpleNamespace(strategy="Bollinger bounce 5m", direction="sell", time=t, entry_price=D("13231"),
                           context={"rejection_candle": REJ_SELL.strftime("%Y-%m-%dT%H:%M:%SZ")})


def _state(m5):
    return auth_state(opp("SELL", (13240, 13250)), written=m5 + timedelta(seconds=3), m5=m5)


B = T(2026, 11, 17, 10, 5)                                           # a 5-minute boundary


def test_TR3_01_just_after_a_boundary_a_destination_touch_in_the_unpublished_candle_refuses(tmp_path):
    from stp.authorise import authorise
    now = B + timedelta(milliseconds=400)                            # IG has not yet sent the 10:00 candle's end
    st = _store_until(B, drop={T(2026, 11, 17, 10, 0)})
    prev = five(T(2026, 11, 17, 10, 0), 13200, 13200, 13169, 13185)   # the engine's own candle: 13170 touched
    v = authorise(auth_settings(tmp_path), st, _sell_idea(now), now, src(_state(T(2026, 11, 17, 10, 0))),
                  partial=None, previous=prev)
    assert not v.allowed and "primary destination 13170 was reached" in " ".join(v.reasons)


def test_TR3_02_normal_publication_timing_does_not_refuse_a_clean_candle(tmp_path):
    from stp.authorise import authorise
    now = B + timedelta(milliseconds=400)
    st = _store_until(B, drop={T(2026, 11, 17, 10, 0)})
    prev = five(T(2026, 11, 17, 10, 0), 13200, 13201, 13199, 13200)
    v = authorise(auth_settings(tmp_path), st, _sell_idea(now), now, src(_state(T(2026, 11, 17, 10, 0))),
                  partial=None, previous=prev)
    assert v.allowed, v.reasons


def test_TR3_03_at_the_boundary_before_any_new_price_the_forming_candle_is_the_finished_one(tmp_path):
    from stp.authorise import authorise
    st = _store_until(B, drop={T(2026, 11, 17, 10, 0)})
    part = five(T(2026, 11, 17, 10, 0), 13200, 13200, 13169, 13185)
    v = authorise(auth_settings(tmp_path), st, _sell_idea(B), B, src(_state(T(2026, 11, 17, 10, 0))),
                  partial=part, previous=None, partial_covered=True)
    assert not v.allowed and "primary destination 13170 was reached" in " ".join(v.reasons)


def test_TR3_04_a_genuine_gap_in_the_most_recent_interval_refuses(tmp_path):
    from stp.authorise import authorise
    now = B + timedelta(seconds=40)
    st = _store_until(B, drop={T(2026, 11, 17, 10, 0)})               # never stored; the engine has no full candle
    v = authorise(auth_settings(tmp_path), st, _sell_idea(now), now, src(_state(T(2026, 11, 17, 10, 0))),
                  partial=None, previous=None)
    assert not v.allowed and any("PD-5" in r for r in v.reasons)


def test_TR3_05_a_candle_the_engine_saw_only_in_part_does_not_count(tmp_path):
    from stp.authorise import authorise
    now = B + timedelta(seconds=2)
    st = _store_until(B, drop={T(2026, 11, 17, 10, 0)})
    part = five(T(2026, 11, 17, 10, 0), 13200, 13201, 13199, 13200)  # began after a restart mid-candle
    v = authorise(auth_settings(tmp_path), st, _sell_idea(B), B, src(_state(T(2026, 11, 17, 10, 0))),
                  partial=part, previous=None, partial_covered=False)
    assert not v.allowed and any("PD-5" in r for r in v.reasons)


def test_TR3_06_the_engine_keeps_the_finished_candle_and_knows_whether_it_saw_it_whole(tmp_path):
    from trading.engine import Trading
    e = SimpleNamespace(partial=None, previous_partial=None, partial_covered=False, previous_covered=False)
    tk = lambda t, p: SimpleNamespace(time=t, buy=D(p) + D("1.2"), sell=D(p))            # noqa: E731
    Trading._forming(e, tk(T(2026, 11, 17, 9, 57), "13200"))          # first price after a start: not whole
    assert e.partial_covered is False
    Trading._forming(e, tk(T(2026, 11, 17, 10, 0, 1), "13201"))       # the 10:00 candle began with prices flowing
    assert e.partial_covered is True and e.previous_partial.start == T(2026, 11, 17, 9, 55)
    assert e.previous_covered is False                                # the 09:55 one was seen only in part
    Trading._forming(e, tk(T(2026, 11, 17, 10, 5, 0, 200000), "13202"))
    assert e.previous_partial.start == T(2026, 11, 17, 10, 0) and e.previous_covered is True


def test_TR3_07_a_published_candle_is_read_from_the_store_as_before(tmp_path):
    from stp.authorise import authorise
    now = B + timedelta(seconds=1)
    st = _store_until(B)
    st.by_tf["5m"] = [c for c in st.by_tf["5m"] if c.start != T(2026, 11, 17, 10, 0)] + \
        [five(T(2026, 11, 17, 10, 0), 13200, 13200, 13169, 13185)]     # stored, with the touch
    v = authorise(auth_settings(tmp_path), st, _sell_idea(now), now, src(_state(T(2026, 11, 17, 10, 0))))
    assert not v.allowed and "the Tue 17 Nov 10:00 GMT 5-minute candle" in " ".join(v.reasons)


# ---- R4: the controlled review (D-R1, D-R2: fail closed) ---------------------------------------------------------------

def test_TR4_01_the_review_report_lists_only_the_blocked_opportunities_with_their_evidence(tmp_path):
    from planner.review import blocked
    st = {"opportunities": [
        {"id": "A", "trade": "SELL", "status": "WAITING", "lineage": "A",
         "data_gaps": [{"from_utc": "x", "to_utc": "y", "status": "review"}]},
        {"id": "B", "trade": "BUY", "status": "ACTIVE", "lineage": "B"}],
        "lineages": {"A": {"tests": {"uncertain": ["2026-11-17T09:00:00Z"]}, "consumed": {"1": ["AB-1"]},
                           "aliases": {"1": ["OLD#t1"]}}, "B": {"tests": {}}}}
    rep = blocked(st)
    assert [r["id"] for r in rep] == ["A"]
    assert rep[0]["consumed"] == {"1": ["AB-1"]} and rep[0]["aliases"] == {"1": ["OLD#t1"]}
    assert rep[0]["uncertain_hours"] == ["2026-11-17T09:00:00Z"] and rep[0]["gaps"][0]["status"] == "review"


def test_TR4_02_an_uncertain_lineage_never_blocks_an_unrelated_one_and_keeps_its_consumed_keys(tmp_path):
    from stp.authorise import authorise
    from tests.technical.test_stp_integration import REJ_BUY, auth_store, idea
    a = opp("SELL", (13240, 13250), oid="A")
    b = opp("BUY", (13150, 13160), oid="B")
    st = auth_state(a, b) | {"lineages": {"A": {"tests": {"events": [["2026-11-17T08:00:00Z", "test"]],
                                                          "uncertain": ["2026-11-17T09:00:00Z"]},
                                                "aliases": {"1": ["OLD#t1"]}}, "B": {"tests": {}}}}
    s = auth_settings(tmp_path)
    from tests.technical.test_stp_integration import AT, REJ_SELL
    assert not authorise(s, auth_store(), idea("sell", REJ_SELL), AT, src(st)).allowed
    assert authorise(s, auth_store(), idea("buy", REJ_BUY), AT, src(st)).allowed
    assert st["lineages"]["A"]["aliases"] == {"1": ["OLD#t1"]}
