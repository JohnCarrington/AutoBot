"""Research candles from outside sources, built exactly as the bot builds its own.

Sources:
  * AutoBot 161's IG 5-minute BID candles (2024-2025): CSV `timestamp,open,high,low,close`,
    UTC, IG points with two decimals ("12787.30"). Sell prices only.
  * Dukascopy 1-minute candles exported by hand with Dukascopy's own Historical
    Data Export tool (CSV, one file per side and period, GMT times).
    Buy (ASK) and sell (BID). Nothing here downloads anything: Dukascopy's terms
    forbid scripted downloading without their written consent.

Output: the bot's candle-store layout and columns (prices/store.py COLUMNS):
    <out>/<size>/<UTC date>.csv  for 5m, 1h, 1d
    <out>/gaps.csv               every gap, in the store's gap columns
Days are UK midnight to midnight with IG's short Sunday candle, using the bot's own
Boundaries and MarketHours with the bot's own settings. Prices are written the way
IG writes them on the spread bet account: 1.33797 is 13379.7. Where a source has
no buy price, the four buy columns are left empty (the live CandleStore cannot read
such files, which is deliberate: they are research data, not the bot's store).

Safety: refuses to write anywhere but under /opt/autobot/data/research/ (or a test
folder), and never into a live candle store. Never contacts anyone.
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Iterable, Iterator
from zoneinfo import ZoneInfo

from prices.calendar import Boundaries, MarketHours, floor_5m
from prices.model import FIVE_MIN, UK, UTC, iso, parse_iso
from prices.store import COLUMNS, GAP_COLUMNS

RESEARCH_ROOT = Path("/opt/autobot/data/research")
LIVE_CANDLES = Path("/opt/autobot/data/candles")
TENTH = Decimal("0.1")
SIZES = ("5m", "1h", "1d")


# ---- prices --------------------------------------------------------------------

def points_from_fx(fx: Decimal) -> Decimal:
    """1.33797 -> 13379.7 (IG's spread bet points). Exact; refuses finer prices."""
    p = (fx * 10000)
    q = p.quantize(TENTH)
    if q != p:
        raise ValueError(f"price {fx} is finer than IG's tenth of a point")
    return q


def points_from_text(text: str) -> Decimal:
    """'12787.30' (points, as 161 wrote them) -> 12787.3. Refuses a non-zero hundredth."""
    p = Decimal(text.strip())
    q = p.quantize(TENTH)
    if q != p or not q.is_finite() or q <= 0:
        raise ValueError(f"not an IG price in points: {text!r}")
    return q


def written(p: Decimal | None) -> str:
    return "" if p is None else format(p.quantize(TENTH), "f")


# ---- a candle with an optional buy or sell side ---------------------------------

Side = tuple[Decimal, Decimal, Decimal, Decimal]   # open, high, low, close


@dataclass(frozen=True)
class RCandle:
    start: datetime
    end: datetime
    buy: Side | None
    sell: Side | None
    parts: int = 1
    expected_parts: int = 1


def _join(sides: list[Side]) -> Side:
    return (sides[0][0], max(s[1] for s in sides), min(s[2] for s in sides), sides[-1][3])


def build(start: datetime, end: datetime, parts: list[RCandle], expected: int) -> RCandle:
    """Same rule as prices.model.build_from, side by side: open of the first,
    highest high, lowest low, close of the last."""
    parts = sorted(parts, key=lambda c: c.start)
    buy = _join([c.buy for c in parts]) if all(c.buy for c in parts) else None
    sell = _join([c.sell for c in parts]) if all(c.sell for c in parts) else None
    return RCandle(start, end, buy, sell, len(parts), expected)


# ---- reading the sources --------------------------------------------------------

def read_161_file(path: Path) -> list[RCandle]:
    rows = list(csv.reader(io.StringIO(path.read_text())))
    if not rows or rows[0] != ["timestamp", "open", "high", "low", "close"]:
        raise ValueError(f"{path}: unexpected header {rows[:1]}")
    out = []
    for r in rows[1:]:
        t = datetime.fromisoformat(r[0])
        if t.utcoffset() != timedelta(0):
            raise ValueError(f"{path}: time {r[0]} is not UTC")
        t = t.astimezone(UTC)
        if t != floor_5m(t):
            raise ValueError(f"{path}: {r[0]} is not on a 5-minute mark")
        o, h, l, c = (points_from_text(v) for v in r[1:5])
        if not (l <= min(o, c) and max(o, c) <= h):
            raise ValueError(f"{path}: {r[0]} high/low do not hold open and close")
        out.append(RCandle(t, t + FIVE_MIN, None, (o, h, l, c)))
    return out


NEW_YORK = ZoneInfo("America/New_York")


def clocks_out_of_step(t: datetime) -> bool:
    """True in the weeks when US clocks are on summer time and the UK's are not
    (17:00 New York is then 21:00 UK). Clock changes happen at weekends, while
    the market is closed, so a whole trading week is either in or out."""
    return t.astimezone(NEW_YORK).utcoffset() - t.astimezone(UK).utcoffset() == timedelta(hours=-4)


def fix_161_out_of_step_weeks(candles: list[RCandle]) -> tuple[list[RCandle], int]:
    """AutoBot 161's times are one hour EARLY in the weeks when US and UK clocks
    are out of step (checked 10 November 2026 against IG's own daily candles:
    shifted one hour later, all four sell prices of those 24 days line up with
    IG's, and every 161 candle then falls inside IG's market hours). The other
    weeks are right as they are. Returns the corrected candles and how many moved."""
    out, moved = [], 0
    hour = timedelta(hours=1)
    for c in candles:
        if clocks_out_of_step(c.start):
            out.append(RCandle(c.start + hour, c.end + hour, c.buy, c.sell, c.parts, c.expected_parts))
            moved += 1
        else:
            out.append(c)
    return sorted(out, key=lambda c: c.start), moved


def read_161(folder: Path) -> list[RCandle]:
    out: list[RCandle] = []
    for p in sorted(Path(folder).glob("*.csv")):
        out.extend(read_161_file(p))
    out.sort(key=lambda c: c.start)
    for a, b in zip(out, out[1:]):
        if a.start == b.start:
            raise ValueError(f"duplicate 161 candle at {iso(a.start)}")
    return out


def _duka_time(text: str, utc_header: bool) -> datetime:
    """Dukascopy export times: '01.11.2025 21:00:00.000', optionally followed by
    ' GMT+0000' (or another stated offset), or ISO. Without a stated offset the
    column itself must say GMT/UTC."""
    text = text.strip()
    m = re.fullmatch(r"(\d{2})\.(\d{2})\.(\d{4}) (\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(?: GMT([+-])(\d{2}):?(\d{2}))?", text)
    if m:
        d, mo, y, h, mi, se = (int(x) for x in m.groups()[:6])
        t = datetime(y, mo, d, h, mi, se, tzinfo=UTC)
        if m.group(7):
            off = timedelta(hours=int(m.group(8)), minutes=int(m.group(9)))
            t -= off if m.group(7) == "+" else -off
        elif not utc_header:
            raise ValueError(f"time {text!r} has no time zone and the column is not GMT/UTC")
        return t
    t = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if t.tzinfo is None:
        if not utc_header:
            raise ValueError(f"time {text!r} has no time zone and the column is not GMT/UTC")
        return t.replace(tzinfo=UTC)
    return t.astimezone(UTC)


def duka_side_of(path: Path) -> str:
    """'BID' or 'ASK', from the file name Dukascopy's export gives
    (e.g. GBPUSD_Candlestick_1_M_BID_01.11.2023-31.10.2024.csv)."""
    words = set(re.split(r"[^A-Z]+", path.name.upper()))
    sides = words & {"BID", "ASK"}
    if len(sides) != 1:
        raise ValueError(f"{path.name}: cannot tell whether it is BID or ASK from the name")
    return sides.pop()


def read_duka_csv(path: Path) -> list[tuple[datetime, Side, Decimal]]:
    """One Dukascopy export file of 1-minute candles: time, open, high, low, close,
    volume. Prices are FX prices (1.33797) and become IG points (13379.7)."""
    rows = list(csv.reader(io.StringIO(path.read_text(encoding="utf-8-sig"))))
    head = [h.strip().lower() for h in rows[0]]
    if head[1:5] != ["open", "high", "low", "close"] or len(head) < 6 or not head[5].startswith("volume"):
        raise ValueError(f"{path.name}: unexpected header {rows[0]}")
    utc_header = any(w in head[0] for w in ("gmt", "utc"))
    out = []
    for n, r in enumerate(rows[1:], start=2):
        if not r or not "".join(r).strip():
            continue
        t = _duka_time(r[0], utc_header)
        if t.second or t.microsecond:
            raise ValueError(f"{path.name} line {n}: {r[0]} is not on a whole minute")
        side = tuple(points_from_fx(Decimal(v.strip())) for v in r[1:5])
        if not (side[2] <= min(side[0], side[3]) and max(side[0], side[3]) <= side[1]):
            raise ValueError(f"{path.name} line {n}: high/low do not hold open and close")
        out.append((t, side, Decimal(r[5].strip())))
    return out


def duka_five_minutes(folder: Path) -> tuple[list[RCandle], dict]:
    """5-minute buy (ASK) and sell (BID) candles from every Dukascopy export file in
    `folder`. A minute counts only if Dukascopy recorded ticks in it (volume above
    0 on either side): its export pads quiet and closed minutes with flat
    zero-volume candles. A minute is used only when both sides have it."""
    minutes: dict[str, dict[datetime, tuple[Side, Decimal]]] = {"BID": {}, "ASK": {}}
    files = sorted(p for p in Path(folder).iterdir() if p.suffix.lower() == ".csv")
    for p in files:
        side = duka_side_of(p)
        for t, s, v in read_duka_csv(p):
            old = minutes[side].get(t)
            if old is not None and old != (s, v):
                raise ValueError(f"{p.name}: {iso(t)} differs from another {side} file")
            minutes[side][t] = (s, v)
    bid, ask = minutes["BID"], minutes["ASK"]
    by_five: dict[datetime, list[tuple[Side, Side]]] = defaultdict(list)
    one_side = 0
    for t in sorted(bid.keys() | ask.keys()):
        if t not in bid or t not in ask:
            one_side += 1
            continue
        if bid[t][1] > 0 or ask[t][1] > 0:
            by_five[floor_5m(t)].append((ask[t][0], bid[t][0]))
    out = [RCandle(t, t + FIVE_MIN, _join([m[0] for m in by_five[t]]), _join([m[1] for m in by_five[t]]))
           for t in sorted(by_five)]
    return out, {"files": [p.name for p in files], "bid_minutes": len(bid), "ask_minutes": len(ask),
                 "minutes_on_one_side_only": one_side}


# ---- building, gaps, writing ----------------------------------------------------

def within_market_hours(fives: list[RCandle], hours: MarketHours) -> tuple[list[RCandle], list[RCandle]]:
    keep, dropped = [], []
    for c in fives:
        (keep if hours.is_open(c.start) else dropped).append(c)
    return keep, dropped


def build_bigger(fives: list[RCandle], b: Boundaries, tf: str) -> list[RCandle]:
    buckets: dict[tuple[datetime, datetime], list[RCandle]] = defaultdict(list)
    for c in fives:
        buckets[b.bucket(tf, c.start)].append(c)
    return [build(s, e, parts, b.expected_parts(s, e)) for (s, e), parts in sorted(buckets.items())]


def _runs(missing: list[datetime], step: timedelta) -> Iterator[tuple[datetime, datetime, int]]:
    if not missing:
        return
    first = prev = missing[0]
    n = 1
    for t in missing[1:]:
        if t - prev == step:
            n += 1
        else:
            yield first, prev + step, n
            first, n = t, 1
        prev = t
    yield first, prev + step, n


def find_gaps(fives: list[RCandle], bigger: dict[str, list[RCandle]], b: Boundaries,
              start: datetime, end: datetime) -> list[tuple[str, datetime, datetime, int]]:
    """Every 5-minute candle the bot's market hours expect in [start, end) that is
    missing, as runs; and every 1h/1d candle with no 5-minute candle at all."""
    have = {c.start for c in fives}
    missing5 = [t for t in b.hours.open_slots(start, end) if t not in have]
    gaps = [("5m", s, e, n) for s, e, n in _runs(missing5, FIVE_MIN)]
    for tf in ("1h", "1d"):
        built = {c.start for c in bigger[tf]}
        expected = sorted({b.bucket(tf, t) for t in b.hours.open_slots(start, end)})
        for s, e in expected:
            if s not in built:
                gaps.append((tf, s, e, 1))
    return gaps


def gap_note(tf: str, s: datetime, e: datetime, hours: MarketHours) -> str:
    """A plain description to help read the gap list (not a judgement)."""
    lu = s.astimezone(UK)
    if (lu.month, lu.day) in ((12, 24), (12, 25), (12, 26), (12, 31), (1, 1)):
        return "Christmas or New Year"
    o, _ = hours.session(s)
    if s == o:
        return "at the week's open"
    c = hours.session(s)[1]
    if e == c:
        return "at the week's close"
    if lu.hour in (21, 22, 23) or (lu.hour == 0 and lu.minute == 0):
        return "around the 22:00 UK rollover"
    return ""


def _check_out_folder(out: Path) -> Path:
    out = Path(out).resolve()
    if out == LIVE_CANDLES or LIVE_CANDLES in out.parents:
        raise PermissionError(f"refusing to write into the live candle store: {out}")
    allowed = [RESEARCH_ROOT]
    if os.environ.get("AUTOBOT_RESEARCH_TEST_ROOT"):
        allowed.append(Path(os.environ["AUTOBOT_RESEARCH_TEST_ROOT"]).resolve())
    if not any(out == a or a in out.parents for a in allowed):
        raise PermissionError(f"research output must be under {RESEARCH_ROOT}: {out}")
    return out


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp-research")
    tmp.write_text(text)
    os.replace(tmp, path)


def candles_csv(candles: Iterable[RCandle]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(COLUMNS)
    for c in candles:
        buy = c.buy or (None,) * 4
        sell = c.sell or (None,) * 4
        w.writerow([iso(c.start), iso(c.end), *(written(p) for p in buy), *(written(p) for p in sell),
                    c.parts, c.expected_parts])
    return buf.getvalue()


def write_store(out: Path, sizes: dict[str, list[RCandle]],
                gaps: list[tuple[str, datetime, datetime, int]], found: datetime, how: str,
                hours: MarketHours) -> dict[str, int]:
    out = _check_out_folder(out)
    counts = {}
    for tf, candles in sizes.items():
        by_day: dict[date, list[RCandle]] = defaultdict(list)
        for c in candles:
            by_day[c.start.astimezone(UTC).date()].append(c)
        for day, cs in by_day.items():
            _write(out / tf / f"{day.isoformat()}.csv", candles_csv(sorted(cs, key=lambda c: c.start)))
        counts[tf] = len(candles)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=GAP_COLUMNS, lineterminator="\n")
    w.writeheader()
    for tf, s, e, n in gaps:
        w.writerow({"timeframe": tf, "from_utc": iso(s), "to_utc": iso(e), "missing_candles": n,
                    "found_utc": iso(found), "how_found": how, "note": gap_note(tf, s, e, hours)})
    _write(out / "gaps.csv", buf.getvalue())
    return counts


def read_store_day(path: Path) -> list[RCandle]:
    """Reads a research day file (buy or sell columns may be empty), or a live
    store day file (read-only)."""
    import gzip
    data = path.read_bytes()
    if path.name.endswith(".gz"):
        data = gzip.decompress(data)
    rows = list(csv.reader(io.StringIO(data.decode())))
    if tuple(rows[0]) != COLUMNS:
        raise ValueError(f"{path}: wrong header")
    out = []
    for r in rows[1:]:
        buy = None if r[2] == "" else tuple(Decimal(v) for v in r[2:6])
        sell = None if r[6] == "" else tuple(Decimal(v) for v in r[6:10])
        out.append(RCandle(parse_iso(r[0]), parse_iso(r[1]), buy, sell, int(r[10]), int(r[11])))
    return out


def read_store(folder: Path, tf: str) -> list[RCandle]:
    out: list[RCandle] = []
    d = Path(folder) / tf
    if d.is_dir():
        for p in sorted(d.iterdir()):
            if p.name.endswith((".csv", ".csv.gz")):
                out.extend(read_store_day(p))
    return sorted(out, key=lambda c: c.start)


# ---- the whole conversion ---------------------------------------------------------

def convert(fives: list[RCandle], b: Boundaries, out: Path, how: str,
            now: datetime | None = None) -> dict:
    """Keep the 5-minute candles inside the bot's market hours, build 1h and 1d,
    record every gap between the first and last candle, and write it all."""
    now = now or datetime.now(UTC)
    kept, dropped = within_market_hours(fives, b.hours)
    sizes = {"5m": kept, "1h": build_bigger(kept, b, "1h"), "1d": build_bigger(kept, b, "1d")}
    gaps = find_gaps(kept, sizes, b, kept[0].start, kept[-1].end) if kept else []
    counts = write_store(out, sizes, gaps, now, how, b.hours)
    return {"counts": counts, "dropped_outside_hours": dropped, "gaps": gaps}


def _boundaries() -> Boundaries:
    from config.settings_loader import load_settings
    s = load_settings().for_pair("GBPUSD")
    return Boundaries(s.candles, MarketHours(s.market_hours))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build research candles (no IG contact).")
    ap.add_argument("source", choices=("ig161", "dukascopy"))
    ap.add_argument("--src", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    b = _boundaries()
    _check_out_folder(a.out)
    if a.source == "ig161":
        fives, moved = fix_161_out_of_step_weeks(read_161(a.src))
        print(f"161 candles moved one hour later (US/UK clocks out of step): {moved}")
        how = ("research conversion of AutoBot 161's IG 5-minute bid candles "
               "(out-of-step weeks moved one hour later)")
    else:
        fives, info = duka_five_minutes(a.src)
        print(f"Dukascopy files: {len(info['files'])}; bid minutes {info['bid_minutes']}, "
              f"ask minutes {info['ask_minutes']}, on one side only {info['minutes_on_one_side_only']}")
        how = "research conversion of Dukascopy 1-minute candles (exported by hand)"
    r = convert(fives, b, a.out, how)
    by_tf: dict[str, list[int]] = defaultdict(list)
    for tf, _, _, n in r["gaps"]:
        by_tf[tf].append(n)
    print(f"written to {a.out}: {r['counts']}")
    print(f"5-minute candles outside the bot's market hours, not kept: {len(r['dropped_outside_hours'])}")
    for tf, ns in by_tf.items():
        print(f"gaps {tf}: {len(ns)} runs, {sum(ns)} candles")
    return 0


if __name__ == "__main__":
    sys.exit(main())
