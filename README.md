# AutoBot

An automated trading bot for GBPUSD on an IG **demo** account. It reads live prices, works out the market state, lets only the right strategies look for trades, checks every trade idea against safety rules, and sends orders to IG with a stop loss and take profit. Every trade is recorded, shown on a dashboard and reported by Telegram.

**Current stage:** settings, plus the IG connection (logging in to the IG demo account, choosing the account and handling IG's errors). There are no prices, candles, orders or trading code yet.

## Where things are

- `docs/ARCHITECTURE.md`: the parts of the bot and how they connect
- `docs/SETTINGS.md`: every setting, what it does, and its value
- `docs/IG_CONNECTION.md`: how the bot logs in to IG, chooses its account and handles IG's errors
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

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Finished normally. |
| 1 | Problem in the settings file. IG was not contacted. |
| **78** | **IG login failure.** Reserved for this alone. The bot must **not** be restarted automatically: the service file must contain `RestartPreventExitStatus=78`. See `docs/IG_CONNECTION.md`. |
