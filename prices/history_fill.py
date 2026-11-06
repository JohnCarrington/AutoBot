"""Filling gaps from IG's history, and the one-off two-week fill.

All IG history requests go through the history door (ig/history.py), which
checks the block marker, the bot's weekly budget, IG's allowance floor and the
maximum size, counting points before anything is sent.

Rules for filling (docs/PRICES_AND_CANDLES.md):
  * Only gaps the store has RECORDED (data/candles/gaps.csv), 5-minute
    candles, during market hours. Never the weekend.
  * Ask only for the missing candles: each request covers one unbroken run of
    missing 5-minute candles, no bigger than history.max_points_per_request.
  * What comes back only fills missing candles. A stored candle is never
    overwritten; anything outside the request is ignored and reported.
  * IG's own UTC times (snapshotTimeUTC) are used. Buy = IG's ask, sell = IG's bid.

Commands:
  .venv/bin/python -m prices.history_fill plan   shows the one-off plan; contacts nobody
  .venv/bin/python -m prices.history_fill go     runs it (once ever: then it is recorded as done)
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from housekeeping.files import safe_write
from prices.builder import build_due
from prices.calendar import Boundaries, MarketHours, floor_5m
from prices.checks import check_store
from prices.model import FIVE_MIN, UK, Candle, plain, price, uk_short
from prices.store import CandleStore

UTC = timezone.utc
DONE_FILE = "one_off_fill_done.json"


@dataclass
class Planned:
    resolution: str            # "MINUTE_5" or "DAY"
    start: datetime            # first candle start (UTC)
    end: datetime              # last candle start (UTC), inclusive
    points: int                # the most candles this can return
    purpose: str               # "fill", "compare" or "ig-daily"
    slots: list[datetime] = field(default_factory=list)   # the exact 5-minute candles asked for


# ---- reading IG's replies ---------------------------------------------------------

def ig_utc(text: str) -> datetime:
    """IG's snapshotTimeUTC, e.g. '2026-11-04T10:00:00'."""
    return datetime.strptime(text[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=UTC)


def candles_from_ig(rows: list[dict], tf: str, length: timedelta) -> tuple[list[Candle], list[str]]:
    """IG's price rows to candles. Buy = ask, sell = bid. Rows with a missing
    price are not used (never guessed)."""
    out, problems = [], []
    for row in rows:
        try:
            start = ig_utc(row["snapshotTimeUTC"])
            p = {k: row[k] for k in ("openPrice", "highPrice", "lowPrice", "closePrice")}
            out.append(Candle(tf, start, start + length,
                              price(p["openPrice"]["ask"]), price(p["highPrice"]["ask"]),
                              price(p["lowPrice"]["ask"]), price(p["closePrice"]["ask"]),
                              price(p["openPrice"]["bid"]), price(p["highPrice"]["bid"]),
                              price(p["lowPrice"]["bid"]), price(p["closePrice"]["bid"])))
        except (KeyError, TypeError, ValueError) as e:
            problems.append(f"IG row {row.get('snapshotTimeUTC', '?')} not used: {e}")
    return out, problems


# ---- what is missing ------------------------------------------------------------------

def missing_slots(store: CandleStore, hours: MarketHours, start: datetime, end: datetime) -> list[datetime]:
    """5-minute candle starts in [start, end) during market hours with no stored candle."""
    stored = {c.start for c in store.read_range("5m", start, end)}
    return [t for t in hours.open_slots(start, end) if t not in stored]


def runs(slots: list[datetime]) -> list[list[datetime]]:
    """Unbroken runs of 5-minute slots (a weekend always breaks a run)."""
    out: list[list[datetime]] = []
    for t in sorted(slots):
        if out and t - out[-1][-1] == FIVE_MIN:
            out[-1].append(t)
        else:
            out.append([t])
    return out


def chunk(run: list[datetime], max_points: int) -> list[list[datetime]]:
    return [run[i:i + max_points] for i in range(0, len(run), max_points)]


def recorded_gap_ranges(store: CandleStore) -> list[tuple[datetime, datetime]]:
    from prices.model import parse_iso
    return [(parse_iso(r["from_utc"]), parse_iso(r["to_utc"])) for r in store.recorded_gaps()
            if r["timeframe"] == "5m"]


def requests_for_recorded_gaps(store: CandleStore, hours: MarketHours, max_points: int,
                               within: tuple[datetime, datetime] | None = None) -> list[Planned]:
    """Requests for the 5-minute candles still missing inside RECORDED gaps,
    during market hours only, one unbroken run at a time, each no bigger than
    max_points."""
    slots: set[datetime] = set()
    for s, e in recorded_gap_ranges(store):
        if within:
            s, e = max(s, within[0]), min(e, within[1])
        if s < e:
            slots.update(missing_slots(store, hours, s, e))
    out = []
    for run in runs(sorted(slots)):
        for part in chunk(run, max_points):
            out.append(Planned("MINUTE_5", part[0], part[-1], len(part), "fill", part))
    return out


def apply_fill(store: CandleStore, req: Planned, candles: list[Candle]) -> dict:
    """Store what came back, but only into the missing candles asked for."""
    wanted = set(req.slots)
    result = {"stored": 0, "already_stored": 0, "not_asked_for": 0, "not_asked_times": []}
    for c in candles:
        if c.start not in wanted:
            result["not_asked_for"] += 1
            result["not_asked_times"].append(c.start)
            continue
        if store.get("5m", c.start) is not None:
            result["already_stored"] += 1      # never overwritten
            continue
        if store.add(c) == "stored":
            result["stored"] += 1
    return result


# ---- the one-off fill ---------------------------------------------------------------

def fill_period(hours: MarketHours, now: datetime) -> tuple[datetime, datetime]:
    """The last two trading weeks: from the Sunday open a week before this
    week's (or the last) open, up to now or this week's close."""
    open_now, close_now = hours.session(now)
    start = hours.session(open_now - timedelta(days=1))[0]
    end = min(floor_5m(now), close_now)
    return start, end


def plan_one_off(store: CandleStore, hours: MarketHours, max_points: int, now: datetime) -> list[Planned]:
    start, end = fill_period(hours, now)
    plan: list[Planned] = []
    # 1. IG's own daily candles for the same two weeks (small: also tells us IG's allowance).
    d0 = datetime(start.year, start.month, start.day, tzinfo=UTC)
    d1 = datetime(end.year, end.month, end.day, tzinfo=UTC)
    plan.append(Planned("DAY", d0, d1 + timedelta(hours=23, minutes=59), (d1 - d0).days + 1, "ig-daily"))
    # 2. The live candles already stored (Stage 4a), asked for once to compare only.
    stored = [c.start for c in store.read_range("5m", start, end)]
    for run in runs(stored):
        for part in chunk(run, max_points):
            plan.append(Planned("MINUTE_5", part[0], part[-1], len(part), "compare", part))
    # 3. Every missing 5-minute candle during market hours.
    for run in runs(missing_slots(store, hours, start, end)):
        for part in chunk(run, max_points):
            plan.append(Planned("MINUTE_5", part[0], part[-1], len(part), "fill", part))
    return plan


def show_plan(plan: list[Planned], door: Any, settings: Any, period: tuple[datetime, datetime],
              say: Callable[[str], None]) -> None:
    total = sum(p.points for p in plan)
    say(f"ONE-OFF FILL PLAN for {settings.market.epic}")
    say(f"  Period: {uk_short(period[0])} to {uk_short(period[1])} (UK time)")
    say(f"  {'#':>2}  {'what':<9} {'resolution':<9} {'from (UK)':<20} {'to (UK)':<20} {'points':>6}")
    for i, p in enumerate(plan, 1):
        say(f"  {i:>2}  {p.purpose:<9} {p.resolution:<9} {uk_short(p.start):<20} {uk_short(p.end):<20} {p.points:>6}")
    fills = [p for p in plan if p.purpose == "fill"]
    say(f"  Requests: {len(plan)} ({len(fills)} fill, {sum(p.purpose == 'compare' for p in plan)} compare, "
        f"{sum(p.purpose == 'ig-daily' for p in plan)} IG daily)")
    say(f"  Points in total (most IG could charge): {total}  "
        f"(5-minute candles to fill: {sum(p.points for p in fills)})")
    say(f"  Largest request: {max(p.points for p in plan)} points (maximum allowed {settings.history.max_points_per_request})")
    used = door.points_last_7_days()
    say(f"  Bot's weekly budget: {settings.history.weekly_budget_points}; used in last 7 days: {used}; "
        f"left after the fill: {settings.history.weekly_budget_points - used - total}")
    fig = door.ig_figures()
    if fig:
        say(f"  IG's remaining allowance (last reported {fig['seen_utc']}): {fig['remaining']} of {fig['total']}; "
            f"after the fill: about {fig['remaining'] - total}")
    else:
        say("  IG's remaining allowance: NOT KNOWN. IG only reports it in the reply to a history request, "
            "and none has ever been made. The first request (IG daily candles) will show it; every later "
            f"request is refused if it would take IG's remaining allowance below {settings.history.min_ig_allowance_remaining}.")
    blocked = door.block_in_place()
    say(f"  Block marker: {blocked or 'none'}")


@dataclass
class FillResult:
    allowance_before: dict | None = None
    allowance_after: dict | None = None
    stored: int = 0
    compare_rows: list = field(default_factory=list)
    ig_daily: list = field(default_factory=list)
    notes: list = field(default_factory=list)


def run_one_off(door: Any, store: CandleStore, settings: Any, now: datetime,
                say: Callable[[str], None], pause: Callable[[float], None] = lambda s: None) -> FillResult:
    hfolder = Path(settings.history.folder)
    done = hfolder / DONE_FILE
    if done.exists():
        raise RuntimeError(f"The one-off fill has already been run ({done}). It never runs again by itself.")
    hours = MarketHours(settings.market_hours)
    b = Boundaries(settings.candles, hours)
    period = fill_period(hours, now)
    plan = plan_one_off(store, hours, settings.history.max_points_per_request, now)
    safe_write(done, (json.dumps({"status": "started", "started_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                   "period_utc": [str(period[0]), str(period[1])]}, indent=1) + "\n").encode())
    res = FillResult(allowance_before=door.ig_figures())

    # Rule: only gaps the store has recorded. Record the missing two weeks first.
    for run in runs(missing_slots(store, hours, *period)):
        covered = any(s <= run[0] and run[-1] + FIVE_MIN <= e for s, e in recorded_gap_ranges(store))
        if not covered:
            store.record_gap("5m", run[0], run[-1] + FIVE_MIN, len(run), now,
                             "before the one-off history fill")
    fills = requests_for_recorded_gaps(store, hours, settings.history.max_points_per_request, within=period)
    assert [(p.start, p.end) for p in fills] == [(p.start, p.end) for p in plan if p.purpose == "fill"], \
        "the requests for recorded gaps differ from the plan"

    for n, p in enumerate(plan, 1):
        if n > 1:
            pause(2)
        if p.purpose == "ig-daily":
            reply = door.fetch(settings.market.epic, "DAY", p.start, p.end, p.points,
                               "IG daily candles to compare boundaries")
            if res.allowance_before is None:
                res.allowance_before = {"remaining": (reply.remaining or 0) + reply.points_counted,
                                        "total": reply.total, "note": "worked out from the first reply"}
            daily, problems = candles_from_ig(reply.rows, "1d", timedelta(days=1))
            res.ig_daily = daily
            res.notes += problems
            say(f"  {n}. IG daily candles: {len(daily)} received; IG allowance now {reply.remaining} of {reply.total}")
            continue
        reply = door.fetch(settings.market.epic, "MINUTE_5", p.start, p.end, p.points,
                           f"one-off fill: {p.purpose}")
        got, problems = candles_from_ig(reply.rows, "5m", FIVE_MIN)
        res.notes += problems
        outside = [c.start for c in got if not p.start <= c.start <= p.end]
        if outside:
            raise RuntimeError(f"IG sent candles outside the requested times ({uk_short(min(outside))} ...): "
                               "the times do not line up. Stopping the fill.")
        if reply.pages and reply.pages > 1:
            res.notes.append(f"Request {n}: IG said there are {reply.pages} pages; only the first was used.")
        if p.purpose == "compare":
            for c in got:
                live = store.get("5m", c.start)
                res.compare_rows.append((live, c))
            say(f"  {n}. compare: {len(got)} candles received for {len(p.slots)} stored live candles")
            continue
        r = apply_fill(store, p, got)
        res.stored += r["stored"]
        say(f"  {n}. fill {uk_short(p.start)} to {uk_short(p.end)}: asked {p.points}, received {len(got)}, "
            f"stored {r['stored']}, already stored {r['already_stored']}, not asked for {r['not_asked_for']}; "
            f"IG allowance now {reply.remaining} of {reply.total}")
    res.allowance_after = door.ig_figures()
    safe_write(done, (json.dumps({"status": "done", "started_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                   "finished_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                   "period_utc": [str(period[0]), str(period[1])],
                                   "candles_stored": res.stored}, indent=1) + "\n").encode())
    _save_ig_daily(hfolder / "ig_daily_candles.csv", res.ig_daily)
    return res


def _save_ig_daily(path: Path, daily: list[Candle]) -> None:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["start_utc", "buy_open", "buy_high", "buy_low", "buy_close",
                "sell_open", "sell_high", "sell_low", "sell_close"])
    for c in daily:
        w.writerow([c.start.strftime("%Y-%m-%dT%H:%M:%SZ"), *(plain(x) for x in c.prices())])
    safe_write(path, buf.getvalue().encode())


# ---- the checks after the fill ----------------------------------------------------------

def report_after(res: FillResult, store: CandleStore, settings: Any, say: Callable[[str], None]) -> bool:
    """Step 6. Returns False if IG's daily boundaries differ from ours."""
    hours = MarketHours(settings.market_hours)
    b = Boundaries(settings.candles, hours)
    say("")
    say("A. FILLED CANDLES vs LIVE CANDLES (Stage 4a), same 5-minute slots:")
    same = 0
    for live, hist in res.compare_rows:
        if live is None:
            say(f"  {uk_short(hist.start)}: no live candle stored at this time (IG's time does not line up)")
            continue
        if live.prices() == hist.prices():
            same += 1
            say(f"  {uk_short(live.start)}: identical (all 8 prices)")
        else:
            diffs = [f"{f} live {plain(a)} history {plain(c)}" for f, a, c in
                     zip(("buy_open", "buy_high", "buy_low", "buy_close", "sell_open", "sell_high", "sell_low",
                          "sell_close"), live.prices(), hist.prices()) if a != c]
            say(f"  {uk_short(live.start)}: DIFFERENT: " + "; ".join(diffs))
    say(f"  {same} of {len(res.compare_rows)} identical")

    built = build_due(store, b, datetime.now(UTC), settings.candles.wait_for_late_candle_seconds,
                      lambda m: res.notes.append(m))
    ours = {c.start: c for c in store.read_range("1d", res.ig_daily[0].start - timedelta(days=3),
                                                  datetime.now(UTC))} if res.ig_daily else {}
    say("")
    say(f"B. IG's DAILY CANDLES vs THE BOT's DAILY CANDLES ({len(built)} bigger candles built from the 5-minute candles)")
    say(f"  {'IG start (UTC)':<18} {'= UK time':<20} {'weekday':<8} {'our daily at same start?':<26}")
    match_all = True
    for c in res.ig_daily:
        mine = ours.get(c.start)
        if mine is None:
            match_all = False
            note = "NO"
        elif mine.prices() == c.prices():
            note = "yes, all 8 prices equal"
        else:
            note = "yes, prices differ: " + ", ".join(
                f"{f} {plain(a)}/{plain(x)}" for f, a, x in zip(("bo", "bh", "bl", "bc", "so", "sh", "sl", "sc"),
                                                              c.prices(), mine.prices()) if a != x)
        say(f"  {c.start.strftime('%Y-%m-%d %H:%M'):<18} {uk_short(c.start):<20} "
            f"{c.start.astimezone(UK).strftime('%A'):<8} {note}")
    sundays = [c for c in res.ig_daily if c.start.astimezone(UK).weekday() == 6 or
               (c.start + timedelta(hours=12)).astimezone(UK).weekday() == 6]
    say(f"  IG has a separate Sunday daily candle: {'YES' if sundays else 'NO'}"
        + (f" ({', '.join(uk_short(c.start) for c in sundays)})" if sundays else ""))
    say("  Our daily candles in the same period:")
    for s, c in sorted(ours.items()):
        say(f"    {uk_short(c.start)} to {uk_short(c.end)}  parts {c.parts}/{c.expected_parts}  "
            f"buy O {plain(c.buy_open)} C {plain(c.buy_close)} | sell O {plain(c.sell_open)} C {plain(c.sell_close)}")
    say(f"  Daily boundaries match IG's: {'YES' if match_all else 'NO'}")

    say("")
    r = check_store(store, b)
    say(f"C. STORE CHECKS ON EVERYTHING: {sum(r.candles.values())} candles "
        f"({', '.join(f'{tf} {n}' for tf, n in r.candles.items())}); {len(r.problems)} problem(s); "
        f"{len(r.gaps)} gap(s), {len(r.new_gaps)} not yet recorded")
    for p in r.problems:
        say("    " + p)
    for g in r.gaps:
        say("    " + g.describe() + (" (recorded)" if g.known else " (NEW)"))
        if not g.known:
            store.record_gap(g.timeframe, g.start, g.end, g.missing, datetime.now(UTC), "store check after the fill")
    for n in res.notes:
        say("  note: " + n)
    return match_all


# ---- command line --------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    from config.settings_loader import load_or_exit
    from housekeeping.logs import setup_logging
    from ig.history import HistoryDoor

    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["plan", "go"])
    args = ap.parse_args(argv)
    settings = load_or_exit()
    setup_logging(settings.housekeeping, "history", console=False)
    store = CandleStore(settings.candles.folder, settings.candles.compress_after_days)
    hours = MarketHours(settings.market_hours)
    now = datetime.now(UTC)
    say = lambda t="": print(t, flush=True)  # noqa: E731

    if args.action == "plan":
        # Contacts nobody: no login, no IG call.
        door = HistoryDoor(None, settings.history)
        if (Path(settings.history.folder) / DONE_FILE).exists():
            say("The one-off fill has already been run; it will not run again.")
            return 0
        plan = plan_one_off(store, hours, settings.history.max_points_per_request, now)
        show_plan(plan, door, settings, fill_period(hours, now), say)
        return 0

    from ig.client import IGClient
    from ig.errors import IGLoginFailure, stop_bot
    from ig.secrets import ENV_PATH, load_credentials
    import time

    client = IGClient(settings.ig, load_credentials(ENV_PATH))
    door = HistoryDoor(client, settings.history)
    say(f"One-off history fill, started {now.astimezone(UK).strftime('%a %d %b %Y %H:%M:%S %Z')}")
    try:
        client.connect()
        res = run_one_off(door, store, settings, now, say, pause=time.sleep)
    except IGLoginFailure as f:
        client.logout()
        stop_bot(f)
    except Exception as e:
        client.logout()
        say(f"FILL STOPPED: {type(e).__name__}: {e}")
        _calls(client, say)
        return 2
    client.logout()
    say("")
    say(f"IG ALLOWANCE BEFORE: {res.allowance_before}")
    say(f"IG ALLOWANCE AFTER:  {res.allowance_after}")
    say(f"5-minute candles stored by the fill: {res.stored}")
    ok = report_after(res, store, settings, say)
    _calls(client, say)
    return 0 if ok else 3


def _calls(client: Any, say: Callable[[str], None]) -> None:
    from collections import Counter
    from ig.client import is_historical_prices_path
    c = Counter(f"{x.method} {x.path.split('?')[0]}" + (f" -> {x.status}" if x.status != 200 else "")
                for x in client.calls)
    say(f"IG CALLS MADE: {len(client.calls)} "
        f"(history requests: {sum(1 for x in client.calls if is_historical_prices_path(x.path))})")
    for k, n in c.items():
        say(f"  {k:<50} {n}")


if __name__ == "__main__":
    sys.exit(main())
