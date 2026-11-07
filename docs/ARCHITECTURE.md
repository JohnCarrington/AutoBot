# How AutoBot fits together

AutoBot works for any currency pair (only GBPUSD is switched on, `docs/PAIRS.md`) on an IG demo account. Every part works on one pair, given to it. It is split into parts, each in its own folder. Each part does one job. Only the `ig/` part talks to IG's servers, and only the order sender (through `ig/`) places or changes trades.

## The parts

| Folder | What it does |
|---|---|
| `ig/` | The only part that talks to IG's servers. Logs in, chooses the bot's account without changing IG's default account, and handles IG's errors. It also runs IG's live price stream (`ig/stream.py`): one connection for every pair switched on, each update tagged with its epic, reconnecting with increasing waits. Its history door (`ig/history.py`) is the only place allowed to ask IG for historical prices, under a weekly budget, an IG allowance floor, a size limit and a block marker, all shared by every pair; every other historical prices call is refused. The order sender will make its IG calls through it. See `docs/IG_CONNECTION.md` and `docs/PRICES_AND_CANDLES.md`. |
| `prices/` | (Also `prices/indicators.py`: the Bollinger band, EMA, MACD and RSI, on the sell price, for the rejection part, the analyser and the strategies.) Takes the live GBPUSD ticks and IG's finished 5-minute candles from the stream, stores the candles (buy and sell kept apart, UTC, one file per day per size, safe writes, never overwritten except that a bigger candle built from an incomplete set is rebuilt after a gap fill, with the old one archived), builds 1-hour, 4-hour, daily and weekly candles from them on IG's boundaries, and checks the store. It fills recorded gaps through the history door (`prices/history_fill.py`), only into missing candles. See `docs/PRICES_AND_CANDLES.md`. |
| `levels/` | Works out, from the stored candles and always with the sell (bid) price, as on Johnny's IG chart (`chart.price`): the daily pivot, R1–R3 and S1–S3, round numbers, the previous day's high and low, London and New York session highs and lows, and hourly turning levels from the last 2 weeks. Groups levels that line up (within 5 pips) and marks the ones that matter most. Writes one current list (`data/levels/current.json`), updated each time a 5-minute candle is stored. Never contacts IG. See `docs/LEVELS.md`. |
| `rejection/` | One shared part that works out, step by step, whether price has been rejected at a level or the Bollinger band: pierce (a level reached within 3 pips counts), reversal candle, confirmation candle, live trigger, cancelled or expired, each a timestamped event. Both the bounce and the quicker range-trade version, both directions, on the sell price. Records the reversal candle's size against the piercing candle and which levels lined up, and marks whether it counts under the reversal watch windows; it never filters. Ignores candles with a spread spike for starting or cancelling. Shared by the analyser, the strategies and the trade manager. Never contacts IG. See `docs/REJECTION.md`. |
| `analyser/` | Decides which of five market states the market is in, and which strategies are allowed. Built so far (Stage 7, part 1): the indicators (EMAs 7, 13, 21, 100, 200; Bollinger 20, 2; MACD 35, 45, 30; RSI 3) on the 5-minute and hourly candles, the direction rule (buy side above the daily pivot and the 5-minute 100 EMA, sell side below both), and whether its data is ready, warming up or out of date. Sell price. Never contacts IG. See `docs/ANALYSER.md`. |
| `strategies/` | One subfolder per strategy: `slow_grind`, `ema_pullback`, `bollinger_bounce`, `range_trade`. Each produces trade ideas. |
| `safety/` | Checks trade size, number of trades, trading hours, news and the off switch. |
| `orders/` | Sends orders to IG, always with a stop loss and take profit, and only ever touches the bot's own trades. |
| `trade_manager/` | Looks after open trades until they close. |
| `records/` | Records every trade. |
| `dashboard/` | Shows trades, the market state and warnings. |
| `news/` | The economic calendar from Finnhub, fetched a few times a day by the price service and kept on disk; which releases are big (AutoBot 161's table); the big-news no-trading windows for each pair's currencies and each big release's expected direction; a Telegram alert if the calendar is missing or out of date. Never contacts IG. See `docs/NEWS.md`. |
| `alerts/` | Sends Telegram alerts, with a limit on repeats: the Sunday and daily "ready" messages (or a problem alert naming each failed check), problem alerts (login failure, stream quiet, candle store problems, history block marker, service crash), and the trade opened and closed messages for the order sender when it is built. Never contacts IG; never stops the bot. See `docs/ALERTS.md`. |
| `config/` | The settings file (`settings.toml`, including each pair's `[pairs.<PAIR>]`), the switches in `.env` (pairs switched on, trading hours, strategies on or off: `switches.py`), and the code that loads and checks them. `settings.for_pair(name)` gives a part its pair (`pairs.py`). Every part reads its numbers from here. |
| `deploy/` | The systemd service file: the price stream runs all the time as `autobot-prices`, restarting after a crash but never after a login failure (exit code 78). |
| `housekeeping/` | Log files rotated by size and age (so they can never fill the disk), and the low disk space warning. |
| `data/candles/<PAIR>/` | Each pair's candle store and gap records, on the server only (not in git). Never deleted; old files are compressed. |
| `data/levels/<PAIR>/` | Each pair's current list of levels (`current.json`), on the server only (not in git). Rewritten (safe write) after every new 5-minute candle. |
| `data/history/` | The history door's records: points ledger, IG's allowance figures, daily record, block marker, and the one-off fill record. |

## How they connect

```
   IG's servers
        ▲
        │  (all IG calls)
       ig ── logs in, chooses the account, handles IG's errors
        │
        ▼  live prices (stream: ticks + IG's finished 5-minute candles)
  prices ──────► candle store, one per pair (data/candles/<PAIR>: 5m, 1h, 4h, 1d, 1w)
                   │
      ┌────────────┼──────────────┐
      ▼            ▼              ▼
   levels      rejection ◄──── (also used by strategies
      │            │             and trade manager)
      └─────┬──────┘
            ▼
        analyser ── decides the market state
            │       and which strategies are allowed
            ▼
       strategies  (only the allowed ones)
            │ trade idea
            ▼
         safety  ── size, number of trades, hours, news, off switch
            │ passed
            ▼
         orders  ──────► ig ──► IG (always with stop loss and take profit)
            │
            ▼
      trade_manager ── looks after the trade until it closes
            │
            ▼
   records ─► dashboard
       └────► alerts (Telegram)
```

In words:

1. **The IG part connects first.** It logs in to the IG demo account, switches to the bot's account and keeps the streaming address. If it cannot, the bot stops with exit code 78 and is not restarted automatically.
2. **Prices feed candles.** The IG part streams live GBPUSD ticks and IG's own 5-minute candles. The prices part stores each 5-minute candle once IG marks it finished, builds the 1-hour, 4-hour, daily and weekly candles from the stored 5-minute candles, and checks the store at start-up and after every new candle. If the stream drops, the IG part reconnects with increasing waits. Historical prices are asked for only through the history door, only for recorded gaps.
3. **Levels follow the candles.** After each new 5-minute candle is stored, the levels part works out every level again from the store and rewrites the current list. A problem there is warned about and never stops the price stream.
4. **The analyser reads candles, levels and the rejection part,** and decides which of the five market states the market is in and which strategies are allowed.
5. **A strategy's trade idea passes the safety rules,** which check trade size, how many trades are open, trading hours, big news and the off switch. An idea that fails any check is dropped.
6. **Then it goes to the order sender,** which sends it to IG through the IG part, with a stop loss and take profit attached.
7. **The trade manager looks after the trade until it closes.** It also closes trades at 20:30 and before big news when the safety part says so.
8. **Everything is recorded and shown on the dashboard, with Telegram alerts.**

## Rules that hold everywhere

- The agreed design is `docs/DESIGN.md`. Where any other document disagrees with it, it wins.
- No part except `ig/` talks to IG's servers (REST or the price stream), and no part except `orders/` asks it to place, change or close a trade.
- **Only the history door (`ig/history.py`) may ask IG for historical prices**, after its checks, counting the points before sending. Only recorded gaps are filled, and a stored 5-minute candle is never overwritten; after a fill, a bigger candle built from an incomplete set is rebuilt from the fuller set and the old one archived, never deleted.
- Times are stored in UTC and shown to people in UK time.
- IG's default account is never changed: changing it would change which account every future login lands on.
- Secrets (passwords, keys, tokens, account numbers) are never printed, logged or committed.
- Every order has a stop loss and a take profit.
- The bot only ever touches its own trades.
- No trade is held overnight.
- All numbers come from `config/settings.toml`; none are written into the code. The one exception is the login-failure exit code (78), which is fixed on purpose so it always matches the service file.
