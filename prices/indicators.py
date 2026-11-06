"""Indicators worked out from stored candles, for the rejection part, the
analyser and the strategies. Every indicator uses the chart price (settings
[chart] price: the SELL (bid) price, as on the owner's IG chart).

Bollinger bands (settings [indicators]): the middle band is the simple average
of the last `periods` closes (this candle's close included); the upper and
lower bands are the middle band plus and minus `std_devs` standard deviations
of those same closes. The standard deviation is the population one (divide by
`periods`), as charting packages normally draw it. Candles are taken in order
as on the chart: the weekend is simply skipped.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Sequence

from prices.model import Candle


@dataclass(frozen=True)
class Band:
    candle_utc: datetime        # start of the candle the band is worked out at (its close included)
    middle: Decimal
    upper: Decimal
    lower: Decimal


def bollinger(candles: Sequence[Candle], side: str, periods: int, std_devs: int) -> dict[datetime, Band]:
    """The Bollinger band at each candle that has `periods` candles up to and
    including it. Keyed by candle start. Earlier candles have no band."""
    closes = [getattr(c, f"{side}_close") for c in candles]
    out: dict[datetime, Band] = {}
    n = Decimal(periods)
    for i in range(periods - 1, len(candles)):
        window = closes[i - periods + 1:i + 1]
        mid = sum(window) / n
        var = sum((x - mid) ** 2 for x in window) / n
        sd = var.sqrt()
        out[candles[i].start] = Band(candles[i].start, mid, mid + std_devs * sd, mid - std_devs * sd)
    return out
