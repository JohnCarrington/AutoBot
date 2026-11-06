# Settings

All settings live in one file: `config/settings.toml`. The code that loads and checks them is `config/settings_loader.py`.

- All times are **UK time** (Europe/London: GMT in winter, BST in summer), written `"HH:MM"`.
- If any setting is missing, unknown, or has an invalid value, the bot **refuses to start** and says exactly which setting is wrong.
- To check the settings file: `.venv/bin/python -m config`
- Every setting in the file must have a row here. A test fails if one is missing.

| Setting | What it does | Value |
|---|---|---|
| `account.pair` | The only market the bot trades. | `GBPUSD` |
| `account.account_type` | Which IG account to use. Only the demo account is allowed for now. | `demo` |
| `prices.candle_timeframes` | The candle sizes built from live prices: tick, 5-minute, 1-hour, 4-hour, daily and weekly. | `tick, 5m, 1h, 4h, 1d, 1w` |
| `trade.size_gbp_per_pip` | Trade size: how many pounds each pip of movement is worth. | £10 per pip |
| `trade.stop_loss_pips` | Stop loss sent with every trade, for every strategy. | 6 pips |
| `trade.take_profit_pips` | Take profit sent to IG with every trade. (The bot may close earlier itself; this is the backstop.) | 100 pips |
| `hours.timezone` | The time zone all times are in. Must be UK time. | `Europe/London` |
| `hours.new_trades_from` | Earliest time a new trade may be opened. | 06:00 |
| `hours.new_trades_until` | Latest time a new trade may be opened. | 20:30 |
| `hours.close_all_trades_at` | Any trade still open is closed at this time. | 20:30 |
| `hours.hold_overnight` | Whether trades may be held overnight. Must be `false`; the bot refuses to start otherwise. | `false` (never) |
| `news.big_news_no_new_trades_before_minutes` | No new trades from this many minutes before big news. | 15 minutes |
| `news.big_news_no_new_trades_after_minutes` | No new trades until this many minutes after big news. | 30 minutes |
| `news.big_news_close_trades_before_minutes` | Open trades are closed this many minutes before big news. | 15 minutes |
| `news.ignore_medium_and_small_news` | Medium and small news are ignored; only big news counts. | `true` |
| `limits.max_open_trades_per_strategy` | How many trades each strategy may have open at once. | 1 |
| `limits.bollinger_bounce_extra_opposite_direction_trades` | The Bollinger band bounce may also have this many trades open in the opposite direction (so up to 1 buy and 1 sell). | 1 |
| `levels.line_up_within_pips` | Two levels "line up" when they are within this many pips of each other. | 5 pips |
| `levels.turning_levels_lookback_weeks` | How far back to look for recent turning levels. | 2 weeks |
| `reversal_watch.times` | Times of day when a reversal is watched for. | 10:00, 11:00, 13:00, 14:00, 16:00, 17:00 |
| `reversal_watch.minutes_before` | The watch starts this many minutes before each time. | 20 minutes |
| `reversal_watch.minutes_after` | The watch ends this many minutes after each time. | 20 minutes |
| `bounce.reversal_candle_within_candles_of_pierce` | A bounce needs a reversal candle within this many candles of the candle that pierced the band. | 3 candles |
| `bounce.confirmation_candle_within_candles_of_reversal` | A bounce needs a confirmation candle within this many candles of the reversal candle. | 3 candles |
| `slow_grind.min_pause_candles` | A slow grind's pause must last at least this many candles. | 3 candles |
| `ema_pullback.setup_expires_after_minutes` | An EMA pullback setup that has not triggered is dropped after this long. | 20 minutes |
| `ema_pullback.entry_beyond_pips` | Entry is this many pips beyond the high (for a buy) or low (for a sell) of the candles before the pullback. | 3 pips |
| `ema_pullback.entry_lookback_candles` | How many candles before the pullback are used to find that high or low. | 5 candles |
| `possible_reversal.min_trend_move_pips` | A possible reversal only counts if the trend before it moved at least this far. | 30 pips |
| `range_trade.close_percent_at_opposite_band` | Share of a range trade closed when price reaches the opposite band. | 50% |
