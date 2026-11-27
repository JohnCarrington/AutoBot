"""The trade manager (design sections 3 and 4): runs each open trade by its own strategy's exits and tells
the order sender to close it, in full or by half. Not connected to the live service yet.

For each open trade, on each price bar (a finished 5-minute candle in a replay; live, a tick can be given as
a bar whose open, high, low and close are the same), in this order (as the research of 8 November 2026):
  1. the scheduled close, at the bar's open, once its time has come: 20:30 UK every day (bounce, range trade,
     slow grind, level reversal) or 20:30 UK on Friday only (EMA pullback, breakout)
     (strategies.common.forced_close_at), or 15 minutes before big news for the strategies closed before it
     (strategies.common.closed_before_big_news), whichever comes first. The bot closes it;
  2. the stop at IG (each strategy's own, strategies.common.stop_loss_pips; the level reversal's beyond the
     furthest point), filled at the stop or at the bar's open if it opened past it. In the entry bar the stop
     counts only if the bar opened past the entry price or closed beyond the stop (a candle does not say
     which came first). The slow grind's lock (strategies.common.profit_lock, 15/10): once the trade has been
     lock_from pips up (in an earlier bar), the bot closes it if price comes back to lock_at pips up. The
     Bollinger bounce's trail (owner, 15 November 2026; the session strategies the same, each with its own
     trail_from_pips and trail_candles: owner, 16 November 2026): once the trade has been bounce.trail_from_pips up (12),
     after each FINISHED 5-minute candle its stop is moved at IG to a tenth of a pip beyond the last
     bounce.trail_candles (3) finished candles (a sell: above their highest buy price; a buy: below their lowest
     sell price), only ever closer than the stop IG holds (TradeManager.on_bar with finished=True); from then on
     the stop at IG is there. The order sender sends the nearest level IG allows if the rule's level is on the
     wrong side of IG's price or inside IG's minimum stop distance (owner, 17 November 2026). Live, each move counts
     only once IG confirms it ("stop moved"); if IG does not confirm it the old stop stays ("stop not moved") and the
     move is tried again after orders.close_retry_seconds, up to orders.stop_move_attempts (3) in all; then the bot
     gives up on that level (one alert to the owner) and works the trail out again after the next finished candle.
     A later candle's level replaces one still waiting (owner, 17 November 2026).
     Johnny's exit for emerging-trend trades (owner, 21 November 2026; switch EMERGING_LADDER, on if left out;
     [emerging_ladder]): a trade opened while the analyser said "emerging trend" (up or down, as recorded on the trade
     at open; every strategy) has its stop at IG moved to +5 once it is +10, and to +10 once it is +15 (pips as IG
     closes it, from the fill). Checked after every price (each tick live, each candle in a replay), from the best
     pips reached so far. It goes through the same stop-move path as the trail (_move_stop: the nearest level IG
     allows, counted only once IG confirms it, 3 attempts then given up until the next finished candle). A level is
     asked for once; it is asked for again only at a new step, or after the next finished candle if IG's stop is not
     there yet (the nearest level IG allowed, or a move given up), at the trail's pace. Never
     backwards, and whichever stop is tighter wins: the ladder moves only to a level closer than the stop IG holds and
     than a move still waiting, and a trail level looser than the ladder's is not sent. The take profit is unchanged.
     Every confirmed stop move (trail or ladder) is kept on the trade (ManagedTrade.stop_moves) and recorded;
  3. the range trade's half close at the opposite band (range_trade.close_percent_at_opposite_band, 50%),
     the band as it stood at the last finished candle; the bot closes that part;
  4. the take profit at IG (strategies.common.take_profit_pips: 100 on a big-news day or in a trend day's
     direction where the design gives it);
  5. the close on a confirmed rejection at a level against the trade (the analyser's rejection part: a bounce
     the other way at a level that counts), only for the strategies the design says (the range trade)
     (strategies.common.closed_on_level_rejection), from the bar after the entry bar, at the rejection's
     trigger. Not for a trade in the day's expected news direction on a day with big news (design 2.4 and 4:
     the expected news direction takes precedence).
Prices: a buy closes on the sell price, a sell on the buy price; pips are from the price the trade opened at.
The stop and take profit are IG's: the manager records them (in a replay or a paper trade it fills them as IG
would); it never sends a close for them. Live, it asks the order sender to confirm with IG that IG closed the
trade, and the trade stays open until IG has; the record then has IG's own level and time.
Live, a close the bot sends counts only once IG confirms it (owner, 10 November 2026): if the order sender reports
it refused or unclear, the trade is put back exactly as it was before that bar (a close not done is recorded, never
a close), and the close is tried again after orders.close_retry_seconds. If IG had already closed the position
(the order sender's "gone at IG", also from its regular check of IG's open positions), the trade is finished as
"closed at IG" at IG's own level and time.
"Watching a level" (design 4): a trade the close on a rejection applies to is watching a level while the
analyser's rejection part has a setup running against it at a level that counts (after its pierce, before it
triggers, is cancelled or expires). It goes back to hold when there is none.
Every decision is recorded in trade_manager.folder/<PAIR>/decisions.jsonl. Each open trade's best pips reached so
far, its half close and whether it is watching a level are saved in trade_manager.folder/<PAIR>/open_trades.json
whenever they change, and restored after a restart (restore()), so the slow grind's lock and the rest carry on.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from analyser.states import EMERGING
from strategies.common import (BUY, RANGE_TRADE, SELL, closed_before_big_news, closed_on_level_rejection,
                               forced_close_at, profit_lock, take_profit_pips, trail)

UTC = timezone.utc
# The decisions (design 4: hold, half close, close, forced close, stopped by IG, take profit hit at IG).
HOLD, HALF_CLOSE, CLOSE, FORCED_CLOSE, STOPPED_BY_IG, TAKE_PROFIT_AT_IG, WATCHING = (
    "hold", "half close", "close", "forced close", "stopped by IG", "take profit hit at IG", "watching a level")
# Live only: IG closed the position without the bot (found by the order sender: IG's level and time), and a
# close the bot sent that IG did not confirm (the trade stays open; recorded, never a close).
CLOSED_AT_IG, CLOSE_NOT_DONE = "closed at IG", "close not done"
# The Bollinger bounce's stop moved at IG by its trail, and a move IG did not confirm (owner, 15 November 2026).
STOP_MOVED, STOP_NOT_MOVED = "stop moved", "stop not moved"
# Who asked for a stop move: a strategy's trail, or Johnny's emerging-trend ladder (owner, 21 November 2026).
BY_TRAIL, BY_LADDER = "trail", "emerging ladder"
# Live only: the owner closed it by hand at IG (IG's channel SYSTEM or WEB, not at the stop or take profit; owner,
# 11 November 2026, WEB 23 November 2026). Kept apart from the bot's own exits in the records, the dashboard and the summaries.
CLOSED_BY_OWNER = "closed by owner"
GONE = ("gone at IG", CLOSED_BY_OWNER)
BOT_CLOSES = (HALF_CLOSE, CLOSE, FORCED_CLOSE)
IG_CLOSES = (STOPPED_BY_IG, TAKE_PROFIT_AT_IG)


@dataclass
class Bar:
    """A price bar with both of IG's prices: a 5-minute candle, or a single tick (all four the same)."""
    start: datetime
    buy_open: Decimal
    buy_high: Decimal
    buy_low: Decimal
    buy_close: Decimal
    sell_open: Decimal
    sell_high: Decimal
    sell_low: Decimal
    sell_close: Decimal

    @classmethod
    def of(cls, c: Any) -> "Bar":
        return cls(c.start, c.buy_open, c.buy_high, c.buy_low, c.buy_close, c.sell_open, c.sell_high, c.sell_low,
                   c.sell_close)


@dataclass
class Rejection:
    """A confirmed rejection at a level from the analyser's rejection part: its direction (sell: rejected
    from above) and its trigger price (the chart, sell, price)."""
    direction: str
    price: Decimal
    levels: str = ""


@dataclass
class Decision:
    kind: str
    price: Decimal | None = None        # the closing-side price
    pips: Decimal | None = None         # for this part
    why: str = ""
    part: Decimal = Decimal(1)          # the share of the trade this decision closes
    at: datetime | None = None          # the start of the bar it was made on


@dataclass
class ManagedTrade:
    reference: str
    strategy: str
    direction: str
    opened_at: datetime                 # the start of the bar it opened in
    entry_price: Decimal                # the strategy's entry price (chart, sell price)
    fill: Decimal                       # the price it opened at (IG's level)
    stop_pips: Decimal                  # its stop's distance from the fill
    take_profit_pips: Decimal
    close_at: datetime                  # its scheduled close
    close_why: str
    lock: tuple[int, int] | None
    level_close: bool
    half_close: bool
    news_direction: str | None          # the day's expected news direction (buy or sell), if any
    best: Decimal | None = None         # the best pips reached in earlier bars
    bars: int = 0
    half_done: bool = False
    half_pips: Decimal | None = None
    half_share: Decimal = Decimal("0.5")
    state: str = HOLD
    watching: bool = False
    expected_at_ig: tuple | None = None     # live: IG's stop or take profit expected, not yet confirmed
    retry_close_at: datetime | None = None  # live: a close IG did not confirm is tried again from this time
    close_attempts: int = 0                 # live: closes sent that IG did not confirm
    trail_from: Decimal | None = None       # the bounce: its stop trails once this many pips up
    trail_candles: int = 3                  # ... beyond the last this many finished candles
    stop_level: Decimal | None = None       # its stop at IG as a price once moved (confirmed); None: not moved
    trail_want: Decimal | None = None       # a stop move not yet confirmed by IG
    retry_move_at: datetime | None = None   # live: a stop move IG did not confirm is tried again from this time
    move_attempts: int = 0                  # live: stop moves IG did not confirm (for the level waiting)
    decisions: list[Decision] = field(default_factory=list)
    market_state: str | None = None         # the analyser's state when it opened, as recorded ("emerging trend up")
    want_by: str | None = None              # who asked for the stop move waiting (BY_TRAIL or BY_LADDER)
    want_why: str | None = None             # ... and why
    ladder_asked: Decimal | None = None     # the ladder's level last asked for: asked again only for a new step, or
                                            # after the next finished candle (as the trail's pace)
    stop_moves: list[dict] = field(default_factory=list)   # every confirmed stop move (owner, 21 November 2026)

    @property
    def open(self) -> bool:
        return self.state in (HOLD, HALF_CLOSE)

    @property
    def decision(self) -> str:
        """The trade's decision now (design 4): hold, watching a level, half close (done), or how it closed."""
        return WATCHING if (self.open and self.watching) else self.state

    def total_pips(self) -> Decimal | None:
        """The whole trade's pips once closed (the half close's share included)."""
        last = self.decisions[-1] if self.decisions else None
        if last is None or self.open:
            return None
        if self.half_pips is None:
            return last.pips
        return self.half_pips * self.half_share + last.pips * (1 - self.half_share)


def day_news_direction(settings: Any, pair: str, t: datetime, calendar: list | None = None) -> str | None:
    """The expected news direction of t's UK day (design 2.4): the first big release time of the day with an
    expected direction, as buy (up) or sell (down); None on a day without one."""
    from datetime import datetime as dt, time as tm, timedelta
    from zoneinfo import ZoneInfo
    from news.calendar import time_directions
    tz = settings.hours.timezone
    uk = ZoneInfo(tz) if isinstance(tz, str) else tz
    day = t.astimezone(uk).date()
    start = dt.combine(day, tm(0, 0), tzinfo=uk).astimezone(UTC)
    end = dt.combine(day + timedelta(days=1), tm(0, 0), tzinfo=uk).astimezone(UTC)
    for td in time_directions(settings, pair, start, end, calendar):
        if td.direction in ("up", "down"):
            return BUY if td.direction == "up" else SELL
    return None


def plan(settings: Any, reference: str, strategy: str, direction: str, opened_at: datetime, entry_price: Decimal,
         fill: Decimal, stop_pips: Decimal, calendar: list | None = None, trend_day: str | None = None,
         market_state: str | None = None) -> ManagedTrade:
    """A trade's exits, worked out when it opens. `market_state`: the analyser's state recorded on the trade when it
    opened (e.g. "emerging trend down"), for the emerging-trend ladder."""
    from news.calendar import big_news_windows
    from datetime import timedelta
    pair = settings.market.pair
    tp = take_profit_pips(settings, strategy, opened_at, pair, calendar, direction=direction, trend_day=trend_day)
    close_at = forced_close_at(settings, strategy, opened_at)
    why = f"{settings.hours.close_all_trades_at:%H:%M} UK close"
    if closed_before_big_news(strategy):
        windows = big_news_windows(settings, pair, opened_at, close_at + timedelta(minutes=1), calendar)
        news = [w.close_open_trades_at for w in windows if w.close_open_trades_at > opened_at]
        if news and min(news) < close_at:
            close_at, why = min(news), "closed 15 minutes before big news"
    return ManagedTrade(reference, strategy, direction, opened_at, Decimal(entry_price), Decimal(fill), Decimal(stop_pips),
                        Decimal(tp), close_at, why, profit_lock(settings, strategy), closed_on_level_rejection(strategy),
                        strategy == RANGE_TRADE, day_news_direction(settings, pair, opened_at, calendar),
                        trail_from=trail_from(settings, strategy), trail_candles=_trail_candles(settings, strategy),
                        market_state=market_state)


def trail_from(settings: Any, strategy: str) -> Decimal | None:
    """The pips in profit after which a trade's stop trails behind the last candles (strategies.common.trail):
    bounce.trail_from_pips for the Bollinger bounce (owner, 15 November 2026: 12), and each session strategy's own
    trail_from_pips (owner, 16 November 2026: 12); None for every other strategy (the first build's bounce,
    Bollinger bounce 5m, has no trail, as on 9 November 2026)."""
    got = trail(settings, strategy)
    return None if got is None else got[0]


def _trail_candles(settings: Any, strategy: str) -> int:
    """How many finished candles the trail looks back over (3); the bounce's for a strategy without a trail."""
    got = trail(settings, strategy)
    return int(settings.bounce.trail_candles) if got is None else got[1]


def ladder_applies(settings: Any, t: ManagedTrade) -> bool:
    """Johnny's emerging-trend ladder runs this trade: the switch is on and the trade opened in "emerging trend"."""
    return bool(getattr(settings.switches, "emerging_ladder", False)) and (t.market_state or "").startswith(EMERGING)


def ladder_stop_pips(settings: Any, t: ManagedTrade) -> Decimal | None:
    """The ladder's stop, in pips up from the fill, for the best pips reached so far: second_stop_pips once
    second_from_pips up, first_stop_pips once first_from_pips up, otherwise None."""
    if t.best is None or not ladder_applies(settings, t):
        return None
    el = settings.emerging_ladder
    if t.best >= Decimal(el.second_from_pips):
        return Decimal(el.second_stop_pips)
    if t.best >= Decimal(el.first_from_pips):
        return Decimal(el.first_stop_pips)
    return None


def _closer(direction: str, a: Decimal, b: Decimal) -> bool:
    """Stop level a is tighter (closer to the price, in the trade's favour) than b."""
    return a < b if direction == SELL else a > b


def step(settings: Any, t: ManagedTrade, bar: Bar, band: tuple[Decimal, Decimal] | None = None,
         rejections: list[Rejection] = ()) -> list[Decision]:
    """One bar for one open trade: the decisions it brings (empty: hold). `band` is the (upper, lower)
    Bollinger band at the last finished candle; `rejections` the analyser's confirmed rejections at levels
    that triggered in this bar."""
    if not t.open:
        return []
    ppp = Decimal(settings.market.points_per_pip)
    sell = t.direction == SELL
    side = "buy" if sell else "sell"                                  # the price it closes on
    g = lambda name: Decimal(getattr(bar, f"{side}_{name}"))          # noqa: E731
    pips = lambda v: ((t.fill - v) if sell else (v - t.fill)) / ppp    # noqa: E731
    first = t.bars == 0
    t.bars += 1
    out: list[Decision] = []

    def finish(kind: str, price: Decimal, why: str) -> list[Decision]:
        d = Decision(kind, price, pips(price), why, (1 - t.half_share) if t.half_done else Decimal(1), bar.start)
        t.decisions.append(d)
        t.state = kind
        out.append(d)
        return out

    if not first and bar.start >= t.close_at:                          # 1. the scheduled close
        return finish(FORCED_CLOSE, g("open"), t.close_why)
    level = -t.stop_pips                                               # 2. the stop at IG, or the lock
    if t.stop_level is not None:                                       # the bounce's stop moved by its trail
        level = max(level, pips(t.stop_level))
    locked = t.lock is not None and t.best is not None and t.best >= t.lock[0]
    if locked:
        level = max(level, Decimal(t.lock[1]))
    worst = pips(g("high") if sell else g("low"))
    best = pips(g("low") if sell else g("high"))
    hit = worst <= level
    if first:
        opened_past = (bar.sell_open <= t.entry_price) if sell else (bar.sell_open >= t.entry_price)
        hit = hit and (opened_past or pips(g("close")) <= -t.stop_pips)
    if hit:
        at_open = pips(g("open"))
        fill_pips = at_open if (not first and at_open <= level) else level
        price = (t.fill - fill_pips * ppp) if sell else (t.fill + fill_pips * ppp)
        if locked and level > 0:
            return finish(CLOSE, price, f"the profit lock: back to {t.lock[1]} pips up after {t.lock[0]} up")
        return finish(STOPPED_BY_IG, price, f"the stop at IG (trailed to {t.stop_level})"
                      if t.stop_level is not None and level == pips(t.stop_level) else "the stop at IG")
    if t.half_close and not t.half_done and band is not None:          # 3. the range trade's half close
        upper, lower = (Decimal(x) for x in band)
        reached = (bar.sell_low <= lower) if sell else (bar.sell_high >= upper)
        if reached:
            b = lower if sell else upper
            price = b + (bar.buy_open - bar.sell_open) if sell else b   # the band is a sell price
            if first and ((bar.sell_open <= lower) if sell else (bar.sell_open >= upper)):
                price = g("open")
            share = Decimal(settings.range_trade.close_percent_at_opposite_band) / 100
            d = Decision(HALF_CLOSE, price, pips(price), "the opposite Bollinger band", share, bar.start)
            t.half_done, t.half_pips, t.half_share, t.state = True, d.pips, share, HALF_CLOSE
            t.decisions.append(d)
            out.append(d)
    if best >= t.take_profit_pips:                                     # 4. the take profit at IG
        price = (t.fill - t.take_profit_pips * ppp) if sell else (t.fill + t.take_profit_pips * ppp)
        return finish(TAKE_PROFIT_AT_IG, price, f"the take profit at IG ({t.take_profit_pips} pips)")
    if t.level_close and not first and t.news_direction != t.direction:   # 5. a rejection at a level against it
        against = BUY if sell else SELL
        got = [r for r in rejections if r.direction == against]
        if got:
            r = got[0]
            price = r.price + (bar.buy_open - bar.sell_open) if sell else r.price
            return finish(CLOSE, price, f"a confirmed rejection at a level: {r.levels}")
    t.best = best if t.best is None else max(t.best, best)
    return out


class TradeManager:
    """Keeps the open trades, takes each bar, and tells the order sender to close (in full or by half).
    The stop and take profit are IG's: recorded, never sent."""

    def __init__(self, settings: Any, sender: Any, *, now: Any = lambda: datetime.now(UTC), ig_confirms: bool = False):
        """`ig_confirms`: live trades, where IG's stop and take profit close the trade only once the order sender
        has confirmed it with IG (otherwise, in a replay or for paper trades, the manager's decision closes it)."""
        self.s, self.sender, self.now, self.ig_confirms = settings, sender, now, ig_confirms
        self.trades: dict[str, ManagedTrade] = {}
        self.folder = Path(settings.trade_manager.folder) / settings.market.pair
        self.journal = self.folder / "decisions.jsonl"
        self.state_file = self.folder / "open_trades.json"
        self._saved: dict = {}
        self.recent: list[Bar] = []                     # the last finished 5-minute candles (the bounce's trail)
        self.on_decision = None                         # the records (trading/engine.py): (trade, decision, answer)

    def _record(self, t: ManagedTrade, d: Decision, sent: Any = None) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        row = {"time_utc": self.now().strftime("%Y-%m-%dT%H:%M:%SZ"), "reference": t.reference, "strategy": t.strategy,
               "decision": d.kind, "price": str(d.price) if d.price is not None else None,
               "pips": str(d.pips) if d.pips is not None else None, "part": str(d.part), "why": d.why}
        if sent is not None:
            row["order_sender"] = getattr(sent, "what", str(sent))
        with self.journal.open("a") as f:
            f.write(json.dumps(row) + "\n")
        if self.on_decision is not None:
            self.on_decision(t, d, sent)

    def add(self, t: ManagedTrade) -> None:
        self.trades[t.reference] = t
        self.save_state()

    @staticmethod
    def _snapshot(t: ManagedTrade) -> dict:
        return {"best": None if t.best is None else str(t.best), "bars": t.bars, "half_done": t.half_done,
                "half_pips": None if t.half_pips is None else str(t.half_pips), "half_share": str(t.half_share),
                "watching": t.watching, "opened_at": t.opened_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "stop_moves": list(t.stop_moves)}

    def save_state(self) -> None:
        """Save each open trade's best pips so far, half close and watching (only when something changed)."""
        now = {ref: self._snapshot(t) for ref, t in self.trades.items() if t.open}
        if now == self._saved:
            return
        self.folder.mkdir(parents=True, exist_ok=True)
        tmp = self.state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(now, indent=1) + "\n")
        tmp.replace(self.state_file)
        self._saved = now

    def load_state(self) -> dict:
        """What was saved for the open trades (read once at start-up, before any trade is added)."""
        try:
            return json.loads(self.state_file.read_text())
        except (FileNotFoundError, ValueError):
            return {}

    def restore(self, t: ManagedTrade, saved_all: dict | None = None) -> bool:
        """After a restart: give a trade back its saved best pips, half close and watching. False if none saved."""
        saved = (saved_all if saved_all is not None else self.load_state()).get(t.reference)
        if not saved:
            return False
        t.best = None if saved["best"] is None else Decimal(saved["best"])
        t.bars = max(int(saved["bars"]), 1)
        t.half_done = bool(saved["half_done"])
        t.half_pips = None if saved["half_pips"] is None else Decimal(saved["half_pips"])
        t.half_share = Decimal(saved["half_share"])
        t.watching = bool(saved["watching"])
        t.stop_moves = list(saved.get("stop_moves") or [])
        if t.half_done and t.state == HOLD:
            t.state = HALF_CLOSE
        return True

    def on_bar(self, bar: Bar, band: tuple[Decimal, Decimal] | None = None, rejections: list[Rejection] = (),
               watching: set[str] | frozenset = frozenset(), only: list[str] | None = None,
               finished: bool = False) -> list[tuple[ManagedTrade, Decision]]:
        """One bar for every open trade (or only the references given). `watching`: the directions (buy, sell) of
        the analyser's rejection setups running at levels that count, after this bar. `finished`: the bar is a
        finished 5-minute candle (not a live price): after it, the bounce's trail is moved."""
        done = []
        for t in [t for t in self.trades.values() if t.open and (only is None or t.reference in only)]:
            self._move_stop(t)
            before = self._before(t)
            kept: list[Decision] = []                   # bot closes IG confirmed in this bar (a half close)
            for d in step(self.s, t, bar, band, rejections):
                sent = None
                if d.kind in BOT_CLOSES and self.ig_confirms and t.retry_close_at is not None \
                        and self.now() < t.retry_close_at:
                    self._put_back(t, before, kept)     # a close IG did not confirm: not tried again yet
                    break
                if d.kind in BOT_CLOSES:
                    sent = self.sender.close(t.reference, half=d.kind == HALF_CLOSE, why=d.why, price=d.price)
                    if self.ig_confirms and getattr(sent, "what", "") in GONE:
                        self._put_back(t, before, kept)
                        self._closed_at_ig(t, sent)
                        done.append((t, t.decisions[-1]))
                        break
                    if self.ig_confirms and not getattr(sent, "ok", False):
                        # never closed unless IG confirms it: the trade stays as it was, the close is tried again
                        self._put_back(t, before, kept)
                        t.close_attempts += 1
                        t.retry_close_at = self.now() + timedelta(seconds=self.s.orders.close_retry_seconds)
                        why = "; ".join(getattr(sent, "reasons", None) or [getattr(sent, "what", "no answer")])
                        self._record(t, Decision(CLOSE_NOT_DONE, d.price, None,
                                                 f"{d.kind} ({d.why}) not done: IG did not confirm it ({why}); the trade "
                                                 f"stays open and the close is tried again in "
                                                 f"{self.s.orders.close_retry_seconds} seconds", d.part), sent)
                        break
                    t.retry_close_at = None
                    if self.ig_confirms:                    # IG's confirmed price and time, not the bot's own
                        d = self._at_igs_level(t, d, sent)
                        if d.kind == HALF_CLOSE:
                            t.half_pips = d.pips
                    if d.kind == HALF_CLOSE:
                        kept.append(d)
                elif d.kind in IG_CLOSES and hasattr(self.sender, "closed_at_ig"):
                    sent = self.sender.closed_at_ig(t.reference, d.kind, d.price)
                    if self.ig_confirms and getattr(sent, "what", "") in GONE:
                        self._put_back(t, before, kept)     # not IG's stop or limit: the owner closed it
                        self._closed_at_ig(t, sent)
                        done.append((t, t.decisions[-1]))
                        break
                    if self.ig_confirms and getattr(sent, "ok", False):
                        d = self._at_igs_level(t, d, sent)
                    if self.ig_confirms and not getattr(sent, "ok", False):
                        t.expected_at_ig = (d.kind, d.price, d)
                        t.state, t.decisions = HOLD if not t.half_done else HALF_CLOSE, t.decisions[:-1]
                        d = Decision(d.kind, d.price, d.pips, d.why + " (expected; IG has not closed it yet)", d.part)
                self._record(t, d, sent)
                done.append((t, d))
            if t.open:
                self._ladder(t)                         # Johnny's emerging-trend ladder, from the best so far
            if t.open and t.level_close:
                against = BUY if t.direction == SELL else SELL
                now_watching = against in watching and t.news_direction != t.direction
                if now_watching != t.watching:
                    t.watching = now_watching
                    self._record(t, Decision(WATCHING if now_watching else HOLD, why="the analyser's rejection setup "
                                             + ("running against it at a level" if now_watching else "is over")))
        if finished:
            self.candle_finished(bar)
        self.save_state()
        return done

    def candle_finished(self, bar: Bar) -> None:
        """A finished 5-minute candle: kept as one of the last candles, then the bounce's trail (every open trade
        with one, whether or not it was run on this bar)."""
        if not self.recent or bar.start > self.recent[-1].start:
            self.recent.append(bar)
            del self.recent[:-50]
        for t in [t for t in self.trades.values() if t.open]:
            t.ladder_asked = None                       # the ladder's level is worked out again now, as the trail's
        for t in [t for t in self.trades.values() if t.open and t.trail_from is not None]:
            self._trail(t)
        for t in [t for t in self.trades.values() if t.open]:
            self._ladder(t)

    def _ladder_level(self, t: ManagedTrade) -> Decimal | None:
        """The ladder's stop as a price (IG's level) for the best so far, or None."""
        pips = ladder_stop_pips(self.s, t)
        if pips is None:
            return None
        ppp = Decimal(self.s.market.points_per_pip)
        return (t.fill - pips * ppp) if t.direction == SELL else (t.fill + pips * ppp)

    def _ladder(self, t: ManagedTrade) -> None:
        """Johnny's emerging-trend ladder (owner, 21 November 2026): once the trade is first_from_pips up its stop
        moves to first_stop_pips up, once second_from_pips up to second_stop_pips up. Only to a level tighter than the
        stop IG holds (never backwards; a tighter trail or earlier move is kept) and tighter than a move still
        waiting; through _move_stop, as the trail."""
        if not t.open:
            return
        level = self._ladder_level(t)
        if level is None or level == t.ladder_asked:
            return                                      # nothing yet, or this level already asked for since the candle
        ppp = Decimal(self.s.market.points_per_pip)
        sell = t.direction == SELL
        now = t.stop_level if t.stop_level is not None else ((t.fill + t.stop_pips * ppp) if sell else (t.fill - t.stop_pips * ppp))
        if not _closer(t.direction, level, now):
            return
        if t.trail_want is not None and not _closer(t.direction, level, t.trail_want):
            return                                      # a move as tight or tighter is already waiting
        el = self.s.emerging_ladder
        second = t.best >= Decimal(el.second_from_pips)
        rule = (f"+{el.second_from_pips} reached: stop to +{el.second_stop_pips}" if second
                else f"+{el.first_from_pips} reached: stop to +{el.first_stop_pips}")
        pips = ladder_stop_pips(self.s, t)
        t.trail_want, t.want_by, t.ladder_asked = level, BY_LADDER, level
        t.want_why = (f"{t.best} pips up at best, opened in {t.market_state}: the emerging-trend ladder ({rule}) moves "
                      f"the stop to {level} ({pips} pips up)")
        t.retry_move_at, t.move_attempts = None, 0
        self._move_stop(t)

    def _trail(self, t: ManagedTrade) -> None:
        """The Bollinger bounce's trail (owner, 15 November 2026): once the trade has been trail_from pips up, its
        stop goes to a tenth of a pip beyond the last trail_candles finished candles (a sell: above their highest buy
        price; a buy: below their lowest sell price), only ever closer."""
        if t.best is None or t.best < t.trail_from or len(self.recent) < t.trail_candles:
            return
        ppp = Decimal(self.s.market.points_per_pip)
        last = self.recent[-t.trail_candles:]
        sell = t.direction == SELL
        want = (max(b.buy_high for b in last) + ppp / 10) if sell else (min(b.sell_low for b in last) - ppp / 10)
        # "Only ever closer" than the stop IG actually holds, never than a move IG refused (17 November 2026: a
        # refused 13181.6 blocked every newer level while price rose, and the same level was sent 31 times).
        now = t.stop_level
        if now is None:
            now = (t.fill + t.stop_pips * ppp) if sell else (t.fill - t.stop_pips * ppp)
        lad = self._ladder_level(t)
        if lad is not None and not _closer(t.direction, want, lad):
            return                                  # the emerging-trend ladder's stop is as tight or tighter: it wins
        if ((want < now) if sell else (want > now)) and want != t.trail_want:
            t.trail_want = want                     # a newer level replaces one still waiting: a fresh set of attempts
            t.want_by, t.want_why = BY_TRAIL, None
            t.retry_move_at = None
            t.move_attempts = 0
            self._move_stop(t)

    def _move_stop(self, t: ManagedTrade) -> None:
        """A stop move the trail asked for: the order sender moves the stop at IG (to the nearest level IG allows, if
        need be). It counts only once IG confirms it; otherwise the old stop stays and the move is tried again after
        orders.close_retry_seconds, up to orders.stop_move_attempts in all, then given up until the next finished
        candle with one alert (live; in a replay or a paper trade the move is recorded at once)."""
        want = t.trail_want
        if want is None:
            return
        if self.ig_confirms and t.retry_move_at is not None and self.now() < t.retry_move_at:
            return
        by = t.want_by or BY_TRAIL
        why = t.want_why or (f"{t.best} pips up at best (the trail from {t.trail_from}): the stop moves to {want}, "
                             f"beyond the last {t.trail_candles} candles")
        sent = self.sender.move_stop(t.reference, want, why=why) if hasattr(self.sender, "move_stop") else None
        if sent is None or getattr(sent, "ok", False) or not self.ig_confirms:
            # the order sender may have sent the nearest level IG allows instead (owner, 17 November 2026)
            level = getattr(sent, "level", None) or want
            if level != want:
                why += f"; sent as {level}, the nearest level IG allowed at that moment"
            if t.move_attempts and hasattr(self.sender, "alerts"):
                self.sender.alerts.info(f"AutoBot: the stop of {t.strategy} {t.direction} trade {t.reference} is now at "
                                        f"{level} at IG, after {t.move_attempts} move(s) IG did not confirm.")
            t.stop_level, t.trail_want, t.retry_move_at, t.move_attempts = level, None, None, 0
            t.want_by = t.want_why = None
            ppp = Decimal(self.s.market.points_per_pip)
            pips = ((t.fill - level) if t.direction == SELL else (level - t.fill)) / ppp
            t.stop_moves.append({"time_utc": self.now().strftime("%Y-%m-%dT%H:%M:%SZ"), "level": str(level),
                                 "pips": str(pips), "by": by, "why": why})
            self._record(t, Decision(STOP_MOVED, level, pips, why), sent)
            return
        t.move_attempts += 1
        attempts = int(self.s.orders.stop_move_attempts)
        reason = "; ".join(getattr(sent, "reasons", None) or [getattr(sent, "what", "no answer")])
        tried = getattr(sent, "level", None) or want
        if t.move_attempts >= attempts:
            # owner, 17 November 2026: give up on this level after orders.stop_move_attempts (3); the stop stays where
            # IG has it and the trail is worked out again after the next finished candle. One alert, not one a try.
            stays = t.stop_level if t.stop_level is not None else "its stop when it opened"
            self._record(t, Decision(STOP_NOT_MOVED, tried, None,
                                     f"{why}: not done, IG did not confirm it ({reason}); gave up after {attempts} "
                                     f"attempts: the stop stays at {stays} and the {by} is worked out again after "
                                     f"the next finished candle"), sent)
            alerts = getattr(self.sender, "alerts", None)
            if alerts is not None and hasattr(alerts, "problem"):
                alerts.problem(f"stop-move-gave-up-{t.reference}",
                               f"IG did not move the stop of {t.strategy} {t.direction} trade {t.reference} to {tried} "
                               f"(the {by}) in {attempts} attempts: {reason}. The stop stays at {stays} at IG and in "
                               f"the bot's records; the {by} is worked out again after the next finished candle.")
            t.trail_want, t.retry_move_at, t.move_attempts = None, None, 0
            t.want_by = t.want_why = None           # the ladder, as the trail: worked out again after the next candle
            return
        t.retry_move_at = self.now() + timedelta(seconds=self.s.orders.close_retry_seconds)
        self._record(t, Decision(STOP_NOT_MOVED, tried, None,
                                 f"{why}: not done, IG did not confirm it ({reason}); attempt {t.move_attempts} of "
                                 f"{attempts}: the old stop stays and the move is tried again in "
                                 f"{self.s.orders.close_retry_seconds} seconds"), sent)

    _KEEP = ("state", "best", "bars", "half_done", "half_pips", "half_share", "expected_at_ig")

    @classmethod
    def _before(cls, t: ManagedTrade) -> dict:
        return {k: getattr(t, k) for k in cls._KEEP} | {"decisions": len(t.decisions)}

    @classmethod
    def _put_back(cls, t: ManagedTrade, before: dict, kept: list[Decision]) -> None:
        """The trade as it was before this bar, plus the half close IG confirmed in it (if any)."""
        for k in cls._KEEP:
            setattr(t, k, before[k])
        del t.decisions[before["decisions"]:]
        for d in kept:
            t.half_done, t.half_pips, t.half_share, t.state = True, d.pips, d.part, HALF_CLOSE
            t.decisions.append(d)

    def _closed_at_ig(self, t: ManagedTrade, found: Any) -> None:
        """IG closed the position without the bot (the order sender's "gone at IG"): finished at IG's own level
        and time when IG's activity gives them."""
        ppp = Decimal(self.s.market.points_per_pip)
        level = getattr(found, "level", None)
        pips = None if level is None else (((t.fill - level) if t.direction == SELL else (level - t.fill)) / ppp)
        why = "; ".join(getattr(found, "reasons", None) or []) or "closed at IG without the bot"
        kind = CLOSED_BY_OWNER if getattr(found, "what", "") == CLOSED_BY_OWNER else CLOSED_AT_IG
        d = Decision(kind, level, pips, why, (1 - t.half_share) if t.half_done else Decimal(1),
                     getattr(found, "closed_utc", None) or self.now())
        t.decisions.append(d)
        t.state = kind
        self._record(t, d, found)
        self.save_state()

    def gone_at_ig(self, found: Any) -> bool:
        """The order sender found this trade gone at IG (regular check or start-up): finish it here too."""
        t = self.trades.get(getattr(found, "reference", ""))
        if t is None or not t.open:
            return False
        self._closed_at_ig(t, found)
        return True

    def _at_igs_level(self, t: ManagedTrade, d: Decision, sent: Any) -> Decision:
        """Live: IG's own close level and time (from IG's activity, via the order sender) replace the manager's."""
        level, when = getattr(sent, "level", None), getattr(sent, "closed_utc", None)
        if not isinstance(level, Decimal) or (level == d.price and (when is None or when == d.at)):
            return d
        ppp = Decimal(self.s.market.points_per_pip)
        pips = ((t.fill - level) if t.direction == SELL else (level - t.fill)) / ppp
        new = Decision(d.kind, level, pips, d.why + (" (IG's level)" if level != d.price else ""), d.part, when or d.at)
        t.decisions[-1] = new
        return new

    def closed_at_ig(self, reference: str, found: Any = None) -> None:
        """The order sender found the trade closed at IG (its stop or take profit): stop managing it. `found`: the
        order sender's answer; IG's own level and time in it replace the price and time the trade manager expected
        (owner, 27 November 2026: the 26 November 06:01 bounce was recorded at the bot's 09:20 reading, 13108.4,
        instead of IG's fill at 09:35:01, 13108.9)."""
        t = self.trades.get(reference)
        if t is not None and t.open:
            expected = getattr(t, "expected_at_ig", None)
            d = expected[2] if expected else Decision(STOPPED_BY_IG, why="closed at IG (found by the order sender)")
            t.decisions.append(d)
            if found is not None:
                d = self._at_igs_level(t, d, found)
            t.state = d.kind
            self._record(t, d)
            self.save_state()
