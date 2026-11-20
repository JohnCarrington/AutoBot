"""Offline structural journeys following confluence-zone encounters.

Uses fixed, as-of structural levels from the encounter day. Measures whether
price first reaches the next opposite structural destination or the next
same-direction breakout destination. Neither is a trading signal.
"""
from __future__ import annotations
import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from prices.store import CandleStore
from research.stp_validation.confluence_encounters import significant_levels, clusters

UTC = timezone.utc


def targets(levels, side, zone_low, zone_high, min_distance):
    """Two pre-known destination candidates, excluding levels inside origin."""
    # Resistance encounter: opposite destination is support below; breakout
    # destination is further resistance above. Mirror for support encounter.
    opposite = "support" if side == "resistance" else "resistance"
    same = side
    def choose(kind, direction):
        candidates = [(name, price) for name, price, s in levels if s == kind
                      and ((price < zone_low - min_distance) if direction == "down"
                           else (price > zone_high + min_distance))]
        if not candidates:
            return None
        name, price = (max(candidates, key=lambda x:x[1]) if direction == "down"
                       else min(candidates, key=lambda x:x[1]))
        return {"name": name, "price": str(price)}
    if side == "resistance":
        return choose(opposite, "down"), choose(same, "up")
    return choose(opposite, "up"), choose(same, "down")


def passage(future, reversal, continuation):
    """First arrival to either predeclared level; ties within M5 are ambiguous."""
    for i, bar in enumerate(future):
        def touched(t):
            if t is None:
                return False
            price = Decimal(t["price"])
            return bar.sell_low <= price <= bar.sell_high or (
                price < bar.sell_low and i == 0 and bar.sell_open <= price
            ) or (price > bar.sell_high and i == 0 and bar.sell_open >= price)
        rev = touched(reversal)
        cont = touched(continuation)
        if rev and cont:
            return "AMBIGUOUS", bar.end.isoformat(), i
        if rev:
            return "REVERSAL_DESTINATION", bar.end.isoformat(), i
        if cont:
            return "CONTINUATION_DESTINATION", bar.end.isoformat(), i
    return "CENSORED", None, None


def analyse(store, encounters, horizon_hours=48, min_distance_pips=5):
    if not encounters:
        return {"summary": {}, "journeys": []}
    first = min(datetime.fromisoformat(r["as_of"]) for r in encounters)
    last = max(datetime.fromisoformat(r["as_of"]) for r in encounters)
    history = store.read_range("5m", first - timedelta(days=40),
                               last + timedelta(hours=horizon_hours+2))
    by_day = defaultdict(list)
    for c in history:
        by_day[c.start.date()].append(c)
    cache = {}
    journeys = []
    for r in encounters:
        at = datetime.fromisoformat(r["as_of"])
        day = at.date()
        if day not in cache:
            cache[day] = significant_levels(history, day)
        levels = cache[day]
        low, high = Decimal(r["zone_low"]), Decimal(r["zone_high"])
        rev, cont = targets(levels, r["side"], low, high, Decimal(str(min_distance_pips)))
        # Only bars that START at/after the encounter closes. No encounter
        # candle leakage; fixed wall-clock horizon including overnight.
        future = [c for c in history if c.start >= at and c.start < at + timedelta(hours=horizon_hours)]
        if rev is None or cont is None:
            result, when, bars = "NO_TWO_SIDED_TARGETS", None, None
        else:
            result, when, bars = passage(future, rev, cont)
        journeys.append({
            "day": r["day"], "as_of": r["as_of"], "side": r["side"],
            "origin_zone": [r["zone_low"], r["zone_high"]],
            "levels": r["levels"], "family_count": r["family_count"],
            "reversal_destination": rev, "continuation_destination": cont,
            "outcome": result, "reached_at": when,
            "bars_after_encounter": bars,
            "previous_20pip_label": r["outcome"],
        })
    counts = Counter(j["outcome"] for j in journeys)
    resolved = counts["REVERSAL_DESTINATION"] + counts["CONTINUATION_DESTINATION"]
    return {
        "method": "as-of structural destination first-passage; no fixed 20-pip outcome",
        "horizon_hours": horizon_hours,
        "summary": {"encounters": len(journeys), "outcomes": dict(counts),
                    "resolved": resolved,
                    "reversal_destination_first_rate": counts["REVERSAL_DESTINATION"]/resolved if resolved else None},
        "caveats": [
            "This scores encounters, not advance STP destination forecasts.",
            "Both target levels are chosen from completed prior UTC sessions.",
            "Closest level is selected independently on each side, not weighted by confluence.",
            "Missing targets and censored outcomes are reported, not silently dropped.",
            "No H1/H4 momentum/exhaustion integration yet.",
            "No execution, no broker access, no production changes.",
        ],
        "journeys": journeys,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--historical-store", type=Path, required=True)
    p.add_argument("--encounters", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--horizon-hours", type=int, default=48)
    a = p.parse_args()
    folder = a.historical_store.resolve()
    if folder.name != "GBPUSD" or not (folder/"rebuild_manifest.json").exists():
        p.error("must use isolated rebuilt GBPUSD historical store")
    if a.output.resolve().is_relative_to(folder):
        p.error("output must be outside historical store")
    if not 1 <= a.horizon_hours <= 72:
        p.error("horizon-hours must be 1..72")
    raw = json.loads(a.encounters.read_text())
    result = analyse(CandleStore(folder, 30), raw["encounters"], a.horizon_hours)
    a.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k != "journeys"}, indent=2))
    print(f"Saved {len(result['journeys'])} journeys to {a.output}")


if __name__ == "__main__":
    main()
