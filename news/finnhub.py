"""Fetches the economic calendar from Finnhub and keeps a copy on disk.

The API key comes from .env (FINNHUB_API_KEY). It is never printed, logged, put
in a message or in an error: it travels in the request's address, so a failed
request is reported by its kind and Finnhub's HTTP status only, never by the
address or the library's own error text (and the HTTP library's request logging
is kept quiet). This module talks to Finnhub only, never to IG.

The copy on disk, <news.folder>/calendar.json (safe writes), holds every release
fetched so far, merged by (time, country, event): a newer fetch updates a
release's figures; releases older than news.keep_days are dropped. It also
records when the last good fetch was, and when the last attempt was, so that a
restart never needs to fetch again and a failure is not retried in a loop.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from config.env_file import env_path, parse
from housekeeping.files import safe_write

log = logging.getLogger("autobot.news")
logging.getLogger("urllib3").setLevel(logging.WARNING)   # it would log the address, key included
UTC = timezone.utc
FILE = "calendar.json"


class FinnhubNotSetUp(Exception):
    pass


@dataclass(frozen=True)
class FinnhubKey:
    key: str = field(repr=False)

    def __repr__(self) -> str:
        return "FinnhubKey(secret hidden)"

    __str__ = __repr__


def load_key(path: str | Path | None = None) -> FinnhubKey:
    path = Path(path or env_path())
    try:
        values = parse(path.read_text())
    except (FileNotFoundError, PermissionError):
        raise FinnhubNotSetUp(f"{path} cannot be read.") from None
    if not values.get("FINNHUB_API_KEY"):
        raise FinnhubNotSetUp(f"FINNHUB_API_KEY must be set in {path}.")
    return FinnhubKey(values["FINNHUB_API_KEY"])


def store_path(settings: Any) -> Path:
    return Path(settings.news.folder) / FILE


def read_store(settings: Any) -> dict:
    p = store_path(settings)
    if not p.exists():
        return {"events": [], "last_fetch_utc": None, "last_attempt_utc": None, "last_error": None}
    return json.loads(p.read_text())


def _write(settings: Any, data: dict) -> None:
    p = store_path(settings)
    p.parent.mkdir(parents=True, exist_ok=True)
    safe_write(p, (json.dumps(data, indent=1, sort_keys=True) + "\n").encode())


def _iso(t: datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _event_time(text: str) -> str:
    """Finnhub's "time" ("2026-11-05 12:00:00", UTC) -> "2026-11-05T12:00:00Z"."""
    return datetime.strptime(text[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class FetchResult:
    ok: bool
    why: str
    received: int = 0


def fetch(settings: Any, key: FinnhubKey, now: datetime, http: Any = None) -> FetchResult:
    """One request for the calendar from fetch_days_back to fetch_days_ahead; merged into the copy on disk."""
    n = settings.news
    data = read_store(settings)
    data["last_attempt_utc"] = _iso(now)
    start = (now - timedelta(days=n.fetch_days_back)).date()
    end = (now + timedelta(days=n.fetch_days_ahead)).date()
    if http is None:
        import requests
        http = requests.Session()
    url = f"{n.finnhub_url}/calendar/economic"
    try:
        r = http.get(url, params={"from": start.isoformat(), "to": end.isoformat(), "token": key.key},
                     timeout=n.request_timeout_seconds)
    except Exception as e:          # the error text may hold the address (and so the key): kind only
        why = f"no reply from Finnhub ({type(e).__name__})"
        data["last_error"] = why
        _write(settings, data)
        log.warning("Economic calendar NOT fetched: %s.", why)
        return FetchResult(False, why)
    if r.status_code != 200:
        why = f"Finnhub refused it: HTTP {r.status_code}"
        data["last_error"] = why
        _write(settings, data)
        log.warning("Economic calendar NOT fetched: %s.", why)
        return FetchResult(False, why)
    try:
        rows = (r.json() or {}).get("economicCalendar")
        if not isinstance(rows, list):
            raise ValueError("no economicCalendar list")
        fresh = []
        for x in rows:
            fresh.append({"time_utc": _event_time(x["time"]), "country": str(x.get("country") or "").upper(),
                          "event": str(x.get("event") or "").strip(), "impact": x.get("impact"),
                          "estimate": x.get("estimate"), "prev": x.get("prev"), "actual": x.get("actual"),
                          "unit": x.get("unit")})
    except Exception as e:
        why = f"Finnhub's reply could not be read ({type(e).__name__})"
        data["last_error"] = why
        _write(settings, data)
        log.warning("Economic calendar NOT fetched: %s.", why)
        return FetchResult(False, why)
    merged = {(e["time_utc"], e["country"], e["event"]): e for e in data["events"]}
    for e in fresh:
        merged[(e["time_utc"], e["country"], e["event"])] = e
    cutoff = _iso(now - timedelta(days=n.keep_days))
    data["events"] = sorted((e for e in merged.values() if e["time_utc"] >= cutoff),
                            key=lambda e: (e["time_utc"], e["country"], e["event"]))
    data["last_fetch_utc"] = _iso(now)
    data["covers"] = sorted({*data.get("covers", []), f"{start.isoformat()}/{end.isoformat()}"})[-50:]
    data["last_error"] = None
    _write(settings, data)
    log.info("Economic calendar fetched: %d releases from %s to %s; %d kept on disk.", len(fresh), start, end,
             len(data["events"]))
    return FetchResult(True, "fetched", len(fresh))
