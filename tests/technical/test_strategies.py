"""Technical tests for the four strategies (design sections 2.2, 2.3 and 3),
with made-up candles. Ideas only: nothing here contacts IG or trades.
Prices are the chart (SELL) prices in points (GBPUSD: 1 point = 1 pip); the
made-up candles' buy prices are a normal 1.5 above."""

from datetime import timedelta
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from analyser.states import CONSOLIDATION, DOWN, EMERGING, NONE, POSSIBLE_REVERSAL, RANGING, TREND, UP
from config.settings_loader import load_settings
from prices.indicators import Band
from prices.model import Candle
from rejection.watch import RejectionWatcher
from strategies import replay as replay_mod
from strategies.bollinger_bounce.strategy import candidates as bounce_candidates
from strategies.common import (BOLLINGER_BOUNCE, BUY, EMA_PULLBACK, RANGE_TRADE, SELL, SLOW_GRIND, Candidate,
                               check)
from strategies.ema_pullback.strategy import EmaPullback, HourlyTrend, HourlyTrendReader
from strategies.range_trade.strategy import candidates as range_candidates
from strategies.slow_grind.strategy import SlowGrind
from tests.technical.fake_stream import T

START = T(2026, 11, 4, 9, 0)        # Wednesday 09:00 UK (GMT)
SPREAD = D("1.5")


@pytest.fixture
def S(pretend_switches):
    """The real settings for GBPUSD, with the pretend switches (every strategy on)."""
    return load_settings(switches_from=pretend_switches).for_pair("GBPUSD")


def changed(s, section, **values):
    """The settings with some values of one section changed."""
    base = {k: v for k, v in vars(getattr(s, section)).items() if not k.startswith("_")}
    base.update(values)
    return SimpleNamespace(**{name: getattr(s, name) for name in
                              ("chart", "market", "slow_grind", "ema_pullback", "switches", "bounce",
                               "range_trade", "rejection", "reversal_watch", "levels")} | {section: SimpleNamespace(**base)})


def C(i, o, h, l, c, start=START, tf="5m", minutes=5):
    o, h, l, c = (D(str(x)) for x in (o, h, l, c))
    t = start + timedelta(minutes=minutes * i)
    return Candle(tf, t, t + timedelta(minutes=minutes), o + SPREAD, h + SPREAD, l + SPREAD, c + SPREAD, o, h, l, c)


def state(name, direction=NONE, kind=None):
    return SimpleNamespace(state=name, direction=direction, trend_type=kind)


def cand(strategy, direction, price=100):
    return Candidate(strategy, direction, START, D(price), ["made up"])


# ---- the checks: switch, state (2.2), direction rule (2.3) -----------------------------------

PIVOT, EMA100 = D(110), D(110)          # a price of 100 is below both: sell side; 120 above both: buy side


def test_an_allowed_idea_records_everything(S):
    i = check(S, "GBPUSD", cand(SLOW_GRIND, SELL), state(TREND, DOWN, "slow grind"), PIVOT, EMA100)
    assert i.allowed and i.blocked_by == ""
    d = i.as_dict()
    assert {k: d[k] for k in ("pair", "strategy", "direction", "time_utc", "entry_price", "state",
                              "state_direction", "trend_type", "direction_rule")} == {
        "pair": "GBPUSD", "strategy": "slow grind", "direction": "sell", "time_utc": "2026-11-04T09:00:00Z",
        "entry_price": "100", "state": "trend", "state_direction": "down", "trend_type": "slow grind",
        "direction_rule": "sell side"}
    assert d["steps"][0] == "made up" and d["steps"][-1].startswith("allowed at entry: slow grind in a trend down")


def test_a_strategy_switched_off_has_no_ideas(S):
    s = changed(S, "switches", slow_grind=False)
    i = check(s, "GBPUSD", cand(SLOW_GRIND, SELL), state(TREND, DOWN), PIVOT, EMA100)
    assert not i.allowed and "STRATEGY_SLOW_GRIND is off" in i.blocked_by
    assert check(s, "GBPUSD", cand(EMA_PULLBACK, SELL), state(TREND, DOWN), PIVOT, EMA100).allowed


# Section 2.2, every state against every strategy (a sell, with the state's direction down)
@pytest.mark.parametrize("st,allowed", [
    (RANGING, {RANGE_TRADE, BOLLINGER_BOUNCE}),
    (EMERGING, {SLOW_GRIND, EMA_PULLBACK, BOLLINGER_BOUNCE}),
    (TREND, {SLOW_GRIND, EMA_PULLBACK, BOLLINGER_BOUNCE}),
    (POSSIBLE_REVERSAL, {BOLLINGER_BOUNCE}),
    (CONSOLIDATION, set()),
])
def test_which_states_allow_which_strategies(S, st, allowed):
    for name in (SLOW_GRIND, EMA_PULLBACK, BOLLINGER_BOUNCE, RANGE_TRADE):
        i = check(S, "GBPUSD", cand(name, SELL), state(st, DOWN), PIVOT, EMA100)
        assert i.allowed == (name in allowed), (st, name, i.blocked_by)


@pytest.mark.parametrize("st", [EMERGING, TREND])
@pytest.mark.parametrize("name", [SLOW_GRIND, EMA_PULLBACK, BOLLINGER_BOUNCE])
def test_in_a_trend_only_the_trends_direction(S, name, st):
    assert check(S, "GBPUSD", cand(name, SELL), state(st, DOWN), PIVOT, EMA100).allowed
    against = check(S, "GBPUSD", cand(name, BUY, 120), state(st, DOWN), PIVOT, EMA100)
    assert not against.allowed and "only in the trend's direction" in against.blocked_by
    assert check(S, "GBPUSD", cand(name, BUY, 120), state(st, UP), PIVOT, EMA100).allowed


def test_a_bounce_when_ranging_may_go_either_way(S):
    for d, price in ((BUY, 120), (SELL, 100)):
        assert check(S, "GBPUSD", cand(BOLLINGER_BOUNCE, d, price), state(RANGING), PIVOT, EMA100).allowed


def test_a_bounce_when_ranging_still_needs_the_direction_rule(S):
    i = check(S, "GBPUSD", cand(BOLLINGER_BOUNCE, BUY, 100), state(RANGING), PIVOT, EMA100)
    assert not i.allowed and "the direction rule says sell side" in i.blocked_by


def test_a_bounce_in_consolidation_is_still_not_allowed(S):
    i = check(S, "GBPUSD", cand(BOLLINGER_BOUNCE, SELL, 100), state(CONSOLIDATION), PIVOT, EMA100)
    assert not i.allowed and "does not allow Bollinger bounce" in i.blocked_by


def test_the_ema_pullback_has_its_own_stop_loss(S):
    from strategies.common import stop_loss_pips
    assert stop_loss_pips(S, EMA_PULLBACK) == 12
    for name in (SLOW_GRIND, BOLLINGER_BOUNCE, RANGE_TRADE):
        assert stop_loss_pips(S, name) == 6


def test_a_bounce_in_a_possible_reversal_may_go_either_way(S):
    for d, price in ((BUY, 120), (SELL, 100)):
        assert check(S, "GBPUSD", cand(BOLLINGER_BOUNCE, d, price), state(POSSIBLE_REVERSAL, UP), PIVOT, EMA100).allowed


def test_range_trade_both_ways_when_ranging(S):
    for d, price in ((BUY, 120), (SELL, 100)):
        assert check(S, "GBPUSD", cand(RANGE_TRADE, d, price), state(RANGING), PIVOT, EMA100).allowed


@pytest.mark.parametrize("price,pivot,ema100,buy_ok,sell_ok,said", [
    (120, 110, 110, True, False, "buy side"),
    (100, 110, 110, False, True, "sell side"),
    (105, 100, 110, False, False, "no clear direction"),     # above the pivot, below the 100 EMA
    (105, 110, 100, False, False, "no clear direction"),
    (110, 110, 100, False, False, "no clear direction"),     # exactly on the pivot
    (100, None, 110, False, False, "no clear direction"),    # no pivot
    (100, 110, None, False, False, "no clear direction"),    # no 100 EMA
])
@pytest.mark.parametrize("name", [SLOW_GRIND, EMA_PULLBACK, BOLLINGER_BOUNCE])
def test_the_direction_rule_uses_the_entry_price(S, name, price, pivot, ema100, buy_ok, sell_ok, said):
    piv = D(pivot) if pivot is not None else None
    e = D(ema100) if ema100 is not None else None
    b = check(S, "GBPUSD", cand(name, BUY, price), state(TREND, UP), piv, e)
    s = check(S, "GBPUSD", cand(name, SELL, price), state(TREND, DOWN), piv, e)
    assert (b.allowed, s.allowed, b.direction_rule) == (buy_ok, sell_ok, said)
    if not buy_ok:
        assert "the direction rule says" in b.blocked_by


@pytest.mark.parametrize("price", [100, 105, 120])
def test_the_direction_rule_does_not_apply_to_the_range_trade(S, price):
    for d in (BUY, SELL):
        i = check(S, "GBPUSD", cand(RANGE_TRADE, d, price), state(RANGING), PIVOT, EMA100)
        assert i.allowed and "does not apply to range trade" in i.steps[-1]
    assert check(S, "GBPUSD", cand(RANGE_TRADE, BUY, 100), state(RANGING), PIVOT, EMA100).direction_rule == "sell side"


@pytest.mark.parametrize("price", [100, 105, 120])
def test_the_direction_rule_does_not_apply_to_a_bounce_in_a_possible_reversal(S, price):
    for d in (BUY, SELL):
        i = check(S, "GBPUSD", cand(BOLLINGER_BOUNCE, d, price), state(POSSIBLE_REVERSAL, UP), PIVOT, EMA100)
        assert i.allowed and "does not apply to Bollinger bounce in a possible reversal" in i.steps[-1]


@pytest.mark.parametrize("st", [EMERGING, TREND])
def test_the_direction_rule_still_applies_to_a_bounce_in_a_trend(S, st):
    i = check(S, "GBPUSD", cand(BOLLINGER_BOUNCE, BUY, 100), state(st, UP), PIVOT, EMA100)
    assert not i.allowed and "the direction rule says sell side" in i.blocked_by


def test_the_exceptions_do_not_lift_the_other_checks(S):
    s = changed(S, "switches", range_trade=False)
    assert "STRATEGY_RANGE_TRADE is off" in check(s, "GBPUSD", cand(RANGE_TRADE, BUY, 100), state(RANGING),
                                                  PIVOT, EMA100).blocked_by
    i = check(S, "GBPUSD", cand(RANGE_TRADE, BUY, 100), state(TREND, UP), PIVOT, EMA100)
    assert not i.allowed and "does not allow range trade" in i.blocked_by and "direction rule" not in i.blocked_by


def test_every_reason_for_blocking_is_given(S):
    s = changed(S, "switches", ema_pullback=False)
    i = check(s, "GBPUSD", cand(EMA_PULLBACK, BUY, 100), state(CONSOLIDATION), PIVOT, EMA100)
    assert i.blocked_by.count(";") == 2 and "consolidation" in i.blocked_by


# ---- 3.1 slow grind (rules 2-4; rule 1 removed by the owner) ---------------------------------

EMA21 = D(120)          # above every made-up price: closes stay below it


def grind(s, candles, ema=EMA21):
    g = SlowGrind(s)
    return [(c, x) for c in candles for x in g.on_candle(c, ema)]


PAUSE = [C(0, 105, 106, 100, 101),         # the first candle watched: the reference, low 100
         C(1, 101, 103, 100.5, 102),       # 1 in a row: no new low, closes below the EMA
         C(2, 102, 103, 101, 101.5),       # 2
         C(3, 101.5, 102.5, 100.2, 102)]   # 3: a pause; its lowest point 100.2
BREAK = C(4, 102, 102, 100.1, 100.5)       # goes below 100.2 (not below the reference 100)


def test_slow_grind_sell_opens_below_the_lowest_point_of_the_pause(S):
    (c, x), = grind(S, PAUSE + [BREAK])
    assert (x.strategy, x.direction, x.entry_price, x.time) == (SLOW_GRIND, SELL, D("100.2"), BREAK.start)
    assert "the last low made: 100" in x.steps[0] and "a pause: 3 candles in a row" in x.steps[1]
    assert "its lowest point 100.2" in x.steps[1] and "broke below" in x.steps[2]


def test_slow_grind_a_candle_opening_below_it_enters_at_its_open(S):
    (_, x), = grind(S, PAUSE + [C(4, 99, 99.5, 98, 98.5)])
    assert x.entry_price == D(99)


def test_slow_grind_needs_three_candles_in_a_row(S):
    assert grind(S, PAUSE[:3] + [C(3, 101.5, 102, 99, 99.5)]) == []        # a new low after 2: no pause


def test_slow_grind_the_pause_length_is_a_setting(S):
    s = changed(S, "slow_grind", min_pause_candles=4)
    assert grind(s, PAUSE + [C(4, 102, 102, 100.3, 101)]) == []
    assert [x.entry_price for _, x in grind(s, PAUSE + [C(4, 102, 102, 100.3, 101), BREAK])] == [D("100.2")]


def test_slow_grind_no_colour_or_size_test(S):
    greens = [C(0, 99, 106, 100, 101), C(1, "100.3", "100.7", "100.2", "100.6"),    # every candle green, tiny
              C(2, "100.4", "100.8", "100.3", "100.7"), C(3, "100.5", "100.9", "100.4", "100.8"),
              C(4, "100.5", "100.5", "99.9", "100")]
    assert [x.entry_price for _, x in grind(S, greens)] == [D("100.2")]


def test_slow_grind_a_close_above_the_21_ema_cancels_and_the_next_candle_is_the_reference(S):
    g, out = SlowGrind(S), []
    for c, e in zip(PAUSE + [BREAK], [EMA21] * 3 + [D(101), EMA21]):       # candle 3 closes 102, above 101
        out += g.on_candle(c, e)
    assert out == [] and g.watch[SELL].ref is BREAK and g.watch[SELL].row == []


def test_slow_grind_a_new_low_before_the_pause_counts_is_the_next_reference(S):
    candles = PAUSE[:2] + [C(2, 102, 102.5, 99.5, 101),     # a new low 99.5: the row starts again from here
                           C(3, 101, 102, 100, 101.5), C(4, 101.5, 102, 100.5, 101), C(5, 101, 101.8, 99.8, 101.2),
                           C(6, 101.2, 101.2, 99.6, 99.7)]
    assert [x.entry_price for _, x in grind(S, candles)] == [D("99.8")]


def test_slow_grind_a_close_exactly_on_the_ema_starts_the_row_again(S):
    g, out = SlowGrind(S), []
    for c, e in zip(PAUSE + [BREAK], [EMA21, EMA21, D("101.5"), EMA21, EMA21]):   # candle 2 closes on it
        out += g.on_candle(c, e)
    assert out == []


def test_slow_grind_one_row_at_a_time_so_one_idea(S):
    assert len(grind(S, PAUSE + [BREAK])) == 1


def test_slow_grind_the_breaking_candle_is_the_next_reference(S):
    after = [C(5 + k, 100.5, 101, 100.2, 100.6) for k in range(3)] + [C(8, 100.6, 100.6, 100, 100.1)]
    assert [x.entry_price for _, x in grind(S, PAUSE + [BREAK] + after)] == [D("100.2"), D("100.2")]


def test_slow_grind_no_time_limit(S):
    waiting = [C(4 + k, 101, 102, 100.3, 101.5) for k in range(30)]
    assert [x.entry_price for _, x in grind(S, PAUSE + waiting + [C(34, 101, 101, 99, 99.5)])] == [D("100.2")]


def test_slow_grind_buy_is_the_mirror_image(S):
    m = lambda x: 200 - x  # noqa: E731     (a mirror: highs become lows)
    mirrored = [C(i, m(c.sell_open), m(c.sell_low), m(c.sell_high), m(c.sell_close))
                for i, c in enumerate(PAUSE + [BREAK])]
    (_, x), = grind(S, mirrored, ema=D(80))
    assert (x.direction, x.entry_price) == (BUY, D("99.8"))


# ---- 3.2 EMA pullback -----------------------------------------------------------------------

class Hourly:
    def __init__(self, direction=BUY, qualified=True):
        self.t = HourlyTrend(direction, qualified, "made-up hourly trend")

    def at(self, t):
        return self.t


BEFORE = [C(i, 100 + i, 102 + i, 99 + i, 101 + i) for i in range(5)]   # highest high 106 (candle 4)
FAST, SLOW = D(103), D(98)
TOUCH = C(5, 104, 104.5, 102.5, 103.5)          # the low reaches the 8 EMA 103; closes above the 21 EMA 98


def pullback(s, candles, hourly=None, fast=FAST, slow=SLOW, early=D(90)):
    """The 8 EMA is `early` (far from price) until candle 4, so no earlier candle is a touch.
    Later made-up candles keep their lows above 103 unless they are meant to touch."""
    p, out = EmaPullback(s, hourly or Hourly()), []
    for i, c in enumerate(candles):
        out += p.on_candle(c, fast if i >= 4 else early, slow)
    return out


def test_ema_pullback_buy_entry_is_3_pips_above_the_five_highs_before_the_touch(S):
    (x,) = pullback(S, BEFORE + [TOUCH, C(6, 103.5, 109.5, 103.2, 109)])
    assert (x.strategy, x.direction, x.entry_price, x.time) == (EMA_PULLBACK, BUY, D(109), C(6, 0, 0, 0, 0).start)
    assert x.steps[0].startswith("step 0") and "dropped to the 5-minute 8 EMA 103" in x.steps[1]
    assert x.steps[2].startswith("entry 109: 3 pips above the highest high of the 5 candles before the touch candle")


def test_ema_pullback_entry_uses_the_five_candles_immediately_before_the_touch_candle(S):
    candles = BEFORE + [C(5, 104, 120, 97, 97.5),          # reaches the 8 EMA but closes below the 21: no setup
                        C(6, 99, 104, 98.5, 103),           # the touch candle
                        C(7, 103, 124, 103.2, 123)]
    (x,) = pullback(S, candles)
    assert x.entry_price == D(123)                        # candles 1-5: highest high 120 (candle 5), + 3


def test_ema_pullback_price_may_cross_the_8_and_13_ema(S):
    touch = C(5, 104, 104.5, 99, 101)
    assert [x.entry_price for x in pullback(S, BEFORE + [touch, C(6, 101, 110, 103.2, 109)])] == [D(109)]


def test_ema_pullback_needs_the_touch(S):
    assert pullback(S, BEFORE + [C(5, 106, 107, 103.5, 106), C(6, 106, 110, 105, 109)]) == []


def test_ema_pullback_a_close_below_the_21_ema_cancels(S):
    assert pullback(S, BEFORE + [C(5, 104, 104.5, 97, 97.5), C(6, 97.5, 110, 98.2, 109)]) == []   # the touch candle
    assert pullback(S, BEFORE + [TOUCH, C(6, 103.5, 104, 103.2, 97.5), C(7, 97.5, 110, 103.2, 109)]) == []


def test_ema_pullback_expires_after_20_minutes(S):
    waits = [C(6 + k, 103.5, 105, 103.2, 104) for k in range(3)]       # 5, 10 and 15 minutes after the touch
    assert len(pullback(S, BEFORE + [TOUCH] + waits[:2] + [C(8, 104, 110, 104, 109)])) == 1   # 15 minutes: in time
    assert pullback(S, BEFORE + [TOUCH] + waits + [C(9, 104, 110, 104, 109)]) == []           # 20 minutes: expired


def test_ema_pullback_expiry_and_entry_are_settings(S):
    s = changed(S, "ema_pullback", setup_expires_after_minutes=30, entry_beyond_pips=1, entry_lookback_candles=2)
    waits = [C(6 + k, 103.5, 105, 103.2, 104) for k in range(3)]
    (x,) = pullback(s, BEFORE + [TOUCH] + waits + [C(9, 104, 110, 104, 109)])
    assert x.entry_price == D(107)                  # 1 pip above the highest of the last 2 (106)


def test_ema_pullback_a_candle_opening_past_the_entry_enters_at_its_open(S):
    (x,) = pullback(S, BEFORE + [TOUCH, C(6, 110, 111, 109.5, 110.5)])
    assert x.entry_price == D(110)


def test_ema_pullback_every_touch_candle_starts_its_own_setup(S):
    candles = BEFORE + [C(5, 104, 108, 102.5, 103.5),      # touch 1: entry 106 + 3 = 109
                        C(6, 103.5, 104, 102.8, 103.6),     # touch 2: candles 1-5, highest 108: entry 111
                        C(7, 103.6, 112, 103.4, 111.5)]     # reaches both
    assert sorted(x.entry_price for x in pullback(S, candles)) == [D(109), D(111)]


def test_ema_pullback_needs_the_hourly_trend(S):
    candles = BEFORE + [TOUCH, C(6, 103.5, 110, 103.2, 109)]
    assert pullback(S, candles, Hourly(BUY, qualified=False)) == []
    assert pullback(S, candles, Hourly(None, qualified=False)) == []
    assert pullback(S, candles, Hourly(SELL)) == []


def test_ema_pullback_sell_is_the_mirror_image(S):
    m = lambda x: 200 - x  # noqa: E731
    candles = BEFORE + [TOUCH, C(6, 103.5, 110, 103.2, 109)]
    mirrored = [C(i, m(c.sell_open), m(c.sell_low), m(c.sell_high), m(c.sell_close)) for i, c in enumerate(candles)]
    (x,) = pullback(S, mirrored, Hourly(SELL), fast=m(FAST), slow=m(SLOW), early=D(110))
    assert (x.direction, x.entry_price) == (SELL, D(91))


def hourly_candles(step, n=120):
    return [C(i, 100 + step * i, 100 + step * i + 1, 100 + step * i - 1, 100 + step * (i + 1),
              start=START - timedelta(hours=n), tf="1h", minutes=60) for i in range(n)]


def test_hourly_trend_rising_and_qualified(S):
    t = HourlyTrendReader(S, hourly_candles(D(2))).at(START)
    assert (t.direction, t.qualified) == (BUY, True) and "slopes 2" in t.why


def test_hourly_trend_falling(S):
    assert HourlyTrendReader(S, hourly_candles(D(-2))).at(START).direction == SELL


def test_hourly_trend_too_slow_is_not_qualified(S):
    t = HourlyTrendReader(S, hourly_candles(D("0.1"))).at(START)
    assert (t.direction, t.qualified) == (BUY, False)


def test_hourly_trend_minimums_are_settings(S):
    s = changed(S, "ema_pullback", hourly_min_slope_pips_per_hour=D("0.05"), hourly_min_gap_fast_mid_pips=D(0),
                hourly_min_gap_mid_slow_pips=D(0))
    assert HourlyTrendReader(s, hourly_candles(D("0.1"))).at(START).qualified


def test_hourly_trend_flat_has_no_direction(S):
    assert HourlyTrendReader(S, hourly_candles(D(0))).at(START).direction is None


def test_hourly_trend_uses_only_finished_hourly_candles(S):
    candles = hourly_candles(D(2))
    assert HourlyTrendReader(S, candles).at(candles[2].end).why == "not enough hourly candles"


# ---- 3.3 and 3.4: the strategies' own rejection watcher (design_only) -----------------------

def band(c, upper=110, lower=90):
    return Band(c.start, D(100), D(upper), D(lower))


BOUNCE_SELL = [C(0, 106, 112, 105, 108),       # pierces the upper band 110
               C(1, 108, 109, 103, 104),       # the first red candle: the reversal candle
               C(2, 104, 105, 100, 101),       # closes below the reversal low 103: the confirmation candle
               C(3, 101, 101.5, 98, 99)]       # goes below the confirmation low 100: the trigger


def watch(s, candles, bands=None):
    w, out = RejectionWatcher(s, design_only=True), []
    for k, c in enumerate(candles):
        ev = w.on_candle(c, band(c, upper=bands[k]) if bands else band(c), None)
        out += bounce_candidates(w, ev) + range_candidates(w, ev)
    return out


def test_bollinger_bounce_takes_the_trigger(S):
    got = [x for x in watch(S, BOUNCE_SELL) if x.strategy == BOLLINGER_BOUNCE]
    assert len(got) == 1
    x = got[0]
    assert (x.direction, x.entry_price, x.time) == (SELL, D(100), BOUNCE_SELL[3].start)
    text = " | ".join(x.steps)
    for word in ("pierce", "reversal", "confirmation", "trigger", "recorded, not used", "counts"):
        assert word in text, word


def test_bollinger_bounce_cancelled_above_the_reversal_high_has_no_idea(S):
    candles = BOUNCE_SELL[:3] + [C(3, 101, 109.5, 101, 109)]
    assert [x for x in watch(S, candles) if x.strategy == BOLLINGER_BOUNCE] == []


TWO_BOUNCES = [C(0, 106, 112, 105, 108),       # pierce 1 (band 110)
               C(1, 108, 109, 103, 104),       # reversal 1 (cancel above 109)
               C(2, 104, 105, 100, 101),       # confirmation 1; the band is down to 104.5: pierce 2
               C(3, 101, 101.5, 98.5, 99)]     # trigger 1 below 100; reversal 2 (red)
TWO_BANDS = [110, 110, D("104.5"), 110]


def test_bounce_every_pierce_starts_its_own_setup(S):
    w = RejectionWatcher(S, design_only=True)
    for c, up in zip(TWO_BOUNCES, TWO_BANDS):
        w.on_candle(c, band(c, upper=up), None)
    sells = [st for st in w.setups if st.version == "bounce" and st.direction == SELL]
    assert len(sells) == 2 and sells[0].status == "triggered" and sells[1].stage == "confirmation"


def test_bounce_a_pierce_while_waiting_starts_a_new_setup_and_does_not_restart_the_first(S):
    w = RejectionWatcher(S, design_only=True)
    for c in [C(0, 106, 112, 105, 108), C(1, 108, 113, 107, 112)]:     # green: pierces again
        w.on_candle(c, band(c), None)
    sells = [st for st in w.setups if st.version == "bounce" and st.direction == SELL]
    assert [st.pierce.start for st in sells] == [START, START + timedelta(minutes=5)]
    assert sells[0].waited == 1                          # the first goes on counting


def test_bounce_a_level_is_reached_from_either_side(S):
    from tests.technical.test_rejection import Levels
    lv = Levels((105, "R1"))
    above = C(0, 106, 106.5, 104.8, 106.2)              # opened above R1, its low went through it
    for design_only, expected in ((True, 1), (False, 0)):
        w = RejectionWatcher(S, design_only=design_only)
        w.on_candle(above, None, lv)
        assert len([st for st in w.setups if st.direction == SELL]) == expected
    near = C(0, 100, 102.5, 99, 101)                     # within 3 pips below R1: reached
    w = RejectionWatcher(S, design_only=True)
    w.on_candle(near, None, lv)
    assert [st.direction for st in w.setups] == [SELL]


def test_the_analysers_watcher_keeps_its_rules(S):
    w = RejectionWatcher(S)
    for c, up in zip(TWO_BOUNCES, TWO_BANDS):
        w.on_candle(c, band(c, upper=up), None)
    assert len([st for st in w.setups if st.version == "bounce" and st.direction == SELL]) == 1
    w = RejectionWatcher(S)
    for c in [C(0, 106, 112, 105, 108), C(1, 108, 113, 107, 112)]:
        w.on_candle(c, band(c), None)
    sells = [st for st in w.setups if st.version == "bounce" and st.direction == SELL]
    assert len(sells) == 1 and sells[0].pierce.start == START + timedelta(minutes=5)   # restarted


def test_range_trade_takes_the_trigger(S):
    candles = [C(0, 106, 112, 105, 108), C(1, 108, 109, 103, 104), C(2, 104, 104.5, 102, 102.5)]
    got = [x for x in watch(S, candles) if x.strategy == RANGE_TRADE]
    assert [(x.direction, x.entry_price, x.time) for x in got] == [(SELL, D(103), candles[2].start)]


def test_range_trade_cancelled_above_the_rejection_high_has_no_idea(S):
    candles = [C(0, 106, 112, 105, 108), C(1, 108, 109, 103, 104), C(2, 104, 110, 103.5, 109.5)]
    assert [x for x in watch(S, candles) if x.strategy == RANGE_TRADE] == []


# ---- the replay: the checks at entry only ----------------------------------------------------

def fake_replay(monkeypatch, S, states):
    """A slow grind sell: the pause counts at candle 3 and price breaks it on candle 4.
    `states`: {candle number: (state, direction) from that candle on}."""
    candles = PAUSE + [BREAK]
    hist = [(SimpleNamespace(candle=c, upper=None, middle=None, lower=None), None, None, [], None, None)
            for c in candles]
    tracker = SimpleNamespace(history=hist, week_open=START, watcher=None, replay=lambda end: None,
                              changes=[SimpleNamespace(time=candles[i].start, state=st, direction=d, trend_type=None)
                                       for i, (st, d) in sorted(states.items())])
    level = SimpleNamespace(type="pivot", price=D(110))
    monkeypatch.setattr(replay_mod, "StateTracker", lambda s, store: tracker)
    monkeypatch.setattr(replay_mod, "MemoStore", lambda store: store)
    monkeypatch.setattr(replay_mod, "check_same_pair", lambda s, store: None)
    monkeypatch.setattr(replay_mod, "last_candles", lambda *a: [])
    monkeypatch.setattr(replay_mod, "ema", lambda candles, side, periods: {c.start: D(120) for c in candles})
    monkeypatch.setattr(replay_mod, "build", lambda s, store, t: SimpleNamespace(levels=[level]))
    return [i for i in replay_mod.run(S, None, START, START + timedelta(hours=1)).ideas
            if i.strategy == SLOW_GRIND and i.direction == SELL]


def test_replay_checks_at_entry_with_the_state_after_the_last_finished_candle(monkeypatch, S):
    (i,) = fake_replay(monkeypatch, S, {0: (TREND, DOWN)})
    assert i.allowed and (i.state, i.state_direction) == (TREND, DOWN) and i.steps[-1].startswith("allowed at entry")
    (j,) = fake_replay(monkeypatch, S, {0: (TREND, DOWN), 3: (CONSOLIDATION, NONE)})
    assert not j.allowed and "consolidation" in j.blocked_by
    (k,) = fake_replay(monkeypatch, S, {0: (TREND, DOWN), 4: (CONSOLIDATION, NONE)})
    assert k.allowed                                    # decided on the entry candle itself: too late to matter


def test_replay_does_not_check_when_a_setup_starts(monkeypatch, S):
    (i,) = fake_replay(monkeypatch, S, {3: (TREND, DOWN)})   # consolidation while the pause formed
    assert i.allowed


# ---- hours, news and the forced close per strategy (design sections 4 and 6) ----------------

from datetime import datetime, timezone  # noqa: E402

from strategies.common import closed_before_big_news, closed_on_level_rejection, forced_close_at, may_open  # noqa: E402

U = lambda *a: datetime(*a, tzinfo=timezone.utc)  # noqa: E731
BOE_CAL = [{"time_utc": "2026-11-05T12:00:00Z", "country": "GB", "event": "BoE Interest Rate Decision",
            "estimate": 4.0, "prev": 4.0, "actual": None, "impact": "high", "unit": "%"}]
OTHERS = (SLOW_GRIND, BOLLINGER_BOUNCE, RANGE_TRADE)


@pytest.mark.parametrize("t", [U(2026, 11, 3, 3, 0), U(2026, 11, 3, 23, 0), U(2026, 11, 1, 21, 5), U(2026, 11, 5, 21, 30)])
def test_the_ema_pullback_may_open_at_any_time_the_market_is_open(S, t):
    assert may_open(S, "GBPUSD", EMA_PULLBACK, t, []) == []
    for name in OTHERS:
        assert "outside the trading hours 06:00 to 20:30 UK" in may_open(S, "GBPUSD", name, t, [])


@pytest.mark.parametrize("t", [U(2026, 11, 7, 12, 0), U(2026, 11, 1, 20, 0), U(2026, 11, 6, 22, 0)])
def test_nothing_opens_while_the_market_is_closed(S, t):
    for name in (EMA_PULLBACK,) + OTHERS:
        assert "the market is closed" in may_open(S, "GBPUSD", name, t, [])


def test_the_other_strategies_open_from_06_00_until_20_30_uk_only(S):
    for name in OTHERS:
        assert may_open(S, "GBPUSD", name, U(2026, 11, 3, 6, 0), []) == []          # GMT: 06:00 UK
        assert may_open(S, "GBPUSD", name, U(2026, 11, 3, 20, 25), []) == []
        assert may_open(S, "GBPUSD", name, U(2026, 11, 3, 20, 30), []) != []
        assert may_open(S, "GBPUSD", name, U(2026, 11, 3, 5, 55), []) != []
        assert may_open(S, "GBPUSD", name, U(2026, 10, 21, 5, 0), []) == []          # BST: 06:00 UK


def test_the_big_news_window_stops_every_strategy_but_the_ema_pullback(S):
    t = U(2026, 11, 5, 11, 50)                      # BoE at 12:00: no new trades 11:45 to 12:30
    assert may_open(S, "GBPUSD", EMA_PULLBACK, t, BOE_CAL) == []
    for name in OTHERS:
        assert any("big-news window" in r for r in may_open(S, "GBPUSD", name, t, BOE_CAL))
    assert closed_before_big_news(EMA_PULLBACK) is False
    assert all(closed_before_big_news(n) for n in OTHERS)


def test_the_other_strategies_are_closed_at_20_30_uk_every_day(S):
    for name in OTHERS:
        assert forced_close_at(S, name, U(2026, 11, 3, 10, 0)) == U(2026, 11, 3, 20, 30)
        assert forced_close_at(S, name, U(2026, 10, 21, 10, 0)) == U(2026, 10, 21, 19, 30)   # BST
        assert forced_close_at(S, name, U(2026, 11, 3, 21, 0)) == U(2026, 11, 4, 20, 30)


def test_the_ema_pullback_is_held_overnight_and_closed_only_on_friday_at_20_30_uk(S):
    assert forced_close_at(S, EMA_PULLBACK, U(2026, 11, 2, 7, 20)) == U(2026, 11, 6, 20, 30)   # Monday -> Friday
    assert forced_close_at(S, EMA_PULLBACK, U(2026, 11, 3, 23, 0)) == U(2026, 11, 6, 20, 30)
    assert forced_close_at(S, EMA_PULLBACK, U(2026, 11, 6, 13, 30)) == U(2026, 11, 6, 20, 30)  # Friday
    assert forced_close_at(S, EMA_PULLBACK, U(2026, 10, 23, 10, 0)) == U(2026, 10, 23, 19, 30)  # BST Friday
    # opened on Friday after 20:30 it is not open at 20:30 that Friday: the next Friday's 20:30
    assert forced_close_at(S, EMA_PULLBACK, U(2026, 11, 6, 20, 45)) == U(2026, 11, 13, 20, 30)


def test_the_ema_pullback_is_not_closed_on_a_rejection_at_a_level(S):
    assert closed_on_level_rejection(EMA_PULLBACK) is False
    assert all(closed_on_level_rejection(n) for n in OTHERS)


def test_the_ema_pullback_trades_in_a_trend_and_an_emerging_trend(S):
    for st in (EMERGING, TREND):
        assert check(S, "GBPUSD", cand(EMA_PULLBACK, SELL), state(st, DOWN), PIVOT, EMA100).allowed
    from analyser.states import ALLOWED
    assert "EMA pullback" in ALLOWED[EMERGING] and "EMA pullback" in ALLOWED[TREND]


def test_the_ema_pullback_has_its_own_take_profit(S):
    from strategies.common import take_profit_pips
    assert take_profit_pips(S, EMA_PULLBACK) == 30
    for name in OTHERS:
        assert take_profit_pips(S, name) == 100


def test_ema_pullback_trades_do_not_count_towards_most_at_once(S):
    from strategies.common import counts_towards_most_at_once
    assert counts_towards_most_at_once(EMA_PULLBACK) is False
    assert all(counts_towards_most_at_once(n) for n in OTHERS)


@pytest.mark.parametrize("t", [U(2026, 11, 6, 20, 30), U(2026, 11, 6, 20, 45), U(2026, 11, 6, 21, 55),
                               U(2026, 10, 23, 19, 30), U(2026, 10, 23, 20, 45)])     # GMT, then BST (19:30 UTC = 20:30 UK)
def test_no_ema_pullback_opens_after_20_30_uk_on_friday(S, t):
    assert any("after 20:30 UK on Friday" in r for r in may_open(S, "GBPUSD", EMA_PULLBACK, t, []))


def test_the_ema_pullback_still_opens_on_friday_before_20_30_uk_and_thursday_night(S):
    assert may_open(S, "GBPUSD", EMA_PULLBACK, U(2026, 10, 23, 19, 25), []) == []      # 20:25 BST
    assert may_open(S, "GBPUSD", EMA_PULLBACK, U(2026, 11, 6, 20, 25), []) == []      # 20:25 GMT
    assert may_open(S, "GBPUSD", EMA_PULLBACK, U(2026, 11, 5, 22, 0), []) == []       # Thursday 22:00
