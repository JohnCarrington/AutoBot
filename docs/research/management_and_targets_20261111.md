# Trade management and targets: nine changes replayed, 25 October to 11 November 2026

Wednesday 11 November 2026, morning UK. Read-only research: **nothing in the bot was changed**. There were no IG calls and no restart, and nothing was written outside `data/research/`.

## Summary

**Data and code.** Everything below comes from a replay of the bot's own code on its own IG candles, from the week's open on Sunday 25 October (21:00 UTC) to the last stored candle (ending Wednesday 11 November 06:25 UTC). Every result is shown twice: once with the stop counted first when one candle reached both a trade's stop and its target, and once with the target counted first.

- **The best combination is changes 1, 2 and 3 together:**
  - 1: the 12-pip stop;
  - 2: the range trade closed **in full** at the opposite band;
  - 3: the bounce closed **half** at the opposite band, with the rest left to run.
  
  It makes **+1,181.6 pips in 164 trades, against +1,128.4 in 170 for the current rules (+53.1)**, with the same result either way round. All of the gain is in the Bollinger bounce (+46.3) and the range trade (+6.7); the other four strategies trade exactly as now.
  
  It is better in the first two weeks (+14.3 and +50.2) and worse in the third (−11.4). **From Monday 9 November to now it makes +145.6 against +157.0.** It wins less on the two bounces that were already winning, and loses 6 more on one range trade.
  
  **A near tie:** with the bounce closed **in full** at the opposite band instead of half, the same combination makes +1,182.5 in 182 trades. That is 0.9 pips more, which is nothing, but it does worse from Monday 9 November (+130.7). The half close is shown trade by trade below because it was the better of the two on its own (+18.6 against +17.3) and gets the same result in 18 fewer trades.
- **New: closing the opposite trades when a Bollinger bounce opens** (added 08:30 UK; see its own section below). Three versions were run, alone and on top of 1 + 2 + 3:
  - **A, every opposite trade:** −26.7 alone, −33.8 on top of 1 + 2 + 3.
  - **B, only those in profit:** −34.5 and −34.5.
  - **C, only when the bounce opens at S2, S3, R2 or R3:** +22.7 and +22.7, so **1 + 2 + 3 + C makes +1,204.2 in 164 trades**.
  
  A and B close trades that would have gone on to their take profits, and lose 105–117 pips in the first week. They gain 33–54 in the second week and 46 (A) and 28 (B) in the third, the third week's gain all on Tuesday 10 November. C closed only 6 trades, on two days, and those 6 made 1.9 less than they would have. C's gain comes from one level reversal buy (+20.0) that could open on Monday 26 October because a close freed its place under the safety limits. Read it as one trade, not as an edge.
- **These three changes each help on their own:**
  - 1: the 12-pip stop, +28.3;
  - 3: the bounce closed half at the opposite band, +18.6 (closed in full there, +17.3);
  - 2: the range trade closed in full at the opposite band, +8.4.
  
  Each helps a little more when combined with the others. Adding any other change on top of the three makes the combination worse or leaves it unchanged (see the best combination section).
- **These hurt:**
  - 6, acting at the extremes: −445.9. Almost all of it is Friday 6 November, where it closed trend trades at S2 and S3 that went on to their 100-pip targets or ran to the 20:30 close. It is −19.2 without that day.
  - 7, no late entries: −880.0 as worded, where being beyond the previous day's extreme counts as within 10 pips of it. It is −576.4 when only 10 pips either side counts, and −111.1 for the S2/R2 part alone. It blocks the trend trades that made most of the period's money.
  - 9, no trend trade opening in a big-news window: −137.2.
  - 4, the level reversal's stop capped at 12 or at 15: −125.6 and −39.4. Capped at 20 it makes no difference here, because none of the trades it changes reached its stop.
  - The bounce closed in full at the middle band: −130.1 with the stop first, −101.7 with the target first. The range trade closed there: −9.6.
- **These change nothing in this period:**
  - **5, hold through the middle levels.** No trend trade is ever closed on a rejection under the current rules. The slow grind, EMA pullback and breakout (and the level reversal) are all in `NO_LEVEL_CLOSE` in `strategies/common.py`. Only the bounce and the range trade are closed on a rejection at a level, so there is nothing for this change to remove.
  - **8, hourly exhaustion.** Its three conditions were all met in 14 of the 298 hours, and no trend trade in that direction was open at any of those times.
- **The stop-and-target assumption hardly matters for these rules.**
  - No candle reached both a trade's stop and its take profit, in any run. An independent check over every candle of every trade agrees; the widest candle covered 66% of the distance between them.
  - The only runs where one candle reached both a stop and a target are those where the bounce closes at the middle band: 6 trades, all on Wednesday 4 November, which make 28.4 pips more with the target first. Every other result is identical both ways.
- **How far to trust it:**
  - The replay covers 2½ weeks and 170 trades. The best combination's +53 pips is less than 5% of the total and comes from about a dozen bounce and range trades.
  - Friday 6 November alone makes +676 of the current rules' +1,128.4 pips.
  - The earlier report (`strategies_by_market_20261110.md`) showed the replay and the live trades disagreeing on the same days.
  
  Read the differences as the direction each change pushes, not as a forecast.
- **The Monday after a big Friday:** 18 Fridays moved 80 pips or more in 2024–2026, 17 with a full Monday after them.
  - Monday went back the other way by a median of 31 pips (25% of Friday's move).
  - It went **half way back on 4 of the 17 Mondays and all the way back on none**.
  - It went further on, in Friday's direction, than it came back on 10 of them, and closed further on than Friday's close on 10.
  - The most recent, Monday 9 November, went 89% of the way back, the most of all.
- **PIA First signals cannot be read through the bot's dealing interface.** IG's REST and streaming API references have no signals, research or analyst endpoint. IG offers the signals (PIA First and Autochartist) only inside its web platform and mobile app.

## How it was done

- **Candles:** a read-only copy of the bot's own IG candle store, taken at 06:30 UTC today (`data/research/replay_stores/live_copy_20261111_0630/`), with IG's real buy and sell prices and nothing else.
- **Code:** a frozen copy of the committed code, `addf1b8`. The working tree also holds another session's uncommitted changes, which are live-only and were left untouched. The replay is the research mode (`research.long_replay`, the same engine, strategies, safety rules, paper order sender and trade manager as the bot's own replay), run week by week.
- **News rules:** Finnhub's past calendar, as in the earlier reports.
- **Switches:** today's `.env` switches (`STOP_LOSS_PIPS=6`, everything on), with `TRADING` off for the replay.
- **The changes:** each one is a patch in the research process only, applied to the bot's own functions while the replay runs. The scripts and every run's trades are in `data/research/replay/mgmt_20261111/`. The scripts are kept out of the repository, which commits only this file.
- **The research copy matches the bot's own code.** Unpatched, the bot's code gives 170 trades and +1,128.6. My version of the trade manager's step, with no change switched on, gives the same 170 trades with the same exits, at +1,128.4. The only difference is in 6 range-trade half closes: the bot's paper mode books a half close at the band's own unrounded value. Here every close at a band is priced at a real IG price: the band rounded to the 0.1 point against the trade, or the candle's open if it opened past the band.
- **Prices:**
  - Entries are at IG's buy price (buys) or sell price (sells) from the candles.
  - Stops and take profits fill at their level, or at the candle's open if it opened past.
  - The 20:30 and news closes are at the candle's open, and closes on a rejection at its trigger price, all on the side the trade closes on.
  - No spread is added: IG's own buy and sell prices already include it.
- **Trades still open at the last candle** (none in these runs) would be counted at that candle's close.

## What each change does in the replay

1. **The 12-pip stop:** `STOP_LOSS_PIPS=12` for the run. That is the stop of the Bollinger bounce and the range trade. The breakout's stop is already 12 (`breakout.stop_loss_pips` in `config/settings.toml`), so it is unchanged.
2. **The range trade at the opposite band:**
   - *close half* is the current rule (the other half runs to the stop, the take profit, a rejection or the scheduled close);
   - *close in full* closes all of it there;
   - *close in full at the middle band* closes all of it as soon as price reaches the middle band.
   
   The bands are the ones the trade manager already uses: as they stood at the last finished candle.
3. **The bounce outside a range:**
   - *as now* is the 100-pip take profit, the stop, the close on a confirmed rejection at a level, the close before big news and the 20:30 close;
   - the other three add a close at a band, exactly as for the range trade: in full at the opposite band, half there with the rest running as now, or in full at the middle band.
4. **The level reversal's stop capped:** the stop stays 6 pips beyond the furthest point, unless that is more than 12, 15 or 20 pips from the entry price. In that case it is 12, 15 or 20 pips from the entry (the chart price, so a buy's stop from its fill is the cap plus the spread).
5. **Hold through the middle levels:** nothing to change, as explained above.
6. **Act at the extremes:** an extreme is S2, S3, R2 or R3 within 5 pips of the previous day's high or low, or of a swing high or low. Swings are the bot's hourly turning levels. When either of these happens there, every open slow grind, EMA pullback and breakout trade the other way that is in profit is closed:
   - a confirmed rejection: the analyser's own rejection trigger, at its trigger price, from the candle after the trade's entry candle;
   - a Bollinger bounce opening: at the bounce's entry.
7. **No late entries:** no new slow grind, EMA pullback or breakout trade in either of these cases, judged on the sell (chart) price:
   - **past S2 or R2:** price has already been at or past S2 that day (for a sell) or R2 (for a buy). "That day" runs from 00:00 UK, the bot's daily candle, up to the entry.
   - **near the previous day's extreme:** the entry is within 10 pips of the previous day's low (for a sell) or high (for a buy).
   
   "Within 10 pips" was run two ways:
   - **as worded:** an entry already beyond the previous day's low or high also counts. For example, a sell 30 pips below Monday's low is blocked.
   - **only within 10 pips either side of it.**
   
   S2 is always below the previous day's low, so under the first reading the S2 part never blocks anything the previous-day part does not. The two parts were also run alone.
8. **Hourly exhaustion:** checked as each hourly candle finishes, on the bot's own hourly candles (sell price), with all three needed:
   - at least 3 of the last 4 hourly candles have a wick against the trade (the upper wick for a buy, the lower for a sell) at least as long as their body;
   - the last 2 hourly closes are at least half way back from the band to the middle band (hourly Bollinger 20, 2: below the midpoint of the upper and middle bands for a buy);
   - the hourly 100 and 200 EMAs have each moved less than 5 pips over the last 12 hourly candles.
   
   When they are met, slow grind, EMA pullback and breakout trades in profit are closed at the next price, the next candle's open.
9. **Big-news windows:** the slow grind, EMA pullback and breakout get the same no-new-trades window before and after big news as the other strategies. Closing before news is unchanged: they are still not closed before big news.

"Trend trades" here are the slow grind, the EMA pullback and the breakout.

## Every change: trades, wins, losses and pips

Wins and losses are trades above and below 0 pips; where the two ways differ, both are shown (stop first / target first). "Without Fri 6 Nov" leaves out the trades opened on Friday 6 November, the period's best day.

| Change | Trades | Won | Lost | Pips, stop first | Pips, target first | Trades with a stop-and-target candle | Against current (stop first / target first) | Without Fri 6 Nov (stop first) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Current rules** | 170 | 78 | 91 | **+1,128.4** | **+1,128.4** | 0 | +0.0 / +0.0 | +452.4 |
| 1. 12-pip stop (bounce and range trade; the breakout's is 12 already) | 164 | 80 | 83 | **+1,156.8** | **+1,156.8** | 0 | +28.3 / +28.3 | +480.8 |
| 2. Range trade: close in full at the opposite band | 170 | 79 | 90 | **+1,136.9** | **+1,136.9** | 0 | +8.4 / +8.4 | +460.9 |
| 2. Range trade: close in full at the middle band | 171 | 77 | 93 | **+1,118.8** | **+1,118.8** | 0 | -9.6 / -9.6 | +442.8 |
| 3. Bounce: close in full at the opposite band | 186 | 84 | 101 | **+1,145.8** | **+1,145.8** | 0 | +17.3 / +17.3 | +469.8 |
| 3. Bounce: close half at the opposite band, the rest runs | 170 | 79 | 90 | **+1,147.0** | **+1,147.0** | 0 | +18.6 / +18.6 | +471.0 |
| 3. Bounce: close in full at the middle band | 253 | 94 | 158 / 157 | **+998.4** | **+1,026.8** | 6 | -130.1 / -101.7 | +322.4 |
| 4. Level reversal stop capped at 12 | 176 | 76 | 99 | **+1,002.8** | **+1,002.8** | 0 | -125.6 / -125.6 | +362.2 |
| 4. Level reversal stop capped at 15 | 171 | 78 | 92 | **+1,089.0** | **+1,089.0** | 0 | -39.4 / -39.4 | +413.0 |
| 4. Level reversal stop capped at 20 | 170 | 78 | 91 | **+1,128.4** | **+1,128.4** | 0 | +0.0 / +0.0 | +452.4 |
| 5. Hold through the middle levels | same as current | | | +1,128.4 | +1,128.4 | 0 | 0 / 0 | +452.4 |
| 6. Act at the extremes | 173 | 81 | 91 | **+682.6** | **+682.6** | 0 | -445.9 / -445.9 | +433.2 |
| 7. No late entries (beyond the previous day's extreme counts as within) | 93 | 41 | 52 | **+248.4** | **+248.4** | 0 | -880.0 / -880.0 | +142.6 |
| 7. No late entries (only within 10 pips either side of it) | 113 | 52 | 60 | **+552.0** | **+552.0** | 0 | -576.4 / -576.4 | +313.6 |
| 7. No late entries: the S2/R2 part only | 132 | 64 | 67 | **+1,017.4** | **+1,017.4** | 0 | -111.1 / -111.1 | +439.6 |
| 7. No late entries: the previous day's part only | 93 | 41 | 52 | **+248.4** | **+248.4** | 0 | -880.0 / -880.0 | +142.6 |
| 8. Hourly exhaustion | 170 | 78 | 91 | **+1,128.4** | **+1,128.4** | 0 | +0.0 / +0.0 | +452.4 |
| 9. Slow grind, EMA pullback and breakout may not open in a big-news window | 167 | 75 | 91 | **+991.2** | **+991.2** | 0 | -137.2 / -137.2 | +393.6 |

## By week

The week of 8 November runs to Wednesday 06:25 UTC. There were no trades on Wednesday before then. Each cell is trades (won–lost) and pips.

**Stop first:**

| Change | w/c 25 Oct | w/c 1 Nov | w/c 8 Nov (to Wed 06:25) |
|---|---:|---:|---:|
| **Current rules** | 60 (30–29) +210.6 | 85 (39–46) +760.8 | 25 (9–16) +157.0 |
| 1. 12-pip stop (bounce and range trade; the breakout's is 12 already) | 59 (30–28) +204.6 | 82 (41–41) +791.6 | 23 (9–14) +160.5 |
| 2. Range trade: close in full at the opposite band | 60 (30–29) +214.6 | 85 (40–45) +765.3 | 25 (9–16) +157.0 |
| 2. Range trade: close in full at the middle band | 60 (30–29) +208.5 | 86 (37–49) +742.8 | 25 (10–15) +167.5 |
| 3. Bounce: close in full at the opposite band | 68 (33–34) +227.6 | 93 (42–51) +790.9 | 25 (9–16) +127.2 |
| 3. Bounce: close half at the opposite band, the rest runs | 60 (31–28) +223.2 | 85 (39–46) +781.8 | 25 (9–16) +142.1 |
| 3. Bounce: close in full at the middle band | 116 (41–74) +169.6 | 108 (45–63) +707.5 | 29 (8–21) +121.2 |
| 4. Level reversal stop capped at 12 | 63 (30–32) +152.4 | 88 (38–50) +718.9 | 25 (8–17) +131.5 |
| 4. Level reversal stop capped at 15 | 60 (31–28) +215.4 | 86 (39–47) +748.2 | 25 (8–17) +125.5 |
| 4. Level reversal stop capped at 20 | 60 (30–29) +210.6 | 85 (39–46) +760.8 | 25 (9–16) +157.0 |
| 5. Hold through the middle levels | 60 (30–29) +210.6 | 85 (39–46) +760.8 | 25 (9–16) +157.0 |
| 6. Act at the extremes | 61 (31–29) +191.4 | 87 (41–46) +334.1 | 25 (9–16) +157.0 |
| 7. No late entries (beyond the previous day's extreme counts as within) | 35 (17–18) -15.2 | 44 (17–27) +75.6 | 14 (7–7) +188.1 |
| 7. No late entries (only within 10 pips either side of it) | 48 (22–25) +57.8 | 49 (22–27) +298.2 | 16 (8–8) +196.1 |
| 7. No late entries: the S2/R2 part only | 57 (29–27) +223.8 | 57 (27–30) +621.5 | 18 (8–10) +172.1 |
| 7. No late entries: the previous day's part only | 35 (17–18) -15.2 | 44 (17–27) +75.6 | 14 (7–7) +188.1 |
| 8. Hourly exhaustion | 60 (30–29) +210.6 | 85 (39–46) +760.8 | 25 (9–16) +157.0 |
| 9. Slow grind, EMA pullback and breakout may not open in a big-news window | 60 (30–29) +210.6 | 82 (36–46) +682.5 | 25 (9–16) +98.1 |
| Combination 1 + 2 | 59 (30–28) +208.6 | 82 (42–40) +799.1 | 23 (9–14) +160.5 |
| Combination 1 + 3 | 59 (30–28) +221.0 | 82 (41–41) +803.6 | 23 (9–14) +145.6 |
| Combination 2 + 3 | 60 (31–28) +227.2 | 85 (40–45) +786.2 | 25 (9–16) +142.1 |
| Combination 1 + 2 + 3 | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 23 (9–14) +145.6 |

**Target first:**

| Change | w/c 25 Oct | w/c 1 Nov | w/c 8 Nov (to Wed 06:25) |
|---|---:|---:|---:|
| **Current rules** | 60 (30–29) +210.6 | 85 (39–46) +760.8 | 25 (9–16) +157.0 |
| 1. 12-pip stop (bounce and range trade; the breakout's is 12 already) | 59 (30–28) +204.6 | 82 (41–41) +791.6 | 23 (9–14) +160.5 |
| 2. Range trade: close in full at the opposite band | 60 (30–29) +214.6 | 85 (40–45) +765.3 | 25 (9–16) +157.0 |
| 2. Range trade: close in full at the middle band | 60 (30–29) +208.5 | 86 (37–49) +742.8 | 25 (10–15) +167.5 |
| 3. Bounce: close in full at the opposite band | 68 (33–34) +227.6 | 93 (42–51) +790.9 | 25 (9–16) +127.2 |
| 3. Bounce: close half at the opposite band, the rest runs | 60 (31–28) +223.2 | 85 (39–46) +781.8 | 25 (9–16) +142.1 |
| 3. Bounce: close in full at the middle band | 116 (41–74) +169.6 | 108 (45–62) +735.9 | 29 (8–21) +121.2 |
| 4. Level reversal stop capped at 12 | 63 (30–32) +152.4 | 88 (38–50) +718.9 | 25 (8–17) +131.5 |
| 4. Level reversal stop capped at 15 | 60 (31–28) +215.4 | 86 (39–47) +748.2 | 25 (8–17) +125.5 |
| 4. Level reversal stop capped at 20 | 60 (30–29) +210.6 | 85 (39–46) +760.8 | 25 (9–16) +157.0 |
| 5. Hold through the middle levels | 60 (30–29) +210.6 | 85 (39–46) +760.8 | 25 (9–16) +157.0 |
| 6. Act at the extremes | 61 (31–29) +191.4 | 87 (41–46) +334.1 | 25 (9–16) +157.0 |
| 7. No late entries (beyond the previous day's extreme counts as within) | 35 (17–18) -15.2 | 44 (17–27) +75.6 | 14 (7–7) +188.1 |
| 7. No late entries (only within 10 pips either side of it) | 48 (22–25) +57.8 | 49 (22–27) +298.2 | 16 (8–8) +196.1 |
| 7. No late entries: the S2/R2 part only | 57 (29–27) +223.8 | 57 (27–30) +621.5 | 18 (8–10) +172.1 |
| 7. No late entries: the previous day's part only | 35 (17–18) -15.2 | 44 (17–27) +75.6 | 14 (7–7) +188.1 |
| 8. Hourly exhaustion | 60 (30–29) +210.6 | 85 (39–46) +760.8 | 25 (9–16) +157.0 |
| 9. Slow grind, EMA pullback and breakout may not open in a big-news window | 60 (30–29) +210.6 | 82 (36–46) +682.5 | 25 (9–16) +98.1 |
| Combination 1 + 2 | 59 (30–28) +208.6 | 82 (42–40) +799.1 | 23 (9–14) +160.5 |
| Combination 1 + 3 | 59 (30–28) +221.0 | 82 (41–41) +803.6 | 23 (9–14) +145.6 |
| Combination 2 + 3 | 60 (31–28) +227.2 | 85 (40–45) +786.2 | 25 (9–16) +142.1 |
| Combination 1 + 2 + 3 | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 23 (9–14) +145.6 |

## Where one candle reached both the stop and the target

| Run | Entry (UK) | Trade | Stop first | Target first |
|---|---|---|---|---|
| 3. Bounce: close in full at the middle band | Wed 04 Nov 13:25 | Bollinger bounce sell | stop 13:30 -6.0 | the middle Bollinger band 13:30 +0.0 |
| 3. Bounce: close in full at the middle band | Wed 04 Nov 14:30 | Bollinger bounce sell | stop 14:30 -6.0 | the middle Bollinger band 14:30 -2.0 |
| 3. Bounce: close in full at the middle band | Wed 04 Nov 14:30 | Bollinger bounce sell | stop 14:30 -6.0 | the middle Bollinger band 14:30 -2.0 |
| 3. Bounce: close in full at the middle band | Wed 04 Nov 16:05 | Bollinger bounce buy | stop 16:05 -6.0 | the middle Bollinger band 16:05 -1.2 |
| 3. Bounce: close in full at the middle band | Wed 04 Nov 16:05 | Bollinger bounce buy | stop 16:05 -6.0 | the middle Bollinger band 16:05 -1.2 |
| 3. Bounce: close in full at the middle band | Wed 04 Nov 16:05 | Bollinger bounce buy | stop 16:05 -6.0 | the middle Bollinger band 16:05 -1.2 |

## The best combination

Combinations of the three changes that helped on their own, all eight of them:

| Change | Trades | Won | Lost | Pips, stop first | Pips, target first | Trades with a stop-and-target candle | Against current (stop first / target first) | Without Fri 6 Nov (stop first) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| none (current rules) | 170 | 78 | 91 | **+1,128.4** | **+1,128.4** | 0 | +0.0 / +0.0 | +452.4 |
| 1 | 164 | 80 | 83 | **+1,156.8** | **+1,156.8** | 0 | +28.3 / +28.3 | +480.8 |
| 2 (full) | 170 | 79 | 90 | **+1,136.9** | **+1,136.9** | 0 | +8.4 / +8.4 | +460.9 |
| 3 (half) | 170 | 79 | 90 | **+1,147.0** | **+1,147.0** | 0 | +18.6 / +18.6 | +471.0 |
| Combination 1 + 2 | 164 | 81 | 82 | **+1,168.2** | **+1,168.2** | 0 | +39.8 / +39.8 | +492.2 |
| Combination 1 + 3 | 164 | 80 | 83 | **+1,170.1** | **+1,170.1** | 0 | +41.6 / +41.6 | +494.1 |
| Combination 2 + 3 | 170 | 80 | 89 | **+1,155.5** | **+1,155.5** | 0 | +27.0 / +27.0 | +479.5 |
| Combination 1 + 2 + 3 | 164 | 81 | 82 | **+1,181.6** | **+1,181.6** | 0 | +53.1 / +53.1 | +505.6 |

The best combination with each other change added, to check that none of them helps once these three are in:

| Change | Trades | Won | Lost | Pips, stop first | Pips, target first | Trades with a stop-and-target candle | Against current (stop first / target first) | Without Fri 6 Nov (stop first) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Best combination: 1 + 2 (full) + 3 (half)** | 164 | 81 | 82 | **+1,181.6** | **+1,181.6** | 0 | +53.1 / +53.1 | +505.6 |
| + 6. act at the extremes | 167 | 84 | 82 | **+735.6** | **+735.6** | 0 | -392.8 / -392.8 | +486.4 |
| + 9. no trend trade in a big-news window | 161 | 78 | 82 | **+1,044.4** | **+1,044.4** | 0 | -84.1 / -84.1 | +446.6 |
| + 7. no late entries (the S2/R2 part) | 126 | 67 | 58 | **+1,070.4** | **+1,070.4** | 0 | -58.0 / -58.0 | +492.8 |
| + 4. level reversal stop capped at 15 | 165 | 81 | 83 | **+1,142.2** | **+1,142.2** | 0 | +13.7 / +13.7 | +466.2 |
| + 8. hourly exhaustion | 164 | 81 | 82 | **+1,181.6** | **+1,181.6** | 0 | +53.1 / +53.1 | +505.6 |
| with 3. the bounce closed in full (not half) at the opposite band | 182 | 88 | 93 | **+1,182.5** | **+1,182.5** | 0 | +54.0 / +54.0 | +506.5 |

"Against current" compares each row with the current rules. Compared with the best combination, each addition costs pips or changes nothing: −446.0 with change 6, −137.2 with 9, −111.2 with 7's S2/R2 part, −39.4 with 4's cap at 15, 0 with 8. Closing the bounce in full instead of half is +0.9.

### By strategy (stop first; the target first is the same)

| Strategy | Current | Best combination (1 + 2 + 3) | 1 alone | 2 (full) alone | 3 (half) alone |
|---|---:|---:|---:|---:|---:|
| slow grind | 23 (14–8) +285.8 | 23 (14–8) +285.8 | 23 (14–8) +285.8 | 23 (14–8) +285.8 | 23 (14–8) +285.8 |
| EMA pullback | 66 (26–40) +583.3 | 66 (26–40) +583.3 | 66 (26–40) +583.3 | 66 (26–40) +583.3 | 66 (26–40) +583.3 |
| breakout | 11 (6–5) +193.8 | 11 (6–5) +193.8 | 11 (6–5) +193.8 | 11 (6–5) +193.8 | 11 (6–5) +193.8 |
| Bollinger bounce | 38 (15–23) -10.3 | 33 (17–16) +36.0 | 33 (17–16) +22.7 | 38 (15–23) -10.3 | 38 (16–22) +8.3 |
| range trade | 10 (6–4) +5.0 | 9 (7–2) +11.7 | 9 (6–3) +0.2 | 10 (7–3) +13.4 | 10 (6–4) +5.0 |
| level reversal | 22 (11–11) +70.9 | 22 (11–11) +70.9 | 22 (11–11) +70.9 | 22 (11–11) +70.9 | 22 (11–11) +70.9 |

### Monday 9 November to now, trade by trade: the best combination against the current rules

The replay, with both rules run on the same candles. "Not taken" means the other rules' trades were still open, so the safety limits refused it (one trade per strategy, one more bounce the other way). The stop first and the target first give the same trades and results here.

| Entry (UK) | Strategy | Way | Current: exit | Current pips | Best combination: exit | Best pips | Difference |
|---|---|---|---|---:|---|---:|---:|
| Mon 09 Nov 05:25 | slow grind | buy | take profit 08:10 | +20.0 | take profit 08:10 | +20.0 | 0 |
| Mon 09 Nov 06:10 | level reversal | buy | take profit 08:15 | +20.0 | take profit 08:15 | +20.0 | 0 |
| Mon 09 Nov 07:55 | breakout | buy | take profit 21:00 | +50.0 | take profit 21:00 | +50.0 | 0 |
| Mon 09 Nov 08:25 | level reversal | buy | take profit 19:35 | +20.0 | take profit 19:35 | +20.0 | 0 |
| Mon 09 Nov 09:35 | slow grind | buy | stop 15:25 | -15.0 | stop 15:25 | -15.0 | 0 |
| Mon 09 Nov 10:30 | EMA pullback | buy | stop 12:00 | -12.0 | stop 12:00 | -12.0 | 0 |
| Mon 09 Nov 13:55 | range trade | buy | stop 14:40 | -6.0 | rejection at new_york_session_high 13421.2 14:45 | -7.7 | -1.7 |
| Mon 09 Nov 14:55 | range trade | buy | stop 15:00 | -6.0 | stop 15:20 | -12.0 | -6.0 |
| Mon 09 Nov 15:15 | range trade | buy | stop 15:20 | -6.0 | not taken | – | +6.0 |
| Mon 09 Nov 15:45 | slow grind | sell | stop 16:15 | -15.0 | stop 16:15 | -15.0 | 0 |
| Mon 09 Nov 19:55 | slow grind | buy | 20:30 close 20:30 | -2.1 | 20:30 close 20:30 | -2.1 | 0 |
| Mon 09 Nov 21:00 | EMA pullback | buy | stop 22:00 | -12.0 | stop 22:00 | -12.0 | 0 |
| Mon 09 Nov 21:00 | EMA pullback | buy | stop 22:00 | -12.0 | stop 22:00 | -12.0 | 0 |
| Tue 10 Nov 05:00 | EMA pullback | buy | stop 09:00 | -12.0 | stop 09:00 | -12.0 | 0 |
| Tue 10 Nov 06:10 | EMA pullback | buy | stop 09:00 | -12.0 | stop 09:00 | -12.0 | 0 |
| Tue 10 Nov 07:20 | EMA pullback | buy | stop 09:00 | -12.0 | stop 09:00 | -12.0 | 0 |
| Tue 10 Nov 07:55 | Bollinger bounce | sell | stop 08:00 | -6.0 | rejection at london_session_low 13446.6, turning_low 13447.2 08:30 | -6.8 | -0.8 |
| Tue 10 Nov 08:20 | Bollinger bounce | sell | stop 08:25 | -6.0 | not taken | – | +6.0 |
| Tue 10 Nov 08:45 | Bollinger bounce | sell | rejection at london_session_low 13422 10:40 | +21.8 | half at the band +3.2, then rejection at london_session_low 13422 10:40 | +12.5 | -9.3 |
| Tue 10 Nov 09:10 | breakout | sell | take profit 14:40 | +50.0 | take profit 14:40 | +50.0 | 0 |
| Tue 10 Nov 13:30 | slow grind | sell | take profit 16:30 | +100.0 | take profit 16:30 | +100.0 | 0 |
| Tue 10 Nov 14:05 | level reversal | sell | take profit 15:25 | +20.0 | take profit 15:25 | +20.0 | 0 |
| Tue 10 Nov 16:25 | level reversal | sell | stop 18:35 | -20.0 | stop 18:35 | -20.0 | 0 |
| Tue 10 Nov 17:00 | Bollinger bounce | buy | 20:30 close 20:30 | +21.3 | half at the band +10.1, then 20:30 close 20:30 | +15.7 | -5.6 |
| Tue 10 Nov 22:00 | EMA pullback | sell | stop 22:00 | -12.0 | stop 22:00 | -12.0 | 0 |
| **Total** | | | | **+157.0** | | **+145.6** | **-11.4** |

## A new change: close the opposite trades when a Bollinger bounce opens

Added Wednesday 11 November, 08:30 UK. Same replay as above: the same candle copy (06:30 UTC), the same frozen code (`addf1b8`), the same switches, prices, news calendar and period. Nothing in the bot was changed.

**The change.** When a Bollinger bounce actually opens, having passed all of the bot's own rules (its safety rules and the order sender), every open trade in the opposite direction is closed at that moment. A rejection alone never closes anything here. Three versions:

- **A:** every opposite trade is closed, whatever its strategy and whether it is in profit or not;
- **B:** only the opposite trades in profit are closed;
- **C:** every opposite trade is closed, but only when the bounce opens at S2, S3, R2 or R3. "At" means the bounce's rejection setup pierced, or came within 3 pips of, one of those levels: the setup's own list of levels, as the analyser records it.

**How it was replayed.**
- The closes happen straight after the order sender opens the bounce, in the same 5-minute candle.
- They are priced at the bounce's own entry. A bounce sell opens at the sell price, which is where a buy closes. A bounce buy fills at the buy price, which is where a sell closes. "In profit" (B) is judged at that same price.
- Each close goes through the paper order sender, as the trade manager's own closes do. That frees the trade's place under the safety limits, so a later trade the limits refused before can now open. The **knock-on** column below counts those other trades.
- The bot handles open trades before new ideas in each candle. So an opposite trade that reached its stop or target in the bounce's candle was already closed there, before the bounce opened.
- The change-6 patch above (act at the extremes) closed its trades without telling the paper order sender. Their places under the safety limits were not freed, which may have changed which later trades it took. That was not re-checked here.

### Trades, wins, losses and pips

Every run gives the same result whether the stop or the target is counted first; no candle reached both.

| Run | Trades | Won | Lost | Pips, stop first | Pips, target first | Stop-and-target candles | Trades closed by a bounce | Against current | Against 1 + 2 + 3 | Without Fri 6 Nov |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Current rules** | 170 | 78 | 91 | **+1,128.4** | **+1,128.4** | 0 | 0 | +0.0 | -53.1 | +452.4 |
| A. Bounce opens: close every opposite trade | 177 | 82 | 95 | **+1,101.8** | **+1,101.8** | 0 | 39 | -26.7 | -79.8 | +425.8 |
| B. Bounce opens: close the opposite trades in profit | 173 | 88 | 84 | **+1,094.0** | **+1,094.0** | 0 | 19 | -34.5 | -87.6 | +418.0 |
| C. Bounce opens at S2, S3, R2 or R3: close every opposite trade | 170 | 79 | 90 | **+1,151.2** | **+1,151.2** | 0 | 6 | +22.7 | -30.4 | +475.2 |
| **Best combination 1 + 2 + 3** | 164 | 81 | 82 | **+1,181.6** | **+1,181.6** | 0 | 0 | +53.1 | +0.0 | +505.6 |
| 1 + 2 + 3 + A (every opposite trade) | 171 | 85 | 86 | **+1,147.8** | **+1,147.8** | 0 | 38 | +19.3 | -33.8 | +471.8 |
| 1 + 2 + 3 + B (opposite trades in profit) | 167 | 91 | 75 | **+1,147.0** | **+1,147.0** | 0 | 19 | +18.6 | -34.5 | +471.0 |
| 1 + 2 + 3 + C (at S2, S3, R2 or R3) | 164 | 82 | 81 | **+1,204.2** | **+1,204.2** | 0 | 6 | +75.8 | +22.7 | +528.2 |

**Where the difference comes from:**

| Run | Against its base (current, or 1 + 2 + 3) | The closed trades, against what they would have made | Knock-on: other trades that changed |
|---|---:|---:|---:|
| A | −26.7 | −40.3 (39 trades) | +13.6 |
| B | −34.5 | −22.6 (19 trades) | −11.9 |
| C | +22.7 | −1.9 (6 trades) | +24.6 |
| 1 + 2 + 3 + A | −33.8 | −47.4 (38 trades) | +13.6 |
| 1 + 2 + 3 + B | −34.5 | −22.6 (19 trades) | −11.9 |
| 1 + 2 + 3 + C | +22.7 | −1.9 (6 trades) | +24.6 |

- **A and B cut winners short.** The trades they close would mostly have gone on to their take profits. The biggest costs are:
  - the breakout sell of Tue 27 Oct 07:00, closed at +0.6 instead of its +50 take profit;
  - three EMA pullbacks on Fri 30 Oct morning, closed instead of reaching their +30 take profits;
  - two EMA pullback sells on Mon 26 Oct, closed instead of reaching +30.
  
  B, closing only trades already in profit, closes exactly the trades that were working. It is the worst version.
- **C's gain is one knock-on trade.** At 14:10 on Mon 26 Oct, the bounce buy at S2 closed five sells: two EMA pullbacks at −4.8 and a level reversal at −1.0, all on their way to their stops; and the two older EMA pullbacks at +12.0, each 18 short of the +30 they reached the next morning. That freed the level reversal's place, and a level reversal buy opened in the same candle and reached its +20 take profit. Under the current rules the level reversal opened at 14:45 instead and made −4.6. Without that knock-on, C is −1.9.
- **C changes only two days:** Monday 26 October (five trades closed) and Wednesday 4 November (one).

### By week (the target first is the same)

Each cell is trades (won–lost) and pips.

| Run | w/c 25 Oct | w/c 1 Nov | w/c 8 Nov (to Wed 06:25) |
|---|---:|---:|---:|
| **Current rules** | 60 (30–29) +210.6 | 85 (39–46) +760.8 | 25 (9–16) +157.0 |
| A. Bounce opens: close every opposite trade | 65 (33–32) +105.0 | 87 (40–47) +794.1 | 25 (9–16) +202.7 |
| B. Bounce opens: close the opposite trades in profit | 63 (36–26) +93.6 | 85 (41–44) +815.2 | 25 (11–14) +185.1 |
| C. Bounce opens at S2, S3, R2 or R3: close every opposite trade | 60 (31–28) +225.4 | 85 (39–46) +768.8 | 25 (9–16) +157.0 |
| **Best combination 1 + 2 + 3** | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 23 (9–14) +145.6 |
| 1 + 2 + 3 + A (every opposite trade) | 64 (33–31) +112.1 | 84 (43–41) +844.4 | 23 (9–14) +191.3 |
| 1 + 2 + 3 + B (opposite trades in profit) | 62 (36–25) +107.9 | 82 (44–38) +865.4 | 23 (11–12) +173.7 |
| 1 + 2 + 3 + C (at S2, S3, R2 or R3) | 59 (31–27) +239.6 | 82 (42–40) +819.0 | 23 (9–14) +145.6 |

- **A and B lose in the first week** (−105.6 and −117.0 against the current rules) and **win in the second and third** (A +33.3 and +45.7; B +54.4 and +28.1).
- **All of the third week's gain is Tuesday 10 November** (see below). On that day, the 07:55 bounce sell closed the three losing EMA pullback buys and the 17:00 bounce buy closed the losing level reversal sell.
- **C is the only version better than its base in every week.** It is level in the third week and ahead in the first two: +14.8 and +8.0 against the current rules, +14.7 and +8.0 against 1 + 2 + 3. That still rests on the one knock-on trade of Monday 26 October.

### Every trade it closed, and what that trade would otherwise have made

"Would have made" is the same trade (same entry time, strategy and direction) in the run without this change: the current rules for A, B and C alone, and 1 + 2 + 3 for the combinations. "Not opened in that run" means the trade only exists because an earlier close freed its place. A close time without a date is on the entry day.

**A, alone:**

| Entry (UK) | Strategy | Way | Closed (UK) | By the bounce | Closed at | Otherwise (same trade, without the change) | Would have made | Difference |
|---|---|---|---|---|---:|---|---:|---:|
| Mon 26 Oct 08:25 | slow grind | sell | Mon 26 Oct 09:05 | buy | +3.5 | take profit 13:55 | +20.0 | -16.5 |
| Mon 26 Oct 08:35 | EMA pullback | sell | Mon 26 Oct 09:05 | buy | -2.7 | take profit Tue 27 Oct 07:05 | +30.0 | -32.7 |
| Mon 26 Oct 08:35 | EMA pullback | sell | Mon 26 Oct 09:05 | buy | -2.7 | take profit Tue 27 Oct 07:05 | +30.0 | -32.7 |
| Mon 26 Oct 13:55 | EMA pullback | sell | Mon 26 Oct 14:10 | buy at S2 | -4.8 | stop 14:30 | -12.0 | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback | sell | Mon 26 Oct 14:10 | buy at S2 | -4.8 | stop 14:30 | -12.0 | +7.2 |
| Mon 26 Oct 13:55 | level reversal | sell | Mon 26 Oct 14:10 | buy at S2 | -1.0 | stop 14:45 | -12.7 | +11.7 |
| Tue 27 Oct 05:45 | slow grind | sell | Tue 27 Oct 07:20 | buy | +6.1 | take profit 09:30 | +20.0 | -13.9 |
| Tue 27 Oct 07:00 | breakout | sell | Tue 27 Oct 07:20 | buy | +0.6 | take profit Wed 28 Oct 07:10 | +50.0 | -49.4 |
| Tue 27 Oct 16:05 | slow grind | sell | Tue 27 Oct 16:40 | buy | -0.6 | 20:30 close 20:30 | +0.0 | -0.6 |
| Tue 27 Oct 16:15 | EMA pullback | sell | Tue 27 Oct 16:40 | buy | -5.3 | stop 17:00 | -12.0 | +6.7 |
| Wed 28 Oct 04:45 | slow grind | sell | Wed 28 Oct 07:25 | buy | +14.5 | the profit lock: back to 10 pips up after 15 up 07:30 | +10.0 | +4.5 |
| Wed 28 Oct 10:20 | slow grind | sell | Wed 28 Oct 10:35 | buy | -7.4 | stop 13:30 | -15.0 | +7.6 |
| Wed 28 Oct 10:45 | EMA pullback | sell | Wed 28 Oct 11:15 | buy | -5.8 | stop 11:35 | -12.0 | +6.2 |
| Wed 28 Oct 10:45 | EMA pullback | sell | Wed 28 Oct 11:15 | buy | -5.8 | stop 11:35 | -12.0 | +6.2 |
| Wed 28 Oct 15:30 | slow grind | buy | Wed 28 Oct 15:50 | sell | -8.8 | the profit lock: back to 10 pips up after 15 up 17:00 | +10.0 | -18.8 |
| Wed 28 Oct 16:15 | level reversal | buy | Wed 28 Oct 17:05 | sell | +3.5 | before big news 17:45 | -1.7 | +5.2 |
| Wed 28 Oct 16:50 | slow grind | buy | Wed 28 Oct 17:05 | sell | -1.1 | not opened in that run | – | – |
| Thu 29 Oct 22:05 | EMA pullback | buy | Fri 30 Oct 07:45 | sell | +16.8 | 20:30 close Fri 30 Oct 20:30 | +10.9 | +5.9 |
| Fri 30 Oct 00:40 | EMA pullback | buy | Fri 30 Oct 07:45 | sell | +11.5 | take profit 09:15 | +30.0 | -18.5 |
| Fri 30 Oct 07:10 | EMA pullback | buy | Fri 30 Oct 07:45 | sell | +0.7 | take profit 09:45 | +30.0 | -29.3 |
| Fri 30 Oct 07:25 | level reversal | buy | Fri 30 Oct 07:45 | sell | -9.9 | take profit 10:05 | +20.0 | -29.9 |
| Fri 30 Oct 08:15 | level reversal | buy | Fri 30 Oct 10:40 | sell | +11.1 | not opened in that run | – | – |
| Fri 30 Oct 08:15 | slow grind | buy | Fri 30 Oct 10:40 | sell | +13.1 | take profit 11:05 | +20.0 | -6.9 |
| Fri 30 Oct 09:15 | EMA pullback | buy | Fri 30 Oct 10:40 | sell | +4.5 | stop 12:40 | -12.0 | +16.5 |
| Fri 30 Oct 09:15 | EMA pullback | buy | Fri 30 Oct 10:40 | sell | +4.5 | stop 12:40 | -12.0 | +16.5 |
| Fri 30 Oct 11:10 | EMA pullback | buy | Fri 30 Oct 11:20 | sell | -4.9 | stop 12:00 | -12.0 | +7.1 |
| Fri 30 Oct 13:25 | level reversal | sell | Fri 30 Oct 15:25 | buy | +0.7 | 20:30 close 20:30 | -4.1 | +4.8 |
| Fri 30 Oct 16:15 | level reversal | buy | Fri 30 Oct 16:25 | sell | -8.4 | not opened in that run | – | – |
| Mon 02 Nov 08:30 | EMA pullback | buy | Mon 02 Nov 09:25 | sell | +15.2 | stop 10:25 | -12.0 | +27.2 |
| Mon 02 Nov 08:30 | EMA pullback | buy | Mon 02 Nov 09:25 | sell | +15.2 | stop 10:25 | -12.0 | +27.2 |
| Tue 03 Nov 08:05 | EMA pullback | buy | Tue 03 Nov 08:20 | sell | -7.8 | stop 08:30 | -12.0 | +4.2 |
| Wed 04 Nov 08:30 | slow grind | buy | Wed 04 Nov 10:40 | sell | -6.7 | stop 11:05 | -15.0 | +8.3 |
| Wed 04 Nov 15:35 | slow grind | sell | Wed 04 Nov 15:40 | buy | -7.5 | stop 17:25 | -15.0 | +7.5 |
| Wed 04 Nov 16:10 | slow grind | sell | Wed 04 Nov 17:10 | buy at R2 | -5.5 | not opened in that run | – | – |
| Thu 05 Nov 08:00 | slow grind | sell | Thu 05 Nov 08:15 | buy | -10.9 | the profit lock: back to 10 pips up after 15 up 12:00 | +9.7 | -20.6 |
| Tue 10 Nov 05:00 | EMA pullback | buy | Tue 10 Nov 07:55 | sell | -0.4 | stop 09:00 | -12.0 | +11.6 |
| Tue 10 Nov 06:10 | EMA pullback | buy | Tue 10 Nov 07:55 | sell | -2.3 | stop 09:00 | -12.0 | +9.7 |
| Tue 10 Nov 07:20 | EMA pullback | buy | Tue 10 Nov 07:55 | sell | -5.7 | stop 09:00 | -12.0 | +6.3 |
| Tue 10 Nov 16:25 | level reversal | sell | Tue 10 Nov 17:00 | buy | -1.9 | stop 18:35 | -20.0 | +18.1 |
| **Total (39)** | | | | | **-1.2** | | **+39.1** | **-40.3** |

**B, alone:**

| Entry (UK) | Strategy | Way | Closed (UK) | By the bounce | Closed at | Otherwise (same trade, without the change) | Would have made | Difference |
|---|---|---|---|---|---:|---|---:|---:|
| Mon 26 Oct 08:25 | slow grind | sell | Mon 26 Oct 09:05 | buy | +3.5 | take profit 13:55 | +20.0 | -16.5 |
| Mon 26 Oct 08:35 | EMA pullback | sell | Mon 26 Oct 14:10 | buy at S2 | +12.0 | take profit Tue 27 Oct 07:05 | +30.0 | -18.0 |
| Mon 26 Oct 08:35 | EMA pullback | sell | Mon 26 Oct 14:10 | buy at S2 | +12.0 | take profit Tue 27 Oct 07:05 | +30.0 | -18.0 |
| Mon 26 Oct 14:45 | level reversal | buy | Mon 26 Oct 17:50 | sell | +7.4 | 20:30 close 20:30 | -4.6 | +12.0 |
| Tue 27 Oct 05:45 | slow grind | sell | Tue 27 Oct 07:20 | buy | +6.1 | take profit 09:30 | +20.0 | -13.9 |
| Tue 27 Oct 07:00 | breakout | sell | Tue 27 Oct 07:20 | buy | +0.6 | take profit Wed 28 Oct 07:10 | +50.0 | -49.4 |
| Wed 28 Oct 04:45 | slow grind | sell | Wed 28 Oct 07:25 | buy | +14.5 | the profit lock: back to 10 pips up after 15 up 07:30 | +10.0 | +4.5 |
| Wed 28 Oct 16:15 | level reversal | buy | Wed 28 Oct 17:05 | sell | +3.5 | before big news 17:45 | -1.7 | +5.2 |
| Thu 29 Oct 22:05 | EMA pullback | buy | Fri 30 Oct 07:45 | sell | +16.8 | 20:30 close Fri 30 Oct 20:30 | +10.9 | +5.9 |
| Fri 30 Oct 00:40 | EMA pullback | buy | Fri 30 Oct 07:45 | sell | +11.5 | take profit 09:15 | +30.0 | -18.5 |
| Fri 30 Oct 07:10 | EMA pullback | buy | Fri 30 Oct 07:45 | sell | +0.7 | take profit 09:45 | +30.0 | -29.3 |
| Fri 30 Oct 08:15 | slow grind | buy | Fri 30 Oct 10:40 | sell | +13.1 | take profit 11:05 | +20.0 | -6.9 |
| Fri 30 Oct 09:15 | EMA pullback | buy | Fri 30 Oct 10:40 | sell | +4.5 | stop 12:40 | -12.0 | +16.5 |
| Fri 30 Oct 09:15 | EMA pullback | buy | Fri 30 Oct 10:40 | sell | +4.5 | stop 12:40 | -12.0 | +16.5 |
| Fri 30 Oct 13:25 | level reversal | sell | Fri 30 Oct 15:25 | buy | +0.7 | 20:30 close 20:30 | -4.1 | +4.8 |
| Mon 02 Nov 08:30 | EMA pullback | buy | Mon 02 Nov 09:25 | sell | +15.2 | stop 10:25 | -12.0 | +27.2 |
| Mon 02 Nov 08:30 | EMA pullback | buy | Mon 02 Nov 09:25 | sell | +15.2 | stop 10:25 | -12.0 | +27.2 |
| Tue 10 Nov 05:00 | EMA pullback | buy | Tue 10 Nov 08:45 | sell | +3.0 | stop 09:00 | -12.0 | +15.0 |
| Tue 10 Nov 06:10 | EMA pullback | buy | Tue 10 Nov 08:45 | sell | +1.1 | stop 09:00 | -12.0 | +13.1 |
| **Total (19)** | | | | | **+145.9** | | **+168.5** | **-22.6** |

**C, alone:**

| Entry (UK) | Strategy | Way | Closed (UK) | By the bounce | Closed at | Otherwise (same trade, without the change) | Would have made | Difference |
|---|---|---|---|---|---:|---|---:|---:|
| Mon 26 Oct 08:35 | EMA pullback | sell | Mon 26 Oct 14:10 | buy at S2 | +12.0 | take profit Tue 27 Oct 07:05 | +30.0 | -18.0 |
| Mon 26 Oct 08:35 | EMA pullback | sell | Mon 26 Oct 14:10 | buy at S2 | +12.0 | take profit Tue 27 Oct 07:05 | +30.0 | -18.0 |
| Mon 26 Oct 13:55 | EMA pullback | sell | Mon 26 Oct 14:10 | buy at S2 | -4.8 | stop 14:30 | -12.0 | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback | sell | Mon 26 Oct 14:10 | buy at S2 | -4.8 | stop 14:30 | -12.0 | +7.2 |
| Mon 26 Oct 13:55 | level reversal | sell | Mon 26 Oct 14:10 | buy at S2 | -1.0 | stop 14:45 | -12.7 | +11.7 |
| Wed 04 Nov 15:35 | slow grind | sell | Wed 04 Nov 17:10 | buy at R2 | -7.0 | stop 17:25 | -15.0 | +8.0 |
| **Total (6)** | | | | | **+6.4** | | **+8.3** | **-1.9** |

**1 + 2 + 3 + A:**

| Entry (UK) | Strategy | Way | Closed (UK) | By the bounce | Closed at | Otherwise (same trade, without the change) | Would have made | Difference |
|---|---|---|---|---|---:|---|---:|---:|
| Mon 26 Oct 08:25 | slow grind | sell | Mon 26 Oct 09:05 | buy | +3.5 | take profit 13:55 | +20.0 | -16.5 |
| Mon 26 Oct 08:35 | EMA pullback | sell | Mon 26 Oct 09:05 | buy | -2.7 | take profit Tue 27 Oct 07:05 | +30.0 | -32.7 |
| Mon 26 Oct 08:35 | EMA pullback | sell | Mon 26 Oct 09:05 | buy | -2.7 | take profit Tue 27 Oct 07:05 | +30.0 | -32.7 |
| Mon 26 Oct 13:55 | EMA pullback | sell | Mon 26 Oct 14:10 | buy at S2 | -4.8 | stop 14:30 | -12.0 | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback | sell | Mon 26 Oct 14:10 | buy at S2 | -4.8 | stop 14:30 | -12.0 | +7.2 |
| Mon 26 Oct 13:55 | level reversal | sell | Mon 26 Oct 14:10 | buy at S2 | -1.0 | stop 14:45 | -12.7 | +11.7 |
| Tue 27 Oct 05:45 | slow grind | sell | Tue 27 Oct 07:20 | buy | +6.1 | take profit 09:30 | +20.0 | -13.9 |
| Tue 27 Oct 07:00 | breakout | sell | Tue 27 Oct 07:20 | buy | +0.6 | take profit Wed 28 Oct 07:10 | +50.0 | -49.4 |
| Tue 27 Oct 16:05 | slow grind | sell | Tue 27 Oct 16:40 | buy | -0.6 | 20:30 close 20:30 | +0.0 | -0.6 |
| Tue 27 Oct 16:15 | EMA pullback | sell | Tue 27 Oct 16:40 | buy | -5.3 | stop 17:00 | -12.0 | +6.7 |
| Wed 28 Oct 04:45 | slow grind | sell | Wed 28 Oct 07:25 | buy | +14.5 | the profit lock: back to 10 pips up after 15 up 07:30 | +10.0 | +4.5 |
| Wed 28 Oct 10:20 | slow grind | sell | Wed 28 Oct 10:35 | buy | -7.4 | stop 13:30 | -15.0 | +7.6 |
| Wed 28 Oct 10:45 | EMA pullback | sell | Wed 28 Oct 11:15 | buy | -5.8 | stop 11:35 | -12.0 | +6.2 |
| Wed 28 Oct 10:45 | EMA pullback | sell | Wed 28 Oct 11:15 | buy | -5.8 | stop 11:35 | -12.0 | +6.2 |
| Wed 28 Oct 15:30 | slow grind | buy | Wed 28 Oct 15:50 | sell | -8.8 | the profit lock: back to 10 pips up after 15 up 17:00 | +10.0 | -18.8 |
| Wed 28 Oct 16:15 | level reversal | buy | Wed 28 Oct 17:05 | sell | +3.5 | before big news 17:45 | -1.7 | +5.2 |
| Wed 28 Oct 16:50 | slow grind | buy | Wed 28 Oct 17:05 | sell | -1.1 | not opened in that run | – | – |
| Thu 29 Oct 22:05 | EMA pullback | buy | Fri 30 Oct 07:45 | sell | +16.8 | 20:30 close Fri 30 Oct 20:30 | +10.9 | +5.9 |
| Fri 30 Oct 00:40 | EMA pullback | buy | Fri 30 Oct 07:45 | sell | +11.5 | take profit 09:15 | +30.0 | -18.5 |
| Fri 30 Oct 07:10 | EMA pullback | buy | Fri 30 Oct 07:45 | sell | +0.7 | take profit 09:45 | +30.0 | -29.3 |
| Fri 30 Oct 07:25 | level reversal | buy | Fri 30 Oct 07:45 | sell | -9.9 | take profit 10:05 | +20.0 | -29.9 |
| Fri 30 Oct 08:15 | level reversal | buy | Fri 30 Oct 10:40 | sell | +11.1 | not opened in that run | – | – |
| Fri 30 Oct 08:15 | slow grind | buy | Fri 30 Oct 10:40 | sell | +13.1 | take profit 11:05 | +20.0 | -6.9 |
| Fri 30 Oct 09:15 | EMA pullback | buy | Fri 30 Oct 10:40 | sell | +4.5 | stop 12:40 | -12.0 | +16.5 |
| Fri 30 Oct 09:15 | EMA pullback | buy | Fri 30 Oct 10:40 | sell | +4.5 | stop 12:40 | -12.0 | +16.5 |
| Fri 30 Oct 13:25 | level reversal | sell | Fri 30 Oct 15:25 | buy | +0.7 | 20:30 close 20:30 | -4.1 | +4.8 |
| Fri 30 Oct 16:15 | level reversal | buy | Fri 30 Oct 16:25 | sell | -8.4 | not opened in that run | – | – |
| Mon 02 Nov 08:30 | EMA pullback | buy | Mon 02 Nov 09:25 | sell | +15.2 | stop 10:25 | -12.0 | +27.2 |
| Mon 02 Nov 08:30 | EMA pullback | buy | Mon 02 Nov 09:25 | sell | +15.2 | stop 10:25 | -12.0 | +27.2 |
| Tue 03 Nov 08:05 | EMA pullback | buy | Tue 03 Nov 08:20 | sell | -7.8 | stop 08:30 | -12.0 | +4.2 |
| Wed 04 Nov 08:30 | slow grind | buy | Wed 04 Nov 10:40 | sell | -6.7 | stop 11:05 | -15.0 | +8.3 |
| Wed 04 Nov 15:35 | slow grind | sell | Wed 04 Nov 15:40 | buy | -7.5 | stop 17:25 | -15.0 | +7.5 |
| Wed 04 Nov 16:10 | slow grind | sell | Wed 04 Nov 17:10 | buy at R2 | -5.5 | not opened in that run | – | – |
| Thu 05 Nov 08:00 | slow grind | sell | Thu 05 Nov 08:15 | buy | -10.9 | the profit lock: back to 10 pips up after 15 up 12:00 | +9.7 | -20.6 |
| Tue 10 Nov 05:00 | EMA pullback | buy | Tue 10 Nov 07:55 | sell | -0.4 | stop 09:00 | -12.0 | +11.6 |
| Tue 10 Nov 06:10 | EMA pullback | buy | Tue 10 Nov 07:55 | sell | -2.3 | stop 09:00 | -12.0 | +9.7 |
| Tue 10 Nov 07:20 | EMA pullback | buy | Tue 10 Nov 07:55 | sell | -5.7 | stop 09:00 | -12.0 | +6.3 |
| Tue 10 Nov 16:25 | level reversal | sell | Tue 10 Nov 17:00 | buy | -1.9 | stop 18:35 | -20.0 | +18.1 |
| **Total (38)** | | | | | **+3.7** | | **+51.1** | **-47.4** |

**1 + 2 + 3 + B:**

| Entry (UK) | Strategy | Way | Closed (UK) | By the bounce | Closed at | Otherwise (same trade, without the change) | Would have made | Difference |
|---|---|---|---|---|---:|---|---:|---:|
| Mon 26 Oct 08:25 | slow grind | sell | Mon 26 Oct 09:05 | buy | +3.5 | take profit 13:55 | +20.0 | -16.5 |
| Mon 26 Oct 08:35 | EMA pullback | sell | Mon 26 Oct 14:10 | buy at S2 | +12.0 | take profit Tue 27 Oct 07:05 | +30.0 | -18.0 |
| Mon 26 Oct 08:35 | EMA pullback | sell | Mon 26 Oct 14:10 | buy at S2 | +12.0 | take profit Tue 27 Oct 07:05 | +30.0 | -18.0 |
| Mon 26 Oct 14:45 | level reversal | buy | Mon 26 Oct 17:50 | sell | +7.4 | 20:30 close 20:30 | -4.6 | +12.0 |
| Tue 27 Oct 05:45 | slow grind | sell | Tue 27 Oct 07:20 | buy | +6.1 | take profit 09:30 | +20.0 | -13.9 |
| Tue 27 Oct 07:00 | breakout | sell | Tue 27 Oct 07:20 | buy | +0.6 | take profit Wed 28 Oct 07:10 | +50.0 | -49.4 |
| Wed 28 Oct 04:45 | slow grind | sell | Wed 28 Oct 07:25 | buy | +14.5 | the profit lock: back to 10 pips up after 15 up 07:30 | +10.0 | +4.5 |
| Wed 28 Oct 16:15 | level reversal | buy | Wed 28 Oct 17:05 | sell | +3.5 | before big news 17:45 | -1.7 | +5.2 |
| Thu 29 Oct 22:05 | EMA pullback | buy | Fri 30 Oct 07:45 | sell | +16.8 | 20:30 close Fri 30 Oct 20:30 | +10.9 | +5.9 |
| Fri 30 Oct 00:40 | EMA pullback | buy | Fri 30 Oct 07:45 | sell | +11.5 | take profit 09:15 | +30.0 | -18.5 |
| Fri 30 Oct 07:10 | EMA pullback | buy | Fri 30 Oct 07:45 | sell | +0.7 | take profit 09:45 | +30.0 | -29.3 |
| Fri 30 Oct 08:15 | slow grind | buy | Fri 30 Oct 10:40 | sell | +13.1 | take profit 11:05 | +20.0 | -6.9 |
| Fri 30 Oct 09:15 | EMA pullback | buy | Fri 30 Oct 10:40 | sell | +4.5 | stop 12:40 | -12.0 | +16.5 |
| Fri 30 Oct 09:15 | EMA pullback | buy | Fri 30 Oct 10:40 | sell | +4.5 | stop 12:40 | -12.0 | +16.5 |
| Fri 30 Oct 13:25 | level reversal | sell | Fri 30 Oct 15:25 | buy | +0.7 | 20:30 close 20:30 | -4.1 | +4.8 |
| Mon 02 Nov 08:30 | EMA pullback | buy | Mon 02 Nov 09:25 | sell | +15.2 | stop 10:25 | -12.0 | +27.2 |
| Mon 02 Nov 08:30 | EMA pullback | buy | Mon 02 Nov 09:25 | sell | +15.2 | stop 10:25 | -12.0 | +27.2 |
| Tue 10 Nov 05:00 | EMA pullback | buy | Tue 10 Nov 08:45 | sell | +3.0 | stop 09:00 | -12.0 | +15.0 |
| Tue 10 Nov 06:10 | EMA pullback | buy | Tue 10 Nov 08:45 | sell | +1.1 | stop 09:00 | -12.0 | +13.1 |
| **Total (19)** | | | | | **+145.9** | | **+168.5** | **-22.6** |

**1 + 2 + 3 + C:**

| Entry (UK) | Strategy | Way | Closed (UK) | By the bounce | Closed at | Otherwise (same trade, without the change) | Would have made | Difference |
|---|---|---|---|---|---:|---|---:|---:|
| Mon 26 Oct 08:35 | EMA pullback | sell | Mon 26 Oct 14:10 | buy at S2 | +12.0 | take profit Tue 27 Oct 07:05 | +30.0 | -18.0 |
| Mon 26 Oct 08:35 | EMA pullback | sell | Mon 26 Oct 14:10 | buy at S2 | +12.0 | take profit Tue 27 Oct 07:05 | +30.0 | -18.0 |
| Mon 26 Oct 13:55 | EMA pullback | sell | Mon 26 Oct 14:10 | buy at S2 | -4.8 | stop 14:30 | -12.0 | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback | sell | Mon 26 Oct 14:10 | buy at S2 | -4.8 | stop 14:30 | -12.0 | +7.2 |
| Mon 26 Oct 13:55 | level reversal | sell | Mon 26 Oct 14:10 | buy at S2 | -1.0 | stop 14:45 | -12.7 | +11.7 |
| Wed 04 Nov 15:35 | slow grind | sell | Wed 04 Nov 17:10 | buy at R2 | -7.0 | stop 17:25 | -15.0 | +8.0 |
| **Total (6)** | | | | | **+6.4** | | **+8.3** | **-1.9** |


### Tuesday 10 November, trade by trade

The replay, stop first (the target first is the same). "Not taken" means the safety limits refused the trade in that run.

**Alone, against the current rules:**

| Entry (UK) | Strategy | Way | Current rules | A. Bounce opens: close every opposite trade | B. Bounce opens: close the opposite trades in profit | C. Bounce opens at S2, S3, R2 or R3: close every opposite trade |
|---|---|---|---|---|---|---|
| Tue 10 Nov 05:00 | EMA pullback | buy | stop 09:00 -12.0 | closed by the bounce 07:55 -0.4 | closed by the bounce 08:45 +3.0 | stop 09:00 -12.0 |
| Tue 10 Nov 06:10 | EMA pullback | buy | stop 09:00 -12.0 | closed by the bounce 07:55 -2.3 | closed by the bounce 08:45 +1.1 | stop 09:00 -12.0 |
| Tue 10 Nov 07:20 | EMA pullback | buy | stop 09:00 -12.0 | closed by the bounce 07:55 -5.7 | stop 09:00 -12.0 | stop 09:00 -12.0 |
| Tue 10 Nov 07:55 | Bollinger bounce | sell | stop 08:00 -6.0 | stop 08:00 -6.0 | stop 08:00 -6.0 | stop 08:00 -6.0 |
| Tue 10 Nov 08:20 | Bollinger bounce | sell | stop 08:25 -6.0 | stop 08:25 -6.0 | stop 08:25 -6.0 | stop 08:25 -6.0 |
| Tue 10 Nov 08:45 | Bollinger bounce | sell | rejection at london_session_low 13422 10:40 +21.8 | rejection at london_session_low 13422 10:40 +21.8 | rejection at london_session_low 13422 10:40 +21.8 | rejection at london_session_low 13422 10:40 +21.8 |
| Tue 10 Nov 09:10 | breakout | sell | take profit 14:40 +50.0 | take profit 14:40 +50.0 | take profit 14:40 +50.0 | take profit 14:40 +50.0 |
| Tue 10 Nov 13:30 | slow grind | sell | take profit 16:30 +100.0 | take profit 16:30 +100.0 | take profit 16:30 +100.0 | take profit 16:30 +100.0 |
| Tue 10 Nov 14:05 | level reversal | sell | take profit 15:25 +20.0 | take profit 15:25 +20.0 | take profit 15:25 +20.0 | take profit 15:25 +20.0 |
| Tue 10 Nov 16:25 | level reversal | sell | stop 18:35 -20.0 | closed by the bounce 17:00 -1.9 | stop 18:35 -20.0 | stop 18:35 -20.0 |
| Tue 10 Nov 17:00 | Bollinger bounce | buy | 20:30 close 20:30 +21.3 | 20:30 close 20:30 +21.3 | 20:30 close 20:30 +21.3 | 20:30 close 20:30 +21.3 |
| Tue 10 Nov 22:00 | EMA pullback | sell | stop 22:00 -12.0 | stop 22:00 -12.0 | stop 22:00 -12.0 | stop 22:00 -12.0 |
| **Total** | | | **+133.1** | **+178.8** | **+161.2** | **+133.1** |

**Added to the best combination (1 + 2 + 3):**

| Entry (UK) | Strategy | Way | Best combination 1 + 2 + 3 | 1 + 2 + 3 + A (every opposite trade) | 1 + 2 + 3 + B (opposite trades in profit) | 1 + 2 + 3 + C (at S2, S3, R2 or R3) |
|---|---|---|---|---|---|---|
| Tue 10 Nov 05:00 | EMA pullback | buy | stop 09:00 -12.0 | closed by the bounce 07:55 -0.4 | closed by the bounce 08:45 +3.0 | stop 09:00 -12.0 |
| Tue 10 Nov 06:10 | EMA pullback | buy | stop 09:00 -12.0 | closed by the bounce 07:55 -2.3 | closed by the bounce 08:45 +1.1 | stop 09:00 -12.0 |
| Tue 10 Nov 07:20 | EMA pullback | buy | stop 09:00 -12.0 | closed by the bounce 07:55 -5.7 | stop 09:00 -12.0 | stop 09:00 -12.0 |
| Tue 10 Nov 07:55 | Bollinger bounce | sell | rejection at london_session_low 13446.6, turning_low 13447.2 08:30 -6.8 | rejection at london_session_low 13446.6, turning_low 13447.2 08:30 -6.8 | rejection at london_session_low 13446.6, turning_low 13447.2 08:30 -6.8 | rejection at london_session_low 13446.6, turning_low 13447.2 08:30 -6.8 |
| Tue 10 Nov 08:45 | Bollinger bounce | sell | half at the band +3.2, then rejection at london_session_low 13422 10:40 +12.5 | half at the band +3.2, then rejection at london_session_low 13422 10:40 +12.5 | half at the band +3.2, then rejection at london_session_low 13422 10:40 +12.5 | half at the band +3.2, then rejection at london_session_low 13422 10:40 +12.5 |
| Tue 10 Nov 09:10 | breakout | sell | take profit 14:40 +50.0 | take profit 14:40 +50.0 | take profit 14:40 +50.0 | take profit 14:40 +50.0 |
| Tue 10 Nov 13:30 | slow grind | sell | take profit 16:30 +100.0 | take profit 16:30 +100.0 | take profit 16:30 +100.0 | take profit 16:30 +100.0 |
| Tue 10 Nov 14:05 | level reversal | sell | take profit 15:25 +20.0 | take profit 15:25 +20.0 | take profit 15:25 +20.0 | take profit 15:25 +20.0 |
| Tue 10 Nov 16:25 | level reversal | sell | stop 18:35 -20.0 | closed by the bounce 17:00 -1.9 | stop 18:35 -20.0 | stop 18:35 -20.0 |
| Tue 10 Nov 17:00 | Bollinger bounce | buy | half at the band +10.1, then 20:30 close 20:30 +15.7 | half at the band +10.1, then 20:30 close 20:30 +15.7 | half at the band +10.1, then 20:30 close 20:30 +15.7 | half at the band +10.1, then 20:30 close 20:30 +15.7 |
| Tue 10 Nov 22:00 | EMA pullback | sell | stop 22:00 -12.0 | stop 22:00 -12.0 | stop 22:00 -12.0 | stop 22:00 -12.0 |
| **Total** | | | **+123.4** | **+169.1** | **+151.5** | **+123.4** |

- **The 07:55 bounce sell** was itself stopped for −6.0 within 5 minutes, but its opening closed the three EMA pullback buys (05:00, 06:10, 07:20) at −0.4, −2.3 and −5.7. They would have gone on to their stops at 09:00 for −12.0 each. A saves +27.6 there.
- **B waits for a buy in profit.** At 07:55 none were. At 08:45 the next bounce sell closed the 05:00 and 06:10 buys at +3.0 and +1.1. The 07:20 buy was still losing, stayed open and was stopped (−12.0).
- **The 17:00 bounce buy** closed the 16:25 level reversal sell at −1.9 under A. It would have been stopped at 18:35 for −20.0. Under B it was losing, so it stayed open; under C the bounce was not at S2, S3, R2 or R3.
- **C closes nothing on Tuesday.** None of the day's bounces opened at S2, S3, R2 or R3.
- The day: current rules +133.1, A +178.8, B +161.2, C +133.1. Best combination +123.4; with A +169.1, with B +151.5, with C +123.4.
- **The cost on other days:** A closes winners too. On Tuesday 27 October and Friday 30 October it closed trades that went on to +50 and +30 take profits.


## The Monday after a Friday that moved 80 pips or more (2024 to 2026)

**How it was measured:**
- **The Friday's move:** the bot's own measure, the same one safety rule 9 uses (`analyser.day_direction.friday_move_pips`): the Friday's daily candle from 00:00 UK, sell price, close less open.
- **The Monday's daily candle:** also from 00:00 UK. Sunday evening's trading is in Sunday's candle and not counted.
- **How far Monday went back:** from Friday's close to Monday's furthest point the other way (Monday's low after an up Friday, its high after a down Friday). 0 means Monday never traded back beyond Friday's close.
- **Candles:** AutoBot 161's IG candles to 24 October 2026, then the bot's own.
- **Fridays missing from the data:** 6, 13 and 20 March 2026 (no candles from 1 to 22 March 2026) and 15 May 2026. Monday 8 June 2026 has only 133 of its 288 five-minute candles, so it is shown but left out of the counts.

| Friday | Friday move (pips) | Monday | Monday furthest back the other way | Share of Friday | Monday close, back from Friday close (+ back, − further on) | Monday furthest on in Friday direction | Half back | All back |
|---|---:|---|---:|---:|---:|---:|:-:|:-:|
| Fri 02 Feb 2024 | -117.2 | Mon 05 Feb 2024 | 0.8 | 1% | -95.1 | 110.3 | no | no |
| Fri 12 Apr 2024 | -106.6 | Mon 15 Apr 2024 | 50.1 | 47% | -0.4 | 12.7 | no | no |
| Fri 16 Aug 2024 | +88.5 | Mon 19 Aug 2024 | 2.1 | 2% | -46.9 | 55.3 | no | no |
| Fri 23 Aug 2024 | +116.4 | Mon 26 Aug 2024 | 29.2 | 25% | +21.3 | 13.3 | no | no |
| Fri 10 Jan 2025 | -93.6 | Mon 13 Jan 2025 | 45.4 | 49% | +27.1 | 105.2 | no | no |
| Fri 24 Jan 2025 | +122.0 | Mon 27 Jan 2025 | 50.2 | 41% | +25.1 | 47.2 | no | no |
| Fri 04 Apr 2025 | -213.5 | Mon 07 Apr 2025 | 42.2 | 20% | -156.4 | 183.6 | no | no |
| Fri 11 Apr 2025 | +97.0 | Mon 14 Apr 2025 | 11.9 | 12% | -95.1 | 115.8 | no | no |
| Fri 23 May 2025 | +110.5 | Mon 26 May 2025 | 3.3 | 3% | -30.3 | 58.5 | no | no |
| Fri 11 Jul 2025 | -99.6 | Mon 14 Jul 2025 | 19.3 | 19% | -58.6 | 64.0 | no | no |
| Fri 22 Aug 2025 | +103.0 | Mon 25 Aug 2025 | 74.1 | 72% | +64.5 | 6.9 | yes | no |
| Fri 19 Sep 2025 | -84.5 | Mon 22 Sep 2025 | 53.7 | 64% | +47.2 | 13.8 | yes | no |
| Fri 23 Jan 2026 | +135.6 | Mon 26 Jan 2026 | 0.0 | 0% | -39.9 | 78.2 | no | no |
| Fri 30 Jan 2026 | -123.6 | Mon 02 Feb 2026 | 31.0 | 25% | -11.7 | 61.5 | no | no |
| Fri 06 Feb 2026 | +88.8 | Mon 09 Feb 2026 | 23.2 | 26% | -72.6 | 90.4 | no | no |
| Fri 08 May 2026 | +85.8 | Mon 11 May 2026 | 54.2 | 63% | +26.3 | 19.1 | yes | no |
| Fri 05 Jun 2026 | -86.4 | Mon 08 Jun 2026 (incomplete: 133 of 288 candles) | 29.9 | 35% | +2.9 | 8.7 | no | no |
| Fri 06 Nov 2026 | -107.6 | Mon 09 Nov 2026 | 96.3 | 89% | +93.2 | 0.0 | yes | no |

**Of the 17 complete Mondays:**
- **Half way back or more: 4.** All the way back: **none**.
- **The median Monday went back 31 pips**, 25% of Friday's move (the mean is 33%).
- **10 went further on**, in Friday's direction, than they ever came back, and 10 closed further on than Friday's close. Monday closed at least half way back on only 3 (25 August 2025, 22 September 2025 and 9 November 2026).
- **The Monday that came back the most** is the most recent: Monday 9 November, 96.3 pips (89%) of Friday 6 November's −107.6.

Safety rule 9 refuses reversal trades against "the direction that reclaims" a big Friday on the Monday. Over these Mondays, price more often carried on in Friday's direction than reclaimed it, though 17 Mondays is a small sample.

## Can the bot read IG's PIA First signals?

**No, not through the dealing interface the bot uses, with or without logging in again.** The answer below comes from IG's public pages only; nothing was logged into or called.

- **IG's REST trading API reference** (https://labs.ig.com/rest-trading-api-reference.html) lists these groups of endpoints:
  - account (accounts, preferences, activity and transaction history);
  - dealing (confirms, positions, working orders);
  - markets (categories, markets, prices);
  - watchlists;
  - client sentiment;
  - login (session);
  - indicative costs and charges;
  - general (application settings).
  
  None returns signals, analyst recommendations, research or news. The words "signal", "PIA" and "Autochartist" do not appear. The nearest thing, client sentiment, is the share of IG clients long and short, not an analyst's view.
- **IG's streaming API reference** (https://labs.ig.com/streaming-api-reference.html) has subscriptions for prices, the account, trade confirmations and position updates, and chart candles and ticks. It has nothing for signals.
- **How IG says signals are delivered** (https://www.ig.com/uk/trading-platforms/trading-signals):
  - "Our signals come directly from two third-party providers, Autochartist and PIA-First";
  - "You can get signals on your mobile devices with the IG Trading app, and on desktop with the IG Trading platform";
  - "Select 'signals' from the left-hand menu to view them."
  
  The forex signals page (https://www.ig.com/en/trading-platforms/trading-signals/forex-signals) says the fundamental signals are "provided by Signal Centre (Pia-First)", viewed "through the IG trading platform, available on desktop or the mobile app".
- **IG's API pages** (https://www.ig.com/en/trading-platforms/trading-apis) describe live prices, historical prices, account data and trade execution, and say nothing about signals.

**Not checked:**
- IG's current API agreement could not be found, and its API FAQ page did not load (an error at IG's end).
- The web platform must get the signals from somewhere inside IG, but that interface is not documented for clients. Using it would mean copying an unsupported, undocumented interface, which may breach IG's terms.
- PIA First (Signal Centre) or Autochartist may sell their own feed directly, which would be a separate account with them.
