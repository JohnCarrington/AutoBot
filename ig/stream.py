"""IG's live price stream (Lightstreamer), with the reconnect rules.

What it subscribes to, for EACH pair switched on (its epic in settings
[pairs.<PAIR>] epic), all on one connection with one IG login:
  CHART:<epic>:TICK      every tick: BID (sell), OFR (buy), UTM (time)
  CHART:<epic>:5MINUTE   IG's own 5-minute candle: buy (OFR_*) and sell (BID_*)
                         open/high/low/close, UTM (candle start) and CONS_END
                         (1 when IG has finished the candle)
Nothing else. The stream has no historical prices, and the bot never asks
IG's REST API for them either (ig.client refuses any /prices call).

The rules:
  * It connects to the streaming address IG gave at login, as the bot's
    account, with the current session tokens.
  * If the stream drops, it waits and reconnects. The waits go up
    (stream.reconnect_waits_seconds: 5, 10, 20, ... 300 seconds) and the
    last wait is repeated after that, so it never reconnects in a fast loop.
    The library's own automatic retrying is cut off: this code decides.
  * If IG refuses the stream's login (Lightstreamer error 1), it makes ONE
    controlled re-login through ig.client (the Stage 3 rule), then connects
    again. If IG refuses again before the stream has been healthy for
    stream.healthy_after_minutes, the bot stops (exit code 78).
  * If no prices arrive for stream.no_prices_warning_seconds while the market
    is open, it writes a warning (once), and says when prices come back.

Callers get prices through on_tick(epic, fields) and on_candle(epic, fields),
as plain dictionaries of what IG sent, with the epic they came from (so each
pair's prices go to that pair's store only). The prices part turns them into ticks and candles.
on_new_connection() is called each time a new connection is opened (first
connect, reconnect, re-login), before anything from it arrives: IG sends only
the tick price that changed, so the prices part starts fresh on each one.
"""

from __future__ import annotations

import logging
import queue
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Protocol

from ig.errors import IGLoginFailure

log = logging.getLogger("autobot.ig.stream")

TICK_FIELDS = ("BID", "OFR", "UTM")
CANDLE_FIELDS = ("BID_OPEN", "BID_HIGH", "BID_LOW", "BID_CLOSE",
                 "OFR_OPEN", "OFR_HIGH", "OFR_LOW", "OFR_CLOSE",
                 "UTM", "CONS_END", "CONS_TICK_COUNT")
AUTH_REFUSED_CODES = frozenset({1})  # Lightstreamer: "user/password check failed"


def tick_item(epic: str) -> str:
    return f"CHART:{epic}:TICK"


def candle_item(epic: str) -> str:
    return f"CHART:{epic}:5MINUTE"


# ---- what a transport tells the stream ---------------------------------------

@dataclass(frozen=True)
class Connected:
    how: str


@dataclass(frozen=True)
class Dropped:
    why: str


@dataclass(frozen=True)
class Refused:
    code: int
    why: str


@dataclass(frozen=True)
class Subscribed:
    item: str


@dataclass(frozen=True)
class SubscriptionFailed:
    item: str
    code: int
    why: str


@dataclass(frozen=True)
class TickUpdate:
    epic: str
    fields: dict


@dataclass(frozen=True)
class CandleUpdate:
    epic: str
    fields: dict


class Transport(Protocol):
    subscriptions_requested: int

    def open(self, endpoint: str, user: str, password: str, epics: tuple[str, ...],
             emit: Callable[[object], None]) -> None: ...

    def close(self) -> None: ...


@dataclass
class StreamStats:
    connects: int = 0               # connection attempts to IG's streaming server
    subscriptions: int = 0          # subscriptions requested
    drops: int = 0
    relogins: int = 0
    ticks: int = 0
    candle_updates: int = 0
    waits: list = field(default_factory=list)


class PriceStream:
    def __init__(self, client: Any, epics: tuple[str, ...] | list[str], stream_settings: Any,
                 transport_factory: Callable[[], Transport], *,
                 on_tick: Callable[[str, dict], None], on_candle: Callable[[str, dict], None],
                 on_new_connection: Callable[[], None] = lambda: None,
                 market_open_since: Callable[[datetime], datetime | None] = lambda now: now,
                 now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
                 wait: Callable[[float], None] | None = None,
                 warn: Callable[[str], None] | None = None):
        self.client = client
        if isinstance(epics, str) or not epics or len(set(epics)) != len(epics):
            raise ValueError("PriceStream needs a list of different epics, one per pair")
        self.epics = tuple(epics)
        self.waits = tuple(stream_settings.reconnect_waits_seconds)
        self.quiet_after = timedelta(seconds=stream_settings.no_prices_warning_seconds)
        self.healthy_after = timedelta(minutes=stream_settings.healthy_after_minutes)
        self.transport_factory = transport_factory
        self.on_tick, self.on_candle = on_tick, on_candle
        self.on_new_connection = on_new_connection
        self.market_open_since = market_open_since
        self.now = now
        self._stop = threading.Event()
        self._wait = wait or (lambda s: self._stop.wait(s))
        self.warn = warn or (lambda m: log.warning(m))

        self.events: "queue.Queue[tuple[int, object]]" = queue.Queue()
        self.stats = StreamStats()
        self.transport: Transport | None = None
        self.generation = 0
        self.connected_since: datetime | None = None
        self.next_wait = 0
        self.relogin_allowed = True
        self.last_price_at: datetime | None = None
        self.quiet_warned = False

    # ---- connecting ----------------------------------------------------------

    def start(self) -> None:
        self._open()

    def _open(self) -> None:
        user, password = self.client.stream_login()
        endpoint = self.client.streaming_endpoint
        self.generation += 1
        gen = self.generation
        # Every connection (first, reconnect, re-login) starts fresh: the
        # prices part forgets the last BID/OFR before anything new arrives.
        self.on_new_connection()
        t = self.transport_factory()
        self.transport = t
        self.connected_since = None
        if self.last_price_at is None:
            self.last_price_at = self.now()
        self.stats.connects += 1
        t.open(endpoint, user, password, self.epics, lambda ev, g=gen: self.events.put((g, ev)))
        self.stats.subscriptions += getattr(t, "subscriptions_requested", 0)

    def _close(self) -> None:
        if self.transport is not None:
            try:
                self.transport.close()
            except Exception as e:  # closing must never stop the bot
                log.info("Closing the old stream connection raised %s; carrying on.", type(e).__name__)
        self.transport = None
        self.generation += 1  # anything still coming from the old connection is ignored

    def request_stop(self) -> None:
        """Ask the stream to stop (safe from a signal handler). It also ends a
        reconnect wait at once. Call stop() afterwards to close the connection."""
        self._stop.set()

    def stop(self) -> None:
        self._stop.set()
        self._close()

    @property
    def stopped(self) -> bool:
        return self._stop.is_set()

    def _reconnect(self, why: str) -> None:
        self.stats.drops += 1
        self._close()
        wait = self.waits[min(self.next_wait, len(self.waits) - 1)]
        self.next_wait += 1
        self.stats.waits.append(wait)
        self.warn(f"Price stream dropped ({why}). Reconnecting in {wait} seconds "
                  f"(attempt {self.next_wait}). Not logging in again.")
        self._wait(wait)
        if not self.stopped:
            self._open()

    # ---- events ---------------------------------------------------------------

    def handle(self, gen: int, ev: object) -> None:
        if gen != self.generation or self.stopped:
            return  # from a connection that has already been closed
        now = self.now()
        if isinstance(ev, Connected):
            self.connected_since = now
            log.info("Price stream connected (%s).", ev.how)
        elif isinstance(ev, Subscribed):
            log.info("Subscribed to %s.", ev.item)
        elif isinstance(ev, TickUpdate):
            self.stats.ticks += 1
            if ev.epic not in self.epics:
                log.warning("Ignored a tick for %s, which this stream did not ask for.", ev.epic)
                return
            self._price_arrived(now)
            self.on_tick(ev.epic, ev.fields)
        elif isinstance(ev, CandleUpdate):
            self.stats.candle_updates += 1
            if ev.epic not in self.epics:
                log.warning("Ignored a candle for %s, which this stream did not ask for.", ev.epic)
                return
            self._price_arrived(now)
            self.on_candle(ev.epic, ev.fields)
        elif isinstance(ev, Dropped):
            self._reconnect(ev.why)
        elif isinstance(ev, SubscriptionFailed):
            self._reconnect(f"IG refused the subscription to {ev.item}: error {ev.code} {ev.why}")
        elif isinstance(ev, Refused):
            self._refused(ev)

    def _refused(self, ev: Refused) -> None:
        if ev.code not in AUTH_REFUSED_CODES:
            self._reconnect(f"IG's streaming server closed the connection: error {ev.code} {ev.why}")
            return
        if not self.relogin_allowed:
            self._close()
            raise IGLoginFailure("stream-login-refused",
                                 f"IG refused the price stream's login again (error {ev.code}) after the one "
                                 "controlled re-login. Stopping.")
        self.relogin_allowed = False
        self.stats.relogins += 1
        self._close()
        self.warn(f"IG refused the price stream's login (error {ev.code}). One controlled re-login.")
        self.client.relogin_for_stream()
        self._open()

    def _price_arrived(self, now: datetime) -> None:
        if self.quiet_warned:
            log.warning("Prices are arriving again (after %d seconds with none).",
                        (now - self.last_price_at).total_seconds() if self.last_price_at else 0)
            self.quiet_warned = False
        self.last_price_at = now

    # ---- regular checks -----------------------------------------------------

    def check(self) -> None:
        """Called about once a second: health and quiet checks."""
        now = self.now()
        if self.connected_since is not None and now - self.connected_since >= self.healthy_after:
            if self.next_wait or not self.relogin_allowed:
                log.info("Price stream healthy for %s: reconnect waits start from the first again.",
                         self.healthy_after)
            self.next_wait = 0
            self.relogin_allowed = True
        opened = self.market_open_since(now)
        if opened is None or self.last_price_at is None or self.quiet_warned:
            return
        since = max(self.last_price_at, opened)
        if now - since >= self.quiet_after:
            self.warn(f"NO PRICES from IG for {int((now - since).total_seconds())} seconds while the market "
                      f"is open (warning after {int(self.quiet_after.total_seconds())} seconds).")
            self.quiet_warned = True

    def pump(self, timeout: float = 0.0) -> int:
        """Handle every waiting event. Waits up to `timeout` for the first."""
        n = 0
        try:
            gen, ev = self.events.get(timeout=timeout) if timeout else self.events.get_nowait()
        except queue.Empty:
            return 0
        while True:
            self.handle(gen, ev)
            n += 1
            try:
                gen, ev = self.events.get_nowait()
            except queue.Empty:
                return n

    def run_until(self, deadline: datetime, every_second: Callable[[], None] = lambda: None) -> None:
        while not self.stopped and self.now() < deadline:
            self.pump(timeout=1.0)
            self.check()
            every_second()


# ---- the real transport: Lightstreamer ----------------------------------------

class LightstreamerTransport:
    """Connects to IG's Lightstreamer server with lightstreamer-client-lib
    (version pinned in requirements.txt)."""

    def __init__(self) -> None:
        self.subscriptions_requested = 0
        self._client = None
        self._closing = False
        self._server_error = threading.Event()

    def open(self, endpoint: str, user: str, password: str, epics: tuple[str, ...],
             emit: Callable[[object], None]) -> None:
        from lightstreamer.client import (ClientListener, LightstreamerClient,
                                          Subscription, SubscriptionListener)
        transport = self

        class _Client(ClientListener):
            def onStatusChange(self, status):
                if transport._closing:
                    return
                if status.startswith("CONNECTED:") and status.endswith(("STREAMING", "POLLING")):
                    emit(Connected(status))
                elif status in ("DISCONNECTED:WILL-RETRY", "DISCONNECTED:TRYING-RECOVERY"):
                    emit(Dropped(status))
                elif status == "DISCONNECTED":
                    # A refusal is followed by onServerError; give it a moment.
                    def later():
                        if not transport._server_error.is_set() and not transport._closing:
                            emit(Dropped("closed by IG's streaming server"))
                    threading.Timer(2.0, later).start()
                elif status == "STALLED":
                    log.warning("Price stream stalled (no data for a while); the library is checking it.")

            def onServerError(self, code, message):
                transport._server_error.set()
                emit(Refused(int(code), str(message)))

        class _Sub(SubscriptionListener):
            def __init__(self, epic, item, fields, kind):
                self.epic, self.item, self.fields, self.kind = epic, item, fields, kind

            def onSubscription(self):
                emit(Subscribed(self.item))

            def onSubscriptionError(self, code, message):
                emit(SubscriptionFailed(self.item, int(code), str(message)))

            def onItemUpdate(self, update):
                values = {f: update.getValue(f) for f in self.fields}
                emit(self.kind(self.epic, values))

        client = LightstreamerClient(endpoint, None)
        client.connectionDetails.setUser(user)
        client.connectionDetails.setPassword(password)
        client.addListener(_Client())

        # Two subscriptions per pair, each for one item, so every update is
        # known to belong to its epic.
        for epic in epics:
            ticks = Subscription("DISTINCT", [tick_item(epic)], list(TICK_FIELDS))
            ticks.setRequestedSnapshot("no")
            ticks.addListener(_Sub(epic, tick_item(epic), TICK_FIELDS, TickUpdate))
            candles = Subscription("MERGE", [candle_item(epic)], list(CANDLE_FIELDS))
            candles.setRequestedSnapshot("yes")  # the current candle's values so far
            candles.addListener(_Sub(epic, candle_item(epic), CANDLE_FIELDS, CandleUpdate))
            client.subscribe(ticks)
            client.subscribe(candles)
        self.subscriptions_requested = 2 * len(epics)
        self._client = client
        client.connect()

    def close(self) -> None:
        self._closing = True
        if self._client is not None:
            self._client.disconnect()
