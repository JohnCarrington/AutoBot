# Three possible new strategies, 26 October to 6 November 2026

Read-only research on the stored GBPUSD 5-minute candles (Monday 26 October to Friday 6 November), on IG's prices. Nothing in the bot was changed. Written 8 November 2026.

## Method (shared)

- **IG's prices:** a buy opens on the buy price (the entry plus the spread at that candle's open) and is stopped and closed on the sell price; a sell opens on the sell price and is stopped and closed on the buy price. Levels, EMAs and setups use the sell price, as the bot does.
- **Inside one 5-minute candle:** a scheduled close (20:30 UK, or 15 minutes before big news where it applies) at its open; then the stop (filled at the candle's open if it opened past it); then the take profit. **Stop counted first.**
- **Entry-candle stop correction:** in the entry candle the stop counts only if the candle opened past the entry or closed beyond the stop.
- **Never opened** in the first 15 minutes after the Sunday open or from 21:55 to 22:15 UK. Choices this research had to make (the request does not set them), the bot's normal rules for a strategy: **new trades 06:00 to 20:30 UK, closed at 20:30 UK every day, one trade at a time per strategy and test, no close on a rejection at a level.** (So the Sunday-open and rollover rules never came into play: both fall outside 06:00-20:30.)
- **Stops** 6, 12 and 15 pips, **take profits** 20, 30, 50 and 100 pips: 12 combinations for each test. Weeks by entry time.
- **Marked** when the total is positive and one day gives at least 80% of it, or one week at least 90% (as in the earlier research).
- **The news calendar starts on Saturday 31 October** (the stored Finnhub copy, `data/news`): there is no calendar for week 1. Big news for GBPUSD in week 2 (the bot's own news table and expected-direction rules, design 2.4): Thursday 5 November 12:00 (BoE rate decision, expected **up**) and Friday 6 November 13:30 (payrolls, expected **down**). Whether week 1 had big news is unknown, so strategy 1 has no week-1 trades, and strategy 2's news rule could only be applied in week 2.

**Limits:** two weeks only, and for strategy 1 two days only; 5-minute candles, not ticks; no slippage beyond candle-open gaps; GBPUSD only.

## 1. News-day trend trade

Only on a UK day with big news for the pair, only in that day's expected news direction (the first release time of the day with an expected direction; each of the two days has one). One trade a day for each test: the first entry that qualifies. Held through the release (not closed before news), closed at 20:30 UK.

- **(a) the first EMA pullback before the release:** the first EMA pullback setup (the bot's own EMA pullback code, design 3.2, including the hourly trend step) in the expected direction from 06:00 UK until the release. The analyser's state and the direction rule were **not** required (the news direction is this strategy's filter); both entries happened to be allowed by them anyway.
- **(b) the first pullback to the 5-minute 8 or 21 EMA after the release:** from the candle after the release candle, the first candle that reaches the EMA (its value at the last finished candle) while the candle before closed on the trend's side of it (below it for a sell). Entry at the EMA, or at the candle's open if it opened past it. Tested with the 8 EMA and with the 21 EMA.

- Thu 05 Nov: release 12:00 UK, expected up; 1 EMA pullback setup(s) in that direction between 06:00 and the release; the first at 07:00.
- Fri 06 Nov: release 13:30 UK, expected down; 6 EMA pullback setup(s) in that direction between 06:00 and the release; the first at 06:45.

### 1(a) first EMA pullback before the release

| Stop | Take profit | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|---|
| 6 | 20 | 2 | 1 | 1 | **+14.0** | -6.0 | 1 | +0.0 | +14.0 | **marked: one day gives +20.0 of +14.0; week 2 gives +14.0 of +14.0** |
| 6 | 30 | 2 | 1 | 1 | **+24.0** | -6.0 | 1 | +0.0 | +24.0 | **marked: one day gives +30.0 of +24.0; week 2 gives +24.0 of +24.0** |
| 6 | 50 | 2 | 1 | 1 | **+44.0** | -6.0 | 1 | +0.0 | +44.0 | **marked: one day gives +50.0 of +44.0; week 2 gives +44.0 of +44.0** |
| 6 | 100 | 2 | 1 | 1 | **+60.3** | -6.0 | 1 | +0.0 | +60.3 | **marked: one day gives +66.3 of +60.3; week 2 gives +60.3 of +60.3** |
| 12 | 20 | 2 | 1 | 1 | **+8.0** | -12.0 | 1 | +0.0 | +8.0 | **marked: one day gives +20.0 of +8.0; week 2 gives +8.0 of +8.0** |
| 12 | 30 | 2 | 1 | 1 | **+18.0** | -12.0 | 1 | +0.0 | +18.0 | **marked: one day gives +30.0 of +18.0; week 2 gives +18.0 of +18.0** |
| 12 | 50 | 2 | 1 | 1 | **+38.0** | -12.0 | 1 | +0.0 | +38.0 | **marked: one day gives +50.0 of +38.0; week 2 gives +38.0 of +38.0** |
| 12 | 100 | 2 | 1 | 1 | **+54.3** | -12.0 | 1 | +0.0 | +54.3 | **marked: one day gives +66.3 of +54.3; week 2 gives +54.3 of +54.3** |
| 15 | 20 | 2 | 1 | 1 | **+5.0** | -15.0 | 1 | +0.0 | +5.0 | **marked: one day gives +20.0 of +5.0; week 2 gives +5.0 of +5.0** |
| 15 | 30 | 2 | 1 | 1 | **+15.0** | -15.0 | 1 | +0.0 | +15.0 | **marked: one day gives +30.0 of +15.0; week 2 gives +15.0 of +15.0** |
| 15 | 50 | 2 | 1 | 1 | **+35.0** | -15.0 | 1 | +0.0 | +35.0 | **marked: one day gives +50.0 of +35.0; week 2 gives +35.0 of +35.0** |
| 15 | 100 | 2 | 1 | 1 | **+51.3** | -15.0 | 1 | +0.0 | +51.3 | **marked: one day gives +66.3 of +51.3; week 2 gives +51.3 of +51.3** |

Each trade's pips for every stop / take profit:

| Entry | Dir | Entry price | 6/20 | 6/30 | 6/50 | 6/100 | 12/20 | 12/30 | 12/50 | 12/100 | 15/20 | 15/30 | 15/50 | 15/100 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Thu 05 Nov 07:00 | BUY | 13497.7 | -6.0 | -6.0 | -6.0 | -6.0 | -12.0 | -12.0 | -12.0 | -12.0 | -15.0 | -15.0 | -15.0 | -15.0 |
| Fri 06 Nov 06:45 | SELL | 13417.7 | +20.0 | +30.0 | +50.0 | +66.3 | +20.0 | +30.0 | +50.0 | +66.3 | +20.0 | +30.0 | +50.0 | +66.3 |

Exits with stop 15 / take profit 100: Thu 07:00 stop 07:20 (-15.0); Fri 06:45 closed by the clock 20:30 (+66.3).

### 1(b) first pullback to the 5-minute 8 EMA after the release

| Stop | Take profit | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|---|
| 6 | 20 | 2 | 0 | 2 | **-12.0** | -6.0 | 2 | +0.0 | -12.0 |  |
| 6 | 30 | 2 | 0 | 2 | **-12.0** | -6.0 | 2 | +0.0 | -12.0 |  |
| 6 | 50 | 2 | 0 | 2 | **-12.0** | -6.0 | 2 | +0.0 | -12.0 |  |
| 6 | 100 | 2 | 0 | 2 | **-12.0** | -6.0 | 2 | +0.0 | -12.0 |  |
| 12 | 20 | 2 | 0 | 2 | **-24.0** | -12.0 | 2 | +0.0 | -24.0 |  |
| 12 | 30 | 2 | 0 | 2 | **-24.0** | -12.0 | 2 | +0.0 | -24.0 |  |
| 12 | 50 | 2 | 0 | 2 | **-24.0** | -12.0 | 2 | +0.0 | -24.0 |  |
| 12 | 100 | 2 | 0 | 2 | **-24.0** | -12.0 | 2 | +0.0 | -24.0 |  |
| 15 | 20 | 2 | 0 | 2 | **-30.0** | -15.0 | 2 | +0.0 | -30.0 |  |
| 15 | 30 | 2 | 0 | 2 | **-30.0** | -15.0 | 2 | +0.0 | -30.0 |  |
| 15 | 50 | 2 | 0 | 2 | **-30.0** | -15.0 | 2 | +0.0 | -30.0 |  |
| 15 | 100 | 2 | 0 | 2 | **-30.0** | -15.0 | 2 | +0.0 | -30.0 |  |

Each trade's pips for every stop / take profit:

| Entry | Dir | Entry price | 6/20 | 6/30 | 6/50 | 6/100 | 12/20 | 12/30 | 12/50 | 12/100 | 15/20 | 15/30 | 15/50 | 15/100 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Thu 05 Nov 12:30 | BUY | 13469.7 | -6.0 | -6.0 | -6.0 | -6.0 | -12.0 | -12.0 | -12.0 | -12.0 | -15.0 | -15.0 | -15.0 | -15.0 |
| Fri 06 Nov 14:30 | SELL | 13353.6 | -6.0 | -6.0 | -6.0 | -6.0 | -12.0 | -12.0 | -12.0 | -12.0 | -15.0 | -15.0 | -15.0 | -15.0 |

Exits with stop 15 / take profit 100: Thu 12:30 stop 13:15 (-15.0); Fri 14:30 stop 14:50 (-15.0).

### 1(b) first pullback to the 5-minute 21 EMA after the release

| Stop | Take profit | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|---|
| 6 | 20 | 2 | 0 | 2 | **-12.2** | -6.2 | 2 | +0.0 | -12.2 |  |
| 6 | 30 | 2 | 0 | 2 | **-12.2** | -6.2 | 2 | +0.0 | -12.2 |  |
| 6 | 50 | 2 | 0 | 2 | **-12.2** | -6.2 | 2 | +0.0 | -12.2 |  |
| 6 | 100 | 2 | 0 | 2 | **-12.2** | -6.2 | 2 | +0.0 | -12.2 |  |
| 12 | 20 | 2 | 0 | 2 | **-24.0** | -12.0 | 2 | +0.0 | -24.0 |  |
| 12 | 30 | 2 | 0 | 2 | **-24.0** | -12.0 | 2 | +0.0 | -24.0 |  |
| 12 | 50 | 2 | 0 | 2 | **-24.0** | -12.0 | 2 | +0.0 | -24.0 |  |
| 12 | 100 | 2 | 0 | 2 | **-24.0** | -12.0 | 2 | +0.0 | -24.0 |  |
| 15 | 20 | 2 | 1 | 1 | **-1.0** | -15.0 | 1 | +0.0 | -1.0 |  |
| 15 | 30 | 2 | 1 | 1 | **-1.0** | -15.0 | 1 | +0.0 | -1.0 |  |
| 15 | 50 | 2 | 1 | 1 | **-1.0** | -15.0 | 1 | +0.0 | -1.0 |  |
| 15 | 100 | 2 | 1 | 1 | **-1.0** | -15.0 | 1 | +0.0 | -1.0 |  |

Each trade's pips for every stop / take profit:

| Entry | Dir | Entry price | 6/20 | 6/30 | 6/50 | 6/100 | 12/20 | 12/30 | 12/50 | 12/100 | 15/20 | 15/30 | 15/50 | 15/100 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Thu 05 Nov 12:30 | BUY | 13464.9 | -6.2 | -6.2 | -6.2 | -6.2 | -12.0 | -12.0 | -12.0 | -12.0 | -15.0 | -15.0 | -15.0 | -15.0 |
| Fri 06 Nov 14:50 | SELL | 13365.4 | -6.0 | -6.0 | -6.0 | -6.0 | -12.0 | -12.0 | -12.0 | -12.0 | +14.0 | +14.0 | +14.0 | +14.0 |

Exits with stop 15 / take profit 100: Thu 12:30 stop 19:25 (-15.0); Fri 14:50 closed by the clock 20:30 (+14.0).

**Reading it:** two trades per test cannot show an edge. (a) lost on Thursday (bought at 07:00, stopped before the BoE release) and won on Friday (sold at 06:45, the day fell). (b) lost both days at every stop except the 21 EMA with a 15-pip stop on Friday: the first pullback after the release went further than 6 or 12 pips. The (a) results are all positive but rest on one Friday trade, and every one is marked. Week 1 shows 0.0 because there is no news calendar for week 1, not because nothing happened.

## 2. Level reversal

A rejection at the **pivot, S2, R2 or a round number ending in 00** (not 50): the shared rejection part as the strategies use it (design 3.3 rules: price reaches the level or comes within 3 pips of it, the reversal candle, the confirmation candle closing past the reversal candle), **entry when price breaks past the confirmation candle** (at that point, or the candle's open if it opened past it). A setup counts if any of the levels it reached is one of these; a setup started by the Bollinger band alone does not. In any analyser state except consolidation (the state after the last finished candle, as for every strategy); in the direction of the rejection (rejected from above: sell). Normal rules for a new strategy: no new trade in a big-news window, closed 15 minutes before big news (week 2 only, see Method), new trades 06:00-20:30 UK, closed 20:30, one at a time. Several setups triggering on the same candle and direction count once.

Of 1539 rejection triggers in the two weeks: 1184 were not at one of these levels, 42 came in consolidation, 117 outside 06:00-20:30 UK, 0 in a big-news window; 116 entries remained (before one at a time).

| Stop | Take profit | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|---|
| 6 | 20 | 58 | 11 | 47 | **-121.9** | -6.0 | 14 | -70.4 | -51.5 |  |
| 6 | 30 | 55 | 9 | 46 | **-99.3** | -6.0 | 15 | -76.4 | -22.9 |  |
| 6 | 50 | 48 | 7 | 41 | **-117.0** | -6.0 | 13 | -57.6 | -59.4 |  |
| 6 | 100 | 47 | 7 | 40 | **-100.9** | -6.0 | 13 | -41.5 | -59.4 |  |
| 12 | 20 | 46 | 10 | 36 | **-237.1** | -12.0 | 9 | -125.1 | -112.0 |  |
| 12 | 30 | 43 | 8 | 35 | **-198.5** | -12.0 | 10 | -137.1 | -61.4 |  |
| 12 | 50 | 38 | 5 | 32 | **-259.1** | -12.0 | 8 | -112.3 | -146.8 |  |
| 12 | 100 | 37 | 5 | 31 | **-237.0** | -12.0 | 8 | -90.2 | -146.8 |  |
| 15 | 20 | 35 | 9 | 26 | **-184.6** | -15.0 | 9 | -115.6 | -69.0 |  |
| 15 | 30 | 33 | 7 | 26 | **-150.9** | -15.0 | 9 | -130.6 | -20.3 |  |
| 15 | 50 | 28 | 4 | 23 | **-195.5** | -15.0 | 8 | -107.4 | -88.1 |  |
| 15 | 100 | 27 | 4 | 22 | **-170.4** | -15.0 | 8 | -82.3 | -88.1 |  |

**Every combination loses.** The least bad is stop 6 / take profit 30 (-99.3 pips, 9 won of 55). By level, with that combination:

| Level | Trades | Won | Total pips |
|---|---|---|---|
| R2 | 7 | 3 | +41.8 |
| S2 | 5 | 1 | -12.3 |
| pivot | 23 | 2 | -60.3 |
| round 00 | 24 | 4 | -76.2 |

(A trade at two of these levels at once is counted under each.)

By state at entry: emerging trend down: 16, emerging trend up: 19, trend down: 11, trend up: 9.

Its trades (stop 6 / take profit 30):

| Entry | Dir | Entry price | Level; state at entry | Closed | How | Pips |
|---|---|---|---|---|---|---|
| Mon 26 Oct 06:00 | BUY | 13374.0 | pivot 13368.0; trend down, slow grind | Mon 26 Oct 06:10 | stop | -6.0 |
| Mon 26 Oct 07:25 | SELL | 13360.5 | pivot 13368.0; emerging trend down | Mon 26 Oct 13:55 | take profit | +30.0 |
| Mon 26 Oct 13:55 | SELL | 13336.3 | S2 13338.6; emerging trend down | Mon 26 Oct 14:15 | stop | -6.0 |
| Mon 26 Oct 14:45 | BUY | 13345.1 | S2 13338.6; trend down, slow grind | Mon 26 Oct 20:30 | closed by the clock | -4.6 |
| Wed 28 Oct 13:55 | SELL | 13294.3 | round 00 13300.0; trend up, slow grind | Wed 28 Oct 14:50 | stop | -6.0 |
| Wed 28 Oct 15:10 | BUY | 13304.2 | round 00 13300.0; emerging trend up | Wed 28 Oct 15:20 | stop | -6.0 |
| Wed 28 Oct 15:20 | SELL | 13300.5 | round 00 13300.0; trend up, slow grind | Wed 28 Oct 16:05 | stop | -6.0 |
| Wed 28 Oct 16:10 | BUY | 13305.8 | round 00 13300.0; trend up, slow grind | Wed 28 Oct 17:50 | stop | -6.0 |
| Wed 28 Oct 18:45 | BUY | 13337.4 | round 00 13300.0; emerging trend up | Wed 28 Oct 18:45 | stop | -6.0 |
| Wed 28 Oct 19:00 | SELL | 13316.2 | pivot 13316.2; emerging trend down | Wed 28 Oct 19:00 | stop | -6.0 |
| Wed 28 Oct 20:00 | BUY | 13329.9 | pivot 13316.2; emerging trend down | Wed 28 Oct 20:25 | stop | -6.0 |
| Thu 29 Oct 06:30 | BUY | 13312.0 | pivot 13312.0; trend down, slow grind | Thu 29 Oct 06:55 | stop | -6.0 |
| Thu 29 Oct 06:55 | SELL | 13308.2 | pivot 13312.0; trend down, slow grind | Thu 29 Oct 07:05 | stop | -6.0 |
| Thu 29 Oct 07:50 | BUY | 13326.3 | pivot 13312.0; emerging trend up | Thu 29 Oct 08:05 | stop | -6.0 |
| Thu 29 Oct 08:50 | SELL | 13304.7 | pivot 13312.0; emerging trend down | Thu 29 Oct 08:55 | stop | -6.0 |
| Thu 29 Oct 09:15 | SELL | 13304.8 | pivot 13312.0; emerging trend down | Thu 29 Oct 09:45 | stop | -6.0 |
| Thu 29 Oct 09:45 | BUY | 13309.5 | round 00 13300.0; trend down, slow grind | Thu 29 Oct 13:15 | stop | -6.0 |
| Thu 29 Oct 13:30 | BUY | 13320.4 | pivot 13312.0; trend down, slow grind | Thu 29 Oct 14:45 | take profit | +30.0 |
| Thu 29 Oct 16:30 | SELL | 13367.4 | R2 13377.1; emerging trend down | Thu 29 Oct 17:00 | stop | -6.0 |
| Fri 30 Oct 06:40 | SELL | 13391.2 | round 00 13400.0; emerging trend down | Fri 30 Oct 07:05 | stop | -6.0 |
| Fri 30 Oct 07:25 | BUY | 13410.6 | round 00 13400.0; emerging trend up | Fri 30 Oct 07:25 | stop | -6.0 |
| Fri 30 Oct 07:30 | BUY | 13411.0 | round 00 13400.0; emerging trend up | Fri 30 Oct 07:30 | stop | -6.0 |
| Fri 30 Oct 08:15 | BUY | 13413.8 | round 00 13400.0; trend up, slow grind | Fri 30 Oct 08:15 | stop | -6.0 |
| Fri 30 Oct 13:25 | SELL | 13393.1 | round 00 13400.0; trend down, slow grind | Fri 30 Oct 16:00 | stop | -6.0 |
| Fri 30 Oct 16:15 | BUY | 13404.9 | round 00 13400.0; emerging trend up | Fri 30 Oct 16:20 | stop | -6.0 |
| Fri 30 Oct 16:25 | SELL | 13397.4 | round 00 13400.0; trend up, slow grind | Fri 30 Oct 20:30 | closed by the clock | +0.2 |
| Mon 02 Nov 06:00 | SELL | 13397.7 | R2 13399.1, round 00 13400.0; emerging trend down | Mon 02 Nov 06:50 | stop | -6.0 |
| Mon 02 Nov 06:55 | BUY | 13404.0 | R2 13399.1; emerging trend up | Mon 02 Nov 08:45 | take profit | +30.0 |
| Mon 02 Nov 11:05 | BUY | 13410.8 | round 00 13400.0; emerging trend up | Mon 02 Nov 18:25 | stop | -6.0 |
| Mon 02 Nov 18:55 | BUY | 13405.7 | round 00 13400.0; trend down, slow grind | Mon 02 Nov 20:30 | closed by the clock | +3.3 |
| Tue 03 Nov 06:20 | BUY | 13415.5 | pivot 13411.6; trend up, slow grind | Tue 03 Nov 06:40 | stop | -6.0 |
| Tue 03 Nov 06:45 | SELL | 13408.8 | pivot 13411.6; trend up, slow grind | Tue 03 Nov 07:00 | stop | -6.0 |
| Tue 03 Nov 07:00 | BUY | 13412.3 | pivot 13411.6; emerging trend up | Tue 03 Nov 10:05 | stop | -6.0 |
| Tue 03 Nov 11:10 | SELL | 13408.6 | pivot 13411.6; emerging trend down | Tue 03 Nov 12:05 | stop | -6.0 |
| Tue 03 Nov 13:25 | BUY | 13419.3 | pivot 13411.6; emerging trend down | Tue 03 Nov 13:50 | stop | -6.0 |
| Tue 03 Nov 14:50 | BUY | 13430.0 | pivot 13411.6; emerging trend up | Tue 03 Nov 14:55 | stop | -6.0 |
| Tue 03 Nov 15:55 | BUY | 13415.4 | pivot 13411.6; emerging trend up | Tue 03 Nov 16:40 | stop | -6.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | pivot 13411.6; emerging trend up | Tue 03 Nov 20:00 | stop | -6.0 |
| Tue 03 Nov 20:25 | BUY | 13415.8 | pivot 13411.6; emerging trend up | Tue 03 Nov 20:30 | closed by the clock | -0.3 |
| Wed 04 Nov 06:15 | SELL | 13453.0 | R2 13458.8; emerging trend down | Wed 04 Nov 06:20 | stop | -6.0 |
| Wed 04 Nov 07:20 | BUY | 13465.7 | R2 13458.8; emerging trend up | Wed 04 Nov 10:15 | take profit | +30.0 |
| Wed 04 Nov 12:40 | SELL | 13487.4 | round 00 13500.0; emerging trend down | Wed 04 Nov 12:45 | stop | -6.0 |
| Wed 04 Nov 13:25 | SELL | 13493.9 | round 00 13500.0; trend up, slow grind | Wed 04 Nov 13:30 | stop | -6.0 |
| Wed 04 Nov 14:00 | SELL | 13483.5 | round 00 13500.0; trend up, slow grind | Wed 04 Nov 14:00 | stop | -6.0 |
| Wed 04 Nov 17:10 | BUY | 13468.3 | R2 13458.8; trend down, slow grind | Wed 04 Nov 18:30 | stop | -6.0 |
| Wed 04 Nov 19:55 | BUY | 13465.7 | R2 13458.8; emerging trend up | Wed 04 Nov 20:30 | closed by the clock | +5.8 |
| Thu 05 Nov 07:15 | SELL | 13488.7 | round 00 13500.0; emerging trend down | Thu 05 Nov 10:45 | take profit | +30.0 |
| Thu 05 Nov 13:10 | SELL | 13458.0 | pivot 13468.0; emerging trend down | Thu 05 Nov 13:25 | stop | -6.0 |
| Thu 05 Nov 14:50 | BUY | 13467.6 | pivot 13468.0; emerging trend up | Thu 05 Nov 14:55 | stop | -6.0 |
| Thu 05 Nov 15:20 | BUY | 13469.8 | pivot 13468.0; emerging trend down | Thu 05 Nov 16:05 | stop | -6.0 |
| Thu 05 Nov 16:20 | BUY | 13468.8 | pivot 13468.0; emerging trend up | Thu 05 Nov 18:40 | stop | -6.0 |
| Fri 06 Nov 07:50 | BUY | 13402.1 | round 00 13400.0; trend down, slow grind | Fri 06 Nov 08:30 | stop | -6.0 |
| Fri 06 Nov 08:55 | SELL | 13393.1 | S2 13399.1, round 00 13400.0; trend down, slow grind | Fri 06 Nov 11:15 | stop | -6.0 |
| Fri 06 Nov 12:20 | BUY | 13402.2 | S2 13399.1, round 00 13400.0; emerging trend up | Fri 06 Nov 12:25 | stop | -6.0 |
| Fri 06 Nov 12:40 | SELL | 13397.6 | S2 13399.1, round 00 13400.0; emerging trend up | Fri 06 Nov 13:15 | closed by the clock | +10.3 |

## 3. Trend-day recognition

Each weekday (10 days). **A trend day** as asked: price moved 80 pips or more between 07:00 and 17:00 UK. "Moved" is read two ways: the **net move** (the 07:00 candle's open to the 16:55 candle's close) and the **range** (highest high to lowest low, 07:00-17:00). Sell prices; all days are GMT, so UK time is UTC.

Measures, each worked out at 09:00 and at 10:00 UK from the candles finished by then:

- **Move since the day's open:** from the 00:00 UK candle's open; picks the day when it is at least 20, 30 or 40 pips either way.
- **Hourly EMA slopes:** (i) the EMA pullback's hourly trend (design 3.2 step 0: hourly 8, 13, 20 EMAs in order, all moving one way, slopes and gaps above the bot's minimums); (ii) the hourly 8 EMA's slope over the last 3 finished hourly candles, at least 2, 3 or 4 pips an hour.
- **London broke the Asian range:** the Asian range is 00:00-07:00 UK; picks the day when London (from 07:00) has gone beyond one side of it and not the other.

| Day | Net move 07-17 | Range 07-17 | Move since open 09:00 / 10:00 | Hourly trend 09:00 / 10:00 | 8 EMA slope (pips/h) 09:00 / 10:00 | Asian range broken 09:00 / 10:00 |
|---|---|---|---|---|---|---|
| Mon 26 Oct | -26.0 | 48.0 | -30.9 / -32.2 | down / down | -3.56 / -4.84 | down / down |
| Tue 27 Oct | -11.9 | 29.9 | -20.8 / -28.4 | down / down | -2.63 / -2.85 | down / down |
| Wed 28 Oct | +36.3 | 48.6 | -14.0 / -19.1 | down / down | -2.10 / -1.16 | down / down |
| Thu 29 Oct | +58.4 | 83.4 | -14.6 / -15.4 | none / none | -0.61 / -0.33 | none / down |
| Fri 30 Oct | +4.7 | 59.8 | +36.6 / +50.0 | up / up | +3.47 / +5.21 | up / up |
| Mon 02 Nov | +13.7 | 47.9 | +55.0 / +35.7 | up / up | +5.54 / +5.64 | up / up |
| Tue 03 Nov | +5.1 | 30.8 | +10.1 / +10.2 | up / up | +1.66 / +1.71 | up / up |
| Wed 04 Nov | -4.4 | 49.8 | +47.3 / +55.9 | up / up | +4.26 / +5.49 | up / up |
| Thu 05 Nov | -14.7 | 55.2 | +4.1 / -12.3 | none / none | -0.73 / -3.01 | both / both |
| Fri 06 Nov | -44.3 | 74.7 | -61.6 / -69.4 | down / down | -6.92 / -7.52 | down / down |

**Days that moved 80 pips or more:** by net move, **none**; by range, **1** (Thu 29 Oct). So in these two weeks there is (almost) nothing for a measure to pick: a measure can only be judged on how often it picks a day that was not a trend day (a false alarm).

### Against: net move of 80 pips or more (no such day)

| Measure | Days picked | Right (trend days picked) | Trend days missed | False alarms | Direction right on the days picked |
|---|---|---|---|---|---|
| move since open >= 20 at 09:00 | 6 | 0 of 0 | 0 | 6 | 5 of 6 |
| move since open >= 30 at 09:00 | 5 | 0 of 0 | 0 | 5 | 4 of 5 |
| move since open >= 40 at 09:00 | 3 | 0 of 0 | 0 | 3 | 2 of 3 |
| hourly trend (step 0) at 09:00 | 8 | 0 of 0 | 0 | 8 | 6 of 8 |
| hourly 8 EMA slope >= 2 pips/h at 09:00 | 7 | 0 of 0 | 0 | 7 | 5 of 7 |
| hourly 8 EMA slope >= 3 pips/h at 09:00 | 5 | 0 of 0 | 0 | 5 | 4 of 5 |
| hourly 8 EMA slope >= 4 pips/h at 09:00 | 3 | 0 of 0 | 0 | 3 | 2 of 3 |
| London broke one side of the Asian range by 09:00 | 8 | 0 of 0 | 0 | 8 | 6 of 8 |
| move since open >= 20 at 10:00 | 6 | 0 of 0 | 0 | 6 | 5 of 6 |
| move since open >= 30 at 10:00 | 5 | 0 of 0 | 0 | 5 | 4 of 5 |
| move since open >= 40 at 10:00 | 3 | 0 of 0 | 0 | 3 | 2 of 3 |
| hourly trend (step 0) at 10:00 | 8 | 0 of 0 | 0 | 8 | 6 of 8 |
| hourly 8 EMA slope >= 2 pips/h at 10:00 | 7 | 0 of 0 | 0 | 7 | 6 of 7 |
| hourly 8 EMA slope >= 3 pips/h at 10:00 | 6 | 0 of 0 | 0 | 6 | 5 of 6 |
| hourly 8 EMA slope >= 4 pips/h at 10:00 | 5 | 0 of 0 | 0 | 5 | 4 of 5 |
| London broke one side of the Asian range by 10:00 | 9 | 0 of 0 | 0 | 9 | 6 of 9 |

### Against: range of 80 pips or more (Thu 29 Oct only)

| Measure | Days picked | Right (trend days picked) | Trend days missed | False alarms | Direction right on the days picked |
|---|---|---|---|---|---|
| move since open >= 20 at 09:00 | 6 | 0 of 1 | 1 | 6 | 5 of 6 |
| move since open >= 30 at 09:00 | 5 | 0 of 1 | 1 | 5 | 4 of 5 |
| move since open >= 40 at 09:00 | 3 | 0 of 1 | 1 | 3 | 2 of 3 |
| hourly trend (step 0) at 09:00 | 8 | 0 of 1 | 1 | 8 | 6 of 8 |
| hourly 8 EMA slope >= 2 pips/h at 09:00 | 7 | 0 of 1 | 1 | 7 | 5 of 7 |
| hourly 8 EMA slope >= 3 pips/h at 09:00 | 5 | 0 of 1 | 1 | 5 | 4 of 5 |
| hourly 8 EMA slope >= 4 pips/h at 09:00 | 3 | 0 of 1 | 1 | 3 | 2 of 3 |
| London broke one side of the Asian range by 09:00 | 8 | 0 of 1 | 1 | 8 | 6 of 8 |
| move since open >= 20 at 10:00 | 6 | 0 of 1 | 1 | 6 | 5 of 6 |
| move since open >= 30 at 10:00 | 5 | 0 of 1 | 1 | 5 | 4 of 5 |
| move since open >= 40 at 10:00 | 3 | 0 of 1 | 1 | 3 | 2 of 3 |
| hourly trend (step 0) at 10:00 | 8 | 0 of 1 | 1 | 8 | 6 of 8 |
| hourly 8 EMA slope >= 2 pips/h at 10:00 | 7 | 0 of 1 | 1 | 7 | 6 of 7 |
| hourly 8 EMA slope >= 3 pips/h at 10:00 | 6 | 0 of 1 | 1 | 6 | 5 of 6 |
| hourly 8 EMA slope >= 4 pips/h at 10:00 | 5 | 0 of 1 | 1 | 5 | 4 of 5 |
| London broke one side of the Asian range by 10:00 | 9 | 1 of 1 | 0 | 8 | 6 of 9 |

"Direction right" compares the measure's direction with the day's net move from 07:00 to 17:00.

**Reading it:** with no 80-pip day by net move and one by range, none of these measures can be shown to recognise trend days in this period. Thursday 29 October (the only 80-pip range) was picked only by the Asian-range break at 10:00, and that break was down while the day then went up 58 pips net. Every measure picked 3 to 9 of the 10 days: by the net-move test all are false alarms, by the range test all but that one. Their direction usually matched the day's net move, but those moves were small: the days picked moved between 4 and 58 pips net from 07:00 to 17:00. More weeks are needed to judge this.

## Summary

- **1. News-day trend trade:** two big-news days, two trades per test. (a) the first EMA pullback before the release made +14.0 to +60.3 pips (one loss, one win); (b) the first pullback after the release lost at nearly every stop. Far too few trades to decide anything.
- **2. Level reversal:** loses at every stop and take profit (-259.1 to -99.3 pips), in both weeks.
- **3. Trend-day recognition:** no day moved 80 pips net between 07:00 and 17:00 (one by range), so the measures cannot be judged yet.
