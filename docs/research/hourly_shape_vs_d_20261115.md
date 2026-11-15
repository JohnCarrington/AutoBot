# The owner's exact shape next to D: the 118 days of 2026 and 2024–2025 (15 November 2026)

**Status: research only. Nothing in the bot or on AutoBot 161 was changed (161's archive was only read, from the copies in `data/research/`). Waiting for the owner.**

## In short

| | Owner's shape (E): all / normal days / trend days | D: all / normal days / trend days |
|---|---|---|
| **2026, 118 complete weekdays** | 27 / 51.9% / +93.7 · 27 / 51.9% / +93.7 · 0 | 55 / 60.0% / +242.5 · 55 / 60.0% / +242.5 · 0 |
| **2024–2025, 517 complete weekdays** | 111 / 45.9% / -13.3 · 109 / 45.9% / -82.7 · 2 / 50.0% / +69.4 | 214 / 44.9% / -60.9 · 209 / 45.5% / -99.9 · 5 / 20.0% / +39.0 |

(trades / win rate / pips)

- **On 2026, both make money; D makes more and trades twice as often.**
- **On 2024–2025, both lose:** the owner's shape slightly (−13.3), D more (−60.9).
  - **By year:** 2024 loses for both (E −50.6, D −92.6). 2025 is positive for both (E +37.3, D +31.7), as 2026 is.
  - So the 2026 result does not hold across all three years.
- **One difference in the data explains part of the gap: Monday mornings.**
  - In 2026 most Monday-morning signals were skipped, because the archive lacks IG's first Sunday hour, which falls inside Monday morning's band window.
  - In 2024–25 they were kept.
  - Without Monday signals before 12:00 UK, the owner's shape is **+13.8** on 2024–25 (101 trades) and D is −15.3.

## The two shapes

Both use the same filters and the same exit:
- **Hourly read:** only while the bot's hourly read is **ranging**.
- **Times:** the pierce candle starts within **60 minutes of 10:00, 14:00 or 16:00 UK**. The 60-minute width is Claude's.
- **Hours:** 07:00–19:00 UK.
- **Stop:** 12 pips.
- **Exit:** the **trail** behind the last 3 candles once +12.
- **One trade at a time in each direction.**

The hourly read is the one known at the entry.

**The owner's shape (E, owner, 15 November 2026):**
1. A 5-minute candle goes more than 3 pips past the hourly Bollinger band (20, 2): above the upper band for a sell, below the lower for a buy.
2. A reversal candle *(Claude's reading: the next candle closes against the push, red after an upper pierce)*.
3. A confirmation candle that closes beyond the reversal candle's low (sell) or high (buy).
4. Entry at the next candle's open.

**D *(Claude's, from `hourly_pierce_fixes_20261115.md`)*:** after the same pierce, the next candle trades back past the pierce candle's far end, and the trade opens at that moment.

**A correction to the earlier D figure.** In `hourly_pierce_fixes_20261115.md`, D's hourly read was taken at the reversal candle's close, which is after D's entry. When that candle closed an hour, the read could include that hour. Taken at the entry, as here, D does slightly better: 55 trades, 60.0% won, **+242.5** (it was 53 trades, +224.4). That write-up now carries a note.

## The data

- **2026:** the 118 complete weekdays, 23 March to 6 November 2026. This is IG's own mid from AutoBot 161's archive, with sell and buy prices rebuilt from IG's typical spread, as in the earlier tests.
- **2024–2025:** built here the same way, from the same vendor's ticks that 161's 2024–25 candles were made from:
  - 5-minute bid and ask candles from the ticks (`data/research/tick_check_20261111/`);
  - the time zone corrected by the table measured on 11 November (`research.ticks.shift_hours`);
  - mid = (bid + ask) / 2 for each of open, high, low and close;
  - sell = mid − half IG's typical spread for that half hour of the week, and buy = mid + half, rounded outward (`research.ticks.ig_prices`);
  - candles at times IG is closed are dropped.

  The data has 517 complete weekdays (every 5-minute candle from 07:00 to 19:00 UK), 39 of them trend days by the owner's rule (17:00 UK close at least 80 pips from the 07:00 open). The hourly candles and the hourly read are built from these 5-minute candles.
- **Costs:** as in the earlier tests. Sells open at the sell price and close at the buy price, buys the mirror, with nothing added.
- **Missing data:** a signal is skipped if its candles aren't consecutive, or if the band's 20-hour window has missing time while the market is open. For 2024–25, the market is taken as open from Sunday 22:00 to Friday 19:55 UK, because the vendor's week usually starts at 22:00 (Claude's choice). So the vendor's missing first IG hour on Sunday, 21:00–22:00, is **not** counted as missing. In 2026 it was, and that is the Monday-morning difference above.

## Month by month

Trades / win rate / pips.

### 2026

| Month | Owner's shape (E) | D |
|---|---|---|
| 2026-03 | 0 | 2 / 50.0% / +6.0 |
| 2026-04 | 0 | 1 / 0.0% / -12.0 |
| 2026-05 | 2 / 50.0% / -6.6 | 5 / 80.0% / +21.3 |
| 2026-06 | 9 / 44.4% / +35.2 | 20 / 55.0% / +76.2 |
| 2026-07 | 3 / 66.7% / +15.0 | 4 / 75.0% / +45.7 |
| 2026-08 | 7 / 28.6% / -33.2 | 13 / 61.5% / +58.3 |
| 2026-09 | 5 / 80.0% / +31.5 | 5 / 80.0% / +19.2 |
| 2026-10 | 1 / 100.0% / +51.8 | 5 / 40.0% / +27.8 |

### 2024–2025

| Month | Owner's shape (E) | D |
|---|---|---|
| 2024-01 | 5 / 40.0% / -16.9 | 14 / 42.9% / -13.6 |
| 2024-02 | 3 / 66.7% / +76.0 | 8 / 50.0% / +76.1 |
| 2024-03 | 1 / 100.0% / +12.1 | 2 / 50.0% / +0.8 |
| 2024-04 | 5 / 60.0% / +21.8 | 12 / 33.3% / -39.7 |
| 2024-05 | 4 / 50.0% / +4.3 | 9 / 44.4% / -12.9 |
| 2024-06 | 6 / 50.0% / -4.4 | 6 / 50.0% / +11.7 |
| 2024-07 | 7 / 42.9% / -35.3 | 13 / 53.8% / +15.1 |
| 2024-08 | 6 / 16.7% / -45.0 | 14 / 35.7% / -49.5 |
| 2024-09 | 3 / 0.0% / -36.0 | 6 / 33.3% / +1.7 |
| 2024-10 | 5 / 40.0% / -24.6 | 12 / 25.0% / -89.6 |
| 2024-11 | 4 / 25.0% / -25.8 | 10 / 30.0% / -18.5 |
| 2024-12 | 7 / 57.1% / +23.2 | 14 / 50.0% / +25.8 |
| 2025-01 | 3 / 33.3% / +9.5 | 9 / 33.3% / -29.4 |
| 2025-02 | 3 / 33.3% / -23.5 | 6 / 50.0% / -5.2 |
| 2025-03 | 2 / 100.0% / +16.0 | 3 / 66.7% / +4.1 |
| 2025-04 | 0 | 1 / 0.0% / -12.0 |
| 2025-05 | 2 / 100.0% / +32.1 | 2 / 100.0% / +31.1 |
| 2025-06 | 6 / 50.0% / -15.0 | 7 / 57.1% / -8.5 |
| 2025-07 | 4 / 25.0% / -33.1 | 8 / 37.5% / +1.3 |
| 2025-08 | 5 / 40.0% / +3.4 | 11 / 45.5% / -15.1 |
| 2025-09 | 8 / 50.0% / +0.7 | 14 / 57.1% / +30.4 |
| 2025-10 | 9 / 44.4% / -36.1 | 9 / 55.6% / +20.2 |
| 2025-11 | 5 / 40.0% / +5.5 | 12 / 58.3% / +41.5 |
| 2025-12 | 8 / 62.5% / +77.8 | 12 / 41.7% / -26.7 |

## Where the vendor data could change the answer

1. **Candle colours and closes:** the owner's shape depends on these.
   - On the one week where the vendor can be checked against IG at 5-minute level (23–31 March 2026), the vendor's candle colour matched IG's on **92%** of candles. IG's own mid matches IG's sell chart on 98%.
   - So about 1 candle in 13 could flip between "reverses" and "doesn't", and the confirmation close can differ too.
   - That changes *which* signals appear. It shouldn't bias the result one way, but on about 100 trades it's enough to move the total by tens of pips.
2. **Highs and lows:** the pierce and D's trigger depend on these. The vendor's are typically 0.5 pips from IG's, and 90% are within about 1.2. Moving the 3-pip threshold by half a pip either way barely changes the answer (from the runs below), so this is not decisive.
3. **Wicks:** the vendor shows fewer 2+ pip wicks than IG; it missed about 28–31% of IG's on the check week. Neither shape here uses a wick rule, but the trail uses the last 3 candles' highs and lows.
4. **The week's open:** this one matters, as above. The vendor lacks IG's first hour on Sunday. Counting it as missing (as in 2026) removes most Monday-morning signals; not counting it keeps them. On 2024–25, Monday mornings lost 27.1 pips for the owner's shape and 45.6 for D.
5. **Spreads:** both data sets charge IG's typical spread, so wider spreads around news are not charged in either.
6. **What is unaffected:** the hourly read and the hourly band use hourly closes, which the vendor matches closely (daily highs and lows typically 0.2–0.3 pips from IG's).

### The runs behind this

```
2024-25|E {'2024': {'n': 56, 'w': 24, 'rate': 42.9, 'pips': -50.6}, '2025': {'n': 55, 'w': 27, 'rate': 49.1, 'pips': 37.3}} | no Monday before 12:00 UK: {'n': 101, 'w': 46, 'rate': 45.5, 'pips': 13.8}
2024-25|D {'2024': {'n': 120, 'w': 49, 'rate': 40.8, 'pips': -92.6}, '2025': {'n': 94, 'w': 47, 'rate': 50.0, 'pips': 31.7}} | no Monday before 12:00 UK: {'n': 199, 'w': 90, 'rate': 45.2, 'pips': -15.3}
2026|E {'2026': {'n': 27, 'w': 14, 'rate': 51.9, 'pips': 93.7}} | no Monday before 12:00 UK: {'n': 27, 'w': 14, 'rate': 51.9, 'pips': 93.7}
2026|D {'2026': {'n': 55, 'w': 33, 'rate': 60.0, 'pips': 242.5}} | no Monday before 12:00 UK: {'n': 55, 'w': 33, 'rate': 60.0, 'pips': 242.5}
2026 E pierce>2.5: {'n': 29, 'w': 15, 'rate': 51.7, 'pips': 133.4} pierce>3: {'n': 27, 'w': 14, 'rate': 51.9, 'pips': 93.7} pierce>3.5: {'n': 26, 'w': 14, 'rate': 53.8, 'pips': 105.7}
2026 D pierce>2.5: {'n': 58, 'w': 34, 'rate': 58.6, 'pips': 245.9} pierce>3: {'n': 55, 'w': 33, 'rate': 60.0, 'pips': 242.5} pierce>3.5: {'n': 51, 'w': 31, 'rate': 60.8, 'pips': 203.1}
2024-25 E pierce>2.5: {'n': 118, 'w': 55, 'rate': 46.6, 'pips': 1.3} pierce>3: {'n': 111, 'w': 51, 'rate': 45.9, 'pips': -13.3} pierce>3.5: {'n': 104, 'w': 47, 'rate': 45.2, 'pips': -29.1}
2024-25 D pierce>2.5: {'n': 228, 'w': 104, 'rate': 45.6, 'pips': -34.8} pierce>3: {'n': 214, 'w': 96, 'rate': 44.9, 'pips': -60.9} pierce>3.5: {'n': 200, 'w': 90, 'rate': 45.0, 'pips': -55.1}
```

## What this means

- **The 2026 result doesn't hold across all three years.** The hourly read plus the owner's times helped on 2026 and 2025, but 2024 lost with both shapes.
- **Comparing the shapes:**
  - The owner's shape (E) trades about half as often as D.
  - E held up better on 2024–25 (−13.3 against −60.9), and it turns positive there without Monday mornings.
  - On 2026, D is ahead.
- **Before going further:** take the Monday-morning question to the owner. Should a signal count when the band's 20 hours include the weekend's first hour? The 2024–25 runs suggest Monday-morning signals are poor in any case.

## Files

`data/research/shape_vs_d_20261115/` (not in git):
- `vendor.py`: the 2024–25 build;
- `shape.py`: both shapes on both data sets;
- `sens.py` and `sens.txt`: by year, without Monday mornings, and the thresholds;
- `result.json`: every trade.
