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


class over:
    """The real settings with some values of one section changed (everything else read through)."""
    def __init__(self, base, section, **values):
        self._base, self._section = base, section
        items = {k: v for k, v in vars(getattr(base, section)).items() if not k.startswith("_")}
        self._values = SimpleNamespace(**(items | values))

    def __getattr__(self, name):
        return self._values if name == self._section else getattr(self._base, name)


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
    (RANGING, {RANGE_TRADE}),
    (EMERGING, {EMA_PULLBACK}),                    # the slow grind: trend only (owner, 8 November 2026)
    (TREND, {SLOW_GRIND, EMA_PULLBACK}),           # a sell in a down trend: the bounce only against it
    (POSSIBLE_REVERSAL, {BOLLINGER_BOUNCE}),
    (CONSOLIDATION, set()),
])
def test_which_states_allow_which_strategies(S, st, allowed):
    for name in (SLOW_GRIND, EMA_PULLBACK, BOLLINGER_BOUNCE, RANGE_TRADE):
        i = check(S, "GBPUSD", cand(name, SELL), state(st, DOWN), PIVOT, EMA100)
        assert i.allowed == (name in allowed), (st, name, i.blocked_by)


@pytest.mark.parametrize("name,st", [(EMA_PULLBACK, EMERGING), (EMA_PULLBACK, TREND), (SLOW_GRIND, TREND)])
def test_in_a_trend_only_the_trends_direction(S, name, st):
    assert check(S, "GBPUSD", cand(name, SELL), state(st, DOWN), PIVOT, EMA100).allowed
    against = check(S, "GBPUSD", cand(name, BUY, 120), state(st, DOWN), PIVOT, EMA100)
    assert not against.allowed and "only in the trend's direction" in against.blocked_by
    assert check(S, "GBPUSD", cand(name, BUY, 120), state(st, UP), PIVOT, EMA100).allowed


def test_a_bounce_in_a_trend_only_against_the_trends_direction(S):
    assert check(S, "GBPUSD", cand(BOLLINGER_BOUNCE, BUY, 120), state(TREND, DOWN), PIVOT, EMA100).allowed
    assert check(S, "GBPUSD", cand(BOLLINGER_BOUNCE, SELL, 100), state(TREND, UP), PIVOT, EMA100).allowed
    with_ = check(S, "GBPUSD", cand(BOLLINGER_BOUNCE, SELL, 100), state(TREND, DOWN), PIVOT, EMA100)
    assert not with_.allowed and "Bollinger bounce only against the trend's direction" in with_.blocked_by


@pytest.mark.parametrize("st,d", [(EMERGING, UP), (EMERGING, DOWN), (RANGING, NONE)])
def test_no_bounce_in_an_emerging_trend_or_ranging(S, st, d):
    for direction, price in ((BUY, 120), (SELL, 100)):
        i = check(S, "GBPUSD", cand(BOLLINGER_BOUNCE, direction, price), state(st, d), PIVOT, EMA100)
        assert not i.allowed and f"the analyser's state is {st}, which does not allow Bollinger bounce" in i.blocked_by


def test_the_analysers_list_for_the_bounce_matches(S):
    from analyser.states import ALLOWED
    assert not any("bounce" in x for x in ALLOWED[RANGING] + ALLOWED[EMERGING])
    assert "Bollinger band bounce (against the trend's direction only)" in ALLOWED[TREND]
    assert ALLOWED[POSSIBLE_REVERSAL] == ("Bollinger band bounce", "level reversal")


def test_a_bounce_in_consolidation_is_still_not_allowed(S):
    i = check(S, "GBPUSD", cand(BOLLINGER_BOUNCE, SELL, 100), state(CONSOLIDATION), PIVOT, EMA100)
    assert not i.allowed and "does not allow Bollinger bounce" in i.blocked_by


def test_the_ema_pullback_has_its_own_stop_loss(S):
    from strategies.common import stop_loss_pips
    assert stop_loss_pips(S, EMA_PULLBACK) == 12
    for name in (BOLLINGER_BOUNCE, RANGE_TRADE):
        assert stop_loss_pips(S, name) == 6                    # the pretend .env's STOP_LOSS_PIPS


def test_owners_12_pip_stop_is_for_the_bounce_range_trade_and_breakout_only(S):
    """Owner, 10 November 2026: STOP_LOSS_PIPS=12 in .env and breakout.stop_loss_pips = 12 give exactly the
    Bollinger bounce, the range trade and the breakout a 12-pip stop; every other strategy keeps its own."""
    from strategies.common import stop_loss_pips
    assert S.breakout.stop_loss_pips == 12                     # config/settings.toml
    s = over(S, "switches", stop_loss_pips=12)                 # the owner's .env line
    assert {n: stop_loss_pips(s, n) for n in (BOLLINGER_BOUNCE, RANGE_TRADE, BREAKOUT)} == \
        {BOLLINGER_BOUNCE: 12, RANGE_TRADE: 12, BREAKOUT: 12}
    assert stop_loss_pips(s, EMA_PULLBACK) == S.switches.stop_loss_pips_ema_pullback == 12   # its own switch
    assert stop_loss_pips(s, SLOW_GRIND) == 15                 # slow_grind.stop_loss_pips
    assert stop_loss_pips(s, LEVEL_REVERSAL) == 6              # 6 pips beyond the furthest point, not from the entry
    s6 = over(S, "switches", stop_loss_pips=6)                 # STOP_LOSS_PIPS reaches only the bounce and range trade
    assert stop_loss_pips(s6, BREAKOUT) == 12 and stop_loss_pips(s6, SLOW_GRIND) == 15


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
@pytest.mark.parametrize("name", [EMA_PULLBACK])        # not the slow grind since 8 November 2026
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
        assert i.allowed and "does not apply to Bollinger bounce" in i.steps[-1]


@pytest.mark.parametrize("price", [100, 105, 120])
def test_the_direction_rule_does_not_apply_to_the_bounce_in_a_trend_either(S, price):
    i = check(S, "GBPUSD", cand(BOLLINGER_BOUNCE, BUY, price), state(TREND, DOWN), PIVOT, EMA100)
    assert i.allowed and "the direction rule does not apply to Bollinger bounce" in i.steps[-1]
    i = check(S, "GBPUSD", cand(BOLLINGER_BOUNCE, SELL, price), state(TREND, UP), PIVOT, EMA100)
    assert i.allowed


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


@pytest.fixture
def S3(S):
    """The mechanism tests below are written with a 3-candle pause (the owner's value is 2 since
    8 November 2026: test_slow_grind_the_owners_pause_is_2_candles)."""
    return over(S, "slow_grind", min_pause_candles=3)


def grind(s, candles, ema=EMA21):
    g = SlowGrind(s)
    return [(c, x) for c in candles for x in g.on_candle(c, ema)]


PAUSE = [C(0, 105, 106, 100, 101),         # the first candle watched: the reference, low 100
         C(1, 101, 103, 100.5, 102),       # 1 in a row: no new low, closes below the EMA
         C(2, 102, 103, 101, 101.5),       # 2
         C(3, 101.5, 102.5, 100.2, 102)]   # 3: a pause; its lowest point 100.2
BREAK = C(4, 102, 102, 100.1, 100.5)       # goes below 100.2 (not below the reference 100)


def test_slow_grind_sell_opens_below_the_lowest_point_of_the_pause(S3):
    (c, x), = grind(S3, PAUSE + [BREAK])
    assert (x.strategy, x.direction, x.entry_price, x.time) == (SLOW_GRIND, SELL, D("100.2"), BREAK.start)
    assert "the last low made: 100" in x.steps[0] and "a pause: 3 candles in a row" in x.steps[1]
    assert "its lowest point 100.2" in x.steps[1] and "broke below" in x.steps[2]


def test_slow_grind_a_candle_opening_below_it_enters_at_its_open(S3):
    (_, x), = grind(S3, PAUSE + [C(4, 99, 99.5, 98, 98.5)])
    assert x.entry_price == D(99)


def test_slow_grind_needs_the_pause_length_in_a_row(S3):
    assert grind(S3, PAUSE[:3] + [C(3, 101.5, 102, 99, 99.5)]) == []        # a new low after 2: no pause


def test_slow_grind_the_pause_length_is_a_setting(S3):
    s = changed(S3, "slow_grind", min_pause_candles=4)
    assert grind(s, PAUSE + [C(4, 102, 102, 100.3, 101)]) == []
    assert [x.entry_price for _, x in grind(s, PAUSE + [C(4, 102, 102, 100.3, 101), BREAK])] == [D("100.2")]


def test_slow_grind_no_colour_or_size_test(S3):
    greens = [C(0, 99, 106, 100, 101), C(1, "100.3", "100.7", "100.2", "100.6"),    # every candle green, tiny
              C(2, "100.4", "100.8", "100.3", "100.7"), C(3, "100.5", "100.9", "100.4", "100.8"),
              C(4, "100.5", "100.5", "99.9", "100")]
    assert [x.entry_price for _, x in grind(S3, greens)] == [D("100.2")]


def test_slow_grind_a_close_above_the_21_ema_cancels_and_the_next_candle_is_the_reference(S3):
    g, out = SlowGrind(S3), []
    for c, e in zip(PAUSE + [BREAK], [EMA21] * 3 + [D(101), EMA21]):       # candle 3 closes 102, above 101
        out += g.on_candle(c, e)
    assert out == [] and g.watch[SELL].ref is BREAK and g.watch[SELL].row == []


def test_slow_grind_a_new_low_before_the_pause_counts_is_the_next_reference(S3):
    candles = PAUSE[:2] + [C(2, 102, 102.5, 99.5, 101),     # a new low 99.5: the row starts again from here
                           C(3, 101, 102, 100, 101.5), C(4, 101.5, 102, 100.5, 101), C(5, 101, 101.8, 99.8, 101.2),
                           C(6, 101.2, 101.2, 99.6, 99.7)]
    assert [x.entry_price for _, x in grind(S3, candles)] == [D("99.8")]


def test_slow_grind_a_close_exactly_on_the_ema_starts_the_row_again(S3):
    g, out = SlowGrind(S3), []
    for c, e in zip(PAUSE + [BREAK], [EMA21, EMA21, D("101.5"), EMA21, EMA21]):   # candle 2 closes on it
        out += g.on_candle(c, e)
    assert out == []


def test_slow_grind_one_row_at_a_time_so_one_idea(S3):
    assert len(grind(S3, PAUSE + [BREAK])) == 1


def test_slow_grind_the_breaking_candle_is_the_next_reference(S3):
    after = [C(5 + k, 100.5, 101, 100.2, 100.6) for k in range(3)] + [C(8, 100.6, 100.6, 100, 100.1)]
    assert [x.entry_price for _, x in grind(S3, PAUSE + [BREAK] + after)] == [D("100.2"), D("100.2")]


def test_slow_grind_no_time_limit(S3):
    waiting = [C(4 + k, 101, 102, 100.3, 101.5) for k in range(30)]
    assert [x.entry_price for _, x in grind(S3, PAUSE + waiting + [C(34, 101, 101, 99, 99.5)])] == [D("100.2")]


def test_slow_grind_buy_is_the_mirror_image(S3):
    m = lambda x: 200 - x  # noqa: E731     (a mirror: highs become lows)
    mirrored = [C(i, m(c.sell_open), m(c.sell_low), m(c.sell_high), m(c.sell_close))
                for i, c in enumerate(PAUSE + [BREAK])]
    (_, x), = grind(S3, mirrored, ema=D(80))
    assert (x.direction, x.entry_price) == (BUY, D("99.8"))


def test_slow_grind_the_owners_pause_is_2_candles(S):
    assert S.slow_grind.min_pause_candles == 2
    (_, x), = grind(S, PAUSE[:3] + [C(3, 101.5, 102.5, 100.2, 102)])   # 2 in a row (lowest 100.5), then below it
    assert x.entry_price == D("100.5") and "a pause: 2 candles in a row" in x.steps[1]
    assert grind(S, PAUSE[:2] + [C(2, 102, 103, 100.2, 101.5)]) == []    # 1 candle in a row is not a pause


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
    S = over(S, "slow_grind", min_pause_candles=3)
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
OTHERS = (BOLLINGER_BOUNCE, RANGE_TRADE)      # the slow grind has its own rules since 8 November 2026


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
    assert closed_before_big_news(EMA_PULLBACK) is False and closed_before_big_news(SLOW_GRIND) is False
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


# ---- the EMA pullback's take profit on big-news days (design section 4) ----------------------

def _ev(t, country, event, impact="high"):
    return {"time_utc": t, "country": country, "event": event, "estimate": 4.0, "prev": 4.0, "actual": None,
            "impact": impact, "unit": "%"}


def test_an_ema_pullback_opened_on_a_big_news_day_gets_100_pips(S):
    from strategies.common import take_profit_pips
    cal = [_ev("2026-11-05T12:00:00Z", "GB", "BoE Interest Rate Decision")]
    for opened in (U(2026, 11, 5, 0, 5), U(2026, 11, 5, 4, 0), U(2026, 11, 5, 13, 0), U(2026, 11, 5, 23, 55)):
        assert take_profit_pips(S, EMA_PULLBACK, opened, "GBPUSD", cal) == 100
    for opened in (U(2026, 11, 4, 23, 55), U(2026, 11, 6, 0, 5)):       # the day before and after
        assert take_profit_pips(S, EMA_PULLBACK, opened, "GBPUSD", cal) == 30


def test_the_big_news_day_is_the_uk_calendar_day(S):
    from strategies.common import take_profit_pips
    cal = [_ev("2026-10-21T23:30:00Z", "US", "Non Farm Payrolls")]      # 00:30 BST on Thursday 22 October
    assert take_profit_pips(S, EMA_PULLBACK, U(2026, 10, 21, 22, 30), "GBPUSD", cal) == 30   # 23:30 BST Wednesday
    assert take_profit_pips(S, EMA_PULLBACK, U(2026, 10, 22, 8, 0), "GBPUSD", cal) == 100


def test_only_big_news_for_the_pair_counts(S):
    from strategies.common import take_profit_pips
    t = U(2026, 11, 5, 9, 0)
    assert take_profit_pips(S, EMA_PULLBACK, t, "GBPUSD", [_ev("2026-11-05T12:00:00Z", "GB", "BoE Interest Rate Decision", "low")]) == 30
    assert take_profit_pips(S, EMA_PULLBACK, t, "GBPUSD", [_ev("2026-11-05T12:00:00Z", "JP", "BoJ Interest Rate Decision")]) == 30
    assert take_profit_pips(S, EMA_PULLBACK, t, "GBPUSD", [_ev("2026-11-05T13:30:00Z", "US", "Retail Sales MoM")]) == 30   # medium
    assert take_profit_pips(S, EMA_PULLBACK, t, "GBPUSD", []) == 30


def test_the_other_strategies_keep_100_pips_on_any_day(S):
    from strategies.common import take_profit_pips
    cal = [_ev("2026-11-05T12:00:00Z", "GB", "BoE Interest Rate Decision")]
    for name in OTHERS:
        for opened in (U(2026, 11, 5, 9, 0), U(2026, 11, 4, 9, 0)):
            assert take_profit_pips(S, name, opened, "GBPUSD", cal) == 100


# ---- 3.5 breakout ---------------------------------------------------------------------------

from datetime import datetime as _dt  # noqa: E402
from strategies.breakout.strategy import BREAKOUT_REASONS, Breakout  # noqa: E402
from strategies.common import BREAKOUT  # noqa: E402

MIDNIGHT = _dt(2026, 11, 4, 0, 0, tzinfo=timezone.utc)      # 00:00 UK (GMT): the day's open candle


def bchange(direction=UP, prev=CONSOLIDATION, reason=None):
    reason = reason if reason is not None else BREAKOUT_REASONS[prev] + ": close beyond the band"
    return SimpleNamespace(previous_state=prev, state=EMERGING, direction=direction, reason=reason)


def B(i, o, h, l, c):
    return C(i, o, h, l, c, start=MIDNIGHT)


OPEN = B(0, 100, 100.5, 99.5, 100)                           # the 00:00 UK candle: the day opens at 100
CONS = [OPEN] + [B(i, 100, 103, 98, 101) for i in range(1, 5)]  # the consolidation: low 98, high 103
UPC = B(5, 101, 106, 100.5, 105.5)                          # the breakout candle: high 106, low 100.5
DOWNC = B(5, 100, 100.5, 96, 96.5)                          # low 96


def run_breakout(s, candles, at=5, change=None, since=MIDNIGHT):
    b, out = Breakout(s), []
    for k, c in enumerate(candles):
        out += b.on_candle(c, (change or bchange()) if k == at else None, since if k == at else None)
    return out, b


def test_breakout_buy_opens_above_the_breakout_candle_high(S):
    (x,), _ = run_breakout(S, CONS + [UPC, B(6, 105.5, 107, 105, 106.5)])
    assert (x.strategy, x.direction, x.entry_price, x.time) == (BREAKOUT, BUY, D(106), B(6, 0, 0, 0, 0).start)
    assert "moved from consolidation to an emerging trend up" in x.steps[0]
    assert "above the day's 00:00 UK open 100" in x.steps[-1]
    assert (x.context["broke_out_of"], x.context["base_low"], x.context["base_high"]) == ("consolidation", D("98"), D("103"))


def test_breakout_sell_opens_below_the_breakout_candle_low(S):
    (x,), _ = run_breakout(S, CONS + [DOWNC, B(6, 96.5, 97, 95, 95.5)], change=bchange(DOWN))
    assert (x.direction, x.entry_price) == (SELL, D(96))


def test_breakout_out_of_a_range_too(S):
    (x,), _ = run_breakout(S, CONS + [UPC, B(6, 105.5, 107, 105, 106.5)], change=bchange(prev=RANGING))
    assert x.context["broke_out_of"] == "range" and "moved from ranging" in x.steps[0]


def test_breakout_only_with_the_days_move_so_far(S):
    high_open = [B(0, 110, 110.5, 109.5, 110)] + CONS[1:]   # the day opened at 110
    out, b = run_breakout(S, high_open + [UPC, B(6, 105.5, 107, 105, 106.5)])
    assert out == [] and any("not above the day's open 110" in t for _, _, t in b.notes)    # a buy below the open
    (x,), _ = run_breakout(S, high_open + [DOWNC, B(6, 96.5, 97, 95, 95.5)], change=bchange(DOWN))
    assert x.direction == SELL                                              # a sell below the open: fine
    low_open = [B(0, 90, 90.5, 89.5, 90)] + CONS[1:]
    assert run_breakout(S, low_open + [DOWNC, B(6, 96.5, 97, 95, 95.5)], change=bchange(DOWN))[0] == []
    flat = [B(0, 106, 106.5, 105.5, 106)] + CONS[1:]        # entry exactly at the open: neither above nor below
    assert run_breakout(S, flat + [UPC, B(6, 105.5, 107, 105, 106.5)])[0] == []


def test_breakout_needs_the_days_00_00_uk_candle(S):
    later = [C(i, 100, 103, 98, 101) for i in range(5)]      # 09:00 onwards: no 00:00 candle seen
    out, b = run_breakout(S, later + [C(5, 101, 106, 100.5, 105.5), C(6, 105.5, 107, 105, 106.5)], since=START)
    assert out == [] and any("00:00 UK open was not seen" in t for _, _, t in b.notes)


def test_breakout_a_candle_opening_past_the_price_enters_at_its_open(S):
    (x,), _ = run_breakout(S, CONS + [UPC, B(6, 107, 108, 106.5, 107.5)])
    assert x.entry_price == D(107)


def test_breakout_expires_after_3_candles(S):
    wait = [B(6 + k, 105, 105.8, 104, 105) for k in range(3)]
    assert run_breakout(S, CONS + [UPC] + wait[:2] + [B(8, 105, 107, 104, 106)])[0] != []     # the 3rd: in time
    out, b = run_breakout(S, CONS + [UPC] + wait + [B(9, 105, 107, 104, 106)])
    assert out == [] and any("expired" in t for _, _, t in b.notes)


def test_breakout_the_expiry_is_a_setting(S):
    s = changed(S, "breakout", trigger_within_candles=1)
    s.hours = S.hours
    assert run_breakout(s, CONS + [UPC, B(6, 105, 105.8, 104, 105), B(7, 105, 107, 104, 106)])[0] == []


@pytest.mark.parametrize("change", [
    bchange(prev=TREND, reason="broke out of the consolidation"),                    # not from consolidation or ranging
    bchange(reason="rejected at a level: closed 13415.6 above the reversal high"),   # not a breakout
    bchange(prev=RANGING, reason=BREAKOUT_REASONS[CONSOLIDATION]),                    # the reason must match the state left
    SimpleNamespace(previous_state=CONSOLIDATION, state=RANGING, direction=NONE, reason=BREAKOUT_REASONS[CONSOLIDATION]),
])
def test_breakout_only_on_the_analysers_breakout_into_an_emerging_trend(S, change):
    assert run_breakout(S, CONS + [UPC, B(6, 105.5, 107, 105, 106.5)], change=change)[0] == []


def test_breakout_states_and_no_direction_rule(S):
    on = changed(S, "switches", breakout=True)
    for price in (100, 120):                               # sell side and buy side: the rule does not apply
        i = check(on, "GBPUSD", cand(BREAKOUT, BUY, price), state(EMERGING, UP), PIVOT, EMA100)
        assert i.allowed and "the direction rule does not apply to breakout" in i.steps[-1]
    assert check(on, "GBPUSD", cand(BREAKOUT, BUY, 120), state(TREND, UP), PIVOT, EMA100).allowed
    assert "only in the trend's direction" in check(on, "GBPUSD", cand(BREAKOUT, SELL, 100), state(EMERGING, UP), PIVOT, EMA100).blocked_by
    for st in (RANGING, CONSOLIDATION, POSSIBLE_REVERSAL):
        assert "does not allow breakout" in check(on, "GBPUSD", cand(BREAKOUT, BUY, 120), state(st, UP), PIVOT, EMA100).blocked_by
    assert "STRATEGY_BREAKOUT is off" in check(S, "GBPUSD", cand(BREAKOUT, BUY, 120), state(EMERGING, UP), PIVOT, EMA100).blocked_by


def test_breakout_hours_news_friday_and_exits(S):
    from strategies.common import closed_before_big_news, counts_towards_most_at_once, stop_loss_pips, take_profit_pips
    assert may_open(S, "GBPUSD", BREAKOUT, U(2026, 11, 3, 6, 0), []) == []
    assert "outside the trading hours 06:00 to 20:30 UK" in may_open(S, "GBPUSD", BREAKOUT, U(2026, 11, 3, 5, 55), [])
    assert "outside the trading hours 06:00 to 20:30 UK" in may_open(S, "GBPUSD", BREAKOUT, U(2026, 11, 3, 20, 30), [])
    assert "outside the trading hours 06:00 to 20:30 UK" in may_open(S, "GBPUSD", BREAKOUT, U(2026, 11, 3, 22, 0), [])
    assert may_open(S, "GBPUSD", BREAKOUT, U(2026, 11, 5, 11, 50), BOE_CAL) == []          # big news: may open
    assert forced_close_at(S, BREAKOUT, U(2026, 11, 3, 10, 0)) == U(2026, 11, 6, 20, 30)   # held to Friday 20:30
    assert closed_before_big_news(BREAKOUT) is False
    assert closed_on_level_rejection(BREAKOUT) is False                                       # no level close
    assert counts_towards_most_at_once(BREAKOUT) is True
    assert (stop_loss_pips(S, BREAKOUT), take_profit_pips(S, BREAKOUT, U(2026, 11, 5, 9, 0), "GBPUSD", BOE_CAL)) == (12, 50)


def test_the_replay_gives_the_breakout_the_analysers_breakout(monkeypatch, S):
    candles = CONS + [UPC, B(6, 105.5, 107, 105, 106.5)]
    hist = [(SimpleNamespace(candle=c, upper=None, middle=None, lower=None), None, None, [], None, None) for c in candles]
    changes = [SimpleNamespace(time=candles[0].start, state=CONSOLIDATION, direction=NONE, trend_type=None,
                               previous_state=TREND, reason="ran out of steam"),
               SimpleNamespace(time=candles[5].start, state=EMERGING, direction=UP, trend_type=None,
                               previous_state=CONSOLIDATION, reason=BREAKOUT_REASONS[CONSOLIDATION] + ": close above the band")]
    tracker = SimpleNamespace(history=hist, week_open=MIDNIGHT, watcher=None, replay=lambda end: None, changes=changes)
    level = SimpleNamespace(type="pivot", price=D(90))
    monkeypatch.setattr(replay_mod, "StateTracker", lambda s, store: tracker)
    monkeypatch.setattr(replay_mod, "MemoStore", lambda store: store)
    monkeypatch.setattr(replay_mod, "check_same_pair", lambda s, store: None)
    monkeypatch.setattr(replay_mod, "last_candles", lambda *a: [])
    monkeypatch.setattr(replay_mod, "ema", lambda candles, side, periods: {c.start: D(80) for c in candles})
    monkeypatch.setattr(replay_mod, "build", lambda s, store, t: SimpleNamespace(levels=[level]))
    (i,) = [x for x in replay_mod.run(S, None, MIDNIGHT, MIDNIGHT + timedelta(hours=1)).ideas if x.strategy == BREAKOUT]
    assert (i.direction, i.entry_price, i.state) == (BUY, D(106), EMERGING)
    assert not i.allowed and i.blocked_by == "its switch STRATEGY_BREAKOUT is off"      # the pretend switches: off
    assert (i.context["base_low"], i.context["base_high"], i.context["day_open"]) == (D(98), D(103), D(100))


# ---- the slow grind switched on (owner, 8 November 2026: design 2.2, 2.3, 3.1, 4, 6) ----------

from datetime import time as _time  # noqa: E402

from strategies.common import (counts_towards_most_at_once, profit_lock, stop_loss_pips,  # noqa: E402
                               take_profit_pips)


def test_slow_grind_only_in_a_trend_in_the_trends_direction(S):
    for kind in ("slow grind", "strong push"):
        assert check(S, "GBPUSD", cand(SLOW_GRIND, SELL, 100), state(TREND, DOWN, kind), PIVOT, EMA100).allowed
        assert check(S, "GBPUSD", cand(SLOW_GRIND, BUY, 120), state(TREND, UP, kind), PIVOT, EMA100).allowed
    assert "only in the trend's direction" in check(S, "GBPUSD", cand(SLOW_GRIND, BUY, 120), state(TREND, DOWN),
                                                     PIVOT, EMA100).blocked_by
    for st in (EMERGING, RANGING, CONSOLIDATION, POSSIBLE_REVERSAL):
        assert "does not allow slow grind" in check(S, "GBPUSD", cand(SLOW_GRIND, SELL, 100), state(st, DOWN),
                                                    PIVOT, EMA100).blocked_by
    from analyser.states import ALLOWED
    assert "slow grind" in ALLOWED[TREND] and "slow grind" not in ALLOWED[EMERGING]


def test_slow_grind_has_no_direction_rule(S):
    for price in (100, 120):                               # sell side and buy side: the rule does not apply
        i = check(S, "GBPUSD", cand(SLOW_GRIND, SELL, price), state(TREND, DOWN), PIVOT, EMA100)
        assert i.allowed and "the direction rule does not apply to slow grind" in i.steps[-1]
    i = check(S, "GBPUSD", cand(SLOW_GRIND, BUY, 100), state(TREND, UP), PIVOT, EMA100)
    assert i.allowed and i.direction_rule == "sell side"   # still recorded


def test_slow_grind_its_own_stop_take_profit_and_lock(S):
    cal = [_ev("2026-11-05T12:00:00Z", "GB", "BoE Interest Rate Decision")]
    assert stop_loss_pips(S, SLOW_GRIND) == 15
    assert take_profit_pips(S, SLOW_GRIND) == 20
    assert take_profit_pips(S, SLOW_GRIND, U(2026, 11, 4, 9, 0), "GBPUSD", cal) == 20
    assert take_profit_pips(S, SLOW_GRIND, U(2026, 11, 5, 1, 55), "GBPUSD", cal) == 100     # big-news day
    assert profit_lock(S, SLOW_GRIND) == (15, 10)
    for name in (EMA_PULLBACK, BOLLINGER_BOUNCE, RANGE_TRADE, BREAKOUT):
        assert profit_lock(S, name) is None


def test_slow_grind_values_are_settings(S):
    s = over(S, "slow_grind", stop_loss_pips=9, take_profit_pips=40, lock_from_pips=20, lock_at_pips=5)
    assert (stop_loss_pips(s, SLOW_GRIND), take_profit_pips(s, SLOW_GRIND), profit_lock(s, SLOW_GRIND)) == (9, 40, (20, 5))


@pytest.mark.parametrize("t", [U(2026, 11, 3, 0, 0), U(2026, 11, 3, 3, 0), U(2026, 11, 3, 5, 55), U(2026, 11, 3, 20, 25),
                               U(2026, 10, 21, 19, 25), U(2026, 11, 2, 0, 5), U(2026, 11, 6, 20, 25)])
def test_slow_grind_may_open_at_any_time_but_20_30_to_midnight(S, t):
    assert may_open(S, "GBPUSD", SLOW_GRIND, t, []) == []


@pytest.mark.parametrize("t", [U(2026, 11, 3, 20, 30), U(2026, 11, 3, 22, 45), U(2026, 11, 3, 23, 55),
                               U(2026, 10, 21, 19, 30), U(2026, 10, 21, 22, 50), U(2026, 11, 6, 20, 30)])  # GMT, BST, Friday
def test_no_slow_grind_from_20_30_to_midnight_uk(S, t):
    assert any("from 20:30 UK to midnight" in r for r in may_open(S, "GBPUSD", SLOW_GRIND, t, []))


def test_no_slow_grind_in_the_first_15_minutes_of_the_week_or_at_the_rollover(S):
    late = over(S, "hours", close_all_trades_at=_time(23, 59))   # so the 20:30-midnight rule does not hide them
    for t in (U(2026, 11, 1, 21, 0), U(2026, 11, 1, 21, 10)):    # the market opens Sunday 21:00 UK
        assert any("first 15 minutes after the week opened" in r for r in may_open(late, "GBPUSD", SLOW_GRIND, t, []))
        assert any("from 20:30 UK to midnight" in r for r in may_open(S, "GBPUSD", SLOW_GRIND, t, []))
    assert may_open(late, "GBPUSD", SLOW_GRIND, U(2026, 11, 1, 21, 15), []) == []
    for t in (U(2026, 11, 3, 21, 55), U(2026, 11, 3, 22, 10)):
        assert any("21:55 to 22:15 UK (the rollover)" in r for r in may_open(late, "GBPUSD", SLOW_GRIND, t, []))
    for t in (U(2026, 11, 3, 21, 50), U(2026, 11, 3, 22, 15)):
        assert may_open(late, "GBPUSD", SLOW_GRIND, t, []) == []
    assert "the market is closed" in may_open(S, "GBPUSD", SLOW_GRIND, U(2026, 11, 7, 12, 0), [])


def test_slow_grind_big_news_closes_and_holding(S):
    assert may_open(S, "GBPUSD", SLOW_GRIND, U(2026, 11, 5, 11, 50), BOE_CAL) == []       # may open in big news
    assert closed_before_big_news(SLOW_GRIND) is False
    assert closed_on_level_rejection(SLOW_GRIND) is False
    assert counts_towards_most_at_once(SLOW_GRIND) is True
    assert forced_close_at(S, SLOW_GRIND, U(2026, 11, 3, 0, 15)) == U(2026, 11, 3, 20, 30)    # the same day
    assert forced_close_at(S, SLOW_GRIND, U(2026, 11, 3, 19, 40)) == U(2026, 11, 3, 20, 30)
    assert forced_close_at(S, SLOW_GRIND, U(2026, 10, 21, 10, 0)) == U(2026, 10, 21, 19, 30)  # BST


# ---- 3.6 level reversal (owner, 8 November 2026) ----------------------------------------------

from decimal import Decimal  # noqa: E402

from rejection.watch import Setup  # noqa: E402
from strategies.common import LEVEL_REVERSAL, stop_price  # noqa: E402
from strategies.level_reversal.strategy import LevelReversal  # noqa: E402

LR0 = C(0, 99, 99.5, 98, 99)                # a candle before the setup


def lr_setup(pierced, highs, direction=SELL):
    """A finished bounce setup: the pierce candle, the reversal candle, the confirmation candle
    (sell highs as given), then a trigger at 96 on the next candle. Returns (strategy, watcher, events, candles)."""
    if direction == SELL:
        cs = [C(1 + k, h - 1, h, h - 3, h - 2) for k, h in enumerate(highs)]
        price = D(96)
    else:
        cs = [C(1 + k, l + 1, l + 3, l, l + 2) for k, l in enumerate(highs)]
        price = D(104)
    trig = C(1 + len(highs), 97, 97, 95, 95.5) if direction == SELL else C(1 + len(highs), 103, 105, 103, 104.5)
    st = Setup(1, "bounce", direction, cs[0], [{"what": w, "price": D(str(p)), "how": "through"} for w, p in pierced])
    st.reversal, st.confirmation = cs[1], cs[-1]
    ev = SimpleNamespace(setup=1, version="bounce", kind="trigger", direction=direction, time=trig.start, price=price,
                         describe=lambda: "made-up trigger")
    watcher = SimpleNamespace(setups=[st], events=[ev])
    return watcher, [ev], [LR0] + cs + [trig]


def run_lr(s, watcher, events, candles):
    g, out = LevelReversal(s), []
    for c in candles:
        out += g.on_candle(c, watcher, events if c is candles[-1] else [])
    return out


def test_level_reversal_at_r2_within_the_allowance(S):
    w, ev, cs = lr_setup([("R2", 100)], [104, 103, 102])          # furthest high 104: 4 pips past R2
    (x,) = run_lr(S, w, ev, cs)
    assert (x.strategy, x.direction, x.entry_price) == (LEVEL_REVERSAL, SELL, D(96))
    assert x.context["level"] == D(100) and x.context["furthest"] == D(104) and x.context["past_level_pips"] == 4
    assert x.context["stop_price"] == D(110)                     # 6 pips above the furthest point
    assert "R2 100" in x.steps[-2] and "4.0 pips past the level" in x.steps[-2] and "to 09:15 GMT" in x.steps[-2]


@pytest.mark.parametrize("what,price,allowance", [("R2", 100, 12), ("S2", 100, 12), ("round_number", 200, 5)])
def test_level_reversal_allowance_for_each_kind_of_level(S, what, price, allowance):
    w, ev, cs = lr_setup([(what, price)], [price + allowance, price + 1, price])              # exactly the allowance: counts
    (x,) = run_lr(S, w, ev, cs)
    assert x.context["past_level_pips"] == allowance and f"(allowance {allowance})" in x.steps[-2]
    w, ev, cs = lr_setup([(what, price)], [price + 1, price + allowance + 0.1, price])        # 0.1 more (the reversal candle): not
    assert run_lr(S, w, ev, cs) == []


def test_level_reversal_each_allowance_is_its_own_setting(S):
    assert (S.level_reversal.allowance_pips_r2, S.level_reversal.allowance_pips_s2,
            S.level_reversal.allowance_pips_round_number) == (12, 12, 5)
    w, ev, cs = lr_setup([("S2", 100)], [113, 101, 100])                                     # 13 past S2
    assert run_lr(S, w, ev, cs) == []
    assert len(run_lr(over(S, "level_reversal", allowance_pips_s2=13), w, ev, cs)) == 1
    assert run_lr(over(S, "level_reversal", allowance_pips_r2=13, allowance_pips_round_number=13), w, ev, cs) == []
    w, ev, cs = lr_setup([("round_number", 200)], [206, 201, 200])                           # 6 past a 00
    assert run_lr(S, w, ev, cs) == []
    assert len(run_lr(over(S, "level_reversal", allowance_pips_round_number=6), w, ev, cs)) == 1


def test_level_reversal_short_of_the_level_counts(S):
    w, ev, cs = lr_setup([("round_number", 100)], [98, 97.5, 97])  # stopped 2 pips short of the 00 round number
    (x,) = run_lr(S, w, ev, cs)
    assert x.context["past_level_pips"] == -2 and x.context["stop_price"] == D(104)


def test_level_reversal_only_s2_r2_and_00_round_numbers(S):
    for what, price in (("R1", 100), ("S1", 100), ("S3", 100), ("R3", 100), ("pivot", 100), ("turning_high", 100),
                        ("upper Bollinger band", 100), ("round_number", 150)):       # 150: a 50, not a 00
        w, ev, cs = lr_setup([(what, price)], [101, 100, 99])
        assert run_lr(S, w, ev, cs) == [], what
    w, ev, cs = lr_setup([("round_number", 200)], [201, 200, 199])
    assert len(run_lr(S, w, ev, cs)) == 1


def test_level_reversal_round_numbers_are_00s_in_pips(S):
    lr = LevelReversal(S)
    assert lr.kind("round_number", D("13400.0")) and not lr.kind("round_number", D("13450.0"))
    assert LevelReversal(over(S, "level_reversal", round_numbers_every_pips=50)).kind("round_number", D("13450.0"))
    assert not LevelReversal(over(S, "level_reversal", level_types=("S2",))).kind("R2", D("13400.0"))


def test_level_reversal_s2_or_r2_before_a_round_number(S):
    w, ev, cs = lr_setup([("round_number", 200), ("R2", 199)], [202, 201, 200])
    (x,) = run_lr(S, w, ev, cs)
    assert x.context["level"] == D(199) and x.context["level_name"].startswith("R2")
    w, ev, cs = lr_setup([("R2", 189), ("round_number", 200)], [202, 201, 200])    # R2 13 past: the 00 is the level
    (x,) = run_lr(S, w, ev, cs)
    assert x.context["level"] == D(200)


def test_level_reversal_buy_is_the_mirror_image(S):
    w, ev, cs = lr_setup([("S2", 100)], [96, 97, 98], direction=BUY)      # lows: furthest 96, 4 past S2
    (x,) = run_lr(S, w, ev, cs)
    assert (x.direction, x.context["past_level_pips"], x.context["stop_price"]) == (BUY, 4, D(90))


def test_level_reversal_one_idea_per_candle_and_direction(S):
    w, ev, cs = lr_setup([("R2", 100)], [104, 103, 102])
    w.setups.append(w.setups[0]); twin = SimpleNamespace(**{**vars(ev[0]), "setup": 2})
    assert len(run_lr(S, w, ev + [twin], cs)) == 1


def test_level_reversal_states_and_no_direction_rule(S):
    for st in (RANGING, EMERGING, TREND, POSSIBLE_REVERSAL):
        for d, price in ((BUY, 100), (SELL, 120)):            # either way, against the direction rule too
            i = check(S, "GBPUSD", cand(LEVEL_REVERSAL, d, price), state(st, UP), PIVOT, EMA100)
            assert i.allowed and "the direction rule does not apply to level reversal" in i.steps[-1], (st, d)
    assert "does not allow level reversal" in check(S, "GBPUSD", cand(LEVEL_REVERSAL, SELL), state(CONSOLIDATION), PIVOT,
                                                    EMA100).blocked_by
    off = changed(S, "switches", level_reversal=False)
    assert "STRATEGY_LEVEL_REVERSAL is off" in check(off, "GBPUSD", cand(LEVEL_REVERSAL, SELL), state(TREND, UP), PIVOT,
                                                     EMA100).blocked_by
    from analyser.states import ALLOWED
    assert all("level reversal" in ALLOWED[x] for x in (RANGING, EMERGING, TREND, POSSIBLE_REVERSAL))
    assert ALLOWED[CONSOLIDATION] == ()


def test_level_reversal_exits_hours_and_news(S):
    from strategies.common import counts_towards_most_at_once, profit_lock, stop_loss_pips, take_profit_pips
    assert take_profit_pips(S, LEVEL_REVERSAL, U(2026, 11, 5, 9, 0), "GBPUSD", BOE_CAL) == 20     # 20 on any day
    assert stop_loss_pips(S, LEVEL_REVERSAL) == 6 and profit_lock(S, LEVEL_REVERSAL) is None
    i = check(S, "GBPUSD", Candidate(LEVEL_REVERSAL, SELL, START, D(96), ["made up"], context={"stop_price": D(110)}),
              state(TREND, UP), PIVOT, EMA100)
    assert stop_price(S, i) == D(110) and i.context["stop_price"] == D(110)
    assert stop_price(S, check(S, "GBPUSD", cand(EMA_PULLBACK, SELL), state(TREND, DOWN), PIVOT, EMA100)) is None
    assert may_open(S, "GBPUSD", LEVEL_REVERSAL, U(2026, 11, 3, 6, 0), []) == []
    for t in (U(2026, 11, 3, 5, 55), U(2026, 11, 3, 20, 30), U(2026, 11, 3, 23, 0)):
        assert "outside the trading hours 06:00 to 20:30 UK" in may_open(S, "GBPUSD", LEVEL_REVERSAL, t, [])
    assert any("big-news window" in r for r in may_open(S, "GBPUSD", LEVEL_REVERSAL, U(2026, 11, 5, 11, 50), BOE_CAL))
    assert closed_before_big_news(LEVEL_REVERSAL) is True
    assert closed_on_level_rejection(LEVEL_REVERSAL) is False
    assert forced_close_at(S, LEVEL_REVERSAL, U(2026, 11, 3, 10, 0)) == U(2026, 11, 3, 20, 30)
    assert counts_towards_most_at_once(LEVEL_REVERSAL) is True


def test_the_replay_runs_the_level_reversal(monkeypatch, S):
    """The replay gives the level reversal the strategies' own rejection watcher and its events."""
    seen = []

    class Spy(LevelReversal):
        def on_candle(self, c, watcher, events):
            seen.append((c.start, watcher, list(events)))
            return []
    monkeypatch.setattr(replay_mod, "LevelReversal", Spy)
    fake_replay(monkeypatch, S, {0: (TREND, DOWN)})
    assert len(seen) == len(PAUSE) + 1 and all(w is seen[0][1] for _, w, _ in seen)
    assert isinstance(seen[0][1], RejectionWatcher)


# ---- the trend day's take profit (design 2.4 and 4; owner, 8 November 2026) ---------------------

def test_on_a_trend_day_ema_pullback_and_slow_grind_in_its_direction_get_100_pips(S):
    from strategies.common import take_profit_pips
    t = U(2026, 11, 4, 9, 0)                                  # no big news that day
    for name, usual in ((EMA_PULLBACK, 30), (SLOW_GRIND, 20)):
        assert take_profit_pips(S, name, t, "GBPUSD", [], direction=SELL, trend_day="down") == 100
        assert take_profit_pips(S, name, t, "GBPUSD", [], direction=BUY, trend_day="up") == 100
        assert take_profit_pips(S, name, t, "GBPUSD", [], direction=BUY, trend_day="down") == usual    # against it
        assert take_profit_pips(S, name, t, "GBPUSD", [], direction=SELL, trend_day="up") == usual
        assert take_profit_pips(S, name, t, "GBPUSD", [], direction=SELL, trend_day=None) == usual     # not a trend day
        assert take_profit_pips(S, name, t, "GBPUSD", [], direction=SELL) == usual


def test_the_trend_day_changes_nothing_for_the_other_strategies(S):
    from strategies.common import take_profit_pips
    t = U(2026, 11, 4, 9, 0)
    for name, usual in ((BREAKOUT, 50), (LEVEL_REVERSAL, 20), (BOLLINGER_BOUNCE, 100), (RANGE_TRADE, 100)):
        for d, td in ((SELL, "down"), (BUY, "up")):
            assert take_profit_pips(S, name, t, "GBPUSD", [], direction=d, trend_day=td) == usual
