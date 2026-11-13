# range_trade

**What it does:** Trades between the edges of a range. The whole trade is closed when price reaches the opposite band (`range_trade.close_percent_at_opposite_band`, 100; owner, 11 November 2026), by the trade manager (`trade_manager/manager.py`).

Its ideas are the shared rejection part's range triggers (`rejection/`, design 3.4): one candle reaches the band (its high goes past the upper band or comes within 3 pips of it, `rejection.near_level_within_pips`; a buy, the low and the lower band; owner, 13 November 2026: no pierce needed), the next is the rejection candle, the idea when price goes past its low during the candle after; cancelled past its high first; spread spikes ignored.

**What it must never do:** Never send orders itself; its trade ideas go through the safety rules first. Never trade when the analyser says the market is not ranging.
