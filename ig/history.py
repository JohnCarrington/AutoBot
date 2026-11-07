"""THE HISTORY DOOR: the only place in the bot allowed to ask IG for
historical prices. Nothing else can: ig.client refuses any /prices call unless
this door has opened it, and a test fails if any other code names it.

Every request must pass these checks, in this order, or it is refused (nothing
is sent) and the refusal is logged and written to the daily record:
  a. No block marker is in place.
  b. The bot's own weekly budget has room for it: points counted in the last
     7 days + this request <= history.weekly_budget_points.
  c. IG's last reported remaining allowance, less this request, stays at or
     above history.min_ig_allowance_remaining. (Before IG has ever reported a
     figure there is nothing to check against; the first request is then
     allowed and its reply gives the figure.)
  d. The request is no bigger than history.max_points_per_request.

Then:
  * The points are counted and saved to disk BEFORE the request is sent, so a
    crash or restart can never lose count. A request whose reply never came is
    still counted.
  * After every reply, IG's own figures are saved: remaining allowance, total
    allowance, and when it resets.
  * If IG refuses because the allowance is used up, a block marker is written
    with the time it expires: IG's reset time if given, and never sooner than
    history.min_block_hours. While it is in place nothing is sent, even after a
    restart. An unreadable marker counts as in place.
  * A daily record (points used, requests, refusals, IG's figures) is rewritten
    after every request and every refusal.

ONE door, ONE budget and ONE copy of IG's allowance for ALL pairs: IG's
history allowance belongs to the account, not to a pair, so every pair's
requests count against the same weekly budget and the same floor. Each
request records its epic in the ledger.

Files, in history.folder itself, shared by all pairs (all written with safe writes):
  ledger.json         every request: when, points, epic, what, what happened
  ig_allowance.json   IG's last reported figures
  daily_record.csv    one line per UTC day
  BLOCKED.json        the block marker (only while blocked)
"""

from __future__ import annotations

import csv
import io
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlencode

from housekeeping.files import safe_write
from ig.errors import HISTORY_ALLOWANCE_EXCEEDED, IGRequestError, short_code

log = logging.getLogger("autobot.ig.history")

UTC = timezone.utc
RESOLUTIONS = {"MINUTE_5", "DAY"}
DAILY_COLUMNS = ("date_utc", "requests_sent", "points_counted", "refused_by_bot", "refused_by_ig",
                 "ig_remaining", "ig_total", "ig_resets_utc", "updated_utc")


class HistoryRefused(Exception):
    """A request was refused by one of the door's checks. Nothing was sent."""

    def __init__(self, check: str, reason: str):
        self.check = check
        super().__init__(f"History request refused ({check}): {reason}")


class HistoryBlocked(HistoryRefused):
    """IG refused because the allowance is used up. A block marker was written."""


@dataclass
class HistoryReply:
    rows: list[dict]           # IG's price rows, as sent
    points_counted: int
    ig_size: int | None
    remaining: int | None
    total: int | None
    resets: datetime | None
    pages: int | None


def _iso(t: datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def ig_time(t: datetime) -> str:
    """How a time is sent to IG: UTC, 'YYYY-MM-DDTHH:MM:SS'."""
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S")


class HistoryDoor:
    def __init__(self, client: Any, history_settings: Any, *,
                 now: Callable[[], datetime] = lambda: datetime.now(UTC),
                 warn: Callable[[str], None] | None = None):
        self.client = client
        self.s = history_settings
        self.folder = Path(history_settings.folder)
        self.now = now
        self.warn = warn or (lambda m: log.warning(m))

    # ---- files ------------------------------------------------------------------

    @property
    def ledger_path(self) -> Path:
        return self.folder / "ledger.json"

    @property
    def allowance_path(self) -> Path:
        return self.folder / "ig_allowance.json"

    @property
    def daily_path(self) -> Path:
        return self.folder / "daily_record.csv"

    @property
    def marker_path(self) -> Path:
        return self.folder / "BLOCKED.json"

    def _write_json(self, path: Path, data: Any) -> None:
        safe_write(path, (json.dumps(data, indent=1) + "\n").encode())

    def ledger(self) -> list[dict]:
        if not self.ledger_path.exists():
            return []
        return json.loads(self.ledger_path.read_text())["requests"]

    def _save_ledger(self, entries: list[dict]) -> None:
        self._write_json(self.ledger_path, {"requests": entries})

    def ig_figures(self) -> dict | None:
        if not self.allowance_path.exists():
            return None
        return json.loads(self.allowance_path.read_text())

    def points_last_7_days(self, now: datetime | None = None) -> int:
        now = now or self.now()
        week_ago = now - timedelta(days=7)
        return sum(e["points"] for e in self.ledger()
                   if e["status"] != "refused-by-bot" and _parse(e["counted_utc"]) > week_ago)

    # ---- the block marker -------------------------------------------------------

    def block_in_place(self) -> str | None:
        """Why history is blocked, or None. An unreadable marker counts as in place."""
        if not self.marker_path.exists():
            return None
        try:
            m = json.loads(self.marker_path.read_text())
            until = _parse(m["expires_utc"])
        except Exception:
            return f"a block marker is in place ({self.marker_path}) and cannot be read; remove it by hand once checked"
        if self.now() >= until:
            log.info("The history block marker expired at %s; removing it.", m["expires_utc"])
            self.marker_path.unlink()
            return None
        return f"blocked until {m['expires_utc']} ({m.get('reason', '')})"

    def _write_marker(self, reason: str, ig_resets: datetime | None) -> datetime:
        now = self.now()
        until = now + timedelta(hours=self.s.min_block_hours)
        if ig_resets is not None and ig_resets > until:
            until = ig_resets
        self._write_json(self.marker_path, {"written_utc": _iso(now), "expires_utc": _iso(until),
                                            "ig_resets_utc": _iso(ig_resets) if ig_resets else None,
                                            "reason": reason})
        return until

    # ---- the one way in -----------------------------------------------------------

    def fetch(self, epic: str, resolution: str, start: datetime, end: datetime,
              points: int, purpose: str) -> HistoryReply:
        """Ask IG for `resolution` candles from `start` to `end` (UTC, both
        inclusive), which the caller has worked out is at most `points` candles."""
        if not getattr(self.client, "account_active", False):
            raise RuntimeError("Not connected to the bot's IG account. Call connect() first.")
        if resolution not in RESOLUTIONS:
            raise ValueError(f"unknown resolution {resolution!r}")
        if points < 1:
            raise ValueError("a request must count at least 1 point")
        what = {"epic": epic, "resolution": resolution, "from_utc": _iso(start), "to_utc": _iso(end), "purpose": purpose}

        # a. block marker
        why = self.block_in_place()
        if why:
            self._refuse("a. block marker", why, points, what)
        # b. the bot's own weekly budget
        used = self.points_last_7_days()
        if used + points > self.s.weekly_budget_points:
            self._refuse("b. weekly budget", f"{used} points used in the last 7 days + {points} would be over "
                                             f"the bot's budget of {self.s.weekly_budget_points}", points, what)
        # c. IG's remaining allowance above the safety floor
        fig = self.ig_figures()
        if fig is not None and fig.get("remaining") is not None:
            if fig["remaining"] - points < self.s.min_ig_allowance_remaining:
                self._refuse("c. IG allowance floor",
                             f"IG last reported {fig['remaining']} points remaining ({fig['seen_utc']}); "
                             f"{points} more would leave less than the floor of "
                             f"{self.s.min_ig_allowance_remaining}", points, what)
        # d. maximum size
        if points > self.s.max_points_per_request:
            self._refuse("d. maximum size", f"{points} points is more than the maximum of "
                                            f"{self.s.max_points_per_request} per request", points, what)

        # Count first, save straight away, then send.
        entries = self.ledger()
        entry = {"counted_utc": _iso(self.now()), "points": points, "status": "counted", **what}
        entries.append(entry)
        self._save_ledger(entries)
        self._write_daily()

        query = urlencode({"resolution": resolution, "from": ig_time(start), "to": ig_time(end),
                           "pageSize": 0})
        path = f"/prices/{epic}?{query}"
        try:
            with self.client._open_history_door():
                r = self.client._call("GET", path, "3", what="a history request")
        except IGRequestError as e:
            self._finish(entries, entry, "no reply", None)
            raise IGRequestError("history request", e.status, e.error_code) from None

        body = self._json(r)
        allowance = (body.get("metadata") or {}).get("allowance") or {}
        resets = self._save_ig_figures(allowance)
        if not 200 <= r.status_code < 300:
            code = short_code((body or {}).get("errorCode"))
            if code in HISTORY_ALLOWANCE_EXCEEDED:
                until = self._write_marker(f"IG refused: {code}", resets)
                self._finish(entries, entry, "refused-by-ig", None)
                msg = (f"IG REFUSED a history request because the allowance is used up ({code}). "
                       f"Block marker written: no history requests until {_iso(until)}.")
                self.warn(msg)
                raise HistoryBlocked("IG allowance", msg)
            self._finish(entries, entry, f"failed HTTP {r.status_code} {code or ''}".strip(), None)
            raise IGRequestError("history request", r.status_code, code)

        meta = body.get("metadata") or {}
        size = meta.get("size")
        pages = (meta.get("pageData") or {}).get("totalPages")
        if isinstance(size, int) and size > points:
            # IG charged more than we counted: count what IG says.
            entry["points"] = size
            self.warn(f"IG sent {size} candles for a request counted as {points} points; counted {size}.")
        self._finish(entries, entry, "replied", size)
        fig = self.ig_figures() or {}
        log.info("History request %s %s to %s: %s candles, %d points counted. IG allowance %s of %s, "
                 "resets %s.", resolution, what["from_utc"], what["to_utc"], size, entry["points"],
                 fig.get("remaining"), fig.get("total"), fig.get("resets_utc"))
        return HistoryReply(list(body.get("prices") or []), entry["points"], size, fig.get("remaining"),
                            fig.get("total"), resets, pages)

    # ---- helpers --------------------------------------------------------------

    @staticmethod
    def _json(r: Any) -> dict:
        try:
            b = r.json()
            return b if isinstance(b, dict) else {}
        except Exception:
            return {}

    def _save_ig_figures(self, allowance: dict) -> datetime | None:
        rem, tot, exp = (allowance.get("remainingAllowance"), allowance.get("totalAllowance"),
                         allowance.get("allowanceExpiry"))
        if rem is None and tot is None and exp is None:
            fig = self.ig_figures()
            return _parse(fig["resets_utc"]) if fig and fig.get("resets_utc") else None
        now = self.now()
        resets = now + timedelta(seconds=int(exp)) if isinstance(exp, (int, float)) else None
        self._write_json(self.allowance_path, {
            "remaining": rem, "total": tot, "resets_utc": _iso(resets) if resets else None,
            "seen_utc": _iso(now)})
        return resets

    def _finish(self, entries: list[dict], entry: dict, status: str, size: int | None) -> None:
        entry["status"] = status
        entry["ig_size"] = size
        entry["finished_utc"] = _iso(self.now())
        self._save_ledger(entries)
        self._write_daily()

    def _refuse(self, check: str, reason: str, points: int, what: dict) -> None:
        msg = f"History request REFUSED by check {check}: {reason}. Nothing was sent."
        self.warn(msg)
        entries = self.ledger()
        entries.append({"counted_utc": _iso(self.now()), "points": points, "status": "refused-by-bot",
                        "check": check, **what})
        self._save_ledger(entries)
        self._write_daily()
        raise (HistoryBlocked if check.startswith("a.") else HistoryRefused)(check, reason)

    def _write_daily(self) -> None:
        days: dict[str, dict] = {}
        for e in self.ledger():
            d = days.setdefault(e["counted_utc"][:10], {"requests_sent": 0, "points_counted": 0,
                                                       "refused_by_bot": 0, "refused_by_ig": 0})
            if e["status"] == "refused-by-bot":
                d["refused_by_bot"] += 1
                continue
            d["requests_sent"] += 1
            d["points_counted"] += e["points"]
            if e["status"] == "refused-by-ig":
                d["refused_by_ig"] += 1
        fig = self.ig_figures() or {}
        old = {}
        if self.daily_path.exists():
            old = {r["date_utc"]: r for r in csv.DictReader(io.StringIO(self.daily_path.read_text()))}
        today = self.now().date().isoformat()
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=DAILY_COLUMNS, lineterminator="\n")
        w.writeheader()
        for date in sorted(days):
            row = {"date_utc": date, **days[date]}
            if date == today:   # IG's figures as last seen on that day
                row.update(ig_remaining=fig.get("remaining"), ig_total=fig.get("total"),
                           ig_resets_utc=fig.get("resets_utc"), updated_utc=_iso(self.now()))
            else:
                prev = old.get(date, {})
                row.update({k: prev.get(k, "") for k in ("ig_remaining", "ig_total", "ig_resets_utc", "updated_utc")})
            w.writerow(row)
        safe_write(self.daily_path, buf.getvalue().encode())
