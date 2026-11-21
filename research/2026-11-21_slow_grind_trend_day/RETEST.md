# Re-test: Johnny's slow grind signal against trend days, read the way a trader means it (21 November 2026)

Research only. Nothing in the live bot, its code or its settings was changed. Server: the new AutoBot server,
/opt/autobot (not AutoBot 161). The scripts and outputs are in `retest/`.

## The answer in brief

**Step 1, the measure.** It picks out 4 of Johnny's 5 days: 9 Nov (up), 11 Nov (down), 12 Nov (down) and 18 Nov (down).

**It misses Monday 5 October.** On IG's own prices that day was not a trend day in either direction:
- only 1 hour in a row worked a band;
- it rose 23 pips by 10:00, chopped, and fell back to −10 by 14:00;
- the whole session's range was 49 pips.

The prices were checked against IG's own hourly candles in the bot's store: every hour matches to within 0.7 pips. No band-based measure can take in 5 October without calling most days trend days.

**Tuesday 6 October is a textbook up day:** at the upper hourly band from 08:00, 13 hours in a row, 69 pips. **Johnny, please check whether you meant 6 October.**

Over the three years (8 Jan 2024 to 19 Nov 2026), the measure calls **227 of 713 weekdays (32%)** trend days: 124 up and 103 down.

**Step 2, the signal.** These figures are over the 703 days that are usable for both the signal and the measure, 223 of which are trend days.
- **The signal turned on (up or down) on 341 days.** On 101 of them (30%) it was a trend day in the signal's direction. On 17 it was a trend day the other way, and on 223 it was not a trend day.
- **Of the 223 trend days, the signal caught 101 (45%) and missed 122:**
  - no signal on 102;
  - both ways in profit on 3;
  - signal the wrong way on 17.
- **Most of the catches are the trend's own start.** On 74 of the 101 days caught, the trend run had already begun before 09:00, inside the signal's own window.
  - On the 107 trend days whose run began at 09:00 or later, the signal caught 27 (25%), pointed the wrong way on 14 and gave no signal on 64.
  - So the signal mostly reports a trend that has already started, and it rarely calls one that is still to come.

## Step 1: the trend-day measure

### Johnny's definition (21 Nov)
- **The band:** during trading hours, 06:00–20:30 UK, price mostly works along one Bollinger band (upper for up, lower for down) in short candles.
- **Pullbacks:** it doesn't have to stay on the band. Pullbacks happen, including back to the EMA cluster. What matters is the day overall.
- **Duration and size:** it goes on for hours, often all day, and can move around 100 pips.

### How it is measured (Claude's reading)

On the **hourly chart**, chart (sell) price, Bollinger (20, 2), with the bot's own indicator code. It uses the 15 hourly candles starting 06:00 to 20:00 UK.
1. **An hour works the band:**
   - **Up:** the hourly candle touches the upper hourly band, or closes in the top quarter of the band.
   - **Down:** the mirror.

   This allows pullbacks inside the hour, even to the EMA cluster, as long as the hour ends near its band.
2. **A trend day**, in the direction with more band hours, has all three of these:
   - **Run:** at least **8 of the 15 session hours in a row** work the band. More than half the session, unbroken: "goes on for hours".
   - **No hour in that run touches the other band.** A touch before the run starts doesn't count, so a trend that starts at 08:00 after a dip at 07:00 still counts.
   - **Move in the run:** at least **40 pips** from the run's first open to its furthest point its way.

The cut-offs are set so that the 4 days that can be caught pass. The two weakest, 9 and 12 Nov, both ran 8 hours with 46 pips in the run, so the measure is set just at them. Stricter and looser versions are below.

**Why hourly and not 5-minute.** The earlier study measured "hugging the band" on 5-minute candles, with a pullback to the EMA cluster ending the hug. That was the too-literal reading: on 5-minute candles price touches the 8 EMA every few candles, so no day in three years hugged for even half the session. On the hourly chart a pullback within an hour doesn't break the run, which is how a trader looks at "the day overall".

"Short candles" is not part of the measure. Johnny's days have typical 5-minute candles of 3.6 to 4.2 pips, and the typical day's is 4.3, so it doesn't separate trend days.

### Johnny's five days

| Day | Johnny | Band hours in a row (from) | Pips in the run | Other band in the run | Measure |
|---|---|---|---|---|---|
| Mon 5 Oct | up | 1 (best direction: down) | 26.6 | 0 | **not a trend day**: fails run and move |
| Mon 9 Nov | up | 8 (from 06:00) | 46.0 | 0 | trend up |
| Wed 11 Nov | down | 13 (from 08:00) | 63.2 | 0 | trend down |
| Thu 12 Nov | down | 8 (from 13:00) | 46.1 | 0 | trend down |
| Wed 18 Nov | down | 14 (from 06:00) | 55.5 | 0 | trend down |
| *Tue 6 Oct, for comparison* | — | 13 (from 08:00) | 69.4 | 0 | trend up |

**5 October, hour by hour (IG's own hourly closes, UK time):**

| Hour (UK) | Close | From the 06:00 open | Upper-band touches (5-min) | Lower-band touches (5-min) |
|---|---|---|---|---|
| 03:00–04:00 | — | fell about 40 pips | — | — |
| 06:00 | 13208.3 | ±0 | 1 | 0 |
| 09:00 | 13231.3 | +23 | 5 | 0 |
| 11:00 | 13220.7 | +12 | 0 | 0 |
| 14:00 | 13197.4 | −11 | 0 | 9 |
| 20:00 | 13222.9 | +14 | — | — |

The 5-minute chart gives the same picture: closes on the up side of the middle band 59% of the time, 33 upper-band touches against 23 lower-band touches, and the high only 49 pips above the low.

**What it would take to include 5 October.** Its best is 1 hour in a row with 27 pips in the run. A measure loose enough to take it in (1 hour in a row, 26 pips in the run) calls 562 of 713 days (79%) trend days. Even 5 hours in a row with 30 pips calls 450 (63%). So the measure was not loosened for it.

### How many days, and 10 at random for Johnny's chart

- **227 trend days of 713 weekdays** measured (32%): 124 up and 103 down.
- **The 703 days used in Step 2:** 223 trend days, 122 up and 101 down.
- Every day is in `retest/days_trend_measure.csv`.

**10 trend days chosen at random** (seed 20261121, so the draw can be repeated):

| Day | Trend | Band hours in a row (from) | Pips in the run |
|---|---|---|---|
| Tue 16 Jan 2024 | down | 9 (06:00) | 60.0 |
| Wed 10 Apr 2024 | down | 8 (13:00) | 173.9 |
| Thu 25 Apr 2024 | up | 8 (06:00) | 60.3 |
| Fri 16 Aug 2024 | up | 9 (06:00) | 41.2 |
| Fri 22 Nov 2024 | down | 11 (06:00) | 81.5 |
| Thu 6 Feb 2025 | down | 10 (06:00) | 123.6 |
| Wed 19 Feb 2025 | down | 10 (09:00) | 49.2 |
| Fri 29 Aug 2025 | down | 9 (06:00) | 56.9 |
| Tue 9 Dec 2025 | down | 9 (12:00) | 41.6 |
| Wed 26 Aug 2026 | down | 14 (07:00) | 51.6 |

**Stricter and looser versions,** for Johnny to choose (no other-band touch in the run, in each):

| Version | Trend days of 703 | Johnny's 4 catchable days |
|---|---|---|
| Looser: 6+ hours in a row, 40+ pips | 338 (48%) | all 4 |
| **Used: 8+ hours in a row, 40+ pips** | **223 (32%)** | **all 4** |
| Stricter: 10+ hours in a row, 50+ pips | 118 (17%) | 11 and 18 Nov only |

## Step 2: Johnny's signal against these trend days

**The signal, unchanged.** A slow grind trade is in profit, as IG would close it, at any point between 06:00 and 09:00 UK. Both directions in profit means no signal.
- The trades are the earlier study's: the live code 4635175's slow grind, firing from 00:00 UK. Trades opened before 06:00 count.
- They are judged by that study's same per-candle rules (see `REPORT.md`).
- Rebuilt here, the signal matches the earlier study on all 703 days, with 0 differences.

### Johnny's rule (in profit at all)

**Of the days the signal turned on:**

| | Days | Share |
|---|---|---|
| Signal on (up or down) | 341 | |
| ... trend day in its direction | **101** | **30%** |
| ... trend day the other way | 17 | 5% |
| ... not a trend day | 223 | 65% |
| Both ways in profit (no signal) | 13 | |
| Did not turn on | 349 | |

**Of all trend days:**

| | Days | Share |
|---|---|---|
| Trend days | 223 | |
| **Caught** (signal in the trend's direction) | **101** | **45%** |
| Missed: no signal | 102 | 46% |
| Missed: both ways in profit | 3 | 1% |
| Missed: signal the wrong way | 17 | 8% |

**How to read it:**
- **Chance:** a signal with no link to the day would land on a trend day in its direction on about 16% of signal days: trend days are 32% of days, and half the time the direction would be wrong. The signal does 30%.
- **The overlap:** much of the difference is that both look at the same morning. On 74 of the 101 days caught, the trend run had already started before 09:00.
- **Later trends:** on the 107 trend days whose run started at 09:00 or later, the signal caught 27 (25%), pointed the wrong way on 14 and was off on 64.
- **Johnny's days:**
  - **9, 11 and 18 Nov:** caught.
  - **12 Nov:** caught, but only just. The sell's best was +2.4 at 06:00–09:00 for a trend that started at 13:00.
  - **5 Oct:** no signal, and not a trend day.
  - **6 Oct:** a trend day up, and the signal said **down** (a sell at +11.4 by 09:00).

### Examples for Johnny's chart (the first draws use seed 20261121)

**Missed: no signal (102 in all), 6 at random:**
- Tue 2 Jul 2024: up, 9 hours from 12:00, 45.8 pips.
- Mon 8 Jul 2024: up, 8 hours from 08:00, 43.3 pips.
- Fri 12 Jul 2024: up, 13 hours from 08:00, 84.4 pips.
- Mon 17 Mar 2025: up, 13 hours from 08:00, 62.8 pips.
- Mon 7 Apr 2025: down, 11 hours from 10:00, 160.6 pips.
- Thu 15 Jan 2026: down, 8 hours from 10:00, 73.9 pips.

**Missed: signal the wrong way (17 in all), 6 at random:**
- Fri 30 Aug 2024: down from 13:00, 69.9 pips. Signal up (a buy at +20.0).
- Tue 25 Mar 2025: up from 09:00, 54.5 pips. Signal down (+13.3).
- Wed 26 Nov 2025: up from 13:00, 57.3 pips. Signal down (+5.6).
- Tue 16 Dec 2025: up from 08:00, 81.1 pips. Signal down (+9.8).
- Tue 30 Dec 2025: down from 12:00, 54.5 pips. Signal up (+4.8).
- Tue 21 Jul 2026: down from 11:00, 67.6 pips. Signal up (+5.5).

**False alarms: signal on, not a trend day (223 in all), 6 at random:**
- Fri 5 Apr 2024: signal down (+9.2); best was 3 hours in a row down.
- Thu 11 Apr 2024: signal down (+2.2); best was 2 hours up.
- Mon 28 Oct 2024: signal up (+8.7); 5 hours up, 28 pips.
- Thu 30 Jan 2025: signal down (+2.5); best was 4 hours up.
- Fri 2 May 2025: signal up (+11.8); 3 hours up.
- Mon 30 Jun 2025: signal up (+5.0); best was 3 hours down.

**October and November 2026, on Johnny's recent charts:**
- **Caught (9):**
  - 13, 16 and 20 Oct (up);
  - 4 Nov (up);
  - 6 Nov (down, 83 pips);
  - 9 Nov (up);
  - 11, 12 and 18 Nov (down).
- **Missed (4):**
  - 2 Oct (up from 13:00, no signal);
  - 6 Oct (up, signal down);
  - 7 Oct (down all day, no signal);
  - 10 Nov (down from 11:00, 115 pips, no signal).
- **False alarms (10):**
  - 8, 26, 27, 28 and 29 Oct (signal down);
  - 9 Oct (signal down, +0.7);
  - 5 Nov (signal down, +1.6);
  - 30 Oct, 2 Nov and 17 Nov (signal up).

### Extra information only (not a rule): the slow grind trade had to reach +5, +10 or +15 by 09:00

| Signal needs | Signal days | Trend day its way | Trend day the other way | Not a trend day | Trend days caught (of 223) | Missed: no signal / both / wrong way |
|---|---|---|---|---|---|---|
| In profit (Johnny) | 341 | 101 (30%) | 17 | 223 | 101 (45%) | 102 / 3 / 17 |
| +5 | 270 | 89 (33%) | 14 | 167 | 89 (40%) | 120 / 0 / 14 |
| +10 | 203 | 76 (37%) | 7 | 120 | 76 (34%) | 140 / 0 / 7 |
| +15 | 138 | 59 (43%) | 2 | 77 | 59 (26%) | 162 / 0 / 2 |

A higher bar makes the signal right more often when it turns on, from 30% to 43%, and almost never the wrong way. But it catches fewer trend days, from 45% down to 26%.

### With the stricter or looser measure (Johnny's rule)

| Measure | Trend days | Signal days that were a trend day its way (of 341) | Trend days caught |
|---|---|---|---|
| Looser (6+ hours, 40+ pips) | 338 | 139 (41%) | 139 (41%) |
| Used (8+ hours, 40+ pips) | 223 | 101 (30%) | 101 (45%) |
| Stricter (10+ hours, 50+ pips) | 118 | 63 (18%) | 63 (53%) |

## Data and limits

- **Candles:** the same research store as the earlier study (`data/research/stp_validation_store`, read only):
  - 2024–25: vendor tick prices, close to IG's;
  - Jan to 24 Oct 2026: IG mid;
  - 25 Oct 2026 on: the bot's own IG candles.

  There is no data for 1–22 March 2026. 5 and 6 October were checked against IG's own hourly candles in the bot's store.
- **Days measured:** weekdays with at least 14 of the 15 session hours. Days used in Step 2: those also usable in the earlier study (703).
- **What "trend day" here is, and isn't:** the measure is Claude's reading of Johnny's words, and its cut-offs come from his four catchable days. It describes the whole day after the fact (it needs the day's hours up to 20:30), so it can't be used live.
- **Entries:** taken at the start of their candle, as in the earlier study.

## Files (`retest/`)

- `daystats.py`: the 5-minute bands and EMAs per day, for the 5 October check.
- `trendday.py`: the measure.
- `step2.py` and `step2.txt`: the signal against the measure, at all four thresholds.
- `examples.py` and `examples.txt`: Johnny's days, the random draws, October–November 2026, the overlap and chance checks.
- `days_trend_measure.csv`: every day, with the measure's parts, the signal and each side's best profit from 06:00 to 09:00.
