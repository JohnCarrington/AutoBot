"""Collect STP plans at regular as-of times from a research candle store. READ ONLY; no IG, no orders.

  python -m research.stp_validation.collect --store S --start 2024-03-01 --end 2026-11-19 --stride-hours 4 --out plans.jsonl.gz
  python -m research.stp_validation.collect --store S --leak-check 20 --out leak.json

Each plan is planner.assess.plan_at(settings, store, as_of) exactly as the walk-forward audit calls it. Times are the
store's own 4-hour boundaries (prices.calendar.Boundaries, [candles] four_hour_starts_at) at which the market is open,
so every decision is made right after a 4-hour candle closes. The bulky 'structure' level map is dropped.

--leak-check N: for N random times, rebuild a store holding only candles that had FINISHED by as_of and compare the
plan with the one from the full store. Any difference means the planner read the future.
"""
from __future__ import annotations

import argparse
import gzip
import json
import random
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config.settings_loader import load_settings
from planner.assess import plan_at
from prices.calendar import Boundaries, MarketHours
from prices.store import CandleStore, _to_csv

UTC = timezone.utc


def as_of_times(settings, start: datetime, end: datetime, stride_hours: int) -> list[datetime]:
    """4-hour boundary times (the store's own boundaries) in [start, end), every stride_hours (a multiple of 4), at
    which the market was open during the previous hour."""
    if stride_hours % 4:
        raise ValueError("stride must be a multiple of 4 hours")
    hours = MarketHours(settings.market_hours)
    b = Boundaries(settings.candles, hours)
    out, t = [], start
    while t < end:
        if b.regular("4h", t)[0] == t and any(True for _ in hours.open_slots(t - timedelta(hours=1), t)):
            out.append(t)
        t += timedelta(hours=1)
    return out[:: stride_hours // 4]


def plan_row(settings, store, t: datetime) -> dict:
    p = plan_at(settings, store, t, calendar=[]).as_dict()
    p.pop("structure", None)
    return p


def truncated_store(src: Path, dst: Path, as_of: datetime, compress_after_days: int) -> CandleStore:
    full = CandleStore(src, compress_after_days)
    out = CandleStore(dst, 10_000)
    for tf in ("5m", "1h", "4h", "1d", "1w"):
        for d in full.days(tf):
            if d > as_of.date():
                continue
            keep = [c for c in full.read_day(tf, d) if c.end <= as_of]
            if keep:
                p = dst / tf / f"{d.isoformat()}.csv"
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(_to_csv(keep))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True, type=Path)
    ap.add_argument("--start", default="2024-03-01")
    ap.add_argument("--end", default="2026-11-19")
    ap.add_argument("--stride-hours", type=int, default=4)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--leak-check", type=int, default=0)
    ap.add_argument("--seed", type=int, default=20261120)
    a = ap.parse_args()
    settings = load_settings().for_pair("GBPUSD")
    store = CandleStore(a.store, settings.candles.compress_after_days)
    start = datetime.fromisoformat(a.start).replace(tzinfo=UTC)
    end = datetime.fromisoformat(a.end).replace(tzinfo=UTC)
    times = as_of_times(settings, start, end, a.stride_hours)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    if a.leak_check:
        rng = random.Random(a.seed)
        sample = sorted(rng.sample(times, a.leak_check))
        results = []
        for t in sample:
            full = plan_row(settings, store, t)
            tmp = Path(tempfile.mkdtemp(prefix="stp_leak_"))
            try:
                cut = truncated_store(a.store, tmp / "GBPUSD", t, settings.candles.compress_after_days)
                part = plan_row(settings, cut, t)
            finally:
                shutil.rmtree(tmp)
            diff = sorted(k for k in set(full) | set(part) if full.get(k) != part.get(k))
            results.append({"as_of_utc": t.isoformat(), "identical": not diff, "differing_keys": diff,
                            "direction": full["dominant_direction"], "trade": full["trade"]})
            print(results[-1], flush=True)
        a.out.write_text(json.dumps({"checked": len(results), "identical": sum(r["identical"] for r in results),
                                     "results": results}, indent=1) + "\n")
        return
    with gzip.open(a.out, "wt") as f:
        for i, t in enumerate(times):
            try:
                row = plan_row(settings, store, t)
            except Exception as e:                       # noqa: BLE001  (recorded, never hidden)
                row = {"as_of_utc": t.isoformat(), "error": f"{type(e).__name__}: {e}"}
            f.write(json.dumps(row, default=str) + "\n")
            if i % 200 == 0:
                print(i, len(times), t.isoformat(), flush=True)


if __name__ == "__main__":
    main()
