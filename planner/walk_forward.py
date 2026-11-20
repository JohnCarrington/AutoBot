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
from prices.model import parse_iso
from prices.store import CandleStore


def audit(settings, store, start: datetime, end: datetime, stride: timedelta,
          horizon: timedelta) -> dict:
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
        plan = plan_at(settings, store, at, calendar=[]).as_dict()
        if not plan["fresh"]:
            rows.append({"as_of_utc": at.isoformat(), "status": "STALE_DATA"})
        elif plan["entry_zone"] is None:
            rows.append({"as_of_utc": at.isoformat(), "status": "NO_PLAN",
                         "reason": plan["no_recommendation"]})
        else:
            future = [c for c in store.read_range("5m", at, at + horizon)
                      if c.start >= at and c.end <= at + horizon]
            result = score_journey(plan, future)
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
    args = parser.parse_args()
    start = datetime.fromisoformat(args.start).replace(tzinfo=timezone.utc)
    end = datetime.fromisoformat(args.end).replace(tzinfo=timezone.utc)
    settings = load_settings().for_pair("GBPUSD")
    store = CandleStore(settings.candles.folder, settings.candles.compress_after_days)
    result = audit(settings, store, start, end, timedelta(hours=args.stride_hours),
                   timedelta(hours=args.horizon_hours))
    data = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(data + "\n")
        print(f"wrote {args.output} ({len(result['samples'])} samples)")
    else:
        print(data)


if __name__ == "__main__":
    main()
