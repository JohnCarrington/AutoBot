"""Pre-deployment verification of exec-integrity (27 November 2026): a recovered position is managed, counted and
recorded with IG's ACTUAL size, stop and limit (not the configured ones), recovery never loosens IG's stop, and an
order IG once confirmed as accepted is never later recorded "not placed at IG". A pretend IG; nothing contacts IG."""

from datetime import timedelta
from decimal import Decimal as D
from types import SimpleNamespace

from strategies.common import SLOW_GRIND
from tests.functional.test_order_reconciliation_20261127 import T0, late_engine, late_order
from tests.functional.test_order_recovery_review_20261127 import closed_rows, opened_rows, restart
from tests.technical.test_orders import events, make, records
from tests.technical import test_trading as tt
from tests.technical.test_trading import S  # noqa: F401

U = tt.U


def recovered(S, monkeypatch, size=10.0, stop=None, limit=None, level=13400.5):
    e, ig, clock, cs = late_engine(S, monkeypatch)
    (ref,) = list(ig.held)
    ig.show(ref, created="2026/11/04 20:05:00:000", level=level)
    pos = ig.positions[-1]["position"]
    pos["size"] = size
    if stop is not None:
        pos["stopLevel"] = stop
    if limit is not None:
        pos["limitLevel"] = limit
    tt.feed(e, clock, cs[1:2])
    return e, ig, clock, cs, ref


# ---- 1. IG's actual position size -------------------------------------------------------------------------------

def test_a_recovered_position_of_another_size_is_counted_managed_and_recorded_at_igs_size(S, monkeypatch):
    e, ig, clock, cs, ref = recovered(S, monkeypatch, size=5.0)        # configured: £10 a pip; IG has £5 a pip
    (row,) = opened_rows(e)
    assert row["size_gbp_per_pip"] in (5, "5", "5.0")
    (ot,) = e.sender.open_trades()
    assert ot.size_gbp_per_pip == D("5") and ot.risk_gbp == D("75")   # exposure: 15 pips x £5
    tick = SimpleNamespace(time=U(2026, 11, 4, 20, 30, 2), buy=D("13401.0"), sell=D("13399.5"))
    clock["t"] = tick.time
    e.on_price(tick)                                                    # the 20:30 close: IG confirms 13390.0
    closes = [c for c in ig.calls if len(c) == 5 and (c[4] or {}).get("_method") == "DELETE"]
    assert closes[-1][3]["size"] == 5.0                                 # the whole position, IG's size
    (c,) = closed_rows(e)
    assert (c["pips"], c["gbp"]) == ("-10.5", "-52.50")                 # -10.5 pips x £5, not x £10


# ---- 2. IG's actual stop and limit, in the trade manager -------------------------------------------------------

def test_the_trade_manager_runs_a_recovered_trade_on_igs_actual_stop_and_limit(S, monkeypatch):
    # the slow grind's own stop is 15 and its take profit 20; IG has 8 and 10 attached (tighter)
    e, ig, clock, cs, ref = recovered(S, monkeypatch, stop=13392.5, limit=13410.5)
    mt = e.manager.trades[ref]
    assert (mt.stop_pips, mt.take_profit_pips) == (D("8"), D("10"))     # never loosened to the strategy's 15 / 20
    up = tt.candle(cs[2].start, 13401, 13411, 13400, 13410)             # the bid reaches IG's limit 13410.5
    again = restart(S, monkeypatch, ig, clock, [up], cs[1].end + timedelta(seconds=5))
    mt2 = again.manager.trades[ref]
    assert (mt2.stop_pips, mt2.take_profit_pips) == (D("8"), D("10"))  # the same after a restart
    clock["t"] = up.end
    again.on_candle(up.end)
    assert any(d.kind == "take profit hit at IG" for d in again.manager.trades[ref].decisions) or \
        again.manager.trades[ref].expected_at_ig[0] == "take profit hit at IG"


def test_recovery_never_sends_a_looser_stop_than_igs(S, monkeypatch):
    e, ig, clock, cs, ref = recovered(S, monkeypatch, stop=13392.5, limit=13420.5)
    tt.feed(e, clock, cs[2:5])
    moves = [c for c in ig.calls if c[0] == "PUT"]
    assert all(c[3]["stopLevel"] >= 13392.5 for c in moves)             # a BUY: a move only ever raises the stop


# ---- 3. an order IG confirmed as accepted is never "not placed" -------------------------------------------------

def test_an_order_once_confirmed_accepted_is_never_recorded_not_placed_when_igs_evidence_goes_quiet(S):
    sender, ig, alerts, clock, r = late_order(S)
    ig.held.pop(r.reference)
    ig.confirms[r.reference] = {"dealStatus": "ACCEPTED", "dealId": "DIACC1", "level": 13120.5, "dealReference": r.reference}
    clock["t"] = T0 + timedelta(minutes=3)
    sender.reconcile("after the candle")                                # IG confirms: accepted as DIACC1
    del ig.confirms[r.reference]                                        # then IG's confirmation answers 404
    for k in (40, 90):                                                  # no position, no activity, long past 30 min
        clock["t"] = T0 + timedelta(minutes=k)
        sender.reconcile("after the candle")
        assert "not placed at IG" not in events(sender)
        assert [t.strategy for t in sender.open_trades()] == [SLOW_GRIND]
    again, ig2, *_ = make(S, ig, t=T0 + timedelta(minutes=120))         # and after a restart
    assert "not placed at IG" not in events(again) and [t.strategy for t in again.open_trades()] == [SLOW_GRIND]
    (acc,) = [x for x in records(again) if x["event"] == "accepted at IG"]
    assert acc["deal_id"] == "DIACC1"
    ig.positions.append({"position": {"dealId": "DIACC1", "dealReference": None, "direction": "BUY", "size": 10.0,
                                      "level": 13120.5}, "market": {"epic": tt.PretendIG and "CS.D.GBPUSD.TODAY.IP"}})
    again.reconcile("after the candle")                                 # found by IG's deal ID alone
    assert [t.deal_id for t in again.trades.values() if t.status == "open"] == ["DIACC1"]
    assert "not ours" not in events(again)
