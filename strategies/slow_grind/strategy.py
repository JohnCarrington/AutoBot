"""Slow grind (design 3.1), written for a sell; a buy is the mirror image.
Sell (bid) price, 5-minute candles. Only the rules written in 3.1 (rule 1, the
two-candle start, was removed by the owner on 7 November 2026; the others keep
their numbers):

  2. It counts as a pause once at least slow_grind.min_pause_candles (2)
     candles in a row have failed to make a new low while staying below the
     slow_grind.ema_periods (21) EMA.
  3. The sell opens as soon as price breaks below the lowest point of the pause.
  4. A candle closing above the 21 EMA cancels the setup. No time limit.

Choices section 3.1 does not make (the simplest, adding no rule; listed for the owner):
  * "a new low" is a low below the last low made: the low of the candle that
    made it (the reference). The first candle watched is the first reference;
  * a candle that goes below the reference before the pause counts makes a new
    low: it becomes the reference and the row starts again from nothing;
  * "staying below the 21 EMA" is judged on the close; a candle closing exactly
    on the EMA neither counts nor cancels, and the row starts again;
  * "the lowest point of the pause" is the lowest low of the candles in the row
    (the candles that failed to make a new low), not the reference;
  * once the pause counts, a candle going below its lowest point opens the
    sell (at that point, or at the candle's open if it opened below it); the
    candle that did so becomes the next reference;
  * after a cancel (rule 4) nothing carries over: the next candle is the next
    reference;
  * so in each direction there is one row at a time, by the meaning of
    "in a row", not by a limit.
With stored candles the break is found from a candle's low. Ideas only.

Switched on by the owner on 8 November 2026. Its other rules (3.1 rules 5 to 7) are shared
checks in strategies/common.py: trend only, in the trend's direction, no direction rule;
its own stop (15), take profit (20, or 100 on a big-news day) and profit lock (15/10); new
trades any time except 20:30 to midnight UK, the first 15 minutes after the Sunday open and
21:55 to 22:15 UK; big news allowed; closed at 20:30 UK every day; no level close.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from prices.model import Candle, plain, uk_short
from strategies.common import BUY, SELL, SLOW_GRIND, Candidate


@dataclass
class _Watch:
    direction: str
    ref: Candle | None = None                 # the candle that made the last low (sell) / high (buy)
    row: list = field(default_factory=list)   # candles in a row without a new low, closing below the EMA


class SlowGrind:
    def __init__(self, settings: Any):
        self.s = settings
        self.side = settings.chart.price
        self.need = settings.slow_grind.min_pause_candles
        self.watch = {SELL: _Watch(SELL), BUY: _Watch(BUY)}
        self.notes: list[tuple] = []              # (time, direction, what happened), for checking

    def _o(self, c): return getattr(c, f"{self.side}_open")
    def _h(self, c): return getattr(c, f"{self.side}_high")
    def _l(self, c): return getattr(c, f"{self.side}_low")
    def _c(self, c): return getattr(c, f"{self.side}_close")

    def on_candle(self, c: Candle, ema: Decimal | None) -> list[Candidate]:
        out: list[Candidate] = []
        if ema is not None:
            for d in (SELL, BUY):
                cand = self._step(self.watch[d], c, ema)
                if cand is not None:
                    out.append(cand)
        return out

    def _step(self, w: _Watch, c: Candle, ema: Decimal) -> Candidate | None:
        sell = w.direction == SELL
        low, word = ("low", "below") if sell else ("high", "above")
        x = self._l if sell else self._h                       # the extreme that matters
        past = (lambda a, b: a < b) if sell else (lambda a, b: a > b)
        q = lambda v: plain(v.quantize(Decimal("0.1")))  # noqa: E731
        if w.ref is None:
            w.ref, w.row = c, []
            return None
        if len(w.row) >= self.need:                            # 3. a pause: does price break its lowest point?
            edge = min(self._l(r) for r in w.row) if sell else max(self._h(r) for r in w.row)
            if past(x(c), edge):
                opened = past(self._o(c), edge)
                price = self._o(c) if opened else edge
                steps = [f"{uk_short(w.ref.start)}: the last {low} made: {plain(x(w.ref))}",
                         f"{uk_short(w.row[0].start)} to {uk_short(w.row[-1].start)[-9:]}: a pause: {len(w.row)} "
                         f"candles in a row without a new {low}, closing {word} the {self.s.slow_grind.ema_periods} EMA; "
                         f"its lowest point {plain(edge)}" if sell else
                         f"{uk_short(w.row[0].start)} to {uk_short(w.row[-1].start)[-9:]}: a pause: {len(w.row)} "
                         f"candles in a row without a new {low}, closing {word} the {self.s.slow_grind.ema_periods} EMA; "
                         f"its highest point {plain(edge)}",
                         f"{uk_short(c.start)}: price broke {word} it"
                         + (f" (the candle opened past it, at {plain(price)})" if opened else " (during this candle)")]
                self.notes.append((c.start, w.direction, f"broke {word} the pause's {plain(edge)}: entry {plain(price)}"))
                w.ref, w.row = c, []
                return Candidate(SLOW_GRIND, w.direction, c.start, price, steps)
        if past(x(c), x(w.ref)):                               # a new low: the next reference, the row starts again
            w.ref, w.row = c, []
            return None
        if (self._c(c) > ema) if sell else (self._c(c) < ema):  # 4.
            if w.row:
                self.notes.append((c.start, w.direction, f"closed {q(self._c(c))} {'above' if sell else 'below'} the "
                                                         f"{self.s.slow_grind.ema_periods} EMA {q(ema)} after "
                                                         f"{len(w.row)} candle(s): cancelled"))
            w.ref, w.row = None, []
            return None
        if (self._c(c) < ema) if sell else (self._c(c) > ema):  # 2.
            w.row.append(c)
            if len(w.row) == self.need:
                self.notes.append((c.start, w.direction, f"a pause ({self.need} candles from "
                                                         f"{uk_short(w.row[0].start)[-9:]}); {low} {plain(x(w.ref))} not broken"))
        else:
            w.row = []                                          # closed exactly on the EMA
        return None
