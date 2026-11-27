"""Structural lineages and D-25 test counting (Phase 2, owner's approval of 27 November 2026: C-2, C-3, C-4, PD-2, PD-3,
PD-4; docs/research/stp_lifecycle_integrity_20261127/).

A published forecast (an STP opportunity, its id) is not the same thing as the structural test it trades. A LINEAGE is
the durable identity of one structural place in one direction (BUY and SELL lineages are always separate). Its id is
the id of its first opportunity (design section 10: "the first id of the opportunity's identity lineage"). Opportunities
join a lineage; the lineage owns the D-25 test count, so hourly republication, completion or invalidation and reissue,
supersession, an overlapping parallel publication, a change in the fixed levels of the same zone, the daily or weekly
rollover, a failed breakout and reclaim, and a restart can no longer restart the duplicate key at "#t1". A genuinely
new structural test still gets the next number, by the unchanged D-25 / P-C8 rule.

Membership (no new number anywhere):
  * a new opportunity joins the lineage of a LIVE opportunity of the same direction with the same identity (FC-05) or
    a zone that OVERLAPS it (shares more than one price: zones that merely share an edge are distinct, PD-3); the
    oldest such lineage if several;
  * otherwise the lineage of the most recently ENDED opportunity of the same direction with the same identity or an
    overlapping zone (C-2; the 00:00 rollover successor, PD-3);
  * otherwise a new lineage.
  Overlap is always tested against a member's own zone, never against a lineage's union or a chain of zones, so two
  places that do not overlap are never merged through a third.

D-25 / P-C8 counting (unchanged rule; owner 17 November 2026): a finished hourly candle that interacts with the zone
starts a test when the count is armed; one wholly clear of it (its whole range more than near_level_within_pips away)
re-arms the count. Two things here keep missing data from making a test that never happened (PD-5):
  * a re-arm needs a COMPLETE hourly candle (built from every 5-minute candle the market hours expect, or IG's own
    candle): a candle missing parts may have touched the zone in the missing parts;
  * an incomplete candle whose stored parts are wholly clear neither starts a test nor re-arms; it is recorded as
    uncertain.
Seeding (C-2, strengthened): a new lineage's count starts at the most recent complete hourly candle wholly clear of its
zone before the creation hour (its last re-arm), found by walking back through the stored hourly candles: every hour
after it is counted. So a test that began before publication is test 1 and the first test after a later re-arm is
test 2, whatever the strategies' confirmation timing. No look-back window is assumed: the walk stops at the re-arm, or
at the start of the store. The creation hour itself is counted when it finishes.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from planner.zones import interacts, wholly_clear
from prices.model import parse_iso

TEST, REARM = "test", "rearm"


def _d(x: Any) -> Decimal:
    return Decimal(str(x))


def _iso(t: datetime | None) -> str | None:
    return None if t is None else t.strftime("%Y-%m-%dT%H:%M:%SZ")


def strict_overlap(a_low: Any, a_high: Any, b_low: Any, b_high: Any) -> bool:
    """Two zones share more than one price (PD-3: zones that merely share an edge are distinct)."""
    return _d(a_low) < _d(b_high) and _d(b_low) < _d(a_high)


def zones_overlap(a: dict | None, b: dict | None) -> bool:
    if not a or not b or None in (a.get("low"), a.get("high"), b.get("low"), b.get("high")):
        return False
    return strict_overlap(a["low"], a["high"], b["low"], b["high"])


def complete(c: Any) -> bool:
    """Built from every 5-minute candle the market hours expect (or IG's own candle: parts 0 of 0)."""
    exp = getattr(c, "expected_parts", 1)
    return exp == 0 or getattr(c, "parts", 1) >= exp


def new_tests() -> dict:
    return {"events": [], "through_utc": None, "since_utc": None, "uncertain": []}


def armed(tests: dict) -> bool:
    ev = tests.get("events") or []
    return not ev or ev[-1][1] == REARM


def count_hour(settings: Any, tests: dict, c: Any, low: Decimal, high: Decimal) -> str | None:
    """Count one finished hourly candle into `tests` (once: candles ending at or before through_utc are skipped).
    Returns "test", "rearm", "uncertain" or None (nothing changed)."""
    through = tests.get("through_utc")
    if through and c.end <= parse_iso(through):
        return None
    what = None
    touches = interacts(settings, c, low, high, True) or interacts(settings, c, low, high, False)
    if armed(tests) and touches:
        tests.setdefault("events", []).append([_iso(c.start), TEST])
        what = TEST
    elif not armed(tests) and not touches and wholly_clear(settings, c, low, high) and complete(c):
        tests.setdefault("events", []).append([_iso(c.start), REARM])
        what = REARM
    elif not touches and not complete(c):
        tests.setdefault("uncertain", []).append(_iso(c.start))
        what = "uncertain"
    tests["through_utc"] = _iso(c.end)
    return what


def _hours(store: Any, start: datetime, end: datetime) -> list:
    return [c for c in store.read_range("1h", start, end) if c.start >= start and c.end <= end]


def last_rearm_before(settings: Any, store: Any, low: Decimal, high: Decimal, upto: datetime) -> Any:
    """The most recent complete hourly candle ending at or before `upto` that is wholly clear of the zone, walking back
    a week at a time to the start of the store; None if there is none."""
    days = store.days("1h") if hasattr(store, "days") else []
    first = datetime.combine(days[0], datetime.min.time(), upto.tzinfo) if days else upto - timedelta(days=28)
    end = upto
    while end > first:
        start = max(first, end - timedelta(days=7))
        for c in reversed(_hours(store, start, end)):
            if complete(c) and wholly_clear(settings, c, low, high):
                return c
        end = start
    return None


def seed_tests(settings: Any, store: Any, low: Any, high: Any, created: datetime) -> dict:
    """A new lineage's D-25 count: from its zone's last re-arm before the creation hour, every finished hour up to the
    creation hour counted; the creation hour is counted by the tracker when it finishes."""
    low, high = _d(low), _d(high)
    hour = created.replace(minute=0, second=0, microsecond=0)
    w = last_rearm_before(settings, store, low, high, hour)
    t = new_tests()
    start = w.end if w is not None else None
    t["since_utc"] = _iso(start)
    t["seed"] = {"last_rearm_hour_utc": _iso(w.start) if w is not None else None, "counted_until_utc": _iso(hour)}
    if start is None:
        days = store.days("1h") if hasattr(store, "days") else []
        start = datetime.combine(days[0], datetime.min.time(), hour.tzinfo) if days else hour
    for c in _hours(store, start, hour):
        count_hour(settings, t, c, low, high)
    t["through_utc"] = _iso(hour)
    return t


def count_gap(settings: Any, store: Any, tests: dict, low: Any, high: Any, upto: datetime) -> list[str]:
    """When a lineage is rejoined after it had no tracked opportunity: the hours it was not counted, from through_utc to
    the creation hour of the rejoining opportunity, counted against the new zone (as stp.authorise.which_test counts the
    hours after the record). Returns what each counted hour did."""
    low, high = _d(low), _d(high)
    hour = upto.replace(minute=0, second=0, microsecond=0)
    frm = parse_iso(tests["through_utc"]) if tests.get("through_utc") else None
    out = []
    if frm is not None and frm < hour:
        for c in _hours(store, frm, hour):
            w = count_hour(settings, tests, c, low, high)
            if w:
                out.append(f"{_iso(c.start)} {w}")
        tests["through_utc"] = _iso(hour)
    return out


def test_number(settings: Any, store: Any, low: Any, high: Any, tests: dict | None, rejection_start: datetime,
                since: datetime | None = None) -> int:
    """The D-25 test that contains the rejection candle: the tests counted before the rejection candle's hour, plus
    the hours after the record (against the current zone), plus one if the count is armed then. 0 for a rejection
    candle before the lineage's counted history (before its seeded re-arm): an earlier, distinct test."""
    low, high = _d(low), _d(high)
    hour = rejection_start.replace(minute=0, second=0, microsecond=0)
    t = json.loads(json.dumps(tests)) if tests else None
    if t is not None and t.get("since_utc") and hour < parse_iso(t["since_utc"]):
        return 0
    if t is None:
        frm = since if since is not None else hour - timedelta(days=14)
        t = new_tests()
        for c in _hours(store, frm, hour):
            if since is not None and c.start < since:
                continue
            count_hour(settings, t, c, low, high)
    else:
        t["events"] = [e for e in t.get("events", []) if parse_iso(e[0]) < hour]
        if t.get("through_utc") and parse_iso(t["through_utc"]) < hour:
            for c in _hours(store, parse_iso(t["through_utc"]), hour):
                count_hour(settings, t, c, low, high)
    n = sum(1 for e in t["events"] if e[1] == TEST)
    return n + 1 if armed(t) else max(n, 1)
