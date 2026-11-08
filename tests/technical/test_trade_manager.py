"""Technical tests for the trade manager (design sections 3 and 4), with made-up bars and a pretend order
sender. Nothing here contacts IG. Prices in points (GBPUSD: 1 point = 1 pip); buy prices 1.5 above sell."""

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from config.settings_loader import load_settings
from strategies.common import (BOLLINGER_BOUNCE, BREAKOUT, BUY, EMA_PULLBACK, LEVEL_REVERSAL, RANGE_TRADE, SELL,
                               SLOW_GRIND)
from trade_manager.manager import (CLOSE, FORCED_CLOSE, HALF_CLOSE, STOPPED_BY_IG, TAKE_PROFIT_AT_IG, Bar, Rejection,
                                   TradeManager, plan, step)

U = lambda *a: datetime(*a, tzinfo=timezone.utc)  # noqa: E731
WED = U(2026, 11, 4, 10, 0)
SPREAD = D("1.5")
BOE_CAL = [{"time_utc": "2026-11-05T12:00:00Z", "country": "GB", "event": "BoE Interest Rate Decision",
            "estimate": 4.0, "prev": 3.75, "actual": None, "impact": "high", "unit": "%"}]       # expected up


class Over:
    def __init__(self, base, **sections):
        self.base, self.sections = base, {}
        for name, values in sections.items():
            items = {k: v for k, v in vars(getattr(base, name)).items() if not k.startswith("_")}
            self.sections[name] = SimpleNamespace(**(items | values))

    def __getattr__(self, name):
        return self.sections[name] if name in self.sections else getattr(self.base, name)


@pytest.fixture
def S(pretend_switches, tmp_path):
    return Over(load_settings(switches_from=pretend_switches).for_pair("GBPUSD"),
                trade_manager={"folder": tmp_path / "tm"})


def bar(t, o, h, l, c):
    o, h, l, c = (D(str(x)) for x in (o, h, l, c))
    return Bar(t, o + SPREAD, h + SPREAD, l + SPREAD, c + SPREAD, o, h, l, c)


def trade(S, strategy, direction=BUY, t=WED, entry="100", stop=None, calendar=(), trend_day=None):
    entry = D(entry)
    fill = entry + SPREAD if direction == BUY else entry
    from strategies.common import stop_loss_pips
    st = D(stop) if stop is not None else D(stop_loss_pips(S, strategy))
    return plan(S, "REF1", strategy, direction, t, entry, fill, st, list(calendar), trend_day)


def bars_from(t0, rows):
    return [bar(t0 + timedelta(minutes=5 * k), *r) for k, r in enumerate(rows)]


def run(S, tr, rows, t0=None, band=None, rejections=None):
    out = []
    for k, b in enumerate(bars_from(t0 or tr.opened_at, rows)):
        out += step(S, tr, b, band, (rejections or {}).get(k, []))
        if not tr.open:
            break
    return out


# ---- the stop and take profit at IG ------------------------------------------------------------------

def test_the_stop_at_ig_is_recorded_not_sent(S):
    tr = trade(S, BOLLINGER_BOUNCE, BUY)                         # fill 101.5 (buy); closes on the sell price
    (d,) = run(S, tr, [(100.5, 101, 100, 100.5), (100.5, 100.5, 95, 96)])
    assert (d.kind, d.price, d.pips) == (STOPPED_BY_IG, D("95.5"), D("-6"))


def test_a_bar_opening_past_the_stop_fills_at_its_open(S):
    tr = trade(S, BREAKOUT, SELL)                                # fill 100 (sell); closes on the buy price
    (d,) = run(S, tr, [(100, 100.5, 99, 99.5), (108, 109, 107, 108)])
    assert d.kind == STOPPED_BY_IG and d.price == D("109.5") and d.pips == D("-9.5")


def test_the_entry_bar_counts_the_stop_only_if_it_opened_past_the_entry_or_closed_beyond_the_stop(S):
    tr = trade(S, BOLLINGER_BOUNCE, SELL)                        # sell at 100, stop 6 (buy price 106)
    assert run(S, tr, [(101, 107, 99, 100)]) == [] and tr.open   # opened above the entry: not past it
    tr = trade(S, BOLLINGER_BOUNCE, SELL)
    assert run(S, tr, [(100, 107, 99, 105)])[0].kind == STOPPED_BY_IG   # closed beyond the stop (105 + 1.5)
    tr = trade(S, BOLLINGER_BOUNCE, SELL)
    assert run(S, tr, [(99.5, 107, 99, 100)])[0].kind == STOPPED_BY_IG  # opened past (below) the entry


@pytest.mark.parametrize("strategy,tp", [(EMA_PULLBACK, 30), (SLOW_GRIND, 20), (BREAKOUT, 50), (LEVEL_REVERSAL, 20),
                                         (BOLLINGER_BOUNCE, 100), (RANGE_TRADE, 100)])
def test_each_strategys_take_profit_at_ig(S, strategy, tp):
    tr = trade(S, strategy, SELL, stop="10")
    assert tr.take_profit_pips == tp
    d = run(S, tr, [(100, 100.5, 99, 99.5)] + [(99.5, 99.5, 100 - tp - 2, 100 - tp)])[-1]
    assert d.kind == TAKE_PROFIT_AT_IG and d.pips == tp


def test_100_pips_on_a_big_news_day_and_in_a_trend_days_direction(S):
    thu = U(2026, 11, 5, 9, 0)
    assert trade(S, EMA_PULLBACK, t=thu, calendar=BOE_CAL).take_profit_pips == 100
    assert trade(S, SLOW_GRIND, t=thu, calendar=BOE_CAL).take_profit_pips == 100
    assert trade(S, EMA_PULLBACK, SELL, trend_day="down").take_profit_pips == 100
    assert trade(S, EMA_PULLBACK, BUY, trend_day="down").take_profit_pips == 30
    assert trade(S, BREAKOUT, t=thu, calendar=BOE_CAL).take_profit_pips == 50


# ---- the slow grind's lock -----------------------------------------------------------------------------

def test_the_slow_grinds_lock_closes_back_at_10_up_after_15_up(S):
    tr = trade(S, SLOW_GRIND, SELL)                              # sell at 100; 15 up = buy price 85
    rows = [(100, 100, 98, 99), (99, 99, 83, 84), (84, 92, 84, 91)]   # 15+ up, then back to 10 up (buy 90)
    (d,) = run(S, tr, rows)
    assert (d.kind, d.price, d.pips) == (CLOSE, D("90"), D("10")) and "profit lock" in d.why


def test_the_lock_needs_15_up_in_an_earlier_bar(S):
    tr = trade(S, SLOW_GRIND, SELL)
    assert run(S, tr, [(100, 100, 98, 99), (99, 99.5, 83, 91)]) == []          # 15 up and back in one bar: not yet
    assert tr.best == D("15.5")                                     # (on the buy price)


def test_only_the_slow_grind_has_a_lock(S):
    for name in (EMA_PULLBACK, BREAKOUT, BOLLINGER_BOUNCE, RANGE_TRADE, LEVEL_REVERSAL):
        tr = trade(S, name, SELL, stop="20")
        assert run(S, tr, [(100, 100, 98, 99), (99, 99, 83, 84), (84, 92, 84, 91)]) == [], name


# ---- the range trade's half close ------------------------------------------------------------------------

def test_the_range_trade_closes_half_at_the_opposite_band(S):
    tr = trade(S, RANGE_TRADE, SELL)                             # sell at 100
    band = (D("110"), D("90"))                                   # the lower band 90 (sell price)
    ds = run(S, tr, [(100, 100.5, 95, 96), (96, 96, 89, 90)], band=band)
    (h,) = ds
    assert (h.kind, h.price, h.pips, h.part) == (HALF_CLOSE, D("91.5"), D("8.5"), D("0.5")) and tr.open
    run(S, tr, [(90, 90, 70, 71)], t0=WED + timedelta(minutes=10), band=band)
    assert tr.state == TAKE_PROFIT_AT_IG or tr.open             # the rest goes on to its own exits


def test_the_rest_of_the_range_trade_and_its_total(S):
    tr = trade(S, RANGE_TRADE, SELL)
    band = (D("110"), D("90"))
    run(S, tr, [(100, 100.5, 95, 96), (96, 96, 89, 90)], band=band)
    (d,) = run(S, tr, [(90, 107, 90, 106)], t0=WED + timedelta(minutes=10), band=band)    # stopped at 106
    assert d.kind == STOPPED_BY_IG and d.part == D("0.5") and tr.total_pips() == D("8.5") * D("0.5") + D("-6") * D("0.5")


def test_only_the_range_trade_closes_by_half(S):
    for name in (BOLLINGER_BOUNCE, BREAKOUT, EMA_PULLBACK):
        tr = trade(S, name, SELL, stop="20")
        assert all(d.kind != HALF_CLOSE for d in run(S, tr, [(100, 100.5, 95, 96), (96, 96, 89, 90)],
                                                     band=(D("110"), D("90"))))


# ---- the close on a rejection at a level ---------------------------------------------------------------------

def test_a_rejection_at_a_level_against_the_trade_closes_it(S):
    tr = trade(S, BOLLINGER_BOUNCE, SELL)
    rej = {1: [Rejection(BUY, D("97.0"), "S2 96.8")]}            # a bounce up: against a sell
    (d,) = run(S, tr, [(100, 100.5, 98, 99), (99, 99.5, 96.5, 97.5)], rejections=rej)
    assert (d.kind, d.price, d.pips) == (CLOSE, D("98.5"), D("1.5")) and "S2 96.8" in d.why     # closed on the buy price


def test_not_in_the_entry_bar_and_not_one_in_the_trades_direction(S):
    tr = trade(S, BOLLINGER_BOUNCE, SELL)
    assert run(S, tr, [(100, 100.5, 98, 99)], rejections={0: [Rejection(BUY, D("99"))]}) == []
    tr = trade(S, BOLLINGER_BOUNCE, SELL)
    assert run(S, tr, [(100, 100.5, 98, 99), (99, 99.5, 97, 98)], rejections={1: [Rejection(SELL, D("98"))]}) == []


@pytest.mark.parametrize("strategy,closes", [(BOLLINGER_BOUNCE, True), (RANGE_TRADE, True), (EMA_PULLBACK, False),
                                             (BREAKOUT, False), (SLOW_GRIND, False), (LEVEL_REVERSAL, False)])
def test_only_the_strategies_the_design_says(S, strategy, closes):
    tr = trade(S, strategy, SELL, stop="10")
    ds = run(S, tr, [(100, 100.5, 98, 99), (99, 99.5, 97, 98)], rejections={1: [Rejection(BUY, D("97.5"))]})
    assert bool(ds and ds[0].kind == CLOSE) is closes


def test_the_expected_news_direction_takes_precedence_on_a_big_news_day(S):
    thu = U(2026, 11, 5, 8, 0)                                   # BoE expected up: a buy is kept open
    tr = trade(S, BOLLINGER_BOUNCE, BUY, t=thu, calendar=BOE_CAL)
    assert tr.news_direction == BUY
    assert run(S, tr, [(100, 101, 99.5, 100.5), (100.5, 101, 99, 100)], rejections={1: [Rejection(SELL, D("99.5"))]}) == []
    tr = trade(S, BOLLINGER_BOUNCE, SELL, t=thu, calendar=BOE_CAL)   # a sell against it is closed
    ds = run(S, tr, [(100, 100.5, 98, 99), (99, 99.5, 97, 98)], rejections={1: [Rejection(BUY, D("97.5"))]})
    assert ds[0].kind == CLOSE


# ---- the scheduled closes ------------------------------------------------------------------------------

@pytest.mark.parametrize("strategy", (BOLLINGER_BOUNCE, RANGE_TRADE, SLOW_GRIND, LEVEL_REVERSAL))
def test_closed_at_20_30_uk_every_day(S, strategy):
    t0 = U(2026, 11, 4, 20, 20)
    tr = trade(S, strategy, SELL, t=t0, stop="30")
    ds = run(S, tr, [(100, 100.5, 99, 99.5), (99.5, 100, 99, 99.6), (99.6, 99.8, 99, 99.2)])
    (d,) = ds
    assert (d.kind, d.price, d.why) == (FORCED_CLOSE, D("101.1"), "20:30 UK close") and tr.decisions[-1].pips == D("-1.1")


@pytest.mark.parametrize("strategy", (EMA_PULLBACK, BREAKOUT))
def test_held_overnight_and_closed_at_20_30_uk_on_friday(S, strategy):
    tr = trade(S, strategy, SELL, t=U(2026, 11, 4, 20, 20), stop="30")
    assert tr.close_at == U(2026, 11, 6, 20, 30)
    assert run(S, tr, [(100, 100.5, 99, 99.5)] * 5) == [] and tr.open
    tr = trade(S, strategy, SELL, t=U(2026, 11, 6, 20, 20), stop="30")
    assert run(S, tr, [(100, 100.5, 99, 99.5)] * 3)[0].kind == FORCED_CLOSE


@pytest.mark.parametrize("strategy,closed", [(BOLLINGER_BOUNCE, True), (RANGE_TRADE, True), (LEVEL_REVERSAL, True),
                                             (EMA_PULLBACK, False), (BREAKOUT, False), (SLOW_GRIND, False)])
def test_closed_15_minutes_before_big_news_only_for_the_strategies_the_design_says(S, strategy, closed):
    t0 = U(2026, 11, 5, 11, 30)                                  # BoE 12:00: closed at 11:45
    tr = trade(S, strategy, SELL, t=t0, stop="30", calendar=BOE_CAL)
    ds = run(S, tr, [(100, 100.5, 99, 99.5)] * 5)
    if closed:
        assert ds[0].kind == FORCED_CLOSE and ds[0].why == "closed 15 minutes before big news"
        assert tr.decisions[-1] and len([d for d in ds]) == 1 and tr.bars == 4      # the 11:45 bar
    else:
        assert ds == []


def test_the_scheduled_close_comes_first_in_its_bar(S):
    tr = trade(S, BOLLINGER_BOUNCE, SELL, t=U(2026, 11, 4, 20, 25))
    ds = run(S, tr, [(100, 100.5, 99, 99.5), (99.5, 120, 80, 99)])     # the 20:30 bar would hit the stop and the take profit
    assert ds[0].kind == FORCED_CLOSE and ds[0].price == D("101")


# ---- the manager and the order sender ------------------------------------------------------------------

class PretendSender:
    def __init__(self):
        self.closes = []

    def close(self, reference, *, half=False, why=""):
        self.closes.append((reference, half, why))
        return SimpleNamespace(what="half closed" if half else "closed")


def test_the_manager_tells_the_order_sender_only_its_own_closes_and_records_every_decision(S):
    sender = PretendSender()
    m = TradeManager(S, sender, now=lambda: WED)
    band = (D("110"), D("90"))
    rng = trade(S, RANGE_TRADE, SELL)
    rng.reference = "RANGE1"
    bo = trade(S, BREAKOUT, SELL)
    bo.reference = "BREAK1"
    m.add(rng)
    m.add(bo)
    for b in bars_from(WED, [(100, 100.5, 95, 96), (96, 96, 89, 90), (90, 92, 48, 50), (50, 107, 50, 106)]):
        m.on_bar(b, band)
    assert sender.closes == [("RANGE1", True, "the opposite Bollinger band")]   # the take profit and stop are IG's
    rows = [json.loads(x) for x in (S.trade_manager.folder / "GBPUSD" / "decisions.jsonl").read_text().splitlines()]
    assert [(r["reference"], r["decision"]) for r in rows] == [("RANGE1", HALF_CLOSE), ("BREAK1", TAKE_PROFIT_AT_IG),
                                                               ("RANGE1", STOPPED_BY_IG)]
    assert rows[0]["order_sender"] == "half closed"


def test_forced_closes_and_the_lock_go_to_the_order_sender(S):
    sender = PretendSender()
    m = TradeManager(S, sender, now=lambda: WED)
    sg = trade(S, SLOW_GRIND, SELL)
    sg.reference = "SG1"
    bb = trade(S, BOLLINGER_BOUNCE, SELL, t=U(2026, 11, 4, 20, 25), stop="30")
    bb.reference = "BB1"
    m.add(sg)
    for b in bars_from(WED, [(100, 100, 98, 99), (99, 99, 83, 84), (84, 92, 84, 91)]):
        m.on_bar(b)
    m.add(bb)
    for b in bars_from(U(2026, 11, 4, 20, 25), [(100, 100.5, 99, 99.5), (99.5, 100, 99, 99.6)]):
        m.on_bar(b)
    assert [(r, h) for r, h, _ in sender.closes] == [("SG1", False), ("BB1", False)]
    assert "profit lock" in sender.closes[0][2] and sender.closes[1][2] == "20:30 UK close"


def test_a_closed_trade_takes_no_more_decisions(S):
    tr = trade(S, BOLLINGER_BOUNCE, BUY)
    run(S, tr, [(100.5, 101, 100, 100.5), (100.5, 100.5, 95, 96)])
    assert step(S, tr, bar(WED + timedelta(minutes=10), 96, 120, 90, 100)) == []
