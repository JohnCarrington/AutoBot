"""The hourly read: the analyser first looks at the hourly chart to see the context, ranging, a sell-off or a
rally (owner, 14 November 2026). Worked out on the hourly candles, sell price (the chart price), each time an
hourly candle closes:

  * a SELL-OFF starts when an hourly candle closes at least hourly_read.break_beyond_pips (3) below the lowest
    low of the hourly_read.range_candles (12) hourly candles before it;
  * a RALLY starts when an hourly candle closes at least 3 pips above the highest high of the 12 before it;
  * a break the other way turns a sell-off straight into a rally, or a rally into a sell-off; a new break the
    same way starts the count below again;
  * it is RANGING once hourly_read.ranging_after_candles (12) more hourly candles have closed with no new break.
    The hourly range is the high and low of the last 12 hourly candles, updated every hour.

The read holds from the close of the hourly candle it was decided on until the next one closes. The hourly
candles are taken in order as stored, so the weekend does not count towards the 12. Before the first break in
the candles read, the read is ranging (there has been no hourly close beyond the range).

What the strategies do with it is in strategies/common.py. Reads candles only; never contacts IG.
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Sequence

from prices.model import Candle, plain, uk_short

RANGING, SELL_OFF, RALLY = "ranging", "sell-off", "rally"


@dataclass(frozen=True)
class HourlyRead:
    state: str                          # ranging, sell-off or rally
    candle: Candle | None               # the last finished hourly candle it was decided on
    low: Decimal | None                 # the hourly range: the lowest low ...
    high: Decimal | None                # ... and the highest high of the last range_candles hourly candles
    since: datetime | None              # start of the hourly candle whose close began this read
    why: str

    def line(self) -> str:
        rng = (f"; the hourly range {plain(self.low)} to {plain(self.high)}"
               if self.low is not None else "")
        return f"hourly {self.state}: {self.why}{rng}"


class HourlyReader:
    """The hourly read after every hourly candle given, worked out once; at(t) gives the read as of the last hourly
    candle finished by t."""

    def __init__(self, settings: Any, hourly: Sequence[Candle]):
        h = settings.hourly_read
        side = settings.chart.price
        ppp = Decimal(settings.market.points_per_pip)
        n, beyond, after = h.range_candles, Decimal(h.break_beyond_pips) * ppp, h.ranging_after_candles
        self.candles = sorted(hourly, key=lambda c: c.start)
        self.ends = [c.end for c in self.candles]
        hi = lambda c: getattr(c, f"{side}_high")    # noqa: E731
        lo = lambda c: getattr(c, f"{side}_low")     # noqa: E731
        state, since_i, why = RANGING, None, "no hourly close beyond the range in the hourly candles read"
        self.reads: list[HourlyRead] = []
        for i, c in enumerate(self.candles):
            close = getattr(c, f"{side}_close")
            if i >= n:
                before = self.candles[i - n:i]
                top, bottom = max(hi(x) for x in before), min(lo(x) for x in before)
                pips = lambda a, b: plain(((a - b) / ppp).quantize(Decimal("0.1")))   # noqa: E731
                if close <= bottom - beyond:
                    state, since_i = SELL_OFF, i
                    why = (f"the {uk_short(c.start)} hourly candle closed at {plain(close)}, {pips(bottom, close)} pips "
                           f"below the low {plain(bottom)} of the {n} hourly candles before it")
                elif close >= top + beyond:
                    state, since_i = RALLY, i
                    why = (f"the {uk_short(c.start)} hourly candle closed at {plain(close)}, {pips(close, top)} pips "
                           f"above the high {plain(top)} of the {n} hourly candles before it")
                elif state != RANGING and i - since_i >= after:
                    state = RANGING
                    why = (f"{after} hourly candles have closed with no new break since the "
                           f"{uk_short(self.candles[since_i].start)} candle")
            window = self.candles[max(0, i - n + 1):i + 1]
            self.reads.append(HourlyRead(state, c, min(lo(x) for x in window), max(hi(x) for x in window),
                                         self.candles[since_i].start if since_i is not None else None, why))

    def at(self, t: datetime) -> HourlyRead:
        k = bisect_right(self.ends, t)
        if k == 0:
            return HourlyRead(RANGING, None, None, None, None, "no hourly candle finished yet")
        return self.reads[k - 1]
