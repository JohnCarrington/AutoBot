# range_trade

**What it does:** Trades between the edges of a range. The whole trade is closed when price reaches the opposite band (`range_trade.close_percent_at_opposite_band`, 100; owner, 11 November 2026), by the trade manager (`trade_manager/manager.py`).

It opens right at the band (design 3.4; owner, 13 November 2026): a sell as soon as price reaches the upper band, a buy as soon as it reaches the lower band; no turn candle and no trigger. Reaching the band: within 3 pips of it or past it (`rejection.near_level_within_pips`), the band as it stood at the last finished candle; a candle with a spread spike does not count. It closes only at the opposite band (in full), its 12-pip stop, 20:30 and 15 minutes before big news: not on a rejection at a level (owner, 13 November 2026).

**What it must never do:** Never send orders itself; its trade ideas go through the safety rules first. Never trade when the analyser says the market is not ranging.
