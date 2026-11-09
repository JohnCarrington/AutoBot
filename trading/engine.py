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
  * Live entries (design 3: a trade opens as soon as the live price reaches its trigger): on every live price the
    5-minute candle forming so far is given to COPIES of the strategies (StrategyRunner.peek, the same code as for
    a finished candle); an idea whose entry price it has reached goes to the order sender at once. When that
    candle finishes, the strategies take it as always (so their state, and the replay, are unchanged) and an idea
    already sent live is not sent again; one the live prices did not show (a gap in the stream) is sent then.
    A trade opened during a candle is not run on that candle's earlier prices.
  * The trade manager's saved state (each open trade's best pips so far, half close, watching a level) is restored
    at start-up.
  * Records (records/book.py, design 9): every trade (opened and closed, with everything section 9 lists) and every
    decision (ideas and why they were blocked, the order sender's answers, the analyser's state changes, the trade
    manager's decisions, the pause switch); the daily and weekly summaries at trading.daily_summary_at (20:35 UK).
  * Telegram: "trade opened" and "trade closed" for every real trade (TRADING on); the daily summary every weekday
    (marked paper while TRADING is off).
  * The pause switch: while the file trading.pause_file exists, no new trade is sent; open trades are still run.
  * The dashboard's status (dashboard.status_folder/<PAIR>/status.json, every dashboard.status_every_seconds):
    the analyser's state and direction, the strategies allowed now, the open trades with live pips, today's
    trades and pips, warnings, whether TRADING is on and whether new trades are paused.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Callable

from analyser.market_state import MemoStore, StateTracker
from analyser.day_direction import day_directions
from analyser.trend_day import trend_day_at
from orders.sender import OrderSender
from records.book import Book, daily_text
from trading.reasons import level_note, one_line, take_profit_kind
from levels.current import build
from prices.calendar import floor_5m
from prices.model import Candle
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
        self.book = Book(settings, paper=not trading_on)
        self.manager.on_decision = lambda t, d, sent: self.book.decision(
            "trade manager", self.now(), reference=t.reference, strategy=t.strategy, decision=d.kind,
            price=d.price, pips=d.pips, why=d.why, order_sender=getattr(sent, "what", None))
        self.meta: dict = {}                                # reference -> what the records and messages need
        self._changes_seen = 0
        self._was_paused: bool | None = None
        self.ready = False
        self._lock = threading.RLock()
        self._last_tick = None
        self.opened: list[tuple[Any, Any]] = []            # (idea, trade manager's trade), for checks
        self.fired: set = set()                             # (strategy, direction, candle start) sent live
        self.partial: Candle | None = None                  # the 5-minute candle forming now, from the live prices
        self._levels: tuple | None = None                   # (candle start, its levels), for the live check

    # ---- start-up ------------------------------------------------------------------------------

    def start(self, now: datetime | None = None) -> None:
        with self._lock:
            now = now or self.now()
            self.sender.start()
            saved = self.manager.load_state()
            for t in [t for t in self.sender.trades.values() if t.status == "open"]:
                mt = plan(self.s, t.reference, t.strategy, t.direction, t.opened_at, t.level, t.level, t.stop_pips,
                          self.calendar, self._trend_day(t.opened_at))
                if t.half_closed:
                    mt.half_done, mt.state = True, "half close"
                mt.bars = 1                                 # already open: no entry-candle rule
                if self.manager.restore(mt, saved):         # its best pips so far, half close, watching
                    log.info("Trade %s: its saved best (%s pips) restored.", t.reference, mt.best)
                self.manager.add(mt)
            if not self.replay:
                self.tracker.replay(now)
                self.runner.step()                          # the week so far: nothing is sent for the past
            self._changes_seen = len(self.tracker.changes)
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
            for ch in self.tracker.changes[self._changes_seen:]:
                self.book.decision("analyser state change", ch.time, state=ch.state, direction=ch.direction,
                                   trend_type=ch.trend_type, line=ch.line() if hasattr(ch, "line") else str(ch))
            self._changes_seen = len(self.tracker.changes)
            self._take_new_candles()
            self._sync_ig()
            self._after_bars()

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
            before = [ref for ref, t in self.manager.trades.items() if t.open and t.opened_at <= c.start]
            self.manager.on_bar(Bar.of(c), band, rej, watching if k == len(new) - 1 else frozenset(), only=before)
            self._after_bars()
            for idea in ideas_by_candle.get(c.start, []):
                sent_live = (idea.strategy, idea.direction, c.start) in self.fired
                self.book.decision("idea", idea.time, strategy=idea.strategy, direction=idea.direction,
                                   entry_price=idea.entry_price, allowed=idea.allowed, blocked_by=idea.blocked_by,
                                   state=idea.state, already_sent_live=sent_live)
                if idea.allowed and not sent_live:
                    self._send(idea, c, band, rej)
        if new:
            last = new[-1].candle.start
            self.fired = {k for k in self.fired if k[2] > last}

    def _send(self, idea: Any, candle: Any, band: Any, rej: list[Rejection]) -> None:
        td = self._trend_day(idea.time)
        if self.replay:
            sell = idea.direction == "sell"
            fill = idea.entry_price if sell else idea.entry_price + (candle.buy_open - candle.sell_open)
            self.sender.quote = lambda: (fill, fill)        # the research's fill: the entry, plus the spread for a buy
        r = self._place(idea, td)
        if not r.ok:
            return
        self._opened(idea, r, candle.start if self.replay else self.now(), td)
        if self.replay:                                     # as the research: it may close in the candle it opened in
            self.manager.on_bar(Bar.of(candle), band, rej, only=[r.reference])
            self._after_bars()

    def _paused(self) -> bool:
        """The pause switch (the dashboard): while the file trading.pause_file exists, no new trade is sent."""
        from pathlib import Path
        paused = Path(self.s.trading.pause_file).exists()
        if paused != self._was_paused:
            if self._was_paused is not None or paused:
                self.book.decision("pause switch", self.now(), paused=paused)
            self._was_paused = paused
        return paused

    def _place(self, idea: Any, td: str | None) -> Any:
        day = day_directions(self.s, self.store, idea.time, self.calendar, td)
        r = self.sender.place(idea, paused=self._paused(), trend_day=td, calendar=self.calendar, day=day)
        self.book.decision("order", self.now(), strategy=idea.strategy, direction=idea.direction, result=r.what,
                           reference=r.reference, reasons=r.reasons, level=r.level)
        return r

    def _opened(self, idea: Any, r: Any, opened_at: datetime, td: str | None) -> None:
        """A trade the order sender opened: to the trade manager, the records, and Telegram (real trades)."""
        t = self.sender.trades[r.reference]
        mt = plan(self.s, r.reference, idea.strategy, idea.direction, opened_at, idea.entry_price, r.level,
                  t.stop_pips, self.calendar, td)
        if not self.replay:
            mt.bars = 1                                     # opened at the market: every later price is after it
        self.manager.add(mt)
        self.opened.append((idea, mt))
        ppp = Decimal(self.s.market.points_per_pip)
        sign = Decimal(1) if idea.direction == "buy" else Decimal(-1)
        state = f"{idea.state} {idea.state_direction}" + (f", {idea.trend_type}" if idea.trend_type else "")
        rec = {"reference": r.reference, "deal_id": r.deal_id, "pair": self.s.market.pair, "strategy": idea.strategy,
               "direction": idea.direction, "size_gbp_per_pip": self.s.trade.size_gbp_per_pip, "market_state": state,
               "opened_utc": opened_at, "entry_price": idea.entry_price, "open_price": r.level,
               "stop_pips": mt.stop_pips, "stop_price": mt.fill - sign * mt.stop_pips * ppp,
               "take_profit_pips": mt.take_profit_pips, "take_profit_price": mt.fill + sign * mt.take_profit_pips * ppp,
               "take_profit_kind": take_profit_kind(self.s, idea, mt.take_profit_pips, td),
               "reason": one_line(idea), "level": level_note(idea), "steps": list(idea.steps)}
        self.meta[r.reference] = rec
        self.book.opened(rec)
        if self.trading_on:
            self.alerts.trade_opened(self._opened_message(rec))

    def _opened_message(self, rec: dict) -> Any:
        from alerts.trades import TradeOpened
        return TradeOpened(rec["pair"], rec["direction"], Decimal(rec["size_gbp_per_pip"]), rec["strategy"],
                           rec["market_state"], Decimal(rec["open_price"]), Decimal(rec["stop_price"]),
                           Decimal(rec["take_profit_price"]), rec["opened_utc"], self.s.market.price_scale,
                           rec["reference"], Decimal(rec["stop_pips"]), Decimal(rec["take_profit_pips"]),
                           rec["take_profit_kind"], rec["reason"], rec["level"], self.s.market.epic)

    def _after_bars(self) -> None:
        """Every trade the trade manager has just finished: to the records, and Telegram (real trades)."""
        from alerts.trades import PartClose, TradeClosed
        size = Decimal(self.s.trade.size_gbp_per_pip)
        for ref, mt in self.manager.trades.items():
            rec = self.meta.get(ref)
            if mt.open or rec is None or rec.get("closed"):
                continue
            last = mt.decisions[-1]
            pips = mt.total_pips()
            gbp = (pips * size).quantize(Decimal("0.01"))
            half = rest = None
            if mt.half_pips is not None:
                h = next(d for d in mt.decisions if d.kind == "half close")
                half = PartClose(h.at or last.at, h.price, h.pips, (h.pips * size * mt.half_share).quantize(Decimal("0.01")), h.why)
                rest = PartClose(last.at, last.price, last.pips,
                                 (last.pips * size * (1 - mt.half_share)).quantize(Decimal("0.01")), last.why)
            best = max([x for x in (mt.best, last.pips) if x is not None], default=None)
            closed_at = last.at or self.now()
            lined = last.why.split("a confirmed rejection at a level: ", 1)[1] if "rejection at a level" in last.why else ""
            rec |= {"closed": True}
            row = {k: v for k, v in rec.items() if k not in ("closed", "steps")} | {
                "closed_utc": closed_at, "close_price": last.price, "how_closed": last.kind, "close_reason": last.why,
                "pips": pips, "gbp": gbp, "result": "win" if gbp > 0 else "loss" if gbp < 0 else "break even",
                "minutes_open": int((closed_at - rec["opened_utc"]).total_seconds() // 60), "best_pips": best,
                "levels_lined_up": lined,
                "half_close": None if half is None else vars(half), "rest": None if rest is None else vars(rest)}
            self.book.closed(row)
            if self.trading_on:
                today = self.book.today(closed_at)
                self.alerts.trade_closed(TradeClosed(self._opened_message(rec), last.price, closed_at, last.why, gbp,
                                                     pips, best, half, rest, today.trades, today.pips))

    def _sync_ig(self) -> None:
        """Live: a trade whose stop or take profit the trade manager expected IG to have closed, but IG had not yet,
        is asked about again (once a candle)."""
        if not self.trading_on:
            return
        for ref, mt in self.manager.trades.items():
            if mt.open and getattr(mt, "expected_at_ig", None):
                r = self.sender.closed_at_ig(ref, mt.expected_at_ig[0], mt.expected_at_ig[1])
                if r.ok:
                    self.manager.closed_at_ig(ref)

    def daily_summary(self, now: datetime) -> None:
        """At trading.daily_summary_at (20:35 UK) each weekday, once: the daily and weekly summaries are written and
        the daily one sent on Telegram."""
        import json
        from pathlib import Path
        uk_now = now.astimezone(self.book.uk)
        if uk_now.weekday() > 4 or uk_now.time() < self.s.trading.daily_summary_at:
            return
        marker = self.book.folder / "summary_sent.json"
        day = uk_now.date()
        try:
            if json.loads(marker.read_text()).get("day") == day.isoformat():
                return
        except (FileNotFoundError, ValueError):
            pass
        s = self.book.write_daily(day)
        from datetime import timedelta as td_
        week = self.book.summary(day - td_(days=day.weekday()), day)
        self.alerts.info(daily_text(self.s.market.pair, day, s, week, self.book.paper), html=True)
        Path(marker).parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(json.dumps({"day": day.isoformat()}) + "\n")

    # ---- every second: the latest price -----------------------------------------------------------

    def on_price(self, tick: Any) -> None:
        """The latest price (prices.model.Tick): the live check of every waiting setup's trigger, then the trade
        manager runs every open trade on it."""
        with self._lock:
            if not self.ready or tick is None or tick is self._last_tick:
                return
            self._last_tick = tick
            self.daily_summary(tick.time)
            self.write_status(tick.time)
            self._live_entries(tick)
            if not any(t.open for t in self.manager.trades.values()):
                return
            b = Bar(tick.time, tick.buy, tick.buy, tick.buy, tick.buy, tick.sell, tick.sell, tick.sell, tick.sell)
            hist = self.tracker.history
            band = (hist[-1][0].upper, hist[-1][0].lower) if hist and hist[-1][0].upper is not None else None
            self.manager.on_bar(b, band, [], analyser_watching(self.tracker.watcher))
            self._after_bars()

    # ---- live entries ---------------------------------------------------------------------------------

    def _forming(self, tick: Any) -> Candle:
        """The 5-minute candle forming now, as far as the live prices have gone."""
        start = floor_5m(tick.time)
        p = self.partial
        if p is None or p.start != start:
            p = Candle("5m", start, start + timedelta(minutes=5),
                       tick.buy, tick.buy, tick.buy, tick.buy, tick.sell, tick.sell, tick.sell, tick.sell)
        else:
            p = Candle("5m", p.start, p.end, p.buy_open, max(p.buy_high, tick.buy), min(p.buy_low, tick.buy), tick.buy,
                       p.sell_open, max(p.sell_high, tick.sell), min(p.sell_low, tick.sell), tick.sell)
        self.partial = p
        return p

    def _live_entries(self, tick: Any) -> None:
        import dataclasses
        p = self._forming(tick)
        if self._levels is None or self._levels[0] != p.start:
            self._levels = (p.start, build(self.s, self.memo, p.start))
        for idea in self.runner.peek(p, self._levels[1]):
            key = (idea.strategy, idea.direction, p.start)
            if not idea.allowed or key in self.fired:
                continue
            self.fired.add(key)
            idea = dataclasses.replace(idea, time=tick.time)
            idea.steps.append(f"reached on the live price at {tick.time.strftime('%H:%M:%S')} UTC "
                              f"(bid {tick.sell}, offer {tick.buy})")
            self.book.decision("idea", tick.time, strategy=idea.strategy, direction=idea.direction,
                               entry_price=idea.entry_price, allowed=True, blocked_by="", state=idea.state, live=True)
            td = self._trend_day(idea.time)
            r = self._place(idea, td)
            if not r.ok:
                continue
            self._opened(idea, r, tick.time, td)
            log.info("Live entry: %s %s at %s (entry price %s).", idea.strategy, idea.direction, r.level, idea.entry_price)

    # ---- the dashboard's status ----------------------------------------------------------------------

    def status(self, now: datetime) -> dict:
        """What the dashboard shows (written to its status file)."""
        from analyser.states import ALLOWED
        from strategies.common import SWITCH
        tick = self._last_tick
        ppp = Decimal(self.s.market.points_per_pip)
        m = getattr(self.tracker, "machine", None)
        st = getattr(m, "now", None)
        warnings = []
        if tick is None or (now - tick.time).total_seconds() > 60:
            warnings.append("No live price for over a minute")
        if self.sender.funds is None:
            warnings.append("The account's available funds are not known: new trades are refused")
        for ref, t in self.manager.trades.items():
            if t.open and t.expected_at_ig:
                warnings.append(f"Trade {ref}: IG's {t.expected_at_ig[0]} expected but not yet confirmed by IG")
        allowed = list(ALLOWED.get(st.state, ())) if st is not None else []
        by_name = {n.lower(): n for n in SWITCH}
        switches = {name: bool(getattr(self.s.switches, key, False)) for name, key in SWITCH.items()}
        trades = []
        for ref, t in self.manager.trades.items():
            if not t.open:
                continue
            live = None
            if tick is not None:
                live = ((t.fill - tick.buy) if t.direction == "sell" else (tick.sell - t.fill)) / ppp
            rec = self.meta.get(ref, {})
            trades.append({"reference": ref, "strategy": t.strategy, "direction": t.direction,
                           "opened_utc": t.opened_at.strftime("%Y-%m-%dT%H:%M:%SZ"), "open_price": str(t.fill),
                           "stop_pips": str(t.stop_pips), "take_profit_pips": str(t.take_profit_pips),
                           "live_pips": None if live is None else str(live.quantize(Decimal("0.1"))),
                           "best_pips": None if t.best is None else str(t.best), "decision": t.decision,
                           "half_closed": t.half_done, "reason": rec.get("reason", "")})
        today = self.book.today(now)
        return {"generated_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "pair": self.s.market.pair,
                "trading_on": self.trading_on, "paused": self._paused(),
                "analyser": None if st is None else {"state": st.state, "direction": st.direction,
                                                    "trend_type": st.trend_type,
                                                    "since_utc": st.since.strftime("%Y-%m-%dT%H:%M:%SZ")},
                "strategies_allowed": [{"name": a, "switched_on": switches.get(by_name.get(a.split(" (")[0].lower().replace(
                    "bollinger band bounce", "bollinger bounce"), ""), True)} for a in allowed],
                "price": None if tick is None else {"bid": str(tick.sell), "offer": str(tick.buy),
                                                    "time_utc": tick.time.strftime("%Y-%m-%dT%H:%M:%SZ")},
                "open_trades": trades,
                "today": {"trades": today.trades, "wins": today.wins, "losses": today.losses,
                          "pips": str(today.pips), "gbp": str(today.gbp)},
                "warnings": warnings}

    def write_status(self, now: datetime, force: bool = False) -> None:
        import json
        from pathlib import Path
        every = self.s.dashboard.status_every_seconds
        last = getattr(self, "_status_at", None)
        if not force and last is not None and (now - last).total_seconds() < every:
            return
        self._status_at = now
        folder = Path(self.s.dashboard.status_folder) / self.s.market.pair
        folder.mkdir(parents=True, exist_ok=True)
        tmp = folder / "status.json.tmp"
        tmp.write_text(json.dumps(self.status(now), indent=1) + "\n")
        tmp.replace(folder / "status.json")
