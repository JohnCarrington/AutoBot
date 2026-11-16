"""Technical tests for check 6, the trend still going (owner, 16 November 2026; strategies/common.py): with the
switch TREND_STILL_GOING on, the EMA pullback, slow grind and breakout only open a sell if, within the last
trend_still_going.within_candles (12) finished 5-minute candles, price made a new low at least
trend_still_going.new_extreme_pips (5) below the previous low (the last swing low before that candle, with
swing_candles_each_side (1) higher lows on each side); a buy is the mirror. Made-up candles; contacts nobody."""

from datetime import timedelta
from decimal import Decimal as D

import pytest

from analyser.states import DOWN, TREND, UP
from strategies.common import (BOLLINGER_BOUNCE, BREAKOUT, BUY, EMA_PULLBACK, LEVEL_REVERSAL, SELL, SLOW_GRIND,
                               still_going_reasons, check)
from tests.technical.test_strategies import C, EMA100, PIVOT, S, cand, over, state  # noqa: F401  (S: fixture)


def lows(*ls):
    """Candles with these sell lows (highs 2 above, opens and closes in between), oldest first."""
    return [C(i, l + 1, l + 2, l, l + 1) for i, l in enumerate(ls)]


def highs(*hs):
    return [C(i, h - 1, h, h - 2, h - 1) for i, h in enumerate(hs)]


def on(S, **values):
    s = over(S, "switches", trend_still_going=True)
    return over(s, "trend_still_going", **values) if values else s


# swing low 100 at the second candle (101 before, 102 after); then a new low
FIVE_BELOW = lows(101, 100, 102, 99, 95)          # 95: 5 pips below the swing low 100
FOUR_BELOW = lows(101, 100, 102, 99, 96)          # 96: only 4


def test_off_by_default_and_while_off_nothing_changes(S):
    assert S.switches.trend_still_going is False
    assert still_going_reasons(S, EMA_PULLBACK, SELL, FOUR_BELOW) == []


def test_the_settings_are_the_owners_numbers(S):
    t = S.trend_still_going
    assert (t.new_extreme_pips, t.within_candles, t.swing_candles_each_side) == (D(5), 12, 1)


def test_a_new_low_5_pips_below_the_previous_swing_low_allows_a_sell(S):
    assert still_going_reasons(on(S), EMA_PULLBACK, SELL, FIVE_BELOW) == []


def test_only_4_pips_below_refuses_it_and_says_why(S):
    (why,) = still_going_reasons(on(S), EMA_PULLBACK, SELL, FOUR_BELOW)
    assert why.startswith("TREND_STILL_GOING is on and the trend is not still going: no new low at least 5 pips "
                          "below the previous low in the last 12 five-minute candles")
    assert "(the most: 4.0 pips below the swing low 100 of 09:05, at 09:20)" in why


def test_a_buy_is_the_mirror(S):
    s = on(S)
    assert still_going_reasons(s, SLOW_GRIND, BUY, highs(99, 100, 98, 101, 105)) == []
    (why,) = still_going_reasons(s, SLOW_GRIND, BUY, highs(99, 100, 98, 101, 104))
    assert "no new high at least 5 pips above the previous high" in why


def test_the_new_low_must_be_within_the_last_12_candles(S):
    s = on(S)
    flat = lows(*([97] * 11))                      # 11 quiet candles after the new low: it is the 12th from the end
    assert still_going_reasons(s, BREAKOUT, SELL, FIVE_BELOW + flat) == []
    assert still_going_reasons(s, BREAKOUT, SELL, FIVE_BELOW + flat + lows(97)) != []    # now 13th: too old


def test_the_previous_low_is_a_swing_low_with_a_higher_low_each_side(S):
    s = on(S)
    # 100 has 101 before but 100 after: not a swing; the swing low is 103 (104 / 104), so 98 is 5 below it
    assert still_going_reasons(s, EMA_PULLBACK, SELL, lows(104, 103, 104, 101, 100, 100, 98)) == []
    # the swing low is the LAST one before the new low: 101 (102 / 103), so 97 is only 4 below (8 below the older
    # swing low 105 would not count); 101 itself was only 4 below 105
    assert still_going_reasons(s, EMA_PULLBACK, SELL, lows(106, 105, 106, 102, 101, 103, 97)) != []


def test_the_swing_needs_its_candle_after_it_before_the_new_low(S):
    # 100 then straight down: 100 is not a swing (no higher low after it before 94); no swing at all: refused
    assert still_going_reasons(on(S), EMA_PULLBACK, SELL, lows(101, 100, 94)) != []


def test_the_numbers_come_from_the_settings(S):
    assert still_going_reasons(on(S, new_extreme_pips=D(4)), EMA_PULLBACK, SELL, FOUR_BELOW) == []
    assert still_going_reasons(on(S, within_candles=1), EMA_PULLBACK, SELL, FIVE_BELOW + lows(97)) != []
    # two each side: 100 (101 / 102) is not a swing with 2 each side (only one candle before it)
    assert still_going_reasons(on(S, swing_candles_each_side=2), EMA_PULLBACK, SELL, FIVE_BELOW) != []


@pytest.mark.parametrize("strategy", [BOLLINGER_BOUNCE, LEVEL_REVERSAL])
def test_only_the_trend_strategies_are_checked(S, strategy):
    assert still_going_reasons(on(S), strategy, SELL, FOUR_BELOW) == []


def test_the_check_refuses_the_idea_with_the_reason(S):
    s = on(S)
    i = check(s, "GBPUSD", cand(EMA_PULLBACK, SELL), state(TREND, DOWN), PIVOT, EMA100, None, FOUR_BELOW)
    assert not i.allowed and "TREND_STILL_GOING is on" in i.blocked_by
    assert check(s, "GBPUSD", cand(EMA_PULLBACK, SELL), state(TREND, DOWN), PIVOT, EMA100, None, FIVE_BELOW).allowed
    assert check(s, "GBPUSD", cand(EMA_PULLBACK, BUY, 120), state(TREND, UP), PIVOT, EMA100, None, FOUR_BELOW).allowed is False
