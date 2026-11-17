"""Market structure for the planner (D-05, D-20; parameters P-B1 to P-B13). Sell price, finished candles only.

Swings: the bot's existing turning-level rule (levels/rules.py turning_levels) with each timeframe's approved
numbers: a swing high is higher than the highs of N candles before it, not lower than the highs of N candles after
it, and price then moves at least M pips below it within K candles; a swing low is the mirror image.
  hourly   N 3, M 20 pips, K 6   ([levels] turning_*; EXISTING)
  4-hour   N 3, M 40 pips, K 6   ([planner] h4_swing_*; provisional, owner 17 November 2026)
  daily    N 3, M 110 pips, K 6  ([planner] daily_swing_*; provisional, owner 17 November 2026)
A swing is used only once the candles that rule needs have finished: `known_utc` is the end of the candle that
completed it (the later of the N-th candle after it and the first candle that made the move).

Structure (P-B12): from the last two confirmed swing highs and the last two confirmed swing lows:
  up    both higher;   down    both lower;   otherwise mixed.
A confirmed break (P-B10, P-B11): planner.structure_break_closes candle close(s) in a row at least
hourly_read.break_beyond_pips (3) beyond the level (the hourly read's own rule, verified). Wicks never count.

Threshold misses (owner's adjustment 2, 17 November 2026): a turn that passes the candles-each-side test but not the
minimum move, and is the most extreme price since the last confirmed swing of its kind, is recorded with the move it
did make, so it can be reviewed. The thresholds are never changed automatically.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Sequence

from levels.rules import turning_levels
from planner.measure import cl, hi, lo, ppp, side_of
from prices.model import Candle, plain, uk_short

UP, DOWN, MIXED = "up", "down", "mixed"


@dataclass(frozen=True)
class Swing:
    kind: str                   # "high" or "low"
    price: Decimal
    timeframe: str
    candle_utc: datetime        # start of the swing candle
    known_utc: datetime         # when it could first be known (end of the candle that completed the rule)
    index: int                  # its position in the candles given

    def describe(self) -> str:
        return f"{self.timeframe} swing {self.kind} {plain(self.price)} ({uk_short(self.candle_utc)})"


def swing_settings(settings: Any, timeframe: str) -> tuple[int, Decimal, int]:
    """(candles each side, minimum move in points, move within) for a timeframe."""
    if timeframe == "1h":
        lv = settings.levels
        return lv.turning_candles_each_side, Decimal(lv.turning_min_move_pips) * ppp(settings), \
            lv.turning_move_within_candles
    p = settings.planner
    key = {"4h": "h4", "1d": "daily"}[timeframe]
    return (getattr(p, f"{key}_swing_candles_each_side"),
            Decimal(getattr(p, f"{key}_swing_min_move_pips")) * ppp(settings),
            getattr(p, f"{key}_swing_move_within_candles"))


def _known(candles: Sequence[Candle], i: int, kind: str, price: Decimal, each: int, move: Decimal, within: int,
           side: str) -> datetime:
    j = i + each
    for k in range(i + 1, min(len(candles), i + 1 + within)):
        if (kind == "high" and lo(candles[k], side) <= price - move) or \
                (kind == "low" and hi(candles[k], side) >= price + move):
            j = max(j, k)
            break
    return candles[min(j, len(candles) - 1)].end


def swings(settings: Any, candles: Sequence[Candle], timeframe: str, min_move: Decimal | None = None) -> list[Swing]:
    """Every confirmed swing in the given finished candles (oldest first), by the existing turning-level rule."""
    side = side_of(settings)
    each, move, within = swing_settings(settings, timeframe)
    if min_move is not None:
        move = min_move
    cs = list(candles)
    if not cs:
        return []
    found = turning_levels(cs, side, cs[0].start, each, move, within, lambda c, which: "")
    index = {c.start: i for i, c in enumerate(cs)}
    out = []
    for lv in found:
        i = index[lv.candle_utc]
        kind = "high" if lv.type == "turning_high" else "low"
        out.append(Swing(kind, lv.price, timeframe, lv.candle_utc,
                         _known(cs, i, kind, lv.price, each, move, within, side), i))
    return sorted(out, key=lambda s: (s.candle_utc, s.kind))


@dataclass
class Structure:
    timeframe: str
    sequence: str                       # up, down or mixed
    highs: list[Swing]                  # the last two confirmed swing highs (oldest first), if any
    lows: list[Swing]
    broken: tuple[str, Candle, Swing] | None   # ("up"/"down", the breaking candle, the swing it broke)
    why: str


def broke(settings: Any, candles: Sequence[Candle], after: Swing, direction: str) -> Candle | None:
    """The first candle after the swing that completes structure_break_closes closes in a row at least
    break_beyond_pips beyond it (`direction` up: above a swing high; down: below a swing low)."""
    side = side_of(settings)
    beyond = Decimal(settings.hourly_read.break_beyond_pips) * ppp(settings)
    need = settings.planner.structure_break_closes
    run = 0
    for c in candles[after.index + 1:]:
        ok = cl(c, side) >= after.price + beyond if direction == UP else cl(c, side) <= after.price - beyond
        run = run + 1 if ok else 0
        if run >= need:
            return c
    return None


def structure(settings: Any, candles: Sequence[Candle], timeframe: str, found: list[Swing] | None = None) -> Structure:
    found = swings(settings, candles, timeframe) if found is None else found
    highs = [s for s in found if s.kind == "high"][-2:]
    lows = [s for s in found if s.kind == "low"][-2:]
    if len(highs) < 2 or len(lows) < 2:
        return Structure(timeframe, MIXED, highs, lows, None,
                         f"too few confirmed {timeframe} swings ({len(highs)} highs, {len(lows)} lows; 2 of each needed)")
    up_h, up_l = highs[1].price > highs[0].price, lows[1].price > lows[0].price
    dn_h, dn_l = highs[1].price < highs[0].price, lows[1].price < lows[0].price
    said = (f"swing highs {plain(highs[0].price)} then {plain(highs[1].price)}, "
            f"swing lows {plain(lows[0].price)} then {plain(lows[1].price)}")
    if dn_h and dn_l:
        b = broke(settings, candles, highs[1], UP)
        return Structure(timeframe, DOWN, highs, lows, (UP, b, highs[1]) if b else None, "lower highs and lower lows: " + said)
    if up_h and up_l:
        b = broke(settings, candles, lows[1], DOWN)
        return Structure(timeframe, UP, highs, lows, (DOWN, b, lows[1]) if b else None, "higher highs and higher lows: " + said)
    return Structure(timeframe, MIXED, highs, lows, None, "mixed: " + said)


def threshold_misses(settings: Any, candles: Sequence[Candle], timeframe: str, confirmed: list[Swing]) -> list[dict]:
    """Turns held back only by the minimum move (adjustment 2): for each kind, the most extreme shape-only turn since
    the last confirmed swing of that kind, if it is not itself confirmed."""
    side = side_of(settings)
    each, move, within = swing_settings(settings, timeframe)
    shape_only = swings(settings, candles, timeframe, min_move=Decimal(0))
    out = []
    for kind in ("high", "low"):
        last = [s for s in confirmed if s.kind == kind]
        since = last[-1].candle_utc if last else None
        cands = [s for s in shape_only if s.kind == kind and (since is None or s.candle_utc > since)
                 and not any(c.candle_utc == s.candle_utc and c.kind == kind for c in confirmed)]
        if not cands:
            continue
        s = max(cands, key=lambda x: x.price) if kind == "high" else min(cands, key=lambda x: x.price)
        window = candles[s.index + 1:s.index + 1 + within]
        if not window:
            continue
        made = (s.price - min(lo(c, side) for c in window)) if kind == "high" else \
            (max(hi(c, side) for c in window) - s.price)
        if made < move:
            out.append({"timeframe": timeframe, "kind": kind, "price": plain(s.price),
                        "candle_utc": s.candle_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "moved_pips": plain((made / ppp(settings)).quantize(Decimal("0.1"))),
                        "needed_pips": plain((move / ppp(settings)).quantize(Decimal("0.1"))),
                        "note": f"a {timeframe} turn at {plain(s.price)} moved {plain((made / ppp(settings)).quantize(Decimal('0.1')))} "
                                f"pips within {within} candles, short of the {plain((move / ppp(settings)).quantize(Decimal('0.1')))} needed: "
                                f"not counted as a swing (provisional threshold, recorded for review)"})
    return out
