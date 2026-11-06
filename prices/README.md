# prices

**What it does:** Receives live GBPUSD prices from IG and builds them into candles: tick, 5-minute, 1-hour, 4-hour, daily and weekly. Every other part gets its prices and candles from here.

**What it must never do:** Never place, change or close a trade. Never invent or fill in missing prices: if prices stop arriving, it must say so rather than carry on with old data.
