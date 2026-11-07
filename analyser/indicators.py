"""The analyser's indicators (design section 2.8), worked out from the STORED
candles on each timeframe in settings [indicators] timeframes (5-minute and
hourly), using the chart price (settings [chart] price: the SELL (bid) price,
as on the owner's IG chart). Reads the candle store only; never contacts IG.

Only candles that had FINISHED at the time asked about are used, so the answer
for a past time never changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from prices.indicators import bollinger, ema, macd, needs_ema, needs_macd, needs_rsi, rsi
from prices.model import Candle
from prices.store import CandleStore

UTC = timezone.utc


@dataclass
class TimeframeIndicators:
    """Every indicator on one timeframe, at its latest finished candle."""
    timeframe: str
    as_of: datetime
    candle: Candle | None                       # the latest candle finished by as_of
    candles_used: int
    values: dict[str, Decimal | None]           # e.g. "ema_100", "bb_upper", "macd_histogram", "rsi"
    ready: dict[str, bool]                      # per indicator: "ema_100", "bollinger", "macd", "rsi"
    needs: dict[str, int]                       # candles each indicator needs to be ready
    series: dict[str, dict[datetime, Any]] = field(repr=False, default_factory=dict)  # full history, for later parts

    def warming_up(self) -> list[str]:
        return [name for name, ok in self.ready.items() if not ok]


def last_candles(store: CandleStore, tf: str, as_of: datetime, count: int) -> list[Candle]:
    """Up to `count` stored candles that had finished by `as_of`, oldest first."""
    out: list[Candle] = []
    for day in reversed(store.days(tf)):
        if day > as_of.date():
            continue
        got = sorted((c for c in store.read_day(tf, day) if c.end <= as_of), key=lambda c: c.start)
        out = got + out
        if len(out) >= count:
            break
    return out[-count:]


def work_out(settings: Any, store: CandleStore, tf: str, as_of: datetime) -> TimeframeIndicators:
    ind, side = settings.indicators, settings.chart.price
    pct = ind.warm_up_seed_weight_percent
    as_of = as_of.astimezone(UTC)
    candles = last_candles(store, tf, as_of, ind.history_candles)
    n = len(candles)
    latest = candles[-1] if candles else None
    values: dict[str, Decimal | None] = {}
    ready: dict[str, bool] = {}
    needs: dict[str, int] = {}
    series: dict[str, dict[datetime, Any]] = {}

    def at(s: dict[datetime, Any]) -> Any:
        return s.get(latest.start) if latest else None

    for p in ind.ema_periods:
        key = f"ema_{p}"
        series[key] = ema(candles, side, p)
        values[key] = at(series[key])
        needs[key] = needs_ema(p, pct)
        ready[key] = n >= needs[key]

    series["bollinger"] = bollinger(candles, side, ind.bollinger_periods, ind.bollinger_std_devs)
    band = at(series["bollinger"])
    values.update(bb_upper=band.upper if band else None, bb_middle=band.middle if band else None,
                  bb_lower=band.lower if band else None)
    needs["bollinger"] = ind.bollinger_periods
    ready["bollinger"] = n >= needs["bollinger"]

    series["macd"] = macd(candles, side, ind.macd_fast_periods, ind.macd_slow_periods, ind.macd_signal_periods)
    m = at(series["macd"])
    values.update(macd_line=m.line if m else None, macd_signal=m.signal if m else None,
                  macd_histogram=m.histogram if m else None)
    needs["macd"] = needs_macd(ind.macd_fast_periods, ind.macd_slow_periods, ind.macd_signal_periods, pct)
    ready["macd"] = n >= needs["macd"]

    series["rsi"] = rsi(candles, side, ind.rsi_periods)
    values["rsi"] = at(series["rsi"])
    needs["rsi"] = needs_rsi(ind.rsi_periods, pct)
    ready["rsi"] = n >= needs["rsi"]

    return TimeframeIndicators(tf, as_of, latest, n, values, ready, needs, series)
