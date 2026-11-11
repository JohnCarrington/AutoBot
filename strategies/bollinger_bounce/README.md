# bollinger_bounce

**What it does:** Looks for price piercing a Bollinger band and bouncing back: a reversal candle within 3 candles of the pierce, then a confirmation candle within 3 candles of the reversal candle. It is the only strategy that may have a second trade open in the opposite direction.

Its ideas are the shared rejection part's bounce triggers (`rejection/`, design 3.3): a level pierced or come within 3 pips of, or the band really pierced; the first red reversal candle within 3 candles; a confirmation close within 3 candles; the idea when price goes below the confirmation candle's low; cancelled above the reversal candle's high; spread spikes ignored. The reversal/piercing size and the watch-window mark are recorded in the reason, never used as filters.

Each idea carries its setup's candles (`setup_context`) for the pace and target rule (`trading/against_trend.py`, design 3.3): against open trend trades, a bounce opens only at a significant level in their direction (within 5 pips) with price moving under 5 pips an hour over the last 2 hours, and then closes every trade open the other way. The engine applies it just before the order is sent.

**What it must never do:** Never send orders itself; its trade ideas go through the safety rules first. Never have more than 1 trade open in each direction.
