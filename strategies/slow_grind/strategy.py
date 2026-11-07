"""Slow grind (design 3.1), written for a sell; a buy is the mirror image.
Sell (bid) price, 5-minute candles. Only the rules written in 3.1:

  1. A pause starts with two candles going in opposite directions (red then
     green, or green then red). No size test.
  2. It counts as a pause once at least slow_grind.min_pause_candles (3)
     candles in a row have failed to make a new low while staying below the
     slow_grind.ema_periods (21) EMA.
  3. The sell opens as soon as price breaks below the lowest point of the pause.
  4. A candle closing above the 21 EMA cancels the setup. No time limit.

Choices section 3.1 does not make (the simplest, adding no rule; listed for the owner):
  * a candle is red when it closes below its open, green when above; a candle
    closing at its open is neither, so it cannot start a pause;
  * every pair of opposite candles starts its own pause (several may run at once);
  * the pause's lowest point is the lowest low of all its candles so far,
    starting with the two that started it;
  * the candles "in a row" are those after the two that started it; "staying
    below the 21 EMA" is judged on the close; a candle that makes a new low
    before the pause counts starts the row again from nothing (and its low
    becomes the pause's lowest point), and so does a close exactly on the EMA;
  * rule 4 applies to the candles after the two that started it;
  * with stored candles the break is found from a candle's low; a candle that
    opened below the low enters at its open.
Ideas only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from prices.model import Candle, plain, uk_short
from strategies.common import BUY, SELL, SLOW_GRIND, Candidate


@dataclass
class _Pause:
    direction: str
    edge: Decimal                         # the pause's lowest point (sell) / highest (buy)
    started: Candle                       # the second of the two candles that started it
    row: int = 0                          # candles in a row without a new low, closing below the EMA
    steps: list = field(default_factory=list)


class SlowGrind:
    def __init__(self, settings: Any):
        self.s = settings
        self.side = settings.chart.price
        self.need = settings.slow_grind.min_pause_candles
        self.prev: Candle | None = None
        self.pauses: list[_Pause] = []
        self.notes: list[tuple] = []              # (time, direction, what happened), for checking

    def _o(self, c): return getattr(c, f"{self.side}_open")
    def _h(self, c): return getattr(c, f"{self.side}_high")
    def _l(self, c): return getattr(c, f"{self.side}_low")
    def _c(self, c): return getattr(c, f"{self.side}_close")

    def on_candle(self, c: Candle, ema: Decimal | None) -> list[Candidate]:
        out: list[Candidate] = []
        if ema is not None:
            for p in list(self.pauses):
                cand = self._step(p, c, ema)
                if cand is not None:
                    out.append(cand)
            self._start(c, ema)
        self.prev = c
        return out

    def _step(self, p: _Pause, c: Candle, ema: Decimal) -> Candidate | None:
        sell = p.direction == SELL
        low, word = ("low", "below") if sell else ("high", "above")
        q = lambda x: plain(x.quantize(Decimal("0.1")))  # noqa: E731
        broke = self._l(c) < p.edge if sell else self._h(c) > p.edge
        if broke and p.row >= self.need:                                    # 3.
            opened_past = self._o(c) < p.edge if sell else self._o(c) > p.edge
            price = self._o(c) if opened_past else p.edge
            self.pauses.remove(p)
            self.notes.append((c.start, p.direction, f"broke {word} the pause's {low} {plain(p.edge)}: entry {plain(price)}"))
            return Candidate(SLOW_GRIND, p.direction, c.start, price, p.steps + [
                f"{uk_short(c.start)}: price broke {word} the pause's {low} {plain(p.edge)}"
                + (f" (the candle opened past it, at {plain(price)})" if opened_past else " (during this candle)")])
        if (self._c(c) > ema) if sell else (self._c(c) < ema):              # 4.
            self.pauses.remove(p)
            self.notes.append((c.start, p.direction, f"pause from {uk_short(p.started.start)[-9:]}: closed {q(self._c(c))} "
                                                     f"{'above' if sell else 'below'} the {self.s.slow_grind.ema_periods} EMA {q(ema)}: cancelled"))
            return None
        if broke:                                                           # 2. a new low: the row starts again
            p.edge = self._l(c) if sell else self._h(c)
            p.row = 0
            return None
        p.row = p.row + 1 if ((self._c(c) < ema) if sell else (self._c(c) > ema)) else 0
        if p.row == self.need:
            p.steps.append(f"{uk_short(c.start)}: a pause: {p.row} candles in a row without a new {low} "
                           f"{word} {plain(p.edge)}, closing {word} the {self.s.slow_grind.ema_periods} EMA")
            self.notes.append((c.start, p.direction, f"pause from {uk_short(p.started.start)[-9:]} counts; waiting "
                                                     f"for a break of {plain(p.edge)}"))
        return None

    def _start(self, c: Candle, ema: Decimal) -> None:                     # 1.
        first = self.prev
        if first is None:
            return
        red = lambda x: self._c(x) < self._o(x)  # noqa: E731
        green = lambda x: self._c(x) > self._o(x)  # noqa: E731
        if not ((red(first) and green(c)) or (green(first) and red(c))):
            return
        colours = "red then green" if red(first) else "green then red"
        for d in (SELL, BUY):
            edge = min(self._l(first), self._l(c)) if d == SELL else max(self._h(first), self._h(c))
            low = "low" if d == SELL else "high"
            self.pauses.append(_Pause(d, edge, c, 0, [
                f"{uk_short(first.start)}-{uk_short(c.start)[-9:]}: a pause starts: {colours}; the pause's {low} "
                f"{plain(edge)} (21 EMA {plain(ema.quantize(Decimal('0.1')))})"]))
            self.notes.append((c.start, d, f"a pause starts ({colours}), {low} {plain(edge)}"))
