# range_trade

**What it does:** Trades between the edges of a range. Half of the trade (50%) is closed when price reaches the opposite band.

Its ideas are the shared rejection part's range triggers (`rejection/`, design 3.4): one candle pierces the band, the next is the rejection candle, the idea when price goes past its low during the candle after; cancelled past its high first; spread spikes ignored. The half close at the other band is for the trade manager (not built yet).

**What it must never do:** Never send orders itself; its trade ideas go through the safety rules first. Never trade when the analyser says the market is not ranging.
