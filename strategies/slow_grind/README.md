# slow_grind

**What it does:** Design 3.1 exactly (written for a sell; a buy is the mirror image). Every pair of candles in opposite directions, in either order, starts a pause; its lowest point is the lowest low of its candles. Once 3 candles in a row after the start (`slow_grind.min_pause_candles`) have made no new low and closed below the 21 EMA, it is a pause (a new low starts the row again); the idea comes as soon as price breaks below the pause's lowest point. A close above the 21 EMA cancels it. No time limit, no size test. Several pauses can run at once. The choices section 3.1 leaves open are listed in `strategy.py`.

**What it must never do:** Never send orders itself; its ideas go through the checks in `strategies/common.py` first.
