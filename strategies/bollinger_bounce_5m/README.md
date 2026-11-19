# bollinger_bounce_5m: the first build's Bollinger bounce ("Bollinger bounce 5m")

Kept and renamed alongside the hourly-pierce Bollinger bounce of 15 November 2026 (`strategies/bollinger_bounce`), so the records, Telegram and the dashboard tell them apart (owner, 19 November 2026). Its rules are exactly the first build's (9 November 2026). Switch: `STRATEGY_BOLLINGER_BOUNCE_5M`.

**What it does:** Looks for price piercing a Bollinger band and bouncing back: a reversal candle within 3 candles of the pierce, then a confirmation candle within 3 candles of the reversal candle. It is the only strategy that may have a second trade open in the opposite direction.

Its ideas are the shared rejection part's bounce triggers (`rejection/`, design 3.3): a level pierced or come within 3 pips of, or the band really pierced; the first red reversal candle within 3 candles; a confirmation close within 3 candles; the idea when price goes below the confirmation candle's low; cancelled above the reversal candle's high; spread spikes ignored. The reversal/piercing size and the watch-window mark are recorded in the reason, never used as filters.

**What it must never do:** Never send orders itself; its trade ideas go through the safety rules first. Never have more than 1 trade open in each direction.
