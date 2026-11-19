# bollinger_bounce

**What it does:** The bounce off the **hourly** Bollinger band, entered on the 5-minute chart (design 3.3; owner, 15 November 2026). Written for a sell; a buy is the mirror image.

1. **Pierce:** a 5-minute candle's high goes more than 3 pips (`bounce.pierce_beyond_pips`) above the hourly upper Bollinger band (20, 2), the band as the IG hourly chart showed it at that moment: the forming hour's band with the high as its close (`prices/hourly_chart.py`).
2. **Rejection candle:** that same candle, red, whatever its size.
3. **Confirmation candle:** a later candle closes below the rejection candle's low within 3 candles (`bounce.confirmation_within_candles`), or the setup expires.
4. **Entry:** the next candle's open (live: its first price). Never sent late.
5. **Cancelled** if price goes above the rejection candle's high first.

Spread spikes (`rejection.max_spread_pips`) cannot make a pierce or cancel a setup. With an hour missing from the hourly chart, nothing starts.

It opens without hindrance: not the analyser's state, the direction rule, the hourly read, the one-view-at-a-time rule or the most at once. Still: its switch, `TRADING`, the pause switch, the trading hours and big-news windows, one bounce at a time in each direction, and the size, risk and funds checks. Two switches of its own in `.env`, both off unless set: `BOUNCE_ONLY_WHEN_HOURLY_RANGING` (only while the hourly read says ranging) and `BOUNCE_ONLY_NEAR_TIMES` (only within 60 minutes of 10:00, 14:00 or 16:00 UK; `bounce.near_times` in `config/settings.toml`). These are checked in `strategies/common.py` (check 5). It closes nothing else when it opens.

**Exits** (trade manager): the 12-pip stop; the trail once 12 pips up (`bounce.trail_from_pips`), behind the last 3 finished candles (`bounce.trail_candles`), moved at IG; the 100-pip take profit; the 20:30 close and the close before big news.

**What it must never do:** Never send orders itself; its trade ideas go through the safety rules first.
