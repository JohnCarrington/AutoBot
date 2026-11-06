# slow_grind

**What it does:** Looks for a slow, steady move that pauses for at least 3 candles, and produces a trade idea in the direction of the move.

**What it must never do:** Never send orders itself; its trade ideas go through the safety rules first. Never use a stop loss other than the one in the settings (6 pips).
