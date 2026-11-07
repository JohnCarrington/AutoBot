# EMA pullback variations, 25 October to 6 November 2026

Read-only research on the stored GBPUSD candles (Sunday 25 October 21:00 UK to Friday 6 November close).
Nothing in the bot was changed. Written 7 November 2026.

## Method

- **Entries** exactly as design section 3.2 (the bot's own `strategies/` code, replayed week by week from
  the Sunday open), checked at entry with the switch, the analyser's state and the direction rule (design
  2.2, 2.3). For the "trend and emerging trend" runs the emerging-trend permission was turned on inside
  the research process only. 62 EMA pullback ideas over the two weeks: 27 in trend, 35 in emerging.
- **IG's prices:** a buy opens on the buy price (the idea's entry plus the spread at that candle's open)
  and is stopped and closed on the sell price; a sell opens on the sell price and is stopped and closed
  on the buy price. A stop or protection level that a candle opens beyond is filled at that open.
- **Order inside a 5-minute candle** (unknown from candles): a scheduled close (20:30, news) happens at
  the candle's open; then the stop (or protection level); then the take profit. **If a stop and a target
  are both reached inside one candle, the stop counts first.** Profit protection uses the best price
  reached up to the candle before (it moves the stop for the next candle). In the entry candle the stop
  is not checked unless the candle opened past the entry (the part before the entry is unknown).
- **Profit protection:** "lock 15/10": once 15 pips up, close if it comes back to 10 up; "break-even at
  10": the stop moves to the entry once 10 pips up; "trail X": the stop follows X pips behind the best
  price reached (never looser than the starting stop).
- **Holding:** "daily 20:30": closed at the first 20:30 UK after opening; "Friday 20:30": held overnight,
  closed at 20:30 UK on Friday (a trade opened on Friday after 20:30 would be open when the data ends:
  marked "open at the end of the data", valued at the last close).
- **Big-news rules "as other strategies":** no new trade from 15 minutes before to 30 minutes after a big
  release, and open trades closed 15 minutes before it.
- **Identical setups:** ideas at the same time, direction and entry price: one trade, or each separate.
- **5-trade limit:** at most 5 EMA pullback trades open at once (the other strategies are not in this
  replay, so in real trading they would also take places).
- **Losing run:** losing trades in a row, in order of entry. **Weeks** by entry time.
- **Profit from one day or week** is marked when the total is positive and one day gives at least 80%
  of it, or one week at least 90% of it.
- 7680 combinations in all (2 x 5 x 4 x 6 x 2 x 2 x 2 x 2 x 2).

**Limits of this test:** two weeks only (one of them, Friday 6 November, a big payrolls trend day); 5-minute
candles, not ticks; no slippage beyond candle-open gaps; GBPUSD only.

## A. The current rules (the starting point)

States trend only; stop 12; take profit 100; no profit protection; held overnight and closed at 20:30 UK on Friday; opens 06:00-20:30 UK; may open during big news and not closed before it; each identical setup a separate trade; the 5-trade limit applied.

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 (26-30 Oct) | Week 2 (2-6 Nov) | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| Current rules | 19 | 4 | 15 | **-58.8** | -12.0 | 13 | -96.0 | +37.2 |  |

**Every trade in the starting point:**

| Entry | Dir | Entry price | State | Exit | Exit reason | Pips |
|---|---|---|---|---|---|---|
| Mon 26 Oct 08:35 | SELL | 13349.3 | trend | Thu 29 Oct 15:00 | stop | -12.0 |
| Mon 26 Oct 08:35 | SELL | 13349.3 | trend | Thu 29 Oct 15:00 | stop | -12.0 |
| Tue 27 Oct 16:15 | SELL | 13305.5 | trend | Tue 27 Oct 17:00 | stop | -12.0 |
| Wed 28 Oct 10:45 | SELL | 13276.8 | trend | Wed 28 Oct 11:35 | stop | -12.0 |
| Wed 28 Oct 10:45 | SELL | 13276.8 | trend | Wed 28 Oct 11:35 | stop | -12.0 |
| Fri 30 Oct 09:15 | BUY | 13420.4 | trend | Fri 30 Oct 12:40 | stop | -12.0 |
| Fri 30 Oct 09:15 | BUY | 13420.4 | trend | Fri 30 Oct 12:40 | stop | -12.0 |
| Fri 30 Oct 11:10 | BUY | 13433.6 | trend | Fri 30 Oct 12:00 | stop | -12.0 |
| Mon 02 Nov 08:30 | BUY | 13420.6 | trend | Mon 02 Nov 10:25 | stop | -12.0 |
| Mon 02 Nov 08:30 | BUY | 13420.6 | trend | Mon 02 Nov 10:25 | stop | -12.0 |
| Wed 04 Nov 08:40 | BUY | 13486.0 | trend | Wed 04 Nov 10:40 | stop | -12.0 |
| Wed 04 Nov 08:45 | BUY | 13487.5 | trend | Wed 04 Nov 10:40 | stop | -12.0 |
| Wed 04 Nov 10:15 | BUY | 13497.6 | trend | Wed 04 Nov 10:30 | stop | -12.0 |
| Fri 06 Nov 08:40 | SELL | 13394.3 | trend | Fri 06 Nov 20:30 | 20:30 | +42.9 |
| Fri 06 Nov 08:40 | SELL | 13393.4 | trend | Fri 06 Nov 12:20 | stop | -12.0 |
| Fri 06 Nov 09:00 | SELL | 13390.1 | trend | Fri 06 Nov 11:25 | stop | -12.0 |
| Fri 06 Nov 13:30 | SELL | 13377.5 | trend | Fri 06 Nov 20:30 | 20:30 | +26.1 |
| Fri 06 Nov 13:30 | SELL | 13377.5 | trend | Fri 06 Nov 20:30 | 20:30 | +26.1 |
| Fri 06 Nov 13:30 | SELL | 13377.5 | trend | Fri 06 Nov 20:30 | 20:30 | +26.1 |

## B. Each variable changed on its own

Everything else as in A. The row marked (A) is the current value.

### States allowed

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 (26-30 Oct) | Week 2 (2-6 Nov) | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| trend only (A) | 19 | 4 | 15 | **-58.8** | -12.0 | 13 | -96.0 | +37.2 |  |
| trend and emerging trend | 38 | 5 | 33 | **-168.3** | -12.0 | 31 | -156.0 | -12.3 |  |

### Stop loss (pips)

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 (26-30 Oct) | Week 2 (2-6 Nov) | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| 6 | 19 | 0 | 19 | **-120.6** | -8.2 | 19 | -48.0 | -72.6 |  |
| 8 | 19 | 0 | 19 | **-152.6** | -8.2 | 19 | -64.0 | -88.6 |  |
| 10 | 19 | 3 | 16 | **-81.7** | -10.0 | 16 | -80.0 | -1.7 |  |
| 12 (A) | 19 | 4 | 15 | **-58.8** | -12.0 | 13 | -96.0 | +37.2 |  |
| 15 | 19 | 5 | 14 | **-46.8** | -15.0 | 13 | -120.0 | +73.2 |  |

### Take profit (pips)

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 (26-30 Oct) | Week 2 (2-6 Nov) | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| 20 | 19 | 8 | 11 | **+28.0** | -12.0 | 6 | -32.0 | +60.0 | one day: Fri 06 Nov gives +56.0 of +28.0; one week: week 2 gives +60.0 of +28.0 |
| 30 | 19 | 6 | 13 | **+24.0** | -12.0 | 11 | -12.0 | +36.0 | one day: Fri 06 Nov gives +96.0 of +24.0; one week: week 2 gives +36.0 of +24.0 |
| 50 | 19 | 6 | 13 | **+72.3** | -12.0 | 11 | +28.0 | +44.3 | one day: Fri 06 Nov gives +104.3 of +72.3 |
| 100 (A) | 19 | 4 | 15 | **-58.8** | -12.0 | 13 | -96.0 | +37.2 |  |

### Profit protection

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 (26-30 Oct) | Week 2 (2-6 Nov) | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| none (A) | 19 | 4 | 15 | **-58.8** | -12.0 | 13 | -96.0 | +37.2 |  |
| lock 15/10 | 19 | 8 | 11 | **-53.4** | -12.0 | 6 | -52.0 | -1.4 |  |
| break-even at 10 | 19 | 0 | 10 | **-108.6** | -12.0 | 4 | -48.0 | -60.6 |  |
| trail 10 | 19 | 6 | 13 | **-52.0** | -10.9 | 5 | -38.8 | -13.2 |  |
| trail 15 | 19 | 2 | 17 | **-106.9** | -12.0 | 9 | -70.0 | -36.9 |  |
| trail 20 | 19 | 7 | 12 | **-64.1** | -12.0 | 6 | -60.6 | -3.5 |  |

### Holding

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 (26-30 Oct) | Week 2 (2-6 Nov) | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| daily 20:30 | 19 | 6 | 13 | **-20.8** | -12.0 | 11 | -58.0 | +37.2 |  |
| Friday 20:30 (A) | 19 | 4 | 15 | **-58.8** | -12.0 | 13 | -96.0 | +37.2 |  |

### Opening hours

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 (26-30 Oct) | Week 2 (2-6 Nov) | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| 06:00-20:30 (A) | 19 | 4 | 15 | **-58.8** | -12.0 | 13 | -96.0 | +37.2 |  |
| any time | 23 | 6 | 17 | **+124.5** | -12.0 | 11 | -97.1 | +221.6 | one day: Fri 06 Nov gives +305.6 of +124.5; one week: week 2 gives +221.6 of +124.5 |

### Big-news rules

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 (26-30 Oct) | Week 2 (2-6 Nov) | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| not applied (A) | 19 | 4 | 15 | **-58.8** | -12.0 | 13 | -96.0 | +37.2 |  |
| as other strategies | 16 | 1 | 15 | **-173.0** | -12.0 | 13 | -96.0 | -77.0 |  |

### Identical setups

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 (26-30 Oct) | Week 2 (2-6 Nov) | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| each separate (A) | 19 | 4 | 15 | **-58.8** | -12.0 | 13 | -96.0 | +37.2 |  |
| one trade | 13 | 2 | 11 | **-63.0** | -12.0 | 9 | -60.0 | -3.0 |  |

### 5-trade limit

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 (26-30 Oct) | Week 2 (2-6 Nov) | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| applied (A) | 19 | 4 | 15 | **-58.8** | -12.0 | 13 | -96.0 | +37.2 |  |
| not applied | 19 | 4 | 15 | **-58.8** | -12.0 | 13 | -96.0 | +37.2 |  |

## C1. The 10 best combinations

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 (26-30 Oct) | Week 2 (2-6 Nov) | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 27 | 14 | 13 | **+394.2** | -15.0 | 6 | +5.9 | +388.3 | one week: week 2 gives +388.3 of +394.2 |
| 2 | 27 | 14 | 13 | **+394.2** | -15.0 | 6 | +5.9 | +388.3 | one week: week 2 gives +388.3 of +394.2 |
| 3 | 27 | 13 | 14 | **+371.2** | -12.0 | 6 | +26.9 | +344.3 | one week: week 2 gives +344.3 of +371.2 |
| 4 | 27 | 13 | 14 | **+371.2** | -12.0 | 6 | +26.9 | +344.3 | one week: week 2 gives +344.3 of +371.2 |
| 5 | 62 | 26 | 36 | **+335.4** | -19.3 | 9 | +90.0 | +245.4 |  |
| 6 | 27 | 14 | 13 | **+318.4** | -15.0 | 6 | -80.1 | +398.5 | one day: Fri 06 Nov gives +396.8 of +318.4; one week: week 2 gives +398.5 of +318.4 |
| 7 | 27 | 14 | 13 | **+308.2** | -15.0 | 6 | -80.1 | +388.3 | one day: Fri 06 Nov gives +313.3 of +308.2; one week: week 2 gives +388.3 of +308.2 |
| 8 | 27 | 14 | 13 | **+308.2** | -15.0 | 6 | -80.1 | +388.3 | one day: Fri 06 Nov gives +313.3 of +308.2; one week: week 2 gives +388.3 of +308.2 |
| 9 | 61 | 25 | 36 | **+305.4** | -19.3 | 9 | +90.0 | +215.4 |  |
| 10 | 27 | 13 | 14 | **+303.4** | -12.0 | 6 | -59.1 | +362.5 | one day: Fri 06 Nov gives +345.8 of +303.4; one week: week 2 gives +362.5 of +303.4 |

1. states allowed trend only, stop loss 15, take profit 50, profit protection none, holding Friday 20:30, opening hours any time, big-news rules not applied, identical setups each separate, 5-trade limit applied
2. states allowed trend only, stop loss 15, take profit 50, profit protection none, holding Friday 20:30, opening hours any time, big-news rules not applied, identical setups each separate, 5-trade limit not applied
3. states allowed trend only, stop loss 12, take profit 50, profit protection none, holding Friday 20:30, opening hours any time, big-news rules not applied, identical setups each separate, 5-trade limit applied
4. states allowed trend only, stop loss 12, take profit 50, profit protection none, holding Friday 20:30, opening hours any time, big-news rules not applied, identical setups each separate, 5-trade limit not applied
5. states allowed trend and emerging trend, stop loss 12, take profit 30, profit protection none, holding Friday 20:30, opening hours any time, big-news rules not applied, identical setups each separate, 5-trade limit not applied
6. states allowed trend only, stop loss 15, take profit 100, profit protection none, holding daily 20:30, opening hours any time, big-news rules not applied, identical setups each separate, 5-trade limit not applied
7. states allowed trend only, stop loss 15, take profit 50, profit protection none, holding daily 20:30, opening hours any time, big-news rules not applied, identical setups each separate, 5-trade limit applied
8. states allowed trend only, stop loss 15, take profit 50, profit protection none, holding daily 20:30, opening hours any time, big-news rules not applied, identical setups each separate, 5-trade limit not applied
9. states allowed trend and emerging trend, stop loss 12, take profit 30, profit protection none, holding Friday 20:30, opening hours any time, big-news rules not applied, identical setups each separate, 5-trade limit applied
10. states allowed trend only, stop loss 12, take profit 100, profit protection none, holding daily 20:30, opening hours any time, big-news rules not applied, identical setups each separate, 5-trade limit not applied

## C2. The 10 worst combinations

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 (26-30 Oct) | Week 2 (2-6 Nov) | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 38 | 3 | 35 | **-342.9** | -12.0 | 32 | -168.0 | -174.9 |  |
| 2 | 37 | 3 | 34 | **-330.9** | -12.0 | 31 | -156.0 | -174.9 |  |
| 3 | 59 | 11 | 48 | **-296.5** | -19.3 | 18 | -181.1 | -115.4 |  |
| 4 | 38 | 2 | 36 | **-291.9** | -10.0 | 32 | -140.0 | -151.9 |  |
| 5 | 38 | 2 | 36 | **-291.9** | -10.0 | 32 | -140.0 | -151.9 |  |
| 6 | 38 | 2 | 36 | **-291.9** | -10.0 | 32 | -140.0 | -151.9 |  |
| 7 | 38 | 2 | 36 | **-291.9** | -10.0 | 32 | -140.0 | -151.9 |  |
| 8 | 59 | 5 | 54 | **-281.2** | -19.3 | 31 | -136.0 | -145.2 |  |
| 9 | 29 | 2 | 27 | **-277.3** | -12.0 | 24 | -120.0 | -157.3 |  |
| 10 | 29 | 2 | 27 | **-277.3** | -12.0 | 24 | -120.0 | -157.3 |  |

1. states allowed trend and emerging trend, stop loss 12, take profit 100, profit protection none, holding Friday 20:30, opening hours 06:00-20:30, big-news rules as other strategies, identical setups each separate, 5-trade limit not applied
2. states allowed trend and emerging trend, stop loss 12, take profit 100, profit protection none, holding Friday 20:30, opening hours 06:00-20:30, big-news rules as other strategies, identical setups each separate, 5-trade limit applied
3. states allowed trend and emerging trend, stop loss 12, take profit 100, profit protection none, holding Friday 20:30, opening hours any time, big-news rules as other strategies, identical setups each separate, 5-trade limit not applied
4. states allowed trend and emerging trend, stop loss 10, take profit 100, profit protection none, holding Friday 20:30, opening hours 06:00-20:30, big-news rules as other strategies, identical setups each separate, 5-trade limit not applied
5. states allowed trend and emerging trend, stop loss 10, take profit 100, profit protection none, holding Friday 20:30, opening hours 06:00-20:30, big-news rules as other strategies, identical setups each separate, 5-trade limit applied
6. states allowed trend and emerging trend, stop loss 10, take profit 50, profit protection none, holding Friday 20:30, opening hours 06:00-20:30, big-news rules as other strategies, identical setups each separate, 5-trade limit not applied
7. states allowed trend and emerging trend, stop loss 10, take profit 50, profit protection none, holding Friday 20:30, opening hours 06:00-20:30, big-news rules as other strategies, identical setups each separate, 5-trade limit applied
8. states allowed trend and emerging trend, stop loss 8, take profit 100, profit protection none, holding Friday 20:30, opening hours any time, big-news rules as other strategies, identical setups each separate, 5-trade limit not applied
9. states allowed trend and emerging trend, stop loss 12, take profit 100, profit protection none, holding Friday 20:30, opening hours 06:00-20:30, big-news rules as other strategies, identical setups one trade, 5-trade limit not applied
10. states allowed trend and emerging trend, stop loss 12, take profit 100, profit protection none, holding Friday 20:30, opening hours 06:00-20:30, big-news rules as other strategies, identical setups one trade, 5-trade limit applied

## C3. The 10 best combinations that are positive in both weeks and not marked in E

| Run | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 (26-30 Oct) | Week 2 (2-6 Nov) | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 62 | 26 | 36 | **+335.4** | -19.3 | 9 | +90.0 | +245.4 |  |
| 2 | 61 | 25 | 36 | **+305.4** | -19.3 | 9 | +90.0 | +215.4 |  |
| 3 | 62 | 23 | 39 | **+279.4** | -19.3 | 9 | +30.0 | +249.4 |  |
| 4 | 27 | 14 | 13 | **+264.0** | -12.0 | 5 | +48.0 | +216.0 |  |
| 5 | 27 | 14 | 13 | **+264.0** | -12.0 | 5 | +48.0 | +216.0 |  |
| 6 | 61 | 22 | 39 | **+249.4** | -19.3 | 9 | +30.0 | +219.4 |  |
| 7 | 24 | 10 | 14 | **+226.7** | -12.0 | 6 | +26.9 | +199.8 |  |
| 8 | 24 | 10 | 14 | **+226.7** | -12.0 | 6 | +26.9 | +199.8 |  |
| 9 | 59 | 23 | 36 | **+222.4** | -19.3 | 9 | +90.0 | +132.4 |  |
| 10 | 45 | 18 | 27 | **+218.0** | -19.3 | 7 | +96.0 | +122.0 |  |

1. states allowed trend and emerging trend, stop loss 12, take profit 30, profit protection none, holding Friday 20:30, opening hours any time, big-news rules not applied, identical setups each separate, 5-trade limit not applied
2. states allowed trend and emerging trend, stop loss 12, take profit 30, profit protection none, holding Friday 20:30, opening hours any time, big-news rules not applied, identical setups each separate, 5-trade limit applied
3. states allowed trend and emerging trend, stop loss 10, take profit 30, profit protection none, holding Friday 20:30, opening hours any time, big-news rules not applied, identical setups each separate, 5-trade limit not applied
4. states allowed trend only, stop loss 12, take profit 30, profit protection none, holding Friday 20:30, opening hours any time, big-news rules not applied, identical setups each separate, 5-trade limit applied
5. states allowed trend only, stop loss 12, take profit 30, profit protection none, holding Friday 20:30, opening hours any time, big-news rules not applied, identical setups each separate, 5-trade limit not applied
6. states allowed trend and emerging trend, stop loss 10, take profit 30, profit protection none, holding Friday 20:30, opening hours any time, big-news rules not applied, identical setups each separate, 5-trade limit applied
7. states allowed trend only, stop loss 12, take profit 50, profit protection none, holding Friday 20:30, opening hours any time, big-news rules as other strategies, identical setups each separate, 5-trade limit applied
8. states allowed trend only, stop loss 12, take profit 50, profit protection none, holding Friday 20:30, opening hours any time, big-news rules as other strategies, identical setups each separate, 5-trade limit not applied
9. states allowed trend and emerging trend, stop loss 12, take profit 30, profit protection none, holding Friday 20:30, opening hours any time, big-news rules as other strategies, identical setups each separate, 5-trade limit not applied
10. states allowed trend and emerging trend, stop loss 12, take profit 30, profit protection none, holding Friday 20:30, opening hours any time, big-news rules not applied, identical setups one trade, 5-trade limit applied

## D. The measures

Every table above gives, for each result: trades, wins, losses, total pips, the biggest single loss, the worst run of losses in a row, and the pips for each of the two weeks.

## E. Results where nearly all the profit comes from one day or one week

- **B: Take profit (pips) = 20** (+28.0 pips): one day: Fri 06 Nov gives +56.0 of +28.0; one week: week 2 gives +60.0 of +28.0
- **B: Take profit (pips) = 30** (+24.0 pips): one day: Fri 06 Nov gives +96.0 of +24.0; one week: week 2 gives +36.0 of +24.0
- **B: Take profit (pips) = 50** (+72.3 pips): one day: Fri 06 Nov gives +104.3 of +72.3
- **B: Opening hours = any time** (+124.5 pips): one day: Fri 06 Nov gives +305.6 of +124.5; one week: week 2 gives +221.6 of +124.5
- **C1 #1** (+394.2 pips): one week: week 2 gives +388.3 of +394.2
- **C1 #2** (+394.2 pips): one week: week 2 gives +388.3 of +394.2
- **C1 #3** (+371.2 pips): one week: week 2 gives +344.3 of +371.2
- **C1 #4** (+371.2 pips): one week: week 2 gives +344.3 of +371.2
- **C1 #6** (+318.4 pips): one day: Fri 06 Nov gives +396.8 of +318.4; one week: week 2 gives +398.5 of +318.4
- **C1 #7** (+308.2 pips): one day: Fri 06 Nov gives +313.3 of +308.2; one week: week 2 gives +388.3 of +308.2
- **C1 #8** (+308.2 pips): one day: Fri 06 Nov gives +313.3 of +308.2; one week: week 2 gives +388.3 of +308.2
- **C1 #10** (+303.4 pips): one day: Fri 06 Nov gives +345.8 of +303.4; one week: week 2 gives +362.5 of +303.4

Of all 7680 combinations, 1815 have a positive total; 1693 of those get nearly all their profit from one day or one week; 320 are positive in both weeks.
