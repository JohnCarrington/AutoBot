"""Read-only, as-of forecast target hit evaluation.

A hit is not a profitable trade, and a same-candle crossing does not prove
which target was reached first. Never feeds outcomes back into plan_at.
"""
from __future__ import annotations

from decimal import Decimal


def score_target_ladder(ladder, candles, as_of, direction, *, require_contiguous_m5=True):
    if direction not in ("BUY", "SELL"):
        return {"status": "NOT_SCORABLE", "reason": "no directional thesis"}
    m5 = sorted((c for c in candles if c.timeframe == "5m" and
                 c.start >= as_of and c.end > as_of), key=lambda c: c.start)
    if not m5:
        return {"status": "DATA_GAP_CENSORED", "reason": "no M5 candles"}
    targets = {name: ladder.get(name) for name in ("immediate", "preferred", "extended")}
    result = {name: {"status": "NOT_FORECAST" if target is None else "NOT_REACHED",
                     "hit_at": None}
              for name, target in targets.items()}
    last_end = as_of
    for candle in m5:
        if require_contiguous_m5 and candle.start > last_end:
            for name, target in targets.items():
                if target is not None and result[name]["status"] == "NOT_REACHED":
                    result[name]["status"] = "DATA_GAP_CENSORED"
            return {"status": "DATA_GAP_CENSORED", "targets": result,
                    "first_gap_at": last_end.isoformat()}
        if candle.start < last_end:
            raise ValueError("overlapping M5 forward candles")
        last_end = candle.end
        low, high = candle.sell_low, candle.sell_high
        for name, target in targets.items():
            if target is None or result[name]["status"] != "NOT_REACHED":
                continue
            zone_low, zone_high = Decimal(str(target["low"])), Decimal(str(target["high"]))
            # A touch of any part of the zone is an observed structural hit.
            if low <= zone_high and high >= zone_low:
                result[name] = {"status": "REACHED", "hit_at": candle.end.isoformat()}
    return {"status": "SCORED", "targets": result,
            "note": "M5 zone touch only; no trade fills, invalidation or P&L"}
