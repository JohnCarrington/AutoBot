"""Runs the rejection watcher over stored candles: for checking past days
against the chart, and for the functional tests. Reads the candle store only;
never contacts IG.

With stored candles there are no ticks, so a trigger or cancel is found from
the candles that follow (their high and low), and is shown at the start of the
candle it happened in. Live, the watcher gets each price and finds the exact
moment (RejectionWatcher.on_price).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from config.pairs import check_same_pair
from levels.current import build
from prices.indicators import bollinger
from prices.store import CandleStore
from rejection.watch import RejectionWatcher

WARM_UP_DAYS = 3     # candles read before `start`, so the Bollinger band is ready (a calendar limit, not a rule)


def replay(settings: Any, store: CandleStore, start: datetime, end: datetime,
           with_levels: bool = True) -> RejectionWatcher:
    check_same_pair(settings, store)
    tf = settings.rejection.candle_timeframe
    ind = settings.indicators
    candles = store.read_range(tf, start - timedelta(days=WARM_UP_DAYS), end)
    bands = bollinger(candles, settings.chart.price, ind.bollinger_periods, ind.bollinger_std_devs)
    w = RejectionWatcher(settings)
    for c in candles:
        if c.start < start:
            continue
        levels = build(settings, store, c.start) if with_levels else None
        w.on_candle(c, bands.get(c.start), levels)
    return w
