# AutoBot

An automated trading bot for GBPUSD on an IG **demo** account. It reads live prices, works out the market state, lets only the right strategies look for trades, checks every trade idea against safety rules, and sends orders to IG with a stop loss and take profit. Every trade is recorded, shown on a dashboard and reported by Telegram.

**Current stage:** any currency pair, with only GBPUSD switched on (`docs/PAIRS.md`), after Stage 7 part 1 (the analyser's indicators and the direction rule). The bot has its settings and the switches in `.env` (pairs switched on, trading hours, strategies on or off), the IG connection, the live price stream and a candle store per pair (running all the time as a service), the guarded history door (one budget for all pairs), the levels, the shared rejection part, and the analyser's indicators, direction rule and data check. Everything uses the sell (bid) price, as on Johnny's IG chart. There are no orders or trading code yet.

**The agreed design** is `docs/DESIGN.md`. Where any other document disagrees with it, it wins.

**Backup:** the code is backed up to the private GitHub repository `JohnCarrington/AutoBot`; `main` is pushed there at the end of each stage, once all tests pass.

## Where things are

- `docs/DESIGN.md`: the agreed design (the master copy)
- `docs/ARCHITECTURE.md`: the parts of the bot and how they connect
- `docs/LEVELS.md`: every levels rule, the current list and its file
- `docs/REJECTION.md`: every rejection rule, the spread-spike rule, and the checks on 5 November
- `docs/NEWS.md`: the economic calendar, big news (161's table), the no-trading windows and expected directions
- `docs/ALERTS.md`: the Telegram alerts: ready messages, problem alerts, trade messages, the limit on repeats
- `docs/PAIRS.md`: how the bot works for any currency pair, what is shared, and how to switch a new pair on
- `docs/ANALYSER.md`: the analyser's indicators, the direction rule, and when its data is ready, warming up or out of date
- `rejection/`: the shared rejection part
- `levels/`: pivots, round numbers, highs and lows, turning levels, and which levels line up
- `/opt/autobot/data/levels/<PAIR>/current.json`: each pair's current list of levels (on the server only, not in git)
- `docs/SETTINGS.md`: every setting, what it does, and its value
- `docs/IG_CONNECTION.md`: how the bot logs in to IG, chooses its account and handles IG's errors
- `deploy/autobot-prices.service`: the systemd service for the price stream
- `docs/PRICES_AND_CANDLES.md`: the live price stream, the candles, the candle store and its checks, the history door and the one-off fill
- `/opt/autobot/data/history/`: the history door's records (points ledger, IG's allowance, daily record, block marker)
- `prices/`: candles, the candle store and its checks
- `housekeeping/`: log rotation and the disk space warning
- `/opt/autobot/data/candles/<PAIR>/`: each pair's candle store (on the server only, not in git)
- `/opt/autobot/logs/`: log files (rotated by size and age)
- `ig/`: the only part that talks to IG's servers
- `config/settings.toml`: the settings file (all numbers live here)
- `.env.example`: the secret settings the bot needs (copy to `.env`; never commit `.env`)
- `tests/technical/` and `tests/functional/`: the tests

## Setting up

```
cd /opt/autobot
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
git config core.hooksPath hooks     # turns on the pre-commit test check
```

## Running the tests

One command runs every test:

```
./run_tests.sh
```

Every commit runs all the tests first (`hooks/pre-commit`). If any test fails, the commit is blocked.

## Checking the settings file

```
.venv/bin/python -m config
```

This prints every setting, or stops with a message saying which setting is missing or wrong.

## Checking the IG connection

```
.venv/bin/python -m ig.check
```

This is the only command that contacts the real IG. It logs in to the IG demo account once, lists the accounts (showing only the last 4 characters of each number), switches to `IG_ACCOUNT_ID` without changing IG's default account, confirms the streaming address was received (without showing it), and logs out. That is four IG calls, with no retries. The tests never contact IG.

## The price stream service

The price stream runs all the time as the systemd service `autobot-prices` (`deploy/autobot-prices.service`). It never restarts after a login failure (exit code 78). How to install, start, stop and check it: `docs/PRICES_AND_CANDLES.md`, "Running the price stream as a service".

## Running the live price stream

```
.venv/bin/python -m prices.run --minutes 20 [--pair GBPUSD]
```

This is a timed run, by hand (stop the service first). It logs in to IG, checks the candle store and reports its newest candle, streams live GBPUSD prices for the given number of minutes (storing IG's finished 5-minute candles and building the bigger ones), then logs out. It reports the ticks received, the candles stored, the store checks, and a count of every IG call made. See `docs/PRICES_AND_CANDLES.md`.

The one-off history fill for GBPUSD (`.venv/bin/python -m prices.history_fill plan` / `go --pair GBPUSD`) ran once on 6 November 2026 and will not run again. A newly switched-on pair is never filled automatically: its fill needs the owner's go-ahead (`docs/PAIRS.md`).

The GBPUSD epic (`CS.D.GBPUSD.TODAY.IP`) was found once with `.venv/bin/python -m ig.find_market GBPUSD` (one market search) and is kept in the settings file.

## Showing the levels

```
.venv/bin/python -m levels [--pair GBPUSD]
```

Works out the levels now from the candle store, prints them by group, and writes the current list. Contacts nobody. `--at 2026-11-06T00:00:00Z` shows the levels as they stood at that UTC time, without writing anything. See `docs/LEVELS.md`.

## Showing rejections

```
.venv/bin/python -m rejection 2026-11-05T21:00:00Z 2026-11-06T00:30:00Z [--pair GBPUSD]
```

Lists every rejection event (pierce, reversal, confirmation, trigger, cancelled, expired, ignored) between two UTC times from the stored candles, then every setup. Contacts nobody. See `docs/REJECTION.md`.

## Showing the analyser

```
.venv/bin/python -m analyser 2026-11-06T13:00:00Z [--pair GBPUSD]
```

Shows the direction (buy side, sell side or no clear direction) and why, whether the data is ready, warming up or out of date, and every indicator on the 5-minute and hourly candles at that UTC time, from the stored candles. Contacts nobody. See `docs/ANALYSER.md`.

## Telegram

```
.venv/bin/python -m alerts test "AutoBot test message"
```

Sends one Telegram message and prints whether Telegram accepted it (never the token or chat ID). The price service sends the ready messages and problem alerts by itself. See `docs/ALERTS.md`.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Finished normally. |
| 1 | Problem in the settings file. IG was not contacted. |
| **78** | **IG login failure** (including IG refusing the price stream again after its one controlled re-login). Reserved for this alone. The bot must **not** be restarted automatically: the service file must contain `RestartPreventExitStatus=78`. See `docs/IG_CONNECTION.md`. |
