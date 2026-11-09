# Telegram alerts

The alerts part (`alerts/`) sends Telegram messages to the owner (design section 9). It never contacts IG and never stops the bot: if Telegram cannot be reached, the failure is written to the log and the bot carries on. Every alert is also written to the log.

## Secrets

The bot token and chat ID are in `/opt/autobot/.env` (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`). They are never printed, logged, put in a message or committed. The token is part of Telegram's address, so an error is reported only by its kind and Telegram's own description (never the address or the library's error text), and the HTTP library's request logging is kept quiet. If either is missing, alerts go to the log only, with a warning naming what is missing (never a value).

## The limit on repeats

The same problem never sends more than one message every 10 minutes (`alerts.same_problem_every_minutes`). Messages held back are counted, and the next message says how many. The record is kept in `/opt/autobot/data/alerts/sent.json`, so it holds across restarts (a crash loop cannot flood the chat).

## Ready messages (run by the price service; `alerts/ready.py`)

- **Sunday:** when every pair switched on has stored its first 5-minute candle of the week after the reopen. If a pair still has none 30 minutes after the reopen (`alerts.sunday_ready_within_minutes`), a problem alert is sent instead.
- **Daily:** at 06:00 UK (`alerts.daily_ready_at`), Monday to Friday, GMT or BST. Not sent if the price service only starts more than 60 minutes later (`alerts.daily_ready_late_by_minutes`).
- **The checks:** logged in to IG; the price stream connected; for each pair, candles arriving (newest 5-minute candle finished within 10 minutes, `alerts.candles_arriving_within_minutes`; on Sunday, from this week's reopen); for each pair, the candle store checks passed (no problem and no gap not yet recorded); IG's remaining history allowance (known, above the 2,000 floor, and no block marker). The daily message adds, for each pair, that day's pivot, R1 to R3 and S1 to S3, the analyser's direction, and a check that the analyser's data is ready.
- **If any check fails,** a problem alert is sent **instead** of the ready message, naming each failed check and listing every check.
- Each is sent once (`/opt/autobot/data/alerts/ready.json`).
- The checks read the price service's own state and files only. The IG allowance comes from the history door's files through a read-only reader (`ig/allowance_status.py`); the price service still never uses the history door.

## Problem alerts

| Problem | Where it comes from |
|---|---|
| IG login failure that stops the bot (exit code 78) | the price service, just before it stops |
| The price stream quiet while the market is open | the price stream's quiet check (`stream.no_prices_warning_seconds`) |
| Any candle store problem: a check problem, or a gap (including a gap since the last candle at start-up) | each pair's price feed |
| A history block marker being written | the history door, in the fill tools (`prices.history_fill`, `prices.long_history`) |
| The price service crashing | the price service (systemd restarts it after 30 seconds) |

## Trade messages and the daily summary (`alerts/trades.py`, `records/book.py`)

Sent by the trading engine for every real trade (`Alerts.trade_opened`, `Alerts.trade_closed`) and each weekday at
20:35 UK (the daily summary). **AutoBot 161's format** (owner, 9 November 2026): a first line, then one item per line,
the label in bold followed by a colon. Sent as Telegram HTML (`parse_mode` HTML, every value escaped); if Telegram
refuses the HTML, the same message is sent again as plain text with the bold taken out. Prices are IG's points with
the real rate in brackets.

```
[AutoBot] 🎯 TRADE OPENED
Time: Wed 04 Nov 10:20 GMT
Deal ref: AB261104102005-1a2b3c4d
Epic: CS.D.GBPUSD.TODAY.IP
Strategy: level reversal
Dir: SELL | Size: £10/pip
Market state: trend up
Entry: 13394.5 (1.33945)
SL: 6 pips @ 13400.5 (1.34005) | Risk: £60.00
TP: 20 pips @ 13374.5 (1.33745) | TP kind: normal
Reason: level reversal: pierced R2 13398.1 at 10:05, confirmed 10:15
Level: R2 13398.1; price went 4.4 pips past it
```

```
[AutoBot] 🟢 TRADE CLOSED
Opened: Wed 04 Nov 10:20 GMT
Deal ref: AB261104102005-1a2b3c4d
Epic: CS.D.GBPUSD.TODAY.IP
Strategy: level reversal
Dir: SELL | Size: £10/pip
Market state: trend up
Entry: 13394.5 (1.33945) → Exit: 13383.2 (1.33832)
Closed: Wed 04 Nov 11:55 GMT
SL: 6 pips @ 13400.5 (1.34005) | Risk: £60.00
TP: 20 pips @ 13374.5 (1.33745) | TP kind: normal
Reason opened: level reversal: pierced R2 13398.1 at 10:05, confirmed 10:15
Level: R2 13398.1; price went 4.4 pips past it
Reason closed: a confirmed rejection at a level: S2 13383.0
PnL: +11.3 pips | +£113.00
Duration: 1 h 34 min
Best: +14.2 pips
Today: 3 trades | +8.4 pips
```

A close at a loss starts "[AutoBot] 🔴 TRADE CLOSED" (break even: ⚪). A range trade's close adds "Half close: ... | PnL: ... / ..." and "Rest: ... | PnL: ... / ..." lines before "Today".

`TP kind` is `normal`, `100 for a big-news day` or `100 for a trend day`.

```
[AutoBot] 📊 DAILY SUMMARY
Date: Wed 04 Nov 2026
Pair: GBPUSD
Mode: paper trades (TRADING is off)       (only while TRADING is off)
Trades: 2 | Won: 1 | Lost: 1
PnL: +14 pips | +£140.00
breakout: 1 trade | -6 pips | -£60.00     (one line per strategy)
Week so far: 3 trades | +64 pips | +£640.00
```

## Checking it by hand

`.venv/bin/python -m alerts test "AutoBot test message"` sends one message and prints whether Telegram accepted it, with its message number (never the token or chat ID). First sent on 7 November 2026: accepted, message number 12869.
