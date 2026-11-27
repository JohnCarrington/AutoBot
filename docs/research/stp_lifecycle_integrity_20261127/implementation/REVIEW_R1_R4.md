# Phase 2 independent review findings R1–R4 (review of `087b8c3`, 27 November 2026)

**Owner's decisions applied:** D-R1 and D-R2 approved as recommended, i.e. fail closed where structural evidence is unavailable or a historical test's identity is uncertain.

**Status:**
- R1, R2 and R3 are **confirmed defects**. Each was reproduced on `087b8c3` (`review_R1_R4_tests_before_fix.txt`) and corrected with the smallest change.
- R4 is a documented, tested procedure with one read-only tool.

No forecasting, strategy confirmation, execution integrity (Phase 1) or trade-management behaviour changed. Nothing is deployed, and no configuration or service was touched.

| Finding | Verdict | Correction | Tests |
|---|---|---|---|
| R1: acknowledgement file after a torn write | **confirmed defect** | end a torn last line before appending | TR1-01..04 |
| R2: destination revised while live | **confirmed defect** | the lineage records the destination at the end; migration reads revisions; price-in-zone fallback | TR2-01..06, FL-D1, FL-D2 |
| R3: the most recent finished interval in the catch-up | **confirmed defect** | each finished interval is either stored or seen whole by the engine, else refuse | TR3-01..07 |
| R4: controlled review of D-R1/D-R2 | procedure (fail closed) | `python -m planner.review` (read only) | TR4-01, TR4-02 |

---

## R1: execution acknowledgement crash recovery

**Mechanism on `087b8c3`.**
1. `ExecutionAcks.record` appends `json + "\n"`.
2. A stop mid-write leaves a last line without its newline.
3. At the next start, `read()` skips that malformed line, so the reference is not "seen".
4. The backfill (from the durable order journal) then appends a full acknowledgement **directly after the fragment**. The joined line is malformed too and is skipped again.
5. The acknowledgement is only recovered at a later restart, when the backfill writes once more, this time on a fresh line. Until then the tracker never learns of the execution:
   - the opportunity is not classified "after a confirmed trade entry";
   - the lineage does not record the test as consumed.

   Rule 11 was never affected: its keys come from the order journal.

**Reproduced on `087b8c3`** (`review_R1_R4_tests_before_fix.txt`): after a torn write and a restart, line 1 is `{"reference": "AB-1"{"reference": "AB-1", ...}` (lost). It is recovered only on the second restart.

**Correction** (`orders/executions.py`): before each append, if the file's last byte is not a newline, one is written first. The fragment stays on its own line, as evidence, and is skipped by readers. Nothing else is changed: the order journal is never touched, and readers still take each reference once.

**Tests:**
- TR1-01: torn write, then restart, then backfill: one acknowledgement, and the fragment kept.
- TR1-02: a damaged last line, later confirmed executions, three restarts with backfill: each reference once; the file ends with a newline.
- TR1-03: the tracker takes the backfilled acknowledgement.
- TR1-04: the real order sender. The acknowledgement is torn, the sender restarts, and every earlier order-journal line is unchanged; the backfill restores the acknowledgement.

## R2: destination changes during an opportunity's lifetime

**Trace on `087b8c3`:**
- `member()` records the primary destination (price and zone) at creation.
- `_update_from()` updates the live record's `destinations` at each supporting re-plan.
- `_retire()` updated the member's entry zone and status **but not its primary**.
- `_duplicate_of()` compares a new proposal with the member's primary.
- So a completed opportunity's duplicate protection used **its destination as first published**, not the one achieved.
- The migration (`history()`) also read only the issued destination.

**On the real days:**
- 25 Nov 0400-27 was published toward 13050, revised to 13053.7, and completed at 13053.7.
- 25 Nov 1200-29 was published toward 13053.7, revised to 13058.1, and completed at 13058.1.

No trade was affected: no reissue of those lineages was compared against them.

**Correction:**
- `_retire()` records the primary destination and its zone as they stand at the ending, which is the one achieved for a completion.
- `migrate_lineage.history()` applies every recorded "primary destination A to B" revision. The journal records the revised **price** but not its zone, so for those members the duplicate rule asks whether the proposal's destination zone **contains** the achieved price. That is the same test applied to a point, with no new number.

**Tests:**
- TR2-01: the achieved destination is recorded.
- TR2-02: a republication overlapping the **revised** destination is withheld.
- TR2-03: a republication overlapping only the **published** destination (13164–13169 against the achieved 13170–13175) is issued, because it is a genuinely different destination.
- TR2-04: after a restart, the achieved destination still decides.
- TR2-05: the migration takes the revision.
- TR2-06: price-in-zone when the zone is unknown.
- FL-D1, FL-D2: the two real cases, in the replay and in the migration.

## R3: a missing candle during the authorisation catch-up

**Why `087b8c3` excluded the most recent interval.** The check covered finished intervals ending at or before `floor_5m(now) − 5 min`. That was written to avoid refusing in the moment between a 5-minute boundary and IG publishing the finished candle. It used a one-interval margin, which is a timing assumption.

**Facts:**
- The engine evaluates live ideas every second on the latest price (`prices/service.py every_second` → `Trading.on_price`), independently of candle storage.
- A finished candle is stored only when IG marks it complete (`CONS_END = 1`, `prices/feed.py`).
- Production's own log: of 4,297 stored candles, 4,291 were written within second :00 after their boundary and 4 within :01. Normal publication delay is therefore under about a second. A candle never stored is a genuine gap (it is then recorded by the store's own check).

**The defect, reproduced on `087b8c3`.** With the 10:00 candle never stored, an idea at 10:05:40 was **authorised**. For as long as the missing interval is the most recent one (up to 5 minutes), nothing checked it: not the store, not the tracker, not the forming candle. A destination touch or a break in it would have gone unseen.

The same blind spot existed in normal timing, for the sub-second before IG publishes. That hole dates from Stage B.

**Correction**, with no new timing threshold:
- The engine (`Trading._forming`) keeps the candle that has just finished, built from every live price, until IG publishes it (`previous_partial`).
- It also records whether it saw each candle **whole**: prices flowing into it from the candle before, not first seen mid-candle after a restart.
- The catch-up then requires every finished interval after the tracker's last step, **the most recent included**, to be either stored, or seen whole by the engine. When seen whole, the tracker's own destination rule is applied to the engine's candle.
- Anything else refuses, with the PD-5 reason.
- During normal publication timing a clean candle does not refuse.

**Behaviour verified:**

| Moment | Case | Result |
|---|---|---|
| At the boundary, before any new price | the forming candle is the finished one, seen whole | used; a destination touch refuses (TR3-03) |
| Just after the boundary, IG not yet published | the engine's finished candle | used: a touch refuses (TR3-01); a clean candle allows (TR3-02) |
| Delayed store write | same as above | the same rule, whatever the delay |
| Genuine gap | neither stored nor seen whole | refuses, PD-5 (TR3-04) |
| After a restart mid-candle | seen only in part | refuses, PD-5 (TR3-05) |
| The candle published | read from the store as before | TR3-07; T-31 to T-38 unchanged |

TR3-06 tests the engine's bookkeeping.

## R4: controlled reconciliation review (D-R1, D-R2: fail closed)

**When an opportunity is blocked** (it authorises nothing; every other rule applies; nothing expires):
- **D-R1, evidence unavailable:** a recorded gap in its life is still open, because IG's history has not supplied every missing candle.
- **D-R2, test identity uncertain:** either of these holds:
  - a gap was re-checked, but a recovered hourly candle would change an already-numbered test, or would place a zone break the tracker can no longer replay (status "review");
  - its lineage holds an uncertain hour (an incomplete hourly candle whose stored parts are clear of the zone).

**Procedure:**
1. `.venv/bin/python -m planner.review --pair GBPUSD` (read only) lists every blocked opportunity with:
   - its gaps;
   - its uncertain hours;
   - the rule (D-R1 or D-R2);
   - its lineage's consumed tests and alias keys.
2. **D-R1:** the approved IG recovery, in a maintenance window with the price service stopped (`prices/history_fill.py gap-plan`, then `gap-go`). The tracker re-checks the opportunity on the recovered candles, in time order, at its next run (`_reconcile_gaps`, `_reconcile_ended`), and records the outcome as new events.
3. **What is still blocked after that** (IG has no candle, or a review case) stays blocked until the opportunity ends by its own rules. There is **no override**: your decision is fail closed. A future opportunity in the same lineage is judged on its own evidence.

**Guarantees, each tested:**

| Guarantee | How | Test |
|---|---|---|
| Uncertainty cannot reset a consumed test | an incomplete clear hour never re-arms; a recovered hour that would renumber is "review", never applied; consumed tests and aliases are never removed | TW1-08, TW3-07, TW3-08, TR4-02 |
| Historical keys remain protected | aliases live in the lineage state and survive the map file's removal, restarts and unsettled orders | TW1-18, FL-M1, TM-06, TR4-01 |
| Unrelated opportunities remain eligible | the block is per opportunity and its lineage | TW3-02, TR4-02 |
| No retrospective trades | the tracker has no order path; an authorisation happens only for a strategy's live idea; reconciliation writes only the tracker's files | TW3-10, T-62 |
| No historical trading record rewritten | the order journal, trade records and decisions are never written by STP; planner events are append-only; corrections are new events | TW3-10, TR1-04, TW2-07 |

## Tests changed by these amendments

One test from the original suite: `tests/technical/test_stp_review_20261125.py::test_R6` (its `_r3_engine` helper). The stand-in it substitutes for `stp.authorise.authorise` copies the real function's signature, and it now also takes the two R3 parameters (`previous`, `partial_covered`) that the engine passes. Its assertions are unchanged. All the new tests are in `tests/technical/test_stp_lifecycle_review_20261127.py`, plus FL-D1 and FL-D2 in the replay functional file.
