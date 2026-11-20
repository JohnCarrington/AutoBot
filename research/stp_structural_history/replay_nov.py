"""Replay the live planner over 17-20 November 2026 with the real keeper, in memory. READ ONLY.

  PYTHONPATH=<worktree> python research/stp_structural_history/replay_nov.py --out DIR [--historical-weeks N] [--until ISO]

The keeper runs every 5 minutes from 17 Nov 20:25 UTC (when the live planner started) to --until. It reads the
production candle store and writes only into DIR (the keeper's files plus hourly_plans.jsonl, every full hourly plan).
Run it from the production-equivalent worktree for the existing behaviour, and from this branch for the corrected one.
Never contacts IG and never touches the live planner folder.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config.settings_loader import load_settings
from planner.assess import plan_at
from planner.keeper import Keeper
from prices.model import parse_iso
from prices.store import CandleStore
from tests.planner_helpers import Over, section

UTC = timezone.utc
LIVE_STORE = "/opt/autobot/data/candles/GBPUSD"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--historical-weeks", type=int, default=None)
    ap.add_argument("--until", default=None)
    a = ap.parse_args()
    base = load_settings().for_pair("GBPUSD")
    changes = {"folder": a.out / "planner"}
    if a.historical_weeks is not None:
        changes["historical_daily_swing_lookback_weeks"] = a.historical_weeks
    s = Over(base, planner=section(base.planner, **changes))
    store = CandleStore(LIVE_STORE, base.candles.compress_after_days)
    until = parse_iso(a.until) if a.until else datetime.now(UTC).replace(second=0, microsecond=0)
    plans = (a.out / "hourly_plans.jsonl").open("w")

    def planner(settings, st, now, calendar=None):
        p = plan_at(settings, st, now) if calendar is None else plan_at(settings, st, now, calendar)
        plans.write(json.dumps(p.as_dict(), default=str) + "\n")
        return p

    t = datetime(2026, 11, 17, 20, 25, 3, tzinfo=UTC)
    while t <= until:
        Keeper(s, store, planner=planner).run(t)      # a fresh keeper each run, as the live subprocess
        t += timedelta(minutes=5)
    plans.close()
    print("done", until.isoformat())


if __name__ == "__main__":
    main()
