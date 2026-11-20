# STP final correction and validation — 20 November 2026

Branch `stp-structural-history-20261120`, isolated worktree `/home/autobot/worktrees/autobot-stp-history`. Production
was not modified. No service was restarted, IG was not contacted, no orders were placed and no shadow trading was
added.

## 1. Root cause and correction

**The five Version B recommendations** come from two episodes. In each, three or two consecutive 4-hour decisions
gave the same plan:

| Decision (UTC) | Entry zone | Primary (Major) | Distance | ADR | Zones passed over | Stored outcome (static) |
|---|---|---|---|---|---|---|
| 12 May 2025 12:00 | 1.32000–1.32117 | 1.30144 | 162.3 pips | 1.6 | 4 Moderate, 1 Minor | entered, then invalidated |
| 12 May 2025 16:00 | 1.32000–1.32149 | 1.30144 | 176.6 | 1.8 | same | entered, then invalidated |
| 12 May 2025 20:00 | 1.32000–1.32149 | 1.30144 | 163.7 | 1.6 | same | entered, then invalidated |
| 18 May 2026 16:00 | 1.34266–1.34380 | 1.32157 | 201.4 | 2.6 | 7 Moderate, 5 Minor | entered, then invalidated |
| 18 May 2026 20:00 | 1.34294–1.34380 | 1.32157 | 213.7 | 2.7 | same | entered, then invalidated |

**Why they were selected.** In every case the direction was BEARISH and the condition CONTINUATION. The entry zone was
a valid Major zone (4–5 families), and the primary was the first Major zone below it (3 families, with a daily swing),
exactly as D-18/D-19 require. Production (A) refused them only because zones were clipped to the 150-pip
round-number radius, which removed every Major zone beyond 150 pips. The owner's 9210ca5 ("preserve all structural
zones for destination selection") removed that clip, so these destinations became eligible.

**Should an existing rule have excluded them? No.**
- **Structure:** the primary is Major, wholly beyond the entry zone, ahead of price and not reached. Every zone in
  between is Moderate or Minor, which by D-18 can be an intermediate destination but never the primary.
- **Volatility:** the approved spec (FC-03) says distance and ADR are "context only; ADR never rules a zone out". At
  1.6–2.7 ADR, with today's range already about 1 ADR or more, these are the cases that rule deliberately leaves
  alone.
- **Market condition:** CONTINUATION is a valid opportunity (FC-04).
- **Invalidation:** the zone-break, structure-break and destination-first conditions were all set correctly.

**What actually happened to them.** The stored "invalidated" outcome is static: the plan is frozen at the decision and
traced for up to 240 hours. The real keeper, replayed on the research store, never invalidated any of the five:
- **18 May 2026 16:00:** entered at 16:10. At 23:00 a nearer Major zone formed and the primary was updated
  (1.32157 → 1.34016). At 00:00 the recommendation was superseded.
- **12 May 2025:** entered at 12:50, then superseded at 19:00, 21:00 and 23:00. Each successor kept the same zone edges
  on different fixed levels (the known identity issue, still awaiting a decision). The line ended by supersession on
  13 May at 12:00, when the zone moved to 1.32331–1.32440. The successor zone was the one later invalidated.

**Statistically, the five are not evidence of a defect.** Together they are two independent episodes. Their
random-walk chances of reaching the destination before the zone break were 19%, 13%, 20%, 11% and 5%, so 0.68 wins
were expected. The chance of 0 of 5 under pure chance is about 48%.

**Conclusion:** the destinations are structurally valid under the approved rules. Excluding them needs a new
reachability rule, which is a methodology change (see section 5). No threshold was introduced or tuned.

**Correction made (no decision changes):**
1. **The refusal text was wrong.** "no Major support zone below the entry zone **within the 150-pip window** for the
   primary destination" described a window that stopped applying with 9210ca5. It now reads "no Major support zone
   below the entry zone for the primary destination". The dashboard and keeper match it by prefix, which is unchanged.
2. **The primary's distance is now recorded as context only:** `observations.primary_distance_pips` and
   `primary_distance_adr`, the same way entry-zone distance already is. No rule reads it. This gives the owner the
   evidence for the reachability decision on live data.
3. **The docstring** for DESTINATIONS in planner/assess.py states that no distance limit applies.

## 2. Files changed

| File | Change |
|---|---|
| planner/assess.py | Refusal text without the stale 150-pip window. Primary distance (pips, ADR) recorded as context. Docstring. |
| tests/functional/test_stp_final_validation_20261120.py | New: 16 functional tests, items 1–10 of the brief. |
| docs/research/stp_final_validation_20261120/ | This report, the focused-replay comparison and the keeper replays of the five. |

Unchanged:
- direction;
- `dominant_structure()` (candidate C, the H4 correction);
- the lifecycle, identity and duplicate rules;
- Major classification;
- D-1;
- invalidation;
- historical discovery (`historical_daily_swing_lookback_weeks = 156`);
- every owner-approved parameter.

## 3. Tests

- **New file:** 16 passed, 0 failed.
- **Full suite:** **2,330 passed, 0 failed** (27 min).

| Brief item | Test(s) |
|---|---|
| 1 Historical levels discovered | test_1 (historical swing 1.32073 in a primary 201 pips away); plus the 5 existing structural-history tests |
| 2 Direction unchanged | test_2 (history on/off identical at all five); November replay; focused replay |
| 3 Major confluence enforced | test_3, test_3b (the in-between Moderate zones are never the primary) |
| 4 Primary structurally valid | test_4 |
| 5 Already-reached rejected | test_5 (18 Nov 06:00, real store); plus the existing D-1 tests |
| 6 Lifecycle | test_6 (real keeper: created, active, primary updated, superseded; no duplicate) |
| 7 The five Version B examples | test_7, test_7b |
| 8 November successes still valid | test_8 (18 Nov 21:00, 19 Nov 12:00 and 14:00, A-equivalent and C); test_8b (20 Nov 08:00 SELL to 1.30841) |
| 9 Pip/price conversion | test_9 (1 point = 1 pip; distance = price − primary edge) |
| 10 Observational only | test_10, test_10b; plus the existing observe-only tests |

## 4. Historical replay comparison

**Baseline (preserved, `docs/research/stp_structural_history_20261120/`):**

| Version | Plans | Destination successes | Invalidations |
|---|---:|---:|---:|
| A — production | 919 | 323 | 345 |
| B — zone retention | 924 | 323 | 350 |
| C — combined | 906 | 332 | 343 |

**C's 31 plans absent from production:**
- **The five Version B plans:** 5 invalidations (static).
- **The other 26, from historical swings:** 13 destination successes, 3 invalidations, 1 destination reached before
  entry, 9 censored.

**Focused replay with the corrected code** (focused_replay.py and focused_compare.py, research store, read only):
- B and C were re-assessed at all 1,003 of the 2,778 decisions where any version had a plan or a "no Major"
  refusal. The other decisions cannot be affected by this change.
- **Decision differences from the stored rows: none.** Direction, condition, trade, entry zone, primary, zone break
  and structure break are identical in every one.
- The reason text changed only by the removed wording: 58 refusals in B, 54 in C.
- Plans: B 924, C 906, as in the baseline. Successes and invalidations are therefore unchanged (B 323/350, C 332/343).

**Primary distance now recorded** (context only):

| Version | Median | 90th percentile | Maximum | Plans over 150 pips |
|---|---|---|---|---|
| B | 13.9 pips (0.17 ADR) | 39.5 (0.45) | 213.7 (2.71) | 5 |
| C | 13.3 pips (0.16 ADR) | 39.5 (0.44) | 213.7 (2.71) | 5 |

The plans over 150 pips are exactly the five Version B examples.

**18–20 November keeper replay (real keeper, production store, 17 Nov 20:25 – 20 Nov 09:00):** B and C reproduce the
stored replays event for event (123 and 125 events; 9 and 11 issued recommendations). The only difference is the
corrected reason text. The 20 Nov 08:00 missing recommendation stays resolved: SELL, primary 1.30841 (historical daily
swing low).

**Gained / lost / changed / introduced / avoided by this correction:** none. Forecasting performance is unchanged by
construction and confirmed by the replays. These counts are not accuracy: in the 20 Nov evaluation the C − A edge was
+0.6 points (−1.0 to +2.4), which is not a measurable improvement.

## 5. Outstanding limitations and the decision for the owner

1. **No predictive edge.**
   - The 20 Nov validation measured direction at 51.6%, with destination-before-break rates at the random-walk
     expectation.
   - Neither the retention fix nor historical discovery changes that measurably.
   - STP is a structural map, not a forecaster.
2. **Far destinations are allowed by design.**
   - Since 9210ca5, a primary can be any distance away. In history this added the five plans above (0.2% of plans).
   - **Decision (owner):** whether STP should have a reachability rule for destinations. Options:
     - (a) **No rule** (recommended on the evidence): five plans in two episodes, consistent with chance, and the
       keeper superseded both before any invalidation. Watch `primary_distance_adr` on live data.
     - (b) Restore 150 pips as a **destination** limit only, keeping discovery unlimited. This uses an existing value
       but partly reverses 9210ca5.
     - (c) A volatility rule, for example primary distance at most k × ADR. This is a new parameter and contradicts
       the approved "ADR never rules a zone out" (FC-03), so it needs a value chosen and approved by the owner.
   - None is implemented.
3. **Identity churn is unchanged.**
   - On 12 May 2025 the same zone edges were superseded three times because the fixed levels underneath changed.
   - This is the identity/dedup question already awaiting a decision (19 Nov). It is not changed here.
4. **The value 156 weeks is still provisional.** `historical_daily_swing_lookback_weeks = 156` was introduced on this
   branch and has not been explicitly approved.

## 6. Approved behaviour preserved

- The H4 dominant-direction correction (candidate C).
- The recommendation lifecycle, D-1 admission and duplicate prevention.
- Major-zone confluence (`major_min_families = 3` plus a daily/weekly level).
- The destination-reached and invalidation rules.
- The 48-week directional window (P-B9), kept separate from historical discovery.

All are unchanged in code and confirmed by the full suite and by the identical decisions in both replays.

## 7. Deployment recommendation

**READY** as an observational map-completeness change (the earlier corrections plus this one), provided the owner
decides:
- the provisional 156-week value;
- the reachability question in section 5 (option a needs no code).

It is not a forecasting improvement. Deploying needs only a planner run (the planner is a fresh subprocess every
5 minutes) plus the owner's dashboard restart for the notation fix already on this branch. Not deployed.
