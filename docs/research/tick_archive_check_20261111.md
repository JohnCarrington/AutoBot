# 161's tick archive (2024 to March 2026): its time zones, how close it is to IG, and how to use it

Wednesday 11 November 2026, UK. Read-only research: **nothing in the live bot was changed**. There were no IG calls and no restart, and nothing was written outside `data/research/`. No tick replay was built. The data is not committed.

## Summary

- **The archive is as sent.** `data/research/ig161/gbpusd_ticks_2024_2026.tar.gz` has the expected sha256 (`44dbee9c…3fb68`). It holds 705 plain files and nothing else: no links, and no absolute or `..` paths. They are a README and 704 daily `.npy` files, 1 January 2024 to 31 March 2026. It was unpacked into a new folder, `data/research/ig161/ticks_2024_2026/` (1.2 GB), and read without numpy or pickle (the header is checked: float64, 3 columns). It holds **53,008,350 ticks** (bid and ask). The README says "approximately 53.8 million". None of the ticks is out of time order.
- **The README's time zones are wrong.** The README says the files are already true UTC for 2024, 2025 and 8 to 31 March 2026, and 5 hours ahead of UTC from 1 January to 7 March 2026. Measured against IG, **the timestamps are New York time written as UTC**: 5 hours behind in winter and 4 hours behind during US summer time, changing on the US dates. The exception is that **2026 stays 5 hours behind all through March**, with no summer-time change on 8 March.

  | File dates | Add to the file's timestamp to get UTC | How it was found |
  |---|---:|---|
  | 1 January to 8 March 2024 | +5 h | 5-minute candles: the best fit on every day |
  | 10 March to 1 November 2024 | +4 h | the same |
  | 3 November 2024 to 7 March 2025 | +5 h | the same, and IG's own daily candles |
  | 9 March to 31 October 2025 | +4 h | the same |
  | 2 November 2025 to 31 March 2026 | +5 h | the same to 26 February; IG's daily candles 1 to 22 March (+5 on 9 of 10 weekdays from 9 March); IG's 5-minute mid 23 to 31 March |

  On each day the best shift matched IG with a median gap of 0.0 pips, and the next best was 4 to 7 pips off. There is no doubt about it.

- **161's "IG" 5-minute candles for 2024, 2025 and January to February 2026 were built from these same ticks.** Candles built from the ticks match them exactly: all four prices of **every one** of the 149,526 candles of 2024 and 2025, and the open and close of every candle in January and February 2026. A different source cannot match IG that closely. Against **IG's own prices**, 161's 2024–2025 daily candles are off by exactly as much as the ticks, month by month. So those candles, and the earlier long replays run on them (`long_replay_20261110.md`, `early_day_type_20261111.md`), use **this vendor's prices, not IG's**. They are close to IG (below), but not exact.

- **How close the ticks are to IG.** Measured only against IG's own prices: IG's daily candles from the bot's long history fill (November 2024 to March 2026, bid), and IG's 5-minute mid from 23 to 31 March 2026.
  - **Daily bid prices:** typically **0.2 to 0.5 pips** off by month, **0.3** overall. 90% are within 1.3 to 5 pips, and only 8% are exact. The worst, 7 to 42 pips, are Sunday open candles and holidays (1 January, 24 and 25 December), when the market is thin and the two sources start at different moments.
  - **5-minute mid, 23 to 31 March 2026:** typically **0.5 pips** off, 90% within 0.85, worst 8.2. The gaps are not one-sided: the median is −0.1, and 52% are below IG. The 5-minute **change** in price differs by 0.35 pips typically (90% within 1.25). Every hour is like this except the rollover hour, 21:00 to 22:00 UK, which is typically 0.9 off with 90% within 4.5.
- **Their spread is about half IG's or less, except in London hours.** Measured at each 5-minute close:
  - **London hours (07:00 to 18:00 UK):** the ticks' spread is typically 0.6 to 0.8 pips. The bot's live IG spread is 0.9 (1.5 at 09:00 and 13:00), about 1.3 times wider.
  - **Overnight:** the ticks are 0.7 to 0.9 against IG's 1.5, about 1.9 times.
  - **The 21:00 and 22:00 rollover:** the ticks are 0.9 and 3.5 to 6.0 against IG's 4.5 and 14.6, two to five times.
  - The ticks' spread hardly changed from 2024 to 2026.

- **Verdict: close enough to use for the path of price inside each candle, but not for the cost.**
  1. **The path of price: yes.** Use the ticks' **mid** for the order in which a candle reached its high and low, and whether a stop or take profit was touched first. It is unbiased and typically half a pip from IG's. That is far below the 12 to 50-pip stops and targets, and the 5-minute moves agree to about a third of a pip. Two cautions:
     - a decision that turns on a tenth of a pip at a level will sometimes come out differently;
     - the rollover hour (21:00 to 22:00 UK) and Sunday opens are less reliable.
  2. **The cost: IG's spread table, not their own spreads.** Their spread is IG's divided by 1.3 in London hours and by 2 to 5 overnight and at the rollover. A replay on their own buy and sell prices would make every trade look cheaper than IG, worst of all for trades opened or stopped outside London hours.
     - So build the buy and sell prices as **tick mid ± half IG's typical spread for that half hour of the week** (`data/research/ig_spread/GBPUSD_spread_by_half_hour.csv`, the bot's own IG prices). That is the way 161's 2026 mid candles were turned into IG prices.
     - Against IG's own daily bid it is as close as the ticks' own bid (typically 0.3 to 0.5 pips either way; table below), and it charges IG's cost.
     - The table holds IG's typical spread in a normal week (from October and November 2026). It does not know IG's wider spreads around big news, so news-time costs would still be understated.
  3. **The time zone must be corrected first**, by the table above, not by the README's rule. Read the README's rule (or 161's `tz.py`) and 2024–2025 would be 4 to 5 hours wrong.

## How it was done

- **Ticks to candles.** Each tick's bid and ask (raw price × 10,000 = IG points) went into 5-minute buckets on the files' own timestamps, keeping the open, high, low and close of the bid and the ask, and the spread at the last tick. A whole-hour time-zone shift then moves every bucket by exactly 12, so each shift could be tested without re-reading the ticks.
- **Time zone.** For each day, every shift from −6 to +6 hours was tried. The 5-minute closes built from the ticks were compared with 161's 5-minute candles: bid for 2024–2025, and mid for 2026. 161's January and February 2026 mid labels were moved 5 hours later, as found in `ig161_mid_2026_20261110.md`. The shift with the smallest median gap won. The same was done against IG's own daily candles, which cannot place a change to the exact day (midnight is quiet), but agree on winter and summer and are the only reference for 1 to 22 March 2026.
- **Against IG.** IG's own prices are:
  - IG's daily candles in the bot's store from November 2024 (the long history fill: `parts` 0, never built by the bot), bid;
  - 161's 2026 mid candles from 23 March, which matched the bot's IG prices exactly where both exist (`ig161_mid_2026_20261110.md`).
  
  The ticks were compared with these only.
- **Spreads.** The ticks' spread at each 5-minute close, against the bot's own IG candles (buy close minus sell close) from 25 October to 11 November 2026, by UK hour. The two periods do not overlap, since the archive ends on 31 March 2026.
- The scripts, the 5-minute candles built from the ticks and every check's output are in `data/research/tick_check_20261111/`. The ticks are in `data/research/ig161/ticks_2024_2026/`. Neither is committed.

## Results

### Against IG's own daily candles, by month (bid; days midnight to midnight UK)

"Typical" is the median gap over the open, high, low and close of each day, in pips. "Worst" is the largest, with its day.

| Month | IG daily candles | Ticks vs IG: typical / 90% / worst (day) | Ticks: prices exact | 161's daily vs IG: typical / worst | 161: prices exact |
|---|---:|---|---:|---|---:|
| 2024-11 | 20 | 0.3 / 3.3 / 18.0 (10 Nov) | 12% | 0.3 / 18.0 | 12% |
| 2024-12 | 27 | 0.3 / 3.4 / 15.7 (24 Dec) | 12% | 0.3 / 15.7 | 12% |
| 2025-01 | 27 | 0.2 / 3.2 / 10.9 (19 Jan) | 13% | 0.2 / 10.9 | 13% |
| 2025-02 | 24 | 0.2 / 3.0 / 17.2 (02 Feb) | 15% | 0.2 / 17.2 | 15% |
| 2025-03 | 26 | 0.8 / 9.9 / 12.9 (27 Mar) | 11% | 0.2 / 10.3 | 15% |
| 2025-04 | 26 | 0.3 / 2.9 / 21.6 (11 Apr) | 12% | 0.3 / 21.6 | 12% |
| 2025-05 | 26 | 0.2 / 3.0 / 42.2 (11 May) | 14% | 0.2 / 42.2 | 14% |
| 2025-06 | 26 | 0.3 / 2.4 / 16.4 (01 Jun) | 8% | 0.3 / 16.4 | 8% |
| 2025-07 | 27 | 0.4 / 2.9 / 6.9 (20 Jul) | 4% | 0.4 / 6.9 | 4% |
| 2025-08 | 26 | 0.5 / 3.3 / 12.8 (03 Aug) | 6% | 0.5 / 12.8 | 6% |
| 2025-09 | 26 | 0.4 / 1.3 / 10.9 (28 Sep) | 5% | 0.4 / 10.9 | 5% |
| 2025-10 | 27 | 0.5 / 4.0 / 9.7 (27 Oct) | 5% | 0.4 / 9.2 | 5% |
| 2025-11 | 25 | 0.3 / 1.6 / 21.5 (16 Nov) | 8% | 0.3 / 21.5 | 8% |
| 2025-12 | 27 | 0.4 / 4.5 / 24.9 (25 Dec) | 3% | 0.4 / 24.9 | 3% |
| 2026-01 | 26 | 0.3 / 2.7 / 18.0 (01 Jan) | 1% | — | — |
| 2026-02 | 24 | 0.4 / 2.1 / 12.2 (08 Feb) | 3% | — | — |
| 2026-03 | 27 | 0.5 / 5.0 / 25.1 (22 Mar) | 9% | — | — |
| **All** | 438 | 0.3 / 3.4 / 90.6 | 8% | 0.3 / 42.2 | 9% |

(161's own daily candles for 2024 and 2025 are off from IG's by the same amounts as the ticks. In March 2025 only, 161's are closer than the ticks'. That was not looked into: it falls in the weeks between the US and UK clock changes.)

### Against 161's 5-minute candles (not IG's own for 2024 to February 2026)

With the time zone above, candles built from the ticks match **every** 5-minute candle 161 has from January 2024 to February 2026: 149,526 bid candles in 2024–2025 (all four prices, worst 0.0), and 11,808 mid candles in January and February 2026 (open and close). For 23 to 31 March 2026, where 161's mid candles are IG's own, the gap is typically 0.5, 95% within 0.9, worst 8.2 (23 March 21:00, the rollover hour).

### Two ways of making IG's prices from the ticks, against IG's own

| Daily price | A, the ticks' own bid: typical / 90% / exact | B, tick mid − half IG's typical spread: typical / 90% / exact |
|---|---|---|
| open | 0.4 / 6.0 / 6% | 0.4 / 6.1 / 7% |
| high | 0.3 / 1.3 / 9% | 0.3 / 1.3 / 11% |
| low | 0.3 / 4.1 / 10% | 0.4 / 3.6 / 8% |
| close | 0.3 / 2.6 / 8% | 0.5 / 4.6 / 5% |

(433 IG daily candles, November 2024 to March 2026.)

| UK hour | Tick mid vs IG mid, 5-minute open and close: typical / 90% / worst | Candles |
|---|---|---:|
| 00:00 | 0.60 / 0.90 / 1.90 | 84 |
| 01:00 | 0.50 / 0.80 / 1.20 | 72 |
| 02:00 | 0.47 / 0.80 / 1.50 | 72 |
| 03:00 | 0.40 / 0.75 / 1.55 | 72 |
| 04:00 | 0.60 / 0.85 / 1.10 | 72 |
| 05:00 | 0.55 / 0.85 / 1.60 | 72 |
| 06:00 | 0.50 / 0.80 / 3.00 | 72 |
| 07:00 | 0.53 / 0.90 / 1.65 | 72 |
| 08:00 | 0.45 / 0.75 / 4.30 | 72 |
| 09:00 | 0.45 / 0.80 / 2.05 | 72 |
| 10:00 | 0.45 / 0.75 / 1.15 | 84 |
| 11:00 | 0.50 / 0.90 / 3.10 | 84 |
| 12:00 | 0.45 / 0.85 / 1.95 | 84 |
| 13:00 | 0.60 / 0.85 / 1.20 | 78 |
| 14:00 | 0.55 / 0.85 / 3.85 | 83 |
| 15:00 | 0.50 / 0.85 / 1.65 | 84 |
| 16:00 | 0.50 / 0.85 / 1.10 | 84 |
| 17:00 | 0.45 / 0.80 / 5.70 | 84 |
| 18:00 | 0.47 / 0.80 / 1.25 | 84 |
| 19:00 | 0.45 / 0.85 / 1.75 | 84 |
| 20:00 | 0.45 / 0.90 / 5.15 | 84 |
| 21:00 | 0.88 / 4.45 / 8.15 | 71 |
| 22:00 | 0.60 / 0.90 / 5.35 | 72 |
| 23:00 | 0.65 / 1.65 / 5.90 | 71 |
| **All hours** | 0.50 / 0.85 / 8.15 | 1863 |

### Spreads by UK hour (pips, at each 5-minute close)

"IG" is the bot's own live IG prices, 25 October to 11 November 2026. "Ticks" is the archive, by year (2026: January to March).

| UK hour | IG (the bot, 25 Oct – 11 Nov 2026): typical / 90% | Ticks 2024: typical / 90% | Ticks 2025: typical / 90% | Ticks 2026 (Jan–Mar): typical / 90% | IG ÷ ticks (2025) |
|---|---|---|---|---|---:|
| 00:00 | 1.5 / 1.5 | 0.9 / 1.2 | 0.9 / 1.3 | 0.7 / 1.1 | 1.7 |
| 01:00 | 1.5 / 1.5 | 0.8 / 1.1 | 0.8 / 1.2 | 0.8 / 1.0 | 1.9 |
| 02:00 | 1.5 / 1.5 | 0.8 / 1.1 | 0.8 / 1.2 | 0.8 / 1.0 | 1.9 |
| 03:00 | 1.5 / 1.5 | 0.8 / 1.1 | 0.8 / 1.2 | 0.7 / 1.0 | 1.9 |
| 04:00 | 1.5 / 1.5 | 0.8 / 1.1 | 0.8 / 1.1 | 0.7 / 1.0 | 1.9 |
| 05:00 | 1.5 / 1.5 | 0.8 / 1.1 | 0.8 / 1.1 | 0.7 / 1.0 | 1.9 |
| 06:00 | 1.5 / 1.5 | 0.8 / 1.1 | 0.8 / 1.2 | 0.8 / 1.0 | 1.9 |
| 07:00 | 0.9 / 1.5 | 0.8 / 1.0 | 0.7 / 1.0 | 0.6 / 0.9 | 1.3 |
| 08:00 | 0.9 / 1.5 | 0.7 / 1.0 | 0.7 / 1.0 | 0.6 / 0.9 | 1.3 |
| 09:00 | 1.5 / 1.5 | 0.7 / 1.0 | 0.7 / 1.0 | 0.6 / 0.9 | 2.1 |
| 10:00 | 0.9 / 1.5 | 0.7 / 1.0 | 0.7 / 1.0 | 0.6 / 0.9 | 1.3 |
| 11:00 | 0.9 / 1.5 | 0.7 / 1.0 | 0.7 / 1.0 | 0.6 / 0.9 | 1.3 |
| 12:00 | 0.9 / 1.5 | 0.7 / 1.0 | 0.7 / 1.0 | 0.6 / 0.9 | 1.3 |
| 13:00 | 1.5 / 1.5 | 0.7 / 1.0 | 0.7 / 1.1 | 0.6 / 0.9 | 2.1 |
| 14:00 | 0.9 / 1.5 | 0.8 / 1.0 | 0.7 / 1.1 | 0.6 / 0.9 | 1.3 |
| 15:00 | 0.9 / 1.5 | 0.8 / 1.0 | 0.7 / 1.0 | 0.6 / 0.9 | 1.3 |
| 16:00 | 0.9 / 1.5 | 0.8 / 1.0 | 0.7 / 1.0 | 0.6 / 0.9 | 1.3 |
| 17:00 | 0.9 / 1.5 | 0.8 / 1.0 | 0.7 / 1.0 | 0.6 / 0.9 | 1.3 |
| 18:00 | 0.9 / 1.5 | 0.8 / 1.0 | 0.7 / 1.1 | 0.6 / 0.9 | 1.3 |
| 19:00 | 1.5 / 1.5 | 0.8 / 1.0 | 0.7 / 1.1 | 0.6 / 0.9 | 2.1 |
| 20:00 | 1.5 / 1.5 | 0.8 / 1.2 | 0.8 / 1.3 | 0.7 / 1.0 | 1.9 |
| 21:00 | 4.5 / 17.7 | 0.9 / 1.4 | 0.9 / 2.0 | 0.9 / 7.7 | 4.9 |
| 22:00 | 14.6 / 16.9 | 3.5 / 7.6 | 6.0 / 12.9 | 4.6 / 10.6 | 2.4 |
| 23:00 | 1.5 / 2.7 | 1.1 / 1.6 | 1.1 / 1.9 | 0.8 / 1.8 | 1.4 |
| **All hours** | 1.5 / 1.5 | 0.8 / 1.2 | 0.8 / 1.2 | 0.7 / 1.1 | |
