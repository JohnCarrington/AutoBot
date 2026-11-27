"""Phase 2 WP2, lifecycle accuracy (owner's approval of 27 November 2026: C-1, PD-1 option C, C-7). Technical tests
TW2-xx. Offline: scripted plans, in-memory candle stores and a pretend IG; nothing is written outside tmp_path.

The SELL zone is 13240-13250, primary destination 13170 (destination zone 13165-13170), as in test_stp_integration."""

from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal as D
from types import SimpleNamespace

from tests.technical.test_trading import S  # noqa: F401  (orders, records and trade manager folders)
from planner.keeper import COMPLETED, INVALIDATED

# the four circumstances (planner/keeper.py BEFORE_ZONE ... AFTER_TRADE), as recorded in destination_case
BEFORE_ZONE, AT_CREATION, AFTER_ZONE, AFTER_TRADE = ("before_zone", "after_zone_at_or_before_creation", "after_zone",
                                                     "after_trade")
from tests.technical.test_planner import T
from tests.technical.test_stp_integration import Bi, ev, five, ok, opps, pd, state, store_with

NOW = T(2026, 11, 17, 9, 0, 3)


def at(h, m=0, s=0):
    return T(2026, 11, 17, h, m, s)


def ends(tmp):
    return [e for e in ev(tmp) if e["event"] in ("completed", "invalidated")]


def ack(tmp, oid, ref="AB261117091000-aaaa0000", executed="2026-11-17T09:12:00Z", test=1, lineage=None):
    p = tmp / "orders" / "GBPUSD" / "stp_executions.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as f:
        f.write(json.dumps({"reference": ref, "deal_id": "DIAAAX", "strategy": "Bollinger bounce 5m", "direction": "sell",
                            "opportunity": oid, "lineage": lineage or oid, "test": test, "key": f"{lineage or oid}#t{test}",
                            "keys": [f"{lineage or oid}#t{test}"], "executed_utc": executed,
                            "recorded_utc": executed, "source": "test"}) + "\n")


def KO(tmp):
    """The tracker with the orders folder in tmp (where the order sender writes its acknowledgements)."""
    from tests.technical.test_stp_integration import KS
    from tests.planner_helpers import Over, section
    from tests.technical.test_planner import S as PS
    s = KS(tmp)
    return Over(s, orders=section(PS.orders, folder=tmp / "orders"))


def krun(tmp, t, plans, **kw):
    from planner.opportunities import OpportunityKeeper
    OpportunityKeeper(KO(tmp), store_with(t, **kw), planner=plans).run(t)


DOWN = [five(at(9, 10), 13200, 13200, 13169, 13170)]                 # reaches 13170 in the 09:10 candle


# ---- C-1: the four circumstances --------------------------------------------------------------------------------------

def test_TW2_01_no_interaction_then_the_destination_is_destination_reached_before_entry(tmp_path):
    krun(tmp_path, NOW, Bi(SELL=[pd()]))
    krun(tmp_path, at(9, 15), Bi(SELL=[pd()]), extra5=DOWN)
    (e,) = ends(tmp_path)
    assert e["status"] == INVALIDATED and e["destination_case"] == BEFORE_ZONE
    assert "destination reached before entry" in e["why"] and "without reaching the zone" in e["why"]


def test_TW2_02_a_zone_reached_only_before_creation_is_reported_truthfully_and_never_activates(tmp_path):
    pre = [five(at(8, 55), 13230, 13241, 13229, 13238)]               # at the zone before the opportunity existed
    krun(tmp_path, NOW, Bi(SELL=[pd()]), extra5=pre)
    krun(tmp_path, at(9, 15), Bi(SELL=[pd()]), extra5=pre + DOWN)
    (e,) = ends(tmp_path)
    assert e["status"] == INVALIDATED and e["destination_case"] == AT_CREATION
    assert "only at or before the opportunity's creation" in e["why"] and "without reaching the zone" not in e["why"]
    assert not any(x["event"] == "active" for x in ev(tmp_path))       # the owner's 18 Nov rule: not an activation


def test_TW2_03_activated_after_creation_completes_as_before(tmp_path):
    krun(tmp_path, NOW, Bi(SELL=[pd()]))
    touch = [five(at(9, 5), 13230, 13241, 13229, 13238)]
    krun(tmp_path, at(9, 15), Bi(SELL=[pd()]), extra5=touch + DOWN)
    (e,) = ends(tmp_path)
    assert e["status"] == COMPLETED and e["destination_case"] == AFTER_ZONE


def test_TW2_04_a_confirmed_trade_entry_before_the_destination_completes_it(tmp_path):
    pre = [five(at(8, 55), 13230, 13241, 13229, 13238)]
    krun(tmp_path, NOW, Bi(SELL=[pd()]), extra5=pre)
    oid = opps(tmp_path)[0]["id"]
    ack(tmp_path, oid, executed="2026-11-17T09:06:00Z")
    krun(tmp_path, at(9, 10), Bi(SELL=[pd()]), extra5=pre)
    assert opps(tmp_path)[0]["executions"][0]["reference"] == "AB261117091000-aaaa0000"
    krun(tmp_path, at(9, 15), Bi(SELL=[pd()]), extra5=pre + DOWN)
    (e,) = ends(tmp_path)
    assert e["status"] == COMPLETED and e["destination_case"] == AFTER_TRADE and "confirmed trade entry" in e["why"]


def test_TW2_05_an_entry_in_the_same_candle_as_the_destination_came_first(tmp_path):
    krun(tmp_path, NOW, Bi(SELL=[pd()]))
    oid = opps(tmp_path)[0]["id"]
    ack(tmp_path, oid, executed="2026-11-17T09:11:30Z")              # inside the 09:10 candle that reached 13170
    krun(tmp_path, at(9, 15), Bi(SELL=[pd()]), extra5=DOWN)
    (e,) = ends(tmp_path)
    assert e["destination_case"] == AFTER_TRADE


def test_TW2_06_an_entry_after_the_destination_does_not_complete_it(tmp_path):
    krun(tmp_path, NOW, Bi(SELL=[pd()]))
    oid = opps(tmp_path)[0]["id"]
    ack(tmp_path, oid, executed="2026-11-17T09:16:00Z")              # after the 09:10 candle's end
    krun(tmp_path, at(9, 15), Bi(SELL=[pd()]), extra5=DOWN)
    (e,) = ends(tmp_path)
    assert e["destination_case"] == BEFORE_ZONE


# ---- PD-1 C: a late acknowledgement; idempotence; restart ----------------------------------------------------------------

def test_TW2_07_a_late_acknowledgement_corrects_the_classification_and_reopens_nothing(tmp_path):
    krun(tmp_path, NOW, Bi(SELL=[pd(), pd()]))
    oid = opps(tmp_path)[0]["id"]
    krun(tmp_path, at(9, 15), Bi(SELL=[pd(), pd()]), extra5=DOWN)    # ended "before entry": the ack not yet there
    ack(tmp_path, oid, executed="2026-11-17T09:08:00Z")              # IG's later confirmation of a 09:08 execution
    krun(tmp_path, at(9, 20), Bi(SELL=[pd(), pd()]), extra5=DOWN)
    fix = [e for e in ev(tmp_path) if e["event"] == "classification corrected"]
    assert len(fix) == 1 and fix[0]["id"] == oid and fix[0]["destination_case"] == AFTER_TRADE
    assert opps(tmp_path) == [] and [e["event"] for e in ends(tmp_path)] == ["invalidated"]     # never reopened
    m = next(m for L in state(tmp_path)["lineages"].values() for m in L["members"] if m["id"] == oid)
    assert m["effective_status"] == COMPLETED
    krun(tmp_path, at(10, 0, 3), Bi(SELL=[pd(), pd()]), extra5=DOWN)  # the same structure again: a duplicate now
    assert opps(tmp_path) == [] and any(e["event"] == "duplicate" for e in ev(tmp_path))


def test_TW2_08_each_acknowledgement_is_taken_once_across_restarts(tmp_path):
    krun(tmp_path, NOW, Bi(SELL=[pd()]))
    oid = opps(tmp_path)[0]["id"]
    ack(tmp_path, oid)
    ack(tmp_path, oid)                                              # written twice (a stop and a backfill)
    for m in (5, 10):
        krun(tmp_path, at(9, m), Bi(SELL=[pd()]))
    o = opps(tmp_path)[0]
    assert len(o["executions"]) == 1
    assert sum(e["event"] == "trade executed" for e in ev(tmp_path)) == 1
    L = state(tmp_path)["lineages"][o["lineage"]]
    assert L["consumed"] == {"1": ["AB261117091000-aaaa0000"]}


# ---- the order sender: only a confirmed execution is acknowledged ---------------------------------------------------------

def _stp_idea(t):
    from strategies.common import BOLLINGER_BOUNCE_5M, SELL
    from tests.technical.test_orders import idea
    return idea(BOLLINGER_BOUNCE_5M, SELL, t=t, price="13400.0", context={
        "signal": "OPP-1#t1", "stp": {"opportunity": "OPP-1", "lineage": "OPP-1", "test": 1, "key": "OPP-1#t1",
                                       "keys": ["OPP-1#t1"], "bypass": []}})


def _acks(sender):
    from orders.executions import FILE, read
    return read(sender.folder / FILE)


def test_TW2_10_an_accepted_order_is_acknowledged_with_its_stp_context(S):
    from tests.technical.test_orders import PretendIG, WED, make
    ig = PretendIG()
    sender, ig, *_ = make(S, ig)
    r = sender.place(_stp_idea(WED), calendar=[])
    assert r.ok
    (a,) = _acks(sender)
    assert (a["reference"], a["opportunity"], a["lineage"], a["test"], a["keys"]) == (r.reference, "OPP-1", "OPP-1", 1,
                                                                                    ["OPP-1#t1"])
    assert a["executed_utc"] == WED.strftime("%Y-%m-%dT%H:%M:%SZ") and "ACCEPTED" in a["source"]
    sending = next(x for x in json.loads("[" + ",".join(sender.journal.read_text().splitlines()) + "]")
                   if x["event"] == "sending")
    assert sending["stp"]["opportunity"] == "OPP-1"


def test_TW2_11_a_refused_order_is_never_acknowledged(S):
    from tests.technical.test_orders import PretendIG, make
    ig = PretendIG()
    ig.post_open = {"dealStatus": "REJECTED", "reason": "INSUFFICIENT_FUNDS"}
    sender, ig, *_ = make(S, ig)
    from tests.technical.test_orders import WED
    r = sender.place(_stp_idea(WED), calendar=[])
    assert not r.ok and _acks(sender) == []


def test_TW2_12_an_unresolved_order_is_not_acknowledged_but_keeps_its_keys(S):
    from tests.functional.test_order_reconciliation_20261127 import LateIG
    from tests.technical.test_orders import make
    ig = LateIG()
    ig.post_open = "late"
    from tests.technical.test_orders import WED
    sender, ig, *_ = make(S, ig)
    r = sender.place(_stp_idea(WED), calendar=[])
    assert not r.ok and _acks(sender) == []
    assert "OPP-1#t1" in sender.used_signals()


def test_TW2_13_a_recovered_order_is_acknowledged_at_igs_own_open_time(S):
    from tests.functional.test_order_reconciliation_20261127 import LateIG
    from tests.technical.test_orders import U, make
    ig = LateIG()
    ig.post_open = "late"
    t0 = U(2026, 11, 25, 18, 2, 3)
    sender, ig, alerts, sleeps, clock = make(S, ig, t=t0)
    r = sender.place(_stp_idea(t0), calendar=[])
    ig.show(r.reference, created="2026/11/25 18:02:03:000")
    clock["t"] = U(2026, 11, 25, 18, 5, 2)
    sender.reconcile("after the candle")
    (a,) = _acks(sender)
    assert a["reference"] == r.reference and a["executed_utc"] == "2026-11-25T18:02:03Z" and "recovered" in a["source"]


def test_TW2_14_a_stop_between_the_journal_and_the_acknowledgement_is_repaired_at_start_up(S):
    from orders.executions import FILE
    from tests.technical.test_orders import PretendIG, WED, make
    sender, ig, *_ = make(S, PretendIG())
    r = sender.place(_stp_idea(WED), calendar=[])
    (sender.folder / FILE).unlink()                                  # as if the process stopped before writing it
    again, *_ = make(S, PretendIG(positions=ig.positions))
    assert [a["reference"] for a in _acks(again)] == [r.reference] and "start-up" in _acks(again)[0]["source"]
    third, *_ = make(S, PretendIG(positions=ig.positions))
    assert len(_acks(third)) == 1                                    # never twice


def test_TW2_15_a_paper_trade_is_never_acknowledged(S):
    from orders.sender import OrderSender
    from tests.technical.test_orders import FakeAlerts, PretendIG, WED
    sender = OrderSender(S, PretendIG(), FakeAlerts(), now=lambda: WED, sleep=lambda s: None,
                         quote=lambda: (D("13400.0"), D("13401.5")), paper=True)
    sender.start()
    r = sender.place(_stp_idea(WED), calendar=[])
    assert r.ok and not (sender.folder / "stp_executions.jsonl").exists()


# ---- C-7: the dashboard --------------------------------------------------------------------------------------------------

def test_TW2_20_the_dashboard_says_watch_and_wait_and_names_the_opportunity_that_binds_first(tmp_path):
    from dashboard.stp import STATUS_LABEL, binds_first, opportunities, test_state
    assert STATUS_LABEL["ACTIVE"] == "WATCH & WAIT"
    old = {"id": "A", "trade": "SELL", "status": "ACTIVE", "created_utc": "2026-11-17T08:00:03Z", "lineage": "A",
           "lineage_created_utc": "2026-11-17T08:00:03Z", "entry_zone": {"low": "13240", "high": "13250"}}
    new = dict(old, id="B", created_utc="2026-11-17T09:00:03Z", lineage="B", lineage_created_utc="2026-11-17T09:00:03Z",
               status="WAITING")
    st = {"opportunities": [new, old], "lineages": {"A": {"tests": {"events": [["2026-11-17T08:00:00Z", "test"]]},
                                                          "consumed": {"1": ["AB1"]}}}}
    assert [o["id"] for o in binds_first(st)] == ["A"]
    assert test_state(st, old) == {"tests_counted": 1, "armed": False, "test_now": 1, "consumed": [1],
                                   "uncertain_hours": 0}
    prices = SimpleNamespace(zone=lambda a, b: f"{a}-{b}", real=lambda x: x)
    rows = {r["id"]: r for r in opportunities(st, prices)}
    assert rows["A"]["binds_first"] and not rows["B"]["binds_first"] and rows["A"]["label"] == "Watch & Wait"


def test_TW2_21_stp_reads_the_acknowledgements_through_the_file_alone():
    """The execution side writes, STP reads, and STP never imports execution code: the same file and format."""
    from orders.executions import FILE, read
    from planner.opportunities import ACKS_FILE, read_acks
    import inspect
    import planner.opportunities as po
    assert FILE == ACKS_FILE and inspect.getsource(read).split('"""', 2)[2] == inspect.getsource(read_acks).split('"""', 2)[2]
    assert "from orders" not in inspect.getsource(po) and "import orders" not in inspect.getsource(po)
