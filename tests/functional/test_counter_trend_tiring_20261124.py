"""Functional tests for the owner's two changes to rule 3 (24 November 2026; strategies/entry_filters.py), with the
real settings and a real candle store of made-up hourly candles (the fixtures of test_counter_trend_tiring.py).

  1. COUNTER_TREND_EMERGING (on if left out): rule 3 also applies when the analyser's state is "emerging trend", not
     only "trend".
  2. COUNTER_TREND_HOURLY_CONFIRMED (on if left out): if the hourly MACD histogram is on the bounce's side of zero
     because it never went to the trend's side, that is NOT tiring (the hourly has not confirmed the trend). A cross
     past zero counts as tiring only when the histogram was on the trend's side first: at an hourly candle since the
     analyser's state began (the owner's answer), before the last finished one. "Shrinking" counts only while the
     histogram is on the trend's side (the owner's answer). Everything else in rule 3 unchanged, including the
     5-minute zero-cross. No link to the slow-grind trend day (the owner's answer).
"""

from datetime import timedelta
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from prices.indicators import macd
from strategies import entry_filters as ef
from strategies.common import BOLLINGER_BOUNCE, BUY, SELL, Candidate, check as strategy_check
from tests.functional.test_counter_trend_tiring import (ACCEL, AT, END, GROWING_DOWN, idea, macd_of, mirror, settings,
                                                        store_of)

# A fall getting faster, then flat for 30 hours: the hourly histogram well below zero, then above it (+3.26 after +2.84).
DOWN_THEN_FLAT = ACCEL + [ACCEL[-1]] * 30


@pytest.fixture
def ON(tmp_path, pretend_switches):
    """Rule 3 with both changes on (left out: on)."""
    return settings(tmp_path, pretend_switches, "on", None, None)


def histograms(S, store):
    """{hourly candle start: histogram} for the store's finished hourly candles at AT."""
    hc = ef.last_candles(store, "1h", AT, S.indicators.history_candles)
    m = macd(hc, S.chart.price, S.indicators.macd_fast_periods, S.indicators.macd_slow_periods,
             S.indicators.macd_signal_periods)
    return {c.start: m[c.start].histogram for c in hc if c.start in m}


def test_both_switches_are_on_if_left_out_and_can_be_switched_off(tmp_path, pretend_switches, ON):
    assert ON.switches.counter_trend_emerging and ON.switches.counter_trend_hourly_confirmed
    off = settings(tmp_path, pretend_switches, "on", "off", "off")
    assert not off.switches.counter_trend_emerging and not off.switches.counter_trend_hourly_confirmed


# ---- change 1: the emerging trend counts ----

def test_a_buy_against_an_emerging_trend_down_is_checked_and_refused_when_not_tiring(tmp_path, pretend_switches, ON):
    growing = store_of(tmp_path, GROWING_DOWN, "growing")
    v = ef.check(ON, growing, idea(state="emerging trend", trend_type=None))
    assert not v.allowed and v.rule == ef.COUNTER_TREND_TIRING
    assert v.details["analyser_state"] == "emerging trend" and "against the emerging trend down" in v.why
    off = settings(tmp_path, pretend_switches, "on", "off", "on")      # change 1 off: not checked, as before
    v = ef.check(off, growing, idea(state="emerging trend", trend_type=None))
    assert v.allowed and any("not against a trend" in x for x in v.checked)


def test_the_mirror_a_sell_against_an_emerging_trend_up(tmp_path, ON):
    rising = store_of(tmp_path, mirror(GROWING_DOWN), "rising")
    v = ef.check(ON, rising, idea(direction=SELL, state="emerging trend", state_direction="up", trend_type=None))
    assert not v.allowed and v.rule == ef.COUNTER_TREND_TIRING


@pytest.mark.parametrize("state,direction", [("possible reversal", "down"), ("ranging", "none"),
                                             ("consolidation", "none")])
def test_other_states_are_still_not_checked(tmp_path, ON, state, direction):
    growing = store_of(tmp_path, GROWING_DOWN, "growing")
    v = ef.check(ON, growing, idea(state=state, state_direction=direction, trend_type=None))
    assert v.allowed and any("not against a trend" in x for x in v.checked)


def test_a_trade_with_the_emerging_trend_is_not_checked(tmp_path, ON):
    growing = store_of(tmp_path, GROWING_DOWN, "growing")
    v = ef.check(ON, growing, idea(direction=SELL, state="emerging trend", trend_type=None))
    assert v.allowed and any("not against a trend" in x for x in v.checked)


# ---- change 2: the hourly must have confirmed the trend ----

def test_a_histogram_that_never_went_to_the_trends_side_is_not_tiring(tmp_path, pretend_switches, ON):
    """A market rising faster (the histogram above zero and growing) while the analyser says trend down (5-minute):
    before, "past zero" let the buy through; now the hourly has not confirmed the trend: refused."""
    rising = store_of(tmp_path, mirror(GROWING_DOWN), "rising")
    assert all(h > 0 for h in list(histograms(ON, rising).values())[-30:])
    since = AT - timedelta(hours=20)
    v = ef.check(ON, rising, ef_idea(since))
    assert not v.allowed and v.rule == ef.COUNTER_TREND_TIRING
    assert "never on the trend's side since the state began" in v.why and "not confirmed the trend" in v.why
    old = settings(tmp_path, pretend_switches, "on", "on", "off")        # change 2 off: past zero, allowed as before
    assert ef.check(old, rising, ef_idea(since)).allowed


def ef_idea(since, **kw):
    i = idea(**kw)
    i.state_since = since
    return i


def test_a_cross_past_zero_after_the_trends_side_since_the_state_began_is_tiring(tmp_path, ON):
    """The fall that went flat: the histogram was below zero, then crossed above. Allowed only if it was below
    zero at an hourly candle since the state began."""
    flat = store_of(tmp_path, DOWN_THEN_FLAT, "down_then_flat")
    hs = histograms(ON, flat)
    last_neg = max(t for t, h in hs.items() if h < 0)
    assert list(hs.values())[-1] > 0
    early = ef.check(ON, flat, ef_idea(last_neg - timedelta(minutes=30)))      # the state began before it: confirmed
    assert early.allowed and any("past zero, the trend is tiring" in x and "on the trend's side at the" in x
                                 for x in early.checked)
    late = ef.check(ON, flat, ef_idea(last_neg + timedelta(hours=2)))         # began after it went above zero
    assert not late.allowed and "never on the trend's side since the state began" in late.why


def test_when_the_states_start_is_not_known_only_the_hourly_candle_before_counts(tmp_path, ON):
    flat = store_of(tmp_path, DOWN_THEN_FLAT, "down_then_flat")
    v = ef.check(ON, flat, ef_idea(None))
    assert not v.allowed and "the state's start not known" in v.why


def test_the_5_minute_zero_cross_still_allows_when_the_hourly_has_not_confirmed(tmp_path, ON):
    up = mirror(GROWING_DOWN)
    store = store_of(tmp_path, up, "rising_5m", five=up)                  # the 5-minute histogram above zero too
    v = ef.check(ON, store, ef_idea(AT - timedelta(hours=20)))
    assert v.allowed and any("not confirmed the trend" in x and "crossed above zero" in x for x in v.checked)


@pytest.mark.parametrize("before,last,seen,allowed", [
    ("-1.00", "-0.99", False, True),     # shrinking on the trend's side: tiring, as before
    ("-1.00", "-1.01", False, False),    # growing on the trend's side
    ("0.50", "0.60", False, False),      # above zero and rising, never below zero: not shrinking, not confirmed
    ("0.60", "0.50", False, False),      # above zero and falling, never below zero: not shrinking (not on the trend's side)
    ("0.50", "0.60", True, True),        # above zero, but below zero earlier in the state: past zero, tiring
    ("-0.05", "0.01", True, True),       # a fresh cross from below: tiring
    ("-0.10", "0", False, False),        # exactly zero is on neither side: not shrinking towards it any more
])
def test_the_hourly_cases_for_a_buy_against_a_trend_down(ON, monkeypatch, before, last, seen, allowed):
    monkeypatch.setattr(ef, "hourly_macd", lambda s, st, at: macd_of(before, last))
    monkeypatch.setattr(ef, "five_minute_macd", lambda s, st, at: (None, "no 5-minute candles"))
    monkeypatch.setattr(ef, "hourly_trend_side_since", lambda *a: (seen, "on the trend's side at the 08:00 hourly candle"
                        if seen else "never on the trend's side since the state began at 09:00 UTC"))
    assert ef.check(ON, None, ef_idea(AT - timedelta(hours=5))).allowed is allowed


@pytest.mark.parametrize("before,last,seen,allowed", [
    ("1.00", "0.99", False, True), ("-0.50", "-0.60", False, False), ("-0.50", "-0.60", True, True),
    ("0.05", "-0.01", True, True)])
def test_the_mirror_for_a_sell_against_a_trend_up(ON, monkeypatch, before, last, seen, allowed):
    monkeypatch.setattr(ef, "hourly_macd", lambda s, st, at: macd_of(before, last))
    monkeypatch.setattr(ef, "five_minute_macd", lambda s, st, at: (None, "no 5-minute candles"))
    monkeypatch.setattr(ef, "hourly_trend_side_since", lambda *a: (seen, "x" if seen else "never on the trend's side"))
    assert ef.check(ON, None, ef_idea(AT - timedelta(hours=5), direction=SELL, state_direction="up")).allowed is allowed


def test_the_idea_carries_when_the_analysers_state_began(ON):
    t = END - timedelta(hours=3)
    st = SimpleNamespace(state="trend", direction="down", trend_type="slow grind", since=t)
    c = Candidate(BOLLINGER_BOUNCE, BUY, AT, D("13000"), [])
    assert strategy_check(ON, "GBPUSD", c, st, None, None).state_since == t
    st0 = SimpleNamespace(state="trend", direction="down", trend_type="slow grind")
    assert strategy_check(ON, "GBPUSD", c, st0, None, None).state_since is None
