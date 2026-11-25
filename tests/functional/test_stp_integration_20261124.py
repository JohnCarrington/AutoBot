"""Functional tests for the STP strategy integration (owner, 24 November 2026; docs/design/
STP_STRATEGY_INTEGRATION_20261124.md section 14): the 24 November journey, the alternative resolutions FT-A1 to FT-A18
and the hourly publication race FT-R1.

  * The journey runs STP's real tracker and planner (planner/opportunities.py, planner/assess.py, both directions)
    over the recorded 24 November candles, after every 5-minute candle as the price service does, and checks every
    expectation as of its time (no later data is used: the tracker only ever sees the store up to its run).
  * The alternatives are CONSTRUCTED: scripted candles at 24 November's real zone prices (sell prices, points).
  * FT-R1 drives the real engine's live path (trading/engine.py: _live_entries, _place, the real authorisation check,
    the order sender in paper mode with a pretend IG) with constructed ticks around the 18:00 publication.
  * The full wired path over the recorded day (FT-A15, FT-A16, FT-A18: the analyser, all strategies, the entry
    filters, safety rules, paper orders, trade manager), switches off and on, takes several minutes: it runs when
    STP_FULL_REPLAY=1 (run for the readiness pack; docs/design/stp_strategy_integration_20261124/implementation/).
No profit or loss is evaluated anywhere; IG is never contacted."""

from __future__ import annotations

import json
import os
from datetime import timedelta
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace

import pytest

from planner.keeper import COMPLETED, INVALIDATED, WAITING
from planner.opportunities import ACTIVE, BROKEN, OpportunityKeeper
from stp.authorise import authorise
from tests.technical.test_planner import C, T
from tests.technical.test_stp_integration import (AT, Bi, KS, auth_settings, auth_state, ev, five, hour, ok, opp,
                                                  opps, pd, src, store_with)

LIVE = Path("/opt/autobot/data/candles/GBPUSD/5m/2026-11-24.csv")
needs_live = pytest.mark.skipif(not LIVE.exists(), reason="the recorded 24 November candles are not on this machine")
full = pytest.mark.skipif(os.environ.get("STP_FULL_REPLAY") != "1" or not LIVE.exists(),
                          reason="the full wired-path replay runs with STP_FULL_REPLAY=1 (several minutes)")


# ---- the 24 November journey (STP's real tracker and planner on the recorded candles) -----------------------------

@pytest.fixture(scope="module")
def journey(tmp_path_factory):
    from tests.stp.harness import Over, live_settings, live_store, run_tracker, events
    tmp = tmp_path_factory.mktemp("journey")
    s = Over(live_settings(tmp, stp_opportunities=True, stp_bidirectional=True), tmp)
    store = live_store(s)
    snaps = run_tracker(s, store, T(2026, 11, 23, 23, 55), T(2026, 11, 24, 20, 55))
    return SimpleNamespace(s=s, snaps=snaps, events=events(s), tmp=tmp)


def _at(j, hhmm):
    """current.json as the tracker wrote it at the run after the candle ending hh:mm (24 November)."""
    want = f"2026-11-24T{hhmm}"
    return next(x for x in j.snaps if x["written_utc"].startswith(want))


def _find(snap, trade, low, high):
    return [o for o in snap["opportunities"] if o["trade"] == trade and o["entry_zone"]["low"] == low
            and o["entry_zone"]["high"] == high]


@needs_live
def test_FT_journey_00_00_the_rollover_ends_the_zone_on_yesterdays_pivots(journey):
    e = [x for x in journey.events if x["time_utc"].startswith("2026-11-24T00:00") and x["event"] == "invalidated"]
    assert e and "structural levels changed" in e[0]["why"] and "daily S2 13062.0" in e[0]["why"]


@needs_live
def test_FT_journey_08_00_a_new_forecast_does_not_end_the_00_00_sell(journey):
    # recorded live (single tracker): 0000-17 INVALIDATED at 08:00 "supporting evidence changed" (a nearer Major zone
    # 13026.6-13037.3 appeared and was reached); its own primary 13016.9 was not. OD-02: it is kept.
    o = _find(_at(journey, "08:00"), "SELL", "13075", "13084.1")
    assert o and o[0]["status"] == WAITING and o[0]["destinations"]["primary"]["price"] == "13016.9"


@needs_live
def test_FT_journey_10_00_a_sell_and_a_buy_at_the_same_pivot_zone(journey):
    snap = _at(journey, "10:00")
    assert _find(snap, "SELL", "13062.1", "13071.5") and _find(snap, "BUY", "13062.1", "13071.5")     # OD-33
    assert _find(snap, "SELL", "13075", "13084.1")                                                    # H11: kept


@needs_live
def test_FT_journey_11_00_the_pivot_buy_completes_and_12_00_breaks_the_sells_then_15_00_ends_them(journey):
    assert not _find(_at(journey, "11:05"), "BUY", "13062.1", "13071.5")
    assert any(x["event"] == "completed" and x["time_utc"].startswith("2026-11-24T11:05") for x in journey.events)
    at12 = _at(journey, "12:00")
    assert [o["status"] for o in _find(at12, "SELL", "13062.1", "13071.5")] == [BROKEN]
    assert [o["status"] for o in _find(at12, "SELL", "13075", "13084.1")] == [BROKEN]
    at15 = _at(journey, "15:00")
    assert not _find(at15, "SELL", "13062.1", "13071.5") and not _find(at15, "SELL", "13075", "13084.1")
    held = [x for x in journey.events if x["time_utc"].startswith("2026-11-24T15:00") and "break held" in (x.get("why") or "")]
    assert len(held) == 2


@needs_live
def test_FT_journey_12_00_stp_proposes_the_continuation_buy_at_the_broken_resistance(journey):
    b = _find(_at(journey, "12:00"), "BUY", "13075", "13085.4")
    assert b and b[0]["relation_to_h4"] == "against" and b[0]["destinations"]["primary"]["price"] == "13135.5"


@needs_live
def test_FT_journey_r1_sell_is_kept_through_15_00_and_17_00_breaks_at_18_00_and_returns_at_19_00(journey):
    for hhmm in ("14:10", "15:00", "17:00"):
        r1 = _find(_at(journey, hhmm), "SELL", "13103", "13114.1")
        assert r1 and r1[0]["status"] == ACTIVE, hhmm                                              # H11, H18
    r1 = _find(_at(journey, "18:00"), "SELL", "13103", "13114.1")
    assert r1 and r1[0]["status"] == BROKEN
    r1b = [o for o in _at(journey, "19:00")["opportunities"] if o["id"] == r1[0]["id"]]
    assert r1b and r1b[0]["status"] == ACTIVE                                                    # OD-31, same id
    assert (r1b[0]["entry_zone"]["low"], r1b[0]["entry_zone"]["high"]) == ("13102.6", "13114.1")   # STP's 19:00 re-plan


@needs_live
def test_FT_journey_17_00_weekly_pivot_sell_and_18_00_buy_at_the_same_zone(journey):
    s17 = _find(_at(journey, "17:10"), "SELL", "13117.6", "13128.6")
    assert s17 and s17[0]["status"] == ACTIVE and s17[0]["invalidation"]["zone_break_close"] == "13131.6"
    b18 = _find(_at(journey, "18:00"), "BUY", "13119.1", "13128.6")
    assert b18 and b18[0]["created_utc"] == "2026-11-24T18:00:03Z"


@needs_live
def test_FT_journey_nothing_ends_for_a_new_forecast_a_direction_change_or_time(journey):
    whys = [x.get("why") or "" for x in journey.events if x["event"] == "invalidated"]
    assert not any("supporting evidence changed" in w or "4-hour direction changed" in w for w in whys)
    assert all(any(k in w for k in ("structural levels changed", "break held", "destination reached before entry",
                                    "structure break")) for w in whys)


# ---- the alternative resolutions (CONSTRUCTED, at 24 November's real prices) --------------------------------------

R1 = (13103, 13114.1)            # 1400-21's R1 zone, SELL; zone break 13117.1, primary 13085.4 (scripted below)


def _r1_plan(**kw):
    return pd("SELL", zone=R1, primary=13085.4, levels=[("daily R1", "13114.1", True), ("hourly swing low", "13103", True)],
              **kw)


def test_FT_A1_a_confirmed_bearish_reversal_at_r1_is_one_authorised_sell_then_completes(tmp_path):
    o = opp("SELL", R1, primary=13085.4, levels=[("daily R1", "13114.1", True)], status=ACTIVE)
    st, s = auth_state(o), auth_settings(tmp_path)
    rej = T(2026, 11, 17, 9, 40)
    store = _store(extra5=[five(rej, 13108, 13115, 13105, 13106)])
    v = authorise(s, store, _idea("sell", rej, "13104"), AT, src(st))
    assert v.allowed and v.stp_key.endswith("#t1")
    ok(tmp_path, store_with(T(2026, 11, 17, 9)), Bi(SELL=[_r1_plan()])).run(T(2026, 11, 17, 9))
    t = T(2026, 11, 17, 9, 20)
    path = [five(T(2026, 11, 17, 9, 5), 13100, 13105, 13099, 13104), five(T(2026, 11, 17, 9, 10), 13104, 13104, 13085, 13086)]
    ok(tmp_path, store_with(t, 13100, extra5=path), Bi(SELL=[_r1_plan()])).run(t)
    assert opps(tmp_path) == [] and any(x["event"] == "completed" for x in ev(tmp_path))


def test_FT_A2_a_held_breakout_ends_the_sell_and_only_stps_own_buy_proposal_authorises_the_retest(tmp_path):
    t0 = T(2026, 11, 17, 9)
    buy_r1 = pd("BUY", zone=R1, primary=13135.5, levels=[("daily R1", "13114.1", True), ("hourly swing low", "13103", True)])
    plans = Bi(SELL=[_r1_plan()] + [_r1_plan(no_rec="above the zone now")] * 9, BUY=[pd("BUY", no_rec="x")] * 4 + [buy_r1])
    ok(tmp_path, store_with(t0, 13110), plans).run(t0)
    extra = []
    for k, close in enumerate([13120.4, 13121, 13122, 13123], start=1):          # broken, held three closes
        t = t0 + timedelta(hours=k)
        extra.append(hour(t - timedelta(hours=1), 13115, close + 1, 13114, close))
        ok(tmp_path, store_with(t, 13121, extra1=extra), plans).run(t)
    o = opps(tmp_path)
    assert [x["trade"] for x in o] == ["BUY"] and o[0]["entry_zone"]["low"] == "13103"
    assert any("break held" in (x.get("why") or "") for x in ev(tmp_path))
    st, s = auth_state(*[dict(x) for x in o]), auth_settings(tmp_path)
    rej = T(2026, 11, 17, 9, 45)
    store = _store(extra5=[five(rej, 13118, 13119, 13112, 13117)])
    assert authorise(s, store, _idea("buy", rej, "13118"), AT, src(st)).allowed                # BUY retest at R1
    assert not authorise(s, store, _idea("sell", rej, "13112"), AT, src(st)).allowed           # the SELL: refused


def test_FT_A2b_a_breakout_without_an_stp_buy_proposal_gives_no_buy(tmp_path):
    st, s = auth_state(opp("SELL", R1, status=BROKEN)), auth_settings(tmp_path)
    rej = T(2026, 11, 17, 9, 45)
    v = authorise(s, _store(extra5=[five(rej, 13118, 13119, 13112, 13117)]), _idea("buy", rej, "13118"), AT, src(st))
    assert not v.allowed and "no live STP BUY opportunity" in v.reasons[0]


def test_FT_A3_several_unsuccessful_rejections_leave_watch_and_wait(tmp_path):
    w = (13117.6, 13128.6)
    plan = pd("SELL", zone=w, primary=13084.1, levels=[("weekly pivot", "13127.3", True)])
    t0 = T(2026, 11, 17, 9)
    ok(tmp_path, store_with(t0, 13115), Bi(SELL=[plan])).run(t0)
    fails = [five(t0 + timedelta(minutes=5 * k), 13116, 13124, 13115, 13121 if k % 2 else 13117) for k in range(1, 13)]
    t = t0 + timedelta(hours=1)
    ok(tmp_path, store_with(t, 13118, extra5=fails), Bi(SELL=[plan])).run(t)
    assert [x["status"] for x in opps(tmp_path)] == [ACTIVE]


def test_FT_A4_a_wick_beyond_the_zone_break_closing_inside_does_not_invalidate(tmp_path):
    t0 = T(2026, 11, 17, 9)
    ok(tmp_path, store_with(t0, 13110), Bi(SELL=[_r1_plan()])).run(t0)
    t = t0 + timedelta(hours=1)
    ok(tmp_path, store_with(t, 13110, extra1=[hour(t0, 13110, 13133, 13108, 13112)]), Bi(SELL=[_r1_plan()])).run(t)
    o = opps(tmp_path)
    assert [x["status"] for x in o] in ([WAITING], [ACTIVE]) and any(x["event"] == "wick sweep" for x in ev(tmp_path))


def test_FT_A4b_a_close_beyond_and_back_returns_to_watch_and_wait(tmp_path):
    t0 = T(2026, 11, 17, 9)
    ok(tmp_path, store_with(t0, 13110), Bi(SELL=[_r1_plan()])).run(t0)
    h = [hour(t0, 13110, 13121, 13108, 13120)]
    ok(tmp_path, store_with(t0 + timedelta(hours=1), 13115, extra1=h), Bi(SELL=[_r1_plan()])).run(t0 + timedelta(hours=1))
    assert opps(tmp_path)[0]["status"] == BROKEN
    h.append(hour(t0 + timedelta(hours=1), 13120, 13121, 13110, 13112))
    ok(tmp_path, store_with(t0 + timedelta(hours=2), 13112, extra1=h), Bi(SELL=[_r1_plan()])).run(t0 + timedelta(hours=2))
    assert opps(tmp_path)[0]["status"] == ACTIVE


def test_FT_A4c_a_break_held_for_three_closes_ends_it(tmp_path):
    t0 = T(2026, 11, 17, 9)
    plans = Bi(SELL=[_r1_plan()] + [_r1_plan(no_rec="x")] * 9)
    ok(tmp_path, store_with(t0, 13110), plans).run(t0)
    h = []
    for k in range(1, 5):
        h.append(hour(t0 + timedelta(hours=k - 1), 13118, 13123, 13117, 13121))
        ok(tmp_path, store_with(t0 + timedelta(hours=k), 13121, extra1=h), plans).run(t0 + timedelta(hours=k))
    assert opps(tmp_path) == [] and any("break held" in (x.get("why") or "") for x in ev(tmp_path))


@pytest.mark.parametrize("high,allowed", [(13115.0, True), (13114.0, False)])
def test_FT_A5_a_rejection_just_short_2_6_pips_is_authorised_3_6_is_not(tmp_path, high, allowed):
    w = (13117.6, 13128.6)
    st, s = auth_state(opp("SELL", w, primary=13084.1, levels=[])), auth_settings(tmp_path)
    rej = T(2026, 11, 17, 9, 40)
    v = authorise(s, _store(extra5=[five(rej, 13108, high, 13105, 13109)]), _idea("sell", rej, "13104"), AT, src(st))
    assert v.allowed is allowed


def test_FT_A6_a_4_hour_close_beyond_the_structure_break_invalidates_the_sells(tmp_path):
    t0 = T(2026, 11, 17, 8)
    h4a = C("4h", t0 - timedelta(hours=4), 4, 13110, 13115, 13100, 13110)
    ok(tmp_path, store_with(t0, 13110, h4=[h4a]), Bi(SELL=[_r1_plan()])).run(t0)
    t = t0 + timedelta(hours=4)
    h4b = C("4h", t0, 4, 13110, 13160, 13100, 13155)                     # structure break 13154.1 (13114.1 + 40)
    ok(tmp_path, store_with(t, 13110, h4=[h4a, h4b]), Bi(SELL=[_r1_plan(no_rec="x")])).run(t)
    assert opps(tmp_path) == [] and any("structure break" in (x.get("why") or "") for x in ev(tmp_path))


def test_FT_A7_sixty_candles_inside_without_confirmation_no_expiry_no_trade(tmp_path):
    t0 = T(2026, 11, 17, 9)
    ok(tmp_path, store_with(t0, 13108), Bi(SELL=[_r1_plan()])).run(t0)
    t = t0 + timedelta(hours=5)
    ok(tmp_path, store_with(t, 13110), Bi(SELL=[_r1_plan()])).run(t)
    assert [x["status"] for x in opps(tmp_path)] == [ACTIVE] and not any(x["event"] == "invalidated" for x in ev(tmp_path))


def test_FT_A8_newer_higher_zones_are_all_held_and_bind_by_interaction(tmp_path):
    a = opp("SELL", R1, oid="R1", levels=[])
    b = opp("SELL", (13135.5, 13142.1), oid="1500", levels=[], created=T(2026, 11, 17, 9))
    c = opp("SELL", (13117.6, 13128.6), oid="1700", levels=[], created=T(2026, 11, 17, 9, 30))
    st, s = auth_state(a, b, c), auth_settings(tmp_path)
    rej = T(2026, 11, 17, 9, 40)
    v = authorise(s, _store(extra5=[five(rej, 13120, 13126, 13119, 13121)]), _idea("sell", rej, "13118"), AT, src(st))
    assert v.allowed and v.opportunity["id"] == "1700"


def test_FT_A9_two_strategies_on_one_opportunity_give_one_trade(tmp_path):
    st, s = auth_state(opp("SELL", R1, levels=[])), auth_settings(tmp_path)
    rej = T(2026, 11, 17, 9, 40)
    store = _store(extra5=[five(rej, 13108, 13115, 13105, 13106)])
    a = authorise(s, store, _idea("sell", rej, "13104"), AT, src(st))
    b = authorise(s, store, _idea("sell", rej, "13104", strategy="level reversal"), AT, src(st))
    from safety.rules import _one_signal
    refused = _one_signal(SimpleNamespace(switches=SimpleNamespace(one_signal_one_trade=True)),
                          SimpleNamespace(context={"signal": b.signal}), {a.signal: "Bollinger bounce 5m"})
    assert a.signal == b.signal and refused


def test_FT_A10_destination_before_entry_and_an_intrabar_touch_that_reverses(tmp_path):
    o = opp("SELL", (13117.6, 13128.6), primary=13084.1, levels=[])
    st, s = auth_state(o), auth_settings(tmp_path)
    rej = T(2026, 11, 17, 9, 40)
    store = _store(extra5=[five(rej, 13110, 13118, 13108, 13112)])
    partial = five(T(2026, 11, 17, 10, 0), 13100, 13101, 13084, 13099)     # touched 13084.1 and came back
    v = authorise(s, store, _idea("sell", rej, "13104"), AT, src(st), partial=partial)
    assert not v.allowed and "forming 5-minute candle" in v.reasons[0]


def test_FT_A11_an_open_position_is_never_touched_by_stp():
    import inspect
    import trade_manager.manager as tm
    text = inspect.getsource(tm)
    assert "planner" not in text and "stp." not in text and "opportunit" not in text


def test_FT_A12_session_close_and_rollover(tmp_path):
    late = T(2026, 11, 24, 23, 0)
    keep = {"levels": [{"name": "daily R1", "price": "13114.1"}, {"name": "hourly swing low", "price": "13103"}]}
    ok(tmp_path, store_with(late, 13110), Bi(SELL=[_r1_plan(structure=keep)])).run(late)
    t = T(2026, 11, 25, 0, 0)
    rolled = {"levels": [{"name": "daily R1", "price": "13135.0"}, {"name": "hourly swing low", "price": "13103"}]}
    ok(tmp_path, store_with(t, 13110), Bi(SELL=[_r1_plan(no_rec="x", structure=rolled)])).run(t)
    assert opps(tmp_path) == [] and any("structural levels changed" in (x.get("why") or "") for x in ev(tmp_path))


def test_FT_A13_stale_data_mid_interaction_refuses_and_resumes_on_fresh_data(tmp_path):
    o = opp("SELL", R1, levels=[])
    s = auth_settings(tmp_path)
    rej = T(2026, 11, 17, 9, 40)
    store = _store(extra5=[five(rej, 13108, 13115, 13105, 13106)])
    stale = auth_state(o, written=AT - timedelta(minutes=12))
    assert not authorise(s, store, _idea("sell", rej, "13104"), AT, src(stale)).allowed
    assert authorise(s, store, _idea("sell", rej, "13104"), AT, src(auth_state(o))).allowed


def test_FT_A14_a_restart_mid_test_keeps_the_state_and_the_test_count(tmp_path):
    t0 = T(2026, 11, 17, 9)
    ok(tmp_path, store_with(t0, 13110), Bi(SELL=[_r1_plan()])).run(t0)
    before = opps(tmp_path)
    again = OpportunityKeeper(KS(tmp_path), store_with(t0, 13110), planner=Bi(SELL=[_r1_plan()]))
    assert [x["id"] for x in again.opportunities] == [x["id"] for x in before]
    assert [x["lineage"] for x in again.opportunities] == [x["lineage"] for x in before]


def test_FT_A17_touched_opportunities_are_shown_as_watch_and_wait(tmp_path):
    t0 = T(2026, 11, 17, 9)
    ok(tmp_path, store_with(t0, 13108), Bi(SELL=[_r1_plan()])).run(t0)
    t = t0 + timedelta(minutes=10)
    ok(tmp_path, store_with(t, 13108), Bi(SELL=[_r1_plan()])).run(t)
    assert opps(tmp_path)[0]["label"] == "Watch & Wait"
    from dashboard.stp import opportunities
    shown = opportunities(json.loads((tmp_path / "planner" / "GBPUSD" / "current.json").read_text()),
                          SimpleNamespace(zone=lambda a, b: f"{a}-{b}", real=lambda x: str(x)))
    assert shown[0]["label"] == "Watch & Wait" and shown[0]["authorises"] is True


# ---- FT-R1: the hourly publication race at 18:00 (the real engine's live path, constructed ticks) ----------------

PUBLISHED = T(2026, 11, 24, 18, 0, 3)
REJ = T(2026, 11, 24, 17, 50)                       # the R1 retest from above: low 13118.3 (recorded 17:50 candle)


def _store(extra5=(), until=None):
    from tests.technical.test_stp_integration import auth_store
    return auth_store(extra5=extra5) if until is None else auth_store(extra5=extra5, until=until)


def _idea(direction, rej, price, strategy="Bollinger bounce 5m"):
    return SimpleNamespace(strategy=strategy, direction=direction, time=AT, entry_price=D(price),
                           context={"rejection_candle": rej.strftime("%Y-%m-%dT%H:%M:%SZ")})


def _race_store():
    from tests.planner_helpers import FakeStore
    fives = [five(T(2026, 11, 24, 17, 0) + timedelta(minutes=5 * k), 13120, 13121, 13119, 13120) for k in range(12)]
    fives[10] = five(REJ, 13118.4, 13121.3, 13118.3, 13119.6)
    hours = [hour(T(2026, 11, 24, h), 13115, 13121, 13110, 13120) for h in range(10, 18)]
    return FakeStore({"5m": fives, "1h": hours, "4h": []})


def _b1800():
    o = opp("BUY", (13119.1, 13128.6), oid="STP-GBPUSD-20261124-1800-11", primary=13135.5, levels=[],
            created=PUBLISHED)
    o["destinations"]["primary"]["zone"] = {"low": "13135.5", "high": "13142.1"}
    return o


def _states():
    f = lambda t: t.strftime("%Y-%m-%dT%H:%M:%SZ")      # noqa: E731
    before = {"opportunities": [], "written_utc": f(T(2026, 11, 24, 17, 55, 3)), "m5_checked_until": f(T(2026, 11, 24, 17, 55)),
              "validated_h1_end": f(T(2026, 11, 24, 17, 0)), "h4_checked_until": f(T(2026, 11, 24, 16, 0)),
              "current": True, "data_fresh": True, "not_current_reasons": []}     # as the tracker marks a current run
    after = dict(before, opportunities=[_b1800()], written_utc=f(PUBLISHED), m5_checked_until=f(T(2026, 11, 24, 18, 0)),
                 validated_h1_end=f(T(2026, 11, 24, 18, 0)))
    return before, after


def _race_engine(monkeypatch, tmp_path, clock):
    """The real engine (trading/engine.py) with a scripted analyser and strategies: the 5m bounce BUY whose trigger
    13120.7 the forming 18:00 candle reaches; the real STP check, entry filters, order sender (paper) and safety rules."""
    from tests.technical import test_trading as tt
    from trading import engine as eng
    from tests.technical.test_orders import Over as OOver
    from config.settings_loader import load_settings
    from tests.stp.harness import LIVE_SWITCHES_20261124
    p = tmp_path / "switches.env"
    p.write_text(LIVE_SWITCHES_20261124 + "STP_OPPORTUNITIES=on\nSTP_BIDIRECTIONAL=on\nSTP_AUTHORISES_ENTRIES=on\n"
                 .replace("HOURLY_CONTEXT=on", "HOURLY_CONTEXT=off"))
    base = load_settings(switches_from=p).for_pair("GBPUSD")
    sw = {k: v for k, v in vars(base.switches).items() if not k.startswith("_")} | {
        "hourly_context": False, "rsi_stretch": False, "counter_trend_tiring": False, "trading": False}
    S = OOver(base, switches=sw, orders={"folder": tmp_path / "orders"}, trade_manager={"folder": tmp_path / "tm"},
              safety={"folder": tmp_path / "safety"}, records={"folder": tmp_path / "records"},
              trading={"pause_file": tmp_path / "control" / "pause"}, dashboard={"status_folder": tmp_path / "status"})
    before, after = _states()
    source = SimpleNamespace(state_at=lambda t=None: after if clock["t"] >= PUBLISHED else before,
                             version=lambda t=None: "after" if clock["t"] >= PUBLISHED else "before")
    store = _race_store()

    class Runner(tt.PretendRunner):
        stp = source

        def stp_version(self):
            return source.version()

        def levels_at(self, t, memo=None):
            return None

        def peek(self, partial, levels=None):
            out = super().peek(partial, levels)
            for i in out:
                i.context = {"rejection_candle": REJ.strftime("%Y-%m-%dT%H:%M:%SZ")}
            return out

    tracker = tt.PretendTracker([])
    tracker.week_open = T(2026, 11, 22, 22, 0)
    monkeypatch.setattr(eng, "StateTracker", lambda s, memo: tracker)
    monkeypatch.setattr(eng, "MemoStore", lambda st: st)
    live = {T(2026, 11, 24, 18, 0): [("Bollinger bounce 5m", "buy", D("13120.7"))]}
    monkeypatch.setattr(eng, "StrategyRunner", lambda s, memo, tr, hourly_end=None: Runner(tr, {}, live))
    monkeypatch.setattr(eng, "trend_day_at", lambda s, st, t: SimpleNamespace(direction=None))
    monkeypatch.setattr(eng, "day_directions", lambda *a, **k: None)
    alerts = SimpleNamespace(problem=lambda k, t: None, info=lambda t, key=None, html=False: None,
                             trade_opened=lambda t: None, trade_closed=lambda c: None)
    e = eng.Trading(S, store, tt.PretendIG(), alerts, trading_on=False, now=lambda: clock["t"],
                    quote=lambda: (D("13120.7"), D("13121.9")), calendar=[], sleep=lambda s: None)
    e.start(T(2026, 11, 24, 17, 59))
    e.ready = True
    return e


def _tick(t, sell):
    return SimpleNamespace(time=t, sell=D(str(sell)), buy=D(str(sell)) + D("1.2"))


def _decisions(tmp_path):
    out = []
    for p in (tmp_path / "records").rglob("decisions.jsonl"):
        out += [json.loads(x) for x in p.read_text().splitlines()]
    return out


def test_FT_R1_a_trigger_before_publication_is_refused_and_never_retried_or_sent_later(monkeypatch, tmp_path):
    clock = {"t": T(2026, 11, 24, 18, 0, 1)}
    e = _race_engine(monkeypatch, tmp_path, clock)
    e.on_price(_tick(clock["t"], "13120.8"))                       # R1-a: the trigger at 18:00:01, before 18:00:03
    for sec in (5, 30, 120, 290):                                  # later ticks in the same candle, after publication
        clock["t"] = T(2026, 11, 24, 18, 0, 0) + timedelta(seconds=sec)
        e.on_price(_tick(clock["t"], "13121.0"))
    d = _decisions(tmp_path)
    assert [x["kind"] for x in d if x["kind"] in ("STP refused", "STP authorised")] == ["STP refused"]
    assert not e.opened and not e.sender.unresolved                # R1-f: nothing opened, nothing queued


def test_FT_R1_b_c_a_trigger_after_publication_is_authorised_against_the_new_buy(monkeypatch, tmp_path):
    clock = {"t": T(2026, 11, 24, 18, 0, 5)}
    e = _race_engine(monkeypatch, tmp_path, clock)
    e.on_price(_tick(clock["t"], "13120.8"))                       # R1-b/c: the setup was in progress at 18:00:03
    d = _decisions(tmp_path)
    auth = [x for x in d if x["kind"] == "STP authorised"]
    assert len(auth) == 1 and auth[0]["opportunity"] == "STP-GBPUSD-20261124-1800-11"
    assert auth[0]["signal"] == "STP-GBPUSD-20261124-1800-11#t1" and len(e.opened) == 1


def test_FT_R1_d_a_new_setup_after_publication_is_considered_normally(tmp_path):
    before, after = _states()
    s = auth_settings(tmp_path)
    rej = T(2026, 11, 24, 18, 30)
    from tests.planner_helpers import FakeStore
    st = _race_store()
    st.by_tf["5m"] += [five(T(2026, 11, 24, 18, 0) + timedelta(minutes=5 * k), 13121, 13122, 13120, 13121) for k in range(8)]
    st.by_tf["5m"] = sorted({c.start: c for c in st.by_tf["5m"]}.values(), key=lambda c: c.start)
    st.by_tf["5m"] = [c if c.start != rej else five(rej, 13121.0, 13122.0, 13119.0, 13121.3) for c in st.by_tf["5m"]]
    at = T(2026, 11, 24, 18, 35, 10)
    after = dict(after, written_utc="2026-11-24T18:35:03Z", m5_checked_until="2026-11-24T18:35:00Z")
    v = authorise(s, st, _idea("buy", rej, "13121.4"), at, src(after))
    assert v.allowed and v.opportunity["id"] == "STP-GBPUSD-20261124-1800-11"


# ---- the full wired path over the recorded day (STP_FULL_REPLAY=1) ------------------------------------------------

@pytest.fixture(scope="module")
def replays(tmp_path_factory):
    from tests.stp.harness import Over, live_settings, live_store, read_records, replay_day
    out = {}
    for name, kw in (("off", {}), ("on", {"stp_opportunities": True, "stp_bidirectional": True,
                                          "stp_authorises_entries": True})):
        tmp = tmp_path_factory.mktemp(name)
        s = Over(live_settings(tmp, **kw), tmp)
        r = replay_day(s, live_store(s), T(2026, 11, 24, 21, 0), stp=bool(kw))
        out[name] = SimpleNamespace(s=s, engine=r["engine"], records=read_records(s), snaps=r["snapshots"])
    return out


def _dec(r):
    lines = next(v for k, v in r.records.items() if k.endswith("decisions.jsonl"))
    return [json.loads(x) for x in lines]


@full
def test_FT_A15_the_ema_pullback_decides_exactly_the_same_with_stp_on(replays):
    # the order sender's deal references have a random part by design: everything else must be the same
    pick = lambda r: [{k: v for k, v in x.items() if k != "reference"}                 # noqa: E731
                      for x in _dec(r) if x.get("strategy") == "EMA pullback"]
    assert pick(replays["off"]) and pick(replays["off"]) == pick(replays["on"])


@full
def test_FT_A16_with_stp_on_the_analyser_and_ungated_strategies_are_unchanged(replays):
    gated = {"Bollinger bounce", "Bollinger bounce 5m", "level reversal"}
    keep = lambda r: [x for x in _dec(r) if x.get("kind") == "analyser state change"]  # noqa: E731
    assert keep(replays["off"]) == keep(replays["on"])
    ideas = lambda r: [(x["time_utc"], x["strategy"], x["direction"], x.get("allowed"))      # noqa: E731
                       for x in _dec(r) if x.get("kind") == "idea" and x.get("strategy") not in gated]
    assert ideas(replays["off"]) == ideas(replays["on"])


@full
def test_FT_A18_the_stp_zone_sells_are_authorised_and_rsi_stretch_does_not_refuse_them(replays):
    d = _dec(replays["on"])
    auth = [x for x in d if x["kind"] == "STP authorised"]
    refused_rsi = [x for x in d if x["kind"] == "entry filter refused" and x.get("rule") == "RSI stretch"
                   and x.get("strategy") in ("Bollinger bounce", "Bollinger bounce 5m", "level reversal")]
    assert auth and not refused_rsi
    assert any(x["kind"] == "STP refused" for x in d)
