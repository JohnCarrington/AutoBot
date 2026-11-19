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

Dominant structure (owner's approval of candidate C, 19 November 2026; D-20, design 6.2/6.3): `structure` above is
the OBSERVED swing sequence and is never changed; `dominant_structure` is the CONFIRMED one used for the 4-hour
direction. They differ only in this case: the observed sequence is mixed because the latest swing high went above the
previous swing high by a wick only (no confirmed close at least 3 pips above the previous high, the P-B10/P-B11
rule), while the swings before it made a down structure (an established trend). Then:
  unresolved   no confirmed close either way since the sweep: it stays mixed (NEUTRAL), with the reason
               "sweep unresolved". A sweep never establishes a direction by itself;
  rejected     a confirmed close (the same rule) at least 3 pips below the last swing low made before the sweep, on a
               candle after the sweep candle: down again. The swings are kept as found: the sweep high stays the
               last swing high (the impulse starts from it; a confirmed close above it is a structural break);
  confirmed    a close at least 3 pips above the previous swing high: a real higher high, the observed (mixed)
               sequence stands.
The mirror image applies to a wick-only lower low in an up structure. No new number; the daily chart is unaffected.

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
    sweep: dict | None = None           # dominant_structure only: a wick-only sweep, "unresolved" or "rejected"


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


def _sweep(settings: Any, candles: Sequence[Candle], timeframe: str, found: list[Swing], st: Structure,
           bear: bool) -> Structure | None:
    """The dominant structure when `st` is mixed only by a wick-only sweep against an established trend (see the
    module text), else None. bear: a swing high above the previous one in a down structure; otherwise the mirror."""
    h0, h1 = st.highs
    l0, l1 = st.lows
    if not (h1.price > h0.price and l1.price < l0.price):
        return None
    sw, held = (h1, h0) if bear else (l1, l0)
    if broke(settings, candles, held, UP if bear else DOWN) is not None:
        return None                                    # a confirmed close beyond the earlier swing: a real break
    prior = structure(settings, candles, timeframe, [s for s in found if s is not sw])
    if prior.sequence != (DOWN if bear else UP):
        return None                                    # no established trend before the sweep: mixed stands
    other = [s for s in found if s.kind == ("low" if bear else "high") and s.candle_utc < sw.candle_utc]
    if not other:
        return None
    anchor = other[-1]                                 # the last swing on the other side made before the sweep
    after_sweep = Swing(anchor.kind, anchor.price, anchor.timeframe, anchor.candle_utc, anchor.known_utc,
                        max(anchor.index, sw.index))   # closes on candles after the sweep candle only
    c = broke(settings, candles, after_sweep, DOWN if bear else UP)
    said = (f"swing {sw.kind} {plain(sw.price)} went {'above' if bear else 'below'} the previous swing {sw.kind} "
            f"{plain(held.price)} by a wick only (no 4-hour close 3 pips beyond it)")
    info = {"swing": sw.kind, "price": plain(sw.price), "beyond": plain(held.price),
            "candle_utc": sw.candle_utc.strftime("%Y-%m-%dT%H:%M:%SZ"), "resolve_beyond": plain(anchor.price)}
    if c is None:
        return Structure(timeframe, MIXED, st.highs, st.lows, None,
                         f"{st.why}; {said}: sweep unresolved (no confirmed close either way yet; it resolves on a "
                         f"confirmed close beyond the swing {anchor.kind} {plain(anchor.price)})",
                         info | {"state": "unresolved"})
    side = side_of(settings)
    return Structure(timeframe, DOWN if bear else UP, st.highs, st.lows, None,
                     f"{'lower highs and lower lows' if bear else 'higher highs and higher lows'} confirmed: {said}; "
                     f"then the {uk_short(c.start)} 4-hour candle closed {plain(cl(c, side))}, beyond the swing "
                     f"{anchor.kind} {plain(anchor.price)}: the sweep was rejected (observed swings: {st.why[7:]})",
                     info | {"state": "rejected", "rejected_by_close_utc": c.start.strftime("%Y-%m-%dT%H:%M:%SZ")})


def dominant_structure(settings: Any, candles: Sequence[Candle], timeframe: str,
                       found: list[Swing] | None = None) -> Structure:
    """The confirmed structure for the dominant direction (see the module text): the observed structure, except a
    mixed one caused only by a wick-only sweep of an established trend."""
    found = swings(settings, candles, timeframe) if found is None else found
    st = structure(settings, candles, timeframe, found)
    if st.sequence != MIXED or len(st.highs) < 2 or len(st.lows) < 2:
        return st
    for bear in (True, False):
        r = _sweep(settings, candles, timeframe, found, st, bear)
        if r is not None:
            return r
    return st


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
