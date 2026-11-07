"""The price stream as a service, running all the time.

Run by systemd (deploy/autobot-prices.service):
    /opt/autobot/.venv/bin/python -m prices.service

What it does:
  1. Start-up, for EACH pair switched on in .env (PAIRS_ON), exactly as the
     live run: checks that pair's candle store, reports the newest candle and
     its age, and RECORDS any gap since it. It never asks IG for history: this
     module does not use the history door at all (a test checks that). A pair
     switched on for the first time simply starts with an empty store; filling
     its history needs the owner's go-ahead (prices.history_fill --pair).
  2. Logs in ONCE (Stage 3 rules) and streams every switched-on pair's ticks
     and IG's 5-minute candles on one connection. Each update carries its
     epic and goes to that pair's feed and store only. Finished candles are
     stored and the bigger ones built, until it is told to stop. Drops are reconnected with increasing waits; IG refusing
     the stream gets one controlled re-login, then exit code 78.
  3. Every stream.status_log_minutes it logs a status line.
  3b. After start-up and each new 5-minute candle, each pair's levels and its
     market states (analyser/market_state.py): at start-up the states replay
     the week from its open; every state change is recorded in
     data/analyser/<PAIR>/state_changes.jsonl.
  3a. Telegram (alerts/): the Sunday and daily "ready" messages (alerts/ready.py),
     and a problem alert for an IG login failure that stops it, the stream going
     quiet while the market is open, any candle store problem, and a crash.
  4. On SIGTERM or SIGINT (systemctl stop): stops the stream, logs out of IG
     and exits with code 0.

Exit codes: 0 stopped normally; 1 settings problem or crash (systemd restarts
it after 30 seconds); 78 IG login failure (systemd does NOT restart it).
"""

from __future__ import annotations

import logging
import signal
import sys
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from alerts.telegram import Alerts
from config.settings_loader import load_or_exit
from housekeeping.disk import check_free_space
from housekeeping.logs import setup_logging
from ig.client import IGClient
from ig.errors import IGLoginFailure, stop_bot
from ig.secrets import ENV_PATH, load_credentials
from ig.stream import LightstreamerTransport, PriceStream
from analyser.market_state import StatesUpdater
from levels.current import LevelsUpdater
from prices.feed import PriceFeed
from prices.model import uk
from prices.store import CandleStore

log = logging.getLogger("autobot.prices.service")
UTC = timezone.utc


def serve(settings: Any = None, *, client: Any = None, transport_factory: Callable = LightstreamerTransport,
          stop: threading.Event | None = None, now: Callable[[], datetime] = lambda: datetime.now(UTC),
          logs: bool = True, signals: bool = True, alerts: Any = None) -> int:
    settings = settings or load_or_exit()
    if logs:
        setup_logging(settings.housekeeping, "prices")
    alerts = alerts if alerts is not None else Alerts.from_env(settings)
    stop = stop or threading.Event()
    feeds: dict[str, PriceFeed] = {}            # epic -> that pair's feed
    for ps in settings.pairs_on():
        feeds[ps.market.epic] = _feed(ps, now, lambda m: alerts.problem("store-problem", m))
    any_feed = next(iter(feeds.values()))
    stream: PriceStream | None = None

    def on_signal(signum, frame):
        log.info("Received %s: stopping.", signal.Signals(signum).name)
        stop.set()
        if stream is not None:
            stream.request_stop()

    if signals:
        signal.signal(signal.SIGTERM, on_signal)
        signal.signal(signal.SIGINT, on_signal)

    log.info("AutoBot price service starting for %s.",
             ", ".join(f"{f.pair} ({epic})" for epic, f in feeds.items()))
    for f in feeds.values():
        f.start_up()   # store check, newest candle, gap recorded; no history asked for

    client = client or IGClient(settings.ig, load_credentials(ENV_PATH))
    every = timedelta(minutes=settings.stream.status_log_minutes)
    next_status = [now() + every]
    ready = None
    if hasattr(settings, "alerts"):
        from alerts.ready import ReadyAlerts, ReadyContext
        from ig.allowance_status import HistoryStatus
        door = HistoryStatus(settings.history.folder, now)   # reads the door's files only; never sends
        ready = ReadyAlerts(settings, alerts, lambda: ReadyContext(
            settings, client, stream, {f.pair: f for f in feeds.values()}, door), now=now)

    def every_second() -> None:
        if ready is not None and stream is not None:
            ready.tick()
        if stop.is_set() and stream is not None:
            stream.request_stop()
        if now() >= next_status[0]:
            next_status[0] = now() + every
            for f in feeds.values():
                f.log.info("Status: %d ticks (%d with a price carried forward, %d skipped) and %d five-minute "
                           "candles stored since start; last tick %s.",
                           f.ticks, f.carried_forward, f.bad_ticks, len(f.stored), f.describe_last_tick())
            log.info("Stream connections %d, drops %d, re-logins %d.",
                     stream.stats.connects, stream.stats.drops, stream.stats.relogins)

    def new_connection() -> None:
        for f in feeds.values():
            f.new_connection()

    try:
        if stop.is_set():
            return 0
        client.connect()
        stream = PriceStream(client, tuple(feeds), settings.stream, transport_factory,
                             on_tick=lambda epic, fields: feeds[epic].on_tick(fields),
                             on_candle=lambda epic, fields: feeds[epic].on_candle(fields),
                             on_new_connection=new_connection,
                             market_open_since=any_feed.market_open_since, now=now, warn=any_feed.warn,
                             on_quiet=lambda m: alerts.problem("stream-quiet", m))
        if stop.is_set():
            stream.request_stop()
        stream.start()
        stream.run_until(datetime.max.replace(tzinfo=UTC), every_second)
    except IGLoginFailure as failure:
        if stream:
            stream.stop()
        client.logout()
        log.error("Stopping: %s", failure)
        alerts.problem("login-failure", f"IG login failure: {failure}. The price service has STOPPED (exit code "
                                        "78) and will not restart by itself: check IG, then start it again.")
        stop_bot(failure)
    except Exception:
        log.exception("The price service crashed. Logging out; systemd restarts it after 30 seconds.")
        alerts.problem("service-crash", "The price service crashed; systemd restarts it after 30 seconds "
                                        "(at most 5 times an hour). The log has the details.")
        if stream:
            stream.stop()
        client.logout()
        raise
    finally:
        if stream:
            stream.stop()
    client.logout()
    log.info("AutoBot price service stopped at %s.", uk(now()))
    for f in feeds.values():
        f.log.info("%d ticks and %d five-minute candles stored since start.", f.ticks, len(f.stored))
    return 0


def _after_candle(*parts: Callable[[datetime], None]) -> Callable[[datetime], None]:
    """After start-up and each new 5-minute candle: the levels, then the market states."""
    def run(now: datetime) -> None:
        for part in parts:
            part(now)
    return run


def _feed(ps: Any, now: Callable[[], datetime], on_store_problem: Callable[[str], None]) -> PriceFeed:
    """One pair's store, feed and levels (ps: settings.for_pair(...))."""
    store = CandleStore(ps.candles.folder, ps.candles.compress_after_days)
    feed: PriceFeed = PriceFeed(ps, store, now=now, disk_check=lambda: check_free_space(
        ps.candles.folder, ps.housekeeping.min_free_disk_mb, feed.warn),
        after_new_candle=_after_candle(LevelsUpdater(ps, store), StatesUpdater(ps, store)),
        on_store_problem=on_store_problem)
    return feed


def main() -> int:
    return serve()


if __name__ == "__main__":
    sys.exit(main())
