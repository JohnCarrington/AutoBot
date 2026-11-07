# ema_pullback

**What it does:** Design 3.2 exactly (written for a buy; a sell is the mirror image). Step 0: the hourly trend, with AutoBot 161's values. Every 5-minute candle whose low reaches the 8 EMA (the last finished candle's 8 EMA, which is where the live 8 EMA meets the price) and does not close below the 21 EMA starts a setup. The entry is 3 pips above the highest high of the 5 completed candles immediately before the touch candle (161's rule); the idea comes when price reaches it, within 20 minutes of the touch. A close below the 21 EMA cancels it. Several setups can run at once. The choices section 3.2 leaves open are listed in `strategy.py`.

**What it must never do:** Never send orders itself. Never keep a setup alive after it has expired.
