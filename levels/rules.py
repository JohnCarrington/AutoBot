"""The rules for every kind of level. Pure functions: candles in, levels out.
No files, no IG, no clock. The plain-English rules are in docs/LEVELS.md.

Every level uses the BUY price (IG's offer, OFR): buy_high, buy_low and
buy_close. The sell price is never used here.

Prices are in IG's points (13354.4 means 1.33544). Pip distances from the
settings are turned into points with market.points_per_pip.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal
from typing import Iterable, Sequence

from prices.model import Candle

# ---- level types --------------------------------------------------------------

PIVOT = "pivot"
R1, R2, R3 = "R1", "R2", "R3"
S1, S2, S3 = "S1", "S2", "S3"
ROUND_NUMBER = "round_number"
PREVIOUS_DAY_HIGH = "previous_day_high"
PREVIOUS_DAY_LOW = "previous_day_low"
LONDON_HIGH, LONDON_LOW = "london_session_high", "london_session_low"
NEW_YORK_HIGH, NEW_YORK_LOW = "new_york_session_high", "new_york_session_low"
TURNING_HIGH, TURNING_LOW = "turning_high", "turning_low"

# The order used when two levels have the same price, and when listing types.
TYPE_ORDER = (S3, S2, S1, PIVOT, R1, R2, R3, ROUND_NUMBER, PREVIOUS_DAY_HIGH, PREVIOUS_DAY_LOW,
              LONDON_HIGH, LONDON_LOW, NEW_YORK_HIGH, NEW_YORK_LOW, TURNING_HIGH, TURNING_LOW)

# The levels that matter most, as the owner set out: S2, R2, the daily pivot,
# round numbers and turning levels.
IMPORTANT_TYPES = frozenset({PIVOT, R2, S2, ROUND_NUMBER, TURNING_HIGH, TURNING_LOW})


@dataclass(frozen=True)
class Level:
    price: Decimal
    type: str
    source: str                       # where it came from, in words a person can read
    candle_utc: datetime | None       # start of the candle (or session) it came from
    important: bool = False
    group: int = 0                    # set by group_levels()


def make(price: Decimal, type_: str, source: str, candle_utc: datetime | None) -> Level:
    return Level(price, type_, source, candle_utc, important=type_ in IMPORTANT_TYPES)


def to_decimals(d: Decimal, decimals: int) -> Decimal:
    return d.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)


# ---- 1. daily pivots --------------------------------------------------------------

def daily_pivots(day: Candle, decimals: int, source: str) -> list[Level]:
    """Classic floor pivots from one daily candle's BUY high, low and close:
         pivot P = (H + L + C) / 3
         R1 = 2P - L          S1 = 2P - H
         R2 = P + (H - L)     S2 = P - (H - L)
         R3 = H + 2(P - L)    S3 = L - 2(H - P)
    Worked out exactly, then written to `decimals` places (half up)."""
    h, l, c = day.buy_high, day.buy_low, day.buy_close
    p = (h + l + c) / 3
    values = {
        PIVOT: p,
        R1: 2 * p - l, S1: 2 * p - h,
        R2: p + (h - l), S2: p - (h - l),
        R3: h + 2 * (p - l), S3: l - 2 * (h - p),
    }
    return [make(to_decimals(v, decimals), t, source, day.start) for t, v in values.items()]


# ---- 2. other levels ---------------------------------------------------------------

def previous_day_high_low(day: Candle, source: str) -> list[Level]:
    return [make(day.buy_high, PREVIOUS_DAY_HIGH, source, day.start),
            make(day.buy_low, PREVIOUS_DAY_LOW, source, day.start)]


def round_numbers(reference: Decimal, every_points: Decimal, within_points: Decimal) -> list[Level]:
    """Every multiple of `every_points` (prices ending in 00 and 50 pips when it
    is 50 pips) from `within_points` below the reference price to
    `within_points` above it, both ends included."""
    lo = ((reference - within_points) / every_points).to_integral_value(ROUND_CEILING)
    hi = ((reference + within_points) / every_points).to_integral_value(ROUND_FLOOR)
    out = []
    n = lo
    while n <= hi:
        out.append(make(n * every_points, ROUND_NUMBER,
                        f"round number (every {every_points.normalize():f} points)", None))
        n += 1
    return out


def session_high_low(candles: Sequence[Candle], high_type: str, low_type: str,
                     source: str, start: datetime) -> list[Level]:
    """The highest BUY high and lowest BUY low of a session's candles."""
    if not candles:
        return []
    return [make(max(c.buy_high for c in candles), high_type, source, start),
            make(min(c.buy_low for c in candles), low_type, source, start)]


def turning_levels(hourly: Sequence[Candle], since: datetime, each_side: int,
                   min_move_points: Decimal, within: int, describe) -> list[Level]:
    """Hourly highs and lows where price clearly reversed. `hourly` must be in
    time order; neighbouring candles are neighbours on the chart (the weekend
    is simply skipped, as on IG's chart).

    A candle's BUY high is a turning high when ALL of these hold:
      1. it is higher than the high of each of the `each_side` candles before it;
      2. it is not lower than the high of any of the `each_side` candles after
         it (so of two equal highs side by side, the first one counts);
      3. within the `within` candles after it, some candle's BUY low is at least
         `min_move_points` below it (price clearly moved away).
    A turning low is the same, upside down. The candle must start at or after
    `since` (the lookback), and the candles needed for rules 1 and 2 must exist.
    """
    out: list[Level] = []
    for i in range(each_side, len(hourly) - each_side):
        c = hourly[i]
        if c.start < since:
            continue
        before = hourly[i - each_side:i]
        after = hourly[i + 1:i + 1 + each_side]
        move = hourly[i + 1:i + 1 + within]
        if (all(c.buy_high > b.buy_high for b in before)
                and all(c.buy_high >= a.buy_high for a in after)
                and any(m.buy_low <= c.buy_high - min_move_points for m in move)):
            out.append(make(c.buy_high, TURNING_HIGH, describe(c, "high"), c.start))
        if (all(c.buy_low < b.buy_low for b in before)
                and all(c.buy_low <= a.buy_low for a in after)
                and any(m.buy_high >= c.buy_low + min_move_points for m in move)):
            out.append(make(c.buy_low, TURNING_LOW, describe(c, "low"), c.start))
    return out


# ---- 3. levels that line up ----------------------------------------------------------

def sort_key(lv: Level):
    return (lv.price, TYPE_ORDER.index(lv.type), lv.candle_utc.timestamp() if lv.candle_utc else 0)


def group_levels(levels: Iterable[Level], within_points: Decimal) -> tuple[list[Level], list[dict]]:
    """Sorts the levels by price and puts them into groups. Going up from the
    lowest, a level joins the current group if it is within `within_points` of
    the LOWEST level in that group; otherwise it starts a new group. So every
    level in a group is within `within_points` of every other. Every level is
    in exactly one group (a level on its own is a group of one). Groups are
    numbered 1, 2, 3 ... from the lowest price. Every kind of level can be
    grouped, the daily pivot included."""
    ordered = sorted(levels, key=sort_key)
    out: list[Level] = []
    groups: list[dict] = []
    for lv in ordered:
        if not groups or lv.price - groups[-1]["low"] > within_points:
            groups.append({"group": len(groups) + 1, "low": lv.price, "high": lv.price, "members": []})
        g = groups[-1]
        g["high"] = lv.price
        placed = replace(lv, group=g["group"])
        g["members"].append(placed)
        out.append(placed)
    for g in groups:
        g["important"] = any(m.important for m in g["members"])
        g["lined_up"] = len(g["members"]) > 1
    return out, groups
