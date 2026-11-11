"""The pace and target rule (owner, 11 November 2026; tested in docs/research/pace_and_target_20261111.md, the
version "within 5 pips, under 5 pips an hour over the last 2 hours"):

  1. While the bot has open trend trades (EMA pullback, slow grind, breakout), no Bollinger bounce may open against
     them unless it opens at a significant level in their direction: a 00, the weekly pivot (from the previous
     week's candle), S2, S3, R2 or R3, with the high (a bounce sell) or low (a bounce buy) the bounce turned from
     within bounce.against_trend_level_within_pips (5) of it.
  2. At that level the bounce is valid only if price has moved under bounce.against_trend_max_pips_per_hour (5) on
     average over the last bounce.against_trend_pace_hours (2). It then opens, and closes every open trade in the
     opposite direction at that moment (trading/engine.py). Otherwise it is refused and the trend trades are held.

Everything is read as at the start of the 5-minute candle the bounce opens in, on the chart (sell) price:
  * the high or low the bounce turned from: the highest high (a sell) or lowest low (a buy) of its setup's
    candles, from the pierce to the confirmation (or the reversal, or the pierce, whichever is last), as the idea
    carries them (strategies/bollinger_bounce/strategy.py, setup_context);
  * the levels: the 00 either side of that price; the weekly pivot, (high + low + close) / 3 of the last finished
    weekly candle, to a tenth; S2, S3, R2 and R3 of the bot's own levels (levels.current.build) at that time;
  * "in their direction": beyond the price at least one of the open trend trades opened at (below it for a bounce
    buy against sells, above it for a bounce sell against buys);
  * the pace: the net move from the close of the last 5-minute candle finished at least `hours` before to the
    last finished close, divided by `hours`. With no candle in the `hours` before that (a gap, the weekend), the
    pace cannot be read and the bounce is not valid.
A bounce with no open trend trade against it is not touched by this rule.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import ROUND_FLOOR, Decimal
from typing import Any

from strategies.common import BOLLINGER_BOUNCE, BREAKOUT, EMA_PULLBACK, SLOW_GRIND

TREND_STRATEGIES = (SLOW_GRIND, EMA_PULLBACK, BREAKOUT)
LEVEL_TYPES = ("S2", "S3", "R2", "R3")

NOT_AT_LEVEL = "not at a significant level"
TOO_FAST = "price moving fast"
PACE_UNKNOWN = "the pace could not be read (no candle that long before)"


@dataclass
class Verdict:
    valid: bool
    reason: str                                     # "" when valid
    against: list[str]                              # the open trend trades it is against
    turned_from: Decimal
    level: str | None                               # the level it is at ("S2 13338.6"), if any
    near: list[str] = field(default_factory=list)   # the nearest levels ahead, with their distance
    pips_per_hour: Decimal | None = None

    def as_dict(self) -> dict:
        return {"valid": self.valid, "reason": self.reason, "against": self.against,
                "turned_from": str(self.turned_from), "level": self.level, "nearest_levels": self.near,
                "pips_per_hour": None if self.pips_per_hour is None else str(self.pips_per_hour.quantize(Decimal("0.1")))}

    def line(self) -> str:
        pace = "unknown" if self.pips_per_hour is None else f"{self.pips_per_hour.quantize(Decimal('0.1'))} pips an hour"
        where = f"at {self.level}" if self.level else ("nearest " + ", ".join(self.near[:2]) if self.near else "no level ahead")
        head = "valid" if self.valid else f"refused: {self.reason}"
        return f"{head} (turned from {self.turned_from}, {where}; {pace}; against {len(self.against)} trend trade(s))"


def trend_trades_against(trades: Any, direction: str) -> list[Any]:
    """The trade manager's open trend trades in the other direction from a bounce."""
    return [t for t in trades if t.open and t.direction != direction and t.strategy in TREND_STRATEGIES]


def turned_from(store: Any, idea: Any) -> Decimal:
    ctx = idea.context
    buy = idea.direction == "buy"
    cs = [c for c in store.read_range("5m", ctx["setup_from"], ctx["setup_last"] + timedelta(minutes=5))
          if c.start <= ctx["setup_last"]]
    prices = [Decimal(c.sell_low if buy else c.sell_high) for c in cs] + [ctx["setup_low" if buy else "setup_high"]]
    return min(prices) if buy else max(prices)


def levels_at(settings: Any, store: Any, price: Decimal, t: datetime) -> list[tuple[str, Decimal]]:
    from levels.current import build
    ppp = Decimal(settings.market.points_per_pip)
    hundred = 100 * ppp
    lo = (price / hundred).to_integral_value(ROUND_FLOOR) * hundred
    out = [("00", lo), ("00", lo + hundred)]
    wk = [c for c in store.read_range("1w", t - timedelta(days=21), t) if c.end <= t]
    if wk:
        w = wk[-1]
        out.append(("weekly pivot", ((Decimal(w.sell_high) + Decimal(w.sell_low) + Decimal(w.sell_close)) / 3)
                    .quantize(Decimal("0.1"))))
    for lv in build(settings, store, t).levels:
        if lv.type in LEVEL_TYPES:
            out.append((lv.type, Decimal(lv.price)))
    return out


def pips_per_hour(settings: Any, store: Any, t: datetime, hours: int) -> Decimal | None:
    ppp = Decimal(settings.market.points_per_pip)
    fin = [c for c in store.read_range("5m", t - timedelta(hours=2 * hours), t) if c.end <= t]
    before = [c for c in fin if c.end <= t - timedelta(hours=hours)]
    if not fin or not before:
        return None
    return abs(Decimal(fin[-1].sell_close) - Decimal(before[-1].sell_close)) / ppp / hours


def check(settings: Any, store: Any, idea: Any, t: datetime, trades: Any) -> Verdict | None:
    """The rule for a Bollinger bounce idea about to be sent, opening in the 5-minute candle starting at t.
    None: not a bounce, or no open trend trade against it (the rule does not apply)."""
    if idea.strategy != BOLLINGER_BOUNCE:
        return None
    opp = trend_trades_against(trades, idea.direction)
    if not opp:
        return None
    b = settings.bounce
    ppp = Decimal(settings.market.points_per_pip)
    buy = idea.direction == "buy"
    against = [f"{x.strategy} {x.direction} {x.reference} at {x.fill}" for x in opp]
    ext = turned_from(store, idea)
    fills = [Decimal(x.fill) for x in opp]
    ahead = [(n, p) for n, p in levels_at(settings, store, ext, t) if (p < max(fills) if buy else p > min(fills))]
    near = sorted((abs(ext - p) / ppp, n, p) for n, p in ahead)
    within = Decimal(str(b.against_trend_level_within_pips))
    hits = [x for x in near if x[0] <= within]
    shown = [f"{n} {p} ({d.quantize(Decimal('0.1'))} pips)" for d, n, p in near[:3]]
    rate = pips_per_hour(settings, store, t, b.against_trend_pace_hours)
    if not hits:
        return Verdict(False, NOT_AT_LEVEL, against, ext, None, shown, rate)
    level = f"{hits[0][1]} {hits[0][2]}"
    if rate is None:
        return Verdict(False, PACE_UNKNOWN, against, ext, level, shown, rate)
    if rate >= Decimal(str(b.against_trend_max_pips_per_hour)):
        return Verdict(False, TOO_FAST, against, ext, level, shown, rate)
    return Verdict(True, "", against, ext, level, shown, rate)
