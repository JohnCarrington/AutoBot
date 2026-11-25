"""Technical tests for the Structural Trade Planner V1 (planner/; owner's approval of 17 November 2026; OBSERVE ONLY).
Made-up candles (tests/planner_helpers.py) and a made-up store; never the real store, never IG. Prices are the chart
(SELL) prices in points (GBPUSD: 1 point = 1 pip)."""

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace

import pytest

from config.settings_loader import load_settings
from levels.rules import daily_pivots
from planner import keeper as keeper_mod
from planner.assess import plan_at
from planner.keeper import ACTIVE, COMPLETED, INVALIDATED, SUPERSEDED, WAITING, Keeper, PlannerUpdater
from planner.measure import adr, four_hour_from_hourly, frame, freshness, snapshot
from planner.panel import LABEL, panel
from planner.structure import DOWN, MIXED, UP, structure, swings, threshold_misses
from planner.zones import (MAJOR, MINOR, MODERATE, MOVING_AVERAGE, PIVOT, PSYCHOLOGICAL, STRUCTURE, MapLevel,
                           interacts, weekly_levels, zone_width, zones)
from prices.builder import build_due
from prices.calendar import Boundaries, MarketHours
from prices.indicators import ema, macd, needs_ema, rsi
from prices.model import Candle
from tests.planner_helpers import FakeStore, build_all, five_minute_path, market, with_folder

UTC = timezone.utc
ROOT = Path(__file__).resolve().parents[2]
S = load_settings().for_pair("GBPUSD")


def T(*a):
    return datetime(*a, tzinfo=UTC)


def C(tf, start, hours, o, h, l, c):
    o, h, l, c = (D(str(x)) for x in (o, h, l, c))
    return Candle(tf, start, start + timedelta(hours=hours), o + 1, h + 1, l + 1, c + 1, o, h, l, c)


# ---- the approved settings -----------------------------------------------------------------------------------------

def test_the_planner_uses_the_approved_numbers_and_your_chart_settings():
    p, ind = S.planner, S.indicators
    assert (p.adr_weekdays, p.h4_swing_min_move_pips, p.daily_swing_min_move_pips) == (20, 40, 110)
    assert (p.h4_swing_candles_each_side, p.h4_swing_move_within_candles, p.daily_swing_candles_each_side) == (3, 6, 3)
    assert (p.zone_width_adr_share, p.major_min_families, p.moderate_min_families, p.min_entry_class) == (D("0.15"), 3, 2, "Moderate")
    assert (p.macd_weakening_candles, p.no_new_extreme_hourly_candles, p.ema_slope_candles, p.structure_break_closes) == (3, 3, 6, 1)
    assert tuple(ind.ema_periods) == (7, 13, 21, 100, 200) and (ind.macd_fast_periods, ind.macd_slow_periods,
                                                                ind.macd_signal_periods, ind.rsi_periods) == (35, 45, 30, 3)
    assert ind.timeframes == ("5m", "1h")              # the analyser's timeframes are NOT changed by the planner
    assert (S.rejection.near_level_within_pips, S.planner.break_beyond_pips, S.levels.line_up_within_pips) == (3, 3, 5)


# ---- indicators -------------------------------------------------------------------------------------------------

def _hours(n, start=T(2026, 11, 2, 0), step=1.0):
    out, p = [], 13000.0
    for i in range(n):
        p += step * (1 if (i // 7) % 2 == 0 else -0.6)
        out.append(C("1h", start + timedelta(hours=i), 1, p, p + 3, p - 3, p + 1))
    return out


def test_indicators_are_the_bots_own_with_your_settings_and_wait_for_warm_up():
    cs = _hours(700)
    f = frame(S, "1h", cs)
    assert f.ema[100] == ema(cs, "sell", 100) and f.ema[200] == ema(cs, "sell", 200)
    assert f.macd == macd(cs, "sell", 35, 45, 30) and f.rsi == rsi(cs, "sell", 3)
    assert f.warming == []
    short = frame(S, "4h", cs[:300])
    assert short.ema_now(200) is None and 200 not in short.ema
    assert f"EMA200 (300 of {needs_ema(200, 2)} candles)" in short.warming
    assert short.ema_now(100) is not None              # EMA100 needs 296: ready at 300


def test_adr_leaves_out_sunday_candles_and_needs_20_weekdays():
    days = []
    t = T(2026, 9, 6)                                  # a Sunday
    for k in range(40):
        d = t + timedelta(days=k)
        if d.weekday() == 5:
            continue                                   # no Saturday candle
        rng = 10 if d.weekday() == 6 else 80          # Sunday stubs 10 pips, weekdays 80
        days.append(C("1d", d, 24, 13000, 13000 + rng, 13000, 13000))
    assert adr(S, days) == D(80)
    assert adr(S, days[:15]) is None                   # fewer than 20 weekdays: none (never guessed)


# ---- timeframes: 4-hour candles from hourly ones --------------------------------------------------------------------

def test_four_hour_candles_are_on_uk_boundaries_in_winter_and_summer():
    for day, first_utc in ((T(2026, 11, 3, 0), 0), (T(2026, 7, 7, 0), 23)):      # winter (GMT), summer (BST)
        start = day - timedelta(hours=1) if first_utc == 23 else day
        hours = [C("1h", start + timedelta(hours=i), 1, 100 + i, 101 + i, 99 + i, 100 + i) for i in range(12)]
        four = four_hour_from_hourly(S, hours, start + timedelta(hours=12))
        assert [c.start.hour for c in four] == [first_utc, (first_utc + 4) % 24, (first_utc + 8) % 24]
        assert four[0].sell_open == hours[0].sell_open and four[0].sell_close == hours[3].sell_close
        assert four[0].sell_high == max(h.sell_high for h in hours[:4])


def test_a_four_hour_candle_with_an_hour_missing_or_not_finished_is_not_used():
    hours = [C("1h", T(2026, 11, 3, i), 1, 100, 101, 99, 100) for i in range(8) if i != 5]
    assert [c.start.hour for c in four_hour_from_hourly(S, hours, T(2026, 11, 3, 8))] == [0]     # 04:00 lacks 05:00
    hours = [C("1h", T(2026, 11, 3, i), 1, 100, 101, 99, 100) for i in range(6)]
    assert [c.start.hour for c in four_hour_from_hourly(S, hours, T(2026, 11, 3, 6))] == [0]     # 04:00 not finished


def test_four_hour_candles_from_hourly_equal_the_price_services_own_four_hour_candles(tmp_path):
    from prices.store import CandleStore
    st = CandleStore(tmp_path / "GBPUSD", 30)
    fives = five_minute_path(S, T(2026, 10, 25, 21), [(0, 13000), (30, 13060), (60, 12990), (100, 13100)])
    for c in fives:
        st.add(c)
    b = Boundaries(S.candles, MarketHours(S.market_hours))
    end = fives[-1].end
    build_due(st, b, end + timedelta(hours=5), 0, lambda m: None)
    hourly = st.read_range("1h", T(2026, 10, 1), end + timedelta(days=1))
    native = [c for c in st.read_range("4h", T(2026, 10, 1), end + timedelta(days=1)) if c.end <= end]
    rebuilt = four_hour_from_hourly(S, hourly, end)
    assert len(native) > 20 and [c.prices() for c in rebuilt] == [c.prices() for c in native]
    assert [c.start for c in rebuilt] == [c.start for c in native]


# ---- no unfinished candle, no future ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def bear_market():
    from tests.functional.test_planner_scenarios import corrective_market
    return corrective_market()


def test_the_plan_at_a_time_uses_only_candles_finished_by_then(bear_market):
    t = bear_market.by_tf["5m"][-1].end - timedelta(hours=7, minutes=10)
    full = plan_at(S, bear_market, t, calendar=[]).as_dict()
    then = plan_at(S, bear_market.until(t), t, calendar=[]).as_dict()
    assert full == then
    snap = snapshot(S, bear_market, t)
    for f in (snap.h1, snap.h4, snap.d1, snap.w1):
        assert all(c.end <= t for c in f.candles)
    assert snap.five.end <= t


# ---- pivots ------------------------------------------------------------------------------------------------------

def test_weekly_pivots_are_the_classic_formulas_on_the_last_weekly_candle():
    wk = C("1w", T(2026, 11, 8), 117, 13300, 13400, 13100, 13200)
    snap = SimpleNamespace(w1=SimpleNamespace(last=wk))
    got = {lv.name: lv.price for lv in weekly_levels(S, snap)}
    p = (D(13400) + D(13100) + D(13200)) / 3
    assert got["weekly pivot"] == D("13233.3") and got["weekly R1"] == (2 * p - D(13100)).quantize(D("0.1"))
    assert got["weekly R2"] == (p + 300).quantize(D("0.1")) and got["weekly S2"] == (p - 300).quantize(D("0.1"))
    assert got["previous week high"] == D(13400) and got["previous week low"] == D(13100)
    assert {lv.price for lv in weekly_levels(S, snap) if lv.name.startswith("weekly")} == \
           {lv.price for lv in daily_pivots(wk, "sell", 1, "")}


def test_tuesday_17_november_daily_r2_is_the_one_on_the_owners_chart():
    monday = C("1d", T(2026, 11, 16), 24, 13215.6, 13224.5, 13175.2, 13183.4)
    r2 = [lv.price for lv in daily_pivots(monday, "sell", 1, "") if lv.type == "R2"][0]
    assert r2 == D("13243.7")


# ---- structure ---------------------------------------------------------------------------------------------------

def _zigzag(points, tf="4h", hours=4, start=T(2026, 9, 7)):
    """Candles walking straight between the given prices, 6 candles a leg."""
    out, t = [], start
    for a, b in zip(points, points[1:]):
        for k in range(6):
            o = a + (b - a) * k / 6
            c = a + (b - a) * (k + 1) / 6
            out.append(C(tf, t, hours, o, max(o, c) + 1, min(o, c) - 1, c))
            t += timedelta(hours=hours)
    return out


def test_swings_use_the_approved_move_and_lower_highs_and_lows_are_a_down_structure():
    cs = _zigzag([13500, 13400, 13460, 13340, 13400, 13280, 13330])       # 4-hour legs of 100/60 pips
    sw = swings(S, cs, "4h")
    st = structure(S, cs, "4h", sw)
    assert st.sequence == DOWN and [s.price for s in st.highs] == [D(13461), D(13401)]
    assert all(s.known_utc >= s.candle_utc for s in sw)
    up = _zigzag([13000, 13100, 13040, 13160, 13100, 13220, 13170])
    assert structure(S, up, "4h").sequence == UP


def test_a_turn_held_back_only_by_the_40_pip_threshold_is_recorded_not_counted():
    cs = _zigzag([13500, 13400, 13460, 13340, 13400, 13280, 13310, 13290])  # last bounce only 30 pips
    found = swings(S, cs, "4h")
    misses = threshold_misses(S, cs, "4h", found)
    assert any(m["kind"] == "high" and D(m["moved_pips"]) < 40 and m["needed_pips"] == "40.0" for m in misses) or \
        any(m["kind"] == "low" for m in misses)
    assert all("provisional threshold, recorded for review" in m["note"] for m in misses)


def test_a_structural_break_needs_a_close_3_pips_beyond_not_a_wick():
    cs = _zigzag([13500, 13400, 13460, 13340, 13400, 13280, 13330])
    st = structure(S, cs, "4h")
    last_high = st.highs[-1].price
    t = cs[-1].end
    wick = cs + [C("4h", t, 4, 13330, last_high + 20, 13320, last_high + D("2.9"))]
    assert structure(S, wick, "4h").broken is None
    close = cs + [C("4h", t, 4, 13330, last_high + 5, 13320, last_high + 3)]
    assert structure(S, close, "4h").broken[0] == UP


# ---- zones -------------------------------------------------------------------------------------------------------

def L(price, name, fam, dw=False, fixed=True, kind=None):
    k = kind or {PIVOT: "daily R/S", STRUCTURE: "hourly swing", MOVING_AVERAGE: "moving average",
                 PSYCHOLOGICAL: "psychological"}[fam]
    return MapLevel(D(str(price)), name, fam, "daily" if dw else "1h", k, T(2026, 11, 10), dw, fixed)


def test_zone_width_is_the_larger_of_5_pips_and_15_percent_of_the_adr():
    assert zone_width(S, D("72.7")) == D("10.905")
    assert zone_width(S, D(20)) == D(5)


def test_moving_levels_never_reshape_a_zone_and_join_the_one_they_fit():
    base = [L(13243.7, "daily R2", PIVOT, True), L(13243.2, "hourly swing high", STRUCTURE)]
    with_ema = base + [L(13236.0, "H1 EMA100", MOVING_AVERAGE, fixed=False)]
    z1 = zones(S, base, D(72.7), [])
    z2 = zones(S, with_ema, D(72.7), [])
    assert len(z1) == len(z2) == 1 and z2[0].fixed_identity == z1[0].fixed_identity
    assert z2[0].low == D("13236.0") and MOVING_AVERAGE in z2[0].families


def test_one_family_counts_once_and_the_classes_need_a_daily_or_weekly_level_for_major():
    three_swings = [L(13240 + i, f"hourly swing high {i}", STRUCTURE) for i in range(3)]
    assert zones(S, three_swings, D(72.7), [])[0].klass == MINOR
    no_dw = three_swings + [L(13241.5, "H1 EMA100", MOVING_AVERAGE, fixed=False), L(13250, "round number", PSYCHOLOGICAL)]
    assert zones(S, no_dw, D(72.7), [])[0].klass == MODERATE           # 3 families, no daily/weekly level
    with_dw = no_dw + [L(13243.7, "daily R2", PIVOT, True)]
    z = zones(S, with_dw, D(72.7), [])[0]
    assert z.klass == MAJOR and len(z.families) == 4 and z.reference.name == "daily R2"


def test_a_zone_is_touched_by_the_existing_one_sided_3_pip_rule():
    c = lambda h, l: C("5m", T(2026, 11, 17, 9), 1 / 12, l + 1, h, l, l + 1)          # noqa: E731
    lo_, hi_ = D(13240), D(13250)
    assert interacts(S, c(13237, 13230), lo_, hi_, from_below=True)       # 3 pips short of the bottom counts
    assert not interacts(S, c(D("13236.9"), 13230), lo_, hi_, from_below=True)
    assert not interacts(S, c(13262, D("13250.1")), lo_, hi_, from_below=True)      # wholly above: not coming up into it
    assert interacts(S, c(13263, 13253), lo_, hi_, from_below=False)      # from above, 3 pips short of the top


# ---- freshness, records, lifecycle --------------------------------------------------------------------------------

def test_data_is_stale_when_the_newest_candles_are_too_old_while_the_market_is_open():
    five = C("5m", T(2026, 11, 17, 9, 0), 1 / 12, 1, 2, 0, 1)
    hour = C("1h", T(2026, 11, 17, 8), 1, 1, 2, 0, 1)
    assert freshness(S, five, hour, T(2026, 11, 17, 9, 6))[0] is True
    fresh, why = freshness(S, five, hour, T(2026, 11, 17, 9, 30))
    assert fresh is False and any("5m" in w for w in why)


class FakePlan:
    def __init__(self, d):
        self.d = d

    def as_dict(self):
        return self.d


def plan_dict(trade="SELL", zone=(13240, 13250), levels=None, direction=None, no_rec=None, primary=13170,
              moving=13238, applies=True, fresh=True):
    bear = trade == "SELL"
    levels = levels if levels is not None else [("daily R2", "13243.7", True), ("hourly swing high", "13243.2", True)]
    mem = [{"price": p, "name": n, "role": "", "family": "pivot", "timeframe": "daily", "origin_utc": None,
            "daily_or_weekly": True, "fixed": f, "note": ""} for n, p, f in levels]
    mem.append({"price": str(moving), "name": "H1 EMA100", "role": "", "family": "moving average", "timeframe": "1h",
                "origin_utc": None, "daily_or_weekly": False, "fixed": False, "note": ""})
    z = {"low": str(zone[0]), "high": str(zone[1]), "class": "Major", "families": ["moving average", "pivot"],
         "daily_or_weekly_level": True, "tests": 0, "reference": None, "levels": mem}
    pz = {"low": str(primary - 5), "high": str(primary), "class": "Major", "families": ["pivot"], "levels": []} if bear else \
        {"low": str(primary), "high": str(primary + 5), "class": "Major", "families": ["pivot"], "levels": []}
    return {"pair": "GBPUSD", "as_of_utc": "x", "market_data_utc": "x", "fresh": fresh,
            "dominant_direction": direction or ("BEARISH" if bear else "BULLISH"), "direction_evidence": ["e"],
            "condition": "CORRECTION_LIKELY", "condition_evidence": ["c"], "opportunity": "corrective reversal",
            "trade": None if no_rec else trade, "expected_movement": "UP into resistance, then DOWN",
            "entry_zone": None if no_rec else z,
            "reference_entry": None if no_rec else {"price": "13243.7", "level": "daily R2"},
            "reachability": "PLAUSIBLE", "selection_reason": "why", "destinations": {} if no_rec else {
                "intermediate": {"price": "13210", "zone": pz}, "primary": {"price": str(primary if bear else primary), "zone": pz},
                "extended": None},
            "invalidation": {} if no_rec else {"conditions": ["an hourly close at or above 13253"],
                                              "destination_first_applies": applies},
            "observations": {"uk_time": "09:00"}, "candidates": [], "alternative": None, "no_recommendation": no_rec,
            "warming_up": [], "threshold_misses": [], "h4_last_swing": None}


class Script:
    """A planner that returns the given plans in turn (the last one again after that)."""

    def __init__(self, *plans):
        self.plans = list(plans)
        self.calls = 0

    def __call__(self, settings, store, now, *a):
        p = self.plans[min(self.calls, len(self.plans) - 1)]
        self.calls += 1
        return FakePlan(p)


def flat_store(until, price=13200, extra5=(), extra1=()):
    """Quiet 5-minute and hourly candles at `price` up to `until`, plus any given ones (replacing the same times)."""
    fives, hours = {}, {}
    t = (until - timedelta(days=1)).replace(minute=0, second=0, microsecond=0)
    while t < until:
        if t + timedelta(minutes=5) <= until:
            fives[t] = C("5m", t, 1 / 12, price, price + 1, price - 1, price)
        if t.minute == 0 and t + timedelta(hours=1) <= until:
            hours[t] = C("1h", t, 1, price, price + 1, price - 1, price)
        t += timedelta(minutes=5)
    for c in extra5:
        fives[c.start] = c
    for c in extra1:
        hours[c.start] = c
    return FakeStore({"5m": list(fives.values()), "1h": list(hours.values())})


def K(tmp_path, store, planner):
    return Keeper(with_folder(S, tmp_path / "planner"), store, planner=planner)


NOW = T(2026, 11, 17, 9, 0)


def history(tmp_path):
    return [json.loads(x) for x in (tmp_path / "planner" / "GBPUSD" / "recommendations.jsonl").read_text().splitlines()]


def test_a_new_recommendation_is_issued_at_once_and_written_with_its_history(tmp_path):
    k = K(tmp_path, flat_store(NOW), Script(plan_dict()))
    k.run(NOW)
    st = json.loads((tmp_path / "planner" / "GBPUSD" / "current.json").read_text())
    rec = st["recommendation"]
    assert rec["status"] == WAITING and rec["trade"] == "SELL" and rec["entry_zone"]["low"] == "13240"
    assert [e["event"] for e in history(tmp_path)] == ["analysis", "created", "waiting"]
    assert st["observe_only"] == "OBSERVE ONLY - DOES NOT CONTROL TRADING" and st["current"] is True
    for key in ("instrument", "created_utc", "dominant_direction", "condition", "expected_movement", "trade", "entry_zone",
                "reference_entry", "destinations", "invalidation", "observations", "status", "status_reason", "six_factors"):
        assert key in rec


def test_the_recommendation_survives_a_restart_and_is_reassessed_not_reissued(tmp_path):
    K(tmp_path, flat_store(NOW), Script(plan_dict())).run(NOW)
    later = NOW + timedelta(hours=1)
    k2 = K(tmp_path, flat_store(later), Script(plan_dict(moving=13236)))
    k2.run(later)
    ev = history(tmp_path)
    assert ev[-1]["event"] == "supported" and len({e["id"] for e in ev if e["id"]}) == 1


def test_waiting_becomes_active_when_a_5_minute_candle_reaches_the_zone_and_back_when_an_hour_stays_clear(tmp_path):
    K(tmp_path, flat_store(NOW), Script(plan_dict())).run(NOW)
    touch = C("5m", NOW, 1 / 12, 13230, 13238, 13229, 13231)                   # 2 pips short of 13240
    t1 = NOW + timedelta(minutes=5)
    k = K(tmp_path, flat_store(t1, extra5=[touch]), Script(plan_dict()))
    k.run(t1)
    assert k.state["recommendation"]["status"] == ACTIVE
    t2 = NOW + timedelta(hours=1, minutes=1)
    k = K(tmp_path, flat_store(t2, extra5=[touch]), Script(plan_dict()))
    k.run(t2)
    assert k.state["recommendation"]["status"] == WAITING                         # the 09:00 hour stayed 40 pips below


def test_an_hourly_close_3_pips_beyond_the_zone_invalidates_less_is_only_recorded(tmp_path):
    K(tmp_path, flat_store(NOW), Script(plan_dict())).run(NOW)
    t = NOW + timedelta(hours=1, minutes=1)
    near = C("1h", NOW, 1, 13245, 13256, 13244, D("13252.9"))                    # 2.9 beyond 13250
    k = K(tmp_path, flat_store(t, extra1=[near]), Script(plan_dict()))
    k.run(t)
    assert k.state["recommendation"]["status"] in (WAITING, ACTIVE)
    assert "closed beyond" in [e["event"] for e in history(tmp_path)]
    t2 = t + timedelta(hours=1)
    far = C("1h", NOW + timedelta(hours=1), 1, 13245, 13256, 13244, 13253)       # exactly 3 beyond
    first = k.state["recommendation"]["id"]
    k = K(tmp_path, flat_store(t2, extra1=[near, far]), Script(plan_dict()))
    k.run(t2)
    inval = [e for e in history(tmp_path) if e["event"] == "invalidated"][-1]
    assert inval["id"] == first and inval["status"] == INVALIDATED
    assert "confirmed break" in inval["why"] and "3.0 pips beyond the zone's top 13250" in inval["why"]
    assert k.state["recent"][0]["id"] == first and k.state["recent"][0]["status"] == INVALIDATED


def test_a_wick_through_the_zone_is_a_sweep_not_a_break(tmp_path):
    K(tmp_path, flat_store(NOW), Script(plan_dict())).run(NOW)
    t = NOW + timedelta(hours=1, minutes=1)
    wick = C("1h", NOW, 1, 13245, 13270, 13244, 13246)
    k = K(tmp_path, flat_store(t, extra1=[wick]), Script(plan_dict()))
    k.run(t)
    assert k.state["recommendation"] is not None
    assert "wick sweep" in [e["event"] for e in history(tmp_path)]


def test_destination_reached_before_entry_invalidates_after_entry_completes(tmp_path):
    K(tmp_path, flat_store(NOW), Script(plan_dict())).run(NOW)
    t = NOW + timedelta(minutes=5)
    drop = C("5m", NOW, 1 / 12, 13200, 13200, 13168, 13169)
    k = K(tmp_path, flat_store(t, extra5=[drop]), Script(plan_dict()))
    k.run(t)
    assert history(tmp_path)[-1]["event"] == "invalidated" and "destination reached before entry" in history(tmp_path)[-1]["why"]
    other = tmp_path / "b"
    other.mkdir()
    K(other, flat_store(NOW), Script(plan_dict())).run(NOW)
    touch = C("5m", NOW, 1 / 12, 13230, 13241, 13229, 13231)
    K(other, flat_store(t, extra5=[touch]), Script(plan_dict())).run(t)
    t2 = t + timedelta(minutes=5)
    k = K(other, flat_store(t2, extra5=[touch, C("5m", t, 1 / 12, 13200, 13200, 13168, 13169)]), Script(plan_dict()))
    k.run(t2)
    assert history(other)[-1]["event"] == "completed"


def test_a_destination_between_price_and_the_zone_has_no_reached_first_check(tmp_path):
    K(tmp_path, flat_store(NOW), Script(plan_dict(applies=False))).run(NOW)
    t = NOW + timedelta(minutes=5)
    drop = C("5m", NOW, 1 / 12, 13200, 13200, 13168, 13169)
    k = K(tmp_path, flat_store(t, extra5=[drop]), Script(plan_dict(applies=False)))
    k.run(t)
    assert k.state["recommendation"]["status"] == WAITING


def test_a_different_zone_supersedes_and_a_lost_basis_or_direction_invalidates(tmp_path):
    later = NOW + timedelta(hours=1)
    k = K(tmp_path, flat_store(NOW), Script(plan_dict()))
    k.run(NOW)
    first = k.state["recommendation"]["id"]
    other = plan_dict(zone=(13280, 13290), levels=[("daily R3", "13285", True), ("round number", "13290", True)])
    k = K(tmp_path, flat_store(later), Script(other))
    k.run(later)
    ev = history(tmp_path)
    assert [e["event"] for e in ev if e["id"] == first][-1] == "superseded"
    assert k.state["recommendation"]["id"] != first and f"supersedes {first}" in k.state["recommendation"]["status_reason"]
    k = K(tmp_path, flat_store(later + timedelta(hours=1)), Script(plan_dict(direction="TRANSITIONAL", no_rec="direction")))
    k.run(later + timedelta(hours=1))
    assert history(tmp_path)[-1]["event"] == "invalidated" and "direction changed" in history(tmp_path)[-1]["why"]


def test_stale_data_makes_the_recommendation_not_current_without_ending_it(tmp_path):
    k = K(tmp_path, flat_store(NOW), Script(plan_dict()))
    k.run(NOW)
    late = NOW + timedelta(minutes=40)                                            # no candle for 40 minutes
    k = K(tmp_path, flat_store(NOW), Script(plan_dict()))
    k.run(late)
    assert k.state["recommendation"]["status"] == WAITING
    assert k.state["current"] is False and k.state["data_fresh"] is False and k.state["not_current_reasons"]


def test_a_damaged_planner_file_is_kept_aside_and_the_planner_starts_afresh(tmp_path):
    folder = tmp_path / "planner" / "GBPUSD"
    folder.mkdir(parents=True)
    (folder / "current.json").write_text("{not json")
    k = K(tmp_path, flat_store(NOW), Script(plan_dict()))
    assert k.state["recommendation"] is None and list(folder.glob("current.damaged-*.json"))


def test_with_no_candles_there_is_no_recommendation_and_no_crash():
    p = plan_at(S, FakeStore({}), NOW, calendar=[]).as_dict()
    assert p["no_recommendation"] and p["entry_zone"] is None and p["fresh"] is False


def test_the_panel_says_observe_only_and_copes_with_a_missing_or_bad_file(tmp_path):
    s2 = with_folder(S, tmp_path / "planner")
    assert panel(s2, NOW) == {"label": LABEL, "available": False, "message": panel(s2, NOW)["message"]}
    K(tmp_path, flat_store(NOW), Script(plan_dict())).run(NOW)
    p = panel(s2, NOW)
    assert p["label"] == "OBSERVE ONLY — DOES NOT CONTROL TRADING" and p["recommendation"]["trade"] == "SELL"
    assert set(p) >= {"observed", "forecast", "recommendation", "invalidation", "last_analysis_utc"}
    (tmp_path / "planner" / "GBPUSD" / "current.json").write_text("[]")
    assert panel(s2, NOW)["available"] is False


# ---- failure isolation, and nothing that can touch a trade ---------------------------------------------------------

def test_the_price_service_starts_the_planner_in_its_own_process_and_never_waits_or_fails():
    calls = []

    class Proc:
        def poll(self):
            return None                                 # still running

    u = PlannerUpdater(S, popen=lambda cmd, **kw: calls.append((cmd, kw)) or Proc())
    u(NOW)
    u(NOW)                                              # the first run still going: no second one
    assert len(calls) == 1
    cmd, kw = calls[0]
    assert cmd[:3] == ["nice", "-n", "10"] and cmd[-4:] == ["planner", "run", "--pair", "GBPUSD"]
    assert kw["start_new_session"] is True
    warned = []
    boom = PlannerUpdater(S, warn=warned.append, popen=lambda *a, **k: (_ for _ in ()).throw(OSError("no")))
    boom(NOW)                                           # no exception reaches the price service
    assert warned and "trading is not affected" in warned[0]


def test_the_planner_runs_last_after_the_trading_engine_and_only_when_switched_on(tmp_path, monkeypatch):
    import prices.service as service
    order = []
    monkeypatch.setattr(service, "LevelsUpdater", lambda ps, store: lambda now: order.append("levels"))
    monkeypatch.setattr(service, "StatesUpdater", lambda ps, store: lambda now: order.append("states"))
    monkeypatch.setattr(keeper_mod, "PlannerUpdater", lambda ps: lambda now: order.append("planner"))

    def settings_with(on):
        sw = SimpleNamespace(planner_observe=on)
        from tests.planner_helpers import Over, section
        return Over(S, switches=sw, candles=section(S.candles, folder=tmp_path / "GBPUSD"))
    for on, expected in ((True, ["levels", "states", "engine", "planner"]), (False, ["levels", "states", "engine"])):
        order.clear()
        feed = service._feed(settings_with(on), lambda: NOW, lambda m: None, (lambda now: order.append("engine"),))
        feed.after_new_candle(NOW)
        assert order == expected


def test_a_failed_planner_run_keeps_its_files_and_returns_an_error(tmp_path, monkeypatch):
    import planner.__main__ as main
    monkeypatch.setattr(main, "load_settings", lambda **kw: SimpleNamespace(for_pair=lambda p: with_folder(S, tmp_path / "pl")))
    monkeypatch.setattr(keeper_mod.Keeper, "run", lambda self, now: (_ for _ in ()).throw(RuntimeError("bad")))
    monkeypatch.setattr("housekeeping.logs.setup_logging", lambda *a, **k: None)
    assert main.main(["run"]) == 1


def test_the_planner_imports_nothing_that_can_reach_ig_or_a_trade():
    code = ("import sys; import planner.assess, planner.keeper, planner.panel, planner.__main__; "
            "print(sorted({m.split('.')[0] for m in sys.modules} & {'ig', 'orders', 'trading', 'trade_manager', "
            "'safety', 'strategies', 'requests'}))")
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    assert out.strip() == "[]"


def test_no_trading_part_uses_the_planner_and_there_is_no_authorisation_switch_yet():
    for folder in ("strategies", "trading", "orders", "trade_manager", "safety", "rejection", "analyser", "levels"):
        for f in (ROOT / folder).rglob("*.py"):
            assert "planner" not in f.read_text(), f"{f} mentions the planner"
    from config.switches import SWITCHES
    assert "PLANNER_AUTHORISES_BOUNCE" not in SWITCHES
    assert not hasattr(S.switches if hasattr(S, "switches") else SimpleNamespace(), "planner_authorises_bounce")


# ---- MACD: a cross during the structure is reversal risk; a line still lagging is not (17 November 2026) --------------

def _h4_with_macd_lines(lines):
    from prices.indicators import Macd
    cs = [C("4h", T(2026, 11, 2) + timedelta(hours=4 * i), 4, 100, 101, 99, 100) for i in range(len(lines))]
    m = {c.start: Macd(c.start, D(str(x)), D(0), D(str(x))) for c, x in zip(cs, lines)}
    return SimpleNamespace(candles=cs, macd=m)


def _structure_from(h4, first):
    sw = SimpleNamespace(candle_utc=h4.candles[first].start)
    return SimpleNamespace(highs=[sw, sw], lows=[sw, sw])


@pytest.mark.parametrize("lines,bear,expected", [
    ([5, 4, 3, 2, 1], True, (False, True)),         # downtrend, line never below zero yet: lagging, no veto
    ([5, -1, -2, -1, 2], True, (True, False)),      # went below zero during the downtrend, back above: a cross
    ([-1, -2, -3, -4, -5], True, (False, False)),   # momentum agrees
    ([-5, -4, -3, -2, -1], False, (False, True)),   # uptrend, line never above zero yet
    ([-5, 1, 2, 1, -2], False, (True, False)),      # uptrend: crossed below zero during it
])
def test_the_macd_line_vetoes_only_by_crossing_against_during_the_structure(lines, bear, expected):
    from planner.assess import macd_against
    h4 = _h4_with_macd_lines(lines)
    assert macd_against(h4, _structure_from(h4, 0), bear) == expected


def test_a_cross_before_the_structure_began_does_not_count():
    from planner.assess import macd_against
    h4 = _h4_with_macd_lines([-3, -2, 1, 2, 3])     # below zero only before the structure's first swing (candle 2)
    assert macd_against(h4, _structure_from(h4, 2), True) == (False, True)


# ---- failure isolation, more (pre-deployment review, 17 November 2026) --------------------------------------------------

def test_with_observation_off_the_price_service_never_imports_the_planner():
    code = ("import sys; import prices.service, trading.engine, strategies.common, trade_manager.manager, "
            "orders.sender, safety.rules; print(sorted(m for m in sys.modules if m.split('.')[0] == 'planner'))")
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    assert out.strip() == "[]"


def test_a_planner_that_cannot_write_its_files_fails_alone(tmp_path, monkeypatch):
    import planner.__main__ as main
    blocked = tmp_path / "not-a-folder"
    blocked.write_text("a file where the planner folder should be")
    monkeypatch.setattr(main, "load_settings", lambda **kw: SimpleNamespace(for_pair=lambda p: with_folder(S, blocked)))
    monkeypatch.setattr("housekeeping.logs.setup_logging", lambda *a, **k: None)
    with pytest.raises(OSError):                      # it cannot even make its own folder: it stops, nothing else is touched
        main.main(["run"])
    k = Keeper(with_folder(S, tmp_path / "p"), flat_store(NOW), planner=Script(plan_dict()))
    monkeypatch.setattr(keeper_mod, "safe_write", lambda *a, **k: (_ for _ in ()).throw(OSError("disk full")))
    with pytest.raises(OSError):                      # inside its own process: logged there, the price service never sees it
        k.run(NOW)


def test_a_crashed_planner_process_does_not_stop_the_next_one_starting():
    calls = []

    class Crashed:
        def poll(self):
            return 1                                    # finished, with an error

    u = PlannerUpdater(S, popen=lambda cmd, **kw: calls.append(cmd) or Crashed())
    u(NOW)
    u(NOW + timedelta(minutes=5))
    assert len(calls) == 2


# ---- R1: opportunity labels exactly as FC-04 (owner, 17 November 2026) ------------------------------------------------

@pytest.mark.parametrize("cond,label", [("CONTINUATION", "healthy-trend pullback"), ("EXHAUSTION", "corrective reversal"),
                                        ("CORRECTION_LIKELY", "corrective reversal"),
                                        ("CORRECTION_ACTIVE", "corrective reversal"), ("REVERSAL_RISK", None),
                                        ("INDETERMINATE", None)])
def test_the_opportunity_label_follows_the_condition_class_as_fc_04(cond, label):
    from planner.assess import opportunity_of
    assert opportunity_of(cond) == label


# ---- R2: identity needs the same fixed levels AND an overlapping zone (owner, 17 November 2026) ------------------------

MOVING_ONLY = [("London session high (so far)", "13245", False)]


def test_a_running_session_high_is_a_moving_level_and_a_finished_one_fixed():
    from planner.zones import from_existing
    lv = lambda src: SimpleNamespace(price=D(13245), type="london_session_high", source=src, candle_utc=NOW)   # noqa: E731
    running, done = from_existing(SimpleNamespace(levels=[
        lv("London session today Tue 17 Nov 07:00-12:00 UTC, so far (to 09:00 UTC)"),
        lv("London session previous Mon 16 Nov 07:00-12:00 UTC")]))
    assert (running.fixed, running.name) == (False, "London session high (so far)")
    assert (done.fixed, done.name) == (True, "London session high")


def test_a_moving_only_zone_that_drifts_but_overlaps_keeps_its_identity(tmp_path):
    K(tmp_path, flat_store(NOW), Script(plan_dict(zone=(13240, 13248), levels=MOVING_ONLY))).run(NOW)
    later = NOW + timedelta(hours=1)
    k = K(tmp_path, flat_store(later), Script(plan_dict(zone=(13244, 13252), levels=MOVING_ONLY)))
    k.run(later)
    ev = history(tmp_path)
    assert ev[-1]["event"] == "changed" and "zone edges 13240-13248 to 13244-13252" in ev[-1]["why"]
    assert len({e["id"] for e in ev if e["id"]}) == 1


def test_a_moving_only_zone_that_no_longer_overlaps_is_superseded_with_history_kept(tmp_path):
    k = K(tmp_path, flat_store(NOW), Script(plan_dict(zone=(13240, 13248), levels=MOVING_ONLY)))
    k.run(NOW)
    first = k.state["recommendation"]["id"]
    later = NOW + timedelta(hours=1)
    k = K(tmp_path, flat_store(later), Script(plan_dict(zone=(13290, 13298), levels=MOVING_ONLY)))
    k.run(later)
    ev = history(tmp_path)
    sup = [e for e in ev if e["event"] == "superseded"]
    assert len(sup) == 1 and sup[0]["id"] == first and "does not overlap the previous one" in sup[0]["why"]
    new = k.state["recommendation"]
    assert new["id"] != first and new["entry_zone"]["low"] == "13290" and f"supersedes {first}" in new["status_reason"]
    assert [e["event"] for e in ev if e["id"] == first][:2] == ["created", "waiting"]       # its history is kept
    assert k.state["recent"][0]["id"] == first and k.state["recent"][0]["status"] == SUPERSEDED


def test_the_same_fixed_levels_with_a_non_overlapping_zone_are_still_superseded(tmp_path):
    K(tmp_path, flat_store(NOW), Script(plan_dict(zone=(13240, 13250)))).run(NOW)
    later = NOW + timedelta(hours=1)
    k = K(tmp_path, flat_store(later), Script(plan_dict(zone=(13260, 13270))))
    k.run(later)
    assert history(tmp_path)[-3]["event"] == "superseded"


# ---- R3: the dashboard panel only while PLANNER_OBSERVE is on (owner, 17 November 2026) --------------------------------

def _dashboard(tmp_path, on):
    from dashboard.server import Dashboard
    from tests.planner_helpers import Over, section
    s2 = Over(S, switches=SimpleNamespace(planner_observe=on), planner=section(S.planner, folder=tmp_path / "planner"),
              dashboard=section(S.dashboard, status_folder=tmp_path / "status"),
              trading=section(S.trading, pause_file=tmp_path / "pause"))
    return Dashboard(s2, None, None, now=lambda: NOW)


def test_with_observation_off_the_status_has_no_planner_at_all(tmp_path):
    K(tmp_path, flat_store(NOW), Script(plan_dict())).run(NOW)               # even with a planner file present
    st = _dashboard(tmp_path, False).status({"csrf": "x"})
    assert "planner" not in st


def test_with_observation_on_the_status_carries_the_observe_only_panel(tmp_path):
    K(tmp_path, flat_store(NOW), Script(plan_dict())).run(NOW)
    p = _dashboard(tmp_path, True).status({"csrf": "x"})["planner"]
    assert p["label"] == LABEL and p["recommendation"]["trade"] == "SELL"
    (tmp_path / "planner" / "GBPUSD" / "current.json").write_text("not json")
    assert _dashboard(tmp_path, True).status({"csrf": "x"})["planner"]["available"] is False


def test_the_page_keeps_the_planner_section_hidden_unless_a_planner_block_arrives():
    page = (ROOT / "dashboard" / "static" / "index.html").read_text()
    assert '<div id="stpsection" hidden>' in page
    assert '$("stpsection").hidden = !p;\n  if (!p) return;' in page
