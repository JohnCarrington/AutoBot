# Wednesday 18 November 2026: the trend day the slow grind didn't trade

**Investigation only.** Nothing was changed, switched or restarted. This is the new AutoBot server (`/opt/autobot`), not AutoBot 161. All times are UK time, which in November is GMT, the same as the logs. Prices are sell prices unless I say otherwise. "IG's buy price" is the price a sell is closed at.

## Short answer

- **The slow grind found 12 sell setups** between Tue 22:00 and Wed 12:00. All 12 would have been in profit at some point between 06:00 and 09:00 if they had been open and held.
- **None of them opened.** The strategy checks refused every one before trading hours or the safety rules came into it. The reasons were:
  - the analyser wasn't in a **trend** state (the slow grind only trades a trend);
  - the **hourly read** was "rally" until 06:00, then "ranging" until 08:00;
  - for four setups, **TREND_STILL_GOING**.
- **The analyser only called "trend down" at 08:35.** By then the hourly read had said "sell-off" since 08:00, so both checks would have let a sell through. But the slow grind's own pattern didn't give a sell between 08:35 and 12:00. Price fell almost every candle with no 2-candle pause, and the one pause that formed (09:10 to 09:25) never broke its low.
- **So Johnny's trend-day signal would not have turned on that day.** There was no slow grind trade at all, so none could be in profit between 06:00 and 09:00.
- **The "emerging trend up" at 07:30 is not what blocked the slow grind.** The slow grind needs "trend". An emerging trend blocks it whichever way it points. The "up" label did block the **EMA pullback** sell at 08:05.

## Which code and switches I replayed

- **The code that was running.** The price service was started at 20:46 on Tue 17 Nov (log: `20:46:38 ... Trading ON: 0 open trade(s) taken over`). It wasn't restarted until 13:35 on Wed 18 Nov (`13:35:20 ... Received SIGTERM: stopping`). At 20:46 the checkout was main **cc70dc5** (the trail-fix merge, 20:36). The checkout moved twice before 13:35: c41ddbd (STP tab) at 23:23, and dd9d36d (STP improvements) at 06:14. Neither change touched the strategies, analyser, trading, orders, safety, prices or levels folders (`git diff --stat cc70dc5 dd9d36d` on those folders is empty). In any case, the running service had already loaded cc70dc5.
- **The switches.** These come from the live `.env` as it stood then: the backup `env.2026-11-18_132302` (last changed 17 Nov 20:36). All 9 strategies were on, with HOURLY_READ=on, TREND_STILL_GOING=on, trading hours 06:00 to 20:30, and none of the later analyser-control or Stage 4 switches. TRADING was off in the replay, so nothing could be sent.
- **How I ran it.** `replay18.py` was run in a clean worktree at cc70dc5. It replays the week from Sunday's open through the live analyser (`StateTracker`) and the live strategy runner (`StrategyRunner`). The hourly read and the hourly trend are rebuilt at every candle, as the live service does.
- **The replay matches the live records exactly:**
  - **Analyser state changes from Tue 22:00 to Wed 12:00:** 27 in `logs/prices.log.3` and 27 in the replay, with the same times and the same wording.
  - **Slow grind setups in `data/records/GBPUSD/decisions.jsonl`:** 17 live and 17 in the replay, with the same times, directions, prices and refusal text.

## 1. Every slow grind sell setup, and whether it was in profit between 06:00 and 09:00

This is the slow grind's own signal: a pause of 2 candles without a new low, closing under the 21 EMA, then a break below the pause's low. The table ignores trading hours and every check. The profit check uses IG's buy price from the stored candles (`profit_check.txt`, `profit18.py`). There are two views:
- **A, held with no exits:** the best and worst between 06:00 and 09:00, and where it stood at 09:00 (the 08:55 candle's buy close).
- **B, with the slow grind's own exits from the live settings:** stop 15, take profit 20, and the profit lock (once 15 pips up, it closes if price comes back to 10 up). Within a candle, the stop is checked first.

| Setup (UK) | Sell entry | A: no exits, 06:00–09:00 | B: own exits |
|---|---|---|---|
| Tue 22:20 | 13198.8 | best +46.7, at 09:00 +44.0 | **stopped at 22:25, −15**: IG's overnight spread was about 17 pips (buy 13215–13218), so the 15-pip stop is hit at once |
| Tue 22:45 | 13201.6 | best +49.5, at 09:00 +46.8 | **stopped at 22:50, −15**: same spread |
| Wed 00:45 | 13199.8 | best +47.7, at 09:00 +45.0 | open at 06:00; take profit +20 at 07:00 |
| Wed 03:10 | 13195.6 | best +43.5, at 09:00 +40.8 | open at 06:00; take profit +20 at 07:05 |
| Wed 04:05 | 13195.5 | best +43.4, at 09:00 +40.7 | open at 06:00; take profit +20 at 07:05 |
| Wed 04:30 | 13192.2 | best +40.1, at 09:00 +37.4 | open at 06:00; best +18.8; profit lock +10 at 07:15 |
| Wed 05:50 | 13190.6 | best +38.5, at 09:00 +35.8 | open at 06:00; best +17.2; profit lock +10 at 07:15 |
| Wed 06:25 | 13188.9 | best +36.8, at 09:00 +34.1 | best +15.5; profit lock +10 at 07:15 |
| Wed 06:40 | 13187.6 | best +35.5, at 09:00 +32.8 | take profit +20 at 08:05 |
| Wed 07:00 | 13189.1 | best +37.0, at 09:00 +34.3 | best +15.7; profit lock +10 at 07:15 |
| Wed 07:25 | 13177.2 | best +25.1, at 09:00 +22.4 | take profit +20 at 08:50 |
| Wed 08:05 | 13171.0 | best +18.9, at 09:00 +16.2 | still open at 09:00 (+16.2); take profit +20 at 09:00 |

All 12 were in profit on IG's buy price at some time between 06:00 and 09:00, except the two Tuesday-night ones once their own stop is applied. These are per-setup checks, not results: none of these trades existed.

There were no more slow grind sells before 12:00. The slow grind's other setups in the window were buys (02:00 and 02:15, then 09:55, 10:10 and 10:45 against the trend). They are in `replay_output.txt`.

## 2. What stopped each sell from opening live

The live decision records (`decisions.jsonl`, `kind: idea`, `strategy: slow grind`, all with `"allowed": false, "already_sent_live": false`):

| Setup | `blocked_by` (quoted) |
|---|---|
| Tue 22:20, 13198.8 | `the analyser's state is emerging trend, which does not allow slow grind; the hourly chart is in a rally: slow grind only buys` |
| Tue 22:45, 13201.6 | `the analyser's state is emerging trend, which does not allow slow grind; the hourly chart is in a rally: slow grind only buys` |
| Wed 00:45, 13199.8 | `the analyser's state is emerging trend, which does not allow slow grind; the hourly chart is in a rally: slow grind only buys` |
| Wed 03:10, 13195.6 | `the analyser's state is emerging trend, which does not allow slow grind; the hourly chart is in a rally: slow grind only buys` |
| Wed 04:05, 13195.5 | `the hourly chart is in a rally: slow grind only buys; TREND_STILL_GOING is on and the trend is not still going: no new low at least 5 pips below the previous low in the last 12 five-minute candles (the most: 0.9 pips below the swing low 13196.7 of 03:40, at 04:00)` |
| Wed 04:30, 13192.2 | `the hourly chart is in a rally: slow grind only buys; TREND_STILL_GOING is on and the trend is not still going: no new low at least 5 pips below the previous low in the last 12 five-minute candles (the most: 4.6 pips below the swing low 13196.7 of 03:40, at 04:10)` |
| Wed 05:50, 13190.6 | `the analyser's state is consolidation, which does not allow slow grind; the hourly chart is in a rally: slow grind only buys` |
| Wed 06:25, 13188.9 | `the analyser's state is consolidation, which does not allow slow grind; the hourly chart is ranging (13188.7 to 13227.9): slow grind waits for an hourly close at least 3 pips beyond the hourly range` |
| Wed 06:40, 13187.6 | `the analyser's state is consolidation, which does not allow slow grind; the hourly chart is ranging (13188.7 to 13227.9): slow grind waits for an hourly close at least 3 pips beyond the hourly range; TREND_STILL_GOING is on and the trend is not still going: ...` |
| Wed 07:00, 13189.1 | `the analyser's state is consolidation, which does not allow slow grind; the hourly chart is ranging (13186.8 to 13219.6): slow grind waits for an hourly close at least 3 pips beyond the hourly range; TREND_STILL_GOING is on and the trend is not still going: ...` |
| Wed 07:25, 13177.2 | `the analyser's state is emerging trend, which does not allow slow grind; the hourly chart is ranging (13186.8 to 13219.6): slow grind waits for an hourly close at least 3 pips beyond the hourly range` |
| Wed 08:05, 13171 | `the analyser's state is emerging trend, which does not allow slow grind` |

**What each kind of block means:**
- **The analyser's state (10 of 12).** The slow grind only opens in a **trend**. Emerging trend, consolidation and ranging all refuse it. At 04:05 and 04:30 the state was "trend down (slow grind)", from 03:10 to 04:35, but other checks refused those two.
- **The hourly read (11 of 12).** The 17:00 hourly candle on Tuesday closed at 13224, a new high, so the read was **"rally"** until 06:00. A rally only lets the slow grind buy. Twelve hourly candles later, with no new break, it became **"ranging"** from 06:00 to 08:00. While ranging, the trend strategies wait for an hourly close at least 3 pips outside the hourly range. The 07:00 hourly candle closed at 13172.8, 14 pips under the range low of 13186.8. That turned the read to **"sell-off"** at 08:00. From then on the hourly read allowed sells.
- **TREND_STILL_GOING (4 of 12).** This needs a new low at least 5 pips below the previous swing low within the last 12 candles.
- **The 08:05 setup was refused by the analyser's state alone.** The hourly read (sell-off) and TREND_STILL_GOING both passed. The analyser had said "emerging trend (up)" since 07:15. The 08:05 candle itself turned it to emerging down, but the check uses the state after the previous candle.

**What did not stop them:**
- **Trading hours.** The slow grind has its own hours: any time except 20:30 to midnight, the rollover from 21:55 to 22:15, and the first 15 minutes of the week (`strategies/common.py` `may_open`). The 06:00 to 20:30 window is for other strategies. So 00:45 to 08:05 were all inside its hours. Tue 22:20 and 22:45 fall in the 20:30 to midnight block and would have been refused for that too. But hours are a safety-rule check, and the safety rules only see ideas the strategy checks allowed, so they never got that far.
- **"At most 1 open".** No slow grind trade was open, and at most one trade of any kind was open (the Asian range breakout sell from 07:30), well under the limit of 5. It never came into it.
- **Big news.** UK CPI was at 07:00. The Asian range breakout was refused for it from 07:05 to 07:25 (`in a big-news window: Core Inflation Rate MoM, Inflation Rate YoY`). The slow grind is allowed in big-news windows.

## The analyser's state, every 5-minute candle from 06:00 to 09:30

"Seen while it formed" is the state a strategy is checked against for that candle (the state after the previous candle). From the replay, which matches the live log line for line (`analyser_per_candle_0600_0930.csv`).

| 5m candle (UK) | State the strategies saw while it formed | State after it closed | Sell close | Hourly read |
|---|---|---|---|---|
| 06:00 | emerging trend down | emerging trend down | 13189.4 | ranging 13188.7–13227.9 |
| 06:05 | emerging trend down | emerging trend down | 13190.8 | ranging 13188.7–13227.9 |
| 06:10 | emerging trend down | consolidation | 13191.7 | ranging 13188.7–13227.9 |
| 06:15 | consolidation | consolidation | 13190.3 | ranging 13188.7–13227.9 |
| 06:20 | consolidation | consolidation | 13189.9 | ranging 13188.7–13227.9 |
| 06:25 | consolidation | consolidation | 13188.1 | ranging 13188.7–13227.9 |
| 06:30 | consolidation | consolidation | 13188.8 | ranging 13188.7–13227.9 |
| 06:35 | consolidation | consolidation | 13187.8 | ranging 13188.7–13227.9 |
| 06:40 | consolidation | consolidation | 13190.4 | ranging 13188.7–13227.9 |
| 06:45 | consolidation | consolidation | 13189.4 | ranging 13188.7–13227.9 |
| 06:50 | consolidation | consolidation | 13190.6 | ranging 13188.7–13227.9 |
| 06:55 | consolidation | consolidation | 13190.4 | ranging 13188.7–13227.9 |
| 07:00 | consolidation | emerging trend down | 13176.7 | ranging 13186.8–13219.6 |
| 07:05 | emerging trend down | emerging trend down | 13174.9 | ranging 13186.8–13219.6 |
| 07:10 | emerging trend down | emerging trend down | 13177.1 | ranging 13186.8–13219.6 |
| 07:15 | emerging trend down | emerging trend up | 13181.7 | ranging 13186.8–13219.6 |
| 07:20 | emerging trend up | emerging trend up | 13179 | ranging 13186.8–13219.6 |
| 07:25 | emerging trend up | emerging trend up | 13179.2 | ranging 13186.8–13219.6 |
| 07:30 | emerging trend up | emerging trend up | 13176.8 | ranging 13186.8–13219.6 |
| 07:35 | emerging trend up | emerging trend up | 13173.8 | ranging 13186.8–13219.6 |
| 07:40 | emerging trend up | emerging trend up | 13172.3 | ranging 13186.8–13219.6 |
| 07:45 | emerging trend up | emerging trend up | 13174.2 | ranging 13186.8–13219.6 |
| 07:50 | emerging trend up | emerging trend up | 13171.8 | ranging 13186.8–13219.6 |
| 07:55 | emerging trend up | emerging trend up | 13172.8 | ranging 13186.8–13219.6 |
| 08:00 | emerging trend up | emerging trend up | 13172.6 | sell-off (07:00 hourly close 13172.8) |
| 08:05 | emerging trend up | emerging trend down | 13171.4 | sell-off (07:00 hourly close 13172.8) |
| 08:10 | emerging trend down | emerging trend down | 13169.6 | sell-off (07:00 hourly close 13172.8) |
| 08:15 | emerging trend down | emerging trend down | 13161.7 | sell-off (07:00 hourly close 13172.8) |
| 08:20 | emerging trend down | emerging trend down | 13162.8 | sell-off (07:00 hourly close 13172.8) |
| 08:25 | emerging trend down | emerging trend down | 13160.6 | sell-off (07:00 hourly close 13172.8) |
| 08:30 | emerging trend down | emerging trend down | 13162.9 | sell-off (07:00 hourly close 13172.8) |
| 08:35 | emerging trend down | trend down (slow grind) | 13160.4 | sell-off (07:00 hourly close 13172.8) |
| 08:40 | trend down (slow grind) | trend down (slow grind) | 13163.7 | sell-off (07:00 hourly close 13172.8) |
| 08:45 | trend down (slow grind) | trend down (slow grind) | 13157.7 | sell-off (07:00 hourly close 13172.8) |
| 08:50 | trend down (slow grind) | trend down (slow grind) | 13153.2 | sell-off (07:00 hourly close 13172.8) |
| 08:55 | trend down (slow grind) | trend down (slow grind) | 13153.3 | sell-off (07:00 hourly close 13172.8) |
| 09:00 | trend down (slow grind) | trend down (slow grind) | 13150.9 | sell-off (08:00 hourly close 13153.3) |
| 09:05 | trend down (slow grind) | trend down (slow grind) | 13153.8 | sell-off (08:00 hourly close 13153.3) |
| 09:10 | trend down (slow grind) | trend down (slow grind) | 13153.6 | sell-off (08:00 hourly close 13153.3) |
| 09:15 | trend down (slow grind) | trend down (slow grind) | 13151.1 | sell-off (08:00 hourly close 13153.3) |
| 09:20 | trend down (slow grind) | trend down (slow grind) | 13155.3 | sell-off (08:00 hourly close 13153.3) |
| 09:25 | trend down (slow grind) | trend down (slow grind) | 13161.4 | sell-off (08:00 hourly close 13153.3) |
| 09:30 | trend down (slow grind) | trend down (slow grind) | 13163.4 | sell-off (08:00 hourly close 13153.3) |

**The analyser's own reasons at each change** (live log, `logs/prices.log.3`):
```
06:10  consolidation (none): the emerging down trend was cancelled: 2 closes in a row back inside the Bollinger bands after the breakout (last 13191.7)
07:00  emerging trend (down): broke out of the consolidation: close 13176.7 below the lower band 13183.1
07:15  emerging trend (up): rejected at a level against the emerging down trend: closed 13181.7 above the reversal high 13177.2; trigger at above 13182.7
08:05  emerging trend (down): rejected at a level against the emerging up trend: closed 13171.4 below the reversal low 13172.2; trigger at below 13163.9
08:35  trend (down, slow grind): the rejection became a trend: a bounce failed under the 21 EMA and middle band, then a new low 13159.0 on the lower band 13158.8; EMAs 7/13/21 stacked down for 40 candles, close 13160.4 below them and the 100 EMA 13188.8; band sloping -1.1 pips/candle
```
After that, no change until the 13:35 restart.

### Why the analyser said "emerging trend up" at 07:30 while price was falling

- **What happened.** The 07:10 candle fell to 13171.9 and then closed near its high (13177.1). That low touched a cluster of levels: S1 13172.3, the New York session low 13172.8 and the London session low 13173.8. The 07:15 candle then closed at 13181.7, above the 07:10 candle's high of 13177.2. That confirms a rejection at those levels.
- **The rule.** In an emerging trend, a confirmed rejection at a level in the opposite direction flips the emerging trend straight away (`analyser/states.py`, about line 309: `rejected at a level against the emerging {d} trend`). There is no test of how far price has fallen.
- **How long it lasted.** The state stayed "emerging trend (up)" from 07:15 to 08:05, while price drifted from 13181 to 13172. A rejection the other way at 08:05 flipped it back. The Asian range breakout trade record has `market_state: "emerging trend up"` for that reason. The Asian range breakout follows no analyser state, so it opened anyway.

### Was that what blocked the slow grind? No.

- **The slow grind needs "trend".** Emerging trend refuses it whichever way it points (`the analyser's state is emerging trend, which does not allow slow grind`). The two slow grind sells in that stretch were 07:25 and 08:05. Both would have been refused just the same with "emerging trend (down)", as the 07:00 and 07:05 candles were.
- **What actually held it back** was that the analyser took until **08:35** to call a down **trend**. From 06:10 to 07:00 it was in consolidation, and from 07:00 to 08:35 in an emerging trend.
- **The "up" did block the EMA pullback**, which does trade an emerging trend: `08:05 EMA pullback sell 13167.1: the emerging trend is up: EMA pullback only in the trend's direction`.

## 3. Would Johnny's trend-day signal have turned on? No.

The signal needs a slow grind trade in profit between 06:00 and 09:00, as IG would close it. **No slow grind trade opened on 18 Nov**, so the signal had nothing to fire on.

**Exactly why:**

1. **06:00 to 08:35: every slow grind sell setup was refused by the strategy checks.** The setups were at 06:25, 06:40, 07:00, 07:25 and 08:05, plus the five overnight ones that were still in profit later (part 2). The analyser wasn't in a trend state. Until 08:00, the hourly read was also against it: rally until 06:00, then ranging. Each of those setups was in profit between 06:00 and 09:00 on IG's buy price (part 1), so the signal would have fired if any had opened.
2. **08:35 to 12:00: the checks would have allowed a sell, but the slow grind's own pattern gave none.** The analyser said trend down and the hourly read said sell-off. But a slow grind sell needs 2 candles in a row that fail to make a new low while closing under the 21 EMA, then a break of their low. Candle by candle (`replay_output.txt`, last section):
   - **08:35 to 09:05:** a new low on almost every candle (13159.0, 13157.4, 13152.8, 13150.6, 13149.2, 13148.0). The one candle that didn't make a new low (08:40) was followed straight away by a new low, so no 2-candle pause ever formed.
   - **09:10 to 09:25:** a pause did form. Its low was 13148, and price never broke it. The 09:30 candle closed at 13163.4, above the 21 EMA (13161.8), which cancelled it (`closed 13163.4 above the 21 EMA 13161.8 after 4 candle(s): cancelled`).
   - **09:30 to 11:20:** closes were around or above the 21 EMA, so the setup kept starting again.
   - **11:25 to 12:00:** new lows again, with no 2-candle pause.
3. **The nearest miss was the 08:05 sell at 13171.0.** The only thing that refused it was the analyser's state: emerging trend, not trend. On IG's buy price it was +16.2 at 09:00 and +18.9 at best before 09:00. Had the analyser been in a down trend after the 08:00 candle, it would have opened (inside the slow grind's hours, nothing else open for the slow grind). The signal would then have turned on.

**In one line:** on 18 Nov the slow grind's sells came while the analyser and the hourly read were still saying "not a trend". By the time both agreed (08:35), the fall was too steady to form the slow grind's pause.

## Files

- `replay18.py`: the replay, run in a worktree at cc70dc5 with `.venv/bin/python replay18.py replay18.json`. It takes about 50 seconds, reads the candle store only and sends nothing.
- `replay_output.txt`: its output. It has the state changes, the slow grind's notes and every setup with every check, other trend ideas from 06:00 to 09:30, the per-candle state and hourly read, and the slow grind's sell watch candle by candle.
- `replay18.json`: the same data, plus the candles from Tue 21:00 to Wed 12:00, buy and sell.
- `profit18.py`, `profit_check.txt`: the profit check in part 1.
- `analyser_per_candle_0600_0930.csv`: the analyser table above, with the full hourly-read text.
