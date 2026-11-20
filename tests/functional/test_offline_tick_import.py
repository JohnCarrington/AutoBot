"""Offline tick import: native bid/ask candle and safe-file regressions."""
import csv
import gzip
from pathlib import Path

import pytest

from planner.offline_tick_import import convert


def test_small_tick_stream(tmp_path):
    source = tmp_path / "ticks.csv"
    source.write_text(
        "timestamp,bid,ask,mid\n"
        "2025-01-06 00:00:01.000,1.25000,1.25020,1.25010\n"
        "2025-01-06 00:04:59.000,1.24990,1.25030,1.25010\n"
        "2025-01-06 00:05:01.000,1.25010,1.25040,1.25025\n"
    )
    out = tmp_path / "candles"
    result = convert([source], out)
    assert result["counts"]["5m"] == 2
    with gzip.open(out / "5m" / "2025-01-06.csv.gz", "rt", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    assert rows[0]["buy_high"] == "1.25030"
    assert rows[0]["sell_low"] == "1.24990"
    assert rows[0]["start_utc"] == "2025-01-06T00:00:00Z"
    assert rows[0]["end_utc"] == "2025-01-06T00:05:00Z"
    assert rows[0]["parts"] == "1"
    with gzip.open(out / "1h" / "2025-01-06.csv.gz", "rt", newline="") as f:
        hour = list(csv.DictReader(f))[0]
    assert hour["parts"] == "2"
    assert hour["expected_parts"] == "12"
    assert hour["buy_close"] == "1.25040"
    assert hour["sell_close"] == "1.25010"


def test_refuse_overwrite(tmp_path):
    source = tmp_path / "ticks.csv"
    source.write_text("timestamp,bid,ask,mid\n2025-01-06 00:00:01,1.25,1.26,1.255\n")
    out = tmp_path / "out"
    convert([source], out)
    with pytest.raises(FileExistsError):
        convert([source], out)


def test_out_of_order_ticks_rejected(tmp_path):
    source = tmp_path / "ticks.csv"
    source.write_text(
        "timestamp,bid,ask,mid\n"
        "2025-01-06 00:05:01,1.25,1.26,1.255\n"
        "2025-01-06 00:00:01,1.25,1.26,1.255\n"
    )
    with pytest.raises(ValueError, match="out of order"):
        convert([source], tmp_path / "out")
