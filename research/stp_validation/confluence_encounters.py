"""Offline, as-of confluence encounters and first-move continuation/reversal study.

Research only. Reads isolated historical GBPUSD candle store; never connects to IG.
Each day's levels are fixed using completed earlier sessions, and encounters are
scored on future 5m candles separately. No model is fitted here.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from prices.store import CandleStore

PIP = Decimal("1")  # GBPUSD native IG points: 1.2500 -> 12500, so 1 pip = 1 point
UTC = timezone.utc


def significant_levels(history, today):
    """Prior-day/week and rolling 10-session extremes, without current-day leakage."""
    by_day = defaultdict(list)
    for c in history:
        if c.end.date() < today:
            by_day[c.start.date()].append(c)
    days = sorted(by_day)
    if len(days) < 10:
        return []
    previous = by_day[days[-1]]
    recent = [c for day in days[-10:] for c in by_day[day]]
    # Completed previous five-session block; calendar weeks may contain holidays.
    last_five = [c for day in days[-5:] for c in by_day[day]]
    prev_hi = max(c.sell_high for c in previous)
    prev_lo = min(c.sell_low for c in previous)
    pivot = (prev_hi + prev_lo + previous[-1].sell_close) / Decimal(3)
    spread = prev_hi - prev_lo
    pivot_levels = [
        ("R1", 2*pivot-prev_lo, "resistance"),
        ("R2", pivot+spread, "resistance"),
        ("R3", prev_hi+2*(pivot-prev_lo), "resistance"),
        ("S1", 2*pivot-prev_hi, "support"),
        ("S2", pivot-spread, "support"),
        ("S3", prev_lo-2*(prev_hi-pivot), "support"),
        ("P_RESISTANCE", pivot, "resistance"),
        ("P_SUPPORT", pivot, "support"),
    ]
    # Confirmed daily swing: both adjacent completed sessions exist.
    daily = [(max(c.sell_high for c in by_day[d]),
              min(c.sell_low for c in by_day[d])) for d in days[-12:]]
    swing_levels = []
    for i in range(1, len(daily)-1):
        if daily[i][0] > max(daily[i-1][0], daily[i+1][0]):
            swing_levels.append((f"SWING_HIGH_{i}", daily[i][0], "resistance"))
        if daily[i][1] < min(daily[i-1][1], daily[i+1][1]):
            swing_levels.append((f"SWING_LOW_{i}", daily[i][1], "support"))
    return pivot_levels + swing_levels + [
        ("PDH", max(c.sell_high for c in previous), "resistance"),
        ("PDL", min(c.sell_low for c in previous), "support"),
        ("5D_HIGH", max(c.sell_high for c in last_five), "resistance"),
        ("5D_LOW", min(c.sell_low for c in last_five), "support"),
        ("10D_HIGH", max(c.sell_high for c in recent), "resistance"),
        ("10D_LOW", min(c.sell_low for c in recent), "support"),
    ]


def family(name):
    if name.startswith(("R1","R2","R3","S1","S2","S3","P_")):
        return "PIVOT"
    if name.startswith("SWING"):
        return "SWING"
    if name.startswith("PD"):
        return "PREVIOUS_DAY"
    return "ROLLING_EXTREME"


def clusters(levels, tolerance):
    """Combine nearby levels; preserve distinct evidence families."""
    ordered = sorted(levels, key=lambda x: x[1])
    groups = []
    for item in ordered:
        if groups and item[2] == groups[-1][-1][2] and item[1] - groups[-1][-1][1] <= tolerance:
            groups[-1].append(item)
        else:
            groups.append([item])
    return [g for g in groups if len({family(x[0]) for x in g}) >= 2]


def outcome(bars, encounter_idx, side, barrier, horizon=288):
    """First passage after encounter, not an unconditional touch within 24h.

    Resistance: down is reversal; up is continuation. Support: inverse.
    Ambiguous if both barriers touched within the same 5m candle.
    """
    first = bars[encounter_idx]
    anchor = first.sell_close
    limit = min(len(bars), encounter_idx + horizon + 1)
    for bar in bars[encounter_idx + 1:limit]:
        up = bar.sell_high >= anchor + barrier
        down = bar.sell_low <= anchor - barrier
        if up and down:
            return "AMBIGUOUS"
        if up or down:
            reversal = down if side == "resistance" else up
            return "REVERSAL" if reversal else "CONTINUATION"
    return "CENSORED"


def run(store, start, end, tolerance_pips=5, excursion_pips=20):
    # M5 history is loaded once. Decisions are built strictly from completed
    # prior-day bars; future bars are used ONLY by outcome().
    bars = store.read_range("5m", start - timedelta(days=40), end + timedelta(days=2))
    by_day = defaultdict(list)
    for bar in bars:
        by_day[bar.start.date()].append(bar)
    tolerance = Decimal(str(tolerance_pips)) * PIP
    barrier = Decimal(str(excursion_pips)) * PIP
    rows = []
    for day in sorted(by_day):
        if not (start.date() <= day <= end.date()) or day.weekday() >= 5:
            continue
        today_bars = by_day[day]
        levels = significant_levels(bars, day)
        # This is a structural-only first pass. Pivots, EMAs, MACD and
        # Bollinger bands are NOT yet included and must not be claimed.
        groups = clusters(levels, tolerance)
        for group in groups:
            side = group[0][2]
            low = min(x[1] for x in group)
            high = max(x[1] for x in group)
            # One encounter per zone per day. Demand approach from correct
            # side, rather than treating any later visit as an initial test.
            hit = None
            for i in range(1, len(today_bars)):
                prior, current = today_bars[i-1], today_bars[i]
                approaching = prior.sell_close < low if side == "resistance" else prior.sell_close > high
                touching = current.sell_high >= low if side == "resistance" else current.sell_low <= high
                if approaching and touching:
                    hit = i
                    break
            if hit is None:
                continue
            result = outcome(today_bars, hit, side, barrier)
            # Descriptive, strictly pre-encounter momentum; no fitted classifier.
            past = today_bars[:hit]
            delta_1h = past[-1].sell_close - past[-13].sell_close if len(past) >= 13 else None
            delta_3h = past[-1].sell_close - past[-37].sell_close if len(past) >= 37 else None
            aligned = (delta_1h is not None and delta_3h is not None
                       and delta_1h * delta_3h > 0
                       and (delta_1h > 0) == (side == "resistance"))
            rows.append({
                "day": str(day), "as_of": today_bars[hit].end.isoformat(),
                "side": side, "zone_low": str(low), "zone_high": str(high),
                "levels": [x[0] for x in group],
                "families": sorted({family(x[0]) for x in group}),
                "family_count": len({family(x[0]) for x in group}),
                "approach_momentum_1h_points": str(delta_1h) if delta_1h is not None else None,
                "approach_momentum_3h_points": str(delta_3h) if delta_3h is not None else None,
                "approach_trend_aligned": aligned,
                "outcome": result,
                "barrier_pips": excursion_pips,
                "note": "M5 first-passage proxy; not an executable trade",
            })
    counts = Counter(r["outcome"] for r in rows)
    resolved = counts["REVERSAL"] + counts["CONTINUATION"]
    by_alignment = {}
    for state in (True, False):
        sample = [r for r in rows if r["approach_trend_aligned"] is state]
        tally = Counter(r["outcome"] for r in sample)
        denominator = tally["REVERSAL"] + tally["CONTINUATION"]
        by_alignment[str(state).lower()] = {
            "encounters": len(sample), "counts": dict(tally),
            "reversal_rate_resolved": tally["REVERSAL"] / denominator if denominator else None,
        }
    return {
        "method": "as-of classic pivots, confirmed daily swings, previous-day and rolling 5/10-session extrema",
        "by_approach_trend_alignment": by_alignment,
        "caveats": [
            "Exploratory, not a predictive model or PIA First replication.",
            "Classic daily pivots and confirmed daily swings included; H1/H4 swings, EMA, MACD and Bollinger not yet included.",
            "Pivot session is UTC-day proxy; must verify against PIA/IG pivot session.",
            "Momentum is descriptive, not a trained trending-day classifier.",
            "No session calendar normalization; 5/10 sessions are observed UTC days.",
            "First-passage measured after encounter candle close; same-bar ambiguity is censored.",
            "24h proxy is capped at remaining same-day candles; overnight moves not assessed.",
            "No claim of accuracy until independent baseline and out-of-sample validation.",
        ],
        "counts": dict(counts), "resolved": resolved,
        "reversal_rate_resolved": counts["REVERSAL"] / resolved if resolved else None,
        "encounters": rows,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--historical-store", type=Path, required=True)
    p.add_argument("--start-date", required=True)
    p.add_argument("--end-date", required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--tolerance-pips", type=float, default=5)
    p.add_argument("--excursion-pips", type=float, default=20)
    a = p.parse_args()
    folder = a.historical_store.resolve()
    if folder.name != "GBPUSD" or not (folder / "rebuild_manifest.json").exists():
        p.error("must use isolated rebuilt historical GBPUSD store")
    if a.output.resolve().is_relative_to(folder):
        p.error("output must be outside historical candle store")
    start = datetime.fromisoformat(a.start_date).replace(tzinfo=UTC)
    end = datetime.fromisoformat(a.end_date).replace(tzinfo=UTC) + timedelta(days=1)
    if end <= start or end - start > timedelta(days=93):
        p.error("date window must be ordered and no longer than 92 days")
    result = run(CandleStore(folder, 30), start, end,
                 a.tolerance_pips, a.excursion_pips)
    a.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "encounters"}, indent=2))
    print(f"Saved {len(result['encounters'])} encounters to {a.output}")


if __name__ == "__main__":
    main()
