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
6. **Strategies** (`strategies/`): slow grind, EMA pullback, Bollinger band bounce, range trade, breakout (switched off until its stop and take profit are chosen), level reversal (3.6), and the three session strategies: Asian range breakout (3.7), session sweep (3.8) and New York open reversal (3.9). Each checks its own entry rules.
7. **Safety rules** (`safety/`): size, number of trades, trading hours, news, total risk, pause switch.
8. **Order sender** (`orders/`): the only part that places, changes or closes trades at IG.
9. **Trade manager** (`trade_manager/`): looks after every open trade until it closes.
10. **Records** (`records/`), **dashboard** (`dashboard/`) and **alerts** (`alerts/`, Telegram).

**Put together (stage 13, `trading/engine.py`):** the strategies, safety rules, order sender and trade manager run inside the price service on its one IG login. After each finished 5-minute candle: the analyser takes it, the trade manager runs every open trade on it (including "watching a level"), the strategies run on it (the same code as the replay) and every idea goes to the order sender, which applies the safety rules before anything is sent. Every second, on the latest price: each waiting setup's trigger is checked (the 5-minute candle forming so far is given to copies of the strategies, the same code as for a finished candle), so a trade opens as soon as the live price reaches its trigger (section 3); then the trade manager runs the open trades on that price. When the candle finishes the strategies take it as always and an idea already sent live is not sent again; a trade opened during a candle is not run on that candle's earlier prices. Each open trade's best price so far, half close and "watching a level" are saved by the trade manager and restored after a restart. The master switch `TRADING` in `.env`: while it is off, everything runs and is recorded but no order is ever sent to IG (paper trades, `data/orders/<PAIR>/paper_orders.jsonl`). A problem in trading is reported and stops trading; the prices go on. `python -m trading.replay_check` confirms that over 26 October to 6 November 2026 the full wired path gives the same 161 trades as `docs/research/all_strategies_together_20261108.md`.

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
| Emerging trend | EMA pullback, breakout (3.5), in the trend's direction only. Not the slow grind (owner, 8 November 2026). Level reversal (3.6), either way |
| Trend | Slow grind (either type of trend, slow grind or strong push; owner, 8 November 2026), EMA pullback, breakout (3.5), in the trend's direction only; level reversal (3.6), either way |
| Possible reversal | Level reversal (3.6), either way |
| Consolidation | None (not even the level reversal). Watch and wait for a break |

- **Ranging:** the Bollinger bands are flat and close together, and price bounces between the upper and lower band. The EMAs weave back and forth instead of staying stacked, and the 100 EMA is flat. In numbers (owner, 7 November 2026): close together is a band width of at least 6 and at most 18 pips; flat is the upper band and the lower band each moving less than 0.2 pips a candle, measured over 6 candles; price bounces between the bands when both bands have been reached within 24 candles.
- **Emerging trend:** a direction is starting to form. Its main job is to stop bounces against the new direction early.
- **Trend:** an established direction, either a slow grind or a strong push. Both are recognised from price action.
- **Possible reversal:** after a trend has been running and price has moved at least 30 pips since it started, a strong reversal candle appears, recognised by the shared rejection part with no extra size rule.
- **Consolidation** (this includes a trend running out of steam): narrow Bollinger bands, price between them touching neither band, small candles with green and red roughly the same size, no direction. Unlike ranging, price stays in the middle. No trading. When price breaks out, the analyser moves to emerging trend.

### 2.3 Direction rule (applies to every strategy except the range trade, the Bollinger band bounce, the breakout, the slow grind, the level reversal and the three session strategies)

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
- **What it changes:** on a trend day, an EMA pullback or slow grind trade in the trend day's direction (back towards the monthly pivot: a sell on a trend day downwards, a buy on a trend day upwards) gets the 100-pip take profit of `TAKE_PROFIT_PIPS` instead of its usual take profit (section 4). Nothing else changes.

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

0. The trend must be established on the hourly chart: hourly 8, 13 and 20 EMAs in order and all rising, with the slope and gap minimums from 161's service as settings.
1. While a 5-minute candle is forming, the live price drops to the 5-minute 8 EMA. Price may cross the 8 and even the 13 EMA.
2. If a 5-minute candle closes below the 21 EMA, the setup is cancelled.
3. The entry price is 3 pips above the highest high (for a buy; 3 pips below the lowest low for a sell) of the five completed 5-minute candles immediately before the touch candle (AutoBot 161's rule).
4. The trade opens as soon as the live price reaches the entry price.
5. If it has not opened within 20 minutes, the setup expires.

EMAs: 8, 13 and 21 on the 5-minute chart. No fanning rule.

### 3.3 Bollinger band bounce (sell) (owner, 15 November 2026)

The bounce off the **hourly** Bollinger band, entered on the 5-minute chart. It replaced the earlier bounce (the 5-minute band or a level, the half close at the opposite band, the break-even, the close on a rejection at a level and the pace and target rule all went, owner, 15 November 2026). `strategies/bollinger_bounce/strategy.py`.

The bot records, for each bounce, how big the reversal candle was compared with the piercing candle, for later review. It never filters on it.

Spread spikes are ignored: when IG's spread on a candle is abnormally wide (over 3 pips, a setting; this happens at the 22:00 rollover and at news), that candle's sell-price highs and lows cannot start a setup or cancel one. The candle is still stored as normal.

### 3.4 Range trade (sell at the upper band)

1. One candle pierces the upper Bollinger band.
2. The next candle is a red rejection candle.
3. The sell opens as soon as the live price, during the candle after that, goes below the rejection candle's low.
4. If price goes above the rejection candle's high first, the setup is cancelled.

Half the trade closes when price reaches the other band.

Spread spikes are ignored as in the shared rejection part (`rejection.max_spread_pips`).

### 3.5 Breakout (owner, 7 November 2026)

1. It looks for a trade only at the moment the analyser moves into an emerging trend because price broke out of a range (two closes beyond the same band, section 2.5) or because a 5-minute candle closed outside the Bollinger band out of a consolidation: that candle is the breakout candle.
2. A buy (breakout up) opens as soon as price breaks above the breakout candle's high; a sell (breakout down) as soon as price breaks below its low.
3. If price does not break it within 3 candles after the breakout candle (`breakout.trigger_within_candles`), the setup expires.
4. It only takes a breakout in the direction of the day's move so far: a buy only when the entry price is above that day's 00:00 UK open, a sell only when it is below (the open of the 5-minute candle starting at 00:00 UK, sell price). The direction rule (2.3) does not apply to it.
5. Stop loss 6 pips (`breakout.stop_loss_pips`), take profit 50 pips (`breakout.take_profit_pips`). No close on a rejection at a level.
6. New trades only from 06:00 to 20:30 UK; it may open during a big-news window, may be held overnight and through news, and any breakout trade still open at 20:30 UK on Friday is closed (sections 4 and 6). One breakout trade open at a time.

**Pullback entry** (owner, approved 19 November 2026; while the switch `PULLBACK_ENTRY` is on, on if left out): the breakout does not open on the break. The breakout candle starts a wait: a candle whose low reaches the 5-minute 8 EMA (a sell: its high), then a close above the 8 EMA (a sell: below; the same candle may do both), within `pullback_entry.wait_candles` (6) candles after the breakout candle; the trade opens at the next candle's open (the 7th at the latest), never sent late. A close below the 21 EMA (a sell: above) cancels it. The day's-move rule (4) is judged at that entry price. Stop 6, take profit and management unchanged (`strategies/pullback.py`).

### 3.6 Level reversal (sell; owner, 8 November 2026)

**Switched on** (`STRATEGY_LEVEL_REVERSAL=on`). From the level reversal research of 8 November 2026 (`docs/research/level_reversal_tolerance_20261108.md`).

1. Only rejections at **round numbers ending in 00** (not 50), **S2** and **R2** (`level_reversal.level_types`, `level_reversal.round_numbers_every_pips`), found by the shared rejection part exactly as for the Bollinger band bounce (3.3 steps 1 to 3 and 5): price reaches the level or comes within 3 pips of it, the reversal candle, the confirmation candle.
2. The rejection counts only if price went no further past the level than its **allowance**: **12 pips at R2 and S2, 5 pips at round numbers** (owner, 8 November 2026; `level_reversal.allowance_pips_r2`, `level_reversal.allowance_pips_s2`, `level_reversal.allowance_pips_round_number`), measured as the furthest price reached from the piercing candle to the confirmation candle.
3. The sell opens as soon as price breaks below the confirmation candle's low (a buy, above its high).
4. **Stop 6 pips beyond the furthest point** price reached (`level_reversal.stop_beyond_furthest_pips`; for a sell, 6 pips above the highest high from the piercing candle to the confirmation candle), so the stop's distance from the entry varies; **take profit 20 pips** (`level_reversal.take_profit_pips`).
5. In every analyser state except consolidation, either way (2.2); the direction rule (2.3) does not apply.
6. New trades from 06:00 to 20:30 UK; closed at 20:30 UK; not opened in a big-news window and closed 15 minutes before big news, like the other strategies (section 6); one level reversal trade at a time; no close on a rejection at a level (section 4).
7. If several of these levels were reached, the first that passes rule 2 is the level (S2 and R2 before round numbers); several setups triggering on the same candle and direction give one trade.

### 3.7 Asian range breakout (owner, 16 November 2026)

**Switched on** (`STRATEGY_ASIAN_RANGE_BREAKOUT=on`). UK times, sell prices as on the chart (`strategies/asian_range_breakout/`).

1. **The Asian range:** the high and low of the 5-minute candles from 00:00 to 07:00 UK (`asian_range_breakout.range_from`, `range_until`).
2. From 07:00 to 10:00 UK (`breakout_from`, `breakout_until`) a 5-minute candle **closes above the Asian high (a buy) or below the Asian low (a sell)**. A wick does not count, nor a close exactly on the line. A candle closing at 09:55 opens at 10:00.
3. The trade opens at the **next candle's open** (live: its first price; never sent late, as the bounce).
4. **One trade each way per day:** once a trade that way has opened that day, no more (safety rule, section 6). A close whose trade was refused (for example in a big-news window) does not use up the day: a later close beyond the range can still open it (owner's answer 4).

**Pullback entry** (owner, approved 19 November 2026; while the switch `PULLBACK_ENTRY` is on, on if left out): only the first close beyond the Asian range each way each day starts a wait, with the breakout's rules (a candle reaching the 5-minute 8 EMA, then a close back beyond it, within `pullback_entry.wait_candles` (6) candles; cancelled by a close beyond the 21 EMA against it); the trade opens at the next candle's open. After a wait expires or is cancelled there is no new wait that day in that direction. Stop 12, trail and once a day unchanged.

### 3.8 Session sweep (sell; owner, 16 November 2026)

**Switched on** (`STRATEGY_SESSION_SWEEP=on`). UK times, sell prices (`strategies/session_sweep/`).

1. **The levels:** the Asian high and low (00:00 to 07:00, `session_sweep.asian_range_from`, `asian_range_until`), counted from 07:00; the London high and low from 07:00 to 12:00 (`london_range_from`, `london_range_until`), fixed at 12:00 and counted from then (owner's answer 5). Each level for the rest of its UK day.
2. **The sweep:** price goes at least 3 pips above the level (`session_sweep.beyond_pips`).
3. Then a 5-minute candle **closes back inside the level** (below it): the rejection candle. It may be the same candle that went beyond (answer 6), and price may stay beyond for any time that day (answer 7). Exactly: a candle closing below the level where the candles since the last close below it, this one included, went at least 3 pips above it.
4. **The confirmation candle** closes below the rejection candle's low within 3 candles of it (`session_sweep.confirmation_within_candles`), or the setup expires; price going above the rejection candle's high first cancels it (as the bounce, 3.3; answer 8). While a setup waits at a level, that level starts no other.
5. The trade opens at the **next candle's open** (live: its first price; never sent late).
6. **Stop:** 1 pip beyond the sweep's furthest point (`session_sweep.stop_beyond_furthest_pips`; the highest price from the first move beyond the level to the entry), and **at least 12 pips** from the entry (`session_sweep.min_stop_pips`; answer 9). Sent to IG as a distance from the price at sending, as the level reversal's.
7. **Each of the four levels at most once a day** for a trade (safety rule, section 6; answer 10).

### 3.9 New York open reversal (sell after a rise; owner, 16 November 2026)

**Switched on** (`STRATEGY_NEW_YORK_OPEN_REVERSAL=on`). UK times, sell prices (`strategies/new_york_open_reversal/`).

1. **The move:** from the open of the 07:00 candle to the close of the last candle before 13:30 UK (`new_york_open_reversal.move_from`, `move_until`), at least 30 pips one way (`min_move_pips`; answer 11).
2. Between 13:30 and 15:00 UK (`window_from`, `window_until`): a **rejection candle against the move**, red after a rise (green after a fall), whatever its size (answer 12). Every rejection candle starts its own setup.
3. **The confirmation candle** closes below the rejection candle's low within 3 candles of it (`confirmation_within_candles`); price going above the rejection candle's high first cancels it (as the bounce; answer 13). Both candles are in the window.
4. The trade opens at the **next candle's open** (live: its first price; never sent late).
5. **One trade a day** (safety rule, section 6; answer 14).
6. **No trade on a day with big news for the pair released at 13:30 UK** (`no_trade_if_big_news_at`; any release the news table counts as big for GBP or USD; answer 15).

**What the three session strategies share** (owner, 16 November 2026, with the owner's answers 1 to 15): a 12-pip stop (`asian_range_breakout.stop_loss_pips`, `new_york_open_reversal.stop_loss_pips`; the sweep's as 3.8), then **the trail behind the last 3 candles once 12 pips up**, exactly as the bounce's (section 4; each strategy's own `trail_from_pips` and `trail_candles`); the 100-pip take profit at IG (`TAKE_PROFIT_PIPS`; answer 1); new trades 06:00 to 20:30 UK, closed at 20:30 UK, no new trade in a big-news window and open trades closed 15 minutes before big news (answer 3); one trade at a time in each direction. They **open without hindrance, like the bounce**: not the analyser's state, the direction rule, the hourly read, the trend still going, the most at once nor one view at a time. No close on a rejection at a level. Every number is a setting in `config/settings.toml` (`[asian_range_breakout]`, `[session_sweep]`, `[new_york_open_reversal]`).

---

### 3.10 Entry filters (owner, 21 November 2026)

Two rules in one module, `strategies/entry_filters.py`, checked once for every trade at one point, just before it opens (`trading/engine.py`, before the order sender's safety rules). No strategy's own rules, stops, take profits or management change. Sell (chart) price throughout; the entry price is the strategy's own entry price (buys too). A refusal is recorded (`decisions.jsonl`, kind `entry filter refused`) with the rule and why.

**Rule 1, hourly context** (switch `HOURLY_CONTEXT`, on if left out; every strategy). DOWN context: the latest hourly swing high is lower than the one before it (a swing high: an hourly candle whose high has 2 lower highs on each side), the last finished hourly candle closed below the hourly 50 EMA, and the 50 EMA is lower than 6 hourly candles before. UP context: the mirror (higher swing low, close above, rising). In a DOWN context no buy opens within 5 pips of the daily pivot or the hourly 50 EMA; in an UP context no sell.

**Rule 2, entry near the 8 EMA** (switch `ENTRY_NEAR_EMA8`; off if left out since 21 November 2026, replaced by rule 2b; the code is kept). A sell opens only if its entry price is no more than 5 pips below the 5-minute 8 EMA (at the last finished 5-minute candle before the entry); a buy only if no more than 5 pips above it. The slow grind, the breakout, the Asian range breakout and the session sweep are exempt (the session sweep: owner, 21 November 2026). Numbers in `[entry_filters]`.

**Rule 2b, the RSI stretch** (switch `RSI_STRETCH`, on if left out; owner, 21 November 2026, in place of rule 2). No sell when the 5-minute RSI 3 (sell price, at the last finished 5-minute candle before the entry) is under 30; no buy when it is over 70. The slow grind, the breakout, the Asian range breakout and the session sweep are exempt. A refusal records the RSI and the strategy.

**Johnny's slow-grind trend day** (switch `TREND_DAY_RSI_OFF`, on if left out; owner, 21 November 2026; not the bot's own trend-day check in 2.4). It starts the first time a slow grind trade is in profit (more than 0 pips at the price IG would close it) at any moment from 06:00 up to 09:00 UK, in that trade's direction, and lasts until 20:30 UK. A slow grind trade the other way also in profit in that window cancels it for the rest of the day. On a trend day rule 2b does not apply to trades in the trend's direction; trades against it are still checked; rule 1 is unchanged. Live it is checked on every price, in a replay on the 5-minute candles. Its start (time, direction, the slow grind trade) and any cancel are recorded and shown on the dashboard; after a restart the day's record is read back.

## 4. Trade management

One shared trade manager for every trade.

- **Stop loss:** a fixed 6 pips for every strategy except the EMA pullback, the breakout and the slow grind, sent to IG. A switch in `.env` (`STOP_LOSS_PIPS`). The EMA pullback's stop is 12 pips (owner, 7 November 2026), its own switch in `.env` (`STOP_LOSS_PIPS_EMA_PULLBACK`). The breakout's is 6 pips (`breakout.stop_loss_pips`) and the slow grind's 15 pips (owner, 8 November 2026; `slow_grind.stop_loss_pips`), in `config/settings.toml`. The level reversal's stop is not a distance from the entry: it is 6 pips beyond the furthest point price reached (owner, 8 November 2026; `level_reversal.stop_beyond_furthest_pips`, section 3.6).
- **Take profit:** a fixed 100 pips sent to IG as a safety net, for every strategy except the EMA pullback, the breakout and the slow grind. A switch in `.env` (`TAKE_PROFIT_PIPS`). The EMA pullback's take profit is 30 pips (owner, 7 November 2026; `ema_pullback.take_profit_pips` in `config/settings.toml`) and the slow grind's 20 pips (owner, 8 November 2026; `slow_grind.take_profit_pips`), except that an EMA pullback or slow grind trade opened on a day with big news for the pair, or opened in the trend day's direction on a trend day (section 2.4, owner, 8 November 2026), gets the 100 pips of `TAKE_PROFIT_PIPS`. The breakout's is 50 pips (`breakout.take_profit_pips`) and the level reversal's 20 pips (owner, 8 November 2026; `level_reversal.take_profit_pips`), on any day. All are the bot's own rule, not an IG requirement.
- **Breakout exits** (owner, 7 November 2026): a breakout trade runs until its 6-pip stop or 50-pip take profit at IG (`breakout.stop_loss_pips`, `breakout.take_profit_pips`), or 20:30 UK on Friday, when any breakout trade still open is closed. It is not closed at 20:30 on other days (it may be held overnight), not closed before big news, and the close on a rejection at a level does not apply to it.
- **Slow grind exits** (owner, 8 November 2026): a slow grind trade runs until its 15-pip stop or its take profit at IG (20 pips; 100 pips, `TAKE_PROFIT_PIPS`, for a trade opened on a UK calendar day with a big release for the pair, or in the trend day's direction on a trend day, section 2.4), the profit lock, or 20:30 UK, when any slow grind trade still open is closed, every day. **Profit lock 15/10:** once the trade has been 15 pips in profit (`slow_grind.lock_from_pips`), it is closed if price comes back to 10 pips in profit (`slow_grind.lock_at_pips`); the lock applies from the candle after the one that reached 15 pips. It is not closed before big news, and the close on a rejection at a level does not apply to it. It never opens from 20:30 UK to midnight, so it is never held overnight.
- **Level reversal exits** (owner, 8 November 2026): a level reversal trade runs until its stop (6 pips beyond the furthest point price reached) or its 20-pip take profit at IG, the close 15 minutes before big news, or 20:30 UK, when any level reversal trade still open is closed, every day. The close on a rejection at a level does not apply to it.
- **Holding:** there is no profit lock except the slow grind's (above), and no close when the analyser's state changes (owner, 7 November 2026): a trade (except the EMA pullback, the breakout, the slow grind and the level reversal, which have their own exits) runs until one of the exits in this section closes it: the 6-pip stop or the 100-pip take profit at IG, the 20:30 close, the close 15 minutes before big news, the range trade's half close at the opposite band, or the close on a confirmed rejection at a level against the trade.
- **EMA pullback exits** (owner, 7 November 2026): an EMA pullback trade runs until its 12-pip stop or its take profit at IG (30 pips; 100 pips, `TAKE_PROFIT_PIPS`, for a trade opened on a UK calendar day with a big release for the pair, owner's decision of 7 November 2026, or in the trend day's direction on a trend day, section 2.4, owner, 8 November 2026), or 20:30 UK on Friday, when any EMA pullback trade still open is closed. It is not closed at 20:30 on other days (it may be held overnight), not closed before big news, and the close on a rejection at a level does not apply to it. It may open at any time the market is open except after 20:30 UK on Friday, and during a big-news window (section 6).
- **At a level:** the trade stays open while price is only wobbling. If price is rejected at the level against the trade, the trade closes at the same moment a bounce the other way would open: when the live price breaks past the confirmation candle. This never depends on a trade the other way being allowed.
- **Distance travelled** does not force a close on its own.
- **Emerging-trend ladder** (Johnny's exit, owner, 21 November 2026; switch `EMERGING_LADDER`, on if left out; numbers in `[emerging_ladder]`): only for a trade opened while the analyser said "emerging trend" (up or down), as recorded on the trade at open; every strategy. Once the trade is +10 pips, its stop at IG moves to +5; once it is +15, to +10. Pips as IG closes it (a buy on the sell price, a sell on the buy price), from the price it opened at, checked after every price from the best reached so far. The stop never moves backwards; where the strategy has its own trail or stop move, whichever stop is tighter wins at each step. The moves go through the trail's stop-move code (the nearest level IG allows, counted only once IG confirms it, 3 attempts then tried again after the next finished candle). Take profit unchanged; trades opened in any other state unchanged. Each stop move is recorded on the trade (`stop_moves` in its closing record) and in the decisions.
- **Reversal watch times:** 10:00, 11:00, 13:00, 14:00, 16:00 and 17:00 UK, from 20 minutes before to 20 minutes after. In those windows a rejection at any level counts; outside them, only at levels where several line up.
- **A change of market state** does not close a trade on its own; it is information for the trade manager.
- **Trend days:** see 2.4. The expected news direction takes precedence over rejections at levels.
- **Range trade:** closes 50% at the opposite band; the rest is managed like any other trade.
- **Decisions:** each open trade is always in one of: hold, watching a level, half close, close, forced close (news or 20:30), stopped by IG, take profit hit at IG.
- For every trade closed at a level, the bot records which levels lined up.

**Built (stage 12, `trade_manager/manager.py`, not connected to the live service yet):** the trade manager runs each open trade by the exits above, on each price bar in this order: the scheduled close (20:30, Friday 20:30, or 15 minutes before big news, each strategy as above); the stop at IG or the slow grind's lock; the range trade's half close at the opposite band (the band at the last finished candle); the take profit at IG; the close on a confirmed rejection at a level (from the bar after the entry bar, for the bounce and the range trade, not for a trade in the day's expected news direction on a big-news day). It tells the order sender to make the bot's own closes (in full or by half) and records IG's stop and take profit without sending anything for them. `python -m trade_manager.replay_check` confirms that over 26 October to 6 November 2026 every trade closes at the same time and price as in `docs/research/all_strategies_together_20261108.md`.

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
- A candle that comes within 3 pips of a level counts the same as a pierce of that level, for rejections (a setting). This applies to levels only: the Bollinger band needs a real pierce.
- The levels that matter most: S2, R2, the daily pivot, round numbers and turning levels.

Example: on 5 November 2026 the fall from 07:00 stopped at about 1.3446 to 1.3450, a round number next to an earlier level, and price shot back up at 12:00.

---

## 6. Limits

- Size: £10 per pip.
- Trades open at once: 1 per strategy (the slow grind and the level reversal too: one trade of each at a time, owner, 8 November 2026); the Bollinger bounce one at a time in each direction (owner, 15 November 2026). The EMA pullback is not limited to one trade at a time: it may have several trades open at once, each managed on its own (owner, 7 November 2026). Most at once: 5. EMA pullback trades do not count towards that limit (owner, 7 November 2026). The Bollinger bounce is not held back by it (its trades still count towards it for the others; owner, 15 November 2026). The three session strategies (3.7 to 3.9; owner, 16 November 2026) as the bounce: one at a time in each direction, not held back by the most at once, nor by one view at a time.
- **Once a day** (owner, 16 November 2026): the Asian range breakout one trade each way per day, the session sweep one trade per level per day, the New York open reversal one trade a day. Counted from the trades that opened (or were sent and are not yet settled), never from refused ones; each trade's once-a-day key is kept in the order record, so a restart does not forget it.
- **Total risk** (owner, 8 November 2026): every open trade's risk (its stop distance x its size) plus the new trade's may not be more than £100,000 (`safety.max_total_risk_gbp`), set so it is never reached.
- **Available funds** (owner, 8 November 2026): a new trade is allowed only if the account's available funds are at least the margin for one trade, £5,000 at £10 a pip (`safety.margin_per_trade_gbp`). The available funds come from IG's account details, read at start-up and again whenever a trade opens or closes, never as an extra call before each trade. If IG refuses a trade for lack of funds, Johnny gets a Telegram alert (section 7).
- **Built (stage 10, `safety/rules.py`):** the safety part decides whether a new order may go out from what it is given (the idea and its order, the open trades, the account's available funds, the time, the pause switch), giving every reason it refuses: the pause switch (blocks every new trade); the strategy's switch; each strategy's hours, news and Friday rules (above and section 4); the trades open at once (each strategy's own limit; at most 5, `limits.max_open_trades`, not counting the EMA pullback's); the size (£10 a pip); the total risk; the available funds (unknown funds refuse). It never contacts IG.
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
- **Built (stage 11, `orders/sender.py`):** the order sender does all of the above using the price service's IG login (never a second one), on the demo account only. It records its own deal reference before each order, counts a trade only once IG confirms it, checks with IG by that reference on a timeout or unclear answer and never sends a trade twice (`orders.unclear_checks`), runs the safety rules before each order, reads the available funds at start-up and whenever a trade opens or closes, recovers its own trades at start-up before any new trade (positions it did not open are left alone and reported), and closes trades in full or by half (the range trade), confirmed with IG. Every order, confirmation, refusal and close is recorded (`orders.folder`). Its open and confirm requests match AutoBot 161's `open_sb_now.py` exactly (owner, 8 November 2026): `POST /positions/otc` with `VERSION: 2` and `Content-Type: application/json`, the same 17 body fields (force open always true, the stop always `stopDistance`: the level reversal's stop price becomes a distance from the current price when the order is sent); `GET /confirms/{reference}` with `VERSION: 1`, up to 5 times a second apart while IG answers 404. Its close matches AutoBot 161's `close_sb_now.py`: `POST /positions/otc` with `VERSION: 1` and `_method: DELETE`, the body `dealId`, `direction` (the opposite), `orderType` MARKET and `size` only, never the epic or expiry; a part close (the range trade's half) sends the smaller size, and since IG leaves the rest as a position with a new deal ID, the order sender finds it among the open positions and records the new deal ID. Not yet called by the strategies: the trade manager will call it. The owner's one test order runs inside the price service from a request file (`orders/test_order.py`), and so do the owner's extras (a) restart recovery, (b) half close and (c) stop refusal, one at a time from a queue, and a read-only check of IG's own records (`orders/ig_records.py`).
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
- **Trade alerts (connected, stage 14):** sent by the trading engine for every real trade (not for paper trades while `TRADING` is off). "Trade opened": the time; IG's deal reference; pair, direction, size, strategy and market state; the open price; the stop and take profit in pips, as prices, and the £ at risk; whether the take profit is the normal one or the 100 for a big-news day or a trend day; the reason in one line (for example "bounce: pierced S2 at 10:05, reversal 10:10, confirmed 10:15"); for the level reversal, the level and how far past it price went. "Trade closed": all of that, plus the close price and time, the reason it closed, pips and £, win or loss, how long it was open, the best profit it reached, for the range trade the half close and the rest shown apart, and today's running total of trades and pips.
- **Daily summary** (owner, 8 November 2026): each weekday at 20:35 UK (`trading.daily_summary_at`): the trades closed that day, won and lost, pips and £, by strategy, and the week so far; marked as paper trades while `TRADING` is off.
- **Records (built, stage 14, `records/book.py`):** kept for good, never deleted or rewritten. `data/records/<PAIR>/trades.jsonl`: every trade when it opens and when it closes (everything in "Each trade records" above, plus the stop and take profit in pips, how long it was open, the best profit it reached and the range trade's half close and rest); `decisions.jsonl`: every decision (ideas, allowed or blocked with the reasons; the order sender's answers and reasons; the analyser's state changes; the trade manager's decisions; the pause switch); daily and weekly summaries in `summaries/`. Paper trades in `data/records/<PAIR>/paper/`.
- **Pause switch:** while the file `trading.pause_file` exists no new trade is sent; open trades are still run. The dashboard sets it; each change is recorded and sent on Telegram.
- **Dashboard (built, stage 14; owner, 8 November 2026):** hosted as AutoBot 161's (nginx on port 3000, a password login page, a signed session cookie: `DASHBOARD_PASSWORD`, `DASHBOARD_SECRET_KEY` in `.env`), except that nginx listens **only on this server's Tailscale address** and the dashboard's data service only on 127.0.0.1. It shows the analyser's state and direction, the strategies allowed now, the open trades with live pips, today's trades and pips, warnings, whether `TRADING` is on, and the pause switch (protected against other websites pressing it: a csrf token from the session and an Origin check). Setting it up: `docs/DASHBOARD.md`.

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
- **6 November 2026:** slow grind down from midnight; consolidation at S1 about 06:00 to 06:45; strong push down 06:45 to 07:30; wobble at S2 07:30 to 08:30; reversal about 10:15; flat at S2 11:30 to 12:45; no buy at 13:00 (direction rule); 13:30 news drives the day down to S3.
- **Market states, tested on the real candles** (`tests/functional/test_market_states_real_candles.py`): the pivot rejection around midnight gives an emerging trend down by 00:20 on 6 November, a trend down by 02:00; consolidation between 05:00 and 06:40; a strong push down between 06:45 and 07:30 and again between 13:30 and 14:30; a possible reversal up between 10:15 and 10:45; sell side at 13:00, so no buy; a restart at 09:00 gives exactly the states of a run that never stopped.
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
- **Switches in `.env`**, checked at start-up and documented in `docs/SETTINGS.md`: the pairs switched on (`PAIRS_ON`, GBPUSD only for now), the trading hours (`NEW_TRADES_FROM` 06:00, `NEW_TRADES_UNTIL` 20:30) the master switch `TRADING` (off: everything runs and is recorded, but no order is sent to IG), each strategy on or off (`STRATEGY_SLOW_GRIND` on, `STRATEGY_EMA_PULLBACK`, `STRATEGY_BOLLINGER_BOUNCE`, `STRATEGY_RANGE_TRADE`, `STRATEGY_BREAKOUT` off, `STRATEGY_LEVEL_REVERSAL`), and the stop loss and take profit sent to IG (`STOP_LOSS_PIPS` 6, the EMA pullback's own `STOP_LOSS_PIPS_EMA_PULLBACK` 12, `TAKE_PROFIT_PIPS` 100). Everything else stays in `config/settings.toml`.
- More detail: `docs/PAIRS.md`.

## Structural Trade Planner V1 (owner, 17 November 2026): observe only

The owner approved the Structural Trade Planner's 38 architectural decisions, its seven parameter groups and FC-01 to FC-13 (with three adjustments: a recommendation is issued on the first analysis with all the evidence; the 4-hour 40-pip and daily 110-pip swing moves are provisional and turns they hold back are recorded; the zone width, the larger of 5 pips and 0.15 x the 20-day ADR, is provisional). The full design and registers are in `/home/autobot/research/structural_trade_planner_v1/` (also in the reports repository). This stage is **observe only**: the planner (`planner/`) forecasts and records but does not authorise, refuse, open, change or close any trade, and nothing in the trading path reads it. It runs only while the switch `PLANNER_OBSERVE` is on (off until the owner approves installation). Letting it authorise hourly-pierce bounces is a later stage needing separate, explicit approval.

---

## first-build-plus (owner, 19 November 2026)

This branch is the first build (f99efe1, live on the IG demo from 9 November 2026 00:09 UTC) with the market analyser
exactly as it was then, plus only the following. Everything else after f99efe1 is left out: the hourly read, the
analyser control, Stage 4, "one view at a time", the pace and target rule, "trend still going",
and every other strategy change.

**Kept as on main:**

1. **The dashboard** (`dashboard/`), with the STP tab.
2. **The Structural Trade Planner** (`planner/`, observe only, `PLANNER_OBSERVE`, off if left out), unchanged, except
   that its "confirmed close beyond a level" number is its own setting, `[planner] break_beyond_pips` (3). On main
   it reads `[hourly_read] break_beyond_pips`, which this branch does not have. Its "link to the bounce"
   (`PLANNER_AUTHORISES_BOUNCE`) was never built on main either, so there is none here.
3. **The hourly-pierce Bollinger bounce** of 15 November (section 3.3 as on main; `strategies/bollinger_bounce`,
   recorded as "Bollinger bounce"), with what it needs:
   - its hourly chart (`prices/hourly_chart.py`);
   - opening at the next candle's first live price, never sent late (`trading/engine.py`);
   - in every analyser state;
   - one each way, not held back by the total;
   - its 12-pip trail behind the last 3 finished candles, with stop moves at IG that IG can accept (3 attempts);
   - `BOUNCE_ONLY_NEAR_TIMES`.
   
   Its `BOUNCE_ONLY_WHEN_HOURLY_RANGING` switch is left out, because it needs the hourly read.

**Kept, renamed:** the first build's own bounce, **"Bollinger bounce 5m"** (`strategies/bollinger_bounce_5m`, switch
`STRATEGY_BOLLINGER_BOUNCE_5M`, required). These are exactly its 9 November rules:
- a 5-minute rejection at a level or the 5-minute band;
- trend: against the trend's direction only; possible reversal: either way;
- 1 each way, plus 1 more in the opposite direction (`limits.bollinger_bounce_extra_opposite_direction_trades`);
- closed on a confirmed rejection at a level;
- no trail.

Its two candle limits are now `[rejection] reversal_candle_within_candles_of_pierce` and
`confirmation_candle_within_candles_of_reversal` (same values), because `[bounce]` holds the new bounce's settings.
Records, Telegram and the dashboard show the two bounces by their names.

**Safety and plumbing fixes added:**
- the Telegram format (9 Nov);
- a close counts only when IG confirms it, and trades are checked against IG's positions (10 Nov);
- your closes by hand recorded apart (11 Nov);
- every close recorded at IG's price (11 Nov);
- the strategies read the candle store afresh (11 Nov);
- no new EMA pullback over the rollover, 21:55–22:15 UK (13 Nov);
- the analyser journal stays the live record (13 Nov);
- one try per strategy, direction and candle (16 Nov);
- trail stop moves IG can accept (17 Nov);
- the live check waits for IG's finished candle, and journal provenance (19 Nov).

**Added later the same day (owner, 19 November 2026): the three session strategies**, exactly as on main (design
3.7 to 3.9 there):
- the Asian range breakout (`strategies/asian_range_breakout`);
- the session sweep (`strategies/session_sweep`);
- the New York open reversal (`strategies/new_york_open_reversal`; the shared UK-day helpers are in
  `strategies/sessions.py`).

They come with their own rules, settings (`[asian_range_breakout]`, `[session_sweep]`, `[new_york_open_reversal]`) and
switches (`STRATEGY_ASIAN_RANGE_BREAKOUT`, `STRATEGY_SESSION_SWEEP`, `STRATEGY_NEW_YORK_OPEN_REVERSAL`, required, as
on main). Like the hourly-pierce bounce they:
- open without hindrance (every analyser state, no direction rule), at the next candle's open, never sent late;
- are limited to one each way, and not held back by the total;
- trail with their own `trail_from_pips` and `trail_candles`.

They bring their own safety rule 10, **once a day**:
- the Asian range breakout: one each way per day;
- the session sweep: one per level per day;
- the New York open reversal: one a day.

The New York open reversal also stays out on a day with big news at 13:30 UK. Their pivot rule is not added (a later
step). Nothing else from main came with them.
