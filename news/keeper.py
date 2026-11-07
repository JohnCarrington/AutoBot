"""Keeps the economic calendar up to date, run by the price service about once
a second (it acts only every news.check_minutes).

  * fetches when the copy on disk is older than news.refresh_hours (or there is
    none), and never sooner than news.retry_minutes after the last attempt: at
    most a few requests a day, never a fast loop; a restart does not fetch if
    the copy on disk is fresh;
  * if the calendar is missing or out of date (news.out_of_date_hours), or the
    Finnhub key is not set up: a Telegram problem alert, at most every
    news.alert_every_hours while it lasts. Trading is not blocked by this.
It can never stop the price service: any problem is written as a warning.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from news.calendar import status
from news.finnhub import FinnhubNotSetUp, fetch, load_key, read_store

log = logging.getLogger("autobot.news")
UTC = timezone.utc


def _t(text: str | None) -> datetime | None:
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC) if text else None


class NewsKeeper:
    def __init__(self, settings: Any, alerts: Any, now: Callable[[], datetime] = lambda: datetime.now(UTC),
                 key_loader: Callable[[], Any] = load_key, http: Any = None):
        self.s, self.alerts, self.now = settings, alerts, now
        self.key_loader, self.http = key_loader, http
        self._next_check: datetime | None = None
        self._last_alert: datetime | None = None
        self.fetches = 0

    def tick(self) -> None:
        try:
            now = self.now()
            if self._next_check is not None and now < self._next_check:
                return
            self._next_check = now + timedelta(minutes=self.s.news.check_minutes)
            self._check(now)
        except Exception as e:          # never stop the price service
            log.warning("News calendar check failed: %s: %s", type(e).__name__, e)

    def due(self, now: datetime) -> bool:
        n, data = self.s.news, read_store(self.s)
        last_fetch, last_try = _t(data.get("last_fetch_utc")), _t(data.get("last_attempt_utc"))
        stale = last_fetch is None or now - last_fetch >= timedelta(hours=n.refresh_hours)
        rested = last_try is None or now - last_try >= timedelta(minutes=n.retry_minutes)
        return stale and rested

    def _check(self, now: datetime) -> None:
        problem = None
        if self.due(now):
            try:
                key = self.key_loader()
            except FinnhubNotSetUp as e:
                problem = f"the economic calendar cannot be fetched: {e}"
            else:
                self.fetches += 1
                fetch(self.s, key, now, self.http)
        st = status(self.s, now)
        if problem is None and not st.ok:
            problem = st.why
        if problem is None:
            self._last_alert = None
            return
        if self._last_alert is None or now - self._last_alert >= timedelta(hours=self.s.news.alert_every_hours):
            self._last_alert = now
            self.alerts.problem("news-calendar", f"{problem}. New trades are NOT blocked by this: the news "
                                                 "windows use the last calendar on disk.")
