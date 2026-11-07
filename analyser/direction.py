"""The direction rule (design section 2.3), which applies to every strategy except
the range trade, the Bollinger bounce and the breakout (strategies/common.py applies it):

  BUY SIDE   price above the daily pivot AND above the 5-minute 100 EMA;
  SELL SIDE  price below the daily pivot AND below the 5-minute 100 EMA;
  NONE       otherwise (they disagree, or price is exactly on one of them):
             no clear direction.

Everything uses the chart price (settings [chart] price: the SELL (bid) price).
"Price" is the live sell price when one is given; otherwise the close of the
latest finished candle on analyser.direction_ema_timeframe (which is what a
replay of stored candles has). The EMA is the one at that latest finished
candle, and the pivot is today's daily pivot, from the levels part.
The EMA timeframe and periods are settings [analyser] direction_ema_*.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

BUY_SIDE, SELL_SIDE, NONE = "buy side", "sell side", "no clear direction"


@dataclass(frozen=True)
class Direction:
    side: str                   # BUY_SIDE, SELL_SIDE or NONE
    price: Decimal | None
    price_from: str             # where the price came from
    pivot: Decimal | None
    ema: Decimal | None
    ema_name: str               # e.g. "5m 100 EMA"
    ema_ready: bool
    reason: str

    @property
    def allows_buy(self) -> bool:
        return self.side == BUY_SIDE

    @property
    def allows_sell(self) -> bool:
        return self.side == SELL_SIDE


def _where(price: Decimal, line: Decimal) -> str:
    return "above" if price > line else "below" if price < line else "exactly on"


def decide(price: Decimal | None, price_from: str, pivot: Decimal | None, ema: Decimal | None,
           ema_name: str, ema_ready: bool) -> Direction:
    def d(side: str, reason: str) -> Direction:
        return Direction(side, price, price_from, pivot, ema, ema_name, ema_ready, reason)
    if price is None:
        return d(NONE, "no price yet")
    if pivot is None:
        return d(NONE, "no daily pivot (the previous day's daily candle is not stored)")
    if ema is None:
        return d(NONE, f"no {ema_name} yet")
    p, e = _where(price, pivot), _where(price, ema)
    said = f"price {price} is {p} the pivot {pivot} and {e} the {ema_name} {ema.quantize(Decimal('0.1'))}"
    if p == e == "above":
        return d(BUY_SIDE, said)
    if p == e == "below":
        return d(SELL_SIDE, said)
    return d(NONE, said + ": they disagree" if "exactly on" not in (p, e) else said)
