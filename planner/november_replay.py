"""Read-only historical STP snapshots for 9 and 10 November 2026.

Usage on AutoBot server, from repository root:
    python -m planner.november_replay --output /tmp/stp_nov_9_10.json

Uses the genuine server candle store. Never connects to IG, submits orders,
changes services or uses future candles in the planner decision.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from config.settings_loader import load_settings
from planner.assess import plan_at
from planner.forward_outcomes import score_journey
from prices.store import CandleStore


TIMES = (
    "2026-11-09T07:00:00+00:00",
    "2026-11-09T09:00:00+00:00",
    "2026-11-09T12:00:00+00:00",
    "2026-11-10T07:00:00+00:00",
    "2026-11-10T09:00:00+00:00",
    "2026-11-10T12:00:00+00:00",
)


def replay(settings, store):
    rows = []
    for raw in TIMES:
        at = datetime.fromisoformat(raw)
        # Snapshot is generated as of each historic timestamp, not today.
        plan = plan_at(settings, store, at, calendar=[]).as_dict()
        future_end = at.replace(tzinfo=timezone.utc)
        from datetime import timedelta
        future_end += timedelta(hours=24)
        future = [
            c for tf in ("5m", "1h", "4h")
            for c in store.read_range(tf, at, future_end)
            if c.start >= at and c.end <= future_end
        ]
        outcome = score_journey(plan, future, require_contiguous_m5=True)
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
            "plan": plan,
        })
    return {"source": "actual AutoBot candle store, as-of historical replay",
            "execution": "none; offline structural assessment only",
            "assessments": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("/tmp/stp_nov_9_10.json"))
    args = parser.parse_args()
    settings = load_settings().for_pair("GBPUSD")
    store = CandleStore(settings.candles.folder, settings.candles.compress_after_days)
    result = replay(settings, store)
    args.output.write_text(json.dumps(result, indent=2, default=str) + "\n")
    print(f"Saved {len(result['assessments'])} historical snapshots to {args.output}")
    for row in result["assessments"]:
        target = (row["destinations"] or {}).get("primary")
        print(row["assessment_utc"], "direction=", row["direction"],
              "entry=", row["entry_zone"], "target=", target,
              "outcome=", row["outcome_24h"]["status"])


if __name__ == "__main__":
    main()
