"""Comparisons for docs/research/dukascopy_check_20261109.md. Read-only: reads the
research candles and the bot's own store files, writes nothing, contacts nobody.

  * sell_diffs: how far one source's sell prices are from another's, candle by
    candle with the same start label (open, high, low, close), by year.
  * spread_by_slot: IG's buy minus sell at each candle's open and close, grouped
    by UK half hour of the week (or hour of the day).
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Callable, Iterable

from prices.model import UK
from research.candles_convert import RCandle, clocks_out_of_step

NAMES = ("open", "high", "low", "close")
DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def quantile(xs: list[Decimal], q: float) -> Decimal:
    """Nearest-rank quantile (no interpolation, so it is always a real value)."""
    s = sorted(xs)
    if not s:
        raise ValueError("no values")
    i = min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))
    return s[i]


def summary(xs: list[Decimal]) -> dict:
    a = [abs(x) for x in xs]
    return {"n": len(xs), "exact": sum(1 for x in xs if x == 0), "median": quantile(a, 0.5),
            "p95": quantile(a, 0.95), "max": max(a),
            "mean_signed": (sum(xs) / len(xs)).quantize(Decimal("0.01"))}


def sell_diffs(ours: Iterable[RCandle], ig: Iterable[RCandle],
               group: Callable[[RCandle], str] = lambda c: str(c.start.astimezone(UK).year),
               only: Callable[[RCandle], bool] = lambda c: True) -> dict[str, dict[str, dict]]:
    """ours minus IG, in points, for each sell price, grouped (by UK year by default),
    over candles with the same start that both have, and that `only` keeps."""
    mine = {c.start: c for c in ours if c.sell}
    theirs = {c.start: c for c in ig if c.sell}
    diffs: dict[str, dict[str, list[Decimal]]] = defaultdict(lambda: defaultdict(list))
    for t in sorted(mine.keys() & theirs.keys()):
        a, b = mine[t], theirs[t]
        if not only(b):
            continue
        for g in (group(b), "all"):
            for i, name in enumerate(NAMES):
                diffs[g][name].append(a.sell[i] - b.sell[i])
    return {g: {name: summary(v) for name, v in d.items()} for g, d in diffs.items()}


def half_hour_of_week(t: datetime) -> str:
    u = t.astimezone(UK)
    return f"{DAYS[u.weekday()]} {u.hour:02d}:{30 if u.minute >= 30 else 0:02d}"


def normal_week_time(t: datetime) -> datetime:
    """IG's 22:00 rollover follows New York time (17:00 New York). In the weeks when
    US and UK clocks are out of step it falls at 21:00 UK, so for a table in "UK time
    in a normal week" those weekday samples move one hour later. Sunday is left on
    UK time: IG's Sunday open follows UK time (docs/SETTINGS.md)."""
    if clocks_out_of_step(t) and t.astimezone(UK).weekday() != 6:
        return t + timedelta(hours=1)
    return t


def half_hour_of_normal_week(t: datetime) -> str:
    return half_hour_of_week(normal_week_time(t))


def hour_of_normal_day(t: datetime) -> str:
    return hour_of_day(normal_week_time(t))


def hour_of_day(t: datetime) -> str:
    return f"{t.astimezone(UK).hour:02d}:00"


def spread_samples(candles: Iterable[RCandle]) -> list[tuple[datetime, Decimal]]:
    """IG's spread at two real moments of each candle: its open (at its start)
    and its close (just before its end). Highs and lows are not used: the buy
    high and the sell high need not happen at the same moment."""
    out = []
    for c in candles:
        if c.buy and c.sell:
            out.append((c.start, c.buy[0] - c.sell[0]))
            out.append((c.end - (c.end - c.start) / 1000, c.buy[3] - c.sell[3]))
    return out


def spread_by(samples: Iterable[tuple[datetime, Decimal]], key: Callable[[datetime], str]) -> dict[str, dict]:
    groups: dict[str, list[Decimal]] = defaultdict(list)
    for t, s in samples:
        groups[key(t)].append(s)
    return {k: {"n": len(v), "median": quantile(v, 0.5), "p90": quantile(v, 0.9), "max": max(v),
                "min": min(v)} for k, v in groups.items()}


def week_order(label: str) -> tuple[int, int, int]:
    """Sort half hours from the Sunday open: Sun 21:00 first, Fri close last."""
    d, hm = label.split()
    h, m = (int(x) for x in hm.split(":"))
    day = (DAYS.index(d) + 1) % 7      # Sun = 0 ... Sat = 6
    return day, h, m


def mean(xs: list[Decimal]) -> Decimal:
    return Decimal(statistics.fmean(float(x) for x in xs)).quantize(Decimal("0.01"))
