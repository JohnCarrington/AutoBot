# prices

**What it does:** Receives live GBPUSD prices from IG and builds them into candles: tick, 5-minute, 1-hour, 4-hour, daily and weekly. Every other part gets its prices and candles from here.

It keeps the buy and sell prices apart in every candle, stores IG's 5-minute candles once IG marks them finished, builds 1-hour, 4-hour, daily and weekly candles from them, keeps them in `/opt/autobot/data/candles/` (one file per day per size, UTC, safe writes, never overwritten), and checks the store at start-up and after every new candle. Rules in full: `docs/PRICES_AND_CANDLES.md`.

Files: `model.py` (ticks and candles), `calendar.py` (market hours and candle boundaries), `store.py` (the candle store), `checks.py` (the store checks), `builder.py` (bigger candles from 5-minute ones), `feed.py` (puts it together), `run.py` (the live run), `history_fill.py` (filling recorded gaps and the one-off fill).

**What it must never do:** Never place, change or close a trade. Never ask IG for historical prices except through the history door, and only to fill recorded gaps. Never invent or fill in missing prices: if prices stop arriving, it must say so rather than carry on with old data. Never store a mid price, never overwrite a stored candle, and never delete candles.
