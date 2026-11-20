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

## Step 0. The −26-pip GBPUSD buy (reported to Johnny first, 18:45 UTC)

- **Did it have a stop on IG?** Yes. IG's activity, 13:10:24: `"Position opened: WDUG25BW", "direction": "BUY",
  "level": 13127.7, "stopLevel": 13093.4, "stopDistance": 34.3, "limitLevel": 13147.7, "limitDistance": 20`.
- **The bot's own record:** journal lines 935–936: `"strategy": "level reversal", "direction": "buy",
  "stop_pips": "32.6", "stop_distance": "34.3", "take_profit_pips": 20, "idea_price": "13126.2"`, then `"opened",
  "deal_id": "DIAAAAYWDUG25BW", "level": "13127.7", "stop_level": 13093.4, "limit_level": 13147.7`.
- **Opened by** the level reversal at 13:10:24 UTC, filled at 13127.7.
- **Why it wasn't stopped out:** the price never reached 13093.4. IG closed it at 16:11:44 at 13101.6, channel
  SYSTEM, not at the stop or the limit (`"profitAndLoss": "£-261.00"`). **Johnny confirmed he closed it by hand.**
  The bot recorded it as `"event": "closed by owner"` (line 979).
- **At 18:53 UTC IG showed one open position:** the level reversal sell opened 18:45:04 at 13088.9, stop 13103.3,
  limit 13068.9. Johnny closed the 17:55 level reversal sell (+2.9) and the 18:42 EMA pullback sell (−1.4) by hand
  at 18:43.

## Which code was running when

Each "Trading ON" in `logs/prices.log*` (the price service starting), and the commit HEAD pointed to at that
moment (`git reflog --date=iso`). The current process started `Thu Nov 19 18:43:54 2026` and is still running.

| Period | From (UTC) | Commits loaded at each restart | What it was |
|---|---|---|---|
| A first build | 9 Nov 00:09 | f99efe1, 2ff445f (9 Nov 12:26), addf1b8, dfa9075, 02a8dfe, 04b3a83, 6ffa36f (11 Nov), 79c5dcf (12 Nov), d96de5f, e24c58f, 1a65151, 714d1c6 (13 Nov) | the first build plus fixes; STOP_LOSS_PIPS 6 → 12 and breakout 6 → 12 on 10 Nov 15:36 |
| B hourly read | 15 Nov 00:16 | b5ca37a, 9b61661 (15 Nov 17:47), e595f6e, aea2275 (16 Nov), 233d054, cc70dc5 (17 Nov) | hourly read, hourly bounce, trend still going, session strategies, STP, trail fix |
| C analyser control | 18 Nov 13:36 | 3d50353 | analyser control stages 1–3 |
| D stage 4 | 19 Nov 09:49 | d9e5d0e | entries/exits + LEVEL_STOPS, LR_ENTRY_NEAR_LEVEL, TRAIL_NO_LOSS, SCALE_OUT_REVERSAL |
| **E first-build-plus** | **19 Nov 18:44** | **02f6c7e** (code = f35bd1b, built on f99efe1) | the live code now |

## Step 1. Every trade

"Rule stop" is the bot's `stop_pips` when sending. "Stop sent" is the `stopDistance` in the order. "IG stop" is
what IG's "Position opened" record shows. Pips and close prices are IG's. "Who": IG stop / IG limit = closed at
IG by the stop or take profit; bot = the bot's own close order; Johnny by hand = IG channel SYSTEM, not at the stop
or limit (Johnny's rule of 11 Nov).

### Since 19 Nov 18:44 (first-build-plus, 02f6c7e)

| Opened UTC | Closed UTC | Strategy | Dir | Entry (IG fill) | Rule stop pips | Stop sent | IG stop level (dist) | TP pips (IG limit) | Close (IG) | IG pips | How closed | Who |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 11-19 19:33 | 11-19 20:16 | level reversal | buy | 13104.4 | 10.9 | 12.6 | 13091.8 (12.6) | 20 (13124.4) | 13100.9 | -3.5 | closed by owner | Johnny by hand |
| 11-19 19:51 | 11-19 20:16 | EMA pullback | sell | 13094.5 | 12 | 12 | 13106.5 (12) | 30 (13064.5) | 13102.4 | -7.9 | closed by owner | Johnny by hand |
| 11-20 06:07 | 11-20 11:59 | level reversal | buy | 13111.4 | 15.4 | 17.3 | 13094.1 (17.3) | 20 (13131.4) | 13094.1 | -17.3 | stopped by IG | IG stop |
| 11-20 07:15 | 11-20 08:00 | Asian range breakout | buy | 13122.3 | 12 | 12 | 13110.3 (12) | 100 (13222.3) | 13110.3 | -12.0 | stopped by IG | IG stop |
| 11-20 07:25 | 11-20 07:45 | Bollinger bounce 5m | sell | 13114.8 | 12 | 12 | 13126.8 (12) | 100 (13014.8) | 13116.5 | -1.7 | close | bot |
| 11-20 07:30 | 11-20 09:13 | session sweep | sell | 13113.5 | 12.0 | 12.0 | 13125.5 (12) | 100 (13013.5) | 13106.0 | 7.5 | stopped by IG | IG stop |
| 11-20 13:10 | 11-20 16:11 | level reversal | buy | 13127.7 | 32.6 | 34.3 | 13093.4 (34.3) | 20 (13147.7) | 13101.6 | -26.1 | closed by owner | Johnny by hand |
| 11-20 13:25 | 11-20 13:41 | slow grind | buy | 13128.3 | 15 | 15 | 13113.3 (15) | 20 (13148.3) | 13113.3 | -15.0 | stopped by IG | IG stop |
| 11-20 13:30 | 11-20 14:32 | Bollinger bounce | sell | 13120.1 | 12 | 12 | 13132.1 (12) | 100 (13020.1) | 13117.2 | 2.9 | stopped by IG | IG stop |
| 11-20 13:32 | 11-20 14:35 | Bollinger bounce 5m | sell | 13118.1 | 12 | 12 | 13130.1 (12) | 100 (13018.1) | 13118.1 | -0.0 | close | bot |
| 11-20 13:35 | 11-20 15:14 | session sweep | sell | 13116.1 | 12.0 | 12.0 | 13128.1 (12) | 100 (13016.1) | 13115.2 | 0.9 | stopped by IG | IG stop |
| 11-20 14:45 | 11-20 15:44 | Bollinger bounce 5m | sell | 13107.1 | 12 | 12 | 13119.1 (12) | 100 (13007.1) | 13119.1 | -12.0 | stopped by IG | IG stop |
| 11-20 17:55 | 11-20 18:43 | level reversal | sell | 13096 | 12.9 | 13.0 | 13109 (13) | 20 (13076) | 13093.1 | 2.9 | closed by owner | Johnny by hand |
| 11-20 18:42 | 11-20 18:43 | EMA pullback | sell | 13091.4 | 12 | 12 | 13103.4 (12) | 30 (13061.4) | 13092.8 | -1.4 | closed by owner | Johnny by hand |
| 11-20 18:45 | OPEN | level reversal | sell | 13088.9 | 14.3 | 14.4 | 13103.3 (14.4) | 20 (13068.9) |  |  |  | still open |

### 9 – 19 Nov, by code version

#### A first build

| Code | Opened UTC | Closed UTC | Strategy | Dir | Entry (IG fill) | Rule stop pips | Stop sent | IG stop level (dist) | TP pips (IG limit) | Close (IG) | IG pips | How closed | Who |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| f99efe1 | 11-09 05:25 | 11-09 08:13 | slow grind | buy | 13380.2 | 15 | 15 | 13365.2 (15) | 20 (13400.2) | 13400.2 | 20.0 | take profit hit at IG | IG limit |
| f99efe1 | 11-09 06:12 | 11-09 08:18 | level reversal | buy | 13385.4 | 11.1 | 12.9 | 13372.5 (12.9) | 20 (13405.4) | 13405.4 | 20.0 | take profit hit at IG | IG limit |
| f99efe1 | 11-09 07:55 | 11-09 15:21 | breakout | buy | 13392.5 | 6 | 6 | 13386.5 (6) | 50 (13442.5) | 13404.2 | 11.7 | closed by owner | Johnny by hand |
| f99efe1 | 11-09 08:25 | 11-09 15:21 | level reversal | buy | 13414.9 | 23.6 | 25.3 | 13389.6 (25.3) | 20 (13434.9) | 13403.7 | -11.2 | closed by owner | Johnny by hand |
| f99efe1 | 11-09 09:00 | 11-09 09:29 | Bollinger bounce | sell | 13408 | 6 | 6 | 13414 (6) | 100 (13308) | 13414.0 | -6.0 | stopped by IG | IG stop |
| f99efe1 | 11-09 09:39 | 11-09 15:21 | slow grind | buy | 13416.8 | 15 | 15 | 13401.8 (15) | 20 (13436.8) | 13404.1 | -12.7 | closed by owner | Johnny by hand |
| 2ff445f | 11-09 13:55 | 11-09 14:43 | range trade | buy | 13418.6 | 6 | 6 | 13412.6 (6) | 100 (13518.6) | 13412.6 | -6.0 | stopped by IG | IG stop |
| 2ff445f | 11-09 14:55 | 11-09 14:58 | range trade | buy | 13415.3 | 6 | 6 | 13409.3 (6) | 100 (13515.3) | 13409.3 | -6.0 | stopped by IG | IG stop |
| 2ff445f | 11-09 15:16 | 11-09 15:20 | range trade | buy | 13410.9 | 6 | 6 | 13404.9 (6) | 100 (13510.9) | 13404.9 | -6.0 | stopped by IG | IG stop |
| 2ff445f | 11-09 15:45 | 11-09 16:17 | slow grind | sell | 13401.6 | 15 | 15 | 13416.6 (15) | 20 (13381.6) | 13416.6 | -15.0 | stopped by IG | IG stop |
| 2ff445f | 11-09 19:55 | 11-09 20:30 | slow grind | buy | 13438.6 | 15 | 15 | 13423.6 (15) | 20 (13458.6) | 13436.1 | -2.5 | forced close | bot (forced) |
| 2ff445f | 11-09 21:02 | 11-09 22:00 | EMA pullback | buy | 13443.6 | 12 | 12 | 13431.6 (12) | 30 (13473.6) | 13431.6 | -12.0 | stopped by IG | IG stop |
| 2ff445f | 11-10 05:01 | 11-10 09:00 | EMA pullback | buy | 13451 | 12 | 12 | 13439 (12) | 100 (13551) | 13439.0 | -12.0 | stopped by IG | IG stop |
| 2ff445f | 11-10 06:12 | 11-10 09:00 | EMA pullback | buy | 13452.8 | 12 | 12 | 13440.8 (12) | 100 (13552.8) | 13440.8 | -12.0 | stopped by IG | IG stop |
| 2ff445f | 11-10 07:21 | 11-10 09:00 | EMA pullback | buy | 13456.1 | 12 | 12 | 13444.1 (12) | 100 (13556.1) | 13444.1 | -12.0 | stopped by IG | IG stop |
| 2ff445f | 11-10 07:55 | 11-10 08:01 | Bollinger bounce | sell | 13449.6 | 6 | 6 | 13455.6 (6) | 100 (13349.6) | 13455.6 | -6.0 | stopped by IG | IG stop |
| 2ff445f | 11-10 08:20 | 11-10 08:24 | Bollinger bounce | sell | 13448.9 | 6 | 6 | 13454.9 (6) | 100 (13348.9) | 13454.9 | -6.0 | stopped by IG | IG stop |
| 2ff445f | 11-10 08:45 | 11-10 10:45 | Bollinger bounce | sell | 13453.7 | 6 | 6 | 13459.7 (6) | 100 (13353.7) | 13430.9 | 22.8 | close | bot |
| 2ff445f | 11-10 09:10 | 11-10 09:24 | breakout | sell | 13432.7 | 6 | 6 | 13438.7 (6) | 50 (13382.7) | 13438.7 | -6.0 | stopped by IG | IG stop |
| 2ff445f | 11-10 11:50 | 11-10 12:02 | breakout | sell | 13422.7 | 6 | 6 | 13428.7 (6) | 50 (13372.7) | 13428.7 | -6.0 | stopped by IG | IG stop |
| 2ff445f | 11-10 13:11 | 11-10 13:29 | breakout | sell | 13419.6 | 6 | 6 | 13425.6 (6) | 50 (13369.6) | 13425.6 | -6.0 | stopped by IG | IG stop |
| 2ff445f | 11-10 13:30 | 11-10 13:30 | slow grind | sell | 13396.5 | 15 | 15 | 13411.5 (15) | 100 (13296.5) | 13411.5 | -15.0 | stopped by IG | IG stop |
| 2ff445f | 11-10 13:56 | 11-10 15:00 | slow grind | sell | 13392.2 | 15 | 15 | 13407.2 (15) | 100 (13292.2) | 13375.1 | 17.1 | close | bot |
| 2ff445f | 11-10 14:06 | 11-10 15:29 | level reversal | sell | 13388.9 | 18.4 | 18.5 | 13407.4 (18.5) | 20 (13368.9) | 13368.9 | 20.0 | take profit hit at IG | IG limit |
| 2ff445f | 11-10 15:19 | 11-10 17:56 | slow grind | sell | 13373 | 15 | 15 | 13388 (15) | 100 (13273) | 13335.2 | 37.8 | closed by owner | Johnny by hand |
| 2ff445f | 11-10 16:26 | 11-10 17:56 | level reversal | sell | 13321 | 20.0 | 20.2 | 13341.2 (20.2) | 20 (13301) | 13335.6 | -14.6 | closed by owner | Johnny by hand |
| 2ff445f | 11-10 17:04 | 11-10 17:12 | Bollinger bounce | buy | 13323.7 | 6 | 6 | 13317.7 (6) | 100 (13423.7) | 13324.3 | 0.6 | closed by owner | Johnny by hand |
| addf1b8 | 11-11 06:20 | 11-11 06:29 | Bollinger bounce | buy | 13342.3 | 6 | 6 | 13336.3 (6) | 100 (13442.3) | 13336.3 | -6.0 | stopped by IG | IG stop |
| dfa9075 | 11-11 06:55 | 11-11 07:30 | Bollinger bounce | buy | 13336.1 | 6 | 6 | 13330.1 (6) | 100 (13436.1) | 13332.8 | -3.3 | close | bot |
| dfa9075 | 11-11 07:32 | 11-11 13:20 | EMA pullback | sell | 13330.9 | 12 | 12 | 13342.9 (12) | 30 (13300.9) | 13300.9 | 30.0 | take profit hit at IG | IG limit |
| dfa9075 | 11-11 08:13 | 11-11 11:47 | slow grind | sell | 13326.6 | 15 | 15 | 13341.6 (15) | 20 (13306.6) | 13316.3 | 10.3 | close | bot |
| dfa9075 | 11-11 08:16 | 11-11 13:51 | EMA pullback | sell | 13323.1 | 12 | 12 | 13335.1 (12) | 30 (13293.1) | 13293.1 | 30.0 | take profit hit at IG | IG limit |
| 02a8dfe | 11-11 08:36 | 11-11 09:30 | Bollinger bounce | buy | 13326.1 | 12 | 12 | 13314.1 (12) | 100 (13426.1) | 13314.1 | -12.0 | stopped by IG | IG stop |
| 02a8dfe | 11-11 09:50 | 11-11 10:50 | Bollinger bounce | buy | 13321.6 | 12 | 12 | 13309.6 (12) | 100 (13421.6) | 13322.0 | 0.4 | close | bot |
| 02a8dfe | 11-11 10:51 | 11-11 13:56 | EMA pullback | sell | 13317 | 12 | 12 | 13329 (12) | 30 (13287) | 13287.0 | 30.0 | take profit hit at IG | IG limit |
| 02a8dfe | 11-11 11:13 | 11-11 12:00 | range trade | buy | 13318.4 | 12 | 12 | 13306.4 (12) | 100 (13418.4) | 13309.3 | -9.1 | close | bot |
| 02a8dfe | 11-11 13:10 | 11-12 02:38 | breakout | sell | 13305.7 | 12 | 12 | 13317.7 (12) | 50 (13255.7) | 13255.7 | 50.0 | take profit hit at IG | IG limit |
| 02a8dfe | 11-11 13:40 | 11-11 14:24 | level reversal | sell | 13294.2 | 13.0 | 13.1 | 13307.3 (13.1) | 20 (13274.2) | 13274.2 | 20.0 | take profit hit at IG | IG limit |
| 02a8dfe | 11-11 14:45 | 11-11 15:14 | slow grind | sell | 13268.7 | 15 | 15 | 13283.7 (15) | 20 (13248.7) | 13283.7 | -15.0 | stopped by IG | IG stop |
| 04b3a83 | 11-11 15:10 | 11-11 17:00 | Bollinger bounce | buy | 13279.3 | 12 | 12 | 13267.3 (12) | 100 (13379.3) | 13279.4 | 0.1 | close | bot |
| 6ffa36f | 11-11 17:37 | 11-11 20:30 | slow grind | sell | 13271.8 | 15 | 15 | 13286.8 (15) | 20 (13251.8) | 13279.3 | -7.5 | forced close | bot (forced) |
| 6ffa36f | 11-11 18:48 | 11-11 22:03 | EMA pullback | sell | 13273.5 | 12 | 12 | 13285.5 (12) | 30 (13243.5) | 13285.5 | -12.0 | stopped by IG | IG stop |
| 6ffa36f | 11-11 21:06 | 11-11 22:00 | EMA pullback | sell | 13270.7 | 12 | 12 | 13282.7 (12) | 30 (13240.7) | 13282.7 | -12.0 | closed at IG | IG (stop) |
| 6ffa36f | 11-12 02:58 | 11-12 07:41 | slow grind | sell | 13255 | 15 | 15 | 13270 (15) | 100 (13155) | 13270.0 | -15.0 | stopped by IG | IG stop |
| 6ffa36f | 11-12 08:33 | 11-12 12:29 | slow grind | buy | 13274.9 | 15 | 15 | 13259.9 (15) | 100 (13374.9) | 13259.9 | -15.0 | stopped by IG | IG stop |
| 6ffa36f | 11-12 10:20 | 11-12 11:22 | breakout | buy | 13279.1 | 12 | 12 | 13267.1 (12) | 50 (13329.1) | 13267.1 | -12.0 | stopped by IG | IG stop |
| 6ffa36f | 11-12 11:30 | 11-12 16:14 | breakout | sell | 13264.6 | 12 | 12 | 13276.6 (12) | 50 (13214.6) | 13243.5 | 21.1 | closed at IG | IG (stop) |
| 79c5dcf | 11-12 19:02 | 11-12 20:02 | EMA pullback | sell | 13225.6 | 12 | 12 | 13237.6 (12) | 100 (13125.6) | 13237.6 | -12.0 | stopped by IG | IG stop |
| 79c5dcf | 11-12 22:00 | 11-12 22:00 | EMA pullback | sell | 13230.7 | 12 | 12 | 13242.7 (12) | 100 (13130.7) | 13242.7 | -12.0 | stopped by IG | IG stop |
| 79c5dcf | 11-12 23:47 | 11-13 01:41 | EMA pullback | sell | 13229.2 | 12 | 12 | 13241.2 (12) | 100 (13129.2) | 13241.2 | -12.0 | stopped by IG | IG stop |
| 79c5dcf | 11-13 06:40 | 11-13 08:22 | breakout | buy | 13233.5 | 12 | 12 | 13221.5 (12) | 50 (13283.5) | 13238.7 | 5.2 | closed by owner | Johnny by hand |
| 79c5dcf | 11-13 09:55 | 11-13 10:32 | range trade | buy | 13235 | 12 | 12 | 13223 (12) | 100 (13335) | 13223.0 | -12.0 | stopped by IG | IG stop |
| d96de5f | 11-13 10:28 | 11-13 13:30 | breakout | sell | 13225.1 | 12 | 12 | 13237.1 (12) | 50 (13175.1) | 13237.1 | -12.0 | closed at IG | IG (stop) |
| d96de5f | 11-13 10:28 | 11-13 13:30 | EMA pullback | sell | 13225.1 | 12 | 12 | 13237.1 (12) | 30 (13195.1) | 13237.1 | -12.0 | closed at IG | IG (stop) |
| d96de5f | 11-13 18:06 | 11-13 18:40 | Bollinger bounce | buy | 13209.5 | 12 | 12 | 13197.5 (12) | 100 (13309.5) | 13213.0 | 3.5 | close | bot |

#### B hourly read

| Code | Opened UTC | Closed UTC | Strategy | Dir | Entry (IG fill) | Rule stop pips | Stop sent | IG stop level (dist) | TP pips (IG limit) | Close (IG) | IG pips | How closed | Who |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 9b61661 | 11-16 06:50 | 11-16 07:15 | level reversal | sell | 13197.5 | 11.2 | 11.5 | 13209 (11.5) | 20 (13177.5) | 13209.0 | -11.5 | stopped by IG | IG stop |
| 9b61661 | 11-16 08:40 | 11-16 09:33 | level reversal | buy | 13210.4 | 14.8 | 16.4 | 13194 (16.4) | 20 (13230.4) | 13194.0 | -16.4 | stopped by IG | IG stop |
| 9b61661 | 11-16 09:50 | 11-16 12:20 | level reversal | sell | 13186.5 | 17.6 | 17.8 | 13204.3 (17.8) | 20 (13166.5) | 13204.3 | -17.8 | stopped by IG | IG stop |
| 9b61661 | 11-16 10:25 | 11-16 10:52 | Bollinger bounce | buy | 13198.3 | 12 | 12 | 13186.3 (12) | 100 (13298.3) | 13186.3 | -12.0 | stopped by IG | IG stop |
| 9b61661 | 11-16 10:50 | 11-16 12:12 | EMA pullback | sell | 13187.1 | 12 | 12 | 13199.1 (12) | 30 (13157.1) | 13199.1 | -12.0 | stopped by IG | IG stop |
| 9b61661 | 11-16 12:37 | 11-16 20:30 | level reversal | sell | 13194.5 | 14.3 | 14.4 | 13208.9 (14.4) | 20 (13174.5) | 13186.2 | 8.3 | forced close | bot (forced) |
| 9b61661 | 11-16 14:26 | 11-17 09:48 | EMA pullback | sell | 13192.1 | 12 | 12 | 13204.1 (12) | 30 (13162.1) | 13204.1 | -12.0 | stopped by IG | IG stop |
| 9b61661 | 11-16 14:57 | 11-16 15:16 | EMA pullback | sell | 13187.3 | 12 | 12 | 13199.3 (12) | 30 (13157.3) | 13199.3 | -12.0 | stopped by IG | IG stop |
| 9b61661 | 11-16 15:47 | 11-16 20:30 | slow grind | sell | 13187.1 | 15 | 15 | 13202.1 (15) | 20 (13167.1) | 13186.5 | 0.6 | forced close | bot (forced) |
| 9b61661 | 11-16 15:50 | 11-16 16:09 | EMA pullback | sell | 13183.2 | 12 | 12 | 13195.2 (12) | 30 (13153.2) | 13195.2 | -12.0 | stopped by IG | IG stop |
| 9b61661 | 11-16 16:53 | 11-16 17:11 | EMA pullback | sell | 13182.5 | 12 | 12 | 13194.5 (12) | 30 (13152.5) | 13194.5 | -12.0 | stopped by IG | IG stop |
| 9b61661 | 11-16 17:27 | 11-16 18:19 | range trade | sell | 13193.7 | 12 | 12 | 13205.7 (12) | 100 (13093.7) | 13182.1 | 11.6 | close | bot |
| 9b61661 | 11-16 20:00 | 11-16 22:04 | EMA pullback | sell | 13184.7 | 12 | 12 | 13196.7 (12) | 30 (13154.7) | 13196.7 | -12.0 | stopped by IG | IG stop |
| aea2275 | 11-17 06:03 | 11-17 06:45 | level reversal | sell | 13198.7 | 9.7 | 9.8 | 13208.5 (9.8) | 20 (13178.7) | 13195.7 | 3.0 | forced close | bot (forced) |
| aea2275 | 11-17 07:35 | 11-17 09:49 | level reversal | sell | 13191.7 | 12.9 | 13.4 | 13205.1 (13.4) | 20 (13171.7) | 13205.1 | -13.4 | stopped by IG | IG stop |
| aea2275 | 11-17 08:59 | 11-17 09:48 | range trade | sell | 13190.4 | 12 | 12 | 13202.4 (12) | 100 (13090.4) | 13202.4 | -12.0 | stopped by IG | IG stop |
| aea2275 | 11-17 10:05 | 11-17 14:06 | Bollinger bounce | sell | 13189.9 | 12 | 12 | 13201.9 (12) | 100 (13089.9) | 13193.2 | -3.3 | stopped by IG | IG stop |
| aea2275 | 11-17 10:05 | 11-17 15:45 | level reversal | sell | 13189.5 | 20.6 | 20.8 | 13210.3 (20.8) | 20 (13169.5) | 13210.3 | -20.8 | stopped by IG | IG stop |
| aea2275 | 11-17 14:00 | 11-17 14:37 | session sweep | buy | 13188.8 | 15.6 | 17.1 | 13171.7 (17.1) | 100 (13288.8) | 13193.9 | 5.1 | stopped by IG | IG stop |
| aea2275 | 11-17 16:22 | 11-17 20:30 | level reversal | buy | 13218.8 | 20.9 | 22.5 | 13196.3 (22.5) | 20 (13238.8) | 13209.6 | -9.2 | forced close | bot (forced) |
| aea2275 | 11-17 16:35 | 11-17 17:16 | Bollinger bounce | sell | 13215.1 | 12 | 12 | 13227.1 (12) | 100 (13115.1) | 13227.1 | -12.0 | stopped by IG | IG stop |
| aea2275 | 11-17 16:46 | 11-17 20:30 | slow grind | buy | 13220 | 15 | 15 | 13205 (15) | 100 (13320) | 13209.6 | -10.4 | forced close | bot (forced) |
| aea2275 | 11-17 17:16 | 11-17 19:59 | EMA pullback | buy | 13225.1 | 12 | 12 | 13213.1 (12) | 100 (13325.1) | 13213.1 | -12.0 | stopped by IG | IG stop |
| aea2275 | 11-17 17:45 | 11-17 20:30 | Bollinger bounce | sell | 13221.1 | 12 | 12 | 13233.1 (12) | 100 (13121.1) | 13210.9 | 10.2 | forced close | bot (forced) |
| cc70dc5 | 11-18 07:30 | 11-18 09:25 | Asian range breakout | sell | 13180.2 | 12 | 12 | 13192.2 (12) | 100 (13080.2) | 13158.5 | 21.7 | stopped by IG | IG stop |
| cc70dc5 | 11-18 09:30 | 11-18 11:03 | Bollinger bounce | buy | 13163.1 | 12 | 12 | 13151.1 (12) | 100 (13263.1) | 13170.3 | 7.2 | stopped by IG | IG stop |
| cc70dc5 | 11-18 12:37 | 11-18 13:07 | EMA pullback | sell | 13156.4 | 12 | 12 | 13168.4 (12) | 100 (13056.4) | 13168.4 | -12.0 | stopped by IG | IG stop |

#### C analyser control

| Code | Opened UTC | Closed UTC | Strategy | Dir | Entry (IG fill) | Rule stop pips | Stop sent | IG stop level (dist) | TP pips (IG limit) | Close (IG) | IG pips | How closed | Who |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3d50353 | 11-18 15:44 | 11-18 22:58 | breakout | sell | 13152.9 | 12 | 12 | 13164.9 (12) | 50 (13102.9) | 13164.9 | -12.0 | stopped by IG | IG stop |
| 3d50353 | 11-18 16:20 | 11-18 16:58 | EMA pullback | sell | 13141.1 | 12 | 12 | 13153.1 (12) | 100 (13041.1) | 13153.1 | -12.0 | stopped by IG | IG stop |
| 3d50353 | 11-18 16:37 | 11-18 16:58 | slow grind | sell | 13138.1 | 15 | 15 | 13153.1 (15) | 100 (13038.1) | 13153.1 | -15.0 | stopped by IG | IG stop |
| 3d50353 | 11-18 19:50 | 11-18 20:19 | level reversal | sell | 13135.8 | 11.2 | 11.3 | 13147.1 (11.3) | 20 (13115.8) | 13147.1 | -11.3 | stopped by IG | IG stop |
| 3d50353 | 11-19 07:35 | 11-19 09:27 | Asian range breakout | buy | 13156.5 | 12 | 12 | 13144.5 (12) | 100 (13256.5) | 13144.5 | -12.0 | stopped by IG | IG stop |

#### D stage 4

| Code | Opened UTC | Closed UTC | Strategy | Dir | Entry (IG fill) | Rule stop pips | Stop sent | IG stop level (dist) | TP pips (IG limit) | Close (IG) | IG pips | How closed | Who |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d9e5d0e | 11-19 11:00 | 11-19 11:57 | slow grind | buy | 13170 | 15 | 15 | 13155 (15) | 20 (13190) | 13155.0 | -15.0 | stopped by IG | IG stop |
| d9e5d0e | 11-19 12:10 | 11-19 15:50 | session sweep | sell | 13150.9 | 22.0 | 22.0 | 13172.9 (22) | 100 (13050.9) | 13122.0 | 28.9 | stopped by IG | IG stop |
| d9e5d0e | 11-19 15:40 | 11-19 16:29 | Bollinger bounce | buy | 13118.8 | 12 | 12 | 13106.8 (12) | 100 (13218.8) | 13106.8 | -12.0 | stopped by IG | IG stop |
| d9e5d0e | 11-19 17:20 | 11-19 17:52 | Bollinger bounce | buy | 13107.4 | 12 | 12 | 13095.4 (12) | 100 (13207.4) | 13107.8 | 0.4 | closed by owner | Johnny by hand |

Notes on the IG match: IG's transaction list misses the 12 Nov 19:02 and 22:00 EMA pullbacks, so their close is
IG's activity close level. Two trades differ between the bot's record and IG, and IG is used for both: 11 Nov 06:55
Bollinger bounce (bot +0.1, IG −3.3) and 18 Nov 12:37 EMA pullback (bot −12.6, IG −12.0).

## Step 2. Per strategy, per version period

IG pips (IG's open and close levels); a trade is a win above 0. Johnny's hand closes are kept apart and are not the bot's result.

### Bot's own exits (IG stop, IG limit, the bot's closes)

| Period | Strategy | Trades | Wins | Losses | Flat | Total pips | Avg win | Avg loss |
|---|---|---|---|---|---|---|---|---|
| A first build | Bollinger bounce | 10 | 4 | 6 | 0 | -12.5 | +6.7 | -6.5 |
| A first build | EMA pullback | 13 | 3 | 10 | 0 | -30.0 | +30.0 | -12.0 |
| A first build | breakout | 7 | 2 | 5 | 0 | +29.1 | +35.5 | -8.4 |
| A first build | level reversal | 3 | 3 | 0 | 0 | +60.0 | +20.0 | +0.0 |
| A first build | range trade | 5 | 0 | 5 | 0 | -39.1 | +0.0 | -7.8 |
| A first build | slow grind | 10 | 3 | 7 | 0 | -37.6 | +15.8 | -12.1 |
| B hourly read | Asian range breakout | 1 | 1 | 0 | 0 | +21.7 | +21.7 | +0.0 |
| B hourly read | Bollinger bounce | 5 | 2 | 3 | 0 | -9.9 | +8.7 | -9.1 |
| B hourly read | EMA pullback | 8 | 0 | 8 | 0 | -96.0 | +0.0 | -12.0 |
| B hourly read | level reversal | 8 | 2 | 6 | 0 | -77.8 | +5.7 | -14.8 |
| B hourly read | range trade | 2 | 1 | 1 | 0 | -0.4 | +11.6 | -12.0 |
| B hourly read | session sweep | 1 | 1 | 0 | 0 | +5.1 | +5.1 | +0.0 |
| B hourly read | slow grind | 2 | 1 | 1 | 0 | -9.8 | +0.6 | -10.4 |
| C analyser control | Asian range breakout | 1 | 0 | 1 | 0 | -12.0 | +0.0 | -12.0 |
| C analyser control | EMA pullback | 1 | 0 | 1 | 0 | -12.0 | +0.0 | -12.0 |
| C analyser control | breakout | 1 | 0 | 1 | 0 | -12.0 | +0.0 | -12.0 |
| C analyser control | level reversal | 1 | 0 | 1 | 0 | -11.3 | +0.0 | -11.3 |
| C analyser control | slow grind | 1 | 0 | 1 | 0 | -15.0 | +0.0 | -15.0 |
| D stage 4 | Bollinger bounce | 1 | 0 | 1 | 0 | -12.0 | +0.0 | -12.0 |
| D stage 4 | session sweep | 1 | 1 | 0 | 0 | +28.9 | +28.9 | +0.0 |
| D stage 4 | slow grind | 1 | 0 | 1 | 0 | -15.0 | +0.0 | -15.0 |
| E first-build-plus | Asian range breakout | 1 | 0 | 1 | 0 | -12.0 | +0.0 | -12.0 |
| E first-build-plus | Bollinger bounce | 1 | 1 | 0 | 0 | +2.9 | +2.9 | +0.0 |
| E first-build-plus | Bollinger bounce 5m | 3 | 0 | 2 | 1 | -13.7 | +0.0 | -6.8 |
| E first-build-plus | level reversal | 1 | 0 | 1 | 0 | -17.3 | +0.0 | -17.3 |
| E first-build-plus | session sweep | 2 | 2 | 0 | 0 | +8.4 | +4.2 | +0.0 |
| E first-build-plus | slow grind | 1 | 0 | 1 | 0 | -15.0 | +0.0 | -15.0 |
| **A first build** | **all** | **48** | **15** | **33** | **0** | **-30.1** | **+19.7** | **-9.9** |
| **B hourly read** | **all** | **27** | **8** | **19** | **0** | **-167.1** | **+8.5** | **-12.4** |
| **C analyser control** | **all** | **5** | **0** | **5** | **0** | **-62.3** | **+0.0** | **-12.5** |
| **D stage 4** | **all** | **3** | **1** | **2** | **0** | **+1.9** | **+28.9** | **-13.5** |
| **E first-build-plus** | **all** | **9** | **3** | **5** | **1** | **-46.7** | **+3.8** | **-11.6** |

### Johnny's hand closes (not the bot's result)

| Period | Strategy | Trades | Wins | Losses | Flat | Total pips | Avg win | Avg loss |
|---|---|---|---|---|---|---|---|---|
| A first build | Bollinger bounce | 1 | 1 | 0 | 0 | +0.6 | +0.6 | +0.0 |
| A first build | breakout | 2 | 2 | 0 | 0 | +16.9 | +8.4 | +0.0 |
| A first build | level reversal | 2 | 0 | 2 | 0 | -25.8 | +0.0 | -12.9 |
| A first build | slow grind | 2 | 1 | 1 | 0 | +25.1 | +37.8 | -12.7 |
| D stage 4 | Bollinger bounce | 1 | 1 | 0 | 0 | +0.4 | +0.4 | +0.0 |
| E first-build-plus | EMA pullback | 2 | 0 | 2 | 0 | -9.3 | +0.0 | -4.7 |
| E first-build-plus | level reversal | 3 | 1 | 2 | 0 | -26.7 | +2.9 | -14.8 |
| **A first build** | **all** | **7** | **4** | **3** | **0** | **+16.8** | **+13.8** | **-12.8** |
| **D stage 4** | **all** | **1** | **1** | **0** | **0** | **+0.4** | **+0.4** | **+0.0** |
| **E first-build-plus** | **all** | **5** | **1** | **4** | **0** | **-36.0** | **+2.9** | **-9.7** |

### Whole period, bot exits, by strategy

| Strategy | Trades | Wins | Losses | Total pips | £ at £10/pip |
|---|---|---|---|---|---|
| EMA pullback | 22 | 3 | 19 | -138.0 | -1380 |
| slow grind | 15 | 4 | 11 | -92.4 | -924 |
| level reversal | 13 | 5 | 8 | -46.4 | -464 |
| range trade | 7 | 1 | 6 | -39.5 | -395 |
| Bollinger bounce | 17 | 7 | 10 | -31.5 | -315 |
| Bollinger bounce 5m | 3 | 0 | 2 | -13.7 | -137 |
| Asian range breakout | 3 | 1 | 2 | -2.3 | -23 |
| breakout | 8 | 2 | 6 | +17.1 | +171 |
| session sweep | 4 | 4 | 0 | +42.4 | +424 |

## Step 3. Mechanics of every losing trade since 19 Nov 18:44

The live code is 02f6c7e: the price service process started at `Thu Nov 19 18:43:54 2026` (`ps -o lstart`) and
has not restarted. The tree was later checked out at 26c06fc (19 Nov 20:20) and bb085f4 (20 Nov 12:11), but
neither was loaded by the running service (memory note `stp-structural-history-deploy`: "autobot-prices NOT
restarted"). Every code reading below is from an exact copy of 02f6c7e (`git archive 02f6c7e`).

### 3.1 The losing (and flat) trades, checked one by one

"Quote at send" is the bot's own `reached on the live price at … (bid, offer)` line in the trade record. "Stop
candle" is the stored 5-minute candle in which IG closed the trade.

| # | Opened | Strategy, dir | Entry rule | Rule price → IG fill | Stop: rule / sent / IG | Stop side | Spread at entry / at stop | Exit | Management |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 19 Nov 19:33:16 | level reversal buy | live break above confirmation high 13102.7 | quote offer 13104.4 (bid 13102.9) → 13104.4 | 13091.8 / 12.6 / 13091.8 (12.6) | below ✔ | 1.5 / – | Johnny 20:16:50 at 13100.9 (−3.5) | none due |
| 2 | 19 Nov 19:51:09 | EMA pullback sell | live, 3 pips below the 5-candle low, 13094.8 | bid 13094.8 → 13094.5 | 12 / 12 / 13106.5 (12) | above ✔ | 1.5 / – | Johnny 20:16:54 at 13102.4 (−7.9) | none due |
| 3 | 20 Nov 06:07:42 | level reversal buy | live break above 13109.6 | offer 13111.5 → 13111.4 | 13094.2 / 17.3 / 13094.1 (17.3) | below ✔ | 1.5 / 1.5 | IG stop 11:59:15 at 13094.1 (−17.3); candle 11:55 sell low 13093.0 | best +10.5; no break-even in this build (rule, not fault) |
| 4 | 07:15:01 | Asian range breakout buy | next candle's open after the 07:10 close above the Asian high 13117.8 | 07:15 open 13120.8 (bid) → offer fill 13122.3 | 12 / 12 / 13110.3 (12) | below ✔ | 1.5 / 0.9–1.5 | IG stop 08:00:46 at 13110.3 (−12.0); candle 08:00 sell low 13105.8 | best −0.9; trail (from +12) never reached |
| 5 | 07:25:06 | Bollinger bounce 5m sell | live break below 13114.8 | bid 13114.7 → 13114.8 | 12 / 12 / 13126.8 (12) | above ✔ | 1.5 / – | bot closed 07:45:02 at 13116.5 (−1.7): "a confirmed rejection at a level: london_session_low 13111.2, pivot 13111.6" | the 5m bounce's level-close rule, as written |
| 6 | 13:10:24 | level reversal buy | live break above confirmation high 13126.2 (confirmation 13:00, trigger on the 13:10 candle) | offer 13127.9 → 13127.7 | 13093.6 / 34.3 / 13093.4 (34.3) | below ✔ | 1.5 / – | Johnny 16:11:44 at 13101.6 (−26.1, −£261) | best +0.9; stop never reached |
| 7 | 13:25:12 | slow grind buy | live break above the pause high 13126.9 | offer 13128.5 → 13128.3 | 15 / 15 / 13113.3 (15) | below ✔ | 1.5 / 1.5 | IG stop 13:41:36 at 13113.3 (−15.0); candle 13:40 sell low 13111.9 | best −1.1 |
| 8 | 13:32:09 | Bollinger bounce 5m sell | live break below 13118.9 | bid 13118.6 → 13118.1 | 12 / 12 / 13130.1 (12) | above ✔ | 1.5 / – | bot closed 14:35:02 at 13118.1 (0.0): "a confirmed rejection at a level: pivot 13111.6" | best +11.0; the 5m bounce has no trail in this build |
| 9 | 14:45:07 | Bollinger bounce 5m sell | live break below 13107.4 | bid 13107.1 → 13107.1 | 12 / 12 / 13119.1 (12) | above ✔ | 1.5 / 1.5 | IG stop 15:44:03 at 13119.1 (−12.0); candle 15:40 buy high 13120.3 | best +3.1; the level watch "hold … the analyser's rejection setup is over" (15:20) |
| 10 | 18:42:26 | EMA pullback sell | live, 13092.3 | bid 13092.3 → 13091.4 | 12 / 12 / 13103.4 (12) | above ✔ | 1.5 / – | Johnny 18:43:24 at 13092.8 (−1.4) | none due |

Raw evidence for row 6 (the −£261 trade):
- Journal line 935: `"event": "sending", "strategy": "level reversal", "direction": "buy", "stop_pips": "32.6", "stop_distance": "34.3", "take_profit_pips": 20, "idea_price": "13126.2"`
- IG activity 13:10:24: `"Position opened: WDUG25BW", "level": 13127.7, "stopLevel": 13093.4, "stopDistance": 34.3, "limitLevel": 13147.7`
- IG transaction: `"openDateUtc": "2026-11-20T13:10:24", "dateUtc": "2026-11-20T16:11:44", "openLevel": "13127.7", "closeLevel": "13101.6", "profitAndLoss": "£-261.00"`
- The record's steps: `pierce 13099.6 … reached round_number 13100` (12:40), `reversal candle … C 13112` (12:55), `confirmation 13125.2 … trigger at above 13126.2` (13:00), `price went above 13126.2` (13:10), `furthest low 13099.6 … 0.4 pips past the level (allowance 5)`, `stop 13093.6: 6 pips below the furthest point; take profit 20 pips`.

### 3.2 Findings for each check

- **Stop sent, accepted, right distance, right side:** yes for all 15 trades since 18:44 (and all 106 since 9 Nov).
  IG's `stopDistance` equals the bot's `stop_distance` on every trade. No trade was ever open without a stop.
- **Opened at the price and time the rule says:** yes. The next-candle strategies (Asian range breakout, hourly
  bounce, session sweep) opened 0–6 seconds into the candle, at its open. The live-break strategies opened while
  the price was at the trigger (each quote at send is within 0.4 pips of the trigger, on the right side). Fills
  differed from the quote by 0.0–0.9 pips (worst: 18:42 EMA sell, bid 13092.3, filled 13091.4).
- **Direction right for the rule:** yes. In 02f6c7e the direction rule applies only to the EMA pullback
  (`NO_DIRECTION_RULE` in `strategies/common.py`). Both EMA sells were on the sell side ("price … below the pivot
  … and below the 5m 100 EMA"). The 5m bounce is allowed only *against* a trend (`BOLLINGER_BOUNCE_5M: {TREND:
  "against", POSSIBLE_REVERSAL: "any"}`), so its sells in "trend up, slow grind" are by design. The hourly bounce
  and the session strategies aren't checked against the state at all (`WITHOUT_HINDRANCE`).
- **Buy vs sell price basis:** the strategies work on the sell (bid) chart. Buys fill at the offer and sells at the
  bid, as they should. IG triggers a buy's stop on the bid and a sell's stop on the offer. Two small effects:
  (a) **for the level reversal and the session sweep, the stop is a bid-chart price.** For a sell, IG triggers it
  when the *offer* reaches it, so a sell's real cushion beyond the furthest high is 6 − spread (≈4.5 pips), while
  a buy gets the full 6. (b) The bot sends a *distance* worked out from the quote at the moment of sending. IG
  applies it to the *fill*, so the stop moves by the slippage: 06:07 rule 13094.2 → IG 13094.1; 13:10 13093.6 →
  13093.4; the open 18:45 sell 13104.0 → 13103.3 (0.7 pips tighter). Small, but not what the rule says.
- **Spread:** 1.5 pips at every entry and at every stop candle (0.9–1.0 at moments). Nothing abnormal, and no stop
  filled worse than its level.
- **Duplicate, late or stale entries:** none. No strategy had two trades open at once in this version. The only
  same-strategy overlaps since 9 Nov are the EMA pullback's (10–11 Nov and 16 Nov), which has no open-trade limit
  by design (safety rule 5: "the EMA pullback no limit"). **One design gap:** a bounce setup's trigger never
  expires after its confirmation candle (`rejection/watch.py`: "4. trigger: the live price goes below the
  confirmation candle's low"; only a cancel past the reversal candle ends it). The 13:10 buy triggered two candles
  after its 13:00 confirmation, after the 13:05 high of 13126.0 missed the trigger by 0.2 pips.
- **Opposite trades open together:** 12 pairs in this version (e.g. 13:10 LR buy and 13:25 slow grind buy open
  while 13:30 bounce sell, 13:32 bounce 5m sell and 13:35 session sweep sell opened). They came from one move:
  the 13:00–13:10 push to 13128.6 was the level reversal's *confirmation* (buy) and the hourly bounce's *rejection
  candle* (sell) at the same time.
- **Trade management:** did what the live rules say. The session sweep at 07:30 trailed from +12 to a stop at
  13106.0 and banked +7.5. The hourly bounce at 13:30 trailed to 13117.2 (+2.9), with IG's minimum distance
  respected ("sent as 13117.6, the nearest level IG allows"). The 5m bounce's level closes fired on confirmed
  rejections. The level reversal has no break-even in this build. TRAIL_NO_LOSS was a Stage 4 switch, and the
  rollback dropped it, so trade 3 went from +10.5 to −17.3. That follows the rules.

### 3.3 Extra check 1: the level reversal's stop

**The exact rule (02f6c7e, `strategies/level_reversal/strategy.py` lines 90–101):**

```python
furthest = max(self._h(c) for c in span) if sell else min(self._l(c) for c in span)
...
beyond = Decimal(self.lr.stop_beyond_furthest_pips) * self.ppp
stop = furthest + beyond if sell else furthest - beyond
```

`span` is every candle from the piercing candle to the confirmation candle. `stop_beyond_furthest_pips = 6`
(`config/settings.toml` `[level_reversal]`). The sender turns that price into a distance from the current price
(`orders/sender.py` `_stop_distance`: `dist = (offer - Decimal(sp))` for a buy). Take profit is a fixed
`take_profit_pips = 20`.

- **17.3 pips (06:07):** furthest low 13100.2 (05:45 candle) − 6 = 13094.2. The entry trigger was 13109.6 and the
  offer 13111.5, so the distance was 13111.5 − 13094.2 = 17.3.
- **34.3 pips (13:10):** furthest low 13099.6 (12:40) − 6 = 13093.6. The trigger was 13126.2 (the confirmation
  candle ran from 13111 to 13125.2) and the offer 13127.9, so the distance was 13127.9 − 13093.6 = 34.3.
- **In the first build (f99efe1)?** Yes, line for line. `git show f99efe1:strategies/level_reversal/strategy.py`
  has the same lines 100–101, `stop_beyond_furthest_pips = 6` and `take_profit_pips = 20`. Its sender has the same
  `_stop_distance`.
- **Does anything cap it?** **No, not in the live code.** No maximum stop, no maximum distance from the level, no
  stop-versus-target check. Safety rule 7 (total risk) is £100,000, "set so it is never reached". The only caps
  ever built were in d9e5d0e (Stage 4, live 19 Nov 09:49–18:43): `LEVEL_STOPS` ("refused if wider than
  widest_stop_pips (20)") and `LR_ENTRY_NEAR_LEVEL` (`entry_within_pips_of_level 6`). Neither file exists in
  02f6c7e. `.env` still has `LEVEL_STOPS=on` and `LR_ENTRY_NEAR_LEVEL=on`, but the live `config/switches.py` reads
  neither. Six other lines in `.env` are also ignored by the live code: `HOURLY_READ`, `TREND_STILL_GOING`,
  `ANALYSER_USES_HOURLY`, `ANALYSER_GOVERNS_ALL`, `SCALE_OUT_REVERSAL`, `TRAIL_NO_LOSS`.

**Stop vs take profit, every level reversal trade since 9 Nov (IG's figures):**

| Opened | Code | Dir | Rule stop pips | IG stop pips | TP pips | Stop ≥ TP? | IG pips | Closed by |
|---|---|---|---|---|---|---|---|---|
| 11-09 06:12 | f99efe1 | buy | 11.1 | 12.9 | 20 | no | 20.0 | take profit hit at IG |
| 11-09 08:25 | f99efe1 | buy | 23.6 | 25.3 | 20 | **yes** | -11.2 | closed by owner |
| 11-10 14:06 | 2ff445f | sell | 18.4 | 18.5 | 20 | no | 20.0 | take profit hit at IG |
| 11-10 16:26 | 2ff445f | sell | 20.0 | 20.2 | 20 | **yes** | -14.6 | closed by owner |
| 11-11 13:40 | 02a8dfe | sell | 13.0 | 13.1 | 20 | no | 20.0 | take profit hit at IG |
| 11-16 06:50 | 9b61661 | sell | 11.2 | 11.5 | 20 | no | -11.5 | stopped by IG |
| 11-16 08:40 | 9b61661 | buy | 14.8 | 16.4 | 20 | no | -16.4 | stopped by IG |
| 11-16 09:50 | 9b61661 | sell | 17.6 | 17.8 | 20 | no | -17.8 | stopped by IG |
| 11-16 12:37 | 9b61661 | sell | 14.3 | 14.4 | 20 | no | 8.3 | forced close |
| 11-17 06:03 | aea2275 | sell | 9.7 | 9.8 | 20 | no | 3.0 | forced close |
| 11-17 07:35 | aea2275 | sell | 12.9 | 13.4 | 20 | no | -13.4 | stopped by IG |
| 11-17 10:05 | aea2275 | sell | 20.6 | 20.8 | 20 | **yes** | -20.8 | stopped by IG |
| 11-17 16:22 | aea2275 | buy | 20.9 | 22.5 | 20 | **yes** | -9.2 | forced close |
| 11-18 19:50 | 3d50353 | sell | 11.2 | 11.3 | 20 | no | -11.3 | stopped by IG |
| 11-19 19:33 | 02f6c7e | buy | 10.9 | 12.6 | 20 | no | -3.5 | closed by owner |
| 11-20 06:07 | 02f6c7e | buy | 15.4 | 17.3 | 20 | no | -17.3 | stopped by IG |
| 11-20 13:10 | 02f6c7e | buy | 32.6 | 34.3 | 20 | **yes** | -26.1 | closed by owner |
| 11-20 17:55 | 02f6c7e | sell | 12.9 | 13.0 | 20 | no | 2.9 | closed by owner |
| 11-20 18:45 | 02f6c7e | sell | 14.3 | 14.4 | 20 | no | open | still open |

Five of the 19 had a stop of 20 pips or more, against the 20-pip target. By the rule's own arithmetic it needs to win
more than half its trades to break even at 1:1, and more than 63% at 34:20.

### 3.4 Extra check 2: the stop each strategy is meant to use, against what it sent

Where the live code decides the stop: `strategies/common.py` `stop_loss_pips()` and `stop_price()`, with the
values from `config/settings.toml` and `.env` (`STOP_LOSS_PIPS=12`, `STOP_LOSS_PIPS_EMA_PULLBACK=12`).

| Strategy | Setting the live code uses | Meant stop | Sent since 19 Nov 18:44 (rule → IG) | Sent 9–19 Nov |
|---|---|---|---|---|
| EMA pullback | `.env STOP_LOSS_PIPS_EMA_PULLBACK` | 12 | 12 → 12 (×3) | 12 → 12 (×22) |
| slow grind | `[slow_grind] stop_loss_pips` | 15 | 15 → 15 | 15 → 15 (×16) |
| Bollinger bounce (hourly) | `.env STOP_LOSS_PIPS` | 12 | 12 → 12 | 6 → 6 (×7, 9–10 Nov when STOP_LOSS_PIPS was 6), 12 → 12 (×11) |
| Bollinger bounce 5m | `.env STOP_LOSS_PIPS` | 12 | 12 → 12 (×3) | – |
| range trade | `.env STOP_LOSS_PIPS` | 12 | – (no trade) | 6 → 6 (×3, 9–10 Nov), 12 → 12 (×4) |
| **breakout** | **`[breakout] stop_loss_pips`** | **6 in the live code** (Johnny set 12 on 10 Nov) | – (no trade) | 6 → 6 (×4, 9–10 Nov), 12 → 12 (×6, from 10 Nov 15:36 to 18 Nov) |
| Asian range breakout | `[asian_range_breakout] stop_loss_pips` | 12 | 12 → 12 | 12 → 12 (×2) |
| New York open reversal | `[new_york_open_reversal] stop_loss_pips` | 12 | – (never traded) | – |
| session sweep | `stop_price()`: 1 beyond the sweep's furthest point, at least `min_stop_pips` 12 | ≥ 12 | 12 → 12 (×2) | 15.6 → 17.1, 22.0 → 22 |
| level reversal | `stop_price()`: 6 beyond the furthest point, **no cap** | varies | 10.9–32.6 → 12.6–34.3 | 9.7–23.6 → 9.8–25.3 |

**The breakout:** the earlier report's "`[breakout] stop_loss_pips = 6`" is what the live code reads (02f6c7e
`config/settings.toml`: `stop_loss_pips = 6`, `take_profit_pips = 50`; `stop_loss_pips()` returns
`settings.breakout.stop_loss_pips`). Johnny's commit 0e1492b (10 Nov 15:36, "Stop 12 pips for the Bollinger
bounce, range trade and breakout") changed it to 12, and every breakout from then to 18 Nov sent 12. First-build-plus
(f35bd1b → 02f6c7e) is built on f99efe1, which predates 0e1492b, so the value went back to 6.
`research/rollback_20261119/REPORT.md` line 125 ("The 9 Nov code would use 12 for the bounce, range trade and
breakout") and `research/first_build_plus_20261119/REPORT.md` line 123 ("both bounces, the range trade and the
breakout take their stop from STOP_LOSS_PIPS") are **wrong about the breakout**. **The 12-pip, −£120 loss today
was the 07:15 Asian range breakout** (journal: `"strategy": "Asian range breakout", "stop_pips": "12"`; IG:
`"openLevel": "13122.3", "closeLevel": "13110.3", "profitAndLoss": "£-120.00"`). Its own setting is 12, as
specified. The other −£120 today was the 14:45 Bollinger bounce 5m (`STOP_LOSS_PIPS` 12).

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

## Step 5. Conclusions

### 5.1 What is mechanically broken, most serious first

1. **The level reversal has no cap on its stop, and its take profit is fixed at 20.** This isn't a code fault
   against its spec: the rule is the first build's, line for line. But it lets one trade risk 34.3 pips to make 20,
   which is what produced today's −£261. The approved fixes (20-pip widest stop, entry within 6 pips of the level)
   were lost in the rollback.
2. **The live `.env` claims protections the live code doesn't have.** `LEVEL_STOPS=on`, `LR_ENTRY_NEAR_LEVEL=on`,
   `TRAIL_NO_LOSS=on`, `SCALE_OUT_REVERSAL=on`, `ANALYSER_USES_HOURLY=on`, `ANALYSER_GOVERNS_ALL=on`,
   `HOURLY_READ`, `TREND_STILL_GOING`: none of these is read by 02f6c7e. Anyone reading `.env` will believe the
   bot has caps and break-even exits it doesn't have.
3. **The breakout's stop silently went back from 12 to 6** in the rollback, against Johnny's 10 Nov instruction,
   and two reports said otherwise. No live breakout has traded since, so no money has been lost to it yet.
4. **A bounce setup's trigger never expires after confirmation.** The level reversal (and the 5m bounce, which
   uses the same watcher) can enter several candles late, far from the level. This is a gap in the written rule
   rather than a coding error, and it is how the 13:10 entry ended up 26.6 pips above the level.
5. **Small price-basis effects on stop prices** (level reversal, session sweep): a sell's stop cushion is about
   1.5 pips smaller than a buy's, and the stop shifts by the entry slippage (up to 0.7 pips seen) because a
   distance is sent rather than the level. Small, but not exactly the rule.

6. **Fixed, older:** on 17 Nov (version B) IG refused the hourly bounce's trail move 31 times
   (`ATTACHED_ORDER_LEVEL_ERROR`, 13:50–14:06), and a +15.6 trade ended at −3.3. The trail fix cc70dc5 (17 Nov
   20:36) sends the nearest level IG allows. No refusal has happened since (the journal has all 31 on 17 Nov).

**Not broken** (checked with IG's records): stops always sent, accepted and correctly placed; stops triggered only
when the price really reached them, with no slippage; normal spreads; entries on time and at the right price;
correct direction for each rule; no duplicate or stale entries; trails and level closes worked as specified.

### 5.2 Which strategies are losing, how much, and why

Bot's own exits only, IG pips, 9–20 Nov (Johnny's hand closes apart; £ at £10 a pip):

| Strategy | Bot trades | Wins | Losses | Total IG pips | £ | Johnny's closes (pips) |
|---|---|---|---|---|---|---|
| EMA pullback | 22 | 3 | 19 | -138.0 | -1380 | -9.3 (2) |
| slow grind | 15 | 4 | 11 | -92.4 | -924 | +25.1 (2) |
| level reversal | 13 | 5 | 8 | -46.4 | -464 | -52.5 (5) |
| range trade | 7 | 1 | 6 | -39.5 | -395 | – |
| Bollinger bounce | 17 | 7 | 10 | -31.5 | -315 | +1.0 (2) |
| Bollinger bounce 5m | 3 | 0 | 2 | -13.7 | -137 | – |
| Asian range breakout | 3 | 1 | 2 | -2.3 | -23 | – |
| breakout | 8 | 2 | 6 | +17.1 | +171 | +16.9 (2) |
| session sweep | 4 | 4 | 0 | +42.4 | +424 | – |
| **all** | **92** | **27** | **64** | **-304.3** | **-3043** | **-18.8 (13)** |

| Strategy | Real reason (from the evidence) |
|---|---|
| **EMA pullback** (−138.0, 3 wins in 22; 0 in 8 in the 15–18 Nov version) | The rules losing in this market. Every loss was a full 12-pip stop against a 30-pip target, which needs 29% wins to break even; it got 14%. Today's 18:42 sell passed step 0 with slopes 1.01/0.60/0.57 pips an hour and a 0.38-pip gap (minimums 0.16 and 0.25): a trend barely there. No mechanical fault found in any of its trades (all 22 stops exactly 12, all stopped at the stop). |
| **slow grind** (−92.4, 4 in 15) | The rules losing in this market. A 15-pip stop against a 20-pip target. Today's 13:25 buy broke a 2-candle pause at 13126.9, 1.7 pips under the day's high 13128.6, at the same moment the hourly bounce was reading that high as a rejection. It never went into profit (best −1.1). |
| **level reversal** (−46.4 bot, and −52.5 on Johnny's closes) | Mostly the rule's risk shape: no cap on the stop, fixed 20-pip target, a trigger with no expiry, and no break-even. Today's 06:07 buy was +10.5 at best and then lost 17.3; the 13:10 buy risked 34.3 for 20. |
| **range trade** (−39.5, 1 in 7) | The rules losing. No trades in the current version. |
| **Bollinger bounce (hourly)** (−31.5, 7 in 17) | The rules losing slightly. Its wins are small trailed gains (+2.9 today); its losses are full 12s. |
| **Bollinger bounce 5m** (−13.7, 0 in 3, current version only) | Too few trades to judge. Two of three were closed near flat by the level-close rule; one was a full 12. All three were sells against "trend up, slow grind", which the rule allows ("against" the trend). |
| **Asian range breakout** (−2.3, 1 in 3) | Too few to judge. Today's 07:15 buy never went into profit (best −0.9) and was stopped at 12. |
| breakout (+17.1, 2 in 8) | Positive, small sample. Stop now 6, not 12 (see 5.1). |
| session sweep (+42.4, 4 in 4) | Positive, small sample. |

Two things cut across strategies:
- **Opposite trades at once.** The strategies read the same candles in opposite ways and nothing stops them
  opening against each other. In this version 12 such pairs were open together. When that happens, at least one
  side must lose, and both pay the spread.
- **The market has narrowed.** The 07:00–20:30 UK range (stored candles, sell price) was 47 pips on 16 Nov, 55,
  57, 80 on 19 Nov, and 41 today, mostly between 13090 and 13128. Several strategies have fixed 12–15 pip stops
  against 20–30 pip (or 100-pip) targets, which suits moves, not chop.

### 5.3 Suggestions (nothing built or changed)

- **Level reversal:**
  - Bring back a stop cap: either the 18 Nov `LEVEL_STOPS` widest 20, or simply refuse when the stop is wider than
    the take profit.
  - Bring back `LR_ENTRY_NEAR_LEVEL` (entry within 6 pips of the level).
  - Make the trigger expire one or two candles after the confirmation.
  - Consider a break-even once +10, as `TRAIL_NO_LOSS` did.
  - Or set the take profit from the stop (for example 1:1 or better).
- **`.env`:** remove or comment out the eight switches the live code ignores, so `.env` describes the live bot.
- **Breakout:** decide 6 or 12, and set `[breakout] stop_loss_pips` to match. Correct the two earlier reports.
- **Cross-strategy conflicts:** for example, no new trade against the direction of a trade another strategy has
  open, or extend rule 11 (one signal, one trade) to the level reversal and the bounce 5m. Today's 13:05–13:10
  candles alone opened five trades both ways.
- **EMA pullback:**
  - Raise step 0's minimum slope and gap, so it needs a real hourly trend (today's 18:42 trade had slopes just above
    the minimum).
  - Or test it only on days the analyser calls a trend from the morning.
  - Its 30-pip target on a 12-pip stop needs a trend that runs.
- **Slow grind:**
  - Avoid buying a pause break within a few pips of the day's high when a reversal setup (bounce, level reversal)
    is live on the same candle.
  - Or require the pause to come back toward the 21 EMA.
- **Bounces and the Asian range breakout:** keep observing; three trades each is not enough to judge.
- **Stop price basis (small):** send the level reversal's and session sweep's stop as a level (`stopLevel`), or
  add the spread on sells, so the stop sits exactly where the rule puts it.
- As always, the live demo is the judge. These are ideas for Johnny to choose from, not tested changes.

## Week review, Mon 16 – Fri 20 Nov (Johnny's added request: Claude Code's own review)

Every trade the bot opened from Mon 16 Nov 00:00 to Fri 20 Nov 19:00 UTC: 51 trades. 44 were closed by the bot
or by IG, 6 by Johnny, and 1 is still open. Pips are IG's. "What price did" is measured on the stored 5-minute
candles: a buy on the sell price, a sell on the buy price, from the fill to the close (`week_paths.py`,
`week_paths.csv`). "Best" is the bot's own recorded best (`best_pips` in the trade record). The entry candle is
counted from its start, so the first-15-minute figures may include a little price action from before the fill.
Code versions: B = 15–18 Nov 13:35, C = 18 Nov 13:36–19 Nov 09:49, D = 19 Nov 09:49–18:43, E = since 19 Nov 18:44
(the current first-build-plus).

### W1. Every trade, one line each

| Opened (UTC) | Version | Strategy | Dir | Stop / target | IG pips | Who closed | What price did after the entry, and what was at fault |
|---|---|---|---|---|---|---|---|
| 11-16 06:50 | B | level reversal | sell | 11.5 / 20 | -11.5 | IG stop | Went against it at once (first 15 min +0.6/−6.6), never 3 pips its way (best +0.6), full stop after 25 min: the entry/signal was wrong; stop and management did their job. |
| 11-16 08:40 | B | level reversal | buy | 16.4 / 20 | -16.4 | IG stop | Was +14.1 in profit, then all the way back to the full stop after 53 min: management (nothing locked the gain). |
| 11-16 09:50 | B | level reversal | sell | 17.8 / 20 | -17.8 | IG stop | Went against it at once (first 15 min +0.0/−3.9), never 3 pips its way (best +2.9), full stop after 150 min: the entry/signal was wrong; stop and management did their job. |
| 11-16 10:25 | B | Bollinger bounce | buy | 12 / 100 | -12.0 | IG stop | Went against it at once (first 15 min +1.5/−2.9), never 3 pips its way (best +1.5), full stop after 27 min: the entry/signal was wrong; stop and management did their job. |
| 11-16 10:50 | B | EMA pullback | sell | 12 / 30 | -12.0 | IG stop | Only +3.5 its way (first 15 min +1.9/−4.3), then back to the full stop after 82 min: a weak signal; the move was too small for its 12-pip stop. |
| 11-16 12:37 | B | level reversal | sell | 14.4 / 20 | 8.3 | bot (20:30) | Held all afternoon and closed at 20:30 at +8.3 (best +15.6, never reached the 20-pip target). |
| 11-16 14:26 | B | EMA pullback | sell | 12 / 30 | -12.0 | IG stop | The EMA pullback is held overnight; it was +22.6 in the night and came all the way back to the stop next day: management (no lock or trail for the EMA pullback). |
| 11-16 14:57 | B | EMA pullback | sell | 12 / 30 | -12.0 | IG stop | Went against it at once (first 15 min +1.2/−5.5), never 3 pips its way (best +1.2), full stop after 19 min: the entry/signal was wrong; stop and management did their job. |
| 11-16 15:47 | B | slow grind | sell | 15 / 20 | 0.6 | bot (20:30) | Worked: first 15 min +6.8/−5.7, best +8.2; the 20:30 close took it at +0.6. |
| 11-16 15:50 | B | EMA pullback | sell | 12 / 30 | -12.0 | IG stop | Went against it at once (first 15 min +2.9/−7.5), never 3 pips its way (best +2.9), full stop after 19 min: the entry/signal was wrong; stop and management did their job. |
| 11-16 16:53 | B | EMA pullback | sell | 12 / 30 | -12.0 | IG stop | Went against it at once (first 15 min +0.0/−8.3), never 3 pips its way (best -1.0), full stop after 17 min: the entry/signal was wrong; stop and management did their job. |
| 11-16 17:27 | B | range trade | sell | 12 / 100 | 11.6 | bot | Worked: first 15 min +2.7/−3.3, best +11.6; the bot's level close took it at +11.6. |
| 11-16 20:00 | B | EMA pullback | sell | 12 / 30 | -12.0 | IG stop | Only +6.2 its way (first 15 min +0.1/−2.9), then back to the full stop after 124 min: a weak signal; the move was too small for its 12-pip stop. |
| 11-17 06:03 | B | level reversal | sell | 9.8 / 20 | 3.0 | bot (20:30) | Worked: first 15 min +3.8/−4.0, best +7.4; the 20:30 close took it at +3.0. |
| 11-17 07:35 | B | level reversal | sell | 13.4 / 20 | -13.4 | IG stop | Only +7.0 its way (first 15 min +2.6/−3.1), then back to the full stop after 133 min: a weak signal; the move was too small for its 13.4-pip stop. |
| 11-17 08:59 | B | range trade | sell | 12 / 100 | -12.0 | IG stop | Went against it at once (first 15 min +0.8/−5.6), never 3 pips its way (best +1.2), full stop after 49 min: the entry/signal was wrong; stop and management did their job. |
| 11-17 10:05 | B | Bollinger bounce | sell | 12 / 100 | -3.3 | IG stop | +15.6; the trail moved its stop to 13193.2 (13:40), but IG refused the next move to 13181.6 about 30 times (13:50–14:06, ATTACHED_ORDER_LEVEL_ERROR) and it was stopped at 13193.2 for −3.3: a mechanical fault of that version's trail (changed by the trail fix cc70dc5, 17 Nov 20:36). |
| 11-17 10:05 | B | level reversal | sell | 20.8 / 20 | -20.8 | IG stop | Same move as the bounce: +15.2, then back to a 20.8-pip stop, wider than its 20-pip target; no break-even in this version: management and stop size. |
| 11-17 14:00 | B | session sweep | buy | 17.1 / 100 | 5.1 | IG stop | Worked: first 15 min +8.8/−7.0, best +12.2; the trail took it at +5.1. |
| 11-17 16:22 | B | level reversal | buy | 22.5 / 20 | -9.2 | bot (20:30) | Its 22.5-pip stop was wider than its 20-pip target; best +9.1, closed at 20:30 at −9.2: stop size and the daily close. |
| 11-17 16:35 | B | Bollinger bounce | sell | 12 / 100 | -12.0 | IG stop | Went against it at once (first 15 min +0.1/−6.7), never 3 pips its way (best +1.7), full stop after 41 min: the entry/signal was wrong; stop and management did their job. |
| 11-17 16:46 | B | slow grind | buy | 15 / 100 | -10.4 | bot (20:30) | Best +7.9, then down; closed at 20:30 at −10.4 before the stop: entry late in a strong push. |
| 11-17 17:16 | B | EMA pullback | buy | 12 / 100 | -12.0 | IG stop | Went against it at once (first 15 min +1.2/−5.0), never 3 pips its way (best +2.8), full stop after 163 min: the entry/signal was wrong; stop and management did their job. |
| 11-17 17:45 | B | Bollinger bounce | sell | 12 / 100 | 10.2 | bot (20:30) | Worked: first 15 min +0.3/−5.6, best +11.3; the 20:30 close took it at +10.2. |
| 11-18 07:30 | B | Asian range breakout | sell | 12 / 100 | 21.7 | IG stop | Worked: first 15 min +6.5/−2.9, best +30.7; stopped in profit at +21.7. |
| 11-18 09:30 | B | Bollinger bounce | buy | 12 / 100 | 7.2 | IG stop | Worked: first 15 min +8.5/−2.0, best +12.5; the trail took it at +7.2. |
| 11-18 12:37 | B | EMA pullback | sell | 12 / 100 | -12.0 | IG stop | Only +5.2 its way (first 15 min +5.2/−7.8), then back to the full stop after 30 min: a weak signal; the move was too small for its 12-pip stop. |
| 11-18 15:44 | C | breakout | sell | 12 / 50 | -12.0 | IG stop | Went +16.1 in 35 minutes, toward its 50-pip target, then all the way back to the 12-pip stop over 7 hours; the breakout has no trail: management. |
| 11-18 16:20 | C | EMA pullback | sell | 12 / 100 | -12.0 | IG stop | Only +4.3 its way (first 15 min +4.3/−3.8), then back to the full stop after 38 min: a weak signal; the move was too small for its 12-pip stop. |
| 11-18 16:37 | C | slow grind | sell | 15 / 100 | -15.0 | IG stop | Went against it at once (first 15 min +0.5/−8.5), never 3 pips its way (best +0.5), full stop after 21 min: the entry/signal was wrong; stop and management did their job. |
| 11-18 19:50 | C | level reversal | sell | 11.3 / 20 | -11.3 | IG stop | Never in profit; stopped in 28 minutes (this trade came from the forming-candle check, 18 Nov review). |
| 11-19 07:35 | C | Asian range breakout | buy | 12 / 100 | -12.0 | IG stop | Only +4.2 its way (first 15 min +0.0/−10.6), then back to the full stop after 112 min: a weak signal; the move was too small for its 12-pip stop. |
| 11-19 11:00 | D | slow grind | buy | 15 / 20 | -15.0 | IG stop | Went against it at once (first 15 min +0.8/−4.5), never 3 pips its way (best +0.8), full stop after 57 min: the entry/signal was wrong; stop and management did their job. |
| 11-19 12:10 | D | session sweep | sell | 22 / 100 | 28.9 | IG stop | Worked: first 15 min +0.0/−9.7, best +42.2; stopped in profit at +28.9. |
| 11-19 15:40 | D | Bollinger bounce | buy | 12 / 100 | -12.0 | IG stop | Only +5.3 its way (first 15 min +3.9/−4.3), then back to the full stop after 49 min: a weak signal; the move was too small for its 12-pip stop. |
| 11-19 17:20 | D | Bollinger bounce | buy | 12 / 100 | 0.4 | Johnny | First 15 min +5.9/−2.8; best +5.9; Johnny closed it after 32 min at +0.4 (not the bot's result). |
| 11-19 19:33 | E | level reversal | buy | 12.6 / 20 | -3.5 | Johnny | First 15 min +0.0/−5.0; best -0.3; Johnny closed it after 43 min at -3.5 (not the bot's result). |
| 11-19 19:51 | E | EMA pullback | sell | 12 / 30 | -7.9 | Johnny | First 15 min +0.8/−7.7; best +0.8; Johnny closed it after 25 min at -7.9 (not the bot's result). |
| 11-20 06:07 | E | level reversal | buy | 17.3 / 20 | -17.3 | IG stop | +10.5 an hour in, then fell back for 5 hours to the 17.3-pip stop; no break-even in this version: management and stop size. |
| 11-20 07:15 | E | Asian range breakout | buy | 12 / 100 | -12.0 | IG stop | Went against it at once (first 15 min +0.0/−8.9), never 3 pips its way (best -0.9), full stop after 45 min: the entry/signal was wrong; stop and management did their job. |
| 11-20 07:25 | E | Bollinger bounce 5m | sell | 12 / 100 | -1.7 | bot | +2.0 at best, then closed at −1.7 by the 5m bounce's level-close rule (London low and pivot): the rule cut a small loss. |
| 11-20 07:30 | E | session sweep | sell | 12 / 100 | 7.5 | IG stop | Worked: first 15 min +0.7/−7.6, best +13.6; the trail took it at +7.5. |
| 11-20 13:10 | E | level reversal | buy | 34.3 / 20 | -26.1 | Johnny | Bought 26.6 pips above the level after one 15-pip candle, with a 34.3-pip stop for a 20-pip target; never more than +0.9; Johnny closed it at −26.1: entry and stop size. |
| 11-20 13:25 | E | slow grind | buy | 15 / 20 | -15.0 | IG stop | Bought the break of a pause 1.7 pips under the day's high at the same candle the hourly bounce read as a rejection; never in profit, stopped in 16 minutes: entry. |
| 11-20 13:30 | E | Bollinger bounce | sell | 12 / 100 | 2.9 | IG stop | Worked: first 15 min +6.7/−3.6, best +13.0; the trail took it at +2.9. |
| 11-20 13:32 | E | Bollinger bounce 5m | sell | 12 / 100 | -0.0 | bot | +11.0 (the 5m bounce has no trail in this build), then closed at 0.0 by its level-close rule at the pivot: management (the level close). |
| 11-20 13:35 | E | session sweep | sell | 12 / 100 | 0.9 | IG stop | Worked: first 15 min +2.7/−5.1, best +12.1; the trail took it at +0.9. |
| 11-20 14:45 | E | Bollinger bounce 5m | sell | 12 / 100 | -12.0 | IG stop | Only +3.1 its way (first 15 min +1.3/−6.0), then back to the full stop after 58 min: a weak signal; the move was too small for its 12-pip stop. |
| 11-20 17:55 | E | level reversal | sell | 13 / 20 | 2.9 | Johnny | First 15 min +0.0/−6.4; best +4.8; Johnny closed it after 47 min at +2.9 (not the bot's result). |
| 11-20 18:42 | E | EMA pullback | sell | 12 / 30 | -1.4 | Johnny | First 15 min +0.2/−4.4; best +0.2; Johnny closed it after 0 min at -1.4 (not the bot's result). |
| 11-20 18:45 | E | level reversal | sell | 14.4 / 20 | – | open | still open at 19:00 (stop 13103.3 at IG). |

### W2. The losers grouped by cause (bot and IG exits only, Johnny's closes apart)

| Cause | What it means | Trades | Pips | Which strategies |
|---|---|---|---|---|
| **A. Wrong from the start** | never 3 pips its way, then the full stop: the entry signal was wrong; stop and management did their job | 14 | **−181.6** | EMA pullback 4, level reversal 3, slow grind 3, Bollinger bounce 2, range trade 1, Asian range breakout 1 |
| **B. Too small a move** | 3–8 pips its way, then the full stop: a weak signal; the move never paid for a 12-pip stop | 8 | **−97.4** | EMA pullback 4, level reversal 1, Asian range breakout 1, Bollinger bounce 1, Bollinger bounce 5m 1 |
| **C. Gave back a real gain** | 8 pips or more its way (+10.5 to +22.6), then the full stop: management (nothing locked the gain) | 6 | **−81.8** | level reversal 3 (−54.5), EMA pullback 1, Bollinger bounce 1 (the 17 Nov trail refusal), breakout 1 |
| **E. The bot's own close at a loss** | closed at 20:30 or by the level-close rule before its stop | 3 | **−21.3** | level reversal 1, slow grind 1, Bollinger bounce 5m 1 |
| *Johnny's closes* | *not the bot's result* | *6* | *−35.6* | *level reversal 3, EMA pullback 2, Bollinger bounce 1* |

Two causes overlap the groups above:
- **Stop wider than the target** (level reversal only): 17 Nov 10:05 (stop 20.8, target 20, −20.8), 17 Nov 16:22
  (22.5 / 20, −9.2), 20 Nov 13:10 (34.3 / 20, −26.1, Johnny's close).
- **Opened against a trade already open in the other direction:** 15 of the week's trades. Of the 14 closed by the
  bot or IG: 5 won, 8 lost and 1 was flat, −57.5 pips net.

Wins: 12 trades, +107.9 pips. Session sweep 4 (+42.4), Bollinger bounce 3 (+20.3), level reversal 2 (+11.3),
Asian range breakout 1 (+21.7), range trade 1 (+11.6), slow grind 1 (+0.6). Only two wins reached more than half
their target: the 18 Nov Asian range breakout (+21.7, trailed from +30.7) and the 19 Nov session sweep (+28.9,
trailed from +42.2). Most wins were trails or the 20:30 close taking a small gain.

### W3. Each strategy this week

| Strategy | Trades | Wins | Losses | Pips | Johnny's closes | Broken, or rules that don't suit this market? |
|---|---|---|---|---|---|---|
| EMA pullback | 9 | 0 | 9 | **−108.0** | −9.3 (2) | **Rules.** All 9 were full 12-pip stops; 8 never got more than +6.2 (causes A and B). No mechanical fault: every stop was sent, accepted, exactly 12, and hit for real. 3 wins in 22 since 9 Nov. |
| level reversal | 10 | 2 | 8 | **−106.4** | −26.7 (3) | **Mostly the rule's risk shape** (no cap on the stop, fixed 20-pip target, a trigger that never expires, no break-even in B, C or E), plus wrong signals (3 of cause A). Three trades were +10.5 to +15.2 and lost their full stop (−54.5). |
| slow grind | 5 | 1 | 4 | **−54.8** | – | **Rules.** 3 of 4 losses never went 3 pips its way; it buys or sells the break of a pause at the end of a move. |
| Bollinger bounce (hourly) | 7 | 3 | 4 | −19.0 | +0.4 (1) | Rules, with **one mechanical fault in B**: the 17 Nov 10:05 trail refused by IG 31 times (fixed since). Otherwise the full 12 on losers and small trailed wins. |
| Bollinger bounce 5m | 3 | 0 | 2 (1 flat) | −13.7 | – | Too few to say. The level-close rule cut one at −1.7 and one at 0.0 (after +11.0; it has no trail). |
| breakout | 1 | 0 | 1 | −12.0 | – | Too few. The 18 Nov sell was +16.1, then lost 12 over 7 hours: no trail (management). Its live stop is now 6. |
| Asian range breakout | 3 | 1 | 2 | −2.3 | – | Too few. One good trailed win (+21.7), two signals that failed at once. |
| range trade | 2 | 1 | 1 | −0.4 | – | Too few. |
| session sweep | 4 | 4 | 0 | **+42.4** | – | Working so far (small sample). |
| **All** | **44** | **12** | **31** (1 flat) | **−274.2** (−£2,742) | **−35.6 (6)** | |

### W4. My recommendations, most important first (nothing built or changed)

1. **Switch the EMA pullback off.** Evidence: 0 wins in 9 this week (−108.0), 3 in 22 since 9 Nov (−138.0), and it
   lost in every code version (A −30.0, B −96.0, C −12.0). Every loss was a clean full stop with no mechanical
   fault, so this is the rule, not the plumbing. It is the biggest single drain.
2. **Fix the level reversal's risk before trading it again, or switch it off until then.** Evidence: −106.4 this
   week and −26.7 more on Johnny's closes. Three stops were at least as wide as the 20-pip target, and 34.3 pips was
   risked to make 20. Three trades gave back +10.5 to +15.2. The fix, in order of value:
   - refuse a trade whose stop is wider than its target (or bring back the 20-pip cap);
   - bring back entry within 6 pips of the level;
   - make the trigger expire 1–2 candles after confirmation;
   - break-even at +10.
3. **Switch the slow grind off.** Evidence: 1 win in 5 this week (−54.8), 4 in 15 since 9 Nov (−92.4). Three of
   this week's 4 losses never went 3 pips its way: its entries are late.
4. **Add a "don't give back a real gain" rule to every strategy:** for example, move the stop to break-even
   once a trade is +10. Evidence: cause C, 6 trades that were +10.5 to +22.6 and ended at −81.8 pips in total.
   In the live code only the hourly bounce and the three session strategies trail (from +12); the slow grind
   closes at +10 once it has been +15; the EMA pullback, level reversal, breakout, range trade and bounce 5m have
   nothing.
5. **Stop strategies trading against each other:** no new trade against the direction of a trade that is already
   open. Evidence: 15 trades this week opened against an open opposite trade (bot exits 5 won, 8 lost, 1 flat,
   −57.5). On 20 Nov 13:10–13:35, five trades opened both ways off one move.
6. **Make `.env` honest and set the breakout stop on purpose.** Remove the eight switches the live code ignores
   (`LEVEL_STOPS`, `LR_ENTRY_NEAR_LEVEL`, `TRAIL_NO_LOSS` and others). Choose 6 or 12 for `[breakout]
   stop_loss_pips` (it is 6 now, Johnny chose 12 on 10 Nov).
7. **Keep:**
   - the session sweep (4 from 4, +42.4);
   - the Asian range breakout and the hourly Bollinger bounce, on watch (near flat; their trails produced the
     week's best wins);
   - the breakout, range trade and Bollinger bounce 5m, on watch (too few trades to judge).

These are judgments from one week of live demo trades (plus 9–13 Nov for context), and every sample is small. The
live demo stays the judge.

## Files in this folder

- `reconcile.py`: matches every live trade (records + journal) to IG's records in `data/orders/ig_check_result*.json`; writes `trades.csv`.
- `trades.csv`: one row per live trade since 9 Nov, with the bot's and IG's figures side by side.
- `tables.py`, `stats.py`, `assemble.py`: the Step 1 and Step 2 tables and this report.
- `replay_live_code.py`: the Step 4 replay through an exact copy of 02f6c7e, in paper mode (it never contacts IG and writes no live file).
- `replay_week_16_20.json`, `replay_week_09_13.json`, `replay_restart_19nov1844.json`, `replay_d9e5d0e_19nov.json`: the replays' paper trades and paper safety refusals.
- `week_paths.py`, `week_paths.csv`, `week_review.py`: the week review (what price did after each entry, and the one-line verdicts).

IG was read twice in this investigation (18:43 and 18:53 UTC), and an earlier session had read it at 16:12. All
three reads went through the price service's read-only check, and their results are kept as
`data/orders/ig_check_result.2026-11-20_*.json`.
