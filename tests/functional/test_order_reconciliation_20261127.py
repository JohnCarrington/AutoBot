"""Execution integrity (owner's brief of 27 November 2026, Phase 1): uncertain order submissions, ownership of AutoBot's
positions, recovery of their management, and IG as the authority for realised results.

Reproduces the 25 November 2026 incident: the slow grind BUY sent at 18:02:03 (reference AB261125180203-7c0f9742) was
accepted by IG at once (IG's activity: "Position opened: XVXWHCBR" at 18:02:03, level 13120.5, stop 13105.5, limit
13140.5), but IG's confirmation answered 404 and the open positions did not show it during the bot's checks, so the
order was recorded "not found"; at 18:05:02 the regular check saw the position, with the bot's own deal reference, and
called it "not ours"; it was never managed, never counted by the safety rules (the 18:45 slow grind BUY opened), never
recorded, and IG's stop closed it at 22:00:00 at 13105.5 (-£150.00, IG's transactions). And the 26 November 06:01 bounce
5m BUY: its stop was expected at IG on the 09:20 candle, IG filled it at 09:35:01 at 13108.9, but the records kept the
bot's own 09:20 reading (13108.4, +4.5) instead of IG's (+5.0). A pretend IG; nothing here contacts IG."""

from datetime import timedelta
from decimal import Decimal as D
from types import SimpleNamespace

from strategies.common import BREAKOUT, BUY, SELL, SLOW_GRIND
from tests.technical.test_orders import EPIC, PretendIG, Reply, U, events, idea, make, records
from tests.technical import test_trading as tt
from tests.technical.test_trading import S  # noqa: F401  (orders, records and trade manager folders)

T0 = U(2026, 11, 25, 18, 2, 3)
REF_FMT = "AB261125180203-7c0f9742"


class LateIG(PretendIG):
    """IG accepting an order whose confirmation and position only become visible later (25 November 2026)."""
    def __init__(self, **kw):
        super().__init__(**kw)
        self.held: dict = {}

    list_lags = False                      # IG's list of open positions not showing a position IG has by its deal ID

    def request(self, method, path, version, body=None, *, what, headers=None):
        if method == "GET" and path.startswith("/history/activity"):      # as IG: only the window asked for
            from urllib.parse import parse_qs
            q = parse_qs(path.split("?", 1)[1])
            self.calls.append((method, path, version, body, headers))
            frm, to = q["from"][0], q["to"][0]
            return Reply({"activities": [a for a in self.activity if frm <= a["date"] <= to][:50]})
        if method == "GET" and path == "/positions" and self.list_lags:
            self.calls.append((method, path, version, body, headers))
            return Reply({"positions": []})
        if method == "POST" and path == "/positions/otc" and "_method" not in (headers or {}) and self.post_open == "late":
            self.calls.append((method, path, version, body, headers))
            self.held[body["dealReference"]] = body
            return Reply({"dealReference": body["dealReference"]})
        return super().request(method, path, version, body, what=what, headers=headers)

    def show(self, ref, confirm=True, level=13120.5, created="2026/11/25 18:02:03:000"):
        """IG's position (and, if `confirm`, its confirmation) appear now."""
        body = self.held.pop(ref)
        deal = f"DIAAA{self.next_deal}"
        self.next_deal += 1
        self.positions.append({"position": {"dealId": deal, "dealReference": ref, "direction": body["direction"],
                                            "size": body["size"], "level": level, "createdDateUTC": created.replace(" ", "T")},
                               "market": {"epic": EPIC}})
        if confirm:
            self.confirms[ref] = {"dealStatus": "ACCEPTED", "dealId": deal, "level": level, "dealReference": ref}
        return deal

    def opened_and_stopped(self, ref, open_at, open_level, close_at, close_level, stop, limit):
        """IG opened the order and its stop closed it while the bot did not know (IG's activity only)."""
        body = self.held.pop(ref)
        deal = f"DIAAA{self.next_deal}"
        self.next_deal += 1
        self.activity += [
            {"date": open_at, "epic": EPIC, "dealId": deal, "channel": "PUBLIC_WEB_API", "type": "POSITION",
             "status": "ACCEPTED", "description": f"Position opened: {deal[-8:]}",
             "details": {"dealReference": ref, "actions": [{"actionType": "POSITION_OPENED", "affectedDealId": deal}],
                         "direction": body["direction"], "level": open_level, "size": body["size"],
                         "stopLevel": stop, "limitLevel": limit}},
            {"date": close_at, "epic": EPIC, "dealId": "DICLOSE" + deal[-3:], "channel": "SYSTEM", "type": "POSITION",
             "status": "ACCEPTED", "description": f"Position/s closed: {deal[-8:]}",
             "details": {"dealReference": None, "actions": [{"actionType": "POSITION_CLOSED", "affectedDealId": deal}],
                         "direction": "SELL" if body["direction"] == "BUY" else "BUY", "level": close_level,
                         "size": body["size"], "stopLevel": stop, "limitLevel": limit}}]
        return deal


def recovery(strategy=SLOW_GRIND):
    return {"entry_price": "13119", "market_state": "trend up, slow grind", "reason": "slow grind: made up",
            "level": "", "steps": ["made up"], "take_profit_kind": "normal", "trend_day": None}


def late_order(S, clock_t=T0, strategy=SLOW_GRIND, direction=BUY):
    ig = LateIG()
    ig.post_open = "late"
    sender, ig, alerts, sleeps, clock = make(S, ig, t=clock_t)
    try:
        r = sender.place(idea(strategy, direction, t=clock_t, price="13119"), calendar=[], recovery=recovery(strategy))
    except TypeError:                       # the code before the fix has no recovery context (kept for the before run)
        r = sender.place(idea(strategy, direction, t=clock_t, price="13119"), calendar=[])
    return sender, ig, alerts, clock, r


# ---- before: what happened on 25 November ---------------------------------------------------------------------------

def test_the_25_november_order_ig_accepted_late_is_adopted_by_the_regular_check_not_called_not_ours(S):
    sender, ig, alerts, clock, r = late_order(S)
    assert (r.ok, r.what) == (False, "not found") and len(ig.orders_sent()) == 1
    deal = ig.show(r.reference)                                    # 18:05:02: IG's open positions show it
    clock["t"] = U(2026, 11, 25, 18, 5, 2)
    sender.reconcile("after the candle")
    ev = events(sender)
    assert "not ours" not in ev and "adopted" in ev
    (t,) = [t for t in sender.trades.values() if t.status == "open"]
    assert (t.reference, t.deal_id, t.strategy, t.level) == (r.reference, deal, SLOW_GRIND, D("13120.5"))
    assert t.opened_at == T0                                       # IG's own open time, not the moment it was found
    assert any(k == f"order-recovered-{r.reference}" for k, _ in alerts.sent)
    assert [x.reference for x in sender.take_recovered()] == [r.reference]
    assert len(ig.orders_sent()) == 1                              # never sent again


def test_while_an_order_is_unresolved_the_same_strategy_cannot_open_another(S):
    sender, ig, alerts, clock, r = late_order(S)
    clock["t"] = U(2026, 11, 25, 18, 45, 3)                         # the 18:45 slow grind BUY
    again = sender.place(idea(SLOW_GRIND, BUY, t=clock["t"], price="13127.1"), calendar=[])
    assert again.what == "safety refused" and "slow grind already has 1 trade(s) open" in again.reasons[0]
    assert f"order {r.reference} sent but not yet accounted for by IG" in again.reasons[-1]
    assert len(ig.orders_sent()) == 1


def test_an_unresolved_order_ig_opened_and_stopped_while_unknown_is_recorded_from_igs_activity_at_start_up(S):
    sender, ig, alerts, clock, r = late_order(S)
    ig.opened_and_stopped(r.reference, "2026-11-25T18:02:03", 13120.5, "2026-11-25T22:00:00", 13105.5, 13105.5, 13140.5)
    again, ig, alerts2, _, clock2 = make(S, ig, t=U(2026, 11, 27, 6, 39, 3))     # the 27 November start-up
    ev = events(again)
    assert "still unresolved" not in ev and "adopted" in ev
    (gone,) = [x for x in records(again) if x["event"] == "gone at IG"]
    assert (gone["reference"], gone["ig_level"], gone["ig_time_utc"]) == (r.reference, "13105.5", "2026-11-25T22:00:00Z")
    assert again.open_trades() == [] and r.reference in {g.reference for g in again.take_gone()}
    assert len(ig.orders_sent()) == 1


def test_an_order_ig_has_no_record_of_is_held_until_igs_own_records_settle_it(S):
    ig = LateIG()
    ig.post_open = "timeout"                                        # the order may never have reached IG
    sender, ig, alerts, sleeps, clock = make(S, ig, t=T0)
    r = sender.place(idea(BREAKOUT, SELL, t=T0), calendar=[])
    assert r.what == "not found"
    clock["t"] = T0 + timedelta(minutes=5)
    sender.reconcile("after the candle")
    assert [t.strategy for t in sender.open_trades()] == [BREAKOUT]         # still held: counted, not guessed away
    clock["t"] = T0 + timedelta(minutes=31)
    sender.reconcile("after the candle")
    assert sender.open_trades() == [] and records(sender)[-1]["event"] != "adopted"
    assert "not placed at IG" in events(sender)
    assert len(ig.orders_sent()) == 1


def test_a_position_with_an_autobot_reference_not_in_the_records_is_escalated_not_adopted(S):
    ig = PretendIG(positions=[{"position": {"dealId": "DIX1", "dealReference": "AB261125999999-deadbeef",
                                            "direction": "BUY", "size": 10.0, "level": 13100.0}, "market": {"epic": EPIC}},
                              {"position": {"dealId": "DIX2", "dealReference": "BYHAND1", "direction": "SELL",
                                            "size": 1.0, "level": 13100.0}, "market": {"epic": EPIC}}])
    sender, ig, alerts, *_ = make(S, ig)
    assert sender.open_trades() == []
    mine = [x for x in records(sender) if x["event"] == "not ours"]
    assert {x["deal_id"]: x.get("autobot_format") for x in mine} == {"DIX1": True, "DIX2": False}
    assert any("AutoBot's own format" in t and "DIX1" in t for _, t in alerts.sent)


def test_reconciliation_is_idempotent_one_adoption_one_trade_across_checks_and_restarts(S):
    sender, ig, alerts, clock, r = late_order(S)
    ig.show(r.reference)
    for _ in range(3):
        sender.reconcile("after the candle")
    again, *_ = make(S, ig, t=T0 + timedelta(minutes=10))
    third, *_ = make(S, ig, t=T0 + timedelta(minutes=20))
    assert events(third).count("adopted") == 1 and len(third.open_trades()) == 1
    assert len(ig.orders_sent()) == 1


def test_the_recovery_context_is_recorded_before_ig_is_contacted(S):
    ig = PretendIG()
    sender, ig, *_ = make(S, ig)
    sender.place(idea(SLOW_GRIND, BUY), calendar=[], recovery=recovery())
    import json
    sent = [json.loads(x) for x in ig.journal_at_post.splitlines() if '"sending"' in x][-1]
    assert sent["recovery"]["market_state"] == "trend up, slow grind" and sent["recovery"]["steps"] == ["made up"]


# ---- the engine: a recovered order is managed and recorded --------------------------------------------------------

def late_engine(S, monkeypatch):
    t0 = U(2026, 11, 4, 20, 0)
    cs = [tt.candle(t0 + timedelta(minutes=5 * k), 13400, 13400.5, 13399.5, 13400) for k in range(8)]
    ig = LateIG()
    ig.post_open = "late"
    e, ig, tracker, clock, quote = tt.make(S, monkeypatch, cs, {cs[0].start: [tt.idea(SLOW_GRIND, cs[0].start, BUY, price="13400")]},
                                           trading_on=True, ig=ig, clock={"t": t0})
    e.start(t0)
    tt.feed(e, clock, cs[:1])
    return e, ig, clock, cs


def test_a_recovered_order_is_managed_by_the_trade_manager_and_recorded_with_its_strategy(S, monkeypatch):
    e, ig, clock, cs = late_engine(S, monkeypatch)
    (ref,) = list(ig.held)
    assert e.manager.trades == {} and tt.trades_rows(e) == []              # "not found": nothing yet
    ig.show(ref, created="2026/11/04 20:05:00:000", level=13400.5)
    tt.feed(e, clock, cs[1:2])                                             # the regular check after the next candle
    assert ref in e.manager.trades and e.manager.trades[ref].open
    (opened,) = [x for x in tt.trades_rows(e) if x["event"] == "opened"]
    assert (opened["reference"], opened["strategy"], opened["open_price"]) == (ref, SLOW_GRIND, "13400.5")
    assert "recovered" in opened["reason"]
    tick = SimpleNamespace(time=U(2026, 11, 4, 20, 30, 2), buy=D("13401.0"), sell=D("13399.5"))
    clock["t"] = tick.time
    e.on_price(tick)                                                       # managed: the 20:30 UK close
    (closed,) = [x for x in tt.trades_rows(e) if x["event"] == "closed"]
    assert closed["reference"] == ref and closed["how_closed"] == "forced close"


def test_after_a_restart_an_order_ig_opened_and_stopped_meanwhile_is_recorded_opened_and_closed_once(S, monkeypatch):
    e, ig, clock, cs = late_engine(S, monkeypatch)
    (ref,) = list(ig.held)
    ig.opened_and_stopped(ref, "2026-11-04T20:05:00", 13400.5, "2026-11-04T20:21:00", 13385.5, 13385.5, 13420.5)
    clock["t"] = U(2026, 11, 4, 20, 25)
    for _ in range(2):                                                    # two restarts: recorded once
        again, *_ = tt.make(S, monkeypatch, cs[1:], {}, trading_on=True, ig=ig, clock=clock)
        again.start(U(2026, 11, 4, 20, 25))
    rows = tt.trades_rows(again)
    assert [x["event"] for x in rows] == ["opened", "closed"]
    closed = rows[1]
    assert (closed["close_price"], closed["closed_utc"], closed["pips"], closed["gbp"]) == \
        ("13385.5", "2026-11-04T20:21:00Z", "-15.0", "-150.00")


# ---- IG is the authority for realised results ---------------------------------------------------------------------

def stop_engine(S, monkeypatch):
    """A slow grind SELL from 13400.5 (stop 15: 13415.5 at IG); the 20:20 candle's offer reaches 13416.0."""
    t0 = U(2026, 11, 4, 20, 0)
    cs = [tt.candle(t0, 13400, 13400.5, 13399.5, 13400), tt.candle(t0 + timedelta(minutes=5), 13400, 13400.5, 13399.5, 13400),
          tt.candle(t0 + timedelta(minutes=10), 13405, 13414.5, 13404, 13410),
          tt.candle(t0 + timedelta(minutes=15), 13410, 13411, 13409, 13410),
          tt.candle(t0 + timedelta(minutes=20), 13410, 13411, 13409, 13410)]
    e, ig, tracker, clock, quote = tt.make(S, monkeypatch, cs, {cs[0].start: [tt.idea(SLOW_GRIND, cs[0].start, price="13400")]},
                                           trading_on=True, clock={"t": t0})
    e.start(t0)
    tt.feed(e, clock, cs[:2])
    return e, e.sender.client, clock, cs


def test_a_stop_ig_fills_after_the_bot_expected_it_is_recorded_at_igs_level_and_time(S, monkeypatch):
    e, ig, clock, cs = stop_engine(S, monkeypatch)
    (ref,) = list(e.manager.trades)
    deal = e.sender.trades[ref].deal_id
    tt.feed(e, clock, cs[2:3])                                             # the bot expects IG's stop; IG has not closed yet
    assert e.manager.trades[ref].open and [x["event"] for x in tt.trades_rows(e)] == ["opened"]
    ig.system_close(deal, 13416.3, "2026-11-04T20:17:40", stop=13415.5)   # IG's stop fills later, worse, at 13416.3
    tt.feed(e, clock, cs[3:4])
    (closed,) = [x for x in tt.trades_rows(e) if x["event"] == "closed"]
    assert (closed["close_price"], closed["closed_utc"], closed["pips"]) == ("13416.3", "2026-11-04T20:17:40Z", "-15.8")


def test_a_close_whose_igs_level_is_not_known_yet_is_corrected_from_igs_activity_later(S, monkeypatch):
    e, ig, clock, cs = stop_engine(S, monkeypatch)
    (ref,) = list(e.manager.trades)
    deal = e.sender.trades[ref].deal_id
    ig.positions = [p for p in ig.positions if p["position"]["dealId"] != deal]   # IG closed it; its activity lags
    tt.feed(e, clock, cs[2:3])
    (closed,) = [x for x in tt.trades_rows(e) if x["event"] == "closed"]
    assert closed["price_source"].startswith("the bot's")                   # never presented as IG's
    ig.activity.append({"date": "2026-11-04T20:14:30", "epic": EPIC, "dealId": "DISYS1", "channel": "SYSTEM",
                        "type": "POSITION", "status": "ACCEPTED", "description": "Position/s closed",
                        "details": {"actions": [{"actionType": "POSITION_CLOSED", "affectedDealId": deal}],
                                    "level": 13416.3, "stopLevel": 13415.5, "limitLevel": None}})
    tt.feed(e, clock, cs[3:4])
    (fix,) = [x for x in tt.trades_rows(e) if x["event"] == "close corrected"]
    assert (fix["close_price"], fix["closed_utc"], fix["pips"], fix["gbp"]) == ("13416.3", "2026-11-04T20:14:30Z", "-15.8", "-158.00")
    (row,) = e.book.closed_trades()
    assert (row["close_price"], row["gbp"], row["price_source"]) == ("13416.3", "-158.00", "IG's activity")
    assert e.book.today(U(2026, 11, 4, 20, 30)).gbp == D("-158.00")
    tt.feed(e, clock, cs[4:5])
    assert len([x for x in tt.trades_rows(e) if x["event"] == "close corrected"]) == 1      # once


def test_a_correction_of_a_half_closed_trade_keeps_the_half_and_corrects_the_rest(S):
    from records.book import apply_corrections
    rows = [{"event": "closed", "reference": "R1", "direction": "sell", "open_price": "13400.0", "size_gbp_per_pip": 10,
             "close_price": "13402.0", "pips": "1.0", "gbp": "10.00", "result": "win",
             "half_close": {"pips": "4.0", "gbp": "20.00"}, "rest": {"pips": "-2.0", "gbp": "-10.00", "price": "13402.0"}},
            {"event": "close corrected", "reference": "R1", "close_price": "13403.0", "closed_utc": "2026-11-04T20:30:05Z"}]
    (r,) = apply_corrections(rows)
    assert (r["close_price"], r["rest"]["pips"], r["rest"]["gbp"], r["pips"], r["gbp"]) == \
        ("13403.0", "-3.0", "-15.00", "0.5", "5.00")


def test_the_dashboard_history_reads_the_corrected_figures(S, tmp_path):
    import json
    from records.book import apply_corrections
    f = tmp_path / "trades.jsonl"
    f.write_text("\n".join(json.dumps(x) for x in [
        {"event": "closed", "reference": "R2", "direction": "buy", "open_price": "13100.0", "size_gbp_per_pip": 10,
         "close_price": "13108.4", "closed_utc": "2026-11-26T09:20:00Z", "pips": "8.4", "gbp": "84.00", "result": "win"},
        {"event": "close corrected", "reference": "R2", "close_price": "13108.9", "closed_utc": "2026-11-26T09:35:01Z"}]))
    rows = apply_corrections([json.loads(x) for x in f.read_text().splitlines()])
    assert [(r["close_price"], r["closed_utc"], r["gbp"]) for r in rows] == [("13108.9", "2026-11-26T09:35:01Z", "89.00")]


def test_an_order_settled_days_later_is_recorded_from_igs_own_open_and_close(S):
    """The production case: AB261125180203-7c0f9742 is still unresolved in the record; at the next start-up (here
    two days later) IG's activity gives its open (18:02:03, 13120.5) and its stop (22:00:00, 13105.5)."""
    sender, ig, alerts, clock, r = late_order(S)
    for k in range(60):                                         # IG's other activity in between (more than one page)
        ig.activity.append({"date": f"2026-11-26T{6 + k // 6:02d}:{(k % 6) * 10:02d}:00", "epic": EPIC, "dealId": f"DIO{k}",
                            "channel": "PUBLIC_WEB_API", "type": "POSITION", "status": "ACCEPTED",
                            "description": "Position edited", "details": {"dealReference": None, "actions": []}})
    ig.opened_and_stopped(r.reference, "2026-11-25T18:02:03", 13120.5, "2026-11-25T22:00:00", 13105.5, 13105.5, 13140.5)
    again, ig, alerts2, _, _ = make(S, ig, t=U(2026, 11, 27, 6, 39, 3))
    (adopted,) = [x for x in records(again) if x["event"] == "adopted"]
    assert (adopted["level"], adopted["opened_utc"], adopted["deal_id"]) == ("13120.5", "2026-11-25T18:02:03Z", "DIAAA1")
    (gone,) = [x for x in records(again) if x["event"] == "gone at IG"]
    assert (gone["ig_level"], gone["ig_time_utc"], gone["level_source"]) == ("13105.5", "2026-11-25T22:00:00Z", "IG's activity")


def test_a_confirmation_that_answers_404_then_accepted_is_adopted_even_while_igs_position_list_lags(S):
    sender, ig, alerts, clock, r = late_order(S)
    deal = ig.show(r.reference)                                 # IG now has the position and the confirmation ...
    ig.list_lags = True                                         # ... but its list of positions does not show it yet
    clock["t"] = T0 + timedelta(minutes=3)
    sender.reconcile("after the candle")
    (t,) = [t for t in sender.trades.values() if t.status == "open"]
    assert t.deal_id == deal and "not ours" not in events(sender) and len(ig.orders_sent()) == 1


def test_the_requested_calculated_and_actual_prices_are_all_kept(S, monkeypatch):
    e, ig, clock, cs = stop_engine(S, monkeypatch)
    (ref,) = list(e.manager.trades)
    sent = [x for x in tt.journal(e) if x["event"] == "sending"][0]
    opened = [x for x in tt.journal(e) if x["event"] == "opened"][0]
    (row,) = [x for x in tt.trades_rows(e) if x["event"] == "opened"]
    assert (sent["idea_price"], sent["stop_distance"]) == ("13400", "15")      # requested: the idea; calculated: the stop
    assert (opened["level"], opened["stop_level"] if "stop_level" in opened else None) == ("13400.5", None)
    assert (row["entry_price"], row["open_price"]) == ("13400", "13400.5")       # the idea and IG's actual fill


def test_a_full_page_of_igs_activity_never_counts_as_ig_having_no_record(S):
    ig = LateIG()
    ig.post_open = "timeout"
    sender, ig, alerts, sleeps, clock = make(S, ig, t=T0)
    r = sender.place(idea(BREAKOUT, SELL, t=T0), calendar=[])
    ig.activity = [{"date": f"2026-11-25T18:{10 + k // 6:02d}:{(k % 6) * 10:02d}", "epic": EPIC, "dealId": f"DIO{k}",
                    "channel": "PUBLIC_WEB_API", "type": "POSITION", "status": "ACCEPTED", "description": "edited",
                    "details": {"dealReference": None, "actions": []}} for k in range(60)]
    clock["t"] = T0 + timedelta(minutes=45)
    sender.reconcile("after the candle")
    assert "not placed at IG" not in events(sender) and [t.strategy for t in sender.open_trades()] == [BREAKOUT]
