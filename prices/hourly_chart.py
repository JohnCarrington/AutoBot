"""The bot's own hourly chart for the Bollinger bounce (design 3.3; owner, 15 November 2026): hourly candles built
from the same IG 5-minute candles as the 5-minute chart, on the chart (sell) price, and the hourly Bollinger band
(indicators.bollinger_periods, 20; indicators.bollinger_std_devs, 2) worked out live, including during the hour
that is still forming, as the owner's IG hourly chart shows it.

  * An hour's candle is the 5-minute candles in it, on the same boundaries as the candle store's 1-hour candles
    (prices/calendar.py Boundaries.bucket): its open is the first one's open, its high and low the highest and
    lowest, its close the last one's close. These are the store's own 1-hour candles (prices/builder.py builds
    them the same way); over 25 October to 6 November 2026 every one of the 241 hours IG's own hourly candles
    overlap had all 8 prices equal to IG's.
  * The band at a price, during an hour: the last 19 finished hourly closes and that price as the forming hour's
    close (IG's chart moves the forming hour's band with the price). At the moment of a 5-minute candle's high the
    upper band the chart showed is the band with the high as the close; at its low, the lower band with the low.
  * Out of date: the band is not known (None) unless the 19 hours before the forming one are all there, one after
    another, with no hour missing while the market was open (the weekend does not count).
Reads nothing and contacts nobody: it is given the finished 5-minute candles in order.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from prices.calendar import Boundaries, MarketHours
from prices.indicators import Band


@dataclass
class Hour:
    start: datetime
    end: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal


class HourlyChart:
    def __init__(self, settings: Any):
        self.s = settings
        self.hours_ = MarketHours(settings.market_hours)
        self.b = Boundaries(settings.candles, self.hours_)
        self.periods = int(settings.indicators.bollinger_periods)
        self.sds = int(settings.indicators.bollinger_std_devs)
        self.side = settings.chart.price
        self.hours: list[Hour] = []
        self._complete: dict = {}                   # forming hour's start -> the closes before it (or None)

    def copy(self) -> "HourlyChart":
        new = HourlyChart.__new__(HourlyChart)
        new.__dict__.update(self.__dict__)
        new.hours = [Hour(h.start, h.end, h.open, h.high, h.low, h.close) for h in self.hours]
        new._complete = dict(self._complete)
        return new

    def hour_of(self, t: datetime) -> tuple[datetime, datetime]:
        return self.b.bucket("1h", t)

    def add(self, c: Any) -> None:
        """A finished 5-minute candle (in time order)."""
        o, h, l, cl = (getattr(c, f"{self.side}_{k}") for k in ("open", "high", "low", "close"))
        start, end = self.hour_of(c.start)
        last = self.hours[-1] if self.hours else None
        if last is not None and last.start == start:
            last.high, last.low, last.close = max(last.high, h), min(last.low, l), cl
        elif last is None or start > last.start:
            self.hours.append(Hour(start, end, o, h, l, cl))
            del self.hours[:-(self.periods + 5)]

    def closes_before(self, hour_start: datetime) -> list[Decimal] | None:
        """The last periods-1 finished hourly closes before the hour starting at hour_start, or None if any hour
        is missing while the market was open (the band is then not known)."""
        if hour_start in self._complete:
            return self._complete[hour_start]
        before = [h for h in self.hours if h.end <= hour_start][-(self.periods - 1):]
        ok = len(before) == self.periods - 1
        if ok:
            ends = [h.end for h in before]
            starts = [h.start for h in before[1:]] + [hour_start]
            ok = all(e >= s or not any(True for _ in self.hours_.open_slots(e, s)) for e, s in zip(ends, starts))
        got = [h.close for h in before] if ok else None
        if len(self._complete) > 50:
            self._complete.clear()
        self._complete[hour_start] = got
        return got

    def band_at(self, t: datetime, price: Decimal) -> Band | None:
        """The hourly band at time t (inside the forming hour) with the price at that moment as its close."""
        start = self.hour_of(t)[0]
        prev = self.closes_before(start)
        if prev is None:
            return None
        window = prev + [Decimal(price)]
        n = Decimal(len(window))
        mid = sum(window) / n
        sd = (sum((x - mid) ** 2 for x in window) / n).sqrt()
        return Band(start, mid, mid + self.sds * sd, mid - self.sds * sd)
