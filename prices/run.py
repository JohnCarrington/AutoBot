"""Run the live price stream for one pair, for a set time. Run:
    .venv/bin/python -m prices.run --minutes 20 [--pair GBPUSD]
(--pair may be left out when only one pair is switched on in .env.)
Stop the price service first: only one login at a time.

1. Logs in to IG and chooses the bot's account (ig.client, Stage 3 rules).
2. Start-up: checks the candle store, reports the newest candle and its age,
   records any gap since it (not filled).
3. Streams that pair's ticks and IG's 5-minute candles for the given minutes,
   storing finished candles and building bigger ones.
4. Logs out, checks the store again and prints a report: ticks, the 5-minute
   candles stored, the store checks, and every IG call made.
No historical prices are asked for.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

from config.pairs import choose_pair
from config.settings_loader import load_or_exit
from housekeeping.disk import check_free_space
from housekeeping.logs import setup_logging
from ig.client import IGClient, is_historical_prices_path
from ig.errors import IGLoginFailure, stop_bot
from ig.secrets import ENV_PATH, load_credentials
from ig.stream import LightstreamerTransport, PriceStream
from prices.checks import check_store
from levels.current import LevelsUpdater
from prices.feed import PriceFeed
from prices.model import plain, uk, uk_short
from prices.store import CandleStore


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, required=True)
    ap.add_argument("--pair")
    args = ap.parse_args(argv)

    settings = choose_pair(load_or_exit(), args.pair)
    setup_logging(settings.housekeeping, "prices")
    store = CandleStore(settings.candles.folder, settings.candles.compress_after_days)
    feed = PriceFeed(settings, store, disk_check=lambda: check_free_space(
        settings.candles.folder, settings.housekeeping.min_free_disk_mb, feed.warn),
        after_new_candle=LevelsUpdater(settings, store))

    def say(text: str = "") -> None:
        print(text, flush=True)

    started = datetime.now(timezone.utc)
    say(f"Live price stream for {settings.market.epic}, {args.minutes:g} minutes, started {uk(started)}")
    report = feed.start_up()
    for line in report.lines:
        say("  " + line)

    client = IGClient(settings.ig, load_credentials(ENV_PATH))
    stream = None
    try:
        client.connect()
        stream = PriceStream(client, (settings.market.epic,), settings.stream, LightstreamerTransport,
                             on_tick=lambda epic, f: feed.on_tick(f), on_candle=lambda epic, f: feed.on_candle(f),
                             on_new_connection=feed.new_connection,
                             market_open_since=feed.market_open_since, warn=feed.warn)
        stream.start()
        stream.run_until(started + timedelta(minutes=args.minutes))
    except IGLoginFailure as failure:
        if stream:
            stream.stop()
        client.logout()
        stop_bot(failure)
    finally:
        if stream:
            stream.stop()
    client.logout()
    ended = datetime.now(timezone.utc)

    final = check_store(store, feed.b)
    say()
    say(f"Run ended {uk(ended)} ({(ended - started).total_seconds() / 60:.1f} minutes).")
    say()
    say(f"TICKS RECEIVED: {feed.ticks}" + (f" (plus {feed.bad_ticks} skipped)" if feed.bad_ticks else ""))
    say(f"  with one price carried forward (IG sent only the price that changed): {feed.carried_forward}")
    if feed.first_tick:
        say(f"  first: {uk(feed.first_tick.time)}  buy {plain(feed.first_tick.buy)}  sell {plain(feed.first_tick.sell)}")
        say(f"  last:  {feed.describe_last_tick()}")
    say(f"Unfinished 5-minute candle updates seen (not stored): {feed.unfinished_seen}")
    say()
    say(f"5-MINUTE CANDLES STORED DURING THE RUN: {len(feed.stored)}")
    say(f"  {'start (UK)':<20} {'BUY open':>9} {'high':>9} {'low':>9} {'close':>9}   "
        f"{'SELL open':>9} {'high':>9} {'low':>9} {'close':>9}")
    for c in feed.stored:
        say(f"  {uk_short(c.start):<20} {plain(c.buy_open):>9} {plain(c.buy_high):>9} {plain(c.buy_low):>9} "
            f"{plain(c.buy_close):>9}   {plain(c.sell_open):>9} {plain(c.sell_high):>9} "
            f"{plain(c.sell_low):>9} {plain(c.sell_close):>9}")
    if feed.built:
        say(f"Bigger candles built: " + ", ".join(f"{c.timeframe} {uk_short(c.start)} ({c.parts}/{c.expected_parts})"
                                                  for c in feed.built))
    say()
    say("STORE CHECKS")
    for line in report.lines[:1]:
        say("  At start-up: " + line.split(": ", 1)[1])
    after = [r for r in feed.check_results[1:]]
    say(f"  After each new candle: {len(after)} check(s), "
        f"{sum(len(r.problems) for r in after)} problem(s), {sum(len(r.new_gaps) for r in after)} new gap(s)")
    say(f"  At the end: {sum(final.candles.values())} candle(s) "
        f"({', '.join(f'{tf} {n}' for tf, n in final.candles.items())}); {len(final.problems)} problem(s); "
        f"{len(final.gaps)} gap(s) ({len(final.new_gaps)} not yet recorded)")
    for p in final.problems:
        say("    " + p)
    for g in final.gaps:
        say("    " + g.describe() + (" (recorded)" if g.known else ""))
    say(f"  Warnings written during the run: {len(feed.warnings)}")
    for w in feed.warnings:
        say("    " + w)
    say()
    rest = Counter(f"{c.method} {c.path.split('?')[0]}" for c in client.calls)
    hist = sum(1 for c in client.calls if is_historical_prices_path(c.path))
    total = len(client.calls) + (stream.stats.connects + stream.stats.subscriptions if stream else 0)
    say(f"IG CALLS MADE: {total}")
    for name, n in rest.items():
        say(f"  {name:<20} {n}")
    if stream:
        say(f"  {'stream connections':<20} {stream.stats.connects}")
        say(f"  {'stream subscriptions':<20} {stream.stats.subscriptions}  "
            f"(CHART:{settings.market.epic}:TICK and :5MINUTE per connection)")
        say(f"  stream drops: {stream.stats.drops}, reconnect waits: {stream.stats.waits or 'none'}, "
            f"re-logins: {stream.stats.relogins}")
    say(f"  HISTORICAL PRICE CALLS: {hist}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
