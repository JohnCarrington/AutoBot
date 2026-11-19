"""New York open reversal (design 3.9; owner, 16 November 2026). UK times, sell prices as on the chart. Written
for a sell after a rise; a buy after a fall is the mirror image.

  1. The move: from the open of the first 5-minute candle at or after new_york_open_reversal.move_from (07:00) to
     the close of the last candle before new_york_open_reversal.move_until (13:30), at least
     new_york_open_reversal.min_move_pips (30) up.
  2. From new_york_open_reversal.window_from (13:30) up to new_york_open_reversal.window_until (15:00): a rejection
     candle against the move, red after a rise, whatever its size (the owner's answer 12).
  3. The confirmation candle closes below the rejection candle's low within
     new_york_open_reversal.confirmation_within_candles (3) candles of it; price going above the rejection candle's
     high first cancels it (strategies/sessions.py, as the bounce). Both candles are in the window.
  4. The trade opens at the next candle's open (live: its first price; never sent late).
Every rejection candle starts its own setup. One trade a day: the safety rules refuse it once one has opened that
day (the idea's context "once_a_day"). No trade on a day with big news for the pair released at
new_york_open_reversal.no_trade_if_big_news_at (13:30): strategies.common.may_open. Nothing else in the strategies
decides whether it opens (like the bounce). Ideas only.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from prices.model import Candle, plain, uk_short
from strategies.common import BUY, NEW_YORK_OPEN_REVERSAL, SELL, Candidate, signal_context
from strategies.sessions import Setup, confirm_step, uk_day_and_time, uk_zone


class NewYorkOpenReversal:
    def __init__(self, settings: Any):
        self.s = settings
        self.n = settings.new_york_open_reversal
        self.uk = uk_zone(settings)
        self.ppp = Decimal(settings.market.points_per_pip)
        self.day = None
        self.first_open = None               # the open of the first candle at or after move_from today
        self.last_close = None               # the close of the last candle before move_until
        self.move = None                     # (direction to trade, the move's text) once judged at move_until
        self.judged = False
        self.waiting: list[Setup] = []
        self.due: list[Setup] = []
        self.notes: list[tuple] = []

    def fork(self) -> "NewYorkOpenReversal":
        new = NewYorkOpenReversal.__new__(NewYorkOpenReversal)
        new.__dict__.update(self.__dict__)
        new.waiting = [x.copy() for x in self.waiting]
        new.due = list(self.due)
        new.notes = []
        return new

    def warm(self, candles: list) -> None:
        for c in candles:
            self._day(c)
            self._measure(c)

    def _day(self, c: Candle) -> None:
        d, _ = uk_day_and_time(c, self.uk)
        if d != self.day:
            self.day, self.first_open, self.last_close, self.move, self.judged = d, None, None, None, False
            self.waiting, self.due = [], []

    def _measure(self, c: Candle) -> None:
        t = c.start.astimezone(self.uk).time()
        if self.n.move_from <= t < self.n.move_until:
            if self.first_open is None:
                self.first_open = c.sell_open
            self.last_close = c.sell_close

    def _judge(self, c: Candle) -> None:
        """At the first candle from move_until: the move from move_from, or none."""
        self.judged = True
        if self.first_open is None:
            return
        pips = (self.last_close - self.first_open) / self.ppp
        txt = (f"from {plain(self.first_open)} at {self.n.move_from:%H:%M} to {plain(self.last_close)} before "
               f"{self.n.move_until:%H:%M} UK, {plain(pips.quantize(Decimal('0.1')))} pips")
        if abs(pips) >= Decimal(self.n.min_move_pips):
            self.move = (SELL if pips > 0 else BUY, f"the move {txt} ({'up' if pips > 0 else 'down'}, at least "
                                                     f"{plain(self.n.min_move_pips)})")
            self.notes.append((c.start, self.move[0], self.move[1]))

    def on_candle(self, c: Candle) -> list[Candidate]:
        """One 5-minute candle (finished; live, the one forming so far): the trades that open at its open."""
        out: list[Candidate] = []
        for st in self.due[:1]:                                   # one a day: never two at once
            steps = st.steps + [f"{uk_short(c.start)} opens at this candle's open, {plain(c.sell_open)} (sell price)"]
            far = st.rejection.sell_high if st.direction == SELL else st.rejection.sell_low
            out.append(Candidate(NEW_YORK_OPEN_REVERSAL, st.direction, c.start, c.sell_open, steps,
                                 {"once_a_day": f"{NEW_YORK_OPEN_REVERSAL} {self.day}",
                                  **signal_context(st.direction, st.rejection.start, far, st.rejection.sell_close)}))
        self.due = []
        self._day(c)
        self._measure(c)
        t = c.start.astimezone(self.uk).time()
        if t >= self.n.move_until and not self.judged:
            self._judge(c)
        in_window = self.n.window_from <= t < self.n.window_until
        if not in_window:
            for st in self.waiting:
                self.notes.append((c.start, st.direction, f"{uk_short(c.start)} the window "
                                   f"{self.n.window_from:%H:%M} to {self.n.window_until:%H:%M} is over, no confirmation"))
            self.waiting = []
            return out
        for st in list(self.waiting):
            what, text = confirm_step(st, c, int(self.n.confirmation_within_candles))
            if what == "waiting":
                continue
            st.steps.append(text)
            self.notes.append((c.start, st.direction, text))
            self.waiting.remove(st)
            if what == "confirmed":
                self.due.append(st)
        if self.move is not None:
            direction, why = self.move
            sell = direction == SELL
            if (c.sell_close < c.sell_open) if sell else (c.sell_close > c.sell_open):
                text = (f"{uk_short(c.start)} rejection candle against the move, {'red' if sell else 'green'} "
                        f"({plain(c.sell_open)} to {plain(c.sell_close)}), high {plain(c.sell_high)}, "
                        f"low {plain(c.sell_low)}")
                self.notes.append((c.start, direction, text))
                self.waiting.append(Setup(direction, c, steps=[why, text]))
        return out
