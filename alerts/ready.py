"""The "ready" messages, run by the price service.

SUNDAY: when every pair switched on has stored its first 5-minute candle of the
week after the Sunday reopen (within alerts.sunday_ready_within_minutes of it).
DAILY: at alerts.daily_ready_at (06:00 UK), Monday to Friday.

The checks (both messages):
  1. logged in to IG (the bot's account active);
  2. the price stream connected;
  3. for each pair switched on: candles arriving (its newest 5-minute candle
     finished within alerts.candles_arriving_within_minutes; on Sunday, from
     this week's reopen);
  4. for each pair: the candle store checks passed (no problem, no gap not yet recorded);
  5. IG's remaining history allowance, as IG last reported it: known, above the
     floor (history.min_ig_allowance_remaining), and no block marker.
DAILY also, for each pair: that day's pivot, S1 to S3 and R1 to R3, and the
analyser's direction, and a check that the analyser's data is ready.

If every check passes, the ready message is sent. If any fails, a problem alert
is sent INSTEAD, naming each check that failed. Each message is sent once
(<alerts folder>/ready.json remembers which day and which week were done).
Nothing here contacts IG: it reads the bot's own state and files.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from housekeeping.files import safe_write
from levels.rules import PIVOT, R1, R2, R3, S1, S2, S3
from prices.calendar import Boundaries, MarketHours
from prices.checks import check_store
from prices.model import UK, plain, uk_short

log = logging.getLogger("autobot.alerts.ready")
UTC = timezone.utc
STATE_FILE = "ready.json"
LEVEL_ORDER = (R3, R2, R1, PIVOT, S1, S2, S3)


@dataclass
class Check:
    name: str
    ok: bool
    detail: str

    def line(self) -> str:
        return f"{'OK  ' if self.ok else 'FAIL'} {self.name}: {self.detail}"


@dataclass
class ReadyContext:
    """What the checks look at: the running price service's own objects."""
    settings: Any                    # the plain settings (with switches)
    client: Any                      # the IG client (account_active)
    stream: Any                      # the price stream (connected_since, stopped)
    feeds: dict                      # pair -> its PriceFeed (feed.settings is that pair's settings)
    history_door: Any                # a HistoryDoor (ig_figures, block_in_place); never sends anything here


def run_checks(ctx: ReadyContext, now: datetime, since: datetime | None = None) -> list[Check]:
    a = ctx.settings.alerts
    out = [Check("Logged in to IG", bool(getattr(ctx.client, "account_active", False)),
                 "the bot's account is active" if getattr(ctx.client, "account_active", False) else "not logged in")]
    st = ctx.stream
    connected = st is not None and getattr(st, "connected_since", None) is not None and not st.stopped
    out.append(Check("Price stream connected", connected,
                     f"since {uk_short(st.connected_since)}" if connected else "not connected"))
    within = timedelta(minutes=a.candles_arriving_within_minutes)
    for pair, feed in ctx.feeds.items():
        newest = feed.store.newest("5m")
        if newest is None:
            out.append(Check(f"{pair} candles arriving", False, "no 5-minute candle stored"))
        elif since is not None and newest.start < since:
            out.append(Check(f"{pair} candles arriving", False,
                             f"no candle since the reopen at {uk_short(since)} (newest {uk_short(newest.start)})"))
        elif now - newest.end > within:
            out.append(Check(f"{pair} candles arriving", False,
                             f"newest 5-minute candle finished {uk_short(newest.end)}, more than "
                             f"{a.candles_arriving_within_minutes} minutes ago"))
        else:
            out.append(Check(f"{pair} candles arriving", True, f"newest 5-minute candle {uk_short(newest.start)}"))
        b = Boundaries(feed.settings.candles, MarketHours(feed.settings.market_hours))
        chk = check_store(feed.store, b)
        n = sum(chk.candles.values())
        ok = not chk.problems and not chk.new_gaps
        detail = (f"{n} candles, 0 problems" if ok else
                  f"{len(chk.problems)} problem(s), {len(chk.new_gaps)} gap(s) not recorded"
                  + (f"; first: {(chk.problems or [g.describe() for g in chk.new_gaps])[0]}"))
        out.append(Check(f"{pair} candle store checks", ok, detail))
    h = ctx.settings.history
    fig = ctx.history_door.ig_figures() or {}
    blocked = ctx.history_door.block_in_place()
    rem = fig.get("remaining")
    if blocked:
        out.append(Check("IG history allowance", False, f"BLOCKED: {blocked}"))
    elif rem is None:
        out.append(Check("IG history allowance", False, "not known (IG has never reported it)"))
    else:
        out.append(Check("IG history allowance", rem >= h.min_ig_allowance_remaining,
                         f"{rem} of {fig.get('total')} left (floor {h.min_ig_allowance_remaining}; "
                         f"last reported {fig.get('seen_utc', '?')[:16].replace('T', ' ')} UTC; "
                         f"IG resets {fig.get('resets_utc', '?')[:16].replace('T', ' ')} UTC)"))
    return out


def pair_day_lines(ctx: ReadyContext, now: datetime) -> tuple[list[str], list[Check]]:
    """For the daily message: each pair's pivot, S1-S3, R1-R3 and the analyser's direction."""
    from analyser.report import analyse
    from levels.current import build
    lines, checks = [], []
    for pair, feed in ctx.feeds.items():
        ps = feed.settings
        ll = build(ps, feed.store, now)
        piv = {lv.type: lv.price for lv in ll.levels if lv.type in LEVEL_ORDER}
        if len(piv) == len(LEVEL_ORDER):
            lines.append(f"{pair} levels: " + ", ".join(f"{'Pivot' if t == PIVOT else t} {plain(piv[t])}"
                                                         for t in LEVEL_ORDER))
        else:
            checks.append(Check(f"{pair} daily pivots", False, "; ".join(ll.warnings) or "not worked out"))
        r = analyse(ps, feed.store, now)
        d = r.direction
        lines.append(f"{pair} direction: {d.side} ({d.reason})")
        checks.append(Check(f"{pair} analyser data", r.data.state == "ready", r.data.describe()))
    return lines, checks


class ReadyAlerts:
    def __init__(self, settings: Any, alerts: Any, context: Callable[[], ReadyContext],
                 now: Callable[[], datetime] = lambda: datetime.now(UTC)):
        self.s = settings
        self.a = settings.alerts
        self.alerts = alerts
        self.context = context
        self.now = now
        self.hours = MarketHours(settings.market_hours)
        self.path = Path(self.a.folder) / STATE_FILE

    def _state(self) -> dict:
        try:
            return json.loads(self.path.read_text())
        except (FileNotFoundError, ValueError):
            return {}

    def _mark(self, **values: str) -> None:
        state = {**self._state(), **values}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        safe_write(self.path, (json.dumps(state, indent=1) + "\n").encode())

    def tick(self) -> None:
        """Called about once a second by the price service. Never raises."""
        try:
            now = self.now()
            self._sunday(now)
            self._daily(now)
        except Exception as e:      # the ready messages must never stop the price service
            log.warning("Ready message check failed: %s: %s", type(e).__name__, e)

    # ---- Sunday ---------------------------------------------------------------------------

    def _sunday(self, now: datetime) -> None:
        opened, closes = self.hours.session(now)
        if not opened <= now < closes:
            return
        key = opened.strftime("%Y-%m-%dT%H:%MZ")
        if self._state().get("sunday") == key:
            return
        late = now - opened > timedelta(minutes=self.a.sunday_ready_within_minutes)
        ctx = self.context()
        arrived = all(c is not None and c.start >= opened for c in (f.store.newest("5m") for f in ctx.feeds.values()))
        if arrived and late:
            # the price service started after the window: these are not "the first candles of the week"
            self._mark(sunday=key)
            log.info("Sunday ready message for %s not sent: the price service started more than %d minutes "
                     "after the reopen.", uk_short(opened), self.a.sunday_ready_within_minutes)
            return
        if not arrived and not late:
            return                    # still waiting for each pair's first candle of the week
        # every pair's first candle has arrived in time (ready, if the checks pass),
        # or the time is up and a pair has none (the candles check fails: a problem alert)
        self._mark(sunday=key)
        self._send("week", f"Sunday reopen {uk_short(opened)}", run_checks(ctx, now, since=opened), [])

    # ---- daily -----------------------------------------------------------------------------

    def _daily(self, now: datetime) -> None:
        uk = now.astimezone(UK)
        if uk.weekday() > 4:
            return
        at = uk.replace(hour=self.a.daily_ready_at.hour, minute=self.a.daily_ready_at.minute, second=0, microsecond=0)
        if uk < at:
            return
        day = uk.date().isoformat()
        if self._state().get("daily") == day:
            return
        self._mark(daily=day)
        if uk - at > timedelta(minutes=self.a.daily_ready_late_by_minutes):
            log.info("Daily ready message for %s not sent: the price service started after %s.", day,
                     (at + timedelta(minutes=self.a.daily_ready_late_by_minutes)).strftime("%H:%M"))
            return
        ctx = self.context()
        checks = run_checks(ctx, now)
        lines, more = pair_day_lines(ctx, now)
        self._send("day", uk.strftime("%a %d %b %Y"), checks + more, lines)

    # ---- sending -------------------------------------------------------------------------

    def _send(self, which: str, when: str, checks: list[Check], extra: list[str]) -> None:
        failed = [c for c in checks if not c.ok]
        if failed:
            text = (f"{'Sunday' if which == 'week' else 'Daily'} ready checks FAILED ({when}): "
                    + "; ".join(f"{c.name}: {c.detail}" for c in failed)
                    + "\n" + "\n".join(c.line() for c in checks))
            self.alerts.problem(f"ready-{which}", text)
            return
        head = "AutoBot READY for the week" if which == "week" else "AutoBot READY for the day"
        self.alerts.info("\n".join([f"{head} ({when})", *(c.line() for c in checks), *extra]))
