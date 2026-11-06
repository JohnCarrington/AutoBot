"""The candle store: files per day per size, UTC times, buy and sell kept
apart, never overwritten, safe writes, compression without deleting."""

import gzip
import os
from decimal import Decimal

import pytest

from prices import store as store_mod
from prices.store import COLUMNS, CandleStore, DamagedFile
from tests.technical.fake_stream import T, five


@pytest.fixture
def warnings():
    return []


@pytest.fixture
def store(tmp_path, warnings):
    return CandleStore(tmp_path / "candles", 30, warn=warnings.append)


def test_one_file_per_day_per_candle_size_named_by_utc_date(store, tmp_path):
    store.add(five(T(2026, 11, 4, 23, 55)))
    store.add(five(T(2026, 11, 5, 0, 0)))
    store.add(five(T(2026, 11, 4, 22, 0), tf="1h", minutes=60))
    files = sorted(p.relative_to(tmp_path / "candles").as_posix() for p in (tmp_path / "candles").rglob("*.csv"))
    assert files == ["1h/2026-11-04.csv", "5m/2026-11-04.csv", "5m/2026-11-05.csv"]


def test_times_are_stored_in_utc_and_buy_and_sell_are_kept_apart(store, tmp_path):
    store.add(five(T(2026, 7, 6, 9, 0)))   # summer: UK time is 10:00 BST, stored as 09:00Z
    text = (tmp_path / "candles" / "5m" / "2026-07-06.csv").read_text().splitlines()
    assert text[0].split(",") == list(COLUMNS)
    assert "mid" not in text[0]
    assert text[1] == ("2026-07-06T09:00:00Z,2026-07-06T09:05:00Z,"
                       "1.31010,1.31060,1.30960,1.31030,1.31000,1.31050,1.30950,1.31020,1,1")


def test_prices_are_kept_exactly(store):
    store.add(five(T(2026, 11, 4, 10, 0), bo="1.312345", sc="1.30001"))
    c = store.newest("5m")
    assert c.buy_open == Decimal("1.312345") and c.sell_close == Decimal("1.30001")


def test_a_stored_candle_is_never_overwritten_and_a_different_value_is_warned(store, warnings, tmp_path):
    start = T(2026, 11, 4, 10, 0)
    assert store.add(five(start)) == "stored"
    before = (tmp_path / "candles" / "5m" / "2026-11-04.csv").read_bytes()
    assert store.add(five(start, bc="1.39999")) == "different"
    assert (tmp_path / "candles" / "5m" / "2026-11-04.csv").read_bytes() == before
    assert str(store.get("5m", start).buy_close) == "1.31030"
    assert len(warnings) == 1 and "DIFFERENT VALUE" in warnings[0] and "kept the stored one" in warnings[0]


def test_the_same_candle_arriving_again_is_not_written_or_warned(store, warnings, tmp_path, monkeypatch):
    start = T(2026, 11, 4, 10, 0)
    store.add(five(start))
    monkeypatch.setattr(store_mod, "safe_write", lambda *a: pytest.fail("must not write"))
    assert store.add(five(start)) == "same"
    assert warnings == []


def test_crash_part_way_through_a_write_leaves_the_old_file_whole(store, tmp_path, monkeypatch):
    store.add(five(T(2026, 11, 4, 10, 0)))
    path = tmp_path / "candles" / "5m" / "2026-11-04.csv"
    before = path.read_bytes()

    real_open = open

    class Crash(Exception):
        pass

    def crashing_open(file, mode="r", *a, **kw):
        f = real_open(file, mode, *a, **kw)
        if "w" in mode and store_mod.TMP_MARK in str(file):
            real_write = f.write

            def half_write(data):
                real_write(data[: len(data) // 2])  # half the file reaches the disk...
                raise Crash("power cut")           # ...then the power goes
            f.write = half_write
        return f

    monkeypatch.setattr("builtins.open", crashing_open)
    with pytest.raises(Crash):
        store.add(five(T(2026, 11, 4, 10, 5)))
    monkeypatch.undo()

    assert path.read_bytes() == before                     # the real file is untouched
    assert [c.start for c in store.read_day("5m", T(2026, 11, 4).date())] == [T(2026, 11, 4, 10, 0)]
    leftovers = list(path.parent.glob(f"*{store_mod.TMP_MARK}*"))
    assert leftovers                                        # a half-written temp file was left
    assert store.days("5m") == [T(2026, 11, 4).date()]      # and is ignored when reading
    assert store.remove_leftover_temp_files() == 1          # and removed at start-up
    assert store.add(five(T(2026, 11, 4, 10, 5))) == "stored"


def test_crash_between_writing_and_renaming_leaves_the_old_file_whole(store, tmp_path, monkeypatch):
    store.add(five(T(2026, 11, 4, 10, 0)))
    path = tmp_path / "candles" / "5m" / "2026-11-04.csv"
    before = path.read_bytes()

    def no_rename(*a):
        raise OSError("power cut before rename")
    monkeypatch.setattr(store_mod.os, "replace", no_rename)
    with pytest.raises(OSError):
        store.add(five(T(2026, 11, 4, 10, 5)))
    monkeypatch.undo()
    assert path.read_bytes() == before


def test_writes_are_flushed_to_disk_before_the_rename(store, monkeypatch):
    order = []
    real_fsync, real_replace = os.fsync, os.replace
    monkeypatch.setattr(store_mod.os, "fsync", lambda fd: (order.append("fsync"), real_fsync(fd)))
    monkeypatch.setattr(store_mod.os, "replace", lambda a, b: (order.append("rename"), real_replace(a, b)))
    store.add(five(T(2026, 11, 4, 10, 0)))
    assert order == ["fsync", "rename", "fsync"]   # file data, rename, then the folder


def test_a_damaged_file_is_reported_and_never_written_over(store, tmp_path):
    path = tmp_path / "candles" / "5m" / "2026-11-04.csv"
    path.parent.mkdir(parents=True)
    path.write_text("start_utc,end_utc\ngarbage")
    with pytest.raises(DamagedFile):
        store.add(five(T(2026, 11, 4, 10, 0)))
    assert path.read_text() == "start_utc,end_utc\ngarbage"


def test_old_files_are_compressed_not_deleted_and_still_readable(store, tmp_path):
    old, recent = T(2026, 9, 1, 10, 0), T(2026, 11, 1, 22, 0)
    store.add(five(old))
    store.add(five(recent))
    n = store.compress_old(T(2026, 11, 6, 12, 0))   # 30 days in the settings used here
    assert n == 1
    folder = tmp_path / "candles" / "5m"
    assert not (folder / "2026-09-01.csv").exists()
    assert (folder / "2026-09-01.csv.gz").exists()
    assert (folder / "2026-11-01.csv").exists()
    assert store.get("5m", old).start == old
    assert gzip.decompress((folder / "2026-09-01.csv.gz").read_bytes()).startswith(b"start_utc")
    assert store.add(five(old, bc="1.5")) == "different"   # still never overwritten when compressed
    assert store.add(five(old + (T(2026, 1, 1, 0, 5) - T(2026, 1, 1)))) == "stored"
    assert len(store.read_day("5m", old.date())) == 2


def test_compress_after_days_comes_from_the_settings_file():
    from tests.technical.fake_stream import SETTINGS
    assert SETTINGS.candles.compress_after_days == 30


def test_gaps_are_recorded_safely(store):
    store.record_gap("5m", T(2026, 11, 4, 10), T(2026, 11, 4, 12), 24, T(2026, 11, 4, 12, 1), "test")
    store.record_gap("5m", T(2026, 11, 5, 10), T(2026, 11, 5, 10, 5), 1, T(2026, 11, 5, 11), "test")
    rows = store.recorded_gaps()
    assert [r["missing_candles"] for r in rows] == ["24", "1"]
    assert rows[0]["from_utc"] == "2026-11-04T10:00:00Z"
