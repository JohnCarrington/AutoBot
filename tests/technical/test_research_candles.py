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


# ---- 161's 2026 mid candles to buy and sell -------------------------------------------------

from research import mid_to_bidask as mb


def mid(t, o, h, l, c):
    return cc.RCandle(t, t + FIVE, None, tuple(D(x) for x in (o, h, l, c)))


def test_mid_snapped_to_a_twentieth_and_refused_otherwise():
    assert mb.snap_mid("13376.150000000001") == D("13376.15")
    assert mb.snap_mid("13373.349999999999") == D("13373.35")
    for bad in ("13376.17", "nan", "-1"):
        with pytest.raises(ValueError):
            mb.snap_mid(bad)


def test_read_161_mid_skips_nan_rows_and_moves_jan_feb(tmp_path):
    (tmp_path / "2026-02-27.csv").write_text(
        "timestamp,open,high,low,close\n2026-02-27T16:55:00+00:00,13500.05,13501.0,13499.5,13500.0\n")
    (tmp_path / "2026-04-19.csv").write_text(
        "timestamp,open,high,low,close\n2026-04-19T20:15:00+00:00,13491.85,nan,nan,13491.75\n"
        "2026-04-19T20:20:00+00:00,13491.85,13492.0,13491.5,13491.75\n")
    r = mb.read_161_mid(tmp_path, mb.jan_feb_five_hours_late)
    assert [c.start for c in r.candles] == [T("2026-02-27T21:55"), T("2026-04-19T20:20")]
    assert r.moved == 1 and len(r.skipped) == 1 and "nan" in r.skipped[0][1]
    # 161's January "Sunday 17:00" open lands on 22:00 UK, inside IG's hours
    assert B.hours.is_open(T("2026-01-04T17:00") + mb.jan_feb_five_hours_late(T("2026-01-04T17:00")))
    assert mb.jan_feb_five_hours_late(T("2026-03-23T00:00")) == timedelta(0)


def test_sell_is_mid_minus_half_buy_is_mid_plus_half_rounded_outward():
    m = mid(T("2026-10-26T10:00"), "13377.55", "13380.65", "13374.6", "13375.45")
    c = mb.to_buy_sell(m, D("0.9"))
    assert c.sell == (D("13377.1"), D("13380.2"), D("13374.1"), D("13375.0"))
    assert c.buy == (D("13378.0"), D("13381.1"), D("13375.1"), D("13375.9"))
    assert all(b - s >= D("0.9") for b, s in zip(c.buy, c.sell))      # never narrower than the spread used
    o = mb.to_buy_sell(m, D("1.0"))                  # 13377.05 / 13378.05: on a twentieth
    assert o.sell[0] == D("13377.0") and o.buy[0] == D("13378.1")
    i = mb.to_buy_sell(m, D("1.0"), "inward")
    assert i.sell[0] == D("13377.1") and i.buy[0] == D("13378.0")
    n = mb.to_buy_sell(m, D("0.9"), "none")
    assert n.sell[0] == D("13377.10") and n.buy[0] == D("13378.00")
    # an IG-exact case: real sell 13366.6 / buy 13385.7 on the Sunday open -> mid 13376.15, spread 19.1
    assert mb.to_buy_sell(mid(T("2026-10-25T21:10"), "13376.15", "13376.15", "13376.15", "13376.15"),
                          D("19.1")).sell[0] == D("13366.6")


def test_spread_table_lookup_uses_uk_time_of_a_normal_week(tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("uk_half_hour_normal_week,samples,typical_points,p90_points,largest_points,smallest_points\n"
                 "Wed 22:00,24,16.9,16.9,24.6,1.8\nWed 21:00,24,0.9,1.5,1.5,0.9\n")
    f = mb.spread_from_table(mb.read_spread_table(p))
    assert f(T("2026-11-04T22:10")) == D("16.9")          # normal week: rollover at 22:00 UK
    assert f(T("2026-10-28T21:10")) == D("16.9")          # out-of-step week: rollover at 21:00 UK
    assert f(T("2026-11-04T21:10")) == D("0.9")
    with pytest.raises(KeyError):
        f(T("2026-11-04T10:00"))


def test_spread_table_built_from_real_ig_candles():
    t = mb.build_spread_table([both(T("2025-11-03T10:00"), spread="0.9"), both(T("2025-11-03T10:05"), spread="1.5"),
                               both(T("2025-11-03T10:10"), spread="0.9")])
    assert t == {"Mon 10:00": D("0.9")}


def test_converted_mids_build_like_the_bot_and_read_in_the_live_store(out):
    mids = [mid(T("2026-11-02T10:00") + i * FIVE, "13000.05", "13001.05", "12999.05", "13000.55") for i in range(12)]
    cc.convert(mb.convert_mids(mids, lambda t: D("0.9")), B, out, "test")
    [h] = CandleStore(out, 30).read_day("1h", date(2026, 11, 2))
    assert (h.parts, h.expected_parts) == (12, 12)
    assert (h.sell_open, h.buy_open) == (D("12999.6"), D("13000.5"))


# ---- research mode: the long replay, its store, its calendar ------------------------------------------

import json as _json
from types import SimpleNamespace as _NS

from research import long_replay as lr
from research import news_history as nh
from research import replay_store as rs


def test_replay_writes_only_under_research_never_a_live_folder(tmp_path):
    for live in ("/opt/autobot/data/candles/GBPUSD", "/opt/autobot/data/orders", "/opt/autobot/data/records/x",
                 "/opt/autobot/data/news", "/opt/autobot/data/trade_manager"):
        with pytest.raises(PermissionError):
            lr.check_research_folder(live)
    with pytest.raises(PermissionError):
        lr.check_research_folder(tmp_path / "x")
    assert lr.check_research_folder(tmp_path / "x", allow=tmp_path) == (tmp_path / "x").resolve()
    assert lr.check_research_folder("/opt/autobot/data/research/replay/x").name == "x"


def test_every_engine_folder_is_moved_into_the_run(tmp_path):
    s = lr.Over(SETTINGS, tmp_path / "run", tmp_path / "store" / "GBPUSD")
    for path in (s.orders.folder, s.trade_manager.folder, s.safety.folder, s.records.folder, s.news.folder,
                 s.market_states.folder, s.trading.pause_file, s.dashboard.status_folder):
        assert str(path).startswith(str(tmp_path / "run"))
    assert s.candles.folder == tmp_path / "store"
    assert s.market.pair == "GBPUSD"                                  # everything else is the bot's own


def test_the_weeks_calendar_is_written_where_the_news_rules_read_it(tmp_path):
    from news.calendar import big_news_windows
    ev = [{"time_utc": "2026-11-05T12:00:00Z", "country": "GB", "event": "BoE Interest Rate Decision",
           "impact": "high", "estimate": 4.0, "prev": 4.0},
          {"time_utc": "2026-10-01T12:00:00Z", "country": "GB", "event": "BoE Interest Rate Decision",
           "impact": "high", "estimate": 4.0, "prev": 4.0}]
    n = lr.write_calendar(tmp_path / "news", ev, T("2026-11-01T21:00"), T("2026-11-06T22:00"))
    assert n == 1                                                     # only the week's releases
    s = lr.Over(SETTINGS, tmp_path, tmp_path / "store" / "GBPUSD")
    w = big_news_windows(s, "GBPUSD", T("2026-11-05T00:00"), T("2026-11-06T00:00"))
    assert [x.event for x in w] == ["BoE Interest Rate Decision"]
    assert lr.write_calendar(tmp_path / "news", None, T("2026-11-01T21:00"), T("2026-11-06T22:00")) == 0
    assert big_news_windows(s, "GBPUSD", T("2026-11-05T00:00"), T("2026-11-06T00:00")) == []


def test_weeks_of_a_range():
    ws = lr.weeks(B.hours, T("2026-10-28T12:00"), T("2026-11-09T10:05"))
    assert ws == [(T("2026-10-25T21:00"), T("2026-10-30T21:00")),      # US still on summer time: 17:00 NY
                  (T("2026-11-01T21:00"), T("2026-11-06T22:00")),
                  (T("2026-11-08T21:00"), T("2026-11-09T10:05"))]
    assert lr.weeks(B.hours, T("2026-10-31T12:00"), T("2026-11-02T00:00"))[0][0] == T("2026-11-01T21:00")


def _t(entry, pips, strategy="slow grind", n=""):
    return lr.Trade("w", entry, strategy, "buy", "1", "1", pips, entry, "stop", "why" + n, "s")


def test_stats_wins_losses_biggest_loss_and_worst_run():
    s = lr.stats([_t("2026-01-01T10:00:00Z", "5"), _t("2026-01-01T11:00:00Z", "-3"),
                  _t("2026-01-01T12:00:00Z", "-12"), _t("2026-01-01T13:00:00Z", "-1"),
                  _t("2026-01-01T14:00:00Z", "0"), _t("2026-01-01T15:00:00Z", "-2")])
    assert (s["trades"], s["won"], s["lost"], s["pips"], s["biggest_loss"], s["worst_run"]) == (6, 1, 4, D(-13), D(-12), 3)
    assert lr.by([_t("2026-01-31T23:30:00Z", "1")], lr.month_of) == {"2026-01": lr.stats([_t("2026-01-31T23:30:00Z", "1")])}
    assert list(lr.by([_t("2026-03-31T23:30:00Z", "1")], lr.month_of)) == ["2026-04"]   # UK month (BST)


def test_compare_counts_copies_opened_in_the_same_minute():
    a = [_t("2026-01-01T10:00:00Z", "30"), _t("2026-01-01T10:00:00Z", "30"), _t("2026-01-01T11:00:00Z", "-12")]
    b = [_t("2026-01-01T10:00:00Z", "30"), _t("2026-01-01T11:00:00Z", "-6")]
    c = lr.compare(a, b)
    assert len(c["same"]) == 1 and len(c["only_a"]) == 1 and c["only_a"][0][3] == 1
    assert len(c["different_result"]) == 1 and c["only_b"] == []


def _walk(n, start="2026-11-02T00:00"):
    import random
    rnd = random.Random(7)
    p, out, t = D("13000.0"), [], T(start)
    for _ in range(n):
        o = p
        c = o + D(rnd.randint(-40, 40)) / 10
        h, l = max(o, c) + D(rnd.randint(0, 20)) / 10, min(o, c) - D(rnd.randint(0, 20)) / 10
        out.append(Candle("5m", t, t + FIVE, o + 1, h + 1, l + 1, c + 1, o, h, l, c))
        p, t = c, t + FIVE
    return out


from prices.model import Candle  # noqa: E402


def test_the_analysers_features_are_causal_so_the_week_can_be_worked_out_once():
    from analyser.features import compute
    candles = _walk(400)
    whole = compute(candles, SETTINGS)
    for n in (1, 25, 150, 399):
        assert compute(candles[:n], SETTINGS) == whole[:n]


def test_speedups_cache_only_the_research_store(tmp_path, out):
    cc.convert([both(T("2026-11-02T10:00"))], B, out, "test")
    other = tmp_path / "other" / "GBPUSD"
    cc.convert([both(T("2026-11-02T10:00"))], B, other, "test")
    from prices.store import CandleStore
    saved = (CandleStore.read_day, CandleStore.days, getattr(CandleStore, "_research_cached", False))
    import analyser.market_state as ms
    saved_compute = ms.compute
    try:
        lr.install_speedups(out)
        st, ot = CandleStore(out, 30), CandleStore(other, 30)
        assert len(st.read_day("5m", date(2026, 11, 2))) == 1
        (out / "5m" / "2026-11-02.csv").write_text((out / "5m" / "2026-11-02.csv").read_text().splitlines()[0] + "\n")
        assert len(st.read_day("5m", date(2026, 11, 2))) == 1          # the research store: read once
        (other / "5m" / "2026-11-02.csv").write_text((other / "5m" / "2026-11-02.csv").read_text().splitlines()[0] + "\n")
        assert ot.read_day("5m", date(2026, 11, 2)) == []              # any other store: read fresh every time
    finally:
        CandleStore.read_day, CandleStore.days = saved[0], saved[1]
        CandleStore._research_cached = saved[2]
        ms.compute = saved_compute


def test_2024_2025_buy_is_sell_plus_the_half_hour_spread():
    fives = [cc.RCandle(T("2025-11-05T22:10"), T("2025-11-05T22:15"), None,
                        (D("13000.0"), D("13001.0"), D("12999.0"), D("13000.5")))]
    [c] = rs.bid_ask_from_sell(fives, lambda t: D("16.9"))
    assert c.buy == (D("13016.9"), D("13017.9"), D("13015.9"), D("13017.4")) and c.sell == fives[0].sell


def test_merged_store_takes_each_candle_from_its_own_source(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTOBOT_RESEARCH_TEST_ROOT", str(tmp_path))
    times = [T("2025-12-31T23:55"), T("2026-01-01T00:00"), T("2026-10-23T20:00"), T("2026-10-26T10:00")]
    src = {}
    for name, bid in (("2024-2025", "13000.0"), ("2026", "13100.0"), ("live", "13200.0")):
        folder = tmp_path / name / "GBPUSD"
        cc.convert([both(t, bid) for t in times], B, folder, "test")       # every source holds every candle
        src[name] = folder
    rs.merge(tmp_path / "merged" / "GBPUSD", src)
    from prices.store import CandleStore
    m = CandleStore(tmp_path / "merged" / "GBPUSD", 30)
    got = {c.start: c.sell_open for d in m.days("5m") for c in m.read_day("5m", d)}
    assert got == {T("2025-12-31T23:55"): D("13000.0"), T("2026-01-01T00:00"): D("13100.0"),
                   T("2026-10-23T20:00"): D("13100.0"), T("2026-10-26T10:00"): D("13200.0")}
    assert rs.source_for(T("2026-10-24T22:55")) == "2026"            # Sat 24 Oct 23:55 BST
    assert rs.source_for(T("2026-10-24T23:00")) == "live"            # Sun 25 Oct 00:00 BST
    with pytest.raises(ValueError, match="GBPUSD"):
        rs.merge(tmp_path / "merged" / "EURUSD", src)


# ---- the past economic calendar from Finnhub ---------------------------------------------------------

def test_months_and_cover_check():
    assert nh.months("2024-01", "2024-03") == [(date(2024, 1, 1), date(2024, 1, 31)), (date(2024, 2, 1), date(2024, 2, 29)),
                                              (date(2024, 3, 1), date(2024, 3, 31))]
    rows = [{"time_utc": "2024-03-01T07:00:00Z"}, {"time_utc": "2024-03-29T12:00:00Z"}]
    assert nh.covers(rows, date(2024, 3, 1), date(2024, 3, 31))      # 31 March is a Sunday: Friday 29th counts
    assert not nh.covers(rows[:1], date(2024, 3, 1), date(2024, 3, 31))


class _Reply:
    def __init__(self, code, rows=None):
        self.status_code, self._rows = code, rows

    def json(self):
        return {"economicCalendar": self._rows}


def test_fetcher_is_gentle_and_never_shows_the_key():
    calls, slept = [], []
    replies = [_Reply(429), _Reply(200, [{"time": "2024-01-01 13:30:00", "country": "US", "event": "CPI"},
                                         {"time": "2024-01-31 13:30:00", "country": "US", "event": "CPI"}])]

    class Http:
        def get(self, url, params, timeout):
            calls.append(params["from"])
            return replies.pop(0)

    logs = []
    clock = iter(range(0, 10 ** 6, 1))
    f = nh.Fetcher("https://x", _NS(key="SECRET"), Http(), gap_seconds=20, sleep=slept.append,
                   clock=lambda: next(clock), log=logs.append)
    rows, problems = f.month(date(2024, 1, 1), date(2024, 1, 31))
    assert len(rows) == 2 and problems == [] and rows[0]["time_utc"] == "2024-01-01T13:30:00Z"
    assert 120 in slept                                              # backed off after the refusal
    assert all("SECRET" not in x for x in logs)
    assert f.requests == 2


def test_a_run_can_change_one_switch_without_touching_env(tmp_path, monkeypatch):
    sw = tmp_path / "switches.env"

    def fake_settings(tmp, switches=None):
        (Path(tmp) / "switches.env").write_text("TRADING=off\nSTOP_LOSS_PIPS=6\nSTOP_LOSS_PIPS_EMA_PULLBACK=12\n")
    from pathlib import Path
    monkeypatch.setattr(lr, "settings_for", fake_settings)
    p = lr.freeze_switches(tmp_path, {"STOP_LOSS_PIPS": "12"})
    assert p.read_text().splitlines() == ["TRADING=off", "STOP_LOSS_PIPS=12", "STOP_LOSS_PIPS_EMA_PULLBACK=12"]
    assert lr.freeze_switches(tmp_path, {"STOP_LOSS_PIPS": "12"}) == p           # same values: fine
    with pytest.raises(ValueError, match="other values"):
        lr.freeze_switches(tmp_path, {"STOP_LOSS_PIPS": "6"})                   # one run never mixes rules
    with pytest.raises(ValueError, match="TRADING off"):
        lr.freeze_switches(tmp_path / "b", {"TRADING": "on"})
    with pytest.raises(ValueError, match="unknown"):
        lr.freeze_switches(tmp_path / "c", {"NO_SUCH": "1"})


def test_two_runs_side_by_side_per_strategy_and_year(tmp_path):
    import json
    from dataclasses import asdict
    from research.long_report import side_by_side

    def write(name, trades):
        (tmp_path / name / "weeks").mkdir(parents=True)
        (tmp_path / name / "weeks" / "w.json").write_text(json.dumps({"trades": [asdict(t) for t in trades]}))
        return tmp_path / name

    a = write("a", [_t("2025-06-01T10:00:00Z", "-6", "Bollinger bounce"), _t("2026-06-01T10:00:00Z", "5")])
    b = write("b", [_t("2025-06-01T10:00:00Z", "-12", "Bollinger bounce"), _t("2026-06-01T10:00:00Z", "5")])
    out = side_by_side(a, b, "stop 6", "stop 12")
    whole = out.split("#### 2025")[0]
    rows = {line.split(" | ")[0]: line for line in whole.splitlines() if line.startswith("| ")}
    assert "#### The whole period" in out and "#### 2025" in out and "#### 2026" in out
    assert rows["| Bollinger bounce"].endswith("**-6.0** |")
    assert rows["| slow grind"].endswith("**+0.0** |")


def test_a_week_rerun_after_an_interruption_starts_from_an_empty_engine_folder(tmp_path, monkeypatch):
    left = tmp_path / "engine" / "2024-03-10" / "trade_manager"
    left.mkdir(parents=True)
    (left / "open.json").write_text("{}")                     # an interrupted attempt's open trade
    seen = []
    monkeypatch.setattr(lr, "settings_for", lambda tmp, switches=None: None)
    monkeypatch.setattr(lr, "replay_week", lambda base, store, a, b, events, folder, only: seen.append(
        list(folder.rglob("*")) if folder.exists() else []) or [])
    w, n, how = lr._job(("s", None, "2024-03-10T20:00:00Z", "2024-03-15T22:00:00Z", tmp_path, None))
    assert (n, how) == (0, "done") and seen == [[]]
    assert (tmp_path / "weeks" / "2024-03-10.json").exists()
