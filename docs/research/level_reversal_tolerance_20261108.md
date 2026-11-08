# Level reversal: overshoot and allowance, 26 October to 6 November 2026

Read-only research on the stored GBPUSD 5-minute candles (Monday 26 October to Friday 6 November), on IG's prices. Nothing in the bot was changed. Written 8 November 2026. It follows `docs/research/new_strategies_20261108.md` (section 2, the level reversal).

## Method

- **Levels:** the bot's own levels (`levels/`, sell prices, daily candles midnight to midnight UK): the pivot, R1, R2, R3, S1, S2, S3 of the day, and round numbers ending in 00 (not 50).
- **IG's prices:** a buy opens on the buy price (the entry plus the spread at that candle's open) and is stopped and closed on the sell price; a sell opens on the sell price and is stopped and closed on the buy price. Levels and setups use the sell price.
- **Inside one 5-minute candle:** a scheduled close at its open; then the stop (filled at the candle's open if it opened past it); then the take profit (**stop counted first**). In the entry candle the stop counts only if the candle opened past the entry or closed beyond the stop (**the entry-candle stop correction**).
- **As before** (the earlier level reversal research): never opened in the first 15 minutes after the Sunday open or from 21:55 to 22:15 UK; new trades 06:00-20:30 UK; not in consolidation (the analyser's state after the last finished candle); no new trade in a big-news window and closed 15 minutes before big news (the news calendar starts on 31 October, so week 2 only); closed at 20:30 UK; one trade at a time for each test; several setups on the same candle and direction count once; no close on a rejection at a level. Weeks by entry time.
- **Marked** when the total is positive and one day gives at least 80% of it, or one week at least 90%.

**Limits:** two weeks only, and few touches of each kind of level (below); 5-minute candles, not ticks (the order of the high and low inside a candle is unknown); no slippage beyond candle-open gaps; GBPUSD only.

## 1. How far past the level price went before turning

Every time price **reached** a level (a candle's sell high at or above it, coming from below, when the candle before was below it; a buy-side touch is the mirror image), the episode is followed until one of:

- **reversed:** price comes back 15 pips on the side it came from, measured from the level (for a touch from below, a sell low at least 15 pips under the level). The **overshoot** is the furthest price went past the level before that (sell prices), counting the touching candle, and the candles after it up to (not including) the one that reversed;
- **broke through:** price went 50 pips past the level first;
- **no reversal within 12 hours.**

A new touch of the same level from the same side counts only after the last episode there has ended and price has been back on its side. Both sides of every level are counted (R1 reached from above is a touch too).

| Level | Touches | Reversed 15 pips | Broke through (50 past) | No reversal in 12 h | Typical overshoot (median) | Largest overshoot | 0-3 | 3-5 | 5-10 | 10-15 | 15-20 | 20+ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R1 | 7 | 3 | 3 | 1 | 0.6 | 21.0 | 2 | 0 | 0 | 0 | 0 | 1 |
| R2 | 12 | 7 | 0 | 5 | 6.3 | 11.6 | 2 | 0 | 3 | 2 | 0 | 0 |
| R3 | 8 | 4 | 0 | 4 | 15.0 | 19.3 | 0 | 0 | 1 | 1 | 2 | 0 |
| S1 | 11 | 7 | 2 | 2 | 6.5 | 16.1 | 2 | 1 | 1 | 2 | 1 | 0 |
| S2 | 6 | 3 | 1 | 2 | 5.0 | 11.5 | 1 | 0 | 1 | 1 | 0 | 0 |
| S3 | 5 | 4 | 0 | 1 | 4.9 | 14.8 | 2 | 0 | 1 | 1 | 0 | 0 |
| pivot | 24 | 16 | 3 | 5 | 10.4 | 24.0 | 1 | 2 | 5 | 4 | 2 | 2 |
| round 00 | 19 | 13 | 1 | 5 | 5.1 | 33.7 | 2 | 4 | 3 | 2 | 1 | 1 |

Overshoots in pips (sell prices), for each touch that reversed:

- **R1:** Wed 28 Oct 18:40 13336.8 from below 0.6; Wed 28 Oct 20:00 13336.8 from below 0.5; Fri 30 Oct 08:00 13412.7 from below 21.0.
- **R2:** Thu 29 Oct 15:50 13377.1 from below 2.3; Thu 29 Oct 20:55 13377.1 from above 11.1; Mon 02 Nov 06:10 13399.1 from above 6.3; Mon 02 Nov 22:35 13399.1 from above 0.9; Wed 04 Nov 01:50 13458.8 from above 7.5; Wed 04 Nov 04:55 13458.8 from above 11.6; Wed 04 Nov 16:35 13458.8 from above 5.5.
- **R3:** Mon 02 Nov 10:35 13405.9 from above 5.5; Wed 04 Nov 07:45 13483.8 from below 14.4; Wed 04 Nov 08:50 13483.8 from above 15.6; Wed 04 Nov 11:40 13483.8 from below 19.3.
- **S1:** Sun 25 Oct 21:45 13350.7 from above 2.0; Mon 26 Oct 07:55 13358.0 from below 3.8; Mon 26 Oct 17:25 13358.0 from below 1.1; Tue 27 Oct 07:05 13318.4 from above 11.2; Tue 27 Oct 09:55 13318.4 from below 16.1; Wed 28 Oct 06:30 13284.2 from above 11.7; Fri 06 Nov 04:20 13427.1 from below 6.5.
- **S2:** Mon 26 Oct 13:25 13338.6 from above 11.5; Fri 06 Nov 08:45 13399.1 from below 1.1; Fri 06 Nov 11:20 13399.1 from below 5.0.
- **S3:** Mon 26 Oct 13:55 13328.6 from above 1.5; Mon 26 Oct 21:55 13328.6 from above 0.8; Fri 06 Nov 13:30 13362.4 from above 8.4; Fri 06 Nov 14:35 13362.4 from below 14.8.
- **pivot:** Wed 28 Oct 16:50 13316.2 from below 4.9; Wed 28 Oct 18:55 13316.2 from above 0.0; Wed 28 Oct 21:15 13316.2 from above 13.7; Thu 29 Oct 00:15 13312.0 from above 9.5; Thu 29 Oct 00:45 13312.0 from below 24.0; Thu 29 Oct 05:50 13312.0 from above 7.7; Thu 29 Oct 08:30 13312.0 from above 16.0; Thu 29 Oct 13:15 13312.0 from above 11.6; Mon 02 Nov 00:40 13385.3 from above 6.2; Tue 03 Nov 00:05 13411.6 from below 3.3; Tue 03 Nov 15:25 13411.6 from above 5.8; Tue 03 Nov 20:55 13411.6 from above 8.9; Thu 05 Nov 08:00 13468.0 from above 22.8; Thu 05 Nov 12:00 13468.0 from below 13.3; Thu 05 Nov 14:05 13468.0 from below 18.0; Thu 05 Nov 15:50 13468.0 from above 11.3.
- **round 00:** Tue 27 Oct 21:35 13300.0 from below 12.3; Wed 28 Oct 15:20 13300.0 from above 5.1; Wed 28 Oct 17:50 13300.0 from above 11.6; Thu 29 Oct 09:20 13300.0 from above 4.0; Fri 30 Oct 01:05 13400.0 from below 6.5; Fri 30 Oct 01:30 13400.0 from above 19.8; Fri 30 Oct 06:25 13400.0 from below 33.7; Fri 30 Oct 16:00 13400.0 from below 6.0; Mon 02 Nov 22:30 13400.0 from above 3.9; Wed 04 Nov 13:00 13500.0 from below 3.1; Thu 05 Nov 07:05 13500.0 from below 0.4; Fri 06 Nov 08:45 13400.0 from below 0.2; Fri 06 Nov 11:20 13400.0 from below 4.1.

**Reading it:** very few touches of each kind (3 to 24 reversals over two weeks), so a median is a rough guide only. R2 and S2 overshot about 5-6 pips typically and never more than 12; R3 overshot the most typically (15 pips); the pivot overshot about 10 typically and up to 24; round 00s about 5 typically, with one of 34. Most R1 touches did not reverse 15 pips.

## 2. Entries with an allowance past the level

Entries come from the shared rejection part as the strategies use it (design 3.3: price reaches the level or comes within 3 pips of it, the reversal candle, the confirmation candle closing past the reversal candle's low (sell), entry when price breaks past the confirmation candle, at that point or at the candle's open if it opened past it; cancelled if price goes past the reversal candle's high). **The allowance:** the rejection counts for a kind of level only if the furthest point price reached from the piercing candle to the confirmation candle is no more than the allowance past that level (0, 3, 5, 10, 15 or 20 pips; at 0 it may not go past it at all, but may stop up to 3 pips short, as the rejection part allows). Each larger allowance includes everything a smaller one does. Each kind of level is tested on its own. **The stop** is 6, 12 or 15 pips beyond that furthest point (a price, triggered on IG's closing price, so for a sell the spread also counts), so each trade's stop distance from the entry is larger than 6, 12 or 15 pips: the biggest loss shows it. **Take profit** 20, 30 or 50 pips from the entry.

Of 1539 rejection triggers, those at these levels and allowed by the checks above (others: 59 in consolidation, 159 outside 06:00-20:30 UK, 0 in a big-news window, 1 at the Sunday open or the rollover) by kind of level, any overshoot: R1 14, R2 34, R3 34, S1 83, S2 25, S3 16, pivot 79, round 00 88.

### The best result for each kind of level and allowance

The best of the 9 stop / take profit combinations by total pips (the full tables follow).

| Level | Allowance | Stop | Take profit | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R1 | 0 | 6 | 50 | 2 | 1 | 1 | **+33.5** | -16.5 | 1 | -16.5 | +50.0 | **marked: one day gives +50.0 of +33.5; week 2 gives +50.0 of +33.5** |
| R1 | 3 | 15 | 50 | 3 | 1 | 2 | **+15.5** | -25.5 | 2 | -34.5 | +50.0 | **marked: one day gives +50.0 of +15.5; week 2 gives +50.0 of +15.5** |
| R1 | 5 | 15 | 50 | 4 | 2 | 2 | **+17.0** | -25.5 | 2 | -33.0 | +50.0 | **marked: one day gives +50.0 of +17.0; week 2 gives +50.0 of +17.0** |
| R1 | 10 | 15 | 50 | 4 | 2 | 2 | **+17.0** | -25.5 | 2 | -33.0 | +50.0 | **marked: one day gives +50.0 of +17.0; week 2 gives +50.0 of +17.0** |
| R1 | 15 | 15 | 50 | 4 | 2 | 2 | **+17.0** | -25.5 | 2 | -33.0 | +50.0 | **marked: one day gives +50.0 of +17.0; week 2 gives +50.0 of +17.0** |
| R1 | 20 | 15 | 50 | 4 | 2 | 2 | **+17.0** | -25.5 | 2 | -33.0 | +50.0 | **marked: one day gives +50.0 of +17.0; week 2 gives +50.0 of +17.0** |
| R2 | 0 | 6 | 30 | 3 | 2 | 1 | **+32.8** | -3.0 | 1 | +0.0 | +32.8 | **marked: one day gives +27.0 of +32.8; week 2 gives +32.8 of +32.8** |
| R2 | 3 | 6 | 20 | 6 | 2 | 4 | **+8.4** | -14.9 | 2 | -14.9 | +23.3 | **marked: one day gives +15.7 of +8.4; week 2 gives +23.3 of +8.4** |
| R2 | 5 | 6 | 30 | 6 | 3 | 3 | **+35.9** | -14.9 | 2 | -14.9 | +50.8 | **marked: one day gives +33.2 of +35.9; week 2 gives +50.8 of +35.9** |
| R2 | 10 | 6 | 30 | 7 | 3 | 4 | **+18.5** | -17.4 | 2 | -14.9 | +33.4 | **marked: one day gives +17.6 of +18.5; week 2 gives +33.4 of +18.5** |
| R2 | 15 | 6 | 30 | 7 | 3 | 4 | **+18.5** | -17.4 | 2 | -14.9 | +33.4 | **marked: one day gives +17.6 of +18.5; week 2 gives +33.4 of +18.5** |
| R2 | 20 | 6 | 30 | 7 | 3 | 4 | **+18.5** | -17.4 | 2 | -14.9 | +33.4 | **marked: one day gives +17.6 of +18.5; week 2 gives +33.4 of +18.5** |
| R3 | 0 | 6 | 20 | 3 | 0 | 3 | **-27.2** | -16.6 | 3 | +0.0 | -27.2 |  |
| R3 | 3 | 6 | 30 | 5 | 1 | 4 | **-18.8** | -19.6 | 4 | +0.0 | -18.8 |  |
| R3 | 5 | 12 | 30 | 4 | 1 | 3 | **-30.0** | -28.0 | 3 | +0.0 | -30.0 |  |
| R3 | 10 | 6 | 30 | 6 | 1 | 5 | **-29.8** | -22.0 | 5 | +0.0 | -29.8 |  |
| R3 | 15 | 6 | 20 | 5 | 3 | 2 | **+43.7** | -13.3 | 2 | +0.0 | +43.7 | **marked: one day gives +40.0 of +43.7; week 2 gives +43.7 of +43.7** |
| R3 | 20 | 6 | 20 | 5 | 3 | 2 | **+43.7** | -13.3 | 2 | +0.0 | +43.7 | **marked: one day gives +40.0 of +43.7; week 2 gives +43.7 of +43.7** |
| S1 | 0 | 12 | 50 | 6 | 4 | 2 | **+24.1** | -20.6 | 1 | -4.8 | +28.9 | **marked: one day gives +28.9 of +24.1; week 2 gives +28.9 of +24.1** |
| S1 | 3 | 12 | 50 | 5 | 3 | 2 | **+40.0** | -18.6 | 2 | +8.3 | +31.7 |  |
| S1 | 5 | 12 | 50 | 5 | 3 | 2 | **+39.2** | -21.0 | 2 | +7.5 | +31.7 | **marked: one day gives +31.7 of +39.2** |
| S1 | 10 | 12 | 50 | 5 | 3 | 2 | **+39.2** | -21.0 | 2 | +7.5 | +31.7 | **marked: one day gives +31.7 of +39.2** |
| S1 | 15 | 12 | 50 | 5 | 3 | 2 | **+39.2** | -21.0 | 2 | +7.5 | +31.7 | **marked: one day gives +31.7 of +39.2** |
| S1 | 20 | 12 | 50 | 5 | 3 | 2 | **+39.2** | -21.0 | 2 | +7.5 | +31.7 | **marked: one day gives +31.7 of +39.2** |
| S2 | 0 | 6 | 20 | 1 | 0 | 1 | **-8.6** | -8.6 | 1 | -8.6 | +0.0 |  |
| S2 | 3 | 6 | 20 | 3 | 0 | 3 | **-26.7** | -18.1 | 3 | -4.6 | -22.1 |  |
| S2 | 5 | 15 | 20 | 2 | 0 | 2 | **-38.9** | -21.7 | 2 | -21.7 | -17.2 |  |
| S2 | 10 | 15 | 20 | 2 | 0 | 2 | **-38.9** | -21.7 | 2 | -21.7 | -17.2 |  |
| S2 | 15 | 15 | 20 | 2 | 0 | 2 | **-38.9** | -21.7 | 2 | -21.7 | -17.2 |  |
| S2 | 20 | 15 | 20 | 2 | 0 | 2 | **-38.9** | -21.7 | 2 | -21.7 | -17.2 |  |
| S3 | 0 | 6 | 20 | 3 | 1 | 2 | **-40.6** | -21.5 | 2 | +1.3 | -41.9 |  |
| S3 | 3 | 12 | 20 | 3 | 1 | 2 | **-33.9** | -27.5 | 2 | +20.0 | -53.9 |  |
| S3 | 5 | 12 | 20 | 2 | 1 | 1 | **+19.6** | -0.4 | 1 | +20.0 | -0.4 | **marked: one day gives +20.0 of +19.6; week 1 gives +20.0 of +19.6** |
| S3 | 10 | 12 | 20 | 2 | 1 | 1 | **+19.6** | -0.4 | 1 | +20.0 | -0.4 | **marked: one day gives +20.0 of +19.6; week 1 gives +20.0 of +19.6** |
| S3 | 15 | 12 | 20 | 2 | 1 | 1 | **+19.6** | -0.4 | 1 | +20.0 | -0.4 | **marked: one day gives +20.0 of +19.6; week 1 gives +20.0 of +19.6** |
| S3 | 20 | 12 | 20 | 2 | 1 | 1 | **+19.6** | -0.4 | 1 | +20.0 | -0.4 | **marked: one day gives +20.0 of +19.6; week 1 gives +20.0 of +19.6** |
| pivot | 0 | 6 | 20 | 11 | 3 | 8 | **-69.2** | -23.4 | 6 | -16.8 | -52.4 |  |
| pivot | 3 | 12 | 20 | 11 | 2 | 9 | **-122.4** | -26.6 | 8 | -50.8 | -71.6 |  |
| pivot | 5 | 6 | 20 | 14 | 3 | 11 | **-105.6** | -20.6 | 8 | -27.2 | -78.4 |  |
| pivot | 10 | 12 | 20 | 10 | 4 | 5 | **-14.2** | -26.1 | 3 | +56.5 | -70.7 |  |
| pivot | 15 | 12 | 20 | 10 | 4 | 5 | **-5.3** | -24.3 | 3 | +56.5 | -61.8 |  |
| pivot | 20 | 12 | 20 | 10 | 4 | 5 | **-5.3** | -24.3 | 3 | +56.5 | -61.8 |  |
| round 00 | 0 | 12 | 20 | 9 | 6 | 3 | **+92.5** | -18.3 | 1 | +33.8 | +58.7 |  |
| round 00 | 3 | 6 | 20 | 15 | 7 | 8 | **+60.9** | -18.1 | 2 | +13.7 | +47.2 |  |
| round 00 | 5 | 6 | 20 | 15 | 8 | 7 | **+71.8** | -16.5 | 2 | +7.5 | +64.3 |  |
| round 00 | 10 | 15 | 30 | 12 | 6 | 6 | **+66.2** | -25.5 | 3 | +5.9 | +60.3 | **marked: one day gives +60.0 of +66.2; week 2 gives +60.3 of +66.2** |
| round 00 | 15 | 15 | 30 | 13 | 6 | 7 | **+51.6** | -25.5 | 3 | -8.7 | +60.3 | **marked: one day gives +60.0 of +51.6; week 2 gives +60.3 of +51.6** |
| round 00 | 20 | 15 | 30 | 13 | 6 | 7 | **+51.6** | -25.5 | 3 | -8.7 | +60.3 | **marked: one day gives +60.0 of +51.6; week 2 gives +60.3 of +51.6** |

**Positive results:** 149 of 432 combinations; 6 of them are positive in both weeks and not marked: round 00 allowance 0, stop 12, take profit 20 (+92.5, 9 trades), round 00 allowance 0, stop 15, take profit 20 (+89.5, 9 trades), round 00 allowance 0, stop 6, take profit 20 (+85.7, 10 trades), round 00 allowance 5, stop 6, take profit 20 (+71.8, 15 trades), round 00 allowance 3, stop 6, take profit 20 (+60.9, 15 trades), S1 allowance 3, stop 12, take profit 50 (+40.0, 5 trades).

Positive combinations by kind of level: R1 25 of 54, R2 20 of 54, R3 6 of 54, S1 38 of 54, S2 0 of 54, S3 24 of 54, pivot 0 of 54, round 00 36 of 54.

**Reading it:**

- **Round 00s** are the only kind positive in both weeks and not marked at more than one setting: with no allowance (0) and a 20-pip take profit, at every stop (+85.7 to +92.5 pips, 9-10 trades), and with an allowance of 3 or 5 pips, stop 6, take profit 20 (+60.9 and +71.8, 15 trades). Larger allowances and larger take profits do worse or rest on one day.
- **R2** is positive at most allowances but every positive result is marked (week 2 gives it all; 3 to 7 trades). **S2** is never positive (1 to 5 trades). So the expectation that R2 and S2 are accurate is not borne out by these few trades, although part 1 shows they overshot least.
- **R1, R3, S1, S3** overshoot more (part 1), and an allowance of 5 or more pips helped R3 and S3, but their positive results rest on 2 to 6 trades and nearly all are marked. One exception: S1 with an allowance of 3, stop 12, take profit 50 (+40.0, 5 trades, both weeks).
- **The pivot** is never positive at any allowance, stop or take profit.
- A larger allowance can give fewer trades: with one trade at a time, an extra entry can block later ones.
- Because the stop is placed beyond the furthest point, the distance from the entry to the stop is bigger than the stop setting (up to 65.5 pips), and so are the losses (the biggest -31.0 pips).

### Trades of the best result for each kind of level (where it is positive)

**R1, allowance 0, stop 6, take profit 50** (+33.5 pips, marked):

| Entry | Dir | Entry price | Level; furthest past it; state at entry | Stop distance | Closed | How | Pips |
|---|---|---|---|---|---|---|---|
| Fri 30 Oct 07:45 | SELL | 13401.6 | R1 13412.7; past it -0.6; trend up, slow grind | 16.5 | Fri 30 Oct 08:40 | stop | -16.5 |
| Mon 02 Nov 06:40 | BUY | 13397.1 | R1 13392.1; past it -0.7; emerging trend up | 11.2 | Mon 02 Nov 09:00 | take profit | +50.0 |

**R2, allowance 5, stop 6, take profit 30** (+35.9 pips, marked):

| Entry | Dir | Entry price | Level; furthest past it; state at entry | Stop distance | Closed | How | Pips |
|---|---|---|---|---|---|---|---|
| Thu 29 Oct 16:30 | SELL | 13367.4 | R2 13377.1; past it +1.7; emerging trend down | 17.4 | Thu 29 Oct 20:30 | closed by the clock | -14.9 |
| Mon 02 Nov 06:00 | SELL | 13397.7 | R2 13399.1; past it +2.0; emerging trend down | 9.4 | Mon 02 Nov 07:20 | stop | -9.4 |
| Mon 02 Nov 07:25 | BUY | 13409.5 | R2 13399.1; past it -1.0; trend up, slow grind | 16.3 | Mon 02 Nov 08:55 | take profit | +30.0 |
| Mon 02 Nov 11:15 | BUY | 13412.5 | R2 13399.1; past it -1.3; emerging trend up | 19.0 | Mon 02 Nov 20:30 | closed by the clock | -3.0 |
| Wed 04 Nov 07:20 | BUY | 13465.7 | R2 13458.8; past it +4.2; emerging trend up | 18.6 | Wed 04 Nov 10:15 | take profit | +30.0 |
| Wed 04 Nov 17:10 | BUY | 13468.3 | R2 13458.8; past it +4.7; trend down, slow grind | 21.7 | Wed 04 Nov 20:30 | closed by the clock | +3.2 |

**R3, allowance 15, stop 6, take profit 20** (+43.7 pips, marked):

| Entry | Dir | Entry price | Level; furthest past it; state at entry | Stop distance | Closed | How | Pips |
|---|---|---|---|---|---|---|---|
| Mon 02 Nov 08:00 | BUY | 13416.6 | R3 13405.9; past it +2.1; trend up, slow grind | 19.7 | Mon 02 Nov 08:50 | take profit | +20.0 |
| Mon 02 Nov 10:50 | SELL | 13402.5 | R3 13405.9; past it +3.9; emerging trend down | 13.3 | Mon 02 Nov 11:15 | stop | -13.3 |
| Mon 02 Nov 11:15 | BUY | 13412.5 | R3 13405.9; past it +5.2; emerging trend up | 18.7 | Mon 02 Nov 20:30 | closed by the clock | -3.0 |
| Wed 04 Nov 08:15 | BUY | 13479.2 | R3 13483.8; past it +13.8; trend up, slow grind | 16.7 | Wed 04 Nov 13:00 | take profit | +20.0 |
| Wed 04 Nov 14:30 | SELL | 13484.4 | R3 13483.8; past it +6.7; trend up, slow grind | 12.1 | Wed 04 Nov 15:15 | take profit | +20.0 |

**S1, allowance 3, stop 12, take profit 50** (+40.0 pips):

| Entry | Dir | Entry price | Level; furthest past it; state at entry | Stop distance | Closed | How | Pips |
|---|---|---|---|---|---|---|---|
| Mon 26 Oct 08:30 | SELL | 13353.7 | S1 13358.0; past it +2.7; trend down, slow grind | 19.0 | Mon 26 Oct 20:30 | closed by the clock | +11.4 |
| Tue 27 Oct 07:20 | BUY | 13324.5 | S1 13318.4; past it +2.6; trend down, slow grind | 21.6 | Tue 27 Oct 20:30 | closed by the clock | -16.1 |
| Wed 28 Oct 06:55 | SELL | 13277.3 | S1 13284.2; past it -0.3; trend down, slow grind | 18.6 | Wed 28 Oct 08:20 | stop | -18.6 |
| Wed 28 Oct 08:20 | BUY | 13291.8 | S1 13284.2; past it +0.1; trend down, slow grind | 20.6 | Wed 28 Oct 20:30 | closed by the clock | +31.6 |
| Fri 06 Nov 06:45 | SELL | 13419.0 | S1 13427.1; past it +0.2; emerging trend down | 20.3 | Fri 06 Nov 13:15 | closed by the clock | +31.7 |

**S3, allowance 5, stop 12, take profit 20** (+19.6 pips, marked):

| Entry | Dir | Entry price | Level; furthest past it; state at entry | Stop distance | Closed | How | Pips |
|---|---|---|---|---|---|---|---|
| Mon 26 Oct 14:10 | BUY | 13336.4 | S3 13328.6; past it +1.5; trend down, slow grind | 22.2 | Mon 26 Oct 17:25 | take profit | +20.0 |
| Fri 06 Nov 14:10 | SELL | 13351.0 | S3 13362.4; past it +4.5; trend down, strong push | 27.9 | Fri 06 Nov 20:30 | closed by the clock | -0.4 |

**round 00, allowance 0, stop 12, take profit 20** (+92.5 pips):

| Entry | Dir | Entry price | Level; furthest past it; state at entry | Stop distance | Closed | How | Pips |
|---|---|---|---|---|---|---|---|
| Wed 28 Oct 14:00 | SELL | 13292.8 | round 00 13300.0; past it -0.9; trend up, slow grind | 18.3 | Wed 28 Oct 16:25 | stop | -18.3 |
| Thu 29 Oct 10:00 | BUY | 13311.5 | round 00 13300.0; past it -2.7; trend down, slow grind | 21.7 | Thu 29 Oct 12:30 | take profit | +20.0 |
| Thu 29 Oct 13:30 | BUY | 13320.4 | round 00 13300.0; past it -0.4; trend down, slow grind | 32.9 | Thu 29 Oct 14:20 | take profit | +20.0 |
| Fri 30 Oct 07:30 | BUY | 13411.0 | round 00 13400.0; past it -0.1; emerging trend up | 23.8 | Fri 30 Oct 10:05 | take profit | +20.0 |
| Fri 30 Oct 13:45 | SELL | 13389.3 | round 00 13400.0; past it -2.0; trend down, slow grind | 20.7 | Fri 30 Oct 20:30 | closed by the clock | -7.9 |
| Mon 02 Nov 07:25 | BUY | 13409.5 | round 00 13400.0; past it -0.1; trend up, slow grind | 22.3 | Mon 02 Nov 08:40 | take profit | +20.0 |
| Mon 02 Nov 11:05 | BUY | 13410.8 | round 00 13400.0; past it -0.4; emerging trend up | 23.3 | Mon 02 Nov 20:30 | closed by the clock | -1.3 |
| Tue 03 Nov 11:50 | BUY | 13408.3 | round 00 13400.0; past it -1.7; emerging trend up | 20.1 | Tue 03 Nov 13:30 | take profit | +20.0 |
| Wed 04 Nov 12:40 | SELL | 13487.4 | round 00 13500.0; past it -0.3; emerging trend down | 24.3 | Wed 04 Nov 15:15 | take profit | +20.0 |

## Summary

- **Overshoot (part 1):** typical overshoot before a 15-pip reversal: R2 6.3, S2 5.0, S3 4.9, round 00 5.1, S1 6.5, pivot 10.4, R3 15.0 pips (R1: only 3 reversals). Largest: round 00 33.7, pivot 24.0, R1 21.0, R3 19.3, S1 16.1, S3 14.8, R2 11.6, S2 11.5. 3 to 16 reversals per kind, so these are rough.
- **Entries (part 2):** only round 00s give results positive in both weeks and not marked at several settings, best with no allowance and a 20-pip take profit (+85.7 to +92.5 pips on 9-10 trades). The pivot and S2 never make money; R1, R2, R3, S1 and S3 make money only on a handful of trades, nearly always from one day or week.
- Two weeks and a few trades per kind of level: not enough to choose settings from.

## Full tables

### R1

| Allowance | Stop | Take profit | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 6 | 20 | 2 | 1 | 1 | **+3.5** | -16.5 | 1 | -16.5 | +20.0 | **marked: one day gives +20.0 of +3.5; week 2 gives +20.0 of +3.5** |
| 0 | 6 | 30 | 2 | 1 | 1 | **+13.5** | -16.5 | 1 | -16.5 | +30.0 | **marked: one day gives +30.0 of +13.5; week 2 gives +30.0 of +13.5** |
| 0 | 6 | 50 | 2 | 1 | 1 | **+33.5** | -16.5 | 1 | -16.5 | +50.0 | **marked: one day gives +50.0 of +33.5; week 2 gives +50.0 of +33.5** |
| 0 | 12 | 20 | 2 | 1 | 1 | **-2.5** | -22.5 | 1 | -22.5 | +20.0 |  |
| 0 | 12 | 30 | 2 | 1 | 1 | **+7.5** | -22.5 | 1 | -22.5 | +30.0 | **marked: one day gives +30.0 of +7.5; week 2 gives +30.0 of +7.5** |
| 0 | 12 | 50 | 2 | 1 | 1 | **+27.5** | -22.5 | 1 | -22.5 | +50.0 | **marked: one day gives +50.0 of +27.5; week 2 gives +50.0 of +27.5** |
| 0 | 15 | 20 | 2 | 1 | 1 | **-5.5** | -25.5 | 1 | -25.5 | +20.0 |  |
| 0 | 15 | 30 | 2 | 1 | 1 | **+4.5** | -25.5 | 1 | -25.5 | +30.0 | **marked: one day gives +30.0 of +4.5; week 2 gives +30.0 of +4.5** |
| 0 | 15 | 50 | 2 | 1 | 1 | **+24.5** | -25.5 | 1 | -25.5 | +50.0 | **marked: one day gives +50.0 of +24.5; week 2 gives +50.0 of +24.5** |
| 3 | 6 | 20 | 4 | 1 | 3 | **-19.6** | -16.5 | 3 | -39.6 | +20.0 |  |
| 3 | 6 | 30 | 4 | 1 | 3 | **-9.6** | -16.5 | 3 | -39.6 | +30.0 |  |
| 3 | 6 | 50 | 4 | 1 | 3 | **+10.4** | -16.5 | 3 | -39.6 | +50.0 | **marked: one day gives +50.0 of +10.4; week 2 gives +50.0 of +10.4** |
| 3 | 12 | 20 | 4 | 1 | 3 | **-33.8** | -22.5 | 3 | -53.8 | +20.0 |  |
| 3 | 12 | 30 | 4 | 1 | 3 | **-23.8** | -22.5 | 3 | -53.8 | +30.0 |  |
| 3 | 12 | 50 | 4 | 1 | 3 | **-3.8** | -22.5 | 3 | -53.8 | +50.0 |  |
| 3 | 15 | 20 | 3 | 1 | 2 | **-14.5** | -25.5 | 2 | -34.5 | +20.0 |  |
| 3 | 15 | 30 | 3 | 1 | 2 | **-4.5** | -25.5 | 2 | -34.5 | +30.0 |  |
| 3 | 15 | 50 | 3 | 1 | 2 | **+15.5** | -25.5 | 2 | -34.5 | +50.0 | **marked: one day gives +50.0 of +15.5; week 2 gives +50.0 of +15.5** |
| 5 | 6 | 20 | 5 | 2 | 3 | **+0.4** | -16.5 | 3 | -19.6 | +20.0 | **marked: one day gives +20.0 of +0.4; week 2 gives +20.0 of +0.4** |
| 5 | 6 | 30 | 5 | 2 | 3 | **-8.1** | -16.5 | 3 | -38.1 | +30.0 |  |
| 5 | 6 | 50 | 5 | 2 | 3 | **+11.9** | -16.5 | 3 | -38.1 | +50.0 | **marked: one day gives +50.0 of +11.9; week 2 gives +50.0 of +11.9** |
| 5 | 12 | 20 | 5 | 2 | 3 | **-13.8** | -22.5 | 3 | -33.8 | +20.0 |  |
| 5 | 12 | 30 | 5 | 2 | 3 | **-22.3** | -22.5 | 3 | -52.3 | +30.0 |  |
| 5 | 12 | 50 | 5 | 2 | 3 | **-2.3** | -22.5 | 3 | -52.3 | +50.0 |  |
| 5 | 15 | 20 | 4 | 2 | 2 | **+5.5** | -25.5 | 2 | -14.5 | +20.0 | **marked: one day gives +20.0 of +5.5; week 2 gives +20.0 of +5.5** |
| 5 | 15 | 30 | 4 | 2 | 2 | **-3.0** | -25.5 | 2 | -33.0 | +30.0 |  |
| 5 | 15 | 50 | 4 | 2 | 2 | **+17.0** | -25.5 | 2 | -33.0 | +50.0 | **marked: one day gives +50.0 of +17.0; week 2 gives +50.0 of +17.0** |
| 10 | 6 | 20 | 5 | 2 | 3 | **+0.4** | -16.5 | 3 | -19.6 | +20.0 | **marked: one day gives +20.0 of +0.4; week 2 gives +20.0 of +0.4** |
| 10 | 6 | 30 | 5 | 2 | 3 | **-8.1** | -16.5 | 3 | -38.1 | +30.0 |  |
| 10 | 6 | 50 | 5 | 2 | 3 | **+11.9** | -16.5 | 3 | -38.1 | +50.0 | **marked: one day gives +50.0 of +11.9; week 2 gives +50.0 of +11.9** |
| 10 | 12 | 20 | 5 | 2 | 3 | **-13.8** | -22.5 | 3 | -33.8 | +20.0 |  |
| 10 | 12 | 30 | 5 | 2 | 3 | **-22.3** | -22.5 | 3 | -52.3 | +30.0 |  |
| 10 | 12 | 50 | 5 | 2 | 3 | **-2.3** | -22.5 | 3 | -52.3 | +50.0 |  |
| 10 | 15 | 20 | 4 | 2 | 2 | **+5.5** | -25.5 | 2 | -14.5 | +20.0 | **marked: one day gives +20.0 of +5.5; week 2 gives +20.0 of +5.5** |
| 10 | 15 | 30 | 4 | 2 | 2 | **-3.0** | -25.5 | 2 | -33.0 | +30.0 |  |
| 10 | 15 | 50 | 4 | 2 | 2 | **+17.0** | -25.5 | 2 | -33.0 | +50.0 | **marked: one day gives +50.0 of +17.0; week 2 gives +50.0 of +17.0** |
| 15 | 6 | 20 | 5 | 2 | 3 | **+0.4** | -16.5 | 3 | -19.6 | +20.0 | **marked: one day gives +20.0 of +0.4; week 2 gives +20.0 of +0.4** |
| 15 | 6 | 30 | 5 | 2 | 3 | **-8.1** | -16.5 | 3 | -38.1 | +30.0 |  |
| 15 | 6 | 50 | 5 | 2 | 3 | **+11.9** | -16.5 | 3 | -38.1 | +50.0 | **marked: one day gives +50.0 of +11.9; week 2 gives +50.0 of +11.9** |
| 15 | 12 | 20 | 5 | 2 | 3 | **-13.8** | -22.5 | 3 | -33.8 | +20.0 |  |
| 15 | 12 | 30 | 5 | 2 | 3 | **-22.3** | -22.5 | 3 | -52.3 | +30.0 |  |
| 15 | 12 | 50 | 5 | 2 | 3 | **-2.3** | -22.5 | 3 | -52.3 | +50.0 |  |
| 15 | 15 | 20 | 4 | 2 | 2 | **+5.5** | -25.5 | 2 | -14.5 | +20.0 | **marked: one day gives +20.0 of +5.5; week 2 gives +20.0 of +5.5** |
| 15 | 15 | 30 | 4 | 2 | 2 | **-3.0** | -25.5 | 2 | -33.0 | +30.0 |  |
| 15 | 15 | 50 | 4 | 2 | 2 | **+17.0** | -25.5 | 2 | -33.0 | +50.0 | **marked: one day gives +50.0 of +17.0; week 2 gives +50.0 of +17.0** |
| 20 | 6 | 20 | 5 | 2 | 3 | **+0.4** | -16.5 | 3 | -19.6 | +20.0 | **marked: one day gives +20.0 of +0.4; week 2 gives +20.0 of +0.4** |
| 20 | 6 | 30 | 5 | 2 | 3 | **-8.1** | -16.5 | 3 | -38.1 | +30.0 |  |
| 20 | 6 | 50 | 5 | 2 | 3 | **+11.9** | -16.5 | 3 | -38.1 | +50.0 | **marked: one day gives +50.0 of +11.9; week 2 gives +50.0 of +11.9** |
| 20 | 12 | 20 | 5 | 2 | 3 | **-13.8** | -22.5 | 3 | -33.8 | +20.0 |  |
| 20 | 12 | 30 | 5 | 2 | 3 | **-22.3** | -22.5 | 3 | -52.3 | +30.0 |  |
| 20 | 12 | 50 | 5 | 2 | 3 | **-2.3** | -22.5 | 3 | -52.3 | +50.0 |  |
| 20 | 15 | 20 | 4 | 2 | 2 | **+5.5** | -25.5 | 2 | -14.5 | +20.0 | **marked: one day gives +20.0 of +5.5; week 2 gives +20.0 of +5.5** |
| 20 | 15 | 30 | 4 | 2 | 2 | **-3.0** | -25.5 | 2 | -33.0 | +30.0 |  |
| 20 | 15 | 50 | 4 | 2 | 2 | **+17.0** | -25.5 | 2 | -33.0 | +50.0 | **marked: one day gives +50.0 of +17.0; week 2 gives +50.0 of +17.0** |

### R2

| Allowance | Stop | Take profit | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 6 | 20 | 3 | 2 | 1 | **+22.8** | -3.0 | 1 | +0.0 | +22.8 | **marked: week 2 gives +22.8 of +22.8** |
| 0 | 6 | 30 | 3 | 2 | 1 | **+32.8** | -3.0 | 1 | +0.0 | +32.8 | **marked: one day gives +27.0 of +32.8; week 2 gives +32.8 of +32.8** |
| 0 | 6 | 50 | 2 | 1 | 0 | **+5.8** | +0.0 | 0 | +0.0 | +5.8 | **marked: one day gives +5.8 of +5.8; week 2 gives +5.8 of +5.8** |
| 0 | 12 | 20 | 3 | 2 | 1 | **+22.8** | -3.0 | 1 | +0.0 | +22.8 | **marked: week 2 gives +22.8 of +22.8** |
| 0 | 12 | 30 | 3 | 2 | 1 | **+32.8** | -3.0 | 1 | +0.0 | +32.8 | **marked: one day gives +27.0 of +32.8; week 2 gives +32.8 of +32.8** |
| 0 | 12 | 50 | 2 | 1 | 0 | **+5.8** | +0.0 | 0 | +0.0 | +5.8 | **marked: one day gives +5.8 of +5.8; week 2 gives +5.8 of +5.8** |
| 0 | 15 | 20 | 3 | 2 | 1 | **+22.8** | -3.0 | 1 | +0.0 | +22.8 | **marked: week 2 gives +22.8 of +22.8** |
| 0 | 15 | 30 | 3 | 2 | 1 | **+32.8** | -3.0 | 1 | +0.0 | +32.8 | **marked: one day gives +27.0 of +32.8; week 2 gives +32.8 of +32.8** |
| 0 | 15 | 50 | 2 | 1 | 0 | **+5.8** | +0.0 | 0 | +0.0 | +5.8 | **marked: one day gives +5.8 of +5.8; week 2 gives +5.8 of +5.8** |
| 3 | 6 | 20 | 6 | 2 | 4 | **+8.4** | -14.9 | 2 | -14.9 | +23.3 | **marked: one day gives +15.7 of +8.4; week 2 gives +23.3 of +8.4** |
| 3 | 6 | 30 | 5 | 1 | 4 | **-0.2** | -14.9 | 2 | -14.9 | +14.7 |  |
| 3 | 6 | 50 | 4 | 0 | 3 | **-27.2** | -14.9 | 2 | -14.9 | -12.3 |  |
| 3 | 12 | 20 | 6 | 2 | 4 | **+2.4** | -15.4 | 2 | -14.9 | +17.3 | **marked: one day gives +15.7 of +2.4; week 2 gives +17.3 of +2.4** |
| 3 | 12 | 30 | 5 | 1 | 4 | **-6.2** | -15.4 | 2 | -14.9 | +8.7 |  |
| 3 | 12 | 50 | 4 | 0 | 3 | **-33.2** | -15.4 | 2 | -14.9 | -18.3 |  |
| 3 | 15 | 20 | 6 | 2 | 4 | **-0.6** | -18.4 | 2 | -14.9 | +14.3 |  |
| 3 | 15 | 30 | 5 | 1 | 4 | **-9.2** | -18.4 | 2 | -14.9 | +5.7 |  |
| 3 | 15 | 50 | 4 | 0 | 4 | **-41.1** | -18.4 | 4 | -14.9 | -26.2 |  |
| 5 | 6 | 20 | 6 | 3 | 3 | **+15.9** | -14.9 | 2 | -14.9 | +30.8 | **marked: one day gives +23.2 of +15.9; week 2 gives +30.8 of +15.9** |
| 5 | 6 | 30 | 6 | 3 | 3 | **+35.9** | -14.9 | 2 | -14.9 | +50.8 | **marked: one day gives +33.2 of +35.9; week 2 gives +50.8 of +35.9** |
| 5 | 6 | 50 | 4 | 1 | 2 | **-18.5** | -14.9 | 2 | -14.9 | -3.6 |  |
| 5 | 12 | 20 | 6 | 3 | 3 | **+9.9** | -15.4 | 2 | -14.9 | +24.8 | **marked: one day gives +23.2 of +9.9; week 2 gives +24.8 of +9.9** |
| 5 | 12 | 30 | 6 | 3 | 3 | **+29.9** | -15.4 | 2 | -14.9 | +44.8 | **marked: one day gives +33.2 of +29.9; week 2 gives +44.8 of +29.9** |
| 5 | 12 | 50 | 4 | 1 | 2 | **-24.5** | -15.4 | 2 | -14.9 | -9.6 |  |
| 5 | 15 | 20 | 6 | 3 | 3 | **+6.9** | -18.4 | 2 | -14.9 | +21.8 | **marked: one day gives +23.2 of +6.9; week 2 gives +21.8 of +6.9** |
| 5 | 15 | 30 | 6 | 3 | 3 | **+26.9** | -18.4 | 2 | -14.9 | +41.8 | **marked: one day gives +33.2 of +26.9; week 2 gives +41.8 of +26.9** |
| 5 | 15 | 50 | 4 | 1 | 3 | **-32.4** | -18.4 | 3 | -14.9 | -17.5 |  |
| 10 | 6 | 20 | 7 | 3 | 4 | **-1.5** | -17.4 | 2 | -14.9 | +13.4 |  |
| 10 | 6 | 30 | 7 | 3 | 4 | **+18.5** | -17.4 | 2 | -14.9 | +33.4 | **marked: one day gives +17.6 of +18.5; week 2 gives +33.4 of +18.5** |
| 10 | 6 | 50 | 5 | 1 | 3 | **-37.8** | -17.4 | 2 | -14.9 | -22.9 |  |
| 10 | 12 | 20 | 7 | 3 | 4 | **-13.5** | -23.4 | 2 | -14.9 | +1.4 |  |
| 10 | 12 | 30 | 6 | 1 | 5 | **-29.6** | -23.4 | 3 | -14.9 | -14.7 |  |
| 10 | 12 | 50 | 5 | 0 | 4 | **-56.6** | -23.4 | 2 | -14.9 | -41.7 |  |
| 10 | 15 | 20 | 6 | 2 | 4 | **-39.5** | -26.4 | 2 | -14.9 | -24.6 |  |
| 10 | 15 | 30 | 6 | 2 | 4 | **-29.5** | -26.4 | 2 | -14.9 | -14.6 |  |
| 10 | 15 | 50 | 5 | 1 | 4 | **-61.4** | -26.4 | 4 | -14.9 | -46.5 |  |
| 15 | 6 | 20 | 7 | 3 | 4 | **-1.5** | -17.4 | 2 | -14.9 | +13.4 |  |
| 15 | 6 | 30 | 7 | 3 | 4 | **+18.5** | -17.4 | 2 | -14.9 | +33.4 | **marked: one day gives +17.6 of +18.5; week 2 gives +33.4 of +18.5** |
| 15 | 6 | 50 | 5 | 1 | 3 | **-37.8** | -17.4 | 2 | -14.9 | -22.9 |  |
| 15 | 12 | 20 | 7 | 3 | 4 | **-13.5** | -23.4 | 2 | -14.9 | +1.4 |  |
| 15 | 12 | 30 | 6 | 1 | 5 | **-29.6** | -23.4 | 3 | -14.9 | -14.7 |  |
| 15 | 12 | 50 | 5 | 0 | 4 | **-56.6** | -23.4 | 2 | -14.9 | -41.7 |  |
| 15 | 15 | 20 | 6 | 2 | 4 | **-39.5** | -26.4 | 2 | -14.9 | -24.6 |  |
| 15 | 15 | 30 | 6 | 2 | 4 | **-29.5** | -26.4 | 2 | -14.9 | -14.6 |  |
| 15 | 15 | 50 | 5 | 1 | 4 | **-61.4** | -26.4 | 4 | -14.9 | -46.5 |  |
| 20 | 6 | 20 | 7 | 3 | 4 | **-1.5** | -17.4 | 2 | -14.9 | +13.4 |  |
| 20 | 6 | 30 | 7 | 3 | 4 | **+18.5** | -17.4 | 2 | -14.9 | +33.4 | **marked: one day gives +17.6 of +18.5; week 2 gives +33.4 of +18.5** |
| 20 | 6 | 50 | 5 | 1 | 3 | **-37.8** | -17.4 | 2 | -14.9 | -22.9 |  |
| 20 | 12 | 20 | 7 | 3 | 4 | **-13.5** | -23.4 | 2 | -14.9 | +1.4 |  |
| 20 | 12 | 30 | 6 | 1 | 5 | **-29.6** | -23.4 | 3 | -14.9 | -14.7 |  |
| 20 | 12 | 50 | 5 | 0 | 4 | **-56.6** | -23.4 | 2 | -14.9 | -41.7 |  |
| 20 | 15 | 20 | 6 | 2 | 4 | **-39.5** | -26.4 | 2 | -14.9 | -24.6 |  |
| 20 | 15 | 30 | 6 | 2 | 4 | **-29.5** | -26.4 | 2 | -14.9 | -14.6 |  |
| 20 | 15 | 50 | 5 | 1 | 4 | **-61.4** | -26.4 | 4 | -14.9 | -46.5 |  |

### R3

| Allowance | Stop | Take profit | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 6 | 20 | 3 | 0 | 3 | **-27.2** | -16.6 | 3 | +0.0 | -27.2 |  |
| 0 | 6 | 30 | 3 | 0 | 3 | **-27.2** | -16.6 | 3 | +0.0 | -27.2 |  |
| 0 | 6 | 50 | 3 | 0 | 3 | **-27.2** | -16.6 | 3 | +0.0 | -27.2 |  |
| 0 | 12 | 20 | 3 | 0 | 3 | **-33.2** | -22.6 | 3 | +0.0 | -33.2 |  |
| 0 | 12 | 30 | 3 | 0 | 3 | **-33.2** | -22.6 | 3 | +0.0 | -33.2 |  |
| 0 | 12 | 50 | 3 | 0 | 3 | **-33.2** | -22.6 | 3 | +0.0 | -33.2 |  |
| 0 | 15 | 20 | 2 | 0 | 2 | **-34.3** | -25.6 | 2 | +0.0 | -34.3 |  |
| 0 | 15 | 30 | 2 | 0 | 2 | **-34.3** | -25.6 | 2 | +0.0 | -34.3 |  |
| 0 | 15 | 50 | 2 | 0 | 2 | **-34.3** | -25.6 | 2 | +0.0 | -34.3 |  |
| 3 | 6 | 20 | 5 | 1 | 4 | **-28.8** | -19.6 | 4 | +0.0 | -28.8 |  |
| 3 | 6 | 30 | 5 | 1 | 4 | **-18.8** | -19.6 | 4 | +0.0 | -18.8 |  |
| 3 | 6 | 50 | 4 | 0 | 4 | **-47.2** | -19.6 | 4 | +0.0 | -47.2 |  |
| 3 | 12 | 20 | 4 | 1 | 3 | **-38.9** | -25.6 | 3 | +0.0 | -38.9 |  |
| 3 | 12 | 30 | 4 | 1 | 3 | **-28.9** | -25.6 | 3 | +0.0 | -28.9 |  |
| 3 | 12 | 50 | 3 | 0 | 3 | **-57.3** | -25.6 | 3 | +0.0 | -57.3 |  |
| 3 | 15 | 20 | 4 | 1 | 3 | **-44.9** | -28.6 | 3 | +0.0 | -44.9 |  |
| 3 | 15 | 30 | 4 | 1 | 3 | **-34.9** | -28.6 | 3 | +0.0 | -34.9 |  |
| 3 | 15 | 50 | 3 | 0 | 3 | **-63.3** | -28.6 | 3 | +0.0 | -63.3 |  |
| 5 | 6 | 20 | 6 | 1 | 5 | **-45.5** | -22.0 | 5 | +0.0 | -45.5 |  |
| 5 | 6 | 30 | 6 | 1 | 5 | **-35.5** | -22.0 | 5 | +0.0 | -35.5 |  |
| 5 | 6 | 50 | 4 | 0 | 4 | **-50.6** | -22.0 | 4 | +0.0 | -50.6 |  |
| 5 | 12 | 20 | 4 | 1 | 3 | **-40.0** | -28.0 | 3 | +0.0 | -40.0 |  |
| 5 | 12 | 30 | 4 | 1 | 3 | **-30.0** | -28.0 | 3 | +0.0 | -30.0 |  |
| 5 | 12 | 50 | 2 | 0 | 2 | **-35.1** | -28.0 | 2 | +0.0 | -35.1 |  |
| 5 | 15 | 20 | 4 | 1 | 3 | **-46.0** | -31.0 | 3 | +0.0 | -46.0 |  |
| 5 | 15 | 30 | 4 | 1 | 3 | **-36.0** | -31.0 | 3 | +0.0 | -36.0 |  |
| 5 | 15 | 50 | 2 | 0 | 2 | **-38.1** | -31.0 | 2 | +0.0 | -38.1 |  |
| 10 | 6 | 20 | 6 | 1 | 5 | **-39.8** | -22.0 | 5 | +0.0 | -39.8 |  |
| 10 | 6 | 30 | 6 | 1 | 5 | **-29.8** | -22.0 | 5 | +0.0 | -29.8 |  |
| 10 | 6 | 50 | 4 | 0 | 4 | **-50.6** | -22.0 | 4 | +0.0 | -50.6 |  |
| 10 | 12 | 20 | 4 | 1 | 3 | **-40.0** | -28.0 | 3 | +0.0 | -40.0 |  |
| 10 | 12 | 30 | 4 | 1 | 3 | **-30.0** | -28.0 | 3 | +0.0 | -30.0 |  |
| 10 | 12 | 50 | 2 | 0 | 2 | **-35.1** | -28.0 | 2 | +0.0 | -35.1 |  |
| 10 | 15 | 20 | 4 | 1 | 3 | **-46.0** | -31.0 | 3 | +0.0 | -46.0 |  |
| 10 | 15 | 30 | 4 | 1 | 3 | **-36.0** | -31.0 | 3 | +0.0 | -36.0 |  |
| 10 | 15 | 50 | 2 | 0 | 2 | **-38.1** | -31.0 | 2 | +0.0 | -38.1 |  |
| 15 | 6 | 20 | 5 | 3 | 2 | **+43.7** | -13.3 | 2 | +0.0 | +43.7 | **marked: one day gives +40.0 of +43.7; week 2 gives +43.7 of +43.7** |
| 15 | 6 | 30 | 4 | 1 | 3 | **-3.0** | -16.7 | 3 | +0.0 | -3.0 |  |
| 15 | 6 | 50 | 2 | 0 | 2 | **-23.8** | -16.7 | 2 | +0.0 | -23.8 |  |
| 15 | 12 | 20 | 5 | 3 | 2 | **+28.0** | -19.3 | 2 | +0.0 | +28.0 | **marked: one day gives +40.0 of +28.0; week 2 gives +28.0 of +28.0** |
| 15 | 12 | 30 | 4 | 1 | 3 | **-24.7** | -22.7 | 3 | +0.0 | -24.7 |  |
| 15 | 12 | 50 | 2 | 0 | 2 | **-29.8** | -22.7 | 2 | +0.0 | -29.8 |  |
| 15 | 15 | 20 | 5 | 3 | 2 | **+25.0** | -22.3 | 2 | +0.0 | +25.0 | **marked: one day gives +40.0 of +25.0; week 2 gives +25.0 of +25.0** |
| 15 | 15 | 30 | 4 | 1 | 3 | **-30.7** | -25.7 | 3 | +0.0 | -30.7 |  |
| 15 | 15 | 50 | 2 | 0 | 2 | **-32.8** | -25.7 | 2 | +0.0 | -32.8 |  |
| 20 | 6 | 20 | 5 | 3 | 2 | **+43.7** | -13.3 | 2 | +0.0 | +43.7 | **marked: one day gives +40.0 of +43.7; week 2 gives +43.7 of +43.7** |
| 20 | 6 | 30 | 4 | 1 | 3 | **-3.0** | -16.7 | 3 | +0.0 | -3.0 |  |
| 20 | 6 | 50 | 2 | 0 | 2 | **-23.8** | -16.7 | 2 | +0.0 | -23.8 |  |
| 20 | 12 | 20 | 5 | 3 | 2 | **+28.0** | -19.3 | 2 | +0.0 | +28.0 | **marked: one day gives +40.0 of +28.0; week 2 gives +28.0 of +28.0** |
| 20 | 12 | 30 | 4 | 1 | 3 | **-24.7** | -22.7 | 3 | +0.0 | -24.7 |  |
| 20 | 12 | 50 | 2 | 0 | 2 | **-29.8** | -22.7 | 2 | +0.0 | -29.8 |  |
| 20 | 15 | 20 | 5 | 3 | 2 | **+25.0** | -22.3 | 2 | +0.0 | +25.0 | **marked: one day gives +40.0 of +25.0; week 2 gives +25.0 of +25.0** |
| 20 | 15 | 30 | 4 | 1 | 3 | **-30.7** | -25.7 | 3 | +0.0 | -30.7 |  |
| 20 | 15 | 50 | 2 | 0 | 2 | **-32.8** | -25.7 | 2 | +0.0 | -32.8 |  |

### S1

| Allowance | Stop | Take profit | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 6 | 20 | 7 | 3 | 4 | **-1.5** | -14.6 | 4 | -21.5 | +20.0 |  |
| 0 | 6 | 30 | 7 | 3 | 4 | **+18.5** | -14.6 | 4 | -11.5 | +30.0 | **marked: one day gives +30.0 of +18.5; week 2 gives +30.0 of +18.5** |
| 0 | 6 | 50 | 7 | 3 | 4 | **+18.8** | -14.6 | 4 | -10.1 | +28.9 | **marked: one day gives +28.9 of +18.8; week 2 gives +28.9 of +18.8** |
| 0 | 12 | 20 | 6 | 4 | 2 | **+3.8** | -20.6 | 1 | -16.2 | +20.0 | **marked: one day gives +20.0 of +3.8; week 2 gives +20.0 of +3.8** |
| 0 | 12 | 30 | 6 | 4 | 2 | **+23.8** | -20.6 | 1 | -6.2 | +30.0 | **marked: one day gives +30.0 of +23.8; week 2 gives +30.0 of +23.8** |
| 0 | 12 | 50 | 6 | 4 | 2 | **+24.1** | -20.6 | 1 | -4.8 | +28.9 | **marked: one day gives +28.9 of +24.1; week 2 gives +28.9 of +24.1** |
| 0 | 15 | 20 | 5 | 3 | 2 | **+1.7** | -21.6 | 2 | -18.3 | +20.0 | **marked: one day gives +20.0 of +1.7; week 2 gives +20.0 of +1.7** |
| 0 | 15 | 30 | 5 | 3 | 2 | **+21.7** | -21.6 | 2 | -8.3 | +30.0 | **marked: one day gives +30.0 of +21.7; week 2 gives +30.0 of +21.7** |
| 0 | 15 | 50 | 5 | 3 | 2 | **+22.0** | -21.6 | 2 | -6.9 | +28.9 | **marked: one day gives +28.9 of +22.0; week 2 gives +28.9 of +22.0** |
| 3 | 6 | 20 | 11 | 4 | 7 | **-24.4** | -19.8 | 7 | -44.4 | +20.0 |  |
| 3 | 6 | 30 | 10 | 3 | 7 | **-24.1** | -19.8 | 7 | -54.1 | +30.0 |  |
| 3 | 6 | 50 | 10 | 3 | 7 | **-18.2** | -19.8 | 7 | -49.9 | +31.7 |  |
| 3 | 12 | 20 | 6 | 4 | 2 | **+36.4** | -18.6 | 2 | +16.4 | +20.0 | **marked: one day gives +31.1 of +36.4** |
| 3 | 12 | 30 | 5 | 3 | 2 | **+36.7** | -18.6 | 2 | +6.7 | +30.0 | **marked: one day gives +30.0 of +36.7** |
| 3 | 12 | 50 | 5 | 3 | 2 | **+40.0** | -18.6 | 2 | +8.3 | +31.7 |  |
| 3 | 15 | 20 | 6 | 4 | 2 | **+33.4** | -21.6 | 2 | +13.4 | +20.0 | **marked: one day gives +31.1 of +33.4** |
| 3 | 15 | 30 | 5 | 3 | 2 | **+33.7** | -21.6 | 2 | +3.7 | +30.0 | **marked: one day gives +30.0 of +33.7** |
| 3 | 15 | 50 | 5 | 3 | 2 | **+36.8** | -21.6 | 2 | +5.1 | +31.7 | **marked: one day gives +31.7 of +36.8** |
| 5 | 6 | 20 | 11 | 5 | 6 | **-28.9** | -19.8 | 3 | -48.9 | +20.0 |  |
| 5 | 6 | 30 | 10 | 4 | 6 | **-26.8** | -19.8 | 3 | -56.8 | +30.0 |  |
| 5 | 6 | 50 | 10 | 4 | 6 | **-23.7** | -19.8 | 3 | -55.4 | +31.7 |  |
| 5 | 12 | 20 | 6 | 4 | 2 | **+34.0** | -21.0 | 2 | +14.0 | +20.0 | **marked: one day gives +31.1 of +34.0** |
| 5 | 12 | 30 | 5 | 3 | 2 | **+36.1** | -21.0 | 2 | +6.1 | +30.0 | **marked: one day gives +30.0 of +36.1** |
| 5 | 12 | 50 | 5 | 3 | 2 | **+39.2** | -21.0 | 2 | +7.5 | +31.7 | **marked: one day gives +31.7 of +39.2** |
| 5 | 15 | 20 | 6 | 4 | 2 | **+31.0** | -24.0 | 2 | +11.0 | +20.0 | **marked: one day gives +31.1 of +31.0** |
| 5 | 15 | 30 | 5 | 3 | 2 | **+33.1** | -24.0 | 2 | +3.1 | +30.0 | **marked: one day gives +30.0 of +33.1; week 2 gives +30.0 of +33.1** |
| 5 | 15 | 50 | 5 | 3 | 2 | **+36.2** | -24.0 | 2 | +4.5 | +31.7 | **marked: one day gives +31.7 of +36.2** |
| 10 | 6 | 20 | 11 | 5 | 6 | **-28.9** | -19.8 | 3 | -48.9 | +20.0 |  |
| 10 | 6 | 30 | 10 | 4 | 6 | **-26.8** | -19.8 | 3 | -56.8 | +30.0 |  |
| 10 | 6 | 50 | 10 | 4 | 6 | **-23.7** | -19.8 | 3 | -55.4 | +31.7 |  |
| 10 | 12 | 20 | 6 | 4 | 2 | **+34.0** | -21.0 | 2 | +14.0 | +20.0 | **marked: one day gives +31.1 of +34.0** |
| 10 | 12 | 30 | 5 | 3 | 2 | **+36.1** | -21.0 | 2 | +6.1 | +30.0 | **marked: one day gives +30.0 of +36.1** |
| 10 | 12 | 50 | 5 | 3 | 2 | **+39.2** | -21.0 | 2 | +7.5 | +31.7 | **marked: one day gives +31.7 of +39.2** |
| 10 | 15 | 20 | 6 | 4 | 2 | **+31.0** | -24.0 | 2 | +11.0 | +20.0 | **marked: one day gives +31.1 of +31.0** |
| 10 | 15 | 30 | 5 | 3 | 2 | **+33.1** | -24.0 | 2 | +3.1 | +30.0 | **marked: one day gives +30.0 of +33.1; week 2 gives +30.0 of +33.1** |
| 10 | 15 | 50 | 5 | 3 | 2 | **+36.2** | -24.0 | 2 | +4.5 | +31.7 | **marked: one day gives +31.7 of +36.2** |
| 15 | 6 | 20 | 11 | 5 | 6 | **-28.9** | -19.8 | 3 | -48.9 | +20.0 |  |
| 15 | 6 | 30 | 10 | 4 | 6 | **-26.8** | -19.8 | 3 | -56.8 | +30.0 |  |
| 15 | 6 | 50 | 10 | 4 | 6 | **-23.7** | -19.8 | 3 | -55.4 | +31.7 |  |
| 15 | 12 | 20 | 6 | 4 | 2 | **+34.0** | -21.0 | 2 | +14.0 | +20.0 | **marked: one day gives +31.1 of +34.0** |
| 15 | 12 | 30 | 5 | 3 | 2 | **+36.1** | -21.0 | 2 | +6.1 | +30.0 | **marked: one day gives +30.0 of +36.1** |
| 15 | 12 | 50 | 5 | 3 | 2 | **+39.2** | -21.0 | 2 | +7.5 | +31.7 | **marked: one day gives +31.7 of +39.2** |
| 15 | 15 | 20 | 6 | 4 | 2 | **+31.0** | -24.0 | 2 | +11.0 | +20.0 | **marked: one day gives +31.1 of +31.0** |
| 15 | 15 | 30 | 5 | 3 | 2 | **+33.1** | -24.0 | 2 | +3.1 | +30.0 | **marked: one day gives +30.0 of +33.1; week 2 gives +30.0 of +33.1** |
| 15 | 15 | 50 | 5 | 3 | 2 | **+36.2** | -24.0 | 2 | +4.5 | +31.7 | **marked: one day gives +31.7 of +36.2** |
| 20 | 6 | 20 | 11 | 5 | 6 | **-28.9** | -19.8 | 3 | -48.9 | +20.0 |  |
| 20 | 6 | 30 | 10 | 4 | 6 | **-26.8** | -19.8 | 3 | -56.8 | +30.0 |  |
| 20 | 6 | 50 | 10 | 4 | 6 | **-23.7** | -19.8 | 3 | -55.4 | +31.7 |  |
| 20 | 12 | 20 | 6 | 4 | 2 | **+34.0** | -21.0 | 2 | +14.0 | +20.0 | **marked: one day gives +31.1 of +34.0** |
| 20 | 12 | 30 | 5 | 3 | 2 | **+36.1** | -21.0 | 2 | +6.1 | +30.0 | **marked: one day gives +30.0 of +36.1** |
| 20 | 12 | 50 | 5 | 3 | 2 | **+39.2** | -21.0 | 2 | +7.5 | +31.7 | **marked: one day gives +31.7 of +39.2** |
| 20 | 15 | 20 | 6 | 4 | 2 | **+31.0** | -24.0 | 2 | +11.0 | +20.0 | **marked: one day gives +31.1 of +31.0** |
| 20 | 15 | 30 | 5 | 3 | 2 | **+33.1** | -24.0 | 2 | +3.1 | +30.0 | **marked: one day gives +30.0 of +33.1; week 2 gives +30.0 of +33.1** |
| 20 | 15 | 50 | 5 | 3 | 2 | **+36.2** | -24.0 | 2 | +4.5 | +31.7 | **marked: one day gives +31.7 of +36.2** |

### S2

| Allowance | Stop | Take profit | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 6 | 20 | 1 | 0 | 1 | **-8.6** | -8.6 | 1 | -8.6 | +0.0 |  |
| 0 | 6 | 30 | 1 | 0 | 1 | **-8.6** | -8.6 | 1 | -8.6 | +0.0 |  |
| 0 | 6 | 50 | 1 | 0 | 1 | **-8.6** | -8.6 | 1 | -8.6 | +0.0 |  |
| 0 | 12 | 20 | 1 | 0 | 1 | **-8.6** | -8.6 | 1 | -8.6 | +0.0 |  |
| 0 | 12 | 30 | 1 | 0 | 1 | **-8.6** | -8.6 | 1 | -8.6 | +0.0 |  |
| 0 | 12 | 50 | 1 | 0 | 1 | **-8.6** | -8.6 | 1 | -8.6 | +0.0 |  |
| 0 | 15 | 20 | 1 | 0 | 1 | **-8.6** | -8.6 | 1 | -8.6 | +0.0 |  |
| 0 | 15 | 30 | 1 | 0 | 1 | **-8.6** | -8.6 | 1 | -8.6 | +0.0 |  |
| 0 | 15 | 50 | 1 | 0 | 1 | **-8.6** | -8.6 | 1 | -8.6 | +0.0 |  |
| 3 | 6 | 20 | 3 | 0 | 3 | **-26.7** | -18.1 | 3 | -4.6 | -22.1 |  |
| 3 | 6 | 30 | 3 | 0 | 3 | **-26.7** | -18.1 | 3 | -4.6 | -22.1 |  |
| 3 | 6 | 50 | 3 | 0 | 3 | **-26.7** | -18.1 | 3 | -4.6 | -22.1 |  |
| 3 | 12 | 20 | 3 | 0 | 3 | **-32.7** | -24.1 | 3 | -4.6 | -28.1 |  |
| 3 | 12 | 30 | 3 | 0 | 3 | **-32.7** | -24.1 | 3 | -4.6 | -28.1 |  |
| 3 | 12 | 50 | 3 | 0 | 3 | **-32.7** | -24.1 | 3 | -4.6 | -28.1 |  |
| 3 | 15 | 20 | 3 | 0 | 3 | **-35.7** | -27.1 | 3 | -4.6 | -31.1 |  |
| 3 | 15 | 30 | 3 | 0 | 3 | **-35.7** | -27.1 | 3 | -4.6 | -31.1 |  |
| 3 | 15 | 50 | 3 | 0 | 3 | **-35.7** | -27.1 | 3 | -4.6 | -31.1 |  |
| 5 | 6 | 20 | 5 | 0 | 5 | **-51.5** | -15.3 | 5 | -17.3 | -34.2 |  |
| 5 | 6 | 30 | 5 | 0 | 5 | **-51.5** | -15.3 | 5 | -17.3 | -34.2 |  |
| 5 | 6 | 50 | 5 | 0 | 5 | **-51.5** | -15.3 | 5 | -17.3 | -34.2 |  |
| 5 | 12 | 20 | 4 | 0 | 4 | **-64.9** | -21.3 | 4 | -18.7 | -46.2 |  |
| 5 | 12 | 30 | 4 | 0 | 4 | **-64.9** | -21.3 | 4 | -18.7 | -46.2 |  |
| 5 | 12 | 50 | 4 | 0 | 4 | **-64.9** | -21.3 | 4 | -18.7 | -46.2 |  |
| 5 | 15 | 20 | 2 | 0 | 2 | **-38.9** | -21.7 | 2 | -21.7 | -17.2 |  |
| 5 | 15 | 30 | 2 | 0 | 2 | **-38.9** | -21.7 | 2 | -21.7 | -17.2 |  |
| 5 | 15 | 50 | 2 | 0 | 2 | **-38.9** | -21.7 | 2 | -21.7 | -17.2 |  |
| 10 | 6 | 20 | 5 | 0 | 5 | **-51.5** | -15.3 | 5 | -17.3 | -34.2 |  |
| 10 | 6 | 30 | 5 | 0 | 5 | **-51.5** | -15.3 | 5 | -17.3 | -34.2 |  |
| 10 | 6 | 50 | 5 | 0 | 5 | **-51.5** | -15.3 | 5 | -17.3 | -34.2 |  |
| 10 | 12 | 20 | 4 | 0 | 4 | **-64.9** | -21.3 | 4 | -18.7 | -46.2 |  |
| 10 | 12 | 30 | 4 | 0 | 4 | **-64.9** | -21.3 | 4 | -18.7 | -46.2 |  |
| 10 | 12 | 50 | 4 | 0 | 4 | **-64.9** | -21.3 | 4 | -18.7 | -46.2 |  |
| 10 | 15 | 20 | 2 | 0 | 2 | **-38.9** | -21.7 | 2 | -21.7 | -17.2 |  |
| 10 | 15 | 30 | 2 | 0 | 2 | **-38.9** | -21.7 | 2 | -21.7 | -17.2 |  |
| 10 | 15 | 50 | 2 | 0 | 2 | **-38.9** | -21.7 | 2 | -21.7 | -17.2 |  |
| 15 | 6 | 20 | 5 | 0 | 5 | **-51.5** | -15.3 | 5 | -17.3 | -34.2 |  |
| 15 | 6 | 30 | 5 | 0 | 5 | **-51.5** | -15.3 | 5 | -17.3 | -34.2 |  |
| 15 | 6 | 50 | 5 | 0 | 5 | **-51.5** | -15.3 | 5 | -17.3 | -34.2 |  |
| 15 | 12 | 20 | 4 | 0 | 4 | **-64.9** | -21.3 | 4 | -18.7 | -46.2 |  |
| 15 | 12 | 30 | 4 | 0 | 4 | **-64.9** | -21.3 | 4 | -18.7 | -46.2 |  |
| 15 | 12 | 50 | 4 | 0 | 4 | **-64.9** | -21.3 | 4 | -18.7 | -46.2 |  |
| 15 | 15 | 20 | 2 | 0 | 2 | **-38.9** | -21.7 | 2 | -21.7 | -17.2 |  |
| 15 | 15 | 30 | 2 | 0 | 2 | **-38.9** | -21.7 | 2 | -21.7 | -17.2 |  |
| 15 | 15 | 50 | 2 | 0 | 2 | **-38.9** | -21.7 | 2 | -21.7 | -17.2 |  |
| 20 | 6 | 20 | 5 | 0 | 5 | **-51.5** | -15.3 | 5 | -17.3 | -34.2 |  |
| 20 | 6 | 30 | 5 | 0 | 5 | **-51.5** | -15.3 | 5 | -17.3 | -34.2 |  |
| 20 | 6 | 50 | 5 | 0 | 5 | **-51.5** | -15.3 | 5 | -17.3 | -34.2 |  |
| 20 | 12 | 20 | 4 | 0 | 4 | **-64.9** | -21.3 | 4 | -18.7 | -46.2 |  |
| 20 | 12 | 30 | 4 | 0 | 4 | **-64.9** | -21.3 | 4 | -18.7 | -46.2 |  |
| 20 | 12 | 50 | 4 | 0 | 4 | **-64.9** | -21.3 | 4 | -18.7 | -46.2 |  |
| 20 | 15 | 20 | 2 | 0 | 2 | **-38.9** | -21.7 | 2 | -21.7 | -17.2 |  |
| 20 | 15 | 30 | 2 | 0 | 2 | **-38.9** | -21.7 | 2 | -21.7 | -17.2 |  |
| 20 | 15 | 50 | 2 | 0 | 2 | **-38.9** | -21.7 | 2 | -21.7 | -17.2 |  |

### S3

| Allowance | Stop | Take profit | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 6 | 20 | 3 | 1 | 2 | **-40.6** | -21.5 | 2 | +1.3 | -41.9 |  |
| 0 | 6 | 30 | 3 | 1 | 2 | **-40.6** | -21.5 | 2 | +1.3 | -41.9 |  |
| 0 | 6 | 50 | 3 | 1 | 2 | **-40.6** | -21.5 | 2 | +1.3 | -41.9 |  |
| 0 | 12 | 20 | 3 | 1 | 2 | **-52.6** | -27.5 | 2 | +1.3 | -53.9 |  |
| 0 | 12 | 30 | 3 | 1 | 2 | **-52.6** | -27.5 | 2 | +1.3 | -53.9 |  |
| 0 | 12 | 50 | 3 | 1 | 2 | **-52.6** | -27.5 | 2 | +1.3 | -53.9 |  |
| 0 | 15 | 20 | 3 | 1 | 2 | **-58.6** | -30.5 | 2 | +1.3 | -59.9 |  |
| 0 | 15 | 30 | 3 | 1 | 2 | **-58.6** | -30.5 | 2 | +1.3 | -59.9 |  |
| 0 | 15 | 50 | 3 | 1 | 2 | **-58.6** | -30.5 | 2 | +1.3 | -59.9 |  |
| 3 | 6 | 20 | 4 | 1 | 3 | **-38.2** | -21.5 | 3 | +20.0 | -58.2 |  |
| 3 | 6 | 30 | 4 | 1 | 3 | **-54.1** | -21.5 | 3 | +4.1 | -58.2 |  |
| 3 | 6 | 50 | 4 | 1 | 3 | **-54.1** | -21.5 | 3 | +4.1 | -58.2 |  |
| 3 | 12 | 20 | 3 | 1 | 2 | **-33.9** | -27.5 | 2 | +20.0 | -53.9 |  |
| 3 | 12 | 30 | 3 | 1 | 2 | **-49.8** | -27.5 | 2 | +4.1 | -53.9 |  |
| 3 | 12 | 50 | 3 | 1 | 2 | **-49.8** | -27.5 | 2 | +4.1 | -53.9 |  |
| 3 | 15 | 20 | 3 | 1 | 2 | **-39.9** | -30.5 | 2 | +20.0 | -59.9 |  |
| 3 | 15 | 30 | 3 | 1 | 2 | **-55.8** | -30.5 | 2 | +4.1 | -59.9 |  |
| 3 | 15 | 50 | 3 | 1 | 2 | **-55.8** | -30.5 | 2 | +4.1 | -59.9 |  |
| 5 | 6 | 20 | 5 | 1 | 4 | **-40.2** | -21.9 | 4 | +20.0 | -60.2 |  |
| 5 | 6 | 30 | 5 | 1 | 4 | **-56.1** | -21.9 | 4 | +4.1 | -60.2 |  |
| 5 | 6 | 50 | 5 | 1 | 4 | **-56.1** | -21.9 | 4 | +4.1 | -60.2 |  |
| 5 | 12 | 20 | 2 | 1 | 1 | **+19.6** | -0.4 | 1 | +20.0 | -0.4 | **marked: one day gives +20.0 of +19.6; week 1 gives +20.0 of +19.6** |
| 5 | 12 | 30 | 2 | 1 | 1 | **+3.7** | -0.4 | 1 | +4.1 | -0.4 | **marked: one day gives +4.1 of +3.7; week 1 gives +4.1 of +3.7** |
| 5 | 12 | 50 | 2 | 1 | 1 | **+3.7** | -0.4 | 1 | +4.1 | -0.4 | **marked: one day gives +4.1 of +3.7; week 1 gives +4.1 of +3.7** |
| 5 | 15 | 20 | 2 | 1 | 1 | **+19.6** | -0.4 | 1 | +20.0 | -0.4 | **marked: one day gives +20.0 of +19.6; week 1 gives +20.0 of +19.6** |
| 5 | 15 | 30 | 2 | 1 | 1 | **+3.7** | -0.4 | 1 | +4.1 | -0.4 | **marked: one day gives +4.1 of +3.7; week 1 gives +4.1 of +3.7** |
| 5 | 15 | 50 | 2 | 1 | 1 | **+3.7** | -0.4 | 1 | +4.1 | -0.4 | **marked: one day gives +4.1 of +3.7; week 1 gives +4.1 of +3.7** |
| 10 | 6 | 20 | 4 | 1 | 3 | **-24.5** | -22.1 | 3 | +20.0 | -44.5 |  |
| 10 | 6 | 30 | 4 | 1 | 3 | **-40.4** | -22.1 | 3 | +4.1 | -44.5 |  |
| 10 | 6 | 50 | 4 | 1 | 3 | **-40.4** | -22.1 | 3 | +4.1 | -44.5 |  |
| 10 | 12 | 20 | 2 | 1 | 1 | **+19.6** | -0.4 | 1 | +20.0 | -0.4 | **marked: one day gives +20.0 of +19.6; week 1 gives +20.0 of +19.6** |
| 10 | 12 | 30 | 2 | 1 | 1 | **+3.7** | -0.4 | 1 | +4.1 | -0.4 | **marked: one day gives +4.1 of +3.7; week 1 gives +4.1 of +3.7** |
| 10 | 12 | 50 | 2 | 1 | 1 | **+3.7** | -0.4 | 1 | +4.1 | -0.4 | **marked: one day gives +4.1 of +3.7; week 1 gives +4.1 of +3.7** |
| 10 | 15 | 20 | 2 | 1 | 1 | **+19.6** | -0.4 | 1 | +20.0 | -0.4 | **marked: one day gives +20.0 of +19.6; week 1 gives +20.0 of +19.6** |
| 10 | 15 | 30 | 2 | 1 | 1 | **+3.7** | -0.4 | 1 | +4.1 | -0.4 | **marked: one day gives +4.1 of +3.7; week 1 gives +4.1 of +3.7** |
| 10 | 15 | 50 | 2 | 1 | 1 | **+3.7** | -0.4 | 1 | +4.1 | -0.4 | **marked: one day gives +4.1 of +3.7; week 1 gives +4.1 of +3.7** |
| 15 | 6 | 20 | 4 | 1 | 3 | **-24.5** | -22.1 | 3 | +20.0 | -44.5 |  |
| 15 | 6 | 30 | 4 | 1 | 3 | **-40.4** | -22.1 | 3 | +4.1 | -44.5 |  |
| 15 | 6 | 50 | 4 | 1 | 3 | **-40.4** | -22.1 | 3 | +4.1 | -44.5 |  |
| 15 | 12 | 20 | 2 | 1 | 1 | **+19.6** | -0.4 | 1 | +20.0 | -0.4 | **marked: one day gives +20.0 of +19.6; week 1 gives +20.0 of +19.6** |
| 15 | 12 | 30 | 2 | 1 | 1 | **+3.7** | -0.4 | 1 | +4.1 | -0.4 | **marked: one day gives +4.1 of +3.7; week 1 gives +4.1 of +3.7** |
| 15 | 12 | 50 | 2 | 1 | 1 | **+3.7** | -0.4 | 1 | +4.1 | -0.4 | **marked: one day gives +4.1 of +3.7; week 1 gives +4.1 of +3.7** |
| 15 | 15 | 20 | 2 | 1 | 1 | **+19.6** | -0.4 | 1 | +20.0 | -0.4 | **marked: one day gives +20.0 of +19.6; week 1 gives +20.0 of +19.6** |
| 15 | 15 | 30 | 2 | 1 | 1 | **+3.7** | -0.4 | 1 | +4.1 | -0.4 | **marked: one day gives +4.1 of +3.7; week 1 gives +4.1 of +3.7** |
| 15 | 15 | 50 | 2 | 1 | 1 | **+3.7** | -0.4 | 1 | +4.1 | -0.4 | **marked: one day gives +4.1 of +3.7; week 1 gives +4.1 of +3.7** |
| 20 | 6 | 20 | 4 | 1 | 3 | **-24.5** | -22.1 | 3 | +20.0 | -44.5 |  |
| 20 | 6 | 30 | 4 | 1 | 3 | **-40.4** | -22.1 | 3 | +4.1 | -44.5 |  |
| 20 | 6 | 50 | 4 | 1 | 3 | **-40.4** | -22.1 | 3 | +4.1 | -44.5 |  |
| 20 | 12 | 20 | 2 | 1 | 1 | **+19.6** | -0.4 | 1 | +20.0 | -0.4 | **marked: one day gives +20.0 of +19.6; week 1 gives +20.0 of +19.6** |
| 20 | 12 | 30 | 2 | 1 | 1 | **+3.7** | -0.4 | 1 | +4.1 | -0.4 | **marked: one day gives +4.1 of +3.7; week 1 gives +4.1 of +3.7** |
| 20 | 12 | 50 | 2 | 1 | 1 | **+3.7** | -0.4 | 1 | +4.1 | -0.4 | **marked: one day gives +4.1 of +3.7; week 1 gives +4.1 of +3.7** |
| 20 | 15 | 20 | 2 | 1 | 1 | **+19.6** | -0.4 | 1 | +20.0 | -0.4 | **marked: one day gives +20.0 of +19.6; week 1 gives +20.0 of +19.6** |
| 20 | 15 | 30 | 2 | 1 | 1 | **+3.7** | -0.4 | 1 | +4.1 | -0.4 | **marked: one day gives +4.1 of +3.7; week 1 gives +4.1 of +3.7** |
| 20 | 15 | 50 | 2 | 1 | 1 | **+3.7** | -0.4 | 1 | +4.1 | -0.4 | **marked: one day gives +4.1 of +3.7; week 1 gives +4.1 of +3.7** |

### pivot

| Allowance | Stop | Take profit | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 6 | 20 | 11 | 3 | 8 | **-69.2** | -23.4 | 6 | -16.8 | -52.4 |  |
| 0 | 6 | 30 | 11 | 2 | 9 | **-106.4** | -23.4 | 7 | -54.0 | -52.4 |  |
| 0 | 6 | 50 | 11 | 2 | 9 | **-106.4** | -23.4 | 7 | -54.0 | -52.4 |  |
| 0 | 12 | 20 | 9 | 2 | 7 | **-93.0** | -26.6 | 6 | -34.8 | -58.2 |  |
| 0 | 12 | 30 | 9 | 1 | 8 | **-136.2** | -26.6 | 7 | -78.0 | -58.2 |  |
| 0 | 12 | 50 | 9 | 1 | 8 | **-136.2** | -26.6 | 7 | -78.0 | -58.2 |  |
| 0 | 15 | 20 | 8 | 1 | 7 | **-128.0** | -29.6 | 6 | -63.8 | -64.2 |  |
| 0 | 15 | 30 | 8 | 0 | 8 | **-167.7** | -29.6 | 8 | -103.5 | -64.2 |  |
| 0 | 15 | 50 | 8 | 0 | 8 | **-167.7** | -29.6 | 8 | -103.5 | -64.2 |  |
| 3 | 6 | 20 | 15 | 3 | 12 | **-128.8** | -20.6 | 9 | -41.4 | -87.4 |  |
| 3 | 6 | 30 | 15 | 2 | 13 | **-166.0** | -20.6 | 10 | -78.6 | -87.4 |  |
| 3 | 6 | 50 | 15 | 2 | 13 | **-166.0** | -20.6 | 10 | -78.6 | -87.4 |  |
| 3 | 12 | 20 | 11 | 2 | 9 | **-122.4** | -26.6 | 8 | -50.8 | -71.6 |  |
| 3 | 12 | 30 | 11 | 1 | 10 | **-165.6** | -26.6 | 9 | -94.0 | -71.6 |  |
| 3 | 12 | 50 | 11 | 1 | 10 | **-165.6** | -26.6 | 9 | -94.0 | -71.6 |  |
| 3 | 15 | 20 | 10 | 1 | 9 | **-163.4** | -29.6 | 8 | -82.8 | -80.6 |  |
| 3 | 15 | 30 | 10 | 0 | 10 | **-203.1** | -29.6 | 10 | -122.5 | -80.6 |  |
| 3 | 15 | 50 | 10 | 0 | 10 | **-203.1** | -29.6 | 10 | -122.5 | -80.6 |  |
| 5 | 6 | 20 | 14 | 3 | 11 | **-105.6** | -20.6 | 8 | -27.2 | -78.4 |  |
| 5 | 6 | 30 | 14 | 2 | 12 | **-129.7** | -20.6 | 9 | -51.3 | -78.4 |  |
| 5 | 6 | 50 | 14 | 2 | 12 | **-141.5** | -20.6 | 9 | -63.1 | -78.4 |  |
| 5 | 12 | 20 | 11 | 2 | 8 | **-121.5** | -26.6 | 4 | -50.8 | -70.7 |  |
| 5 | 12 | 30 | 11 | 1 | 9 | **-168.1** | -26.6 | 5 | -97.4 | -70.7 |  |
| 5 | 12 | 50 | 11 | 1 | 9 | **-168.1** | -26.6 | 5 | -97.4 | -70.7 |  |
| 5 | 15 | 20 | 10 | 1 | 8 | **-162.5** | -29.6 | 4 | -82.8 | -79.7 |  |
| 5 | 15 | 30 | 10 | 0 | 9 | **-205.6** | -29.6 | 6 | -125.9 | -79.7 |  |
| 5 | 15 | 50 | 10 | 0 | 9 | **-205.6** | -29.6 | 6 | -125.9 | -79.7 |  |
| 10 | 6 | 20 | 15 | 4 | 11 | **-83.9** | -20.1 | 4 | -5.5 | -78.4 |  |
| 10 | 6 | 30 | 15 | 3 | 12 | **-98.0** | -20.1 | 5 | -19.6 | -78.4 |  |
| 10 | 6 | 50 | 15 | 3 | 12 | **-89.8** | -20.1 | 5 | -11.4 | -78.4 |  |
| 10 | 12 | 20 | 10 | 4 | 5 | **-14.2** | -26.1 | 3 | +56.5 | -70.7 |  |
| 10 | 12 | 30 | 9 | 2 | 6 | **-70.8** | -26.1 | 3 | -0.1 | -70.7 |  |
| 10 | 12 | 50 | 9 | 2 | 6 | **-50.8** | -26.1 | 3 | +19.9 | -70.7 |  |
| 10 | 15 | 20 | 9 | 3 | 5 | **-46.2** | -29.1 | 3 | +33.5 | -79.7 |  |
| 10 | 15 | 30 | 8 | 1 | 6 | **-99.3** | -29.1 | 3 | -19.6 | -79.7 |  |
| 10 | 15 | 50 | 8 | 1 | 6 | **-79.3** | -29.1 | 3 | +0.4 | -79.7 |  |
| 15 | 6 | 20 | 15 | 4 | 11 | **-81.8** | -18.3 | 4 | -5.5 | -76.3 |  |
| 15 | 6 | 30 | 15 | 3 | 12 | **-95.9** | -18.3 | 5 | -19.6 | -76.3 |  |
| 15 | 6 | 50 | 15 | 3 | 12 | **-87.7** | -18.3 | 5 | -11.4 | -76.3 |  |
| 15 | 12 | 20 | 10 | 4 | 5 | **-5.3** | -24.3 | 3 | +56.5 | -61.8 |  |
| 15 | 12 | 30 | 9 | 2 | 6 | **-61.9** | -24.3 | 3 | -0.1 | -61.8 |  |
| 15 | 12 | 50 | 9 | 2 | 6 | **-41.9** | -24.3 | 3 | +19.9 | -61.8 |  |
| 15 | 15 | 20 | 9 | 3 | 5 | **-34.3** | -27.3 | 3 | +33.5 | -67.8 |  |
| 15 | 15 | 30 | 8 | 1 | 6 | **-87.4** | -27.3 | 3 | -19.6 | -67.8 |  |
| 15 | 15 | 50 | 8 | 1 | 6 | **-67.4** | -27.3 | 3 | +0.4 | -67.8 |  |
| 20 | 6 | 20 | 15 | 4 | 11 | **-81.8** | -18.3 | 4 | -5.5 | -76.3 |  |
| 20 | 6 | 30 | 15 | 3 | 12 | **-95.9** | -18.3 | 5 | -19.6 | -76.3 |  |
| 20 | 6 | 50 | 15 | 3 | 12 | **-87.7** | -18.3 | 5 | -11.4 | -76.3 |  |
| 20 | 12 | 20 | 10 | 4 | 5 | **-5.3** | -24.3 | 3 | +56.5 | -61.8 |  |
| 20 | 12 | 30 | 9 | 2 | 6 | **-61.9** | -24.3 | 3 | -0.1 | -61.8 |  |
| 20 | 12 | 50 | 9 | 2 | 6 | **-41.9** | -24.3 | 3 | +19.9 | -61.8 |  |
| 20 | 15 | 20 | 9 | 3 | 5 | **-34.3** | -27.3 | 3 | +33.5 | -67.8 |  |
| 20 | 15 | 30 | 8 | 1 | 6 | **-87.4** | -27.3 | 3 | -19.6 | -67.8 |  |
| 20 | 15 | 50 | 8 | 1 | 6 | **-67.4** | -27.3 | 3 | +0.4 | -67.8 |  |

### round 00

| Allowance | Stop | Take profit | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 6 | 20 | 10 | 6 | 4 | **+85.7** | -14.7 | 2 | +27.0 | +58.7 |  |
| 0 | 6 | 30 | 9 | 4 | 5 | **+45.1** | -17.8 | 3 | -20.8 | +65.9 | **marked: week 2 gives +65.9 of +45.1** |
| 0 | 6 | 50 | 8 | 3 | 4 | **+19.3** | -17.8 | 3 | -0.8 | +20.1 | **marked: one day gives +50.0 of +19.3; week 2 gives +20.1 of +19.3** |
| 0 | 12 | 20 | 9 | 6 | 3 | **+92.5** | -18.3 | 1 | +33.8 | +58.7 |  |
| 0 | 12 | 30 | 8 | 4 | 4 | **+45.9** | -23.8 | 2 | -20.0 | +65.9 | **marked: week 2 gives +65.9 of +45.9** |
| 0 | 12 | 50 | 7 | 3 | 3 | **+20.1** | -23.8 | 2 | -0.0 | +20.1 | **marked: one day gives +50.0 of +20.1; week 2 gives +20.1 of +20.1** |
| 0 | 15 | 20 | 9 | 6 | 3 | **+89.5** | -21.3 | 1 | +30.8 | +58.7 |  |
| 0 | 15 | 30 | 8 | 4 | 4 | **+39.9** | -26.8 | 2 | -26.0 | +65.9 | **marked: week 2 gives +65.9 of +39.9** |
| 0 | 15 | 50 | 7 | 3 | 3 | **+14.1** | -26.8 | 2 | -6.0 | +20.1 | **marked: one day gives +50.0 of +14.1; week 2 gives +20.1 of +14.1** |
| 3 | 6 | 20 | 15 | 7 | 8 | **+60.9** | -18.1 | 2 | +13.7 | +47.2 |  |
| 3 | 6 | 30 | 14 | 5 | 9 | **+29.1** | -19.0 | 4 | -35.3 | +64.4 | **marked: one day gives +30.0 of +29.1; week 2 gives +64.4 of +29.1** |
| 3 | 6 | 50 | 13 | 4 | 8 | **+6.6** | -19.0 | 4 | -15.3 | +21.9 | **marked: one day gives +50.0 of +6.6; week 2 gives +21.9 of +6.6** |
| 3 | 12 | 20 | 14 | 6 | 8 | **-2.1** | -28.6 | 4 | -37.3 | +35.2 |  |
| 3 | 12 | 30 | 13 | 5 | 8 | **+5.1** | -28.6 | 4 | -47.3 | +52.4 | **marked: one day gives +30.0 of +5.1; week 2 gives +52.4 of +5.1** |
| 3 | 12 | 50 | 12 | 4 | 7 | **-17.4** | -28.6 | 4 | -27.3 | +9.9 |  |
| 3 | 15 | 20 | 13 | 6 | 7 | **+18.3** | -27.1 | 3 | -10.9 | +29.2 | **marked: one day gives +40.0 of +18.3; week 2 gives +29.2 of +18.3** |
| 3 | 15 | 30 | 12 | 5 | 7 | **+25.5** | -27.1 | 3 | -20.9 | +46.4 | **marked: one day gives +30.0 of +25.5; week 2 gives +46.4 of +25.5** |
| 3 | 15 | 50 | 11 | 4 | 7 | **-1.9** | -27.1 | 4 | -0.9 | -1.0 |  |
| 5 | 6 | 20 | 15 | 8 | 7 | **+71.8** | -16.5 | 2 | +7.5 | +64.3 |  |
| 5 | 6 | 30 | 15 | 7 | 8 | **+70.0** | -19.0 | 4 | -11.5 | +81.5 | **marked: one day gives +60.0 of +70.0; week 2 gives +81.5 of +70.0** |
| 5 | 6 | 50 | 13 | 5 | 7 | **+17.5** | -19.0 | 4 | -21.5 | +39.0 | **marked: one day gives +50.0 of +17.5; week 2 gives +39.0 of +17.5** |
| 5 | 12 | 20 | 14 | 7 | 7 | **+11.8** | -28.6 | 4 | -40.5 | +52.3 | **marked: one day gives +40.0 of +11.8; week 2 gives +52.3 of +11.8** |
| 5 | 12 | 30 | 14 | 7 | 7 | **+49.0** | -28.6 | 4 | -20.5 | +69.5 | **marked: one day gives +60.0 of +49.0; week 2 gives +69.5 of +49.0** |
| 5 | 12 | 50 | 12 | 5 | 6 | **-3.5** | -28.6 | 4 | -30.5 | +27.0 |  |
| 5 | 15 | 20 | 13 | 6 | 7 | **+17.9** | -25.5 | 3 | -14.1 | +32.0 | **marked: one day gives +40.0 of +17.9; week 2 gives +32.0 of +17.9** |
| 5 | 15 | 30 | 13 | 6 | 7 | **+55.1** | -25.5 | 3 | +5.9 | +49.2 | **marked: one day gives +60.0 of +55.1** |
| 5 | 15 | 50 | 11 | 4 | 7 | **-2.3** | -25.5 | 4 | -4.1 | +1.8 |  |
| 10 | 6 | 20 | 16 | 7 | 9 | **+42.6** | -16.5 | 3 | +7.5 | +35.1 | **marked: one day gives +40.0 of +42.6** |
| 10 | 6 | 30 | 16 | 6 | 10 | **+40.8** | -19.0 | 4 | -11.5 | +52.3 | **marked: one day gives +60.0 of +40.8; week 2 gives +52.3 of +40.8** |
| 10 | 6 | 50 | 14 | 4 | 9 | **-11.7** | -19.0 | 4 | -21.5 | +9.8 |  |
| 10 | 12 | 20 | 15 | 6 | 9 | **-23.4** | -28.6 | 4 | -40.5 | +17.1 |  |
| 10 | 12 | 30 | 15 | 6 | 9 | **+13.8** | -28.6 | 4 | -20.5 | +34.3 | **marked: one day gives +60.0 of +13.8; week 2 gives +34.3 of +13.8** |
| 10 | 12 | 50 | 13 | 4 | 8 | **-38.7** | -28.6 | 4 | -30.5 | -8.2 |  |
| 10 | 15 | 20 | 12 | 6 | 6 | **+29.0** | -25.5 | 3 | -14.1 | +43.1 | **marked: one day gives +40.0 of +29.0; week 2 gives +43.1 of +29.0** |
| 10 | 15 | 30 | 12 | 6 | 6 | **+66.2** | -25.5 | 3 | +5.9 | +60.3 | **marked: one day gives +60.0 of +66.2; week 2 gives +60.3 of +66.2** |
| 10 | 15 | 50 | 10 | 4 | 6 | **+8.8** | -25.5 | 4 | -4.1 | +12.9 | **marked: one day gives +50.0 of +8.8; week 2 gives +12.9 of +8.8** |
| 15 | 6 | 20 | 17 | 7 | 10 | **+28.0** | -16.5 | 3 | -7.1 | +35.1 | **marked: one day gives +40.0 of +28.0; week 2 gives +35.1 of +28.0** |
| 15 | 6 | 30 | 17 | 6 | 11 | **+26.2** | -19.0 | 4 | -26.1 | +52.3 | **marked: one day gives +60.0 of +26.2; week 2 gives +52.3 of +26.2** |
| 15 | 6 | 50 | 15 | 4 | 10 | **-26.3** | -19.0 | 4 | -36.1 | +9.8 |  |
| 15 | 12 | 20 | 16 | 6 | 10 | **-38.0** | -28.6 | 4 | -55.1 | +17.1 |  |
| 15 | 12 | 30 | 16 | 6 | 10 | **-0.8** | -28.6 | 4 | -35.1 | +34.3 |  |
| 15 | 12 | 50 | 14 | 4 | 9 | **-53.3** | -28.6 | 4 | -45.1 | -8.2 |  |
| 15 | 15 | 20 | 13 | 6 | 7 | **+14.4** | -25.5 | 3 | -28.7 | +43.1 | **marked: one day gives +40.0 of +14.4; week 2 gives +43.1 of +14.4** |
| 15 | 15 | 30 | 13 | 6 | 7 | **+51.6** | -25.5 | 3 | -8.7 | +60.3 | **marked: one day gives +60.0 of +51.6; week 2 gives +60.3 of +51.6** |
| 15 | 15 | 50 | 11 | 4 | 7 | **-5.8** | -25.5 | 4 | -18.7 | +12.9 |  |
| 20 | 6 | 20 | 17 | 7 | 10 | **+28.0** | -16.5 | 3 | -7.1 | +35.1 | **marked: one day gives +40.0 of +28.0; week 2 gives +35.1 of +28.0** |
| 20 | 6 | 30 | 17 | 6 | 11 | **+26.2** | -19.0 | 4 | -26.1 | +52.3 | **marked: one day gives +60.0 of +26.2; week 2 gives +52.3 of +26.2** |
| 20 | 6 | 50 | 15 | 4 | 10 | **-26.3** | -19.0 | 4 | -36.1 | +9.8 |  |
| 20 | 12 | 20 | 16 | 6 | 10 | **-38.0** | -28.6 | 4 | -55.1 | +17.1 |  |
| 20 | 12 | 30 | 16 | 6 | 10 | **-0.8** | -28.6 | 4 | -35.1 | +34.3 |  |
| 20 | 12 | 50 | 14 | 4 | 9 | **-53.3** | -28.6 | 4 | -45.1 | -8.2 |  |
| 20 | 15 | 20 | 13 | 6 | 7 | **+14.4** | -25.5 | 3 | -28.7 | +43.1 | **marked: one day gives +40.0 of +14.4; week 2 gives +43.1 of +14.4** |
| 20 | 15 | 30 | 13 | 6 | 7 | **+51.6** | -25.5 | 3 | -8.7 | +60.3 | **marked: one day gives +60.0 of +51.6; week 2 gives +60.3 of +51.6** |
| 20 | 15 | 50 | 11 | 4 | 7 | **-5.8** | -25.5 | 4 | -18.7 | +12.9 |  |

