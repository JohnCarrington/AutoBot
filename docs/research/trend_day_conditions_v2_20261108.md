# Trend-day conditions (version 2), to 6 November 2026

Read-only research on the stored GBPUSD candles, sell prices. Nothing in the bot was changed. Written 8 November 2026. It follows `docs/research/trend_day_conditions_20261108.md`.

**The idea tested:** when price is stretched a long way from the structure and the daily chart is overbought or oversold, the day tends to move a long way back.

## Method

- **Days:** 504 weekdays from Mon 02 Dec 2024 to Fri 06 Nov 2026 on the daily candles (midnight to midnight UK); 66 of them (07 Aug 2026 onwards) also have hourly candles.
- **Levels** with the bot's own classic pivot formula (`levels/rules.py`): **daily** from the previous daily candle (Monday's from IG's short Sunday candle, as the bot does); **weekly** from the previous weekly candle (stored weekly candles, Sunday to Friday, from November 2022); **monthly** from the previous UK calendar month, built from the daily candles (no monthly candles are stored), so from 01 Jan 2025 only (the first month whose previous month is complete in the store).
- **Daily Bollinger bands (20, 2)** and **daily RSI (3 and 14 periods, Wilder's)** with the bot's own indicator code (`prices/indicators.py`), up to and including the previous day's close.
- **The price tested:** the day's open (00:00 UK) on the daily candles; the 08:00 UK hourly open on the hourly candles. Measure 3 is on the hourly candles only, at 08:00 and at 10:00.
- **Measures ("stretched"):** 1. at or beyond the weekly R1/R2/R3 (up) or S1/S2/S3 (down); 2. the same with the monthly levels; 3. the same with the daily levels, at 08:00 and at 10:00; 4. above the previous day's high (below its low), above the previous week's high (below its low); 5. 50, 80 or 100+ pips above (below) the daily middle band; 6. 3, 4 or 5+ up (down) days in a row (weekday candles closing above (below) their open, ending the day before).
- **Daily-chart conditions:** 7. the previous day's high reached the upper band (its low the lower band); 8. the previous day's RSI above 70 (below 30), with 3 and with 14 periods. Each alone, and each with each measure, on the **same side** only.
- **The move back:** for the up side, from the price tested down to the lowest low after it that day (the day's low from the open; the lowest hourly low from 08:00, or from 10:00 for measure 3 at 10:00); for the down side, up to the highest high.
- **Compared with all other days, the same way round:** for a group of flagged days, the other days' moves are taken in the same directions (if 60% of the flagged days were up-side, 60% of the comparison is the other days' down move and 40% their up move). **Ranked** by how many more percentage points of the flagged days moved 80 pips than of the other days; only groups with at least 10 days (daily candles) or 5 days (hourly) are ranked.

**For scale:** the open was a median 80 pips from the daily middle band, and the band's half-width a median 154 pips, so the 50/80/100-pip distances of measure 5 are small on a daily chart (they flag 200 to 344 days). The open is next to the previous close, so it is almost never beyond the previous day's high or low (measure 4, 1 day).

**Limits:** about two years of daily candles (fewer for the monthly levels) and only three months of hourly; GBPUSD only; many groups were tested, so some will look good by chance; the furthest point in a day is not a move a trade could have caught in full.

## How many days each measure and condition flagged (from the open)

| Measure / condition | Days | Up side | Down side |
|---|---|---|---|
| 1. beyond the weekly R1/S1 | 109 | 64 | 45 |
| 1. beyond the weekly R2/S2 | 24 | 10 | 14 |
| 1. beyond the weekly R3/S3 | 6 | 2 | 4 |
| 2. beyond the monthly R1/S1 | 139 | 85 | 54 |
| 2. beyond the monthly R2/S2 | 33 | 19 | 14 |
| 2. beyond the monthly R3/S3 | 0 | 0 | 0 |
| 4. beyond the previous day's high/low | 1 | 1 | 0 |
| 4. beyond the previous week's high/low | 149 | 87 | 62 |
| 5. 50+ pips from the daily middle band | 344 | 198 | 146 |
| 5. 80+ pips from the daily middle band | 251 | 147 | 104 |
| 5. 100+ pips from the daily middle band | 200 | 119 | 81 |
| 6. 3+ up/down days in a row | 105 | 48 | 57 |
| 6. 4+ up/down days in a row | 53 | 24 | 29 |
| 6. 5+ up/down days in a row | 24 | 11 | 13 |
| 7. previous day touched the daily band | 132 | 63 | 69 |
| 8. daily RSI(3) beyond 70/30 | 254 | 144 | 110 |
| 8. daily RSI(14) beyond 70/30 | 34 | 19 | 15 |

## Ranking: from the day's open (daily candles)

| Rank | Measure / condition | Days (up/down) | 50+ | Others 50+ | 80+ | Others 80+ | 100+ | Others 100+ | 80+ difference | Median move |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2. beyond the monthly R2/S2 + 8. daily RSI(14) beyond 70/30 | 16 (9/7) | 56% | 33% | **38%** | 14% | 19% | 9% | **+24** | 64 |
| 2 | 2. beyond the monthly R2/S2 + 7. previous day touched the daily band | 14 (7/7) | 43% | 33% | **36%** | 14% | 7% | 9% | **+22** | 48 |
| 3 | 2. beyond the monthly R2/S2 + 8. daily RSI(3) beyond 70/30 | 24 (14/10) | 50% | 33% | **29%** | 13% | 12% | 9% | **+16** | 51 |
| 4 | 2. beyond the monthly R2/S2 | 33 (19/14) | 48% | 33% | **27%** | 13% | 12% | 9% | **+14** | 48 |
| 5 | 8. daily RSI(14) beyond 70/30 | 34 (19/15) | 44% | 33% | **26%** | 14% | 15% | 8% | **+13** | 46 |
| 6 | 5. 50+ pips from the daily middle band + 8. daily RSI(14) beyond 70/30 | 34 (19/15) | 44% | 33% | **26%** | 14% | 15% | 8% | **+13** | 46 |
| 7 | 5. 80+ pips from the daily middle band + 8. daily RSI(14) beyond 70/30 | 34 (19/15) | 44% | 33% | **26%** | 14% | 15% | 8% | **+13** | 46 |
| 8 | 5. 100+ pips from the daily middle band + 8. daily RSI(14) beyond 70/30 | 34 (19/15) | 44% | 33% | **26%** | 14% | 15% | 8% | **+13** | 46 |
| 9 | 4. beyond the previous week's high/low + 8. daily RSI(14) beyond 70/30 | 24 (16/8) | 38% | 33% | **25%** | 13% | 17% | 8% | **+12** | 41 |
| 10 | 1. beyond the weekly R1/S1 + 8. daily RSI(14) beyond 70/30 | 20 (13/7) | 40% | 33% | **25%** | 14% | 20% | 8% | **+11** | 42 |
| 11 | 6. 5+ up/down days in a row + 7. previous day touched the daily band | 12 (7/5) | 33% | 33% | **25%** | 14% | 8% | 9% | **+11** | 37 |
| 12 | 2. beyond the monthly R1/S1 + 8. daily RSI(14) beyond 70/30 | 29 (19/10) | 45% | 33% | **24%** | 13% | 14% | 8% | **+11** | 47 |
| 13 | 6. 3+ up/down days in a row + 8. daily RSI(14) beyond 70/30 | 13 (6/7) | 38% | 33% | **23%** | 14% | 23% | 8% | **+9** | 47 |
| 14 | 6. 4+ up/down days in a row + 7. previous day touched the daily band | 24 (11/13) | 33% | 33% | **21%** | 14% | 8% | 9% | **+7** | 40 |
| 15 | 1. beyond the weekly R1/S1 | 109 (64/45) | 39% | 32% | **19%** | 13% | 14% | 7% | **+7** | 32 |
| 16 | 7. previous day touched the daily band | 132 (63/69) | 37% | 32% | **19%** | 13% | 11% | 8% | **+6** | 34 |
| 17 | 5. 80+ pips from the daily middle band + 7. previous day touched the daily band | 108 (49/59) | 37% | 32% | **19%** | 13% | 11% | 8% | **+6** | 34 |
| 18 | 5. 50+ pips from the daily middle band + 7. previous day touched the daily band | 119 (56/63) | 37% | 32% | **18%** | 13% | 11% | 8% | **+5** | 34 |
| 19 | 1. beyond the weekly R1/S1 + 8. daily RSI(3) beyond 70/30 | 100 (59/41) | 39% | 32% | **18%** | 13% | 13% | 7% | **+5** | 32 |
| 20 | 4. beyond the previous week's high/low + 7. previous day touched the daily band | 86 (43/43) | 36% | 33% | **19%** | 14% | 12% | 8% | **+5** | 34 |
| 21 | 4. beyond the previous week's high/low | 149 (87/62) | 36% | 33% | **17%** | 13% | 11% | 8% | **+4** | 34 |
| 22 | 5. 100+ pips from the daily middle band + 7. previous day touched the daily band | 95 (45/50) | 35% | 33% | **17%** | 14% | 8% | 8% | **+3** | 34 |
| 23 | 8. daily RSI(3) beyond 70/30 | 254 (144/110) | 35% | 32% | **15%** | 13% | 10% | 7% | **+3** | 34 |
| 24 | 2. beyond the monthly R1/S1 + 8. daily RSI(3) beyond 70/30 | 81 (49/32) | 38% | 33% | **16%** | 14% | 9% | 8% | **+2** | 39 |
| 25 | 5. 100+ pips from the daily middle band + 8. daily RSI(3) beyond 70/30 | 140 (85/55) | 37% | 32% | **16%** | 13% | 10% | 8% | **+2** | 37 |
| 26 | 4. beyond the previous week's high/low + 8. daily RSI(3) beyond 70/30 | 135 (80/55) | 36% | 33% | **16%** | 13% | 10% | 8% | **+2** | 34 |
| 27 | 1. beyond the weekly R2/S2 | 24 (10/14) | 42% | 33% | **17%** | 14% | 12% | 9% | **+2** | 38 |
| 28 | 1. beyond the weekly R2/S2 + 8. daily RSI(3) beyond 70/30 | 24 (10/14) | 42% | 33% | **17%** | 14% | 12% | 9% | **+2** | 38 |
| 29 | 6. 3+ up/down days in a row + 7. previous day touched the daily band | 38 (19/19) | 26% | 33% | **16%** | 14% | 8% | 8% | **+2** | 34 |
| 30 | 5. 80+ pips from the daily middle band + 8. daily RSI(3) beyond 70/30 | 166 (101/65) | 37% | 32% | **15%** | 14% | 10% | 8% | **+1** | 36 |
| 31 | 6. 4+ up/down days in a row | 53 (24/29) | 30% | 33% | **15%** | 14% | 6% | 9% | **+1** | 34 |
| 32 | 5. 50+ pips from the daily middle band + 8. daily RSI(3) beyond 70/30 | 191 (115/76) | 36% | 33% | **15%** | 14% | 9% | 8% | **+1** | 34 |
| 33 | 1. beyond the weekly R1/S1 + 7. previous day touched the daily band | 68 (34/34) | 34% | 33% | **15%** | 14% | 9% | 8% | **+1** | 31 |
| 34 | 2. beyond the monthly R1/S1 + 7. previous day touched the daily band | 55 (26/29) | 29% | 33% | **15%** | 14% | 5% | 9% | **+1** | 28 |
| 35 | 6. 4+ up/down days in a row + 8. daily RSI(3) beyond 70/30 | 48 (21/27) | 29% | 33% | **15%** | 14% | 6% | 9% | **+1** | 34 |
| 36 | 6. 3+ up/down days in a row + 8. daily RSI(3) beyond 70/30 | 84 (39/45) | 30% | 33% | **14%** | 14% | 7% | 9% | **+0** | 33 |
| 37 | 2. beyond the monthly R1/S1 | 139 (85/54) | 35% | 32% | **14%** | 14% | 8% | 8% | **+0** | 34 |
| 38 | 5. 100+ pips from the daily middle band | 200 (119/81) | 36% | 32% | **14%** | 14% | 8% | 9% | **-0** | 37 |
| 39 | 6. 5+ up/down days in a row + 8. daily RSI(3) beyond 70/30 | 22 (10/12) | 18% | 33% | **14%** | 14% | 5% | 9% | **-1** | 29 |
| 40 | 5. 80+ pips from the daily middle band | 251 (147/104) | 37% | 32% | **14%** | 15% | 9% | 9% | **-1** | 36 |
| 41 | 6. 3+ up/down days in a row | 105 (48/57) | 28% | 33% | **12%** | 14% | 6% | 9% | **-2** | 32 |
| 42 | 6. 5+ up/down days in a row | 24 (11/13) | 17% | 33% | **12%** | 14% | 4% | 9% | **-2** | 29 |
| 43 | 5. 50+ pips from the daily middle band | 344 (198/146) | 35% | 31% | **13%** | 16% | 8% | 9% | **-2** | 33 |
| 44 | 1. beyond the weekly R2/S2 + 7. previous day touched the daily band | 19 (7/12) | 42% | 33% | **11%** | 15% | 11% | 9% | **-4** | 40 |

Fewer than 10 days (not ranked): 1. beyond the weekly R3/S3 6 (80+: 0%); 4. beyond the previous day's high/low 1 (80+: 0%); 1. beyond the weekly R2/S2 + 8. daily RSI(14) beyond 70/30 9 (80+: 22%); 1. beyond the weekly R3/S3 + 7. previous day touched the daily band 6 (80+: 0%); 1. beyond the weekly R3/S3 + 8. daily RSI(3) beyond 70/30 6 (80+: 0%); 1. beyond the weekly R3/S3 + 8. daily RSI(14) beyond 70/30 4 (80+: 0%); 4. beyond the previous day's high/low + 8. daily RSI(3) beyond 70/30 1 (80+: 0%); 6. 4+ up/down days in a row + 8. daily RSI(14) beyond 70/30 6 (80+: 17%); 6. 5+ up/down days in a row + 8. daily RSI(14) beyond 70/30 1 (80+: 100%).

No days: 2. beyond the monthly R3/S3; 2. beyond the monthly R3/S3 + 7. previous day touched the daily band; 2. beyond the monthly R3/S3 + 8. daily RSI(3) beyond 70/30; 2. beyond the monthly R3/S3 + 8. daily RSI(14) beyond 70/30; 4. beyond the previous day's high/low + 7. previous day touched the daily band; 4. beyond the previous day's high/low + 8. daily RSI(14) beyond 70/30.

## Ranking: from 08:00 UK (hourly candles, three months)

| Rank | Measure / condition | Days (up/down) | 50+ | Others 50+ | 80+ | Others 80+ | 100+ | Others 100+ | 80+ difference | Median move |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 4. beyond the previous day's high/low | 21 (12/9) | 14% | 19% | **5%** | 3% | 5% | 1% | **+2** | 21 |
| 2 | 2. beyond the monthly R2/S2 | 5 (0/5) | 20% | 15% | **0%** | 0% | 0% | 0% | **+0** | 39 |
| 3 | 2. beyond the monthly R1/S1 + 7. previous day touched the daily band | 10 (3/7) | 0% | 18% | **0%** | 2% | 0% | 1% | **-2** | 17 |
| 4 | 5. 100+ pips from the daily middle band + 8. daily RSI(14) beyond 70/30 | 7 (2/5) | 14% | 18% | **0%** | 2% | 0% | 1% | **-2** | 31 |
| 5 | 2. beyond the monthly R1/S1 | 15 (5/10) | 13% | 18% | **0%** | 2% | 0% | 1% | **-2** | 22 |
| 6 | 5. 100+ pips from the daily middle band | 24 (11/13) | 8% | 20% | **0%** | 2% | 0% | 2% | **-2** | 24 |
| 7 | 6. 3+ up/down days in a row + 7. previous day touched the daily band | 6 (2/4) | 0% | 18% | **0%** | 2% | 0% | 1% | **-2** | 25 |
| 8 | 2. beyond the monthly R1/S1 + 8. daily RSI(3) beyond 70/30 | 12 (5/7) | 8% | 19% | **0%** | 2% | 0% | 2% | **-2** | 18 |
| 9 | 8. daily RSI(14) beyond 70/30 | 8 (3/5) | 25% | 18% | **0%** | 3% | 0% | 1% | **-3** | 35 |
| 10 | 2. beyond the monthly R1/S1 + 8. daily RSI(14) beyond 70/30 | 8 (3/5) | 25% | 18% | **0%** | 3% | 0% | 1% | **-3** | 35 |
| 11 | 5. 50+ pips from the daily middle band + 8. daily RSI(14) beyond 70/30 | 8 (3/5) | 25% | 18% | **0%** | 3% | 0% | 1% | **-3** | 35 |
| 12 | 5. 80+ pips from the daily middle band + 8. daily RSI(14) beyond 70/30 | 8 (3/5) | 25% | 18% | **0%** | 3% | 0% | 1% | **-3** | 35 |
| 13 | 1. beyond the weekly R2/S2 | 5 (2/3) | 0% | 18% | **0%** | 3% | 0% | 1% | **-3** | 28 |
| 14 | 1. beyond the weekly R2/S2 + 7. previous day touched the daily band | 5 (2/3) | 0% | 18% | **0%** | 3% | 0% | 1% | **-3** | 28 |
| 15 | 1. beyond the weekly R2/S2 + 8. daily RSI(3) beyond 70/30 | 5 (2/3) | 0% | 18% | **0%** | 3% | 0% | 1% | **-3** | 28 |
| 16 | 5. 50+ pips from the daily middle band | 46 (25/21) | 13% | 21% | **0%** | 3% | 0% | 3% | **-3** | 22 |
| 17 | 1. beyond the weekly R1/S1 + 8. daily RSI(3) beyond 70/30 | 10 (4/6) | 0% | 20% | **0%** | 3% | 0% | 1% | **-3** | 27 |
| 18 | 4. beyond the previous week's high/low + 8. daily RSI(3) beyond 70/30 | 17 (8/9) | 12% | 20% | **0%** | 3% | 0% | 2% | **-3** | 25 |
| 19 | 4. beyond the previous week's high/low | 18 (9/9) | 11% | 20% | **0%** | 3% | 0% | 2% | **-3** | 25 |
| 20 | 5. 100+ pips from the daily middle band + 7. previous day touched the daily band | 15 (8/7) | 7% | 19% | **0%** | 3% | 0% | 2% | **-3** | 22 |
| 21 | 4. beyond the previous day's high/low + 8. daily RSI(3) beyond 70/30 | 8 (5/3) | 12% | 19% | **0%** | 3% | 0% | 2% | **-3** | 23 |
| 22 | 4. beyond the previous week's high/low + 7. previous day touched the daily band | 12 (7/5) | 8% | 19% | **0%** | 3% | 0% | 2% | **-3** | 17 |
| 23 | 5. 100+ pips from the daily middle band + 8. daily RSI(3) beyond 70/30 | 17 (9/8) | 6% | 20% | **0%** | 3% | 0% | 2% | **-3** | 25 |
| 24 | 1. beyond the weekly R1/S1 | 11 (5/6) | 0% | 20% | **0%** | 3% | 0% | 2% | **-3** | 26 |
| 25 | 5. 50+ pips from the daily middle band + 8. daily RSI(3) beyond 70/30 | 30 (18/12) | 10% | 23% | **0%** | 3% | 0% | 2% | **-3** | 24 |
| 26 | 5. 80+ pips from the daily middle band + 7. previous day touched the daily band | 16 (9/7) | 6% | 19% | **0%** | 3% | 0% | 2% | **-3** | 22 |
| 27 | 1. beyond the weekly R1/S1 + 7. previous day touched the daily band | 8 (4/4) | 0% | 19% | **0%** | 3% | 0% | 2% | **-3** | 20 |
| 28 | 8. daily RSI(3) beyond 70/30 | 35 (19/16) | 11% | 26% | **0%** | 4% | 0% | 2% | **-4** | 25 |
| 29 | 5. 50+ pips from the daily middle band + 7. previous day touched the daily band | 17 (10/7) | 6% | 19% | **0%** | 4% | 0% | 2% | **-4** | 22 |
| 30 | 5. 80+ pips from the daily middle band | 35 (20/15) | 14% | 22% | **0%** | 4% | 0% | 4% | **-4** | 22 |
| 31 | 7. previous day touched the daily band | 19 (11/8) | 11% | 18% | **0%** | 4% | 0% | 2% | **-4** | 22 |
| 32 | 6. 4+ up/down days in a row | 5 (3/2) | 0% | 20% | **0%** | 4% | 0% | 2% | **-4** | 28 |
| 33 | 3. beyond the daily R1/S1 at 08:00 + 8. daily RSI(3) beyond 70/30 | 5 (3/2) | 0% | 20% | **0%** | 4% | 0% | 2% | **-4** | 25 |
| 34 | 6. 4+ up/down days in a row + 8. daily RSI(3) beyond 70/30 | 5 (3/2) | 0% | 20% | **0%** | 4% | 0% | 2% | **-4** | 28 |
| 35 | 6. 3+ up/down days in a row | 11 (6/5) | 0% | 21% | **0%** | 4% | 0% | 2% | **-4** | 25 |
| 36 | 6. 3+ up/down days in a row + 8. daily RSI(3) beyond 70/30 | 11 (6/5) | 0% | 21% | **0%** | 4% | 0% | 2% | **-4** | 25 |
| 37 | 3. beyond the daily R2/S2 at 08:00 | 6 (4/2) | 17% | 19% | **0%** | 4% | 0% | 2% | **-4** | 24 |
| 38 | 3. beyond the daily R1/S1 at 08:00 | 14 (9/5) | 7% | 20% | **0%** | 5% | 0% | 2% | **-5** | 18 |
| 39 | 5. 80+ pips from the daily middle band + 8. daily RSI(3) beyond 70/30 | 25 (17/8) | 8% | 23% | **0%** | 5% | 0% | 3% | **-5** | 25 |

Fewer than 5 days (not ranked): 1. beyond the weekly R3/S3 1 (80+: 0%); 3. beyond the daily R3/S3 at 08:00 1 (80+: 0%); 6. 5+ up/down days in a row 2 (80+: 0%); 1. beyond the weekly R1/S1 + 8. daily RSI(14) beyond 70/30 4 (80+: 0%); 1. beyond the weekly R2/S2 + 8. daily RSI(14) beyond 70/30 3 (80+: 0%); 1. beyond the weekly R3/S3 + 7. previous day touched the daily band 1 (80+: 0%); 1. beyond the weekly R3/S3 + 8. daily RSI(3) beyond 70/30 1 (80+: 0%); 1. beyond the weekly R3/S3 + 8. daily RSI(14) beyond 70/30 1 (80+: 0%); 2. beyond the monthly R2/S2 + 7. previous day touched the daily band 2 (80+: 0%); 2. beyond the monthly R2/S2 + 8. daily RSI(3) beyond 70/30 3 (80+: 0%); 2. beyond the monthly R2/S2 + 8. daily RSI(14) beyond 70/30 4 (80+: 0%); 3. beyond the daily R1/S1 at 08:00 + 7. previous day touched the daily band 2 (80+: 0%); 3. beyond the daily R2/S2 at 08:00 + 8. daily RSI(3) beyond 70/30 3 (80+: 0%); 3. beyond the daily R3/S3 at 08:00 + 8. daily RSI(3) beyond 70/30 1 (80+: 0%); 4. beyond the previous day's high/low + 7. previous day touched the daily band 4 (80+: 0%); 4. beyond the previous week's high/low + 8. daily RSI(14) beyond 70/30 4 (80+: 0%); 6. 3+ up/down days in a row + 8. daily RSI(14) beyond 70/30 3 (80+: 0%); 6. 4+ up/down days in a row + 7. previous day touched the daily band 3 (80+: 0%); 6. 4+ up/down days in a row + 8. daily RSI(14) beyond 70/30 2 (80+: 0%); 6. 5+ up/down days in a row + 7. previous day touched the daily band 1 (80+: 0%); 6. 5+ up/down days in a row + 8. daily RSI(3) beyond 70/30 2 (80+: 0%).

No days: 2. beyond the monthly R3/S3; 2. beyond the monthly R3/S3 + 7. previous day touched the daily band; 2. beyond the monthly R3/S3 + 8. daily RSI(3) beyond 70/30; 2. beyond the monthly R3/S3 + 8. daily RSI(14) beyond 70/30; 3. beyond the daily R1/S1 at 08:00 + 8. daily RSI(14) beyond 70/30; 3. beyond the daily R2/S2 at 08:00 + 7. previous day touched the daily band; 3. beyond the daily R2/S2 at 08:00 + 8. daily RSI(14) beyond 70/30; 3. beyond the daily R3/S3 at 08:00 + 7. previous day touched the daily band; 3. beyond the daily R3/S3 at 08:00 + 8. daily RSI(14) beyond 70/30; 4. beyond the previous day's high/low + 8. daily RSI(14) beyond 70/30; 6. 5+ up/down days in a row + 8. daily RSI(14) beyond 70/30.

### Measure 3 at 10:00 UK (from 10:00)

| Rank | Measure / condition | Days (up/down) | 50+ | Others 50+ | 80+ | Others 80+ | 100+ | Others 100+ | 80+ difference | Median move |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 3. beyond the daily R2/S2 at 10:00 | 7 (5/2) | 0% | 14% | **0%** | 2% | 0% | 2% | **-2** | 23 |
| 2 | 3. beyond the daily R1/S1 at 10:00 + 8. daily RSI(3) beyond 70/30 | 6 (5/1) | 0% | 13% | **0%** | 3% | 0% | 3% | **-3** | 23 |
| 3 | 3. beyond the daily R1/S1 at 10:00 | 20 (14/6) | 5% | 13% | **0%** | 3% | 0% | 3% | **-3** | 21 |

Fewer than 5 days (not ranked): 3. beyond the daily R3/S3 at 10:00 3 (80+: 0%); 3. beyond the daily R1/S1 at 10:00 + 7. previous day touched the daily band 4 (80+: 0%); 3. beyond the daily R1/S1 at 10:00 + 8. daily RSI(14) beyond 70/30 1 (80+: 0%); 3. beyond the daily R2/S2 at 10:00 + 8. daily RSI(3) beyond 70/30 3 (80+: 0%); 3. beyond the daily R3/S3 at 10:00 + 8. daily RSI(3) beyond 70/30 2 (80+: 0%).

No days: 3. beyond the daily R2/S2 at 10:00 + 7. previous day touched the daily band; 3. beyond the daily R2/S2 at 10:00 + 8. daily RSI(14) beyond 70/30; 3. beyond the daily R3/S3 at 10:00 + 7. previous day touched the daily band; 3. beyond the daily R3/S3 at 10:00 + 8. daily RSI(14) beyond 70/30.

## Flagged days for the best ten (from the open)

**1. 2. beyond the monthly R2/S2 + 8. daily RSI(14) beyond 70/30** (16 days; 80+ pips on 38% against 14%):

| Day | Side | Price at the open | Move back (pips) |
|---|---|---|---|
| Mon 13 Jan 2025 | down | 12203.0 | 46.7 |
| Wed 15 Jan 2025 | down | 12209.2 | 96.3 |
| Mon 20 Jan 2025 | down | 12174.3 | 170.0 |
| Wed 19 Mar 2025 | up | 12999.6 | 44.8 |
| Thu 20 Mar 2025 | up | 13009.8 | 74.2 |
| Tue 22 Apr 2025 | up | 13381.6 | 148.5 |
| Wed 24 Dec 2025 | up | 13511.8 | 20.0 |
| Thu 25 Dec 2025 | up | 13515.3 | 19.5 |
| Fri 26 Dec 2025 | up | 13506.2 | 29.0 |
| Wed 28 Jan 2026 | up | 13826.6 | 77.1 |
| Thu 29 Jan 2026 | up | 13825.1 | 83.0 |
| Fri 30 Jan 2026 | up | 13807.0 | 128.2 |
| Thu 24 Sep 2026 | down | 13241.8 | 13.9 |
| Fri 25 Sep 2026 | down | 13214.6 | 48.5 |
| Mon 28 Sep 2026 | down | 13226.4 | 53.3 |
| Wed 30 Sep 2026 | down | 13226.4 | 84.7 |

**2. 2. beyond the monthly R2/S2 + 7. previous day touched the daily band** (14 days; 80+ pips on 36% against 14%):

| Day | Side | Price at the open | Move back (pips) |
|---|---|---|---|
| Mon 13 Jan 2025 | down | 12203.0 | 46.7 |
| Tue 14 Jan 2025 | down | 12230.8 | 14.4 |
| Wed 15 Jan 2025 | down | 12209.2 | 96.3 |
| Tue 23 Dec 2025 | up | 13467.9 | 0.2 |
| Wed 24 Dec 2025 | up | 13511.8 | 20.0 |
| Thu 25 Dec 2025 | up | 13515.3 | 19.5 |
| Fri 26 Dec 2025 | up | 13506.2 | 29.0 |
| Wed 28 Jan 2026 | up | 13826.6 | 77.1 |
| Thu 29 Jan 2026 | up | 13825.1 | 83.0 |
| Fri 30 Jan 2026 | up | 13807.0 | 128.2 |
| Mon 16 Mar 2026 | down | 13245.1 | 93.6 |
| Tue 31 Mar 2026 | down | 13178.9 | 85.3 |
| Thu 24 Sep 2026 | down | 13241.8 | 13.9 |
| Fri 25 Sep 2026 | down | 13214.6 | 48.5 |

**3. 2. beyond the monthly R2/S2 + 8. daily RSI(3) beyond 70/30** (24 days; 80+ pips on 29% against 13%):

| Day | Side | Price at the open | Move back (pips) |
|---|---|---|---|
| Mon 13 Jan 2025 | down | 12203.0 | 46.7 |
| Tue 14 Jan 2025 | down | 12230.8 | 14.4 |
| Wed 15 Jan 2025 | down | 12209.2 | 96.3 |
| Mon 20 Jan 2025 | down | 12174.3 | 170.0 |
| Tue 18 Mar 2025 | up | 12983.7 | 32.4 |
| Wed 19 Mar 2025 | up | 12999.6 | 44.8 |
| Thu 20 Mar 2025 | up | 13009.8 | 74.2 |
| Mon 21 Apr 2025 | up | 13303.8 | 2.9 |
| Tue 22 Apr 2025 | up | 13381.6 | 148.5 |
| Tue 29 Apr 2025 | up | 13435.5 | 55.5 |
| Tue 23 Dec 2025 | up | 13467.9 | 0.2 |
| Wed 24 Dec 2025 | up | 13511.8 | 20.0 |
| Thu 25 Dec 2025 | up | 13515.3 | 19.5 |
| Fri 26 Dec 2025 | up | 13506.2 | 29.0 |
| Tue 30 Dec 2025 | up | 13507.8 | 58.2 |
| Wed 28 Jan 2026 | up | 13826.6 | 77.1 |
| Thu 29 Jan 2026 | up | 13825.1 | 83.0 |
| Fri 30 Jan 2026 | up | 13807.0 | 128.2 |
| Mon 16 Mar 2026 | down | 13245.1 | 93.6 |
| Mon 30 Mar 2026 | down | 13237.9 | 44.6 |
| Tue 31 Mar 2026 | down | 13178.9 | 85.3 |
| Thu 24 Sep 2026 | down | 13241.8 | 13.9 |
| Fri 25 Sep 2026 | down | 13214.6 | 48.5 |
| Mon 28 Sep 2026 | down | 13226.4 | 53.3 |

**4. 2. beyond the monthly R2/S2** (33 days; 80+ pips on 27% against 13%):

| Day | Side | Price at the open | Move back (pips) |
|---|---|---|---|
| Mon 13 Jan 2025 | down | 12203.0 | 46.7 |
| Tue 14 Jan 2025 | down | 12230.8 | 14.4 |
| Wed 15 Jan 2025 | down | 12209.2 | 96.3 |
| Thu 16 Jan 2025 | down | 12242.0 | 17.9 |
| Fri 17 Jan 2025 | down | 12233.7 | 10.4 |
| Mon 20 Jan 2025 | down | 12174.3 | 170.0 |
| Tue 18 Mar 2025 | up | 12983.7 | 32.4 |
| Wed 19 Mar 2025 | up | 12999.6 | 44.8 |
| Thu 20 Mar 2025 | up | 13009.8 | 74.2 |
| Mon 21 Apr 2025 | up | 13303.8 | 2.9 |
| Tue 22 Apr 2025 | up | 13381.6 | 148.5 |
| Fri 25 Apr 2025 | up | 13336.9 | 63.2 |
| Mon 28 Apr 2025 | up | 13298.5 | 18.8 |
| Tue 29 Apr 2025 | up | 13435.5 | 55.5 |
| Wed 30 Apr 2025 | up | 13409.8 | 100.9 |
| Tue 23 Dec 2025 | up | 13467.9 | 0.2 |
| Wed 24 Dec 2025 | up | 13511.8 | 20.0 |
| Thu 25 Dec 2025 | up | 13515.3 | 19.5 |
| Fri 26 Dec 2025 | up | 13506.2 | 29.0 |
| Mon 29 Dec 2025 | up | 13495.5 | 26.2 |
| Tue 30 Dec 2025 | up | 13507.8 | 58.2 |
| Wed 31 Dec 2025 | up | 13466.6 | 64.6 |
| Wed 28 Jan 2026 | up | 13826.6 | 77.1 |
| Thu 29 Jan 2026 | up | 13825.1 | 83.0 |
| Fri 30 Jan 2026 | up | 13807.0 | 128.2 |
| Mon 16 Mar 2026 | down | 13245.1 | 93.6 |
| Mon 30 Mar 2026 | down | 13237.9 | 44.6 |
| Tue 31 Mar 2026 | down | 13178.9 | 85.3 |
| Thu 24 Sep 2026 | down | 13241.8 | 13.9 |
| Fri 25 Sep 2026 | down | 13214.6 | 48.5 |
| Mon 28 Sep 2026 | down | 13226.4 | 53.3 |
| Tue 29 Sep 2026 | down | 13254.5 | 0.4 |
| Wed 30 Sep 2026 | down | 13226.4 | 84.7 |

**5. 8. daily RSI(14) beyond 70/30** (34 days; 80+ pips on 26% against 14%):

| Day | Side | Price at the open | Move back (pips) |
|---|---|---|---|
| Fri 03 Jan 2025 | down | 12378.9 | 54.7 |
| Mon 13 Jan 2025 | down | 12203.0 | 46.7 |
| Wed 15 Jan 2025 | down | 12209.2 | 96.3 |
| Mon 20 Jan 2025 | down | 12174.3 | 170.0 |
| Thu 06 Mar 2025 | up | 12889.3 | 23.9 |
| Fri 07 Mar 2025 | up | 12882.4 | 6.6 |
| Mon 10 Mar 2025 | up | 12931.5 | 70.3 |
| Thu 13 Mar 2025 | up | 12963.8 | 43.2 |
| Wed 19 Mar 2025 | up | 12999.6 | 44.8 |
| Thu 20 Mar 2025 | up | 13009.8 | 74.2 |
| Fri 04 Apr 2025 | up | 13105.0 | 252.5 |
| Tue 22 Apr 2025 | up | 13381.6 | 148.5 |
| Fri 01 Aug 2025 | down | 13206.4 | 104.0 |
| Fri 31 Oct 2025 | down | 13158.3 | 6.4 |
| Mon 03 Nov 2025 | down | 13133.2 | 28.9 |
| Tue 04 Nov 2025 | down | 13133.8 | 5.2 |
| Wed 05 Nov 2025 | down | 13021.1 | 32.2 |
| Thu 06 Nov 2025 | down | 13051.4 | 90.2 |
| Wed 24 Dec 2025 | up | 13511.8 | 20.0 |
| Thu 25 Dec 2025 | up | 13515.3 | 19.5 |
| Fri 26 Dec 2025 | up | 13506.2 | 29.0 |
| Mon 26 Jan 2026 | up | 13663.5 | 21.1 |
| Tue 27 Jan 2026 | up | 13674.5 | 11.2 |
| Wed 28 Jan 2026 | up | 13826.6 | 77.1 |
| Thu 29 Jan 2026 | up | 13825.1 | 83.0 |
| Fri 30 Jan 2026 | up | 13807.0 | 128.2 |
| Fri 21 Aug 2026 | up | 13636.3 | 18.4 |
| Mon 24 Aug 2026 | up | 13642.4 | 24.9 |
| Wed 26 Aug 2026 | up | 13648.6 | 68.7 |
| Fri 18 Sep 2026 | down | 13358.2 | 39.8 |
| Thu 24 Sep 2026 | down | 13241.8 | 13.9 |
| Fri 25 Sep 2026 | down | 13214.6 | 48.5 |
| Mon 28 Sep 2026 | down | 13226.4 | 53.3 |
| Wed 30 Sep 2026 | down | 13226.4 | 84.7 |

**6. 5. 50+ pips from the daily middle band + 8. daily RSI(14) beyond 70/30**: the same days as number 5.

**7. 5. 80+ pips from the daily middle band + 8. daily RSI(14) beyond 70/30**: the same days as number 5.

**8. 5. 100+ pips from the daily middle band + 8. daily RSI(14) beyond 70/30**: the same days as number 5.

**9. 4. beyond the previous week's high/low + 8. daily RSI(14) beyond 70/30** (24 days; 80+ pips on 25% against 13%):

| Day | Side | Price at the open | Move back (pips) |
|---|---|---|---|
| Fri 03 Jan 2025 | down | 12378.9 | 54.7 |
| Thu 06 Mar 2025 | up | 12889.3 | 23.9 |
| Fri 07 Mar 2025 | up | 12882.4 | 6.6 |
| Thu 13 Mar 2025 | up | 12963.8 | 43.2 |
| Wed 19 Mar 2025 | up | 12999.6 | 44.8 |
| Thu 20 Mar 2025 | up | 13009.8 | 74.2 |
| Fri 04 Apr 2025 | up | 13105.0 | 252.5 |
| Tue 22 Apr 2025 | up | 13381.6 | 148.5 |
| Fri 01 Aug 2025 | down | 13206.4 | 104.0 |
| Fri 31 Oct 2025 | down | 13158.3 | 6.4 |
| Wed 05 Nov 2025 | down | 13021.1 | 32.2 |
| Thu 06 Nov 2025 | down | 13051.4 | 90.2 |
| Wed 24 Dec 2025 | up | 13511.8 | 20.0 |
| Thu 25 Dec 2025 | up | 13515.3 | 19.5 |
| Fri 26 Dec 2025 | up | 13506.2 | 29.0 |
| Mon 26 Jan 2026 | up | 13663.5 | 21.1 |
| Tue 27 Jan 2026 | up | 13674.5 | 11.2 |
| Wed 28 Jan 2026 | up | 13826.6 | 77.1 |
| Thu 29 Jan 2026 | up | 13825.1 | 83.0 |
| Fri 30 Jan 2026 | up | 13807.0 | 128.2 |
| Fri 21 Aug 2026 | up | 13636.3 | 18.4 |
| Fri 18 Sep 2026 | down | 13358.2 | 39.8 |
| Thu 24 Sep 2026 | down | 13241.8 | 13.9 |
| Fri 25 Sep 2026 | down | 13214.6 | 48.5 |

**10. 1. beyond the weekly R1/S1 + 8. daily RSI(14) beyond 70/30** (20 days; 80+ pips on 25% against 14%):

| Day | Side | Price at the open | Move back (pips) |
|---|---|---|---|
| Fri 03 Jan 2025 | down | 12378.9 | 54.7 |
| Thu 06 Mar 2025 | up | 12889.3 | 23.9 |
| Fri 07 Mar 2025 | up | 12882.4 | 6.6 |
| Wed 19 Mar 2025 | up | 12999.6 | 44.8 |
| Thu 20 Mar 2025 | up | 13009.8 | 74.2 |
| Fri 04 Apr 2025 | up | 13105.0 | 252.5 |
| Tue 22 Apr 2025 | up | 13381.6 | 148.5 |
| Fri 01 Aug 2025 | down | 13206.4 | 104.0 |
| Fri 31 Oct 2025 | down | 13158.3 | 6.4 |
| Wed 05 Nov 2025 | down | 13021.1 | 32.2 |
| Wed 24 Dec 2025 | up | 13511.8 | 20.0 |
| Thu 25 Dec 2025 | up | 13515.3 | 19.5 |
| Fri 26 Dec 2025 | up | 13506.2 | 29.0 |
| Wed 28 Jan 2026 | up | 13826.6 | 77.1 |
| Thu 29 Jan 2026 | up | 13825.1 | 83.0 |
| Fri 30 Jan 2026 | up | 13807.0 | 128.2 |
| Fri 21 Aug 2026 | up | 13636.3 | 18.4 |
| Fri 18 Sep 2026 | down | 13358.2 | 39.8 |
| Thu 24 Sep 2026 | down | 13241.8 | 13.9 |
| Fri 25 Sep 2026 | down | 13214.6 | 48.5 |

## Flagged days for the best ten from 08:00 (hourly candles)

**1. 4. beyond the previous day's high/low** (21 days; 80+ pips on 5% against 3%):

| Day | Side | Price at 08:00 | Move back (pips) |
|---|---|---|---|
| Mon 10 Aug 2026 | up | 13494.2 | 3.9 |
| Thu 13 Aug 2026 | down | 13482.4 | 30.6 |
| Mon 17 Aug 2026 | up | 13557.8 | 29.0 |
| Tue 18 Aug 2026 | down | 13526.8 | 23.3 |
| Mon 31 Aug 2026 | up | 13543.3 | 8.3 |
| Wed 02 Sep 2026 | down | 13492.6 | 21.4 |
| Mon 07 Sep 2026 | up | 13525.7 | 4.9 |
| Mon 14 Sep 2026 | down | 13490.6 | 23.0 |
| Wed 23 Sep 2026 | down | 13317.0 | 1.2 |
| Mon 05 Oct 2026 | down | 13219.1 | 19.9 |
| Mon 12 Oct 2026 | up | 13253.6 | 55.0 |
| Wed 14 Oct 2026 | up | 13269.2 | 133.6 |
| Fri 16 Oct 2026 | up | 13310.0 | 1.1 |
| Tue 20 Oct 2026 | up | 13350.0 | 13.8 |
| Thu 22 Oct 2026 | up | 13405.0 | 50.1 |
| Tue 27 Oct 2026 | down | 13324.0 | 10.5 |
| Wed 28 Oct 2026 | down | 13289.2 | 48.4 |
| Fri 30 Oct 2026 | up | 13404.3 | 30.4 |
| Mon 02 Nov 2026 | up | 13413.8 | 15.6 |
| Wed 04 Nov 2026 | up | 13478.1 | 24.8 |
| Fri 06 Nov 2026 | down | 13398.0 | 11.8 |

**2. 2. beyond the monthly R2/S2** (5 days; 80+ pips on 0% against 0%):

| Day | Side | Price at 08:00 | Move back (pips) |
|---|---|---|---|
| Thu 24 Sep 2026 | down | 13243.9 | 11.8 |
| Fri 25 Sep 2026 | down | 13223.6 | 39.5 |
| Mon 28 Sep 2026 | down | 13241.0 | 38.7 |
| Tue 29 Sep 2026 | down | 13240.0 | 11.6 |
| Wed 30 Sep 2026 | down | 13254.4 | 56.7 |

**3. 2. beyond the monthly R1/S1 + 7. previous day touched the daily band** (10 days; 80+ pips on 0% against 2%):

| Day | Side | Price at 08:00 | Move back (pips) |
|---|---|---|---|
| Thu 20 Aug 2026 | up | 13615.9 | 8.0 |
| Fri 21 Aug 2026 | up | 13648.9 | 31.0 |
| Mon 24 Aug 2026 | up | 13642.6 | 25.1 |
| Thu 17 Sep 2026 | down | 13398.3 | 8.1 |
| Fri 18 Sep 2026 | down | 13369.6 | 28.4 |
| Mon 21 Sep 2026 | down | 13377.4 | 22.1 |
| Tue 22 Sep 2026 | down | 13372.7 | 0.9 |
| Wed 23 Sep 2026 | down | 13317.0 | 1.2 |
| Thu 24 Sep 2026 | down | 13243.9 | 11.8 |
| Fri 25 Sep 2026 | down | 13223.6 | 39.5 |

**4. 5. 100+ pips from the daily middle band + 8. daily RSI(14) beyond 70/30** (7 days; 80+ pips on 0% against 2%):

| Day | Side | Price at 08:00 | Move back (pips) |
|---|---|---|---|
| Fri 21 Aug 2026 | up | 13648.9 | 31.0 |
| Mon 24 Aug 2026 | up | 13642.6 | 25.1 |
| Fri 18 Sep 2026 | down | 13369.6 | 28.4 |
| Thu 24 Sep 2026 | down | 13243.9 | 11.8 |
| Fri 25 Sep 2026 | down | 13223.6 | 39.5 |
| Mon 28 Sep 2026 | down | 13241.0 | 38.7 |
| Wed 30 Sep 2026 | down | 13254.4 | 56.7 |

**5. 2. beyond the monthly R1/S1** (15 days; 80+ pips on 0% against 2%):

| Day | Side | Price at 08:00 | Move back (pips) |
|---|---|---|---|
| Thu 20 Aug 2026 | up | 13615.9 | 8.0 |
| Fri 21 Aug 2026 | up | 13648.9 | 31.0 |
| Mon 24 Aug 2026 | up | 13642.6 | 25.1 |
| Tue 25 Aug 2026 | up | 13626.9 | 1.3 |
| Wed 26 Aug 2026 | up | 13632.2 | 52.3 |
| Thu 17 Sep 2026 | down | 13398.3 | 8.1 |
| Fri 18 Sep 2026 | down | 13369.6 | 28.4 |
| Mon 21 Sep 2026 | down | 13377.4 | 22.1 |
| Tue 22 Sep 2026 | down | 13372.7 | 0.9 |
| Wed 23 Sep 2026 | down | 13317.0 | 1.2 |
| Thu 24 Sep 2026 | down | 13243.9 | 11.8 |
| Fri 25 Sep 2026 | down | 13223.6 | 39.5 |
| Mon 28 Sep 2026 | down | 13241.0 | 38.7 |
| Tue 29 Sep 2026 | down | 13240.0 | 11.6 |
| Wed 30 Sep 2026 | down | 13254.4 | 56.7 |

**6. 5. 100+ pips from the daily middle band** (24 days; 80+ pips on 0% against 2%):

| Day | Side | Price at 08:00 | Move back (pips) |
|---|---|---|---|
| Mon 17 Aug 2026 | up | 13557.8 | 29.0 |
| Thu 20 Aug 2026 | up | 13615.9 | 8.0 |
| Fri 21 Aug 2026 | up | 13648.9 | 31.0 |
| Mon 24 Aug 2026 | up | 13642.6 | 25.1 |
| Thu 17 Sep 2026 | down | 13398.3 | 8.1 |
| Fri 18 Sep 2026 | down | 13369.6 | 28.4 |
| Mon 21 Sep 2026 | down | 13377.4 | 22.1 |
| Tue 22 Sep 2026 | down | 13372.7 | 0.9 |
| Wed 23 Sep 2026 | down | 13317.0 | 1.2 |
| Thu 24 Sep 2026 | down | 13243.9 | 11.8 |
| Fri 25 Sep 2026 | down | 13223.6 | 39.5 |
| Mon 28 Sep 2026 | down | 13241.0 | 38.7 |
| Tue 29 Sep 2026 | down | 13240.0 | 11.6 |
| Wed 30 Sep 2026 | down | 13254.4 | 56.7 |
| Thu 01 Oct 2026 | down | 13262.5 | 3.6 |
| Fri 02 Oct 2026 | down | 13212.8 | 42.2 |
| Mon 05 Oct 2026 | down | 13219.1 | 19.9 |
| Tue 20 Oct 2026 | up | 13350.0 | 13.8 |
| Wed 21 Oct 2026 | up | 13375.7 | 3.9 |
| Thu 22 Oct 2026 | up | 13405.0 | 50.1 |
| Fri 23 Oct 2026 | up | 13382.8 | 22.4 |
| Fri 30 Oct 2026 | up | 13404.3 | 30.4 |
| Wed 04 Nov 2026 | up | 13478.1 | 24.8 |
| Thu 05 Nov 2026 | up | 13471.1 | 35.4 |

**7. 6. 3+ up/down days in a row + 7. previous day touched the daily band** (6 days; 80+ pips on 0% against 2%):

| Day | Side | Price at 08:00 | Move back (pips) |
|---|---|---|---|
| Thu 17 Sep 2026 | down | 13398.3 | 8.1 |
| Fri 18 Sep 2026 | down | 13369.6 | 28.4 |
| Thu 24 Sep 2026 | down | 13243.9 | 11.8 |
| Fri 25 Sep 2026 | down | 13223.6 | 39.5 |
| Fri 23 Oct 2026 | up | 13382.8 | 22.4 |
| Thu 05 Nov 2026 | up | 13471.1 | 35.4 |

**8. 2. beyond the monthly R1/S1 + 8. daily RSI(3) beyond 70/30** (12 days; 80+ pips on 0% against 2%):

| Day | Side | Price at 08:00 | Move back (pips) |
|---|---|---|---|
| Thu 20 Aug 2026 | up | 13615.9 | 8.0 |
| Fri 21 Aug 2026 | up | 13648.9 | 31.0 |
| Mon 24 Aug 2026 | up | 13642.6 | 25.1 |
| Tue 25 Aug 2026 | up | 13626.9 | 1.3 |
| Wed 26 Aug 2026 | up | 13632.2 | 52.3 |
| Thu 17 Sep 2026 | down | 13398.3 | 8.1 |
| Fri 18 Sep 2026 | down | 13369.6 | 28.4 |
| Tue 22 Sep 2026 | down | 13372.7 | 0.9 |
| Wed 23 Sep 2026 | down | 13317.0 | 1.2 |
| Thu 24 Sep 2026 | down | 13243.9 | 11.8 |
| Fri 25 Sep 2026 | down | 13223.6 | 39.5 |
| Mon 28 Sep 2026 | down | 13241.0 | 38.7 |

**9. 8. daily RSI(14) beyond 70/30** (8 days; 80+ pips on 0% against 3%):

| Day | Side | Price at 08:00 | Move back (pips) |
|---|---|---|---|
| Fri 21 Aug 2026 | up | 13648.9 | 31.0 |
| Mon 24 Aug 2026 | up | 13642.6 | 25.1 |
| Wed 26 Aug 2026 | up | 13632.2 | 52.3 |
| Fri 18 Sep 2026 | down | 13369.6 | 28.4 |
| Thu 24 Sep 2026 | down | 13243.9 | 11.8 |
| Fri 25 Sep 2026 | down | 13223.6 | 39.5 |
| Mon 28 Sep 2026 | down | 13241.0 | 38.7 |
| Wed 30 Sep 2026 | down | 13254.4 | 56.7 |

**10. 2. beyond the monthly R1/S1 + 8. daily RSI(14) beyond 70/30**: the same days as number 9.

## Reading it

- **From the open, the best result is price beyond the monthly R2 or S2** (rank 4 on its own: 27% of 33 days moved 80+ pips back, against 13% of other days), and it is stronger with the daily RSI(14) beyond 70/30 or a band touch the day before (ranks 1 and 2: 38% and 36% against 14%). These are the same few days seen several ways: the best group is 16 days, of which 6 moved 80+ pips where about 2 would be expected. The chance of 6 or more by luck alone is about 1% for one group, and about 140 groups were tested here (59 from the open), so one result this strong is not evidence on its own.
- **The daily RSI(14) beyond 70/30** on its own (34 days) gave 80-pip moves on 26% of days against 14%. With 14 periods it picks far fewer and more extreme days than with 3 periods (254 days, 15% against 13%). The 50/80/100-pip distances from the middle band add nothing to it: every RSI(14) day was already 100+ pips from the band.
- **Measures used widely** (beyond the weekly R1/S1, beyond the previous week's high/low, the band touch, RSI(3)) flag 100 to 250 days and change the 80-pip rate by only 2 to 6 points (15-19% against 13%).
- **Up/down days in a row** add a little only with a band touch (5+ days and a touch: 25% against 14%, 12 days).
- **From 08:00 and 10:00 on the hourly candles** (66 days) almost no day moved 80+ pips after 08:00 (2-3% of all days), so these three months cannot rank anything; the daily R1/R2/R3 at 08:00 or 10:00 (measure 3) flagged 1 to 20 days; at most one day of each moved 50+ pips back, and none 80.
- **Worth testing further** (more history, and on the bot's own trades rather than the day's furthest point): price beyond the monthly R2/S2, with the daily RSI(14) beyond 70/30.

