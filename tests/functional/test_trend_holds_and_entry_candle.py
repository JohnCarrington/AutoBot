"""Functional tests for two switches (owner, 25 November 2026), each off if left out of .env:

  ANALYSER_TREND_HOLDS_TO_100EMA: an emerging trend that started from a breakout is no longer cancelled by 2 closes
  back inside the Bollinger bands; it is cancelled only by one close back past the 5-minute 100 EMA (above it for a
  down trend, below it for an up trend). Every other analyser rule is unchanged, the level-rejection cancel (2 closes
  back beyond the level) included (analyser/states.py).

  EMA_PULLBACK_ENTRY_PULLBACK_CANDLE: once a valid touch candle has formed, the EMA pullback's entry is when a later
  candle trades below the touch candle's low (a sell) or above its high (a buy), in place of 3 pips beyond the last 5
  candles' low / high. The 20-minute expiry, the 21 EMA cancel, the stop and the take profit unchanged
  (strategies/ema_pullback/strategy.py).

For each: a case where it changes the result and one showing off behaves as before. Made-up features and candles;
contacts nobody."""

from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from analyser.states import CONSOLIDATION, DOWN, EMERGING, NONE, UP
from strategies.common import BUY, SELL
from strategies.ema_pullback.strategy import EmaPullback
from tests.functional.test_ema_pullback_trend_rules import settings as ema_settings
from tests.technical.test_market_states import F, breakout_downtrend, level_downtrend, machine, run
from tests.technical.test_market_states import st  # noqa: F401  (the fixture)
from tests.technical.test_strategies import BEFORE, FAST, SLOW, TOUCH, C, Hourly


# ---- ANALYSER_TREND_HOLDS_TO_100EMA -------------------------------------------------------------------------------

class WithSwitch:
    """The test settings with ANALYSER_TREND_HOLDS_TO_100EMA set."""
    def __init__(self, base, on):
        self._base = base
        sw = {k: getattr(base.switches, k) for k in dir(base.switches) if not k.startswith("_")}
        self.switches = SimpleNamespace(**(sw | {"analyser_trend_holds_to_100ema": on}))

    def __getattr__(self, name):
        return getattr(self._base, name)


INSIDE = dict(lower=11640, upper=11660)                  # closes 11641-11659 are back inside the bands


def test_the_two_switches_are_off_if_left_out_of_env(pretend_switches):
    from config.settings_loader import load_settings
    sw = load_settings(switches_from=pretend_switches).switches
    assert (sw.analyser_trend_holds_to_100ema, sw.ema_pullback_entry_pullback_candle) == (False, False)


def test_on_closes_back_inside_the_bands_but_below_the_100_ema_keep_a_breakout_down_trend(st):
    m = breakout_downtrend(WithSwitch(st, True), 11650)
    assert "cancelled only by a close back above the 100 EMA" in " ".join(m.now.evidence)
    # 4 closes in a row back inside the bands, all below the 100 EMA 11670: no change
    assert run(m, [(i, F(i, c=11655, ema100=11670, **INSIDE)) for i in range(1, 5)]) == []
    assert (m.now.state, m.now.direction) == (EMERGING, DOWN)


def test_on_one_close_back_above_the_100_ema_cancels_it(st):
    m = breakout_downtrend(WithSwitch(st, True), 11650)
    assert run(m, [(1, F(1, c=11655, ema100=11670, **INSIDE))]) == []
    (ch,) = run(m, [(2, F(2, c="11670.1", ema100=11670, lower=11640, upper=11680))])     # one close is enough
    assert (ch.state, ch.direction) == (CONSOLIDATION, NONE)
    assert ch.reason == ("the emerging down trend was cancelled: a close back above the 100 EMA 11670.0 "
                         "after the breakout (last 11670.1)")


def test_on_a_close_exactly_on_the_100_ema_is_not_past_it(st):
    m = breakout_downtrend(WithSwitch(st, True), 11650)
    assert run(m, [(1, F(1, c=11670, ema100=11670, lower=11640, upper=11680))]) == []


def test_on_the_up_trend_is_the_mirror_image(st):
    m = machine(WithSwitch(st, True))
    run(m, [(0, F(0, c=11650, lower=11637, upper=11649))])                     # closed above the upper band
    assert (m.now.state, m.now.direction) == (EMERGING, UP)
    assert run(m, [(1, F(1, c=11645, ema100=11630, **INSIDE))]) == []           # inside, above the 100 EMA
    (ch,) = run(m, [(2, F(2, c="11629.9", ema100=11630, lower=11620, upper=11660))])
    assert "a close back below the 100 EMA 11630.0" in ch.reason


def test_on_the_level_rejection_cancel_is_unchanged(st):
    m = level_downtrend(WithSwitch(st, True))                                  # rejected at the pivot 11660
    assert run(m, [(1, F(1, c=11661, ema100=11700))]) == []
    (ch,) = run(m, [(2, F(2, c=11662, ema100=11700))])                        # 2 closes back above the level
    assert "2 closes in a row back above the pivot 11660.0 it was rejected at" in ch.reason


def test_off_2_closes_back_inside_the_bands_cancel_it_as_before(st):
    m = breakout_downtrend(WithSwitch(st, False), 11650)
    assert "2 closes in a row back inside the Bollinger bands" in " ".join(m.now.evidence)
    assert run(m, [(1, F(1, c=11655, ema100=11670, **INSIDE))]) == []
    (ch,) = run(m, [(2, F(2, c=11655, ema100=11670, **INSIDE))])
    assert "2 closes in a row back inside the Bollinger bands after the breakout" in ch.reason


# ---- EMA_PULLBACK_ENTRY_PULLBACK_CANDLE ---------------------------------------------------------------------------
# The made-up buy: the 5 candles before the touch have a highest high of 106 (the old entry 106 + 3 = 109); the touch
# candle TOUCH (high 104.5, low 102.5) reaches the 8 EMA 103 and closes 103.5, above the 21 EMA 98.

def run_pullback(s, candles, hourly=None):
    p, out = EmaPullback(s, hourly or Hourly()), []
    for i, c in enumerate(candles):
        out += p.on_candle(c, FAST if i >= 4 else D(90), SLOW)
    return p, out


@pytest.fixture
def ON(tmp_path, pretend_switches):
    return ema_settings(tmp_path, pretend_switches, EMA_PULLBACK_ENTRY_PULLBACK_CANDLE="on")


@pytest.fixture
def OFF(tmp_path, pretend_switches):
    return ema_settings(tmp_path, pretend_switches, EMA_PULLBACK_ENTRY_PULLBACK_CANDLE="off")


NEXT = C(6, 103.5, 104.6, 103.2, 104.4)          # trades above the touch candle's high 104.5, well short of 109


def test_entry_on_a_buy_opens_when_a_later_candle_trades_above_the_touch_candles_high(ON):
    p, (x,) = run_pullback(ON, BEFORE + [TOUCH, NEXT])
    assert (x.direction, x.entry_price, x.time) == (BUY, D("104.5"), NEXT.start)
    assert "entry when a later candle trades above the touch candle high 104.5" in x.steps[2]


def test_entry_off_the_same_candles_open_nothing_as_before(OFF):
    assert run_pullback(OFF, BEFORE + [TOUCH, NEXT])[1] == []                 # needs 109
    (x,) = run_pullback(OFF, BEFORE + [TOUCH, C(6, 103.5, 109.5, 103.2, 109)])[1]
    assert x.entry_price == D(109)


def test_entry_on_trading_exactly_at_the_touch_high_is_not_above_it(ON):
    assert run_pullback(ON, BEFORE + [TOUCH, C(6, 103.5, 104.5, 103.2, 104)])[1] == []


def test_entry_on_a_candle_opening_above_it_enters_at_its_open(ON):
    (x,) = run_pullback(ON, BEFORE + [TOUCH, C(6, 105, 106, 104.8, 105.5)])[1]
    assert x.entry_price == D(105)


def test_entry_on_the_sell_is_the_mirror_image(ON):
    m = lambda x: 200 - x  # noqa: E731
    candles = BEFORE + [TOUCH, NEXT]
    mirrored = [C(i, m(c.sell_open), m(c.sell_low), m(c.sell_high), m(c.sell_close)) for i, c in enumerate(candles)]
    p = EmaPullback(ON, Hourly(SELL))
    out = []
    for i, c in enumerate(mirrored):
        out += p.on_candle(c, m(FAST) if i >= 4 else D(110), m(SLOW))
    (x,) = out
    assert (x.direction, x.entry_price) == (SELL, D("95.5"))                  # below the touch candle's low 95.5


def test_entry_on_the_expiry_and_the_21_ema_cancel_are_unchanged(ON):
    waits = [C(6 + k, 103.5, 104.4, 103.2, 104) for k in range(3)]            # 5, 10 and 15 minutes: not above
    assert run_pullback(ON, BEFORE + [TOUCH] + waits + [C(9, 104, 110, 104, 109)])[1] == []    # 20 minutes: expired
    assert len(run_pullback(ON, BEFORE + [TOUCH] + waits[:2] + [C(8, 104, 110, 104, 109)])[1]) == 1
    assert run_pullback(ON, BEFORE + [TOUCH, C(6, 103.5, 104, 97, 97.5), NEXT])[1] == []      # closed below the 21
