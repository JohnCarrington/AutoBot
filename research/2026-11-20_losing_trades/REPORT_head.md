# Losing trades: what is broken, and which strategies lose (AutoBot new server, 20 Nov 2026)

Read-only investigation for Johnny, Fri 20 Nov 2026 (UK = UTC in November; every time below is UTC = UK).
No code, settings or `.env` changed, no restart, no order sent, no stop moved. IG was only read, via the price
service's own read-only check (`data/orders/ig_check_request.json`, GETs only), at 18:43 and 18:53 UTC.

Sources quoted: the bot's order journal `data/orders/GBPUSD/orders.jsonl`, its trade records
`data/records/GBPUSD/trades.jsonl`, the trade manager's decisions `data/trade_manager/GBPUSD/decisions.jsonl`,
the stored 5-minute candles `data/candles/GBPUSD/5m/`, and IG's own activity, transactions and open positions in
every `data/orders/ig_check_result*.json` (26 files, 8–20 Nov). All 106 live trades since 9 Nov were matched to IG:
every one has IG's "Position opened" record, and every closed one has IG's close.

## The short answer

1. **Nothing in the order mechanics is broken.** Every one of the 106 trades since 9 Nov had a stop on IG, on the
   right side of the price, at exactly the distance the bot sent. Every IG stop since 19 Nov 18:44 was a genuine
   hit (the price reached it on the right side), it filled exactly at the stop level, and the spread was a normal
   1.5 pips. Entries opened at the time and price their rules call for, and the trails moved as specified.
   Replaying the live code over the same candles produced every trade since 19 Nov 18:44 at the same candle,
   direction and entry (Step 4). Two of them it made only as ideas: in the week-long replay an earlier paper level
   reversal was still open, so "at most 1" held them back. One fault did happen this week, but in an older version: on 17 Nov IG refused a
   bounce's trail move 31 times, and a +15.6 trade ended at −3.3. The trail fix of 17 Nov 20:36 changed this, and
   there have been no refusals since.
2. **The −£261 trade was a level reversal with a 34.3-pip stop, which its rule allows.** The level reversal sets
   its stop 6 pips beyond the furthest point of the setup, with **no cap**, against a **fixed 20-pip take
   profit**. Today at 13:10 it bought 26.6 pips above the level, so it risked 34.3 pips to make 20. This rule is
   identical in the first build (f99efe1). The two protections approved on 18 Nov (stop at most 20 pips; entry
   within 6 pips of the level) existed only in the Stage 4 build, and the rollback to first-build-plus removed
   them. **`.env` still says `LEVEL_STOPS=on` and `LR_ENTRY_NEAR_LEVEL=on`, but the live code doesn't read them.**
3. **The breakout's live stop is 6 pips, not 12.** Johnny raised it to 12 on 10 Nov (0e1492b). First-build-plus is
   built on 9 Nov's code, so it went back to 6. Two earlier reports wrongly said it takes `STOP_LOSS_PIPS` (12).
   The breakout made no trade in the current version, so this hasn't cost anything yet. **The 12-pip loss today
   (07:15) was the Asian range breakout**, which has its own 12-pip setting, as specified.
4. **The money is being lost by the strategies' rules, not by faults.** From 9 to 20 Nov, judged only on the bot's
   own exits at IG's prices: EMA pullback −138.0 pips (3 wins in 22), slow grind −92.4 (4 in 15), level reversal
   −46.4 (and −52.5 more on trades Johnny closed by hand), range trade −39.5, Bollinger bounce (hourly) −31.5,
   Bollinger bounce 5m −13.7, Asian range breakout −2.3. Only the breakout (+17.1) and the session sweep (+42.4,
   4 from 4) are positive. Every sample is small.
5. **The strategies trade against each other.** At 13:10–13:35 today one move up to 13128 set off a level
   reversal buy and a slow grind buy, then three sells (both bounces and the session sweep), all open together. In
   the current version, 12 pairs of trades were open in opposite directions at the same time. Nothing in the rules
   stops this: rule 11 (one signal, one trade) doesn't cover the level reversal or the bounce 5m (approved as is).

6. **This week (16–20 Nov): 44 trades closed by the bot or IG, 12 won, 31 lost, −274.2 pips (−£2,742).** By cause:
   - 14 trades never went 3 pips their way (−181.6): the signal was wrong;
   - 8 went only 3–8 pips their way (−97.4);
   - 6 were +10.5 to +22.6 and then lost their full stop (−81.8): management;
   - 3 were closed by the bot at a loss (−21.3).

   My recommendations, in order: switch off the EMA pullback (0 from 9 this week) and the slow grind (1 from 5);
   fix the level reversal's risk, or switch it off until then; add break-even at about +10; stop the strategies
   trading against each other; keep the session sweep. See the week review near the end.

Details, proof and suggestions follow.
