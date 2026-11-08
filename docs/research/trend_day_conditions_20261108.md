# Trend-day conditions, daily and hourly candles to 6 November 2026

Read-only research on the stored GBPUSD candles, sell prices: daily candles for 504 weekdays (Mon 02 Dec 2024 to Fri 06 Nov 2026), hourly candles for 66 of them (Fri 07 Aug 2026 onwards). Nothing in the bot was changed. Written 8 November 2026.

## Method

- **Days:** Monday to Friday. Each day's levels come from the **previous daily candle**: pivot, R1-R3, S1-S3 with the bot's own formula (`levels/rules.py`, classic floor pivots). Daily candles run midnight to midnight UK; Monday's previous candle is IG's short Sunday candle, as the bot and IG's chart do.
- **Daily Bollinger bands (20, 2) and daily RSI (3)** with the bot's own indicator code (`prices/indicators.py`; Wilder's RSI), on daily closes up to and including the previous day (Sunday candles included, as on the chart). The first 20 candles of the store are used to start them.
- **Condition 1:** the day's open (the 00:00 UK daily open) at or above R3 (up), or at or below S3 (down). Also checked at the London open on the hourly candles: the 08:00 UK hourly candle's open.
- **Condition 2:** the previous day's high reached the upper band of that day (up), or its low the lower band (down).
- **Condition 3:** the previous day's RSI above 70 (up) or below 30 (down).
- Conditions are combined only on the **same side** (all up or all down).
- **The move back towards the pivot:** for the up side, from the open down to the day's lowest low (from 08:00: the 08:00 open down to the lowest low from 08:00 to the day's end); for the down side, up to the highest high. **Levels passed:** the day's levels (R3 to S3 and the pivot) between the starting price and that furthest point.
- **All other days** (the comparison): every other weekday, measured towards its own pivot (down if it opened at or above the pivot, up if below).

**Limits:** about two years of daily candles and three months of hourly ones; GBPUSD only; the furthest point in a day is not a move a trade could have caught in full.

## How often each condition held

- Condition 1 (open at or beyond R3/S3): **0** of 504 days (0 up, 0 down); at 08:00 on the hourly candles: **1** of 66 days.
  - For scale (not one of the conditions): the open was at or beyond R2/S2 on 0 days.
  - For scale (not one of the conditions): the open was at or beyond R1/S1 on 0 days.
- Condition 2 (previous day touched a band): **132** days (63 upper, 69 lower, 0 both).
- Condition 3 (RSI beyond 70/30): **254** days (144 above 70, 110 below 30).

**Why condition 1 never held at the open.** With the classic formula, R1 is never below the previous day's close and S1 never above it (R1 - close = (2 x high - low - close) / 3, which cannot be negative; S1 is the mirror image). GBPUSD trades through midnight, so the day opens next to the previous close (a median gap of 0.2 pips; the largest two gaps 14 and 21 pips), between S1 and R1, so beyond R2 or R3 only after a big gap (the open was never even beyond R1 or S1 in these two years). At the open, condition 1 cannot pick out any day. Later in the day it can: at 08:00 UK the price was at or beyond R3 or S3 on one day of the 66 with hourly candles.

Days with condition 1 at 08:00 (the only ones):

| Day | Side | 08:00 price | R3 / S3 | Condition 2 | Condition 3 (RSI) | Move towards the pivot from 08:00 | Levels passed |
|---|---|---|---|---|---|---|---|
| Mon 02 Nov 2026 | up | 13413.8 | 13405.9 | no | 71 (up) | 15.6 | 2: R2, R3 |

## The move back towards the pivot, from the day's open (daily candles)

| Conditions | Days | Moved 50+ | Moved 80+ | Moved 100+ | Median move | Median levels passed | All other days | Others 50+ | Others 80+ | Others 100+ | Others median |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | - | - | - | - | - | 504 | 170 (34%) | 69 (14%) | 42 (8%) | 33 |
| 2 | 132 | 49 (37%) | 25 (19%) | 15 (11%) | 34 | 1 | 372 | 127 (34%) | 52 (14%) | 30 (8%) | 33 |
| 3 | 254 | 90 (35%) | 39 (15%) | 26 (10%) | 34 | 1 | 250 | 84 (34%) | 33 (13%) | 16 (6%) | 33 |
| 1 + 2 | 0 | - | - | - | - | - | 504 | 170 (34%) | 69 (14%) | 42 (8%) | 33 |
| 1 + 3 | 0 | - | - | - | - | - | 504 | 170 (34%) | 69 (14%) | 42 (8%) | 33 |
| 2 + 3 | 103 | 35 (34%) | 17 (17%) | 9 (9%) | 32 | 1 | 401 | 135 (34%) | 55 (14%) | 32 (8%) | 33 |
| 1 + 2 + 3 | 0 | - | - | - | - | - | 504 | 170 (34%) | 69 (14%) | 42 (8%) | 33 |

## The move back towards the pivot, from 08:00 UK (hourly candles)

Condition 1 is checked at 08:00 here (the 08:00 price against R3/S3); conditions 2 and 3 as above.

| Conditions | Days | Moved 50+ | Moved 80+ | Moved 100+ | Median move | Median levels passed | All other days | Others 50+ | Others 80+ | Others 100+ | Others median |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 0 (0%) | 0 (0%) | 0 (0%) | 16 | 2 | 65 | 15 (23%) | 1 (2%) | 1 (2%) | 27 |
| 2 | 19 | 2 (11%) | 0 (0%) | 0 (0%) | 22 | 1 | 47 | 13 (28%) | 1 (2%) | 1 (2%) | 28 |
| 3 | 35 | 4 (11%) | 0 (0%) | 0 (0%) | 25 | 1 | 31 | 11 (35%) | 1 (3%) | 1 (3%) | 30 |
| 1 + 2 | 0 | - | - | - | - | - | 66 | 15 (23%) | 1 (2%) | 1 (2%) | 27 |
| 1 + 3 | 1 | 0 (0%) | 0 (0%) | 0 (0%) | 16 | 2 | 65 | 15 (23%) | 1 (2%) | 1 (2%) | 27 |
| 2 + 3 | 14 | 1 (7%) | 0 (0%) | 0 (0%) | 24 | 1 | 52 | 14 (27%) | 1 (2%) | 1 (2%) | 28 |
| 1 + 2 + 3 | 0 | - | - | - | - | - | 66 | 15 (23%) | 1 (2%) | 1 (2%) | 27 |

## Every flagged day (all three conditions on the same side)

**None.** No day met all three conditions, at the open or at 08:00.

## Days with conditions 2 and 3 together (the band and the RSI), for reference

103 days. Where the open stood against the levels, and the move towards the pivot from the open:

| Day | Side | Open | Open vs levels | RSI | Move towards the pivot | Levels passed |
|---|---|---|---|---|---|---|
| Thu 19 Dec 2024 | down | 12566.5 | above S1 | 22 | 100.2 | 1: pivot |
| Fri 20 Dec 2024 | down | 12496.4 | above S1 | 15 | 116.9 | 2: pivot, R1 |
| Fri 03 Jan 2025 | down | 12378.9 | above S1 | 7 | 54.7 | 1: pivot |
| Thu 09 Jan 2025 | down | 12357.8 | above S1 | 23 | 6.9 | 0: - |
| Fri 10 Jan 2025 | down | 12297.8 | above S1 | 16 | 23.3 | 1: pivot |
| Mon 13 Jan 2025 | down | 12203.0 | above pivot | 10 | 46.7 | 3: R1, R2, R3 |
| Tue 14 Jan 2025 | down | 12230.8 | above pivot | 29 | 14.4 | 0: - |
| Wed 15 Jan 2025 | down | 12209.2 | above pivot | 23 | 96.3 | 1: R1 |
| Fri 14 Feb 2025 | up | 12564.1 | above pivot | 87 | 14.9 | 0: - |
| Mon 17 Feb 2025 | up | 12583.8 | above S1 | 87 | 4.9 | 0: - |
| Tue 18 Feb 2025 | up | 12620.4 | above pivot | 92 | 38.6 | 2: S1, pivot |
| Wed 05 Mar 2025 | up | 12794.6 | above pivot | 87 | 27.5 | 0: - |
| Thu 06 Mar 2025 | up | 12889.3 | above pivot | 92 | 23.9 | 0: - |
| Fri 07 Mar 2025 | up | 12882.4 | above S1 | 88 | 6.6 | 0: - |
| Mon 10 Mar 2025 | up | 12931.5 | above pivot | 92 | 70.3 | 4: S3, S2, S1, pivot |
| Thu 03 Apr 2025 | up | 13007.2 | above pivot | 85 | 2.1 | 0: - |
| Fri 04 Apr 2025 | up | 13105.0 | above S1 | 93 | 252.5 | 2: S2, S1 |
| Tue 08 Apr 2025 | down | 12735.3 | above S1 | 16 | 78.4 | 1: pivot |
| Tue 15 Apr 2025 | up | 13180.1 | above pivot | 85 | 16.4 | 0: - |
| Wed 16 Apr 2025 | up | 13236.4 | above pivot | 88 | 25.1 | 1: pivot |
| Thu 17 Apr 2025 | up | 13236.2 | above S1 | 88 | 33.8 | 0: - |
| Tue 13 May 2025 | down | 13175.8 | above S1 | 18 | 139.7 | 2: pivot, R1 |
| Thu 22 May 2025 | up | 13404.6 | above S1 | 84 | 14.0 | 0: - |
| Fri 23 May 2025 | up | 13424.0 | above pivot | 87 | 5.8 | 1: pivot |
| Mon 26 May 2025 | up | 13534.6 | above pivot | 95 | 3.8 | 0: - |
| Tue 27 May 2025 | up | 13565.0 | above pivot | 96 | 65.0 | 3: S2, S1, pivot |
| Fri 13 Jun 2025 | up | 13616.7 | above pivot | 77 | 100.5 | 2: S1, pivot |
| Wed 18 Jun 2025 | down | 13423.0 | above S1 | 16 | 53.1 | 1: pivot |
| Thu 19 Jun 2025 | down | 13420.5 | above S1 | 16 | 51.3 | 2: pivot, R1 |
| Mon 23 Jun 2025 | down | 13427.8 | above pivot | 29 | 119.5 | 3: R1, R2, R3 |
| Wed 25 Jun 2025 | up | 13613.0 | above pivot | 84 | 22.3 | 1: pivot |
| Thu 26 Jun 2025 | up | 13665.8 | above pivot | 89 | 0.2 | 0: - |
| Fri 27 Jun 2025 | up | 13718.4 | above pivot | 92 | 36.6 | 1: pivot |
| Tue 15 Jul 2025 | down | 13426.9 | above S1 | 1 | 40.0 | 1: pivot |
| Wed 16 Jul 2025 | down | 13384.8 | above S1 | 1 | 99.3 | 2: pivot, R1 |
| Thu 17 Jul 2025 | down | 13414.0 | above S1 | 27 | 16.2 | 1: pivot |
| Wed 30 Jul 2025 | down | 13351.7 | above pivot | 15 | 33.5 | 1: R1 |
| Thu 31 Jul 2025 | down | 13252.9 | above S1 | 7 | 28.3 | 0: - |
| Fri 01 Aug 2025 | down | 13206.4 | above S1 | 5 | 104.0 | 2: pivot, R1 |
| Wed 03 Sep 2025 | down | 13385.8 | above S1 | 19 | 71.9 | 1: pivot |
| Tue 16 Sep 2025 | up | 13604.1 | above pivot | 82 | 6.6 | 0: - |
| Wed 17 Sep 2025 | up | 13648.8 | above pivot | 90 | 29.8 | 1: pivot |
| Thu 18 Sep 2025 | up | 13629.8 | above S1 | 70 | 96.5 | 2: S2, S1 |
| Fri 26 Sep 2025 | down | 13342.6 | above S1 | 11 | 70.3 | 1: pivot |
| Fri 10 Oct 2025 | down | 13299.4 | above S1 | 12 | 71.3 | 1: pivot |
| Wed 15 Oct 2025 | down | 13318.7 | above pivot | 27 | 88.8 | 1: R1 |
| Wed 29 Oct 2025 | down | 13277.6 | above S1 | 21 | 2.6 | 0: - |
| Thu 30 Oct 2025 | down | 13194.0 | above S1 | 10 | 23.8 | 1: pivot |
| Fri 31 Oct 2025 | down | 13158.3 | above S1 | 7 | 6.4 | 1: pivot |
| Mon 03 Nov 2025 | down | 13133.2 | above S1 | 5 | 28.9 | 4: pivot, R1, R2, R3 |
| Tue 04 Nov 2025 | down | 13133.8 | above S1 | 7 | 5.2 | 1: pivot |
| Wed 05 Nov 2025 | down | 13021.1 | above S1 | 2 | 32.2 | 0: - |
| Thu 06 Nov 2025 | down | 13051.4 | above pivot | 25 | 90.2 | 3: R1, R2, R3 |
| Wed 26 Nov 2025 | up | 13158.1 | above pivot | 84 | 35.0 | 1: pivot |
| Thu 27 Nov 2025 | up | 13244.2 | above pivot | 94 | 34.0 | 0: - |
| Fri 28 Nov 2025 | up | 13240.4 | above pivot | 90 | 40.1 | 2: S1, pivot |
| Thu 04 Dec 2025 | up | 13347.0 | above pivot | 90 | 30.1 | 0: - |
| Fri 05 Dec 2025 | up | 13321.2 | above S1 | 73 | 5.5 | 0: - |
| Tue 23 Dec 2025 | up | 13467.9 | above pivot | 87 | 0.2 | 0: - |
| Wed 24 Dec 2025 | up | 13511.8 | above pivot | 91 | 20.0 | 1: pivot |
| Thu 25 Dec 2025 | up | 13515.3 | above pivot | 81 | 19.5 | 1: pivot |
| Fri 26 Dec 2025 | up | 13506.2 | above pivot | 83 | 29.0 | 4: S3, S2, S1, pivot |
| Fri 16 Jan 2026 | down | 13381.9 | above S1 | 27 | 30.4 | 1: pivot |
| Mon 26 Jan 2026 | up | 13663.5 | above S1 | 94 | 21.1 | 1: S1 |
| Tue 27 Jan 2026 | up | 13674.5 | above S1 | 95 | 11.2 | 0: - |
| Wed 28 Jan 2026 | up | 13826.6 | above pivot | 98 | 77.1 | 1: pivot |
| Thu 29 Jan 2026 | up | 13825.1 | above pivot | 98 | 83.0 | 2: S1, pivot |
| Fri 30 Jan 2026 | up | 13807.0 | above pivot | 83 | 128.2 | 3: S2, S1, pivot |
| Wed 18 Feb 2026 | down | 13562.4 | above pivot | 15 | 19.6 | 0: - |
| Fri 20 Feb 2026 | down | 13459.1 | above S1 | 6 | 55.2 | 2: pivot, R1 |
| Mon 02 Mar 2026 | down | 13404.2 | above S1 | 17 | 51.4 | 3: pivot, R1, R2 |
| Tue 03 Mar 2026 | down | 13407.6 | above pivot | 19 | 17.2 | 0: - |
| Wed 04 Mar 2026 | down | 13350.9 | above pivot | 10 | 52.0 | 0: - |
| Thu 05 Mar 2026 | down | 13368.6 | above pivot | 27 | 18.2 | 0: - |
| Fri 06 Mar 2026 | down | 13355.3 | above pivot | 22 | 54.0 | 1: R1 |
| Mon 16 Mar 2026 | down | 13245.1 | above pivot | 27 | 93.6 | 3: R1, R2, R3 |
| Tue 31 Mar 2026 | down | 13178.9 | above S1 | 9 | 85.3 | 2: pivot, R1 |
| Thu 09 Apr 2026 | up | 13397.0 | above S1 | 83 | 16.5 | 0: - |
| Wed 15 Apr 2026 | up | 13567.9 | above pivot | 84 | 25.5 | 1: pivot |
| Fri 01 May 2026 | up | 13603.9 | above pivot | 77 | 36.3 | 0: - |
| Fri 15 May 2026 | down | 13398.6 | above S1 | 10 | 0.1 | 0: - |
| Mon 18 May 2026 | down | 13314.6 | above pivot | 6 | 133.9 | 3: R1, R2, R3 |
| Mon 08 Jun 2026 | down | 13322.2 | above pivot | 4 | 47.4 | 3: R1, R2, R3 |
| Tue 09 Jun 2026 | down | 13339.9 | above pivot | 26 | 71.2 | 2: R1, R2 |
| Thu 18 Jun 2026 | down | 13296.5 | above S1 | 20 | 28.2 | 0: - |
| Mon 22 Jun 2026 | down | 13207.9 | above pivot | 13 | 65.2 | 3: R1, R2, R3 |
| Wed 24 Jun 2026 | down | 13200.5 | above S1 | 25 | 8.1 | 0: - |
| Thu 25 Jun 2026 | down | 13165.4 | above S1 | 18 | 53.6 | 2: pivot, R1 |
| Thu 16 Jul 2026 | up | 13538.1 | above pivot | 89 | 79.1 | 1: pivot |
| Thu 20 Aug 2026 | up | 13602.9 | above pivot | 90 | 8.4 | 0: - |
| Fri 21 Aug 2026 | up | 13636.3 | above pivot | 93 | 18.4 | 1: pivot |
| Mon 24 Aug 2026 | up | 13642.4 | above pivot | 90 | 24.9 | 1: pivot |
| Thu 17 Sep 2026 | down | 13379.5 | above S1 | 4 | 26.9 | 0: - |
| Fri 18 Sep 2026 | down | 13358.2 | above S1 | 3 | 39.8 | 2: pivot, R1 |
| Tue 22 Sep 2026 | down | 13369.6 | above S1 | 23 | 17.5 | 1: pivot |
| Wed 23 Sep 2026 | down | 13341.8 | above S1 | 14 | 3.2 | 0: - |
| Thu 24 Sep 2026 | down | 13241.8 | above S1 | 5 | 13.9 | 0: - |
| Fri 25 Sep 2026 | down | 13214.6 | above S1 | 4 | 48.5 | 2: pivot, R1 |
| Mon 19 Oct 2026 | up | 13322.5 | above pivot | 80 | 31.4 | 2: S1, pivot |
| Wed 21 Oct 2026 | up | 13371.7 | above pivot | 83 | 7.6 | 0: - |
| Thu 22 Oct 2026 | up | 13390.1 | above pivot | 86 | 35.2 | 2: S1, pivot |
| Fri 23 Oct 2026 | up | 13400.4 | above pivot | 88 | 40.0 | 2: S1, pivot |
| Thu 05 Nov 2026 | up | 13475.6 | above pivot | 95 | 39.9 | 1: pivot |

## Reading it

- **All three conditions together: no day**, at the open or at 08:00, so the combination cannot be judged on this data. Condition 1 is the reason: at the open it is impossible (above), and at 08:00 it happened once in three months.
- **Condition 2 (previous day touched the band) and condition 3 (RSI beyond 70/30)**, from the open: days with either moved back towards the pivot about as often as other days. 50+ pips: 37% and 35% against 34%; 80+: 19% and 15% against 13-14%; 100+: 11% and 10% against 6-8%. Both together: 34%, 17%, 9%. A few points more often for the larger moves, on 103 to 254 days: a small difference.
- **From 08:00 on the hourly candles** (66 days, three months), days with condition 2 or 3 moved 50+ pips less often than other days (11% against 28-35%), and no day of either reached 80. Too few days to read much into.
- More history (hourly candles especially) would be needed to test condition 1 at 08:00 or later in the day.

