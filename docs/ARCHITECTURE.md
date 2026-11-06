# How AutoBot fits together

AutoBot trades GBPUSD on an IG demo account. It is split into parts, each in its own folder. Each part does one job. Only the `ig/` part talks to IG's servers, and only the order sender (through `ig/`) places or changes trades.

## The parts

| Folder | What it does |
|---|---|
| `ig/` | The only part that talks to IG's servers. Logs in, chooses the bot's account without changing IG's default account, and handles IG's errors. The price feed and the order sender make their IG calls through it. See `docs/IG_CONNECTION.md`. |
| `prices/` | Receives live GBPUSD prices from IG and builds candles: tick, 5-minute, 1-hour, 4-hour, daily and weekly. |
| `levels/` | Works out pivots, round numbers, the previous day's high and low, session highs and lows, and recent turning levels. |
| `rejection/` | Works out whether price has been rejected at a level or band. Shared by the analyser, the strategies and the trade manager. |
| `analyser/` | Decides which of five market states the market is in, and which strategies are allowed. |
| `strategies/` | One subfolder per strategy: `slow_grind`, `ema_pullback`, `bollinger_bounce`, `range_trade`. Each produces trade ideas. |
| `safety/` | Checks trade size, number of trades, trading hours, news and the off switch. |
| `orders/` | Sends orders to IG, always with a stop loss and take profit, and only ever touches the bot's own trades. |
| `trade_manager/` | Looks after open trades until they close. |
| `records/` | Records every trade. |
| `dashboard/` | Shows trades, the market state and warnings. |
| `alerts/` | Sends Telegram alerts. |
| `config/` | The settings file (`settings.toml`) and the code that loads and checks it. Every part reads its numbers from here. |

## How they connect

```
   IG's servers
        ▲
        │  (all IG calls)
       ig ── logs in, chooses the account, handles IG's errors
        │
        ▼  live prices
  prices ──────► candles
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
2. **Prices feed candles.** The prices part receives live GBPUSD prices from IG through the IG part and builds them into candles of every size.
3. **The analyser reads candles, levels and the rejection part,** and decides which of the five market states the market is in and which strategies are allowed.
4. **A strategy's trade idea passes the safety rules,** which check trade size, how many trades are open, trading hours, big news and the off switch. An idea that fails any check is dropped.
5. **Then it goes to the order sender,** which sends it to IG through the IG part, with a stop loss and take profit attached.
6. **The trade manager looks after the trade until it closes.** It also closes trades at 20:30 and before big news when the safety part says so.
7. **Everything is recorded and shown on the dashboard, with Telegram alerts.**

## Rules that hold everywhere

- No part except `ig/` talks to IG's servers, and no part except `orders/` asks it to place, change or close a trade.
- IG's default account is never changed: other bots share this IG login.
- Secrets (passwords, keys, tokens, account numbers) are never printed, logged or committed.
- Every order has a stop loss and a take profit.
- The bot only ever touches its own trades.
- No trade is held overnight.
- All numbers come from `config/settings.toml`; none are written into the code. The one exception is the login-failure exit code (78), which is fixed on purpose so it always matches the service file.
