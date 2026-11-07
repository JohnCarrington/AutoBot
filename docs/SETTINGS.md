# Settings

The settings live in `config/settings.toml`, except a few **switches**, which live in `.env` next to the IG secrets (see "Switches in .env" below). The code that loads and checks them is `config/settings_loader.py` and `config/switches.py`.

- All times are **UK time** (Europe/London: GMT in winter, BST in summer), written `"HH:MM"`. (Candles and prices are *stored* in UTC; every time in this file, and every time shown to a person, is UK time.)
- **One exception:** the four session times under `[levels]` are in **UTC**, as the owner gave them (`levels.sessions_time_zone`).
- If any setting is missing, unknown, or has an invalid value, the bot **refuses to start** and says exactly which setting is wrong.
- To check the settings file and the switches: `.venv/bin/python -m config`
- Every setting in the file, and every switch in `.env`, must have a row here. A test fails if one is missing.

| Setting | What it does | Value |
|---|---|---|
| `account.account_type` | Which IG account to use. Only the demo account is allowed for now. | `demo` |
| `prices.candle_timeframes` | The candle sizes built from live prices: tick, 5-minute, 1-hour, 4-hour, daily and weekly. | `tick, 5m, 1h, 4h, 1d, 1w` |
| `trade.size_gbp_per_pip` | Trade size: how many pounds each pip of movement is worth. | £10 per pip |
| `hours.timezone` | The time zone all times are in. Must be UK time. | `Europe/London` |
| `hours.close_all_trades_at` | Any trade still open is closed at this time. | 20:30 |
| `hours.hold_overnight` | Whether trades may be held overnight. Must be `false`; the bot refuses to start otherwise. | `false` (never) |
| `news.big_news_no_new_trades_before_minutes` | No new trades from this many minutes before big news. | 15 minutes |
| `news.big_news_no_new_trades_after_minutes` | No new trades until this many minutes after big news. | 30 minutes |
| `news.big_news_close_trades_before_minutes` | Open trades are closed this many minutes before big news. | 15 minutes |
| `news.ignore_medium_and_small_news` | Medium and small news are ignored; only big news counts. | `true` |
| `limits.max_open_trades_per_strategy` | How many trades each strategy may have open at once. | 1 |
| `limits.bollinger_bounce_extra_opposite_direction_trades` | The Bollinger band bounce may also have this many trades open in the opposite direction (so up to 1 buy and 1 sell). | 1 |
| `chart.price` | The price every level and indicator is worked out from: `sell` (IG's bid), to match Johnny's IG chart, which is set to the sell price. Daily candles run midnight to midnight UK (`candles.day_starts_at`). Trades still open and close at IG's real buy or sell price as normal. Must be `sell` or `buy`. | `sell` |
| `levels.line_up_within_pips` | Two levels "line up" when they are within this many pips of each other. | 5 pips |
| `levels.turning_levels_lookback_weeks` | How far back to look for recent turning levels. | 2 weeks |
| `levels.folder` | Where the current list of levels is written (`current.json`) for the rest of the bot to read. On the server only, not in git. | `/opt/autobot/data/levels` |
| `levels.level_decimals` | Levels worked out by a formula (the pivots) are written to this many decimal places of a point, rounding halves up. IG shows GBPUSD to 1 decimal place of a point. | 1 |
| `levels.round_number_every_pips` | Round numbers are every price that is a multiple of this many pips: with 50, every price ending in 00 or 50 (1.3400, 1.3450, ...). | 50 pips |
| `levels.round_numbers_within_pips` | Only round numbers within this many pips above or below the latest sell close are listed. **Starting value, for the owner to confirm.** | 150 pips |
| `levels.sessions_time_zone` | The time zone of the four session times below. **These times are in UTC, not UK time** (the exception to the rule at the top of this page), as the owner gave them. Must be `UTC`. | `UTC` |
| `levels.london_session_from` | Start of the London session, for the London session high and low (UTC). **Starting value from AutoBot 161, for the owner to confirm.** | 07:00 UTC |
| `levels.london_session_until` | End of the London session (UTC); a candle starting at this time is not in it. **Starting value from AutoBot 161, for the owner to confirm.** | 12:00 UTC |
| `levels.new_york_session_from` | Start of the New York session, for the New York session high and low (UTC). **Starting value from AutoBot 161, for the owner to confirm.** | 12:00 UTC |
| `levels.new_york_session_until` | End of the New York session (UTC); a candle starting at this time is not in it. **Starting value from AutoBot 161, for the owner to confirm.** | 21:00 UTC |
| `levels.turning_candles_each_side` | Turning levels, rule 1 and 2 (`docs/LEVELS.md`): an hourly high must be higher than this many hourly candles before it and not lower than this many after it (a low: the same, upside down). **Starting value, for the owner to confirm.** | 3 candles |
| `levels.turning_min_move_pips` | Turning levels, rule 3: after the high (low), price must move at least this many pips down (up) from it ... **Starting value, for the owner to confirm.** | 20 pips |
| `levels.turning_move_within_candles` | Turning levels, rule 3: ... within this many hourly candles after it. **Starting value, for the owner to confirm.** | 6 candles |
| `reversal_watch.times` | Times of day when a reversal is watched for. | 10:00, 11:00, 13:00, 14:00, 16:00, 17:00 |
| `reversal_watch.minutes_before` | The watch starts this many minutes before each time. | 20 minutes |
| `reversal_watch.minutes_after` | The watch ends this many minutes after each time. | 20 minutes |
| `bounce.reversal_candle_within_candles_of_pierce` | A bounce needs a reversal candle within this many candles of the candle that pierced the band or reached a level. | 3 candles |
| `bounce.confirmation_candle_within_candles_of_reversal` | A bounce needs a confirmation candle within this many candles of the reversal candle. | 3 candles |
| `slow_grind.min_pause_candles` | A slow grind's pause must last at least this many candles. | 3 candles |
| `ema_pullback.setup_expires_after_minutes` | An EMA pullback setup that has not triggered is dropped after this long. | 20 minutes |
| `ema_pullback.entry_beyond_pips` | Entry is this many pips beyond the high (for a buy) or low (for a sell) of the candles before the pullback. | 3 pips |
| `ema_pullback.entry_lookback_candles` | How many candles before the pullback are used to find that high or low. | 5 candles |
| `possible_reversal.min_trend_move_pips` | A possible reversal only counts if the trend before it moved at least this far. | 30 pips |
| `range_trade.close_percent_at_opposite_band` | Share of a range trade closed when price reaches the opposite band. | 50% |
| `range_trade.rejection_candle_within_candles` | Range trade (and the shared rejection part's range version): the red rejection candle must come within this many candles after the candle that pierced the band. 1 means the very next candle, as the design says. | 1 candle |
| `range_trade.trigger_within_candles` | Range trade: the live price must go below the rejection candle's low within this many candles after the rejection candle. 1 means during the candle after it, as the design says; otherwise the setup expires. | 1 candle |
| `indicators.bollinger_periods` | Bollinger bands: the middle band is the average of this many closes (chart price), as on Johnny's IG chart. | 20 candles |
| `indicators.bollinger_std_devs` | Bollinger bands: the upper and lower bands are this many standard deviations above and below the middle band. | 2 |
| `indicators.ema_periods` | The EMAs worked out on each indicator timeframe, on the chart price, as on Johnny's IG chart: 7, 13 and 21 (trend: slope and fanning), 100 and 200. Each starts as the simple average of its first closes, then each value = previous + (close - previous) x 2 / (periods + 1). | 7, 13, 21, 100, 200 |
| `indicators.macd_fast_periods` | MACD fast EMA, as on Johnny's IG chart. MACD line = fast EMA - slow EMA. | 35 candles |
| `indicators.macd_slow_periods` | MACD slow EMA, as on Johnny's IG chart. Must be bigger than the fast one. | 45 candles |
| `indicators.macd_signal_periods` | MACD signal line: the EMA of the MACD line, as on Johnny's IG chart. Histogram = MACD line - signal line. | 30 candles |
| `indicators.rsi_periods` | RSI (Wilder's smoothing, the usual RSI), as on Johnny's IG chart. | 3 candles |
| `indicators.rsi_upper_line` | RSI line above which the market counts as stretched up (design section 2.6). | 70 |
| `indicators.rsi_lower_line` | RSI line below which the market counts as stretched down. | 30 |
| `indicators.timeframes` | The candle sizes the analyser's indicators are worked out on (design section 2.8). | `5m`, `1h` |
| `indicators.history_candles` | How many stored candles, up to the time asked about, are read to work out the indicators. Must cover the longest indicator. | 2000 candles |
| `indicators.warm_up_seed_weight_percent` | An EMA, MACD or RSI starts from a guess (a simple average). It counts as ready once that guess makes up no more than this percent of its value; until then it is "warming up" and the analyser's data is not ready. With 2: a 100 EMA needs 296 candles, a 200 EMA 592, the MACD 134, the RSI 14 (`docs/ANALYSER.md`). **Starting value, for Johnny to confirm.** | 2% |
| `analyser.direction_ema_timeframe` | Direction rule (design section 2.3): the candle size of the EMA price must be above (buy side) or below (sell side), together with the daily pivot. | `5m` |
| `analyser.direction_ema_periods` | Direction rule: which EMA. Must be one of `indicators.ema_periods`. | 100 |
| `analyser.out_of_date_after_minutes` | While the market is open, the analyser's data is out of date (new trades blocked) when the newest stored candle on an indicator timeframe is more than this far behind the newest one that should have finished. A weekend is never out of date. **Starting value, for Johnny to confirm.** | 10 minutes |
| `market_states.narrow_band_max_pips` | Consolidation: the Bollinger bands count as narrow when at most this many pips apart (or when they have narrowed for `narrowing_candles` in a row). **Owner's value, 7 November 2026**; it replaced 161's `CHOP_BB_WIDTH_MAX_PIPS` 8.0. | 14 pips |
| `market_states.narrowing_candles` | Consolidation: the bands also count as narrow when their width has got smaller on each of this many candles in a row. **Owner's value, 7 November 2026.** | 6 candles |
| `market_states.flat_max_pips_per_candle` | A band counts as flat when it moves less than this many pips a candle (over `flat_slope_candles`); at least this much the other way is "sloping". **From 161:** `CHOP_SLOPE_MAX_PIPS_PER_BAR` 0.5. | 0.5 pips a candle |
| `market_states.flat_slope_candles` | How many candles a band's slope is measured over. **From 161:** `CHOP_SLOPE_LOOKBACK` 6. | 6 candles |
| `market_states.ranging_min_band_pips` | Ranging: the bands at least this many pips apart. **From 161:** `NORMAL_STATE_BB_MIN_RANGE_PIPS` 8.0. | 8 pips |
| `market_states.ranging_max_efficiency_ratio` | Ranging: the efficiency ratio (net move / total movement over `efficiency_candles`) below this: price is going back and forth, not trending. **From 161:** `NORMAL_STATE_ER_MAX_RANGE` 0.5. | 0.5 |
| `market_states.efficiency_candles` | Candles the efficiency ratio is worked out over. **From 161:** `REGIME_RANGE_ER_BARS` 10. | 10 candles |
| `market_states.ranging_min_crossings` | Ranging: the close crosses the middle band at least this often within `crossing_candles`. **From 161:** `NORMAL_STATE_CROSS_MIN_RANGE` 2. | 2 |
| `market_states.crossing_candles` | Candles the middle-band crossings are counted over. **From 161:** `REGIME_RANGE_CROSSING_WINDOW` 12. | 12 candles |
| `market_states.ranging_both_bands_candles` | Ranging ("price bounces between the upper and lower band"): both bands reached within this many candles. **New starting value.** | 24 candles |
| `market_states.weave_candles` | Ranging ("the EMAs weave instead of staying stacked"): the order of the 7, 13 and 21 EMAs changed at least once within this many candles. **New starting value.** | 12 candles |
| `market_states.ema100_flat_max_pips` | Ranging ("the 100 EMA is flat"): it moved less than this many pips over `ema100_flat_candles`. **New starting value.** | 3 pips |
| `market_states.ema100_flat_candles` | Candles the 100 EMA's move is measured over. **New starting value.** | 12 candles |
| `market_states.consolidation_quiet_candles` | Consolidation ("price between the bands"): no candle has closed outside the Bollinger bands for this many candles (**owner's rule, 7 November 2026**; it replaced "neither band reached"); also the window for the average body and the green/red balance. | 6 candles |
| `market_states.consolidation_max_body_pips` | Consolidation ("small candles"): average body at most this many pips. **New starting value.** | 3 pips |
| `market_states.consolidation_colour_max_ratio` | Consolidation ("green and red roughly the same size"): the larger of the green and red bodies added up is at most this many times the smaller. **New starting value.** | 2 |
| `market_states.near_band_pips` | "On or near" a band: within this many pips of it. **New starting value.** | 1 pip |
| `market_states.persistence_candles` | Flip-flop protection: a state that depends on a condition (ranging, consolidation, a trend ending past the 100 EMA, a change of trend type, a breakout from a range) needs it for this many candles in a row. Also how many closes in a row cancel an emerging trend: back beyond the level it was rejected at, or back inside the Bollinger bands after a breakout (owner's rule, 7 November 2026; it replaced 161's 3-pip cancel). **From 161:** `PERSISTENCE_BARS` 2. | 2 candles |
| `market_states.evidence_fades_after_candles` | Evidence fades: an emerging trend, trend or possible reversal with nothing new (no new extreme, no new rejection) for this many candles ends. **From 161:** `EVIDENCE_TTL_BARS` 24 (120 minutes). | 24 candles |
| `market_states.ema_stacked_candles` | The 7, 13 and 21 EMAs count as stacked (crossed and turned) once in order for this many candles. **From 161:** rule E7 ("EMA 7>13>21 three bars"). | 3 candles |
| `market_states.failed_bounce_within_pips` | A failed bounce (section 2.5): a candle against the trend whose high (low, for an uptrend) stays at or within this many pips beyond the higher of the 21 EMA and the middle band. **New starting value.** | 1 pip |
| `market_states.push_candles` | Strong push (section 2.5): the candles looked at. **New starting value.** | 6 candles |
| `market_states.push_same_colour_percent` | Strong push: at least this share of those candles are the trend's colour. **New starting value.** | 70% |
| `market_states.push_band_widening_percent` | Strong push ("the bands opening up wide"): the band at least this percent of its width `band_widening_candles` before. **New starting value.** | 150% |
| `market_states.band_widening_candles` | How far back the band width is compared. **New starting value.** | 12 candles |
| `market_states.push_ema_fan_pips` | Strong push ("the 7, 13 and 21 EMAs fanning wide apart"): the 7 and 21 EMAs at least this many pips apart. **New starting value.** | 6 pips |
| `market_states.push_riding_band_closes` | Strong push ("price riding along or just outside the band"): at least this many of the `push_candles` closes on or beyond the outer band. **New starting value.** | 3 |
| `market_states.spike_range_multiple` | A big spike: a candle's high-low range more than this many times the average of the last `spike_average_candles`. **New starting value.** | 3 |
| `market_states.spike_average_candles` | Candles the average range is taken over, for spikes. **New starting value.** | 20 candles |
| `market_states.indicator_warm_up_candles` | The 5-minute candles read before the week's open to start the indicators from. Fixed, so a replay after a restart gives exactly what a run that never stopped gave. | 2000 candles |
| `market_states.folder` | Where every market state change is recorded, one folder per pair (`state_changes.jsonl`, `current.json`). On the server only, not in git. | `/opt/autobot/data/analyser` |
| `rejection.candle_timeframe` | The candle size the shared rejection part watches for pierces, reversal and confirmation candles. | `5m` |
| `rejection.near_level_within_pips` | A candle that comes within this many pips of a level counts the same as a pierce of that level (for a sell: it opens at or below the level and its high gets to within this many pips of it; a buy is the mirror image). Levels only: the Bollinger band needs a real pierce. | 3 pips |
| `rejection.max_spread_pips` | When IG's spread on a candle (the widest buy-minus-sell gap of its open, high, low and close) is over this, the spread is abnormally wide (the 22:00 rollover, news) and that candle's sell highs and lows cannot start a setup or cancel one. The candle is still stored. Chosen from the 2,880 stored candles: normal is 0.9 or 1.5; everything over 3 is at the rollover or at news (`docs/REJECTION.md`). **Starting value, for Johnny to confirm.** | 3 pips |
| `ig.demo_base_url` | IG's demo address. Every IG call goes here. Only the demo address is allowed; the bot refuses to start with any other. | `https://demo-api.ig.com/gateway/deal` |
| `ig.slowed_down_waits_seconds` | When IG slows the bot down, how long to wait before each try again, in order. If IG is still slowing it down after the last wait, the bot stops. | 60, 90, 120, 180 seconds |
| `ig.request_timeout_seconds` | How long to wait for IG to reply to one call before giving up on it. | 30 seconds |
| `pairs.PAIR.epic` | Each pair the bot knows has a `[pairs.<PAIR>]` section (pair names are 6 capital letters). `epic`: IG's name for the pair on the spread bet account. GBPUSD's was found with one IG market search (`GET /markets?searchTerm=GBPUSD`) on 6 November 2026: "GBP/USD", expiry DFB (daily funded bet), status TRADEABLE. For a new pair, `python -m ig.find_market <PAIR>` makes the one search. Two pairs cannot share an epic. | GBPUSD: `CS.D.GBPUSD.TODAY.IP` |
| `pairs.PAIR.pip_size` | One pip in the real exchange rate, written in quotes. 0.0001 for most pairs; 0.01 for pairs with JPY. | GBPUSD: `"0.0001"` |
| `pairs.PAIR.price_scale` | IG's price = real price x this. IG sends GBPUSD spread bet prices as `13354.4` for 1.33544, so 10000. One pip is `pip_size` x `price_scale` of IG's points (GBPUSD: 1 point); every pip distance in these settings is turned into IG's points that way, per pair. Check it against IG's prices before switching a new pair on. | GBPUSD: 10000 |
| `market_hours.opens_day` | The day IG's GBPUSD market opens each week. | Sunday |
| `market_hours.opens_at` | The time it opens, in `opens_time_zone`. From IG's page and IG's own candles (see below). | 21:00 |
| `market_hours.opens_time_zone` | The time zone of `opens_at`. IG's open follows UK time all year (see below). | `Europe/London` (UK time) |
| `market_hours.closes_day` | The day IG's GBPUSD market closes each week. | Friday |
| `market_hours.closes_at` | The time it closes, in `closes_time_zone`: the last 5-minute candle ends then. | 17:00 |
| `market_hours.closes_time_zone` | The time zone of `closes_at`. IG's close follows New York time (see below): 22:00 UK time most of the year, 21:00 UK time in the weeks when US clocks are on summer time and the UK's are not. This is the one setting that is not in UK time. | `America/New_York` |
| `stream.reconnect_waits_seconds` | After the price stream drops, how long to wait before each reconnect, in order. After the last one, every further wait is the last value. Must go up. | 5, 10, 20, 40, 80, 160, 300 seconds |
| `stream.no_prices_warning_seconds` | Write a warning if no prices arrive for this long while the market is open. | 120 seconds |
| `stream.healthy_after_minutes` | Once the stream has stayed connected this long, the reconnect waits start again from the first one, and one more controlled re-login is allowed. | 60 minutes |
| `stream.status_log_minutes` | When the price stream runs as a service, it writes a status line to the log this often: ticks (with how many used a carried-forward price, and how many were skipped) and candles stored since start, the last tick, connections, drops and re-logins. | 60 minutes |
| `candles.folder` | Where the candle store is kept. | `/opt/autobot/data/candles` |
| `candles.hour_starts_at_minute` | 1-hour candles start at this many minutes past each hour. | 0 (on the hour) |
| `candles.four_hour_starts_at` | 4-hour candles start at this time and every 4 hours after it. Must line up with `day_starts_at`. | 00:00 (so 00:00, 04:00, 08:00, 12:00, 16:00, 20:00) |
| `candles.day_starts_at` | Daily candles start and end at this UK time. Midnight, to match IG's own daily candles. | 00:00 |
| `candles.week_starts_day` | Weekly candles start on this day at `day_starts_at`. | Sunday |
| `candles.join_opening_stretch` | `false`: like IG, every candle keeps its normal boundary label even when the market opens later. So there is a short Sunday daily candle labelled Sunday 00:00 UK, holding 21:00 to midnight, and a short first 4-hour candle labelled 20:00. `true`: that stretch is joined onto the following candle instead. | `false` |
| `candles.wait_for_late_candle_seconds` | A 1-hour, 4-hour, daily or weekly candle that is missing some 5-minute candles is built only after waiting this long past its end (unless a later 5-minute candle has already arrived). | 300 seconds |
| `candles.compress_after_days` | Candle files older than this many days are compressed. Candles are never deleted. | 30 days |
| `housekeeping.log_folder` | Where log files are written. | `/opt/autobot/logs` |
| `housekeeping.log_max_file_mb` | A new log file is started when the current one reaches this size. | 10 MB |
| `housekeeping.log_new_file_every_hours` | A new log file is also started when the current one is this old. | 24 hours |
| `housekeeping.log_keep_files` | How many old log files are kept for each log. Older ones are deleted. | 20 |
| `housekeeping.log_max_age_days` | Old log files older than this are deleted. | 30 days |
| `housekeeping.min_free_disk_mb` | Write a warning if free disk space falls below this. | 2048 MB |
| `history.folder` | Where the history door keeps its records: the points ledger, IG's last figures, the daily record and the block marker. | `/opt/autobot/data/history` |
| `history.weekly_budget_points` | The bot's own budget for IG historical prices: the most points it may use in any 7 days (one point per candle). IG's own allowance is 10,000 a week for the whole account, so this one budget is shared by every pair. It may not be set above 8,000 (IG's 10,000 less the 2,000 floor in `history.min_ig_allowance_remaining`). Raised from 4,000 to 7,000 by Johnny on 7 November 2026, for the long history fill. | 7000 points |
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
- **There is a short Sunday daily candle, labelled Sunday 00:00 UK,** because IG has one labelled that way. It holds the candles from the 21:00 open to midnight. (`candles.join_opening_stretch = false`.)
- **Friday's daily candle ends at the close:** 22:00 UK, or 21:00 UK when 17:00 New York is 21:00 UK.
- **1-hour candles start on the hour.** UK time and UTC differ by whole hours, so an hour is the same in both.
- **4-hour candles start at 00:00, 04:00, 08:00, 12:00, 16:00 and 20:00 UK time,** so six fit into each day. The first of the week is labelled Sunday 20:00 and holds 21:00 to midnight.
- **Weekly candles are labelled Sunday 00:00 UK** and hold Sunday's 21:00 open to Friday's close.
- **Each candle file is named after the UTC date of the candle's start.** In summer, a UK day starts at 23:00 UTC the evening before, so that day's daily candle is in the previous date's file.

**The earlier layout.** Until 6 November 2026 the boundaries were 22:00 to 22:00 UK, with Sunday's first hour joined onto Monday. That layout is still available by setting `day_starts_at = "22:00"`, `four_hour_starts_at = "22:00"` and `join_opening_stretch = true`.

The 1-hour, 4-hour, daily and weekly candles first built under that layout were **moved, not deleted**, to `/opt/autobot/data/candles/archive_22h_layout/` on 6 November 2026. They were then rebuilt from the stored 5-minute candles on IG's boundaries. A new bigger candle is never built over one already stored.

## Alerts (Telegram)

| Setting | What it does | Value |
|---|---|---|
| `alerts.telegram_url` | Telegram's address. The bot token and chat ID are secrets in `.env` (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`) and are never printed, logged or committed. | `https://api.telegram.org` |
| `alerts.request_timeout_seconds` | How long to wait for Telegram before giving up on one message (the bot carries on either way). | 15 seconds |
| `alerts.same_problem_every_minutes` | The same problem never sends more than one message in this many minutes. Messages held back are counted and mentioned in the next one. Kept across restarts. | 10 minutes |
| `alerts.folder` | Where the alerts part keeps what it has sent (for the limit above and so a ready message is sent once). On the server only, not in git. | `/opt/autobot/data/alerts` |
| `alerts.daily_ready_at` | The daily "ready" message, Monday to Friday, UK time. | 06:00 |
| `alerts.daily_ready_late_by_minutes` | The daily ready message is sent at the first check at or after `daily_ready_at`, but not if the price service only starts more than this many minutes later that day. | 60 minutes |
| `alerts.sunday_ready_within_minutes` | The Sunday "ready" message is sent when every pair switched on has its first 5-minute candle of the week. If a pair still has none this many minutes after the reopen, a problem alert is sent instead. | 30 minutes |
| `alerts.candles_arriving_within_minutes` | For the ready checks, a pair's candles count as arriving if its newest 5-minute candle finished no more than this many minutes ago. | 10 minutes |

## Switches in .env

These live in `.env` (not in `config/settings.toml`), next to the IG secrets, so they can be changed without touching the settings file. They are checked every time a program starts: a missing or invalid switch stops it with a message naming the switch (never showing a secret). `.env.example` lists them with their current values. Tests never read the real `.env`.

| Setting | What it does | Value |
|---|---|---|
| `PAIRS_ON` | The pairs switched on, comma-separated. The price service streams each one, into its own candle store. Each must have a `[pairs.<PAIR>]` section in `config/settings.toml`. A newly switched-on pair starts with an empty store and is **never** filled from IG's history automatically: that needs the owner's go-ahead (`python -m prices.history_fill plan|go --pair <PAIR>`). | `GBPUSD` |
| `NEW_TRADES_FROM` | Trading hours: the earliest UK time a new trade may be opened, `HH:MM`. Must be earlier than `NEW_TRADES_UNTIL`. | 06:00 |
| `NEW_TRADES_UNTIL` | Trading hours: the latest UK time a new trade may be opened, `HH:MM`. Must not be later than `hours.close_all_trades_at`. | 20:30 |
| `STRATEGY_SLOW_GRIND` | The slow grind strategy, `on` or `off`. | on |
| `STRATEGY_EMA_PULLBACK` | The EMA pullback strategy, `on` or `off`. | on |
| `STRATEGY_BOLLINGER_BOUNCE` | The Bollinger band bounce strategy, `on` or `off`. | on |
| `STRATEGY_RANGE_TRADE` | The range trade strategy, `on` or `off`. | on |
| `STOP_LOSS_PIPS` | The stop loss sent with every trade, for every strategy, in pips: a whole number from 1 to 100. Turned into IG's points per pair (`pairs.PAIR.pip_size` x `pairs.PAIR.price_scale`). Moved from `trade.stop_loss_pips` in `config/settings.toml` on 7 November 2026. | 6 |
| `TAKE_PROFIT_PIPS` | The take profit sent to IG with every trade, in pips: a whole number from 1 to 1000. The bot may close earlier itself; this is the backstop. Moved from `trade.take_profit_pips` on 7 November 2026. | 100 |
