"""Safety rules 9 (one view at a time) and 11 (one signal, one trade), brought into first-build-plus from production
(owner, 19 November 2026). The tests are main's (tests/technical/test_analyser_control.py, stage 3), here without the
analyser control they sat beside. Made-up ideas; never contacts IG."""

from types import SimpleNamespace

import pytest

from analyser.states import EMERGING
from config.settings_loader import load_settings
from safety.rules import _one_signal, is_reversal
from strategies.common import (ASIAN_RANGE_BREAKOUT, BOLLINGER_BOUNCE, BUY, EMA_PULLBACK, LEVEL_REVERSAL,
                               NEW_YORK_OPEN_REVERSAL, SELL, SESSION_SWEEP)

BASE = load_settings().for_pair("GBPUSD")


class On:
    """The real settings (no .env read) with some switches on."""
    def __init__(self, **switches):
        names = ("slow_grind", "ema_pullback", "bollinger_bounce", "range_trade", "breakout", "level_reversal",
                 "asian_range_breakout", "session_sweep", "new_york_open_reversal")
        self.switches = SimpleNamespace(**({k: True for k in names} | switches))

    def __getattr__(self, name):
        return getattr(BASE, name)


def idea(strategy, direction, state=EMERGING, state_direction="up", context=None):
    return SimpleNamespace(strategy=strategy, direction=direction, state=state, state_direction=state_direction,
                           trend_type=None, context=context or {})


def test_one_signal_one_trade():
    on, off = On(one_signal_one_trade=True), On()
    i = idea(LEVEL_REVERSAL, SELL, context={"signal": "sell 2026-11-17T09:55:00Z"})
    used = {"sell 2026-11-17T09:55:00Z": BOLLINGER_BOUNCE}
    assert _one_signal(on, i, used) == ["same signal already traded by Bollinger bounce"]
    assert _one_signal(off, i, used) == []
    assert _one_signal(on, i, {"buy 2026-11-17T09:55:00Z": BOLLINGER_BOUNCE}) == []   # the other way: another signal
    assert _one_signal(on, idea(EMA_PULLBACK, SELL), used) == []                       # no rejection candle


@pytest.mark.parametrize("strategy,counts_when_on", [(SESSION_SWEEP, True), (NEW_YORK_OPEN_REVERSAL, True),
                                                     (ASIAN_RANGE_BREAKOUT, False), (BOLLINGER_BOUNCE, False),
                                                     (LEVEL_REVERSAL, True)])
def test_stage_3_the_sweep_and_new_york_reversal_come_under_one_view_at_a_time(strategy, counts_when_on):
    against = idea(strategy, SELL)                          # a sell in an emerging trend up
    assert is_reversal(against, On(one_signal_one_trade=True)) is counts_when_on
    assert is_reversal(against, On()) is (strategy == LEVEL_REVERSAL)
    assert is_reversal(idea(strategy, BUY), On(one_signal_one_trade=True)) is False     # with the trend
