# breakout

**What it does:** Design 3.5 (owner, 7 November 2026). Only at the moment the analyser moves into an emerging trend because price broke out of a range, or because a candle closed outside the band out of a consolidation: a buy when price then breaks above that candle's high, a sell when it breaks below its low, within 3 candles (`breakout.trigger_within_candles`), or the setup expires. Only in the direction of the day's move so far (a buy above the day's 00:00 UK open, a sell below it); the direction rule does not apply. Stop 6 pips and take profit 50 pips (`breakout.stop_loss_pips`, `breakout.take_profit_pips`); no close on a rejection at a level; new trades from 06:00 to 20:30 UK; may open during big news, may be held overnight, closed at 20:30 UK on Friday; one breakout trade at a time.

**What it must never do:** Never send orders itself; its ideas go through the checks in `strategies/common.py` first.
