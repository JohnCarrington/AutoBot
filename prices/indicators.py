"""Indicators worked out from stored candles, for the rejection part, the
analyser and the strategies. Every indicator uses the chart price (settings
[chart] price: the SELL (bid) price, as on the owner's IG chart).

Bollinger bands (settings [indicators]): the middle band is the simple average
of the last `periods` closes (this candle's close included); the upper and
lower bands are the middle band plus and minus `std_devs` standard deviations
of those same closes. The standard deviation is the population one (divide by
`periods`), as charting packages normally draw it. Candles are taken in order
as on the chart: the weekend is simply skipped.

EMA (exponential moving average) of `periods`: it starts at the candle that
completes the first `periods` closes, as the simple average of them; after
that each value = previous + (close - previous) x 2 / (periods + 1).

MACD (fast, slow, signal): MACD line = EMA(fast) - EMA(slow) of the closes;
signal line = EMA(signal) of the MACD line (started the same way, from the
simple average of its first `signal` values); histogram = MACD line - signal.

RSI of `periods` (Wilder's, the usual RSI): from the close-to-close changes.
The first average gain and loss are the simple averages of the first `periods`
changes; after that each = (previous x (periods - 1) + this change) / periods.
RSI = 100 - 100 / (1 + average gain / average loss) (100 when there is no
loss, 50 when there is neither gain nor loss).

Warming up: an EMA, MACD or RSI starts from a guess (the simple average), and
every later candle shrinks that guess's share of the value. needs_*() give how
many candles it takes for the guess to count for no more than a given percent:
until then the value is "warming up" (docs/ANALYSER.md).
"""

from __future__ import annotations

import math
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


def _closes(candles: Sequence[Candle], side: str) -> list[Decimal]:
    return [getattr(c, f"{side}_close") for c in candles]


def _ema_values(values: Sequence[Decimal], periods: int) -> list[Decimal | None]:
    """EMA of a list of values: None until the first `periods` values are in."""
    out: list[Decimal | None] = [None] * len(values)
    if len(values) < periods:
        return out
    k = Decimal(2) / Decimal(periods + 1)
    e = sum(values[:periods]) / Decimal(periods)
    out[periods - 1] = e
    for i in range(periods, len(values)):
        e = e + (values[i] - e) * k
        out[i] = e
    return out


def ema(candles: Sequence[Candle], side: str, periods: int) -> dict[datetime, Decimal]:
    """The EMA at each candle from the one that completes the first `periods`
    closes. Keyed by candle start (that candle's close included)."""
    vals = _ema_values(_closes(candles, side), periods)
    return {c.start: v for c, v in zip(candles, vals) if v is not None}


@dataclass(frozen=True)
class Macd:
    candle_utc: datetime
    line: Decimal
    signal: Decimal
    histogram: Decimal


def macd(candles: Sequence[Candle], side: str, fast: int, slow: int, signal: int) -> dict[datetime, Macd]:
    closes = _closes(candles, side)
    f, s = _ema_values(closes, fast), _ema_values(closes, slow)
    first = slow - 1
    if len(closes) <= first:
        return {}
    line = [f[i] - s[i] for i in range(first, len(closes))]
    sig = _ema_values(line, signal)
    out: dict[datetime, Macd] = {}
    for j, sv in enumerate(sig):
        if sv is not None:
            c = candles[first + j]
            out[c.start] = Macd(c.start, line[j], sv, line[j] - sv)
    return out


def rsi(candles: Sequence[Candle], side: str, periods: int) -> dict[datetime, Decimal]:
    closes = _closes(candles, side)
    if len(closes) <= periods:
        return {}
    n = Decimal(periods)
    changes = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gain = sum(max(d, Decimal(0)) for d in changes[:periods]) / n
    loss = sum(max(-d, Decimal(0)) for d in changes[:periods]) / n
    out: dict[datetime, Decimal] = {}

    def value() -> Decimal:
        if loss == 0:
            return Decimal(50) if gain == 0 else Decimal(100)
        return Decimal(100) - Decimal(100) / (1 + gain / loss)
    out[candles[periods].start] = value()
    for i in range(periods, len(changes)):
        d = changes[i]
        gain = (gain * (n - 1) + max(d, Decimal(0))) / n
        loss = (loss * (n - 1) + max(-d, Decimal(0))) / n
        out[candles[i + 1].start] = value()
    return out


def _more_for(share_left_each_candle: float, percent: int) -> int:
    """Candles after the start for the starting guess to shrink to `percent`."""
    return max(0, math.ceil(math.log(percent / 100) / math.log(share_left_each_candle)))


def needs_ema(periods: int, percent: int) -> int:
    """Candles an EMA needs before it is ready (warmed up)."""
    return periods + _more_for(1 - 2 / (periods + 1), percent)


def needs_macd(fast: int, slow: int, signal: int, percent: int) -> int:
    return max(needs_ema(fast, percent), needs_ema(slow, percent), slow - 1 + needs_ema(signal, percent))


def needs_rsi(periods: int, percent: int) -> int:
    return periods + 1 + _more_for(1 - 1 / periods, percent)
