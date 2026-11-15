# The hourly band pierce rule: 118 complete weekdays, 23 March to 6 November 2026

**Status: research only. Nothing in the bot or on AutoBot 161 was changed (161's archive was only read, from the copy in `data/research/`). Waiting for the owner.**

## In short

**Every version loses money over the 118 days.** There are 36 versions: 4 readings of "reverses", 3 exits and 3 choices of hours.

- **Least bad:** reading D (price trades back past the pierce candle's far end on the next candle, entering at that moment), with fixed 12 and 07:00–19:00 UK. That made 285 trades, won 48.4% and lost **108.0 pips**.
- **Worst:** reading A with fixed 20 and no hours limit, at −676.0.
- **Normal days on their own come out about even at best:**
  - D with fixed 12, 07:00–19:00: +36.0 on 267 trades;
  - A with the trail, 07:00–19:00: +15.9;
  - D with the trail, 07:00–19:00: +10.6.

  None of these is a clear edge.
- **Trend days lose in almost every version.** By the 80-pip rule there are 4 trend days in the 118. On them a pierce of the band is usually the move carrying on, not a turn.
- **Limiting the hours helps:** no limit is the worst in every reading and exit. 07:00–19:00 beats the bot's own 06:00–20:30 in 10 of the 12 reading-and-exit pairs. The exceptions are reading C with fixed 12 (−264.0 against −252.0) and with the trail (−166.1 against −153.6).
- **Fixed 20 is the worst exit in every case.** A 20-pip target needs 37.5% wins to break even against a 12-pip stop, and it won only about a third of the time.
- **By month, every version swings with no steady edge.** In the 07:00–19:00 versions, June and October lose every time; September and the spring months are positive in most.

## The rule, as given (owner, 15 November 2026)

1. Price pierces the hourly Bollinger band (20, 2) by more than 3 pips: above the upper band for a sell, below the lower band for a buy.
2. The next bar on the 5-minute chart reverses.
3. 12-pip stop.

### How the rule was read

- **"Pierces by more than 3 pips":** a 5-minute candle's high (sell price) is more than 3 pips above the upper hourly band, or its low more than 3 pips below the lower band.
  - The band is the live one, as on the chart: the last 19 finished hourly sell closes plus the candle's close. This is the same as in the earlier hourly band tests.
  - That candle is the pierce candle, and "the next bar" is the 5-minute candle after it.

### The options tested, where the rule doesn't say

- **What "reverses" means, and where the trade opens:**
  - **A.** The next candle closes against the push (a red candle after an upper pierce). Entry at the open of the candle after it.
  - **B.** The next candle closes beyond the pierce candle's far end (below its low after an upper pierce). Entry at the open of the candle after it.
  - **C.** *(Claude's suggestion)* The next candle closes back inside the band. Entry at the open of the candle after it.
  - **D.** *(Claude's suggestion)* The next candle trades past the pierce candle's far end. Entry at that moment, at the pierce candle's low for a sell, or the next candle's open if it opened already past it.
    - Inside the entry candle, only its close is used after the entry, because the order of its prices is unknown.
  - For A, B and C, entering at the reversal candle's close is the same as entering at the next open on 5-minute data, so it was not run separately.
- **The exit:**
  - **Fixed 12:** a take profit 12 pips from the entry.
  - **Fixed 20:** a take profit 20 pips from the entry.
  - **Trail:** once the trade is 12 pips in profit, the stop follows the last 3 candles: for a sell, 0.1 above their highest buy price; for a buy, 0.1 below their lowest sell price.
  - The stop is always 12 pips from the entry until the trail moves it. A stop and a target in the same candle count as the stop.
- **Hours, judged at the pierce candle's start (UK):**
  - no limit;
  - the bot's own trading hours, 06:00–20:30;
  - 07:00–19:00, as in the earlier tests.

### Carried over from the earlier tests, not in the rule

- **Trades at a time:** one trade at a time in each direction.
- **Overnight:** no end-of-day close. In the 07:00–19:00 versions, 7 to 21 trades were held overnight.
- **Costs, as in the 11-day test, nothing added:**
  - sells open at the sell price and close at the buy price;
  - buys open at the buy price and close at the sell price;
  - the stop is checked on the closing price.

## The data

- **Days:** the 118 complete weekdays from 23 March to 6 November 2026 in AutoBot 161's archive. These are the weekdays with every 5-minute candle from 07:00 to 19:00 UK.
- **Price:** the archive holds IG's own **mid** price for this period, which matches the bot's IG mid exactly where both exist. Sell and buy prices are the earlier rebuild: mid minus and plus half IG's typical spread for that half hour of the week (`data/research/candles_ig161_2026/`). The rebuilt sell price is within 0.3 pips of IG's on 90% of prices, and a "within 3 pips of the hourly band" test gives the same answer as IG's 97% of the time (`data/research/archive_fitness_20261115/`). Wider spreads around news are not charged.
- **Missing data:** a signal is skipped if the pierce candle, the next candle or the entry candle is missing, or if the band's 20-hour window has any missing time.
  - For "no limit" and 06:00–20:30, the hours outside 07:00–19:00 are used only where the archive has them.
  - 2 to 6 trades per version stayed open across a later stretch of missing data.
- **Trend day (owner's rule):** the 17:00 UK close is at least 80 pips above or below the 07:00 UK open, on the sell price. Every other day is a normal day. Of the 118 days, 4 are trend days:
  - 23 March (+111.3);
  - 15 July (+86.3);
  - 30 July (+110.0);
  - 14 October (−118.5).

## Results: every version

Trades / win rate / pips.

| Reverses (entry) | Hours | Exit | All: trades / win rate / pips | Normal days | Trend days |
|---|---|---|---|---|---|
| A. closes against the push | none | fixed 12 | 379 / 43.5% / -588.0 | 352 / 45.2% / -408.0 | 27 / 22.2% / -180.0 |
| A. closes against the push | none | fixed 20 | 331 / 31.1% / -676.0 | 308 / 32.5% / -496.0 | 23 / 13.0% / -180.0 |
| A. closes against the push | none | trail | 343 / 42.6% / -452.0 | 319 / 44.5% / -273.8 | 24 / 16.7% / -178.2 |
| A. closes against the push | 06:00-20:30 | fixed 12 | 341 / 45.5% / -372.0 | 315 / 47.6% / -180.0 | 26 / 19.2% / -192.0 |
| A. closes against the push | 06:00-20:30 | fixed 20 | 294 / 32.3% / -488.0 | 272 / 34.2% / -288.0 | 22 / 9.1% / -200.0 |
| A. closes against the push | 06:00-20:30 | trail | 309 / 44.3% / -256.0 | 286 / 46.9% / -72.0 | 23 / 13.0% / -184.0 |
| A. closes against the push | 07:00-19:00 | fixed 12 | 314 / 46.2% / -288.0 | 290 / 48.6% / -96.0 | 24 / 16.7% / -192.0 |
| A. closes against the push | 07:00-19:00 | fixed 20 | 271 / 32.8% / -404.0 | 250 / 35.2% / -184.0 | 21 / 4.8% / -220.0 |
| A. closes against the push | 07:00-19:00 | trail | 284 / 44.7% / -177.9 | 262 / 47.7% / +15.9 | 22 / 9.1% / -193.8 |
| B. closes beyond the pierce candle's far end | none | fixed 12 | 278 / 43.5% / -432.0 | 265 / 43.8% / -396.0 | 13 / 38.5% / -36.0 |
| B. closes beyond the pierce candle's far end | none | fixed 20 | 260 / 31.9% / -464.0 | 250 / 32.0% / -440.0 | 10 / 30.0% / -24.0 |
| B. closes beyond the pierce candle's far end | none | trail | 257 / 42.8% / -300.0 | 247 / 42.9% / -271.4 | 10 / 40.0% / -28.6 |
| B. closes beyond the pierce candle's far end | 06:00-20:30 | fixed 12 | 254 / 45.3% / -288.0 | 242 / 45.9% / -240.0 | 12 / 33.3% / -48.0 |
| B. closes beyond the pierce candle's far end | 06:00-20:30 | fixed 20 | 236 / 33.1% / -336.0 | 227 / 33.5% / -292.0 | 9 / 22.2% / -44.0 |
| B. closes beyond the pierce candle's far end | 06:00-20:30 | trail | 234 / 44.9% / -169.7 | 225 / 45.3% / -135.3 | 9 / 33.3% / -34.4 |
| B. closes beyond the pierce candle's far end | 07:00-19:00 | fixed 12 | 234 / 46.2% / -216.0 | 224 / 46.9% / -168.0 | 10 / 30.0% / -48.0 |
| B. closes beyond the pierce candle's far end | 07:00-19:00 | fixed 20 | 217 / 33.2% / -300.0 | 209 / 34.0% / -236.0 | 8 / 12.5% / -64.0 |
| B. closes beyond the pierce candle's far end | 07:00-19:00 | trail | 215 / 45.6% / -87.3 | 207 / 46.4% / -45.8 | 8 / 25.0% / -41.5 |
| C. closes back inside the band | none | fixed 12 | 254 / 41.7% / -504.0 | 247 / 41.3% / -516.0 | 7 / 57.1% / +12.0 |
| C. closes back inside the band | none | fixed 20 | 243 / 30.0% / -580.0 | 236 / 29.7% / -592.0 | 7 / 42.9% / +12.0 |
| C. closes back inside the band | none | trail | 247 / 41.3% / -419.2 | 240 / 40.8% / -414.6 | 7 / 57.1% / -4.6 |
| C. closes back inside the band | 06:00-20:30 | fixed 12 | 223 / 45.3% / -252.0 | 217 / 45.2% / -252.0 | 6 / 50.0% / +0.0 |
| C. closes back inside the band | 06:00-20:30 | fixed 20 | 212 / 32.5% / -336.0 | 206 / 32.5% / -328.0 | 6 / 33.3% / -8.0 |
| C. closes back inside the band | 06:00-20:30 | trail | 216 / 44.9% / -153.6 | 210 / 44.8% / -143.2 | 6 / 50.0% / -10.4 |
| C. closes back inside the band | 07:00-19:00 | fixed 12 | 208 / 44.7% / -264.0 | 203 / 44.8% / -252.0 | 5 / 40.0% / -12.0 |
| C. closes back inside the band | 07:00-19:00 | fixed 20 | 198 / 32.3% / -328.0 | 193 / 32.1% / -332.0 | 5 / 40.0% / +4.0 |
| C. closes back inside the band | 07:00-19:00 | trail | 203 / 43.8% / -166.1 | 198 / 43.9% / -147.7 | 5 / 40.0% / -18.4 |
| D. trades past the pierce candle's far end (entry at that moment) | none | fixed 12 | 341 / 45.5% / -372.0 | 321 / 46.7% / -252.0 | 20 / 25.0% / -120.0 |
| D. trades past the pierce candle's far end (entry at that moment) | none | fixed 20 | 297 / 32.3% / -492.0 | 279 / 33.3% / -372.0 | 18 / 16.7% / -120.0 |
| D. trades past the pierce candle's far end (entry at that moment) | none | trail | 320 / 43.8% / -388.2 | 301 / 44.9% / -259.1 | 19 / 26.3% / -129.1 |
| D. trades past the pierce candle's far end (entry at that moment) | 06:00-20:30 | fixed 12 | 307 / 47.9% / -156.0 | 288 / 49.7% / -24.0 | 19 / 21.1% / -132.0 |
| D. trades past the pierce candle's far end (entry at that moment) | 06:00-20:30 | fixed 20 | 263 / 33.8% / -308.0 | 246 / 35.4% / -168.0 | 17 / 11.8% / -140.0 |
| D. trades past the pierce candle's far end (entry at that moment) | 06:00-20:30 | trail | 287 / 46.0% / -201.5 | 269 / 47.6% / -64.7 | 18 / 22.2% / -136.8 |
| D. trades past the pierce candle's far end (entry at that moment) | 07:00-19:00 | fixed 12 | 285 / 48.4% / -108.0 | 267 / 50.6% / +36.0 | 18 / 16.7% / -144.0 |
| D. trades past the pierce candle's far end (entry at that moment) | 07:00-19:00 | fixed 20 | 242 / 33.9% / -280.0 | 226 / 35.8% / -120.0 | 16 / 6.2% / -160.0 |
| D. trades past the pierce candle's far end (entry at that moment) | 07:00-19:00 | trail | 266 / 46.6% / -133.4 | 249 / 48.6% / +10.6 | 17 / 17.6% / -144.0 |

## Month by month (07:00–19:00 UK)

Months are by the pierce candle's day. Every version, every hours choice and every month is in `hourly_pierce_20261115_by_month.csv`.

**fixed 12, 07:00–19:00 UK** (trades / win rate / pips)

| Month | A | B | C | D |
|---|---|---|---|---|
| 2026-03 | 14 / 50.0% / +0.0 | 9 / 55.6% / +12.0 | 11 / 54.5% / +12.0 | 13 / 53.8% / +12.0 |
| 2026-04 | 13 / 46.2% / -12.0 | 7 / 71.4% / +36.0 | 6 / 66.7% / +24.0 | 12 / 50.0% / +0.0 |
| 2026-05 | 34 / 50.0% / +0.0 | 26 / 61.5% / +72.0 | 23 / 52.2% / +12.0 | 30 / 56.7% / +48.0 |
| 2026-06 | 64 / 37.5% / -192.0 | 51 / 31.4% / -228.0 | 46 / 34.8% / -168.0 | 62 / 45.2% / -72.0 |
| 2026-07 | 49 / 40.8% / -108.0 | 31 / 48.4% / -12.0 | 28 / 39.3% / -72.0 | 43 / 44.2% / -60.0 |
| 2026-08 | 51 / 47.1% / -36.0 | 42 / 40.5% / -96.0 | 32 / 43.8% / -48.0 | 44 / 52.3% / +24.0 |
| 2026-09 | 38 / 63.2% / +120.0 | 32 / 53.1% / +24.0 | 31 / 51.6% / +12.0 | 37 / 54.1% / +36.0 |
| 2026-10 | 51 / 45.1% / -60.0 | 36 / 47.2% / -24.0 | 31 / 45.2% / -36.0 | 44 / 40.9% / -96.0 |
| 2026-11 | 0 | 0 | 0 | 0 |

**fixed 20, 07:00–19:00 UK** (trades / win rate / pips)

| Month | A | B | C | D |
|---|---|---|---|---|
| 2026-03 | 12 / 41.7% / +16.0 | 9 / 44.4% / +20.0 | 9 / 44.4% / +20.0 | 12 / 41.7% / +16.0 |
| 2026-04 | 11 / 45.5% / +28.0 | 6 / 66.7% / +56.0 | 5 / 60.0% / +36.0 | 8 / 50.0% / +32.0 |
| 2026-05 | 33 / 39.4% / +20.0 | 22 / 40.9% / +24.0 | 21 / 33.3% / -28.0 | 26 / 46.2% / +72.0 |
| 2026-06 | 49 / 24.5% / -204.0 | 47 / 17.0% / -308.0 | 45 / 24.4% / -188.0 | 51 / 23.5% / -228.0 |
| 2026-07 | 43 / 18.6% / -260.0 | 29 / 27.6% / -92.0 | 27 / 33.3% / -36.0 | 37 / 24.3% / -156.0 |
| 2026-08 | 42 / 33.3% / -56.0 | 39 / 33.3% / -52.0 | 31 / 29.0% / -84.0 | 35 / 37.1% / -4.0 |
| 2026-09 | 36 / 47.2% / +112.0 | 32 / 46.9% / +96.0 | 31 / 41.9% / +44.0 | 34 / 47.1% / +104.0 |
| 2026-10 | 45 / 33.3% / -60.0 | 33 / 33.3% / -44.0 | 29 / 27.6% / -92.0 | 39 / 28.2% / -116.0 |
| 2026-11 | 0 | 0 | 0 | 0 |

**trail, 07:00–19:00 UK** (trades / win rate / pips)

| Month | A | B | C | D |
|---|---|---|---|---|
| 2026-03 | 12 / 58.3% / +39.1 | 9 / 55.6% / +19.4 | 9 / 55.6% / +35.8 | 11 / 54.5% / +31.7 |
| 2026-04 | 11 / 45.5% / -16.6 | 6 / 66.7% / +12.1 | 6 / 66.7% / +6.8 | 10 / 50.0% / -21.6 |
| 2026-05 | 28 / 50.0% / +0.4 | 20 / 60.0% / +73.5 | 21 / 52.4% / +1.1 | 26 / 53.8% / +34.9 |
| 2026-06 | 58 / 36.2% / -92.4 | 47 / 31.9% / -136.8 | 46 / 32.6% / -109.0 | 59 / 42.4% / -64.5 |
| 2026-07 | 46 / 39.1% / -100.5 | 30 / 46.7% / -20.8 | 27 / 37.0% / -47.0 | 42 / 42.9% / -55.8 |
| 2026-08 | 46 / 45.7% / -47.1 | 39 / 43.6% / -62.8 | 32 / 43.8% / -31.8 | 41 / 51.2% / +4.0 |
| 2026-09 | 37 / 62.2% / +76.7 | 30 / 53.3% / +28.4 | 31 / 51.6% / +1.7 | 35 / 54.3% / +6.7 |
| 2026-10 | 46 / 39.1% / -37.5 | 34 / 44.1% / -0.3 | 31 / 45.2% / -23.7 | 42 / 38.1% / -68.8 |
| 2026-11 | 0 | 0 | 0 | 0 |

## How much to trust this

- **The sample:** 118 days on IG's own mid with a rebuilt typical spread. None of these days was used to shape the rule.
- **Limits:**
  - the typical spread understates costs around news;
  - about 1 candle in 70 gets a different wick answer from IG's sell chart;
  - a stop and a target in the same candle count as the stop;
  - for D, the entry candle's own prices after the entry are not known.

  None is large enough to turn these totals positive.
- **Small differences between versions are noise.** With 200 to 380 trades per version, a few dozen pips separate them.

## Files

- `hourly_pierce_20261115_by_month.csv` (next to this write-up): every version by month.
- `data/research/hourly_pierce_20261115/` (not in git):
  - `pierce.py`: the test;
  - `data.py`: the shared data loader, as in the archive test;
  - `pierce.txt` and `result.json`: the output, with every trade of every version;
  - `tables.md`: the tables above.
