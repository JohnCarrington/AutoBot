"""Functional tests for EMA_PULLBACK_NO_HOURLY_GAP_MIN (owner, 25 November 2026; off if left out): while on, the EMA
pullback's hourly check (step 0) ignores the two minimum gaps between the hourly EMAs (hourly_min_gap_fast_mid_pips
0.25, hourly_min_gap_mid_slow_pips 0.20); the order, the 1-hour direction and the 3-hour slope are checked exactly as
before. Off: the gaps are checked as now. Made-up hourly EMAs and candles; contacts nobody."""

from decimal import Decimal as D

from strategies.common import BUY
from strategies.ema_pullback.strategy import EmaPullback
from tests.functional.test_ema_pullback_trend_rules import BACK_RIGHT, PREV, reader_with, settings
from tests.technical.test_strategies import BEFORE, FAST, SLOW, START, TOUCH, C

# a buy: in order (8 > 13 > 20), each higher than an hour before, slopes over 3 hours well above 0.16 an hour, but the
# 13 and 20 EMAs only 0.1 apart (under the 0.20 minimum); the 8 and 13 are 5 apart
NARROW = (13110, 13105, "13104.9")
ENTRY = C(6, 103.5, 109.5, 103.2, 109)          # reaches the 5-candle entry 109


def test_the_switch_is_off_if_left_out_of_env(pretend_switches):
    from config.settings_loader import load_settings
    assert load_settings(switches_from=pretend_switches).switches.ema_pullback_no_hourly_gap_min is False


def ideas(s):
    p, out = EmaPullback(s, reader_with(s, NARROW, PREV, BACK_RIGHT)), []
    for i, c in enumerate(BEFORE + [TOUCH, ENTRY]):
        out += p.on_candle(c, FAST if i >= 4 else D(90), SLOW)
    return p, out


def test_on_a_gap_under_the_minimum_no_longer_blocks_and_the_trade_goes_through(tmp_path, pretend_switches):
    s = settings(tmp_path, pretend_switches, EMA_PULLBACK_NO_HOURLY_GAP_MIN="on")
    t = reader_with(s, NARROW, PREV, BACK_RIGHT).at(START)
    assert (t.direction, t.qualified) == (BUY, True)
    assert "gaps 5.00 and 0.10 pips (not checked: EMA_PULLBACK_NO_HOURLY_GAP_MIN)" in t.why
    p, (x,) = ideas(s)
    assert (x.direction, x.entry_price) == (BUY, D(109))


def test_off_the_same_gap_blocks_as_before(tmp_path, pretend_switches):
    s = settings(tmp_path, pretend_switches, EMA_PULLBACK_NO_HOURLY_GAP_MIN="off")
    t = reader_with(s, NARROW, PREV, BACK_RIGHT).at(START)
    assert (t.direction, t.qualified) == (BUY, False) and "gaps 5.00 and 0.10 pips (min 0.25 and 0.2)" in t.why
    p, out = ideas(s)
    assert out == [] and any("the hourly trend is not qualified" in n[2] for n in p.notes)


def test_on_the_order_1_hour_direction_and_3_hour_slope_are_still_checked(tmp_path, pretend_switches):
    s = settings(tmp_path, pretend_switches, EMA_PULLBACK_NO_HOURLY_GAP_MIN="on")
    assert reader_with(s, (13110, 13104, 13105), PREV, BACK_RIGHT).at(START).direction is None     # out of order
    assert reader_with(s, NARROW, (13111, 13104, 13099), BACK_RIGHT).at(START).direction is None   # 8 fell in the hour
    slow = reader_with(s, NARROW, PREV, (13109.8, 13104.8, 13104.7)).at(START)                    # 3-hour slopes tiny
    assert (slow.direction, slow.qualified) == (BUY, False)
