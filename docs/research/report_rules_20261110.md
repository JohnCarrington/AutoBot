# The rules from the live investigation, replayed: 25 October to 10 November 2026

Read-only replay of all six strategies on the stored GBPUSD candles (IG's prices), through the bot's own code, from Sunday 25 October 21:00 UK to the latest stored candle, Tuesday 10 November 14:40 UTC. It compares the current rules with five rules taken from `live_investigation_20261110.md`, used together, and then, with those rules, the stop for the bounce, range trade and breakout at 6, 8, 10 and 12 pips, and an exhaustion-at-a-level check off, closing the trade, or moving its stop. **Nothing in the bot was changed.** Written Tuesday 10 November 2026.

## Summary

- **The five rules together lose almost all of the replay's profit.** The current rules make **+1071.0 pips** in 176 trades from 25 October to Tuesday 10 November 14:40 UTC. The five rules together make +65.0 in 69 trades. With them, the best of the twelve stop and exhaustion versions is **stop 12 for the bounce, range trade and breakout, with exhaustion moving the stop to the last swing: +110.6 pips** in 65 trades, 960.4 fewer than now. Every one of the twelve is between +27.9 and +110.6.
- **What it changes:** a smaller biggest loss when exhaustion closes the trade (-15.0 against -17.4 now), and a shorter worst losing run (9 against 14). But every week is worse, the week of 9 November included (-10.4 against +14.9).
- **Two rules do most of the damage:**
  - **Rule 1, 8 pips of room to a strong level**, on its own: +444.5. Strong levels are close together (round numbers every 50 pips, the pivots, R1 to R3, S1 to S3, the previous day's high and low, and lined-up turning levels). Under the current rules, the 90 trades with less than 8 pips of room made +630.3 pips, more than the 86 trades with 8 or more (+440.7).
  - **Rule 2, one trade per direction per strategy**, on its own: +547.9. It mostly stops the EMA pullback holding several trades at once, and those stacked trades made the big days: 13 EMA pullbacks on Friday 6 November made +566.4.
  - Together, these two leave +84.1.
- **Rule 3, protection once 10 pips up**, on its own costs 157.9 pips (+913.1). Trades moved to break-even came back to their entry before going on to the take profit, mostly in the week of 26 October.
- **Rules 4 and 5 help on their own:**
  - The bounce only in the first hour of the state: +1108.3 (+37.3).
  - The level reversal only from 07:00 to 12:00 UK: +1116.4 (+45.4).
  - The two together: **+1153.7 (+82.7)**, the best of the 32 combinations of the five rules, with a smaller biggest loss (-15.0). But the week of 9 November drops from +14.9 to -8.0.
- **The stop and exhaustion with the current rules** (none of the five rules), for comparison:
  - A 12-pip stop for the bounce, range trade and breakout makes **+1214.5** (+143.5), with fewer losses (82 against 96), a worst run of 12, and the week of 9 November at +86.4.
  - A 10-pip stop: +1181.0.
  - Exhaustion closing the trade costs 192 to 267 pips at each stop. Moving the stop to the last swing costs 34 to 103.
- **Monday 9 and Tuesday 10 November in the replay:**
  - The current rules make +23.9 on Monday (13 trades) and -9.0 on Tuesday (11 trades). The best five-rule version makes -4.7 (8 trades) and -5.7 (3 trades).
  - On Monday, rule 1 refused three winners: the 05:25 slow grind (+20.0), the 07:55 breakout (+50.0) and, on Tuesday, the 13:30 slow grind (+32.3). On Tuesday it also refused the two bounces stopped at -6 and the bounce that made +21.8.
  - Live at IG these two days made -62.9; the gap from the replay is ticks against candles, fills, and IG's own closes on Monday (see `live_investigation_20261110.md`).
- **How sure this is:** two weeks and two days, carried by one strong Friday. These are indications, not proof.

## Method

- **The bot's own code.** The trade ideas come from the strategies' replay (`strategies/replay.py`, all six switched on, as in `.env`). Each idea goes through the safety rules' `decide()` (`safety/rules.py`, with the day's directions from `analyser/day_direction.py`, as the live engine passes them: hours, news, Friday rules, limits, total risk, funds, no reversal against a strong push or the day's direction). Each trade is then run by the trade manager's `plan()` and `step()` (`trade_manager/manager.py`). Bands, rejections at levels and the analyser's states come from the analyser (`StateTracker`) replayed week by week, as `trading/engine.py` uses them. The rules under test are added on top, in a scratchpad script only.
- **Checked against the full wired path.** With the current rules, the first two weeks give exactly +280.6 and +775.5 pips, the same as `trading/engine.py` run candle by candle (`trading/replay_check.py`'s `wired_trades`, in `live_investigation_20261110.md`).
- **The live week is not the live result.** For the week of 9 November the replay gives what the bot's code does on 5-minute candles. Live, the bot works on ticks, three trades were closed by IG's own system on Monday, and fills differ. Live at IG, Monday made -25.7 pips and Tuesday -37.2 (20 trades); the replay's current rules give the figures below.
- **Trades still open at the last candle** are counted at its close price. Every trade is £10 a pip, so pips are shown. Pips per week are by entry time.

### How each rule was put into the replay

1. **Room to a strong level.** An idea is refused if the nearest strong level in its way (above a buy's entry price, below a sell's) is less than 8 pips away. Strong levels are the analyser's: `market_states.strong_level_types` (pivot, R1 to R3, S1 to S3, round numbers every 50 pips, the previous day's high and low), or a turning level in a lined-up group that holds one of those. They are taken from the level list the analyser built at the start of the entry candle. No strong level that way: allowed.
2. **One trade per direction per strategy; identical setups once.** An idea is refused while the same strategy already has a trade open in the same direction (this mainly limits the EMA pullback, which today may hold several; the other strategies keep their current, stricter limits). And a setup already taken is not taken again: the same strategy, direction and entry price on the same UK day.
3. **Protection once 10 pips up.** At the close of each candle: once the trade has been 10 pips or more up (the trade manager's own best), the first strong push in its favour (the analyser's state after that candle: a trend of the strong-push type in its direction) or MACD histogram cross in its favour (through zero, on that candle) switches off its close on a rejection at a level and moves its stop to break-even (a stop already at or past break-even, such as the slow grind's lock, is not loosened).
4. **The bounce only within the first hour of the analyser's state**: refused if more than 60 minutes have passed since the end of the candle the current state was decided on.
5. **The level reversal only from 07:00 to 12:00 UK** (entry time from 07:00 up to 11:59).

### The stop and exhaustion

- **Stop**: the bounce, range trade and breakout use 6 pips today. Each version gives all three the same stop: 6, 8, 10 or 12 pips (for the safety rules' total risk as well). The other strategies keep theirs (EMA pullback 12, slow grind 15, level reversal beyond the furthest point).
- **Exhaustion at a level**, checked at the close of each candle for every trade open before that candle, all three together:
  - 2 of the last 3 candles have a wick against the trade (the upper wick for a buy, the lower for a sell) at least twice the body (sell prices);
  - a strong level ahead (at or above the close for a buy, at or below for a sell) within 5 pips of the close;
  - RSI(3) failing a new extreme: the last 3 candles made a new high (buy) or low (sell) against the 9 candles before them, but RSI(3) on the candle that made it did not pass its own highest (lowest) of those 9.
- **What it does:** off; close the trade at that candle's close; or move the stop to just beyond the last small swing: 1 pip past the latest candle low (buy, sell price) or high (sell, buy price) that is beyond the candles either side of it, only if that is tighter than the stop it has and not already past the price.

## Results

### The current rules, each rule on its own, and the rules together

| Version | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 26 Oct | Week 2 Nov | Week 9 Nov (to Tue 14:45) |
|---|---|---|---|---|---|---|---|---|---|
| **Current rules** | 176 | 79 | 96 | **+1071.0** | -17.4 | 14 | +280.6 | +775.5 | +14.9 |
| Only rule 1: 8 pips of room to a strong level | 99 | 40 | 58 | **+444.5** | -22.6 | 11 | +76.8 | +384.5 | -16.8 |
| Only rule 2: one per direction per strategy, identical setups once | 134 | 60 | 73 | **+547.9** | -17.4 | 11 | +244.6 | +252.4 | +50.9 |
| Only rule 3: protection once 10 up | 177 | 71 | 92 | **+913.1** | -17.4 | 14 | +159.0 | +726.4 | +27.7 |
| Only rule 4: bounce in the first hour of the state | 168 | 78 | 89 | **+1108.3** | -17.4 | 14 | +299.9 | +793.5 | +14.9 |
| Only rule 5: level reversal 07:00 to 12:00 UK | 162 | 74 | 87 | **+1116.4** | -15.0 | 17 | +345.3 | +779.1 | -8.0 |
| **The five rules together** (stop 6, exhaustion off) | 69 | 24 | 40 | **+65.0** | -22.6 | 9 | +57.1 | +32.7 | -24.8 |

### With the five rules: the stop and exhaustion

| Version | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 26 Oct | Week 2 Nov | Week 9 Nov (to Tue 14:45) |
|---|---|---|---|---|---|---|---|---|---|
| **Current rules** | 176 | 79 | 96 | **+1071.0** | -17.4 | 14 | +280.6 | +775.5 | +14.9 |
| Five rules, stop 6, exhaustion off | 69 | 24 | 40 | **+65.0** | -22.6 | 9 | +57.1 | +32.7 | -24.8 |
| Five rules, stop 6, exhaustion: close | 69 | 26 | 39 | **+96.6** | -15.0 | 9 | +51.7 | +57.6 | -12.7 |
| Five rules, stop 6, exhaustion: stop to the last swing | 69 | 26 | 39 | **+93.9** | -17.6 | 9 | +62.1 | +52.5 | -20.7 |
| Five rules, stop 8, exhaustion off | 69 | 24 | 40 | **+27.9** | -22.6 | 9 | +53.1 | +9.6 | -34.8 |
| Five rules, stop 8, exhaustion: close | 69 | 27 | 38 | **+80.6** | -15.0 | 9 | +47.7 | +55.6 | -22.7 |
| Five rules, stop 8, exhaustion: stop to the last swing | 69 | 27 | 38 | **+69.5** | -17.6 | 9 | +58.1 | +42.1 | -30.7 |
| Five rules, stop 10, exhaustion off | 67 | 25 | 36 | **+58.0** | -22.6 | 9 | +50.2 | +32.6 | -24.8 |
| Five rules, stop 10, exhaustion: close | 67 | 28 | 34 | **+95.7** | -15.0 | 9 | +44.8 | +63.6 | -12.7 |
| Five rules, stop 10, exhaustion: stop to the last swing | 67 | 28 | 34 | **+107.0** | -17.6 | 9 | +55.2 | +72.5 | -20.7 |
| Five rules, stop 12, exhaustion off | 65 | 26 | 33 | **+76.3** | -22.6 | 9 | +65.2 | +25.6 | -14.5 |
| Five rules, stop 12, exhaustion: close | 65 | 28 | 32 | **+94.2** | -15.0 | 9 | +59.8 | +36.8 | -2.4 |
| **Five rules, stop 12, exhaustion: stop to the last swing** (best) | 65 | 28 | 32 | **+110.6** | -17.6 | 9 | +70.2 | +50.8 | -10.4 |

The best of these is **the five rules, stop 12, exhaustion moving the stop to the last swing**: +110.6 pips, against +1071.0 with the current rules (-960.4).

### What the rules refused, and what the trade-management rules did (each version)

| Version | Refused by rule 1 (room) | Rule 2 (one per direction) | Rule 2 (identical setup) | Rule 4 (bounce hour) | Rule 5 (level reversal hours) | Protected (rule 3) | Exhaustion: closed | Exhaustion: stop moved |
|---|---|---|---|---|---|---|---|---|
| current rules | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Only rule 1: 8 pips of room to a strong level | 354 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Only rule 2: one per direction per strategy, identical setups once | 0 | 258 | 1 | 0 | 0 | 0 | 0 | 0 |
| Only rule 3: protection once 10 up | 0 | 0 | 0 | 0 | 0 | 42 | 0 | 0 |
| Only rule 4: bounce in the first hour of the state | 0 | 0 | 0 | 82 | 0 | 0 | 0 | 0 |
| Only rule 5: level reversal 07:00 to 12:00 UK | 0 | 0 | 0 | 0 | 90 | 0 | 0 | 0 |
| rules, stop 6, exhaustion off | 223 | 69 | 0 | 82 | 90 | 13 | 0 | 0 |
| rules, stop 6, exhaustion close | 223 | 69 | 0 | 82 | 90 | 11 | 5 | 0 |
| rules, stop 6, exhaustion swing | 223 | 69 | 0 | 82 | 90 | 12 | 0 | 6 |
| rules, stop 8, exhaustion off | 223 | 69 | 0 | 82 | 90 | 13 | 0 | 0 |
| rules, stop 8, exhaustion close | 223 | 69 | 0 | 82 | 90 | 11 | 7 | 0 |
| rules, stop 8, exhaustion swing | 223 | 69 | 0 | 82 | 90 | 12 | 0 | 7 |
| rules, stop 10, exhaustion off | 223 | 71 | 0 | 82 | 90 | 15 | 0 | 0 |
| rules, stop 10, exhaustion close | 223 | 71 | 0 | 82 | 90 | 12 | 7 | 0 |
| rules, stop 10, exhaustion swing | 223 | 71 | 0 | 82 | 90 | 14 | 0 | 10 |
| rules, stop 12, exhaustion off | 223 | 72 | 0 | 82 | 90 | 15 | 0 | 0 |
| rules, stop 12, exhaustion close | 223 | 72 | 0 | 82 | 90 | 12 | 6 | 0 |
| rules, stop 12, exhaustion swing | 223 | 72 | 0 | 82 | 90 | 14 | 0 | 9 |

Refusals are counted per idea; the strategies give the same idea again on later candles while their setup lasts, so one refused setup can count more than once. A refused idea can also free a limit for a later one.

### By strategy

| Strategy | Current: trades | Current: pips | Five rules (stop 6, exhaustion off): trades | pips | Best (stop 12, exhaustion swing): trades | pips |
|---|---|---|---|---|---|---|
| EMA pullback | 65 | +614.4 | 18 | +4.0 | 18 | +4.0 |
| slow grind | 23 | +238.1 | 13 | -0.9 | 13 | +18.9 |
| breakout | 15 | +84.4 | 8 | -45.4 | 6 | -43.9 |
| level reversal | 23 | +99.1 | 7 | +63.2 | 7 | +68.2 |
| Bollinger bounce | 40 | +29.9 | 16 | +48.2 | 15 | +72.2 |
| range trade | 10 | +5.1 | 7 | -4.1 | 6 | -8.8 |

### By strategy and week, current rules against the best version

| Strategy | Week | Current: trades | Current: pips | Best: trades | Best: pips |
|---|---|---|---|---|---|
| EMA pullback | 26 Oct | 17 | +90.0 | 4 | +6.0 |
| EMA pullback | 2 Nov | 42 | +596.4 | 12 | +22.0 |
| EMA pullback | 9 Nov | 6 | -72.0 | 2 | -24.0 |
| slow grind | 26 Oct | 10 | +115.0 | 4 | +5.0 |
| slow grind | 2 Nov | 8 | +102.9 | 5 | +4.7 |
| slow grind | 9 Nov | 5 | +20.2 | 4 | +9.2 |
| breakout | 26 Oct | 2 | +44.0 | 0 | +0.0 |
| breakout | 2 Nov | 9 | +8.4 | 4 | -48.0 |
| breakout | 9 Nov | 4 | +32.0 | 2 | +4.1 |
| level reversal | 26 Oct | 10 | -24.7 | 1 | -17.6 |
| level reversal | 2 Nov | 10 | +80.9 | 5 | +65.8 |
| level reversal | 9 Nov | 3 | +42.9 | 1 | +20.0 |
| Bollinger bounce | 26 Oct | 24 | +50.4 | 8 | +72.9 |
| Bollinger bounce | 2 Nov | 13 | -30.3 | 7 | -0.7 |
| Bollinger bounce | 9 Nov | 3 | +9.8 | 0 | +0.0 |
| range trade | 26 Oct | 2 | +5.9 | 1 | +3.9 |
| range trade | 2 Nov | 5 | +17.2 | 3 | +7.0 |
| range trade | 9 Nov | 3 | -18.0 | 2 | -19.7 |

### More combinations, for comparison

Each of the 32 combinations of the five rules (stop 6, exhaustion off), by total pips. "x" means the rule is on.

| # | 1 room | 2 one per direction | 3 protection | 4 bounce hour | 5 level reversal hours | Trades | Won | Lost | Total pips | Biggest loss | Worst run | Week 26 Oct | Week 2 Nov | Week 9 Nov |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 |  |  |  | x | x | 154 | 73 | 80 | +1153.7 | -15.0 | 14 | +364.6 | +797.1 | -8.0 |
| 2 |  |  |  |  | x | 162 | 74 | 87 | +1116.4 | -15.0 | 17 | +345.3 | +779.1 | -8.0 |
| 3 |  |  |  | x |  | 168 | 78 | 89 | +1108.3 | -17.4 | 14 | +299.9 | +793.5 | +14.9 |
| 4 |  |  |  |  |  | 176 | 79 | 96 | +1071.0 | -17.4 | 14 | +280.6 | +775.5 | +14.9 |
| 5 |  |  | x | x | x | 154 | 64 | 77 | +986.5 | -15.0 | 14 | +237.0 | +744.7 | +4.8 |
| 6 |  |  | x |  | x | 162 | 65 | 83 | +955.2 | -15.0 | 17 | +223.7 | +726.7 | +4.8 |
| 7 |  |  | x | x |  | 169 | 70 | 86 | +944.4 | -17.4 | 14 | +172.3 | +744.4 | +27.7 |
| 8 |  |  | x |  |  | 177 | 71 | 92 | +913.1 | -17.4 | 14 | +159.0 | +726.4 | +27.7 |
| 9 |  | x |  | x | x | 113 | 54 | 58 | +624.6 | -15.0 | 11 | +328.6 | +268.0 | +28.0 |
| 10 |  | x | x | x | x | 114 | 51 | 57 | +601.7 | -15.0 | 11 | +291.0 | +269.9 | +40.8 |
| 11 |  | x |  |  | x | 120 | 55 | 64 | +593.3 | -15.0 | 13 | +309.3 | +256.0 | +28.0 |
| 12 |  | x |  | x |  | 127 | 59 | 67 | +579.2 | -17.4 | 11 | +263.9 | +264.4 | +50.9 |
| 13 |  | x | x |  | x | 121 | 52 | 62 | +576.4 | -15.0 | 13 | +277.7 | +257.9 | +40.8 |
| 14 |  | x | x | x |  | 129 | 57 | 66 | +559.6 | -17.4 | 11 | +226.3 | +269.6 | +63.7 |
| 15 |  | x |  |  |  | 134 | 60 | 73 | +547.9 | -17.4 | 11 | +244.6 | +252.4 | +50.9 |
| 16 |  | x | x |  |  | 136 | 58 | 71 | +534.3 | -17.4 | 11 | +213.0 | +257.6 | +63.7 |
| 17 | x |  |  | x |  | 96 | 40 | 55 | +462.5 | -22.6 | 11 | +88.8 | +390.5 | -16.8 |
| 18 | x |  |  |  |  | 99 | 40 | 58 | +444.5 | -22.6 | 11 | +76.8 | +384.5 | -16.8 |
| 19 | x |  |  | x | x | 90 | 36 | 53 | +427.6 | -22.6 | 11 | +97.1 | +367.3 | -36.8 |
| 20 | x |  |  |  | x | 93 | 36 | 56 | +409.6 | -22.6 | 11 | +85.1 | +361.3 | -36.8 |
| 21 | x |  | x | x |  | 97 | 35 | 52 | +364.0 | -22.6 | 11 | +42.8 | +338.0 | -16.8 |
| 22 | x |  | x |  |  | 100 | 35 | 54 | +352.0 | -22.6 | 11 | +36.8 | +332.0 | -16.8 |
| 23 | x |  | x | x | x | 91 | 31 | 50 | +329.1 | -22.6 | 11 | +51.1 | +314.8 | -36.8 |
| 24 | x |  | x |  | x | 94 | 31 | 52 | +317.1 | -22.6 | 11 | +45.1 | +308.8 | -36.8 |
| 25 | x | x |  | x |  | 74 | 29 | 44 | +102.1 | -22.6 | 9 | +64.8 | +42.1 | -4.8 |
| 26 | x | x | x | x |  | 75 | 28 | 42 | +99.9 | -22.6 | 9 | +48.8 | +55.9 | -4.8 |
| 27 | x | x | x |  |  | 78 | 28 | 44 | +87.9 | -22.6 | 9 | +42.8 | +49.9 | -4.8 |
| 28 | x | x |  |  |  | 77 | 29 | 47 | +84.1 | -22.6 | 9 | +52.8 | +36.1 | -4.8 |
| 29 | x | x |  | x | x | 68 | 25 | 42 | +67.2 | -22.6 | 9 | +73.1 | +18.9 | -24.8 |
| 30 | x | x | x | x | x | 69 | 24 | 40 | +65.0 | -22.6 | 9 | +57.1 | +32.7 | -24.8 |
| 31 | x | x | x |  | x | 72 | 24 | 42 | +53.0 | -22.6 | 9 | +51.1 | +26.7 | -24.8 |
| 32 | x | x |  |  | x | 71 | 25 | 45 | +49.2 | -22.6 | 9 | +61.1 | +12.9 | -24.8 |

The stop and exhaustion options with the current rules (none of the five rules):

| Version | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 26 Oct | Week 2 Nov | Week 9 Nov (to Tue 14:45) |
|---|---|---|---|---|---|---|---|---|---|
| Current rules, stop 6, exhaustion off | 176 | 79 | 96 | **+1071.0** | -17.4 | 14 | +280.6 | +775.5 | +14.9 |
| Current rules, stop 6, exhaustion close | 181 | 80 | 100 | **+856.3** | -17.4 | 14 | +77.6 | +743.2 | +35.5 |
| Current rules, stop 6, exhaustion stop to the last swing | 178 | 80 | 97 | **+1022.6** | -17.4 | 14 | +215.7 | +787.4 | +19.5 |
| Current rules, stop 8, exhaustion off | 174 | 80 | 93 | **+1055.2** | -17.4 | 13 | +272.8 | +775.5 | +6.9 |
| Current rules, stop 8, exhaustion close | 179 | 82 | 96 | **+863.6** | -17.4 | 13 | +71.8 | +764.3 | +27.5 |
| Current rules, stop 8, exhaustion stop to the last swing | 176 | 82 | 93 | **+1021.5** | -17.4 | 13 | +209.9 | +800.1 | +11.5 |
| Current rules, stop 10, exhaustion off | 169 | 81 | 87 | **+1181.0** | -17.4 | 13 | +327.4 | +777.5 | +76.1 |
| Current rules, stop 10, exhaustion close | 175 | 83 | 91 | **+931.9** | -17.4 | 13 | +68.4 | +766.8 | +96.7 |
| Current rules, stop 10, exhaustion stop to the last swing | 171 | 82 | 88 | **+1091.3** | -17.4 | 13 | +206.5 | +804.1 | +80.7 |
| Current rules, stop 12, exhaustion off | 166 | 83 | 82 | **+1214.5** | -17.4 | 12 | +336.4 | +791.7 | +86.4 |
| Current rules, stop 12, exhaustion close | 172 | 84 | 87 | **+947.6** | -17.4 | 12 | +77.4 | +763.2 | +107.0 |
| Current rules, stop 12, exhaustion stop to the last swing | 168 | 83 | 84 | **+1111.2** | -17.4 | 12 | +215.5 | +804.7 | +91.0 |

## Monday 9 and Tuesday 10 November, trade by trade: the best version against the current rules

The best version is the five rules, stop 12, exhaustion swing. "Both" means the same trade (strategy, direction, entry candle) was taken in both. Live at IG on these days: 20 trades, -62.9 pips (Monday -25.7, Tuesday -37.2).

### Monday 9 November

| Entry (UK) | Strategy | Dir | In | Current: closed | Current: pips | Best: closed | Best: pips |
|---|---|---|---|---|---|---|---|
| Mon 09 Nov 05:25 | slow grind | buy | current only | Mon 09 Nov 08:10: take profit hit at IG, the take profit at IG (20 pips) | +20.0 | - | - |
| Mon 09 Nov 05:40 | slow grind | buy | best only | - | - | Mon 09 Nov 08:10: take profit hit at IG, the take profit at IG (20 pips) | +20.0 |
| Mon 09 Nov 06:10 | level reversal | buy | current only | Mon 09 Nov 08:15: take profit hit at IG, the take profit at IG (20 pips) | +20.0 | - | - |
| Mon 09 Nov 07:55 | breakout | buy | current only | Mon 09 Nov 21:00: take profit hit at IG, the take profit at IG (50 pips) | +50.0 | - | - |
| Mon 09 Nov 08:25 | level reversal | buy | both | Mon 09 Nov 19:35: take profit hit at IG, the take profit at IG (20 pips) | +20.0 | Mon 09 Nov 19:35: take profit hit at IG, the take profit at IG (20 pips) | +20.0 |
| Mon 09 Nov 09:35 | slow grind | buy | both | Mon 09 Nov 15:25: stopped by IG, the stop at IG | -15.0 | Mon 09 Nov 15:25: stopped by IG, the stop at IG | -15.0 |
| Mon 09 Nov 10:30 | EMA pullback | buy | both | Mon 09 Nov 12:00: stopped by IG, the stop at IG | -12.0 | Mon 09 Nov 12:00: stopped by IG, the stop at IG | -12.0 |
| Mon 09 Nov 13:55 | range trade | buy | both | Mon 09 Nov 14:40: stopped by IG, the stop at IG | -6.0 | Mon 09 Nov 14:45: close, a confirmed rejection at a level: new_york_session_high 13421.2 | -7.7 |
| Mon 09 Nov 14:55 | range trade | buy | both | Mon 09 Nov 15:00: stopped by IG, the stop at IG | -6.0 | Mon 09 Nov 15:20: stopped by IG, the stop at IG | -12.0 |
| Mon 09 Nov 15:15 | range trade | buy | current only | Mon 09 Nov 15:20: stopped by IG, the stop at IG | -6.0 | - | - |
| Mon 09 Nov 15:45 | slow grind | sell | current only | Mon 09 Nov 16:15: stopped by IG, the stop at IG | -15.0 | - | - |
| Mon 09 Nov 19:35 | breakout | buy | best only | - | - | Mon 09 Nov 22:00: stopped by IG, the stop at IG | +4.1 |
| Mon 09 Nov 19:55 | slow grind | buy | both | Mon 09 Nov 20:30: forced close, 20:30 UK close | -2.1 | Mon 09 Nov 20:30: forced close, 20:30 UK close | -2.1 |
| Mon 09 Nov 21:00 | EMA pullback | buy | current only | Mon 09 Nov 22:00: stopped by IG, the stop at IG | -12.0 | - | - |
| **Total** | | | | 13 trades | **+23.9** | 8 trades | **-4.7** |

Why the current rules' trades that the best version did not take were left out (checked against the five rules at that idea):

- Mon 09 Nov 05:25 slow grind buy (+20.0): rule 1: 0.7 pips to a strong level in its way
- Mon 09 Nov 06:10 level reversal buy (+20.0): rule 5: outside 07:00 to 12:00 UK
- Mon 09 Nov 07:55 breakout buy (+50.0): rule 1: 5.8 pips to a strong level in its way
- Mon 09 Nov 15:15 range trade buy (-6.0): no rule refuses it on its own: a trade the best version still held (a strategy's limit or rule 2) or a different earlier trade changed what was open
- Mon 09 Nov 15:45 slow grind sell (-15.0): rule 1: 1.4 pips to a strong level in its way
- Mon 09 Nov 21:00 EMA pullback buy (-12.0): rule 1: 4.5 pips to a strong level in its way; possibly rule 2 (an EMA pullback the same way already open)

### Tuesday 10 November

| Entry (UK) | Strategy | Dir | In | Current: closed | Current: pips | Best: closed | Best: pips |
|---|---|---|---|---|---|---|---|
| Tue 10 Nov 05:00 | EMA pullback | buy | current only | Tue 10 Nov 09:00: stopped by IG, the stop at IG | -12.0 | - | - |
| Tue 10 Nov 06:10 | EMA pullback | buy | both | Tue 10 Nov 09:00: stopped by IG, the stop at IG | -12.0 | Tue 10 Nov 09:00: stopped by IG, the stop at IG | -12.0 |
| Tue 10 Nov 07:20 | EMA pullback | buy | current only | Tue 10 Nov 09:00: stopped by IG, the stop at IG | -12.0 | - | - |
| Tue 10 Nov 07:55 | Bollinger bounce | sell | current only | Tue 10 Nov 08:00: stopped by IG, the stop at IG | -6.0 | - | - |
| Tue 10 Nov 08:20 | Bollinger bounce | sell | current only | Tue 10 Nov 08:25: stopped by IG, the stop at IG | -6.0 | - | - |
| Tue 10 Nov 08:45 | Bollinger bounce | sell | current only | Tue 10 Nov 10:40: close, a confirmed rejection at a level: london_session_low 13422 | +21.8 | - | - |
| Tue 10 Nov 09:10 | breakout | sell | both | Tue 10 Nov 09:20: stopped by IG, the stop at IG | -6.0 | Tue 10 Nov 13:30: stopped by IG, the stop at IG | +0.0 |
| Tue 10 Nov 11:50 | breakout | sell | current only | Tue 10 Nov 12:00: stopped by IG, the stop at IG | -6.0 | - | - |
| Tue 10 Nov 13:10 | breakout | sell | current only | Tue 10 Nov 13:25: stopped by IG, the stop at IG | -6.0 | - | - |
| Tue 10 Nov 13:30 | slow grind | sell | current only | Tue 10 Nov 14:40: close, open at the end of the data | +32.3 | - | - |
| Tue 10 Nov 13:55 | slow grind | sell | best only | - | - | Tue 10 Nov 14:40: close, open at the end of the data | +6.3 |
| Tue 10 Nov 14:05 | level reversal | sell | current only | Tue 10 Nov 14:40: close, open at the end of the data | +2.9 | - | - |
| **Total** | | | | 11 trades | **-9.0** | 3 trades | **-5.7** |

Why the current rules' trades that the best version did not take were left out (checked against the five rules at that idea):

- Tue 10 Nov 05:00 EMA pullback buy (-12.0): rule 1: 0.8 pips to a strong level in its way; possibly rule 2 (an EMA pullback the same way already open)
- Tue 10 Nov 07:20 EMA pullback buy (-12.0): possibly rule 2 (an EMA pullback the same way already open)
- Tue 10 Nov 07:55 Bollinger bounce sell (-6.0): rule 1: 0.3 pips to a strong level in its way
- Tue 10 Nov 08:20 Bollinger bounce sell (-6.0): rule 1: 1.2 pips to a strong level in its way
- Tue 10 Nov 08:45 Bollinger bounce sell (+21.8): rule 1: 3.7 pips to a strong level in its way
- Tue 10 Nov 11:50 breakout sell (-6.0): no rule refuses it on its own: a trade the best version still held (a strategy's limit or rule 2) or a different earlier trade changed what was open
- Tue 10 Nov 13:10 breakout sell (-6.0): rule 1: 6.4 pips to a strong level in its way
- Tue 10 Nov 13:30 slow grind sell (+32.3): rule 1: 4.7 pips to a strong level in its way
- Tue 10 Nov 14:05 level reversal sell (+2.9): rule 1: 4.7 pips to a strong level in its way; rule 5: outside 07:00 to 12:00 UK

