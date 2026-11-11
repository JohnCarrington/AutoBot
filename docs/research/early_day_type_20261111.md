# Early day type: what 08:00, 09:00 and 10:00 UK told about the day, 2024 to 2026

Wednesday 11 November 2026, UK. Read-only research: **nothing in the bot was changed**. There were no IG calls and no restart. Only the candle stores and the news calendar were read, and nothing was written outside `data/research/`.

## Summary

**The days.** Every weekday is put in one type, on the sell price (IG's bid), from the open at midnight UK to the close:

- **Trended:** closed 60 pips or more from its open.
- **Came back:** moved 30 to 40 pips from its open one way (never more than 40 either way), then gave back at least half of that move by the close.
- **Other:** everything else.

| | Weekdays | Trended | Came back | Other |
|---|---:|---:|---:|---:|
| 2024 (AutoBot 161's IG candles) | 259 | 65 (25%) | 26 (10%) | 168 (65%) |
| 2025 (AutoBot 161's IG candles) | 259 | 73 (28%) | 21 (8%) | 165 (64%) |
| 2026, 26 October to 10 November (the bot's own) | 12 | 3 | 1 | 8 |

A rule is only counted as telling the types apart if it beat the base rate in **both** 2024 and 2025. 2026 is too short to judge by (12 days) and is shown for reference only.

**What told trended days apart:**

- **The move since 07:00 was the best single sign.** Earlier signs barely helped:
  - **By 08:00:** weak. The best single signs were an Asian range of 40+ pips (47% and 37% right) and a range of 30+ pips since 07:00 (45% and 35%), against base rates of 25% and 28%.
  - **By 09:00, moved 30+ pips (net) since 07:00:** a trend day **44% of the time in 2024 and 59% in 2025**, about twice the base rate. It caught 17% and 36% of the trend days.
  - **By 09:00, moved 20+ pips:** right 36% and 42%, but caught half of all trend days (37% and 51%).
  - **By 10:00, moved 30+ pips:** right 42% and 57%, catching 28% and 49%.
- **The early move also gave the direction.** On trend days, a move of 10+ pips since 07:00 pointed the right way **71 to 87% of the time** (85% in both years by 10:00). London's one-way break of the Asian range pointed the right way **77 to 85%** of the time.
- **Together, the strongest were about 2.3 times the base rate.** Each fired on only 11 to 41 days a year:
  - **no big news + moved 30+ pips since 07:00 by 09:00:** 57% and 68% right;
  - **moved 20+ pips by 09:00 + daily RSI under 40:** 62% and 64%, but on only 13 and 11 days.
  
  None is right much more than two times in three.
- **These did not tell trend days apart on their own:** big news, where the day opened against the pivot or the previous day's high and low, the daily RSI, and whether London broke out of the Asian range at all.
  - Big news still to come after 09:00 came closest: 31% and 38% trended. It almost never gave a came-back day (2% and 0%).
  - Where the day opened against the pivot did not even give the direction of a trend day: 50% and 41% of trend days went back towards it.

**What told came-back days apart: almost nothing.**

- They are 8 to 10% of days.
- No condition known by 08:00 or 09:00 picked them out on its own.
- By 10:00 the only one was **price having moved under 15 pips (net) since 07:00** (under 5 pips an hour): 14% and 10% came-back days, against 10% and 8%. It was wrong about 87% of the time.
- The best pairs were right 12 to 31% of the time.
- Came-back days look like the other quiet days until the afternoon.

**What told that a day would not trend.** This is the most dependable reading:

- **Moved under 5 pips since 07:00 by 09:00:** no trend on **81% (2024) and 86% (2025)** of those days, against 75% and 72% of all days.
- **By 10:00, any of these:** **82 to 87%** no trend.
  - under 15 pips since 07:00;
  - London broke out of the Asian range both ways.

**Since 25 October 2026:** on 6 November, 9 November and 10 November (the three trend days) the move since 07:00 by 09:00 was −21.4, +22.3 and +6.6 pips. Two of the three passed "moved 20+", and none passed "30+". On 2 November, the day with the biggest early move (+36.4 by 09:00), the day did not trend (+22.4).

**How far to trust it:**

- 518 days in two years, and each finding holds in both. But the conditions were tested from a menu of 36 at each time, and 630 pairs, so some of the weaker pairs will have passed by chance.
- The findings to rely on are the plain ones that are strong in both years: the size of the move since 07:00, and the direction it gives.
- 2025 moved more than 2024 (a median day range of 83 pips against 73, and a median Asian range of 28.5 against 20.4), so fixed pip thresholds fire more often in 2025.

## How it was done

- **Candles:**
  - **2024 and 2025:** AutoBot 161's IG candles, `data/research/candles_ig161_bidask/` (161's 5-minute IG bid prices, with daily candles built midnight to midnight UK; see `ig161_mid_2026_20261110.md`). The sell price is IG's bid exactly.
  - **26 October to 10 November 2026:** the bot's own IG candles, a read-only copy taken at 17:38 UTC today (`data/research/replay_stores/live_copy_20261111_1738/`). Its daily candles from November 2024 give the previous day's levels and the RSI.
  - Today is left out because its close is not in yet. AutoBot 161's 2026 candles (January to October) were not asked for and are not used.
- **Days used:** 530 weekdays. Five were left out because their candles are incomplete: 1 January and 25 December in both years (the market is open only a few hours), and 7 November 2024 (240 of 288 candles). The first 24 weekdays of 2024 have no RSI reading: the RSI needs 30 earlier daily candles, and 161's history starts on 1 January 2024.
- **What was known at 08:00, 09:00 and 10:00 UK.** Only candles that had finished by then were used.
  - **Big-news day:** a release the bot's own news rules count as big for GBP or USD (`news.calendar.big_news_windows`, Finnhub's past calendar, the bot's news table) on that UK day. It is a scheduled release, so it is known from the open. Also recorded: whether that news was already out by the time, or still to come.
  - **The Asian session:** the bot has no Asian session, so it is taken as the day's open (midnight UK) to 07:00 UK. Its range is its high minus its low. "London broke out" means price went above the Asian high (up), below the Asian low (down), or both, between 07:00 and the time.
  - **Where the day opened:**
    - against the bot's daily pivot (the previous trading day's (high + low + close) ÷ 3, as the bot works it out, so Monday's is from the short Sunday candle);
    - against the previous day's high and low: within 10 pips of either, in the top or bottom fifth of that range, or in its middle third.
    
    It always opens inside the previous day's range, since the market trades straight through midnight.
  - **How far since 07:00:** the net move from the 07:00 open to the last close before the time, and the range (high minus low) since 07:00.
  - **How fast:**
    - **pips an hour:** the net move divided by the hours since 07:00. At a fixed time this is the same test as the distance, so identical conditions are shown on one row joined by "=".
    - **the average size of the 5-minute candles since 07:00** (high minus low), which does not depend on the direction.
  - **Daily RSI:** the bot's own reading for trend days, RSI(14) with Wilder's smoothing on the daily closes up to the previous day (`prices.indicators.rsi`, `trend_day.rsi_periods`).
- **Telling the types apart:**
  - Each condition is tested alone, and every pair of conditions together, for each of trended and came back.
  - **How often it was right** is the share of the days it held on that were of that type.
  - **Caught** is the share of all that year's days of that type it held on.
  - **×** is how many times the year's base rate it was.
  - A condition is listed only if it was at least 1.25 times the base rate in both 2024 and 2025, on at least 15 days in each (10 for pairs).
- The scripts and the day-by-day data (`days.json`) are in `data/research/early_day_type_20261111/`. The scripts are kept out of the repository, which commits only this file.

## Results

### How many days of each type

| Year | Weekdays | Trended | Came back | Other |
|---|---:|---:|---:|---:|
| 2024 | 259 | 65 (25%) | 26 (10%) | 168 (65%) |
| 2025 | 259 | 73 (28%) | 21 (8%) | 165 (64%) |
| 2026 (26 Oct to 10 Nov) | 12 | 3 (25%) | 1 (8%) | 8 (67%) |

### Telling trended days apart

#### Known by 8:00 UK

Each cell: days of that type / days the condition held = how often it was right, (× the year's base rate), and the share of all that year's trended days it caught. Only conditions better than the base rate by ×1.25 in both 2024 and 2025, on at least 15 days in each, are listed; 2026 is shown but not used to choose.

| Condition, alone | 2024 | 2025 | 2026 |
|---|---|---|---|
| 5-minute candles since 07:00 average 8+ pips | 5/15 = 33% (×1.3), caught 8% | 12/29 = 41% (×1.5), caught 16% | — |
| Asian range 40 or more | 7/15 = 47% (×1.9), caught 11% | 23/63 = 37% (×1.3), caught 32% | 1/2 = 50% |
| range since 07:00 30+ pips | 13/29 = 45% (×1.8), caught 20% | 12/34 = 35% (×1.3), caught 16% | 0/2 = 0% |

Best two conditions together (47 different pairs passed, at least 10 days in each year; the 8 strongest):

| Conditions together | 2024 | 2025 | 2026 |
|---|---|---|---|
| opened in the middle third of the previous day's range + moved 20+ pips since 07:00 | 5/10 = 50% (×2.0), caught 8% | 8/12 = 67% (×2.4), caught 11% | 0/1 = 0% |
| no big news + range since 07:00 30+ pips | 6/11 = 55% (×2.2), caught 9% | 10/20 = 50% (×1.8), caught 14% | 0/1 = 0% |
| Asian range 30 or more + 15+ pips an hour since 07:00 (net move ÷ hours) | 6/13 = 46% (×1.8), caught 9% | 16/32 = 50% (×1.8), caught 22% | 1/2 = 50% |
| 15+ pips an hour since 07:00 (net move ÷ hours) + daily RSI under 40 | 5/11 = 45% (×1.8), caught 8% | 5/10 = 50% (×1.8), caught 7% | — |
| Asian range 40 or more + moved 10+ pips since 07:00 (net) | 5/10 = 50% (×2.0), caught 8% | 16/33 = 48% (×1.7), caught 22% | 1/2 = 50% |
| no big news + moved 20+ pips since 07:00 | 5/12 = 42% (×1.7), caught 8% | 14/28 = 50% (×1.8), caught 19% | — |
| range since 07:00 30+ pips + 15+ pips an hour since 07:00 (net move ÷ hours) | 10/23 = 43% (×1.7), caught 15% | 12/26 = 46% (×1.6), caught 16% | 0/2 = 0% |
| opened in the middle third of the previous day's range + 15+ pips an hour since 07:00 (net move ÷ hours) | 8/19 = 42% (×1.7), caught 12% | 8/18 = 44% (×1.6), caught 11% | 0/1 = 0% |

#### Known by 9:00 UK

Each cell: days of that type / days the condition held = how often it was right, (× the year's base rate), and the share of all that year's trended days it caught. Only conditions better than the base rate by ×1.25 in both 2024 and 2025, on at least 15 days in each, are listed; 2026 is shown but not used to choose.

| Condition, alone | 2024 | 2025 | 2026 |
|---|---|---|---|
| moved 30+ pips since 07:00 = 15+ pips an hour since 07:00 (net move ÷ hours) | 11/25 = 44% (×1.8), caught 17% | 26/44 = 59% (×2.1), caught 36% | 0/1 = 0% |
| range since 07:00 40+ pips | 15/35 = 43% (×1.7), caught 23% | 28/59 = 47% (×1.7), caught 38% | 0/1 = 0% |
| moved 20+ pips since 07:00 | 24/66 = 36% (×1.4), caught 37% | 37/89 = 42% (×1.5), caught 51% | 2/6 = 33% |
| 10+ pips an hour since 07:00 (net move ÷ hours) | 24/67 = 36% (×1.4), caught 37% | 37/89 = 42% (×1.5), caught 51% | 2/6 = 33% |
| Asian range 40 or more | 7/15 = 47% (×1.9), caught 11% | 23/63 = 37% (×1.3), caught 32% | 1/2 = 50% |

Best two conditions together (73 different pairs passed, at least 10 days in each year; the 8 strongest):

| Conditions together | 2024 | 2025 | 2026 |
|---|---|---|---|
| no big news + moved 30+ pips since 07:00 | 8/14 = 57% (×2.3), caught 12% | 19/28 = 68% (×2.4), caught 26% | 0/1 = 0% |
| moved 20+ pips since 07:00 + daily RSI under 40 | 8/13 = 62% (×2.5), caught 12% | 7/11 = 64% (×2.3), caught 10% | — |
| 10+ pips an hour since 07:00 (net move ÷ hours) + daily RSI under 40 | 8/14 = 57% (×2.3), caught 12% | 7/11 = 64% (×2.3), caught 10% | — |
| moved 30+ pips since 07:00 + 5-minute candles since 07:00 average 6+ pips | 9/17 = 53% (×2.1), caught 14% | 21/36 = 58% (×2.1), caught 29% | — |
| opened within 10 pips of the previous day's high or low + moved 30+ pips since 07:00 | 6/12 = 50% (×2.0), caught 9% | 10/16 = 62% (×2.2), caught 14% | 0/1 = 0% |
| opened in the top or bottom fifth of the previous day's range + moved 30+ pips since 07:00 | 7/14 = 50% (×2.0), caught 11% | 12/18 = 67% (×2.4), caught 16% | — |
| moved 10+ pips since 07:00 (net) + 5-minute candles since 07:00 average 8+ pips | 7/10 = 70% (×2.8), caught 11% | 14/25 = 56% (×2.0), caught 19% | — |
| no big news + range since 07:00 40+ pips | 10/19 = 53% (×2.1), caught 15% | 22/41 = 54% (×1.9), caught 30% | 0/1 = 0% |

#### Known by 10:00 UK

Each cell: days of that type / days the condition held = how often it was right, (× the year's base rate), and the share of all that year's trended days it caught. Only conditions better than the base rate by ×1.25 in both 2024 and 2025, on at least 15 days in each, are listed; 2026 is shown but not used to choose.

| Condition, alone | 2024 | 2025 | 2026 |
|---|---|---|---|
| moved 30+ pips since 07:00 = 10+ pips an hour since 07:00 (net move ÷ hours) | 18/43 = 42% (×1.7), caught 28% | 36/63 = 57% (×2.0), caught 49% | 1/3 = 33% |
| range since 07:00 40+ pips | 25/66 = 38% (×1.5), caught 38% | 44/102 = 43% (×1.5), caught 60% | 0/2 = 0% |
| moved 20+ pips since 07:00 | 34/87 = 39% (×1.6), caught 52% | 49/124 = 40% (×1.4), caught 67% | 3/7 = 43% |
| 15+ pips an hour since 07:00 (net move ÷ hours) | 5/15 = 33% (×1.3), caught 8% | 12/21 = 57% (×2.0), caught 16% | — |
| Asian range 40 or more | 7/15 = 47% (×1.9), caught 11% | 23/63 = 37% (×1.3), caught 32% | 1/2 = 50% |

Best two conditions together (71 different pairs passed, at least 10 days in each year; the 8 strongest):

| Conditions together | 2024 | 2025 | 2026 |
|---|---|---|---|
| opened in the middle third of the previous day's range + moved 30+ pips since 07:00 | 7/12 = 58% (×2.3), caught 11% | 12/18 = 67% (×2.4), caught 16% | 0/1 = 0% |
| Asian range 30 or more + moved 30+ pips since 07:00 | 8/14 = 57% (×2.3), caught 12% | 18/30 = 60% (×2.1), caught 25% | 0/1 = 0% |
| no big news + moved 30+ pips since 07:00 | 13/26 = 50% (×2.0), caught 20% | 27/41 = 66% (×2.3), caught 37% | 1/2 = 50% |
| opened in the top or bottom fifth of the previous day's range + moved 30+ pips since 07:00 | 10/21 = 48% (×1.9), caught 15% | 15/28 = 54% (×1.9), caught 21% | 1/2 = 50% |
| moved 30+ pips since 07:00 + 5-minute candles since 07:00 average 6+ pips | 11/23 = 48% (×1.9), caught 17% | 23/44 = 52% (×1.9), caught 32% | — |
| opened within 10 pips of the previous day's high or low + moved 30+ pips since 07:00 | 10/22 = 45% (×1.8), caught 15% | 15/26 = 58% (×2.0), caught 21% | 1/1 = 100% |
| London broke out of the Asian range one way only + moved 30+ pips since 07:00 | 17/38 = 45% (×1.8), caught 26% | 30/47 = 64% (×2.3), caught 41% | 1/2 = 50% |
| range since 07:00 40+ pips + daily RSI under 40 | 7/14 = 50% (×2.0), caught 11% | 8/16 = 50% (×1.8), caught 11% | — |

### Telling came back days apart

#### Known by 8:00 UK

Each cell: days of that type / days the condition held = how often it was right, (× the year's base rate), and the share of all that year's came back days it caught. Only conditions better than the base rate by ×1.25 in both 2024 and 2025, on at least 15 days in each, are listed; 2026 is shown but not used to choose.

No single condition passed.

Best two conditions together (14 different pairs passed, at least 10 days in each year; the 8 strongest):

| Conditions together | 2024 | 2025 | 2026 |
|---|---|---|---|
| opened within 10 pips of the previous day's high or low + 5-minute candles since 07:00 average under 4 pips | 8/50 = 16% (×1.6), caught 31% | 3/11 = 27% (×3.4), caught 14% | 0/1 = 0% |
| Asian range under 25 + opened 20+ pips from the pivot | 6/36 = 17% (×1.7), caught 23% | 2/16 = 12% (×1.5), caught 10% | 0/1 = 0% |
| London did not break out + moved 10+ pips since 07:00 (net) | 3/14 = 21% (×2.1), caught 12% | 3/24 = 12% (×1.5), caught 14% | 0/1 = 0% |
| London broke out of the Asian range one way only + 5-minute candles since 07:00 average under 4 pips | 11/74 = 15% (×1.5), caught 42% | 2/15 = 13% (×1.6), caught 10% | 0/1 = 0% |
| London did not break out + opened 20+ pips from the pivot | 3/14 = 21% (×2.1), caught 12% | 3/25 = 12% (×1.5), caught 14% | — |
| no big news + opened 20+ pips from the pivot | 8/39 = 21% (×2.0), caught 31% | 6/51 = 12% (×1.5), caught 29% | 0/1 = 0% |
| opened 20+ pips from the pivot + daily RSI 40 to 60 | 8/26 = 31% (×3.1), caught 31% | 4/34 = 12% (×1.5), caught 19% | 0/2 = 0% |
| no big news + 5-minute candles since 07:00 average under 4 pips | 13/90 = 14% (×1.4), caught 50% | 5/23 = 22% (×2.7), caught 24% | 0/1 = 0% |

#### Known by 9:00 UK

Each cell: days of that type / days the condition held = how often it was right, (× the year's base rate), and the share of all that year's came back days it caught. Only conditions better than the base rate by ×1.25 in both 2024 and 2025, on at least 15 days in each, are listed; 2026 is shown but not used to choose.

No single condition passed.

Best two conditions together (8 different pairs passed, at least 10 days in each year; the 8 strongest):

| Conditions together | 2024 | 2025 | 2026 |
|---|---|---|---|
| Asian range under 25 + opened 20+ pips from the pivot | 6/36 = 17% (×1.7), caught 23% | 2/16 = 12% (×1.5), caught 10% | 0/1 = 0% |
| no big news + opened 20+ pips from the pivot | 8/39 = 21% (×2.0), caught 31% | 6/51 = 12% (×1.5), caught 29% | 0/1 = 0% |
| opened 20+ pips from the pivot + daily RSI 40 to 60 | 8/26 = 31% (×3.1), caught 31% | 4/34 = 12% (×1.5), caught 19% | 0/2 = 0% |
| no big news + daily RSI 40 to 60 | 14/94 = 15% (×1.5), caught 54% | 12/104 = 12% (×1.4), caught 57% | 0/6 = 0% |
| opened within 10 pips of the previous day's high or low + opened 20+ pips from the pivot | 7/40 = 18% (×1.7), caught 27% | 4/35 = 11% (×1.4), caught 19% | 0/1 = 0% |
| opened within 10 pips of the previous day's high or low + under 5 pips an hour since 07:00 (net move ÷ hours) | 8/57 = 14% (×1.4), caught 31% | 4/36 = 11% (×1.4), caught 19% | 0/1 = 0% |
| opened within 5 pips of the pivot + under 5 pips an hour since 07:00 (net move ÷ hours) | 6/40 = 15% (×1.5), caught 23% | 3/27 = 11% (×1.4), caught 14% | 0/1 = 0% |
| opened within 5 pips of the pivot + moved under 5 pips since 07:00 | 3/23 = 13% (×1.3), caught 12% | 2/13 = 15% (×1.9), caught 10% | — |

#### Known by 10:00 UK

Each cell: days of that type / days the condition held = how often it was right, (× the year's base rate), and the share of all that year's came back days it caught. Only conditions better than the base rate by ×1.25 in both 2024 and 2025, on at least 15 days in each, are listed; 2026 is shown but not used to choose.

| Condition, alone | 2024 | 2025 | 2026 |
|---|---|---|---|
| under 5 pips an hour since 07:00 (net move ÷ hours) | 20/141 = 14% (×1.4), caught 77% | 11/106 = 10% (×1.3), caught 52% | 1/4 = 25% |

Best two conditions together (10 different pairs passed, at least 10 days in each year; the 8 strongest):

| Conditions together | 2024 | 2025 | 2026 |
|---|---|---|---|
| under 5 pips an hour since 07:00 (net move ÷ hours) + daily RSI 40 to 60 | 13/75 = 17% (×1.7), caught 50% | 8/58 = 14% (×1.7), caught 38% | 1/4 = 25% |
| no big news + under 5 pips an hour since 07:00 (net move ÷ hours) | 18/110 = 16% (×1.6), caught 69% | 10/76 = 13% (×1.6), caught 48% | 0/2 = 0% |
| Asian range under 25 + opened 20+ pips from the pivot | 6/36 = 17% (×1.7), caught 23% | 2/16 = 12% (×1.5), caught 10% | 0/1 = 0% |
| no big news + opened 20+ pips from the pivot | 8/39 = 21% (×2.0), caught 31% | 6/51 = 12% (×1.5), caught 29% | 0/1 = 0% |
| opened 20+ pips from the pivot + daily RSI 40 to 60 | 8/26 = 31% (×3.1), caught 31% | 4/34 = 12% (×1.5), caught 19% | 0/2 = 0% |
| no big news + daily RSI 40 to 60 | 14/94 = 15% (×1.5), caught 54% | 12/104 = 12% (×1.4), caught 57% | 0/6 = 0% |
| opened within 10 pips of the previous day's high or low + opened 20+ pips from the pivot | 7/40 = 18% (×1.7), caught 27% | 4/35 = 11% (×1.4), caught 19% | 0/1 = 0% |
| London broke out of the Asian range one way only + under 5 pips an hour since 07:00 (net move ÷ hours) | 16/112 = 14% (×1.4), caught 62% | 9/80 = 11% (×1.4), caught 43% | 1/4 = 25% |

### Telling that a day would not trend

Conditions under which trended days were at most three quarters of the year's base rate in both 2024 and 2025 (at least 15 days each). Each cell: days that did NOT trend / days the condition held = how often "not a trend day" was right (the base rate of days that did not trend: 2024 75%, 2025 72%).

#### Known by 8:00 UK

None.

#### Known by 9:00 UK

| Condition | 2024 | 2025 | 2026 |
|---|---|---|---|
| moved under 5 pips since 07:00 | 61/75 = 81% | 48/56 = 86% | 2/2 = 100% |

#### Known by 10:00 UK

| Condition | 2024 | 2025 | 2026 |
|---|---|---|---|
| moved under 5 pips since 07:00 | 41/49 = 84% | 33/40 = 82% | 1/1 = 100% |
| London broke out both ways | 40/49 = 82% | 39/45 = 87% | 1/2 = 50% |
| under 5 pips an hour since 07:00 (net move ÷ hours) | 115/141 = 82% | 88/106 = 83% | 4/4 = 100% |

### Every condition at 09:00 UK: the share of each type when it held (2024 / 2025)

| Condition | Days (2024 / 2025) | Trended | Came back | Other |
|---|---|---|---|---|
| big-news day | 70 / 73 | 29% / 32% | 6% / 3% | 66% / 66% |
| no big news | 189 / 186 | 24% / 27% | 12% / 10% | 65% / 63% |
| big news still to come after 9:00 | 48 / 56 | 31% / 38% | 2% / 0% | 67% / 62% |
| big news already out by 9:00 | 29 / 28 | 24% / 18% | 10% / 7% | 66% / 75% |
| Asian range under 15 | 55 / 2 | 27% / 0% | 5% / 0% | 67% / 100% |
| Asian range under 20 | 124 / 33 | 22% / 33% | 9% / 6% | 69% / 61% |
| Asian range under 25 | 179 / 86 | 23% / 27% | 11% / 6% | 66% / 67% |
| Asian range 30 or more | 43 / 115 | 40% / 32% | 2% / 7% | 58% / 61% |
| Asian range 40 or more | 15 / 63 | 47% / 37% | 0% / 0% | 53% / 63% |
| London broke out of the Asian range one way only | 201 / 206 | 28% / 30% | 10% / 8% | 62% / 62% |
| London broke out both ways | 34 / 20 | 24% / 20% | 12% / 5% | 65% / 75% |
| London did not break out | 24 / 33 | 4% / 24% | 8% / 9% | 88% / 67% |
| opened within 10 pips of the previous day's high or low | 129 / 104 | 22% / 24% | 12% / 7% | 65% / 69% |
| opened in the top or bottom fifth of the previous day's range | 129 / 113 | 25% / 21% | 9% / 7% | 66% / 72% |
| opened in the middle third of the previous day's range | 71 / 82 | 27% / 28% | 6% / 10% | 68% / 62% |
| opened 20+ pips from the pivot | 59 / 69 | 32% / 22% | 15% / 9% | 53% / 70% |
| opened within 5 pips of the pivot | 83 / 80 | 17% / 29% | 10% / 9% | 73% / 62% |
| moved 10+ pips since 07:00 (net) | 138 / 161 | 30% / 34% | 10% / 7% | 60% / 59% |
| moved 20+ pips since 07:00 | 66 / 89 | 36% / 42% | 8% / 2% | 56% / 56% |
| moved 30+ pips since 07:00 | 25 / 44 | 44% / 59% | 0% / 2% | 56% / 39% |
| moved under 5 pips since 07:00 | 75 / 56 | 19% / 14% | 8% / 11% | 73% / 75% |
| range since 07:00 20+ pips | 165 / 229 | 30% / 29% | 9% / 8% | 61% / 62% |
| range since 07:00 30+ pips | 82 / 123 | 38% / 35% | 7% / 5% | 55% / 60% |
| range since 07:00 40+ pips | 35 / 59 | 43% / 47% | 0% / 2% | 57% / 51% |
| range since 07:00 under 15 | 30 / 7 | 20% / 29% | 10% / 0% | 70% / 71% |
| 10+ pips an hour since 07:00 (net move ÷ hours) | 67 / 89 | 36% / 42% | 7% / 2% | 57% / 56% |
| 15+ pips an hour since 07:00 (net move ÷ hours) | 25 / 44 | 44% / 59% | 0% / 2% | 56% / 39% |
| 20+ pips an hour since 07:00 (net move ÷ hours) | 11 / 20 | 36% / 65% | 0% / 0% | 64% / 35% |
| under 5 pips an hour since 07:00 (net move ÷ hours) | 120 / 97 | 19% / 19% | 10% / 9% | 71% / 72% |
| 5-minute candles since 07:00 average 6+ pips | 56 / 119 | 38% / 34% | 2% / 7% | 61% / 59% |
| 5-minute candles since 07:00 average 8+ pips | 11 / 34 | 73% / 44% | 0% / 3% | 27% / 53% |
| 5-minute candles since 07:00 average under 4 pips | 63 / 7 | 22% / 29% | 11% / 29% | 67% / 43% |
| daily RSI over 60 | 61 / 79 | 30% / 23% | 7% / 9% | 64% / 68% |
| daily RSI under 40 | 44 / 40 | 30% / 32% | 7% / 5% | 64% / 62% |
| daily RSI over 70 or under 30 | 17 / 18 | 41% / 33% | 12% / 6% | 47% / 61% |
| daily RSI 40 to 60 | 130 / 140 | 23% / 30% | 12% / 9% | 65% / 61% |
| **All days (the base rate)** | 259 / 259 | 25% / 28% | 10% / 8% | 65% / 64% |

### On trended days: did the early move point the right way?

| Known by | Early sign | 2024 | 2025 | 2026 |
|---|---|---|---|---|
| 8:00 | the move since 07:00 (when 10+ pips) | 23/29 = 79% | 28/37 = 76% | 1/1 = 100% |
| 8:00 | London's breakout of the Asian range (one way only) | 42/54 = 78% | 45/54 = 83% | 2/3 = 67% |
| 8:00 | where it opened against the pivot (when 10+ pips away) | 16/32 = 50% | 15/37 = 41% | 1/1 = 100% |
| 9:00 | the move since 07:00 (when 10+ pips) | 29/41 = 71% | 48/55 = 87% | 2/2 = 100% |
| 9:00 | London's breakout of the Asian range (one way only) | 43/56 = 77% | 51/61 = 84% | 2/3 = 67% |
| 9:00 | where it opened against the pivot (when 10+ pips away) | 16/32 = 50% | 15/37 = 41% | 1/1 = 100% |
| 10:00 | the move since 07:00 (when 10+ pips) | 39/46 = 85% | 50/59 = 85% | 3/3 = 100% |
| 10:00 | London's breakout of the Asian range (one way only) | 43/55 = 78% | 53/62 = 85% | 2/2 = 100% |
| 10:00 | where it opened against the pivot (when 10+ pips away) | 16/32 = 50% | 15/37 = 41% | 1/1 = 100% |

(For the pivot, "right" means the day trended back towards the pivot: down when it opened above it, up when below.)

### Since 25 October 2026, day by day (the bot's own candles)

| Day | Type | Net | Big news | Asian range | London by 09:00 | Open: below previous high / above previous low | Open vs pivot | Since 07:00 by 09:00 | Avg 5-min candle | RSI |
|---|---|---:|---|---:|---|---|---:|---:|---:|---:|
| Mon 26 Oct | other | -33.0 | no | 20.3 | down | 1.0 / 28.4 | +9.1 | -26.6 (range 31.5) | 4.5 | 57.5 |
| Tue 27 Oct | other | -39.1 | no | 22.1 | down | 43.3 / 16.9 | -8.8 | -3.2 (range 13.8) | 4.2 | 52.9 |
| Wed 28 Oct | came back | +20.8 | yes | 35.6 | down | 43.1 / 9.5 | -11.2 | +12.0 (range 23.1) | 4.0 | 48.0 |
| Thu 29 Oct | other | +51.6 | yes | 33.5 | none | 11.2 / 53.9 | +14.4 | +2.6 (range 26.2) | 5.0 | 50.6 |
| Fri 30 Oct | other | +8.3 | no | 31.4 | up | 10.9 / 82.1 | +23.8 | +20.6 (range 24.3) | 5.5 | 56.5 |
| Mon 02 Nov | other | +22.4 | no | 25.0 | up | 6.8 / 7.0 | +0.1 | +36.4 (range 40.8) | 4.5 | 57.2 |
| Tue 03 Nov | other | +25.4 | no | 20.5 | up | 40.3 / 28.6 | -3.9 | +5.7 (range 18.0) | 4.9 | 59.8 |
| Wed 04 Nov | other | +42.5 | no | 52.3 | up | 0.9 / 36.9 | +12.0 | +20.4 (range 37.4) | 6.5 | 62.4 |
| Thu 05 Nov | other | -20.4 | yes | 22.4 | both | 27.5 / 50.1 | +7.6 | -16.5 (range 36.0) | 5.3 | 66.5 |
| Fri 06 Nov | trended | -107.6 | yes | 50.7 | down | 45.9 / 18.8 | -9.3 | -21.4 (range 24.1) | 6.5 | 63.0 |
| Mon 09 Nov | trended | +80.6 | no | 28.7 | up | 2.2 / 25.5 | +7.8 | +22.3 (range 33.7) | 4.2 | 49.8 |
| Tue 10 Nov | trended | -92.6 | yes | 22.0 | up | 3.9 / 81.2 | +25.5 | +6.6 (range 12.0) | 4.2 | 58.0 |

