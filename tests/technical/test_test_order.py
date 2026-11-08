"""Technical tests for the owner's one test order (orders/test_order.py), with the pretend IG of
test_orders.py. Nothing here contacts IG."""

import json
from datetime import timedelta
from decimal import Decimal as D

import pytest

from orders.test_order import DONE, REQUEST, RESULT, RUNNING, TestOrder
from tests.technical.test_orders import WED, FakeAlerts, Over, PretendIG, S  # noqa: F401  (S: the fixture)


class Alerts(FakeAlerts):
    def __init__(self):
        super().__init__()
        self.infos = []

    def info(self, text, key=None):
        self.infos.append(text)


def make(S, request=None, quote=(D("13400.0"), D("13401.5")), t=WED, ig=None):
    ig = ig or PretendIG()
    folder = S.orders.folder
    folder.mkdir(parents=True, exist_ok=True)
    if request is not None:
        (folder / REQUEST).write_text(json.dumps(request) if isinstance(request, dict) else request)
    clock, sleeps = {"t": t}, []
    alerts = Alerts()
    test = TestOrder(S, ig, alerts, lambda: quote, now=lambda: clock["t"], sleep=sleeps.append, threaded=False)
    ig.journal = folder / "GBPUSD" / "orders.jsonl"
    return test, ig, alerts, sleeps, clock, folder


REQ = {"approved_by": "owner", "not_before_utc": "2026-11-04T10:30:00Z", "direction": "buy", "strategy": "breakout",
       "hold_seconds": 60}


def test_nothing_happens_without_the_owners_request(S):
    test, ig, *_ = make(S)
    test.tick()
    assert ig.calls == []


def test_nothing_happens_before_its_time(S):
    test, ig, alerts, sleeps, clock, folder = make(S, REQ, t=WED)          # 10:00, the request says 10:30
    test.tick()
    assert ig.calls == [] and (folder / REQUEST).exists()


def test_one_order_opened_held_and_closed_then_never_again(S):
    test, ig, alerts, sleeps, clock, folder = make(S, REQ, t=WED + timedelta(minutes=30))
    test.tick()
    assert [c[3]["direction"] for c in ig.orders_sent()] == ["BUY"]
    body = ig.orders_sent()[0][3]
    assert (body["size"], body["stopDistance"], body["limitDistance"], body["forceOpen"]) == (10.0, 6.0, 50.0, True)
    assert sleeps[-1] == 60 and len([c for c in ig.calls if len(c) == 5 and (c[4] or {}).get("_method")]) == 1
    result = json.loads((folder / RESULT).read_text())
    assert (result["placed"], result["closed"], result["open_trades_after"]) == ("opened", "closed", 0)
    assert result["deal_id"] and result["fill"] == "13400.5" and result["available_funds_at_start"] == "20000.0"
    assert not (folder / REQUEST).exists() and not (folder / RUNNING).exists() and (folder / DONE).exists()
    assert "placed: opened" in alerts.infos[-1]
    n = len(ig.calls)
    test.tick()
    assert len(ig.calls) == n                                                # never twice


def test_the_request_is_renamed_before_anything_is_sent(S):
    test, ig, alerts, sleeps, clock, folder = make(S, REQ, t=WED + timedelta(minutes=30))
    seen = {}
    real = ig.request

    def spy(method, path, version, body=None, *, what, headers=None):
        if method == "POST":
            seen["request still there"] = (folder / REQUEST).exists()
            seen["running"] = (folder / RUNNING).exists()
        return real(method, path, version, body, what=what, headers=headers)
    ig.request = spy
    test.tick()
    assert seen == {"request still there": False, "running": True}


@pytest.mark.parametrize("bad", [dict(REQ, approved_by="someone"), dict(REQ, direction="up"), dict(REQ, hold_seconds=5),
                                 dict(REQ, strategy="martingale")])
def test_a_bad_request_sends_nothing(S, bad):
    test, ig, alerts, sleeps, clock, folder = make(S, bad, t=WED + timedelta(minutes=30))
    test.tick()
    assert ig.orders_sent() == [] and "refused" in json.loads((folder / RESULT).read_text())


def test_an_unreadable_request_sends_nothing_and_alerts(S):
    test, ig, alerts, sleeps, clock, folder = make(S, "{not json", t=WED + timedelta(minutes=30))
    test.tick()
    assert ig.calls == [] and alerts.sent[-1][0] == "test-order" and (folder / DONE).exists()


def test_no_current_price_sends_nothing(S):
    test, ig, alerts, sleeps, clock, folder = make(S, REQ, quote=None, t=WED + timedelta(minutes=30))
    test.tick()
    assert ig.orders_sent() == [] and json.loads((folder / RESULT).read_text())["refused"] == "no current price from the stream"


def test_the_safety_rules_still_apply(S):
    sunday = dict(REQ, not_before_utc="2026-11-08T07:00:00Z")                 # the market is closed
    from datetime import datetime, timezone
    test, ig, alerts, sleeps, clock, folder = make(S, sunday, t=datetime(2026, 11, 8, 8, 0, tzinfo=timezone.utc))
    test.tick()
    result = json.loads((folder / RESULT).read_text())
    assert result["placed"] == "safety refused" and "the market is closed" in result["reasons"] and ig.orders_sent() == []
