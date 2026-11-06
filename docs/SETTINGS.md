# Settings

All settings live in one file: `config/settings.toml`. The code that loads and checks them is `config/settings_loader.py`.

- All times are **UK time** (Europe/London: GMT in winter, BST in summer), written `"HH:MM"`. (Candles and prices are *stored* in UTC; every time in this file, and every time shown to a person, is UK time.)
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
| `ig.demo_base_url` | IG's demo address. Every IG call goes here. Only the demo address is allowed; the bot refuses to start with any other. | `https://demo-api.ig.com/gateway/deal` |
| `ig.slowed_down_waits_seconds` | When IG slows the bot down, how long to wait before each try again, in order. If IG is still slowing it down after the last wait, the bot stops. | 60, 90, 120, 180 seconds |
| `ig.request_timeout_seconds` | How long to wait for IG to reply to one call before giving up on it. | 30 seconds |
| `market.epic` | IG's name for the one market the bot streams: GBPUSD on the spread bet account. Found with one IG market search (`GET /markets?searchTerm=GBPUSD`) on 6 November 2026: "GBP/USD", expiry DFB (daily funded bet), status TRADEABLE. | `CS.D.GBPUSD.TODAY.IP` |
| `market_hours.opens_day` | The day IG's GBPUSD market opens each week. | Sunday |
| `market_hours.opens_at` | The time it opens (UK time). From IG's own page (see below). | 21:00 |
| `market_hours.closes_day` | The day IG's GBPUSD market closes each week. | Friday |
| `market_hours.closes_at` | The time it closes (UK time). IG says "until 21.59"; written 22:00 because the last 5-minute candle runs 21:55 to 22:00. | 22:00 |
| `stream.reconnect_waits_seconds` | After the price stream drops, how long to wait before each reconnect, in order. After the last one, every further wait is the last value. Must go up. | 5, 10, 20, 40, 80, 160, 300 seconds |
| `stream.no_prices_warning_seconds` | Write a warning if no prices arrive for this long while the market is open. | 120 seconds |
| `stream.healthy_after_minutes` | Once the stream has stayed connected this long, the reconnect waits start again from the first one, and one more controlled re-login is allowed. | 60 minutes |
| `candles.folder` | Where the candle store is kept. | `/opt/autobot/data/candles` |
| `candles.hour_starts_at_minute` | 1-hour candles start at this many minutes past each hour. | 0 (on the hour) |
| `candles.four_hour_starts_at` | 4-hour candles start at this time and every 4 hours after it. Must line up with `day_starts_at`. | 22:00 (so 22:00, 02:00, 06:00, 10:00, 14:00, 18:00) |
| `candles.day_starts_at` | Daily candles start and end at this time. | 22:00 |
| `candles.week_starts_day` | Weekly candles start on this day at `day_starts_at`. | Sunday |
| `candles.wait_for_late_candle_seconds` | A 1-hour, 4-hour, daily or weekly candle that is missing some 5-minute candles is built only after waiting this long past its end (unless a later 5-minute candle has already arrived). | 300 seconds |
| `candles.compress_after_days` | Candle files older than this many days are compressed. Candles are never deleted. | 30 days |
| `housekeeping.log_folder` | Where log files are written. | `/opt/autobot/logs` |
| `housekeeping.log_max_file_mb` | A new log file is started when the current one reaches this size. | 10 MB |
| `housekeeping.log_new_file_every_hours` | A new log file is also started when the current one is this old. | 24 hours |
| `housekeeping.log_keep_files` | How many old log files are kept for each log. Older ones are deleted. | 20 |
| `housekeeping.log_max_age_days` | Old log files older than this are deleted. | 30 days |
| `housekeeping.min_free_disk_mb` | Write a warning if free disk space falls below this. | 2048 MB |

## Where the market hours come from

IG Help Centre, **"Forex spread betting product details"**, note 1 (page dated 8 September 2026, read on 6 November 2026):

> "Normal dealing hours for all pairs are from 21.00 (London time) on Sunday until 21.59 (London time) on Friday, with the exception of emerging-market pairs, which operate on different schedules."
>
> "All dealing times listed are London times."

https://www.ig.com/uk/help-and-support/spread-betting-and-cfds-5064504a/products-markets-and-trading-hours-008e7240/forex-spread-betting-product-details-3134d533

The same page lists no daily break for GBP/USD. IG's own market details call could have given the hours, but this stage allows only the one market search call, so the hours come from IG's published page instead.

Two things to know:

- **Clock changes.** The same page says: "Daylight Savings Time in the UK or the country of origin may cause the times shown to be imprecise." For a few weeks each year (March, and late October to early November) the UK and US clocks change on different dates, and the real open or close may move by an hour. If that happens, the store checks will show it as a gap (or a candle outside market hours). The times here can then be corrected.
- **Holidays.** IG does not open on Christmas Day or New Year's Day, and hours can be shorter around UK and US holidays. Those days are not in the settings, so they will show up as gaps in the store checks. They are warnings only; nothing is filled.

## How the candle boundaries were chosen

- **1-hour candles start on the hour.** UK time and UTC differ by whole hours, so an hour is the same in both. This is the usual choice and matches IG's charts.
- **Daily candles run from 22:00 to 22:00 UK time.** The forex day is normally taken to end at 5pm New York time, which is 22:00 UK time for most of the year. It is also exactly when IG's market closes on Friday. So the last daily candle of the week ends at the close, and each week has five daily candles, Monday to Friday. (Midnight would have given a small sixth candle on Sunday night and cut the evening session in two.)
- **The first hour of the week is joined onto Monday.** IG opens at 21:00 on Sunday, an hour before the 22:00 boundary. Rather than make a one-hour "Sunday" daily candle, that hour is joined onto Monday's daily candle, which therefore runs from Sunday 21:00 to Monday 22:00. In the same way, the first 4-hour candle of the week runs from Sunday 21:00 to Monday 02:00, and the weekly candle starts at Sunday 21:00.
- **4-hour candles start at 22:00, 02:00, 06:00, 10:00, 14:00 and 18:00 UK time,** so that exactly six of them fit into each day.
- **Weekly candles run from Sunday's open to Friday's close.** No candle ever runs past Friday's close.
- **Each candle file is named after the UTC date of the candle's start.** For example, Tuesday's daily candle starts at 22:00 on Monday, so it is in Monday's file.
