"""Putting it together (design sections 1, 3, 4, 6, 7 and 13): the strategies, the safety rules, the order
sender and the trade manager, run inside the price service on its IG login.

  * After each finished 5-minute candle is stored: the analyser takes it (this engine's own StateTracker, as the
    replay); the trade manager runs every open trade on it (the scheduled closes, IG's stop and take profit, the
    slow grind's lock, the range trade's half close, the close on a rejection at a level, "watching a level");
    then the strategies run on it (strategies.replay.StrategyRunner, the same code as the replay) and every idea
    goes to the order sender, which applies the safety rules before anything is sent. A trade it opens is handed
    to the trade manager.
  * Every second, the latest price from the stream: the trade manager runs every open trade on it.
  * The master switch TRADING (.env): while it is off, everything runs and is recorded but the order sender is in
    paper mode: no order is ever sent to IG.
  * At start-up: the order sender's start-up (live: finds its own trades at IG; reads the funds), the trade
    manager takes over the open trades, and the strategies replay the week from its open up to now WITHOUT
    sending anything for the past, so they carry on from where the week is.
Entries are found when a 5-minute candle finishes (the strategies are written for finished candles), so a live
order goes at the market a moment after the candle that reached its entry price.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Callable

from analyser.market_state import MemoStore, StateTracker
from analyser.trend_day import trend_day_at
from orders.sender import OrderSender
from strategies.replay import StrategyRunner
from trade_manager.manager import Bar, Rejection, TradeManager, plan

log = logging.getLogger("autobot.trading")
UTC = timezone.utc


def analyser_rejections(watcher: Any, at: datetime) -> list[Rejection]:
    """The analyser's confirmed rejections at levels that count, triggered in the candle starting at `at`."""
    out = []
    for e in watcher.events:
        if e.version == "bounce" and e.kind == "trigger" and e.time == at:
            st = watcher.setups[e.setup - 1]
            levels = [p for p in st.pierced if "Bollinger" not in p["what"]]
            if levels and st.counts:
                out.append(Rejection(e.direction, e.price, ", ".join(f"{p['what']} {p['price']}" for p in levels)))
    return out


def analyser_watching(watcher: Any) -> set[str]:
    """The directions of the analyser's bounce setups running now at levels that count."""
    return {st.direction for st in watcher.setups
            if st.version == "bounce" and st.status == "running" and st.counts
            and any("Bollinger" not in p["what"] for p in st.pierced)}


class Trading:
    def __init__(self, settings: Any, store: Any, client: Any, alerts: Any, *, trading_on: bool,
                 now: Callable[[], datetime] = lambda: datetime.now(UTC),
                 quote: Callable[[], tuple[Decimal, Decimal] | None] = lambda: None,
                 calendar: list | None = None, replay_end: datetime | None = None,
                 sleep: Callable[[float], None] | None = None):
        """`replay_end`: a replay (the replay check): the hourly trend read once up to it, each new trade run on
        the candle it opened in, as the research. `calendar`: the economic calendar (None: the one on disk)."""
        self.s, self.store, self.alerts, self.now = settings, store, alerts, now
        self.trading_on, self.calendar, self.replay = trading_on, calendar, replay_end is not None
        self.memo = MemoStore(store)
        self.tracker = StateTracker(settings, self.memo)
        self.runner = StrategyRunner(settings, self.memo, self.tracker, hourly_end=replay_end)
        self.quote = quote
        kw = {"sleep": sleep} if sleep is not None else {}
        self.sender = OrderSender(settings, client, alerts, now=now, quote=quote, paper=not trading_on, **kw)
        self.manager = TradeManager(settings, self.sender, now=now, ig_confirms=trading_on)
        self.ready = False
        self._lock = threading.RLock()
        self._last_tick = None
        self.opened: list[tuple[Any, Any]] = []            # (idea, trade manager's trade), for checks

    # ---- start-up ------------------------------------------------------------------------------

    def start(self, now: datetime | None = None) -> None:
        with self._lock:
            now = now or self.now()
            self.sender.start()
            for t in [t for t in self.sender.trades.values() if t.status == "open"]:
                mt = plan(self.s, t.reference, t.strategy, t.direction, t.opened_at, t.level, t.level, t.stop_pips,
                          self.calendar, self._trend_day(t.opened_at))
                if t.half_closed:
                    mt.half_done, mt.state = True, "half close"
                mt.bars = 1                                 # already open: no entry-candle rule
                self.manager.add(mt)
            if not self.replay:
                self.tracker.replay(now)
                self.runner.step()                          # the week so far: nothing is sent for the past
            self.ready = True
            log.info("Trading %s: %d open trade(s) taken over; the strategies are up to %s.",
                     "ON" if self.trading_on else "OFF (paper trades, nothing sent to IG)",
                     len([t for t in self.manager.trades.values() if t.open]), now.strftime("%Y-%m-%d %H:%M UTC"))

    def _trend_day(self, t: datetime) -> str | None:
        try:
            return trend_day_at(self.s, self.store, t).direction
        except Exception:                                   # noqa: BLE001  (no trend day if it cannot be worked out)
            return None

    # ---- each finished 5-minute candle --------------------------------------------------------------

    def on_candle(self, now: datetime) -> None:
        """After a new 5-minute candle is stored (the price service's after_new_candle)."""
        with self._lock:
            if not self.ready:
                return
            self.tracker.advance(now)
            self._take_new_candles()

    def _take_new_candles(self) -> None:
        hist = self.tracker.history
        first = self.runner.done if self.runner.week_open == self.tracker.week_open else 0
        new = [h[0] for h in hist[first:]]
        ideas_by_candle: dict = {}
        for c, idea in self.runner.step():
            ideas_by_candle.setdefault(c.start, []).append(idea)
        watching = analyser_watching(self.tracker.watcher)
        for k, f in enumerate(new):
            c = f.candle
            i = first + k
            band = (hist[i - 1][0].upper, hist[i - 1][0].lower) if i > 0 and hist[i - 1][0].upper is not None else None
            rej = analyser_rejections(self.tracker.watcher, c.start)
            self.manager.on_bar(Bar.of(c), band, rej, watching if k == len(new) - 1 else frozenset())
            for idea in ideas_by_candle.get(c.start, []):
                if idea.allowed:
                    self._send(idea, c, band, rej)

    def _send(self, idea: Any, candle: Any, band: Any, rej: list[Rejection]) -> None:
        td = self._trend_day(idea.time)
        if self.replay:
            sell = idea.direction == "sell"
            fill = idea.entry_price if sell else idea.entry_price + (candle.buy_open - candle.sell_open)
            self.sender.quote = lambda: (fill, fill)        # the research's fill: the entry, plus the spread for a buy
        r = self.sender.place(idea, trend_day=td, calendar=self.calendar)
        if not r.ok:
            return
        t = self.sender.trades[r.reference]
        opened_at = candle.start if self.replay else self.now()
        mt = plan(self.s, r.reference, idea.strategy, idea.direction, opened_at, idea.entry_price, r.level,
                  t.stop_pips, self.calendar, td)
        if not self.replay:
            mt.bars = 1                                     # opened at the market after its candle: every price
                                                            # from now on is after it opened (no entry-candle rule)
        self.manager.add(mt)
        self.opened.append((idea, mt))
        if self.replay:                                     # as the research: it may close in the candle it opened in
            self.manager.on_bar(Bar.of(candle), band, rej, only=[r.reference])

    # ---- every second: the latest price -----------------------------------------------------------

    def on_price(self, tick: Any) -> None:
        """The latest price (prices.model.Tick): the trade manager runs every open trade on it."""
        with self._lock:
            if not self.ready or tick is None or tick is self._last_tick:
                return
            self._last_tick = tick
            if not any(t.open for t in self.manager.trades.values()):
                return
            b = Bar(tick.time, tick.buy, tick.buy, tick.buy, tick.buy, tick.sell, tick.sell, tick.sell, tick.sell)
            hist = self.tracker.history
            band = (hist[-1][0].upper, hist[-1][0].lower) if hist and hist[-1][0].upper is not None else None
            self.manager.on_bar(b, band, [], analyser_watching(self.tracker.watcher))
