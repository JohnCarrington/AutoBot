# AutoBot — Agreed Design (master copy)

This is the master copy of the design for the new AutoBot, as agreed with Johnny on 6 November 2026. It lives in the repository at `docs/DESIGN.md`. Where any other document disagrees with this one, this one wins, unless Johnny says otherwise. Any change to the design is made here first, then built.

The bot is built to work for any currency pair, with only GBPUSD switched on (section 13). It trades on the IG demo spread bet account, at £10 per pip. No code is copied from AutoBot 161. 161 was studied only to learn from it; the audit reports are in the public repository JohnCarrington/autobot_reports.

---

## 1. How the parts fit together

One program, made of separate parts, each with one job:

1. **IG connection** (`ig/`): the only part that talks to IG. Login, account, errors. Built (stage 3).
2. **Prices and candles** (`prices/`): live prices from IG's stream, candles on 5-minute, 1-hour, 4-hour, daily and weekly, with buy and sell prices kept separate. Built (stage 4).
3. **Levels** (`levels/`): pivots, round numbers, highs and lows, turning levels, and which levels line up.
4. **Rejection** (`rejection/`): one shared part that works out whether price has been rejected at a level or band. The analyser, the strategies and the trade manager all read the same answer.
5. **Market analyser** (`analyser/`): decides the market state and direction, and which strategies are allowed.
6. **Strategies** (`strategies/`): slow grind, EMA pullback, Bollinger band bounce, range trade, breakout (switched off until its stop and take profit are chosen), level reversal (3.6). Each checks its own entry rules.
7. **Safety rules** (`safety/`): size, number of trades, trading hours, news, total risk, pause switch.
8. **Order sender** (`orders/`): the only part that places, changes or closes trades at IG.
9. **Trade manager** (`trade_manager/`): looks after every open trade until it closes.
10. **Records** (`records/`), **dashboard** (`dashboard/`) and **alerts** (`alerts/`, Telegram).

**Put together (stage 13, `trading/engine.py`):** the strategies, safety rules, order sender and trade manager run inside the price service on its one IG login. After each finished 5-minute candle: the analyser takes it, the trade manager runs every open trade on it (including "watching a level"), the strategies run on it (the same code as the replay) and every idea goes to the order sender, which applies the safety rules before anything is sent. Every second, on the latest price: each waiting setup's trigger is checked (the 5-minute candle forming so far is given to copies of the strategies, the same code as for a finished candle), so a trade opens as soon as the live price reaches its trigger (section 3); then the trade manager runs the open trades on that price. When the candle finishes the strategies take it as always and an idea already sent live is not sent again; a trade opened during a candle is not run on that candle's earlier prices. The strategies, like the analyser, read the candle store afresh on every call (each finished candle and each live check), so they always see the latest candles and levels: never a copy kept from start-up (owner, 11 November 2026; until then the strategies kept the store as it was when the service started, so after a restart they never saw a new day's file or new candles in a day's file already read; `tests/technical/test_strategies_see_latest_candles.py`). Each open trade's best price so far, half close and "watching a level" are saved by the trade manager and restored after a restart. The master switch `TRADING` in `.env`: while it is off, everything runs and is recorded but no order is ever sent to IG (paper trades, `data/orders/<PAIR>/paper_orders.jsonl`). A problem in trading is reported and stops trading; the prices go on. `python -m trading.replay_check` confirms that over 25 October 21:00 UK to the candle of 9 November 2026 10:00 UTC the full wired path, with the one view at a time rules (section 6), gives the result of rank 1 in `docs/research/one_view_20261109.md`: 157 trades, 76 won, 80 lost, +1120.9 pips, the same biggest loss, worst losing run and pips each week, and none of the trades those rules left out. (Before those rules it gave the same 161 trades as `docs/research/all_strategies_together_20261108.md` over 26 October to 6 November.)

The dashboard only displays and pauses. It never trades.

---

## 2. Market analyser

The analyser does not predict. It watches what price is actually doing, using the higher timeframes for the wider picture.

### 2.1 What it reports

Every result gives: the market state, the direction (up, down or none), the type of trend (slow grind or strong push), when the state started, the evidence for it, and whether its data is ready, warming up or out of date. If the data is not ready, new trades are blocked but open trades are still managed. Every state change is recorded.

### 2.2 The five states

| State | Strategies allowed |
| --- | --- |
| Ranging | Range trade; level reversal (3.6), either way |
| Emerging trend | EMA pullback, breakout (3.5), in the trend's direction only. Bollinger band bounce in the emerging trend's direction only (owner, 13 November 2026). Not the slow grind (owner, 8 November 2026). Level reversal (3.6), either way |
| Trend | Slow grind (either type of trend, slow grind or strong push; owner, 8 November 2026), EMA pullback, breakout (3.5), in the trend's direction only; Bollinger band bounce against the trend's direction only (owner, 7 November 2026); level reversal (3.6), either way |
| Possible reversal | Bollinger band bounce; level reversal (3.6), either way |
| Consolidation | None (not even the level reversal). Watch and wait for a break |

- **Ranging:** the Bollinger bands are flat and close together, and price bounces between the upper and lower band. The EMAs weave back and forth instead of staying stacked, and the 100 EMA is flat. In numbers (owner, 7 November 2026): close together is a band width of at least 6 and at most 18 pips; flat is the upper band and the lower band each moving less than 0.5 pips a candle, measured over 6 candles (owner, 13 November 2026; 0.2 before); price bounces between the bands when both bands have been reached within 24 candles.
- **Emerging trend:** a direction is starting to form. Its main job is to stop bounces against the new direction early. The Bollinger band bounce trades in an emerging trend only in the emerging trend's direction; a bounce against it stays blocked (owner, 13 November 2026; from 7 November it did not trade in an emerging trend at all).
- **Trend:** an established direction, either a slow grind or a strong push. Both are recognised from price action.
- **Possible reversal:** after a trend has been running and price has moved at least 30 pips since it started, a strong reversal candle appears, recognised by the shared rejection part with no extra size rule.
- **Consolidation** (this includes a trend running out of steam): narrow Bollinger bands, price between them touching neither band, small candles with green and red roughly the same size, no direction. Unlike ranging, price stays in the middle. No trading. When price breaks out, the analyser moves to emerging trend.

### 2.3 Direction rule (applies to every strategy except the range trade, the Bollinger band bounce, the breakout, the slow grind and the level reversal)

- **Buy side:** price above the daily pivot and above the 5-minute 100 EMA.
- **Sell side:** price below the daily pivot and below the 5-minute 100 EMA.
- If they disagree, there is no clear direction.
- This applies to every strategy except the range trade, the Bollinger band bounce and the breakout (owner, 7 November 2026) and the slow grind and the level reversal (owner, 8 November 2026), which it does not apply to in any state. The breakout has its own direction filter instead: the day's move so far (section 3.5). The slow grind has no direction filter: only the trend's direction (2.2).

Functional test: on 6 November 2026 at 13:00 the signs of a reversal up appeared, but price was below the pivot and the 100 EMA, and carried on down through S2 to S3. Expected answer: no buy at 13:00, and the sell side stays allowed all the way down to S3.

### 2.4 News direction and trend days

- For each big release, read the forecast and previous figures from Finnhub, work out whether the expected result is good or bad for the pound or the dollar, and use that as the expected direction for the day.
- **Big releases at the same time** (owner, 7 November 2026): if their expected directions agree, that is the direction for that time. If they disagree, the **headline release decides**: a rate decision over everything else at that time, main payrolls over private payrolls, headline CPI over core CPI (the order is part of the news table, `config/news_table.toml`). If the headline release has no expected direction, there is no expected direction for that time; if several releases share the top place and do not agree, there is none either. Example: on Friday 6 November 2026 at 13:30, main payrolls (forecast above previous: good for the dollar) decide: GBPUSD down.
- On a trend day, when the trend and the expected news direction agree, expect price to continue through levels rather than reverse. The expected news direction takes precedence: a trade in that direction is kept open through rejections at levels.
- Example: on 6 November 2026 the 13:30 news produced a big red candle and the day traded down through S1, S2 and S3.
- **The trend-day check** (owner, 8 November 2026; `analyser/trend_day.py`): at each UK day's 00:00 open, on the sell price, it is a **trend day downwards** if the open is at or above the previous month's **R2** and the **daily RSI(14)** at the previous day's close is **above 70**; a **trend day upwards** if the open is at or below the previous month's **S2** and the daily RSI(14) is **below 30**. Otherwise it is not a trend day. The monthly levels are the classic pivots of the previous UK calendar month, built from the stored daily candles of that month (only when the store holds the whole month); the RSI is Wilder's on the stored daily candles up to the previous day (Monday: IG's short Sunday candle). Saturday and Sunday have no 00:00 open and are never trend days. The levels and the RSI periods and lines are settings (`[trend_day]`: `level_above` R2, `level_below` S2, `rsi_periods` 14, `rsi_above` 70, `rsi_below` 30). These are exactly the conditions of rank 1 in `docs/research/trend_day_conditions_v2_20261108.md`: on the stored candles to 6 November 2026 they flag 16 days.
- **What it changes:** on a trend day, an EMA pullback or slow grind trade in the trend day's direction (back towards the monthly pivot: a sell on a trend day downwards, a buy on a trend day upwards) gets the 100-pip take profit of `TAKE_PROFIT_PIPS` instead of its usual take profit (section 4); and no reversal trade against the trend day's direction opens (section 6, "One view at a time"; owner, 9 November 2026). On a big-news day, likewise no reversal trade against the expected news direction (section 6).

### 2.5 How a trend starts

Price pushes into a strong level, such as the daily pivot, is rejected, and steps away from it. The analyser watches the levels itself and moves to emerging trend at the moment the level is rejected, without waiting for any strategy. From then on, bounces against the new direction are blocked.

**What shows the rejection has become a trend** (for a downtrend; an uptrend is the mirror image):

1. Price falls away from the level, each candle opening near where the last one closed.
2. Price drops through the 7, 13 and 21 EMAs and stays below them. They flatten, cross and turn down in order, then start to spread apart.
3. Price drops below the 100 EMA and stays below it.
4. Small bounces fail at or below the short EMAs and the middle of the Bollinger band, and the next candle makes a lower low.
5. Price moves to the bottom of the Bollinger band and stays on or near it, and the band starts to slope down.
6. The candles are small and steady, with no big spikes.

It becomes clear when the first bounce fails under the EMAs and middle band and price makes a new low on the lower band. Example: just before midnight on 5 November 2026, the rejection at the daily pivot.

**Strong push** (for up; down is the mirror image): candles mostly green, closing higher one after another with hardly any pauses; price riding along or just outside the upper band; the bands opening up wide; the 7, 13 and 21 EMAs fanning wide apart and pointing steeply up; price pulling away from the 100 EMA. In a slow grind the bands slope but stay fairly even and the EMAs stay close together.

### 2.6 What points to a possible reversal

- **MACD** still shows the move that is ending: at its biggest histogram bar in the old direction, or already past its biggest and shrinking. MACD lags price, so the bot must never wait for MACD to turn before allowing a reversal.
- **RSI** has gone beyond 30 or 70 and is turning back.
- **A rejection candle**, such as a hammer.
- **Time of day**, such as just before the New York session opens.
- **Price at a level**, including recent hourly highs and lows.

### 2.7 How it must behave

- Steady enough not to flip back and forth between states; quick enough to spot a real change. Every state is protected from flip-flopping.
- Evidence fades after a set time if nothing new happens.
- A trend needs proof in the price itself, not momentum alone.
- Words such as flat, narrow, close together, widening and fanning become settings, starting from NMS's values on 161 where they exist, checked against real days Johnny knows.

### 2.8 Indicators (as on Johnny's IG chart)

| Indicator | Settings | Used for |
| --- | --- | --- |
| EMAs | 7, 13, 21, plus 100 and 200 | Trend: slope and fanning |
| Bollinger bands | 20 periods, 2 standard deviations | Trend or range |
| MACD | 35, 45, 30 | Exhaustion |
| RSI | 3 periods, 70 and 30 lines | Exhaustion |
| Pivots | Daily, (high + low + close) / 3, R1–R3, S1–S3 | Levels and direction |

Timeframes: weekly, daily, 4-hour, 1-hour, 5-minute and tick. The EMA pullback uses its own EMAs (section 3.2).

Every indicator, for the analyser and the strategies, is worked out from the sell (bid) price, with daily candles running midnight to midnight UK, to match Johnny's IG chart, which is set to the sell price. Trades still open and close at IG's real buy or sell price as normal.

---

## 3. Strategies

The analyser decides which are allowed. Each strategy then has its own entry rules. All rules below are written for one direction; the other is the mirror image.

### 3.1 Slow grind (sell)

**Switched on** (owner, 8 November 2026): `STRATEGY_SLOW_GRIND=on`, with result 13 of the slow grind research (`docs/research/slow_grind_variations_20261107.md`) and holding rule 2. Rule 1, the two-candle start, was removed on 7 November 2026; the others keep their numbers.

Price moves in a staircase: it pauses rather than bouncing back to the middle of the band.

2. It counts as a pause once at least 2 candles in a row (`slow_grind.min_pause_candles`) have failed to make a new low while staying below the 21 EMA.
3. The sell opens as soon as the live price breaks below the lowest point of the pause.
4. If a candle closes above the 21 EMA, the setup is cancelled. No time limit: a long pause becomes consolidation in the analyser.
5. Only in a trend (either type, slow grind or strong push), in the trend's direction (2.2); not in an emerging trend. The direction rule (2.3) does not apply, and there is no other direction filter.
6. Stop loss 15 pips (`slow_grind.stop_loss_pips`); take profit 20 pips (`slow_grind.take_profit_pips`), or 100 pips (`TAKE_PROFIT_PIPS`) for a trade opened on a UK day with big news for the pair, or in the trend day's direction on a trend day (2.4); the profit lock 15/10; no close on a rejection at a level (section 4).
7. New trades at any time the market is open, big-news windows included, except from 20:30 UK to midnight every day, in the first 15 minutes after the Sunday open, and from 21:55 to 22:15 UK. Any slow grind trade still open at 20:30 UK is closed, every day; not closed before big news. One slow grind trade open at a time (section 6).

### 3.2 EMA pullback (buy)

0. The trend must be established on the hourly chart: hourly 8, 13 and 20 EMAs in order and all rising, with the slope and gap minimums from 161's service as settings. Each EMA's slope over the last 3 hourly candles must point the trend's way (rising for a buy, falling for a sell) and be at least 0.16 pips an hour: 161's rule, "the right sign and absolute magnitude" (owner, 13 November 2026; until then only the size was checked).
1. While a 5-minute candle is forming, the live price drops to the 5-minute 8 EMA. Price may cross the 8 and even the 13 EMA.
2. If a 5-minute candle closes below the 21 EMA, the setup is cancelled.
3. The entry price is 3 pips above the highest high (for a buy; 3 pips below the lowest low for a sell) of the five completed 5-minute candles immediately before the touch candle (AutoBot 161's rule).
4. The trade opens as soon as the live price reaches the entry price.
5. If it has not opened within 20 minutes, the setup expires.

EMAs: 8, 13 and 21 on the 5-minute chart. No fanning rule.

### 3.3 Bollinger band bounce (sell)

1. Price pierces a level or the Bollinger band. For a level, a candle that comes within 3 pips of it counts the same as a pierce (a setting). The Bollinger band needs a real pierce (for the bounce; the range trade, 3.4, counts price reaching the band).
2. The reversal candle is the first red candle after the pierce, with no size rule. If none appears within 3 candles, the setup expires.
3. A later confirmation candle closes below the reversal candle's low, within 3 candles of it, or the setup expires. A wick below without a close does not count.
4. The sell opens as soon as the live price goes below the confirmation candle's low.
5. If price goes above the reversal candle's high at any point, the setup is cancelled.

Half the trade closes when price reaches the opposite Bollinger band; the rest goes on to the bounce's normal exits (section 4) (owner, 11 November 2026, as tested in `docs/research/management_and_targets_20261111.md`; `bounce.close_percent_at_opposite_band` 50).

Once the trade has been 6 pips in profit, its stop is moved at IG to break-even, the price it opened at (owner, 13 November 2026; section 4, "Bollinger bounce break-even").

**Against open trend trades: the pace and target rule** (owner, 11 November 2026, as tested in `docs/research/pace_and_target_20261111.md`, the version "within 5 pips, under 5 pips an hour over the last 2 hours": +1,379.5 pips in 158 trades against +1,329.2 in 176 over 25 October to 11 November 2026; `trading/against_trend.py`). The owner's words: "I decide by looking at how quickly the price is moving. It is moving slowly this morning so it is not unreasonable to think it is grinding to a halt and will take a couple of hours to hit that level. If it was moving faster all morning I might expect it to break through and continue."

1. While the bot has open trend trades (EMA pullback, slow grind, breakout), no bounce may open against them unless it opens at a significant level in their direction: a 00, the weekly pivot (the standard one from the previous Monday-to-Friday week, (high + low + close) ÷ 3 of that week's daily candles from Monday to Friday, not including Sunday's prices; owner, 13 November 2026), S2, S3, R2 or R3, with the high (a bounce sell) or low (a bounce buy) the bounce turned from within 5 pips of it (`bounce.against_trend_level_within_pips`). "In their direction" means beyond the price at least one of those trades opened at.
2. At that level the bounce is valid only if price has moved under 5 pips an hour on average over the last 2 hours (`bounce.against_trend_max_pips_per_hour`, `bounce.against_trend_pace_hours`): the net move from the close 2 hours earlier to the last close, divided by 2. It then opens, and **closes every trade open in the opposite direction at that moment**, whatever its strategy, in profit or not. Otherwise it is refused and the trend trades are held.

Everything is read as at the start of the 5-minute candle the bounce opens in, on the sell price: the high or low is the extreme of the setup's candles from the pierce to the confirmation; the levels are those of that moment; the pace uses finished candles only, and with no candle 2 hours earlier (after a gap or the weekend) it cannot be read and the bounce is refused. Bounce setups that trigger the same way in the same candle are one bounce, judged by the first (live, only the first is sent). The rule applies on the live price and on a finished candle alike. A bounce with no open trend trade against it is not affected. Every refused bounce goes in the decision log ("bounce refused", with the reason: not at a significant level, price moving fast, or the pace could not be read), and every valid one too ("bounce against trend trades"), with the level, the high or low it turned from, the nearest levels and the pips an hour. The closes are priced like the bounce's own entry: a bounce sell opens at the sell price, where a buy closes; a bounce buy opens at the buy price, where a sell closes. Live, each close counts only once IG confirms it (IG's level and time are recorded); a close IG does not confirm leaves the trade open, is recorded as a close not done, and is tried again after `orders.close_retry_seconds`.

The bot records, for each bounce, how big the reversal candle was compared with the piercing candle, for later review. It never filters on it.

Spread spikes are ignored: when IG's spread on a candle is abnormally wide (over 3 pips, a setting; this happens at the 22:00 rollover and at news), that candle's sell-price highs and lows cannot start a setup or cancel one. The candle is still stored as normal.

### 3.4 Range trade (sell at the upper band)

1. One candle reaches the upper Bollinger band: its high goes above it or comes within 3 pips of it (`rejection.near_level_within_pips`, the same 3 pips as for a level). A pierce is not needed (owner, 13 November 2026).
2. The next candle is a red rejection candle.
3. The sell opens as soon as the live price, during the candle after that, goes below the rejection candle's low.
4. If price goes above the rejection candle's high first, the setup is cancelled.

The whole trade closes when price reaches the other band (owner, 11 November 2026, as tested in `docs/research/management_and_targets_20261111.md`; half before; `range_trade.close_percent_at_opposite_band` 100).

Spread spikes are ignored in the same way as for the bounce (3.3).

### 3.5 Breakout (owner, 7 November 2026)

1. It looks for a trade only at the moment the analyser moves into an emerging trend because price broke out of a range (two closes beyond the same band, section 2.5) or because a 5-minute candle closed outside the Bollinger band out of a consolidation: that candle is the breakout candle.
2. A buy (breakout up) opens as soon as price breaks above the breakout candle's high; a sell (breakout down) as soon as price breaks below its low.
3. If price does not break it within 3 candles after the breakout candle (`breakout.trigger_within_candles`), the setup expires.
4. It only takes a breakout in the direction of the day's move so far: a buy only when the entry price is above that day's 00:00 UK open, a sell only when it is below (the open of the 5-minute candle starting at 00:00 UK, sell price). The direction rule (2.3) does not apply to it.
5. Stop loss 12 pips (`breakout.stop_loss_pips`; owner, 10 November 2026), take profit 50 pips (`breakout.take_profit_pips`). No close on a rejection at a level.
6. New trades only from 06:00 to 20:30 UK; it may open during a big-news window, may be held overnight and through news, and any breakout trade still open at 20:30 UK on Friday is closed (sections 4 and 6). One breakout trade open at a time.

### 3.6 Level reversal (sell; owner, 8 November 2026)

**Switched on** (`STRATEGY_LEVEL_REVERSAL=on`). From the level reversal research of 8 November 2026 (`docs/research/level_reversal_tolerance_20261108.md`).

1. Only rejections at **round numbers ending in 00** (not 50), **S2**, **R2** and the **daily pivot** (H + L + C) / 3 (the pivot added by the owner, 13 November 2026) (`level_reversal.level_types`, `level_reversal.round_numbers_every_pips`), found by the shared rejection part exactly as for the Bollinger band bounce (3.3 steps 1 to 3 and 5): price reaches the level or comes within 3 pips of it, the reversal candle, the confirmation candle.
2. The rejection counts only if price went no further past the level than its **allowance**: **12 pips at R2 and S2, 5 pips at round numbers** (owner, 8 November 2026), **12 pips at the daily pivot** (owner, 13 November 2026) (`level_reversal.allowance_pips_r2`, `level_reversal.allowance_pips_s2`, `level_reversal.allowance_pips_pivot`, `level_reversal.allowance_pips_round_number`), measured as the furthest price reached from the piercing candle to the confirmation candle.
3. The sell opens as soon as price breaks below the confirmation candle's low (a buy, above its high).
4. **Stop 6 pips beyond the furthest point** price reached (`level_reversal.stop_beyond_furthest_pips`; for a sell, 6 pips above the highest high from the piercing candle to the confirmation candle), so the stop's distance from the entry varies. **Take profit: the next daily pivot level** beyond the entry, in the trade's direction (owner, 13 November 2026): the nearest of the pivot, R1 to R3 and S1 to S3 below the entry for a sell (above it for a buy), from the levels as they stand at that candle, and the trade closes exactly at that level (sent to IG as a distance from the price the trade opens at, as for the stop). For example, a sell at the pivot runs to S1. Only when there is no daily pivot level beyond the entry (a sell below S3, a buy above R3) is it 20 pips (`level_reversal.take_profit_pips`).
5. In every analyser state except consolidation, either way (2.2); the direction rule (2.3) does not apply.
6. New trades from 06:00 to 20:30 UK; closed at 20:30 UK; not opened in a big-news window and closed 15 minutes before big news, like the other strategies (section 6); up to two level reversal trades open at once (`level_reversal.max_open_trades`; owner, 13 November 2026, one before); no close on a rejection at a level (section 4).
7. If several of these levels were reached, the first that passes rule 2 is the level (S2, R2 and the pivot before round numbers); several setups triggering on the same candle and direction give one trade.

---

## 4. Trade management

One shared trade manager for every trade.

- **Stop loss:** a fixed 12 pips for every strategy except the EMA pullback, the breakout, the slow grind and the level reversal, sent to IG: that is the Bollinger bounce and the range trade (owner, 10 November 2026; 6 pips before; confirmed on 11 November 2026 as change 1 of `docs/research/management_and_targets_20261111.md`, put live with the closes at the opposite band; the live `.env` still held 6 until then). A switch in `.env` (`STOP_LOSS_PIPS=12`). The EMA pullback's stop is 12 pips (owner, 7 November 2026), its own switch in `.env` (`STOP_LOSS_PIPS_EMA_PULLBACK`). The breakout's is 12 pips (owner, 10 November 2026; 6 before; `breakout.stop_loss_pips`) and the slow grind's 15 pips (owner, 8 November 2026; `slow_grind.stop_loss_pips`), in `config/settings.toml`. The level reversal's stop is not a distance from the entry: it is 6 pips beyond the furthest point price reached (owner, 8 November 2026; `level_reversal.stop_beyond_furthest_pips`, section 3.6).
- **Take profit:** a fixed 100 pips sent to IG as a safety net, for every strategy except the EMA pullback, the breakout and the slow grind. A switch in `.env` (`TAKE_PROFIT_PIPS`). The EMA pullback's take profit is 30 pips (owner, 7 November 2026; `ema_pullback.take_profit_pips` in `config/settings.toml`) and the slow grind's 20 pips (owner, 8 November 2026; `slow_grind.take_profit_pips`), except that an EMA pullback or slow grind trade opened on a day with big news for the pair, or opened in the trend day's direction on a trend day (section 2.4, owner, 8 November 2026), gets the 100 pips of `TAKE_PROFIT_PIPS`. The breakout's is 50 pips (`breakout.take_profit_pips`), on any day. The level reversal's is the next daily pivot level beyond its entry (owner, 13 November 2026; section 3.6), or 20 pips when there is none (`level_reversal.take_profit_pips`). All are the bot's own rule, not an IG requirement.
- **Breakout exits** (owner, 7 November 2026): a breakout trade runs until its 12-pip stop (owner, 10 November 2026) or 50-pip take profit at IG (`breakout.stop_loss_pips`, `breakout.take_profit_pips`), or 20:30 UK on Friday, when any breakout trade still open is closed. It is not closed at 20:30 on other days (it may be held overnight), not closed before big news, and the close on a rejection at a level does not apply to it.
- **Slow grind exits** (owner, 8 November 2026): a slow grind trade runs until its 15-pip stop or its take profit at IG (20 pips; 100 pips, `TAKE_PROFIT_PIPS`, for a trade opened on a UK calendar day with a big release for the pair, or in the trend day's direction on a trend day, section 2.4), the profit lock, or 20:30 UK, when any slow grind trade still open is closed, every day. **Profit lock 15/10:** once the trade has been 15 pips in profit (`slow_grind.lock_from_pips`), it is closed if price comes back to 10 pips in profit (`slow_grind.lock_at_pips`); the lock applies from the candle after the one that reached 15 pips. It is not closed before big news, and the close on a rejection at a level does not apply to it. It never opens from 20:30 UK to midnight, so it is never held overnight.
- **Level reversal exits** (owner, 8 November 2026): a level reversal trade runs until its stop (6 pips beyond the furthest point price reached) or its 20-pip take profit at IG, the close 15 minutes before big news, or 20:30 UK, when any level reversal trade still open is closed, every day. The close on a rejection at a level does not apply to it.
- **Bollinger bounce break-even** (owner, 13 November 2026; change 4 of `docs/research/bounce_changes_20261113.md`, +6.1 pips over 25 October to 13 November 2026, the only one of the four changes tested that gained): once a bounce has been 6 pips in profit (`bounce.break_even_after_pips`; its best so far, from an earlier candle or, live, an earlier price), its stop is moved at IG to break-even, the price the trade opened at (IG's level). The move is made at IG and counts only once IG confirms it: from then on the stop at IG is at the open price, and a stop there closes the trade at 0 pips ("stopped by IG"). If IG refuses the move, or does not answer clearly and its position still shows the old stop, the old stop stays (at IG and in the bot's records), the owner gets a Telegram alert with IG's error, and the move is tried again every `orders.close_retry_seconds` until IG confirms it. After a restart a stop already moved is known from the order record. The other exits (the half close at the opposite band, the take profit, the close on a rejection at a level, the close before big news, 20:30) are unchanged.
- **Holding:** there is no profit lock except the slow grind's (above), and no stop moved except the bounce's break-even (above), and no close when the analyser's state changes (owner, 7 November 2026): a trade (except the EMA pullback, the breakout, the slow grind and the level reversal, which have their own exits) runs until one of the exits in this section closes it: the 12-pip stop or the 100-pip take profit at IG, the 20:30 close, the close 15 minutes before big news, the close at the opposite band (the range trade in full, the bounce by half), or the close on a confirmed rejection at a level against the trade.
- **EMA pullback exits** (owner, 7 November 2026): an EMA pullback trade runs until its 12-pip stop or its take profit at IG (30 pips; 100 pips, `TAKE_PROFIT_PIPS`, for a trade opened on a UK calendar day with a big release for the pair, owner's decision of 7 November 2026, or in the trend day's direction on a trend day, section 2.4, owner, 8 November 2026), or 20:30 UK on Friday, when any EMA pullback trade still open is closed. It is not closed at 20:30 on other days (it may be held overnight), not closed before big news, and the close on a rejection at a level does not apply to it. It may open at any time the market is open except after 20:30 UK on Friday and from 21:55 to 22:15 UK (the rollover), and during a big-news window (section 6).
- **At a level:** the trade stays open while price is only wobbling. If price is rejected at the level against the trade, the trade closes at the same moment a bounce the other way would open: when the live price breaks past the confirmation candle. This never depends on a trade the other way being allowed.
- **Distance travelled** does not force a close on its own.
- **Reversal watch times:** 10:00, 11:00, 13:00, 14:00, 16:00 and 17:00 UK, from 20 minutes before to 20 minutes after. In those windows a rejection at any level counts; outside them, only at levels where several line up.
- **A change of market state** does not close a trade on its own; it is information for the trade manager.
- **Trend days:** see 2.4. The expected news direction takes precedence over rejections at levels.
- **At the opposite band** (owner, 11 November 2026; changes 2 and 3 of `docs/research/management_and_targets_20261111.md`, put live exactly as tested together with the 12-pip stop: +1,181.6 pips in 164 trades against +1,128.4 in 170 over 25 October to 11 November 2026): the **range trade closes in full** when price reaches the opposite Bollinger band (50% before); the **Bollinger bounce closes half** there, and the rest goes on to its normal exits (the stop, the 100-pip take profit, the close on a confirmed rejection at a level, the close 15 minutes before big news, 20:30). The band is the one at the last finished candle. The close is priced at the price IG would give: the band on the side the trade closes on (a sell's band plus the spread), rounded to IG's tenth of a pip against the trade, or the price itself if it is already past the band; live, the record has IG's confirmed level. Settings `range_trade.close_percent_at_opposite_band` (100) and `bounce.close_percent_at_opposite_band` (50), each 50 or 100 (the bounce's may also be 0), since the order sender closes in full or by half only.
- **Closed by a bounce against it** (owner, 11 November 2026; section 3.3, the pace and target rule): a Bollinger bounce that opens against open trend trades, at a significant level with price moving slowly, closes every trade open in the opposite direction at that moment. A bounce that is not at such a level, or comes while price is moving fast, is refused and the trend trades are held.
- **Decisions:** each open trade is always in one of: hold, watching a level, half close, close, forced close (news or 20:30), stopped by IG, take profit hit at IG. The bounce's break-even is recorded as "stop moved" (IG confirmed it) or "stop not moved" (IG did not; tried again), without changing the trade's decision.
- For every trade closed at a level, the bot records which levels lined up.

**Built (stage 12, `trade_manager/manager.py`, not connected to the live service yet):** the trade manager runs each open trade by the exits above, on each price bar in this order: the bounce's break-even (the stop moved at IG, before the bar is looked at, once the trade was 6 pips up in an earlier bar or price); the scheduled close (20:30, Friday 20:30, or 15 minutes before big news, each strategy as above); the stop at IG (at break-even once moved) or the slow grind's lock; the close at the opposite band (the range trade in full, the bounce by half; the band at the last finished candle); the take profit at IG; the close on a confirmed rejection at a level (from the bar after the entry bar, for the bounce and the range trade, not for a trade in the day's expected news direction on a big-news day). It tells the order sender to make the bot's own closes (in full or by half) and records IG's stop and take profit without sending anything for them. `python -m trade_manager.replay_check` confirms that over 26 October to 6 November 2026 every trade closes at the same time and price as in `docs/research/all_strategies_together_20261108.md`.

Functional test: a profitable sell is held through a temporary wobble at S2 (6 November 2026, about 07:30 to 08:30) and closes only on a confirmed rejection.

---

## 5. Levels

All levels use the sell (bid) price, with daily candles running midnight to midnight UK, to match Johnny's IG chart, which is set to the sell price. Trades still open and close at IG's real buy or sell price as normal.

- Daily pivot, R1–R3 and S1–S3 from the previous day's daily candle. Monday's pivots come from the short Sunday daily candle, as IG's chart does.
- Round numbers ending in 00 and 50.
- The previous day's high and low.
- London and New York session highs and lows (times are settings; starting values from 161 for Johnny to confirm).
- Turning levels: hourly highs and lows where price clearly reversed, in the last 2 weeks.
- Levels line up when within 5 pips of each other, pivot included. A setting.
- A candle that comes within 3 pips of a level counts the same as a pierce of that level, for rejections (a setting). For the bounce this applies to levels only: the Bollinger band needs a real pierce. For the range trade, a candle within 3 pips of the band counts as reaching it (3.4; owner, 13 November 2026).
- The levels that matter most: S2, R2, the daily pivot, round numbers and turning levels.

Example: on 5 November 2026 the fall from 07:00 stopped at about 1.3446 to 1.3450, a round number next to an earlier level, and price shot back up at 12:00.

---

## 6. Limits

- Size: £10 per pip.
- Trades open at once: 1 per strategy (the slow grind too: one trade at a time, owner, 8 November 2026); the level reversal up to 2 at once (owner, 13 November 2026; `level_reversal.max_open_trades`; one from 8 November); the bounce may also have 1 in the opposite direction. The EMA pullback is not limited to one trade at a time: it may have several trades open at once, each managed on its own (owner, 7 November 2026). Most at once: 5. EMA pullback trades do not count towards that limit (owner, 7 November 2026).
- **Total risk** (owner, 8 November 2026): every open trade's risk (its stop distance x its size) plus the new trade's may not be more than £100,000 (`safety.max_total_risk_gbp`), set so it is never reached.
- **Available funds** (owner, 8 November 2026): a new trade is allowed only if the account's available funds are at least the margin for one trade, £5,000 at £10 a pip (`safety.margin_per_trade_gbp`). The available funds come from IG's account details, read at start-up and again whenever a trade opens or closes, never as an extra call before each trade. If IG refuses a trade for lack of funds, Johnny gets a Telegram alert (section 7).
- **Built (stage 10, `safety/rules.py`):** the safety part decides whether a new order may go out from what it is given (the idea and its order, the open trades, the account's available funds, the time, the pause switch), giving every reason it refuses: the pause switch (blocks every new trade); the strategy's switch; each strategy's hours, news and Friday rules (above and section 4); the trades open at once (each strategy's own limit; at most 5, `limits.max_open_trades`, not counting the EMA pullback's); the size (£10 a pip); the total risk; the available funds (unknown funds refuse); one view at a time (above: no reversal trade against a strong push or against the day's direction on an exception day; the trading engine gives it the day's directions, worked out from the calendar and the stored candles). It never contacts IG.
- **One view at a time** (owner, 9 November 2026): the best combination of `docs/research/one_view_20261109.md` (rank 1 of "The 10 best combinations", +1120.9 pips over 26 October to 9 November 2026 against +1083.2 with the earlier rules), exactly as tested. A **reversal trade** is every Bollinger band bounce, and a level reversal that trades against the analyser's trend direction (the trend's direction in an emerging trend or a trend; in a possible reversal, the direction of the trend being reversed; a level reversal in ranging has no trend to go against, so it is not a reversal). The EMA pullback, slow grind, breakout and range trade are never reversal trades. Two rules, checked by the safety rules before each order:
  1. **No reversal trade against a strong push:** refused while the analyser's state (after the last finished candle, as the strategies see it) is a trend of the strong-push type in the other direction.
  2. **No reversal trade against the day's direction** on an exception day, all day (each UK day; `analyser/day_direction.py`): on a **big-news day**, against the day's expected news direction (2.4, as the trade manager uses it); on a **trend day**, against the trend day's direction (2.4: a sell on a trend day downwards, a buy upwards); on the **Monday after a Friday whose daily candle moved 80 pips or more** (sell price, open to close, UK day; `safety.big_friday_move_pips`), against the direction that reclaims Friday's move (Friday fell: no reversal sell; Friday rose: no reversal buy). If a day has more than one of these and they disagree, a reversal trade against any of them is refused.
  Nothing else changes: open trades are not closed because of these rules, and the other strategies' trades are not affected.
- Trading hours (UK clock time): new trades from 06:00 to 20:30 (switches in `.env`, section 13). Any trade open at 20:30 is closed. Nothing held overnight. A trade opened just before 20:30 is simply closed at 20:30.
- **EMA pullback hours** (owner, 7 November 2026): the EMA pullback may open at any time the market is open, not only 06:00 to 20:30, except after 20:30 UK on Friday: no new EMA pullback trade opens then, so none is ever held over the weekend. Nor from 21:55 to 22:15 UK (`ema_pullback.rollover_no_new_trades_from`, `ema_pullback.rollover_no_new_trades_until`; owner, 13 November 2026): IG's spread jumps to about 17 pips at the 22:00 rollover, and an EMA pullback opened then was stopped at once. It may be held overnight: it is not closed at 20:30, except on Friday, when any EMA pullback trade still open at 20:30 UK is closed. All other strategies keep the hours above.
- **Slow grind hours** (owner, 8 November 2026): the slow grind may open at any time the market is open, not only 06:00 to 20:30, except: from 20:30 UK to midnight every day (`hours.close_all_trades_at` to midnight); in the first 15 minutes after the market opens on Sunday (`slow_grind.week_open_no_new_trades_minutes`); and from 21:55 to 22:15 UK (`slow_grind.rollover_no_new_trades_from`, `slow_grind.rollover_no_new_trades_until`). With today's market hours (open Sunday 21:00 UK) the last two fall inside 20:30 to midnight; they are kept so they still hold if either changes. Any slow grind trade still open at 20:30 UK is closed, every day, so none is held overnight. It may open during a big-news window and is not closed before big news.
- **Level reversal hours** (owner, 8 November 2026): the hours above (new trades 06:00 to 20:30 UK, closed at 20:30 UK, nothing held overnight) and the big-news rule below (no new trade in the window, open trades closed 15 minutes before). It counts towards "most at once: 5".
- **Breakout hours** (owner, 7 November 2026): new breakout trades only from 06:00 to 20:30 UK, like the other strategies; it may open during a big-news window, may be held overnight, and any breakout trade still open at 20:30 UK on Friday is closed. One breakout trade open at a time (it counts towards "most at once: 5").
- **Per pair and in total (to be built with the safety rules):** every limit above will apply to each pair on its own, plus a total across all pairs switched on (for example the most trades open at once, and the total risk, across all pairs). Nothing is built for this yet.
- Big news: no new trades from 15 minutes before to 30 minutes after. Open trades closed 15 minutes before. This does not apply to the EMA pullback or the breakout (owner, 7 November 2026), or the slow grind (owner, 8 November 2026): they may open during the window, and their open trades are not closed before big news. Medium and small news ignored. Which releases count as big comes from AutoBot's own small, medium and big table (built: the owner's table from AutoBot 161, copied as data into `config/news_table.toml`, plus a GBP "Interest Rate" row for the Bank of England decision; `docs/NEWS.md`). News times and figures from Finnhub (built: `news/`, fetched a few times a day by the price service). If the news data is missing or out of date, alert Johnny rather than block trading indefinitely (built: a Telegram problem alert; trading is not blocked by it).

---

## 7. Broker safety

- **Force open** on every order, so an opposite trade opens a new position rather than closing an existing one.
- **Confirmed with IG:** a trade only counts as open, closed or half closed once IG confirms it. On a timeout, check with IG before trying again, so nothing is ever opened or closed twice.
- **Restart recovery:** on start-up, find the bot's own positions at IG using the saved deal references, take over managing them, and only then allow new trades. Never touch positions the bot did not open.
- **Stop check** (owner, 8 November 2026): IG's dealing rules are not fetched before trades; the bot assumes each strategy's own stop meets IG's minimum stop distance. Only if IG refuses a trade because of its stop does the bot fetch IG's current minimum once, record it (`safety.folder`), and send Johnny a Telegram alert with the strategy, its stop and IG's minimum (`safety/refusals.py`). Never widen the stop quietly.
- **Lack of funds:** if IG refuses a trade for lack of funds, Johnny gets a Telegram alert (`safety/refusals.py`).
- **Built (stage 11, `orders/sender.py`):** the order sender does all of the above using the price service's IG login (never a second one), on the demo account only. It records its own deal reference before each order, counts a trade only once IG confirms it, checks with IG by that reference on a timeout or unclear answer and never sends a trade twice (`orders.unclear_checks`), runs the safety rules before each order, reads the available funds at start-up and whenever a trade opens or closes, recovers its own trades at start-up before any new trade (positions it did not open are left alone and reported), and closes trades in full or by half (the Bollinger bounce at the opposite band; the range trade only if set to half), confirmed with IG. Every order, confirmation, refusal and close is recorded (`orders.folder`). Its open and confirm requests match AutoBot 161's `open_sb_now.py` exactly (owner, 8 November 2026): `POST /positions/otc` with `VERSION: 2` and `Content-Type: application/json`, the same 17 body fields (force open always true, the stop always `stopDistance`: the level reversal's stop price becomes a distance from the current price when the order is sent); `GET /confirms/{reference}` with `VERSION: 1`, up to 5 times a second apart while IG answers 404. Its close matches AutoBot 161's `close_sb_now.py`: `POST /positions/otc` with `VERSION: 1` and `_method: DELETE`, the body `dealId`, `direction` (the opposite), `orderType` MARKET and `size` only, never the epic or expiry; a part close (the bounce's half) sends the smaller size, and since IG leaves the rest as a position with a new deal ID, the order sender finds it among the open positions and records the new deal ID. It moves the bounce's stop to break-even (owner, 13 November 2026, section 4): it reads IG's open position (`GET /positions/{dealId}`, `VERSION: 2`) for its take profit, then updates it (`PUT /positions/otc/{dealId}`, `VERSION: 2`, the body `stopLevel` (the open price), `limitLevel` as IG has it so the take profit is never removed, `trailingStop` false, `trailingStopDistance` and `trailingStopIncrement` null, `guaranteedStop` false) and confirms it (`GET /confirms/{reference}`). The rule that a stop is always sent as `stopDistance` is for orders; moving the stop of an open position to a price is a level. A move IG does not confirm leaves the old stop, alerts the owner, and is tried again. Not yet called by the strategies: the trade manager will call it. The owner's one test order runs inside the price service from a request file (`orders/test_order.py`), and so do the owner's extras (a) restart recovery, (b) half close and (c) stop refusal, one at a time from a queue, and a read-only check of IG's own records (`orders/ig_records.py`).
- **Closes only when IG confirms them, and the bot's trades checked against IG (owner, 10 November 2026):** at 20:30 UK on 10 November IG refused the bot's two 20:30 closes (`error.service.marketdata.position.notional.details.null.error`) and the bot recorded both trades as closed anyway. IG's own records showed why IG refused: both positions were already closed (17:12 and 17:56 UK, channel SYSTEM, not their stops or limits; the owner had closed them by hand, as three others on 9 November at 15:21), and the bot had not noticed. The request itself was the same as AutoBot 161's `close_sb_now.py`. Now (a) a trade is closed in the records only once IG confirms the close: a refused or unclear close leaves it open, alerts the owner at once with IG's error and is tried again every `orders.close_retry_seconds`; (b) after a refused close IG is asked whether the position still exists, and one IG had already closed is recorded with IG's own close level and time from IG's activity; (c) at start-up and after every 5-minute candle the order sender compares the bot's open trades with IG's open positions and alerts every difference (a trade IG no longer has, a size that differs, a position the bot did not open); (d) IG's stops and take profits are recorded at IG's level; (e) after a restart, a trade taken over gets its close recorded (before, the records could only close trades opened since the last start).
- **The owner's closes by hand are kept apart (owner, 11 November 2026):** a trade IG shows closed on channel SYSTEM but not at its stop or take profit (at or beyond either counts as the stop or limit) was closed by the owner by hand. It is recorded "closed by owner" (`closed_by: owner` in `trades.jsonl`) at IG's price and time, the owner gets a short Telegram message rather than a warning, and it is never counted in the bot's trades, wins, losses, pips or £: the daily and weekly summaries and the dashboard's trading history show it on its own line ("closed by you, not counted"), and research on live trades leaves it out. The six closes of 9 and 10 November were corrected in `trades.jsonl` to IG's figures (the original kept as `trades.jsonl.before-2026-11-11-correction`).
- **Every live close at IG's price and time (owner, 11 November 2026):** the bot's own closes (close, forced close, half close) are recorded at IG's confirmed level and the time IG confirmed them, no longer at the trade manager's decision price and the start of the 5-minute candle (on 10 November the 10:40 and 14:55 closes were IG's 10:45:02 at 13430.9 and 15:00:02 at 13375.1); IG's stops and take profits already were. The bot's older closes of 9 to 11 November were corrected to IG's figures in `trades.jsonl` (the file before kept as `trades.jsonl.before-2026-11-11-ig-prices`): 22 trades of the bot's own, 5 won, 17 lost, -40.6 pips (-£406.00), equal to IG's booked results.
- **IG login rules:** stop on any login failure; never retry in a loop. Exceptions: being slowed down by IG (wait 60, 90, 120, 180 seconds, then stop) and client-token-invalid (one controlled re-login). A 412 on the account switch is harmless. Switch account without changing IG's default. Exit code 78 means do not restart.
- The new AutoBot is now the only bot using this IG account. The FXi briefing on 178 runs separately.

---

## 8. Candle store and IG's history allowance

- The bot never exceeds IG's history allowance (10,000 points a week for the whole account). The allowance, the bot's weekly budget and the block marker are **shared by all pairs**: every pair's requests go through the same door and count against the same budget. It keeps its own smaller weekly budget, counts points before every request, saves the count straight away, and records IG's own figures from every reply.
- Only one guarded part of the code may ask IG for history. A refusal writes a block marker that survives restarts.
- History is only requested for a candle genuinely missing during market hours. It only fills gaps and never overwrites stored candles, with one exception: when a gap fill completes missing 5-minute candles, any bigger candle that was built from an incomplete set is rebuilt from the full set, and the old one is archived, never deleted.
- History requests are sent to IG in UK time (IG reads them that way); every stored time stays UTC. Every reply is saved before it is checked. IG's own weekly, daily and hourly candles (filled 7 November 2026) are kept with the bot's own; IG's weekly candles, labelled Monday 00:00 UK by IG, are stored under the bot's Sunday 00:00 UK label, because their prices match the bot's weeks exactly.
- The weekend is never missing data. Market hours: open Sunday 21:00 UK, close Friday 17:00 New York time (22:00 UK most of the year, 21:00 in the clock-change weeks).
- Every candle keeps buy and sell prices separately, never mixed. Times stored in UTC, shown in UK time. Candles with a spread spike are stored as normal; only the rejection rules ignore their highs and lows (3.3).
- Daily candles run midnight to midnight UK, with IG's short Sunday candle, matching IG's chart. Hourly, 4-hour, daily and weekly are built from the bot's own 5-minute candles.
- Candles are kept, not deleted; older files are compressed. Logs are rotated by size and age. The store is checked automatically for gaps, duplicates and bad prices.
- The price stream runs all the time as a service. On a restart it records any gap and does not ask IG for history.
- Each pair has its own candle store (`data/candles/<PAIR>/`), gap records and levels (`data/levels/<PAIR>/`). A newly switched-on pair starts with an empty store and is **never filled from IG's history automatically**: its one-off fill needs Johnny's go-ahead, like GBPUSD's first fill.

---

## 9. Records, dashboard and alerts

**Each trade records:** direction, size, strategy, market state when it opened, time opened, open price, stop loss, take profit, time closed, close price, reason it closed, profit or loss, win or loss, and the levels that lined up.

**Dashboard:** the list of trades, the current market state, which strategies are allowed right now, warnings, and one switch labelled "pause new trades" (open trades are still managed while paused). Switching a single strategy on or off is a settings change.

**Telegram:** every trade opened, every trade closed, every problem.

- **Built (alerts/):** the Telegram sender, with a limit so the same problem never sends more than one message every 10 minutes (`alerts.same_problem_every_minutes`). The token and chat ID are secrets in `.env`, never printed or logged.
- **Ready messages:** on Sunday when every pair switched on has its first 5-minute candle of the week, and at 06:00 UK Monday to Friday. They confirm: logged in to IG, price stream connected, candles arriving for each pair, the candle store checks passed, and IG's remaining history allowance. The daily one adds each pair's pivot, S1 to S3, R1 to R3 and the analyser's direction. If any check fails, a problem alert naming each failed check is sent instead.
- **Problem alerts:** an IG login failure that stops the bot, the price stream going quiet while the market is open, any candle store problem (including a gap), a history block marker being written, and the price service crashing.
- **Trade alerts (connected, stage 14):** sent by the trading engine for every real trade (not for paper trades while `TRADING` is off). "Trade opened": the time; IG's deal reference; pair, direction, size, strategy and market state; the open price; the stop and take profit in pips, as prices, and the £ at risk; whether the take profit is the normal one or the 100 for a big-news day or a trend day; the reason in one line (for example "bounce: pierced S2 at 10:05, reversal 10:10, confirmed 10:15"); for the level reversal, the level and how far past it price went. "Trade closed": all of that, plus the close price and time, the reason it closed, pips and £, win or loss, how long it was open, the best profit it reached, for a half close (the bounce at the opposite band) the half close and the rest shown apart, and today's running total of trades and pips.
- **Daily summary** (owner, 8 November 2026): each weekday at 20:35 UK (`trading.daily_summary_at`): the trades closed that day, won and lost, pips and £, by strategy, and the week so far; marked as paper trades while `TRADING` is off.
- **Records (built, stage 14, `records/book.py`):** kept for good, never deleted or rewritten. `data/records/<PAIR>/trades.jsonl`: every trade when it opens and when it closes (everything in "Each trade records" above, plus the stop and take profit in pips, how long it was open, the best profit it reached and a half close and its rest); `decisions.jsonl`: every decision (ideas, allowed or blocked with the reasons; the order sender's answers and reasons; the analyser's state changes; the trade manager's decisions; the pause switch); daily and weekly summaries in `summaries/`. Paper trades in `data/records/<PAIR>/paper/`.
- **Pause switch:** while the file `trading.pause_file` exists no new trade is sent; open trades are still run. The dashboard sets it; each change is recorded and sent on Telegram.
- **Dashboard (built, stage 14; owner, 8 November 2026):** hosted as AutoBot 161's (nginx on port 3000, a password login page, a signed session cookie: `DASHBOARD_PASSWORD`, `DASHBOARD_SECRET_KEY` in `.env`), except that nginx listens **only on this server's Tailscale address** and the dashboard's data service only on 127.0.0.1. It shows the analyser's state and direction, the strategies allowed now, the open trades with live pips, today's trades and pips, warnings, whether `TRADING` is on, and the pause switch (protected against other websites pressing it: a csrf token from the session and an Origin check). **Trading history** (owner, 9 November 2026): AutoBot 161's date picker and Day / Week / Month / All buttons, exactly as in 161's page, reading the bot's own trade records instead of IG (back to the very first trade, no 30-day limit): the chosen day's or period's trades, totals (trades, wins, losses, pips, £) and a breakdown by strategy; real trades only unless the paper trades switch is on; today by default. Setting it up: `docs/DASHBOARD.md`.

---

## 10. Engineering rules

- Each part has one job and only talks to the others in agreed ways. Changing one part never breaks another.
- Every number lives in the settings file, or in the switches in `.env`, and is documented in `docs/SETTINGS.md` (a test enforces this for both).
- Every part works on one pair, given to it, and never assumes GBPUSD. A part given another pair's candle store stops at once.
- Technical tests check each part works. Functional tests check the analyser and strategies do what Johnny intends, using real past days where he knows from his chart what should have happened.
- All tests must pass before any commit (pre-commit hook).
- Documentation always matches the code.
- Commits as the autobot user, on main, pushed to the private repository JohnCarrington/AutoBot at the end of each stage once all tests pass. Never force push.
- Claude Code's reports are checked against the raw evidence before a stage is accepted.

---

## 11. Build plan

Done: 1 server, 2 project, 3 IG connection, 4 prices and candles (including the price service), 5 levels, 6 the rejection part, 7 part 1 (the analyser's indicators and direction rule), and any currency pair (section 13).

Remaining, in three rounds:

- **Round 1:** levels, the rejection part, the market analyser.
- **Round 2:** the four strategies, safety rules, order sender and trade manager, running on live prices without placing real trades.
- **Round 3:** records, dashboard, Telegram, then live on the demo account.

---

## 12. Known example days for functional tests

- **5 November 2026:** fall from 07:00 stopping at 1.3446 to 1.3450 (round number plus earlier level), sharp reversal up at 12:00. Pivot rejection just before midnight starting the downtrend into 6 November.
- **5 November 2026, Bank of England:** the 12:00 Bank of England rate decision was big news, so the bot must open no new trades between 11:45 and 12:30 (15 minutes before to 30 minutes after, as in section 6's news rules and settings `news.big_news_no_new_trades_before_minutes` and `news.big_news_no_new_trades_after_minutes`).
- **6 November 2026:** slow grind down from midnight; consolidation at S1 about 06:00 to 06:45; a sharp drop at 07:00 that was a UK news spike (Finnhub's GB releases at 07:00 UK: "House Price Index MoM" −0.6% against +0.1% expected and "Lloyds House Price Index YoY" −1.2% against −0.3%, both marked medium by Finnhub, so small news for the bot's news table), not the start of a real trend (owner, 12 November 2026), so the analyser calls no trend on it; wobble at S2 07:30 to 08:30; trend down from 09:50; reversal about 10:15 (not a possible reversal for the analyser: the trend down started at 08:20 and had moved 18.3 pips, under 30); flat at S2 11:30 to 12:45; no buy at 13:00 (direction rule); 13:30 news drives the day down to S3.
- **Market states, tested on the real candles** (`tests/functional/test_market_states_real_candles.py`): the pivot rejection around midnight gives an emerging trend down by 00:20 on 6 November, a trend down by 02:00 (with a short range at 01:10 in between, since ranging may end an emerging trend, owner, 13 November 2026); consolidation between 05:00 and 06:40; no trend on the 07:00 UK news spike, whose 07:05 candle is both the failed bounce and the new low (2.5: the bounce fails first, the new low after; owner, 12 November 2026), and a trend down at 09:50; no possible reversal between 10:15 and 10:45, and a possible reversal up at 14:30; a strong push down between 13:30 and 14:30; sell side at 13:00, so no buy; a restart at 09:00 gives exactly the states of a run that never stopped.
- **Known issue, to check in the no-trading run:** the market states change about 220 times a week (2 to 6 November: 220, of which 130 inside trading hours), with many short consolidation and emerging-trend spells (median 20 minutes; 70 under 15 minutes). Check whether strategies following them behave sensibly before trading.
- **Known shortfall, to revisit with more days:** the flat spell at S2 from 11:30 to 12:45 on 6 November is not yet called consolidation. (Measured: the bands are still wide, 14 to 24 pips until 12:10, and the middle band still sloping after the 10:15 bounce; the consolidation checks pass on one candle only, 12:35. It is not tested.)
---

## 13. Currency pairs and switches

- **Any pair, GBPUSD switched on.** Every part (IG connection, prices and candles, the candle store, levels, rejection, the analyser, the history door) takes the pair as an input and never assumes GBPUSD. A part given another pair's candle store stops at once.
- **Per-pair settings** (`[pairs.<PAIR>]` in `config/settings.toml`): IG's epic, the pip size (0.0001; 0.01 for JPY pairs) and IG's price scale (GBPUSD: 13354.4 means 1.33544, so 10000). Pip distances in the settings are turned into IG's points per pair.
- **Per-pair data:** each pair's candles and gap records in `data/candles/<PAIR>/`, its levels in `data/levels/<PAIR>/`, its history-fill records in `data/history/<PAIR>/`.
- **Shared:** one IG login and one price stream connection for all pairs switched on; one history door, with one weekly budget and IG's one allowance (section 8).
- **A newly switched-on pair is never filled from IG's history automatically.** Its one-off fill needs Johnny's go-ahead (`python -m prices.history_fill plan|go --pair <PAIR>`), like GBPUSD's first fill.
- **Limits** will be per pair plus a total across all pairs (section 6). Not built yet.
- **Switches in `.env`**, checked at start-up and documented in `docs/SETTINGS.md`: the pairs switched on (`PAIRS_ON`, GBPUSD only for now), the trading hours (`NEW_TRADES_FROM` 06:00, `NEW_TRADES_UNTIL` 20:30) the master switch `TRADING` (off: everything runs and is recorded, but no order is sent to IG), each strategy on or off (`STRATEGY_SLOW_GRIND` on, `STRATEGY_EMA_PULLBACK`, `STRATEGY_BOLLINGER_BOUNCE`, `STRATEGY_RANGE_TRADE`, `STRATEGY_BREAKOUT` off, `STRATEGY_LEVEL_REVERSAL`), and the stop loss and take profit sent to IG (`STOP_LOSS_PIPS` 12, the EMA pullback's own `STOP_LOSS_PIPS_EMA_PULLBACK` 12, `TAKE_PROFIT_PIPS` 100). Everything else stays in `config/settings.toml`.
- More detail: `docs/PAIRS.md`.
