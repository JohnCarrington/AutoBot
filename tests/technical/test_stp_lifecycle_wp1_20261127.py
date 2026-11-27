"""Phase 2 WP1, structural identity and duplicate protection (owner's approval of 27 November 2026: C-2, C-3, C-4,
PD-2, PD-3, PD-4; docs/research/stp_lifecycle_integrity_20261127/). Technical tests TW1-xx. Offline: scripted plans and
in-memory candle stores; IG is never contacted; nothing is written outside tmp_path.

Prices are sell prices in points. The SELL zone in these tests is 13240-13250 (pd() in test_stp_integration). A flat
market at 13236 keeps every hourly candle within 3 pips of the zone (it interacts, so the D-25 count is never re-armed);
one at 13200 is wholly clear of it (a re-arm)."""

from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from planner.keeper import COMPLETED, INVALIDATED
from planner.opportunities import ACTIVE, OpportunityKeeper
from stp.authorise import authorise
from tests.technical.test_planner import C, T
from tests.technical.test_stp_integration import (Bi, KS, auth_settings, ev, five, hour, ok, opps, pd, src, state,
                                                  store_with)

NOW = T(2026, 11, 17, 9, 0, 3)                    # a publication seconds after the 09:00 hourly close


def at(h, m=0, s=0):
    return T(2026, 11, 17, h, m, s)


def run(tmp, t, plans, **kw):
    ok(tmp, store_with(t, **kw), plans).run(t)
    return state(tmp)


def sell_idea(rej, price="13231", strategy="Bollinger bounce 5m", signal=None):
    ctx = {"rejection_candle": rej.strftime("%Y-%m-%dT%H:%M:%SZ")} | ({"signal": signal} if signal else {})
    return SimpleNamespace(strategy=strategy, direction="sell", time=rej, entry_price=D(price), context=ctx, steps=[])


def check(tmp, store, rej, when, **kw):
    """The authorisation check against the tracker's own file as it stands, a minute after its last run."""
    st = state(tmp)
    st = dict(st) | {"written_utc": (when - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")}
    return authorise(auth_settings(tmp), store, sell_idea(rej, **kw), when, src(st))


def rule11(used):
    from safety.rules import _one_signal
    return lambda key: _one_signal(SimpleNamespace(switches=SimpleNamespace(one_signal_one_trade=True)),
                                   SimpleNamespace(context={"signal": key}), used)


def used_from(signal, strategy="Bollinger bounce 5m"):
    from orders.sender import OrderSender
    return OrderSender.used_signals(SimpleNamespace(unresolved={}, trades={
        "r": SimpleNamespace(signal=signal, strategy=strategy)}))


def near_hours(start, end, price=13236):
    """Hourly candles that interact with the 13240-13250 zone (high = price + 1 = 13237, 3 pips short of 13240)."""
    out, t = [], start
    while t < end:
        out.append(hour(t, price, price + 1, price - 1, price))
        t += timedelta(hours=1)
    return out


# ---- C-2: lineage continuity across completion, invalidation and reissue ----------------------------------------------

def test_TW1_01_a_reissue_after_completion_with_no_re_arm_continues_the_lineage_and_its_key(tmp_path):
    plans = Bi(SELL=[pd(primary=13170), pd(primary=13150)])               # 13150: another destination (C-3)
    run(tmp_path, NOW, plans, price=13236)
    a = opps(tmp_path)[0]["id"]
    run(tmp_path, at(9, 10), plans, price=13236)                                # the 09:05 candle reaches the zone
    assert opps(tmp_path)[0]["status"] == ACTIVE
    down = [five(at(9, 10), 13236, 13237, 13169, 13170)]
    run(tmp_path, at(9, 15), plans, price=13236, extra5=down)
    assert opps(tmp_path) == [] and any(e["event"] == "completed" and e["id"] == a for e in ev(tmp_path))
    t = at(10, 0, 3)
    st = run(tmp_path, t, plans, price=13236, extra5=down, extra1=near_hours(at(8), at(10)))
    b = opps(tmp_path)[0]
    assert b["id"] != a and b["lineage"] == a                                   # the same structural place
    store = store_with(t, 13236, extra5=down, extra1=near_hours(at(8), at(10)))
    first = check(tmp_path, store, at(9, 5), t)                                 # a rejection in the same test
    assert first.allowed and first.stp_key == f"{a}#t1"
    assert rule11(used_from(f"{a}#t1"))(first.signal)                          # already traded: refused


def test_TW1_02_a_reissue_after_destination_before_entry_with_no_re_arm_continues_the_lineage(tmp_path):
    plans = Bi(SELL=[pd()])
    pre = [hour(at(8), 13200, 13241, 13199, 13200)]                             # a test before publication (08:00 hour)
    run(tmp_path, NOW, plans, extra1=pre)
    a = opps(tmp_path)[0]["id"]
    down = [five(at(9, 5), 13200, 13200, 13169, 13170)]
    run(tmp_path, at(9, 15), plans, extra5=down, extra1=pre)
    assert opps(tmp_path) == [] and any("destination reached before entry" in (e.get("why") or "")
                                        for e in ev(tmp_path) if e["id"] == a)
    hrs = pre + [hour(at(9), 13200, 13238, 13169, 13200)]                       # 09:00 hour still within 3 pips
    t = at(10, 0, 3)
    run(tmp_path, t, plans, extra5=down, extra1=hrs)
    b = opps(tmp_path)[0]
    assert b["id"] != a and b["lineage"] == a


def test_TW1_03_a_re_arm_between_retirement_and_reissue_gives_the_next_test(tmp_path):
    plans = Bi(SELL=[pd(primary=13170), pd(primary=13150)])
    run(tmp_path, NOW, plans, price=13236)
    run(tmp_path, at(9, 10), plans, price=13236)
    down = [five(at(9, 10), 13236, 13237, 13169, 13170)]
    run(tmp_path, at(9, 15), plans, price=13236, extra5=down)
    a = next(e["id"] for e in ev(tmp_path) if e["event"] == "created")
    clear = [hour(at(10), 13200, 13201, 13199, 13200), hour(at(11), 13200, 13201, 13199, 13200)]   # wholly clear: re-arm
    hrs = near_hours(at(8), at(10)) + clear + near_hours(at(12), at(13))
    t = at(13, 0, 3)
    run(tmp_path, t, plans, price=13236, extra5=down, extra1=hrs)
    b = opps(tmp_path)[0]
    assert b["lineage"] == a
    store = store_with(t, 13236, extra5=down + [five(at(12, 30), 13236, 13241, 13235, 13238)], extra1=hrs)
    v = check(tmp_path, store, at(12, 30), t + timedelta(minutes=1))
    assert v.allowed and v.stp_key == f"{a}#t2"                                 # a genuinely new test: next number
    assert not rule11(used_from(f"{a}#t1"))(v.signal)                           # tradable after a trade on test 1


# ---- C-2 seeding: a test that began before publication; the creation hour -----------------------------------------------

def test_TW1_04_a_pre_publication_test_is_test_1_and_the_first_test_after_a_re_arm_is_test_2(tmp_path):
    created = at(10, 0, 3)
    hrs = [hour(at(9), 13230, 13241, 13229, 13235),                             # 09:00: the zone tested before publication
           hour(at(10), 13200, 13201, 13199, 13200), hour(at(11), 13200, 13201, 13199, 13200),   # re-armed
           hour(at(12), 13230, 13241, 13229, 13235)]                             # 12:00: a new test
    plans = Bi(SELL=[pd()])
    ok(tmp_path, store_with(created, extra1=hrs[:1]), plans).run(created)
    for h in (11, 12, 13):
        t = at(h, 0, 3)
        ok(tmp_path, store_with(t, extra1=hrs), plans).run(t)
    a = opps(tmp_path)[0]["id"]
    rej = [five(at(9, 40), 13230, 13241, 13229, 13235), five(at(12, 30), 13230, 13241, 13229, 13235)]
    store = store_with(at(13, 0, 3), extra5=rej, extra1=hrs)
    assert check(tmp_path, store, at(9, 40), at(13, 1)).stp_key == f"{a}#t1"
    assert check(tmp_path, store, at(12, 30), at(13, 1)).stp_key == f"{a}#t2"


def test_TW1_05_an_interaction_in_the_creation_hour_is_counted(tmp_path):
    created = at(10, 0, 3)
    hrs = [hour(at(9), 13200, 13201, 13199, 13200),                             # wholly clear before publication
           hour(at(10), 13230, 13241, 13229, 13235),                            # the creation hour tests the zone
           hour(at(11), 13200, 13201, 13199, 13200),                            # re-armed
           hour(at(12), 13230, 13241, 13229, 13235)]
    plans = Bi(SELL=[pd()])
    ok(tmp_path, store_with(created, extra1=hrs[:1]), plans).run(created)
    for h in (11, 12, 13):
        t = at(h, 0, 3)
        ok(tmp_path, store_with(t, extra1=hrs), plans).run(t)
    a = opps(tmp_path)[0]["id"]
    rej = [five(at(10, 30), 13230, 13241, 13229, 13235), five(at(12, 20), 13230, 13241, 13229, 13235)]
    store = store_with(at(13, 0, 3), extra5=rej, extra1=hrs)
    assert check(tmp_path, store, at(10, 30), at(13, 1)).stp_key == f"{a}#t1"
    assert check(tmp_path, store, at(12, 20), at(13, 1)).stp_key == f"{a}#t2"


def test_TW1_06_delayed_publication_and_a_rejection_spanning_the_hour_boundary(tmp_path):
    created = at(10, 5, 3)                                                       # the re-plan five minutes late
    hrs = [hour(at(8), 13200, 13201, 13199, 13200), hour(at(9), 13230, 13241, 13229, 13235)]
    plans = Bi(SELL=[pd()])
    ok(tmp_path, store_with(created, extra1=hrs), plans).run(created)
    a = opps(tmp_path)[0]["id"]
    rej = [five(at(9, 55), 13230, 13241, 13229, 13235)]                          # pierce 09:55, trigger after 10:05
    store = store_with(at(10, 10), extra5=rej, extra1=hrs)
    assert check(tmp_path, store, at(9, 55), at(10, 10)).stp_key == f"{a}#t1"


def test_TW1_07_a_rejection_before_the_lineage_s_last_re_arm_is_a_distinct_earlier_test(tmp_path):
    created = at(12, 0, 3)
    hrs = [hour(at(9), 13230, 13241, 13229, 13235), hour(at(10), 13200, 13201, 13199, 13200),
           hour(at(11), 13230, 13241, 13229, 13235)]
    ok(tmp_path, store_with(created, extra1=hrs), Bi(SELL=[pd()])).run(created)
    a = opps(tmp_path)[0]["id"]
    rej = [five(at(9, 30), 13230, 13241, 13229, 13235), five(at(11, 30), 13230, 13241, 13229, 13235)]
    store = store_with(at(12, 5), extra5=rej, extra1=hrs)
    k_old = check(tmp_path, store, at(9, 30), at(12, 5)).stp_key
    k_new = check(tmp_path, store, at(11, 30), at(12, 5)).stp_key
    assert k_old == f"{a}#t0" and k_new == f"{a}#t1" and k_old != k_new


# ---- missing data never makes a new test -------------------------------------------------------------------------------

def test_TW1_08_an_incomplete_hourly_candle_cannot_re_arm_the_count(tmp_path):
    created = at(9, 0, 3)
    plans = Bi(SELL=[pd()])
    pre = [hour(at(8), 13230, 13241, 13229, 13235)]
    ok(tmp_path, store_with(created, extra1=pre), plans).run(created)
    a = opps(tmp_path)[0]["id"]
    gap = C("1h", at(9), 1, 13200, 13201, 13199, 13200)
    gap = type(gap)(**{**gap.__dict__, "parts": 9, "expected_parts": 12})      # 3 of its 12 candles missing
    hrs = pre + [gap, hour(at(10), 13230, 13241, 13229, 13235)]
    for h in (10, 11):
        t = at(h, 0, 3)
        ok(tmp_path, store_with(t, extra1=hrs), plans).run(t)
    rej = [five(at(10, 30), 13230, 13241, 13229, 13235)]
    store = store_with(at(11, 1), extra5=rej, extra1=hrs)
    lin = state(tmp_path)["lineages"][a]
    from planner.lineage import test_number
    assert test_number(KS(tmp_path), store, D("13240"), D("13250"),
                       lin["tests"], at(10, 30)) == 1                         # not 2: no re-arm from missing data
    assert "2026-11-17T09:00:00Z" in lin["tests"]["uncertain"]
    v = check(tmp_path, store, at(10, 30), at(11, 1))                          # WP3 (PD-5 B): nor any authorisation
    assert not v.allowed and "uncertain" in v.reasons[0]                       # until that hour is reconciled


# ---- C-3 / PD-2: the completed-opportunity duplicate rule on destination zones ------------------------------------------

def _completed(tmp, plans):
    run(tmp, NOW, plans, price=13236)
    run(tmp, at(9, 10), plans, price=13236)
    down = [five(at(9, 10), 13236, 13237, 13169, 13170)]
    run(tmp, at(9, 15), plans, price=13236, extra5=down)
    return down


@pytest.mark.parametrize("primary,issued", [(13169, False), (13166, False), (13170, False), (13150, True),
                                            (13164, True)])
def test_TW1_09_a_shifted_destination_overlapping_the_achieved_one_is_not_reissued(tmp_path, primary, issued):
    # pd's SELL destination zone is primary-5 to primary: 13165-13170 achieved. 13164 gives 13159-13164: no overlap
    plans = Bi(SELL=[pd(primary=13170), pd(primary=primary)])
    down = _completed(tmp_path, plans)
    t = at(10, 0, 3)
    run(tmp_path, t, plans, price=13236, extra5=down, extra1=near_hours(at(8), at(10)))
    assert bool(opps(tmp_path)) is issued
    if not issued:
        assert any(e["event"] == "duplicate" for e in ev(tmp_path))


def test_TW1_10_a_progressively_shifting_destination_never_chains_overlaps(tmp_path):
    plans = Bi(SELL=[pd(primary=13170), pd(primary=13166), pd(primary=13162)])
    down = _completed(tmp_path, plans)
    run(tmp_path, at(10, 0, 3), plans, price=13236, extra5=down, extra1=near_hours(at(8), at(10)))
    assert opps(tmp_path) == []                                   # 13161-13166 overlaps 13165-13170: not reissued
    run(tmp_path, at(11, 0, 3), plans, price=13236, extra5=down, extra1=near_hours(at(8), at(11)))
    assert len(opps(tmp_path)) == 1                               # 13157-13162 does not overlap the ACHIEVED 13165-13170


# ---- C-4 / PD-3: overlapping parallel publication; edges; rollover; BUY and SELL ---------------------------------------

def _other(zone, trade="SELL"):
    lv = [("hourly swing high", str(zone[0] + 1), True)] if trade == "SELL" else [("hourly swing low", str(zone[1] - 1), True)]
    return pd(trade, zone, levels=lv, primary=13170 if trade == "SELL" else 13320)


def test_TW1_11_an_overlapping_same_direction_publication_shares_the_live_lineage(tmp_path):
    plans = Bi(SELL=[pd(), _other((13242, 13252))])
    run(tmp_path, NOW, plans)
    run(tmp_path, at(10, 0, 3), plans)
    o = sorted(opps(tmp_path), key=lambda x: x["created_utc"])
    assert len(o) == 2 and o[1]["lineage"] == o[0]["id"]


def test_TW1_12_zones_that_merely_share_an_edge_keep_separate_lineages(tmp_path):
    plans = Bi(SELL=[pd(), _other((13250, 13260))])
    run(tmp_path, NOW, plans)
    run(tmp_path, at(10, 0, 3), plans)
    o = sorted(opps(tmp_path), key=lambda x: x["created_utc"])
    assert len(o) == 2 and o[1]["lineage"] == o[1]["id"] != o[0]["lineage"]


def test_TW1_13_buy_and_sell_at_the_same_zone_have_separate_lineages(tmp_path):
    plans = Bi(SELL=[pd(zone=(13240, 13250))], BUY=[pd("BUY", (13240, 13250))])
    run(tmp_path, NOW, plans)
    o = opps(tmp_path)
    assert {x["trade"] for x in o} == {"SELL", "BUY"} and len({x["lineage"] for x in o}) == 2


def test_TW1_14_the_rollover_successor_continues_the_lineage_of_the_one_it_replaced(tmp_path):
    late = T(2026, 11, 17, 23, 0, 3)
    keep = {"levels": [{"name": "daily R2", "price": "13243.7"}, {"name": "hourly swing high", "price": "13243.2"}]}
    ok(tmp_path, store_with(late, 13236), Bi(SELL=[pd(structure=keep)])).run(late)
    a = opps(tmp_path)[0]["id"]
    t = T(2026, 11, 18, 0, 0, 3)
    rolled = {"levels": [{"name": "daily R2", "price": "13246.0"}, {"name": "hourly swing high", "price": "13243.2"}]}
    nxt = pd(levels=[("daily R2", "13246.0", True), ("hourly swing high", "13243.2", True)], structure=rolled)
    ok(tmp_path, store_with(t, 13236), Bi(SELL=[nxt])).run(t)
    o = opps(tmp_path)
    assert any("structural levels changed" in (e.get("why") or "") and e["id"] == a for e in ev(tmp_path))
    assert len(o) == 1 and o[0]["id"] != a and o[0]["lineage"] == a


# ---- several lineages under one rejection; restart ---------------------------------------------------------------------

def test_TW1_15_a_rejection_reaching_two_lineages_consumes_both_keys(tmp_path):
    plans = Bi(SELL=[pd(zone=(13240, 13250)), _other((13250, 13260))])
    run(tmp_path, NOW, plans)
    run(tmp_path, at(10, 0, 3), plans)
    o = sorted(opps(tmp_path), key=lambda x: x["created_utc"])
    rej = [five(at(10, 10), 13240, 13252, 13239, 13245)]                       # reaches both zones
    store = store_with(at(10, 20), extra5=rej)
    v = check(tmp_path, store, at(10, 10), at(10, 20))
    parts = set(v.signal.split("|"))
    assert {f"{o[0]['lineage']}#t1", f"{o[1]['lineage']}#t1"} <= parts
    rej2 = [five(at(10, 15), 13250, 13253, 13249, 13251)]                      # later: only the upper zone
    v2 = check(tmp_path, store_with(at(10, 25), extra5=rej + rej2), at(10, 15), at(10, 25))
    assert v2.allowed and rule11(used_from(v.signal))(v2.signal)               # the same test of the upper lineage


def test_TW1_16_a_restart_keeps_the_lineage_registry_and_counts_each_hour_once(tmp_path):
    plans = Bi(SELL=[pd()])
    run(tmp_path, NOW, plans, price=13236)
    a = opps(tmp_path)[0]["id"]
    t = at(10, 0, 3)
    run(tmp_path, t, plans, price=13236)
    before = state(tmp_path)["lineages"][a]["tests"]
    run(tmp_path, t, plans, price=13236)                                       # the same step again (a restart)
    assert state(tmp_path)["lineages"][a]["tests"] == before


# ---- PD-4: historical keys reconciled by an auditable map --------------------------------------------------------------

def test_TW1_17_a_mapped_alias_key_is_protected_as_well(tmp_path):
    plans = Bi(SELL=[pd()])
    run(tmp_path, NOW, plans, price=13236)
    a = opps(tmp_path)[0]["id"]
    path = tmp_path / "planner" / "GBPUSD" / "lineage_map.json"
    m = {"version": 1, "lineages": {a: {"trade": "SELL", "aliases": {"1": ["OLD-ID#t1"]}}},
         "opportunity_lineage": {a: a}}
    path.write_text(json.dumps(m))
    run(tmp_path, at(9, 10), plans, price=13236)
    store = store_with(at(9, 15), 13236)
    v = check(tmp_path, store, at(9, 5), at(9, 15))
    assert v.allowed and "OLD-ID#t1" in v.signal.split("|")
    assert rule11(used_from("OLD-ID#t1"))(v.signal)


def test_TW1_18_alias_keys_survive_a_restart_and_an_unresolved_submission_holding_one_refuses(tmp_path):
    """PD-4: after the map is applied, a fresh tracker process (restart) still carries the alias in its own state, and
    an order sent with the old key but never settled at IG (Phase 1: unresolved, counted by rule 11) refuses the test."""
    from orders.sender import OrderSender
    plans = Bi(SELL=[pd()])
    run(tmp_path, NOW, plans, price=13236)
    a = opps(tmp_path)[0]["id"]
    (tmp_path / "planner" / "GBPUSD" / "lineage_map.json").write_text(json.dumps(
        {"version": 1, "lineages": {a: {"trade": "SELL", "aliases": {"1": ["OLD-ID#t1"]}}}, "opportunity_lineage": {}}))
    run(tmp_path, at(9, 10), plans, price=13236)
    (tmp_path / "planner" / "GBPUSD" / "lineage_map.json").unlink()          # the file gone: the state keeps it
    for m in (15, 20):                                                         # two more processes (restarts)
        run(tmp_path, at(9, m), plans, price=13236)
    assert state(tmp_path)["lineages"][a]["aliases"] == {"1": ["OLD-ID#t1"]}
    v = check(tmp_path, store_with(at(9, 25), 13236), at(9, 5), at(9, 25))
    assert v.allowed and "OLD-ID#t1" in v.signal.split("|")
    used = OrderSender.used_signals(SimpleNamespace(trades={}, unresolved={
        "AB-unsettled": {"signal": "OLD-ID#t1", "strategy": "Bollinger bounce 5m"}}))
    assert rule11(used)(v.signal) == ["same signal already traded by Bollinger bounce 5m"]


def test_TW1_19_after_a_re_arm_a_republication_toward_the_achieved_destination_is_a_new_test_and_is_issued(tmp_path):
    """Review of fec364b: the completed-opportunity duplicate rule withholds a republication only while the zone has
    not re-armed since the completion (D-25 / P-C8: a complete hourly candle wholly clear of it)."""
    plans = Bi(SELL=[pd(primary=13170), pd(primary=13170), pd(primary=13170)])
    down = _completed(tmp_path, plans)
    run(tmp_path, at(10, 0, 3), plans, price=13236, extra5=down, extra1=near_hours(at(8), at(10)))
    assert opps(tmp_path) == []                                   # no re-arm yet: withheld
    hrs = near_hours(at(8), at(10)) + [hour(at(10), 13200, 13201, 13199, 13200)] + near_hours(at(11), at(12))
    run(tmp_path, at(12, 0, 3), plans, price=13236, extra5=down, extra1=hrs)    # 10:00 wholly clear: re-armed
    o = opps(tmp_path)
    assert len(o) == 1 and o[0]["lineage"] != o[0]["id"]           # issued, in the same lineage, as a new test
