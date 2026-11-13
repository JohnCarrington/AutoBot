"""Level reversal (design 3.6, owner, 8 November 2026), written for a sell; a buy is the mirror image.
Its ideas are the triggers of the strategies' own rejection watcher (rejection/watch.py,
design_only=True, the same setups as the Bollinger bounce, design 3.3), kept only when:

  1. the setup reached one of the levels in level_reversal.level_types: S2, R2, the daily pivot
     (owner, 13 November 2026) and round numbers, the round numbers only on a multiple of
     level_reversal.round_numbers_every_pips (100: the 00s, not the 50s);
  2. the furthest price went past that level, from the piercing candle to the confirmation candle,
     is no more than that kind of level's allowance: level_reversal.allowance_pips_r2 (12),
     allowance_pips_s2 (12), allowance_pips_round_number (5) (owner, 8 November 2026),
     allowance_pips_pivot (12, as at R2 and S2; owner, 13 November 2026). It may also
     have stopped short of the level
     (by up to rejection.near_level_within_pips, as the rejection part allows);
  3. entry when price breaks past the confirmation candle (the watcher's trigger: at the confirmation
     candle's low for a sell, or at the candle's open if it opened past it).

The stop is level_reversal.stop_beyond_furthest_pips (6) beyond that furthest point (the candidate's
context: "furthest", "stop_price"); the take profit level_reversal.take_profit_pips (20). The other
rules (states, no direction rule, hours, news, the 20:30 close, no level close) are the shared checks
in strategies/common.py.

Choices the owner's rules do not make (the simplest, as in the research of 8 November 2026):
  * the piercing candle is the setup's last one (a pierce again starts the count again, rejection/watch.py);
  * if several of these levels were reached, the first that passes rule 2 is the level (S2, R2 and the pivot
    before round numbers);
  * several setups triggering on the same candle and direction give one idea.
Sell (bid) prices, as the chart. Ideas only.
"""

from __future__ import annotations

from collections import deque
from decimal import Decimal
from typing import Any

from prices.model import Candle, plain, uk_short
from strategies.common import BUY, LEVEL_REVERSAL, SELL, Candidate

ROUND_NUMBER = "round_number"
KEEP_CANDLES = 300          # more than any setup lasts (pierce, reversal and confirmation within a few candles)


class LevelReversal:
    def __init__(self, settings: Any):
        self.s = settings
        self.lr = settings.level_reversal
        self.side = settings.chart.price
        self.ppp = Decimal(settings.market.points_per_pip)
        self.candles: deque = deque(maxlen=KEEP_CANDLES)

    def _h(self, c): return getattr(c, f"{self.side}_high")
    def _l(self, c): return getattr(c, f"{self.side}_low")

    def kind(self, what: str, price: Decimal) -> str | None:
        """The level's name if it is one this strategy trades, else None."""
        if what not in self.lr.level_types:
            return None
        if what == ROUND_NUMBER:
            pips = price / self.ppp
            if pips % self.lr.round_numbers_every_pips != 0:
                return None
            return f"round number {plain(price)}"
        return f"{what} {plain(price)}"

    def allowance(self, what: str) -> int:
        """How far past a level of this type price may go, in pips (design 3.6 rule 2)."""
        return getattr(self.lr, f"allowance_pips_{what.lower()}")

    def on_candle(self, c: Candle, watcher: Any, events: list) -> list[Candidate]:
        """Give it every finished candle, after the watcher has seen it, with the watcher's new events."""
        self.candles.append(c)
        out: list[Candidate] = []
        seen = set()
        for e in events:
            if e.version != "bounce" or e.kind != "trigger" or (e.time, e.direction) in seen:
                continue
            cand = self._candidate(watcher, e)
            if cand is not None:
                seen.add((e.time, e.direction))
                out.append(cand)
        return out

    def _candidate(self, watcher: Any, e: Any) -> Candidate | None:
        st = watcher.setups[e.setup - 1]
        if st.confirmation is None:
            return None
        sell = e.direction == SELL
        span = [c for c in self.candles if st.pierce.start <= c.start <= st.confirmation.start]
        if not span:
            return None
        furthest = max(self._h(c) for c in span) if sell else min(self._l(c) for c in span)
        order = sorted(st.pierced, key=lambda p: p["what"] == ROUND_NUMBER)      # S2, R2 and the pivot first
        for p in order:
            name = self.kind(p["what"], p["price"])
            if name is None:
                continue
            past = (furthest - p["price"]) if sell else (p["price"] - furthest)
            allowance = self.allowance(p["what"])
            if past > Decimal(allowance) * self.ppp:
                continue
            beyond = Decimal(self.lr.stop_beyond_furthest_pips) * self.ppp
            stop = furthest + beyond if sell else furthest - beyond
            word = "above" if sell else "below"
            steps = [x.describe() for x in watcher.events if x.setup == e.setup and x.kind != "ignored"]
            steps.append(f"{name}: furthest {'high' if sell else 'low'} {plain(furthest)} from "
                         f"{uk_short(st.pierce.start)} to {uk_short(st.confirmation.start)[-9:]}, "
                         f"{plain((past / self.ppp).quantize(Decimal('0.1')))} pips past the level "
                         f"(allowance {allowance})")
            steps.append(f"stop {plain(stop)}: {self.lr.stop_beyond_furthest_pips} pips {word} the furthest point; "
                         f"take profit {self.lr.take_profit_pips} pips")
            return Candidate(LEVEL_REVERSAL, SELL if sell else BUY, e.time, e.price, steps,
                             context={"level": p["price"], "level_name": name, "furthest": furthest,
                                      "past_level_pips": past / self.ppp, "stop_price": stop})
        return None
