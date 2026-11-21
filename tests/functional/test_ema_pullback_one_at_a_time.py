"""Functional tests for EMA_PULLBACK_ONE_AT_A_TIME (owner, 21 November 2026), through the live engine with the real
order sender, safety rules and trade manager and a pretend IG (the harness of tests/technical/test_trading.py):

  * while an EMA pullback trade is open, no other EMA pullback trade opens; a new one can open once that trade has
    closed;
  * setups still form and are logged as now; only the opening of the second trade is stopped, and the reason is
    logged when one is skipped;
  * off (the default): the EMA pullback exactly as before; no other strategy changes either way.
Contacts nobody."""

from datetime import timedelta

import pytest

from strategies.common import BUY, EMA_PULLBACK, SELL, SLOW_GRIND
from tests.technical.test_orders import Over
from tests.technical.test_trading import U, candle, decisions, feed, idea, journal, make, trades_rows

T0 = U(2026, 11, 4, 10, 0)                                                     # a Wednesday, GMT
CS = [candle(T0 + timedelta(minutes=5 * k), 13400, 13400.5, 13399.5, 13400) for k in range(8)]
SKIPPED = "EMA pullback already has 1 trade(s) open (at most 1)"


def settings(pretend_switches, tmp_path, on):
    from config.settings_loader import load_settings
    s = load_settings(switches_from=pretend_switches).for_pair("GBPUSD")
    return Over(s, switches={k: True for k in ("slow_grind", "ema_pullback", "bollinger_bounce", "range_trade",
                                                 "breakout", "level_reversal")}
                | {"trading": False, "ema_pullback_one_at_a_time": on},
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


def ema(k, direction=SELL):
    return idea(EMA_PULLBACK, CS[k].start, direction, price="13400")


def run(S, monkeypatch, ideas, upto):
    e, ig, tracker, clock, quote = make(S, monkeypatch, CS, ideas, trading_on=True, clock={"t": T0})
    e.start(T0)
    feed(e, clock, CS[:upto])
    return e, ig, clock


def ema_trades(e):
    return [t for t in e.manager.trades.values() if t.strategy == EMA_PULLBACK]


def test_the_switch_is_off_if_left_out_of_env(pretend_switches):
    from config.settings_loader import load_settings
    assert load_settings(switches_from=pretend_switches).switches.ema_pullback_one_at_a_time is False


def test_on_a_second_setup_reaching_its_entry_while_one_trade_is_open_does_not_open(ON, monkeypatch):
    e, ig, clock = run(ON, monkeypatch, {CS[1].start: [ema(1)], CS[3].start: [ema(3)]}, 5)
    assert len(ig.orders_sent()) == 1 and len(ema_trades(e)) == 1                # only the first opened
    (first,) = ema_trades(e)
    assert first.open and first.opened_at == CS[1].end
    # the second setup is logged as now: its idea, allowed by the strategy's rules, at its candle
    ideas = [d for d in decisions(e) if d["kind"] == "idea" and d["strategy"] == EMA_PULLBACK]
    assert [d["time_utc"] for d in ideas] == ["2026-11-04T10:05:00Z", "2026-11-04T10:15:00Z"]
    assert all(d["allowed"] for d in ideas)
    # and the reason it was skipped is logged, in the orders journal and the decisions
    (refused,) = [r for r in journal(e) if r["event"] == "safety refused"]
    assert refused["strategy"] == EMA_PULLBACK and refused["reasons"] == [SKIPPED]
    (order,) = [d for d in decisions(e) if d["kind"] == "order" and d["result"] == "safety refused"]
    assert order["strategy"] == EMA_PULLBACK and order["reasons"] == [SKIPPED]


def test_on_the_other_direction_does_not_open_either(ON, monkeypatch):
    e, ig, clock = run(ON, monkeypatch, {CS[1].start: [ema(1, SELL)], CS[3].start: [ema(3, BUY)]}, 5)
    assert len(ig.orders_sent()) == 1 and [t.direction for t in ema_trades(e)] == [SELL]
    assert [r["reasons"] for r in journal(e) if r["event"] == "safety refused"] == [[SKIPPED]]


def test_on_a_new_one_opens_once_the_open_trade_has_closed(ON, monkeypatch):
    e, ig, clock = run(ON, monkeypatch, {CS[1].start: [ema(1)], CS[3].start: [ema(3)], CS[6].start: [ema(6)]}, 5)
    (first,) = ema_trades(e)
    ig.system_close(e.sender.trades[first.reference].deal_id, 13412.5, "2026-11-04T10:26:00",
                    stop=float(first.fill) + 12)                                  # IG's stop: the trade closes
    feed(e, clock, CS[5:6])                                                       # found closed after the candle
    assert not first.open and first.state == "closed at IG"
    feed(e, clock, CS[6:7])                                                       # a later setup reaches its entry
    assert len(ig.orders_sent()) == 2
    second = [t for t in ema_trades(e) if t.reference != first.reference]
    assert len(second) == 1 and second[0].open and second[0].opened_at == CS[6].end
    assert [r["reasons"] for r in journal(e) if r["event"] == "safety refused"] == [[SKIPPED]]   # only the 10:15 one


def test_off_a_second_ema_pullback_trade_still_opens(OFF, monkeypatch):
    e, ig, clock = run(OFF, monkeypatch, {CS[1].start: [ema(1)], CS[3].start: [ema(3)]}, 5)
    assert len(ig.orders_sent()) == 2 and all(t.open for t in ema_trades(e))
    assert not [r for r in journal(e) if r["event"] == "safety refused"]


def test_on_an_ema_pullback_trade_still_does_not_count_towards_another_strategys_limits(ON, monkeypatch):
    e, ig, clock = run(ON, monkeypatch, {CS[1].start: [ema(1)], CS[3].start: [idea(SLOW_GRIND, CS[3].start,
                                                                                     price="13400")]}, 5)
    assert sorted(t.strategy for t in e.manager.trades.values()) == [EMA_PULLBACK, SLOW_GRIND]
    assert not [r for r in journal(e) if r["event"] == "safety refused"]


def test_no_other_strategys_limit_changes(ON, OFF):
    from datetime import timedelta as td
    from decimal import Decimal as D
    from safety.rules import AccountFunds, OpenTrade, decide, order_for
    from strategies.common import BOLLINGER_BOUNCE, BREAKOUT, LEVEL_REVERSAL, RANGE_TRADE, Idea
    t = U(2026, 11, 4, 10, 0)
    for strategy in (SLOW_GRIND, BOLLINGER_BOUNCE, RANGE_TRADE, BREAKOUT, LEVEL_REVERSAL):
        ctx = {"stop_price": D("13410.0")} if strategy == LEVEL_REVERSAL else {}
        i = Idea("GBPUSD", strategy, SELL, t, D("13400.0"), "trend", "down", None, "sell side", ["made up"], True, "", ctx)
        for open_trades in ([], [OpenTrade(strategy, SELL, t - td(hours=1), D("12"), D("10"))],
                            [OpenTrade(EMA_PULLBACK, SELL, t - td(hours=1), D("12"), D("10"))]):
            a = decide(ON, order_for(ON, i), list(open_trades), AccountFunds(D("20000"), t - td(minutes=30)), t, False, [])
            b = decide(OFF, order_for(OFF, i), list(open_trades), AccountFunds(D("20000"), t - td(minutes=30)), t, False, [])
            assert (a.allowed, a.reasons) == (b.allowed, b.reasons), (strategy, open_trades)
