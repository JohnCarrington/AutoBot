"""Technical tests for Stage 7 part 1: the analyser's indicators (EMA, MACD,
RSI, Bollinger), the direction rule, and whether the data is ready, warming up
or out of date. Uses made-up candles in a temporary store; never contacts IG."""

import re
from datetime import timedelta
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace

import pytest

from analyser.data_status import OUT_OF_DATE, READY, WARMING_UP, judge, last_open_slot_before
from analyser.direction import BUY_SIDE, NONE, SELL_SIDE, decide
from analyser.indicators import last_candles, work_out
from analyser.report import analyse
from prices.calendar import MarketHours
from prices.indicators import ema, macd, needs_ema, needs_macd, needs_rsi, rsi
from prices.model import Candle
from prices.store import CandleStore
from tests.technical.fake_stream import SETTINGS, T

ROOT = Path(__file__).resolve().parents[2]
FIVE = timedelta(minutes=5)


def C(start, close, tf="5m", minutes=5, spread=D("1.0")):
    """A candle whose SELL close is `close` (buy = sell + spread)."""
    c = D(str(close))
    return Candle(tf, start, start + timedelta(minutes=minutes), c + spread, c + 1 + spread, c - 1 + spread,
                  c + spread, c, c + 1, c - 1, c)


def series(closes, start=T(2026, 11, 4, 9)):
    return [C(start + i * FIVE, x) for i, x in enumerate(closes)]


# ---- the indicator maths --------------------------------------------------------------

def test_ema_starts_from_the_simple_average_then_uses_2_over_periods_plus_1():
    cs = series([1, 2, 3, 4, 5, 10])
    e = ema(cs, "sell", 3)
    assert cs[1].start not in e                                     # not enough closes yet
    assert e[cs[2].start] == D(2)                                   # (1 + 2 + 3) / 3
    assert e[cs[3].start] == D(3)                                   # 2 + (4 - 2) x 0.5
    assert e[cs[4].start] == D(4)
    assert e[cs[5].start] == D(7)                                   # 4 + (10 - 4) x 0.5


def test_indicators_use_the_sell_price_not_the_buy_price():
    cs = series([1, 2, 3])
    assert ema(cs, "sell", 3)[cs[2].start] == D(2)
    assert ema(cs, "buy", 3)[cs[2].start] == D(3)                   # buy is sell + 1 here


def test_macd_line_is_fast_minus_slow_signal_is_its_ema_histogram_the_difference():
    closes = [10, 11, 13, 12, 15, 14, 16, 18, 17, 20]
    cs = series(closes)
    m = macd(cs, "sell", 2, 3, 2)
    f, s = ema(cs, "sell", 2), ema(cs, "sell", 3)
    lines = [f[c.start] - s[c.start] for c in cs[2:]]
    assert cs[2].start not in m                                     # the signal needs 2 MACD values
    first = m[cs[3].start]
    assert first.line == lines[1] and first.signal == (lines[0] + lines[1]) / 2
    nxt = m[cs[4].start]
    assert nxt.signal == first.signal + (lines[2] - first.signal) * D(2) / D(3)
    assert nxt.histogram == nxt.line - nxt.signal


def test_rsi_is_wilders_smoothing():
    cs = series([10, 11, 10, 12, 11])          # changes +1 -1 +2 -1
    r = rsi(cs, "sell", 3)
    assert cs[2].start not in r
    # first: gain (1+0+2)/3 = 1, loss (0+1+0)/3 = 1/3 -> RS 3 -> RSI 75
    assert r[cs[3].start] == D(75)
    # next: gain (1x2 + 0)/3 = 2/3, loss (1/3 x 2 + 1)/3 = 5/9 -> RS 1.2 -> RSI 54.5...
    assert abs(r[cs[4].start] - (D(100) - D(100) / (1 + (D(2) / 3) / (D(5) / 9)))) < D("1e-20")


def test_rsi_is_100_with_no_losses_and_50_when_flat():
    assert list(rsi(series([1, 2, 3, 4]), "sell", 3).values()) == [D(100)]
    assert list(rsi(series([5, 5, 5, 5]), "sell", 3).values()) == [D(50)]


def test_warm_up_counts_follow_the_2_percent_rule():
    # an EMA of 3: weight 0.5 a candle; 0.5^6 = 1.6% <= 2% -> 3 + 6 candles
    assert needs_ema(3, 2) == 9
    assert needs_ema(100, 2) == 296 and needs_ema(200, 2) == 592
    assert needs_rsi(3, 2) == 4 + 10                          # (2/3)^10 = 1.7%
    # MACD: the slow EMA (45 + 89 = 134) or the signal line started at candle 45 (44 + 89 = 133)
    assert needs_macd(35, 45, 30, 2) == max(needs_ema(45, 2), 44 + needs_ema(30, 2)) == 134


def test_the_indicator_settings_are_as_on_the_chart():
    ind = SETTINGS.indicators
    assert ind.ema_periods == (7, 13, 21, 100, 200)
    assert (ind.bollinger_periods, ind.bollinger_std_devs) == (20, 2)
    assert (ind.macd_fast_periods, ind.macd_slow_periods, ind.macd_signal_periods) == (35, 45, 30)
    assert (ind.rsi_periods, ind.rsi_upper_line, ind.rsi_lower_line) == (3, 70, 30)
    assert ind.timeframes == ("5m", "1h") and SETTINGS.chart.price == "sell"
    assert (SETTINGS.analyser.direction_ema_timeframe, SETTINGS.analyser.direction_ema_periods) == ("5m", 100)


# ---- working them out from the store ------------------------------------------------

def _settings(tmp_path, **ind):
    d = {k: v for k, v in vars(SETTINGS.indicators).items() if not k.startswith("_")}
    d.update(ind)
    cand = {k: v for k, v in vars(SETTINGS.candles).items() if not k.startswith("_")}
    cand["folder"] = tmp_path / "candles" / "GBPUSD"
    lv = {k: v for k, v in vars(SETTINGS.levels).items() if not k.startswith("_")}
    lv["folder"] = tmp_path / "levels"
    return SimpleNamespace(indicators=SimpleNamespace(**d), chart=SETTINGS.chart, analyser=SETTINGS.analyser,
                           market=SETTINGS.market, market_hours=SETTINGS.market_hours,
                           candles=SimpleNamespace(**cand), levels=SimpleNamespace(**lv))


def _store(s, candles):
    st = CandleStore(s.candles.folder, 30)
    for c in candles:
        st.add(c)
    return st


def test_only_candles_finished_by_the_time_asked_are_used(tmp_path):
    s = _settings(tmp_path)
    st = _store(s, series(range(100, 130)))
    f = work_out(s, st, "5m", T(2026, 11, 4, 9, 52))
    assert f.candle.start == T(2026, 11, 4, 9, 45) and f.candles_used == 10      # 09:50 not finished at 09:52
    assert len(last_candles(st, "5m", T(2026, 11, 4, 12), 7)) == 7


def test_values_and_readiness_on_one_timeframe(tmp_path):
    s = _settings(tmp_path, ema_periods=(3, 5), bollinger_periods=3, macd_fast_periods=2, macd_slow_periods=3,
                  macd_signal_periods=2, rsi_periods=3, history_candles=20)
    st = _store(s, series([10, 11, 10, 12, 11, 13, 12, 14, 13, 15]))
    f = work_out(s, st, "5m", T(2026, 11, 4, 10))
    assert f.values["ema_3"] == ema(series([10, 11, 10, 12, 11, 13, 12, 14, 13, 15]), "sell", 3)[T(2026, 11, 4, 9, 45)]
    # 10 candles: EMA 3 needs 9, EMA 5 needs 15, MACD 2/3/2 needs 9, RSI 3 needs 14
    assert f.ready == {"ema_3": True, "ema_5": False, "bollinger": True, "macd": True, "rsi": False}
    assert f.warming_up() == ["ema_5", "rsi"]


# ---- the direction rule ------------------------------------------------------------

@pytest.mark.parametrize("price,pivot,ema_,side", [
    (D(105), D(100), D(101), BUY_SIDE),
    (D(95), D(100), D(99), SELL_SIDE),
    (D(100.5), D(100), D(101), NONE),            # above the pivot, below the EMA
    (D(99.5), D(100), D(99), NONE),              # below the pivot, above the EMA
    (D(100), D(100), D(99), NONE),               # exactly on the pivot
    (D(105), None, D(99), NONE),                 # no pivot
    (D(105), D(100), None, NONE),                # no EMA
])
def test_direction_rule(price, pivot, ema_, side):
    d = decide(price, "test", pivot, ema_, "5m 100 EMA", True)
    assert d.side == side
    assert d.allows_buy == (side == BUY_SIDE) and d.allows_sell == (side == SELL_SIDE)


# ---- ready, warming up, out of date ----------------------------------------------

def _frame(tf, end, warming=()):
    c = C(end - (FIVE if tf == "5m" else timedelta(hours=1)), 100, tf,
          5 if tf == "5m" else 60) if end else None
    return SimpleNamespace(timeframe=tf, candle=c, candles_used=50, needs={n: 99 for n in warming},
                           warming_up=lambda: list(warming))


def test_ready_when_up_to_date_and_warmed_up():
    st = judge(SETTINGS, [_frame("5m", T(2026, 11, 4, 12)), _frame("1h", T(2026, 11, 4, 12))], T(2026, 11, 4, 12, 1))
    assert st.state == READY


def test_warming_up_names_each_indicator():
    st = judge(SETTINGS, [_frame("5m", T(2026, 11, 4, 12)), _frame("1h", T(2026, 11, 4, 12), ["ema_200"])],
               T(2026, 11, 4, 12, 1))
    assert st.state == WARMING_UP and st.reasons == ["1h ema_200 has 50 of the 99 candles it needs"]


def test_out_of_date_while_the_market_is_open_comes_first():
    st = judge(SETTINGS, [_frame("5m", T(2026, 11, 4, 11, 45)), _frame("1h", T(2026, 11, 4, 11), ["ema_200"])],
               T(2026, 11, 4, 12, 1))
    assert st.state == OUT_OF_DATE and st.reasons[0].startswith("5m: newest candle ends")
    allowed = judge(SETTINGS, [_frame("5m", T(2026, 11, 4, 11, 50)), _frame("1h", T(2026, 11, 4, 12))],
                    T(2026, 11, 4, 12, 1))
    assert allowed.state == READY                                       # 10 minutes behind is allowed
    assert judge(SETTINGS, [_frame("5m", None)], T(2026, 11, 4, 12)).state == OUT_OF_DATE


def test_a_weekend_is_not_out_of_date():
    # Market closed Fri 6 Nov 22:00 GMT; asked on Sunday 8 Nov at 20:00 and at 21:03 (opened 21:00)
    frames = [_frame("5m", T(2026, 11, 6, 22)), _frame("1h", T(2026, 11, 6, 22))]
    assert judge(SETTINGS, frames, T(2026, 11, 8, 20)).state == READY
    assert judge(SETTINGS, frames, T(2026, 11, 8, 21, 3)).state == READY
    assert judge(SETTINGS, frames, T(2026, 11, 8, 21, 20)).state == OUT_OF_DATE   # open 20 minutes, nothing new


def test_last_open_slot_before():
    h = MarketHours(SETTINGS.market_hours)
    assert last_open_slot_before(h, T(2026, 11, 4, 12, 2)) == T(2026, 11, 4, 11, 55)
    assert last_open_slot_before(h, T(2026, 11, 7, 12)) == T(2026, 11, 6, 21, 55)
    assert last_open_slot_before(h, T(2026, 11, 8, 21, 0)) == T(2026, 11, 6, 21, 55)
    assert last_open_slot_before(h, T(2026, 11, 8, 21, 5)) == T(2026, 11, 8, 21, 0)


# ---- the whole report ------------------------------------------------------------

def test_report_from_a_store_with_a_pivot(tmp_path):
    s = _settings(tmp_path, ema_periods=(3, 100), history_candles=400)
    day = T(2026, 11, 3)                                                  # Tue: a full day for the pivot
    cs = [C(day + i * FIVE, 100 + (i % 7)) for i in range(288)]
    cs += [C(T(2026, 11, 4) + i * FIVE, 120) for i in range(24)]          # Wed 00:00-02:00 well above
    st = _store(s, cs)
    st.add(Candle("1d", day, day + timedelta(days=1), D(104), D(108), D(100), D(104), D(103), D(107), D(99), D(103)))
    r = analyse(s, st, T(2026, 11, 4, 2))
    assert r.direction.pivot == D("103.0")                               # (107 + 99 + 103) / 3
    assert r.direction.price == D(120) and r.direction.side == BUY_SIDE
    assert r.direction.price_from.startswith("close of the 5m candle")
    assert analyse(s, st, T(2026, 11, 4, 2), price=D(90)).direction.side == SELL_SIDE   # live price, below both


def test_the_analyser_never_contacts_ig():
    for p in (ROOT / "analyser").glob("*.py"):
        src = p.read_text()
        assert not re.search(r"^\s*(from|import)\s+ig\b", src, re.M), p.name
