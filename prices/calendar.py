"""When the market is open, and where candle boundaries go.

Market hours (settings [market_hours], UK time): the market opens once a week
(Sunday 21:00) and closes once a week (Friday 22:00), with no break in between.
The time between the close and the next open is the weekend: no candles are
expected then, so it is never a gap.

Candle boundaries (settings [candles], UK time):
  5m  every 5 minutes (IG's own candles)
  1h  on the hour (hour_starts_at_minute)
  4h  every 4 hours from four_hour_starts_at (22:00, 02:00, 06:00, ...)
  1d  from day_starts_at to day_starts_at the next day (22:00 to 22:00)
  1w  from week_starts_day at day_starts_at (Sunday 22:00) for 7 days

Two rules join these to the market hours, so that no candle is cut into a
small piece by the weekend:
  * The stretch from the weekly open to the first normal boundary after it is
    joined onto the candle that follows. (With the market opening at Sunday
    21:00, Monday's daily candle runs from Sunday 21:00 to Monday 22:00, and
    the first 4-hour candle of the week runs from Sunday 21:00 to 02:00.)
  * No candle runs past the weekly close. (The weekly candle ends at Friday 22:00.)
"""

from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Any, Iterator

from prices.model import FIVE_MIN, UK, UTC


def _local(day: datetime, at: time) -> datetime:
    """UK wall-clock time `at` on the UK date of `day`, as a UTC time."""
    d = day.astimezone(UK).date()
    return datetime(d.year, d.month, d.day, at.hour, at.minute, tzinfo=UK).astimezone(UTC)


def _days_back_to(t: datetime, weekday: int) -> int:
    return (t.astimezone(UK).weekday() - weekday) % 7


class MarketHours:
    def __init__(self, s: Any):
        self.opens_day, self.opens_at = int(s.opens_day), s.opens_at
        self.closes_day, self.closes_at = int(s.closes_day), s.closes_at

    def _open_on_or_before(self, t: datetime) -> datetime:
        back = _days_back_to(t, self.opens_day)
        o = _local(t.astimezone(UK) - timedelta(days=back), self.opens_at)
        if o > t:
            o = _local(t.astimezone(UK) - timedelta(days=back + 7), self.opens_at)
        return o

    def _close_after(self, opened: datetime) -> datetime:
        ahead = (self.closes_day - self.opens_day) % 7
        return _local(opened.astimezone(UK) + timedelta(days=ahead), self.closes_at)

    def session(self, t: datetime) -> tuple[datetime, datetime]:
        """The trading week that `t` falls in or most recently ended: (open, close)."""
        o = self._open_on_or_before(t)
        return o, self._close_after(o)

    def is_open(self, t: datetime) -> bool:
        o, c = self.session(t)
        return o <= t < c

    def next_open(self, t: datetime) -> datetime:
        """The first time at or after `t` when the market is open."""
        if self.is_open(t):
            return t
        o = self._open_on_or_before(t)
        nxt = _local(o.astimezone(UK) + timedelta(days=7), self.opens_at)
        return nxt

    def open_slots(self, start: datetime, end: datetime) -> Iterator[datetime]:
        """Every 5-minute candle start in [start, end) while the market is open."""
        t = floor_5m(start)
        if t < start:
            t += FIVE_MIN
        while t < end:
            if self.is_open(t):
                t_next = t + FIVE_MIN
                yield t
                t = t_next
            else:
                t = max(t + FIVE_MIN, floor_5m(self.next_open(t)))


def floor_5m(t: datetime) -> datetime:
    t = t.astimezone(UTC)
    return t.replace(minute=t.minute - t.minute % 5, second=0, microsecond=0)


class Boundaries:
    """Where each candle size starts and ends."""

    def __init__(self, candle_settings: Any, hours: MarketHours):
        self.c = candle_settings
        self.hours = hours

    # ---- the normal boundaries, before the market-hours rules -------------

    def regular(self, tf: str, t: datetime) -> tuple[datetime, datetime]:
        t = t.astimezone(UTC)
        if tf == "5m":
            s = floor_5m(t)
            return s, s + FIVE_MIN
        if tf == "1h":
            m = self.c.hour_starts_at_minute
            s = t.replace(minute=m, second=0, microsecond=0)
            if s > t:
                s -= timedelta(hours=1)
            return s, s + timedelta(hours=1)
        if tf == "4h":
            anchor = self.c.four_hour_starts_at
            local = t.astimezone(UK)
            minutes = local.hour * 60 + local.minute - (anchor.hour * 60 + anchor.minute)
            back = minutes % 240
            s_local = local.replace(second=0, microsecond=0) - timedelta(minutes=back)
            s = datetime(s_local.year, s_local.month, s_local.day, s_local.hour, s_local.minute,
                         tzinfo=UK).astimezone(UTC)
            e_local = s.astimezone(UK) + timedelta(hours=4)
            e = datetime(e_local.year, e_local.month, e_local.day, e_local.hour, e_local.minute,
                         tzinfo=UK).astimezone(UTC)
            return s, e
        if tf == "1d":
            s = _local(t, self.c.day_starts_at)
            if s > t:
                s = _local(t.astimezone(UK) - timedelta(days=1), self.c.day_starts_at)
            return s, _local(s.astimezone(UK) + timedelta(days=1), self.c.day_starts_at)
        if tf == "1w":
            wd = int(self.c.week_starts_day)
            back = _days_back_to(t, wd)
            s = _local(t.astimezone(UK) - timedelta(days=back), self.c.day_starts_at)
            if s > t:
                s = _local(t.astimezone(UK) - timedelta(days=back + 7), self.c.day_starts_at)
            return s, _local(s.astimezone(UK) + timedelta(days=7), self.c.day_starts_at)
        raise ValueError(f"unknown candle size {tf!r}")

    # ---- with the market-hours rules ------------------------------------

    def bucket(self, tf: str, t: datetime) -> tuple[datetime, datetime]:
        """The (start, end) of the candle of size `tf` that time `t` falls in."""
        s, e = self.regular(tf, t)
        if tf == "5m" or not self.hours.is_open(t):
            return s, e
        o, c = self.hours.session(t)
        if s < o:
            # t is in the stretch between the weekly open and the first normal
            # boundary: it is joined onto the next candle.
            start, end = o, self.regular(tf, e)[1]
        else:
            ps = self.regular(tf, s - timedelta(seconds=1))[0]
            start, end = (o, e) if ps < o < s else (s, e)
        return start, min(end, c)

    def expected_parts(self, start: datetime, end: datetime) -> int:
        return sum(1 for _ in self.hours.open_slots(start, end))

    def is_on_boundary(self, tf: str, start: datetime) -> bool:
        return self.bucket(tf, start)[0] == start

    def next_start(self, tf: str, end: datetime) -> datetime:
        """Where the next candle should start after one that ends at `end`."""
        t = self.hours.next_open(end)
        return self.bucket(tf, t)[0]
