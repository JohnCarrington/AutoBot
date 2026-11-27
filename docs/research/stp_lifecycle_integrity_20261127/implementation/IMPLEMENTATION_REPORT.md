# Phase 2: STP lifecycle integrity, implementation report (27 November 2026)

**Status: implemented on branch `stp-lifecycle-integrity` (from production baseline `fadf228`), for independent review. Ready for deployment, but nothing is deployed.**

**Contents:** 1 Architecture · 2 Decision register · 3 Defects and corrections · 4 Migration method · 5 Protection of consumed tests · 6 Test results · 7 Before and after · 8 Full regression · 9 Candle recovery plan · 10 Deployment and rollback · 11 Production changes today · 12 Residual risks · 13 Review pack

No code was deployed and no service was restarted. Only one production change was made, which you approved: `STP_AUTHORISES_ENTRIES` switched off (§11). The candle recovery (OP-1) is deferred to Saturday, as you decided.

The investigation it implements is `../REPORT.md` (commit `d9ca86e`, accepted).

| Work package | Commit | What |
|---|---|---|
| WP1: structural identity and duplicate protection | `f4a7a13` | C-2, C-3/PD-2, C-4/PD-3, PD-4 migration |
| WP2: lifecycle accuracy and dashboard | `37aca0e` | C-1, PD-1 C, C-7/PD-6 |
| WP3: market data integrity | `b49337e` | PD-5 A+B+C |
| Report and evidence | the final commit (§13.10) | this document, the replay comparisons, the live migration dry run |

---

## 1. Updated architecture

```
price service (unchanged order)
 ├─ engine ─► _place ─► STP check (stp/authorise.py, read only) ─► entry filters ─► OrderSender ─► IG DEMO
 │                       key = <LINEAGE>#t<n> | alias keys | keys of every other lineage the rejection reached
 │                       refuses: no live opportunity · catch-up · data gap (PD-5 B) · rule 11 on ANY key part
 │                                                                           │
 │                                     IG confirms the trade (ACCEPTED, or recovered at IG's own time)
 │                                                                           ▼
 │                                    orders/<PAIR>/stp_executions.jsonl  (one-way acknowledgement, WP2)
 │                                                                           │ read only, by its file
 └─ planner subprocess (tracker) ◄────────────────────────────────────────────┘
      planner/opportunities.py   lifecycle per opportunity (unchanged rules) + the LINEAGE registry
      planner/lineage.py         lineage membership; D-25/P-C8 counting (complete-candle re-arm; walk-back seed)
      planner/gaps.py            expected candles by market hours; gaps recorded, reconciled after IG recovery
      planner/migrate_lineage.py the historical lineage map (PD-4), run once at deployment
      current.json: opportunities + lineages + acks_seen      recommendations.jsonl: every event (append-only)
```

- **Forecast ≠ structural test.** An opportunity is a published forecast. A **lineage** is the structural place in one direction (BUY and SELL are always separate), and it owns the D-25 test count.
  - A new opportunity **joins** a lineage if any of these holds:
    - a live opportunity of the same direction has the same identity;
    - a live opportunity of the same direction has a zone overlapping both its zone and the lineage's **home zone** (the first opportunity's zone), where zones sharing only an edge do not overlap;
    - failing those, the most recently ended such opportunity.
  - Otherwise it starts a new lineage. Because of the home zone, a lineage never chains to a place its first opportunity did not overlap.
- **Duplicate key** = `<lineage>#t<n>`. Republication, reissue after completion or invalidation, supersession, fixed-level changes, rollover, reclaim and restart all keep the lineage. So none of them can restart a test at #t1.
- **Separation kept:**
  - STP never imports execution code; a guard test enforces this;
  - STP reads the acknowledgement file only, which carries no price, size or result;
  - the trade manager never reads STP;
  - execution writes only that one file.
- **Unchanged:**
  - STP's forecasting, hourly generation, levels, direction, zones and destinations;
  - every strategy's confirmation and entry;
  - stops, take profits and trade management;
  - Phase 1;
  - the admission of every ungated strategy;
  - the gated strategies' admission while STP authorisation is off.

## 2. Approved decision register (implemented)

| Decision | Approved option | Where |
|---|---|---|
| PD-0 | `STP_AUTHORISES_ENTRIES` off until the corrected build is reviewed, deployed and explicitly approved for activation | production `.env` 27 Nov 14:58 UTC (§11) |
| PD-1 | C: trade-linked completion, with the safeguards | `orders/executions.py`; `planner/keeper.py destination_end`; `OpportunityKeeper._take_acks` |
| PD-2 | Duplicate rule on overlapping destination zones | `OpportunityKeeper._duplicate_of` (compared with the ACHIEVED zone only: no chains) |
| PD-3 | Shared lineage for overlapping same-direction opportunities, excluding edge-only zones | `planner/lineage.py strict_overlap`; `_lineage_for`, `_belongs` (home zone) |
| PD-4 | Preserve and reconcile existing lineage identities | `planner/migrate_lineage.py`; `_apply_lineage_map` |
| PD-5 | A+B+C | `planner/gaps.py`; `_record_gaps`, `_reconcile_gaps`, `_reconcile_ended`; `stp/authorise.py unreconciled` |
| PD-6 / C-7 | Dashboard wording and presentation | `dashboard/stp.py`, `dashboard/static/stp/stp.js` |
| OP-1 | Recover the 27 Nov candles from IG | deferred to Saturday, service stopped (owner, 27 Nov) |
| C-1 | Accurate destination classification | `planner/keeper.py` (`destination_case`) |
| C-2 | Lineage continuity, test seeding, duplicate protection | `planner/lineage.py`, `planner/opportunities.py`, `stp/authorise.py` |

No new numerical threshold was introduced. The only numbers used are the approved P-C2 / P-C8 3 pips, the 300-second late-candle wait the builder already had, and the market hours.

## 3. Implementation mapped to every confirmed defect

| Defect (investigation) | Correction | Evidence |
|---|---|---|
| **L-2:** a reissue restarts the key at #t1 | lineage continuity (C-2) + map (PD-4) | TW1-01..03, TW1-17, FL-A3/A4, FL-M1: the 12:01 BUY is refused; no republication of test 1 can authorise |
| **L-1:** a traded opportunity ends "destination reached before entry" | PD-1 C acknowledgements; four-way `destination_case` | TW2-04..07, FL-B1: 1700-34 is COMPLETED `after_trade` at 18:20 |
| **L-3:** the duplicate rule compares exact prices | PD-2 destination-zone overlap | TW1-09, TW1-10, FL-A8 |
| **L-4:** parallel lineages; rollover successor | PD-3 shared lineage; cross-lineage keys | TW1-11..15, TM-03, TM-05 |
| **L-5:** a gap hides lifecycle events; "current" across a gap | PD-5 A+B+C | TW3-01..10, FL-C1..C4 |
| **L-6:** dashboard wording | C-7 | TW2-20, R4 |
| **L-7:** a pre-creation test is not counted | walk-back seeding; the creation hour counted; test 0 before the seed | TW1-04..07 |
| (new) missing data can make a test | only a complete hourly candle re-arms; an incomplete clear one is "uncertain" and blocks until reconciled | TW1-08, TW3-07/08, FL-C3 |

## 4. Historical lineage migration methodology (PD-4)

`python -m planner.migrate_lineage --pair GBPUSD --as-of <UTC>`: a dry run by default; `--apply` writes `data/planner/GBPUSD/lineage_map.json`. It is deterministic (TM-01) and read-only on every record. The tracker applies each version of the file once, idempotently: the file's sha256 is recorded, and a crash mid-apply changes nothing (TM-06).

1. **History.** Every opportunity since 24 Nov from the planner's own records: issued zone, then each recorded zone change, plus identity, primary destination and its zone, ending, and "supersedes". A supersession counts only for the same identity. Before STP_OPPORTUNITIES, the single tracker superseded on any zone change, which is not the same place (TM-05).
2. **Lineages.** The tracker's own membership rule, replayed in creation order (retirements before creations at a re-plan).
3. **D-25 counts.** The tracker's own counting, hour by hour while a member was tracked, plus the untracked hours when one rejoins.
4. **Consumed keys.**
   - Every STP key part of an order that opened, was adopted, or was sent and never settled (the order journal) is checked.
   - Its rejection candle is taken from the trade's own entry step "STP authorised: the rejection candle …"; no financial figure is read.
   - Its test m is computed under the lineage.
   - If `<lineage>#t<m>` differs from the old key, the old key becomes an **alias** of test m. The authorisation then adds every alias of test m to the idea's key, so rule 11 refuses it if any is used.
   - A key without a rejection candle is reported as **ambiguous**, with no guess (TM-04).
5. **Live opportunities** are mapped to their lineage.

**Result on the 27 Nov 14:15 production records:**

| Lineage | Members | Consumed tests | Aliases |
|---|---|---|---|
| BUY 0300-56 (13121.3–13130.9) | 0300-56, 1200-57, **1305-58 (live)** | t1: AB261127065505 (06:55), AB261127120127 (12:01) | t1 ← **1200-57#t1** |
| BUY 1700-34 | 1700-34, 2100-36 | t1: AB261125170604 | – |
| BUY 0000-37 | 0000-37, 1000-39, 1100-41, 1200-43, 1500-45, 2100-48, 0100-52 | t1: AB261126060101; t2: AB261126114004 | – |
| SELL 0400-38 | 0400-38, 1200-42, 2300-49, 0100-51 | t1: AB261126063004; t2: AB261126125133 | – |
| SELL 1700-23 (13117.6–13128.6) | 1700-23, 0000-26, 1800-35, 1100-40, 1400-44, 2000-46, 2100-47, 0000-50, 0200-53, 0300-55 | t2: AB261125200515; t6: AB261126142255 | t2 ← 1800-35#t1; t6 ← 1400-44#t1 |

The three keys you named:
- **0300-56#t1:** consumed by the 06:55 trade; it is the lineage's own key for test 1.
- **1200-57#t1:** consumed by the 12:01 trade, whose rejection candle was 11:40. Under the lineage that candle is test 1. No hourly candle from 02:00 to 13:00 was wholly clear of the zone, so it is the same test, and the key is mapped as an **alias of 0300-56#t1**.
- **1305-58#t1:** never issued. No idea was ever authorised against 1305-58: STP was off for authorisation from 14:58, and nothing was authorised before. 1305-58 itself is mapped to lineage 0300-56, so any idea in that test now gets `0300-56#t1|1200-57#t1` and is refused (FL-M1).

Nothing is ambiguous. No historical trade record or order journal is changed.

## 5. Consumed structural tests stay protected

- **FL-M1**, the real production state of 27 Nov 14:15 with the map applied:
  - 1305-58 is in lineage 0300-56;
  - a BUY whose rejection candle is 13:10 gets `0300-56#t1|1200-57#t1`;
  - each old trade's journal key alone makes rule 11 refuse it;
  - the map is applied only once across a restart.
- **FL-A4:** a 13:20 BUY in the same test after the 13:05 re-plan is refused.
- **TW1-15:** a rejection that reaches two lineages consumes both lineages' keys.
- **TW1-16** (restart), and **TW2-12** (an unresolved order keeps its keys).

## 6. Test results

| Suite | Result |
|---|---|
| WP1 technical TW1-01..17 | 21 passed. Before the fix (`fadf228`): 15 failed, 6 passed (`wp1_tests_before_fix.txt`) |
| WP1 migration TM-01..06 | 6 passed |
| WP1 functional FL-A1..A9, FL-M1 | 10 passed. Before the fix: 5 failed (`wp1_functional_before_fix.txt`) |
| WP1 technical TW1-18 (alias keys across restarts and unresolved orders) | passed (added with WP3) |
| WP2 technical TW2-01..15, 20, 21 | 17 passed. Before (WP1 only): 14 failed (`wp2_tests_before_fix.txt`) |
| WP2 functional FL-B1..B3 | 3 passed |
| WP3 technical TW3-01..10 | 10 passed. Before (WP2 only): 9 failed (`wp3_tests_before_fix.txt`) |
| WP3 functional FL-C1..C4, the real 27 Nov gap | 4 passed |
| Full regression | see §8 |

**The replay harness** (`tests/stp/lifecycle_replay.py`) uses:
- the frozen production candles (14:15 on 27 Nov, the gap included);
- STP's own plans at every recorded analysis time, recomputed with the unchanged planner (124 plans, **0 differences** from the journal);
- the start at 25 Nov 09:15, the first opportunity-tracker run in production;
- hourly candles visible only when production built them.

On `fadf228` it reproduces production's journal **for all 32 opportunities with 0 differences**, and authorises the 9 trades with their recorded keys. That is the fidelity check behind every functional test.

**Mandatory scenarios** (the brief, §6):

| Scenario | Test |
|---|---|
| 27 Nov 06:55 BUY remains valid | FL-A5 |
| Duplicate 12:01 BUY refused | FL-A3 |
| Further republication cannot trade the consumed test | FL-A4, FL-M1, FL-C4 |
| A genuine new test after a re-arm stays tradable | TW1-03, TW1-04, FL-A5 (26 Nov 11:40 #t2) |
| 25 Nov 17:06 BUY valid and correctly classified | FL-A7, FL-B1 |
| 26 Nov 11:40 BUY remains valid | FL-A5 |
| 25 Nov session sweep unaffected | FL-A9 (never gated) |
| Multiple strategies cannot trade one test | FL-A6, TW1-15 |
| A rejected broker submission records no completion | TW2-11 |
| An unresolved submission keeps duplicate protection | TW2-12 |
| A recovered execution gives the correct acknowledgement | TW2-13 (IG's own open time) |
| A restart cannot lose an acknowledgement or reset a consumed test | TW2-08, TW2-14, TW1-16, TM-06, TW3-10 |
| Missing data cannot create a new test | TW1-08, TW3-07, FL-C3 |
| Recovered candles cannot trigger retrospective execution | TW3-10 (the tracker writes only its own files; there is no order path); TW3-04/05 |
| STP off keeps the previous admission | FL-A9; existing T-27, T-48, T53/T66 |

**Crash and restart** at every new persistent boundary:
- lineage registry: TW1-16;
- lineage map apply: TM-06;
- journal → acknowledgement (sender): TW2-14;
- acknowledgement intake: TW2-08;
- gap reconciliation: TW3-10.

## 7. Before and after: the recorded STP-authorised trades (replay, 25 Nov 09:15 to 27 Nov 14:10)

| Trade | Idea | Before (`fadf228` = production) | After (this branch) |
|---|---|---|---|
| AB261125170604 (5m bounce BUY) | 25 Nov 17:06 | 1700-34#t1, opened; 1700-34 ended INVALIDATED "before entry" | 1700-34#t1, **opened**; 1700-34 **COMPLETED after_trade** |
| AB261125200515 (SELL) | 25 Nov 20:05 | 1800-35#t1, opened | same key, **opened** |
| AB261126060101 (BUY) | 26 Nov 06:01 | 0000-37#t1, opened | lineage 0000-37 #t1, **opened** |
| AB261126063004 (SELL) | 26 Nov 06:30 | 0400-38#t1, opened | lineage 0400-38 #t1, **opened** |
| AB261126114004 (BUY, +14.0) | 26 Nov 11:40 | 0000-37#t2, opened | lineage 0000-37 **#t2**, **opened** |
| AB261126125133 (SELL) | 26 Nov 12:51 | 0400-38#t2, opened | lineage 0400-38 #t2, **opened** |
| AB261126142255 (SELL) | 26 Nov 14:22 | 1400-44#t1, opened | lineage 1800-35 #t5 (the replay's resistance lineage), **opened**; COMPLETED after_trade |
| AB261127065505 (BUY) | 27 Nov 06:55 | 0300-56#t1, opened | lineage 0300-56 #t1, **opened**; COMPLETED after_trade |
| **AB261127120127 (BUY)** | **27 Nov 12:01** | 1200-57#t1, **opened** (the duplicate) | **refused**: 1200-57 is not published (PD-2: the destination just achieved). With the map, rule 11 refuses it anyway (FL-M1) |

**Publications.**
- **Identical to production:** 23 of the 31 opportunities from 25 Nov 09:15, with the same lifecycle.
- **Classification corrected:** 1700-34.
- **Withheld as reissues of a place whose destination had just been achieved (7):**
  - BUY 13084.1 at 25 Nov 21:00;
  - SELL 13115.1 at 26 Nov 20:00 and 21:00;
  - SELL 13108.5 at 27 Nov 00:00 and 02:00;
  - BUY 13121.3 at 27 Nov 12:00 and 13:05.
- **None of the 7 opened a trade** in production during trading hours.
- Replay ids after the first withheld publication are numbered one lower than production's. That is cosmetic: the ids count publications.

Results are given in pips as recorded. No financial improvement is claimed.

## 8. Complete regression suite

| Commit | Result |
|---|---|
| `fadf228` (baseline) | 2818 passed, 3 skipped |
| WP1 `f4a7a13` (pre-commit hook) | **2855 passed, 3 skipped** (856 s) |
| WP2 `37aca0e` (pre-commit hook) | **2874 passed, 3 skipped** (812 s) |
| WP3 `b49337e` (pre-commit hook: the integrated tree, technical, functional and architectural guards) | **2889 passed, 3 skipped** (825 s) |

No test was skipped or deselected for these runs. The 3 skips are the suite's own: tests that need data absent from this machine. The architectural guards are in the full suite and pass:
- `test_stp_final_validation_20261120.py::test_10`: the planner imports no broker or trading code;
- `test_planner.py::test_no_trading_part_uses_the_planner...`: no trading module mentions the planner;
- T-49 and T-55: the analyser and trade manager never read STP;
- TW2-21: STP reads the acknowledgements through the file alone.

## 9. Historical candle recovery (OP-1): procedure for Saturday, not yet run

The read-only plan (contacts nobody), as of 27 Nov:

```
gap-plan --pair GBPUSD --from 2026-11-27T11:55:00Z --to 2026-11-27T12:20:00Z
  Fri 27 Nov 12:00 GMT to Fri 27 Nov 12:10 GMT: 3 candle(s) (12:00, 12:05, 12:10)
  Requests: 1, points: 3. Bot's weekly budget 7000, used in the last 7 days 0. IG remaining 4157 of 10000.
```

Saturday window (market closed; the price service stopped by you; no concurrent IG session):
1. List every recorded gap: `gap-plan` over the week, including the 14:58 restart's own gap once you restart.
2. Back up `data/candles/GBPUSD` (tar + sha256).
3. You stop `autobot-prices`.
4. Run `gap-go` for each recorded gap: one request per unbroken run, only missing candles, never overwriting. The 1h and 4h candles are rebuilt under the standing rule, with the old ones archived.
5. Verify: store check, timestamps on the 5-minute boundaries, no duplicates, the parts now complete, and IG's points used.
6. Report, then you start the service.

Phase 2 reconciliation code does not run in production until it is deployed (your instruction).

## 10. Deployment and rollback (NOT authorised: for after the review)

**Deploy**, with STP authorisation staying off:
1. Pre-checks: IG positions and AutoBot open or unresolved orders; nothing in flight.
2. Backups: `.env`, `settings.toml`, and `data/{planner,orders,records,trade_manager,trading}` (tar + sha256).
3. Fast-forward `/opt/autobot` to the branch's final commit. No `.env` or settings change is needed.
4. Run `python -m planner.migrate_lineage --pair GBPUSD --as-of <now>` (dry run). Review the lineages, aliases and live mapping against §4, then run it with `--apply`.
5. You restart `autobot-prices` and `autobot-dashboard`.
6. Post-checks:
   - the next tracker run records "lineage map applied" once;
   - any live reissue shows its lineage;
   - the dashboard shows Watch & Wait, the lineage, test and consumed columns, and Stage A;
   - no "data gap" on opportunities created after the restart.
7. Re-activating `STP_AUTHORISES_ENTRIES` is a separate, explicit approval.

**Rollback:**
1. Stop both services.
2. `git -C /opt/autobot reset --hard fadf228`.
3. Start both services.

`fadf228` reads the new `current.json` safely. The extra keys (`lineages`, `acks_seen`, `data_gaps`, `executions`) are ignored, and each opportunity still carries its `tests`. `lineage_map.json` and `stp_executions.jsonl` are not read by `fadf228`. To return to the exact earlier state, restore `data-state.tgz` from the deployment backup.

## 11. Production change made today (approved, PD-0)

- **14:58:26 UTC:** `STP_AUTHORISES_ENTRIES=on` → `off`. Exactly one line changed; all 43 switches load, and the only difference is that switch.
  - Backup: `/home/autobot/backups/env-before-stp-auth-off-20261127_145826`.
  - Pre-checks first: IG had 0 positions (funds £96,746.61); AutoBot had 0 open trades and 0 unresolved orders.
- **In effect since your restart at 16:26:57 UTC** (prices PID 1406204):
  - Trading ON at 16:27:49, 0 open trades taken over, price stream connected;
  - the STP tracker ran at 16:30:04, marked itself current, and is still in opportunities mode;
  - no STP decision recorded since the restart.
  - The dashboard (PID 1392498) was not restarted, so its STP tab still says Stage B (R6).
- Before the restart, the running process still had the switch on:
  - at 15:11:16 STP authorised a 5m bounce SELL (AB261127151117, `1500-59#t1`);
  - a slow grind SELL (AB261127154711) opened at 15:47:10;
  - as you instructed, the restart waited until both had closed;
  - IG closed both at 16:20:09 and 16:20:11 through its SYSTEM channel (a hand close, not AutoBot's stop or take profit), at 13097.7;
  - AutoBot recorded both "closed by owner" from IG's activity at 16:25 (+9.0 and +4.3 pips);
  - checks before the restart: IG 0 positions, funds £96,879.61; AutoBot 0 open trades, 0 unresolved.
- Development baseline backup: `/home/autobot/backups/phase2-stp-lifecycle-20261127_145802` (env, settings, data state, full candle store, commit).

## 12. Residual risks and outstanding decisions

| # | Risk / item | Effect | Proposed handling |
|---|---|---|---|
| R1 | A 5-minute slot IG never sent, even in its history, cannot be reconciled | an opportunity live across it never authorises again until it ends (fail closed, per D-21) | **owner decision:** keep, or accept IG's own confirmation of no data as reconciled |
| R2 | A recovered hourly candle that would renumber an already-numbered test is left for **review** | that opportunity stays ineligible until it ends | **owner decision:** a review procedure, or keep fail-closed |
| R3 | A crash inside a tracker run can leave a duplicate event line in `recommendations.jsonl` (an existing property) | audit noise only: state is idempotent | none |
| R4 | A zone that drifts out of its lineage's home zone, with no identity match, starts a new lineage | a new key namespace for a new place; a rejection reaching both consumes both | as designed (PD-3, no chains) |
| R5 | PD-2 now withholds reissues across fixed-level changes in the same lineage | 7 fewer publications on the real days; no trade lost | as approved |
| R6 | The dashboard reads the switches at its own start | its STP tab says Stage B until the dashboard is restarted | your choice of restart |
| R7 | OP-1 not yet done; reconciliation not yet exercised on IG's real candles for 27 Nov | FL-C covers the pre-recovery half | Saturday; re-run FL-C with the recovered store |
| R8 | The migration must be applied at deployment | without it, the live reissue keeps its own lineage | step 4 of §10 |
| R9 | Phase 1 start-up rate limiting (IG activity reads) | separate operational improvement | unchanged, as you instructed |

The three Phase 1 historical financial corrections (−£23) were **not** applied. Nothing from Phase 3 is included.

---

## 13. Review pack

### 13.1 Tests changed from the original suite

| Test | Change | Justification |
|---|---|---|
| `tests/technical/test_stp_integration.py::test_T12_a_break_held_for_three_closes_invalidates` | Its last assertion was "the reissue has its own lineage". It now asserts that the reissue has a **new id**, starts **WAITING** (not the broken one restored), and **continues the lineage** | The approved C-2 and brief §3.1, "invalidation and subsequent reissue" must not reset duplicate protection. Every other assertion of T12 is unchanged |
| `tests/technical/test_stp_review_20261125.py::test_R4_...every_field_its_script_reads` | The set of fields the dashboard script reads gains `lineage`, `test`, `binds_first`, `data_gaps` | C-7 / PD-6: the page now shows them. The test's purpose (every field the script reads is supplied) is unchanged |
| `tests/technical/test_stp_lifecycle_wp1_20261127.py::TW1-08` (new in WP1) | WP3 adds: no authorisation while the hour is uncertain. The test number is checked directly | The PD-5 B block, added on top of WP1's rule |

No other existing test was changed. Every existing test passes unchanged (§8).

### 13.2 Historical opportunities withheld by the new publication rules

All 7 come from the destination-zone duplicate rule (PD-2): each is a reissue of a structural place whose primary destination had just been **achieved** (the last ended member of its lineage COMPLETED, or completed after a confirmed trade), with an overlapping destination zone.

| Published in production | What it did there | Why withheld |
|---|---|---|
| BUY 13084.1–13093, 25 Nov 21:00 (2100-36) | nothing authorised; INVALIDATED at the 00:00 rollover | 1700-34 completed after its 17:06 trade (13127.3) |
| SELL 13115.1–13123.9, 26 Nov 20:00 (2000-46) | nothing; destination before entry at 22:00 | 1400-44 completed at 14:45 (13103) |
| SELL 13115.1–13123.9, 26 Nov 21:00 (2100-47) | nothing; destination before entry at 22:00 | the same |
| SELL 13108.5–13119.1, 27 Nov 00:00 (0000-50) | nothing; destination before entry at 00:10 | the same lineage's completion toward 13103 |
| SELL 13108.5–13119.1, 27 Nov 02:00 (0200-53) | one authorisation at 04:10, **refused by the trading hours**; break held at 09:00 | the same |
| BUY 13121.3–13130.3, 27 Nov 12:00 (1200-57) | **the duplicate 12:01 trade** | 0300-56 completed at 11:05 (13135.5; 13134.6 overlaps) |
| BUY 13121.3–13130.3, 27 Nov 13:05 (1305-58) | nothing authorised by 14:15 | the same |

**None of them produced a trade in trading hours, except the duplicate.** Whether they were legitimate by the approved rules: each was a republication of an achieved forecast, which is exactly what the 19 November rule, now with PD-2, withholds. Twenty-three other publications are unchanged.

### 13.3 Genuine new structural tests remain tradable

- **TW1-03:** after a completion and a wholly clear hour between, the reissue's next test is `#t2`, and it is tradable after a trade on `#t1`.
- **TW1-04, TW1-05:** a pre-publication test is `#t1` and the first test after a re-arm is `#t2`, including an interaction in the creation hour.
- **FL-A2, FL-A5:** on the real days, all 8 legitimate trades are on distinct tests, and no key part is shared. The 26 Nov 11:40 BUY (+14.0, `0000-37#t2`, after the 10:00 re-arm) and the 26 Nov 12:51 SELL (`0400-38#t2`, after the reclaim and the 10:00 re-arm) open as before.

### 13.4 Delayed execution acknowledgements cannot reopen terminal opportunities

- **TW2-07:**
  - an opportunity ends "destination reached before entry";
  - IG's acknowledgement of an earlier execution then arrives;
  - **one** "classification corrected" event is recorded; the ending event stands; the opportunity is not in the live list again;
  - the lineage member's effective status becomes COMPLETED, so the duplicate rule then withholds a republication.
- The code path (`OpportunityKeeper._take_acks`) only appends an event and updates the ended member's classification. It never appends to the live list and never changes a status.
- **TW2-06:** an execution after the destination never changes the ending.

### 13.5 Missing-data reconciliation cannot generate retrospective trades

- **TW3-10:** reconciliation runs twice (as after a restart) and produces one reconciliation event. Under a fresh temporary root, the only files written are the tracker's own (`planner/`): no order, decision or record.
- **Architecture:**
  - the tracker has no order path;
  - an STP authorisation happens only in `Trading._place`, for a strategy's live idea, against the live price;
  - the engine tries each strategy, direction and candle once, and never retries a refused idea (T-62);
  - recovered candles are older than every live candle, and no strategy is re-run on them.
- **TW3-04, TW3-05:**
  - a reconciled zone touch only restores eligibility for future ideas;
  - a reconciled destination only ends the opportunity, at the reconciliation time with the candle's own evidence.

### 13.6 Historical key aliases survive restarts and unresolved broker submissions

- **TW1-18:**
  - the map is applied, then the file is removed, then two further tracker processes run;
  - the alias is still in the lineage, and the authorisation still adds it;
  - an **unsettled order** holding the old key (rule 11 counts unresolved orders, Phase 1) refuses the test.
- **FL-M1:** on the real 14:15 state, either old trade's journal key alone refuses the test, and the map is applied once across a restart.
- **TM-06:** re-applying after a crash mid-apply changes nothing.

### 13.7 Residual architectural and operational risks

The full list is §12 (R1–R9). Two need your decision before or after deployment, and neither blocks the review:
- **R1:** how to treat a slot IG never sent, even in its history;
- **R2:** a review procedure for a recovered hourly candle that would renumber a test.

Also:
- **Operational:** the deployment needs the migration applied (§10 step 4).
- **Operational:** PD-0 is in effect since the 16:26:57 restart (§11).

### 13.8 Updated decision register

| ID | Status |
|---|---|
| PD-0 to PD-6, OP-1, C-1, C-2 | approved (27 Nov) and implemented as §2. OP-1 scheduled for Saturday |
| **D-R1 (new)** | open, for you: an IG-confirmed absent candle and reconciliation |
| **D-R2 (new)** | open, for you: a review procedure for a recovered hour that conflicts with numbered tests |
| Deployment of `stp-lifecycle-integrity` | not authorised; awaits independent review |
| Re-activation of `STP_AUTHORISES_ENTRIES` | not authorised; a separate, explicit approval after deployment |

### 13.9 Migration verified on the live production records (dry run, 27 Nov 16:16:46 UTC)

The migration was run read-only on `/opt/autobot/data` (`lineage_map_live_dryrun_20261127_1616.json`, the lineages with consumed tests and their evidence):
- deterministic: two builds are identical;
- nothing ambiguous;
- the live **1305-58 → lineage 0300-56**, with `1200-57#t1` an alias of test 1;
- the live **1500-60 → lineage 0200-54**.

The trade STP authorised at 15:11:16 (AB261127151117, `1500-59#t1`, before your restart) maps to **test 9** of the SELL lineage 1700-23 (home zone 13117.6–13128.6). That is a distinct test from the ones traded on 25 Nov (t2) and 26 Nov (t6), so under the new rules it is a genuine new test, and its old key is kept as an alias of test 9. At deployment the map is built again, with `--as-of` set to the deployment time (§10 step 4).

### 13.10 Branch and commits

| Commit | What |
|---|---|
| `f4a7a13` | WP1 |
| `37aca0e` | WP2 |
| `b49337e` | WP3 |
| the final commit on `stp-lifecycle-integrity` | this report and the evidence files |

GitHub: https://github.com/JohnCarrington/AutoBot/tree/stp-lifecycle-integrity
