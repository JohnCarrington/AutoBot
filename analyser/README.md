# analyser

**What it does:** Reads the candles, the levels and the rejection part, decides which of the five market states the market is in, and decides which strategies are allowed to look for trades right now.

**What it must never do:** Never place, change or close a trade. Never let a strategy run that is not allowed in the current market state.
