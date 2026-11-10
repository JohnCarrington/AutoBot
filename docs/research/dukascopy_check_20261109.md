# Research data: Dukascopy, AutoBot 161's IG history, and IG's real spread

Started 9 November 2026, results 10 November 2026. Research only: nothing here changes live trading.

## Summary

- **Dukascopy's terms do not allow scripted downloading** without their written consent. On the owner's decision (10 November), **the Dukascopy data will be exported by hand** with Dukascopy's own export page. No script contacted Dukascopy's data server. The conversion code for those export files is written and tested. The Dukascopy checks (steps 3 and 4 for Dukascopy) run once the files are in `data/research/dukascopy/GBPUSD/` (see "Dukascopy: waiting for the export").
- **AutoBot 161's IG history** (2024 and 2025, 5-minute sell candles) was unpacked, checked and converted into the bot's own candle format: 149,526 5-minute, 12,468 hourly and 627 daily candles.
- **Two problems were found in 161's data.** (1) In the weeks when US and UK clocks are out of step, **161's times are one hour early**. The conversion corrects this, and the correction was proved against IG's own daily candles. (2) **161's data starts every week at 17:00 New York**, so in a normal week **it misses IG's first hour, Sunday 21:00 to 22:00 UK**. That hour cannot be recovered and is recorded as a gap (96 Sundays).
- **161 against IG's own daily candles** (360 days, November 2024 to December 2025): Monday to Thursday, outside Christmas, the sell prices are typically **0.2 to 0.3 points** apart and 95% are within **1.0 to 2.2 points**, but they match exactly on only about 1 day in 10. So 161's prices come from a very close IG price, not exactly the bot's. Sunday opens and Friday closes differ more (see below).
- **IG's real spread** (the bot's own buy and sell prices): **0.9 or 1.5 points** almost all day, **about 16 to 17 points through the 22:00 to 23:00 UK rollover hour**, and **18 to 19 points in the first hour after the Sunday 21:00 open**. A half-hour-of-the-week table for the research replays is below, and is also saved as `data/research/ig_spread/GBPUSD_spread_by_half_hour.csv`.

## What was and was not touched

- **No IG calls.** Nothing here imports the IG part or the history door. The price service was not restarted or stopped.
- **Nothing was written to `data/candles` or any other live folder.** The conversion refuses to write anywhere outside `data/research/`, and refuses the live candle store even if asked (tested). The bot's own candles were only read.
- **Every long job ran at the lowest priority:** `nice -n 19 ionice -c3` (the conversion took 31 seconds, the full test suite 7.7 minutes).
- **Nothing was downloaded from Dukascopy.** Their terms pages were read once each.
- Committed: this file, `research/` (the conversion and checks) and `tests/technical/test_research_candles.py`. No data is committed (`data/` is in `.gitignore`).

## 1. Dukascopy's terms of use

Read on 10 November 2026 from Dukascopy's "Terms & Conditions" page (`dukascopy.com/swiss/english/legal-pages/terms-of-use/`), their "Important Disclaimer" page and the Historical Data Export page. I found no separate licence for the historical data, so the general website terms apply. Section 4 also makes anything downloaded subject to them. This is a plain reading, not legal advice.

| Question | What the terms say |
|---|---|
| Own research use | Allowed: downloads are licensed "ONLY for your own personal, non-commercial use" (section 4). The export page itself names backtesting as a use. |
| Scripted downloading | **Not allowed without consent:** "You shall not use or attempt to use any 'scraper,' 'robot,' 'bot,' 'spider,' 'data mining' … to access, acquire, copy, or monitor any portion of the WEBSITE, any data or content … without the prior express written consent of DUKASCOPY" (section 3). Also no "unreasonable or disproportionately large load". No rate limit is published. |
| Sharing | Not allowed: no recirculating, redistributing or publishing without written consent, no resale or use "for the benefit of, any other person", and nothing that "could compete with the business of DUKASCOPY" (section 3). |
| Databases | "may not be used to construct a database of any kind", nor "stored … in databases for access by you or any third party" (section 3). Keeping files on our own server for our own research is not expressly covered either way. |
| Accuracy | No guarantee of "sequence, accuracy, completeness … or timeliness", including "quotes and financial data". Provided "AS IS". The export page warns of "changes in regular trading hours". |
| Login | Using the website "is free of charge and does not require to be a client of DUKASCOPY" (section 5). |
| If the terms end | "destroy promptly all materials obtained from the WEBSITE and any copies thereof" (section 10). |
| Law | Swiss law, arbitration in Geneva. The terms can change at any time. |

**What this means here:** the data stays on this server, for our own non-commercial research, and is never committed, shared or published. It is fetched by hand through Dukascopy's own export page, not by a script. Pushing this document is fine: it holds our own measurements, not Dukascopy's data.

## 2. AutoBot 161's IG history

- `data/research/ig161/gbpusd_5m_bid_2024_2025.tar.gz`: **sha256 matched** (`2e558ec1…9992ff`). Before unpacking, the archive was checked: 629 entries, only `README.md`, `GBPUSD/` and `GBPUSD/YYYY-MM-DD.csv`, and no links or odd paths. It was unpacked in that folder.
- **README:** GBPUSD 5-minute **bid** candles from AutoBot 161 (`/opt/tradingbot/data/candles_ext_v2/GBPUSD/`), IG points (`12718.40` = 1.27184), UTC times, one file per UTC date, 2024-01-01 to 2025-12-31, 627 files, 149,526 rows, columns `timestamp,open,high,low,close`.
- **Checked:** 149,526 rows as stated. Every time is UTC and on a 5-minute mark. There are no duplicates, every high and low holds the open and close, and every price has exactly two decimals with the second always 0, so each is a whole tenth of a point, as IG writes it.

### Problem 1: one hour early when US and UK clocks are out of step (corrected)

In the weeks when US clocks are on summer time and the UK's are not (from the second to the last Sunday of March, and from the last Sunday of October to the first Sunday of November), 161's week runs from Sunday 20:00 to Friday 20:00 UK. That is outside IG's hours: 94 of its candles fall before IG's open. Tested against IG's own daily candles for those weeks (24 days):

| 161's times in those weeks | open | high | low | close | 161 candles outside IG's hours |
|---|---:|---:|---:|---:|---:|
| as written: typical / largest gap to IG (points) | 5.8 / 12.3 | 0.4 / 8.4 | 0.2 / 17.7 | 4.0 / 11.9 | 94 |
| **moved one hour later** | **0.2 / 10.3** | **0.3 / 1.6** | **0.1 / 3.6** | **0.2 / 2.3** | **0** |

Moving all the other weeks by an hour, in either direction, makes them much worse (typical open and close gap 3.5 to 4.8 points instead of 0.3 to 0.4), so they are right as written. **The conversion moves the out-of-step weeks one hour later** (11,506 candles; `fix_161_out_of_step_weeks`). The files from 161 are left exactly as received.

### Problem 2: the first hour of each week is missing (recorded as gaps)

With problem 1 corrected, 161's data starts **every** week at Sunday 17:00 New York time. IG opens at **21:00 UK** (`docs/SETTINGS.md`; the bot's hourly IG candles from August to November 2026 start at 21:00 UK every Sunday). So in the normal weeks 161 misses 21:00 to 22:00 UK. IG did have prices in that hour in 2024 and 2025 too: IG's Sunday daily opens differ from 161's by a typical 4.8 points (up to 42.2), while Sunday closes agree (typical 0.2).

### The gaps (all recorded in `data/research/candles_ig161/GBPUSD/gaps.csv`)

| Size | Where | Runs | Candles |
|---|---|---:|---:|
| 5m | the week's open (Sunday 21:00 UK: 91 × 12 candles, 5 × 13, 1 × 1) | 97 | 1,158 |
| 5m | Christmas and New Year (IG closed or thin) | 29 | 689 |
| 5m | 21:00 to 00:00 UK, mostly single candles around the rollover | 18 | 67 |
| 5m | other whole hours | 4 | 48 |
| 1h | hours with no 5-minute candle at all (same causes) | 156 | 156 |
| 1d | none | 0 | 0 |

The whole hours missing outside the weekend are: Fri 19 Jan 2024 20:00 UTC; Mon 1 Apr 2024 and Mon 31 Mar 2025 00:00 to 01:00 UK (both the night after the UK clocks go forward, so probably another clock-change slip in 161's fetch); Fri 1 Nov 2024 19:00 UTC; and Thu 7 Nov 2024, every other hour from 17:00 to 00:00 UTC.

## 3. The conversion

`research/candles_convert.py` builds the candles **with the bot's own code and settings**: `prices.calendar.Boundaries` and `MarketHours` from `config/settings.toml`, so the days are UK midnight to midnight, with IG's short Sunday candle labelled Sunday 00:00 UK (21:00 to midnight, 36 parts) and Friday's ending at 17:00 New York. Each bigger candle takes the open of the first 5-minute candle, the highest high, the lowest low and the close of the last, buy and sell separately, with `parts` and `expected_parts`. The files use the store's exact columns, with one file per UTC date per size, and prices are written IG's way (1.33797 as 13379.7). Only 5-minute candles inside IG's market hours are kept.

- **161** → `data/research/candles_ig161/GBPUSD/` (5m, 1h, 1d, `gaps.csv`). It has sell prices only, so **the four buy columns are left empty**. The live `CandleStore` refuses such files, on purpose (tested).
- **Dukascopy** → `data/research/candles_dukascopy/GBPUSD/`, with buy (Dukascopy's ASK) and sell (BID). Those files read in the live `CandleStore`'s own reader (tested). A minute counts only if Dukascopy recorded ticks in it: their export pads quiet and closed minutes with flat zero-volume candles.

```
nice -n 19 ionice -c3 .venv/bin/python -m research.candles_convert ig161 \
    --src data/research/ig161/GBPUSD --out data/research/candles_ig161/GBPUSD
nice -n 19 ionice -c3 .venv/bin/python -m research.candles_convert dukascopy \
    --src data/research/dukascopy/GBPUSD --out data/research/candles_dukascopy/GBPUSD
```

## 4. Check: 161's sell prices against IG's

**Where both exist:** the bot holds IG's own daily candles from 7 November 2024, so 161 and IG overlap on **360 daily candles** (7 November 2024 to 31 December 2025). The bot's IG hourly candles (from 7 August 2026) and 5-minute candles (from 25 October 2026) start after 161's data ends, so those cannot be compared. Distances are 161 minus IG, in points (1 point = 0.0001 = 1 pip), after the problem 1 correction.

**By year**

| Year | Price | Days | Exact | Typical | 95% within | Largest | Average |
|---|---|---:|---:|---:|---:|---:|---:|
| 2024 (from 7 Nov) | open | 47 | 6 | 0.3 | 13.7 | 17.9 | +0.73 |
| | high | 47 | 4 | 0.4 | 5.8 | 7.0 | +0.34 |
| | low | 47 | 7 | 0.1 | 7.9 | 18.0 | +0.64 |
| | close | 47 | 6 | 0.3 | 4.1 | 15.7 | −0.25 |
| 2025 | open | 313 | 21 | 0.4 | 7.0 | 42.2 | −0.22 |
| | high | 313 | 27 | 0.3 | 2.0 | 12.0 | +0.28 |
| | low | 313 | 34 | 0.3 | 6.1 | 17.2 | +0.72 |
| | close | 313 | 29 | 0.3 | 3.5 | 21.6 | +0.04 |

**By day of the week**

| Days | Price | Days | Exact | Typical | 95% within | Largest |
|---|---|---:|---:|---:|---:|---:|
| Mon–Thu, outside 24 Dec–1 Jan | open | 230 | 23 | 0.3 | 1.0 | 5.6 |
| | high | 230 | 24 | 0.2 | 1.0 | 4.6 |
| | low | 230 | 33 | 0.2 | 2.2 | 5.0 |
| | close | 230 | 25 | 0.3 | 1.0 | 6.1 |
| Friday | open / high / low | 60 | 4–5 | 0.2–0.3 | 1.0–2.7 | 3.5–7.9 |
| | **close** | 60 | **0** | **1.9** | 6.0 | 21.6 |
| Sunday | **open** | 60 | 0 | **4.8** | 17.9 | 42.2 |
| | high | 60 | 2 | 0.6 | 6.3 | 7.4 |
| | **low** | 60 | 1 | **4.1** | 10.2 | 18.0 |
| | close | 60 | 10 | 0.2 | 1.0 | 1.1 |

**Largest differences:** Sun 11 May 2025, open −42.2 (161 has 24 of 36 Sunday candles); Thu 25 Dec 2025, open −24.9 (99 of 288); Fri 11 Apr 2025, close −21.6; Sun 16 Nov 2025, open −21.5; Sun 20 Apr 2025, open −18.1; Tue 24 Dec 2024, close −15.7. Almost all of these are the missing Sunday hour, Christmas, or a Friday close.

**Reading it:**

- On ordinary weekdays 161 is within a fraction of a point of IG, but exact on only about 10% of days. It is good enough for research on moves of several points. It is not a copy of the bot's own prices: a different IG price source (perhaps a different epic or account type) is the likely reason, but that is not proven.
- **Sunday:** the missing 21:00 hour shifts the open, and the low (IG's widest, thinnest hour). Research on the Sunday open should not use 161.
- **Friday close:** IG's daily close differs from 161's last candle by a typical 1.9 points and never matches, though Friday's other prices agree. This is not explained yet. Research that holds trades into the Friday close should not trust 161's last minutes.

## 5. IG's real spread

From the bot's own IG prices: buy minus sell at each candle's open and close (two real moments per candle; the highs and lows are not used, because the buy high and the sell high need not happen at the same moment). Rows are **UK time in a normal week**. IG's rollover follows New York time (17:00 New York), so in the out-of-step weeks it falls at 21:00 UK. Those weekdays' samples are moved one hour later (that was the week of 26 to 30 October). Sunday stays on UK time, because the open follows UK time.

### By hour of the day

| UK hour | 5-min, 25 Oct–10 Nov: typical | 90% | largest | samples | hourly, 7 Aug–23 Oct: typical | 90% | largest | samples |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 00:00 | 1.5 | 1.5 | 2.6 | 264 | 0.9 | 1.5 | 6.5 | 110 |
| 01:00 | 1.5 | 1.5 | 2.2 | 288 | 0.9 | 1.5 | 6.5 | 112 |
| 02:00 | 1.5 | 1.5 | 2.3 | 288 | 0.9 | 0.9 | 1.5 | 112 |
| 03:00 | 1.5 | 1.5 | 1.5 | 288 | 0.9 | 0.9 | 1.5 | 112 |
| 04:00 | 1.5 | 1.5 | 1.9 | 288 | 0.9 | 0.9 | 1.5 | 112 |
| 05:00 | 1.5 | 1.5 | 1.5 | 288 | 0.9 | 0.9 | 1.5 | 112 |
| 06:00 | 1.5 | 1.5 | 2.5 | 288 | 0.9 | 1.5 | 11.4 | 112 |
| 07:00 | 0.9 | 1.5 | 2.2 | 288 | 0.9 | 1.5 | 16.0 | 112 |
| 08:00 | 0.9 | 1.5 | 1.9 | 288 | 0.9 | 0.9 | 1.5 | 112 |
| 09:00 | 0.9 | 1.5 | 2.8 | 288 | 0.9 | 0.9 | 1.5 | 112 |
| 10:00 | 0.9 | 1.5 | 1.6 | 288 | 0.9 | 0.9 | 1.4 | 112 |
| 11:00 | 0.9 | 1.5 | 7.9 | 288 | 0.9 | 0.9 | 4.9 | 112 |
| 12:00 | 0.9 | 1.5 | 13.5 | 288 | 0.9 | 0.9 | 16.0 | 112 |
| 13:00 | 0.9 | 1.5 | 15.7 | 288 | 0.9 | 0.9 | 1.5 | 112 |
| 14:00 | 0.9 | 1.5 | 8.5 | 286 | 0.9 | 1.5 | 8.9 | 112 |
| 15:00 | 0.9 | 1.5 | 8.7 | 264 | 0.9 | 1.9 | 10.4 | 112 |
| 16:00 | 0.9 | 1.5 | 1.5 | 264 | 0.9 | 0.9 | 1.5 | 112 |
| 17:00 | 0.9 | 1.5 | 1.5 | 264 | 0.9 | 0.9 | 1.5 | 112 |
| 18:00 | 0.9 | 1.5 | 7.1 | 264 | 0.9 | 0.9 | 16.0 | 112 |
| 19:00 | 1.5 | 1.5 | 6.2 | 264 | 0.9 | 0.9 | 16.0 | 112 |
| 20:00 | 0.9 | 1.5 | 1.5 | 264 | 0.9 | 0.9 | 1.5 | 112 |
| **21:00** (Sunday open in it) | 1.5 | 17.7 | 26.9 | 324 | 4.9 | 19.0 | 26.9 | 134 |
| **22:00** (rollover) | **16.0** | 16.9 | 24.6 | 288 | **16.9** | 16.9 | 25.0 | 110 |
| 23:00 | 1.8 | 2.9 | 16.9 | 288 | 4.4 | 16.9 | 21.9 | 110 |

- IG's spread moves in steps: **0.9** (the normal daytime spread), **1.5**, and about **16 to 17** at the rollover. The rollover lasts the whole 22:00 hour and part of 23:00.
- **Overnight (00:00 to 07:00 UK) it was typically 1.5 in November but 0.9 from August to October.** Whether that is the season or a change by IG is not known yet. The hourly figures are also only from each hour's first and last moments, and the 5-minute ones cover just over two weeks.
- The occasional 8 to 16 point spreads during the day come mostly between 11:00 and 15:00 UK. They have not been checked against the news calendar yet.

### Table for the research replays: IG's typical spread for each half hour of the week

Typical / 90% (points), from the bot's 5-minute IG candles, Sunday 25 October to Tuesday 10 November 2026: 24 to 36 samples per half hour (two or three weeks). The same table, with largest and smallest, is in `data/research/ig_spread/GBPUSD_spread_by_half_hour.csv` (`uk_half_hour_normal_week,samples,typical_points,p90_points,largest_points,smallest_points`). **To use it in a replay:** look up the candle's UK half hour, moving it one hour later on the weekdays of an out-of-step week. Use "typical" for the normal cost and "90%" for a cautious one.

| UK time | Sun | Mon | Tue | Wed | Thu | Fri |
|---|---:|---:|---:|---:|---:|---:|
| 00:00 |  | 1.5 / 1.5 | 1.5 / 2.3 | 1.5 / 2.3 | 1.5 / 1.5 | 1.5 / 1.5 |
| 00:30 |  | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 |
| 01:00 |  | 0.9 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 |
| 01:30 |  | 0.9 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 |
| 02:00 |  | 0.9 / 1.5 | 1.5 / 1.5 | 1.5 / 2.1 | 1.5 / 1.5 | 1.5 / 1.5 |
| 02:30 |  | 0.9 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 |
| 03:00 |  | 0.9 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 |
| 03:30 |  | 0.9 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 0.9 / 1.5 | 1.5 / 1.5 |
| 04:00 |  | 0.9 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 0.9 / 1.5 | 1.5 / 1.5 |
| 04:30 |  | 0.9 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 |
| 05:00 |  | 0.9 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 |
| 05:30 |  | 0.9 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 |
| 06:00 |  | 0.9 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 |
| 06:30 |  | 0.9 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 |
| 07:00 |  | 0.9 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 0.9 / 1.5 | 1.5 / 1.5 |
| 07:30 |  | 0.9 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 0.9 / 1.5 |
| 08:00 |  | 0.9 / 1.5 | 0.9 / 1.5 | 1.5 / 1.5 | 0.9 / 1.5 | 1.5 / 1.5 |
| 08:30 |  | 0.9 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 0.9 / 1.5 |
| 09:00 |  | 0.9 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 |
| 09:30 |  | 0.9 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 0.9 / 1.5 | 1.5 / 1.5 |
| 10:00 |  | 0.9 / 1.5 | 0.9 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 0.9 / 1.5 |
| 10:30 |  | 0.9 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 0.9 / 1.5 |
| 11:00 |  | 0.9 / 1.5 | 1.5 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 |
| 11:30 |  | 0.9 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 |
| 12:00 |  | 0.9 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 0.9 / 1.5 |
| 12:30 |  | 0.9 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 0.9 / 1.5 |
| 13:00 |  | 0.9 / 1.5 | 1.5 / 1.5 | 1.5 / 2.2 | 1.5 / 1.5 | 1.5 / 1.5 |
| 13:30 |  | 0.9 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 |
| 14:00 |  | 0.9 / 1.5 | 0.9 / 1.5 | 1.5 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 |
| 14:30 |  | 0.9 / 1.5 | 1.5 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 | 1.5 / 1.5 |
| 15:00 |  | 0.9 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 |
| 15:30 |  | 0.9 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 | 0.9 / 0.9 |
| 16:00 |  | 1.5 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 |
| 16:30 |  | 1.5 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 |
| 17:00 |  | 1.5 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 | 1.5 / 1.5 | 0.9 / 1.5 |
| 17:30 |  | 0.9 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 | 1.5 / 1.5 | 0.9 / 1.5 |
| 18:00 |  | 0.9 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 | 1.5 / 1.5 | 0.9 / 1.5 |
| 18:30 |  | 0.9 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 | 1.5 / 1.5 |
| 19:00 |  | 1.5 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 |
| 19:30 |  | 1.5 / 1.5 | 0.9 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 | 0.9 / 1.5 |
| 20:00 |  | 1.0 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 |
| 20:30 |  | 0.9 / 1.5 | 1.5 / 1.5 | 0.9 / 1.5 | 1.5 / 1.5 | 0.9 / 1.5 |
| 21:00 | **18.4 / 26.0** | 1.5 / 1.5 | 0.9 / 1.5 | 0.9 / 1.5 | 1.5 / 1.5 | 1.5 / 1.5 |
| 21:30 | **19.0 / 21.8** | 1.5 / 3.6 | 1.5 / 3.8 | 1.5 / 5.7 | 1.5 / 4.1 | 1.5 / 2.4 |
| 22:00 | **10.7 / 16.9** | **16.9 / 16.9** | **16.9 / 16.9** | **16.0 / 16.9** | **16.0 / 16.9** | closed |
| 22:30 | **9.3 / 16.9** | **14.9 / 16.9** | **13.7 / 16.9** | **16.9 / 16.9** | **14.5 / 16.9** | closed |
| 23:00 | 1.5 / 3.9 | 2.4 / 5.2 | 2.4 / 6.3 | 2.4 / 3.7 | 2.4 / 4.9 | closed |
| 23:30 | 0.9 / 1.5 | 1.5 / 2.7 | 2.1 / 2.4 | 2.4 / 2.4 | 2.4 / 2.4 | closed |

**Limits:** two to three weeks, all in late autumn, so each half hour is backed by 2 or 3 days. Most half hours flip between 0.9 and 1.5, so the typical value of a single half hour should not be read too finely. A replay could fairly use 0.9 for 07:00 to 21:00 and 1.5 overnight. The rollover, the Sunday open and the 23:00 tail are the parts that matter, and they are clear. This table should be rebuilt as the bot's store grows (the code is `research.dukascopy_check.spread_by` with `half_hour_of_normal_week`).

## 6. Dukascopy: waiting for the export

The folder `data/research/dukascopy/GBPUSD/` is ready and empty. **What to export** from Dukascopy's Historical Data Export page (`dukascopy.com/swiss/english/marketwatch/historical/`):

- Instrument **GBP/USD**, timeframe **1 minute**, **both BID and ASK** (one file each).
- Dates **10 November 2023 to 9 November 2026** (or whatever splits the page allows; several files per side are fine, and overlapping files are checked against each other).
- Time zone **GMT/UTC** (not local time). Files whose times are not marked GMT/UTC are refused rather than guessed.
- Format **CSV**, with volume. Flats filtered or not: both work.
- Keep Dukascopy's file names: the reader works out BID or ASK from the name, for example `GBPUSD_Candlestick_1_M_BID_10.11.2023-09.11.2026.csv`.

**Then, with no further decision needed:** convert into `data/research/candles_dukascopy/GBPUSD/` (gaps recorded), and compare Dukascopy's sell prices with 161 (2024 and 2025, 5-minute, hourly and daily) and with the bot's IG candles (5-minute from 25 October, hourly from 7 August, daily from 7 November 2024). This shows the typical and largest distances by year, compares Dukascopy's spread with IG's by hour of the day, including the 22:00 rollover and the Sunday open, and adds the results to this document. The code for all of this is written and tested (`research/candles_convert.py`, `research/dukascopy_check.py`).

## 7. Folder sizes (10 November 2026)

| Folder | Size |
|---|---:|
| `data/research/dukascopy/GBPUSD/` | empty (waiting for the export) |
| `data/research/ig161/` (archive 1.6 MB + unpacked 11 MB) | 12 MB |
| `data/research/candles_ig161/GBPUSD/` (1,880 files) | 18 MB |
| `data/research/candles_dukascopy/GBPUSD/` | not built yet |
| `data/research/ig_spread/` | 12 KB |
| `data/research/` in all | 30 MB |

## 8. Code and tests

- `research/candles_convert.py`: reads 161's files and Dukascopy's export files, applies the 161 correction, builds 5m, 1h and 1d candles with the bot's `Boundaries`, records gaps, and writes only under `data/research/`.
- `research/dukascopy_check.py`: sell-price distances by year and by day, and spread by hour and by half hour of the week. Read-only.
- `tests/technical/test_research_candles.py` (17 tests): IG's way of writing prices; reading 161 (UTC only, high and low hold open and close); the out-of-step correction; UK-midnight days with the short Sunday candle, 36 of 36, and the summer day in the previous UTC date's file; sell-only files refused by the live store; buy and sell built apart; gaps recorded, with the weekend not a gap; candles outside market hours not kept; **refuses the live candle store and anywhere outside `data/research/`**; Dukascopy export files (zero-volume minutes skipped, GMT only, BID or ASK from the name, bad rows refused); the comparison and spread tables. The full suite passed: 1,780 tests before the last changes, and the 17 research tests after them. The commit hook runs everything again.
