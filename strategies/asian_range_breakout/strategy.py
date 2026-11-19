"""Asian range breakout (design 3.7; owner, 16 November 2026). UK times, sell prices as on the chart.

  1. The Asian range: the high and low of the 5-minute candles from asian_range_breakout.range_from (00:00) up to
     asian_range_breakout.range_until (07:00).
  2. From asian_range_breakout.breakout_from (07:00) up to asian_range_breakout.breakout_until (10:00), a 5-minute
     candle closes above the Asian high (a buy) or below the Asian low (a sell).
  3. The trade opens at the next candle's open (live: its first price; never sent late).
  4. One trade each way per day: every such close gives an idea, and the safety rules refuse it once a trade that
     way has opened that day (the idea's context "once_a_day"; a close whose idea was refused, for example in a
     big-news window, does not use up the day: the owner's answer 4).
Nothing else in the strategies decides whether it opens (strategies/common.py: like the bounce). Ideas only.
"""

from __future__ import annotations

from typing import Any

from prices.model import Candle, plain, uk_short
from strategies.common import ASIAN_RANGE_BREAKOUT, BUY, SELL, Candidate
from strategies.sessions import uk_day_and_time, uk_zone


class AsianRangeBreakout:
    def __init__(self, settings: Any):
        self.s = settings
        self.a = settings.asian_range_breakout
        self.uk = uk_zone(settings)
        self.day = None
        self.high = self.low = None          # the Asian range so far (today)
        self.due: list[tuple[str, list]] = []  # (direction, steps): they open at the next candle's open
        self.notes: list[tuple] = []         # (time, direction, text)

    def fork(self) -> "AsianRangeBreakout":
        new = AsianRangeBreakout.__new__(AsianRangeBreakout)
        new.__dict__.update(self.__dict__)
        new.due = [(d, list(st)) for d, st in self.due]
        new.notes = []
        return new

    def warm(self, candles: list) -> None:
        """The finished 5-minute candles before the replay starts: the Asian range only."""
        for c in candles:
            self._day(c)
            if self.a.range_from <= c.start.astimezone(self.uk).time() < self.a.range_until:
                self._take(c)

    def _day(self, c: Candle) -> None:
        d, _ = uk_day_and_time(c, self.uk)
        if d != self.day:
            self.day, self.high, self.low = d, None, None

    def _take(self, c: Candle) -> None:
        self.high = c.sell_high if self.high is None else max(self.high, c.sell_high)
        self.low = c.sell_low if self.low is None else min(self.low, c.sell_low)

    def on_candle(self, c: Candle) -> list[Candidate]:
        """One 5-minute candle (finished; live, the one forming so far): the trades that open at its open."""
        out: list[Candidate] = []
        for direction, steps in self.due:
            steps = steps + [f"{uk_short(c.start)} opens at this candle's open, {plain(c.sell_open)} (sell price)"]
            out.append(Candidate(ASIAN_RANGE_BREAKOUT, direction, c.start, c.sell_open, steps,
                                 {"once_a_day": f"{ASIAN_RANGE_BREAKOUT} {direction} {self.day}"}))
        self.due = []
        self._day(c)
        t = c.start.astimezone(self.uk).time()
        if self.a.range_from <= t < self.a.range_until:
            self._take(c)
        elif self.a.breakout_from <= t < self.a.breakout_until and self.high is not None:
            rng = (f"the Asian range {self.a.range_from:%H:%M} to {self.a.range_until:%H:%M}, "
                   f"high {plain(self.high)}, low {plain(self.low)}")
            for direction, beyond in ((BUY, c.sell_close > self.high), (SELL, c.sell_close < self.low)):
                if beyond:
                    what = (f"{uk_short(c.start)} closed at {plain(c.sell_close)}, "
                            f"{'above the Asian high' if direction == BUY else 'below the Asian low'} ({rng})")
                    self.notes.append((c.start, direction, what))
                    self.due.append((direction, [what]))
        return out
