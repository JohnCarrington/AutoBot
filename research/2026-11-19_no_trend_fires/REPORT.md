# Why no trend strategy bought this morning: Thursday 19 November 2026, 06:00 to about 09:55 UK

Read-only. Nothing was changed or restarted. UK times; in November, UK time is GMT, which is the log's time. Sell prices.

**Sources:**
- `logs/prices.log`
- `data/records/GBPUSD/decisions.jsonl`
- `data/records/GBPUSD/trades.jsonl`
- the stored candles
- the code at main d9e5d0e

**What the bot doesn't log.** It logs every analyser state change and every strategy idea, allowed or refused. It doesn't log when a strategy looks at a candle and finds no setup, and it doesn't log the hourly read on its own.

**How I filled those gaps.** I ran today's stored candles through the live code (d9e5d0e, live switches, nothing sent) and printed the EMA pullback's own notes and the hourly read. The replay gives exactly the live results: the same state changes, and the same six slow grind ideas at the same times, refused for the same reasons as the live records below. The script is `research/2026-11-19_no_trend_fires/trend19.py`.

The service was restarted at 09:49 for Stage 4 and the live-check fix:
- `09:49:10 ... Market states replayed from the week's open (1009 candles): trend (up, slow grind) since 2026-11-19 07:45 UTC`
- `09:49:56 ... Trading ON`

Neither change touches the EMA pullback's or the slow grind's rules.

## 1. Analyser state changes and hourly read changes

**The analyser's state changes (log lines):**
```
2026-11-19 06:00:03 GMT INFO    autobot.analyser: [GBPUSD] Market state: Thu 19 Nov 05:55 GMT  emerging trend (down): rejected at a level: closed 13134.1 below the reversal low 13135; trigger at below 13133.9
2026-11-19 06:10:01 GMT INFO    autobot.analyser: [GBPUSD] Market state: Thu 19 Nov 06:05 GMT  consolidation (none): the emerging down trend settled into consolidation: bands 5.2 pips wide (narrow: <= 14, or narrowing for 6 candles: 11), middle band 0.3 pips/candle, no close outside the bands for 6 candles, average body 0.6 pips, green/red 1.3
2026-11-19 06:35:01 GMT INFO    autobot.analyser: [GBPUSD] Market state: Thu 19 Nov 06:30 GMT  emerging trend (up): rejected at a level: closed 13140 above the reversal high 13139.9; trigger at above 13141.9
2026-11-19 07:35:01 GMT INFO    autobot.analyser: [GBPUSD] Market state: Thu 19 Nov 07:30 GMT  trend (up, strong push): the rejection became a trend: a bounce failed under the 21 EMA and middle band, then a new high 13156.5 on the upper band 13154.3; EMAs 7/13/21 stacked up for 33 candles, close 13155.7 above them and the 100 EMA 13139.2; band sloping 2.0 pips/candle
2026-11-19 07:50:01 GMT INFO    autobot.analyser: [GBPUSD] Market state: Thu 19 Nov 07:45 GMT  trend (up, slow grind): slow grind: 41% of the body size green, bands 2.6x as wide as 12 candles ago, 7/21 EMAs 4.5 pips apart, 3 closes on the band
```
There has been no change since. The analyser has said **trend up since 07:30**.

**The hourly read: "sell-off" all morning, with no change.** It comes from the 03:00 hourly candle. Only its range moved, as the latest 12 hourly candles changed. From the replay:
```
06:00  hourly sell-off: the Thu 19 Nov 03:00 GMT hourly candle closed at 13125.2, 5.4 pips below the low 13130.6 of the 12 hourly candles before it; the hourly range 13119.1 to 13157.5
07:00  hourly sell-off: (the same); the hourly range 13119.1 to 13153.3
08:00  hourly sell-off: (the same); the hourly range 13119.1 to 13157.5
09:00  no change
```
The live records say the same. The 07:35 trade record has `hourly sell-off: the Thu 19 Nov 03:00 GMT hourly candle closed at 13125.2 ...`, and every slow grind refusal below has `the hourly chart is in a sell-off`.

**The 07:00 hourly candle came within 1.2 pips of turning the read into a rally.** A rally needs an hourly close at least 3 pips above the highest high of the 12 hourly candles before it (`analyser/hourly_read.py`: `elif close >= top + beyond: state, since_i = RALLY, i`). Worked out from the stored hourly candles:

| Hourly candle | Close | Highest high of the 12 before it | Close needed for a rally |
|---|---|---|---|
| 06:00 | 13138.7 | 13157.5 (18 Nov 18:00) | 13160.5 |
| 07:00 | 13155.1 | 13153.3 (19 Nov 00:00) | 13156.3 |
| 08:00 | 13155.5 | 13157.5 (19 Nov 07:00) | 13160.5 |

## 2. Every check of the EMA pullback and the slow grind, and what stopped it

### EMA pullback: no idea at all since 06:00

`decisions.jsonl` has no EMA pullback line today, so it never reached the entry checks. What stopped it is its own step 0, the hourly trend.

The rule (`strategies/ema_pullback/strategy.py`):
```python
if f > m > s and f > fp and m > mp and s > sp:
    d = BUY
elif f < m < s and f < fp and m < mp and s < sp:
    d = SELL
else:
    return HourlyTrend(None, False, f"hourly EMAs not in order and all moving one way ...")
...
if trend.direction != d or not trend.qualified:
    ...
    continue
```
Step 0 each hour, from the replay:
```
06:00  sell, qualified | hourly 8/13/20 EMAs in order, falling; slopes 2.19, 2.16, 2.09 pips/hour (min 0.16); gaps 4.90 and 6.74 pips (min 0.25 and 0.2)
07:00  none            | hourly EMAs not in order and all moving one way (8 13137.6, 13 13141.7, 20 13147.9)
08:00  none            | hourly EMAs not in order and all moving one way (8 13141.5, 13 13143.6, 20 13148.6)
09:00  none            | hourly EMAs not in order and all moving one way (8 13144.6, 13 13145.3, 20 13149.3)
```
So the EMA pullback couldn't buy at any point today:
- **06:00 to 06:55:** the hourly trend was down, so only sells could start.
- **From 07:00:** the hourly EMAs were in no order the rule accepts. They were still stacked downwards (8 below 13 below 20) but no longer all falling.

In the 06:00 hour, every 5-minute candle touched the 8 EMA for a sell setup. Each was cancelled because the touch candle closed above the 21 EMA. The EMA pullback's notes, from the replay:
```
06:00 sell touched the 8 EMA 13134.3; the touch candle closed 13134.2 above the 21 EMA 13133.2: cancelled
06:05 sell touched the 8 EMA 13134.3; the touch candle closed 13133.8 above the 21 EMA 13133.3: cancelled
06:10 sell touched the 8 EMA 13134.2; the touch candle closed 13136.2 above the 21 EMA 13133.6: cancelled
06:15 sell touched the 8 EMA 13134.6; the touch candle closed 13138.0 above the 21 EMA 13134.0: cancelled
06:20 sell touched the 8 EMA 13135.4; the touch candle closed 13138.1 above the 21 EMA 13134.3: cancelled
06:25 sell touched the 8 EMA 13136.0; the touch candle closed 13139.5 above the 21 EMA 13134.8: cancelled
06:30 sell touched the 8 EMA 13136.8; the touch candle closed 13140.0 above the 21 EMA 13135.3: cancelled
06:35 sell touched the 8 EMA 13137.5; the touch candle closed 13138.3 above the 21 EMA 13135.5: cancelled
06:40 sell touched the 8 EMA 13137.7; the touch candle closed 13139.3 above the 21 EMA 13135.9: cancelled
06:45 sell touched the 8 EMA 13138.0; the touch candle closed 13140.1 above the 21 EMA 13136.3: cancelled
06:50 sell touched the 8 EMA 13138.5; the touch candle closed 13137.6 above the 21 EMA 13136.4: cancelled
06:55 sell touched the 8 EMA 13138.3; the touch candle closed 13138.7 above the 21 EMA 13136.6: cancelled
```
From 07:00 there are no notes, because the code notes a touch only when the hourly trend is in that touch's direction (`if trend.direction == d: self.notes.append(...)`).

### Slow grind: six buy ideas, all refused

Its live decisions (`decisions.jsonl`), each with the refusal reasons quoted in full:

| Time | Idea | Refused because |
|---|---|---|
| 06:10 | buy 13135.8 | `the analyser's state is consolidation, which does not allow slow grind; the hourly chart is in a sell-off: slow grind only sells; TREND_STILL_GOING is on and the trend is not still going: no new high at least 5 pips above the previous high in the last 12 five-minute candles (the most: 1.6 pips above ...)` |
| 07:00 | buy 13140.9 | `the analyser's state is emerging trend, which does not allow slow grind; the hourly chart is in a sell-off: slow grind only sells; TREND_STILL_GOING is on and the trend is not still going: no new high at least 5 pips above the previous high in the last 12 five-minute candles (the most: 4.9 pips above ...)` |
| 07:55 | buy 13155.6 | `the hourly chart is in a sell-off: slow grind only sells` |
| 08:10 | buy 13155.2 | `the hourly chart is in a sell-off: slow grind only sells` |
| 08:35 | buy 13155.1 | `the hourly chart is in a sell-off: slow grind only sells; TREND_STILL_GOING is on and the trend is not still going: no new high at least 5 pips above the previous high in the last 12 five-minute candles (the most: 1.0 pips above the swing high 13156.5 of 07:30, at 07:55)` |
| 08:50 | buy 13154 | `the hourly chart is in a sell-off: slow grind only sells; TREND_STILL_GOING is on and the trend is not still going: no new high at least 5 pips above the previous high in the last 12 five-minute candles (the most: 1.0 pips above the swing high 13156.5 of 07:30, at 07:55)` |

At 07:55 and 08:10, the only reason was the hourly read: `the hourly chart is in a sell-off: slow grind only sells`.

The code (`strategies/common.py` `hourly_reasons`, check 4; it applies to `TREND_STRATEGIES = (EMA_PULLBACK, SLOW_GRIND, BREAKOUT)`):
```python
if hourly.state == HOURLY_SELL_OFF and direction == BUY:
    return [f"the hourly chart is in a sell-off: {strategy} only sells"]
```
The slow grind's other notes, from the replay:
- one more pause, at 09:10 (`a pause (2 candles from 09:05 GMT); high 13160.7 not broken`), cancelled at 09:20 (`closed 13151.0 below the 21 EMA 13152.8 after 3 candle(s): cancelled`);
- a sell pause at 09:40 (`low 13142.3 not broken`).

## 3. Is the daily pivot (direction) rule blocking buys? No. The pivot is 13162.5.

**The pivot is 13162.5.** From the 07:35 trade record: `direction rule no clear direction (price 13155 is below the pivot 13162.5 and above the 5m 100 EMA 13139.2: they disagree)`.

**Slow grind: the direction rule doesn't apply** (`NO_DIRECTION_RULE = (RANGE_TRADE, BOLLINGER_BOUNCE, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL) + SESSION_STRATEGIES`). None of its six refusals mentions it.

**EMA pullback: the direction rule does apply, but it never got the chance.** EMA pullback never made a buy idea (part 2), so the rule was never asked. If it had been, it would have refused one. A buy needs buy side: `price above the daily pivot and the 5-minute 100 EMA` (`strategies/common.py`, check 3). The highest sell price since 06:00 is 13160.7 (the 09:00 candle), still below 13162.5.

**So the blocks this morning were:**
- **EMA pullback:** the hourly trend (its step 0).
- **Slow grind:** the hourly read ("sell-off") and, from 08:35, TREND_STILL_GOING. Before 07:30, the analyser's state also blocked it.

## 4. What would have to happen, under the current rules, for a trend buy to be allowed

**Slow grind buy.** All of these:
1. **The analyser says trend up.** It has since 07:30.
2. **The hourly read stops saying sell-off.** There are two ways (`analyser/hourly_read.py`):
   - **It turns to rally.** An hourly candle closes at least 3 pips above the highest high of the 12 hourly candles before it. For the 09:00 candle (closing at 10:00) that's 13160.5: the highest high of the 12 before it is 13157.5, at 07:00.
   - **It turns to ranging.** That happens once 12 more hourly candles have closed with no new break after the 03:00 candle: at the close of the 15:00 hourly candle, 16:00 UK. While the read is ranging, a trend buy needs a 5-minute close at least 3 pips above the hourly range high (ANALYSER_USES_HOURLY; check 4 and check 7). Until then, check 7 refuses the trend group: `the hourly chart is ranging ...: the trend group opens nothing`.
3. **TREND_STILL_GOING is met:** a new high at least 5 pips above the previous swing high, within the last 12 five-minute candles.
4. **Its own setup completes:** a pause of 2 candles without a new high, closing above the 21 EMA, then price breaks above the pause's high.

**EMA pullback buy.** All of these:
1. **Step 0 says up:** the hourly 8, 13 and 20 EMAs in order (8 above 13 above 20) and each above its value an hour before; slopes at least 0.16 pips an hour over the last 3 hourly candles; gaps at least 0.25 and 0.20 pips. At 09:00 they were still stacked the other way: 8 13144.6, 13 13145.3, 20 13149.3.
2. **Its own setup:**
   - a 5-minute candle touches the 8 EMA and doesn't close below the 21 EMA;
   - entry 3 pips above the highest high of the 5 candles before the touch;
   - it has to be reached within 20 minutes.
3. **The entry checks:**
   - the analyser in an emerging trend or trend up;
   - the direction rule on the buy side: the entry above the daily pivot, 13162.5, and above the 5-minute 100 EMA;
   - the hourly read not a sell-off (point 2 above);
   - TREND_STILL_GOING met.

## Plain English

- **Analyser:** it has called trend up since 07:30.
- **Hourly read:** still "sell-off", from the 03:00 hourly close at 13125.2. The 07:00 hourly candle closed 1.2 pips short of the close that would have turned it to rally. That alone refused every slow grind buy.
- **EMA pullback:** it never got a buy setup to check. Its hourly-EMA test needs the 8, 13 and 20 EMAs rising and stacked up, and they are still stacked down.
- **Daily pivot:** it isn't what's stopping buys. It doesn't apply to the slow grind, and the EMA pullback never got far enough to be asked. Even so, price (high 13160.7) has stayed below the pivot, 13162.5.
