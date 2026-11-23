"""Functional tests for rule 3, counter-trend tiring (owner, 23 November 2026; strategies/entry_filters.py), with the
real settings and a real candle store of made-up hourly candles.

Johnny's rule (21 October 2026): "A bounce against an established trend is allowed only when the trend is tiring
(MACD 35/45/30 histogram shrinking); otherwise blocked."
  * every reversal-type strategy: the Bollinger bounce (hourly), the Bollinger bounce 5m, the level reversal, the
    session sweep and the New York open reversal;
  * against the trend = against the analyser's trend direction at the time;
  * each refusal records the strategy, the analyser state and the MACD values.
The owner's answers (23 November 2026): the HOURLY histogram; shrinking over 1 bar (closer to zero than the hourly bar
before); past zero on the trade's side counts as tiring; only the analyser's "trend" state counts as an established
trend (not "emerging trend" or "possible reversal"). Switch COUNTER_TREND_TIRING, on if left out.
Johnny's addition (23 November 2026): also allowed when the 5-MINUTE MACD 35/45/30 histogram, at the last finished
5-minute candle, has crossed zero onto the bounce's side (above zero for a buy, below for a sell). Everything else
stays the same.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace

import pytest

from config.settings_loader import load_settings
from prices.model import Candle
from prices.store import CandleStore
from strategies import entry_filters as ef
from strategies.common import (ASIAN_RANGE_BREAKOUT, BOLLINGER_BOUNCE, BOLLINGER_BOUNCE_5M, BREAKOUT, BUY,
                               EMA_PULLBACK, LEVEL_REVERSAL, NEW_YORK_OPEN_REVERSAL, RANGE_TRADE, SELL, SESSION_SWEEP,
                               SLOW_GRIND, Idea)

UTC = timezone.utc
AT = datetime(2026, 11, 18, 12, 0, 30, tzinfo=UTC)          # just after the 11:00 hourly candle finished
END = datetime(2026, 11, 18, 12, 0, tzinfo=UTC)
OTHERS = ("HOURLY_CONTEXT", "ENTRY_NEAR_EMA8", "RSI_STRETCH", "TREND_DAY_RSI_OFF", "COUNTER_TREND_TIRING")
REVERSALS = (BOLLINGER_BOUNCE, BOLLINGER_BOUNCE_5M, LEVEL_REVERSAL, SESSION_SWEEP, NEW_YORK_OPEN_REVERSAL)


def settings(tmp_path: Path, pretend_switches: Path, tiring: str | None = "on"):
    """The real settings with the tests' pretend switches: rules 1, 2 and 2b off; rule 3 as given (None: left out)."""
    text = "".join(line + "\n" for line in pretend_switches.read_text().splitlines()
                   if not line.startswith(tuple(k + "=" for k in OTHERS)))
    text += "HOURLY_CONTEXT=off\nENTRY_NEAR_EMA8=off\nRSI_STRETCH=off\nTREND_DAY_RSI_OFF=off\n"
    if tiring is not None:
        text += f"COUNTER_TREND_TIRING={tiring}\n"
    env = tmp_path / f"switches_tiring_{tiring}.env"
    env.write_text(text)
    return load_settings(switches_from=env).for_pair("GBPUSD")


@pytest.fixture
def S(tmp_path, pretend_switches):
    return settings(tmp_path, pretend_switches)


def hours(closes, tf="1h", minutes=60) -> list:
    """Candles (hourly unless given) ending at Wed 18 Nov 12:00 UTC, one per close; sell prices as given, buy 1.5 pips
    above."""
    n, out = len(closes), []
    for k, cl in enumerate(closes):
        t, p = END - timedelta(minutes=minutes * (n - k)), D(str(cl))
        out.append(Candle(tf, t, t + timedelta(minutes=minutes), *[p + D("1.5")] * 4, p, p, p, p, 60, 60))
    return out


def store_of(tmp_path, closes, name, five=None) -> CandleStore:
    """The hourly candles from `closes`, and 5-minute candles from `five` (the same shapes, on 5-minute candles)."""
    st = CandleStore(tmp_path / name / "candles" / "GBPUSD", 30)
    for x in hours(closes) + ([] if five is None else hours(five, "5m", 5)):
        st.add(x)
    return st


def mirror(closes):
    return [26600 - x for x in closes]


ACCEL = [13300] * 150 + [13300 - k * k * 0.2 for k in range(1, 47)]
# A fall getting faster: the hourly histogram below zero and growing (-14.77 after -14.54): NOT tiring for a buy.
GROWING_DOWN = ACCEL + [ACCEL[-1] - 15 * k for k in range(1, 5)]
# The same fall slowing to 5 pips an hour: below zero and shrinking (-13.81 after -13.93): tiring.
SHRINKING_DOWN = ACCEL + [ACCEL[-1] - 5 * k for k in range(1, 5)]
# A steady fall that has gone flat for 20 hours: the histogram past zero (2.46): tiring.
PAST_ZERO_DOWN = [13300 - 3 * k for k in range(180)] + [13300 - 3 * 179] * 20


@pytest.fixture
def GROWING(tmp_path):
    return store_of(tmp_path, GROWING_DOWN, "growing")


@pytest.fixture
def SHRINKING(tmp_path):
    return store_of(tmp_path, SHRINKING_DOWN, "shrinking")


@pytest.fixture
def PAST_ZERO(tmp_path):
    return store_of(tmp_path, PAST_ZERO_DOWN, "past_zero")


def idea(strategy=BOLLINGER_BOUNCE, direction=BUY, state="trend", state_direction="down", trend_type="slow grind",
         t=AT, price=13000) -> Idea:
    return Idea("GBPUSD", strategy, direction, t, D(str(price)), state, state_direction, trend_type, "sell side", [])


def hist(store, S):
    last, before, _ = ef.hourly_macd(S, store, AT)
    return before.histogram, last.histogram


def test_the_made_up_hours_give_a_growing_a_shrinking_and_a_past_zero_histogram(S, GROWING, SHRINKING, PAST_ZERO):
    b, h = hist(GROWING, S)
    assert h < b < 0                                   # further below zero
    b, h = hist(SHRINKING, S)
    assert b < h < 0                                   # closer to zero
    _, h = hist(PAST_ZERO, S)
    assert h > 0


def test_a_buy_against_a_trend_down_with_the_histogram_growing_is_refused_and_records_the_numbers(S, GROWING):
    v = ef.check(S, GROWING, idea())
    assert not v.allowed and v.rule == ef.COUNTER_TREND_TIRING
    d = v.details
    b, h = hist(GROWING, S)
    assert d["strategy"] == BOLLINGER_BOUNCE
    assert (d["analyser_state"], d["analyser_direction"], d["trend_type"]) == ("trend", "down", "slow grind")
    assert d["macd_timeframe"] == "1h"
    assert d["macd_candle"] == "2026-11-18T11:00Z" and d["macd_candle_before"] == "2026-11-18T10:00Z"
    assert (d["macd_histogram"], d["macd_histogram_before"]) == (f"{h:.2f}", f"{b:.2f}")
    assert "macd_line" in d and "macd_signal" in d
    assert "not shrinking" in v.why and "refused" in v.why


def test_shrinking_towards_zero_over_1_bar_is_tiring_and_allowed(S, SHRINKING):
    v = ef.check(S, SHRINKING, idea())
    assert v.allowed
    assert any("shrinking towards zero" in x for x in v.checked)


def test_past_zero_on_the_trades_side_counts_as_tiring(S, PAST_ZERO):
    v = ef.check(S, PAST_ZERO, idea())
    assert v.allowed
    assert any("past zero" in x for x in v.checked)


def test_the_mirror_a_sell_against_a_trend_up(tmp_path, S):
    up_growing = store_of(tmp_path, mirror(GROWING_DOWN), "up_growing")
    up_shrinking = store_of(tmp_path, mirror(SHRINKING_DOWN), "up_shrinking")
    up_past = store_of(tmp_path, mirror(PAST_ZERO_DOWN), "up_past")
    sell = dict(direction=SELL, state_direction="up", price=13600)
    v = ef.check(S, up_growing, idea(**sell))
    assert not v.allowed and v.rule == ef.COUNTER_TREND_TIRING
    assert ef.check(S, up_shrinking, idea(**sell)).allowed
    assert ef.check(S, up_past, idea(**sell)).allowed


@pytest.mark.parametrize("strategy", REVERSALS)
def test_every_reversal_type_strategy_is_checked(S, GROWING, strategy):
    v = ef.check(S, GROWING, idea(strategy))
    assert not v.allowed and v.rule == ef.COUNTER_TREND_TIRING and v.details["strategy"] == strategy


@pytest.mark.parametrize("strategy", (SLOW_GRIND, EMA_PULLBACK, RANGE_TRADE, BREAKOUT, ASIAN_RANGE_BREAKOUT))
def test_no_other_strategy_is_checked(S, GROWING, strategy):
    v = ef.check(S, GROWING, idea(strategy))
    assert v.allowed and not any("counter-trend" in x for x in v.checked)


def test_a_trade_with_the_trend_is_not_checked(S, GROWING):
    v = ef.check(S, GROWING, idea(direction=SELL))        # a sell in a trend down
    assert v.allowed and any("not against a trend" in x for x in v.checked)


@pytest.mark.parametrize("state,direction", [("emerging trend", "down"), ("possible reversal", "down"),
                                             ("ranging", "none"), ("consolidation", "none")])
def test_only_the_analysers_trend_state_counts_as_an_established_trend(S, GROWING, state, direction):
    v = ef.check(S, GROWING, idea(state=state, state_direction=direction, trend_type=None))
    assert v.allowed and any("not against a trend" in x for x in v.checked)


def macd_of(before, last):
    t = END - timedelta(hours=1)
    return (SimpleNamespace(candle_utc=t, histogram=D(str(last)), line=D("-5"), signal=D("-5")),
            SimpleNamespace(candle_utc=t - timedelta(hours=1), histogram=D(str(before)), line=D("-5"), signal=D("-5")), "")


@pytest.mark.parametrize("before,last,allowed", [
    ("-1.00", "-0.99", True),         # closer to zero
    ("-1.00", "-1.00", False),        # the same: not shrinking
    ("-1.00", "-1.01", False),        # further from zero
    ("0.77", "-0.05", False),         # crossing back below zero (today's 15:00 hour): growing on the trend's side
    ("-0.05", "0.01", True),          # crossing above zero: past zero
    ("0.50", "0.20", True),           # still above zero: past zero
    ("-0.10", "0", True),             # up to zero: closer to zero
])
def test_the_1_bar_comparison_for_a_buy_against_a_trend_down(S, monkeypatch, before, last, allowed):
    monkeypatch.setattr(ef, "hourly_macd", lambda s, st, at: macd_of(before, last))
    monkeypatch.setattr(ef, "five_minute_macd", lambda s, st, at: (None, "no 5-minute candles"))
    assert ef.check(S, None, idea()).allowed is allowed


@pytest.mark.parametrize("before,last,allowed", [
    ("1.00", "0.99", True), ("1.00", "1.00", False), ("1.00", "1.01", False), ("-0.77", "0.05", False),
    ("0.05", "-0.01", True), ("-0.50", "-0.20", True)])
def test_the_1_bar_comparison_for_a_sell_against_a_trend_up(S, monkeypatch, before, last, allowed):
    monkeypatch.setattr(ef, "hourly_macd", lambda s, st, at: macd_of(before, last))
    monkeypatch.setattr(ef, "five_minute_macd", lambda s, st, at: (None, "no 5-minute candles"))
    assert ef.check(S, None, idea(direction=SELL, state_direction="up")).allowed is allowed


def test_only_finished_hourly_candles_count(S, GROWING):
    early = AT - timedelta(minutes=1)                      # 11:59:30: the 11:00 candle has not finished
    last, before, _ = ef.hourly_macd(S, GROWING, early)
    assert (last.candle_utc.hour, before.candle_utc.hour) == (10, 9)


def test_too_few_hourly_candles_is_not_checked(S, tmp_path):
    few = store_of(tmp_path, GROWING_DOWN[-100:], "few")
    v = ef.check(S, few, idea())
    assert v.allowed and any("not checked" in x for x in v.checked)


def test_switch_off_and_left_out(tmp_path, pretend_switches, GROWING):
    off = settings(tmp_path, pretend_switches, "off")
    assert not off.switches.counter_trend_tiring
    assert ef.check(off, GROWING, idea()).allowed
    left_out = settings(tmp_path, pretend_switches, None)
    assert left_out.switches.counter_trend_tiring
    assert not ef.check(left_out, GROWING, idea()).allowed


# ---- Johnny's addition (23 November 2026): the 5-minute histogram across zero onto the bounce's side ----

def test_the_hourly_not_tiring_but_the_5_minute_histogram_above_zero_allows_a_buy(tmp_path, S):
    st = store_of(tmp_path, GROWING_DOWN, "g_5m_above", five=PAST_ZERO_DOWN)
    last5, _ = ef.five_minute_macd(S, st, AT)
    assert last5.candle_utc == END - timedelta(minutes=5) and last5.histogram > 0     # the 11:55 candle, above zero
    v = ef.check(S, st, idea())
    assert v.allowed
    assert any("not shrinking; but the 5-minute MACD" in x and "crossed above zero" in x for x in v.checked)


def test_the_hourly_not_tiring_and_the_5_minute_histogram_below_zero_refuses_a_buy_and_records_both(tmp_path, S):
    st = store_of(tmp_path, GROWING_DOWN, "g_5m_below", five=GROWING_DOWN)
    v = ef.check(S, st, idea())
    assert not v.allowed and v.rule == ef.COUNTER_TREND_TIRING
    last5, _ = ef.five_minute_macd(S, st, AT)
    d = v.details
    assert d["macd_5m_candle"] == "2026-11-18T11:55Z" and d["macd_5m_histogram"] == f"{last5.histogram:.2f}"
    assert "macd_5m_line" in d and "macd_5m_signal" in d
    assert d["macd_histogram"] and d["macd_histogram_before"] and d["analyser_state"] == "trend"
    assert "is not above zero" in v.why


def test_the_mirror_a_sell_against_a_trend_up_with_the_5_minute_histogram_below_zero(tmp_path, S):
    sell = dict(direction=SELL, state_direction="up", price=13600)
    across = store_of(tmp_path, mirror(GROWING_DOWN), "up_5m_below", five=mirror(PAST_ZERO_DOWN))
    not_across = store_of(tmp_path, mirror(GROWING_DOWN), "up_5m_above", five=mirror(GROWING_DOWN))
    assert ef.check(S, across, idea(**sell)).allowed
    v = ef.check(S, not_across, idea(**sell))
    assert not v.allowed and "is not below zero" in v.why


def five_of(h):
    return SimpleNamespace(candle_utc=END - timedelta(minutes=5), histogram=D(str(h)), line=D("0"), signal=D("0")), ""


@pytest.mark.parametrize("direction,state_direction,h5,allowed", [
    (BUY, "down", "0.01", True), (BUY, "down", "0", False), (BUY, "down", "-0.01", False),
    (SELL, "up", "-0.01", True), (SELL, "up", "0", False), (SELL, "up", "0.01", False)])
def test_the_5_minute_histogram_must_be_across_zero_on_the_bounces_side_exactly_zero_is_not(
        S, monkeypatch, direction, state_direction, h5, allowed):
    growing = ("-1.00", "-1.01") if state_direction == "down" else ("1.00", "1.01")      # hourly: not tiring
    monkeypatch.setattr(ef, "hourly_macd", lambda s, st, at: macd_of(*growing))
    monkeypatch.setattr(ef, "five_minute_macd", lambda s, st, at: five_of(h5))
    assert ef.check(S, None, idea(direction=direction, state_direction=state_direction)).allowed is allowed


def test_the_5_minute_histogram_is_only_looked_at_when_the_hourly_says_not_tiring(S, monkeypatch):
    calls = []
    monkeypatch.setattr(ef, "hourly_macd", lambda s, st, at: macd_of("-1.00", "-0.99"))       # shrinking
    monkeypatch.setattr(ef, "five_minute_macd", lambda s, st, at: calls.append(at) or five_of("-5"))
    assert ef.check(S, None, idea()).allowed and calls == []


def test_too_few_5_minute_candles_leaves_the_hourly_to_decide(tmp_path, S):
    st = store_of(tmp_path, GROWING_DOWN, "g_5m_few", five=PAST_ZERO_DOWN[-60:])
    m5, why = ef.five_minute_macd(S, st, AT)
    assert m5 is None and "5-minute" in why
    v = ef.check(S, st, idea())
    assert not v.allowed and v.details["macd_5m_histogram"] is None


def test_only_finished_5_minute_candles_count(tmp_path, S):
    st = store_of(tmp_path, GROWING_DOWN, "g_5m_finished", five=PAST_ZERO_DOWN)
    m5, _ = ef.five_minute_macd(S, st, END - timedelta(seconds=30))          # 11:59:30: the 11:55 candle not finished
    assert m5.candle_utc == END - timedelta(minutes=10)
