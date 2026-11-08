# trading

**What it does:** Puts the bot together inside the price service (`engine.py`): after each finished 5-minute candle the analyser takes it, the trade manager runs every open trade on it, the strategies run on it (the same code as the replay) and every idea goes to the order sender, which applies the safety rules before anything is sent; every second the trade manager runs the open trades on the latest price. The master switch `TRADING` in `.env`: while it is off everything runs and is recorded, but the order sender is in paper mode and nothing is ever sent to IG.

`python -m trading.replay_check`: over 26 October to 6 November 2026, the full wired path (strategies, safety rules, order sender in paper mode, trade manager) gives the same trades, closed at the same time and price, as `docs/research/all_strategies_together_20261108.md`.

**What it must never do:** Never log in to IG (it uses the price service's login). Never send an order while `TRADING` is off. Never stop the price service: a problem is reported and trading stops, the prices go on.
