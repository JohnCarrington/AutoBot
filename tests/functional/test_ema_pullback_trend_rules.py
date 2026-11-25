"""Functional tests for the EMA pullback's trend rules (owner, 25 November 2026), each behind its own switch in .env,
off if left out:

  1. EMA_PULLBACK_TREND_ONLY: the EMA pullback opens only when the analyser says "trend" in the trade's direction;
     "emerging trend" is no longer allowed (strategies/common.py, allowed).
  2. EMA_PULLBACK_SLOPE_DIRECTION: the 3-hour slope check also checks direction: each hourly EMA (8/13/20) higher
     than 3 hours before for a buy, lower for a sell; the size check stays as it is
     (strategies/ema_pullback/strategy.py, HourlyTrendReader).
  3. EMA_PULLBACK_RECHECK_AT_OPEN: the full hourly check (order, 1-hour direction, 3-hour slope) again at the moment
     the trade is about to open, not only at the touch candle; if it fails, the setup is cancelled
     (strategies/ema_pullback/strategy.py, EmaPullback).
  4. EMA_PULLBACK_NO_R3_S3: no new EMA pullback buy when the price is at or above the day's R3, no new sell when it is
     at or below the day's S3, from the bot's daily pivot levels (strategies/entry_filters.py).

For each: a case where it blocks and one where it allows, and off (the default) as before. Real settings
(config/settings.toml); made-up candles. Contacts nobody."""

from datetime import timedelta
from decimal import Decimal as D

import pytest

from analyser.states import DOWN, EMERGING, TREND, UP
from config.settings_loader import load_settings
from levels.current import build as build_levels
from levels.rules import R3, S3
from strategies import entry_filters as ef
from strategies.common import BUY, EMA_PULLBACK, LEVEL_REVERSAL, SELL, Candidate, check
from strategies.ema_pullback.strategy import EmaPullback, HourlyTrend, HourlyTrendReader
from tests.functional.test_entry_filters import AT, TUE_DOWN, down_hours, idea as ef_idea, store_with
from tests.technical.test_strategies import BEFORE, FAST, SLOW, START, TOUCH, C, hourly_candles, state

SWITCHES = ("EMA_PULLBACK_TREND_ONLY", "EMA_PULLBACK_SLOPE_DIRECTION", "EMA_PULLBACK_RECHECK_AT_OPEN",
            "EMA_PULLBACK_NO_R3_S3")


def settings(tmp_path, pretend_switches, **on):
    """The real settings with the tests' pretend switches; the four new switches as given (left out: off). The other
    entry filters are switched off, so only rule 4 is looked at in the entry-filter tests."""
    text = "".join(line + "\n" for line in pretend_switches.read_text().splitlines()
                   if not line.startswith(SWITCHES + ("HOURLY_CONTEXT=", "RSI_STRETCH=", "ENTRY_NEAR_EMA8=")))
    text += "HOURLY_CONTEXT=off\nRSI_STRETCH=off\nENTRY_NEAR_EMA8=off\n"
    text += "".join(f"{k}={v}\n" for k, v in on.items())
    env = tmp_path / ("switches_" + "_".join(f"{k}{v}" for k, v in on.items()) + ".env")
    env.write_text(text)
    return load_settings(switches_from=env).for_pair("GBPUSD")


def test_the_four_switches_are_off_if_left_out_of_env(pretend_switches):
    sw = load_settings(switches_from=pretend_switches).switches
    assert (sw.ema_pullback_trend_only, sw.ema_pullback_slope_direction, sw.ema_pullback_recheck_at_open,
            sw.ema_pullback_no_r3_s3) == (False, False, False, False)


# ---- 1. EMA_PULLBACK_TREND_ONLY -------------------------------------------------------------------------------------

def ema_idea(s, st, direction=SELL, price=100):
    # pivot and 100 EMA above a sell at 100 and below a buy at 120, so the direction rule allows either
    return check(s, "GBPUSD", Candidate(EMA_PULLBACK, direction, START, D(price), ["made up"]), st,
                 D(110), D(110))


def test_1_on_an_emerging_trend_no_longer_allows_the_ema_pullback(tmp_path, pretend_switches):
    s = settings(tmp_path, pretend_switches, EMA_PULLBACK_TREND_ONLY="on")
    x = ema_idea(s, state(EMERGING, DOWN))
    assert not x.allowed
    assert x.blocked_by == ("the analyser's state is emerging trend, which does not allow EMA pullback "
                            "(EMA_PULLBACK_TREND_ONLY: trend only)")
    assert not ema_idea(s, state(EMERGING, UP), BUY, 120).allowed


def test_1_on_a_trend_in_the_trades_direction_still_allows_it_and_not_against_it(tmp_path, pretend_switches):
    s = settings(tmp_path, pretend_switches, EMA_PULLBACK_TREND_ONLY="on")
    assert ema_idea(s, state(TREND, DOWN, "slow grind")).allowed
    assert ema_idea(s, state(TREND, UP, "strong push"), BUY, 120).allowed
    assert not ema_idea(s, state(TREND, UP, "slow grind")).allowed                 # a sell in a trend up: as before


def test_1_off_an_emerging_trend_allows_it_as_before(tmp_path, pretend_switches):
    s = settings(tmp_path, pretend_switches, EMA_PULLBACK_TREND_ONLY="off")
    assert ema_idea(s, state(EMERGING, DOWN)).allowed


def test_1_changes_no_other_strategy(tmp_path, pretend_switches):
    on = settings(tmp_path, pretend_switches, EMA_PULLBACK_TREND_ONLY="on")
    c = Candidate(LEVEL_REVERSAL, SELL, START, D(100), ["made up"])
    assert check(on, "GBPUSD", c, state(EMERGING, DOWN), D(110), D(110)).allowed


# ---- 2. EMA_PULLBACK_SLOPE_DIRECTION --------------------------------------------------------------------------------

def reader_with(s, now, prev, back):
    """A reader whose 8/13/20 EMAs are made up at three hourly candles: the last finished (now), the one before
    (prev) and 3 before (back). Each argument: (8, 13, 20)."""
    r = HourlyTrendReader(s, hourly_candles(D(2)))
    done = [c for c in r.candles if c.end <= START]
    for key, vals in ((done[-1].start, now), (done[-2].start, prev), (done[-4].start, back)):
        r.f[key], r.m[key], r.sl[key] = (D(str(v)) for v in vals)
    return r


# a buy: in order (8 > 13 > 20), each higher than an hour before; slopes over 3 hours at least 0.16 an hour in size.
# BACK_WRONG: the 20 EMA 3 hours ago was 13101, so now (13100) it is LOWER than 3 hours before (slope -0.33 an hour).
NOW, PREV = (13110, 13105, 13100), (13108, 13104, 13099)
BACK_RIGHT, BACK_WRONG = (13100, 13100, 13098), (13100, 13100, 13101)


def test_2_on_a_buy_whose_20_ema_is_lower_than_3_hours_before_is_not_qualified(tmp_path, pretend_switches):
    s = settings(tmp_path, pretend_switches, EMA_PULLBACK_SLOPE_DIRECTION="on")
    t = reader_with(s, NOW, PREV, BACK_WRONG).at(START)
    assert (t.direction, t.qualified) == (BUY, False)
    assert "EMA_PULLBACK_SLOPE_DIRECTION: the 20 EMA not higher than 3 hours before" in t.why


def test_2_on_a_buy_with_every_ema_higher_than_3_hours_before_is_qualified(tmp_path, pretend_switches):
    s = settings(tmp_path, pretend_switches, EMA_PULLBACK_SLOPE_DIRECTION="on")
    t = reader_with(s, NOW, PREV, BACK_RIGHT).at(START)
    assert (t.direction, t.qualified) == (BUY, True) and "each higher than 3 hours before" in t.why


def test_2_on_the_sell_is_the_mirror_image(tmp_path, pretend_switches):
    s = settings(tmp_path, pretend_switches, EMA_PULLBACK_SLOPE_DIRECTION="on")
    m = lambda v: tuple(26200 - x for x in v)  # noqa: E731
    assert reader_with(s, m(NOW), m(PREV), m(BACK_RIGHT)).at(START).qualified
    t = reader_with(s, m(NOW), m(PREV), m(BACK_WRONG)).at(START)
    assert (t.direction, t.qualified) == (SELL, False) and "the 20 EMA not lower than 3 hours before" in t.why


def test_2_off_the_size_check_alone_as_before(tmp_path, pretend_switches):
    s = settings(tmp_path, pretend_switches, EMA_PULLBACK_SLOPE_DIRECTION="off")
    t = reader_with(s, NOW, PREV, BACK_WRONG).at(START)
    assert (t.direction, t.qualified) == (BUY, True)                     # |13100 - 13101| / 3 = 0.33 >= 0.16


def test_2_on_the_size_check_is_kept(tmp_path, pretend_switches):
    s = settings(tmp_path, pretend_switches, EMA_PULLBACK_SLOPE_DIRECTION="on")
    small = (13110, 13105, 13099.8)                                     # 20 EMA: +0.2 in 3 hours, 0.07 an hour
    assert not reader_with(s, NOW, PREV, small).at(START).qualified


# ---- 3. EMA_PULLBACK_RECHECK_AT_OPEN --------------------------------------------------------------------------------

class HourlyByTime:
    """A made-up hourly reading: qualified for a buy up to `until`, then the given reading."""
    def __init__(self, until, later):
        self.until, self.later = until, later

    def at(self, t):
        return HourlyTrend(BUY, True, "made-up hourly trend") if t < self.until else self.later


ENTRY = C(6, 103.5, 109.5, 103.2, 109)          # reaches the entry 109 (106 + 3)


def run(s, hourly, candles):
    p, out = EmaPullback(s, hourly), []
    for i, c in enumerate(candles):
        out += p.on_candle(c, FAST if i >= 4 else D(90), SLOW)
    return p, out


def test_3_on_the_hourly_check_failing_at_the_open_cancels_the_setup(tmp_path, pretend_switches):
    s = settings(tmp_path, pretend_switches, EMA_PULLBACK_RECHECK_AT_OPEN="on")
    later = HourlyTrend(None, False, "hourly EMAs not in order and all moving one way (made up)")
    hourly = HourlyByTime(ENTRY.start, later)                         # qualified at the touch, not at the open
    p, out = run(s, hourly, BEFORE + [TOUCH, ENTRY, C(7, 109, 112, 108, 111)])
    assert out == [] and p.setups == []
    (note,) = [n for n in p.notes if "check at the open failed" in n[2]]
    assert note[0] == ENTRY.start and "cancelled (EMA_PULLBACK_RECHECK_AT_OPEN)" in note[2]


def test_3_on_qualified_again_at_the_open_the_trade_opens(tmp_path, pretend_switches):
    s = settings(tmp_path, pretend_switches, EMA_PULLBACK_RECHECK_AT_OPEN="on")
    hourly = HourlyByTime(ENTRY.start, HourlyTrend(BUY, True, "still qualified (made up)"))
    p, (x,) = run(s, hourly, BEFORE + [TOUCH, ENTRY])
    assert (x.direction, x.entry_price, x.time) == (BUY, D(109), ENTRY.start)
    assert x.steps[-1] == "hourly check again at the open (EMA_PULLBACK_RECHECK_AT_OPEN): still qualified (made up)"


def test_3_on_a_reading_the_other_way_at_the_open_also_cancels(tmp_path, pretend_switches):
    s = settings(tmp_path, pretend_switches, EMA_PULLBACK_RECHECK_AT_OPEN="on")
    hourly = HourlyByTime(ENTRY.start, HourlyTrend(SELL, True, "falling (made up)"))
    assert run(s, hourly, BEFORE + [TOUCH, ENTRY])[1] == []


def test_3_off_checked_only_at_the_touch_as_before(tmp_path, pretend_switches):
    s = settings(tmp_path, pretend_switches, EMA_PULLBACK_RECHECK_AT_OPEN="off")
    hourly = HourlyByTime(ENTRY.start, HourlyTrend(None, False, "not in order (made up)"))
    p, (x,) = run(s, hourly, BEFORE + [TOUCH, ENTRY])
    assert x.entry_price == D(109)                    # opened although the reading at the open is not qualified
    assert not any("again at the open" in step for step in x.steps)


# ---- 4. EMA_PULLBACK_NO_R3_S3 ---------------------------------------------------------------------------------------

@pytest.fixture
def STORE(tmp_path):
    return store_with(tmp_path, down_hours(), TUE_DOWN, name="r3s3")


def level(s, store, name):
    (p,) = [lv.price for lv in build_levels(s, store, AT).levels if lv.type == name]
    return p


def test_4_the_made_up_day_gives_these_r3_and_s3(tmp_path, pretend_switches, STORE):
    s = settings(tmp_path, pretend_switches, EMA_PULLBACK_NO_R3_S3="on")
    # Tuesday H 13240, L 13100, C 13150: P 13163.3; R3 = H + 2(P - L) = 13366.7; S3 = L - 2(H - P) = 12946.7
    assert level(s, STORE, R3) == D("13366.7") and level(s, STORE, S3) == D("12946.7")


def test_4_on_a_buy_at_or_above_r3_is_refused(tmp_path, pretend_switches, STORE):
    s = settings(tmp_path, pretend_switches, EMA_PULLBACK_NO_R3_S3="on")
    for price in ("13366.7", "13370"):
        v = ef.check(s, STORE, ef_idea(EMA_PULLBACK, BUY, price))
        assert not v.allowed and v.rule == ef.EMA_PULLBACK_NO_R3_S3, price
        assert v.details["level"] == "R3" and v.details["level_price"] == "13366.7"
    assert "no EMA pullback BUY at or above the day's R3" in v.why and "3.3 pips above" in v.why


def test_4_on_a_buy_below_r3_is_allowed(tmp_path, pretend_switches, STORE):
    s = settings(tmp_path, pretend_switches, EMA_PULLBACK_NO_R3_S3="on")
    v = ef.check(s, STORE, ef_idea(EMA_PULLBACK, BUY, "13366.6"))
    assert v.allowed and any("0.1 pips below the day's R3 13366.7: allowed" in x for x in v.checked)


def test_4_on_a_sell_at_or_below_s3_is_refused_and_above_it_allowed(tmp_path, pretend_switches, STORE):
    s = settings(tmp_path, pretend_switches, EMA_PULLBACK_NO_R3_S3="on")
    for price in ("12946.7", "12940"):
        v = ef.check(s, STORE, ef_idea(EMA_PULLBACK, SELL, price))
        assert not v.allowed and v.details["level"] == "S3", price
    assert ef.check(s, STORE, ef_idea(EMA_PULLBACK, SELL, "12946.8")).allowed


def test_4_on_a_buy_near_s3_and_a_sell_near_r3_are_not_affected(tmp_path, pretend_switches, STORE):
    s = settings(tmp_path, pretend_switches, EMA_PULLBACK_NO_R3_S3="on")
    assert ef.check(s, STORE, ef_idea(EMA_PULLBACK, BUY, "12940")).allowed
    assert ef.check(s, STORE, ef_idea(EMA_PULLBACK, SELL, "13370")).allowed


def test_4_off_a_buy_above_r3_is_allowed_as_before(tmp_path, pretend_switches, STORE):
    s = settings(tmp_path, pretend_switches, EMA_PULLBACK_NO_R3_S3="off")
    v = ef.check(s, STORE, ef_idea(EMA_PULLBACK, BUY, "13370"))
    assert v.allowed and not any("R3" in x for x in v.checked)


def test_4_changes_no_other_strategy(tmp_path, pretend_switches, STORE):
    s = settings(tmp_path, pretend_switches, EMA_PULLBACK_NO_R3_S3="on")
    assert ef.check(s, STORE, ef_idea(LEVEL_REVERSAL, BUY, "13370")).allowed
