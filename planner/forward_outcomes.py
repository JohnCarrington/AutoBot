"""Read-only forward-outcome scoring for STP conditional journeys.

Consumes a frozen plan made at as_of and ONLY later completed candles.
No orders, no prediction probabilities, no interpolation within a candle.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Sequence

from prices.model import Candle, parse_iso


def score_journey(plan: dict[str, Any], candles: Sequence[Candle]) -> dict[str, Any]:
    """Measure whether entry preceded destination, with honest same-bar ambiguity.

    No execution assumptions: OHLC cannot establish which level traded first
    when both are touched in one candle. A destination hit before entry is a
    failed conditional sequence, not a winning trade. Untouched = censored.
    """
    direction = plan.get("trade")
    entry = plan.get("entry_zone")
    destinations = plan.get("destinations") or {}
    target = (destinations.get("primary") or {}).get("zone")
    if direction not in ("BUY", "SELL") or not entry or not target:
        return {"status": "NOT_SCORABLE", "reason": "no complete entry and primary destination"}
    lo_e, hi_e = Decimal(str(entry["low"])), Decimal(str(entry["high"]))
    lo_t, hi_t = Decimal(str(target["low"])), Decimal(str(target["high"]))
    if not (lo_e <= hi_e and lo_t <= hi_t):
        raise ValueError("invalid zone boundaries")
    if (direction == "SELL" and hi_t >= lo_e) or (direction == "BUY" and lo_t <= hi_e):
        return {"status": "NOT_SCORABLE", "reason": "destination not beyond entry"}
    as_of = parse_iso(plan["as_of_utc"])
    invalidation = plan.get("invalidation") or {}
    # The structural rules are CLOSE-based. This scorer applies those
    # thresholds to M5 closes as a conservative diagnostic, not as a claim
    # that the H1/H4 structural-close condition has been satisfied.
    # Only the zone-break level is checked here; higher-timeframe structural
    # invalidation needs completed H1/H4 candles in a separate audit.
    zone_break = invalidation.get("zone_break_close")
    zone_break = Decimal(str(zone_break)) if zone_break is not None else None
    entry_at = None
    seen = None
    for candle in sorted(candles, key=lambda c: c.start):
        # Require strictly future, fully closed candles; reject any overlapping
        # or stale candle instead of accidentally using look-ahead information.
        if candle.start < as_of:
            continue
        if seen is not None and candle.start < seen:
            raise ValueError("overlapping forward candles")
        seen = candle.end
        low, high = candle.sell_low, candle.sell_high
        hits_entry = low <= hi_e and high >= lo_e
        hits_target = low <= hi_t and high >= lo_t
        zone_invalidated = (
            zone_break is not None and (
                candle.sell_close >= zone_break if direction == "SELL"
                else candle.sell_close <= zone_break
            )
        )
        if entry_at is None:
            if hits_entry and hits_target:
                return {"status": "AMBIGUOUS_SAME_CANDLE", "at": candle.end.isoformat()}
            if hits_target:
                return {"status": "DESTINATION_BEFORE_ENTRY", "at": candle.end.isoformat()}
            if zone_invalidated:
                return {"status": "ZONE_INVALIDATED_BEFORE_ENTRY", "at": candle.end.isoformat()}
            if hits_entry:
                entry_at = candle.end.isoformat()
        else:
            if hits_target and zone_invalidated:
                return {"status": "AMBIGUOUS_TARGET_OR_INVALIDATION",
                        "entry_at": entry_at, "at": candle.end.isoformat()}
            if zone_invalidated:
                return {"status": "ZONE_INVALIDATED_AFTER_ENTRY",
                        "entry_at": entry_at, "at": candle.end.isoformat()}
            if hits_target:
                return {"status": "ENTRY_THEN_DESTINATION", "entry_at": entry_at,
                        "destination_at": candle.end.isoformat()}
    if entry_at is not None:
        return {"status": "ENTRY_ONLY_CENSORED", "entry_at": entry_at}
    return {"status": "NEITHER_CENSORED"}
