"""The entry filters (owner, 21 November 2026): two rules checked once for every trade, at one point, just before it
opens (trading/engine.py, Trading._place, before the order sender's safety rules). No strategy's own code changes;
each strategy's rules, stops, take profits and trade management stay as they are. Each rule has its own switch.

RULE 1. HOURLY CONTEXT (switch HOURLY_CONTEXT, on if left out). Every strategy.
  DOWN context: the last two hourly swing highs are lower highs (the latest swing high is lower than the one before
  it), AND the last finished hourly candle closed below the hourly 50 EMA, AND the hourly 50 EMA is falling (lower
  than [entry_filters] hourly_ema_slope_candles (6) hourly candles before).
  UP context: the mirror: the latest hourly swing low is higher than the one before it, the last hourly close is
  above the 50 EMA, and the 50 EMA is rising.
  In a DOWN context no BUY opens when the entry price is within hourly_context_near_pips (5) of the daily pivot or
  the hourly 50 EMA; in an UP context no SELL opens when the entry price is within 5 pips of either.
  A swing high: an hourly candle whose high has hourly_swing_candles_each_side (2) lower hourly highs on each side
  (a swing low: 2 higher lows on each side); only finished hourly candles, so a swing is known 2 hours after it.

RULE 2. ENTRY LOCATION (switch ENTRY_NEAR_EMA8, on if left out).
  A SELL opens only if the entry price is no more than ema8_max_distance_pips (5) below the 5-minute 8 EMA (at it,
  above it, or up to 5 pips below); a BUY only if it is no more than 5 pips above it. The 8 EMA on the sell price at
  the last finished 5-minute candle before the entry. The slow grind, the breakout, the Asian range breakout and the
  session sweep are exempt (the session sweep: owner, 21 November 2026, after the check of the 19 November 12:10 sell).

The owner's answers (21 November 2026): the entry price is the strategy's own entry price (the sell / chart price,
as the bot records entry_price), for buys too; "price below / above the hourly 50 EMA" is the last finished hourly
candle's close against the 50 EMA at that candle. Everything is on the chart (sell) price: the hourly candles, the
50 EMA, the 8 EMA and the daily pivot (the bot's own pivot, levels/current.py). "Within 5 pips" includes exactly 5;
"no more than 5 pips" allows exactly 5.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from analyser.indicators import last_candles
from levels.current import build as build_levels
from levels.rules import PIVOT
from prices.indicators import ema
from prices.model import plain
from strategies.common import ASIAN_RANGE_BREAKOUT, BREAKOUT, SESSION_SWEEP, SLOW_GRIND

HOURLY_CONTEXT = "hourly context"
ENTRY_NEAR_EMA8 = "entry near the 8 EMA"
EMA8_EXEMPT = (SLOW_GRIND, BREAKOUT, ASIAN_RANGE_BREAKOUT, SESSION_SWEEP)          # owner, 21 November 2026
DOWN, UP = "down", "up"


@dataclass
class Context:
    """The hourly context at a moment: DOWN, UP or None, with what it was worked out from."""
    kind: str | None
    why: str
    ema50: Decimal | None = None
    ema50_before: Decimal | None = None
    close: Decimal | None = None
    swings: tuple = ()                                   # (earlier, latest) swing highs (DOWN) or lows (UP): (time, price)


@dataclass
class Verdict:
    allowed: bool
    rule: str = ""                                       # the rule that refused it ("" when allowed)
    why: str = ""                                        # one line, for the records
    details: dict = field(default_factory=dict)          # the numbers, for the records
    checked: list[str] = field(default_factory=list)     # what was checked (allowed or not), for the records


def swings(candles: list, side: str, each_side: int, high: bool) -> list:
    """[(time, price)] of every swing high (high=True) or swing low in `candles`, oldest first: a candle whose high
    has `each_side` strictly lower highs on each side (a low: strictly higher lows)."""
    vals = [getattr(c, f"{side}_high" if high else f"{side}_low") for c in candles]
    out = []
    for i in range(each_side, len(vals) - each_side):
        others = vals[i - each_side:i] + vals[i + 1:i + 1 + each_side]
        if all((v < vals[i]) if high else (v > vals[i]) for v in others):
            out.append((candles[i].start, vals[i]))
    return out


def hourly_context(settings: Any, store: Any, at: datetime) -> Context:
    f, side = settings.entry_filters, settings.chart.price
    hc = last_candles(store, "1h", at, settings.indicators.history_candles)
    k = f.hourly_ema_slope_candles
    if len(hc) < f.hourly_ema_periods + k:
        return Context(None, f"not enough finished hourly candles ({len(hc)}) for the 50 EMA and its slope: "
                             "no context")
    e = ema(hc, side, f.hourly_ema_periods)
    last, before = hc[-1], hc[-1 - k]
    e_now, e_before = e.get(last.start), e.get(before.start)
    close = getattr(last, f"{side}_close")
    if e_now is None or e_before is None:
        return Context(None, "the hourly 50 EMA is not worked out yet: no context")
    highs = swings(hc, side, f.hourly_swing_candles_each_side, True)
    lows = swings(hc, side, f.hourly_swing_candles_each_side, False)
    hh = f"{last.start:%a %d %b %H:%M}"
    base = (f"last hourly close {plain(close)} ({hh} candle), 50 EMA {e_now:.1f}, {k} candles before {e_before:.1f}")
    if len(highs) >= 2 and highs[-1][1] < highs[-2][1] and close < e_now and e_now < e_before:
        return Context(DOWN, f"DOWN context: lower high {plain(highs[-1][1])} ({highs[-1][0]:%a %H:%M}) after "
                             f"{plain(highs[-2][1])} ({highs[-2][0]:%a %H:%M}); {base}: close below it and falling",
                       e_now, e_before, close, (highs[-2], highs[-1]))
    if len(lows) >= 2 and lows[-1][1] > lows[-2][1] and close > e_now and e_now > e_before:
        return Context(UP, f"UP context: higher low {plain(lows[-1][1])} ({lows[-1][0]:%a %H:%M}) after "
                           f"{plain(lows[-2][1])} ({lows[-2][0]:%a %H:%M}); {base}: close above it and rising",
                       e_now, e_before, close, (lows[-2], lows[-1]))
    parts = []
    if len(highs) >= 2:
        parts.append(f"swing highs {plain(highs[-2][1])} then {plain(highs[-1][1])}")
    if len(lows) >= 2:
        parts.append(f"swing lows {plain(lows[-2][1])} then {plain(lows[-1][1])}")
    return Context(None, "no DOWN or UP context: " + "; ".join(parts + [base]), e_now, e_before, close)


def daily_pivot(settings: Any, store: Any, at: datetime) -> Decimal | None:
    """The daily pivot as the bot's levels had it at `at` (levels/current.py)."""
    for lv in build_levels(settings, store, at).levels:
        if lv.type == PIVOT:
            return lv.price
    return None


def ema8_at(settings: Any, store: Any, at: datetime) -> tuple[Decimal | None, Any]:
    """The 5-minute 8 EMA (sell price) at the last 5-minute candle finished by `at`, and that candle."""
    f = settings.entry_filters
    c5 = last_candles(store, "5m", at, settings.indicators.history_candles)
    if len(c5) < f.ema8_periods:
        return None, None
    return ema(c5, settings.chart.price, f.ema8_periods).get(c5[-1].start), c5[-1]


def check(settings: Any, store: Any, idea: Any) -> Verdict:
    """Both rules, as their switches say, for one trade about to open. The first rule that refuses it is given."""
    sw, f = settings.switches, settings.entry_filters
    ppp = Decimal(settings.market.points_per_pip)
    at, price, buy = idea.time, Decimal(idea.entry_price), idea.direction == "buy"
    checked: list[str] = []

    if sw.hourly_context:
        ctx = hourly_context(settings, store, at)
        against = (ctx.kind == DOWN and buy) or (ctx.kind == UP and not buy)
        if against:
            near = Decimal(f.hourly_context_near_pips)
            piv = daily_pivot(settings, store, at)
            lines = [("the daily pivot", piv)] + [("the hourly 50 EMA", ctx.ema50)]
            hits = [(name, lv, abs(price - lv) / ppp) for name, lv in lines if lv is not None and abs(price - lv) / ppp <= near]
            if hits:
                name, lv, dist = min(hits, key=lambda h: h[2])
                why = (f"{ctx.why}. A {idea.direction.upper()} at {plain(price)} is {dist:.1f} pips from {name} "
                       f"{lv:.1f} (within {plain(near)}): refused")
                return Verdict(False, HOURLY_CONTEXT, why, {
                    "context": ctx.kind, "entry_price": str(price), "line": name, "line_price": f"{lv:.1f}",
                    "pips_from_line": f"{dist:.1f}", "daily_pivot": None if piv is None else str(piv),
                    "hourly_ema50": f"{ctx.ema50:.1f}", "hourly_ema50_before": f"{ctx.ema50_before:.1f}",
                    "last_hourly_close": str(ctx.close),
                    "swings": [[f"{t:%Y-%m-%dT%H:%MZ}", str(p)] for t, p in ctx.swings]}, checked)
            checked.append(f"hourly context: {ctx.why}; the {idea.direction} is not within {plain(near)} pips of the "
                           f"daily pivot ({'none' if piv is None else plain(piv)}) or the 50 EMA ({ctx.ema50:.1f})")
        else:
            checked.append(f"hourly context: {ctx.why}")

    if sw.entry_near_ema8:
        if idea.strategy in EMA8_EXEMPT:
            checked.append(f"entry near the 8 EMA: {idea.strategy} is exempt")
        else:
            e8, c = ema8_at(settings, store, at)
            if e8 is None:
                checked.append("entry near the 8 EMA: the 5-minute 8 EMA is not worked out yet: not checked")
            else:
                limit = Decimal(f.ema8_max_distance_pips)
                beyond = (price - e8) / ppp if buy else (e8 - price) / ppp     # pips above (buy) / below (sell) it
                side = "above" if buy else "below"
                line = (f"entry {plain(price)}, 5-minute 8 EMA {e8:.1f} (at the {c.start:%H:%M} candle), "
                        f"{abs(beyond):.1f} pips {side if beyond >= 0 else ('below' if buy else 'above')} it")
                if beyond > limit:
                    why = (f"a {idea.direction.upper()} more than {plain(limit)} pips {side} the 5-minute 8 EMA: "
                           f"{line}: refused")
                    return Verdict(False, ENTRY_NEAR_EMA8, why, {
                        "entry_price": str(price), "ema8_5m": f"{e8:.1f}", "ema8_candle": f"{c.start:%Y-%m-%dT%H:%MZ}",
                        "pips_beyond_ema8": f"{beyond:.1f}", "limit_pips": str(limit)}, checked)
                checked.append(f"entry near the 8 EMA: {line}: allowed")
    return Verdict(True, checked=checked)
