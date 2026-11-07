# ema_pullback

**What it does:** Design 3.2 (written for a buy; a sell is the mirror image). Step 0: the hourly trend, with AutoBot 161's values (hourly 8, 13 and 20 EMAs in order and all rising; slopes over 3 hourly candles at least 0.16 pips an hour; gaps 0.25 and 0.20 pips). Then a 5-minute candle whose low reaches the 8 EMA (the live 8 EMA moves with the price, so this is the last finished candle's 8 EMA) and does not close below the 21 EMA. The entry is 3 pips above the highest high of the 5 candles before the first candle of the unbroken run of candles reaching the 8 EMA; the idea comes when price reaches it, within 20 minutes of the touch. A close below the 21 EMA cancels it.

**What it must never do:** Never send orders itself. Never keep a setup alive after it has expired.
