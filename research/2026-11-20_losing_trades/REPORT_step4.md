## Step 4. Each strategy's three most recent live trades, replayed through the code

**How:** `replay_live_code.py` runs the stored 5-minute candles through the bot's own engine (`trading/engine.py`:
analyser, strategies, safety rules, order sender in **paper mode**, trade manager), using an exact copy of the
code (`git archive`). A stand-in IG raises an error if anything calls it. Every data folder except the candle store
(read only) is redirected to a temporary copy. Runs:
- (1) the live code 02f6c7e over Sun 15 Nov 21:00 – Fri 20 Nov 18:52, in its own replay mode from the week's open;
- (2) the same code over the week of 9–13 Nov, for the 13 Nov breakout and range trade;
- (3) 02f6c7e started exactly as the live service started (19 Nov 18:44:38), to see the ideas it made, with the
  paper safety refusals kept;
- (4) the Stage 4 code d9e5d0e over 19 Nov to 18:43:54, for the two Stage 4 trades the live code didn't reproduce.

A replay is a check of the code on these named trades, not a judgment of the rules (the live demo is the judge).

| Strategy | Live trade (UTC, version) | Live code 02f6c7e replay | Verdict |
|---|---|---|---|
| level reversal | 20 Nov 13:10 buy (E) | 13:10 buy at 13126.2, stop 34.1 | ✔ the rule called for it, stop included |
| level reversal | 20 Nov 17:55 sell (E) | run (1): not opened, because the 13:10 paper buy was still open (its stop came at 18:35; live, Johnny closed it at 16:11) and the level reversal allows 1 open. Run (3): the idea was made at 17:55 (`"level reversal", "sell"` in the paper safety log) | ✔ the rule called for it |
| level reversal | 20 Nov 18:45 sell (E) | 18:45 sell at 13089.7, stop 14.3 | ✔ |
| EMA pullback | 18 Nov 16:20 sell (C) | 16:20 sell at 13140.8 | ✔ |
| EMA pullback | 19 Nov 19:51 sell (E) | 19:50 candle sell at 13094.8 | ✔ |
| EMA pullback | 20 Nov 18:42 sell (E) | 18:40 candle sell at 13092.3 | ✔ |
| slow grind | 18 Nov 16:37 sell (C) | not opened: in the replay a paper slow grind sell from 04:05 was open all day (at most 1). Under its own code this trade was checked by the 18 Nov review (2c42722) | not reproducible by 02f6c7e (different code and path); no fault found by the 18 Nov review |
| slow grind | 19 Nov 11:00 buy (D) | not opened by 02f6c7e (path: its 07:55 paper buy was stopped, the live Stage 4 bot had none). Run (4), its own code d9e5d0e: 11:00 buy at 13169.7, stop 15 | ✔ under the code that took it |
| slow grind | 20 Nov 13:25 buy (E) | 13:25 buy at 13126.9 | ✔ |
| Bollinger bounce (hourly) | 19 Nov 15:40 buy (D) | 15:40 buy at 13116.3 | ✔ |
| Bollinger bounce (hourly) | 19 Nov 17:20 buy (D) | 17:20 buy at 13105.9 | ✔ |
| Bollinger bounce (hourly) | 20 Nov 13:30 sell (E) | 13:30 sell at 13119.4 | ✔ |
| Bollinger bounce 5m | 20 Nov 07:25 sell (E) | 07:25 sell at 13114.8 | ✔ |
| Bollinger bounce 5m | 20 Nov 13:32 sell (E) | 13:30 candle sell at 13118.9 | ✔ |
| Bollinger bounce 5m | 20 Nov 14:45 sell (E) | 14:45 sell at 13107.4 | ✔ |
| breakout | 13 Nov 06:40 buy (A) | run (2): 06:40 buy at 13231.9, **stop 6** (live then: 12) | ✔ the entry; the stop differs because the live code has 6 |
| breakout | 13 Nov 10:28 sell (A) | run (2): 10:25 candle sell at 13225.3, **stop 6** (live then: 12) | ✔ the entry; stop as above |
| breakout | 18 Nov 15:44 sell (C) | 15:40 candle sell at 13153.7, **stop 6** (live then: 12) | ✔ the entry; stop as above |
| range trade | 13 Nov 09:55 buy (A) | run (2): 09:55 buy at 13232.7 | ✔ |
| range trade | 16 Nov 17:27 sell (B) | 17:25 candle sell at 13193.8 | ✔ |
| range trade | 17 Nov 08:59 sell (B) | 08:55 candle sell at 13190.8 | ✔ |
| session sweep | 19 Nov 12:10 sell (D) | not opened by 02f6c7e (its 09:30 paper sell used the day's Asian-high sweep: once a day). Run (4), d9e5d0e: 12:10 sell at 13151.1, stop 21.8 (live 22) | ✔ under the code that took it |
| session sweep | 20 Nov 07:30 sell (E) | 07:30 sell at 13113.4 | ✔ |
| session sweep | 20 Nov 13:35 sell (E) | 13:35 sell at 13116.2 | ✔ |
| Asian range breakout | 18 Nov 07:30 sell (B) | 07:30 sell at 13179.3 | ✔ |
| Asian range breakout | 19 Nov 07:35 buy (C) | 07:35 buy at 13155.6 | ✔ |
| Asian range breakout | 20 Nov 07:15 buy (E) | 07:15 buy at 13121.0 | ✔ |
| New York open reversal | never traded live | – | – |

The 19 Nov 19:33 level reversal buy (E) isn't among the three most recent, but it was the other trade the
week-long replay didn't open. There, a paper level reversal buy from 17:20 was still open until 20:30. Live, the
Stage 4 code had no such trade. Run (3), which starts as the live service did, made the idea at the 19:30 candle.

**Result: every period-E trade is one the live code's rules call for, at the same candle, direction and entry
price** (entries within 0.4 pips: the replay fills at the candle's trigger, live at the live price). No trade was
taken that its rules would not have taken. The only code difference this exposed is the breakout's stop (6 in the
live code, 12 when those breakouts were live). Older trades that the live code doesn't reproduce were taken by
older code, and the differences come from those versions' different rules and trade paths, as shown.

Side observation from run (3): its level reversal ideas match the live journal's level reversal ideas (sent and
refused) candle for candle, from 19 Nov 19:30 to 20 Nov 18:45. The one exception is a live refusal at 11:30:04
that run (3) didn't make. On 20 Nov the rule fired eight more times while one was open (live journal, `"safety
refused" … "level reversal already has 1 trade(s) open (at most 1)"` at 06:10, 09:30, 09:41, 11:16, 11:22, 11:30,
18:25, 18:30). It fires often around round numbers in a narrow market.
