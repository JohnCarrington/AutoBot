# Why the afternoon trades were stopped out: Wednesday 18 November 2026

Read-only. Nothing was changed or restarted. Everything here comes from the bot's own records and logs and the stored candles:
- `data/records/GBPUSD/trades.jsonl`
- `data/orders/GBPUSD/orders.jsonl`
- `data/records/GBPUSD/decisions.jsonl`
- `logs/prices.log.1`, which covers 17 Nov 21:20 to 18 Nov 21:20, and `logs/prices.log`, from 18 Nov 21:20
- `data/candles/GBPUSD` (5m and 1h)

The times are UK time; in November that is GMT, so the log's "GMT" is UK time. Prices are sell (bid) prices, as on the chart. Where a stop was hit, the buy (offer) price is given too, because IG fills a sell trade's stop at the offer.

## Two corrections to the background

- **The Bollinger bounce did not close the Asian range breakout.** The breakout sell was closed by IG at its trailed stop at 09:25:12, and the bounce opened afterwards, at 09:30:01.
  - Breakout close: `"closed_utc": "2026-11-18T09:25:12Z", ... "how_closed": "stopped by IG", "close_reason": "the stop at IG (trailed to 13158.5)"`
  - Bounce open: `"opened_utc": "2026-11-18T09:30:01Z"`
- **The bounce's record names the lower hourly Bollinger band, not S1 or S2:** `Wed 18 Nov 09:20 GMT pierce and rejection candle: its low 13150 went 9.4 pips below the lower hourly Bollinger band (13159.4 at that moment), and it closed green (13151.4 to 13155.3)`

## 1. Every trade, 06:00 to 20:30 UK

| # | Opened | Closed | Strategy | Dir | Open (signal / IG fill) | Stop | Take profit | Close | Pips | How it closed | Analyser state at open | Hourly read at open |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 07:30:02 | 09:25:12 | Asian range breakout | sell | 13179.8 / 13180.2 | 13192.2 | 13080.2 | 13158.5 | +21.7 | the stop at IG (trailed to 13158.5) | emerging trend up | ranging (13186.8 to 13219.6) |
| 2 | 09:30:01 | 11:03:23 | Bollinger bounce | buy | 13161.5 / 13163.1 | 13151.1 | 13263.1 | 13170.3 | +7.2 | the stop at IG (trailed to 13170.3) | trend down, slow grind | sell-off (range 13150.6 to 13211.1) |
| 3 | 12:37:37 | 13:07:56 | EMA pullback | sell | 13156.2 / 13156.4 | 13168.4 | 13056.4 | 13169.0 | −12.6 | the stop at IG | trend down, slow grind | sell-off (range 13148 to 13206.9) |
| 4 | 15:44:06 | 22:58:18 | breakout | sell | 13153.7 / 13152.9 | 13164.9 | 13102.9 | 13164.9 | −12.0 | the stop at IG (IG's level) | emerging trend down | sell-off (range 13148 to 13201.9) |
| 5 | 16:20:25 | 16:58:29 | EMA pullback | sell | 13140.8 / 13141.1 | 13153.1 | 13041.1 | 13153.1 | −12.0 | the stop at IG (IG's level) | trend down, strong push | sell-off (range 13148 to 13198.6) |
| 6 | 16:37:27 | 16:58:29 | slow grind | sell | 13138.2 / 13138.1 | 13153.1 | 13038.1 | 13153.1 | −15.0 | the stop at IG | trend down, strong push | sell-off (range 13148 to 13198.6) |
| 7 | 19:50:58 | 20:19:49 | level reversal | sell | 13135.7 / 13135.8 | 13147.1 | 13115.8 | 13147.1 | −11.3 | the stop at IG (IG's level) | trend down, slow grind | sell-off (range 13135.5 to 13192.7) |

Where each column comes from:
- **Trade details:** the trade records' `opened_utc`, `entry_price`, `open_price`, `stop_price`, `take_profit_price`, `closed_utc`, `close_price`, `pips`, `close_reason` and `market_state` fields.
- **Hourly read:** the record's "allowed at entry" step (quoted in part 2).
- **Trade 4:** it opened inside 06:00–20:30 but closed at 22:58, outside it. It is included because it was stopped out.

**Hand closes (IG channel "SYSTEM"): none.** IG reports every one of these closes with channel SYSTEM, but each one was at the stop level IG held. That is IG's stop, not a hand close. From `orders.jsonl`:
```
2026-11-18T09:25:13Z AB261118073003-e0728f6f how: stopped by IG level 13158.5 ig_stop_level 13158.5 channel SYSTEM
2026-11-18T11:03:23Z AB261118093004-63abaf9b how: stopped by IG level 13170.3 ig_stop_level 13170.3 channel SYSTEM
2026-11-18T13:07:56Z AB261118123737-487acb12 how: stopped by IG level 13169.0 (no channel recorded; "expected": "stopped by IG")
2026-11-18T16:58:29Z AB261118163727-fdafdecc how: stopped by IG level 13153.1 ig_stop_level 13153.1 channel SYSTEM
2026-11-18T16:58:30Z AB261118162026-27e65c6f how: stopped by IG level 13153.1 ig_stop_level 13153.1 channel SYSTEM
2026-11-18T20:19:50Z AB261118195058-28e04fad how: stopped by IG level 13147.1 ig_stop_level 13147.1 channel SYSTEM
2026-11-18T22:58:18Z AB261118154406-7bfbc777 how: stopped by IG level 13164.9 ig_stop_level 13164.9 channel SYSTEM
```
Every trade record has `"closed_by": "bot"`.

## 2. The afternoon stop-outs

There were five, all sells:
- **#3**, opened 12:37, before the change;
- **#4, #5, #6 and #7**, all opened after the 13:35 change.

### Which rule allowed each one

Each trade record's own "allowed at entry" step:

- **#3, EMA pullback 12:37:37: before 13:35 (old rules).**
  `allowed at entry: EMA pullback in a trend down; direction rule sell side (price 13156.2 is below the pivot 13200.1 and below the 5m 100 EMA 13174.1); hourly sell-off: the Wed 18 Nov 08:00 GMT hourly candle closed at 13153.3, 16.8 pips below the low 13170.1 of the 12 hourly candles before it; the hourly range 13148 to 13206.9`
  Its setup: `step 0, hourly 8/13/20 EMAs in order, falling; slopes 2.99, 2.76, 2.21 pips/hour (min 0.16); gaps 6.60 and 5.05 pips (min 0.25 and 0.2)`, `price rose to the 5-minute 8 EMA 13163.2 (high 13164.5); closed 13161.1, below the 21 EMA`
- **#4, breakout 15:44:06: after 13:35 (new rules).**
  `allowed at entry: breakout in a emerging trend down; direction rule sell side (price 13153.7 is below the pivot 13200.1 and below the 5m 100 EMA 13168.1); the direction rule does not apply to breakout; hourly sell-off: the Wed 18 Nov 08:00 GMT hourly candle closed at 13153.3, 16.8 pips below the low 13170.1 of the 12 hourly candles before it; the hourly range 13148 to 13201.9`
  Its setup: `breakout: the analyser moved from ranging to an emerging trend down: broke out of the range: 2 closes below the band (last 13155.0, band 13155.8); entry: below the breakout candle low 13153.7, within 3 candles`
- **#5, EMA pullback 16:20:25: after 13:35.**
  `allowed at entry: EMA pullback in a trend down; direction rule sell side (price 13140.8 is below the pivot 13200.1 and below the 5m 100 EMA 13165.4); hourly sell-off: the Wed 18 Nov 08:00 GMT hourly candle closed at 13153.3, 16.8 pips below the low 13170.1 of the 12 hourly candles before it; the hourly range 13148 to 13198.6`
  Its setup: `step 0, hourly 8/13/20 EMAs in order, falling; slopes 2.44, 2.48, 2.19 pips/hour (min 0.16); gaps 6.64 and 6.40 pips (min 0.25 and 0.2)`, `price rose to the 5-minute 8 EMA 13151.6 (high 13152.4); closed 13143.4, below the 21 EMA`
- **#6, slow grind 16:37:27: after 13:35.**
  `allowed at entry: slow grind in a trend down; direction rule sell side (price 13138.2 is below the pivot 13200.1 and below the 5m 100 EMA 13163.9); the direction rule does not apply to slow grind; hourly sell-off: the Wed 18 Nov 08:00 GMT hourly candle closed at 13153.3, 16.8 pips below the low 13170.1 of the 12 hourly candles before it; the hourly range 13148 to 13198.6`
  Its setup: `slow grind: the last low made: 13135.5; a pause: 2 candles in a row without a new low, closing below the 21 EMA; its lowest point 13138.2; price broke below it (during this candle)`
- **#7, level reversal 19:50:58: after 13:35.**
  `allowed at entry: level reversal in a trend down; direction rule sell side (price 13135.7 is below the pivot 13200.1 and below the 5m 100 EMA 13155.1); the direction rule does not apply to level reversal; hourly sell-off: the Wed 18 Nov 08:00 GMT hourly candle closed at 13153.3, 16.8 pips below the low 13170.1 of the 12 hourly candles before it; the hourly range 13135.5 to 13192.7`
  Its setup: `level reversal: pierced S2 13140.2 at 19:30, reversal 19:35, confirmed 19:45, broke it 19:50`. It opened from the live check, while the 19:50 candle was still forming. The finished candle gave no idea:
  - its low, 13135.6, went below the trigger price 13135.7, and its high, 13139.9, went above the reversal candle's high 13139.2;
  - for a candle that went both ways, `rejection/watch.py` treats the setup as cancelled ("from candles alone the order is unknown").

**What allowed #4 to #7 under the new rules.** ANALYSER_GOVERNS_ALL (check 7) was on for all four, and none of their records carries an `ANALYSER_GOVERNS_ALL:` reason. In `strategies/common.py` `governs_reasons`, a trade in an emerging trend or trend is refused only if it goes against the trend:
```python
elif st in (EMERGING, TREND):
    if direction != want:
        out.append(f"ANALYSER_GOVERNS_ALL: the {st} is {d}: {strategy} only in the trend's direction")
```
Each of these was a sell in a down state. The hourly-ranging part of check 7 (`if hourly is not None and hourly.state == HOURLY_RANGING ...`) didn't come into play either: the hourly read said sell-off at every one of these entries.

**The hourly read said "sell-off" all afternoon, based on the 08:00 hourly candle.** All five records quote the same break: `the Wed 18 Nov 08:00 GMT hourly candle closed at 13153.3, 16.8 pips below the low 13170.1 of the 12 hourly candles before it`. The bot's hourly read never said consolidation or ranging during these trades. The hourly candles themselves (below) stayed between 13135.5 and 13157.5 from 16:00 to 20:59.

### Each stop-out in candles

Sell prices on the chart; buy high and low show where a sell trade's stop is hit. From the stored candles (data/candles/GBPUSD).

#### #3, EMA pullback sell 12:37

Hourly candles, 09:00 to 13:00 UK:

| Start (UK) | Sell open | Sell high | Sell low | Sell close | Buy high | Buy low |
|---|---|---|---|---|---|---|
| 09:00 | 13153.2 | 13172.1 | 13148 | 13170.8 | 13173.4 | 13149.5 |
| 10:00 | 13170.6 | 13175.6 | 13163.6 | 13173.7 | 13177.1 | 13165.1 |
| 11:00 | 13173.5 | 13173.8 | 13154.4 | 13157 | 13175.3 | 13155.9 |
| 12:00 | 13156.7 | 13166.9 | 13149.7 | 13160.1 | 13168.4 | 13151.2 |
| 13:00 | 13159.8 | 13172.6 | 13159.4 | 13162.6 | 13174.1 | 13160.9 |

5-minute candles from the open (12:37:37) to the stop-out (2026-11-18 13:07):

| Start (UK) | Sell open | Sell high | Sell low | Sell close | Buy high | Buy low |
|---|---|---|---|---|---|---|
| 12:35 | 13160.9 | 13162.7 | 13154.3 | 13159.1 | 13164.2 | 13155.8 |
| 12:40 | 13159.2 | 13161.6 | 13155.5 | 13156.5 | 13163.1 | 13157 |
| 12:45 | 13156.8 | 13158.4 | 13149.7 | 13152.3 | 13159.9 | 13151.2 |
| 12:50 | 13152.5 | 13157.4 | 13150.9 | 13156.6 | 13158.9 | 13152.4 |
| 12:55 | 13156.5 | 13161 | 13155.9 | 13160.1 | 13162.5 | 13157.4 |
| 13:00 | 13159.8 | 13165.5 | 13159.8 | 13160.1 | 13167 | 13161.3 |
| 13:05 | 13160.9 | 13170.4 | 13160.5 | 13167.9 | 13171.9 | 13161.4 |

The hour after the stop (5-minute candles 13:10 to 14:05):

| Start (UK) | Sell open | Sell high | Sell low | Sell close | Buy high | Buy low |
|---|---|---|---|---|---|---|
| 13:10 | 13168 | 13172.6 | 13167.2 | 13167.6 | 13174.1 | 13168.7 |
| 13:15 | 13167.7 | 13167.7 | 13163.1 | 13166.1 | 13169.2 | 13164.6 |
| 13:20 | 13166.2 | 13168.6 | 13163.8 | 13164.1 | 13170.1 | 13165.3 |
| 13:25 | 13164.2 | 13166.4 | 13161.1 | 13161.2 | 13167.9 | 13162.6 |
| 13:30 | 13160.7 | 13165.2 | 13159.4 | 13164.2 | 13166.7 | 13160.9 |
| 13:35 | 13163.7 | 13167.1 | 13163.4 | 13166.7 | 13168.6 | 13164.9 |
| 13:40 | 13166.8 | 13169.9 | 13166.2 | 13167.8 | 13171.4 | 13167.7 |
| 13:45 | 13167.7 | 13171.5 | 13165.2 | 13171.5 | 13173 | 13166.7 |
| 13:50 | 13171.9 | 13171.9 | 13167.1 | 13168.2 | 13173.4 | 13168.6 |
| 13:55 | 13167.6 | 13169 | 13162.3 | 13162.6 | 13170.5 | 13163.8 |
| 14:00 | 13162.9 | 13166.5 | 13162.4 | 13165.1 | 13167.8 | 13163.9 |
| 14:05 | 13165 | 13166.8 | 13163.1 | 13163.9 | 13168.3 | 13164.6 |


#### #5, EMA pullback sell 16:20

Hourly candles, 13:00 to 17:00 UK:

| Start (UK) | Sell open | Sell high | Sell low | Sell close | Buy high | Buy low |
|---|---|---|---|---|---|---|
| 13:00 | 13159.8 | 13172.6 | 13159.4 | 13162.6 | 13174.1 | 13160.9 |
| 14:00 | 13162.9 | 13169.1 | 13157 | 13164.2 | 13170.6 | 13158.5 |
| 15:00 | 13165 | 13168.6 | 13148.1 | 13148.1 | 13170.1 | 13149.3 |
| 16:00 | 13147.8 | 13152.4 | 13135.5 | 13150.2 | 13153.9 | 13136.8 |
| 17:00 | 13150.3 | 13155.1 | 13143.9 | 13151.6 | 13156.6 | 13145.4 |

5-minute candles from the open (16:20:25) to the stop-out (2026-11-18 16:58):

| Start (UK) | Sell open | Sell high | Sell low | Sell close | Buy high | Buy low |
|---|---|---|---|---|---|---|
| 16:20 | 13143.2 | 13143.4 | 13135.5 | 13138.3 | 13144.9 | 13136.8 |
| 16:25 | 13138.7 | 13143 | 13138.7 | 13140.4 | 13144.5 | 13140.2 |
| 16:30 | 13140.3 | 13140.9 | 13138.2 | 13140.8 | 13142.4 | 13139.7 |
| 16:35 | 13141 | 13142.6 | 13136.3 | 13137.7 | 13144.1 | 13137.8 |
| 16:40 | 13137.8 | 13142.1 | 13136.1 | 13142 | 13143.6 | 13137.6 |
| 16:45 | 13141.9 | 13145.1 | 13141.4 | 13143.5 | 13146.6 | 13142.9 |
| 16:50 | 13143.4 | 13149 | 13143.4 | 13149 | 13150.5 | 13144.9 |
| 16:55 | 13149.1 | 13152.3 | 13147.8 | 13150.2 | 13153.8 | 13149.3 |

The hour after the stop (5-minute candles 17:00 to 17:55):

| Start (UK) | Sell open | Sell high | Sell low | Sell close | Buy high | Buy low |
|---|---|---|---|---|---|---|
| 17:00 | 13150.3 | 13151.6 | 13147.4 | 13147.4 | 13153 | 13148.9 |
| 17:05 | 13147.5 | 13148.8 | 13144.1 | 13144.3 | 13150.3 | 13145.6 |
| 17:10 | 13145 | 13149.7 | 13143.9 | 13148.8 | 13151.1 | 13145.4 |
| 17:15 | 13148.7 | 13151.3 | 13148.5 | 13149 | 13152.8 | 13150 |
| 17:20 | 13149.1 | 13151.4 | 13148.6 | 13151.3 | 13152.9 | 13150.1 |
| 17:25 | 13151.2 | 13155.1 | 13150.9 | 13154.8 | 13156.6 | 13152.4 |
| 17:30 | 13154.7 | 13155 | 13151.4 | 13151.7 | 13156.5 | 13152.8 |
| 17:35 | 13151.8 | 13152.9 | 13150.5 | 13151.2 | 13154.4 | 13152 |
| 17:40 | 13151.1 | 13152.1 | 13149.2 | 13150.6 | 13153.6 | 13150.7 |
| 17:45 | 13150.5 | 13150.5 | 13147.8 | 13149 | 13152 | 13148.8 |
| 17:50 | 13149.1 | 13149.4 | 13147.2 | 13148.7 | 13150.9 | 13148.7 |
| 17:55 | 13148.6 | 13152 | 13148.1 | 13151.6 | 13153.5 | 13149.6 |


#### #6, slow grind sell 16:37

Hourly candles, 13:00 to 17:00 UK:

| Start (UK) | Sell open | Sell high | Sell low | Sell close | Buy high | Buy low |
|---|---|---|---|---|---|---|
| 13:00 | 13159.8 | 13172.6 | 13159.4 | 13162.6 | 13174.1 | 13160.9 |
| 14:00 | 13162.9 | 13169.1 | 13157 | 13164.2 | 13170.6 | 13158.5 |
| 15:00 | 13165 | 13168.6 | 13148.1 | 13148.1 | 13170.1 | 13149.3 |
| 16:00 | 13147.8 | 13152.4 | 13135.5 | 13150.2 | 13153.9 | 13136.8 |
| 17:00 | 13150.3 | 13155.1 | 13143.9 | 13151.6 | 13156.6 | 13145.4 |

5-minute candles from the open (16:37:27) to the stop-out (2026-11-18 16:58):

| Start (UK) | Sell open | Sell high | Sell low | Sell close | Buy high | Buy low |
|---|---|---|---|---|---|---|
| 16:35 | 13141 | 13142.6 | 13136.3 | 13137.7 | 13144.1 | 13137.8 |
| 16:40 | 13137.8 | 13142.1 | 13136.1 | 13142 | 13143.6 | 13137.6 |
| 16:45 | 13141.9 | 13145.1 | 13141.4 | 13143.5 | 13146.6 | 13142.9 |
| 16:50 | 13143.4 | 13149 | 13143.4 | 13149 | 13150.5 | 13144.9 |
| 16:55 | 13149.1 | 13152.3 | 13147.8 | 13150.2 | 13153.8 | 13149.3 |

The hour after the stop (5-minute candles 17:00 to 17:55):

| Start (UK) | Sell open | Sell high | Sell low | Sell close | Buy high | Buy low |
|---|---|---|---|---|---|---|
| 17:00 | 13150.3 | 13151.6 | 13147.4 | 13147.4 | 13153 | 13148.9 |
| 17:05 | 13147.5 | 13148.8 | 13144.1 | 13144.3 | 13150.3 | 13145.6 |
| 17:10 | 13145 | 13149.7 | 13143.9 | 13148.8 | 13151.1 | 13145.4 |
| 17:15 | 13148.7 | 13151.3 | 13148.5 | 13149 | 13152.8 | 13150 |
| 17:20 | 13149.1 | 13151.4 | 13148.6 | 13151.3 | 13152.9 | 13150.1 |
| 17:25 | 13151.2 | 13155.1 | 13150.9 | 13154.8 | 13156.6 | 13152.4 |
| 17:30 | 13154.7 | 13155 | 13151.4 | 13151.7 | 13156.5 | 13152.8 |
| 17:35 | 13151.8 | 13152.9 | 13150.5 | 13151.2 | 13154.4 | 13152 |
| 17:40 | 13151.1 | 13152.1 | 13149.2 | 13150.6 | 13153.6 | 13150.7 |
| 17:45 | 13150.5 | 13150.5 | 13147.8 | 13149 | 13152 | 13148.8 |
| 17:50 | 13149.1 | 13149.4 | 13147.2 | 13148.7 | 13150.9 | 13148.7 |
| 17:55 | 13148.6 | 13152 | 13148.1 | 13151.6 | 13153.5 | 13149.6 |


#### #7, level reversal sell 19:50

Hourly candles, 16:00 to 20:00 UK:

| Start (UK) | Sell open | Sell high | Sell low | Sell close | Buy high | Buy low |
|---|---|---|---|---|---|---|
| 16:00 | 13147.8 | 13152.4 | 13135.5 | 13150.2 | 13153.9 | 13136.8 |
| 17:00 | 13150.3 | 13155.1 | 13143.9 | 13151.6 | 13156.6 | 13145.4 |
| 18:00 | 13151.5 | 13157.5 | 13150.1 | 13151.9 | 13159 | 13151.6 |
| 19:00 | 13151.5 | 13151.9 | 13135.6 | 13138.8 | 13158.6 | 13137.1 |
| 20:00 | 13138.7 | 13151.6 | 13137.6 | 13150.4 | 13153.1 | 13139.1 |

5-minute candles from the open (19:50:58) to the stop-out (2026-11-18 20:19):

| Start (UK) | Sell open | Sell high | Sell low | Sell close | Buy high | Buy low |
|---|---|---|---|---|---|---|
| 19:50 | 13136.5 | 13139.9 | 13135.6 | 13138.3 | 13141.4 | 13137.1 |
| 19:55 | 13138.4 | 13139.4 | 13136.6 | 13138.8 | 13140.9 | 13138.1 |
| 20:00 | 13138.7 | 13141 | 13137.6 | 13140.7 | 13141.9 | 13139.1 |
| 20:05 | 13140.1 | 13141.9 | 13139.9 | 13140.7 | 13143.3 | 13141.4 |
| 20:10 | 13140.9 | 13141.5 | 13139.5 | 13140.3 | 13143 | 13141 |
| 20:15 | 13140.4 | 13146.1 | 13140.4 | 13145.8 | 13147.6 | 13141.9 |

The hour after the stop (5-minute candles 20:20 to 21:15):

| Start (UK) | Sell open | Sell high | Sell low | Sell close | Buy high | Buy low |
|---|---|---|---|---|---|---|
| 20:20 | 13145.6 | 13148 | 13144.4 | 13146 | 13149.5 | 13145.9 |
| 20:25 | 13145.9 | 13148.4 | 13145.6 | 13148.3 | 13149.9 | 13147.1 |
| 20:30 | 13148.1 | 13150.1 | 13147.6 | 13149.2 | 13151.6 | 13149.1 |
| 20:35 | 13149.1 | 13149.4 | 13147.6 | 13148.7 | 13150.9 | 13149.1 |
| 20:40 | 13148.5 | 13149.5 | 13147.3 | 13147.6 | 13151 | 13148.8 |
| 20:45 | 13147.4 | 13149.1 | 13146.1 | 13148.5 | 13150.6 | 13147.6 |
| 20:50 | 13148.4 | 13150.4 | 13147.6 | 13150.4 | 13151.9 | 13149.1 |
| 20:55 | 13150.2 | 13151.6 | 13149.7 | 13150.4 | 13153.1 | 13150.6 |
| 21:00 | 13150.5 | 13151.3 | 13149.5 | 13151.3 | 13152.8 | 13150.8 |
| 21:05 | 13151.2 | 13151.3 | 13148.3 | 13148.3 | 13152.8 | 13149.8 |
| 21:10 | 13148.5 | 13150.2 | 13148.2 | 13148.6 | 13151.7 | 13149.7 |
| 21:15 | 13148.2 | 13149.2 | 13147.3 | 13147.6 | 13150.7 | 13148.8 |


#### #4, breakout sell 15:44

Hourly candles, 12:00 to 16:00 UK:

| Start (UK) | Sell open | Sell high | Sell low | Sell close | Buy high | Buy low |
|---|---|---|---|---|---|---|
| 12:00 | 13156.7 | 13166.9 | 13149.7 | 13160.1 | 13168.4 | 13151.2 |
| 13:00 | 13159.8 | 13172.6 | 13159.4 | 13162.6 | 13174.1 | 13160.9 |
| 14:00 | 13162.9 | 13169.1 | 13157 | 13164.2 | 13170.6 | 13158.5 |
| 15:00 | 13165 | 13168.6 | 13148.1 | 13148.1 | 13170.1 | 13149.3 |
| 16:00 | 13147.8 | 13152.4 | 13135.5 | 13150.2 | 13153.9 | 13136.8 |

5-minute candles from the open (15:44:06) to the stop-out (2026-11-18 22:58):

| Start (UK) | Sell open | Sell high | Sell low | Sell close | Buy high | Buy low |
|---|---|---|---|---|---|---|
| 15:40 | 13154.6 | 13156.9 | 13151.4 | 13153.1 | 13158.4 | 13152.9 |
| 15:45 | 13153 | 13154.7 | 13149.4 | 13154.5 | 13156.2 | 13150.9 |
| 15:50 | 13154.4 | 13157.1 | 13152.2 | 13155.9 | 13158.6 | 13153.7 |
| 15:55 | 13156 | 13157.1 | 13148.1 | 13148.1 | 13158.6 | 13149.3 |
| 16:00 | 13147.8 | 13148.8 | 13143.8 | 13147.2 | 13150.3 | 13145.1 |
| 16:05 | 13147.4 | 13149 | 13144.8 | 13146.7 | 13150.5 | 13146.3 |
| 16:10 | 13147 | 13151 | 13145 | 13150.4 | 13152.5 | 13146.5 |
| 16:15 | 13150.5 | 13152.4 | 13142.7 | 13143.4 | 13153.9 | 13144.1 |
| 16:20 | 13143.2 | 13143.4 | 13135.5 | 13138.3 | 13144.9 | 13136.8 |
| 16:25 | 13138.7 | 13143 | 13138.7 | 13140.4 | 13144.5 | 13140.2 |
| 16:30 | 13140.3 | 13140.9 | 13138.2 | 13140.8 | 13142.4 | 13139.7 |
| 16:35 | 13141 | 13142.6 | 13136.3 | 13137.7 | 13144.1 | 13137.8 |
| 16:40 | 13137.8 | 13142.1 | 13136.1 | 13142 | 13143.6 | 13137.6 |
| 16:45 | 13141.9 | 13145.1 | 13141.4 | 13143.5 | 13146.6 | 13142.9 |
| 16:50 | 13143.4 | 13149 | 13143.4 | 13149 | 13150.5 | 13144.9 |
| 16:55 | 13149.1 | 13152.3 | 13147.8 | 13150.2 | 13153.8 | 13149.3 |
| 17:00 | 13150.3 | 13151.6 | 13147.4 | 13147.4 | 13153 | 13148.9 |
| 17:05 | 13147.5 | 13148.8 | 13144.1 | 13144.3 | 13150.3 | 13145.6 |
| 17:10 | 13145 | 13149.7 | 13143.9 | 13148.8 | 13151.1 | 13145.4 |
| 17:15 | 13148.7 | 13151.3 | 13148.5 | 13149 | 13152.8 | 13150 |
| 17:20 | 13149.1 | 13151.4 | 13148.6 | 13151.3 | 13152.9 | 13150.1 |
| 17:25 | 13151.2 | 13155.1 | 13150.9 | 13154.8 | 13156.6 | 13152.4 |
| 17:30 | 13154.7 | 13155 | 13151.4 | 13151.7 | 13156.5 | 13152.8 |
| 17:35 | 13151.8 | 13152.9 | 13150.5 | 13151.2 | 13154.4 | 13152 |
| 17:40 | 13151.1 | 13152.1 | 13149.2 | 13150.6 | 13153.6 | 13150.7 |
| 17:45 | 13150.5 | 13150.5 | 13147.8 | 13149 | 13152 | 13148.8 |
| 17:50 | 13149.1 | 13149.4 | 13147.2 | 13148.7 | 13150.9 | 13148.7 |
| 17:55 | 13148.6 | 13152 | 13148.1 | 13151.6 | 13153.5 | 13149.6 |
| 18:00 | 13151.5 | 13154.1 | 13150.1 | 13154 | 13155.6 | 13151.6 |
| 18:05 | 13153.9 | 13157.1 | 13153.5 | 13157 | 13158.6 | 13155 |
| 18:10 | 13156.9 | 13156.9 | 13152 | 13152 | 13158.4 | 13153.5 |
| 18:15 | 13151.9 | 13152.8 | 13150.5 | 13151.4 | 13154.3 | 13152 |
| 18:20 | 13151.2 | 13154.1 | 13150.9 | 13153.5 | 13155.6 | 13152.4 |
| 18:25 | 13153.4 | 13155 | 13153.2 | 13153.6 | 13156.5 | 13154.7 |
| 18:30 | 13153 | 13154.9 | 13152.9 | 13153.9 | 13156.4 | 13154.4 |
| 18:35 | 13153.8 | 13157.2 | 13153.8 | 13156.8 | 13158.7 | 13155.3 |
| 18:40 | 13156.7 | 13157.5 | 13156 | 13157.2 | 13159 | 13157.5 |
| 18:45 | 13157.3 | 13157.3 | 13154.1 | 13154.9 | 13158.8 | 13155.6 |
| 18:50 | 13154.8 | 13154.8 | 13152.7 | 13153.8 | 13156.3 | 13154.2 |
| 18:55 | 13153.9 | 13154.9 | 13151.9 | 13151.9 | 13158.3 | 13154.3 |
| 19:00 | 13151.5 | 13151.9 | 13145.6 | 13145.9 | 13158.6 | 13147.1 |
| 19:05 | 13146 | 13146.5 | 13139.3 | 13142.2 | 13148 | 13140.8 |
| 19:10 | 13141.9 | 13142.8 | 13140.9 | 13142.3 | 13144.3 | 13142.4 |
| 19:15 | 13142.2 | 13143.5 | 13139.9 | 13143.4 | 13145 | 13141.4 |
| 19:20 | 13143.5 | 13145.2 | 13140.8 | 13141.4 | 13146.7 | 13142.3 |
| 19:25 | 13141.3 | 13141.4 | 13138.9 | 13139.8 | 13142.9 | 13140.4 |
| 19:30 | 13139.7 | 13140.9 | 13137.9 | 13138.2 | 13142.4 | 13139.4 |
| 19:35 | 13138.3 | 13139.2 | 13136.7 | 13137.3 | 13140.7 | 13138.2 |
| 19:40 | 13137.2 | 13137.9 | 13136.3 | 13137.9 | 13139.4 | 13137.8 |
| 19:45 | 13137.8 | 13138.5 | 13135.7 | 13135.9 | 13139.4 | 13137.2 |
| 19:50 | 13136.5 | 13139.9 | 13135.6 | 13138.3 | 13141.4 | 13137.1 |
| 19:55 | 13138.4 | 13139.4 | 13136.6 | 13138.8 | 13140.9 | 13138.1 |
| 20:00 | 13138.7 | 13141 | 13137.6 | 13140.7 | 13141.9 | 13139.1 |
| 20:05 | 13140.1 | 13141.9 | 13139.9 | 13140.7 | 13143.3 | 13141.4 |
| 20:10 | 13140.9 | 13141.5 | 13139.5 | 13140.3 | 13143 | 13141 |
| 20:15 | 13140.4 | 13146.1 | 13140.4 | 13145.8 | 13147.6 | 13141.9 |
| 20:20 | 13145.6 | 13148 | 13144.4 | 13146 | 13149.5 | 13145.9 |
| 20:25 | 13145.9 | 13148.4 | 13145.6 | 13148.3 | 13149.9 | 13147.1 |
| 20:30 | 13148.1 | 13150.1 | 13147.6 | 13149.2 | 13151.6 | 13149.1 |
| 20:35 | 13149.1 | 13149.4 | 13147.6 | 13148.7 | 13150.9 | 13149.1 |
| 20:40 | 13148.5 | 13149.5 | 13147.3 | 13147.6 | 13151 | 13148.8 |
| 20:45 | 13147.4 | 13149.1 | 13146.1 | 13148.5 | 13150.6 | 13147.6 |
| 20:50 | 13148.4 | 13150.4 | 13147.6 | 13150.4 | 13151.9 | 13149.1 |
| 20:55 | 13150.2 | 13151.6 | 13149.7 | 13150.4 | 13153.1 | 13150.6 |
| 21:00 | 13150.5 | 13151.3 | 13149.5 | 13151.3 | 13152.8 | 13150.8 |
| 21:05 | 13151.2 | 13151.3 | 13148.3 | 13148.3 | 13152.8 | 13149.8 |
| 21:10 | 13148.5 | 13150.2 | 13148.2 | 13148.6 | 13151.7 | 13149.7 |
| 21:15 | 13148.2 | 13149.2 | 13147.3 | 13147.6 | 13150.7 | 13148.8 |
| 21:20 | 13147.3 | 13148.6 | 13145.4 | 13146.7 | 13150.1 | 13146.9 |
| 21:25 | 13146.6 | 13147.5 | 13145 | 13145.7 | 13149 | 13146.5 |
| 21:30 | 13145.8 | 13146.8 | 13145.5 | 13146.1 | 13148.3 | 13147 |
| 21:35 | 13146 | 13147.7 | 13145.9 | 13146.9 | 13149.2 | 13147.4 |
| 21:40 | 13146.8 | 13148.7 | 13146.7 | 13147.8 | 13150.2 | 13148.2 |
| 21:45 | 13147.3 | 13148.3 | 13145.9 | 13147.6 | 13149.8 | 13148.3 |
| 21:50 | 13147.5 | 13147.9 | 13146.7 | 13147.4 | 13149.5 | 13148.3 |
| 21:55 | 13143.9 | 13146.9 | 13142.2 | 13142.2 | 13153.7 | 13149.9 |
| 22:00 | 13137.3 | 13139.7 | 13136.3 | 13137.9 | 13156.6 | 13153.2 |
| 22:05 | 13139.8 | 13141.9 | 13139.8 | 13141.9 | 13158.8 | 13156.7 |
| 22:10 | 13142.3 | 13144.8 | 13142.3 | 13143.3 | 13161.7 | 13159.2 |
| 22:15 | 13143.4 | 13143.5 | 13141.8 | 13141.9 | 13160.4 | 13158.7 |
| 22:20 | 13142.8 | 13144.8 | 13142.8 | 13143.3 | 13161.7 | 13159.7 |
| 22:25 | 13143.2 | 13146.3 | 13143.2 | 13144.6 | 13161.6 | 13159.9 |
| 22:30 | 13144.5 | 13145.3 | 13144.5 | 13145.3 | 13162.2 | 13161.4 |
| 22:35 | 13145.1 | 13145.6 | 13145 | 13145.3 | 13162.3 | 13161.8 |
| 22:40 | 13145.2 | 13145.6 | 13145.2 | 13145.3 | 13162.3 | 13161.9 |
| 22:45 | 13145.4 | 13146.6 | 13145.3 | 13146.5 | 13162.3 | 13161.6 |
| 22:50 | 13146.6 | 13147.4 | 13145.7 | 13146.7 | 13161.9 | 13160 |
| 22:55 | 13147.1 | 13150.5 | 13147 | 13150.3 | 13165.2 | 13158.5 |

The hour after the stop (5-minute candles 23:00 to 23:55):

| Start (UK) | Sell open | Sell high | Sell low | Sell close | Buy high | Buy low |
|---|---|---|---|---|---|---|
| 23:00 | 13150.2 | 13150.2 | 13144.7 | 13146.2 | 13161.7 | 13149.7 |
| 23:05 | 13146.5 | 13148 | 13146.3 | 13147.6 | 13150.2 | 13148.1 |
| 23:10 | 13147.7 | 13148.7 | 13146.7 | 13146.9 | 13150.4 | 13148.2 |
| 23:15 | 13146.8 | 13146.9 | 13145.8 | 13146.7 | 13148.4 | 13147.3 |
| 23:20 | 13146.8 | 13147.1 | 13145.9 | 13146.8 | 13148.6 | 13147.4 |
| 23:25 | 13146.9 | 13148 | 13146.6 | 13146.9 | 13149.5 | 13148.1 |
| 23:30 | 13146.7 | 13147 | 13146.5 | 13146.8 | 13148.5 | 13148 |
| 23:35 | 13146.6 | 13147.1 | 13145.3 | 13146.1 | 13148.6 | 13146.8 |
| 23:40 | 13146.2 | 13147.4 | 13145.7 | 13147.1 | 13148.9 | 13147.2 |
| 23:45 | 13146.8 | 13147.1 | 13146 | 13146 | 13148.6 | 13147.5 |
| 23:50 | 13146.1 | 13146.5 | 13145.5 | 13145.7 | 13148 | 13147 |
| 23:55 | 13146 | 13146.1 | 13145 | 13145.1 | 13147.6 | 13146.5 |


### What price did in the hour after each stop

Sell prices, from the 5-minute candles above.

| # | Stop | Hour after the stop: sell high | Sell low | Last close | The trade's entry | Carried on, or came back? |
|---|---|---|---|---|---|---|
| 3 | 13168.4 (filled 13169.0), 13:07:56 | 13172.6 (13:10) | 13159.4 (13:30) | 13163.9 (14:05) | 13156.2 | Went 4.2 pips above the stop at 13:10, then came back down 13 pips to 13159.4. It never got back to the entry. |
| 4 | 13164.9, 22:58:18 | 13150.2 (23:00) | 13144.7 (23:00) | 13145.1 (23:55) | 13153.7 | The sell price never came near the stop (see below). Throughout the hour it was below the entry, which is the trade's way. |
| 5 | 13153.1, 16:58:29 | 13155.1 (17:25) | 13143.9 (17:10) | 13151.6 (17:55) | 13140.8 | At most 2.0 pips past the stop. It moved sideways between 13143.9 and 13155.1 and never got back to the entry. |
| 6 | 13153.1, 16:58:29 | the same hour as #5 | | | 13138.2 | The same as #5. |
| 7 | 13147.1, 20:19:49 | 13151.6 (20:55) | 13144.4 (20:20) | 13147.6 (21:15) | 13135.7 | Up to 4.5 pips past the stop, ending the hour just above it. It never came back towards the entry. |

**#4 was stopped by the 22:55 rollover spread, not by the sell price.** A sell trade's stop is hit on the buy price. In the 22:55 candle the buy price reached the stop but the sell price was 14.4 pips below it:
```
| 22:50 | sell O 13146.6 H 13147.4 L 13145.7 C 13146.7 | buy H 13161.9 L 13160   |
| 22:55 | sell O 13147.1 H 13150.5 L 13147   C 13150.3 | buy H 13165.2 L 13158.5 |
2026-11-18 22:58:18 GMT INFO    autobot.orders: Order record: closed at IG AB261118154406-7bfbc777
```
Before 22:55 the gap between the buy and sell prices had already been about 15 pips since at least 22:40 (the 22:40 candle: sell high 13145.6, buy high 13162.3). Before the rollover, the trade had been as much as 16.1 pips in profit (`"best_pips": "16.1"`).

Its stop stayed at 13164.9 throughout:
- the order records for AB261118154406-7bfbc777 have only three events, `sending` (15:44:06), `opened` (15:44:07, `"stop_level": 13164.9`) and `closed at IG` (22:58:18);
- its decision records have only the open and the close.

Why the stop was not moved is not covered here.

## 3. The 13:35 restart, and the analyser's state changes through the day

**The restart, from the service log:**
```
2026-11-18 13:35:20 GMT INFO    autobot.prices.service: Received SIGTERM: stopping.
2026-11-18 13:35:21 GMT INFO    autobot.prices.service: AutoBot price service stopped at Wed 18 Nov 2026 13:35:21 GMT.
2026-11-18 13:35:21 GMT INFO    autobot.prices.service: AutoBot price service starting for GBPUSD (CS.D.GBPUSD.TODAY.IP).
2026-11-18 13:35:28 GMT INFO    autobot.analyser: [GBPUSD] Market states replayed from the week's open (767 candles): emerging trend (down) since 2026-11-18 13:15 UTC; 111 state change(s) this week, recorded in /opt/autobot/data/analyser/GBPUSD/state_changes.jsonl.
2026-11-18 13:36:02 GMT INFO    autobot.trading: Trading ON: 0 open trade(s) taken over; the strategies are up to 2026-11-18 13:35 UTC.
```

**The analyser's state changes as the live bot logged them, all day** (the `Market state:` lines in `logs/prices.log.1`, then `logs/prices.log` from 21:20; each line is logged when the candle it names closes):
```
00:10:00 Market state: 00:05  consolidation (none): the emerging up trend was cancelled: 2 closes in a row back below the turning_high 13204.4 it was rejected at (last 13199.7)
00:15:01 Market state: 00:10  emerging trend (up): rejected at a level: closed 13202 above the reversal high 13200.1; trigger at above 13202
00:50:00 Market state: 00:45  consolidation (none): the emerging up trend settled into consolidation: bands 12.0 pips wide ...
00:55:00 Market state: 00:50  emerging trend (down): rejected at a level: closed 13196.9 below the reversal low 13197.9; trigger at below 13194.9
01:20:00 Market state: 01:15  consolidation (none): the emerging down trend settled into consolidation: bands 12.0 pips wide ...
01:35:00 Market state: 01:30  emerging trend (up): rejected at a level: closed 13204.8 above the reversal high 13203; trigger at above 13206.7
01:45:00 Market state: 01:40  emerging trend (down): rejected at a level against the emerging up trend: closed 13202.2 below the reversal low 13203.8; trigger at below 13202.1
02:00:00 Market state: 01:55  emerging trend (up): rejected at a level against the emerging down trend: closed 13205.9 above the reversal high 13205.2; trigger at above 13206.1
02:10:00 Market state: 02:05  consolidation (none): the emerging up trend settled into consolidation: bands 11.2 pips wide ...
02:20:00 Market state: 02:15  emerging trend (up): rejected at a level: closed 13206 above the reversal high 13203.8; trigger at above 13206.6
02:30:01 Market state: 02:25  consolidation (none): the emerging up trend settled into consolidation: bands 12.1 pips wide ...
02:55:00 Market state: 02:50  emerging trend (down): rejected at a level: closed 13201.3 below the reversal low 13202.4; trigger at below 13200.2
03:15:00 Market state: 03:10  trend (down, slow grind): the rejection became a trend: a bounce failed under the 21 EMA and middle band, then a new low 13195.0 on the lower band 13195.7; ...
04:40:01 Market state: 04:35  consolidation (none): the down trend ran out of steam: bands 8.9 pips wide ...
05:35:00 Market state: 05:30  emerging trend (down): broke out of the consolidation: close 13191.1 below the lower band 13191.5
05:45:00 Market state: 05:40  consolidation (none): the emerging down trend was cancelled: 2 closes in a row back inside the Bollinger bands after the breakout (last 13193.9)
05:55:00 Market state: 05:50  emerging trend (down): broke out of the consolidation: close 13190.5 below the lower band 13190.8
06:15:00 Market state: 06:10  consolidation (none): the emerging down trend was cancelled: 2 closes in a row back inside the Bollinger bands after the breakout (last 13191.7)
07:05:00 Market state: 07:00  emerging trend (down): broke out of the consolidation: close 13176.7 below the lower band 13183.1
07:20:00 Market state: 07:15  emerging trend (up): rejected at a level against the emerging down trend: closed 13181.7 above the reversal high 13177.2; trigger at above 13182.7
08:10:01 Market state: 08:05  emerging trend (down): rejected at a level against the emerging up trend: closed 13171.4 below the reversal low 13172.2; trigger at below 13163.9
08:40:01 Market state: 08:35  trend (down, slow grind): the rejection became a trend: a bounce failed under the 21 EMA and middle band, then a new low 13159.0 on the lower band 13158.8; EMAs 7/13/21 stacked down for 40 candles, close 13160.4 below them and the 100 EMA 13188.8; band sloping -1.1 pips/candle
        [13:35 restart: "emerging trend (down) since 2026-11-18 13:15 UTC", from the replay above; no Market state line logged]
14:55:00 Market state: 14:50  consolidation (none): the emerging down trend settled into consolidation: bands 12.7 pips wide (narrow: <= 14, or narrowing for 6 candles: 8), middle band 0.1 pips/candle, no close outside the bands for 6 candles, average body 2.4 pips, green/red 1.5
15:05:01 Market state: 15:00  ranging (none): bands 12.9 pips wide (close together: 6 to 18) and flat (upper -0.1, lower 0.1 pips/candle), both bands reached, EMAs weaving, 100 EMA moved 1.7 pips
15:40:01 Market state: 15:35  emerging trend (down): broke out of the range: 2 closes below the band (last 13155.0, band 13155.8)
15:55:01 Market state: 15:50  emerging trend (up): rejected at a level against the emerging down trend: closed 13155.9 above the reversal high 13154.7; trigger at above 13157.1
16:05:01 Market state: 16:00  consolidation (none): the emerging up trend was cancelled: 2 closes in a row back below the round_number 13150.0 it was rejected at (last 13147.2)
16:20:01 Market state: 16:15  trend (down, strong push): the trend proof held in consolidation: a bounce failed under the 21 EMA and middle band, then a new low 13142.7 on the lower band 13142.8; EMAs 7/13/21 stacked down for 12 candles, close 13143.4 below them and the 100 EMA 13165.4; band sloping -1.7 pips/candle
16:40:01 Market state: 16:35  trend (down, slow grind): slow grind: 73% of the body size red, bands 2.9x as wide as 12 candles ago, 7/21 EMAs 7.8 pips apart, 2 closes on the band
19:00:01 Market state: 18:55  consolidation (none): the down trend ran out of steam: bands 9.5 pips wide (narrow: <= 14, or narrowing for 6 candles: 3), middle band 0.3 pips/candle, no close outside the bands for 6 candles, average body 1.6 pips, green/red 1.2
19:30:01 Market state: 19:25  trend (down, slow grind): the trend proof held in consolidation: a bounce failed under the 21 EMA and middle band, then a new low 13138.9 on the lower band 13139.2; EMAs 7/13/21 stacked down for 5 candles, close 13139.8 below them and the 100 EMA 13156.6; band sloping -1.5 pips/candle
21:45:00 Market state: 21:40  consolidation (none): the down trend ran out of steam: bands 10.9 pips wide ...
23:15:00 Market state: 23:10  ranging (none): bands 11.0 pips wide (close together: 6 to 18) and flat ...
23:25:00 Market state: 23:20  consolidation (none): bands 10.8 pips wide ...
23:35:01 Market state: 23:30  ranging (none): bands 10.6 pips wide ...
23:50:01 Market state: 23:45  consolidation (none): bands 7.0 pips wide ...
```
Each line is shortened to its time and text: the log prefix `GMT INFO autobot.analyser: [GBPUSD]` and the day are left out. Where a line ends in "...", the full text is in the log.

**There are no live state lines between 08:40 and 14:55.** In the live log the state stays "trend down, slow grind" from 08:35 until the 13:35 restart. Under the new code, the restart's replay of the week put the state at "emerging trend (down) since 13:15". The analyser journal (`state_changes.jsonl`) also has entries between 09:30 and 13:15. Those were written by that replay at 13:35, not by the live bot at the time; this was found in the 18 Nov review and is annotated by fix ee3eaa6 (`docs/research/execution_integrity_20261119/`).

## 4. Summary

**What the afternoon market did.** From the stored candles:
- **12:00 to 15:15:** sideways between about 13149.7 and 13172.6.
- **15:15 to 16:20:** a 33-pip fall to 13135.5, which was the low of the day and just under S2 (13140.2).
- **16:20 to 18:55:** after a 17-pip bounce, sideways between 13135.5 and 13157.5.
- **19:00:** the FOMC minutes took price back down to 13135.6 by 19:50.
- **20:00 to 20:30:** back up to about 13150.

On the hourly chart, the five hourly candles from 16:00 to 20:59 all stayed inside 13135.5 to 13157.5, a 22-pip band. That fits Johnny's reading of consolidation. The bot's hourly read did not call it that: it said "sell-off", from the 08:00 hourly candle, at every afternoon entry. The 5-minute analyser called "trend down" at 16:15 and 19:25, near the bottom of each fall.

**Why each stop-out happened:**
- **#3, EMA pullback, 12:37 (old rules).** It sold a rise to the 5-minute 8 EMA at 13156.2, near the bottom of the midday range. Price rose to the top of that range and took the stop at 13:07 (the 13:05 candle's buy high was 13171.9, and the trade filled at 13169.0). Within the next 25 minutes price came back to 13159.4, but not to the entry.
- **#5 EMA pullback (16:20) and #6 slow grind (16:37) (new rules).** Both sold after the 33-pip fall, at 13140.8 and 13138.2, within 5 pips of the day's low, 13135.5. Neither got more than 5 pips in its favour (the record's `best_pips` is 4.3 and 0.5). Price then bounced 17 pips: the 16:55 candle's buy high of 13153.8 hit both stops at 13153.1, at 16:58. For the next hour price moved sideways between 13143.9 and 13155.1, so it neither carried on far nor came back to the entries.
- **#7, level reversal, 19:50 (new rules).** It sold at 13135.7 after the 16-pip FOMC fall, 0.1 pip above that fall's low of 13135.6. It was never in profit (`"best_pips": "-1.3"`). The 20:15 candle rose to a sell high of 13146.1 (buy high 13147.6) and took the stop at 20:19. The next hour went up to 13151.6 and ended at 13147.6.
- **#4, breakout, 15:44 (new rules).** It sold the break out of the 15:00 range at 13152.9 and was up to 16.1 pips in profit. It wasn't stopped by price: the 22:55 rollover spread took the buy price to 13165.2 while the sell price was at most 13150.5. The stop of 13164.9 had never been moved. In the hour after, the sell price stayed between 13144.7 and 13150.2, below the entry.
