# range_trade

**What it does:** Trades between the edges of a range. Half of the trade (50%) is closed when price reaches the opposite band.

**What it must never do:** Never send orders itself; its trade ideas go through the safety rules first. Never trade when the analyser says the market is not ranging.
