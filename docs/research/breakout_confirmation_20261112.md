# Confirming the consolidation breakout, 25 October to 12 November 2026

Thursday 12 November 2026, UK. This is read-only research: **nothing in the bot was changed**. There were no IG calls and no restart, and nothing was written outside `data/research/`.

## Summary

**The question.** Today the analyser calls a breakout out of a consolidation on one candle closing beyond a Bollinger band. The breakout strategy then opens as soon as price passes that candle's high (buy) or low (sell), within 3 candles. Would a confirmation do better?

1. Two closes in a row beyond the same band, as the range breakout already uses.
2. For comparison: one close beyond the band by at least 1, 2 or 3 pips.
3. A retest that holds. After the breakout candle, wait for price to come back within 1, 2 or 3 pips of the consolidation's edge without a candle closing back inside it. Then enter when price passes the breakout candle's high (or low) again. The setup gets 6 or 12 candles; if no retest comes, either skip the trade or enter anyway.

**The current rules make +1,540.7 pips in 149 trades** (78 won, 71 lost), from the week's open on Sunday 25 October to the last stored candle, which ended at 18:10 UTC today. That includes 15 breakout trades (+192.2), 14 of them after a consolidation (+204.2). Five of the breakouts reached their 50-pip take profit.

**The results:**

- **1. Two closes in a row: −28.1** (+1,512.6).
  - It makes 3 fewer breakout trades, and they make 52.0 less. The breakout candle is one candle later, so the trades that still open enter later and at a worse price.
  - Four of the five take-profit breakouts still happen, a candle or a few later. The 27 October sell (+50.0) is lost.
  - Other strategies gain 23.9, because the emerging trend now starts a candle later.
- **2. One close by 1, 2 or 3 pips: −16.9, +45.4 and −44.7.**
  - **Only 2+ pips does better, and not through the breakouts.** Its breakout trades make 12.4 less. The +45.4 comes from 22 trades of other strategies (+57.8) that change because the analyser starts fewer emerging trends.
  - At 3+ pips, two of the take-profit breakouts are lost (27 and 29 October).
- **3. The retest that holds: 231 to 271 pips worse, in every version.**
  - **All five breakouts that reached their take profit (+50.0 each) ran away without ever coming back** within 1 to 3 pips of the consolidation's edge. The retest rule never takes them, so 250 pips are lost.
  - The breakouts that did come back were mostly the weak ones. Their entries after the retest were stopped (−12.0) in all but one or two cases.
  - It does save losing breakouts that never re-broke, or closed back inside first: seven of them (−12.0 each) in the 1-pip versions.
  - **"Enter anyway" doesn't rescue it.** It adds only one or two trades and changes the result by −11.8 to +39.9 against "skip". By the time the window ends, the analyser has often gone back to consolidation (where a breakout may not open), or it is outside the 06:00 to 20:30 trading hours, or another breakout trade is already open.
  - The "skip" versions are the same with 6 and 12 candles.
- **No candle reached both a trade's stop and its target** in any of the 18 runs, so stop first and target first give the same result everywhere.

**Today, Thursday 12 November:**

- **Under the current rules**, the 11:30 breakout sell opens at 13264.8. It is still open at the last candle (18:05 UK), at **+34.4**. Live, the bot's 11:30 sell opened at 13264.6 and closed at 16:14 UK at +21.1.
- **Two closes in a row:** it opens at 15:05 instead, at 13243.1 (+12.7, still open).
- **1+ pips:** it opens at 13:10 and is stopped (−12.0); a second sell at 15:00 is +14.8.
- **2+ and 3+ pips:** it does not open.
- **Every "skip" retest version, and every 12-candle "enter anyway" version:** it opens one candle later, at 11:35 at 13264.9 (+34.5).
- **"Enter anyway" with 6 candles:**
  - 1 or 2 pips: it is refused, because an earlier "enter anyway" breakout is still open and the bot allows one breakout at a time. A sell at 15:30 is then stopped (−12.0).
  - 3 pips: the sell opens at 15:05 instead (+13.8).
- The losing 10:20 breakout buy (−12.0) is not taken in any version.

**In short:** of the three, only "2+ pips beyond the band" does better (+45.4), and it does so through the other strategies, not the breakout trades. The best breakouts are the ones that never look back, which is exactly what a retest rule misses. These are 14 consolidation breakouts in 13 trading days, so none of this is settled.

## How it was done

- **Candles.** A read-only copy of the bot's own IG candle store, taken at 18:12 UTC today (`data/research/replay_stores/live_copy_20261112_1812/`). It ends with the candle that finished at 18:10 UTC.
- **Code.** A frozen copy of the committed code, `79c5dcf`: the current rules, including today's trend proof (the failed bounce on an earlier candle than the new extreme). The replay is the research mode (`research.long_replay`), with the same engine, strategies, safety rules, paper order sender and trade manager as the bot's own replay, run week by week.
- **The rules tested are switches in that frozen copy only,** read from the research process's environment. With them off, the copy is the bot:
  - the bot's analyser tests and breakout tests pass on it (74 and 16 tests);
  - the replay with no switch on gives the same 149 trades as the bot's own code, trade for trade.
  
  The scripts and every run's trades are in `data/research/replay/breakout_confirmation_20261112/`. The repository commits only this file.
- **1 and 2 change the analyser,** for consolidations only (the range breakout keeps its own rule).
  - The analyser moves from consolidation to an emerging trend only after two closes in a row beyond the same band. Each close is checked against that candle's own band, on consecutive candles. Or, for 2, after one close beyond the band by at least 1, 2 or 3 pips.
  - The breakout candle is the candle that completes the confirmation. The breakout strategy works as now from it: price past its high (or low) within 3 candles, in the direction of the day's move.
  - Because the analyser's state changes, other strategies that depend on an emerging trend can change too. Those trades are shown with the breakouts.
- **3 changes only the breakout strategy,** for consolidation breakouts. The analyser is unchanged.
  - **The edge** is the consolidation's high (buy) or low (sell), the same range the breakout records today: from the consolidation's start to the candle before the breakout candle.
  - **The retest:** a later candle's low (buy) comes within 1, 2 or 3 pips of the edge, or goes below it, without closing below it. For a sell, a high within that distance of the low, without closing above it.
  - **A close back inside the consolidation** at any point ends the setup.
  - **The entry:** after the retest candle, the first candle whose high passes the breakout candle's high (a sell: low below its low). It fills at that price, or at the candle's open if it opened past it. A retest and entry on the same candle are not counted, since the order inside a candle is not known.
  - **The time limit:** the retest and the entry must both come within 6 or 12 candles of the breakout candle.
  - **No retest in time:**
    - "skip": no trade;
    - "enter anyway": enter at the open of the next candle, if nothing closed back inside.
  - Every entry still passes the day's-move check and all of the bot's own rules. A breakout opens only in an emerging trend or a trend, and only one breakout trade is open at a time.
- **Prices.**
  - Entries are at IG's buy price (buys) or sell price (sells), from the candles.
  - Stops and take profits fill at their level, or at the candle's open if it opened past them.
  - No spread is added: IG's buy and sell prices already include it.
- **Trades still open at the last candle** are counted at that candle's close. In the current rules, that is the 11:30 breakout sell.
- **Win and loss:** a trade with more than 0 pips is a win, below 0 a loss. **Times** are UK times.

## Results

### Totals

| Version | Trades | Won | Lost | Pips, stop first | Pips, target first | Against current | Breakout trades: all | of them after a consolidation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Current rules** | 149 | 78 | 71 | **+1,540.7** | **+1,540.7** |  | 15 (7–8) +192.2 | 14 (7–7) +204.2 |
| 1. Two closes in a row beyond the band | 136 | 74 | 62 | **+1,512.6** | **+1,512.6** | -28.1 | 12 (5–7) +140.2 | 11 (5–6) +152.2 |
| 2. One close beyond the band by 1+ pips | 138 | 77 | 61 | **+1,523.8** | **+1,523.8** | -16.9 | 11 (6–5) +158.6 | 10 (6–4) +170.6 |
| 2. One close beyond the band by 2+ pips | 129 | 75 | 54 | **+1,586.1** | **+1,586.1** | +45.4 | 7 (5–2) +179.8 | 5 (5–0) +203.8 |
| 2. One close beyond the band by 3+ pips | 125 | 71 | 54 | **+1,496.0** | **+1,496.0** | -44.7 | 6 (3–3) +125.5 | 4 (3–1) +149.5 |
| 3. Retest within 1 pips, 6 candles, no retest: skip | 143 | 72 | 71 | **+1,305.8** | **+1,305.8** | -234.9 | 7 (1–6) -37.5 | 6 (1–5) -25.5 |
| 3. Retest within 1 pips, 6 candles, no retest: enter anyway | 144 | 72 | 72 | **+1,307.9** | **+1,307.9** | -232.8 | 9 (1–8) -35.6 | 8 (1–7) -23.6 |
| 3. Retest within 1 pips, 12 candles, no retest: skip | 143 | 72 | 71 | **+1,305.8** | **+1,305.8** | -234.9 | 7 (1–6) -37.5 | 6 (1–5) -25.5 |
| 3. Retest within 1 pips, 12 candles, no retest: enter anyway | 143 | 72 | 71 | **+1,294.0** | **+1,294.0** | -246.7 | 8 (1–7) -49.5 | 7 (1–6) -37.5 |
| 3. Retest within 2 pips, 6 candles, no retest: skip | 145 | 72 | 73 | **+1,281.8** | **+1,281.8** | -258.9 | 9 (1–8) -61.5 | 8 (1–7) -49.5 |
| 3. Retest within 2 pips, 6 candles, no retest: enter anyway | 145 | 72 | 73 | **+1,295.9** | **+1,295.9** | -244.8 | 10 (1–9) -47.6 | 9 (1–8) -35.6 |
| 3. Retest within 2 pips, 12 candles, no retest: skip | 145 | 72 | 73 | **+1,281.8** | **+1,281.8** | -258.9 | 9 (1–8) -61.5 | 8 (1–7) -49.5 |
| 3. Retest within 2 pips, 12 candles, no retest: enter anyway | 144 | 72 | 72 | **+1,282.0** | **+1,282.0** | -258.7 | 9 (1–8) -61.5 | 8 (1–7) -49.5 |
| 3. Retest within 3 pips, 6 candles, no retest: skip | 146 | 72 | 74 | **+1,269.8** | **+1,269.8** | -270.9 | 10 (1–9) -73.5 | 9 (1–8) -61.5 |
| 3. Retest within 3 pips, 6 candles, no retest: enter anyway | 146 | 73 | 73 | **+1,309.7** | **+1,309.7** | -231.0 | 11 (2–9) -33.8 | 10 (2–8) -21.8 |
| 3. Retest within 3 pips, 12 candles, no retest: skip | 146 | 72 | 74 | **+1,269.8** | **+1,269.8** | -270.9 | 10 (1–9) -73.5 | 9 (1–8) -61.5 |
| 3. Retest within 3 pips, 12 candles, no retest: enter anyway | 145 | 72 | 73 | **+1,270.0** | **+1,270.0** | -270.7 | 10 (1–9) -73.5 | 9 (1–8) -61.5 |

### By week: trades (won–lost) and pips

| Version | 25 – 30 Oct | 1 – 6 Nov | 8 – 12 Nov 18:10 UTC |
|---|---:|---:|---:|
| **Current rules** | 38 (18–20) +162.4 | 78 (40–38) +911.1 | 33 (20–13) +467.2 |
| 1. Two closes in a row beyond the band | 38 (17–21) +100.4 | 67 (38–29) +1,019.8 | 31 (19–12) +392.4 |
| 2. One close beyond the band by 1+ pips | 36 (17–19) +124.4 | 70 (41–29) +1,022.7 | 32 (19–13) +376.7 |
| 2. One close beyond the band by 2+ pips | 38 (18–20) +122.4 | 63 (39–24) +1,057.0 | 28 (18–10) +406.7 |
| 2. One close beyond the band by 3+ pips | 35 (15–20) +31.5 | 63 (38–25) +1,052.7 | 27 (18–9) +411.8 |
| 3. Retest within 1 pips, 6 candles, no retest: skip | 36 (16–20) +69.4 | 74 (39–35) +943.3 | 33 (17–16) +293.1 |
| 3. Retest within 1 pips, 6 candles, no retest: enter anyway | 36 (16–20) +69.4 | 75 (39–36) +941.7 | 33 (17–16) +296.8 |
| 3. Retest within 1 pips, 12 candles, no retest: skip | 36 (16–20) +69.4 | 74 (39–35) +943.3 | 33 (17–16) +293.1 |
| 3. Retest within 1 pips, 12 candles, no retest: enter anyway | 36 (16–20) +69.4 | 74 (39–35) +943.3 | 33 (17–16) +281.3 |
| 3. Retest within 2 pips, 6 candles, no retest: skip | 36 (16–20) +69.4 | 75 (39–36) +931.3 | 34 (17–17) +281.1 |
| 3. Retest within 2 pips, 6 candles, no retest: enter anyway | 36 (16–20) +69.4 | 76 (39–37) +929.7 | 33 (17–16) +296.8 |
| 3. Retest within 2 pips, 12 candles, no retest: skip | 36 (16–20) +69.4 | 75 (39–36) +931.3 | 34 (17–17) +281.1 |
| 3. Retest within 2 pips, 12 candles, no retest: enter anyway | 36 (16–20) +69.4 | 75 (39–36) +931.3 | 33 (17–16) +281.3 |
| 3. Retest within 3 pips, 6 candles, no retest: skip | 36 (16–20) +69.4 | 76 (39–37) +919.3 | 34 (17–17) +281.1 |
| 3. Retest within 3 pips, 6 candles, no retest: enter anyway | 36 (16–20) +69.4 | 77 (39–38) +917.7 | 33 (18–15) +322.6 |
| 3. Retest within 3 pips, 12 candles, no retest: skip | 36 (16–20) +69.4 | 76 (39–37) +919.3 | 34 (17–17) +281.1 |
| 3. Retest within 3 pips, 12 candles, no retest: enter anyway | 36 (16–20) +69.4 | 76 (39–37) +919.3 | 33 (17–16) +281.3 |

### Every trade that changes, with what it made before and after

Versions with exactly the same changes are listed together. Breakout trades come first, then the other strategies' trades that change with them. "Not opened" in the current rules' columns means the trade is new in that version.

**1. Two closes in a row beyond the band:** 24 breakout trades change (-52.0), 16 other trades change (+23.9); in all -28.1.

| Entry (UK) | Strategy | Way | Current rules | Pips | This version | Pips | Difference |
|---|---|---|---|---:|---|---:|---:|
| Tue 27 Oct 07:00 | breakout | sell | take profit Wed 07:10 | +50.0 | not opened | – | -50.0 |
| Wed 28 Oct 18:40 | breakout | buy | stop Wed 18:55 | -12.0 | not opened | – | +12.0 |
| Thu 29 Oct 06:05 | breakout | sell | not opened | – | stop Thu 07:30 | -12.0 | -12.0 |
| Thu 29 Oct 08:00 | breakout | buy | not opened | – | stop Thu 08:10 | -12.0 | -12.0 |
| Thu 29 Oct 14:45 | breakout | buy | take profit Fri 01:05 | +50.0 | not opened | – | -50.0 |
| Thu 29 Oct 14:50 | breakout | buy | not opened | – | take profit Fri 01:10 | +50.0 | +50.0 |
| Tue 03 Nov 13:45 | breakout | buy | stop Tue 13:50 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 14:50 | breakout | buy | stop Tue 15:10 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:05 | breakout | buy | stop Tue 20:00 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:10 | breakout | buy | not opened | – | stop Tue 19:45 | -12.0 | -12.0 |
| Wed 04 Nov 20:05 | breakout | buy | stop Thu 10:00 | -12.0 | not opened | – | +12.0 |
| Wed 04 Nov 20:10 | breakout | buy | not opened | – | stop Wed 22:00 | -12.0 | -12.0 |
| Thu 05 Nov 07:05 | breakout | buy | not opened | – | stop Thu 07:10 | -12.0 | -12.0 |
| Thu 05 Nov 10:00 | breakout | sell | stop Thu 12:00 | -12.0 | not opened | – | +12.0 |
| Fri 06 Nov 17:50 | breakout | sell | 20:30 close Fri 20:30 | +3.8 | not opened | – | -3.8 |
| Fri 06 Nov 17:55 | breakout | sell | not opened | – | 20:30 close Fri 20:30 | -0.5 | -0.5 |
| Mon 09 Nov 07:55 | breakout | buy | take profit Mon 21:00 | +50.0 | not opened | – | -50.0 |
| Mon 09 Nov 08:10 | breakout | buy | not opened | – | take profit Tue 05:00 | +50.0 | +50.0 |
| Tue 10 Nov 09:10 | breakout | sell | take profit Tue 14:40 | +50.0 | take profit Tue 14:35 | +50.0 | +0.0 |
| Wed 11 Nov 13:10 | breakout | sell | take profit Thu 02:35 | +50.0 | not opened | – | -50.0 |
| Wed 11 Nov 13:25 | breakout | sell | not opened | – | take profit Thu 14:55 | +50.0 | +50.0 |
| Thu 12 Nov 10:20 | breakout | buy | stop Thu 11:20 | -12.0 | not opened | – | +12.0 |
| Thu 12 Nov 11:30 | breakout | sell | still open at the end Thu 18:05 | +34.4 | not opened | – | -34.4 |
| Thu 12 Nov 15:05 | breakout | sell | not opened | – | still open at the end Thu 18:05 | +12.7 | +12.7 |
| Mon 02 Nov 14:20 | range trade | buy | opposite band Mon 14:35 | +10.0 | not opened | – | -10.0 |
| Tue 03 Nov 14:50 | EMA pullback | buy | stop Tue 15:10 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:05 | EMA pullback | buy | stop Tue 20:00 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:05 | EMA pullback | buy | stop Tue 20:00 | -12.0 | not opened | – | +12.0 |
| Wed 04 Nov 04:35 | EMA pullback | buy | stop Wed 04:40 | -12.0 | not opened | – | +12.0 |
| Wed 04 Nov 04:35 | EMA pullback | buy | stop Wed 04:40 | -12.0 | not opened | – | +12.0 |
| Thu 05 Nov 04:00 | EMA pullback | buy | stop Thu 07:20 | -12.0 | not opened | – | +12.0 |
| Thu 05 Nov 07:00 | EMA pullback | buy | stop Thu 07:15 | -12.0 | not opened | – | +12.0 |
| Thu 05 Nov 10:20 | slow grind | sell | stop Thu 12:00 | -15.0 | not opened | – | +15.0 |
| Mon 09 Nov 13:50 | range trade | buy | not opened | – | rejection at a level Mon 14:45 | -4.0 | -4.0 |
| Mon 09 Nov 13:55 | range trade | buy | rejection at a level Mon 14:45 | -7.7 | not opened | – | +7.7 |
| Tue 10 Nov 13:30 | slow grind | sell | take profit Tue 16:30 | +100.0 | not opened | – | -100.0 |
| Tue 10 Nov 14:30 | slow grind | sell | not opened | – | 20:30 close Tue 20:30 | +41.1 | +41.1 |
| Tue 10 Nov 17:00 | Bollinger bounce | buy | half at the band +10.1, then 20:30 close Tue 20:30 | +15.7 | not opened | – | -15.7 |
| Tue 10 Nov 22:00 | EMA pullback | sell | stop Tue 22:00 | -12.0 | not opened | – | +12.0 |
| Thu 12 Nov 06:20 | range trade | buy | not opened | – | before big news Thu 06:45 | -6.2 | -6.2 |

**2. One close beyond the band by 1+ pips:** 18 breakout trades change (-33.6), 13 other trades change (+16.7); in all -16.9.

| Entry (UK) | Strategy | Way | Current rules | Pips | This version | Pips | Difference |
|---|---|---|---|---:|---|---:|---:|
| Tue 27 Oct 07:00 | breakout | sell | take profit Wed 07:10 | +50.0 | not opened | – | -50.0 |
| Wed 28 Oct 18:40 | breakout | buy | stop Wed 18:55 | -12.0 | not opened | – | +12.0 |
| Thu 29 Oct 14:45 | breakout | buy | take profit Fri 01:05 | +50.0 | not opened | – | -50.0 |
| Thu 29 Oct 20:10 | breakout | buy | not opened | – | take profit Fri 09:40 | +50.0 | +50.0 |
| Tue 03 Nov 13:45 | breakout | buy | stop Tue 13:50 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:05 | breakout | buy | stop Tue 20:00 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:10 | breakout | buy | not opened | – | stop Tue 19:45 | -12.0 | -12.0 |
| Wed 04 Nov 20:05 | breakout | buy | stop Thu 10:00 | -12.0 | not opened | – | +12.0 |
| Thu 05 Nov 07:05 | breakout | buy | not opened | – | stop Thu 07:10 | -12.0 | -12.0 |
| Thu 05 Nov 10:00 | breakout | sell | stop Thu 12:00 | -12.0 | not opened | – | +12.0 |
| Mon 09 Nov 07:55 | breakout | buy | take profit Mon 21:00 | +50.0 | not opened | – | -50.0 |
| Mon 09 Nov 08:05 | breakout | buy | not opened | – | take profit Tue 04:55 | +50.0 | +50.0 |
| Wed 11 Nov 13:10 | breakout | sell | take profit Thu 02:35 | +50.0 | not opened | – | -50.0 |
| Wed 11 Nov 13:20 | breakout | sell | not opened | – | take profit Thu 03:15 | +50.0 | +50.0 |
| Thu 12 Nov 10:20 | breakout | buy | stop Thu 11:20 | -12.0 | not opened | – | +12.0 |
| Thu 12 Nov 11:30 | breakout | sell | still open at the end Thu 18:05 | +34.4 | not opened | – | -34.4 |
| Thu 12 Nov 13:10 | breakout | sell | not opened | – | stop Thu 13:40 | -12.0 | -12.0 |
| Thu 12 Nov 15:00 | breakout | sell | not opened | – | still open at the end Thu 18:05 | +14.8 | +14.8 |
| Tue 03 Nov 18:05 | EMA pullback | buy | stop Tue 20:00 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:05 | EMA pullback | buy | stop Tue 20:00 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 20:10 | range trade | buy | not opened | – | 20:30 close Tue 20:30 | +0.6 | +0.6 |
| Wed 04 Nov 04:35 | EMA pullback | buy | stop Wed 04:40 | -12.0 | not opened | – | +12.0 |
| Wed 04 Nov 04:35 | EMA pullback | buy | stop Wed 04:40 | -12.0 | not opened | – | +12.0 |
| Thu 05 Nov 04:00 | EMA pullback | buy | stop Thu 07:20 | -12.0 | not opened | – | +12.0 |
| Thu 05 Nov 07:00 | EMA pullback | buy | stop Thu 07:15 | -12.0 | not opened | – | +12.0 |
| Thu 05 Nov 10:20 | slow grind | sell | stop Thu 12:00 | -15.0 | not opened | – | +15.0 |
| Mon 09 Nov 13:50 | range trade | buy | not opened | – | rejection at a level Mon 14:45 | -4.0 | -4.0 |
| Mon 09 Nov 13:55 | range trade | buy | rejection at a level Mon 14:45 | -7.7 | not opened | – | +7.7 |
| Tue 10 Nov 13:30 | slow grind | sell | take profit Tue 16:30 | +100.0 | not opened | – | -100.0 |
| Tue 10 Nov 14:30 | slow grind | sell | not opened | – | 20:30 close Tue 20:30 | +41.1 | +41.1 |
| Tue 10 Nov 17:00 | Bollinger bounce | buy | half at the band +10.1, then 20:30 close Tue 20:30 | +15.7 | not opened | – | -15.7 |

**2. One close beyond the band by 2+ pips:** 16 breakout trades change (-12.4), 22 other trades change (+57.8); in all +45.4.

| Entry (UK) | Strategy | Way | Current rules | Pips | This version | Pips | Difference |
|---|---|---|---|---:|---|---:|---:|
| Tue 27 Oct 07:00 | breakout | sell | take profit Wed 07:10 | +50.0 | not opened | – | -50.0 |
| Wed 28 Oct 18:40 | breakout | buy | stop Wed 18:55 | -12.0 | not opened | – | +12.0 |
| Thu 29 Oct 08:00 | breakout | buy | not opened | – | stop Thu 08:10 | -12.0 | -12.0 |
| Thu 29 Oct 14:45 | breakout | buy | take profit Fri 01:05 | +50.0 | not opened | – | -50.0 |
| Thu 29 Oct 20:10 | breakout | buy | not opened | – | take profit Fri 09:40 | +50.0 | +50.0 |
| Tue 03 Nov 13:45 | breakout | buy | stop Tue 13:50 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 14:50 | breakout | buy | stop Tue 15:10 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:05 | breakout | buy | stop Tue 20:00 | -12.0 | not opened | – | +12.0 |
| Wed 04 Nov 20:05 | breakout | buy | stop Thu 10:00 | -12.0 | not opened | – | +12.0 |
| Thu 05 Nov 10:00 | breakout | sell | stop Thu 12:00 | -12.0 | not opened | – | +12.0 |
| Mon 09 Nov 07:55 | breakout | buy | take profit Mon 21:00 | +50.0 | not opened | – | -50.0 |
| Mon 09 Nov 08:05 | breakout | buy | not opened | – | take profit Tue 04:55 | +50.0 | +50.0 |
| Wed 11 Nov 13:10 | breakout | sell | take profit Thu 02:35 | +50.0 | not opened | – | -50.0 |
| Wed 11 Nov 13:20 | breakout | sell | not opened | – | take profit Thu 03:15 | +50.0 | +50.0 |
| Thu 12 Nov 10:20 | breakout | buy | stop Thu 11:20 | -12.0 | not opened | – | +12.0 |
| Thu 12 Nov 11:30 | breakout | sell | still open at the end Thu 18:05 | +34.4 | not opened | – | -34.4 |
| Thu 29 Oct 07:35 | range trade | sell | not opened | – | opposite band Thu 08:45 | +10.0 | +10.0 |
| Mon 02 Nov 14:20 | range trade | buy | opposite band Mon 14:35 | +10.0 | not opened | – | -10.0 |
| Mon 02 Nov 18:55 | Bollinger bounce | buy | half at the band +7.7, then 20:30 close Mon 20:30 | +5.5 | not opened | – | -5.5 |
| Mon 02 Nov 19:40 | slow grind | sell | 20:30 close Mon 20:30 | -1.8 | not opened | – | +1.8 |
| Tue 03 Nov 14:50 | EMA pullback | buy | stop Tue 15:10 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:05 | EMA pullback | buy | stop Tue 20:00 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:05 | EMA pullback | buy | stop Tue 20:00 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 20:10 | range trade | buy | not opened | – | 20:30 close Tue 20:30 | +0.6 | +0.6 |
| Wed 04 Nov 04:35 | EMA pullback | buy | stop Wed 04:40 | -12.0 | not opened | – | +12.0 |
| Wed 04 Nov 04:35 | EMA pullback | buy | stop Wed 04:40 | -12.0 | not opened | – | +12.0 |
| Thu 05 Nov 04:00 | EMA pullback | buy | stop Thu 07:20 | -12.0 | not opened | – | +12.0 |
| Thu 05 Nov 07:00 | EMA pullback | buy | stop Thu 07:15 | -12.0 | not opened | – | +12.0 |
| Thu 05 Nov 10:20 | slow grind | sell | stop Thu 12:00 | -15.0 | not opened | – | +15.0 |
| Mon 09 Nov 13:50 | range trade | buy | not opened | – | rejection at a level Mon 14:45 | -4.0 | -4.0 |
| Mon 09 Nov 13:55 | range trade | buy | rejection at a level Mon 14:45 | -7.7 | not opened | – | +7.7 |
| Tue 10 Nov 13:30 | slow grind | sell | take profit Tue 16:30 | +100.0 | not opened | – | -100.0 |
| Tue 10 Nov 14:30 | slow grind | sell | not opened | – | 20:30 close Tue 20:30 | +41.1 | +41.1 |
| Tue 10 Nov 17:00 | Bollinger bounce | buy | half at the band +10.1, then 20:30 close Tue 20:30 | +15.7 | not opened | – | -15.7 |
| Tue 10 Nov 22:00 | EMA pullback | sell | stop Tue 22:00 | -12.0 | not opened | – | +12.0 |
| Wed 11 Nov 21:05 | EMA pullback | sell | stop Wed 22:00 | -12.0 | not opened | – | +12.0 |
| Thu 12 Nov 02:55 | slow grind | sell | stop Thu 07:40 | -15.0 | not opened | – | +15.0 |
| Thu 12 Nov 06:20 | range trade | buy | not opened | – | before big news Thu 06:45 | -6.2 | -6.2 |

**2. One close beyond the band by 3+ pips:** 17 breakout trades change (-66.7), 27 other trades change (+22.0); in all -44.7.

| Entry (UK) | Strategy | Way | Current rules | Pips | This version | Pips | Difference |
|---|---|---|---|---:|---|---:|---:|
| Tue 27 Oct 07:00 | breakout | sell | take profit Wed 07:10 | +50.0 | not opened | – | -50.0 |
| Wed 28 Oct 18:40 | breakout | buy | stop Wed 18:55 | -12.0 | not opened | – | +12.0 |
| Thu 29 Oct 08:00 | breakout | buy | not opened | – | stop Thu 08:10 | -12.0 | -12.0 |
| Thu 29 Oct 14:45 | breakout | buy | take profit Fri 01:05 | +50.0 | not opened | – | -50.0 |
| Tue 03 Nov 13:45 | breakout | buy | stop Tue 13:50 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 14:50 | breakout | buy | stop Tue 15:10 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:05 | breakout | buy | stop Tue 20:00 | -12.0 | not opened | – | +12.0 |
| Wed 04 Nov 20:05 | breakout | buy | stop Thu 10:00 | -12.0 | not opened | – | +12.0 |
| Thu 05 Nov 10:00 | breakout | sell | stop Thu 12:00 | -12.0 | not opened | – | +12.0 |
| Fri 06 Nov 17:50 | breakout | sell | 20:30 close Fri 20:30 | +3.8 | not opened | – | -3.8 |
| Fri 06 Nov 17:55 | breakout | sell | not opened | – | 20:30 close Fri 20:30 | -0.5 | -0.5 |
| Mon 09 Nov 07:55 | breakout | buy | take profit Mon 21:00 | +50.0 | not opened | – | -50.0 |
| Mon 09 Nov 08:15 | breakout | buy | not opened | – | take profit Tue 07:20 | +50.0 | +50.0 |
| Wed 11 Nov 13:10 | breakout | sell | take profit Thu 02:35 | +50.0 | not opened | – | -50.0 |
| Wed 11 Nov 13:20 | breakout | sell | not opened | – | take profit Thu 03:15 | +50.0 | +50.0 |
| Thu 12 Nov 10:20 | breakout | buy | stop Thu 11:20 | -12.0 | not opened | – | +12.0 |
| Thu 12 Nov 11:30 | breakout | sell | still open at the end Thu 18:05 | +34.4 | not opened | – | -34.4 |
| Thu 29 Oct 07:35 | range trade | sell | not opened | – | opposite band Thu 08:45 | +10.0 | +10.0 |
| Thu 29 Oct 22:05 | EMA pullback | buy | 20:30 close Fri 20:30 | +10.9 | not opened | – | -10.9 |
| Fri 30 Oct 00:40 | EMA pullback | buy | take profit Fri 09:15 | +30.0 | not opened | – | -30.0 |
| Mon 02 Nov 14:20 | range trade | buy | opposite band Mon 14:35 | +10.0 | not opened | – | -10.0 |
| Mon 02 Nov 18:55 | Bollinger bounce | buy | half at the band +7.7, then 20:30 close Mon 20:30 | +5.5 | not opened | – | -5.5 |
| Mon 02 Nov 19:40 | slow grind | sell | 20:30 close Mon 20:30 | -1.8 | not opened | – | +1.8 |
| Tue 03 Nov 14:50 | EMA pullback | buy | stop Tue 15:10 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:05 | EMA pullback | buy | stop Tue 20:00 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:05 | EMA pullback | buy | stop Tue 20:00 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 20:10 | range trade | buy | not opened | – | 20:30 close Tue 20:30 | +0.6 | +0.6 |
| Wed 04 Nov 04:35 | EMA pullback | buy | stop Wed 04:40 | -12.0 | not opened | – | +12.0 |
| Wed 04 Nov 04:35 | EMA pullback | buy | stop Wed 04:40 | -12.0 | not opened | – | +12.0 |
| Thu 05 Nov 04:00 | EMA pullback | buy | stop Thu 07:20 | -12.0 | not opened | – | +12.0 |
| Thu 05 Nov 07:00 | EMA pullback | buy | stop Thu 07:15 | -12.0 | not opened | – | +12.0 |
| Thu 05 Nov 10:20 | slow grind | sell | stop Thu 12:00 | -15.0 | not opened | – | +15.0 |
| Mon 09 Nov 13:50 | range trade | buy | not opened | – | rejection at a level Mon 14:45 | -4.0 | -4.0 |
| Mon 09 Nov 13:55 | range trade | buy | rejection at a level Mon 14:45 | -7.7 | not opened | – | +7.7 |
| Tue 10 Nov 13:30 | slow grind | sell | take profit Tue 16:30 | +100.0 | not opened | – | -100.0 |
| Tue 10 Nov 14:30 | slow grind | sell | not opened | – | 20:30 close Tue 20:30 | +41.1 | +41.1 |
| Tue 10 Nov 17:00 | Bollinger bounce | buy | half at the band +10.1, then 20:30 close Tue 20:30 | +15.7 | not opened | – | -15.7 |
| Tue 10 Nov 22:00 | EMA pullback | sell | stop Tue 22:00 | -12.0 | not opened | – | +12.0 |
| Wed 11 Nov 14:45 | slow grind | sell | stop Wed 15:10 | -15.0 | not opened | – | +15.0 |
| Wed 11 Nov 15:50 | slow grind | sell | 20:30 close Wed 20:30 | -2.1 | not opened | – | +2.1 |
| Wed 11 Nov 18:45 | EMA pullback | sell | not opened | – | stop Wed 22:00 | -12.0 | -12.0 |
| Wed 11 Nov 21:05 | EMA pullback | sell | stop Wed 22:00 | -12.0 | not opened | – | +12.0 |
| Thu 12 Nov 02:55 | slow grind | sell | stop Thu 07:40 | -15.0 | not opened | – | +15.0 |
| Thu 12 Nov 06:20 | range trade | buy | not opened | – | before big news Thu 06:45 | -6.2 | -6.2 |

**3. Retest within 1 pips, 6 candles, no retest: skip; 3. Retest within 1 pips, 12 candles, no retest: skip:** 20 breakout trades change (-229.7), 2 other trades change (-5.2); in all -234.9.

| Entry (UK) | Strategy | Way | Current rules | Pips | This version | Pips | Difference |
|---|---|---|---|---:|---|---:|---:|
| Tue 27 Oct 07:00 | breakout | sell | take profit Wed 07:10 | +50.0 | not opened | – | -50.0 |
| Wed 28 Oct 18:40 | breakout | buy | stop Wed 18:55 | -12.0 | not opened | – | +12.0 |
| Thu 29 Oct 14:45 | breakout | buy | take profit Fri 01:05 | +50.0 | not opened | – | -50.0 |
| Tue 03 Nov 13:45 | breakout | buy | stop Tue 13:50 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 14:50 | breakout | buy | stop Tue 15:10 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:05 | breakout | buy | stop Tue 20:00 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:10 | breakout | buy | not opened | – | stop Tue 19:45 | -12.0 | -12.0 |
| Wed 04 Nov 20:05 | breakout | buy | stop Thu 10:00 | -12.0 | not opened | – | +12.0 |
| Thu 05 Nov 07:05 | breakout | buy | not opened | – | stop Thu 07:15 | -12.0 | -12.0 |
| Thu 05 Nov 10:00 | breakout | sell | stop Thu 12:00 | -12.0 | not opened | – | +12.0 |
| Fri 06 Nov 17:50 | breakout | sell | 20:30 close Fri 20:30 | +3.8 | not opened | – | -3.8 |
| Mon 09 Nov 07:55 | breakout | buy | take profit Mon 21:00 | +50.0 | not opened | – | -50.0 |
| Mon 09 Nov 09:55 | breakout | buy | not opened | – | stop Mon 15:05 | -12.0 | -12.0 |
| Mon 09 Nov 19:40 | breakout | buy | not opened | – | stop Tue 09:45 | -12.0 | -12.0 |
| Tue 10 Nov 09:10 | breakout | sell | take profit Tue 14:40 | +50.0 | not opened | – | -50.0 |
| Tue 10 Nov 13:10 | breakout | sell | not opened | – | stop Tue 13:30 | -12.0 | -12.0 |
| Wed 11 Nov 13:10 | breakout | sell | take profit Thu 02:35 | +50.0 | not opened | – | -50.0 |
| Thu 12 Nov 10:20 | breakout | buy | stop Thu 11:20 | -12.0 | not opened | – | +12.0 |
| Thu 12 Nov 11:30 | breakout | sell | still open at the end Thu 18:05 | +34.4 | not opened | – | -34.4 |
| Thu 12 Nov 11:35 | breakout | sell | not opened | – | still open at the end Thu 18:05 | +34.5 | +34.5 |
| Tue 27 Oct 07:20 | Bollinger bounce | buy | not opened | – | rejection at a level Tue 08:10 | -5.0 | -5.0 |
| Wed 11 Nov 15:10 | Bollinger bounce | buy | not opened | – | rejection at a level Wed 16:55 | -0.2 | -0.2 |

**3. Retest within 1 pips, 6 candles, no retest: enter anyway:** 22 breakout trades change (-227.8), 1 other trades change (-5.0); in all -232.8.

| Entry (UK) | Strategy | Way | Current rules | Pips | This version | Pips | Difference |
|---|---|---|---|---:|---|---:|---:|
| Tue 27 Oct 07:00 | breakout | sell | take profit Wed 07:10 | +50.0 | not opened | – | -50.0 |
| Wed 28 Oct 18:40 | breakout | buy | stop Wed 18:55 | -12.0 | not opened | – | +12.0 |
| Thu 29 Oct 14:45 | breakout | buy | take profit Fri 01:05 | +50.0 | not opened | – | -50.0 |
| Tue 03 Nov 13:45 | breakout | buy | stop Tue 13:50 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 14:50 | breakout | buy | stop Tue 15:10 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:05 | breakout | buy | stop Tue 20:00 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:10 | breakout | buy | not opened | – | stop Tue 19:45 | -12.0 | -12.0 |
| Wed 04 Nov 20:05 | breakout | buy | stop Thu 10:00 | -12.0 | not opened | – | +12.0 |
| Thu 05 Nov 07:05 | breakout | buy | not opened | – | stop Thu 07:15 | -12.0 | -12.0 |
| Thu 05 Nov 10:00 | breakout | sell | stop Thu 12:00 | -12.0 | not opened | – | +12.0 |
| Fri 06 Nov 17:50 | breakout | sell | 20:30 close Fri 20:30 | +3.8 | not opened | – | -3.8 |
| Fri 06 Nov 18:20 | breakout | sell | not opened | – | 20:30 close Fri 20:30 | -1.6 | -1.6 |
| Mon 09 Nov 07:55 | breakout | buy | take profit Mon 21:00 | +50.0 | not opened | – | -50.0 |
| Mon 09 Nov 09:55 | breakout | buy | not opened | – | stop Mon 15:05 | -12.0 | -12.0 |
| Mon 09 Nov 19:40 | breakout | buy | not opened | – | stop Tue 09:45 | -12.0 | -12.0 |
| Tue 10 Nov 09:10 | breakout | sell | take profit Tue 14:40 | +50.0 | not opened | – | -50.0 |
| Tue 10 Nov 13:10 | breakout | sell | not opened | – | stop Tue 13:30 | -12.0 | -12.0 |
| Wed 11 Nov 13:10 | breakout | sell | take profit Thu 02:35 | +50.0 | not opened | – | -50.0 |
| Wed 11 Nov 13:40 | breakout | sell | not opened | – | take profit Thu 15:00 | +50.0 | +50.0 |
| Thu 12 Nov 10:20 | breakout | buy | stop Thu 11:20 | -12.0 | not opened | – | +12.0 |
| Thu 12 Nov 11:30 | breakout | sell | still open at the end Thu 18:05 | +34.4 | not opened | – | -34.4 |
| Thu 12 Nov 15:30 | breakout | sell | not opened | – | stop Thu 16:10 | -12.0 | -12.0 |
| Tue 27 Oct 07:20 | Bollinger bounce | buy | not opened | – | rejection at a level Tue 08:10 | -5.0 | -5.0 |

**3. Retest within 1 pips, 12 candles, no retest: enter anyway:** 21 breakout trades change (-241.7), 1 other trades change (-5.0); in all -246.7.

| Entry (UK) | Strategy | Way | Current rules | Pips | This version | Pips | Difference |
|---|---|---|---|---:|---|---:|---:|
| Tue 27 Oct 07:00 | breakout | sell | take profit Wed 07:10 | +50.0 | not opened | – | -50.0 |
| Wed 28 Oct 18:40 | breakout | buy | stop Wed 18:55 | -12.0 | not opened | – | +12.0 |
| Thu 29 Oct 14:45 | breakout | buy | take profit Fri 01:05 | +50.0 | not opened | – | -50.0 |
| Tue 03 Nov 13:45 | breakout | buy | stop Tue 13:50 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 14:50 | breakout | buy | stop Tue 15:10 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:05 | breakout | buy | stop Tue 20:00 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:10 | breakout | buy | not opened | – | stop Tue 19:45 | -12.0 | -12.0 |
| Wed 04 Nov 20:05 | breakout | buy | stop Thu 10:00 | -12.0 | not opened | – | +12.0 |
| Thu 05 Nov 07:05 | breakout | buy | not opened | – | stop Thu 07:15 | -12.0 | -12.0 |
| Thu 05 Nov 10:00 | breakout | sell | stop Thu 12:00 | -12.0 | not opened | – | +12.0 |
| Fri 06 Nov 17:50 | breakout | sell | 20:30 close Fri 20:30 | +3.8 | not opened | – | -3.8 |
| Mon 09 Nov 07:55 | breakout | buy | take profit Mon 21:00 | +50.0 | not opened | – | -50.0 |
| Mon 09 Nov 09:55 | breakout | buy | not opened | – | stop Mon 15:05 | -12.0 | -12.0 |
| Mon 09 Nov 19:40 | breakout | buy | not opened | – | stop Tue 09:45 | -12.0 | -12.0 |
| Tue 10 Nov 09:10 | breakout | sell | take profit Tue 14:40 | +50.0 | not opened | – | -50.0 |
| Tue 10 Nov 13:10 | breakout | sell | not opened | – | stop Tue 13:30 | -12.0 | -12.0 |
| Wed 11 Nov 13:10 | breakout | sell | take profit Thu 02:35 | +50.0 | not opened | – | -50.0 |
| Wed 11 Nov 14:10 | breakout | sell | not opened | – | stop Wed 22:05 | -12.0 | -12.0 |
| Thu 12 Nov 10:20 | breakout | buy | stop Thu 11:20 | -12.0 | not opened | – | +12.0 |
| Thu 12 Nov 11:30 | breakout | sell | still open at the end Thu 18:05 | +34.4 | not opened | – | -34.4 |
| Thu 12 Nov 11:35 | breakout | sell | not opened | – | still open at the end Thu 18:05 | +34.5 | +34.5 |
| Tue 27 Oct 07:20 | Bollinger bounce | buy | not opened | – | rejection at a level Tue 08:10 | -5.0 | -5.0 |

**3. Retest within 2 pips, 6 candles, no retest: skip; 3. Retest within 2 pips, 12 candles, no retest: skip:** 22 breakout trades change (-253.7), 2 other trades change (-5.2); in all -258.9.

| Entry (UK) | Strategy | Way | Current rules | Pips | This version | Pips | Difference |
|---|---|---|---|---:|---|---:|---:|
| Tue 27 Oct 07:00 | breakout | sell | take profit Wed 07:10 | +50.0 | not opened | – | -50.0 |
| Wed 28 Oct 18:40 | breakout | buy | stop Wed 18:55 | -12.0 | not opened | – | +12.0 |
| Thu 29 Oct 14:45 | breakout | buy | take profit Fri 01:05 | +50.0 | not opened | – | -50.0 |
| Tue 03 Nov 13:45 | breakout | buy | stop Tue 13:50 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 14:50 | breakout | buy | stop Tue 15:10 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:05 | breakout | buy | stop Tue 20:00 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:10 | breakout | buy | not opened | – | stop Tue 19:45 | -12.0 | -12.0 |
| Wed 04 Nov 20:05 | breakout | buy | stop Thu 10:00 | -12.0 | not opened | – | +12.0 |
| Wed 04 Nov 20:10 | breakout | buy | not opened | – | stop Wed 22:00 | -12.0 | -12.0 |
| Thu 05 Nov 07:05 | breakout | buy | not opened | – | stop Thu 07:15 | -12.0 | -12.0 |
| Thu 05 Nov 10:00 | breakout | sell | stop Thu 12:00 | -12.0 | not opened | – | +12.0 |
| Fri 06 Nov 17:50 | breakout | sell | 20:30 close Fri 20:30 | +3.8 | not opened | – | -3.8 |
| Mon 09 Nov 07:55 | breakout | buy | take profit Mon 21:00 | +50.0 | not opened | – | -50.0 |
| Mon 09 Nov 09:55 | breakout | buy | not opened | – | stop Mon 15:05 | -12.0 | -12.0 |
| Mon 09 Nov 19:40 | breakout | buy | not opened | – | stop Tue 09:45 | -12.0 | -12.0 |
| Tue 10 Nov 09:10 | breakout | sell | take profit Tue 14:40 | +50.0 | not opened | – | -50.0 |
| Tue 10 Nov 13:10 | breakout | sell | not opened | – | stop Tue 13:30 | -12.0 | -12.0 |
| Wed 11 Nov 13:10 | breakout | sell | take profit Thu 02:35 | +50.0 | not opened | – | -50.0 |
| Wed 11 Nov 17:20 | breakout | sell | not opened | – | stop Wed 22:00 | -12.0 | -12.0 |
| Thu 12 Nov 10:20 | breakout | buy | stop Thu 11:20 | -12.0 | not opened | – | +12.0 |
| Thu 12 Nov 11:30 | breakout | sell | still open at the end Thu 18:05 | +34.4 | not opened | – | -34.4 |
| Thu 12 Nov 11:35 | breakout | sell | not opened | – | still open at the end Thu 18:05 | +34.5 | +34.5 |
| Tue 27 Oct 07:20 | Bollinger bounce | buy | not opened | – | rejection at a level Tue 08:10 | -5.0 | -5.0 |
| Wed 11 Nov 15:10 | Bollinger bounce | buy | not opened | – | rejection at a level Wed 16:55 | -0.2 | -0.2 |

**3. Retest within 2 pips, 6 candles, no retest: enter anyway:** 23 breakout trades change (-239.8), 1 other trades change (-5.0); in all -244.8.

| Entry (UK) | Strategy | Way | Current rules | Pips | This version | Pips | Difference |
|---|---|---|---|---:|---|---:|---:|
| Tue 27 Oct 07:00 | breakout | sell | take profit Wed 07:10 | +50.0 | not opened | – | -50.0 |
| Wed 28 Oct 18:40 | breakout | buy | stop Wed 18:55 | -12.0 | not opened | – | +12.0 |
| Thu 29 Oct 14:45 | breakout | buy | take profit Fri 01:05 | +50.0 | not opened | – | -50.0 |
| Tue 03 Nov 13:45 | breakout | buy | stop Tue 13:50 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 14:50 | breakout | buy | stop Tue 15:10 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:05 | breakout | buy | stop Tue 20:00 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:10 | breakout | buy | not opened | – | stop Tue 19:45 | -12.0 | -12.0 |
| Wed 04 Nov 20:05 | breakout | buy | stop Thu 10:00 | -12.0 | not opened | – | +12.0 |
| Wed 04 Nov 20:10 | breakout | buy | not opened | – | stop Wed 22:00 | -12.0 | -12.0 |
| Thu 05 Nov 07:05 | breakout | buy | not opened | – | stop Thu 07:15 | -12.0 | -12.0 |
| Thu 05 Nov 10:00 | breakout | sell | stop Thu 12:00 | -12.0 | not opened | – | +12.0 |
| Fri 06 Nov 17:50 | breakout | sell | 20:30 close Fri 20:30 | +3.8 | not opened | – | -3.8 |
| Fri 06 Nov 18:20 | breakout | sell | not opened | – | 20:30 close Fri 20:30 | -1.6 | -1.6 |
| Mon 09 Nov 07:55 | breakout | buy | take profit Mon 21:00 | +50.0 | not opened | – | -50.0 |
| Mon 09 Nov 09:55 | breakout | buy | not opened | – | stop Mon 15:05 | -12.0 | -12.0 |
| Mon 09 Nov 19:40 | breakout | buy | not opened | – | stop Tue 09:45 | -12.0 | -12.0 |
| Tue 10 Nov 09:10 | breakout | sell | take profit Tue 14:40 | +50.0 | not opened | – | -50.0 |
| Tue 10 Nov 13:10 | breakout | sell | not opened | – | stop Tue 13:30 | -12.0 | -12.0 |
| Wed 11 Nov 13:10 | breakout | sell | take profit Thu 02:35 | +50.0 | not opened | – | -50.0 |
| Wed 11 Nov 13:40 | breakout | sell | not opened | – | take profit Thu 15:00 | +50.0 | +50.0 |
| Thu 12 Nov 10:20 | breakout | buy | stop Thu 11:20 | -12.0 | not opened | – | +12.0 |
| Thu 12 Nov 11:30 | breakout | sell | still open at the end Thu 18:05 | +34.4 | not opened | – | -34.4 |
| Thu 12 Nov 15:30 | breakout | sell | not opened | – | stop Thu 16:10 | -12.0 | -12.0 |
| Tue 27 Oct 07:20 | Bollinger bounce | buy | not opened | – | rejection at a level Tue 08:10 | -5.0 | -5.0 |

**3. Retest within 2 pips, 12 candles, no retest: enter anyway:** 22 breakout trades change (-253.7), 1 other trades change (-5.0); in all -258.7.

| Entry (UK) | Strategy | Way | Current rules | Pips | This version | Pips | Difference |
|---|---|---|---|---:|---|---:|---:|
| Tue 27 Oct 07:00 | breakout | sell | take profit Wed 07:10 | +50.0 | not opened | – | -50.0 |
| Wed 28 Oct 18:40 | breakout | buy | stop Wed 18:55 | -12.0 | not opened | – | +12.0 |
| Thu 29 Oct 14:45 | breakout | buy | take profit Fri 01:05 | +50.0 | not opened | – | -50.0 |
| Tue 03 Nov 13:45 | breakout | buy | stop Tue 13:50 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 14:50 | breakout | buy | stop Tue 15:10 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:05 | breakout | buy | stop Tue 20:00 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:10 | breakout | buy | not opened | – | stop Tue 19:45 | -12.0 | -12.0 |
| Wed 04 Nov 20:05 | breakout | buy | stop Thu 10:00 | -12.0 | not opened | – | +12.0 |
| Wed 04 Nov 20:10 | breakout | buy | not opened | – | stop Wed 22:00 | -12.0 | -12.0 |
| Thu 05 Nov 07:05 | breakout | buy | not opened | – | stop Thu 07:15 | -12.0 | -12.0 |
| Thu 05 Nov 10:00 | breakout | sell | stop Thu 12:00 | -12.0 | not opened | – | +12.0 |
| Fri 06 Nov 17:50 | breakout | sell | 20:30 close Fri 20:30 | +3.8 | not opened | – | -3.8 |
| Mon 09 Nov 07:55 | breakout | buy | take profit Mon 21:00 | +50.0 | not opened | – | -50.0 |
| Mon 09 Nov 09:55 | breakout | buy | not opened | – | stop Mon 15:05 | -12.0 | -12.0 |
| Mon 09 Nov 19:40 | breakout | buy | not opened | – | stop Tue 09:45 | -12.0 | -12.0 |
| Tue 10 Nov 09:10 | breakout | sell | take profit Tue 14:40 | +50.0 | not opened | – | -50.0 |
| Tue 10 Nov 13:10 | breakout | sell | not opened | – | stop Tue 13:30 | -12.0 | -12.0 |
| Wed 11 Nov 13:10 | breakout | sell | take profit Thu 02:35 | +50.0 | not opened | – | -50.0 |
| Wed 11 Nov 14:10 | breakout | sell | not opened | – | stop Wed 22:05 | -12.0 | -12.0 |
| Thu 12 Nov 10:20 | breakout | buy | stop Thu 11:20 | -12.0 | not opened | – | +12.0 |
| Thu 12 Nov 11:30 | breakout | sell | still open at the end Thu 18:05 | +34.4 | not opened | – | -34.4 |
| Thu 12 Nov 11:35 | breakout | sell | not opened | – | still open at the end Thu 18:05 | +34.5 | +34.5 |
| Tue 27 Oct 07:20 | Bollinger bounce | buy | not opened | – | rejection at a level Tue 08:10 | -5.0 | -5.0 |

**3. Retest within 3 pips, 6 candles, no retest: skip; 3. Retest within 3 pips, 12 candles, no retest: skip:** 23 breakout trades change (-265.7), 2 other trades change (-5.2); in all -270.9.

| Entry (UK) | Strategy | Way | Current rules | Pips | This version | Pips | Difference |
|---|---|---|---|---:|---|---:|---:|
| Tue 27 Oct 07:00 | breakout | sell | take profit Wed 07:10 | +50.0 | not opened | – | -50.0 |
| Wed 28 Oct 18:40 | breakout | buy | stop Wed 18:55 | -12.0 | not opened | – | +12.0 |
| Thu 29 Oct 14:45 | breakout | buy | take profit Fri 01:05 | +50.0 | not opened | – | -50.0 |
| Tue 03 Nov 13:45 | breakout | buy | stop Tue 13:50 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 14:50 | breakout | buy | stop Tue 15:10 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 14:55 | breakout | buy | not opened | – | stop Tue 15:10 | -12.0 | -12.0 |
| Tue 03 Nov 18:05 | breakout | buy | stop Tue 20:00 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:10 | breakout | buy | not opened | – | stop Tue 19:45 | -12.0 | -12.0 |
| Wed 04 Nov 20:05 | breakout | buy | stop Thu 10:00 | -12.0 | not opened | – | +12.0 |
| Wed 04 Nov 20:10 | breakout | buy | not opened | – | stop Wed 22:00 | -12.0 | -12.0 |
| Thu 05 Nov 07:05 | breakout | buy | not opened | – | stop Thu 07:15 | -12.0 | -12.0 |
| Thu 05 Nov 10:00 | breakout | sell | stop Thu 12:00 | -12.0 | not opened | – | +12.0 |
| Fri 06 Nov 17:50 | breakout | sell | 20:30 close Fri 20:30 | +3.8 | not opened | – | -3.8 |
| Mon 09 Nov 07:55 | breakout | buy | take profit Mon 21:00 | +50.0 | not opened | – | -50.0 |
| Mon 09 Nov 09:55 | breakout | buy | not opened | – | stop Mon 15:05 | -12.0 | -12.0 |
| Mon 09 Nov 19:40 | breakout | buy | not opened | – | stop Tue 09:45 | -12.0 | -12.0 |
| Tue 10 Nov 09:10 | breakout | sell | take profit Tue 14:40 | +50.0 | not opened | – | -50.0 |
| Tue 10 Nov 13:10 | breakout | sell | not opened | – | stop Tue 13:30 | -12.0 | -12.0 |
| Wed 11 Nov 13:10 | breakout | sell | take profit Thu 02:35 | +50.0 | not opened | – | -50.0 |
| Wed 11 Nov 17:20 | breakout | sell | not opened | – | stop Wed 22:00 | -12.0 | -12.0 |
| Thu 12 Nov 10:20 | breakout | buy | stop Thu 11:20 | -12.0 | not opened | – | +12.0 |
| Thu 12 Nov 11:30 | breakout | sell | still open at the end Thu 18:05 | +34.4 | not opened | – | -34.4 |
| Thu 12 Nov 11:35 | breakout | sell | not opened | – | still open at the end Thu 18:05 | +34.5 | +34.5 |
| Tue 27 Oct 07:20 | Bollinger bounce | buy | not opened | – | rejection at a level Tue 08:10 | -5.0 | -5.0 |
| Wed 11 Nov 15:10 | Bollinger bounce | buy | not opened | – | rejection at a level Wed 16:55 | -0.2 | -0.2 |

**3. Retest within 3 pips, 6 candles, no retest: enter anyway:** 24 breakout trades change (-226.0), 1 other trades change (-5.0); in all -231.0.

| Entry (UK) | Strategy | Way | Current rules | Pips | This version | Pips | Difference |
|---|---|---|---|---:|---|---:|---:|
| Tue 27 Oct 07:00 | breakout | sell | take profit Wed 07:10 | +50.0 | not opened | – | -50.0 |
| Wed 28 Oct 18:40 | breakout | buy | stop Wed 18:55 | -12.0 | not opened | – | +12.0 |
| Thu 29 Oct 14:45 | breakout | buy | take profit Fri 01:05 | +50.0 | not opened | – | -50.0 |
| Tue 03 Nov 13:45 | breakout | buy | stop Tue 13:50 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 14:50 | breakout | buy | stop Tue 15:10 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 14:55 | breakout | buy | not opened | – | stop Tue 15:10 | -12.0 | -12.0 |
| Tue 03 Nov 18:05 | breakout | buy | stop Tue 20:00 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:10 | breakout | buy | not opened | – | stop Tue 19:45 | -12.0 | -12.0 |
| Wed 04 Nov 20:05 | breakout | buy | stop Thu 10:00 | -12.0 | not opened | – | +12.0 |
| Wed 04 Nov 20:10 | breakout | buy | not opened | – | stop Wed 22:00 | -12.0 | -12.0 |
| Thu 05 Nov 07:05 | breakout | buy | not opened | – | stop Thu 07:15 | -12.0 | -12.0 |
| Thu 05 Nov 10:00 | breakout | sell | stop Thu 12:00 | -12.0 | not opened | – | +12.0 |
| Fri 06 Nov 17:50 | breakout | sell | 20:30 close Fri 20:30 | +3.8 | not opened | – | -3.8 |
| Fri 06 Nov 18:20 | breakout | sell | not opened | – | 20:30 close Fri 20:30 | -1.6 | -1.6 |
| Mon 09 Nov 07:55 | breakout | buy | take profit Mon 21:00 | +50.0 | not opened | – | -50.0 |
| Mon 09 Nov 09:55 | breakout | buy | not opened | – | stop Mon 15:05 | -12.0 | -12.0 |
| Mon 09 Nov 19:40 | breakout | buy | not opened | – | stop Tue 09:45 | -12.0 | -12.0 |
| Tue 10 Nov 09:10 | breakout | sell | take profit Tue 14:40 | +50.0 | not opened | – | -50.0 |
| Tue 10 Nov 13:10 | breakout | sell | not opened | – | stop Tue 13:30 | -12.0 | -12.0 |
| Wed 11 Nov 13:10 | breakout | sell | take profit Thu 02:35 | +50.0 | not opened | – | -50.0 |
| Wed 11 Nov 13:40 | breakout | sell | not opened | – | take profit Thu 15:00 | +50.0 | +50.0 |
| Thu 12 Nov 10:20 | breakout | buy | stop Thu 11:20 | -12.0 | not opened | – | +12.0 |
| Thu 12 Nov 11:30 | breakout | sell | still open at the end Thu 18:05 | +34.4 | not opened | – | -34.4 |
| Thu 12 Nov 15:05 | breakout | sell | not opened | – | still open at the end Thu 18:05 | +13.8 | +13.8 |
| Tue 27 Oct 07:20 | Bollinger bounce | buy | not opened | – | rejection at a level Tue 08:10 | -5.0 | -5.0 |

**3. Retest within 3 pips, 12 candles, no retest: enter anyway:** 23 breakout trades change (-265.7), 1 other trades change (-5.0); in all -270.7.

| Entry (UK) | Strategy | Way | Current rules | Pips | This version | Pips | Difference |
|---|---|---|---|---:|---|---:|---:|
| Tue 27 Oct 07:00 | breakout | sell | take profit Wed 07:10 | +50.0 | not opened | – | -50.0 |
| Wed 28 Oct 18:40 | breakout | buy | stop Wed 18:55 | -12.0 | not opened | – | +12.0 |
| Thu 29 Oct 14:45 | breakout | buy | take profit Fri 01:05 | +50.0 | not opened | – | -50.0 |
| Tue 03 Nov 13:45 | breakout | buy | stop Tue 13:50 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 14:50 | breakout | buy | stop Tue 15:10 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 14:55 | breakout | buy | not opened | – | stop Tue 15:10 | -12.0 | -12.0 |
| Tue 03 Nov 18:05 | breakout | buy | stop Tue 20:00 | -12.0 | not opened | – | +12.0 |
| Tue 03 Nov 18:10 | breakout | buy | not opened | – | stop Tue 19:45 | -12.0 | -12.0 |
| Wed 04 Nov 20:05 | breakout | buy | stop Thu 10:00 | -12.0 | not opened | – | +12.0 |
| Wed 04 Nov 20:10 | breakout | buy | not opened | – | stop Wed 22:00 | -12.0 | -12.0 |
| Thu 05 Nov 07:05 | breakout | buy | not opened | – | stop Thu 07:15 | -12.0 | -12.0 |
| Thu 05 Nov 10:00 | breakout | sell | stop Thu 12:00 | -12.0 | not opened | – | +12.0 |
| Fri 06 Nov 17:50 | breakout | sell | 20:30 close Fri 20:30 | +3.8 | not opened | – | -3.8 |
| Mon 09 Nov 07:55 | breakout | buy | take profit Mon 21:00 | +50.0 | not opened | – | -50.0 |
| Mon 09 Nov 09:55 | breakout | buy | not opened | – | stop Mon 15:05 | -12.0 | -12.0 |
| Mon 09 Nov 19:40 | breakout | buy | not opened | – | stop Tue 09:45 | -12.0 | -12.0 |
| Tue 10 Nov 09:10 | breakout | sell | take profit Tue 14:40 | +50.0 | not opened | – | -50.0 |
| Tue 10 Nov 13:10 | breakout | sell | not opened | – | stop Tue 13:30 | -12.0 | -12.0 |
| Wed 11 Nov 13:10 | breakout | sell | take profit Thu 02:35 | +50.0 | not opened | – | -50.0 |
| Wed 11 Nov 14:10 | breakout | sell | not opened | – | stop Wed 22:05 | -12.0 | -12.0 |
| Thu 12 Nov 10:20 | breakout | buy | stop Thu 11:20 | -12.0 | not opened | – | +12.0 |
| Thu 12 Nov 11:30 | breakout | sell | still open at the end Thu 18:05 | +34.4 | not opened | – | -34.4 |
| Thu 12 Nov 11:35 | breakout | sell | not opened | – | still open at the end Thu 18:05 | +34.5 | +34.5 |
| Tue 27 Oct 07:20 | Bollinger bounce | buy | not opened | – | rejection at a level Tue 08:10 | -5.0 | -5.0 |

### Today, Thursday 12 November

Current rules, trade by trade:

| Entry (UK) | Strategy | Way | Entry price | Exit | Pips |
|---|---|---|---:|---|---:|
| 02:55 | slow grind | sell | 13255.2 | stop Thu 07:40 | -15.0 |
| 10:20 | breakout | buy | 13277.4 | stop Thu 11:20 | -12.0 |
| 11:30 | breakout | sell | 13264.8 | still open at the end Thu 18:05 | +34.4 |
| **Total** | | | | | **+7.4** |

Each version today: its trades, and how they differ from the current rules:

| Version | Today | The 11:30 breakout sell | Other differences today |
|---|---:|---|---|
| **Current rules** | 3 (1–2) +7.4 | opens 11:30 at 13264.8, still open at the end Thu 18:05, +34.4 | none |
| 1. Two closes in a row beyond the band | 3 (1–2) -8.5 | opens 15:05 at 13243.1, still open at the end Thu 18:05, +12.7 | 06:20 range trade buy: new (before big news Thu 06:45, -6.2); 10:20 breakout buy: only in the current rules (-12.0) |
| 2. One close beyond the band by 1+ pips | 3 (1–2) -12.2 | opens 13:10 at 13254.2, stop Thu 13:40, -12.0; opens 15:00 at 13245.2, still open at the end Thu 18:05, +14.8 | 10:20 breakout buy: only in the current rules (-12.0) |
| 2. One close beyond the band by 2+ pips | 1 (0–1) -6.2 | does not open | 02:55 slow grind sell: only in the current rules (-15.0); 06:20 range trade buy: new (before big news Thu 06:45, -6.2); 10:20 breakout buy: only in the current rules (-12.0) |
| 2. One close beyond the band by 3+ pips | 1 (0–1) -6.2 | does not open | 02:55 slow grind sell: only in the current rules (-15.0); 06:20 range trade buy: new (before big news Thu 06:45, -6.2); 10:20 breakout buy: only in the current rules (-12.0) |
| 3. Retest within 1 pips, 6 candles, no retest: skip | 2 (1–1) +19.5 | opens 11:35 at 13264.9, still open at the end Thu 18:05, +34.5 | 10:20 breakout buy: only in the current rules (-12.0) |
| 3. Retest within 1 pips, 6 candles, no retest: enter anyway | 2 (0–2) -27.0 | opens 15:30 at 13230.9, stop Thu 16:10, -12.0 | 10:20 breakout buy: only in the current rules (-12.0) |
| 3. Retest within 1 pips, 12 candles, no retest: skip | 2 (1–1) +19.5 | opens 11:35 at 13264.9, still open at the end Thu 18:05, +34.5 | 10:20 breakout buy: only in the current rules (-12.0) |
| 3. Retest within 1 pips, 12 candles, no retest: enter anyway | 2 (1–1) +19.5 | opens 11:35 at 13264.9, still open at the end Thu 18:05, +34.5 | 10:20 breakout buy: only in the current rules (-12.0) |
| 3. Retest within 2 pips, 6 candles, no retest: skip | 2 (1–1) +19.5 | opens 11:35 at 13264.9, still open at the end Thu 18:05, +34.5 | 10:20 breakout buy: only in the current rules (-12.0) |
| 3. Retest within 2 pips, 6 candles, no retest: enter anyway | 2 (0–2) -27.0 | opens 15:30 at 13230.9, stop Thu 16:10, -12.0 | 10:20 breakout buy: only in the current rules (-12.0) |
| 3. Retest within 2 pips, 12 candles, no retest: skip | 2 (1–1) +19.5 | opens 11:35 at 13264.9, still open at the end Thu 18:05, +34.5 | 10:20 breakout buy: only in the current rules (-12.0) |
| 3. Retest within 2 pips, 12 candles, no retest: enter anyway | 2 (1–1) +19.5 | opens 11:35 at 13264.9, still open at the end Thu 18:05, +34.5 | 10:20 breakout buy: only in the current rules (-12.0) |
| 3. Retest within 3 pips, 6 candles, no retest: skip | 2 (1–1) +19.5 | opens 11:35 at 13264.9, still open at the end Thu 18:05, +34.5 | 10:20 breakout buy: only in the current rules (-12.0) |
| 3. Retest within 3 pips, 6 candles, no retest: enter anyway | 2 (1–1) -1.2 | opens 15:05 at 13244.2, still open at the end Thu 18:05, +13.8 | 10:20 breakout buy: only in the current rules (-12.0) |
| 3. Retest within 3 pips, 12 candles, no retest: skip | 2 (1–1) +19.5 | opens 11:35 at 13264.9, still open at the end Thu 18:05, +34.5 | 10:20 breakout buy: only in the current rules (-12.0) |
| 3. Retest within 3 pips, 12 candles, no retest: enter anyway | 2 (1–1) +19.5 | opens 11:35 at 13264.9, still open at the end Thu 18:05, +34.5 | 10:20 breakout buy: only in the current rules (-12.0) |
