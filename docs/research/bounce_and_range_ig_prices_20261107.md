# Bollinger bounce and range trade on IG's prices, 26 October to 6 November 2026

Read-only replay of the stored GBPUSD candles. Nothing in the bot was changed. Written 7 November 2026.

## Method

- **Entries:** the bot's own strategies (`strategies/`), replayed week by week from the Sunday open, with
  the current design: the bounce in ranging (either way), emerging trend and trend (trend's direction
  only) and possible reversal (either way); the range trade in ranging only; the direction rule for the
  bounce except in a possible reversal, not for the range trade (design 2.2, 2.3, 3.3, 3.4). The
  strategies' own rejection watcher (only the rules of 3.3 and 3.4, several setups at once).
- **Section 6, from the bot's own code:** new trades only from 06:00 to 20:30 UK and not in a big-news
  window (`may_open`); one bounce buy and one bounce sell open at a time; one range trade at a time;
  most at once 5 (the EMA pullback does not count; it and the slow grind are not in this replay).
  Candidates are taken in time order (the bounce first at the same moment).
- **Exits (design 4, from the bot's own code):** the 6-pip stop (`STOP_LOSS_PIPS`), the 100-pip take profit
  (`TAKE_PROFIT_PIPS`), the 20:30 UK close every day, the close 15 minutes before big news, the close on a
  confirmed rejection at a level against the trade (the shared rejection part as the analyser runs it: a
  bounce the other way, at a level, that counts, triggering in a candle after the entry candle), and for
  the range trade the half close at the opposite band.
- **IG's prices:** a buy opens on the buy price (the idea's entry plus the spread at that candle's open)
  and is stopped and closed on the sell price; a sell opens on the sell price and is stopped and closed on
  the buy price. A rejection close is at the rejection's trigger (a sell price), so a sell is closed at it
  plus the spread. The range half close happens when the chart (sell) price reaches the opposite band (the
  band of the last finished candle), filled on the closing price.
- **Inside one 5-minute candle:** a scheduled close (20:30, news) at its open; then the stop (a candle
  opening past it fills at its open); then the take profit; then the half close; then the rejection close.
  In the entry candle the stop counts only if the candle opened past the entry, or closed beyond the stop
  (its close comes after the entry, so the stop was then hit after the entry).
- **Range trade pips** are for the whole trade: the average of the half closed at the band and the half
  closed at the exit. A half-closed range trade still counts as open for the limits.
- **Marked** when the total is positive and one day gives at least 80% of it, or one week at least 90%.

## Results

| | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 (26-30 Oct) | Week 2 (2-6 Nov) | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| Bollinger bounce | 76 | 28 | 48 | **-14.2** | -6.0 | 9 | -28.7 | +14.5 |  |
| range trade | 7 | 6 | 1 | **+23.1** | -2.3 | 1 | +5.9 | +17.2 |  |

### Pips by day

| Day | Bollinger bounce | Range trade |
|---|---|---|
| Mon 26 Oct | +13.2 | +2.0 |
| Tue 27 Oct | -17.3 | +3.9 |
| Wed 28 Oct | -21.6 | +0.0 |
| Thu 29 Oct | +2.1 | +0.0 |
| Fri 30 Oct | -5.1 | +0.0 |
| Mon 02 Nov | +42.6 | +12.2 |
| Tue 03 Nov | -27.8 | +7.3 |
| Wed 04 Nov | -17.9 | +0.0 |
| Thu 05 Nov | -8.0 | -2.3 |
| Fri 06 Nov | +25.6 | +0.0 |

### Bollinger bounce by the analyser's state at entry

| | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 (26-30 Oct) | Week 2 (2-6 Nov) | Profit from one day or week |
|---|---|---|---|---|---|---|---|---|---|
| ranging | 2 | 0 | 2 | **-9.7** | -6.0 | 2 | -3.7 | -6.0 |  |
| emerging trend | 57 | 20 | 37 | **-25.5** | -6.0 | 7 | -19.8 | -5.7 |  |
| trend | 11 | 4 | 7 | **-4.6** | -6.0 | 2 | +0.3 | -4.9 |  |
| possible reversal | 6 | 4 | 2 | **+25.6** | -6.0 | 1 | -5.5 | +31.1 | one day: Mon 02 Nov gives +25.0 of +25.6; one week: week 2 gives +31.1 of +25.6 |

### Not taken

- Bollinger bounce: outside 06:00-20:30 UK: 174
- Bollinger bounce: a sell already open: 137
- Bollinger bounce: a buy already open: 129
- Bollinger bounce: in a big-news window: 6
- range trade: outside 06:00-20:30 UK: 3
- range trade: one already open: 1

## Every Bollinger bounce trade

| Entry (UK) | Dir | Entry | State at entry | Half close at the band | Exit | Exit time | Exit pips | Trade pips |
|---|---|---|---|---|---|---|---|---|
| Mon 26 Oct 07:20 | SELL | 13366.0 | emerging trend down | - | rejection at a level (turning_high 13341.7, london_session_low 13346.2) | 09:05 | +14.0 | **+14.0** |
| Mon 26 Oct 09:55 | SELL | 13344.1 | trend down, slow grind | - | stop | 10:15 | -6.0 | **-6.0** |
| Mon 26 Oct 11:55 | SELL | 13348.9 | emerging trend down | - | rejection at a level (turning_high 13341.7, london_session_low 13341.8, new_york_session_low 13345.4) | 12:20 | -4.2 | **-4.2** |
| Mon 26 Oct 12:40 | SELL | 13349.5 | emerging trend down | - | stop | 12:50 | -6.0 | **-6.0** |
| Mon 26 Oct 13:05 | SELL | 13352.0 | emerging trend down | - | rejection at a level (S3 13328.6, new_york_session_low 13335.5, turning_low 13336.2, turning_high 13336.4) | 14:10 | +14.7 | **+14.7** |
| Mon 26 Oct 15:45 | SELL | 13341.6 | trend down, slow grind | - | stop | 15:55 | -6.0 | **-6.0** |
| Mon 26 Oct 19:00 | SELL | 13349.0 | emerging trend down | - | 20:30 | 20:30 | +6.7 | **+6.7** |
| Tue 27 Oct 06:00 | SELL | 13331.9 | trend down, slow grind | - | rejection at a level (S1 13318.4, london_session_low 13320.6) | 07:20 | +6.5 | **+6.5** |
| Tue 27 Oct 08:50 | SELL | 13318.8 | emerging trend down | - | stop | 08:55 | -6.0 | **-6.0** |
| Tue 27 Oct 09:10 | SELL | 13318.4 | emerging trend down | - | rejection at a level (turning_low 13306.5, london_session_low 13308.1, turning_low 13309.9) | 09:55 | +1.2 | **+1.2** |
| Tue 27 Oct 10:35 | SELL | 13312.6 | emerging trend down | - | stop | 10:45 | -6.0 | **-6.0** |
| Tue 27 Oct 11:40 | SELL | 13318.9 | emerging trend down | - | stop | 12:05 | -6.0 | **-6.0** |
| Tue 27 Oct 13:30 | SELL | 13319.5 | emerging trend down | - | rejection at a level (new_york_session_low 13316.6) | 14:00 | -3.0 | **-3.0** |
| Tue 27 Oct 15:15 | SELL | 13313.7 | emerging trend down | - | stop | 15:30 | -6.0 | **-6.0** |
| Tue 27 Oct 15:45 | SELL | 13311.3 | emerging trend down | - | rejection at a level (new_york_session_low 13305.7, turning_low 13306.5, london_session_low 13307.2, turning_low 13307.2) | 16:40 | +0.5 | **+0.5** |
| Tue 27 Oct 17:35 | SELL | 13314.9 | emerging trend down | - | rejection at a level (new_york_session_low 13304.6, turning_low 13306.5, london_session_low 13307.2, turning_low 13307.2) | 18:15 | +2.7 | **+2.7** |
| Tue 27 Oct 18:50 | SELL | 13312.4 | emerging trend down | - | rejection at a level (turning_low 13306.5, london_session_low 13307.2, turning_low 13307.2, turning_low 13309.9) | 19:05 | -4.1 | **-4.1** |
| Tue 27 Oct 20:00 | SELL | 13313.1 | emerging trend down | - | 20:30 | 20:30 | +2.9 | **+2.9** |
| Wed 28 Oct 06:35 | SELL | 13281.7 | emerging trend down | - | rejection at a level (turning_high 13270.7, turning_high 13275.1, london_session_low 13275.6) | 07:25 | +2.1 | **+2.1** |
| Wed 28 Oct 08:40 | SELL | 13291.0 | emerging trend down | - | stop | 09:10 | -6.0 | **-6.0** |
| Wed 28 Oct 09:45 | SELL | 13285.1 | emerging trend down | - | rejection at a level (turning_high 13277.8) | 10:35 | -2.6 | **-2.6** |
| Wed 28 Oct 10:45 | SELL | 13279.5 | trend down, slow grind | - | rejection at a level (london_session_low 13272.5, turning_low 13272.5, turning_high 13275.1) | 11:15 | -3.1 | **-3.1** |
| Wed 28 Oct 12:30 | SELL | 13287.3 | emerging trend down | - | stop | 12:35 | -6.0 | **-6.0** |
| Wed 28 Oct 18:45 | BUY | 13337.4 (buy 13338.9) | emerging trend up | - | stop | 18:50 | -6.0 | **-6.0** |
| Thu 29 Oct 06:55 | SELL | 13308.2 | trend down, slow grind | - | stop | 07:05 | -6.0 | **-6.0** |
| Thu 29 Oct 07:50 | BUY | 13326.3 (buy 13327.2) | emerging trend up | - | stop | 08:05 | -6.0 | **-6.0** |
| Thu 29 Oct 08:50 | SELL | 13304.7 | emerging trend down | - | stop | 08:55 | -6.0 | **-6.0** |
| Thu 29 Oct 09:15 | SELL | 13304.8 | emerging trend down | - | rejection at a level (london_session_high 13296.4, turning_high 13296.4, round_number 13300, turning_low 13300.6, london_session_low 13302.4, turning_low 13302.5) | 09:35 | -0.3 | **-0.3** |
| Thu 29 Oct 14:45 | BUY | 13349.7 (buy 13350.6) | emerging trend up | - | rejection at a level (turning_low 13376.1, R2 13377.1, turning_low 13378.7, new_york_session_high 13379.4) | 16:30 | +16.8 | **+16.8** |
| Thu 29 Oct 20:10 | BUY | 13376.9 (buy 13377.8) | emerging trend up | - | 20:30 | 20:30 | +3.6 | **+3.6** |
| Fri 30 Oct 06:10 | BUY | 13394.0 (buy 13394.9) | ranging none | - | rejection at a level (round_number 13400, turning_high 13400.6, turning_high 13401.5, turning_high 13403.2) | 06:40 | -3.7 | **-3.7** |
| Fri 30 Oct 07:10 | BUY | 13399.5 (buy 13400.4) | emerging trend up | - | rejection at a level (london_session_high 13410.6, R1 13412.7) | 07:45 | +1.2 | **+1.2** |
| Fri 30 Oct 08:15 | BUY | 13413.8 (buy 13414.7) | trend up, slow grind | - | rejection at a level (london_session_high 13432.3) | 11:20 | +14.9 | **+14.9** |
| Fri 30 Oct 11:20 | SELL | 13429.6 | possible reversal down | - | rejection at a level (new_york_session_low 13421.3) | 12:20 | +0.5 | **+0.5** |
| Fri 30 Oct 15:25 | BUY | 13391.5 (buy 13392.4) | possible reversal up | - | stop | 15:45 | -6.0 | **-6.0** |
| Fri 30 Oct 16:05 | BUY | 13402.0 (buy 13402.9) | emerging trend up | - | stop | 16:25 | -6.0 | **-6.0** |
| Fri 30 Oct 19:15 | BUY | 13396.8 (buy 13397.7) | emerging trend up | - | stop | 19:30 | -6.0 | **-6.0** |
| Mon 02 Nov 06:40 | BUY | 13397.1 (buy 13398.0) | emerging trend up | - | rejection at a level (london_session_high 13448.0, round_number 13450) | 09:25 | +38.7 | **+38.7** |
| Mon 02 Nov 09:25 | SELL | 13436.7 | possible reversal down | - | rejection at a level (round_number 13400, london_session_low 13400.1, turning_high 13400.6, turning_high 13401.5, turning_high 13403.2) | 11:05 | +25.0 | **+25.0** |
| Mon 02 Nov 11:05 | BUY | 13410.8 (buy 13411.7) | emerging trend up | - | rejection at a level (new_york_session_high 13423.2) | 13:25 | +2.0 | **+2.0** |
| Mon 02 Nov 14:30 | BUY | 13422.2 (buy 13423.1) | emerging trend up | - | stop | 14:40 | -6.0 | **-6.0** |
| Mon 02 Nov 15:10 | BUY | 13425.1 (buy 13426.0) | emerging trend up | - | stop | 15:15 | -6.0 | **-6.0** |
| Mon 02 Nov 16:20 | BUY | 13415.9 (buy 13416.8) | emerging trend up | - | rejection at a level (turning_high 13418.6) | 16:45 | -5.1 | **-5.1** |
| Mon 02 Nov 17:00 | BUY | 13418.4 (buy 13419.9) | emerging trend up | - | stop | 17:45 | -6.0 | **-6.0** |
| Tue 03 Nov 06:20 | BUY | 13415.5 (buy 13417.0) | trend up, slow grind | - | stop | 06:40 | -6.0 | **-6.0** |
| Tue 03 Nov 07:00 | BUY | 13412.3 (buy 13413.8) | emerging trend up | - | rejection at a level (london_session_high 13423.0) | 08:20 | +5.5 | **+5.5** |
| Tue 03 Nov 09:25 | BUY | 13416.4 (buy 13417.9) | emerging trend up | - | stop | 10:00 | -6.0 | **-6.0** |
| Tue 03 Nov 10:05 | SELL | 13408.0 | ranging none | - | stop | 10:30 | -6.0 | **-6.0** |
| Tue 03 Nov 10:35 | BUY | 13413.6 (buy 13415.1) | emerging trend up | - | stop | 11:00 | -6.0 | **-6.0** |
| Tue 03 Nov 11:10 | SELL | 13408.6 | emerging trend down | - | rejection at a level (round_number 13400, london_session_low 13400.1, turning_high 13400.6, turning_high 13401.5, new_york_session_low 13402.5, turning_high 13403.2, london_session_low 13405.5, turning_high 13406.0, turning_high 13406.5) | 11:50 | -1.2 | **-1.2** |
| Tue 03 Nov 12:05 | BUY | 13412.3 (buy 13413.8) | emerging trend up | - | stop | 12:30 | -6.0 | **-6.0** |
| Tue 03 Nov 12:55 | BUY | 13411.8 (buy 13413.3) | emerging trend up | - | rejection at a level (turning_high 13418.6, new_york_session_high 13419.3, london_session_high 13426.4, turning_high 13426.4) | 13:50 | +3.7 | **+3.7** |
| Tue 03 Nov 14:50 | BUY | 13430.0 (buy 13431.5) | emerging trend up | - | stop | 14:55 | -6.0 | **-6.0** |
| Tue 03 Nov 15:55 | BUY | 13415.4 (buy 13416.3) | emerging trend up | - | stop | 16:40 | -6.0 | **-6.0** |
| Tue 03 Nov 17:00 | BUY | 13417.2 (buy 13418.1) | emerging trend up | - | rejection at a level (new_york_session_high 13430.3, turning_high 13430.3) | 18:30 | +6.2 | **+6.2** |
| Wed 04 Nov 06:40 | BUY | 13459.3 (buy 13460.8) | emerging trend up | - | stop | 07:00 | -6.0 | **-6.0** |
| Wed 04 Nov 07:20 | BUY | 13465.7 (buy 13467.2) | emerging trend up | - | rejection at a level (london_session_high 13498.2) | 11:00 | +8.3 | **+8.3** |
| Wed 04 Nov 11:00 | SELL | 13475.5 | possible reversal down | - | stop | 11:30 | -6.0 | **-6.0** |
| Wed 04 Nov 12:25 | BUY | 13493.2 (buy 13494.7) | emerging trend up | - | stop | 12:30 | -6.0 | **-6.0** |
| Wed 04 Nov 12:30 | BUY | 13498.9 (buy 13500.4) | emerging trend up | - | stop | 12:30 | -6.0 | **-6.0** |
| Wed 04 Nov 12:55 | BUY | 13494.9 (buy 13496.4) | emerging trend up | - | rejection at a level (round_number 13500, new_york_session_high 13501.4) | 13:25 | -2.5 | **-2.5** |
| Wed 04 Nov 20:20 | BUY | 13471.8 (buy 13472.7) | emerging trend up | - | 20:30 | 20:30 | +0.3 | **+0.3** |
| Thu 05 Nov 09:50 | SELL | 13461.7 | emerging trend down | - | stop | 10:05 | -6.0 | **-6.0** |
| Thu 05 Nov 10:35 | SELL | 13458.4 | trend down, slow grind | - | stop | 10:50 | -6.0 | **-6.0** |
| Thu 05 Nov 11:05 | SELL | 13459.2 | trend down, slow grind | - | news (BoE Interest Rate Decision) | 11:45 | +3.8 | **+3.8** |
| Thu 05 Nov 13:10 | SELL | 13458.0 | emerging trend down | - | stop | 13:25 | -6.0 | **-6.0** |
| Thu 05 Nov 16:20 | BUY | 13468.8 (buy 13470.3) | emerging trend up | - | rejection at a level (new_york_session_high 13484.6) | 17:40 | +8.0 | **+8.0** |
| Thu 05 Nov 18:45 | SELL | 13460.9 | emerging trend down | - | rejection at a level (new_york_session_low 13453.3, turning_low 13453.3, london_session_low 13454.6) | 19:00 | -1.8 | **-1.8** |
| Fri 06 Nov 06:45 | SELL | 13419.0 | emerging trend down | - | rejection at a level (turning_low 13396.1, S2 13399.1, round_number 13400, london_session_low 13400.1, turning_low 13401.7, turning_low 13402.7) | 07:50 | +16.0 | **+16.0** |
| Fri 06 Nov 08:25 | SELL | 13398.5 | trend down, slow grind | - | rejection at a level (turning_low 13378.4, turning_low 13380.2, london_session_low 13382.6) | 10:35 | +9.3 | **+9.3** |
| Fri 06 Nov 10:35 | BUY | 13388.3 (buy 13389.2) | possible reversal up | - | rejection at a level (turning_low 13401.7, new_york_session_high 13402.2, turning_low 13402.7, turning_high 13406.0, turning_high 13406.5) | 12:45 | +3.1 | **+3.1** |
| Fri 06 Nov 13:10 | SELL | 13383.3 | emerging trend down | - | news (Non Farm Payrolls) | 13:15 | -4.0 | **-4.0** |
| Fri 06 Nov 14:00 | SELL | 13356.8 | trend down, strong push | - | stop | 14:35 | -6.0 | **-6.0** |
| Fri 06 Nov 14:35 | BUY | 13357.4 (buy 13358.9) | possible reversal up | - | rejection at a level (turning_low 13373.9, turning_low 13378.4) | 15:35 | +9.0 | **+9.0** |
| Fri 06 Nov 17:50 | SELL | 13355.2 | emerging trend down | - | rejection at a level (turning_high 13348.1, turning_low 13348.7, round_number 13350) | 18:40 | -1.3 | **-1.3** |
| Fri 06 Nov 19:15 | SELL | 13353.1 | emerging trend down | - | rejection at a level (turning_high 13348.1, turning_low 13348.7) | 20:05 | -0.5 | **-0.5** |

## Every range trade

| Entry (UK) | Dir | Entry | State at entry | Half close at the band | Exit | Exit time | Exit pips | Trade pips |
|---|---|---|---|---|---|---|---|---|
| Mon 26 Oct 11:50 | SELL | 13351.1 | ranging none | 12:05: +6.0 | rejection at a level (turning_high 13341.7, london_session_low 13341.8, new_york_session_low 13345.4) | 12:20 | -2.0 | **+2.0** |
| Tue 27 Oct 17:30 | SELL | 13316.1 | ranging none | not reached | rejection at a level (new_york_session_low 13304.6, turning_low 13306.5, london_session_low 13307.2, turning_low 13307.2) | 18:15 | +3.9 | **+3.9** |
| Mon 02 Nov 14:20 | BUY | 13414.2 (buy 13415.1) | ranging none | 14:35: +10.1 | rejection at a level (turning_high 13418.6) | 16:00 | -0.3 | **+4.9** |
| Mon 02 Nov 17:35 | SELL | 13417.7 | ranging none | 18:15: +4.0 | rejection at a level (round_number 13400, london_session_low 13400.1, turning_high 13400.6, turning_high 13401.5, turning_high 13403.2, new_york_session_low 13405.0) | 18:55 | +10.6 | **+7.3** |
| Tue 03 Nov 10:00 | SELL | 13417.5 | ranging none | 10:00: +3.1 | rejection at a level (new_york_session_low 13402.5, turning_high 13403.2, turning_high 13406.0, turning_high 13406.5, turning_high 13406.7, london_session_low 13406.9, turning_high 13407.4, turning_high 13409.2) | 10:35 | +2.4 | **+2.7** |
| Tue 03 Nov 12:50 | BUY | 13409.6 (buy 13411.1) | ranging none | 13:10: +3.3 | rejection at a level (turning_high 13418.6, new_york_session_high 13419.3, london_session_high 13426.4, turning_high 13426.4) | 13:50 | +5.9 | **+4.6** |
| Thu 05 Nov 06:05 | BUY | 13491.1 (buy 13492.6) | ranging none | 06:30: +1.4 | stop | 07:15 | -6.0 | **-2.3** |
