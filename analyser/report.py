"""The analyser's answer at one moment (Stage 7, part 1: indicators, the
direction rule and whether the data is ready). The market state is added in a
later part. Reads the candle store only; never contacts IG.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from config.pairs import check_same_pair
from analyser.data_status import DataStatus, judge
from analyser.direction import Direction, decide
from analyser.indicators import TimeframeIndicators, work_out
from levels.current import build
from levels.rules import PIVOT
from prices.model import uk_short
from prices.store import CandleStore

UTC = timezone.utc


@dataclass
class AnalyserReport:
    as_of: datetime
    indicators: dict[str, TimeframeIndicators]
    direction: Direction
    data: DataStatus

    @property
    def new_trades_allowed_by_data(self) -> bool:
        return self.data.state == "ready"


def analyse(settings: Any, store: CandleStore, as_of: datetime, price: Decimal | None = None) -> AnalyserReport:
    """Everything as it stood at `as_of`, from candles finished by then.
    `price`: the live sell price, if there is one (otherwise the latest close)."""
    check_same_pair(settings, store)
    as_of = as_of.astimezone(UTC)
    frames = {tf: work_out(settings, store, tf, as_of) for tf in settings.indicators.timeframes}
    an = settings.analyser
    f = frames[an.direction_ema_timeframe]
    key = f"ema_{an.direction_ema_periods}"
    if price is None and f.candle is not None:
        price = getattr(f.candle, f"{settings.chart.price}_close")
        price_from = f"close of the {f.timeframe} candle {uk_short(f.candle.start)} ({settings.chart.price})"
    else:
        price_from = f"live {settings.chart.price} price" if price is not None else "none"
    pivots = [lv.price for lv in build(settings, store, as_of).levels if lv.type == PIVOT]
    pivot = pivots[0] if pivots else None
    direction = decide(price, price_from, pivot, f.values[key],
                       f"{f.timeframe} {an.direction_ema_periods} EMA", f.ready[key])
    return AnalyserReport(as_of, frames, direction, judge(settings, frames.values(), as_of))
