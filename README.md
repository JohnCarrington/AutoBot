# AutoBot

An automated trading bot for GBPUSD on an IG **demo** account. It reads live prices, works out the market state, lets only the right strategies look for trades, checks every trade idea against safety rules, and sends orders to IG with a stop loss and take profit. Every trade is recorded, shown on a dashboard and reported by Telegram.

**Current stage:** Stage 4a. The bot has its settings, the IG connection (logging in to the IG demo account, choosing the account and handling IG's errors), and now the live GBPUSD price stream and the candle store (5-minute candles from IG; 1-hour, 4-hour, daily and weekly candles built from them; checks on the store). There are no orders or trading code yet. **The bot never asks IG for historical prices.**

**Backup:** the code is backed up to the private GitHub repository `JohnCarrington/AutoBot`; `main` is pushed there at the end of each stage, once all tests pass.

## Where things are

- `docs/ARCHITECTURE.md`: the parts of the bot and how they connect
- `docs/SETTINGS.md`: every setting, what it does, and its value
- `docs/IG_CONNECTION.md`: how the bot logs in to IG, chooses its account and handles IG's errors
- `docs/PRICES_AND_CANDLES.md`: the live price stream, the candles, the candle store and its checks
- `prices/`: candles, the candle store and its checks
- `housekeeping/`: log rotation and the disk space warning
- `/opt/autobot/data/candles/`: the candle store (on the server only, not in git)
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

## Running the live price stream

```
.venv/bin/python -m prices.run --minutes 20
```

This logs in to IG, checks the candle store and reports its newest candle, streams live GBPUSD prices for the given number of minutes (storing IG's finished 5-minute candles and building the bigger ones), then logs out. It reports the ticks received, the candles stored, the store checks, and a count of every IG call made. See `docs/PRICES_AND_CANDLES.md`.

The GBPUSD epic (`CS.D.GBPUSD.TODAY.IP`) was found once with `.venv/bin/python -m ig.find_market` (one market search) and is kept in the settings file.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Finished normally. |
| 1 | Problem in the settings file. IG was not contacted. |
| **78** | **IG login failure** (including IG refusing the price stream again after its one controlled re-login). Reserved for this alone. The bot must **not** be restarted automatically: the service file must contain `RestartPreventExitStatus=78`. See `docs/IG_CONNECTION.md`. |
