# Slow grind variations, 25 October to 6 November 2026

Read-only research on the stored GBPUSD candles (Sunday 25 October 21:00 UK to Friday 6 November close). Nothing in
the bot was changed (the slow grind is switched off). Written 7 November 2026.

## Method

- **Entries.** For each entry mechanism, every slow grind entry in both weeks, both directions, at any time, from the
  stored 5-minute candles (sell prices) and the strategy's 21 EMA. The current mechanism (a pause of 3, entry below the
  pause's lowest point) was checked against the bot's own slow grind code: the same 124 entries.
  - **Pause of N** (2, 3, 4, 5): N candles in a row that fail to make a new low (high) while closing below (above) the
    21 EMA, as now (design 3.1 and the choices in `strategies/slow_grind/strategy.py`). Entry below the pause's lowest
    point (as now) or below the low made just before the pause.
  - **The owner's alternative, N lower lows** (3, 4, 5, 6): N candles in a row each making a lower low (higher high)
    while closing below (above) the 21 EMA; the sell (buy) opens when the next candle makes a lower low (higher high),
    at the previous candle's low. Choices: the entry must come on the very next candle (otherwise the run starts
    again), and the count starts again after an entry.
- **Market conditions at entry.** The analyser's state after the last finished candle (the week replayed from its
  open), always in the trend's direction (as the slow grind's rule now). "Trend and emerging trend when the type is
  slow grind": emerging trends have no type, so this means an emerging trend, or a trend of type slow grind. Direction
  filters at the entry price: the direction rule (the pivot and the 5-minute 100 EMA); the day's 00:00 UK open; the
  previous day's close; the daily 20 EMA (last finished daily candle). An EMA pullback trade "open" means one of its
  trades under its current rules (59 trades) was open in the same direction at the moment of entry.
- **Never opened:** in the first 15 minutes after the Sunday open, or from 21:55 to 22:15 UK. "Any time" also opens
  no new trade after 20:30 UK on Friday (as the EMA pullback), so none is held over the weekend.
- **Big news "as the bounce":** no new trade from 15 minutes before to 30 minutes after a big release, and open trades
  closed 15 minutes before it. "As the EMA pullback": may open in the window, not closed before news.
- **IG's prices:** a buy opens on the buy price (the entry plus the spread at that candle's open) and is stopped and
  closed on the sell price; a sell opens on the sell price and is stopped and closed on the buy price.
- **Inside one 5-minute candle:** a scheduled close (20:30, news) at its open; then the stop or protection level
  (filled at the candle's open if it opened past it); then the take profit; then the close on a rejection at a level;
  then the 21 EMA close (at the candle's close). In the entry candle the stop counts only if the candle opened past the
  entry or closed beyond the stop (the entry-candle stop correction).
- **Profit protection:** "lock 15/10": once 15 pips up, close if it comes back to 10 up; "trail 10 from 25 up": once
  25 up, the stop follows 10 pips behind the best price; "21 EMA close from 10 up": once 10 up (the candle's own best
  counts), close at the close of a candle that closes back across the 21 EMA. Levels move from the next candle.
- **Take profit "X (100 on big-news days)":** 100 pips on a UK day with big news for the pair (5 and 6 November), X on
  other days.
- **The close on a rejection at a level:** the shared rejection part as the analyser runs it (a bounce the other way,
  at a level, that counts, triggering in a candle after the entry candle), filled at its trigger on the closing price.
- **Trades open at once:** "one at a time" (as section 6 now) or no limit. Other strategies are not in this replay.
- **Weeks** by entry time. **Marked** when the total is positive and one day gives at least 80% of it, or one week at
  least 90%.
- 2,150,400 combinations (12 entry mechanisms x 2 x 4 x 5 x 2 x 2 x 5 x 7 x 4 x 2 x 2 x 2).

**Limits of this test:** two weeks only; 5-minute candles, not ticks; no slippage beyond candle-open gaps; GBPUSD only.

## A. The current rules (the starting point)

Pause of 3 candles, entry below the pause's lowest point; in a trend and an emerging trend (the trend's direction); the direction rule; 06:00-20:30 UK; big news as the bounce (no new trade in the window, closed 15 minutes before); stop 6 (STOP_LOSS_PIPS), take profit 100 (TAKE_PROFIT_PIPS); no profit protection; closed at 20:30 UK every day; the close on a rejection at a level applied; one slow grind trade at a time; EMA pullback trades not considered.

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| Current rules | 23 | 11 | 12 | **+11.9** | -6.0 | 6 | +21.9 | -10.0 | one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9 |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Mon 26 Oct 09:05 | +3.5 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Mon 26 Oct 10:25 | -6.0 |
| Mon 26 Oct 13:55 | SELL | 13336.3 | emerging trend down | Mon 26 Oct 14:10 | -1.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Mon 26 Oct 20:30 | +2.9 |
| Tue 27 Oct 06:00 | SELL | 13331.3 | trend down, slow grind | Tue 27 Oct 07:20 | +5.9 |
| Tue 27 Oct 09:10 | SELL | 13318.4 | emerging trend down | Tue 27 Oct 09:55 | +1.2 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Tue 27 Oct 16:40 | +2.6 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 09:35 | +1.8 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 07:45 | -0.5 |
| Fri 30 Oct 09:05 | BUY | 13416.6 | trend up, slow grind | Fri 30 Oct 11:20 | +11.5 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Mon 02 Nov 09:25 | +31.2 |
| Mon 02 Nov 11:45 | BUY | 13419.7 | emerging trend up | Mon 02 Nov 11:50 | -6.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 08:00 | -6.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 11:50 | -3.7 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 08:35 | -6.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 09:20 | -6.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:30 | -6.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:05 | -6.0 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 07:50 | +2.0 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 08:45 | -6.0 |
| Fri 06 Nov 09:20 | SELL | 13389.4 | trend down, slow grind | Fri 06 Nov 10:35 | +0.2 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:05 | -4.1 |

## B. Each variable changed on its own

Everything else as in A; (A) marks the current value.

### 1. The pause's length (entry at its lowest point)

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| pause 2, the pause's lowest point | 28 | 13 | 15 | **+12.2** | -6.0 | 6 | +28.3 | -16.1 | one day gives +19.2 of +12.2; week 1 gives +28.3 of +12.2 |
| pause 3, the pause's lowest point (A) | 23 | 11 | 12 | **+11.9** | -6.0 | 6 | +21.9 | -10.0 | one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9 |
| pause 4, the pause's lowest point | 21 | 6 | 15 | **-18.9** | -6.0 | 6 | +15.1 | -34.0 |  |
| pause 5, the pause's lowest point | 13 | 2 | 11 | **-44.7** | -6.0 | 10 | +2.2 | -46.9 |  |

### 2. The pause's entry point (pause of 3)

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| pause 3, the pause's lowest point (A) | 23 | 11 | 12 | **+11.9** | -6.0 | 6 | +21.9 | -10.0 | one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9 |
| pause 3, the low before the pause | 28 | 5 | 23 | **-67.1** | -6.0 | 9 | -4.4 | -62.7 |  |

### 3. The owner's alternative: lower lows in a row

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| 3 lower lows in a row, then the next | 29 | 6 | 23 | **-60.0** | -6.0 | 5 | -38.9 | -21.1 |  |
| 4 lower lows in a row, then the next | 20 | 4 | 16 | **-33.3** | -6.0 | 7 | -28.7 | -4.6 |  |
| 5 lower lows in a row, then the next | 9 | 2 | 6 | **+5.3** | -6.0 | 2 | -24.0 | +29.3 | one day gives +31.7 of +5.3; week 2 gives +29.3 of +5.3 |
| 6 lower lows in a row, then the next | 7 | 1 | 6 | **-26.0** | -6.0 | 5 | -18.0 | -8.0 |  |

### 4. An EMA pullback trade open in the same direction

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| regardless (A) | 23 | 11 | 12 | **+11.9** | -6.0 | 6 | +21.9 | -10.0 | one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9 |
| only if no EMA pullback trade is open in the same direction | 9 | 5 | 4 | **-6.2** | -6.0 | 3 | +9.1 | -15.3 |  |

### 5. States allowed

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| trend only | 13 | 7 | 6 | **+13.6** | -6.0 | 3 | +14.9 | -1.3 | one day gives +20.1 of +13.6; week 1 gives +14.9 of +13.6 |
| trend and emerging trend (A) | 23 | 11 | 12 | **+11.9** | -6.0 | 6 | +21.9 | -10.0 | one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9 |
| trend only, type slow grind | 13 | 7 | 6 | **+13.6** | -6.0 | 3 | +14.9 | -1.3 | one day gives +20.1 of +13.6; week 1 gives +14.9 of +13.6 |
| emerging trend, or trend of type slow grind | 23 | 11 | 12 | **+11.9** | -6.0 | 6 | +21.9 | -10.0 | one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9 |

### 6. Direction filter

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| none | 32 | 12 | 20 | **-29.6** | -6.0 | 8 | -1.6 | -28.0 |  |
| the direction rule (A) | 23 | 11 | 12 | **+11.9** | -6.0 | 6 | +21.9 | -10.0 | one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9 |
| the day's 00:00 UK open | 26 | 11 | 15 | **-1.2** | -6.0 | 7 | +14.8 | -16.0 |  |
| the previous day's close | 26 | 11 | 15 | **-1.2** | -6.0 | 7 | +14.8 | -16.0 |  |
| the daily 20 EMA | 16 | 5 | 11 | **-10.3** | -6.0 | 8 | +4.6 | -14.9 |  |

### 7. Opening hours

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| 06:00-20:30 UK (A) | 23 | 11 | 12 | **+11.9** | -6.0 | 6 | +21.9 | -10.0 | one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9 |
| any time | 28 | 14 | 14 | **+64.4** | -6.0 | 4 | +24.4 | +40.0 |  |

### 8. Big news

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| as the bounce (A) | 23 | 11 | 12 | **+11.9** | -6.0 | 6 | +21.9 | -10.0 | one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9 |
| as the EMA pullback | 25 | 11 | 14 | **+0.2** | -6.0 | 8 | +21.9 | -21.7 | one day gives +25.2 of +0.2; week 1 gives +21.9 of +0.2 |

### 9. Stop loss

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| 6 (A) | 23 | 11 | 12 | **+11.9** | -6.0 | 6 | +21.9 | -10.0 | one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9 |
| 8 | 22 | 11 | 11 | **+18.1** | -8.0 | 6 | +23.2 | -5.1 | one day gives +23.2 of +18.1; week 1 gives +23.2 of +18.1 |
| 10 | 20 | 11 | 9 | **+28.1** | -10.0 | 4 | +23.2 | +4.9 |  |
| 12 | 20 | 11 | 9 | **+28.9** | -12.0 | 4 | +23.2 | +5.7 | one day gives +24.3 of +28.9 |
| 15 | 20 | 11 | 9 | **+25.9** | -15.0 | 4 | +23.2 | +2.7 | one day gives +24.3 of +25.9 |

### 10. Take profit

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| 20 | 23 | 11 | 12 | **+0.7** | -6.0 | 6 | +21.9 | -21.2 | one day gives +14.0 of +0.7; week 1 gives +21.9 of +0.7 |
| 30 | 23 | 11 | 12 | **+10.7** | -6.0 | 6 | +21.9 | -11.2 | one day gives +24.0 of +10.7; week 1 gives +21.9 of +10.7 |
| 50 | 23 | 11 | 12 | **+11.9** | -6.0 | 6 | +21.9 | -10.0 | one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9 |
| 100 (A) | 23 | 11 | 12 | **+11.9** | -6.0 | 6 | +21.9 | -10.0 | one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9 |
| 20 (100 on big-news days) | 23 | 11 | 12 | **+0.7** | -6.0 | 6 | +21.9 | -21.2 | one day gives +14.0 of +0.7; week 1 gives +21.9 of +0.7 |
| 30 (100 on big-news days) | 23 | 11 | 12 | **+10.7** | -6.0 | 6 | +21.9 | -11.2 | one day gives +24.0 of +10.7; week 1 gives +21.9 of +10.7 |
| 50 (100 on big-news days) | 23 | 11 | 12 | **+11.9** | -6.0 | 6 | +21.9 | -10.0 | one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9 |

### 11. Profit protection

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| none (A) | 23 | 11 | 12 | **+11.9** | -6.0 | 6 | +21.9 | -10.0 | one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9 |
| lock 15/10 | 23 | 11 | 12 | **+10.4** | -6.0 | 6 | +20.4 | -10.0 | one day gives +25.2 of +10.4; week 1 gives +20.4 of +10.4 |
| trail 10 from 25 up | 23 | 11 | 12 | **+13.2** | -6.0 | 6 | +21.9 | -8.7 | one day gives +26.5 of +13.2; week 1 gives +21.9 of +13.2 |
| 21 EMA close from 10 up | 23 | 11 | 12 | **+6.3** | -6.0 | 6 | +16.3 | -10.0 | one day gives +25.2 of +6.3; week 1 gives +16.3 of +6.3 |

### 12. Holding

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| daily 20:30 (A) | 23 | 11 | 12 | **+11.9** | -6.0 | 6 | +21.9 | -10.0 | one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9 |
| Friday 20:30 | 23 | 11 | 12 | **+10.5** | -6.0 | 6 | +20.5 | -10.0 | one day gives +25.2 of +10.5; week 1 gives +20.5 of +10.5 |

### 13. The close on a rejection at a level

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| applied (A) | 23 | 11 | 12 | **+11.9** | -6.0 | 6 | +21.9 | -10.0 | one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9 |
| not applied | 16 | 4 | 12 | **-22.3** | -6.0 | 5 | +22.3 | -44.6 |  |

### 14. Trades open at once

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| one at a time (A) | 23 | 11 | 12 | **+11.9** | -6.0 | 6 | +21.9 | -10.0 | one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9 |
| no limit | 32 | 15 | 17 | **+34.2** | -6.0 | 7 | +13.0 | +21.2 | one day gives +63.5 of +34.2 |

## C1. The 10 best combinations

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 67 | 24 | 43 | **+754.6** | -15.0 | 13 | +305.0 | +449.6 |  |
| 2 | 73 | 25 | 48 | **+729.6** | -15.0 | 16 | +280.0 | +449.6 |  |
| 3 | 73 | 25 | 48 | **+729.6** | -15.0 | 16 | +280.0 | +449.6 |  |
| 4 | 67 | 30 | 37 | **+724.6** | -15.0 | 13 | +330.0 | +394.6 |  |
| 5 | 74 | 25 | 49 | **+714.6** | -15.0 | 16 | +280.0 | +434.6 | one day gives +574.6 of +714.6 |
| 6 | 74 | 25 | 49 | **+714.6** | -15.0 | 16 | +280.0 | +434.6 | one day gives +574.6 of +714.6 |
| 7 | 66 | 23 | 43 | **+704.6** | -15.0 | 13 | +305.0 | +399.6 | one day gives +574.6 of +704.6 |
| 8 | 66 | 29 | 37 | **+694.6** | -15.0 | 13 | +330.0 | +364.6 | one day gives +574.6 of +694.6 |
| 9 | 73 | 31 | 42 | **+679.6** | -15.0 | 13 | +285.0 | +394.6 | one day gives +574.6 of +679.6 |
| 10 | 73 | 31 | 42 | **+679.6** | -15.0 | 13 | +285.0 | +394.6 | one day gives +574.6 of +679.6 |

1. entry: pause 2, the pause's lowest point; hours: any time; news: as the EMA pullback; stop: 15; take profit: 50 (100 on big-news days); holding: Friday 20:30; level close: not applied; trades at once: no limit
2. entry: pause 2, the pause's lowest point; states: emerging trend, or trend of type slow grind; direction: the day's 00:00 UK open; hours: any time; news: as the EMA pullback; stop: 15; take profit: 50 (100 on big-news days); holding: Friday 20:30; level close: not applied; trades at once: no limit
3. entry: pause 2, the pause's lowest point; states: emerging trend, or trend of type slow grind; direction: the previous day's close; hours: any time; news: as the EMA pullback; stop: 15; take profit: 50 (100 on big-news days); holding: Friday 20:30; level close: not applied; trades at once: no limit
4. entry: pause 2, the pause's lowest point; hours: any time; news: as the EMA pullback; stop: 15; take profit: 30 (100 on big-news days); holding: Friday 20:30; level close: not applied; trades at once: no limit
5. entry: pause 2, the pause's lowest point; direction: the day's 00:00 UK open; hours: any time; news: as the EMA pullback; stop: 15; take profit: 50 (100 on big-news days); holding: Friday 20:30; level close: not applied; trades at once: no limit
6. entry: pause 2, the pause's lowest point; direction: the previous day's close; hours: any time; news: as the EMA pullback; stop: 15; take profit: 50 (100 on big-news days); holding: Friday 20:30; level close: not applied; trades at once: no limit
7. entry: pause 2, the pause's lowest point; states: emerging trend, or trend of type slow grind; hours: any time; news: as the EMA pullback; stop: 15; take profit: 50 (100 on big-news days); holding: Friday 20:30; level close: not applied; trades at once: no limit
8. entry: pause 2, the pause's lowest point; states: emerging trend, or trend of type slow grind; hours: any time; news: as the EMA pullback; stop: 15; take profit: 30 (100 on big-news days); holding: Friday 20:30; level close: not applied; trades at once: no limit
9. entry: pause 2, the pause's lowest point; states: emerging trend, or trend of type slow grind; direction: the day's 00:00 UK open; hours: any time; news: as the EMA pullback; stop: 15; take profit: 30 (100 on big-news days); holding: Friday 20:30; level close: not applied; trades at once: no limit
10. entry: pause 2, the pause's lowest point; states: emerging trend, or trend of type slow grind; direction: the previous day's close; hours: any time; news: as the EMA pullback; stop: 15; take profit: 30 (100 on big-news days); holding: Friday 20:30; level close: not applied; trades at once: no limit

## C2. The 10 worst combinations

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 65 | 4 | 61 | **-731.1** | -15.0 | 53 | -390.6 | -340.5 |  |
| 2 | 63 | 4 | 59 | **-701.1** | -15.0 | 51 | -390.6 | -310.5 |  |
| 3 | 60 | 4 | 56 | **-653.4** | -16.3 | 47 | -315.8 | -337.6 |  |
| 4 | 46 | 1 | 45 | **-646.6** | -15.0 | 44 | -285.0 | -361.6 |  |
| 5 | 45 | 1 | 44 | **-631.6** | -15.0 | 43 | -285.0 | -346.6 |  |
| 6 | 58 | 4 | 54 | **-622.3** | -16.3 | 46 | -315.8 | -306.5 |  |
| 7 | 63 | 10 | 53 | **-617.9** | -15.0 | 27 | -390.6 | -227.3 |  |
| 8 | 61 | 9 | 52 | **-617.4** | -15.0 | 27 | -390.6 | -226.8 |  |
| 9 | 59 | 8 | 51 | **-596.1** | -16.1 | 22 | -315.8 | -280.3 |  |
| 10 | 40 | 0 | 40 | **-588.5** | -16.1 | 40 | -225.0 | -363.5 |  |

1. entry: pause 2, the pause's lowest point; direction: none; news: as the EMA pullback; stop: 15; holding: Friday 20:30; level close: not applied; trades at once: no limit
2. entry: pause 2, the pause's lowest point; states: emerging trend, or trend of type slow grind; direction: none; news: as the EMA pullback; stop: 15; holding: Friday 20:30; level close: not applied; trades at once: no limit
3. entry: pause 2, the low before the pause; direction: none; news: as the EMA pullback; stop: 15; holding: Friday 20:30; level close: not applied; trades at once: no limit
4. entry: pause 2, the pause's lowest point; direction: the daily 20 EMA; hours: any time; news: as the EMA pullback; stop: 15; holding: Friday 20:30; level close: not applied; trades at once: no limit
5. entry: pause 2, the pause's lowest point; states: emerging trend, or trend of type slow grind; direction: the daily 20 EMA; hours: any time; news: as the EMA pullback; stop: 15; holding: Friday 20:30; level close: not applied; trades at once: no limit
6. entry: pause 2, the low before the pause; states: emerging trend, or trend of type slow grind; direction: none; news: as the EMA pullback; stop: 15; holding: Friday 20:30; level close: not applied; trades at once: no limit
7. entry: pause 2, the pause's lowest point; direction: none; stop: 15; holding: Friday 20:30; level close: not applied; trades at once: no limit
8. entry: pause 2, the pause's lowest point; states: emerging trend, or trend of type slow grind; direction: none; stop: 15; holding: Friday 20:30; level close: not applied; trades at once: no limit
9. entry: pause 2, the low before the pause; direction: none; stop: 15; holding: Friday 20:30; level close: not applied; trades at once: no limit
10. entry: pause 2, the low before the pause; direction: the daily 20 EMA; hours: any time; news: as the EMA pullback; stop: 15; holding: Friday 20:30; level close: not applied; trades at once: no limit

## D. The measures

Every table gives trades, wins, losses, total pips, the biggest single loss, the worst run of losses in a row, and each week's pips (week 1: 26-30 October; week 2: 2-6 November).

## E. Results where nearly all the profit comes from one day or one week

- **A** (+11.9): one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9
- **B 1: pause 2, the pause's lowest point** (+12.2): one day gives +19.2 of +12.2; week 1 gives +28.3 of +12.2
- **B 1: pause 3, the pause's lowest point** (+11.9): one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9
- **B 2: pause 3, the pause's lowest point** (+11.9): one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9
- **B 3: 5 lower lows in a row, then the next** (+5.3): one day gives +31.7 of +5.3; week 2 gives +29.3 of +5.3
- **B 4: regardless** (+11.9): one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9
- **B 5: trend only** (+13.6): one day gives +20.1 of +13.6; week 1 gives +14.9 of +13.6
- **B 5: trend and emerging trend** (+11.9): one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9
- **B 5: trend only, type slow grind** (+13.6): one day gives +20.1 of +13.6; week 1 gives +14.9 of +13.6
- **B 5: emerging trend, or trend of type slow grind** (+11.9): one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9
- **B 6: the direction rule** (+11.9): one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9
- **B 7: 06:00-20:30 UK** (+11.9): one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9
- **B 8: as the bounce** (+11.9): one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9
- **B 8: as the EMA pullback** (+0.2): one day gives +25.2 of +0.2; week 1 gives +21.9 of +0.2
- **B 9: 6** (+11.9): one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9
- **B 9: 8** (+18.1): one day gives +23.2 of +18.1; week 1 gives +23.2 of +18.1
- **B 9: 12** (+28.9): one day gives +24.3 of +28.9
- **B 9: 15** (+25.9): one day gives +24.3 of +25.9
- **B 10: 20** (+0.7): one day gives +14.0 of +0.7; week 1 gives +21.9 of +0.7
- **B 10: 30** (+10.7): one day gives +24.0 of +10.7; week 1 gives +21.9 of +10.7
- **B 10: 50** (+11.9): one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9
- **B 10: 100** (+11.9): one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9
- **B 10: 20 (100 on big-news days)** (+0.7): one day gives +14.0 of +0.7; week 1 gives +21.9 of +0.7
- **B 10: 30 (100 on big-news days)** (+10.7): one day gives +24.0 of +10.7; week 1 gives +21.9 of +10.7
- **B 10: 50 (100 on big-news days)** (+11.9): one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9
- **B 11: none** (+11.9): one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9
- **B 11: lock 15/10** (+10.4): one day gives +25.2 of +10.4; week 1 gives +20.4 of +10.4
- **B 11: trail 10 from 25 up** (+13.2): one day gives +26.5 of +13.2; week 1 gives +21.9 of +13.2
- **B 11: 21 EMA close from 10 up** (+6.3): one day gives +25.2 of +6.3; week 1 gives +16.3 of +6.3
- **B 12: daily 20:30** (+11.9): one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9
- **B 12: Friday 20:30** (+10.5): one day gives +25.2 of +10.5; week 1 gives +20.5 of +10.5
- **B 13: applied** (+11.9): one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9
- **B 14: one at a time** (+11.9): one day gives +25.2 of +11.9; week 1 gives +21.9 of +11.9
- **B 14: no limit** (+34.2): one day gives +63.5 of +34.2
- **C1 #5** (+714.6): one day gives +574.6 of +714.6
- **C1 #6** (+714.6): one day gives +574.6 of +714.6
- **C1 #7** (+704.6): one day gives +574.6 of +704.6
- **C1 #8** (+694.6): one day gives +574.6 of +694.6
- **C1 #9** (+679.6): one day gives +574.6 of +679.6
- **C1 #10** (+679.6): one day gives +574.6 of +679.6

Of all 2,150,400 combinations, 353,521 have a positive total; 319,352 of those get nearly all their profit from one day or one week; 130,887 are positive in both weeks.

## F. Every combination positive in both weeks and not marked, best first

**34,169 combinations.** Listing each with its trades would make this file about 70 MB, so it is not included in full. Below: how often each value of each variable appears among them (against all combinations), then the 50 best different results, best first, each with its trades; combinations giving exactly the same result are grouped, with how many there are and what they share.

### How often each value appears in F

| Variable | Value | In F | Share of F | Share of all combinations |
|---|---|---|---|---|
| entry | pause 2, the pause's lowest point | 10,185 | 30% | 8% |
| entry | pause 3, the pause's lowest point | 8,277 | 24% | 8% |
| entry | pause 4, the pause's lowest point | 8,071 | 24% | 8% |
| entry | 4 lower lows in a row, then the next | 1,808 | 5% | 8% |
| entry | pause 5, the pause's lowest point | 1,425 | 4% | 8% |
| entry | pause 2, the low before the pause | 1,387 | 4% | 8% |
| entry | pause 3, the low before the pause | 1,343 | 4% | 8% |
| entry | pause 4, the low before the pause | 842 | 2% | 8% |
| entry | pause 5, the low before the pause | 507 | 1% | 8% |
| entry | 6 lower lows in a row, then the next | 210 | 1% | 8% |
| entry | 5 lower lows in a row, then the next | 90 | 0% | 8% |
| entry | 3 lower lows in a row, then the next | 24 | 0% | 8% |
| EMA pullback open | regardless | 31,064 | 91% | 50% |
| EMA pullback open | only if no EMA pullback trade is open in the same direction | 3,105 | 9% | 50% |
| states | trend only, type slow grind | 16,048 | 47% | 25% |
| states | trend only | 14,677 | 43% | 25% |
| states | emerging trend, or trend of type slow grind | 1,855 | 5% | 25% |
| states | trend and emerging trend | 1,589 | 5% | 25% |
| direction | the direction rule | 12,107 | 35% | 20% |
| direction | the day's 00:00 UK open | 7,711 | 23% | 20% |
| direction | the previous day's close | 7,711 | 23% | 20% |
| direction | the daily 20 EMA | 3,589 | 11% | 20% |
| direction | none | 3,051 | 9% | 20% |
| hours | any time | 28,279 | 83% | 50% |
| hours | 06:00-20:30 UK | 5,890 | 17% | 50% |
| news | as the bounce | 23,874 | 70% | 50% |
| news | as the EMA pullback | 10,295 | 30% | 50% |
| stop | 15 | 8,436 | 25% | 20% |
| stop | 10 | 7,704 | 23% | 20% |
| stop | 12 | 6,295 | 18% | 20% |
| stop | 6 | 6,203 | 18% | 20% |
| stop | 8 | 5,531 | 16% | 20% |
| take profit | 20 | 6,617 | 19% | 14% |
| take profit | 20 (100 on big-news days) | 6,134 | 18% | 14% |
| take profit | 30 (100 on big-news days) | 5,260 | 15% | 14% |
| take profit | 30 | 5,164 | 15% | 14% |
| take profit | 50 | 3,915 | 11% | 14% |
| take profit | 50 (100 on big-news days) | 3,841 | 11% | 14% |
| take profit | 100 | 3,238 | 9% | 14% |
| protection | none | 11,670 | 34% | 25% |
| protection | trail 10 from 25 up | 8,231 | 24% | 25% |
| protection | lock 15/10 | 7,331 | 21% | 25% |
| protection | 21 EMA close from 10 up | 6,937 | 20% | 25% |
| holding | Friday 20:30 | 18,687 | 55% | 50% |
| holding | daily 20:30 | 15,482 | 45% | 50% |
| level close | applied | 17,151 | 50% | 50% |
| level close | not applied | 17,018 | 50% | 50% |
| trades at once | one at a time | 24,573 | 72% | 50% |
| trades at once | no limit | 9,596 | 28% | 50% |

### The 50 best different results


#### F1. +754.6 pips, 1 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend and emerging trend; direction: the direction rule; hours: any time; news: as the EMA pullback; stop: 15; take profit: 50 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.


| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F1 | 67 | 24 | 43 | **+754.6** | -15.0 | 13 | +305.0 | +449.6 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Wed 28 Oct 04:15 | +50.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 16:30 | -15.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Wed 28 Oct 04:20 | +50.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Wed 28 Oct 04:15 | +50.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 07:10 | +50.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Wed 28 Oct 16:50 | -15.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -15.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 16:10 | -15.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 13:30 | -15.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:25 | -15.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Fri 30 Oct 14:05 | -15.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:45 | -15.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 13:00 | -15.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:50 | -15.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:35 | -15.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Wed 04 Nov 01:15 | +50.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:50 | -15.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:45 | -15.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 18:35 | -15.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 16:05 | -15.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -15.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 04:05 | -15.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Wed 04 Nov 01:25 | +50.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 10:05 | -15.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:25 | -15.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Wed 04 Nov 01:30 | +50.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:50 | -15.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:25 | -15.0 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -15.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -15.0 |
| Wed 04 Nov 00:15 | BUY | 13432.8 | trend up, strong push | Wed 04 Nov 08:40 | +50.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -15.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -15.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -15.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:40 | -15.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -15.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 14:10 | +100.0 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 20:30 | +80.1 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 20:30 | +53.6 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 20:30 | +44.2 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 20:30 | +43.3 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 12:20 | -15.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:25 | -15.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 11:15 | -15.0 |
| Fri 06 Nov 13:30 | SELL | 13383.9 | trend down, slow grind | Fri 06 Nov 13:30 | -15.0 |
| Fri 06 Nov 13:45 | SELL | 13366.7 | trend down, slow grind | Fri 06 Nov 20:30 | +15.3 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F2. +729.6 pips, 2 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: emerging trend, or trend of type slow grind; hours: any time; news: as the EMA pullback; stop: 15; take profit: 50 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.
Any of: direction: the day's 00:00 UK open / the previous day's close.

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F2 | 73 | 25 | 48 | **+729.6** | -15.0 | 16 | +280.0 | +449.6 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 01:50 | BUY | 13384.0 | emerging trend up | Mon 26 Oct 05:50 | -15.0 |
| Mon 26 Oct 06:05 | SELL | 13371.1 | trend down, slow grind | Tue 27 Oct 07:05 | +50.0 |
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Wed 28 Oct 04:15 | +50.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 16:30 | -15.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Wed 28 Oct 04:20 | +50.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Wed 28 Oct 04:15 | +50.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 07:10 | +50.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Wed 28 Oct 16:50 | -15.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -15.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 16:10 | -15.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 13:30 | -15.0 |
| Wed 28 Oct 16:50 | BUY | 13313.2 | trend up, slow grind | Wed 28 Oct 17:50 | -15.0 |
| Thu 29 Oct 05:05 | SELL | 13318.6 | trend down, slow grind | Thu 29 Oct 12:30 | -15.0 |
| Thu 29 Oct 05:25 | SELL | 13316.5 | trend down, slow grind | Thu 29 Oct 11:20 | -15.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:25 | -15.0 |
| Thu 29 Oct 13:15 | SELL | 13314.2 | emerging trend down | Thu 29 Oct 13:35 | -15.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Fri 30 Oct 14:05 | -15.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:45 | -15.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 13:00 | -15.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:50 | -15.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:35 | -15.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Wed 04 Nov 01:15 | +50.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:50 | -15.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:45 | -15.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 18:35 | -15.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 16:05 | -15.0 |
| Mon 02 Nov 23:45 | BUY | 13406.0 | emerging trend up | Wed 04 Nov 01:20 | +50.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -15.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 04:05 | -15.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Wed 04 Nov 01:25 | +50.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 10:05 | -15.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:25 | -15.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Wed 04 Nov 01:30 | +50.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:50 | -15.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:25 | -15.0 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -15.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -15.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -15.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -15.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -15.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:40 | -15.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -15.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 14:10 | +100.0 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 20:30 | +80.1 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 20:30 | +53.6 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 20:30 | +44.2 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 20:30 | +43.3 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 12:20 | -15.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:25 | -15.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 11:15 | -15.0 |
| Fri 06 Nov 13:30 | SELL | 13383.9 | trend down, slow grind | Fri 06 Nov 13:30 | -15.0 |
| Fri 06 Nov 13:45 | SELL | 13366.7 | trend down, slow grind | Fri 06 Nov 20:30 | +15.3 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F3. +724.6 pips, 1 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend and emerging trend; direction: the direction rule; hours: any time; news: as the EMA pullback; stop: 15; take profit: 30 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.


| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F3 | 67 | 30 | 37 | **+724.6** | -15.0 | 13 | +330.0 | +394.6 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Mon 26 Oct 13:55 | +30.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 07:00 | +30.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Tue 27 Oct 09:20 | +30.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Tue 27 Oct 09:25 | +30.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 16:30 | -15.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Tue 27 Oct 09:25 | +30.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Tue 27 Oct 09:20 | +30.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Tue 27 Oct 09:25 | +30.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 01:00 | +30.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 01:00 | +30.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 04:10 | +30.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 06:30 | +30.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Wed 28 Oct 06:50 | +30.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Wed 28 Oct 07:10 | +30.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -15.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 16:10 | -15.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 13:30 | -15.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:25 | -15.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Fri 30 Oct 09:10 | +30.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 10:10 | +30.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 13:00 | -15.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:50 | -15.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:35 | -15.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Mon 02 Nov 08:45 | +30.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 09:00 | +30.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:45 | -15.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 18:35 | -15.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 16:05 | -15.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -15.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 04:05 | -15.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Wed 04 Nov 01:00 | +30.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 10:05 | -15.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:25 | -15.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Wed 04 Nov 01:00 | +30.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:50 | -15.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:25 | -15.0 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -15.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -15.0 |
| Wed 04 Nov 00:15 | BUY | 13432.8 | trend up, strong push | Wed 04 Nov 01:30 | +30.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 01:35 | +30.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -15.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -15.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -15.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:40 | -15.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -15.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 14:10 | +100.0 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 20:30 | +80.1 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 20:30 | +53.6 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 20:30 | +44.2 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 20:30 | +43.3 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 12:20 | -15.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:25 | -15.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 11:15 | -15.0 |
| Fri 06 Nov 13:30 | SELL | 13383.9 | trend down, slow grind | Fri 06 Nov 13:30 | -15.0 |
| Fri 06 Nov 13:45 | SELL | 13366.7 | trend down, slow grind | Fri 06 Nov 20:30 | +15.3 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F4. +590.2 pips, 1 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend and emerging trend; direction: the direction rule; hours: any time; news: as the EMA pullback; stop: 10; take profit: 50 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.


| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F4 | 67 | 17 | 50 | **+590.2** | -11.6 | 14 | +250.0 | +340.2 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Mon 26 Oct 11:40 | -10.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Mon 26 Oct 11:40 | -10.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 14:45 | -10.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Wed 28 Oct 04:20 | +50.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Wed 28 Oct 04:15 | +50.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 07:10 | +50.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 18:35 | -10.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Tue 27 Oct 17:20 | -10.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Tue 27 Oct 21:00 | -10.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -10.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 13:40 | -10.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 11:45 | -10.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:10 | -10.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Thu 29 Oct 23:35 | -10.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:25 | -10.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 12:50 | -10.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:40 | -10.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:00 | -10.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Wed 04 Nov 01:15 | +50.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:35 | -10.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:30 | -10.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 14:10 | -10.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 15:35 | -10.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -10.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 03:40 | -10.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Tue 03 Nov 11:25 | -10.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 08:45 | -10.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 12:10 | -10.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Tue 03 Nov 12:30 | -10.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:45 | -10.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:00 | -11.6 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -10.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -10.0 |
| Wed 04 Nov 00:15 | BUY | 13432.8 | trend up, strong push | Wed 04 Nov 08:40 | +50.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -10.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 10:40 | -10.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:30 | -10.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:30 | -10.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -10.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 12:00 | -10.0 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 12:00 | -10.0 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 12:00 | -10.0 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 12:00 | -10.0 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:35 | -10.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:20 | -10.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:15 | -10.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -10.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 14:10 | +100.0 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 20:30 | +80.1 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 20:30 | +53.6 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 12:20 | -10.0 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 12:20 | -10.0 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 11:15 | -10.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 10:55 | -10.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 10:50 | -10.0 |
| Fri 06 Nov 13:30 | SELL | 13383.9 | trend down, slow grind | Fri 06 Nov 13:30 | -10.0 |
| Fri 06 Nov 13:45 | SELL | 13366.7 | trend down, slow grind | Fri 06 Nov 15:20 | -10.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F5. +533.4 pips, 1 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend and emerging trend; direction: the direction rule; hours: any time; news: as the EMA pullback; stop: 15; take profit: 50; protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.


| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F5 | 67 | 24 | 43 | **+533.4** | -15.0 | 13 | +305.0 | +228.4 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Wed 28 Oct 04:15 | +50.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 16:30 | -15.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Wed 28 Oct 04:20 | +50.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Wed 28 Oct 04:15 | +50.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 07:10 | +50.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Wed 28 Oct 16:50 | -15.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -15.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 16:10 | -15.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 13:30 | -15.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:25 | -15.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Fri 30 Oct 14:05 | -15.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:45 | -15.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 13:00 | -15.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:50 | -15.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:35 | -15.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Wed 04 Nov 01:15 | +50.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:50 | -15.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:45 | -15.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 18:35 | -15.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 16:05 | -15.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -15.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 04:05 | -15.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Wed 04 Nov 01:25 | +50.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 10:05 | -15.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:25 | -15.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Wed 04 Nov 01:30 | +50.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:50 | -15.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:25 | -15.0 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -15.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -15.0 |
| Wed 04 Nov 00:15 | BUY | 13432.8 | trend up, strong push | Wed 04 Nov 08:40 | +50.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -15.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -15.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -15.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:40 | -15.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -15.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:30 | +50.0 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 14:05 | +50.0 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 14:15 | +50.0 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 14:15 | +50.0 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 12:20 | -15.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:25 | -15.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 11:15 | -15.0 |
| Fri 06 Nov 13:30 | SELL | 13383.9 | trend down, slow grind | Fri 06 Nov 13:30 | -15.0 |
| Fri 06 Nov 13:45 | SELL | 13366.7 | trend down, slow grind | Fri 06 Nov 20:30 | +15.3 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F6. +525.5 pips, 1 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend and emerging trend; direction: the direction rule; hours: any time; news: as the bounce; stop: 15; take profit: 50 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.


| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F6 | 65 | 27 | 38 | **+525.5** | -15.0 | 12 | +305.0 | +220.5 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Wed 28 Oct 04:15 | +50.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 16:30 | -15.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Wed 28 Oct 04:20 | +50.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Wed 28 Oct 04:15 | +50.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 07:10 | +50.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Wed 28 Oct 16:50 | -15.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -15.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 16:10 | -15.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 13:30 | -15.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:25 | -15.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Fri 30 Oct 14:05 | -15.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:45 | -15.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 13:00 | -15.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:50 | -15.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:35 | -15.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Wed 04 Nov 01:15 | +50.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:50 | -15.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:45 | -15.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 18:35 | -15.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 16:05 | -15.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -15.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 04:05 | -15.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Wed 04 Nov 01:25 | +50.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 10:05 | -15.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:25 | -15.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Wed 04 Nov 01:30 | +50.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:50 | -15.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:25 | -15.0 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -15.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -15.0 |
| Wed 04 Nov 00:15 | BUY | 13432.8 | trend up, strong push | Wed 04 Nov 08:40 | +50.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -15.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -15.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -15.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:40 | -15.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -15.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 13:15 | +61.8 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 13:15 | +58.9 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 13:15 | +8.3 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 13:15 | +7.4 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 12:20 | -15.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:25 | -15.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 11:15 | -15.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F7. +515.0 pips, 2 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend and emerging trend; hours: any time; news: as the bounce; stop: 15; take profit: 50 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.
Any of: direction: the day's 00:00 UK open / the previous day's close.

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F7 | 72 | 29 | 43 | **+515.0** | -15.0 | 16 | +280.0 | +235.0 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 01:50 | BUY | 13384.0 | emerging trend up | Mon 26 Oct 05:50 | -15.0 |
| Mon 26 Oct 06:05 | SELL | 13371.1 | trend down, slow grind | Tue 27 Oct 07:05 | +50.0 |
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Wed 28 Oct 04:15 | +50.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 16:30 | -15.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Wed 28 Oct 04:20 | +50.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Wed 28 Oct 04:15 | +50.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 07:10 | +50.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Wed 28 Oct 16:50 | -15.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -15.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 16:10 | -15.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 13:30 | -15.0 |
| Wed 28 Oct 16:50 | BUY | 13313.2 | trend up, slow grind | Wed 28 Oct 17:50 | -15.0 |
| Thu 29 Oct 05:05 | SELL | 13318.6 | trend down, slow grind | Thu 29 Oct 12:30 | -15.0 |
| Thu 29 Oct 05:25 | SELL | 13316.5 | trend down, slow grind | Thu 29 Oct 11:20 | -15.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:25 | -15.0 |
| Thu 29 Oct 13:15 | SELL | 13314.2 | emerging trend down | Thu 29 Oct 13:35 | -15.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Fri 30 Oct 14:05 | -15.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:45 | -15.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 13:00 | -15.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:50 | -15.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:35 | -15.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Wed 04 Nov 01:15 | +50.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:50 | -15.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:45 | -15.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 18:35 | -15.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 16:05 | -15.0 |
| Mon 02 Nov 23:45 | BUY | 13406.0 | emerging trend up | Wed 04 Nov 01:20 | +50.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -15.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 04:05 | -15.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Wed 04 Nov 01:25 | +50.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 10:05 | -15.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:25 | -15.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Wed 04 Nov 01:30 | +50.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:50 | -15.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:25 | -15.0 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -15.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -15.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -15.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -15.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -15.0 |
| Thu 05 Nov 08:00 | SELL | 13469.9 | trend down, strong push | Thu 05 Nov 11:45 | +14.5 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:40 | -15.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -15.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 13:15 | +61.8 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 13:15 | +58.9 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 13:15 | +8.3 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 13:15 | +7.4 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 12:20 | -15.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:25 | -15.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 11:15 | -15.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F8. +508.4 pips, 2 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: emerging trend, or trend of type slow grind; hours: any time; news: as the EMA pullback; stop: 15; take profit: 50; protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.
Any of: direction: the day's 00:00 UK open / the previous day's close.

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F8 | 73 | 25 | 48 | **+508.4** | -15.0 | 16 | +280.0 | +228.4 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 01:50 | BUY | 13384.0 | emerging trend up | Mon 26 Oct 05:50 | -15.0 |
| Mon 26 Oct 06:05 | SELL | 13371.1 | trend down, slow grind | Tue 27 Oct 07:05 | +50.0 |
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Wed 28 Oct 04:15 | +50.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 16:30 | -15.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Wed 28 Oct 04:20 | +50.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Wed 28 Oct 04:15 | +50.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 07:10 | +50.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Wed 28 Oct 16:50 | -15.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -15.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 16:10 | -15.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 13:30 | -15.0 |
| Wed 28 Oct 16:50 | BUY | 13313.2 | trend up, slow grind | Wed 28 Oct 17:50 | -15.0 |
| Thu 29 Oct 05:05 | SELL | 13318.6 | trend down, slow grind | Thu 29 Oct 12:30 | -15.0 |
| Thu 29 Oct 05:25 | SELL | 13316.5 | trend down, slow grind | Thu 29 Oct 11:20 | -15.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:25 | -15.0 |
| Thu 29 Oct 13:15 | SELL | 13314.2 | emerging trend down | Thu 29 Oct 13:35 | -15.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Fri 30 Oct 14:05 | -15.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:45 | -15.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 13:00 | -15.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:50 | -15.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:35 | -15.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Wed 04 Nov 01:15 | +50.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:50 | -15.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:45 | -15.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 18:35 | -15.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 16:05 | -15.0 |
| Mon 02 Nov 23:45 | BUY | 13406.0 | emerging trend up | Wed 04 Nov 01:20 | +50.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -15.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 04:05 | -15.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Wed 04 Nov 01:25 | +50.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 10:05 | -15.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:25 | -15.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Wed 04 Nov 01:30 | +50.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:50 | -15.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:25 | -15.0 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -15.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -15.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -15.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -15.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -15.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:40 | -15.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -15.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:30 | +50.0 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 14:05 | +50.0 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 14:15 | +50.0 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 14:15 | +50.0 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 12:20 | -15.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:25 | -15.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 11:15 | -15.0 |
| Fri 06 Nov 13:30 | SELL | 13383.9 | trend down, slow grind | Fri 06 Nov 13:30 | -15.0 |
| Fri 06 Nov 13:45 | SELL | 13366.7 | trend down, slow grind | Fri 06 Nov 20:30 | +15.3 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F9. +500.5 pips, 2 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: emerging trend, or trend of type slow grind; hours: any time; news: as the bounce; stop: 15; take profit: 50 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.
Any of: direction: the day's 00:00 UK open / the previous day's close.

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F9 | 71 | 28 | 43 | **+500.5** | -15.0 | 16 | +280.0 | +220.5 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 01:50 | BUY | 13384.0 | emerging trend up | Mon 26 Oct 05:50 | -15.0 |
| Mon 26 Oct 06:05 | SELL | 13371.1 | trend down, slow grind | Tue 27 Oct 07:05 | +50.0 |
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Wed 28 Oct 04:15 | +50.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 16:30 | -15.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Wed 28 Oct 04:20 | +50.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Wed 28 Oct 04:15 | +50.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 07:10 | +50.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Wed 28 Oct 16:50 | -15.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -15.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 16:10 | -15.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 13:30 | -15.0 |
| Wed 28 Oct 16:50 | BUY | 13313.2 | trend up, slow grind | Wed 28 Oct 17:50 | -15.0 |
| Thu 29 Oct 05:05 | SELL | 13318.6 | trend down, slow grind | Thu 29 Oct 12:30 | -15.0 |
| Thu 29 Oct 05:25 | SELL | 13316.5 | trend down, slow grind | Thu 29 Oct 11:20 | -15.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:25 | -15.0 |
| Thu 29 Oct 13:15 | SELL | 13314.2 | emerging trend down | Thu 29 Oct 13:35 | -15.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Fri 30 Oct 14:05 | -15.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:45 | -15.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 13:00 | -15.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:50 | -15.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:35 | -15.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Wed 04 Nov 01:15 | +50.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:50 | -15.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:45 | -15.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 18:35 | -15.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 16:05 | -15.0 |
| Mon 02 Nov 23:45 | BUY | 13406.0 | emerging trend up | Wed 04 Nov 01:20 | +50.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -15.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 04:05 | -15.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Wed 04 Nov 01:25 | +50.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 10:05 | -15.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:25 | -15.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Wed 04 Nov 01:30 | +50.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:50 | -15.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:25 | -15.0 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -15.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -15.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -15.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -15.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -15.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:40 | -15.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -15.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 13:15 | +61.8 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 13:15 | +58.9 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 13:15 | +8.3 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 13:15 | +7.4 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 12:20 | -15.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:25 | -15.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 11:15 | -15.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F10. +495.5 pips, 1 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend and emerging trend; direction: the direction rule; hours: any time; news: as the bounce; stop: 15; take profit: 30 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.


| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F10 | 65 | 33 | 32 | **+495.5** | -15.0 | 5 | +330.0 | +165.5 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Mon 26 Oct 13:55 | +30.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 07:00 | +30.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Tue 27 Oct 09:20 | +30.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Tue 27 Oct 09:25 | +30.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 16:30 | -15.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Tue 27 Oct 09:25 | +30.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Tue 27 Oct 09:20 | +30.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Tue 27 Oct 09:25 | +30.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 01:00 | +30.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 01:00 | +30.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 04:10 | +30.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 06:30 | +30.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Wed 28 Oct 06:50 | +30.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Wed 28 Oct 07:10 | +30.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -15.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 16:10 | -15.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 13:30 | -15.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:25 | -15.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Fri 30 Oct 09:10 | +30.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 10:10 | +30.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 13:00 | -15.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:50 | -15.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:35 | -15.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Mon 02 Nov 08:45 | +30.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 09:00 | +30.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:45 | -15.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 18:35 | -15.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 16:05 | -15.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -15.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 04:05 | -15.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Wed 04 Nov 01:00 | +30.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 10:05 | -15.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:25 | -15.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Wed 04 Nov 01:00 | +30.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:50 | -15.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:25 | -15.0 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -15.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -15.0 |
| Wed 04 Nov 00:15 | BUY | 13432.8 | trend up, strong push | Wed 04 Nov 01:30 | +30.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 01:35 | +30.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -15.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -15.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -15.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:40 | -15.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -15.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 13:15 | +61.8 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 13:15 | +58.9 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 13:15 | +8.3 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 13:15 | +7.4 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 12:20 | -15.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:25 | -15.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 11:15 | -15.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F11. +493.4 pips, 2 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend and emerging trend; hours: any time; news: as the EMA pullback; stop: 15; take profit: 50; protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.
Any of: direction: the day's 00:00 UK open / the previous day's close.

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F11 | 74 | 25 | 49 | **+493.4** | -15.0 | 16 | +280.0 | +213.4 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 01:50 | BUY | 13384.0 | emerging trend up | Mon 26 Oct 05:50 | -15.0 |
| Mon 26 Oct 06:05 | SELL | 13371.1 | trend down, slow grind | Tue 27 Oct 07:05 | +50.0 |
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Wed 28 Oct 04:15 | +50.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 16:30 | -15.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Wed 28 Oct 04:20 | +50.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Wed 28 Oct 04:15 | +50.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 07:10 | +50.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Wed 28 Oct 16:50 | -15.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -15.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 16:10 | -15.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 13:30 | -15.0 |
| Wed 28 Oct 16:50 | BUY | 13313.2 | trend up, slow grind | Wed 28 Oct 17:50 | -15.0 |
| Thu 29 Oct 05:05 | SELL | 13318.6 | trend down, slow grind | Thu 29 Oct 12:30 | -15.0 |
| Thu 29 Oct 05:25 | SELL | 13316.5 | trend down, slow grind | Thu 29 Oct 11:20 | -15.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:25 | -15.0 |
| Thu 29 Oct 13:15 | SELL | 13314.2 | emerging trend down | Thu 29 Oct 13:35 | -15.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Fri 30 Oct 14:05 | -15.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:45 | -15.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 13:00 | -15.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:50 | -15.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:35 | -15.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Wed 04 Nov 01:15 | +50.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:50 | -15.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:45 | -15.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 18:35 | -15.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 16:05 | -15.0 |
| Mon 02 Nov 23:45 | BUY | 13406.0 | emerging trend up | Wed 04 Nov 01:20 | +50.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -15.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 04:05 | -15.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Wed 04 Nov 01:25 | +50.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 10:05 | -15.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:25 | -15.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Wed 04 Nov 01:30 | +50.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:50 | -15.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:25 | -15.0 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -15.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -15.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -15.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -15.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -15.0 |
| Thu 05 Nov 08:00 | SELL | 13469.9 | trend down, strong push | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:40 | -15.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -15.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:30 | +50.0 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 14:05 | +50.0 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 14:15 | +50.0 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 14:15 | +50.0 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 12:20 | -15.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:25 | -15.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 11:15 | -15.0 |
| Fri 06 Nov 13:30 | SELL | 13383.9 | trend down, slow grind | Fri 06 Nov 13:30 | -15.0 |
| Fri 06 Nov 13:45 | SELL | 13366.7 | trend down, slow grind | Fri 06 Nov 20:30 | +15.3 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F12. +486.4 pips, 1 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend and emerging trend; direction: the direction rule; hours: any time; news: as the bounce; stop: 15; take profit: 50; protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.


| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F12 | 65 | 27 | 38 | **+486.4** | -15.0 | 12 | +305.0 | +181.4 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Wed 28 Oct 04:15 | +50.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 16:30 | -15.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Wed 28 Oct 04:20 | +50.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Wed 28 Oct 04:15 | +50.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 07:10 | +50.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Wed 28 Oct 16:50 | -15.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -15.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 16:10 | -15.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 13:30 | -15.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:25 | -15.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Fri 30 Oct 14:05 | -15.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:45 | -15.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 13:00 | -15.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:50 | -15.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:35 | -15.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Wed 04 Nov 01:15 | +50.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:50 | -15.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:45 | -15.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 18:35 | -15.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 16:05 | -15.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -15.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 04:05 | -15.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Wed 04 Nov 01:25 | +50.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 10:05 | -15.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:25 | -15.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Wed 04 Nov 01:30 | +50.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:50 | -15.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:25 | -15.0 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -15.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -15.0 |
| Wed 04 Nov 00:15 | BUY | 13432.8 | trend up, strong push | Wed 04 Nov 08:40 | +50.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -15.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -15.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -15.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:40 | -15.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -15.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 13:15 | +8.3 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 13:15 | +7.4 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 12:20 | -15.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:25 | -15.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 11:15 | -15.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F13. +483.4 pips, 1 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: emerging trend, or trend of type slow grind; direction: the direction rule; hours: any time; news: as the EMA pullback; stop: 15; take profit: 50; protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.


| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F13 | 66 | 23 | 43 | **+483.4** | -15.0 | 13 | +305.0 | +178.4 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Wed 28 Oct 04:15 | +50.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 16:30 | -15.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Wed 28 Oct 04:20 | +50.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Wed 28 Oct 04:15 | +50.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 07:10 | +50.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Wed 28 Oct 16:50 | -15.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -15.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 16:10 | -15.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 13:30 | -15.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:25 | -15.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Fri 30 Oct 14:05 | -15.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:45 | -15.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 13:00 | -15.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:50 | -15.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:35 | -15.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Wed 04 Nov 01:15 | +50.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:50 | -15.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:45 | -15.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 18:35 | -15.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 16:05 | -15.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -15.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 04:05 | -15.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Wed 04 Nov 01:25 | +50.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 10:05 | -15.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:25 | -15.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Wed 04 Nov 01:30 | +50.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:50 | -15.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:25 | -15.0 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -15.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -15.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -15.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -15.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -15.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:40 | -15.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -15.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:30 | +50.0 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 14:05 | +50.0 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 14:15 | +50.0 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 14:15 | +50.0 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 12:20 | -15.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:25 | -15.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 11:15 | -15.0 |
| Fri 06 Nov 13:30 | SELL | 13383.9 | trend down, slow grind | Fri 06 Nov 13:30 | -15.0 |
| Fri 06 Nov 13:45 | SELL | 13366.7 | trend down, slow grind | Fri 06 Nov 20:30 | +15.3 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F14. +481.5 pips, 1 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend only; direction: the direction rule; hours: any time; news: as the EMA pullback; stop: 15; take profit: 30 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.


| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F14 | 40 | 19 | 21 | **+481.5** | -15.0 | 9 | +180.0 | +301.5 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Mon 26 Oct 13:55 | +30.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 07:00 | +30.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Tue 27 Oct 09:20 | +30.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Tue 27 Oct 09:25 | +30.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 01:00 | +30.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 01:00 | +30.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Wed 28 Oct 06:50 | +30.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Wed 28 Oct 07:10 | +30.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -15.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 16:10 | -15.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 13:30 | -15.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Fri 30 Oct 09:10 | +30.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 13:00 | -15.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:50 | -15.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:35 | -15.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 09:00 | +30.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:45 | -15.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -15.0 |
| Wed 04 Nov 00:15 | BUY | 13432.8 | trend up, strong push | Wed 04 Nov 01:30 | +30.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 01:35 | +30.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -15.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -15.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 12:00 | -15.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | -15.0 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 20:30 | +80.1 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 20:30 | +53.6 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 20:30 | +44.2 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 20:30 | +43.3 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 12:20 | -15.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:25 | -15.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 11:15 | -15.0 |
| Fri 06 Nov 13:30 | SELL | 13383.9 | trend down, slow grind | Fri 06 Nov 13:30 | -15.0 |
| Fri 06 Nov 13:45 | SELL | 13366.7 | trend down, slow grind | Fri 06 Nov 20:30 | +15.3 |

#### F15. +475.9 pips, 2 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend and emerging trend; hours: any time; news: as the bounce; stop: 15; take profit: 50; protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.
Any of: direction: the day's 00:00 UK open / the previous day's close.

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F15 | 72 | 29 | 43 | **+475.9** | -15.0 | 16 | +280.0 | +195.9 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 01:50 | BUY | 13384.0 | emerging trend up | Mon 26 Oct 05:50 | -15.0 |
| Mon 26 Oct 06:05 | SELL | 13371.1 | trend down, slow grind | Tue 27 Oct 07:05 | +50.0 |
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Wed 28 Oct 04:15 | +50.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 16:30 | -15.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Wed 28 Oct 04:20 | +50.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Wed 28 Oct 04:15 | +50.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 07:10 | +50.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Wed 28 Oct 16:50 | -15.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -15.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 16:10 | -15.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 13:30 | -15.0 |
| Wed 28 Oct 16:50 | BUY | 13313.2 | trend up, slow grind | Wed 28 Oct 17:50 | -15.0 |
| Thu 29 Oct 05:05 | SELL | 13318.6 | trend down, slow grind | Thu 29 Oct 12:30 | -15.0 |
| Thu 29 Oct 05:25 | SELL | 13316.5 | trend down, slow grind | Thu 29 Oct 11:20 | -15.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:25 | -15.0 |
| Thu 29 Oct 13:15 | SELL | 13314.2 | emerging trend down | Thu 29 Oct 13:35 | -15.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Fri 30 Oct 14:05 | -15.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:45 | -15.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 13:00 | -15.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:50 | -15.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:35 | -15.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Wed 04 Nov 01:15 | +50.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:50 | -15.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:45 | -15.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 18:35 | -15.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 16:05 | -15.0 |
| Mon 02 Nov 23:45 | BUY | 13406.0 | emerging trend up | Wed 04 Nov 01:20 | +50.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -15.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 04:05 | -15.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Wed 04 Nov 01:25 | +50.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 10:05 | -15.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:25 | -15.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Wed 04 Nov 01:30 | +50.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:50 | -15.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:25 | -15.0 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -15.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -15.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -15.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -15.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -15.0 |
| Thu 05 Nov 08:00 | SELL | 13469.9 | trend down, strong push | Thu 05 Nov 11:45 | +14.5 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:40 | -15.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -15.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 13:15 | +8.3 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 13:15 | +7.4 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 12:20 | -15.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:25 | -15.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 11:15 | -15.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F16. +475.5 pips, 1 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: emerging trend, or trend of type slow grind; direction: the direction rule; hours: any time; news: as the bounce; stop: 15; take profit: 50 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.


| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F16 | 64 | 26 | 38 | **+475.5** | -15.0 | 12 | +305.0 | +170.5 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Wed 28 Oct 04:15 | +50.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 16:30 | -15.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Wed 28 Oct 04:20 | +50.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Wed 28 Oct 04:15 | +50.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 07:10 | +50.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Wed 28 Oct 16:50 | -15.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -15.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 16:10 | -15.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 13:30 | -15.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:25 | -15.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Fri 30 Oct 14:05 | -15.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:45 | -15.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 13:00 | -15.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:50 | -15.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:35 | -15.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Wed 04 Nov 01:15 | +50.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:50 | -15.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:45 | -15.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 18:35 | -15.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 16:05 | -15.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -15.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 04:05 | -15.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Wed 04 Nov 01:25 | +50.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 10:05 | -15.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:25 | -15.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Wed 04 Nov 01:30 | +50.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:50 | -15.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:25 | -15.0 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -15.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -15.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -15.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -15.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -15.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:40 | -15.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -15.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 13:15 | +61.8 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 13:15 | +58.9 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 13:15 | +8.3 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 13:15 | +7.4 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 12:20 | -15.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:25 | -15.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 11:15 | -15.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F17. +465.5 pips, 1 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: emerging trend, or trend of type slow grind; direction: the direction rule; hours: any time; news: as the bounce; stop: 15; take profit: 30 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.


| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F17 | 64 | 32 | 32 | **+465.5** | -15.0 | 5 | +330.0 | +135.5 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Mon 26 Oct 13:55 | +30.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 07:00 | +30.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Tue 27 Oct 09:20 | +30.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Tue 27 Oct 09:25 | +30.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 16:30 | -15.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Tue 27 Oct 09:25 | +30.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Tue 27 Oct 09:20 | +30.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Tue 27 Oct 09:25 | +30.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 01:00 | +30.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 01:00 | +30.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 04:10 | +30.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 06:30 | +30.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Wed 28 Oct 06:50 | +30.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Wed 28 Oct 07:10 | +30.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -15.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 16:10 | -15.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 13:30 | -15.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:25 | -15.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Fri 30 Oct 09:10 | +30.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 10:10 | +30.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 13:00 | -15.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:50 | -15.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:35 | -15.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Mon 02 Nov 08:45 | +30.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 09:00 | +30.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:45 | -15.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 18:35 | -15.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 16:05 | -15.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -15.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 04:05 | -15.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Wed 04 Nov 01:00 | +30.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 10:05 | -15.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:25 | -15.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Wed 04 Nov 01:00 | +30.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:50 | -15.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:25 | -15.0 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -15.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -15.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 01:35 | +30.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -15.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -15.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -15.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:40 | -15.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -15.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 13:15 | +61.8 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 13:15 | +58.9 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 13:15 | +8.3 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 13:15 | +7.4 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 12:20 | -15.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:25 | -15.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 11:15 | -15.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F18. +465.0 pips, 2 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend and emerging trend; hours: any time; news: as the bounce; stop: 15; take profit: 30 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.
Any of: direction: the day's 00:00 UK open / the previous day's close.

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F18 | 72 | 35 | 37 | **+465.0** | -15.0 | 8 | +285.0 | +180.0 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 01:50 | BUY | 13384.0 | emerging trend up | Mon 26 Oct 05:50 | -15.0 |
| Mon 26 Oct 06:05 | SELL | 13371.1 | trend down, slow grind | Mon 26 Oct 13:20 | +30.0 |
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Mon 26 Oct 13:55 | +30.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 07:00 | +30.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Tue 27 Oct 09:20 | +30.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Tue 27 Oct 09:25 | +30.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 16:30 | -15.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Tue 27 Oct 09:25 | +30.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Tue 27 Oct 09:20 | +30.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Tue 27 Oct 09:25 | +30.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 01:00 | +30.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 01:00 | +30.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 04:10 | +30.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 06:30 | +30.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Wed 28 Oct 06:50 | +30.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Wed 28 Oct 07:10 | +30.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -15.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 16:10 | -15.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 13:30 | -15.0 |
| Wed 28 Oct 16:50 | BUY | 13313.2 | trend up, slow grind | Wed 28 Oct 17:50 | -15.0 |
| Thu 29 Oct 05:05 | SELL | 13318.6 | trend down, slow grind | Thu 29 Oct 12:30 | -15.0 |
| Thu 29 Oct 05:25 | SELL | 13316.5 | trend down, slow grind | Thu 29 Oct 11:20 | -15.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:25 | -15.0 |
| Thu 29 Oct 13:15 | SELL | 13314.2 | emerging trend down | Thu 29 Oct 13:35 | -15.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Fri 30 Oct 09:10 | +30.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 10:10 | +30.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 13:00 | -15.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:50 | -15.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:35 | -15.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Mon 02 Nov 08:45 | +30.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 09:00 | +30.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:45 | -15.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 18:35 | -15.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 16:05 | -15.0 |
| Mon 02 Nov 23:45 | BUY | 13406.0 | emerging trend up | Wed 04 Nov 00:15 | +30.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -15.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 04:05 | -15.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Wed 04 Nov 01:00 | +30.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 10:05 | -15.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:25 | -15.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Wed 04 Nov 01:00 | +30.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:50 | -15.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:25 | -15.0 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -15.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -15.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 01:35 | +30.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -15.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -15.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -15.0 |
| Thu 05 Nov 08:00 | SELL | 13469.9 | trend down, strong push | Thu 05 Nov 11:45 | +14.5 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:40 | -15.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -15.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 13:15 | +61.8 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 13:15 | +58.9 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 13:15 | +8.3 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 13:15 | +7.4 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 12:20 | -15.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:25 | -15.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 11:15 | -15.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F19. +450.5 pips, 2 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: emerging trend, or trend of type slow grind; hours: any time; news: as the bounce; stop: 15; take profit: 30 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.
Any of: direction: the day's 00:00 UK open / the previous day's close.

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F19 | 71 | 34 | 37 | **+450.5** | -15.0 | 8 | +285.0 | +165.5 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 01:50 | BUY | 13384.0 | emerging trend up | Mon 26 Oct 05:50 | -15.0 |
| Mon 26 Oct 06:05 | SELL | 13371.1 | trend down, slow grind | Mon 26 Oct 13:20 | +30.0 |
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Mon 26 Oct 13:55 | +30.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 07:00 | +30.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Tue 27 Oct 09:20 | +30.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Tue 27 Oct 09:25 | +30.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 16:30 | -15.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Tue 27 Oct 09:25 | +30.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Tue 27 Oct 09:20 | +30.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Tue 27 Oct 09:25 | +30.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 01:00 | +30.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 01:00 | +30.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 04:10 | +30.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 06:30 | +30.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Wed 28 Oct 06:50 | +30.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Wed 28 Oct 07:10 | +30.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -15.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 16:10 | -15.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 13:30 | -15.0 |
| Wed 28 Oct 16:50 | BUY | 13313.2 | trend up, slow grind | Wed 28 Oct 17:50 | -15.0 |
| Thu 29 Oct 05:05 | SELL | 13318.6 | trend down, slow grind | Thu 29 Oct 12:30 | -15.0 |
| Thu 29 Oct 05:25 | SELL | 13316.5 | trend down, slow grind | Thu 29 Oct 11:20 | -15.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:25 | -15.0 |
| Thu 29 Oct 13:15 | SELL | 13314.2 | emerging trend down | Thu 29 Oct 13:35 | -15.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Fri 30 Oct 09:10 | +30.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 10:10 | +30.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 13:00 | -15.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:50 | -15.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:35 | -15.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Mon 02 Nov 08:45 | +30.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 09:00 | +30.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:45 | -15.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 18:35 | -15.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 16:05 | -15.0 |
| Mon 02 Nov 23:45 | BUY | 13406.0 | emerging trend up | Wed 04 Nov 00:15 | +30.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -15.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 04:05 | -15.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Wed 04 Nov 01:00 | +30.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 10:05 | -15.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:25 | -15.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Wed 04 Nov 01:00 | +30.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:50 | -15.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:25 | -15.0 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -15.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -15.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 01:35 | +30.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -15.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -15.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -15.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:40 | -15.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -15.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 13:15 | +61.8 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 13:15 | +58.9 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 13:15 | +8.3 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 13:15 | +7.4 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 12:20 | -15.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:25 | -15.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 11:15 | -15.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F20. +436.4 pips, 1 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: emerging trend, or trend of type slow grind; direction: the direction rule; hours: any time; news: as the bounce; stop: 15; take profit: 50; protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.


| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F20 | 64 | 26 | 38 | **+436.4** | -15.0 | 12 | +305.0 | +131.4 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Wed 28 Oct 04:15 | +50.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 16:30 | -15.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Wed 28 Oct 04:20 | +50.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Wed 28 Oct 04:15 | +50.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 07:10 | +50.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Wed 28 Oct 16:50 | -15.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -15.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 16:10 | -15.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 13:30 | -15.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:25 | -15.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Fri 30 Oct 14:05 | -15.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:45 | -15.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 13:00 | -15.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:50 | -15.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:35 | -15.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Wed 04 Nov 01:15 | +50.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:50 | -15.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:45 | -15.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 18:35 | -15.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 16:05 | -15.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -15.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 04:05 | -15.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Wed 04 Nov 01:25 | +50.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 10:05 | -15.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:25 | -15.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Wed 04 Nov 01:30 | +50.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:50 | -15.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:25 | -15.0 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -15.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -15.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -15.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -15.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -15.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:40 | -15.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -15.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 13:15 | +8.3 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 13:15 | +7.4 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 12:20 | -15.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:25 | -15.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 11:15 | -15.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F21. +433.2 pips, 1 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend and emerging trend; direction: the direction rule; hours: any time; news: as the bounce; stop: 10; take profit: 50 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.


| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F21 | 65 | 21 | 44 | **+433.2** | -11.6 | 14 | +250.0 | +183.2 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Mon 26 Oct 11:40 | -10.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Mon 26 Oct 11:40 | -10.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 14:45 | -10.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Wed 28 Oct 04:20 | +50.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Wed 28 Oct 04:15 | +50.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 07:10 | +50.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 18:35 | -10.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Tue 27 Oct 17:20 | -10.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Tue 27 Oct 21:00 | -10.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -10.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 13:40 | -10.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 11:45 | -10.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:10 | -10.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Thu 29 Oct 23:35 | -10.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:25 | -10.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 12:50 | -10.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:40 | -10.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:00 | -10.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Wed 04 Nov 01:15 | +50.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:35 | -10.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:30 | -10.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 14:10 | -10.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 15:35 | -10.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -10.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 03:40 | -10.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Tue 03 Nov 11:25 | -10.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 08:45 | -10.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 12:10 | -10.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Tue 03 Nov 12:30 | -10.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:45 | -10.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:00 | -11.6 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -10.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -10.0 |
| Wed 04 Nov 00:15 | BUY | 13432.8 | trend up, strong push | Wed 04 Nov 08:40 | +50.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -10.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 10:40 | -10.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:30 | -10.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:30 | -10.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -10.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:35 | -10.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:20 | -10.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:15 | -10.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -10.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 13:15 | +61.8 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 13:15 | +58.9 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 12:20 | -10.0 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 12:20 | -10.0 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 11:15 | -10.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 10:55 | -10.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 10:50 | -10.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F22. +401.2 pips, 1 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend and emerging trend; direction: the direction rule; hours: any time; news: as the bounce; stop: 8; take profit: 50 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.


| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F22 | 65 | 19 | 46 | **+401.2** | -11.6 | 28 | +222.0 | +179.2 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Mon 26 Oct 11:00 | -8.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Mon 26 Oct 11:00 | -8.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 14:45 | -8.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Wed 28 Oct 04:20 | +50.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Wed 28 Oct 04:15 | +50.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Tue 27 Oct 12:20 | -8.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 16:50 | -8.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Tue 27 Oct 17:00 | -8.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Tue 27 Oct 21:00 | -8.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -8.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 13:40 | -8.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 10:35 | -8.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:00 | -8.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Thu 29 Oct 23:30 | -8.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:00 | -8.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 12:45 | -8.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:40 | -8.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 10:40 | -8.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Tue 03 Nov 02:20 | -8.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:30 | -8.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:25 | -8.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 11:55 | -8.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 15:30 | -8.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -8.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 03:30 | -8.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Tue 03 Nov 06:45 | -8.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 08:35 | -8.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 12:05 | -8.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Tue 03 Nov 12:30 | -8.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:45 | -8.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:00 | -11.6 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -8.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -8.0 |
| Wed 04 Nov 00:15 | BUY | 13432.8 | trend up, strong push | Wed 04 Nov 08:40 | +50.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -8.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 08:35 | -8.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 09:30 | -8.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:30 | -8.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:25 | -8.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:30 | -8.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:15 | -8.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:10 | -8.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -8.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 13:15 | +61.8 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 13:15 | +58.9 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 11:40 | -8.0 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 11:40 | -8.0 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 11:05 | -8.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 10:50 | -8.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 10:40 | -8.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F23. +394.1 pips, 1 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend and emerging trend; direction: the direction rule; hours: any time; news: as the bounce; stop: 10; take profit: 50; protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.


| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F23 | 65 | 21 | 44 | **+394.1** | -11.6 | 14 | +250.0 | +144.1 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Mon 26 Oct 11:40 | -10.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Mon 26 Oct 11:40 | -10.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 14:45 | -10.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Wed 28 Oct 04:20 | +50.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Wed 28 Oct 04:15 | +50.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 07:10 | +50.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 18:35 | -10.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Tue 27 Oct 17:20 | -10.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Tue 27 Oct 21:00 | -10.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -10.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 13:40 | -10.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 11:45 | -10.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:10 | -10.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Thu 29 Oct 23:35 | -10.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:25 | -10.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 12:50 | -10.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:40 | -10.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:00 | -10.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Wed 04 Nov 01:15 | +50.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:35 | -10.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:30 | -10.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 14:10 | -10.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 15:35 | -10.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -10.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 03:40 | -10.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Tue 03 Nov 11:25 | -10.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 08:45 | -10.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 12:10 | -10.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Tue 03 Nov 12:30 | -10.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:45 | -10.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:00 | -11.6 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -10.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -10.0 |
| Wed 04 Nov 00:15 | BUY | 13432.8 | trend up, strong push | Wed 04 Nov 08:40 | +50.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -10.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 10:40 | -10.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:30 | -10.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:30 | -10.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -10.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:35 | -10.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:20 | -10.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:15 | -10.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -10.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 12:20 | -10.0 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 12:20 | -10.0 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 11:15 | -10.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 10:55 | -10.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 10:50 | -10.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F24. +394.1 pips, 1 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend only; direction: the direction rule; hours: any time; news: as the EMA pullback; stop: 6; take profit: 50 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.


| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F24 | 40 | 9 | 31 | **+394.1** | -6.0 | 12 | +134.0 | +260.1 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Mon 26 Oct 10:25 | -6.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Mon 26 Oct 10:25 | -6.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Tue 27 Oct 17:00 | -6.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Tue 27 Oct 20:55 | -6.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -6.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 13:30 | -6.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 10:30 | -6.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Thu 29 Oct 23:10 | -6.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 12:40 | -6.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 09:00 | -6.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 10:40 | -6.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:25 | -6.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:25 | -6.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -6.0 |
| Wed 04 Nov 00:15 | BUY | 13432.8 | trend up, strong push | Wed 04 Nov 08:40 | +50.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 08:35 | -6.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 09:20 | -6.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:30 | -6.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:25 | -6.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 12:00 | -6.0 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 12:00 | -6.0 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 12:00 | -6.0 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 12:00 | -6.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:05 | -6.0 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 20:30 | +80.1 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 08:15 | -6.0 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 08:45 | -6.0 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 11:20 | -6.0 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 10:50 | -6.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 10:40 | -6.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 10:35 | -6.0 |
| Fri 06 Nov 13:30 | SELL | 13383.9 | trend down, slow grind | Fri 06 Nov 13:30 | -6.0 |
| Fri 06 Nov 13:45 | SELL | 13366.7 | trend down, slow grind | Fri 06 Nov 13:50 | -6.0 |

#### F25. +393.7 pips, 1 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend only; direction: the direction rule; hours: any time; news: as the EMA pullback; stop: 8; take profit: 50 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.


| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F25 | 40 | 10 | 30 | **+393.7** | -8.0 | 12 | +112.0 | +281.7 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Mon 26 Oct 11:00 | -8.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Mon 26 Oct 11:00 | -8.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Tue 27 Oct 17:00 | -8.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Tue 27 Oct 21:00 | -8.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -8.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 13:40 | -8.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 10:35 | -8.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Thu 29 Oct 23:30 | -8.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 12:45 | -8.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:40 | -8.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 10:40 | -8.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:30 | -8.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:25 | -8.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -8.0 |
| Wed 04 Nov 00:15 | BUY | 13432.8 | trend up, strong push | Wed 04 Nov 08:40 | +50.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 08:35 | -8.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 09:30 | -8.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:30 | -8.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:25 | -8.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 12:00 | -8.0 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 12:00 | -8.0 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 12:00 | -8.0 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 12:00 | -8.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:10 | -8.0 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 20:30 | +80.1 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 20:30 | +53.6 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 11:40 | -8.0 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 11:40 | -8.0 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 11:05 | -8.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 10:50 | -8.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 10:40 | -8.0 |
| Fri 06 Nov 13:30 | SELL | 13383.9 | trend down, slow grind | Fri 06 Nov 13:30 | -8.0 |
| Fri 06 Nov 13:45 | SELL | 13366.7 | trend down, slow grind | Fri 06 Nov 13:50 | -8.0 |

#### F26. +390.5 pips, 1 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend and emerging trend; direction: the direction rule; hours: any time; news: as the bounce; stop: 15; take profit: 20 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.


| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F26 | 65 | 36 | 29 | **+390.5** | -15.0 | 5 | +250.0 | +140.5 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Mon 26 Oct 13:20 | +20.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Mon 26 Oct 13:55 | +20.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Tue 27 Oct 07:00 | +20.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Tue 27 Oct 07:00 | +20.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 16:30 | -15.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Tue 27 Oct 07:00 | +20.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Tue 27 Oct 07:00 | +20.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Tue 27 Oct 07:00 | +20.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Tue 27 Oct 09:30 | +20.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Tue 27 Oct 09:30 | +20.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Tue 27 Oct 16:15 | +20.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 05:20 | +20.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Wed 28 Oct 05:30 | +20.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Wed 28 Oct 06:30 | +20.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -15.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 07:15 | +20.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 13:30 | -15.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:25 | -15.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Fri 30 Oct 07:20 | +20.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 09:15 | +20.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 11:05 | +20.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:50 | -15.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:35 | -15.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Mon 02 Nov 08:35 | +20.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 08:45 | +20.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 08:50 | +20.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 18:35 | -15.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 16:05 | -15.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -15.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 04:05 | -15.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Tue 03 Nov 23:55 | +20.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 10:05 | -15.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:25 | -15.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Wed 04 Nov 00:15 | +20.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:50 | -15.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:25 | -15.0 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -15.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -15.0 |
| Wed 04 Nov 00:15 | BUY | 13432.8 | trend up, strong push | Wed 04 Nov 01:15 | +20.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 01:25 | +20.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -15.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -15.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -15.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:40 | -15.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -15.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 13:15 | +61.8 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 13:15 | +58.9 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 13:15 | +8.3 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 13:15 | +7.4 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 12:20 | -15.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:25 | -15.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 11:15 | -15.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F27. +385.3 pips, 1 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend and emerging trend; direction: the direction rule; hours: any time; news: as the bounce; stop: 12; take profit: 50 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.


| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F27 | 65 | 23 | 42 | **+385.3** | -13.9 | 14 | +218.7 | +166.6 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Mon 26 Oct 12:50 | -12.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Mon 26 Oct 12:50 | -12.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 15:20 | -12.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Wed 28 Oct 04:20 | +50.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Wed 28 Oct 04:15 | +50.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 07:10 | +50.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 18:35 | -12.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Wed 28 Oct 18:35 | -12.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Tue 27 Oct 21:25 | -13.3 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -12.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 16:05 | -12.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 12:05 | -12.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:10 | -12.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Thu 29 Oct 23:45 | -12.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:40 | -12.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 12:50 | -12.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:45 | -12.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:35 | -12.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Wed 04 Nov 01:15 | +50.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:40 | -12.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:35 | -12.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 14:10 | -12.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 15:35 | -12.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -12.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 03:50 | -12.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Tue 03 Nov 11:25 | -12.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 09:15 | -12.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:10 | -12.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Tue 03 Nov 12:40 | -12.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:50 | -12.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:20 | -13.9 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -12.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -12.0 |
| Wed 04 Nov 00:15 | BUY | 13432.8 | trend up, strong push | Wed 04 Nov 08:40 | +50.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -12.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -12.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:30 | -12.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:30 | -12.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -12.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:40 | -12.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:20 | -12.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:20 | -12.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -12.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 13:15 | +61.8 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 13:15 | +58.9 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 13:15 | +8.3 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 13:15 | +7.4 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 11:25 | -12.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:10 | -12.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 10:55 | -12.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F28. +385.0 pips, 2 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend and emerging trend; hours: any time; news: as the bounce; stop: 15; take profit: 20 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.
Any of: direction: the day's 00:00 UK open / the previous day's close.

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F28 | 72 | 39 | 33 | **+385.0** | -15.0 | 5 | +230.0 | +155.0 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 01:50 | BUY | 13384.0 | emerging trend up | Mon 26 Oct 05:50 | -15.0 |
| Mon 26 Oct 06:05 | SELL | 13371.1 | trend down, slow grind | Mon 26 Oct 08:35 | +20.0 |
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Mon 26 Oct 13:20 | +20.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Mon 26 Oct 13:55 | +20.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Tue 27 Oct 07:00 | +20.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Tue 27 Oct 07:00 | +20.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 16:30 | -15.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Tue 27 Oct 07:00 | +20.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Tue 27 Oct 07:00 | +20.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Tue 27 Oct 07:00 | +20.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Tue 27 Oct 09:30 | +20.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Tue 27 Oct 09:30 | +20.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Tue 27 Oct 16:15 | +20.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 05:20 | +20.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Wed 28 Oct 05:30 | +20.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Wed 28 Oct 06:30 | +20.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -15.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 07:15 | +20.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 13:30 | -15.0 |
| Wed 28 Oct 16:50 | BUY | 13313.2 | trend up, slow grind | Wed 28 Oct 17:50 | -15.0 |
| Thu 29 Oct 05:05 | SELL | 13318.6 | trend down, slow grind | Thu 29 Oct 09:20 | +20.0 |
| Thu 29 Oct 05:25 | SELL | 13316.5 | trend down, slow grind | Thu 29 Oct 11:20 | -15.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:25 | -15.0 |
| Thu 29 Oct 13:15 | SELL | 13314.2 | emerging trend down | Thu 29 Oct 13:35 | -15.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Fri 30 Oct 07:20 | +20.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 09:15 | +20.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 11:05 | +20.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:50 | -15.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:35 | -15.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Mon 02 Nov 08:35 | +20.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 08:45 | +20.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 08:50 | +20.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 18:35 | -15.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 16:05 | -15.0 |
| Mon 02 Nov 23:45 | BUY | 13406.0 | emerging trend up | Tue 03 Nov 13:30 | +20.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -15.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 04:05 | -15.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Tue 03 Nov 23:55 | +20.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 10:05 | -15.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:25 | -15.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Wed 04 Nov 00:15 | +20.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:50 | -15.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:25 | -15.0 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -15.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -15.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 01:25 | +20.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -15.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -15.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -15.0 |
| Thu 05 Nov 08:00 | SELL | 13469.9 | trend down, strong push | Thu 05 Nov 11:45 | +14.5 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:40 | -15.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -15.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 13:15 | +61.8 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 13:15 | +58.9 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 13:15 | +8.3 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 13:15 | +7.4 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 12:20 | -15.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:25 | -15.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 11:15 | -15.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F29. +383.2 pips, 1 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: emerging trend, or trend of type slow grind; direction: the direction rule; hours: any time; news: as the bounce; stop: 10; take profit: 50 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.


| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F29 | 64 | 20 | 44 | **+383.2** | -11.6 | 14 | +250.0 | +133.2 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Mon 26 Oct 11:40 | -10.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Mon 26 Oct 11:40 | -10.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 14:45 | -10.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Wed 28 Oct 04:20 | +50.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Wed 28 Oct 04:15 | +50.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 07:10 | +50.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 18:35 | -10.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Tue 27 Oct 17:20 | -10.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Tue 27 Oct 21:00 | -10.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -10.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 13:40 | -10.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 11:45 | -10.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:10 | -10.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Thu 29 Oct 23:35 | -10.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:25 | -10.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 12:50 | -10.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:40 | -10.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:00 | -10.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Wed 04 Nov 01:15 | +50.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:35 | -10.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:30 | -10.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 14:10 | -10.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 15:35 | -10.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -10.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 03:40 | -10.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Tue 03 Nov 11:25 | -10.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 08:45 | -10.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 12:10 | -10.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Tue 03 Nov 12:30 | -10.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:45 | -10.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:00 | -11.6 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -10.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -10.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -10.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 10:40 | -10.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:30 | -10.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:30 | -10.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -10.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:35 | -10.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:20 | -10.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:15 | -10.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -10.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 13:15 | +61.8 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 13:15 | +58.9 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 12:20 | -10.0 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 12:20 | -10.0 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 11:15 | -10.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 10:55 | -10.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 10:50 | -10.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F30. +382.3 pips, 2 combination(s) with this result

Shared: entry: pause 3, the pause's lowest point; EMA pullback open: regardless; states: emerging trend, or trend of type slow grind; hours: any time; news: as the bounce; stop: 8; take profit: 30 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.
Any of: direction: the day's 00:00 UK open / the previous day's close.

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F30 | 48 | 18 | 30 | **+382.3** | -8.0 | 6 | +106.0 | +276.3 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 01:50 | BUY | 13384.0 | emerging trend up | Mon 26 Oct 05:20 | -8.0 |
| Mon 26 Oct 06:10 | SELL | 13369.9 | trend down, slow grind | Mon 26 Oct 13:25 | +30.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 07:00 | +30.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Mon 26 Oct 11:00 | -8.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Mon 26 Oct 11:00 | -8.0 |
| Mon 26 Oct 13:55 | SELL | 13336.3 | emerging trend down | Mon 26 Oct 14:30 | -8.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Tue 27 Oct 09:25 | +30.0 |
| Mon 26 Oct 20:00 | SELL | 13345.4 | emerging trend down | Tue 27 Oct 09:25 | +30.0 |
| Tue 27 Oct 06:00 | SELL | 13331.3 | trend down, slow grind | Wed 28 Oct 01:00 | +30.0 |
| Tue 27 Oct 09:10 | SELL | 13318.4 | emerging trend down | Tue 27 Oct 12:05 | -8.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 06:30 | +30.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -8.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 13:40 | -8.0 |
| Wed 28 Oct 16:50 | BUY | 13313.2 | trend up, slow grind | Wed 28 Oct 17:35 | -8.0 |
| Thu 29 Oct 05:30 | SELL | 13316.4 | trend down, slow grind | Thu 29 Oct 07:45 | -8.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:00 | -8.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Thu 29 Oct 23:30 | -8.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 10:10 | +30.0 |
| Fri 30 Oct 09:05 | BUY | 13416.6 | trend up, slow grind | Fri 30 Oct 12:40 | -8.0 |
| Fri 30 Oct 10:05 | BUY | 13431.2 | trend up, slow grind | Fri 30 Oct 10:40 | -8.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Mon 02 Nov 08:45 | +30.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 09:00 | +30.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:25 | -8.0 |
| Mon 02 Nov 11:45 | BUY | 13419.7 | emerging trend up | Mon 02 Nov 11:55 | -8.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 08:35 | -8.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 12:05 | -8.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -8.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 01:35 | +30.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -8.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 08:35 | -8.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 09:30 | -8.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:30 | -8.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:25 | -8.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:30 | SELL | 13454.4 | trend down, slow grind | Thu 05 Nov 11:45 | -1.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:10 | -8.0 |
| Thu 05 Nov 22:25 | SELL | 13440.5 | emerging trend down | Thu 05 Nov 22:25 | -8.0 |
| Fri 06 Nov 01:35 | SELL | 13448.6 | emerging trend down | Fri 06 Nov 13:15 | +61.3 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:20 | SELL | 13445.9 | trend down, slow grind | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 11:40 | -8.0 |
| Fri 06 Nov 09:20 | SELL | 13389.4 | trend down, slow grind | Fri 06 Nov 11:05 | -8.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 10:50 | -8.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F31. +378.1 pips, 1 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend only; direction: none; hours: any time; news: as the EMA pullback; stop: 6; take profit: 50 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.


| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F31 | 52 | 10 | 42 | **+378.1** | -6.0 | 19 | +148.0 | +230.1 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 06:05 | SELL | 13371.1 | trend down, slow grind | Tue 27 Oct 07:05 | +50.0 |
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Mon 26 Oct 10:25 | -6.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Mon 26 Oct 10:25 | -6.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Tue 27 Oct 17:00 | -6.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Tue 27 Oct 20:55 | -6.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -6.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 13:30 | -6.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 10:30 | -6.0 |
| Wed 28 Oct 15:30 | BUY | 13303.0 | trend up, slow grind | Wed 28 Oct 15:45 | -6.0 |
| Wed 28 Oct 16:50 | BUY | 13313.2 | trend up, slow grind | Wed 28 Oct 17:25 | -6.0 |
| Thu 29 Oct 05:05 | SELL | 13318.6 | trend down, slow grind | Thu 29 Oct 07:45 | -6.0 |
| Thu 29 Oct 05:25 | SELL | 13316.5 | trend down, slow grind | Thu 29 Oct 07:30 | -6.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Thu 29 Oct 23:10 | -6.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 12:40 | -6.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 09:00 | -6.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 10:40 | -6.0 |
| Fri 30 Oct 13:20 | SELL | 13394.0 | trend down, slow grind | Fri 30 Oct 16:00 | -6.0 |
| Fri 30 Oct 13:40 | SELL | 13391.0 | trend down, slow grind | Fri 30 Oct 14:40 | -6.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:25 | -6.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:25 | -6.0 |
| Mon 02 Nov 19:40 | SELL | 13409.5 | trend down, slow grind | Mon 02 Nov 20:00 | -6.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -6.0 |
| Wed 04 Nov 00:15 | BUY | 13432.8 | trend up, strong push | Wed 04 Nov 08:40 | +50.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 08:35 | -6.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 09:20 | -6.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:30 | -6.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:25 | -6.0 |
| Wed 04 Nov 15:35 | SELL | 13462.8 | trend down, strong push | Wed 04 Nov 15:40 | -6.0 |
| Wed 04 Nov 16:10 | SELL | 13464.3 | trend down, slow grind | Wed 04 Nov 17:10 | -6.0 |
| Wed 04 Nov 16:35 | SELL | 13461.2 | trend down, slow grind | Wed 04 Nov 17:05 | -6.0 |
| Thu 05 Nov 08:00 | SELL | 13469.9 | trend down, strong push | Thu 05 Nov 08:05 | -6.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 12:00 | -6.0 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 12:00 | -6.0 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 12:00 | -6.0 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 12:00 | -6.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:05 | -6.0 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 20:30 | +80.1 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 08:15 | -6.0 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 08:45 | -6.0 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 11:20 | -6.0 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 10:50 | -6.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 10:40 | -6.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 10:35 | -6.0 |
| Fri 06 Nov 13:30 | SELL | 13383.9 | trend down, slow grind | Fri 06 Nov 13:30 | -6.0 |
| Fri 06 Nov 13:45 | SELL | 13366.7 | trend down, slow grind | Fri 06 Nov 13:50 | -6.0 |

#### F32. +376.3 pips, 2 combination(s) with this result

Shared: entry: pause 3, the pause's lowest point; EMA pullback open: regardless; direction: the direction rule; hours: any time; news: as the bounce; stop: 8; take profit: 30 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.
Any of: states: emerging trend, or trend of type slow grind / trend and emerging trend.

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F32 | 44 | 17 | 27 | **+376.3** | -8.0 | 5 | +100.0 | +276.3 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 07:00 | +30.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Mon 26 Oct 11:00 | -8.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Mon 26 Oct 11:00 | -8.0 |
| Mon 26 Oct 13:55 | SELL | 13336.3 | emerging trend down | Mon 26 Oct 14:30 | -8.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Tue 27 Oct 09:25 | +30.0 |
| Mon 26 Oct 20:00 | SELL | 13345.4 | emerging trend down | Tue 27 Oct 09:25 | +30.0 |
| Tue 27 Oct 06:00 | SELL | 13331.3 | trend down, slow grind | Wed 28 Oct 01:00 | +30.0 |
| Tue 27 Oct 09:10 | SELL | 13318.4 | emerging trend down | Tue 27 Oct 12:05 | -8.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 06:30 | +30.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -8.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 13:40 | -8.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:00 | -8.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Thu 29 Oct 23:30 | -8.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 10:10 | +30.0 |
| Fri 30 Oct 09:05 | BUY | 13416.6 | trend up, slow grind | Fri 30 Oct 12:40 | -8.0 |
| Fri 30 Oct 10:05 | BUY | 13431.2 | trend up, slow grind | Fri 30 Oct 10:40 | -8.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Mon 02 Nov 08:45 | +30.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 09:00 | +30.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:25 | -8.0 |
| Mon 02 Nov 11:45 | BUY | 13419.7 | emerging trend up | Mon 02 Nov 11:55 | -8.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 08:35 | -8.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 12:05 | -8.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -8.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 01:35 | +30.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -8.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 08:35 | -8.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 09:30 | -8.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:30 | -8.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:25 | -8.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:30 | SELL | 13454.4 | trend down, slow grind | Thu 05 Nov 11:45 | -1.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:10 | -8.0 |
| Thu 05 Nov 22:25 | SELL | 13440.5 | emerging trend down | Thu 05 Nov 22:25 | -8.0 |
| Fri 06 Nov 01:35 | SELL | 13448.6 | emerging trend down | Fri 06 Nov 13:15 | +61.3 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:20 | SELL | 13445.9 | trend down, slow grind | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 11:40 | -8.0 |
| Fri 06 Nov 09:20 | SELL | 13389.4 | trend down, slow grind | Fri 06 Nov 11:05 | -8.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 10:50 | -8.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F33. +376.1 pips, 2 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend only, type slow grind; hours: any time; news: as the EMA pullback; stop: 6; take profit: 50 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.
Any of: direction: the day's 00:00 UK open / the previous day's close.

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F33 | 43 | 9 | 34 | **+376.1** | -6.0 | 15 | +166.0 | +210.1 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 06:05 | SELL | 13371.1 | trend down, slow grind | Tue 27 Oct 07:05 | +50.0 |
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Mon 26 Oct 10:25 | -6.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Mon 26 Oct 10:25 | -6.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Tue 27 Oct 17:00 | -6.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Tue 27 Oct 20:55 | -6.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -6.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 13:30 | -6.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 10:30 | -6.0 |
| Wed 28 Oct 16:50 | BUY | 13313.2 | trend up, slow grind | Wed 28 Oct 17:25 | -6.0 |
| Thu 29 Oct 05:05 | SELL | 13318.6 | trend down, slow grind | Thu 29 Oct 07:45 | -6.0 |
| Thu 29 Oct 05:25 | SELL | 13316.5 | trend down, slow grind | Thu 29 Oct 07:30 | -6.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Thu 29 Oct 23:10 | -6.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 12:40 | -6.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 09:00 | -6.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 10:40 | -6.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:25 | -6.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:25 | -6.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -6.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 08:35 | -6.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 09:20 | -6.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:30 | -6.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:25 | -6.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 12:00 | -6.0 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 12:00 | -6.0 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 12:00 | -6.0 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 12:00 | -6.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:05 | -6.0 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 20:30 | +80.1 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 08:15 | -6.0 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 08:45 | -6.0 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 11:20 | -6.0 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 10:50 | -6.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 10:40 | -6.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 10:35 | -6.0 |
| Fri 06 Nov 13:30 | SELL | 13383.9 | trend down, slow grind | Fri 06 Nov 13:30 | -6.0 |
| Fri 06 Nov 13:45 | SELL | 13366.7 | trend down, slow grind | Fri 06 Nov 13:50 | -6.0 |

#### F34. +375.3 pips, 2 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: emerging trend, or trend of type slow grind; hours: any time; news: as the bounce; stop: 12; take profit: 50 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.
Any of: direction: the day's 00:00 UK open / the previous day's close.

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F34 | 71 | 24 | 47 | **+375.3** | -13.9 | 16 | +208.7 | +166.6 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 01:50 | BUY | 13384.0 | emerging trend up | Mon 26 Oct 05:40 | -12.0 |
| Mon 26 Oct 06:05 | SELL | 13371.1 | trend down, slow grind | Tue 27 Oct 07:05 | +50.0 |
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Mon 26 Oct 12:50 | -12.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Mon 26 Oct 12:50 | -12.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 15:20 | -12.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Wed 28 Oct 04:20 | +50.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Wed 28 Oct 04:15 | +50.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 07:10 | +50.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 18:35 | -12.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Wed 28 Oct 18:35 | -12.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Tue 27 Oct 21:25 | -13.3 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -12.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 16:05 | -12.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 12:05 | -12.0 |
| Wed 28 Oct 16:50 | BUY | 13313.2 | trend up, slow grind | Wed 28 Oct 17:50 | -12.0 |
| Thu 29 Oct 05:05 | SELL | 13318.6 | trend down, slow grind | Thu 29 Oct 08:00 | -12.0 |
| Thu 29 Oct 05:25 | SELL | 13316.5 | trend down, slow grind | Thu 29 Oct 07:50 | -12.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:10 | -12.0 |
| Thu 29 Oct 13:15 | SELL | 13314.2 | emerging trend down | Thu 29 Oct 13:30 | -12.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Thu 29 Oct 23:45 | -12.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:40 | -12.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 12:50 | -12.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:45 | -12.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:35 | -12.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Wed 04 Nov 01:15 | +50.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:40 | -12.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:35 | -12.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 14:10 | -12.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 15:35 | -12.0 |
| Mon 02 Nov 23:45 | BUY | 13406.0 | emerging trend up | Wed 04 Nov 01:20 | +50.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -12.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 03:50 | -12.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Tue 03 Nov 11:25 | -12.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 09:15 | -12.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:10 | -12.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Tue 03 Nov 12:40 | -12.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:50 | -12.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:20 | -13.9 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -12.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -12.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -12.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -12.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:30 | -12.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:30 | -12.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -12.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:40 | -12.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:20 | -12.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:20 | -12.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -12.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 13:15 | +61.8 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 13:15 | +58.9 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 13:15 | +8.3 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 13:15 | +7.4 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 11:25 | -12.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:10 | -12.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 10:55 | -12.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F35. +374.3 pips, 2 combination(s) with this result

Shared: entry: pause 3, the pause's lowest point; EMA pullback open: regardless; states: trend and emerging trend; hours: any time; news: as the bounce; stop: 8; take profit: 30 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.
Any of: direction: the day's 00:00 UK open / the previous day's close.

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F35 | 49 | 18 | 31 | **+374.3** | -8.0 | 6 | +106.0 | +268.3 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 01:50 | BUY | 13384.0 | emerging trend up | Mon 26 Oct 05:20 | -8.0 |
| Mon 26 Oct 06:10 | SELL | 13369.9 | trend down, slow grind | Mon 26 Oct 13:25 | +30.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 07:00 | +30.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Mon 26 Oct 11:00 | -8.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Mon 26 Oct 11:00 | -8.0 |
| Mon 26 Oct 13:55 | SELL | 13336.3 | emerging trend down | Mon 26 Oct 14:30 | -8.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Tue 27 Oct 09:25 | +30.0 |
| Mon 26 Oct 20:00 | SELL | 13345.4 | emerging trend down | Tue 27 Oct 09:25 | +30.0 |
| Tue 27 Oct 06:00 | SELL | 13331.3 | trend down, slow grind | Wed 28 Oct 01:00 | +30.0 |
| Tue 27 Oct 09:10 | SELL | 13318.4 | emerging trend down | Tue 27 Oct 12:05 | -8.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 06:30 | +30.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -8.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 13:40 | -8.0 |
| Wed 28 Oct 16:50 | BUY | 13313.2 | trend up, slow grind | Wed 28 Oct 17:35 | -8.0 |
| Thu 29 Oct 05:30 | SELL | 13316.4 | trend down, slow grind | Thu 29 Oct 07:45 | -8.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:00 | -8.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Thu 29 Oct 23:30 | -8.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 10:10 | +30.0 |
| Fri 30 Oct 09:05 | BUY | 13416.6 | trend up, slow grind | Fri 30 Oct 12:40 | -8.0 |
| Fri 30 Oct 10:05 | BUY | 13431.2 | trend up, slow grind | Fri 30 Oct 10:40 | -8.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Mon 02 Nov 08:45 | +30.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 09:00 | +30.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:25 | -8.0 |
| Mon 02 Nov 11:45 | BUY | 13419.7 | emerging trend up | Mon 02 Nov 11:55 | -8.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 08:35 | -8.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 12:05 | -8.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -8.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 01:35 | +30.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -8.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 08:35 | -8.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 09:30 | -8.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:30 | -8.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:25 | -8.0 |
| Thu 05 Nov 08:00 | SELL | 13469.9 | trend down, strong push | Thu 05 Nov 08:10 | -8.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:30 | SELL | 13454.4 | trend down, slow grind | Thu 05 Nov 11:45 | -1.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:10 | -8.0 |
| Thu 05 Nov 22:25 | SELL | 13440.5 | emerging trend down | Thu 05 Nov 22:25 | -8.0 |
| Fri 06 Nov 01:35 | SELL | 13448.6 | emerging trend down | Fri 06 Nov 13:15 | +61.3 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:20 | SELL | 13445.9 | trend down, slow grind | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 11:40 | -8.0 |
| Fri 06 Nov 09:20 | SELL | 13389.4 | trend down, slow grind | Fri 06 Nov 11:05 | -8.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 10:50 | -8.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F36. +373.2 pips, 1 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend and emerging trend; direction: the direction rule; hours: any time; news: as the bounce; stop: 8; take profit: 30 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.


| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F36 | 65 | 23 | 42 | **+373.2** | -11.6 | 13 | +158.0 | +215.2 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Mon 26 Oct 13:55 | +30.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 07:00 | +30.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Mon 26 Oct 11:00 | -8.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Mon 26 Oct 11:00 | -8.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 14:45 | -8.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Tue 27 Oct 09:25 | +30.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Tue 27 Oct 09:20 | +30.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Tue 27 Oct 09:25 | +30.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 01:00 | +30.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 01:00 | +30.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Tue 27 Oct 12:20 | -8.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 06:30 | +30.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Tue 27 Oct 17:00 | -8.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Tue 27 Oct 21:00 | -8.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -8.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 13:40 | -8.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 10:35 | -8.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:00 | -8.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Thu 29 Oct 23:30 | -8.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 10:10 | +30.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 12:45 | -8.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:40 | -8.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 10:40 | -8.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Mon 02 Nov 08:45 | +30.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 09:00 | +30.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:25 | -8.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 11:55 | -8.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 15:30 | -8.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -8.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 03:30 | -8.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Tue 03 Nov 06:45 | -8.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 08:35 | -8.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 12:05 | -8.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Tue 03 Nov 12:30 | -8.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:45 | -8.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:00 | -11.6 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -8.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -8.0 |
| Wed 04 Nov 00:15 | BUY | 13432.8 | trend up, strong push | Wed 04 Nov 01:30 | +30.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 01:35 | +30.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -8.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 08:35 | -8.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 09:30 | -8.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:30 | -8.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:25 | -8.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:30 | -8.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:15 | -8.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:10 | -8.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -8.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 13:15 | +61.8 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 13:15 | +58.9 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 11:40 | -8.0 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 11:40 | -8.0 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 11:05 | -8.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 10:50 | -8.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 10:40 | -8.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F37. +373.2 pips, 2 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: emerging trend, or trend of type slow grind; hours: any time; news: as the bounce; stop: 10; take profit: 50 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.
Any of: direction: the day's 00:00 UK open / the previous day's close.

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F37 | 71 | 21 | 50 | **+373.2** | -11.6 | 16 | +250.0 | +123.2 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 01:50 | BUY | 13384.0 | emerging trend up | Mon 26 Oct 05:25 | -10.0 |
| Mon 26 Oct 06:05 | SELL | 13371.1 | trend down, slow grind | Tue 27 Oct 07:05 | +50.0 |
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Mon 26 Oct 11:40 | -10.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Mon 26 Oct 11:40 | -10.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 14:45 | -10.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Wed 28 Oct 04:20 | +50.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Wed 28 Oct 04:15 | +50.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 07:10 | +50.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 18:35 | -10.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Tue 27 Oct 17:20 | -10.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Tue 27 Oct 21:00 | -10.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -10.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 13:40 | -10.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 11:45 | -10.0 |
| Wed 28 Oct 16:50 | BUY | 13313.2 | trend up, slow grind | Wed 28 Oct 17:50 | -10.0 |
| Thu 29 Oct 05:05 | SELL | 13318.6 | trend down, slow grind | Thu 29 Oct 07:50 | -10.0 |
| Thu 29 Oct 05:25 | SELL | 13316.5 | trend down, slow grind | Thu 29 Oct 07:45 | -10.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:10 | -10.0 |
| Thu 29 Oct 13:15 | SELL | 13314.2 | emerging trend down | Thu 29 Oct 13:30 | -10.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Thu 29 Oct 23:35 | -10.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:25 | -10.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 12:50 | -10.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:40 | -10.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:00 | -10.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Wed 04 Nov 01:15 | +50.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:35 | -10.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:30 | -10.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 14:10 | -10.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 15:35 | -10.0 |
| Mon 02 Nov 23:45 | BUY | 13406.0 | emerging trend up | Tue 03 Nov 02:20 | -10.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -10.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 03:40 | -10.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Tue 03 Nov 11:25 | -10.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 08:45 | -10.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 12:10 | -10.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Tue 03 Nov 12:30 | -10.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:45 | -10.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:00 | -11.6 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -10.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -10.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -10.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 10:40 | -10.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:30 | -10.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:30 | -10.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -10.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:35 | -10.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:20 | -10.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:15 | -10.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -10.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 13:15 | +61.8 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 13:15 | +58.9 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 12:20 | -10.0 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 12:20 | -10.0 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 11:15 | -10.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 10:55 | -10.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 10:50 | -10.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F38. +370.5 pips, 2 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: emerging trend, or trend of type slow grind; hours: any time; news: as the bounce; stop: 15; take profit: 20 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.
Any of: direction: the day's 00:00 UK open / the previous day's close.

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F38 | 71 | 38 | 33 | **+370.5** | -15.0 | 5 | +230.0 | +140.5 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 01:50 | BUY | 13384.0 | emerging trend up | Mon 26 Oct 05:50 | -15.0 |
| Mon 26 Oct 06:05 | SELL | 13371.1 | trend down, slow grind | Mon 26 Oct 08:35 | +20.0 |
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Mon 26 Oct 13:20 | +20.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Mon 26 Oct 13:55 | +20.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Tue 27 Oct 07:00 | +20.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Tue 27 Oct 07:00 | +20.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 16:30 | -15.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Tue 27 Oct 07:00 | +20.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Tue 27 Oct 07:00 | +20.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Tue 27 Oct 07:00 | +20.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Tue 27 Oct 09:30 | +20.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Tue 27 Oct 09:30 | +20.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Tue 27 Oct 16:15 | +20.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 05:20 | +20.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Wed 28 Oct 05:30 | +20.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Wed 28 Oct 06:30 | +20.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -15.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 07:15 | +20.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 13:30 | -15.0 |
| Wed 28 Oct 16:50 | BUY | 13313.2 | trend up, slow grind | Wed 28 Oct 17:50 | -15.0 |
| Thu 29 Oct 05:05 | SELL | 13318.6 | trend down, slow grind | Thu 29 Oct 09:20 | +20.0 |
| Thu 29 Oct 05:25 | SELL | 13316.5 | trend down, slow grind | Thu 29 Oct 11:20 | -15.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:25 | -15.0 |
| Thu 29 Oct 13:15 | SELL | 13314.2 | emerging trend down | Thu 29 Oct 13:35 | -15.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Fri 30 Oct 07:20 | +20.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 09:15 | +20.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 11:05 | +20.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:50 | -15.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:35 | -15.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Mon 02 Nov 08:35 | +20.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 08:45 | +20.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 08:50 | +20.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 18:35 | -15.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 16:05 | -15.0 |
| Mon 02 Nov 23:45 | BUY | 13406.0 | emerging trend up | Tue 03 Nov 13:30 | +20.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -15.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 04:05 | -15.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Tue 03 Nov 23:55 | +20.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 10:05 | -15.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:25 | -15.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Wed 04 Nov 00:15 | +20.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:50 | -15.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:25 | -15.0 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -15.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -15.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 01:25 | +20.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -15.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -15.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -15.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:40 | -15.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -15.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 13:15 | +61.8 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 13:15 | +58.9 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 13:15 | +8.3 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 13:15 | +7.4 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 12:20 | -15.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:25 | -15.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 11:15 | -15.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F39. +370.5 pips, 1 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: emerging trend, or trend of type slow grind; direction: the direction rule; hours: any time; news: as the bounce; stop: 15; take profit: 20 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.


| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F39 | 64 | 35 | 29 | **+370.5** | -15.0 | 5 | +250.0 | +120.5 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Mon 26 Oct 13:20 | +20.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Mon 26 Oct 13:55 | +20.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Tue 27 Oct 07:00 | +20.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Tue 27 Oct 07:00 | +20.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 16:30 | -15.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Tue 27 Oct 07:00 | +20.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Tue 27 Oct 07:00 | +20.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Tue 27 Oct 07:00 | +20.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Tue 27 Oct 09:30 | +20.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Tue 27 Oct 09:30 | +20.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Tue 27 Oct 16:15 | +20.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 05:20 | +20.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Wed 28 Oct 05:30 | +20.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Wed 28 Oct 06:30 | +20.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -15.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 07:15 | +20.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 13:30 | -15.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:25 | -15.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Fri 30 Oct 07:20 | +20.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 09:15 | +20.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 11:05 | +20.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:50 | -15.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:35 | -15.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Mon 02 Nov 08:35 | +20.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 08:45 | +20.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 08:50 | +20.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 18:35 | -15.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 16:05 | -15.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -15.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 04:05 | -15.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Tue 03 Nov 23:55 | +20.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 10:05 | -15.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:25 | -15.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Wed 04 Nov 00:15 | +20.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:50 | -15.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:25 | -15.0 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -15.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -15.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 01:25 | +20.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -15.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -15.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -15.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:40 | -15.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -15.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 13:15 | +61.8 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 13:15 | +58.9 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 13:15 | +8.3 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 13:15 | +7.4 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 12:20 | -15.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:25 | -15.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 11:15 | -15.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F40. +370.1 pips, 2 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend only; hours: any time; news: as the EMA pullback; stop: 6; take profit: 50 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.
Any of: direction: the day's 00:00 UK open / the previous day's close.

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F40 | 44 | 9 | 35 | **+370.1** | -6.0 | 15 | +166.0 | +204.1 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 06:05 | SELL | 13371.1 | trend down, slow grind | Tue 27 Oct 07:05 | +50.0 |
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Mon 26 Oct 10:25 | -6.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Mon 26 Oct 10:25 | -6.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Tue 27 Oct 17:00 | -6.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Tue 27 Oct 20:55 | -6.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -6.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 13:30 | -6.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 10:30 | -6.0 |
| Wed 28 Oct 16:50 | BUY | 13313.2 | trend up, slow grind | Wed 28 Oct 17:25 | -6.0 |
| Thu 29 Oct 05:05 | SELL | 13318.6 | trend down, slow grind | Thu 29 Oct 07:45 | -6.0 |
| Thu 29 Oct 05:25 | SELL | 13316.5 | trend down, slow grind | Thu 29 Oct 07:30 | -6.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Thu 29 Oct 23:10 | -6.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 12:40 | -6.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 09:00 | -6.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 10:40 | -6.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:25 | -6.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:25 | -6.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -6.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 08:35 | -6.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 09:20 | -6.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:30 | -6.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:25 | -6.0 |
| Thu 05 Nov 08:00 | SELL | 13469.9 | trend down, strong push | Thu 05 Nov 08:05 | -6.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 12:00 | -6.0 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 12:00 | -6.0 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 12:00 | -6.0 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 12:00 | -6.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:05 | -6.0 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 20:30 | +80.1 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 08:15 | -6.0 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 08:45 | -6.0 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 11:20 | -6.0 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 10:50 | -6.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 10:40 | -6.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 10:35 | -6.0 |
| Fri 06 Nov 13:30 | SELL | 13383.9 | trend down, slow grind | Fri 06 Nov 13:30 | -6.0 |
| Fri 06 Nov 13:45 | SELL | 13366.7 | trend down, slow grind | Fri 06 Nov 13:50 | -6.0 |

#### F41. +369.7 pips, 2 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend only, type slow grind; hours: any time; news: as the EMA pullback; stop: 8; take profit: 50 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.
Any of: direction: the day's 00:00 UK open / the previous day's close.

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F41 | 43 | 10 | 33 | **+369.7** | -8.0 | 15 | +138.0 | +231.7 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 06:05 | SELL | 13371.1 | trend down, slow grind | Tue 27 Oct 07:05 | +50.0 |
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Mon 26 Oct 11:00 | -8.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Mon 26 Oct 11:00 | -8.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Tue 27 Oct 17:00 | -8.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Tue 27 Oct 21:00 | -8.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -8.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 13:40 | -8.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 10:35 | -8.0 |
| Wed 28 Oct 16:50 | BUY | 13313.2 | trend up, slow grind | Wed 28 Oct 17:35 | -8.0 |
| Thu 29 Oct 05:05 | SELL | 13318.6 | trend down, slow grind | Thu 29 Oct 07:45 | -8.0 |
| Thu 29 Oct 05:25 | SELL | 13316.5 | trend down, slow grind | Thu 29 Oct 07:45 | -8.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Thu 29 Oct 23:30 | -8.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 12:45 | -8.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:40 | -8.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 10:40 | -8.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:30 | -8.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:25 | -8.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -8.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 08:35 | -8.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 09:30 | -8.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:30 | -8.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:25 | -8.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 12:00 | -8.0 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 12:00 | -8.0 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 12:00 | -8.0 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 12:00 | -8.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:10 | -8.0 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 20:30 | +80.1 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 20:30 | +53.6 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 11:40 | -8.0 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 11:40 | -8.0 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 11:05 | -8.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 10:50 | -8.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 10:40 | -8.0 |
| Fri 06 Nov 13:30 | SELL | 13383.9 | trend down, slow grind | Fri 06 Nov 13:30 | -8.0 |
| Fri 06 Nov 13:45 | SELL | 13366.7 | trend down, slow grind | Fri 06 Nov 13:50 | -8.0 |

#### F42. +363.3 pips, 2 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend and emerging trend; hours: any time; news: as the bounce; stop: 12; take profit: 50 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.
Any of: direction: the day's 00:00 UK open / the previous day's close.

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F42 | 72 | 24 | 48 | **+363.3** | -13.9 | 16 | +208.7 | +154.6 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 01:50 | BUY | 13384.0 | emerging trend up | Mon 26 Oct 05:40 | -12.0 |
| Mon 26 Oct 06:05 | SELL | 13371.1 | trend down, slow grind | Tue 27 Oct 07:05 | +50.0 |
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Mon 26 Oct 12:50 | -12.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Mon 26 Oct 12:50 | -12.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 15:20 | -12.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Wed 28 Oct 04:20 | +50.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Wed 28 Oct 04:15 | +50.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 07:10 | +50.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 18:35 | -12.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Wed 28 Oct 18:35 | -12.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Tue 27 Oct 21:25 | -13.3 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -12.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 16:05 | -12.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 12:05 | -12.0 |
| Wed 28 Oct 16:50 | BUY | 13313.2 | trend up, slow grind | Wed 28 Oct 17:50 | -12.0 |
| Thu 29 Oct 05:05 | SELL | 13318.6 | trend down, slow grind | Thu 29 Oct 08:00 | -12.0 |
| Thu 29 Oct 05:25 | SELL | 13316.5 | trend down, slow grind | Thu 29 Oct 07:50 | -12.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:10 | -12.0 |
| Thu 29 Oct 13:15 | SELL | 13314.2 | emerging trend down | Thu 29 Oct 13:30 | -12.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Thu 29 Oct 23:45 | -12.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:40 | -12.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 12:50 | -12.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:45 | -12.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:35 | -12.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Wed 04 Nov 01:15 | +50.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:40 | -12.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:35 | -12.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 14:10 | -12.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 15:35 | -12.0 |
| Mon 02 Nov 23:45 | BUY | 13406.0 | emerging trend up | Wed 04 Nov 01:20 | +50.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -12.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 03:50 | -12.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Tue 03 Nov 11:25 | -12.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 09:15 | -12.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:10 | -12.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Tue 03 Nov 12:40 | -12.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:50 | -12.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:20 | -13.9 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -12.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -12.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -12.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -12.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:30 | -12.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:30 | -12.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -12.0 |
| Thu 05 Nov 08:00 | SELL | 13469.9 | trend down, strong push | Thu 05 Nov 08:15 | -12.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:40 | -12.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:20 | -12.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:20 | -12.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -12.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 13:15 | +61.8 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 13:15 | +58.9 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 13:15 | +8.3 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 13:15 | +7.4 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 11:25 | -12.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:10 | -12.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 10:55 | -12.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F43. +363.2 pips, 2 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend and emerging trend; hours: any time; news: as the bounce; stop: 10; take profit: 50 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.
Any of: direction: the day's 00:00 UK open / the previous day's close.

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F43 | 72 | 21 | 51 | **+363.2** | -11.6 | 16 | +250.0 | +113.2 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 01:50 | BUY | 13384.0 | emerging trend up | Mon 26 Oct 05:25 | -10.0 |
| Mon 26 Oct 06:05 | SELL | 13371.1 | trend down, slow grind | Tue 27 Oct 07:05 | +50.0 |
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Mon 26 Oct 11:40 | -10.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Mon 26 Oct 11:40 | -10.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 14:45 | -10.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Wed 28 Oct 04:20 | +50.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Wed 28 Oct 04:15 | +50.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 07:10 | +50.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 18:35 | -10.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Tue 27 Oct 17:20 | -10.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Tue 27 Oct 21:00 | -10.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -10.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 13:40 | -10.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 11:45 | -10.0 |
| Wed 28 Oct 16:50 | BUY | 13313.2 | trend up, slow grind | Wed 28 Oct 17:50 | -10.0 |
| Thu 29 Oct 05:05 | SELL | 13318.6 | trend down, slow grind | Thu 29 Oct 07:50 | -10.0 |
| Thu 29 Oct 05:25 | SELL | 13316.5 | trend down, slow grind | Thu 29 Oct 07:45 | -10.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:10 | -10.0 |
| Thu 29 Oct 13:15 | SELL | 13314.2 | emerging trend down | Thu 29 Oct 13:30 | -10.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Thu 29 Oct 23:35 | -10.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:25 | -10.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 12:50 | -10.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:40 | -10.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:00 | -10.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Wed 04 Nov 01:15 | +50.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:35 | -10.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:30 | -10.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 14:10 | -10.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 15:35 | -10.0 |
| Mon 02 Nov 23:45 | BUY | 13406.0 | emerging trend up | Tue 03 Nov 02:20 | -10.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -10.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 03:40 | -10.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Tue 03 Nov 11:25 | -10.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 08:45 | -10.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 12:10 | -10.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Tue 03 Nov 12:30 | -10.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:45 | -10.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:00 | -11.6 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -10.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -10.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -10.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 10:40 | -10.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:30 | -10.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:30 | -10.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -10.0 |
| Thu 05 Nov 08:00 | SELL | 13469.9 | trend down, strong push | Thu 05 Nov 08:10 | -10.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:35 | -10.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:20 | -10.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:15 | -10.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -10.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 13:15 | +61.8 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 13:15 | +58.9 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 12:20 | -10.0 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 12:20 | -10.0 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 11:15 | -10.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 10:55 | -10.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 10:50 | -10.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F44. +362.1 pips, 1 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend and emerging trend; direction: the direction rule; hours: any time; news: as the bounce; stop: 8; take profit: 50; protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.


| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F44 | 65 | 19 | 46 | **+362.1** | -11.6 | 28 | +222.0 | +140.1 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Mon 26 Oct 11:00 | -8.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Mon 26 Oct 11:00 | -8.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 14:45 | -8.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Wed 28 Oct 04:20 | +50.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Wed 28 Oct 04:15 | +50.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Tue 27 Oct 12:20 | -8.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 16:50 | -8.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Tue 27 Oct 17:00 | -8.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Tue 27 Oct 21:00 | -8.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -8.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 13:40 | -8.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 10:35 | -8.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:00 | -8.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Thu 29 Oct 23:30 | -8.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:00 | -8.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 12:45 | -8.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:40 | -8.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 10:40 | -8.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Tue 03 Nov 02:20 | -8.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:30 | -8.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:25 | -8.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 11:55 | -8.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 15:30 | -8.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -8.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 03:30 | -8.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Tue 03 Nov 06:45 | -8.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 08:35 | -8.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 12:05 | -8.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Tue 03 Nov 12:30 | -8.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:45 | -8.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:00 | -11.6 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -8.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -8.0 |
| Wed 04 Nov 00:15 | BUY | 13432.8 | trend up, strong push | Wed 04 Nov 08:40 | +50.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -8.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 08:35 | -8.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 09:30 | -8.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:30 | -8.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:25 | -8.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:30 | -8.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:15 | -8.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:10 | -8.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -8.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 11:40 | -8.0 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 11:40 | -8.0 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 11:05 | -8.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 10:50 | -8.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 10:40 | -8.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F45. +361.7 pips, 2 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend only; hours: any time; news: as the EMA pullback; stop: 8; take profit: 50 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.
Any of: direction: the day's 00:00 UK open / the previous day's close.

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F45 | 44 | 10 | 34 | **+361.7** | -8.0 | 15 | +138.0 | +223.7 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 06:05 | SELL | 13371.1 | trend down, slow grind | Tue 27 Oct 07:05 | +50.0 |
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Mon 26 Oct 11:00 | -8.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Mon 26 Oct 11:00 | -8.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Tue 27 Oct 17:00 | -8.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Tue 27 Oct 21:00 | -8.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -8.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 13:40 | -8.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 10:35 | -8.0 |
| Wed 28 Oct 16:50 | BUY | 13313.2 | trend up, slow grind | Wed 28 Oct 17:35 | -8.0 |
| Thu 29 Oct 05:05 | SELL | 13318.6 | trend down, slow grind | Thu 29 Oct 07:45 | -8.0 |
| Thu 29 Oct 05:25 | SELL | 13316.5 | trend down, slow grind | Thu 29 Oct 07:45 | -8.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Thu 29 Oct 23:30 | -8.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 12:45 | -8.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:40 | -8.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 10:40 | -8.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:30 | -8.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:25 | -8.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -8.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 08:35 | -8.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 09:30 | -8.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:30 | -8.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:25 | -8.0 |
| Thu 05 Nov 08:00 | SELL | 13469.9 | trend down, strong push | Thu 05 Nov 08:10 | -8.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 12:00 | -8.0 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 12:00 | -8.0 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 12:00 | -8.0 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 12:00 | -8.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:10 | -8.0 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 14:15 | +100.0 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 20:30 | +80.1 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 20:30 | +53.6 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 11:40 | -8.0 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 11:40 | -8.0 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 11:05 | -8.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 10:50 | -8.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 10:40 | -8.0 |
| Fri 06 Nov 13:30 | SELL | 13383.9 | trend down, slow grind | Fri 06 Nov 13:30 | -8.0 |
| Fri 06 Nov 13:45 | SELL | 13366.7 | trend down, slow grind | Fri 06 Nov 13:50 | -8.0 |

#### F46. +359.6 pips, 2 combination(s) with this result

Shared: entry: pause 3, the pause's lowest point; EMA pullback open: regardless; direction: the direction rule; hours: any time; news: as the bounce; stop: 15; take profit: 30 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.
Any of: states: emerging trend, or trend of type slow grind / trend and emerging trend.

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F46 | 44 | 21 | 23 | **+359.6** | -15.0 | 5 | +165.0 | +194.6 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 07:00 | +30.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Tue 27 Oct 09:20 | +30.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Tue 27 Oct 09:25 | +30.0 |
| Mon 26 Oct 13:55 | SELL | 13336.3 | emerging trend down | Mon 26 Oct 15:55 | -15.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Tue 27 Oct 09:25 | +30.0 |
| Mon 26 Oct 20:00 | SELL | 13345.4 | emerging trend down | Tue 27 Oct 09:25 | +30.0 |
| Tue 27 Oct 06:00 | SELL | 13331.3 | trend down, slow grind | Wed 28 Oct 01:00 | +30.0 |
| Tue 27 Oct 09:10 | SELL | 13318.4 | emerging trend down | Tue 27 Oct 12:10 | -15.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 06:30 | +30.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -15.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 16:10 | -15.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:25 | -15.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Fri 30 Oct 09:10 | +30.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 10:10 | +30.0 |
| Fri 30 Oct 09:05 | BUY | 13416.6 | trend up, slow grind | Fri 30 Oct 12:50 | -15.0 |
| Fri 30 Oct 10:05 | BUY | 13431.2 | trend up, slow grind | Fri 30 Oct 12:35 | -15.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Mon 02 Nov 08:45 | +30.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 09:00 | +30.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:45 | -15.0 |
| Mon 02 Nov 11:45 | BUY | 13419.7 | emerging trend up | Mon 02 Nov 18:25 | -15.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 10:05 | -15.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:25 | -15.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -15.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 01:35 | +30.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -15.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -15.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -15.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:30 | SELL | 13454.4 | trend down, slow grind | Thu 05 Nov 11:45 | -1.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 22:25 | SELL | 13440.5 | emerging trend down | Thu 05 Nov 22:25 | -15.0 |
| Fri 06 Nov 01:35 | SELL | 13448.6 | emerging trend down | Fri 06 Nov 13:15 | +61.3 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:20 | SELL | 13445.9 | trend down, slow grind | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 13:15 | +8.3 |
| Fri 06 Nov 09:20 | SELL | 13389.4 | trend down, slow grind | Fri 06 Nov 12:20 | -15.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:25 | -15.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F47. +359.1 pips, 2 combination(s) with this result

Shared: entry: pause 3, the pause's lowest point; EMA pullback open: regardless; states: trend and emerging trend; hours: any time; news: as the bounce; stop: 15; take profit: 30 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.
Any of: direction: the day's 00:00 UK open / the previous day's close.

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F47 | 49 | 23 | 26 | **+359.1** | -15.0 | 5 | +150.0 | +209.1 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 01:50 | BUY | 13384.0 | emerging trend up | Mon 26 Oct 05:50 | -15.0 |
| Mon 26 Oct 06:10 | SELL | 13369.9 | trend down, slow grind | Mon 26 Oct 13:25 | +30.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 07:00 | +30.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Tue 27 Oct 09:20 | +30.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Tue 27 Oct 09:25 | +30.0 |
| Mon 26 Oct 13:55 | SELL | 13336.3 | emerging trend down | Mon 26 Oct 15:55 | -15.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Tue 27 Oct 09:25 | +30.0 |
| Mon 26 Oct 20:00 | SELL | 13345.4 | emerging trend down | Tue 27 Oct 09:25 | +30.0 |
| Tue 27 Oct 06:00 | SELL | 13331.3 | trend down, slow grind | Wed 28 Oct 01:00 | +30.0 |
| Tue 27 Oct 09:10 | SELL | 13318.4 | emerging trend down | Tue 27 Oct 12:10 | -15.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 06:30 | +30.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -15.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 16:10 | -15.0 |
| Wed 28 Oct 16:50 | BUY | 13313.2 | trend up, slow grind | Wed 28 Oct 17:50 | -15.0 |
| Thu 29 Oct 05:30 | SELL | 13316.4 | trend down, slow grind | Thu 29 Oct 11:20 | -15.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:25 | -15.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Fri 30 Oct 09:10 | +30.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 10:10 | +30.0 |
| Fri 30 Oct 09:05 | BUY | 13416.6 | trend up, slow grind | Fri 30 Oct 12:50 | -15.0 |
| Fri 30 Oct 10:05 | BUY | 13431.2 | trend up, slow grind | Fri 30 Oct 12:35 | -15.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Mon 02 Nov 08:45 | +30.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 09:00 | +30.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:45 | -15.0 |
| Mon 02 Nov 11:45 | BUY | 13419.7 | emerging trend up | Mon 02 Nov 18:25 | -15.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 10:05 | -15.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:25 | -15.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -15.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 01:35 | +30.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -15.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -15.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -15.0 |
| Thu 05 Nov 08:00 | SELL | 13469.9 | trend down, strong push | Thu 05 Nov 11:45 | +14.5 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:30 | SELL | 13454.4 | trend down, slow grind | Thu 05 Nov 11:45 | -1.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 22:25 | SELL | 13440.5 | emerging trend down | Thu 05 Nov 22:25 | -15.0 |
| Fri 06 Nov 01:35 | SELL | 13448.6 | emerging trend down | Fri 06 Nov 13:15 | +61.3 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:20 | SELL | 13445.9 | trend down, slow grind | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 13:15 | +8.3 |
| Fri 06 Nov 09:20 | SELL | 13389.4 | trend down, slow grind | Fri 06 Nov 12:20 | -15.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:25 | -15.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F48. +359.1 pips, 2 combination(s) with this result

Shared: entry: pause 3, the pause's lowest point; EMA pullback open: regardless; states: trend and emerging trend; hours: any time; news: as the bounce; stop: 15; take profit: 50 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.
Any of: direction: the day's 00:00 UK open / the previous day's close.

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F48 | 49 | 19 | 30 | **+359.1** | -15.0 | 11 | +155.0 | +204.1 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 01:50 | BUY | 13384.0 | emerging trend up | Mon 26 Oct 05:50 | -15.0 |
| Mon 26 Oct 06:10 | SELL | 13369.9 | trend down, slow grind | Tue 27 Oct 07:05 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Wed 28 Oct 04:15 | +50.0 |
| Mon 26 Oct 13:55 | SELL | 13336.3 | emerging trend down | Mon 26 Oct 15:55 | -15.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Wed 28 Oct 04:20 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.4 | emerging trend down | Wed 28 Oct 04:15 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.3 | trend down, slow grind | Wed 28 Oct 06:45 | +50.0 |
| Tue 27 Oct 09:10 | SELL | 13318.4 | emerging trend down | Tue 27 Oct 12:10 | -15.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 18:35 | -15.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -15.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 16:10 | -15.0 |
| Wed 28 Oct 16:50 | BUY | 13313.2 | trend up, slow grind | Wed 28 Oct 17:50 | -15.0 |
| Thu 29 Oct 05:30 | SELL | 13316.4 | trend down, slow grind | Thu 29 Oct 11:20 | -15.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:25 | -15.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Fri 30 Oct 14:05 | -15.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:45 | -15.0 |
| Fri 30 Oct 09:05 | BUY | 13416.6 | trend up, slow grind | Fri 30 Oct 12:50 | -15.0 |
| Fri 30 Oct 10:05 | BUY | 13431.2 | trend up, slow grind | Fri 30 Oct 12:35 | -15.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Wed 04 Nov 01:15 | +50.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:50 | -15.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:45 | -15.0 |
| Mon 02 Nov 11:45 | BUY | 13419.7 | emerging trend up | Mon 02 Nov 18:25 | -15.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 10:05 | -15.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 13:25 | -15.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -15.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -15.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | -15.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:40 | -15.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -15.0 |
| Thu 05 Nov 08:00 | SELL | 13469.9 | trend down, strong push | Thu 05 Nov 11:45 | +14.5 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:30 | SELL | 13454.4 | trend down, slow grind | Thu 05 Nov 11:45 | -1.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | -15.0 |
| Thu 05 Nov 22:25 | SELL | 13440.5 | emerging trend down | Thu 05 Nov 22:25 | -15.0 |
| Fri 06 Nov 01:35 | SELL | 13448.6 | emerging trend down | Fri 06 Nov 13:15 | +61.3 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:20 | SELL | 13445.9 | trend down, slow grind | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 13:15 | +17.7 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 13:15 | +8.3 |
| Fri 06 Nov 09:20 | SELL | 13389.4 | trend down, slow grind | Fri 06 Nov 12:20 | -15.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 11:25 | -15.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F49. +359.1 pips, 1 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend and emerging trend; direction: the direction rule; hours: any time; news: as the bounce; stop: 6; take profit: 50 (100 on big-news days); protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.


| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F49 | 65 | 16 | 49 | **+359.1** | -6.0 | 28 | +142.0 | +217.1 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Mon 26 Oct 10:25 | -6.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Mon 26 Oct 10:25 | -6.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 14:30 | -6.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Mon 26 Oct 22:00 | -6.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Mon 26 Oct 22:00 | -6.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Tue 27 Oct 12:10 | -6.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Tue 27 Oct 17:10 | -6.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Tue 27 Oct 17:00 | -6.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Tue 27 Oct 20:55 | -6.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -6.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 13:30 | -6.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 10:30 | -6.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:00 | -6.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Thu 29 Oct 23:10 | -6.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:00 | -6.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 12:40 | -6.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 09:00 | -6.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 10:40 | -6.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Mon 02 Nov 22:30 | -6.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:25 | -6.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:25 | -6.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 11:50 | -6.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 15:25 | -6.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -6.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 02:45 | -6.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Tue 03 Nov 06:00 | -6.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 08:00 | -6.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 11:55 | -6.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Tue 03 Nov 12:25 | -6.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:45 | -6.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 20:00 | -6.0 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -6.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -6.0 |
| Wed 04 Nov 00:15 | BUY | 13432.8 | trend up, strong push | Wed 04 Nov 08:40 | +50.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:10 | -6.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 08:35 | -6.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 09:20 | -6.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:30 | -6.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:25 | -6.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 11:45 | +6.4 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 11:45 | +5.4 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 11:45 | +2.6 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 11:45 | +1.3 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:20 | -6.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 17:40 | -6.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:05 | -6.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -6.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 13:15 | +61.8 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 13:15 | +59.8 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 13:15 | +58.9 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 13:15 | +58.6 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:15 | +44.2 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 08:15 | -6.0 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 08:45 | -6.0 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 11:20 | -6.0 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 10:50 | -6.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 10:40 | -6.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 10:35 | -6.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |

#### F50. +356.5 pips, 1 combination(s) with this result

Shared: entry: pause 2, the pause's lowest point; EMA pullback open: regardless; states: trend and emerging trend; direction: the direction rule; hours: any time; news: as the EMA pullback; stop: 10; take profit: 50; protection: none; holding: Friday 20:30; level close: not applied; trades at once: no limit.


| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| F50 | 67 | 17 | 50 | **+356.5** | -11.6 | 14 | +250.0 | +106.5 |  |

| Entry | Dir | Entry price | State at entry | Closed | Pips |
|---|---|---|---|---|---|
| Mon 26 Oct 07:40 | SELL | 13361.1 | trend down, slow grind | Tue 27 Oct 09:30 | +50.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Tue 27 Oct 16:15 | +50.0 |
| Mon 26 Oct 09:30 | SELL | 13345.7 | trend down, slow grind | Mon 26 Oct 11:40 | -10.0 |
| Mon 26 Oct 09:55 | SELL | 13345.4 | trend down, slow grind | Mon 26 Oct 11:40 | -10.0 |
| Mon 26 Oct 13:50 | SELL | 13338.3 | emerging trend down | Mon 26 Oct 14:45 | -10.0 |
| Mon 26 Oct 19:30 | SELL | 13345.2 | emerging trend down | Wed 28 Oct 04:20 | +50.0 |
| Mon 26 Oct 19:45 | SELL | 13346.2 | emerging trend down | Wed 28 Oct 04:10 | +50.0 |
| Mon 26 Oct 20:00 | SELL | 13345.5 | emerging trend down | Wed 28 Oct 04:15 | +50.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | Wed 28 Oct 06:40 | +50.0 |
| Tue 27 Oct 07:00 | SELL | 13326.4 | emerging trend down | Wed 28 Oct 07:10 | +50.0 |
| Tue 27 Oct 15:40 | SELL | 13313.4 | emerging trend down | Wed 28 Oct 18:35 | -10.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Tue 27 Oct 17:20 | -10.0 |
| Tue 27 Oct 20:45 | SELL | 13306.1 | trend down, slow grind | Tue 27 Oct 21:00 | -10.0 |
| Tue 27 Oct 21:25 | SELL | 13297.0 | trend down, slow grind | Tue 27 Oct 21:25 | -10.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 13:40 | -10.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 11:45 | -10.0 |
| Thu 29 Oct 09:10 | SELL | 13306.9 | emerging trend down | Thu 29 Oct 10:10 | -10.0 |
| Thu 29 Oct 22:50 | BUY | 13386.9 | trend up, slow grind | Thu 29 Oct 23:35 | -10.0 |
| Fri 30 Oct 07:10 | BUY | 13401.2 | emerging trend up | Fri 30 Oct 13:25 | -10.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 12:50 | -10.0 |
| Fri 30 Oct 08:55 | BUY | 13415.9 | trend up, slow grind | Fri 30 Oct 12:40 | -10.0 |
| Fri 30 Oct 10:00 | BUY | 13430.7 | trend up, slow grind | Fri 30 Oct 12:00 | -10.0 |
| Mon 02 Nov 07:20 | BUY | 13404.6 | emerging trend up | Wed 04 Nov 01:15 | +50.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 10:35 | -10.0 |
| Mon 02 Nov 08:25 | BUY | 13417.6 | trend up, slow grind | Mon 02 Nov 10:30 | -10.0 |
| Mon 02 Nov 11:40 | BUY | 13419.3 | emerging trend up | Mon 02 Nov 14:10 | -10.0 |
| Mon 02 Nov 15:05 | BUY | 13424.5 | emerging trend up | Mon 02 Nov 15:35 | -10.0 |
| Tue 03 Nov 00:35 | BUY | 13413.8 | emerging trend up | Tue 03 Nov 00:40 | -10.0 |
| Tue 03 Nov 02:35 | SELL | 13397.2 | emerging trend down | Tue 03 Nov 03:40 | -10.0 |
| Tue 03 Nov 05:30 | BUY | 13412.2 | emerging trend up | Tue 03 Nov 11:25 | -10.0 |
| Tue 03 Nov 07:55 | BUY | 13421.1 | emerging trend up | Tue 03 Nov 08:45 | -10.0 |
| Tue 03 Nov 11:15 | SELL | 13406.1 | emerging trend down | Tue 03 Nov 12:10 | -10.0 |
| Tue 03 Nov 12:25 | BUY | 13414.8 | emerging trend up | Tue 03 Nov 12:30 | -10.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:45 | -10.0 |
| Tue 03 Nov 17:00 | BUY | 13417.2 | emerging trend up | Tue 03 Nov 22:00 | -11.6 |
| Tue 03 Nov 22:15 | SELL | 13407.3 | emerging trend down | Tue 03 Nov 22:15 | -10.0 |
| Tue 03 Nov 22:45 | SELL | 13403.6 | trend down, slow grind | Tue 03 Nov 22:45 | -10.0 |
| Wed 04 Nov 00:15 | BUY | 13432.8 | trend up, strong push | Wed 04 Nov 08:40 | +50.0 |
| Wed 04 Nov 01:00 | BUY | 13442.2 | trend up, slow grind | Wed 04 Nov 09:15 | +50.0 |
| Wed 04 Nov 03:05 | BUY | 13473.5 | emerging trend up | Wed 04 Nov 03:15 | -10.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 10:40 | -10.0 |
| Wed 04 Nov 09:15 | BUY | 13490.6 | trend up, slow grind | Wed 04 Nov 10:30 | -10.0 |
| Wed 04 Nov 09:35 | BUY | 13491.2 | trend up, slow grind | Wed 04 Nov 10:30 | -10.0 |
| Wed 04 Nov 10:05 | BUY | 13494.4 | trend up, slow grind | Wed 04 Nov 10:30 | -10.0 |
| Thu 05 Nov 10:20 | SELL | 13461.8 | trend down, slow grind | Thu 05 Nov 12:00 | -10.0 |
| Thu 05 Nov 10:35 | SELL | 13460.8 | trend down, slow grind | Thu 05 Nov 12:00 | -10.0 |
| Thu 05 Nov 11:10 | SELL | 13458.0 | trend down, slow grind | Thu 05 Nov 12:00 | -10.0 |
| Thu 05 Nov 11:25 | SELL | 13456.7 | trend down, slow grind | Thu 05 Nov 12:00 | -10.0 |
| Thu 05 Nov 16:50 | BUY | 13476.4 | emerging trend up | Thu 05 Nov 18:35 | -10.0 |
| Thu 05 Nov 17:10 | BUY | 13482.0 | emerging trend up | Thu 05 Nov 18:20 | -10.0 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:15 | -10.0 |
| Thu 05 Nov 22:15 | SELL | 13444.9 | emerging trend down | Thu 05 Nov 22:15 | -10.0 |
| Fri 06 Nov 01:30 | SELL | 13449.1 | emerging trend down | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 02:15 | SELL | 13446.2 | trend down, slow grind | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 02:45 | SELL | 13445.9 | emerging trend down | Fri 06 Nov 07:30 | +50.0 |
| Fri 06 Nov 04:05 | SELL | 13431.5 | trend down, slow grind | Fri 06 Nov 13:30 | +50.0 |
| Fri 06 Nov 07:25 | SELL | 13405.0 | trend down, slow grind | Fri 06 Nov 14:05 | +50.0 |
| Fri 06 Nov 08:40 | SELL | 13395.6 | trend down, slow grind | Fri 06 Nov 12:20 | -10.0 |
| Fri 06 Nov 08:55 | SELL | 13394.7 | trend down, slow grind | Fri 06 Nov 12:20 | -10.0 |
| Fri 06 Nov 09:15 | SELL | 13389.6 | trend down, slow grind | Fri 06 Nov 11:15 | -10.0 |
| Fri 06 Nov 09:50 | SELL | 13386.5 | trend down, slow grind | Fri 06 Nov 10:55 | -10.0 |
| Fri 06 Nov 10:15 | SELL | 13384.5 | trend down, slow grind | Fri 06 Nov 10:50 | -10.0 |
| Fri 06 Nov 13:30 | SELL | 13383.9 | trend down, slow grind | Fri 06 Nov 13:30 | -10.0 |
| Fri 06 Nov 13:45 | SELL | 13366.7 | trend down, slow grind | Fri 06 Nov 15:20 | -10.0 |
| Fri 06 Nov 19:45 | SELL | 13349.5 | emerging trend down | Fri 06 Nov 20:30 | -1.9 |
