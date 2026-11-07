# Market analyser

Stage 7 is built in parts. **Part 1 (built):** the indicators, the direction rule, and whether the data is ready, warming up or out of date. **Part 2 (built):** the five market states, checked against Johnny's chart for 5 and 6 November and fixed into functional tests (`tests/functional/test_market_states_real_candles.py`). Known shortfall: the S2 flat spell from 11:30 to 12:45 on 6 November is not yet called consolidation (design section 12).

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

**Now:** since the long history fill on 7 November 2026 the store holds IG's hourly candles from 7 August 2026, so every indicator on both timeframes is ready and the analyser reports **ready** (for example at 16:00 on Friday 6 November: 1,587 hourly candles). Before that fill the hourly 100 and 200 EMAs were warming up.

## Direction rule (design section 2.3)

- **Buy side:** price above the daily pivot **and** above the 5-minute 100 EMA.
- **Sell side:** price below the daily pivot **and** below the 5-minute 100 EMA.
- **No clear direction:** otherwise (they disagree, price is exactly on one, or there is no pivot or EMA yet).

Price is the live sell price when there is one. With stored candles (a replay or a test), it is the close of the latest finished 5-minute candle: at 13:00, the 12:55 candle's close. The EMA is the one at that candle. The pivot is today's daily pivot from the levels part (`docs/LEVELS.md`). It applies to every strategy, including bounces in a possible reversal.

## Checking a time against the chart

```
.venv/bin/python -m analyser 2026-11-06T13:00:00Z [more UTC times ...] [--pair GBPUSD]
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

## The five market states (Stage 7, part 2)

Code: `analyser/features.py` (what each state looks at, per 5-minute candle), `analyser/states.py` (the state machine), `analyser/market_state.py` (the start-up replay, the live steps and the records). Sell price, 5-minute candles. **Every number is a setting** (`[market_states]`, listed in `docs/SETTINGS.md` with where each came from: AutoBot 161's NMS, the design, or a new starting value).

Each result gives the state, the direction (up, down or none), the type of trend (slow grind or strong push, for a trend), when the state started, and the evidence, plus the strategies it allows (design section 2.2).

| State | How the analyser recognises it |
| --- | --- |
| **Consolidation** | Bands narrow: **14 pips or less, or narrowing for 6 candles in a row** (owner's rule, 7 November 2026), and flat (middle band under 0.5 pips a candle over 6); **no candle closed outside the bands for 6 candles** (owner's rule); average body at most 3 pips; green and red bodies within 2 times of each other. Also the state at each week's open ("watch and wait"), and where a trend ends with no range. |
| **Ranging** | Design 2.2 exactly (owner's values, 7 November 2026): bands 8 to 10 pips apart (close together), the upper and the lower band each moving less than 0.5 pips a candle over 6 candles (flat), both bands reached within 24 candles (price bounces between them), the 7/13/21 EMAs changing order within 12 (weaving), the 100 EMA moving under 3 pips over 12 (flat). |
| **Emerging trend** | Started at once by: a level rejection (the shared rejection part confirms a bounce rejection at a **strong level**: the pivot, R1 to R3, S1 to S3, a round number 00 or 50, the previous day's high or low, or a turning level that lines up with one of those; `market_states.strong_level_types`, owner's rule, 7 November 2026; a turning level on its own does not), a close beyond a band out of consolidation, or 2 closes beyond the same band out of a range, or a possible reversal being confirmed. |
| **Trend** | An emerging trend becomes a trend at the moment of the proof in section 2.5: a bounce failed at or under the 21 EMA and middle band, then price makes a new extreme on the outer band, with the 7/13/21 EMAs stacked for 3 candles, price beyond them and the 100 EMA, and the outer band sloping. **Strong push** when, over 6 candles, 70% of the total candle body size is in the trend's colour (by size, not by count: owner's rule, 7 November 2026), the bands are at least 1.5 times as wide as 12 candles before, the 7 and 21 EMAs are at least 6 pips apart and at least 3 closes are on the band; otherwise **slow grind**. |
| **Possible reversal** | In an emerging trend or trend that has moved at least 30 pips since it started, **and** the shared rejection part confirms a rejection at a level against it (a single opposite candle, or a rejection at the band only, is not enough; owner's rule, 7 November 2026). Section 2.6's signs (MACD still showing the move, RSI, the time of day, a level) are recorded as evidence; none is waited for. When that rejection triggers, it becomes an emerging trend the new way. |

**How it moves on** (sections 2.5 to 2.7). What price *did* on a candle acts at once: a level rejection, a breakout, the trend proof, a confirmed level rejection after a 30-pip move (possible reversal), the old trend making a new extreme or the reversal setup being cancelled or expiring (back to the trend), the reversal triggering (emerging trend the new way).

**An emerging trend is replaced** by an emerging trend the other way when the shared rejection part confirms a rejection at a **strong level** (as above) in the opposite direction (owner's rule, 7 November 2026). A rejection at the band only, at a turning level on its own, or at another level (such as a session high or low) does not replace it. Turning levels still count everywhere else: in the rejection part, and for a possible reversal (which needs a confirmed rejection at any level after a 30-pip move).

**An emerging trend is cancelled only** (owner's rule, 7 November 2026; it replaced 161's 3-pip cancel): if it started from a **rejection at a level**, by **2 closes in a row back beyond that level** (the important level nearest the piercing candle's edge); if it started from a **breakout**, by **2 closes in a row back inside the Bollinger bands**. The 100 EMA and ranging do not end an emerging trend. Besides its cancel rule it ends only by becoming a trend, a possible reversal, being replaced by an opposite rejection at an important level, settling into **consolidation** (its checks held for 2 candles in a row; owner's rule, 7 November 2026), or fading.

Anything that depends on a **condition** needs it for **2 candles in a row** (flip-flop protection): ranging, consolidation, a trend ending with 2 closes back past the 100 EMA, a change of trend type. **Evidence fades:** an emerging trend, trend or possible reversal with nothing new for 24 candles (2 hours) ends (design section 2.7).

**Start-up replay.** The machine starts fresh at each week's open (Sunday 21:00 UK), and its indicators always start 2,000 candles before that open. So on start-up it replays the week from the open and reaches exactly the state, and the same list of changes, as a run that never stopped. A technical test checks this three ways (replayed, never stopped, stopped part-way and started again).

**Records.** Each change is recorded with its time (the 5-minute candle it was decided on), state, direction, type of trend, one-line reason and evidence, in `data/analyser/<PAIR>/state_changes.jsonl`, once each even after a restart; the current state is in `current.json`. The price service runs the market states for each pair switched on (`StatesUpdater`): at start-up it replays the week from its open, then it takes each new 5-minute candle; each change is recorded and written to the price service's log (`[GBPUSD] Market state: ...`). A problem with the states is warned about and never stops the price service.

**Timeline.** `.venv/bin/python -m analyser.states_timeline <from UTC> <to UTC> [--pair GBPUSD]` replays the week and prints every change in between. With `--measure`, it shows instead, for every 5-minute candle, the consolidation checks (band width, how long the bands have narrowed, middle-band slope, average body, green and red counts, when a candle last closed outside the bands) and which failed by how much; `--push` the strong-push checks with each candle's rejection events and the move since the trend started; `--events` every rejection event in full. Contacts nobody; writes nothing.

**This week (2 to 6 November) with the strong-level rule:** 220 state changes (130 inside trading hours, 90 outside); median length 20 minutes; 70 lasted under 15 minutes, 116 from 15 to 60 minutes, 34 over an hour. Many short consolidation and emerging-trend spells: a known issue to check in the no-trading run (design section 12).

