# bollinger_bounce

**What it does:** Looks for price piercing a Bollinger band and bouncing back: a reversal candle within 3 candles of the pierce, then a confirmation candle within 3 candles of the reversal candle. It is the only strategy that may have a second trade open in the opposite direction.

**What it must never do:** Never send orders itself; its trade ideas go through the safety rules first. Never have more than 1 trade open in each direction.
