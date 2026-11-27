"""Independent review of execution integrity commit 5902147 (27 November 2026): R1 an accepted order whose position
IG does not show yet; R2 a restart during the hand-over of a recovered order; R3 a restart during a financial
correction, and IG confirming the provisional figures; R4 an order IG shows after it was recorded "not placed at IG".
Plus: a recovered position takes IG's size, fill, stop and limit; every summary reads the corrected records. A pretend
IG; nothing here contacts IG."""

import json
from datetime import timedelta
from decimal import Decimal as D
from types import SimpleNamespace

from strategies.common import BREAKOUT, BUY, SELL, SLOW_GRIND
from tests.functional.test_order_reconciliation_20261127 import (T0, LateIG, late_engine, late_order, recovery,
                                                                 stop_engine)
from tests.technical.test_orders import EPIC, events, idea, make, records
from tests.technical import test_trading as tt
from tests.technical.test_trading import S  # noqa: F401

U = tt.U


def opened_rows(e):
    return [x for x in tt.trades_rows(e) if x["event"] == "opened"]


def closed_rows(e):
    return [x for x in tt.trades_rows(e) if x["event"] == "closed"]


def restart(S, monkeypatch, ig, clock, cs, at):
    clock["t"] = at
    again, *_ = tt.make(S, monkeypatch, cs, {}, trading_on=True, ig=ig, clock=clock)
    again.start(at)
    return again


# ---- R1: accepted at IG, its position not visible yet -----------------------------------------------------------------

def test_r1_an_accepted_order_whose_position_is_not_visible_yet_is_never_recorded_closed(S):
    sender, ig, alerts, clock, r = late_order(S)
    ig.held.pop(r.reference)
    ig.confirms[r.reference] = {"dealStatus": "ACCEPTED", "dealId": "DILAG1", "level": 13120.5, "dealReference": r.reference}
    for k in (3, 8):                                           # IG: accepted, but no position by list or by deal ID yet
        clock["t"] = T0 + timedelta(minutes=k)
        sender.reconcile("after the candle")
        ev = events(sender)
        assert "gone at IG" not in ev and "adopted" not in ev and "not placed at IG" not in ev
        assert [t.strategy for t in sender.open_trades()] == [SLOW_GRIND]           # still counted
    ig.positions.append({"position": {"dealId": "DILAG1", "dealReference": r.reference, "direction": "BUY",
                                      "size": 10.0, "level": 13120.5}, "market": {"epic": EPIC}})
    clock["t"] = T0 + timedelta(minutes=13)
    sender.reconcile("after the candle")
    (t,) = [t for t in sender.trades.values() if t.status == "open"]
    assert (t.deal_id, t.level) == ("DILAG1", D("13120.5")) and "gone at IG" not in events(sender)


def test_r1_an_accepted_order_is_recorded_closed_only_on_igs_own_evidence_of_the_close(S):
    sender, ig, alerts, clock, r = late_order(S)
    ig.held.pop(r.reference)
    ig.confirms[r.reference] = {"dealStatus": "ACCEPTED", "dealId": "DILAG2", "level": 13120.5, "dealReference": r.reference}
    ig.activity.append({"date": "2026-11-25T18:20:00", "epic": EPIC, "dealId": "DICL2", "channel": "SYSTEM",
                        "type": "POSITION", "status": "ACCEPTED", "description": "Position/s closed",
                        "details": {"actions": [{"actionType": "POSITION_CLOSED", "affectedDealId": "DILAG2"}],
                                    "level": 13105.5, "stopLevel": 13105.5, "limitLevel": 13140.5}})
    clock["t"] = T0 + timedelta(minutes=25)
    sender.reconcile("after the candle")
    (g,) = [x for x in records(sender) if x["event"] == "gone at IG"]
    assert (g["ig_level"], g["ig_time_utc"]) == ("13105.5", "2026-11-25T18:20:00Z") and sender.open_trades() == []


# ---- R2: a restart during the hand-over of a recovered order --------------------------------------------------------

def test_r2_adoption_recorded_but_not_handed_to_the_engine_is_recovered_after_a_restart(S, monkeypatch):
    e, ig, clock, cs = late_engine(S, monkeypatch)
    (ref,) = list(ig.held)
    ig.show(ref, created="2026/11/04 20:05:00:000", level=13400.5)
    clock["t"] = cs[1].end
    e.sender.reconcile("after the candle")                    # "adopted" written ... then the process stops
    assert "adopted" in [x["event"] for x in tt.journal(e)] and opened_rows(e) == []
    again = restart(S, monkeypatch, ig, clock, cs[2:], cs[1].end)
    assert [x["reference"] for x in opened_rows(again)] == [ref] and again.manager.trades[ref].open
    third = restart(S, monkeypatch, ig, clock, cs[2:], cs[1].end + timedelta(seconds=30))
    assert len(opened_rows(third)) == 1                       # exactly once
    tick = SimpleNamespace(time=U(2026, 11, 4, 20, 30, 2), buy=D("13401.0"), sell=D("13399.5"))
    clock["t"] = tick.time
    third.on_price(tick)                                      # managed: its close recorded
    assert [x["reference"] for x in closed_rows(third)] == [ref]


def test_r2_trade_manager_state_saved_but_no_opened_record_is_recorded_once_after_a_restart(S, monkeypatch):
    from trade_manager.manager import plan
    e, ig, clock, cs = late_engine(S, monkeypatch)
    (ref,) = list(ig.held)
    ig.show(ref, created="2026/11/04 20:05:00:000", level=13400.5)
    clock["t"] = cs[1].end
    e.sender.reconcile("after the candle")
    (t,) = e.sender.take_recovered()
    mt = plan(S, ref, t.strategy, t.direction, t.opened_at, t.level, t.level, t.stop_pips, [], None)
    e.manager.add(mt)
    e.manager.save_state()                                    # ... then the process stops before the record
    again = restart(S, monkeypatch, ig, clock, cs[2:], cs[1].end)
    assert [x["reference"] for x in opened_rows(again)] == [ref] and again.manager.trades[ref].open


def test_r2_a_recovered_trade_ig_had_closed_is_recorded_opened_and_closed_once_after_a_restart(S, monkeypatch):
    e, ig, clock, cs = late_engine(S, monkeypatch)
    (ref,) = list(ig.held)
    ig.opened_and_stopped(ref, "2026-11-04T20:05:00", 13400.5, "2026-11-04T20:21:00", 13385.5, 13385.5, 13420.5)
    clock["t"] = U(2026, 11, 4, 20, 25)
    e.sender.reconcile("after the candle")                    # "adopted" and "gone at IG" written ... then it stops
    assert tt.trades_rows(e) == []
    for k in range(2):
        again = restart(S, monkeypatch, ig, clock, cs[5:], U(2026, 11, 4, 20, 26 + k))
    assert [x["event"] for x in tt.trades_rows(again)] == ["opened", "closed"]
    c = closed_rows(again)[0]
    assert (c["close_price"], c["closed_utc"], c["gbp"]) == ("13385.5", "2026-11-04T20:21:00Z", "-150.00")


# ---- R3: a restart during a financial correction ---------------------------------------------------------------------

def lagging_close(S, monkeypatch):
    e, ig, clock, cs = stop_engine(S, monkeypatch)
    (ref,) = list(e.manager.trades)
    deal = e.sender.trades[ref].deal_id
    ig.positions = [p for p in ig.positions if p["position"]["dealId"] != deal]
    tt.feed(e, clock, cs[2:3])                                # recorded at the bot's price
    return e, ig, clock, cs, ref, deal


def close_activity(deal, when, level):
    return {"date": when, "epic": EPIC, "dealId": "DISYS1", "channel": "SYSTEM", "type": "POSITION", "status": "ACCEPTED",
            "description": "Position/s closed", "details": {"actions": [{"actionType": "POSITION_CLOSED",
                                                                         "affectedDealId": deal}],
                                                            "level": level, "stopLevel": 13415.5, "limitLevel": None}}


def test_r3_a_correction_confirmed_at_ig_but_not_yet_recorded_is_applied_once_after_a_restart(S, monkeypatch):
    e, ig, clock, cs, ref, deal = lagging_close(S, monkeypatch)
    ig.activity.append(close_activity(deal, "2026-11-04T20:14:30", 13416.3))
    clock["t"] = cs[3].end
    e.sender.reconcile("after the candle")                    # IG_CLOSE_CONFIRMED written ... then the process stops
    assert "IG close confirmed" in [x["event"] for x in tt.journal(e)]
    assert [x for x in tt.trades_rows(e) if x["event"] == "close corrected"] == []
    for k in range(2):
        again = restart(S, monkeypatch, ig, clock, cs[4:], cs[3].end + timedelta(seconds=10 * k))
    (fix,) = [x for x in tt.trades_rows(again) if x["event"] == "close corrected"]
    assert (fix["close_price"], fix["gbp"]) == ("13416.3", "-158.00")
    assert again.book.closed_trades()[0]["price_source"] == "IG's activity"


def test_r3_ig_confirming_the_provisional_figures_changes_their_source_not_the_figures(S, monkeypatch):
    e, ig, clock, cs, ref, deal = lagging_close(S, monkeypatch)
    (row,) = closed_rows(e)
    ig.activity.append(close_activity(deal, row["closed_utc"].rstrip("Z"), float(row["close_price"])))
    tt.feed(e, clock, cs[3:4])
    (fix,) = [x for x in tt.trades_rows(e) if x["event"] == "close corrected"]
    (now,) = e.book.closed_trades()
    assert (now["close_price"], now["gbp"], now["closed_utc"]) == (row["close_price"], row["gbp"], row["closed_utc"])
    assert now["price_source"] == "IG's activity" and row["price_source"].startswith("the bot's")


# ---- R4: an order IG shows after "not placed at IG" ------------------------------------------------------------------

def test_r4_an_order_ig_shows_after_not_placed_at_ig_is_still_recovered_as_the_bots_and_counted(S):
    ig = LateIG()
    ig.post_open = "late"
    sender, ig, alerts, sleeps, clock = make(S, ig, t=T0)
    r = sender.place(idea(BREAKOUT, SELL, t=T0, price="13119"), calendar=[], recovery=recovery(BREAKOUT))
    clock["t"] = T0 + timedelta(minutes=31)
    sender.reconcile("after the candle")
    assert "not placed at IG" in events(sender) and sender.open_trades() == []
    deal = ig.show(r.reference, created="2026/11/25 18:40:00:000")     # IG shows it after all
    clock["t"] = T0 + timedelta(minutes=40)
    sender.reconcile("after the candle")
    ev = events(sender)
    assert "not ours" not in ev and ev.count("adopted") == 1
    (t,) = [t for t in sender.trades.values() if t.status == "open"]
    assert (t.deal_id, t.strategy) == (deal, BREAKOUT) and [x.strategy for x in sender.open_trades()] == [BREAKOUT]
    assert any(k == f"order-recovered-{r.reference}" for k, _ in alerts.sent)
    again, *_ = make(S, ig, t=T0 + timedelta(minutes=45))     # and after a restart
    assert [x.deal_id for x in again.open_trades()] == [deal] and "not ours" not in events(again)


# ---- the broker's size, fill, stop and limit; summaries -----------------------------------------------------------

def test_a_recovered_position_takes_igs_size_fill_stop_and_limit(S, monkeypatch):
    e, ig, clock, cs = late_engine(S, monkeypatch)
    (ref,) = list(ig.held)
    ig.show(ref, created="2026/11/04 20:05:00:000", level=13400.9)
    pos = ig.positions[-1]["position"]
    pos.update(size=10.0, stopLevel=13385.4, limitLevel=13420.9)    # IG's stop 15.5 below the fill, limit 20 above
    tt.feed(e, clock, cs[1:2])
    (row,) = opened_rows(e)
    assert (row["open_price"], row["stop_price"], row["take_profit_price"]) == ("13400.9", "13385.4", "13420.9")
    assert (row["stop_pips"], row["take_profit_pips"]) == ("15.5", "20.0")
    t = e.sender.trades[ref]
    assert (t.size, t.stop_pips, t.recovery["ig_stop_level"], t.recovery["ig_limit_level"]) == \
        (D("10.0"), D("15.5"), "13385.4", "13420.9")
    assert t.stop_level is None                               # IG's stop as attached, not a moved stop


def test_the_daily_and_weekly_summaries_read_the_corrected_records(S, monkeypatch):
    e, ig, clock, cs, ref, deal = lagging_close(S, monkeypatch)
    ig.activity.append(close_activity(deal, "2026-11-04T20:14:30", 13416.3))
    tt.feed(e, clock, cs[3:4])
    from datetime import date
    s = e.book.write_daily(date(2026, 11, 4))
    week = json.loads(next((e.book.folder / "summaries" / "weekly").glob("*.json")).read_text())
    daily = json.loads((e.book.folder / "summaries" / "daily" / "2026-11-04.json").read_text())
    assert s.gbp == D("-158.00") and daily["gbp"] == "-158.00" and week["gbp"] == "-158.00"
