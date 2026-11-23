# Are trends that start after 09:00 UK news-driven? (23 November 2026)

Research only. Nothing in the live bot, its code or its settings was changed. Server: the new AutoBot server,
/opt/autobot (not AutoBot 161). The script and its outputs are in `retest/` (`news_trends.py`, `news_trends.txt`,
`news_trends_late_trend_days.csv`).

## The answer in brief

- **Some are, most are not, as far as the calendar can show.** There were 110 trend days whose run started at
  09:00 or later. A big or medium GBP or USD release came out before the run, or inside its first hour, on **43 of
  them (39%)**.
  - On the other 67, no such release came first. 34 had no big or medium release all day. On 33 the day's
    releases only came out after the trend had already started.
- **When a release did come first, it was usually right at the start.** On 25 of the 43, the release fell inside the
  run's first hour, nearly always US data at 13:30 with the run starting at 13:00. On 17 of the 43 the run began 1 to
  6 hours after the release.
- **Right at the start, the result pointed the right way.** Of those 25, 19 had a reading (actual against forecast).
  **16 of the 19 matched** the trend's direction. When the run began an hour or more after the release, only 3 of 10
  matched. Over all 43, 29 had a reading and 19 matched (66%).
- **The other way round, a big release usually does not make a trend day.** 172 days had a big release between
  06:00 and 13:59. **31 (18%) became a trend day after it.** On 34 a trend was already under way, and 107 (62%)
  were not trend days.
  - Big-release days are a little more often trend days than other days: 65 of 172 (38%), against 156 of 516 (30%)
    on days with no big release.

So the picture is: big US data at 13:30 can start a trend, and when it does the trend usually goes the way the
figure surprised. But most late-starting trends had no calendar release behind them, and most big releases didn't
start one.

## What was measured

**Trend days.** The re-test's measure, unchanged (`RETEST.md`). On the hourly chart, 8 or more of the 15 session
hours (06:00 to 20:00 UK) in a row work one Bollinger band, with no touch of the other band in that run and at least
40 pips in the run. Its cut-offs were set on 9, 11, 12 and 18 Nov.
- **6 October in place of 5 October.** 6 Oct passes the same cut-offs (up, 13 hours from 08:00, 69 pips), so nothing
  had to change.
- 6 Oct's run started at 08:00, so it isn't one of the "09:00 or later" days. Of Johnny's days, only 12 Nov is.
- Over 8 Jan 2024 to 19 Nov 2026 there are 713 measured weekdays and 227 trend days. **110 of the trend days had a
  run that started at 09:00 or later:**

  | Run started | 09:00 | 10:00 | 11:00 | 12:00 | 13:00 |
  |---|---|---|---|---|---|
  | Days | 26 | 14 | 18 | 20 | 32 |

- **The measure can't see a trend that starts after 13:00.** It needs 8 hours in a row ending by the 20:00 candle.
  So a release at 14:00 or later (ISM at 15:00, Fed decisions and minutes at 18:00 or 19:00) can never be followed
  by a trend day here. That matters for question 5.
- **Run start is to the hour.** It is the hour of the run's first hourly candle, so a 13:00 run includes 13:30 data.

**News.** The bot's own news table (`config/news_table.toml`, read the way the live bot reads it), applied to
Finnhub's past calendar, as the earlier study did. GBP and USD releases only.
- **Big and medium:** only releases Finnhub marks as high impact can be big or medium. Everything else is small.
- **The calendar:** Finnhub's past calendar (`data/research/news/finnhub_calendar.json`) was fetched on 10 Nov, so
  it has no actual figures after that date. From 1 Nov 2026 the bot's own calendar (`data/news/calendar.json`) is
  used instead.
- **"That day"** means a release from 00:00 to 20:30 UK.

**Which release counts for a trend (questions 2 and 3).** The last big or medium release before the run started, or
inside the run's first hour. If several came out at the same minute, they are taken together.

**Which way a result pointed (question 3).** Actual against forecast.
- **Good or bad:** higher than forecast is good for the currency. The exceptions are the bot's "lower is better"
  names: unemployment rate, jobless claims and claimant count.
- **Direction:** good for GBP or bad for USD means GBPUSD up. The reverse means down.
- **Several releases at once:** if they disagree, the bot's headline order decides (rate decision, then payrolls,
  then headline CPI, then core CPI).
- **No reading:** actual equal to forecast is "in line". A release with no actual or no forecast figure has no
  reading.

## 1. Big or medium release on the late-trend days

Over the **110** trend days whose run started at 09:00 or later:

| | Days |
|---|---|
| A big release that day | 38 |
| A medium release but no big one | 38 |
| **No big or medium release** | **34** |

But a release only counts as a cause if it came out before the trend started:

| | Days |
|---|---|
| **Release before the run, or inside its first hour** | **43** (big 20, medium 23) |
| Releases that day, but only after the run's first hour | 33 |
| No big or medium release at all | 34 |

**The 43 by release time (UK):**

| Time | Releases | Days |
|---|---|---|
| 13:30 | US data: payrolls, CPI, PPI, retail sales, durable goods, GDP, PCE | 21 |
| 07:00 | UK data: CPI, unemployment, GDP, retail sales | 14 |
| 09:30 | UK flash PMIs | 5 |
| 12:00 | Bank of England rate decision | 2 |
| 12:30 | US data, in the weeks when US and UK clocks differ | 1 |

Every one of the 110 days, with its releases, is in `retest/news_trends_late_trend_days.csv`.

## 2. How long after the release the trend run started

For the 43 days with a release first. A run's start is its first hourly candle, so "inside the first hour" means
the release came out during that candle (for example a 13:30 release and a run from 13:00).

| Release to run start | Days | Big | Medium |
|---|---|---|---|
| Release inside the run's first hour | **25** | 12 | 13 |
| Run started up to 59 minutes after | 1 | 1 | 0 |
| 1 to 2 hours after | 4 | 3 | 1 |
| 3 to 5 hours after | 12 | 3 | 9 |
| 6 hours after | 1 | 1 | 0 |

**The two groups.** The times bunch into two groups:
- **Within the hour:** almost all 13:30 US data with a 13:00 run.
- **3 to 6 hours later:** mostly a 07:00 UK release with a run starting 10:00 to 13:00. These are the doubtful ones.
  A trend starting 4 or 5 hours after a release may not be about that release at all.

**Did the move start before or after the release?** For the 25 runs whose first hour held the release, I looked at
5-minute candles:
- **18 of 25 had made less than 10 pips** the trend's way before the release came out.
- **On these the trend began at the release, not before.** For example: 10 Apr 2024 made 1 pip before US CPI, then
  174 in the run; 17 Jun 2025 made 3 pips before US retail sales, then 139.
- **The clearest exception is 26 Nov 2025:** 41 of its 57 pips came before the 13:30 data.

## 3. Did the trend go the way the result pointed?

Of the 43 days with a release first:
- **29 had a reading. 19 matched the trend's direction (66%) and 10 didn't.**
- 14 had no reading:
  - 7 were in line with forecast;
  - 6 had no actual figure in Finnhub's data (5 of them UK flash PMIs);
  - on 1 the releases at that minute disagreed with no headline to decide.

| | Matched | Of |
|---|---|---|
| **Release inside the run's first hour** | **16** | **19** |
| Run started 1 to 6 hours after the release | 3 | 10 |
| Big release | 12 | 16 |
| Medium release | 7 | 13 |

**Close to the release, the result predicts the direction well (16 of 19). Hours later, it doesn't (3 of 10).**

**Matched, within the hour, for Johnny's chart:**
- Fri 2 Feb 2024: US payrolls 353k against 180k forecast, down from 13:00, 143 pips.
- Wed 10 Apr 2024: US CPI 0.4% against 0.3%, down from 13:00, 174 pips.
- Fri 2 Aug 2024: US payrolls 114k against 175k, up from 13:00.
- Wed 11 Jun 2025: US CPI 0.1% against 0.2%, up from 13:00.
- Fri 7 Aug 2026: US payrolls −23k against 80k, up from 13:00.
- Fri 2 Oct 2026: US payrolls 29k against 90k, up from 13:00.

**The 10 that didn't match:**

| Day | Trend | Release (UK) | Result | Pointed | Gap |
|---|---|---|---|---|---|
| Fri 24 May 2024 | up from 10:00, 46 pips | 07:00 GBP retail sales (medium) | −2.3% vs −0.4% | down | 3 h |
| Thu 12 Sep 2024 | up from 13:00, 81 pips | 13:30 USD PPI (medium) | 0.2% vs 0.1% | down | in first hour |
| Fri 20 Dec 2024 | up from 12:00, 108 pips | 07:00 GBP retail sales (medium) | 0.2% vs 0.5% | down | 5 h |
| Wed 19 Feb 2025 | down from 09:00, 49 pips | 07:00 GBP CPI (big) | 3.0% vs 2.8% | up | 2 h |
| Tue 17 Jun 2025 | down from 13:00, 139 pips | 13:30 USD retail sales (medium) | −0.9% vs −0.7% | up | in first hour |
| Wed 26 Nov 2025 | up from 13:00, 57 pips | 13:30 USD durable goods (medium), with GDP and PCE (no actuals) | 0.5% vs 0.3% | down | in first hour |
| Thu 15 Jan 2026 | down from 10:00, 74 pips | 07:00 GBP GDP (medium) | 0.3% vs 0.1% | up | 3 h |
| Thu 16 Apr 2026 | down from 09:00, 44 pips | 07:00 GBP GDP (medium) | 0.5% vs 0.1% | up | 2 h |
| Tue 21 Jul 2026 | down from 11:00, 68 pips | 07:00 GBP unemployment (big) | 4.9% vs 5.0% | up | 4 h |
| Thu 12 Nov 2026 | down from 13:00, 46 pips | 07:00 GBP GDP (QoQ in line; MoM 0.2% vs 0.0%) | | up | 6 h |

Seven of the ten are a 07:00 UK release with the run starting 2 to 6 hours later. **12 Nov, Johnny's own day, is one
of them.** UK GDP beat at 07:00, but the trend down began at 13:00. No big or medium release came at that time.

## 4. Late-trend days with no big or medium release at all

**34 of the 110** (31%). A further 33 had releases only after the trend had started (for example 10 Nov 2026: down
from 11:00, with US CPI at 13:30).

**10 to check on the chart:**
- Tue 20 Feb 2024: up from 09:00, 81 pips.
- Tue 23 Apr 2024: up from 12:00, 108 pips.
- Wed 28 Aug 2024: down from 09:00, 64 pips.
- Mon 16 Dec 2024: up from 09:00, 60 pips.
- Mon 20 Jan 2025: up from 13:00, 147 pips.
- Mon 28 Apr 2025: up from 09:00, 137 pips.
- Wed 6 Aug 2025: up from 11:00, 70 pips.
- Tue 27 Jan 2026: up from 09:00, 195 pips.
- Mon 9 Feb 2026: up from 11:00, 91 pips.
- Mon 29 Jun 2026: up from 10:00, 55 pips.

All 34 are listed in `retest/news_trends.txt`.

**These are days with no calendar release, which doesn't mean no news.** Some of them clearly had news off the
calendar:
- 20 Jan 2025 was the US presidential inauguration;
- 2 and 7 Apr 2025 were the US tariff announcement and the sell-off after it.

Speeches, headlines and small-tier releases aren't counted here.

## 5. Days with a big release: did a trend follow?

There were **197 measured days with a big GBP or USD release between 06:00 and 20:30 UK.** They split by when the
day's first big release came out.

**First big release between 06:00 and 13:59: 172 days.**

| What followed | Days | Share |
|---|---|---|
| **A trend run began in or after the release's hour** | **31** | 18% |
| A trend day, but the run was already under way before the release | 34 | 20% |
| **Not a trend day** | **107** | 62% |

For the 31, the gap from release to run start:

| Release to run start | Days |
|---|---|
| Release inside the run's first hour | 12 |
| Run started up to 59 minutes after | 7 |
| 1 to 2 hours after | 6 |
| 3 to 5 hours after | 3 |
| 6 hours after | 3 |

**First big release at 14:00 or later: 25 days,** almost all Fed decisions and FOMC minutes at 18:00 or 19:00.
- None can be followed by a trend day on this measure, because a run starting after 13:00 can't reach 8 hours.
- 6 were trend days already under way, and 19 were not trend days.

**For comparison** (all 713 measured days):

| Days | Trend day | Run started 09:00 or later |
|---|---|---|
| A big release between 06:00 and 13:59 | 65 of 172 (38%) | 34 of 172 (20%) |
| No big release that day | 156 of 516 (30%) | 72 of 516 (14%) |

Big-release days are somewhat more likely to be trend days, but most of them aren't.

**By the day's first big release** (became a trend after it / already trending / not a trend day):

| Release | After | Already | Not |
|---|---|---|---|
| US payrolls | 7 | 6 | 21 |
| UK unemployment | 7 | 6 | 21 |
| UK CPI | 7 | 3 | 25 |
| US CPI | 3 | 8 | 16 |
| Bank of England decision | 2 | 7 | 10 |
| UK GDP (prelim) | 3 | 0 | 9 |
| US GDP (advance) | 2 | 4 | 5 |
| Fed decision, FOMC minutes, payroll revisions (late releases) | 0 | 6 | 19 |

**Became a trend day after the release (31 in all), a few:**
- Fri 2 Feb 2024: 13:30 US payrolls, down from 13:00.
- Fri 10 Jan 2025: 13:30 US payrolls, down from 13:00.
- Thu 5 Feb 2026: 12:00 BoE decision, down from 12:00.
- Fri 13 Feb 2026: 13:30 US CPI, up from 13:00.
- Fri 3 Apr 2026: 13:30 US payrolls, down from 13:00.
- Wed 17 Jun 2026: 07:00 UK CPI, down from 07:00.
- Fri 7 Aug 2026: 13:30 US payrolls, up from 13:00.
- Fri 2 Oct 2026: 13:30 US payrolls, up from 13:00.

**Big release, not a trend day (107 in all), a few:**
- Fri 7 Feb 2025: 13:30 US payrolls.
- Wed 12 Feb 2025: 13:30 US CPI.
- Thu 8 May 2025: 12:00 BoE decision.
- Fri 9 Jan 2026: 13:30 US payrolls.
- Wed 21 Jan 2026: 07:00 UK CPI.
- Fri 4 Sep 2026: 13:30 US payrolls.
- Wed 14 Oct 2026: 13:30 US CPI.
- Thu 5 Nov 2026: 12:00 BoE decision.
- Tue 17 Nov 2026: 07:00 UK unemployment.

**Big release, but the trend had already started (34 in all), a few:**
- Fri 4 Apr 2025: down from 07:00, before 13:30 payrolls.
- Fri 8 May 2026: up from 09:00, before 13:30 payrolls.
- Fri 6 Nov 2026: down from 06:00, before 13:30 payrolls.
- Wed 18 Nov 2026: down from 06:00, before 07:00 UK CPI.

All are listed in `retest/news_trends.txt`.

## Limits

- **The trend measure is Claude's reading of Johnny's words.** Its cut-offs come from his known days.
- **Time limits:**
  - run starts are to the hour;
  - the measure can't see trends that start after 13:00, so news at 14:00 and later can't be tested.
- **Calendar data:**
  - Finnhub's past data is missing some actual figures (UK flash PMIs in particular), so some days have no reading;
  - only GBP and USD releases count;
  - speeches, headlines and off-calendar events aren't counted.
- **Prices:** the same research store as the re-test. There is no data for 1 to 22 March 2026.
- **Small counts.** The strongest figure, 16 of 19 matching when the release falls in the run's first hour, rests
  on 19 days.

## Rerun

    cd research/2026-11-21_slow_grind_trend_day/retest
    python news_trends.py .
