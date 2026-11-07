"""The one-off LONG history fill for a pair (owner's instruction, 7 November 2026):
IG's own weekly candles for the last 4 years, daily candles for the last 2
years and hourly candles for the last 3 months, buy and sell prices.

Three steps, each run by hand, each only with the owner's go-ahead:

  .venv/bin/python -m prices.long_history plan --pair GBPUSD
      The requests, points, the shared weekly budget and IG's allowance before
      and after. Contacts nobody.
  .venv/bin/python -m prices.long_history go --pair GBPUSD
      Sends the requests through the history door (ig/history.py: block marker,
      weekly budget, IG's allowance floor, size limit, points counted first).
      IG's candles are kept in a HOLDING folder, <candles folder>/<PAIR>/ig_history/,
      which no part of the bot reads. Then IG's candles are compared with the
      bot's own candles for the same periods (weekly first, the same way the
      daily ones were checked on 6 November): start label and all 8 prices.
      Nothing is used yet.
  .venv/bin/python -m prices.long_history prove --pair GBPUSD
      One small hourly request in UK summer time (3 points), to prove IG's
      times line up with the request now that the door sends UK time.
  .venv/bin/python -m prices.long_history store --pair GBPUSD
      After the owner has seen the comparison: copies IG's candles into the
      pair's store. A candle already stored is never overwritten (the bot's own
      candle is kept). An IG candle whose start is not on the bot's boundaries is
      not stored, and is reported. Then the rebuild rule is applied, the store
      checked, and any new gap recorded.

IG's own candles are stored with parts 0 and expected_parts 0, meaning "IG's
candle, not built by the bot", so the rebuild rule never touches them.

Every reply is SAVED as IG sent it (<history folder>/<PAIR>/long_history_replies/)
BEFORE it is checked, so a reply that fails a check is never lost. "go" can be
run again after a stop: a request whose candles are already in the holding
folder is not sent again.

IG labels its weekly candles Monday 00:00 UK; the bot labels the same week
Sunday 00:00 UK (its week holds the Sunday evening). On 7 November 2026 both
overlapping weeks had all 8 prices equal, so IG's weeks are compared and stored
under the bot's Sunday 00:00 UK label (owner's decision, 7 November 2026).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from config.pairs import check_same_pair
from housekeeping.files import safe_write
from prices.builder import rebuild_incomplete
from prices.calendar import Boundaries, MarketHours
from prices.checks import check_store
from prices.history_fill import Planned, candles_from_ig, chunk
from prices.model import UK, Candle, plain, uk_short
from prices.store import CandleStore

UTC = timezone.utc
# The periods the owner asked for on 7 November 2026 (a one-off: not settings).
PERIODS = (("1w", "WEEK", {"years": 4}), ("1d", "DAY", {"years": 2}), ("1h", "HOUR", {"months": 3}))
NOMINAL = {"1w": timedelta(days=7), "1d": timedelta(days=1), "1h": timedelta(hours=1)}
HOLDING = "ig_history"
DONE_FILE = "long_history.json"
FIELDS = ("bo", "bh", "bl", "bc", "so", "sh", "sl", "sc")


def back(now: datetime, years: int = 0, months: int = 0) -> datetime:
    m = now.month - 1 - months
    y = now.year - years + m // 12
    m = m % 12 + 1
    day = min(now.day, 28)
    return now.replace(year=y, month=m, day=day, hour=0, minute=0, second=0, microsecond=0)


def to_bot_label(b: Boundaries, tf: str, c: Candle) -> Candle:
    """IG's weekly candle labelled Monday 00:00 UK -> the bot's label, Sunday 00:00 UK
    (prices unchanged). Any other candle is returned as it is."""
    uk = c.start.astimezone(UK)
    if tf != "1w" or b.is_on_boundary(tf, c.start) or (uk.weekday(), uk.hour, uk.minute) != (0, 0, 0):
        return c
    start = (uk - timedelta(days=1)).astimezone(UTC)        # wall-clock: Sunday 00:00 UK, GMT or BST
    if not b.is_on_boundary(tf, start):
        return c
    end = b.bucket(tf, max(start, b.hours.next_open(start)))[1]
    return Candle(tf, start, end, *c.prices(), c.parts, c.expected_parts)


def finished_buckets(b: Boundaries, tf: str, start: datetime, now: datetime) -> list[tuple[datetime, datetime]]:
    """Every candle period of size tf from start to now that has market hours in it and has ended."""
    out, t = [], start
    while t < now:
        s, e = b.regular(tf, t)
        if s >= start and b.expected_parts(s, e) > 0:
            bs, be = b.bucket(tf, max(s, b.hours.next_open(s)))
            if be <= now:
                out.append((bs, be))
        t = e
    return sorted(set(out))


def plan(settings: Any, now: datetime) -> list[Planned]:
    b = Boundaries(settings.candles, MarketHours(settings.market_hours))
    out: list[Planned] = []
    for tf, resolution, ago in PERIODS:
        buckets = finished_buckets(b, tf, back(now, **ago), now)
        for part in chunk(buckets, settings.history.max_points_per_request):
            # ask up to just before the end of the last period, so a different IG label is still inside
            out.append(Planned(resolution, part[0][0], part[-1][1] - timedelta(minutes=1), len(part),
                               f"ig-{tf}", [s for s, _ in part]))
    return out


def holding(settings: Any) -> CandleStore:
    return CandleStore(Path(settings.candles.folder) / HOLDING, 10 ** 6, warn=lambda m: None)


def _status(settings: Any) -> dict:
    p = Path(settings.history.pair_folder) / DONE_FILE
    return json.loads(p.read_text()) if p.exists() else {}


def _set_status(settings: Any, **values: Any) -> None:
    p = Path(settings.history.pair_folder) / DONE_FILE
    data = {**_status(settings), **values}
    p.parent.mkdir(parents=True, exist_ok=True)
    safe_write(p, (json.dumps(data, indent=1) + "\n").encode())


def _when(t: datetime) -> str:
    return t.astimezone(UK).strftime("%a %d %b %Y %H:%M %Z")


def show_plan(settings: Any, door: Any, reqs: list[Planned], now: datetime, say: Callable[[str], None]) -> bool:
    """Prints the plan. Returns True if every request would pass the door's checks."""
    h = settings.history
    say(f"LONG HISTORY FILL PLAN for {settings.market.pair} ({settings.market.epic}), worked out {uk_short(now)}")
    say(f"  {'#':>2}  {'IG resolution':<13} {'from (UK)':<25} {'to (UK)':<25} {'points':>6}")
    for i, p in enumerate(reqs, 1):
        say(f"  {i:>2}  {p.resolution:<13} {_when(p.start):<25} {_when(p.end):<25} {p.points:>6}")
    store = CandleStore(settings.candles.folder, settings.candles.compress_after_days)
    for tf, resolution, ago in PERIODS:
        mine = [p for p in reqs if p.purpose == f"ig-{tf}"]
        if not mine:
            continue                       # nothing left to send for this size
        n = sum(p.points for p in mine)
        have = sum(1 for p in mine for s in p.slots if store.get(tf, s) is not None)
        say(f"  {tf}: {n} candles, {_when(mine[0].slots[0])} to {_when(mine[-1].slots[-1])}, in {len(mine)} request(s); "
            f"{have} of them the bot already has (kept; IG's used only to compare)")
    total = sum(p.points for p in reqs)
    used = door.points_last_7_days(now)
    fig = door.ig_figures() or {}
    rem = fig.get("remaining")
    say(f"  Requests: {len(reqs)}. Points in total (the most IG could charge): {total}. "
        f"Largest request: {max(p.points for p in reqs)} (maximum {h.max_points_per_request}).")
    say(f"  Bot's weekly budget (all pairs): {h.weekly_budget_points}; used in the last 7 days: {used}; "
        f"left now {h.weekly_budget_points - used}; left after: {h.weekly_budget_points - used - total}")
    if rem is not None:
        say(f"  IG's remaining allowance (last reported {fig.get('seen_utc')}): {rem} of {fig.get('total')}; "
            f"after: about {rem - total}; floor {h.min_ig_allowance_remaining}; IG resets {fig.get('resets_utc')}")
    blocked = door.block_in_place()
    say(f"  Block marker: {blocked or 'none'}")
    ok = (used + total <= h.weekly_budget_points and not blocked
          and (rem is None or rem - total >= h.min_ig_allowance_remaining))
    say(f"  Every request passes the door's checks: {'YES' if ok else 'NO'}")
    return ok


# ---- go: fetch into the holding folder, then compare ---------------------------------------

def replies_folder(settings: Any) -> Path:
    return Path(settings.history.pair_folder) / "long_history_replies"


def save_reply(settings: Any, n: int, p: Planned, reply: Any, now: datetime) -> Path:
    """Keep IG's reply exactly as sent, before any check."""
    path = replies_folder(settings) / f"{n:02d}_{p.resolution}_{p.start:%Y%m%dT%H%MZ}_{now:%Y%m%dT%H%M%SZ}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"request": {"resolution": p.resolution, "from_utc": p.start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "to_utc": p.end.strftime("%Y-%m-%dT%H:%M:%SZ"), "points": p.points, "purpose": p.purpose},
            "points_counted": reply.points_counted, "ig_remaining": reply.remaining, "ig_total": reply.total,
            "pages": reply.pages, "rows": reply.rows}
    safe_write(path, (json.dumps(data, indent=1) + "\n").encode())
    return path


def already_held(settings: Any, p: Planned) -> bool:
    """True if this request's candles are already in the holding folder (it is not sent again)."""
    tf = p.purpose.removeprefix("ig-")
    return bool(holding(settings).read_range(tf, p.start, p.end + timedelta(minutes=1)))


def fetch(door: Any, settings: Any, reqs: list[Planned], say: Callable[[str], None],
          pause: Callable[[float], None] = lambda s: None,
          now: Callable[[], datetime] = lambda: datetime.now(UTC)) -> dict[str, list[Candle]]:
    b = Boundaries(settings.candles, MarketHours(settings.market_hours))
    hold = holding(settings)
    got: dict[str, list[Candle]] = {tf: [] for tf, _, _ in PERIODS}
    sent = 0
    for n, p in enumerate(reqs, 1):
        tf = p.purpose.removeprefix("ig-")
        if already_held(settings, p):
            held = hold.read_range(tf, p.start, p.end + timedelta(minutes=1))
            got[tf] += held
            say(f"  {n}. {p.resolution} {uk_short(p.start)} to {uk_short(p.end)}: already in the holding folder "
                f"({len(held)} candles); not sent again")
            continue
        if sent:
            pause(2)
        sent += 1
        reply = door.fetch(settings.market.epic, p.resolution, p.start, p.end, p.points, f"long history {tf}")
        saved = save_reply(settings, n, p, reply, now())                 # kept BEFORE any check
        candles, problems = candles_from_ig(reply.rows, tf, NOMINAL[tf])
        out = []
        for c in candles:
            end = b.bucket(tf, c.start)[1] if b.is_on_boundary(tf, c.start) else c.start + NOMINAL[tf]
            out.append(Candle(tf, c.start, end, *c.prices(), 0, 0))     # parts 0/0: IG's own candle
        outside = [c.start for c in out if not p.start <= c.start <= p.end]
        if outside:
            raise RuntimeError(f"IG sent {tf} candles outside the requested times ({uk_short(min(outside))} ...). "
                               f"Stopping. The reply is kept in {saved}.")
        for c in out:
            hold.add(c)
        got[tf] += out
        say(f"  {n}. {p.resolution} {uk_short(p.start)} to {uk_short(p.end)}: asked {p.points}, received "
            f"{len(out)}, IG allowance now {reply.remaining} of {reply.total}"
            + (f"; {len(problems)} row(s) not used" if problems else ""))
        for x in problems:
            say(f"     {x}")
        if reply.pages and reply.pages > 1:
            say(f"     IG said there are {reply.pages} pages; only the first was used.")
    return got


def compare(settings: Any, tf: str, ig: list[Candle], say: Callable[[str], None]) -> dict:
    """IG's candles against the bot's own of the same size, for every bot candle in IG's period:
    same start label? all 8 prices equal?"""
    store = CandleStore(settings.candles.folder, settings.candles.compress_after_days)
    b = Boundaries(settings.candles, MarketHours(settings.market_hours))
    if not ig:
        say(f"  {tf}: IG sent none.")
        return {"tf": tf, "compared": 0, "same_label": 0, "equal": 0, "off_boundary": 0}
    relabelled = sum(1 for c in ig if to_bot_label(b, tf, c) is not c)
    ig = [to_bot_label(b, tf, c) for c in ig]
    if relabelled:
        say(f"  {tf}: {relabelled} of IG's candles labelled Monday 00:00 UK are compared under the bot's label, "
            "Sunday 00:00 UK")
    first, last = min(c.start for c in ig), max(c.end for c in ig)
    by_start = {c.start: c for c in ig}
    mine = [c for c in store.read_range(tf, first, last)]
    off = [c for c in ig if not b.is_on_boundary(tf, c.start)]
    labels = sorted({(c.start.astimezone(UK).strftime("%A %H:%M")) for c in ig})
    res = {"tf": tf, "compared": len(mine), "same_label": 0, "equal": 0, "off_boundary": len(off)}
    say(f"  {tf}: IG sent {len(ig)} candles; IG's start labels in UK time: {', '.join(labels[:8])}"
        + (" ..." if len(labels) > 8 else ""))
    say(f"      IG candles NOT on the bot's {tf} boundaries: {len(off)}"
        + (f" (first: {', '.join(uk_short(c.start) for c in off[:5])})" if off else ""))
    lines = []
    for c in mine:
        theirs = by_start.get(c.start)
        if theirs is None:
            near = sorted((x for x in ig if c.start - NOMINAL[tf] < x.start < c.end),
                          key=lambda x: abs(x.start - c.start))          # the closest IG label first
            lines.append(f"      {uk_short(c.start):<20} bot {c.parts}/{c.expected_parts}: IG has NO candle with this "
                         "label" + (f"; nearest IG label {uk_short(near[0].start)}: " + _diff(near[0], c)
                                    if near else ""))
            continue
        res["same_label"] += 1
        if theirs.prices() == c.prices():
            res["equal"] += 1
            if tf == "1w" or c.parts != c.expected_parts:
                lines.append(f"      {uk_short(c.start):<20} bot {c.parts}/{c.expected_parts}: same label, all 8 prices equal")
        else:
            lines.append(f"      {uk_short(c.start):<20} bot {c.parts}/{c.expected_parts}: same label, " + _diff(theirs, c))
    say(f"      the bot's own {tf} candles in that period: {len(mine)}; same label {res['same_label']}; "
        f"all 8 prices equal {res['equal']}")
    for x in lines:
        say(x)
    return res


def _diff(ig: Candle, mine: Candle) -> str:
    d = [f"{f} IG {plain(a)} / bot {plain(x)}" for f, a, x in zip(FIELDS, ig.prices(), mine.prices()) if a != x]
    return "all 8 prices equal" if not d else "prices differ: " + ", ".join(d)


# ---- store: copy into the pair's store (never overwriting) ----------------------------------

def store_into(settings: Any, store: CandleStore, now: datetime, say: Callable[[str], None]) -> dict:
    check_same_pair(settings, store)
    b = Boundaries(settings.candles, MarketHours(settings.market_hours))
    hold = holding(settings)
    counts: dict[str, dict[str, int]] = {}
    for tf, _, _ in PERIODS:
        c_ = counts.setdefault(tf, {"stored": 0, "kept_bots_own": 0, "not_on_boundary": 0, "relabelled": 0})
        for day in hold.days(tf):
            for c in hold.read_day(tf, day):
                bot = to_bot_label(b, tf, c)
                if bot is not c:
                    c_["relabelled"] += 1
                    c = bot
                if not b.is_on_boundary(tf, c.start):
                    c_["not_on_boundary"] += 1
                    continue
                r = store.add(c) if store.get(tf, c.start) is None else "kept"
                c_["stored" if r == "stored" else "kept_bots_own"] += 1
        say(f"  {tf}: stored {c_['stored']} ({c_['relabelled']} under the bot's Sunday 00:00 UK label); "
            f"the bot's own kept (not overwritten) {c_['kept_bots_own']}; "
            f"not stored (start not on the bot's boundaries) {c_['not_on_boundary']}")
    # the rebuild rule, over every 5-minute candle in the periods filled
    first = min((d for tf, _, _ in PERIODS for d in hold.days(tf)), default=None)
    fives = [c.start for c in store.read_range("5m", datetime.combine(first, datetime.min.time(), UTC), now)] \
        if first else []
    rebuilt = rebuild_incomplete(store, b, fives, now, "long history fill: rebuilt from the fuller set")
    say(f"  Rebuild rule: {len(rebuilt)} bigger candle(s) rebuilt" + (
        "" if rebuilt else " (this fill adds no 5-minute candles, so no bot candle has a fuller set)"))
    for old, new in rebuilt:
        say(f"    {new.timeframe} {uk_short(new.start)}: {old.parts} -> {new.parts} of {new.expected_parts}")
    return counts


def _counts(store: CandleStore, settings: Any, say: Callable[[str], None], record: bool = False) -> None:
    b = Boundaries(settings.candles, MarketHours(settings.market_hours))
    chk = check_store(store, b)
    say("  candles: " + ", ".join(f"{k} {v}" for k, v in chk.candles.items()) + f" (total {sum(chk.candles.values())})")
    say(f"  store checks: {len(chk.problems)} problem(s); {len(chk.gaps)} gap(s), {len(chk.new_gaps)} not recorded")
    for p in chk.problems[:20]:
        say("    " + p)
    for g in chk.gaps[:40]:
        say("    " + g.describe() + (" (recorded)" if g.known else " (NEW)"))
    if len(chk.gaps) > 40:
        say(f"    ... and {len(chk.gaps) - 40} more")
    if record:
        for g in chk.new_gaps:
            store.record_gap(g.timeframe, g.start, g.end, g.missing, datetime.now(UTC),
                             "store check after the long history fill")


# ---- prove: one small summer hourly request ------------------------------------------------

PROOF_FROM_UTC = datetime(2026, 8, 12, 9, 0, tzinfo=UTC)     # Wed 12 Aug 2026 10:00 BST
PROOF_CANDLES = 3


def _prove(settings: Any, say: Callable[[str], None]) -> int:
    """One request for 3 hourly candles in UK summer time; succeeds only if IG's
    candles are exactly the 3 asked for (UTC 09:00, 10:00, 11:00 = 10:00 to 12:00 BST)."""
    from ig.client import IGClient
    from ig.errors import IGLoginFailure, stop_bot
    from ig.history import HistoryDoor, ig_time
    from ig.secrets import ENV_PATH, load_credentials
    want = [PROOF_FROM_UTC + timedelta(hours=i) for i in range(PROOF_CANDLES)]
    p = Planned("HOUR", want[0], want[-1], PROOF_CANDLES, "ig-1h", want)
    say(f"PROOF: HOUR candles {uk_short(want[0])} to {uk_short(want[-1])} ({PROOF_CANDLES} points); sent to IG as "
        f"from {ig_time(p.start)} to {ig_time(p.end)} (UK time)")
    client = IGClient(settings.ig, load_credentials(ENV_PATH))
    door = HistoryDoor(client, settings.history)
    try:
        client.connect()
        reply = door.fetch(settings.market.epic, "HOUR", p.start, p.end, p.points, "proof: request times in UK time")
    except IGLoginFailure as f:
        client.logout()
        stop_bot(f)
    client.logout()
    saved = save_reply(settings, 0, p, reply, datetime.now(UTC))
    got, problems = candles_from_ig(reply.rows, "1h", NOMINAL["1h"])
    labels = [c.start for c in got]
    say(f"  IG sent {len(got)} candle(s), labelled (UTC): {', '.join(t.strftime('%Y-%m-%dT%H:%MZ') for t in labels)}")
    say(f"  asked for (UTC):                  {', '.join(t.strftime('%Y-%m-%dT%H:%MZ') for t in want)}")
    say(f"  reply kept in {saved}; IG allowance now {reply.remaining} of {reply.total}")
    ok = labels == want and not problems
    say(f"  IG's times line up with the request: {'YES' if ok else 'NO'}")
    return 0 if ok else 3


# ---- command line --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    from config.settings_loader import load_or_exit
    from housekeeping.logs import setup_logging
    from ig.history import HistoryDoor

    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["plan", "go", "prove", "store"])
    ap.add_argument("--pair", required=True, help="always named: never assumed")
    args = ap.parse_args(argv)
    settings = load_or_exit().for_pair(args.pair.upper())
    setup_logging(settings.housekeeping, "history", console=False)
    store = CandleStore(settings.candles.folder, settings.candles.compress_after_days)
    now = datetime.now(UTC).replace(second=0, microsecond=0)
    say = lambda t="": print(t, flush=True)  # noqa: E731
    status = _status(settings)

    if args.action == "plan":
        if status:
            say(f"The long history fill for {settings.market.pair} has already been started: {status.get('status')}.")
            return 0
        ok = show_plan(settings, HistoryDoor(None, settings.history), plan(settings, now), now, say)
        return 0 if ok else 3

    if args.action == "store":
        if status.get("status") != "fetched and compared":
            say(f"Nothing to store: the fetch has not been done (status: {status.get('status', 'none')}).")
            return 3
        say("BEFORE:")
        _counts(store, settings, say)
        say("STORING IG's candles (never overwriting):")
        counts = store_into(settings, store, now, say)
        say("AFTER:")
        _counts(store, settings, say, record=True)
        _set_status(settings, status="stored", stored_utc=now.strftime("%Y-%m-%dT%H:%M:%SZ"), counts=counts)
        return 0

    # go (or prove)
    if args.action == "go" and status.get("status") not in (None, "started"):
        say(f"Already {status.get('status')}: it never runs twice.")
        return 3
    from prices.move_to_pairs import SERVICE, service_state
    state = service_state()
    if state != "inactive":
        say(f"STOPPED: the price service is '{state}'. Only one IG login at a time: stop it first "
            f"(sudo systemctl stop {SERVICE}). Nothing sent.")
        return 3
    from ig.client import IGClient
    from ig.errors import IGLoginFailure, stop_bot
    from ig.secrets import ENV_PATH, load_credentials
    import time
    if args.action == "prove":
        return _prove(settings, say)
    # A run that stopped is carried on from the same plan (worked out at its start).
    anchor = datetime.strptime(status["started_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC) if status else now
    reqs = plan(settings, anchor)
    todo = [p for p in reqs if not already_held(settings, p)]
    if status:
        say(f"Carrying on the run started {uk_short(anchor)}: {len(reqs) - len(todo)} of {len(reqs)} requests are "
            f"already in the holding folder; {len(todo)} to send ({sum(p.points for p in todo)} points).")
    if not show_plan(settings, HistoryDoor(None, settings.history), todo or reqs, now, say):
        say("STOPPED: a request would not pass the door's checks. Nothing sent.")
        return 3
    client = IGClient(settings.ig, load_credentials(ENV_PATH))
    door = HistoryDoor(client, settings.history)
    if not status:
        _set_status(settings, status="started", started_utc=now.strftime("%Y-%m-%dT%H:%M:%SZ"))
    try:
        client.connect()
        say("")
        say("FETCHING into the holding folder (nothing used yet):")
        got = fetch(door, settings, reqs, say, pause=time.sleep)
    except IGLoginFailure as f:
        client.logout()
        stop_bot(f)
    except Exception as e:
        client.logout()
        say(f"FETCH STOPPED: {type(e).__name__}: {e}")
        return 2
    client.logout()
    say("")
    say("COMPARISON: IG's candles vs the bot's own (start label and all 8 prices):")
    results = [compare(settings, tf, got[tf], say) for tf, _, _ in PERIODS]
    _set_status(settings, status="fetched and compared", compared=results)
    fig = door.ig_figures() or {}
    say(f"IG's allowance now {fig.get('remaining')} of {fig.get('total')}; bot's 7-day use {door.points_last_7_days()}.")
    say("Nothing has been put in the store. 'store' does that, after the owner has seen this.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
