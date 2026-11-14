"""Technical tests for the hourly read (analyser/hourly_read.py; owner, 14 November 2026) and what it allows
(strategies/common.py, check 4), with made-up hourly candles. Prices are the chart (SELL) prices in points
(GBPUSD: 1 point = 1 pip)."""

from datetime import timedelta
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from analyser.hourly_read import RALLY, RANGING, SELL_OFF, HourlyRead, HourlyReader
from analyser.states import DOWN, TREND, UP
from config.settings_loader import load_settings
from prices.model import Candle
from strategies.common import (BOLLINGER_BOUNCE, BREAKOUT, BUY, EMA_PULLBACK, LEVEL_REVERSAL, RANGE_TRADE, SELL,
                               SLOW_GRIND, TREND_STRATEGIES, Candidate, check, hourly_reasons)
from tests.technical.fake_stream import T

START = T(2026, 11, 2, 0, 0)            # Monday 00:00


@pytest.fixture
def S(pretend_switches):
    return load_settings(switches_from=pretend_switches).for_pair("GBPUSD")


def H(i, o, h, l, c):
    o, h, l, c = (D(str(x)) for x in (o, h, l, c))
    t = START + timedelta(hours=i)
    return Candle("1h", t, t + timedelta(hours=1), o + 2, h + 2, l + 2, c + 2, o, h, l, c)


def flat(n, start=0):
    """n quiet hourly candles between 100 and 110."""
    return [H(start + k, 105, 110, 100, 105) for k in range(n)]


def read_after(S, candles):
    return HourlyReader(S, candles).at(candles[-1].end)


def test_the_settings_are_the_owners(S):
    h = S.hourly_read
    assert (h.range_candles, h.break_beyond_pips, h.ranging_after_candles) == (12, 3, 12)


def test_a_close_3_pips_beyond_the_last_12_candles_starts_a_sell_off_or_a_rally(S):
    assert read_after(S, flat(12) + [H(12, 105, 105, 96, 97)]).state == SELL_OFF        # 3 below the low 100
    assert read_after(S, flat(12) + [H(12, 105, 114, 104, 113)]).state == RALLY        # 3 above the high 110


def test_a_close_less_than_3_pips_beyond_or_only_a_wick_is_not_a_break(S):
    assert read_after(S, flat(12) + [H(12, 105, 105, 96, D("97.1"))]).state == RANGING
    assert read_after(S, flat(12) + [H(12, 105, 125, 104, 109)]).state == RANGING     # wick far above, close inside


def test_only_the_12_candles_before_count_for_the_break(S):
    early_low = [H(0, 105, 110, 80, 105)]                                              # 13 candles back: not counted
    r = read_after(S, early_low + flat(12, 1) + [H(13, 105, 105, 96, 97)])
    assert r.state == SELL_OFF and "below the low 100" in r.why


def test_ranging_again_after_12_candles_with_no_new_break(S):
    cs = flat(12) + [H(12, 100, 100, 90, 92)]                                          # sell-off
    cs += [H(13 + k, 92, 95, 89, 92) for k in range(11)]                              # 11 quiet candles after it
    assert read_after(S, cs).state == SELL_OFF
    cs.append(H(24, 92, 95, 89, 92))                                                   # the 12th
    r = read_after(S, cs)
    assert r.state == RANGING
    assert (r.low, r.high) == (D(89), D(95))                                           # the last 12 candles


def test_a_new_break_the_same_way_starts_the_12_again(S):
    cs = flat(12) + [H(12, 100, 100, 90, 92)]
    cs += [H(13 + k, 92, 95, 89, 92) for k in range(6)]
    cs.append(H(19, 92, 92, 80, 82))                                                   # lower again: a new break
    cs += [H(20 + k, 82, 85, 79, 82) for k in range(11)]
    assert read_after(S, cs).state == SELL_OFF
    cs.append(H(31, 82, 85, 79, 82))
    assert read_after(S, cs).state == RANGING


def test_a_break_the_other_way_turns_a_sell_off_into_a_rally(S):
    cs = flat(12) + [H(12, 100, 100, 90, 92), H(13, 92, 116, 92, 115)]                # 3+ above the high 110
    assert read_after(S, cs).state == RALLY


def test_the_read_holds_from_an_hourly_close_until_the_next(S):
    cs = flat(12) + [H(12, 105, 105, 96, 97)]
    r = HourlyReader(S, cs)
    assert r.at(cs[-1].end - timedelta(seconds=1)).state == RANGING                   # the break candle not closed yet
    assert r.at(cs[-1].end).state == SELL_OFF
    assert r.at(cs[-1].end + timedelta(minutes=59)).state == SELL_OFF
    assert r.at(START).state == RANGING and r.at(START).candle is None


# ---- check 4: what the strategies may do -------------------------------------------------------

def hourly(state, low=D(100), high=D(110)):
    return HourlyRead(state, None, low, high, None, "made up")


def cand(strategy, direction):
    return Candidate(strategy, direction, START, D(100), ["made up"])


def st(direction):
    return SimpleNamespace(state=TREND, direction=direction, trend_type="slow grind")


def test_the_trend_strategies_are_the_ema_pullback_slow_grind_and_breakout():
    assert set(TREND_STRATEGIES) == {EMA_PULLBACK, SLOW_GRIND, BREAKOUT}


@pytest.mark.parametrize("strategy", [EMA_PULLBACK, SLOW_GRIND, BREAKOUT])
def test_hourly_ranging_blocks_the_trend_strategies(S, strategy):
    assert hourly_reasons(S, strategy, BUY, hourly(RANGING)) and hourly_reasons(S, strategy, SELL, hourly(RANGING))
    i = check(S, "GBPUSD", cand(strategy, SELL), st(DOWN), D(110), D(110), hourly(RANGING))
    assert not i.allowed
    assert "the hourly chart is ranging (100 to 110)" in i.blocked_by and "at least 3 pips beyond" in i.blocked_by


@pytest.mark.parametrize("strategy", [EMA_PULLBACK, SLOW_GRIND, BREAKOUT])
def test_trend_strategies_trade_only_with_the_hourly(S, strategy):
    assert hourly_reasons(S, strategy, SELL, hourly(SELL_OFF)) == []
    assert hourly_reasons(S, strategy, BUY, hourly(RALLY)) == []
    assert hourly_reasons(S, strategy, BUY, hourly(SELL_OFF)) == [f"the hourly chart is in a sell-off: {strategy} only sells"]
    assert hourly_reasons(S, strategy, SELL, hourly(RALLY)) == [f"the hourly chart is in a rally: {strategy} only buys"]
    no = check(S, "GBPUSD", cand(strategy, BUY), st(UP), D(90), D(90), hourly(SELL_OFF))
    assert not no.allowed and "the hourly chart is in a sell-off" in no.blocked_by
    if strategy != BREAKOUT:                                    # the pretend switches: the breakout is off
        assert check(S, "GBPUSD", cand(strategy, SELL), st(DOWN), D(110), D(110), hourly(SELL_OFF)).allowed
        assert check(S, "GBPUSD", cand(strategy, BUY), st(UP), D(90), D(90), hourly(RALLY)).allowed


def test_the_level_reversal_bounce_and_range_trade_are_not_affected(S):
    from analyser.states import POSSIBLE_REVERSAL, RANGING as RANGING_5M
    for name, s5 in ((LEVEL_REVERSAL, st(DOWN)), (BOLLINGER_BOUNCE, SimpleNamespace(state=POSSIBLE_REVERSAL,
                                                                                   direction=UP, trend_type=None)),
                     (RANGE_TRADE, SimpleNamespace(state=RANGING_5M, direction="none", trend_type=None))):
        for h in (RANGING, SELL_OFF, RALLY):
            for d in (BUY, SELL):
                assert check(S, "GBPUSD", cand(name, d), s5, D(110), D(110), hourly(h)).allowed, (name, h, d)


def test_an_allowed_idea_records_the_hourly_read(S):
    i = check(S, "GBPUSD", cand(EMA_PULLBACK, SELL), st(DOWN), D(110), D(110), hourly(SELL_OFF))
    assert "hourly sell-off: made up" in i.steps[-1]
