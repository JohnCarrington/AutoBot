# All six strategies together, 26 October to 6 November 2026

Read-only replay on the stored GBPUSD candles (Sunday 25 October 21:00 UK to Friday 6 November close), on IG's prices, through the bot's own code. Nothing in the bot was changed. Written 8 November 2026.

## Method

- **Ideas:** every idea of the six strategies from the bot's own replay (`strategies/replay.py`: the EMA pullback, Bollinger bounce, range trade, breakout, slow grind and level reversal, each with its current settings), kept only when the bot's checks allowed it (its switch, the analyser's state, the direction rule where it applies). All six switched on.
- **The rules between them**, in time order (several ideas on one candle in the replay's order: breakout, slow grind, EMA pullback, bounce, range trade, level reversal), all from `strategies/common.py` and design sections 4 and 6:
  - each strategy's **hours and news rules** (`may_open`);
  - **each strategy's own limit:** one trade at a time, except the bounce (one each way) and the EMA pullback (no limit);
  - **most at once: 5**, every open trade except the EMA pullback's counted (`counts_towards_most_at_once`). An idea refused only because 5 such trades were already open is **lost to the limits because of the others**;
  - **stops:** 6 pips (bounce, range trade, breakout), 12 (EMA pullback), 15 (slow grind), the level reversal's 6 beyond the furthest point; **take profits:** 100 (bounce, range trade), 50 (breakout), 20 (level reversal), 30 (EMA pullback) and 20 (slow grind), each 100 on a big-news day (5 and 6 November) or in a trend day's direction (`take_profit_pips`; there were **no trend days** in these two weeks);
  - **closes:** 20:30 UK every day (bounce, range trade, slow grind, level reversal), Friday 20:30 UK only (EMA pullback, breakout); closed 15 minutes before big news (bounce, range trade, level reversal; BoE Thu 5 Nov 12:00, payrolls Fri 6 Nov 13:30); the slow grind's profit lock 15/10; the **range trade's 50% close at the opposite band** (the band at the last finished candle; the rest managed as before); the **close on a rejection at a level** against the trade for the bounce and the range trade (the analyser's rejection part: a bounce the other way at a level that counts, by section 4's reversal watch times or levels lining up, triggering after the entry candle; closed at its trigger).
- **Not applied:** total risk and available funds (section 6) have no figures in the settings yet; size is £10 a pip for every trade, so pips are shown.
- **IG's prices:** a buy opens on the buy price and closes on the sell price, a sell the reverse. Inside a candle: a scheduled close at its open; then the stop or lock; then the half close; then the take profit; then the close on a rejection. The entry-candle stop correction as before. Weeks and days by entry time (UK).

**Limits:** two weeks only; 5-minute candles, not ticks; no slippage beyond candle-open gaps; GBPUSD only.

## Results

| Strategy | Trades | Won | Lost | Total pips | Biggest loss | Worst losing run | Week 1 | Week 2 | Most open at once |
|---|---|---|---|---|---|---|---|---|---|
| EMA pullback | 59 | 26 | 33 | **+686.4** | -12.0 | 9 | +90.0 | +596.4 | 10 (Fri 06 Nov 13:30) |
| Bollinger bounce | 44 | 18 | 26 | **+28.4** | -6.0 | 12 | +50.4 | -22.0 | 1 (Mon 26 Oct 06:00) |
| range trade | 7 | 6 | 1 | **+23.2** | -2.3 | 1 | +5.9 | +17.3 | 1 (Mon 26 Oct 11:50) |
| breakout | 11 | 3 | 8 | **+52.4** | -9.4 | 7 | +44.0 | +8.4 | 1 (Tue 27 Oct 07:00) |
| slow grind | 18 | 12 | 5 | **+217.9** | -15.0 | 2 | +115.0 | +102.9 | 1 (Mon 26 Oct 06:05) |
| level reversal | 22 | 9 | 13 | **+16.2** | -17.4 | 4 | -24.7 | +40.9 | 1 (Mon 26 Oct 13:55) |
| **The whole bot** | 161 | 74 | 86 | **+1024.5** | -17.4 | 7 | +280.6 | +743.9 | 11 (Fri 06 Nov 10:35) |

Counted towards "most at once: 5" (every trade but the EMA pullback's), the most open at once was **3** (Tue 27 Oct 07:20).

## Pips for each day (by entry day)

| Day | EMA pullback | Bollinger bounce | range trade | breakout | slow grind | level reversal | **Whole bot** |
|---|---|---|---|---|---|---|---|
| Mon 26 Oct | +24.0 (5) | +3.4 (4) | +2.0 (1) | - | +30.0 (2) | -17.3 (2) | **+42.1** |
| Tue 27 Oct | +48.0 (3) | -0.9 (4) | +3.9 (1) | -6.0 (1) | +20.0 (2) | - | **+65.0** |
| Wed 28 Oct | -24.0 (2) | -5.9 (7) | - | - | +15.0 (3) | -31.9 (2) | **-46.8** |
| Thu 29 Oct | +30.0 (1) | +65.8 (4) | - | +50.0 (1) | +20.0 (1) | +25.1 (3) | **+190.9** |
| Fri 30 Oct | +12.0 (6) | -12.0 (5) | - | - | +30.0 (2) | -0.6 (3) | **+29.4** |
| Mon 02 Nov | +30.0 (8) | +28.3 (2) | +12.2 (2) | - | +18.2 (2) | +9.3 (3) | **+98.0** |
| Tue 03 Nov | -48.0 (4) | -4.6 (2) | +7.4 (2) | -24.0 (4) | - | +20.0 (1) | **-49.2** |
| Wed 04 Nov | +84.0 (14) | -42.0 (7) | - | -9.4 (1) | -10.0 (3) | +25.8 (4) | **+48.4** |
| Thu 05 Nov | -36.0 (3) | -11.3 (6) | -2.3 (1) | +38.0 (3) | -5.3 (2) | +20.0 (1) | **+3.1** |
| Fri 06 Nov | +566.4 (13) | +7.6 (3) | - | +3.8 (1) | +100.0 (1) | -34.2 (3) | **+643.6** |

(The number of trades in brackets.)

## Trades lost to the limits because of the others

**None.** The 5-trade limit never refused a trade: at most 3 trades that count towards it were open at once. No other limit in section 6 depends on another strategy (each strategy's own one-at-a-time limit, hours and news rules apply to it alone), so every strategy took exactly the trades it takes when run on its own:

| Strategy | Alone: trades, pips | Together: trades, pips | Trades that differ |
|---|---|---|---|
| EMA pullback | 59, +686.4 | 59, +686.4 | 0 |
| Bollinger bounce | 44, +28.4 | 44, +28.4 | 0 |
| range trade | 7, +23.2 | 7, +23.2 | 0 |
| breakout | 11, +52.4 | 11, +52.4 | 0 |
| slow grind | 18, +217.9 | 18, +217.9 | 0 |
| level reversal | 22, +16.2 | 22, +16.2 | 0 |

Ideas allowed by the checks but not taken, by reason (each strategy's own rules, not the others):

| Strategy | Hours or news | Its own trade already open |
|---|---|---|
| EMA pullback | 3 | 0 |
| Bollinger bounce | 77 | 152 |
| range trade | 3 | 1 |
| breakout | 13 | 1 |
| slow grind | 4 | 30 |
| level reversal | 40 | 44 |

## How the trades closed

| Strategy | stop | profit lock | take profit | rejection at a level | 20:30 close | closed before big news | open at the end |
|---|---|---|---|---|---|---|---|
| EMA pullback | 32 | 0 | 17 | 0 | 10 | 0 | 0 |
| Bollinger bounce | 23 | 0 | 0 | 19 | 2 | 0 | 0 |
| range trade | 1 | 0 | 0 | 6 | 0 | 0 | 0 |
| breakout | 8 | 0 | 2 | 0 | 1 | 0 | 0 |
| slow grind | 4 | 4 | 8 | 0 | 2 | 0 | 0 |
| level reversal | 8 | 0 | 8 | 0 | 5 | 1 | 0 |

The range trade half-closed at the opposite band on 6 of its 7 trades. The EMA pullback's and the breakout's "20:30 close" is Friday's.

## Reading it

- **The whole bot:** 161 trades, **+1024.5 pips** (week 1 +280.6, week 2 +743.9). The EMA pullback made +686.4 of it, most of that in week 2 (the big-news days' 100-pip take profit).
- **The strategies did not get in each other's way:** the counted trades never went above 3 at once, so the 5-trade limit never came into play and nothing was lost. The EMA pullback, which is not counted, had up to 10 trades open at once.
- The bounce took 44 of its 273 allowed ideas: its own one-each-way limit (152) and its hours and news rules (77) stopped the rest.
- Two weeks only: one strong fortnight for the EMA pullback dominates the total.

## Every trade

### EMA pullback (59)

| Entry | Dir | Entry price | State at entry | Closed | How | Pips |
|---|---|---|---|---|---|---|
| Mon 26 Oct 08:35 | SELL | 13349.3 | trend down, slow grind | Tue 27 Oct 07:05 | take profit 30 | +30.0 |
| Mon 26 Oct 08:35 | SELL | 13349.3 | trend down, slow grind | Tue 27 Oct 07:05 | take profit 30 | +30.0 |
| Mon 26 Oct 12:05 | SELL | 13343.5 | emerging trend down | Mon 26 Oct 12:25 | stop | -12.0 |
| Mon 26 Oct 13:55 | SELL | 13332.5 | emerging trend down | Mon 26 Oct 14:30 | stop | -12.0 |
| Mon 26 Oct 13:55 | SELL | 13332.5 | emerging trend down | Mon 26 Oct 14:30 | stop | -12.0 |
| Tue 27 Oct 16:15 | SELL | 13305.5 | trend down, slow grind | Tue 27 Oct 17:00 | stop | -12.0 |
| Tue 27 Oct 17:55 | SELL | 13311.6 | emerging trend down | Wed 28 Oct 06:40 | take profit 30 | +30.0 |
| Tue 27 Oct 19:55 | SELL | 13313.3 | emerging trend down | Wed 28 Oct 06:30 | take profit 30 | +30.0 |
| Wed 28 Oct 10:45 | SELL | 13276.8 | trend down, slow grind | Wed 28 Oct 11:35 | stop | -12.0 |
| Wed 28 Oct 10:45 | SELL | 13276.8 | trend down, slow grind | Wed 28 Oct 11:35 | stop | -12.0 |
| Thu 29 Oct 22:05 | BUY | 13382.4 | trend up, slow grind | Fri 30 Oct 08:25 | take profit 30 | +30.0 |
| Fri 30 Oct 00:40 | BUY | 13389.2 | trend up, slow grind | Fri 30 Oct 09:15 | take profit 30 | +30.0 |
| Fri 30 Oct 03:00 | BUY | 13397.3 | emerging trend up | Fri 30 Oct 04:50 | stop | -12.0 |
| Fri 30 Oct 07:10 | BUY | 13400.0 | emerging trend up | Fri 30 Oct 09:45 | take profit 30 | +30.0 |
| Fri 30 Oct 09:15 | BUY | 13420.4 | trend up, slow grind | Fri 30 Oct 12:40 | stop | -12.0 |
| Fri 30 Oct 09:15 | BUY | 13420.4 | trend up, slow grind | Fri 30 Oct 12:40 | stop | -12.0 |
| Fri 30 Oct 11:10 | BUY | 13433.6 | trend up, slow grind | Fri 30 Oct 12:00 | stop | -12.0 |
| Mon 02 Nov 07:20 | BUY | 13408.4 | emerging trend up | Mon 02 Nov 08:50 | take profit 30 | +30.0 |
| Mon 02 Nov 07:20 | BUY | 13408.4 | emerging trend up | Mon 02 Nov 08:50 | take profit 30 | +30.0 |
| Mon 02 Nov 07:20 | BUY | 13408.4 | emerging trend up | Mon 02 Nov 08:50 | take profit 30 | +30.0 |
| Mon 02 Nov 08:30 | BUY | 13420.6 | trend up, slow grind | Mon 02 Nov 10:25 | stop | -12.0 |
| Mon 02 Nov 08:30 | BUY | 13420.6 | trend up, slow grind | Mon 02 Nov 10:25 | stop | -12.0 |
| Mon 02 Nov 12:25 | BUY | 13421.8 | emerging trend up | Mon 02 Nov 13:55 | stop | -12.0 |
| Mon 02 Nov 14:30 | BUY | 13421.9 | emerging trend up | Mon 02 Nov 16:00 | stop | -12.0 |
| Mon 02 Nov 17:00 | BUY | 13421.6 | emerging trend up | Mon 02 Nov 18:15 | stop | -12.0 |
| Tue 03 Nov 08:05 | BUY | 13425.6 | emerging trend up | Tue 03 Nov 08:30 | stop | -12.0 |
| Tue 03 Nov 14:50 | BUY | 13428.8 | emerging trend up | Tue 03 Nov 15:10 | stop | -12.0 |
| Tue 03 Nov 18:05 | BUY | 13424.8 | emerging trend up | Tue 03 Nov 20:00 | stop | -12.0 |
| Tue 03 Nov 18:05 | BUY | 13424.8 | emerging trend up | Tue 03 Nov 20:00 | stop | -12.0 |
| Wed 04 Nov 01:00 | BUY | 13446.3 | trend up, slow grind | Wed 04 Nov 04:35 | take profit 30 | +30.0 |
| Wed 04 Nov 01:00 | BUY | 13446.3 | trend up, slow grind | Wed 04 Nov 04:35 | take profit 30 | +30.0 |
| Wed 04 Nov 01:00 | BUY | 13445.2 | trend up, slow grind | Wed 04 Nov 04:35 | take profit 30 | +30.0 |
| Wed 04 Nov 02:35 | BUY | 13468.9 | emerging trend up | Wed 04 Nov 03:15 | stop | -12.0 |
| Wed 04 Nov 02:35 | BUY | 13468.9 | emerging trend up | Wed 04 Nov 03:15 | stop | -12.0 |
| Wed 04 Nov 04:05 | BUY | 13472.3 | emerging trend up | Wed 04 Nov 04:50 | stop | -12.0 |
| Wed 04 Nov 04:35 | BUY | 13476.9 | emerging trend up | Wed 04 Nov 04:40 | stop | -12.0 |
| Wed 04 Nov 04:35 | BUY | 13476.9 | emerging trend up | Wed 04 Nov 04:40 | stop | -12.0 |
| Wed 04 Nov 05:45 | BUY | 13458.6 | emerging trend up | Wed 04 Nov 08:45 | take profit 30 | +30.0 |
| Wed 04 Nov 06:50 | BUY | 13460.9 | emerging trend up | Wed 04 Nov 09:15 | take profit 30 | +30.0 |
| Wed 04 Nov 07:20 | BUY | 13465.8 | emerging trend up | Wed 04 Nov 10:15 | take profit 30 | +30.0 |
| Wed 04 Nov 08:40 | BUY | 13486.0 | trend up, slow grind | Wed 04 Nov 10:40 | stop | -12.0 |
| Wed 04 Nov 08:45 | BUY | 13487.5 | trend up, slow grind | Wed 04 Nov 10:40 | stop | -12.0 |
| Wed 04 Nov 10:15 | BUY | 13497.6 | trend up, slow grind | Wed 04 Nov 10:30 | stop | -12.0 |
| Thu 05 Nov 04:00 | BUY | 13495.2 | emerging trend up | Thu 05 Nov 07:20 | stop | -12.0 |
| Thu 05 Nov 07:00 | BUY | 13497.7 | emerging trend up | Thu 05 Nov 07:15 | stop | -12.0 |
| Thu 05 Nov 22:00 | SELL | 13441.9 | emerging trend down | Thu 05 Nov 22:00 | stop | -12.0 |
| Fri 06 Nov 02:00 | SELL | 13443.9 | trend down, slow grind | Fri 06 Nov 14:15 | take profit 100 | +100.0 |
| Fri 06 Nov 02:55 | SELL | 13442.1 | emerging trend down | Fri 06 Nov 20:30 | 20:30 close | +90.7 |
| Fri 06 Nov 04:10 | SELL | 13425.7 | trend down, slow grind | Fri 06 Nov 20:30 | 20:30 close | +74.3 |
| Fri 06 Nov 04:10 | SELL | 13425.7 | trend down, slow grind | Fri 06 Nov 20:30 | 20:30 close | +74.3 |
| Fri 06 Nov 06:45 | SELL | 13417.7 | emerging trend down | Fri 06 Nov 20:30 | 20:30 close | +66.3 |
| Fri 06 Nov 06:45 | SELL | 13417.7 | emerging trend down | Fri 06 Nov 20:30 | 20:30 close | +66.3 |
| Fri 06 Nov 08:40 | SELL | 13394.3 | trend down, slow grind | Fri 06 Nov 20:30 | 20:30 close | +42.9 |
| Fri 06 Nov 08:40 | SELL | 13393.4 | trend down, slow grind | Fri 06 Nov 12:20 | stop | -12.0 |
| Fri 06 Nov 09:00 | SELL | 13390.1 | trend down, slow grind | Fri 06 Nov 11:25 | stop | -12.0 |
| Fri 06 Nov 13:30 | SELL | 13377.5 | trend down, slow grind | Fri 06 Nov 20:30 | 20:30 close | +26.1 |
| Fri 06 Nov 13:30 | SELL | 13377.5 | trend down, slow grind | Fri 06 Nov 20:30 | 20:30 close | +26.1 |
| Fri 06 Nov 13:30 | SELL | 13377.5 | trend down, slow grind | Fri 06 Nov 20:30 | 20:30 close | +26.1 |
| Fri 06 Nov 19:50 | SELL | 13348.7 | emerging trend down | Fri 06 Nov 20:30 | 20:30 close | -2.7 |

### Bollinger bounce (44)

| Entry | Dir | Entry price | State at entry | Closed | How | Pips |
|---|---|---|---|---|---|---|
| Mon 26 Oct 06:00 | BUY | 13374.0 | trend down, slow grind | Mon 26 Oct 06:10 | stop | -6.0 |
| Mon 26 Oct 09:05 | BUY | 13351.1 | trend down, slow grind | Mon 26 Oct 09:30 | stop | -6.0 |
| Mon 26 Oct 14:10 | BUY | 13336.4 | trend down, slow grind | Mon 26 Oct 15:45 | rejection at previous_day_low 13348.7, turning_low 13348.7, round_number 13350 | +4.3 |
| Mon 26 Oct 17:50 | SELL | 13353.4 | trend up, slow grind | Mon 26 Oct 20:30 | 20:30 close | +11.1 |
| Tue 27 Oct 07:20 | BUY | 13324.5 | trend down, slow grind | Tue 27 Oct 08:10 | rejection at previous_day_low 13327.1, new_york_session_low 13327.1, turning_low 13327.1, turning_low 13327.8, london_session_high 13329.6 | -5.0 |
| Tue 27 Oct 09:55 | BUY | 13316.3 | trend down, slow grind | Tue 27 Oct 10:35 | stop | -6.0 |
| Tue 27 Oct 12:35 | SELL | 13328.5 | trend up, slow grind | Tue 27 Oct 14:00 | rejection at new_york_session_low 13316.6 | +6.0 |
| Tue 27 Oct 16:40 | BUY | 13309.9 | trend down, slow grind | Tue 27 Oct 17:35 | rejection at S1 13318.4 | +4.1 |
| Wed 28 Oct 07:25 | BUY | 13278.7 | trend down, slow grind | Wed 28 Oct 08:40 | rejection at london_session_high 13295.1, previous_day_low 13295.5, new_york_session_low 13296.4 | +11.4 |
| Wed 28 Oct 10:35 | BUY | 13286.8 | trend down, slow grind | Wed 28 Oct 10:40 | stop | -6.0 |
| Wed 28 Oct 11:15 | BUY | 13281.7 | trend down, slow grind | Wed 28 Oct 12:30 | rejection at turning_low 13291.1, new_york_session_high 13292.8, previous_day_low 13295.5, london_session_high 13296.4, new_york_session_low 13296.4 | +4.7 |
| Wed 28 Oct 13:55 | SELL | 13294.3 | trend up, slow grind | Wed 28 Oct 14:35 | rejection at S1 13284.2, new_york_session_low 13284.4, turning_low 13291.1 | +1.4 |
| Wed 28 Oct 15:20 | SELL | 13300.5 | trend up, slow grind | Wed 28 Oct 15:35 | rejection at round_number 13300, turning_low 13300.6 | -5.4 |
| Wed 28 Oct 15:50 | SELL | 13295.1 | trend up, slow grind | Wed 28 Oct 15:55 | stop | -6.0 |
| Wed 28 Oct 17:05 | SELL | 13313.0 | trend up, slow grind | Wed 28 Oct 18:35 | stop | -6.0 |
| Thu 29 Oct 06:30 | BUY | 13312.0 | trend down, slow grind | Thu 29 Oct 06:55 | stop | -6.0 |
| Thu 29 Oct 08:15 | SELL | 13315.4 | trend up, slow grind | Thu 29 Oct 09:35 | rejection at london_session_high 13296.4, turning_high 13296.4, round_number 13300, turning_low 13300.6, london_session_low 13302.4, turning_low 13302.5 | +10.3 |
| Thu 29 Oct 09:35 | BUY | 13304.2 | trend down, slow grind | Thu 29 Oct 12:00 | rejection at london_session_high 13332.0, turning_high 13334.5 | +15.4 |
| Thu 29 Oct 13:30 | BUY | 13320.4 | trend down, slow grind | Thu 29 Oct 16:30 | rejection at turning_low 13376.1, R2 13377.1, turning_low 13378.7, new_york_session_high 13379.4 | +46.1 |
| Fri 30 Oct 07:45 | SELL | 13401.6 | trend up, slow grind | Fri 30 Oct 08:00 | stop | -6.0 |
| Fri 30 Oct 10:40 | SELL | 13425.8 | trend up, slow grind | Fri 30 Oct 11:00 | stop | -6.0 |
| Fri 30 Oct 11:20 | SELL | 13429.6 | possible reversal down | Fri 30 Oct 12:20 | rejection at new_york_session_low 13421.3 | +0.5 |
| Fri 30 Oct 15:25 | BUY | 13391.5 | possible reversal up | Fri 30 Oct 15:45 | stop | -6.0 |
| Fri 30 Oct 16:25 | SELL | 13397.4 | trend up, slow grind | Fri 30 Oct 18:10 | rejection at turning_low 13380.2, turning_low 13382.3, turning_low 13382.8, new_york_session_high 13384.4 | +5.5 |
| Mon 02 Nov 09:25 | SELL | 13436.7 | possible reversal down | Mon 02 Nov 11:05 | rejection at round_number 13400, london_session_low 13400.1, turning_high 13400.6, turning_high 13401.5, turning_high 13403.2 | +25.0 |
| Mon 02 Nov 18:55 | BUY | 13405.7 | trend down, slow grind | Mon 02 Nov 20:30 | 20:30 close | +3.3 |
| Tue 03 Nov 06:45 | SELL | 13408.8 | trend up, slow grind | Tue 03 Nov 07:00 | stop | -6.0 |
| Tue 03 Nov 08:20 | SELL | 13419.3 | trend up, slow grind | Tue 03 Nov 09:25 | rejection at pivot 13411.6 | +1.4 |
| Wed 04 Nov 10:40 | SELL | 13479.1 | trend up, slow grind | Wed 04 Nov 11:40 | stop | -6.0 |
| Wed 04 Nov 13:25 | SELL | 13493.9 | trend up, slow grind | Wed 04 Nov 13:30 | stop | -6.0 |
| Wed 04 Nov 14:00 | SELL | 13483.5 | trend up, slow grind | Wed 04 Nov 14:05 | stop | -6.0 |
| Wed 04 Nov 14:30 | SELL | 13484.4 | trend up, slow grind | Wed 04 Nov 14:30 | stop | -6.0 |
| Wed 04 Nov 14:30 | SELL | 13484.4 | trend up, slow grind | Wed 04 Nov 14:30 | stop | -6.0 |
| Wed 04 Nov 15:40 | BUY | 13469.4 | trend down, slow grind | Wed 04 Nov 16:10 | stop | -6.0 |
| Wed 04 Nov 17:10 | BUY | 13468.3 | trend down, slow grind | Wed 04 Nov 18:30 | stop | -6.0 |
| Thu 05 Nov 07:50 | BUY | 13475.8 | trend down, strong push | Thu 05 Nov 07:55 | stop | -6.0 |
| Thu 05 Nov 08:15 | BUY | 13479.3 | trend down, slow grind | Thu 05 Nov 08:25 | stop | -6.0 |
| Thu 05 Nov 08:50 | BUY | 13478.6 | trend down, slow grind | Thu 05 Nov 09:10 | stop | -6.0 |
| Thu 05 Nov 17:40 | SELL | 13478.3 | trend up, slow grind | Thu 05 Nov 17:40 | stop | -6.0 |
| Thu 05 Nov 17:40 | SELL | 13478.3 | trend up, slow grind | Thu 05 Nov 17:40 | stop | -6.0 |
| Thu 05 Nov 18:00 | SELL | 13481.4 | trend up, slow grind | Thu 05 Nov 19:00 | rejection at new_york_session_low 13453.3, turning_low 13453.3, london_session_low 13454.6 | +18.7 |
| Fri 06 Nov 07:50 | BUY | 13402.1 | trend down, slow grind | Fri 06 Nov 08:25 | rejection at turning_low 13401.7, turning_low 13402.7, turning_high 13406.0, turning_high 13406.5 | -4.5 |
| Fri 06 Nov 10:35 | BUY | 13388.3 | possible reversal up | Fri 06 Nov 12:45 | rejection at turning_low 13401.7, new_york_session_high 13402.2, turning_low 13402.7, turning_high 13406.0, turning_high 13406.5 | +3.1 |
| Fri 06 Nov 14:35 | BUY | 13357.4 | possible reversal up | Fri 06 Nov 15:35 | rejection at turning_low 13373.9, turning_low 13378.4 | +9.0 |

### range trade (7)

| Entry | Dir | Entry price | State at entry | Closed | How | Pips |
|---|---|---|---|---|---|---|
| Mon 26 Oct 11:50 | SELL | 13351.1 | ranging none | Mon 26 Oct 12:20 | rejection at turning_high 13341.7, london_session_low 13341.8, new_york_session_low 13345.4; half closed at the opposite band Mon 12:05 (+6.0) | +2.0 |
| Tue 27 Oct 17:30 | SELL | 13316.1 | ranging none | Tue 27 Oct 18:15 | rejection at new_york_session_low 13304.6, turning_low 13306.5, london_session_low 13307.2, turning_low 13307.2 | +3.9 |
| Mon 02 Nov 14:20 | BUY | 13414.2 | ranging none | Mon 02 Nov 16:00 | rejection at turning_high 13418.6; half closed at the opposite band Mon 14:35 (+10.1) | +4.9 |
| Mon 02 Nov 17:35 | SELL | 13417.7 | ranging none | Mon 02 Nov 18:55 | rejection at round_number 13400, london_session_low 13400.1, turning_high 13400.6, turning_high 13401.5, turning_high 13403.2, new_york_session_low 13405.0; half closed at the opposite band Mon 18:15 (+4.0) | +7.3 |
| Tue 03 Nov 10:00 | SELL | 13417.5 | ranging none | Tue 03 Nov 10:35 | rejection at new_york_session_low 13402.5, turning_high 13403.2, turning_high 13406.0, turning_high 13406.5, turning_high 13406.7, london_session_low 13406.9, turning_high 13407.4, turning_high 13409.2; half closed at the opposite band Tue 10:00 (+3.1) | +2.8 |
| Tue 03 Nov 12:50 | BUY | 13409.6 | ranging none | Tue 03 Nov 13:50 | rejection at turning_high 13418.6, new_york_session_high 13419.3, london_session_high 13426.4, turning_high 13426.4; half closed at the opposite band Tue 13:10 (+3.3) | +4.6 |
| Thu 05 Nov 06:05 | BUY | 13491.1 | ranging none | Thu 05 Nov 07:15 | stop; half closed at the opposite band Thu 06:30 (+1.4) | -2.3 |

### breakout (11)

| Entry | Dir | Entry price | State at entry | Closed | How | Pips |
|---|---|---|---|---|---|---|
| Tue 27 Oct 07:00 | SELL | 13326.0 | emerging trend down | Tue 27 Oct 12:10 | stop | -6.0 |
| Thu 29 Oct 14:45 | BUY | 13349.7 | emerging trend up | Fri 30 Oct 01:05 | take profit 50 | +50.0 |
| Tue 03 Nov 10:15 | SELL | 13406.9 | emerging trend down | Tue 03 Nov 10:30 | stop | -6.0 |
| Tue 03 Nov 13:45 | BUY | 13428.5 | emerging trend up | Tue 03 Nov 13:45 | stop | -6.0 |
| Tue 03 Nov 14:50 | BUY | 13430.0 | emerging trend up | Tue 03 Nov 14:55 | stop | -6.0 |
| Tue 03 Nov 18:05 | BUY | 13423.5 | emerging trend up | Tue 03 Nov 19:10 | stop | -6.0 |
| Wed 04 Nov 20:05 | BUY | 13470.6 | emerging trend up | Wed 04 Nov 22:00 | stop | -9.4 |
| Thu 05 Nov 07:00 | BUY | 13497.2 | emerging trend up | Thu 05 Nov 07:10 | stop | -6.0 |
| Thu 05 Nov 09:50 | SELL | 13461.7 | emerging trend down | Thu 05 Nov 10:05 | stop | -6.0 |
| Thu 05 Nov 18:35 | SELL | 13468.2 | emerging trend down | Fri 06 Nov 06:45 | take profit 50 | +50.0 |
| Fri 06 Nov 17:50 | SELL | 13355.2 | emerging trend down | Fri 06 Nov 20:30 | 20:30 close | +3.8 |

### slow grind (18)

| Entry | Dir | Entry price | State at entry | Closed | How | Pips |
|---|---|---|---|---|---|---|
| Mon 26 Oct 06:05 | SELL | 13371.1 | trend down, slow grind | Mon 26 Oct 08:05 | profit lock | +10.0 |
| Mon 26 Oct 08:25 | SELL | 13355.5 | trend down, slow grind | Mon 26 Oct 13:55 | take profit 20 | +20.0 |
| Tue 27 Oct 05:45 | SELL | 13331.5 | trend down, slow grind | Tue 27 Oct 09:30 | take profit 20 | +20.0 |
| Tue 27 Oct 16:05 | SELL | 13310.2 | trend down, slow grind | Tue 27 Oct 20:30 | 20:30 close | +0.0 |
| Wed 28 Oct 04:45 | SELL | 13294.1 | trend down, slow grind | Wed 28 Oct 07:15 | take profit 20 | +20.0 |
| Wed 28 Oct 10:20 | SELL | 13280.3 | trend down, slow grind | Wed 28 Oct 13:30 | stop | -15.0 |
| Wed 28 Oct 15:30 | BUY | 13303.0 | trend up, slow grind | Wed 28 Oct 17:00 | profit lock | +10.0 |
| Thu 29 Oct 05:05 | SELL | 13318.6 | trend down, slow grind | Thu 29 Oct 09:20 | take profit 20 | +20.0 |
| Fri 30 Oct 08:15 | BUY | 13411.8 | trend up, slow grind | Fri 30 Oct 11:05 | take profit 20 | +20.0 |
| Fri 30 Oct 13:20 | SELL | 13394.0 | trend down, slow grind | Fri 30 Oct 14:10 | profit lock | +10.0 |
| Mon 02 Nov 08:00 | BUY | 13415.7 | trend up, slow grind | Mon 02 Nov 08:45 | take profit 20 | +20.0 |
| Mon 02 Nov 19:40 | SELL | 13409.5 | trend down, slow grind | Mon 02 Nov 20:30 | 20:30 close | -1.8 |
| Wed 04 Nov 00:15 | BUY | 13432.8 | trend up, strong push | Wed 04 Nov 01:15 | take profit 20 | +20.0 |
| Wed 04 Nov 08:30 | BUY | 13484.3 | trend up, slow grind | Wed 04 Nov 11:05 | stop | -15.0 |
| Wed 04 Nov 15:35 | SELL | 13462.8 | trend down, strong push | Wed 04 Nov 17:25 | stop | -15.0 |
| Thu 05 Nov 08:00 | SELL | 13469.9 | trend down, strong push | Thu 05 Nov 12:00 | profit lock | +9.7 |
| Thu 05 Nov 17:45 | BUY | 13483.2 | trend up, slow grind | Thu 05 Nov 18:30 | stop | -15.0 |
| Fri 06 Nov 01:55 | SELL | 13447.1 | trend down, slow grind | Fri 06 Nov 14:15 | take profit 100 | +100.0 |

### level reversal (22)

| Entry | Dir | Entry price | State at entry | Closed | How | Pips |
|---|---|---|---|---|---|---|
| Mon 26 Oct 13:55 | SELL | 13336.3 | emerging trend down | Mon 26 Oct 14:45 | stop | -12.7 |
| Mon 26 Oct 14:45 | BUY | 13345.1 | trend down, slow grind | Mon 26 Oct 20:30 | 20:30 close | -4.6 |
| Wed 28 Oct 13:55 | SELL | 13294.3 | trend up, slow grind | Wed 28 Oct 16:15 | stop | -15.5 |
| Wed 28 Oct 16:15 | BUY | 13308.6 | trend up, slow grind | Wed 28 Oct 18:30 | stop | -16.4 |
| Thu 29 Oct 09:35 | BUY | 13304.2 | trend down, slow grind | Thu 29 Oct 10:55 | take profit 20 | +20.0 |
| Thu 29 Oct 13:30 | BUY | 13320.4 | trend down, slow grind | Thu 29 Oct 14:20 | take profit 20 | +20.0 |
| Thu 29 Oct 16:30 | SELL | 13367.4 | emerging trend down | Thu 29 Oct 20:30 | 20:30 close | -14.9 |
| Fri 30 Oct 06:40 | SELL | 13391.2 | emerging trend down | Fri 30 Oct 07:20 | stop | -16.5 |
| Fri 30 Oct 07:25 | BUY | 13410.6 | emerging trend up | Fri 30 Oct 10:05 | take profit 20 | +20.0 |
| Fri 30 Oct 13:25 | SELL | 13393.1 | trend down, slow grind | Fri 30 Oct 20:30 | 20:30 close | -4.1 |
| Mon 02 Nov 06:00 | SELL | 13397.7 | emerging trend down | Mon 02 Nov 07:20 | stop | -9.4 |
| Mon 02 Nov 07:25 | BUY | 13409.5 | trend up, slow grind | Mon 02 Nov 08:40 | take profit 20 | +20.0 |
| Mon 02 Nov 11:05 | BUY | 13410.8 | emerging trend up | Mon 02 Nov 20:30 | 20:30 close | -1.3 |
| Tue 03 Nov 11:50 | BUY | 13408.3 | emerging trend up | Tue 03 Nov 13:30 | take profit 20 | +20.0 |
| Wed 04 Nov 06:15 | SELL | 13453.0 | emerging trend down | Wed 04 Nov 07:25 | stop | -17.4 |
| Wed 04 Nov 07:25 | BUY | 13467.6 | emerging trend up | Wed 04 Nov 08:45 | take profit 20 | +20.0 |
| Wed 04 Nov 12:40 | SELL | 13487.4 | emerging trend down | Wed 04 Nov 15:15 | take profit 20 | +20.0 |
| Wed 04 Nov 17:10 | BUY | 13468.3 | trend down, slow grind | Wed 04 Nov 20:30 | 20:30 close | +3.2 |
| Thu 05 Nov 07:15 | SELL | 13488.7 | emerging trend down | Thu 05 Nov 08:00 | take profit 20 | +20.0 |
| Fri 06 Nov 07:50 | BUY | 13402.1 | trend down, slow grind | Fri 06 Nov 09:00 | stop | -14.9 |
| Fri 06 Nov 12:20 | BUY | 13402.2 | emerging trend up | Fri 06 Nov 12:45 | stop | -15.3 |
| Fri 06 Nov 13:10 | SELL | 13383.3 | emerging trend down | Fri 06 Nov 13:15 | closed 15 minutes before big news | -4.0 |

