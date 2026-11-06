# levels

**What it does:** Works out the price levels the bot cares about: pivots, round numbers, the previous day's high and low, session highs and lows, and recent turning levels (looking back 2 weeks). Levels within 5 pips of each other are treated as lining up.

**What it must never do:** Never place, change or close a trade. Never decide on its own whether a trade should be taken; it only supplies levels.
