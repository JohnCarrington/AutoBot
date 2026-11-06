"""Candle boundaries, building bigger candles from stored 5-minute candles,
the store checks, and restarts."""

from datetime import timedelta

import pytest

from prices.builder import build_due
from prices.calendar import Boundaries, MarketHours
from prices.checks import check_store
from prices.feed import PriceFeed
from prices.model import uk
from prices.store import CandleStore
from tests.technical.fake_stream import SETTINGS, Clock, T, five

HOURS = MarketHours(SETTINGS.market_hours)
B = Boundaries(SETTINGS.candles, HOURS)
FIVE = timedelta(minutes=5)


def fill(store, start, end):
    t = start
    while t < end:
        if HOURS.is_open(t):
            store.add(five(t))
        t += FIVE


@pytest.fixture
def warnings():
    return []


@pytest.fixture
def store(tmp_path, warnings):
    return CandleStore(tmp_path / "candles", 30, warn=warnings.append)


# ---- market hours ---------------------------------------------------------------

def test_market_hours_in_the_settings_file():
    mh = SETTINGS.market_hours
    assert (str(mh.opens_day), mh.opens_at.strftime("%H:%M"), str(mh.opens_time_zone)) == \
        ("Sunday", "21:00", "Europe/London")
    assert (str(mh.closes_day), mh.closes_at.strftime("%H:%M"), str(mh.closes_time_zone)) == \
        ("Friday", "17:00", "America/New_York")


# What IG's own 5-minute candles showed (the one-off fill, 25 Oct - 6 Nov 2026):
# first and last candle of each trading week. The rule must agree with every one.
IG_EVIDENCE = [
    ("Sun 25 Oct: last minute before IG's first candle", T(2026, 10, 25, 20, 55), False),
    ("Sun 25 Oct: IG's first candle, 21:00 GMT = 17:00 New York", T(2026, 10, 25, 21, 0), True),
    ("Fri 30 Oct: IG's last candle, 20:55 GMT", T(2026, 10, 30, 20, 55), True),
    ("Fri 30 Oct: no IG candle at 21:00 GMT = 17:00 New York", T(2026, 10, 30, 21, 0), False),
    ("Fri 30 Oct: no IG candle at 21:55 GMT", T(2026, 10, 30, 21, 55), False),
    ("Sun 1 Nov: before IG's first candle", T(2026, 11, 1, 20, 55), False),
    ("Sun 1 Nov: IG's first candle, 21:00 GMT = 16:00 New York", T(2026, 11, 1, 21, 0), True),
    ("Every weeknight 21:00-22:55 UK: IG candles present", T(2026, 10, 27, 22, 0), True),
]


@pytest.mark.parametrize("what, t, is_open", IG_EVIDENCE, ids=[e[0] for e in IG_EVIDENCE])
def test_market_hours_agree_with_what_igs_candles_showed(what, t, is_open):
    assert HOURS.is_open(t) is is_open, what


@pytest.mark.parametrize("what, t, is_open", [
    # IG's page (summer): "21.00 (London time) on Sunday until 21.59 (London time) on Friday"
    ("summer Sunday 21:00 BST opens", T(2026, 7, 12, 20, 0), True),
    ("summer Sunday 20:55 BST still closed", T(2026, 7, 12, 19, 55), False),
    ("summer Friday 21:55 BST last candle", T(2026, 7, 10, 20, 55), True),
    ("summer Friday 22:00 BST = 17:00 New York closed", T(2026, 7, 10, 21, 0), False),
    # Winter, both on standard time: close 22:00 GMT = 17:00 New York (expected tonight, 6 Nov)
    ("winter Friday 21:55 GMT last candle", T(2026, 11, 6, 21, 55), True),
    ("winter Friday 22:00 GMT closed", T(2026, 11, 6, 22, 0), False),
    # March 2027: US summer time from 14 Mar, UK from 28 Mar -> close 21:00 GMT, open 21:00 GMT
    ("March gap week Friday 21:00 GMT = 17:00 New York closed", T(2027, 3, 19, 21, 0), False),
    ("March gap week Friday 20:55 GMT open", T(2027, 3, 19, 20, 55), True),
    ("March gap week Sunday 21:00 GMT opens", T(2027, 3, 21, 21, 0), True),
])
def test_market_hours_through_the_year(what, t, is_open):
    assert HOURS.is_open(t) is is_open, what


def test_the_weekend_after_fri_30_oct_is_not_a_gap_but_a_missing_hour_before_it_would_be(store):
    fill(store, T(2026, 10, 30, 19), T(2026, 10, 30, 21))     # IG's last candle 20:55 GMT
    fill(store, T(2026, 11, 1, 21), T(2026, 11, 1, 22))
    assert check_store(store, B).gaps == []
    weekly = B.bucket("1w", T(2026, 10, 28, 12))
    assert weekly == (T(2026, 10, 25, 21), T(2026, 10, 30, 21))
    assert B.expected_parts(*weekly) == 1440                   # exactly what IG sent that week


@pytest.mark.parametrize("t, is_open", [
    (T(2026, 11, 6, 21, 55), True),    # Friday, last candle
    (T(2026, 11, 6, 22, 0), False),    # Friday close (GMT: UK time = UTC)
    (T(2026, 11, 7, 12, 0), False),    # Saturday
    (T(2026, 11, 8, 20, 55), False),   # Sunday before the open
    (T(2026, 11, 8, 21, 0), True),     # Sunday open
    (T(2026, 7, 10, 20, 55), True),    # summer Friday 21:55 BST (= 16:55 New York)
    (T(2026, 7, 10, 21, 0), False),    # summer Friday 22:00 BST
    (T(2026, 7, 12, 20, 0), True),     # summer Sunday 21:00 BST
])
def test_market_hours_are_uk_time_in_summer_and_winter(t, is_open):
    assert HOURS.is_open(t) is is_open


# ---- boundaries -------------------------------------------------------------------

def test_candle_boundaries_match_igs_midnight_uk_days():
    wed = T(2026, 11, 4, 10, 37)
    assert B.bucket("1h", wed) == (T(2026, 11, 4, 10), T(2026, 11, 4, 11))
    assert B.bucket("4h", wed) == (T(2026, 11, 4, 8), T(2026, 11, 4, 12))
    assert B.bucket("1d", wed) == (T(2026, 11, 4, 0), T(2026, 11, 5, 0))
    assert B.bucket("1w", wed) == (T(2026, 11, 1, 21), T(2026, 11, 6, 22))


def test_sundays_opening_is_its_own_short_candle_like_igs():
    sun = T(2026, 11, 8, 21, 30)
    assert B.bucket("1h", sun) == (T(2026, 11, 8, 21), T(2026, 11, 8, 22))
    assert B.bucket("4h", sun) == (T(2026, 11, 8, 21), T(2026, 11, 9, 0))
    assert B.bucket("1d", sun) == (T(2026, 11, 8, 21), T(2026, 11, 9, 0))      # IG's Sunday daily candle
    assert B.bucket("1d", T(2026, 11, 9, 15)) == (T(2026, 11, 9, 0), T(2026, 11, 10, 0))
    assert B.bucket("1w", sun) == (T(2026, 11, 8, 21), T(2026, 11, 13, 22))
    assert B.expected_parts(T(2026, 11, 8, 21), T(2026, 11, 9, 0)) == 36


def test_fridays_daily_candle_ends_at_the_close():
    assert B.bucket("1d", T(2026, 11, 6, 12)) == (T(2026, 11, 6, 0), T(2026, 11, 6, 22))
    assert B.bucket("1d", T(2026, 10, 30, 12)) == (T(2026, 10, 30, 0), T(2026, 10, 30, 21))   # 17:00 New York


def test_boundaries_follow_uk_time_in_summer():
    wed = T(2026, 7, 8, 10, 0)   # 11:00 BST
    assert B.bucket("1d", wed) == (T(2026, 7, 7, 23), T(2026, 7, 8, 23))   # midnight BST to midnight BST
    assert B.bucket("4h", wed) == (T(2026, 7, 8, 7), T(2026, 7, 8, 11))    # 08:00 to 12:00 BST


def test_boundaries_are_settings():
    c = SETTINGS.candles
    assert c.hour_starts_at_minute == 0
    assert c.four_hour_starts_at.strftime("%H:%M") == "00:00"
    assert c.day_starts_at.strftime("%H:%M") == "00:00"
    assert str(c.week_starts_day) == "Sunday"
    assert c.join_opening_stretch is False


def test_the_other_layout_still_works_when_set_22_00_days_with_sunday_joined_to_monday():
    from types import SimpleNamespace
    from datetime import time
    c = SimpleNamespace(hour_starts_at_minute=0, four_hour_starts_at=time(22), day_starts_at=time(22),
                        week_starts_day=SETTINGS.candles.week_starts_day, join_opening_stretch=True)
    b = Boundaries(c, HOURS)
    sun = T(2026, 11, 8, 21, 30)
    assert b.bucket("4h", sun) == (T(2026, 11, 8, 21), T(2026, 11, 9, 2))
    assert b.bucket("1d", sun) == (T(2026, 11, 8, 21), T(2026, 11, 9, 22))
    assert b.bucket("1d", T(2026, 11, 9, 15)) == (T(2026, 11, 8, 21), T(2026, 11, 9, 22))
    assert b.bucket("1w", sun) == (T(2026, 11, 8, 21), T(2026, 11, 13, 22))


# ---- building bigger candles --------------------------------------------------------

def test_one_hour_candle_built_from_stored_5_minute_candles_buy_and_sell_separately(store, warnings):
    t = T(2026, 11, 4, 10)
    prices = [("1.30010", "1.30020"), ("1.30110", "1.30120"), ("1.29910", "1.29920")]
    for i in range(12):
        hi = "1.31500" if i == 3 else "1.31060"
        lo = "1.30500" if i == 7 else "1.30960"
        store.add(five(t + i * FIVE, bo=f"1.310{i:02d}", bc=f"1.311{i:02d}", so=f"1.300{i:02d}",
                       sc=f"1.301{i:02d}", bh=hi, sh="1.31050", bl="1.30960", sl=lo))
    built = build_due(store, B, T(2026, 11, 4, 11, 0, 5), 300, warnings.append)
    h = [c for c in built if c.timeframe == "1h"][0]
    assert (str(h.buy_open), str(h.buy_high), str(h.buy_low), str(h.buy_close)) == \
        ("1.31000", "1.31500", "1.30960", "1.31111")
    assert (str(h.sell_open), str(h.sell_high), str(h.sell_low), str(h.sell_close)) == \
        ("1.30000", "1.31050", "1.30500", "1.30111")
    assert (h.parts, h.expected_parts) == (12, 12)
    assert warnings == []


def test_bigger_candles_wait_until_their_time_is_over(store, warnings):
    fill(store, T(2026, 11, 4, 10), T(2026, 11, 4, 10, 30))
    assert build_due(store, B, T(2026, 11, 4, 10, 31), 300, warnings.append) == []


def test_a_bigger_candle_missing_a_5_minute_candle_waits_then_is_built_and_marked(store, warnings):
    fill(store, T(2026, 11, 4, 10), T(2026, 11, 4, 10, 55))   # 10:55 missing
    assert build_due(store, B, T(2026, 11, 4, 11, 0, 30), 300, warnings.append) == []
    built = build_due(store, B, T(2026, 11, 4, 11, 5), 300, warnings.append)
    h = [c for c in built if c.timeframe == "1h"][0]
    assert (h.parts, h.expected_parts) == (11, 12)
    assert any("only 11 of 12" in w for w in warnings)


def test_daily_and_weekly_candles_cover_the_whole_trading_week(store, warnings):
    fill(store, T(2026, 11, 1, 21), T(2026, 11, 6, 22))
    built = build_due(store, B, T(2026, 11, 6, 22, 0, 10), 300, warnings.append)
    days = [c for c in built if c.timeframe == "1d"]
    weeks = [c for c in built if c.timeframe == "1w"]
    assert [(c.start, c.end, c.parts) for c in days] == [
        (T(2026, 11, 1, 21), T(2026, 11, 2), 36),            # IG's short Sunday candle
        (T(2026, 11, 2), T(2026, 11, 3), 288), (T(2026, 11, 3), T(2026, 11, 4), 288),
        (T(2026, 11, 4), T(2026, 11, 5), 288), (T(2026, 11, 5), T(2026, 11, 6), 288),
        (T(2026, 11, 6), T(2026, 11, 6, 22), 264)]           # Friday, to the close
    assert all(c.parts == c.expected_parts for c in days)
    assert [(c.start, c.end, c.parts) for c in weeks] == [(T(2026, 11, 1, 21), T(2026, 11, 6, 22), 1452)]
    assert len([c for c in built if c.timeframe == "4h"]) == 1 + 24 + 6
    assert warnings == []
    assert check_store(store, B).problems == []


def test_new_candles_are_never_built_over_ones_already_stored(store, warnings):
    """Candles built before a boundary change are kept; nothing new overlaps them."""
    fill(store, T(2026, 11, 2, 0), T(2026, 11, 3, 12))
    old = five(T(2026, 11, 1, 22), tf="1d", minutes=24 * 60)   # an old-style 22:00 to 22:00 daily candle
    store.add(old)
    built = build_due(store, B, T(2026, 11, 3, 12), 300, warnings.append)
    assert [c.start for c in built if c.timeframe == "1d"] == []   # 2 Nov 00:00 would overlap: not built
    assert store.get("1d", T(2026, 11, 2)) is None and store.get("1d", T(2026, 11, 1, 22)) == old


# ---- the store checks ----------------------------------------------------------------

def test_clean_store_passes_every_check(store):
    fill(store, T(2026, 11, 4, 10), T(2026, 11, 4, 12))
    r = check_store(store, B)
    assert r.problems == [] and r.gaps == [] and r.candles["5m"] == 24


def test_gap_during_market_hours_is_found(store):
    fill(store, T(2026, 11, 4, 10), T(2026, 11, 4, 10, 30))
    fill(store, T(2026, 11, 4, 11), T(2026, 11, 4, 11, 30))
    r = check_store(store, B)
    assert [(g.timeframe, g.start, g.end, g.missing) for g in r.gaps] == \
        [("5m", T(2026, 11, 4, 10, 30), T(2026, 11, 4, 11), 6)]


def test_the_weekend_close_and_reopen_is_not_a_gap(store):
    fill(store, T(2026, 11, 6, 21), T(2026, 11, 6, 22))      # Friday up to the close
    fill(store, T(2026, 11, 8, 21), T(2026, 11, 8, 22))      # Sunday from the open
    r = check_store(store, B)
    assert r.gaps == [] and r.problems == []


def test_a_gap_just_after_the_sunday_open_is_still_a_gap(store):
    fill(store, T(2026, 11, 6, 21), T(2026, 11, 6, 22))
    fill(store, T(2026, 11, 8, 21, 10), T(2026, 11, 8, 22))
    r = check_store(store, B)
    assert [(g.start, g.missing) for g in r.gaps] == [(T(2026, 11, 8, 21), 2)]


def _write_rows(store, tf, day, rows):
    from prices.store import _to_csv, safe_write
    safe_write(store._plain(tf, day), _to_csv(rows))


def test_duplicate_candle_is_found(store):
    c = five(T(2026, 11, 4, 10))
    _write_rows(store, "5m", c.start.date(), [c, c])
    assert any("DUPLICATE" in p for p in check_store(store, B).problems)


def test_buy_price_below_sell_price_is_found(store):
    _write_rows(store, "5m", T(2026, 11, 4).date(), [five(T(2026, 11, 4, 10), bc="1.30000", sc="1.30010")])
    assert any("BUY BELOW SELL" in p and "close" in p for p in check_store(store, B).problems)


def test_high_below_low_is_found(store):
    _write_rows(store, "5m", T(2026, 11, 4).date(), [five(T(2026, 11, 4, 10), sh="1.30000", sl="1.30100")])
    assert any("HIGH BELOW LOW" in p and "sell" in p for p in check_store(store, B).problems)


def test_out_of_time_order_is_found(store):
    a, b = five(T(2026, 11, 4, 10, 5)), five(T(2026, 11, 4, 10, 0))
    _write_rows(store, "5m", T(2026, 11, 4).date(), [a, b])
    assert any("OUT OF TIME ORDER" in p for p in check_store(store, B).problems)


def test_candle_in_the_wrong_days_file_is_found(store):
    _write_rows(store, "5m", T(2026, 11, 3).date(), [five(T(2026, 11, 4, 10))])
    assert any("is in the file for 2026-11-03" in p for p in check_store(store, B).problems)


def test_candle_not_on_its_boundary_is_found(store):
    _write_rows(store, "5m", T(2026, 11, 4).date(), [five(T(2026, 11, 4, 10, 2))])
    assert any("does not start on a 5m boundary" in p for p in check_store(store, B).problems)


def test_damaged_file_is_found(store):
    p = store._plain("5m", T(2026, 11, 4).date())
    p.parent.mkdir(parents=True)
    p.write_text("nonsense")
    assert any("DAMAGED FILE" in x for x in check_store(store, B).problems)


def test_checks_run_after_every_new_candle_and_warn(tmp_path):
    clock = Clock(T(2026, 11, 4, 10, 10))
    store = CandleStore(tmp_path / "c", 30)
    feed = PriceFeed(SETTINGS, store, now=clock)
    feed.add_five_minute(five(T(2026, 11, 4, 10)))
    feed.add_five_minute(five(T(2026, 11, 4, 10, 15)))           # 10:05 and 10:10 missing
    assert any("GAP in 5m" in w and "2 candle(s)" in w for w in feed.warnings)
    feed.add_five_minute(five(T(2026, 11, 4, 10, 20), bc="1.20000"))   # buy close below sell close
    assert any("BUY BELOW SELL" in w for w in feed.warnings)
    assert len(store.recorded_gaps()) == 1


def test_disk_space_is_checked_after_every_new_candle(tmp_path):
    calls = []
    feed = PriceFeed(SETTINGS, CandleStore(tmp_path / "c", 30), now=Clock(T(2026, 11, 4, 10, 10)),
                     disk_check=lambda: calls.append(1))
    feed.add_five_minute(five(T(2026, 11, 4, 10)))
    feed.add_five_minute(five(T(2026, 11, 4, 10, 5)))
    assert len(calls) == 2


# ---- restarts ---------------------------------------------------------------------

def _restart(tmp_path, now):
    feed = PriceFeed(SETTINGS, CandleStore(tmp_path / "candles", 30), now=Clock(now))
    return feed, feed.start_up()


def test_restart_after_5_minutes(store, tmp_path):
    fill(store, T(2026, 11, 4, 9), T(2026, 11, 4, 10))      # newest ends 10:00
    feed, r = _restart(tmp_path, T(2026, 11, 4, 10, 5, 30))  # 10:00-10:05 finished while stopped
    assert r.newest.start == T(2026, 11, 4, 9, 55)
    assert r.age == timedelta(minutes=5, seconds=30)
    assert any("finished 5 minute(s) ago" in l for l in r.lines)
    assert [(g.start, g.missing) for g in r.gaps_since] == [(T(2026, 11, 4, 10), 1)]
    assert len(store.recorded_gaps()) == 1
    assert store.newest("5m").start == T(2026, 11, 4, 9, 55)  # not filled


def test_restart_within_the_same_5_minutes_is_not_a_gap(store, tmp_path):
    fill(store, T(2026, 11, 4, 9), T(2026, 11, 4, 10))
    feed, r = _restart(tmp_path, T(2026, 11, 4, 10, 3))
    assert r.gaps_since == [] and store.recorded_gaps() == []


def test_restart_after_2_hours(store, tmp_path):
    fill(store, T(2026, 11, 4, 9), T(2026, 11, 4, 10))
    feed, r = _restart(tmp_path, T(2026, 11, 4, 12, 0, 20))
    assert r.age == timedelta(hours=2, seconds=20)
    assert any("2 hour(s) 0 minute(s)" in l for l in r.lines)
    assert [(g.start, g.end, g.missing) for g in r.gaps_since] == [(T(2026, 11, 4, 10), T(2026, 11, 4, 12), 24)]
    rows = store.recorded_gaps()
    assert rows[0]["missing_candles"] == "24" and "start-up" in rows[0]["how_found"]
    assert store.newest("5m").start == T(2026, 11, 4, 9, 55)   # not filled
    # It carries on: the 09:00 hour candle is built from what is stored.
    assert store.get("1h", T(2026, 11, 4, 9)) is not None
    # When IG's candles arrive again, the known gap is not warned about twice.
    feed.add_five_minute(five(T(2026, 11, 4, 12)))
    assert sum("GAP" in w for w in feed.warnings) == 1


def test_restart_on_monday_morning_the_weekend_is_not_a_gap(store, tmp_path):
    fill(store, T(2026, 11, 6, 20), T(2026, 11, 6, 22))         # up to Friday's close
    feed, r = _restart(tmp_path, T(2026, 11, 9, 7, 0, 10))      # Monday 07:00 UK
    assert r.newest.end == T(2026, 11, 6, 22)
    # Only Sunday 21:00 to Monday 07:00 is missing; Friday 22:00 to Sunday 21:00 is the weekend.
    assert [(g.start, g.end, g.missing) for g in r.gaps_since] == [(T(2026, 11, 8, 21), T(2026, 11, 9, 7), 120)]


def test_restart_on_sunday_before_the_open_has_no_gap(store, tmp_path):
    fill(store, T(2026, 11, 6, 20), T(2026, 11, 6, 22))
    feed, r = _restart(tmp_path, T(2026, 11, 8, 20, 30))
    assert r.gaps_since == []


def test_restart_reports_an_empty_store(tmp_path):
    feed, r = _restart(tmp_path, T(2026, 11, 4, 10))
    assert r.newest is None and any("store is empty" in l for l in r.lines)


def test_start_up_removes_leftover_temp_files_and_checks_the_store(store, tmp_path):
    fill(store, T(2026, 11, 4, 9), T(2026, 11, 4, 10))
    (tmp_path / "candles" / "5m" / "2026-11-04.csv.tmp-999").write_text("half a fi")
    feed, r = _restart(tmp_path, T(2026, 11, 4, 10, 1))
    assert not list((tmp_path / "candles").rglob("*.tmp-*"))
    assert r.check.candles["5m"] == 12 and r.check.problems == []


def test_times_shown_to_a_person_are_uk_time():
    assert uk(T(2026, 7, 6, 9, 0)) == "Mon 06 Jul 2026 10:00:00 BST"
    assert uk(T(2026, 11, 6, 9, 0)) == "Fri 06 Nov 2026 09:00:00 GMT"
