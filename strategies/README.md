# strategies

**What it does:** Holds one subfolder per strategy (design section 3). Each strategy looks for its own setup and, when its entry price is reached, produces a candidate. A candidate becomes a **trade idea** only if all of these allow it at that moment (`common.py`): the strategy's `.env` switch is on; the analyser's current state allows the strategy (design 2.2, including "in the trend's direction only"); and the direction rule allows that direction (design 2.3, using the entry price). Otherwise it is kept as blocked, with every reason.

- `slow_grind/` (3.1), `ema_pullback/` (3.2), `bollinger_bounce/` (3.3), `range_trade/` (3.4).
- The bounce and the range trade take their triggers from the shared rejection part (`rejection/`), which follows 3.3 and 3.4 step by step.
- Each idea records: the pair, strategy, direction, the moment the entry price was reached, the entry price, the market state and direction at that moment, the direction rule's answer, and the reason step by step.
- `replay.py` / `python -m strategies <from> <to> [--blocked]`: every idea between two UTC times from the stored candles (the week replayed from its open; an entry is shown at the start of the candle it was reached in).

Ideas only, for now: nothing here is in the price service yet.

**What it must never do:** Never send orders to IG, or place, change or close a trade. Never skip the safety rules. Never give an idea the analyser or the direction rule has not allowed.
