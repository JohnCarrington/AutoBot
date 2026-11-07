"""Technical tests for the news part (news/): the tiers (AutoBot 161's table),
the big-news no-trading windows for each pair's currencies, the expected
direction, fetching from a pretend Finnhub, keeping the key secret, and the
keeper (a few fetches a day, never a loop, an alert when the calendar is
missing or out of date). Never contacts Finnhub."""

import json
import logging
from datetime import datetime, timedelta, timezone

import pytest

from news.calendar import (BIG, DOWN, IN_LINE, MIDDLE, NO_DIRECTION, SMALL, UP, big_news_windows,
                           close_open_trades, expected_direction, no_new_trades, status, tier_of)
from news.finnhub import FinnhubKey, FinnhubNotSetUp, fetch, load_key, read_store, store_path
from news.keeper import NewsKeeper
from tests.technical.test_pairs import pretend

UTC = timezone.utc
KEY = "SECRET-finnhub-key-123"


def T(*a):
    return datetime(*a, tzinfo=UTC)


@pytest.fixture
def st(tmp_path):
    return pretend(tmp_path)                      # every folder in tmp_path


def ev(time, country, event, estimate=None, prev=None, impact="high"):
    return {"time_utc": time, "country": country, "event": event, "estimate": estimate, "prev": prev,
            "actual": None, "impact": impact, "unit": "%"}


BOE = ev("2026-11-05T12:00:00Z", "GB", "BoE Interest Rate Decision", 4.0, 4.0)


# ---- tiers: 161's table ----------------------------------------------------------------------

def test_the_tiers_are_161s_table(st):
    assert tier_of(st, "GBP", "BoE Interest Rate Decision") == BIG
    assert tier_of(st, "USD", "Non Farm Payrolls") == BIG
    assert tier_of(st, "GBP", "GDP MoM") == MIDDLE                   # 161: MIDDLE for GBP
    assert tier_of(st, "USD", "Initial Jobless Claims") == MIDDLE
    assert tier_of(st, "GBP", "BRC Shop Price Index YoY") == SMALL     # not listed: SMALL
    assert tier_of(st, "EUR", "Inflation Rate YoY") == SMALL           # no EUR list yet
    assert (len(st.news_tiers.big_GBP), len(st.news_tiers.big_USD)) == (11, 16)


# ---- windows ---------------------------------------------------------------------------------

def test_big_news_stops_new_trades_15_before_to_30_after_and_closes_trades_15_before(st):
    cal = [BOE]
    (w,) = big_news_windows(st, "GBPUSD", T(2026, 11, 5), T(2026, 11, 6), cal)
    assert (w.no_new_trades_from, w.no_new_trades_until, w.close_open_trades_at) == (
        T(2026, 11, 5, 11, 45), T(2026, 11, 5, 12, 30), T(2026, 11, 5, 11, 45))
    assert not no_new_trades(st, "GBPUSD", T(2026, 11, 5, 11, 44, 59), cal)
    assert no_new_trades(st, "GBPUSD", T(2026, 11, 5, 11, 45), cal)
    assert no_new_trades(st, "GBPUSD", T(2026, 11, 5, 12, 29, 59), cal)
    assert not no_new_trades(st, "GBPUSD", T(2026, 11, 5, 12, 30), cal)
    assert close_open_trades(st, "GBPUSD", T(2026, 11, 5, 11, 50), cal)
    assert not close_open_trades(st, "GBPUSD", T(2026, 11, 5, 12, 0), cal)       # released: nothing more to close


def test_only_big_news_in_the_pairs_own_currencies_counts(st):
    cal = [BOE, ev("2026-11-05T13:30:00Z", "US", "Initial Jobless Claims", 220, 218),       # USD MIDDLE: ignored
           ev("2026-11-05T09:00:00Z", "GB", "BRC Shop Price Index YoY", 1, 1),             # GBP SMALL: ignored
           ev("2026-11-06T13:30:00Z", "US", "Non Farm Payrolls", 150, 120),                # USD BIG
           ev("2026-11-05T10:00:00Z", "JP", "BoJ Interest Rate Decision")]                 # not GBP or USD
    got = [(w.currency, w.event) for w in big_news_windows(st, "GBPUSD", T(2026, 11, 4), T(2026, 11, 8), cal)]
    assert got == [("GBP", "BoE Interest Rate Decision"), ("USD", "Non Farm Payrolls")]
    assert big_news_windows(st, "EURJPY", T(2026, 11, 4), T(2026, 11, 8), cal) == []        # no EUR or JPY BIG list


# ---- expected direction (section 2.4) -------------------------------------------------------

@pytest.mark.parametrize("pair,currency,event,est,prev,want", [
    ("GBPUSD", "GBP", "Inflation Rate YoY", 3.4, 3.2, UP),        # higher: good for GBP -> GBPUSD up
    ("GBPUSD", "GBP", "Inflation Rate YoY", 3.0, 3.2, DOWN),
    ("GBPUSD", "USD", "Non Farm Payrolls", 180, 150, DOWN),       # good for USD -> GBPUSD down
    ("GBPUSD", "USD", "Unemployment Rate", 4.1, 4.3, DOWN),       # lower is better: good for USD
    ("GBPUSD", "GBP", "Claimant Count Change", 30, 20, DOWN),     # higher claims: bad for GBP
    ("GBPUSD", "GBP", "BoE Interest Rate Decision", 4.0, 4.0, IN_LINE),
    ("GBPUSD", "USD", "FOMC Minutes", None, None, NO_DIRECTION),
])
def test_the_expected_direction_is_the_forecast_against_the_previous_figure(st, pair, currency, event, est, prev, want):
    d, why = expected_direction(st, pair, currency, event, est, prev)
    assert d == want and why


# ---- fetching -------------------------------------------------------------------------------------

class Reply:
    def __init__(self, status=200, body=None):
        self.status_code, self._body = status, body

    def json(self):
        return self._body


class PretendFinnhub:
    def __init__(self, *replies):
        self.calls, self.replies = [], list(replies)

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, dict(params), timeout))
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def finnhub_rows(*rows):
    return Reply(200, {"economicCalendar": [
        {"time": t, "country": c, "event": e, "estimate": est, "prev": pv, "actual": None, "impact": "high",
         "unit": "%"} for t, c, e, est, pv in rows]})


def test_a_fetch_asks_for_the_window_and_keeps_a_merged_copy_on_disk(st):
    http = PretendFinnhub(finnhub_rows(("2026-11-05 12:00:00", "GB", "BoE Interest Rate Decision", 4.0, 4.0)),
                          finnhub_rows(("2026-11-05 12:00:00", "GB", "BoE Interest Rate Decision", 3.75, 4.0),
                                       ("2026-11-06 13:30:00", "US", "Non Farm Payrolls", 150, 120)))
    assert fetch(st, FinnhubKey(KEY), T(2026, 11, 3, 6), http).ok
    url, params, timeout = http.calls[0]
    assert url == "https://finnhub.io/api/v1/calendar/economic" and timeout == 20
    assert params == {"from": "2026-10-27", "to": "2026-11-17", "token": KEY}        # 7 days back, 14 ahead
    assert fetch(st, FinnhubKey(KEY), T(2026, 11, 3, 12), http).ok
    data = read_store(st)
    assert [(e["event"], e["estimate"]) for e in data["events"]] == [("BoE Interest Rate Decision", 3.75),
                                                                     ("Non Farm Payrolls", 150)]
    assert data["last_fetch_utc"] == "2026-11-03T12:00:00Z" and data["last_error"] is None
    assert data["events"][0]["time_utc"] == "2026-11-05T12:00:00Z"                  # Finnhub's time is UTC


def test_old_releases_are_dropped_after_keep_days(st):
    http = PretendFinnhub(finnhub_rows(("2026-08-01 12:00:00", "GB", "Inflation Rate YoY", 3, 3),
                                       ("2026-11-05 12:00:00", "GB", "BoE Interest Rate Decision", 4, 4)))
    fetch(st, FinnhubKey(KEY), T(2026, 11, 7), http)
    assert [e["event"] for e in read_store(st)["events"]] == ["BoE Interest Rate Decision"]


def test_the_key_is_never_logged_or_shown(st, caplog, tmp_path):
    caplog.set_level(logging.DEBUG)
    err = ConnectionError(f"HTTPSConnectionPool: /calendar/economic?token={KEY} failed")
    a = fetch(st, FinnhubKey(KEY), T(2026, 11, 7), PretendFinnhub(err))
    b = fetch(st, FinnhubKey(KEY), T(2026, 11, 7), PretendFinnhub(Reply(403, {"error": f"bad token {KEY}"})))
    assert (a.ok, a.why) == (False, "no reply from Finnhub (ConnectionError)")
    assert (b.ok, b.why) == (False, "Finnhub refused it: HTTP 403")
    shown = caplog.text + a.why + b.why + store_path(st).read_text() + repr(FinnhubKey(KEY))
    assert KEY not in shown and "SECRET" not in shown
    env = tmp_path / "x.env"
    env.write_text("IG_PASSWORD=x\n")
    with pytest.raises(FinnhubNotSetUp, match="FINNHUB_API_KEY must be set"):
        load_key(env)


def test_status_is_out_of_date_after_24_hours_or_if_never_fetched(st):
    assert not status(st, T(2026, 11, 7)).ok and "never been fetched" in status(st, T(2026, 11, 7)).why
    fetch(st, FinnhubKey(KEY), T(2026, 11, 7), PretendFinnhub(finnhub_rows()))
    assert status(st, T(2026, 11, 8)).ok
    s = status(st, T(2026, 11, 8, 0, 1))
    assert not s.ok and "out of date" in s.why


# ---- the keeper -------------------------------------------------------------------------------------

class Clock:
    def __init__(self, t):
        self.t = t

    def __call__(self):
        return self.t


class Alerts:
    def __init__(self):
        self.sent = []

    def problem(self, key, text):
        self.sent.append((key, text))


def test_the_keeper_fetches_a_few_times_a_day_never_in_a_loop(st):
    clock, alerts = Clock(T(2026, 11, 7, 6)), Alerts()
    http = PretendFinnhub(*[finnhub_rows() for _ in range(10)])
    k = NewsKeeper(st, alerts, now=clock, key_loader=lambda: FinnhubKey(KEY), http=http)
    for _ in range(600):                          # 10 minutes of ticks, once a second
        k.tick()
        clock.t += timedelta(seconds=1)
    assert len(http.calls) == 1                   # fetched once
    clock.t = T(2026, 11, 7, 11, 59)
    k.tick()
    assert len(http.calls) == 1                   # under 6 hours old
    clock.t = T(2026, 11, 7, 12, 10)
    k.tick()
    assert len(http.calls) == 2 and alerts.sent == []
    restarted = NewsKeeper(st, alerts, now=clock, key_loader=lambda: FinnhubKey(KEY), http=http)
    restarted.tick()
    assert len(http.calls) == 2                   # a restart uses the copy on disk


def test_after_a_failed_fetch_it_waits_60_minutes(st):
    clock, alerts = Clock(T(2026, 11, 7, 6)), Alerts()
    http = PretendFinnhub(Reply(500, {}), Reply(500, {}), finnhub_rows())
    k = NewsKeeper(st, alerts, now=clock, key_loader=lambda: FinnhubKey(KEY), http=http)
    k.tick()
    for minutes in range(5, 60, 5):
        clock.t = T(2026, 11, 7, 6) + timedelta(minutes=minutes)
        k.tick()
    assert len(http.calls) == 1
    clock.t = T(2026, 11, 7, 7, 0)
    k.tick()
    assert len(http.calls) == 2


def test_a_missing_or_out_of_date_calendar_sends_an_alert_at_most_every_6_hours(st):
    clock, alerts = Clock(T(2026, 11, 7, 6)), Alerts()

    def no_key():
        raise FinnhubNotSetUp("FINNHUB_API_KEY must be set in /opt/autobot/.env.")
    k = NewsKeeper(st, alerts, now=clock, key_loader=no_key)
    for hours in range(0, 12):
        clock.t = T(2026, 11, 7, 6) + timedelta(hours=hours)
        k.tick()
    assert len(alerts.sent) == 2                              # 06:00 and 12:00
    key, text = alerts.sent[0]
    assert key == "news-calendar" and "FINNHUB_API_KEY must be set" in text and "NOT blocked" in text


def test_a_news_problem_never_stops_the_price_service(st):
    def broken():
        raise RuntimeError("pretend")
    NewsKeeper(st, Alerts(), now=lambda: T(2026, 11, 7), key_loader=broken).tick()
