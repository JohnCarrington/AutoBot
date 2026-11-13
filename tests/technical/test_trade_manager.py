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
from trade_manager.manager import (CLOSE, FORCED_CLOSE, HALF_CLOSE, STOP_MOVED, STOP_NOT_MOVED, STOPPED_BY_IG,
                                   TAKE_PROFIT_AT_IG, Bar, Rejection, TradeManager, plan, step)

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
    (d,) = run(S, tr, [(100, 100.5, 99, 99.5), (111, 112, 110, 111)])   # stop 12 (owner, 10 November 2026)
    assert d.kind == STOPPED_BY_IG and d.price == D("112.5") and d.pips == D("-12.5")


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


# ---- the close at the opposite band (owner, 11 November 2026: range trade in full, bounce half) ---------------

def test_the_range_trade_closes_in_full_at_the_opposite_band(S):
    tr = trade(S, RANGE_TRADE, SELL)                             # sell at 100
    band = (D("110"), D("90"))                                   # the lower band 90 (sell price)
    (d,) = run(S, tr, [(100, 100.5, 95, 96), (96, 96, 89, 90)], band=band)
    assert (d.kind, d.price, d.pips, d.part, d.why) == (CLOSE, D("91.5"), D("8.5"), D("1"), "the opposite Bollinger band")
    assert not tr.open and tr.total_pips() == D("8.5") and not tr.half_done


def test_the_bounce_closes_half_at_the_opposite_band_and_the_rest_goes_on(S):
    tr = trade(S, BOLLINGER_BOUNCE, SELL)                        # sell at 100
    band = (D("110"), D("90"))
    (h,) = run(S, tr, [(100, 100.5, 95, 96), (96, 96, 89, 90)], band=band)
    assert (h.kind, h.price, h.pips, h.part) == (HALF_CLOSE, D("91.5"), D("8.5"), D("0.5")) and tr.open
    assert run(S, tr, [(90, 91, 88, 89)], t0=WED + timedelta(minutes=10), band=band) == []   # only once
    (d,) = run(S, tr, [(89, 107, 89, 106)], t0=WED + timedelta(minutes=15), band=band)    # the rest: its stop
    assert d.kind == STOPPED_BY_IG and d.part == D("0.5") and tr.total_pips() == D("8.5") * D("0.5") + D("-6") * D("0.5")


def test_the_rest_of_the_bounce_keeps_its_close_on_a_rejection_at_a_level(S):
    tr = trade(S, BOLLINGER_BOUNCE, SELL)
    band = (D("110"), D("90"))
    run(S, tr, [(100, 100.5, 95, 96), (96, 96, 89, 90)], band=band)
    (d,) = run(S, tr, [(90, 92, 89.5, 91)], t0=WED + timedelta(minutes=10), band=band,
               rejections={0: [Rejection(BUY, D("90.5"), "S2 90.2")]})
    assert (d.kind, d.price, d.part) == (CLOSE, D("92.0"), D("0.5")) and "S2 90.2" in d.why


def test_no_other_strategy_closes_at_the_opposite_band(S):
    for name in (BREAKOUT, EMA_PULLBACK, SLOW_GRIND, LEVEL_REVERSAL):
        tr = trade(S, name, SELL, stop="20")
        assert all(d.why != "the opposite Bollinger band"
                   for d in run(S, tr, [(100, 100.5, 95, 96), (96, 96, 89, 90)], band=(D("110"), D("90"))))


def test_a_band_close_is_priced_at_igs_tenth_of_a_pip_against_the_trade(S):
    sell = trade(S, RANGE_TRADE, SELL)
    (d,) = run(S, sell, [(100, 100.5, 95, 96), (96, 96, 89, 90)], band=(D("110"), D("90.04")))
    assert d.price == D("91.6")                                  # 90.04 + 1.5 = 91.54: up, on the buy price
    buy = trade(S, RANGE_TRADE, BUY)                             # buy at 101.5 (100 + the spread)
    (d,) = run(S, buy, [(100, 100.5, 99.5, 100), (100, 111, 100, 110)], band=(D("109.96"), D("90")))
    assert d.price == D("109.9")                                 # down, on the sell price


def test_a_bar_that_opens_past_the_band_closes_at_its_open(S):
    tr = trade(S, RANGE_TRADE, SELL)
    (d,) = run(S, tr, [(100, 100.5, 95, 96), (88, 89, 87, 88)], band=(D("110"), D("90")))
    assert d.price == D("89.5")                                  # the open 88 on the buy price, not the band


def test_the_shares_come_from_the_settings(S):
    from trade_manager.manager import band_close_share
    assert (band_close_share(S, RANGE_TRADE), band_close_share(S, BOLLINGER_BOUNCE)) == (D(1), D("0.5"))
    assert all(band_close_share(S, n) == 0 for n in (BREAKOUT, EMA_PULLBACK, SLOW_GRIND, LEVEL_REVERSAL))
    half = Over(S, range_trade={"close_percent_at_opposite_band": 50}, bounce={"close_percent_at_opposite_band": 0})
    tr = trade(half, RANGE_TRADE, SELL)
    (h,) = run(half, tr, [(100, 100.5, 95, 96), (96, 96, 89, 90)], band=(D("110"), D("90")))
    assert h.kind == HALF_CLOSE and tr.open
    bo = trade(half, BOLLINGER_BOUNCE, SELL)
    assert run(half, bo, [(100, 100.5, 95, 96), (96, 96, 89, 90)], band=(D("110"), D("90"))) == []


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

    def close(self, reference, *, half=False, why="", price=None):
        self.closes.append((reference, half, why))
        return SimpleNamespace(what="half closed" if half else "closed", ok=True)


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
    assert sender.closes == [("RANGE1", False, "the opposite Bollinger band")]  # the take profit and stop are IG's
    rows = [json.loads(x) for x in (S.trade_manager.folder / "GBPUSD" / "decisions.jsonl").read_text().splitlines()]
    assert [(r["reference"], r["decision"]) for r in rows] == [("RANGE1", CLOSE), ("BREAK1", TAKE_PROFIT_AT_IG)]
    assert rows[0]["order_sender"] == "closed"


def test_the_manager_asks_the_order_sender_for_the_bounces_half_close(S):
    sender = PretendSender()
    m = TradeManager(S, sender, now=lambda: WED)
    bo = trade(S, BOLLINGER_BOUNCE, SELL)
    m.add(bo)
    for b in bars_from(WED, [(100, 100.5, 95, 96), (96, 96, 89, 90), (90, 107, 90, 106)]):
        m.on_bar(b, (D("110"), D("90")))
    assert sender.closes == [("REF1", True, "the opposite Bollinger band")]     # its stop is IG's
    rows = [json.loads(x) for x in (S.trade_manager.folder / "GBPUSD" / "decisions.jsonl").read_text().splitlines()]
    assert [(r["decision"], r["order_sender"] if "order_sender" in r else None) for r in rows] == [
        (HALF_CLOSE, "half closed"), (STOP_MOVED, None), (STOPPED_BY_IG, None)]   # 9.5 up: its stop at break-even


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


# ---- watching a level, and IG's own closes -----------------------------------------------------------

from trade_manager.manager import HOLD, WATCHING  # noqa: E402


def test_watching_a_level_while_a_rejection_setup_runs_against_the_trade(S):
    m = TradeManager(S, PretendSender(), now=lambda: WED)
    tr = trade(S, BOLLINGER_BOUNCE, SELL)
    m.add(tr)
    bs = bars_from(WED, [(100, 100.5, 99, 99.5), (99.5, 100, 98.5, 99), (99, 99.5, 98, 98.5)])
    m.on_bar(bs[0], watching=set())
    assert tr.decision == HOLD
    m.on_bar(bs[1], watching={BUY})                    # a bounce up setting up at a level: against the sell
    assert tr.decision == WATCHING and tr.open
    m.on_bar(bs[2], watching=set())
    assert tr.decision == HOLD
    rows = [json.loads(x)["decision"] for x in (S.trade_manager.folder / "GBPUSD" / "decisions.jsonl").read_text().splitlines()]
    assert rows == [WATCHING, HOLD]


def test_not_watching_for_a_setup_the_same_way_or_a_strategy_without_the_level_close(S):
    m = TradeManager(S, PretendSender(), now=lambda: WED)
    bb, ep = trade(S, BOLLINGER_BOUNCE, SELL), trade(S, EMA_PULLBACK, SELL)
    bb.reference, ep.reference = "BB", "EP"
    m.add(bb)
    m.add(ep)
    m.on_bar(bar(WED, 100, 100.5, 99, 99.5), watching={SELL})
    assert bb.decision == HOLD
    m.on_bar(bar(WED + timedelta(minutes=5), 99.5, 100, 99, 99.5), watching={BUY})
    assert bb.decision == WATCHING and ep.decision == HOLD


class IGSender(PretendSender):
    def __init__(self, ig_closed):
        super().__init__()
        self.ig_closed, self.asked = ig_closed, []

    def closed_at_ig(self, reference, kind, price=None):
        self.asked.append((reference, kind))
        return SimpleNamespace(ok=self.ig_closed, what="closed at IG" if self.ig_closed else "still open at IG")


def test_igs_stop_is_passed_to_the_order_sender(S):
    sender = IGSender(True)
    m = TradeManager(S, sender, now=lambda: WED)
    tr = trade(S, BOLLINGER_BOUNCE, BUY)
    m.add(tr)
    for b in bars_from(WED, [(100.5, 101, 100, 100.5), (100.5, 100.5, 95, 96)]):
        m.on_bar(b)
    assert sender.asked == [("REF1", STOPPED_BY_IG)] and sender.closes == [] and not tr.open


def test_live_a_trade_stays_open_until_ig_has_closed_it(S):
    sender = IGSender(False)
    m = TradeManager(S, sender, now=lambda: WED, ig_confirms=True)
    tr = trade(S, BOLLINGER_BOUNCE, BUY)
    m.add(tr)
    for b in bars_from(WED, [(100.5, 101, 100, 100.5), (100.5, 100.5, 95, 96)]):
        m.on_bar(b)
    assert tr.open and sender.asked == [("REF1", STOPPED_BY_IG)]
    m.closed_at_ig("REF1")
    assert not tr.open


def test_only_some_trades_can_be_stepped(S):
    m = TradeManager(S, PretendSender(), now=lambda: WED)
    a, b = trade(S, BREAKOUT, SELL), trade(S, EMA_PULLBACK, SELL)
    a.reference, b.reference = "A", "B"
    m.add(a)
    m.add(b)
    m.on_bar(bar(WED, 100, 100.5, 99, 99.5), only=["B"])
    assert (a.bars, b.bars) == (0, 1)


# ---- live: a close is never recorded unless IG confirms it (owner, 10 November 2026) -------------------

from trade_manager.manager import CLOSE_NOT_DONE, CLOSED_AT_IG  # noqa: E402


class AnswerSender(PretendSender):
    """Answers each close from a script: "refused", "closed", or a gone-at-IG result."""
    def __init__(self, answers):
        super().__init__()
        self.answers = list(answers)

    def close(self, reference, *, half=False, why="", price=None):
        self.closes.append((reference, half, why))
        a = self.answers.pop(0)
        if a == "refused":
            return SimpleNamespace(ok=False, what="close refused",
                                   reasons=["error.service.marketdata.position.notional.details.null.error"])
        if a == "closed":
            return SimpleNamespace(ok=True, what="half closed" if half else "closed", reasons=[])
        return a


def tm_rows(S):
    return [json.loads(x) for x in (S.trade_manager.folder / "GBPUSD" / "decisions.jsonl").read_text().splitlines()]


def test_live_a_close_ig_refuses_leaves_the_trade_open_and_is_tried_again(S):
    clock = {"t": U(2026, 11, 10, 20, 30)}
    sender = AnswerSender(["refused", "closed"])
    m = TradeManager(S, sender, now=lambda: clock["t"], ig_confirms=True)
    tr = trade(S, BOLLINGER_BOUNCE, BUY, t=U(2026, 11, 10, 20, 25), stop="30")
    tr.bars = 1
    m.add(tr)
    m.on_bar(bar(U(2026, 11, 10, 20, 30), 100, 100.5, 99.5, 100))          # 20:30: the forced close
    assert tr.open and tr.state == HOLD and tr.decisions == [] and tr.close_attempts == 1
    (row,) = tm_rows(S)
    assert row["decision"] == CLOSE_NOT_DONE and "notional.details.null" in row["why"] and "stays open" in row["why"]
    clock["t"] = U(2026, 11, 10, 20, 30, 10)                                 # 10 seconds later: not yet again
    m.on_bar(bar(clock["t"], 100, 100, 100, 100))
    assert len(sender.closes) == 1 and tr.open
    clock["t"] = U(2026, 11, 10, 20, 30, 31)                                 # after close_retry_seconds (30)
    m.on_bar(bar(clock["t"], 100, 100, 100, 100))
    assert len(sender.closes) == 2 and not tr.open and tr.state == FORCED_CLOSE
    assert [r["decision"] for r in tm_rows(S)] == [CLOSE_NOT_DONE, FORCED_CLOSE]


def test_live_a_refused_half_close_is_undone_and_tried_again(S):
    clock = {"t": WED}
    sender = AnswerSender(["refused", "closed"])
    m = TradeManager(S, sender, now=lambda: clock["t"], ig_confirms=True)
    tr = trade(S, BOLLINGER_BOUNCE, SELL)                        # closed by half at the opposite band
    tr.bars = 1
    m.add(tr)
    band = (D("110"), D("90"))
    m.on_bar(bar(WED + timedelta(minutes=5), 96, 96, 89, 90), band)
    assert not tr.half_done and tr.half_pips is None and tr.state == HOLD and tr.decisions == []
    clock["t"] = WED + timedelta(minutes=10)
    m.on_bar(bar(clock["t"], 90, 91, 89, 90), band)
    assert tr.half_done and tr.state == HALF_CLOSE and [d.kind for d in tr.decisions] == [HALF_CLOSE]


def test_live_a_trade_ig_already_closed_is_finished_at_igs_level_and_time(S):
    gone = SimpleNamespace(ok=True, what="gone at IG", reference="REF1", level=D("13335.2"),
                           closed_utc=U(2026, 11, 10, 17, 56, 27), reasons=["IG refused the close because it had already closed it"])
    sender = AnswerSender([gone])
    m = TradeManager(S, sender, now=lambda: U(2026, 11, 10, 20, 30), ig_confirms=True)
    tr = plan(S, "REF1", SLOW_GRIND, SELL, U(2026, 11, 10, 15, 19), D("13373.2"), D("13373.0"), D("15"), [])
    tr.bars = 1
    m.add(tr)
    m.on_bar(bar(U(2026, 11, 10, 20, 30), 13346, 13346, 13346, 13346))
    assert not tr.open and tr.state == CLOSED_AT_IG
    d = tr.decisions[-1]
    assert (d.price, d.pips, d.at) == (D("13335.2"), D("37.8"), U(2026, 11, 10, 17, 56, 27))
    assert tr.total_pips() == D("37.8") and tm_rows(S)[-1]["order_sender"] == "gone at IG"


def test_the_regular_check_finishes_a_trade_ig_closed(S):
    m = TradeManager(S, PretendSender(), now=lambda: WED, ig_confirms=True)
    tr = trade(S, EMA_PULLBACK, BUY)
    m.add(tr)
    found = SimpleNamespace(what="gone at IG", reference="REF1", level=tr.fill - D("4"), closed_utc=WED, reasons=["x"])
    assert m.gone_at_ig(found) and not tr.open and tr.total_pips() == D("-4")
    assert not m.gone_at_ig(found)                                           # only once


def test_live_igs_stop_is_recorded_at_igs_level(S):
    class Confirmed(IGSender):
        def closed_at_ig(self, reference, kind, price=None):
            self.asked.append((reference, kind))
            return SimpleNamespace(ok=True, what="closed at IG", level=D("94.0"), closed_utc=WED + timedelta(minutes=7))
    m = TradeManager(S, Confirmed(True), now=lambda: WED, ig_confirms=True)
    tr = trade(S, BOLLINGER_BOUNCE, BUY)                                    # fill 101.5
    m.add(tr)
    for b in bars_from(WED, [(100.5, 101, 100, 100.5), (100.5, 100.5, 95, 96)]):
        m.on_bar(b)
    d = tr.decisions[-1]
    assert not tr.open and (d.kind, d.price, d.pips, d.at) == (STOPPED_BY_IG, D("94.0"), D("-7.5"), WED + timedelta(minutes=7))
    assert tm_rows(S)[-1]["price"] == "94.0"


# ---- the Bollinger bounce's break-even (owner, 13 November 2026) ----------------------------------------------

class MovingSender(PretendSender):
    """Moves a stop at IG: answers from a list (True: IG confirms; False: IG refuses), then confirms."""
    def __init__(self, answers=()):
        super().__init__()
        self.answers, self.moves = list(answers), []
        self.alerts = SimpleNamespace(infos=[], info=lambda text, key=None, html=False: self.alerts.infos.append(text))

    def move_stop(self, reference, level, why=""):
        self.moves.append((reference, level))
        ok = self.answers.pop(0) if self.answers else True
        return SimpleNamespace(ok=ok, what="stop moved" if ok else "stop not moved",
                               reasons=[] if ok else ["error.service.otc.invalid.stop"])


def decisions(S):
    return [json.loads(x) for x in (S.trade_manager.folder / "GBPUSD" / "decisions.jsonl").read_text().splitlines()]


def test_the_bounces_break_even_comes_from_the_settings_and_only_for_the_bounce(S):
    assert trade(S, BOLLINGER_BOUNCE, BUY).break_even_after == D("6")
    for strategy in (EMA_PULLBACK, SLOW_GRIND, BREAKOUT, RANGE_TRADE, LEVEL_REVERSAL):
        assert trade(S, strategy, BUY).break_even_after is None
    off = Over(S, bounce={"break_even_after_pips": D("0")})
    assert trade(off, BOLLINGER_BOUNCE, BUY).break_even_after is None


def test_a_bounce_6_pips_up_has_its_stop_moved_to_its_open_price_and_is_stopped_there_at_0(S):
    sender = MovingSender()
    m = TradeManager(S, sender, now=lambda: WED)
    tr = trade(S, BOLLINGER_BOUNCE, BUY)                         # fill 101.5; closes on the sell price
    m.add(tr)
    for b in bars_from(WED, [(100.5, 101, 100, 100.5), (100.5, 107.5, 100.5, 107), (107, 107, 101, 101)]):
        m.on_bar(b)
    assert sender.moves == [("REF1", D("101.5"))]                # the open price (IG's level)
    assert tr.stop_moved and not tr.open
    last = tr.decisions[-1]
    assert (last.kind, last.price, last.pips) == (STOPPED_BY_IG, D("101.5"), D("0"))
    assert [r["decision"] for r in decisions(S)] == [STOP_MOVED, STOPPED_BY_IG]


def test_the_break_even_needs_6_up_in_an_earlier_bar(S):
    sender = MovingSender()
    m = TradeManager(S, sender, now=lambda: WED)
    tr = trade(S, BOLLINGER_BOUNCE, BUY)
    m.add(tr)
    for b in bars_from(WED, [(100.5, 101, 100, 100.5), (100.5, 107.5, 95, 96)]):   # 6 up and the old stop, one bar
        m.on_bar(b)
    assert sender.moves == [] and tr.decisions[-1].pips == D("-6")


def test_under_6_up_the_stop_is_not_moved(S):
    sender = MovingSender()
    m = TradeManager(S, sender, now=lambda: WED)
    tr = trade(S, BOLLINGER_BOUNCE, BUY)
    m.add(tr)
    for b in bars_from(WED, [(100.5, 101, 100, 100.5), (100.5, 107.4, 100.5, 107), (107, 107, 95, 96)]):
        m.on_bar(b)
    assert sender.moves == [] and tr.decisions[-1].pips == D("-6")


def test_the_stop_is_moved_once(S):
    sender = MovingSender()
    m = TradeManager(S, sender, now=lambda: WED)
    tr = trade(S, BOLLINGER_BOUNCE, SELL)                        # fill 100; closes on the buy price
    m.add(tr)
    for b in bars_from(WED, [(100, 100.5, 99, 99.5), (99.5, 99.5, 91, 92), (92, 93, 90, 91), (91, 92, 89, 90)]):
        m.on_bar(b)
    assert sender.moves == [("REF1", D("100"))] and tr.open


def test_live_a_refused_move_keeps_the_old_stop_and_is_tried_again_after_the_wait(S):
    clock = {"t": WED}
    sender = MovingSender([False, True])
    m = TradeManager(S, sender, now=lambda: clock["t"], ig_confirms=True)
    tr = trade(S, BOLLINGER_BOUNCE, BUY)
    m.add(tr)
    m.on_bar(bar(WED, 100.5, 108, 100.5, 107))                  # 6.5 up
    clock["t"] = WED + timedelta(seconds=5)
    m.on_bar(bar(WED, 107, 107, 102, 102))                      # IG refuses: the old stop stays
    assert not tr.stop_moved and tr.open and len(sender.moves) == 1
    clock["t"] = WED + timedelta(seconds=10)
    m.on_bar(bar(WED, 102, 103, 101, 102))                      # before orders.close_retry_seconds: not tried
    assert len(sender.moves) == 1 and tr.open                   # 101 is under the open price, over the old stop
    clock["t"] = WED + timedelta(seconds=5 + S.orders.close_retry_seconds)
    m.on_bar(bar(WED, 102, 103, 102, 102))                      # tried again: IG confirms
    assert len(sender.moves) == 2 and tr.stop_moved
    assert [r["decision"] for r in decisions(S)] == [STOP_NOT_MOVED, STOP_MOVED]
    assert "error.service.otc.invalid.stop" in decisions(S)[0]["why"]
    assert sender.alerts.infos and "break-even" in sender.alerts.infos[0]


def test_a_refused_move_leaves_the_trade_to_its_old_stop(S):
    sender = MovingSender([False, False, False])
    m = TradeManager(S, sender, now=lambda: WED, ig_confirms=True)
    tr = trade(S, BOLLINGER_BOUNCE, BUY)
    m.add(tr)
    for b in bars_from(WED, [(100.5, 108, 100.5, 107), (107, 107, 100, 100.5)]):    # back under the open price
        m.on_bar(b)
    assert tr.open and not tr.stop_moved                         # at break-even it would have been stopped
