"""Slow grind (design 3.1), written for a sell; a buy is the mirror image.
Sell (bid) price, 5-minute candles. Price moves in a staircase: it pauses
rather than bouncing back to the middle of the band.

  1. A pause starts with two candles going in opposite directions, in either
     order (red then green, or green then red; owner, 7 November 2026). No size
     test and no other condition. The pause's low is the lower of their lows.
  2. It counts as a pause once at least slow_grind.min_pause_candles (3)
     candles in a row have failed to make a new low while closing below the
     slow_grind.ema_periods (21) EMA. The second candle of the start counts when
     its low is not below the first one's and it closes below the 21 EMA. A new
     low before the pause counts throws it away, and a new pause may start there
     (kept, owner 7 November 2026). "Below the 21 EMA" is judged on closes (kept).
  3. The sell idea comes as soon as price breaks below the lowest point of the
     pause (entry price = that low; or the candle's open if it opened below it).
  4. A candle closing above the 21 EMA cancels it. No time limit.
The checks (switch, state, direction rule) are asked when the pause starts
(may_start); a pause they refuse is not started. With stored candles the break
is found from the next candles' lows. Ideas only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Callable

from prices.model import Candle, plain, uk_short
from strategies.common import BUY, SELL, SLOW_GRIND, Candidate


@dataclass
class _Pause:
    direction: str
    edge: Decimal                         # the pause's lowest point (sell) / highest (buy)
    started: Candle
    count: int = 1
    counted_at: Candle | None = None
    steps: list = field(default_factory=list)


class SlowGrind:
    def __init__(self, settings: Any, may_start: Callable | None = None):
        """may_start(strategy, direction, candle, price, during) -> (ok, note)."""
        self.s = settings
        self.side = settings.chart.price
        self.need = settings.slow_grind.min_pause_candles
        self.may_start = may_start
        self.prev: Candle | None = None
        self.pause: dict[str, _Pause | None] = {SELL: None, BUY: None}
        self.notes: list[tuple] = []              # (time, direction, what happened), for checking

    def _o(self, c): return getattr(c, f"{self.side}_open")
    def _h(self, c): return getattr(c, f"{self.side}_high")
    def _l(self, c): return getattr(c, f"{self.side}_low")
    def _c(self, c): return getattr(c, f"{self.side}_close")

    def on_candle(self, c: Candle, ema: Decimal | None) -> list[Candidate]:
        out: list[Candidate] = []
        if ema is not None:
            for d in (SELL, BUY):
                cand = self._step(d, c, ema)
                if cand is not None:
                    out.append(cand)
        self.prev = c
        return out

    def _step(self, d: str, c: Candle, ema: Decimal) -> Candidate | None:
        sell = d == SELL
        low, word = ("low", "below") if sell else ("high", "above")
        p = self.pause[d]
        if p is not None:
            beyond_ema = self._c(c) > ema if sell else self._c(c) < ema
            broke = self._l(c) < p.edge if sell else self._h(c) > p.edge
            if broke and p.count >= self.need:
                opened_past = self._o(c) < p.edge if sell else self._o(c) > p.edge
                price = self._o(c) if opened_past else p.edge
                self.pause[d] = None
                self.notes.append((c.start, d, f"broke {word} the pause's {low} {plain(p.edge)}: entry {plain(price)}"))
                return Candidate(SLOW_GRIND, d, c.start, price, p.steps + [
                    f"{uk_short(c.start)}: price broke {word} the pause's {low} {plain(p.edge)}"
                    + (f" (the candle opened past it, at {plain(price)})" if opened_past else " (during this candle)")])
            if broke:
                self.pause[d] = None
                self.notes.append((c.start, d, f"a new {low} {plain(self._l(c) if sell else self._h(c))} after "
                                               f"{p.count} candle(s): the pause is thrown away"))
            elif beyond_ema:
                self.pause[d] = None
                self.notes.append((c.start, d, f"closed {plain(self._c(c))} {'above' if sell else 'below'} the "
                                               f"{self.s.slow_grind.ema_periods} EMA {plain(ema.quantize(Decimal('0.1')))}: cancelled"))
                return None
            else:
                p.count += 1 if ((self._c(c) < ema) if sell else (self._c(c) > ema)) else 0
                if p.count == self.need and p.counted_at is None:
                    p.counted_at = c
                    p.steps.append(f"{uk_short(c.start)}: a pause: {p.count} candles in a row without a new "
                                   f"{low} {word} {plain(p.edge)}, closing {word} the {self.s.slow_grind.ema_periods} EMA")
                    self.notes.append((c.start, d, f"a pause ({p.count} candles); waiting for a break of {plain(p.edge)}"))
                return None
        if self.pause[d] is None and self.prev is not None:
            first, second = self.prev, c
            red = lambda x: self._c(x) < self._o(x)  # noqa: E731
            green = lambda x: self._c(x) > self._o(x)  # noqa: E731
            if not ((red(first) and green(second)) or (green(first) and red(second))):
                return None
            edge = min(self._l(first), self._l(second)) if sell else max(self._h(first), self._h(second))
            held = self._l(second) >= self._l(first) if sell else self._h(second) <= self._h(first)
            under = self._c(second) < ema if sell else self._c(second) > ema
            colours = "red then green" if red(first) else "green then red"
            if self.may_start is not None:
                ok, note = self.may_start(SLOW_GRIND, d, c, self._c(c), False)
                if not ok:
                    self.notes.append((c.start, d, f"a pause would start ({colours}) but is not started: {note}"))
                    return None
            else:
                note = ""
            count = 1 if (held and under) else 0
            self.pause[d] = _Pause(d, edge, first, count, None, [
                f"{uk_short(first.start)}-{uk_short(second.start)[-9:]}: a pause starts: {colours}, the pause's "
                f"{low} {plain(edge)}" + (f"; the second candle counts (no new {low}, closed {word} the "
                                         f"{self.s.slow_grind.ema_periods} EMA {plain(ema.quantize(Decimal('0.1')))})" if count else "")]
                + ([note] if note else []))
            self.notes.append((c.start, d, f"a pause starts ({colours}), {low} {plain(edge)}"))
            if count >= self.need:
                self.pause[d].counted_at = c
        return None
