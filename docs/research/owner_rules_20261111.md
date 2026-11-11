# The owner's three rules replayed, 25 October to 11 November 2026

Wednesday 11 November 2026, UK. Read-only research: **nothing in the bot was changed**. There were no IG calls and no restart, and nothing was written outside `data/research/`.

## Summary

**Data and code.** This is a replay of the bot's own code (the current rules, commit `02a8dfe`) on its own IG candles. It runs from the week's open on Sunday 25 October (21:00 UTC) to the last stored candle, which ends at 08:35 UTC on Wednesday 11 November. Prices are IG's real buy and sell prices with no spread added. Every result is shown with the stop counted first and with the target counted first. **No candle in any of the 63 runs reached both a trade's stop and its target** (its take profit or its opposite-band close), so the two columns are the same everywhere.

**The current rules make +1,191.8 pips in 169 trades** (84 won, 84 lost, 1 at 0):

- 25 to 30 October: +224.9
- 1 to 6 November: +811.0
- 8 November to 11 November 08:35: +155.8

| Rules | Trades | Pips | Against current |
|---|---:|---:|---:|
| Current rules | 169 | +1,191.8 | |
| 1. Opposite trades closed when any bounce opens | 176 | +1,158.0 | **−33.8** |
| 1. … only bounces at S2, S3, R2 or R3 | 169 | +1,214.4 | **+22.7** |
| 2. A bounce in profit is not closed on a rejection | 163 | +1,196.7 | **+5.0** |
| 3. The hourly signs a trend has run out (19 of the 27 versions change something) | 169–173 | +988.8 to +1,205.8 | **−203.0 to +14.1**; 3 better, 16 worse, 8 no change |
| 1 (S2/S3/R2/R3) + 2 | 163 | +1,223.8 | **+32.1** |
| 1 (S2/S3/R2/R3) + 2 + 3 | 163–167 | +1,077.8 to +1,251.4 | **−113.9 to +59.7** |
| 1 (any bounce) + 2 | 170 | +1,184.6 | **−7.2** |
| 1 (any bounce) + 2 + 3 | 170–173 | +1,066.6 to +1,198.7 | **−125.2 to +7.0** |

- **Rule 1, any bounce: −33.8.**
  - It closed 38 trades on 10 days. Of the 34 that also traded under the current rules, 22 did better and 12 worse, but those 34 made **43.5 pips less** in all.
  - The 12 that did worse include trades on their way to their take profits:
    - the 27 October breakout sell, closed at +0.6 instead of +50.0;
    - four EMA pullbacks (+30 each) on 26 and 30 October;
    - three slow grinds and a level reversal (+20 each) on 26, 27 and 30 October.
  - By week: −112.8 in the first, +33.4 in the second, and **+45.7 in the third, all of it on Tuesday 10 November.**
- **Rule 1, only at S2, S3, R2 or R3: +22.7.**
  - It closed 6 trades on two days: five when the 14:10 bounce buy at S2 opened on Monday 26 October, and one when the 17:10 bounce buy at R2 opened on Wednesday 4 November.
  - **Those 6 made 1.9 pips less** than they would have.
  - The whole gain comes from one trade, a level reversal buy at 14:10 on 26 October (+20.0). It could open because the closes freed its place under the safety limits, and it replaced one at 14:45 that made −4.6.
  - Nothing changes on Tuesday 10 November: no bounce opened at those levels.
  - "At S2, S3, R2 or R3" means one of the levels the bounce's own setup records as pierced. On 2 and 4 November, bounce buys at the lower band pierced R3 and R2 from above.
- **Rule 2: +5.0.**
  - 16 bounces end differently: 7 better and 9 worse, **+6.2 pips on them**.
  - A bounce held longer is still open when the next bounce would have opened, and the bot runs one bounce at a time. So 6 bounces of the current rules never open (−1.2 in all).
  - On **Tuesday 10 November** the 07:55 bounce sell rode through the rejections at 08:30, 10:40 and 12:10. It was closed 15 minutes before the big news, at **+15.5 instead of −6.8 (+22.3)**. The 08:45 bounce sell (+12.5) then could not open, so Tuesday is +9.8.
- **Rule 3: worse in 16 of the 19 versions that change anything.**
  - It mostly closes trend trades that went on to their take profits: breakouts on 27 and 29 October and on 5, 9 and 10 November (+50 each), and EMA pullbacks on 26 October (+30 each).
  - **The looser versions lose most:** "flat" as under 8 pips loses 20 to 203, depending on the other two numbers.
  - The 3 better ones:
    - 3 of 5 · a quarter back · flat under 5: +14.1;
    - 2 of 5 · three quarters back · flat under 3: +11.3, one trade;
    - 2 of 5 · a quarter back · flat under 3: +5.8.
  - The 8 versions that change nothing need 4 of 5 wicks with "flat" under 3 or 5 pips, or 3 of 5 with three quarters back and "flat" under 3 or 5. They never saw all three signs while a trend trade in that direction was open.
- **All three together.**
  - With rule 1 at S2, S3, R2 or R3, the best is **+59.7** (2 of 5 · a quarter back · flat under 5). That is 27.6 more than rules 1 and 2 without rule 3.
  - That gain is again a knock-on, not the closes: 15 of the 16 trades it closed also traded under the current rules, and those 15 made 29.5 pips less. Closing the 29 October 14:45 breakout buy at 20:00 let a new breakout buy open at 20:10, and that one reached its +50 take profit.
  - With rule 1 for any bounce, no version of all three does better than +7.0.
- **How far to trust it:**
  - The replay covers 2½ weeks. Every difference above is a handful of trades, and the biggest gains of rule 1 (S2/S3/R2/R3) and of the best combination each come from one trade that only opened because a close freed a place.
  - Rule 3 is the owner's description, given no numbers. All 27 versions are shown and none is picked.
  - The replay and the live trades disagree on the same days: on Tuesday 10 November the replay makes +123.4 in 11 trades, while the bot's own live exits made −21.1 in 12 trades. See `strategies_by_market_20261110.md`.

## How it was done

- **Candles:** a read-only copy of the bot's own IG candle store, taken at 08:37 UTC today (`data/research/replay_stores/live_copy_20261111_0837/`). It holds IG's real buy and sell prices, ending with the candle that finished at 08:35 UTC.
- **Code:** a frozen copy of the committed code, `02a8dfe`: the range trade closed in full and the bounce by half at the opposite band. The replay is the research mode (`research.long_replay`: the same engine, strategies, safety rules, paper order sender and trade manager as the bot's own replay), run week by week.
- **Switches:** today's `.env` switches (`STOP_LOSS_PIPS=12`, every strategy on), with `TRADING` off for the replay.
- **News rules:** Finnhub's past calendar, as in the earlier reports.
- **The research copy matches the bot's own code.**
  - Unpatched, the bot's code gives 169 trades and +1,191.8.
  - My version of the trade manager's step, with no rule switched on, gives the same 169 trades, trade for trade, with the same exits, times and pips.
  - Each rule is a patch in the research process only, applied to the bot's functions while the replay runs. The scripts and every run's trades are in `data/research/replay/owner_rules_20261111/`. The scripts are kept out of the repository, which commits only this file.
- **Prices:**
  - Entries are at IG's buy price (buys) or sell price (sells), from the candles.
  - Stops and take profits fill at their level, or at the candle's open if it opened past them.
  - The 20:30 and news closes, and the rule 3 closes, are at the candle's open. Closes on a rejection are at its trigger price.
  - A rule 1 close is at the price the bounce opened at, on the side the closed trade closes on. A bounce sell opens at the sell price, where a buy closes; a bounce buy opens at the buy price, where a sell closes.
  - No spread is added: IG's buy and sell prices already include it.
- **Stop first and target first.** The run is made with the stop first. Where no candle reached both a trade's stop and its target, the target-first run takes exactly the same path, so it is not run again. That was the case in all 63 runs.
- **Trades still open at the last candle** are counted at that candle's close. In the current rules there are 4: three EMA pullback sells and a slow grind sell from this morning.
- **The 8 rule 3 versions marked \*** never saw all three signs while a trend trade in that direction was open, in the run they were added to. A rule that never closes anything leaves the run exactly as it was, so that run's result is shown for them. The check was conservative: any trend trade open across the hour counted.
- **Repeated EMA pullbacks.** In the replay the EMA pullback sometimes opens two or three trades on one candle, from separate touches with the same entry. The earlier replays did the same. Each is counted as its own trade, and the lists below show each one.
- **Win and loss:** a trade with more than 0 pips is a win, below 0 a loss.

## What each rule does in the replay

1. **A Bollinger bounce opening closes the opposite trades.** When a Bollinger bounce opens, after passing all of the bot's own rules and the safety limits (the order sender's paper open), every trade then open in the opposite direction is closed at that moment, whatever its strategy, in profit or not. Nothing closes unless a bounce actually opens.
   - *At S2, S3, R2 or R3:* the same, but only when one of the levels the bounce's setup pierced (the analyser's own list for that setup) is S2, S3, R2 or R3.
2. **A bounce in profit is held through a rejection.** Once a Bollinger bounce has been in profit in an earlier bar (its best so far above 0 pips), a confirmed rejection at a level against it no longer closes it. It runs to its stop, its take profit, the 20:30 close, or the close 15 minutes before big news.
   - The current half close at the opposite band still happens; the rest of the trade then runs.
   - A bounce that has not yet been in profit is still closed on a rejection, as now.
3. **The hourly signs that a trend has run out.** Checked as each hourly candle finishes, on the bot's own hourly candles (sell price). When all three signs are seen, every slow grind, EMA pullback and breakout trade in that direction is closed at the open of the next 5-minute candle. The level reversal is not a trend trade and is not touched. The owner's words describe a buy trend; a sell is the mirror.
   - **"Several candles with buying wicks":** at least **2, 3 or 4 of the last 5** hourly candles have a wick against the trend at least as long as their body. That is the upper wick for a buy trend and the lower wick for a sell trend, the same reading as in the earlier management report.
   - **"Well below the upper Bollinger band":** the last hourly candle closed at least **a quarter, a half or three quarters** of the way back from the upper band (20, 2) to the middle band (a sell trend: up from the lower band).
   - **"The 100 and 200 EMA completely flat":** each moved less than **3, 5 or 8 pips** over the last 12 hourly candles.

## Results

### Rules 1 and 2, alone and together

| Rules | Trades | Won | Lost | Pips, stop first | Pips, target first | Against current (stop / target) |
|---|---:|---:|---:|---:|---:|---:|
| Current rules | 169 | 84 | 84 | +1,191.8 | +1,191.8 | +0.0 / +0.0 |
| 1. Close opposite trades when a bounce opens (every bounce) | 176 | 88 | 88 | +1,158.0 | +1,158.0 | -33.8 / -33.8 |
| 1. … only bounces at S2, S3, R2 or R3 | 169 | 85 | 83 | +1,214.4 | +1,214.4 | +22.7 / +22.7 |
| 2. A bounce in profit holds through a rejection | 163 | 80 | 82 | +1,196.7 | +1,196.7 | +5.0 / +5.0 |
| 1 (every bounce) + 2 | 170 | 87 | 83 | +1,184.6 | +1,184.6 | -7.2 / -7.2 |
| 1 (S2/S3/R2/R3) + 2 | 163 | 81 | 81 | +1,223.8 | +1,223.8 | +32.1 / +32.1 |

### By week: trades (won–lost) and pips

| Rules | 25 Oct – 30 Oct | 1 Nov – 6 Nov | 8 Nov – 11 Nov 08:35 |
|---|---:|---:|---:|
| Current rules | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 28 (12–16) +155.8 |
| 1. Close opposite trades when a bounce opens (every bounce) | 64 (33–31) +112.1 | 84 (43–41) +844.4 | 28 (12–16) +201.5 |
| 1. … only bounces at S2, S3, R2 or R3 | 59 (31–27) +239.6 | 82 (42–40) +819.0 | 28 (12–16) +155.8 |
| 2. A bounce in profit holds through a rejection | 54 (28–25) +244.6 | 82 (41–41) +799.0 | 27 (11–16) +153.2 |
| 1 (every bounce) + 2 | 59 (34–25) +149.2 | 84 (42–42) +836.4 | 27 (11–16) +198.9 |
| 1 (S2/S3/R2/R3) + 2 | 54 (29–24) +259.2 | 82 (41–41) +811.4 | 27 (11–16) +153.2 |

### Rule 3 alone: all 27 versions

\* never saw all three signs while a trend trade in that direction was open, so the same as the current rules.

| Rule 3: wicks · back from band · EMAs flat | Trades | Won | Lost | Pips, stop first | Pips, target first | Against current (stop / target) |
|---|---:|---:|---:|---:|---:|---:|
| 2 of 5 · 25% back · flat < 3 | 170 | 85 | 84 | +1,197.6 | +1,197.6 | +5.8 / +5.8 |
| 2 of 5 · 25% back · flat < 5 | 172 | 87 | 84 | +1,162.4 | +1,162.4 | -29.4 / -29.4 |
| 2 of 5 · 25% back · flat < 8 | 173 | 84 | 88 | +988.8 | +988.8 | -203.0 / -203.0 |
| 2 of 5 · 50% back · flat < 3 | 170 | 84 | 85 | +1,175.2 | +1,175.2 | -16.5 / -16.5 |
| 2 of 5 · 50% back · flat < 5 | 171 | 84 | 86 | +1,105.6 | +1,105.6 | -86.1 / -86.1 |
| 2 of 5 · 50% back · flat < 8 | 171 | 83 | 87 | +1,018.0 | +1,018.0 | -173.8 / -173.8 |
| 2 of 5 · 75% back · flat < 3 | 169 | 84 | 84 | +1,203.0 | +1,203.0 | +11.3 / +11.3 |
| 2 of 5 · 75% back · flat < 5 | 170 | 82 | 87 | +1,116.0 | +1,116.0 | -75.7 / -75.7 |
| 2 of 5 · 75% back · flat < 8 | 170 | 81 | 88 | +1,066.2 | +1,066.2 | -125.6 / -125.6 |
| 3 of 5 · 25% back · flat < 3 | 170 | 85 | 84 | +1,186.2 | +1,186.2 | -5.5 / -5.5 |
| 3 of 5 · 25% back · flat < 5 | 170 | 86 | 83 | +1,205.8 | +1,205.8 | +14.1 / +14.1 |
| 3 of 5 · 25% back · flat < 8 | 170 | 85 | 84 | +1,107.0 | +1,107.0 | -84.7 / -84.7 |
| 3 of 5 · 50% back · flat < 3 | 170 | 83 | 86 | +1,092.8 | +1,092.8 | -99.0 / -99.0 |
| 3 of 5 · 50% back · flat < 5 | 170 | 83 | 86 | +1,092.8 | +1,092.8 | -99.0 / -99.0 |
| 3 of 5 · 50% back · flat < 8 | 170 | 83 | 86 | +1,111.8 | +1,111.8 | -80.0 / -80.0 |
| 3 of 5 · 75% back · flat < 3 * | 169 | 84 | 84 | +1,191.8 | +1,191.8 | +0.0 / +0.0 |
| 3 of 5 · 75% back · flat < 5 * | 169 | 84 | 84 | +1,191.8 | +1,191.8 | +0.0 / +0.0 |
| 3 of 5 · 75% back · flat < 8 | 169 | 83 | 85 | +1,141.8 | +1,141.8 | -49.9 / -49.9 |
| 4 of 5 · 25% back · flat < 3 * | 169 | 84 | 84 | +1,191.8 | +1,191.8 | +0.0 / +0.0 |
| 4 of 5 · 25% back · flat < 5 * | 169 | 84 | 84 | +1,191.8 | +1,191.8 | +0.0 / +0.0 |
| 4 of 5 · 25% back · flat < 8 | 169 | 84 | 84 | +1,172.2 | +1,172.2 | -19.6 / -19.6 |
| 4 of 5 · 50% back · flat < 3 * | 169 | 84 | 84 | +1,191.8 | +1,191.8 | +0.0 / +0.0 |
| 4 of 5 · 50% back · flat < 5 * | 169 | 84 | 84 | +1,191.8 | +1,191.8 | +0.0 / +0.0 |
| 4 of 5 · 50% back · flat < 8 | 169 | 83 | 85 | +1,141.8 | +1,141.8 | -49.9 / -49.9 |
| 4 of 5 · 75% back · flat < 3 * | 169 | 84 | 84 | +1,191.8 | +1,191.8 | +0.0 / +0.0 |
| 4 of 5 · 75% back · flat < 5 * | 169 | 84 | 84 | +1,191.8 | +1,191.8 | +0.0 / +0.0 |
| 4 of 5 · 75% back · flat < 8 | 169 | 83 | 85 | +1,141.8 | +1,141.8 | -49.9 / -49.9 |

### Rule 3 alone, by week

| Rule 3 | 25 Oct – 30 Oct | 1 Nov – 6 Nov | 8 Nov – 11 Nov 08:35 |
|---|---:|---:|---:|
| 2 of 5 · 25% back · flat < 3 | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 29 (13–16) +161.6 |
| 2 of 5 · 25% back · flat < 5 | 61 (31–29) +170.1 | 82 (42–40) +811.0 | 29 (14–15) +181.2 |
| 2 of 5 · 25% back · flat < 8 | 61 (28–32) +38.6 | 82 (42–40) +804.0 | 30 (14–16) +146.1 |
| 2 of 5 · 50% back · flat < 3 | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 29 (12–17) +139.3 |
| 2 of 5 · 50% back · flat < 5 | 60 (30–29) +155.3 | 82 (42–40) +811.0 | 29 (12–17) +139.3 |
| 2 of 5 · 50% back · flat < 8 | 60 (29–30) +99.4 | 82 (42–40) +779.2 | 29 (12–17) +139.3 |
| 2 of 5 · 75% back · flat < 3 | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 28 (12–16) +167.1 |
| 2 of 5 · 75% back · flat < 5 | 60 (28–31) +137.9 | 82 (42–40) +811.0 | 28 (12–16) +167.1 |
| 2 of 5 · 75% back · flat < 8 | 60 (27–32) +82.0 | 82 (42–40) +817.0 | 28 (12–16) +167.1 |
| 3 of 5 · 25% back · flat < 3 | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 29 (13–16) +150.3 |
| 3 of 5 · 25% back · flat < 5 | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 29 (14–15) +169.9 |
| 3 of 5 · 25% back · flat < 8 | 59 (29–29) +138.2 | 82 (42–40) +775.4 | 29 (14–15) +193.4 |
| 3 of 5 · 50% back · flat < 3 | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 29 (11–18) +56.8 |
| 3 of 5 · 50% back · flat < 5 | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 29 (11–18) +56.8 |
| 3 of 5 · 50% back · flat < 8 | 59 (29–29) +169.0 | 82 (42–40) +817.0 | 29 (12–17) +125.7 |
| 3 of 5 · 75% back · flat < 3 * | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 28 (12–16) +155.8 |
| 3 of 5 · 75% back · flat < 5 * | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 28 (12–16) +155.8 |
| 3 of 5 · 75% back · flat < 8 | 59 (29–29) +169.0 | 82 (42–40) +817.0 | 28 (12–16) +155.8 |
| 4 of 5 · 25% back · flat < 3 * | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 28 (12–16) +155.8 |
| 4 of 5 · 25% back · flat < 5 * | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 28 (12–16) +155.8 |
| 4 of 5 · 25% back · flat < 8 | 59 (29–29) +169.0 | 82 (42–40) +817.0 | 28 (13–15) +186.1 |
| 4 of 5 · 50% back · flat < 3 * | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 28 (12–16) +155.8 |
| 4 of 5 · 50% back · flat < 5 * | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 28 (12–16) +155.8 |
| 4 of 5 · 50% back · flat < 8 | 59 (29–29) +169.0 | 82 (42–40) +817.0 | 28 (12–16) +155.8 |
| 4 of 5 · 75% back · flat < 3 * | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 28 (12–16) +155.8 |
| 4 of 5 · 75% back · flat < 5 * | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 28 (12–16) +155.8 |
| 4 of 5 · 75% back · flat < 8 | 59 (29–29) +169.0 | 82 (42–40) +817.0 | 28 (12–16) +155.8 |

### All three together, rule 1 for any bounce

Rules 1 (any bounce) and 2, with each version of rule 3. \* the same as rules 1 and 2 without rule 3 (+1,184.6).

| Rule 3: wicks · back from band · EMAs flat | Trades | Won | Lost | Pips, stop first | Pips, target first | Against current (stop / target) |
|---|---:|---:|---:|---:|---:|---:|
| 2 of 5 · 25% back · flat < 3 | 171 | 88 | 83 | +1,190.4 | +1,190.4 | -1.4 / -1.4 |
| 2 of 5 · 25% back · flat < 5 | 172 | 89 | 83 | +1,192.5 | +1,192.5 | +0.8 / +0.8 |
| 2 of 5 · 25% back · flat < 8 | 173 | 87 | 86 | +1,066.6 | +1,066.6 | -125.2 / -125.2 |
| 2 of 5 · 50% back · flat < 3 | 171 | 87 | 84 | +1,168.1 | +1,168.1 | -23.6 / -23.6 |
| 2 of 5 · 50% back · flat < 5 | 171 | 86 | 85 | +1,162.0 | +1,162.0 | -29.8 / -29.8 |
| 2 of 5 · 50% back · flat < 8 | 171 | 86 | 85 | +1,130.2 | +1,130.2 | -61.6 / -61.6 |
| 2 of 5 · 75% back · flat < 3 | 170 | 87 | 83 | +1,195.9 | +1,195.9 | +4.2 / +4.2 |
| 2 of 5 · 75% back · flat < 5 | 170 | 86 | 84 | +1,189.8 | +1,189.8 | -2.0 / -2.0 |
| 2 of 5 · 75% back · flat < 8 | 170 | 86 | 84 | +1,195.8 | +1,195.8 | +4.0 / +4.0 |
| 3 of 5 · 25% back · flat < 3 | 171 | 88 | 83 | +1,179.1 | +1,179.1 | -12.6 / -12.6 |
| 3 of 5 · 25% back · flat < 5 | 171 | 89 | 82 | +1,198.7 | +1,198.7 | +7.0 / +7.0 |
| 3 of 5 · 25% back · flat < 8 | 171 | 89 | 82 | +1,127.3 | +1,127.3 | -64.4 / -64.4 |
| 3 of 5 · 50% back · flat < 3 | 171 | 88 | 83 | +1,179.5 | +1,179.5 | -12.2 / -12.2 |
| 3 of 5 · 50% back · flat < 5 | 171 | 88 | 83 | +1,179.5 | +1,179.5 | -12.2 / -12.2 |
| 3 of 5 · 50% back · flat < 8 | 171 | 88 | 83 | +1,185.5 | +1,185.5 | -6.2 / -6.2 |
| 3 of 5 · 75% back · flat < 3 * | 170 | 87 | 83 | +1,184.6 | +1,184.6 | -7.2 / -7.2 |
| 3 of 5 · 75% back · flat < 5 * | 170 | 87 | 83 | +1,184.6 | +1,184.6 | -7.2 / -7.2 |
| 3 of 5 · 75% back · flat < 8 | 170 | 87 | 83 | +1,190.6 | +1,190.6 | -1.2 / -1.2 |
| 4 of 5 · 25% back · flat < 3 * | 170 | 87 | 83 | +1,184.6 | +1,184.6 | -7.2 / -7.2 |
| 4 of 5 · 25% back · flat < 5 * | 170 | 87 | 83 | +1,184.6 | +1,184.6 | -7.2 / -7.2 |
| 4 of 5 · 25% back · flat < 8 | 170 | 87 | 83 | +1,190.6 | +1,190.6 | -1.2 / -1.2 |
| 4 of 5 · 50% back · flat < 3 * | 170 | 87 | 83 | +1,184.6 | +1,184.6 | -7.2 / -7.2 |
| 4 of 5 · 50% back · flat < 5 * | 170 | 87 | 83 | +1,184.6 | +1,184.6 | -7.2 / -7.2 |
| 4 of 5 · 50% back · flat < 8 | 170 | 87 | 83 | +1,190.6 | +1,190.6 | -1.2 / -1.2 |
| 4 of 5 · 75% back · flat < 3 * | 170 | 87 | 83 | +1,184.6 | +1,184.6 | -7.2 / -7.2 |
| 4 of 5 · 75% back · flat < 5 * | 170 | 87 | 83 | +1,184.6 | +1,184.6 | -7.2 / -7.2 |
| 4 of 5 · 75% back · flat < 8 | 170 | 87 | 83 | +1,190.6 | +1,190.6 | -1.2 / -1.2 |

### All three together, rule 1 for any bounce, by week

| Rule 3 | 25 Oct – 30 Oct | 1 Nov – 6 Nov | 8 Nov – 11 Nov 08:35 |
|---|---:|---:|---:|
| 2 of 5 · 25% back · flat < 3 | 59 (34–25) +149.2 | 84 (42–42) +836.4 | 28 (12–16) +204.7 |
| 2 of 5 · 25% back · flat < 5 | 60 (34–26) +131.8 | 84 (42–42) +836.4 | 28 (13–15) +224.3 |
| 2 of 5 · 25% back · flat < 8 | 60 (32–28) +76.4 | 84 (42–42) +829.4 | 29 (13–16) +160.7 |
| 2 of 5 · 50% back · flat < 3 | 59 (34–25) +149.2 | 84 (42–42) +836.4 | 28 (11–17) +182.4 |
| 2 of 5 · 50% back · flat < 5 | 59 (33–26) +143.2 | 84 (42–42) +836.4 | 28 (11–17) +182.4 |
| 2 of 5 · 50% back · flat < 8 | 59 (33–26) +143.2 | 84 (42–42) +804.6 | 28 (11–17) +182.4 |
| 2 of 5 · 75% back · flat < 3 | 59 (34–25) +149.2 | 84 (42–42) +836.4 | 27 (11–16) +210.2 |
| 2 of 5 · 75% back · flat < 5 | 59 (33–26) +143.2 | 84 (42–42) +836.4 | 27 (11–16) +210.2 |
| 2 of 5 · 75% back · flat < 8 | 59 (33–26) +143.2 | 84 (42–42) +842.4 | 27 (11–16) +210.2 |
| 3 of 5 · 25% back · flat < 3 | 59 (34–25) +149.2 | 84 (42–42) +836.4 | 28 (12–16) +193.4 |
| 3 of 5 · 25% back · flat < 5 | 59 (34–25) +149.2 | 84 (42–42) +836.4 | 28 (13–15) +213.0 |
| 3 of 5 · 25% back · flat < 8 | 59 (34–25) +118.4 | 84 (42–42) +800.8 | 28 (13–15) +208.0 |
| 3 of 5 · 50% back · flat < 3 | 59 (34–25) +149.2 | 84 (42–42) +836.4 | 28 (12–16) +193.8 |
| 3 of 5 · 50% back · flat < 5 | 59 (34–25) +149.2 | 84 (42–42) +836.4 | 28 (12–16) +193.8 |
| 3 of 5 · 50% back · flat < 8 | 59 (34–25) +149.2 | 84 (42–42) +842.4 | 28 (12–16) +193.8 |
| 3 of 5 · 75% back · flat < 3 * | 59 (34–25) +149.2 | 84 (42–42) +836.4 | 27 (11–16) +198.9 |
| 3 of 5 · 75% back · flat < 5 * | 59 (34–25) +149.2 | 84 (42–42) +836.4 | 27 (11–16) +198.9 |
| 3 of 5 · 75% back · flat < 8 | 59 (34–25) +149.2 | 84 (42–42) +842.4 | 27 (11–16) +198.9 |
| 4 of 5 · 25% back · flat < 3 * | 59 (34–25) +149.2 | 84 (42–42) +836.4 | 27 (11–16) +198.9 |
| 4 of 5 · 25% back · flat < 5 * | 59 (34–25) +149.2 | 84 (42–42) +836.4 | 27 (11–16) +198.9 |
| 4 of 5 · 25% back · flat < 8 | 59 (34–25) +149.2 | 84 (42–42) +842.4 | 27 (11–16) +198.9 |
| 4 of 5 · 50% back · flat < 3 * | 59 (34–25) +149.2 | 84 (42–42) +836.4 | 27 (11–16) +198.9 |
| 4 of 5 · 50% back · flat < 5 * | 59 (34–25) +149.2 | 84 (42–42) +836.4 | 27 (11–16) +198.9 |
| 4 of 5 · 50% back · flat < 8 | 59 (34–25) +149.2 | 84 (42–42) +842.4 | 27 (11–16) +198.9 |
| 4 of 5 · 75% back · flat < 3 * | 59 (34–25) +149.2 | 84 (42–42) +836.4 | 27 (11–16) +198.9 |
| 4 of 5 · 75% back · flat < 5 * | 59 (34–25) +149.2 | 84 (42–42) +836.4 | 27 (11–16) +198.9 |
| 4 of 5 · 75% back · flat < 8 | 59 (34–25) +149.2 | 84 (42–42) +842.4 | 27 (11–16) +198.9 |

### All three together, rule 1 at S2, S3, R2 or R3

Rules 1 (S2/S3/R2/R3) and 2, with each version of rule 3. \* the same as rules 1 and 2 without rule 3 (+1,223.8).

| Rule 3: wicks · back from band · EMAs flat | Trades | Won | Lost | Pips, stop first | Pips, target first | Against current (stop / target) |
|---|---:|---:|---:|---:|---:|---:|
| 2 of 5 · 25% back · flat < 3 | 164 | 82 | 81 | +1,229.6 | +1,229.6 | +37.9 / +37.9 |
| 2 of 5 · 25% back · flat < 5 | 166 | 84 | 81 | +1,251.4 | +1,251.4 | +59.7 / +59.7 |
| 2 of 5 · 25% back · flat < 8 | 167 | 81 | 85 | +1,077.8 | +1,077.8 | -113.9 / -113.9 |
| 2 of 5 · 50% back · flat < 3 | 164 | 81 | 82 | +1,207.4 | +1,207.4 | +15.6 / +15.6 |
| 2 of 5 · 50% back · flat < 5 | 165 | 81 | 83 | +1,194.8 | +1,194.8 | +3.0 / +3.0 |
| 2 of 5 · 50% back · flat < 8 | 165 | 80 | 84 | +1,107.0 | +1,107.0 | -84.7 / -84.7 |
| 2 of 5 · 75% back · flat < 3 | 163 | 81 | 81 | +1,235.2 | +1,235.2 | +43.4 / +43.4 |
| 2 of 5 · 75% back · flat < 5 | 164 | 81 | 82 | +1,222.6 | +1,222.6 | +30.8 / +30.8 |
| 2 of 5 · 75% back · flat < 8 | 164 | 80 | 83 | +1,172.6 | +1,172.6 | -19.1 / -19.1 |
| 3 of 5 · 25% back · flat < 3 | 164 | 82 | 81 | +1,218.4 | +1,218.4 | +26.6 / +26.6 |
| 3 of 5 · 25% back · flat < 5 | 164 | 83 | 80 | +1,238.0 | +1,238.0 | +46.2 / +46.2 |
| 3 of 5 · 25% back · flat < 8 | 164 | 82 | 81 | +1,139.2 | +1,139.2 | -52.6 / -52.6 |
| 3 of 5 · 50% back · flat < 3 | 164 | 80 | 83 | +1,124.8 | +1,124.8 | -66.9 / -66.9 |
| 3 of 5 · 50% back · flat < 5 | 164 | 80 | 83 | +1,124.8 | +1,124.8 | -66.9 / -66.9 |
| 3 of 5 · 50% back · flat < 8 | 164 | 80 | 83 | +1,143.8 | +1,143.8 | -47.9 / -47.9 |
| 3 of 5 · 75% back · flat < 3 * | 163 | 81 | 81 | +1,223.8 | +1,223.8 | +32.1 / +32.1 |
| 3 of 5 · 75% back · flat < 5 * | 163 | 81 | 81 | +1,223.8 | +1,223.8 | +32.1 / +32.1 |
| 3 of 5 · 75% back · flat < 8 | 163 | 80 | 82 | +1,174.0 | +1,174.0 | -17.8 / -17.8 |
| 4 of 5 · 25% back · flat < 3 * | 163 | 81 | 81 | +1,223.8 | +1,223.8 | +32.1 / +32.1 |
| 4 of 5 · 25% back · flat < 5 * | 163 | 81 | 81 | +1,223.8 | +1,223.8 | +32.1 / +32.1 |
| 4 of 5 · 25% back · flat < 8 | 163 | 81 | 81 | +1,204.2 | +1,204.2 | +12.5 / +12.5 |
| 4 of 5 · 50% back · flat < 3 * | 163 | 81 | 81 | +1,223.8 | +1,223.8 | +32.1 / +32.1 |
| 4 of 5 · 50% back · flat < 5 * | 163 | 81 | 81 | +1,223.8 | +1,223.8 | +32.1 / +32.1 |
| 4 of 5 · 50% back · flat < 8 | 163 | 80 | 82 | +1,174.0 | +1,174.0 | -17.8 / -17.8 |
| 4 of 5 · 75% back · flat < 3 * | 163 | 81 | 81 | +1,223.8 | +1,223.8 | +32.1 / +32.1 |
| 4 of 5 · 75% back · flat < 5 * | 163 | 81 | 81 | +1,223.8 | +1,223.8 | +32.1 / +32.1 |
| 4 of 5 · 75% back · flat < 8 | 163 | 80 | 82 | +1,174.0 | +1,174.0 | -17.8 / -17.8 |

### All three together, rule 1 at S2, S3, R2 or R3, by week

| Rule 3 | 25 Oct – 30 Oct | 1 Nov – 6 Nov | 8 Nov – 11 Nov 08:35 |
|---|---:|---:|---:|
| 2 of 5 · 25% back · flat < 3 | 54 (29–24) +259.2 | 82 (41–41) +811.4 | 28 (12–16) +159.0 |
| 2 of 5 · 25% back · flat < 5 | 56 (30–25) +261.4 | 82 (41–41) +811.4 | 28 (13–15) +178.6 |
| 2 of 5 · 25% back · flat < 8 | 56 (27–28) +130.0 | 82 (41–41) +804.4 | 29 (13–16) +143.5 |
| 2 of 5 · 50% back · flat < 3 | 54 (29–24) +259.2 | 82 (41–41) +811.4 | 28 (11–17) +136.7 |
| 2 of 5 · 50% back · flat < 5 | 55 (29–25) +246.6 | 82 (41–41) +811.4 | 28 (11–17) +136.7 |
| 2 of 5 · 50% back · flat < 8 | 55 (28–26) +190.8 | 82 (41–41) +779.6 | 28 (11–17) +136.7 |
| 2 of 5 · 75% back · flat < 3 | 54 (29–24) +259.2 | 82 (41–41) +811.4 | 27 (11–16) +164.5 |
| 2 of 5 · 75% back · flat < 5 | 55 (29–25) +246.6 | 82 (41–41) +811.4 | 27 (11–16) +164.5 |
| 2 of 5 · 75% back · flat < 8 | 55 (28–26) +190.8 | 82 (41–41) +817.4 | 27 (11–16) +164.5 |
| 3 of 5 · 25% back · flat < 3 | 54 (29–24) +259.2 | 82 (41–41) +811.4 | 28 (12–16) +147.7 |
| 3 of 5 · 25% back · flat < 5 | 54 (29–24) +259.2 | 82 (41–41) +811.4 | 28 (13–15) +167.3 |
| 3 of 5 · 25% back · flat < 8 | 54 (28–25) +172.6 | 82 (41–41) +775.8 | 28 (13–15) +190.8 |
| 3 of 5 · 50% back · flat < 3 | 54 (29–24) +259.2 | 82 (41–41) +811.4 | 28 (10–18) +54.2 |
| 3 of 5 · 50% back · flat < 5 | 54 (29–24) +259.2 | 82 (41–41) +811.4 | 28 (10–18) +54.2 |
| 3 of 5 · 50% back · flat < 8 | 54 (28–25) +203.4 | 82 (41–41) +817.4 | 28 (11–17) +123.1 |
| 3 of 5 · 75% back · flat < 3 * | 54 (29–24) +259.2 | 82 (41–41) +811.4 | 27 (11–16) +153.2 |
| 3 of 5 · 75% back · flat < 5 * | 54 (29–24) +259.2 | 82 (41–41) +811.4 | 27 (11–16) +153.2 |
| 3 of 5 · 75% back · flat < 8 | 54 (28–25) +203.4 | 82 (41–41) +817.4 | 27 (11–16) +153.2 |
| 4 of 5 · 25% back · flat < 3 * | 54 (29–24) +259.2 | 82 (41–41) +811.4 | 27 (11–16) +153.2 |
| 4 of 5 · 25% back · flat < 5 * | 54 (29–24) +259.2 | 82 (41–41) +811.4 | 27 (11–16) +153.2 |
| 4 of 5 · 25% back · flat < 8 | 54 (28–25) +203.4 | 82 (41–41) +817.4 | 27 (12–15) +183.5 |
| 4 of 5 · 50% back · flat < 3 * | 54 (29–24) +259.2 | 82 (41–41) +811.4 | 27 (11–16) +153.2 |
| 4 of 5 · 50% back · flat < 5 * | 54 (29–24) +259.2 | 82 (41–41) +811.4 | 27 (11–16) +153.2 |
| 4 of 5 · 50% back · flat < 8 | 54 (28–25) +203.4 | 82 (41–41) +817.4 | 27 (11–16) +153.2 |
| 4 of 5 · 75% back · flat < 3 * | 54 (29–24) +259.2 | 82 (41–41) +811.4 | 27 (11–16) +153.2 |
| 4 of 5 · 75% back · flat < 5 * | 54 (29–24) +259.2 | 82 (41–41) +811.4 | 27 (11–16) +153.2 |
| 4 of 5 · 75% back · flat < 8 | 54 (28–25) +203.4 | 82 (41–41) +817.4 | 27 (11–16) +153.2 |

## Tuesday 10 November, trade by trade

Times are UK (the same as UTC since 25 October). The rule 3 versions with the same Tuesday are grouped together.

### Current rules

| UK | Trade | Pips | How it closed |
|---|---|---:|---|
| 05:00 | EMA pullback buy | -12.0 | stop |
| 06:10 | EMA pullback buy | -12.0 | stop |
| 07:20 | EMA pullback buy | -12.0 | stop |
| 07:55 | Bollinger bounce sell | -6.8 | rejection at a level |
| 08:45 | Bollinger bounce sell | +12.5 | rejection at a level (half at the band +3.2) |
| 09:10 | breakout sell | +50.0 | take profit |
| 13:30 | slow grind sell | +100.0 | take profit |
| 14:05 | level reversal sell | +20.0 | take profit |
| 16:25 | level reversal sell | -20.0 | stop |
| 17:00 | Bollinger bounce buy | +15.7 | scheduled close (half at the band +10.1) |
| 22:00 | EMA pullback sell | -12.0 | stop |
| | **Tuesday** | **+123.4** | 11 trades |

### 1. Close opposite trades when a bounce opens (every bounce)

| UK | Trade | Current rules | With the rule | Difference |
|---|---|---|---|---:|
| 05:00 | EMA pullback buy | -12.0 stop | -0.4 closed: bounce opened | +11.6 |
| 06:10 | EMA pullback buy | -12.0 stop | -2.3 closed: bounce opened | +9.7 |
| 07:20 | EMA pullback buy | -12.0 stop | -5.7 closed: bounce opened | +6.3 |
| 07:55 | Bollinger bounce sell | -6.8 rejection at a level | -6.8 rejection at a level | +0.0 |
| 08:45 | Bollinger bounce sell | +12.5 rejection at a level (half at the band +3.2) | +12.5 rejection at a level (half at the band +3.2) | +0.0 |
| 09:10 | breakout sell | +50.0 take profit | +50.0 take profit | +0.0 |
| 13:30 | slow grind sell | +100.0 take profit | +100.0 take profit | +0.0 |
| 14:05 | level reversal sell | +20.0 take profit | +20.0 take profit | +0.0 |
| 16:25 | level reversal sell | -20.0 stop | -1.9 closed: bounce opened | +18.1 |
| 17:00 | Bollinger bounce buy | +15.7 scheduled close (half at the band +10.1) | +15.7 scheduled close (half at the band +10.1) | +0.0 |
| 22:00 | EMA pullback sell | -12.0 stop | -12.0 stop | +0.0 |
| | **Tuesday** | **11 trades, +123.4** | **11 trades, +169.1** | **+45.7** |

### 1. … only bounces at S2, S3, R2 or R3

| UK | Trade | Current rules | With the rule | Difference |
|---|---|---|---|---:|
| 05:00 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 06:10 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 07:20 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 07:55 | Bollinger bounce sell | -6.8 rejection at a level | -6.8 rejection at a level | +0.0 |
| 08:45 | Bollinger bounce sell | +12.5 rejection at a level (half at the band +3.2) | +12.5 rejection at a level (half at the band +3.2) | +0.0 |
| 09:10 | breakout sell | +50.0 take profit | +50.0 take profit | +0.0 |
| 13:30 | slow grind sell | +100.0 take profit | +100.0 take profit | +0.0 |
| 14:05 | level reversal sell | +20.0 take profit | +20.0 take profit | +0.0 |
| 16:25 | level reversal sell | -20.0 stop | -20.0 stop | +0.0 |
| 17:00 | Bollinger bounce buy | +15.7 scheduled close (half at the band +10.1) | +15.7 scheduled close (half at the band +10.1) | +0.0 |
| 22:00 | EMA pullback sell | -12.0 stop | -12.0 stop | +0.0 |
| | **Tuesday** | **11 trades, +123.4** | **11 trades, +123.4** | **+0.0** |

### 2. A bounce in profit holds through a rejection

| UK | Trade | Current rules | With the rule | Difference |
|---|---|---|---|---:|
| 05:00 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 06:10 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 07:20 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 07:55 | Bollinger bounce sell | -6.8 rejection at a level | +15.5 before big news (half at the band -0.2) | +22.3 |
| 08:45 | Bollinger bounce sell | +12.5 rejection at a level (half at the band +3.2) | — |  |
| 09:10 | breakout sell | +50.0 take profit | +50.0 take profit | +0.0 |
| 13:30 | slow grind sell | +100.0 take profit | +100.0 take profit | +0.0 |
| 14:05 | level reversal sell | +20.0 take profit | +20.0 take profit | +0.0 |
| 16:25 | level reversal sell | -20.0 stop | -20.0 stop | +0.0 |
| 17:00 | Bollinger bounce buy | +15.7 scheduled close (half at the band +10.1) | +15.7 scheduled close (half at the band +10.1) | +0.0 |
| 22:00 | EMA pullback sell | -12.0 stop | -12.0 stop | +0.0 |
| | **Tuesday** | **11 trades, +123.4** | **10 trades, +133.2** | **+9.8** |

### 1 (every bounce) + 2

| UK | Trade | Current rules | With the rule | Difference |
|---|---|---|---|---:|
| 05:00 | EMA pullback buy | -12.0 stop | -0.4 closed: bounce opened | +11.6 |
| 06:10 | EMA pullback buy | -12.0 stop | -2.3 closed: bounce opened | +9.7 |
| 07:20 | EMA pullback buy | -12.0 stop | -5.7 closed: bounce opened | +6.3 |
| 07:55 | Bollinger bounce sell | -6.8 rejection at a level | +15.5 before big news (half at the band -0.2) | +22.3 |
| 08:45 | Bollinger bounce sell | +12.5 rejection at a level (half at the band +3.2) | — |  |
| 09:10 | breakout sell | +50.0 take profit | +50.0 take profit | +0.0 |
| 13:30 | slow grind sell | +100.0 take profit | +100.0 take profit | +0.0 |
| 14:05 | level reversal sell | +20.0 take profit | +20.0 take profit | +0.0 |
| 16:25 | level reversal sell | -20.0 stop | -1.9 closed: bounce opened | +18.1 |
| 17:00 | Bollinger bounce buy | +15.7 scheduled close (half at the band +10.1) | +15.7 scheduled close (half at the band +10.1) | +0.0 |
| 22:00 | EMA pullback sell | -12.0 stop | -12.0 stop | +0.0 |
| | **Tuesday** | **11 trades, +123.4** | **10 trades, +178.9** | **+55.5** |

### 1 (S2/S3/R2/R3) + 2

| UK | Trade | Current rules | With the rule | Difference |
|---|---|---|---|---:|
| 05:00 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 06:10 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 07:20 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 07:55 | Bollinger bounce sell | -6.8 rejection at a level | +15.5 before big news (half at the band -0.2) | +22.3 |
| 08:45 | Bollinger bounce sell | +12.5 rejection at a level (half at the band +3.2) | — |  |
| 09:10 | breakout sell | +50.0 take profit | +50.0 take profit | +0.0 |
| 13:30 | slow grind sell | +100.0 take profit | +100.0 take profit | +0.0 |
| 14:05 | level reversal sell | +20.0 take profit | +20.0 take profit | +0.0 |
| 16:25 | level reversal sell | -20.0 stop | -20.0 stop | +0.0 |
| 17:00 | Bollinger bounce buy | +15.7 scheduled close (half at the band +10.1) | +15.7 scheduled close (half at the band +10.1) | +0.0 |
| 22:00 | EMA pullback sell | -12.0 stop | -12.0 stop | +0.0 |
| | **Tuesday** | **11 trades, +123.4** | **10 trades, +133.2** | **+9.8** |

### 3: 2 of 5 · 25% back · flat < 3; 2 of 5 · 25% back · flat < 5; 2 of 5 · 50% back · flat < 3; 2 of 5 · 50% back · flat < 5; 2 of 5 · 50% back · flat < 8; 2 of 5 · 75% back · flat < 3; 2 of 5 · 75% back · flat < 5; 2 of 5 · 75% back · flat < 8; 3 of 5 · 25% back · flat < 3; 3 of 5 · 25% back · flat < 5; 3 of 5 · 75% back · flat < 3; 3 of 5 · 75% back · flat < 5; 3 of 5 · 75% back · flat < 8; 4 of 5 · 25% back · flat < 3; 4 of 5 · 25% back · flat < 5; 4 of 5 · 50% back · flat < 3; 4 of 5 · 50% back · flat < 5; 4 of 5 · 50% back · flat < 8; 4 of 5 · 75% back · flat < 3; 4 of 5 · 75% back · flat < 5; 4 of 5 · 75% back · flat < 8

| UK | Trade | Current rules | With the rule | Difference |
|---|---|---|---|---:|
| 05:00 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 06:10 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 07:20 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 07:55 | Bollinger bounce sell | -6.8 rejection at a level | -6.8 rejection at a level | +0.0 |
| 08:45 | Bollinger bounce sell | +12.5 rejection at a level (half at the band +3.2) | +12.5 rejection at a level (half at the band +3.2) | +0.0 |
| 09:10 | breakout sell | +50.0 take profit | +50.0 take profit | +0.0 |
| 13:30 | slow grind sell | +100.0 take profit | +100.0 take profit | +0.0 |
| 14:05 | level reversal sell | +20.0 take profit | +20.0 take profit | +0.0 |
| 16:25 | level reversal sell | -20.0 stop | -20.0 stop | +0.0 |
| 17:00 | Bollinger bounce buy | +15.7 scheduled close (half at the band +10.1) | +15.7 scheduled close (half at the band +10.1) | +0.0 |
| 22:00 | EMA pullback sell | -12.0 stop | -12.0 stop | +0.0 |
| | **Tuesday** | **11 trades, +123.4** | **11 trades, +123.4** | **+0.0** |

### 3: 2 of 5 · 25% back · flat < 8

| UK | Trade | Current rules | With the rule | Difference |
|---|---|---|---|---:|
| 05:00 | EMA pullback buy | -12.0 stop | -5.8 closed: hourly exhaustion | +6.2 |
| 06:10 | EMA pullback buy | -12.0 stop | -4.8 closed: hourly exhaustion | +7.2 |
| 07:20 | EMA pullback buy | -12.0 stop | -4.8 closed: hourly exhaustion | +7.2 |
| 07:55 | Bollinger bounce sell | -6.8 rejection at a level | -6.8 rejection at a level | +0.0 |
| 08:45 | Bollinger bounce sell | +12.5 rejection at a level (half at the band +3.2) | +12.5 rejection at a level (half at the band +3.2) | +0.0 |
| 09:10 | breakout sell | +50.0 take profit | +6.3 closed: hourly exhaustion | -43.7 |
| 13:10 | breakout sell | — | -12.0 stop |  |
| 13:30 | slow grind sell | +100.0 take profit | +100.0 take profit | +0.0 |
| 14:05 | level reversal sell | +20.0 take profit | +20.0 take profit | +0.0 |
| 16:25 | level reversal sell | -20.0 stop | -20.0 stop | +0.0 |
| 17:00 | Bollinger bounce buy | +15.7 scheduled close (half at the band +10.1) | +15.7 scheduled close (half at the band +10.1) | +0.0 |
| 22:00 | EMA pullback sell | -12.0 stop | -12.0 stop | +0.0 |
| | **Tuesday** | **11 trades, +123.4** | **12 trades, +88.3** | **-35.1** |

### 3: 3 of 5 · 25% back · flat < 8

| UK | Trade | Current rules | With the rule | Difference |
|---|---|---|---|---:|
| 05:00 | EMA pullback buy | -12.0 stop | -2.9 closed: hourly exhaustion | +9.1 |
| 06:10 | EMA pullback buy | -12.0 stop | -4.8 closed: hourly exhaustion | +7.2 |
| 07:20 | EMA pullback buy | -12.0 stop | -4.8 closed: hourly exhaustion | +7.2 |
| 07:55 | Bollinger bounce sell | -6.8 rejection at a level | -6.8 rejection at a level | +0.0 |
| 08:45 | Bollinger bounce sell | +12.5 rejection at a level (half at the band +3.2) | +12.5 rejection at a level (half at the band +3.2) | +0.0 |
| 09:10 | breakout sell | +50.0 take profit | +50.0 take profit | +0.0 |
| 13:30 | slow grind sell | +100.0 take profit | +100.0 take profit | +0.0 |
| 14:05 | level reversal sell | +20.0 take profit | +20.0 take profit | +0.0 |
| 16:25 | level reversal sell | -20.0 stop | -20.0 stop | +0.0 |
| 17:00 | Bollinger bounce buy | +15.7 scheduled close (half at the band +10.1) | +15.7 scheduled close (half at the band +10.1) | +0.0 |
| 22:00 | EMA pullback sell | -12.0 stop | -12.0 stop | +0.0 |
| | **Tuesday** | **11 trades, +123.4** | **11 trades, +146.9** | **+23.5** |

### 3: 3 of 5 · 50% back · flat < 3; 3 of 5 · 50% back · flat < 5

| UK | Trade | Current rules | With the rule | Difference |
|---|---|---|---|---:|
| 05:00 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 06:10 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 07:20 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 07:55 | Bollinger bounce sell | -6.8 rejection at a level | -6.8 rejection at a level | +0.0 |
| 08:45 | Bollinger bounce sell | +12.5 rejection at a level (half at the band +3.2) | +12.5 rejection at a level (half at the band +3.2) | +0.0 |
| 09:10 | breakout sell | +50.0 take profit | — |  |
| 13:10 | breakout sell | — | -12.0 stop |  |
| 13:30 | slow grind sell | +100.0 take profit | +100.0 take profit | +0.0 |
| 14:05 | level reversal sell | +20.0 take profit | +20.0 take profit | +0.0 |
| 16:25 | level reversal sell | -20.0 stop | -20.0 stop | +0.0 |
| 17:00 | Bollinger bounce buy | +15.7 scheduled close (half at the band +10.1) | +15.7 scheduled close (half at the band +10.1) | +0.0 |
| 22:00 | EMA pullback sell | -12.0 stop | -12.0 stop | +0.0 |
| | **Tuesday** | **11 trades, +123.4** | **11 trades, +61.4** | **-62.0** |

### 3: 3 of 5 · 50% back · flat < 8

| UK | Trade | Current rules | With the rule | Difference |
|---|---|---|---|---:|
| 05:00 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 06:10 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 07:20 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 07:55 | Bollinger bounce sell | -6.8 rejection at a level | -6.8 rejection at a level | +0.0 |
| 08:45 | Bollinger bounce sell | +12.5 rejection at a level (half at the band +3.2) | +12.5 rejection at a level (half at the band +3.2) | +0.0 |
| 09:10 | breakout sell | +50.0 take profit | — |  |
| 11:50 | breakout sell | — | +50.0 take profit |  |
| 13:30 | slow grind sell | +100.0 take profit | +100.0 take profit | +0.0 |
| 14:05 | level reversal sell | +20.0 take profit | +20.0 take profit | +0.0 |
| 16:25 | level reversal sell | -20.0 stop | -20.0 stop | +0.0 |
| 17:00 | Bollinger bounce buy | +15.7 scheduled close (half at the band +10.1) | +15.7 scheduled close (half at the band +10.1) | +0.0 |
| 22:00 | EMA pullback sell | -12.0 stop | -12.0 stop | +0.0 |
| | **Tuesday** | **11 trades, +123.4** | **11 trades, +123.4** | **+0.0** |

### 3: 4 of 5 · 25% back · flat < 8

| UK | Trade | Current rules | With the rule | Difference |
|---|---|---|---|---:|
| 05:00 | EMA pullback buy | -12.0 stop | +0.5 closed: hourly exhaustion | +12.5 |
| 06:10 | EMA pullback buy | -12.0 stop | -1.4 closed: hourly exhaustion | +10.6 |
| 07:20 | EMA pullback buy | -12.0 stop | -4.8 closed: hourly exhaustion | +7.2 |
| 07:55 | Bollinger bounce sell | -6.8 rejection at a level | -6.8 rejection at a level | +0.0 |
| 08:45 | Bollinger bounce sell | +12.5 rejection at a level (half at the band +3.2) | +12.5 rejection at a level (half at the band +3.2) | +0.0 |
| 09:10 | breakout sell | +50.0 take profit | +50.0 take profit | +0.0 |
| 13:30 | slow grind sell | +100.0 take profit | +100.0 take profit | +0.0 |
| 14:05 | level reversal sell | +20.0 take profit | +20.0 take profit | +0.0 |
| 16:25 | level reversal sell | -20.0 stop | -20.0 stop | +0.0 |
| 17:00 | Bollinger bounce buy | +15.7 scheduled close (half at the band +10.1) | +15.7 scheduled close (half at the band +10.1) | +0.0 |
| 22:00 | EMA pullback sell | -12.0 stop | -12.0 stop | +0.0 |
| | **Tuesday** | **11 trades, +123.4** | **11 trades, +153.7** | **+30.3** |

### 1 (every) + 2 + 3: 2 of 5 · 25% back · flat < 3; 2 of 5 · 25% back · flat < 5; 2 of 5 · 50% back · flat < 3; 2 of 5 · 50% back · flat < 5; 2 of 5 · 50% back · flat < 8; 2 of 5 · 75% back · flat < 3; 2 of 5 · 75% back · flat < 5; 2 of 5 · 75% back · flat < 8; 3 of 5 · 25% back · flat < 3; 3 of 5 · 25% back · flat < 5; 3 of 5 · 50% back · flat < 3; 3 of 5 · 50% back · flat < 5; 3 of 5 · 50% back · flat < 8; 3 of 5 · 75% back · flat < 3; 3 of 5 · 75% back · flat < 5; 3 of 5 · 75% back · flat < 8; 4 of 5 · 25% back · flat < 3; 4 of 5 · 25% back · flat < 5; 4 of 5 · 25% back · flat < 8; 4 of 5 · 50% back · flat < 3; 4 of 5 · 50% back · flat < 5; 4 of 5 · 50% back · flat < 8; 4 of 5 · 75% back · flat < 3; 4 of 5 · 75% back · flat < 5; 4 of 5 · 75% back · flat < 8

| UK | Trade | Current rules | With the rule | Difference |
|---|---|---|---|---:|
| 05:00 | EMA pullback buy | -12.0 stop | -0.4 closed: bounce opened | +11.6 |
| 06:10 | EMA pullback buy | -12.0 stop | -2.3 closed: bounce opened | +9.7 |
| 07:20 | EMA pullback buy | -12.0 stop | -5.7 closed: bounce opened | +6.3 |
| 07:55 | Bollinger bounce sell | -6.8 rejection at a level | +15.5 before big news (half at the band -0.2) | +22.3 |
| 08:45 | Bollinger bounce sell | +12.5 rejection at a level (half at the band +3.2) | — |  |
| 09:10 | breakout sell | +50.0 take profit | +50.0 take profit | +0.0 |
| 13:30 | slow grind sell | +100.0 take profit | +100.0 take profit | +0.0 |
| 14:05 | level reversal sell | +20.0 take profit | +20.0 take profit | +0.0 |
| 16:25 | level reversal sell | -20.0 stop | -1.9 closed: bounce opened | +18.1 |
| 17:00 | Bollinger bounce buy | +15.7 scheduled close (half at the band +10.1) | +15.7 scheduled close (half at the band +10.1) | +0.0 |
| 22:00 | EMA pullback sell | -12.0 stop | -12.0 stop | +0.0 |
| | **Tuesday** | **11 trades, +123.4** | **10 trades, +178.9** | **+55.5** |

### 1 (every) + 2 + 3: 2 of 5 · 25% back · flat < 8

| UK | Trade | Current rules | With the rule | Difference |
|---|---|---|---|---:|
| 05:00 | EMA pullback buy | -12.0 stop | -5.8 closed: hourly exhaustion | +6.2 |
| 06:10 | EMA pullback buy | -12.0 stop | -4.8 closed: hourly exhaustion | +7.2 |
| 07:20 | EMA pullback buy | -12.0 stop | -5.7 closed: bounce opened | +6.3 |
| 07:55 | Bollinger bounce sell | -6.8 rejection at a level | +15.5 before big news (half at the band -0.2) | +22.3 |
| 08:45 | Bollinger bounce sell | +12.5 rejection at a level (half at the band +3.2) | — |  |
| 09:10 | breakout sell | +50.0 take profit | +6.3 closed: hourly exhaustion | -43.7 |
| 13:10 | breakout sell | — | -12.0 stop |  |
| 13:30 | slow grind sell | +100.0 take profit | +100.0 take profit | +0.0 |
| 14:05 | level reversal sell | +20.0 take profit | +20.0 take profit | +0.0 |
| 16:25 | level reversal sell | -20.0 stop | -1.9 closed: bounce opened | +18.1 |
| 17:00 | Bollinger bounce buy | +15.7 scheduled close (half at the band +10.1) | +15.7 scheduled close (half at the band +10.1) | +0.0 |
| 22:00 | EMA pullback sell | -12.0 stop | -12.0 stop | +0.0 |
| | **Tuesday** | **11 trades, +123.4** | **11 trades, +115.3** | **-8.1** |

### 1 (every) + 2 + 3: 3 of 5 · 25% back · flat < 8

| UK | Trade | Current rules | With the rule | Difference |
|---|---|---|---|---:|
| 05:00 | EMA pullback buy | -12.0 stop | -2.9 closed: hourly exhaustion | +9.1 |
| 06:10 | EMA pullback buy | -12.0 stop | -4.8 closed: hourly exhaustion | +7.2 |
| 07:20 | EMA pullback buy | -12.0 stop | -5.7 closed: bounce opened | +6.3 |
| 07:55 | Bollinger bounce sell | -6.8 rejection at a level | +15.5 before big news (half at the band -0.2) | +22.3 |
| 08:45 | Bollinger bounce sell | +12.5 rejection at a level (half at the band +3.2) | — |  |
| 09:10 | breakout sell | +50.0 take profit | +50.0 take profit | +0.0 |
| 13:30 | slow grind sell | +100.0 take profit | +100.0 take profit | +0.0 |
| 14:05 | level reversal sell | +20.0 take profit | +20.0 take profit | +0.0 |
| 16:25 | level reversal sell | -20.0 stop | -1.9 closed: bounce opened | +18.1 |
| 17:00 | Bollinger bounce buy | +15.7 scheduled close (half at the band +10.1) | +15.7 scheduled close (half at the band +10.1) | +0.0 |
| 22:00 | EMA pullback sell | -12.0 stop | -12.0 stop | +0.0 |
| | **Tuesday** | **11 trades, +123.4** | **10 trades, +173.9** | **+50.5** |

### 1 (S2–R3) + 2 + 3: 2 of 5 · 25% back · flat < 3; 2 of 5 · 25% back · flat < 5; 2 of 5 · 50% back · flat < 3; 2 of 5 · 50% back · flat < 5; 2 of 5 · 50% back · flat < 8; 2 of 5 · 75% back · flat < 3; 2 of 5 · 75% back · flat < 5; 2 of 5 · 75% back · flat < 8; 3 of 5 · 25% back · flat < 3; 3 of 5 · 25% back · flat < 5; 3 of 5 · 75% back · flat < 3; 3 of 5 · 75% back · flat < 5; 3 of 5 · 75% back · flat < 8; 4 of 5 · 25% back · flat < 3; 4 of 5 · 25% back · flat < 5; 4 of 5 · 50% back · flat < 3; 4 of 5 · 50% back · flat < 5; 4 of 5 · 50% back · flat < 8; 4 of 5 · 75% back · flat < 3; 4 of 5 · 75% back · flat < 5; 4 of 5 · 75% back · flat < 8

| UK | Trade | Current rules | With the rule | Difference |
|---|---|---|---|---:|
| 05:00 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 06:10 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 07:20 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 07:55 | Bollinger bounce sell | -6.8 rejection at a level | +15.5 before big news (half at the band -0.2) | +22.3 |
| 08:45 | Bollinger bounce sell | +12.5 rejection at a level (half at the band +3.2) | — |  |
| 09:10 | breakout sell | +50.0 take profit | +50.0 take profit | +0.0 |
| 13:30 | slow grind sell | +100.0 take profit | +100.0 take profit | +0.0 |
| 14:05 | level reversal sell | +20.0 take profit | +20.0 take profit | +0.0 |
| 16:25 | level reversal sell | -20.0 stop | -20.0 stop | +0.0 |
| 17:00 | Bollinger bounce buy | +15.7 scheduled close (half at the band +10.1) | +15.7 scheduled close (half at the band +10.1) | +0.0 |
| 22:00 | EMA pullback sell | -12.0 stop | -12.0 stop | +0.0 |
| | **Tuesday** | **11 trades, +123.4** | **10 trades, +133.2** | **+9.8** |

### 1 (S2–R3) + 2 + 3: 2 of 5 · 25% back · flat < 8

| UK | Trade | Current rules | With the rule | Difference |
|---|---|---|---|---:|
| 05:00 | EMA pullback buy | -12.0 stop | -5.8 closed: hourly exhaustion | +6.2 |
| 06:10 | EMA pullback buy | -12.0 stop | -4.8 closed: hourly exhaustion | +7.2 |
| 07:20 | EMA pullback buy | -12.0 stop | -4.8 closed: hourly exhaustion | +7.2 |
| 07:55 | Bollinger bounce sell | -6.8 rejection at a level | +15.5 before big news (half at the band -0.2) | +22.3 |
| 08:45 | Bollinger bounce sell | +12.5 rejection at a level (half at the band +3.2) | — |  |
| 09:10 | breakout sell | +50.0 take profit | +6.3 closed: hourly exhaustion | -43.7 |
| 13:10 | breakout sell | — | -12.0 stop |  |
| 13:30 | slow grind sell | +100.0 take profit | +100.0 take profit | +0.0 |
| 14:05 | level reversal sell | +20.0 take profit | +20.0 take profit | +0.0 |
| 16:25 | level reversal sell | -20.0 stop | -20.0 stop | +0.0 |
| 17:00 | Bollinger bounce buy | +15.7 scheduled close (half at the band +10.1) | +15.7 scheduled close (half at the band +10.1) | +0.0 |
| 22:00 | EMA pullback sell | -12.0 stop | -12.0 stop | +0.0 |
| | **Tuesday** | **11 trades, +123.4** | **11 trades, +98.1** | **-25.3** |

### 1 (S2–R3) + 2 + 3: 3 of 5 · 25% back · flat < 8

| UK | Trade | Current rules | With the rule | Difference |
|---|---|---|---|---:|
| 05:00 | EMA pullback buy | -12.0 stop | -2.9 closed: hourly exhaustion | +9.1 |
| 06:10 | EMA pullback buy | -12.0 stop | -4.8 closed: hourly exhaustion | +7.2 |
| 07:20 | EMA pullback buy | -12.0 stop | -4.8 closed: hourly exhaustion | +7.2 |
| 07:55 | Bollinger bounce sell | -6.8 rejection at a level | +15.5 before big news (half at the band -0.2) | +22.3 |
| 08:45 | Bollinger bounce sell | +12.5 rejection at a level (half at the band +3.2) | — |  |
| 09:10 | breakout sell | +50.0 take profit | +50.0 take profit | +0.0 |
| 13:30 | slow grind sell | +100.0 take profit | +100.0 take profit | +0.0 |
| 14:05 | level reversal sell | +20.0 take profit | +20.0 take profit | +0.0 |
| 16:25 | level reversal sell | -20.0 stop | -20.0 stop | +0.0 |
| 17:00 | Bollinger bounce buy | +15.7 scheduled close (half at the band +10.1) | +15.7 scheduled close (half at the band +10.1) | +0.0 |
| 22:00 | EMA pullback sell | -12.0 stop | -12.0 stop | +0.0 |
| | **Tuesday** | **11 trades, +123.4** | **10 trades, +156.7** | **+33.3** |

### 1 (S2–R3) + 2 + 3: 3 of 5 · 50% back · flat < 3; 3 of 5 · 50% back · flat < 5

| UK | Trade | Current rules | With the rule | Difference |
|---|---|---|---|---:|
| 05:00 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 06:10 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 07:20 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 07:55 | Bollinger bounce sell | -6.8 rejection at a level | +15.5 before big news (half at the band -0.2) | +22.3 |
| 08:45 | Bollinger bounce sell | +12.5 rejection at a level (half at the band +3.2) | — |  |
| 09:10 | breakout sell | +50.0 take profit | — |  |
| 13:10 | breakout sell | — | -12.0 stop |  |
| 13:30 | slow grind sell | +100.0 take profit | +100.0 take profit | +0.0 |
| 14:05 | level reversal sell | +20.0 take profit | +20.0 take profit | +0.0 |
| 16:25 | level reversal sell | -20.0 stop | -20.0 stop | +0.0 |
| 17:00 | Bollinger bounce buy | +15.7 scheduled close (half at the band +10.1) | +15.7 scheduled close (half at the band +10.1) | +0.0 |
| 22:00 | EMA pullback sell | -12.0 stop | -12.0 stop | +0.0 |
| | **Tuesday** | **11 trades, +123.4** | **10 trades, +71.2** | **-52.2** |

### 1 (S2–R3) + 2 + 3: 3 of 5 · 50% back · flat < 8

| UK | Trade | Current rules | With the rule | Difference |
|---|---|---|---|---:|
| 05:00 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 06:10 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 07:20 | EMA pullback buy | -12.0 stop | -12.0 stop | +0.0 |
| 07:55 | Bollinger bounce sell | -6.8 rejection at a level | +15.5 before big news (half at the band -0.2) | +22.3 |
| 08:45 | Bollinger bounce sell | +12.5 rejection at a level (half at the band +3.2) | — |  |
| 09:10 | breakout sell | +50.0 take profit | — |  |
| 11:50 | breakout sell | — | +50.0 take profit |  |
| 13:30 | slow grind sell | +100.0 take profit | +100.0 take profit | +0.0 |
| 14:05 | level reversal sell | +20.0 take profit | +20.0 take profit | +0.0 |
| 16:25 | level reversal sell | -20.0 stop | -20.0 stop | +0.0 |
| 17:00 | Bollinger bounce buy | +15.7 scheduled close (half at the band +10.1) | +15.7 scheduled close (half at the band +10.1) | +0.0 |
| 22:00 | EMA pullback sell | -12.0 stop | -12.0 stop | +0.0 |
| | **Tuesday** | **11 trades, +123.4** | **10 trades, +133.2** | **+9.8** |

### 1 (S2–R3) + 2 + 3: 4 of 5 · 25% back · flat < 8

| UK | Trade | Current rules | With the rule | Difference |
|---|---|---|---|---:|
| 05:00 | EMA pullback buy | -12.0 stop | +0.5 closed: hourly exhaustion | +12.5 |
| 06:10 | EMA pullback buy | -12.0 stop | -1.4 closed: hourly exhaustion | +10.6 |
| 07:20 | EMA pullback buy | -12.0 stop | -4.8 closed: hourly exhaustion | +7.2 |
| 07:55 | Bollinger bounce sell | -6.8 rejection at a level | +15.5 before big news (half at the band -0.2) | +22.3 |
| 08:45 | Bollinger bounce sell | +12.5 rejection at a level (half at the band +3.2) | — |  |
| 09:10 | breakout sell | +50.0 take profit | +50.0 take profit | +0.0 |
| 13:30 | slow grind sell | +100.0 take profit | +100.0 take profit | +0.0 |
| 14:05 | level reversal sell | +20.0 take profit | +20.0 take profit | +0.0 |
| 16:25 | level reversal sell | -20.0 stop | -20.0 stop | +0.0 |
| 17:00 | Bollinger bounce buy | +15.7 scheduled close (half at the band +10.1) | +15.7 scheduled close (half at the band +10.1) | +0.0 |
| 22:00 | EMA pullback sell | -12.0 stop | -12.0 stop | +0.0 |
| | **Tuesday** | **11 trades, +123.4** | **10 trades, +163.5** | **+40.1** |

## Every trade each rule closed

Each close is shown with what that trade made under the current rules (stop first, the same as target first here). "Not opened under the current rules" means the trade only opened because an earlier close freed a place under the safety limits. Below each list are the trades that opened in only one of the two runs, for the same reason. Rule 2 closes nothing early: its list shows every bounce whose result changed, with the rejections it held through.

### 1, every bounce

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:25 | slow grind sell | Mon 26 Oct 09:05 | +3.5 | closed: bounce opened | +20.0 (take profit) | -16.5 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Tue 27 Oct 05:45 | slow grind sell | Tue 27 Oct 07:20 | +6.1 | closed: bounce opened | +20.0 (take profit) | -13.9 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 07:20 | +0.6 | closed: bounce opened | +50.0 (take profit) | -49.4 |
| Tue 27 Oct 16:05 | slow grind sell | Tue 27 Oct 16:40 | -0.6 | closed: bounce opened | +0.0 (scheduled close) | -0.6 |
| Tue 27 Oct 16:15 | EMA pullback sell | Tue 27 Oct 16:40 | -5.3 | closed: bounce opened | -12.0 (stop) | +6.7 |
| Wed 28 Oct 04:45 | slow grind sell | Wed 28 Oct 07:25 | +14.5 | closed: bounce opened | +10.0 (profit lock) | +4.5 |
| Wed 28 Oct 10:20 | slow grind sell | Wed 28 Oct 10:35 | -7.4 | closed: bounce opened | -15.0 (stop) | +7.6 |
| Wed 28 Oct 10:45 | EMA pullback sell | Wed 28 Oct 11:15 | -5.8 | closed: bounce opened | -12.0 (stop) | +6.2 |
| Wed 28 Oct 10:45 | EMA pullback sell | Wed 28 Oct 11:15 | -5.8 | closed: bounce opened | -12.0 (stop) | +6.2 |
| Wed 28 Oct 15:30 | slow grind buy | Wed 28 Oct 15:50 | -8.8 | closed: bounce opened | +10.0 (profit lock) | -18.8 |
| Wed 28 Oct 16:15 | level reversal buy | Wed 28 Oct 17:05 | +3.5 | closed: bounce opened | -1.7 (before big news) | +5.2 |
| Wed 28 Oct 16:50 | slow grind buy | Wed 28 Oct 17:05 | -1.1 | closed: bounce opened | not opened under the current rules |  |
| Thu 29 Oct 22:05 | EMA pullback buy | Fri 30 Oct 07:45 | +16.8 | closed: bounce opened | +10.9 (scheduled close) | +5.9 |
| Fri 30 Oct 00:40 | EMA pullback buy | Fri 30 Oct 07:45 | +11.5 | closed: bounce opened | +30.0 (take profit) | -18.5 |
| Fri 30 Oct 07:10 | EMA pullback buy | Fri 30 Oct 07:45 | +0.7 | closed: bounce opened | +30.0 (take profit) | -29.3 |
| Fri 30 Oct 07:25 | level reversal buy | Fri 30 Oct 07:45 | -9.9 | closed: bounce opened | +20.0 (take profit) | -29.9 |
| Fri 30 Oct 08:15 | level reversal buy | Fri 30 Oct 10:40 | +11.1 | closed: bounce opened | not opened under the current rules |  |
| Fri 30 Oct 08:15 | slow grind buy | Fri 30 Oct 10:40 | +13.1 | closed: bounce opened | +20.0 (take profit) | -6.9 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 13:25 | level reversal sell | Fri 30 Oct 15:25 | +0.7 | closed: bounce opened | -4.1 (scheduled close) | +4.8 |
| Fri 30 Oct 16:15 | level reversal buy | Fri 30 Oct 16:25 | -8.4 | closed: bounce opened | not opened under the current rules |  |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Tue 03 Nov 08:05 | EMA pullback buy | Tue 03 Nov 08:20 | -7.8 | closed: bounce opened | -12.0 (stop) | +4.2 |
| Wed 04 Nov 08:30 | slow grind buy | Wed 04 Nov 10:40 | -6.7 | closed: bounce opened | -15.0 (stop) | +8.3 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 15:40 | -7.5 | closed: bounce opened | -15.0 (stop) | +7.5 |
| Wed 04 Nov 16:10 | slow grind sell | Wed 04 Nov 17:10 | -5.5 | closed: bounce opened at R2 | not opened under the current rules |  |
| Thu 05 Nov 08:00 | slow grind sell | Thu 05 Nov 08:15 | -10.9 | closed: bounce opened | +9.7 (profit lock) | -20.6 |
| Tue 10 Nov 05:00 | EMA pullback buy | Tue 10 Nov 07:55 | -0.4 | closed: bounce opened | -12.0 (stop) | +11.6 |
| Tue 10 Nov 06:10 | EMA pullback buy | Tue 10 Nov 07:55 | -2.3 | closed: bounce opened | -12.0 (stop) | +9.7 |
| Tue 10 Nov 07:20 | EMA pullback buy | Tue 10 Nov 07:55 | -5.7 | closed: bounce opened | -12.0 (stop) | +6.3 |
| Tue 10 Nov 16:25 | level reversal sell | Tue 10 Nov 17:00 | -1.9 | closed: bounce opened | -20.0 (stop) | +18.1 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Wed 28 Oct 16:50 | slow grind buy | opened only with the rule | -1.1 (closed: bounce opened) |
| Fri 30 Oct 08:15 | level reversal buy | opened only with the rule | +11.1 (closed: bounce opened) |
| Fri 30 Oct 16:15 | level reversal buy | opened only with the rule | -8.4 (closed: bounce opened) |
| Fri 30 Oct 16:45 | level reversal sell | opened only with the rule | -6.0 (scheduled close) |
| Wed 04 Nov 16:10 | slow grind sell | opened only with the rule | -5.5 (closed: bounce opened at R2) |
| Thu 05 Nov 10:20 | slow grind sell | opened only with the rule | -15.0 (stop) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |

### 1, bounces at S2, S3, R2 or R3

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 17:10 | -7.0 | closed: bounce opened at R2 | -15.0 (stop) | +8.0 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |

### 2, bounces held through a rejection (every bounce whose result changed)

| Opened | Trade | Closed | Pips with the rule | How (and the rejections it held through) | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 09:05 | Bollinger bounce buy | Mon 26 Oct 13:20 | -6.0 | stop (half at the band +0.1), held at 09:55, 11:55, 12:40, 13:05 | -7.9 (rejection at a level) | +2.0 |
| Mon 26 Oct 14:10 | Bollinger bounce buy | Mon 26 Oct 20:30 | +7.0 | scheduled close (half at the band +10.0), held at 15:45, 17:50, 18:35, 19:00, 20:05 | +7.2 (rejection at a level (half at the band +10.0)) | -0.1 |
| Tue 27 Oct 07:20 | Bollinger bounce buy | Tue 27 Oct 09:25 | -12.0 | stop, held at 08:10, 08:50, 09:10 | -5.0 (rejection at a level) | -7.0 |
| Tue 27 Oct 09:55 | Bollinger bounce buy | Tue 27 Oct 16:15 | -4.6 | stop (half at the band +2.9), held at 10:35, 11:40, 12:35, 13:10, 13:30, 14:25, 14:45, 15:15 | -4.6 (rejection at a level) | +0.0 |
| Tue 27 Oct 12:35 | Bollinger bounce sell | Tue 27 Oct 20:30 | +13.2 | scheduled close (half at the band +8.0), held at 14:00, 16:40, 17:00, 18:15, 19:05 | +7.0 (rejection at a level (half at the band +8.0)) | +6.2 |
| Tue 27 Oct 16:40 | Bollinger bounce buy | Tue 27 Oct 20:30 | +3.0 | scheduled close (half at the band +7.4), held at 17:35 | +5.8 (rejection at a level (half at the band +7.4)) | -2.8 |
| Wed 28 Oct 07:25 | Bollinger bounce buy | Wed 28 Oct 17:45 | +19.8 | before big news (half at the band +11.4), held at 08:40, 09:00, 09:45, 10:20, 12:30, 14:00, 14:15, 15:20, 15:50, 17:05, 17:20 | +11.4 (rejection at a level (half at the band +11.4)) | +8.4 |
| Wed 28 Oct 13:55 | Bollinger bounce sell | Wed 28 Oct 16:05 | -12.0 | stop, held at 14:35, 15:05, 15:35, 16:00 | +1.4 (rejection at a level) | -13.4 |
| Fri 30 Oct 10:40 | Bollinger bounce sell | Fri 30 Oct 20:30 | +14.2 | scheduled close (half at the band -0.2), held at 12:20, 15:25, 16:00, 16:15, 18:10, 18:35, 19:15, 19:50 | -1.8 (rejection at a level (half at the band -0.2)) | +16.0 |
| Fri 30 Oct 15:25 | Bollinger bounce buy | Fri 30 Oct 20:30 | +4.9 | scheduled close (half at the band +6.5), held at 16:25, 16:45, 17:20, 18:45, 19:35 | +5.8 (rejection at a level (half at the band +6.5)) | -0.8 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 20:30 | +26.0 | scheduled close (half at the band +26.5), held at 11:05, 11:25, 12:25, 14:30, 16:20, 17:00, 17:20, 18:55, 19:10 | +25.8 (rejection at a level (half at the band +26.5)) | +0.2 |
| Tue 03 Nov 06:45 | Bollinger bounce sell | Tue 03 Nov 07:20 | -6.6 | stop (half at the band -1.1), held at 07:00 | -3.0 (rejection at a level (half at the band -1.1)) | -3.5 |
| Tue 03 Nov 08:20 | Bollinger bounce sell | Tue 03 Nov 13:30 | -2.9 | stop (half at the band +6.2), held at 09:25, 10:35, 11:50, 12:55, 13:25 | +3.8 (rejection at a level (half at the band +6.2)) | -6.7 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 20:30 | +13.5 | scheduled close (half at the band +7.6), held at 15:40, 16:05, 17:10 | +15.6 (rejection at a level (half at the band +7.6)) | -2.1 |
| Tue 10 Nov 07:55 | Bollinger bounce sell | Tue 10 Nov 13:15 | +15.5 | before big news (half at the band -0.2), held at 08:30, 10:40, 12:10 | -6.8 (rejection at a level) | +22.3 |
| Wed 11 Nov 06:55 | Bollinger bounce buy | Wed 11 Nov 08:10 | -12.0 | stop, held at 07:30 | +0.4 (rejection at a level) | -12.4 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Fri 30 Oct 16:25 | Bollinger bounce sell | opened only under the current rules | +6.4 (rejection at a level (half at the band +7.3)) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 3: 2 of 5 · 25% back · flat < 3

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 15:00 | +17.2 | closed: hourly exhaustion | +50.0 (take profit) | -32.8 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 15:00 | -7.2 | closed: hourly exhaustion | -15.0 (stop) | +7.8 |
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 22:00 | +7.7 | closed: hourly exhaustion | not opened under the current rules |  |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | +7.7 (closed: hourly exhaustion) |

### 3: 2 of 5 · 25% back · flat < 5

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 06:05 | slow grind sell | Mon 26 Oct 07:00 | -2.6 | closed: hourly exhaustion | +10.0 (profit lock) | -12.6 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 17:00 | +1.5 | closed: hourly exhaustion | +30.0 (take profit) | -28.5 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 17:00 | +1.5 | closed: hourly exhaustion | +30.0 (take profit) | -28.5 |
| Thu 29 Oct 14:45 | breakout buy | Thu 29 Oct 20:00 | +14.8 | closed: hourly exhaustion | +50.0 (take profit) | -35.2 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 14:00 | +27.0 | closed: hourly exhaustion | +50.0 (take profit) | -23.0 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 14:00 | +2.6 | closed: hourly exhaustion | -15.0 (stop) | +17.6 |
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 22:00 | +7.7 | closed: hourly exhaustion | not opened under the current rules |  |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 07:40 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Thu 29 Oct 20:10 | breakout buy | opened only with the rule | +50.0 (take profit) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | +7.7 (closed: hourly exhaustion) |
| Mon 26 Oct 08:25 | slow grind sell | opened only under the current rules | +20.0 (take profit) |

### 3: 2 of 5 · 25% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 06:05 | slow grind sell | Mon 26 Oct 07:00 | -2.6 | closed: hourly exhaustion | +10.0 (profit lock) | -12.6 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 17:00 | +1.5 | closed: hourly exhaustion | +30.0 (take profit) | -28.5 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 17:00 | +1.5 | closed: hourly exhaustion | +30.0 (take profit) | -28.5 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 13:00 | -5.9 | closed: hourly exhaustion | +50.0 (take profit) | -55.9 |
| Thu 29 Oct 14:45 | breakout buy | Thu 29 Oct 20:00 | +14.8 | closed: hourly exhaustion | +50.0 (take profit) | -35.2 |
| Thu 29 Oct 20:10 | breakout buy | Thu 29 Oct 22:00 | -8.0 | closed: hourly exhaustion | not opened under the current rules |  |
| Thu 29 Oct 22:05 | EMA pullback buy | Fri 30 Oct 00:00 | -6.7 | closed: hourly exhaustion | +10.9 (scheduled close) | -17.6 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |
| Tue 03 Nov 18:05 | EMA pullback buy | Tue 03 Nov 19:00 | -2.9 | closed: hourly exhaustion | -12.0 (stop) | +9.1 |
| Tue 03 Nov 18:05 | EMA pullback buy | Tue 03 Nov 19:00 | -2.9 | closed: hourly exhaustion | -12.0 (stop) | +9.1 |
| Tue 03 Nov 18:05 | breakout buy | Tue 03 Nov 19:00 | -1.6 | closed: hourly exhaustion | -12.0 (stop) | +10.4 |
| Thu 05 Nov 18:35 | breakout sell | Thu 05 Nov 20:00 | +8.4 | closed: hourly exhaustion | +50.0 (take profit) | -41.6 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 14:00 | +27.0 | closed: hourly exhaustion | +50.0 (take profit) | -23.0 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 14:00 | +2.6 | closed: hourly exhaustion | -15.0 (stop) | +17.6 |
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 22:00 | +7.7 | closed: hourly exhaustion | not opened under the current rules |  |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Tue 10 Nov 05:00 | EMA pullback buy | Tue 10 Nov 06:00 | -5.8 | closed: hourly exhaustion | -12.0 (stop) | +6.2 |
| Tue 10 Nov 06:10 | EMA pullback buy | Tue 10 Nov 07:00 | -4.8 | closed: hourly exhaustion | -12.0 (stop) | +7.2 |
| Tue 10 Nov 07:20 | EMA pullback buy | Tue 10 Nov 08:00 | -4.8 | closed: hourly exhaustion | -12.0 (stop) | +7.2 |
| Tue 10 Nov 09:10 | breakout sell | Tue 10 Nov 12:00 | +6.3 | closed: hourly exhaustion | +50.0 (take profit) | -43.7 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 07:40 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Thu 29 Oct 20:10 | breakout buy | opened only with the rule | -8.0 (closed: hourly exhaustion) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | +7.7 (closed: hourly exhaustion) |
| Tue 10 Nov 13:10 | breakout sell | opened only with the rule | -12.0 (stop) |
| Mon 26 Oct 08:25 | slow grind sell | opened only under the current rules | +20.0 (take profit) |

### 3: 2 of 5 · 50% back · flat < 3

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 15:00 | +17.2 | closed: hourly exhaustion | +50.0 (take profit) | -32.8 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 15:00 | -7.2 | closed: hourly exhaustion | -15.0 (stop) | +7.8 |
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 23:00 | -2.8 | closed: hourly exhaustion | not opened under the current rules |  |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | -2.8 (closed: hourly exhaustion) |

### 3: 2 of 5 · 50% back · flat < 5

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 06:05 | slow grind sell | Mon 26 Oct 07:00 | -2.6 | closed: hourly exhaustion | +10.0 (profit lock) | -12.6 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 17:00 | +1.5 | closed: hourly exhaustion | +30.0 (take profit) | -28.5 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 17:00 | +1.5 | closed: hourly exhaustion | +30.0 (take profit) | -28.5 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 15:00 | +17.2 | closed: hourly exhaustion | +50.0 (take profit) | -32.8 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 15:00 | -7.2 | closed: hourly exhaustion | -15.0 (stop) | +7.8 |
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 23:00 | -2.8 | closed: hourly exhaustion | not opened under the current rules |  |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 07:40 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | -2.8 (closed: hourly exhaustion) |
| Mon 26 Oct 08:25 | slow grind sell | opened only under the current rules | +20.0 (take profit) |

### 3: 2 of 5 · 50% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 06:05 | slow grind sell | Mon 26 Oct 07:00 | -2.6 | closed: hourly exhaustion | +10.0 (profit lock) | -12.6 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 17:00 | +1.5 | closed: hourly exhaustion | +30.0 (take profit) | -28.5 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 17:00 | +1.5 | closed: hourly exhaustion | +30.0 (take profit) | -28.5 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 13:00 | -5.9 | closed: hourly exhaustion | +50.0 (take profit) | -55.9 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |
| Thu 05 Nov 18:35 | breakout sell | Fri 06 Nov 00:00 | +12.2 | closed: hourly exhaustion | +50.0 (take profit) | -37.8 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 15:00 | +17.2 | closed: hourly exhaustion | +50.0 (take profit) | -32.8 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 15:00 | -7.2 | closed: hourly exhaustion | -15.0 (stop) | +7.8 |
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 23:00 | -2.8 | closed: hourly exhaustion | not opened under the current rules |  |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 07:40 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | -2.8 (closed: hourly exhaustion) |
| Mon 26 Oct 08:25 | slow grind sell | opened only under the current rules | +20.0 (take profit) |

### 3: 2 of 5 · 75% back · flat < 3

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |

### 3: 2 of 5 · 75% back · flat < 5

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 06:05 | slow grind sell | Mon 26 Oct 07:00 | -2.6 | closed: hourly exhaustion | +10.0 (profit lock) | -12.6 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 18:00 | -7.2 | closed: hourly exhaustion | +30.0 (take profit) | -37.2 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 18:00 | -7.2 | closed: hourly exhaustion | +30.0 (take profit) | -37.2 |
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 07:40 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 08:25 | slow grind sell | opened only under the current rules | +20.0 (take profit) |

### 3: 2 of 5 · 75% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 06:05 | slow grind sell | Mon 26 Oct 07:00 | -2.6 | closed: hourly exhaustion | +10.0 (profit lock) | -12.6 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 18:00 | -7.2 | closed: hourly exhaustion | +30.0 (take profit) | -37.2 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 18:00 | -7.2 | closed: hourly exhaustion | +30.0 (take profit) | -37.2 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 13:00 | -5.9 | closed: hourly exhaustion | +50.0 (take profit) | -55.9 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 07:40 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 08:25 | slow grind sell | opened only under the current rules | +20.0 (take profit) |

### 3: 3 of 5 · 25% back · flat < 3

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 15:00 | +17.2 | closed: hourly exhaustion | +50.0 (take profit) | -32.8 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 15:00 | -7.2 | closed: hourly exhaustion | -15.0 (stop) | +7.8 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 22:00 | +7.7 | closed: hourly exhaustion | not opened under the current rules |  |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | +7.7 (closed: hourly exhaustion) |

### 3: 3 of 5 · 25% back · flat < 5

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 14:00 | +27.0 | closed: hourly exhaustion | +50.0 (take profit) | -23.0 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 14:00 | +2.6 | closed: hourly exhaustion | -15.0 (stop) | +17.6 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 22:00 | +7.7 | closed: hourly exhaustion | not opened under the current rules |  |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | +7.7 (closed: hourly exhaustion) |

### 3: 3 of 5 · 25% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 13:00 | -5.9 | closed: hourly exhaustion | +50.0 (take profit) | -55.9 |
| Thu 29 Oct 14:45 | breakout buy | Thu 29 Oct 22:00 | +19.2 | closed: hourly exhaustion | +50.0 (take profit) | -30.8 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |
| Thu 05 Nov 18:35 | breakout sell | Thu 05 Nov 20:00 | +8.4 | closed: hourly exhaustion | +50.0 (take profit) | -41.6 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 14:00 | +27.0 | closed: hourly exhaustion | +50.0 (take profit) | -23.0 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 14:00 | +2.6 | closed: hourly exhaustion | -15.0 (stop) | +17.6 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 22:00 | +7.7 | closed: hourly exhaustion | not opened under the current rules |  |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Tue 10 Nov 05:00 | EMA pullback buy | Tue 10 Nov 07:00 | -2.9 | closed: hourly exhaustion | -12.0 (stop) | +9.1 |
| Tue 10 Nov 06:10 | EMA pullback buy | Tue 10 Nov 07:00 | -4.8 | closed: hourly exhaustion | -12.0 (stop) | +7.2 |
| Tue 10 Nov 07:20 | EMA pullback buy | Tue 10 Nov 08:00 | -4.8 | closed: hourly exhaustion | -12.0 (stop) | +7.2 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | +7.7 (closed: hourly exhaustion) |

### 3: 3 of 5 · 50% back · flat < 3

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 15:00 | +17.2 | closed: hourly exhaustion | +50.0 (take profit) | -32.8 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 15:00 | -7.2 | closed: hourly exhaustion | -15.0 (stop) | +7.8 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | -12.0 (stop) |
| Tue 10 Nov 13:10 | breakout sell | opened only with the rule | -12.0 (stop) |
| Tue 10 Nov 09:10 | breakout sell | opened only under the current rules | +50.0 (take profit) |

### 3: 3 of 5 · 50% back · flat < 5

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 15:00 | +17.2 | closed: hourly exhaustion | +50.0 (take profit) | -32.8 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 15:00 | -7.2 | closed: hourly exhaustion | -15.0 (stop) | +7.8 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | -12.0 (stop) |
| Tue 10 Nov 13:10 | breakout sell | opened only with the rule | -12.0 (stop) |
| Tue 10 Nov 09:10 | breakout sell | opened only under the current rules | +50.0 (take profit) |

### 3: 3 of 5 · 50% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 13:00 | -5.9 | closed: hourly exhaustion | +50.0 (take profit) | -55.9 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 15:00 | +17.2 | closed: hourly exhaustion | +50.0 (take profit) | -32.8 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 15:00 | -7.2 | closed: hourly exhaustion | -15.0 (stop) | +7.8 |
| Mon 09 Nov 19:35 | breakout buy | Tue 10 Nov 10:00 | -5.1 | closed: hourly exhaustion | not opened under the current rules |  |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | -5.1 (closed: hourly exhaustion) |
| Tue 10 Nov 11:50 | breakout sell | opened only with the rule | +50.0 (take profit) |
| Tue 10 Nov 09:10 | breakout sell | opened only under the current rules | +50.0 (take profit) |

### 3: 3 of 5 · 75% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 13:00 | -5.9 | closed: hourly exhaustion | +50.0 (take profit) | -55.9 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |

### 3: 4 of 5 · 25% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 13:00 | -5.9 | closed: hourly exhaustion | +50.0 (take profit) | -55.9 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |
| Tue 10 Nov 05:00 | EMA pullback buy | Tue 10 Nov 08:00 | +0.5 | closed: hourly exhaustion | -12.0 (stop) | +12.5 |
| Tue 10 Nov 06:10 | EMA pullback buy | Tue 10 Nov 08:00 | -1.4 | closed: hourly exhaustion | -12.0 (stop) | +10.6 |
| Tue 10 Nov 07:20 | EMA pullback buy | Tue 10 Nov 08:00 | -4.8 | closed: hourly exhaustion | -12.0 (stop) | +7.2 |

### 3: 4 of 5 · 50% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 13:00 | -5.9 | closed: hourly exhaustion | +50.0 (take profit) | -55.9 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |

### 3: 4 of 5 · 75% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 13:00 | -5.9 | closed: hourly exhaustion | +50.0 (take profit) | -55.9 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |

## Every trade closed with all three rules together

The closes made by rules 1 and 3 in each combined run that differs from rules 1 + 2 alone. The bounces held by rule 2 are as in its own list above, apart from the knock-on trades shown.

### 1 (every bounce) + 2 + 3: 2 of 5 · 25% back · flat < 3

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:25 | slow grind sell | Mon 26 Oct 09:05 | +3.5 | closed: bounce opened | +20.0 (take profit) | -16.5 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 26 Oct 14:10 | Bollinger bounce buy | Mon 26 Oct 17:50 | +13.0 | closed: bounce opened | +7.2 (rejection at a level (half at the band +10.0)) | +5.9 |
| Tue 27 Oct 05:45 | slow grind sell | Tue 27 Oct 07:20 | +6.1 | closed: bounce opened | +20.0 (take profit) | -13.9 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 07:20 | +0.6 | closed: bounce opened | +50.0 (take profit) | -49.4 |
| Tue 27 Oct 09:55 | Bollinger bounce buy | Tue 27 Oct 12:35 | +7.1 | closed: bounce opened | -4.6 (rejection at a level) | +11.7 |
| Tue 27 Oct 12:35 | Bollinger bounce sell | Tue 27 Oct 16:40 | +12.8 | closed: bounce opened | +7.0 (rejection at a level (half at the band +8.0)) | +5.8 |
| Tue 27 Oct 16:05 | slow grind sell | Tue 27 Oct 16:40 | -0.6 | closed: bounce opened | +0.0 (scheduled close) | -0.6 |
| Tue 27 Oct 16:15 | EMA pullback sell | Tue 27 Oct 16:40 | -5.3 | closed: bounce opened | -12.0 (stop) | +6.7 |
| Wed 28 Oct 04:45 | slow grind sell | Wed 28 Oct 07:25 | +14.5 | closed: bounce opened | +10.0 (profit lock) | +4.5 |
| Wed 28 Oct 07:25 | Bollinger bounce buy | Wed 28 Oct 13:55 | +13.0 | closed: bounce opened | +11.4 (rejection at a level (half at the band +11.4)) | +1.6 |
| Wed 28 Oct 16:15 | level reversal buy | Wed 28 Oct 17:05 | +3.5 | closed: bounce opened | -1.7 (before big news) | +5.2 |
| Thu 29 Oct 22:05 | EMA pullback buy | Fri 30 Oct 07:45 | +16.8 | closed: bounce opened | +10.9 (scheduled close) | +5.9 |
| Fri 30 Oct 00:40 | EMA pullback buy | Fri 30 Oct 07:45 | +11.5 | closed: bounce opened | +30.0 (take profit) | -18.5 |
| Fri 30 Oct 07:10 | EMA pullback buy | Fri 30 Oct 07:45 | +0.7 | closed: bounce opened | +30.0 (take profit) | -29.3 |
| Fri 30 Oct 07:25 | level reversal buy | Fri 30 Oct 07:45 | -9.9 | closed: bounce opened | +20.0 (take profit) | -29.9 |
| Fri 30 Oct 08:15 | level reversal buy | Fri 30 Oct 10:40 | +11.1 | closed: bounce opened | not opened under the current rules |  |
| Fri 30 Oct 08:15 | slow grind buy | Fri 30 Oct 10:40 | +13.1 | closed: bounce opened | +20.0 (take profit) | -6.9 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 10:40 | Bollinger bounce sell | Fri 30 Oct 15:25 | +16.6 | closed: bounce opened | -1.8 (rejection at a level (half at the band -0.2)) | +18.4 |
| Fri 30 Oct 13:25 | level reversal sell | Fri 30 Oct 15:25 | +0.7 | closed: bounce opened | -4.1 (scheduled close) | +4.8 |
| Fri 30 Oct 15:25 | Bollinger bounce buy | Fri 30 Oct 16:25 | +5.8 | closed: bounce opened | +5.8 (rejection at a level (half at the band +6.5)) | +0.0 |
| Fri 30 Oct 16:15 | level reversal buy | Fri 30 Oct 16:25 | -8.4 | closed: bounce opened | not opened under the current rules |  |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 08:05 | EMA pullback buy | Tue 03 Nov 08:20 | -7.8 | closed: bounce opened | -12.0 (stop) | +4.2 |
| Wed 04 Nov 08:30 | slow grind buy | Wed 04 Nov 10:40 | -6.7 | closed: bounce opened | -15.0 (stop) | +8.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 15:40 | +15.6 | closed: bounce opened | +15.6 (rejection at a level (half at the band +7.6)) | +0.0 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 15:40 | -7.5 | closed: bounce opened | -15.0 (stop) | +7.5 |
| Wed 04 Nov 16:10 | slow grind sell | Wed 04 Nov 17:10 | -5.5 | closed: bounce opened at R2 | not opened under the current rules |  |
| Thu 05 Nov 08:00 | slow grind sell | Thu 05 Nov 08:15 | -10.9 | closed: bounce opened | +9.7 (profit lock) | -20.6 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 15:00 | +17.2 | closed: hourly exhaustion | +50.0 (take profit) | -32.8 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 15:00 | -7.2 | closed: hourly exhaustion | -15.0 (stop) | +7.8 |
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 22:00 | +7.7 | closed: hourly exhaustion | not opened under the current rules |  |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Tue 10 Nov 05:00 | EMA pullback buy | Tue 10 Nov 07:55 | -0.4 | closed: bounce opened | -12.0 (stop) | +11.6 |
| Tue 10 Nov 06:10 | EMA pullback buy | Tue 10 Nov 07:55 | -2.3 | closed: bounce opened | -12.0 (stop) | +9.7 |
| Tue 10 Nov 07:20 | EMA pullback buy | Tue 10 Nov 07:55 | -5.7 | closed: bounce opened | -12.0 (stop) | +6.3 |
| Tue 10 Nov 16:25 | level reversal sell | Tue 10 Nov 17:00 | -1.9 | closed: bounce opened | -20.0 (stop) | +18.1 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Fri 30 Oct 08:15 | level reversal buy | opened only with the rule | +11.1 (closed: bounce opened) |
| Fri 30 Oct 16:15 | level reversal buy | opened only with the rule | -8.4 (closed: bounce opened) |
| Fri 30 Oct 16:45 | level reversal sell | opened only with the rule | -6.0 (scheduled close) |
| Wed 04 Nov 16:10 | slow grind sell | opened only with the rule | -5.5 (closed: bounce opened at R2) |
| Thu 05 Nov 10:20 | slow grind sell | opened only with the rule | -15.0 (stop) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | +7.7 (closed: hourly exhaustion) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (every bounce) + 2 + 3: 2 of 5 · 25% back · flat < 5

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 06:05 | slow grind sell | Mon 26 Oct 07:00 | -2.6 | closed: hourly exhaustion | +10.0 (profit lock) | -12.6 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 26 Oct 14:10 | Bollinger bounce buy | Mon 26 Oct 17:50 | +13.0 | closed: bounce opened | +7.2 (rejection at a level (half at the band +10.0)) | +5.9 |
| Tue 27 Oct 05:45 | slow grind sell | Tue 27 Oct 07:20 | +6.1 | closed: bounce opened | +20.0 (take profit) | -13.9 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 07:20 | +0.6 | closed: bounce opened | +50.0 (take profit) | -49.4 |
| Tue 27 Oct 09:55 | Bollinger bounce buy | Tue 27 Oct 12:35 | +7.1 | closed: bounce opened | -4.6 (rejection at a level) | +11.7 |
| Tue 27 Oct 12:35 | Bollinger bounce sell | Tue 27 Oct 16:40 | +12.8 | closed: bounce opened | +7.0 (rejection at a level (half at the band +8.0)) | +5.8 |
| Tue 27 Oct 16:05 | slow grind sell | Tue 27 Oct 16:40 | -0.6 | closed: bounce opened | +0.0 (scheduled close) | -0.6 |
| Tue 27 Oct 16:15 | EMA pullback sell | Tue 27 Oct 16:40 | -5.3 | closed: bounce opened | -12.0 (stop) | +6.7 |
| Wed 28 Oct 04:45 | slow grind sell | Wed 28 Oct 07:25 | +14.5 | closed: bounce opened | +10.0 (profit lock) | +4.5 |
| Wed 28 Oct 07:25 | Bollinger bounce buy | Wed 28 Oct 13:55 | +13.0 | closed: bounce opened | +11.4 (rejection at a level (half at the band +11.4)) | +1.6 |
| Wed 28 Oct 16:15 | level reversal buy | Wed 28 Oct 17:05 | +3.5 | closed: bounce opened | -1.7 (before big news) | +5.2 |
| Thu 29 Oct 14:45 | breakout buy | Thu 29 Oct 20:00 | +14.8 | closed: hourly exhaustion | +50.0 (take profit) | -35.2 |
| Thu 29 Oct 20:10 | breakout buy | Fri 30 Oct 07:45 | +23.8 | closed: bounce opened | not opened under the current rules |  |
| Thu 29 Oct 22:05 | EMA pullback buy | Fri 30 Oct 07:45 | +16.8 | closed: bounce opened | +10.9 (scheduled close) | +5.9 |
| Fri 30 Oct 00:40 | EMA pullback buy | Fri 30 Oct 07:45 | +11.5 | closed: bounce opened | +30.0 (take profit) | -18.5 |
| Fri 30 Oct 07:10 | EMA pullback buy | Fri 30 Oct 07:45 | +0.7 | closed: bounce opened | +30.0 (take profit) | -29.3 |
| Fri 30 Oct 07:25 | level reversal buy | Fri 30 Oct 07:45 | -9.9 | closed: bounce opened | +20.0 (take profit) | -29.9 |
| Fri 30 Oct 08:15 | level reversal buy | Fri 30 Oct 10:40 | +11.1 | closed: bounce opened | not opened under the current rules |  |
| Fri 30 Oct 08:15 | slow grind buy | Fri 30 Oct 10:40 | +13.1 | closed: bounce opened | +20.0 (take profit) | -6.9 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 10:40 | Bollinger bounce sell | Fri 30 Oct 15:25 | +16.6 | closed: bounce opened | -1.8 (rejection at a level (half at the band -0.2)) | +18.4 |
| Fri 30 Oct 13:25 | level reversal sell | Fri 30 Oct 15:25 | +0.7 | closed: bounce opened | -4.1 (scheduled close) | +4.8 |
| Fri 30 Oct 15:25 | Bollinger bounce buy | Fri 30 Oct 16:25 | +5.8 | closed: bounce opened | +5.8 (rejection at a level (half at the band +6.5)) | +0.0 |
| Fri 30 Oct 16:15 | level reversal buy | Fri 30 Oct 16:25 | -8.4 | closed: bounce opened | not opened under the current rules |  |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 08:05 | EMA pullback buy | Tue 03 Nov 08:20 | -7.8 | closed: bounce opened | -12.0 (stop) | +4.2 |
| Wed 04 Nov 08:30 | slow grind buy | Wed 04 Nov 10:40 | -6.7 | closed: bounce opened | -15.0 (stop) | +8.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 15:40 | +15.6 | closed: bounce opened | +15.6 (rejection at a level (half at the band +7.6)) | +0.0 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 15:40 | -7.5 | closed: bounce opened | -15.0 (stop) | +7.5 |
| Wed 04 Nov 16:10 | slow grind sell | Wed 04 Nov 17:10 | -5.5 | closed: bounce opened at R2 | not opened under the current rules |  |
| Thu 05 Nov 08:00 | slow grind sell | Thu 05 Nov 08:15 | -10.9 | closed: bounce opened | +9.7 (profit lock) | -20.6 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 14:00 | +27.0 | closed: hourly exhaustion | +50.0 (take profit) | -23.0 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 14:00 | +2.6 | closed: hourly exhaustion | -15.0 (stop) | +17.6 |
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 22:00 | +7.7 | closed: hourly exhaustion | not opened under the current rules |  |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Tue 10 Nov 05:00 | EMA pullback buy | Tue 10 Nov 07:55 | -0.4 | closed: bounce opened | -12.0 (stop) | +11.6 |
| Tue 10 Nov 06:10 | EMA pullback buy | Tue 10 Nov 07:55 | -2.3 | closed: bounce opened | -12.0 (stop) | +9.7 |
| Tue 10 Nov 07:20 | EMA pullback buy | Tue 10 Nov 07:55 | -5.7 | closed: bounce opened | -12.0 (stop) | +6.3 |
| Tue 10 Nov 16:25 | level reversal sell | Tue 10 Nov 17:00 | -1.9 | closed: bounce opened | -20.0 (stop) | +18.1 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 07:40 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Thu 29 Oct 20:10 | breakout buy | opened only with the rule | +23.8 (closed: bounce opened) |
| Fri 30 Oct 08:15 | level reversal buy | opened only with the rule | +11.1 (closed: bounce opened) |
| Fri 30 Oct 16:15 | level reversal buy | opened only with the rule | -8.4 (closed: bounce opened) |
| Fri 30 Oct 16:45 | level reversal sell | opened only with the rule | -6.0 (scheduled close) |
| Wed 04 Nov 16:10 | slow grind sell | opened only with the rule | -5.5 (closed: bounce opened at R2) |
| Thu 05 Nov 10:20 | slow grind sell | opened only with the rule | -15.0 (stop) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | +7.7 (closed: hourly exhaustion) |
| Mon 26 Oct 08:25 | slow grind sell | opened only under the current rules | +20.0 (take profit) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (every bounce) + 2 + 3: 2 of 5 · 25% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 06:05 | slow grind sell | Mon 26 Oct 07:00 | -2.6 | closed: hourly exhaustion | +10.0 (profit lock) | -12.6 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 26 Oct 14:10 | Bollinger bounce buy | Mon 26 Oct 17:50 | +13.0 | closed: bounce opened | +7.2 (rejection at a level (half at the band +10.0)) | +5.9 |
| Tue 27 Oct 05:45 | slow grind sell | Tue 27 Oct 07:20 | +6.1 | closed: bounce opened | +20.0 (take profit) | -13.9 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 07:20 | +0.6 | closed: bounce opened | +50.0 (take profit) | -49.4 |
| Tue 27 Oct 09:55 | Bollinger bounce buy | Tue 27 Oct 12:35 | +7.1 | closed: bounce opened | -4.6 (rejection at a level) | +11.7 |
| Tue 27 Oct 12:35 | Bollinger bounce sell | Tue 27 Oct 16:40 | +12.8 | closed: bounce opened | +7.0 (rejection at a level (half at the band +8.0)) | +5.8 |
| Tue 27 Oct 16:05 | slow grind sell | Tue 27 Oct 16:40 | -0.6 | closed: bounce opened | +0.0 (scheduled close) | -0.6 |
| Tue 27 Oct 16:15 | EMA pullback sell | Tue 27 Oct 16:40 | -5.3 | closed: bounce opened | -12.0 (stop) | +6.7 |
| Wed 28 Oct 04:45 | slow grind sell | Wed 28 Oct 07:25 | +14.5 | closed: bounce opened | +10.0 (profit lock) | +4.5 |
| Wed 28 Oct 07:25 | Bollinger bounce buy | Wed 28 Oct 13:55 | +13.0 | closed: bounce opened | +11.4 (rejection at a level (half at the band +11.4)) | +1.6 |
| Wed 28 Oct 16:15 | level reversal buy | Wed 28 Oct 17:05 | +3.5 | closed: bounce opened | -1.7 (before big news) | +5.2 |
| Thu 29 Oct 14:45 | breakout buy | Thu 29 Oct 20:00 | +14.8 | closed: hourly exhaustion | +50.0 (take profit) | -35.2 |
| Thu 29 Oct 20:10 | breakout buy | Thu 29 Oct 22:00 | -8.0 | closed: hourly exhaustion | not opened under the current rules |  |
| Thu 29 Oct 22:05 | EMA pullback buy | Fri 30 Oct 00:00 | -6.7 | closed: hourly exhaustion | +10.9 (scheduled close) | -17.6 |
| Fri 30 Oct 00:40 | EMA pullback buy | Fri 30 Oct 07:45 | +11.5 | closed: bounce opened | +30.0 (take profit) | -18.5 |
| Fri 30 Oct 07:10 | EMA pullback buy | Fri 30 Oct 07:45 | +0.7 | closed: bounce opened | +30.0 (take profit) | -29.3 |
| Fri 30 Oct 07:25 | level reversal buy | Fri 30 Oct 07:45 | -9.9 | closed: bounce opened | +20.0 (take profit) | -29.9 |
| Fri 30 Oct 08:15 | level reversal buy | Fri 30 Oct 10:40 | +11.1 | closed: bounce opened | not opened under the current rules |  |
| Fri 30 Oct 08:15 | slow grind buy | Fri 30 Oct 10:40 | +13.1 | closed: bounce opened | +20.0 (take profit) | -6.9 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 10:40 | Bollinger bounce sell | Fri 30 Oct 15:25 | +16.6 | closed: bounce opened | -1.8 (rejection at a level (half at the band -0.2)) | +18.4 |
| Fri 30 Oct 13:25 | level reversal sell | Fri 30 Oct 15:25 | +0.7 | closed: bounce opened | -4.1 (scheduled close) | +4.8 |
| Fri 30 Oct 15:25 | Bollinger bounce buy | Fri 30 Oct 16:25 | +5.8 | closed: bounce opened | +5.8 (rejection at a level (half at the band +6.5)) | +0.0 |
| Fri 30 Oct 16:15 | level reversal buy | Fri 30 Oct 16:25 | -8.4 | closed: bounce opened | not opened under the current rules |  |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 08:05 | EMA pullback buy | Tue 03 Nov 08:20 | -7.8 | closed: bounce opened | -12.0 (stop) | +4.2 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |
| Tue 03 Nov 18:05 | EMA pullback buy | Tue 03 Nov 19:00 | -2.9 | closed: hourly exhaustion | -12.0 (stop) | +9.1 |
| Tue 03 Nov 18:05 | EMA pullback buy | Tue 03 Nov 19:00 | -2.9 | closed: hourly exhaustion | -12.0 (stop) | +9.1 |
| Tue 03 Nov 18:05 | breakout buy | Tue 03 Nov 19:00 | -1.6 | closed: hourly exhaustion | -12.0 (stop) | +10.4 |
| Wed 04 Nov 08:30 | slow grind buy | Wed 04 Nov 10:40 | -6.7 | closed: bounce opened | -15.0 (stop) | +8.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 15:40 | +15.6 | closed: bounce opened | +15.6 (rejection at a level (half at the band +7.6)) | +0.0 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 15:40 | -7.5 | closed: bounce opened | -15.0 (stop) | +7.5 |
| Wed 04 Nov 16:10 | slow grind sell | Wed 04 Nov 17:10 | -5.5 | closed: bounce opened at R2 | not opened under the current rules |  |
| Thu 05 Nov 08:00 | slow grind sell | Thu 05 Nov 08:15 | -10.9 | closed: bounce opened | +9.7 (profit lock) | -20.6 |
| Thu 05 Nov 18:35 | breakout sell | Thu 05 Nov 20:00 | +8.4 | closed: hourly exhaustion | +50.0 (take profit) | -41.6 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 14:00 | +27.0 | closed: hourly exhaustion | +50.0 (take profit) | -23.0 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 14:00 | +2.6 | closed: hourly exhaustion | -15.0 (stop) | +17.6 |
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 22:00 | +7.7 | closed: hourly exhaustion | not opened under the current rules |  |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Tue 10 Nov 05:00 | EMA pullback buy | Tue 10 Nov 06:00 | -5.8 | closed: hourly exhaustion | -12.0 (stop) | +6.2 |
| Tue 10 Nov 06:10 | EMA pullback buy | Tue 10 Nov 07:00 | -4.8 | closed: hourly exhaustion | -12.0 (stop) | +7.2 |
| Tue 10 Nov 07:20 | EMA pullback buy | Tue 10 Nov 07:55 | -5.7 | closed: bounce opened | -12.0 (stop) | +6.3 |
| Tue 10 Nov 09:10 | breakout sell | Tue 10 Nov 12:00 | +6.3 | closed: hourly exhaustion | +50.0 (take profit) | -43.7 |
| Tue 10 Nov 16:25 | level reversal sell | Tue 10 Nov 17:00 | -1.9 | closed: bounce opened | -20.0 (stop) | +18.1 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 07:40 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Thu 29 Oct 20:10 | breakout buy | opened only with the rule | -8.0 (closed: hourly exhaustion) |
| Fri 30 Oct 08:15 | level reversal buy | opened only with the rule | +11.1 (closed: bounce opened) |
| Fri 30 Oct 16:15 | level reversal buy | opened only with the rule | -8.4 (closed: bounce opened) |
| Fri 30 Oct 16:45 | level reversal sell | opened only with the rule | -6.0 (scheduled close) |
| Wed 04 Nov 16:10 | slow grind sell | opened only with the rule | -5.5 (closed: bounce opened at R2) |
| Thu 05 Nov 10:20 | slow grind sell | opened only with the rule | -15.0 (stop) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | +7.7 (closed: hourly exhaustion) |
| Tue 10 Nov 13:10 | breakout sell | opened only with the rule | -12.0 (stop) |
| Mon 26 Oct 08:25 | slow grind sell | opened only under the current rules | +20.0 (take profit) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (every bounce) + 2 + 3: 2 of 5 · 50% back · flat < 3

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:25 | slow grind sell | Mon 26 Oct 09:05 | +3.5 | closed: bounce opened | +20.0 (take profit) | -16.5 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 26 Oct 14:10 | Bollinger bounce buy | Mon 26 Oct 17:50 | +13.0 | closed: bounce opened | +7.2 (rejection at a level (half at the band +10.0)) | +5.9 |
| Tue 27 Oct 05:45 | slow grind sell | Tue 27 Oct 07:20 | +6.1 | closed: bounce opened | +20.0 (take profit) | -13.9 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 07:20 | +0.6 | closed: bounce opened | +50.0 (take profit) | -49.4 |
| Tue 27 Oct 09:55 | Bollinger bounce buy | Tue 27 Oct 12:35 | +7.1 | closed: bounce opened | -4.6 (rejection at a level) | +11.7 |
| Tue 27 Oct 12:35 | Bollinger bounce sell | Tue 27 Oct 16:40 | +12.8 | closed: bounce opened | +7.0 (rejection at a level (half at the band +8.0)) | +5.8 |
| Tue 27 Oct 16:05 | slow grind sell | Tue 27 Oct 16:40 | -0.6 | closed: bounce opened | +0.0 (scheduled close) | -0.6 |
| Tue 27 Oct 16:15 | EMA pullback sell | Tue 27 Oct 16:40 | -5.3 | closed: bounce opened | -12.0 (stop) | +6.7 |
| Wed 28 Oct 04:45 | slow grind sell | Wed 28 Oct 07:25 | +14.5 | closed: bounce opened | +10.0 (profit lock) | +4.5 |
| Wed 28 Oct 07:25 | Bollinger bounce buy | Wed 28 Oct 13:55 | +13.0 | closed: bounce opened | +11.4 (rejection at a level (half at the band +11.4)) | +1.6 |
| Wed 28 Oct 16:15 | level reversal buy | Wed 28 Oct 17:05 | +3.5 | closed: bounce opened | -1.7 (before big news) | +5.2 |
| Thu 29 Oct 22:05 | EMA pullback buy | Fri 30 Oct 07:45 | +16.8 | closed: bounce opened | +10.9 (scheduled close) | +5.9 |
| Fri 30 Oct 00:40 | EMA pullback buy | Fri 30 Oct 07:45 | +11.5 | closed: bounce opened | +30.0 (take profit) | -18.5 |
| Fri 30 Oct 07:10 | EMA pullback buy | Fri 30 Oct 07:45 | +0.7 | closed: bounce opened | +30.0 (take profit) | -29.3 |
| Fri 30 Oct 07:25 | level reversal buy | Fri 30 Oct 07:45 | -9.9 | closed: bounce opened | +20.0 (take profit) | -29.9 |
| Fri 30 Oct 08:15 | level reversal buy | Fri 30 Oct 10:40 | +11.1 | closed: bounce opened | not opened under the current rules |  |
| Fri 30 Oct 08:15 | slow grind buy | Fri 30 Oct 10:40 | +13.1 | closed: bounce opened | +20.0 (take profit) | -6.9 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 10:40 | Bollinger bounce sell | Fri 30 Oct 15:25 | +16.6 | closed: bounce opened | -1.8 (rejection at a level (half at the band -0.2)) | +18.4 |
| Fri 30 Oct 13:25 | level reversal sell | Fri 30 Oct 15:25 | +0.7 | closed: bounce opened | -4.1 (scheduled close) | +4.8 |
| Fri 30 Oct 15:25 | Bollinger bounce buy | Fri 30 Oct 16:25 | +5.8 | closed: bounce opened | +5.8 (rejection at a level (half at the band +6.5)) | +0.0 |
| Fri 30 Oct 16:15 | level reversal buy | Fri 30 Oct 16:25 | -8.4 | closed: bounce opened | not opened under the current rules |  |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 08:05 | EMA pullback buy | Tue 03 Nov 08:20 | -7.8 | closed: bounce opened | -12.0 (stop) | +4.2 |
| Wed 04 Nov 08:30 | slow grind buy | Wed 04 Nov 10:40 | -6.7 | closed: bounce opened | -15.0 (stop) | +8.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 15:40 | +15.6 | closed: bounce opened | +15.6 (rejection at a level (half at the band +7.6)) | +0.0 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 15:40 | -7.5 | closed: bounce opened | -15.0 (stop) | +7.5 |
| Wed 04 Nov 16:10 | slow grind sell | Wed 04 Nov 17:10 | -5.5 | closed: bounce opened at R2 | not opened under the current rules |  |
| Thu 05 Nov 08:00 | slow grind sell | Thu 05 Nov 08:15 | -10.9 | closed: bounce opened | +9.7 (profit lock) | -20.6 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 15:00 | +17.2 | closed: hourly exhaustion | +50.0 (take profit) | -32.8 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 15:00 | -7.2 | closed: hourly exhaustion | -15.0 (stop) | +7.8 |
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 23:00 | -2.8 | closed: hourly exhaustion | not opened under the current rules |  |
| Tue 10 Nov 05:00 | EMA pullback buy | Tue 10 Nov 07:55 | -0.4 | closed: bounce opened | -12.0 (stop) | +11.6 |
| Tue 10 Nov 06:10 | EMA pullback buy | Tue 10 Nov 07:55 | -2.3 | closed: bounce opened | -12.0 (stop) | +9.7 |
| Tue 10 Nov 07:20 | EMA pullback buy | Tue 10 Nov 07:55 | -5.7 | closed: bounce opened | -12.0 (stop) | +6.3 |
| Tue 10 Nov 16:25 | level reversal sell | Tue 10 Nov 17:00 | -1.9 | closed: bounce opened | -20.0 (stop) | +18.1 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Fri 30 Oct 08:15 | level reversal buy | opened only with the rule | +11.1 (closed: bounce opened) |
| Fri 30 Oct 16:15 | level reversal buy | opened only with the rule | -8.4 (closed: bounce opened) |
| Fri 30 Oct 16:45 | level reversal sell | opened only with the rule | -6.0 (scheduled close) |
| Wed 04 Nov 16:10 | slow grind sell | opened only with the rule | -5.5 (closed: bounce opened at R2) |
| Thu 05 Nov 10:20 | slow grind sell | opened only with the rule | -15.0 (stop) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | -2.8 (closed: hourly exhaustion) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (every bounce) + 2 + 3: 2 of 5 · 50% back · flat < 5

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 06:05 | slow grind sell | Mon 26 Oct 07:00 | -2.6 | closed: hourly exhaustion | +10.0 (profit lock) | -12.6 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 26 Oct 14:10 | Bollinger bounce buy | Mon 26 Oct 17:50 | +13.0 | closed: bounce opened | +7.2 (rejection at a level (half at the band +10.0)) | +5.9 |
| Tue 27 Oct 05:45 | slow grind sell | Tue 27 Oct 07:20 | +6.1 | closed: bounce opened | +20.0 (take profit) | -13.9 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 07:20 | +0.6 | closed: bounce opened | +50.0 (take profit) | -49.4 |
| Tue 27 Oct 09:55 | Bollinger bounce buy | Tue 27 Oct 12:35 | +7.1 | closed: bounce opened | -4.6 (rejection at a level) | +11.7 |
| Tue 27 Oct 12:35 | Bollinger bounce sell | Tue 27 Oct 16:40 | +12.8 | closed: bounce opened | +7.0 (rejection at a level (half at the band +8.0)) | +5.8 |
| Tue 27 Oct 16:05 | slow grind sell | Tue 27 Oct 16:40 | -0.6 | closed: bounce opened | +0.0 (scheduled close) | -0.6 |
| Tue 27 Oct 16:15 | EMA pullback sell | Tue 27 Oct 16:40 | -5.3 | closed: bounce opened | -12.0 (stop) | +6.7 |
| Wed 28 Oct 04:45 | slow grind sell | Wed 28 Oct 07:25 | +14.5 | closed: bounce opened | +10.0 (profit lock) | +4.5 |
| Wed 28 Oct 07:25 | Bollinger bounce buy | Wed 28 Oct 13:55 | +13.0 | closed: bounce opened | +11.4 (rejection at a level (half at the band +11.4)) | +1.6 |
| Wed 28 Oct 16:15 | level reversal buy | Wed 28 Oct 17:05 | +3.5 | closed: bounce opened | -1.7 (before big news) | +5.2 |
| Thu 29 Oct 22:05 | EMA pullback buy | Fri 30 Oct 07:45 | +16.8 | closed: bounce opened | +10.9 (scheduled close) | +5.9 |
| Fri 30 Oct 00:40 | EMA pullback buy | Fri 30 Oct 07:45 | +11.5 | closed: bounce opened | +30.0 (take profit) | -18.5 |
| Fri 30 Oct 07:10 | EMA pullback buy | Fri 30 Oct 07:45 | +0.7 | closed: bounce opened | +30.0 (take profit) | -29.3 |
| Fri 30 Oct 07:25 | level reversal buy | Fri 30 Oct 07:45 | -9.9 | closed: bounce opened | +20.0 (take profit) | -29.9 |
| Fri 30 Oct 08:15 | level reversal buy | Fri 30 Oct 10:40 | +11.1 | closed: bounce opened | not opened under the current rules |  |
| Fri 30 Oct 08:15 | slow grind buy | Fri 30 Oct 10:40 | +13.1 | closed: bounce opened | +20.0 (take profit) | -6.9 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 10:40 | Bollinger bounce sell | Fri 30 Oct 15:25 | +16.6 | closed: bounce opened | -1.8 (rejection at a level (half at the band -0.2)) | +18.4 |
| Fri 30 Oct 13:25 | level reversal sell | Fri 30 Oct 15:25 | +0.7 | closed: bounce opened | -4.1 (scheduled close) | +4.8 |
| Fri 30 Oct 15:25 | Bollinger bounce buy | Fri 30 Oct 16:25 | +5.8 | closed: bounce opened | +5.8 (rejection at a level (half at the band +6.5)) | +0.0 |
| Fri 30 Oct 16:15 | level reversal buy | Fri 30 Oct 16:25 | -8.4 | closed: bounce opened | not opened under the current rules |  |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 08:05 | EMA pullback buy | Tue 03 Nov 08:20 | -7.8 | closed: bounce opened | -12.0 (stop) | +4.2 |
| Wed 04 Nov 08:30 | slow grind buy | Wed 04 Nov 10:40 | -6.7 | closed: bounce opened | -15.0 (stop) | +8.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 15:40 | +15.6 | closed: bounce opened | +15.6 (rejection at a level (half at the band +7.6)) | +0.0 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 15:40 | -7.5 | closed: bounce opened | -15.0 (stop) | +7.5 |
| Wed 04 Nov 16:10 | slow grind sell | Wed 04 Nov 17:10 | -5.5 | closed: bounce opened at R2 | not opened under the current rules |  |
| Thu 05 Nov 08:00 | slow grind sell | Thu 05 Nov 08:15 | -10.9 | closed: bounce opened | +9.7 (profit lock) | -20.6 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 15:00 | +17.2 | closed: hourly exhaustion | +50.0 (take profit) | -32.8 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 15:00 | -7.2 | closed: hourly exhaustion | -15.0 (stop) | +7.8 |
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 23:00 | -2.8 | closed: hourly exhaustion | not opened under the current rules |  |
| Tue 10 Nov 05:00 | EMA pullback buy | Tue 10 Nov 07:55 | -0.4 | closed: bounce opened | -12.0 (stop) | +11.6 |
| Tue 10 Nov 06:10 | EMA pullback buy | Tue 10 Nov 07:55 | -2.3 | closed: bounce opened | -12.0 (stop) | +9.7 |
| Tue 10 Nov 07:20 | EMA pullback buy | Tue 10 Nov 07:55 | -5.7 | closed: bounce opened | -12.0 (stop) | +6.3 |
| Tue 10 Nov 16:25 | level reversal sell | Tue 10 Nov 17:00 | -1.9 | closed: bounce opened | -20.0 (stop) | +18.1 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 07:40 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Fri 30 Oct 08:15 | level reversal buy | opened only with the rule | +11.1 (closed: bounce opened) |
| Fri 30 Oct 16:15 | level reversal buy | opened only with the rule | -8.4 (closed: bounce opened) |
| Fri 30 Oct 16:45 | level reversal sell | opened only with the rule | -6.0 (scheduled close) |
| Wed 04 Nov 16:10 | slow grind sell | opened only with the rule | -5.5 (closed: bounce opened at R2) |
| Thu 05 Nov 10:20 | slow grind sell | opened only with the rule | -15.0 (stop) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | -2.8 (closed: hourly exhaustion) |
| Mon 26 Oct 08:25 | slow grind sell | opened only under the current rules | +20.0 (take profit) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (every bounce) + 2 + 3: 2 of 5 · 50% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 06:05 | slow grind sell | Mon 26 Oct 07:00 | -2.6 | closed: hourly exhaustion | +10.0 (profit lock) | -12.6 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 26 Oct 14:10 | Bollinger bounce buy | Mon 26 Oct 17:50 | +13.0 | closed: bounce opened | +7.2 (rejection at a level (half at the band +10.0)) | +5.9 |
| Tue 27 Oct 05:45 | slow grind sell | Tue 27 Oct 07:20 | +6.1 | closed: bounce opened | +20.0 (take profit) | -13.9 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 07:20 | +0.6 | closed: bounce opened | +50.0 (take profit) | -49.4 |
| Tue 27 Oct 09:55 | Bollinger bounce buy | Tue 27 Oct 12:35 | +7.1 | closed: bounce opened | -4.6 (rejection at a level) | +11.7 |
| Tue 27 Oct 12:35 | Bollinger bounce sell | Tue 27 Oct 16:40 | +12.8 | closed: bounce opened | +7.0 (rejection at a level (half at the band +8.0)) | +5.8 |
| Tue 27 Oct 16:05 | slow grind sell | Tue 27 Oct 16:40 | -0.6 | closed: bounce opened | +0.0 (scheduled close) | -0.6 |
| Tue 27 Oct 16:15 | EMA pullback sell | Tue 27 Oct 16:40 | -5.3 | closed: bounce opened | -12.0 (stop) | +6.7 |
| Wed 28 Oct 04:45 | slow grind sell | Wed 28 Oct 07:25 | +14.5 | closed: bounce opened | +10.0 (profit lock) | +4.5 |
| Wed 28 Oct 07:25 | Bollinger bounce buy | Wed 28 Oct 13:55 | +13.0 | closed: bounce opened | +11.4 (rejection at a level (half at the band +11.4)) | +1.6 |
| Wed 28 Oct 16:15 | level reversal buy | Wed 28 Oct 17:05 | +3.5 | closed: bounce opened | -1.7 (before big news) | +5.2 |
| Thu 29 Oct 22:05 | EMA pullback buy | Fri 30 Oct 07:45 | +16.8 | closed: bounce opened | +10.9 (scheduled close) | +5.9 |
| Fri 30 Oct 00:40 | EMA pullback buy | Fri 30 Oct 07:45 | +11.5 | closed: bounce opened | +30.0 (take profit) | -18.5 |
| Fri 30 Oct 07:10 | EMA pullback buy | Fri 30 Oct 07:45 | +0.7 | closed: bounce opened | +30.0 (take profit) | -29.3 |
| Fri 30 Oct 07:25 | level reversal buy | Fri 30 Oct 07:45 | -9.9 | closed: bounce opened | +20.0 (take profit) | -29.9 |
| Fri 30 Oct 08:15 | level reversal buy | Fri 30 Oct 10:40 | +11.1 | closed: bounce opened | not opened under the current rules |  |
| Fri 30 Oct 08:15 | slow grind buy | Fri 30 Oct 10:40 | +13.1 | closed: bounce opened | +20.0 (take profit) | -6.9 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 10:40 | Bollinger bounce sell | Fri 30 Oct 15:25 | +16.6 | closed: bounce opened | -1.8 (rejection at a level (half at the band -0.2)) | +18.4 |
| Fri 30 Oct 13:25 | level reversal sell | Fri 30 Oct 15:25 | +0.7 | closed: bounce opened | -4.1 (scheduled close) | +4.8 |
| Fri 30 Oct 15:25 | Bollinger bounce buy | Fri 30 Oct 16:25 | +5.8 | closed: bounce opened | +5.8 (rejection at a level (half at the band +6.5)) | +0.0 |
| Fri 30 Oct 16:15 | level reversal buy | Fri 30 Oct 16:25 | -8.4 | closed: bounce opened | not opened under the current rules |  |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 08:05 | EMA pullback buy | Tue 03 Nov 08:20 | -7.8 | closed: bounce opened | -12.0 (stop) | +4.2 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |
| Wed 04 Nov 08:30 | slow grind buy | Wed 04 Nov 10:40 | -6.7 | closed: bounce opened | -15.0 (stop) | +8.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 15:40 | +15.6 | closed: bounce opened | +15.6 (rejection at a level (half at the band +7.6)) | +0.0 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 15:40 | -7.5 | closed: bounce opened | -15.0 (stop) | +7.5 |
| Wed 04 Nov 16:10 | slow grind sell | Wed 04 Nov 17:10 | -5.5 | closed: bounce opened at R2 | not opened under the current rules |  |
| Thu 05 Nov 08:00 | slow grind sell | Thu 05 Nov 08:15 | -10.9 | closed: bounce opened | +9.7 (profit lock) | -20.6 |
| Thu 05 Nov 18:35 | breakout sell | Fri 06 Nov 00:00 | +12.2 | closed: hourly exhaustion | +50.0 (take profit) | -37.8 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 15:00 | +17.2 | closed: hourly exhaustion | +50.0 (take profit) | -32.8 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 15:00 | -7.2 | closed: hourly exhaustion | -15.0 (stop) | +7.8 |
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 23:00 | -2.8 | closed: hourly exhaustion | not opened under the current rules |  |
| Tue 10 Nov 05:00 | EMA pullback buy | Tue 10 Nov 07:55 | -0.4 | closed: bounce opened | -12.0 (stop) | +11.6 |
| Tue 10 Nov 06:10 | EMA pullback buy | Tue 10 Nov 07:55 | -2.3 | closed: bounce opened | -12.0 (stop) | +9.7 |
| Tue 10 Nov 07:20 | EMA pullback buy | Tue 10 Nov 07:55 | -5.7 | closed: bounce opened | -12.0 (stop) | +6.3 |
| Tue 10 Nov 16:25 | level reversal sell | Tue 10 Nov 17:00 | -1.9 | closed: bounce opened | -20.0 (stop) | +18.1 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 07:40 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Fri 30 Oct 08:15 | level reversal buy | opened only with the rule | +11.1 (closed: bounce opened) |
| Fri 30 Oct 16:15 | level reversal buy | opened only with the rule | -8.4 (closed: bounce opened) |
| Fri 30 Oct 16:45 | level reversal sell | opened only with the rule | -6.0 (scheduled close) |
| Wed 04 Nov 16:10 | slow grind sell | opened only with the rule | -5.5 (closed: bounce opened at R2) |
| Thu 05 Nov 10:20 | slow grind sell | opened only with the rule | -15.0 (stop) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | -2.8 (closed: hourly exhaustion) |
| Mon 26 Oct 08:25 | slow grind sell | opened only under the current rules | +20.0 (take profit) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (every bounce) + 2 + 3: 2 of 5 · 75% back · flat < 3

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:25 | slow grind sell | Mon 26 Oct 09:05 | +3.5 | closed: bounce opened | +20.0 (take profit) | -16.5 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 26 Oct 14:10 | Bollinger bounce buy | Mon 26 Oct 17:50 | +13.0 | closed: bounce opened | +7.2 (rejection at a level (half at the band +10.0)) | +5.9 |
| Tue 27 Oct 05:45 | slow grind sell | Tue 27 Oct 07:20 | +6.1 | closed: bounce opened | +20.0 (take profit) | -13.9 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 07:20 | +0.6 | closed: bounce opened | +50.0 (take profit) | -49.4 |
| Tue 27 Oct 09:55 | Bollinger bounce buy | Tue 27 Oct 12:35 | +7.1 | closed: bounce opened | -4.6 (rejection at a level) | +11.7 |
| Tue 27 Oct 12:35 | Bollinger bounce sell | Tue 27 Oct 16:40 | +12.8 | closed: bounce opened | +7.0 (rejection at a level (half at the band +8.0)) | +5.8 |
| Tue 27 Oct 16:05 | slow grind sell | Tue 27 Oct 16:40 | -0.6 | closed: bounce opened | +0.0 (scheduled close) | -0.6 |
| Tue 27 Oct 16:15 | EMA pullback sell | Tue 27 Oct 16:40 | -5.3 | closed: bounce opened | -12.0 (stop) | +6.7 |
| Wed 28 Oct 04:45 | slow grind sell | Wed 28 Oct 07:25 | +14.5 | closed: bounce opened | +10.0 (profit lock) | +4.5 |
| Wed 28 Oct 07:25 | Bollinger bounce buy | Wed 28 Oct 13:55 | +13.0 | closed: bounce opened | +11.4 (rejection at a level (half at the band +11.4)) | +1.6 |
| Wed 28 Oct 16:15 | level reversal buy | Wed 28 Oct 17:05 | +3.5 | closed: bounce opened | -1.7 (before big news) | +5.2 |
| Thu 29 Oct 22:05 | EMA pullback buy | Fri 30 Oct 07:45 | +16.8 | closed: bounce opened | +10.9 (scheduled close) | +5.9 |
| Fri 30 Oct 00:40 | EMA pullback buy | Fri 30 Oct 07:45 | +11.5 | closed: bounce opened | +30.0 (take profit) | -18.5 |
| Fri 30 Oct 07:10 | EMA pullback buy | Fri 30 Oct 07:45 | +0.7 | closed: bounce opened | +30.0 (take profit) | -29.3 |
| Fri 30 Oct 07:25 | level reversal buy | Fri 30 Oct 07:45 | -9.9 | closed: bounce opened | +20.0 (take profit) | -29.9 |
| Fri 30 Oct 08:15 | level reversal buy | Fri 30 Oct 10:40 | +11.1 | closed: bounce opened | not opened under the current rules |  |
| Fri 30 Oct 08:15 | slow grind buy | Fri 30 Oct 10:40 | +13.1 | closed: bounce opened | +20.0 (take profit) | -6.9 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 10:40 | Bollinger bounce sell | Fri 30 Oct 15:25 | +16.6 | closed: bounce opened | -1.8 (rejection at a level (half at the band -0.2)) | +18.4 |
| Fri 30 Oct 13:25 | level reversal sell | Fri 30 Oct 15:25 | +0.7 | closed: bounce opened | -4.1 (scheduled close) | +4.8 |
| Fri 30 Oct 15:25 | Bollinger bounce buy | Fri 30 Oct 16:25 | +5.8 | closed: bounce opened | +5.8 (rejection at a level (half at the band +6.5)) | +0.0 |
| Fri 30 Oct 16:15 | level reversal buy | Fri 30 Oct 16:25 | -8.4 | closed: bounce opened | not opened under the current rules |  |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 08:05 | EMA pullback buy | Tue 03 Nov 08:20 | -7.8 | closed: bounce opened | -12.0 (stop) | +4.2 |
| Wed 04 Nov 08:30 | slow grind buy | Wed 04 Nov 10:40 | -6.7 | closed: bounce opened | -15.0 (stop) | +8.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 15:40 | +15.6 | closed: bounce opened | +15.6 (rejection at a level (half at the band +7.6)) | +0.0 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 15:40 | -7.5 | closed: bounce opened | -15.0 (stop) | +7.5 |
| Wed 04 Nov 16:10 | slow grind sell | Wed 04 Nov 17:10 | -5.5 | closed: bounce opened at R2 | not opened under the current rules |  |
| Thu 05 Nov 08:00 | slow grind sell | Thu 05 Nov 08:15 | -10.9 | closed: bounce opened | +9.7 (profit lock) | -20.6 |
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |
| Tue 10 Nov 05:00 | EMA pullback buy | Tue 10 Nov 07:55 | -0.4 | closed: bounce opened | -12.0 (stop) | +11.6 |
| Tue 10 Nov 06:10 | EMA pullback buy | Tue 10 Nov 07:55 | -2.3 | closed: bounce opened | -12.0 (stop) | +9.7 |
| Tue 10 Nov 07:20 | EMA pullback buy | Tue 10 Nov 07:55 | -5.7 | closed: bounce opened | -12.0 (stop) | +6.3 |
| Tue 10 Nov 16:25 | level reversal sell | Tue 10 Nov 17:00 | -1.9 | closed: bounce opened | -20.0 (stop) | +18.1 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Fri 30 Oct 08:15 | level reversal buy | opened only with the rule | +11.1 (closed: bounce opened) |
| Fri 30 Oct 16:15 | level reversal buy | opened only with the rule | -8.4 (closed: bounce opened) |
| Fri 30 Oct 16:45 | level reversal sell | opened only with the rule | -6.0 (scheduled close) |
| Wed 04 Nov 16:10 | slow grind sell | opened only with the rule | -5.5 (closed: bounce opened at R2) |
| Thu 05 Nov 10:20 | slow grind sell | opened only with the rule | -15.0 (stop) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (every bounce) + 2 + 3: 2 of 5 · 75% back · flat < 5

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 06:05 | slow grind sell | Mon 26 Oct 07:00 | -2.6 | closed: hourly exhaustion | +10.0 (profit lock) | -12.6 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 26 Oct 14:10 | Bollinger bounce buy | Mon 26 Oct 17:50 | +13.0 | closed: bounce opened | +7.2 (rejection at a level (half at the band +10.0)) | +5.9 |
| Tue 27 Oct 05:45 | slow grind sell | Tue 27 Oct 07:20 | +6.1 | closed: bounce opened | +20.0 (take profit) | -13.9 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 07:20 | +0.6 | closed: bounce opened | +50.0 (take profit) | -49.4 |
| Tue 27 Oct 09:55 | Bollinger bounce buy | Tue 27 Oct 12:35 | +7.1 | closed: bounce opened | -4.6 (rejection at a level) | +11.7 |
| Tue 27 Oct 12:35 | Bollinger bounce sell | Tue 27 Oct 16:40 | +12.8 | closed: bounce opened | +7.0 (rejection at a level (half at the band +8.0)) | +5.8 |
| Tue 27 Oct 16:05 | slow grind sell | Tue 27 Oct 16:40 | -0.6 | closed: bounce opened | +0.0 (scheduled close) | -0.6 |
| Tue 27 Oct 16:15 | EMA pullback sell | Tue 27 Oct 16:40 | -5.3 | closed: bounce opened | -12.0 (stop) | +6.7 |
| Wed 28 Oct 04:45 | slow grind sell | Wed 28 Oct 07:25 | +14.5 | closed: bounce opened | +10.0 (profit lock) | +4.5 |
| Wed 28 Oct 07:25 | Bollinger bounce buy | Wed 28 Oct 13:55 | +13.0 | closed: bounce opened | +11.4 (rejection at a level (half at the band +11.4)) | +1.6 |
| Wed 28 Oct 16:15 | level reversal buy | Wed 28 Oct 17:05 | +3.5 | closed: bounce opened | -1.7 (before big news) | +5.2 |
| Thu 29 Oct 22:05 | EMA pullback buy | Fri 30 Oct 07:45 | +16.8 | closed: bounce opened | +10.9 (scheduled close) | +5.9 |
| Fri 30 Oct 00:40 | EMA pullback buy | Fri 30 Oct 07:45 | +11.5 | closed: bounce opened | +30.0 (take profit) | -18.5 |
| Fri 30 Oct 07:10 | EMA pullback buy | Fri 30 Oct 07:45 | +0.7 | closed: bounce opened | +30.0 (take profit) | -29.3 |
| Fri 30 Oct 07:25 | level reversal buy | Fri 30 Oct 07:45 | -9.9 | closed: bounce opened | +20.0 (take profit) | -29.9 |
| Fri 30 Oct 08:15 | level reversal buy | Fri 30 Oct 10:40 | +11.1 | closed: bounce opened | not opened under the current rules |  |
| Fri 30 Oct 08:15 | slow grind buy | Fri 30 Oct 10:40 | +13.1 | closed: bounce opened | +20.0 (take profit) | -6.9 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 10:40 | Bollinger bounce sell | Fri 30 Oct 15:25 | +16.6 | closed: bounce opened | -1.8 (rejection at a level (half at the band -0.2)) | +18.4 |
| Fri 30 Oct 13:25 | level reversal sell | Fri 30 Oct 15:25 | +0.7 | closed: bounce opened | -4.1 (scheduled close) | +4.8 |
| Fri 30 Oct 15:25 | Bollinger bounce buy | Fri 30 Oct 16:25 | +5.8 | closed: bounce opened | +5.8 (rejection at a level (half at the band +6.5)) | +0.0 |
| Fri 30 Oct 16:15 | level reversal buy | Fri 30 Oct 16:25 | -8.4 | closed: bounce opened | not opened under the current rules |  |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 08:05 | EMA pullback buy | Tue 03 Nov 08:20 | -7.8 | closed: bounce opened | -12.0 (stop) | +4.2 |
| Wed 04 Nov 08:30 | slow grind buy | Wed 04 Nov 10:40 | -6.7 | closed: bounce opened | -15.0 (stop) | +8.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 15:40 | +15.6 | closed: bounce opened | +15.6 (rejection at a level (half at the band +7.6)) | +0.0 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 15:40 | -7.5 | closed: bounce opened | -15.0 (stop) | +7.5 |
| Wed 04 Nov 16:10 | slow grind sell | Wed 04 Nov 17:10 | -5.5 | closed: bounce opened at R2 | not opened under the current rules |  |
| Thu 05 Nov 08:00 | slow grind sell | Thu 05 Nov 08:15 | -10.9 | closed: bounce opened | +9.7 (profit lock) | -20.6 |
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |
| Tue 10 Nov 05:00 | EMA pullback buy | Tue 10 Nov 07:55 | -0.4 | closed: bounce opened | -12.0 (stop) | +11.6 |
| Tue 10 Nov 06:10 | EMA pullback buy | Tue 10 Nov 07:55 | -2.3 | closed: bounce opened | -12.0 (stop) | +9.7 |
| Tue 10 Nov 07:20 | EMA pullback buy | Tue 10 Nov 07:55 | -5.7 | closed: bounce opened | -12.0 (stop) | +6.3 |
| Tue 10 Nov 16:25 | level reversal sell | Tue 10 Nov 17:00 | -1.9 | closed: bounce opened | -20.0 (stop) | +18.1 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 07:40 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Fri 30 Oct 08:15 | level reversal buy | opened only with the rule | +11.1 (closed: bounce opened) |
| Fri 30 Oct 16:15 | level reversal buy | opened only with the rule | -8.4 (closed: bounce opened) |
| Fri 30 Oct 16:45 | level reversal sell | opened only with the rule | -6.0 (scheduled close) |
| Wed 04 Nov 16:10 | slow grind sell | opened only with the rule | -5.5 (closed: bounce opened at R2) |
| Thu 05 Nov 10:20 | slow grind sell | opened only with the rule | -15.0 (stop) |
| Mon 26 Oct 08:25 | slow grind sell | opened only under the current rules | +20.0 (take profit) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (every bounce) + 2 + 3: 2 of 5 · 75% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 06:05 | slow grind sell | Mon 26 Oct 07:00 | -2.6 | closed: hourly exhaustion | +10.0 (profit lock) | -12.6 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 26 Oct 14:10 | Bollinger bounce buy | Mon 26 Oct 17:50 | +13.0 | closed: bounce opened | +7.2 (rejection at a level (half at the band +10.0)) | +5.9 |
| Tue 27 Oct 05:45 | slow grind sell | Tue 27 Oct 07:20 | +6.1 | closed: bounce opened | +20.0 (take profit) | -13.9 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 07:20 | +0.6 | closed: bounce opened | +50.0 (take profit) | -49.4 |
| Tue 27 Oct 09:55 | Bollinger bounce buy | Tue 27 Oct 12:35 | +7.1 | closed: bounce opened | -4.6 (rejection at a level) | +11.7 |
| Tue 27 Oct 12:35 | Bollinger bounce sell | Tue 27 Oct 16:40 | +12.8 | closed: bounce opened | +7.0 (rejection at a level (half at the band +8.0)) | +5.8 |
| Tue 27 Oct 16:05 | slow grind sell | Tue 27 Oct 16:40 | -0.6 | closed: bounce opened | +0.0 (scheduled close) | -0.6 |
| Tue 27 Oct 16:15 | EMA pullback sell | Tue 27 Oct 16:40 | -5.3 | closed: bounce opened | -12.0 (stop) | +6.7 |
| Wed 28 Oct 04:45 | slow grind sell | Wed 28 Oct 07:25 | +14.5 | closed: bounce opened | +10.0 (profit lock) | +4.5 |
| Wed 28 Oct 07:25 | Bollinger bounce buy | Wed 28 Oct 13:55 | +13.0 | closed: bounce opened | +11.4 (rejection at a level (half at the band +11.4)) | +1.6 |
| Wed 28 Oct 16:15 | level reversal buy | Wed 28 Oct 17:05 | +3.5 | closed: bounce opened | -1.7 (before big news) | +5.2 |
| Thu 29 Oct 22:05 | EMA pullback buy | Fri 30 Oct 07:45 | +16.8 | closed: bounce opened | +10.9 (scheduled close) | +5.9 |
| Fri 30 Oct 00:40 | EMA pullback buy | Fri 30 Oct 07:45 | +11.5 | closed: bounce opened | +30.0 (take profit) | -18.5 |
| Fri 30 Oct 07:10 | EMA pullback buy | Fri 30 Oct 07:45 | +0.7 | closed: bounce opened | +30.0 (take profit) | -29.3 |
| Fri 30 Oct 07:25 | level reversal buy | Fri 30 Oct 07:45 | -9.9 | closed: bounce opened | +20.0 (take profit) | -29.9 |
| Fri 30 Oct 08:15 | level reversal buy | Fri 30 Oct 10:40 | +11.1 | closed: bounce opened | not opened under the current rules |  |
| Fri 30 Oct 08:15 | slow grind buy | Fri 30 Oct 10:40 | +13.1 | closed: bounce opened | +20.0 (take profit) | -6.9 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 10:40 | Bollinger bounce sell | Fri 30 Oct 15:25 | +16.6 | closed: bounce opened | -1.8 (rejection at a level (half at the band -0.2)) | +18.4 |
| Fri 30 Oct 13:25 | level reversal sell | Fri 30 Oct 15:25 | +0.7 | closed: bounce opened | -4.1 (scheduled close) | +4.8 |
| Fri 30 Oct 15:25 | Bollinger bounce buy | Fri 30 Oct 16:25 | +5.8 | closed: bounce opened | +5.8 (rejection at a level (half at the band +6.5)) | +0.0 |
| Fri 30 Oct 16:15 | level reversal buy | Fri 30 Oct 16:25 | -8.4 | closed: bounce opened | not opened under the current rules |  |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 08:05 | EMA pullback buy | Tue 03 Nov 08:20 | -7.8 | closed: bounce opened | -12.0 (stop) | +4.2 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |
| Wed 04 Nov 08:30 | slow grind buy | Wed 04 Nov 10:40 | -6.7 | closed: bounce opened | -15.0 (stop) | +8.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 15:40 | +15.6 | closed: bounce opened | +15.6 (rejection at a level (half at the band +7.6)) | +0.0 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 15:40 | -7.5 | closed: bounce opened | -15.0 (stop) | +7.5 |
| Wed 04 Nov 16:10 | slow grind sell | Wed 04 Nov 17:10 | -5.5 | closed: bounce opened at R2 | not opened under the current rules |  |
| Thu 05 Nov 08:00 | slow grind sell | Thu 05 Nov 08:15 | -10.9 | closed: bounce opened | +9.7 (profit lock) | -20.6 |
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |
| Tue 10 Nov 05:00 | EMA pullback buy | Tue 10 Nov 07:55 | -0.4 | closed: bounce opened | -12.0 (stop) | +11.6 |
| Tue 10 Nov 06:10 | EMA pullback buy | Tue 10 Nov 07:55 | -2.3 | closed: bounce opened | -12.0 (stop) | +9.7 |
| Tue 10 Nov 07:20 | EMA pullback buy | Tue 10 Nov 07:55 | -5.7 | closed: bounce opened | -12.0 (stop) | +6.3 |
| Tue 10 Nov 16:25 | level reversal sell | Tue 10 Nov 17:00 | -1.9 | closed: bounce opened | -20.0 (stop) | +18.1 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 07:40 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Fri 30 Oct 08:15 | level reversal buy | opened only with the rule | +11.1 (closed: bounce opened) |
| Fri 30 Oct 16:15 | level reversal buy | opened only with the rule | -8.4 (closed: bounce opened) |
| Fri 30 Oct 16:45 | level reversal sell | opened only with the rule | -6.0 (scheduled close) |
| Wed 04 Nov 16:10 | slow grind sell | opened only with the rule | -5.5 (closed: bounce opened at R2) |
| Thu 05 Nov 10:20 | slow grind sell | opened only with the rule | -15.0 (stop) |
| Mon 26 Oct 08:25 | slow grind sell | opened only under the current rules | +20.0 (take profit) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (every bounce) + 2 + 3: 3 of 5 · 25% back · flat < 3

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:25 | slow grind sell | Mon 26 Oct 09:05 | +3.5 | closed: bounce opened | +20.0 (take profit) | -16.5 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 26 Oct 14:10 | Bollinger bounce buy | Mon 26 Oct 17:50 | +13.0 | closed: bounce opened | +7.2 (rejection at a level (half at the band +10.0)) | +5.9 |
| Tue 27 Oct 05:45 | slow grind sell | Tue 27 Oct 07:20 | +6.1 | closed: bounce opened | +20.0 (take profit) | -13.9 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 07:20 | +0.6 | closed: bounce opened | +50.0 (take profit) | -49.4 |
| Tue 27 Oct 09:55 | Bollinger bounce buy | Tue 27 Oct 12:35 | +7.1 | closed: bounce opened | -4.6 (rejection at a level) | +11.7 |
| Tue 27 Oct 12:35 | Bollinger bounce sell | Tue 27 Oct 16:40 | +12.8 | closed: bounce opened | +7.0 (rejection at a level (half at the band +8.0)) | +5.8 |
| Tue 27 Oct 16:05 | slow grind sell | Tue 27 Oct 16:40 | -0.6 | closed: bounce opened | +0.0 (scheduled close) | -0.6 |
| Tue 27 Oct 16:15 | EMA pullback sell | Tue 27 Oct 16:40 | -5.3 | closed: bounce opened | -12.0 (stop) | +6.7 |
| Wed 28 Oct 04:45 | slow grind sell | Wed 28 Oct 07:25 | +14.5 | closed: bounce opened | +10.0 (profit lock) | +4.5 |
| Wed 28 Oct 07:25 | Bollinger bounce buy | Wed 28 Oct 13:55 | +13.0 | closed: bounce opened | +11.4 (rejection at a level (half at the band +11.4)) | +1.6 |
| Wed 28 Oct 16:15 | level reversal buy | Wed 28 Oct 17:05 | +3.5 | closed: bounce opened | -1.7 (before big news) | +5.2 |
| Thu 29 Oct 22:05 | EMA pullback buy | Fri 30 Oct 07:45 | +16.8 | closed: bounce opened | +10.9 (scheduled close) | +5.9 |
| Fri 30 Oct 00:40 | EMA pullback buy | Fri 30 Oct 07:45 | +11.5 | closed: bounce opened | +30.0 (take profit) | -18.5 |
| Fri 30 Oct 07:10 | EMA pullback buy | Fri 30 Oct 07:45 | +0.7 | closed: bounce opened | +30.0 (take profit) | -29.3 |
| Fri 30 Oct 07:25 | level reversal buy | Fri 30 Oct 07:45 | -9.9 | closed: bounce opened | +20.0 (take profit) | -29.9 |
| Fri 30 Oct 08:15 | level reversal buy | Fri 30 Oct 10:40 | +11.1 | closed: bounce opened | not opened under the current rules |  |
| Fri 30 Oct 08:15 | slow grind buy | Fri 30 Oct 10:40 | +13.1 | closed: bounce opened | +20.0 (take profit) | -6.9 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 10:40 | Bollinger bounce sell | Fri 30 Oct 15:25 | +16.6 | closed: bounce opened | -1.8 (rejection at a level (half at the band -0.2)) | +18.4 |
| Fri 30 Oct 13:25 | level reversal sell | Fri 30 Oct 15:25 | +0.7 | closed: bounce opened | -4.1 (scheduled close) | +4.8 |
| Fri 30 Oct 15:25 | Bollinger bounce buy | Fri 30 Oct 16:25 | +5.8 | closed: bounce opened | +5.8 (rejection at a level (half at the band +6.5)) | +0.0 |
| Fri 30 Oct 16:15 | level reversal buy | Fri 30 Oct 16:25 | -8.4 | closed: bounce opened | not opened under the current rules |  |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 08:05 | EMA pullback buy | Tue 03 Nov 08:20 | -7.8 | closed: bounce opened | -12.0 (stop) | +4.2 |
| Wed 04 Nov 08:30 | slow grind buy | Wed 04 Nov 10:40 | -6.7 | closed: bounce opened | -15.0 (stop) | +8.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 15:40 | +15.6 | closed: bounce opened | +15.6 (rejection at a level (half at the band +7.6)) | +0.0 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 15:40 | -7.5 | closed: bounce opened | -15.0 (stop) | +7.5 |
| Wed 04 Nov 16:10 | slow grind sell | Wed 04 Nov 17:10 | -5.5 | closed: bounce opened at R2 | not opened under the current rules |  |
| Thu 05 Nov 08:00 | slow grind sell | Thu 05 Nov 08:15 | -10.9 | closed: bounce opened | +9.7 (profit lock) | -20.6 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 15:00 | +17.2 | closed: hourly exhaustion | +50.0 (take profit) | -32.8 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 15:00 | -7.2 | closed: hourly exhaustion | -15.0 (stop) | +7.8 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 22:00 | +7.7 | closed: hourly exhaustion | not opened under the current rules |  |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Tue 10 Nov 05:00 | EMA pullback buy | Tue 10 Nov 07:55 | -0.4 | closed: bounce opened | -12.0 (stop) | +11.6 |
| Tue 10 Nov 06:10 | EMA pullback buy | Tue 10 Nov 07:55 | -2.3 | closed: bounce opened | -12.0 (stop) | +9.7 |
| Tue 10 Nov 07:20 | EMA pullback buy | Tue 10 Nov 07:55 | -5.7 | closed: bounce opened | -12.0 (stop) | +6.3 |
| Tue 10 Nov 16:25 | level reversal sell | Tue 10 Nov 17:00 | -1.9 | closed: bounce opened | -20.0 (stop) | +18.1 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Fri 30 Oct 08:15 | level reversal buy | opened only with the rule | +11.1 (closed: bounce opened) |
| Fri 30 Oct 16:15 | level reversal buy | opened only with the rule | -8.4 (closed: bounce opened) |
| Fri 30 Oct 16:45 | level reversal sell | opened only with the rule | -6.0 (scheduled close) |
| Wed 04 Nov 16:10 | slow grind sell | opened only with the rule | -5.5 (closed: bounce opened at R2) |
| Thu 05 Nov 10:20 | slow grind sell | opened only with the rule | -15.0 (stop) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | +7.7 (closed: hourly exhaustion) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (every bounce) + 2 + 3: 3 of 5 · 25% back · flat < 5

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:25 | slow grind sell | Mon 26 Oct 09:05 | +3.5 | closed: bounce opened | +20.0 (take profit) | -16.5 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 26 Oct 14:10 | Bollinger bounce buy | Mon 26 Oct 17:50 | +13.0 | closed: bounce opened | +7.2 (rejection at a level (half at the band +10.0)) | +5.9 |
| Tue 27 Oct 05:45 | slow grind sell | Tue 27 Oct 07:20 | +6.1 | closed: bounce opened | +20.0 (take profit) | -13.9 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 07:20 | +0.6 | closed: bounce opened | +50.0 (take profit) | -49.4 |
| Tue 27 Oct 09:55 | Bollinger bounce buy | Tue 27 Oct 12:35 | +7.1 | closed: bounce opened | -4.6 (rejection at a level) | +11.7 |
| Tue 27 Oct 12:35 | Bollinger bounce sell | Tue 27 Oct 16:40 | +12.8 | closed: bounce opened | +7.0 (rejection at a level (half at the band +8.0)) | +5.8 |
| Tue 27 Oct 16:05 | slow grind sell | Tue 27 Oct 16:40 | -0.6 | closed: bounce opened | +0.0 (scheduled close) | -0.6 |
| Tue 27 Oct 16:15 | EMA pullback sell | Tue 27 Oct 16:40 | -5.3 | closed: bounce opened | -12.0 (stop) | +6.7 |
| Wed 28 Oct 04:45 | slow grind sell | Wed 28 Oct 07:25 | +14.5 | closed: bounce opened | +10.0 (profit lock) | +4.5 |
| Wed 28 Oct 07:25 | Bollinger bounce buy | Wed 28 Oct 13:55 | +13.0 | closed: bounce opened | +11.4 (rejection at a level (half at the band +11.4)) | +1.6 |
| Wed 28 Oct 16:15 | level reversal buy | Wed 28 Oct 17:05 | +3.5 | closed: bounce opened | -1.7 (before big news) | +5.2 |
| Thu 29 Oct 22:05 | EMA pullback buy | Fri 30 Oct 07:45 | +16.8 | closed: bounce opened | +10.9 (scheduled close) | +5.9 |
| Fri 30 Oct 00:40 | EMA pullback buy | Fri 30 Oct 07:45 | +11.5 | closed: bounce opened | +30.0 (take profit) | -18.5 |
| Fri 30 Oct 07:10 | EMA pullback buy | Fri 30 Oct 07:45 | +0.7 | closed: bounce opened | +30.0 (take profit) | -29.3 |
| Fri 30 Oct 07:25 | level reversal buy | Fri 30 Oct 07:45 | -9.9 | closed: bounce opened | +20.0 (take profit) | -29.9 |
| Fri 30 Oct 08:15 | level reversal buy | Fri 30 Oct 10:40 | +11.1 | closed: bounce opened | not opened under the current rules |  |
| Fri 30 Oct 08:15 | slow grind buy | Fri 30 Oct 10:40 | +13.1 | closed: bounce opened | +20.0 (take profit) | -6.9 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 10:40 | Bollinger bounce sell | Fri 30 Oct 15:25 | +16.6 | closed: bounce opened | -1.8 (rejection at a level (half at the band -0.2)) | +18.4 |
| Fri 30 Oct 13:25 | level reversal sell | Fri 30 Oct 15:25 | +0.7 | closed: bounce opened | -4.1 (scheduled close) | +4.8 |
| Fri 30 Oct 15:25 | Bollinger bounce buy | Fri 30 Oct 16:25 | +5.8 | closed: bounce opened | +5.8 (rejection at a level (half at the band +6.5)) | +0.0 |
| Fri 30 Oct 16:15 | level reversal buy | Fri 30 Oct 16:25 | -8.4 | closed: bounce opened | not opened under the current rules |  |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 08:05 | EMA pullback buy | Tue 03 Nov 08:20 | -7.8 | closed: bounce opened | -12.0 (stop) | +4.2 |
| Wed 04 Nov 08:30 | slow grind buy | Wed 04 Nov 10:40 | -6.7 | closed: bounce opened | -15.0 (stop) | +8.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 15:40 | +15.6 | closed: bounce opened | +15.6 (rejection at a level (half at the band +7.6)) | +0.0 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 15:40 | -7.5 | closed: bounce opened | -15.0 (stop) | +7.5 |
| Wed 04 Nov 16:10 | slow grind sell | Wed 04 Nov 17:10 | -5.5 | closed: bounce opened at R2 | not opened under the current rules |  |
| Thu 05 Nov 08:00 | slow grind sell | Thu 05 Nov 08:15 | -10.9 | closed: bounce opened | +9.7 (profit lock) | -20.6 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 14:00 | +27.0 | closed: hourly exhaustion | +50.0 (take profit) | -23.0 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 14:00 | +2.6 | closed: hourly exhaustion | -15.0 (stop) | +17.6 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 22:00 | +7.7 | closed: hourly exhaustion | not opened under the current rules |  |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Tue 10 Nov 05:00 | EMA pullback buy | Tue 10 Nov 07:55 | -0.4 | closed: bounce opened | -12.0 (stop) | +11.6 |
| Tue 10 Nov 06:10 | EMA pullback buy | Tue 10 Nov 07:55 | -2.3 | closed: bounce opened | -12.0 (stop) | +9.7 |
| Tue 10 Nov 07:20 | EMA pullback buy | Tue 10 Nov 07:55 | -5.7 | closed: bounce opened | -12.0 (stop) | +6.3 |
| Tue 10 Nov 16:25 | level reversal sell | Tue 10 Nov 17:00 | -1.9 | closed: bounce opened | -20.0 (stop) | +18.1 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Fri 30 Oct 08:15 | level reversal buy | opened only with the rule | +11.1 (closed: bounce opened) |
| Fri 30 Oct 16:15 | level reversal buy | opened only with the rule | -8.4 (closed: bounce opened) |
| Fri 30 Oct 16:45 | level reversal sell | opened only with the rule | -6.0 (scheduled close) |
| Wed 04 Nov 16:10 | slow grind sell | opened only with the rule | -5.5 (closed: bounce opened at R2) |
| Thu 05 Nov 10:20 | slow grind sell | opened only with the rule | -15.0 (stop) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | +7.7 (closed: hourly exhaustion) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (every bounce) + 2 + 3: 3 of 5 · 25% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:25 | slow grind sell | Mon 26 Oct 09:05 | +3.5 | closed: bounce opened | +20.0 (take profit) | -16.5 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 26 Oct 14:10 | Bollinger bounce buy | Mon 26 Oct 17:50 | +13.0 | closed: bounce opened | +7.2 (rejection at a level (half at the band +10.0)) | +5.9 |
| Tue 27 Oct 05:45 | slow grind sell | Tue 27 Oct 07:20 | +6.1 | closed: bounce opened | +20.0 (take profit) | -13.9 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 07:20 | +0.6 | closed: bounce opened | +50.0 (take profit) | -49.4 |
| Tue 27 Oct 09:55 | Bollinger bounce buy | Tue 27 Oct 12:35 | +7.1 | closed: bounce opened | -4.6 (rejection at a level) | +11.7 |
| Tue 27 Oct 12:35 | Bollinger bounce sell | Tue 27 Oct 16:40 | +12.8 | closed: bounce opened | +7.0 (rejection at a level (half at the band +8.0)) | +5.8 |
| Tue 27 Oct 16:05 | slow grind sell | Tue 27 Oct 16:40 | -0.6 | closed: bounce opened | +0.0 (scheduled close) | -0.6 |
| Tue 27 Oct 16:15 | EMA pullback sell | Tue 27 Oct 16:40 | -5.3 | closed: bounce opened | -12.0 (stop) | +6.7 |
| Wed 28 Oct 04:45 | slow grind sell | Wed 28 Oct 07:25 | +14.5 | closed: bounce opened | +10.0 (profit lock) | +4.5 |
| Wed 28 Oct 07:25 | Bollinger bounce buy | Wed 28 Oct 13:55 | +13.0 | closed: bounce opened | +11.4 (rejection at a level (half at the band +11.4)) | +1.6 |
| Wed 28 Oct 16:15 | level reversal buy | Wed 28 Oct 17:05 | +3.5 | closed: bounce opened | -1.7 (before big news) | +5.2 |
| Thu 29 Oct 14:45 | breakout buy | Thu 29 Oct 22:00 | +19.2 | closed: hourly exhaustion | +50.0 (take profit) | -30.8 |
| Thu 29 Oct 22:05 | EMA pullback buy | Fri 30 Oct 07:45 | +16.8 | closed: bounce opened | +10.9 (scheduled close) | +5.9 |
| Fri 30 Oct 00:40 | EMA pullback buy | Fri 30 Oct 07:45 | +11.5 | closed: bounce opened | +30.0 (take profit) | -18.5 |
| Fri 30 Oct 07:10 | EMA pullback buy | Fri 30 Oct 07:45 | +0.7 | closed: bounce opened | +30.0 (take profit) | -29.3 |
| Fri 30 Oct 07:25 | level reversal buy | Fri 30 Oct 07:45 | -9.9 | closed: bounce opened | +20.0 (take profit) | -29.9 |
| Fri 30 Oct 08:15 | level reversal buy | Fri 30 Oct 10:40 | +11.1 | closed: bounce opened | not opened under the current rules |  |
| Fri 30 Oct 08:15 | slow grind buy | Fri 30 Oct 10:40 | +13.1 | closed: bounce opened | +20.0 (take profit) | -6.9 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 10:40 | Bollinger bounce sell | Fri 30 Oct 15:25 | +16.6 | closed: bounce opened | -1.8 (rejection at a level (half at the band -0.2)) | +18.4 |
| Fri 30 Oct 13:25 | level reversal sell | Fri 30 Oct 15:25 | +0.7 | closed: bounce opened | -4.1 (scheduled close) | +4.8 |
| Fri 30 Oct 15:25 | Bollinger bounce buy | Fri 30 Oct 16:25 | +5.8 | closed: bounce opened | +5.8 (rejection at a level (half at the band +6.5)) | +0.0 |
| Fri 30 Oct 16:15 | level reversal buy | Fri 30 Oct 16:25 | -8.4 | closed: bounce opened | not opened under the current rules |  |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 08:05 | EMA pullback buy | Tue 03 Nov 08:20 | -7.8 | closed: bounce opened | -12.0 (stop) | +4.2 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |
| Wed 04 Nov 08:30 | slow grind buy | Wed 04 Nov 10:40 | -6.7 | closed: bounce opened | -15.0 (stop) | +8.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 15:40 | +15.6 | closed: bounce opened | +15.6 (rejection at a level (half at the band +7.6)) | +0.0 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 15:40 | -7.5 | closed: bounce opened | -15.0 (stop) | +7.5 |
| Wed 04 Nov 16:10 | slow grind sell | Wed 04 Nov 17:10 | -5.5 | closed: bounce opened at R2 | not opened under the current rules |  |
| Thu 05 Nov 08:00 | slow grind sell | Thu 05 Nov 08:15 | -10.9 | closed: bounce opened | +9.7 (profit lock) | -20.6 |
| Thu 05 Nov 18:35 | breakout sell | Thu 05 Nov 20:00 | +8.4 | closed: hourly exhaustion | +50.0 (take profit) | -41.6 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 14:00 | +27.0 | closed: hourly exhaustion | +50.0 (take profit) | -23.0 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 14:00 | +2.6 | closed: hourly exhaustion | -15.0 (stop) | +17.6 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 22:00 | +7.7 | closed: hourly exhaustion | not opened under the current rules |  |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Tue 10 Nov 05:00 | EMA pullback buy | Tue 10 Nov 07:00 | -2.9 | closed: hourly exhaustion | -12.0 (stop) | +9.1 |
| Tue 10 Nov 06:10 | EMA pullback buy | Tue 10 Nov 07:00 | -4.8 | closed: hourly exhaustion | -12.0 (stop) | +7.2 |
| Tue 10 Nov 07:20 | EMA pullback buy | Tue 10 Nov 07:55 | -5.7 | closed: bounce opened | -12.0 (stop) | +6.3 |
| Tue 10 Nov 16:25 | level reversal sell | Tue 10 Nov 17:00 | -1.9 | closed: bounce opened | -20.0 (stop) | +18.1 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Fri 30 Oct 08:15 | level reversal buy | opened only with the rule | +11.1 (closed: bounce opened) |
| Fri 30 Oct 16:15 | level reversal buy | opened only with the rule | -8.4 (closed: bounce opened) |
| Fri 30 Oct 16:45 | level reversal sell | opened only with the rule | -6.0 (scheduled close) |
| Wed 04 Nov 16:10 | slow grind sell | opened only with the rule | -5.5 (closed: bounce opened at R2) |
| Thu 05 Nov 10:20 | slow grind sell | opened only with the rule | -15.0 (stop) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | +7.7 (closed: hourly exhaustion) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (every bounce) + 2 + 3: 3 of 5 · 50% back · flat < 3

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:25 | slow grind sell | Mon 26 Oct 09:05 | +3.5 | closed: bounce opened | +20.0 (take profit) | -16.5 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 26 Oct 14:10 | Bollinger bounce buy | Mon 26 Oct 17:50 | +13.0 | closed: bounce opened | +7.2 (rejection at a level (half at the band +10.0)) | +5.9 |
| Tue 27 Oct 05:45 | slow grind sell | Tue 27 Oct 07:20 | +6.1 | closed: bounce opened | +20.0 (take profit) | -13.9 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 07:20 | +0.6 | closed: bounce opened | +50.0 (take profit) | -49.4 |
| Tue 27 Oct 09:55 | Bollinger bounce buy | Tue 27 Oct 12:35 | +7.1 | closed: bounce opened | -4.6 (rejection at a level) | +11.7 |
| Tue 27 Oct 12:35 | Bollinger bounce sell | Tue 27 Oct 16:40 | +12.8 | closed: bounce opened | +7.0 (rejection at a level (half at the band +8.0)) | +5.8 |
| Tue 27 Oct 16:05 | slow grind sell | Tue 27 Oct 16:40 | -0.6 | closed: bounce opened | +0.0 (scheduled close) | -0.6 |
| Tue 27 Oct 16:15 | EMA pullback sell | Tue 27 Oct 16:40 | -5.3 | closed: bounce opened | -12.0 (stop) | +6.7 |
| Wed 28 Oct 04:45 | slow grind sell | Wed 28 Oct 07:25 | +14.5 | closed: bounce opened | +10.0 (profit lock) | +4.5 |
| Wed 28 Oct 07:25 | Bollinger bounce buy | Wed 28 Oct 13:55 | +13.0 | closed: bounce opened | +11.4 (rejection at a level (half at the band +11.4)) | +1.6 |
| Wed 28 Oct 16:15 | level reversal buy | Wed 28 Oct 17:05 | +3.5 | closed: bounce opened | -1.7 (before big news) | +5.2 |
| Thu 29 Oct 22:05 | EMA pullback buy | Fri 30 Oct 07:45 | +16.8 | closed: bounce opened | +10.9 (scheduled close) | +5.9 |
| Fri 30 Oct 00:40 | EMA pullback buy | Fri 30 Oct 07:45 | +11.5 | closed: bounce opened | +30.0 (take profit) | -18.5 |
| Fri 30 Oct 07:10 | EMA pullback buy | Fri 30 Oct 07:45 | +0.7 | closed: bounce opened | +30.0 (take profit) | -29.3 |
| Fri 30 Oct 07:25 | level reversal buy | Fri 30 Oct 07:45 | -9.9 | closed: bounce opened | +20.0 (take profit) | -29.9 |
| Fri 30 Oct 08:15 | level reversal buy | Fri 30 Oct 10:40 | +11.1 | closed: bounce opened | not opened under the current rules |  |
| Fri 30 Oct 08:15 | slow grind buy | Fri 30 Oct 10:40 | +13.1 | closed: bounce opened | +20.0 (take profit) | -6.9 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 10:40 | Bollinger bounce sell | Fri 30 Oct 15:25 | +16.6 | closed: bounce opened | -1.8 (rejection at a level (half at the band -0.2)) | +18.4 |
| Fri 30 Oct 13:25 | level reversal sell | Fri 30 Oct 15:25 | +0.7 | closed: bounce opened | -4.1 (scheduled close) | +4.8 |
| Fri 30 Oct 15:25 | Bollinger bounce buy | Fri 30 Oct 16:25 | +5.8 | closed: bounce opened | +5.8 (rejection at a level (half at the band +6.5)) | +0.0 |
| Fri 30 Oct 16:15 | level reversal buy | Fri 30 Oct 16:25 | -8.4 | closed: bounce opened | not opened under the current rules |  |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 08:05 | EMA pullback buy | Tue 03 Nov 08:20 | -7.8 | closed: bounce opened | -12.0 (stop) | +4.2 |
| Wed 04 Nov 08:30 | slow grind buy | Wed 04 Nov 10:40 | -6.7 | closed: bounce opened | -15.0 (stop) | +8.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 15:40 | +15.6 | closed: bounce opened | +15.6 (rejection at a level (half at the band +7.6)) | +0.0 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 15:40 | -7.5 | closed: bounce opened | -15.0 (stop) | +7.5 |
| Wed 04 Nov 16:10 | slow grind sell | Wed 04 Nov 17:10 | -5.5 | closed: bounce opened at R2 | not opened under the current rules |  |
| Thu 05 Nov 08:00 | slow grind sell | Thu 05 Nov 08:15 | -10.9 | closed: bounce opened | +9.7 (profit lock) | -20.6 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 15:00 | +17.2 | closed: hourly exhaustion | +50.0 (take profit) | -32.8 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 15:00 | -7.2 | closed: hourly exhaustion | -15.0 (stop) | +7.8 |
| Mon 09 Nov 19:35 | breakout buy | Tue 10 Nov 07:55 | +19.9 | closed: bounce opened | not opened under the current rules |  |
| Tue 10 Nov 05:00 | EMA pullback buy | Tue 10 Nov 07:55 | -0.4 | closed: bounce opened | -12.0 (stop) | +11.6 |
| Tue 10 Nov 06:10 | EMA pullback buy | Tue 10 Nov 07:55 | -2.3 | closed: bounce opened | -12.0 (stop) | +9.7 |
| Tue 10 Nov 07:20 | EMA pullback buy | Tue 10 Nov 07:55 | -5.7 | closed: bounce opened | -12.0 (stop) | +6.3 |
| Tue 10 Nov 16:25 | level reversal sell | Tue 10 Nov 17:00 | -1.9 | closed: bounce opened | -20.0 (stop) | +18.1 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Fri 30 Oct 08:15 | level reversal buy | opened only with the rule | +11.1 (closed: bounce opened) |
| Fri 30 Oct 16:15 | level reversal buy | opened only with the rule | -8.4 (closed: bounce opened) |
| Fri 30 Oct 16:45 | level reversal sell | opened only with the rule | -6.0 (scheduled close) |
| Wed 04 Nov 16:10 | slow grind sell | opened only with the rule | -5.5 (closed: bounce opened at R2) |
| Thu 05 Nov 10:20 | slow grind sell | opened only with the rule | -15.0 (stop) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | +19.9 (closed: bounce opened) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (every bounce) + 2 + 3: 3 of 5 · 50% back · flat < 5

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:25 | slow grind sell | Mon 26 Oct 09:05 | +3.5 | closed: bounce opened | +20.0 (take profit) | -16.5 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 26 Oct 14:10 | Bollinger bounce buy | Mon 26 Oct 17:50 | +13.0 | closed: bounce opened | +7.2 (rejection at a level (half at the band +10.0)) | +5.9 |
| Tue 27 Oct 05:45 | slow grind sell | Tue 27 Oct 07:20 | +6.1 | closed: bounce opened | +20.0 (take profit) | -13.9 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 07:20 | +0.6 | closed: bounce opened | +50.0 (take profit) | -49.4 |
| Tue 27 Oct 09:55 | Bollinger bounce buy | Tue 27 Oct 12:35 | +7.1 | closed: bounce opened | -4.6 (rejection at a level) | +11.7 |
| Tue 27 Oct 12:35 | Bollinger bounce sell | Tue 27 Oct 16:40 | +12.8 | closed: bounce opened | +7.0 (rejection at a level (half at the band +8.0)) | +5.8 |
| Tue 27 Oct 16:05 | slow grind sell | Tue 27 Oct 16:40 | -0.6 | closed: bounce opened | +0.0 (scheduled close) | -0.6 |
| Tue 27 Oct 16:15 | EMA pullback sell | Tue 27 Oct 16:40 | -5.3 | closed: bounce opened | -12.0 (stop) | +6.7 |
| Wed 28 Oct 04:45 | slow grind sell | Wed 28 Oct 07:25 | +14.5 | closed: bounce opened | +10.0 (profit lock) | +4.5 |
| Wed 28 Oct 07:25 | Bollinger bounce buy | Wed 28 Oct 13:55 | +13.0 | closed: bounce opened | +11.4 (rejection at a level (half at the band +11.4)) | +1.6 |
| Wed 28 Oct 16:15 | level reversal buy | Wed 28 Oct 17:05 | +3.5 | closed: bounce opened | -1.7 (before big news) | +5.2 |
| Thu 29 Oct 22:05 | EMA pullback buy | Fri 30 Oct 07:45 | +16.8 | closed: bounce opened | +10.9 (scheduled close) | +5.9 |
| Fri 30 Oct 00:40 | EMA pullback buy | Fri 30 Oct 07:45 | +11.5 | closed: bounce opened | +30.0 (take profit) | -18.5 |
| Fri 30 Oct 07:10 | EMA pullback buy | Fri 30 Oct 07:45 | +0.7 | closed: bounce opened | +30.0 (take profit) | -29.3 |
| Fri 30 Oct 07:25 | level reversal buy | Fri 30 Oct 07:45 | -9.9 | closed: bounce opened | +20.0 (take profit) | -29.9 |
| Fri 30 Oct 08:15 | level reversal buy | Fri 30 Oct 10:40 | +11.1 | closed: bounce opened | not opened under the current rules |  |
| Fri 30 Oct 08:15 | slow grind buy | Fri 30 Oct 10:40 | +13.1 | closed: bounce opened | +20.0 (take profit) | -6.9 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 10:40 | Bollinger bounce sell | Fri 30 Oct 15:25 | +16.6 | closed: bounce opened | -1.8 (rejection at a level (half at the band -0.2)) | +18.4 |
| Fri 30 Oct 13:25 | level reversal sell | Fri 30 Oct 15:25 | +0.7 | closed: bounce opened | -4.1 (scheduled close) | +4.8 |
| Fri 30 Oct 15:25 | Bollinger bounce buy | Fri 30 Oct 16:25 | +5.8 | closed: bounce opened | +5.8 (rejection at a level (half at the band +6.5)) | +0.0 |
| Fri 30 Oct 16:15 | level reversal buy | Fri 30 Oct 16:25 | -8.4 | closed: bounce opened | not opened under the current rules |  |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 08:05 | EMA pullback buy | Tue 03 Nov 08:20 | -7.8 | closed: bounce opened | -12.0 (stop) | +4.2 |
| Wed 04 Nov 08:30 | slow grind buy | Wed 04 Nov 10:40 | -6.7 | closed: bounce opened | -15.0 (stop) | +8.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 15:40 | +15.6 | closed: bounce opened | +15.6 (rejection at a level (half at the band +7.6)) | +0.0 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 15:40 | -7.5 | closed: bounce opened | -15.0 (stop) | +7.5 |
| Wed 04 Nov 16:10 | slow grind sell | Wed 04 Nov 17:10 | -5.5 | closed: bounce opened at R2 | not opened under the current rules |  |
| Thu 05 Nov 08:00 | slow grind sell | Thu 05 Nov 08:15 | -10.9 | closed: bounce opened | +9.7 (profit lock) | -20.6 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 15:00 | +17.2 | closed: hourly exhaustion | +50.0 (take profit) | -32.8 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 15:00 | -7.2 | closed: hourly exhaustion | -15.0 (stop) | +7.8 |
| Mon 09 Nov 19:35 | breakout buy | Tue 10 Nov 07:55 | +19.9 | closed: bounce opened | not opened under the current rules |  |
| Tue 10 Nov 05:00 | EMA pullback buy | Tue 10 Nov 07:55 | -0.4 | closed: bounce opened | -12.0 (stop) | +11.6 |
| Tue 10 Nov 06:10 | EMA pullback buy | Tue 10 Nov 07:55 | -2.3 | closed: bounce opened | -12.0 (stop) | +9.7 |
| Tue 10 Nov 07:20 | EMA pullback buy | Tue 10 Nov 07:55 | -5.7 | closed: bounce opened | -12.0 (stop) | +6.3 |
| Tue 10 Nov 16:25 | level reversal sell | Tue 10 Nov 17:00 | -1.9 | closed: bounce opened | -20.0 (stop) | +18.1 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Fri 30 Oct 08:15 | level reversal buy | opened only with the rule | +11.1 (closed: bounce opened) |
| Fri 30 Oct 16:15 | level reversal buy | opened only with the rule | -8.4 (closed: bounce opened) |
| Fri 30 Oct 16:45 | level reversal sell | opened only with the rule | -6.0 (scheduled close) |
| Wed 04 Nov 16:10 | slow grind sell | opened only with the rule | -5.5 (closed: bounce opened at R2) |
| Thu 05 Nov 10:20 | slow grind sell | opened only with the rule | -15.0 (stop) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | +19.9 (closed: bounce opened) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (every bounce) + 2 + 3: 3 of 5 · 50% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:25 | slow grind sell | Mon 26 Oct 09:05 | +3.5 | closed: bounce opened | +20.0 (take profit) | -16.5 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 26 Oct 14:10 | Bollinger bounce buy | Mon 26 Oct 17:50 | +13.0 | closed: bounce opened | +7.2 (rejection at a level (half at the band +10.0)) | +5.9 |
| Tue 27 Oct 05:45 | slow grind sell | Tue 27 Oct 07:20 | +6.1 | closed: bounce opened | +20.0 (take profit) | -13.9 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 07:20 | +0.6 | closed: bounce opened | +50.0 (take profit) | -49.4 |
| Tue 27 Oct 09:55 | Bollinger bounce buy | Tue 27 Oct 12:35 | +7.1 | closed: bounce opened | -4.6 (rejection at a level) | +11.7 |
| Tue 27 Oct 12:35 | Bollinger bounce sell | Tue 27 Oct 16:40 | +12.8 | closed: bounce opened | +7.0 (rejection at a level (half at the band +8.0)) | +5.8 |
| Tue 27 Oct 16:05 | slow grind sell | Tue 27 Oct 16:40 | -0.6 | closed: bounce opened | +0.0 (scheduled close) | -0.6 |
| Tue 27 Oct 16:15 | EMA pullback sell | Tue 27 Oct 16:40 | -5.3 | closed: bounce opened | -12.0 (stop) | +6.7 |
| Wed 28 Oct 04:45 | slow grind sell | Wed 28 Oct 07:25 | +14.5 | closed: bounce opened | +10.0 (profit lock) | +4.5 |
| Wed 28 Oct 07:25 | Bollinger bounce buy | Wed 28 Oct 13:55 | +13.0 | closed: bounce opened | +11.4 (rejection at a level (half at the band +11.4)) | +1.6 |
| Wed 28 Oct 16:15 | level reversal buy | Wed 28 Oct 17:05 | +3.5 | closed: bounce opened | -1.7 (before big news) | +5.2 |
| Thu 29 Oct 22:05 | EMA pullback buy | Fri 30 Oct 07:45 | +16.8 | closed: bounce opened | +10.9 (scheduled close) | +5.9 |
| Fri 30 Oct 00:40 | EMA pullback buy | Fri 30 Oct 07:45 | +11.5 | closed: bounce opened | +30.0 (take profit) | -18.5 |
| Fri 30 Oct 07:10 | EMA pullback buy | Fri 30 Oct 07:45 | +0.7 | closed: bounce opened | +30.0 (take profit) | -29.3 |
| Fri 30 Oct 07:25 | level reversal buy | Fri 30 Oct 07:45 | -9.9 | closed: bounce opened | +20.0 (take profit) | -29.9 |
| Fri 30 Oct 08:15 | level reversal buy | Fri 30 Oct 10:40 | +11.1 | closed: bounce opened | not opened under the current rules |  |
| Fri 30 Oct 08:15 | slow grind buy | Fri 30 Oct 10:40 | +13.1 | closed: bounce opened | +20.0 (take profit) | -6.9 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 10:40 | Bollinger bounce sell | Fri 30 Oct 15:25 | +16.6 | closed: bounce opened | -1.8 (rejection at a level (half at the band -0.2)) | +18.4 |
| Fri 30 Oct 13:25 | level reversal sell | Fri 30 Oct 15:25 | +0.7 | closed: bounce opened | -4.1 (scheduled close) | +4.8 |
| Fri 30 Oct 15:25 | Bollinger bounce buy | Fri 30 Oct 16:25 | +5.8 | closed: bounce opened | +5.8 (rejection at a level (half at the band +6.5)) | +0.0 |
| Fri 30 Oct 16:15 | level reversal buy | Fri 30 Oct 16:25 | -8.4 | closed: bounce opened | not opened under the current rules |  |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 08:05 | EMA pullback buy | Tue 03 Nov 08:20 | -7.8 | closed: bounce opened | -12.0 (stop) | +4.2 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |
| Wed 04 Nov 08:30 | slow grind buy | Wed 04 Nov 10:40 | -6.7 | closed: bounce opened | -15.0 (stop) | +8.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 15:40 | +15.6 | closed: bounce opened | +15.6 (rejection at a level (half at the band +7.6)) | +0.0 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 15:40 | -7.5 | closed: bounce opened | -15.0 (stop) | +7.5 |
| Wed 04 Nov 16:10 | slow grind sell | Wed 04 Nov 17:10 | -5.5 | closed: bounce opened at R2 | not opened under the current rules |  |
| Thu 05 Nov 08:00 | slow grind sell | Thu 05 Nov 08:15 | -10.9 | closed: bounce opened | +9.7 (profit lock) | -20.6 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 15:00 | +17.2 | closed: hourly exhaustion | +50.0 (take profit) | -32.8 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 15:00 | -7.2 | closed: hourly exhaustion | -15.0 (stop) | +7.8 |
| Mon 09 Nov 19:35 | breakout buy | Tue 10 Nov 07:55 | +19.9 | closed: bounce opened | not opened under the current rules |  |
| Tue 10 Nov 05:00 | EMA pullback buy | Tue 10 Nov 07:55 | -0.4 | closed: bounce opened | -12.0 (stop) | +11.6 |
| Tue 10 Nov 06:10 | EMA pullback buy | Tue 10 Nov 07:55 | -2.3 | closed: bounce opened | -12.0 (stop) | +9.7 |
| Tue 10 Nov 07:20 | EMA pullback buy | Tue 10 Nov 07:55 | -5.7 | closed: bounce opened | -12.0 (stop) | +6.3 |
| Tue 10 Nov 16:25 | level reversal sell | Tue 10 Nov 17:00 | -1.9 | closed: bounce opened | -20.0 (stop) | +18.1 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Fri 30 Oct 08:15 | level reversal buy | opened only with the rule | +11.1 (closed: bounce opened) |
| Fri 30 Oct 16:15 | level reversal buy | opened only with the rule | -8.4 (closed: bounce opened) |
| Fri 30 Oct 16:45 | level reversal sell | opened only with the rule | -6.0 (scheduled close) |
| Wed 04 Nov 16:10 | slow grind sell | opened only with the rule | -5.5 (closed: bounce opened at R2) |
| Thu 05 Nov 10:20 | slow grind sell | opened only with the rule | -15.0 (stop) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | +19.9 (closed: bounce opened) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (every bounce) + 2 + 3: 3 of 5 · 75% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:25 | slow grind sell | Mon 26 Oct 09:05 | +3.5 | closed: bounce opened | +20.0 (take profit) | -16.5 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 26 Oct 14:10 | Bollinger bounce buy | Mon 26 Oct 17:50 | +13.0 | closed: bounce opened | +7.2 (rejection at a level (half at the band +10.0)) | +5.9 |
| Tue 27 Oct 05:45 | slow grind sell | Tue 27 Oct 07:20 | +6.1 | closed: bounce opened | +20.0 (take profit) | -13.9 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 07:20 | +0.6 | closed: bounce opened | +50.0 (take profit) | -49.4 |
| Tue 27 Oct 09:55 | Bollinger bounce buy | Tue 27 Oct 12:35 | +7.1 | closed: bounce opened | -4.6 (rejection at a level) | +11.7 |
| Tue 27 Oct 12:35 | Bollinger bounce sell | Tue 27 Oct 16:40 | +12.8 | closed: bounce opened | +7.0 (rejection at a level (half at the band +8.0)) | +5.8 |
| Tue 27 Oct 16:05 | slow grind sell | Tue 27 Oct 16:40 | -0.6 | closed: bounce opened | +0.0 (scheduled close) | -0.6 |
| Tue 27 Oct 16:15 | EMA pullback sell | Tue 27 Oct 16:40 | -5.3 | closed: bounce opened | -12.0 (stop) | +6.7 |
| Wed 28 Oct 04:45 | slow grind sell | Wed 28 Oct 07:25 | +14.5 | closed: bounce opened | +10.0 (profit lock) | +4.5 |
| Wed 28 Oct 07:25 | Bollinger bounce buy | Wed 28 Oct 13:55 | +13.0 | closed: bounce opened | +11.4 (rejection at a level (half at the band +11.4)) | +1.6 |
| Wed 28 Oct 16:15 | level reversal buy | Wed 28 Oct 17:05 | +3.5 | closed: bounce opened | -1.7 (before big news) | +5.2 |
| Thu 29 Oct 22:05 | EMA pullback buy | Fri 30 Oct 07:45 | +16.8 | closed: bounce opened | +10.9 (scheduled close) | +5.9 |
| Fri 30 Oct 00:40 | EMA pullback buy | Fri 30 Oct 07:45 | +11.5 | closed: bounce opened | +30.0 (take profit) | -18.5 |
| Fri 30 Oct 07:10 | EMA pullback buy | Fri 30 Oct 07:45 | +0.7 | closed: bounce opened | +30.0 (take profit) | -29.3 |
| Fri 30 Oct 07:25 | level reversal buy | Fri 30 Oct 07:45 | -9.9 | closed: bounce opened | +20.0 (take profit) | -29.9 |
| Fri 30 Oct 08:15 | level reversal buy | Fri 30 Oct 10:40 | +11.1 | closed: bounce opened | not opened under the current rules |  |
| Fri 30 Oct 08:15 | slow grind buy | Fri 30 Oct 10:40 | +13.1 | closed: bounce opened | +20.0 (take profit) | -6.9 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 10:40 | Bollinger bounce sell | Fri 30 Oct 15:25 | +16.6 | closed: bounce opened | -1.8 (rejection at a level (half at the band -0.2)) | +18.4 |
| Fri 30 Oct 13:25 | level reversal sell | Fri 30 Oct 15:25 | +0.7 | closed: bounce opened | -4.1 (scheduled close) | +4.8 |
| Fri 30 Oct 15:25 | Bollinger bounce buy | Fri 30 Oct 16:25 | +5.8 | closed: bounce opened | +5.8 (rejection at a level (half at the band +6.5)) | +0.0 |
| Fri 30 Oct 16:15 | level reversal buy | Fri 30 Oct 16:25 | -8.4 | closed: bounce opened | not opened under the current rules |  |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 08:05 | EMA pullback buy | Tue 03 Nov 08:20 | -7.8 | closed: bounce opened | -12.0 (stop) | +4.2 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |
| Wed 04 Nov 08:30 | slow grind buy | Wed 04 Nov 10:40 | -6.7 | closed: bounce opened | -15.0 (stop) | +8.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 15:40 | +15.6 | closed: bounce opened | +15.6 (rejection at a level (half at the band +7.6)) | +0.0 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 15:40 | -7.5 | closed: bounce opened | -15.0 (stop) | +7.5 |
| Wed 04 Nov 16:10 | slow grind sell | Wed 04 Nov 17:10 | -5.5 | closed: bounce opened at R2 | not opened under the current rules |  |
| Thu 05 Nov 08:00 | slow grind sell | Thu 05 Nov 08:15 | -10.9 | closed: bounce opened | +9.7 (profit lock) | -20.6 |
| Tue 10 Nov 05:00 | EMA pullback buy | Tue 10 Nov 07:55 | -0.4 | closed: bounce opened | -12.0 (stop) | +11.6 |
| Tue 10 Nov 06:10 | EMA pullback buy | Tue 10 Nov 07:55 | -2.3 | closed: bounce opened | -12.0 (stop) | +9.7 |
| Tue 10 Nov 07:20 | EMA pullback buy | Tue 10 Nov 07:55 | -5.7 | closed: bounce opened | -12.0 (stop) | +6.3 |
| Tue 10 Nov 16:25 | level reversal sell | Tue 10 Nov 17:00 | -1.9 | closed: bounce opened | -20.0 (stop) | +18.1 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Fri 30 Oct 08:15 | level reversal buy | opened only with the rule | +11.1 (closed: bounce opened) |
| Fri 30 Oct 16:15 | level reversal buy | opened only with the rule | -8.4 (closed: bounce opened) |
| Fri 30 Oct 16:45 | level reversal sell | opened only with the rule | -6.0 (scheduled close) |
| Wed 04 Nov 16:10 | slow grind sell | opened only with the rule | -5.5 (closed: bounce opened at R2) |
| Thu 05 Nov 10:20 | slow grind sell | opened only with the rule | -15.0 (stop) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (every bounce) + 2 + 3: 4 of 5 · 25% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:25 | slow grind sell | Mon 26 Oct 09:05 | +3.5 | closed: bounce opened | +20.0 (take profit) | -16.5 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 26 Oct 14:10 | Bollinger bounce buy | Mon 26 Oct 17:50 | +13.0 | closed: bounce opened | +7.2 (rejection at a level (half at the band +10.0)) | +5.9 |
| Tue 27 Oct 05:45 | slow grind sell | Tue 27 Oct 07:20 | +6.1 | closed: bounce opened | +20.0 (take profit) | -13.9 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 07:20 | +0.6 | closed: bounce opened | +50.0 (take profit) | -49.4 |
| Tue 27 Oct 09:55 | Bollinger bounce buy | Tue 27 Oct 12:35 | +7.1 | closed: bounce opened | -4.6 (rejection at a level) | +11.7 |
| Tue 27 Oct 12:35 | Bollinger bounce sell | Tue 27 Oct 16:40 | +12.8 | closed: bounce opened | +7.0 (rejection at a level (half at the band +8.0)) | +5.8 |
| Tue 27 Oct 16:05 | slow grind sell | Tue 27 Oct 16:40 | -0.6 | closed: bounce opened | +0.0 (scheduled close) | -0.6 |
| Tue 27 Oct 16:15 | EMA pullback sell | Tue 27 Oct 16:40 | -5.3 | closed: bounce opened | -12.0 (stop) | +6.7 |
| Wed 28 Oct 04:45 | slow grind sell | Wed 28 Oct 07:25 | +14.5 | closed: bounce opened | +10.0 (profit lock) | +4.5 |
| Wed 28 Oct 07:25 | Bollinger bounce buy | Wed 28 Oct 13:55 | +13.0 | closed: bounce opened | +11.4 (rejection at a level (half at the band +11.4)) | +1.6 |
| Wed 28 Oct 16:15 | level reversal buy | Wed 28 Oct 17:05 | +3.5 | closed: bounce opened | -1.7 (before big news) | +5.2 |
| Thu 29 Oct 22:05 | EMA pullback buy | Fri 30 Oct 07:45 | +16.8 | closed: bounce opened | +10.9 (scheduled close) | +5.9 |
| Fri 30 Oct 00:40 | EMA pullback buy | Fri 30 Oct 07:45 | +11.5 | closed: bounce opened | +30.0 (take profit) | -18.5 |
| Fri 30 Oct 07:10 | EMA pullback buy | Fri 30 Oct 07:45 | +0.7 | closed: bounce opened | +30.0 (take profit) | -29.3 |
| Fri 30 Oct 07:25 | level reversal buy | Fri 30 Oct 07:45 | -9.9 | closed: bounce opened | +20.0 (take profit) | -29.9 |
| Fri 30 Oct 08:15 | level reversal buy | Fri 30 Oct 10:40 | +11.1 | closed: bounce opened | not opened under the current rules |  |
| Fri 30 Oct 08:15 | slow grind buy | Fri 30 Oct 10:40 | +13.1 | closed: bounce opened | +20.0 (take profit) | -6.9 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 10:40 | Bollinger bounce sell | Fri 30 Oct 15:25 | +16.6 | closed: bounce opened | -1.8 (rejection at a level (half at the band -0.2)) | +18.4 |
| Fri 30 Oct 13:25 | level reversal sell | Fri 30 Oct 15:25 | +0.7 | closed: bounce opened | -4.1 (scheduled close) | +4.8 |
| Fri 30 Oct 15:25 | Bollinger bounce buy | Fri 30 Oct 16:25 | +5.8 | closed: bounce opened | +5.8 (rejection at a level (half at the band +6.5)) | +0.0 |
| Fri 30 Oct 16:15 | level reversal buy | Fri 30 Oct 16:25 | -8.4 | closed: bounce opened | not opened under the current rules |  |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 08:05 | EMA pullback buy | Tue 03 Nov 08:20 | -7.8 | closed: bounce opened | -12.0 (stop) | +4.2 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |
| Wed 04 Nov 08:30 | slow grind buy | Wed 04 Nov 10:40 | -6.7 | closed: bounce opened | -15.0 (stop) | +8.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 15:40 | +15.6 | closed: bounce opened | +15.6 (rejection at a level (half at the band +7.6)) | +0.0 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 15:40 | -7.5 | closed: bounce opened | -15.0 (stop) | +7.5 |
| Wed 04 Nov 16:10 | slow grind sell | Wed 04 Nov 17:10 | -5.5 | closed: bounce opened at R2 | not opened under the current rules |  |
| Thu 05 Nov 08:00 | slow grind sell | Thu 05 Nov 08:15 | -10.9 | closed: bounce opened | +9.7 (profit lock) | -20.6 |
| Tue 10 Nov 05:00 | EMA pullback buy | Tue 10 Nov 07:55 | -0.4 | closed: bounce opened | -12.0 (stop) | +11.6 |
| Tue 10 Nov 06:10 | EMA pullback buy | Tue 10 Nov 07:55 | -2.3 | closed: bounce opened | -12.0 (stop) | +9.7 |
| Tue 10 Nov 07:20 | EMA pullback buy | Tue 10 Nov 07:55 | -5.7 | closed: bounce opened | -12.0 (stop) | +6.3 |
| Tue 10 Nov 16:25 | level reversal sell | Tue 10 Nov 17:00 | -1.9 | closed: bounce opened | -20.0 (stop) | +18.1 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Fri 30 Oct 08:15 | level reversal buy | opened only with the rule | +11.1 (closed: bounce opened) |
| Fri 30 Oct 16:15 | level reversal buy | opened only with the rule | -8.4 (closed: bounce opened) |
| Fri 30 Oct 16:45 | level reversal sell | opened only with the rule | -6.0 (scheduled close) |
| Wed 04 Nov 16:10 | slow grind sell | opened only with the rule | -5.5 (closed: bounce opened at R2) |
| Thu 05 Nov 10:20 | slow grind sell | opened only with the rule | -15.0 (stop) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (every bounce) + 2 + 3: 4 of 5 · 50% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:25 | slow grind sell | Mon 26 Oct 09:05 | +3.5 | closed: bounce opened | +20.0 (take profit) | -16.5 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 26 Oct 14:10 | Bollinger bounce buy | Mon 26 Oct 17:50 | +13.0 | closed: bounce opened | +7.2 (rejection at a level (half at the band +10.0)) | +5.9 |
| Tue 27 Oct 05:45 | slow grind sell | Tue 27 Oct 07:20 | +6.1 | closed: bounce opened | +20.0 (take profit) | -13.9 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 07:20 | +0.6 | closed: bounce opened | +50.0 (take profit) | -49.4 |
| Tue 27 Oct 09:55 | Bollinger bounce buy | Tue 27 Oct 12:35 | +7.1 | closed: bounce opened | -4.6 (rejection at a level) | +11.7 |
| Tue 27 Oct 12:35 | Bollinger bounce sell | Tue 27 Oct 16:40 | +12.8 | closed: bounce opened | +7.0 (rejection at a level (half at the band +8.0)) | +5.8 |
| Tue 27 Oct 16:05 | slow grind sell | Tue 27 Oct 16:40 | -0.6 | closed: bounce opened | +0.0 (scheduled close) | -0.6 |
| Tue 27 Oct 16:15 | EMA pullback sell | Tue 27 Oct 16:40 | -5.3 | closed: bounce opened | -12.0 (stop) | +6.7 |
| Wed 28 Oct 04:45 | slow grind sell | Wed 28 Oct 07:25 | +14.5 | closed: bounce opened | +10.0 (profit lock) | +4.5 |
| Wed 28 Oct 07:25 | Bollinger bounce buy | Wed 28 Oct 13:55 | +13.0 | closed: bounce opened | +11.4 (rejection at a level (half at the band +11.4)) | +1.6 |
| Wed 28 Oct 16:15 | level reversal buy | Wed 28 Oct 17:05 | +3.5 | closed: bounce opened | -1.7 (before big news) | +5.2 |
| Thu 29 Oct 22:05 | EMA pullback buy | Fri 30 Oct 07:45 | +16.8 | closed: bounce opened | +10.9 (scheduled close) | +5.9 |
| Fri 30 Oct 00:40 | EMA pullback buy | Fri 30 Oct 07:45 | +11.5 | closed: bounce opened | +30.0 (take profit) | -18.5 |
| Fri 30 Oct 07:10 | EMA pullback buy | Fri 30 Oct 07:45 | +0.7 | closed: bounce opened | +30.0 (take profit) | -29.3 |
| Fri 30 Oct 07:25 | level reversal buy | Fri 30 Oct 07:45 | -9.9 | closed: bounce opened | +20.0 (take profit) | -29.9 |
| Fri 30 Oct 08:15 | level reversal buy | Fri 30 Oct 10:40 | +11.1 | closed: bounce opened | not opened under the current rules |  |
| Fri 30 Oct 08:15 | slow grind buy | Fri 30 Oct 10:40 | +13.1 | closed: bounce opened | +20.0 (take profit) | -6.9 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 10:40 | Bollinger bounce sell | Fri 30 Oct 15:25 | +16.6 | closed: bounce opened | -1.8 (rejection at a level (half at the band -0.2)) | +18.4 |
| Fri 30 Oct 13:25 | level reversal sell | Fri 30 Oct 15:25 | +0.7 | closed: bounce opened | -4.1 (scheduled close) | +4.8 |
| Fri 30 Oct 15:25 | Bollinger bounce buy | Fri 30 Oct 16:25 | +5.8 | closed: bounce opened | +5.8 (rejection at a level (half at the band +6.5)) | +0.0 |
| Fri 30 Oct 16:15 | level reversal buy | Fri 30 Oct 16:25 | -8.4 | closed: bounce opened | not opened under the current rules |  |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 08:05 | EMA pullback buy | Tue 03 Nov 08:20 | -7.8 | closed: bounce opened | -12.0 (stop) | +4.2 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |
| Wed 04 Nov 08:30 | slow grind buy | Wed 04 Nov 10:40 | -6.7 | closed: bounce opened | -15.0 (stop) | +8.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 15:40 | +15.6 | closed: bounce opened | +15.6 (rejection at a level (half at the band +7.6)) | +0.0 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 15:40 | -7.5 | closed: bounce opened | -15.0 (stop) | +7.5 |
| Wed 04 Nov 16:10 | slow grind sell | Wed 04 Nov 17:10 | -5.5 | closed: bounce opened at R2 | not opened under the current rules |  |
| Thu 05 Nov 08:00 | slow grind sell | Thu 05 Nov 08:15 | -10.9 | closed: bounce opened | +9.7 (profit lock) | -20.6 |
| Tue 10 Nov 05:00 | EMA pullback buy | Tue 10 Nov 07:55 | -0.4 | closed: bounce opened | -12.0 (stop) | +11.6 |
| Tue 10 Nov 06:10 | EMA pullback buy | Tue 10 Nov 07:55 | -2.3 | closed: bounce opened | -12.0 (stop) | +9.7 |
| Tue 10 Nov 07:20 | EMA pullback buy | Tue 10 Nov 07:55 | -5.7 | closed: bounce opened | -12.0 (stop) | +6.3 |
| Tue 10 Nov 16:25 | level reversal sell | Tue 10 Nov 17:00 | -1.9 | closed: bounce opened | -20.0 (stop) | +18.1 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Fri 30 Oct 08:15 | level reversal buy | opened only with the rule | +11.1 (closed: bounce opened) |
| Fri 30 Oct 16:15 | level reversal buy | opened only with the rule | -8.4 (closed: bounce opened) |
| Fri 30 Oct 16:45 | level reversal sell | opened only with the rule | -6.0 (scheduled close) |
| Wed 04 Nov 16:10 | slow grind sell | opened only with the rule | -5.5 (closed: bounce opened at R2) |
| Thu 05 Nov 10:20 | slow grind sell | opened only with the rule | -15.0 (stop) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (every bounce) + 2 + 3: 4 of 5 · 75% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:25 | slow grind sell | Mon 26 Oct 09:05 | +3.5 | closed: bounce opened | +20.0 (take profit) | -16.5 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 09:05 | -2.7 | closed: bounce opened | +30.0 (take profit) | -32.7 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 26 Oct 14:10 | Bollinger bounce buy | Mon 26 Oct 17:50 | +13.0 | closed: bounce opened | +7.2 (rejection at a level (half at the band +10.0)) | +5.9 |
| Tue 27 Oct 05:45 | slow grind sell | Tue 27 Oct 07:20 | +6.1 | closed: bounce opened | +20.0 (take profit) | -13.9 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 07:20 | +0.6 | closed: bounce opened | +50.0 (take profit) | -49.4 |
| Tue 27 Oct 09:55 | Bollinger bounce buy | Tue 27 Oct 12:35 | +7.1 | closed: bounce opened | -4.6 (rejection at a level) | +11.7 |
| Tue 27 Oct 12:35 | Bollinger bounce sell | Tue 27 Oct 16:40 | +12.8 | closed: bounce opened | +7.0 (rejection at a level (half at the band +8.0)) | +5.8 |
| Tue 27 Oct 16:05 | slow grind sell | Tue 27 Oct 16:40 | -0.6 | closed: bounce opened | +0.0 (scheduled close) | -0.6 |
| Tue 27 Oct 16:15 | EMA pullback sell | Tue 27 Oct 16:40 | -5.3 | closed: bounce opened | -12.0 (stop) | +6.7 |
| Wed 28 Oct 04:45 | slow grind sell | Wed 28 Oct 07:25 | +14.5 | closed: bounce opened | +10.0 (profit lock) | +4.5 |
| Wed 28 Oct 07:25 | Bollinger bounce buy | Wed 28 Oct 13:55 | +13.0 | closed: bounce opened | +11.4 (rejection at a level (half at the band +11.4)) | +1.6 |
| Wed 28 Oct 16:15 | level reversal buy | Wed 28 Oct 17:05 | +3.5 | closed: bounce opened | -1.7 (before big news) | +5.2 |
| Thu 29 Oct 22:05 | EMA pullback buy | Fri 30 Oct 07:45 | +16.8 | closed: bounce opened | +10.9 (scheduled close) | +5.9 |
| Fri 30 Oct 00:40 | EMA pullback buy | Fri 30 Oct 07:45 | +11.5 | closed: bounce opened | +30.0 (take profit) | -18.5 |
| Fri 30 Oct 07:10 | EMA pullback buy | Fri 30 Oct 07:45 | +0.7 | closed: bounce opened | +30.0 (take profit) | -29.3 |
| Fri 30 Oct 07:25 | level reversal buy | Fri 30 Oct 07:45 | -9.9 | closed: bounce opened | +20.0 (take profit) | -29.9 |
| Fri 30 Oct 08:15 | level reversal buy | Fri 30 Oct 10:40 | +11.1 | closed: bounce opened | not opened under the current rules |  |
| Fri 30 Oct 08:15 | slow grind buy | Fri 30 Oct 10:40 | +13.1 | closed: bounce opened | +20.0 (take profit) | -6.9 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 09:15 | EMA pullback buy | Fri 30 Oct 10:40 | +4.5 | closed: bounce opened | -12.0 (stop) | +16.5 |
| Fri 30 Oct 10:40 | Bollinger bounce sell | Fri 30 Oct 15:25 | +16.6 | closed: bounce opened | -1.8 (rejection at a level (half at the band -0.2)) | +18.4 |
| Fri 30 Oct 13:25 | level reversal sell | Fri 30 Oct 15:25 | +0.7 | closed: bounce opened | -4.1 (scheduled close) | +4.8 |
| Fri 30 Oct 15:25 | Bollinger bounce buy | Fri 30 Oct 16:25 | +5.8 | closed: bounce opened | +5.8 (rejection at a level (half at the band +6.5)) | +0.0 |
| Fri 30 Oct 16:15 | level reversal buy | Fri 30 Oct 16:25 | -8.4 | closed: bounce opened | not opened under the current rules |  |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 08:30 | EMA pullback buy | Mon 02 Nov 09:25 | +15.2 | closed: bounce opened | -12.0 (stop) | +27.2 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 08:05 | EMA pullback buy | Tue 03 Nov 08:20 | -7.8 | closed: bounce opened | -12.0 (stop) | +4.2 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |
| Wed 04 Nov 08:30 | slow grind buy | Wed 04 Nov 10:40 | -6.7 | closed: bounce opened | -15.0 (stop) | +8.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 15:40 | +15.6 | closed: bounce opened | +15.6 (rejection at a level (half at the band +7.6)) | +0.0 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 15:40 | -7.5 | closed: bounce opened | -15.0 (stop) | +7.5 |
| Wed 04 Nov 16:10 | slow grind sell | Wed 04 Nov 17:10 | -5.5 | closed: bounce opened at R2 | not opened under the current rules |  |
| Thu 05 Nov 08:00 | slow grind sell | Thu 05 Nov 08:15 | -10.9 | closed: bounce opened | +9.7 (profit lock) | -20.6 |
| Tue 10 Nov 05:00 | EMA pullback buy | Tue 10 Nov 07:55 | -0.4 | closed: bounce opened | -12.0 (stop) | +11.6 |
| Tue 10 Nov 06:10 | EMA pullback buy | Tue 10 Nov 07:55 | -2.3 | closed: bounce opened | -12.0 (stop) | +9.7 |
| Tue 10 Nov 07:20 | EMA pullback buy | Tue 10 Nov 07:55 | -5.7 | closed: bounce opened | -12.0 (stop) | +6.3 |
| Tue 10 Nov 16:25 | level reversal sell | Tue 10 Nov 17:00 | -1.9 | closed: bounce opened | -20.0 (stop) | +18.1 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Fri 30 Oct 08:15 | level reversal buy | opened only with the rule | +11.1 (closed: bounce opened) |
| Fri 30 Oct 16:15 | level reversal buy | opened only with the rule | -8.4 (closed: bounce opened) |
| Fri 30 Oct 16:45 | level reversal sell | opened only with the rule | -6.0 (scheduled close) |
| Wed 04 Nov 16:10 | slow grind sell | opened only with the rule | -5.5 (closed: bounce opened at R2) |
| Thu 05 Nov 10:20 | slow grind sell | opened only with the rule | -15.0 (stop) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (S2/S3/R2/R3) + 2 + 3: 2 of 5 · 25% back · flat < 3

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 17:10 | +15.8 | closed: bounce opened at R2 | +15.6 (rejection at a level (half at the band +7.6)) | +0.2 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 17:10 | -7.0 | closed: bounce opened at R2 | -15.0 (stop) | +8.0 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 15:00 | +17.2 | closed: hourly exhaustion | +50.0 (take profit) | -32.8 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 15:00 | -7.2 | closed: hourly exhaustion | -15.0 (stop) | +7.8 |
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 22:00 | +7.7 | closed: hourly exhaustion | not opened under the current rules |  |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | +7.7 (closed: hourly exhaustion) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Fri 30 Oct 16:25 | Bollinger bounce sell | opened only under the current rules | +6.4 (rejection at a level (half at the band +7.3)) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (S2/S3/R2/R3) + 2 + 3: 2 of 5 · 25% back · flat < 5

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 06:05 | slow grind sell | Mon 26 Oct 07:00 | -2.6 | closed: hourly exhaustion | +10.0 (profit lock) | -12.6 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Thu 29 Oct 14:45 | breakout buy | Thu 29 Oct 20:00 | +14.8 | closed: hourly exhaustion | +50.0 (take profit) | -35.2 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 17:10 | +15.8 | closed: bounce opened at R2 | +15.6 (rejection at a level (half at the band +7.6)) | +0.2 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 17:10 | -7.0 | closed: bounce opened at R2 | -15.0 (stop) | +8.0 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 14:00 | +27.0 | closed: hourly exhaustion | +50.0 (take profit) | -23.0 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 14:00 | +2.6 | closed: hourly exhaustion | -15.0 (stop) | +17.6 |
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 22:00 | +7.7 | closed: hourly exhaustion | not opened under the current rules |  |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 07:40 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Thu 29 Oct 20:10 | breakout buy | opened only with the rule | +50.0 (take profit) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | +7.7 (closed: hourly exhaustion) |
| Mon 26 Oct 08:25 | slow grind sell | opened only under the current rules | +20.0 (take profit) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Fri 30 Oct 16:25 | Bollinger bounce sell | opened only under the current rules | +6.4 (rejection at a level (half at the band +7.3)) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (S2/S3/R2/R3) + 2 + 3: 2 of 5 · 25% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 06:05 | slow grind sell | Mon 26 Oct 07:00 | -2.6 | closed: hourly exhaustion | +10.0 (profit lock) | -12.6 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 13:00 | -5.9 | closed: hourly exhaustion | +50.0 (take profit) | -55.9 |
| Thu 29 Oct 14:45 | breakout buy | Thu 29 Oct 20:00 | +14.8 | closed: hourly exhaustion | +50.0 (take profit) | -35.2 |
| Thu 29 Oct 20:10 | breakout buy | Thu 29 Oct 22:00 | -8.0 | closed: hourly exhaustion | not opened under the current rules |  |
| Thu 29 Oct 22:05 | EMA pullback buy | Fri 30 Oct 00:00 | -6.7 | closed: hourly exhaustion | +10.9 (scheduled close) | -17.6 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |
| Tue 03 Nov 18:05 | EMA pullback buy | Tue 03 Nov 19:00 | -2.9 | closed: hourly exhaustion | -12.0 (stop) | +9.1 |
| Tue 03 Nov 18:05 | EMA pullback buy | Tue 03 Nov 19:00 | -2.9 | closed: hourly exhaustion | -12.0 (stop) | +9.1 |
| Tue 03 Nov 18:05 | breakout buy | Tue 03 Nov 19:00 | -1.6 | closed: hourly exhaustion | -12.0 (stop) | +10.4 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 17:10 | +15.8 | closed: bounce opened at R2 | +15.6 (rejection at a level (half at the band +7.6)) | +0.2 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 17:10 | -7.0 | closed: bounce opened at R2 | -15.0 (stop) | +8.0 |
| Thu 05 Nov 18:35 | breakout sell | Thu 05 Nov 20:00 | +8.4 | closed: hourly exhaustion | +50.0 (take profit) | -41.6 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 14:00 | +27.0 | closed: hourly exhaustion | +50.0 (take profit) | -23.0 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 14:00 | +2.6 | closed: hourly exhaustion | -15.0 (stop) | +17.6 |
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 22:00 | +7.7 | closed: hourly exhaustion | not opened under the current rules |  |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Tue 10 Nov 05:00 | EMA pullback buy | Tue 10 Nov 06:00 | -5.8 | closed: hourly exhaustion | -12.0 (stop) | +6.2 |
| Tue 10 Nov 06:10 | EMA pullback buy | Tue 10 Nov 07:00 | -4.8 | closed: hourly exhaustion | -12.0 (stop) | +7.2 |
| Tue 10 Nov 07:20 | EMA pullback buy | Tue 10 Nov 08:00 | -4.8 | closed: hourly exhaustion | -12.0 (stop) | +7.2 |
| Tue 10 Nov 09:10 | breakout sell | Tue 10 Nov 12:00 | +6.3 | closed: hourly exhaustion | +50.0 (take profit) | -43.7 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 07:40 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Thu 29 Oct 20:10 | breakout buy | opened only with the rule | -8.0 (closed: hourly exhaustion) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | +7.7 (closed: hourly exhaustion) |
| Tue 10 Nov 13:10 | breakout sell | opened only with the rule | -12.0 (stop) |
| Mon 26 Oct 08:25 | slow grind sell | opened only under the current rules | +20.0 (take profit) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Fri 30 Oct 16:25 | Bollinger bounce sell | opened only under the current rules | +6.4 (rejection at a level (half at the band +7.3)) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (S2/S3/R2/R3) + 2 + 3: 2 of 5 · 50% back · flat < 3

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 17:10 | +15.8 | closed: bounce opened at R2 | +15.6 (rejection at a level (half at the band +7.6)) | +0.2 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 17:10 | -7.0 | closed: bounce opened at R2 | -15.0 (stop) | +8.0 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 15:00 | +17.2 | closed: hourly exhaustion | +50.0 (take profit) | -32.8 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 15:00 | -7.2 | closed: hourly exhaustion | -15.0 (stop) | +7.8 |
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 23:00 | -2.8 | closed: hourly exhaustion | not opened under the current rules |  |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | -2.8 (closed: hourly exhaustion) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Fri 30 Oct 16:25 | Bollinger bounce sell | opened only under the current rules | +6.4 (rejection at a level (half at the band +7.3)) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (S2/S3/R2/R3) + 2 + 3: 2 of 5 · 50% back · flat < 5

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 06:05 | slow grind sell | Mon 26 Oct 07:00 | -2.6 | closed: hourly exhaustion | +10.0 (profit lock) | -12.6 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 17:10 | +15.8 | closed: bounce opened at R2 | +15.6 (rejection at a level (half at the band +7.6)) | +0.2 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 17:10 | -7.0 | closed: bounce opened at R2 | -15.0 (stop) | +8.0 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 15:00 | +17.2 | closed: hourly exhaustion | +50.0 (take profit) | -32.8 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 15:00 | -7.2 | closed: hourly exhaustion | -15.0 (stop) | +7.8 |
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 23:00 | -2.8 | closed: hourly exhaustion | not opened under the current rules |  |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 07:40 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | -2.8 (closed: hourly exhaustion) |
| Mon 26 Oct 08:25 | slow grind sell | opened only under the current rules | +20.0 (take profit) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Fri 30 Oct 16:25 | Bollinger bounce sell | opened only under the current rules | +6.4 (rejection at a level (half at the band +7.3)) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (S2/S3/R2/R3) + 2 + 3: 2 of 5 · 50% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 06:05 | slow grind sell | Mon 26 Oct 07:00 | -2.6 | closed: hourly exhaustion | +10.0 (profit lock) | -12.6 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 13:00 | -5.9 | closed: hourly exhaustion | +50.0 (take profit) | -55.9 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 17:10 | +15.8 | closed: bounce opened at R2 | +15.6 (rejection at a level (half at the band +7.6)) | +0.2 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 17:10 | -7.0 | closed: bounce opened at R2 | -15.0 (stop) | +8.0 |
| Thu 05 Nov 18:35 | breakout sell | Fri 06 Nov 00:00 | +12.2 | closed: hourly exhaustion | +50.0 (take profit) | -37.8 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 15:00 | +17.2 | closed: hourly exhaustion | +50.0 (take profit) | -32.8 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 15:00 | -7.2 | closed: hourly exhaustion | -15.0 (stop) | +7.8 |
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 23:00 | -2.8 | closed: hourly exhaustion | not opened under the current rules |  |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 07:40 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | -2.8 (closed: hourly exhaustion) |
| Mon 26 Oct 08:25 | slow grind sell | opened only under the current rules | +20.0 (take profit) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Fri 30 Oct 16:25 | Bollinger bounce sell | opened only under the current rules | +6.4 (rejection at a level (half at the band +7.3)) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (S2/S3/R2/R3) + 2 + 3: 2 of 5 · 75% back · flat < 3

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 17:10 | +15.8 | closed: bounce opened at R2 | +15.6 (rejection at a level (half at the band +7.6)) | +0.2 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 17:10 | -7.0 | closed: bounce opened at R2 | -15.0 (stop) | +8.0 |
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Fri 30 Oct 16:25 | Bollinger bounce sell | opened only under the current rules | +6.4 (rejection at a level (half at the band +7.3)) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (S2/S3/R2/R3) + 2 + 3: 2 of 5 · 75% back · flat < 5

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 06:05 | slow grind sell | Mon 26 Oct 07:00 | -2.6 | closed: hourly exhaustion | +10.0 (profit lock) | -12.6 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 17:10 | +15.8 | closed: bounce opened at R2 | +15.6 (rejection at a level (half at the band +7.6)) | +0.2 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 17:10 | -7.0 | closed: bounce opened at R2 | -15.0 (stop) | +8.0 |
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 07:40 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Mon 26 Oct 08:25 | slow grind sell | opened only under the current rules | +20.0 (take profit) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Fri 30 Oct 16:25 | Bollinger bounce sell | opened only under the current rules | +6.4 (rejection at a level (half at the band +7.3)) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (S2/S3/R2/R3) + 2 + 3: 2 of 5 · 75% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 06:05 | slow grind sell | Mon 26 Oct 07:00 | -2.6 | closed: hourly exhaustion | +10.0 (profit lock) | -12.6 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 13:00 | -5.9 | closed: hourly exhaustion | +50.0 (take profit) | -55.9 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 17:10 | +15.8 | closed: bounce opened at R2 | +15.6 (rejection at a level (half at the band +7.6)) | +0.2 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 17:10 | -7.0 | closed: bounce opened at R2 | -15.0 (stop) | +8.0 |
| Mon 09 Nov 15:45 | slow grind sell | Mon 09 Nov 16:00 | -3.7 | closed: hourly exhaustion | -15.0 (stop) | +11.3 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 07:40 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 09:30 | slow grind sell | opened only with the rule | +10.0 (profit lock) |
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Mon 26 Oct 08:25 | slow grind sell | opened only under the current rules | +20.0 (take profit) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Fri 30 Oct 16:25 | Bollinger bounce sell | opened only under the current rules | +6.4 (rejection at a level (half at the band +7.3)) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (S2/S3/R2/R3) + 2 + 3: 3 of 5 · 25% back · flat < 3

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 17:10 | +15.8 | closed: bounce opened at R2 | +15.6 (rejection at a level (half at the band +7.6)) | +0.2 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 17:10 | -7.0 | closed: bounce opened at R2 | -15.0 (stop) | +8.0 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 15:00 | +17.2 | closed: hourly exhaustion | +50.0 (take profit) | -32.8 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 15:00 | -7.2 | closed: hourly exhaustion | -15.0 (stop) | +7.8 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 22:00 | +7.7 | closed: hourly exhaustion | not opened under the current rules |  |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | +7.7 (closed: hourly exhaustion) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Fri 30 Oct 16:25 | Bollinger bounce sell | opened only under the current rules | +6.4 (rejection at a level (half at the band +7.3)) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (S2/S3/R2/R3) + 2 + 3: 3 of 5 · 25% back · flat < 5

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 17:10 | +15.8 | closed: bounce opened at R2 | +15.6 (rejection at a level (half at the band +7.6)) | +0.2 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 17:10 | -7.0 | closed: bounce opened at R2 | -15.0 (stop) | +8.0 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 14:00 | +27.0 | closed: hourly exhaustion | +50.0 (take profit) | -23.0 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 14:00 | +2.6 | closed: hourly exhaustion | -15.0 (stop) | +17.6 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 22:00 | +7.7 | closed: hourly exhaustion | not opened under the current rules |  |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | +7.7 (closed: hourly exhaustion) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Fri 30 Oct 16:25 | Bollinger bounce sell | opened only under the current rules | +6.4 (rejection at a level (half at the band +7.3)) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (S2/S3/R2/R3) + 2 + 3: 3 of 5 · 25% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 13:00 | -5.9 | closed: hourly exhaustion | +50.0 (take profit) | -55.9 |
| Thu 29 Oct 14:45 | breakout buy | Thu 29 Oct 22:00 | +19.2 | closed: hourly exhaustion | +50.0 (take profit) | -30.8 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 17:10 | +15.8 | closed: bounce opened at R2 | +15.6 (rejection at a level (half at the band +7.6)) | +0.2 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 17:10 | -7.0 | closed: bounce opened at R2 | -15.0 (stop) | +8.0 |
| Thu 05 Nov 18:35 | breakout sell | Thu 05 Nov 20:00 | +8.4 | closed: hourly exhaustion | +50.0 (take profit) | -41.6 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 14:00 | +27.0 | closed: hourly exhaustion | +50.0 (take profit) | -23.0 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 14:00 | +2.6 | closed: hourly exhaustion | -15.0 (stop) | +17.6 |
| Mon 09 Nov 19:35 | breakout buy | Mon 09 Nov 22:00 | +7.7 | closed: hourly exhaustion | not opened under the current rules |  |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Mon 09 Nov 21:00 | EMA pullback buy | Mon 09 Nov 22:00 | -6.1 | closed: hourly exhaustion | -12.0 (stop) | +5.9 |
| Tue 10 Nov 05:00 | EMA pullback buy | Tue 10 Nov 07:00 | -2.9 | closed: hourly exhaustion | -12.0 (stop) | +9.1 |
| Tue 10 Nov 06:10 | EMA pullback buy | Tue 10 Nov 07:00 | -4.8 | closed: hourly exhaustion | -12.0 (stop) | +7.2 |
| Tue 10 Nov 07:20 | EMA pullback buy | Tue 10 Nov 08:00 | -4.8 | closed: hourly exhaustion | -12.0 (stop) | +7.2 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | +7.7 (closed: hourly exhaustion) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Fri 30 Oct 16:25 | Bollinger bounce sell | opened only under the current rules | +6.4 (rejection at a level (half at the band +7.3)) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (S2/S3/R2/R3) + 2 + 3: 3 of 5 · 50% back · flat < 3

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 17:10 | +15.8 | closed: bounce opened at R2 | +15.6 (rejection at a level (half at the band +7.6)) | +0.2 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 17:10 | -7.0 | closed: bounce opened at R2 | -15.0 (stop) | +8.0 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 15:00 | +17.2 | closed: hourly exhaustion | +50.0 (take profit) | -32.8 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 15:00 | -7.2 | closed: hourly exhaustion | -15.0 (stop) | +7.8 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | -12.0 (stop) |
| Tue 10 Nov 13:10 | breakout sell | opened only with the rule | -12.0 (stop) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Fri 30 Oct 16:25 | Bollinger bounce sell | opened only under the current rules | +6.4 (rejection at a level (half at the band +7.3)) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |
| Tue 10 Nov 09:10 | breakout sell | opened only under the current rules | +50.0 (take profit) |

### 1 (S2/S3/R2/R3) + 2 + 3: 3 of 5 · 50% back · flat < 5

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 17:10 | +15.8 | closed: bounce opened at R2 | +15.6 (rejection at a level (half at the band +7.6)) | +0.2 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 17:10 | -7.0 | closed: bounce opened at R2 | -15.0 (stop) | +8.0 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 15:00 | +17.2 | closed: hourly exhaustion | +50.0 (take profit) | -32.8 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 15:00 | -7.2 | closed: hourly exhaustion | -15.0 (stop) | +7.8 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | -12.0 (stop) |
| Tue 10 Nov 13:10 | breakout sell | opened only with the rule | -12.0 (stop) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Fri 30 Oct 16:25 | Bollinger bounce sell | opened only under the current rules | +6.4 (rejection at a level (half at the band +7.3)) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |
| Tue 10 Nov 09:10 | breakout sell | opened only under the current rules | +50.0 (take profit) |

### 1 (S2/S3/R2/R3) + 2 + 3: 3 of 5 · 50% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 13:00 | -5.9 | closed: hourly exhaustion | +50.0 (take profit) | -55.9 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 17:10 | +15.8 | closed: bounce opened at R2 | +15.6 (rejection at a level (half at the band +7.6)) | +0.2 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 17:10 | -7.0 | closed: bounce opened at R2 | -15.0 (stop) | +8.0 |
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 15:00 | +17.2 | closed: hourly exhaustion | +50.0 (take profit) | -32.8 |
| Mon 09 Nov 09:35 | slow grind buy | Mon 09 Nov 15:00 | -7.2 | closed: hourly exhaustion | -15.0 (stop) | +7.8 |
| Mon 09 Nov 19:35 | breakout buy | Tue 10 Nov 10:00 | -5.1 | closed: hourly exhaustion | not opened under the current rules |  |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Mon 09 Nov 19:35 | breakout buy | opened only with the rule | -5.1 (closed: hourly exhaustion) |
| Tue 10 Nov 11:50 | breakout sell | opened only with the rule | +50.0 (take profit) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Fri 30 Oct 16:25 | Bollinger bounce sell | opened only under the current rules | +6.4 (rejection at a level (half at the band +7.3)) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |
| Tue 10 Nov 09:10 | breakout sell | opened only under the current rules | +50.0 (take profit) |

### 1 (S2/S3/R2/R3) + 2 + 3: 3 of 5 · 75% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 13:00 | -5.9 | closed: hourly exhaustion | +50.0 (take profit) | -55.9 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 17:10 | +15.8 | closed: bounce opened at R2 | +15.6 (rejection at a level (half at the band +7.6)) | +0.2 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 17:10 | -7.0 | closed: bounce opened at R2 | -15.0 (stop) | +8.0 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Fri 30 Oct 16:25 | Bollinger bounce sell | opened only under the current rules | +6.4 (rejection at a level (half at the band +7.3)) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (S2/S3/R2/R3) + 2 + 3: 4 of 5 · 25% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 13:00 | -5.9 | closed: hourly exhaustion | +50.0 (take profit) | -55.9 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 17:10 | +15.8 | closed: bounce opened at R2 | +15.6 (rejection at a level (half at the band +7.6)) | +0.2 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 17:10 | -7.0 | closed: bounce opened at R2 | -15.0 (stop) | +8.0 |
| Tue 10 Nov 05:00 | EMA pullback buy | Tue 10 Nov 08:00 | +0.5 | closed: hourly exhaustion | -12.0 (stop) | +12.5 |
| Tue 10 Nov 06:10 | EMA pullback buy | Tue 10 Nov 08:00 | -1.4 | closed: hourly exhaustion | -12.0 (stop) | +10.6 |
| Tue 10 Nov 07:20 | EMA pullback buy | Tue 10 Nov 08:00 | -4.8 | closed: hourly exhaustion | -12.0 (stop) | +7.2 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Fri 30 Oct 16:25 | Bollinger bounce sell | opened only under the current rules | +6.4 (rejection at a level (half at the band +7.3)) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (S2/S3/R2/R3) + 2 + 3: 4 of 5 · 50% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 13:00 | -5.9 | closed: hourly exhaustion | +50.0 (take profit) | -55.9 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 17:10 | +15.8 | closed: bounce opened at R2 | +15.6 (rejection at a level (half at the band +7.6)) | +0.2 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 17:10 | -7.0 | closed: bounce opened at R2 | -15.0 (stop) | +8.0 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Fri 30 Oct 16:25 | Bollinger bounce sell | opened only under the current rules | +6.4 (rejection at a level (half at the band +7.3)) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |

### 1 (S2/S3/R2/R3) + 2 + 3: 4 of 5 · 75% back · flat < 8

| Opened | Trade | Closed by the rule | Pips with the rule | How | Under the current rules | Difference |
|---|---|---|---:|---|---|---:|
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 08:35 | EMA pullback sell | Mon 26 Oct 14:10 | +12.0 | closed: bounce opened at S2 | +30.0 (take profit) | -18.0 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | EMA pullback sell | Mon 26 Oct 14:10 | -4.8 | closed: bounce opened at S2 | -12.0 (stop) | +7.2 |
| Mon 26 Oct 13:55 | level reversal sell | Mon 26 Oct 14:10 | -1.0 | closed: bounce opened at S2 | -12.7 (stop) | +11.7 |
| Tue 27 Oct 07:00 | breakout sell | Tue 27 Oct 13:00 | -5.9 | closed: hourly exhaustion | +50.0 (take profit) | -55.9 |
| Mon 02 Nov 09:25 | Bollinger bounce sell | Mon 02 Nov 18:55 | +28.0 | closed: bounce opened at R3 | +25.8 (rejection at a level (half at the band +26.5)) | +2.3 |
| Tue 03 Nov 10:15 | breakout sell | Tue 03 Nov 11:00 | -6.0 | closed: hourly exhaustion | -12.0 (stop) | +6.0 |
| Wed 04 Nov 13:25 | Bollinger bounce sell | Wed 04 Nov 17:10 | +15.8 | closed: bounce opened at R2 | +15.6 (rejection at a level (half at the band +7.6)) | +0.2 |
| Wed 04 Nov 15:35 | slow grind sell | Wed 04 Nov 17:10 | -7.0 | closed: bounce opened at R2 | -15.0 (stop) | +8.0 |

Trades that opened in only one of the two runs:

| Opened | Trade | | Pips |
|---|---|---|---:|
| Mon 26 Oct 14:10 | level reversal buy | opened only with the rule | +20.0 (take profit) |
| Mon 26 Oct 14:45 | level reversal buy | opened only under the current rules | -4.6 (scheduled close) |
| Wed 28 Oct 10:35 | Bollinger bounce buy | opened only under the current rules | -12.0 (stop) |
| Wed 28 Oct 11:15 | Bollinger bounce buy | opened only under the current rules | +7.4 (rejection at a level (half at the band +10.1)) |
| Wed 28 Oct 15:20 | Bollinger bounce sell | opened only under the current rules | -5.4 (rejection at a level) |
| Wed 28 Oct 15:50 | Bollinger bounce sell | opened only under the current rules | -7.7 (rejection at a level) |
| Fri 30 Oct 16:25 | Bollinger bounce sell | opened only under the current rules | +6.4 (rejection at a level (half at the band +7.3)) |
| Tue 10 Nov 08:45 | Bollinger bounce sell | opened only under the current rules | +12.5 (rejection at a level (half at the band +3.2)) |
