"""Chronological replay of the STP technical forecast (planner/technical.py). READ ONLY.

  PYTHONPATH=. python -m research.stp_technical.replay --store S --start 2025-01-01 --end 2025-07-01 --every 2 --out F

At each UTC hour on the --every grid (+4 s, after the hourly candle) while the market is open, one snapshot is taken
from finished candles only and the forecast is made. Nothing after the decision time is read. Outcomes are scored
separately (research/stp_technical/score.py), after every forecast has been written.
"""
from __future__ import annotations

import argparse
import gzip
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config.settings_loader import load_settings
from planner.technical import technical_at
from prices.calendar import MarketHours
from prices.store import CandleStore

UTC = timezone.utc


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True, type=Path)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--every", type=int, default=2)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    s = load_settings().for_pair("GBPUSD")
    store = CandleStore(a.store, s.candles.compress_after_days)
    hours = MarketHours(s.market_hours)
    t = datetime.fromisoformat(a.start).replace(tzinfo=UTC) + timedelta(seconds=4)
    end = datetime.fromisoformat(a.end).replace(tzinfo=UTC)
    with gzip.open(a.out, "wt") as f:
        while t < end:
            if t.hour % a.every == 0 and hours.is_open(t) and hours.is_open(t - timedelta(hours=1)):
                try:
                    fc = technical_at(s, store, t)
                except Exception as e:                          # noqa: BLE001  recorded, never skipped silently
                    fc = {"as_of_utc": t.strftime("%Y-%m-%dT%H:%M:%SZ"), "error": f"{type(e).__name__}: {e}"}
                f.write(json.dumps(fc, default=str) + "\n")
                f.flush()
            t += timedelta(hours=1)
    print("done", a.out)


if __name__ == "__main__":
    main()
