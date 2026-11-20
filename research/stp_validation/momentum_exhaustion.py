"""Offline as-of momentum/exhaustion stratification of structural zone encounters.

Reads the encounter JSON from confluence_encounters and the isolated M5 store.
No broker, no model fitting. Features use candles completed BEFORE the
encounter candle; labels are inherited from the exploratory first-passage test.
"""
from __future__ import annotations
import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from prices.store import CandleStore


def ema(values, period):
    if len(values) < period:
        return None
    alpha = Decimal(2) / Decimal(period + 1)
    value = sum(values[:period]) / Decimal(period)
    for x in values[period:]:
        value += alpha * (x - value)
    return value


def rsi(values, period=14):
    if len(values) <= period:
        return None
    gains = [max(values[i] - values[i-1], Decimal(0)) for i in range(1, len(values))]
    losses = [max(values[i-1] - values[i], Decimal(0)) for i in range(1, len(values))]
    gain = sum(gains[:period]) / period
    loss = sum(losses[:period]) / period
    for g, l in zip(gains[period:], losses[period:]):
        gain = (gain * (period - 1) + g) / period
        loss = (loss * (period - 1) + l) / period
    if loss == 0:
        return Decimal(100) if gain else Decimal(50)
    return Decimal(100) - Decimal(100) / (Decimal(1) + gain / loss)


def macd_histogram(values):
    if len(values) < 45:
        return None
    # EMA(12)-EMA(26), signal EMA(9), all computed from closed candles.
    fast = slow = None
    line = []
    for i in range(26, len(values)+1):
        fast = ema(values[:i], 12)
        slow = ema(values[:i], 26)
        line.append(fast - slow)
    if len(line) < 11:
        return None
    return line[-1] - ema(line, 9), line[-4] - ema(line[:-3], 9)


def features(history, at, side):
    past = [c for c in history if c.end <= at]
    if len(past) < 110:
        return {"state": "INSUFFICIENT_DATA"}
    closes = [c.sell_close for c in past]
    highs = [c.sell_high for c in past]
    lows = [c.sell_low for c in past]
    direction = Decimal(1) if side == "resistance" else Decimal(-1)
    e8, e20, e50 = (ema(closes, n) for n in (8, 20, 50))
    e20_prev = ema(closes[:-12], 20)
    slope = (e20 - e20_prev) * direction
    stack = (e8 - e20) * direction > 0 and (e20 - e50) * direction > 0
    momentum = (closes[-1] - closes[-13]) * direction
    momentum_earlier = (closes[-13] - closes[-25]) * direction
    hist = macd_histogram(closes)
    hist_now, hist_prev = hist if hist is not None else (None, None)
    macd_fading = hist is not None and (hist_now - hist_prev) * direction < 0
    r_now = rsi(closes)
    r_prev = rsi(closes[:-12])
    rsi_fading = r_now is not None and r_prev is not None and (r_now - r_prev) * direction < 0
    # New extreme in last hour relative to previous 3 hours, with declining
    # directional momentum. This is an exhaustion CANDIDATE, not confirmation.
    new_extreme = (max(highs[-12:]) > max(highs[-48:-12]) if direction > 0
                   else min(lows[-12:]) < min(lows[-48:-12]))
    decelerating = momentum < momentum_earlier
    exhaustion = new_extreme and decelerating and (macd_fading or rsi_fading)
    strong = stack and slope > 0 and momentum > 0 and not exhaustion
    return {
        "state": "EXHAUSTION_CANDIDATE" if exhaustion else
                 "MOMENTUM_STRONG" if strong else "MIXED",
        "ema_stack_aligned": bool(stack),
        "ema20_slope_1h_points": str(slope),
        "momentum_1h_points": str(momentum),
        "momentum_prior_1h_points": str(momentum_earlier),
        "new_extreme": bool(new_extreme),
        "macd_histogram_fading": bool(macd_fading),
        "rsi_fading": bool(rsi_fading),
        "rsi": str(r_now) if r_now is not None else None,
    }


def analyse(store, source):
    rows = []
    raw = json.loads(source.read_text())
    encounters = raw["encounters"]
    if not encounters:
        return {"counts": {}, "encounters": []}
    first = min(datetime.fromisoformat(x["as_of"]) for x in encounters)
    last = max(datetime.fromisoformat(x["as_of"]) for x in encounters)
    candles = store.read_range("5m", first - timedelta(days=7), last + timedelta(days=1))
    # Precompute complete candle cutoffs by day to avoid future leakage.
    for row in encounters:
        at = datetime.fromisoformat(row["as_of"])
        # Encounter candle must NOT contribute to features.
        prior = [c for c in candles if c.end < at]
        f = features(prior, at, row["side"])
        rows.append({**row, "momentum_exhaustion": f})
    states = defaultdict(list)
    for row in rows:
        states[row["momentum_exhaustion"]["state"]].append(row)
    summary = {}
    for state, group in sorted(states.items()):
        counts = Counter(r["outcome"] for r in group)
        resolved = counts["REVERSAL"] + counts["CONTINUATION"]
        summary[state] = {
            "encounters": len(group), "outcomes": dict(counts),
            "reversal_rate_resolved": counts["REVERSAL"] / resolved if resolved else None,
            "continuation_rate_resolved": counts["CONTINUATION"] / resolved if resolved else None,
        }
    return {
        "method": "pre-encounter M5 EMA stack/slope, momentum deceleration, MACD and RSI fading; exploratory",
        "by_momentum_exhaustion": summary,
        "caveats": [
            "Not a validated trending-day classifier; M5 features only.",
            "Uses encounter labels from source, including same-day 20-pip proxy and its limitations.",
            "Exhaustion is a candidate signal, not a confirmed reversal.",
            "Rates are descriptive; compare against baseline and out-of-sample data.",
            "No production or broker access.",
        ],
        "encounters": rows,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--historical-store", type=Path, required=True)
    p.add_argument("--encounters", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    folder = a.historical_store.resolve()
    if folder.name != "GBPUSD" or not (folder / "rebuild_manifest.json").exists():
        p.error("must use isolated rebuilt GBPUSD historical store")
    if a.output.resolve().is_relative_to(folder):
        p.error("output must be outside historical store")
    result = analyse(CandleStore(folder, 30), a.encounters)
    a.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k:v for k,v in result.items() if k != "encounters"}, indent=2))
    print(f"Saved {len(result['encounters'])} encounters to {a.output}")


if __name__ == "__main__":
    main()
