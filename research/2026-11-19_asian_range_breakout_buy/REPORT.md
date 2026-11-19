# The Asian range breakout buy: Thursday 19 November 2026, 07:35 UK

Read-only. Nothing was changed or restarted. Sources:
- `data/records/GBPUSD/trades.jsonl`
- `data/records/GBPUSD/decisions.jsonl`
- `data/orders/GBPUSD/orders.jsonl`
- `logs/prices.log` (19 Nov) and `logs/prices.log.1` (18 Nov)
- the stored 5-minute candles
- the code at main d9e5d0e

UK times; in November, UK time is GMT, which is the log's time. Sell prices, unless a buy price is named.

## 1. The trade record and the log lines when it fired

**It opened at 07:35:02 UK, not 07:40:**
- signal price 13155 (sell)
- IG fill 13156.5 (the offer)
- stop 13144.5 (12 pips)
- take profit 13256.5 (100 pips)

It closed at 09:27:19 at its stop, for −12.0 pips.

The opening trade record (`trades.jsonl`; steps quoted in full):
```
"event": "opened", "reference": "AB261119073504-1cd81a72", "deal_id": "DIAAAAYV6EGY8BF", "strategy": "Asian range breakout",
"direction": "buy", "market_state": "trend up, strong push", "opened_utc": "2026-11-19T07:35:02Z", "entry_price": "13155",
"open_price": "13156.5", "stop_pips": "12", "stop_price": "13144.5", "take_profit_pips": "100", "take_profit_price": "13256.5"
steps:
  Thu 19 Nov 07:30 GMT closed at 13155.7, above the Asian high (the Asian range 00:00 to 07:00, high 13153.3, low 13119.1)
  Thu 19 Nov 07:35 GMT opens at this candle's open, 13155 (sell price)
  allowed at entry: Asian range breakout in a trend up; direction rule no clear direction (price 13155 is below the pivot 13162.5 and above the 5m 100 EMA 13139.2: they disagree); the direction rule does not apply to Asian range breakout; hourly sell-off: the Thu 19 Nov 03:00 GMT hourly candle closed at 13125.2, 5.4 pips below the low 13130.6 of the 12 hourly candles before it; the hourly range 13119.1 to 13153.3
  reached on the live price at 07:35:02 UTC (bid 13155, offer 13156.5)
```
The closing record: `"closed_utc": "2026-11-19T09:27:19Z", "close_price": "13144.5", "how_closed": "stopped by IG", "close_reason": "the stop at IG (IG's level)", "pips": "-12.0", "best_pips": "4.2", "closed_by": "bot"`.

The decisions (`decisions.jsonl`):
```
{"time_utc": "2026-11-19T07:35:02Z", "kind": "idea", "strategy": "Asian range breakout", "direction": "buy", "entry_price": "13155", "allowed": true, "blocked_by": "", "state": "trend", "live": true}
{"time_utc": "2026-11-19T07:35:05Z", "kind": "order", "strategy": "Asian range breakout", "direction": "buy", "result": "opened", "reference": "AB261119073504-1cd81a72", ...}
```

The log (`logs/prices.log`):
```
2026-11-19 07:35:00 GMT INFO    autobot.prices: [GBPUSD] Stored 5m Thu 19 Nov 07:30 GMT: buy O 13153.9 H 13158 L 13153.9 C 13157.2 | sell O 13152.4 H 13156.5 L 13152.4 C 13155.7
2026-11-19 07:35:01 GMT INFO    autobot.analyser: [GBPUSD] Market state: Thu 19 Nov 07:30 GMT  trend (up, strong push): the rejection became a trend: a bounce failed under the 21 EMA and middle band, then a new high 13156.5 on the upper band 13154.3; EMAs 7/13/21 stacked up for 33 candles, close 13155.7 above them and the 100 EMA 13139.2; band sloping 2.0 pips/candle
2026-11-19 07:35:04 GMT INFO    autobot.orders: Order record: sending AB261119073504-1cd81a72
2026-11-19 07:35:05 GMT INFO    autobot.orders: Order record: opened AB261119073504-1cd81a72
2026-11-19 07:35:06 GMT INFO    autobot.trading: Live entry: Asian range breakout buy at 13156.5 (entry price 13155).
```

**How it went.** From the 5-minute candles (sell price, which is where a buy is closed and its stop hit):
- **07:40 candle:** fell to 13145.9, 10.6 pips below the fill.
- **09:00 candle:** rose to 13160.7, 4.2 pips above the fill (the record's `best_pips` is 4.2).
- **09:25 candle:** fell to 13143.0, through the stop at 13144.5. IG closed the trade at 09:27:19.

## 2. The Asian range it used

The range was 00:00 to 07:00 UK, sell prices, from `strategies/asian_range_breakout/strategy.py` `_take` (`self.high = ... max(self.high, c.sell_high)`, `self.low = ... min(self.low, c.sell_low)`):
- **High 13153.3:** from the 00:55 candle (`2026-11-19 00:55, sell O 13149.9 H 13153.3 L 13149.5 C 13151.6`).
- **Low 13119.1:** from the 03:10 candle (`2026-11-19 03:10, sell O 13124.9 H 13124.9 L 13119.1 C 13120.2`).

**The trigger.** The 07:30 candle closed at 13155.7, above 13153.3. The trade opened at the next candle's open, 07:35, at 13155 (the sell price) / 13156.5 (the buy price).

## 3. Analyser state, hourly read, and the rule that allowed it

**The analyser state was "trend up, strong push".** It was logged at 07:35:01, one second before the live entry (quoted in part 1). From 06:30 it had been an emerging trend up: `06:35:01 ... Market state: Thu 19 Nov 06:30 GMT  emerging trend (up): rejected at a level: closed 13140 above the reversal high 13139.9; trigger at above 13141.9`.

**The hourly read was "sell-off":** `hourly sell-off: the Thu 19 Nov 03:00 GMT hourly candle closed at 13125.2, 5.4 pips below the low 13130.6 of the 12 hourly candles before it`. That's the record's own step. The hourly read does not apply to the Asian range breakout: `TREND_STRATEGIES = (EMA_PULLBACK, SLOW_GRIND, BREAKOUT)` (`strategies/common.py`).

**The rule that allowed it: ANALYSER_GOVERNS_ALL's check 7.** The Asian range breakout's own rules (strategy file header) say: `Nothing else in the strategies decides whether it opens (strategies/common.py: like the bounce).` With ANALYSER_GOVERNS_ALL on, check 7 replaces the "without hindrance" exemption (`STATE_RULE_REPLACED = (LEVEL_REVERSAL,) + WITHOUT_HINDRANCE`). Check 7 puts it in the trend group "for direction only" (`strategies/common.py` `governs_reasons`):
```python
# the Asian range breakout: the trend group for direction only; ranging, consolidation and the hourly-ranging
# rule do not block it, breaking out of the quiet Asian range being its job (owner, 18 November 2026)
arb = strategy == ASIAN_RANGE_BREAKOUT
...
elif st in (EMERGING, TREND):
    if direction != want:
        out.append(f"ANALYSER_GOVERNS_ALL: the {st} is {d}: {strategy} only in the trend's direction")
```
The state was "trend up" and the trade was a buy, so check 7 had no objection.

## 4. Does the Asian range breakout check the direction rule (above the daily pivot = buy side)? No.

The direction rule doesn't apply to the session strategies, and the Asian range breakout is one of them. From `strategies/common.py`:
```python
SESSION_STRATEGIES = (ASIAN_RANGE_BREAKOUT, SESSION_SWEEP, NEW_YORK_OPEN_REVERSAL)
...
# The direction rule (section 2.3) does not apply to these (owner, 7 and 8 November 2026).
NO_DIRECTION_RULE = (RANGE_TRADE, BOLLINGER_BOUNCE, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL) + SESSION_STRATEGIES
...
    need = BUY_SIDE if direction == BUY else SELL_SIDE
    if rule.side != need and strategy not in NO_DIRECTION_RULE:
        reasons.append(f"the direction rule says {rule.side} ({rule.reason})")
```
The module's own description of check 3 says the same: `It does not apply to the session strategies (owner, 16 November 2026), ...`. Its answer is still worked out and recorded. Here it was `no clear direction (price 13155 is below the pivot 13162.5 and above the 5m 100 EMA 13139.2: they disagree)`.

So the buy opened 7.5 pips under the daily pivot (13162.5). Even if the direction rule did apply, it would have said "no clear direction" here, not "sell side": the price was below the pivot but above the 5-minute 100 EMA.

The strategy file itself has no mention of the pivot or the direction rule (`grep -n "pivot\|direction rule" strategies/asian_range_breakout/strategy.py` finds nothing).

## 5. Yesterday's morning Asian range breakout (Wed 18 November), for comparison

**The trade (`trades.jsonl`):**
```
"reference": "AB261118073003-e0728f6f", "strategy": "Asian range breakout", "direction": "sell", "market_state": "emerging trend up",
"opened_utc": "2026-11-18T07:30:02Z", "entry_price": "13179.8", "open_price": "13180.2", "stop_price": "13192.2", "take_profit_price": "13080.2"
"reason": "Asian range breakout: Wed 18 Nov 07:25 GMT closed at 13179.2, below the Asian low (the Asian range 00:00 to 07:00, high 13206.9, low 13186.8); Wed 18 Nov 07:30 GMT opens at this candle's open, 13179.8 (sell price)"
allowed at entry: Asian range breakout in a emerging trend up; direction rule sell side (price 13179.8 is below the pivot 13200.1 and below the 5m 100 EMA 13195.4); the direction rule does not apply to Asian range breakout; hourly ranging: 12 hourly candles have closed with no new break since the Tue 17 Nov 17:00 GMT candle; the hourly range 13186.8 to 13219.6
"closed_utc": "2026-11-18T09:25:12Z", "close_price": "13158.5", "how_closed": "stopped by IG", "close_reason": "the stop at IG (trailed to 13158.5)", "pips": "21.7", "best_pips": "30.7"
```

**The log:**
```
2026-11-18 07:30:00 GMT INFO    autobot.prices: [GBPUSD] Stored 5m Wed 18 Nov 07:25 GMT: buy O 13180.2 H 13180.8 L 13177.1 C 13180.7 | sell O 13178.7 H 13179.3 L 13175.6 C 13179.2
2026-11-18 07:30:03 GMT INFO    autobot.orders: Order record: sending AB261118073003-e0728f6f
2026-11-18 07:30:03 GMT INFO    autobot.orders: Order record: opened AB261118073003-e0728f6f
2026-11-18 07:30:04 GMT INFO    autobot.trading: Live entry: Asian range breakout sell at 13180.2 (entry price 13179.8).
```

**Its Asian range:**
- high 13206.9, from the 02:25 candle (`sell H 13206.9`);
- low 13186.8, from the 06:40 candle (`sell L 13186.8`).

**Earlier ideas were refused for the UK inflation news.** The first closes below the low, at 07:15 and 07:20, gave ideas that the safety rules refused:
```
{"time_utc": "2026-11-18T07:20:02Z", "kind": "order", "strategy": "Asian range breakout", "direction": "sell", "result": "safety refused", "reasons": ["in a big-news window: Core Inflation Rate MoM, Inflation Rate YoY"]}
{"time_utc": "2026-11-18T07:25:02Z", "kind": "order", "strategy": "Asian range breakout", "direction": "sell", "result": "safety refused", "reasons": ["in a big-news window: Core Inflation Rate MoM, Inflation Rate YoY"]}
```

**The state and hourly read at entry:**
- **Analyser state: "emerging trend up"**, against the sell.
- **Hourly read: ranging** (13186.8 to 13219.6).
- **Old rules:** this was before the 13:35 change, so ANALYSER_GOVERNS_ALL was off. The Asian range breakout opened "without hindrance" (`WITHOUT_HINDRANCE = (BOLLINGER_BOUNCE,) + SESSION_STRATEGIES`) and wasn't checked against the state.

**The direction rule was not checked yesterday either** ("the direction rule does not apply to Asian range breakout"). It happened to agree with the trade: `sell side (price 13179.8 is below the pivot 13200.1 and below the 5m 100 EMA 13195.4)`.

**How it went:**
- The highest sell price from 07:30 to 09:25 was 13181.6, in the 07:30 opening candle itself. From the 07:35 candle on, the sell price stayed below the entry.
- At best it was 30.7 pips in profit (low 13148.0 in the 09:05 candle).
- Its stop was trailed, and it closed at 13158.5 for +21.7.

## Side by side

| | Wed 18 Nov | Thu 19 Nov |
|---|---|---|
| Direction | sell | buy |
| Asian range | 13186.8 (06:40) to 13206.9 (02:25) | 13119.1 (03:10) to 13153.3 (00:55) |
| Break | 07:25 close 13179.2, below the low; the 07:15 and 07:20 ideas were refused (news window) | 07:30 close 13155.7, above the high |
| Open | 07:30:02, 13179.8 / fill 13180.2 | 07:35:02, 13155 / fill 13156.5 |
| Daily pivot | 13200.1: the trade was 20.3 below it, on the sell side | 13162.5: the trade was 7.5 below it |
| Direction rule (recorded, not applied) | sell side | no clear direction |
| Analyser state | emerging trend up (against the trade) | trend up, strong push (with the trade) |
| Rules in force | old: not checked against the state | new: check 7, buy in a trend up |
| Hourly read (not applied to this strategy) | ranging 13186.8–13219.6 | sell-off since the 03:00 hourly close |
| Result | +21.7 (best 30.7), trailed stop | −12.0 (best 4.2), stop |
