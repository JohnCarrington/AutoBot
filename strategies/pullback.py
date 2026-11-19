"""The pullback entry (owner, approved 19 November 2026), only for the breakout and the Asian range breakout, while
the switch PULLBACK_ENTRY is on (on if left out). Written for a buy; a sell is the mirror image. Sell (bid) price,
as on the chart; the 5-minute EMAs are the strategies' own 8 and 21 (ema_pullback.fast_ema_periods and
slow_ema_periods), as they stand after each finished candle.

  1. When the strategy sees its break it does not open: it waits, from the candle after the break candle.
  2. Entry: a candle's low reaches the 8 EMA (a sell: its high), and a candle closes above the 8 EMA (a sell: below);
     the same candle may do both. The trade opens at the next candle's open (owner's answers 1, 2 and 4).
  3. Wait: the confirming close must come within pullback_entry.wait_candles (6) candles after the break candle; the
     trade then opens at the next candle's open, so the 7th at the latest (answer 5). No entry by then: no trade.
  4. Cancel: a candle that closes below the 21 EMA (a sell: above) cancels it: no trade.
Each strategy's stop, take profit and trade management are unchanged (answer 3). Ideas only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from prices.model import Candle, plain, uk_short
from strategies.common import BUY

WAITING, CONFIRMED, CANCELLED, EXPIRED = "waiting", "confirmed", "cancelled", "expired"


def pullback_on(settings: Any) -> bool:
    """The switch PULLBACK_ENTRY (on if left out of .env)."""
    return bool(getattr(getattr(settings, "switches", None), "pullback_entry", False))


@dataclass
class Wait:
    direction: str
    break_candle: Candle
    steps: list = field(default_factory=list)
    context: dict = field(default_factory=dict)
    waited: int = 0
    touched: bool = False


def advance(w: Wait, c: Candle, fast: Decimal | None, slow: Decimal | None, limit: int, side: str) -> tuple[str, str]:
    """One finished candle after the break candle: (WAITING, CONFIRMED, CANCELLED or EXPIRED, what happened)."""
    buy = w.direction == BUY
    w.waited += 1
    close, low, high = (getattr(c, f"{side}_{x}") for x in ("close", "low", "high"))
    q = lambda x: plain(x.quantize(Decimal("0.1")))   # noqa: E731
    if slow is not None and (close < slow if buy else close > slow):
        return CANCELLED, (f"{uk_short(c.start)} closed {plain(close)} {'below' if buy else 'above'} the 21 EMA "
                           f"{q(slow)}: cancelled, no trade")
    if fast is not None:
        if low <= fast if buy else high >= fast:
            if not w.touched:
                w.steps.append(f"{uk_short(c.start)}: price came back to the 8 EMA {q(fast)} "
                               f"({'low' if buy else 'high'} {plain(low if buy else high)})")
            w.touched = True
        if w.touched and (close > fast if buy else close < fast):
            w.steps.append(f"{uk_short(c.start)}: closed {plain(close)} {'above' if buy else 'below'} the 8 EMA "
                           f"{q(fast)}, candle {w.waited} of {limit} after the break")
            return CONFIRMED, f"confirmed at {uk_short(c.start)}"
    if w.waited >= limit:
        return EXPIRED, f"no entry within {limit} candles after the break candle: no trade"
    return WAITING, ""


def started(w: Wait, limit: int, what: str) -> None:
    """The step recorded when the wait starts."""
    side = "low reaches" if w.direction == BUY else "high reaches"
    w.steps.append(f"PULLBACK_ENTRY: not opened on the break; waiting up to {limit} candles for a candle whose {side} "
                   f"the 8 EMA, then a close back {'above' if w.direction == BUY else 'below'} it ({what})")
