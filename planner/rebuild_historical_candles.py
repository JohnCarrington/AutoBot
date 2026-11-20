"""Rebuild imported historical candles on AutoBot's native boundaries and IG point scale.

Research-only: source and destination MUST be distinct, destination empty.
Reads ONLY imported 5m candles; recomputes 1h/4h/1d/1w using live
Boundaries and MarketHours. Never modifies production data or contacts IG.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
from collections import Counter
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from config.settings_loader import load_settings
from prices.calendar import Boundaries, MarketHours
from prices.model import Candle, build_from, parse_iso
from prices.store import COLUMNS, CandleStore


def rebuild(source: Path, dest: Path, settings):
    source, dest = Path(source).resolve(), Path(dest).resolve()
    if source == dest or source in dest.parents or dest in source.parents:
        raise ValueError("source and destination must be separate")
    if dest.exists() and any(dest.iterdir()):
        raise FileExistsError("destination must be empty")
    source_store = CandleStore(source, 999999)
    output = CandleStore(dest, 999999)
    boundaries = Boundaries(settings.candles, MarketHours(settings.market_hours))
    scale = Decimal(settings.market.price_scale)
    active = {}
    day_rows = {}
    counts = Counter()
    incomplete = Counter()
    prev = None

    def write(c):
        day = c.start.date()
        key = (c.timeframe, day)
        if key not in day_rows:
            day_rows[key] = []
        day_rows[key].append(c)
        counts[c.timeframe] += 1
        if c.parts < c.expected_parts:
            incomplete[c.timeframe] += 1

    def finish(tf):
        item = active.pop(tf, None)
        if item is None:
            return
        start, end, parts = item
        expected = boundaries.expected_parts(start, end)
        if not expected:
            return
        write(build_from(tf, start, end, parts, expected))

    def flush_days(current_day):
        for (tf, day), rows in list(day_rows.items()):
            if day < current_day:
                output._write_day(tf, day, rows)
                del day_rows[(tf, day)]

    for day in source_store.days("5m"):
        for c in source_store.read_day("5m", day):
            if prev is not None and c.start <= prev:
                raise ValueError("duplicate/out-of-order 5m candle")
            prev = c.start
            # Validate imported candles before converting to IG points.
            if c.end <= c.start or c.end != c.start + __import__("datetime").timedelta(minutes=5):
                raise ValueError(f"invalid 5m interval: {c.start}")
            if not boundaries.hours.is_open(c.start):
                counts["outside_market_hours"] += 1
                continue
            scaled = replace(c, **{f: getattr(c, f) * scale for f in
                ("buy_open","buy_high","buy_low","buy_close",
                 "sell_open","sell_high","sell_low","sell_close")})
            write(scaled)
            for tf in ("1h", "4h", "1d", "1w"):
                start, end = boundaries.bucket(tf, scaled.start)
                existing = active.get(tf)
                if existing is not None and (existing[0], existing[1]) != (start, end):
                    finish(tf)
                    existing = None
                if existing is None:
                    active[tf] = (start, end, [])
                active[tf][2].append(scaled)
        # Weekly and daily buckets can be labelled earlier than current day.
        # Flush only when safely older than all possible open buckets.
        from datetime import timedelta
        flush_days(day - timedelta(days=9))
    for tf in ("1h", "4h", "1d", "1w"):
        finish(tf)
    for (tf, day), rows in sorted(day_rows.items()):
        output._write_day(tf, day, rows)
    report = {
        "source": str(source), "destination": str(dest),
        "price_scale": str(scale), "counts": dict(counts),
        "incomplete": dict(incomplete),
        "warning": "timestamp UTC assumption and market calendar need independent verification; incomplete periods must be censored",
    }
    (dest / "rebuild_manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    settings = load_settings().for_pair("GBPUSD")
    print(json.dumps(rebuild(args.source, args.output, settings), indent=2))


if __name__ == "__main__":
    main()
