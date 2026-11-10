# Why the live trades are losing: entry conditions and trade management, 9 to 10 November 2026

Read-only investigation. **Nothing in the bot was changed.** Written Tuesday 10 November 2026, about 13:40 UK.

## Summary

**The live result.** 20 trades at IG: 4 won, 16 lost, **-62.9 pips (-£629.00)**. Monday made -25.7 and Tuesday -37.2. Over 26 October to 6 November the same code made +1056.1 pips in 152 trades. But 676.0 of those pips came from one day, Friday 6 November, a big-news day with an expected direction, when the EMA pullback alone made +566.4 in 13 trades. Without that Friday the replay makes +380.1 in 136 trades (+2.8 a trade). Neither live day was like it. Monday followed a big Friday and went up, then sideways, then down and up again. Tuesday was a big-news day with no expected direction, and its strong push down started at 13:35 UK, after the last trade.

**Three trades were closed by IG, not by the bot.** On Monday at 15:21 UK, IG's own system closed the breakout, level reversal and slow grind buys at the market price, not at their stops or take profits. The bot did not notice. It kept treating them as open and later marked them closed by price alone, and its trade records have no close for any of the three. IG booked -12.2 pips for the three. On the bot's own prices, left alone they would have made +55.0. That is 67.2 pips, more than the whole live loss. Why IG closed them is not in the records read here. The bot also records its own decision price rather than IG's fill, so its records show the losses 0.1 to 3.3 pips worse than IG booked them.

**How the 20 trades ended:**
- **7 never got 5 pips up**, for -59.5 pips: almost the whole loss.
- **9 closed too early**, for -22.2 pips. Price then went another 208.7 pips their way within 2 hours:
  - 5 were stopped at 6 pips within minutes, and then price went 15 to 37 pips in their direction: both Tuesday breakouts, two Tuesday bounces and one range trade.
  - 3 were the trades IG closed.
  - 1 was a slow grind that hit its 20-pip take profit; price went 18.5 further.
- **None was held too long.**
- **4 were managed about right**, for +18.8 pips.

The replay shows the same shape over 152 trades:
- **42 never got 5 pips up**, for -385.2 pips. They were short (median 34 minutes), with a median best of +1.3, reached within 5 minutes: they went wrong from the start.
- **36 closed too early**, for -14.5 pips, with 927 pips of further move left behind. 22 of them were stopped out and price then went on in their direction.
- **8 held too long**, for -64.0 pips, after giving back 215.5.
- **66 managed about right**, for +1519.8 pips.

**EMA pullback.**
- **Live:** 4 trades, all lost, all stopped at 12 pips (-48.0).
  - The three Tuesday buys (05:01, 06:12 and 07:21 UK) were all in an emerging up trend, open together, and stopped within the same four seconds at 09:00. That was the same moment the analyser's up trend ran out of steam (consolidation on the 08:55 candle, then an emerging trend down). Their best was +7.6, +5.8 and +2.5.
  - Three of the four entered with a level less than 3 pips in the way. On Tuesday 05:01, for example, the round number 13450 was 0.8 pips above.
  - The Monday 21:02 buy came 77 minutes into a slow-grind trend, was never in profit and was stopped at 22:00.
- **Replay:** +686.4 in 59 trades, but +566.4 of it in 13 trades on Friday 6 November. The other 46 made +120.0.
  - By state: +8.2 a trade in an emerging trend and +15.7 in a slow-grind trend, but +2.9 when the state was over an hour old.
  - By time of day (UK): Asia +567.9 in 19 trades, London morning +84.9 in 22, and 12:00 to 20:30 +15.6 in 16.
  - Groups: 20 of 59 never got 5 pips up (-230.7). 9 closed too early, 8 of them by the stop, after which price went on 212 pips. 4 held too long (-48.0, after giving back 125.8).

**Slow grind.**
- **Live:** 4 trades, -10.2.
  - Monday 05:25: hit its 20-pip take profit, then price went 18.5 further.
  - Monday 09:39: entered 0.4 pips under the London session high and was +9.2 at best. IG closed it at -12.7; on the bot's prices it would have been stopped at -15.
  - Monday 15:45 sell: came 10 minutes into a down slow grind, was +1.0 at best, and was stopped at -15 at 16:17, as price closed back above the 100 EMA and the analyser ended the trend.
  - Monday 19:55: +2.0 at best, closed by the 20:30 close at -2.5.
- **Replay:** +217.9 in 18 trades, 12 won. Asia 6 of 6 for +190.0; the New York afternoon -16.8 in 3. Ten were managed about right; 5 closed too early, two of them by the 15/10 lock.

**Breakout.**
- **Live:** 3 trades, -0.3.
  - Monday 07:55: was +33.5 at best. IG closed it at +11.7; on the bot's prices it would have reached its 50-pip take profit that evening.
  - Tuesday 09:10 and 11:50 sells: each was stopped at 6 pips within 14 and 12 minutes (best +0.6 and -2.5). Each had entered with a level 1 pip or less below it, in its way. Price then fell another 15.3 and 36.7 pips within 2 hours.
- **Replay:** +52.4 in 11 trades: 3 won, 8 lost. 5 never got 5 pips up. 4 closed too early, 3 of them stopped before price went on. London morning 0 of 4 (-24.0); 12:00 to 20:30 +76.4 in 7.

**Level reversal.**
- **Live:** 2 trades, +8.8.
  - Monday 06:12: hit its 20-pip take profit.
  - Monday 08:25: entered 2.9 pips under the London session high and was +11.1 at best. IG closed it at -11.2; on the bot's prices it would have reached its take profit later.
- **Replay:** +56.2 in 20 trades, 10 won.
  - By time of day: London morning 7 of 8 (+124.5); Asia 0 of 3 (-43.3); the New York afternoon -28.1.
  - By time in the state: within 15 minutes of the state starting, +108.7 in 11 trades; later, -52.5 in 9.
  - By room to the next level: 8 pips or more, 4 of 4 for +63.2; 3 to 8 pips, 3 of 10 for -21.4.
  - Its 3 held-too-long trades gave back 60 pips, the most for a strategy of its size.

**Bollinger bounce.**
- **Live:** 4 trades, +4.8, all sells against a slow-grind up trend in the London morning.
  - Monday 09:00: lost -6 (best +0.7).
  - Tuesday 07:55 and 08:20: stopped at 6 pips after 6 and 4 minutes. Price then fell 32.1 and 31.4 pips within 2 hours.
  - Tuesday 08:45: the third sell caught that fall. It was +30.3 at best and was closed by the bot on a rejection at the London session low, at +22.8.
- **Replay:** +20.1 in 37 trades (+0.5 a trade).
  - By state: the 34 in a slow-grind trend made +0.6 together; the 3 in a possible reversal made +19.5.
  - By time in the state: entered over an hour into the state, 1 of 10 won (-49.3); within 15 minutes, +67.1 in 15.
  - Groups: 12 closed too early (-23.1), leaving 328.3 pips behind, the most of any strategy; 8 of those were stopped at 6 pips before price went their way. 11 never got 5 pips up (-64.4). 13 were managed about right (+113.6).

**Range trade.**
- **Live:** 3 buys on Monday afternoon (13:55, 14:55 and 15:16), all in ranging, all stopped at -6 within 4 to 48 minutes. The best any of them reached was +2.2. Price kept falling, and the analyser called an emerging trend down on the 15:25 candle. After the third was stopped, price went 18 pips its way.
- **Replay:** 7 trades, 6 won, +23.1.

**Signals the bot already has, while trades were open** (all 172 trades together):
- **A strong push against an open trade never happened**, live or replay. Consolidation after a push happened twice, both times in winning trades.
- **A strong push in the trade's favour** came in 22 trades, which made +859.6 (+39.1 average). Of the 21 that were already 10 pips up when it came, 2 closed at a loss. 9 trades had one in their first 30 minutes: none of them ended in group c.
- **After a trade was 10 pips up** (82 trades), the MACD histogram crossing in its favour came in 37. Only 2 of those closed at a loss (+34.9 average), against 12 of the 45 without it (+9.5 average).
- **Of the 14 trades that were 10 pips up and still closed at a loss**, 12 had seen the analyser turn against them, 12 a rejection at a level against them, and 12 the MACD histogram cross against them, all after the 10-pip point. Those same signals also came in many trades that won (35 of 47, 27 of 39 and 27 of 39).
- **In the first 30 minutes:**
  - The analyser turning against the trade came in 14 trades. Half ended in group c (-5.3 average).
  - RSI(3) stretched against the trade came in 36 trades: 16 in group c (-1.2 average).
  - A rejection at a level in the trade's favour came in 105 trades: 18 in group c (+8.9). Of the 67 without one, 31 were in group c (+0.9).
  - The MACD histogram crossing in the trade's favour came in 27 trades: 2 in group c (+16.9 average).
- **Signals that separate little:** RSI(3) stretched in the trade's favour comes in almost every trade (150 of 172), so it separates little. The MACD and RSI at entry made no clear difference.
- **Bounces and range trades** already close on a rejection at a level against them, so that signal shows as 0% for them.

**How sure this is.** The live sample is 20 trades over a day and a half, and the replay is two weeks with one exceptional Friday. These are indications, not proof. No rule changes are proposed here.

## Method and sources

- **Live trades: all 20** since trading went on (Monday 9 November 05:25 UK to Tuesday 10 November 12:02 UK, the last close before this was written). Each is taken from **IG's own records**, read with the owner's read-only IG records check (`orders/ig_records.py`, inside the price service, on its own login: IG's activity and transactions for 9 November and for 10 November up to 13:10 UTC). Entry and close times, fill and close prices, pips and £ are IG's. Every trade's pips times £10 equals IG's booked profit or loss to the penny. The strategy, the entry (trigger) price, the stop and take profit pips and the kind of take profit come from the bot's records, matched to IG by deal ID.
- **Replay: 152 trades**, Monday 26 October to Friday 6 November, through the bot's full wired path as it runs now (`trading/replay_check.py`'s `wired_trades`: the analyser, the six strategies, the safety rules with the one-view-at-a-time rules, the order sender in paper mode, the trade manager), candle by candle on the stored IG candles. It gives 152 trades and +1056.1 pips, exactly the first two weeks of rank 1 in `one_view_20261109.md` (+280.6 and +775.5).
- **The analyser** was replayed for each week from the stored candles (`StateTracker`, as the bot runs it). For the live week its state changes were checked against the bot's own journal (`data/analyser/GBPUSD/state_changes.jsonl`): 72 of 72 the same, none different. So the states below are the states the live bot had.
- **The state at entry** is the last state change decided on a candle that had finished before the entry. "In that state for" counts from the end of that candle.
- **Nearest levels**: the bot's full level list as it stood at the entry time (`levels.current.build`), the nearest above and below the strategy's entry price, with the distance in pips.
- **Day**: big news = a big release for GBP or USD that day in the bot's calendar (`news.calendar.big_news_windows`), with its expected direction if it has one; trend day = `analyser/trend_day.py`; Monday after a big Friday = Friday's daily candle moved 80 pips or more (`analyser/day_direction.py`).
- **With or against the trend**: against the analyser's direction in an emerging trend or a trend; in a possible reversal, against the trend being reversed; ranging and consolidation have no trend.
- **Best and worst** are on the price the trade closes on (bid for a buy, offer for a sell), from its fill, on the 5-minute candles. The entry candle counts only by its close and the close candle only by the close price, because the order of the high and low inside those candles cannot be known. So best and worst are, if anything, slightly understated.
- **The 2 hours after the close** are measured from the close price, on the same side, over the next 24 candles (into the next week's first candles where the market closed).
- **Classes**, as asked, in this order (a trade is put in the first one it meets; where it met more than one, the others are shown): a. closed too early: price went 15 pips or more further its way within 2 hours of the close; b. held too long: it was 10 pips or more up at some point and closed at a loss; c. should never have opened: it never reached 5 pips up; d. managed about right: none of these. "Left behind" for a is the further move after the close; for b, the best less the result.
- **Signals** are things the bot already works out, counted when they happened while the trade was open (decided on a candle that finished after the entry and by the close): the analyser's state changes, a strong push, consolidation within 60 minutes of the end of a strong push, a confirmed rejection at a level (the rejection part's trigger at a level that counts, not a Bollinger band), the MACD histogram crossing zero, and RSI(3) beyond 70 or 30 (the settings' lines).
- **Limits:** 20 live trades over a day and a half, and two weeks of replay. 5-minute candles, not ticks. Live and replay trades are reported apart, and the live sample is far too small to prove anything on its own.

## What IG's records show that the bot's records do not

| Entry (UK) | Strategy | IG: closed (UK) | IG: how | IG: pips | The bot's record |
|---|---|---|---|---|---|
| Mon 09 Nov 07:55 | breakout buy | Mon 09 Nov 15:21 | closed by IG's system at market (not at its stop or take profit) | +11.7 | take profit hit at IG (orders file only; no closed trade record), Mon 09 Nov 21:01 at 13442.5 |
| Mon 09 Nov 08:25 | level reversal buy | Mon 09 Nov 15:21 | closed by IG's system at market (not at its stop or take profit) | -11.2 | take profit hit at IG (orders file only; no closed trade record), Mon 09 Nov 19:38 at 13434.9 |
| Mon 09 Nov 09:39 | slow grind buy | Mon 09 Nov 15:21 | closed by IG's system at market (not at its stop or take profit) | -12.7 | stopped by IG (orders file only; no closed trade record), Mon 09 Nov 15:26 at 13401.8 |
| Mon 09 Nov 13:55 | range trade buy | Mon 09 Nov 14:43 | stop at IG | -6.0 | stopped by IG, Mon 09 Nov 14:43 at 13411.9, -6.7 pips |
| Mon 09 Nov 14:55 | range trade buy | Mon 09 Nov 14:58 | stop at IG | -6.0 | stopped by IG, Mon 09 Nov 14:58 at 13408.9, -6.4 pips |
| Mon 09 Nov 15:16 | range trade buy | Mon 09 Nov 15:20 | stop at IG | -6.0 | stopped by IG, Mon 09 Nov 15:20 at 13404.5, -6.4 pips |
| Mon 09 Nov 21:02 | EMA pullback buy | Mon 09 Nov 22:00 | stop at IG | -12.0 | stopped by IG, Mon 09 Nov 22:00 at 13428.3, -15.3 pips |
| Tue 10 Nov 05:01 | EMA pullback buy | Tue 10 Nov 09:00 | stop at IG | -12.0 | stopped by IG, Tue 10 Nov 09:00 at 13438.1, -12.9 pips |
| Tue 10 Nov 06:12 | EMA pullback buy | Tue 10 Nov 09:00 | stop at IG | -12.0 | stopped by IG, Tue 10 Nov 09:00 at 13440.6, -12.2 pips |
| Tue 10 Nov 07:55 | Bollinger bounce sell | Tue 10 Nov 08:01 | stop at IG | -6.0 | stopped by IG, Tue 10 Nov 08:01 at 13456.1, -6.5 pips |
| Tue 10 Nov 08:20 | Bollinger bounce sell | Tue 10 Nov 08:24 | stop at IG | -6.0 | stopped by IG, Tue 10 Nov 08:24 at 13455.1, -6.2 pips |
| Tue 10 Nov 08:45 | Bollinger bounce sell | Tue 10 Nov 10:45 | closed by the bot | +22.8 | close, Tue 10 Nov 10:40 at 13431.9, 21.8 pips |
| Tue 10 Nov 09:10 | breakout sell | Tue 10 Nov 09:24 | stop at IG | -6.0 | stopped by IG, Tue 10 Nov 09:24 at 13439.2, -6.5 pips |
| Tue 10 Nov 11:50 | breakout sell | Tue 10 Nov 12:02 | stop at IG | -6.0 | stopped by IG, Tue 10 Nov 12:02 at 13429.0, -6.3 pips |

- **Three trades were closed by IG's system at the market price at 15:21 UK on Monday**, within 7 seconds of each other, not at their stops or take profits (IG's activity: channel SYSTEM, description "Position/s closed", close levels 13404.1, 13403.7 and 13404.2). The bot did not send these closes and did not notice them: it went on treating the trades as open and later marked them closed by price alone (the slow grind "stopped" at 15:26; the level reversal and the breakout "take profit hit" at 19:38 and 21:01). Its trade records (`trades.jsonl`) have no closed entry for any of the three. IG booked -12.7, -11.2 and +11.7 (-12.2 pips together). On the bot's own prices, left alone they would have ended at -15.0, +20.0 and +50.0 (+55.0 together). Why IG closed them is not in the records read here.
- IG also shows a cash entry of +£80,000.00 at 00:08 UTC on Monday 9 November (reference CS26307403101794182924883984), before any trade.
- Elsewhere the bot records its own decision price, not IG's fill: losses on stops are recorded 0.1 to 3.3 pips worse than IG booked (the Monday 21:02 EMA pullback: -15.3 recorded, -12.0 at IG), and the Tuesday 08:45 bounce's close +21.8 recorded, +22.8 at IG (decided on the 10:40 candle, sent at 10:45:01).
- **Totals on IG's figures:** 20 trades, 4 won, 16 lost, -62.9 pips (£-629.00). Monday -25.7, Tuesday -37.2.

| Strategy | Live trades | Won | Lost | Live pips | Replay trades | Replay won | Replay pips | Replay average |
|---|---|---|---|---|---|---|---|---|
| EMA pullback | 4 | 0 | 4 | -48.0 | 59 | 26 | +686.4 | +11.6 |
| slow grind | 4 | 1 | 3 | -10.2 | 18 | 12 | +217.9 | +12.1 |
| breakout | 3 | 1 | 2 | -0.3 | 11 | 3 | +52.4 | +4.8 |
| level reversal | 2 | 1 | 1 | +8.8 | 20 | 10 | +56.2 | +2.8 |
| Bollinger bounce | 4 | 1 | 3 | +4.8 | 37 | 15 | +20.1 | +0.5 |
| range trade | 3 | 0 | 3 | -18.0 | 7 | 6 | +23.1 | +3.3 |
| **All** | 20 | 4 | 16 | -62.9 | 152 | 72 | +1056.1 | +6.9 |

## 1. The conditions at entry

### Live trades

Monday 9 November was the Monday after Friday 6 November fell 107.6 pips (direction: up). Tuesday 10 November was a big-news day (US inflation at 13:30 UK, no expected direction in the calendar). Neither day was a trend day.

| # | Entry (UK) | Strategy | Dir | Analyser at entry | In that state for | Nearest level above (type price, pips) | Nearest level below | Day | Time of day | With or against the trend | Pips |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Mon 09 Nov 05:25 | slow grind | buy | trend up, slow grind | 10m | R2 13379.4 (0.7) | turning_low 13378.4 (0.3) | Monday after a Friday of -107.6 (big) | Asia (00-07) | with the trend | +20.0 |
| 2 | Mon 09 Nov 06:12 | level reversal | buy | emerging trend up | 2m | turning_low 13396.1 (12.5) | london_session_low 13380.7 (2.9) | Monday after a Friday of -107.6 (big) | Asia (00-07) | with the trend | +20.0 |
| 3 | Mon 09 Nov 07:55 | breakout | buy | emerging trend up | 0m | turning_low 13396.1 (4.8) | london_session_low 13381.8 (9.5) | Monday after a Friday of -107.6 (big) | London morning (07-12) | with the trend | +11.7 |
| 4 | Mon 09 Nov 08:25 | level reversal | buy | emerging trend up | 30m | london_session_high 13416.1 (2.9) | turning_high 13406.5 (6.7) | Monday after a Friday of -107.6 (big) | London morning (07-12) | with the trend | -11.2 |
| 5 | Mon 09 Nov 09:00 | Bollinger bounce | sell | trend up, slow grind | 5m | london_session_high 13415.5 (7.3) | turning_high 13406.5 (1.7) | Monday after a Friday of -107.6 (big) | London morning (07-12) | against the trend | -6.0 |
| 6 | Mon 09 Nov 09:39 | slow grind | buy | trend up, slow grind | 44m | london_session_high 13415.5 (0.4) | turning_high 13406.5 (8.6) | Monday after a Friday of -107.6 (big) | London morning (07-12) | with the trend | -12.7 |
| 7 | Mon 09 Nov 13:55 | range trade | buy | ranging | 0m | new_york_session_high 13421.2 (4.2) | london_session_high 13416.1 (0.9) | Monday after a Friday of -107.6 (big) | London/New York (12-16) | no trend | -6.0 |
| 8 | Mon 09 Nov 14:55 | range trade | buy | ranging | 15m | london_session_high 13416.1 (1.9) | new_york_session_low 13408 (6.2) | Monday after a Friday of -107.6 (big) | London/New York (12-16) | no trend | -6.0 |
| 9 | Mon 09 Nov 15:16 | range trade | buy | ranging | 36m | london_session_high 13416.1 (6.3) | turning_high 13406.5 (3.3) | Monday after a Friday of -107.6 (big) | London/New York (12-16) | no trend | -6.0 |
| 10 | Mon 09 Nov 15:45 | slow grind | sell | trend down, slow grind | 10m | turning_low 13401.7 (0.3) | round_number 13400 (1.4) | Monday after a Friday of -107.6 (big) | London/New York (12-16) | with the trend | -15.0 |
| 11 | Mon 09 Nov 19:55 | slow grind | buy | trend up, slow grind | 10m | new_york_session_high 13441.9 (4.9) | turning_low 13435.7 (1.3) | Monday after a Friday of -107.6 (big) | New York afternoon (16-20:30) | with the trend | -2.5 |
| 12 | Mon 09 Nov 21:02 | EMA pullback | buy | trend up, slow grind | 1h17 | turning_low 13445.2 (2.5) | new_york_session_high 13441.9 (0.8) | Monday after a Friday of -107.6 (big) | evening (20:30-24) | with the trend | -12.0 |
| 13 | Tue 10 Nov 05:01 | EMA pullback | buy | emerging trend up | 21m | round_number 13450 (0.8) | turning_high 13448.0 (1.2) | big news (no expected direction; USD Core Inflation Rate MoM 13:30 and 3 more) | Asia (00-07) | with the trend | -12.0 |
| 14 | Tue 10 Nov 06:12 | EMA pullback | buy | emerging trend up | 12m | turning_low 13453.3 (2.2) | round_number 13450 (1.1) | big news (no expected direction; USD Core Inflation Rate MoM 13:30 and 3 more) | Asia (00-07) | with the trend | -12.0 |
| 15 | Tue 10 Nov 07:21 | EMA pullback | buy | emerging trend up | 16m | turning_high 13463.3 (8.8) | london_session_high 13453.7 (0.8) | big news (no expected direction; USD Core Inflation Rate MoM 13:30 and 3 more) | London morning (07-12) | with the trend | -12.0 |
| 16 | Tue 10 Nov 07:55 | Bollinger bounce | sell | trend up, slow grind | 10m | turning_low 13453.3 (3.0) | round_number 13450 (0.3) | big news (no expected direction; USD Core Inflation Rate MoM 13:30 and 3 more) | London morning (07-12) | against the trend | -6.0 |
| 17 | Tue 10 Nov 08:20 | Bollinger bounce | sell | trend up, slow grind | 35m | round_number 13450 (0.8) | turning_high 13448.0 (1.2) | big news (no expected direction; USD Core Inflation Rate MoM 13:30 and 3 more) | London morning (07-12) | against the trend | -6.0 |
| 18 | Tue 10 Nov 08:45 | Bollinger bounce | sell | trend up, slow grind | 1h00 | london_session_high 13458.6 (4.9) | turning_low 13453.3 (0.4) | big news (no expected direction; USD Core Inflation Rate MoM 13:30 and 3 more) | London morning (07-12) | against the trend | +22.8 |
| 19 | Tue 10 Nov 09:10 | breakout | sell | emerging trend down | 5m | turning_high 13433.7 (1.1) | turning_high 13432.5 (0.1) | big news (no expected direction; USD Core Inflation Rate MoM 13:30 and 3 more) | London morning (07-12) | with the trend | -6.0 |
| 20 | Tue 10 Nov 11:50 | breakout | sell | emerging trend down | 0m | london_session_high 13426 (3.2) | london_session_low 13421.9 (0.9) | big news (no expected direction; USD Core Inflation Rate MoM 13:30 and 3 more) | London morning (07-12) | with the trend | -6.0 |

### Replay, 26 October to 6 November (every trade)

Days: Thursday 5 November big news (expected up), Friday 6 November big news (expected down); no trend days; neither Monday followed a big Friday.

#### EMA pullback (59)

| # | Entry (UK) | Strategy | Dir | Analyser at entry | In that state for | Nearest level above (type price, pips) | Nearest level below | Day | Time of day | With or against the trend | Pips |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Mon 26 Oct 08:35 | EMA pullback | sell | trend down, slow grind | 1h05 | round_number 13350 (0.7) | previous_day_low 13348.7 (0.6) | ordinary | London morning (07-12) | with the trend | +30.0 |
| 2 | Mon 26 Oct 08:35 | EMA pullback | sell | trend down, slow grind | 1h05 | round_number 13350 (0.7) | previous_day_low 13348.7 (0.6) | ordinary | London morning (07-12) | with the trend | +30.0 |
| 3 | Mon 26 Oct 12:05 | EMA pullback | sell | emerging trend down | 10m | new_york_session_low 13345.4 (1.9) | london_session_low 13341.8 (1.7) | ordinary | London/New York (12-16) | with the trend | -12.0 |
| 4 | Mon 26 Oct 13:55 | EMA pullback | sell | emerging trend down | 50m | new_york_session_low 13335.5 (3.0) | S3 13328.6 (3.9) | ordinary | London/New York (12-16) | with the trend | -12.0 |
| 5 | Mon 26 Oct 13:55 | EMA pullback | sell | emerging trend down | 50m | new_york_session_low 13335.5 (3.0) | S3 13328.6 (3.9) | ordinary | London/New York (12-16) | with the trend | -12.0 |
| 6 | Tue 27 Oct 16:15 | EMA pullback | sell | trend down, slow grind | 20m | new_york_session_low 13305.7 (0.2) | turning_low 13300.6 (4.9) | ordinary | New York afternoon (16-20:30) | with the trend | -12.0 |
| 7 | Tue 27 Oct 17:55 | EMA pullback | sell | emerging trend down | 20m | S1 13318.4 (6.8) | turning_low 13309.9 (1.7) | ordinary | New York afternoon (16-20:30) | with the trend | +30.0 |
| 8 | Tue 27 Oct 19:55 | EMA pullback | sell | emerging trend down | 0m | S1 13318.4 (5.1) | turning_low 13309.9 (3.4) | ordinary | New York afternoon (16-20:30) | with the trend | +30.0 |
| 9 | Wed 28 Oct 10:45 | EMA pullback | sell | trend down, slow grind | 40m | turning_high 13277.8 (1.0) | turning_high 13275.1 (1.7) | ordinary | London morning (07-12) | with the trend | -12.0 |
| 10 | Wed 28 Oct 10:45 | EMA pullback | sell | trend down, slow grind | 40m | turning_high 13277.8 (1.0) | turning_high 13275.1 (1.7) | ordinary | London morning (07-12) | with the trend | -12.0 |
| 11 | Thu 29 Oct 22:05 | EMA pullback | buy | trend up, slow grind | 1h40 | turning_low 13382.8 (0.4) | turning_low 13382.3 (0.1) | ordinary | evening (20:30-24) | with the trend | +30.0 |
| 12 | Fri 30 Oct 00:40 | EMA pullback | buy | trend up, slow grind | 4h15 | round_number 13400 (10.8) | previous_day_high 13389.0 (0.2) | ordinary | Asia (00-07) | with the trend | +30.0 |
| 13 | Fri 30 Oct 03:00 | EMA pullback | buy | emerging trend up | 10m | round_number 13400 (2.7) | previous_day_high 13389.0 (8.3) | ordinary | Asia (00-07) | with the trend | -12.0 |
| 14 | Fri 30 Oct 07:10 | EMA pullback | buy | emerging trend up | 0m | turning_high 13400.6 (0.6) | london_session_high 13399.5 (0.5) | ordinary | London morning (07-12) | with the trend | +30.0 |
| 15 | Fri 30 Oct 09:15 | EMA pullback | buy | trend up, slow grind | 1h40 | R2 13447.3 (26.9) | london_session_high 13419.9 (0.5) | ordinary | London morning (07-12) | with the trend | -12.0 |
| 16 | Fri 30 Oct 09:15 | EMA pullback | buy | trend up, slow grind | 1h40 | R2 13447.3 (26.9) | london_session_high 13419.9 (0.5) | ordinary | London morning (07-12) | with the trend | -12.0 |
| 17 | Fri 30 Oct 11:10 | EMA pullback | buy | trend up, slow grind | 10m | R2 13447.3 (13.7) | london_session_high 13433.0 (0.6) | ordinary | London morning (07-12) | with the trend | -12.0 |
| 18 | Mon 02 Nov 07:20 | EMA pullback | buy | emerging trend up | 25m | turning_high 13409.2 (0.8) | turning_high 13407.4 (1.0) | ordinary | London morning (07-12) | with the trend | +30.0 |
| 19 | Mon 02 Nov 07:20 | EMA pullback | buy | emerging trend up | 25m | turning_high 13409.2 (0.8) | turning_high 13407.4 (1.0) | ordinary | London morning (07-12) | with the trend | +30.0 |
| 20 | Mon 02 Nov 07:20 | EMA pullback | buy | emerging trend up | 25m | turning_high 13409.2 (0.8) | turning_high 13407.4 (1.0) | ordinary | London morning (07-12) | with the trend | +30.0 |
| 21 | Mon 02 Nov 08:30 | EMA pullback | buy | trend up, slow grind | 1h05 | new_york_session_high 13430.9 (10.3) | london_session_high 13420.2 (0.4) | ordinary | London morning (07-12) | with the trend | -12.0 |
| 22 | Mon 02 Nov 08:30 | EMA pullback | buy | trend up, slow grind | 1h05 | new_york_session_high 13430.9 (10.3) | london_session_high 13420.2 (0.4) | ordinary | London morning (07-12) | with the trend | -12.0 |
| 23 | Mon 02 Nov 12:25 | EMA pullback | buy | emerging trend up | 1h20 | new_york_session_high 13430.9 (9.1) | new_york_session_high 13419.8 (2.0) | ordinary | London/New York (12-16) | with the trend | -12.0 |
| 24 | Mon 02 Nov 14:30 | EMA pullback | buy | emerging trend up | 0m | new_york_session_high 13430.3 (8.4) | turning_high 13418.6 (3.3) | ordinary | London/New York (12-16) | with the trend | -12.0 |
| 25 | Mon 02 Nov 17:00 | EMA pullback | buy | emerging trend up | 2h30 | new_york_session_high 13430.3 (8.7) | turning_high 13418.6 (3.0) | ordinary | New York afternoon (16-20:30) | with the trend | -12.0 |
| 26 | Tue 03 Nov 08:05 | EMA pullback | buy | emerging trend up | 40m | new_york_session_high 13430.3 (4.7) | london_session_high 13423.0 (2.6) | ordinary | London morning (07-12) | with the trend | -12.0 |
| 27 | Tue 03 Nov 14:50 | EMA pullback | buy | emerging trend up | 0m | new_york_session_high 13430.1 (1.3) | london_session_high 13426.4 (2.4) | ordinary | London/New York (12-16) | with the trend | -12.0 |
| 28 | Tue 03 Nov 18:05 | EMA pullback | buy | emerging trend up | 0m | london_session_high 13426.4 (1.6) | turning_high 13418.6 (6.2) | ordinary | New York afternoon (16-20:30) | with the trend | -12.0 |
| 29 | Tue 03 Nov 18:05 | EMA pullback | buy | emerging trend up | 0m | london_session_high 13426.4 (1.6) | turning_high 13418.6 (6.2) | ordinary | New York afternoon (16-20:30) | with the trend | -12.0 |
| 30 | Wed 04 Nov 01:00 | EMA pullback | buy | trend up, slow grind | 25m | turning_high 13448.0 (1.7) | R1 13446.0 (0.3) | ordinary | Asia (00-07) | with the trend | +30.0 |
| 31 | Wed 04 Nov 01:00 | EMA pullback | buy | trend up, slow grind | 25m | turning_high 13448.0 (1.7) | R1 13446.0 (0.3) | ordinary | Asia (00-07) | with the trend | +30.0 |
| 32 | Wed 04 Nov 01:00 | EMA pullback | buy | trend up, slow grind | 25m | R1 13446.0 (0.8) | previous_day_high 13433.9 (11.3) | ordinary | Asia (00-07) | with the trend | +30.0 |
| 33 | Wed 04 Nov 02:35 | EMA pullback | buy | emerging trend up | 10m | R3 13483.8 (14.9) | R2 13458.8 (10.1) | ordinary | Asia (00-07) | with the trend | -12.0 |
| 34 | Wed 04 Nov 02:35 | EMA pullback | buy | emerging trend up | 10m | R3 13483.8 (14.9) | R2 13458.8 (10.1) | ordinary | Asia (00-07) | with the trend | -12.0 |
| 35 | Wed 04 Nov 04:05 | EMA pullback | buy | emerging trend up | 1h40 | R3 13483.8 (11.5) | R2 13458.8 (13.5) | ordinary | Asia (00-07) | with the trend | -12.0 |
| 36 | Wed 04 Nov 04:35 | EMA pullback | buy | emerging trend up | 0m | R3 13483.8 (6.9) | R2 13458.8 (18.1) | ordinary | Asia (00-07) | with the trend | -12.0 |
| 37 | Wed 04 Nov 04:35 | EMA pullback | buy | emerging trend up | 0m | R3 13483.8 (6.9) | R2 13458.8 (18.1) | ordinary | Asia (00-07) | with the trend | -12.0 |
| 38 | Wed 04 Nov 05:45 | EMA pullback | buy | emerging trend up | 0m | R2 13458.8 (0.2) | round_number 13450 (8.6) | ordinary | Asia (00-07) | with the trend | +30.0 |
| 39 | Wed 04 Nov 06:50 | EMA pullback | buy | emerging trend up | 10m | R3 13483.8 (22.9) | R2 13458.8 (2.1) | ordinary | Asia (00-07) | with the trend | +30.0 |
| 40 | Wed 04 Nov 07:20 | EMA pullback | buy | emerging trend up | 0m | R3 13483.8 (18.0) | london_session_high 13465.7 (0.1) | ordinary | London morning (07-12) | with the trend | +30.0 |
| 41 | Wed 04 Nov 08:40 | EMA pullback | buy | trend up, slow grind | 40m | round_number 13500 (14.0) | london_session_high 13484.7 (1.3) | ordinary | London morning (07-12) | with the trend | -12.0 |
| 42 | Wed 04 Nov 08:45 | EMA pullback | buy | trend up, slow grind | 45m | round_number 13500 (12.5) | london_session_high 13486.7 (0.8) | ordinary | London morning (07-12) | with the trend | -12.0 |
| 43 | Wed 04 Nov 10:15 | EMA pullback | buy | trend up, slow grind | 2h15 | round_number 13500 (2.4) | london_session_high 13495.8 (1.8) | ordinary | London morning (07-12) | with the trend | -12.0 |
| 44 | Thu 05 Nov 04:00 | EMA pullback | buy | emerging trend up | 0m | london_session_high 13498.2 (3.0) | turning_low 13468.2 (27.0) | big news | Asia (00-07) | with the trend | -12.0 |
| 45 | Thu 05 Nov 07:00 | EMA pullback | buy | emerging trend up | 0m | london_session_high 13498.2 (0.5) | turning_low 13468.2 (29.5) | big news | London morning (07-12) | with the trend | -12.0 |
| 46 | Thu 05 Nov 22:00 | EMA pullback | sell | emerging trend down | 0m | new_york_session_low 13445.2 (3.3) | turning_high 13433.7 (8.2) | big news | evening (20:30-24) | with the trend | -12.0 |
| 47 | Fri 06 Nov 02:00 | EMA pullback | sell | trend down, slow grind | 20m | new_york_session_low 13445.2 (1.3) | previous_day_low 13435.7 (8.2) | big news | Asia (00-07) | with the trend | +100.0 |
| 48 | Fri 06 Nov 02:55 | EMA pullback | sell | emerging trend down | 10m | new_york_session_low 13445.2 (3.1) | previous_day_low 13435.7 (6.4) | big news | Asia (00-07) | with the trend | +90.7 |
| 49 | Fri 06 Nov 04:10 | EMA pullback | sell | trend down, slow grind | 55m | turning_high 13426.4 (0.7) | turning_high 13406.5 (19.2) | big news | Asia (00-07) | with the trend | +74.3 |
| 50 | Fri 06 Nov 04:10 | EMA pullback | sell | trend down, slow grind | 55m | turning_high 13426.4 (0.7) | turning_high 13406.5 (19.2) | big news | Asia (00-07) | with the trend | +74.3 |
| 51 | Fri 06 Nov 06:45 | EMA pullback | sell | emerging trend down | 0m | turning_high 13426.4 (8.7) | turning_high 13406.5 (11.2) | big news | Asia (00-07) | with the trend | +66.3 |
| 52 | Fri 06 Nov 06:45 | EMA pullback | sell | emerging trend down | 0m | turning_high 13426.4 (8.7) | turning_high 13406.5 (11.2) | big news | Asia (00-07) | with the trend | +66.3 |
| 53 | Fri 06 Nov 08:40 | EMA pullback | sell | trend down, slow grind | 1h15 | turning_low 13396.1 (1.8) | london_session_low 13394.1 (0.2) | big news | London morning (07-12) | with the trend | +42.9 |
| 54 | Fri 06 Nov 08:40 | EMA pullback | sell | trend down, slow grind | 1h15 | london_session_low 13394.1 (0.7) | turning_high 13388.0 (5.4) | big news | London morning (07-12) | with the trend | -12.0 |
| 55 | Fri 06 Nov 09:00 | EMA pullback | sell | trend down, slow grind | 1h35 | london_session_low 13392.0 (1.9) | turning_high 13388.0 (2.1) | big news | London morning (07-12) | with the trend | -12.0 |
| 56 | Fri 06 Nov 13:30 | EMA pullback | sell | trend down, slow grind | 15m | turning_low 13378.4 (0.9) | turning_low 13373.9 (3.6) | big news | London/New York (12-16) | with the trend | +26.1 |
| 57 | Fri 06 Nov 13:30 | EMA pullback | sell | trend down, slow grind | 15m | turning_low 13378.4 (0.9) | turning_low 13373.9 (3.6) | big news | London/New York (12-16) | with the trend | +26.1 |
| 58 | Fri 06 Nov 13:30 | EMA pullback | sell | trend down, slow grind | 15m | turning_low 13378.4 (0.9) | turning_low 13373.9 (3.6) | big news | London/New York (12-16) | with the trend | +26.1 |
| 59 | Fri 06 Nov 19:50 | EMA pullback | sell | emerging trend down | 45m | round_number 13350 (1.3) | turning_high 13348.1 (0.6) | big news | New York afternoon (16-20:30) | with the trend | -2.7 |

#### slow grind (18)

| # | Entry (UK) | Strategy | Dir | Analyser at entry | In that state for | Nearest level above (type price, pips) | Nearest level below | Day | Time of day | With or against the trend | Pips |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Mon 26 Oct 06:05 | slow grind | sell | trend down, slow grind | 10m | turning_low 13376.1 (5.0) | turning_high 13370.8 (0.3) | ordinary | Asia (00-07) | with the trend | +10.0 |
| 2 | Mon 26 Oct 08:25 | slow grind | sell | trend down, slow grind | 55m | S1 13358.0 (2.5) | turning_low 13354.9 (0.6) | ordinary | London morning (07-12) | with the trend | +20.0 |
| 3 | Tue 27 Oct 05:45 | slow grind | sell | trend down, slow grind | 10m | turning_low 13336.2 (4.7) | turning_low 13327.8 (3.7) | ordinary | Asia (00-07) | with the trend | +20.0 |
| 4 | Tue 27 Oct 16:05 | slow grind | sell | trend down, slow grind | 10m | S1 13318.4 (8.2) | turning_low 13309.9 (0.3) | ordinary | New York afternoon (16-20:30) | with the trend | +0.0 |
| 5 | Wed 28 Oct 04:45 | slow grind | sell | trend down, slow grind | 25m | previous_day_low 13295.5 (1.4) | turning_low 13291.1 (3.0) | ordinary | Asia (00-07) | with the trend | +20.0 |
| 6 | Wed 28 Oct 10:20 | slow grind | sell | trend down, slow grind | 15m | S1 13284.2 (3.9) | turning_high 13277.8 (2.5) | ordinary | London morning (07-12) | with the trend | -15.0 |
| 7 | Wed 28 Oct 15:30 | slow grind | buy | trend up, slow grind | 15m | new_york_session_high 13304.4 (1.4) | turning_low 13300.6 (2.4) | ordinary | London/New York (12-16) | with the trend | +10.0 |
| 8 | Thu 29 Oct 05:05 | slow grind | sell | trend down, slow grind | 10m | turning_low 13327.1 (8.5) | turning_high 13312.3 (6.3) | ordinary | Asia (00-07) | with the trend | +20.0 |
| 9 | Fri 30 Oct 08:15 | slow grind | buy | trend up, slow grind | 40m | R1 13412.7 (0.9) | turning_high 13409.2 (2.6) | ordinary | London morning (07-12) | with the trend | +20.0 |
| 10 | Fri 30 Oct 13:20 | slow grind | sell | trend down, slow grind | 0m | round_number 13400 (6.0) | london_session_low 13393.1 (0.9) | ordinary | London/New York (12-16) | with the trend | +10.0 |
| 11 | Mon 02 Nov 08:00 | slow grind | buy | trend up, slow grind | 35m | london_session_high 13416.6 (0.9) | turning_high 13409.2 (6.5) | ordinary | London morning (07-12) | with the trend | +20.0 |
| 12 | Mon 02 Nov 19:40 | slow grind | sell | trend down, slow grind | 1h00 | turning_high 13418.6 (9.1) | turning_high 13409.2 (0.3) | ordinary | New York afternoon (16-20:30) | with the trend | -1.8 |
| 13 | Wed 04 Nov 00:15 | slow grind | buy | trend up, strong push | 10m | turning_high 13433.7 (0.9) | new_york_session_high 13432.5 (0.3) | ordinary | Asia (00-07) | with the trend | +20.0 |
| 14 | Wed 04 Nov 08:30 | slow grind | buy | trend up, slow grind | 30m | london_session_high 13484.7 (0.4) | R3 13483.8 (0.5) | ordinary | London morning (07-12) | with the trend | -15.0 |
| 15 | Wed 04 Nov 15:35 | slow grind | sell | trend down, strong push | 10m | turning_low 13468.2 (5.4) | new_york_session_low 13461.1 (1.7) | ordinary | London/New York (12-16) | with the trend | -15.0 |
| 16 | Thu 05 Nov 08:00 | slow grind | sell | trend down, strong push | 20m | london_session_high 13498.2 (28.3) | london_session_low 13469.0 (0.9) | big news | London morning (07-12) | with the trend | +9.7 |
| 17 | Thu 05 Nov 17:45 | slow grind | buy | trend up, slow grind | 20m | new_york_session_high 13484.6 (1.4) | turning_low 13468.2 (15.0) | big news | New York afternoon (16-20:30) | with the trend | -15.0 |
| 18 | Fri 06 Nov 01:55 | slow grind | sell | trend down, slow grind | 15m | turning_low 13447.2 (0.1) | london_session_low 13446.8 (0.3) | big news | Asia (00-07) | with the trend | +100.0 |

#### breakout (11)

| # | Entry (UK) | Strategy | Dir | Analyser at entry | In that state for | Nearest level above (type price, pips) | Nearest level below | Day | Time of day | With or against the trend | Pips |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Tue 27 Oct 07:00 | breakout | sell | emerging trend down | 10m | previous_day_low 13327.1 (1.1) | S1 13318.4 (7.6) | ordinary | London morning (07-12) | with the trend | -6.0 |
| 2 | Thu 29 Oct 14:45 | breakout | buy | emerging trend up | 0m | round_number 13350 (0.3) | turning_low 13348.7 (1.0) | ordinary | London/New York (12-16) | with the trend | +50.0 |
| 3 | Tue 03 Nov 10:15 | breakout | sell | emerging trend down | 5m | turning_high 13407.4 (0.5) | turning_high 13406.7 (0.2) | ordinary | London morning (07-12) | with the trend | -6.0 |
| 4 | Tue 03 Nov 13:45 | breakout | buy | emerging trend up | 0m | new_york_session_high 13430.1 (1.6) | london_session_high 13426.4 (2.1) | ordinary | London/New York (12-16) | with the trend | -6.0 |
| 5 | Tue 03 Nov 14:50 | breakout | buy | emerging trend up | 0m | new_york_session_high 13430.1 (0.1) | london_session_high 13426.4 (3.6) | ordinary | London/New York (12-16) | with the trend | -6.0 |
| 6 | Tue 03 Nov 18:05 | breakout | buy | emerging trend up | 0m | london_session_high 13426.4 (2.9) | turning_high 13418.6 (4.9) | ordinary | New York afternoon (16-20:30) | with the trend | -6.0 |
| 7 | Wed 04 Nov 20:05 | breakout | buy | emerging trend up | 0m | R3 13483.8 (13.2) | turning_low 13468.2 (2.4) | ordinary | New York afternoon (16-20:30) | with the trend | -9.4 |
| 8 | Thu 05 Nov 07:00 | breakout | buy | emerging trend up | 0m | london_session_high 13498.2 (1.0) | turning_low 13468.2 (29.0) | big news | London morning (07-12) | with the trend | -6.0 |
| 9 | Thu 05 Nov 09:50 | breakout | sell | emerging trend down | 0m | pivot 13468.0 (6.3) | london_session_low 13454.6 (7.1) | big news | London morning (07-12) | with the trend | -6.0 |
| 10 | Thu 05 Nov 18:35 | breakout | sell | emerging trend down | 0m | new_york_session_high 13486.0 (17.8) | pivot 13468.0 (0.2) | big news | New York afternoon (16-20:30) | with the trend | +50.0 |
| 11 | Fri 06 Nov 17:50 | breakout | sell | emerging trend down | 0m | turning_high 13357.4 (2.2) | round_number 13350 (5.2) | big news | New York afternoon (16-20:30) | with the trend | +3.8 |

#### level reversal (20)

| # | Entry (UK) | Strategy | Dir | Analyser at entry | In that state for | Nearest level above (type price, pips) | Nearest level below | Day | Time of day | With or against the trend | Pips |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Mon 26 Oct 13:55 | level reversal | sell | emerging trend down | 50m | turning_high 13336.4 (0.1) | turning_low 13336.2 (0.1) | ordinary | London/New York (12-16) | with the trend | -12.7 |
| 2 | Mon 26 Oct 14:45 | level reversal | buy | trend down, slow grind | 45m | previous_day_low 13348.7 (3.6) | london_session_low 13341.8 (3.3) | ordinary | London/New York (12-16) | against the trend | -4.6 |
| 3 | Wed 28 Oct 13:55 | level reversal | sell | trend up, slow grind | 15m | previous_day_low 13295.5 (1.2) | turning_low 13291.1 (3.2) | ordinary | London/New York (12-16) | against the trend | -15.5 |
| 4 | Wed 28 Oct 16:15 | level reversal | buy | trend up, slow grind | 1h00 | turning_low 13309.9 (1.3) | london_session_low 13307.2 (1.4) | ordinary | New York afternoon (16-20:30) | with the trend | -16.4 |
| 5 | Thu 29 Oct 09:35 | level reversal | buy | trend down, slow grind | 5m | turning_low 13306.5 (2.3) | turning_low 13302.5 (1.7) | ordinary | London morning (07-12) | against the trend | +20.0 |
| 6 | Thu 29 Oct 13:30 | level reversal | buy | trend down, slow grind | 10m | turning_low 13327.1 (6.7) | turning_high 13312.3 (8.1) | ordinary | London/New York (12-16) | against the trend | +20.0 |
| 7 | Thu 29 Oct 16:30 | level reversal | sell | emerging trend down | 55m | turning_high 13370.8 (3.4) | turning_low 13364.3 (3.1) | ordinary | New York afternoon (16-20:30) | with the trend | -14.9 |
| 8 | Fri 30 Oct 06:40 | level reversal | sell | emerging trend down | 0m | round_number 13400 (8.8) | previous_day_high 13389.0 (2.2) | ordinary | Asia (00-07) | with the trend | -16.5 |
| 9 | Fri 30 Oct 07:25 | level reversal | buy | emerging trend up | 15m | R1 13412.7 (2.1) | turning_high 13409.2 (1.4) | ordinary | London morning (07-12) | with the trend | +20.0 |
| 10 | Fri 30 Oct 13:25 | level reversal | sell | trend down, slow grind | 5m | round_number 13400 (6.9) | previous_day_high 13389.0 (4.1) | ordinary | London/New York (12-16) | with the trend | -4.1 |
| 11 | Mon 02 Nov 06:00 | level reversal | sell | emerging trend down | 0m | R2 13399.1 (1.4) | london_session_low 13393.1 (4.6) | ordinary | Asia (00-07) | with the trend | -9.4 |
| 12 | Mon 02 Nov 07:25 | level reversal | buy | trend up, slow grind | 0m | turning_high 13418.6 (9.1) | turning_high 13409.2 (0.3) | ordinary | London morning (07-12) | with the trend | +20.0 |
| 13 | Mon 02 Nov 11:05 | level reversal | buy | emerging trend up | 0m | turning_high 13418.6 (7.8) | turning_high 13409.2 (1.6) | ordinary | London morning (07-12) | with the trend | -1.3 |
| 14 | Tue 03 Nov 11:50 | level reversal | buy | emerging trend up | 5m | turning_high 13409.2 (0.9) | turning_high 13407.4 (0.9) | ordinary | London morning (07-12) | with the trend | +20.0 |
| 15 | Wed 04 Nov 06:15 | level reversal | sell | emerging trend down | 15m | R2 13458.8 (5.8) | round_number 13450 (3.0) | ordinary | Asia (00-07) | with the trend | -17.4 |
| 16 | Wed 04 Nov 07:25 | level reversal | buy | emerging trend up | 5m | R3 13483.8 (16.2) | R2 13458.8 (8.8) | ordinary | London morning (07-12) | with the trend | +20.0 |
| 17 | Wed 04 Nov 12:40 | level reversal | sell | emerging trend down | 0m | london_session_high 13498.2 (10.8) | R3 13483.8 (3.6) | ordinary | London/New York (12-16) | with the trend | +20.0 |
| 18 | Wed 04 Nov 17:10 | level reversal | buy | trend down, slow grind | 1h30 | R3 13483.8 (15.5) | turning_low 13468.2 (0.1) | ordinary | New York afternoon (16-20:30) | against the trend | +3.2 |
| 19 | Thu 05 Nov 07:15 | level reversal | sell | emerging trend down | 0m | london_session_high 13498.2 (9.5) | turning_low 13468.2 (20.5) | big news | London morning (07-12) | with the trend | +20.0 |
| 20 | Fri 06 Nov 08:55 | level reversal | sell | trend down, slow grind | 1h30 | turning_low 13396.1 (3.0) | turning_high 13388.0 (5.1) | big news | London morning (07-12) | with the trend | +5.8 |

#### Bollinger bounce (37)

| # | Entry (UK) | Strategy | Dir | Analyser at entry | In that state for | Nearest level above (type price, pips) | Nearest level below | Day | Time of day | With or against the trend | Pips |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Mon 26 Oct 06:00 | Bollinger bounce | buy | trend down, slow grind | 5m | turning_low 13376.1 (2.1) | turning_high 13370.8 (3.2) | ordinary | Asia (00-07) | against the trend | -6.0 |
| 2 | Mon 26 Oct 09:05 | Bollinger bounce | buy | trend down, slow grind | 1h35 | turning_low 13354.9 (3.8) | round_number 13350 (1.1) | ordinary | London morning (07-12) | against the trend | -6.0 |
| 3 | Mon 26 Oct 14:10 | Bollinger bounce | buy | trend down, slow grind | 10m | S2 13338.6 (2.2) | turning_low 13336.2 (0.2) | ordinary | London/New York (12-16) | against the trend | +4.3 |
| 4 | Mon 26 Oct 17:50 | Bollinger bounce | sell | trend up, slow grind | 20m | turning_low 13354.9 (1.5) | round_number 13350 (3.4) | ordinary | New York afternoon (16-20:30) | against the trend | +11.1 |
| 5 | Tue 27 Oct 07:20 | Bollinger bounce | buy | trend down, slow grind | 15m | london_session_high 13326.6 (2.1) | S1 13318.4 (6.1) | ordinary | London morning (07-12) | against the trend | -5.0 |
| 6 | Tue 27 Oct 09:55 | Bollinger bounce | buy | trend down, slow grind | 30m | S1 13318.4 (2.1) | turning_low 13309.9 (6.4) | ordinary | London morning (07-12) | against the trend | -6.0 |
| 7 | Tue 27 Oct 12:35 | Bollinger bounce | sell | trend up, slow grind | 15m | london_session_high 13329.6 (1.1) | turning_low 13327.8 (0.7) | ordinary | London/New York (12-16) | against the trend | +6.0 |
| 8 | Tue 27 Oct 16:40 | Bollinger bounce | buy | trend down, slow grind | 45m | S1 13318.4 (8.5) | london_session_low 13307.2 (2.7) | ordinary | New York afternoon (16-20:30) | against the trend | +4.1 |
| 9 | Wed 28 Oct 07:25 | Bollinger bounce | buy | trend down, slow grind | 40m | london_session_high 13280.3 (1.6) | turning_high 13277.8 (0.9) | ordinary | London morning (07-12) | against the trend | +11.4 |
| 10 | Wed 28 Oct 10:35 | Bollinger bounce | buy | trend down, slow grind | 30m | turning_low 13291.1 (4.3) | S1 13284.2 (2.6) | ordinary | London morning (07-12) | against the trend | -6.0 |
| 11 | Wed 28 Oct 11:15 | Bollinger bounce | buy | trend down, slow grind | 1h10 | S1 13284.2 (2.5) | turning_high 13277.8 (3.9) | ordinary | London morning (07-12) | against the trend | +4.7 |
| 12 | Wed 28 Oct 13:55 | Bollinger bounce | sell | trend up, slow grind | 15m | previous_day_low 13295.5 (1.2) | turning_low 13291.1 (3.2) | ordinary | London/New York (12-16) | against the trend | +1.4 |
| 13 | Wed 28 Oct 15:20 | Bollinger bounce | sell | trend up, slow grind | 5m | turning_low 13300.6 (0.1) | round_number 13300 (0.5) | ordinary | London/New York (12-16) | against the trend | -5.4 |
| 14 | Wed 28 Oct 15:50 | Bollinger bounce | sell | trend up, slow grind | 35m | previous_day_low 13295.5 (0.4) | turning_low 13291.1 (4.0) | ordinary | London/New York (12-16) | against the trend | -6.0 |
| 15 | Wed 28 Oct 17:05 | Bollinger bounce | sell | trend up, slow grind | 1h50 | pivot 13316.2 (3.2) | turning_high 13312.3 (0.7) | ordinary | New York afternoon (16-20:30) | against the trend | -6.0 |
| 16 | Thu 29 Oct 06:30 | Bollinger bounce | buy | trend down, slow grind | 1h35 | turning_high 13312.3 (0.3) | turning_low 13309.9 (2.1) | ordinary | Asia (00-07) | against the trend | -6.0 |
| 17 | Thu 29 Oct 08:15 | Bollinger bounce | sell | trend up, slow grind | 10m | turning_low 13327.1 (11.7) | turning_high 13312.3 (3.1) | ordinary | London morning (07-12) | against the trend | +10.3 |
| 18 | Thu 29 Oct 09:35 | Bollinger bounce | buy | trend down, slow grind | 5m | turning_low 13306.5 (2.3) | turning_low 13302.5 (1.7) | ordinary | London morning (07-12) | against the trend | +15.4 |
| 19 | Thu 29 Oct 13:30 | Bollinger bounce | buy | trend down, slow grind | 10m | turning_low 13327.1 (6.7) | turning_high 13312.3 (8.1) | ordinary | London/New York (12-16) | against the trend | +46.1 |
| 20 | Fri 30 Oct 07:45 | Bollinger bounce | sell | trend up, slow grind | 10m | turning_high 13403.2 (1.6) | turning_high 13401.5 (0.1) | ordinary | London morning (07-12) | against the trend | -6.0 |
| 21 | Fri 30 Oct 10:40 | Bollinger bounce | sell | trend up, slow grind | 3h05 | london_session_high 13432.3 (6.5) | turning_high 13418.6 (7.2) | ordinary | London morning (07-12) | against the trend | -6.0 |
| 22 | Fri 30 Oct 11:20 | Bollinger bounce | sell | possible reversal down | 0m | london_session_high 13433.7 (4.1) | turning_high 13418.6 (11.0) | ordinary | London morning (07-12) | against the trend | +0.5 |
| 23 | Fri 30 Oct 15:25 | Bollinger bounce | buy | possible reversal up | 0m | london_session_low 13393.1 (1.6) | previous_day_high 13389.0 (2.5) | ordinary | London/New York (12-16) | against the trend | -6.0 |
| 24 | Fri 30 Oct 16:25 | Bollinger bounce | sell | trend up, slow grind | 5m | round_number 13400 (2.6) | london_session_low 13393.1 (4.3) | ordinary | New York afternoon (16-20:30) | against the trend | +5.5 |
| 25 | Mon 02 Nov 09:25 | Bollinger bounce | sell | possible reversal down | 0m | london_session_high 13448.0 (11.3) | london_session_high 13433.7 (3.0) | ordinary | London morning (07-12) | against the trend | +25.0 |
| 26 | Mon 02 Nov 18:55 | Bollinger bounce | buy | trend down, slow grind | 15m | R3 13405.9 (0.2) | turning_high 13403.2 (2.5) | ordinary | New York afternoon (16-20:30) | against the trend | +3.3 |
| 27 | Tue 03 Nov 06:45 | Bollinger bounce | sell | trend up, slow grind | 1h00 | turning_high 13409.2 (0.4) | turning_high 13407.4 (1.4) | ordinary | Asia (00-07) | against the trend | -6.0 |
| 28 | Tue 03 Nov 08:20 | Bollinger bounce | sell | trend up, slow grind | 10m | london_session_high 13426.4 (7.1) | turning_high 13418.6 (0.7) | ordinary | London morning (07-12) | against the trend | +1.4 |
| 29 | Wed 04 Nov 10:40 | Bollinger bounce | sell | trend up, slow grind | 2h40 | R3 13483.8 (4.7) | R2 13458.8 (20.3) | ordinary | London morning (07-12) | against the trend | -6.0 |
| 30 | Wed 04 Nov 13:25 | Bollinger bounce | sell | trend up, slow grind | 10m | london_session_high 13498.2 (4.3) | R3 13483.8 (10.1) | ordinary | London/New York (12-16) | against the trend | -6.0 |
| 31 | Wed 04 Nov 14:00 | Bollinger bounce | sell | trend up, slow grind | 45m | R3 13483.8 (0.3) | new_york_session_low 13481.1 (2.4) | ordinary | London/New York (12-16) | against the trend | -6.0 |
| 32 | Wed 04 Nov 14:30 | Bollinger bounce | sell | trend up, slow grind | 1h15 | london_session_high 13498.2 (13.8) | R3 13483.8 (0.6) | ordinary | London/New York (12-16) | against the trend | -6.0 |
| 33 | Wed 04 Nov 14:30 | Bollinger bounce | sell | trend up, slow grind | 1h15 | london_session_high 13498.2 (13.8) | R3 13483.8 (0.6) | ordinary | London/New York (12-16) | against the trend | -6.0 |
| 34 | Wed 04 Nov 15:40 | Bollinger bounce | buy | trend down, slow grind | 0m | R3 13483.8 (14.4) | turning_low 13468.2 (1.2) | ordinary | London/New York (12-16) | against the trend | -6.0 |
| 35 | Wed 04 Nov 17:10 | Bollinger bounce | buy | trend down, slow grind | 1h30 | R3 13483.8 (15.5) | turning_low 13468.2 (0.1) | ordinary | New York afternoon (16-20:30) | against the trend | -6.0 |
| 36 | Thu 05 Nov 08:15 | Bollinger bounce | buy | trend down, slow grind | 10m | london_session_high 13498.2 (18.9) | turning_low 13468.2 (11.1) | big news | London morning (07-12) | against the trend | -6.0 |
| 37 | Thu 05 Nov 08:50 | Bollinger bounce | buy | trend down, slow grind | 45m | london_session_high 13498.2 (19.6) | turning_low 13468.2 (10.4) | big news | London morning (07-12) | against the trend | -6.0 |

#### range trade (7)

| # | Entry (UK) | Strategy | Dir | Analyser at entry | In that state for | Nearest level above (type price, pips) | Nearest level below | Day | Time of day | With or against the trend | Pips |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Mon 26 Oct 11:50 | range trade | sell | ranging | 15m | turning_low 13354.9 (3.8) | round_number 13350 (1.1) | ordinary | London morning (07-12) | no trend | +2.0 |
| 2 | Tue 27 Oct 17:30 | range trade | sell | ranging | 10m | S1 13318.4 (2.3) | turning_low 13309.9 (6.2) | ordinary | New York afternoon (16-20:30) | no trend | +3.9 |
| 3 | Mon 02 Nov 14:20 | range trade | buy | ranging | 10m | turning_high 13418.6 (4.4) | turning_high 13409.2 (5.0) | ordinary | London/New York (12-16) | no trend | +4.9 |
| 4 | Mon 02 Nov 17:35 | range trade | sell | ranging | 5m | turning_high 13418.6 (0.9) | turning_high 13409.2 (8.5) | ordinary | New York afternoon (16-20:30) | no trend | +7.3 |
| 5 | Tue 03 Nov 10:00 | range trade | sell | ranging | 15m | turning_high 13418.6 (1.1) | pivot 13411.6 (5.9) | ordinary | London morning (07-12) | no trend | +2.8 |
| 6 | Tue 03 Nov 12:50 | range trade | buy | ranging | 5m | pivot 13411.6 (2.0) | turning_high 13409.2 (0.4) | ordinary | London/New York (12-16) | no trend | +4.6 |
| 7 | Thu 05 Nov 06:05 | range trade | buy | ranging | 50m | london_session_high 13498.2 (7.1) | turning_low 13468.2 (22.9) | big news | Asia (00-07) | no trend | -2.3 |

## 2. The life of each trade

### Live trades

| # | Entry (UK) | Strategy | Dir | Analyser changes while open | Best (pips at UK time) | Worst | Closed (UK) | What closed it | Pips | 2 h after: further in its favour (max) | further against (max) | at 2 h | Group |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Mon 09 Nov 05:25 | slow grind | buy | 05:55 consolidation; 06:10 emerging trend up; 07:30 consolidation; 07:40 emerging trend up; 07:50 consolidation; 07:55 emerging trend up | +20.0 at 08:13 | -1.7 at 05:40 | Mon 09 Nov 08:13 | take profit at IG | +20.0 | +18.5 | +1.8 | +17.8 | a |
| 2 | Mon 09 Nov 06:12 | level reversal | buy | 07:30 consolidation; 07:40 emerging trend up; 07:50 consolidation; 07:55 emerging trend up | +20.0 at 08:18 | -3.6 at 07:15 | Mon 09 Nov 08:18 | take profit at IG | +20.0 | +13.9 | +0.0 | +13.6 | d |
| 3 | Mon 09 Nov 07:55 | breakout | buy | 08:30 trend up, strong push; 08:55 trend up, slow grind; 10:40 possible reversal down; 11:00 emerging trend down; 11:15 consolidation; 11:55 emerging trend down; 12:25 consolidation; 13:45 emerging trend down; 13:55 ranging; 14:30 consolidation; 14:40 ranging | +33.5 at 11:15 | -3.3 at 08:00 | Mon 09 Nov 15:21 | closed by IG's system at market (not at its stop or take profit) | +11.7 | +18.7 | -6.5 | +18.3 | a |
| 4 | Mon 09 Nov 08:25 | level reversal | buy | 08:30 trend up, strong push; 08:55 trend up, slow grind; 10:40 possible reversal down; 11:00 emerging trend down; 11:15 consolidation; 11:55 emerging trend down; 12:25 consolidation; 13:45 emerging trend down; 13:55 ranging; 14:30 consolidation; 14:40 ranging | +11.1 at 11:15 | -11.2 at 15:21 | Mon 09 Nov 15:21 | closed by IG's system at market (not at its stop or take profit) | -11.2 | +19.2 | -6.0 | +18.8 | a (also b) |
| 5 | Mon 09 Nov 09:00 | Bollinger bounce | sell | none | +0.7 at 09:20 | -6.0 at 09:29 | Mon 09 Nov 09:29 | stop at IG | -6.0 | +2.2 | -13.5 | -5.8 | c |
| 6 | Mon 09 Nov 09:39 | slow grind | buy | 10:40 possible reversal down; 11:00 emerging trend down; 11:15 consolidation; 11:55 emerging trend down; 12:25 consolidation; 13:45 emerging trend down; 13:55 ranging; 14:30 consolidation; 14:40 ranging | +9.2 at 11:15 | -12.7 at 15:21 | Mon 09 Nov 15:21 | closed by IG's system at market (not at its stop or take profit) | -12.7 | +18.8 | -6.4 | +18.4 | a |
| 7 | Mon 09 Nov 13:55 | range trade | buy | 14:30 consolidation; 14:40 ranging | +2.2 at 14:20 | -6.0 at 14:43 | Mon 09 Nov 14:43 | stop at IG | -6.0 | +4.2 | -14.9 | -0.7 | c |
| 8 | Mon 09 Nov 14:55 | range trade | buy | none | -6.0 at 14:58 | -6.0 at 14:58 | Mon 09 Nov 14:58 | stop at IG | -6.0 | +10.3 | -11.6 | +8.8 | c |
| 9 | Mon 09 Nov 15:16 | range trade | buy | none | -3.9 at 15:20 | -6.0 at 15:20 | Mon 09 Nov 15:20 | stop at IG | -6.0 | +18.0 | -7.2 | +17.6 | a (also c) |
| 10 | Mon 09 Nov 15:45 | slow grind | sell | 16:15 consolidation | +1.0 at 15:50 | -15.0 at 16:17 | Mon 09 Nov 16:17 | stop at IG | -15.0 | +4.3 | -10.8 | -3.5 | c |
| 11 | Mon 09 Nov 19:55 | slow grind | buy | none | +2.0 at 20:15 | -2.6 at 20:05 | Mon 09 Nov 20:30 | closed by the bot: 20:30 UK close | -2.5 | +7.1 | -10.3 | -9.3 | c |
| 12 | Mon 09 Nov 21:02 | EMA pullback | buy | 21:45 consolidation | -0.4 at 21:25 | -12.0 at 22:00 | Mon 09 Nov 22:00 | stop at IG | -12.0 | +9.9 | -5.8 | +8.5 | c |
| 13 | Tue 10 Nov 05:01 | EMA pullback | buy | 05:15 emerging trend down; 05:25 emerging trend up; 05:40 emerging trend down; 06:00 emerging trend up; 06:25 emerging trend down; 06:40 consolidation; 06:45 emerging trend down; 07:00 consolidation; 07:05 emerging trend up; 07:45 trend up, slow grind; 09:00 consolidation | +7.6 at 08:30 | -12.0 at 09:00 | Tue 10 Nov 09:00 | stop at IG | -12.0 | +1.8 | -17.1 | -11.6 | d |
| 14 | Tue 10 Nov 06:12 | EMA pullback | buy | 06:25 emerging trend down; 06:40 consolidation; 06:45 emerging trend down; 07:00 consolidation; 07:05 emerging trend up; 07:45 trend up, slow grind; 09:00 consolidation | +5.8 at 08:30 | -12.0 at 09:00 | Tue 10 Nov 09:00 | stop at IG | -12.0 | +0.0 | -18.9 | -13.4 | d |
| 15 | Tue 10 Nov 07:21 | EMA pullback | buy | 07:45 trend up, slow grind; 09:00 consolidation | +2.5 at 08:30 | -12.0 at 09:00 | Tue 10 Nov 09:00 | stop at IG | -12.0 | -3.3 | -22.2 | -16.7 | c |
| 16 | Tue 10 Nov 07:55 | Bollinger bounce | sell | none | -3.2 at 08:00 | -6.0 at 08:01 | Tue 10 Nov 08:01 | stop at IG | -6.0 | +32.1 | -4.5 | +28.9 | a (also c) |
| 17 | Tue 10 Nov 08:20 | Bollinger bounce | sell | none | -6.0 at 08:24 | -6.0 at 08:24 | Tue 10 Nov 08:24 | stop at IG | -6.0 | +31.4 | -5.2 | +28.0 | a (also c) |
| 18 | Tue 10 Nov 08:45 | Bollinger bounce | sell | 09:00 consolidation; 09:05 emerging trend down; 09:30 consolidation | +30.3 at 10:25 | -3.9 at 08:50 | Tue 10 Nov 10:45 | closed by the bot: a confirmed rejection at a level: london_session_low 13422 | +22.8 | +7.9 | -3.0 | +1.8 | d |
| 19 | Tue 10 Nov 09:10 | breakout | sell | none | +0.6 at 09:15 | -6.0 at 09:24 | Tue 10 Nov 09:24 | stop at IG | -6.0 | +15.3 | -2.4 | +9.7 | a (also c) |
| 20 | Tue 10 Nov 11:50 | breakout | sell | 12:00 consolidation | -2.5 at 11:55 | -6.0 at 12:02 | Tue 10 Nov 12:02 | stop at IG | -6.0 | +36.7 | -5.3 | +30.4 | a (also c) |

### Replay (every trade)

#### EMA pullback (59)

| # | Entry (UK) | Strategy | Dir | Analyser changes while open | Best (pips at UK time) | Worst | Closed (UK) | What closed it | Pips | 2 h after: further in its favour (max) | further against (max) | at 2 h | Group |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Mon 26 Oct 08:35 | EMA pullback | sell | 10:25 consolidation; 11:00 emerging trend up; 11:10 consolidation; 11:15 emerging trend down; 11:25 consolidation; 11:35 ranging; 11:55 emerging trend down; 12:55 emerging trend up; 13:05 emerging trend down; 14:00 trend down, slow grind; 15:50 consolidation; 16:40 emerging trend up; 17:00 consolidation; 17:20 emerging trend up; 17:30 trend up, slow grind; 18:50 consolidation; 19:00 emerging trend down; 20:05 consolidation; 20:30 emerging trend down; 20:45 emerging trend up; 22:40 consolidation; 23:55 emerging trend up; 00:15 trend up, slow grind; 00:55 consolidation; 01:05 emerging trend down; 01:30 consolidation; 04:55 ranging; 05:10 emerging trend down; 05:35 trend down, slow grind; 06:25 consolidation; 06:50 emerging trend down; 07:05 trend down, slow grind | +30.0 at 07:05 | -10.7 at 17:30 | Tue 27 Oct 07:05 | take profit hit at IG: the take profit at IG (30 pips) | +30.0 | +1.7 | -11.2 | -3.9 | d |
| 2 | Mon 26 Oct 08:35 | EMA pullback | sell | 10:25 consolidation; 11:00 emerging trend up; 11:10 consolidation; 11:15 emerging trend down; 11:25 consolidation; 11:35 ranging; 11:55 emerging trend down; 12:55 emerging trend up; 13:05 emerging trend down; 14:00 trend down, slow grind; 15:50 consolidation; 16:40 emerging trend up; 17:00 consolidation; 17:20 emerging trend up; 17:30 trend up, slow grind; 18:50 consolidation; 19:00 emerging trend down; 20:05 consolidation; 20:30 emerging trend down; 20:45 emerging trend up; 22:40 consolidation; 23:55 emerging trend up; 00:15 trend up, slow grind; 00:55 consolidation; 01:05 emerging trend down; 01:30 consolidation; 04:55 ranging; 05:10 emerging trend down; 05:35 trend down, slow grind; 06:25 consolidation; 06:50 emerging trend down; 07:05 trend down, slow grind | +30.0 at 07:05 | -10.7 at 17:30 | Tue 27 Oct 07:05 | take profit hit at IG: the take profit at IG (30 pips) | +30.0 | +1.7 | -11.2 | -3.9 | d |
| 3 | Mon 26 Oct 12:05 | EMA pullback | sell | none | -3.3 at 12:10 | -12.0 at 12:25 | Mon 26 Oct 12:25 | stopped by IG: the stop at IG | -12.0 | +27.5 | -2.8 | +12.9 | a (also c) |
| 4 | Mon 26 Oct 13:55 | EMA pullback | sell | 14:00 trend down, slow grind | +2.7 at 14:00 | -12.0 at 14:30 | Mon 26 Oct 14:30 | stopped by IG: the stop at IG | -12.0 | +5.1 | -8.5 | -6.3 | c |
| 5 | Mon 26 Oct 13:55 | EMA pullback | sell | 14:00 trend down, slow grind | +2.7 at 14:00 | -12.0 at 14:30 | Mon 26 Oct 14:30 | stopped by IG: the stop at IG | -12.0 | +5.1 | -8.5 | -6.3 | c |
| 6 | Tue 27 Oct 16:15 | EMA pullback | sell | none | -0.2 at 16:20 | -12.0 at 17:00 | Tue 27 Oct 17:00 | stopped by IG: the stop at IG | -12.0 | +9.5 | -3.0 | +4.1 | c |
| 7 | Tue 27 Oct 17:55 | EMA pullback | sell | 18:25 consolidation; 18:45 emerging trend down; 18:55 consolidation; 19:55 emerging trend down; 20:35 trend down, slow grind; 23:15 consolidation; 23:50 emerging trend up; 00:00 consolidation; 00:05 emerging trend up; 00:25 consolidation; 01:00 ranging; 02:00 emerging trend up; 02:15 emerging trend down; 02:25 consolidation; 02:40 emerging trend up; 03:20 consolidation; 03:30 ranging; 04:05 emerging trend down; 04:20 trend down, slow grind; 04:50 consolidation; 05:10 emerging trend down; 05:45 emerging trend up; 06:00 consolidation; 06:35 emerging trend down | +30.0 at 06:40 | -7.8 at 21:25 | Wed 28 Oct 06:40 | take profit hit at IG: the take profit at IG (30 pips) | +30.0 | +8.2 | -14.9 | -11.4 | d |
| 8 | Tue 27 Oct 19:55 | EMA pullback | sell | 20:35 trend down, slow grind; 23:15 consolidation; 23:50 emerging trend up; 00:00 consolidation; 00:05 emerging trend up; 00:25 consolidation; 01:00 ranging; 02:00 emerging trend up; 02:15 emerging trend down; 02:25 consolidation; 02:40 emerging trend up; 03:20 consolidation; 03:30 ranging; 04:05 emerging trend down; 04:20 trend down, slow grind; 04:50 consolidation; 05:10 emerging trend down; 05:45 emerging trend up; 06:00 consolidation | +30.0 at 06:30 | -6.1 at 21:25 | Wed 28 Oct 06:30 | take profit hit at IG: the take profit at IG (30 pips) | +30.0 | +9.9 | -12.7 | -11.5 | d |
| 9 | Wed 28 Oct 10:45 | EMA pullback | sell | none | +2.0 at 11:00 | -12.0 at 11:35 | Wed 28 Oct 11:35 | stopped by IG: the stop at IG | -12.0 | +3.5 | -11.3 | -9.8 | c |
| 10 | Wed 28 Oct 10:45 | EMA pullback | sell | none | +2.0 at 11:00 | -12.0 at 11:35 | Wed 28 Oct 11:35 | stopped by IG: the stop at IG | -12.0 | +3.5 | -11.3 | -9.8 | c |
| 11 | Thu 29 Oct 22:05 | EMA pullback | buy | 00:50 ranging; 01:00 emerging trend up; 01:15 trend up, strong push; 01:35 trend up, slow grind; 02:25 consolidation; 02:50 emerging trend up; 03:25 emerging trend down; 04:00 emerging trend up; 04:15 emerging trend down; 04:25 ranging; 05:05 emerging trend down; 05:30 trend down, slow grind; 05:50 consolidation; 06:10 ranging; 06:30 emerging trend up; 06:40 emerging trend down; 07:10 emerging trend up; 07:35 trend up, slow grind | +30.0 at 08:25 | -9.7 at 00:05 | Fri 30 Oct 08:25 | take profit hit at IG: the take profit at IG (30 pips) | +30.0 | +17.5 | -4.8 | +13.5 | a |
| 12 | Fri 30 Oct 00:40 | EMA pullback | buy | 00:50 ranging; 01:00 emerging trend up; 01:15 trend up, strong push; 01:35 trend up, slow grind; 02:25 consolidation; 02:50 emerging trend up; 03:25 emerging trend down; 04:00 emerging trend up; 04:15 emerging trend down; 04:25 ranging; 05:05 emerging trend down; 05:30 trend down, slow grind; 05:50 consolidation; 06:10 ranging; 06:30 emerging trend up; 06:40 emerging trend down; 07:10 emerging trend up; 07:35 trend up, slow grind | +30.0 at 09:15 | -9.9 at 05:25 | Fri 30 Oct 09:15 | take profit hit at IG: the take profit at IG (30 pips) | +30.0 | +13.6 | -1.4 | +11.2 | d |
| 13 | Fri 30 Oct 03:00 | EMA pullback | buy | 03:25 emerging trend down; 04:00 emerging trend up; 04:15 emerging trend down; 04:25 ranging | +5.1 at 03:10 | -12.0 at 04:50 | Fri 30 Oct 04:50 | stopped by IG: the stop at IG | -12.0 | +14.9 | -6.6 | +5.4 | d |
| 14 | Fri 30 Oct 07:10 | EMA pullback | buy | 07:35 trend up, slow grind | +30.0 at 09:45 | -2.8 at 07:50 | Fri 30 Oct 09:45 | take profit hit at IG: the take profit at IG (30 pips) | +30.0 | +2.8 | -7.9 | -2.1 | d |
| 15 | Fri 30 Oct 09:15 | EMA pullback | buy | 10:45 possible reversal down; 11:00 trend up, slow grind; 11:20 possible reversal down; 11:25 emerging trend down; 11:40 consolidation; 12:40 emerging trend down | +12.4 at 11:10 | -12.0 at 12:40 | Fri 30 Oct 12:40 | stopped by IG: the stop at IG | -12.0 | -1.1 | -35.4 | -20.3 | b |
| 16 | Fri 30 Oct 09:15 | EMA pullback | buy | 10:45 possible reversal down; 11:00 trend up, slow grind; 11:20 possible reversal down; 11:25 emerging trend down; 11:40 consolidation; 12:40 emerging trend down | +12.4 at 11:10 | -12.0 at 12:40 | Fri 30 Oct 12:40 | stopped by IG: the stop at IG | -12.0 | -1.1 | -35.4 | -20.3 | b |
| 17 | Fri 30 Oct 11:10 | EMA pullback | buy | 11:20 possible reversal down; 11:25 emerging trend down; 11:40 consolidation | -2.4 at 11:15 | -12.0 at 12:00 | Fri 30 Oct 12:00 | stopped by IG: the stop at IG | -12.0 | +8.4 | -42.6 | -40.5 | c |
| 18 | Mon 02 Nov 07:20 | EMA pullback | buy | 07:25 trend up, slow grind | +30.0 at 08:50 | -1.5 at 07:25 | Mon 02 Nov 08:50 | take profit hit at IG: the take profit at IG (30 pips) | +30.0 | +8.7 | -36.8 | -36.4 | d |
| 19 | Mon 02 Nov 07:20 | EMA pullback | buy | 07:25 trend up, slow grind | +30.0 at 08:50 | -1.5 at 07:25 | Mon 02 Nov 08:50 | take profit hit at IG: the take profit at IG (30 pips) | +30.0 | +8.7 | -36.8 | -36.4 | d |
| 20 | Mon 02 Nov 07:20 | EMA pullback | buy | 07:25 trend up, slow grind | +30.0 at 08:50 | -1.5 at 07:25 | Mon 02 Nov 08:50 | take profit hit at IG: the take profit at IG (30 pips) | +30.0 | +8.7 | -36.8 | -36.4 | d |
| 21 | Mon 02 Nov 08:30 | EMA pullback | buy | 09:10 trend up, strong push; 09:25 possible reversal down; 09:30 emerging trend down | +26.5 at 09:00 | -12.0 at 10:25 | Mon 02 Nov 10:25 | stopped by IG: the stop at IG | -12.0 | +10.4 | -9.1 | +10.3 | b |
| 22 | Mon 02 Nov 08:30 | EMA pullback | buy | 09:10 trend up, strong push; 09:25 possible reversal down; 09:30 emerging trend down | +26.5 at 09:00 | -12.0 at 10:25 | Mon 02 Nov 10:25 | stopped by IG: the stop at IG | -12.0 | +10.4 | -9.1 | +10.3 | b |
| 23 | Mon 02 Nov 12:25 | EMA pullback | buy | 13:15 consolidation | +7.6 at 13:35 | -12.0 at 13:55 | Mon 02 Nov 13:55 | stopped by IG: the stop at IG | -12.0 | +16.5 | -3.2 | +8.7 | a |
| 24 | Mon 02 Nov 14:30 | EMA pullback | buy | none | +4.4 at 15:20 | -12.0 at 16:00 | Mon 02 Nov 16:00 | stopped by IG: the stop at IG | -12.0 | +12.7 | -2.4 | +3.6 | c |
| 25 | Mon 02 Nov 17:00 | EMA pullback | buy | 17:15 consolidation; 17:30 ranging; 18:10 consolidation | +0.4 at 17:25 | -12.0 at 18:15 | Mon 02 Nov 18:15 | stopped by IG: the stop at IG | -12.0 | +7.2 | -8.6 | -1.0 | c |
| 26 | Tue 03 Nov 08:05 | EMA pullback | buy | 08:10 trend up, slow grind | -0.8 at 08:10 | -12.0 at 08:30 | Tue 03 Nov 08:30 | stopped by IG: the stop at IG | -12.0 | +8.8 | -9.6 | -4.8 | c |
| 27 | Tue 03 Nov 14:50 | EMA pullback | buy | 15:05 consolidation | +1.4 at 14:55 | -12.0 at 15:10 | Tue 03 Nov 15:10 | stopped by IG: the stop at IG | -12.0 | +2.2 | -12.5 | +1.2 | c |
| 28 | Tue 03 Nov 18:05 | EMA pullback | buy | 18:30 consolidation; 19:35 emerging trend down; 19:55 consolidation | +2.3 at 18:10 | -12.0 at 20:00 | Tue 03 Nov 20:00 | stopped by IG: the stop at IG | -12.0 | +4.0 | -3.1 | -2.7 | c |
| 29 | Tue 03 Nov 18:05 | EMA pullback | buy | 18:30 consolidation; 19:35 emerging trend down; 19:55 consolidation | +2.3 at 18:10 | -12.0 at 20:00 | Tue 03 Nov 20:00 | stopped by IG: the stop at IG | -12.0 | +4.0 | -3.1 | -2.7 | c |
| 30 | Wed 04 Nov 01:00 | EMA pullback | buy | 02:10 possible reversal down; 02:20 emerging trend down; 02:25 emerging trend up; 04:15 consolidation; 04:35 emerging trend up | +30.0 at 04:35 | -8.3 at 01:05 | Wed 04 Nov 04:35 | take profit hit at IG: the take profit at IG (30 pips) | +30.0 | -4.1 | -30.6 | -20.7 | d |
| 31 | Wed 04 Nov 01:00 | EMA pullback | buy | 02:10 possible reversal down; 02:20 emerging trend down; 02:25 emerging trend up; 04:15 consolidation; 04:35 emerging trend up | +30.0 at 04:35 | -8.3 at 01:05 | Wed 04 Nov 04:35 | take profit hit at IG: the take profit at IG (30 pips) | +30.0 | -4.1 | -30.6 | -20.7 | d |
| 32 | Wed 04 Nov 01:00 | EMA pullback | buy | 02:10 possible reversal down; 02:20 emerging trend down; 02:25 emerging trend up; 04:15 consolidation; 04:35 emerging trend up | +30.0 at 04:35 | -7.2 at 01:05 | Wed 04 Nov 04:35 | take profit hit at IG: the take profit at IG (30 pips) | +30.0 | -3.0 | -29.5 | -19.6 | d |
| 33 | Wed 04 Nov 02:35 | EMA pullback | buy | none | +3.3 at 03:05 | -12.0 at 03:15 | Wed 04 Nov 03:15 | stopped by IG: the stop at IG | -12.0 | +19.4 | -6.5 | -5.8 | a (also c) |
| 34 | Wed 04 Nov 02:35 | EMA pullback | buy | none | +3.3 at 03:05 | -12.0 at 03:15 | Wed 04 Nov 03:15 | stopped by IG: the stop at IG | -12.0 | +19.4 | -6.5 | -5.8 | a (also c) |
| 35 | Wed 04 Nov 04:05 | EMA pullback | buy | 04:15 consolidation; 04:35 emerging trend up; 04:45 consolidation | +4.0 at 04:35 | -12.0 at 04:50 | Wed 04 Nov 04:50 | stopped by IG: the stop at IG | -12.0 | +2.6 | -14.6 | -1.7 | c |
| 36 | Wed 04 Nov 04:35 | EMA pullback | buy | none | -6.6 at 04:40 | -12.0 at 04:40 | Wed 04 Nov 04:40 | stopped by IG: the stop at IG | -12.0 | +2.9 | -19.2 | -8.1 | c |
| 37 | Wed 04 Nov 04:35 | EMA pullback | buy | none | -6.6 at 04:40 | -12.0 at 04:40 | Wed 04 Nov 04:40 | stopped by IG: the stop at IG | -12.0 | +2.9 | -19.2 | -8.1 | c |
| 38 | Wed 04 Nov 05:45 | EMA pullback | buy | 06:00 emerging trend down; 06:40 emerging trend up; 07:15 consolidation; 07:20 emerging trend up; 07:45 trend up, strong push; 08:00 trend up, slow grind | +30.0 at 08:45 | -9.6 at 06:25 | Wed 04 Nov 08:45 | take profit hit at IG: the take profit at IG (30 pips) | +30.0 | +8.1 | -14.6 | -12.8 | d |
| 39 | Wed 04 Nov 06:50 | EMA pullback | buy | 07:15 consolidation; 07:20 emerging trend up; 07:45 trend up, strong push; 08:00 trend up, slow grind | +30.0 at 09:15 | -7.8 at 07:05 | Wed 04 Nov 09:15 | take profit hit at IG: the take profit at IG (30 pips) | +30.0 | +5.8 | -24.2 | -18.9 | d |
| 40 | Wed 04 Nov 07:20 | EMA pullback | buy | 07:45 trend up, strong push; 08:00 trend up, slow grind | +30.0 at 10:15 | -1.1 at 07:25 | Wed 04 Nov 10:15 | take profit hit at IG: the take profit at IG (30 pips) | +30.0 | -1.3 | -29.1 | -11.8 | d |
| 41 | Wed 04 Nov 08:40 | EMA pullback | buy | none | +10.7 at 10:15 | -12.0 at 10:40 | Wed 04 Nov 10:40 | stopped by IG: the stop at IG | -12.0 | +24.2 | -7.3 | +12.6 | a (also b) |
| 42 | Wed 04 Nov 08:45 | EMA pullback | buy | none | +9.2 at 10:15 | -12.0 at 10:40 | Wed 04 Nov 10:40 | stopped by IG: the stop at IG | -12.0 | +22.7 | -8.8 | +11.1 | a |
| 43 | Wed 04 Nov 10:15 | EMA pullback | buy | none | -3.1 at 10:25 | -12.0 at 10:30 | Wed 04 Nov 10:30 | stopped by IG: the stop at IG | -12.0 | +11.8 | -18.9 | +8.2 | c |
| 44 | Thu 05 Nov 04:00 | EMA pullback | buy | 04:10 consolidation; 05:15 ranging; 06:25 consolidation; 07:00 emerging trend up; 07:15 emerging trend down | +4.3 at 07:05 | -12.0 at 07:20 | Thu 05 Nov 07:20 | stopped by IG: the stop at IG | -12.0 | -1.4 | -19.7 | -14.2 | c |
| 45 | Thu 05 Nov 07:00 | EMA pullback | buy | 07:15 emerging trend down | +1.2 at 07:05 | -12.0 at 07:15 | Thu 05 Nov 07:15 | stopped by IG: the stop at IG | -12.0 | -0.4 | -22.8 | -16.0 | c |
| 46 | Thu 05 Nov 22:00 | EMA pullback | sell | none | -12.0 at 22:00 | -12.0 at 22:00 | Thu 05 Nov 22:00 | stopped by IG: the stop at IG | -12.0 | +2.9 | -17.6 | -2.8 | c |
| 47 | Fri 06 Nov 02:00 | EMA pullback | sell | 02:35 consolidation; 02:45 emerging trend down; 03:15 trend down, slow grind; 05:10 consolidation; 05:35 emerging trend up; 05:45 consolidation; 05:50 emerging trend up; 06:00 consolidation; 06:45 emerging trend down; 07:10 trend down, strong push; 07:25 trend down, slow grind; 10:35 possible reversal up; 10:40 emerging trend up; 12:00 emerging trend down; 12:20 emerging trend up; 12:50 ranging; 13:10 emerging trend down; 13:15 trend down, slow grind; 13:55 trend down, strong push | +100.0 at 14:15 | -7.0 at 02:25 | Fri 06 Nov 14:15 | take profit hit at IG: the take profit at IG (100 pips) | +100.0 | +0.9 | -34.2 | -19.0 | d |
| 48 | Fri 06 Nov 02:55 | EMA pullback | sell | 03:15 trend down, slow grind; 05:10 consolidation; 05:35 emerging trend up; 05:45 consolidation; 05:50 emerging trend up; 06:00 consolidation; 06:45 emerging trend down; 07:10 trend down, strong push; 07:25 trend down, slow grind; 10:35 possible reversal up; 10:40 emerging trend up; 12:00 emerging trend down; 12:20 emerging trend up; 12:50 ranging; 13:10 emerging trend down; 13:15 trend down, slow grind; 13:55 trend down, strong push; 14:35 possible reversal up; 14:40 emerging trend up; 17:30 consolidation; 17:50 emerging trend down; 18:10 consolidation; 18:20 emerging trend down; 18:35 emerging trend up; 19:05 emerging trend down; 20:05 emerging trend up; 20:30 consolidation | +99.2 at 14:15 | -1.6 at 03:00 | Fri 06 Nov 20:30 | forced close: 20:30 UK close | +90.7 | +3.4 | -14.6 | -9.7 | d |
| 49 | Fri 06 Nov 04:10 | EMA pullback | sell | 05:10 consolidation; 05:35 emerging trend up; 05:45 consolidation; 05:50 emerging trend up; 06:00 consolidation; 06:45 emerging trend down; 07:10 trend down, strong push; 07:25 trend down, slow grind; 10:35 possible reversal up; 10:40 emerging trend up; 12:00 emerging trend down; 12:20 emerging trend up; 12:50 ranging; 13:10 emerging trend down; 13:15 trend down, slow grind; 13:55 trend down, strong push; 14:35 possible reversal up; 14:40 emerging trend up; 17:30 consolidation; 17:50 emerging trend down; 18:10 consolidation; 18:20 emerging trend down; 18:35 emerging trend up; 19:05 emerging trend down; 20:05 emerging trend up; 20:30 consolidation | +82.8 at 14:15 | -9.4 at 04:55 | Fri 06 Nov 20:30 | forced close: 20:30 UK close | +74.3 | +3.4 | -14.6 | -9.7 | d |
| 50 | Fri 06 Nov 04:10 | EMA pullback | sell | 05:10 consolidation; 05:35 emerging trend up; 05:45 consolidation; 05:50 emerging trend up; 06:00 consolidation; 06:45 emerging trend down; 07:10 trend down, strong push; 07:25 trend down, slow grind; 10:35 possible reversal up; 10:40 emerging trend up; 12:00 emerging trend down; 12:20 emerging trend up; 12:50 ranging; 13:10 emerging trend down; 13:15 trend down, slow grind; 13:55 trend down, strong push; 14:35 possible reversal up; 14:40 emerging trend up; 17:30 consolidation; 17:50 emerging trend down; 18:10 consolidation; 18:20 emerging trend down; 18:35 emerging trend up; 19:05 emerging trend down; 20:05 emerging trend up; 20:30 consolidation | +82.8 at 14:15 | -9.4 at 04:55 | Fri 06 Nov 20:30 | forced close: 20:30 UK close | +74.3 | +3.4 | -14.6 | -9.7 | d |
| 51 | Fri 06 Nov 06:45 | EMA pullback | sell | 07:10 trend down, strong push; 07:25 trend down, slow grind; 10:35 possible reversal up; 10:40 emerging trend up; 12:00 emerging trend down; 12:20 emerging trend up; 12:50 ranging; 13:10 emerging trend down; 13:15 trend down, slow grind; 13:55 trend down, strong push; 14:35 possible reversal up; 14:40 emerging trend up; 17:30 consolidation; 17:50 emerging trend down; 18:10 consolidation; 18:20 emerging trend down; 18:35 emerging trend up; 19:05 emerging trend down; 20:05 emerging trend up; 20:30 consolidation | +74.8 at 14:15 | -3.0 at 06:50 | Fri 06 Nov 20:30 | forced close: 20:30 UK close | +66.3 | +3.4 | -14.6 | -9.7 | d |
| 52 | Fri 06 Nov 06:45 | EMA pullback | sell | 07:10 trend down, strong push; 07:25 trend down, slow grind; 10:35 possible reversal up; 10:40 emerging trend up; 12:00 emerging trend down; 12:20 emerging trend up; 12:50 ranging; 13:10 emerging trend down; 13:15 trend down, slow grind; 13:55 trend down, strong push; 14:35 possible reversal up; 14:40 emerging trend up; 17:30 consolidation; 17:50 emerging trend down; 18:10 consolidation; 18:20 emerging trend down; 18:35 emerging trend up; 19:05 emerging trend down; 20:05 emerging trend up; 20:30 consolidation | +74.8 at 14:15 | -3.0 at 06:50 | Fri 06 Nov 20:30 | forced close: 20:30 UK close | +66.3 | +3.4 | -14.6 | -9.7 | d |
| 53 | Fri 06 Nov 08:40 | EMA pullback | sell | 10:35 possible reversal up; 10:40 emerging trend up; 12:00 emerging trend down; 12:20 emerging trend up; 12:50 ranging; 13:10 emerging trend down; 13:15 trend down, slow grind; 13:55 trend down, strong push; 14:35 possible reversal up; 14:40 emerging trend up; 17:30 consolidation; 17:50 emerging trend down; 18:10 consolidation; 18:20 emerging trend down; 18:35 emerging trend up; 19:05 emerging trend down; 20:05 emerging trend up; 20:30 consolidation | +51.4 at 14:15 | -11.3 at 12:20 | Fri 06 Nov 20:30 | forced close: 20:30 UK close | +42.9 | +3.4 | -14.6 | -9.7 | d |
| 54 | Fri 06 Nov 08:40 | EMA pullback | sell | 10:35 possible reversal up; 10:40 emerging trend up; 12:00 emerging trend down; 12:20 emerging trend up | +11.4 at 10:20 | -12.0 at 12:20 | Fri 06 Nov 12:20 | stopped by IG: the stop at IG | -12.0 | +62.5 | +2.2 | +56.5 | a (also b) |
| 55 | Fri 06 Nov 09:00 | EMA pullback | sell | 10:35 possible reversal up; 10:40 emerging trend up | +8.1 at 10:20 | -12.0 at 11:25 | Fri 06 Nov 11:25 | stopped by IG: the stop at IG | -12.0 | +20.1 | -3.5 | +11.1 | a |
| 56 | Fri 06 Nov 13:30 | EMA pullback | sell | 13:55 trend down, strong push; 14:35 possible reversal up; 14:40 emerging trend up; 17:30 consolidation; 17:50 emerging trend down; 18:10 consolidation; 18:20 emerging trend down; 18:35 emerging trend up; 19:05 emerging trend down; 20:05 emerging trend up; 20:30 consolidation | +34.6 at 14:15 | -8.3 at 13:35 | Fri 06 Nov 20:30 | forced close: 20:30 UK close | +26.1 | +3.4 | -14.6 | -9.7 | d |
| 57 | Fri 06 Nov 13:30 | EMA pullback | sell | 13:55 trend down, strong push; 14:35 possible reversal up; 14:40 emerging trend up; 17:30 consolidation; 17:50 emerging trend down; 18:10 consolidation; 18:20 emerging trend down; 18:35 emerging trend up; 19:05 emerging trend down; 20:05 emerging trend up; 20:30 consolidation | +34.6 at 14:15 | -8.3 at 13:35 | Fri 06 Nov 20:30 | forced close: 20:30 UK close | +26.1 | +3.4 | -14.6 | -9.7 | d |
| 58 | Fri 06 Nov 13:30 | EMA pullback | sell | 13:55 trend down, strong push; 14:35 possible reversal up; 14:40 emerging trend up; 17:30 consolidation; 17:50 emerging trend down; 18:10 consolidation; 18:20 emerging trend down; 18:35 emerging trend up; 19:05 emerging trend down; 20:05 emerging trend up; 20:30 consolidation | +34.6 at 14:15 | -8.3 at 13:35 | Fri 06 Nov 20:30 | forced close: 20:30 UK close | +26.1 | +3.4 | -14.6 | -9.7 | d |
| 59 | Fri 06 Nov 19:50 | EMA pullback | sell | 20:05 emerging trend up; 20:30 consolidation | -0.8 at 19:55 | -6.0 at 20:05 | Fri 06 Nov 20:30 | forced close: 20:30 UK close | -2.7 | +3.4 | -14.6 | -9.7 | c |

#### slow grind (18)

| # | Entry (UK) | Strategy | Dir | Analyser changes while open | Best (pips at UK time) | Worst | Closed (UK) | What closed it | Pips | 2 h after: further in its favour (max) | further against (max) | at 2 h | Group |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Mon 26 Oct 06:05 | slow grind | sell | 06:35 consolidation; 07:20 emerging trend down; 07:30 trend down, slow grind | +17.7 at 08:00 | -5.5 at 06:50 | Mon 26 Oct 08:05 | close: the profit lock: back to 10 pips up after 15 up | +10.0 | +17.8 | -0.5 | +14.5 | a |
| 2 | Mon 26 Oct 08:25 | slow grind | sell | 10:25 consolidation; 11:00 emerging trend up; 11:10 consolidation; 11:15 emerging trend down; 11:25 consolidation; 11:35 ranging; 11:55 emerging trend down; 12:55 emerging trend up; 13:05 emerging trend down | +20.0 at 13:55 | -2.8 at 12:50 | Mon 26 Oct 13:55 | take profit hit at IG: the take profit at IG (20 pips) | +20.0 | +5.7 | -14.8 | -8.7 | d |
| 3 | Tue 27 Oct 05:45 | slow grind | sell | 06:25 consolidation; 06:50 emerging trend down; 07:05 trend down, slow grind; 08:10 consolidation; 08:50 emerging trend down; 09:00 consolidation; 09:10 emerging trend down; 09:25 trend down, slow grind | +20.0 at 09:30 | -4.6 at 06:10 | Tue 27 Oct 09:30 | take profit hit at IG: the take profit at IG (20 pips) | +20.0 | +3.4 | -14.8 | -12.7 | d |
| 4 | Tue 27 Oct 16:05 | slow grind | sell | 17:20 ranging; 17:35 emerging trend down; 18:25 consolidation; 18:45 emerging trend down; 18:55 consolidation; 19:55 emerging trend down | +4.7 at 16:15 | -10.3 at 17:20 | Tue 27 Oct 20:30 | forced close: 20:30 UK close | +0.0 | +6.7 | -9.2 | +3.5 | c |
| 5 | Wed 28 Oct 04:45 | slow grind | sell | 04:50 consolidation; 05:10 emerging trend down; 05:45 emerging trend up; 06:00 consolidation; 06:35 emerging trend down; 06:45 trend down, slow grind | +20.0 at 07:15 | -3.2 at 05:00 | Wed 28 Oct 07:15 | take profit hit at IG: the take profit at IG (20 pips) | +20.0 | -1.1 | -23.2 | -20.2 | d |
| 6 | Wed 28 Oct 10:20 | slow grind | sell | 12:10 consolidation; 12:15 emerging trend up; 12:30 emerging trend down; 13:05 emerging trend up; 13:15 consolidation | +5.5 at 11:00 | -15.0 at 13:30 | Wed 28 Oct 13:30 | stopped by IG: the stop at IG | -15.0 | +8.4 | -10.0 | -5.8 | d |
| 7 | Wed 28 Oct 15:30 | slow grind | buy | none | +17.2 at 16:55 | -9.0 at 15:50 | Wed 28 Oct 17:00 | close: the profit lock: back to 10 pips up after 15 up | +10.0 | +23.7 | -25.5 | +3.1 | a |
| 8 | Thu 29 Oct 05:05 | slow grind | sell | 07:20 consolidation; 07:30 emerging trend up; 07:40 consolidation; 07:50 emerging trend up; 08:05 trend up, slow grind; 08:20 consolidation; 08:50 emerging trend down | +20.0 at 09:20 | -12.2 at 08:00 | Thu 29 Oct 09:20 | take profit hit at IG: the take profit at IG (20 pips) | +20.0 | +1.7 | -30.8 | -30.8 | d |
| 9 | Fri 30 Oct 08:15 | slow grind | buy | 10:45 possible reversal down; 11:00 trend up, slow grind | +20.0 at 11:05 | -3.5 at 08:20 | Fri 30 Oct 11:05 | take profit hit at IG: the take profit at IG (20 pips) | +20.0 | +1.0 | -38.7 | -37.5 | d |
| 10 | Fri 30 Oct 13:20 | slow grind | sell | none | +19.2 at 14:05 | -4.2 at 13:30 | Fri 30 Oct 14:10 | close: the profit lock: back to 10 pips up after 15 up | +10.0 | +3.9 | -19.8 | -19.5 | d |
| 11 | Mon 02 Nov 08:00 | slow grind | buy | none | +20.0 at 08:45 | -5.4 at 08:05 | Mon 02 Nov 08:45 | take profit hit at IG: the take profit at IG (20 pips) | +20.0 | +11.4 | -33.0 | -33.0 | d |
| 12 | Mon 02 Nov 19:40 | slow grind | sell | 20:10 consolidation; 20:20 ranging; 20:30 consolidation | +3.4 at 19:50 | -10.3 at 20:00 | Mon 02 Nov 20:30 | forced close: 20:30 UK close | -1.8 | +4.2 | -11.8 | -6.1 | c |
| 13 | Wed 04 Nov 00:15 | slow grind | buy | 00:35 trend up, slow grind | +20.0 at 01:15 | -4.7 at 00:50 | Wed 04 Nov 01:15 | take profit hit at IG: the take profit at IG (20 pips) | +20.0 | +19.1 | -3.5 | +14.8 | a |
| 14 | Wed 04 Nov 08:30 | slow grind | buy | 10:45 possible reversal down; 11:05 emerging trend down | +12.4 at 10:15 | -15.0 at 11:05 | Wed 04 Nov 11:05 | stopped by IG: the stop at IG | -15.0 | +30.6 | +0.5 | +29.1 | a (also b) |
| 15 | Wed 04 Nov 15:35 | slow grind | sell | 15:40 trend down, slow grind | +8.0 at 16:45 | -15.0 at 17:25 | Wed 04 Nov 17:25 | stopped by IG: the stop at IG | -15.0 | +17.1 | -0.8 | +10.3 | a |
| 16 | Thu 05 Nov 08:00 | slow grind | sell | 08:05 trend down, slow grind; 09:30 ranging; 09:50 emerging trend down; 10:05 trend down, slow grind | +21.6 at 11:50 | -14.3 at 09:00 | Thu 05 Nov 12:00 | close: the profit lock: back to 10 pips up after 15 up | +9.7 | +4.8 | -23.8 | -3.1 | d |
| 17 | Thu 05 Nov 17:45 | slow grind | buy | 18:30 consolidation | +1.3 at 17:50 | -15.0 at 18:30 | Thu 05 Nov 18:30 | stopped by IG: the stop at IG | -15.0 | -0.3 | -21.9 | -16.3 | c |
| 18 | Fri 06 Nov 01:55 | slow grind | sell | 02:35 consolidation; 02:45 emerging trend down; 03:15 trend down, slow grind; 05:10 consolidation; 05:35 emerging trend up; 05:45 consolidation; 05:50 emerging trend up; 06:00 consolidation; 06:45 emerging trend down; 07:10 trend down, strong push; 07:25 trend down, slow grind; 10:35 possible reversal up; 10:40 emerging trend up; 12:00 emerging trend down; 12:20 emerging trend up; 12:50 ranging; 13:10 emerging trend down; 13:15 trend down, slow grind; 13:55 trend down, strong push | +100.0 at 14:15 | -3.8 at 02:25 | Fri 06 Nov 14:15 | take profit hit at IG: the take profit at IG (100 pips) | +100.0 | +4.1 | -31.0 | -15.8 | d |

#### breakout (11)

| # | Entry (UK) | Strategy | Dir | Analyser changes while open | Best (pips at UK time) | Worst | Closed (UK) | What closed it | Pips | 2 h after: further in its favour (max) | further against (max) | at 2 h | Group |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Tue 27 Oct 07:00 | breakout | sell | 07:05 trend down, slow grind; 08:10 consolidation; 08:50 emerging trend down; 09:00 consolidation; 09:10 emerging trend down; 09:25 trend down, slow grind; 10:25 consolidation; 10:35 emerging trend down; 10:45 consolidation; 11:20 emerging trend up; 11:40 emerging trend down; 11:55 emerging trend up | +17.9 at 09:40 | -6.0 at 12:10 | Tue 27 Oct 12:10 | stopped by IG: the stop at IG | -6.0 | +16.6 | -3.4 | +2.5 | a (also b) |
| 2 | Thu 29 Oct 14:45 | breakout | buy | 15:05 consolidation; 15:35 emerging trend down; 17:35 consolidation; 18:35 emerging trend down; 18:55 consolidation; 20:10 emerging trend up; 20:25 trend up, slow grind; 00:50 ranging; 01:00 emerging trend up | +50.0 at 01:05 | -1.1 at 14:50 | Fri 30 Oct 01:05 | take profit hit at IG: the take profit at IG (50 pips) | +50.0 | +5.9 | -11.6 | -1.6 | d |
| 3 | Tue 03 Nov 10:15 | breakout | sell | 10:30 consolidation | -0.6 at 10:20 | -6.0 at 10:30 | Tue 03 Nov 10:30 | stopped by IG: the stop at IG | -6.0 | +9.8 | -3.9 | +3.1 | c |
| 4 | Tue 03 Nov 13:45 | breakout | buy | none | -6.0 at 13:45 | -6.0 at 13:45 | Tue 03 Nov 13:45 | stopped by IG: the stop at IG | -6.0 | +8.5 | -18.2 | -15.7 | c |
| 5 | Tue 03 Nov 14:50 | breakout | buy | none | -0.9 at 14:55 | -6.0 at 14:55 | Tue 03 Nov 14:55 | stopped by IG: the stop at IG | -6.0 | +3.2 | -19.7 | -10.2 | c |
| 6 | Tue 03 Nov 18:05 | breakout | buy | 18:30 consolidation | +3.6 at 18:10 | -6.0 at 19:10 | Tue 03 Nov 19:10 | stopped by IG: the stop at IG | -6.0 | +3.7 | -7.2 | -5.6 | c |
| 7 | Wed 04 Nov 20:05 | breakout | buy | 20:25 consolidation; 20:35 emerging trend up; 20:45 consolidation | +4.6 at 20:35 | -9.4 at 22:00 | Wed 04 Nov 22:00 | stopped by IG: the stop at IG | -9.4 | +16.1 | -1.6 | +13.4 | a (also c) |
| 8 | Thu 05 Nov 07:00 | breakout | buy | none | +1.7 at 07:05 | -6.0 at 07:10 | Thu 05 Nov 07:10 | stopped by IG: the stop at IG | -6.0 | -1.3 | -28.3 | -15.0 | c |
| 9 | Thu 05 Nov 09:50 | breakout | sell | 10:05 trend down, slow grind | +1.4 at 10:00 | -6.0 at 10:05 | Thu 05 Nov 10:05 | stopped by IG: the stop at IG | -6.0 | +19.4 | -18.6 | -7.0 | a (also c) |
| 10 | Thu 05 Nov 18:35 | breakout | sell | 19:00 consolidation; 19:50 emerging trend up; 20:40 consolidation; 21:10 emerging trend down; 21:20 emerging trend up; 21:35 emerging trend down; 21:45 consolidation; 22:00 emerging trend down; 23:10 consolidation; 23:20 emerging trend up; 23:40 consolidation; 00:20 emerging trend down; 01:40 trend down, slow grind; 02:35 consolidation; 02:45 emerging trend down; 03:15 trend down, slow grind; 05:10 consolidation; 05:35 emerging trend up; 05:45 consolidation; 05:50 emerging trend up; 06:00 consolidation; 06:45 emerging trend down | +50.0 at 06:45 | -3.4 at 22:00 | Fri 06 Nov 06:45 | take profit hit at IG: the take profit at IG (50 pips) | +50.0 | +23.6 | -2.5 | +20.9 | a |
| 11 | Fri 06 Nov 17:50 | breakout | sell | 18:10 consolidation; 18:20 emerging trend down; 18:35 emerging trend up; 19:05 emerging trend down; 20:05 emerging trend up; 20:30 consolidation | +7.9 at 19:50 | -3.5 at 18:00 | Fri 06 Nov 20:30 | forced close: 20:30 UK close | +3.8 | +3.4 | -14.6 | -9.7 | d |

#### level reversal (20)

| # | Entry (UK) | Strategy | Dir | Analyser changes while open | Best (pips at UK time) | Worst | Closed (UK) | What closed it | Pips | 2 h after: further in its favour (max) | further against (max) | at 2 h | Group |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Mon 26 Oct 13:55 | level reversal | sell | 14:00 trend down, slow grind | +6.5 at 14:00 | -12.7 at 14:45 | Mon 26 Oct 14:45 | stopped by IG: the stop at IG | -12.7 | +7.8 | -5.2 | -3.0 | d |
| 2 | Mon 26 Oct 14:45 | level reversal | buy | 15:50 consolidation; 16:40 emerging trend up; 17:00 consolidation; 17:20 emerging trend up; 17:30 trend up, slow grind; 18:50 consolidation; 19:00 emerging trend down; 20:05 consolidation; 20:30 emerging trend down | +13.1 at 17:30 | -5.7 at 15:00 | Mon 26 Oct 20:30 | forced close: 20:30 UK close | -4.6 | +1.2 | -13.6 | -2.1 | b |
| 3 | Wed 28 Oct 13:55 | level reversal | sell | 14:25 ranging; 15:05 emerging trend up; 15:15 trend up, slow grind | +7.4 at 14:15 | -15.5 at 16:15 | Wed 28 Oct 16:15 | stopped by IG: the stop at IG | -15.5 | +10.9 | -12.2 | +7.0 | d |
| 4 | Wed 28 Oct 16:15 | level reversal | buy | 18:00 consolidation; 18:25 emerging trend down | +11.6 at 16:55 | -16.4 at 18:30 | Wed 28 Oct 18:30 | stopped by IG: the stop at IG | -16.4 | +44.5 | +8.3 | +31.0 | a (also b) |
| 5 | Thu 29 Oct 09:35 | level reversal | buy | 10:20 consolidation | +20.0 at 10:55 | +1.1 at 09:40 | Thu 29 Oct 10:55 | take profit hit at IG: the take profit at IG (20 pips) | +20.0 | +13.5 | -9.7 | -2.7 | d |
| 6 | Thu 29 Oct 13:30 | level reversal | buy | 13:40 consolidation | +20.0 at 14:20 | -5.5 at 13:40 | Thu 29 Oct 14:20 | take profit hit at IG: the take profit at IG (20 pips) | +20.0 | +38.1 | -6.9 | +28.3 | a |
| 7 | Thu 29 Oct 16:30 | level reversal | sell | 17:35 consolidation; 18:35 emerging trend down; 18:55 consolidation; 20:10 emerging trend up; 20:25 trend up, slow grind | +6.9 at 18:40 | -16.6 at 20:25 | Thu 29 Oct 20:30 | forced close: 20:30 UK close | -14.9 | +3.3 | -9.1 | -2.4 | d |
| 8 | Fri 30 Oct 06:40 | level reversal | sell | 07:10 emerging trend up | +1.8 at 06:45 | -16.5 at 07:20 | Fri 30 Oct 07:20 | stopped by IG: the stop at IG | -16.5 | +8.7 | -16.9 | -16.2 | c |
| 9 | Fri 30 Oct 07:25 | level reversal | buy | 07:35 trend up, slow grind | +20.0 at 10:05 | -13.4 at 07:50 | Fri 30 Oct 10:05 | take profit hit at IG: the take profit at IG (20 pips) | +20.0 | +2.2 | -10.2 | -4.9 | d |
| 10 | Fri 30 Oct 13:25 | level reversal | sell | 14:45 possible reversal up; 15:10 trend down, slow grind; 15:25 possible reversal up; 15:30 emerging trend up; 15:50 emerging trend down; 16:00 emerging trend up; 16:20 trend up, slow grind; 16:30 consolidation; 16:45 emerging trend down; 17:00 emerging trend up; 17:20 emerging trend down; 18:35 emerging trend up; 18:45 emerging trend down; 19:00 consolidation; 19:10 emerging trend up; 19:35 emerging trend down; 19:50 emerging trend up; 20:05 consolidation; 20:20 ranging; 20:25 emerging trend down | +18.3 at 14:05 | -13.8 at 16:15 | Fri 30 Oct 20:30 | forced close: 20:30 UK close | -4.1 | +7.6 | -4.5 | +3.0 | b |
| 11 | Mon 02 Nov 06:00 | level reversal | sell | 06:10 emerging trend up; 06:25 emerging trend down; 06:40 emerging trend up; 06:50 consolidation; 06:55 emerging trend up | +4.0 at 06:30 | -9.4 at 07:20 | Mon 02 Nov 07:20 | stopped by IG: the stop at IG | -9.4 | -1.6 | -41.8 | -36.6 | c |
| 12 | Mon 02 Nov 07:25 | level reversal | buy | none | +20.0 at 08:40 | -1.3 at 07:30 | Mon 02 Nov 08:40 | take profit hit at IG: the take profit at IG (20 pips) | +20.0 | +17.6 | -24.5 | -22.7 | a |
| 13 | Mon 02 Nov 11:05 | level reversal | buy | 13:15 consolidation; 14:00 emerging trend down; 14:10 ranging; 14:30 emerging trend up; 17:15 consolidation; 17:30 ranging; 18:10 consolidation; 18:20 emerging trend down; 18:40 trend down, slow grind; 20:10 consolidation; 20:20 ranging; 20:30 consolidation | +18.6 at 13:35 | -9.2 at 18:45 | Mon 02 Nov 20:30 | forced close: 20:30 UK close | -1.3 | +3.6 | -9.9 | -9.9 | b |
| 14 | Tue 03 Nov 11:50 | level reversal | buy | 12:35 consolidation; 12:45 ranging; 12:55 emerging trend up; 13:10 consolidation; 13:15 emerging trend up; 13:25 emerging trend down | +20.0 at 13:30 | -6.3 at 12:40 | Tue 03 Nov 13:30 | take profit hit at IG: the take profit at IG (20 pips) | +20.0 | +2.7 | -20.2 | -18.6 | d |
| 15 | Wed 04 Nov 06:15 | level reversal | sell | 06:40 emerging trend up; 07:15 consolidation; 07:20 emerging trend up | +1.0 at 06:25 | -17.4 at 07:25 | Wed 04 Nov 07:25 | stopped by IG: the stop at IG | -17.4 | -0.5 | -25.0 | -18.1 | c |
| 16 | Wed 04 Nov 07:25 | level reversal | buy | 07:45 trend up, strong push; 08:00 trend up, slow grind | +20.0 at 08:45 | +0.3 at 07:30 | Wed 04 Nov 08:45 | take profit hit at IG: the take profit at IG (20 pips) | +20.0 | +9.1 | -13.6 | -11.8 | d |
| 17 | Wed 04 Nov 12:40 | level reversal | sell | 12:55 emerging trend up; 13:15 trend up, slow grind; 14:50 consolidation; 14:55 emerging trend down; 15:15 trend down, slow grind | +20.0 at 15:15 | -18.2 at 13:15 | Wed 04 Nov 15:15 | take profit hit at IG: the take profit at IG (20 pips) | +20.0 | +12.6 | -7.8 | -4.3 | d |
| 18 | Wed 04 Nov 17:10 | level reversal | buy | 17:30 consolidation; 18:50 emerging trend down; 19:00 consolidation; 19:50 emerging trend up; 20:00 consolidation; 20:05 emerging trend up; 20:25 consolidation | +7.5 at 17:25 | -10.6 at 18:45 | Wed 04 Nov 20:30 | forced close: 20:30 UK close | +3.2 | +3.1 | -13.1 | -8.5 | d |
| 19 | Thu 05 Nov 07:15 | level reversal | sell | 07:40 trend down, strong push | +20.0 at 08:00 | +0.5 at 07:20 | Thu 05 Nov 08:00 | take profit hit at IG: the take profit at IG (20 pips) | +20.0 | +6.4 | -15.5 | +3.9 | d |
| 20 | Fri 06 Nov 08:55 | level reversal | sell | 10:35 possible reversal up; 10:40 emerging trend up; 12:00 emerging trend down; 12:20 emerging trend up; 12:50 ranging; 13:10 emerging trend down; 13:15 trend down, slow grind | +11.1 at 10:20 | -12.5 at 12:20 | Fri 06 Nov 13:15 | forced close: closed 15 minutes before big news | +5.8 | +44.4 | -12.3 | +14.5 | a |

#### Bollinger bounce (37)

| # | Entry (UK) | Strategy | Dir | Analyser changes while open | Best (pips at UK time) | Worst | Closed (UK) | What closed it | Pips | 2 h after: further in its favour (max) | further against (max) | at 2 h | Group |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Mon 26 Oct 06:00 | Bollinger bounce | buy | none | -2.6 at 06:05 | -6.0 at 06:10 | Mon 26 Oct 06:10 | stopped by IG: the stop at IG | -6.0 | +6.8 | -16.6 | -8.6 | c |
| 2 | Mon 26 Oct 09:05 | Bollinger bounce | buy | none | +0.6 at 09:20 | -6.0 at 09:30 | Mon 26 Oct 09:30 | stopped by IG: the stop at IG | -6.0 | +7.2 | -4.2 | +1.3 | c |
| 3 | Mon 26 Oct 14:10 | Bollinger bounce | buy | none | +12.1 at 15:20 | -0.1 at 14:20 | Mon 26 Oct 15:45 | close: a confirmed rejection at a level: previous_day_low 13348.7, turning_low 13348.7, round_number 13350 | +4.3 | +17.5 | +1.0 | +13.8 | a |
| 4 | Mon 26 Oct 17:50 | Bollinger bounce | sell | 18:50 consolidation; 19:00 emerging trend down; 20:05 consolidation; 20:30 emerging trend down | +11.1 at 20:30 | -4.3 at 18:10 | Mon 26 Oct 20:30 | forced close: 20:30 UK close | +11.1 | +1.7 | -9.7 | +0.6 | d |
| 5 | Tue 27 Oct 07:20 | Bollinger bounce | buy | 08:10 consolidation | +4.2 at 07:30 | -5.0 at 08:00 | Tue 27 Oct 08:10 | close: a confirmed rejection at a level: previous_day_low 13327.1, new_york_session_low 13327.1, turning_low 13327.1, turning_low 13327.8, london_session_high 13329.6 | -5.0 | +5.3 | -13.2 | -3.4 | c |
| 6 | Tue 27 Oct 09:55 | Bollinger bounce | buy | 10:25 consolidation; 10:35 emerging trend down | +2.4 at 10:10 | -6.0 at 10:35 | Tue 27 Oct 10:35 | stopped by IG: the stop at IG | -6.0 | +23.3 | +0.1 | +18.0 | a (also c) |
| 7 | Tue 27 Oct 12:35 | Bollinger bounce | sell | 13:20 consolidation; 13:30 emerging trend down | +13.1 at 13:35 | -5.7 at 13:00 | Tue 27 Oct 14:00 | close: a confirmed rejection at a level: new_york_session_low 13316.6 | +6.0 | +13.1 | -10.3 | +9.0 | d |
| 8 | Tue 27 Oct 16:40 | Bollinger bounce | buy | 17:20 ranging; 17:35 emerging trend down | +8.8 at 17:20 | -2.1 at 16:45 | Tue 27 Oct 17:35 | close: a confirmed rejection at a level: S1 13318.4 | +4.1 | +2.7 | -7.8 | +1.8 | d |
| 9 | Wed 28 Oct 07:25 | Bollinger bounce | buy | 08:30 consolidation; 08:40 emerging trend down | +16.0 at 08:30 | +1.3 at 07:55 | Wed 28 Oct 08:40 | close: a confirmed rejection at a level: london_session_high 13295.1, previous_day_low 13295.5, new_york_session_low 13296.4 | +11.4 | +5.4 | -11.2 | -6.4 | d |
| 10 | Wed 28 Oct 10:35 | Bollinger bounce | buy | none | -3.1 at 10:40 | -6.0 at 10:40 | Wed 28 Oct 10:40 | stopped by IG: the stop at IG | -6.0 | +12.4 | -7.8 | +8.4 | c |
| 11 | Wed 28 Oct 11:15 | Bollinger bounce | buy | 12:10 consolidation; 12:15 emerging trend up; 12:30 emerging trend down | +11.5 at 12:10 | -3.2 at 11:20 | Wed 28 Oct 12:30 | close: a confirmed rejection at a level: turning_low 13291.1, new_york_session_high 13292.8, previous_day_low 13295.5, london_session_high 13296.4, new_york_session_low 13296.4 | +4.7 | +16.5 | -2.9 | +2.4 | a |
| 12 | Wed 28 Oct 13:55 | Bollinger bounce | sell | 14:25 ranging | +7.4 at 14:15 | -3.3 at 14:05 | Wed 28 Oct 14:35 | close: a confirmed rejection at a level: S1 13284.2, new_york_session_low 13284.4, turning_low 13291.1 | +1.4 | +2.3 | -22.0 | -20.2 | d |
| 13 | Wed 28 Oct 15:20 | Bollinger bounce | sell | none | -0.3 at 15:25 | -5.4 at 15:30 | Wed 28 Oct 15:35 | close: a confirmed rejection at a level: round_number 13300, turning_low 13300.6 | -5.4 | +10.1 | -16.1 | -3.2 | c |
| 14 | Wed 28 Oct 15:50 | Bollinger bounce | sell | none | -4.4 at 15:55 | -6.0 at 15:55 | Wed 28 Oct 15:55 | stopped by IG: the stop at IG | -6.0 | +1.5 | -20.9 | +1.5 | c |
| 15 | Wed 28 Oct 17:05 | Bollinger bounce | sell | 18:00 consolidation; 18:25 emerging trend down | +23.7 at 18:30 | -6.0 at 18:35 | Wed 28 Oct 18:35 | stopped by IG: the stop at IG | -6.0 | +3.7 | -20.1 | -7.9 | b |
| 16 | Thu 29 Oct 06:30 | Bollinger bounce | buy | none | +0.9 at 06:45 | -6.0 at 06:55 | Thu 29 Oct 06:55 | stopped by IG: the stop at IG | -6.0 | +23.0 | -3.2 | +0.0 | a (also c) |
| 17 | Thu 29 Oct 08:15 | Bollinger bounce | sell | 08:20 consolidation; 08:50 emerging trend down; 09:30 trend down, slow grind | +18.5 at 09:25 | -2.9 at 08:55 | Thu 29 Oct 09:35 | close: a confirmed rejection at a level: london_session_high 13296.4, turning_high 13296.4, round_number 13300, turning_low 13300.6, london_session_low 13302.4, turning_low 13302.5 | +10.3 | -2.0 | -27.8 | -24.6 | d |
| 18 | Thu 29 Oct 09:35 | Bollinger bounce | buy | 10:20 consolidation; 12:00 emerging trend down | +27.1 at 11:45 | +1.1 at 09:40 | Thu 29 Oct 12:00 | close: a confirmed rejection at a level: london_session_high 13332.0, turning_high 13334.5 | +15.4 | +18.1 | -20.1 | +3.7 | a |
| 19 | Thu 29 Oct 13:30 | Bollinger bounce | buy | 13:40 consolidation; 14:25 emerging trend up; 14:40 consolidation; 14:45 emerging trend up; 15:05 consolidation; 15:35 emerging trend down | +58.1 at 15:50 | -5.5 at 13:40 | Thu 29 Oct 16:30 | close: a confirmed rejection at a level: turning_low 13376.1, R2 13377.1, turning_low 13378.7, new_york_session_high 13379.4 | +46.1 | +7.1 | -6.0 | -3.5 | d |
| 20 | Fri 30 Oct 07:45 | Bollinger bounce | sell | none | +2.6 at 07:50 | -6.0 at 08:00 | Fri 30 Oct 08:00 | stopped by IG: the stop at IG | -6.0 | +2.5 | -24.7 | -21.4 | c |
| 21 | Fri 30 Oct 10:40 | Bollinger bounce | sell | 10:45 possible reversal down; 11:00 trend up, slow grind | +0.9 at 10:45 | -6.0 at 11:00 | Fri 30 Oct 11:00 | stopped by IG: the stop at IG | -6.0 | +32.2 | -2.9 | +26.7 | a (also c) |
| 22 | Fri 30 Oct 11:20 | Bollinger bounce | sell | 11:25 emerging trend down; 11:40 consolidation | +7.4 at 12:00 | -2.2 at 11:40 | Fri 30 Oct 12:20 | close: a confirmed rejection at a level: new_york_session_low 13421.3 | +0.5 | +54.3 | -1.0 | +45.2 | a |
| 23 | Fri 30 Oct 15:25 | Bollinger bounce | buy | 15:30 emerging trend up | +4.9 at 15:30 | -6.0 at 15:45 | Fri 30 Oct 15:45 | stopped by IG: the stop at IG | -6.0 | +19.6 | -1.8 | +0.5 | a (also c) |
| 24 | Fri 30 Oct 16:25 | Bollinger bounce | sell | 16:30 consolidation; 16:45 emerging trend down; 17:00 emerging trend up; 17:20 emerging trend down | +13.3 at 17:55 | -3.8 at 16:55 | Fri 30 Oct 18:10 | close: a confirmed rejection at a level: turning_low 13380.2, turning_low 13382.3, turning_low 13382.8, new_york_session_high 13384.4 | +5.5 | +1.8 | -6.8 | -5.6 | d |
| 25 | Mon 02 Nov 09:25 | Bollinger bounce | sell | 09:30 emerging trend down; 11:05 emerging trend up | +35.4 at 10:50 | -1.9 at 09:30 | Mon 02 Nov 11:05 | close: a confirmed rejection at a level: round_number 13400, london_session_low 13400.1, turning_high 13400.6, turning_high 13401.5, turning_high 13403.2 | +25.0 | +2.6 | -13.4 | -9.3 | d |
| 26 | Mon 02 Nov 18:55 | Bollinger bounce | buy | 20:10 consolidation; 20:20 ranging; 20:30 consolidation | +11.2 at 20:00 | -2.3 at 19:50 | Mon 02 Nov 20:30 | forced close: 20:30 UK close | +3.3 | +3.6 | -9.9 | -9.9 | d |
| 27 | Tue 03 Nov 06:45 | Bollinger bounce | sell | 06:50 consolidation; 07:00 emerging trend up | +0.6 at 06:50 | -6.0 at 07:00 | Tue 03 Nov 07:00 | stopped by IG: the stop at IG | -6.0 | +4.9 | -13.1 | -4.5 | c |
| 28 | Tue 03 Nov 08:20 | Bollinger bounce | sell | 09:00 consolidation; 09:25 emerging trend up | +7.5 at 09:15 | -4.4 at 08:25 | Tue 03 Nov 09:25 | close: a confirmed rejection at a level: pivot 13411.6 | +1.4 | +10.9 | -7.3 | +10.0 | d |
| 29 | Wed 04 Nov 10:40 | Bollinger bounce | sell | 10:45 possible reversal down; 11:05 emerging trend down | +9.4 at 11:05 | -6.0 at 11:40 | Wed 04 Nov 11:40 | stopped by IG: the stop at IG | -6.0 | +2.6 | -20.5 | -12.3 | d |
| 30 | Wed 04 Nov 13:25 | Bollinger bounce | sell | none | -3.5 at 13:30 | -6.0 at 13:30 | Wed 04 Nov 13:30 | stopped by IG: the stop at IG | -6.0 | +37.3 | -2.0 | +34.8 | a (also c) |
| 31 | Wed 04 Nov 14:00 | Bollinger bounce | sell | none | -5.0 at 14:05 | -6.0 at 14:05 | Wed 04 Nov 14:05 | stopped by IG: the stop at IG | -6.0 | +26.9 | -2.5 | +15.7 | a (also c) |
| 32 | Wed 04 Nov 14:30 | Bollinger bounce | sell | none | -6.0 at 14:30 | -6.0 at 14:30 | Wed 04 Nov 14:30 | stopped by IG: the stop at IG | -6.0 | +29.8 | -1.4 | +24.7 | a (also c) |
| 33 | Wed 04 Nov 14:30 | Bollinger bounce | sell | none | -6.0 at 14:30 | -6.0 at 14:30 | Wed 04 Nov 14:30 | stopped by IG: the stop at IG | -6.0 | +29.8 | -1.4 | +24.7 | a (also c) |
| 34 | Wed 04 Nov 15:40 | Bollinger bounce | buy | none | +3.7 at 16:05 | -6.0 at 16:10 | Wed 04 Nov 16:10 | stopped by IG: the stop at IG | -6.0 | +13.0 | -11.0 | +5.9 | c |
| 35 | Wed 04 Nov 17:10 | Bollinger bounce | buy | 17:30 consolidation | +7.5 at 17:25 | -6.0 at 18:30 | Wed 04 Nov 18:30 | stopped by IG: the stop at IG | -6.0 | +9.4 | -4.6 | +9.1 | d |
| 36 | Thu 05 Nov 08:15 | Bollinger bounce | buy | none | +1.3 at 08:20 | -6.0 at 08:25 | Thu 05 Nov 08:25 | stopped by IG: the stop at IG | -6.0 | +7.9 | -16.4 | -14.1 | c |
| 37 | Thu 05 Nov 08:50 | Bollinger bounce | buy | none | +2.6 at 09:00 | -6.0 at 09:10 | Thu 05 Nov 09:10 | stopped by IG: the stop at IG | -6.0 | +1.2 | -17.1 | -15.3 | c |

#### range trade (7)

| # | Entry (UK) | Strategy | Dir | Analyser changes while open | Best (pips at UK time) | Worst | Closed (UK) | What closed it | Pips | 2 h after: further in its favour (max) | further against (max) | at 2 h | Group |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Mon 26 Oct 11:50 | range trade | sell | 11:55 emerging trend down | +6.7 at 12:05 | -2.0 at 12:15 | Mon 26 Oct 12:20 | close: a confirmed rejection at a level: turning_high 13341.7, london_session_low 13341.8, new_york_session_low 13345.4 | +2.0 | +25.1 | -5.2 | +12.2 | a |
| 2 | Tue 27 Oct 17:30 | range trade | sell | 17:35 emerging trend down | +8.1 at 18:00 | -2.4 at 17:35 | Tue 27 Oct 18:15 | close: a confirmed rejection at a level: new_york_session_low 13304.6, turning_low 13306.5, london_session_low 13307.2, turning_low 13307.2 | +3.9 | +2.0 | -7.0 | +1.2 | d |
| 3 | Mon 02 Nov 14:20 | range trade | buy | 14:30 emerging trend up | +12.1 at 15:20 | -2.5 at 14:25 | Mon 02 Nov 16:00 | close: a confirmed rejection at a level: turning_high 13418.6 | +4.9 | +8.7 | -6.4 | -0.4 | d |
| 4 | Mon 02 Nov 17:35 | range trade | sell | 18:10 consolidation; 18:20 emerging trend down; 18:40 trend down, slow grind | +13.7 at 18:45 | -3.7 at 17:50 | Mon 02 Nov 18:55 | close: a confirmed rejection at a level: round_number 13400, london_session_low 13400.1, turning_high 13400.6, turning_high 13401.5, turning_high 13403.2, new_york_session_low 13405.0 | +7.3 | +1.0 | -12.7 | -5.9 | d |
| 5 | Tue 03 Nov 10:00 | range trade | sell | 10:10 emerging trend down; 10:30 consolidation; 10:35 emerging trend up | +10.5 at 10:15 | +2.4 at 10:30 | Tue 03 Nov 10:35 | close: a confirmed rejection at a level: new_york_session_low 13402.5, turning_high 13403.2, turning_high 13406.0, turning_high 13406.5, turning_high 13406.7, london_session_low 13406.9, turning_high 13407.4, turning_high 13409.2 | +2.8 | +12.0 | -1.7 | +6.3 | d |
| 6 | Tue 03 Nov 12:50 | range trade | buy | 12:55 emerging trend up; 13:10 consolidation; 13:15 emerging trend up; 13:25 emerging trend down; 13:35 consolidation; 13:45 emerging trend up | +19.0 at 13:30 | -2.7 at 12:55 | Tue 03 Nov 13:50 | close: a confirmed rejection at a level: turning_high 13418.6, new_york_session_high 13419.3, london_session_high 13426.4, turning_high 13426.4 | +4.6 | +15.5 | -11.2 | -5.1 | a |
| 7 | Thu 05 Nov 06:05 | range trade | buy | 06:25 consolidation; 07:00 emerging trend up; 07:15 emerging trend down | +7.8 at 07:05 | -5.2 at 06:15 | Thu 05 Nov 07:15 | stopped by IG: the stop at IG | -2.3 | +0.2 | -22.2 | -15.4 | d |

## 3. Classes

### Live

| Strategy | Trades | Pips | a: trades | a: pips | a: left behind (further move after the close) | b: trades | b: pips | b: given back (best less result) | c: trades | c: pips | d: trades | d: pips |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EMA pullback | 4 | -48.0 | 0 | +0.0 | 0.0 | 0 | +0.0 | 0.0 | 2 | -24.0 | 2 | -24.0 |
| slow grind | 4 | -10.2 | 2 | +7.3 | 37.3 | 0 | +0.0 | 0.0 | 2 | -17.5 | 0 | +0.0 |
| breakout | 3 | -0.3 | 3 | -0.3 | 70.7 | 0 | +0.0 | 0.0 | 0 | +0.0 | 0 | +0.0 |
| level reversal | 2 | +8.8 | 1 | -11.2 | 19.2 | 0 | +0.0 | 0.0 | 0 | +0.0 | 1 | +20.0 |
| Bollinger bounce | 4 | +4.8 | 2 | -12.0 | 63.5 | 0 | +0.0 | 0.0 | 1 | -6.0 | 1 | +22.8 |
| range trade | 3 | -18.0 | 1 | -6.0 | 18.0 | 0 | +0.0 | 0.0 | 2 | -12.0 | 0 | +0.0 |
| **All** | 20 | -62.9 | 9 | -22.2 | 208.7 | 0 | +0.0 | 0.0 | 7 | -59.5 | 4 | +18.8 |

### Replay

| Strategy | Trades | Pips | a: trades | a: pips | a: left behind (further move after the close) | b: trades | b: pips | b: given back (best less result) | c: trades | c: pips | d: trades | d: pips |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EMA pullback | 59 | +686.4 | 9 | -66.0 | 229.8 | 4 | -48.0 | 125.8 | 20 | -230.7 | 26 | +1031.1 |
| slow grind | 18 | +217.9 | 5 | +10.0 | 108.3 | 0 | +0.0 | 0.0 | 3 | -16.8 | 10 | +224.7 |
| breakout | 11 | +52.4 | 4 | +28.6 | 75.7 | 0 | +0.0 | 0.0 | 5 | -30.0 | 2 | +53.8 |
| level reversal | 20 | +56.2 | 4 | +29.4 | 144.6 | 3 | -10.0 | 60.0 | 3 | -43.3 | 10 | +80.1 |
| Bollinger bounce | 37 | +20.1 | 12 | -23.1 | 328.3 | 1 | -6.0 | 29.7 | 11 | -64.4 | 13 | +113.6 |
| range trade | 7 | +23.1 | 2 | +6.6 | 40.6 | 0 | +0.0 | 0.0 | 0 | +0.0 | 5 | +16.5 |
| **All** | 152 | +1056.1 | 36 | -14.5 | 927.3 | 8 | -64.0 | 215.5 | 42 | -385.2 | 66 | +1519.8 |

Overlaps: 5 live and 13 replay trades in group a also never reached 5 pips up (they are stopped-out trades after which price went 15 or more their way); 6 trades in group a were also b.

What closed the trades in each group (live and replay together):

| Group | What closed it | Trades | Pips |
|---|---|---|---|
| a. closed too early | closed by IG's system at market (not at its stop or take profit) | 3 | -12.2 |
| a. closed too early | forced close: closed 15 minutes before big news | 1 | +5.8 |
| a. closed too early | rejection at a level | 6 | +31.5 |
| a. closed too early | slow grind 15/10 lock | 2 | +20.0 |
| a. closed too early | stop | 27 | -241.8 |
| a. closed too early | take profit | 6 | +160.0 |
| b. held too long | 20:30 UK close | 3 | -10.0 |
| b. held too long | stop | 5 | -54.0 |
| c. should never have opened | 20:30 UK close | 4 | -7.0 |
| c. should never have opened | rejection at a level | 2 | -10.4 |
| c. should never have opened | stop | 43 | -427.3 |
| d. managed about right | 20:30 UK close | 14 | +499.6 |
| d. managed about right | rejection at a level | 14 | +152.8 |
| d. managed about right | slow grind 15/10 lock | 2 | +19.7 |
| d. managed about right | stop | 9 | -93.5 |
| d. managed about right | take profit | 31 | +960.0 |

## 4. Each strategy's results by condition

### Analyser state and trend type at entry

**Live**

| Strategy | Analyser state and trend type at entry | Trades | Won | Lost | Pips | Average |
|---|---|---|---|---|---|---|
| EMA pullback | emerging trend | 3 | 0 | 3 | -36.0 | -12.0 |
| EMA pullback | trend, slow grind | 1 | 0 | 1 | -12.0 | -12.0 |
| slow grind | trend, slow grind | 4 | 1 | 3 | -10.2 | -2.6 |
| breakout | emerging trend | 3 | 1 | 2 | -0.3 | -0.1 |
| level reversal | emerging trend | 2 | 1 | 1 | +8.8 | +4.4 |
| Bollinger bounce | trend, slow grind | 4 | 1 | 3 | +4.8 | +1.2 |
| range trade | ranging | 3 | 0 | 3 | -18.0 | -6.0 |

**Replay**

| Strategy | Analyser state and trend type at entry | Trades | Won | Lost | Pips | Average |
|---|---|---|---|---|---|---|
| EMA pullback | emerging trend | 32 | 12 | 20 | +262.6 | +8.2 |
| EMA pullback | trend, slow grind | 27 | 14 | 13 | +423.8 | +15.7 |
| slow grind | trend, slow grind | 15 | 10 | 4 | +203.2 | +13.5 |
| slow grind | trend, strong push | 3 | 2 | 1 | +14.7 | +4.9 |
| breakout | emerging trend | 11 | 3 | 8 | +52.4 | +4.8 |
| level reversal | emerging trend | 11 | 5 | 6 | +27.8 | +2.5 |
| level reversal | trend, slow grind | 9 | 5 | 4 | +28.4 | +3.2 |
| Bollinger bounce | trend, slow grind | 34 | 13 | 21 | +0.6 | +0.0 |
| Bollinger bounce | possible reversal | 3 | 2 | 1 | +19.5 | +6.5 |
| range trade | ranging | 7 | 6 | 1 | +23.1 | +3.3 |

### With or against the trend

**Live**

| Strategy | With or against the trend | Trades | Won | Lost | Pips | Average |
|---|---|---|---|---|---|---|
| EMA pullback | with the trend | 4 | 0 | 4 | -48.0 | -12.0 |
| slow grind | with the trend | 4 | 1 | 3 | -10.2 | -2.6 |
| breakout | with the trend | 3 | 1 | 2 | -0.3 | -0.1 |
| level reversal | with the trend | 2 | 1 | 1 | +8.8 | +4.4 |
| Bollinger bounce | against the trend | 4 | 1 | 3 | +4.8 | +1.2 |
| range trade | no trend | 3 | 0 | 3 | -18.0 | -6.0 |

**Replay**

| Strategy | With or against the trend | Trades | Won | Lost | Pips | Average |
|---|---|---|---|---|---|---|
| EMA pullback | with the trend | 59 | 26 | 33 | +686.4 | +11.6 |
| slow grind | with the trend | 18 | 12 | 5 | +217.9 | +12.1 |
| breakout | with the trend | 11 | 3 | 8 | +52.4 | +4.8 |
| level reversal | with the trend | 15 | 7 | 8 | +33.1 | +2.2 |
| level reversal | against the trend | 5 | 3 | 2 | +23.1 | +4.6 |
| Bollinger bounce | against the trend | 37 | 15 | 22 | +20.1 | +0.5 |
| range trade | no trend | 7 | 6 | 1 | +23.1 | +3.3 |

### Time in that state before entry

**Live**

| Strategy | Time in that state before entry | Trades | Won | Lost | Pips | Average |
|---|---|---|---|---|---|---|
| EMA pullback | 15 to 60 min | 2 | 0 | 2 | -24.0 | -12.0 |
| EMA pullback | over 60 min | 1 | 0 | 1 | -12.0 | -12.0 |
| EMA pullback | under 15 min | 1 | 0 | 1 | -12.0 | -12.0 |
| slow grind | under 15 min | 3 | 1 | 2 | +2.5 | +0.8 |
| slow grind | 15 to 60 min | 1 | 0 | 1 | -12.7 | -12.7 |
| breakout | under 15 min | 3 | 1 | 2 | -0.3 | -0.1 |
| level reversal | under 15 min | 1 | 1 | 0 | +20.0 | +20.0 |
| level reversal | 15 to 60 min | 1 | 0 | 1 | -11.2 | -11.2 |
| Bollinger bounce | under 15 min | 2 | 0 | 2 | -12.0 | -6.0 |
| Bollinger bounce | 15 to 60 min | 1 | 0 | 1 | -6.0 | -6.0 |
| Bollinger bounce | over 60 min | 1 | 1 | 0 | +22.8 | +22.8 |
| range trade | 15 to 60 min | 2 | 0 | 2 | -12.0 | -6.0 |
| range trade | under 15 min | 1 | 0 | 1 | -6.0 | -6.0 |

**Replay**

| Strategy | Time in that state before entry | Trades | Won | Lost | Pips | Average |
|---|---|---|---|---|---|---|
| EMA pullback | under 15 min | 22 | 8 | 14 | +205.3 | +9.3 |
| EMA pullback | 15 to 60 min | 22 | 13 | 9 | +438.2 | +19.9 |
| EMA pullback | over 60 min | 15 | 5 | 10 | +42.9 | +2.9 |
| slow grind | 15 to 60 min | 10 | 7 | 3 | +154.7 | +15.5 |
| slow grind | under 15 min | 7 | 5 | 1 | +65.0 | +9.3 |
| slow grind | over 60 min | 1 | 0 | 1 | -1.8 | -1.8 |
| breakout | under 15 min | 11 | 3 | 8 | +52.4 | +4.8 |
| level reversal | under 15 min | 11 | 7 | 4 | +108.7 | +9.9 |
| level reversal | 15 to 60 min | 6 | 1 | 5 | -45.1 | -7.5 |
| level reversal | over 60 min | 3 | 2 | 1 | -7.4 | -2.5 |
| Bollinger bounce | under 15 min | 15 | 8 | 7 | +67.1 | +4.5 |
| Bollinger bounce | 15 to 60 min | 12 | 6 | 6 | +2.3 | +0.2 |
| Bollinger bounce | over 60 min | 10 | 1 | 9 | -49.3 | -4.9 |
| range trade | under 15 min | 4 | 4 | 0 | +20.7 | +5.2 |
| range trade | 15 to 60 min | 3 | 2 | 1 | +2.4 | +0.8 |

### Room to the nearest level in the trade's way (above a buy, below a sell)

**Live**

| Strategy | Room to the nearest level in the trade's way | Trades | Won | Lost | Pips | Average |
|---|---|---|---|---|---|---|
| EMA pullback | under 3 pips | 3 | 0 | 3 | -36.0 | -12.0 |
| EMA pullback | 8 pips or more | 1 | 0 | 1 | -12.0 | -12.0 |
| slow grind | under 3 pips | 3 | 1 | 2 | -7.7 | -2.6 |
| slow grind | 3 to 8 pips | 1 | 0 | 1 | -2.5 | -2.5 |
| breakout | under 3 pips | 2 | 0 | 2 | -12.0 | -6.0 |
| breakout | 3 to 8 pips | 1 | 1 | 0 | +11.7 | +11.7 |
| level reversal | 8 pips or more | 1 | 1 | 0 | +20.0 | +20.0 |
| level reversal | under 3 pips | 1 | 0 | 1 | -11.2 | -11.2 |
| Bollinger bounce | under 3 pips | 4 | 1 | 3 | +4.8 | +1.2 |
| range trade | 3 to 8 pips | 2 | 0 | 2 | -12.0 | -6.0 |
| range trade | under 3 pips | 1 | 0 | 1 | -6.0 | -6.0 |

**Replay**

| Strategy | Room to the nearest level in the trade's way | Trades | Won | Lost | Pips | Average |
|---|---|---|---|---|---|---|
| EMA pullback | under 3 pips | 24 | 13 | 11 | +280.2 | +11.7 |
| EMA pullback | 8 pips or more | 22 | 8 | 14 | +303.2 | +13.8 |
| EMA pullback | 3 to 8 pips | 13 | 5 | 8 | +103.0 | +7.9 |
| slow grind | under 3 pips | 15 | 9 | 5 | +157.9 | +10.5 |
| slow grind | 3 to 8 pips | 3 | 3 | 0 | +60.0 | +20.0 |
| breakout | under 3 pips | 7 | 2 | 5 | +70.0 | +10.0 |
| breakout | 3 to 8 pips | 3 | 1 | 2 | -8.2 | -2.7 |
| breakout | 8 pips or more | 1 | 0 | 1 | -9.4 | -9.4 |
| level reversal | 3 to 8 pips | 10 | 3 | 7 | -21.4 | -2.1 |
| level reversal | under 3 pips | 6 | 3 | 3 | +14.4 | +2.4 |
| level reversal | 8 pips or more | 4 | 4 | 0 | +63.2 | +15.8 |
| Bollinger bounce | under 3 pips | 19 | 7 | 12 | -23.9 | -1.3 |
| Bollinger bounce | 3 to 8 pips | 10 | 6 | 4 | +75.4 | +7.5 |
| Bollinger bounce | 8 pips or more | 8 | 2 | 6 | -31.4 | -3.9 |
| range trade | 3 to 8 pips | 4 | 3 | 1 | +9.3 | +2.3 |
| range trade | under 3 pips | 2 | 2 | 0 | +6.6 | +3.3 |
| range trade | 8 pips or more | 1 | 1 | 0 | +7.3 | +7.3 |

### Day

**Live**

| Strategy | Day | Trades | Won | Lost | Pips | Average |
|---|---|---|---|---|---|---|
| EMA pullback | big news | 3 | 0 | 3 | -36.0 | -12.0 |
| EMA pullback | Mon after big Fri | 1 | 0 | 1 | -12.0 | -12.0 |
| slow grind | Mon after big Fri | 4 | 1 | 3 | -10.2 | -2.6 |
| breakout | big news | 2 | 0 | 2 | -12.0 | -6.0 |
| breakout | Mon after big Fri | 1 | 1 | 0 | +11.7 | +11.7 |
| level reversal | Mon after big Fri | 2 | 1 | 1 | +8.8 | +4.4 |
| Bollinger bounce | big news | 3 | 1 | 2 | +10.8 | +3.6 |
| Bollinger bounce | Mon after big Fri | 1 | 0 | 1 | -6.0 | -6.0 |
| range trade | Mon after big Fri | 3 | 0 | 3 | -18.0 | -6.0 |

**Replay**

| Strategy | Day | Trades | Won | Lost | Pips | Average |
|---|---|---|---|---|---|---|
| EMA pullback | ordinary | 43 | 16 | 27 | +156.0 | +3.6 |
| EMA pullback | big news | 16 | 10 | 6 | +530.4 | +33.2 |
| slow grind | ordinary | 15 | 10 | 4 | +123.2 | +8.2 |
| slow grind | big news | 3 | 2 | 1 | +94.7 | +31.6 |
| breakout | ordinary | 7 | 1 | 6 | +10.6 | +1.5 |
| breakout | big news | 4 | 2 | 2 | +41.8 | +10.4 |
| level reversal | ordinary | 18 | 8 | 10 | +30.4 | +1.7 |
| level reversal | big news | 2 | 2 | 0 | +25.8 | +12.9 |
| Bollinger bounce | ordinary | 35 | 15 | 20 | +32.1 | +0.9 |
| Bollinger bounce | big news | 2 | 0 | 2 | -12.0 | -6.0 |
| range trade | ordinary | 6 | 6 | 0 | +25.4 | +4.2 |
| range trade | big news | 1 | 0 | 1 | -2.3 | -2.3 |

### Time of day (UK)

**Live**

| Strategy | Time of day | Trades | Won | Lost | Pips | Average |
|---|---|---|---|---|---|---|
| EMA pullback | Asia (00-07) | 2 | 0 | 2 | -24.0 | -12.0 |
| EMA pullback | evening (20:30-24) | 1 | 0 | 1 | -12.0 | -12.0 |
| EMA pullback | London morning (07-12) | 1 | 0 | 1 | -12.0 | -12.0 |
| slow grind | Asia (00-07) | 1 | 1 | 0 | +20.0 | +20.0 |
| slow grind | London morning (07-12) | 1 | 0 | 1 | -12.7 | -12.7 |
| slow grind | London/New York (12-16) | 1 | 0 | 1 | -15.0 | -15.0 |
| slow grind | New York afternoon (16-20:30) | 1 | 0 | 1 | -2.5 | -2.5 |
| breakout | London morning (07-12) | 3 | 1 | 2 | -0.3 | -0.1 |
| level reversal | Asia (00-07) | 1 | 1 | 0 | +20.0 | +20.0 |
| level reversal | London morning (07-12) | 1 | 0 | 1 | -11.2 | -11.2 |
| Bollinger bounce | London morning (07-12) | 4 | 1 | 3 | +4.8 | +1.2 |
| range trade | London/New York (12-16) | 3 | 0 | 3 | -18.0 | -6.0 |

**Replay**

| Strategy | Time of day | Trades | Won | Lost | Pips | Average |
|---|---|---|---|---|---|---|
| EMA pullback | London morning (07-12) | 22 | 8 | 14 | +84.9 | +3.9 |
| EMA pullback | Asia (00-07) | 19 | 12 | 7 | +567.9 | +29.9 |
| EMA pullback | London/New York (12-16) | 9 | 3 | 6 | +6.3 | +0.7 |
| EMA pullback | New York afternoon (16-20:30) | 7 | 2 | 5 | +9.3 | +1.3 |
| EMA pullback | evening (20:30-24) | 2 | 1 | 1 | +18.0 | +9.0 |
| slow grind | Asia (00-07) | 6 | 6 | 0 | +190.0 | +31.7 |
| slow grind | London morning (07-12) | 6 | 4 | 2 | +39.7 | +6.6 |
| slow grind | New York afternoon (16-20:30) | 3 | 0 | 2 | -16.8 | -5.6 |
| slow grind | London/New York (12-16) | 3 | 2 | 1 | +5.0 | +1.7 |
| breakout | London morning (07-12) | 4 | 0 | 4 | -24.0 | -6.0 |
| breakout | New York afternoon (16-20:30) | 4 | 2 | 2 | +38.4 | +9.6 |
| breakout | London/New York (12-16) | 3 | 1 | 2 | +38.0 | +12.7 |
| level reversal | London morning (07-12) | 8 | 7 | 1 | +124.5 | +15.6 |
| level reversal | London/New York (12-16) | 6 | 2 | 4 | +3.1 | +0.5 |
| level reversal | New York afternoon (16-20:30) | 3 | 1 | 2 | -28.1 | -9.4 |
| level reversal | Asia (00-07) | 3 | 0 | 3 | -43.3 | -14.4 |
| Bollinger bounce | London morning (07-12) | 16 | 7 | 9 | +15.7 | +1.0 |
| Bollinger bounce | London/New York (12-16) | 12 | 4 | 8 | +10.4 | +0.9 |
| Bollinger bounce | New York afternoon (16-20:30) | 6 | 4 | 2 | +12.0 | +2.0 |
| Bollinger bounce | Asia (00-07) | 3 | 0 | 3 | -18.0 | -6.0 |
| range trade | London morning (07-12) | 2 | 2 | 0 | +4.7 | +2.4 |
| range trade | New York afternoon (16-20:30) | 2 | 2 | 0 | +11.2 | +5.6 |
| range trade | London/New York (12-16) | 2 | 2 | 0 | +9.5 | +4.7 |
| range trade | Asia (00-07) | 1 | 0 | 1 | -2.3 | -2.3 |

## 5. Signals while the trade was open

How often each signal came while the trade was open, before it closed, in each group. For group b, also counted only after the trade had first been 10 pips up; for group c, also only in the first 30 minutes.

### Live

| Signal (while the trade was open, before it closed) | a. closed too early (9) | b. held too long (0) | b: after it was 10+ up | c. never opened (7) | c: in its first 30 min | d. about right (4) |
|---|---|---|---|---|---|---|
| state moved in the trade's favour | 3 (33%) | - | - | 1 (14%) | 1 (14%) | 4 (100%) |
| state turned against the trade | 3 (33%) | - | - | 0 (0%) | 0 (0%) | 2 (50%) |
| state lost its direction (consolidation or ranging) | 5 (56%) | - | - | 4 (57%) | 1 (14%) | 4 (100%) |
| strong push in the trade's favour | 2 (22%) | - | - | 0 (0%) | 0 (0%) | 0 (0%) |
| strong push against the trade | 0 (0%) | - | - | 0 (0%) | 0 (0%) | 0 (0%) |
| consolidation after a push in the trade's favour | 0 (0%) | - | - | 0 (0%) | 0 (0%) | 0 (0%) |
| consolidation after a push against the trade | 0 (0%) | - | - | 0 (0%) | 0 (0%) | 0 (0%) |
| rejection at a level in the trade's favour | 6 (67%) | - | - | 4 (57%) | 2 (29%) | 4 (100%) |
| rejection at a level against the trade | 3 (33%) | - | - | 1 (14%) | 0 (0%) | 3 (75%) |
| MACD histogram crossed in the trade's favour | 1 (11%) | - | - | 1 (14%) | 1 (14%) | 3 (75%) |
| MACD histogram crossed against the trade | 3 (33%) | - | - | 0 (0%) | 0 (0%) | 2 (50%) |
| RSI(3) stretched in the trade's favour (70+ buy, 30- sell) | 5 (56%) | - | - | 5 (71%) | 5 (71%) | 4 (100%) |
| RSI(3) stretched against the trade | 4 (44%) | - | - | 3 (43%) | 1 (14%) | 4 (100%) |
| (no signal of any kind) | 2 (22%) | - | - | 1 (14%) | 1 (14%) | 0 (0%) |

### Replay

| Signal (while the trade was open, before it closed) | a. closed too early (36) | b. held too long (8) | b: after it was 10+ up | c. never opened (42) | c: in its first 30 min | d. about right (66) |
|---|---|---|---|---|---|---|
| state moved in the trade's favour | 15 (42%) | 8 (100%) | 8 (100%) | 7 (17%) | 5 (12%) | 56 (85%) |
| state turned against the trade | 13 (36%) | 7 (88%) | 7 (88%) | 10 (24%) | 7 (17%) | 42 (64%) |
| state lost its direction (consolidation or ranging) | 14 (39%) | 6 (75%) | 6 (75%) | 17 (40%) | 11 (26%) | 50 (76%) |
| strong push in the trade's favour | 1 (3%) | 2 (25%) | 2 (25%) | 0 (0%) | 0 (0%) | 17 (26%) |
| strong push against the trade | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) |
| consolidation after a push in the trade's favour | 1 (3%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 1 (2%) |
| consolidation after a push against the trade | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) |
| rejection at a level in the trade's favour | 24 (67%) | 8 (100%) | 8 (100%) | 17 (40%) | 16 (38%) | 61 (92%) |
| rejection at a level against the trade | 13 (36%) | 7 (88%) | 7 (88%) | 16 (38%) | 11 (26%) | 31 (47%) |
| MACD histogram crossed in the trade's favour | 8 (22%) | 3 (38%) | 2 (25%) | 3 (7%) | 1 (2%) | 43 (65%) |
| MACD histogram crossed against the trade | 8 (22%) | 7 (88%) | 7 (88%) | 7 (17%) | 1 (2%) | 27 (41%) |
| RSI(3) stretched in the trade's favour (70+ buy, 30- sell) | 32 (89%) | 8 (100%) | 8 (100%) | 30 (71%) | 30 (71%) | 66 (100%) |
| RSI(3) stretched against the trade | 24 (67%) | 7 (88%) | 7 (88%) | 24 (57%) | 15 (36%) | 48 (73%) |
| (no signal of any kind) | 2 (6%) | 0 (0%) | 0 (0%) | 4 (10%) | 4 (10%) | 0 (0%) |

### Live and replay together

| Signal (while the trade was open, before it closed) | a. closed too early (45) | b. held too long (8) | b: after it was 10+ up | c. never opened (49) | c: in its first 30 min | d. about right (70) |
|---|---|---|---|---|---|---|
| state moved in the trade's favour | 18 (40%) | 8 (100%) | 8 (100%) | 8 (16%) | 6 (12%) | 60 (86%) |
| state turned against the trade | 16 (36%) | 7 (88%) | 7 (88%) | 10 (20%) | 7 (14%) | 44 (63%) |
| state lost its direction (consolidation or ranging) | 19 (42%) | 6 (75%) | 6 (75%) | 21 (43%) | 12 (24%) | 54 (77%) |
| strong push in the trade's favour | 3 (7%) | 2 (25%) | 2 (25%) | 0 (0%) | 0 (0%) | 17 (24%) |
| strong push against the trade | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) |
| consolidation after a push in the trade's favour | 1 (2%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 1 (1%) |
| consolidation after a push against the trade | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) |
| rejection at a level in the trade's favour | 30 (67%) | 8 (100%) | 8 (100%) | 21 (43%) | 18 (37%) | 65 (93%) |
| rejection at a level against the trade | 16 (36%) | 7 (88%) | 7 (88%) | 17 (35%) | 11 (22%) | 34 (49%) |
| MACD histogram crossed in the trade's favour | 9 (20%) | 3 (38%) | 2 (25%) | 4 (8%) | 2 (4%) | 46 (66%) |
| MACD histogram crossed against the trade | 11 (24%) | 7 (88%) | 7 (88%) | 7 (14%) | 1 (2%) | 29 (41%) |
| RSI(3) stretched in the trade's favour (70+ buy, 30- sell) | 37 (82%) | 8 (100%) | 8 (100%) | 35 (71%) | 35 (71%) | 70 (100%) |
| RSI(3) stretched against the trade | 28 (62%) | 7 (88%) | 7 (88%) | 27 (55%) | 16 (33%) | 52 (74%) |
| (no signal of any kind) | 4 (9%) | 0 (0%) | 0 (0%) | 5 (10%) | 5 (10%) | 0 (0%) |

### How the trades ended when each signal came, and when it did not (live and replay together)

| Signal | Trades it came in | Their pips | Average | Trades it did not come in | Their pips | Average |
|---|---|---|---|---|---|---|
| state moved in the trade's favour | 94 | +1436.8 | +15.3 | 78 | -443.6 | -5.7 |
| state turned against the trade | 77 | +1001.5 | +13.0 | 95 | -8.3 | -0.1 |
| state lost its direction (consolidation or ranging) | 100 | +1118.2 | +11.2 | 72 | -125.0 | -1.7 |
| strong push in the trade's favour | 22 | +859.6 | +39.1 | 150 | +133.6 | +0.9 |
| strong push against the trade | 0 | +0.0 | - | 172 | +993.2 | +5.8 |
| consolidation after a push in the trade's favour | 2 | +60.0 | +30.0 | 170 | +933.2 | +5.5 |
| consolidation after a push against the trade | 0 | +0.0 | - | 172 | +993.2 | +5.8 |
| rejection at a level in the trade's favour | 124 | +1330.6 | +10.7 | 48 | -337.3 | -7.0 |
| rejection at a level against the trade | 74 | +736.5 | +10.0 | 98 | +256.7 | +2.6 |
| MACD histogram crossed in the trade's favour | 62 | +1300.1 | +21.0 | 110 | -306.9 | -2.8 |
| MACD histogram crossed against the trade | 54 | +898.2 | +16.6 | 118 | +95.0 | +0.8 |
| RSI(3) stretched in the trade's favour (70+ buy, 30- sell) | 150 | +1165.1 | +7.8 | 22 | -171.9 | -7.8 |
| RSI(3) stretched against the trade | 114 | +923.5 | +8.1 | 58 | +69.7 | +1.2 |

### By strategy (live and replay together): share of each group's trades in which the signal came

| Strategy | Group (trades) | state in favour | state against | state lost direction | push in favour | push against | consol. after push in favour | consol. after push against | rejection in favour | rejection against | MACD in favour | MACD against | RSI stretched in favour | RSI stretched against |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EMA pullback | a (9) | 22% | 33% | 22% | 11% | 0% | 11% | 0% | 44% | 56% | 11% | 33% | 100% | 78% |
| EMA pullback | b (4) | 100% | 100% | 50% | 50% | 0% | 0% | 0% | 100% | 100% | 0% | 100% | 100% | 100% |
| EMA pullback | c (22) | 27% | 27% | 45% | 0% | 0% | 0% | 0% | 27% | 55% | 14% | 27% | 77% | 73% |
| EMA pullback | d (28) | 100% | 79% | 82% | 50% | 0% | 4% | 0% | 93% | 68% | 71% | 71% | 100% | 86% |
| slow grind | a (7) | 57% | 29% | 43% | 0% | 0% | 0% | 0% | 71% | 71% | 14% | 29% | 100% | 100% |
| slow grind | c (5) | 20% | 0% | 80% | 0% | 0% | 0% | 0% | 20% | 20% | 20% | 20% | 100% | 80% |
| slow grind | d (10) | 80% | 60% | 70% | 10% | 0% | 0% | 0% | 100% | 60% | 40% | 40% | 100% | 70% |
| breakout | a (7) | 71% | 43% | 71% | 14% | 0% | 0% | 0% | 57% | 43% | 14% | 43% | 86% | 57% |
| breakout | c (5) | 0% | 0% | 40% | 0% | 0% | 0% | 0% | 0% | 20% | 0% | 0% | 80% | 20% |
| breakout | d (2) | 100% | 100% | 100% | 0% | 0% | 0% | 0% | 100% | 100% | 100% | 100% | 100% | 100% |
| level reversal | a (5) | 40% | 60% | 80% | 20% | 0% | 0% | 0% | 100% | 60% | 20% | 60% | 100% | 60% |
| level reversal | b (3) | 100% | 100% | 100% | 0% | 0% | 0% | 0% | 100% | 100% | 67% | 100% | 100% | 100% |
| level reversal | c (3) | 33% | 100% | 67% | 0% | 0% | 0% | 0% | 67% | 100% | 0% | 0% | 67% | 100% |
| level reversal | d (11) | 82% | 45% | 64% | 18% | 0% | 0% | 0% | 91% | 55% | 55% | 18% | 100% | 73% |
| Bollinger bounce | a (14) | 21% | 29% | 29% | 0% | 0% | 0% | 0% | 71% | 0% | 29% | 0% | 57% | 43% |
| Bollinger bounce | b (1) | 100% | 0% | 100% | 0% | 0% | 0% | 0% | 100% | 0% | 100% | 0% | 100% | 0% |
| Bollinger bounce | c (12) | 0% | 8% | 17% | 0% | 0% | 0% | 0% | 92% | 0% | 0% | 0% | 50% | 25% |
| Bollinger bounce | d (14) | 57% | 50% | 86% | 0% | 0% | 0% | 0% | 100% | 7% | 79% | 0% | 100% | 57% |
| range trade | a (3) | 67% | 33% | 33% | 0% | 0% | 0% | 0% | 67% | 0% | 33% | 0% | 67% | 33% |
| range trade | c (2) | 0% | 0% | 50% | 0% | 0% | 0% | 0% | 50% | 0% | 0% | 0% | 50% | 0% |
| range trade | d (5) | 100% | 40% | 60% | 0% | 0% | 0% | 0% | 60% | 0% | 60% | 20% | 100% | 60% |

### A fairer comparison: trades that were 10 pips or more up (live and replay together)

Longer trades see more of every signal, so the counts above favour group d, which held longest. Here only the 82 trades that were at some point 10 pips or more up are compared, and only signals that came after that point.

| Signal after it was 10+ up | Trades it came in | Of those, closed at a loss | Their average pips | Trades it did not come in | Of those, closed at a loss | Their average pips |
|---|---|---|---|---|---|---|
| state moved in the trade's favour | 56 | 10 | +25.4 | 26 | 4 | +11.4 |
| state turned against the trade | 47 | 12 | +24.5 | 35 | 2 | +16.2 |
| state lost its direction (consolidation or ranging) | 48 | 9 | +26.2 | 34 | 5 | +13.6 |
| strong push in the trade's favour | 21 | 2 | +41.5 | 61 | 12 | +13.9 |
| strong push against the trade | 0 | 0 | - | 82 | 14 | +21.0 |
| consolidation after a push in the trade's favour | 2 | 0 | +30.0 | 80 | 14 | +20.7 |
| consolidation after a push against the trade | 0 | 0 | - | 82 | 14 | +21.0 |
| rejection at a level in the trade's favour | 65 | 12 | +23.0 | 17 | 2 | +13.0 |
| rejection at a level against the trade | 39 | 12 | +25.8 | 43 | 2 | +16.6 |
| MACD histogram crossed in the trade's favour | 37 | 2 | +34.9 | 45 | 12 | +9.5 |
| MACD histogram crossed against the trade | 39 | 12 | +25.8 | 43 | 2 | +16.6 |
| RSI(3) stretched in the trade's favour (70+ buy, 30- sell) | 81 | 13 | +21.4 | 1 | 1 | -12.0 |
| RSI(3) stretched against the trade | 51 | 13 | +23.4 | 31 | 1 | +17.0 |

### A fairer comparison: signals in the first 30 minutes (live and replay together)

All 172 trades: when each signal came in the trade's first 30 minutes (and the trade was still open), how many ended in group c (never 5 pips up) and their average pips.

| Signal in the first 30 minutes | Trades it came in | Of those, group c | Their average pips | Trades it did not come in | Of those, group c | Their average pips |
|---|---|---|---|---|---|---|
| state moved in the trade's favour | 44 | 6 | +12.3 | 128 | 43 | +3.5 |
| state turned against the trade | 14 | 7 | -5.3 | 158 | 42 | +6.8 |
| state lost its direction (consolidation or ranging) | 38 | 12 | +4.9 | 134 | 37 | +6.0 |
| strong push in the trade's favour | 9 | 0 | +30.0 | 163 | 49 | +4.4 |
| strong push against the trade | 0 | 0 | - | 172 | 49 | +5.8 |
| consolidation after a push in the trade's favour | 0 | 0 | - | 172 | 49 | +5.8 |
| consolidation after a push against the trade | 0 | 0 | - | 172 | 49 | +5.8 |
| rejection at a level in the trade's favour | 105 | 18 | +8.9 | 67 | 31 | +0.9 |
| rejection at a level against the trade | 28 | 11 | +3.6 | 144 | 38 | +6.2 |
| MACD histogram crossed in the trade's favour | 27 | 2 | +16.9 | 145 | 47 | +3.7 |
| MACD histogram crossed against the trade | 2 | 1 | +4.0 | 170 | 48 | +5.8 |
| RSI(3) stretched in the trade's favour (70+ buy, 30- sell) | 147 | 35 | +7.2 | 25 | 14 | -2.7 |
| RSI(3) stretched against the trade | 36 | 16 | -1.2 | 136 | 33 | +7.6 |

### At entry: MACD histogram and a strong push already running (live and replay together)

| At entry | Trades | a | b | c | d | Pips | Average |
|---|---|---|---|---|---|---|---|
| MACD histogram on the trade's side of zero | 84 | 25 | 5 | 24 | 30 | +532.6 | +6.3 |
| MACD histogram on the other side of zero | 88 | 20 | 3 | 25 | 40 | +460.7 | +5.2 |
| RSI(3) already stretched the trade's way (70+ buy, 30- sell) | 94 | 25 | 6 | 28 | 35 | +526.6 | +5.6 |
| RSI(3) not stretched the trade's way | 78 | 20 | 2 | 21 | 35 | +466.6 | +6.0 |
| a strong push running at entry | 3 | 2 | 0 | 0 | 1 | +14.7 | +4.9 |

### How long the trades in each group were open

| Group | Trades | Median minutes open | Median best pips | Median minutes from entry to best |
|---|---|---|---|---|
| a. closed too early | 45 | 75 | +8.1 | 50 |
| b. held too long | 8 | 205 | +18.5 | 100 |
| c. should never have opened | 49 | 34 | +1.3 | 5 |
| d. managed about right | 70 | 160 | +20.0 | 123 |

