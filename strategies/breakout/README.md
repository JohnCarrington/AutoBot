# breakout

**What it does:** Design 3.5 (owner, 7 November 2026). Only at the moment the analyser moves from consolidation to an emerging trend because a candle closed outside the Bollinger band: a buy when price then breaks above that candle's high, a sell when it breaks below its low, within 3 candles (`breakout.trigger_within_candles`), or the setup expires. Hours, news and Friday rules as for the EMA pullback. Its stop and take profit (`breakout.stop_loss_pips`, `breakout.take_profit_pips`) are not chosen yet (0), so it stays switched off (`STRATEGY_BREAKOUT=off`); the bot will not start with it on while either is 0.

**What it must never do:** Never send orders itself; its ideas go through the checks in `strategies/common.py` first.
