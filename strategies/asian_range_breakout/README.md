# asian_range_breakout

**What it does:** The Asian range breakout (design 3.7; owner, 16 November 2026). UK times, sell prices as on the chart.

1. **Asian range:** the high and low of the 5-minute candles from 00:00 to 07:00 UK (`asian_range_breakout.range_from`, `range_until`).
2. **Breakout:** from 07:00 to 10:00 UK (`breakout_from`, `breakout_until`) a 5-minute candle closes above the Asian high (a buy) or below the Asian low (a sell). A wick does not count, nor a close exactly on the line.
3. **Entry:** the next candle's open (live: its first price). Never sent late.
4. **One trade each way per day:** every close beyond gives an idea; the safety rules refuse it once a trade that way has opened that day (the idea's `once_a_day`). A close whose idea was refused does not use up the day.

It opens without hindrance, like the bounce: not the analyser's state, the direction rule, the hourly read, the trend still going, the most at once or one view at a time. Still: its switch `STRATEGY_ASIAN_RANGE_BREAKOUT`, `TRADING`, the pause switch, the trading hours (06:00 to 20:30) and big-news windows, one trade at a time in each direction, and the size, risk and funds checks.

**Exits** (trade manager): the 12-pip stop (`asian_range_breakout.stop_loss_pips`); the trail once 12 pips up (`trail_from_pips`), behind the last 3 finished candles (`trail_candles`), moved at IG; the 100-pip take profit; the 20:30 close and the close 15 minutes before big news.

**What it must never do:** Never send orders itself; its trade ideas go through the safety rules first.
