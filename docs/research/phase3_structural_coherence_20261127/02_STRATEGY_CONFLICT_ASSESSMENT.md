# 2. Strategy-by-strategy structural conflict assessment

The code facts are at production `fadf228`, with file:line references in `evidence/inventory/strategy_admission.md`
(admission path) and `evidence/inventory/stp_states.md` (STP states, gate, Phase 2 differences).
The trade evidence covers 18–27 Nov, from `evidence/output/impact.json`. The idea breadth counts every confirmed
idea that passed `common.check`, one per strategy, direction and 10-minute bucket (`breadth.json`). State codes
are defined in §3.3.

## 2.1 What every strategy shares (observed)

- **The order path** is `common.check` (switch, analyser state, direction rule), then `Trading._place`. There it
  meets the STP gate (three strategies, switch off since 27 Nov 16:26:57), the entry filters (rules 1, 2b, 3,
  R3/S3), `day_directions`, then `OrderSender.place` (safety rules, then IG). The engine sees each idea once per
  strategy, direction and candle. **A refused idea is never retried** (engine.py:269–278, 660–663).
- **No strategy looks at STP zones in the opposite direction.** OD-18 A, approved 24 Nov, says: "no new rule
  against an ungated trade opposite an STP opportunity". OD-33: the gated three need a same-direction zone, and
  nothing checks the other direction.
- **No strategy compares its direction with other strategies' open positions.** `forceOpen: true` opens an
  independent opposite position.
- **The only structural filter shared by most strategies is rule 1** (hourly context). It refuses only within
  5 pips of the daily pivot or the hourly 50 EMA, against the hourly context. Breakouts are exempt.
- **No strategy checks the room to the next opposing level.** ROOM_TO_LEVEL exists only on the unmerged branch
  `room-to-level` (1f4038d), for the breakouts and daily pivot/R/S levels.

## 2.2 Per strategy

### EMA Pullback (continuation)
- **Admission.** TREND state only, in the trend's direction. Direction rule, R1, R2b, R3/S3, one at a time, own
  hours. The stop is 12 pips.
- **Structure.** Hourly and 5m EMAs. Pivot and hourly 50 EMA (R1), R3/S3. No STP, no levels.
- **Conflicts.** 9 trades. **S4: 23 Nov 06:45 BUY −12.0** (4.5 pips above SELL 0100-10 ACTIVE 13113.2–123.7,
  no D-20 break: STP broke it at 07:00 from the 06:00 hourly). **S4: 25 Nov 19:10 BUY −5.7** (inside SELL
  1800-35 after an unconfirmed push through it). Room: 25 Nov 11:00 SELL −12.0 had 11.3 pips to BUY 1000-28
  against its 12-pip stop.
- **Legitimate continuation kept.** 23 Nov 14:39 SELL **+30.0**: S2, opposite open position, no STP zone near.
  Owner closes 19 Nov 19:51, 20 Nov 18:42 and 23 Nov 15:54 (+6.7) are all S2.
- **Ideas.** 17 confirmed: 10 S2, 6 S4, 1 S3.
- **Assessment.** The defect is continuation through a touched opposing zone that STP had not yet seen broken.
  The SCA's "past without D-20 break" clause covers it, and STP's own break later releases the continuation. In
  these cases the trend-pullback logic was not wrong. The entry came before the structural evidence.

### Slow Grind (continuation)
- **Admission.** TREND, in its direction. R1. RSI exempt. Own hours (not from 06:00). The stop is 15.
- **Conflicts.** 13 trades. **S4: 20 Nov 13:25 BUY −15.0** (past SELL 1300-8 ACTIVE). **25 Nov 18:02 BUY −15.0**
  (the orphan, inside SELL 1800-35). **25 Nov 18:45 BUY −5.1** (past 1800-35, unconfirmed). **26 Nov 11:55 SELL
  −15.0** (inside BUY 13093–103, against 0400-38's upward D-20 break). **27 Nov 15:47 SELL**, owner close +4.3
  (past BUY 1500-60, 13 minutes before its D-20 break).
- **Healthy trend pullbacks kept.** 23 Nov 10:57 SELL +20 and 24 Nov 08:55 BUY +10 are S2. 25 Nov 03:37 SELL +20
  is S2. 23 Nov 01:47 BUY +20 is S2, but the room rule would refuse it (4.1 pips to SELL 0100-10 vs stop 15).
  See §3.9.
- **Ideas.** 30: 16 S2, 9 S4, 4 S1, 1 S6.
- **Assessment.** This strategy has the most structural conflicts, and 4 of the 5 are its biggest losers (stop
  15). It uses no levels at all. The SCA applies unchanged. After a deferral, the strategy's next own pause-break
  is the fresh confirmation. On 27 Nov that came at 16:05, after the D-20 break (S6), and safety rule "1 open"
  refused it only because the 15:47 trade was still open.

### Bollinger Bounce, hourly (reversal)
- **Admission.** No state check. R1, R2b, R3. One per direction. STP-gated when the switch is on.
- **Conflicts.** 10 trades, none S4. **S1: 20 Nov 13:30 SELL +2.9 and 23 Nov 09:05 SELL +14.8**, a SELL at a SELL
  zone, i.e. a genuine reversal at structure. The 23 Nov 15:30–17:00 BUYs (−12 ×4) were S2. STP had no live
  opportunity during that down-move, so the SCA cannot see them. That is a residual limitation.
- **Ideas.** 27: 20 S2, 3 S1, 2 S5, 1 S6, 1 S3.
- **Assessment.** The SCA affects little here. The losing cluster is the trend-following problem rule 3 targets,
  not a structural one.

### Bollinger Bounce 5m (reversal)
- **Admission.** TREND (against) or POSSIBLE_REVERSAL. R1, R2b, R3. One each way, two in total. STP-gated when
  the switch is on. In production it has no rule-11 key.
- **Triggers.** It fires off any bot level or the 5m band.
- **Conflicts.** 20 trades. **S4: 23 Nov 12:26 BUY −12.0** (inside SELL 1200-13) and **23 Nov 13:00 BUY −12.0**
  (inside SELL 1300-14, created 9 s earlier). **S3: 26 Nov 12:51 SELL −6.4** (1.6 pips above contested zone
  13093–103).
- **Reversals kept.** S5 26 Nov 06:01 BUY +5.0, S5 06:30 SELL −7.3, S6 26 Nov 11:40 BUY **+14.0** (inside the
  zone after STP's upward D-20 break of SELL 0400-38: a retest of broken resistance), S1 25 Nov 20:05, 26 Nov
  14:22 (+2.1), S7 27 Nov 12:01, S5 27 Nov 15:11 (owner +9.0).
- **Ideas.** 167, the noisiest: 51 S2, 38 S4, 24 S7, 20 S5, 13 S1, 13 S6, 8 S3.
- **Assessment.** This is the strategy most exposed to the SCA. 38 of its ideas would be deferred, most of them
  SELLs at the 27 Nov BUY zone that held. The contested-zone exception (S5) keeps its OD-33 behaviour. A
  rejection candle must reach the zone. In production the strategy sets `context.rejection_candle` only while
  STP authorisation is on, so the build must always emit it (§8 WP-2). That is a context field, not a change to
  the confirmation.

### Level Reversal (reversal)
- **Admission.** Any state but consolidation. R1, R2b, R3, R9. The stop is a price (furthest ±6), uncapped. It
  triggers only off S2, R2 and 00-round levels (plus STP zones while gated).
- **Conflicts.** 12 trades. **S4: 23 Nov 06:00 BUY −14.6** (inside SELL 0100-10). **20 Nov 13:10 BUY**, owner
  close −26.1 (past SELL 1300-8, stop 34.3).
- **Reversals kept.** 23 Nov 10:21 SELL +20, 23 Nov 14:50 SELL +20, 20 Nov 18:45 SELL +3.7 (all S2).
- **Ideas.** 109: 59 S2, 18 S4, 12 S5, 10 S7, 5 S1, 5 S6.
- **Assessment.** The SCA applies. Its biggest losses (20 Nov 06:07 −17.3, 23 Nov 14:25 −21.4, 24 Nov 13:32
  −16.6) are S2. They come from its uncapped stop, a stop question outside Phase 3 (constraint: stop
  methodology unchanged). A room rule would not help either: the room check compares against the stop, so a
  wide stop is refused more often, and these losers had no opposing zone ahead.

### Range Trade (reversal)
- **Admission.** RANGING only, R1, R2b. No trade in the window. 1 idea (S2).
- **Assessment.** It applies in principle. There is no evidence either way.

### Breakout (breakout)
- **Admission.** EMERGING or TREND in its direction. Exempt from R1 and R2b. 8-EMA pullback entry. The stop is 6.
- **Conflicts.** 7 trades. **S4: 26 Nov 11:45 SELL −6.0** (inside BUY zones 13093–103, against the upward break).
  27 Nov 10:00 BUY −6.0 is S7 (permitted: lower zones' breaks held; inside a BUY zone).
- **Valid breakouts kept.** **24 Nov 08:55 BUY +50.0** (S2, no opposing zone).
- **Ideas.** 13: 10 S2, 2 S4, 1 S7.
- **Assessment.** The SCA keeps valid breakouts through structure only once STP's own D-20 break exists. A
  breakout into an unresolved opposing zone is deferred, and its pullback window (6 candles) usually expires
  before an hourly break. In practice the deferral works as a refusal. This is a deliberate consequence (§4,
  option B-2). ROOM_TO_LEVEL (approved 19 Nov for this strategy) is separate and remains unmerged.

### Asian Range Breakout (breakout)
- **Admission.** It has the fewest checks: no state, no R1/R2b/R3/R9. Once each way per day.
- **Conflicts.** 6 trades, all S2, including **18 Nov 07:30 SELL +21.7**. 34 ideas, all S2: its 07:00–10:00
  window rarely met a live STP zone.
- **Assessment.** No observed structural conflict. The SCA would apply if one arose.

### Session Sweep (reversal)
- **Admission.** No state check. R1, R3, R9, R10 (one per level per day), R11. The stop is a price, ≥12.
- **Conflicts.** 8 trades. **S4: 23 Nov 12:30 BUY −13.5** (inside SELL 1200-13) and **25 Nov 12:25 BUY**, owner
  close −6.0 (inside SELL 1200-29 13071.5–080.7: it swept the Asian low 13075.5 *into* a live resistance).
- **The 25 Nov 15:05 BUY +61.4 is kept.** It swept the **London** low 13053.7 (a different level from 12:25, so
  R10 is unaffected). At entry, 13061.8, no opposing opportunity was live. The SELL zone 1200-29 that the 12:25
  sweep had bought into reached its destination and completed at 13:10. So it had done its job and was no
  longer live. The only zone
  touching the move was BUY 1500-32 (13046.1–053.7), the swept low itself, which agrees with the trade. State:
  **S2** under every option in §4. Room: no live opposing zone ahead. If the 12:25 idea had been deferred, the
  15:05 setup was still a fresh confirmation of the strategy's own (§6.4).
- **Ideas.** 16: 9 S2, 4 S1, 2 S4, 1 S7.
- **Assessment.** The SCA applies. The two S4 sweeps swept a session level that sat inside a live opposing STP
  zone, which is exactly the "approaching or entering" case. The one profitable sweep in the brief is untouched.

### New York Open Reversal (reversal)
- **Admission.** 13:30–15:00 window, ≥30-pip move. R1, R2b, R3, R9, R10, R11.
- **Conflicts.** 1 trade: 23 Nov 14:25 BUY −12.0, S2. 2 ideas, both S2.
- **Assessment.** No observed structural conflict.

## 2.3 Summary

| Strategy | Trades | S4 trades (bot result) | S3 | Room R refusals | Ideas | Ideas S4 |
|---|---|---|---|---|---|---|
| EMA pullback | 9 | 2 (−12.0, −5.7) | 0 | 1 (−12.0) | 17 | 6 |
| Slow grind | 13 | 4 (−15, −15, −5.1, −15) + 1 owner | 0 | 1 (+20.0) | 30 | 9 |
| Bollinger bounce (1h) | 10 | 0 | 0 | 0 | 27 | 0 |
| Bollinger bounce 5m | 20 | 2 (−12, −12) | 1 (−6.4) | 2 (−6.4, +2.1) | 167 | 38 |
| Level reversal | 12 | 1 (−14.6) + 1 owner | 0 | 0 | 109 | 18 |
| Range trade | 0 | 0 | 0 | 0 | 1 | 0 |
| Breakout | 7 | 1 (−6.0) | 0 | 0 | 13 | 2 |
| Asian range breakout | 6 | 0 | 0 | 0 | 34 | 0 |
| Session sweep | 8 | 1 (−13.5) + 1 owner | 0 | 0 | 16 | 2 |
| NY open reversal | 1 | 0 | 0 | 0 | 2 | 0 |

The table counts trades and ideas. It is not a profitability forecast (§6.1).
