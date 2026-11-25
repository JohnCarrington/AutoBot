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
| `news.finnhub_url` | Finnhub's address for the economic calendar. The API key is a secret in `.env` (`FINNHUB_API_KEY`), never printed, logged or committed. | `https://finnhub.io/api/v1` |
| `news.request_timeout_seconds` | How long to wait for Finnhub before giving up on one fetch. | 20 seconds |
| `news.refresh_hours` | Fetch the calendar again once the copy on disk is this old. So a few requests a day, and a restart does not fetch again while the copy is fresh. | 6 hours |
| `news.retry_minutes` | After a failed fetch, wait at least this long before trying again (never a fast loop). | 60 minutes |
| `news.fetch_days_back` | Each fetch covers this many days before today (UTC) ... | 7 days |
| `news.fetch_days_ahead` | ... and this many days after. | 14 days |
| `news.keep_days` | Releases older than this are dropped from the copy on disk. | 90 days |
| `news.out_of_date_hours` | The calendar is out of date when the last good fetch is older than this: a Telegram problem alert. It does not block trading by itself (design section 6). | 24 hours |
| `news.check_minutes` | How often the price service looks at the copy on disk (it fetches only when `refresh_hours` and `retry_minutes` say so). | 5 minutes |
| `news.alert_every_hours` | While the calendar is missing, out of date, or the key is not set up, the problem alert is sent at most this often. | 6 hours |
| `news.folder` | Where the copy of the calendar is kept (`calendar.json`). On the server only, not in git. | `/opt/autobot/data/news` |
| `news.lower_is_better` | Expected direction (design section 2.4): for most releases a higher forecast than the previous figure is good for the currency; for releases whose name contains one of these, a lower one is. | Unemployment Rate, Jobless Claims, Claimant Count Change |
| `news.country_currencies` | Finnhub's country code for each currency, so a release can be matched to the currencies of each pair switched on. | GB and UK = GBP, US = USD, EU and EMU = EUR, JP = JPY, CH = CHF, CA = CAD, AU = AUD, NZ = NZD |
| `news.table_impacts` | Big, medium and small news come from AutoBot's news table, `config/news_table.toml` (see "News table" below). As on AutoBot 161, the table is applied only to releases Finnhub marks with one of these impacts; every other release is small. | high |
| `limits.max_open_trades_per_strategy` | How many trades each strategy may have open at once. | 1 |
| `limits.bollinger_bounce_extra_opposite_direction_trades` | The first build's bounce (Bollinger bounce 5m) may also have this many trades open in the opposite direction (so up to 1 buy and 1 sell), as on 9 November 2026. | 1 |
| `limits.max_open_trades` | The most trades open at once, not counting the EMA pullback's (design 6). The safety part refuses a new trade that would go over it. | 5 |
| `orders.folder` | The order sender's record: every order, confirmation, refusal and close in `<folder>/<PAIR>/orders.jsonl`, from which the open trades are rebuilt after a restart (design 7). | /opt/autobot/data/orders |
| `orders.expiry` | IG's expiry for the orders (a daily funded spread bet). From the market search of 6 November 2026. | DFB |
| `orders.currency` | IG's currency code for the orders. | GBP |
| `orders.deal_reference_prefix` | Every deal reference the bot makes starts with this (letters only), then the time and a random part (30 characters at most, IG's limit). | AB |
| `orders.unclear_checks` | When IG times out or its answer is unclear, how many times the order sender checks with IG (the deal reference's confirmation, then the open positions) before reporting it. The order is never sent again (design 7). **Starting value.** | 3 |
| `orders.unclear_check_wait_seconds` | The wait between those checks. **Starting value.** | 2 seconds |
| `orders.confirm_attempts` | IG's confirmation of a new order or a close (`GET /confirms/{reference}`) is asked for up to this many times while IG answers 404 (not there yet), as AutoBot 161's `open_sb_now.py`. | 5 |
| `orders.confirm_wait_seconds` | The wait between those attempts, as AutoBot 161. | 1 second |
| `orders.close_retry_seconds` | A close that IG refuses, or does not answer clearly, never closes the trade in the records: the trade stays open and the trade manager tries the close again after this many seconds, for as long as the position is open at IG (each refusal is a Telegram alert with IG's error). **Starting value.** | 30 seconds |
| `orders.stop_move_attempts` | A trail's stop move that IG refuses, or does not answer clearly, is tried again every `orders.close_retry_seconds`, this many attempts in all at that level. Then the bot gives up on that level (one Telegram alert), keeps the stop IG has, and works the trail out again after the next finished 5-minute candle; a later candle's level replaces one still being tried. **Owner's value, 17 November 2026.** | 3 |
| `trade_manager.folder` | Where the trade manager records every decision it makes: `<folder>/<PAIR>/decisions.jsonl` (design 4). | /opt/autobot/data/trade_manager |
| `records.folder` | The bot's records, kept for good (design 9): `<folder>/<PAIR>/trades.jsonl` (every trade, opened and closed), `decisions.jsonl` (every decision), `summaries/daily/` and `summaries/weekly/`; paper trades (while `TRADING` is off) in `<folder>/<PAIR>/paper/`. | /opt/autobot/data/records |
| `trading.daily_summary_at` | The daily summary is written and sent on Telegram each weekday at this UK time. **Owner's value, 8 November 2026.** | 20:35 |
| `trading.pause_file` | The pause switch (design 9): while this file exists, no new trade is sent; open trades are still run. The dashboard will create and remove it. | /opt/autobot/data/control/pause_new_trades |
| `dashboard.port` | The dashboard's data service listens on 127.0.0.1 at this port only; nginx (on the Tailscale address, port 3000) is the only way in (design 9). | 8766 |
| `dashboard.session_days` | The signed session cookie lasts this many days (as AutoBot 161). | 30 days |
| `dashboard.login_failures_per_minute` | More wrong passwords than this in a minute and logging in is refused for the rest of that minute. **Starting value.** | 5 |
| `dashboard.status_folder` | The price service writes the trading engine's status for the dashboard here (`<folder>/<PAIR>/status.json`). | /opt/autobot/data/trading |
| `dashboard.status_every_seconds` | How often that status is written. **Starting value.** | 5 seconds |
| `dashboard.status_stale_seconds` | The dashboard warns when the status is older than this (the price service may not be running). **Starting value.** | 30 seconds |
| `safety.big_friday_move_pips` | One view at a time (design 6): on the Monday after a Friday whose daily candle (sell price, open to close, UK day) moved at least this many pips, up or down, no reversal trade (a Bollinger bounce, or a level reversal against the analyser's trend direction) against the direction that reclaims Friday's move (Friday fell: no reversal sell; Friday rose: no reversal buy), all day. **Owner's value, 9 November 2026** (the value tested in `docs/research/one_view_20261109.md`). | 80 pips |
| `safety.max_total_risk_gbp` | Total risk across all open trades (each trade's stop distance x its size, the new trade included) may not be more than this (design 6). **Owner's value, 8 November 2026: set so it is never reached.** | £100,000 |
| `safety.margin_per_trade_gbp` | A new trade is allowed only if the account's available funds (IG's account details, read at start-up and whenever a trade opens or closes, never before each trade) are at least this: the margin for one trade at £10 a pip (design 6). **Owner's value, 8 November 2026.** | £5,000 |
| `safety.ig_stop_refusal_reasons` | IG's reasons (in its deal confirmation) that mean it refused a trade because of its stop: the bot then fetches IG's minimum stop distance once, records it and sends a Telegram alert (design 7). **Starting value, to be confirmed against IG when the order sender is built.** | ATTACHED_ORDER_LEVEL_ERROR |
| `safety.ig_funds_refusal_reasons` | IG's reasons that mean it refused a trade for lack of funds: a Telegram alert (design 7). **Starting value, to be confirmed against IG when the order sender is built.** | INSUFFICIENT_FUNDS |
| `safety.folder` | Where the bot records IG's minimum stop distance each time IG refuses a trade because of its stop (`ig_min_stop_refusals.jsonl`). | /opt/autobot/data/safety |
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
| `bounce.pierce_beyond_pips` | The Bollinger bounce (design 3.3): a 5-minute candle's high must go MORE than this many pips above the hourly upper Bollinger band (20, 2), as the hourly chart showed the band at that moment (its low below the lower band, for a buy). That candle, red for a sell (green for a buy), is the rejection candle. **Owner's value, 15 November 2026.** | 3 pips |
| `bounce.confirmation_within_candles` | The confirmation candle must close beyond the rejection candle's low (sell) or high (buy) within this many candles of it, or the setup expires. **Owner's value, 15 November 2026.** | 3 candles |
| `bounce.trail_from_pips` | Once a Bollinger bounce has been this many pips in profit, its stop trails: after each finished 5-minute candle it is moved at IG to a tenth of a pip beyond the last `bounce.trail_candles` candles (a sell: above their highest buy price; a buy: below their lowest sell price), only ever closer. **Owner's value, 15 November 2026.** | 12 pips |
| `bounce.trail_candles` | The number of finished 5-minute candles the trail follows. **Owner's value, 15 November 2026.** | 3 candles |
| `bounce.near_times` | While the switch `BOUNCE_ONLY_NEAR_TIMES` is on, a Bollinger bounce opens only near one of these UK clock times (judged at the moment it opens). **Owner's times, 15 November 2026.** | 10:00, 14:00, 16:00 |
| `bounce.near_times_within_minutes` | How near: this many minutes either side of one of `bounce.near_times`, both ends included (60: 09:00 to 11:00, 13:00 to 17:00). **Owner's value, 15 November 2026.** | 60 minutes |
| `slow_grind.min_pause_candles` | A slow grind's pause must last at least this many candles. **Owner's value, 8 November 2026.** | 2 candles |
| `slow_grind.ema_periods` | The EMA a slow grind's pause must stay below (above, for a buy); a candle closing beyond it cancels the setup (design 3.1). | 21 |
| `slow_grind.stop_loss_pips` | The slow grind's own stop loss, sent to IG with each of its trades (design 4). **Owner's value, 8 November 2026.** | 15 pips |
| `slow_grind.take_profit_pips` | The slow grind's own take profit, sent to IG with each of its trades; a trade opened on a UK day with big news for the pair gets `TAKE_PROFIT_PIPS` instead (design 4). **Owner's value, 8 November 2026.** | 20 pips |
| `slow_grind.lock_from_pips` | The slow grind's profit lock (design 4): once a trade has been this many pips in profit... | 15 pips |
| `slow_grind.lock_at_pips` | ...it is closed if price comes back to this many pips in profit. Must be smaller than `lock_from_pips`. **Owner's values, 8 November 2026.** | 10 pips |
| `slow_grind.week_open_no_new_trades_minutes` | No new slow grind trade in the first this many minutes after the market opens on Sunday (design 6). **Owner's value, 8 November 2026.** | 15 minutes |
| `slow_grind.rollover_no_new_trades_from` | No new slow grind trade from this UK time... | 21:55 |
| `slow_grind.rollover_no_new_trades_until` | ...until this UK time (the 22:00 rollover; design 6). It also opens none from `hours.close_all_trades_at` (20:30) to midnight UK. **Owner's values, 8 November 2026.** | 22:15 |
| `ema_pullback.setup_expires_after_minutes` | An EMA pullback setup that has not triggered is dropped after this long. | 20 minutes |
| `ema_pullback.entry_beyond_pips` | Entry is this many pips beyond the high (for a buy) or low (for a sell) of the candles before the pullback. | 3 pips |
| `ema_pullback.entry_lookback_candles` | How many candles before the pullback are used to find that high or low. | 5 candles |
| `ema_pullback.take_profit_pips` | The EMA pullback's own take profit, sent to IG with each of its trades (every other strategy uses `TAKE_PROFIT_PIPS`). **Owner's value, 7 November 2026.** | 30 pips |
| `ema_pullback.fast_ema_periods` | The 5-minute EMA the pullback must reach (design 3.2). | 8 |
| `ema_pullback.mid_ema_periods` | The 5-minute middle EMA (price may cross it; named in design 3.2, used in no rule). | 13 |
| `ema_pullback.slow_ema_periods` | A 5-minute candle closing beyond this EMA cancels the setup. | 21 |
| `ema_pullback.hourly_fast_ema_periods` | Step 0, the hourly trend: the fast hourly EMA. From AutoBot 161's EMA pullback service. | 8 |
| `ema_pullback.hourly_mid_ema_periods` | The middle hourly EMA. | 13 |
| `ema_pullback.hourly_slow_ema_periods` | The slow hourly EMA. For a buy the three are in order (8 above 13 above 20) and each rose since the hourly candle before. | 20 |
| `ema_pullback.hourly_slope_candles` | Each hourly EMA's slope is measured over this many finished hourly candles. | 3 hourly candles |
| `ema_pullback.hourly_min_slope_pips_per_hour` | Each hourly EMA's slope must be at least this. 161's value. | 0.16 pips an hour |
| `ema_pullback.hourly_min_gap_fast_mid_pips` | The hourly 8 and 13 EMAs must be at least this far apart. 161's value. | 0.25 pips |
| `ema_pullback.hourly_min_gap_mid_slow_pips` | The hourly 13 and 20 EMAs must be at least this far apart. 161's value. | 0.20 pips |
| `ema_pullback.hourly_history_candles` | Stored hourly candles read to work out the hourly EMAs (enough for them to settle). | 600 hourly candles |
| `ema_pullback.rollover_no_new_trades_from` | No new EMA pullback trade from this UK time... | 21:55 |
| `ema_pullback.rollover_no_new_trades_until` | ...until this UK time (the 22:00 rollover, when IG's spread jumps to about 17 pips). **Owner's decision, 13 November 2026.** | 22:15 |
| `possible_reversal.min_trend_move_pips` | A possible reversal only counts if the trend before it moved at least this far. | 30 pips |
| `range_trade.close_percent_at_opposite_band` | Share of a range trade closed when price reaches the opposite band. | 50% |
| `range_trade.rejection_candle_within_candles` | Range trade (and the shared rejection part's range version): the red rejection candle must come within this many candles after the candle that pierced the band. 1 means the very next candle, as the design says. | 1 candle |
| `range_trade.trigger_within_candles` | Range trade: the live price must go below the rejection candle's low within this many candles after the rejection candle. 1 means during the candle after it, as the design says; otherwise the setup expires. | 1 candle |
| `trend_day.level_above` | The trend-day check (design 2.4): a trend day downwards needs the day's open at or above this level of the previous month (R1, R2 or R3). **Owner's choice, 8 November 2026.** | R2 |
| `trend_day.level_below` | A trend day upwards needs the open at or below this level of the previous month (S1, S2 or S3). **Owner's choice, 8 November 2026.** | S2 |
| `trend_day.rsi_periods` | The daily RSI's periods (Wilder's, at the previous day's close). **Owner's value, 8 November 2026.** | 14 |
| `trend_day.rsi_above` | A trend day downwards needs that RSI above this. **Owner's value, 8 November 2026.** | 70 |
| `trend_day.rsi_below` | A trend day upwards needs that RSI below this. **Owner's value, 8 November 2026.** | 30 |
| `trend_day.rsi_history_candles` | Stored daily candles read to work out the RSI (all the store holds, up to this many; the RSI depends a little on where it starts). | 1000 |
| `level_reversal.level_types` | Level reversal (design 3.6): the levels it trades rejections at, from `S2`, `R2` and `round_number`. **Owner's choice, 8 November 2026.** | S2, R2, round_number |
| `level_reversal.round_numbers_every_pips` | Round numbers count only on a multiple of this many pips (100: the 00s, not the 50s). **Owner's choice, 8 November 2026.** | 100 pips |
| `level_reversal.allowance_pips_r2` | A rejection at R2 counts only if price went no more than this far past it, from the piercing candle to the confirmation candle (design 3.6). **Owner's value, 8 November 2026.** | 12 pips |
| `level_reversal.allowance_pips_s2` | The same at S2. **Owner's value, 8 November 2026.** | 12 pips |
| `level_reversal.allowance_pips_round_number` | The same at a round number ending in 00. **Owner's value, 8 November 2026.** | 5 pips |
| `level_reversal.stop_beyond_furthest_pips` | Its stop: this many pips beyond the furthest point price reached (so the distance from the entry varies). **Owner's value, 8 November 2026.** | 6 pips |
| `level_reversal.take_profit_pips` | Its take profit, in pips from the entry, sent to IG. **Owner's value, 8 November 2026.** | 20 pips |
| `asian_range_breakout.range_from` | Asian range breakout (design 3.7): the Asian range starts with the 5-minute candle at this UK time. **Owner's value, 16 November 2026.** | 00:00 |
| `asian_range_breakout.range_until` | ... and takes every candle before this UK time: the Asian high and low. **Owner's value, 16 November 2026.** | 07:00 |
| `asian_range_breakout.breakout_from` | From this UK time a 5-minute candle closing above the Asian high (a buy) or below the Asian low (a sell) opens a trade at the next candle's open. **Owner's value, 16 November 2026.** | 07:00 |
| `asian_range_breakout.breakout_until` | ... up to this UK time (a candle starting at 09:55 is the last). One trade each way per day. **Owner's value, 16 November 2026.** | 10:00 |
| `asian_range_breakout.stop_loss_pips` | Its stop loss, in pips from the entry, sent to IG. **Owner's value, 16 November 2026.** | 12 pips |
| `pullback_entry.wait_candles` | While `PULLBACK_ENTRY` is on, the breakout and the Asian range breakout do not open on the break: they wait for a candle whose low reaches the 5-minute 8 EMA (a sell: its high) and a close back above it (a sell: below; the same candle may do both); that confirming close must come within this many 5-minute candles after the break candle, and the trade opens at the next candle's open. A close below the 21 EMA (a sell: above) cancels it. Sell price (`strategies/pullback.py`). **Owner's value, 19 November 2026.** | 6 candles |
| `entry_filters.hourly_swing_candles_each_side` | Rule 1, the hourly context (switch `HOURLY_CONTEXT`): a swing high is an hourly candle whose high has this many strictly lower hourly highs on each side (a swing low: strictly higher lows). Finished hourly candles only, sell price. DOWN context: the latest swing high is lower than the one before it, the last hourly close is below the hourly 50 EMA and that EMA is falling; UP: the mirror (`strategies/entry_filters.py`). **Owner's value, 21 November 2026.** | 2 candles |
| `entry_filters.hourly_ema_periods` | Rule 1: the hourly EMA the last finished hourly close is compared with, and whose distance from the entry counts (sell price). **Owner's value, 21 November 2026.** | 50 |
| `entry_filters.hourly_ema_slope_candles` | Rule 1: the hourly 50 EMA is falling when it is lower than this many hourly candles before (rising: higher). **Owner's value, 21 November 2026.** | 6 candles |
| `entry_filters.hourly_context_near_pips` | Rule 1: in a DOWN context no buy opens, and in an UP context no sell opens, when the strategy's entry price is within this many pips (exactly this many included) of the daily pivot or the hourly 50 EMA. Every strategy except the breakout and the Asian range breakout (exempt, owner 21 November 2026). **Owner's value, 21 November 2026.** | 5 pips |
| `entry_filters.ema8_periods` | Rule 2, entry near the 8 EMA (switch `ENTRY_NEAR_EMA8`): the 5-minute EMA used, on the sell price, at the last finished 5-minute candle before the entry. **Owner's value, 21 November 2026.** | 8 |
| `entry_filters.ema8_max_distance_pips` | Rule 2: a sell opens only if the strategy's entry price is no more than this many pips below the 5-minute 8 EMA (at it, above it, or up to this many below); a buy only if no more than this many above it. The slow grind, the breakout, the Asian range breakout and the session sweep are exempt. **Owner's value, 21 November 2026.** | 5 pips |
| `entry_filters.rsi_periods` | Rule 2b, the RSI stretch (switch `RSI_STRETCH`): the 5-minute RSI's periods (Wilder's smoothing, sell price, at the last finished 5-minute candle before the entry). **Owner's value, 21 November 2026.** | 3 |
| `entry_filters.rsi_sell_below` | Rule 2b: no sell opens while the 5-minute RSI 3 is under this. The slow grind, the breakout, the Asian range breakout and the session sweep are exempt. **Owner's value, 21 November 2026.** | 30 |
| `entry_filters.rsi_buy_above` | Rule 2b: no buy opens while the 5-minute RSI 3 is over this (same exemptions). **Owner's value, 21 November 2026.** | 70 |
| `entry_filters.trend_day_from` | Johnny's slow-grind trend day (switch `TREND_DAY_RSI_OFF`): it starts the first time a slow grind trade is in profit (more than 0 pips at the price IG would close it) at any moment from this UK time ... **Owner's value, 21 November 2026.** | 06:00 |
| `entry_filters.trend_day_until` | ... up to this UK time, in that trade's direction. A slow grind trade in the other direction also in profit in this window cancels the trend day for the rest of the day. **Owner's value, 21 November 2026.** | 09:00 |
| `entry_filters.trend_day_ends_at` | The trend day lasts until this UK time (the bot's close). Meanwhile rule 2b does not apply to trades in the trend's direction; trades against it, and rule 1, are unchanged. **Owner's answer, 21 November 2026.** | 20:30 |
| `emerging_ladder.first_from_pips` | Johnny's exit for emerging-trend trades (switch `EMERGING_LADDER`; `trade_manager/manager.py`): for a trade opened while the analyser said "emerging trend" (up or down), once it is this many pips up (as IG closes it: a buy on the sell price, a sell on the buy price, from the price it opened at) ... **Owner's value, 21 November 2026.** | 10 pips |
| `emerging_ladder.first_stop_pips` | ... its stop at IG moves to this many pips up. Never backwards; a tighter trail or stop move is kept. **Owner's value, 21 November 2026.** | 5 pips |
| `emerging_ladder.second_from_pips` | ... once it is this many pips up ... (must be above `first_from_pips`) **Owner's value, 21 November 2026.** | 15 pips |
| `emerging_ladder.second_stop_pips` | ... its stop at IG moves to this many pips up (must be above `first_stop_pips`, and each stop below the pips that move it). Take profit unchanged. **Owner's value, 21 November 2026.** | 10 pips |
| `asian_range_breakout.trail_from_pips` | Its trail: once this many pips in profit, after each finished 5-minute candle the stop is moved at IG to a tenth of a pip beyond the last `trail_candles` candles, only ever closer (as the bounce's). **Owner's value, 16 November 2026.** | 12 pips |
| `asian_range_breakout.trail_candles` | How many finished candles the trail looks back over. **Owner's value, 16 November 2026.** | 3 candles |
| `session_sweep.asian_range_from` | Session sweep (design 3.8): the Asian high and low are the 5-minute candles' from this UK time ... **Owner's value, 16 November 2026.** | 00:00 |
| `session_sweep.asian_range_until` | ... up to this UK time; they count as levels from this time. **Owner's value, 16 November 2026.** | 07:00 |
| `session_sweep.london_range_from` | The London high and low are the candles' from this UK time ... **Owner's value, 16 November 2026.** | 07:00 |
| `session_sweep.london_range_until` | ... up to this UK time, fixed then; they count as levels from this time (the owner's answer 5). **Owner's value, 16 November 2026.** | 12:00 |
| `session_sweep.beyond_pips` | The sweep: price must go at least this far beyond the level before a candle closes back inside it. **Owner's value, 16 November 2026.** | 3 pips |
| `session_sweep.confirmation_within_candles` | The confirmation candle must close beyond the rejection candle's low (sell) or high (buy) within this many candles of it, or the setup expires; price past the rejection candle's other side first cancels it (as the bounce). Owner's answer 8, 16 November 2026. | 3 candles |
| `session_sweep.stop_beyond_furthest_pips` | Its stop: this far beyond the sweep's furthest point (from the first move beyond the level to the entry). Owner's answer 9, 16 November 2026. | 1 pip |
| `session_sweep.min_stop_pips` | ... and never closer to the entry than this. **Owner's value, 16 November 2026.** | 12 pips |
| `session_sweep.trail_from_pips` | Its trail, as `asian_range_breakout.trail_from_pips`. **Owner's value, 16 November 2026.** | 12 pips |
| `session_sweep.trail_candles` | How many finished candles its trail looks back over. **Owner's value, 16 November 2026.** | 3 candles |
| `new_york_open_reversal.move_from` | New York open reversal (design 3.9): the move is measured from the open of the 5-minute candle at this UK time ... **Owner's value, 16 November 2026.** | 07:00 |
| `new_york_open_reversal.move_until` | ... to the close of the last candle before this UK time (owner's answer 11). **Owner's value, 16 November 2026.** | 13:30 |
| `new_york_open_reversal.min_move_pips` | The move must be at least this many pips one way; the trade is against it. **Owner's value, 16 November 2026.** | 30 pips |
| `new_york_open_reversal.window_from` | The rejection candle (red after a rise, green after a fall) and its confirmation candle must both start from this UK time ... **Owner's value, 16 November 2026.** | 13:30 |
| `new_york_open_reversal.window_until` | ... and before this UK time; the trade opens at the next candle's open. One trade a day. **Owner's value, 16 November 2026.** | 15:00 |
| `new_york_open_reversal.confirmation_within_candles` | The confirmation candle must close beyond the rejection candle within this many candles of it; price past the rejection candle's other side first cancels it (as the bounce). Owner's answer 13, 16 November 2026. | 3 candles |
| `new_york_open_reversal.no_trade_if_big_news_at` | No New York open reversal on a day with big news for the pair (the news table) released at this UK time. **Owner's value, 16 November 2026.** | 13:30 |
| `new_york_open_reversal.stop_loss_pips` | Its stop loss, in pips from the entry, sent to IG. **Owner's value, 16 November 2026.** | 12 pips |
| `new_york_open_reversal.trail_from_pips` | Its trail, as `asian_range_breakout.trail_from_pips`. **Owner's value, 16 November 2026.** | 12 pips |
| `new_york_open_reversal.trail_candles` | How many finished candles its trail looks back over. **Owner's value, 16 November 2026.** | 3 candles |
| `breakout.trigger_within_candles` | Breakout (design 3.5): the breakout candle's high (buy) or low (sell) must be broken within this many candles after it, or the setup expires. **Owner's value, 7 November 2026.** | 3 candles |
| `breakout.stop_loss_pips` | The breakout's stop loss, in pips. **Owner's value, 7 November 2026.** 0 means not chosen: `STRATEGY_BREAKOUT` cannot be switched on while it is 0. | 6 pips |
| `breakout.take_profit_pips` | The breakout's take profit, in pips. **Owner's value, 7 November 2026.** 0 means not chosen: `STRATEGY_BREAKOUT` cannot be switched on while it is 0. | 50 pips |
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
| `market_states.ranging_min_band_pips` | Ranging ("the Bollinger bands are close together"): the bands at least this many pips apart. **Owner's value, 7 November 2026** (it replaced 161's `NORMAL_STATE_BB_MIN_RANGE_PIPS` 8.0). | 6 pips |
| `market_states.ranging_max_band_pips` | Ranging ("close together"): the bands at most this many pips apart. **Owner's value, 7 November 2026.** | 18 pips |
| `market_states.ranging_band_flat_max_pips_per_candle` | Ranging ("the Bollinger bands are flat"): the upper band and the lower band each move less than this many pips a candle, over `flat_slope_candles`. **Owner's value, 7 November 2026.** | 0.2 pips a candle |
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
| `market_states.push_colour_body_percent` | Strong push: at least this percent of the total candle body size over the `push_candles` is in the trend's colour (red bodies added up / all bodies added up, for a fall). By body size, so a few big red candles with small green ones between still count (**owner's rule, 7 November 2026**; it replaced a count of candles). The 70 is a new starting value. | 70% |
| `market_states.push_band_widening_percent` | Strong push ("the bands opening up wide"): the band at least this percent of its width `band_widening_candles` before. **New starting value.** | 150% |
| `market_states.band_widening_candles` | How far back the band width is compared. **New starting value.** | 12 candles |
| `market_states.push_ema_fan_pips` | Strong push ("the 7, 13 and 21 EMAs fanning wide apart"): the 7 and 21 EMAs at least this many pips apart. **New starting value.** | 6 pips |
| `market_states.push_riding_band_closes` | Strong push ("price riding along or just outside the band"): at least this many of the `push_candles` closes on or beyond the outer band. **New starting value.** | 3 |
| `market_states.spike_range_multiple` | A big spike: a candle's high-low range more than this many times the average of the last `spike_average_candles`. **New starting value.** | 3 |
| `market_states.spike_average_candles` | Candles the average range is taken over, for spikes. **New starting value.** | 20 candles |
| `market_states.indicator_warm_up_candles` | The 5-minute candles read before the week's open to start the indicators from. Fixed, so a replay after a restart gives exactly what a run that never stopped gave. | 2000 candles |
| `market_states.folder` | Where every market state change is recorded, one folder per pair (`state_changes.jsonl`, `current.json`). On the server only, not in git. | `/opt/autobot/data/analyser` |
| `market_states.strong_level_types` | The levels a confirmed rejection must be at to **start or replace an emerging trend**: the pivot, R1 to R3, S1 to S3, round numbers (every 00 and 50), and the previous day's high or low. A turning level counts only when it lines up with one of these (same group, `levels.line_up_within_pips`); on its own it does not, though it still counts everywhere else (possible reversals, the rejection part). **Owner's rule, 7 November 2026.** | pivot, R1, R2, R3, S1, S2, S3, round_number, previous_day_high, previous_day_low |
| `rejection.candle_timeframe` | The candle size the shared rejection part watches for pierces, reversal and confirmation candles. | `5m` |
| `rejection.near_level_within_pips` | A candle that comes within this many pips of a level counts the same as a pierce of that level (for a sell: it opens at or below the level and its high gets to within this many pips of it; a buy is the mirror image). Levels only: the Bollinger band needs a real pierce. | 3 pips |
| `rejection.max_spread_pips` | When IG's spread on a candle (the widest buy-minus-sell gap of its open, high, low and close) is over this, the spread is abnormally wide (the 22:00 rollover, news) and that candle's sell highs and lows cannot start a setup or cancel one. The candle is still stored. Chosen from the 2,880 stored candles: normal is 0.9 or 1.5; everything over 3 is at the rollover or at news (`docs/REJECTION.md`). **Starting value, for Johnny to confirm.** | 3 pips |
| `rejection.reversal_candle_within_candles_of_pierce` | The shared rejection part's bounce setups (the level reversal and the analyser; not the Bollinger bounce) need a reversal candle within this many candles of the candle that pierced the band or reached a level. | 3 candles |
| `rejection.confirmation_candle_within_candles_of_reversal` | The same setups need a confirmation candle within this many candles of the reversal candle. | 3 candles |
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

### The Structural Trade Planner (`[planner]`, observe only)

| Setting | What it does | Value |
|---|---|---|
| `planner.folder` | Where the Structural Trade Planner (observe only) writes its recommendation (`<folder>/<PAIR>/current.json`) and its full history (`recommendations.jsonl`, append-only). | `/opt/autobot/data/planner` |
| `planner.adr_weekdays` | The planner's average daily range: the average sell high-to-low range of this many finished weekday daily candles, IG's short Sunday candles left out (P-A8). Context only, never a limit. **Owner's value, 17 November 2026.** | 20 |
| `planner.h4_swing_candles_each_side` | A 4-hour swing high is higher than the highs of this many 4-hour candles before it and not lower than this many after it (a low: the mirror), the existing turning-level rule (P-B2). **Owner's value, 17 November 2026.** | 3 |
| `planner.h4_swing_min_move_pips` | ... and price then moves at least this many pips away from it (P-B3). **Owner's provisional value, 17 November 2026**; turns held back only by it are recorded. | 40 pips |
| `planner.h4_swing_move_within_candles` | ... within this many 4-hour candles (P-B4). **Owner's value, 17 November 2026.** | 6 |
| `planner.daily_swing_candles_each_side` | The same for daily swings (P-B5). **Owner's value, 17 November 2026.** | 3 |
| `planner.daily_swing_min_move_pips` | The move for a daily swing (P-B6). **Owner's provisional value, 17 November 2026**; turns held back only by it are recorded. | 110 pips |
| `planner.daily_swing_move_within_candles` | ... within this many daily candles (P-B7). **Owner's value, 17 November 2026.** | 6 |
| `planner.h4_swing_lookback_weeks` | 4-hour swings from this many weeks back are levels on the planner's map (P-B8); the direction always uses the latest swings. **Owner's value, 17 November 2026.** | 8 |
| `planner.daily_swing_lookback_weeks` | The same for daily swings (P-B9). **Owner's value, 17 November 2026.** | 48 |
| `planner.historical_daily_swing_lookback_weeks` | Historical daily swings: daily swings older than `daily_swing_lookback_weeks` are also kept as levels ("historical daily swing low/high"), back this many weeks; 0 = none. Never used for the direction. **Owner's approval, 20 November 2026 (structural-history correction).** | 156 |
| `planner.structure_break_closes` | A 4-hour structural break needs this many closes in a row at least `planner.break_beyond_pips` beyond the last swing (P-B11). **Owner's value, 17 November 2026.** | 1 |
| `planner.zone_width_adr_share` | A zone holds the levels within the larger of `levels.line_up_within_pips` and this share of the ADR of its lowest level (P-C3). **Owner's provisional value, 17 November 2026.** | 0.15 |
| `planner.major_min_families` | A Major zone has at least this many families of evidence, including a daily-or-weekly level (P-C7). **Owner's value, 17 November 2026.** | 3 |
| `planner.moderate_min_families` | A Moderate zone has at least this many families (P-C7). **Owner's value, 17 November 2026.** | 2 |
| `planner.min_entry_class` | The weakest zone class that may be the entry zone (P-C7). **Owner's value, 17 November 2026.** | Moderate |
| `planner.ema_slope_candles` | The 4-hour EMA100 slope (supporting evidence) is over this many 4-hour candles (P-D1). **Owner's value, 17 November 2026.** | 6 |
| `planner.macd_weakening_candles` | Momentum weakening: the 4-hour MACD histogram moves towards zero for this many candles in a row (P-D6). **Owner's value, 17 November 2026.** | 3 |
| `planner.no_new_extreme_hourly_candles` | CORRECTION_LIKELY: no new extreme in this many finished hourly candles (P-D9). **Owner's value, 17 November 2026.** | 3 |
| `planner.failed_breakout_within_candles` | Recorded only: a confirmed zone break that closes back within this many hourly candles is a failed breakout (P-F7). **Owner's value, 17 November 2026.** | 3 |
| `planner.panel_history` | Past recommendations shown on the dashboard's planner panel (P-G3). **Owner's value, 17 November 2026.** | 5 |
| `planner.break_beyond_pips` | A confirmed close beyond a level, for the planner: zone invalidation (FC-02), 4-hour structure breaks and flipped levels need a close at least this many pips beyond. On main the planner reads `hourly_read.break_beyond_pips`; here it is the planner's own setting (owner, 19 November 2026). | 3 pips |
| `stp_technical.enabled` | Write the STP technical forecast (planner/technical.py, observe only) to `planner.folder/<PAIR>/technical.json` and `technical.jsonl` on each planner run. It never feeds the recommendation lifecycle, IG or orders. **Provisional (issue #3, 20 November 2026), for the owner to approve.** | true (switched on by the observe-only deployment, 20 Nov 2026; was false) |
| `stp_technical.h1_ema_period` | The H1 EMA a pullback is measured against (the issue names H1 EMA20), worked out with the bot's own EMA code. **Provisional (issue #3, 20 November 2026), for the owner to approve.** | 20 |
| `stp_technical.rsi_periods` | The RSI period for RSI direction and turns in the technical forecast (the chart's RSI 3 is left as it is). **Provisional (issue #3, 20 November 2026), for the owner to approve.** | 14 |
| `stp_technical.trend_candles` | The H1 EMA trend is its change over this many H1 candles. **Provisional (issue #3, 20 November 2026), for the owner to approve.** | 12 |
| `stp_technical.avg_range_candles` | The H1 average range (the forecast's volatility unit) is the average high-to-low of this many H1 candles. **Provisional (issue #3, 20 November 2026), for the owner to approve.** | 14 |
| `stp_technical.stop_buffer_range_share` | A forecast's stop sits this share of the H1 average range beyond the entry zone, at least `planner.break_beyond_pips`; hypothesised from the PIA First example of 20 November 2026. **Provisional (issue #3, 20 November 2026), for the owner to approve.** | 0.3 |
| `stp_technical.range_lookback_candles` | A range (the grey box) is looked for over this many H1 candles. **Provisional (issue #3, 20 November 2026), for the owner to approve.** | 48 |
| `stp_technical.range_min_tests` | ... its top and bottom each reached at least this many separate times. **Provisional (issue #3, 20 November 2026), for the owner to approve.** | 2 |
| `stp_technical.range_max_ema_drift_share` | ... with the H1 EMA drifting less than this share of the range height. **Provisional (issue #3, 20 November 2026), for the owner to approve.** | 0.25 |
| `stp_technical.min_evidence` | A technical forecast needs at least this many evidence points; below it there is no forecast. **Provisional (issue #3, 20 November 2026), for the owner to approve.** | 4 |
| `stp_technical.validity_hours` | A technical forecast lapses if price has not reached its entry zone within this many hours (lifecycle and replay). **Provisional (issue #3, 20 November 2026), for the owner to approve.** | 8 |

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


## News table (`config/news_table.toml`)

Which economic releases are big, medium or small news: **the owner's table from AutoBot 161**, copied as data from the public audit report `news_impact_table_161.csv` (override table version 2026-08-14.v1; snapshot 7 November 2026) and its README. 161's code was not copied. Five rows were added for AutoBot by the owner (marked below): GBP "Interest Rate" and GBP "Unemployment Rate" big; USD "Building Permits Prel", "Existing Home Sales" and "Housing Starts" placed as small. An override may say small: a release the owner has placed as small, so it is no longer logged as unmatched.

**How a release is matched** (`news/table.py`):

1. Only releases Finnhub marks high-impact (`news.table_impacts`) are matched; any other release is small.
2. Its name is lower-cased. The **override** rows are tried first, each only for its own currency; then the **big** rows; then the **medium** rows (any currency). The first row that matches decides.
3. A row matches when every keyword in it appears in the name, in any order (or, for a "name is exactly" row, when the name is exactly that, ignoring case).
4. A "same day" row matches only if another release of the same currency on the same UTC day matches one of its keyword groups: the US unemployment rate is big only on a payrolls day, and a Fed chair speech only on a rate-decision day.
5. No row matches: **small**, and the release is logged once (and kept in `data/news/unmatched.json`) so the owner can place it.

Only **big** releases stop trading (design section 6). Medium and small news is ignored. Each row below is one keyword group; a rule with several groups has several rows.

| # | Section | Rule | Tier | Currency | Keywords (all required) | Same day |
|---|---|---|---|---|---|---|
| 1 | override | gbp_interest_rate (added for AutoBot) | big | GBP | name is exactly "Interest Rate" |  |
| 2 | override | gbp_unemployment_rate (added for AutoBot) | big | GBP | name is exactly "Unemployment Rate" |  |
| 3 | override | usd_building_permits_prel (added for AutoBot) | small | USD | name is exactly "Building Permits Prel" |  |
| 4 | override | usd_existing_home_sales (added for AutoBot) | small | USD | name is exactly "Existing Home Sales" |  |
| 5 | override | usd_housing_starts (added for AutoBot) | small | USD | name is exactly "Housing Starts" |  |
| 6 | override | usd_fed_press_conf_override | big | USD | fed + press conference |  |
| 7 | override | usd_fed_press_conf_override | big | USD | fomc + press conference |  |
| 8 | override | usd_gdp_adv_override | big | USD | gdp + adv |  |
| 9 | override | gbp_gdp_mom_override | medium | GBP | gdp + mom |  |
| 10 | override | uk_cpi_override | big | GBP | cpi |  |
| 11 | override | uk_cpi_override | big | GBP | inflation + rate |  |
| 12 | override | uk_cpi_override | big | GBP | core + inflation |  |
| 13 | big | us_core_cpi | big | any | core + cpi |  |
| 14 | big | us_core_cpi | big | any | core + inflation + rate |  |
| 15 | big | us_cpi | big | any | cpi |  |
| 16 | big | us_cpi | big | any | inflation + rate |  |
| 17 | big | us_nfp | big | any | non farm payroll |  |
| 18 | big | us_nfp | big | any | non-farm payroll |  |
| 19 | big | us_nfp | big | any | nonfarm payroll |  |
| 20 | big | us_nfp | big | any | nfp |  |
| 21 | big | us_unemployment_with_nfp | big | any | unemployment rate | payrolls day |
| 22 | big | us_fomc | big | any | fomc |  |
| 23 | big | us_fomc | big | any | federal funds rate |  |
| 24 | big | us_fomc | big | any | fed funds rate |  |
| 25 | big | us_fomc | big | any | fed + interest rate decision |  |
| 26 | big | us_fomc | big | any | fed + rate decision |  |
| 27 | big | us_fed_chair_speech_at_rate_decision | big | any | fed chair + speech | rate-decision day |
| 28 | big | us_fed_chair_speech_at_rate_decision | big | any | powell + speech | rate-decision day |
| 29 | big | us_fed_chair_speech_at_rate_decision | big | any | warsh + speech | rate-decision day |
| 30 | big | us_fed_chair_speech_at_rate_decision | big | any | fed chair | rate-decision day |
| 31 | big | uk_boe_rate | big | any | boe + interest rate decision |  |
| 32 | big | uk_boe_rate | big | any | boe + rate decision |  |
| 33 | big | uk_boe_rate | big | any | bank of england + rate decision |  |
| 34 | big | uk_boe_rate | big | any | bank rate |  |
| 35 | big | uk_boe_rate | big | any | boe + press conference |  |
| 36 | big | uk_boe_rate | big | any | boe + monetary policy |  |
| 37 | big | ecb_rate | big | any | ecb + interest rate decision |  |
| 38 | big | ecb_rate | big | any | ecb + rate decision |  |
| 39 | big | ecb_rate | big | any | ecb + press conference |  |
| 40 | big | ecb_rate | big | any | main refinancing |  |
| 41 | big | ecb_rate | big | any | deposit facility |  |
| 42 | big | ecb_rate | big | any | ecb + monetary policy |  |
| 43 | big | uk_core_cpi | big | any | uk + core + cpi |  |
| 44 | big | uk_core_cpi | big | any | uk + core + inflation |  |
| 45 | big | uk_gdp | big | any | uk + gdp |  |
| 46 | big | uk_gdp | big | any | gdp + prel |  |
| 47 | big | uk_gdp | big | any | gdp + prelim |  |
| 48 | big | uk_gdp | big | any | gdp + advance |  |
| 49 | big | uk_gdp | big | any | gdp + flash |  |
| 50 | big | us_gdp_advance_prelim | big | any | gdp + advance |  |
| 51 | big | us_gdp_advance_prelim | big | any | gdp + prel |  |
| 52 | big | us_gdp_advance_prelim | big | any | gdp + prelim |  |
| 53 | big | central_bank_minutes | big | any | fomc + minutes |  |
| 54 | big | central_bank_minutes | big | any | ecb + minutes |  |
| 55 | big | central_bank_minutes | big | any | boe + minutes |  |
| 56 | big | central_bank_minutes | big | any | mpc + minutes |  |
| 57 | big | central_bank_minutes | big | any | monetary policy + minutes |  |
| 58 | middle | ism_manufacturing_pmi | medium | any | ism + manufacturing |  |
| 59 | middle | ism_services_pmi | medium | any | ism + services |  |
| 60 | middle | ism_services_pmi | medium | any | ism + non-manufacturing |  |
| 61 | middle | global_pmi_flash | medium | any | s&p global + pmi + flash |  |
| 62 | middle | global_pmi_flash | medium | any | markit + pmi + flash |  |
| 63 | middle | global_pmi_flash | medium | any | pmi + flash |  |
| 64 | middle | global_pmi_flash | medium | any | composite pmi |  |
| 65 | middle | retail_sales | medium | any | retail sales |  |
| 66 | middle | retail_sales | medium | any | core retail sales |  |
| 67 | middle | ppi | medium | any | ppi |  |
| 68 | middle | ppi | medium | any | producer price |  |
| 69 | middle | initial_jobless_claims | medium | any | initial jobless |  |
| 70 | middle | initial_jobless_claims | medium | any | initial claims |  |
| 71 | middle | continuing_claims | medium | any | continuing claims |  |
| 72 | middle | continuing_claims | medium | any | continuing jobless |  |
| 73 | middle | adp | medium | any | adp |  |
| 74 | middle | jolts | medium | any | jolt |  |
| 75 | middle | consumer_confidence | medium | any | consumer confidence |  |
| 76 | middle | uom_sentiment | medium | any | michigan + sentiment |  |
| 77 | middle | uom_sentiment | medium | any | uom + sentiment |  |
| 78 | middle | uom_sentiment | medium | any | michigan consumer |  |
| 79 | middle | durable_goods | medium | any | durable goods |  |
| 80 | middle | core_pce | medium | any | core + pce |  |
| 81 | middle | pce | medium | any | pce |  |
| 82 | middle | industrial_production | medium | any | industrial production |  |
| | default | default_small | small | any | (no row matched) | |

**Headline order** (`[[headline]]` in the same file; owner, 7 November 2026). When two or more big releases come out at the same time and their expected directions disagree, the first row below that one of them matches decides (design section 2.4). If it has no expected direction, there is none for that time; releases sharing the top row must agree. A release in no row ranks below them all.

| Rank | Name | Matches names containing any of | But not |
|---|---|---|---|
| 1 | rate decision | rate decision; interest rate; federal funds rate; fed funds rate; bank rate; main refinancing; deposit facility | |
| 2 | main payrolls | non farm payroll; non-farm payroll; nonfarm payroll; nfp | private |
| 3 | private payrolls | payroll + private | |
| 4 | headline CPI | cpi; inflation rate | core |
| 5 | core CPI | core + cpi; core + inflation | |

## Switches in .env

These live in `.env` (not in `config/settings.toml`), next to the IG secrets, so they can be changed without touching the settings file. They are checked every time a program starts: a missing or invalid switch stops it with a message naming the switch (never showing a secret). `.env.example` lists them with their current values. Tests never read the real `.env`.

| Setting | What it does | Value |
|---|---|---|
| `PAIRS_ON` | The pairs switched on, comma-separated. The price service streams each one, into its own candle store. Each must have a `[pairs.<PAIR>]` section in `config/settings.toml`. A newly switched-on pair starts with an empty store and is **never** filled from IG's history automatically: that needs the owner's go-ahead (`python -m prices.history_fill plan|go --pair <PAIR>`). | `GBPUSD` |
| `NEW_TRADES_FROM` | Trading hours: the earliest UK time a new trade may be opened, `HH:MM`. Must be earlier than `NEW_TRADES_UNTIL`. | 06:00 |
| `NEW_TRADES_UNTIL` | Trading hours: the latest UK time a new trade may be opened, `HH:MM`. Must not be later than `hours.close_all_trades_at`. | 20:30 |
| `STRATEGY_SLOW_GRIND` | The slow grind strategy (design 3.1), `on` or `off`. Switched off by the owner on 7 November 2026; **switched on** on 8 November 2026. | on |
| `STRATEGY_EMA_PULLBACK` | The EMA pullback strategy, `on` or `off`. | on |
| `STRATEGY_BOLLINGER_BOUNCE` | The hourly-pierce Bollinger band bounce (15 November 2026; `strategies/bollinger_bounce`), `on` or `off`. | on |
| `STRATEGY_BOLLINGER_BOUNCE_5M` | The first build's Bollinger band bounce (5-minute band and levels; `strategies/bollinger_bounce_5m`, recorded as "Bollinger bounce 5m"), `on` or `off`. Kept and renamed alongside the hourly-pierce bounce (owner, 19 November 2026). Required. | on |
| `ONE_SIGNAL_ONE_TRADE` | Stage 3 of the analyser control (design 6), `on` or `off`. On: two strategies opening the same way from the same rejection candle give one trade, the first to trigger (the others refused: "same signal already traded by ..."); the session sweep and the New York open reversal come under one view at a time. Off if left out of `.env`. **Owner's switch, off, 18 November 2026.** | off |
| `PULLBACK_ENTRY` | The breakout's and the Asian range breakout's pullback entry (`strategies/pullback.py`), `on` or `off`. On: neither opens on its break; each waits up to `pullback_entry.wait_candles` (6) for a pullback to the 5-minute 8 EMA and a close back beyond it, then opens at the next candle's open; a close beyond the 21 EMA against the break cancels. The Asian range breakout: only the first close beyond the range each way each day starts a wait. The breakout's day-direction rule is judged at the new entry price. Stops, take profits and trade management unchanged (breakout 6, Asian range breakout 12). Off: as before. **On if left out of `.env`. Owner's switch, on, 19 November 2026.** | on |
| `EMA_PULLBACK_TRADING_HOURS` | The EMA pullback's hours, `on` or `off`. On: a new EMA pullback trade opens only within the trading hours `NEW_TRADES_FROM` to `NEW_TRADES_UNTIL` (UK clock: GMT in winter, BST in summer), the same check as every other strategy, and every open EMA pullback trade is closed at `hours.close_all_trades_at` (20:30) UK every day, not only on Friday, so none is held overnight. The 21:55-22:15 rollover pause (`ema_pullback.rollover_no_new_trades_*`) stays as it is. Off (the EMA pullback's own hours: any time except Friday after 20:30 and the rollover; closed 20:30 UK on Friday only) if left out of `.env`. **Owner, 21 November 2026.** | off |
| `EMA_PULLBACK_ONE_AT_A_TIME` | Only one EMA pullback trade open at a time, `on` or `off`. On: while an EMA pullback trade is open (either direction), no other EMA pullback trade opens; a new one can open once it has closed. This is the per-strategy limit the other strategies already have (`limits.max_open_trades_per_strategy`, 1). Setups still form and are logged as before; a skipped one is recorded as refused by the safety rules, with the reason ("EMA pullback already has 1 trade(s) open (at most 1)"), in the orders journal and the decisions. EMA pullback trades still do not count towards `limits.max_open_trades`. Off (no limit, as before) if left out of `.env`. **Owner, 21 November 2026.** | off |
| `EMA_PULLBACK_TREND_ONLY` | The EMA pullback in a trend only, `on` or `off`. On: an EMA pullback opens only when the analyser says `trend` (slow grind or strong push) in the trade's direction; `emerging trend` no longer allows it, and the refusal says "(EMA_PULLBACK_TREND_ONLY: trend only)" (`strategies/common.py`, `allowed`). Off (emerging trend or trend, in the trend's direction, as before) if left out of `.env`. **Owner, 25 November 2026.** | off |
| `EMA_PULLBACK_SLOPE_DIRECTION` | The direction of step 0's 3-hour slope, `on` or `off`. On: as well as the size check (each slope at least `ema_pullback.hourly_min_slope_pips_per_hour`, unchanged), each hourly EMA (8, 13 and 20) must be higher than `ema_pullback.hourly_slope_candles` (3) finished hourly candles before for a buy, and lower for a sell; otherwise the hourly trend is not qualified and no setup starts (`strategies/ema_pullback/strategy.py`, `HourlyTrendReader`). Off (size only, as before) if left out of `.env`. **Owner, 25 November 2026.** | off |
| `EMA_PULLBACK_RECHECK_AT_OPEN` | Step 0 again at the open, `on` or `off`. On: when a setup's entry price is reached, the full hourly check (step 0: order, each EMA moving the trade's way since the hourly candle before, the 3-hour slope with its size and gap minimums, and its direction while `EMA_PULLBACK_SLOPE_DIRECTION` is on) is run again, from the hourly candles finished by the start of the 5-minute candle the entry is reached in (hourly candles end on the hour, so this is every hourly candle finished at the moment of the open). If it is not qualified the same way, the setup is cancelled and the reason noted; it does not open (`strategies/ema_pullback/strategy.py`, `EmaPullback`). Off (checked only at the touch candle, as before) if left out of `.env`. **Owner, 25 November 2026.** | off |
| `EMA_PULLBACK_NO_R3_S3` | No EMA pullback beyond the day's R3 or S3, `on` or `off`. On: no new EMA pullback buy when its entry price (the strategy's own, sell / chart price, as the other entry filters) is at or above the day's R3, and no new sell when it is at or below the day's S3, from the bot's daily pivot levels (`levels/current.py`). Checked with the entry filters just before the trade opens (`strategies/entry_filters.py`); a refusal is recorded as `entry filter refused`, rule "EMA pullback R3/S3", with the entry, the level and the distance. If the levels have no R3 (buy) or S3 (sell), it is not checked, and that is recorded. Off if left out of `.env`. **Owner, 25 November 2026.** | off |
| `HOURLY_CONTEXT` | The entry filters' rule 1, the hourly context (`strategies/entry_filters.py`), `on` or `off`. On: in an hourly DOWN context (the latest hourly swing high lower than the one before, the last hourly close below the hourly 50 EMA, the 50 EMA falling over 6 hourly candles) no strategy (except the breakout and the Asian range breakout, exempt) opens a buy whose entry price is within 5 pips of the daily pivot or the hourly 50 EMA; in an UP context (the mirror) no sell. Checked once for every trade, just before it opens; a refusal is recorded with the context and the line. Numbers in `[entry_filters]`. **On if left out of `.env`. Owner, 21 November 2026.** | on |
| `ENTRY_NEAR_EMA8` | The entry filters' rule 2, entry near the 8 EMA (`strategies/entry_filters.py`), `on` or `off`. On: a sell opens only if its entry price is no more than 5 pips below the 5-minute 8 EMA (sell price, last finished 5-minute candle), a buy only if no more than 5 pips above it; the slow grind, the breakout, the Asian range breakout and the session sweep are exempt (the session sweep: owner, 21 November 2026). A refusal is recorded with the entry price, the 8 EMA and the distance. **Off if left out of `.env` since 21 November 2026 (owner: replaced by `RSI_STRETCH`; the code is kept).** | off |
| `RSI_STRETCH` | The entry filters' rule 2b, the RSI stretch (`strategies/entry_filters.py`), `on` or `off`. On: no sell opens while the 5-minute RSI 3 (sell price, last finished 5-minute candle) is under 30, no buy while it is over 70; the slow grind, the breakout, the Asian range breakout and the session sweep are exempt. A refusal is recorded with the RSI and the strategy. Numbers in `[entry_filters]`. **On if left out of `.env`. Owner, 21 November 2026 (in place of `ENTRY_NEAR_EMA8`).** | on |
| `TREND_DAY_RSI_OFF` | Johnny's slow-grind trend day (`strategies/entry_filters.py`), `on` or `off`. On: once a slow grind trade is in profit (as IG would close it) at any moment between 06:00 and 09:00 UK, a trend day in its direction is on until 20:30 UK, and `RSI_STRETCH` does not apply to trades in that direction (trades against it are still checked; rule 1 unchanged). A slow grind trade the other way also in profit in that window cancels it for the day. Its start (time, direction, the slow grind trade) and any cancel are recorded in `decisions.jsonl` and shown on the dashboard. Not the bot's own trend-day check. **On if left out of `.env`. Owner, 21 November 2026.** | on |
| `EMERGING_LADDER` | Johnny's exit for emerging-trend trades (`trade_manager/manager.py`), `on` or `off`. On: a trade opened while the analyser said "emerging trend" (up or down, as recorded on the trade at open; every strategy) has its stop at IG moved to +5 pips once it is +10, and to +10 once it is +15 (pips as IG closes it). Never backwards; where the strategy has its own trail or stop move, the tighter stop wins. Through the trail's stop-move code (nearest level IG allows, IG must confirm, 3 attempts). Take profit unchanged; other states unchanged. Each move recorded on the trade. Numbers in `[emerging_ladder]`. **On if left out of `.env`. Owner, 21 November 2026.** | on |
| `COUNTER_TREND_TIRING` | The entry filters' rule 3, counter-trend tiring (`strategies/entry_filters.py`), `on` or `off`. On: a Bollinger bounce (hourly), Bollinger bounce 5m, level reversal, session sweep or New York open reversal against the analyser's trend (state `trend` down for a buy, up for a sell; `emerging trend` and `possible reversal` do not count) opens only when the trend is tiring: the hourly MACD 35/45/30 histogram (sell price, last finished hourly candle) is past zero on the trade's side, or closer to zero than the hourly bar before (1 bar); or the 5-minute MACD 35/45/30 histogram (last finished 5-minute candle) has crossed zero onto the trade's side (above zero for a buy, below for a sell; Johnny's addition, 23 November 2026). Otherwise refused, recorded in `decisions.jsonl` ("entry filter refused") with the strategy, the analyser state and the hourly and 5-minute MACD values. Too few hourly candles: not checked; too few 5-minute candles: the hourly alone decides. Johnny's rule of 21 October 2026; the owner's answers, 23 November 2026. **On if left out of `.env`.** | on |
| `TREND_ENDS_IN_CONSOLIDATION` | The analyser (`analyser/states.py`), `on` or `off`. On: once the analyser calls a trend (slow grind or strong push) it does not go to a possible reversal, and a trend ends only in consolidation: the consolidation reading, 2 closes back past the 100 EMA, the 24-candle fade and the ranging reading all go to consolidation. Emerging trends and a possible reversal from an emerging trend are unchanged. Off: as before. On if left out. **Owner's rule, 24 November 2026.** | on |
| `COUNTER_TREND_EMERGING` | Rule 3 in an emerging trend (`strategies/entry_filters.py`), `on` or `off`. On: rule 3 also checks a reversal-type trade against the analyser's `emerging trend`, not only against `trend`. Off: only `trend`. On if left out. **Owner's change, 24 November 2026.** | on |
| `COUNTER_TREND_HOURLY_CONFIRMED` | Rule 3's hourly confirmation (`strategies/entry_filters.py`), `on` or `off`. On: an hourly MACD 35/45/30 histogram on the bounce's side of zero that never went to the trend's side is not tiring (the hourly has not confirmed the trend). Past zero counts as tiring only if the histogram was on the trend's side at an hourly candle since the analyser's current state began, before the last finished one; shrinking counts only while it is on the trend's side. The 5-minute zero-cross is unchanged. Off: rule 3 as built on 23 November. On if left out. **Owner's change, 24 November 2026.** | on |
| `PLANNER_OBSERVE` | The Structural Trade Planner (`planner/`), `on` or `off`. On: after each new 5-minute candle the price service starts the planner in a separate, low-priority process (never on the price feed's thread): it re-plans on each completed hourly candle and checks its zone on each 5-minute candle, writing `planner.folder`. **Observe only:** it never authorises, refuses, opens, changes or closes a trade, and the dashboard panel says so. Off if left out of `.env`. **Off until the owner approves installation.** | off |
| `STRATEGY_RANGE_TRADE` | The range trade strategy, `on` or `off`. | on |
| `STRATEGY_BREAKOUT` | The breakout strategy (design 3.5), `on` or `off`. The bot refuses to start with it on while `breakout.stop_loss_pips` or `breakout.take_profit_pips` is 0. Switched on by the owner, 7 November 2026. | on |
| `TRADING` | The master switch, `on` or `off` (design 13). While it is off, the strategies, safety rules, order sender and trade manager all run inside the price service and everything is recorded, but no order is ever sent to IG: trades are paper trades, recorded in `data/orders/<PAIR>/paper_orders.jsonl`. **Owner's switch, 8 November 2026.** | off |
| `STRATEGY_LEVEL_REVERSAL` | The level reversal strategy (design 3.6), `on` or `off`. Added and switched on by the owner, 8 November 2026. | on |
| `STRATEGY_ASIAN_RANGE_BREAKOUT` | The Asian range breakout (design 3.7), `on` or `off`. **Owner's switch, on, 16 November 2026.** | on |
| `STRATEGY_SESSION_SWEEP` | The session sweep (design 3.8), `on` or `off`. **Owner's switch, on, 16 November 2026.** | on |
| `STRATEGY_NEW_YORK_OPEN_REVERSAL` | The New York open reversal (design 3.9), `on` or `off`. **Owner's switch, on, 16 November 2026.** | on |
| `BOUNCE_ONLY_NEAR_TIMES` | The Bollinger bounce (design 3.3), `on` or `off`. On: a bounce opens only within `bounce.near_times_within_minutes` (60) of `bounce.near_times` (10:00, 14:00, 16:00 UK). Off if left out of `.env`. **Owner's switch, off, 15 November 2026.** | off |
| `STOP_LOSS_PIPS` | The stop loss sent with every trade, for every strategy except the EMA pullback (which has `STOP_LOSS_PIPS_EMA_PULLBACK`), the breakout (`breakout.stop_loss_pips`), the slow grind (`slow_grind.stop_loss_pips`) and the level reversal (`level_reversal.stop_beyond_furthest_pips`): today that is the Bollinger bounce and the range trade. In pips: a whole number from 1 to 100. Turned into IG's points per pair (`pairs.PAIR.pip_size` x `pairs.PAIR.price_scale`). Moved from `trade.stop_loss_pips` in `config/settings.toml` on 7 November 2026. **Owner's value 12, 10 November 2026** (6 before), set in `.env`. | 12 |
| `STOP_LOSS_PIPS_EMA_PULLBACK` | The EMA pullback's stop loss, sent with each of its trades, in pips: a whole number from 1 to 100. Turned into IG's points per pair like `STOP_LOSS_PIPS`. **Owner's value, 7 November 2026.** | 12 |
| `TAKE_PROFIT_PIPS` | The take profit sent to IG with every trade, in pips: a whole number from 1 to 1000. The bot may close earlier itself; this is the backstop. Moved from `trade.take_profit_pips` on 7 November 2026. | 100 |
