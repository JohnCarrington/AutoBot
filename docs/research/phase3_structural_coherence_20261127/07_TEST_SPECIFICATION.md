# 7. Technical and functional test specification

The house practice applies: failing tests first, then the code. The full suite runs in the pre-commit hook.
Crash/restart tests go at every new persistent boundary (the SCA has none: it is stateless and reads
current.json). Fixtures are built from the real records of the named trades: candles from the store, the STP
state reconstructed from recommendations.jsonl at the entry second.

## 7.1 Technical tests (unit / integration)

| ID | Requirement | Fixture / assertion |
|---|---|---|
| TS-01 | Grouping by zone overlap, edge-only excluded (PD-2/PD-3) | two opps 13093–103 and 13103–113 → two groups; 13093–103 and 13093–103 → one |
| TS-02 | Position in the trade's direction (AHEAD / NEAR_AHEAD / AT / PAST), NEAR = `rejection.near_level_within_pips` read from settings, never a literal | BUY 13126.9 vs 13115.1–123.9 → AT (≤3 past); 13127.1 → PAST 3.2 |
| TS-03 | S4(a) AT an unbroken opposing zone | 25 Nov 18:02 slow grind BUY 13119.0 vs SELL 1800-35 WAITING → S4 |
| TS-04 | S4(b) PAST an ACTIVE opposing zone, no D-20 | 25 Nov 18:45 BUY 13127.1 → S4; same with BROKEN-up → S6 |
| TS-05 | S4(c) against a confirmed break | 26 Nov 11:55 slow grind SELL in 13093–103 with 0400-38 BROKEN up → S4 |
| TS-06 | S5 contested-zone rejection, reversal family only | 26 Nov 06:01 bounce 5m BUY (0000-37 BUY + 0400-38 SELL ACTIVE) → S5; the same idea as slow grind → S4; no rejection candle at the zone → S4 |
| TS-07 | S6 confirmed break in the trade's direction | 26 Nov 11:40 bounce 5m BUY → S6 |
| TS-08 | S7 held break | 27 Nov 10:00 breakout BUY → S7 |
| TS-09 | S3 approaching (record only by default) | 26 Nov 12:51 SELL 13104.6 → S3, permitted under D-1, deferred under D-2 |
| TS-10 | S2 when no structure; the 61.4 sweep | 25 Nov 15:05:01 sweep BUY 13061.8 → S2, permitted (regression guard, named in the brief) |
| TS-11 | Pending D-20 break via `_catch_up` | an hourly close ≥ `zone_break_close` stored but not yet processed by the tracker → S6, not S4 |
| TS-12 | As-of-order-time state; publication race | an opp created at 13:00:03 is visible to an idea at 13:00:12 only if current.json was written before; both orderings are tested, and the result is journalled with `written_utc` |
| TS-13 | Fail open (F-1) | unreadable / stale (> 10 min) / `current: false` → S2 "structure unknown", permitted, journalled |
| TS-14 | Phase 2 semantics | lineage member COMPLETED `after_trade` → ended, not a barrier; an unreconciled opposing member still counts as a barrier; an unreconciled agreeing member gives no S5 |
| TS-15 | Journal shape | `structure refused` + `order` result `structure: watch and wait`, the same fields as `entry filter refused`; permitted ideas get one `idea.steps` line naming the state |
| TS-16 | Switch | STRUCTURAL_COHERENCE off → `_place` byte-identical in behaviour to today (the full suite passes unchanged with the switch off in the test switches) |
| TS-17 | No deferred execution | after a refusal, no queue, timer or file is written; the same idea on the same candle is not re-tried (engine one-try rule) |
| TS-18 | Rule-11 key not consumed | a refused STP-authorised idea leaves `used_signals()` unchanged; a later fresh setup on the same lineage/test is not refused by rule 11 |
| TS-19 | Rejection candle always emitted (WP-2) | bounce 5m and level reversal candidates carry `rejection_candle` with STP_AUTHORISES_ENTRIES off; their trigger prices and times are unchanged against fixtures (no confirmation change) |
| TS-20 | Read-only | the SCA never writes to data/planner; the planner never imports the SCA (mirrors test_stp_final_validation test_10) |
| TS-21 | Room rule independence (only if adopted) | STRUCTURAL_ROOM on/off leaves SCA verdicts unchanged and vice versa; separate journal kind `room refused` |

## 7.2 Functional tests (owner-readable, on real days)

The day is replayed through `Trading` with the switch on. Only the decisions are compared, never P&L.

| ID | Day / trade | Expected |
|---|---|---|
| FS-01 | 25 Nov 15:05 session sweep BUY (+61.4) | opens unchanged: same entry, stop, steps (+ one SCA line) |
| FS-02 | 25 Nov 12:25 session sweep BUY | Watch & Wait (inside SELL 1200-29); the 15:05 sweep still opens |
| FS-03 | 25 Nov 18:45 slow grind and 19:10 EMA pullback BUYs | Watch & Wait (1800-35 unresolved) |
| FS-04 | 26 Nov 06:01 / 06:30 bounce 5m | both open (S5) |
| FS-05 | 26 Nov 11:40 bounce 5m BUY | opens (S6); 11:45 breakout and 11:55 slow grind SELLs → Watch & Wait |
| FS-06 | 23 Nov 14:39 EMA pullback SELL (+30.0) | opens (S2) |
| FS-07 | 24 Nov 08:55 breakout BUY (+50.0) | opens (S2) |
| FS-08 | 27 Nov 13:20–14:23 SELL ideas | Watch & Wait until the 15:00 D-20 break of 1305-58; 15:11 bounce SELL opens (S5) |
| FS-09 | 27 Nov 12:01 bounce 5m BUY at re-issued 1200-57 | opens (S7/S1): legitimate new test after re-arming |
| FS-10 | 18–19 Nov (no live STP) | no SCA refusal all day |
| FS-11 | A planner outage (file removed mid-day) | every idea S2 "structure unknown"; trading unchanged |

## 7.3 Acceptance

- Full suite green with the switch off and on, run once and not concurrently (shared checkout).
- FS-01 … FS-11 as expected.
- An independent code review before deployment, as for Phases 1 and 2.
