"""Read-only forward-outcome scoring for STP conditional journeys.

Consumes a frozen plan made at as_of and ONLY later completed candles.
No orders, no prediction probabilities, no interpolation within a candle.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Sequence

from prices.model import Candle, parse_iso


def score_journey(plan: dict[str, Any], candles: Sequence[Candle]) -> dict[str, Any]:
    """Score a frozen conditional path using completed candles of each timeframe.

    5m candles establish zone touches. H1 closes establish zone-break
    invalidation; H4 closes establish structure-break invalidation. All events
    with the same closing timestamp are assessed together to avoid inventing
    their order. This measures structural sequences, never actual fills/P&L.
    """
    from itertools import groupby

    direction = plan.get("trade")
    entry = plan.get("entry_zone")
    target = ((plan.get("destinations") or {}).get("primary") or {}).get("zone")
    if direction not in ("BUY", "SELL") or not entry or not target:
        return {"status": "NOT_SCORABLE", "reason": "no complete entry and primary destination"}
    lo_e, hi_e = Decimal(str(entry["low"])), Decimal(str(entry["high"]))
    lo_t, hi_t = Decimal(str(target["low"])), Decimal(str(target["high"]))
    if not (lo_e <= hi_e and lo_t <= hi_t):
        raise ValueError("invalid zone boundaries")
    if (direction == "SELL" and hi_t >= lo_e) or (direction == "BUY" and lo_t <= hi_e):
        return {"status": "NOT_SCORABLE", "reason": "destination not beyond entry"}

    as_of = parse_iso(plan["as_of_utc"])
    inv = plan.get("invalidation") or {}
    zone_break = Decimal(str(inv["zone_break_close"])) if inv.get("zone_break_close") is not None else None
    structure_break = (Decimal(str(inv["structure_break_close"]))
                       if inv.get("structure_break_close") is not None else None)
    entry_at = None
    for journey in (plan.get("observations") or {}).get("conditional_journeys", []):
        if (journey.get("entry") == [entry["low"], entry["high"]]
                and journey.get("countermove_evidence_state") == "AT_ENTRY_NOW"):
            entry_at = as_of.isoformat()
            break

    future = sorted((c for c in candles if c.start >= as_of and c.end > as_of),
                    key=lambda c: (c.end, c.start, c.timeframe))
    last_end: dict[str, Any] = {}
    gap_at = None
    for candle in future:
        if candle.timeframe not in ("5m", "1h", "4h"):
            raise ValueError(f"unsupported scoring timeframe: {candle.timeframe}")
        if candle.start < last_end.get(candle.timeframe, as_of):
            raise ValueError("overlapping forward candles")
        if candle.timeframe == "5m":
            previous = last_end.get("5m", as_of)
            if candle.start > previous and gap_at is None:
                gap_at = previous
        last_end[candle.timeframe] = candle.end

    if gap_at is not None:
        # A missing M5 interval can hide either entry, target or invalidation.
        # Refuse to score the sequence across that hole, including weekends.
        return {"status": "DATA_GAP_CENSORED", "first_gap_at": gap_at.isoformat()}

    for end, events_iter in groupby(future, key=lambda c: c.end):
        events = list(events_iter)
        touches = [c for c in events if c.timeframe == "5m"]
        hits_entry = any(c.sell_low <= hi_e and c.sell_high >= lo_e for c in touches)
        hits_target = any(c.sell_low <= hi_t and c.sell_high >= lo_t for c in touches)
        invalidated = any(
            (
                c.timeframe == "1h" and zone_break is not None
                and (c.sell_close >= zone_break if direction == "SELL" else c.sell_close <= zone_break)
            ) or (
                c.timeframe == "4h" and structure_break is not None
                and (c.sell_close >= structure_break if direction == "SELL"
                     else c.sell_close <= structure_break)
            )
            for c in events
        )
        when = end.isoformat()
        if entry_at is None:
            if hits_entry and hits_target:
                return {"status": "AMBIGUOUS_SAME_CANDLE", "at": when}
            if hits_target:
                return {"status": "DESTINATION_BEFORE_ENTRY", "at": when}
            if invalidated and hits_entry:
                return {"status": "AMBIGUOUS_ENTRY_OR_INVALIDATION", "at": when}
            if invalidated:
                return {"status": "STRUCTURE_INVALIDATED_BEFORE_ENTRY", "at": when}
            if hits_entry:
                entry_at = when
        else:
            if hits_target and invalidated:
                return {"status": "AMBIGUOUS_TARGET_OR_INVALIDATION",
                        "entry_at": entry_at, "at": when}
            if invalidated:
                return {"status": "STRUCTURE_INVALIDATED_AFTER_ENTRY",
                        "entry_at": entry_at, "at": when}
            if hits_target:
                return {"status": "ENTRY_THEN_DESTINATION", "entry_at": entry_at,
                        "destination_at": when}
    if entry_at is not None:
        return {"status": "ENTRY_ONLY_CENSORED", "entry_at": entry_at}
    return {"status": "NEITHER_CENSORED"}
