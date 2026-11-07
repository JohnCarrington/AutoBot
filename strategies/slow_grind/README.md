# slow_grind

**What it does:** Design 3.1 (written for a sell; a buy is the mirror image). A pause starts with a red candle then a green one that does not break the red one's low, both closing below the 21 EMA. Once 3 candles in a row (`slow_grind.min_pause_candles`) have made no new low and closed below the 21 EMA, it is a pause; the idea comes as soon as price breaks below the pause's low (at the open, if a candle opens below it). A close above the 21 EMA cancels it. No time limit, no size test.

**What it must never do:** Never send orders itself; its ideas go through the checks in `strategies/common.py` first.
