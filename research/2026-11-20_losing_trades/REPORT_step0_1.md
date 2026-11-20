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

E_TABLE

### 9 – 19 Nov, by code version

OLDER_TABLES

Notes on the IG match: IG's transaction list misses the 12 Nov 19:02 and 22:00 EMA pullbacks, so their close is
IG's activity close level. Two trades differ between the bot's record and IG, and IG is used for both: 11 Nov 06:55
Bollinger bounce (bot +0.1, IG −3.3) and 18 Nov 12:37 EMA pullback (bot −12.6, IG −12.0).
