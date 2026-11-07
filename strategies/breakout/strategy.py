"""Breakout (design 3.5; owner, 7 November 2026). Sell (bid) price. Ideas only.

  1. It looks for a trade only at the moment the analyser moves into an emerging
     trend because price broke out of a range ("broke out of the range") or
     because a candle closed outside the Bollinger band out of a consolidation
     ("broke out of the consolidation"): that candle is the breakout candle.
  2. A buy (breakout up) opens as soon as price breaks above the breakout
     candle's high; a sell (breakout down) as soon as price breaks below its low.
  3. Not broken within breakout.trigger_within_candles (3) candles after the
     breakout candle: the setup expires.
  4. Only in the direction of the day's move so far: a buy only when the entry
     price is above that day's 00:00 UK open, a sell only when it is below. The
     day's open is the open of the 5-minute candle starting at 00:00 UK; a day
     whose 00:00 candle was not seen gives no breakout trade.
The idea records the range or consolidation it broke out of (its lowest low and
highest high, from its start to the candle before the breakout candle). With
stored candles the break is found from a candle's high or low; a candle that
opened past the price enters at its open.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time as clock
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from analyser.states import CONSOLIDATION, EMERGING, RANGING, UP
from prices.model import Candle, plain, uk_short
from strategies.common import BREAKOUT, BUY, SELL, Candidate

# The analyser's reasons for these changes (analyser/states.py), by the state left.
BREAKOUT_REASONS = {CONSOLIDATION: "broke out of the consolidation", RANGING: "broke out of the range"}


@dataclass
class _Setup:
    direction: str
    candle: Candle
    price: Decimal
    waited: int = 0
    context: dict = field(default_factory=dict)
    steps: list = field(default_factory=list)


class Breakout:
    def __init__(self, settings: Any):
        self.s = settings
        self.side = settings.chart.price
        self.limit = settings.breakout.trigger_within_candles
        tz = settings.hours.timezone
        self.uk = ZoneInfo(tz) if isinstance(tz, str) else tz
        self.setups: list[_Setup] = []
        self.recent: list[Candle] = []
        self.day_open: tuple | None = None          # (UK date, open of its 00:00 UK candle)
        self.notes: list[tuple] = []

    def _o(self, c): return getattr(c, f"{self.side}_open")
    def _h(self, c): return getattr(c, f"{self.side}_high")
    def _l(self, c): return getattr(c, f"{self.side}_low")

    def on_candle(self, c: Candle, change: Any = None, since: datetime | None = None) -> list[Candidate]:
        """`change`: the analyser's state change decided on this candle (or None); `since`: when the
        range or consolidation it left began."""
        lt = c.start.astimezone(self.uk)
        if lt.time() == clock(0, 0):
            self.day_open = (lt.date(), self._o(c))
        out = []
        for st in list(self.setups):
            buy = st.direction == BUY
            hit = self._h(c) > st.price if buy else self._l(c) < st.price
            if hit:
                opened = self._o(c) > st.price if buy else self._o(c) < st.price
                px = self._o(c) if opened else st.price
                self.setups.remove(st)
                op = self.day_open[1] if self.day_open and self.day_open[0] == lt.date() else None
                if op is None:
                    self.notes.append((c.start, st.direction, "broken, but the day's 00:00 UK open was not seen: no trade"))
                    continue
                if not (px > op if buy else px < op):
                    self.notes.append((c.start, st.direction, f"broken at {plain(px)}, but {'not above' if buy else 'not below'} "
                                                              f"the day's open {plain(op)}: no trade"))
                    continue
                out.append(Candidate(BREAKOUT, st.direction, c.start, px, st.steps + [
                    f"{uk_short(c.start)}: price broke {'above' if buy else 'below'} {plain(st.price)}"
                    + (f" (the candle opened past it, at {plain(px)})" if opened else " (during this candle)"),
                    f"the day's move: {plain(px)} is {'above' if buy else 'below'} the day's 00:00 UK open {plain(op)}"],
                    dict(st.context, day_open=op)))
                continue
            st.waited += 1
            if st.waited >= self.limit:
                self.setups.remove(st)
                self.notes.append((c.start, st.direction, f"expired: {plain(st.price)} not broken within {self.limit} candles"))
        left = getattr(change, "previous_state", None) if change is not None else None
        if (left in BREAKOUT_REASONS and change.state == EMERGING
                and str(change.reason).startswith(BREAKOUT_REASONS[left])):
            d = BUY if change.direction == UP else SELL
            rng = [x for x in self.recent if since is None or x.start >= since]
            ctx = {"broke_out_of": "range" if left == RANGING else "consolidation",
                   "base_low": min((self._l(x) for x in rng), default=None),
                   "base_high": max((self._h(x) for x in rng), default=None),
                   "base_since": since, "breakout_candle": c.start}
            price = self._h(c) if d == BUY else self._l(c)
            self.setups.append(_Setup(d, c, price, 0, ctx, [
                f"{uk_short(c.start)}: the analyser moved from {left} to an emerging trend {change.direction}: {change.reason}",
                f"entry: {'above the breakout candle high' if d == BUY else 'below the breakout candle low'} "
                f"{plain(price)}, within {self.limit} candles"]))
            self.notes.append((c.start, d, f"setup at {plain(price)} ({ctx['broke_out_of']})"))
        self.recent.append(c)
        self.recent = self.recent[-600:]
        return out
