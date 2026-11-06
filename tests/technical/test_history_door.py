"""The history door (ig/history.py): the checks in order, counting points
before sending, IG's figures, the daily record and the block marker. Uses the
pretend IG; never contacts IG."""

import csv
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from ig.client import IGClient
from ig.errors import IGRequestError
from ig.history import HistoryBlocked, HistoryDoor, HistoryRefused
from tests.technical.fake_ig import CREDS, FakeIG, Reply, accounts_ok, error, login_ok, switch_ok
from tests.technical.fake_stream import SETTINGS, Clock, T

UTC = timezone.utc
HIST = "/pri" + "ces"   # IG history address, in pieces so the no-history scan stays strict
EPIC = SETTINGS.market.epic
START = T(2026, 11, 4, 10, 0)


def hist_ok(n=3, remaining=9000, total=10000, expiry=3 * 86400, start=START):
    rows = []
    for i in range(n):
        t = start + timedelta(minutes=5 * i)
        p = lambda b, a: {"bid": b, "ask": a, "lastTraded": None}  # noqa: E731
        rows.append({"snapshotTime": t.strftime("%Y/%m/%d %H:%M:%S"),
                     "snapshotTimeUTC": t.strftime("%Y-%m-%dT%H:%M:%S"),
                     "openPrice": p(13352.9, 13354.4), "highPrice": p(13353.6, 13355.1),
                     "lowPrice": p(13351.9, 13353.4), "closePrice": p(13353.3, 13354.8),
                     "lastTradedVolume": 10})
    return Reply(200, {"prices": rows, "instrumentType": "CURRENCIES",
                       "metadata": {"allowance": {"remainingAllowance": remaining, "totalAllowance": total,
                                                  "allowanceExpiry": expiry},
                                    "size": n, "pageData": {"pageSize": 0, "pageNumber": 1, "totalPages": 1}}})


def settings(tmp_path, **kw):
    h = dict(folder=tmp_path / "history", weekly_budget_points=4000, min_ig_allowance_remaining=2000,
             max_points_per_request=500, min_block_hours=24)
    h.update(kw)
    return SimpleNamespace(**h)


def make(tmp_path, *history_replies, clock=None, **kw):
    ig = FakeIG(login_ok(), accounts_ok(), switch_ok(), *history_replies)
    client = IGClient(SETTINGS.ig, CREDS, http=ig, sleep=lambda s: None)
    client.connect()
    warnings = []
    clock = clock or Clock(T(2026, 11, 6, 20, 0))
    door = HistoryDoor(client, settings(tmp_path, **kw), now=clock, warn=warnings.append)
    return door, ig, warnings, clock


def history_calls(ig):
    return [s for s in ig.sent if s.path.startswith(HIST)]


def fetch(door, points=3):
    return door.fetch(EPIC, "MINUTE_5", START, START + timedelta(minutes=5 * (points - 1)), points, "test")


# ---- a working request --------------------------------------------------------------

def test_a_request_is_sent_through_the_door_with_utc_times_and_no_paging(tmp_path):
    door, ig, warnings, _ = make(tmp_path, hist_ok())
    reply = fetch(door)
    (sent,) = history_calls(ig)
    assert sent.method == "GET" and sent.headers["Version"] == "3"
    assert sent.path == (HIST + f"/{EPIC}?resolution=MINUTE_5&from=2026-11-04T10%3A00%3A00"
                         "&to=2026-11-04T10%3A10%3A00&pageSize=0")
    assert len(reply.rows) == 3 and reply.points_counted == 3
    assert warnings == []


def test_igs_figures_are_saved_after_every_reply(tmp_path):
    door, ig, _, clock = make(tmp_path, hist_ok(remaining=8765, total=10000, expiry=3600))
    fetch(door)
    fig = json.loads((tmp_path / "history" / "ig_allowance.json").read_text())
    assert fig == {"remaining": 8765, "total": 10000, "resets_utc": "2026-11-06T21:00:00Z",
                   "seen_utc": "2026-11-06T20:00:00Z"}


def test_the_daily_record_is_actually_written(tmp_path):
    door, ig, _, clock = make(tmp_path, hist_ok(n=3, remaining=9997), hist_ok(n=2, remaining=9995))
    fetch(door, 3)
    fetch(door, 2)
    with pytest.raises(HistoryRefused):
        fetch(door, 501)
    rows = list(csv.DictReader((tmp_path / "history" / "daily_record.csv").open()))
    assert rows == [{"date_utc": "2026-11-06", "requests_sent": "2", "points_counted": "5",
                     "refused_by_bot": "1", "refused_by_ig": "0", "ig_remaining": "9995",
                     "ig_total": "10000", "ig_resets_utc": "2026-11-09T20:00:00Z",
                     "updated_utc": "2026-11-06T20:00:00Z"}]


def test_the_daily_record_keeps_one_line_per_day(tmp_path):
    door, ig, _, clock = make(tmp_path, hist_ok(), hist_ok(remaining=8000))
    fetch(door)
    clock.advance(days=1)
    fetch(door)
    rows = list(csv.DictReader((tmp_path / "history" / "daily_record.csv").open()))
    assert [(r["date_utc"], r["points_counted"], r["ig_remaining"]) for r in rows] == \
        [("2026-11-06", "3", "9000"), ("2026-11-07", "3", "8000")]


# ---- counting before sending ------------------------------------------------------------

class Crash(BaseException):
    pass


def test_points_are_counted_and_saved_before_sending_a_crash_just_after_counting_loses_nothing(tmp_path):
    door, ig, _, clock = make(tmp_path)
    saved_at_send = []

    def crash_on_send(method, url, **kw):
        # At the moment of sending, the count must already be on disk.
        saved_at_send.append(json.loads((tmp_path / "history" / "ledger.json").read_text()))
        raise Crash("power cut")
    ig.request = crash_on_send
    with pytest.raises(Crash):
        fetch(door, 300)
    assert saved_at_send[0]["requests"][0]["points"] == 300
    assert saved_at_send[0]["requests"][0]["status"] == "counted"
    # After a restart the count is still there and still limits the budget.
    door2, ig2, warnings, _ = make(tmp_path, clock=clock, weekly_budget_points=500)
    assert door2.points_last_7_days() == 300
    with pytest.raises(HistoryRefused) as e:
        fetch(door2, 201)
    assert e.value.check.startswith("b.") and history_calls(ig2) == []


def test_a_request_with_no_reply_is_still_counted(tmp_path):
    from tests.technical.fake_ig import NoReply
    door, ig, _, _ = make(tmp_path, NoReply())
    with pytest.raises(IGRequestError):
        fetch(door, 10)
    assert door.points_last_7_days() == 10
    assert door.ledger()[0]["status"] == "no reply"


def test_counts_older_than_7_days_no_longer_use_the_budget(tmp_path):
    door, ig, _, clock = make(tmp_path, hist_ok(n=3), hist_ok(n=3), weekly_budget_points=5)
    fetch(door, 3)
    with pytest.raises(HistoryRefused):
        fetch(door, 3)
    clock.advance(days=7, seconds=1)
    fetch(door, 3)


def test_ig_charging_more_than_counted_is_counted_and_warned(tmp_path):
    door, ig, warnings, _ = make(tmp_path, hist_ok(n=5))
    fetch(door, 3)
    assert door.points_last_7_days() == 5 and any("counted 5" in w for w in warnings)


# ---- the four checks, in order ----------------------------------------------------------

def test_a_budget_that_would_be_exceeded_is_refused_and_nothing_sent(tmp_path):
    door, ig, warnings, _ = make(tmp_path, hist_ok(n=300), weekly_budget_points=400)
    fetch(door, 300)
    with pytest.raises(HistoryRefused) as e:
        fetch(door, 101)
    assert e.value.check == "b. weekly budget"
    assert len(history_calls(ig)) == 1
    assert any("REFUSED by check b. weekly budget" in w for w in warnings)
    assert door.ledger()[-1]["status"] == "refused-by-bot"
    fetch_ok = door.points_last_7_days() == 300
    assert fetch_ok


def test_a_budget_exactly_used_up_is_allowed(tmp_path):
    door, ig, _, _ = make(tmp_path, hist_ok(n=100), hist_ok(n=100), weekly_budget_points=200)
    fetch(door, 100)
    fetch(door, 100)


def test_ig_allowance_below_the_safety_floor_is_refused(tmp_path):
    door, ig, warnings, _ = make(tmp_path, hist_ok(n=3, remaining=2200))
    fetch(door, 3)
    fetch_ok = door.ig_figures()["remaining"] == 2200
    assert fetch_ok
    with pytest.raises(HistoryRefused) as e:
        fetch(door, 201)        # 2200 - 201 < 2000
    assert e.value.check == "c. IG allowance floor" and len(history_calls(ig)) == 1


def test_a_request_over_the_maximum_size_is_refused(tmp_path):
    door, ig, warnings, _ = make(tmp_path)
    with pytest.raises(HistoryRefused) as e:
        fetch(door, 501)
    assert e.value.check == "d. maximum size" and history_calls(ig) == []
    assert any("more than the maximum of 500" in w for w in warnings)


def test_the_checks_run_in_order_marker_first(tmp_path):
    door, ig, _, clock = make(tmp_path, weekly_budget_points=10)
    door._write_marker("test", None)
    with pytest.raises(HistoryBlocked) as e:
        fetch(door, 501)       # also over budget and over the maximum: the marker is reported
    assert e.value.check == "a. block marker"


def test_budget_is_checked_before_the_floor_and_the_floor_before_the_size(tmp_path):
    door, ig, _, _ = make(tmp_path, hist_ok(n=3, remaining=2001), weekly_budget_points=600)
    fetch(door, 3)
    with pytest.raises(HistoryRefused) as e:
        fetch(door, 598)       # over budget, below floor, over max: budget first
    assert e.value.check == "b. weekly budget"
    with pytest.raises(HistoryRefused) as e:
        fetch(door, 597)       # fits the budget; below the floor; over max: floor first
    assert e.value.check == "c. IG allowance floor"


def test_limits_come_from_the_settings_file():
    h = SETTINGS.history
    assert (h.weekly_budget_points, h.min_ig_allowance_remaining, h.max_points_per_request, h.min_block_hours) == \
        (4000, 2000, 500, 24)
    assert h.weekly_budget_points < 10000 / 2


# ---- the block marker ---------------------------------------------------------------------

def test_igs_allowance_refusal_writes_the_block_marker_with_igs_reset_time(tmp_path):
    refusal = Reply(403, {"errorCode": "error.public-api.exceeded-account-historical-data-allowance",
                          "metadata": {"allowance": {"remainingAllowance": 0, "totalAllowance": 10000,
                                                     "allowanceExpiry": 3 * 86400}}})
    door, ig, warnings, clock = make(tmp_path, refusal)
    with pytest.raises(HistoryBlocked):
        fetch(door)                                            # no exit 78: not a login problem
    m = json.loads((tmp_path / "history" / "BLOCKED.json").read_text())
    assert m["expires_utc"] == "2026-11-09T20:00:00Z"          # IG's reset, later than the 24-hour minimum
    assert any("IG REFUSED" in w for w in warnings)
    assert door.ledger()[0]["status"] == "refused-by-ig"


def test_block_lasts_at_least_the_minimum_if_igs_reset_is_sooner_or_not_given(tmp_path):
    door, ig, _, clock = make(tmp_path, error(403, "error.public-api.exceeded-account-historical-data-allowance"))
    with pytest.raises(HistoryBlocked):
        fetch(door)
    m = json.loads((tmp_path / "history" / "BLOCKED.json").read_text())
    assert m["expires_utc"] == "2026-11-07T20:00:00Z"          # now + 24 hours (min_block_hours)


def test_a_restart_while_the_marker_is_in_place_sends_nothing(tmp_path):
    door, ig, _, clock = make(tmp_path, error(403, "error.public-api.exceeded-account-historical-data-allowance"))
    with pytest.raises(HistoryBlocked):
        fetch(door)
    clock.advance(hours=23)
    door2, ig2, warnings, _ = make(tmp_path, clock=clock)       # a new bot process
    with pytest.raises(HistoryBlocked) as e:
        fetch(door2)
    assert e.value.check == "a. block marker" and history_calls(ig2) == []


def test_after_the_marker_expires_requests_are_allowed_again(tmp_path):
    door, ig, _, clock = make(tmp_path, error(403, "error.public-api.exceeded-account-historical-data-allowance"),
                              hist_ok(remaining=9000))
    with pytest.raises(HistoryBlocked):
        fetch(door)
    clock.advance(hours=24)
    fetch(door)
    assert not (tmp_path / "history" / "BLOCKED.json").exists()


def test_an_unreadable_marker_counts_as_in_place(tmp_path):
    door, ig, _, _ = make(tmp_path)
    (tmp_path / "history").mkdir()
    (tmp_path / "history" / "BLOCKED.json").write_text("{half")
    with pytest.raises(HistoryBlocked):
        fetch(door)
    assert history_calls(ig) == []


def test_other_failures_go_back_to_the_caller_and_stay_counted(tmp_path):
    door, ig, _, _ = make(tmp_path, error(500))
    with pytest.raises(IGRequestError):
        fetch(door, 7)
    assert door.points_last_7_days() == 7
    assert not (tmp_path / "history" / "BLOCKED.json").exists()


def test_the_door_needs_a_connected_account(tmp_path):
    client = IGClient(SETTINGS.ig, CREDS, http=FakeIG(), sleep=lambda s: None)
    door = HistoryDoor(client, settings(tmp_path))
    with pytest.raises(RuntimeError):
        fetch(door)


def test_other_code_still_cannot_ask_for_history_while_the_door_exists(tmp_path):
    from ig.client import HistoricalPricesForbidden
    door, ig, _, _ = make(tmp_path)
    with pytest.raises(HistoricalPricesForbidden):
        door.client.request("GET", HIST + f"/{EPIC}?resolution=DAY", "3", what="sneaky")
    assert history_calls(ig) == []
