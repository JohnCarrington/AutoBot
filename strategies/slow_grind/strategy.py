"""Slow grind (design 3.1), written for a sell; a buy is the mirror image.
Sell (bid) price, 5-minute candles. Price moves in a staircase: it pauses
rather than bouncing back to the middle of the band.

  1. A pause starts with two candles going in opposite directions: for a sell,
     a red candle then a green one (no size test). The red candle's low is the
     low the pause must not break.
  2. It counts as a pause once at least slow_grind.min_pause_candles candles in
     a row (from the green one) have failed to make a new low while closing
     below the slow_grind.ema_periods (21) EMA. A new low before then is not a
     pause (the grind simply carried on).
  3. The sell idea comes as soon as price breaks below the lowest point of the
     pause (entry price = that low; or the candle's open if it opened below it).
  4. A candle closing above the 21 EMA cancels it. No time limit.
With stored candles the break is found from the next candles' lows (a candle
that opened past the low triggers at its open). Ideas only.
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
    started: Candle
    count: int = 1
    counted_at: Candle | None = None
    steps: list = field(default_factory=list)


class SlowGrind:
    def __init__(self, settings: Any):
        self.s = settings
        self.side = settings.chart.price
        self.need = settings.slow_grind.min_pause_candles
        self.prev: Candle | None = None
        self.pause: dict[str, _Pause | None] = {SELL: None, BUY: None}

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
        p = self.pause[d]
        if p is not None:
            beyond_ema = self._c(c) > ema if sell else self._c(c) < ema
            broke = self._l(c) < p.edge if sell else self._h(c) > p.edge
            if broke and p.count >= self.need:
                opened_past = self._o(c) < p.edge if sell else self._o(c) > p.edge
                price = self._o(c) if opened_past else p.edge
                self.pause[d] = None
                return Candidate(SLOW_GRIND, d, c.start, price, p.steps + [
                    f"{uk_short(c.start)}: price broke {'below' if sell else 'above'} the pause's "
                    f"{'low' if sell else 'high'} {plain(p.edge)}"
                    + (f" (the candle opened past it, at {plain(price)})" if opened_past else " (during this candle)")])
            if broke:                                   # a new low before the pause counted: no pause
                self.pause[d] = None
            elif beyond_ema:
                self.pause[d] = None                    # 4. closed beyond the 21 EMA: cancelled
                return None
            else:
                p.count += 1
                if p.count == self.need:
                    p.counted_at = c
                    p.steps.append(f"{uk_short(c.start)}: a pause: {p.count} candles in a row without a new "
                                   f"{'low' if sell else 'high'} below {plain(p.edge)}, closing "
                                   f"{'below' if sell else 'above'} the {self.s.slow_grind.ema_periods} EMA")
                return None
        if self.pause[d] is None and self.prev is not None:
            first, second = self.prev, c
            red = lambda x: self._c(x) < self._o(x)  # noqa: E731
            green = lambda x: self._c(x) > self._o(x)  # noqa: E731
            starts = (red(first) and green(second)) if sell else (green(first) and red(second))
            edge = self._l(first) if sell else self._h(first)
            holds = (self._l(second) >= edge) if sell else (self._h(second) <= edge)
            under = (self._c(first) < ema and self._c(second) < ema) if sell else \
                    (self._c(first) > ema and self._c(second) > ema)
            if starts and holds and under:
                self.pause[d] = _Pause(d, edge, first, 1, None, [
                    f"{uk_short(first.start)}-{uk_short(second.start)[-9:]}: a pause starts: a "
                    f"{'red then a green' if sell else 'green then a red'} candle, the "
                    f"{'low' if sell else 'high'} {plain(edge)} not broken, closing "
                    f"{'below' if sell else 'above'} the {self.s.slow_grind.ema_periods} EMA {plain(ema.quantize(Decimal('0.1')))}"])
                if self.need <= 1:
                    self.pause[d].counted_at = c
        return None
