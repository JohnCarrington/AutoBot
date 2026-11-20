"""Offline STP historical walk-forward audit. READ ONLY; no IG or orders.

Example:
  python -m planner.walk_forward --start 2026-10-25 --end 2026-11-17 --stride-hours 4

Each decision uses only candles available at its timestamp. Future M5 candles
are used solely by the outcome scorer, never by plan_at. No P&L is inferred.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config.settings_loader import load_settings
from planner.assess import plan_at
from planner.forward_outcomes import score_journey
from planner.measure import four_hour_from_hourly
from prices.calendar import MarketHours
from prices.store import CandleStore


def forward_candles(settings, store, start: datetime, end: datetime) -> list:
    """The finished 5m, 1h and 4h candles wholly inside [start, end] for outcome scoring. The 4-hour candles are built
    from the hourly ones with the planner's own four_hour_from_hourly (as the plan itself saw 4-hour structure), never
    read from a stored 4h folder: research stores have none, and a missing folder silently disabled the 4-hour
    structure-break invalidation (found in the 20 Nov 2026 historical validation)."""
    five = store.read_range("5m", start, end)
    hourly = store.read_range("1h", start - timedelta(hours=4), end)
    four = four_hour_from_hourly(settings, hourly, end)
    return [c for c in [*five, *hourly, *four] if c.start >= start and c.end <= end]


def open_slots_fn(settings, weekly_open_grace: timedelta = timedelta(0)):
    """5-minute starts the market was open for, by the bot's market hours, optionally skipping the first
    weekly_open_grace after each weekly open (a source that opens later than the bot's hours, e.g. the 2024-26
    vendor/IG 161 candles that start at 17:00 New York)."""
    hours = MarketHours(settings.market_hours)

    def slots(a: datetime, b: datetime):
        for s in hours.open_slots(a, b):
            if weekly_open_grace and s - hours.session(s)[0] < weekly_open_grace:
                continue
            yield s
    return slots


def audit(settings, store, start: datetime, end: datetime, stride: timedelta,
          horizon: timedelta, *, weekly_open_grace: timedelta = timedelta(0)) -> dict:
    if start.tzinfo is None or end.tzinfo is None or start >= end:
        raise ValueError("start/end must be timezone-aware, with start < end")
    if stride <= timedelta(0) or horizon <= timedelta(0):
        raise ValueError("stride and horizon must be positive")
    # The end of the requested audit must not exceed the actual stored history.
    newest = store.newest("5m")
    if newest is None:
        raise ValueError("no stored 5m candles")
    available_end = newest.end
    rows = []
    at = start
    while at < end:
        if at + horizon > available_end:
            rows.append({"as_of_utc": at.isoformat(), "status": "INSUFFICIENT_FUTURE_DATA"})
            at += stride
            continue
        hours = MarketHours(settings.market_hours)
        if not any(True for _ in hours.open_slots(at - timedelta(hours=1), at)):
            # The market was shut for the whole previous hour (weekend, holiday close): no decision is due, and a
            # window with no trading in it is not a data gap (found in the 20 Nov 2026 historical validation:
            # Saturday decisions were reported as DATA_GAP_CENSORED).
            rows.append({"as_of_utc": at.isoformat(), "status": "MARKET_CLOSED"})
            at += stride
            continue
        plan = plan_at(settings, store, at, calendar=[]).as_dict()
        if not plan["fresh"]:
            rows.append({"as_of_utc": at.isoformat(), "status": "STALE_DATA"})
        elif plan["entry_zone"] is None:
            rows.append({"as_of_utc": at.isoformat(), "status": "NO_PLAN",
                         "reason": plan["no_recommendation"]})
        else:
            future = forward_candles(settings, store, at, at + horizon)
            slots = open_slots_fn(settings, weekly_open_grace)
            result = score_journey(plan, future, require_contiguous_m5=True, open_slots=slots)
            if result["status"] in ("ENTRY_ONLY_CENSORED", "NEITHER_CENSORED"):
                m5 = [c for c in future if c.timeframe == "5m"]
                last = max((c.end for c in m5), default=at)
                if not m5 or any(True for _ in slots(last, at + horizon)):
                    result = {"status": "DATA_GAP_CENSORED",
                              "reason": "incomplete M5 coverage at end of observation window"}
            rows.append({"as_of_utc": at.isoformat(), "direction": plan["trade"],
                         "entry": plan["entry_zone"], "primary": plan["destinations"]["primary"],
                         "condition": plan["condition"], **result})
        at += stride
    return {
        "method": "read-only, as-of walk-forward structural sequence; no fills or P&L",
        "window_start": start.isoformat(), "window_end": end.isoformat(),
        "stride_hours": stride.total_seconds() / 3600,
        "horizon_hours": horizon.total_seconds() / 3600,
        "counts": dict(sorted(Counter(r["status"] for r in rows).items())),
        "samples": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", required=True, help="UTC date YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="UTC date YYYY-MM-DD, exclusive")
    parser.add_argument("--stride-hours", type=int, default=4)
    parser.add_argument("--horizon-hours", type=int, default=24)
    parser.add_argument("--output", type=Path, help="optional JSON output; otherwise stdout")
    parser.add_argument("--store", type=Path, help="candle store folder (default: [candles] folder); research stores")
    parser.add_argument("--weekly-open-grace-minutes", type=int, default=0,
                        help="ignore missing 5m candles this long after each weekly open (late-opening sources)")
    args = parser.parse_args()
    start = datetime.fromisoformat(args.start).replace(tzinfo=timezone.utc)
    end = datetime.fromisoformat(args.end).replace(tzinfo=timezone.utc)
    settings = load_settings().for_pair("GBPUSD")
    folder = args.store or settings.candles.folder
    store = CandleStore(folder, settings.candles.compress_after_days)
    result = audit(settings, store, start, end, timedelta(hours=args.stride_hours),
                   timedelta(hours=args.horizon_hours),
                   weekly_open_grace=timedelta(minutes=args.weekly_open_grace_minutes))
    data = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(data + "\n")
        print(f"wrote {args.output} ({len(result['samples'])} samples)")
    else:
        print(data)


if __name__ == "__main__":
    main()
