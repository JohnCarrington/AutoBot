# Levels

How AutoBot works out the price levels it watches, and how levels that line up are grouped. The agreed design is in `docs/DESIGN.md`, section 5. Every rule below is checked by a test (listed at the end).

The levels part (`levels/`) reads only the candle store. **It never contacts IG.** It never places, changes or closes a trade, and never decides whether a trade should be taken: it only supplies levels.

## The basics

- **Every level uses the BUY price** (IG's offer, `OFR`): the buy high, buy low and buy close of the stored candles. This matches Johnny's IG chart. The sell price is never used for levels.
- **Prices are in IG's points**, exactly as stored: `13450` means 1.3450. One pip (0.0001) is one point (`market.points_per_pip`). Every distance in pips in the settings is turned into points this way.
- Levels are worked out **as they stood at a given time**, using only candles that had finished by then. A candle still in progress is never used.
- "Today" is the daily candle that the time falls in: midnight to midnight UK, like IG's chart (`docs/PRICES_AND_CANDLES.md`).

## 1. Daily pivots

From the **previous day's daily candle** in the store, using its buy high (H), buy low (L) and buy close (C):

| Level | Formula |
|---|---|
| Pivot (P) | (H + L + C) / 3 |
| R1 | 2 × P − L |
| S1 | 2 × P − H |
| R2 | P + (H − L) |
| S2 | P − (H − L) |
| R3 | H + 2 × (P − L) |
| S3 | L − 2 × (H − P) |

- These are the classic daily pivot formulas. They are worked out exactly, then written to 1 decimal place of a point (`levels.level_decimals`), rounding halves up. IG shows GBPUSD to 1 decimal place of a point.
- **The previous day** is the last daily candle before today in which the market was open:
  - **Monday's pivots come from the short Sunday daily candle** (labelled Sunday 00:00, holding Sunday 21:00 to midnight), exactly as IG's chart does.
  - Sunday's (after the 21:00 open) come from Friday's.
  - Saturday has no market, so it is skipped.
- If the previous day's candle **is not stored yet**, there are no pivots and no previous day high or low, and a warning says so. (The daily candle is built just after midnight, before the levels are updated.)
- If the previous day's candle is missing some 5-minute candles, it is still used as stored, and a warning says how many are missing.

## 2. Other levels

### Round numbers

- Every price ending in **00 or 50** pips: 1.3400, 1.3450, 1.3500 ... (multiples of `levels.round_number_every_pips`, 50 pips).
- Only those within **150 pips** above or below the latest buy close are listed (`levels.round_numbers_within_pips`, both ends included). The latest buy close is the close of the newest finished 5-minute candle.

### The previous day's high and low

- The buy high and buy low of the same previous daily candle the pivots use. So Monday's are the Sunday candle's, like the pivots.

### London and New York session highs and lows

- **London: 07:00 to 12:00 UTC. New York: 12:00 to 21:00 UTC.** These are settings (`levels.london_session_from` ... `levels.new_york_session_until`). **They are in UTC, not UK time**, and are starting values from AutoBot 161 for Johnny to confirm.
- A session holds the 5-minute candles that start at or after its start and end by its end. So a candle starting at 12:00 belongs to New York, not London.
- The session's high is the highest buy high of those candles, and its low the lowest buy low.
- For each session there are two pairs of levels:
  - **today's session**: once it has started, its high and low so far, marked "so far" until it ends.
  - **the previous day's session**: the most recent earlier day that had that session (so on Monday morning, Friday's).
- The session's date is today's UK date, with the session times taken in UTC on that date.

### Turning levels

Hourly highs and lows where price clearly reversed, from the last **2 weeks** (`levels.turning_levels_lookback_weeks`). The hourly candles are taken in order as on IG's chart: the weekend is simply skipped, so Friday's last candle is next to Sunday's first.

**An hourly candle's buy high is a turning high when all three of these are true:**

1. It is **higher than the high of each of the 3 hourly candles before it** (`levels.turning_candles_each_side`).
2. It is **not lower than the high of any of the 3 hourly candles after it**. So when two candles side by side have the same high, the first one counts, once.
3. **Price then clearly moved away:** within the **6 hourly candles after it** (`levels.turning_move_within_candles`), some candle's buy low is at least **20 pips below** it (`levels.turning_min_move_pips`).

**A turning low is the same, upside down:** lower than the low of each of the 3 candles before it, not higher than the low of any of the 3 after it, and within the 6 candles after it some candle's buy high is at least 20 pips above it.

- The candle must start within the last 2 weeks. The candles before it may be older (they are only used for rule 1).
- A high or low only becomes a turning level once the 3 candles after it have finished. So a turning level appears about 3 hours after the high or low, and only once price has moved the 20 pips.
- A turning level stays on the list for the whole 2 weeks, even if price later goes through it.
- **3 candles, 20 pips and 6 candles are starting values, for Johnny to confirm.** With them, the 2 weeks up to Friday 6 November 21:00 UTC give 43 turning levels (22 highs, 21 lows). A bigger move or more candles each side gives fewer.

## 3. Levels that line up

- Levels within **5 pips** of each other line up (`levels.line_up_within_pips`). **Every kind of level can be grouped, the daily pivot included.**
- **How the groups are made:** all the levels are put in price order. Going up from the lowest, a level joins the current group if it is within 5 pips of the **lowest** level in that group; otherwise it starts a new group. So every level in a group is within 5 pips of every other, and a group is never more than 5 pips wide.
  - Example: 13450, 13454 and 13458 make two groups: 13450 with 13454, and 13458 on its own (it is 8 pips from 13450).
  - Exactly 5 pips apart lines up; 5.1 pips does not.
- Every level is in exactly one group. A level on its own is a group of one. Groups are numbered 1, 2, 3 ... from the lowest price.
- **For each group, the list records which levels are in it**, their type and price, and whether more than one level lines up there.
- **The levels that matter most are marked:** S2, R2, the daily pivot, round numbers and turning levels. A group is marked when it holds at least one of them.

## 4. The current list

- **One file: `/opt/autobot/data/levels/current.json`** (`levels.folder`), on the server only, not in git. It is written with a safe write (a new file is written, flushed and renamed in one step), so a reader never sees a half-written list.
- It holds:
  - when it was written and what time the levels are for (UTC), the price used (`buy`), the start of today's daily candle, the previous day's daily candle it used, and the latest buy close;
  - any warnings (for example, the previous day's candle not stored yet);
  - **every level**: its price (exact, as text), its type, where it came from (for example `hourly candle Wed 04 Nov 05:00 GMT low (buy)` or `daily candle Thu 05 Nov (buy H 13501.6 L 13446.8 C 13456.7)`), the time of the candle it came from, whether it is one that matters most, and its group;
  - **every group**: its number, lowest and highest price, whether it matters most, whether levels line up there, and the levels in it.
- The rest of the bot reads it with `levels.current.read_current()`.
- Level types: `pivot`, `R1` `R2` `R3`, `S1` `S2` `S3`, `round_number`, `previous_day_high`, `previous_day_low`, `london_session_high`, `london_session_low`, `new_york_session_high`, `new_york_session_low`, `turning_high`, `turning_low`.

### When it is updated

- **Each time the price service stores a new 5-minute candle** (after any bigger candles due have been built), and at its start-up. The same happens during a timed live run (`prices.run`).
- **A problem with the levels can never stop the price service.** If the list cannot be worked out or written, a warning is written and the previous list is kept.
- A levels warning (such as a missing previous day candle) is written to the log once, not every 5 minutes.
- The price service picks this up the next time it is restarted.

### Commands (contact nobody)

- `.venv/bin/python -m levels` works out the levels now, prints them by group (highest first), and writes `current.json`.
- `.venv/bin/python -m levels --at 2026-11-06T00:00:00Z` prints the levels as they stood at that UTC time. It never writes the file.

## Checked against real days

Functional tests (`tests/functional/test_levels_real_candles.py`) use the real stored candles:

- **Friday 6 November's pivots**, from Thursday 5 November's daily candle (buy H 13501.6, L 13446.8, C 13456.7): R3 13544.7, R2 13523.2, R1 13489.9, **pivot 13468.4**, S1 13435.1, S2 13413.6, S3 13380.3.
- **The hourly low at about 1.3380 around 30 October is a turning level:** 13381.1 (Fri 30 Oct 05:00 GMT), and also 13380.0 (Mon 2 Nov 02:00), in the same group as S3 13380.3 on 6 November.
- **5 November** (`docs/DESIGN.md`: "the fall from 07:00 stopped at about 1.3446 to 1.3450, a round number next to an earlier level, and price shot back up at 12:00"): the fall stopped at 11:50 GMT at buy 13448.3 (sell 13446.8). At 12:00 that low is in the same group as the round number 13450 and two earlier turning levels, 13448.7 (Wed 4 Nov 05:00) and 13448.9 (Mon 2 Nov 09:00).

## Tests

| File | What it checks |
|---|---|
| `tests/technical/test_levels.py` | Made-up candles. Pivot formulas, buy price not sell, decimals from the settings. Friday's pivots from Thursday; **Monday's from the short Sunday candle**; Sunday's from Friday; no pivots (with a warning) when the previous day is not stored; a previous day with missing candles is used with a warning. Round numbers end in 00 and 50 within the set distance, around the latest buy close. Previous day high and low. London and New York session highs and lows in UTC from the settings, 12:00 belonging to New York, today's session so far, the previous day's session. Turning levels: a clear high and low; neighbours on each side; the move and its window; equal highs counted once; the setting for candles each side; candles after must exist; the lookback; buy prices. Grouping within 5 pips, exactly 5, never wider than 5, the pivot grouped, the setting used; each group lists its levels; the levels that matter most marked. The file: every field, safe write, updated when a 5-minute candle is stored and not when nothing new is stored; a problem never stops the price service and keeps the old list; a warning written once; only finished candles used. The levels part never contacts IG. The live run and the service update the levels. |
| `tests/functional/test_levels_real_candles.py` | The real stored candles: 6 November's pivots, the turning low at about 1.3380 from 30 October, and 5 November's stop at 1.3446 to 1.3450 grouped with the round number and an earlier level. Skipped where the real candle store is not present. |
