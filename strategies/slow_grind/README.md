# slow_grind

**What it does:** Design 3.1 exactly, rules 2 to 4 (rule 1, the two-candle start, was removed by the owner on 7 November 2026; written for a sell, a buy is the mirror image). Once 3 candles in a row (`slow_grind.min_pause_candles`) have failed to make a new low (below the last low made) while closing below the 21 EMA, it is a pause; the idea comes as soon as price breaks below the lowest point of the pause. A close above the 21 EMA cancels it. No time limit. The choices section 3.1 leaves open are listed in `strategy.py`.

**What it must never do:** Never send orders itself; its ideas go through the checks in `strategies/common.py` first.
