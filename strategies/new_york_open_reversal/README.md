# new_york_open_reversal

**What it does:** The New York open reversal (design 3.9; owner, 16 November 2026). UK times, sell prices. Written for a sell after a rise; a buy after a fall is the mirror image.

1. **The move:** from the open of the 07:00 candle to the close of the last candle before 13:30 UK (`new_york_open_reversal.move_from`, `move_until`), at least 30 pips up (`min_move_pips`).
2. **Rejection candle:** between 13:30 and 15:00 UK (`window_from`, `window_until`), a red 5-minute candle, whatever its size. Every rejection candle starts its own setup.
3. **Confirmation candle:** closes below the rejection candle's low within 3 candles (`confirmation_within_candles`); price above the rejection candle's high first cancels it (as the bounce). Both candles in the window.
4. **Entry:** the next candle's open (live: its first price). Never sent late.
- **One trade a day** (the safety rules, from the idea's `once_a_day`).
- **No trade on a day with big news for the pair released at 13:30 UK** (`no_trade_if_big_news_at`; `strategies.common.may_open`).

It opens without hindrance, like the bounce (see `asian_range_breakout/README.md` for what still applies). Its switch: `STRATEGY_NEW_YORK_OPEN_REVERSAL`.

**Exits** (trade manager): the 12-pip stop (`stop_loss_pips`); the trail once 12 pips up (`trail_from_pips`), behind the last 3 finished candles (`trail_candles`); the 100-pip take profit; the 20:30 close and the close 15 minutes before big news.

**What it must never do:** Never send orders itself; its trade ideas go through the safety rules first.
