# session_sweep

**What it does:** The session sweep (design 3.8; owner, 16 November 2026). UK times, sell prices. Written for a sell at a high; a buy at a low is the mirror image.

- **Levels:** the Asian high and low (00:00 to 07:00, `session_sweep.asian_range_from`, `asian_range_until`), counted from 07:00; the London high and low (07:00 to 12:00, `london_range_from`, `london_range_until`), fixed at 12:00 and counted from then. Each for the rest of its UK day.
1. **Sweep:** price goes at least 3 pips above the level (`beyond_pips`).
2. **Rejection candle:** a 5-minute candle closes back below the level. It may be the candle that went beyond, and price may stay above for any time that day. Exactly: a candle closing below the level where the candles since the last close below it, this one included, went at least 3 pips above it.
3. **Confirmation candle:** closes below the rejection candle's low within 3 candles (`confirmation_within_candles`), or the setup expires; price above the rejection candle's high first cancels it (as the bounce). While a setup waits at a level, that level starts no other.
4. **Entry:** the next candle's open (live: its first price). Never sent late.
- **Stop:** 1 pip above the sweep's furthest point (`stop_beyond_furthest_pips`), and at least 12 pips from the entry (`min_stop_pips`); the idea's `stop_price`, sent to IG as a distance from the price at sending, as the level reversal's.
- **Each level at most once a day** for a trade (the safety rules, from the idea's `once_a_day`).

It opens without hindrance, like the bounce (see `asian_range_breakout/README.md` for what still applies). Its switch: `STRATEGY_SESSION_SWEEP`.

**Exits** (trade manager): its stop; the trail once 12 pips up (`trail_from_pips`), behind the last 3 finished candles (`trail_candles`); the 100-pip take profit; the 20:30 close and the close 15 minutes before big news.

**What it must never do:** Never send orders itself; its trade ideas go through the safety rules first.
