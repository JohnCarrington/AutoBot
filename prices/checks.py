"""Checks on the candle store.

Run on every stored candle when the bot starts, and on each new candle as it
is stored. Each of these is written as a warning:
  * a gap during market hours (a candle missing between two stored ones;
    the weekend close is not a gap)
  * a duplicate candle (two candles with the same start time)
  * a buy price below the sell price (open, high, low or close)
  * a high below a low (buy or sell)
  * anything out of time order (candles not in order in their file, or in
    the wrong day's file), or a candle that does not start on its boundary
  * a file that cannot be read
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Iterable

from prices.calendar import Boundaries
from prices.model import TIMEFRAMES, UTC, Candle, parse_iso, plain, uk_short
from prices.store import CandleStore, DamagedFile


@dataclass
class Gap:
    timeframe: str
    start: datetime
    end: datetime
    missing: int
    known: bool = False

    def describe(self) -> str:
        return (f"GAP in {self.timeframe} candles during market hours: {self.missing} candle(s) missing "
                f"from {uk_short(self.start)} to {uk_short(self.end)}")


@dataclass
class CheckResult:
    candles: dict[str, int] = field(default_factory=dict)
    problems: list[str] = field(default_factory=list)
    gaps: list[Gap] = field(default_factory=list)

    @property
    def new_gaps(self) -> list[Gap]:
        return [g for g in self.gaps if not g.known]


def candle_problems(c: Candle) -> list[str]:
    """Problems inside one candle."""
    out = []
    for part in ("open", "high", "low", "close"):
        b, s = getattr(c, f"buy_{part}"), getattr(c, f"sell_{part}")
        if b < s:
            out.append(f"BUY BELOW SELL in {c.timeframe} candle {uk_short(c.start)}: "
                       f"buy {part} {plain(b)} is below sell {part} {plain(s)}")
    for side in ("buy", "sell"):
        hi, lo = getattr(c, f"{side}_high"), getattr(c, f"{side}_low")
        if hi < lo:
            out.append(f"HIGH BELOW LOW in {c.timeframe} candle {uk_short(c.start)}: "
                       f"{side} high {plain(hi)} is below {side} low {plain(lo)}")
    if c.end <= c.start:
        out.append(f"OUT OF TIME ORDER in {c.timeframe} candle {uk_short(c.start)}: it ends before it starts")
    return out


def file_problems(tf: str, day: date, candles: list[Candle], b: Boundaries) -> list[str]:
    """Problems in one day's file, with the candles in the order they are stored."""
    out = []
    seen: set[datetime] = set()
    for i, c in enumerate(candles):
        if c.start in seen:
            out.append(f"DUPLICATE {tf} candle {uk_short(c.start)} in the file for {day}")
        seen.add(c.start)
        if i and c.start < candles[i - 1].start:
            out.append(f"OUT OF TIME ORDER in the {tf} file for {day}: {uk_short(c.start)} "
                       f"comes after {uk_short(candles[i - 1].start)}")
        if c.start.astimezone(UTC).date() != day:
            out.append(f"OUT OF TIME ORDER: {tf} candle {uk_short(c.start)} is in the file for {day}")
        if not b.is_on_boundary(tf, c.start):
            out.append(f"OUT OF TIME ORDER: {tf} candle {uk_short(c.start)} does not start on a {tf} boundary")
        out.extend(candle_problems(c))
    return out


def missing_between(tf: str, prev: Candle, nxt: Candle, b: Boundaries) -> list[Gap]:
    """Candles that should be between two stored candles while the market is open."""
    return missing_after(tf, prev.end, nxt.start, b)


def missing_after(tf: str, after: datetime, before: datetime, b: Boundaries) -> list[Gap]:
    """Missing candles that should have started in [after, before)."""
    gaps: list[Gap] = []
    t = after
    while True:
        s = b.next_start(tf, t)
        if s >= before:
            break
        e = b.bucket(tf, s)[1]
        if gaps and gaps[-1].end == s:
            gaps[-1].end, gaps[-1].missing = e, gaps[-1].missing + 1
        else:
            gaps.append(Gap(tf, s, e, 1))
        t = e
    return gaps


def mark_known(gaps: Iterable[Gap], store: CandleStore) -> list[Gap]:
    recorded = [(r["timeframe"], parse_iso(r["from_utc"]), parse_iso(r["to_utc"]))
                for r in store.recorded_gaps()]
    out = list(gaps)
    for g in out:
        g.known = any(tf == g.timeframe and s <= g.start and g.end <= e for tf, s, e in recorded)
    return out


def check_store(store: CandleStore, b: Boundaries) -> CheckResult:
    """Check every stored candle of every size."""
    result = CheckResult()
    for tf in TIMEFRAMES:
        result.candles[tf] = 0
        prev: Candle | None = None
        for day in store.days(tf):
            try:
                candles = store.read_day(tf, day)
            except DamagedFile as e:
                result.problems.append(f"DAMAGED FILE: {e}")
                prev = None
                continue
            result.candles[tf] += len(candles)
            result.problems.extend(file_problems(tf, day, candles, b))
            for c in sorted(candles, key=lambda c: c.start):
                if prev is not None:
                    if c.start < prev.end and c.start != prev.start:
                        result.problems.append(f"OUT OF TIME ORDER: {tf} candle {uk_short(c.start)} starts "
                                               f"before the one before it ends ({uk_short(prev.end)})")
                    elif c.start > prev.start:
                        result.gaps.extend(missing_between(tf, prev, c, b))
                prev = c
    result.gaps = mark_known(result.gaps, store)
    return result


def check_new_candle(store: CandleStore, b: Boundaries, c: Candle) -> CheckResult:
    """Check a candle that has just been stored, against its own file and the
    stored candle before it."""
    result = CheckResult()
    day = c.start.astimezone(UTC).date()
    try:
        candles = store.read_day(c.timeframe, day)
    except DamagedFile as e:
        result.problems.append(f"DAMAGED FILE: {e}")
        return result
    result.problems.extend(p for p in file_problems(c.timeframe, day, candles, b)
                           if uk_short(c.start) in p or "DUPLICATE" in p or "OUT OF TIME ORDER in the" in p)
    # The stored candle before it (looking back far enough to cover a long weekend or holiday).
    look_back = timedelta(days=60 if c.timeframe == "1w" else 14)
    before = store.read_range(c.timeframe, c.start - look_back, c.start)
    if before:
        result.gaps.extend(missing_between(c.timeframe, before[-1], c, b))
    result.gaps = mark_known(result.gaps, store)
    return result

