"""Offline tick CSV -> AutoBot-compatible bid/ask candle store.

Run on the *source* droplet with a copy of this script. Writes ONLY under
--output; never imports trading services, accesses IG, or edits input ticks.

Timestamp assumption: naive source timestamps represent UTC. Verify independently.
Input must be ordered chronologically. Incomplete intervals are retained and
reported, never filled with invented prices.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

UTC = timezone.utc
FIELDS = ("buy_open", "buy_high", "buy_low", "buy_close",
          "sell_open", "sell_high", "sell_low", "sell_close")
HEADER = ("start_utc", "end_utc", *FIELDS, "parts", "expected_parts")
SIZES = {"5m": 300, "1h": 3600, "4h": 14400, "1d": 86400, "1w": 604800}


def bucket(ts, tf):
    if tf == "1w":
        base = ts.replace(hour=0, minute=0, second=0, microsecond=0)
        return base - timedelta(days=base.weekday())
    seconds = SIZES[tf]
    epoch = int(ts.timestamp())
    return datetime.fromtimestamp(epoch - epoch % seconds, UTC)


def stamp(ts):
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_tick(row):
    ts = datetime.fromisoformat(row["timestamp"].strip()).replace(tzinfo=UTC)
    bid, ask = Decimal(row["bid"]), Decimal(row["ask"])
    if not (bid.is_finite() and ask.is_finite() and 0 < bid <= ask):
        raise ValueError("invalid bid/ask")
    return ts, bid, ask


class OHLC:
    def __init__(self, start, tf, bid, ask):
        self.start, self.tf = start, tf
        self.values = [ask, ask, ask, ask, bid, bid, bid, bid]
        self.parts = 0

    def update(self, bid, ask):
        v = self.values
        v[1], v[2], v[3] = max(v[1], ask), min(v[2], ask), ask
        v[5], v[6], v[7] = max(v[5], bid), min(v[6], bid), bid

    def absorb(self, other):
        v, w = self.values, other.values
        v[1], v[2], v[3] = max(v[1], w[1]), min(v[2], w[2]), w[3]
        v[5], v[6], v[7] = max(v[5], w[5]), min(v[6], w[6]), w[7]
        self.parts += 1

    def row(self):
        expected = 1 if self.tf == "5m" else SIZES[self.tf] // 300
        return [stamp(self.start), stamp(self.start + timedelta(seconds=SIZES[self.tf])),
                *(format(v, "f") for v in self.values), self.parts or 1, expected]


class Writer:
    def __init__(self, root):
        self.root = Path(root)
        self.handles = {}
        self.counts = Counter()

    def write(self, tf, row):
        day = row[0][:10]
        key = (tf, day)
        if key not in self.handles:
            directory = self.root / tf
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / (day + ".csv.gz")
            if path.exists():
                raise FileExistsError(f"refusing to overwrite {path}")
            handle = gzip.open(path, "wt", newline="")
            writer = csv.writer(handle, lineterminator="\\n")
            writer.writerow(HEADER)
            self.handles[key] = (handle, writer)
        self.handles[key][1].writerow(row)
        self.counts[tf] += 1

    def close(self):
        for handle, _ in self.handles.values():
            handle.close()
        self.handles.clear()


def convert(inputs, output):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("output directory must be new or empty")
    writer = Writer(output)
    current = None
    aggregates = {}
    quality = Counter()
    previous = None

    def emit_five(c):
        writer.write("5m", c.row())
        for tf in ("1h", "4h", "1d", "1w"):
            key = bucket(c.start, tf)
            old = aggregates.get(tf)
            if old is not None and old.start != key:
                writer.write(tf, old.row())
                old = None
            if old is None:
                old = OHLC(key, tf, c.values[4], c.values[0])
            old.absorb(c)
            aggregates[tf] = old

    try:
        for source in inputs:
            with open(source, newline="") as stream:
                reader = csv.DictReader(stream)
                if not {"timestamp", "bid", "ask", "mid"} <= set(reader.fieldnames or ()):
                    raise ValueError(f"wrong CSV header: {source}")
                for line, row in enumerate(reader, 2):
                    try:
                        ts, bid, ask = parse_tick(row)
                    except (ValueError, InvalidOperation) as exc:
                        quality["invalid_rows"] += 1
                        raise ValueError(f"{source}:{line}: {exc}") from exc
                    if previous is not None and ts < previous:
                        raise ValueError(f"{source}:{line}: timestamps out of order")
                    if previous is not None and ts == previous:
                        quality["duplicate_timestamps"] += 1
                    if bid == ask:
                        quality["zero_spread_ticks"] += 1
                    quality["ticks"] += 1
                    if "first_tick" not in quality:
                        pass
                    key = bucket(ts, "5m")
                    if current is None or key != current.start:
                        if current is not None:
                            emit_five(current)
                        current = OHLC(key, "5m", bid, ask)
                    else:
                        current.update(bid, ask)
                    previous = ts
        if current is not None:
            emit_five(current)
        for tf, c in aggregates.items():
            writer.write(tf, c.row())
    finally:
        writer.close()
    manifest = {
        "source": [str(p) for p in inputs],
        "timestamp_assumption": "source naive timestamps interpreted as UTC; unverified",
        "price_mapping": "buy=ask, sell=bid; mid ignored",
        "counts": dict(writer.counts),
        "quality": dict(quality),
        "last_tick_utc": stamp(previous) if previous else None,
        "warning": "incomplete sessions and candle gaps must be audited before replay",
    }
    (output / "import_manifest.json").write_text(json.dumps(manifest, indent=2) + "\\n")
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", nargs="+", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(convert(args.input, args.output), indent=2))


if __name__ == "__main__":
    main()
