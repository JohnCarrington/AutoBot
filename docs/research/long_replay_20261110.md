# The bot's current rules replayed from February 2024 to November 2026

10 November 2026. Research only: nothing in the bot was changed. No IG calls, no restart of the price service, nothing written outside `data/research/`; every long job ran at `nice -n 19`.

## Summary

**The bot's current rules lose over the whole period, in every year and in every strategy.** Replayed through the bot's own code from Sunday 18 February 2024 to Friday 6 November 2026 (139 weeks with candles), with the news rules on:

| Bollinger bounce and range trade stop | Trades | Won % | Pips | Biggest loss | Worst losing run | Weeks up | Months up |
|---|---:|---:|---:|---:|---:|---:|---:|
| **6 pips** (today's `.env`) | 9,819 | 31% | **−8,975.8** | −74.8 | 26 | 40 of 139 | 7 of 34 |
| **12 pips** (commit `0e1492b`) | 9,360 | 34% | **−7,007.7** | −74.8 | 21 | 46 of 139 | 9 of 34 |

- **By year (6-pip stop):** 2024 −775.0, 2025 −5,250.0, 2026 to 6 November −2,950.8. **With the 12-pip stop:** −121.1, −4,439.2 and −2,447.4.
- **Every strategy loses**, with either stop. With the 6-pip stop: Bollinger bounce −3,130.4, EMA pullback −2,741.5, slow grind −1,062.4, breakout −947.7, level reversal −945.7, range trade −148.1.
- **The 12-pip stop is better, by +1,968 pips, but it does not make the bot profitable.** Almost all of the gain is in the Bollinger bounce (+1,931.8: from −3,130.4 to −1,198.6; won 37% instead of 25%, worst losing run 15 instead of 43), and it is better in every year. The range trade gains +36.3. The other four strategies are unchanged, trade for trade.
- **The fortnight the earlier checks used (25 October to 6 November 2026) was the best of the whole period.** The week of 1 November is the best of all 139 weeks (+754.9), and the week of 25 October made +202.7. The 33 months before lost in 27.
- **The spread costs more than the bot makes.** The average spread when a trade opens is about 1.3 pips; over 9,819 trades that is roughly 12,500 pips. Before the spread the trades would come to about +3,500: the rules pick the direction a little better than chance, but not by enough to pay for so many short trades.
- **The level reversal's stop has no limit on its distance.** It is 6 pips beyond the furthest point of the move, however far that is. 185 of its losses were more than 20 pips (−4,896.8 together), 34 more than 30, and the biggest was −74.8 (5 August 2024).
- **How far to trust it:** section 3 showed that the research store's candles move a two-week result by about 15% through spread noise alone. That cannot turn a loss in every year and every strategy into a profit, but read any single total as one plausible path, not exact to the pip.

## 1. The research mode

`research/long_replay.py` replays any date range through **the bot's own code, as the live engine runs it**: each trading week goes through `trading.engine.Trading` exactly as the bot's own replay (`trading.replay_check.wired_trades`) runs it. That covers the analyser, the strategies, the safety rules inside the order sender (paper mode, with a pretend IG that only gives the funds and fails any other call), the trade manager and the records. Trades still open at the end of a week or of the range are counted at the last candle's close, as the bot's replay does. Only three things differ, all about where it reads and writes:

- **Candles:** a research store folder in the bot's own format (`research/replay_store.py`), read with the bot's own `CandleStore`:

  | Candles starting (UK time) | From | Sell price | Buy price |
  |---|---|---|---|
  | before 1 January 2026 | AutoBot 161's IG 5-minute candles, 2024–25 | IG's bid as 161 stored it | sell + IG's typical spread for that half hour of the week |
  | 1 January to 24 October 2026 | 161's 2026 IG mid candles | mid − half the typical spread | mid + half (`ig161_mid_2026_20261110.md`) |
  | from 25 October 2026 | the bot's own IG candles (read only) | IG's | IG's |

  The hourly and daily candles are built from the 5-minute ones exactly as the bot builds its own. The half-hour spread table is the one in `dukascopy_check_20261109.md`.
- **The economic calendar:** Finnhub's calendar for the past (section 2), written for each week into the run's own news folder, which is where the bot's news rules read it. With no calendar the run says "NO NEWS RULES" in every result.
- **Folders:** every folder the engine writes to (orders, trade manager, safety, records, status, the pause file, news, the analyser's) is moved into the run's folder under `data/research/replay/`. The live folders are refused, and tests check every one is moved.

**The rules replayed are the bot's current ones:** the code at this commit and today's settings and switches, frozen once per run (`switches.env` in the run folder) so that every week uses the same rules. All six strategies are on, and `TRADING` is off (paper). **The Bollinger bounce and range trade stop is 6 pips**, because `.env` still has `STOP_LOSS_PIPS=6`; commit `0e1492b` says it is to be 12, but `.env` has not been changed. The breakout's stop is 12 (`settings.toml`), the EMA pullback's 12 and the slow grind's 15.

**Warm-up:** each week starts at its open with the bot's own warm-up taken from the store before it: 2,000 5-minute candles, 600 hourly candles for the EMA pullback's hourly trend, and the daily candles for the trend day and the levels. The first week with all of that already in the store is the week of **Sunday 18 February 2024**, so the long replay starts there.

**Speed:** the bot's own replay takes about 12 minutes per trading week here. The research mode adds two caches, for its own process only. The research store's files are read once (the store never changes during a replay; the live store is never cached). The analyser's features are worked out once per week instead of again at every candle: they are causal, so the first *n* are the same either way (a test checks this on 400 candles). With these, a week takes about 40 seconds. Section 3 shows the results are trade for trade the same as the bot's own replay.

## 2. News: Finnhub's past calendar

**Finnhub does give past calendars with the existing key.** `research/news_history.py` fetched November 2023 to November 2026: one request per month, at least 20 seconds apart (3 a minute at most), backing off on any refusal. **37 requests, no refusals, 97,239 releases.** Every month's reply reached both ends of the month. Every month has 10 to 19 big GBP or USD releases by the bot's news table (`config/news_table.toml`), including US payrolls, CPI, the Fed and the Bank of England every month. Saved in `data/research/news/finnhub_calendar.json`; the key was read as the bot reads it and never printed or saved.

**Caveat:** Finnhub's forecasts and previous figures are as Finnhub holds them today. Where a previous figure was later revised, the expected direction worked out from it may differ from the one the bot would have seen on the day.

**The news rules are on in every result below.**

## 3. The check: 25 October to 6 November

### First: the research mode is the bot's own replay

On exactly the bot's inputs (a read-only copy of the live candle store and of the bot's own calendar file, both taken on the afternoon of 10 November), over exactly the bot's replay period (Sunday 25 October 21:00 UK to the candle of Monday 9 November 10:00 UTC):

| | Trades | Won | Lost | Pips | Biggest loss | Worst losing run | Time |
|---|---:|---:|---:|---:|---:|---:|---:|
| The bot's own replay (`trading.replay_check.wired_trades`, unchanged) | 155 | 77 | 77 | +1162.3 | −17.4 | 7 | 27 minutes |
| The research mode | 155 | 77 | 77 | +1162.3 | −17.4 | 7 | 1.5 minutes |

**All 155 trades are identical in every field:** entry time, strategy, direction, entry price, fill, pips, close time, how and why it closed, and the analyser's state. So every difference below comes from the inputs, not from the research mode.

### Then: the research store against the bot's own candles, 25 October 21:00 UK to 6 November 18:05 UTC

161's 2026 candles end at its last candle (Friday 6 November 18:00 UTC), so this check stops there. Five runs separate the two inputs that change:

| Run | Candles in the period | Candles before it (warm-up) | Calendar | Trades | Won | Lost | Pips |
|---|---|---|---|---:|---:|---:|---:|
| **A**: the bot's own replay of those days | IG's (bot's own) | IG's (bot's store) | bot's own file | 149 | 73 | 75 | **+1063.2** |
| E | IG's | 161's | bot's own | 151 | 73 | 77 | +1049.2 |
| B | 161's rebuilt | 161's | bot's own | 157 | 71 | 86 | +890.8 |
| D | IG's | IG's | Finnhub's | 144 | 69 | 74 | +937.3 |
| **C**: the research store, as the long replay reads it | 161's rebuilt | 161's | Finnhub's | 152 | 67 | 85 | **+785.5** |

Biggest loss −17.4 in all five, worst losing run 6 or 7. **The research store makes 277.7 pips (26%) less than the bot's own replay over these two weeks.** Trade by trade (`research/replay_compare.py`), that comes from three causes:

**1. The calendar: −125.9 pips (A → D, same candles).** 138 trades the same, 6 with a different result, 5 only in A.
- **The bot's own calendar file holds only 31 October onwards** (it keeps a rolling window), so the bot's own replay of 25 to 30 October runs with no news at all. Finnhub's past calendar has the two big releases in those days: the Fed decision (Wednesday 28 October 18:00 UTC) and US GDP (Thursday 29 October 12:30, expected "GBPUSD down").
- With them, the news rules refuse 5 reversal buys on Thursday 29 October as against a big-news day's expected direction (−95.5 pips of winners). Two trades are closed 15 minutes before the Fed (+25.0 net), and four close differently because the news day changes their take profit or management (−55.4).
- **Here the Finnhub run is the one closer to a bot running on those days.** The bot fetches 14 days ahead, so it would have had both releases. The bot's own replay leaves them out only because its calendar file has since rolled past them, and that makes these two weeks look better than they would have been.

**2. The warm-up history before 25 October: −14.0 pips (A → E).** 147 trades the same, 6 different (161's daily and hourly candles shift a pivot or a state now and then). Small.

**3. The candles inside the period: −158.4 pips (E → B).** Only 77 trades the same; 55 have a different result, 19 are only on IG's real candles and 25 only on 161's rebuilt ones.
- 161's mid is exactly IG's, so the whole difference is the spread. Where the half-hour table says 1.5 and IG's real spread was 0.9 (or the other way round), the rebuilt sell price is 0.3 points off. That happens on about 4 in 10 candles in normal hours (`ig161_mid_2026_20261110.md`).
- **Fills hardly matter:** 36 trades filled 0.3 points apart, for −1.0 pips net.
- **The path matters:** a sell price 0.3 points different moves a candle across a band, a level or an entry trigger. The analyser's state then changes, a setup triggers a candle earlier or later, or a trade of the same strategy is still open when the next one comes (the safety rules allow one at a time). Of the 44 trades taken in only one run, the causes were: the entry candle differing (11), the analyser's state (10), a trade of that strategy already open (8), the candles just before it differing (6), more or fewer copies opened in the same minute (6), and another rule (3).
- Over two weeks the net was −158 pips. **That is not a bias that can be corrected:** the same 0.3-point noise could as easily have gone the other way. It is a measure of how much the bot's result moves when the chart price moves by a fraction of a pip.

**What this means for the long replay.** The research mode itself is exact. But its candles are not the bot's: 2024–25 is IG's bid as 161 stored it (typically 0.2 to 0.3 points from IG's own daily candles, `dukascopy_check_20261109.md`) with a typical spread added, and 2026 is IG's exact mid with a typical spread. **Read the long-replay totals as one plausible path of the current rules, not as what they would have made to the pip:** in this check, two weeks moved by 15% on spread noise alone. Comparisons between strategies, or between years, are more trustworthy than any single total. A difference of a few percent between two rule sets would not be significant here.

## 4. The whole period

Sunday 18 February 2024 21:00 UTC (the first fully warmed-up week) to the close on Friday 6 November 2026: 142 trading weeks, two weeks running side by side at `nice -n 19`, each week as in section 1, with Finnhub's calendar and the news rules on. Run folders: `data/research/replay/long_20261110` (6-pip stop, today's switches) and `long_20261110_stop12` (the same switches with `STOP_LOSS_PIPS=12`; nothing else changed).

**What the data does not cover:**
- **1 to 22 March 2026: no candles** (161's 2026 archive has none), so the weeks of 1, 8 and 15 March have no trades and March 2026 is only its last nine days.
- April, May and July 2026 have only 84–91% of their 5-minute candles (gaps in 161's 2026 archive, listed in `data/research/candles_ig161_2026/GBPUSD/gaps.csv`). December and January show 95–96% because of the Christmas and New Year closures, which the market hours count as open.
- November 2026 is 1 to 6 November only.

**A fix during the run.** The 6-pip run was stopped and restarted twice early on. A restarted week re-used the engine folder of its interrupted attempt, so that attempt's open trades were still in the trade manager: in the week of 10 March 2024 the safety rules then refused 9 slow grind trades ("slow grind already has 1 trade(s) open"). The research mode now empties a week's engine folder before running it (with a test). Comparing every week's records with the 12-pip run, which was never interrupted, found two such weeks (10 and 24 March 2024); both were rerun. After that, **the four strategies the stop does not touch are identical, trade for trade, in the two runs**, which also checks that each run is repeatable.

### The current rules (6-pip Bollinger bounce and range trade stop)

Period: 2024-02-18T21:00:00Z to 2026-11-07T00:00:00Z (UTC), 142 trading weeks. News rules ON (the calendar given).

#### The whole period, by strategy

| Strategy | Trades | Won | Lost | Won % | Pips | Biggest loss | Worst losing run |
|---|---:|---:|---:|---:|---:|---:|---:|
| slow grind | 1614 | 768 | 842 | 48% | **-1062.4** | -15.2 | 14 |
| EMA pullback | 2914 | 646 | 2266 | 22% | **-2741.5** | -25.6 | 43 |
| Bollinger bounce | 2761 | 698 | 2058 | 25% | **-3130.4** | -8.7 | 43 |
| range trade | 220 | 79 | 141 | 36% | **-148.1** | -6.0 | 8 |
| breakout | 762 | 151 | 611 | 20% | **-947.7** | -25.7 | 29 |
| level reversal | 1548 | 715 | 829 | 46% | **-945.7** | -74.8 | 11 |
| **Whole bot** | 9819 | 3057 | 6747 | 31% | **-8975.8** | -74.8 | 26 |

#### By year, the whole bot

| Year | Trades | Won | Lost | Won % | Pips | Biggest loss | Worst losing run |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2024 | 3041 | 1006 | 2029 | 33% | **-775.0** | -74.8 | 21 |
| 2025 | 4041 | 1240 | 2796 | 31% | **-5250.0** | -64.8 | 19 |
| 2026 | 2737 | 811 | 1922 | 30% | **-2950.8** | -58.6 | 26 |

#### 2024, by strategy

| Strategy | Trades | Won | Lost | Won % | Pips | Biggest loss | Worst losing run |
|---|---:|---:|---:|---:|---:|---:|---:|
| slow grind | 514 | 237 | 275 | 46% | **-391.7** | -15.2 | 9 |
| EMA pullback | 857 | 224 | 633 | 26% | **+880.7** | -25.6 | 40 |
| Bollinger bounce | 852 | 232 | 617 | 27% | **-683.8** | -6.2 | 16 |
| range trade | 63 | 23 | 40 | 37% | **-16.3** | -6.0 | 6 |
| breakout | 259 | 54 | 205 | 21% | **-198.0** | -25.7 | 18 |
| level reversal | 496 | 236 | 259 | 48% | **-365.9** | -74.8 | 9 |
| **Whole bot** | 3041 | 1006 | 2029 | 33% | **-775.0** | -74.8 | 21 |

#### 2025, by strategy

| Strategy | Trades | Won | Lost | Won % | Pips | Biggest loss | Worst losing run |
|---|---:|---:|---:|---:|---:|---:|---:|
| slow grind | 665 | 325 | 339 | 49% | **-537.7** | -15.0 | 8 |
| EMA pullback | 1248 | 251 | 996 | 20% | **-2968.4** | -24.2 | 43 |
| Bollinger bounce | 1131 | 283 | 846 | 25% | **-1264.1** | -6.6 | 20 |
| range trade | 75 | 26 | 49 | 35% | **-55.2** | -6.0 | 6 |
| breakout | 294 | 55 | 239 | 19% | **-399.1** | -19.1 | 29 |
| level reversal | 628 | 300 | 327 | 48% | **-25.5** | -64.8 | 10 |
| **Whole bot** | 4041 | 1240 | 2796 | 31% | **-5250.0** | -64.8 | 19 |

#### 2026, by strategy

| Strategy | Trades | Won | Lost | Won % | Pips | Biggest loss | Worst losing run |
|---|---:|---:|---:|---:|---:|---:|---:|
| slow grind | 435 | 206 | 228 | 47% | **-133.0** | -15.0 | 14 |
| EMA pullback | 809 | 171 | 637 | 21% | **-653.8** | -17.5 | 37 |
| Bollinger bounce | 778 | 183 | 595 | 24% | **-1182.5** | -8.7 | 43 |
| range trade | 82 | 30 | 52 | 37% | **-76.6** | -6.0 | 8 |
| breakout | 209 | 42 | 167 | 20% | **-350.6** | -15.9 | 16 |
| level reversal | 424 | 179 | 243 | 42% | **-554.3** | -58.6 | 11 |
| **Whole bot** | 2737 | 811 | 1922 | 30% | **-2950.8** | -58.6 | 26 |

#### By month, the whole bot (with how complete the candles were)

| Month | Candles | Trades | Won | Lost | Won % | Pips | Biggest loss | Worst losing run |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2024-02 | 99% | 117 | 38 | 79 | 32% | **-305.1** | -23.8 | 10 |
| 2024-03 | 100% | 259 | 86 | 173 | 33% | **-147.7** | -29.5 | 21 |
| 2024-04 | 99% | 252 | 83 | 168 | 33% | **-60.4** | -27.2 | 21 |
| 2024-05 | 99% | 273 | 86 | 186 | 32% | **-62.9** | -29.4 | 11 |
| 2024-06 | 99% | 240 | 78 | 162 | 32% | **-287.6** | -22.9 | 12 |
| 2024-07 | 99% | 257 | 95 | 160 | 37% | **+833.0** | -33.0 | 20 |
| 2024-08 | 99% | 347 | 107 | 239 | 31% | **-176.9** | -74.8 | 14 |
| 2024-09 | 99% | 298 | 112 | 186 | 38% | **+307.3** | -40.3 | 17 |
| 2024-10 | 99% | 334 | 97 | 237 | 29% | **-846.4** | -24.2 | 11 |
| 2024-11 | 98% | 347 | 126 | 221 | 36% | **+521.6** | -37.9 | 12 |
| 2024-12 | 96% ⚠ | 317 | 98 | 218 | 31% | **-549.7** | -31.5 | 12 |
| 2025-01 | 95% ⚠ | 351 | 127 | 224 | 36% | **+375.3** | -41.7 | 19 |
| 2025-02 | 99% | 321 | 94 | 226 | 29% | **-592.3** | -64.8 | 13 |
| 2025-03 | 99% | 362 | 92 | 270 | 25% | **-1119.7** | -34.5 | 16 |
| 2025-04 | 99% | 425 | 144 | 281 | 34% | **+289.2** | -43.4 | 14 |
| 2025-05 | 99% | 347 | 106 | 240 | 31% | **-493.5** | -36.4 | 16 |
| 2025-06 | 99% | 345 | 102 | 243 | 30% | **-466.2** | -28.4 | 16 |
| 2025-07 | 99% | 366 | 116 | 250 | 32% | **-445.2** | -26.3 | 14 |
| 2025-08 | 99% | 320 | 104 | 216 | 32% | **-279.3** | -31.0 | 14 |
| 2025-09 | 99% | 299 | 97 | 202 | 32% | **-371.7** | -42.9 | 12 |
| 2025-10 | 99% | 329 | 94 | 235 | 29% | **-801.3** | -29.6 | 13 |
| 2025-11 | 99% | 298 | 79 | 216 | 27% | **-878.1** | -22.8 | 12 |
| 2025-12 | 96% ⚠ | 278 | 85 | 193 | 31% | **-467.2** | -26.4 | 15 |
| 2026-01 | 95% ⚠ | 298 | 94 | 204 | 32% | **-356.1** | -58.6 | 13 |
| 2026-02 | 99% | 268 | 89 | 179 | 33% | **-52.9** | -39.1 | 15 |
| 2026-03 | 29% ⚠ | 118 | 20 | 98 | 17% | **-717.6** | -44.5 | 26 |
| 2026-04 | 91% ⚠ | 344 | 94 | 250 | 27% | **-515.1** | -24.6 | 24 |
| 2026-05 | 84% ⚠ | 265 | 77 | 187 | 29% | **-534.9** | -41.5 | 17 |
| 2026-06 | 97% ⚠ | 309 | 96 | 213 | 31% | **-6.2** | -24.0 | 9 |
| 2026-07 | 87% ⚠ | 261 | 89 | 171 | 34% | **+555.6** | -20.8 | 14 |
| 2026-08 | 100% | 233 | 57 | 176 | 24% | **-715.6** | -25.9 | 18 |
| 2026-09 | 97% ⚠ | 271 | 64 | 207 | 24% | **-1022.0** | -28.6 | 15 |
| 2026-10 | 97% | 284 | 92 | 190 | 32% | **-340.8** | -23.1 | 12 |
| 2026-11 | 32% ⚠ | 86 | 39 | 47 | 45% | **+754.9** | -17.4 | 7 |

#### By month and strategy: pips (trades)

| Month | slow grind | EMA pullback | Bollinger bounce | range trade | breakout | level reversal | Whole bot |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2024-02 | -55.9 (16) | -87.2 (24) | -62.5 (38) | +9.9 (2) | -87.1 (12) | -22.3 (25) | -305.1 (117) |
| 2024-03 | -37.2 (47) | -101.3 (66) | -12.1 (69) | +9.5 (8) | -7.4 (26) | +0.8 (43) | -147.7 (259) |
| 2024-04 | -25.5 (46) | -7.4 (76) | -74.1 (59) | -14.0 (8) | -4.0 (21) | +64.6 (42) | -60.4 (252) |
| 2024-05 | -47.8 (49) | +365.4 (76) | -130.5 (79) | -26.2 (7) | -235.2 (26) | +11.4 (36) | -62.9 (273) |
| 2024-06 | -153.4 (43) | -130.8 (58) | -101.1 (76) | -3.4 (6) | +30.7 (21) | +70.4 (36) | -287.6 (240) |
| 2024-07 | -110.2 (47) | +790.5 (75) | -6.0 (62) | +1.4 (8) | +99.6 (26) | +57.7 (39) | +833.0 (257) |
| 2024-08 | +116.5 (44) | +102.9 (122) | -24.5 (87) | -9.6 (3) | +66.8 (22) | -429.0 (69) | -176.9 (347) |
| 2024-09 | +102.9 (59) | +78.1 (80) | -15.1 (84) | -2.4 (4) | +188.8 (22) | -45.0 (49) | +307.3 (298) |
| 2024-10 | -114.4 (56) | -534.0 (97) | -141.3 (95) | +16.0 (4) | -112.6 (27) | +39.9 (55) | -846.4 (334) |
| 2024-11 | +153.3 (49) | +518.6 (106) | -64.1 (100) | -17.1 (8) | -12.0 (29) | -57.1 (55) | +521.6 (347) |
| 2024-12 | -220.0 (58) | -114.1 (77) | -52.5 (103) | +19.8 (5) | -125.6 (27) | -57.3 (47) | -549.7 (317) |
| 2025-01 | +127.1 (59) | +109.5 (99) | -102.3 (91) | -3.4 (2) | +134.0 (32) | +110.4 (68) | +375.3 (351) |
| 2025-02 | -84.9 (49) | -84.8 (87) | -284.7 (111) | +3.0 (4) | -34.6 (19) | -106.3 (51) | -592.3 (321) |
| 2025-03 | -68.5 (56) | -758.7 (108) | -122.5 (120) | +5.3 (5) | -139.8 (26) | -35.5 (47) | -1119.7 (362) |
| 2025-04 | -28.5 (69) | +259.6 (167) | -186.4 (98) | +29.6 (2) | +106.8 (24) | +108.1 (65) | +289.2 (425) |
| 2025-05 | -59.0 (58) | -320.0 (95) | -66.9 (106) | -4.4 (6) | -114.6 (27) | +71.4 (55) | -493.5 (347) |
| 2025-06 | -113.4 (57) | -475.1 (107) | +26.8 (100) | -13.4 (10) | +11.1 (26) | +97.8 (45) | -466.2 (345) |
| 2025-07 | -4.9 (73) | -235.8 (96) | -69.3 (101) | -20.5 (9) | -4.0 (29) | -110.7 (58) | -445.2 (366) |
| 2025-08 | -22.2 (48) | +205.8 (103) | -61.3 (82) | -54.3 (17) | -80.1 (18) | -267.2 (52) | -279.3 (320) |
| 2025-09 | +93.0 (49) | -273.0 (96) | -103.5 (78) | -6.7 (8) | -72.9 (25) | -8.6 (43) | -371.7 (299) |
| 2025-10 | -38.1 (48) | -680.1 (117) | -154.1 (91) | +18.7 (3) | -50.4 (18) | +102.7 (52) | -801.3 (329) |
| 2025-11 | -246.6 (54) | -663.8 (98) | -68.2 (76) | -17.3 (5) | -16.0 (22) | +133.8 (43) | -878.1 (298) |
| 2025-12 | -91.7 (45) | -52.0 (75) | -71.7 (77) | +8.2 (4) | -138.6 (28) | -121.4 (49) | -467.2 (278) |
| 2026-01 | -102.0 (52) | -29.9 (98) | +72.0 (62) | -19.9 (8) | -172.6 (25) | -103.7 (53) | -356.1 (298) |
| 2026-02 | -65.0 (47) | -39.0 (72) | +136.5 (72) | -18.0 (6) | -78.2 (21) | +10.8 (50) | -52.9 (268) |
| 2026-03 | -88.5 (22) | -360.2 (30) | -184.3 (43) | - | -6.5 (3) | -78.1 (20) | -717.6 (118) |
| 2026-04 | +16.5 (44) | -107.3 (123) | -374.3 (95) | -13.1 (12) | +119.1 (21) | -156.0 (49) | -515.1 (344) |
| 2026-05 | -100.2 (40) | -189.2 (72) | -195.4 (90) | +6.3 (1) | +28.4 (18) | -84.8 (44) | -534.9 (265) |
| 2026-06 | +173.6 (51) | +12.7 (92) | -132.6 (90) | +11.7 (10) | -205.9 (22) | +134.3 (44) | -6.2 (309) |
| 2026-07 | +86.0 (47) | +352.6 (60) | -29.9 (91) | -13.1 (11) | +116.1 (19) | +43.9 (33) | +555.6 (261) |
| 2026-08 | -144.0 (33) | -261.0 (60) | -223.9 (70) | -27.0 (13) | +31.4 (20) | -91.1 (37) | -715.6 (233) |
| 2026-09 | -100.2 (50) | -558.7 (69) | -122.7 (75) | -0.5 (11) | -100.5 (27) | -139.4 (39) | -1022.0 (271) |
| 2026-10 | +87.9 (41) | -70.2 (91) | -91.6 (76) | -20.1 (5) | -75.7 (26) | -171.1 (45) | -340.8 (284) |
| 2026-11 | +102.9 (8) | +596.4 (42) | -36.3 (14) | +17.2 (5) | -6.2 (7) | +80.9 (10) | +754.9 (86) |

### The same period with the 12-pip stop

The same store, calendar, code and switches, with only `STOP_LOSS_PIPS` changed from 6 to 12 for the run (`--set STOP_LOSS_PIPS=12`, recorded in the run's `run.json` and `switches.env`; `.env` was not touched). That switch is the stop of the Bollinger bounce and the range trade. The breakout's 12, the EMA pullback's 12, the slow grind's 15 and the level reversal's own stop are unchanged.

**First, on the bot's own inputs** (the section 3 check period, 25 October to 9 November, live candle store copy and the bot's calendar): 155 trades and +1,162.3 pips with the 6-pip stop, 151 trades and +1,192.9 with 12. The stopped-out bounces now lose −12 instead of −6, as intended.

**Over the whole period:**

- **+1,968.1 pips better** (−7,007.7 instead of −8,975.8), better in every year: 2024 +654, 2025 +811, 2026 +503.
- **The Bollinger bounce gains +1,931.8.** With 6 pips most of its trades were stopped out by ordinary noise: won 25%, worst losing run 43. With 12 it wins 37%, its worst losing run is 15 and it trades 445 times less (one at a time, so a trade that stays open longer blocks the next). It still loses −1,198.6.
- **The range trade gains +36.3** (won 46% instead of 36%).
- **The slow grind, EMA pullback, breakout and level reversal are unchanged, trade for trade.**
- The 12-pip stop does not make any strategy profitable over the period. The comparison is between two runs on the same candles, so it is more trustworthy than either total (section 3).

#### Stop 6 and stop 12: the whole period

| Strategy | Stop 6: trades | won % | pips | biggest loss | worst run | Stop 12: trades | won % | pips | biggest loss | worst run | Change in pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| slow grind | 1614 | 48% | -1062.4 | -15.2 | 14 | 1614 | 48% | -1062.4 | -15.2 | 14 | **+0.0** |
| EMA pullback | 2914 | 22% | -2741.5 | -25.6 | 43 | 2914 | 22% | -2741.5 | -25.6 | 43 | **+0.0** |
| Bollinger bounce | 2761 | 25% | -3130.4 | -8.7 | 43 | 2316 | 37% | -1198.6 | -12.1 | 15 | **+1931.8** |
| range trade | 220 | 36% | -148.1 | -6.0 | 8 | 206 | 46% | -111.8 | -12.0 | 6 | **+36.3** |
| breakout | 762 | 20% | -947.7 | -25.7 | 29 | 762 | 20% | -947.7 | -25.7 | 29 | **+0.0** |
| level reversal | 1548 | 46% | -945.7 | -74.8 | 11 | 1548 | 46% | -945.7 | -74.8 | 11 | **+0.0** |
| **Whole bot** | 9819 | 31% | -8975.8 | -74.8 | 26 | 9360 | 34% | -7007.7 | -74.8 | 21 | **+1968.1** |

#### Stop 6 and stop 12: 2024

| Strategy | Stop 6: trades | won % | pips | biggest loss | worst run | Stop 12: trades | won % | pips | biggest loss | worst run | Change in pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| slow grind | 514 | 46% | -391.7 | -15.2 | 9 | 514 | 46% | -391.7 | -15.2 | 9 | **+0.0** |
| EMA pullback | 857 | 26% | +880.7 | -25.6 | 40 | 857 | 26% | +880.7 | -25.6 | 40 | **+0.0** |
| Bollinger bounce | 852 | 27% | -683.8 | -6.2 | 16 | 721 | 39% | -47.4 | -12.0 | 10 | **+636.4** |
| range trade | 63 | 37% | -16.3 | -6.0 | 6 | 60 | 47% | +1.2 | -12.0 | 5 | **+17.5** |
| breakout | 259 | 21% | -198.0 | -25.7 | 18 | 259 | 21% | -198.0 | -25.7 | 18 | **+0.0** |
| level reversal | 496 | 48% | -365.9 | -74.8 | 9 | 496 | 48% | -365.9 | -74.8 | 9 | **+0.0** |
| **Whole bot** | 3041 | 33% | -775.0 | -74.8 | 21 | 2907 | 36% | -121.1 | -74.8 | 21 | **+653.9** |

#### Stop 6 and stop 12: 2025

| Strategy | Stop 6: trades | won % | pips | biggest loss | worst run | Stop 12: trades | won % | pips | biggest loss | worst run | Change in pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| slow grind | 665 | 49% | -537.7 | -15.0 | 8 | 665 | 49% | -537.7 | -15.0 | 8 | **+0.0** |
| EMA pullback | 1248 | 20% | -2968.4 | -24.2 | 43 | 1248 | 20% | -2968.4 | -24.2 | 43 | **+0.0** |
| Bollinger bounce | 1131 | 25% | -1264.1 | -6.6 | 20 | 940 | 37% | -471.2 | -12.0 | 13 | **+792.9** |
| range trade | 75 | 35% | -55.2 | -6.0 | 6 | 68 | 46% | -37.3 | -12.0 | 5 | **+17.9** |
| breakout | 294 | 19% | -399.1 | -19.1 | 29 | 294 | 19% | -399.1 | -19.1 | 29 | **+0.0** |
| level reversal | 628 | 48% | -25.5 | -64.8 | 10 | 628 | 48% | -25.5 | -64.8 | 10 | **+0.0** |
| **Whole bot** | 4041 | 31% | -5250.0 | -64.8 | 19 | 3843 | 34% | -4439.2 | -64.8 | 16 | **+810.8** |

#### Stop 6 and stop 12: 2026

| Strategy | Stop 6: trades | won % | pips | biggest loss | worst run | Stop 12: trades | won % | pips | biggest loss | worst run | Change in pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| slow grind | 435 | 47% | -133.0 | -15.0 | 14 | 435 | 47% | -133.0 | -15.0 | 14 | **+0.0** |
| EMA pullback | 809 | 21% | -653.8 | -17.5 | 37 | 809 | 21% | -653.8 | -17.5 | 37 | **+0.0** |
| Bollinger bounce | 778 | 24% | -1182.5 | -8.7 | 43 | 655 | 34% | -680.0 | -12.1 | 15 | **+502.5** |
| range trade | 82 | 37% | -76.6 | -6.0 | 8 | 78 | 46% | -75.7 | -12.0 | 6 | **+0.9** |
| breakout | 209 | 20% | -350.6 | -15.9 | 16 | 209 | 20% | -350.6 | -15.9 | 16 | **+0.0** |
| level reversal | 424 | 42% | -554.3 | -58.6 | 11 | 424 | 42% | -554.3 | -58.6 | 11 | **+0.0** |
| **Whole bot** | 2737 | 30% | -2950.8 | -58.6 | 26 | 2610 | 33% | -2447.4 | -58.6 | 20 | **+503.4** |

#### The 12-pip stop by month, the whole bot (candles as above)

| Month | Candles | Trades | Won | Lost | Won % | Pips | Biggest loss | Worst losing run |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2024-02 | 99% | 108 | 39 | 69 | 36% | **-261.1** | -23.8 | 10 |
| 2024-03 | 100% | 251 | 93 | 158 | 37% | **-90.6** | -29.5 | 12 |
| 2024-04 | 99% | 246 | 87 | 158 | 35% | **-76.4** | -27.2 | 21 |
| 2024-05 | 99% | 260 | 90 | 169 | 35% | **-9.3** | -29.4 | 10 |
| 2024-06 | 99% | 229 | 82 | 147 | 36% | **-277.2** | -22.9 | 10 |
| 2024-07 | 99% | 247 | 99 | 146 | 40% | **+934.1** | -33.0 | 19 |
| 2024-08 | 99% | 334 | 115 | 218 | 34% | **-78.8** | -74.8 | 10 |
| 2024-09 | 99% | 286 | 119 | 166 | 42% | **+405.4** | -40.3 | 8 |
| 2024-10 | 99% | 322 | 97 | 225 | 30% | **-900.2** | -24.2 | 11 |
| 2024-11 | 98% | 325 | 131 | 194 | 40% | **+558.0** | -37.9 | 12 |
| 2024-12 | 96% ⚠ | 299 | 109 | 190 | 36% | **-324.8** | -31.5 | 12 |
| 2025-01 | 95% ⚠ | 331 | 136 | 195 | 41% | **+576.9** | -41.7 | 11 |
| 2025-02 | 99% | 307 | 95 | 211 | 31% | **-714.1** | -64.8 | 13 |
| 2025-03 | 99% | 331 | 95 | 235 | 29% | **-1076.5** | -34.5 | 16 |
| 2025-04 | 99% | 403 | 152 | 251 | 38% | **+343.8** | -43.4 | 14 |
| 2025-05 | 99% | 328 | 113 | 214 | 34% | **-355.5** | -36.4 | 13 |
| 2025-06 | 99% | 325 | 109 | 216 | 34% | **-383.6** | -28.4 | 11 |
| 2025-07 | 99% | 351 | 121 | 230 | 34% | **-445.3** | -26.3 | 12 |
| 2025-08 | 99% | 301 | 112 | 189 | 37% | **-90.8** | -31.0 | 12 |
| 2025-09 | 99% | 287 | 106 | 181 | 37% | **-257.0** | -42.9 | 11 |
| 2025-10 | 99% | 316 | 97 | 219 | 31% | **-776.7** | -29.6 | 13 |
| 2025-11 | 99% | 291 | 85 | 203 | 29% | **-834.1** | -22.8 | 12 |
| 2025-12 | 96% ⚠ | 272 | 88 | 184 | 32% | **-426.5** | -26.4 | 14 |
| 2026-01 | 95% ⚠ | 292 | 99 | 193 | 34% | **-335.2** | -58.6 | 11 |
| 2026-02 | 99% | 259 | 94 | 165 | 36% | **+16.7** | -39.1 | 14 |
| 2026-03 | 29% ⚠ | 106 | 23 | 83 | 22% | **-644.1** | -44.5 | 20 |
| 2026-04 | 91% ⚠ | 329 | 102 | 227 | 31% | **-469.6** | -24.6 | 20 |
| 2026-05 | 84% ⚠ | 247 | 80 | 166 | 32% | **-489.2** | -41.5 | 16 |
| 2026-06 | 97% ⚠ | 295 | 99 | 196 | 34% | **+21.7** | -24.0 | 9 |
| 2026-07 | 87% ⚠ | 246 | 95 | 150 | 39% | **+629.2** | -20.8 | 14 |
| 2026-08 | 100% | 222 | 64 | 158 | 29% | **-624.0** | -25.9 | 13 |
| 2026-09 | 97% ⚠ | 260 | 68 | 192 | 26% | **-997.7** | -28.6 | 14 |
| 2026-10 | 97% | 271 | 94 | 175 | 35% | **-339.0** | -23.1 | 12 |
| 2026-11 | 32% ⚠ | 83 | 41 | 42 | 49% | **+783.8** | -17.4 | 6 |

## 5. Data, folders and code

All data is under `data/research/` (git-ignored, never committed). Sizes:

| Folder | Size | What |
|---|---:|---|
| `ig161/` | 21 MB | 161's 2024–25 archive, unpacked |
| `candles_ig161/` | 18 MB | 2024–25 in the bot's format (sell only) |
| `candles_ig161_bidask/` | 22 MB | 2024–25 with the buy price added |
| `candles_ig161_2026/` | 8.4 MB | 161's 2026 mid turned into buy and sell |
| `ig_spread/` | 12 KB | the half-hour spread table |
| `news/` | 19 MB | Finnhub's calendar, November 2023 to November 2026, and a copy of the bot's calendar file |
| `replay_stores/` | 63 MB | `main` (the long replay's store, 30 MB), `check161` (section 3, 30 MB), `live_copy_20261110` (read-only copy of the live store, 3.2 MB) |
| `replay/` | 275 MB | `long_20261110` (132 MB), `long_20261110_stop12` (130 MB), `check` (15 MB), `profile` |
| **`data/research/` in all** | **425 MB** | |

**Code** (all new, in `research/`):
- `news_history.py`: fetches Finnhub's past calendar a month at a time, at least 20 seconds apart, backing off on refusals.
- `replay_store.py`: builds a research candle store from the three sources, each candle from its own source.
- `long_replay.py`: the research mode: one week at a time through `trading.engine.Trading`, folders moved into the run, switches frozen per run (`--set SWITCH=VALUE` changes one for that run only, never `TRADING`), results and comparisons.
- `replay_compare.py`: two runs trade by trade, with the cause of each difference.
- `long_report.py`: the tables in this report, and the side-by-side comparison of two runs.

**Tests:** `tests/technical/test_research_candles.py`, 38 tests in all, including that nothing is written to a live folder, every engine folder is moved, the calendar is written where the news rules read it, the speed-ups touch only the research store and give the same features, a rerun week starts clean, and a run's switch change never touches `.env`. The bot's guard test that only `ig/`, the Telegram sender and the Finnhub fetcher may make web requests (`tests/technical/test_ig_connection.py`) now also allows `research/news_history.py`, under the same check as the Finnhub fetcher: it must use the Finnhub address setting and never hold IG's address.

**To repeat** (at `nice -n 19`):

```
.venv/bin/python -m research.replay_store --bake --out data/research/replay_stores/main/GBPUSD
.venv/bin/python -m research.long_replay run --store data/research/replay_stores/main/GBPUSD \
    --calendar data/research/news/finnhub_calendar.json --from 2024-02-18T21:00:00Z --to 2026-11-07 \
    --out data/research/replay/long_20261110 --jobs 2 [--set STOP_LOSS_PIPS=12]
.venv/bin/python -m research.long_report RUN_FOLDER data/research/replay_stores/main/GBPUSD
.venv/bin/python -m research.long_report compare RUN_A RUN_B NAME_A NAME_B
```

## Appendix: every strategy by month (6-pip stop)

#### slow grind

| Month | Trades | Won | Lost | Won % | Pips | Biggest loss | Worst losing run |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2024-02 | 16 | 6 | 10 | 38% | **-55.9** | -15.0 | 3 |
| 2024-03 | 47 | 20 | 27 | 43% | **-37.2** | -15.0 | 4 |
| 2024-04 | 46 | 23 | 23 | 50% | **-25.5** | -15.0 | 5 |
| 2024-05 | 49 | 25 | 24 | 51% | **-47.8** | -15.0 | 3 |
| 2024-06 | 43 | 16 | 27 | 37% | **-153.4** | -15.2 | 4 |
| 2024-07 | 47 | 15 | 30 | 32% | **-110.2** | -15.0 | 5 |
| 2024-08 | 44 | 27 | 17 | 61% | **+116.5** | -15.0 | 2 |
| 2024-09 | 59 | 31 | 28 | 53% | **+102.9** | -15.0 | 4 |
| 2024-10 | 56 | 23 | 33 | 41% | **-114.4** | -15.0 | 9 |
| 2024-11 | 49 | 28 | 21 | 57% | **+153.3** | -15.0 | 4 |
| 2024-12 | 58 | 23 | 35 | 40% | **-220.0** | -15.0 | 5 |
| 2025-01 | 59 | 35 | 24 | 59% | **+127.1** | -15.0 | 3 |
| 2025-02 | 49 | 21 | 28 | 43% | **-84.9** | -15.0 | 6 |
| 2025-03 | 56 | 26 | 30 | 46% | **-68.5** | -15.0 | 5 |
| 2025-04 | 69 | 36 | 33 | 52% | **-28.5** | -15.0 | 4 |
| 2025-05 | 58 | 27 | 31 | 47% | **-59.0** | -15.0 | 7 |
| 2025-06 | 57 | 26 | 31 | 46% | **-113.4** | -15.0 | 5 |
| 2025-07 | 73 | 36 | 37 | 49% | **-4.9** | -15.0 | 5 |
| 2025-08 | 48 | 24 | 24 | 50% | **-22.2** | -15.0 | 3 |
| 2025-09 | 49 | 28 | 21 | 57% | **+93.0** | -15.0 | 6 |
| 2025-10 | 48 | 24 | 24 | 50% | **-38.1** | -15.0 | 4 |
| 2025-11 | 54 | 20 | 33 | 37% | **-246.6** | -15.0 | 8 |
| 2025-12 | 45 | 22 | 23 | 49% | **-91.7** | -15.0 | 3 |
| 2026-01 | 52 | 24 | 28 | 46% | **-102.0** | -15.0 | 9 |
| 2026-02 | 47 | 23 | 24 | 49% | **-65.0** | -15.0 | 6 |
| 2026-03 | 22 | 7 | 15 | 32% | **-88.5** | -15.0 | 4 |
| 2026-04 | 44 | 24 | 20 | 55% | **+16.5** | -15.0 | 5 |
| 2026-05 | 40 | 13 | 27 | 32% | **-100.2** | -15.0 | 10 |
| 2026-06 | 51 | 29 | 22 | 57% | **+173.6** | -15.0 | 4 |
| 2026-07 | 47 | 26 | 21 | 55% | **+86.0** | -15.0 | 5 |
| 2026-08 | 33 | 12 | 21 | 36% | **-144.0** | -15.0 | 4 |
| 2026-09 | 50 | 21 | 29 | 42% | **-100.2** | -15.0 | 10 |
| 2026-10 | 41 | 23 | 17 | 56% | **+87.9** | -15.0 | 6 |
| 2026-11 | 8 | 4 | 4 | 50% | **+102.9** | -15.0 | 2 |

#### EMA pullback

| Month | Trades | Won | Lost | Won % | Pips | Biggest loss | Worst losing run |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2024-02 | 24 | 5 | 19 | 21% | **-87.2** | -21.2 | 8 |
| 2024-03 | 66 | 17 | 49 | 26% | **-101.3** | -19.6 | 22 |
| 2024-04 | 76 | 20 | 56 | 26% | **-7.4** | -17.4 | 13 |
| 2024-05 | 76 | 21 | 55 | 28% | **+365.4** | -25.6 | 20 |
| 2024-06 | 58 | 14 | 44 | 24% | **-130.8** | -14.9 | 12 |
| 2024-07 | 75 | 24 | 51 | 32% | **+790.5** | -12.0 | 11 |
| 2024-08 | 122 | 29 | 93 | 24% | **+102.9** | -19.3 | 30 |
| 2024-09 | 80 | 25 | 55 | 31% | **+78.1** | -17.3 | 11 |
| 2024-10 | 97 | 15 | 82 | 15% | **-534.0** | -12.0 | 39 |
| 2024-11 | 106 | 36 | 70 | 34% | **+518.6** | -16.0 | 22 |
| 2024-12 | 77 | 18 | 59 | 23% | **-114.1** | -20.6 | 16 |
| 2025-01 | 99 | 23 | 76 | 23% | **+109.5** | -12.0 | 18 |
| 2025-02 | 87 | 21 | 65 | 24% | **-84.8** | -14.4 | 18 |
| 2025-03 | 108 | 13 | 95 | 12% | **-758.7** | -20.5 | 43 |
| 2025-04 | 167 | 45 | 122 | 27% | **+259.6** | -12.4 | 24 |
| 2025-05 | 95 | 18 | 77 | 19% | **-320.0** | -14.4 | 24 |
| 2025-06 | 107 | 19 | 88 | 18% | **-475.1** | -14.7 | 20 |
| 2025-07 | 96 | 20 | 76 | 21% | **-235.8** | -15.2 | 17 |
| 2025-08 | 103 | 29 | 74 | 28% | **+205.8** | -24.2 | 15 |
| 2025-09 | 96 | 18 | 78 | 19% | **-273.0** | -20.6 | 31 |
| 2025-10 | 117 | 15 | 102 | 13% | **-680.1** | -16.2 | 34 |
| 2025-11 | 98 | 11 | 87 | 11% | **-663.8** | -12.0 | 35 |
| 2025-12 | 75 | 19 | 56 | 25% | **-52.0** | -20.9 | 20 |
| 2026-01 | 98 | 27 | 71 | 28% | **-29.9** | -15.3 | 16 |
| 2026-02 | 72 | 13 | 59 | 18% | **-39.0** | -13.0 | 12 |
| 2026-03 | 30 | 0 | 30 | 0% | **-360.2** | -12.2 | 30 |
| 2026-04 | 123 | 26 | 97 | 21% | **-107.3** | -17.5 | 37 |
| 2026-05 | 72 | 16 | 55 | 22% | **-189.2** | -12.0 | 21 |
| 2026-06 | 92 | 14 | 78 | 15% | **+12.7** | -15.2 | 20 |
| 2026-07 | 60 | 15 | 45 | 25% | **+352.6** | -13.3 | 14 |
| 2026-08 | 60 | 10 | 50 | 17% | **-261.0** | -14.0 | 19 |
| 2026-09 | 69 | 5 | 64 | 7% | **-558.7** | -16.8 | 26 |
| 2026-10 | 91 | 26 | 65 | 29% | **-70.2** | -12.0 | 14 |
| 2026-11 | 42 | 19 | 23 | 45% | **+596.4** | -12.0 | 9 |

#### Bollinger bounce

| Month | Trades | Won | Lost | Won % | Pips | Biggest loss | Worst losing run |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2024-02 | 38 | 13 | 25 | 34% | **-62.5** | -6.0 | 5 |
| 2024-03 | 69 | 19 | 50 | 28% | **-12.1** | -6.0 | 8 |
| 2024-04 | 59 | 13 | 45 | 22% | **-74.1** | -6.2 | 6 |
| 2024-05 | 79 | 19 | 60 | 24% | **-130.5** | -6.0 | 11 |
| 2024-06 | 76 | 22 | 54 | 29% | **-101.1** | -6.0 | 16 |
| 2024-07 | 62 | 22 | 40 | 35% | **-6.0** | -6.0 | 11 |
| 2024-08 | 87 | 22 | 64 | 25% | **-24.5** | -6.0 | 13 |
| 2024-09 | 84 | 22 | 62 | 26% | **-15.1** | -6.0 | 8 |
| 2024-10 | 95 | 26 | 69 | 27% | **-141.3** | -6.0 | 11 |
| 2024-11 | 100 | 25 | 75 | 25% | **-64.1** | -6.0 | 13 |
| 2024-12 | 103 | 29 | 73 | 28% | **-52.5** | -6.0 | 12 |
| 2025-01 | 91 | 22 | 69 | 24% | **-102.3** | -6.0 | 14 |
| 2025-02 | 111 | 26 | 85 | 23% | **-284.7** | -6.1 | 14 |
| 2025-03 | 120 | 25 | 95 | 21% | **-122.5** | -6.0 | 16 |
| 2025-04 | 98 | 18 | 80 | 18% | **-186.4** | -6.0 | 14 |
| 2025-05 | 106 | 29 | 77 | 27% | **-66.9** | -6.0 | 14 |
| 2025-06 | 100 | 23 | 77 | 23% | **+26.8** | -6.0 | 11 |
| 2025-07 | 101 | 27 | 74 | 27% | **-69.3** | -6.0 | 20 |
| 2025-08 | 82 | 27 | 55 | 33% | **-61.3** | -6.0 | 7 |
| 2025-09 | 78 | 23 | 55 | 29% | **-103.5** | -6.0 | 13 |
| 2025-10 | 91 | 22 | 69 | 24% | **-154.1** | -6.6 | 13 |
| 2025-11 | 76 | 19 | 55 | 25% | **-68.2** | -6.2 | 8 |
| 2025-12 | 77 | 22 | 55 | 29% | **-71.7** | -6.0 | 11 |
| 2026-01 | 62 | 17 | 45 | 27% | **+72.0** | -6.0 | 12 |
| 2026-02 | 72 | 24 | 48 | 33% | **+136.5** | -6.0 | 8 |
| 2026-03 | 43 | 3 | 40 | 7% | **-184.3** | -6.0 | 31 |
| 2026-04 | 95 | 14 | 81 | 15% | **-374.3** | -8.7 | 19 |
| 2026-05 | 90 | 25 | 65 | 28% | **-195.4** | -6.0 | 14 |
| 2026-06 | 90 | 25 | 65 | 28% | **-132.6** | -6.0 | 9 |
| 2026-07 | 91 | 23 | 68 | 25% | **-29.9** | -6.0 | 10 |
| 2026-08 | 70 | 11 | 59 | 16% | **-223.9** | -6.1 | 14 |
| 2026-09 | 75 | 16 | 59 | 21% | **-122.7** | -6.0 | 13 |
| 2026-10 | 76 | 22 | 54 | 29% | **-91.6** | -6.0 | 13 |
| 2026-11 | 14 | 3 | 11 | 21% | **-36.3** | -6.0 | 9 |

#### range trade

| Month | Trades | Won | Lost | Won % | Pips | Biggest loss | Worst losing run |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2024-02 | 2 | 2 | 0 | 100% | **+9.9** | +1.0 | 0 |
| 2024-03 | 8 | 4 | 4 | 50% | **+9.5** | -6.0 | 3 |
| 2024-04 | 8 | 2 | 6 | 25% | **-14.0** | -6.0 | 4 |
| 2024-05 | 7 | 1 | 6 | 14% | **-26.2** | -6.0 | 5 |
| 2024-06 | 6 | 2 | 4 | 33% | **-3.4** | -4.2 | 4 |
| 2024-07 | 8 | 3 | 5 | 38% | **+1.4** | -6.0 | 4 |
| 2024-08 | 3 | 1 | 2 | 33% | **-9.6** | -6.0 | 2 |
| 2024-09 | 4 | 1 | 3 | 25% | **-2.4** | -6.0 | 2 |
| 2024-10 | 4 | 2 | 2 | 50% | **+16.0** | -6.0 | 1 |
| 2024-11 | 8 | 3 | 5 | 38% | **-17.1** | -6.0 | 4 |
| 2024-12 | 5 | 2 | 3 | 40% | **+19.8** | -6.0 | 2 |
| 2025-01 | 2 | 1 | 1 | 50% | **-3.4** | -6.0 | 1 |
| 2025-02 | 4 | 2 | 2 | 50% | **+3.0** | -6.0 | 2 |
| 2025-03 | 5 | 2 | 3 | 40% | **+5.3** | -6.0 | 2 |
| 2025-04 | 2 | 2 | 0 | 100% | **+29.6** | +12.5 | 0 |
| 2025-05 | 6 | 2 | 4 | 33% | **-4.4** | -6.0 | 2 |
| 2025-06 | 10 | 3 | 7 | 30% | **-13.4** | -6.0 | 4 |
| 2025-07 | 9 | 2 | 7 | 22% | **-20.5** | -6.0 | 4 |
| 2025-08 | 17 | 4 | 13 | 24% | **-54.3** | -6.0 | 6 |
| 2025-09 | 8 | 4 | 4 | 50% | **-6.7** | -6.0 | 4 |
| 2025-10 | 3 | 2 | 1 | 67% | **+18.7** | -3.0 | 1 |
| 2025-11 | 5 | 1 | 4 | 20% | **-17.3** | -6.0 | 3 |
| 2025-12 | 4 | 1 | 3 | 25% | **+8.2** | -3.3 | 2 |
| 2026-01 | 8 | 2 | 6 | 25% | **-19.9** | -6.0 | 6 |
| 2026-02 | 6 | 1 | 5 | 17% | **-18.0** | -6.0 | 3 |
| 2026-04 | 12 | 6 | 6 | 50% | **-13.1** | -6.0 | 3 |
| 2026-05 | 1 | 1 | 0 | 100% | **+6.3** | +6.3 | 0 |
| 2026-06 | 10 | 4 | 6 | 40% | **+11.7** | -6.0 | 5 |
| 2026-07 | 11 | 3 | 8 | 27% | **-13.1** | -6.0 | 6 |
| 2026-08 | 13 | 4 | 9 | 31% | **-27.0** | -6.0 | 4 |
| 2026-09 | 11 | 4 | 7 | 36% | **-0.5** | -6.0 | 4 |
| 2026-10 | 5 | 1 | 4 | 20% | **-20.1** | -6.0 | 4 |
| 2026-11 | 5 | 4 | 1 | 80% | **+17.2** | -2.3 | 1 |

#### breakout

| Month | Trades | Won | Lost | Won % | Pips | Biggest loss | Worst losing run |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2024-02 | 12 | 1 | 11 | 8% | **-87.1** | -17.1 | 9 |
| 2024-03 | 26 | 6 | 20 | 23% | **-7.4** | -25.7 | 11 |
| 2024-04 | 21 | 4 | 17 | 19% | **-4.0** | -12.0 | 10 |
| 2024-05 | 26 | 2 | 24 | 8% | **-235.2** | -12.0 | 11 |
| 2024-06 | 21 | 6 | 15 | 29% | **+30.7** | -12.0 | 6 |
| 2024-07 | 26 | 8 | 18 | 31% | **+99.6** | -15.8 | 5 |
| 2024-08 | 22 | 5 | 17 | 23% | **+66.8** | -12.0 | 9 |
| 2024-09 | 22 | 8 | 14 | 36% | **+188.8** | -17.7 | 4 |
| 2024-10 | 27 | 4 | 23 | 15% | **-112.6** | -17.7 | 15 |
| 2024-11 | 29 | 6 | 23 | 21% | **-12.0** | -12.4 | 8 |
| 2024-12 | 27 | 4 | 23 | 15% | **-125.6** | -12.0 | 11 |
| 2025-01 | 32 | 9 | 23 | 28% | **+134.0** | -12.0 | 10 |
| 2025-02 | 19 | 3 | 16 | 16% | **-34.6** | -12.0 | 8 |
| 2025-03 | 26 | 3 | 23 | 12% | **-139.8** | -12.0 | 15 |
| 2025-04 | 24 | 7 | 17 | 29% | **+106.8** | -12.0 | 10 |
| 2025-05 | 27 | 4 | 23 | 15% | **-114.6** | -17.5 | 15 |
| 2025-06 | 26 | 6 | 20 | 23% | **+11.1** | -12.0 | 6 |
| 2025-07 | 29 | 6 | 23 | 21% | **-4.0** | -13.6 | 9 |
| 2025-08 | 18 | 2 | 16 | 11% | **-80.1** | -12.0 | 10 |
| 2025-09 | 25 | 4 | 21 | 16% | **-72.9** | -15.3 | 13 |
| 2025-10 | 18 | 3 | 15 | 17% | **-50.4** | -19.1 | 9 |
| 2025-11 | 22 | 4 | 18 | 18% | **-16.0** | -12.0 | 8 |
| 2025-12 | 28 | 4 | 24 | 14% | **-138.6** | -14.8 | 21 |
| 2026-01 | 25 | 2 | 23 | 8% | **-172.6** | -14.1 | 14 |
| 2026-02 | 21 | 3 | 18 | 14% | **-78.2** | -12.0 | 10 |
| 2026-03 | 3 | 1 | 2 | 33% | **-6.5** | -12.0 | 2 |
| 2026-04 | 21 | 6 | 15 | 29% | **+119.1** | -12.9 | 9 |
| 2026-05 | 18 | 5 | 13 | 28% | **+28.4** | -12.0 | 5 |
| 2026-06 | 22 | 1 | 21 | 5% | **-205.9** | -15.9 | 11 |
| 2026-07 | 19 | 7 | 12 | 37% | **+116.1** | -12.2 | 4 |
| 2026-08 | 20 | 5 | 15 | 25% | **+31.4** | -12.0 | 6 |
| 2026-09 | 27 | 4 | 23 | 15% | **-100.5** | -15.6 | 14 |
| 2026-10 | 26 | 6 | 20 | 23% | **-75.7** | -12.2 | 7 |
| 2026-11 | 7 | 2 | 5 | 29% | **-6.2** | -12.0 | 5 |

#### level reversal

| Month | Trades | Won | Lost | Won % | Pips | Biggest loss | Worst losing run |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2024-02 | 25 | 11 | 14 | 44% | **-22.3** | -23.8 | 6 |
| 2024-03 | 43 | 20 | 23 | 47% | **+0.8** | -29.5 | 5 |
| 2024-04 | 42 | 21 | 21 | 50% | **+64.6** | -27.2 | 5 |
| 2024-05 | 36 | 18 | 17 | 50% | **+11.4** | -29.4 | 4 |
| 2024-06 | 36 | 18 | 18 | 50% | **+70.4** | -22.9 | 3 |
| 2024-07 | 39 | 23 | 16 | 59% | **+57.7** | -33.0 | 3 |
| 2024-08 | 69 | 23 | 46 | 33% | **-429.0** | -74.8 | 8 |
| 2024-09 | 49 | 25 | 24 | 51% | **-45.0** | -40.3 | 6 |
| 2024-10 | 55 | 27 | 28 | 49% | **+39.9** | -24.2 | 9 |
| 2024-11 | 55 | 28 | 27 | 51% | **-57.1** | -37.9 | 3 |
| 2024-12 | 47 | 22 | 25 | 47% | **-57.3** | -31.5 | 3 |
| 2025-01 | 68 | 37 | 31 | 54% | **+110.4** | -41.7 | 5 |
| 2025-02 | 51 | 21 | 30 | 41% | **-106.3** | -64.8 | 6 |
| 2025-03 | 47 | 23 | 24 | 49% | **-35.5** | -34.5 | 5 |
| 2025-04 | 65 | 36 | 29 | 55% | **+108.1** | -43.4 | 4 |
| 2025-05 | 55 | 26 | 28 | 47% | **+71.4** | -36.4 | 6 |
| 2025-06 | 45 | 25 | 20 | 56% | **+97.8** | -28.4 | 2 |
| 2025-07 | 58 | 25 | 33 | 43% | **-110.7** | -26.3 | 8 |
| 2025-08 | 52 | 18 | 34 | 35% | **-267.2** | -31.0 | 9 |
| 2025-09 | 43 | 20 | 23 | 47% | **-8.6** | -42.9 | 6 |
| 2025-10 | 52 | 28 | 24 | 54% | **+102.7** | -29.6 | 7 |
| 2025-11 | 43 | 24 | 19 | 56% | **+133.8** | -22.8 | 4 |
| 2025-12 | 49 | 17 | 32 | 35% | **-121.4** | -26.4 | 10 |
| 2026-01 | 53 | 22 | 31 | 42% | **-103.7** | -58.6 | 6 |
| 2026-02 | 50 | 25 | 25 | 50% | **+10.8** | -39.1 | 4 |
| 2026-03 | 20 | 9 | 11 | 45% | **-78.1** | -44.5 | 7 |
| 2026-04 | 49 | 18 | 31 | 37% | **-156.0** | -24.6 | 7 |
| 2026-05 | 44 | 17 | 27 | 39% | **-84.8** | -41.5 | 8 |
| 2026-06 | 44 | 23 | 21 | 52% | **+134.3** | -24.0 | 3 |
| 2026-07 | 33 | 15 | 17 | 45% | **+43.9** | -20.8 | 4 |
| 2026-08 | 37 | 15 | 22 | 41% | **-91.1** | -25.9 | 10 |
| 2026-09 | 39 | 14 | 25 | 36% | **-139.4** | -28.6 | 8 |
| 2026-10 | 45 | 14 | 30 | 31% | **-171.1** | -23.1 | 9 |
| 2026-11 | 10 | 7 | 3 | 70% | **+80.9** | -17.4 | 1 |
