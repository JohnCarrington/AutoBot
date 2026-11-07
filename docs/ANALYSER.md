# Market analyser

Stage 7 is built in parts. **Part 1 (built):** the indicators, the direction rule, and whether the data is ready, warming up or out of date. The five market states (design section 2.2) come in later parts.

The analyser reads the candle store and the levels only. It never contacts IG (a test checks that `analyser/` never imports the IG connection). Everything uses the chart price, the **sell (bid) price**, with daily candles midnight to midnight UK, as on Johnny's IG chart. Only candles that had **finished** at the time asked about are used, so the answer for a past time never changes.

## Indicators (design section 2.8)

Worked out on the 5-minute and hourly candles (`indicators.timeframes`), from the last 2000 stored candles up to the time asked about (`indicators.history_candles`). The code is in `prices/indicators.py`; `analyser/indicators.py` gathers them for each timeframe.

| Indicator | Settings | How it is worked out |
| --- | --- | --- |
| EMAs | 7, 13, 21, 100, 200 | Starts as the simple average of the first closes; then each value = previous + (close - previous) x 2 / (periods + 1). |
| Bollinger bands | 20, 2 | Middle = average of the last 20 closes; upper and lower = middle ± 2 standard deviations (population). As in Stage 6. |
| MACD | 35, 45, 30 | MACD line = EMA 35 - EMA 45; signal = EMA 30 of the MACD line; histogram = MACD line - signal. |
| RSI | 3, lines 70 and 30 | Wilder's smoothing (the usual RSI), from close-to-close changes. 100 with no losses, 50 when flat. |

IG does not publish exactly how its chart starts an EMA or smooths the RSI. These are the usual ways. Once warmed up (below), how an EMA was started makes no visible difference, so the values should match the chart. **The RSI smoothing is still to be checked against Johnny's chart.**

## Ready, warming up, out of date (design section 2.1)

- **Warming up:** an EMA, the MACD or the RSI starts from a guess, and every later candle shrinks the guess's share of the value. An indicator counts as ready once the guess counts for no more than 2% (`indicators.warm_up_seed_weight_percent`). That takes: EMA 7: 21 candles; 13: 39; 21: 63; 100: 296; 200: 592; MACD 35/45/30: 134; RSI 3: 14; Bollinger 20: 20.
- **Out of date:** while the market is open, the newest stored candle on the 5-minute or hourly timeframe is more than 10 minutes (`analyser.out_of_date_after_minutes`) behind the newest one that should have finished. While the market is shut (the weekend), the data is judged against the last candle before the close, so a weekend is not out of date. Out of date is checked first.
- **Ready:** neither. Only then may new trades be allowed (open trades are always managed).

**Now:** the store starts on Sunday 25 October 2026, so the 5-minute indicators are all ready, but the **hourly 100 and 200 EMAs are warming up** (about 235 hourly candles by Friday 6 November; they need 296 and 592). With the price service running, the hourly 100 EMA becomes ready in about the second week of November and the hourly 200 EMA at the end of November, unless more hourly history is filled through the history door. Until then the analyser reports "warming up" and the hourly 100 and 200 EMA values are not yet the chart's.

## Direction rule (design section 2.3)

- **Buy side:** price above the daily pivot **and** above the 5-minute 100 EMA.
- **Sell side:** price below the daily pivot **and** below the 5-minute 100 EMA.
- **No clear direction:** otherwise (they disagree, price is exactly on one, or there is no pivot or EMA yet).

Price is the live sell price when there is one. With stored candles (a replay or a test), it is the close of the latest finished 5-minute candle: at 13:00, the 12:55 candle's close. The EMA is the one at that candle. The pivot is today's daily pivot from the levels part (`docs/LEVELS.md`). It applies to every strategy, including bounces in a possible reversal.

## Checking a time against the chart

```
.venv/bin/python -m analyser 2026-11-06T13:00:00Z [more UTC times ...]
```

Prints the direction and why, the data status, and every indicator on the 5-minute and hourly candles (`*` marks one still warming up). Contacts nobody.

## Functional tests (`tests/functional/test_analyser_real_candles.py`)

- **a.** At 13:00 on Friday 6 November the direction is sell side (no buy at 13:00).
- **b.** The 5-minute 100 EMA, the pivot and the direction at 06:00, 09:00, 13:00 and 16:00 on Friday 6 November, printed for checking against the chart:

| UK time | Price | 5m 100 EMA | Daily pivot | Direction |
| --- | --- | --- | --- | --- |
| 06:00 | 13424.9 (05:55 close) | 13441.4 | 13463.8 | sell side |
| 09:00 | 13392.9 (08:55 close) | 13423.4 | 13463.8 | sell side |
| 13:00 | 13388.2 (12:55 close) | 13405.2 | 13463.8 | sell side |
| 16:00 | 13358.4 (15:55 close) | 13385.4 | 13463.8 | sell side |

The pivot is 13463.8 from the stored candles; Johnny's chart shows 13463.4 for this day (the difference is still to be explained, `docs/LEVELS.md`). It does not change any direction here.
