"""Breakout (design 3.5; owner, 7 November 2026). Sell (bid) price. Ideas only.

  1. It looks for a trade only at the moment the analyser moves from
     consolidation to an emerging trend because a 5-minute candle closed outside
     the Bollinger band: that candle is the breakout candle.
  2. A buy (breakout up) opens as soon as price breaks above the breakout
     candle's high; a sell (breakout down) as soon as price breaks below its low.
  3. Not broken within breakout.trigger_within_candles (3) candles after the
     breakout candle: the setup expires.
The idea records the consolidation's range (its lowest low and highest high,
from the consolidation's start to the candle before the breakout candle) for
the trade manager.
With stored candles the break is found from a candle's high or low; a candle
that opened past the price enters at its open.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from analyser.states import CONSOLIDATION, EMERGING, UP
from prices.model import Candle, plain, uk_short
from strategies.common import BREAKOUT, BUY, SELL, Candidate

BREAKOUT_REASON = "broke out of the consolidation"     # the analyser's reason for this change (analyser/states.py)


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
        self.setups: list[_Setup] = []
        self.recent: list[Candle] = []
        self.notes: list[tuple] = []

    def _o(self, c): return getattr(c, f"{self.side}_open")
    def _h(self, c): return getattr(c, f"{self.side}_high")
    def _l(self, c): return getattr(c, f"{self.side}_low")

    def on_candle(self, c: Candle, change: Any = None, consolidation_since: datetime | None = None) -> list[Candidate]:
        """`change`: the analyser's state change decided on this candle (or None); `consolidation_since`:
        when the consolidation it left began."""
        out = []
        for st in list(self.setups):
            buy = st.direction == BUY
            hit = self._h(c) > st.price if buy else self._l(c) < st.price
            if hit:
                opened = self._o(c) > st.price if buy else self._o(c) < st.price
                px = self._o(c) if opened else st.price
                self.setups.remove(st)
                out.append(Candidate(BREAKOUT, st.direction, c.start, px, st.steps + [
                    f"{uk_short(c.start)}: price broke {'above' if buy else 'below'} {plain(st.price)}"
                    + (f" (the candle opened past it, at {plain(px)})" if opened else " (during this candle)")],
                    dict(st.context)))
                continue
            st.waited += 1
            if st.waited >= self.limit:
                self.setups.remove(st)
                self.notes.append((c.start, st.direction, f"expired: {plain(st.price)} not broken within {self.limit} candles"))
        if (change is not None and getattr(change, "previous_state", None) == CONSOLIDATION
                and change.state == EMERGING and str(change.reason).startswith(BREAKOUT_REASON)):
            d = BUY if change.direction == UP else SELL
            rng = [x for x in self.recent if consolidation_since is None or x.start >= consolidation_since]
            ctx = {"consolidation_low": min((self._l(x) for x in rng), default=None),
                   "consolidation_high": max((self._h(x) for x in rng), default=None),
                   "consolidation_since": consolidation_since, "breakout_candle": c.start}
            price = self._h(c) if d == BUY else self._l(c)
            self.setups.append(_Setup(d, c, price, 0, ctx, [
                f"{uk_short(c.start)}: the analyser moved from consolidation to an emerging trend {change.direction}: "
                f"{change.reason}",
                f"entry: {'above the breakout candle high' if d == BUY else 'below the breakout candle low'} "
                f"{plain(price)}, within {self.limit} candles"]))
            self.notes.append((c.start, d, f"setup at {plain(price)}"))
        self.recent.append(c)
        self.recent = self.recent[-600:]
        return out
