# The hourly band reversal on AutoBot 161's archive: 118 complete weekdays, 23 March to 6 November 2026

**Status: research only. Nothing in the bot or on AutoBot 161 was changed (161's archive was only read, from the copy in `data/research/`). Waiting for the owner.**

## In short

**On the archive the signal loses.** With the trail it made 286 trades, won 45.8% and lost **188.8 pips**. With a fixed 12-pip target it made 291 trades, won 47.1% and lost **204.0 pips**. The 11-day test made +130.9 and +96.0 with the same rules.

- **Normal days (114):** −73.5 with the trail, −96.0 with fixed 12.
- **Trend days (4):** −115.3 and −108.0, from only 13 trades. Only 1 of the 13 won with the trail.
- **Only September was clearly positive** (+118.2 with the trail). Every other month was negative or about flat: June made +5.9, and the two November days gave no trades. July's normal days made +62.7, but its two trend days lost 96.0.

The rules were frozen exactly as found. Nothing was retuned.

## The data

- **Which part of the archive.** The owner chose the 118 complete weekdays (owner, 15 November 2026). These are the weekdays from 23 March to 6 November 2026 with every 5-minute candle from 07:00 to 19:00 UK. That part of the archive is IG's own prices, which the data check (`data/research/archive_fitness_20261115/`) found trustworthy. The 2024–2025 part is a vendor's prices whose wicks don't match IG's well enough, so it was not used. So were January and February 2026 (not IG's exact prices) and 1–22 March 2026 (missing).
- **The price it uses.** 161's archive for this period holds IG's **mid** price: (IG's buy + IG's sell) / 2, from IG's own 5-minute candles. It matches the bot's own IG mid exactly where both exist. The sell and buy prices used here are the earlier research rebuild (`data/research/candles_ig161_2026/`):
  - sell = mid − half IG's typical spread for that half hour of the week;
  - buy = mid + half that spread.

  The typical spread comes from the bot's own IG prices. IG's chart and the bot use the sell price.
- **Costs, as in the 11-day test, nothing added.** As in the 11-day test:
  - sells open at the sell price and close at the buy price;
  - buys open at the buy price and close at the sell price;
  - the stop is checked on the price the trade closes at.

  The one difference is the spread. The 11-day test used IG's real buy and sell prices from the bot's candles. Here the spread is IG's *typical* spread for that half hour, so wider spreads around news are not charged.
- **How close the rebuilt sell price is to IG's** (data check, 25 Oct–6 Nov 2026):
  - 90% of prices are within 0.3 pips of IG's.
  - The "2+ pip wick" test gives the same answer as IG's sell chart on 98.7% of candles.
  - The "within 3 pips of the hourly band" test gives the same answer 97% of the time.
- **Missing data.** A signal was skipped if any 5-minute candle of its hour-long lookback or the 2 after was missing. It was also skipped if the hourly band's 20-hour window had any missing time (owner, 15 November 2026). That removed 104 of 532 signals. More than half of them (58) were on Mondays: the archive often lacks IG's first hour on Sunday, 21:00 to 22:00 UK, which falls inside Monday morning's band window. Of the trades taken, 3 (trail) and 2 (fixed 12) were still open across a later stretch of missing data. Together they came to −0.5 and 0.0 pips.

## The rules, frozen exactly as found

From `docs/research/hourly_band_reversal_20261115.md`. The code is the 11-day test's own `p3.py`, unchanged apart from taking its data as arguments (`data/research/hourly_band_archive_20261115/frozen.py`). Run on the 11-day data, the port reproduces that test exactly: within 3 pips, 32 trades, +96.0 with fixed 12 and +130.9 with the trail.

- **The push:** candle 1's high (sell) is above the previous 11 candles' highs, or its low (buy) below their lows: a new 1-hour high or low.
- **The rejection:** candle 1 or candle 2 has a wick of 2 pips or more, and candle 2 closes against the push. Entry is at candle 3's open.
- **At the hourly band:** price is within 3 pips of the hourly Bollinger band (20, 2), sells at the upper band and buys at the lower. The band is the live one, as on the chart: the last 19 finished hourly sell closes plus the candle's close. It is judged on the higher of candles 1 and 2.
- **Hours and limits:**
  - candle 1 starts between 07:00 and 19:00 UK;
  - one trade at a time in each direction;
  - a 12-pip stop.
- **Two details carried over unchanged from the 11-day code, not given by the owner:**
  - a candle 1 whose spread is over 3 pips is skipped;
  - candles with a spread over 3 pips use their open and close in place of their high and low.

  With the rebuilt typical spread neither ever applies between 07:00 and 19:00.
- **Exits:**
  - **Trail:** once the trade is 12 pips in profit, the stop follows the last 3 candles: for a sell, 0.1 pips above their highest buy price; for a buy, 0.1 pips below their lowest sell price.
  - **Fixed 12:** a take profit 12 pips from the entry.
  - A stop and a target in the same 5-minute candle count as the stop.
  - There is no end-of-day close, as in the 11-day test. 7 trades with the trail and 5 with fixed 12 were held overnight. None was still open at the end of the data.
- **Trend day (owner's rule):** the 17:00 UK close is at least 80 pips above or below the 07:00 UK open, on the sell price. Every other day is a normal day. Of the 118 days, 4 are trend days:
  - 23 March (+111.3);
  - 15 July (+86.3);
  - 30 July (+110.0);
  - 14 October (−118.5).

## Results

### Totals

| | Trail behind the last 3 candles | | | Fixed 12 | | |
|---|---:|---:|---:|---:|---:|---:|
| | Trades | Win rate | Pips | Trades | Win rate | Pips |
| **All 118 days** | 286 | 45.8% | **−188.8** | 291 | 47.1% | **−204.0** |
| Normal days (114) | 273 | 47.6% | −73.5 | 278 | 48.6% | −96.0 |
| Trend days (4) | 13 | 7.7% | −115.3 | 13 | 15.4% | −108.0 |
| *11-day test, for comparison (25 Oct–13 Nov 2026)* | *32* | *59%* | *+130.9* | *32* | *63%* | *+96.0* |

The two exits trade slightly different counts (286 and 291) because one trade at a time in each direction depends on when the previous trade ended.

### Month by month

Days are the complete weekdays in that month. Months are by the day of candle 1.

**Trail**

| Month | Days (trend) | All: trades / win rate / pips | Normal days | Trend days |
|---|---|---|---|---|
| Mar (23–31) | 5 (1) | 13 / 38.5% / −34.7 | 13 / 38.5% / −34.7 | 0 |
| Apr | 10 (0) | 13 / 46.2% / −3.4 | 13 / 46.2% / −3.4 | — |
| May | 11 (0) | 29 / 41.4% / −75.2 | 29 / 41.4% / −75.2 | — |
| Jun | 19 (0) | 63 / 46.0% / +5.9 | 63 / 46.0% / +5.9 | — |
| Jul | 15 (2) | 35 / 42.9% / −33.3 | 27 / 55.6% / +62.7 | 8 / 0% / −96.0 |
| Aug | 21 (0) | 50 / 48.0% / −75.3 | 50 / 48.0% / −75.3 | — |
| Sep | 18 (0) | 38 / 65.8% / **+118.2** | 38 / 65.8% / +118.2 | — |
| Oct | 17 (1) | 45 / 33.3% / −91.0 | 40 / 35.0% / −71.7 | 5 / 20.0% / −19.3 |
| Nov (1–6) | 2 (0) | 0 | 0 | — |

**Fixed 12**

| Month | Days (trend) | All: trades / win rate / pips | Normal days | Trend days |
|---|---|---|---|---|
| Mar (23–31) | 5 (1) | 13 / 38.5% / −36.0 | 13 / 38.5% / −36.0 | 0 |
| Apr | 10 (0) | 13 / 46.2% / −12.0 | 13 / 46.2% / −12.0 | — |
| May | 11 (0) | 29 / 41.4% / −60.0 | 29 / 41.4% / −60.0 | — |
| Jun | 19 (0) | 66 / 47.0% / −48.0 | 66 / 47.0% / −48.0 | — |
| Jul | 15 (2) | 36 / 44.4% / −48.0 | 28 / 57.1% / +48.0 | 8 / 0% / −96.0 |
| Aug | 21 (0) | 50 / 48.0% / −24.0 | 50 / 48.0% / −24.0 | — |
| Sep | 18 (0) | 39 / 64.1% / **+132.0** | 39 / 64.1% / +132.0 | — |
| Oct | 17 (1) | 45 / 40.0% / −108.0 | 40 / 40.0% / −96.0 | 5 / 40.0% / −12.0 |
| Nov (1–6) | 2 (0) | 0 | 0 | — |

## What this says

- **The 11-day result did not carry over.** With a 12-pip stop and a 12-pip target, about 50% wins is break-even before the spread. The archive gave 47–49% on normal days, against 63% in the 11 days, and with the trail about 48% against 59%.
- **Trend days are where it does worst, but they are rare by the 80-pip rule:** 4 of 118 days. On those days a reversal at the band is usually a pause in the move. All 8 trades on 15 and 30 July lost.
- **On normal days it swings by month** from −75 to +118, with no steady edge. Excluding trend days doesn't make it profitable: −73.5 with the trail.
- **How much to trust this.** The prices are IG's own mid, with a rebuilt typical spread, on 118 complete days: about ten times the 11-day sample, and none of these days was used to pick the rules. The main limits:
  - the typical spread understates costs around news;
  - about 1 candle in 70 gets a different wick answer from IG's sell chart;
  - a stop and a target in the same candle count as the stop.

  None of these is large enough to turn −189 into a profit.

## Files

- `hourly_band_archive_20261115_trades.csv` (next to this write-up): every trade under both exits. Columns: exit, day, day type, side, entry and exit (UK), pips, how it closed, and whether it crossed missing data.
- `data/research/hourly_band_archive_20261115/` (not in git):
  - `frozen.py`: the frozen rules;
  - `validate.py`: reproduces the 11-day test;
  - `run.py` and `run.txt`: this test;
  - `result.json`: every trade, the day types and the monthly figures;
  - `skipped.py`: the signals removed for missing data, and the trade list.
- The data check: `data/research/archive_fitness_20261115/`.
