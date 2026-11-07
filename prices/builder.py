"""Builds 1-hour, 4-hour, daily and weekly candles from the STORED 5-minute
candles. Nothing else goes into them: no ticks, no mid prices, and nothing
asked from IG.

A bigger candle is built once its time is over and either
  * all the 5-minute candles the market hours say it should have are stored, or
  * a later 5-minute candle has been stored (so IG has moved on), or
  * candles.wait_for_late_candle_seconds has passed since its end.
If some 5-minute candles are missing, it is still built, from those that are
stored, and it records how many it used ("parts", e.g. 11 of 12) with a warning.

When a gap fill later completes missing 5-minute candles, rebuild_incomplete()
rebuilds every bigger candle that was built from an incomplete set, from the
fuller set, and archives the old one (never deleted).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable

from prices.calendar import Boundaries
from prices.model import BUILT, Candle, build_from, uk_short
from prices.store import CandleStore


def _buckets(tf: str, fives: list[Candle], b: Boundaries) -> dict[tuple[datetime, datetime], list[Candle]]:
    out: dict[tuple[datetime, datetime], list[Candle]] = {}
    for c in fives:
        out.setdefault(b.bucket(tf, c.start), []).append(c)
    return out


def build_due(store: CandleStore, b: Boundaries, now: datetime, wait_seconds: int,
              warn: Callable[[str], None], also_for: datetime | None = None) -> list[Candle]:
    """Build every bigger candle that is due. Returns the ones newly stored.
    `also_for`: the start of a 5-minute candle just stored; its bigger
    candles are looked at even if they were built before (a late arrival
    then shows up as a different value, which is warned about)."""
    stored: list[Candle] = []
    wait = timedelta(seconds=wait_seconds)
    for tf in BUILT:
        newest = store.newest(tf)
        if newest is not None:
            scan_from = newest.end
        else:
            days = store.days("5m")
            if not days:
                continue
            first = store.read_day("5m", days[0])
            scan_from = min(c.start for c in first) if first else now
        fives = store.read_range("5m", scan_from, now)
        buckets = _buckets(tf, fives, b)
        if also_for is not None:
            s, e = b.bucket(tf, also_for)
            if (s, e) not in buckets:
                buckets[(s, e)] = store.read_range("5m", s, e)
        latest_five = max((c.start for c in fives), default=None)
        for (s, e), parts in sorted(buckets.items()):
            if e > now:
                continue
            if newest is not None and s < newest.end and store.get(tf, s) is None:
                # It would overlap a candle already stored (for example one built
                # before the boundaries were changed). Stored candles are kept.
                continue
            parts = store.read_range("5m", s, e)  # every stored 5-minute candle in it
            if not parts:
                continue
            expected = b.expected_parts(s, e)
            moved_on = latest_five is not None and latest_five >= e
            if len(parts) < expected and not moved_on and now < e + wait:
                continue  # give a late 5-minute candle a chance
            candle = build_from(tf, s, e, parts, expected)
            if store.add(candle) == "stored":
                stored.append(candle)
                if len(parts) < expected:
                    warn(f"{tf} candle {uk_short(s)} built from only {len(parts)} of {expected} "
                         "5-minute candles (some are missing).")
    return stored


def rebuild_incomplete(store: CandleStore, b: Boundaries, filled: list[datetime], now: datetime,
                       reason: str) -> list[tuple[Candle, Candle]]:
    """The standing rule after a gap fill (docs/PRICES_AND_CANDLES.md): every
    bigger candle that holds one of the `filled` 5-minute candles, and that was
    built from an incomplete set, is rebuilt from ALL the 5-minute candles now
    stored, if that is a fuller set. The old one is archived, never deleted
    (CandleStore.replace_with_fuller). Candles not yet built are left to
    build_due. Returns (old, new) for each one replaced."""
    out: list[tuple[Candle, Candle]] = []
    for tf in BUILT:
        for s, e in sorted({b.bucket(tf, t) for t in filled}):
            old = store.get(tf, s)
            if old is None or old.parts >= old.expected_parts:
                continue
            parts = store.read_range("5m", s, e)
            if len(parts) <= old.parts:
                continue
            new = build_from(tf, s, e, parts, old.expected_parts)
            store.replace_with_fuller(new, reason, now)
            out.append((old, new))
    return out

