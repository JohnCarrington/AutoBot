"""Each UK weekday's direction on an exception day (design 6, "One view at a time"; owner, 9 November 2026).
Chart (sell) prices, stored candles and the calendar only; never contacts IG.

A UK day may have up to three directions (buy or sell), exactly as in docs/research/one_view_20261109.md:
  * news: on a big-news day, the day's expected news direction (trade_manager.manager.day_news_direction, as the
    trade manager uses it for the 100-pip take profit and the close on a rejection);
  * trend day: on a trend day (analyser/trend_day.py), its direction (down: sell, up: buy);
  * Monday: on a Monday after a Friday whose daily candle (sell price, open to close, UK day) moved
    safety.big_friday_move_pips (80) or more, the direction that reclaims Friday's move (Friday fell: buy;
    Friday rose: sell).
The safety rules refuse a reversal trade against any of them (safety/rules.py).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from analyser.trend_day import day_start, trend_day_at
from prices.model import UK

BUY, SELL = "buy", "sell"


@dataclass(frozen=True)
class DayDirections:
    """A UK day's directions, each buy, sell or None."""
    day: date | None = None
    news: str | None = None
    trend_day: str | None = None
    monday: str | None = None
    friday_move_pips: Decimal | None = None             # Monday only: the Friday's move, for the records

    def against(self, direction: str) -> list[str]:
        """Each of the day's directions that `direction` goes against, described."""
        out = []
        if self.news and self.news != direction:
            out.append(f"a big-news day, expected news direction {self.news}")
        if self.trend_day and self.trend_day != direction:
            out.append(f"a trend day, direction {self.trend_day}")
        if self.monday and self.monday != direction:
            out.append(f"the Monday after a Friday that moved {self.friday_move_pips:+} pips, direction {self.monday}")
        return out


def friday_move_pips(settings: Any, store: Any, monday: date) -> Decimal | None:
    """The move of the Friday before `monday`, in pips: its stored daily candle, sell price (chart.price), close
    less open. None when that candle is not stored."""
    friday = monday - timedelta(days=3)
    t0 = day_start(friday)
    got = [c for c in store.read_range("1d", t0, t0 + timedelta(minutes=5)) if c.start == t0]
    if not got:
        return None
    side = settings.chart.price
    c = got[0]
    return (Decimal(getattr(c, f"{side}_close")) - Decimal(getattr(c, f"{side}_open"))) / Decimal(settings.market.points_per_pip)


def day_directions(settings: Any, store: Any, t: datetime, calendar: list | None = None,
                   trend_day: str | None | bool = False) -> DayDirections:
    """The directions of t's UK day. `trend_day`: the trend-day check's answer ("up", "down" or None) when the
    caller already has it; otherwise it is worked out here. A part that cannot be worked out gives no direction."""
    from trade_manager.manager import day_news_direction
    day = t.astimezone(UK).date()
    try:
        news = day_news_direction(settings, settings.market.pair, t, calendar)
    except Exception:                                   # noqa: BLE001  (no news direction if it cannot be worked out)
        news = None
    if trend_day is False:
        try:
            trend_day = trend_day_at(settings, store, t).direction
        except Exception:                               # noqa: BLE001
            trend_day = None
    td = {"down": SELL, "up": BUY}.get(trend_day)
    monday = move = None
    if day.weekday() == 0:
        try:
            move = friday_move_pips(settings, store, day)
        except Exception:                               # noqa: BLE001
            move = None
        if move is not None and abs(move) >= Decimal(settings.safety.big_friday_move_pips):
            monday = BUY if move < 0 else SELL
    return DayDirections(day, news, td, monday, move)
