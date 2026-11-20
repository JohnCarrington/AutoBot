"""Read-only STP rejection audit: every hourly checkpoint, 18-20 November 2026.

Run from repository root with the same settings/candle store as STP:
    python -m planner.recommendation_audit --output /tmp/stp_rejections_20261118_20.json
Never contacts the broker, changes services, or writes into production storage.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config.settings_loader import load_settings
from planner.assess import plan_at
from prices.store import CandleStore


def checkpoints(start, end):
    at = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
    stop = datetime.fromisoformat(end).replace(tzinfo=timezone.utc)
    if stop < at:
        raise ValueError("end precedes start")
    while at <= stop:
        yield at
        at += timedelta(hours=1)


def audit(settings, store, start, end):
    rows = []
    for at in checkpoints(start, end):
        try:
            plan = plan_at(settings, store, at, calendar=[]).as_dict()
            obs = plan.get("observations") or {}
            journeys = obs.get("conditional_journeys") or []
            row = {
                "time_utc": at.isoformat(),
                "fresh": plan.get("fresh"),
                "direction": plan.get("direction"),
                "condition": plan.get("condition"),
                "opportunity": plan.get("opportunity"),
                "recommendation": plan.get("no_recommendation") is None,
                "rejection": plan.get("no_recommendation"),
                "entry_zone": plan.get("entry_zone"),
                "destinations": plan.get("destinations"),
                "candidates": plan.get("candidates"),
                "journeys": journeys,
                "major_zones": [z for z in (plan.get("structure") or {}).get("zones", [])
                                if z.get("class") == "Major"],
            }
        except Exception as exc:
            row = {"time_utc": at.isoformat(), "error": repr(exc)}
        rows.append(row)
    counts = Counter(
        "ERROR: " + r["error"] if "error" in r else
        "RECOMMENDATION" if r["recommendation"] else
        r["rejection"] or "UNKNOWN"
        for r in rows
    )
    return {"period_utc": [start, end], "assessments": rows,
            "reason_counts": dict(counts), "read_only": True}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--start", default="2026-11-18T00:00:00")
    p.add_argument("--end", default="2026-11-20T08:00:00")
    p.add_argument("--output", type=Path, default=Path("/tmp/stp_rejections_20261118_20.json"))
    args = p.parse_args()
    settings = load_settings().for_pair("GBPUSD")
    store = CandleStore(settings.candles.folder, settings.candles.compress_after_days)
    report = audit(settings, store, args.start, args.end)
    args.output.write_text(json.dumps(report, indent=2, default=str) + "\n")
    print("REJECTION COUNTS:", json.dumps(report["reason_counts"], indent=2))
    for row in report["assessments"]:
        print(row["time_utc"], "YES" if row.get("recommendation") else "NO",
              row.get("rejection") or row.get("error") or "",
              "major_zones=", len(row.get("major_zones", [])),
              "journeys=", len(row.get("journeys", [])))
    print("DETAILS:", args.output)


if __name__ == "__main__":
    main()
