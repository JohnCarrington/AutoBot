# 7. Technical and functional test specification

**Revision 2, 28 Nov.** This revision adds the tests for review items R1–R5 (§10). Every test that touches
admission asserts two things, **structural permission** (the SCA's state and verdict) and **overall admission**
(the `order` result, naming the layer that decided), as separate fields.

The house practice applies: failing tests first, then the code. The full suite runs in the pre-commit hook.
Crash/restart tests go at every new persistent boundary. The SCA has none: it is stateless and reads current.json.
Fixtures are built from the real records of the named trades: candles from the store, and the STP state
reconstructed from recommendations.jsonl at the entry second. On the Phase 2 build, fixtures also use its
`lineages` and `data_gaps`.

## 7.1 Technical tests (unit / integration)

| ID | Requirement | Fixture / assertion |
|---|---|---|
| TS-01 | Overlap is PD-2 strict overlap; edge-only contact is excluded (PD-3) | opportunities on 13093–103 and 13103–113 do not overlap; 13093–103 and 13093–103 do |
| TS-02 | Position against **each opportunity's own zone** in the trade's direction. NEAR comes from settings. **PAST = at or beyond the opportunity's own `invalidation.zone_break_close`** (R1), never NEAR, never a literal | BUY 13126.9 vs SELL 13115.1–123.9 (break 13126.9) → PAST; 13126.8 → AT. With `break_beyond_pips` set to 5 in the test settings, 13126.9 → AT (the boundary follows STP's setting) |
| TS-03 | S4(a): AT an unbroken opposing opportunity | 25 Nov 18:02 slow grind BUY 13119.0 vs SELL 1800-35 WAITING → S4 |
| TS-04 | S4(b): PAST an ACTIVE opposing opportunity with no D-20 break | 25 Nov 18:45 BUY 13127.1 → S4; the same with 1800-35 BROKEN up → S6 |
| TS-05 | S4(c): against a live break | 26 Nov 11:55 slow grind SELL in 13093–103 with SELL 0400-38 BROKEN up → S4 |
| TS-06 | S5: contested pair, reversal family only | 26 Nov 06:01 bounce 5m BUY (BUY 0000-37 + SELL 0400-38 ACTIVE) → S5. The same idea as slow grind → S4. Rejection candle not at the zone → S4. |
| TS-07 | S6: the opposing opportunity's own D-20 break in the trade's direction | 26 Nov 11:40 bounce 5m BUY → S6 |
| TS-08 | S7 is naming only | 27 Nov 10:00 breakout BUY → S7, verdict permit; removing the ended opportunities → S1, the same verdict |
| TS-09 | S3: approaching (record only by default) | 26 Nov 12:51 SELL 13104.6 → S3; permitted under D-1, deferred under D-2 |
| TS-10 | S2 when STP is current with no relevant structure; the 61.4 sweep | 25 Nov 15:05:01 sweep BUY 13061.8 → S2, permitted (regression guard named in the brief) |
| TS-11 | Pending D-20 break via `_catch_up` on complete data | an hourly close ≥ `zone_break_close` stored, not yet processed by the tracker, every 5m stored → S6, not S4 |
| TS-12 | State as of the order time; the publication race | an opportunity created at 13:00:03 is visible to an idea at 13:00:12 only if current.json was written before. Both orderings are tested, and the result is journalled with `written_utc`. |
| TS-13 | **UNKNOWN, not S2** (R5) | unreadable / `written_utc` older than `analyser.out_of_date_after_minutes` / `current` not True / stale live price → state `UNKNOWN`, verdict permit, decision `structure unknown` with the reason. The record never carries `S2`. |
| TS-14 | Phase 2 membership | a lineage member COMPLETED `after_trade` has ended: not a barrier |
| TS-15 | Journal shape | `structure refused` + `order` with result `structure: watch and wait`, the same fields as `entry filter refused`, plus **every opportunity's own finding**. A permitted idea gets one `idea.steps` line naming the state, the verdict and the deciding opportunity. |
| TS-16 | Switch | STRUCTURAL_COHERENCE off → `_place` behaves byte-identically to today (the full suite passes unchanged with the switch off in the test switches) |
| TS-17 | No deferred execution | after a refusal, no queue, timer or file is written; the same idea on the same candle is not re-tried (the engine's one-try rule) |
| TS-18 | The rule-11 key is not consumed | a refused STP-authorised idea leaves `used_signals()` unchanged; a later fresh setup on the same lineage and test is not refused by rule 11 because of the SCA |
| TS-19 | Rejection candle always emitted (WP-2) | bounce 5m and level-reversal candidates carry `rejection_candle` with STP_AUTHORISES_ENTRIES off; trigger prices and times unchanged against fixtures (no confirmation change) |
| TS-20 | Read-only | the SCA never writes to data/planner; the planner never imports the SCA (mirrors test_stp_final_validation test_10) |
| TS-21 | Room-rule independence (only if adopted) | STRUCTURAL_ROOM on/off leaves SCA verdicts unchanged, and vice versa; separate journal kind `room refused` |
| **TS-22** | R3: no S6 from a BROKEN opportunity with an open gap | opposing BROKEN in the trade's direction, `data_gaps` status open → S4(d) *unverifiable*, with Phase 2's reason text in `why`; the same gap `reconciled` → S6 |
| **TS-23** | R3: no pending break while a 5m candle is missing | hourly close beyond `zone_break_close` stored, but `_catch_up` reports "IG's 5-minute candle … is not stored yet" → S4(d); candle stored → S6 |
| **TS-24** | R3: lineage uncertainty blocks resolution | lineage `tests.uncertain` or `review_hours` non-empty on the opposing opportunity → no S5, no S6 |
| **TS-25** | R3: no S5 with an unreconciled agreeing member | contested pair, agreeing member with an open gap → S4; gap reconciled → S5 |
| **TS-26** | R3: reconciled vs review | gap `reconciled` → normal judgement; gap `review` → stays unresolved until the review clears it; an ended opportunity with a gap stays ended (no reopening; `classification corrected` changes nothing) |
| **TS-27** | R3: one interpretation | the adapter recognises exactly Phase 2's zone-break and PD-5 reason strings (fixtures from `stp/authorise.py`); if either wording changes, this test fails. A test confirms the module calls `_catch_up`/`unreconciled` (monkeypatched to return nothing → no pending-break S6) and reads no 1h candle itself. |
| **TS-28** | R4: permission ≠ admission | a matrix over gate verdict × entry filters × SCA verdict × day_directions × safety (rule 11) → admitted only if all pass. An SCA permit never turns a refusal into an admission. A gate refusal writes no structure step. A rule-11 refusal is written after a structure step "permit". |
| **TS-29** | R5: the gate stays fail-closed | gate on, STP stale → gated strategy refused by the gate with today's exact text, and the SCA not called; ungated strategy → UNKNOWN, permitted |
| **TS-30** | R5: one availability test | for a set of current.json fixtures (missing, unreadable, old, `current` false, stale tick, fine), "unavailable" for the SCA ⇔ `authorise()` refuses at steps 1–2 |
| **TS-31** | R2: independent of order | shuffling `opportunities[]` (all permutations of the 26 Nov 11:40–11:55 and 27 Nov 15:11 fixtures) gives the same state, verdict and findings |
| **TS-32** | R1: ended opportunities are never barriers; no time window | an opposing opportunity ended "confirmed break held" 1 minute or 3 days earlier → no S4 from it in either case; S7 naming only |
| **TS-33** | R1: break price read at decision time | a "changed" re-plan moves the zone edges and `zone_break_close` → PAST/AT follow the new values at once |

## 7.2 Functional tests (owner-readable, on real days)

The day is replayed through `Trading` with the switch on, on the Phase 2 build. Only decisions are compared, never
P&L. Each row states the structural permission and the overall admission.

| ID | Day / trade | Structural permission (SCA) | Overall admission |
|---|---|---|---|
| FS-01 | 25 Nov 15:05 session sweep BUY (+61.4) | S2 permit | opens unchanged: same entry, stop and steps, plus one SCA line |
| FS-02 | 25 Nov 12:25 session sweep BUY | S4 (inside SELL 1200-29) | refused: structure. The 15:05 sweep still opens (FS-01). |
| FS-03 | 25 Nov 18:45 slow grind and 19:10 EMA pullback BUYs | S4(b) past 1800-35 (ACTIVE; STP wick sweeps at 19:00 and 20:00) | refused: structure |
| FS-04 | 26 Nov 06:01 / 06:30 bounce 5m | S5 each: the opposing member resolved by the pair, the agreeing one S1 | open (Phase 2 `#t1` each) |
| FS-05 | 26 Nov 11:45 breakout and 11:55 slow grind SELLs | S4: three opposing BUYs unresolved, plus SELL 0400-38 broken against | refused: structure |
| FS-06 | 23 Nov 14:39 EMA pullback SELL (+30.0) | S2 | opens |
| FS-07 | 24 Nov 08:55 breakout BUY (+50.0) | S2 | opens |
| FS-08 | 27 Nov 13:20–14:23 SELL ideas | S4(b) past 1305-58 | refused: structure. Released by the 15:00 D-20 break; the 15:11 bounce SELL opens (S5). |
| **FS-09** *(rewritten, R4)* | **27 Nov 12:01 bounce 5m BUY** | **S7 permit** (1200-57 not published; 0300-56 ended; held breaks below) | **refused by Phase 2**: the gate finds no live BUY opportunity (PD-2 withholding). With the lineage map applied, rule 11 refuses alias `0300-56#t1`. The test asserts the refusing layer and that no SCA permit is recorded as admission. Gate off: the SCA adds no duplicate rule (asserted). |
| FS-10 | 18–19 Nov (no live STP) | S2 all day | no structure refusal |
| FS-11 *(R5)* | A planner outage (file removed mid-day), gate on and gate off | UNKNOWN for every idea, never S2 | gate on: the three gated strategies are refused by the gate (fail-closed, today's text); the others trade unchanged. Gate off: all unchanged. Dashboard: "Structure unknown". |
| **FS-12** *(R4)* | 26 Nov 11:40 bounce 5m BUY (+14.0), the genuine re-armed test `0000-37#t2` | S6 | opens (Phase 2 `#t2`, FL-A5) |
| **FS-13** *(R2)* | 27 Nov 01:10–01:50 BUYs at 13093–103 | 01:10 S5 (pair 0100-51 / 0100-52). 01:35, 01:45, 01:50: S4(b) past the new SELL 0100-51. The earlier ended held breaks clear nothing. | 01:10 per the other layers; the rest refused: structure until the 02:00 break |
| **FS-14** *(R2)* | 27 Nov 15:11 bounce 5m SELL, 15:47 slow grind SELL | 15:11: 1305-58 S6, 1500-60 S5 with 1500-59 → S5. 15:47: 1305-58 S6, but 1500-60 unresolved (continuation family) → S4. | production state: 15:11 opens. Phase 2 state before OP-1: 15:11 is S4(d) unverifiable (FS-23) and refused under D-R2. 15:47 refused: structure. 16:05 slow grind S6, then refused by safety (FS-24). |
| **FS-15** *(R2, synthetic)* | **Indirect overlap.** BUY reversal at 105, rejection low 99. Agreeing BUY A 98–103, opposing SELL O1 100–108, opposing SELL O2 104–112. A overlaps O1, O1 overlaps O2, A does not overlap O2. | O1 S5 (pair with A); O2 S4(a): no direct agreeing pair | refused: structure |
| **FS-16** *(R2, synthetic)* | **Contested pair plus an independent barrier.** As FS-15 without O2, plus SELL O3 90–95 ACTIVE, entry beyond its break 98 | O1 S5; O3 S4(b) | refused: structure |
| **FS-17** *(R2, synthetic)* | **Edge-only contact.** Agreeing BUY 108–115, opposing SELL 100–108, rejection reaches both | no pair (PD-3) → S4(a) | refused: structure |
| **FS-18** *(R2, synthetic)* | **S5 cannot clear S4(c).** BUY reversal AT an agreeing BUY zone BROKEN down, with another live BUY overlapping it and a live SELL on it | S4(c) stands | refused: structure |
| **FS-19** *(R2, synthetic)* | **Two opposing opportunities on one zone, one broken.** SELL O1 BROKEN up, newer SELL O4 ACTIVE overlapping, BUY continuation PAST both | O1 S6; O4 S4(b) | refused: structure |
| **FS-20** *(R2, synthetic)* | **Rejection reached the agreeing zone only.** Pair overlaps, but the rejection candle reaches only A's part | O: S4(a) | refused: structure |
| **FS-21** *(R2+R3, synthetic)* | **Three overlapping.** Opposing O; agreeing A1 (open gap) and A2 (reconciled), both directly overlapping O and reached | O: S5 via A2 only; with A2 removed → S4 | permitted / refused accordingly |
| **FS-22** *(R1)* | 27 Nov 13:00–16:05 hour by hour | S4(b) past 1305-58 in the 13:00 hour. The 13:00 close is 13120.1 (closed beyond, 1.2): not a break, still S4(b) at 14:05–14:23. The 14:00 close (13113.8) breaks it, so S6 through `_catch_up` from the moment IG's 14:00 hourly candle is stored, before the tracker runs. 1500-60: S4(b) in the 15:00 hour, S6 from 16:00. | refusals and releases at exactly those closes; no release at any other time |
| **FS-23** *(R3)* | 27 Nov on the Phase 2 build, with the 12:00–12:10 restart gap (OP-1), unreconciled and then reconciled | Unreconciled: no opportunity whose evidence runs through the gap gives S5 or S6. **15:11 bounce SELL: 1500-59's lineage has the uncertain 12:00 hour, so it gives no S5, and 1500-60 makes it S4(d) unverifiable.** Reconciled: verdicts equal the reconciled replay. | unreconciled: 15:11 refused (Phase 2 D-R2 first, at the gate). Reconciled: as Phase 2 re-decides. |
| **FS-24** *(R4)* | 23 Nov 10:42 level reversal BUY; 27 Nov 16:05 slow grind SELL | S2; S6 (permit) | **refused by the safety limit** (the earlier trade was open). The journal shows the structure step "permit" and the safety refusal as separate fields. |

## 7.3 Acceptance

- The full suite is green with the switch off and on, run once and not concurrently (shared checkout).
- FS-01 … FS-24 are as expected.
- R1: no S4(b) survives an hourly close at which price is beyond that opportunity's break price (FS-22, TS-32,
  TS-33).
- R2: no resolution transfers between opportunities (FS-13 … FS-21, TS-31).
- R3: no resolution from unreconciled or incomplete evidence (TS-22 … TS-27, FS-23).
- R4: no SCA permit is ever recorded or reported as admission (TS-28, FS-09, FS-24).
- R5: UNKNOWN is never S2; the gate is unchanged and fail-closed (TS-13, TS-29, TS-30, FS-11).
- An independent code review before deployment, as for Phases 1 and 2.
