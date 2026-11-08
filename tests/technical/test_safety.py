"""Technical tests for the safety rules (design sections 4, 6 and 7), with made-up ideas, open trades,
dealing rules and times. Nothing here contacts IG or trades."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from config.settings_loader import load_settings
from safety.rules import DealingRules, OpenTrade, Order, decide, order_for
from strategies.common import (BOLLINGER_BOUNCE, BREAKOUT, BUY, EMA_PULLBACK, LEVEL_REVERSAL, RANGE_TRADE, SELL,
                               SLOW_GRIND, Idea)

U = lambda *a: datetime(*a, tzinfo=timezone.utc)  # noqa: E731
WED = U(2026, 11, 4, 10, 0)                         # Wednesday 10:00 UK (GMT), no news
BOE_CAL = [{"time_utc": "2026-11-05T12:00:00Z", "country": "GB", "event": "BoE Interest Rate Decision",
            "estimate": 4.0, "prev": 4.0, "actual": None, "impact": "high", "unit": "%"}]
ALL = (EMA_PULLBACK, BOLLINGER_BOUNCE, RANGE_TRADE, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL)


class Over:
    """The real settings with some values of sections changed."""
    def __init__(self, base, **sections):
        self.base, self.sections = base, {}
        for name, values in sections.items():
            items = {k: v for k, v in vars(getattr(base, name)).items() if not k.startswith("_")}
            self.sections[name] = SimpleNamespace(**(items | values))

    def __getattr__(self, name):
        return self.sections[name] if name in self.sections else getattr(self.base, name)


@pytest.fixture
def S(pretend_switches):
    s = load_settings(switches_from=pretend_switches).for_pair("GBPUSD")
    return Over(s, switches={k: True for k in ("slow_grind", "ema_pullback", "bollinger_bounce", "range_trade",
                                                 "breakout", "level_reversal")})


def idea(strategy, direction=SELL, t=WED, price="13400.0", allowed=True, blocked="", context=None):
    ctx = context if context is not None else ({"stop_price": D("13410.0")} if strategy == LEVEL_REVERSAL else {})
    return Idea("GBPUSD", strategy, direction, t, D(price), "trend", "down", None, "sell side", ["made up"],
                allowed, blocked, ctx)


def rules(t=WED, value="2", unit="POINTS", age=5):
    return DealingRules(D(value), unit, t - timedelta(minutes=age))


def go(S, i, open_trades=(), t=None, paused=False, dealing="fresh", size=None, stop=None, calendar=()):
    t = t or i.time
    o = order_for(S, i)
    if size is not None or stop is not None:
        o = Order(i, D(size) if size is not None else o.size_gbp_per_pip, D(stop) if stop is not None else o.stop_pips)
    dr = rules(t) if dealing == "fresh" else dealing
    return decide(S, o, list(open_trades), D("10000"), dr, t, paused, list(calendar))


def opened(strategy, direction=BUY):
    return OpenTrade(strategy, direction, WED - timedelta(hours=1))


# ---- everything allowed ----------------------------------------------------------------------

@pytest.mark.parametrize("strategy", ALL)
def test_every_strategy_may_open_when_every_check_passes(S, strategy):
    d = go(S, idea(strategy))
    assert d.allowed and d.reasons == []


# ---- the pause switch, the idea's checks, the switch -------------------------------------------

@pytest.mark.parametrize("strategy", ALL)
def test_the_pause_switch_blocks_every_new_trade(S, strategy):
    d = go(S, idea(strategy), paused=True)
    assert not d.allowed and d.reasons == ["the pause switch is on: no new trades"]


def test_a_blocked_idea_is_refused_with_its_reason(S):
    d = go(S, idea(BOLLINGER_BOUNCE, allowed=False, blocked="the analyser's state is consolidation"))
    assert d.reasons == ["the idea was blocked: the analyser's state is consolidation"]


@pytest.mark.parametrize("strategy,switch", [(SLOW_GRIND, "slow_grind"), (EMA_PULLBACK, "ema_pullback"),
                                             (BOLLINGER_BOUNCE, "bollinger_bounce"), (RANGE_TRADE, "range_trade"),
                                             (BREAKOUT, "breakout"), (LEVEL_REVERSAL, "level_reversal")])
def test_the_switch_is_checked_again_even_for_an_allowed_idea(S, strategy, switch):
    s = Over(S, switches=vars(S.switches) | {switch: False})
    d = go(s, idea(strategy))
    assert d.reasons == [f"its switch STRATEGY_{switch.upper()} is off"]


# ---- hours, news and Friday rules (design 4 and 6) ------------------------------------------------

@pytest.mark.parametrize("strategy,t,ok", [
    (BOLLINGER_BOUNCE, U(2026, 11, 4, 5, 55), False), (BOLLINGER_BOUNCE, U(2026, 11, 4, 6, 0), True),
    (BOLLINGER_BOUNCE, U(2026, 11, 4, 20, 30), False), (RANGE_TRADE, U(2026, 11, 4, 20, 25), True),
    (RANGE_TRADE, U(2026, 11, 4, 22, 0), False), (LEVEL_REVERSAL, U(2026, 11, 4, 5, 0), False),
    (BREAKOUT, U(2026, 11, 4, 21, 0), False), (BREAKOUT, U(2026, 11, 4, 20, 25), True),
    (EMA_PULLBACK, U(2026, 11, 4, 3, 0), True), (EMA_PULLBACK, U(2026, 11, 4, 23, 0), True),
    (SLOW_GRIND, U(2026, 11, 4, 3, 0), True), (SLOW_GRIND, U(2026, 11, 4, 20, 30), False),
    (SLOW_GRIND, U(2026, 11, 4, 23, 55), False), (SLOW_GRIND, U(2026, 11, 5, 0, 0), True),
])
def test_each_strategys_hours(S, strategy, t, ok):
    d = go(S, idea(strategy, t=t))
    assert d.allowed is ok, d.reasons


def test_big_news_stops_the_bounce_range_trade_and_level_reversal_only(S):
    t = U(2026, 11, 5, 11, 50)                       # BoE at 12:00: no new trades 11:45 to 12:30
    for strategy in (BOLLINGER_BOUNCE, RANGE_TRADE, LEVEL_REVERSAL):
        d = go(S, idea(strategy, t=t), calendar=BOE_CAL)
        assert any("big-news window: BoE Interest Rate Decision" in r for r in d.reasons), strategy
    for strategy in (EMA_PULLBACK, BREAKOUT, SLOW_GRIND):
        assert go(S, idea(strategy, t=t), calendar=BOE_CAL).allowed, strategy


@pytest.mark.parametrize("t", [U(2026, 11, 6, 20, 30), U(2026, 11, 6, 21, 50), U(2026, 10, 23, 19, 30)])  # last: BST
def test_no_ema_pullback_after_20_30_uk_on_friday(S, t):
    assert any("after 20:30 UK on Friday" in r for r in go(S, idea(EMA_PULLBACK, t=t)).reasons)


def test_nothing_opens_while_the_market_is_closed(S):
    for strategy in ALL:
        assert "the market is closed" in go(S, idea(strategy, t=U(2026, 11, 7, 12, 0))).reasons


# ---- trades open at once (design 6) ----------------------------------------------------------------

@pytest.mark.parametrize("strategy", (RANGE_TRADE, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL))
def test_one_trade_at_a_time_for_each_strategy(S, strategy):
    d = go(S, idea(strategy), [opened(strategy)])
    assert d.reasons == [f"{strategy} already has 1 trade(s) open (at most 1)"]
    assert go(S, idea(strategy), [opened(s) for s in (RANGE_TRADE, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL)
                                  if s != strategy]).allowed


def test_the_bounce_may_have_one_each_way(S):
    assert go(S, idea(BOLLINGER_BOUNCE, SELL), [opened(BOLLINGER_BOUNCE, BUY)]).allowed
    d = go(S, idea(BOLLINGER_BOUNCE, BUY), [opened(BOLLINGER_BOUNCE, BUY)])
    assert d.reasons == ["Bollinger bounce already has 1 buy trade(s) open (at most 1 each way)"]
    d = go(S, idea(BOLLINGER_BOUNCE, SELL), [opened(BOLLINGER_BOUNCE, BUY), opened(BOLLINGER_BOUNCE, SELL)])
    assert not d.allowed
    s = Over(S, limits=vars(S.limits) | {"bollinger_bounce_extra_opposite_direction_trades": 0})
    assert "Bollinger bounce already has 1 trade(s) open (at most 1)" in \
        go(s, idea(BOLLINGER_BOUNCE, SELL), [opened(BOLLINGER_BOUNCE, BUY)]).reasons


def test_the_ema_pullback_has_no_limit_of_its_own(S):
    assert go(S, idea(EMA_PULLBACK), [opened(EMA_PULLBACK) for _ in range(12)]).allowed


FIVE = [opened(BOLLINGER_BOUNCE, BUY), opened(BOLLINGER_BOUNCE, SELL), opened(RANGE_TRADE), opened(BREAKOUT),
        opened(SLOW_GRIND)]


def test_a_sixth_counted_trade_is_refused_but_an_ema_pullback_is_not(S):
    d = go(S, idea(LEVEL_REVERSAL), FIVE)
    assert d.reasons == ["5 trades open that count towards the most at once (5; EMA pullback trades not counted)"]
    assert go(S, idea(EMA_PULLBACK), FIVE).allowed


def test_ema_pullback_trades_do_not_count_towards_the_5(S):
    assert go(S, idea(LEVEL_REVERSAL), FIVE[:4] + [opened(EMA_PULLBACK) for _ in range(6)]).allowed


def test_the_most_at_once_is_a_setting(S):
    s = Over(S, limits=vars(S.limits) | {"max_open_trades": 2})
    assert "2 trades open that count towards the most at once (2; EMA pullback trades not counted)" in \
        go(s, idea(LEVEL_REVERSAL), FIVE[:2]).reasons
    assert S.limits.max_open_trades == 5


# ---- size and stop ---------------------------------------------------------------------------------

def test_the_size_is_10_pounds_a_pip(S):
    assert order_for(S, idea(BREAKOUT)).size_gbp_per_pip == D(10)
    assert go(S, idea(BREAKOUT), size="5").reasons == ["the size is £5 a pip, not £10"]
    assert go(S, idea(BREAKOUT), size="10.0").allowed


def test_each_strategys_stop_in_its_order(S):
    assert [order_for(S, idea(n)).stop_pips for n in ALL] == [D(12), D(6), D(6), D(6), D(15), D(10)]
    lr = idea(LEVEL_REVERSAL, BUY, price="13400.0", context={"stop_price": D("13387.5")})
    assert order_for(S, lr).stop_pips == D("12.5")                       # from the entry to its stop price


def test_the_stop_must_be_at_least_igs_minimum(S):
    i8 = rules(value="8")
    d = go(S, idea(BOLLINGER_BOUNCE), dealing=i8)
    assert d.reasons == ["the stop (6.0 pips) is closer than IG's minimum stop distance (8.0 pips)"]
    assert go(S, idea(EMA_PULLBACK), dealing=i8).allowed                       # 12 pips
    assert go(S, idea(SLOW_GRIND), dealing=i8).allowed                         # 15 pips
    assert go(S, idea(BOLLINGER_BOUNCE), dealing=rules(value="6")).allowed      # exactly the minimum


def test_igs_minimum_as_a_percentage_of_the_price(S):
    d = go(S, idea(BREAKOUT, price="13400.0"), dealing=rules(value="0.05", unit="PERCENTAGE"))   # 6.7 pips
    assert d.reasons == ["the stop (6.0 pips) is closer than IG's minimum stop distance (6.7 pips)"]
    assert go(S, idea(EMA_PULLBACK), dealing=rules(value="0.05", unit="PERCENTAGE")).allowed


def test_missing_old_or_odd_dealing_rules_refuse(S):
    assert go(S, idea(EMA_PULLBACK), dealing=None).reasons == \
        ["IG's dealing rules for the market are not known: its minimum stop distance cannot be checked"]
    old = rules(age=61)
    assert go(S, idea(EMA_PULLBACK), dealing=old).reasons == \
        ["IG's dealing rules are out of date (fetched 61 minutes ago; at most 60)"]
    assert go(S, idea(EMA_PULLBACK), dealing=rules(age=60)).allowed
    assert "unknown unit" in go(S, idea(EMA_PULLBACK), dealing=rules(unit="PIPS")).reasons[0]


def test_dealing_rules_from_igs_market_reply():
    t = U(2026, 11, 4, 9, 0)
    r = DealingRules.from_ig({"dealingRules": {"minNormalStopOrLimitDistance": {"unit": "POINTS", "value": 2.0},
                                               "minStepDistance": {"unit": "POINTS", "value": 1.0}}}, t)
    assert (r.min_stop_value, r.min_stop_unit, r.fetched_at) == (D("2.0"), "POINTS", t)


# ---- every reason at once -------------------------------------------------------------------------

def test_every_reason_is_given(S):
    t = U(2026, 11, 5, 11, 50)
    d = go(S, idea(RANGE_TRADE, t=t, allowed=False, blocked="made up"), [opened(RANGE_TRADE)], paused=True,
           size="20", dealing=None, calendar=BOE_CAL)
    assert not d.allowed and len(d.reasons) == 6
    assert d.reasons[0] == "the pause switch is on: no new trades"
    assert "the idea was blocked: made up" in d.reasons and "the size is £20 a pip, not £10" in d.reasons
