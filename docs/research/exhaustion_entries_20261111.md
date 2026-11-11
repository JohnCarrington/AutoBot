# Exhaustion as a reason not to open trend trades, 25 October to 11 November 2026

Wednesday 11 November 2026, UK. This is read-only research: **nothing in the bot was changed**. There were no IG calls and no restart, and nothing was written outside `data/research/`.

## Summary

**The question.** While the owner's hourly signs that a trend is running out are showing, does stopping new trend trades in that direction help? The trend trades are the EMA pullback, the slow grind and the breakout. Open trades are not touched.

The owner's words for a buy trend are: "several candles with buyside wicks, well below the Bollinger band, 100 and 200 EMA completely flat". For sells, the mirror. No numbers were given, so all 27 versions are shown:

- "several" is 2, 3 or 4 of the last 5 hourly candles;
- "well below the band" is a quarter, a half or three quarters of the way back to the middle band;
- "flat" is under 3, 5 or 8 pips over 12 hours.

**The current rules make +1,322.0 pips in 177 trades** (91 won, 85 lost, 1 at 0), from the week's open on Sunday 25 October to the last stored candle, which ended at 15:15 UK time on Wednesday 11 November:

- 25 to 30 October: +224.9
- 1 to 6 November: +811.0
- 8 November to 11 November 15:15: +286.0

**The results:**

- **17 versions do better, by 5.0 to 40.1 pips.** 3 do worse, by 5.0, 55.0 and 106.8. 7 change nothing.
- **The rule rarely acts.** The versions stop 0 to 11 of the current rules' 177 trades. Most stop 1 or 2.
- **Most of the gain is one trade.** The slow grind sell at 15:45 on Monday 9 November lost 15.0. It is stopped in 18 versions: every one with 2 or 3 of 5 wicks. It is the whole of the +15.0 that 9 versions make. Some of those 9 also stop the 29 October breakout, which comes back the same evening (see the next point).
- **The 29 October breakout buy.** It made +50.0, and the signs were showing when it triggered at 14:45 (4 of 5 wicks). 18 versions stop it. In 16 of them, the breakout comes again at 20:10, once the signs have gone, and makes the same +50.0, so stopping it costs nothing, but only by luck of timing. In the other two (2 · a quarter · under 5 or 8), the 20:10 entry is stopped too.
- **The best versions, 3 of 5 with "flat" under 8:**
  - a quarter back: +40.1 (172 trades);
  - a half back: +39.0 (174 trades).
  - Both stop the two breakouts on Tuesday 3 November (−12.0 each), as well as the 9 November slow grind sell.
  - Both stop the 29 October breakout (+50.0), which then comes again at 20:10.
  - The quarter-back version also stops the 07:20 EMA pullback buy on 10 November (−12.0) and an EMA pullback buy on 29 October that made +10.9.
- **Only the three-quarters-back versions stopped losers on balance.** Their stopped trades made −5.0 to −27.0 under the current rules, so the result is that much better (+5.0 to +27.0). Every quarter-back and half-back version also stopped trades that were winning.
- **The worst version is 2 of 5 · a quarter back · flat under 8: −106.8.** It stops 11 trades that made +157.9 between them. They include:
  - the slow grind sell at 13:30 on Tuesday 10 November, which made +100.0 (another slow grind sell opened at 14:30 and made +41.1);
  - slow grind sells on 26 and 27 October (+10.0 and +20.0);
  - the 29 October breakout buy (+50.0), which is stopped again at 20:10;
  - EMA pullback buys on 29 and 30 October (+10.9 and +30.0).
- **Tuesday 10 November is the same as the current rules (+123.4) in 25 of the 27 versions.**
  - The three EMA pullback buys that lost 12.0 each that morning (05:00, 06:10 and 07:20) were stopped only by the loosest versions.
  - When they triggered, the 100 EMA had moved 6.0 to 6.4 pips in 12 hours and the 200 EMA 4.2 to 4.4. That is not "flat" under 3 or 5. At most 3 of the last 5 hourly candles had upper wicks.
  - The loosest version (2 · a quarter · under 8) stops the 06:10 and 07:20 buys, saving 24.0. But it also stops the 13:30 slow grind sell, which made +100.0, so its Tuesday is +88.5. 3 · a quarter · under 8 stops only the 07:20 buy, and its Tuesday is +135.4.
- **No candle reached both a trade's stop and its target** in any of the 29 runs, so stop first and target first give the same result everywhere.

**What this does and doesn't show.** The rule saw too few cases in these 13 trading days to judge it. The best result rests on 4 to 7 stopped trades, and the 29 October breakout only came out level because it came again later. The tighter versions do little harm, but also little good, mostly the one trade on 9 November. The loosest versions stop strong trend trades early in a move: the sign "100 and 200 EMA flat" is still true for some hours after a new trend starts, because the slow EMAs turn late. All 27 versions are shown and none is picked.

## How it was done

- **Candles.** A read-only copy of the bot's own IG candle store, taken at 15:19 UTC today (`data/research/replay_stores/live_copy_20261111_1519/`). It holds IG's real buy and sell prices and ends with the candle that finished at 15:15 UTC.
- **Code.** A frozen copy of the committed code, `04b3a83`: the current rules, with the strategies reading the candle store afresh on every call. The replay is the research mode (`research.long_replay`), with the same engine, strategies, safety rules, paper order sender and trade manager as the bot's own replay, run week by week.
- **Switches and news.**
  - Switches: today's `.env` (`STOP_LOSS_PIPS=12`, `TAKE_PROFIT_PIPS=100`, every strategy on), with `TRADING` off for the replay.
  - Take profits and stops: as the bot's own code gives each trade in the replay.
  - News rules: Finnhub's past calendar, as in the earlier reports.
- **The research copy matches the bot's own code.**
  - Unpatched, the bot's code gives 177 trades and +1,322.0.
  - With no rule switched on, the research version gives the same 177 trades, trade for trade, with the same exits, times and pips. Its trade manager step is the one from the earlier reports; the trade manager has not changed since.
  - The rule is a patch in the research process only, applied to the bot's functions while the replay runs. The scripts and every run's trades are in `data/research/replay/exhaustion_entries_20261111/`. The repository commits only this file.
- **The rule.**
  - When a slow grind, EMA pullback or breakout passes all of the bot's own rules and is about to be sent, the signs are read as of the last hourly candle that had finished before the 5-minute candle in which the entry was reached.
  - The signs are read on the bot's own stored hourly candles, at the sell price (the chart price).
  - If all three signs show for that direction, the trade is not opened. Bollinger bounce, range trade and level reversal entries are never stopped, and open trades are never closed.
  - **"Several candles with buyside wicks":** at least 2, 3 or 4 of the last 5 hourly candles have an upper wick (for a sell, a lower wick) at least as long as their body. This is the same reading as in the earlier reports.
  - **"Well below the Bollinger band":** the last hourly candle closed at least a quarter, a half or three quarters of the way back from the upper band (20, 2) to the middle band. For a sell, it is up from the lower band. A close beyond the middle band counts too: it is more than all the way back.
  - **"The 100 and 200 EMA completely flat":** each moved less than 3, 5 or 8 pips between the hourly closes 12 hours apart.
- **Prices.**
  - Entries are at IG's buy price (buys) or sell price (sells), from the candles.
  - Stops and take profits fill at their level, or at the candle's open if it opened past them.
  - No spread is added: IG's buy and sell prices already include it.
- **A stopped entry can come again.** If the strategy's setup is still there on a later candle, or a new one forms, it is tried again. If the signs have gone by then, it opens. These later trades are listed under "Trades that opened because of a stopped entry". The "other attempts stopped" column counts entries stopped that the current rules never opened, mostly retries of one already stopped.
- **Trades still open at the last candle** are counted at that candle's close. In the current rules there are 2: a breakout sell from 13:10 UTC and a Bollinger bounce buy from 15:10 UTC.
- **Win and loss:** a trade with more than 0 pips is a win, below 0 a loss.
- **Times** are UK times (GMT; British Summer Time until 25 October).

## Results

### All 27 versions

| Version: wicks · back from the band · EMAs flat | Trades | Won | Lost | Pips, stop first | Pips, target first | Against current | Current rules' trades stopped | What they made under the current rules | Other attempts stopped |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Current rules** | 177 | 91 | 85 | **+1,322.0** | **+1,322.0** | | | | |
| 2 of 5 · a quarter back · flat < 3 | 176 | 91 | 84 | **+1,337.0** | **+1,337.0** | +15.0 | 2 | +35.0 | 0 |
| 2 of 5 · a quarter back · flat < 5 | 174 | 89 | 84 | **+1,267.0** | **+1,267.0** | -55.0 | 4 | +65.0 | 4 |
| 2 of 5 · a quarter back · flat < 8 | 168 | 87 | 80 | **+1,215.2** | **+1,215.2** | -106.8 | 11 | +157.9 | 7 |
| 2 of 5 · a half back · flat < 3 | 176 | 91 | 84 | **+1,337.0** | **+1,337.0** | +15.0 | 2 | +35.0 | 0 |
| 2 of 5 · a half back · flat < 5 | 175 | 90 | 84 | **+1,317.0** | **+1,317.0** | -5.0 | 4 | +65.0 | 3 |
| 2 of 5 · a half back · flat < 8 | 173 | 90 | 82 | **+1,341.0** | **+1,341.0** | +19.0 | 6 | +41.0 | 3 |
| 2 of 5 · three quarters back · flat < 3 | 176 | 91 | 84 | **+1,337.0** | **+1,337.0** | +15.0 | 1 | -15.0 | 0 |
| 2 of 5 · three quarters back · flat < 5 | 175 | 90 | 84 | **+1,327.0** | **+1,327.0** | +5.0 | 2 | -5.0 | 1 |
| 2 of 5 · three quarters back · flat < 8 | 174 | 90 | 83 | **+1,339.0** | **+1,339.0** | +17.0 | 3 | -17.0 | 1 |
| 3 of 5 · a quarter back · flat < 3 | 176 | 91 | 84 | **+1,337.0** | **+1,337.0** | +15.0 | 2 | +35.0 | 0 |
| 3 of 5 · a quarter back · flat < 5 | 176 | 91 | 84 | **+1,337.0** | **+1,337.0** | +15.0 | 2 | +35.0 | 0 |
| 3 of 5 · a quarter back · flat < 8 | 172 | 90 | 81 | **+1,362.1** | **+1,362.1** | +40.1 | 6 | +9.9 | 1 |
| 3 of 5 · a half back · flat < 3 | 176 | 91 | 84 | **+1,337.0** | **+1,337.0** | +15.0 | 2 | +35.0 | 0 |
| 3 of 5 · a half back · flat < 5 | 176 | 91 | 84 | **+1,337.0** | **+1,337.0** | +15.0 | 2 | +35.0 | 0 |
| 3 of 5 · a half back · flat < 8 | 174 | 91 | 82 | **+1,361.0** | **+1,361.0** | +39.0 | 4 | +11.0 | 0 |
| 3 of 5 · three quarters back · flat < 3 | 176 | 91 | 84 | **+1,337.0** | **+1,337.0** | +15.0 | 1 | -15.0 | 0 |
| 3 of 5 · three quarters back · flat < 5 | 176 | 91 | 84 | **+1,337.0** | **+1,337.0** | +15.0 | 1 | -15.0 | 0 |
| 3 of 5 · three quarters back · flat < 8 | 175 | 91 | 83 | **+1,349.0** | **+1,349.0** | +27.0 | 2 | -27.0 | 0 |
| 4 of 5 · a quarter back · flat < 3 | 177 | 91 | 85 | **+1,322.0** | **+1,322.0** | 0 | 1 | +50.0 | 0 |
| 4 of 5 · a quarter back · flat < 5 | 177 | 91 | 85 | **+1,322.0** | **+1,322.0** | 0 | 1 | +50.0 | 0 |
| 4 of 5 · a quarter back · flat < 8 | 176 | 91 | 84 | **+1,334.0** | **+1,334.0** | +12.0 | 2 | +38.0 | 0 |
| 4 of 5 · a half back · flat < 3 | 177 | 91 | 85 | **+1,322.0** | **+1,322.0** | 0 | 1 | +50.0 | 0 |
| 4 of 5 · a half back · flat < 5 | 177 | 91 | 85 | **+1,322.0** | **+1,322.0** | 0 | 1 | +50.0 | 0 |
| 4 of 5 · a half back · flat < 8 | 176 | 91 | 84 | **+1,334.0** | **+1,334.0** | +12.0 | 2 | +38.0 | 0 |
| 4 of 5 · three quarters back · flat < 3 | 177 | 91 | 85 | **+1,322.0** | **+1,322.0** | 0 | 0 |  | 0 |
| 4 of 5 · three quarters back · flat < 5 | 177 | 91 | 85 | **+1,322.0** | **+1,322.0** | 0 | 0 |  | 0 |
| 4 of 5 · three quarters back · flat < 8 | 177 | 91 | 85 | **+1,322.0** | **+1,322.0** | 0 | 0 |  | 0 |

### By week: trades (won–lost) and pips

| Version | 25 – 30 Oct | 1 – 6 Nov | 8 – 11 Nov 15:15 |
|---|---:|---:|---:|
| **Current rules** | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 36 (19–17) +286.0 |
| 2 of 5 · a quarter back · flat < 3 | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 35 (19–16) +301.0 |
| 2 of 5 · a quarter back · flat < 5 | 57 (28–28) +154.9 | 82 (42–40) +811.0 | 35 (19–16) +301.0 |
| 2 of 5 · a quarter back · flat < 8 | 55 (26–28) +114.0 | 80 (42–38) +835.0 | 33 (19–14) +266.2 |
| 2 of 5 · a half back · flat < 3 | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 35 (19–16) +301.0 |
| 2 of 5 · a half back · flat < 5 | 58 (29–28) +204.9 | 82 (42–40) +811.0 | 35 (19–16) +301.0 |
| 2 of 5 · a half back · flat < 8 | 58 (29–28) +204.9 | 80 (42–38) +835.0 | 35 (19–16) +301.0 |
| 2 of 5 · three quarters back · flat < 3 | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 35 (19–16) +301.0 |
| 2 of 5 · three quarters back · flat < 5 | 58 (29–28) +214.9 | 82 (42–40) +811.0 | 35 (19–16) +301.0 |
| 2 of 5 · three quarters back · flat < 8 | 58 (29–28) +214.9 | 81 (42–39) +823.0 | 35 (19–16) +301.0 |
| 3 of 5 · a quarter back · flat < 3 | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 35 (19–16) +301.0 |
| 3 of 5 · a quarter back · flat < 5 | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 35 (19–16) +301.0 |
| 3 of 5 · a quarter back · flat < 8 | 58 (29–28) +214.0 | 80 (42–38) +835.0 | 34 (19–15) +313.0 |
| 3 of 5 · a half back · flat < 3 | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 35 (19–16) +301.0 |
| 3 of 5 · a half back · flat < 5 | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 35 (19–16) +301.0 |
| 3 of 5 · a half back · flat < 8 | 59 (30–28) +224.9 | 80 (42–38) +835.0 | 35 (19–16) +301.0 |
| 3 of 5 · three quarters back · flat < 3 | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 35 (19–16) +301.0 |
| 3 of 5 · three quarters back · flat < 5 | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 35 (19–16) +301.0 |
| 3 of 5 · three quarters back · flat < 8 | 59 (30–28) +224.9 | 81 (42–39) +823.0 | 35 (19–16) +301.0 |
| 4 of 5 · a quarter back · flat < 3 | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 36 (19–17) +286.0 |
| 4 of 5 · a quarter back · flat < 5 | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 36 (19–17) +286.0 |
| 4 of 5 · a quarter back · flat < 8 | 59 (30–28) +224.9 | 81 (42–39) +823.0 | 36 (19–17) +286.0 |
| 4 of 5 · a half back · flat < 3 | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 36 (19–17) +286.0 |
| 4 of 5 · a half back · flat < 5 | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 36 (19–17) +286.0 |
| 4 of 5 · a half back · flat < 8 | 59 (30–28) +224.9 | 81 (42–39) +823.0 | 36 (19–17) +286.0 |
| 4 of 5 · three quarters back · flat < 3 | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 36 (19–17) +286.0 |
| 4 of 5 · three quarters back · flat < 5 | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 36 (19–17) +286.0 |
| 4 of 5 · three quarters back · flat < 8 | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 36 (19–17) +286.0 |

### Every trade stopped, with what it made under the current rules

Each row is one entry the rule stopped in at least one version. The last column lists the versions that stopped it, written as wicks · back from the band · flat. For example, 3·25%·8 means 3 of 5 wicks, a quarter back, and flat under 8. "Not opened under the current rules" means the rule stopped an entry the current rules never made. That is usually a retry of a trade it had already stopped.

| Entry (UK) | Strategy | Way | Under the current rules | Pips | Stopped by (wicks·back·flat) |
|---|---|---|---|---:|---|
| Mon 26 Oct 06:05 | slow grind | sell | profit lock Mon 08:05 | +10.0 | 6: 2·25%·5, 2·25%·8, 2·50%·5, 2·50%·8, 2·75%·5, 2·75%·8 |
| Mon 26 Oct 07:40 | slow grind | sell | not opened under the current rules | – | 6: 2·25%·5, 2·25%·8, 2·50%·5, 2·50%·8, 2·75%·5, 2·75%·8 |
| Mon 26 Oct 20:30 | breakout | sell | not opened under the current rules | – | 4: 2·25%·5, 2·25%·8, 2·50%·5, 2·50%·8 |
| Tue 27 Oct 05:15 | breakout | sell | not opened under the current rules | – | 4: 2·25%·5, 2·25%·8, 2·50%·5, 2·50%·8 |
| Tue 27 Oct 05:45 | slow grind | sell | take profit Tue 09:30 | +20.0 | 4: 2·25%·5, 2·25%·8, 2·50%·5, 2·50%·8 |
| Thu 29 Oct 14:45 | breakout | buy | take profit Fri 01:05 | +50.0 | 18: 2·25%·3, 2·25%·5, 2·25%·8, 2·50%·3, 2·50%·5, 2·50%·8, 3·25%·3, 3·25%·5, 3·25%·8, 3·50%·3, 3·50%·5, 3·50%·8, 4·25%·3, 4·25%·5, 4·25%·8, 4·50%·3, 4·50%·5, 4·50%·8 |
| Thu 29 Oct 20:10 | breakout | buy | not opened under the current rules | – | 2: 2·25%·5, 2·25%·8 |
| Thu 29 Oct 22:05 | EMA pullback | buy | 20:30 close Fri 20:30 | +10.9 | 2: 2·25%·8, 3·25%·8 |
| Thu 29 Oct 22:50 | slow grind | buy | not opened under the current rules | – | 2: 2·25%·8, 3·25%·8 |
| Fri 30 Oct 00:40 | EMA pullback | buy | take profit Fri 09:15 | +30.0 | 1: 2·25%·8 |
| Tue 03 Nov 10:15 | breakout | sell | stop Tue 13:10 | -12.0 | 6: 2·25%·8, 2·50%·8, 2·75%·8, 3·25%·8, 3·50%·8, 3·75%·8 |
| Tue 03 Nov 13:45 | breakout | buy | stop Tue 13:50 | -12.0 | 6: 2·25%·8, 2·50%·8, 3·25%·8, 3·50%·8, 4·25%·8, 4·50%·8 |
| Mon 09 Nov 15:45 | slow grind | sell | stop Mon 16:15 | -15.0 | 18: 2·25%·3, 2·25%·5, 2·25%·8, 2·50%·3, 2·50%·5, 2·50%·8, 2·75%·3, 2·75%·5, 2·75%·8, 3·25%·3, 3·25%·5, 3·25%·8, 3·50%·3, 3·50%·5, 3·50%·8, 3·75%·3, 3·75%·5, 3·75%·8 |
| Tue 10 Nov 06:10 | EMA pullback | buy | stop Tue 09:00 | -12.0 | 1: 2·25%·8 |
| Tue 10 Nov 07:20 | EMA pullback | buy | stop Tue 09:00 | -12.0 | 2: 2·25%·8, 3·25%·8 |
| Tue 10 Nov 13:10 | breakout | sell | not opened under the current rules | – | 1: 2·25%·8 |
| Tue 10 Nov 13:30 | slow grind | sell | take profit Tue 16:30 | +100.0 | 1: 2·25%·8 |
| Tue 10 Nov 13:55 | slow grind | sell | not opened under the current rules | – | 1: 2·25%·8 |

Signs seen at each stopped entry (the loosest version that stopped it):

- Mon 26 Oct 06:05 slow grind sell: 2 of the last 5 hourly candles with a wick against it, the last close 0.91 of the way back to the middle band, the 100 EMA moved 1.6 and the 200 EMA 4.4 pips in 12 hours.
- Mon 26 Oct 07:40 slow grind sell: 2 of the last 5 hourly candles with a wick against it, the last close 0.87 of the way back to the middle band, the 100 EMA moved 1.6 and the 200 EMA 4.4 pips in 12 hours.
- Mon 26 Oct 20:30 breakout sell: 2 of the last 5 hourly candles with a wick against it, the last close 0.60 of the way back to the middle band, the 100 EMA moved 4.7 and the 200 EMA 0.7 pips in 12 hours.
- Tue 27 Oct 05:15 breakout sell: 2 of the last 5 hourly candles with a wick against it, the last close 0.57 of the way back to the middle band, the 100 EMA moved 4.8 and the 200 EMA 0.2 pips in 12 hours.
- Tue 27 Oct 05:45 slow grind sell: 2 of the last 5 hourly candles with a wick against it, the last close 0.57 of the way back to the middle band, the 100 EMA moved 4.8 and the 200 EMA 0.2 pips in 12 hours.
- Thu 29 Oct 14:45 breakout buy: 4 of the last 5 hourly candles with a wick against it, the last close 0.61 of the way back to the middle band, the 100 EMA moved 2.3 and the 200 EMA 1.2 pips in 12 hours.
- Thu 29 Oct 20:10 breakout buy: 2 of the last 5 hourly candles with a wick against it, the last close 0.26 of the way back to the middle band, the 100 EMA moved 3.3 and the 200 EMA 1.6 pips in 12 hours.
- Thu 29 Oct 22:05 EMA pullback buy: 3 of the last 5 hourly candles with a wick against it, the last close 0.32 of the way back to the middle band, the 100 EMA moved 5.5 and the 200 EMA 2.7 pips in 12 hours.
- Thu 29 Oct 22:50 slow grind buy: 3 of the last 5 hourly candles with a wick against it, the last close 0.32 of the way back to the middle band, the 100 EMA moved 5.5 and the 200 EMA 2.7 pips in 12 hours.
- Fri 30 Oct 00:40 EMA pullback buy: 2 of the last 5 hourly candles with a wick against it, the last close 0.36 of the way back to the middle band, the 100 EMA moved 7.6 and the 200 EMA 3.8 pips in 12 hours.
- Tue 03 Nov 10:15 breakout sell: 3 of the last 5 hourly candles with a wick against it, the last close 1.61 of the way back to the middle band, the 100 EMA moved 7.2 and the 200 EMA 5.8 pips in 12 hours.
- Tue 03 Nov 13:45 breakout buy: 4 of the last 5 hourly candles with a wick against it, the last close 0.74 of the way back to the middle band, the 100 EMA moved 7.1 and the 200 EMA 5.8 pips in 12 hours.
- Mon 09 Nov 15:45 slow grind sell: 3 of the last 5 hourly candles with a wick against it, the last close 1.50 of the way back to the middle band, the 100 EMA moved 2.6 and the 200 EMA 0.1 pips in 12 hours.
- Tue 10 Nov 06:10 EMA pullback buy: 2 of the last 5 hourly candles with a wick against it, the last close 0.42 of the way back to the middle band, the 100 EMA moved 6.0 and the 200 EMA 4.2 pips in 12 hours.
- Tue 10 Nov 07:20 EMA pullback buy: 3 of the last 5 hourly candles with a wick against it, the last close 0.38 of the way back to the middle band, the 100 EMA moved 6.4 and the 200 EMA 4.4 pips in 12 hours.
- Tue 10 Nov 13:10 breakout sell: 2 of the last 5 hourly candles with a wick against it, the last close 0.26 of the way back to the middle band, the 100 EMA moved 5.2 and the 200 EMA 3.9 pips in 12 hours.
- Tue 10 Nov 13:30 slow grind sell: 2 of the last 5 hourly candles with a wick against it, the last close 0.26 of the way back to the middle band, the 100 EMA moved 5.2 and the 200 EMA 3.9 pips in 12 hours.
- Tue 10 Nov 13:55 slow grind sell: 2 of the last 5 hourly candles with a wick against it, the last close 0.26 of the way back to the middle band, the 100 EMA moved 5.2 and the 200 EMA 3.9 pips in 12 hours.

### Trades that opened because of a stopped entry

These trades are in a version but not in the current rules. They are entries that came again, or new setups that opened once a stopped trade was not taking the strategy's place. In no version did any other trade change its exit.

| Version | Entry (UK) | Strategy | Way | What | Current | Version |
|---|---|---|---|---|---|---|
| 2·25%·3 | Thu 29 Oct 20:10 | breakout | buy | new | –  | take profit Fri 09:40 +50.0 |
| 2·25%·5 | Tue 27 Oct 06:00 | slow grind | sell | new | –  | profit lock Tue 07:10 +10.0 |
| 2·25%·8 | Tue 27 Oct 06:00 | slow grind | sell | new | –  | profit lock Tue 07:10 +10.0 |
| 2·25%·8 | Tue 10 Nov 14:30 | slow grind | sell | new | –  | 20:30 close Tue 20:30 +41.1 |
| 2·50%·3 | Thu 29 Oct 20:10 | breakout | buy | new | –  | take profit Fri 09:40 +50.0 |
| 2·50%·5 | Tue 27 Oct 06:00 | slow grind | sell | new | –  | profit lock Tue 07:10 +10.0 |
| 2·50%·5 | Thu 29 Oct 20:10 | breakout | buy | new | –  | take profit Fri 09:40 +50.0 |
| 2·50%·8 | Tue 27 Oct 06:00 | slow grind | sell | new | –  | profit lock Tue 07:10 +10.0 |
| 2·50%·8 | Thu 29 Oct 20:10 | breakout | buy | new | –  | take profit Fri 09:40 +50.0 |
| 3·25%·3 | Thu 29 Oct 20:10 | breakout | buy | new | –  | take profit Fri 09:40 +50.0 |
| 3·25%·5 | Thu 29 Oct 20:10 | breakout | buy | new | –  | take profit Fri 09:40 +50.0 |
| 3·25%·8 | Thu 29 Oct 20:10 | breakout | buy | new | –  | take profit Fri 09:40 +50.0 |
| 3·50%·3 | Thu 29 Oct 20:10 | breakout | buy | new | –  | take profit Fri 09:40 +50.0 |
| 3·50%·5 | Thu 29 Oct 20:10 | breakout | buy | new | –  | take profit Fri 09:40 +50.0 |
| 3·50%·8 | Thu 29 Oct 20:10 | breakout | buy | new | –  | take profit Fri 09:40 +50.0 |
| 4·25%·3 | Thu 29 Oct 20:10 | breakout | buy | new | –  | take profit Fri 09:40 +50.0 |
| 4·25%·5 | Thu 29 Oct 20:10 | breakout | buy | new | –  | take profit Fri 09:40 +50.0 |
| 4·25%·8 | Thu 29 Oct 20:10 | breakout | buy | new | –  | take profit Fri 09:40 +50.0 |
| 4·50%·3 | Thu 29 Oct 20:10 | breakout | buy | new | –  | take profit Fri 09:40 +50.0 |
| 4·50%·5 | Thu 29 Oct 20:10 | breakout | buy | new | –  | take profit Fri 09:40 +50.0 |
| 4·50%·8 | Thu 29 Oct 20:10 | breakout | buy | new | –  | take profit Fri 09:40 +50.0 |

### Tuesday 10 November, trade by trade

| Entry (UK) | Strategy | Way | Current rules: exit | Pips | Versions that stopped it | Versions it opened in |
|---|---|---|---|---:|---|---|
| 05:00 | EMA pullback | buy | stop Tue 09:00 | -12.0 | none | all 27 |
| 06:10 | EMA pullback | buy | stop Tue 09:00 | -12.0 | 2·25%·8 | all but 2·25%·8 |
| 07:20 | EMA pullback | buy | stop Tue 09:00 | -12.0 | 2·25%·8, 3·25%·8 | all but 2·25%·8, 3·25%·8 |
| 07:55 | Bollinger bounce | sell | rejection at a level Tue 08:30 | -6.8 | none | all 27 |
| 08:45 | Bollinger bounce | sell | half at the band +3.2, then rejection at a level Tue 10:40 | +12.5 | none | all 27 |
| 09:10 | breakout | sell | take profit Tue 14:40 | +50.0 | none | all 27 |
| 13:30 | slow grind | sell | take profit Tue 16:30 | +100.0 | 2·25%·8 | all but 2·25%·8 |
| 14:05 | level reversal | sell | take profit Tue 15:25 | +20.0 | none | all 27 |
| 14:30 | slow grind | sell | not opened | – | none | 2·25%·8 |
| 16:25 | level reversal | sell | stop Tue 18:35 | -20.0 | none | all 27 |
| 17:00 | Bollinger bounce | buy | half at the band +10.1, then 20:30 close Tue 20:30 | +15.7 | none | all 27 |
| 22:00 | EMA pullback | sell | stop Tue 22:00 | -12.0 | none | all 27 |

| Version | Tuesday 10 November: trades (won–lost) and pips |
|---|---:|
| **Current rules** | 11 (5–6) +123.4 |
| 2 of 5 · a quarter back · flat < 3 | 11 (5–6) +123.4 |
| 2 of 5 · a quarter back · flat < 5 | 11 (5–6) +123.4 |
| 2 of 5 · a quarter back · flat < 8 | 9 (5–4) +88.5 |
| 2 of 5 · a half back · flat < 3 | 11 (5–6) +123.4 |
| 2 of 5 · a half back · flat < 5 | 11 (5–6) +123.4 |
| 2 of 5 · a half back · flat < 8 | 11 (5–6) +123.4 |
| 2 of 5 · three quarters back · flat < 3 | 11 (5–6) +123.4 |
| 2 of 5 · three quarters back · flat < 5 | 11 (5–6) +123.4 |
| 2 of 5 · three quarters back · flat < 8 | 11 (5–6) +123.4 |
| 3 of 5 · a quarter back · flat < 3 | 11 (5–6) +123.4 |
| 3 of 5 · a quarter back · flat < 5 | 11 (5–6) +123.4 |
| 3 of 5 · a quarter back · flat < 8 | 10 (5–5) +135.4 |
| 3 of 5 · a half back · flat < 3 | 11 (5–6) +123.4 |
| 3 of 5 · a half back · flat < 5 | 11 (5–6) +123.4 |
| 3 of 5 · a half back · flat < 8 | 11 (5–6) +123.4 |
| 3 of 5 · three quarters back · flat < 3 | 11 (5–6) +123.4 |
| 3 of 5 · three quarters back · flat < 5 | 11 (5–6) +123.4 |
| 3 of 5 · three quarters back · flat < 8 | 11 (5–6) +123.4 |
| 4 of 5 · a quarter back · flat < 3 | 11 (5–6) +123.4 |
| 4 of 5 · a quarter back · flat < 5 | 11 (5–6) +123.4 |
| 4 of 5 · a quarter back · flat < 8 | 11 (5–6) +123.4 |
| 4 of 5 · a half back · flat < 3 | 11 (5–6) +123.4 |
| 4 of 5 · a half back · flat < 5 | 11 (5–6) +123.4 |
| 4 of 5 · a half back · flat < 8 | 11 (5–6) +123.4 |
| 4 of 5 · three quarters back · flat < 3 | 11 (5–6) +123.4 |
| 4 of 5 · three quarters back · flat < 5 | 11 (5–6) +123.4 |
| 4 of 5 · three quarters back · flat < 8 | 11 (5–6) +123.4 |
