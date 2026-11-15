# Making the hourly band pierce rule work: diagnosis, fixes and a check on unseen days (15 November 2026)

**Status: research only. Nothing in the bot or on AutoBot 161 was changed (161's archive was only read, from the copy in `data/research/`). Waiting for the owner.**

## In short

- **The rule as given loses in every version** on the 118 complete weekdays (`hourly_pierce_20261115.md`).
- **Most of the losses come from pierces made while the hourly chart is trending.** In the first half, trades taken while the bot's hourly read said sell-off or rally lost on average. Trades while it said ranging came close to break-even.
- **Two of the owner's own ideas, together, make it work on both halves:**
  1. **the hourly read** (`analyser/hourly_read.py`, as built on 14 November): take the pierce only while the hourly read is **ranging**;
  2. **the owner's reversal times:** take the pierce only within **60 minutes of 10:00, 14:00 or 16:00 UK**. The 60-minute width is Claude's suggestion.
- **With both, 7 of the 12 versions are positive on both halves.** Those 7 include both of the owner's own readings of "reverses" (A and B) with the trail.
  - **Best:** reading D *(Claude's)* with the trail: **53 trades, 58.5% won, +224.4 pips**. That's +91.5 on the first half and +132.9 on the second. It was positive in 7 of the 8 months.
  - **Owner's reading A with the trail:** 58 trades, 55.2% won, +214.4 (+67.1 and +147.3).
  - **Owner's reading B with the trail:** 40 trades, 55.0% won, +118.2 (+5.1 and +113.1).
- **Trend days are taken out by the hourly read on its own.** No surviving version took a single trade on any of the 4 trend days, because on those days the hourly read is never ranging.
- **What didn't help:**
  - the trend-day guard by "move since 07:00";
  - the direction rule;
  - a stop just beyond the turn.
- **How much to trust it:**
  - About 50 trades in 118 days, roughly one every two days. That is a small sample.
  - June holds about a third of the trades.
  - The fixes were picked on the first half and held on the second. That's encouraging, but it isn't proof.

## How it was done

- **The rule (owner, 15 November 2026):** a 5-minute candle goes more than 3 pips past the hourly Bollinger band (20, 2), the next 5-minute bar reverses, 12-pip stop. The readings, entries and exits are as in `hourly_pierce_20261115.md`:
  - A and B are the owner's examples of "reverses";
  - C and D are Claude's suggestions;
  - the exits are fixed 12, fixed 20 and the trail behind the last 3 candles once +12.

  All results here use **07:00–19:00 UK**, the best hours choice in that test. The same code was checked to reproduce that test exactly for all 12 versions.
- **The data:** the 118 complete weekdays in AutoBot 161's archive (IG's own mid, with sell and buy prices rebuilt from IG's typical spread). Signals with missing data are skipped. Costs are treated as before, with nothing added. Trend day (owner): the 17:00 UK close is at least 80 pips from the 07:00 open.
- **Split:**
  - **First half:** 23 March to 30 June (45 days, 1 trend day: 23 March, with no trade in 07:00–19:00). This is where the losing trades were studied and the fixes were looked for.
  - **Second half:** 1 July to 6 November (73 days, 3 trend days). This was used only as a check.
  - A fix counts only if it adds pips on both halves.
- **Carried over, not in the rule:** one trade at a time in each direction; no end-of-day close.

### The rule as given, by half

| Version | First half: trades / win rate / pips | Second half |
|---|---|---|
| A. closes against the push, fixed 12 | 125 / 43.2% / -204.0 | 189 / 48.1% / -84.0 |
| A. closes against the push, fixed 20 | 105 / 33.3% / -140.0 | 166 / 32.5% / -264.0 |
| A. closes against the push, trail | 109 / 43.1% / -69.5 | 175 / 45.7% / -108.4 |
| B. closes beyond the pierce candle, fixed 12 | 93 / 45.2% / -108.0 | 141 / 46.8% / -108.0 |
| B. closes beyond the pierce candle, fixed 20 | 84 / 29.8% / -208.0 | 133 / 35.3% / -92.0 |
| B. closes beyond the pierce candle, trail | 82 / 43.9% / -31.8 | 133 / 46.6% / -55.5 |
| C. closes back inside the band (Claude's), fixed 12 | 86 / 44.2% / -120.0 | 122 / 45.1% / -144.0 |
| C. closes back inside the band (Claude's), fixed 20 | 80 / 31.2% / -160.0 | 118 / 33.1% / -168.0 |
| C. closes back inside the band (Claude's), trail | 82 / 42.7% / -65.3 | 121 / 44.6% / -100.8 |
| D. trades past the pierce candle (Claude's), fixed 12 | 117 / 49.6% / -12.0 | 168 / 47.6% / -96.0 |
| D. trades past the pierce candle (Claude's), fixed 20 | 97 / 34.0% / -108.0 | 145 / 33.8% / -172.0 |
| D. trades past the pierce candle (Claude's), trail | 106 / 47.2% / -19.5 | 160 / 46.2% / -113.9 |

## Why it loses (first half only)

All 12 versions pooled; average pips per trade. The full tables are in `data/research/pierce_fixes_20261115/diagnose.txt`.

- **The hourly read:**
  - trades while the hourly is in a sell-off or rally against the trade: 724 trades, −1.14 pips each;
  - trades while it is ranging: 421 trades, −0.39 each;
  - the few trades with the hourly behind the trade (21) all lost.

  A pierce of the hourly band while the hourly is trending is usually the trend carrying on.
- **Time of day:**
  - 12:00 was the best hour (+3.53 a trade) and 09:00 and 13:00 were positive;
  - 08:00 was the worst (−8.12);
  - 10:00, 14:00 and 16:00 were among the losing hours.

  The owner's times therefore don't help on their own, but they do help together with the hourly read (below).
- **Move since 07:00:**
  - fading a move of 40+ pips since 07:00 won 59.5% (+4.70 a trade);
  - smaller moves lost.

  This is the opposite of "big moves are trend days, avoid them". On normal days a stretched move is the best one to fade.
- **Pierce depth:** pierces of 8+ pips past the band did better (+2.09 a trade) than shallow ones (about −3.7).
- **The direction rule (daily pivot and 100 EMA):** a pierce of the upper band is almost always above the pivot and the 100 EMA. So the rule is "against" in 912 of 924 trades with a pivot. It barely separates anything.
- **Speed:** a third of the losers were stopped within 30 minutes of the pierce.

## Every fix on its own

"Better on both halves" counts the 12 versions where the fix added pips on both the first and the second half.

| Fix | Whose idea | Versions better on both halves | Versions positive on both halves |
|---|---|---|---|
| owner's times +-30 min (10:00, 14:00, 16:00) | owner | 8 / 12 | none |
| owner's times +-60 min | owner | 10 / 12 | D trail |
| skip fading a move of 60+ since 07:00 (trend-day guard) | owner idea, Claude's number | 1 / 12 | none |
| skip fading a move of 80+ since 07:00 (trend-day guard) | owner idea, Claude's number | 0 / 12 | none |
| only against the direction rule | owner rule, Claude's reading | 10 / 12 | D fixed 12 |
| skip when the direction rule is with the trade | owner rule, Claude's reading | 0 / 12 | none |
| hourly read: only when ranging | owner (hourly read) | 12 / 12 | A trail, D fixed 12, D trail |
| hourly read: skip when the hourly agrees with the trade | owner (hourly read) | 6 / 12 | none |
| hourly read: skip when the hourly is against the trade | owner (hourly read) | 12 / 12 | A trail, D fixed 12, D trail |
| stop 1 pip beyond the turn (max 12) | owner idea, Claude's number | 0 / 12 | none |
| stop 2 pips beyond the turn (max 12) | owner idea, Claude's number | 2 / 12 | none |
| stop 3 pips beyond the turn (max 12) | owner idea, Claude's number | 3 / 12 | none |
| stop 2 pips beyond the turn (max 20) | owner idea, Claude's number | 1 / 12 | none |
| only fading a move of 40+ since 07:00 | Claude (from the diagnosis) | 8 / 12 | B fixed 12, B trail |
| only fading a move of 30+ since 07:00 | Claude (from the diagnosis) | 3 / 12 | none |
| only a pierce 8+ pips past the band | Claude (from the diagnosis) | 4 / 12 | C fixed 12 |
| only a pierce 6+ pips past the band | Claude (from the diagnosis) | 8 / 12 | C fixed 12, D fixed 12 |

Notes:
- **The direction rule:** "only against the direction rule" looks good, but almost all it removes is days with no pivot, where the previous day's candles are incomplete in the archive. That's an artefact of the data, not a rule, so it is not counted.
- **The trend-day guard:** "skip fading a move of 60+ or 80+ since 07:00" (Claude's real-time stand-in for the owner's trend-day rule, which is only known at 17:00) does not help, because on normal days fading big moves is the best trade. The hourly read keeps the trend days out instead.
- **A stop just beyond the turn** (Claude's numbers: 1, 2 or 3 pips past the turn's extreme, at most 12 or 20) changes the results by large amounts both ways, with no steady direction.
- **Claude's fixes from the diagnosis** ("only fading 40+", "only pierces of 6+ or 8+ pips") help a lot on the first half, where they were found, but not reliably on the second.

## Combinations, built on the hourly read

✔ = positive on both halves.

### H: hourly read ranging only (owner's idea)

| Version | First half | Second half | Normal days | Trend days |
|---|---|---|---|---|
| A. closes against the push, fixed 12 | 50 / 48.0% / -24.0 | 47 / 51.1% / +12.0 | 97 / 49.5% / -12.0 | 0 |
| A. closes against the push, fixed 20 | 42 / 33.3% / -56.0 | 42 / 35.7% / -24.0 | 84 / 34.5% / -80.0 | 0 |
| A. closes against the push, trail ✔ | 45 / 51.1% / +55.9 | 45 / 51.1% / +72.9 | 90 / 51.1% / +128.8 | 0 |
| B. closes beyond the pierce candle, fixed 12 | 31 / 48.4% / -12.0 | 32 / 53.1% / +24.0 | 63 / 50.8% / +12.0 | 0 |
| B. closes beyond the pierce candle, fixed 20 | 29 / 27.6% / -92.0 | 32 / 43.8% / +64.0 | 61 / 36.1% / -28.0 | 0 |
| B. closes beyond the pierce candle, trail | 29 / 48.3% / -19.7 | 31 / 54.8% / +90.7 | 60 / 51.7% / +71.0 | 0 |
| C. closes back inside the band (Claude's), fixed 12 | 28 / 42.9% / -48.0 | 25 / 56.0% / +36.0 | 53 / 49.1% / -12.0 | 0 |
| C. closes back inside the band (Claude's), fixed 20 | 25 / 28.0% / -76.0 | 24 / 45.8% / +64.0 | 49 / 36.7% / -12.0 | 0 |
| C. closes back inside the band (Claude's), trail | 25 / 44.0% / -8.0 | 24 / 54.2% / +126.2 | 49 / 49.0% / +118.2 | 0 |
| D. trades past the pierce candle (Claude's), fixed 12 ✔ | 42 / 57.1% / +72.0 | 40 / 52.5% / +24.0 | 82 / 54.9% / +96.0 | 0 |
| D. trades past the pierce candle (Claude's), fixed 20 | 38 / 31.6% / -72.0 | 37 / 43.2% / +68.0 | 75 / 37.3% / -4.0 | 0 |
| D. trades past the pierce candle (Claude's), trail ✔ | 38 / 57.9% / +101.9 | 39 / 51.3% / +80.5 | 77 / 54.5% / +182.4 | 0 |

### H + the owner's reversal times, within 60 minutes (owner's ideas; the width is Claude's)

| Version | First half | Second half | Normal days | Trend days |
|---|---|---|---|---|
| A. closes against the push, fixed 12 ✔ | 31 / 51.6% / +12.0 | 30 / 60.0% / +72.0 | 61 / 55.7% / +84.0 | 0 |
| A. closes against the push, fixed 20 | 27 / 37.0% / -4.0 | 26 / 42.3% / +40.0 | 53 / 39.6% / +36.0 | 0 |
| A. closes against the push, trail ✔ | 30 / 50.0% / +67.1 | 28 / 60.7% / +147.3 | 58 / 55.2% / +214.4 | 0 |
| B. closes beyond the pierce candle, fixed 12 ✔ | 21 / 52.4% / +12.0 | 21 / 57.1% / +36.0 | 42 / 54.8% / +48.0 | 0 |
| B. closes beyond the pierce candle, fixed 20 | 20 / 25.0% / -80.0 | 21 / 47.6% / +68.0 | 41 / 36.6% / -12.0 | 0 |
| B. closes beyond the pierce candle, trail ✔ | 20 / 50.0% / +5.1 | 20 / 60.0% / +113.1 | 40 / 55.0% / +118.2 | 0 |
| C. closes back inside the band (Claude's), fixed 12 | 20 / 45.0% / -24.0 | 16 / 50.0% / +0.0 | 36 / 47.2% / -24.0 | 0 |
| C. closes back inside the band (Claude's), fixed 20 | 19 / 31.6% / -36.0 | 15 / 33.3% / -20.0 | 34 / 32.4% / -56.0 | 0 |
| C. closes back inside the band (Claude's), trail ✔ | 19 / 47.4% / +24.9 | 15 / 46.7% / +87.1 | 34 / 47.1% / +112.0 | 0 |
| D. trades past the pierce candle (Claude's), fixed 12 ✔ | 29 / 58.6% / +60.0 | 26 / 61.5% / +72.0 | 55 / 60.0% / +132.0 | 0 |
| D. trades past the pierce candle (Claude's), fixed 20 | 27 / 33.3% / -36.0 | 23 / 47.8% / +76.0 | 50 / 40.0% / +40.0 | 0 |
| D. trades past the pierce candle (Claude's), trail ✔ | 28 / 57.1% / +91.5 | 25 / 60.0% / +132.9 | 53 / 58.5% / +224.4 | 0 |

### H + the owner's reversal times, within 30 minutes

| Version | First half | Second half | Normal days | Trend days |
|---|---|---|---|---|
| A. closes against the push, fixed 12 ✔ | 20 / 55.0% / +24.0 | 23 / 60.9% / +60.0 | 43 / 58.1% / +84.0 | 0 |
| A. closes against the push, fixed 20 | 17 / 35.3% / -12.0 | 21 / 47.6% / +68.0 | 38 / 42.1% / +56.0 | 0 |
| A. closes against the push, trail ✔ | 19 / 52.6% / +104.7 | 21 / 61.9% / +74.1 | 40 / 57.5% / +178.8 | 0 |
| B. closes beyond the pierce candle, fixed 12 | 15 / 46.7% / -12.0 | 16 / 56.2% / +24.0 | 31 / 51.6% / +12.0 | 0 |
| B. closes beyond the pierce candle, fixed 20 | 15 / 20.0% / -84.0 | 16 / 50.0% / +64.0 | 31 / 35.5% / -20.0 | 0 |
| B. closes beyond the pierce candle, trail | 15 / 40.0% / -11.3 | 15 / 53.3% / +23.4 | 30 / 46.7% / +12.1 | 0 |
| C. closes back inside the band (Claude's), fixed 12 | 11 / 36.4% / -36.0 | 11 / 54.5% / +12.0 | 22 / 45.5% / -24.0 | 0 |
| C. closes back inside the band (Claude's), fixed 20 | 11 / 27.3% / -36.0 | 10 / 30.0% / -24.0 | 21 / 28.6% / -60.0 | 0 |
| C. closes back inside the band (Claude's), trail ✔ | 11 / 36.4% / +26.5 | 10 / 50.0% / +18.3 | 21 / 42.9% / +44.8 | 0 |
| D. trades past the pierce candle (Claude's), fixed 12 ✔ | 17 / 70.6% / +84.0 | 21 / 61.9% / +60.0 | 38 / 65.8% / +144.0 | 0 |
| D. trades past the pierce candle (Claude's), fixed 20 | 16 / 37.5% / +0.0 | 18 / 44.4% / +40.0 | 34 / 41.2% / +40.0 | 0 |
| D. trades past the pierce candle (Claude's), trail ✔ | 17 / 70.6% / +141.6 | 21 / 61.9% / +41.1 | 38 / 65.8% / +182.7 | 0 |

The other combinations tried are in `data/research/pierce_fixes_20261115/combos.txt`:
- H with fading 40+;
- H with pierces of 6+ pips;
- H with the times and either of those.

With fading 40+, every version is positive on both halves, but on only 1 to 10 trades per half, too few to count.

### Month by month: H + the owner's times within 60 minutes

Trades / win rate / pips.

| Month | D trail | D fixed 12 | A trail | B trail | A fixed 12 | B fixed 12 | C trail |
|---|---|---|---|---|---|---|---|
| 2026-03 | 2 / 50.0% / +6.0 | 2 / 50.0% / +0.0 | 3 / 33.3% / -7.5 | 2 / 50.0% / +4.5 | 3 / 33.3% / -12.0 | 2 / 50.0% / +0.0 | 3 / 33.3% / -3.4 |
| 2026-04 | 1 / 0.0% / -12.0 | 1 / 0.0% / -12.0 | 2 / 50.0% / -6.9 | 0 | 2 / 50.0% / +0.0 | 0 | 0 |
| 2026-05 | 5 / 80.0% / +21.3 | 5 / 80.0% / +36.0 | 6 / 66.7% / +9.5 | 4 / 100.0% / +36.3 | 7 / 57.1% / +12.0 | 5 / 80.0% / +36.0 | 3 / 100.0% / +25.6 |
| 2026-06 | 20 / 55.0% / +76.2 | 21 / 57.1% / +36.0 | 19 / 47.4% / +72.0 | 14 / 35.7% / -35.7 | 19 / 52.6% / +12.0 | 14 / 42.9% / -24.0 | 13 / 38.5% / +2.7 |
| 2026-07 | 3 / 66.7% / +32.2 | 3 / 66.7% / +12.0 | 4 / 75.0% / +50.9 | 3 / 66.7% / +15.0 | 5 / 80.0% / +36.0 | 3 / 66.7% / +12.0 | 2 / 50.0% / +26.6 |
| 2026-08 | 12 / 58.3% / +53.7 | 13 / 61.5% / +36.0 | 16 / 50.0% / +22.1 | 9 / 55.6% / +43.5 | 17 / 47.1% / -12.0 | 10 / 50.0% / +0.0 | 7 / 42.9% / +16.0 |
| 2026-09 | 5 / 80.0% / +19.2 | 5 / 80.0% / +36.0 | 5 / 100.0% / +45.2 | 5 / 80.0% / +26.8 | 5 / 100.0% / +60.0 | 5 / 80.0% / +36.0 | 3 / 66.7% / +15.4 |
| 2026-10 | 5 / 40.0% / +27.8 | 5 / 40.0% / -12.0 | 3 / 33.3% / +29.1 | 3 / 33.3% / +27.8 | 3 / 33.3% / -12.0 | 3 / 33.3% / -12.0 | 3 / 33.3% / +29.1 |

## What Claude suggests

1. **Use the owner's hourly read as the filter.** Take a pierce of the hourly band only while the hourly read is ranging. It is the owner's own idea, it improved all 12 versions on both halves, and it keeps every trend day out.
2. **Add the owner's reversal times:** only within 60 minutes of 10:00, 14:00 and 16:00 UK *(the 60-minute width is Claude's suggestion; 30 minutes also works but leaves very few trades)*.
3. **Reverses and entry:** D *(Claude's: price trades back past the pierce candle's far end on the next candle, entry at that moment)* did best. The owner's A with the trail is close behind.
4. **Exit:** the trail behind the last 3 candles once +12. It was the best exit for A, B, C and D. Fixed 20 is the weakest.
5. **Keep the 12-pip stop.** A stop just beyond the turn did not hold up.

**Before anything goes live, all of this needs:**
- more days: these are about 50 trades;
- the owner's look at the trades on the chart.

Nothing has been built.

## How much to trust this

- **Sample:** about 50 trades over 118 days; June holds about a third of them.
- **Data:** prices are IG's mid with a rebuilt typical spread. About 1 candle in 70 gets a different wick answer from IG's sell chart, and costs around news are understated.
- **Order inside a candle:** a stop and a target in the same 5-minute candle count as the stop. For D, the entry candle's own prices after the entry aren't known.
- **The hourly read** runs on the archive's hourly candles, which have a few gaps, so some reads may differ slightly from what the live bot would have shown.

## Files

`data/research/pierce_fixes_20261115/` (not in git):
- `lib.py`: signals and trades;
- `check_lib.py`: reproduces the pierce test;
- `diagnose.py` and `diagnose.txt`;
- `fixes.py`, `fixes.txt` and `fixes.json`;
- `combos.py`, `combos.txt` and `combos.json`.
