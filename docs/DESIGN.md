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
6. **Strategies** (`strategies/`): slow grind, EMA pullback, Bollinger band bounce, range trade. Each checks its own entry rules.
7. **Safety rules** (`safety/`): size, number of trades, trading hours, news, total risk, pause switch.
8. **Order sender** (`orders/`): the only part that places, changes or closes trades at IG.
9. **Trade manager** (`trade_manager/`): looks after every open trade until it closes.
10. **Records** (`records/`), **dashboard** (`dashboard/`) and **alerts** (`alerts/`, Telegram).

The dashboard only displays and pauses. It never trades.

---

## 2. Market analyser

The analyser does not predict. It watches what price is actually doing, using the higher timeframes for the wider picture.

### 2.1 What it reports

Every result gives: the market state, the direction (up, down or none), the type of trend (slow grind or strong push), when the state started, the evidence for it, and whether its data is ready, warming up or out of date. If the data is not ready, new trades are blocked but open trades are still managed. Every state change is recorded.

### 2.2 The five states

| State | Strategies allowed |
| --- | --- |
| Ranging | Range trade |
| Emerging trend | Slow grind, EMA pullback, Bollinger band bounce in the trend's direction only |
| Trend | Slow grind, EMA pullback, Bollinger band bounce in the trend's direction only |
| Possible reversal | Bollinger band bounce |
| Consolidation | None. Watch and wait for a break |

- **Ranging:** the Bollinger bands are flat and close together, and price bounces between the upper and lower band. The EMAs weave back and forth instead of staying stacked, and the 100 EMA is flat.
- **Emerging trend:** a direction is starting to form. Its main job is to stop bounces against the new direction early. Bounces with the new direction are still allowed.
- **Trend:** an established direction, either a slow grind or a strong push. Both are recognised from price action.
- **Possible reversal:** after a trend has been running and price has moved at least 30 pips since it started, a strong reversal candle appears, recognised by the shared rejection part with no extra size rule.
- **Consolidation** (this includes a trend running out of steam): narrow Bollinger bands, price between them touching neither band, small candles with green and red roughly the same size, no direction. Unlike ranging, price stays in the middle. No trading. When price breaks out, the analyser moves to emerging trend.

### 2.3 Direction rule (applies to every strategy)

- **Buy side:** price above the daily pivot and above the 5-minute 100 EMA.
- **Sell side:** price below the daily pivot and below the 5-minute 100 EMA.
- If they disagree, there is no clear direction.
- This applies to every strategy, including bounces in a possible reversal.

Functional test: on 6 November 2026 at 13:00 the signs of a reversal up appeared, but price was below the pivot and the 100 EMA, and carried on down through S2 to S3. Expected answer: no buy at 13:00, and the sell side stays allowed all the way down to S3.

### 2.4 News direction and trend days

- For each big release, read the forecast and previous figures from Finnhub, work out whether the expected result is good or bad for the pound or the dollar, and use that as the expected direction for the day.
- **Big releases at the same time** (owner, 7 November 2026): if their expected directions agree, that is the direction for that time. If they disagree, the **headline release decides**: a rate decision over everything else at that time, main payrolls over private payrolls, headline CPI over core CPI (the order is part of the news table, `config/news_table.toml`). If the headline release has no expected direction, there is no expected direction for that time; if several releases share the top place and do not agree, there is none either. Example: on Friday 6 November 2026 at 13:30, main payrolls (forecast above previous: good for the dollar) decide: GBPUSD down.
- On a trend day, when the trend and the expected news direction agree, expect price to continue through levels rather than reverse. The expected news direction takes precedence: a trade in that direction is kept open through rejections at levels.
- Example: on 6 November 2026 the 13:30 news produced a big red candle and the day traded down through S1, S2 and S3.

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

Price moves in a staircase: it pauses rather than bouncing back to the middle of the band.

1. A pause starts with two candles going in opposite directions, such as a red candle then a green one. No size test.
2. It counts as a pause once at least 3 candles in a row have failed to make a new low while staying below the 21 EMA.
3. The sell opens as soon as the live price breaks below the lowest point of the pause.
4. If a candle closes above the 21 EMA, the setup is cancelled. No time limit: a long pause becomes consolidation in the analyser.

### 3.2 EMA pullback (buy)

0. The trend must be established on the hourly chart: hourly 8, 13 and 20 EMAs in order and all rising, with the slope and gap minimums from 161's service as settings.
1. While a 5-minute candle is forming, the live price drops to the 5-minute 8 EMA. Price may cross the 8 and even the 13 EMA.
2. If a 5-minute candle closes below the 21 EMA, the setup is cancelled.
3. The entry price is 3 pips above the highest high (for a buy; 3 pips below the lowest low for a sell) of the five completed 5-minute candles immediately before the touch candle (AutoBot 161's rule).
4. The trade opens as soon as the live price reaches the entry price.
5. If it has not opened within 20 minutes, the setup expires.

EMAs: 8, 13 and 21 on the 5-minute chart. No fanning rule.

### 3.3 Bollinger band bounce (sell)

1. Price pierces a level or the Bollinger band. For a level, a candle that comes within 3 pips of it counts the same as a pierce (a setting). The Bollinger band needs a real pierce.
2. The reversal candle is the first red candle after the pierce, with no size rule. If none appears within 3 candles, the setup expires.
3. A later confirmation candle closes below the reversal candle's low, within 3 candles of it, or the setup expires. A wick below without a close does not count.
4. The sell opens as soon as the live price goes below the confirmation candle's low.
5. If price goes above the reversal candle's high at any point, the setup is cancelled.

The bot records, for each bounce, how big the reversal candle was compared with the piercing candle, for later review. It never filters on it.

Spread spikes are ignored: when IG's spread on a candle is abnormally wide (over 3 pips, a setting; this happens at the 22:00 rollover and at news), that candle's sell-price highs and lows cannot start a setup or cancel one. The candle is still stored as normal.

### 3.4 Range trade (sell at the upper band)

1. One candle pierces the upper Bollinger band.
2. The next candle is a red rejection candle.
3. The sell opens as soon as the live price, during the candle after that, goes below the rejection candle's low.
4. If price goes above the rejection candle's high first, the setup is cancelled.

Half the trade closes when price reaches the other band.

Spread spikes are ignored in the same way as for the bounce (3.3).

---

## 4. Trade management

One shared trade manager for every trade.

- **Stop loss:** a fixed 6 pips for every strategy, sent to IG. A switch in `.env` (`STOP_LOSS_PIPS`).
- **Take profit:** a fixed 100 pips sent to IG as a safety net. A switch in `.env` (`TAKE_PROFIT_PIPS`). Both are the bot's own rule, not an IG requirement.
- **Holding:** a trade runs until the analyser's state becomes consolidation, and is then closed (owner, 7 November 2026). There is no profit lock. The 6-pip stop and the 100-pip take profit at IG, the 20:30 close, the big-news close and the other exits in this section stay.
- **At a level:** the trade stays open while price is only wobbling. If price is rejected at the level against the trade, the trade closes at the same moment a bounce the other way would open: when the live price breaks past the confirmation candle. This never depends on a trade the other way being allowed.
- **Distance travelled** does not force a close on its own.
- **Reversal watch times:** 10:00, 11:00, 13:00, 14:00, 16:00 and 17:00 UK, from 20 minutes before to 20 minutes after. In those windows a rejection at any level counts; outside them, only at levels where several line up.
- **A change of market state** does not close a trade on its own; it is information for the trade manager.
- **Trend days:** see 2.4. The expected news direction takes precedence over rejections at levels.
- **Range trade:** closes 50% at the opposite band; the rest is managed like any other trade.
- **Decisions:** each open trade is always in one of: hold, watching a level, half close, close, forced close (news or 20:30), stopped by IG, take profit hit at IG.
- For every trade closed at a level, the bot records which levels lined up.

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
- Trades open at once: 1 per strategy; the bounce may also have 1 in the opposite direction. Most at once: 5.
- Total risk across all open trades and available funds are also checked.
- Trading hours (UK clock time): new trades from 06:00 to 20:30 (switches in `.env`, section 13). Any trade open at 20:30 is closed. Nothing held overnight. A trade opened just before 20:30 is simply closed at 20:30.
- **Per pair and in total (to be built with the safety rules):** every limit above will apply to each pair on its own, plus a total across all pairs switched on (for example the most trades open at once, and the total risk, across all pairs). Nothing is built for this yet.
- Big news: no new trades from 15 minutes before to 30 minutes after. Open trades closed 15 minutes before. Medium and small news ignored. Which releases count as big comes from AutoBot's own small, medium and big table (built: the owner's table from AutoBot 161, copied as data into `config/news_table.toml`, plus a GBP "Interest Rate" row for the Bank of England decision; `docs/NEWS.md`). News times and figures from Finnhub (built: `news/`, fetched a few times a day by the price service). If the news data is missing or out of date, alert Johnny rather than block trading indefinitely (built: a Telegram problem alert; trading is not blocked by it).

---

## 7. Broker safety

- **Force open** on every order, so an opposite trade opens a new position rather than closing an existing one.
- **Confirmed with IG:** a trade only counts as open, closed or half closed once IG confirms it. On a timeout, check with IG before trying again, so nothing is ever opened or closed twice.
- **Restart recovery:** on start-up, find the bot's own positions at IG using the saved deal references, take over managing them, and only then allow new trades. Never touch positions the bot did not open.
- **Stop check:** check IG's minimum stop distance at start-up and regularly in the background, never at the moment of a trade. If IG's minimum is ever above 6 pips, refuse new trades and alert Johnny. Never widen the stop quietly.
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
- **Trade alerts (built, not yet connected):** "trade opened" shows the pair, direction, size, strategy, market state, open price, stop loss and take profit; "trade closed" adds the close price, reason, profit or loss and win or loss. They are tested with pretend trades and **will be connected to the order sender when it is built** (`Alerts.trade_opened` and `Alerts.trade_closed`).

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
- **Switches in `.env`**, checked at start-up and documented in `docs/SETTINGS.md`: the pairs switched on (`PAIRS_ON`, GBPUSD only for now), the trading hours (`NEW_TRADES_FROM` 06:00, `NEW_TRADES_UNTIL` 20:30) each strategy on or off (`STRATEGY_SLOW_GRIND`, `STRATEGY_EMA_PULLBACK`, `STRATEGY_BOLLINGER_BOUNCE`, `STRATEGY_RANGE_TRADE`), and the stop loss and take profit sent to IG (`STOP_LOSS_PIPS` 6, `TAKE_PROFIT_PIPS` 100). Everything else stays in `config/settings.toml`.
- More detail: `docs/PAIRS.md`.
