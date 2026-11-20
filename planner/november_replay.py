"""Read-only historical STP snapshots for 9 and 10 November 2026.

Usage on AutoBot server, from repository root:
    python -m planner.november_replay --output /tmp/stp_nov_9_10.json

Uses the genuine server candle store. Never connects to IG, submits orders,
changes services or uses future candles in the planner decision.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone, date, timedelta
from pathlib import Path

from config.settings_loader import load_settings
from planner.assess import plan_at
from planner.forward_outcomes import score_journey
from planner.target_outcomes import score_target_ladder
from prices.store import CandleStore


TIMES = (
    "2026-11-09T07:00:00+00:00",
    "2026-11-09T09:00:00+00:00",
    "2026-11-09T12:00:00+00:00",
    "2026-11-10T07:00:00+00:00",
    "2026-11-10T09:00:00+00:00",
    "2026-11-10T12:00:00+00:00",
)


def assessment_times(start_date=None, end_date=None):
    """UTC weekday checkpoints; retain the original six cases by default."""
    if start_date is None and end_date is None:
        return TIMES
    if not start_date or not end_date:
        raise ValueError("both start_date and end_date are required")
    start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
    if end < start or (end - start).days > 90:
        raise ValueError("date range must be ordered and at most 91 calendar days")
    checkpoints = []
    day = start
    while day <= end:
        if day.weekday() < 5:
            checkpoints.extend(
                f"{day.isoformat()}T{hour:02d}:00:00+00:00"
                for hour in (7, 9, 12)
            )
        day += timedelta(days=1)
    return tuple(checkpoints)


def replay(settings, store, *, start_date=None, end_date=None):
    rows = []
    for raw in assessment_times(start_date, end_date):
        at = datetime.fromisoformat(raw)
        # Snapshot is generated as of each historic timestamp, not today.
        plan = plan_at(settings, store, at, calendar=[]).as_dict()
        future_end = at.replace(tzinfo=timezone.utc)
        future_end += timedelta(hours=24)
        future = [
            c for tf in ("5m", "1h", "4h")
            for c in store.read_range(tf, at, future_end)
            if c.start >= at and c.end <= future_end
        ]
        outcome = score_journey(plan, future, require_contiguous_m5=True)
        ladder = (plan.get("observations") or {}).get("target_ladder") or {}
        target_outcome = score_target_ladder(
            ladder, future, at, plan.get("trade"), require_contiguous_m5=True
        )
        rows.append({
            "assessment_utc": raw,
            "fresh": plan.get("fresh"),
            "direction": plan.get("trade"),
            "condition": plan.get("condition"),
            "entry_zone": plan.get("entry_zone"),
            "destinations": plan.get("destinations"),
            "invalidation": plan.get("invalidation"),
            "observations": plan.get("observations"),
            "no_recommendation": plan.get("no_recommendation"),
            "outcome_24h": outcome,
            "target_outcome_24h": target_outcome,
            "plan": plan,
        })
    return {"source": "actual AutoBot candle store, as-of historical replay",
            "execution": "none; offline structural assessment only",
            "assessments": rows, "target_summary": target_summary(rows),
            "daily_target_summary": daily_target_summary(rows)}


def target_summary(rows):
    """Counts forecast coverage and observed hits without treating absent forecasts as misses."""
    result = {}
    for name in ("immediate", "preferred", "extended"):
        counts = {"forecast": 0, "reached": 0, "not_reached": 0,
                  "data_gap_censored": 0, "not_forecast": 0, "not_scorable": 0}
        for row in rows:
            target = ((row.get("observations") or {}).get("target_ladder") or {}).get(name)
            if target is None:
                counts["not_forecast"] += 1
                continue
            counts["forecast"] += 1
            outcome = row.get("target_outcome_24h") or {}
            status = (outcome.get("targets") or {}).get(name, {}).get("status")
            if status == "REACHED":
                counts["reached"] += 1
            elif status == "NOT_REACHED":
                counts["not_reached"] += 1
            elif status == "DATA_GAP_CENSORED" or outcome.get("status") == "DATA_GAP_CENSORED":
                counts["data_gap_censored"] += 1
            else:
                counts["not_scorable"] += 1
        result[name] = counts
    return result


def daily_target_summary(rows):
    """Daily buckets keep correlated intraday observations visible."""
    days = sorted({row["assessment_utc"][:10] for row in rows})
    return {
        day: target_summary([row for row in rows
                             if row["assessment_utc"].startswith(day)])
        for day in days
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("/tmp/stp_nov_9_10.json"))
    parser.add_argument("--start-date", help="inclusive UTC date YYYY-MM-DD")
    parser.add_argument("--end-date", help="inclusive UTC date YYYY-MM-DD")
    args = parser.parse_args()
    if bool(args.start_date) != bool(args.end_date):
        parser.error("--start-date and --end-date must be provided together")
    try:
        assessment_times(args.start_date, args.end_date)
    except ValueError as exc:
        parser.error(str(exc))
    settings = load_settings().for_pair("GBPUSD")
    store = CandleStore(settings.candles.folder, settings.candles.compress_after_days)
    result = replay(settings, store, start_date=args.start_date, end_date=args.end_date)
    args.output.write_text(json.dumps(result, indent=2, default=str) + "\n")
    print(f"Saved {len(result['assessments'])} historical snapshots to {args.output}")
    print("Target summary:", json.dumps(result["target_summary"], sort_keys=True))
    print("Daily target summary:", json.dumps(result["daily_target_summary"], sort_keys=True))
    for row in result["assessments"]:
        target = (row["destinations"] or {}).get("primary")
        print(row["assessment_utc"], "direction=", row["direction"],
              "entry=", row["entry_zone"], "target=", target,
              "outcome=", row["outcome_24h"]["status"],
              "targets=", row["target_outcome_24h"].get("targets",
                         row["target_outcome_24h"]["status"]),
              "forecast_diagnostic=", ((row.get("observations") or {}).get("target_ladder") or {}).get("diagnostic"),
              "research_status=", ((row.get("observations") or {}).get("target_ladder") or {}).get("research_status"))


if __name__ == "__main__":
    main()
