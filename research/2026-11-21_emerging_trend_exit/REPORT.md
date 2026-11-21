# Emerging trend: do trades fade after 10–15 pips, and would a special exit bank more? (21 Nov 2026)

This is an investigation only. Nothing in the bot was changed and nothing was built. It covers the new AutoBot
server (/opt/autobot), not AutoBot 161.

**The question (Johnny):** trades opened when the analyser says "emerging trend" seem to go 10–15 pips and then
fade. Would an exit made for that state bank more?

## What was used

- Every live trade from Mon 9 Nov 05:25 to Fri 20 Nov 18:45 UTC (`research/2026-11-20_losing_trades/trades.csv`,
  which agrees with IG). That is 106 trades:
  - 1 is still open, so it is left out.
  - 13 were closed by Johnny by hand. They are kept out of the bot's results, as usual. 9 of those 13 are
    emerging-trend trades; they are listed on their own at the end.
  - That leaves **92 trades closed by the bot or by IG**. Every number below uses these 92.
- **"Best"** means how far a trade went its way while it was open. It is the bot's own live record
  (`best_pips`), which is measured on every tick. 7 early trades have no record, so for them the best is read from
  the stored 5-minute candles. Where both exist, the live record and the candles agree on whether a trade reached
  +10 for all 92 trades.
- The **timing** (how long to the best) and **whether price came back after +10** are read from the stored 5-minute
  candles. A buy is read on the sell price and a sell on the buy price, because that is the price IG closes at.
  Two trades are missing a few candles (3 out of 304). Neither result depends on the missing candles.
- The analyser state is the one recorded when the trade opened. No trade opened in **consolidation**, so that state
  has no row. Up and down are counted together (for example, "emerging trend up" and "emerging trend down").
- The script is `analyse.py`, its printed output is `analyse_output.txt`, and there is one row per trade in
  `trades_paths.csv`.

## 1–2. How far trades went their way, by state at entry

| State at entry | Trades | Won | Actual pips | Went straight against (never +3) | Reached +5 | +10 | +15 | +20 | +30 | Median best | Median min. to best | Median min. to best, trades that reached +10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **emerging trend** | **33** | 8 | −135.9 | 12 (36%) | 20 (61%) | **14 (42%)** | 10 (30%) | 6 (18%) | 4 (12%) | 6.2 | 72 | 156 |
| trend slow grind | 40 | 15 | −61.0 | 19 (48%) | 19 (48%) | 12 (30%) | 7 (18%) | 6 (15%) | 4 (10%) | 3.7 | 39 | 124 |
| trend strong push | 9 | 2 | −54.3 | 3 (33%) | 3 (33%) | 2 (22%) | 2 (22%) | 1 (11%) | 0 | 4.3 | 16 | 68 |
| ranging | 7 | 1 | −39.5 | 6 (86%) | 1 (14%) | 1 (14%) | 0 | 0 | 0 | 0.3 | 25 | 47 |
| possible reversal | 3 | 1 | −13.6 | 1 (33%) | 2 (67%) | 0 | 0 | 0 | 0 | 5.3 | 15 | – |
| consolidation | 0 | | | | | | | | | | | |
| *all states except emerging* | *59* | *19* | *−168.4* | *29 (49%)* | *25 (42%)* | *15 (25%)* | *9 (15%)* | *7 (12%)* | *4 (7%)* | *3.1* | *34* | *89* |

How to read this table:
- "Best" only counts the time the trade was open. A trade that hit its 20-pip target cannot show more than about 20,
  and a trade that was stopped early cannot show anything that happened after it closed.
- "Minutes to best" counts from the fill to the start of the 5-minute candle where the best was reached.

**Did trades fade after reaching +10?** This counts the trades that were +10 or better at some point and then
closed at break-even or worse.

| State at entry | Reached +10 | Then closed at 0 or worse | Then closed below +5 | Median best of these |
|---|---|---|---|---|
| **emerging trend** | 14 | **6** | 6 | 15.9 |
| trend slow grind | 12 | 1 | 3 | 18.5 |
| trend strong push | 2 | 0 | 0 | 19.0 |
| ranging | 1 | 0 | 0 | 11.6 |
| *all states except emerging* | *15* | *1* | *3* | *18.0* |

## 3. Emerging trend: what each exit would have made

Each what-if changes only the exit. The entry, stop, target, trails and the bot's own closes stay exactly as they
were live.
- **a** = close all at +10
- **b** = close all at +15
- **c** = close half at +10 and move the stop on the other half to +2
- **d** = move the stop to +5 once the trade is +10

Results are pips per trade. The +2 and +5 stops are assumed to fill at exactly +2 and +5, with no slippage.

| Opened (UTC) | Ver | Strategy | Dir | Stop / target | Best | Min. to best | How it closed | **Actual** | a +10 | b +15 | c half +10, rest +2 | d +5 once +10 | Note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 11-09 06:12 | A | level reversal | buy | 12.9 / 20 | 20 | 122 | target hit | +20.0 | +10.0 | +15.0 | +15.0 | +20.0 | |
| 11-10 05:01 | A | EMA pullback | buy | 12 / 100 | 7.6 | 208 | stopped | −12.0 | −12.0 | −12.0 | −12.0 | −12.0 | |
| 11-10 06:12 | A | EMA pullback | buy | 12 / 100 | 5.8 | 137 | stopped | −12.0 | −12.0 | −12.0 | −12.0 | −12.0 | |
| 11-10 07:21 | A | EMA pullback | buy | 12 / 100 | 2.5 | 68 | stopped | −12.0 | −12.0 | −12.0 | −12.0 | −12.0 | |
| 11-10 09:10 | A | breakout | sell | 6 / 50 | 2.6 | 0 | stopped | −6.0 | −6.0 | −6.0 | −6.0 | −6.0 | |
| 11-10 11:50 | A | breakout | sell | 6 / 50 | −0.3 | – | stopped | −6.0 | −6.0 | −6.0 | −6.0 | −6.0 | |
| 11-10 13:11 | A | breakout | sell | 6 / 50 | 2.2 | 3 | stopped | −6.0 | −6.0 | −6.0 | −6.0 | −6.0 | |
| 11-11 13:10 | A | breakout | sell | 12 / 50 | 50 | 804 | target hit | **+50.0** | +10.0 | +15.0 | +30.0 | +50.0 | |
| 11-11 21:06 | A | EMA pullback | sell | 12 / 30 | −0.7 | – | stopped (at IG) | −12.0 | −12.0 | −12.0 | −12.0 | −12.0 | |
| 11-12 10:20 | A | breakout | buy | 12 / 50 | 0 | 0 | stopped | −12.0 | −12.0 | −12.0 | −12.0 | −12.0 | |
| 11-12 11:30 | A | breakout | sell | 12 / 50 | 43.2 | 249 | closed at IG | +21.1 | +10.0 | +15.0 | +6.0 | +5.0 | was +12.9, fell to −10, then ran to +43 |
| 11-12 19:02 | A | EMA pullback | sell | 12 / 100 | 0.4 | 0 | stopped | −12.0 | −12.0 | −12.0 | −12.0 | −12.0 | |
| 11-12 22:00 | A | EMA pullback | sell | 12 / 100 | −12 | – | stopped | −12.0 | −12.0 | −12.0 | −12.0 | −12.0 | |
| 11-12 23:47 | A | EMA pullback | sell | 12 / 100 | 0.1 | 27 | stopped | −12.0 | −12.0 | −12.0 | −12.0 | −12.0 | |
| 11-13 10:28 | A | breakout | sell | 12 / 50 | 6.2 | 141 | stopped (at IG) | −12.0 | −12.0 | −12.0 | −12.0 | −12.0 | |
| 11-13 10:28 | A | EMA pullback | sell | 12 / 30 | 6.2 | 141 | stopped (at IG) | −12.0 | −12.0 | −12.0 | −12.0 | −12.0 | |
| 11-16 06:50 | B | level reversal | sell | 11.5 / 20 | 0.6 | 4 | stopped | −11.5 | −11.5 | −11.5 | −11.5 | −11.5 | |
| 11-16 08:40 | B | level reversal | buy | 16.4 / 20 | 14.1 | 19 | stopped | −16.4 | +10.0 | −16.4 | +6.0 | +5.0 | |
| 11-16 09:50 | B | level reversal | sell | 17.8 / 20 | 2.9 | 74 | stopped | −17.8 | −17.8 | −17.8 | −17.8 | −17.8 | |
| 11-16 10:25 | B | Bollinger bounce | buy | 12 / 100 | 1.5 | 0 | stopped | −12.0 | −12.0 | −12.0 | −12.0 | −12.0 | |
| 11-16 10:50 | B | EMA pullback | sell | 12 / 30 | 3.5 | 14 | stopped | −12.0 | −12.0 | −12.0 | −12.0 | −12.0 | |
| 11-16 12:37 | B | level reversal | sell | 14.4 / 20 | 15.6 | 362 | bot's 20:30 close | +8.3 | +10.0 | +15.0 | +6.0 | +5.0 | |
| 11-16 14:26 | B | EMA pullback | sell | 12 / 30 | 22.6 | 664 | stopped | −12.0 | +10.0 | +15.0 | +6.0 | +5.0 | held overnight |
| 11-16 20:00 | B | EMA pullback | sell | 12 / 30 | 6.2 | 69 | stopped | −12.0 | −12.0 | −12.0 | −12.0 | −12.0 | |
| 11-17 07:35 | B | level reversal | sell | 13.4 / 20 | 7 | 24 | stopped | −13.4 | −13.4 | −13.4 | −13.4 | −13.4 | |
| 11-17 10:05 | B | Bollinger bounce | sell | 12 / 100 | 15.6 | 209 | stopped (trail) | −3.3 | +10.0 | +15.0 | +6.0 | +5.0 | the old trail fault (fixed 17 Nov) |
| 11-17 10:05 | B | level reversal | sell | 20.8 / 20 | 15.2 | 209 | stopped | −20.8 | +10.0 | +15.0 | +6.0 | +5.0 | |
| 11-17 14:00 | B | session sweep | buy | 17.1 / 100 | 12.2 | 29 | stopped (trail) | +5.1 | +10.0 | +5.1 | +7.5 | +5.0 | (d) back to +5 is seen only in the close candle |
| 11-18 07:30 | B | Asian range breakout | sell | 12 / 100 | 30.7 | 94 | stopped (trail) | +21.7 | +10.0 | +15.0 | +15.8 | +21.7 | |
| 11-18 15:44 | C | breakout | sell | 12 / 50 | 16.1 | 35 | stopped | −12.0 | +10.0 | +15.0 | +6.0 | +5.0 | |
| 11-19 12:10 | D | session sweep | sell | 22 / 100 | 42.2 | 189 | stopped (trail) | +28.9 | +10.0 | +15.0 | +19.4 | +28.9 | |
| 11-20 06:07 | E | level reversal | buy | 17.3 / 20 | 10.5 | 62 | stopped | −17.3 | +10.0 | −17.3 | +6.0 | +5.0 | |
| 11-20 07:30 | E | session sweep | sell | 12 / 100 | 13.6 | 80 | stopped (trail) | +7.5 | +10.0 | +7.5 | +8.8 | +7.5 | (d) +10 and +5 in the same candle, order unknown |
| **Total, 33 trades** | | | | | | | | **−135.9** | **−76.7** | **−87.8** | **−72.1** | **−43.6** | |

| Exit | Total | Change vs actual | Trades better / worse / same |
|---|---|---|---|
| Actual | −135.9 | – | – |
| a: all at +10 | −76.7 | +59.2 | 9 / 5 / 19 |
| b: all at +15 | −87.8 | +48.1 | 5 / 5 / 23 |
| c: half at +10, rest stop +2 | −72.1 | +63.8 | 8 / 6 / 19 |
| d: stop to +5 once +10 | **−43.6** | **+92.3** | 6 / 3 / 24 |

**How much the order depends on single trades:**
- **The 50-pip winner (11 Nov 13:10).** This one trade decides whether **d** comes first.
  - With it: d is best.
  - Without it, the totals are: actual −185.9, a −86.7, b −102.8, c −102.1, d −93.6. So **a** comes first and
    d is second.
  - The reason: d keeps a trade that runs to its target, while a, b and c cut it short.
- **The 12 Nov 11:30 trade.** It went to +12.9, fell to −10, then ran to +43. All four exits would have taken
  far less than the +21.1 it actually made.
- **The two outcomes in the Note column that the candles cannot settle** (17 Nov 14:00 and 20 Nov 07:30). Either way
  they move the d total by about 2.5 pips at most.

**Two things are in all four totals:**
- **19 of the 33 trades never reached +10.** Every exit leaves them unchanged.
- **11 of the 33 are EMA pullbacks.** They lost −132.0 together. No exit helps them, because only one ever got
  to +10.

**Split by code version:**
- **First build (A, 9–13 Nov, 16 trades).** Every exit does *worse* than what actually happened (actual −46.9;
  a −108, b −93, c −87, d −63). That week's winners ran to their 20- and 50-pip targets.
- **Since 16 Nov (B–E, 17 trades).** Every exit does much better than what actually happened (actual −89.0;
  a +31.3, b +5.2, c +14.9, d +19.4). Several trades went +10 to +16 and then came back to the full stop.

**The same exits on the trades in all the other states, for comparison (59 trades, actual −168.4):** a −251.4,
b −233.6, c −226.9, d −214.6. **All four exits make the other states worse.**

**Johnny's 9 hand-closed emerging-trend trades** are not in any total above.
- 2 of them reached +10: 9 Nov 07:55 (best 33.5, closed at +11.7) and 9 Nov 08:25 (best 11.1, closed at −11.2).
- The other 7 never got past +9.7, so none of the exits would have changed them.

## 4. Plain-English answer

**Does "emerging trend" behave differently?** Yes, in the way Johnny describes. These figures come from **33
trades** closed by the bot or IG, against 59 trades in the other states.

- **More emerging-trend trades get going.**
  - 42% reached +10 at some point, against 25% in the other states.
  - 30% reached +15, against 15%.
  - Fewer went straight against: 36%, against 49%.
- **They give it back much more often.** 14 reached +10. 6 of those 14 then closed at break-even or worse,
  mostly at the full stop. In all the other states it was 1 trade out of 15.
- **The moves are slow, not quick pops.** For the trades that reached +10, the median time to their best was about
  2½ hours.

**Which exit banks most for it?**
- **d (stop to +5 once +10) banked the most:** −43.6 against −135.9 actual, an improvement of 92 pips.
- Next came c (−72.1), a (−76.7) and b (−87.8). All four did better than what actually happened.
- **The lead for d depends on one trade, the 50-pip winner on 11 Nov.** Without it, **a (close all at +10)**
  comes first and d is second.
- **The answer is different in different weeks.** In the first-build week every exit would have lost pips,
  because winners ran to their targets. Since 16 Nov every exit would have gained, because +10 to +16 trades kept
  coming back to the full stop.
- **The pattern is specific to emerging trend.** On the other states, all four exits would have made results worse.

**How far to trust this:**
- It rests on 33 trades, and only 14 of them reached +10, where an exit can make any difference at all.
- The +10 to +16 trades that came back are spread over several strategies.
- The what-ifs are read from candles, not tested on the live demo. As always, the live demo is the judge.
- No exit level is recommended here. This is information for Johnny to decide with.
