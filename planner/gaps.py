"""Missing market data in STP's lifecycle (Phase 2 WP3, PD-5 A+B+C; owner's approval of 27 November 2026).

A: every 5-minute candle the market hours expect (prices/calendar.py MarketHours: the weekly session, so the weekend
   and other closures are never a gap) that the store does not hold, while an opportunity is tracked, is recorded on
   that opportunity as a data gap: its zone touch, destination, break and invalidation could have happened unseen.
B: an opportunity with an unreconciled data gap does not authorise a new trade (stp/authorise.py), and neither does an
   opportunity whose lineage's D-25 count holds an uncertain hour (an incomplete hourly candle whose stored parts are
   clear of the zone: it may have hidden a test or a re-arm). Every other opportunity is unaffected. No expiry: the
   opportunity keeps every other rule and becomes eligible again only by reconciliation.
C: once the store holds every missing candle (filled from IG's own history by the approved procedure,
   prices/history_fill.py gap-go: never interpolated, never fabricated), the tracker re-checks the opportunity on them,
   in time order, by its own rules: a zone touch it missed (WAITING -> Watch & Wait, recorded at that candle), the
   primary destination it missed (it ends, at that candle, by the four-way rule, a confirmed trade entry's own time
   deciding), and the rebuilt hourly candles for its D-25 count. A rebuilt hourly candle that would change a test
   already numbered, or a zone break the tracker can no longer place in its failed-breakout window, is recorded and
   left for review: the opportunity then stays ineligible. Reconciliation never creates a trade, an order or a
   delayed entry, never reopens an opportunity and never rewrites a recorded event: every correction is a new event.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

FIVE = timedelta(minutes=5)


def _iso(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def missing_fives(settings: Any, store: Any, start: datetime, end: datetime) -> list[tuple[datetime, datetime]]:
    """The expected 5-minute candles (market hours) starting in [start, end) and ending by `end` that the store does
    not hold, merged into intervals [from, to)."""
    from prices.calendar import MarketHours
    hours = MarketHours(settings.market_hours)
    have = {c.start for c in store.read_range("5m", start, end)}
    out: list[list[datetime]] = []
    for s in hours.open_slots(start, end):
        if s + FIVE > end or s in have:
            continue
        if out and out[-1][1] == s:
            out[-1][1] = s + FIVE
        else:
            out.append([s, s + FIVE])
    return [(a, b) for a, b in out]


def filled(settings: Any, store: Any, gap: dict) -> bool:
    from prices.model import parse_iso
    return not missing_fives(settings, store, parse_iso(gap["from_utc"]), parse_iso(gap["to_utc"]))
