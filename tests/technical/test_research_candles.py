"""Research candles (research/): built like the bot's own, never into a live folder."""

import csv
from datetime import date, datetime, timedelta
from decimal import Decimal as D

import pytest

from prices.calendar import Boundaries, MarketHours
from prices.model import UTC
from prices.store import COLUMNS, GAP_COLUMNS, CandleStore, DamagedFile
from research import candles_convert as cc
from research import dukascopy_check as chk
from tests.technical.fake_stream import SETTINGS

B = Boundaries(SETTINGS.candles, MarketHours(SETTINGS.market_hours))
FIVE = timedelta(minutes=5)


def T(s):
    return datetime.fromisoformat(s).replace(tzinfo=UTC)


@pytest.fixture
def out(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOBOT_RESEARCH_TEST_ROOT", str(tmp_path))
    return tmp_path / "candles" / "GBPUSD"


def sell(t, o="13000.0", h=None, l=None, c=None):
    o = D(o)
    return cc.RCandle(t, t + FIVE, None, (o, D(h) if h else o + 1, D(l) if l else o - 1, D(c) if c else o))


def both(t, bid="13000.0", spread="0.9"):
    s = sell(t, bid).sell
    return cc.RCandle(t, t + FIVE, tuple(p + D(spread) for p in s), s)


def week(start, end, make=sell):
    return [make(t) for t in B.hours.open_slots(start, end)]


# ---- prices written IG's way -------------------------------------------------------

def test_prices_in_ig_points():
    assert cc.points_from_fx(D("1.33797")) == D("13379.7")
    assert cc.written(cc.points_from_fx(D("1.34"))) == "13400.0"
    assert cc.points_from_text("12787.30") == D("12787.3")
    with pytest.raises(ValueError):
        cc.points_from_fx(D("1.337975"))
    with pytest.raises(ValueError):
        cc.points_from_text("12787.35")


# ---- reading 161's files -------------------------------------------------------------

def test_read_161_file(tmp_path):
    p = tmp_path / "2024-08-05.csv"
    p.write_text("timestamp,open,high,low,close\n2024-08-05T00:00:00+00:00,12787.30,12787.60,12785.00,12785.00\n")
    [c] = cc.read_161_file(p)
    assert c.start == T("2024-08-05T00:00") and c.buy is None
    assert c.sell == (D("12787.3"), D("12787.6"), D("12785.0"), D("12785.0"))
    p.write_text("timestamp,open,high,low,close\n2024-08-05T01:00:00+01:00,1,2,1,1\n")
    with pytest.raises(ValueError, match="not UTC"):
        cc.read_161_file(p)
    p.write_text("timestamp,open,high,low,close\n2024-08-05T00:00:00+00:00,12787.30,12787.00,12785.00,12785.00\n")
    with pytest.raises(ValueError, match="high/low"):
        cc.read_161_file(p)


def test_161_out_of_step_weeks_move_one_hour_later():
    odd = sell(T("2025-03-10T12:00"))      # US on summer time since 9 March, UK not until 30 March
    odd2 = sell(T("2025-10-27T12:00"))     # UK back on GMT since 26 October, US not until 2 November
    normal = sell(T("2025-03-03T12:00"))
    summer = sell(T("2025-07-07T12:00"))
    fixed, moved = cc.fix_161_out_of_step_weeks([odd, odd2, normal, summer])
    assert moved == 2
    assert [c.start for c in fixed] == [T("2025-03-03T12:00"), T("2025-03-10T13:00"),
                                        T("2025-07-07T12:00"), T("2025-10-27T13:00")]
    # 161's Sunday open in such a week (20:00 UK) lands on IG's 21:00 UK open.
    sun = sell(T("2025-03-09T20:00"))
    assert not B.hours.is_open(sun.start)
    assert B.hours.is_open(cc.fix_161_out_of_step_weeks([sun])[0][0].start)


# ---- built like the bot ------------------------------------------------------------

def test_days_are_uk_midnight_with_igs_short_sunday(out):
    # GMT week: Sunday 2 Nov 2025 21:00 to Friday 7 Nov 22:00
    fives = week(T("2025-11-02T21:00"), T("2025-11-07T22:00"))
    r = cc.convert(fives, B, out, "test")
    days = {c.start: c for c in cc.read_store(out, "1d")}
    sun = days[T("2025-11-02T00:00")]
    assert (sun.parts, sun.expected_parts) == (36, 36)
    assert days[T("2025-11-03T00:00")].expected_parts == 288
    fri = days[T("2025-11-07T00:00")]
    assert fri.end == T("2025-11-07T22:00") and fri.expected_parts == 264
    assert r["gaps"] == [] and r["dropped_outside_hours"] == []


def test_summer_day_is_in_the_previous_utc_date_file(out):
    fives = week(T("2025-07-06T20:00"), T("2025-07-08T00:00"))
    cc.convert(fives, B, out, "test")
    sun = list(csv.reader((out / "1d" / "2025-07-05.csv").open()))
    mon = list(csv.reader((out / "1d" / "2025-07-06.csv").open()))
    assert tuple(sun[0]) == COLUMNS
    assert [r[0] for r in sun[1:]] == ["2025-07-05T23:00:00Z"]     # Sunday 00:00 BST
    assert sun[1][-2:] == ["36", "36"]                               # holding 21:00 to midnight
    assert [r[0] for r in mon[1:]] == ["2025-07-06T23:00:00Z"]     # Monday 00:00 BST


def test_sell_only_files_leave_buy_empty_and_the_live_store_cannot_read_them(out):
    cc.convert(week(T("2025-11-03T00:00"), T("2025-11-03T01:00")), B, out, "test")
    row = list(csv.reader((out / "5m" / "2025-11-03.csv").open()))[1]
    assert row[2:6] == ["", "", "", ""] and row[6] == "13000.0" and row[10:] == ["1", "1"]
    with pytest.raises(DamagedFile):
        CandleStore(out, 30).read_day("5m", date(2025, 11, 3))


def test_bigger_candles_keep_buy_and_sell_apart(out):
    fives = [both(T("2025-11-03T10:00"), "13000.0", "0.9"), both(T("2025-11-03T10:05"), "13010.0", "1.5")]
    cc.convert(fives, B, out, "test")
    [h] = CandleStore(out, 30).read_day("1h", date(2025, 11, 3))   # full files read in the live store
    assert (h.sell_open, h.sell_high, h.sell_low, h.sell_close) == (D("13000.0"), D("13011.0"), D("12999.0"), D("13010.0"))
    assert (h.buy_open, h.buy_high, h.buy_low, h.buy_close) == (D("13000.9"), D("13012.5"), D("12999.9"), D("13011.5"))
    assert (h.parts, h.expected_parts) == (2, 12)


# ---- gaps ----------------------------------------------------------------------------

def test_every_gap_is_recorded_and_the_weekend_is_not_one(out):
    fives = week(T("2025-10-31T20:00"), T("2025-11-03T01:00"))       # Friday evening to Monday
    fives = [c for c in fives if c.start not in (T("2025-11-02T21:00"), T("2025-11-03T00:30"),
                                                 T("2025-11-03T00:35"))]
    r = cc.convert(fives, B, out, "test")
    five = [(s, e, n) for tf, s, e, n in r["gaps"] if tf == "5m"]
    assert five == [(T("2025-11-02T21:00"), T("2025-11-02T21:05"), 1),
                    (T("2025-11-03T00:30"), T("2025-11-03T00:40"), 2)]
    rows = list(csv.DictReader((out / "gaps.csv").open()))
    assert tuple(rows[0].keys()) == GAP_COLUMNS
    assert rows[0]["note"] == "at the week's open" and rows[0]["how_found"] == "test"


def test_a_missing_hour_is_a_1h_gap(out):
    fives = [c for c in week(T("2025-11-03T00:00"), T("2025-11-03T03:00")) if c.start.hour != 1]
    r = cc.convert(fives, B, out, "test")
    assert ("1h", T("2025-11-03T01:00"), T("2025-11-03T02:00"), 1) in r["gaps"]


def test_candles_outside_market_hours_are_not_kept(out):
    r = cc.convert([sell(T("2025-11-01T12:00")), sell(T("2025-11-03T12:00"))], B, out, "test")
    assert [c.start for c in r["dropped_outside_hours"]] == [T("2025-11-01T12:00")]


# ---- never a live folder ---------------------------------------------------------------

def test_refuses_the_live_store_and_anywhere_outside_research(tmp_path, monkeypatch):
    monkeypatch.delenv("AUTOBOT_RESEARCH_TEST_ROOT", raising=False)
    fives = [sell(T("2025-11-03T12:00"))]
    for where in ("/opt/autobot/data/candles/GBPUSD", "/opt/autobot/data/candles", "/opt/autobot/data/orders",
                  str(tmp_path / "x")):
        with pytest.raises(PermissionError):
            cc.convert(fives, B, where, "test")
    monkeypatch.setenv("AUTOBOT_RESEARCH_TEST_ROOT", "/opt/autobot/data")
    with pytest.raises(PermissionError, match="live candle store"):
        cc.convert(fives, B, "/opt/autobot/data/candles/GBPUSD", "test")


# ---- Dukascopy's 1-minute export files (exported by hand) ---------------------------------

HEAD = "Gmt time,Open,High,Low,Close,Volume\n"


def test_dukascopy_export_to_five_minute_buy_and_sell(tmp_path, out):
    src = tmp_path / "duka"
    src.mkdir()
    (src / "GBPUSD_Candlestick_1_M_BID_01.11.2025-03.11.2025.csv").write_text(
        HEAD + "03.11.2025 10:00:00.000,1.30000,1.30020,1.29990,1.30010,1.5\n"
               "03.11.2025 10:01:00.000,1.30010,1.30040,1.30000,1.30030,2.0\n"
               "03.11.2025 10:02:00.000,1.30030,1.30030,1.30030,1.30030,0\n")   # no ticks: not used
    (src / "GBPUSD_Candlestick_1_M_ASK_01.11.2025-03.11.2025.csv").write_text(
        HEAD + "03.11.2025 10:00:00.000,1.30009,1.30029,1.29999,1.30019,1.5\n"
               "03.11.2025 10:01:00.000,1.30019,1.30049,1.30009,1.30039,2.0\n"
               "03.11.2025 10:02:00.000,1.30039,1.30039,1.30039,1.30039,0\n")
    [c], info = cc.duka_five_minutes(src)
    assert info["minutes_on_one_side_only"] == 0 and info["bid_minutes"] == 3
    assert c.start == T("2025-11-03T10:00")
    assert c.sell == (D("13000.0"), D("13004.0"), D("12999.0"), D("13003.0"))
    assert c.buy == (D("13000.9"), D("13004.9"), D("12999.9"), D("13003.9"))
    cc.convert([c], B, out, "test")
    [s] = CandleStore(out, 30).read_day("5m", date(2025, 11, 3))     # the live store's own reader
    assert s.buy_close - s.sell_close == D("0.9")


def test_dukascopy_times_must_be_gmt():
    assert cc._duka_time("03.11.2025 10:00:00.000", True) == T("2025-11-03T10:00")
    assert cc._duka_time("03.11.2025 10:00:00.000 GMT+0100", False) == T("2025-11-03T09:00")
    assert cc._duka_time("2025-11-03T10:00:00Z", False) == T("2025-11-03T10:00")
    with pytest.raises(ValueError, match="no time zone"):
        cc._duka_time("03.11.2025 10:00:00.000", False)        # a 'Local time' column


def test_dukascopy_files_refused_when_unclear(tmp_path):
    p = tmp_path / "GBPUSD_1_M.csv"
    p.write_text(HEAD)
    with pytest.raises(ValueError, match="BID or ASK"):
        cc.duka_side_of(p)
    p = tmp_path / "GBPUSD_BID.csv"
    p.write_text(HEAD + "03.11.2025 10:00:00.000,1.30000,1.29990,1.29990,1.30010,1\n")
    with pytest.raises(ValueError, match="high/low"):
        cc.read_duka_csv(p)
    p.write_text(HEAD + "03.11.2025 10:00:00.000,1.300005,1.30020,1.29990,1.30010,1\n")
    with pytest.raises(ValueError, match="finer"):
        cc.read_duka_csv(p)
    p.write_text("Local time,Open,High,Low,Close,Volume\n03.11.2025 10:00:00.000,1.3,1.3,1.3,1.3,1\n")
    with pytest.raises(ValueError, match="no time zone"):
        cc.read_duka_csv(p)


# ---- the comparisons ----------------------------------------------------------------------

def test_sell_diffs_by_year():
    a = [sell(T("2024-12-02T00:00"), "13000.5"), sell(T("2025-01-06T00:00"), "13000.0")]
    b = [sell(T("2024-12-02T00:00"), "13000.0"), sell(T("2025-01-06T00:00"), "13000.0"),
         sell(T("2025-01-07T00:00"), "13000.0")]
    r = chk.sell_diffs(a, b)
    assert r["2024"]["open"]["median"] == D("0.5") and r["2024"]["open"]["mean_signed"] == D("0.50")
    assert r["2025"]["close"]["exact"] == 1 and r["all"]["open"]["n"] == 2


def test_spread_by_uk_half_hour_of_the_week():
    c = both(T("2025-11-02T21:00"), spread="18.4")      # Sunday 21:00 UK (GMT)
    d = both(T("2025-07-07T08:30"), spread="0.9")       # Monday 09:30 UK (BST)
    s = chk.spread_samples([c, d])
    r = chk.spread_by(s, chk.half_hour_of_week)
    assert r["Sun 21:00"]["median"] == D("18.4") and r["Sun 21:00"]["n"] == 2
    assert r["Mon 09:30"]["median"] == D("0.9")
    assert sorted(["Mon 00:00", "Fri 21:30", "Sun 21:00"], key=chk.week_order) == ["Sun 21:00", "Mon 00:00", "Fri 21:30"]


def test_spread_table_in_uk_time_of_a_normal_week():
    # Wed 28 Oct 2026: US still on summer time, UK not; IG's rollover is at 21:00 UK
    assert chk.half_hour_of_normal_week(T("2026-10-28T21:10")) == "Wed 22:00"
    assert chk.half_hour_of_normal_week(T("2026-11-04T22:10")) == "Wed 22:00"   # normal week
    assert chk.half_hour_of_normal_week(T("2026-10-25T21:10")) == "Sun 21:00"   # the open follows UK time
    assert chk.hour_of_normal_day(T("2026-10-28T21:10")) == "22:00"
