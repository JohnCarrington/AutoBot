"""Functional tests for the safety rules, on the REAL economic calendar kept on disk (the big news of
5 and 6 November 2026) and the real settings. Contacts nobody; places nothing."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal as D

import pytest

from config.settings_loader import load_settings
from news.finnhub import store_path
from safety.rules import AccountFunds, OpenTrade, decide, order_for
from strategies.common import (BOLLINGER_BOUNCE, BREAKOUT, BUY, EMA_PULLBACK, LEVEL_REVERSAL, RANGE_TRADE, SELL,
                               SLOW_GRIND, Idea)

UTC = timezone.utc
pytestmark = pytest.mark.skipif(not store_path(load_settings()).exists(),
                                reason="the economic calendar is only on the server, once fetched")


@pytest.fixture
def S(pretend_switches):
    return load_settings(switches_from=pretend_switches).for_pair("GBPUSD")


def idea(strategy, t, direction=SELL):
    ctx = {"stop_price": D("13410.0")} if strategy == LEVEL_REVERSAL else {}
    return Idea("GBPUSD", strategy, direction, t, D("13400.0"), "trend", "down", None, "sell side", ["made up"],
                True, "", ctx)


def decision(S, strategy, t, open_trades=()):
    i = idea(strategy, t)
    return decide(S, order_for(S, i), list(open_trades), AccountFunds(D("20000"), t - timedelta(minutes=30)),
                  t, False)                                  # calendar: the real one on disk


@pytest.mark.parametrize("hh,mm", [(11, 45), (12, 0), (12, 15), (12, 29)])      # GMT: UK time = UTC
def test_no_new_bounce_range_trade_or_level_reversal_in_the_boe_window_but_an_ema_pullback(S, hh, mm):
    t = datetime(2026, 11, 5, hh, mm, tzinfo=UTC)
    for strategy in (BOLLINGER_BOUNCE, RANGE_TRADE, LEVEL_REVERSAL):
        d = decision(S, strategy, t)
        assert not d.allowed and any("big-news window" in r and "BoE" in r for r in d.reasons), (strategy, d.reasons)
    assert decision(S, EMA_PULLBACK, t).allowed


@pytest.mark.parametrize("hh,mm", [(11, 40), (12, 30)])
def test_just_outside_the_boe_window_they_may_open_again(S, hh, mm):
    t = datetime(2026, 11, 5, hh, mm, tzinfo=UTC)
    for strategy in (BOLLINGER_BOUNCE, RANGE_TRADE, LEVEL_REVERSAL):
        assert decision(S, strategy, t).allowed, strategy


def test_no_ema_pullback_at_20_45_uk_on_friday_6_november(S):
    d = decision(S, EMA_PULLBACK, datetime(2026, 11, 6, 20, 45, tzinfo=UTC))
    assert d.reasons == ["after 20:30 UK on Friday: no EMA pullback trade is held over the weekend"]


def test_a_sixth_trade_is_refused_when_5_that_count_are_open_but_an_ema_pullback_is_allowed(S):
    t = datetime(2026, 11, 4, 10, 0, tzinfo=UTC)
    ago = t - timedelta(hours=1)
    five = [OpenTrade(BOLLINGER_BOUNCE, BUY, ago, D(6), D(10)), OpenTrade(BOLLINGER_BOUNCE, SELL, ago, D(6), D(10)),
            OpenTrade(RANGE_TRADE, BUY, ago, D(6), D(10)), OpenTrade(BREAKOUT, BUY, ago, D(6), D(10)),
            OpenTrade(SLOW_GRIND, BUY, ago, D(15), D(10))]
    d = decision(S, LEVEL_REVERSAL, t, five)
    assert d.reasons == ["5 trades open that count towards the most at once (5; EMA pullback trades not counted)"]
    assert decision(S, EMA_PULLBACK, t, five).allowed


# ---- one view at a time: the exception days of docs/research/one_view_20261109.md -----------------------

def _store(S):
    from prices.store import CandleStore
    if not (S.candles.folder / "1d").is_dir():
        pytest.skip("the real candle store is only on the server")
    return CandleStore(S.candles.folder, S.candles.compress_after_days)


@pytest.mark.parametrize("day,news,monday", [
    (datetime(2026, 11, 5, 10, 0, tzinfo=UTC), BUY, None),          # Bank of England: expected up
    (datetime(2026, 11, 6, 10, 0, tzinfo=UTC), SELL, None),         # payrolls: expected down
    (datetime(2026, 11, 9, 10, 0, tzinfo=UTC), None, BUY),          # after Friday 6 November fell 107.6 pips
    (datetime(2026, 11, 2, 10, 0, tzinfo=UTC), None, None),         # Friday 30 October moved +8.3 only
    (datetime(2026, 10, 26, 10, 0, tzinfo=UTC), None, None),        # Friday 23 October moved -31.0 only
    (datetime(2026, 11, 4, 10, 0, tzinfo=UTC), None, None)])
def test_the_days_directions_found_by_the_research(S, day, news, monday):
    from analyser.day_direction import day_directions
    d = day_directions(S, _store(S), day)
    assert (d.news, d.trend_day, d.monday) == (news, None, monday)


def test_the_fridays_moves_of_the_research(S):
    from datetime import date
    from analyser.day_direction import friday_move_pips
    store = _store(S)
    assert [friday_move_pips(S, store, date(2026, 11, d)) for d in (2, 9)] == [D("8.3"), D("-107.6")]
    assert friday_move_pips(S, store, date(2026, 10, 26)) == D("-31.0")
