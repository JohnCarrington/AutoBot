"""What the three session strategies share (owner, 16 November 2026): the UK clock time of a candle, and the
confirmation step written exactly as the Bollinger bounce's (design 3.3 steps 3 and 5; the owner's answers 8 and
13 of 16 November 2026):
  * the confirmation candle: a later 5-minute candle closes beyond the rejection candle's low (a sell) or high (a
    buy) within `within` candles of it, or the setup expires. A wick does not count;
  * price going beyond the rejection candle's high (a sell) or low (a buy) before the confirmation cancels the
    setup; a candle that goes beyond it and also closes past the other side counts as the cancel (the order inside
    a candle is unknown).
Sell prices throughout, as on the chart. Ideas only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from typing import Any
from zoneinfo import ZoneInfo

from prices.model import Candle, plain, uk_short
from strategies.common import SELL


def uk_zone(settings: Any) -> ZoneInfo:
    tz = settings.hours.timezone
    return ZoneInfo(tz) if isinstance(tz, str) else tz


def uk_day_and_time(c: Candle, uk: ZoneInfo) -> tuple[date, time]:
    """The UK calendar day and clock time of a candle's start."""
    lt = c.start.astimezone(uk)
    return lt.date(), lt.time()


@dataclass
class Setup:
    """A rejection candle waiting for its confirmation."""
    direction: str
    rejection: Candle
    candles: int = 0                    # candles since the rejection candle
    steps: list = field(default_factory=list)
    context: dict = field(default_factory=dict)

    def copy(self) -> "Setup":
        return Setup(self.direction, self.rejection, self.candles, list(self.steps), dict(self.context))


def confirm_step(st: Setup, c: Candle, within: int) -> tuple[str, str]:
    """One later candle for a waiting setup: ("cancelled" | "confirmed" | "expired" | "waiting", what happened)."""
    st.candles += 1
    sell = st.direction == SELL
    r = st.rejection
    if (c.sell_high > r.sell_high) if sell else (c.sell_low < r.sell_low):
        return "cancelled", (f"{uk_short(c.start)} cancelled, price went {'above' if sell else 'below'} the rejection "
                             f"candle's {'high' if sell else 'low'} ({plain(r.sell_high if sell else r.sell_low)})")
    if (c.sell_close < r.sell_low) if sell else (c.sell_close > r.sell_high):
        return "confirmed", (f"{uk_short(c.start)} confirmation candle, closed at {plain(c.sell_close)}, "
                             f"{'below' if sell else 'above'} the rejection candle's {'low' if sell else 'high'} "
                             f"({plain(r.sell_low if sell else r.sell_high)})")
    if st.candles >= within:
        return "expired", f"{uk_short(c.start)} expired, no confirmation within {within} candles of the rejection candle"
    return "waiting", ""
