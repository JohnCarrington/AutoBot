"""Phase 2 WP3, market data integrity (owner's approval of 27 November 2026: PD-5 A+B+C). Technical tests TW3-xx.
Offline: scripted plans and in-memory candle stores. The "recovered" candles here are TEST DATA standing in for IG's
own candles after the approved recovery (prices/history_fill.py gap-go); no production candle is made up anywhere.

The SELL zone is 13240-13250, primary 13170 (destination zone 13165-13170)."""

from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal as D
from types import SimpleNamespace

from planner.opportunities import ACTIVE, OpportunityKeeper
from stp.authorise import authorise
from tests.planner_helpers import FakeStore
from tests.technical.test_planner import C, T
from tests.technical.test_stp_integration import Bi, KS, auth_settings, ev, five, hour, opps, pd, src, state, store_with

NOW = T(2026, 11, 17, 9, 0, 3)


def at(h, m=0, s=0, d=17):
    return T(2026, 11, d, h, m, s)


def gapped(t, missing, **kw):
    """A store up to t without the 5-minute candles starting at `missing` (as the store after an outage)."""
    st = store_with(t, **kw)
    st.by_tf["5m"] = [c for c in st.by_tf["5m"] if c.start not in missing]
    return st


def run(tmp, st, t, plans):
    OpportunityKeeper(KS(tmp), st, planner=plans).run(t)


def sell(rej, t):
    return SimpleNamespace(strategy="Bollinger bounce 5m", direction="sell", time=t, entry_price=D("13231"),
                           context={"rejection_candle": rej.strftime("%Y-%m-%dT%H:%M:%SZ")}, steps=[])


def check(tmp, st, rej, t):
    s_ = state(tmp) | {"written_utc": (t - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")}
    return authorise(auth_settings(tmp), st, sell(rej, t), t, src(s_))


GAP = [at(9, 10), at(9, 15)]                                     # two missing candles


def test_TW3_01_a_gap_in_an_opportunitys_life_is_recorded_and_stops_its_authorisations(tmp_path):
    plans = Bi(SELL=[pd()])
    run(tmp_path, store_with(NOW), NOW, plans)
    run(tmp_path, gapped(at(9, 25), GAP), at(9, 25), plans)
    o = opps(tmp_path)[0]
    assert o["data_gaps"] == [{"from_utc": "2026-11-17T09:10:00Z", "to_utc": "2026-11-17T09:20:00Z",
                               "found_utc": "2026-11-17T09:25:00Z", "status": "open"}]
    assert any(e["event"] == "data gap" for e in ev(tmp_path))
    rej = five(at(9, 20), 13230, 13241, 13229, 13238)
    st = gapped(at(9, 26), GAP, extra5=[rej])
    v = check(tmp_path, st, at(9, 20), at(9, 26))
    assert not v.allowed and "data gap" in v.reasons[0] and "not reconciled" in v.reasons[0]


def test_TW3_02_an_opportunity_created_after_the_gap_is_not_blocked(tmp_path):
    st = gapped(at(9, 25), GAP)
    run(tmp_path, st, at(9, 25), Bi(SELL=[pd()]))                 # first run after the gap (no step before it)
    assert opps(tmp_path) and not opps(tmp_path)[0].get("data_gaps")
    rej = five(at(9, 25), 13230, 13241, 13229, 13238)
    v = check(tmp_path, gapped(at(9, 31), GAP, extra5=[rej]), at(9, 25), at(9, 31))
    assert v.allowed, v.reasons


def test_TW3_03_the_weekend_is_never_a_gap(tmp_path):
    from planner.gaps import missing_fives
    s = KS(tmp_path)
    from prices.calendar import MarketHours
    hours = MarketHours(s.market_hours)
    fri_close = hours.session(T(2026, 11, 20, 12, 0))[1]           # the settings' own weekly close and open
    sun_open = hours.next_open(fri_close)
    fri, sun = fri_close - timedelta(minutes=10), sun_open + timedelta(minutes=10)
    fives = [C("5m", t, 1 / 12, 1, 2, 0, 1) for t in (fri_close - timedelta(minutes=10), fri_close - timedelta(minutes=5),
                                                     sun_open, sun_open + timedelta(minutes=5))]
    assert missing_fives(s, FakeStore({"5m": fives}), fri, sun) == []


def test_TW3_04_after_recovery_a_missed_zone_touch_is_reconciled_and_authorisation_resumes(tmp_path):
    plans = Bi(SELL=[pd()])
    run(tmp_path, store_with(NOW), NOW, plans)
    run(tmp_path, gapped(at(9, 25), GAP), at(9, 25), plans)
    assert opps(tmp_path)[0]["status"] == "WAITING"
    rec = [five(at(9, 10), 13230, 13241, 13229, 13238)]          # the recovered 09:10 candle reached the zone
    st = store_with(at(9, 30), extra5=rec)                       # both candles now stored
    run(tmp_path, st, at(9, 30), plans)
    o = opps(tmp_path)[0]
    assert o["status"] == ACTIVE and o["activation"]["candle_start_utc"] == "2026-11-17T09:10:00Z"
    assert o["data_gaps"][0]["status"] == "reconciled"
    assert any(e["event"] == "data gap reconciled" and "eligible again" in e["why"] for e in ev(tmp_path))
    v = check(tmp_path, store_with(at(9, 31), extra5=rec), at(9, 10), at(9, 31))
    assert v.allowed, v.reasons


def test_TW3_05_after_recovery_a_destination_reached_in_the_gap_ends_it(tmp_path):
    plans = Bi(SELL=[pd()])
    run(tmp_path, store_with(NOW), NOW, plans)
    run(tmp_path, gapped(at(9, 25), GAP), at(9, 25), plans)
    rec = [five(at(9, 15), 13200, 13200, 13169, 13170)]          # recovered: the destination was reached at 09:15
    run(tmp_path, store_with(at(9, 30), extra5=rec), at(9, 30), plans)
    assert opps(tmp_path) == []
    e = next(e for e in ev(tmp_path) if e["event"] == "invalidated")
    assert e["candle_start_utc"] == "2026-11-17T09:15:00Z" and e["destination_case"] == "before_zone"


def test_TW3_06_a_gap_still_missing_keeps_it_ineligible_without_any_expiry(tmp_path):
    plans = Bi(SELL=[pd()])
    run(tmp_path, store_with(NOW), NOW, plans)
    for t in (at(9, 25), at(11, 0, 3), at(15, 0, 3)):
        run(tmp_path, gapped(t, GAP), t, plans)
    o = opps(tmp_path)[0]
    assert o["status"] in ("WAITING", ACTIVE) and o["data_gaps"][0]["status"] == "open"


def test_TW3_07_an_uncertain_hour_blocks_until_rebuilt_and_is_then_reconciled(tmp_path):
    plans = Bi(SELL=[pd()])
    pre = [hour(at(8), 13230, 13241, 13229, 13235)]
    run(tmp_path, store_with(NOW, extra1=pre), NOW, plans)
    inc = C("1h", at(9), 1, 13200, 13201, 13199, 13200)
    inc = type(inc)(**{**inc.__dict__, "parts": 10, "expected_parts": 12})
    st = gapped(at(10, 0, 3), [at(9, 10), at(9, 15)], extra1=pre + [inc])
    run(tmp_path, st, at(10, 0, 3), plans)
    a = opps(tmp_path)[0]["lineage"]
    assert state(tmp_path)["lineages"][a]["tests"]["uncertain"] == ["2026-11-17T09:00:00Z"]
    rej = five(at(10, 10), 13230, 13241, 13229, 13238)
    assert not check(tmp_path, gapped(at(10, 15), GAP, extra1=pre + [inc], extra5=[rej]), at(10, 10), at(10, 15)).allowed
    full = hour(at(9), 13200, 13201, 13199, 13200)              # rebuilt from the recovered candles: wholly clear
    st = store_with(at(10, 20), extra1=pre + [full], extra5=[rej])
    run(tmp_path, st, at(10, 20), plans)
    t = state(tmp_path)["lineages"][a]["tests"]
    assert t["uncertain"] == [] and ["2026-11-17T09:00:00Z", "rearm"] in t["events"]


def test_TW3_08_a_rebuilt_hour_that_would_renumber_a_test_is_left_for_review(tmp_path):
    plans = Bi(SELL=[pd()])
    pre = [hour(at(8), 13230, 13241, 13229, 13235)]
    run(tmp_path, store_with(NOW, extra1=pre), NOW, plans)
    inc = C("1h", at(9), 1, 13200, 13201, 13199, 13200)
    inc = type(inc)(**{**inc.__dict__, "parts": 10, "expected_parts": 12})
    later = [hour(at(10), 13230, 13241, 13229, 13235), hour(at(11), 13200, 13201, 13199, 13200),
             hour(at(12), 13230, 13241, 13229, 13235)]
    for h in (10, 11, 12, 13):
        t = at(h, 0, 3)
        run(tmp_path, gapped(t, GAP, extra1=pre + [inc] + later), t, plans)
    full = hour(at(9), 13200, 13201, 13199, 13200)
    run(tmp_path, store_with(at(13, 5), extra1=pre + [full] + later), at(13, 5), plans)
    o = opps(tmp_path)[0]
    assert o["data_gaps"][0]["status"] == "review"
    assert any(e["event"] == "data gap review" and "not renumbered" in e["why"] for e in ev(tmp_path))
    rej = five(at(13, 0), 13230, 13241, 13229, 13238)
    assert not check(tmp_path, store_with(at(13, 6), extra1=pre + [full] + later, extra5=[rej]), at(13, 0),
                     at(13, 6)).allowed


def test_TW3_09_a_missing_candle_after_the_trackers_last_step_refuses_at_entry(tmp_path):
    plans = Bi(SELL=[pd()])
    run(tmp_path, store_with(at(9, 5, 3)), at(9, 5, 3), plans)
    rej = five(at(9, 0), 13230, 13241, 13229, 13238)
    st = gapped(at(9, 22), [at(9, 5), at(9, 10)], extra5=[rej])  # the tracker last ran at 09:05; 09:05-09:15 missing
    s_ = state(tmp_path) | {"written_utc": "2026-11-17T09:21:00Z"}
    v = authorise(auth_settings(tmp_path), st, sell(at(9, 0), at(9, 22)), at(9, 22), src(s_))
    assert not v.allowed and any("PD-5" in r for r in v.reasons)


def test_TW3_10_reconciliation_is_idempotent_and_writes_nothing_but_the_trackers_own_files(tmp_path):
    plans = Bi(SELL=[pd()])
    run(tmp_path, store_with(NOW), NOW, plans)
    run(tmp_path, gapped(at(9, 25), GAP), at(9, 25), plans)
    st = store_with(at(9, 30))
    run(tmp_path, st, at(9, 30), plans)
    run(tmp_path, st, at(9, 30), plans)                           # again, as after a restart
    assert sum(e["event"] == "data gap reconciled" for e in ev(tmp_path)) == 1
    written = {p.relative_to(tmp_path).parts[0] for p in tmp_path.rglob("*") if p.is_file()}
    assert written == {"planner"}                                 # no order, decision or record of any kind
