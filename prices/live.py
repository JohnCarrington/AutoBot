"""The 5-minute candles as the live price stream showed them (Phase 2 review R3.1; owner's brief of 27 November 2026).

Only one use: STP's authorisation check (stp/authorise.py) may let the candle that has just finished stand in for the
authoritative one IG has not published yet (its normal publication delay, under a second), but ONLY when live coverage
of that whole candle is established. This is built from EVERY price the feed receives (prices/feed.py on_tick), not the
engine's once-a-second sample, and coverage comes only from the stream's own connection state, with no timing number:

  * a candle is WHOLE when one connection was delivering prices without interruption from before the candle began to
    after it ended: the first price on a connection starts coverage from the NEXT candle (the one it arrives in was
    entered part-way); IG's stream sends every price change, so no price on an unbroken connection means no change;
  * anything that breaks the connection's continuity ends coverage at once: a drop and reconnection, IG's library
    reporting the stream STALLED, a re-login, a restart (a new feed). After it, coverage starts again only from the
    next candle after the next price.

A candle not whole is never offered as a stand-in; the authorisation then refuses (PD-5). Once IG publishes the
authoritative candle, the store holds it and it decides; this is never stored, never used for anything else."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from prices.model import Candle

FIVE = timedelta(minutes=5)


def _slot(t: datetime) -> datetime:
    return t.replace(minute=t.minute - t.minute % 5, second=0, microsecond=0)


class LiveCandles:
    def __init__(self) -> None:
        self.current: Candle | None = None
        self.previous: Candle | None = None
        self.covered_from: datetime | None = None   # the first candle start this connection has seen whole
        self._last: Any = None

    def interrupted(self) -> None:
        """The stream's continuity is broken (a drop, a stall, a new connection)."""
        self.covered_from = None
        self._last = None

    def add(self, tick: Any) -> None:
        s = _slot(tick.time)
        if self.covered_from is None:               # the first price since the stream (re)started: this candle was
            self.covered_from = s + FIVE            # entered part-way, the next one is the first seen whole
        c = self.current
        if c is None or c.start != s:
            self.previous = c
            o_buy, o_sell = (c.buy_close, c.sell_close) if c is not None and c.end == s and self._last is not None \
                else (tick.buy, tick.sell)          # unchanged since the last price: the candle opens at it
            c = Candle("5m", s, s + FIVE, o_buy, max(o_buy, tick.buy), min(o_buy, tick.buy), tick.buy,
                       o_sell, max(o_sell, tick.sell), min(o_sell, tick.sell), tick.sell)
        else:
            c = Candle("5m", c.start, c.end, c.buy_open, max(c.buy_high, tick.buy), min(c.buy_low, tick.buy), tick.buy,
                       c.sell_open, max(c.sell_high, tick.sell), min(c.sell_low, tick.sell), tick.sell)
        self.current = c
        self._last = tick

    def observed(self, start: datetime) -> tuple[Candle | None, bool]:
        """The candle starting at `start` as the stream showed it, and whether it was seen whole (see the module
        text). Asked after the candle has ended; a candle with no price yet (an unbroken quiet stream) is the last
        price carried, still whole."""
        c = next((x for x in (self.current, self.previous) if x is not None and x.start == start), None)
        whole = self.covered_from is not None and start >= self.covered_from
        if c is None and whole and self.current is not None and self.current.end <= start:
            last = self.current                     # no price at all in that candle on an unbroken stream
            c = Candle("5m", start, start + FIVE, last.buy_close, last.buy_close, last.buy_close, last.buy_close,
                       last.sell_close, last.sell_close, last.sell_close, last.sell_close)
        return c, whole and c is not None
