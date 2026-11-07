"""Turns what the price stream sends into ticks and stored candles, and runs
the store checks.

* Every tick is counted and the latest one kept (buy and sell separately).
  Ticks are not stored on disk. IG's BID is the sell price and its OFR the
  buy price.
* IG sends only the price that changed: a blank BID or OFR means "unchanged".
  The blank side is filled with the last value received ON THIS CONNECTION,
  and only once both BID and OFR have been received at least once on it.
  Every new connection (first connect, reconnect, re-login) starts fresh, so
  a value from before a reconnect is never carried forward. A value that is
  present but unreadable is not used, and that side is unknown again until IG
  sends a fresh one.
* IG's 5-minute candle is stored only once IG marks it finished (CONS_END = 1).
  An unfinished candle is never stored.
* After each new 5-minute candle: the new candle is checked, bigger candles
  that are due are built from the stored 5-minute candles (and checked), and
  free disk space is checked.
* At start-up: leftover temporary files are removed, old files compressed,
  every stored candle checked, the newest candle and its age reported, and
  any gap since it recorded. The gap is NOT filled.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Callable

from config.pairs import check_same_pair
from prices.builder import build_due
from prices.calendar import Boundaries, MarketHours, floor_5m
from prices.checks import CheckResult, Gap, check_new_candle, check_store, missing_after
from prices.model import FIVE_MIN, Candle, Tick, plain, price, uk, uk_short, utc_ms
from prices.store import CandleStore

log = logging.getLogger("autobot.prices")


class _PairLog(logging.LoggerAdapter):
    def __init__(self, logger: logging.Logger, pair: str):
        super().__init__(logger, {})
        self.pair = pair

    def process(self, msg, kwargs):
        return f"[{self.pair}] {msg}", kwargs


@dataclass
class StartReport:
    newest: Candle | None
    age: timedelta | None
    gaps_since: list[Gap]
    check: CheckResult
    built: list[Candle]
    lines: list[str] = field(default_factory=list)


class PriceFeed:
    def __init__(self, settings: Any, store: CandleStore, *,
                 now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
                 disk_check: Callable[[], Any] = lambda: None,
                 after_new_candle: Callable[[datetime], None] = lambda now: None):
        check_same_pair(settings, store)
        self.settings = settings
        self.pair = settings.market.pair
        self.log = _PairLog(log, self.pair)       # every log line starts with the pair
        # Called after start-up and after each new 5-minute candle is stored
        # (and any bigger candles built): the levels part updates its list.
        self.after_new_candle = after_new_candle
        self.store = store
        self.hours = MarketHours(settings.market_hours)
        self.b = Boundaries(settings.candles, self.hours)
        self.now = now
        self.disk_check = disk_check
        self.wait_late = settings.candles.wait_for_late_candle_seconds
        self.warnings: list[str] = []
        store.warn = self.warn

        self.ticks = 0
        self.first_tick: Tick | None = None
        self.last_tick: Tick | None = None
        self.bad_ticks = 0                    # ticks skipped, for any reason
        self.carried_forward = 0              # ticks that used a carried-forward price
        self.connections = 0                  # stream connections seen by the feed
        # The last BID (sell) and OFR (buy) received on the current connection.
        self._sell: Decimal | None = None
        self._buy: Decimal | None = None
        self.stored: list[Candle] = []        # 5-minute candles stored by this run
        self.built: list[Candle] = []         # bigger candles built by this run
        self.unfinished_seen = 0
        self.check_results: list[CheckResult] = []
        self._compressed_on: object = None

    def warn(self, message: str) -> None:
        self.warnings.append(message)
        self.log.warning(message)

    # ---- market hours, for the stream's quiet check ----------------------------

    def market_open_since(self, now: datetime) -> datetime | None:
        if not self.hours.is_open(now):
            return None
        return self.hours.session(now)[0]

    # ---- start-up ---------------------------------------------------------------

    def start_up(self) -> StartReport:
        now = self.now()
        self.store.remove_leftover_temp_files()
        self._compress(now)
        check = check_store(self.store, self.b)
        self._report_check(check, "store check at start-up")
        newest = self.store.newest("5m")
        lines = [f"Store check at start-up: {sum(check.candles.values())} candle(s) checked "
                 f"({', '.join(f'{tf} {n}' for tf, n in check.candles.items())}); "
                 f"{len(check.problems)} problem(s); {len(check.new_gaps)} new gap(s); "
                 f"{len(check.gaps) - len(check.new_gaps)} gap(s) already recorded."]
        gaps_since: list[Gap] = []
        age = None
        if newest is None:
            lines.append("Newest 5-minute candle in the store: none (the store is empty).")
        else:
            age = now - newest.end
            lines.append(f"Newest 5-minute candle in the store: {uk_short(newest.start)} to "
                         f"{uk_short(newest.end)}, finished {_age(age)} ago.")
            gaps_since = missing_after("5m", newest.end, floor_5m(now), self.b)
            for g in gaps_since:
                self.warn(f"{g.describe()}, since the last stored candle (the bot was not running). "
                          "Recorded; not filled.")
                self.store.record_gap("5m", g.start, g.end, g.missing, now, "since the last candle, at start-up")
            if not gaps_since:
                lines.append("No gap since the last stored candle.")
            else:
                lines.append(f"Gap since the last stored candle: {sum(g.missing for g in gaps_since)} "
                             "five-minute candle(s) during market hours, recorded and not filled.")
        built = build_due(self.store, self.b, now, self.wait_late, self.warn)
        for c in built:
            self._check_new(c)
        self.built.extend(built)
        self.disk_check()
        for line in lines:
            self.log.info(line)
        self.after_new_candle(now)
        return StartReport(newest, age, gaps_since, check, built, lines)

    # ---- from the stream ---------------------------------------------------------

    def new_connection(self) -> None:
        """Called by the stream each time it opens a new connection (first
        connect, reconnect or re-login). Forgets the last prices, so nothing
        from before the reconnect is ever carried forward."""
        self.connections += 1
        self._sell = None
        self._buy = None

    def on_tick(self, fields: dict) -> None:
        problems: list[str] = []
        carried = False
        # BID is the sell price, OFR the buy price.
        for name, side in (("BID", "_sell"), ("OFR", "_buy")):
            raw = fields.get(name)
            if raw is None or str(raw).strip() == "":
                if getattr(self, side) is None:
                    problems.append(f"{name} blank and not yet received on this connection")
                else:
                    carried = True
                continue
            try:
                setattr(self, side, price(raw))
            except ValueError as e:
                setattr(self, side, None)   # the real price is unknown until IG sends a fresh one
                problems.append(f"{name} {e}")
        try:
            time = utc_ms(fields["UTM"])
        except (ValueError, TypeError, KeyError, OverflowError, OSError):
            problems.append("UTM missing or unreadable")
        if problems:
            self.bad_ticks += 1
            # Show exactly what IG sent (prices and time are not secret), so the
            # reason can be found. Nothing is guessed.
            self.log.info("Tick skipped (%s). IG sent: BID (sell)=%r OFR (buy)=%r UTM=%r",
                     "; ".join(problems), fields.get("BID"), fields.get("OFR"), fields.get("UTM"))
            return
        tick = Tick(time, buy=self._buy, sell=self._sell)
        if carried:
            self.carried_forward += 1
        self.ticks += 1
        if self.first_tick is None:
            self.first_tick = tick
        self.last_tick = tick

    def on_candle(self, fields: dict) -> None:
        if str(fields.get("CONS_END") or "").strip() != "1":
            self.unfinished_seen += 1
            return  # IG has not finished this candle: never stored
        try:
            start = utc_ms(fields["UTM"])
            c = Candle("5m", start, start + FIVE_MIN,
                       buy_open=price(fields.get("OFR_OPEN")), buy_high=price(fields.get("OFR_HIGH")),
                       buy_low=price(fields.get("OFR_LOW")), buy_close=price(fields.get("OFR_CLOSE")),
                       sell_open=price(fields.get("BID_OPEN")), sell_high=price(fields.get("BID_HIGH")),
                       sell_low=price(fields.get("BID_LOW")), sell_close=price(fields.get("BID_CLOSE")))
        except (ValueError, TypeError, KeyError) as e:
            self.warn(f"A finished 5-minute candle from IG had a missing or unreadable value ({e}); "
                      "not stored.")
            return
        if start != floor_5m(start):
            self.warn(f"A finished 5-minute candle from IG starts at {uk(start)}, which is not on a "
                      "5-minute mark; not stored.")
            return
        self.add_five_minute(c)

    def add_five_minute(self, c: Candle) -> str:
        if not self.hours.is_open(c.start):
            self.warn(f"IG sent a finished 5-minute candle at {uk_short(c.start)}, outside the market hours "
                      "in the settings file. Stored, but please check [market_hours].")
        result = self.store.add(c)
        if result != "stored":
            return result
        self.stored.append(c)
        self.log.info("Stored %s", c.describe())
        self._check_new(c)
        now = self.now()
        built = build_due(self.store, self.b, now, self.wait_late, self.warn, also_for=c.start)
        for bc in built:
            self.log.info("Built %s (from %d of %d 5-minute candles)", bc.describe(), bc.parts, bc.expected_parts)
            self._check_new(bc)
        self.built.extend(built)
        self._compress(now)
        self.disk_check()
        self.after_new_candle(now)
        return result

    # ---- checks ---------------------------------------------------------------

    def _check_new(self, c: Candle) -> None:
        self._report_check(check_new_candle(self.store, self.b, c), "store check after a new candle")

    def _report_check(self, result: CheckResult, how: str) -> None:
        self.check_results.append(result)
        for p in result.problems:
            self.warn(p)
        now = self.now()
        for g in result.gaps:
            if g.known:
                self.log.info("%s (already recorded).", g.describe())
            else:
                self.warn(g.describe() + ".")
                self.store.record_gap(g.timeframe, g.start, g.end, g.missing, now, how)

    def _compress(self, now: datetime) -> None:
        day = now.date()
        if self._compressed_on == day:
            return
        self._compressed_on = day
        n = self.store.compress_old(now)
        if n:
            self.log.info("Compressed %d candle file(s) older than %d days.", n, self.store.compress_after_days)

    def describe_last_tick(self) -> str:
        t = self.last_tick
        return "none" if t is None else f"{uk(t.time)}: buy {plain(t.buy)} sell {plain(t.sell)}"


def _age(d: timedelta) -> str:
    s = int(d.total_seconds())
    if s < 0:
        return "0 minutes"
    days, s = divmod(s, 86400)
    h, s = divmod(s, 3600)
    m = s // 60
    parts = ([f"{days} day(s)"] if days else []) + ([f"{h} hour(s)"] if h else []) + [f"{m} minute(s)"]
    return " ".join(parts)
