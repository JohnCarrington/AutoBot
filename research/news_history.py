"""The economic calendar for past dates, from Finnhub, for the research replays.

One request per calendar month, at least `gap_seconds` apart (default 20: at most 3 a
minute), backing off on a refusal and carrying on with the next month if one keeps
failing. Each month's reply is checked to reach both ends of the month; a month that
comes back cut short is fetched again in halves. Releases are kept in the same shape
as the bot's own calendar (news/finnhub.py), so the bot's news rules read them
unchanged. Saved to data/research/news/finnhub_calendar.json (never the live news
folder). The key is read as the bot reads it and never printed or saved.

    nice -n 19 .venv/bin/python -m research.news_history --from 2023-11 --to 2026-11
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from news.finnhub import _event_time

UTC = timezone.utc
OUT = Path("/opt/autobot/data/research/news/finnhub_calendar.json")


def months(first: str, last: str) -> list[tuple[date, date]]:
    """'2024-01', '2024-03' -> [(1 Jan, 31 Jan), (1 Feb, 29 Feb), (1 Mar, 31 Mar)]."""
    y, m = (int(x) for x in first.split("-"))
    ly, lm = (int(x) for x in last.split("-"))
    out = []
    while (y, m) <= (ly, lm):
        start = date(y, m, 1)
        y2, m2 = (y + (m == 12), m % 12 + 1)
        out.append((start, date(y2, m2, 1) - timedelta(days=1)))
        y, m = y2, m2
    return out


def release(x: dict) -> dict:
    return {"time_utc": _event_time(x["time"]), "country": str(x.get("country") or "").upper(),
            "event": str(x.get("event") or "").strip(), "impact": x.get("impact"),
            "estimate": x.get("estimate"), "prev": x.get("prev"), "actual": x.get("actual"), "unit": x.get("unit")}


def covers(rows: list[dict], start: date, end: date) -> bool:
    """The reply reaches the first two and the last two days of the range (a cut-short reply does not).
    Weekend ends are allowed for: the check is on the weekdays nearest each end."""
    if not rows:
        return False
    days = {r["time_utc"][:10] for r in rows}
    def weekday_near(d: date, step: int) -> date:
        while d.weekday() > 4:
            d += timedelta(days=step)
        return d
    first, last = weekday_near(start, 1), weekday_near(end, -1)
    return first.isoformat() in days and last.isoformat() in days


class Fetcher:
    def __init__(self, url: str, key: Any, http: Any, *, gap_seconds: float = 20, timeout: float = 30,
                 sleep: Callable[[float], None] = time.sleep, clock: Callable[[], float] = time.monotonic,
                 log: Callable[[str], None] = print):
        self.url, self.key, self.http = url, key, http
        self.gap, self.timeout, self.sleep, self.clock, self.log = gap_seconds, timeout, sleep, clock, log
        self._last: float | None = None
        self.requests = 0

    def _wait(self) -> None:
        if self._last is not None:
            left = self.gap - (self.clock() - self._last)
            if left > 0:
                self.sleep(left)
        self._last = self.clock()

    def get(self, start: date, end: date, tries: int = 3) -> list[dict] | None:
        """One range, retried gently (2, then 4 minutes) on a refusal. None if it never worked."""
        for n in range(tries):
            self._wait()
            self.requests += 1
            try:
                r = self.http.get(f"{self.url}/calendar/economic",
                                  params={"from": start.isoformat(), "to": end.isoformat(), "token": self.key.key},
                                  timeout=self.timeout)
                if r.status_code == 200:
                    rows = (r.json() or {}).get("economicCalendar")
                    if isinstance(rows, list):
                        return [release(x) for x in rows]
                    why = "no economicCalendar list in the reply"
                else:
                    why = f"HTTP {r.status_code}"
            except Exception as e:          # the error text may hold the address, and so the key: kind only
                why = f"no reply ({type(e).__name__})"
            self.log(f"  {start}..{end}: {why}; try {n + 1} of {tries}")
            if n + 1 < tries:
                self.sleep(120 * (n + 1))
        return None

    def month(self, start: date, end: date, depth: int = 0) -> tuple[list[dict], list[str]]:
        rows = self.get(start, end)
        if rows is None:
            return [], [f"{start}..{end}: not fetched"]
        if covers(rows, start, end) or depth >= 3 or start == end:
            return rows, [] if covers(rows, start, end) else [f"{start}..{end}: reply does not reach both ends"]
        mid = start + (end - start) // 2
        a, pa = self.month(start, mid, depth + 1)
        b, pb = self.month(mid + timedelta(days=1), end, depth + 1)
        return a + b, pa + pb


def save(path: Path, events: list[dict], problems: list[str], ranges: list[str]) -> None:
    merged = {(e["time_utc"], e["country"], e["event"]): e for e in events}
    data = {"events": sorted(merged.values(), key=lambda e: (e["time_utc"], e["country"], e["event"])),
            "covers": ranges, "problems": problems, "fetched_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": "Finnhub /calendar/economic, one request per month (research.news_history)"}
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1) + "\n")
    tmp.replace(path)


def load(path: Path = OUT) -> dict:
    return json.loads(Path(path).read_text())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="first", required=True)
    ap.add_argument("--to", dest="last", required=True)
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args(argv)
    if "/data/research/" not in str(a.out.resolve()):
        raise SystemExit("the research calendar must be written under data/research/")
    import requests
    from config.settings_loader import load_settings
    from news.finnhub import load_key
    s = load_settings().for_pair("GBPUSD")
    f = Fetcher(s.news.finnhub_url, load_key(), requests.Session())
    events, problems, ranges = [], [], []
    for start, end in months(a.first, a.last):
        rows, probs = f.month(start, end)
        events += rows
        problems += probs
        ranges.append(f"{start}/{end}")
        print(f"{start:%Y-%m}: {len(rows)} releases{'  PROBLEM: ' + '; '.join(probs) if probs else ''}", flush=True)
        save(a.out, events, problems, ranges)      # saved after every month: a stop loses nothing
    print(f"done: {len(events)} releases, {f.requests} requests, {len(problems)} problem(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
