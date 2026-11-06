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
| `market_hours.opens_at` | The time it opens, in `opens_time_zone`. From IG's page and IG's own candles (see below). | 21:00 |
| `market_hours.opens_time_zone` | The time zone of `opens_at`. IG's open follows UK time all year (see below). | `Europe/London` (UK time) |
| `market_hours.closes_day` | The day IG's GBPUSD market closes each week. | Friday |
| `market_hours.closes_at` | The time it closes, in `closes_time_zone`: the last 5-minute candle ends then. | 17:00 |
| `market_hours.closes_time_zone` | The time zone of `closes_at`. IG's close follows New York time (see below): 22:00 UK time most of the year, 21:00 UK time in the weeks when US clocks are on summer time and the UK's are not. This is the one setting that is not in UK time. | `America/New_York` |
| `stream.reconnect_waits_seconds` | After the price stream drops, how long to wait before each reconnect, in order. After the last one, every further wait is the last value. Must go up. | 5, 10, 20, 40, 80, 160, 300 seconds |
| `stream.no_prices_warning_seconds` | Write a warning if no prices arrive for this long while the market is open. | 120 seconds |
| `stream.healthy_after_minutes` | Once the stream has stayed connected this long, the reconnect waits start again from the first one, and one more controlled re-login is allowed. | 60 minutes |
| `candles.folder` | Where the candle store is kept. | `/opt/autobot/data/candles` |
| `candles.hour_starts_at_minute` | 1-hour candles start at this many minutes past each hour. | 0 (on the hour) |
| `candles.four_hour_starts_at` | 4-hour candles start at this time and every 4 hours after it. Must line up with `day_starts_at`. | 00:00 (so 00:00, 04:00, 08:00, 12:00, 16:00, 20:00) |
| `candles.day_starts_at` | Daily candles start and end at this UK time. Midnight, to match IG's own daily candles. | 00:00 |
| `candles.week_starts_day` | Weekly candles start on this day at `day_starts_at`. | Sunday |
| `candles.join_opening_stretch` | `false`: like IG, the first candle of the week starts at Sunday's open, so there is a short Sunday daily candle (21:00 to midnight UK) and a short first 4-hour candle. `true`: that stretch is joined onto the following candle instead. | `false` |
| `candles.wait_for_late_candle_seconds` | A 1-hour, 4-hour, daily or weekly candle that is missing some 5-minute candles is built only after waiting this long past its end (unless a later 5-minute candle has already arrived). | 300 seconds |
| `candles.compress_after_days` | Candle files older than this many days are compressed. Candles are never deleted. | 30 days |
| `housekeeping.log_folder` | Where log files are written. | `/opt/autobot/logs` |
| `housekeeping.log_max_file_mb` | A new log file is started when the current one reaches this size. | 10 MB |
| `housekeeping.log_new_file_every_hours` | A new log file is also started when the current one is this old. | 24 hours |
| `housekeeping.log_keep_files` | How many old log files are kept for each log. Older ones are deleted. | 20 |
| `housekeeping.log_max_age_days` | Old log files older than this are deleted. | 30 days |
| `housekeeping.min_free_disk_mb` | Write a warning if free disk space falls below this. | 2048 MB |
| `history.folder` | Where the history door keeps its records: the points ledger, IG's last figures, the daily record and the block marker. | `/opt/autobot/data/history` |
| `history.weekly_budget_points` | The bot's own budget for IG historical prices: the most points it may use in any 7 days (one point per candle). IG's own allowance is 10,000 a week; this is kept well below it, and may not be set above 5,000. | 4000 points |
| `history.min_ig_allowance_remaining` | Safety floor: a history request is refused if IG's last reported remaining allowance, less the request, would fall below this. | 2000 points |
| `history.max_points_per_request` | The biggest history request allowed. | 500 points |
| `history.min_block_hours` | After IG refuses a history request because the allowance is used up, nothing more is asked for at least this long (longer if IG's reset time is later). | 24 hours |

## Where the market hours come from

The rule is: **IG's GBPUSD market opens on Sunday at 21:00 UK time and closes on Friday at 17:00 New York time**, with no daily break. In UK time the close is 22:00 most of the year, but 21:00 in the few weeks each year when US clocks are on summer time and the UK's are not (from the second Sunday of March to the last Sunday of March, and from the last Sunday of October to the first Sunday of November).

It comes from two sources.

**1. IG's published hours.** IG Help Centre, **"Forex spread betting product details"**, note 1 (page dated 8 September 2026, read on 6 November 2026):

> "Normal dealing hours for all pairs are from 21.00 (London time) on Sunday until 21.59 (London time) on Friday, with the exception of emerging-market pairs, which operate on different schedules."
>
> "All dealing times listed are London times." … "Please note that Daylight Savings Time in the UK or the country of origin may cause the times shown to be imprecise."

https://www.ig.com/uk/help-and-support/spread-betting-and-cfds-5064504a/products-markets-and-trading-hours-008e7240/forex-spread-betting-product-details-3134d533

**2. IG's own 5-minute candles** from the one-off history fill (25 October to 6 November 2026), looking at IG's first and last candle each week:

| What IG's candles showed | UK time | New York time |
|---|---|---|
| First candle, Sunday 25 October | 21:00 GMT | 17:00 EDT |
| Last candle ended, Friday 30 October | 21:00 GMT | 17:00 EDT |
| First candle, Sunday 1 November | 21:00 GMT | 16:00 EST |
| Every weeknight, 21:00 to 22:55 UK time | all 24 candles present | (no daily break) |

The week of 25 October is one of the weeks when US clocks were still on summer time but the UK's were not.

- **The open follows UK time.** It was 21:00 UK on both Sundays, although New York time was 17:00 one week and 16:00 the next.
- **The close follows New York time.** On Friday 30 October IG's last candle ended at 21:00 GMT (17:00 New York), not at 22:00 as IG's page says. IG's page was written in summer, when 17:00 New York is 22:00 UK time ("until 21.59"), so the page and the candles agree.
- **These three rules were tested against the evidence:**

| Rule | 25 Oct open | 30 Oct close | 1 Nov open |
|---|---|---|---|
| IG's page as written (21:00 UK / 22:00 UK) | fits | **wrong** | fits |
| Both in New York time (16:00 / 17:00 New York) | **wrong** | fits | fits |
| **21:00 UK / 17:00 New York (used)** | fits | fits | fits |

**Not yet seen:** a Friday close in normal winter time. The rule says 22:00 GMT, the first being 6 November 2026. The data from the fill ends at 20:00 that day, because that is when the fill ran. The reopen on Sunday 8 November at 21:00 GMT will be checked live.

**Holidays.** IG does not open on Christmas Day or New Year's Day, and hours can be shorter around UK and US holidays. Those days are not in the settings, so they will show up as gaps in the store checks. They are warnings only; nothing is filled automatically.

## How the candle boundaries were chosen

The boundaries **match IG's own candles**. This was checked against IG's daily candles from the one-off history fill (25 October to 6 November 2026).

- **Daily candles run from midnight to midnight UK time (00:00 to 00:00),** exactly as IG's do.
  - IG's daily candles started at 00:00 UK time every day, including 00:00 BST on Sunday 25 October, just before the clocks changed.
  - Daily candles built from the bot's own stored 5-minute candles on the same midnight boundaries matched IG's on **all 8 prices for all 11 complete days**. The twelfth, Friday 6 November, was still in progress when IG was asked.
- **There is a short Sunday daily candle,** 21:00 to midnight UK, because IG has one. (`candles.join_opening_stretch = false`.)
- **Friday's daily candle ends at the close:** 22:00 UK, or 21:00 UK when 17:00 New York is 21:00 UK.
- **1-hour candles start on the hour.** UK time and UTC differ by whole hours, so an hour is the same in both.
- **4-hour candles start at 00:00, 04:00, 08:00, 12:00, 16:00 and 20:00 UK time,** so six fit into each day. The first of the week runs 21:00 to midnight on Sunday.
- **Weekly candles run from Sunday's open to Friday's close.**
- **Each candle file is named after the UTC date of the candle's start.** In summer, a UK day starts at 23:00 UTC the evening before, so that day's daily candle is in the previous date's file.

**The earlier layout.** Until 6 November 2026 the boundaries were 22:00 to 22:00 UK, with Sunday's first hour joined onto Monday. That layout is still available by setting `day_starts_at = "22:00"`, `four_hour_starts_at = "22:00"` and `join_opening_stretch = true`.

The 1-hour, 4-hour, daily and weekly candles first built under that layout were **moved, not deleted**, to `/opt/autobot/data/candles/archive_22h_layout/` on 6 November 2026. They were then rebuilt from the stored 5-minute candles on IG's boundaries. A new bigger candle is never built over one already stored.
