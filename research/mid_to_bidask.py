"""Buy and sell candles from AutoBot 161's 2026 MID candles (research only).

    sell = mid - half the spread        buy = mid + half the spread

for each of open, high, low and close. The spread for each 5-minute candle is IG's
typical spread for that half hour of the week (data/research/ig_spread/
GBPUSD_spread_by_half_hour.csv, built from the bot's own IG prices by
research.dukascopy_check). 161's own stored spreads (its ohlc folder) are NOT used:
checked 10 November 2026, that folder's prices never exactly match IG's or 161's
mid candles (29 points off in April) and its spreads are far narrower than IG's
(docs/research/ig161_mid_2026_20261110.md).

161's mid is (IG BID + IG OFR) / 2 for each leg, from IG's own 5-minute candles
(161's README). Every IG price is a whole tenth of a point, so a mid is a whole
twentieth; 161 wrote them as floats (13376.150000000001), so they are snapped back
to the twentieth, and anything further off is refused.

Rounding to IG's tenth of a point: "outward" puts the sell price down and the buy
price up (the spread is never narrower than the one used); "inward" does the
opposite; "none" keeps the twentieths (for comparison only, IG never writes them).

Nothing here contacts anyone or writes outside data/research/ (candles_convert).
"""

from __future__ import annotations

import csv
import io
import argparse
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from pathlib import Path
from typing import Callable, Iterable

from prices.calendar import floor_5m
from prices.model import FIVE_MIN, UTC
from research.candles_convert import RCandle
from research.dukascopy_check import half_hour_of_normal_week, quantile, spread_samples

TWENTIETH = Decimal("0.05")
TENTH = Decimal("0.1")
ROUNDINGS = ("outward", "inward", "none")


# ---- 161's mid candles --------------------------------------------------------------

def snap_mid(text: str) -> Decimal:
    """'13376.150000000001' -> 13376.15. Refuses anything not within a hair of a twentieth."""
    v = Decimal(text.strip())
    if not v.is_finite() or v <= 0:
        raise ValueError(f"not a price: {text!r}")
    s = (v / TWENTIETH).quantize(Decimal(1)) * TWENTIETH
    if abs(s - v) > Decimal("0.000001"):
        raise ValueError(f"{text!r} is not a mid of two IG prices (a whole twentieth of a point)")
    return s


@dataclass
class MidRead:
    candles: list[RCandle]          # the mid is held in the `sell` slot until converted
    skipped: list[tuple[str, str]]  # (file, line) rows not usable, e.g. 'nan'
    moved: int = 0


MARCH_2026 = datetime(2026, 3, 1, tzinfo=UTC)


def jan_feb_five_hours_late(t: datetime) -> timedelta:
    """161's 2026 mid candles labelled before 1 March 2026 carry New York time
    (EST, UTC-5) written as UTC: their weeks run "Sunday 17:00" to "Friday 16:55".
    Checked 10 November 2026 against IG's own daily candles: moved 5 hours later
    they line up (median 0.5 points); no other shift does. 161 has no candles from
    27 February to 23 March, and from 23 March its times are true UTC."""
    return timedelta(hours=5) if t < MARCH_2026 else timedelta(0)


def read_161_mid(folder: Path, shift: Callable[[datetime], timedelta] = lambda t: timedelta(0)) -> MidRead:
    """Every 161 mid file in `folder`. `shift(t)` gives a correction for a candle
    labelled `t` (see JAN_FEB_FIVE_HOURS_LATE). Rows with a missing number ('nan')
    are skipped and listed, never guessed."""
    out, skipped, moved = [], [], 0
    for p in sorted(Path(folder).glob("*.csv")):
        rows = list(csv.reader(io.StringIO(p.read_text())))
        if not rows or rows[0] != ["timestamp", "open", "high", "low", "close"]:
            raise ValueError(f"{p}: unexpected header {rows[:1]}")
        for r in rows[1:]:
            if any(v.strip().lower() in ("nan", "", "inf", "-inf") for v in r[1:5]):
                skipped.append((p.name, ",".join(r)))
                continue
            t = datetime.fromisoformat(r[0])
            if t.utcoffset() != timedelta(0):
                raise ValueError(f"{p}: {r[0]} is not UTC")
            t = t.astimezone(UTC)
            if t != floor_5m(t):
                raise ValueError(f"{p}: {r[0]} is not on a 5-minute mark")
            o, h, l, c = (snap_mid(v) for v in r[1:5])
            if not (l <= min(o, c) and max(o, c) <= h):
                raise ValueError(f"{p}: {r[0]} high/low do not hold open and close")
            d = shift(t)
            if d:
                moved += 1
            out.append(RCandle(t + d, t + d + FIVE_MIN, None, (o, h, l, c)))
    out.sort(key=lambda c: c.start)
    for a, b in zip(out, out[1:]):
        if a.start == b.start:
            raise ValueError(f"two 161 mid candles at {a.start.isoformat()}")
    return MidRead(out, skipped, moved)


# ---- spreads ------------------------------------------------------------------------

def read_spread_table(path: Path) -> dict[str, Decimal]:
    """The half-hour table: {'Mon 09:30': typical spread in points}."""
    rows = list(csv.DictReader(io.StringIO(Path(path).read_text())))
    return {r["uk_half_hour_normal_week"]: Decimal(r["typical_points"]) for r in rows}


def spread_from_table(table: dict[str, Decimal]) -> Callable[[datetime], Decimal]:
    def f(t: datetime) -> Decimal:
        k = half_hour_of_normal_week(t)
        if k not in table:
            raise KeyError(f"no spread in the table for {k} ({t.isoformat()})")
        return table[k]
    return f


def build_spread_table(candles: Iterable[RCandle]) -> dict[str, Decimal]:
    """Typical (median) spread per half hour of the week, from candles holding
    real IG buy and sell prices (their opens and closes)."""
    groups: dict[str, list[Decimal]] = {}
    for t, s in spread_samples(candles):
        groups.setdefault(half_hour_of_normal_week(t), []).append(s)
    return {k: quantile(v, 0.5) for k, v in groups.items()}


# ---- the conversion ---------------------------------------------------------------

def _round(p: Decimal, up: bool, rounding: str) -> Decimal:
    if rounding == "none":
        return p
    return p.quantize(TENTH, rounding=ROUND_CEILING if up else ROUND_FLOOR)


def to_buy_sell(mid: RCandle, spread: Decimal, rounding: str = "outward") -> RCandle:
    if rounding not in ROUNDINGS:
        raise ValueError(f"rounding must be one of {ROUNDINGS}")
    half = spread / 2
    up_sell = rounding == "inward"     # inward: sell rounded up, buy rounded down
    sell = tuple(_round(m - half, up_sell, rounding) for m in mid.sell)
    buy = tuple(_round(m + half, not up_sell, rounding) for m in mid.sell)
    # Rounding a high and a low in the same direction keeps high >= open/close >= low.
    return RCandle(mid.start, mid.end, buy, sell, mid.parts, mid.expected_parts)


def convert_mids(mids: Iterable[RCandle], spread_for: Callable[[datetime], Decimal],
                 rounding: str = "outward") -> list[RCandle]:
    return [to_buy_sell(m, spread_for(m.start), rounding) for m in mids]


def main(argv: list[str] | None = None) -> int:
    from research.candles_convert import _boundaries, _check_out_folder, convert, within_market_hours
    ap = argparse.ArgumentParser(description="Buy and sell candles from 161's 2026 mid candles (no IG contact).")
    ap.add_argument("--src", type=Path, required=True)
    ap.add_argument("--table", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--rounding", choices=ROUNDINGS[:2], default="outward")
    a = ap.parse_args(argv)
    _check_out_folder(a.out)
    b = _boundaries()
    r = read_161_mid(a.src, jan_feb_five_hours_late)
    kept, dropped = within_market_hours(r.candles, b.hours)
    candles = convert_mids(kept, spread_from_table(read_spread_table(a.table)), a.rounding)
    res = convert(candles, b, a.out, "research conversion of AutoBot 161's 2026 IG mid candles: "
                  f"mid -/+ half IG's typical half-hour spread, rounded {a.rounding}")
    print(f"161 mid candles read: {len(r.candles)}; moved 5 hours later (before 1 March): {r.moved}")
    print(f"rows skipped (missing numbers): {len(r.skipped)} {r.skipped}")
    print(f"outside the bot's market hours, not kept: {len(dropped)}")
    print(f"written to {a.out}: {res['counts']}")
    by: dict[str, list[int]] = {}
    for tf, _, _, n in res["gaps"]:
        by.setdefault(tf, []).append(n)
    for tf, ns in by.items():
        print(f"gaps {tf}: {len(ns)} runs, {sum(ns)} candles")
    return 0


if __name__ == "__main__":
    sys.exit(main())
