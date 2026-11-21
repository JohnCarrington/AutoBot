# EMA pullback on the IG demo account, 9-20 November 2026: how it really behaved

Read-only investigation for Johnny, 21 Nov 2026. Nothing in the bot was changed, restarted or sent to IG. The sources are the bot's own records:
- `data/records/GBPUSD/trades.jsonl` and `decisions.jsonl`;
- `data/orders/GBPUSD/orders.jsonl`;
- IG's activity and transactions already saved by the bot's read-only IG checks (`data/orders/ig_check_result*.json`);
- the stored candles (`data/candles/GBPUSD`);
- the stored news calendar (`data/news/calendar.json`);
- `logs/prices.log*`;
- `git reflog`.

Everything was worked out with the bot's own code, from an exact `git archive` copy of the checked-out commit. Its EMA pullback, indicator, level and news code is identical to `02f6c7e`, the code the running service loaded. Code is quoted from `02f6c7e`.

The scripts are `build.py` (writes `results.json`) and `report.py` (writes this report's detail and the CSVs). The full lists are in `trades.csv`, `setups.csv` and `blocked.csv`. UK time = GMT = UTC in November.

The week ended Friday 20 Nov 22:00, so "up to now" means up to then.

## Summary

**The trades.** There were 24 EMA pullback trades. Johnny closed 2 by hand (−9.3 pips); they are kept apart. The bot's own 22 exits: 3 won, 19 lost, −138.0 pips. Every exit was IG's 12-pip stop or IG's take profit.

The code changed twice, so the results are split into three periods:

| Period | Code | Bot's own exits |
|---|---|---|
| A, 9–13 Nov 10:22 | first build: hourly slope checked by size only | 12 trades, 3 won, −18.0 pips |
| B, 13 Nov 10:22–19 Nov 18:44 | slope must point the trade's way, plus later gates | 10 trades, 0 won, −120.0 pips |
| C, from 19 Nov 18:44 | first-build-plus: slope by size only again | none (only the 2 owner closes) |

**1. Hourly slope direction.**
- **The problem never happened.** No trade had any of the three hourly EMAs' 3-hour slopes pointing against it, either as the bot read it or as it really was at the touch. Only 4 of the 483 setups had one (sells on 20 Nov, 09:10–09:30). None reached its entry.
- **Something the records showed instead:** from 9 Nov to 11 Nov 14:56, the live bot judged the hourly trend from hourly candles as stored at its last start. For example, the 10 Nov buys used the 9 Nov 11:00 hourly candle. This affected 7 trades and was fixed by `04b3a83`.

**2. Several trades at once.** This happened 4 times and involved 13 of the 24 trades. At most 3 were open together, always going the same way:

| When | Trades | Result |
|---|---|---|
| 10 Nov | 3 buys | −36.0 |
| 11 Nov morning | 3 sells | +90.0 |
| 11 Nov evening | 2 sells | −24.0 |
| 16 Nov | 5 sells, at most 2 at once | −60.0 |

**3. Big news.**
- No trade opened from 15 minutes before to 30 minutes after a big release.
- 1 trade was open when one came out: trade 15, through GBP Unemployment Rate on 17 Nov 07:00. It was stopped at 09:48 for −12.0. One trade is too few to say anything.

**4. Hours and overnight.**
- 5 trades opened outside 06:00–20:30 UK. All 5 lost 12.0, all in period A.
- 3 trades were held past 20:30 UK. All 3 lost 12.0.
- 5 trades were stopped between 22:00:00 and 22:04:53, the IG rollover. Spreads in the stored 22:00 candles were 7.3 to 16.9 pips.
- Trade 11 opened at 22:00:03 with an offer 16.9 above the bid and was stopped the same second. That was before the 21:55–22:15 no-trade window was added on 13 Nov.

**5. Slippage and stale prices.** The code checks neither.
- Against the setup's entry, IG's fill was between 1.8 pips worse and 0.3 pips better. The largest gaps are buys, and they include the spread, because the entry is on the bid.
- Against the same side of the live price that triggered it, the fill was between 0.9 pips worse and 0.4 pips better.
- The price was 0 to 3 seconds old (IG's own time stamp) when the order went out.

**The direction rule.**
- The bot applies it only when a setup reaches its entry price. Setups that never get there are never checked or logged, so all 483 setups were rebuilt from the candles with the bot's own code. The rebuild matches every logged idea and every trade.
- 85 setups reached their entry while the service was live: 24 traded, 14 were allowed but not sent (another one had already gone that candle), and 47 were blocked.
- Of the 47 blocked: the analyser state blocked 40 (30 on its own). The pivot blocked 2 and the 100 EMA blocked 1, never on their own. Period B's extra gates (hourly read, TREND_STILL_GOING, ANALYSER_GOVERNS_ALL) blocked 15 (7 on their own).
- Trades by state at the open: emerging trend, 11 trades, 0 won, −132.0; trend, 11 trades, 3 won, −6.0.
- **LOOK BACK, not live results:** from the entry, 17 blocked setups would have reached +30 first, 27 would have hit −12 first, 1 reached neither, and 2 could not have opened.
- Blocked setups came at all hours. 26 of the 47 were between 16:00 and 23:59 UK. The pivot blocked only 2, both buys at night, so the record can't show whether it blocks early in trend days.

**Wick past the 21 EMA.** 54 of the 86 setups that reached their entry had a candle wick beyond the 21 EMA without closing beyond it. Among the bot's 22 trades:
- with a wick: 15 trades, 2 won, −96.0;
- without: 7 trades, 1 won, −42.0.

The largest wick on a trade was 2.5 pips. With 22 trades and 3 winners, this is too small a sample to say whether wicks matter. The full list sorted by distance is in 3.4, with no cut-off.


## 0. Which code was live, and the three periods

Every start of the price service from 9 Nov (each `Trading ON` line in the bot's log), with the commit checked out at that moment (`git reflog` of /opt/autobot, in the order HEAD moved). "Code as of" is the newest commit before it that changed anything outside `research/` and `docs/`. The service ran from 19 Nov 18:44 to the end of the week without a restart, so `02f6c7e` ran to the end; the later checkouts (`26c06fc` 19 Nov 20:20, `bb085f4` 20 Nov 12:11, `5d7942e` 20 Nov 21:10) were never loaded. Their EMA pullback code is the same as `02f6c7e`'s. UK time is GMT in November, so every time in this report is both UK time and UTC.

| Start (UK) | Log line (quoted) | HEAD | Code as of | EMA pullback hourly slope check | Other EMA-related code present (switch state at the time is not recorded except in the blocked reasons) |
|---|---|---|---|---|---|
| Mon 09 Nov 00:09:52 | `logs/prices.log.12:199` `INFO    autobot.trading: Trading ON: 0 open trade(s) taken over; the strategies are up to 2026-11-09 00:09 UTC.` | `f99efe1` | `f99efe1` Test order extras (a), (b), (c) one at a time; read-only chec | size only (abs) | - |
| Mon 09 Nov 12:26:37 | `logs/prices.log.12:660` `INFO    autobot.trading: Trading ON: 3 open trade(s) taken over; the strategies are up to 2026-11-09 12:26 UTC.` | `2ff445f` | `2ff445f` One view at a time: no reversal trade against a strong push o | size only (abs) | - |
| Wed 11 Nov 06:19:43 | `logs/prices.log.10:338` `INFO    autobot.trading: Trading ON: 0 open trade(s) taken over; the strategies are up to 2026-11-11 06:19 UTC.` | `addf1b8` | `addf1b8` Closes count only when IG confirms them; the bot's trades che | size only (abs) | - |
| Wed 11 Nov 06:47:15 | `logs/prices.log.10:390` `INFO    autobot.trading: Trading ON: 0 open trade(s) taken over; the strategies are up to 2026-11-11 06:46 UTC.` | `dfa9075` | `dfa9075` The owner's closes by hand: recorded apart at IG's price, a s | size only (abs) | - |
| Wed 11 Nov 08:34:18 | `logs/prices.log.10:507` `INFO    autobot.trading: Trading ON: 3 open trade(s) taken over; the strategies are up to 2026-11-11 08:33 UTC.` | `03be0aa` | `02a8dfe` Range trade closed in full and bounce by half at the opposite | size only (abs) | - |
| Wed 11 Nov 14:56:48 | `logs/prices.log.10:813` `INFO    autobot.trading: Trading ON: 2 open trade(s) taken over; the strategies are up to 2026-11-11 14:56 UTC.` | `04b3a83` | `04b3a83` The strategies read the candle store afresh on every call, ne | size only (abs) | - |
| Wed 11 Nov 17:37:51 | `logs/prices.log.10:932` `INFO    autobot.trading: Trading ON: 1 open trade(s) taken over; the strategies are up to 2026-11-11 17:37 UTC.` | `6ffa36f` | `6ffa36f` The pace and target rule: a Bollinger bounce against open tre | size only (abs) | - |
| Wed 11 Nov 18:32:36 | `logs/prices.log.10:993` `INFO    autobot.trading: Trading ON: 2 open trade(s) taken over; the strategies are up to 2026-11-11 18:32 UTC.` | `9467e19` | `6ffa36f` The pace and target rule: a Bollinger bounce against open tre | size only (abs) | - |
| Thu 12 Nov 18:07:26 | `logs/prices.log.9:767` `INFO    autobot.trading: Trading ON: 0 open trade(s) taken over; the strategies are up to 2026-11-12 18:06 UTC.` | `79c5dcf` | `79c5dcf` Trend proof as design 2.5 line 85: the bounce fails first, th | size only (abs) | - |
| Fri 13 Nov 10:22:14 | `logs/prices.log.8:487` `INFO    autobot.trading: Trading ON: 1 open trade(s) taken over; the strategies are up to 2026-11-13 10:21 UTC.` | `d96de5f` | `d96de5f` EMA pullback: no new trade from 21:55 to 22:15 UK, the rollov | signed (must point the trade's way) | 21:55-22:15 rollover window |
| Fri 13 Nov 15:58:26 | `logs/prices.log.8:708` `INFO    autobot.trading: Trading ON: 0 open trade(s) taken over; the strategies are up to 2026-11-13 15:57 UTC.` | `d96de5f` | `d96de5f` EMA pullback: no new trade from 21:55 to 22:15 UK, the rollov | signed (must point the trade's way) | 21:55-22:15 rollover window |
| Fri 13 Nov 19:41:21 | `logs/prices.log.8:860` `INFO    autobot.trading: Trading ON: 0 open trade(s) taken over; the strategies are up to 2026-11-13 19:40 UTC.` | `e24c58f` | `e24c58f` Bollinger bounce: stop moved to break-even at IG once 6 pips  | signed (must point the trade's way) | 21:55-22:15 rollover window |
| Fri 13 Nov 21:14:41 | `logs/prices.log.7:42` `INFO    autobot.trading: Trading ON: 0 open trade(s) taken over; the strategies are up to 2026-11-13 21:13 UTC.` | `1a65151` | `1a65151` Level reversal: up to 2 open at once; take profit at the next | signed (must point the trade's way) | 21:55-22:15 rollover window |
| Fri 13 Nov 21:41:35 | `logs/prices.log.7:83` `INFO    autobot.trading: Trading ON: 0 open trade(s) taken over; the strategies are up to 2026-11-13 21:40 UTC.` | `714d1c6` | `714d1c6` Range trade: opens right at the band; closes only at the oppo | signed (must point the trade's way) | 21:55-22:15 rollover window |
| Sat 14 Nov 06:19:19 | `logs/prices.log.7:147` `INFO    autobot.trading: Trading ON: 0 open trade(s) taken over; the strategies are up to 2026-11-14 06:18 UTC.` | `714d1c6` | `714d1c6` Range trade: opens right at the band; closes only at the oppo | signed (must point the trade's way) | 21:55-22:15 rollover window |
| Sun 15 Nov 00:16:58 | `logs/prices.log.6:31` `INFO    autobot.trading: Trading ON: 0 open trade(s) taken over; the strategies are up to 2026-11-15 00:15 UTC.` | `b5ca37a` | `b5ca37a` Back to step 3 of the Friday replay; the hourly read behind H | signed (must point the trade's way) | 21:55-22:15 rollover window, hourly read |
| Sun 15 Nov 17:47:46 | `logs/prices.log.6:94` `INFO    autobot.trading: Trading ON: 0 open trade(s) taken over; the strategies are up to 2026-11-15 17:46 UTC.` | `9b61661` | `9b61661` Bollinger bounce off the hourly band, with a trail; two bounc | signed (must point the trade's way) | 21:55-22:15 rollover window, hourly read |
| Mon 16 Nov 23:07:38 | `logs/prices.log.4:141` `INFO    autobot.trading: Trading ON: 1 open trade(s) taken over; the strategies are up to 2026-11-16 23:07 UTC.` | `e595f6e` | `e595f6e` Trend still going: the EMA pullback, slow grind and breakout  | signed (must point the trade's way) | 21:55-22:15 rollover window, hourly read, TREND_STILL_GOING |
| Mon 16 Nov 23:47:07 | `logs/prices.log.4:200` `INFO    autobot.trading: Trading ON: 1 open trade(s) taken over; the strategies are up to 2026-11-16 23:46 UTC.` | `aea2275` | `dc261d7` Three session strategies: Asian range breakout, session sweep | signed (must point the trade's way) | 21:55-22:15 rollover window, hourly read, TREND_STILL_GOING |
| Tue 17 Nov 20:24:41 | `logs/prices.log.4:1099` `INFO    autobot.trading: Trading ON: 3 open trade(s) taken over; the strategies are up to 2026-11-17 20:24 UTC.` | `233d054` | `aac51f6` Planner: owner's R1-R3 (17 November 2026): FC-04 labels; iden | signed (must point the trade's way) | 21:55-22:15 rollover window, hourly read, TREND_STILL_GOING |
| Tue 17 Nov 20:46:38 | `logs/prices.log.4:1157` `INFO    autobot.trading: Trading ON: 0 open trade(s) taken over; the strategies are up to 2026-11-17 20:46 UTC.` | `cc70dc5` | `cc70dc5` Merge trail-fix: trail stop moves IG can accept: compared wit | signed (must point the trade's way) | 21:55-22:15 rollover window, hourly read, TREND_STILL_GOING |
| Wed 18 Nov 13:36:02 | `logs/prices.log.3:627` `INFO    autobot.trading: Trading ON: 0 open trade(s) taken over; the strategies are up to 2026-11-18 13:35 UTC.` | `3d50353` | `3d50353` Analyser control stage 1b: trends called quickly, behind ANAL | signed (must point the trade's way) | 21:55-22:15 rollover window, hourly read, TREND_STILL_GOING, ANALYSER_GOVERNS_ALL |
| Thu 19 Nov 09:49:56 | `logs/prices.log.2:450` `INFO    autobot.trading: Trading ON: 0 open trade(s) taken over; the strategies are up to 2026-11-19 09:49 UTC.` | `d9e5d0e` | `d9e5d0e` Merge fix/live-check-and-journal-provenance (ee3eaa6) into ma | signed (must point the trade's way) | 21:55-22:15 rollover window, hourly read, TREND_STILL_GOING, ANALYSER_GOVERNS_ALL, LEVEL_STOPS |
| Thu 19 Nov 18:44:38 | `logs/prices.log.2:828` `INFO    autobot.trading: Trading ON: 0 open trade(s) taken over; the strategies are up to 2026-11-19 18:44 UTC.` | `02f6c7e` | `f35bd1b` first-build-plus: production's safety rules 9 (one view at a  | size only (abs) | 21:55-22:15 rollover window |

Counts below are kept apart by period:

* **Period A: 9 Nov 00:09 - 13 Nov 10:22 (f99efe1 to 79c5dcf; first-build EMA pullback, slope size only)**
* **Period B: 13 Nov 10:22 - 19 Nov 18:44 (d96de5f to d9e5d0e; slope must point the trade's way, plus later gates)**
* **Period C: 19 Nov 18:44 - 20 Nov 22:00 (02f6c7e first-build-plus; slope size only again)**
* Inside period A, until the 11 Nov 14:56:48 start (`04b3a83` "The strategies read the candle store afresh on every call, never a copy kept from start-up"), the live strategies judged the hourly trend from the hourly candles as they were stored when the service started. This is shown in the logged step 0 of every trade of 9-11 Nov (Part 1.1), and this report reproduces it exactly.

## 1. The 24 EMA pullback trades on the IG demo account

IG's own figures are used for every open and close (IG's activity and transactions saved by the bot's read-only IG checks in `data/orders/ig_check_result*.json`; failing that, IG's confirmations copied into `data/orders/GBPUSD/orders.jsonl`). The bot's record is `data/records/GBPUSD/trades.jsonl`. Pips are IG's fill to IG's close. A close is the owner's when IG shows channel SYSTEM and the close is not at the stop or the take profit (owner rule, 11 Nov); there are 2, listed apart and left out of every result below.

| # | Opened (IG) | Closed (IG) | Dir | Period / commit | Analyser state at open (trades.jsonl) | IG fill | IG stop | IG limit | IG close | Pips | Closed by | Record lines | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Mon 09 Nov 21:02:06 | Mon 09 Nov 22:00:00 | buy | A `2ff445f` | trend up, slow grind | 13443.6 | 13431.6 | 13473.6 | 13431.6 | -12.0 | IG stop (IG channel SYSTEM) | trades.jsonl:20,21; orders.jsonl:87,88; decisions.jsonl:281 | open: IG activity (ig_check_result.2026-11-09_day.json, dealId DIAAAAYTGDX2MBQ); close: IG transactions |
| 2 | Tue 10 Nov 05:01:31 | Tue 10 Nov 09:00:12 | buy | A `2ff445f` | emerging trend up | 13451.0 | 13439.0 | 13551.0 | 13439.0 | -12.0 | IG stop (IG channel SYSTEM) | trades.jsonl:22,32; orders.jsonl:93,94; decisions.jsonl:351 | open: IG activity (ig_check_result.2026-11-10_morning.json, dealId DIAAAAYTHAMJYBP); close: IG transactions |
| 3 | Tue 10 Nov 06:12:03 | Tue 10 Nov 09:00:11 | buy | A `2ff445f` | emerging trend up | 13452.8 | 13440.8 | 13552.8 | 13440.8 | -12.0 | IG stop (IG channel SYSTEM) | trades.jsonl:23,31; orders.jsonl:96,97; decisions.jsonl:377 | open: IG activity (ig_check_result.2026-11-10_morning.json, dealId DIAAAAYTHB8UGBY); close: IG transactions |
| 4 | Tue 10 Nov 07:21:03 | Tue 10 Nov 09:00:08 | buy | A `2ff445f` | emerging trend up | 13456.1 | 13444.1 | 13556.1 | 13444.1 | -12.0 | IG stop (IG channel SYSTEM) | trades.jsonl:24,30; orders.jsonl:99,100; decisions.jsonl:401 | open: IG activity (ig_check_result.2026-11-10_morning.json, dealId DIAAAAYTKU7WSBH); close: IG transactions |
| 5 | Wed 11 Nov 07:32:27 | Wed 11 Nov 13:20:33 | sell | A `dfa9075` | trend down, slow grind | 13330.9 | 13342.9 | 13300.9 | 13300.9 | +30.0 | IG take profit (IG channel SYSTEM) | trades.jsonl:58,71; orders.jsonl:201,202; decisions.jsonl:747 | open: IG activity (ig_check_result.2026-11-11_rest.json, dealId DIAAAAYT4CWFTA2); close: IG transactions |
| 6 | Wed 11 Nov 08:16:26 | Wed 11 Nov 13:51:00 | sell | A `dfa9075` | trend down, slow grind | 13323.1 | 13335.1 | 13293.1 | 13293.1 | +30.0 | IG take profit (IG channel SYSTEM) | trades.jsonl:61,73; orders.jsonl:210,211; decisions.jsonl:760 | open: IG activity (ig_check_result.2026-11-11_rest.json, dealId DIAAAAYT4FSZFBN); close: IG transactions |
| 7 | Wed 11 Nov 10:51:37 | Wed 11 Nov 13:56:51 | sell | A `03be0aa` | trend down, slow grind | 13317.0 | 13329.0 | 13287.0 | 13287.0 | +30.0 | IG take profit (IG channel SYSTEM) | trades.jsonl:66,74; orders.jsonl:236,237; decisions.jsonl:800 | open: IG activity (ig_check_result.2026-11-11_rest.json, dealId DIAAAAYT4TW6QAN); close: IG transactions |
| 8 | Wed 11 Nov 18:48:20 | Wed 11 Nov 22:03:08 | sell | A `9467e19` | trend down, slow grind | 13273.5 | 13285.5 | 13243.5 | 13285.5 | -12.0 | IG stop (IG channel SYSTEM) | trades.jsonl:81,85; orders.jsonl:296,297; decisions.jsonl:918 | open: IG activity (ig_check_result.2026-11-11_rest.json, dealId DIAAAAYT544FZB2); close: IG transactions |
| 9 | Wed 11 Nov 21:06:02 | Wed 11 Nov 22:00:00 | sell | A `9467e19` | emerging trend down | 13270.7 | 13282.7 | 13240.7 | 13282.7 | -12.0 | IG stop (IG channel SYSTEM) | trades.jsonl:83,84; orders.jsonl:304,305; decisions.jsonl:935 | open: IG activity (ig_check_result.2026-11-11_rest.json, dealId DIAAAAYT6AZB7BF); close: IG transactions |
| 10 | Thu 12 Nov 19:02:17 | Thu 12 Nov 20:02:25 | sell | A `79c5dcf` | emerging trend down | 13225.6 | 13237.6 | 13125.6 | 13237.6 | -12.0 | IG stop (IG channel SYSTEM) | trades.jsonl:95,96; orders.jsonl:349,350; decisions.jsonl:1183 | open: IG activity (ig_check_result.2026-11-12_to_now.json, dealId DIAAAAYUKBRCMA6); close: IG activity (ig_check_result.2026-11-12_to_now.json) |
| 11 | Thu 12 Nov 22:00:03 | Thu 12 Nov 22:00:03 | sell | A `79c5dcf` | emerging trend down | 13230.7 | 13242.7 | 13130.7 | 13242.7 | -12.0 | IG stop (IG channel SYSTEM) | trades.jsonl:97,98; orders.jsonl:355,356; decisions.jsonl:1208 | open: IG activity (ig_check_result.2026-11-12_to_now.json, dealId DIAAAAYUKK65XAH); close: IG activity (ig_check_result.2026-11-12_to_now.json) |
| 12 | Thu 12 Nov 23:47:19 | Fri 13 Nov 01:41:27 | sell | A `79c5dcf` | emerging trend down | 13229.2 | 13241.2 | 13129.2 | 13241.2 | -12.0 | IG stop (IG channel SYSTEM) | trades.jsonl:99,100; orders.jsonl:361,362; decisions.jsonl:1219 | open: IG activity (ig_check_result.2026-11-12_to_now.json, dealId DIAAAAYUKQXNTBX); close: IG transactions |
| 13 | Fri 13 Nov 10:28:47 | Fri 13 Nov 13:30:02 | sell | B `d96de5f` | emerging trend down | 13225.1 | 13237.1 | 13195.1 | 13237.1 | -12.0 | IG stop (IG channel SYSTEM) | trades.jsonl:105,108; orders.jsonl:386,387; decisions.jsonl:1313 | open: IG activity (ig_check_result.2026-11-12_to_now.json, dealId DIAAAAYUPMWB6AY); close: IG transactions |
| 14 | Mon 16 Nov 10:50:10 | Mon 16 Nov 12:12:21 | sell | B `9b61661` | emerging trend down | 13187.1 | 13199.1 | 13157.1 | 13199.1 | -12.0 | IG stop (IG channel SYSTEM) | trades.jsonl:117,119; orders.jsonl:449,450; decisions.jsonl:1519 | open: IG activity (ig_check_result.2026-11-13_1500_to_17.json, dealId DIAAAAYUVWT52A8); close: IG transactions |
| 15 | Mon 16 Nov 14:26:00 | Tue 17 Nov 09:48:55 | sell | B `9b61661` | emerging trend down | 13192.1 | 13204.1 | 13162.1 | 13204.1 | -12.0 | IG stop (IG channel SYSTEM) | trades.jsonl:122,141; orders.jsonl:467,468; decisions.jsonl:1557 | open: IG activity (ig_check_result.2026-11-13_1500_to_17.json, dealId DIAAAAYUWJDEEAW); close: IG transactions |
| 16 | Mon 16 Nov 14:57:56 | Mon 16 Nov 15:16:57 | sell | B `9b61661` | trend down, slow grind | 13187.3 | 13199.3 | 13157.3 | 13199.3 | -12.0 | IG stop (IG channel SYSTEM) | trades.jsonl:123,124; orders.jsonl:472,473; decisions.jsonl:1569 | open: IG activity (ig_check_result.2026-11-13_1500_to_17.json, dealId DIAAAAYUWRLWZA2); close: IG transactions |
| 17 | Mon 16 Nov 15:50:42 | Mon 16 Nov 16:09:45 | sell | B `9b61661` | trend down, slow grind | 13183.2 | 13195.2 | 13153.2 | 13195.2 | -12.0 | IG stop (IG channel SYSTEM) | trades.jsonl:126,127; orders.jsonl:484,485; decisions.jsonl:1591 | open: IG activity (ig_check_result.2026-11-13_1500_to_17.json, dealId DIAAAAYUWW4E4BY); close: IG transactions |
| 18 | Mon 16 Nov 16:53:48 | Mon 16 Nov 17:11:19 | sell | B `9b61661` | trend down, slow grind | 13182.5 | 13194.5 | 13152.5 | 13194.5 | -12.0 | IG stop (IG channel SYSTEM) | trades.jsonl:128,129; orders.jsonl:492,493; decisions.jsonl:1606 | open: IG activity (ig_check_result.2026-11-13_1500_to_17.json, dealId DIAAAAYUW8M98AY); close: IG transactions |
| 19 | Mon 16 Nov 20:00:03 | Mon 16 Nov 22:04:53 | sell | B `9b61661` | emerging trend down | 13184.7 | 13196.7 | 13154.7 | 13196.7 | -12.0 | IG stop (IG channel SYSTEM) | trades.jsonl:132,135; orders.jsonl:508,509; decisions.jsonl:1637 | open: IG activity (ig_check_result.2026-11-13_1500_to_17.json, dealId DIAAAAYUXPMB8BF); close: IG transactions |
| 20 | Tue 17 Nov 17:16:01 | Tue 17 Nov 19:59:26 | buy | B `aea2275` | trend up, slow grind | 13225.1 | 13213.1 | 13325.1 | 13213.1 | -12.0 | IG stop (IG channel SYSTEM) | trades.jsonl:152,155; orders.jsonl:650,651; decisions.jsonl:1807 | open: IG activity (ig_check_result.2026-11-19_0947.json, dealId DIAAAAYVGFY5RBT); close: IG transactions |
| 21 | Wed 18 Nov 12:37:37 | Wed 18 Nov 13:07:56 | sell | B `cc70dc5` | trend down, slow grind | 13156.4 | 13168.4 | 13056.4 | 13168.4 | -12.0 | IG stop (IG channel SYSTEM) | trades.jsonl:163,164; orders.jsonl:769,770; decisions.jsonl:2069 | open: IG activity (ig_check_result.2026-11-19_1752.json, dealId DIAAAAYVS8ND5BM); close: IG transactions |
| 22 | Wed 18 Nov 16:20:26 | Wed 18 Nov 16:58:29 | sell | B `3d50353` | trend down, strong push | 13141.1 | 13153.1 | 13041.1 | 13153.1 | -12.0 | IG stop (IG channel SYSTEM) | trades.jsonl:166,169; orders.jsonl:781,782; decisions.jsonl:2094 | open: IG activity (ig_check_result.2026-11-19_1752.json, dealId DIAAAAYVZT8VJAL); close: IG transactions |
| 23 | Thu 19 Nov 19:51:10 | Thu 19 Nov 20:16:54 | sell | C `02f6c7e` | emerging trend down | 13094.5 | 13106.5 | 13064.5 | 13102.4 | -7.9 | owner close (IG channel SYSTEM) | trades.jsonl:184,186; orders.jsonl:867,868; decisions.jsonl:2302 | open: IG activity (ig_check_result.2026-11-19_2015.json, dealId DIAAAAYV8QV4MAH); close: IG transactions |
| 24 | Fri 20 Nov 18:42:26 | Fri 20 Nov 18:43:24 | sell | C `02f6c7e` | emerging trend down | 13091.4 | 13103.4 | 13061.4 | 13092.8 | -1.4 | owner close (IG channel SYSTEM) | trades.jsonl:208,210; orders.jsonl:986,987; decisions.jsonl:2680 | open: IG activity (ig_check_result.json, dealId DIAAAAYWE2N4FBM); close: IG transactions |

* Period A: bot's own exits 12 trades, 3 won, 9 lost, -18.0 pips; owner closes none.
* Period B: bot's own exits 10 trades, 0 won, 10 lost, -120.0 pips; owner closes none.
* Period C: bot's own exits none; owner closes 2 trades, 0 won, 2 lost, -9.3 pips.
* All periods: bot's own exits 22 trades, 3 won, 19 lost, -138.0 pips; owner closes 2 trades, 0 won, 2 lost, -9.3 pips (kept apart).
* Trade 21: the bot's record says -12.6 pips at 13169.0; IG's close 13168.4 gives -12.0. IG's figure is used.

Take profit sent (IG limit minus IG fill), with the bot's `take_profit_kind` from `trades.jsonl`: 30 pips (normal) on 15 trades; 100 pips (100 for a big-news day) on 9 trades. Stop (IG fill to IG stop): 12 pips on 24 trades.

| # | Take profit pips | take_profit_kind |
|---|---|---|
| 1 | 30 | normal |
| 2 | 100 | 100 for a big-news day |
| 3 | 100 | 100 for a big-news day |
| 4 | 100 | 100 for a big-news day |
| 5 | 30 | normal |
| 6 | 30 | normal |
| 7 | 30 | normal |
| 8 | 30 | normal |
| 9 | 30 | normal |
| 10 | 100 | 100 for a big-news day |
| 11 | 100 | 100 for a big-news day |
| 12 | 100 | 100 for a big-news day |
| 13 | 30 | normal |
| 14 | 30 | normal |
| 15 | 30 | normal |
| 16 | 30 | normal |
| 17 | 30 | normal |
| 18 | 30 | normal |
| 19 | 30 | normal |
| 20 | 100 | 100 for a big-news day |
| 21 | 100 | 100 for a big-news day |
| 22 | 100 | 100 for a big-news day |
| 23 | 30 | normal |
| 24 | 30 | normal |

# Part 1. Do the five problems really happen?

## 1.1 Hourly slope direction

**The live code (period C, and period A):** the slope is taken as a size only (`abs`).

`strategies/ema_pullback/strategy.py` at `02f6c7e`, lines 65-94:

```python
  65      def at(self, t: datetime) -> HourlyTrend:
  66          done = [c for c in self.candles if c.end <= t]
  67          n = self.e.hourly_slope_candles
  68          if len(done) < n + 1:
  69              return HourlyTrend(None, False, "not enough hourly candles")
  70          now, prev, back = done[-1].start, done[-2].start, done[-1 - n].start
  71          try:
  72              f, m, s = self.f[now], self.m[now], self.sl[now]
  73              fp, mp, sp = self.f[prev], self.m[prev], self.sl[prev]
  74              fb, mb, sb = self.f[back], self.m[back], self.sl[back]
  75          except KeyError:
  76              return HourlyTrend(None, False, "hourly EMAs not ready")
  77          if f > m > s and f > fp and m > mp and s > sp:
  78              d = BUY
  79          elif f < m < s and f < fp and m < mp and s < sp:
  80              d = SELL
  81          else:
  82              return HourlyTrend(None, False, f"hourly EMAs not in order and all moving one way "
  83                                              f"(8 {plain(f.quantize(Decimal('0.1')))}, 13 {plain(m.quantize(Decimal('0.1')))}, "
  84                                              f"20 {plain(s.quantize(Decimal('0.1')))})")
  85          slopes = [abs(x - y) / n / self.ppp for x, y in ((f, fb), (m, mb), (s, sb))]
  86          gaps = (abs(f - m) / self.ppp, abs(m - s) / self.ppp)
  87          ok = (min(slopes) >= self.e.hourly_min_slope_pips_per_hour
  88                and gaps[0] >= self.e.hourly_min_gap_fast_mid_pips and gaps[1] >= self.e.hourly_min_gap_mid_slow_pips)
  89          why = (f"hourly 8/13/20 EMAs in order, {'rising' if d == BUY else 'falling'}; slopes "
  90                 + ", ".join(plain(x.quantize(Decimal('0.01'))) for x in slopes) + " pips/hour (min "
  91                 f"{self.e.hourly_min_slope_pips_per_hour}); gaps {plain(gaps[0].quantize(Decimal('0.01')))} and "
  92                 f"{plain(gaps[1].quantize(Decimal('0.01')))} pips (min {self.e.hourly_min_gap_fast_mid_pips} and "
  93                 f"{self.e.hourly_min_gap_mid_slow_pips})")
  94          return HourlyTrend(d, ok, why)
```

Period A ran the same lines (the file is identical at `f99efe1`). **Period B** ran `f69492c`'s version (13 Nov 08:43, first live at the 13 Nov 10:22 start), where the slope must point the trade's way:

`strategies/ema_pullback/strategy.py` at `f69492c`, lines 86-89:

```python
  86          # each EMA's slope over the last n hourly candles, signed in the trend's direction: AutoBot 161's rule, "the
  87          # right sign and absolute magnitude >= 0.16 pips/hour" (owner, 13 November 2026)
  88          sign = 1 if d == BUY else -1
  89          slopes = [sign * (x - y) / n / self.ppp for x, y in ((f, fb), (m, mb), (s, sb))]
```

Line 77 (both versions) already requires each hourly EMA to be higher (buy) or lower (sell) than on the hourly candle before. The `abs` on line 85 can only let through a 3-hour slope that points the other way when an EMA has turned within the last 3 hours: one hour's move the trade's way, but a net move against it over 3 hours.

**How often it happened live: on 0 of the 24 trades.** For each trade: the logged step 0 (quoted from `trades.jsonl`, the `steps` list), the hourly candles the live bot read, and the signed 3-hour slope of each hourly EMA in pips per hour (positive = up). A slope against the trade would be negative for a buy or positive for a sell.

| # | Dir | Touch candle | Logged step 0 (trades.jsonl line) | Hourly candles the bot read | 8 / 13 / 20 EMA 3-hour slope as read by the bot | True 8 / 13 / 20 slope at the touch | Any against? | Pips |
|---|---|---|---|---|---|---|---|---|
| 1 | buy | Mon 09 Nov 20:45 | `step 0, hourly 8/13/20 EMAs in order, rising; slopes 5.57, 4.58, 3.20 pips/hour (min 0.16); gaps 8.39 and 3.92 pips (min 0.25 and 0.2)` (20) | as stored at start-up: hourly candles as stored at the 09 Nov 12:26:37 start; last hourly candle Mon 09 Nov 11:00 | +5.57 / +4.58 / +3.20 | +3.43 / +3.05 / +2.56 | no | -12.0 |
| 2 | buy | Tue 10 Nov 04:50 | `step 0, hourly 8/13/20 EMAs in order, rising; slopes 5.57, 4.58, 3.20 pips/hour (min 0.16); gaps 8.39 and 3.92 pips (min 0.25 and 0.2)` (22) | as stored at start-up: hourly candles as stored at the 09 Nov 12:26:37 start; last hourly candle Mon 09 Nov 11:00 | +5.57 / +4.58 / +3.20 | +1.86 / +2.08 / +2.11 | no | -12.0 |
| 3 | buy | Tue 10 Nov 06:00 | `step 0, hourly 8/13/20 EMAs in order, rising; slopes 5.57, 4.58, 3.20 pips/hour (min 0.16); gaps 8.39 and 3.92 pips (min 0.25 and 0.2)` (23) | as stored at start-up: hourly candles as stored at the 09 Nov 12:26:37 start; last hourly candle Mon 09 Nov 11:00 | +5.57 / +4.58 / +3.20 | +1.62 / +1.86 / +1.96 | no | -12.0 |
| 4 | buy | Tue 10 Nov 07:10 | `step 0, hourly 8/13/20 EMAs in order, rising; slopes 5.57, 4.58, 3.20 pips/hour (min 0.16); gaps 8.39 and 3.92 pips (min 0.25 and 0.2)` (24) | as stored at start-up: hourly candles as stored at the 09 Nov 12:26:37 start; last hourly candle Mon 09 Nov 11:00 | +5.57 / +4.58 / +3.20 | +1.60 / +1.81 / +1.91 | no | -12.0 |
| 5 | sell | Wed 11 Nov 07:25 | `step 0, hourly 8/13/20 EMAs in order, falling; slopes 0.67, 1.35, 1.89 pips/hour (min 0.16); gaps 5.17 and 9.32 pips (min 0.25 and 0.2)` (58) | as stored at start-up: hourly candles as stored at the 11 Nov 06:47:15 start; last hourly candle Wed 11 Nov 05:00 | -0.67 / -1.35 / -1.89 | -1.12 / -1.54 / -1.97 | no | +30.0 |
| 6 | sell | Wed 11 Nov 08:00 | `step 0, hourly 8/13/20 EMAs in order, falling; slopes 0.67, 1.35, 1.89 pips/hour (min 0.16); gaps 5.17 and 9.32 pips (min 0.25 and 0.2)` (61) | as stored at start-up: hourly candles as stored at the 11 Nov 06:47:15 start; last hourly candle Wed 11 Nov 05:00 | -0.67 / -1.35 / -1.89 | -2.28 / -2.23 / -2.38 | no | +30.0 |
| 7 | sell | Wed 11 Nov 10:40 | `step 0, hourly 8/13/20 EMAs in order, falling; slopes 2.28, 2.23, 2.38 pips/hour (min 0.16); gaps 5.74 and 9.29 pips (min 0.25 and 0.2)` (66) | as stored at start-up: hourly candles as stored at the 11 Nov 08:34:18 start; last hourly candle Wed 11 Nov 07:00 | -2.28 / -2.23 / -2.38 | -3.49 / -3.07 / -2.94 | no | +30.0 |
| 8 | sell | Wed 11 Nov 18:40 | `step 0, hourly 8/13/20 EMAs in order, falling; slopes 4.73, 4.72, 4.41 pips/hour (min 0.16); gaps 11.69 and 13.78 pips (min 0.25 and 0.2)` (81) | fresh; last hourly candle Wed 11 Nov 17:00 | -4.73 / -4.72 / -4.41 | -4.73 / -4.72 / -4.41 | no | -12.0 |
| 9 | sell | Wed 11 Nov 20:50 | `step 0, hourly 8/13/20 EMAs in order, falling; slopes 3.37, 3.81, 3.85 pips/hour (min 0.16); gaps 10.40 and 13.44 pips (min 0.25 and 0.2)` (83) | fresh; last hourly candle Wed 11 Nov 19:00 | -3.37 / -3.81 / -3.85 | -3.37 / -3.81 / -3.85 | no | -12.0 |
| 10 | sell | Thu 12 Nov 18:45 | `step 0, hourly 8/13/20 EMAs in order, falling; slopes 5.50, 4.12, 3.34 pips/hour (min 0.16); gaps 6.77 and 7.81 pips (min 0.25 and 0.2)` (95) | fresh; last hourly candle Thu 12 Nov 17:00 | -5.50 / -4.12 / -3.34 | -5.50 / -4.12 / -3.34 | no | -12.0 |
| 11 | sell | Thu 12 Nov 21:55 | `step 0, hourly 8/13/20 EMAs in order, falling; slopes 2.14, 2.36, 2.34 pips/hour (min 0.16); gaps 6.09 and 7.87 pips (min 0.25 and 0.2)` (97) | fresh; last hourly candle Thu 12 Nov 20:00 | -2.14 / -2.36 / -2.34 | -2.14 / -2.36 / -2.34 | no | -12.0 |
| 12 | sell | Thu 12 Nov 23:35 | `step 0, hourly 8/13/20 EMAs in order, falling; slopes 1.66, 1.97, 2.08 pips/hour (min 0.16); gaps 5.83 and 7.84 pips (min 0.25 and 0.2)` (99) | fresh; last hourly candle Thu 12 Nov 22:00 | -1.66 / -1.97 / -2.08 | -1.66 / -1.97 / -2.08 | no | -12.0 |
| 13 | sell | Fri 13 Nov 10:10 | `step 0, hourly 8/13/20 EMAs in order, falling; slopes 0.29, 0.49, 0.78 pips/hour (min 0.16); gaps 1.69 and 4.14 pips (min 0.25 and 0.2)` (105) | fresh; last hourly candle Fri 13 Nov 09:00 | -0.28 / -0.49 / -0.78 | -0.28 / -0.49 / -0.78 | no | -12.0 |
| 14 | sell | Mon 16 Nov 10:35 | `step 0, hourly 8/13/20 EMAs in order, falling; slopes 0.91, 0.92, 0.96 pips/hour (min 0.16); gaps 2.78 and 3.82 pips (min 0.25 and 0.2)` (117) | fresh; last hourly candle Mon 16 Nov 09:00 | -0.91 / -0.92 / -0.96 | -0.91 / -0.92 / -0.96 | no | -12.0 |
| 15 | sell | Mon 16 Nov 14:20 | `step 0, hourly 8/13/20 EMAs in order, falling; slopes 0.40, 0.76, 0.92 pips/hour (min 0.16); gaps 2.70 and 3.95 pips (min 0.25 and 0.2)` (122) | fresh; last hourly candle Mon 16 Nov 13:00 | -0.40 / -0.76 / -0.92 | -0.40 / -0.76 / -0.92 | no | -12.0 |
| 16 | sell | Mon 16 Nov 14:40 | `step 0, hourly 8/13/20 EMAs in order, falling; slopes 0.40, 0.76, 0.92 pips/hour (min 0.16); gaps 2.70 and 3.95 pips (min 0.25 and 0.2)` (123) | fresh; last hourly candle Mon 16 Nov 13:00 | -0.40 / -0.76 / -0.92 | -0.40 / -0.76 / -0.92 | no | -12.0 |
| 17 | sell | Mon 16 Nov 15:35 | `step 0, hourly 8/13/20 EMAs in order, falling; slopes 0.98, 1.08, 1.12 pips/hour (min 0.16); gaps 3.39 and 4.35 pips (min 0.25 and 0.2)` (126) | fresh; last hourly candle Mon 16 Nov 14:00 | -0.98 / -1.08 / -1.12 | -0.98 / -1.08 / -1.12 | no | -12.0 |
| 18 | sell | Mon 16 Nov 16:35 | `step 0, hourly 8/13/20 EMAs in order, falling; slopes 1.77, 1.57, 1.44 pips/hour (min 0.16); gaps 3.67 and 4.56 pips (min 0.25 and 0.2)` (128) | fresh; last hourly candle Mon 16 Nov 15:00 | -1.77 / -1.57 / -1.44 | -1.77 / -1.57 / -1.44 | no | -12.0 |
| 19 | sell | Mon 16 Nov 19:50 | `step 0, hourly 8/13/20 EMAs in order, falling; slopes 1.17, 1.27, 1.28 pips/hour (min 0.16); gaps 3.37 and 4.51 pips (min 0.25 and 0.2)` (132) | fresh; last hourly candle Mon 16 Nov 18:00 | -1.17 / -1.27 / -1.28 | -1.17 / -1.27 / -1.28 | no | -12.0 |
| 20 | buy | Tue 17 Nov 17:00 | `step 0, hourly 8/13/20 EMAs in order, rising; slopes 2.66, 1.80, 1.18 pips/hour (min 0.16); gaps 2.86 and 1.34 pips (min 0.25 and 0.2)` (152) | fresh; last hourly candle Tue 17 Nov 16:00 | +2.66 / +1.80 / +1.18 | +2.66 / +1.80 / +1.18 | no | -12.0 |
| 21 | sell | Wed 18 Nov 12:30 | `step 0, hourly 8/13/20 EMAs in order, falling; slopes 2.99, 2.76, 2.21 pips/hour (min 0.16); gaps 6.60 and 5.05 pips (min 0.25 and 0.2)` (163) | fresh; last hourly candle Wed 18 Nov 11:00 | -2.99 / -2.77 / -2.21 | -2.99 / -2.77 / -2.21 | no | -12.0 |
| 22 | sell | Wed 18 Nov 16:15 | `step 0, hourly 8/13/20 EMAs in order, falling; slopes 2.44, 2.48, 2.19 pips/hour (min 0.16); gaps 6.64 and 6.40 pips (min 0.25 and 0.2)` (166) | fresh; last hourly candle Wed 18 Nov 15:00 | -2.44 / -2.48 / -2.19 | -2.44 / -2.48 / -2.19 | no | -12.0 |
| 23 | sell | Thu 19 Nov 19:35 | `step 0, hourly 8/13/20 EMAs in order, falling; slopes 6.55, 4.81, 3.58 pips/hour (min 0.16); gaps 7.27 and 6.26 pips (min 0.25 and 0.2)` (184) | fresh; last hourly candle Thu 19 Nov 18:00 | -6.55 / -4.81 / -3.58 | -6.55 / -4.81 / -3.58 | no | -7.9 (owner) |
| 24 | sell | Fri 20 Nov 18:30 | `step 0, hourly 8/13/20 EMAs in order, falling; slopes 1.01, 0.60, 0.57 pips/hour (min 0.16); gaps 0.38 and 1.88 pips (min 0.25 and 0.2)` (208) | fresh; last hourly candle Fri 20 Nov 17:00 | -1.01 / -0.59 / -0.57 | -1.01 / -0.59 / -0.57 | no | -1.4 (owner) |

Trades judged on hourly candles as stored at the service's start (before 11 Nov 14:56): 7 (trades 1, 2, 3, 4, 5, 6, 7). Trades 2-4 on 10 Nov used the hourly candle of Mon 09 Nov 11:00.

Check on the method: the step 0 text worked out with the bot's own `HourlyTrendReader` from the stored hourly candles (as read at the time: as stored at start-up before 11 Nov 14:56, fresh after) is character-for-character the logged text on all 24 trades.

**Setups (traded or not):** of the 483 setups worked out from the candles (Part 2.2), 4 had a 3-hour slope against the setup's direction. None reached its entry price, so none could trade:

| Touch | Dir | Slopes 8 / 13 / 20 (pips/hour) | Against | Commit at touch | Slope check in that code | What happened |
|---|---|---|---|---|---|---|
| Fri 20 Nov 09:10 | sell | +1.23 / +0.53 / -0.18 | 8,13 | `02f6c7e` | size only (abs) | expired: `setup from 09:10 GMT: expired, 13095.4 not reached within 20 minutes` |
| Fri 20 Nov 09:20 | sell | +1.23 / +0.53 / -0.18 | 8,13 | `02f6c7e` | size only (abs) | cancelled: `setup from 09:20 GMT: closed 13106.9 above the 21 EMA 13105.9: cancelled` |
| Fri 20 Nov 09:25 | sell | +1.23 / +0.53 / -0.18 | 8,13 | `02f6c7e` | size only (abs) | cancelled: `setup from 09:25 GMT: closed 13106.9 above the 21 EMA 13105.9: cancelled` |
| Fri 20 Nov 09:30 | sell | +1.23 / +0.53 / -0.18 | 8,13 | `02f6c7e` | size only (abs) | cancelled: `setup from 09:30 GMT: closed 13106.9 above the 21 EMA 13105.9: cancelled` |

## 1.2 Several trades at once

**The live code.** Every touch starts its own setup, so several can run at once:

`strategies/ema_pullback/strategy.py` at `02f6c7e`, lines 146-166:

```python
 146          # 1. a touch candle (0. with the hourly trend)
 147          if self.prev_fast is not None and slow is not None and len(self.done) >= self.e.entry_lookback_candles:
 148              trend = self.hourly.at(c.start)
 149              for d in (BUY, SELL):
 150                  buy = d == BUY
 151                  if not (self._l(c) <= self.prev_fast if buy else self._h(c) >= self.prev_fast):
 152                      continue
 153                  if trend.direction != d or not trend.qualified:
 154                      if trend.direction == d:
 155                          self.notes.append((c.start, d, f"touched the 8 EMA {q(self.prev_fast)}; the hourly trend "
 156                                                         f"is not qualified ({trend.why})"))
 157                      continue
 158                  if (self._c(c) < slow) if buy else (self._c(c) > slow):
 159                      self.notes.append((c.start, d, f"touched the 8 EMA {q(self.prev_fast)}; the touch candle closed "
 160                                                     f"{q(self._c(c))} {'below' if buy else 'above'} the "
 161                                                     f"{self.e.slow_ema_periods} EMA {q(slow)}: cancelled"))
 162                      continue
 163                  before = self.done[-self.e.entry_lookback_candles:]
 164                  beyond = Decimal(self.e.entry_beyond_pips) * self.ppp
 165                  entry = (max(self._h(x) for x in before) + beyond) if buy else (min(self._l(x) for x in before) - beyond)
 166                  self.setups.append(_Setup(d, c, entry, [
```

The per-strategy limit is skipped for the EMA pullback:

`safety/rules.py` at `02f6c7e`, lines 110-113:

```python
 110  def _limits(settings: Any, order: Order, open_trades: list[OpenTrade]) -> list[str]:
 111      lim, idea = settings.limits, order.idea
 112      out = []
 113      if idea.strategy != EMA_PULLBACK:
```

and its trades are not counted towards the most at once (5):

`strategies/common.py` at `02f6c7e`, lines 306-308:

```python
 306  def counts_towards_most_at_once(strategy: str) -> bool:
 307      """Section 6: "most at once: 5" counts every open trade except the EMA pullback's."""
 308      return strategy != EMA_PULLBACK
```

Nothing else limits how many EMA pullback trades are open at once. The engine sends at most one idea per strategy, direction and 5-minute candle:

`trading/engine.py` at `02f6c7e`, lines 450-453:

```python
 450              key = (idea.strategy, idea.direction, p.start)
 451              if not idea.allowed or key in self.fired:
 452                  continue
 453              self.fired.add(key)
```

**How often it happened live: 4 times, involving 13 of the 24 trades.** Each group is a run of trades whose open times overlapped:

| Group | Trade # | Dir | Opened | Closed | Period / commit | Pips | Closed by | Most open at once in the group |
|---|---|---|---|---|---|---|---|---|
| 1 | 2 | buy | Tue 10 Nov 05:01:31 | Tue 10 Nov 09:00:12 | A `2ff445f` | -12.0 | IG stop | 3 |
| 1 | 3 | buy | Tue 10 Nov 06:12:03 | Tue 10 Nov 09:00:11 | A `2ff445f` | -12.0 | IG stop | 3 |
| 1 | 4 | buy | Tue 10 Nov 07:21:03 | Tue 10 Nov 09:00:08 | A `2ff445f` | -12.0 | IG stop | 3 |
| 1 | total | | | | | -36.0 | | |
| 2 | 5 | sell | Wed 11 Nov 07:32:27 | Wed 11 Nov 13:20:33 | A `dfa9075` | +30.0 | IG take profit | 3 |
| 2 | 6 | sell | Wed 11 Nov 08:16:26 | Wed 11 Nov 13:51:00 | A `dfa9075` | +30.0 | IG take profit | 3 |
| 2 | 7 | sell | Wed 11 Nov 10:51:37 | Wed 11 Nov 13:56:51 | A `03be0aa` | +30.0 | IG take profit | 3 |
| 2 | total | | | | | +90.0 | | |
| 3 | 8 | sell | Wed 11 Nov 18:48:20 | Wed 11 Nov 22:03:08 | A `9467e19` | -12.0 | IG stop | 2 |
| 3 | 9 | sell | Wed 11 Nov 21:06:02 | Wed 11 Nov 22:00:00 | A `9467e19` | -12.0 | IG stop | 2 |
| 3 | total | | | | | -24.0 | | |
| 4 | 15 | sell | Mon 16 Nov 14:26:00 | Tue 17 Nov 09:48:55 | B `9b61661` | -12.0 | IG stop | 2 |
| 4 | 16 | sell | Mon 16 Nov 14:57:56 | Mon 16 Nov 15:16:57 | B `9b61661` | -12.0 | IG stop | 2 |
| 4 | 17 | sell | Mon 16 Nov 15:50:42 | Mon 16 Nov 16:09:45 | B `9b61661` | -12.0 | IG stop | 2 |
| 4 | 18 | sell | Mon 16 Nov 16:53:48 | Mon 16 Nov 17:11:19 | B `9b61661` | -12.0 | IG stop | 2 |
| 4 | 19 | sell | Mon 16 Nov 20:00:03 | Mon 16 Nov 22:04:53 | B `9b61661` | -12.0 | IG stop | 2 |
| 4 | total | | | | | -60.0 | | |

All the trades in each group went the same way. The 14 allowed setups that reached their entry in the same candle as a trade and were not sent (Part 2.2) are the engine's one-per-candle rule at work; they are not in this table.

## 1.3 Big news

**The live code.** For the EMA pullback, `may_open` returns before the news check, so big-news windows do not stop it opening:

`strategies/common.py` at `02f6c7e`, lines 170-179:

```python
 170      if strategy == EMA_PULLBACK:
 171          lt = t.astimezone(ZoneInfo(tz) if isinstance(tz, str) else tz)
 172          if lt.weekday() == 4 and lt.time() >= settings.hours.close_all_trades_at:
 173              reasons.append(f"after {settings.hours.close_all_trades_at:%H:%M} UK on Friday: "
 174                             f"no {strategy} trade is held over the weekend")
 175          ep = settings.ema_pullback
 176          if ep.rollover_no_new_trades_from <= lt.time() < ep.rollover_no_new_trades_until:
 177              reasons.append(f"from {ep.rollover_no_new_trades_from:%H:%M} to {ep.rollover_no_new_trades_until:%H:%M} UK "
 178                             f"(the rollover): no new {strategy} trade")
 179          return reasons
```

and its open trades are not closed before big news:

`strategies/common.py` at `02f6c7e`, lines 247-250:

```python
 247  def closed_before_big_news(strategy: str) -> bool:
 248      """Open trades are closed 15 minutes before big news, except the EMA pullback's, the breakout's
 249      and the slow grind's."""
 250      return strategy not in NEWS_ALLOWED
```

`strategies/common.py` at `02f6c7e`, lines 61-62:

```python
  61  # May open in a big-news window and not closed before big news (owner, 7 and 8 November 2026).
  62  NEWS_ALLOWED = (EMA_PULLBACK, BREAKOUT, SLOW_GRIND)
```

Big releases are taken from the bot's own news table (`config/news_table.toml`, unchanged since `f99efe1`) applied with the bot's own `news.calendar.big_news_windows` to its stored calendar `data/news/calendar.json` (it covers 31 Oct onwards). The big releases for GBP or USD in the period:

| Release (UK) | Events |
|---|---|
| Tue 10 Nov 13:30 | USD Core Inflation Rate MoM; USD Core Inflation Rate YoY; USD Inflation Rate MoM; USD Inflation Rate YoY |
| Thu 12 Nov 07:00 | GBP GDP Growth Rate QoQ Prel; GBP GDP Growth Rate YoY Prel |
| Tue 17 Nov 07:00 | GBP Unemployment Rate |
| Wed 18 Nov 07:00 | GBP Core Inflation Rate MoM; GBP Inflation Rate YoY |
| Wed 18 Nov 19:00 | USD FOMC Minutes |

**Opened from 15 minutes before to 30 minutes after a big release: 0 trades.**

**Still open when a big release came out: 1 trade.**

| # | Dir | Opened | Closed | Release(s) while open | Pips | Closed by | Commit |
|---|---|---|---|---|---|---|---|
| 15 | sell | Mon 16 Nov 14:26:00 | Tue 17 Nov 09:48:55 | GBP Unemployment Rate Tue 17 Nov 07:00 | -12.0 | IG stop | `9b61661` |

One trade is too few to say anything about how the strategy behaves around big news.

## 1.4 Hours and overnight

**The live code.** The only hours the EMA pullback keeps are: none after 20:30 UK on Friday, and (from `d96de5f`, 13 Nov 10:22, and in `02f6c7e`) none from 21:55 to 22:15 UK. The same `may_open` lines as in 1.3. It is held overnight and closed only at 20:30 UK on Friday:

`strategies/common.py` at `02f6c7e`, lines 58-60:

```python
  58  # Held overnight and closed at 20:30 UK on Friday only (owner, 7 November 2026); every other
  59  # strategy is closed at 20:30 UK every day.
  60  OWN_HOURS = (EMA_PULLBACK, BREAKOUT)
```

`strategies/common.py` at `02f6c7e`, lines 196-211:

```python
 196  def forced_close_at(settings: Any, strategy: str, opened: datetime) -> datetime:
 197      """When a trade opened at `opened` is closed by the clock: hours.close_all_trades_at (20:30) UK,
 198      the first one after it opened; for the EMA pullback and the breakout, the first FRIDAY 20:30 UK
 199      after it opened. (A slow grind trade never opens between 20:30 and midnight UK, so it is
 200      always closed at 20:30 the day it opened.)"""
 201      from datetime import datetime as dt, timedelta, timezone
 202      from zoneinfo import ZoneInfo
 203      tz = settings.hours.timezone
 204      uk = ZoneInfo(tz) if isinstance(tz, str) else tz
 205      lt = opened.astimezone(uk)
 206      for k in range(0, 8):
 207          day = lt.date() + timedelta(days=k)
 208          cut = dt.combine(day, settings.hours.close_all_trades_at, tzinfo=uk)
 209          if cut > lt and (strategy not in OWN_HOURS or day.weekday() == 4):
 210              return cut.astimezone(timezone.utc)
 211      raise AssertionError("no close found within a week")
```

Period A (before `d96de5f`) had no rollover window: `f99efe1`'s `may_open` EMA branch only has the Friday rule.

`strategies/common.py` at `f99efe1`, lines 144-149:

```python
 144      if strategy == EMA_PULLBACK:
 145          lt = t.astimezone(ZoneInfo(tz) if isinstance(tz, str) else tz)
 146          if lt.weekday() == 4 and lt.time() >= settings.hours.close_all_trades_at:
 147              reasons.append(f"after {settings.hours.close_all_trades_at:%H:%M} UK on Friday: "
 148                             f"no {strategy} trade is held over the weekend")
 149          return reasons
```

**Opened outside 06:00-20:30 UK: 5 trades.**

| # | Dir | Opened | Closed | Pips | Closed by | Period / commit | Spread (buy minus sell, from the stored 5-minute candles) in the candle it closed |
|---|---|---|---|---|---|---|---|
| 1 | buy | Mon 09 Nov 21:02:06 | Mon 09 Nov 22:00:00 | -12.0 | IG stop | A `2ff445f` | 7.3 at the 22:00 candle's open, 16.9 at its close |
| 2 | buy | Tue 10 Nov 05:01:31 | Tue 10 Nov 09:00:12 | -12.0 | IG stop | A `2ff445f` | 1.5 at the 09:00 candle's open, 1.5 at its close |
| 9 | sell | Wed 11 Nov 21:06:02 | Wed 11 Nov 22:00:00 | -12.0 | IG stop | A `9467e19` | 12.6 at the 22:00 candle's open, 16.9 at its close |
| 11 | sell | Thu 12 Nov 22:00:03 | Thu 12 Nov 22:00:03 | -12.0 | IG stop | A `79c5dcf` | 16.7 at the 22:00 candle's open, 16.9 at its close |
| 12 | sell | Thu 12 Nov 23:47:19 | Fri 13 Nov 01:41:27 | -12.0 | IG stop | A `79c5dcf` | 1.5 at the 01:40 candle's open, 1.5 at its close |

**Held past 20:30 UK: 3 trades.**

| # | Dir | Opened | Closed | 20:30 passed | Pips | Closed by | Period / commit | Spread in the candle it closed |
|---|---|---|---|---|---|---|---|---|
| 8 | sell | Wed 11 Nov 18:48:20 | Wed 11 Nov 22:03:08 | Wed 11 Nov 20:30 | -12.0 | IG stop | A `9467e19` | 12.6 at the 22:00 candle's open, 16.9 at its close |
| 15 | sell | Mon 16 Nov 14:26:00 | Tue 17 Nov 09:48:55 | Mon 16 Nov 20:30 | -12.0 | IG stop | B `9b61661` | 1.5 at the 09:45 candle's open, 1.5 at its close |
| 19 | sell | Mon 16 Nov 20:00:03 | Mon 16 Nov 22:04:53 | Mon 16 Nov 20:30 | -12.0 | IG stop | B `9b61661` | 7.3 at the 22:00 candle's open, 16.9 at its close |

Trade 11 opened at the 22:00 rollover. Its last step, quoted from `trades.jsonl` line 97: `reached on the live price at 22:00:00 UTC (bid 13230.7, offer 13247.6)` (offer minus bid 16.9). IG shows the stop filled at 13242.7 at Thu 12 Nov 22:00:03, the same second it opened. This was before the 21:55-22:15 window was added (`d96de5f`, 13 Nov).

Closes between 21:55 and 22:15: trade 1 at 22:00:00 (-12.0), trade 8 at 22:03:08 (-12.0), trade 9 at 22:00:00 (-12.0), trade 11 at 22:00:03 (-12.0), trade 19 at 22:04:53 (-12.0).

## 1.5 Slippage and stale prices

**The live code.** When a live price reaches the entry, the engine sends the order at once:

`trading/engine.py` at `02f6c7e`, lines 444-464:

```python
 444      def _live_entries(self, tick: Any) -> None:
 445          import dataclasses
 446          p = self._forming(tick)
 447          if self._levels is None or self._levels[0] != p.start:
 448              self._levels = (p.start, build(self.s, MemoStore(self.store), p.start))
 449          for idea in self.runner.peek(p, self._levels[1]):
 450              key = (idea.strategy, idea.direction, p.start)
 451              if not idea.allowed or key in self.fired:
 452                  continue
 453              self.fired.add(key)
 454              idea = dataclasses.replace(idea, time=tick.time)
 455              idea.steps.append(f"reached on the live price at {tick.time.strftime('%H:%M:%S')} UTC "
 456                                f"(bid {tick.sell}, offer {tick.buy})")
 457              self.book.decision("idea", tick.time, strategy=idea.strategy, direction=idea.direction,
 458                                 entry_price=idea.entry_price, allowed=True, blocked_by="", state=idea.state, live=True)
 459              td = self._trend_day(idea.time)
 460              r = self._place(idea, td)
 461              if not r.ok:
 462                  continue
 463              self._opened(idea, r, tick.time, td)
 464              log.info("Live entry: %s %s at %s (entry price %s).", idea.strategy, idea.direction, r.level, idea.entry_price)
```

and the order is a market order with no price or quote attached (the stop and limit are distances from IG's fill):

`orders/sender.py` at `02f6c7e`, lines 521-535:

```python
 521              body = {                                                # exactly AutoBot 161's 17 fields
 522                  "currencyCode": self.o.currency,
 523                  "direction": idea.direction.upper(),
 524                  "epic": self.epic,
 525                  "expiry": self.o.expiry,
 526                  "forceOpen": True,                                  # always
 527                  "guaranteedStop": False,
 528                  "level": None,
 529                  "limitDistance": float(Decimal(tp) * self.ppp),
 530                  "limitLevel": None,
 531                  "orderType": "MARKET",
 532                  "quoteId": None,
 533                  "size": float(order.size_gbp_per_pip / self.ppp),
 534                  "stopDistance": float(stop_points),                 # always a distance, never stopLevel
 535                  "stopLevel": None,
```

Nothing in `trading/engine.py`, `orders/sender.py`, `safety/rules.py` or `strategies/common.py` compares the price's age or the fill with the entry (no match for `slippage`, `stale`, `max_age` or any age check on the tick).

**What the records hold.** The setup's entry (step `entry ...` in `trades.jsonl`); the price the idea gave (`entry_price`; it differs from the setup's entry only when the candle opened past it); the live bid and offer when the entry was reached and that price's time, which is IG's own time stamp on the price (`UTM`, `prices/feed.py`), written to the second (last step in `trades.jsonl`); the time the order went out (`sending`, `orders.jsonl`, to the second); IG's fill and open time (IG activity). The age column is the sending time minus IG's time on the price, in whole seconds (both are cut to the second, so each is +/- 1 s).

The gap is in the trade's disfavour when positive: a buy's fill above the entry, a sell's fill below it. The chart (and the entry) is the sell (bid) price, so a buy's gap includes the spread. The last column takes the spread out: the fill against the same side of the live price that reached the entry (a buy's offer, a sell's bid).

| # | Dir | Setup entry | Idea price | Live bid / offer at the entry (IG time) | IG fill | Gap vs setup entry (pips) | Gap vs same-side live price (pips) | Price age when sent (s) | IG open time minus price time (s) | Pips | Closed by | Commit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | buy | 13449.2 | 13449.2 | 13449.7 / 13451.2 (10 Nov 05:01:31) | 13451.0 | +1.8 | -0.2 | 0 | 0 | -12.0 | IG stop | `2ff445f` |
| 20 | buy | 13223.3 | 13223.3 | 13223.6 / 13225.1 (17 Nov 17:16:00) | 13225.1 | +1.8 | +0.0 | 1 | 1 | -12.0 | IG stop | `aea2275` |
| 3 | buy | 13451.1 | 13451.1 | 13451.3 / 13452.8 (10 Nov 06:12:03) | 13452.8 | +1.7 | +0.0 | 0 | 0 | -12.0 | IG stop | `2ff445f` |
| 4 | buy | 13454.5 | 13454.5 | 13454.5 / 13456.0 (10 Nov 07:21:03) | 13456.1 | +1.6 | +0.1 | 0 | 0 | -12.0 | IG stop | `2ff445f` |
| 9 | sell | 13271.9 | 13271.9 | 13271.3 / 13272.8 (11 Nov 21:06:01) | 13270.7 | +1.2 | +0.6 | 0 | 1 | -12.0 | IG stop | `9467e19` |
| 1 | buy | 13442.7 | 13442.7 | 13442.7 / 13443.6 (09 Nov 21:02:06) | 13443.6 | +0.9 | +0.0 | 0 | 0 | -12.0 | IG stop | `2ff445f` |
| 24 | sell | 13092.3 | 13092.3 | 13092.3 / 13093.8 (20 Nov 18:42:26) | 13091.4 | +0.9 | +0.9 | 0 | 0 | -1.4 | owner close | `02f6c7e` |
| 11 | sell | 13231.3 | 13230.7 | 13230.7 / 13247.6 (12 Nov 22:00:00) | 13230.7 | +0.6 | +0.0 | 3 | 3 | -12.0 | IG stop | `79c5dcf` |
| 7 | sell | 13317.4 | 13317.4 | 13317.0 / 13318.5 (11 Nov 10:51:36) | 13317.0 | +0.4 | +0.0 | 1 | 1 | +30.0 | IG take profit | `03be0aa` |
| 12 | sell | 13229.6 | 13229.6 | 13229.2 / 13230.7 (12 Nov 23:47:19) | 13229.2 | +0.4 | +0.0 | 0 | 0 | -12.0 | IG stop | `79c5dcf` |
| 23 | sell | 13094.8 | 13094.8 | 13094.8 / 13096.3 (19 Nov 19:51:09) | 13094.5 | +0.3 | +0.3 | 1 | 1 | -7.9 | owner close | `02f6c7e` |
| 10 | sell | 13225.7 | 13225.7 | 13225.7 / 13227.2 (12 Nov 19:02:16) | 13225.6 | +0.1 | +0.1 | 1 | 1 | -12.0 | IG stop | `79c5dcf` |
| 13 | sell | 13225.2 | 13225.2 | 13225.0 / 13226.5 (13 Nov 10:28:45) | 13225.1 | +0.1 | -0.1 | 2 | 2 | -12.0 | IG stop | `d96de5f` |
| 18 | sell | 13182.6 | 13182.6 | 13182.5 / 13184.0 (16 Nov 16:53:48) | 13182.5 | +0.1 | +0.0 | 0 | 0 | -12.0 | IG stop | `9b61661` |
| 5 | sell | 13330.9 | 13330.9 | 13330.9 / 13332.4 (11 Nov 07:32:27) | 13330.9 | +0.0 | +0.0 | 0 | 0 | +30.0 | IG take profit | `dfa9075` |
| 6 | sell | 13323.1 | 13323.1 | 13323.1 / 13324.6 (11 Nov 08:16:25) | 13323.1 | +0.0 | +0.0 | 1 | 1 | +30.0 | IG take profit | `dfa9075` |
| 8 | sell | 13273.5 | 13273.5 | 13273.5 / 13275.0 (11 Nov 18:48:20) | 13273.5 | +0.0 | +0.0 | 0 | 0 | -12.0 | IG stop | `9467e19` |
| 15 | sell | 13192.1 | 13192.1 | 13192.1 / 13193.6 (16 Nov 14:26:00) | 13192.1 | +0.0 | +0.0 | 0 | 0 | -12.0 | IG stop | `9b61661` |
| 19 | sell | 13184.7 | 13184.7 | 13184.7 / 13186.2 (16 Nov 20:00:03) | 13184.7 | +0.0 | +0.0 | 0 | 0 | -12.0 | IG stop | `9b61661` |
| 17 | sell | 13183.1 | 13183.1 | 13183.1 / 13184.6 (16 Nov 15:50:41) | 13183.2 | -0.1 | -0.1 | 1 | 1 | -12.0 | IG stop | `9b61661` |
| 16 | sell | 13187.1 | 13187.1 | 13187.1 / 13188.6 (16 Nov 14:57:56) | 13187.3 | -0.2 | -0.2 | 0 | 0 | -12.0 | IG stop | `9b61661` |
| 21 | sell | 13156.2 | 13156.2 | 13156.2 / 13157.7 (18 Nov 12:37:37) | 13156.4 | -0.2 | -0.2 | 0 | 0 | -12.0 | IG stop | `cc70dc5` |
| 14 | sell | 13186.8 | 13186.8 | 13186.8 / 13188.3 (16 Nov 10:50:10) | 13187.1 | -0.3 | -0.3 | 0 | 0 | -12.0 | IG stop | `9b61661` |
| 22 | sell | 13140.8 | 13140.8 | 13140.7 / 13142.2 (18 Nov 16:20:25) | 13141.1 | -0.3 | -0.4 | 1 | 1 | -12.0 | IG stop | `3d50353` |

Gap vs the setup's entry: largest +1.8, smallest -0.3. Gap vs the same-side live price: largest +0.9, smallest -0.4. Price age when sent: 0 to 3 s.

# Part 2. How well does the direction rule work?

## 2.1 The live code

Which states allow the EMA pullback, and only in the trend's direction:

`strategies/common.py` at `02f6c7e`, lines 70-72:

```python
  70  ALLOWED_IN = {
  71      SLOW_GRIND: {TREND: "trend"},                      # trend only (owner, 8 November 2026)
  72      EMA_PULLBACK: {EMERGING: "trend", TREND: "trend"},
```

The check (state, then the direction rule; the EMA pullback is not in `NO_DIRECTION_RULE`):

`strategies/common.py` at `02f6c7e`, lines 348-372:

```python
 348  def allowed(settings: Any, strategy: str, direction: str, price: Decimal, state: Any, pivot: Decimal | None,
 349              ema100: Decimal | None, t: datetime | None = None) -> tuple[list[str], Any]:
 350      """Every reason the switch, the state (2.2) or the direction rule (2.3) does not allow
 351      this strategy in this direction at this price (empty: allowed), and the direction rule."""
 352      rule = decide(price, "the price", pivot, ema100, "5m 100 EMA", ema100 is not None)
 353      reasons = []
 354      if not getattr(settings.switches, SWITCH[strategy]):
 355          reasons.append(f"its switch STRATEGY_{SWITCH[strategy].upper()} is off")
 356      ok_in = ALLOWED_IN[strategy]
 357      if strategy in WITHOUT_HINDRANCE:
 358          pass                                            # not checked against the state (owner, 15 and 16 November 2026)
 359      elif state.state not in ok_in:
 360          reasons.append(f"the analyser's state is {state.state}, which does not allow {strategy}")
 361      elif ok_in[state.state] in ("trend", "against"):
 362          want = SELL if state.direction == DOWN else BUY if state.direction == UP else None
 363          if ok_in[state.state] == "against":
 364              want = {SELL: BUY, BUY: SELL}.get(want)
 365          if direction != want:
 366              how = "in" if ok_in[state.state] == "trend" else "against"
 367              reasons.append(f"the {state.state} is {state.direction}: {strategy} only {how} the trend's direction")
 368      need = BUY_SIDE if direction == BUY else SELL_SIDE
 369      if rule.side != need and strategy not in NO_DIRECTION_RULE:
 370          reasons.append(f"the direction rule says {rule.side} ({rule.reason})")
 371      reasons += bounce_reasons(settings, strategy, t)
 372      return reasons, rule
```

The direction rule itself (pivot and 5-minute 100 EMA must agree):

`analyser/direction.py` at `02f6c7e`, lines 50-66:

```python
  50  def decide(price: Decimal | None, price_from: str, pivot: Decimal | None, ema: Decimal | None,
  51             ema_name: str, ema_ready: bool) -> Direction:
  52      def d(side: str, reason: str) -> Direction:
  53          return Direction(side, price, price_from, pivot, ema, ema_name, ema_ready, reason)
  54      if price is None:
  55          return d(NONE, "no price yet")
  56      if pivot is None:
  57          return d(NONE, "no daily pivot (the previous day's daily candle is not stored)")
  58      if ema is None:
  59          return d(NONE, f"no {ema_name} yet")
  60      p, e = _where(price, pivot), _where(price, ema)
  61      said = f"price {price} is {p} the pivot {pivot} and {e} the {ema_name} {ema.quantize(Decimal('0.1'))}"
  62      if p == e == "above":
  63          return d(BUY_SIDE, said)
  64      if p == e == "below":
  65          return d(SELL_SIDE, said)
  66      return d(NONE, said + ": they disagree" if "exactly on" not in (p, e) else said)
```

The price used is the idea's entry price; the pivot is the day's pivot as at the candle in which the entry was reached; the 100 EMA is the one at the candle before it (`strategies/replay.py`):

`strategies/replay.py` at `02f6c7e`, lines 214-218:

```python
 214              if cands:
 215                  st = self.state_after(i - 1)
 216                  e100 = ema100.get(self.week[i - 1].start) if i > 0 else None
 217                  for cand in cands:
 218                      out.append((c, check(s, s.market.pair, cand, st, self.pivot_at(c.start), e100)))
```

`NO_DIRECTION_RULE` (EMA pullback not listed):

`strategies/common.py` at `02f6c7e`, lines 66-66:

```python
  66  NO_DIRECTION_RULE = (RANGE_TRADE, BOLLINGER_BOUNCE, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL, BOLLINGER_BOUNCE_5M) + SESSION_STRATEGIES
```

In period B, extra checks were added on some commits (the hourly read, TREND_STILL_GOING, ANALYSER_GOVERNS_ALL; table in section 0). They are not part of the direction rule; where they blocked a setup they are listed as "other" below.

## 2.2 Which setups the bot logged

**The bot logs an EMA pullback idea, allowed or blocked, only when a setup reaches its entry price.** The state and direction rule are checked only at that moment (`check()` is called on a candidate, and the strategy makes a candidate only when price reaches the entry, `strategy.py` lines 133-141). A setup (a touch of the 8 EMA) that is cancelled or expires before price reaches its entry is not logged anywhere and is never checked against the rule. Blocked ideas are logged on the finished candle (`decisions.jsonl`, `"kind": "idea"`, `"allowed": false`, with `blocked_by`); the live price path logs only allowed ideas.

So every setup was worked out from the stored 5-minute and hourly candles, by running the bot's own `EmaPullback` class (exact copy of the live code) candle by candle, exactly as the live runner feeds it: the 5-minute 8 and 21 EMAs over the 2,000 warm-up candles plus the week; the hourly trend reader rebuilt for every candle (as stored at start-up before 11 Nov 14:56, see section 0). Each setup's start, entry and end comes from the class's own notes. Method checks:

* all 85 finished-candle EMA pullback idea lines in `decisions.jsonl` (allowed and blocked) match a worked-out setup that reached its entry in the same candle, same direction, same price;
* all 24 trades match a worked-out setup (same touch candle, direction and entry);
* the step 0 text and the pivot and 100 EMA in each trade's `allowed at entry` step are reproduced exactly on all 24 trades (23 with the step; trade-level check in `results.json` `pivot_e100_check`).

**Setups 8 Nov 22:00 - 20 Nov 22:00: 483.** Reached their entry 86; cancelled by a close beyond the 21 EMA 226; expired after 20 minutes 169; still waiting at the week's end 2. Not setups (the bot's notes): 54 touches with the hourly trend the right way but not qualified, and 804 touch candles that closed beyond the 21 EMA (both counted per direction and candle).

Of the 86 that reached their entry, 1 did so before the service started on 9 Nov 00:09 (8 Nov 22:55, not live). The other 85: 24 traded; 14 were allowed but not sent because another EMA pullback setup the same way had already been sent in that candle (each of their lines has `"already_sent_live": true`); 47 were blocked.

| Period | Setups | Reached entry | Cancelled | Expired | Waiting at week end |
|---|---|---|---|---|---|
| A | 251 | 42 | 114 | 95 | 0 |
| B | 173 | 35 | 91 | 46 | 1 |
| C | 59 | 9 | 21 | 28 | 1 |

## 2.3 Each logged setup: which checks passed and which blocked it

The 38 allowed ideas (24 traded, 14 not sent, above) passed all three. The 47 blocked ones are below, each with its raw line. "State" is blocked when `blocked_by` says the state does not allow the EMA pullback or the trend goes the other way. Pivot and 100 EMA are read from the bot's own `blocked_by` text where the direction rule blocked (2 lines); where the direction rule does not appear in `blocked_by` it passed, and the pivot and 100 EMA values shown are worked out with the bot's code (the same calculation reproduces all 23 trades' logged values).

| decisions.jsonl line | Entry candle | Dir | Entry | Period / commit | State logged | State | Pivot (value) | 100 EMA (value) | Other checks that blocked |
|---|---|---|---|---|---|---|---|---|---|
| 212 | Mon 09 Nov 16:10 | buy | 13409.5 | A `2ff445f` | trend | blocked | passed (13351.7) | passed (13406.9) | - |
| 235 | Mon 09 Nov 18:25 | buy | 13424.7 | A `2ff445f` | consolidation | blocked | passed (13351.7) | passed (13412.1) | - |
| 236 | Mon 09 Nov 18:25 | buy | 13424.6 | A `2ff445f` | consolidation | blocked | passed (13351.7) | passed (13412.1) | - |
| 237 | Mon 09 Nov 18:25 | buy | 13423.4 | A `2ff445f` | consolidation | blocked | passed (13351.7) | passed (13412.1) | - |
| 245 | Mon 09 Nov 19:25 | buy | 13428.0 | A `2ff445f` | consolidation | blocked | passed (13351.7) | passed (13414.6) | - |
| 246 | Mon 09 Nov 19:25 | buy | 13426.9 | A `2ff445f` | consolidation | blocked | passed (13351.7) | passed (13414.6) | - |
| 247 | Mon 09 Nov 19:25 | buy | 13426.9 | A `2ff445f` | consolidation | blocked | passed (13351.7) | passed (13414.6) | - |
| 250 | Mon 09 Nov 19:30 | buy | 13426.9 | A `2ff445f` | consolidation | blocked | passed (13351.7) | passed (13414.8) | - |
| 296 | Mon 09 Nov 23:05 | buy | 13436.9 | A `2ff445f` | consolidation | blocked | passed (13351.7) | passed (13426.4) | - |
| 310 | Tue 10 Nov 01:10 | buy | 13440.4 | A `2ff445f` | emerging trend | blocked | passed (13413.8) | passed (13430.8) | - |
| 333 | Tue 10 Nov 03:15 | buy | 13445.4 | A `2ff445f` | emerging trend | blocked | passed (13413.8) | passed (13435.3) | - |
| 617 | Tue 10 Nov 23:05 | buy | 13345.2 | A `2ff445f` | trend | blocked | blocked (13413.8) | blocked (13350.6) | - |
| 658 | Wed 11 Nov 03:05 | buy | 13351.0 | A `2ff445f` | consolidation | blocked | blocked (13372.5) | passed (13348.9) | - |
| 840 | Wed 11 Nov 13:05 | sell | 13307.3 | A `03be0aa` | consolidation | blocked | passed (13372.5) | passed (13324.0) | - |
| 841 | Wed 11 Nov 13:05 | sell | 13307.3 | A `03be0aa` | consolidation | blocked | passed (13372.5) | passed (13324.0) | - |
| 842 | Wed 11 Nov 13:05 | sell | 13307.3 | A `03be0aa` | consolidation | blocked | passed (13372.5) | passed (13324.0) | - |
| 940 | Wed 11 Nov 21:55 | sell | 13267.9 | A `9467e19` | consolidation | blocked | passed (13372.5) | passed (13282.1) | - |
| 941 | Wed 11 Nov 21:55 | sell | 13267.9 | A `9467e19` | consolidation | blocked | passed (13372.5) | passed (13282.1) | - |
| 949 | Wed 11 Nov 22:40 | sell | 13262.3 | A `9467e19` | consolidation | blocked | passed (13372.5) | passed (13280.3) | - |
| 1017 | Thu 12 Nov 06:10 | sell | 13255.7 | A `9467e19` | consolidation | blocked | passed (13294.9) | passed (13266.1) | - |
| 1165 | Thu 12 Nov 17:20 | sell | 13230.2 | A `9467e19` | consolidation | blocked | passed (13294.9) | passed (13251.7) | - |
| 1166 | Thu 12 Nov 17:20 | sell | 13230.3 | A `9467e19` | consolidation | blocked | passed (13294.9) | passed (13251.7) | - |
| 1261 | Fri 13 Nov 06:30 | sell | 13221.8 | A `79c5dcf` | consolidation | blocked | passed (13243.5) | passed (13231.8) | - |
| 1262 | Fri 13 Nov 06:30 | sell | 13221.0 | A `79c5dcf` | consolidation | blocked | passed (13243.5) | passed (13231.8) | - |
| 1263 | Fri 13 Nov 06:30 | sell | 13221.0 | A `79c5dcf` | consolidation | blocked | passed (13243.5) | passed (13231.8) | - |
| 1476 | Mon 16 Nov 06:30 | sell | 13202.3 | B `9b61661` | consolidation | blocked | passed (13211.7) | passed (13209.7) | - |
| 1647 | Mon 16 Nov 22:05 | sell | 13177.6 | B `9b61661` | consolidation | blocked | passed (13211.7) | passed (13187.1) | - |
| 1661 | Tue 17 Nov 00:20 | sell | 13179.4 | B `aea2275` | ranging | blocked | passed (13194.4) | passed (13185.4) | TREND_STILL_GOING is on and the trend is not still going: no new low at least 5 pips below the previous low in the last 12 five-minute candles (the most: 2.6 pips below the swing low 13182.4 of 00:00, at 00:15) |
| 1665 | Tue 17 Nov 01:10 | sell | 13175.9 | B `aea2275` | emerging trend | passed | passed (13194.4) | passed (13184.7) | TREND_STILL_GOING is on and the trend is not still going: no new low at least 5 pips below the previous low in the last 12 five-minute candles (the most: 3.9 pips below the swing low 13182.4 of 00:00, at 00:25) |
| 1918 | Wed 18 Nov 07:05 | sell | 13177.1 | B `cc70dc5` | emerging trend | passed | passed (13200.1) | passed (13197.1) | the hourly chart is ranging (13186.8 to 13219.6): EMA pullback waits for an hourly close at least 3 pips beyond the hourly range |
| 1964 | Wed 18 Nov 08:05 | sell | 13167.1 | B `cc70dc5` | emerging trend | blocked | passed (13200.1) | passed (13192.5) | - |
| 2065 | Wed 18 Nov 11:30 | sell | 13164.1 | B `cc70dc5` | trend | passed | passed (13200.1) | passed (13177.8) | TREND_STILL_GOING is on and the trend is not still going: no new low at least 5 pips below the previous low in the last 12 five-minute candles (the most: 3.8 pips below the swing low 13170.9 of 10:40, at 11:05) |
| 2077 | Wed 18 Nov 14:10 | sell | 13159.3 | B `3d50353` | emerging trend | passed | passed (13200.1) | passed (13170.8) | TREND_STILL_GOING is on and the trend is not still going: no new low at least 5 pips below the previous low in the last 12 five-minute candles (the most: 3.7 pips below the swing low 13163.1 of 13:15, at 13:30) |
| 2081 | Wed 18 Nov 15:20 | sell | 13158.6 | B `3d50353` | ranging | blocked | passed (13200.1) | passed (13168.9) | TREND_STILL_GOING is on and the trend is not still going: no new low at least 5 pips below the previous low in the last 12 five-minute candles (the most: 1.2 pips below the swing low 13158.2 of 14:10, at 14:30); ANALYSER_GOVERNS_ALL: the analyser's state is ranging: the trend group opens nothing |
| 2110 | Wed 18 Nov 19:00 | sell | 13149.7 | B `3d50353` | consolidation | blocked | passed (13200.1) | passed (13158.4) | TREND_STILL_GOING is on and the trend is not still going: no new low at least 5 pips below the previous low in the last 12 five-minute candles (the most: 1.0 pips below the swing low 13152.9 of 18:30, at 18:55); ANALYSER_GOVERNS_ALL: the analyser's state is consolidation: the trend group opens nothing |
| 2128 | Thu 19 Nov 00:10 | sell | 13142.0 | B `3d50353` | consolidation | blocked | passed (13162.5) | passed (13149.1) | the hourly chart is ranging (13135.5 to 13172.6): EMA pullback waits for a 5-minute close (ANALYSER_USES_HOURLY) at least 3 pips beyond the hourly range; TREND_STILL_GOING is on and the trend is not still going: no new low at least 5 pips below the previous low in the last 12 five-minute candles (the most: 1.6 pips below the swing low 13145.3 of 23:35, at 00:00); ANALYSER_GOVERNS_ALL: the analyser's state is consolidation: the trend group opens nothing; ANALYSER_GOVERNS_ALL: the hourly chart is ranging (13135.5 to 13172.6): the trend group opens nothing |
| 2144 | Thu 19 Nov 03:00 | sell | 13129.0 | B `3d50353` | consolidation | blocked | passed (13162.5) | passed (13145.0) | ANALYSER_GOVERNS_ALL: the analyser's state is consolidation: the trend group opens nothing |
| 2253 | Thu 19 Nov 16:10 | sell | 13111.5 | B `d9e5d0e` | emerging trend | blocked | passed (13162.5) | passed (13144.0) | the hourly chart is in a rally: EMA pullback only buys; ANALYSER_GOVERNS_ALL: the emerging trend is up: EMA pullback only in the trend's direction |
| 2255 | Thu 19 Nov 16:15 | sell | 13110.6 | B `d9e5d0e` | emerging trend | passed | passed (13162.5) | passed (13143.3) | the hourly chart is in a rally: EMA pullback only buys |
| 2261 | Thu 19 Nov 17:05 | sell | 13101.4 | B `d9e5d0e` | emerging trend | passed | passed (13162.5) | passed (13137.6) | the hourly chart is in a rally: EMA pullback only buys |
| 2262 | Thu 19 Nov 17:05 | sell | 13101.4 | B `d9e5d0e` | emerging trend | passed | passed (13162.5) | passed (13137.6) | the hourly chart is in a rally: EMA pullback only buys |
| 2276 | Thu 19 Nov 17:55 | sell | 13101.6 | B `d9e5d0e` | emerging trend | blocked | passed (13162.5) | passed (13132.1) | the hourly chart is in a rally: EMA pullback only buys; ANALYSER_GOVERNS_ALL: the emerging trend is up: EMA pullback only in the trend's direction |
| 2277 | Thu 19 Nov 17:55 | sell | 13101.8 | B `d9e5d0e` | emerging trend | blocked | passed (13162.5) | passed (13132.1) | the hourly chart is in a rally: EMA pullback only buys; ANALYSER_GOVERNS_ALL: the emerging trend is up: EMA pullback only in the trend's direction |
| 2399 | Fri 20 Nov 01:45 | sell | 13086.5 | C `02f6c7e` | consolidation | blocked | passed (13111.6) | passed (13096.7) | - |
| 2700 | Fri 20 Nov 19:25 | sell | 13084.9 | C `02f6c7e` | consolidation | blocked | passed (13111.6) | passed (13102.1) | - |
| 2718 | Fri 20 Nov 20:30 | sell | 13079.1 | C `02f6c7e` | consolidation | blocked | passed (13111.6) | passed (13098.3) | - |
| 2719 | Fri 20 Nov 20:30 | sell | 13079.1 | C `02f6c7e` | consolidation | blocked | passed (13111.6) | passed (13098.3) | - |

<details><summary>The 47 raw lines, exactly as in data/records/GBPUSD/decisions.jsonl</summary>

```
212: {"time_utc": "2026-11-09T16:10:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "buy", "entry_price": "13409.5", "allowed": false, "blocked_by": "the trend is down: EMA pullback only in the trend's direction", "state": "trend", "already_sent_live": false}
235: {"time_utc": "2026-11-09T18:25:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "buy", "entry_price": "13424.7", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback", "state": "consolidation", "already_sent_live": false}
236: {"time_utc": "2026-11-09T18:25:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "buy", "entry_price": "13424.6", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback", "state": "consolidation", "already_sent_live": false}
237: {"time_utc": "2026-11-09T18:25:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "buy", "entry_price": "13423.4", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback", "state": "consolidation", "already_sent_live": false}
245: {"time_utc": "2026-11-09T19:25:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "buy", "entry_price": "13428", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback", "state": "consolidation", "already_sent_live": false}
246: {"time_utc": "2026-11-09T19:25:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "buy", "entry_price": "13426.9", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback", "state": "consolidation", "already_sent_live": false}
247: {"time_utc": "2026-11-09T19:25:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "buy", "entry_price": "13426.9", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback", "state": "consolidation", "already_sent_live": false}
250: {"time_utc": "2026-11-09T19:30:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "buy", "entry_price": "13426.9", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback", "state": "consolidation", "already_sent_live": false}
296: {"time_utc": "2026-11-09T23:05:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "buy", "entry_price": "13436.9", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback", "state": "consolidation", "already_sent_live": false}
310: {"time_utc": "2026-11-10T01:10:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "buy", "entry_price": "13440.4", "allowed": false, "blocked_by": "the emerging trend is down: EMA pullback only in the trend's direction", "state": "emerging trend", "already_sent_live": false}
333: {"time_utc": "2026-11-10T03:15:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "buy", "entry_price": "13445.4", "allowed": false, "blocked_by": "the emerging trend is down: EMA pullback only in the trend's direction", "state": "emerging trend", "already_sent_live": false}
617: {"time_utc": "2026-11-10T23:05:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "buy", "entry_price": "13345.2", "allowed": false, "blocked_by": "the trend is down: EMA pullback only in the trend's direction; the direction rule says sell side (price 13345.2 is below the pivot 13413.8 and below the 5m 100 EMA 13350.6)", "state": "trend", "already_sent_live": false}
658: {"time_utc": "2026-11-11T03:05:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "buy", "entry_price": "13351", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback; the direction rule says no clear direction (price 13351 is below the pivot 13372.5 and above the 5m 100 EMA 13348.9: they disagree)", "state": "consolidation", "already_sent_live": false}
840: {"time_utc": "2026-11-11T13:05:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13307.3", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback", "state": "consolidation", "already_sent_live": false}
841: {"time_utc": "2026-11-11T13:05:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13307.3", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback", "state": "consolidation", "already_sent_live": false}
842: {"time_utc": "2026-11-11T13:05:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13307.3", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback", "state": "consolidation", "already_sent_live": false}
940: {"time_utc": "2026-11-11T21:55:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13267.9", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback", "state": "consolidation", "already_sent_live": false}
941: {"time_utc": "2026-11-11T21:55:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13267.9", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback", "state": "consolidation", "already_sent_live": false}
949: {"time_utc": "2026-11-11T22:40:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13262.3", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback", "state": "consolidation", "already_sent_live": false}
1017: {"time_utc": "2026-11-12T06:10:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13255.7", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback", "state": "consolidation", "already_sent_live": false}
1165: {"time_utc": "2026-11-12T17:20:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13230.2", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback", "state": "consolidation", "already_sent_live": false}
1166: {"time_utc": "2026-11-12T17:20:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13230.3", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback", "state": "consolidation", "already_sent_live": false}
1261: {"time_utc": "2026-11-13T06:30:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13221.8", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback", "state": "consolidation", "already_sent_live": false}
1262: {"time_utc": "2026-11-13T06:30:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13221", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback", "state": "consolidation", "already_sent_live": false}
1263: {"time_utc": "2026-11-13T06:30:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13221", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback", "state": "consolidation", "already_sent_live": false}
1476: {"time_utc": "2026-11-16T06:30:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13202.3", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback", "state": "consolidation", "already_sent_live": false}
1647: {"time_utc": "2026-11-16T22:05:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13177.6", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback", "state": "consolidation", "already_sent_live": false}
1661: {"time_utc": "2026-11-17T00:20:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13179.4", "allowed": false, "blocked_by": "the analyser's state is ranging, which does not allow EMA pullback; TREND_STILL_GOING is on and the trend is not still going: no new low at least 5 pips below the previous low in the last 12 five-minute candles (the most: 2.6 pips below the swing low 13182.4 of 00:00, at 00:15)", "state": "ranging", "already_sent_live": false}
1665: {"time_utc": "2026-11-17T01:10:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13175.9", "allowed": false, "blocked_by": "TREND_STILL_GOING is on and the trend is not still going: no new low at least 5 pips below the previous low in the last 12 five-minute candles (the most: 3.9 pips below the swing low 13182.4 of 00:00, at 00:25)", "state": "emerging trend", "already_sent_live": false}
1918: {"time_utc": "2026-11-18T07:05:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13177.1", "allowed": false, "blocked_by": "the hourly chart is ranging (13186.8 to 13219.6): EMA pullback waits for an hourly close at least 3 pips beyond the hourly range", "state": "emerging trend", "already_sent_live": false}
1964: {"time_utc": "2026-11-18T08:05:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13167.1", "allowed": false, "blocked_by": "the emerging trend is up: EMA pullback only in the trend's direction", "state": "emerging trend", "already_sent_live": false}
2065: {"time_utc": "2026-11-18T11:30:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13164.1", "allowed": false, "blocked_by": "TREND_STILL_GOING is on and the trend is not still going: no new low at least 5 pips below the previous low in the last 12 five-minute candles (the most: 3.8 pips below the swing low 13170.9 of 10:40, at 11:05)", "state": "trend", "already_sent_live": false}
2077: {"time_utc": "2026-11-18T14:10:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13159.3", "allowed": false, "blocked_by": "TREND_STILL_GOING is on and the trend is not still going: no new low at least 5 pips below the previous low in the last 12 five-minute candles (the most: 3.7 pips below the swing low 13163.1 of 13:15, at 13:30)", "state": "emerging trend", "already_sent_live": false}
2081: {"time_utc": "2026-11-18T15:20:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13158.6", "allowed": false, "blocked_by": "the analyser's state is ranging, which does not allow EMA pullback; TREND_STILL_GOING is on and the trend is not still going: no new low at least 5 pips below the previous low in the last 12 five-minute candles (the most: 1.2 pips below the swing low 13158.2 of 14:10, at 14:30); ANALYSER_GOVERNS_ALL: the analyser's state is ranging: the trend group opens nothing", "state": "ranging", "already_sent_live": false}
2110: {"time_utc": "2026-11-18T19:00:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13149.7", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback; TREND_STILL_GOING is on and the trend is not still going: no new low at least 5 pips below the previous low in the last 12 five-minute candles (the most: 1.0 pips below the swing low 13152.9 of 18:30, at 18:55); ANALYSER_GOVERNS_ALL: the analyser's state is consolidation: the trend group opens nothing", "state": "consolidation", "already_sent_live": false}
2128: {"time_utc": "2026-11-19T00:10:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13142", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback; the hourly chart is ranging (13135.5 to 13172.6): EMA pullback waits for a 5-minute close (ANALYSER_USES_HOURLY) at least 3 pips beyond the hourly range; TREND_STILL_GOING is on and the trend is not still going: no new low at least 5 pips below the previous low in the last 12 five-minute candles (the most: 1.6 pips below the swing low 13145.3 of 23:35, at 00:00); ANALYSER_GOVERNS_ALL: the analyser's state is consolidation: the trend group opens nothing; ANALYSER_GOVERNS_ALL: the hourly chart is ranging (13135.5 to 13172.6): the trend group opens nothing", "state": "consolidation", "already_sent_live": false}
2144: {"time_utc": "2026-11-19T03:00:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13129", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback; ANALYSER_GOVERNS_ALL: the analyser's state is consolidation: the trend group opens nothing", "state": "consolidation", "already_sent_live": false}
2253: {"time_utc": "2026-11-19T16:10:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13111.5", "allowed": false, "blocked_by": "the emerging trend is up: EMA pullback only in the trend's direction; the hourly chart is in a rally: EMA pullback only buys; ANALYSER_GOVERNS_ALL: the emerging trend is up: EMA pullback only in the trend's direction", "state": "emerging trend", "already_sent_live": false}
2255: {"time_utc": "2026-11-19T16:15:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13110.6", "allowed": false, "blocked_by": "the hourly chart is in a rally: EMA pullback only buys", "state": "emerging trend", "already_sent_live": false}
2261: {"time_utc": "2026-11-19T17:05:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13101.4", "allowed": false, "blocked_by": "the hourly chart is in a rally: EMA pullback only buys", "state": "emerging trend", "already_sent_live": false}
2262: {"time_utc": "2026-11-19T17:05:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13101.4", "allowed": false, "blocked_by": "the hourly chart is in a rally: EMA pullback only buys", "state": "emerging trend", "already_sent_live": false}
2276: {"time_utc": "2026-11-19T17:55:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13101.6", "allowed": false, "blocked_by": "the emerging trend is up: EMA pullback only in the trend's direction; the hourly chart is in a rally: EMA pullback only buys; ANALYSER_GOVERNS_ALL: the emerging trend is up: EMA pullback only in the trend's direction", "state": "emerging trend", "already_sent_live": false}
2277: {"time_utc": "2026-11-19T17:55:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13101.8", "allowed": false, "blocked_by": "the emerging trend is up: EMA pullback only in the trend's direction; the hourly chart is in a rally: EMA pullback only buys; ANALYSER_GOVERNS_ALL: the emerging trend is up: EMA pullback only in the trend's direction", "state": "emerging trend", "already_sent_live": false}
2399: {"time_utc": "2026-11-20T01:45:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13086.5", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback", "state": "consolidation", "already_sent_live": false}
2700: {"time_utc": "2026-11-20T19:25:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13084.9", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback", "state": "consolidation", "already_sent_live": false}
2718: {"time_utc": "2026-11-20T20:30:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13079.1", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback", "state": "consolidation", "already_sent_live": false}
2719: {"time_utc": "2026-11-20T20:30:00Z", "kind": "idea", "paper": false, "strategy": "EMA pullback", "direction": "sell", "entry_price": "13079.1", "allowed": false, "blocked_by": "the analyser's state is consolidation, which does not allow EMA pullback", "state": "consolidation", "already_sent_live": false}
```
</details>

## 2.4 Trades that went ahead, by analyser state at the open

Bot's own exits only (owner closes listed apart). "Trend" includes the trend's sub-types written in `trades.jsonl` (`slow grind`, `strong push`).

| Period | Emerging trend | Trend |
|---|---|---|
| A | 7 trades, 0 won, 7 lost, -84.0 pips | 5 trades, 3 won, 2 lost, +66.0 pips |
| B | 4 trades, 0 won, 4 lost, -48.0 pips | 6 trades, 0 won, 6 lost, -72.0 pips |
| C | none | none |
| all | 11 trades, 0 won, 11 lost, -132.0 pips | 11 trades, 3 won, 8 lost, -6.0 pips |

Owner closes: trade 23 (emerging trend down, -7.9); trade 24 (emerging trend down, -1.4).

Per trade (bot's own exits):

| # | State at open | Dir | Opened | Pips | Closed by | Period |
|---|---|---|---|---|---|---|
| 1 | trend up, slow grind | buy | Mon 09 Nov 21:02 | -12.0 | IG stop | A |
| 2 | emerging trend up | buy | Tue 10 Nov 05:01 | -12.0 | IG stop | A |
| 3 | emerging trend up | buy | Tue 10 Nov 06:12 | -12.0 | IG stop | A |
| 4 | emerging trend up | buy | Tue 10 Nov 07:21 | -12.0 | IG stop | A |
| 5 | trend down, slow grind | sell | Wed 11 Nov 07:32 | +30.0 | IG take profit | A |
| 6 | trend down, slow grind | sell | Wed 11 Nov 08:16 | +30.0 | IG take profit | A |
| 7 | trend down, slow grind | sell | Wed 11 Nov 10:51 | +30.0 | IG take profit | A |
| 8 | trend down, slow grind | sell | Wed 11 Nov 18:48 | -12.0 | IG stop | A |
| 9 | emerging trend down | sell | Wed 11 Nov 21:06 | -12.0 | IG stop | A |
| 10 | emerging trend down | sell | Thu 12 Nov 19:02 | -12.0 | IG stop | A |
| 11 | emerging trend down | sell | Thu 12 Nov 22:00 | -12.0 | IG stop | A |
| 12 | emerging trend down | sell | Thu 12 Nov 23:47 | -12.0 | IG stop | A |
| 13 | emerging trend down | sell | Fri 13 Nov 10:28 | -12.0 | IG stop | B |
| 14 | emerging trend down | sell | Mon 16 Nov 10:50 | -12.0 | IG stop | B |
| 15 | emerging trend down | sell | Mon 16 Nov 14:26 | -12.0 | IG stop | B |
| 16 | trend down, slow grind | sell | Mon 16 Nov 14:57 | -12.0 | IG stop | B |
| 17 | trend down, slow grind | sell | Mon 16 Nov 15:50 | -12.0 | IG stop | B |
| 18 | trend down, slow grind | sell | Mon 16 Nov 16:53 | -12.0 | IG stop | B |
| 19 | emerging trend down | sell | Mon 16 Nov 20:00 | -12.0 | IG stop | B |
| 20 | trend up, slow grind | buy | Tue 17 Nov 17:16 | -12.0 | IG stop | B |
| 21 | trend down, slow grind | sell | Wed 18 Nov 12:37 | -12.0 | IG stop | B |
| 22 | trend down, strong push | sell | Wed 18 Nov 16:20 | -12.0 | IG stop | B |

22 trades split 11 and 11 is a small sample; it shows what happened, not how the states would behave over time.

## 2.5 Blocked setups: what blocked them, and a LOOK BACK at what price did next

| What blocked it | Setups |
|---|---|
| state (alone) | 30 |
| state + other | 8 |
| other (alone) | 7 |
| state + pivot + 100 EMA | 1 |
| state + pivot | 1 |

Each part, counted wherever it appears: state 40 (30 alone); pivot 2 (0 alone); 100 EMA 1 (0 alone); other checks 15 (7 alone).

Several blocked setups often reached their entry in the same candle: the 47 lines are 34 different candles and directions.

> **LOOK BACK - not live results.** Nothing below was traded. Every blocked setup reached its entry (the bot logs a blocked setup only at that moment), so "reached the entry within the 20-minute expiry" is yes for all 47. From the entry: fill as the bot's engine sets it on a finished candle (a sell at the entry price; a buy at the entry plus that candle's opening spread), then the stored 5-minute candles on the price a trade would close on (a buy on the sell price, a sell on the buy price), looking for 12 pips against (the stop) or 30 pips in favour (the brief's take profit) first, up to the EMA pullback's Friday 20:30 close. Where both fall in one candle the order is unknown and it says so; a hit in the entry candle itself is marked, because the part of that candle after the entry is unknown. Setups at or after Friday 20:30 UK could not have opened (`may_open`).

| decisions.jsonl line | Entry candle | Dir | What blocked it | LOOK BACK fill | LOOK BACK result | LOOK BACK when |
|---|---|---|---|---|---|---|
| 212 | Mon 09 Nov 16:10 | buy | state | 13411.0 | take profit (30 for) first | Mon 09 Nov 19:40 |
| 235 | Mon 09 Nov 18:25 | buy | state | 13426.2 | take profit (30 for) first | Tue 10 Nov 07:25 |
| 236 | Mon 09 Nov 18:25 | buy | state | 13426.1 | take profit (30 for) first | Tue 10 Nov 07:25 |
| 237 | Mon 09 Nov 18:25 | buy | state | 13424.9 | take profit (30 for) first | Tue 10 Nov 07:20 |
| 245 | Mon 09 Nov 19:25 | buy | state | 13429.5 | stop (12 against) first | Tue 10 Nov 13:10 |
| 246 | Mon 09 Nov 19:25 | buy | state | 13428.4 | take profit (30 for) first | Tue 10 Nov 08:30 |
| 247 | Mon 09 Nov 19:25 | buy | state | 13428.4 | take profit (30 for) first | Tue 10 Nov 08:30 |
| 250 | Mon 09 Nov 19:30 | buy | state | 13428.4 | take profit (30 for) first | Tue 10 Nov 08:30 |
| 296 | Mon 09 Nov 23:05 | buy | state | 13441.2 | stop (12 against) first | Tue 10 Nov 09:10 |
| 310 | Tue 10 Nov 01:10 | buy | state | 13441.9 | stop (12 against) first | Tue 10 Nov 09:10 |
| 333 | Tue 10 Nov 03:15 | buy | state | 13446.9 | stop (12 against) first | Tue 10 Nov 09:00 |
| 617 | Tue 10 Nov 23:05 | buy | state + pivot + 100 EMA | 13347.6 | stop (12 against) first | Wed 11 Nov 06:30 |
| 658 | Wed 11 Nov 03:05 | buy | state + pivot | 13352.5 | stop (12 against) first | Wed 11 Nov 06:00 |
| 840 | Wed 11 Nov 13:05 | sell | state | 13307.3 | take profit (30 for) first | Wed 11 Nov 14:00 |
| 841 | Wed 11 Nov 13:05 | sell | state | 13307.3 | take profit (30 for) first | Wed 11 Nov 14:00 |
| 842 | Wed 11 Nov 13:05 | sell | state | 13307.3 | take profit (30 for) first | Wed 11 Nov 14:00 |
| 940 | Wed 11 Nov 21:55 | sell | state | 13267.9 | stop (12 against) first | Wed 11 Nov 22:00 |
| 941 | Wed 11 Nov 21:55 | sell | state | 13267.9 | stop (12 against) first | Wed 11 Nov 22:00 |
| 949 | Wed 11 Nov 22:40 | sell | state | 13262.3 | stop (12 against) first - in the entry candle itself, where the order of prices after the entry is unknown | Wed 11 Nov 22:40 |
| 1017 | Thu 12 Nov 06:10 | sell | state | 13255.7 | stop (12 against) first | Thu 12 Nov 07:40 |
| 1165 | Thu 12 Nov 17:20 | sell | state | 13230.2 | stop (12 against) first | Thu 12 Nov 21:55 |
| 1166 | Thu 12 Nov 17:20 | sell | state | 13230.3 | stop (12 against) first | Thu 12 Nov 21:55 |
| 1261 | Fri 13 Nov 06:30 | sell | state | 13221.8 | stop (12 against) first | Fri 13 Nov 06:40 |
| 1262 | Fri 13 Nov 06:30 | sell | state | 13221.0 | stop (12 against) first | Fri 13 Nov 06:35 |
| 1263 | Fri 13 Nov 06:30 | sell | state | 13221.0 | stop (12 against) first | Fri 13 Nov 06:35 |
| 1476 | Mon 16 Nov 06:30 | sell | state | 13202.3 | stop (12 against) first | Mon 16 Nov 08:40 |
| 1647 | Mon 16 Nov 22:05 | sell | state | 13177.6 | stop (12 against) first - in the entry candle itself, where the order of prices after the entry is unknown | Mon 16 Nov 22:05 |
| 1661 | Tue 17 Nov 00:20 | sell | state + other | 13179.4 | stop (12 against) first | Tue 17 Nov 03:10 |
| 1665 | Tue 17 Nov 01:10 | sell | other | 13175.9 | stop (12 against) first | Tue 17 Nov 02:55 |
| 1918 | Wed 18 Nov 07:05 | sell | other | 13177.1 | take profit (30 for) first | Wed 18 Nov 16:00 |
| 1964 | Wed 18 Nov 08:05 | sell | state | 13167.1 | take profit (30 for) first | Wed 18 Nov 16:20 |
| 2065 | Wed 18 Nov 11:30 | sell | other | 13164.1 | take profit (30 for) first | Thu 19 Nov 02:20 |
| 2077 | Wed 18 Nov 14:10 | sell | other | 13159.3 | take profit (30 for) first | Thu 19 Nov 03:00 |
| 2081 | Wed 18 Nov 15:20 | sell | state + other | 13158.6 | take profit (30 for) first | Thu 19 Nov 03:00 |
| 2110 | Wed 18 Nov 19:00 | sell | state + other | 13149.7 | stop (12 against) first | Wed 18 Nov 22:10 |
| 2128 | Thu 19 Nov 00:10 | sell | state + other | 13142.0 | stop (12 against) first | Thu 19 Nov 00:55 |
| 2144 | Thu 19 Nov 03:00 | sell | state + other | 13129.0 | stop (12 against) first | Thu 19 Nov 06:20 |
| 2253 | Thu 19 Nov 16:10 | sell | state + other | 13111.5 | take profit (30 for) first | Thu 19 Nov 21:30 |
| 2255 | Thu 19 Nov 16:15 | sell | other | 13110.6 | take profit (30 for) first | Fri 20 Nov 02:10 |
| 2261 | Thu 19 Nov 17:05 | sell | other | 13101.4 | stop (12 against) first | Thu 19 Nov 17:20 |
| 2262 | Thu 19 Nov 17:05 | sell | other | 13101.4 | stop (12 against) first | Thu 19 Nov 17:20 |
| 2276 | Thu 19 Nov 17:55 | sell | state + other | 13101.6 | stop (12 against) first | Fri 20 Nov 06:10 |
| 2277 | Thu 19 Nov 17:55 | sell | state + other | 13101.8 | stop (12 against) first | Fri 20 Nov 06:10 |
| 2399 | Fri 20 Nov 01:45 | sell | state | 13086.5 | stop (12 against) first | Fri 20 Nov 03:35 |
| 2700 | Fri 20 Nov 19:25 | sell | state | 13084.9 | neither by 2026-11-20T20:30:00Z (the EMA pullback's Friday 20:30 UK close or the data end) |  |
| 2718 | Fri 20 Nov 20:30 | sell | state | 13079.1 | could not have opened: Friday after 20:30 UK |  |
| 2719 | Fri 20 Nov 20:30 | sell | state | 13079.1 | could not have opened: Friday after 20:30 UK |  |

LOOK BACK totals (setups, not trades; same-candle duplicates each counted):

* stop (12 against) first: 27
* take profit (30 for) first: 17
* could not have opened: 2
* neither: 1

LOOK BACK by what blocked it:

| What blocked it | Take profit first | Stop first | Both in one candle | Neither | Could not have opened |
|---|---|---|---|---|---|
| state | 11 | 16 | 0 | 1 | 2 |
| state + other | 2 | 6 | 0 | 0 | 0 |
| other | 4 | 3 | 0 | 0 | 0 |
| state + pivot + 100 EMA | 0 | 1 | 0 | 0 | 0 |
| state + pivot | 0 | 1 | 0 | 0 | 0 |

## 2.6 When the blocked setups came

By UK hour of the entry candle (all 47; the state that blocked is the logged state):

| UK hour | Blocked setups | Of which state consolidation / ranging / emerging or trend the other way / passed state | Dates |
|---|---|---|---|
| 00 | 2 | 1 / 1 / 0 / 0 | 17 Nov, 19 Nov |
| 01 | 3 | 1 / 0 / 1 / 1 | 10 Nov, 17 Nov, 20 Nov |
| 03 | 3 | 2 / 0 / 1 / 0 | 10 Nov, 11 Nov, 19 Nov |
| 06 | 5 | 5 / 0 / 0 / 0 | 12 Nov, 13 Nov, 16 Nov |
| 07 | 1 | 0 / 0 / 0 / 1 | 18 Nov |
| 08 | 1 | 0 / 0 / 1 / 0 | 18 Nov |
| 11 | 1 | 0 / 0 / 0 / 1 | 18 Nov |
| 13 | 3 | 3 / 0 / 0 / 0 | 11 Nov |
| 14 | 1 | 0 / 0 / 0 / 1 | 18 Nov |
| 15 | 1 | 0 / 1 / 0 / 0 | 18 Nov |
| 16 | 3 | 0 / 0 / 2 / 1 | 09 Nov, 19 Nov |
| 17 | 6 | 2 / 0 / 2 / 2 | 12 Nov, 19 Nov |
| 18 | 3 | 3 / 0 / 0 / 0 | 09 Nov |
| 19 | 6 | 6 / 0 / 0 / 0 | 09 Nov, 18 Nov, 20 Nov |
| 20 | 2 | 2 / 0 / 0 / 0 | 20 Nov |
| 21 | 2 | 2 / 0 / 0 / 0 | 11 Nov |
| 22 | 2 | 2 / 0 / 0 / 0 | 11 Nov, 16 Nov |
| 23 | 2 | 1 / 0 / 1 / 0 | 09 Nov, 10 Nov |

In three blocks: 00:00-06:59: 13; 07:00-15:59: 8; 16:00-23:59: 26.

By day:

| Day | Blocked setups | Traded setups that day |
|---|---|---|
| Mon 09 Nov | 9 | 1 |
| Tue 10 Nov | 3 | 3 |
| Wed 11 Nov | 7 | 5 |
| Thu 12 Nov | 3 | 3 |
| Fri 13 Nov | 3 | 1 |
| Mon 16 Nov | 2 | 6 |
| Tue 17 Nov | 2 | 1 |
| Wed 18 Nov | 6 | 2 |
| Thu 19 Nov | 8 | 1 |
| Fri 20 Nov | 4 | 1 |

The pivot blocked 2 setups (both also blocked by the state), both buys in the night: decisions.jsonl lines 617 (Tue 10 Nov 23:05) and 658 (Wed 11 Nov 03:05). There is no case in the record of the pivot blocking a setup early in a trend day, so the record cannot show whether that happens.

# Part 3. Wick past the 21 EMA vs close past it

## 3.1 The live cancel code

`strategies/ema_pullback/strategy.py` at `02f6c7e`, lines 125-145:

```python
 125          for st in list(self.setups):
 126              d, buy = st.direction, st.direction == BUY
 127              tag = f"setup from {uk_short(st.touch.start)[-9:]}"
 128              if c.start >= st.touch.start + expire:                          # 5.
 129                  self.setups.remove(st)
 130                  self.notes.append((c.start, d, f"{tag}: expired, {plain(st.entry)} not reached within "
 131                                                 f"{self.e.setup_expires_after_minutes} minutes"))
 132                  continue
 133              if self._h(c) >= st.entry if buy else self._l(c) <= st.entry:   # 4.
 134                  opened = self._o(c) >= st.entry if buy else self._o(c) <= st.entry
 135                  price = self._o(c) if opened else st.entry
 136                  self.setups.remove(st)
 137                  self.notes.append((c.start, d, f"{tag}: reached the entry {plain(st.entry)}: entry {plain(price)}"))
 138                  out.append(Candidate(EMA_PULLBACK, d, c.start, price, st.steps + [
 139                      f"{uk_short(c.start)}: price reached the entry {plain(st.entry)}"
 140                      + (f" (the candle opened past it, at {plain(price)})" if opened else " (during this candle)")]))
 141                  continue
 142              if slow is not None and ((self._c(c) < slow) if buy else (self._c(c) > slow)):   # 2.
 143                  self.setups.remove(st)
 144                  self.notes.append((c.start, d, f"{tag}: closed {q(self._c(c))} {'below' if buy else 'above'} the "
 145                                                 f"{self.e.slow_ema_periods} EMA {q(slow)}: cancelled"))
```

The touch candle itself is also refused if it closes beyond the 21 EMA:

`strategies/ema_pullback/strategy.py` at `02f6c7e`, lines 158-162:

```python
 158                  if (self._c(c) < slow) if buy else (self._c(c) > slow):
 159                      self.notes.append((c.start, d, f"touched the 8 EMA {q(self.prev_fast)}; the touch candle closed "
 160                                                     f"{q(self._c(c))} {'below' if buy else 'above'} the "
 161                                                     f"{self.e.slow_ema_periods} EMA {q(slow)}: cancelled"))
 162                      continue
```

The 21 EMA compared is the one at that candle's own close (`slow.get(c.start)` in `strategies/replay.py`), on the sell (chart) price.

## 3.2 Every setup: a wick beyond the 21 EMA without a close beyond it

For each setup, every 5-minute candle from the touch candle up to the candle before the entry candle (or up to the candle before the cancel or expiry): a buy's low below that candle's 21 EMA while its close stayed at or above it (a sell: high above, close at or below). Distance = how far the wick went beyond the 21 EMA, in pips, sell price. The entry candle is listed apart: within it the order of the wick and the entry is unknown. The full list of all setups, with every wick, is `setups.csv`.

| Outcome | Setups | With a wick beyond the 21 EMA | Without |
|---|---|---|---|
| reached | 86 | 54 | 32 |
| cancelled | 226 | 140 | 86 |
| expired | 169 | 83 | 86 |
| open at week end | 2 | 2 | 0 |

## 3.3 Trades: with a wick vs without

Bot's own exits: with a wick before the entry candle 15 trades, 2 won, 13 lost, -96.0 pips; without 7 trades, 1 won, 6 lost, -42.0 pips. Owner closes: trade 23 wick 0.5 (-7.9); trade 24 wick 0.0 (-1.4).

* Period A: with a wick 8 trades, 2 won, 6 lost, -12.0 pips; without 4 trades, 1 won, 3 lost, -6.0 pips.
* Period B: with a wick 7 trades, 0 won, 7 lost, -84.0 pips; without 3 trades, 0 won, 3 lost, -36.0 pips.
* Period C: with a wick none; without none.

With 22 trades and 3 winners this is too small a sample to say whether a wick past the 21 EMA matters.

## 3.4 How far past the 21 EMA the wicks went (trades)

Every trade, sorted by its largest wick beyond the 21 EMA before the entry candle, largest first. Each wick candle is listed. No cut-off is applied.

| # | Dir | Opened | Largest wick (pips) | Every wick candle: time, 21 EMA, low/high, close, pips beyond | Entry candle wick (order unknown) | Pips | Closed by | Period |
|---|---|---|---|---|---|---|---|---|
| 15 | sell | Mon 16 Nov 14:26 | 2.5 | 14:20 21 EMA 13197.6, high 13200.1, close 13193.5: 2.5 | - | -12.0 | IG stop | B |
| 19 | sell | Mon 16 Nov 20:00 | 2.1 | 19:50 21 EMA 13187.4, high 13189.5, close 13187.2: 2.1; 19:55 21 EMA 13187.2, high 13187.5, close 13185.8: 0.3 | - | -12.0 | IG stop | B |
| 12 | sell | Thu 12 Nov 23:47 | 1.6 | 23:35 21 EMA 13232.2, high 13233.8, close 13232.2: 1.6; 23:40 21 EMA 13232.1, high 13232.5, close 13230.6: 0.4 | - | -12.0 | IG stop | A |
| 7 | sell | Wed 11 Nov 10:51 | 1.4 | 10:40 21 EMA 13323.0, high 13324.4, close 13322.7: 1.4; 10:45 21 EMA 13322.7, high 13323.6, close 13319.8: 0.9 | - | +30.0 | IG take profit | A |
| 11 | sell | Thu 12 Nov 22:00 | 1.3 | 21:55 21 EMA 13235.1, high 13236.4, close 13229.1: 1.3 | - | -12.0 | IG stop | A |
| 16 | sell | Mon 16 Nov 14:57 | 1.3 | 14:40 21 EMA 13196.5, high 13197.8, close 13193.5: 1.3; 14:45 21 EMA 13196.4, high 13196.8, close 13195.7: 0.4; 14:50 21 EMA 13195.8, high 13196.4, close 13189.5: 0.6 | - | -12.0 | IG stop | B |
| 5 | sell | Wed 11 Nov 07:32 | 1.0 | 07:25 21 EMA 13339.4, high 13340.4, close 13336.4: 1.0 | - | +30.0 | IG take profit | A |
| 8 | sell | Wed 11 Nov 18:48 | 1.0 | 18:40 21 EMA 13276.9, high 13277.9, close 13276.7: 1.0 | 18:45 0.1 | -12.0 | IG stop | A |
| 3 | buy | Tue 10 Nov 06:12 | 0.8 | 06:00 21 EMA 13445.6, low 13444.8, close 13446.2: 0.8; 06:05 21 EMA 13445.9, low 13445.7, close 13448.8: 0.2 | - | -12.0 | IG stop | A |
| 4 | buy | Tue 10 Nov 07:21 | 0.6 | 07:10 21 EMA 13447.9, low 13447.3, close 13449.6: 0.6 | - | -12.0 | IG stop | A |
| 23 | sell | Thu 19 Nov 19:51 | 0.5 | 19:35 21 EMA 13102.4, high 13102.5, close 13100.4: 0.1; 19:45 21 EMA 13101.9, high 13102.4, close 13098.3: 0.5 | - | -7.9 | owner close | C |
| 13 | sell | Fri 13 Nov 10:28 | 0.3 | 10:10 21 EMA 13233.3, high 13233.6, close 13231.3: 0.3 | - | -12.0 | IG stop | B |
| 21 | sell | Wed 18 Nov 12:37 | 0.3 | 12:30 21 EMA 13164.2, high 13164.5, close 13161.1: 0.3 | - | -12.0 | IG stop | B |
| 9 | sell | Wed 11 Nov 21:06 | 0.2 | 20:50 21 EMA 13276.6, high 13276.8, close 13276.3: 0.2; 20:55 21 EMA 13276.3, high 13276.4, close 13273.4: 0.1 | - | -12.0 | IG stop | A |
| 14 | sell | Mon 16 Nov 10:50 | 0.2 | 10:35 21 EMA 13197.0, high 13197.2, close 13196.6: 0.2; 10:40 21 EMA 13196.5, high 13196.6, close 13191.1: 0.1 | - | -12.0 | IG stop | B |
| 18 | sell | Mon 16 Nov 16:53 | 0.1 | 16:35 21 EMA 13188.9, high 13189.0, close 13185.8: 0.1 | - | -12.0 | IG stop | B |
| 1 | buy | Mon 09 Nov 21:02 | 0.0 | - | - | -12.0 | IG stop | A |
| 2 | buy | Tue 10 Nov 05:01 | 0.0 | - | - | -12.0 | IG stop | A |
| 6 | sell | Wed 11 Nov 08:16 | 0.0 | - | - | +30.0 | IG take profit | A |
| 10 | sell | Thu 12 Nov 19:02 | 0.0 | - | - | -12.0 | IG stop | A |
| 17 | sell | Mon 16 Nov 15:50 | 0.0 | - | - | -12.0 | IG stop | B |
| 20 | buy | Tue 17 Nov 17:16 | 0.0 | - | - | -12.0 | IG stop | B |
| 22 | sell | Wed 18 Nov 16:20 | 0.0 | - | - | -12.0 | IG stop | B |
| 24 | sell | Fri 20 Nov 18:42 | 0.0 | - | - | -1.4 | owner close | C |

For comparison, the same measure on the setups that reached their entry but were blocked (LOOK BACK result beside it, not a live result):

| decisions.jsonl line | Dir | Entry candle | Largest wick (pips) | LOOK BACK result |
|---|---|---|---|---|
| 212 | buy | Mon 09 Nov 16:10 | 6.6 | LOOK BACK: take profit (30 for) first |
| 296 | buy | Mon 09 Nov 23:05 | 4.8 | LOOK BACK: stop (12 against) first |
| 617 | buy | Tue 10 Nov 23:05 | 3.9 | LOOK BACK: stop (12 against) first |
| 1661 | sell | Tue 17 Nov 00:20 | 2.9 | LOOK BACK: stop (12 against) first |
| 1918 | sell | Wed 18 Nov 07:05 | 2.8 | LOOK BACK: take profit (30 for) first |
| 1165 | sell | Thu 12 Nov 17:20 | 2.5 | LOOK BACK: stop (12 against) first |
| 2065 | sell | Wed 18 Nov 11:30 | 2.5 | LOOK BACK: take profit (30 for) first |
| 2081 | sell | Wed 18 Nov 15:20 | 2.5 | LOOK BACK: take profit (30 for) first |
| 2077 | sell | Wed 18 Nov 14:10 | 2.3 | LOOK BACK: take profit (30 for) first |
| 2110 | sell | Wed 18 Nov 19:00 | 2.1 | LOOK BACK: stop (12 against) first |
| 1665 | sell | Tue 17 Nov 01:10 | 2.0 | LOOK BACK: stop (12 against) first |
| 2399 | sell | Fri 20 Nov 01:45 | 1.5 | LOOK BACK: stop (12 against) first |
| 310 | buy | Tue 10 Nov 01:10 | 1.4 | LOOK BACK: stop (12 against) first |
| 1476 | sell | Mon 16 Nov 06:30 | 1.3 | LOOK BACK: stop (12 against) first |
| 1647 | sell | Mon 16 Nov 22:05 | 1.3 | LOOK BACK: stop (12 against) first - in the entry candle itself, where the order of prices after the entry is unknown |
| 658 | buy | Wed 11 Nov 03:05 | 1.0 | LOOK BACK: stop (12 against) first |
| 1017 | sell | Thu 12 Nov 06:10 | 1.0 | LOOK BACK: stop (12 against) first |
| 333 | buy | Tue 10 Nov 03:15 | 0.8 | LOOK BACK: stop (12 against) first |
| 840 | sell | Wed 11 Nov 13:05 | 0.8 | LOOK BACK: take profit (30 for) first |
| 841 | sell | Wed 11 Nov 13:05 | 0.8 | LOOK BACK: take profit (30 for) first |
| 842 | sell | Wed 11 Nov 13:05 | 0.8 | LOOK BACK: take profit (30 for) first |
| 245 | buy | Mon 09 Nov 19:25 | 0.5 | LOOK BACK: stop (12 against) first |
| 246 | buy | Mon 09 Nov 19:25 | 0.5 | LOOK BACK: take profit (30 for) first |
| 247 | buy | Mon 09 Nov 19:25 | 0.5 | LOOK BACK: take profit (30 for) first |
| 1261 | sell | Fri 13 Nov 06:30 | 0.5 | LOOK BACK: stop (12 against) first |
| 1262 | sell | Fri 13 Nov 06:30 | 0.5 | LOOK BACK: stop (12 against) first |
| 1263 | sell | Fri 13 Nov 06:30 | 0.5 | LOOK BACK: stop (12 against) first |
| 235 | buy | Mon 09 Nov 18:25 | 0.4 | LOOK BACK: take profit (30 for) first |
| 236 | buy | Mon 09 Nov 18:25 | 0.4 | LOOK BACK: take profit (30 for) first |
| 949 | sell | Wed 11 Nov 22:40 | 0.4 | LOOK BACK: stop (12 against) first - in the entry candle itself, where the order of prices after the entry is unknown |
| 237 | buy | Mon 09 Nov 18:25 | 0.3 | LOOK BACK: take profit (30 for) first |
| 940 | sell | Wed 11 Nov 21:55 | 0.2 | LOOK BACK: stop (12 against) first |
| 941 | sell | Wed 11 Nov 21:55 | 0.2 | LOOK BACK: stop (12 against) first |
| 2128 | sell | Thu 19 Nov 00:10 | 0.2 | LOOK BACK: stop (12 against) first |
| 250 | buy | Mon 09 Nov 19:30 | 0.0 | LOOK BACK: take profit (30 for) first |
| 1166 | sell | Thu 12 Nov 17:20 | 0.0 | LOOK BACK: stop (12 against) first |
| 1964 | sell | Wed 18 Nov 08:05 | 0.0 | LOOK BACK: take profit (30 for) first |
| 2144 | sell | Thu 19 Nov 03:00 | 0.0 | LOOK BACK: stop (12 against) first |
| 2253 | sell | Thu 19 Nov 16:10 | 0.0 | LOOK BACK: take profit (30 for) first |
| 2255 | sell | Thu 19 Nov 16:15 | 0.0 | LOOK BACK: take profit (30 for) first |
| 2261 | sell | Thu 19 Nov 17:05 | 0.0 | LOOK BACK: stop (12 against) first |
| 2262 | sell | Thu 19 Nov 17:05 | 0.0 | LOOK BACK: stop (12 against) first |
| 2276 | sell | Thu 19 Nov 17:55 | 0.0 | LOOK BACK: stop (12 against) first |
| 2277 | sell | Thu 19 Nov 17:55 | 0.0 | LOOK BACK: stop (12 against) first |
| 2700 | sell | Fri 20 Nov 19:25 | 0.0 | LOOK BACK: neither by 2026-11-20T20:30:00Z (the EMA pullback's Friday 20:30 UK close or the data end) |
| 2718 | sell | Fri 20 Nov 20:30 | 0.0 | could not have opened: Friday after 20:30 UK |
| 2719 | sell | Fri 20 Nov 20:30 | 0.0 | could not have opened: Friday after 20:30 UK |


# What I couldn't check, and why

1. **The exact age of the price when an order went out.**
   - The records keep IG's time stamp on the triggering price and the time the order was sent, both only to the second, so the ages in 1.5 are each ±1 s.
   - The bot doesn't record when it received the price, so delay between IG and the bot can't be told apart from delay inside the bot.
   - Live prices aren't stored, so the prices between the trigger and IG's fill can't be seen.
2. **Prices inside a 5-minute candle.** Only finished 5-minute candles are stored. So:
   - which came first inside the entry candle, a wick or the entry, is unknown (listed apart in 3.4);
   - a LOOK BACK stop or take profit hit inside the entry candle is marked as uncertain;
   - the spread at a close is known only at the candle's open and close (1.4).
3. **Setups that never reached their entry.** The bot doesn't log them, so the 395 that were cancelled or expired can only be rebuilt from the candles, not checked against a live record. The rebuild matches all 85 logged idea lines and all 24 trades exactly. Every setup that reached its entry while the service was running is in the log, so the service missed none.
4. **The direction rule on setups that never reached their entry.** The bot only checks the rule at the entry, so for those setups there is no "passed" or "blocked" to report. I didn't work out what the rule would have said, because the bot never applied it.
5. **Which switches were on at each moment.** The repository doesn't record the history of `.env`. Period B's extra gates (the hourly read, TREND_STILL_GOING, ANALYSER_GOVERNS_ALL) show only where they blocked something (2.3). Section 0 lists only whether each gate's code was present.
6. **Uncommitted code at each start.** The commit per start is HEAD from `git reflog`. Edits that weren't committed can't be ruled out. For every trade, though, the logged step 0, pivot and 100 EMA are reproduced exactly by this code.
7. **The news calendar as it stood at the time.** I used the calendar copy on disk now (fetched again every 6 hours, covering 31 Oct onwards). Event times may have been revised after the fact. The news table itself is unchanged since `f99efe1`.
8. **The LOOK BACK take profit.** It uses the brief's 30 pips. 9 of the 24 live trades were actually sent with 100 pips (`take_profit_kind` "100 for a big-news day", section 1).
9. **How long the LOOK BACK runs.** It follows each blocked setup up to the EMA pullback's Friday 20:30 close, so some results come many hours later (the "LOOK BACK when" column). A live trade could also have been closed by Johnny or hit by a rollover spread, and the LOOK BACK doesn't model either.
10. **Sample size.** 22 bot-closed trades with 3 winners, and every win came on one morning (11 Nov, trades 5–7). That is too few to judge any of the five problems, the analyser states or the wick question on results. The counts show what happened; they don't show what will happen.
