"""Data-quality report for the STP validation candle store. READ ONLY; writes one JSON file.

  python -m research.stp_validation.dq --store data/research/stp_validation_store/GBPUSD --out dq.json

Checks per timeframe: range, duplicates, ordering, OHLC sanity on both sides, bid <= ask, spread distribution,
5m completeness against the bot's own market hours (missing open slots listed as gap runs), 1h vs the 5m candles it
should be built from, and 4h buildability with the planner's own four_hour_from_hourly. Nothing is repaired.
"""
from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from config.settings_loader import load_settings
from planner.measure import four_hour_from_hourly
from prices.calendar import Boundaries, MarketHours
from prices.store import CandleStore

UTC = timezone.utc


def _sanity(c) -> list[str]:
    bad = []
    for side in ("buy", "sell"):
        o, h, l, cl = (getattr(c, f"{side}_{k}") for k in ("open", "high", "low", "close"))
        if not (l <= min(o, cl) and h >= max(o, cl) and l <= h):
            bad.append(f"{side} OHLC")
    if c.buy_close < c.sell_close or c.buy_low < c.sell_low:
        bad.append("ask below bid")
    return bad


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    settings = load_settings().for_pair("GBPUSD")
    store = CandleStore(a.store, settings.candles.compress_after_days)
    hours = MarketHours(settings.market_hours)
    out: dict = {"store": str(a.store), "timeframes": {}}
    loaded = {}
    for tf in ("5m", "1h", "4h", "1d", "1w"):
        days = store.days(tf)
        cs = [c for d in days for c in store.read_day(tf, d)]
        loaded[tf] = cs
        if not cs:
            out["timeframes"][tf] = {"candles": 0, "note": "not stored"}
            continue
        starts = [c.start for c in cs]
        dup = [k.isoformat() for k, n in Counter(starts).items() if n > 1]
        unordered = sum(1 for x, y in zip(starts, starts[1:]) if y <= x)
        insane = Counter(b for c in cs for b in _sanity(c))
        spreads = [float(c.buy_close - c.sell_close) for c in cs]
        partial = sum(1 for c in cs if c.parts is not None and c.expected_parts and c.parts < c.expected_parts)
        tz_bad = sum(1 for c in cs if c.start.utcoffset() != timedelta(0))
        out["timeframes"][tf] = {
            "candles": len(cs), "files": len(days), "first": cs[0].start.isoformat(), "last_end": cs[-1].end.isoformat(),
            "duplicates": len(dup), "duplicate_examples": dup[:5], "out_of_order": unordered,
            "ohlc_or_side_problems": dict(insane), "partial_candles(parts<expected)": partial,
            "non_utc_timestamps": tz_bad,
            "spread_points_median": statistics.median(spreads), "spread_points_p95": sorted(spreads)[int(.95 * len(spreads))],
            "spread_points_min": min(spreads), "spread_points_max": max(spreads),
        }
    # 5m completeness against market hours, by month, with gap runs
    five = loaded["5m"]
    have = {c.start for c in five}
    t0, t1 = five[0].start, five[-1].end
    expected = [s for s in hours.open_slots(t0, t1)]
    missing = [s for s in expected if s not in have]
    extra = sorted(have - set(expected))
    by_month = defaultdict(lambda: [0, 0])
    for s in expected:
        by_month[s.strftime("%Y-%m")][0] += 1
    for s in missing:
        by_month[s.strftime("%Y-%m")][1] += 1
    runs = []
    for s in missing:
        if runs and s - runs[-1][1] <= timedelta(minutes=5):
            runs[-1][1] = s
        else:
            runs.append([s, s])
    runs = [{"from": r[0].isoformat(), "to_last_missing": r[1].isoformat(),
             "slots": int((r[1] - r[0]) / timedelta(minutes=5)) + 1} for r in runs]
    big = [r for r in runs if r["slots"] >= 12]
    out["m5_completeness"] = {
        "expected_open_slots": len(expected), "present": len(expected) - len(missing), "missing": len(missing),
        "pct_present": round(100 * (1 - len(missing) / len(expected)), 2),
        "candles_outside_market_hours": len(extra), "outside_examples": [e.isoformat() for e in extra[:5]],
        "by_month": {m: {"expected": e, "missing": x, "pct_present": round(100 * (1 - x / e), 1)}
                     for m, (e, x) in sorted(by_month.items())},
        "gap_runs_total": len(runs), "gap_runs_ge_1h": len(big), "gap_runs_ge_1h_list": big,
    }
    # 1h consistency vs its 5m parts (sell side)
    fives_by_hour = defaultdict(list)
    for c in five:
        fives_by_hour[c.start.replace(minute=0)].append(c)
    mism, checked, worst = 0, 0, []
    for c in loaded["1h"]:
        parts = fives_by_hour.get(c.start)
        if not parts or len(parts) != 12:
            continue
        checked += 1
        hi = max(p.sell_high for p in parts); lo = min(p.sell_low for p in parts)
        d = max(abs(hi - c.sell_high), abs(lo - c.sell_low), abs(parts[-1].sell_close - c.sell_close))
        if d > Decimal("0.05"):
            mism += 1
            worst.append((float(d), c.start.isoformat()))
    out["h1_vs_m5"] = {"complete_hours_checked": checked, "mismatched": mism,
                       "worst": sorted(worst, reverse=True)[:5]}
    hourly_have = {c.start for c in loaded["1h"]}
    hourly_expected = sorted({s.replace(minute=0) for s in expected})
    out["h1_completeness"] = {"expected_open_hours": len(hourly_expected),
                              "missing": sum(1 for h in hourly_expected if h not in hourly_have)}
    # 4h: the planner builds 4h from hourly; count buildable vs dropped buckets
    four = four_hour_from_hourly(settings, loaded["1h"], loaded["1h"][-1].end)
    b = Boundaries(settings.candles, hours)
    buckets = {b.bucket("4h", h) for h in hourly_expected}
    out["h4_from_h1"] = {"expected_buckets": len(buckets), "built_complete": len(four),
                         "dropped_incomplete": len(buckets) - len(four),
                         "note": "planner/measure.py four_hour_from_hourly drops any 4h bucket missing an open hour"}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "m5_completeness"}, indent=1, default=str)[:4000])
    m = out["m5_completeness"]
    print({k: m[k] for k in ("expected_open_slots", "missing", "pct_present", "gap_runs_total", "gap_runs_ge_1h",
                             "candles_outside_market_hours")})


if __name__ == "__main__":
    main()
