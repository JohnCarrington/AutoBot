"""The trend-day check (design section 2.4; owner, 8 November 2026). Chart (sell) prices, stored
candles only; never contacts IG.

At each UK day's 00:00 open:
  * a trend day DOWNWARDS when the open is at or above the previous month's trend_day.level_above
    (R2) and the daily RSI (trend_day.rsi_periods, 14) at the previous day's close is above
    trend_day.rsi_above (70);
  * a trend day UPWARDS when the open is at or below the previous month's trend_day.level_below (S2)
    and that RSI is below trend_day.rsi_below (30);
  * otherwise not a trend day.
Exactly rank 1 of docs/research/trend_day_conditions_v2_20261108.md:
  * the monthly levels are the classic pivots (levels/rules.py) of the previous UK calendar month,
    built from the stored daily candles of that month (its highest high, lowest low and last close;
    IG's short Sunday candles included), only when the store has daily candles from before that month
    began (so the month is complete);
  * the RSI is Wilder's (prices/indicators.py) on the stored daily candles finished by the day's start
    (up to trend_day.rsi_history_candles of them; Sunday candles included, as on the chart), its value
    at the last of them (Monday: IG's short Sunday candle);
  * the open is the day's daily candle's open, or the 00:00 UK 5-minute candle's open.
A day with no 00:00 open (Saturday, and Sunday, when the market opens at 21:00 UK) is never a trend day.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any

from analyser.indicators import last_candles
from levels.rules import daily_pivots
from prices.indicators import rsi
from prices.model import UK, plain
from prices.store import CandleStore

UTC = timezone.utc
UP, DOWN = "up", "down"


@dataclass(frozen=True)
class TrendDay:
    day: date
    direction: str | None               # "down", "up" or None (not a trend day)
    reason: str
    open_price: Decimal | None = None
    level: Decimal | None = None        # the monthly level that counted (R2 or S2)
    rsi: Decimal | None = None


class _Month:
    def __init__(self, high, low, close):
        self.start, self.sell_high, self.sell_low, self.sell_close = None, high, low, close
        self.buy_high, self.buy_low, self.buy_close = high, low, close


def day_start(day: date) -> datetime:
    return datetime.combine(day, time(0, 0), tzinfo=UK).astimezone(UTC)


def monthly_levels(settings: Any, store: CandleStore, day: date) -> dict[str, Decimal] | None:
    """The previous UK calendar month's pivots, from the stored daily candles, or None when the store
    does not hold that whole month."""
    side = settings.chart.price
    first = date(day.year, day.month, 1)
    prev_first = date(first.year - 1, 12, 1) if first.month == 1 else date(first.year, first.month - 1, 1)
    start, end = day_start(prev_first), day_start(first)
    month = [c for c in store.read_range("1d", start - timedelta(days=1), end) if start <= c.start < end]
    if not month:
        return None
    before = store.read_range("1d", start - timedelta(days=40), start)
    if not [c for c in before if c.start < start]:
        return None                                         # the month's start is not in the store
    month.sort(key=lambda c: c.start)
    m = _Month(max(getattr(c, f"{side}_high") for c in month), min(getattr(c, f"{side}_low") for c in month),
               getattr(month[-1], f"{side}_close"))
    return {lv.type: lv.price for lv in daily_pivots(m, side, settings.levels.level_decimals, "previous month")}


def day_open(settings: Any, store: CandleStore, day: date) -> Decimal | None:
    side, t0 = settings.chart.price, day_start(day)
    for tf in ("1d", "5m"):
        got = [c for c in store.read_range(tf, t0, t0 + timedelta(minutes=5)) if c.start == t0]
        if got:
            return getattr(got[0], f"{side}_open")
    return None


def check(settings: Any, store: CandleStore, day: date) -> TrendDay:
    """Whether `day` (a UK date) is a trend day, and which way."""
    td = settings.trend_day
    if day.weekday() >= 5:
        return TrendDay(day, None, "no 00:00 UK open on a Saturday or Sunday")
    o = day_open(settings, store, day)
    if o is None:
        return TrendDay(day, None, "no 00:00 UK open stored")
    lv = monthly_levels(settings, store, day)
    if lv is None:
        return TrendDay(day, None, "the previous month is not complete in the store", o)
    daily = last_candles(store, "1d", day_start(day), td.rsi_history_candles)
    values = rsi(daily, settings.chart.price, td.rsi_periods)
    if not daily or daily[-1].start not in values:
        return TrendDay(day, None, f"not enough daily candles for the RSI({td.rsi_periods})", o)
    r = values[daily[-1].start]
    above, below = lv[td.level_above], lv[td.level_below]
    rs = f"daily RSI({td.rsi_periods}) {plain(r.quantize(Decimal('0.1')))}"
    if o >= above and r > td.rsi_above:
        return TrendDay(day, DOWN, f"trend day downwards: open {plain(o)} at or above the monthly {td.level_above} "
                                   f"{plain(above)}; {rs} above {td.rsi_above}", o, above, r)
    if o <= below and r < td.rsi_below:
        return TrendDay(day, UP, f"trend day upwards: open {plain(o)} at or below the monthly {td.level_below} "
                                 f"{plain(below)}; {rs} below {td.rsi_below}", o, below, r)
    return TrendDay(day, None, f"not a trend day: open {plain(o)}, monthly {td.level_above} {plain(above)} and "
                               f"{td.level_below} {plain(below)}; {rs}", o, None, r)


def trend_day_at(settings: Any, store: CandleStore, t: datetime) -> TrendDay:
    """The trend-day check for the UK day of time t."""
    return check(settings, store, t.astimezone(UK).date())
