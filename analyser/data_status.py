"""Whether the analyser's data is ready, warming up or out of date (design
section 2.1). If it is not ready, new trades are blocked (open trades are still
managed: that is for later parts).

  OUT OF DATE   the market is open (or has just closed) and the newest stored
                candle on an indicator timeframe is more than
                analyser.out_of_date_after_minutes behind the newest one that
                should have finished. Checked first: old data is never "ready".
  WARMING UP    some indicator has not had enough candles yet (see
                indicators.warm_up_seed_weight_percent).
  READY         neither.
While the market is shut, the data is judged against the last candle before
the close, so a weekend is not "out of date".
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Iterable

from analyser.indicators import TimeframeIndicators
from prices.calendar import Boundaries, MarketHours, floor_5m
from prices.model import uk_short

READY, WARMING_UP, OUT_OF_DATE = "ready", "warming up", "out of date"
FIVE = timedelta(minutes=5)


@dataclass
class DataStatus:
    state: str
    reasons: list[str]

    def describe(self) -> str:
        return self.state + (": " + "; ".join(self.reasons) if self.reasons else "")


def last_open_slot_before(hours: MarketHours, t: datetime) -> datetime | None:
    """The start of the newest 5-minute candle that had finished by `t` while the market was open."""
    s = floor_5m(t) - FIVE
    if hours.is_open(s):
        return s
    o, c = hours.session(t)
    if c > t:                                   # this week's market opened less than 5 minutes ago
        o, c = hours.session(o - FIVE)
    return c - FIVE


def should_have_finished(b: Boundaries, hours: MarketHours, tf: str, t: datetime) -> datetime | None:
    """The end of the newest candle on `tf` that should have finished by `t`."""
    slot = last_open_slot_before(hours, t)
    for _ in range(2000):
        if slot is None:
            return None
        s, e = b.bucket(tf, slot)
        if e <= t:
            return e
        slot = last_open_slot_before(hours, s)
    return None


def judge(settings: Any, frames: Iterable[TimeframeIndicators], as_of: datetime) -> DataStatus:
    hours = MarketHours(settings.market_hours)
    b = Boundaries(settings.candles, hours)
    allowed = timedelta(minutes=settings.analyser.out_of_date_after_minutes)
    old, warming = [], []
    for f in frames:
        due = should_have_finished(b, hours, f.timeframe, as_of)
        have = f.candle.end if f.candle else None
        if due is not None and (have is None or due - have > allowed):
            old.append(f"{f.timeframe}: newest candle ends {uk_short(have) if have else 'none stored'}, "
                       f"one ending {uk_short(due)} should be stored")
        for name in f.warming_up():
            warming.append(f"{f.timeframe} {name} has {f.candles_used} of the {f.needs[name]} candles it needs")
    if old:
        return DataStatus(OUT_OF_DATE, old)
    if warming:
        return DataStatus(WARMING_UP, warming)
    return DataStatus(READY, [])
