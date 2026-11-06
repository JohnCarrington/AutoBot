"""The price stream as a service, running all the time.

Run by systemd (deploy/autobot-prices.service):
    /opt/autobot/.venv/bin/python -m prices.service

What it does:
  1. Start-up, exactly as the live run: checks the candle store, reports the
     newest candle and its age, and RECORDS any gap since it. It never asks IG
     for history: this module does not use the history door at all (a test
     checks that).
  2. Logs in (Stage 3 rules) and streams GBPUSD ticks and IG's 5-minute
     candles, storing finished candles and building the bigger ones, until it
     is told to stop. Drops are reconnected with increasing waits; IG refusing
     the stream gets one controlled re-login, then exit code 78.
  3. Every stream.status_log_minutes it logs a status line.
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

from config.settings_loader import load_or_exit
from housekeeping.disk import check_free_space
from housekeeping.logs import setup_logging
from ig.client import IGClient
from ig.errors import IGLoginFailure, stop_bot
from ig.secrets import ENV_PATH, load_credentials
from ig.stream import LightstreamerTransport, PriceStream
from levels.current import LevelsUpdater
from prices.feed import PriceFeed
from prices.model import uk
from prices.store import CandleStore

log = logging.getLogger("autobot.prices.service")
UTC = timezone.utc


def serve(settings: Any = None, *, client: Any = None, transport_factory: Callable = LightstreamerTransport,
          stop: threading.Event | None = None, now: Callable[[], datetime] = lambda: datetime.now(UTC),
          logs: bool = True, signals: bool = True) -> int:
    settings = settings or load_or_exit()
    if logs:
        setup_logging(settings.housekeeping, "prices")
    stop = stop or threading.Event()
    store = CandleStore(settings.candles.folder, settings.candles.compress_after_days)
    feed = PriceFeed(settings, store, now=now, disk_check=lambda: check_free_space(
        settings.candles.folder, settings.housekeeping.min_free_disk_mb, feed.warn),
        after_new_candle=LevelsUpdater(settings, store))
    stream: PriceStream | None = None

    def on_signal(signum, frame):
        log.info("Received %s: stopping.", signal.Signals(signum).name)
        stop.set()
        if stream is not None:
            stream.request_stop()

    if signals:
        signal.signal(signal.SIGTERM, on_signal)
        signal.signal(signal.SIGINT, on_signal)

    log.info("AutoBot price service starting for %s.", settings.market.epic)
    feed.start_up()   # store check, newest candle, gap recorded; no history asked for

    client = client or IGClient(settings.ig, load_credentials(ENV_PATH))
    every = timedelta(minutes=settings.stream.status_log_minutes)
    next_status = [now() + every]

    def every_second() -> None:
        if stop.is_set() and stream is not None:
            stream.request_stop()
        if now() >= next_status[0]:
            next_status[0] = now() + every
            log.info("Status: %d ticks (%d with a price carried forward, %d skipped) and %d five-minute "
                     "candles stored since start; last tick %s; stream connections %d, drops %d, re-logins %d.",
                     feed.ticks, feed.carried_forward, feed.bad_ticks, len(feed.stored),
                     feed.describe_last_tick(), stream.stats.connects, stream.stats.drops, stream.stats.relogins)

    try:
        if stop.is_set():
            return 0
        client.connect()
        stream = PriceStream(client, settings.market.epic, settings.stream, transport_factory,
                             on_tick=feed.on_tick, on_candle=feed.on_candle,
                             on_new_connection=feed.new_connection,
                             market_open_since=feed.market_open_since, now=now, warn=feed.warn)
        if stop.is_set():
            stream.request_stop()
        stream.start()
        stream.run_until(datetime.max.replace(tzinfo=UTC), every_second)
    except IGLoginFailure as failure:
        if stream:
            stream.stop()
        client.logout()
        log.error("Stopping: %s", failure)
        stop_bot(failure)
    except Exception:
        log.exception("The price service crashed. Logging out; systemd restarts it after 30 seconds.")
        if stream:
            stream.stop()
        client.logout()
        raise
    finally:
        if stream:
            stream.stop()
    client.logout()
    log.info("AutoBot price service stopped at %s: %d ticks and %d five-minute candles stored since start.",
             uk(now()), feed.ticks, len(feed.stored))
    return 0


def main() -> int:
    return serve()


if __name__ == "__main__":
    sys.exit(main())
