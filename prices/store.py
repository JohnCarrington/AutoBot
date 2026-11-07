"""The candle store: one CSV file per day per candle size.

    <folder>/<size>/<YYYY-MM-DD>.csv      (the UTC date of each candle's start)
    <folder>/<size>/<YYYY-MM-DD>.csv.gz   (the same, once compressed)
    <folder>/gaps.csv                     (every gap found, kept as a record)

Rules:
  * A stored candle is never overwritten. If a different value arrives for a
    stored candle, the stored one is kept and a warning is written.
    The ONE exception (replace_with_fuller): a bigger candle (1h, 4h, 1d, 1w)
    built from an incomplete set of 5-minute candles is rebuilt from the fuller
    set after a gap fill. The old one is archived first
    (archive_rebuilt/<size>/<UTC date>.csv, with when and why), never deleted.
    A 5-minute candle is never replaced.
  * Every write is safe: the new file is written in full to a temporary file
    in the same folder, flushed to disk, then renamed over the old one in one
    step. A crash or power cut leaves either the old file or the new file,
    never a damaged one. Leftover temporary files are removed at start-up.
  * Candles are never deleted. Files older than compress_after_days are
    compressed (gzip), using the same safe-write steps.
"""

from __future__ import annotations

import csv
import gzip
import io
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable, Iterable

from housekeeping.files import TMP_MARK, safe_write
from housekeeping.files import fsync_dir as _fsync_dir
from prices.model import (PRICE_FIELDS, TIMEFRAMES, UTC, Candle, iso, parse_iso,
                          plain, price, uk_short)

log = logging.getLogger("autobot.prices.store")
BUILT_SIZES = ("1h", "4h", "1d", "1w")

COLUMNS = ("start_utc", "end_utc") + PRICE_FIELDS + ("parts", "expected_parts")
GAP_COLUMNS = ("timeframe", "from_utc", "to_utc", "missing_candles", "found_utc", "how_found", "note")
GAP_REQUIRED = GAP_COLUMNS[:6]   # "note" was added later; older files without it still read


class DamagedFile(Exception):
    """A store file cannot be read. It is left exactly as it is."""


def _to_csv(candles: Iterable[Candle]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(COLUMNS)
    for c in candles:
        w.writerow([iso(c.start), iso(c.end), *(plain(p) for p in c.prices()), c.parts, c.expected_parts])
    return buf.getvalue().encode()


def _from_csv(tf: str, data: bytes, where: str) -> list[Candle]:
    try:
        rows = list(csv.reader(io.StringIO(data.decode())))
    except Exception as e:
        raise DamagedFile(f"{where}: cannot be read ({e})") from None
    if not rows or tuple(rows[0]) != COLUMNS:
        raise DamagedFile(f"{where}: missing or wrong header line")
    out = []
    for n, row in enumerate(rows[1:], start=2):
        if len(row) != len(COLUMNS):
            raise DamagedFile(f"{where}: line {n} has {len(row)} values, expected {len(COLUMNS)}")
        try:
            out.append(Candle(tf, parse_iso(row[0]), parse_iso(row[1]),
                              *(price(v) for v in row[2:10]), parts=int(row[10]), expected_parts=int(row[11])))
        except ValueError as e:
            raise DamagedFile(f"{where}: line {n}: {e}") from None
    return out


class CandleStore:
    def __init__(self, folder: Path, compress_after_days: int, *,
                 warn: Callable[[str], None] | None = None):
        self.folder = Path(folder)
        self.compress_after_days = compress_after_days
        self.warn = warn or (lambda m: log.warning(m))

    # ---- files ------------------------------------------------------------

    def _plain(self, tf: str, day: date) -> Path:
        return self.folder / tf / f"{day.isoformat()}.csv"

    def _gz(self, tf: str, day: date) -> Path:
        return self.folder / tf / f"{day.isoformat()}.csv.gz"

    def days(self, tf: str) -> list[date]:
        d = self.folder / tf
        if not d.is_dir():
            return []
        found = set()
        for p in d.iterdir():
            if TMP_MARK in p.name:
                continue
            name = p.name.removesuffix(".gz").removesuffix(".csv")
            try:
                found.add(date.fromisoformat(name))
            except ValueError:
                continue
        return sorted(found)

    def read_day(self, tf: str, day: date) -> list[Candle]:
        """The candles in one day's file, as stored (not re-sorted)."""
        p, g = self._plain(tf, day), self._gz(tf, day)
        if p.exists():
            return _from_csv(tf, p.read_bytes(), str(p))
        if g.exists():
            try:
                data = gzip.decompress(g.read_bytes())
            except Exception as e:
                raise DamagedFile(f"{g}: cannot be uncompressed ({e})") from None
            return _from_csv(tf, data, str(g))
        return []

    def _write_day(self, tf: str, day: date, candles: list[Candle]) -> None:
        data = _to_csv(candles)
        if self._gz(tf, day).exists() and not self._plain(tf, day).exists():
            safe_write(self._gz(tf, day), gzip.compress(data))
        else:
            safe_write(self._plain(tf, day), data)

    # ---- adding a candle --------------------------------------------------

    def get(self, tf: str, start: datetime) -> Candle | None:
        for c in self.read_day(tf, start.astimezone(UTC).date()):
            if c.start == start:
                return c
        return None

    def relabel(self, tf: str, old_start: datetime, new_start: datetime) -> Candle:
        """Give a stored candle a new start label, keeping every price and its
        end. Only for a deliberate, approved relabelling. The relabelled candle
        is written first, then the old one is removed, each with a safe write,
        so a crash in between leaves both (the store check would show it as a
        duplicate period), never neither."""
        old = self.get(tf, old_start)
        if old is None:
            raise KeyError(f"no stored {tf} candle at {iso(old_start)}")
        if self.get(tf, new_start) is not None:
            raise ValueError(f"a {tf} candle is already stored at {iso(new_start)}")
        from dataclasses import replace
        new = replace(old, start=new_start)
        if self.add(new) != "stored":
            raise RuntimeError("relabelled candle was not stored")
        day = old_start.astimezone(UTC).date()
        self._write_day(tf, day, [c for c in self.read_day(tf, day) if c.start != old_start])
        log.info("Relabelled %s candle %s as %s (prices unchanged).", tf, iso(old_start), iso(new_start))
        return new

    # ---- replacing an incomplete bigger candle (the one exception) ---------

    ARCHIVE_REBUILT = "archive_rebuilt"
    ARCHIVE_COLUMNS = COLUMNS + ("archived_utc", "reason", "replaced_by_parts")

    def replace_with_fuller(self, new: Candle, reason: str, now: datetime) -> Candle:
        """The ONE case where a stored candle is replaced: a bigger candle that
        was built from an incomplete set of 5-minute candles, rebuilt from a
        fuller set after a gap fill. The old candle is ARCHIVED first, never
        deleted (<store>/archive_rebuilt/<size>/<UTC date>.csv, with when and
        why), then the day file is rewritten with the new candle in its place,
        each with a safe write. A crash in between leaves the old candle stored
        and archived; running again archives it only once. Returns the old candle."""
        tf = new.timeframe
        if tf not in BUILT_SIZES:
            raise ValueError(f"only built candles (1h, 4h, 1d, 1w) can be rebuilt, not {tf}")
        old = self.get(tf, new.start)
        if old is None:
            raise KeyError(f"no stored {tf} candle at {iso(new.start)}")
        if old.end != new.end or old.expected_parts != new.expected_parts:
            raise ValueError(f"the rebuilt {tf} candle at {iso(new.start)} does not cover the same time")
        if not (old.parts < old.expected_parts and new.parts > old.parts):
            raise ValueError(f"the stored {tf} candle at {iso(new.start)} ({old.parts}/{old.expected_parts}) "
                             f"is complete, or the rebuild ({new.parts}) is not fuller: nothing replaced")
        day = new.start.astimezone(UTC).date()
        apath = self.folder / self.ARCHIVE_REBUILT / tf / f"{day.isoformat()}.csv"
        row = [iso(old.start), iso(old.end), *(plain(x) for x in old.prices()), str(old.parts),
               str(old.expected_parts)]
        rows: list[list[str]] = []
        if apath.exists():
            rows = list(csv.reader(io.StringIO(apath.read_text())))[1:]
        if not any(r[:len(row)] == row for r in rows):
            rows.append(row + [iso(now), reason, str(new.parts)])
            buf = io.StringIO()
            w = csv.writer(buf, lineterminator="\n")
            w.writerow(self.ARCHIVE_COLUMNS)
            w.writerows(rows)
            apath.parent.mkdir(parents=True, exist_ok=True)
            safe_write(apath, buf.getvalue().encode())
        self._write_day(tf, day, [new if c.start == new.start else c for c in self.read_day(tf, day)])
        log.info("Rebuilt %s from %d of %d 5-minute candles (was %d); the old one is archived in %s.",
                 new.describe(), new.parts, new.expected_parts, old.parts, apath)
        return old

    def add(self, candle: Candle) -> str:
        """Store one candle. Returns 'stored', 'same' (already stored with the
        same values: nothing written) or 'different' (a different value for a
        stored candle: the stored one is kept and a warning written)."""
        if candle.timeframe not in TIMEFRAMES:
            raise ValueError(f"unknown candle size {candle.timeframe!r}")
        day = candle.start.astimezone(UTC).date()
        existing = self.read_day(candle.timeframe, day)  # DamagedFile: nothing is written
        for c in existing:
            if c.start == candle.start:
                if c.same_values(candle):
                    return "same"
                self.warn(
                    f"DIFFERENT VALUE for a stored candle, kept the stored one. "
                    f"Stored: {c.describe()} (parts {c.parts}/{c.expected_parts}). "
                    f"Arrived: {candle.describe()} (parts {candle.parts}/{candle.expected_parts}).")
                return "different"
        updated = sorted(existing + [candle], key=lambda c: c.start)
        self._write_day(candle.timeframe, day, updated)
        return "stored"

    # ---- reading ------------------------------------------------------------

    def read_range(self, tf: str, start: datetime, end: datetime) -> list[Candle]:
        """Stored candles with start in [start, end), in time order."""
        out = []
        for day in self.days(tf):
            if start.date() - timedelta(days=1) <= day <= end.date():
                out.extend(c for c in self.read_day(tf, day) if start <= c.start < end)
        return sorted(out, key=lambda c: c.start)

    def newest(self, tf: str) -> Candle | None:
        for day in reversed(self.days(tf)):
            candles = self.read_day(tf, day)
            if candles:
                return max(candles, key=lambda c: c.start)
        return None

    # ---- housekeeping --------------------------------------------------------

    def remove_leftover_temp_files(self) -> int:
        """Temporary files left by a crash mid-write. The real files were never
        touched by such a crash, so these are simply removed."""
        n = 0
        if not self.folder.is_dir():
            return 0
        for p in self.folder.rglob(f"*{TMP_MARK}*"):
            p.unlink()
            n += 1
        if n:
            self.warn(f"Removed {n} unfinished temporary file(s) left by an interrupted write. "
                      "No stored candle was affected.")
        return n

    def compress_old(self, now: datetime) -> int:
        """Compress files more than compress_after_days old. Never deletes candles."""
        cutoff = now.astimezone(UTC).date() - timedelta(days=self.compress_after_days)
        n = 0
        for tf in TIMEFRAMES:
            for day in self.days(tf):
                p, g = self._plain(tf, day), self._gz(tf, day)
                if day >= cutoff or not p.exists():
                    continue
                data = p.read_bytes()
                _from_csv(tf, data, str(p))           # never compress a damaged file
                if g.exists():
                    if gzip.decompress(g.read_bytes()) != data:
                        self.warn(f"{p} and {g} both exist and differ; both kept. Please check by hand.")
                        continue
                else:
                    safe_write(g, gzip.compress(data))
                if gzip.decompress(g.read_bytes()) == data:  # check before removing the original
                    p.unlink()
                    _fsync_dir(p.parent)
                    n += 1
        return n

    # ---- the record of gaps -------------------------------------------------

    def _gaps_path(self) -> Path:
        return self.folder / "gaps.csv"

    def recorded_gaps(self) -> list[dict]:
        p = self._gaps_path()
        if not p.exists():
            return []
        rows = list(csv.DictReader(io.StringIO(p.read_text())))
        out = [r for r in rows if set(GAP_REQUIRED) <= set(r)]
        for r in out:
            r["note"] = r.get("note") or ""
        return out

    def _write_gaps(self, rows: list[dict]) -> None:
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=GAP_COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows({k: r.get(k, "") for k in GAP_COLUMNS} for r in rows)
        safe_write(self._gaps_path(), buf.getvalue().encode())

    def note_gap(self, tf: str, start: datetime, end: datetime, note: str) -> None:
        """Add a note to a recorded gap. The record itself is kept unchanged;
        gap records are never removed."""
        rows = self.recorded_gaps()
        hits = [r for r in rows if (r["timeframe"], r["from_utc"], r["to_utc"]) == (tf, iso(start), iso(end))]
        if not hits:
            raise KeyError(f"no recorded {tf} gap from {iso(start)} to {iso(end)}")
        for r in hits:
            r["note"] = (r["note"] + " | " if r["note"] else "") + note
        self._write_gaps(rows)

    def record_gap(self, tf: str, start: datetime, end: datetime, missing: int,
                   found: datetime, how: str) -> None:
        rows = self.recorded_gaps()
        rows.append({"timeframe": tf, "from_utc": iso(start), "to_utc": iso(end),
                     "missing_candles": str(missing), "found_utc": iso(found), "how_found": how, "note": ""})
        self._write_gaps(rows)
        log.info("Gap recorded: %s %s to %s (%d candle(s)), found %s.",
                 tf, uk_short(start), uk_short(end), missing, how)
