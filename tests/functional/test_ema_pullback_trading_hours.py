"""Functional tests for EMA_PULLBACK_TRADING_HOURS (owner, 21 November 2026), through the live engine with the real
order sender, safety rules and trade manager and a pretend IG (the harness of tests/technical/test_trading.py):

  * new EMA pullback trades only between 06:00 and 20:30 UK time, following UK clocks (GMT in winter, BST in summer);
  * any open EMA pullback trade closed at 20:30 UK every day, not just Friday; nothing held overnight;
  * the 21:55-22:15 rollover pause kept as it is;
  * off (the default): the EMA pullback exactly as before; no other strategy changes either way.
Contacts nobody."""

from datetime import timedelta
from decimal import Decimal as D

import pytest

from strategies.common import (ASIAN_RANGE_BREAKOUT, BOLLINGER_BOUNCE, BOLLINGER_BOUNCE_5M, BREAKOUT, EMA_PULLBACK,
                               LEVEL_REVERSAL, NEW_YORK_OPEN_REVERSAL, RANGE_TRADE, SELL, SESSION_SWEEP, SLOW_GRIND,
                               forced_close_at, may_open)
from tests.technical.test_orders import Over
from tests.technical.test_trading import U, candle, feed, idea, journal, make, tick, trades_rows


def settings(pretend_switches, tmp_path, on):
    from config.settings_loader import load_settings
    s = load_settings(switches_from=pretend_switches).for_pair("GBPUSD")
    return Over(s, switches={k: True for k in ("slow_grind", "ema_pullback", "bollinger_bounce", "range_trade",
                                                 "breakout", "level_reversal")}
                | {"trading": False, "ema_pullback_trading_hours": on},
                orders={"folder": tmp_path / "orders"}, trade_manager={"folder": tmp_path / "tm"},
                safety={"folder": tmp_path / "safety"}, records={"folder": tmp_path / "records"},
                trading={"pause_file": tmp_path / "control" / "pause_new_trades"},
                dashboard={"status_folder": tmp_path / "status"})


@pytest.fixture
def ON(pretend_switches, tmp_path):
    return settings(pretend_switches, tmp_path, True)


@pytest.fixture
def OFF(pretend_switches, tmp_path):
    return settings(pretend_switches, tmp_path, False)


def test_the_switch_is_off_if_left_out_of_env(pretend_switches):
    from config.settings_loader import load_settings
    assert load_settings(switches_from=pretend_switches).switches.ema_pullback_trading_hours is False


# ---- the 20:30 close ------------------------------------------------------------------------------------------

def open_at(S, monkeypatch, t0):
    """An EMA pullback sell opened on the candle starting at t0 (sent when it finishes, t0 + 5 minutes)."""
    cs = [candle(t0 + timedelta(minutes=5 * k), 13400, 13400.5, 13399.5, 13400) for k in range(4)]
    e, ig, tracker, clock, quote = make(S, monkeypatch, cs, {cs[0].start: [idea(EMA_PULLBACK, cs[0].start,
                                                                                price="13400")]},
                                        trading_on=True, clock={"t": t0})
    e.start(t0)
    feed(e, clock, cs[:1])
    (t,) = e.manager.trades.values()
    assert t.strategy == EMA_PULLBACK and t.open
    return e, clock, t


def price_at(e, clock, when):
    clock["t"] = when
    e.on_price(tick(when, 13399.5))


def test_on_a_trade_open_at_20_29_is_closed_at_20_30_uk_on_a_wednesday_gmt(ON, monkeypatch):
    e, clock, t = open_at(ON, monkeypatch, U(2026, 11, 4, 20, 15))           # Wed 4 Nov: GMT, UK time = UTC
    price_at(e, clock, U(2026, 11, 4, 20, 29, 0))
    assert t.open                                                             # 20:29: still open
    price_at(e, clock, U(2026, 11, 4, 20, 30, 0))
    assert not t.open and t.state == "forced close"                           # 20:30: closed
    (closed,) = [r for r in trades_rows(e) if r["event"] == "closed"]
    assert closed["how_closed"] == "forced close" and "20:30 UK close" in closed["close_reason"]
    assert closed["closed_utc"] == "2026-11-04T20:30:00Z"


def test_on_a_trade_open_at_20_29_bst_is_closed_at_20_30_bst(ON, monkeypatch):
    e, clock, t = open_at(ON, monkeypatch, U(2026, 10, 21, 19, 15))          # Wed 21 Oct: BST, 20:15 UK
    price_at(e, clock, U(2026, 10, 21, 19, 29, 0))                            # 20:29 UK
    assert t.open
    price_at(e, clock, U(2026, 10, 21, 19, 30, 0))                            # 20:30 UK
    assert not t.open and t.state == "forced close"


@pytest.mark.parametrize("day", [2, 3, 4, 5, 6])                              # Monday 2 to Friday 6 November
def test_on_the_close_is_every_day_not_just_friday(ON, day):
    assert forced_close_at(ON, EMA_PULLBACK, U(2026, 11, day, 10, 0)) == U(2026, 11, day, 20, 30)


def test_off_the_ema_pullback_is_still_held_past_20_30_until_friday(OFF, monkeypatch):
    e, clock, t = open_at(OFF, monkeypatch, U(2026, 11, 4, 20, 15))
    price_at(e, clock, U(2026, 11, 4, 20, 30, 0))
    assert t.open                                                             # as before: no daily close
    assert forced_close_at(OFF, EMA_PULLBACK, U(2026, 11, 4, 10, 0)) == U(2026, 11, 6, 20, 30)


# ---- new trades only from 06:00 to 20:30 UK --------------------------------------------------------------------

def live_ema_at(S, monkeypatch, when):
    """An EMA pullback sell reaching its entry on the live price at `when` (the engine's live entry)."""
    forming = when - timedelta(minutes=when.minute % 5, seconds=when.second)
    cs = [candle(forming + timedelta(minutes=5 * k), 100, 100.5, 99.5, 100) for k in (-2, -1, 0)]
    e, ig, tracker, clock, quote = make(S, monkeypatch, cs, {}, trading_on=True, clock={"t": cs[0].start},
                                        live={forming: [(EMA_PULLBACK, SELL, D("100.5"))]})
    e.start(cs[0].start)
    feed(e, clock, cs[:2])
    clock["t"] = when
    e.on_price(tick(when, 100.4))
    return e, ig


def refusals(e):
    return [r["reasons"] for r in journal(e) if r["event"] == "safety refused"]


@pytest.mark.parametrize("when,opens", [
    (U(2026, 11, 4, 5, 59, 59), False),                                       # GMT: 05:59:59 UK
    (U(2026, 11, 4, 6, 0, 0), True),                                          # 06:00 UK
    (U(2026, 11, 4, 20, 29, 59), True),                                       # 20:29:59 UK
    (U(2026, 11, 4, 20, 30, 0), False),                                       # 20:30 UK
    (U(2026, 10, 21, 4, 59, 59), False),                                      # BST: 05:59:59 UK
    (U(2026, 10, 21, 5, 0, 0), True),                                         # BST: 06:00 UK
    (U(2026, 10, 21, 19, 29, 59), True),                                      # BST: 20:29:59 UK
    (U(2026, 10, 21, 19, 30, 0), False),                                      # BST: 20:30 UK
])
def test_on_new_ema_pullback_trades_only_from_06_00_to_20_30_uk(ON, monkeypatch, when, opens):
    e, ig = live_ema_at(ON, monkeypatch, when)
    assert (len(ig.orders_sent()) == 1) is opens
    if not opens:
        assert refusals(e) == [["outside the trading hours 06:00 to 20:30 UK"]]


@pytest.mark.parametrize("when", [U(2026, 11, 4, 5, 59, 59), U(2026, 11, 4, 20, 30, 0), U(2026, 11, 4, 23, 0)])
def test_off_the_ema_pullback_still_opens_outside_those_hours(OFF, monkeypatch, when):
    e, ig = live_ema_at(OFF, monkeypatch, when)
    assert len(ig.orders_sent()) == 1


# ---- the rollover pause stays as it is ---------------------------------------------------------------------------

@pytest.mark.parametrize("hh,mm", [(21, 55), (22, 0), (22, 14)])
def test_the_rollover_pause_is_kept_as_it_is(ON, OFF, hh, mm):
    t = U(2026, 11, 4, hh, mm)
    rollover = "from 21:55 to 22:15 UK (the rollover): no new EMA pullback trade"
    assert may_open(OFF, "GBPUSD", EMA_PULLBACK, t, []) == [rollover]
    assert may_open(ON, "GBPUSD", EMA_PULLBACK, t, []) == [rollover, "outside the trading hours 06:00 to 20:30 UK"]


# ---- no other strategy changes -----------------------------------------------------------------------------------

OTHERS = (SLOW_GRIND, BOLLINGER_BOUNCE, BOLLINGER_BOUNCE_5M, RANGE_TRADE, BREAKOUT, LEVEL_REVERSAL,
          ASIAN_RANGE_BREAKOUT, SESSION_SWEEP, NEW_YORK_OPEN_REVERSAL)


@pytest.mark.parametrize("strategy", OTHERS)
def test_no_other_strategys_hours_or_close_change(ON, OFF, strategy):
    for day in (2, 4, 6):
        for hh, mm in ((5, 59), (6, 0), (12, 0), (20, 29), (20, 30), (21, 55), (23, 0)):
            t = U(2026, 11, day, hh, mm)
            assert may_open(ON, "GBPUSD", strategy, t, []) == may_open(OFF, "GBPUSD", strategy, t, []), (strategy, t)
            assert forced_close_at(ON, strategy, t) == forced_close_at(OFF, strategy, t), (strategy, t)
