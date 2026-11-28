# Phase 3 — Common structural awareness across AutoBot strategies: research and design pack

27–28 November 2026. **Research and design only. Nothing is implemented, nothing in production was changed, and
the Phase 2 freeze is untouched.** Branch `research/phase3-structural-coherence-20261127`, from production
`fadf228`. Worktree `/home/autobot/worktrees/autobot-phase3-research`.

## Contents (deliverables 1–9)

| # | Document | Deliverable |
|---|---|---|
| 1 | [01_FORENSIC_ANALYSIS.md](01_FORENSIC_ANALYSIS.md) | Extended forensic trade analysis, 18–27 Nov (Phase 1 + Friday), IG-reconciled |
| 2 | [02_STRATEGY_CONFLICT_ASSESSMENT.md](02_STRATEGY_CONFLICT_ASSESSMENT.md) | Strategy-by-strategy structural conflict assessment |
| 3 | [03_ARCHITECTURE.md](03_ARCHITECTURE.md) | Proposed common structural coherence assessment (SCA); room rule kept separate (§3.9) |
| 4 | [04_DESIGN_OPTIONS.md](04_DESIGN_OPTIONS.md) | Alternative design options and their implications |
| 5 | [05_DECISION_REGISTER.md](05_DECISION_REGISTER.md) | Decision register with recommendations (D-1…D-15) and outstanding items |
| 6 | [06_HISTORICAL_IMPACT.md](06_HISTORICAL_IMPACT.md) | Historical trade impact, an evidence card per rule, breadth, Watch & Wait releases |
| 7 | [07_TEST_SPECIFICATION.md](07_TEST_SPECIFICATION.md) | Technical and functional tests |
| 8 | [08_WORK_PACKAGES.md](08_WORK_PACKAGES.md) | Implementation work packages |
| 9 | [09_DEPLOYMENT_ROLLBACK.md](09_DEPLOYMENT_ROLLBACK.md) | Deployment and rollback approach |
| 10 | [10_REVIEW_CLARIFICATIONS.md](10_REVIEW_CLARIFICATIONS.md) | **Revision 2:** answers to the independent review R1–R5, evidence, errata |

**Revision 2 (28 Nov)** answers the review of `c7ba045`:
- R1: an old zone cannot block continuation further away;
- R2: S4 takes precedence over S5, judged per opportunity;
- R3: no resolution from unreconciled data;
- R4: structural permission is not admission;
- R5: UNKNOWN is separate from neutral.

No trade changes state. 8 of 416 ideas do. Errata are in 05.

Evidence: `evidence/scripts` (read-only analysis), `evidence/output` (JSON, tables, source hashes),
`evidence/inventory` (code inventories with file:line at fadf228 and 9e0ffd5).

## Findings in brief

1. **The structural defect is narrow and specific.** Of 70 bot trades, 11 were opened at, inside, or through an
   opposing STP zone that STP still held unresolved. Those are trades with no D-20 break in their direction and
   not reversals at a two-direction zone. All 11 lost (recorded IG results). 3 owner-closed trades had the same
   defect. 28 of the 45 bot losers are structurally neutral, so no structural check can touch them.
2. **One assessment at one point (`Trading._place`, after the entry filters), reusing STP only.** It uses STP's
   opportunities, labels, lifecycle, D-20 break and NEAR. Seven states. Only "within an unresolved opposing
   zone" (S4) defers. Everything else permits, so STP is not a blanket veto. Deferred ideas (82 of 416, rev 2) split 46 BUY / 36 SELL,
   and days with no STP structure see no deferral.
3. **Watch & Wait is a refusal, not a queue.** A later trade needs the strategy's own fresh setup. On 25 Nov the
   deferred 12:25 sweep is followed by the fresh 15:05 sweep that made 61.4 pips.
4. **Preserved, shown trade by trade.** The 61.4-pip sweep (S2). EMA pullback +30.0 (S2). Healthy slow-grind
   pullbacks +20 ×3. The breakout +50.0. Reversals at structure (S1/S5). The retest of a broken zone (26 Nov 11:40
   +14.0, S6), which is also the genuine new test after re-arming (`0000-37#t2`). The 27 Nov 12:01 BUY is a
   duplicate: S7 structurally, but refused by Phase 2 (rev 1 erratum E-1).
5. **The main cost** is later entry for break continuations, which wait for STP's hourly D-20 close (27 Nov
   13:20–15:00). Breakouts into an unresolved zone are effectively refused.
6. **Room to level is kept separate and not recommended now.** The evidence is 2 bot winners vs 2 losers. An
   opposite-position rule is not recommended: it refuses 4 winners and is directional.
7. **OD-18 A would be partly superseded** (D-2). That is the owner's decision.

## Constraints honoured

There is no new forecasting engine and no change to STP methodology, strategy confirmation, stops/TP, trade
management, or Phase 1/2 code. There are no RSI thresholds, expiries, directional vetoes or delayed entries,
and no shadow trading, deployment or comparison. Only existing thresholds are used (NEAR 3, break 3, own stop).
No IG session was opened. Production data was read from a copy taken after the 20:30 UTC last entry.

## Reproducing

Copy the data snapshot (records, orders, planner, candles) to a folder `S` (`S/data/...`, `S/store/GBPUSD`)
and copy the scripts into `S`. Then, from a worktree at fadf228 with its `.venv`, run:
`python forensic2.py S`, then `classify2.py S`, `impact.py S`, `breadth.py S` and `gen_tables.py S`. For
revision 2, run `classify3.py S` and then `r1_evidence.py S` (it needs breadth.json).
`forensic2.py` also needs `S/switches.env` (the non-secret switch lines of .env). The source files' hashes are
in `evidence/output/SOURCE_SHA256.txt`.
