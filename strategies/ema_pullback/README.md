# ema_pullback

**What it does:** Looks for price pulling back to the moving average (EMA) in a trend. The entry is 3 pips beyond the high or low of the 5 candles before the pullback. A setup that has not triggered within 20 minutes is dropped.

**What it must never do:** Never send orders itself; its trade ideas go through the safety rules first. Never keep a setup alive after it has expired.
