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
    (RANGING, {RANGE_TRADE}),
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
def test_in_a_trend_only_the_trends_direction(S, st, name):
    assert check(S, "GBPUSD", cand(name, SELL), state(st, DOWN), PIVOT, EMA100).allowed
    against = check(S, "GBPUSD", cand(name, BUY, 120), state(st, DOWN), PIVOT, EMA100)
    assert not against.allowed and "only in the trend's direction" in against.blocked_by
    assert check(S, "GBPUSD", cand(name, BUY, 120), state(st, UP), PIVOT, EMA100).allowed


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
def test_the_direction_rule_uses_the_entry_price(S, price, pivot, ema100, buy_ok, sell_ok, said):
    piv = D(pivot) if pivot is not None else None
    e = D(ema100) if ema100 is not None else None
    b = check(S, "GBPUSD", cand(RANGE_TRADE, BUY, price), state(RANGING), piv, e)
    s = check(S, "GBPUSD", cand(RANGE_TRADE, SELL, price), state(RANGING), piv, e)
    assert (b.allowed, s.allowed, b.direction_rule) == (buy_ok, sell_ok, said)
    if not buy_ok:
        assert "the direction rule says" in b.blocked_by


def test_the_direction_rule_applies_to_bounces_in_a_possible_reversal_too(S):
    i = check(S, "GBPUSD", cand(BOLLINGER_BOUNCE, BUY, 100), state(POSSIBLE_REVERSAL, UP), PIVOT, EMA100)
    assert not i.allowed and "sell side" in i.blocked_by


def test_every_reason_for_blocking_is_given(S):
    s = changed(S, "switches", ema_pullback=False)
    i = check(s, "GBPUSD", cand(EMA_PULLBACK, BUY, 100), state(CONSOLIDATION), PIVOT, EMA100)
    assert i.blocked_by.count(";") == 2 and "consolidation" in i.blocked_by


# ---- 3.1 slow grind -------------------------------------------------------------------------

EMA21 = D(120)          # above every made-up price: a sell pause stays below it


def grind(s, candles, ema=EMA21):
    g = SlowGrind(s)
    return [(c, x) for c in candles for x in g.on_candle(c, ema)]


SELL_PAUSE = [C(0, 105, 106, 100, 101),      # red
              C(1, 101, 103, 100.5, 102),    # green: the pause starts; low 100 not broken
              C(2, 102, 103, 101, 101.5),    # 2nd candle without a new low
              C(3, 101.5, 102.5, 100.2, 102)]  # 3rd: a pause


def test_slow_grind_sell_opens_when_price_breaks_the_pause_low(S):
    got = grind(S, SELL_PAUSE + [C(4, 102, 102, 99, 99.5)])
    assert len(got) == 1
    c, x = got[0]
    assert (x.strategy, x.direction, x.entry_price, x.time) == (SLOW_GRIND, SELL, D(100), c.start)
    assert "a pause starts" in x.steps[0] and "a pause: 3 candles" in x.steps[1] and "broke below" in x.steps[2]


def test_slow_grind_a_candle_opening_below_the_low_enters_at_its_open(S):
    (_, x), = grind(S, SELL_PAUSE + [C(4, 99, 99.5, 98, 98.5)])
    assert x.entry_price == D(99)


def test_slow_grind_needs_three_candles_before_the_break(S):
    assert grind(S, SELL_PAUSE[:3] + [C(3, 101.5, 102, 99, 99.5)]) == []


def test_slow_grind_the_pause_length_is_a_setting(S):
    s = changed(S, "slow_grind", min_pause_candles=4)
    assert grind(s, SELL_PAUSE + [C(4, 102, 102, 99, 99.5)]) == []
    assert len(grind(s, SELL_PAUSE + [C(4, 102, 102.5, 101, 101.5), C(5, 101.5, 101.5, 99, 99.5)])) == 1


def test_slow_grind_a_close_above_the_21_ema_cancels(S):
    ema = {i: EMA21 for i in range(6)}
    ema[4] = D(101)                      # candle 4 closes 102, above this EMA
    g, out = SlowGrind(S), []
    for i, c in enumerate(SELL_PAUSE + [C(4, 102, 102.5, 101, 102), C(5, 102, 102, 99, 99.5)]):
        out += g.on_candle(c, ema[i])
    assert out == []


def test_slow_grind_no_time_limit(S):
    waiting = [C(4 + k, 102, 103, 101, 101.5) for k in range(30)]
    assert len(grind(S, SELL_PAUSE + waiting + [C(34, 101.5, 101.5, 99, 99.5)])) == 1


def test_slow_grind_no_size_test(S):
    tiny = [C(0, 100.2, 100.3, 100, 100.1), C(1, 100.1, 100.2, 100.05, 100.15),
            C(2, 100.15, 100.2, 100.1, 100.12), C(3, 100.12, 100.2, 100.1, 100.15), C(4, 100.15, 100.15, 99.9, 99.95)]
    assert [x.entry_price for _, x in grind(S, tiny)] == [D(100)]


def test_slow_grind_buy_is_the_mirror_image(S):
    m = lambda x: 200 - x  # noqa: E731     (a mirror: highs become lows)
    mirrored = [C(i, m(c.sell_open), m(c.sell_low), m(c.sell_high), m(c.sell_close))
                for i, c in enumerate(SELL_PAUSE + [C(4, 102, 102, 99, 99.5)])]
    (_, x), = grind(S, mirrored, ema=D(80))
    assert (x.direction, x.entry_price) == (BUY, D(100))


def test_slow_grind_a_pause_above_the_ema_is_no_sell_pause(S):
    assert grind(S, SELL_PAUSE + [C(4, 102, 102, 99, 99.5)], ema=D(90)) == []


# ---- 3.2 EMA pullback -----------------------------------------------------------------------

class Hourly:
    def __init__(self, direction=BUY, qualified=True):
        self.t = HourlyTrend(direction, qualified, "made-up hourly trend")

    def at(self, t):
        return self.t


BEFORE = [C(i, 100 + i, 102 + i, 99 + i, 101 + i) for i in range(5)]   # highest high 106 (candle 4)
FAST, SLOW = D(103), D(98)


def pullback(s, candles, hourly=None, fast=FAST, slow=SLOW, early=D(90)):
    """The 8 EMA is `early` (far from price) until candle 4, so only candle 5 can be the touch."""
    p, out = EmaPullback(s, hourly or Hourly()), []
    for i, c in enumerate(candles):
        out += p.on_candle(c, fast if i >= 4 else early, slow)
    return out


def test_ema_pullback_buy_entry_is_3_pips_above_the_five_highs_before(S):
    touch = C(5, 104, 104.5, 102.5, 103.5)          # the low reaches the 8 EMA 103; closes above the 21 EMA 98
    (x,) = pullback(S, BEFORE + [touch, C(6, 103.5, 109.5, 103, 109)])
    assert (x.strategy, x.direction, x.entry_price, x.time) == (EMA_PULLBACK, BUY, D(109), C(6, 0, 0, 0, 0).start)
    assert x.steps[0].startswith("step 0") and "dropped to the 5-minute 8 EMA 103" in x.steps[1]
    assert x.steps[2].startswith("entry 109: 3 pips above the highest high of the 5 candles")


def test_ema_pullback_price_may_cross_the_8_and_13_ema(S):
    touch = C(5, 104, 104.5, 99, 101)               # far through the 8 (and a 13 between) but closes above the 21
    assert len(pullback(S, BEFORE + [touch, C(6, 101, 110, 101, 109)])) == 1


def test_ema_pullback_needs_the_touch(S):
    no_touch = C(5, 106, 107, 103.5, 106)
    assert pullback(S, BEFORE + [no_touch, C(6, 106, 110, 105, 109)]) == []


def test_ema_pullback_a_close_below_the_21_ema_cancels(S):
    touch = C(5, 104, 104.5, 102.5, 103.5)
    assert pullback(S, BEFORE + [C(5, 104, 104.5, 97, 97.5), C(6, 97.5, 110, 97, 109)]) == []   # the touch candle
    assert pullback(S, BEFORE + [touch, C(6, 103.5, 104, 97, 97.5), C(7, 97.5, 110, 97, 109)]) == []


def test_ema_pullback_expires_after_20_minutes(S):
    touch = C(5, 104, 104.5, 102.5, 103.5)
    waits = [C(6 + k, 103.5, 105, 102, 104) for k in range(3)]      # 5, 10 and 15 minutes after the touch
    assert len(pullback(S, BEFORE + [touch] + waits[:2] + [C(8, 104, 110, 104, 109)])) == 1     # 15 minutes: in time
    assert pullback(S, BEFORE + [touch] + waits + [C(9, 104, 110, 104, 109)]) == []             # 20 minutes: expired


def test_ema_pullback_expiry_and_entry_are_settings(S):
    s = changed(S, "ema_pullback", setup_expires_after_minutes=30, entry_beyond_pips=1, entry_lookback_candles=2)
    touch = C(5, 104, 104.5, 102.5, 103.5)
    waits = [C(6 + k, 103.5, 105, 102, 104) for k in range(3)]
    (x,) = pullback(s, BEFORE + [touch] + waits + [C(9, 104, 110, 104, 109)])
    assert x.entry_price == D(107)                  # 1 pip above the highest of the last 2 (106)


def test_ema_pullback_a_candle_opening_past_the_entry_enters_at_its_open(S):
    (x,) = pullback(S, BEFORE + [C(5, 104, 104.5, 102.5, 103.5), C(6, 110, 111, 109.5, 110.5)])
    assert x.entry_price == D(110)


def test_ema_pullback_needs_the_hourly_trend(S):
    candles = BEFORE + [C(5, 104, 104.5, 102.5, 103.5), C(6, 103.5, 110, 103, 109)]
    assert pullback(S, candles, Hourly(BUY, qualified=False)) == []
    assert pullback(S, candles, Hourly(None, qualified=False)) == []
    assert pullback(S, candles, Hourly(SELL)) == []


def test_ema_pullback_sell_is_the_mirror_image(S):
    m = lambda x: 200 - x  # noqa: E731
    candles = BEFORE + [C(5, 104, 104.5, 102.5, 103.5), C(6, 103.5, 110, 103, 109)]
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
    t = HourlyTrendReader(S, candles)
    assert t.at(candles[2].end).why == "not enough hourly candles"


# ---- 3.3 and 3.4: from the shared rejection part --------------------------------------------

def band(c, upper=110, lower=90):
    return Band(c.start, D(100), D(upper), D(lower))


BOUNCE_SELL = [C(0, 106, 112, 105, 108),       # pierces the upper band 110
               C(1, 108, 109, 103, 104),       # the first red candle: the reversal candle
               C(2, 104, 105, 100, 101),       # closes below the reversal low 103: the confirmation candle
               C(3, 101, 101.5, 98, 99)]       # goes below the confirmation low 100: the trigger


def watch(s, candles):
    w, out = RejectionWatcher(s), []
    for c in candles:
        ev = w.on_candle(c, band(c), None)
        out += bounce_candidates(w, ev) + range_candidates(w, ev)
    return out


def test_bollinger_bounce_takes_the_rejection_parts_trigger(S):
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


def test_range_trade_takes_the_rejection_parts_trigger(S):
    candles = [C(0, 106, 112, 105, 108), C(1, 108, 109, 103, 104), C(2, 104, 104.5, 102, 102.5)]
    got = [x for x in watch(S, candles) if x.strategy == RANGE_TRADE]
    assert [(x.direction, x.entry_price, x.time) for x in got] == [(SELL, D(103), candles[2].start)]


def test_range_trade_cancelled_above_the_rejection_high_has_no_idea(S):
    candles = [C(0, 106, 112, 105, 108), C(1, 108, 109, 103, 104), C(2, 104, 110, 103.5, 109.5)]
    assert [x for x in watch(S, candles) if x.strategy == RANGE_TRADE] == []


# ---- the replay: the checks when a setup starts and again at entry -----------------------------

def fake_replay(monkeypatch, S, states):
    """A slow grind sell: the pause starts at candle 1 (red 0, green 1), counts at 3, and price
    breaks it on candle 4. `states`: {candle number: state from that candle on}."""
    candles = SELL_PAUSE + [C(4, 102, 102, 99, 99.5)]
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
    return replay_mod.run(S, None, START, START + timedelta(hours=1))


def grind_ideas(r):
    return [i for i in r.ideas if i.strategy == SLOW_GRIND and i.direction == SELL]


def test_replay_allowed_at_start_and_at_entry_gives_an_idea(monkeypatch, S):
    r = fake_replay(monkeypatch, S, {0: (TREND, DOWN)})
    (i,) = grind_ideas(r)
    assert i.allowed and (i.state, i.state_direction) == (TREND, DOWN)
    assert any(x.startswith("setup start allowed: slow grind sell in a trend down") for x in i.steps)
    assert i.steps[-1].startswith("allowed at entry")


def test_replay_a_setup_that_starts_when_not_allowed_is_not_started(monkeypatch, S):
    r = fake_replay(monkeypatch, S, {3: (TREND, DOWN)})      # consolidation when the pause starts (candle 1)
    assert grind_ideas(r) == []
    assert any(st == SLOW_GRIND and d == SELL and "consolidation" in why for _, st, d, why in r.not_started)
    assert any("not started" in txt for _, d, txt in r.notes[SLOW_GRIND] if d == SELL)


def test_replay_a_setup_starting_at_a_close_uses_the_state_after_that_candle(monkeypatch, S):
    (i,) = grind_ideas(fake_replay(monkeypatch, S, {1: (TREND, DOWN)}))   # decided on the pause's start candle
    assert i.allowed


def test_replay_checked_again_at_entry_with_the_state_after_the_last_finished_candle(monkeypatch, S):
    r = fake_replay(monkeypatch, S, {0: (TREND, DOWN), 3: (CONSOLIDATION, NONE)})
    (i,) = grind_ideas(r)
    assert not i.allowed and "consolidation" in i.blocked_by
    (j,) = grind_ideas(fake_replay(monkeypatch, S, {0: (TREND, DOWN), 4: (CONSOLIDATION, NONE)}))
    assert j.allowed                                          # decided on the entry candle itself: too late to matter


# ---- the start check inside each strategy ---------------------------------------------------

def refuse(*a):
    return False, "not allowed (made up)"


def test_slow_grind_a_refused_start_starts_no_pause(S):
    g = SlowGrind(S, refuse)
    out = [x for c in SELL_PAUSE + [C(4, 102, 102, 99, 99.5)] for x in g.on_candle(c, EMA21)]
    assert out == [] and any("not started: not allowed (made up)" in t for _, _, t in g.notes)


def test_ema_pullback_a_refused_touch_starts_no_setup(S):
    p, out = EmaPullback(S, Hourly(), refuse), []
    for i, c in enumerate(BEFORE + [C(5, 104, 104.5, 102.5, 103.5), C(6, 103.5, 110, 103, 109)]):
        out += p.on_candle(c, FAST if i >= 4 else D(90), SLOW)
    assert out == [] and any("setup not started" in t for _, _, t in p.notes)


def test_ema_pullback_start_check_gets_the_touch_price_while_the_candle_forms(S):
    seen = []
    p = EmaPullback(S, Hourly(), lambda *a: (seen.append(a), (True, "ok"))[1])
    for i, c in enumerate(BEFORE + [C(5, 104, 104.5, 102.5, 103.5)]):
        p.on_candle(c, FAST if i >= 4 else D(90), SLOW)
    (strategy, d, c, price, during), = seen
    assert (strategy, d, price, during) == (EMA_PULLBACK, BUY, FAST, True)


def test_bounce_a_refused_pierce_starts_no_setup(S):
    w = RejectionWatcher(S, may_start=refuse)
    for c in BOUNCE_SELL:
        w.on_candle(c, band(c), None)
    assert w.setups == [] and w.not_started[0][:2] == ("bounce", SELL)


# ---- 3.3: several bounce setups in the same direction ---------------------------------------

TWO_BOUNCES = [C(0, 106, 112, 105, 108),       # pierce 1 (band 110)
               C(1, 108, 109, 103, 104),       # reversal 1 (cancel above 109)
               C(2, 104, 105, 100, 101),       # confirmation 1 (closes below 103); the band is down to 104.5: pierce 2
               C(3, 101, 101.5, 98.5, 99)]     # trigger 1 below 100; reversal 2 (red)
TWO_BANDS = [110, 110, D("104.5"), 110]


def test_bounce_several_setups_per_direction_for_the_strategies(S):
    w = RejectionWatcher(S, several=frozenset({"bounce"}))
    for c, up in zip(TWO_BOUNCES, TWO_BANDS):
        w.on_candle(c, band(c, upper=up), None)
    sells = [st for st in w.setups if st.version == "bounce" and st.direction == SELL]
    assert len(sells) == 2 and sells[1].pierce.start == TWO_BOUNCES[2].start
    assert sells[0].status == "triggered" and sells[1].stage == "confirmation"


def test_bounce_the_analysers_watcher_keeps_one_setup_per_direction(S):
    w = RejectionWatcher(S)
    for c, up in zip(TWO_BOUNCES, TWO_BANDS):
        w.on_candle(c, band(c, upper=up), None)
    assert len([st for st in w.setups if st.version == "bounce" and st.direction == SELL]) == 1


def test_bounce_a_fresh_pierce_while_waiting_for_the_reversal_restarts_it_not_a_second_setup(S):
    w = RejectionWatcher(S, several=frozenset({"bounce"}))
    for c in [C(0, 106, 112, 105, 108), C(1, 108, 113, 107, 112)]:     # green: pierces again
        w.on_candle(c, band(c), None)
    sells = [st for st in w.setups if st.version == "bounce" and st.direction == SELL]
    assert len(sells) == 1 and sells[0].pierce.start == START + timedelta(minutes=5)


# ---- 3.1: a pause starts with two candles in opposite directions, in either order -----------

def test_slow_grind_green_then_red_also_starts_a_pause(S):
    candles = [C(0, 101, 103, 100, 102.5),      # green
               C(1, 102.5, 103, 100.5, 101),    # red: no new low below 100, closes below the EMA: counts
               C(2, 101, 102, 100.2, 101.5), C(3, 101.5, 102.5, 100.1, 102), C(4, 102, 102, 99, 99.5)]
    (_, x), = grind(S, candles)
    assert (x.direction, x.entry_price) == (SELL, D(100)) and "green then red" in x.steps[0]


def test_slow_grind_no_extra_start_conditions(S):
    # the second candle makes a new low: the pause still starts, its low is the lower one, and it does not count
    candles = [C(0, 105, 106, 100, 101), C(1, 99.5, 101, 99, 100.5), C(2, 100.5, 101, 99.5, 100),
               C(3, 100, 100.8, 99.2, 100.5), C(4, 100.5, 101, 99.3, 100.2), C(5, 100.2, 100.2, 98, 98.5)]
    (_, x), = grind(S, candles)
    assert x.entry_price == D(99) and "the second candle counts" not in x.steps[0]
    # the start candles may close above the EMA (a later close above it still cancels)
    g = SlowGrind(S)
    g.on_candle(C(0, 105, 106, 100, 101), D(100.5))
    g.on_candle(C(1, 101, 103, 100.5, 102), D(100.5))
    assert g.pause[SELL] is not None and g.pause[SELL].count == 0


# ---- 3.2: the entry counts back from the first candle that reached the 8 EMA -----------------

def test_ema_pullback_entry_from_the_candles_before_the_first_candle_to_reach_the_8_ema(S):
    candles = BEFORE + [C(5, 104, 120, 97, 97.5),         # reaches the 8 EMA but closes below the 21: no setup
                        C(6, 99, 104, 98.5, 103),          # reaches it again: the setup
                        C(7, 103, 110, 103, 109)]
    (x,) = pullback(S, candles)
    assert x.entry_price == D(109)                       # BEFORE's highest high 106 + 3, not candle 5's 120 + 3
    assert "the first candle to reach the 8 EMA was" in x.steps[1]


def test_ema_pullback_a_candle_that_does_not_reach_the_8_ema_ends_the_run(S):
    candles = BEFORE + [C(5, 104, 120, 97, 97.5),         # reaches it (closes below the 21)
                        C(6, 104, 106, 103.5, 105),        # does not reach it: the run ends
                        C(7, 105, 108, 102.5, 104),        # a new run starts here: the setup
                        C(8, 104, 124, 104, 123)]
    (x,) = pullback(S, candles)
    assert x.entry_price == D(123)                       # highest high of candles 2-6 is candle 5's 120, + 3
