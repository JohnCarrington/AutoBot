"""Functional tests for DIRECTION_RULE_SESSIONS (owner, 19 November 2026), with the real settings and the live switches
of 19 November 2026 (research/analyser_control_days.py BASE_SWITCHES, the analyser control, stage 4 and
TREND_IGNORES_HOURLY_READ on), and on the REAL candles in the candle store for Thursday 19 November 2026.

The owner's rule: above the daily pivot (and above the 5-minute 100 EMA) is buy side, below both is sell side. The Asian
range breakout, the session sweep and the New York open reversal now use the bot's EXISTING direction rule
(analyser/direction.py, applied in strategies/common.py), exactly as the strategies that already use it: the same pivot,
the same 100 EMA, the same "no clear direction". The slow grind does not use it (the owner's decision), nor, unchanged
and reported to the owner, the range trade, the Bollinger bounce, the breakout and the level reversal. These tests check
only that the code does what the owner said; they judge nothing on profit.

  a. The switch is on if left out of .env.
  b. Each of the three is refused a buy below the pivot and a sell above it, and a buy or a sell when the rule says no
     clear direction; with the switch off, none of that.
  c. Every other strategy gets exactly the same answer with the switch on and off.
  d. The real 19 November 07:35 Asian range breakout buy (13155: below the pivot 13162.5, above the 100 EMA 13139.2) is
     refused with the switch on and allowed with it off; nothing else changes that morning.
"""

import tempfile
from datetime import date, datetime, timezone
from decimal import Decimal as D
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

import pytest

from analyser.states import DOWN, RANGING, TREND, UP
from config.settings_loader import load_settings
from research.analyser_control_days import UK, ideas_day, settings_with
from strategies.common import (ASIAN_RANGE_BREAKOUT, BOLLINGER_BOUNCE, BREAKOUT, BUY, EMA_PULLBACK, LEVEL_REVERSAL,
                               NEW_YORK_OPEN_REVERSAL, RANGE_TRADE, SELL, SESSION_STRATEGIES, SESSION_SWEEP, SLOW_GRIND,
                               allowed, skips_direction_rule)

BASE = load_settings().for_pair("GBPUSD")
pytestmark = pytest.mark.skipif(not (BASE.candles.folder / "5m").is_dir(),
                                reason="the real candle store is only on the server")

LIVE = {"SCALE_OUT_REVERSAL": "on", "TRAIL_NO_LOSS": "on", "LR_ENTRY_NEAR_LEVEL": "on", "LEVEL_STOPS": "on",
        "TREND_IGNORES_HOURLY_READ": "on"}


def settings(**extra):
    with tempfile.TemporaryDirectory() as tmp:
        return settings_with(True, Path(tmp), **(LIVE | extra))


ON, OFF = settings(DIRECTION_RULE_SESSIONS="on"), settings(DIRECTION_RULE_SESSIONS="off")
PIVOT, EMA = D("13162.5"), D("13139.2")             # Thursday 19 November 2026, 07:35 UK (the trade record)
BELOW, ABOVE, BETWEEN = D("13130"), D("13170"), D("13155")
# Ranging, with no hourly read given: neither the analyser control's state table nor its hourly-ranging rule stops any
# of the three, so only the direction rule can.
QUIET = SimpleNamespace(state=RANGING, direction="none", trend_type=None)


def rule_reasons(s, strategy, direction, price, state=QUIET):
    reasons, _ = allowed(s, strategy, direction, price, state, PIVOT, EMA)
    return [r for r in reasons if r.startswith("the direction rule says")]


def test_the_switch_is_on_if_left_out_and_can_be_switched_off():
    assert settings().switches.direction_rule_sessions is True        # BASE_SWITCHES leave it out
    assert OFF.switches.direction_rule_sessions is False
    assert set(SESSION_STRATEGIES) == {ASIAN_RANGE_BREAKOUT, SESSION_SWEEP, NEW_YORK_OPEN_REVERSAL}
    assert not any(skips_direction_rule(ON, s) for s in SESSION_STRATEGIES)
    assert all(skips_direction_rule(OFF, s) for s in SESSION_STRATEGIES)


@pytest.mark.parametrize("strategy", SESSION_STRATEGIES)
def test_the_session_strategies_are_refused_a_buy_below_the_pivot_and_a_sell_above_it(strategy):
    assert rule_reasons(ON, strategy, BUY, BELOW) == [
        "the direction rule says sell side (price 13130 is below the pivot 13162.5 and below the 5m 100 EMA 13139.2)"]
    assert rule_reasons(ON, strategy, SELL, ABOVE) == [
        "the direction rule says buy side (price 13170 is above the pivot 13162.5 and above the 5m 100 EMA 13139.2)"]
    assert rule_reasons(ON, strategy, BUY, ABOVE) == [] and rule_reasons(ON, strategy, SELL, BELOW) == []


@pytest.mark.parametrize("strategy", SESSION_STRATEGIES)
def test_no_clear_direction_refuses_both_ways_as_for_the_strategies_that_already_use_the_rule(strategy):
    said = ("the direction rule says no clear direction (price 13155 is below the pivot 13162.5 and above the 5m 100 EMA "
            "13139.2: they disagree)")
    assert rule_reasons(ON, strategy, BUY, BETWEEN) == [said] and rule_reasons(ON, strategy, SELL, BETWEEN) == [said]
    trend_up = SimpleNamespace(state=TREND, direction=UP, trend_type="slow grind")
    assert rule_reasons(ON, EMA_PULLBACK, BUY, BETWEEN, trend_up) == [said]          # the same words, the same rule


@pytest.mark.parametrize("strategy", SESSION_STRATEGIES)
def test_with_the_switch_off_the_session_strategies_skip_the_rule_as_before(strategy):
    for direction in (BUY, SELL):
        for price in (BELOW, ABOVE, BETWEEN):
            assert rule_reasons(OFF, strategy, direction, price) == []


@pytest.mark.parametrize("strategy", [SLOW_GRIND, EMA_PULLBACK, RANGE_TRADE, BOLLINGER_BOUNCE, BREAKOUT, LEVEL_REVERSAL])
def test_every_other_strategy_gets_the_same_answer_with_the_switch_on_and_off(strategy):
    states = [QUIET, SimpleNamespace(state=TREND, direction=UP, trend_type="slow grind"),
              SimpleNamespace(state=TREND, direction=DOWN, trend_type="slow grind")]
    for st in states:
        for direction in (BUY, SELL):
            for price in (BELOW, ABOVE, BETWEEN):
                assert allowed(ON, strategy, direction, price, st, PIVOT, EMA) == \
                       allowed(OFF, strategy, direction, price, st, PIVOT, EMA)
    assert skips_direction_rule(ON, strategy) == (strategy != EMA_PULLBACK)       # the slow grind still skips it


# ---- d. the real morning of Thursday 19 November 2026 ------------------------------------------------------------

A, B = datetime(2026, 11, 19, 6, 0, tzinfo=timezone.utc), datetime(2026, 11, 19, 10, 30, tzinfo=timezone.utc)


@lru_cache(maxsize=None)
def thursday(switch: str) -> dict:
    _, ideas, _ = ideas_day(date(2026, 11, 19), True, **LIVE, DIRECTION_RULE_SESSIONS=switch)
    return {(i.time.astimezone(UK).strftime("%H:%M"), i.strategy, i.direction): i for i in ideas if A <= i.time <= B}


def test_the_07_35_asian_range_breakout_buy_is_refused_by_the_direction_rule():
    on, off = thursday("on")[("07:35", ASIAN_RANGE_BREAKOUT, BUY)], thursday("off")[("07:35", ASIAN_RANGE_BREAKOUT, BUY)]
    assert on.entry_price == off.entry_price
    assert on.direction_rule == "no clear direction"
    assert not on.allowed and on.blocked_by.startswith("the direction rule says no clear direction (price ")
    assert "below the pivot 13162.5 and above the 5m 100 EMA" in on.blocked_by
    assert off.allowed


def test_nothing_but_the_three_session_strategies_changes_that_morning():
    key = lambda i: (i.entry_price, i.allowed, i.blocked_by)              # noqa: E731
    on, off = thursday("on"), thursday("off")
    assert set(on) == set(off)
    assert {k: key(v) for k, v in on.items() if k[1] not in SESSION_STRATEGIES} == \
           {k: key(v) for k, v in off.items() if k[1] not in SESSION_STRATEGIES}
