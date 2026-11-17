"""Functional tests for the Structural Trade Planner V1 (OBSERVE ONLY): made-up GBP/USD markets, each built from a price
path into 5-minute, hourly, 4-hour, daily and weekly candles exactly as the price service builds them
(tests/planner_helpers.py), checked against the owner's approved rules (DECISION_REGISTER.md, PARAMETER_APPROVAL_REGISTER.md,
IMPLEMENTATION_READINESS.md, 17 November 2026). No real candles, no IG, no trading records. Nothing here is tuned to
any past trade. Prices are chart (SELL) prices in points (1 point = 1 pip).

The made-up markets (all from Sunday 6 September 2026):
  * a base week in 12250-12320, then a rally in 120/50-pip legs (levels below for later destinations);
  * then a downtrend in 110/55-pip legs (4-hour lower highs and lower lows, swings well over 40 pips);
  * then an ending: a corrective rally after a slowing new low; a fresh new low still accelerating (a healthy trend);
    a slowing new low with a small lift (exhaustion); a break back above the last lower high.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from functools import lru_cache

import pytest

from config.settings_loader import load_settings
from planner.assess import (BEARISH, BULLISH, CONTINUATION, CORRECTION_ACTIVE, CORRECTION_LIKELY, CORRECTIVE, EXHAUSTION,
                            EXTENDED, NEAR, NEUTRAL, PLAUSIBLE, PULLBACK, UNLIKELY, choose_zone, plan_at)
from planner.keeper import SUPERSEDED, WAITING, Keeper
from planner.zones import MAJOR, MINOR, MODERATE, MOVING_AVERAGE, PIVOT, PSYCHOLOGICAL, STRUCTURE, MapLevel, Zone, zones
from prices.model import UK, Candle
from tests.planner_helpers import FakeStore, market, mirrored, with_folder

UTC = timezone.utc
S = load_settings().for_pair("GBPUSD")
START = datetime(2026, 9, 6, 20, 0, tzinfo=UTC)          # Sunday 21:00 UK (BST)
CORRECTIVE_END = [(8, -40), (50, -100), (58, -80)]       # a slow drift to a new low, then a rally
PULLBACK_END = [(10, -70), (20, -135)]                    # a new low, still accelerating
EXHAUSTION_END = [(8, -40), (56, -105), (58, -99), (60, -104)]
CORRECTIVE_GROUP = (EXHAUSTION, CORRECTION_LIKELY, CORRECTION_ACTIVE)


def waypoints(ending):
    w, h, p = [(0, 12300)], 0, 12300
    for _ in range(6):
        h += 10; w.append((h, 12250)); h += 10; w.append((h, 12320))              # noqa: E702
    p = 12320
    for _ in range(12):
        h += 22; p += 120; w.append((h, p)); h += 14; p -= 50; w.append((h, p))   # noqa: E702
    for _ in range(10):
        h += 22; p -= 110; w.append((h, p)); h += 14; p += 55; w.append((h, p))   # noqa: E702
    return w + [(h + x, p + y) for x, y in ending]


@lru_cache(maxsize=None)
def _market(ending):
    return market(S, START, waypoints(list(ending)))


def corrective_market():
    return _market(tuple(CORRECTIVE_END))


def at_end(store):
    t = store.by_tf["5m"][-1].end
    return t, plan_at(S, store, t, calendar=[]).as_dict()


def price(store):
    return store.by_tf["5m"][-1].sell_close


def zone_of(p):
    z = p["entry_zone"]
    return D(z["low"]), D(z["high"])


# ---- 1. an established bearish trend with a corrective rally ---------------------------------------------------------

def test_1_bearish_trend_with_a_corrective_rally_gives_a_sell_zone_above_price_below_the_last_lower_high():
    st = corrective_market()
    t, p = at_end(st)
    assert p["dominant_direction"] == BEARISH and p["condition"] in CORRECTIVE_GROUP
    assert p["opportunity"] == CORRECTIVE and p["trade"] == "SELL"
    assert p["expected_movement"] == "UP into resistance, then DOWN"
    assert any("divergence" in e or "momentum weakening" in e for e in p["condition_evidence"])
    low, high = zone_of(p)
    last_high = D(p["h4_last_swing"]["price"])
    assert p["h4_last_swing"]["kind"] == "high" and low <= last_high               # not beyond the structure
    assert low >= price(st) - 3                                                    # above price, or price in it
    assert p["entry_zone"]["class"] in (MAJOR, MODERATE) and p["reachability"] in (NEAR, PLAUSIBLE)
    d = p["destinations"]
    assert D(d["primary"]["price"]) < low and D(d["intermediate"]["price"]) < low
    assert d["primary"]["zone"]["class"] == MAJOR
    assert D(d["primary"]["price"]) == D(d["primary"]["zone"]["high"])           # the near edge, no offset (D-19)
    inv = p["invalidation"]
    assert D(inv["zone_break_close"]) == high + 3 and D(inv["structure_break_close"]) == last_high + 3
    assert p["selection_reason"] and p["entry_zone"]["families"] and p["entry_zone"]["levels"]
    ref = p["reference_entry"]
    assert low <= D(ref["price"]) <= high and ref["level"] in [m["name"] for m in p["entry_zone"]["levels"]]


# ---- 2. an established bullish trend with a corrective decline (the same market upside down) --------------------------

def test_2_the_mirror_image_bullish_market_gives_the_mirror_image_buy_recommendation():
    up = mirrored(corrective_market())
    t, p = at_end(up)
    _, down = at_end(corrective_market())
    assert p["dominant_direction"] == BULLISH and p["trade"] == "BUY"
    assert p["condition"] == down["condition"] and p["opportunity"] == down["opportunity"] == CORRECTIVE
    assert p["expected_movement"] == "DOWN into support, then UP"
    low, high = zone_of(p)
    last_low = D(p["h4_last_swing"]["price"])
    assert p["h4_last_swing"]["kind"] == "low" and high >= last_low and high <= price(up) + 3
    assert D(p["destinations"]["primary"]["price"]) > high
    assert D(p["invalidation"]["zone_break_close"]) == low - 3
    assert D(p["invalidation"]["structure_break_close"]) == last_low - 3


# ---- 3. a healthy-trend pullback -------------------------------------------------------------------------------------

def test_3_a_healthy_trend_is_a_pullback_opportunity_without_needing_exhaustion():
    st = _market(tuple(PULLBACK_END))
    t, p = at_end(st)
    assert p["dominant_direction"] == BEARISH and p["condition"] == CONTINUATION
    assert p["opportunity"] == PULLBACK and p["trade"] == "SELL" and p["no_recommendation"] is None
    assert not any("momentum weakening" in e or "divergence" in e for e in p["condition_evidence"])
    low, _ = zone_of(p)
    assert low > price(st)                                                         # waits for a retrace up into it


# ---- 4. exhaustion without a confirmed reversal ----------------------------------------------------------------------

def test_4_exhaustion_is_not_a_reversal_the_trade_stays_with_the_4_hour_trend():
    t, p = at_end(_market(tuple(EXHAUSTION_END)))
    assert p["condition"] in (EXHAUSTION, CORRECTION_LIKELY)
    assert any("exhaustion" in e for e in p["condition_evidence"])
    assert p["dominant_direction"] == BEARISH and p["trade"] == "SELL"            # never a buy on exhaustion
    assert not any("structure broken" in e for e in p["direction_evidence"])


# ---- 5. conflicting higher-timeframe evidence -------------------------------------------------------------------------

def _daily_uptrend(store):
    """The same market, but with daily candles in a clear daily uptrend (4 days up 250, 3 days down 120)."""
    days = [c for c in store.by_tf["1d"]]
    out, p, k = [], D(11000), 0
    for c in days:
        if c.start.astimezone(UK).weekday() == 6:                                 # IG's short Sunday candle
            out.append(Candle("1d", c.start, c.end, p + 1, p + 3, p, p + 1, p, p + 2, p - 1, p))
            continue
        step = D(62) if k % 7 < 4 else D(-40)
        o, cl = p, p + step
        out.append(Candle("1d", c.start, c.end, o + 1, max(o, cl) + 6, min(o, cl) - 5, cl + 1,
                          o, max(o, cl) + 5, min(o, cl) - 6, cl))
        p, k = cl, k + 1
    return FakeStore({**store.by_tf, "1d": out})


def test_5_when_the_daily_disagrees_the_4_hour_still_decides_and_the_conflict_is_shown():
    st = _daily_uptrend(corrective_market())
    t, p = at_end(st)
    assert p["dominant_direction"] == BEARISH
    assert p["observations"]["daily_structure"].startswith("higher highs and higher lows")
    assert any("daily structure (up) is against the 4-hour structure (down)" in e for e in p["direction_evidence"])
    assert p["trade"] in ("SELL", None)                                            # never a buy against the 4-hour


# ---- 6. strong structural confluence (the owner's own example, 17 November 2026) ---------------------------------------

def _lv(price, name, fam, dw, fixed=True, kind=None):
    return MapLevel(D(price), name, fam, "daily" if dw else "1h", kind, datetime(2026, 11, 16, tzinfo=UTC), dw, fixed)


def test_6_the_owners_resistance_area_1_3241_to_1_3250_is_one_major_zone_of_four_families():
    levels = [_lv("13240.9", "H1 EMA100", MOVING_AVERAGE, False, False, "moving average"),
              _lv("13243.2", "hourly swing high", STRUCTURE, False, True, "hourly swing"),
              _lv("13243.7", "daily R2", PIVOT, True, True, "daily R/S"),
              _lv("13249.0", "4-hour swing low", STRUCTURE, False, True, "4-hour swing"),     # former support
              _lv("13250", "round number", PSYCHOLOGICAL, False, True, "psychological")]
    zs = zones(S, levels, D("72.7"), [])                                           # 20-day ADR about 73 pips
    assert len(zs) == 1
    z = zs[0]
    assert (z.low, z.high) == (D("13240.9"), D("13250"))
    assert z.klass == MAJOR and z.families == sorted({MOVING_AVERAGE, STRUCTURE, PIVOT, PSYCHOLOGICAL})
    assert len(z.members) == 5 and z.reference.name == "daily R2"                  # the most significant level
    narrow = zones(S, levels, D(30), [])                                           # a quiet market: 5-pip zones
    assert len(narrow) == 2


# ---- 7 and 8. competing zones and intermediate obstacles --------------------------------------------------------------

def Zn(low, high, klass):
    return Zone(D(low), D(high), [], [], klass, klass == MAJOR)


class Swing:
    kind, price = "high", D(13300)


def test_7_the_strongest_reachable_zone_wins_not_simply_the_nearest_and_ties_go_to_the_nearer():
    zs = [Zn(13205, 13212, MODERATE), Zn(13240, 13250, MAJOR), Zn(13215, 13216, MINOR)]
    looked, good = choose_zone(S, zs, D(13200), True, Swing, D(72.7))
    assert good[0][0].low == D(13240)                                             # Major beats the nearer Moderate
    assert all(z.klass != MINOR for z, *_ in good)                                 # Minor is never an entry zone
    two = [Zn(13270, 13275, MAJOR), Zn(13230, 13236, MAJOR)]
    _, good = choose_zone(S, two, D(13200), True, Swing, D(72.7))
    assert good[0][0].low == D(13230)


def test_8_a_major_zone_in_between_makes_the_further_zone_extended_a_moderate_one_does_not():
    zs = [Zn(13220, 13226, MAJOR), Zn(13260, 13270, MAJOR)]
    looked, good = choose_zone(S, zs, D(13200), True, Swing, D(72.7))
    reach = {z.low: r for z, r, *_ in looked}
    assert reach[D(13260)] == EXTENDED and reach[D(13220)] == PLAUSIBLE and good[0][0].low == D(13220)
    zs = [Zn(13220, 13226, MODERATE), Zn(13260, 13270, MAJOR)]
    looked, good = choose_zone(S, zs, D(13200), True, Swing, D(72.7))
    assert {z.low: r for z, r, *_ in looked}[D(13260)] == PLAUSIBLE and good[0][0].low == D(13260)
    beyond = [Zn(13310, 13320, MAJOR)]                                             # above the last lower high 13300
    looked, good = choose_zone(S, beyond, D(13200), True, Swing, D(72.7))
    assert looked[0][1] == UNLIKELY and good == []


def test_8b_distance_and_adr_never_rule_a_zone_out_by_themselves():
    far = [Zn(13290, 13299, MAJOR)]                                                # 90 pips: over today's ADR of 40
    looked, good = choose_zone(S, far, D(13200), True, Swing, D(40))
    assert looked[0][1] == PLAUSIBLE and good and looked[0][3]["distance_adr"] == "2.25"


# ---- 9. structural invalidation --------------------------------------------------------------------------------------

def test_9_a_close_back_above_the_last_lower_high_ends_the_bearish_view_and_its_sell():
    st = corrective_market()
    _, before = at_end(st)
    last_high = float(before["h4_last_swing"]["price"])
    w = waypoints(CORRECTIVE_END)
    h, p = w[-1]
    broken = market(S, START, w + [(h + 12, last_high + 25), (h + 20, last_high + 30)])
    _, after = at_end(broken)
    assert after["dominant_direction"] != BEARISH and after["trade"] != "SELL"
    if after["dominant_direction"] == "TRANSITIONAL":
        assert any("structure broken" in e for e in after["direction_evidence"])


# ---- 10. daily pivot rollover ----------------------------------------------------------------------------------------

def test_10_at_the_uk_midnight_rollover_the_plan_uses_the_new_days_pivots():
    st = corrective_market()
    end = st.by_tf["5m"][-1].end
    midnight = end.astimezone(UK).replace(hour=0, minute=0, second=0, microsecond=0)
    before = plan_at(S, st, midnight - timedelta(minutes=10), calendar=[]).as_dict()
    after = plan_at(S, st, midnight + timedelta(minutes=10), calendar=[]).as_dict()
    assert before["observations"]["vs_daily_pivot"] != after["observations"]["vs_daily_pivot"]
    from levels.rules import daily_pivots
    prev_day = [c for c in st.by_tf["1d"] if c.end == midnight.astimezone(UTC)][0]
    p = [lv.price for lv in daily_pivots(prev_day, "sell", 1, "") if lv.type == "pivot"][0]
    assert after["observations"]["vs_daily_pivot"].endswith(str(p))


def test_10b_a_zone_built_on_the_old_days_pivots_is_superseded_and_its_history_kept(tmp_path):
    from tests.technical.test_planner import Script, flat_store, plan_dict
    night = datetime(2026, 11, 17, 23, 2, tzinfo=UTC)
    old = plan_dict(levels=[("daily R2", "13243.7", True), ("hourly swing high", "13243.2", True)])
    new = plan_dict(levels=[("daily R1", "13241.0", True), ("hourly swing high", "13243.2", True)])
    Keeper(with_folder(S, tmp_path / "p"), flat_store(night), planner=Script(old)).run(night)
    k = Keeper(with_folder(S, tmp_path / "p"), flat_store(night + timedelta(hours=1)), planner=Script(new))
    k.run(night + timedelta(hours=1))
    assert k.state["recent"][0]["status"] == SUPERSEDED and k.state["recommendation"]["status"] == WAITING
    lines = (tmp_path / "p" / "GBPUSD" / "recommendations.jsonl").read_text().count('"event": "superseded"')
    assert lines == 1


# ---- 11. the 4-hour EMA200 not warmed up -------------------------------------------------------------------------------

def test_11_without_the_4_hour_ema200_the_planner_still_works_and_never_uses_a_guessed_value():
    st = corrective_market()
    assert len(st.by_tf["4h"]) < 592
    _, p = at_end(st)
    assert any(w.startswith("4h EMA200") for w in p["warming_up"])
    assert p["observations"]["h4_ema200"] == "warming up"
    assert "4-hour EMA200: warming up (not used)" in p["direction_evidence"]
    names = [m["name"] for m in p["entry_zone"]["levels"]] + [x for c in p["candidates"] for x in c["levels"]]
    assert not any("H4 EMA200" in n for n in names)
    assert p["no_recommendation"] is None


# ---- 12. stale market data ---------------------------------------------------------------------------------------------

def test_12_stale_data_stops_the_recommendation_counting_as_current_but_does_not_end_it(tmp_path):
    st = corrective_market()
    end = st.by_tf["5m"][-1].end
    k = Keeper(with_folder(S, tmp_path / "p"), st)
    k.run(end)
    rec = k.state["recommendation"]
    assert rec is not None and k.state["current"] is True
    k = Keeper(with_folder(S, tmp_path / "p"), st)
    k.run(end + timedelta(minutes=40))                                             # no new candle for 40 minutes
    assert k.state["data_fresh"] is False and k.state["current"] is False
    assert k.state["recommendation"]["id"] == rec["id"] and k.state["recommendation"]["status"] in ("WAITING", "ACTIVE")


# ---- 13. no defensible recommendation ----------------------------------------------------------------------------------

def test_13_a_ranging_market_with_mixed_swings_gets_no_recommendation_and_says_why():
    w, h, amp = [(0, 12450)], 0, 30
    for _ in range(30):
        h += 18; w.append((h, 12450 + amp)); h += 18; w.append((h, 12450 - amp)); amp += 4      # noqa: E702
    _, p = at_end(market(S, START, w))
    assert p["dominant_direction"] == NEUTRAL and p["trade"] is None and p["entry_zone"] is None
    assert "NEUTRAL" in p["no_recommendation"]


def test_13b_without_a_major_destination_there_is_no_recommendation():
    w = [(0, 13900)]
    h, p = 0, 13900
    for _ in range(18):                                                             # only a downtrend: nothing below
        h += 22; p -= 110; w.append((h, p)); h += 14; p += 55; w.append((h, p))   # noqa: E702
    _, plan = at_end(market(S, START, w + [(h + 14, p - 70), (h + 28, p - 140)]))
    assert plan["trade"] == "SELL" and plan["entry_zone"] is None
    assert "no Major support zone below the entry zone" in plan["no_recommendation"]


# ---- the real candle store (on the server only; read only) --------------------------------------------------------------

def test_real_store_four_hour_candles_rebuilt_from_hourly_equal_the_stored_ones():
    """D-31: on the real GBPUSD store, every stored 4-hour candle equals the one rebuilt from the stored hourly
    candles (checked 17 November 2026: all 104 from 25 October). Reads the store only."""
    from prices.store import CandleStore
    from planner.measure import four_hour_from_hourly
    if not (S.candles.folder / "4h").is_dir():
        pytest.skip("the real candle store is only on the server")
    st = CandleStore(S.candles.folder, S.candles.compress_after_days)
    end = datetime(2026, 11, 17, 8, tzinfo=UTC)
    native = [c for c in st.read_range("4h", datetime(2026, 10, 25, tzinfo=UTC), end) if c.end <= end]
    hourly = st.read_range("1h", datetime(2026, 10, 24, tzinfo=UTC), end)
    rebuilt = {c.start: c for c in four_hour_from_hourly(S, hourly, end)}
    assert len(native) >= 100
    assert all(rebuilt[c.start].prices() == c.prices() for c in native)


# ---- 14 to 17. MACD supports, the 4-hour structure decides (correction of 17 November 2026) ------------------------------
# Straight after a long rally the slow MACD 35/45/30 line is still above zero when the 4-hour structure has already
# turned down. The approved rule (D-10) is a MACD line CROSSING above zero during the structure; a line that has not
# yet fallen below zero is momentum lagging, recorded as supporting evidence, never a veto.

def rally_then_drop(ending):
    w, h, p = [(0, 12000)], 0, 12000
    for _ in range(7):                                                              # a long rally: +300 / -150
        h += 40; p += 300; w.append((h, p)); h += 30; p -= 150; w.append((h, p))   # noqa: E702
    h += 40; p += 300; w.append((h, p))                                             # noqa: E702
    for _ in range(4):                                                              # then 4-hour lower highs and lows
        h += 12; p -= 70; w.append((h, p)); h += 14; p += 45; w.append((h, p))     # noqa: E702
    for x, y in ending:
        h += x; p += y; w.append((h, p))                                            # noqa: E702
    return w


@lru_cache(maxsize=None)
def _lagging(ending):
    return market(S, START, rally_then_drop(list(ending)))


LAG_CORRECTION = ((10, -50), (30, -40), (8, 25))
LAG_PULLBACK = ((10, -60), (10, -50))


def test_14_a_confirmed_4_hour_downtrend_with_the_macd_line_still_positive_is_not_vetoed():
    st = _lagging(LAG_CORRECTION)
    t, p = at_end(st)
    assert D(p["observations"]["h4_macd"]["line"]) > 0                             # MACD still positive
    assert p["dominant_direction"] == BEARISH and p["condition"] != "REVERSAL_RISK"
    assert p["trade"] == "SELL" and p["no_recommendation"] is None
    assert any("momentum has not yet confirmed the new 4-hour downtrend (supporting evidence only, not a veto)" in e
               for e in p["condition_evidence"])


def test_15_a_confirmed_4_hour_uptrend_with_the_macd_line_still_negative_is_not_vetoed():
    t, p = at_end(mirrored(_lagging(LAG_CORRECTION)))
    assert D(p["observations"]["h4_macd"]["line"]) < 0
    assert p["dominant_direction"] == BULLISH and p["condition"] != "REVERSAL_RISK"
    assert p["trade"] == "BUY" and p["no_recommendation"] is None
    assert any("not yet confirmed the new 4-hour uptrend" in e for e in p["condition_evidence"])


def test_16_a_healthy_pullback_opportunity_survives_lagging_macd_in_both_directions():
    for store, trade in ((_lagging(LAG_PULLBACK), "SELL"), (mirrored(_lagging(LAG_PULLBACK)), "BUY")):
        t, p = at_end(store)
        assert p["condition"] == CONTINUATION and p["opportunity"] == PULLBACK and p["trade"] == trade
        assert p["no_recommendation"] is None


def test_17_corrective_reversals_are_unchanged_by_the_correction():
    t, p = at_end(corrective_market())                                             # MACD below zero all along
    assert D(p["observations"]["h4_macd"]["line"]) < 0 and p["opportunity"] == CORRECTIVE and p["trade"] == "SELL"
    assert not any("not yet confirmed" in e for e in p["condition_evidence"])
