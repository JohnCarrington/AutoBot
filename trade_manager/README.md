# trade_manager

**What it does:** Runs each open trade by its own strategy's exits (design sections 3 and 4; `manager.py`) and tells the order sender to close it, in full or by half. On each price bar, in order: the scheduled close (20:30 UK every day for the bounce, range trade, slow grind and level reversal; 20:30 UK on Friday for the EMA pullback and breakout; 15 minutes before big news for the bounce, range trade and level reversal); the stop at IG, or the slow grind's 15/10 lock; the range trade's half close at the opposite band; the take profit at IG (100 pips on big-news days and in a trend day's direction where the design gives it); the close on a confirmed rejection at a level for the bounce and the range trade, except for a trade in the day's expected news direction on a big-news day. The stop and take profit are IG's: recorded, never sent. Every decision is recorded in `data/trade_manager/<PAIR>/decisions.jsonl`.

`python -m trade_manager.replay_check`: over 26 October to 6 November 2026, through the bot's own code, every trade closes at the same time and price as in `docs/research/all_strategies_together_20261108.md` (161 of 161).

**What it must never do:** Never open new trades. Never widen or remove a stop loss. Never touch a trade the bot did not open.

**Not connected yet** to the live service.
