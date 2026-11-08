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


# ---- the spread condition (owner, 8 November 2026) ---------------------------------------------------

from datetime import datetime, timezone  # noqa: E402

UTC = timezone.utc
TONIGHT = {"approved_by": "owner", "not_before_utc": "2026-11-08T22:30:00Z", "direction": "buy",
           "strategy": "EMA pullback", "hold_seconds": 60, "max_spread_pips": 2, "spread_minutes": 15,
           "check_every_minutes": 5, "give_up_utc": "2026-11-09T00:00:00Z"}


def run_night(S, spread_at, start=(22, 0), end=(0, 5), step=10):
    """Tick every `step` seconds from start to end UK (GMT); spread_at(t) gives the spread in pips (None: no price)."""
    box = {"q": None}
    test, ig, alerts, sleeps, clock, folder = make(S, TONIGHT, t=datetime(2026, 11, 8, *start, tzinfo=UTC))
    test.quote = lambda: box["q"]
    t = datetime(2026, 11, 8, *start, tzinfo=UTC)
    stop = datetime(2026, 11, 9 if end[0] < start[0] else 8, *end, tzinfo=UTC)
    while t <= stop:
        clock["t"] = t
        s_ = spread_at(t)
        box["q"] = None if s_ is None else (D("13400.0"), D("13400.0") + D(str(s_)))
        test.tick()
        if ig.orders_sent():
            break
        t += timedelta(seconds=step)
    return test, ig, alerts, folder


def test_sent_at_22_30_when_the_spread_was_under_2_pips_for_15_minutes(S):
    test, ig, alerts, folder = run_night(S, lambda t: 1.4)
    (o,) = ig.orders_sent()
    assert o[3]["direction"] == "BUY" and o[3]["stopDistance"] == 12.0 and o[3]["limitDistance"] == 30.0
    result = json.loads((folder / RESULT).read_text())
    assert result["started_utc"] == "2026-11-08T22:30:00Z" and result["spread_checks"][0].startswith("22:30:00 UTC: send")


def test_a_wide_spread_waits_and_checks_again_every_5_minutes(S):
    wide = datetime(2026, 11, 8, 22, 20, tzinfo=UTC)
    test, ig, alerts, folder = run_night(S, lambda t: 2.5 if t == wide else 1.5)
    assert len(ig.orders_sent()) == 1
    result = json.loads((folder / RESULT).read_text())
    assert [c[:14] for c in result["spread_checks"]] == ["22:30:00 UTC: ", "22:35:00 UTC: ", "22:40:00 UTC: "]
    assert "wait (the spread reached 2.5 pips" in result["spread_checks"][0] and "send" in result["spread_checks"][2]
    assert result["started_utc"] == "2026-11-08T22:40:00Z"


def test_exactly_2_pips_is_not_under_2(S):
    test, ig, alerts, folder = run_night(S, lambda t: 2.0, end=(22, 31))
    assert ig.orders_sent() == []


def test_never_under_2_pips_by_midnight_sends_nothing_and_tells_the_owner(S):
    test, ig, alerts, folder = run_night(S, lambda t: 3.0)
    assert ig.orders_sent() == [] and ig.calls == []
    result = json.loads((folder / RESULT).read_text())
    assert result["sent"].startswith("nothing: the spread was never under 2 pips for 15 minutes")
    assert len(result["checks"]) == 19 and result["checks"][-1].startswith("00:00:00 UTC: wait")   # 22:30 ... 00:00
    assert alerts.sent[-1][0] == "test-order" and "NOT sent" in alerts.sent[-1][1]
    assert (folder / DONE).exists() and not (folder / REQUEST).exists()


def test_no_current_price_counts_against_it(S):
    gap = (datetime(2026, 11, 8, 22, 25, tzinfo=UTC), datetime(2026, 11, 8, 22, 25, 30, tzinfo=UTC))
    test, ig, alerts, folder = run_night(S, lambda t: None if gap[0] <= t <= gap[1] else 1.5)
    result = json.loads((folder / RESULT).read_text())
    assert "second(s) with no current price" in result["spread_checks"][0] and result["started_utc"] == "2026-11-08T22:45:00Z"


def test_a_gap_in_the_samples_counts_against_it(S):
    test, ig, alerts, folder = run_night(S, lambda t: 1.5, step=90, end=(22, 31))
    assert ig.orders_sent() == [] and "gap of 90 seconds" in test.checks[0]


def test_not_enough_samples_yet_waits(S):
    test, ig, alerts, folder = run_night(S, lambda t: 1.5, start=(22, 25), end=(22, 31))
    assert ig.orders_sent() == [] and "not enough spread samples" in test.checks[0]


# ---- the owner's extras (8 November 2026) and the queue ---------------------------------------------

from orders.test_order import QUEUE, RECOVERING, RESTART  # noqa: E402

AT = WED + timedelta(minutes=30)


def result_of(folder, extra):
    return json.loads((folder / f"test_result_{extra}.json").read_text())


def test_half_close_closes_half_then_the_rest_and_follows_the_new_deal_id(S):
    req = dict(REQ, strategy="range trade", extra="half_close")
    test, ig, alerts, sleeps, clock, folder = make(S, req, t=AT)
    test.tick()
    cl = [c for c in ig.calls if len(c) == 5 and (c[4] or {}).get("_method")]
    assert [c[3]["size"] for c in cl] == [5.0, 5.0] and sleeps[-2:] == [60, 60]
    assert cl[1][3]["dealId"].startswith("DIREST")                           # the rest, by its new deal ID
    r = result_of(folder, "half_close")
    assert (r["placed"], r["half_closed"], r["closed"], r["open_trades_after"]) == ("opened", "half closed", "closed", 0)
    assert r["remaining_size"] == "5.0" and r["deal_id_of_the_rest"].startswith("DIREST")
    assert ig.positions == [] and (folder / "test_request.half_close.done.json").exists()
    assert not (folder / RESULT).exists()                                    # the first test's result is left alone


def test_half_close_is_for_the_range_trade_only(S):
    test, ig, alerts, sleeps, clock, folder = make(S, dict(REQ, extra="half_close"), t=AT)
    test.tick()
    assert ig.orders_sent() == [] and "range trade only" in result_of(folder, "half_close")["refused"]


def test_stop_refusal_sends_half_of_igs_minimum_and_reports_igs_reason(S):
    ig = PretendIG()
    ig.post_open = {"dealStatus": "REJECTED", "reason": "ATTACHED_ORDER_LEVEL_ERROR"}
    test, ig, alerts, sleeps, clock, folder = make(S, dict(REQ, extra="stop_refusal"), t=AT, ig=ig)
    test.tick()
    (o,) = ig.orders_sent()
    assert o[3]["stopDistance"] == 4.0                                       # the pretend IG's minimum is 8 points
    r = result_of(folder, "stop_refusal")
    assert r["placed"] == "refused" and r["ig_refused_it"] is True and "ATTACHED_ORDER_LEVEL_ERROR" in r["reasons"][0]
    assert r["ig_min_stop_points"] == "8.0" and r["stop_sent_points"] == "4.0"
    assert any(k.startswith("ig-stop-refused") for k, _ in alerts.sent)      # the refusal alert
    assert [c[1] for c in ig.calls if c[0] == "GET" and str(c[1]).startswith("/markets/")].__len__() == 2   # before, after


def test_stop_refusal_accepted_anyway_is_closed(S):
    test, ig, alerts, sleeps, clock, folder = make(S, dict(REQ, extra="stop_refusal"), t=AT)
    test.tick()
    r = result_of(folder, "stop_refusal")
    assert (r["placed"], r["ig_refused_it"], r["closed"]) == ("opened", False, "closed") and ig.positions == []


def test_restart_recovery_restarts_then_finds_the_trade_by_its_reference_and_closes_it(S):
    test, ig, alerts, sleeps, clock, folder = make(S, dict(REQ, extra="restart_recovery"), t=AT)
    asked = []
    test.request_restart = asked.append
    test.tick()
    assert asked and (folder / RESTART).exists() and len(ig.positions) == 1 and closes_sent(ig) == []
    assert not (folder / "test_result_restart_recovery.json").exists()
    test.tick()                                   # the dying service never ticks again; nothing more here anyway
    # the restarted service: a new TestOrder on the same files and the same IG
    after = TestOrder(S, ig, alerts, lambda: (D("13400.0"), D("13401.5")), now=lambda: clock["t"], sleep=sleeps.append,
                      threaded=False)
    after.tick()
    r = result_of(folder, "restart_recovery")
    assert r["found_by_reference"] is True and r["found_before_ready"] is True and r["open_trades_at_start"] == 1
    assert r["closed"] == "closed" and r["open_trades_after"] == 0 and ig.positions == []
    assert r["before_the_restart"]["reference"] == ig.orders_sent()[0][3]["dealReference"]
    assert (folder / "test_request.restart_recovery.done.json").exists() and not (folder / RECOVERING).exists()
    n = len(ig.calls)
    after.tick()
    assert len(ig.calls) == n                                                # never twice


def test_restart_recovery_when_the_trade_went_while_the_service_was_down(S):
    test, ig, alerts, sleeps, clock, folder = make(S, dict(REQ, extra="restart_recovery"), t=AT)
    test.request_restart = lambda why: None
    test.tick()
    ig.positions.clear()                                                     # stopped out at IG meanwhile
    after = TestOrder(S, ig, alerts, lambda: (D("13400.0"), D("13401.5")), now=lambda: clock["t"], sleep=sleeps.append,
                      threaded=False)
    after.tick()
    r = result_of(folder, "restart_recovery")
    assert r["found_by_reference"] is False and r["closed"].startswith("nothing to close") and closes_sent(ig) == []


def test_restart_recovery_without_a_service_recovers_in_place(S):
    test, ig, alerts, sleeps, clock, folder = make(S, dict(REQ, extra="restart_recovery"), t=AT)
    test.tick()
    r = result_of(folder, "restart_recovery")
    assert r["found_by_reference"] is True and r["closed"] == "closed"


def closes_sent(ig):
    return [c for c in ig.calls if len(c) == 5 and (c[4] or {}).get("_method")]


def test_the_queue_runs_one_at_a_time_with_a_gap(S):
    test, ig, alerts, sleeps, clock, folder = make(S, None, t=AT)
    (folder / QUEUE).write_text(json.dumps([dict(REQ, extra="stop_refusal"), dict(REQ, strategy="range trade",
                                                                                   extra="half_close")]))
    test.tick()
    assert len(ig.orders_sent()) == 1 and result_of(folder, "stop_refusal")["placed"] == "opened"
    test.tick()                                                              # taken off the queue, but 5 minutes later
    assert len(ig.orders_sent()) == 1
    assert json.loads((folder / REQUEST).read_text())["not_before_utc"] == "2026-11-04T10:35:00Z"
    assert not (folder / QUEUE).exists()
    clock["t"] = AT + timedelta(minutes=5)
    test.tick()
    assert len(ig.orders_sent()) == 2 and result_of(folder, "half_close")["closed"] == "closed"


def test_the_queue_waits_for_the_spread_rule_again(S):
    test, ig, alerts, sleeps, clock, folder = make(S, None, t=AT)
    (folder / QUEUE).write_text(json.dumps([dict(TONIGHT, not_before_utc="2026-11-04T10:30:00Z", extra="stop_refusal")]))
    test.tick()
    assert ig.calls == [] and "not enough spread samples" in test.checks[0]


def test_an_unreadable_queue_sends_nothing_and_alerts(S):
    test, ig, alerts, sleeps, clock, folder = make(S, None, t=AT)
    (folder / QUEUE).write_text("{not a list")
    test.tick()
    assert ig.calls == [] and alerts.sent[-1][0] == "test-order" and (folder / (QUEUE + ".bad")).exists()


# ---- the check of IG's records (read-only) ----------------------------------------------------------

from orders.ig_records import DONE as CHECK_DONE, REQUEST as CHECK_REQUEST, RESULT as CHECK_RESULT, IGRecordsCheck  # noqa: E402
from tests.technical.test_orders import Reply  # noqa: E402


class HistoryIG(PretendIG):
    def request(self, method, path, version, body=None, *, what, headers=None):
        if method == "GET" and path.startswith("/history/activity"):
            self.calls.append((method, path, version, body, headers))
            return Reply({"activities": [
                {"epic": "CS.D.GBPUSD.TODAY.IP", "dealId": "DIAAAAYS9LEACBT", "type": "POSITION",
                 "details": {"dealReference": "AB1", "stopLevel": 13345.1, "limitLevel": 13387.1, "actions": []}},
                {"epic": "IX.D.FTSE.DAILY.IP", "dealId": "DIOTHER", "details": {"actions": []}}]})
        if method == "GET" and path.startswith("/history/transactions"):
            self.calls.append((method, path, version, body, headers))
            return Reply({"transactions": [{"instrumentName": "GBP/USD", "profitAndLoss": "£-11.00"}]})
        return super().request(method, path, version, body, what=what, headers=headers)


def test_the_ig_records_check_reads_only_and_writes_its_result(S):
    ig = HistoryIG()
    folder = S.orders.folder
    folder.mkdir(parents=True, exist_ok=True)
    (folder / CHECK_REQUEST).write_text(json.dumps({"from_utc": "2026-11-08T23:00:00Z", "to_utc": "2026-11-08T23:45:00Z",
                                                    "deal_ids": ["DIAAAAYS9LEACBT"]}))
    alerts = Alerts()
    check = IGRecordsCheck(S, ig, alerts, now=lambda: AT, threaded=False)
    check.tick()
    assert all(c[0] == "GET" for c in ig.calls)
    assert any("from=2026-11-08T23:00:00&to=2026-11-08T23:45:00&detailed=true" in c[1] for c in ig.calls)
    r = json.loads((folder / CHECK_RESULT).read_text())
    assert [a["dealId"] for a in r["activity"]] == ["DIAAAAYS9LEACBT"] and r["transactions"][0]["profitAndLoss"] == "£-11.00"
    assert r["open_positions"] == [] and r["funds"]["available"] == 20000.0
    assert (folder / CHECK_DONE).exists() and not (folder / CHECK_REQUEST).exists() and "0 open positions" in alerts.infos[-1]
    n = len(ig.calls)
    check.tick()
    assert len(ig.calls) == n                                                # never twice
