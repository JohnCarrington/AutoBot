"""Filling gaps from history and the one-off fill, with pretend IG replies."""

import json
from datetime import timedelta
from types import SimpleNamespace

import pytest

from ig.client import IGClient
from ig.history import HistoryDoor
from prices.calendar import Boundaries, MarketHours
from prices.history_fill import (DONE_FILE, Planned, apply_fill, candles_from_ig, fill_period,
                                 plan_one_off, report_after, requests_for_recorded_gaps, run_one_off)
from prices.store import CandleStore
from tests.technical.fake_ig import CREDS, FakeIG, Reply, accounts_ok, login_ok, switch_ok
from tests.technical.fake_stream import SETTINGS, T, five
from tests.technical.test_history_door import hist_ok

HIST = "/pri" + "ces"   # in pieces so the no-history scan stays strict
HOURS = MarketHours(SETTINGS.market_hours)
B = Boundaries(SETTINGS.candles, HOURS)
FIVE = timedelta(minutes=5)


@pytest.fixture
def store(tmp_path):
    return CandleStore(tmp_path / "candles", 30)


def row(t, bid=13352.9, ask=13354.4):
    p = {"bid": bid, "ask": ask, "lastTraded": None}
    return {"snapshotTimeUTC": t.strftime("%Y-%m-%dT%H:%M:%S"), "openPrice": p, "highPrice": p,
            "lowPrice": p, "closePrice": p}


# ---- reading IG's rows --------------------------------------------------------------

def test_ig_rows_use_igs_utc_time_ask_as_buy_and_bid_as_sell():
    (c,), problems = candles_from_ig([dict(row(T(2026, 7, 6, 9, 0)), snapshotTime="2026/07/06 10:00:00")],
                                     "5m", FIVE)
    assert c.start == T(2026, 7, 6, 9, 0)                    # snapshotTimeUTC, not the UK-time field
    assert str(c.buy_open) == "13354.4" and str(c.sell_open) == "13352.9"
    assert problems == []


def test_a_row_with_a_missing_price_is_not_used():
    r = row(T(2026, 11, 4, 10))
    r["closePrice"] = {"bid": None, "ask": 13354.4}
    candles, problems = candles_from_ig([r], "5m", FIVE)
    assert candles == [] and "not used" in problems[0]


# ---- filling only recorded gaps --------------------------------------------------------

def test_only_recorded_gaps_are_filled(store):
    store.add(five(T(2026, 11, 4, 10)))
    store.add(five(T(2026, 11, 4, 11)))   # 10:05-10:55 missing but NOT recorded
    assert requests_for_recorded_gaps(store, HOURS, 500) == []
    store.record_gap("5m", T(2026, 11, 4, 10, 5), T(2026, 11, 4, 11), 11, T(2026, 11, 4, 11, 1), "test")
    (req,) = requests_for_recorded_gaps(store, HOURS, 500)
    assert (req.start, req.end, req.points) == (T(2026, 11, 4, 10, 5), T(2026, 11, 4, 10, 55), 11)


def test_the_weekend_is_never_asked_for(store):
    store.record_gap("5m", T(2026, 11, 6, 21), T(2026, 11, 8, 21, 30), 999, T(2026, 11, 9), "test")
    reqs = requests_for_recorded_gaps(store, HOURS, 500)
    assert [(r.start, r.end, r.points) for r in reqs] == [
        (T(2026, 11, 6, 21), T(2026, 11, 6, 21, 55), 12),          # Friday up to the close
        (T(2026, 11, 8, 21), T(2026, 11, 8, 21, 25), 6)]           # Sunday from the open
    assert not any(not HOURS.is_open(t) for r in reqs for t in r.slots)


def test_only_missing_candles_are_asked_for_and_requests_are_no_bigger_than_the_maximum(store):
    store.record_gap("5m", T(2026, 11, 3, 0), T(2026, 11, 4, 12), 432, T(2026, 11, 4, 12), "test")
    store.add(five(T(2026, 11, 3, 12)))   # one candle inside the gap is already stored
    reqs = requests_for_recorded_gaps(store, HOURS, 100)
    asked = [t for r in reqs for t in r.slots]
    assert T(2026, 11, 3, 12) not in asked
    assert len(asked) == 432 - 1
    assert max(r.points for r in reqs) == 100
    assert all(r.points == len(r.slots) for r in reqs)


def test_what_comes_back_only_fills_missing_candles_and_never_overwrites(store):
    stored = five(T(2026, 11, 4, 10, 5), bc="1.11111")
    store.add(stored)
    req = Planned("MINUTE_5", T(2026, 11, 4, 10), T(2026, 11, 4, 10, 10), 2,
                  "fill", [T(2026, 11, 4, 10), T(2026, 11, 4, 10, 10)])
    came_back = [five(T(2026, 11, 4, 9, 55)), five(T(2026, 11, 4, 10)), five(T(2026, 11, 4, 10, 5)),
                 five(T(2026, 11, 4, 10, 10))]
    r = apply_fill(store, req, came_back)
    assert r == {"stored": 2, "already_stored": 0, "not_asked_for": 2,
                 "not_asked_times": [T(2026, 11, 4, 9, 55), T(2026, 11, 4, 10, 5)]}
    assert str(store.get("5m", T(2026, 11, 4, 10, 5)).buy_close) == "1.11111"
    assert store.get("5m", T(2026, 11, 4, 9, 55)) is None


# ---- the one-off plan --------------------------------------------------------------------

def test_the_fill_period_is_the_last_two_trading_weeks():
    assert fill_period(HOURS, T(2026, 11, 6, 19, 52)) == (T(2026, 10, 25, 21), T(2026, 11, 6, 19, 50))
    assert fill_period(HOURS, T(2026, 11, 7, 12)) == (T(2026, 10, 25, 21), T(2026, 11, 6, 22))


def test_the_plan_daily_first_then_compare_then_fills_none_too_big_no_weekend(store):
    for i in range(4):
        store.add(five(T(2026, 11, 6, 19, 20) + i * FIVE))
    plan = plan_one_off(store, HOURS, 500, T(2026, 11, 7, 12))
    assert [p.purpose for p in plan[:2]] == ["ig-daily", "compare"]
    assert plan[0].resolution == "DAY" and plan[0].points == 13
    assert plan[1].slots == [T(2026, 11, 6, 19, 20) + i * FIVE for i in range(4)]
    fills = [p for p in plan if p.purpose == "fill"]
    assert all(p.points <= 500 for p in plan)
    slots = [t for p in fills for t in p.slots]
    # 25-30 Oct: 1440 (closes 21:00 GMT = 17:00 New York); 1-6 Nov: 1452; less the 4 stored
    assert len(slots) == 1440 + 1452 - 4 and len(set(slots)) == len(slots)
    assert all(HOURS.is_open(t) for t in slots)


# ---- the one-off run ------------------------------------------------------------------------

def _settings(tmp_path):
    return SimpleNamespace(
        market=SETTINGS.market, market_hours=SETTINGS.market_hours, candles=SETTINGS.candles,
        history=SimpleNamespace(folder=tmp_path / "history", weekly_budget_points=4000,
                                min_ig_allowance_remaining=2000, max_points_per_request=500, min_block_hours=24))


def _reply_for(p, remaining):
    if p.purpose == "ig-daily":
        rows = [row(T(2026, 10, 25, 22) + timedelta(days=d)) for d in range(12) if d % 7 not in (5, 6)]
    else:
        rows = [row(t) for t in p.slots]
    return Reply(200, {"prices": rows, "metadata": {
        "allowance": {"remainingAllowance": remaining, "totalAllowance": 10000, "allowanceExpiry": 86400},
        "size": len(rows), "pageData": {"totalPages": 1}}})


def _run(tmp_path, store, now, replies=None):
    s = _settings(tmp_path)
    plan = plan_one_off(store, HOURS, 500, now)
    rem = 9000
    replies = replies or []
    if not replies:
        for p in plan:
            rem -= p.points
            replies.append(_reply_for(p, rem))
    ig = FakeIG(login_ok(), accounts_ok(), switch_ok(), *replies)
    client = IGClient(SETTINGS.ig, CREDS, http=ig, sleep=lambda x: None)
    client.connect()
    door = HistoryDoor(client, s.history, now=lambda: now)
    out = []
    res = run_one_off(door, store, s, now, out.append)
    return res, ig, out, s, plan


def test_the_one_off_fill_records_the_gaps_fills_them_and_is_recorded_as_done(tmp_path, store):
    for i in range(4):
        store.add(five(T(2026, 11, 6, 19, 20) + i * FIVE, bo="13354.4", bh="13354.4", bl="13354.4",
                       bc="13354.4", so="13352.9", sh="13352.9", sl="13352.9", sc="13352.9"))
    res, ig, out, s, plan = _run(tmp_path, store, T(2026, 11, 7, 12))
    assert res.stored == 1440 + 1452 - 4
    assert [h for h in ig.calls() if h[1].startswith(HIST)][0][1].startswith(
        HIST + f"/{SETTINGS.market.epic}?resolution=DAY")
    assert len(store.recorded_gaps()) == 3   # week 1, week 2 before the live candles, after them
    done = json.loads((tmp_path / "history" / DONE_FILE).read_text())
    assert done["status"] == "done" and done["candles_stored"] == res.stored
    # The live candles were compared, not overwritten.
    assert len(res.compare_rows) == 4 and all(l.prices() == h.prices() for l, h in res.compare_rows)
    # It can never run again by itself.
    with pytest.raises(RuntimeError, match="already been run"):
        _run(tmp_path, store, T(2026, 11, 7, 12, 5), replies=[Reply(200, {})])
    # The checks afterwards: our daily boundaries, IG's daily candles, the store.
    said = []
    report_after(res, store, s, said.append)
    text = "\n".join(said)
    assert "4 of 4 identical" in text
    assert "C. STORE CHECKS ON EVERYTHING" in text and "0 problem(s)" in text


def test_the_fill_stops_if_igs_times_do_not_line_up(tmp_path, store):
    now = T(2026, 11, 7, 12)
    plan = plan_one_off(store, HOURS, 500, now)
    shifted = [_reply_for(plan[0], 8000)]
    p = plan[1]
    shifted.append(Reply(200, {"prices": [row(t - timedelta(hours=1)) for t in p.slots],
                               "metadata": {"allowance": {"remainingAllowance": 7000, "totalAllowance": 10000,
                                                          "allowanceExpiry": 86400}, "size": p.points}}))
    with pytest.raises(RuntimeError, match="do not line up"):
        _run(tmp_path, store, now, replies=shifted)
    assert store.newest("5m") is None
    assert json.loads((tmp_path / "history" / DONE_FILE).read_text())["status"] == "started"
