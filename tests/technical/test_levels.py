"""Technical tests for the levels part, with made-up candles. Never contacts IG.

Prices are in IG's points (13450 means 1.3450); one pip is one point."""

import dataclasses
import json
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace

import pytest

from levels import rules
from levels.current import LevelsUpdater, build, previous_trading_day, read_current, write_current
from levels.rules import (IMPORTANT_TYPES, PIVOT, R1, R2, R3, ROUND_NUMBER, S1, S2, S3, Level,
                          daily_pivots, group_levels, round_numbers, turning_levels)
from prices.calendar import Boundaries, MarketHours
from prices.feed import PriceFeed
from prices.model import Candle
from prices.store import CandleStore
from tests.technical.fake_stream import SETTINGS, T

ROOT = Path(__file__).resolve().parents[2]
UTC = timezone.utc


def settings(tmp_path, **levels_over):
    lv = {k: v for k, v in vars(SETTINGS.levels).items() if not k.startswith("_")}
    lv.update(folder=tmp_path / "levels", **levels_over)
    cs = {k: v for k, v in vars(SETTINGS.candles).items() if not k.startswith("_")}
    cs.update(folder=tmp_path / "candles" / "GBPUSD")
    return SimpleNamespace(levels=SimpleNamespace(**lv), market=SETTINGS.market, chart=SETTINGS.chart,
                           market_hours=SETTINGS.market_hours, candles=SimpleNamespace(**cs),
                           housekeeping=SETTINGS.housekeeping)


def candle(tf, start, minutes, h, l, c=None, o=None, spread=D("1.5")):
    """A made-up candle. The SELL prices (the chart price) are as given; the buy
    prices are the sell prices plus a spread, so a test can tell if the buy
    price was used by mistake."""
    h, l = D(str(h)), D(str(l))
    c = D(str(c)) if c is not None else (h + l) / 2
    o = D(str(o)) if o is not None else c
    return Candle(tf, start, start + timedelta(minutes=minutes), o + spread, h + spread, l + spread, c + spread,
                  o, h, l, c)


def hourly(start, pairs):
    """Consecutive hourly candles from (high, low) pairs."""
    return [candle("1h", start + timedelta(hours=i), 60, h, l) for i, (h, l) in enumerate(pairs)]


def describe(c, side):
    return f"{c.start:%H:%M} {side}"


# ---- 1. daily pivots -------------------------------------------------------------------

def test_pivots_use_high_low_close_over_3_and_the_classic_formulas():
    day = candle("1d", T(2026, 11, 5), 1440, h=13501.6, l=13446.8, c=13456.7)
    p = {lv.type: lv.price for lv in daily_pivots(day, "sell", 1, "x")}
    P = (D("13501.6") + D("13446.8") + D("13456.7")) / 3          # 13468.3666...
    H, L = D("13501.6"), D("13446.8")
    exact = {PIVOT: P, R1: 2 * P - L, S1: 2 * P - H, R2: P + (H - L), S2: P - (H - L),
             R3: H + 2 * (P - L), S3: L - 2 * (H - P)}
    for t, v in exact.items():
        assert p[t] == v.quantize(D("0.1")), t
    assert p == {PIVOT: D("13468.4"), R1: D("13489.9"), S1: D("13435.1"), R2: D("13523.2"),
                 S2: D("13413.6"), R3: D("13544.7"), S3: D("13380.3")}


def test_the_chart_price_is_the_sell_price():
    assert SETTINGS.chart.price == "sell"


def test_pivots_use_the_sell_price_not_the_buy_price(tmp_path):
    day = candle("1d", T(2026, 11, 5), 1440, h=100.0, l=70.0, c=90.0, spread=D(10))
    p = {lv.type: lv.price for lv in daily_pivots(day, "sell", 1, "x")}
    assert p[PIVOT] == D("86.7")            # (100 + 70 + 90) / 3, sell prices
    assert day.buy_high == D("110.0")       # the buy side would have given 96.7
    # Through the settings: the chart price (sell) is used, never mixed with buy.
    ll = build(settings(tmp_path), _store_with_days(tmp_path, [
        candle("1d", T(2026, 11, 5), 1440, h=13501.6, l=13446.8, c=13456.7, spread=D(10))]), T(2026, 11, 6, 9))
    assert ll.side == "sell" and ll.of_type(PIVOT)[0].price == D("13468.4")
    assert "(sell H 13501.6 L 13446.8 C 13456.7)" in ll.of_type(PIVOT)[0].source


def test_pivot_decimals_come_from_the_settings():
    day = candle("1d", T(2026, 11, 5), 1440, h=13501.6, l=13446.8, c=13456.7)
    assert {lv.type: lv.price for lv in daily_pivots(day, "sell", 3, "x")}[PIVOT] == D("13468.367")


def _store_with_days(tmp_path, days):
    store = CandleStore(tmp_path / "candles" / "GBPUSD", 30)
    for c in days:
        store.add(c)
    return store


def test_friday_pivots_come_from_thursdays_daily_candle(tmp_path):
    thu = candle("1d", T(2026, 11, 5), 1440, h=13501.6, l=13446.8, c=13456.7)
    wed = candle("1d", T(2026, 11, 4), 1440, h=13600, l=13400, c=13500)
    store = _store_with_days(tmp_path, [wed, thu])
    ll = build(settings(tmp_path), store, T(2026, 11, 6, 9))
    assert ll.previous_day.start == T(2026, 11, 5)
    assert ll.of_type(PIVOT)[0].price == D("13468.4")
    assert "Thu 05 Nov" in ll.of_type(PIVOT)[0].source


def test_monday_pivots_come_from_the_short_sunday_candle_like_igs_chart(tmp_path):
    # Sunday 1 Nov: IG's short daily candle, labelled 00:00, holding 21:00 to midnight.
    fri = candle("1d", T(2026, 10, 30), 21 * 60, h=13434.7, l=13374.8, c=13394.3)
    sun = candle("1d", T(2026, 11, 1), 1440, h=13401.7, l=13384.2, c=13386.1)
    store = _store_with_days(tmp_path, [fri, sun])
    ll = build(settings(tmp_path), store, T(2026, 11, 2, 8))
    assert ll.previous_day.start == T(2026, 11, 1)                       # Sunday, not Friday
    P = (D("13401.7") + D("13384.2") + D("13386.1")) / 3
    assert ll.of_type(PIVOT)[0].price == P.quantize(D("0.1"))
    assert {lv.price for lv in ll.of_type("previous_day_high")} == {D("13401.7")}


def test_sundays_levels_come_from_friday_and_the_weekend_is_skipped(tmp_path):
    b = Boundaries(SETTINGS.candles, MarketHours(SETTINGS.market_hours))
    assert previous_trading_day(b, T(2026, 11, 1))[0] == T(2026, 10, 30)      # Sunday -> Friday
    assert previous_trading_day(b, T(2026, 11, 2))[0] == T(2026, 11, 1)       # Monday -> Sunday
    assert previous_trading_day(b, T(2026, 11, 4))[0] == T(2026, 11, 3)       # Wednesday -> Tuesday


def test_no_pivots_if_the_previous_days_candle_is_not_stored_yet(tmp_path):
    wed = candle("1d", T(2026, 11, 4), 1440, h=13600, l=13400, c=13500)
    store = _store_with_days(tmp_path, [wed])
    ll = build(settings(tmp_path), store, T(2026, 11, 6, 0, 5))     # Thursday's candle missing
    assert not ll.of_type(PIVOT) and not ll.of_type("previous_day_low")
    assert any("Thu 05 Nov" in w and "not stored yet" in w for w in ll.warnings)


def test_a_previous_day_missing_some_5_minute_candles_is_used_with_a_warning(tmp_path):
    thu = candle("1d", T(2026, 11, 5), 1440, h=13501.6, l=13446.8, c=13456.7)
    thu = dataclasses.replace(thu, parts=280, expected_parts=288)
    store = _store_with_days(tmp_path, [thu])
    ll = build(settings(tmp_path), store, T(2026, 11, 6, 9))
    assert ll.of_type(PIVOT)
    assert any("missing 8" in w for w in ll.warnings)


# ---- 2. other levels -------------------------------------------------------------------

def test_round_numbers_end_in_00_and_50_within_the_set_distance_both_ends_included():
    got = [lv.price for lv in round_numbers(D("13457.4"), D(50), D(150))]
    assert got == [D(13350), D(13400), D(13450), D(13500), D(13550), D(13600)]
    edge = [lv.price for lv in round_numbers(D("13450"), D(50), D(100))]
    assert edge == [D(13350), D(13400), D(13450), D(13500), D(13550)]
    assert all(lv.type == ROUND_NUMBER and lv.important for lv in round_numbers(D(13450), D(50), D(50)))


def test_round_numbers_are_around_the_latest_sell_close(tmp_path):
    store = CandleStore(tmp_path / "candles" / "GBPUSD", 30)
    store.add(candle("5m", T(2026, 11, 6, 9), 5, 13462, 13455, c=13460.0, spread=D(30)))
    ll = build(settings(tmp_path, round_numbers_within_pips=60), store, T(2026, 11, 6, 9, 5))
    assert ll.reference_price == D("13460.0")
    assert [lv.price for lv in ll.of_type(ROUND_NUMBER)] == [D(13400), D(13450), D(13500)]


def test_previous_day_high_and_low_use_the_sell_price(tmp_path):
    thu = candle("1d", T(2026, 11, 5), 1440, h=13501.6, l=13446.8, c=13456.7)
    ll = build(settings(tmp_path), _store_with_days(tmp_path, [thu]), T(2026, 11, 6, 9))
    assert [lv.price for lv in ll.of_type("previous_day_high")] == [D("13501.6")]
    assert [lv.price for lv in ll.of_type("previous_day_low")] == [D("13446.8")]


def _day_of_5m(store, day, highs_lows):
    """5-minute candles at the given UTC times: {(h, m): (high, low)}."""
    for (h, m), (hi, lo) in highs_lows.items():
        store.add(candle("5m", day.replace(hour=h, minute=m), 5, hi, lo, spread=D(20)))


def test_london_and_new_york_session_highs_and_lows_use_utc_times_from_the_settings(tmp_path):
    store = CandleStore(tmp_path / "candles" / "GBPUSD", 30)
    _day_of_5m(store, T(2026, 11, 5), {
        (6, 55): (13600, 13300),            # before London (07:00 UTC): not used
        (7, 0): (13480, 13470), (9, 30): (13490, 13460), (11, 55): (13485, 13465),
        (12, 0): (13500, 13440),            # 12:00 starts New York, not London
        (20, 55): (13470, 13450),
        (21, 0): (13700, 13200),            # after New York (21:00 UTC): not used
    })
    ll = build(settings(tmp_path), store, T(2026, 11, 5, 23, 0))
    by = {lv.type: lv.price for lv in ll.levels}
    assert by["london_session_high"] == 13490 and by["london_session_low"] == 13460
    assert by["new_york_session_high"] == 13500 and by["new_york_session_low"] == 13440
    # Other times in the settings change the result.
    ll2 = build(settings(tmp_path, london_session_from=SETTINGS.levels.london_session_from.replace(hour=6)),
                store, T(2026, 11, 5, 23, 0))
    assert {lv.type: lv.price for lv in ll2.levels}["london_session_high"] == 13600


def test_a_running_session_counts_only_finished_candles_and_says_so_far(tmp_path):
    store = CandleStore(tmp_path / "candles" / "GBPUSD", 30)
    _day_of_5m(store, T(2026, 11, 5), {(7, 0): (13480, 13470), (7, 5): (13495, 13465), (7, 10): (13999, 13001)})
    ll = build(settings(tmp_path), store, T(2026, 11, 5, 7, 12))        # 07:10 candle not finished
    hi = ll.of_type("london_session_high")[0]
    assert hi.price == 13495 and "so far" in hi.source
    assert not ll.of_type("new_york_session_high")


def test_the_previous_days_sessions_are_levels_too(tmp_path):
    store = CandleStore(tmp_path / "candles" / "GBPUSD", 30)
    _day_of_5m(store, T(2026, 11, 4), {(8, 0): (13420, 13410), (15, 0): (13440, 13400)})
    _day_of_5m(store, T(2026, 11, 5), {(8, 0): (13480, 13470)})
    ll = build(settings(tmp_path), store, T(2026, 11, 5, 9))
    london_highs = sorted(lv.price for lv in ll.of_type("london_session_high"))
    assert london_highs == [13420, 13480]
    assert [lv.price for lv in ll.of_type("new_york_session_low")] == [13400]
    assert any("previous Wed 04 Nov" in lv.source for lv in ll.of_type("new_york_session_low"))


# ---- turning levels ----------------------------------------------------------------------

S = T(2026, 11, 2, 0)


def test_a_clear_hourly_high_and_low_are_turning_levels():
    hs = hourly(S, [(110, 100), (112, 102), (115, 105), (140, 120), (125, 112), (118, 104), (116, 103),
                    (114, 100), (120, 101), (130, 115)])
    got = turning_levels(hs, "sell", S, 3, D(20), 6, describe)
    assert [(lv.type, lv.price) for lv in got] == [("turning_high", D(140))]
    assert got[0].important and got[0].candle_utc == S + timedelta(hours=3)


def test_a_turning_low_needs_lower_than_its_neighbours_and_a_clear_bounce():
    lows = hourly(S, [(130, 120), (128, 118), (126, 116), (110, 90), (115, 100), (120, 104), (125, 108),
                      (130, 112)])
    got = turning_levels(lows, "sell", S, 3, D(20), 6, describe)
    assert [(lv.type, lv.price) for lv in got] == [("turning_low", D(90))]


def test_no_turning_level_without_a_big_enough_move_within_the_set_candles():
    hs = hourly(S, [(110, 100), (112, 102), (115, 105), (140, 125), (139, 125), (138, 124), (137, 123),
                    (136, 121), (135, 121), (134, 121), (130, 110)])
    # From 140, the low must reach 120 or below within 6 candles: it only reaches 121.
    assert turning_levels(hs, "sell", S, 3, D(20), 6, describe) == []
    # The 110 low comes 7 candles later: allowed only if the window is 7.
    assert [lv.price for lv in turning_levels(hs, "sell", S, 3, D(20), 7, describe)] == [D(140)]
    # A smaller move setting lets it count.
    assert [lv.price for lv in turning_levels(hs, "sell", S, 3, D(19), 6, describe)] == [D(140)]


def test_the_high_must_beat_every_candle_on_each_side():
    hs = hourly(S, [(110, 100), (141, 102), (115, 105), (140, 110), (125, 112), (118, 104), (116, 103),
                    (114, 100)])
    assert all(lv.price != 140 for lv in turning_levels(hs, "sell", S, 3, D(20), 6, describe))   # 141 before it
    hs2 = hourly(S, [(110, 100), (112, 102), (115, 105), (140, 110), (125, 112), (141, 104), (116, 103),
                     (114, 100), (113, 90), (112, 95)])
    assert all(lv.price != 140 for lv in turning_levels(hs2, "sell", S, 3, D(20), 6, describe))  # 141 after it


def test_of_two_equal_highs_side_by_side_the_first_counts_once():
    hs = hourly(S, [(110, 100), (112, 102), (115, 105), (140, 120), (140, 118), (118, 104), (116, 103),
                    (114, 100), (113, 99)])
    got = [lv for lv in turning_levels(hs, "sell", S, 3, D(20), 6, describe) if lv.type == "turning_high"]
    assert [(lv.price, lv.candle_utc) for lv in got] == [(D(140), S + timedelta(hours=3))]


def test_the_number_of_candles_each_side_is_a_setting():
    hs = hourly(S, [(110, 100), (139, 102), (115, 105), (140, 110), (125, 112), (118, 104), (116, 103),
                    (114, 100), (113, 98)])
    assert [lv.price for lv in turning_levels(hs, "sell", S, 1, D(20), 6, describe)
            if lv.type == "turning_high"] == [D(139), D(140)]
    assert [lv.price for lv in turning_levels(hs, "sell", S, 2, D(20), 6, describe)
            if lv.type == "turning_high"] == [D(140)]


def test_a_turning_level_needs_the_candles_after_it_to_exist():
    hs = hourly(S, [(110, 100), (112, 102), (115, 105), (140, 110), (100, 90), (99, 89)])
    assert turning_levels(hs, "sell", S, 3, D(20), 6, describe) == []          # only 2 candles after it


def test_turning_levels_older_than_the_lookback_are_left_out_and_sell_prices_are_used(tmp_path):
    store = CandleStore(tmp_path / "candles" / "GBPUSD", 30)
    pattern = [(110, 100), (112, 102), (115, 105), (140, 120), (125, 112), (118, 104), (116, 103), (114, 100)]
    for start in (T(2026, 10, 19), T(2026, 11, 2)):                 # 18 days and 4 days before
        for c in hourly(start, pattern):
            store.add(Candle(c.timeframe, c.start, c.end, *(p + 13000 for p in c.prices())))
    ll = build(settings(tmp_path), store, T(2026, 11, 6, 9))
    got = ll.of_type("turning_high")
    assert [(lv.price, lv.candle_utc) for lv in got] == [(D(13140), T(2026, 11, 2, 3))]
    assert "hourly candle" in got[0].source
    ll3 = build(settings(tmp_path, turning_levels_lookback_weeks=3), store, T(2026, 11, 6, 9))
    assert len(ll3.of_type("turning_high")) == 2


# ---- 3. levels that line up -----------------------------------------------------------------

def L(price, t=ROUND_NUMBER):
    return rules.make(D(str(price)), t, "made up", None)


def test_levels_within_5_pips_are_grouped_and_each_group_lists_its_levels():
    levels, groups = group_levels([L(13450), L("13446.8", "previous_day_low"), L("13455.1", "R1"),
                                   L("13468.4", PIVOT), L("13470.0", "turning_high")], D(5))
    assert [(g["group"], [f"{m.type} {m.price}" for m in g["members"]]) for g in groups] == [
        (1, ["previous_day_low 13446.8", "round_number 13450"]),
        (2, ["R1 13455.1"]),
        (3, ["pivot 13468.4", "turning_high 13470.0"]),        # the pivot can be grouped
    ]
    assert {lv.type: lv.group for lv in levels} == {"previous_day_low": 1, ROUND_NUMBER: 1, "R1": 2,
                                                   PIVOT: 3, "turning_high": 3}


def test_exactly_5_pips_apart_lines_up_and_more_than_5_does_not():
    _, g = group_levels([L(13450), L(13455)], D(5))
    assert len(g) == 1
    _, g = group_levels([L(13450), L("13455.1")], D(5))
    assert len(g) == 2


def test_every_level_in_a_group_is_within_5_pips_of_every_other():
    # 13450, 13454, 13458: each next one is within 5 of the one before, but 13458
    # is 8 from 13450, so it starts a new group.
    _, g = group_levels([L(13450), L(13454), L(13458)], D(5))
    assert [[m.price for m in x["members"]] for x in g] == [[D(13450), D(13454)], [D(13458)]]
    for x in g:
        assert x["high"] - x["low"] <= 5


def test_the_grouping_distance_is_the_setting(tmp_path):
    _, g = group_levels([L(13450), L(13457)], D(SETTINGS.levels.line_up_within_pips))
    assert len(g) == 2
    _, g = group_levels([L(13450), L(13457)], D(8))
    assert len(g) == 1


def test_the_levels_that_matter_most_are_marked():
    assert IMPORTANT_TYPES == {"S2", "R2", "pivot", "round_number", "turning_high", "turning_low"}
    day = candle("1d", T(2026, 11, 5), 1440, h=13501.6, l=13446.8, c=13456.7)
    marks = {lv.type: lv.important for lv in daily_pivots(day, "sell", 1, "x")}
    assert marks == {PIVOT: True, R1: False, R2: True, R3: False, S1: False, S2: True, S3: False}
    _, g = group_levels([L(13300, "R1"), L(13302, "turning_low"), L(13400, "S1")], D(5))
    assert [x["important"] for x in g] == [True, False]


# ---- 4. output: one current list, updated when a candle is stored ------------------------------

def _full_store(tmp_path):
    store = CandleStore(tmp_path / "candles" / "GBPUSD", 30)
    store.add(candle("1d", T(2026, 11, 5), 1440, h=13501.6, l=13446.8, c=13456.7))
    _day_of_5m(store, T(2026, 11, 6), {(7, 0): (13460, 13448), (7, 5): (13462, 13451)})
    return store


def test_the_current_list_has_price_type_source_and_group_for_every_level(tmp_path):
    s = settings(tmp_path)
    ll = build(s, _full_store(tmp_path), T(2026, 11, 6, 7, 10))
    path = write_current(s.levels.folder, ll, T(2026, 11, 6, 7, 10))
    assert path == tmp_path / "levels" / "current.json"
    data = read_current(s.levels.folder)
    assert data["price_used"] == "sell" and data["as_of_utc"] == "2026-11-06T07:10:00Z"
    assert data["previous_day_candle_utc"] == "2026-11-05T00:00:00Z"
    for lv in data["levels"]:
        assert set(lv) == {"price", "type", "source", "candle_utc", "important", "group"}
        assert re.fullmatch(r"\d+(\.\d+)?", lv["price"]) and lv["source"] and lv["group"] >= 1
    group_ids = {g["group"] for g in data["groups"]}
    assert {lv["group"] for lv in data["levels"]} == group_ids
    g = next(g for g in data["groups"] if "round_number 13450" in g["levels"])
    assert "previous_day_low 13446.8" in g["levels"] and g["lined_up"] and g["important"]


def test_the_list_is_written_with_a_safe_write(tmp_path, monkeypatch):
    import levels.current as cur
    seen = []
    monkeypatch.setattr(cur, "safe_write", lambda p, data: seen.append((p, json.loads(data))))
    s = settings(tmp_path)
    write_current(s.levels.folder, build(s, _full_store(tmp_path), T(2026, 11, 6, 7, 10)), T(2026, 11, 6, 7, 10))
    assert seen and seen[0][0].name == "current.json"


def test_the_list_is_updated_each_time_a_5_minute_candle_is_stored(tmp_path):
    s = settings(tmp_path)
    store = _full_store(tmp_path)
    clock = [T(2026, 11, 6, 7, 15)]
    updater = LevelsUpdater(s, store)
    feed = PriceFeed(SETTINGS, store, now=lambda: clock[0], after_new_candle=updater)
    feed.add_five_minute(candle("5m", T(2026, 11, 6, 7, 10), 5, 13499, 13440))
    assert updater.updates == 1
    data = read_current(s.levels.folder)
    assert data["as_of_utc"] == "2026-11-06T07:15:00Z"
    assert any(lv["type"] == "london_session_high" and lv["price"] == "13499" for lv in data["levels"])
    feed.add_five_minute(candle("5m", T(2026, 11, 6, 7, 10), 5, 13499, 13440))     # same candle again
    assert updater.updates == 1                                                    # nothing new stored


def test_a_levels_problem_never_stops_the_price_service(tmp_path, caplog):
    s = settings(tmp_path)
    store = _full_store(tmp_path)
    write_current(s.levels.folder, build(s, store, T(2026, 11, 6, 7, 10)), T(2026, 11, 6, 7, 10))
    before = (s.levels.folder / "current.json").read_text()
    broken = SimpleNamespace(**{**vars(s), "levels": SimpleNamespace(**{**vars(s.levels), "line_up_within_pips": None})})
    warnings = []
    updater = LevelsUpdater(broken, store, warn=warnings.append)
    updater(T(2026, 11, 6, 7, 15))                       # does not raise
    assert warnings and "Levels not updated" in warnings[0]
    assert (s.levels.folder / "current.json").read_text() == before       # old list kept


def test_a_levels_warning_is_written_once_not_every_5_minutes(tmp_path):
    s = settings(tmp_path)
    store = CandleStore(tmp_path / "candles" / "GBPUSD", 30)
    _day_of_5m(store, T(2026, 11, 6), {(7, 0): (13460, 13448)})       # no daily candle stored
    warnings = []
    updater = LevelsUpdater(s, store, warn=warnings.append)
    updater(T(2026, 11, 6, 7, 5))
    updater(T(2026, 11, 6, 7, 10))
    assert sum("not stored yet" in w for w in warnings) == 1


def test_only_candles_finished_by_then_are_used(tmp_path):
    store = _full_store(tmp_path)
    ll = build(settings(tmp_path), store, T(2026, 11, 6, 7, 7))       # 07:05 candle not finished
    assert ll.of_type("london_session_high")[0].price == 13460
    ll = build(settings(tmp_path), store, T(2026, 11, 5, 12))         # Thursday: its own candle not finished
    assert ll.previous_day is None or ll.previous_day.start < T(2026, 11, 5)


def test_the_levels_part_never_contacts_ig():
    for f in (ROOT / "levels").glob("*.py"):
        src = f.read_text()
        assert not re.search(r"^\s*(from|import)\s+ig\b", src, re.M), f.name
        assert "requests" not in src and "lightstreamer" not in src, f.name


def test_the_live_run_and_the_service_update_the_levels():
    assert "after_new_candle=LevelsUpdater(settings, store)" in (ROOT / "prices/run.py").read_text()
    assert "after_new_candle=_after_candle(LevelsUpdater(ps, store), StatesUpdater(ps, store))" in \
        (ROOT / "prices/service.py").read_text()   # each pair's own levels, then its market states
