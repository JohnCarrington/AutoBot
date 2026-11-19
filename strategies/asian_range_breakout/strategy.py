"""Asian range breakout (design 3.7; owner, 16 November 2026). UK times, sell prices as on the chart.

  1. The Asian range: the high and low of the 5-minute candles from asian_range_breakout.range_from (00:00) up to
     asian_range_breakout.range_until (07:00).
  2. From asian_range_breakout.breakout_from (07:00) up to asian_range_breakout.breakout_until (10:00), a 5-minute
     candle closes above the Asian high (a buy) or below the Asian low (a sell).
  3. The trade opens at the next candle's open (live: its first price; never sent late).
  4. One trade each way per day: every such close gives an idea, and the safety rules refuse it once a trade that
     way has opened that day (the idea's context "once_a_day"; a close whose idea was refused, for example in a
     big-news window, does not use up the day: the owner's answer 4).
While the switch PULLBACK_ENTRY is on (owner, approved 19 November 2026; strategies/pullback.py) rule 3 is replaced:
only the FIRST close beyond the range each way each day starts a wait for a pullback to the 5-minute 8 EMA and a
close back beyond it, within pullback_entry.wait_candles (6) candles, cancelled by a close beyond the 21 EMA against
it; the trade then opens at the next candle's open. After a wait expires or is cancelled there is no new wait that
day in that direction (the owner's answer 6). The stop and the trail are unchanged.
Nothing else in the strategies decides whether it opens (strategies/common.py: like the bounce). Ideas only.
"""

from __future__ import annotations

import copy
from decimal import Decimal
from typing import Any

from prices.model import Candle, plain, uk_short
from strategies.common import ASIAN_RANGE_BREAKOUT, BUY, SELL, Candidate
from strategies.pullback import CANCELLED, CONFIRMED, EXPIRED, Wait, advance, pullback_on, started
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
        self.pullback = pullback_on(settings)                  # PULLBACK_ENTRY (owner, 19 November 2026)
        self.wait_limit = settings.pullback_entry.wait_candles if self.pullback else 0
        self.waits: list[Wait] = []                            # breaks waiting for their pullback
        self.waited: set = set()                               # (day, direction): a wait already started that day

    def fork(self) -> "AsianRangeBreakout":
        new = AsianRangeBreakout.__new__(AsianRangeBreakout)
        new.__dict__.update(self.__dict__)
        new.due = [(d, list(st)) for d, st in self.due]
        new.notes = []
        new.waits = copy.deepcopy(self.waits)
        new.waited = set(self.waited)
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

    def on_candle(self, c: Candle, fast: Decimal | None = None, slow: Decimal | None = None) -> list[Candidate]:
        """One 5-minute candle (finished; live, the one forming so far): the trades that open at its open. `fast`,
        `slow`: the 5-minute 8 and 21 EMAs after this candle (the pullback entry only)."""
        out: list[Candidate] = []
        for direction, steps in self.due:
            steps = steps + [f"{uk_short(c.start)} opens at this candle's open, {plain(c.sell_open)} (sell price)"]
            out.append(Candidate(ASIAN_RANGE_BREAKOUT, direction, c.start, c.sell_open, steps,
                                 {"once_a_day": f"{ASIAN_RANGE_BREAKOUT} {direction} {self.day}"}))
        self.due = []
        self._day(c)
        for w in list(self.waits):                             # PULLBACK_ENTRY: the candles after the break candle
            result, what = advance(w, c, fast, slow, self.wait_limit, "sell")
            if result == CONFIRMED:
                self.waits.remove(w)
                self.due.append((w.direction, w.steps))
            elif result in (CANCELLED, EXPIRED):
                self.waits.remove(w)
                self.notes.append((c.start, w.direction, what))
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
                    if not self.pullback:
                        self.due.append((direction, [what]))
                    elif (self.day, direction) not in self.waited:      # only the first close beyond, each way
                        self.waited.add((self.day, direction))
                        w = Wait(direction, c, [what])
                        started(w, self.wait_limit, f"the first close beyond the range, {uk_short(c.start)}")
                        self.waits.append(w)
        return out
