# Rejections

How AutoBot decides that price has been rejected at a level or at a Bollinger band. The agreed design is in `docs/DESIGN.md`, sections 3.3 (Bollinger band bounce), 3.4 (range trade), 4 (trade management: the reversal watch times) and 5 (levels). Every rule below is checked by a test (listed at the end).

There is **one** rejection part (`rejection/`), shared by the analyser, the strategies and the trade manager, so all three read the same answer. It **never contacts IG** and **never places, changes or closes a trade**. Every number comes from `config/settings.toml`.

## The basics

- **Every price is the sell (bid) price**, as on Johnny's IG chart (`chart.price`), with daily candles running midnight to midnight UK. Trades still open and close at IG's real buy or sell price; that is not this part's job.
- It watches **5-minute candles** (`rejection.candle_timeframe`).
- Each step is reported as a **separate, timestamped event**: pierce, reversal candle, confirmation candle, trigger, and cancelled or expired. A step found from a finished candle carries that candle's start time. A trigger or cancel found from a live price carries the exact moment and price.
- Rules are written for a **sell** (price pushed up into a level or the upper band, then turned down). A **buy** is the mirror image: price pushed down, green candles instead of red, lows and highs swapped.
- Red means the candle closed below where it opened; green means it closed above. A candle that closes where it opened is neither.

## The Bollinger band

- **20 candles, 2 standard deviations**, on the sell close, as on Johnny's chart (`indicators.bollinger_periods`, `indicators.bollinger_std_devs`).
- The middle band is the average of the last 20 closes, this candle's included. The upper and lower bands are 2 standard deviations above and below it. The standard deviation divides by 20 (the usual way charts draw it).
- Candles are taken in order as on the chart: the weekend is simply skipped. Until there are 20 candles there is no band.
- The code is in `prices/indicators.py`, so the analyser and strategies can use the same band.

## What counts as a pierce

- **The Bollinger band needs a real pierce:** for a sell, the candle's high is above the upper band (for a buy, its low is below the lower band). Coming close does not count.
- **A level counts when the candle reaches it:** for a sell, the candle opens at or below the level, and its high either goes through it or **comes within 3 pips** of it (`rejection.near_level_within_pips`). For a buy, the candle opens at or above the level, and its low goes through it or comes within 3 pips of it. Each event says how close it came: "through", "touched", or "within 2.3 pips".
- The levels are the current list from the levels part (`docs/LEVELS.md`), **as it stood at the start of the candle**. Every kind of level counts.
- One candle can reach several things at once (the band and several levels). They all go into the same setup.

## Version 1: the bounce (design 3.3)

1. **Pierce:** a candle pierces the upper band or reaches a level (above).
2. **Reversal candle:** the first red candle after the pierce, **within 3 candles** of it (`bounce.reversal_candle_within_candles_of_pierce`). There is no size rule. If none comes, the setup **expires**.
   - If another candle pierces again (and is not red) while waiting, it becomes the piercing candle and the 3-candle count starts again.
3. **Confirmation candle:** a later candle that **closes** below the reversal candle's low, **within 3 candles** of the reversal candle (`bounce.confirmation_candle_within_candles_of_reversal`). A wick below without a close does not count. If none comes, the setup **expires**.
4. **Trigger:** the live price goes below the confirmation candle's low. There is no time limit for this.
5. **Cancelled:** if price goes above the reversal candle's high at any point after the reversal candle.

## Version 2: the quicker range-trade version (design 3.4)

1. **Pierce:** a candle pierces the upper Bollinger band. Levels play no part in this version.
2. **Rejection candle:** the very next candle is red (`range_trade.rejection_candle_within_candles`, 1). Otherwise the setup **expires**.
3. **Trigger:** during the candle after that (`range_trade.trigger_within_candles`, 1), the live price goes below the rejection candle's low. Otherwise the setup **expires** at that candle's close.
4. **Cancelled:** if price goes above the rejection candle's high first.

## One setup at a time

- For each version and each direction, only one setup runs at a time. A new setup can start once the last one has triggered, been cancelled or expired, including on the same candle that ended it.
- So at any moment there can be up to four running: bounce sell, bounce buy, range sell, range buy.

## Spread spikes are ignored

- IG's spread is normally 0.9 or 1.5 points. At the 22:00 rollover and around news it jumps (up to 26 points in the stored candles). On the sell price that shows up as false dips: for example 22:25 GMT on 5 November, and 12:00 that day.
- **When IG's spread on a candle is over 3 pips** (`rejection.max_spread_pips`), that candle's highs and lows **cannot start a setup** (a first pierce, or a pierce that starts the count again) **and cannot cancel one**. An "ignored" event records what was ignored and the spread. The candle's other steps carry on as normal (it can still be a reversal or confirmation candle, trigger a setup, or count towards an expiry). The candle is still stored as normal.
- A candle's spread is the widest of its four buy-minus-sell gaps (open, high, low, close).
- Live, a price that comes with a spread over the limit cannot cancel a setup either.
- **Why 3 pips (a starting value, for Johnny to confirm).** In the 2,880 stored 5-minute candles (25 October to 6 November):
  - 1,294 had a spread of 0.9 and 1,204 of 1.5. These are the normal values.
  - 184 (6.4%) were over 3. Of those, 158 were between 21:00 and 23:59 UK (the rollover). The other 26 were all at news times: 12:25–12:30, 13:25–13:30, 14:55–15:00, 17:55–18:00 and 20:55.
  - The few between 1.6 and 3.0 were mostly the tail of the rollover (22:00 to 01:00). They move the sell price by 1.5 pips or less, which is under the 3-pip level rule.
  - The limit sits where it is not delicate: moving it from 3 to 4 would change only 6 candles.

## The reversal watch windows

- From the settings: 10:00, 11:00, 13:00, 14:00, 16:00 and 17:00 UK (`reversal_watch.times`), each from 20 minutes before (`reversal_watch.minutes_before`) to 20 minutes after (`reversal_watch.minutes_after`), both ends included. UK clock time, so the windows move with BST.
- **Inside a window, any level counts. Outside, only levels where several line up** (a group of more than one, `docs/LEVELS.md`). A Bollinger band pierce always counts.
- This is worked out from the piercing candle's start time, and **only sets a `counts` mark** on the setup. The setup always runs and every event is reported: the rejection part never filters. The trade manager reads the mark.

## What is recorded for every setup

- Its version and direction; every event.
- What was pierced (the band and its value, each level, and how close the candle came).
- **Which levels lined up:** for each level reached, its group and every level in it, and whether more than one lines up.
- Whether the piercing candle was in a reversal watch window, and whether the setup counts.
- **How big the reversal candle was compared with the piercing candle:** the body (open to close) and the high-to-low size of each, and the two ratios. Never used to filter.
- Its status: running, triggered, cancelled or expired.

## With stored candles instead of live prices

- Checking a past day (and the functional tests) uses the stored 5-minute candles, which have no ticks inside them. A trigger or cancel is then found from the next candles' highs and lows, and is shown at the start of the candle it happened in.
- If one candle goes both past the trigger price and past the cancel price, the order inside it is unknown. It counts as a trigger only if it opened past the trigger price; otherwise it counts as cancelled.
- Live, the watcher gets every price (`RejectionWatcher.on_price`) and triggers or cancels at the exact moment.

## Commands (contact nobody)

- `.venv/bin/python -m rejection 2026-11-05T21:00:00Z 2026-11-06T00:30:00Z [--pair GBPUSD]` lists every event between two UTC times from the stored candles, then a summary of every setup.
- The live price service does not run the rejection part yet; the analyser and strategies will.

## Checked against real days (5 November 2026, sell prices)

**a. The rejection at the daily pivot around midnight** (design 2.5 and 12):
- Thursday's pivot was 13468.0. The sell price never came within 3 pips of it before midnight: the highest was 13462.3 at 23:25.
- Just after midnight, Friday's pivot (13463.8; 13463.4 on Johnny's chart) was reached: within 2.3 pips at 00:00 and 0.5 pips at 00:05. A red reversal candle followed at 00:10 (low 13459.8), a close below it at 00:15 (13458.0, low 13457.0), and the **trigger at 00:20** (below 13457.0). The pivot's group also held a turning low at 13468.2.
- Before midnight, the only completed sell rejection was the range version at the upper band: pierce at 23:25, rejection candle at 23:30, trigger at 23:35 below 13454.5.

**b. The turn at 1.3446 to 1.3450 around 12:00** (design 5 and 12):
- 11:45 pierce: low 13448.8, through the lower band (13451.5) and reaching 13447.2, 13448.0, 13450, 13450.1 and others, which line up.
- 11:50 green reversal candle (low 13446.8).
- The range version triggered at 11:55 (above 13450.8).
- 12:00: IG's spread jumped to 13.5 points, dipping the sell price to 13445.2. That would have cancelled the bounce, but it is ignored. The same candle closed at 13473.2, above the reversal high: the confirmation.
- **Trigger at 12:20**, above 13481.3.

## Tests

| File | What it checks |
|---|---|
| `tests/technical/test_rejection.py` | Made-up candles. The Bollinger band (20, 2, population, sell closes). The watch windows from the settings, in UK time, both ends included, summer and winter. The bounce step by step with each event's time and price; the first red candle with no size rule; the 3-candle limits and their settings; a new pierce starts the count again; a wick does not confirm; cancelling while waiting for confirmation or trigger; a candle going both ways; the buy mirror image; live triggers and cancels at the exact moment. Levels reached through or within 3 pips, from below only, the setting, the buy side; the band needs a real pierce. Lined-up levels recorded; counts inside a window or when levels line up; nothing is filtered; sizes recorded. The range version: pierce, next candle, the candle after, expiry, cancel, band only, its settings. Spread spikes: the limit, no start, no pierce again, no cancel while other steps go on, live too. Sell prices only. No IG. |
| `tests/functional/test_rejection_real_candles.py` | The real candles of 5 November: a sell rejection at the daily pivot between 22:00 and 00:30 that triggers; a buy rejection from 1.3446 to 1.3450 that triggers between 11:45 and 12:15. Every event is printed with its time and price. |
