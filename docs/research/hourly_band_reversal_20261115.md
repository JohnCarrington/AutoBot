# Normal-day reversals: the price-only signal at the hourly Bollinger band (15 November 2026)

**Status: research only. Nothing in the bot or in AutoBot 161 was changed. Waiting for the owner.**

## What was asked (owner, 15 November 2026)

Take the price-only reversal signal from the previous round and only take it when price is at the hourly
Bollinger band (20, 2): sells at the upper hourly band, buys at the lower.

- **The signal:** a new 1-hour high or low; candle 1 or 2 has a wick of 2 pips or more; candle 2 closes against
  the push; entry at candle 3's open; 07:00 to 19:00 UK; 12-pip stop.
- **Days:** normal days from 25 October to 13 November 2026 (every day except the trend days 6, 9, 10 and
  11 November), with the same 30 turns of 30 pips or more as the previous rounds.
- **Asked for:**
  1. how close to the hourly band counts as "at" it, with options and results;
  2. turns caught, false signals and pips, against the signal without the band;
  3. the exits fixed 12, 20 and 30, and a trail behind the last 3 candles once +12;
  4. on top: keep IG's 12-pip stop, but the bot closes the trade itself if price goes back past the turn
     candle's high (sell) or low (buy).

**Data:** the bot's own 5-minute candles (sell price), from a copy of its IG candle store. Rules the owner
did not give are marked as Claude's.

## The result

**In short: the hourly band filter is the first addition that helped under every setting I tried.** It removes most of the false signals and catches nearly as many turns. The bot closing the trade itself past the turn candle doesn't reliably save anything.

Two readings of mine to check:
- **"At the band"** is judged on the highest high (or lowest low) of candles 1 and 2. The distance is measured on the sell price, against the hourly band at that candle's close.
- **"Hourly band"** is the live one, as on your chart: the last 19 finished hours plus the current price. I also tested a band from finished hours only; the results are very similar (in `p3_grid.txt`).

## 1–3. How close counts as "at" the band, with each exit

All rows use your signal: 07:00–19:00 UK, 12-pip stop, and one trade at a time in each direction (my rule from last time).

**Fixed 12-pip target**

| At the band means | Trades | Turns caught | False | Pips |
|---|---|---|---|---|
| No band filter (last time) | 89 | 12 / 30 | 77 | +12 |
| Through it by 2+ pips | 19 | 7 | 12 | +60 |
| Touching or through it | 27 | 9 | 18 | +60 |
| Within 2 pips | 29 | 9 | 20 | +84 |
| **Within 3 pips** | 32 | 9 | 23 | **+96** |
| Within 5 pips | 39 | 11 | 28 | +60 |
| Within 10 pips | 53 | 11 | 42 | +84 |

**Pips with the other exits**

| At the band means | Fixed 20 | Fixed 30 | Trail behind last 3 candles once +12 |
|---|---|---|---|
| No band filter | −20 | −108 | −8 |
| Through it by 2+ pips | +52 | +18 | +72 |
| Touching or through it | +64 | +60 | +109 |
| Within 2 pips | +84 | +72 | +128 |
| **Within 3 pips** | +92 | +90 | **+131** |
| Within 5 pips | +96 | +72 | +101 |
| Within 10 pips | +112 | +30 | +121 |

- **Every distance and every exit is now positive.** Without the band, the signal ranged from +12 to −108.
- **The filter mostly removes false signals.** With "within 3 pips", false signals drop from 77 to 23 while caught turns only drop from 12 to 9.
- **Best combination: within 3 pips with the trail.** That gave +131 pips on 32 trades. The 9 caught turns made +170, including +53 and +42 on the 29 and 30 October turns. The 23 false signals lost only 39, because many of them still made something.
- **More reassuring than last time:** the result doesn't flip from one setting to the next.
- **Ceiling on catches:** 8 of the 30 turns came outside 07:00–19:00, so 22 is the most the hours allow. The band filter catches 9 to 11 of those.

## 4. The bot closing the trade past the turn candle

**(my readings)**
- **"The turn candle's high"** is the higher of candles 1 and 2. The wick is often on candle 2, and price is already past candle 1's high by the entry.
- **The trigger** is the chart's sell price; the trade closes at the real buy price (mirrored for buys).
- **IG's 12-pip stop stays in place.** The turn's extreme was typically only 6 pips from the entry (range 2 to 16), so the bot's close is usually the nearer of the two.

I compared it on exactly the same trades. Otherwise closing early frees the one-trade slot, which lets in extra signals and muddies the comparison.

| At the band | Exit | False signals: 12-pip stop only | With the bot's close | Total pips |
|---|---|---|---|---|
| Touching | Trail 3 | −61 | −61 | +109 → +109 |
| Within 3 | Fixed 12 | −12 | −22 | +96 → +86 |
| Within 3 | Fixed 20 | −88 | −77 | +92 → +103 |
| Within 3 | Fixed 30 | −96 | −79 | +90 → +115 |
| Within 3 | Trail 3 | −39 | −42 | +131 → +127 |
| Within 5 | Trail 3 | −95 | −78 | +101 → +118 |
| Within 10 | Trail 3 | −75 | −107 | +121 → +88 |
| No filter | Trail 3 | −202 | −204 | −8 → −10 |

- **It does cut the losers:** a false signal that went wrong typically lost about 6 pips instead of 12, and about half the false signals were cut this way.
- **But it also closes trades that would have won.** Some false signals dip back past the turn high and then still reach the target, and each of those costs 12–20 pips.
- **Overall the two roughly cancel out:** between about −50 and +30 pips depending on the setting, with no steady direction.
- **A 2-pip margin past the turn high** (a number I tried, as an option) doesn't change that.
- **When it is allowed to take the extra trades** it frees up, it is worse in nearly every case (in `p3_inval.txt`).

## How much to trust this

- These are 11 days and 32 to 53 trades, all measured on the same days the rules were picked on.
- The band filter holding up under every setting is a better sign than last time's single best number, but it is still not proof.
- 5-minute candles can't show which came first inside a candle, so a stop and a target in the same candle were counted as the stop.

## Files

- Results tables, kept next to this write-up:
  - `hourly_band_reversal_20261115_p3_grid.txt`: every distance and exit, for both the live and the finished-hour band.
  - `hourly_band_reversal_20261115_p3_same.txt`: step 4, the bot's close on the same trades.
  - `hourly_band_reversal_20261115_p3_inval.txt`: the bot's close with the extra trades allowed, and the trade
    list for "within 3 pips" with the trail.
- The scripts and every file from the three rounds of this research (levels, price only, hourly band) are in
  `data/research/hourly_band_reversal_20261115/` (not in git). That includes `prep.py` and its candle extract
  `prep.pkl`, and `p3.py`, `p3_same.py` and `p3_inval.py` for this round.
