# Slow grind trend-day signal: does the rest of the day trend? (21 November 2026)

Research only. Nothing in the live bot, its code or its settings was changed. Server: the new AutoBot server,
/opt/autobot (not AutoBot 161).

## The answer in brief

- **The signal turns on about half the time.** Out of 703 usable weekdays (Jan 2024 to 19 Nov 2026), it turned on
  up on 167 days and down on 174. On 13 days slow grind trades both ways were in profit, so those are not trend
  days. On 349 days it did not turn on.
- **After 09:00 it points the right way only slightly more often than a coin toss.** On the 341 days it turned on,
  09:00 to 20:30 ended in the signal's direction on 189 days (55%). The median day finished +4.6 pips its way.
  The biggest move its way had a median of 29.7 pips, and the biggest move against it 24.5. With 341 days, chance
  alone would land anywhere from about 45% to 55%, so 55% sits at the very edge of what chance gives.
- **Signal days did not hug the band more than other days.** Measured the way Johnny describes a trend day (price
  keeps hugging the Bollinger band, and pullbacks don't reach the 5-minute EMA cluster), signal days spent a median
  14% of the session hugging in the signal's direction. They spent 12% hugging the other way. Strongly hugging days
  (the top 10% of all days) were 18 of 341 in the signal's direction (5%), against 13 of 341 the other way (4%).
  Days with no signal produced them at the same rate: 36 out of 698 day-directions (5%).
- **Days without the signal moved just as much.** The median net move size from 09:00 to 20:30 was 26.3 pips on
  signal days and 28.6 pips on days without it. 59% and 62% of days moved 20+ pips net either way.
- **Big news later in the day makes the signal less reliable, not more.** On signal days with big news from 09:00 to
  20:30, 38 of 71 ended its way (54%). 26 finished 20+ pips its way, and 25 finished 20+ pips against it. Without
  big news, it was 151 of 270 (56%).
- **The 13 "both ways" days were quiet.** Their median net move size was 11.2 pips, and only 2 of 13 moved 20+ net.
  There are too few of them to rely on.

By year, the share of signal days ending in its direction was 64 of 117 in 2024 (55%), 76 of 138 in 2025 (55%)
and 49 of 86 in 2026 (57%). No year stands out.

## What was run

**Candles.** `data/research/stp_validation_store/GBPUSD` is the research store checked and used by the STP historical
validation on 19–20 Nov (see `docs/research/stp_validation_20261120/REPORT.md` on that branch). I used a copy of
it, so nothing was written to the original.
- Jan 2024 to Dec 2025: AutoBot 161's candles from a vendor tick archive. These are close to IG's prices (typically
  0.2–0.5 pips off) but are not IG's own.
- Jan to 24 Oct 2026: 161's IG mid candles.
- 25 Oct 2026 on: the bot's own IG bid/ask candles.
- In the first two periods the buy price is the bid plus IG's typical spread.
- 1–22 March 2026 has no data. 46 weekdays were left out for missing candles (the rule is below).

Johnny's brief mentions candles rebuilt on 20 Nov at `/home/autobot/stp-research/historical`. I did not use them:
they stop on 10 April 2026, their manifest warns that the UTC timestamps are unverified, and on a sample day they
sit about 12 pips away from the validated store.

**Code.** An exact copy (`git archive`) of the code running live now: 4635175, which the price service has run since
the 14:08 UTC restart today. It used the live `.env` switches; secrets were removed, which changes nothing here.

**The slow grind signal, exactly as the live code makes it.** For each trading week, the steps are the live
runner's (`strategies/replay.StrategyRunner.step`), for the slow grind only:
1. the analyser's `StateTracker` replays the week;
2. the 21 EMA is worked out on the warm-up plus the week's candles;
3. `SlowGrind.on_candle` finds the setups;
4. `strategies.common.check` applies the state rule (trend only, in the trend's direction).

The other strategies were not run, because they don't feed the slow grind. On a test week (8–13 June 2025) this
gave the same 111 slow grind ideas (28 allowed) as the full bot replay.

**Trades.** These follow `trade_manager/replay_check.py`:
- `may_open` applies the slow grind's hours. New trades are allowed from 00:00 UK, except in the first 15 minutes
  after the Sunday open and during the 21:55–22:15 rollover; none open from 20:30 to midnight.
- Only one slow grind trade can be open at a time.
- A sell fills at the entry price. A buy fills at the entry plus that candle's spread.
- The live trade manager's `plan` and `step` run the trade candle by candle. That gives a stop of 15, a take profit of
  20 (100 on a big-news day or a trend day in its direction), the 15/10 profit lock and the 20:30 close.
- 1,707 trades in all.
- Not modelled: the overall limit of 5 open trades across all strategies, which other strategies' trades could
  reach.

**"In profit between 06:00 and 09:00 UK, measured as IG would close it."** A buy is judged on the sell price and a
sell on the buy price, against the trade's fill, on 5-minute candles starting 06:00 to 08:55 UK:
- The candle the trade opened in counts only if it closed in profit. A candle doesn't show whether its high came
  before or after the entry.
- The candle the trade closed in counts if the trade closed in profit (lock or take profit), or if that candle opened
  in profit.
- Every candle in between counts if its best price was beyond the fill.

Trades opened at any time from 00:00 count, as long as they are open during the window.
- **Up** = only buys in profit in the window.
- **Down** = only sells in profit.
- **Both** = buys and sells in profit, so not a trend day.
- **Signal time** = the first 5-minute candle in the window in which it was in profit.

**Rest of the day.** 5-minute candles from 09:00 to 20:25 UK, on the chart (sell) price. The open is the 09:00
candle's open and the close is the 20:25 candle's close. The biggest moves each way are measured from the 09:00
open.

**Hugging the band.** All on the chart price, with the bot's own indicator code. Down is the mirror of up.
- The band is the Bollinger band (20, 2), as on Johnny's chart.
- "The 5-minute EMA cluster" is the EMA pullback's 8/13/21.
- A candle **touches** the band if its high reaches the upper band.
- A candle is **hugging** if it doesn't reach the cluster, and either it touches the band or the candle before it was
  hugging. So a hug starts at a band touch and ends at the first pullback that reaches the cluster. It is worked
  out from 00:00 and counted on the 09:00–20:25 candles.

Two readings of "didn't reach the cluster":
- **Strict:** the pullback doesn't touch the 8 EMA, the near edge of the cluster.
- **Loose:** the pullback doesn't touch the 21 EMA, the far edge.

Under the strict reading, no day in the three years hugged for even half the session: the most was 40%. That is
because on 5-minute candles price touches the 8 EMA every few candles. So a "strongly hugging day" here means the
top 10% of all usable days in their better direction: 25% or more of the session (strict), or 50% or more (loose).
These cut-offs are my choice, made from the spread of all days. Johnny didn't set them.

**Big news.** The bot's own table (`config/news_table.toml`, read by `news.calendar.big_news_windows`), applied to
Finnhub's past calendar (`data/research/news/finnhub_calendar.json`, Nov 2023 – Nov 2026, the calendar the 10 Nov
long replay used). The bot's own calendar file only goes back to late October. "Later that day" means a big
GBP or USD release between 09:00 and 20:30 UK, so the rule is the same for every group. Releases at other times
(for example UK data at 07:00) are listed in `days.csv` but don't count for the split. 140 of the 703 days had
big news from 09:00 to 20:30.

**Usable days.** At least 65 of 72 candles from 00:00 to 06:00, 33 of 36 from 06:00 to 09:00, and 124 of 138 from
09:00 to 20:30, including the 09:00 and 20:25 candles.

**Check against a real day.** On 18 Nov 2026 the run opens the 04:05 UTC sell at 13195.5 and turns the signal on
down at 06:00. This matches another session's replay of 5d7942e for that night
(research/trend-day-18nov-20261121, part 2). From 09:00, 18 Nov finished 4.9 pips the signal's way.

## 1. Did the signal turn on, when, and which way

Every day is in `days.csv`, with these columns:
- `signal` (up / down / both / none) and `signal_time_uk`;
- `buy_in_profit_0609` and `sell_in_profit_0609`: the first time each side was in profit;
- the trade counts for the day.

Every trade is in `slow_grind_trades.csv`.

| Signal | Days | Share |
|---|---|---|
| Up (only buys in profit) | 167 | 24% |
| Down (only sells in profit) | 174 | 25% |
| Both ways in profit: not a trend day | 13 | 2% |
| Did not turn on | 349 | 50% |

| Signal time (UK) | Signal days |
|---|---|
| 06:00 (already in profit at the window's first candle) | 107 |
| 06:05–06:55 | 82 |
| 07:00–07:55 | 71 |
| 08:00–08:55 | 81 |

## 2 and 3. The rest of the day on signal days (09:00–20:30, in the signal's direction)

| Figure | All signal days (341) | Up (167) | Down (174) |
|---|---|---|---|
| Net pips, median / mean | +4.6 / +3.3 | +4.3 / +2.8 | +4.8 / +3.8 |
| Ended in its direction | 189 (55%) | 93 (56%) | 96 (55%) |
| ... by 20+ pips | 111 (33%) | 52 (31%) | 59 (34%) |
| Ended 20+ pips against it | 89 (26%) | 41 (25%) | 48 (28%) |
| Biggest move its way, median / mean | 29.7 / 36.1 | 28.2 / 34.8 | 30.6 / 37.4 |
| Biggest move against it, median / mean | 24.5 / 31.8 | 24.8 / 31.8 | 23.9 / 31.9 |
| Biggest move its way larger than against | 184 (54%) | 92 (55%) | 92 (53%) |
| Share of session hugging its way (strict), median | 14% | 14% | 13% |
| Strongly hugging day its way (strict, top 10%) | 18 (5%) | see summary.md | see summary.md |
| ... the other way | 13 (4%) | | |
| Share hugging its way (loose, 21 EMA), median | 28% | | |
| Strongly hugging day its way (loose, top 10%) | 22 (6%) | | |
| ... the other way | 13 (4%) | | |
| Band touches its way, median | 17 | 17 | 17 |

## 4. Days the signal did not turn on, as the comparison

These days have no direction, so the table compares the size of the move and the day's better hugging direction.
The signal days are shown the same way for a like-for-like comparison.

| Group | Days | Net move size, median | Moved 20+ net either way | Larger of the two biggest moves, median | Better-direction hug share (strict), median | Strongly hugging day either way (strict) | Strongly hugging day either way (loose) |
|---|---|---|---|---|---|---|---|
| Signal on (up/down) | 341 | 26.3 | 200 (59%) | 47.9 | 17% | 31 (9%) | 35 (10%) |
| Both ways (not trend) | 13 | 11.2 | 2 (15%) | 37.1 | 14% | 0 | 0 |
| Signal not on | 349 | 28.6 | 217 (62%) | 47.9 | 17% | 36 (10%) | 43 (12%) |

Counted per direction (each day can hug up or down), days without the signal gave a strongly hugging
day-direction in 36 of 698 cases (5%) under the strict reading, and 43 of 698 (6%) under the loose one. On signal
days, the signal's own direction gave 18 of 341 (5%) and 22 of 341 (6%). That is the same rate.

## 5. Split by big news later that day (09:00–20:30 UK)

| Group | Big news later? | Days | Ended in signal's direction | 20+ its way | 20+ against | Net its way, median | Biggest move its way / against, median |
|---|---|---|---|---|---|---|---|
| Signal days | yes | 71 | 38 (54%) | 26 (37%) | 25 (35%) | +4.9 | 34.6 / 33.7 |
| Signal days | no | 270 | 151 (56%) | 85 (31%) | 64 (24%) | +4.4 | 28.3 / 23.4 |

| Group | Big news later? | Days | Net move size, median | Moved 20+ net either way | Larger biggest move, median | Strongly hugging day either way (strict) |
|---|---|---|---|---|---|---|
| Signal on | yes | 71 | 34.7 | 51 (72%) | 58.0 | 0 (0%) |
| Signal not on | yes | 66 | 42.5 | 53 (80%) | 69.4 | 0 (0%) |
| Both ways | yes | 3 | 11.0 | 1 | 69.6 | 0 |
| Signal on | no | 270 | 23.9 | 149 (55%) | 44.5 | see summary.md |
| Signal not on | no | 283 | 24.3 | 164 (58%) | 43.7 | see summary.md |
| Both ways | no | 10 | 11.4 | 1 | 34.8 | 0 |

Big news brings bigger moves, but bigger moves both ways: on signal days the move against grows as much as the
move with it. Days without the signal moved more on news days than signal days did.

## Limits

- Entries are taken at the start of the candle they happen in (stored candles have no ticks). For the entry candle,
  "in profit" is judged on its close only.
- 2024–25 prices are vendor prices close to IG's, not IG's own. The buy price before 25 Oct 2026 is modelled with
  IG's typical spread.
- Finnhub's past forecasts and previous figures are as Finnhub holds them today. This only matters for whether a
  day counts as a big-news day for the 100-pip take profit, not for the news split.
- The bot's 5-trades-at-once limit across strategies isn't modelled.
- The hugging cut-offs are my choice. Under both readings and at every level I looked at, signal days and other
  days came out the same.
- As Johnny asked, this report gives no profit or loss totals for the slow grind trades.

## Files

| File | What it is |
|---|---|
| `days.csv` | One row per weekday: signal, time, rest-of-day figures, hugging both ways under both readings, big news |
| `slow_grind_trades.csv` | Every simulated slow grind trade (open, fill, take profit, close, why) |
| `summary.md` | Every table, as `summary.py` prints it from `days.csv` |
| `trades.py`, `days.py`, `summary.py` | The scripts. They were run from a `git archive` copy of 4635175 with `settings.toml` folders pointed at a scratch copy of the store (scratch output folders, never live ones) and `AUTOBOT_ENV_FILE` set to the live switches |

To run them again, from such a copy (package `research_sg/`):

    python -m research_sg.trades ENV data/research/news/finnhub_calendar.json OUT 2024-01-08T12:00:00Z 2026-11-20T00:00:00Z
    python -m research_sg.days ENV data/research/news/finnhub_calendar.json OUT/weeks.jsonl OUT/days.csv
    python -m research_sg.summary OUT/days.csv
