# 10. Review clarifications R1–R5 (revision 2 of the design pack)

28 November 2026. This answers the independent review of the pack at `c7ba045`. It is design only: nothing is
implemented and nothing in production is changed. The scope stays the same: no new filter, no new threshold, and
no change to STP's forecasting. Where a clarification changes the design, the change is written into
03_ARCHITECTURE, 05_DECISION_REGISTER, 06_HISTORICAL_IMPACT and 07_TEST_SPECIFICATION. This document gives the
reasoning and the evidence.

Evidence was re-run with `evidence/scripts/classify3.py` (the amended rules) and `evidence/scripts/r1_evidence.py`
on the same data snapshot as revision 1. Outputs: `evidence/output/sca3.json`, `breadth3.json`,
`classify3_trades.txt`, `r1_r2_ideas.txt`.

## Summary of what changed

| Item | Revision 1 (c7ba045) | Revision 2 |
|---|---|---|
| Unit of judgement | A *group* of overlapping zones, judged as one | **Each live STP opportunity judged on its own.** One opportunity's resolution never clears another's conflict (R2). |
| "PAST" boundary | More than NEAR (3 pips) beyond the group's far edge | **At or beyond the opportunity's own `zone_break_close`**, the price STP's D-20 rule uses (R1). Numerically the same today (NEAR = `break_beyond_pips` = 3), but it is now tied to STP's own rule. |
| Ended opportunities | Ended by "confirmed break held" in the last **24 h** were still read | **An ended opportunity is never a barrier and never resolves one.** The 24-hour look-back was an arbitrary time threshold and is removed (R1). A held break now only *names* S7, which permits exactly as S2 does. |
| S5 contested zone | The rejection reached the group band, and the group held a live agreeing member | The rejection candle reached **this** opposing opportunity's zone **and** a live agreeing opportunity whose zone **directly** overlaps it (PD-2: strict overlap, not edge-only, not through a third zone). It resolves that opposing opportunity only (R2). |
| Unreconciled evidence | "An unreconciled opposing opportunity is still a barrier; an unreconciled agreeing one gives no S5" | Also: **no resolution of any kind (S5, S6, pending break) from an opportunity with Phase 2 `unreconciled()` reasons or from a `_catch_up` that reports missing candles.** The state stays S4, marked *resolution unverifiable* (R3). |
| Duplicate protection | Not discussed. The 27 Nov 12:01 BUY was wrongly called "a legitimate new test after re-arming" | **Structural permission and overall admission are kept apart.** The SCA can only refuse. It runs after the STP gate and before the safety rules (rule 11), so it can never re-admit what Phase 2 refuses. The 12:01 BUY is refused by Phase 2. The genuine re-armed example is **26 Nov 11:40 (+14.0, `0000-37#t2`)** (R4). |
| STP unavailable | "S2 (unknown)", journalled `structure unknown` | **A separate state, `UNKNOWN`**, never counted or shown as S2/neutral. The fail-open verdict is kept. Availability uses the gate's own checks and settings (rev 1's "10 min" is the gate's `analyser.out_of_date_after_minutes`, not a new number). The gate stays fail-closed (R5). |

**Effect on the evidence.** No actual trade changes state (86 of 86 identical, `classify3_trades.txt`). Eight
ideas change, out of 416. Deferred (S4) ideas go from 75 to 82: 19.7% of ideas, 46 BUY and 36 SELL.

| Idea (27 Nov) | Rev 1 | Rev 2 | Why |
|---|---|---|---|
| 01:10 bounce 5m BUY 13101.6 | S7 | S5 | Contested pair SELL 0100-51 / BUY 0100-52. The older held breaks on the zone no longer decide it. |
| 01:35, 01:45, 01:50 bounce 5m and level reversal BUYs (6 ideas) | S7 | **S4** | Past the new SELL 0100-51 (ACTIVE, created 01:00) with no D-20 break yet. The 0400-38/1200-42 breaks were held, but those opportunities had ended. Under rev 1 they cleared a newer, independent opportunity. STP broke 0100-51 at the 02:00 close. |
| 17:34 level reversal BUY 13106.8 | S7 | **S4** | Past the new SELL 1700-61 (ACTIVE). STP recorded a wick sweep at 18:00: not overcome. |

None of these ideas became a trade. This is the R2 defect the review anticipated, now found and fixed.

---

## R1 — An older ACTIVE opposing zone cannot indefinitely block continuation further away

### The rule (revision 2)

S4(b) applies to an opposing opportunity *O* only when the entry is **at or beyond O's own `zone_break_close`**
in the trade's direction, *O* is ACTIVE, and STP has not broken it. `zone_break_close` is O's far edge ± 3 pips:
`invalidation.zone_break_close`, read at decision time, the same price STP's D-20 rule uses. No distance or time
is introduced.

### Why it cannot persist (STP's own lifecycle)

1. **STP judges every live opportunity at every hourly close.** There is no distance or age limit
   (`planner/opportunities.py` `hourly`, fadf228 :208–217, unchanged in Phase 2 :634–713). If the close is at or
   beyond `zone_break_close`, the opportunity becomes BROKEN.
2. **S4(b) needs price to be beyond that same price.** At the close of the hour in which S4(b) arises, there are
   only two outcomes:
   - The close is beyond. STP breaks *O* at that close, and the SCA gives S6 from that second, through
     `_catch_up`, even before the tracker runs.
   - The close is back inside the band. STP records it as a "wick sweep", "closed beyond" (< 3 pips) or "reclaim".
     That is STP's own record that the zone was **not** overcome, and at that close the price is no longer PAST.
3. **After a break, the zone is either restored or ended.**
   - If the break fails (a close back inside the far edge within `failed_breakout_within_candles` = 3), *O*
     returns to Watch & Wait. Price is then back at the zone, so this is no longer a trade "further away".
   - If the break holds, STP ends *O* (INVALIDATED "confirmed break held"). Under revision 2 an ended opportunity
     is never a barrier again.
   - The other STP endings remove *O* too: destination reached (COMPLETED), 4-hour structure break, the 00:00 UK
     rollover, or a supersession.
4. **The other S4 forms are also bounded.**
   - S4(c), an agreeing zone BROKEN against the trade, lasts at most STP's 3-candle break window. After that the
     zone is restored (ACTIVE, which gives S1 if the entry is at it) or ended.
   - S4(a) is at the zone itself, not further away.

So an old ACTIVE zone can hold back continuation trades beyond it only within the hour in which price is beyond it.
That repeats only while STP keeps finding the hour's close back inside the break band, which is exactly the brief's
"no evidence that an opposing zone had been overcome". Once one close is beyond, the zone is broken and continuation
is permitted (S6). If the break holds, the zone has ended and plays no further part.

### Evidence: every S4(b) idea, 18–27 Nov (35 ideas, 14 hour-episodes)

Hour figures are IG's sell-price hourly candles from the store. "At that close" is STP's own recorded event for
that opportunity.

| Opportunity, zone | Hour (UTC) | Hour high / low / close | STP at that close | S4(b) ideas | Then |
|---|---|---|---|---|---|
| 20 Nov SELL 1300-8, 13111.6–121.9 | 13:00 | 13128.6 / 13111.0 / 13119.0 | wick sweep | 2: 13:10 level reversal BUY (owner −26.1), 13:25 slow grind BUY −15.0 | not overcome |
| 23 Nov SELL 0100-10, 13113.2–123.7 | 06:00 | 13130.5 / 13119.7 / 13127.3 | break, 3.6 beyond (single-tracker mode: ended) | 1: 06:45 EMA pullback BUY −12.0 | resolved at 07:00 |
| 25 Nov SELL 1800-35, 13115.1–123.9 | 18:00 | 13129.2 / 13114.4 / 13123.7 | wick sweep | 2: incl. 18:45 slow grind BUY −5.1 | not overcome |
| same | 19:00 | 13128.9 / 13121.3 / 13121.5 | wick sweep | 6: incl. 19:10 EMA pullback BUY −5.7 | not overcome |
| 26 Nov SELL 0400-38, 13093–103 | 07:00 | 13113.0 / 13095.7 / 13103.4 | closed beyond (0.4) | 1 | not overcome |
| same | 09:00 | 13117.3 / 13103.7 / 13107.8 | broken, 4.8 | 1 | resolved 10:00; 11:40 BUY +14.0 is S6 |
| 27 Nov SELL 0100-51, 13093–103 | 01:00 | 13114.9 / 13094.1 / 13114.9 | broken, 11.9 | 6 | resolved 02:00 |
| 27 Nov SELL 0200-53, 13108.5–119.1 | 02:00 | 13128.8 / 13113.7 / 13124.1 | broken, 5.0 | 1 | resolved 03:00 (failed 04:00: back at the zone) |
| same | 05:00 | 13131.9 / 13116.0 / 13125.3 | broken, 6.2 | 2 | resolved 06:00, held, ended 09:00 |
| 27 Nov BUY 0300-56, 13121.3–130.5 | 08:00 | 13130.1 / 13115.4 / 13124.2 | reclaim | 2 SELLs | not overcome (zone completed 11:05) |
| 27 Nov BUY 1305-58, 13121.3–130.3 | 13:00 | 13129.9 / **13107.3** / 13120.1 | closed beyond (1.2) | 3 SELLs | not overcome |
| same | 14:00 | 13122.0 / 13109.6 / 13113.8 | broken, 7.5 | 4 SELLs | resolved 15:00 |
| 27 Nov BUY 1500-60, 13108.5–119.1 | 15:00 | 13116.1 / 13097.8 / 13105.4 | broken, 3.1 | 3: incl. 15:47 slow grind SELL (owner +4.3) | resolved 16:00; 16:05 SELL is S6 |
| 27 Nov SELL 1700-61, 13093–103 | 17:00 | 13106.9 / 13094.7 / 13099.3 | wick sweep | 1 | not overcome |

- **7 of 14 episodes ended in a D-20 break at that very close.** The other 7 closed back inside STP's break band.
- **No S4(b) idea occurred after an hourly close at which price was beyond that opportunity's break price.**
- **The longest S4(b) on one opportunity was two consecutive hours:** 1305-58, 27 Nov 13:00–15:00. Price fell 14
  pips beyond the zone within the 13:00 hour (low 13107.3), but the close came back to 13120.1, only 1.2 pips
  beyond the edge. STP rules that this is not a break, so the SELLs waited for the next close, which broke it.

### Residual case (stated, not hidden)

If an opportunity carries an unreconciled Phase 2 data gap, its resolution cannot be verified (R3). It then
stays S4 for trades at or past it until Phase 2 reconciles the gap. Meanwhile STP's other lifecycle rules (4-hour
structure break, destination, rollover) still run on it and can end it. If Phase 2 leaves the gap "for review",
it stays until the owner's D-R2 review procedure (`planner/review.py`). This follows from R3 and is recorded as a
consequence of D-14.

---

## R2 — Contested and overlapping zones: S4 takes precedence over S5

### Precedence rules (revision 2)

1. **Every live STP opportunity (WAITING, ACTIVE, BROKEN) is judged separately** against the trade, using its own
   zone, its own status and its own break price.
2. **The verdict is Watch & Wait if any one opportunity is unresolved for this trade (S4).** The reported state is
   the highest per-opportunity finding in S4 > S3 > S5 > S6 > S7 > S1 > S2.
3. **A resolution belongs only to the opportunity it resolves.**
   - S6 resolves only the opportunity that STP broke.
   - S5 resolves only the opposing opportunity whose zone the strategy's own rejection candle reached, and only
     when a live agreeing opportunity (WAITING or ACTIVE) whose zone **directly** overlaps it was reached by the
     same candle.
   - **Neither ever clears another opportunity's S4.**
4. **Direct overlap only.** This is PD-2's strict overlap. Zones that only share an edge do not count (PD-3).
   Chained or indirect overlap, where A overlaps B and B overlaps O but A does not overlap O, does not make A and O
   a contested pair.
5. **S5 never resolves S4(c)** (an agreeing zone BROKEN against the trade). Only STP's failed-breakout rule restores
   such a zone.
6. **S5 is for the reversal family only** (both bounces, level reversal, session sweep, NY open reversal, range),
   whose own confirmation is a rejection. Continuation and breakout ideas at a contested zone are judged by S4/S6.
7. **No S5 from unreconciled evidence** on either member of the pair (R3).
8. **The result is independent of the order of opportunities in `current.json`** (TS-31).

### Real multi-opportunity cases (all in the functional tests)

| Case | Opportunities | Per-opportunity findings | Result |
|---|---|---|---|
| 26 Nov 06:01 bounce 5m BUY / 06:30 SELL | BUY 0000-37 ACTIVE, SELL 0400-38 ACTIVE, same zone 13093–103 | each idea: the opposing member S5 (rejection reached both), the agreeing member S1 | permit both (S5) |
| 26 Nov 11:40 bounce 5m BUY (+14.0) | BUY 0000-37, 1000-39, 1100-41 ACTIVE; SELL 0400-38 BROKEN up | the only opposing member is broken in the trade's direction: S6; the BUYs S1 | permit (S6) |
| 26 Nov 11:45 breakout SELL, 11:55 slow grind SELL | same four | three opposing BUYs AT and unresolved: S4(a). SELL 0400-38 broken against the trade: S4(c). Not reversal family: no S5. | Watch & Wait |
| 27 Nov 01:35–01:50 BUYs | new SELL 0100-51 ACTIVE; ended SELLs 0400-38 / 1200-42 (breaks held) | 0100-51 PAST, unresolved: S4(b). The ended ones only name S7. | Watch & Wait (changed from rev 1) |
| 27 Nov 15:11 bounce 5m SELL (owner +9.0) | BUY 1305-58 BROKEN down; SELL 1500-59 and BUY 1500-60 ACTIVE on 13108.5–119.1 | 1305-58: S6. 1500-60: S5 with 1500-59 (direct overlap, both reached). 1500-59: S1. | permit (S5) on production data; S4(d) on the Phase 2 build before OP-1 (R3) |
| 27 Nov 15:47 slow grind SELL (owner +4.3) | 1305-58 BROKEN; 1500-60 ACTIVE | 1305-58: S6. 1500-60: PAST, unresolved: S4(b). Continuation family: no S5. | Watch & Wait. 1305-58's break does not clear 1500-60. |

**Indirect overlap did not occur in the window.** No idea had a chained overlap among the opportunities bearing a
state (`r1_r2_ideas.txt`). The indirect and multi-zone cases are therefore specified as synthetic functional tests
(FS-15 to FS-21, §7), built from real fixtures with constructed opportunities.

---

## R3 — No resolution from incomplete or unreconciled evidence

### Rules (revision 2), all reusing Phase 2 unchanged

1. **The SCA never recomputes a lifecycle or a break.** It reads STP's opportunities and lineages from
   `current.json` (the Phase 2 build). For what the tracker has not yet processed, it calls
   `stp.authorise._catch_up` and `stp.authorise.unreconciled` exactly as the gate does. It reads no hourly candle
   itself and has no break rule of its own.
2. **A resolution needs reconciled evidence.** An opposing opportunity is resolved (S6 from BROKEN, S6 from a
   pending break, or S5) only when all of these hold:
   - `unreconciled(state, o)` is empty for it, and for an S5 pair it is also empty for the agreeing member;
   - for a pending break, `_catch_up` reports the zone break **and** reports no PD-5 "IG's 5-minute candle … is not
     stored yet" reason.
3. **Otherwise the opportunity stays unresolved.** If the entry is AT or PAST it, the result is S4 marked
   *resolution unverifiable*, and Phase 2's reasons are copied word for word into the journal (`why`).
4. **The barrier itself is STP's.** An opportunity with an open gap is still a live STP opportunity, so it still
   counts as a barrier when the entry is AT or PAST it. The SCA does not treat a gap as an ending.
5. **Endings stand, as in Phase 2.** Phase 2 never reopens an ended opportunity; a late reconciliation only corrects
   its classification (`_reconcile_ended`). The SCA follows this: an ended opportunity is neither a barrier nor
   reopened, and a "classification corrected" event changes nothing for the SCA.
6. **Interface detail (WP-1).** `_catch_up` returns its reasons as text. The SCA reads two of them (the zone break
   and the PD-5 missing-candle line) through a thin adapter, and a test pins the adapter to Phase 2's exact wording
   (TS-27), so a wording change fails the suite rather than silently changing behaviour. Changing `_catch_up` to
   return tagged reasons would be a Phase 2 code change, so it is not proposed here.
7. **R3 is per opportunity; R5 is for the whole of STP.** If STP as a whole is unavailable, see R5.

### Demonstration

- **On the data:** fadf228's `current.json` and `recommendations.jsonl` carry no Phase 2 gap fields, so no
  historical figure in §6 depends on R3. R3 applies from the Phase 2 build onwards.
- **In the tests:** each route by which incomplete evidence could resolve a barrier has its own failing-first test:
  - BROKEN with an open gap → S4 unverifiable (TS-22);
  - a pending break while a 5-minute candle is missing → S4 (TS-23);
  - lineage `uncertain` or `review_hours` → no resolution (TS-24);
  - an agreeing member with a gap → no S5 (TS-25);
  - a gap reconciled → normal judgement resumes; a gap left for review → still unresolved (TS-26);
  - the adapter pinned to Phase 2's reasons, with no other break computation in the module (TS-27).
- **On a real day: 27 Nov 15:11 bounce 5m SELL.**
  - On production data it is S5: the contested pair 1500-59 SELL / 1500-60 BUY, with the rejection reaching both.
  - On the Phase 2 build before OP-1, the agreeing 1500-59's lineage count runs through the uncertain 12:00 hour,
    which was built from 9 of 12 candles (Phase 2 REVIEW_R3_2, Saturday pack §8). Its evidence is unreconciled, so
    it gives no S5. 1500-60 stays unresolved, and the state is **S4(d), resolution unverifiable**.
  - This matches Phase 2, which refuses the same idea under D-R2. The SCA reaches the same conclusion from the
    same Phase 2 field and adds no interpretation of its own.
  - After OP-1 reconciles the hour, the S5 judgement resumes (FS-23).

---

## R4 — Structural permission is not trade admission

### Composition

A trade is admitted only if **every** layer of `Trading._place` lets it through, in this order:

1. try recorded
2. STP gate (the three gated strategies, when STP_AUTHORISES_ENTRIES is on)
3. entry filters
4. **SCA**
5. (room rule, only if ever adopted)
6. `day_directions`
7. `OrderSender.place` → safety rules (including rule 11, one signal one trade) → IG

The SCA has exactly two outcomes, *refuse* (Watch & Wait) or *continue*. It has no "admit" outcome. It is not
in the gate's bypass list, and it bypasses nothing.

- **A gate refusal returns before the SCA runs**, so no structure step is written for that idea.
- **A rule-11 refusal comes after the SCA.** The journal shows the structure step ("permit, S7") and then the
  safety refusal. The two are separate fields (`idea.steps` versus `order.result`), and every report keeps them
  apart.

### The 27 Nov 12:01 BUY (AB261127120127)

| Build | Structural permission (SCA) | Duplicate protection | Overall admission |
|---|---|---|---|
| Production fadf228 (what happened) | S7 permit (computed afterwards; no SCA existed) | none: 1200-57 restarted the key at `#t1` (Phase 2 L-2) | opened; owner closed it at −1.4 |
| Phase 2 + SCA, gate on | S7 permit. 1200-57 is not published, 0300-56 has ended, and the breaks held below. | the gate finds no live BUY opportunity (PD-2 withholds 1200-57, whose test 1 never re-armed). With the lineage map, rule 11 also refuses alias `0300-56#t1` (Phase 2 FL-A3, FL-M1). | **refused by Phase 2**, whatever the SCA says |
| Phase 2 + SCA, gate off (PD-0, today) | S7 permit | STP duplicate protection applies only to STP-authorised ideas (Phase 2 scope). The SCA adds no duplicate rule (no new filter). | not decided by the SCA |

**Correction to revision 1:**
- **Wrong:** 02, 06, 07 (FS-09) and the README called the 12:01 BUY "a legitimate new test after re-arming". It is
  the duplicate of test 1 that Phase 2 found (L-2).
- **The genuine re-armed new test is 26 Nov 11:40 bounce 5m BUY +14.0** (`0000-37#t2`, after the 10:00 re-arm).
  Its SCA state is S6 (permit), Phase 2 admits `#t2` (FL-A5), and it is admitted overall.

---

## R5 — Unknown structure is not neutral structure

| Condition | SCA state | Verdict | Journal | Dashboard / summary |
|---|---|---|---|---|
| STP is current and no opportunity is in a conflicting position | **S2 neutral** | permit | `idea.steps`: "structure: neutral" | "Neutral" |
| **STP unavailable:** the file is missing or unreadable; `written_utc` is older than the gate's limit (`analyser.out_of_date_after_minutes`); `current` is not True; or the live price / latest 5m is older than that limit | **UNKNOWN** (not one of S1–S7) | permit (fail open, F-1) | decision `structure unknown`, with the reason in the gate's own words; `idea.steps`: "structure: unknown (STP unavailable: …), permitted" | "Structure unknown", shown distinctly and never as Neutral. The daily summary counts it separately, and breadth figures never fold it into S2. |
| STP current, one opportunity's evidence unreconciled, entry AT or PAST it | **S4**, *resolution unverifiable* | Watch & Wait | `structure refused`, with Phase 2's reasons | "Watch & Wait (unverifiable: data gap)" |

- **Same availability test as the gate.** The SCA applies the same checks as `authorise()` steps 1–2, with the
  same settings, so the two cannot disagree on whether STP is available. Extracting a shared helper would change
  Phase 2's `stp/authorise.py`. Instead the SCA repeats the checks and an equivalence test pins them to the gate's
  refusals (TS-30).
- **The STP gate keeps its fail-closed behaviour.** With the gate on and STP unavailable, the three gated
  strategies are refused at the gate exactly as today (same journal text), before the SCA runs. The ungated
  strategies are permitted with UNKNOWN (TS-29, FS-11). The SCA's fail-open only means it does not add its own
  refusal. It never authorises anything, so an UNKNOWN can never let a gated idea past the gate.
- **History.** The window's STP availability cannot be reconstructed, because `current.json` is overwritten
  every run. Every S2 in §6 is "neutral as reconstructed from recommendations.jsonl". In the build, UNKNOWN is
  separate from the first idea onwards.
