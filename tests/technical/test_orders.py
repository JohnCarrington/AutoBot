"""Technical tests for the order sender (design sections 6 and 7), with a pretend IG. Nothing here
contacts IG or sends a real order."""

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from config.settings_loader import load_settings
from ig.errors import IGRequestError
from orders.sender import NotReady, OrderSender
from strategies.common import (BOLLINGER_BOUNCE, BREAKOUT, BUY, EMA_PULLBACK, LEVEL_REVERSAL, RANGE_TRADE, SELL,
                               SLOW_GRIND, Idea)

U = lambda *a: datetime(*a, tzinfo=timezone.utc)  # noqa: E731
WED = U(2026, 11, 4, 10, 0)
EPIC = "CS.D.GBPUSD.TODAY.IP"
DEMO_URL = "https://demo-api.ig.com/gateway/deal"
BOE_CAL = [{"time_utc": "2026-11-05T12:00:00Z", "country": "GB", "event": "BoE Interest Rate Decision",
            "estimate": 4.0, "prev": 4.0, "actual": None, "impact": "high", "unit": "%"}]


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
    s = load_settings(switches_from=pretend_switches).for_pair("GBPUSD")
    return Over(s, switches={k: True for k in ("slow_grind", "ema_pullback", "bollinger_bounce", "range_trade",
                                                 "breakout", "level_reversal")},
                orders={"folder": tmp_path / "orders"}, safety={"folder": tmp_path / "safety"})


class Reply:
    def __init__(self, body=None):
        self.body, self.status_code = body, 200

    def json(self):
        return self.body


class PretendIG:
    """Stands in for the price service's IG client: answers from a script, records every call."""
    def __init__(self, positions=(), confirms=None, available=20000.0, base_url=DEMO_URL, active=True):
        self.base_url, self.account_active = base_url, active
        self.positions = list(positions)                    # IG's open positions
        self.confirms = confirms if confirms is not None else {}   # reference -> confirmation (or a list of answers)
        self.available = available
        self.calls, self.post_open = [], None               # post_open: what to do with POST /positions/otc
        self.close_answer = "accept"
        self.journal_at_post = None
        self.journal = None
        self.next_deal = 1

    def login(self):
        raise AssertionError("the order sender must never log in")

    connect = login

    def account_balance(self):
        self.calls.append(("GET", "/accounts"))
        if isinstance(self.available, Exception):
            raise self.available
        return {"balance": 20000.0, "available": self.available}

    def request(self, method, path, version, body=None, *, what, headers=None):
        self.calls.append((method, path, version, body, headers))
        if method == "GET" and path == "/positions":
            return Reply({"positions": self.positions})
        if method == "GET" and path.startswith("/confirms/"):
            ref = path.split("/")[-1]
            got = self.confirms.get(ref)
            if isinstance(got, list):
                got = got.pop(0) if got else None
            if got is None:
                raise IGRequestError(what, 404, "error.confirms.deal-not-found")
            return Reply(got)
        if method == "GET" and path.startswith("/markets/"):
            return Reply({"dealingRules": {"minNormalStopOrLimitDistance": {"unit": "POINTS", "value": 8.0}}})
        if method == "GET" and path.startswith("/positions/"):
            deal = path.split("/")[-1]
            p = next((p for p in self.positions if p["position"]["dealId"] == deal), None)
            if p is None:
                raise IGRequestError(what, 404, "error.positions.generic.position.not.found")
            return Reply(p)
        if method == "POST" and path == "/positions/otc" and "_method" not in headers:     # an order
            self.journal_at_post = self.journal.read_text() if self.journal and self.journal.exists() else ""
            ref = body["dealReference"]
            act = self.post_open or "accept"
            if act == "timeout":
                raise IGRequestError(what, None, "ReadTimeout")
            if act == "timeout-but-done":
                self._fill(ref, body)
                raise IGRequestError(what, None, "ReadTimeout")
            if act == "timeout-position-only":
                self._fill(ref, body, confirm=False)
                raise IGRequestError(what, None, "ReadTimeout")
            if act == "http-400":
                raise IGRequestError(what, 400, "validation.null-not-allowed.request")
            if isinstance(act, dict):                       # a confirmation to give (e.g. REJECTED)
                self.confirms[ref] = dict(act, dealReference=ref)
                return Reply({"dealReference": ref})
            self._fill(ref, body)
            return Reply({"dealReference": ref})
        if method == "POST" and path == "/positions/otc" and headers.get("_method") == "DELETE":   # a close
            if self.close_answer == "timeout":
                raise IGRequestError(what, None, "ReadTimeout")
            if self.close_answer == "timeout-done":
                self._close(body)
                raise IGRequestError(what, None, "ReadTimeout")
            ref = f"CLOSE{len(self.calls)}"
            if self.close_answer == "reject":
                self.confirms[ref] = {"dealStatus": "REJECTED", "reason": "POSITION_NOT_AVAILABLE_TO_CLOSE"}
            else:
                self._close(body)
                self.confirms[ref] = {"dealStatus": "ACCEPTED", "level": 13390.0, "profit": 100.0}
            return Reply({"dealReference": ref})
        raise AssertionError(f"unexpected call {method} {path}")

    def _fill(self, ref, body, confirm=True):
        deal = f"DIAAA{self.next_deal}"
        self.next_deal += 1
        self.positions.append({"position": {"dealId": deal, "dealReference": ref, "direction": body["direction"],
                                            "size": body["size"], "level": 13400.5}, "market": {"epic": EPIC}})
        if confirm:
            self.confirms[ref] = {"dealStatus": "ACCEPTED", "dealId": deal, "level": 13400.5, "reason": "SUCCESS",
                                  "dealReference": ref}

    def _close(self, body):
        p = next(p for p in self.positions if p["position"]["dealId"] == body["dealId"])
        left = p["position"]["size"] - body["size"]
        if left <= 0:
            self.positions.remove(p)
        else:
            p["position"]["size"] = left

    def orders_sent(self):
        return [c for c in self.calls if c[0] == "POST" and c[1] == "/positions/otc" and "_method" not in c[4]]


class FakeAlerts:
    def __init__(self):
        self.sent = []

    def problem(self, key, text):
        self.sent.append((key, text))


def idea(strategy, direction=SELL, t=WED, price="13400.0", context=None):
    ctx = context if context is not None else ({"stop_price": D("13410.0")} if strategy == LEVEL_REVERSAL else {})
    return Idea("GBPUSD", strategy, direction, t, D(price), "trend", "down", None, "sell side", ["made up"], True, "", ctx)


def make(S, ig=None, t=WED, start=True, quote=(D("13400.0"), D("13401.5"))):
    ig = ig or PretendIG()
    alerts = FakeAlerts()
    clock = {"t": t}
    sleeps = []
    sender = OrderSender(S, ig, alerts, now=lambda: clock["t"], sleep=sleeps.append, quote=lambda: quote)
    ig.journal = sender.journal
    if start:
        sender.start()
    return sender, ig, alerts, sleeps, clock


def closes(ig):
    return [c for c in ig.calls if len(c) == 5 and (c[4] or {}).get("_method")]


def records(sender):
    return [json.loads(x) for x in sender.journal.read_text().splitlines()]


def events(sender):
    return [r["event"] for r in records(sender)]


# ---- the IG session, demo only -----------------------------------------------------------------

def test_it_uses_the_price_services_login_and_never_logs_in_itself(S):
    sender, ig, *_ = make(S)                                # PretendIG.login raises if called
    assert sender.ready and not any(c[1] == "/session" for c in ig.calls)
    with pytest.raises(NotReady, match="never logs in itself"):
        make(S, PretendIG(active=False))


def test_demo_only(S):
    with pytest.raises(NotReady, match="demo address"):
        make(S, PretendIG(base_url="https://api.ig.com/gateway/deal"))


def test_no_order_before_the_start_up_is_done(S):
    sender, ig, *_ = make(S, start=False)
    r = sender.place(idea(EMA_PULLBACK), calendar=[])
    assert (r.ok, r.what) == (False, "safety refused") and ig.orders_sent() == []


# ---- the order -----------------------------------------------------------------------------------

@pytest.mark.parametrize("strategy,stop,limit", [(EMA_PULLBACK, 12, 30), (BOLLINGER_BOUNCE, 6, 100), (RANGE_TRADE, 6, 100),
                                                 (BREAKOUT, 6, 50), (SLOW_GRIND, 15, 20)])
def test_a_market_order_with_its_strategys_stop_and_take_profit_and_force_open(S, strategy, stop, limit):
    sender, ig, *_ = make(S)
    r = sender.place(idea(strategy), calendar=[])
    assert r.ok and r.what == "opened"
    (_, path, version, body, headers), = ig.orders_sent()
    assert (path, version, headers) == ("/positions/otc", "2", {"VERSION": "2", "Content-Type": "application/json"})
    assert body == {"currencyCode": "GBP", "direction": "SELL", "epic": EPIC, "expiry": "DFB", "forceOpen": True,
                    "guaranteedStop": False, "level": None, "limitDistance": float(limit), "limitLevel": None,
                    "orderType": "MARKET", "quoteId": None, "size": 10.0, "stopDistance": float(stop),
                    "stopLevel": None, "trailingStop": False, "trailingStopIncrement": None,
                    "dealReference": r.reference}
    assert list(body) == ["currencyCode", "direction", "epic", "expiry", "forceOpen", "guaranteedStop", "level",
                          "limitDistance", "limitLevel", "orderType", "quoteId", "size", "stopDistance", "stopLevel",
                          "trailingStop", "trailingStopIncrement", "dealReference"]           # AutoBot 161's 17


def test_the_level_reversals_stop_price_becomes_a_distance_when_sent(S):
    sender, ig, *_ = make(S, quote=(D("13400.0"), D("13401.5")))
    sender.place(idea(LEVEL_REVERSAL, BUY, context={"stop_price": D("13387.5")}), calendar=[])
    body = ig.orders_sent()[0][3]                              # a buy opens on the offer, 13401.5
    assert body["stopDistance"] == 14.0 and body["stopLevel"] is None and body["limitDistance"] == 20.0
    sender, ig, *_ = make(S, quote=(D("13400.0"), D("13401.5")))
    sender.place(idea(LEVEL_REVERSAL, SELL, context={"stop_price": D("13410.0")}), calendar=[])
    assert ig.orders_sent()[0][3]["stopDistance"] == 10.0      # a sell opens on the bid, 13400.0


def test_the_level_reversal_needs_a_current_price_on_the_right_side_of_its_stop(S):
    sender, ig, *_ = make(S, quote=None)
    r = sender.place(idea(LEVEL_REVERSAL), calendar=[])
    assert r.reasons == ["no current price to turn the level reversal's stop price into a distance"] and not ig.orders_sent()
    sender, ig, *_ = make(S, quote=(D("13412.0"), D("13413.5")))
    r = sender.place(idea(LEVEL_REVERSAL, SELL, context={"stop_price": D("13410.0")}), calendar=[])
    assert "already past the level reversal's stop price" in r.reasons[0] and not ig.orders_sent()


def test_the_stop_is_never_sent_as_a_level_and_force_open_is_always_true(S):
    sender, ig, *_ = make(S)
    for n in (EMA_PULLBACK, BOLLINGER_BOUNCE, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL, RANGE_TRADE):
        sender.place(idea(n), calendar=[])
    for _, _, _, body, _ in ig.orders_sent():
        assert body["stopLevel"] is None and body["stopDistance"] > 0 and body["forceOpen"] is True


def test_the_big_news_and_trend_day_take_profit(S):
    sender, ig, *_ = make(S, t=U(2026, 11, 5, 9, 0))
    sender.place(idea(EMA_PULLBACK, t=U(2026, 11, 5, 9, 0)), calendar=BOE_CAL)
    assert ig.orders_sent()[-1][3]["limitDistance"] == 100.0
    sender, ig, *_ = make(S)
    sender.place(idea(SLOW_GRIND, SELL), calendar=[], trend_day="down")
    assert ig.orders_sent()[-1][3]["limitDistance"] == 100.0


def test_every_order_has_a_stop_and_a_take_profit(S):
    sender, ig, *_ = make(S)
    for n in (EMA_PULLBACK, BOLLINGER_BOUNCE, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL, RANGE_TRADE):
        sender.place(idea(n), calendar=[])
    for _, _, _, body, _ in ig.orders_sent():
        assert body["stopDistance"] > 0 and body["limitDistance"] > 0 and body["forceOpen"]


# ---- the deal reference and IG's confirmation --------------------------------------------------------

def test_its_own_deal_reference_is_recorded_before_sending(S):
    sender, ig, *_ = make(S)
    r = sender.place(idea(BREAKOUT), calendar=[])
    sent_before = [json.loads(x) for x in ig.journal_at_post.splitlines()]
    assert sent_before[-1]["event"] == "sending" and sent_before[-1]["reference"] == r.reference
    assert r.reference.startswith("AB") and len(r.reference) <= 30


def test_references_are_unique(S):
    sender, ig, *_ = make(S)
    refs = {sender.place(idea(EMA_PULLBACK), calendar=[]).reference for _ in range(20)}
    assert len(refs) == 20


def test_a_trade_counts_only_once_ig_confirms_it_with_its_deal_id_and_fill(S):
    sender, ig, *_ = make(S)
    r = sender.place(idea(BREAKOUT), calendar=[])
    opened = [x for x in records(sender) if x["event"] == "opened"][-1]
    assert (opened["reference"], opened["deal_id"], opened["level"]) == (r.reference, "DIAAA1", "13400.5")
    assert [t.strategy for t in sender.open_trades()] == [BREAKOUT]


def test_ig_rejecting_for_lack_of_funds_alerts_and_counts_nothing(S):
    ig = PretendIG()
    ig.post_open = {"dealStatus": "REJECTED", "reason": "INSUFFICIENT_FUNDS"}
    sender, ig, alerts, *_ = make(S, ig)
    r = sender.place(idea(BREAKOUT), calendar=[])
    assert (r.ok, r.what) == (False, "refused") and sender.open_trades() == []
    assert alerts.sent[-1][0] == "ig-funds-refused" and "refused" in events(sender)


def test_ig_rejecting_for_its_stop_reads_igs_minimum_once_and_alerts(S):
    ig = PretendIG()
    ig.post_open = {"dealStatus": "REJECTED", "reason": "ATTACHED_ORDER_LEVEL_ERROR"}
    sender, ig, alerts, *_ = make(S, ig)
    sender.place(idea(BOLLINGER_BOUNCE), calendar=[])
    assert [c[1] for c in ig.calls].count(f"/markets/{EPIC}") == 1
    assert "IG's minimum stop distance is now 8.0 pips" in alerts.sent[-1][1]
    assert (S.safety.folder / "ig_min_stop_refusals.jsonl").exists()


def test_an_error_reply_to_the_order_is_a_refusal(S):
    ig = PretendIG()
    ig.post_open = "http-400"
    sender, ig, *_ = make(S, ig)
    r = sender.place(idea(BREAKOUT), calendar=[])
    assert r.what == "refused" and "validation.null-not-allowed.request" in r.reasons[0] and len(ig.orders_sent()) == 1


# ---- a timeout or an unclear answer: check, never send twice ----------------------------------------------

def test_a_timeout_is_checked_by_its_reference_and_never_sent_again(S):
    ig = PretendIG()
    ig.post_open = "timeout-but-done"
    sender, ig, *_ = make(S, ig)
    r = sender.place(idea(BREAKOUT), calendar=[])
    assert r.ok and r.what == "opened" and len(ig.orders_sent()) == 1
    assert "unclear" in events(sender) and "checked" in events(sender)


def test_a_timeout_found_only_among_the_open_positions(S):
    ig = PretendIG()
    ig.post_open = "timeout-position-only"
    sender, ig, *_ = make(S, ig)
    r = sender.place(idea(SLOW_GRIND), calendar=[])
    assert r.ok and len(ig.orders_sent()) == 1 and [t.strategy for t in sender.open_trades()] == [SLOW_GRIND]
    assert [x for x in records(sender) if x["event"] == "adopted"][0]["reference"] == r.reference


def test_a_timeout_that_ig_cannot_account_for_is_reported_and_not_sent_again(S):
    ig = PretendIG()
    ig.post_open = "timeout"
    sender, ig, alerts, sleeps, _ = make(S, ig)
    r = sender.place(idea(BREAKOUT), calendar=[])
    assert (r.ok, r.what) == (False, "not found") and len(ig.orders_sent()) == 1
    assert sleeps == [2, 2] and [c[1] for c in ig.calls].count(f"/confirms/{r.reference}") == 3
    assert alerts.sent[-1][0] == "order-unclear" and "NOT sent again" in alerts.sent[-1][1]


def test_no_confirmation_yet_then_accepted(S):
    ig = PretendIG()
    sender, ig, *_ = make(S, ig)
    real_fill = ig._fill

    def fill_later(ref, body, confirm=True):
        real_fill(ref, body)
        ig.confirms[ref] = [None, ig.confirms[ref]]             # the first check: not there yet
    ig._fill = fill_later
    r = sender.place(idea(BREAKOUT), calendar=[])
    assert r.ok and len(ig.orders_sent()) == 1


# ---- the safety rules before every order -----------------------------------------------------------------

def test_the_safety_rules_come_first_with_its_own_open_trades_and_funds(S):
    sender, ig, *_ = make(S)
    assert sender.place(idea(BOLLINGER_BOUNCE), calendar=[]).ok
    r = sender.place(idea(BOLLINGER_BOUNCE), calendar=[])                  # a second sell bounce
    assert r.what == "safety refused" and "already has 1 sell trade(s) open" in r.reasons[0]
    assert len(ig.orders_sent()) == 1
    r = sender.place(idea(BREAKOUT), paused=True, calendar=[])
    assert r.reasons == ["the pause switch is on: no new trades"] and len(ig.orders_sent()) == 1
    assert events(sender).count("safety refused") == 2


def test_funds_are_read_at_start_up_and_whenever_a_trade_opens_or_closes(S):
    sender, ig, *_ = make(S)
    assert ig.calls.count(("GET", "/accounts")) == 1
    r = sender.place(idea(RANGE_TRADE), calendar=[])
    assert ig.calls.count(("GET", "/accounts")) == 2
    sender.close(r.reference, half=True)
    sender.close(r.reference)
    assert ig.calls.count(("GET", "/accounts")) == 4


def test_low_or_unknown_funds_stop_new_trades(S):
    sender, ig, *_ = make(S, PretendIG(available=4000.0))
    assert "less than the margin for one trade" in sender.place(idea(EMA_PULLBACK), calendar=[]).reasons[0]
    sender, ig, alerts, *_ = make(S, PretendIG(available=RuntimeError("no reply")))
    assert sender.funds is None and alerts.sent[-1][0] == "funds-not-read"
    assert "not known" in sender.place(idea(EMA_PULLBACK), calendar=[]).reasons[0] and ig.orders_sent() == []


# ---- restart recovery ----------------------------------------------------------------------------------

def theirs(deal="DIZZZ9", epic="IX.D.FTSE.DAILY.IP"):
    return {"position": {"dealId": deal, "dealReference": "BYHAND1", "direction": "BUY", "size": 1.0, "level": 7400.0},
            "market": {"epic": epic}}


def test_after_a_restart_it_finds_its_own_trades_and_leaves_others_alone(S):
    sender, ig, *_ = make(S)
    a = sender.place(idea(BREAKOUT), calendar=[])
    b = sender.place(idea(SLOW_GRIND), calendar=[])
    ig.positions = [p for p in ig.positions if p["position"]["dealReference"] != b.reference]   # b stopped at IG
    ig.positions.append(theirs())
    ig.calls.clear()
    again, ig2, alerts, *_ = make(S, ig)                       # a new start, the same record
    assert [t.deal_id for t in again.open_trades()] == [a.deal_id]
    ev = events(again)
    assert "found at IG" in ev and "gone at IG" in ev and "not ours" in ev
    assert alerts.sent[-1][0] == "position-not-ours" and "left alone" in alerts.sent[-1][1]
    assert not any(c[0] == "POST" for c in ig.calls)            # nothing sent, nothing closed


def test_an_order_sent_before_a_restart_is_adopted_or_settled_by_its_reference(S, tmp_path):
    sender, ig, *_ = make(S)
    ig.post_open = "timeout"
    lost = sender.place(idea(BREAKOUT), calendar=[]).reference          # IG never accounted for it
    ig.positions.append({"position": {"dealId": "DILATE1", "dealReference": lost, "direction": "SELL", "size": 10.0,
                                      "level": 13399.0}, "market": {"epic": EPIC}})      # it shows up later
    again, *_ = make(S, ig)
    assert [t.deal_id for t in again.open_trades()] == ["DILATE1"] and "adopted" in events(again)


def test_an_unresolved_order_ig_rejected_is_settled_at_start_up(S):
    sender, ig, *_ = make(S)
    ig.post_open = "timeout"
    ref = sender.place(idea(BREAKOUT), calendar=[]).reference
    ig.confirms[ref] = {"dealStatus": "REJECTED", "reason": "MARKET_CLOSED_WITH_EDITS"}
    again, ig, alerts, *_ = make(S, ig)
    assert again.open_trades() == [] and records(again)[-3]["event"] == "refused"


def test_an_unresolved_order_still_unknown_is_reported_at_start_up_and_never_sent(S):
    sender, ig, *_ = make(S)
    ig.post_open = "timeout"
    sender.place(idea(BREAKOUT), calendar=[])
    n = len(ig.orders_sent())
    again, ig, alerts, *_ = make(S, ig)
    assert "still unresolved" in events(again) and alerts.sent[-1][0] == "order-unresolved" and len(ig.orders_sent()) == n


def test_the_open_trades_are_rebuilt_from_the_record(S):
    sender, ig, *_ = make(S)
    r = sender.place(idea(RANGE_TRADE), calendar=[])
    sender.close(r.reference, half=True)
    again, *_ = make(S, ig)
    (t,) = [t for t in again.trades.values() if t.status == "open"]
    assert t.half_closed and t.size == D("5.0") and again.open_trades()[0].size_gbp_per_pip == D(5)


# ---- closing -----------------------------------------------------------------------------------------

def test_a_full_close_confirmed_with_ig(S):
    sender, ig, *_ = make(S)
    r = sender.place(idea(BREAKOUT, BUY), calendar=[])
    c = sender.close(r.reference, why="20:30 close")
    assert (c.ok, c.what) == (True, "closed") and sender.open_trades() == []
    (m, path, version, body, headers), = closes(ig)
    assert (path, version, headers) == ("/positions/otc", "1",
                                        {"VERSION": "1", "Content-Type": "application/json", "_method": "DELETE"})
    assert body == {"dealId": r.deal_id, "direction": "SELL", "size": 10.0, "orderType": "MARKET", "expiry": "DFB"}
    closed = [x for x in records(sender) if x["event"] == "closed"][0]
    assert (closed["level"], closed["profit"], closed["how"]) == ("13390.0", 100.0, "confirmed")


def test_the_range_trade_closes_by_half_once(S):
    sender, ig, *_ = make(S)
    r = sender.place(idea(RANGE_TRADE), calendar=[])
    h = sender.close(r.reference, half=True, why="the opposite band")
    assert (h.ok, h.what) == (True, "half closed") and closes(ig)[-1][3]["size"] == 5.0
    assert not sender.close(r.reference, half=True).ok                  # only once
    assert sender.close(r.reference).ok and closes(ig)[-1][3]["size"] == 5.0


def test_only_the_range_trade_closes_by_half(S):
    sender, ig, *_ = make(S)
    r = sender.place(idea(BREAKOUT), calendar=[])
    c = sender.close(r.reference, half=True)
    assert not c.ok and "only a range trade" in c.reasons[0] and not closes(ig)


def test_it_never_closes_a_position_it_did_not_open(S):
    ig = PretendIG(positions=[theirs()])
    sender, ig, *_ = make(S, ig)
    c = sender.close("BYHAND1")
    assert c.what == "not open" and not closes(ig)


def test_a_refused_close_is_recorded_and_alerted(S):
    sender, ig, alerts, *_ = make(S)
    r = sender.place(idea(BREAKOUT), calendar=[])
    ig.close_answer = "reject"
    c = sender.close(r.reference)
    assert c.what == "close refused" and alerts.sent[-1][0] == "close-refused" and len(sender.open_trades()) == 1


def test_an_unclear_close_is_checked_on_the_position(S):
    sender, ig, *_ = make(S)
    r = sender.place(idea(BREAKOUT), calendar=[])
    ig.close_answer = "timeout-done"
    c = sender.close(r.reference)
    assert (c.ok, c.what) == (True, "closed")
    closed = [x for x in records(sender) if x["event"] == "closed"][0]
    assert closed["how"] == "the position is gone at IG"


def test_an_unclear_close_with_the_position_unchanged_is_not_sent_again(S):
    sender, ig, alerts, *_ = make(S)
    r = sender.place(idea(BREAKOUT), calendar=[])
    ig.close_answer = "timeout"
    c = sender.close(r.reference)
    assert c.what == "close not done" and len(closes(ig)) == 1 and alerts.sent[-1][0] == "close-unclear"


# ---- everything is recorded ----------------------------------------------------------------------------

def test_every_order_confirmation_refusal_and_close_is_recorded(S):
    sender, ig, *_ = make(S)
    r = sender.place(idea(RANGE_TRADE), calendar=[])
    sender.place(idea(RANGE_TRADE), calendar=[])                               # safety refused
    sender.close(r.reference, half=True)
    sender.close(r.reference)
    ig.post_open = {"dealStatus": "REJECTED", "reason": "MARKET_CLOSED"}
    sender.place(idea(BREAKOUT), calendar=[])
    ev = events(sender)
    for e in ("ready", "funds", "sending", "opened", "safety refused", "close sending", "half closed", "closed", "refused"):
        assert e in ev, e
    assert all(x["pair"] == "GBPUSD" and x["time_utc"] for x in records(sender))


# ---- with the real IG client: the close's header, and no login --------------------------------------------

def test_with_the_real_ig_client_the_close_sends_the_delete_header_and_no_login(S):
    from ig.client import IGClient
    from tests.technical.fake_ig import CREDS, FakeIG, Reply as R
    fake = FakeIG(
        R(200, {"positions": []}),                                                  # start-up: positions
        R(200, {"accounts": [{"accountId": CREDS.account_id, "balance": {"available": 20000.0}}]}),   # funds
        R(200, {"dealReference": "X"}),                                             # the order
    )
    client = IGClient(S.ig, CREDS, http=fake, sleep=lambda s: None)
    client._cst, client._security_token, client.account_active = "CST", "XST", True   # the price service's session
    sender = OrderSender(S, client, FakeAlerts(), now=lambda: WED, sleep=lambda s: None)
    sender.start()
    fake.replies += [R(200, {"dealStatus": "ACCEPTED", "dealId": "DI1", "level": 13400.5}),          # the confirmation
                     R(200, {"accounts": [{"accountId": CREDS.account_id, "balance": {"available": 19000.0}}]})]
    r = sender.place(idea(BREAKOUT), calendar=[])
    assert r.ok
    fake.replies += [R(200, {"dealReference": "C1"}), R(200, {"dealStatus": "ACCEPTED", "level": 13390.0}),
                     R(200, {"accounts": [{"accountId": CREDS.account_id, "balance": {"available": 20100.0}}]})]
    assert sender.close(r.reference).ok
    order, close = [s for s in fake.sent if s.method == "POST" and s.path == "/positions/otc"]
    assert order.headers["VERSION"] == "2" and "Version" not in order.headers
    assert order.headers["Content-Type"] == "application/json" and order.headers["Accept"] == "application/json; charset=UTF-8"
    assert {"X-IG-API-KEY", "CST", "X-SECURITY-TOKEN"} <= set(order.headers)
    assert order.url == "https://demo-api.ig.com/gateway/deal/positions/otc"
    confirm = [s for s in fake.sent if s.path.startswith("/confirms/")][0]
    assert confirm.method == "GET" and confirm.headers["VERSION"] == "1" and confirm.json is None
    assert close.headers["_method"] == "DELETE" and close.headers["VERSION"] == "1"
    assert not any(s.path == "/session" for s in fake.sent) and fake.all_used()


def test_the_confirmation_is_asked_for_as_161_does(S):
    """GET /confirms/{reference}, VERSION 1, up to 5 times, 1 second apart, while IG answers 404."""
    sender, ig, alerts, sleeps, _ = make(S)
    real_fill = ig._fill

    def late(ref, body, confirm=True):
        real_fill(ref, body)
        ig.confirms[ref] = [None, None, None, None, ig.confirms[ref]]          # 404 four times, then there
    ig._fill = late
    r = sender.place(idea(BREAKOUT), calendar=[])
    confirms = [c for c in ig.calls if c[1].startswith("/confirms/")]
    assert r.ok and len(confirms) == 5 and sleeps == [1, 1, 1, 1]
    assert all(c[2] == "1" and c[4] == {"VERSION": "1", "Content-Type": "application/json"} for c in confirms)


def test_the_reference_ig_echoes_is_the_one_confirmed(S):
    sender, ig, *_ = make(S)
    real = ig.request

    def echo_other(method, path, version, body=None, *, what, headers=None):
        r = real(method, path, version, body, what=what, headers=headers)
        if method == "POST" and "_method" not in headers:
            ig.confirms["IGECHO1"] = ig.confirms[body["dealReference"]]
            return Reply({"dealReference": "IGECHO1"})
        return r
    ig.request = echo_other
    r = sender.place(idea(BREAKOUT), calendar=[])
    assert r.ok and any(c[1] == "/confirms/IGECHO1" for c in ig.calls)
    assert [x for x in records(sender) if x["event"] == "reference echoed"][0]["ig_reference"] == "IGECHO1"
