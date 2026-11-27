# 1. Extended forensic trade analysis (18–27 November 2026)

Phase 3, research only. Branch `research/phase3-structural-coherence-20261127` (from production `fadf228`).
Nothing in production was changed. Data was copied read-only after Friday's last entry window (20:30 UTC;
no position open). The source file hashes are in `evidence/output/SOURCE_SHA256.txt`.

## 1.1 Scope and evidence rules

| Item | What was used |
|---|---|
| Window | **25–27 Nov at full depth.** This extends Phase 1 (25–26 Nov) to the end of Friday's session. **18–24 Nov at the same automated depth**, because STP has published live opportunities since 17 Nov 20:24 UTC. STP changed during the window: structural history from 20 Nov, two-direction opportunities from 24 Nov, Stage B authorisation 25 Nov 13:10 to 27 Nov 16:26. Each trade is assessed against the STP state recorded at the time. |
| Trades | All 86 trades opened 18–27 Nov: 70 bot exits and 16 owner closes (IG channel SYSTEM/WEB, not at stop/limit). Owner closes are listed separately and are never counted as bot results. |
| Broker evidence | Opens: every trade has an IG deal ID and IG level (orders.jsonl). Closes: IG evidence where saved. The Phase 1 execution-integrity findings are applied: **26 Nov 06:01** bounce = IG +5.0 (record +4.5, R5). **18 Nov 12:37** EMA pullback = IG −12.0 (record −12.6, R6). **25 Nov 18:02** slow grind (the orphan) = IG −15.0, booked from IG's activity. The 12 records from 20–27 Nov with no saved IG close evidence are marked as such. Their figures are the bot's records. |
| Structural state | STP lifecycle events (`recommendations.jsonl`) with time ≤ entry. Finished 5-minute candles before the entry. No later information. |
| Thresholds | Only existing ones: NEAR = `rejection.near_level_within_pips` 3 (STP's own "interacts"). Break = STP's D-20 event `broken` (hourly close ≥ `planner.break_beyond_pips` 3 beyond the far edge). Held break = STP's own "confirmed break held". Own stop = the trade's actual stop distance at IG. |
| Tick evidence | **No tick archive covers November 2026.** The vendor archive ends in February 2026, and the bot does not store IG ticks. Intrabar order was settled from the journals' second-resolution timestamps (orders.jsonl, decisions.jsonl, recommendations.jsonl). Section 1.5 lists the only two cases where seconds matter. MFE/MAE come from 5-minute bid/ask candles ("strict" = candles wholly inside the trade). These are bounds, not tick paths. |

Observed facts and interpretation are separated: tables A and B are observed or computed from records; the
"Reading" paragraphs are interpretation.

## 1.2 Week in one view

| | Bot trades | Winners | Losers | Owner closes |
|---|---|---|---|---|
| 18–24 Nov | 50 | 18 | 32 | 12 |
| 25–27 Nov | 20 | 7 | 13 | 4 |

(Recorded IG results. Per-trade figures are in Table A. No totals are used as a verdict on any rule; see §6.)

## 1.3 Friday 27 November (new since Phase 1)

| Time | Trade | Structural situation (observed) | Result |
|---|---|---|---|
| 06:55 | Bounce 5m BUY 13125.9 (STP-authorised, 0300-56) | Zones 13093–103 and 13108.5–119.1 broken upwards overnight (D-20; 13093–103 break held). Inside BUY zone 13121.3–130.6 after its 05:00 failed breakout. | −2.0 |
| 10:00 | Breakout BUY 13127.8 | Inside the same BUY zone. Hourly wick sweeps below it at 07:00, 09:00 and 10:00 all closed back inside. The lower zones' breaks held. | −6.0 (stop 6) |
| 12:01 | Bounce 5m BUY 13132.0 (STP-authorised, 1200-57) | At the re-issued BUY zone (0300-56 completed 11:05; 1200-57 created 12:00). | owner close −1.4, 31 s before the deployment stop |
| 15:11 | Bounce 5m SELL 13106.7 (STP-authorised, 1500-59) | BUY zone 13121.3–130.3 broken downwards (D-20, 15:00). Contested zone 13108.5–119.1: SELL 1500-59 and BUY 1500-60 both Watch & Wait. | owner close +9.0 at 16:20 |
| 15:47 | Slow grind SELL 13102.0 | 5.9 pips below BUY 1500-60 (13108.5–119.1), which STP held in Watch & Wait. Its D-20 break came at 16:00, 13 minutes later. | owner close +4.3 at 16:20 |

The Friday ideas that never became trades matter more for Phase 3 than Friday's trades. 37 of Friday's 94
confirmed ideas sat inside or beyond an unresolved opposing STP zone (§6.3). Most were bounce 5m and
level-reversal SELLs at the BUY zone 13121.3–130.x between 03:45 and 10:52. That zone held: three hourly wick
sweeps closed back inside it, and 0300-56 completed at 11:05. The entry filters (RSI stretch, counter-trend
tiring) refused those SELLs, so none of them opened.

## 1.4 Patterns across the window (observed)

1. **Continuation through an opposing zone STP had not seen broken.** These trades opened past the far edge of a
   touched opposing zone (STP status ACTIVE), before STP's D-20 hourly break. 20 Nov 13:25 slow grind BUY.
   23 Nov 06:45 EMA pullback BUY. 25 Nov 18:45 slow grind BUY. Also 20 Nov 13:10 level reversal BUY and 27 Nov
   15:47 slow grind SELL, both owner closes. Every bot trade here lost.
2. **Entries inside an opposing zone with no structural resolution.** 23 Nov 06:00 level reversal BUY.
   23 Nov 12:26 bounce BUY and 12:30 sweep BUY, both inside SELL 1200-13. 23 Nov 13:00 bounce 5m BUY. 25 Nov
   12:25 sweep BUY, inside SELL 1200-29 (owner close). 25 Nov 18:02 slow grind BUY, inside SELL 1800-35 (the
   orphan). 25 Nov 19:10 EMA pullback BUY. 26 Nov 11:45 breakout SELL and 11:55 slow grind SELL, inside BUY
   zones and against STP's upward D-20 break of 0400-38. Every bot trade here lost.
3. **Reversals at a contested zone** (STP live in both directions on the same zone, OD-33). 26 Nov 06:01 BUY
   +5.0 and 06:30 SELL −7.3. 27 Nov 15:11 SELL (owner close +9.0). Here the strategy's own rejection is the only
   resolving evidence. The outcomes were mixed.
4. **Opposite positions.** 26 trades opened while a bot position in the other direction was open. 14 of them had
   no structural relation to any STP zone (neutral): 4 bot winners (EMA pullback 23 Nov 14:39 +30, slow grind
   23 Nov 10:57 +20, two sweeps +7.5/+12.2) and 10 bot losers. That is mostly the 23 Nov hourly-bounce BUYs during
   the down-move, when STP had no live opportunity.
5. **Most losses are structurally neutral.** 45 bot losers: 11 are within-opposing (S4), 1 is approaching
   (S3), 28 are neutral (S2), and 5 are aligned, confirmed rejection, confirmed break or continuation (S1/S5/S6/S7). No structural check built on STP can touch the neutral ones. This matches the
   brief: a small number of outlier trades are structural, the rest are strategy behaviour.

## 1.5 Intrabar and sequencing notes

| Trade | Sequencing question | Evidence | Effect |
|---|---|---|---|
| 23 Nov 13:00:12 bounce 5m BUY | SELL 1300-14 created 13:00:03, 9 s before | recommendations.jsonl / decisions.jsonl timestamps | S4 depends on the planner having published first. The implementation must assess against the state as of the order (test TS-12). |
| 25 Nov 18:02:03 slow grind BUY | SELL 1800-35 created 18:00:02 | same | no ambiguity (2 min) |
| 25 Nov 15:05:01 session sweep BUY | BUY 1500-32 created 15:00:03 at the swept low | same | permitted under every option |
| 26 Nov 11:55:14 slow grind SELL | 0400-38 failed breakout at 12:00:00 | same | at 11:55 the zone was BROKEN upwards; S4 (against a confirmed break) |
| 27 Nov 15:11:16 bounce 5m SELL | 1500-59/60 active 15:10:00 | same | S5 |

## 1.6 Table A1 — execution record, 25–27 Nov (IG levels; prices in points, 13108.9 = 1.31089)

| # | Opened UTC | Strategy | Dir | Fill | Stop pips | Closed UTC | How closed | Pips | By | MFE / MAE | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 63 | 11-25 03:37 | slow grind | SELL | 13096.1 | 15 | 11-25 07:01 | take profit hit at IG | 20.0 | bot | 19.1 / 1.5 | IG |
| 64 | 11-25 07:40 | Asian range breakout | SELL | 13079.5 | 12 | 11-25 08:00 | stopped by IG | 5.0 | bot | 10.5 / 5.8 | IG |
| 65 | 11-25 08:05 | breakout | SELL | 13070.6 | 6 | 11-25 08:06 | stopped by IG | -6.0 | bot | -0.8 / 6.2 | IG |
| 66 | 11-25 11:00 | EMA pullback | SELL | 13066.9 | 12 | 11-25 12:20 | stopped by IG | -12.0 | bot | 10.4 / 10.9 | IG |
| 67 | 11-25 12:25 | session sweep | BUY | 13078.5 | 25.1 | 11-25 12:41 | closed by owner | -6.0 | owner | -0.3 / 9.8 | IG |
| 68 | 11-25 15:00 | breakout | SELL | 13053.1 | 6 | 11-25 15:00 | stopped by IG | -6.0 | bot | -2.1 / 10.3 | IG |
| 69 | 11-25 15:05 | session sweep | BUY | 13063.2 | 18.2 | 11-25 19:36 | stopped by IG | 61.4 | bot | 66.0 / 9.1 | IG |
| 70 | 11-25 17:06 | Bollinger bounce 5m | BUY | 13108.9 | 12 | 11-25 17:40 | close | 4.7 | bot | 11.9 / 5.3 | open IG (deal id); close: bot record, no saved IG evidence |
| 71 | 11-25 18:02 | slow grind | BUY | 13120.5 | 15 | 11-25 22:00 | closed at IG | -15.0 | bot | 8.7 / 14.2 | IG activity (orphan, booked at start-up 27 Nov) |
| 72 | 11-25 18:45 | slow grind | BUY | 13128.7 | 15 | 11-25 20:30 | forced close | -5.1 | bot | 0.2 / 9.1 | IG |
| 73 | 11-25 19:10 | EMA pullback | BUY | 13128.8 | 12 | 11-25 20:30 | forced close | -5.7 | bot | 0.1 / 9.2 | IG |
| 74 | 11-25 20:05 | Bollinger bounce 5m | SELL | 13120.1 | 12 | 11-25 20:30 | forced close | -4.4 | bot | -3.2 / 6.5 | IG |
| 75 | 11-26 06:01 | Bollinger bounce 5m | BUY | 13103.9 | 12 | 11-26 09:20 | stopped by IG | 5.0 | bot | 9.1 / 8.2 | IG 09:35:01 13108.9, +5.0 (record +4.5, R5) |
| 76 | 11-26 06:30 | Bollinger bounce 5m | SELL | 13099.7 | 12 | 11-26 07:20 | close | -7.3 | bot | 1.4 / 8.0 | open IG (deal id); close: bot record, no saved IG evidence |
| 77 | 11-26 11:40 | Bollinger bounce 5m | BUY | 13102.2 | 12 | 11-26 14:25 | close | 14.0 | bot | 20.7 / 6.5 | open IG (deal id); close: bot record, no saved IG evidence |
| 78 | 11-26 11:45 | breakout | SELL | 13099.1 | 6 | 11-26 12:08 | stopped by IG | -6.0 | bot | 1.9 / 5.9 | IG |
| 79 | 11-26 11:55 | slow grind | SELL | 13096.7 | 15 | 11-26 13:38 | stopped by IG | -15.0 | bot | -1.6 / 14.1 | IG |
| 80 | 11-26 12:51 | Bollinger bounce 5m | SELL | 13104.2 | 12 | 11-26 13:40 | close | -6.4 | bot | 4.7 / 8.0 | open IG (deal id); close: bot record, no saved IG evidence |
| 81 | 11-26 14:22 | Bollinger bounce 5m | SELL | 13114.7 | 12 | 11-26 15:10 | close | 2.1 | bot | 10.6 / 3.3 | open IG (deal id); close: bot record, no saved IG evidence |
| 82 | 11-27 06:55 | Bollinger bounce 5m | BUY | 13125.9 | 12 | 11-27 07:20 | close | -2.0 | bot | 3.6 / 4.2 | open IG (deal id); close: bot record, no saved IG evidence |
| 83 | 11-27 10:00 | breakout | BUY | 13127.8 | 6 | 11-27 10:03 | stopped by IG | -6.0 | bot | -1.2 / 8.0 | IG |
| 84 | 11-27 12:01 | Bollinger bounce 5m | BUY | 13132.0 | 12 | 11-27 12:05 | closed by owner | -1.4 | owner | — | IG |
| 85 | 11-27 15:11 | Bollinger bounce 5m | SELL | 13106.7 | 12 | 11-27 16:20 | closed by owner | 9.0 | owner | 11.1 / 4.1 | IG |
| 86 | 11-27 15:47 | slow grind | SELL | 13102.0 | 15 | 11-27 16:20 | closed by owner | 4.3 | owner | 6.4 / 6.3 | IG |


## 1.7 Table B1 — structural context at the entry, 25–27 Nov (only what was known then)

SCA state = the proposed assessment (§3), computed by `evidence/scripts/classify2.py`. Positions are measured in the trade's own direction: *ahead* = in the trade's path; *at* = inside, or within NEAR (3 pips) past the far edge; *past* = more than NEAR beyond the far edge; *near ahead* = within NEAR before the near edge. Members list each STP opportunity on the zone: id suffix, its trade label, status, `held` = the break was held, `brk-up/down` = the direction of STP's D-20 break. Room R is the separate room rule (§3.9): room to the nearest live opposing zone ahead vs the trade's own stop.

| # | Opened | Strategy | Dir | Analyser | SCA state | Zones at/near the entry (members: id, label, status) | Room R (pips vs stop) | Opposite bot position open |
|---|---|---|---|---|---|---|---|---|
| 63 | 11-25 03:37 | slow grind | SELL | trend | **S2 neutral** | — | — | — |
| 64 | 11-25 07:40 | Asian range breakout | SELL | consolidation | **S2 neutral** | 13084.1–13093.0 past 5.0: — (0400-27 SELL ACTIVE) | — | — |
| 65 | 11-25 08:05 | breakout | SELL | consolidation | **S2 neutral** | 13084.1–13093.0 past 12.5: — (0400-27 SELL ACTIVE) | — | — |
| 66 | 11-25 11:00 | EMA pullback | SELL | trend | **S2 neutral** | 13047.3–13053.7 ahead 11.3: — (1000-28 BUY WAITING)<br>13082.6–13093.0 past 17.6: — (0400-27 SELL ACTIVE) | 11.3 vs 12 **refuse** (R-b: refuse) | — |
| 67 | 11-25 12:25 | session sweep | BUY | consolidation | **S4 within unresolved opposing** | 13071.5–13080.7 at: S4_WITHIN_OPPOSING (1200-29 SELL ACTIVE) | — | — |
| 68 | 11-25 15:00 | breakout | SELL | emerging trend | **S2 neutral** | — | — | — |
| 69 | 11-25 15:05 | session sweep | BUY | emerging trend | **S2 neutral** | 13046.1–13053.7 past 8.1: — (1500-32 BUY WAITING) | — | — |
| 70 | 11-25 17:06 | Bollinger bounce 5m | BUY | trend | **S2 neutral** | 13084.1–13096.0 past 10.9: — (1700-34 BUY WAITING) | — | — |
| 71 | 11-25 18:02 | slow grind | BUY | trend | **S4 within unresolved opposing** | 13084.1–13093.0 past 26.0: — (1700-34 BUY WAITING)<br>13115.1–13123.9 at: S4_WITHIN_OPPOSING (1800-35 SELL WAITING) | — | — |
| 72 | 11-25 18:45 | slow grind | BUY | trend | **S4 within unresolved opposing** | 13115.1–13123.9 past 3.2: S4_WITHIN_OPPOSING (1800-35 SELL ACTIVE) | — | — |
| 73 | 11-25 19:10 | EMA pullback | BUY | trend | **S4 within unresolved opposing** | 13115.1–13123.9 at: S4_WITHIN_OPPOSING (1800-35 SELL ACTIVE) | — | — |
| 74 | 11-25 20:05 | Bollinger bounce 5m | SELL | trend | **S1 aligned** | 13115.1–13123.9 at: S1_ALIGNED (1800-35 SELL ACTIVE) | — | #71 slow grind buy, #72 slow grind buy, #73 EMA pullback buy |
| 75 | 11-26 06:01 | Bollinger bounce 5m | BUY | emerging trend | **S5 confirmed rejection** | 13093.0–13103.0 at: S5_CONFIRMED_REJECTION (0000-37 BUY ACTIVE; 0400-38 SELL ACTIVE) | — | — |
| 76 | 11-26 06:30 | Bollinger bounce 5m | SELL | consolidation | **S5 confirmed rejection** | 13093.0–13103.0 at: S5_CONFIRMED_REJECTION (0000-37 BUY ACTIVE; 0400-38 SELL ACTIVE) | — | #75 Bollinger bounce 5m buy |
| 77 | 11-26 11:40 | Bollinger bounce 5m | BUY | trend | **S6 confirmed break** | 13093.0–13103.0 at: S6_CONFIRMED_BREAK (0000-37 BUY ACTIVE; 0400-38 SELL BROKEN brk-up; 1000-39 BUY ACTIVE; 1100-41 BUY ACTIVE) | — | — |
| 78 | 11-26 11:45 | breakout | SELL | trend | **S4 within unresolved opposing** | 13093.0–13103.0 at: S4_WITHIN_OPPOSING (0000-37 BUY ACTIVE; 0400-38 SELL BROKEN brk-up; 1000-39 BUY ACTIVE; 1100-41 BUY ACTIVE) | — | #77 Bollinger bounce 5m buy |
| 79 | 11-26 11:55 | slow grind | SELL | trend | **S4 within unresolved opposing** | 13093.0–13103.0 at: S4_WITHIN_OPPOSING (0000-37 BUY ACTIVE; 0400-38 SELL BROKEN brk-up; 1000-39 BUY ACTIVE; 1100-41 BUY ACTIVE) | — | #77 Bollinger bounce 5m buy |
| 80 | 11-26 12:51 | Bollinger bounce 5m | SELL | consolidation | **S3 approaching opposing** | 13093.0–13103.0 near ahead 1.6: S3_APPROACHING (0000-37 BUY ACTIVE; 0400-38 SELL ACTIVE; 1000-39 BUY ACTIVE; 1100-41 BUY ACTIVE; 1200-42 SELL ACTIVE; 1200-43 BUY ACTIVE) | 1.6 vs 12 **refuse** (R-b: permit) | #77 Bollinger bounce 5m buy |
| 81 | 11-26 14:22 | Bollinger bounce 5m | SELL | trend | **S1 aligned** | 13093.0–13103.0 ahead 11.8: — (0000-37 BUY ACTIVE; 0400-38 SELL BROKEN brk-up; 1000-39 BUY ACTIVE; 1100-41 BUY ACTIVE; 1200-42 SELL BROKEN brk-up; 1200-43 BUY ACTIVE)<br>13115.1–13123.9 at: S1_ALIGNED (1400-44 SELL ACTIVE) | 11.8 vs 12 **refuse** (R-b: refuse) | #77 Bollinger bounce 5m buy |
| 82 | 11-27 06:55 | Bollinger bounce 5m | BUY | emerging trend | **S6 confirmed break** | 13093.0–13103.0 past 21.3: S7_CONTINUATION (0400-38 SELL INVALIDATED held brk-up; 1200-42 SELL INVALIDATED held brk-up; 0100-51 SELL INVALIDATED held brk-up)<br>13108.5–13119.1 past 5.2: S6_CONFIRMED_BREAK (0200-53 SELL BROKEN brk-up)<br>13121.3–13130.6 at: S1_ALIGNED (0300-56 BUY ACTIVE) | — | — |
| 83 | 11-27 10:00 | breakout | BUY | consolidation | **S7 continuation after break** | 13093.0–13103.0 past 23.3: S7_CONTINUATION (0400-38 SELL INVALIDATED held brk-up; 1200-42 SELL INVALIDATED held brk-up; 0100-51 SELL INVALIDATED held brk-up)<br>13108.5–13119.1 past 7.2: S7_CONTINUATION (0200-53 SELL INVALIDATED held brk-up)<br>13121.3–13130.4 at: S1_ALIGNED (0300-56 BUY ACTIVE) | — | — |
| 84 | 11-27 12:01 | Bollinger bounce 5m | BUY | emerging trend | **S7 continuation after break** | 13093.0–13103.0 past 27.0: S7_CONTINUATION (0400-38 SELL INVALIDATED held brk-up; 1200-42 SELL INVALIDATED held brk-up; 0100-51 SELL INVALIDATED held brk-up)<br>13108.5–13119.1 past 10.9: S7_CONTINUATION (0200-53 SELL INVALIDATED held brk-up)<br>13121.3–13130.3 at: S1_ALIGNED (1200-57 BUY WAITING) | — | — |
| 85 | 11-27 15:11 | Bollinger bounce 5m | SELL | trend | **S5 confirmed rejection** | 13093.0–13103.0 ahead 3.5: — (0400-38 SELL INVALIDATED held brk-up; 1200-42 SELL INVALIDATED held brk-up; 0100-51 SELL INVALIDATED held brk-up)<br>13108.5–13119.1 at: S5_CONFIRMED_REJECTION (0200-53 SELL INVALIDATED held brk-up; 1500-59 SELL ACTIVE; 1500-60 BUY ACTIVE)<br>13121.3–13130.3 past 14.8: S6_CONFIRMED_BREAK (1305-58 BUY BROKEN brk-down) | — | — |
| 86 | 11-27 15:47 | slow grind | SELL | trend | **S4 within unresolved opposing** | 13093.0–13103.0 at: — (0400-38 SELL INVALIDATED held brk-up; 1200-42 SELL INVALIDATED held brk-up; 0100-51 SELL INVALIDATED held brk-up)<br>13108.5–13119.1 past 5.9: S4_WITHIN_OPPOSING (0200-53 SELL INVALIDATED held brk-up; 1500-60 BUY ACTIVE)<br>13121.3–13130.3 past 18.7: S6_CONFIRMED_BREAK (1305-58 BUY BROKEN brk-down) | — | — |


## 1.8 Table A2 — execution record, 18–24 Nov

| # | Opened UTC | Strategy | Dir | Fill | Stop pips | Closed UTC | How closed | Pips | By | MFE / MAE | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 11-18 07:30 | Asian range breakout | SELL | 13180.2 | 12 | 11-18 09:25 | stopped by IG | 21.7 | bot | 30.7 / -1.4 | IG |
| 2 | 11-18 09:30 | Bollinger bounce | BUY | 13163.1 | 12 | 11-18 11:03 | stopped by IG | 7.2 | bot | 12.5 / -0.4 | IG |
| 3 | 11-18 12:37 | EMA pullback | SELL | 13156.4 | 12 | 11-18 13:07 | stopped by IG | -12.0 | bot | 5.2 / 10.6 | IG 13168.4, -12.0 (record -12.6, R6) |
| 4 | 11-18 15:44 | breakout | SELL | 13152.9 | 12 | 11-18 22:58 | stopped by IG | -12.0 | bot | 16.1 / 9.4 | IG |
| 5 | 11-18 16:20 | EMA pullback | SELL | 13141.1 | 12 | 11-18 16:58 | stopped by IG | -12.0 | bot | 3.5 / 9.4 | IG |
| 6 | 11-18 16:37 | slow grind | SELL | 13138.1 | 15 | 11-18 16:58 | stopped by IG | -15.0 | bot | 0.5 / 12.4 | IG |
| 7 | 11-18 19:50 | level reversal | SELL | 13135.8 | 11.3 | 11-18 20:19 | stopped by IG | -11.3 | bot | -2.3 / 7.5 | IG |
| 8 | 11-19 07:35 | Asian range breakout | BUY | 13156.5 | 12 | 11-19 09:27 | stopped by IG | -12.0 | bot | 4.2 / 10.6 | IG |
| 9 | 11-19 11:00 | slow grind | BUY | 13170.0 | 15 | 11-19 11:57 | stopped by IG | -15.0 | bot | -0.1 / 13.4 | IG |
| 10 | 11-19 12:10 | session sweep | SELL | 13150.9 | 22 | 11-19 15:50 | stopped by IG | 28.9 | bot | 42.2 / 15.0 | IG |
| 11 | 11-19 15:40 | Bollinger bounce | BUY | 13118.8 | 12 | 11-19 16:29 | stopped by IG | -12.0 | bot | 5.3 / 11.0 | IG |
| 12 | 11-19 17:20 | Bollinger bounce | BUY | 13107.4 | 12 | 11-19 17:52 | closed by owner | 0.4 | owner | 5.6 / 2.6 | IG |
| 13 | 11-19 19:33 | level reversal | BUY | 13104.4 | 12.6 | 11-19 20:16 | closed by owner | -3.5 | owner | -1.9 / 12.2 | IG |
| 14 | 11-19 19:51 | EMA pullback | SELL | 13094.5 | 12 | 11-19 20:16 | closed by owner | -7.9 | owner | -1.8 / 8.5 | IG |
| 15 | 11-20 06:07 | level reversal | BUY | 13111.4 | 17.3 | 11-20 11:59 | stopped by IG | -17.3 | bot | 10.5 / 13.5 | IG |
| 16 | 11-20 07:15 | Asian range breakout | BUY | 13122.3 | 12 | 11-20 08:00 | stopped by IG | -12.0 | bot | -1.0 / 11.0 | IG |
| 17 | 11-20 07:25 | Bollinger bounce 5m | SELL | 13114.8 | 12 | 11-20 07:45 | close | -1.7 | bot | 2.0 / 6.3 | IG |
| 18 | 11-20 07:30 | session sweep | SELL | 13113.5 | 12 | 11-20 09:13 | stopped by IG | 7.5 | bot | 13.6 / 9.3 | IG |
| 19 | 11-20 13:10 | level reversal | BUY | 13127.7 | 34.3 | 11-20 16:11 | closed by owner | -26.1 | owner | -0.5 / 31.5 | IG |
| 20 | 11-20 13:25 | slow grind | BUY | 13128.3 | 15 | 11-20 13:41 | stopped by IG | -15.0 | bot | -6.1 / 14.6 | IG |
| 21 | 11-20 13:30 | Bollinger bounce | SELL | 13120.1 | 12 | 11-20 14:32 | stopped by IG | 2.9 | bot | 13.0 / 2.8 | IG |
| 22 | 11-20 13:32 | Bollinger bounce 5m | SELL | 13118.1 | 12 | 11-20 14:35 | close | 0.0 | bot | 11.0 / 4.8 | IG |
| 23 | 11-20 13:35 | session sweep | SELL | 13116.1 | 12 | 11-20 15:14 | stopped by IG | 0.9 | bot | 12.1 / 6.8 | IG |
| 24 | 11-20 14:45 | Bollinger bounce 5m | SELL | 13107.1 | 12 | 11-20 15:44 | stopped by IG | -12.0 | bot | 3.1 / 9.7 | IG |
| 25 | 11-20 17:55 | level reversal | SELL | 13096.0 | 13 | 11-20 18:43 | closed by owner | 2.9 | owner | 0.9 / 6.4 | IG |
| 26 | 11-20 18:42 | EMA pullback | SELL | 13091.4 | 12 | 11-20 18:43 | closed by owner | -1.4 | owner | 0.2 / 4.4 | IG |
| 27 | 11-20 18:45 | level reversal | SELL | 13088.9 | 14.4 | 11-20 20:30 | forced close | 3.7 | bot | 5.4 / 9.6 | open IG (deal id); close: bot record, no saved IG evidence |
| 28 | 11-20 19:31 | breakout | SELL | 13084.6 | 6 | 11-20 19:38 | stopped by IG | -6.0 | bot | -0.9 / 8.2 | IG |
| 29 | 11-23 01:47 | slow grind | BUY | 13110.2 | 15 | 11-23 06:46 | take profit hit at IG | 20.0 | bot | 17.2 / 7.2 | IG |
| 30 | 11-23 06:00 | level reversal | BUY | 13123.7 | 14.6 | 11-23 10:15 | stopped by IG | -14.6 | bot | 18.4 / 13.6 | IG |
| 31 | 11-23 06:45 | EMA pullback | BUY | 13130.1 | 12 | 11-23 08:03 | stopped by IG | -12.0 | bot | 1.0 / 10.5 | IG |
| 32 | 11-23 09:00 | Asian range breakout | BUY | 13133.6 | 12 | 11-23 09:30 | stopped by IG | -12.0 | bot | -4.2 / 10.9 | IG |
| 33 | 11-23 09:05 | Bollinger bounce | SELL | 13127.4 | 12 | 11-23 10:42 | stopped by IG | 14.8 | bot | 22.8 / 3.5 | IG |
| 34 | 11-23 09:10 | session sweep | SELL | 13124.8 | 18.4 | 11-23 10:42 | stopped by IG | 12.2 | bot | 20.2 / 5.6 | IG |
| 35 | 11-23 10:21 | level reversal | SELL | 13105.7 | 19.9 | 11-23 12:45 | take profit hit at IG | 20.0 | bot | 18.2 / 10.6 | IG |
| 36 | 11-23 10:42 | Bollinger bounce 5m | BUY | 13112.6 | 12 | 11-23 11:05 | close | -7.3 | bot | 2.2 / 8.7 | open IG (deal id); close: bot record, no saved IG evidence |
| 37 | 11-23 10:57 | slow grind | SELL | 13105.6 | 15 | 11-23 12:45 | take profit hit at IG | 20.0 | bot | 18.1 / 3.5 | IG |
| 38 | 11-23 12:26 | Bollinger bounce 5m | BUY | 13098.9 | 12 | 11-23 12:43 | stopped by IG | -12.0 | bot | 1.0 / 7.1 | IG |
| 39 | 11-23 12:30 | session sweep | BUY | 13099.4 | 13.5 | 11-23 12:45 | stopped by IG | -13.5 | bot | 0.5 / 13.4 | IG |
| 40 | 11-23 13:00 | Bollinger bounce 5m | BUY | 13084.4 | 12 | 11-23 13:09 | stopped by IG | -12.0 | bot | -0.5 / 12.8 | IG |
| 41 | 11-23 14:25 | New York open reversal | BUY | 13078.3 | 12 | 11-23 14:37 | stopped by IG | -12.0 | bot | 0.6 / 10.6 | IG |
| 42 | 11-23 14:25 | level reversal | BUY | 13078.4 | 21.4 | 11-23 14:44 | stopped by IG | -21.4 | bot | -3.0 / 17.0 | IG |
| 43 | 11-23 14:39 | EMA pullback | SELL | 13061.7 | 12 | 11-23 15:13 | take profit hit at IG | 30.0 | bot | 24.2 / 5.3 | IG |
| 44 | 11-23 14:50 | level reversal | SELL | 13054.6 | 22.8 | 11-23 15:13 | take profit hit at IG | 20.0 | bot | 17.1 / 5.4 | IG |
| 45 | 11-23 15:30 | Bollinger bounce | BUY | 13045.1 | 12 | 11-23 15:50 | stopped by IG | -12.0 | bot | 6.1 / 7.5 | IG |
| 46 | 11-23 15:30 | Bollinger bounce 5m | BUY | 13045.3 | 12 | 11-23 15:50 | stopped by IG | -12.0 | bot | 5.9 / 7.7 | IG |
| 47 | 11-23 15:54 | EMA pullback | SELL | 13028.8 | 12 | 11-23 18:36 | closed by owner | 6.7 | owner | 17.3 / 4.3 | IG |
| 48 | 11-23 16:10 | Bollinger bounce | BUY | 13027.0 | 12 | 11-23 16:15 | stopped by IG | -12.0 | bot | -0.4 / 14.5 | IG |
| 49 | 11-23 16:15 | slow grind | SELL | 13016.0 | 15 | 11-23 18:36 | closed by owner | -6.1 | owner | 4.5 / 10.8 | IG |
| 50 | 11-23 16:35 | Bollinger bounce | BUY | 13023.3 | 12 | 11-23 17:48 | stopped by IG | -12.0 | bot | 2.0 / 11.9 | IG |
| 51 | 11-23 17:00 | Bollinger bounce 5m | BUY | 13022.8 | 12 | 11-23 17:48 | stopped by IG | -12.0 | bot | 2.5 / 7.7 | IG |
| 52 | 11-23 18:00 | Bollinger bounce | BUY | 13015.6 | 12 | 11-23 18:36 | closed by owner | 5.9 | owner | 6.7 / 2.4 | IG |
| 53 | 11-23 18:01 | Bollinger bounce 5m | BUY | 13017.4 | 12 | 11-23 18:36 | closed by owner | 4.1 | owner | 4.9 / 4.2 | IG |
| 54 | 11-24 07:15 | session sweep | BUY | 13039.6 | 13.7 | 11-24 07:55 | closed by owner | -2.3 | owner | 2.9 / 5.7 | IG |
| 55 | 11-24 08:55 | breakout | BUY | 13051.8 | 6 | 11-24 13:05 | take profit hit at IG | 50.0 | bot | 49.2 / 4.3 | open IG (deal id); close: bot record, no saved IG evidence |
| 56 | 11-24 08:55 | Asian range breakout | BUY | 13052.4 | 12 | 11-24 10:20 | stopped by IG | 8.4 | bot | 18.7 / 4.9 | IG |
| 57 | 11-24 08:55 | slow grind | BUY | 13052.5 | 15 | 11-24 10:02 | close | 10.0 | bot | 16.0 / 5.0 | open IG (deal id); close: bot record, no saved IG evidence |
| 58 | 11-24 12:39 | slow grind | BUY | 13091.5 | 15 | 11-24 14:30 | closed by owner | 8.9 | owner | 14.5 / 3.2 | IG |
| 59 | 11-24 13:20 | Bollinger bounce | SELL | 13096.9 | 12 | 11-24 14:36 | stopped by IG | -12.0 | bot | 7.1 / 10.5 | IG |
| 60 | 11-24 13:32 | Bollinger bounce 5m | SELL | 13092.8 | 12 | 11-24 14:10 | close | -8.2 | bot | 0.8 / 11.2 | open IG (deal id); close: bot record, no saved IG evidence |
| 61 | 11-24 13:32 | level reversal | SELL | 13091.5 | 16.6 | 11-24 14:35 | stopped by IG | -16.6 | bot | -0.5 / 15.9 | IG |
| 62 | 11-24 15:30 | level reversal | BUY | 13114.2 | 18.3 | 11-24 20:30 | forced close | 1.4 | bot | 9.7 / 15.8 | open IG (deal id); close: bot record, no saved IG evidence |


## 1.9 Table B2 — structural context at the entry, 18–24 Nov

18–19 Nov: STP had no live opportunity at any of these entries (its direction was NEUTRAL from 18 Nov 08:00; see the 19 Nov RCA). Every trade is S2 by construction.

| # | Opened | Strategy | Dir | Analyser | SCA state | Zones at/near the entry (members: id, label, status) | Room R (pips vs stop) | Opposite bot position open |
|---|---|---|---|---|---|---|---|---|
| 1 | 11-18 07:30 | Asian range breakout | SELL | emerging trend | **S2 neutral** | — | — | — |
| 2 | 11-18 09:30 | Bollinger bounce | BUY | trend | **S2 neutral** | — | — | — |
| 3 | 11-18 12:37 | EMA pullback | SELL | trend | **S2 neutral** | — | — | — |
| 4 | 11-18 15:44 | breakout | SELL | emerging trend | **S2 neutral** | — | — | — |
| 5 | 11-18 16:20 | EMA pullback | SELL | trend | **S2 neutral** | — | — | — |
| 6 | 11-18 16:37 | slow grind | SELL | trend | **S2 neutral** | — | — | — |
| 7 | 11-18 19:50 | level reversal | SELL | trend | **S2 neutral** | — | — | — |
| 8 | 11-19 07:35 | Asian range breakout | BUY | trend | **S2 neutral** | — | — | — |
| 9 | 11-19 11:00 | slow grind | BUY | trend | **S2 neutral** | — | — | — |
| 10 | 11-19 12:10 | session sweep | SELL | emerging trend | **S2 neutral** | — | — | — |
| 11 | 11-19 15:40 | Bollinger bounce | BUY | emerging trend | **S2 neutral** | — | — | #10 session sweep sell |
| 12 | 11-19 17:20 | Bollinger bounce | BUY | emerging trend | **S2 neutral** | — | — | — |
| 13 | 11-19 19:33 | level reversal | BUY | emerging trend | **S2 neutral** | — | — | — |
| 14 | 11-19 19:51 | EMA pullback | SELL | emerging trend | **S2 neutral** | — | — | #13 level reversal buy |
| 15 | 11-20 06:07 | level reversal | BUY | emerging trend | **S2 neutral** | — | — | — |
| 16 | 11-20 07:15 | Asian range breakout | BUY | trend | **S2 neutral** | — | — | — |
| 17 | 11-20 07:25 | Bollinger bounce 5m | SELL | emerging trend | **S2 neutral** | — | — | #15 level reversal buy, #16 Asian range breakout buy |
| 18 | 11-20 07:30 | session sweep | SELL | emerging trend | **S2 neutral** | — | — | #15 level reversal buy, #16 Asian range breakout buy |
| 19 | 11-20 13:10 | level reversal | BUY | trend | **S4 within unresolved opposing** | 13111.6–13121.9 past 4.3: S4_WITHIN_OPPOSING (-1300-8 SELL ACTIVE) | — | — |
| 20 | 11-20 13:25 | slow grind | BUY | trend | **S4 within unresolved opposing** | 13111.6–13121.9 past 5.0: S4_WITHIN_OPPOSING (-1300-8 SELL ACTIVE) | — | — |
| 21 | 11-20 13:30 | Bollinger bounce | SELL | trend | **S1 aligned** | 13111.6–13121.9 at: S1_ALIGNED (-1300-8 SELL ACTIVE) | — | #19 level reversal buy, #20 slow grind buy |
| 22 | 11-20 13:32 | Bollinger bounce 5m | SELL | trend | **S1 aligned** | 13111.6–13121.9 at: S1_ALIGNED (-1300-8 SELL ACTIVE) | — | #19 level reversal buy, #20 slow grind buy |
| 23 | 11-20 13:35 | session sweep | SELL | trend | **S1 aligned** | 13111.6–13121.9 at: S1_ALIGNED (-1300-8 SELL ACTIVE) | — | #19 level reversal buy, #20 slow grind buy |
| 24 | 11-20 14:45 | Bollinger bounce 5m | SELL | trend | **S2 neutral** | 13111.6–13121.9 past 4.2: — (-1300-8 SELL ACTIVE) | — | #19 level reversal buy |
| 25 | 11-20 17:55 | level reversal | SELL | emerging trend | **S2 neutral** | 13111.6–13121.9 past 15.5: — (-1300-8 SELL ACTIVE) | — | — |
| 26 | 11-20 18:42 | EMA pullback | SELL | emerging trend | **S2 neutral** | 13111.6–13121.9 past 19.3: — (-1300-8 SELL WAITING) | — | — |
| 27 | 11-20 18:45 | level reversal | SELL | emerging trend | **S2 neutral** | 13111.6–13121.9 past 21.9: — (-1300-8 SELL WAITING) | — | — |
| 28 | 11-20 19:31 | breakout | SELL | emerging trend | **S2 neutral** | — | — | — |
| 29 | 11-23 01:47 | slow grind | BUY | trend | **S2 neutral** | 13113.2–13121.9 ahead 4.1: — (0100-10 SELL ACTIVE) | 4.1 vs 15 **refuse** (R-b: refuse) | — |
| 30 | 11-23 06:00 | level reversal | BUY | emerging trend | **S4 within unresolved opposing** | 13113.2–13123.7 at: S4_WITHIN_OPPOSING (0100-10 SELL ACTIVE) | — | — |
| 31 | 11-23 06:45 | EMA pullback | BUY | emerging trend | **S4 within unresolved opposing** | 13113.2–13123.7 past 4.5: S4_WITHIN_OPPOSING (0100-10 SELL ACTIVE) | — | — |
| 32 | 11-23 09:00 | Asian range breakout | BUY | consolidation | **S2 neutral** | — | — | — |
| 33 | 11-23 09:05 | Bollinger bounce | SELL | consolidation | **S1 aligned** | 13127.3–13135.6 at: S1_ALIGNED (0900-11 SELL WAITING) | — | #30 level reversal buy, #32 Asian range breakout buy |
| 34 | 11-23 09:10 | session sweep | SELL | consolidation | **S2 neutral** | — | — | #30 level reversal buy, #32 Asian range breakout buy |
| 35 | 11-23 10:21 | level reversal | SELL | trend | **S2 neutral** | — | — | — |
| 36 | 11-23 10:42 | Bollinger bounce 5m | BUY | trend | **S2 neutral** | — | — | #35 level reversal sell |
| 37 | 11-23 10:57 | slow grind | SELL | trend | **S2 neutral** | — | — | #36 Bollinger bounce 5m buy |
| 38 | 11-23 12:26 | Bollinger bounce 5m | BUY | trend | **S4 within unresolved opposing** | 13087.6–13097.1 at: S4_WITHIN_OPPOSING (1200-13 SELL ACTIVE) | — | #35 level reversal sell, #37 slow grind sell |
| 39 | 11-23 12:30 | session sweep | BUY | trend | **S4 within unresolved opposing** | 13087.6–13097.1 at: S4_WITHIN_OPPOSING (1200-13 SELL ACTIVE) | — | #35 level reversal sell, #37 slow grind sell |
| 40 | 11-23 13:00 | Bollinger bounce 5m | BUY | emerging trend | **S4 within unresolved opposing** | 13075.0–13084.1 at: S4_WITHIN_OPPOSING (1300-14 SELL WAITING) | — | — |
| 41 | 11-23 14:25 | New York open reversal | BUY | emerging trend | **S2 neutral** | — | — | — |
| 42 | 11-23 14:25 | level reversal | BUY | emerging trend | **S2 neutral** | — | — | — |
| 43 | 11-23 14:39 | EMA pullback | SELL | emerging trend | **S2 neutral** | — | — | #42 level reversal buy |
| 44 | 11-23 14:50 | level reversal | SELL | trend | **S2 neutral** | — | — | — |
| 45 | 11-23 15:30 | Bollinger bounce | BUY | emerging trend | **S2 neutral** | — | — | — |
| 46 | 11-23 15:30 | Bollinger bounce 5m | BUY | emerging trend | **S2 neutral** | — | — | — |
| 47 | 11-23 15:54 | EMA pullback | SELL | emerging trend | **S2 neutral** | — | — | — |
| 48 | 11-23 16:10 | Bollinger bounce | BUY | trend | **S2 neutral** | — | — | #47 EMA pullback sell |
| 49 | 11-23 16:15 | slow grind | SELL | trend | **S2 neutral** | — | — | #48 Bollinger bounce buy |
| 50 | 11-23 16:35 | Bollinger bounce | BUY | trend | **S2 neutral** | — | — | #47 EMA pullback sell, #49 slow grind sell |
| 51 | 11-23 17:00 | Bollinger bounce 5m | BUY | trend | **S2 neutral** | — | — | #47 EMA pullback sell, #49 slow grind sell |
| 52 | 11-23 18:00 | Bollinger bounce | BUY | trend | **S2 neutral** | — | — | #47 EMA pullback sell, #49 slow grind sell |
| 53 | 11-23 18:01 | Bollinger bounce 5m | BUY | trend | **S2 neutral** | — | — | #47 EMA pullback sell, #49 slow grind sell |
| 54 | 11-24 07:15 | session sweep | BUY | consolidation | **S2 neutral** | — | 36.7 vs 13.7 | — |
| 55 | 11-24 08:55 | breakout | BUY | trend | **S2 neutral** | — | — | — |
| 56 | 11-24 08:55 | Asian range breakout | BUY | trend | **S2 neutral** | — | — | — |
| 57 | 11-24 08:55 | slow grind | BUY | trend | **S2 neutral** | — | — | — |
| 58 | 11-24 12:39 | slow grind | BUY | trend | **S2 neutral** | — | — | — |
| 59 | 11-24 13:20 | Bollinger bounce | SELL | possible reversal | **S2 neutral** | 13135.5–13142.1 past 39.1: — (1300-20 SELL WAITING) | — | #58 slow grind buy |
| 60 | 11-24 13:32 | Bollinger bounce 5m | SELL | emerging trend | **S2 neutral** | 13135.5–13142.1 past 41.6: — (1300-20 SELL WAITING) | — | #58 slow grind buy |
| 61 | 11-24 13:32 | level reversal | SELL | emerging trend | **S2 neutral** | 13135.5–13142.1 past 41.6: — (1300-20 SELL WAITING) | — | #58 slow grind buy |
| 62 | 11-24 15:30 | level reversal | BUY | emerging trend | **S2 neutral** | — | 22.5 vs 18.3 | — |
