# 5. Decision register (awaiting the owner)

This is research and design only; nothing is built. Each decision lists its options (§4), its evidence (§6) and a
recommendation. Implementation waits for approval.

**Revision 2, 28 Nov.** This revision answers the independent review's clarifications R1–R5
([10_REVIEW_CLARIFICATIONS.md](10_REVIEW_CLARIFICATIONS.md)):
- D-4, D-5, D-9 and D-14 are amended;
- D-16 and D-17 are new;
- the scope is unchanged, with no new filter and no new threshold;
- the errata are listed at the end.

| ID | Decision | Options | Recommendation | Evidence / reason |
|---|---|---|---|---|
| **D-1** | Adopt a common structural coherence assessment (SCA) in `Trading._place`, for all ten strategies | adopt / do not adopt | **Adopt** | 11 bot losers and 0 bot winners in the S4 state (§6.2). Every strategy passes the same point. Reuses STP only. |
| **D-2** | **Partly supersede OD-18 A** ("no new rule against an ungated trade opposite an STP opportunity", approved 24 Nov) | keep OD-18 A / supersede it for S4 only | **Supersede for S4 only** | OD-18 A is why the 25 Nov 18:45/19:10 BUYs opened (coherence review 25 Nov). The SCA never refuses on an opposing label alone: S1/S2/S5–S7 permit. |
| **D-3** | Source of a zone's role | A-1 STP labels + lifecycle / A-2 price-path inference / A-3 all levels | **A-1** | A-2 was unstable when tested and is a new algorithm. A-3 refuses the +£614 sweep and the +£200 slow grind (Phase 1). |
| **D-4** *(amended, R1)* | Scope of S4 | B-1 AT only / B-2 AT + past-unconfirmed / B-3 + untouched WAITING | **B-2**, judged per opportunity, with three clarifications (below the table) | B-2 adds 3 bot losers (20 Nov 13:25, 23 Nov 06:45, 25 Nov 18:45) and no winners. In the window, 35 S4(b) ideas in 14 hour-episodes were each settled at that hour's close: 7 by a break, 7 by a close back inside (§10 R1). Cost: continuations wait for the D-20 close; the longest wait was 2 h (27 Nov 13:00–15:00). |
| **D-5** *(amended, R2)* | Contested zones (OD-33) and overlapping zones | C-1 reversal-family exemption with own rejection / C-2 none / C-3 all families | **C-1, per opportunity, with explicit precedence** (below the table) | Keeps OD-33. C-2 would defer all 35 S5 ideas and three trades (26 Nov 06:01 +5.0, 06:30 −7.3, 27 Nov 15:11 owner +9.0). Judging per opportunity changed 8 ideas and no trades. On 27 Nov 01:35–01:50 and 17:34, old held breaks had cleared newer unresolved opportunities (§10). |
| **D-6** | Opposite open positions | G-1 record only / G-2 require a justifying state | **G-1** | G-2 refuses 4 bot winners (+30.0, +20.0, +12.2, +7.5) along with 10 losers. It is a directional rule (constraint 7). |
| **D-7** | Room to an opposing zone (a separate rule) | I-1 not now / I-2 R / I-3 R-b | **I-1 not now** | 2 bot winners (+20.0, +2.1) vs 2 losers (−12.0, −6.4). Kept separate so it can be decided on its own evidence later. |
| **D-8** | Approaching (S3) | D-1 record only / D-2 Watch & Wait | **D-1** | One trade (−6.4). Distance is the room rule's question. |
| **D-9** *(amended, R5)* | STP unavailable | F-1 fail open / F-2 fail closed | **F-1, as a separate state UNKNOWN, never S2** | UNKNOWN is journalled as `structure unknown` with the gate's reason. The dashboard and the daily summary show and count it apart from Neutral. Availability uses the gate's own checks and settings (TS-30). The STP gate stays fail-closed for the three gated strategies, and the gate runs first. F-2 would let an outage stop every strategy. |
| **D-10** | Switch default | `STRUCTURAL_COHERENCE` on if left out / off if left out | **off if left out, on in .env at deployment** | Rollback is one line plus a restart (R-1). The tests' pretend switches stay off. |
| **D-11** | Breakouts into an unresolved zone | E-1 same rule / E-2 accept the 5m break | **E-1** | E-2 would be a new threshold mixing timeframes. Breakouts with no opposing zone (24 Nov +50) are unaffected. |
| **D-12** | Build base and order | H-1 on reviewed Phase 2 / H-2 on fadf228 now | **H-1** | One lineage reader; Phase 2's data-gap semantics (now required by D-14). Do not interfere with the Phase 2 freeze. |
| **D-13** | Emit the rejection candle always (WP-2) | yes / limit S5 to strategies that already emit it | **yes** | Needed for S5 with the gate off. It is a context field; the confirmation is unchanged (TS-19). |
| **D-14** *(amended, R3)* | Unreconciled STP data (Phase 2 PD-5) | still a barrier and never resolved / ignore unreconciled opportunities | **Still a barrier; never resolved on unreconciled or incomplete evidence** (below the table) | Structure does not vanish with a data gap, and it is not declared overcome on incomplete data. This reuses Phase 2's semantics and adds no break interpretation of the SCA's own. |
| **D-15** | Approve implementation WP-0…WP-5 and WP-7 (WP-6 only with D-7) | approve / amend / defer | **Approve after the review of revision 2** | — |
| **D-16** *(new, R4)* | Structural permission versus overall admission | the SCA as a refuse-only layer / anything else | **Refuse-only.** The SCA has no admit or bypass outcome, sits after the STP gate and before the safety rules, and is not in the gate's bypass list. | Phase 2 duplicate protection (PD-2 withholding, lineage keys, rule 11) keeps the last word. 27 Nov 12:01 BUY: SCA S7 permit, refused by Phase 2. 26 Nov 11:40 (+14.0, `#t2`): permit and admitted. Reports keep the two columns apart (§6.5). |
| **D-17** *(new, R1)* | Ended opportunities | ignored as barriers / kept for a fixed period | **Ignored as barriers and never resolving.** The rev 1 24-hour look-back for held breaks is withdrawn; a held break only names S7. | The 24 h was an arbitrary time threshold. Withdrawing it removed a resolution that cleared newer opportunities (D-5 evidence). |

**D-4: the three clarifications.**
1. PAST means at or beyond the opportunity's **own** `zone_break_close`.
2. Each opportunity is judged separately.
3. Ended opportunities are never barriers (D-17).

**D-5: the explicit precedence.**
1. The verdict is Watch & Wait if **any** opportunity is unresolved.
2. S5 resolves only the opposing opportunity whose zone the strategy's own rejection reached, and only when that
   rejection also reached a **directly** overlapping live agreeing opportunity. Edge-only and chained overlap do
   not count.
3. S5 never resolves S4(c) or another opportunity.

**D-14: what counts as unreconciled or incomplete.**
1. No S5, no S6 and no pending break may come from an opportunity with Phase 2 `unreconciled()` reasons, or from a
   `_catch_up` reporting the PD-5 missing-candle reason.
2. Such an opportunity in an S4 position gives S4 *resolution unverifiable*, with Phase 2's reasons in the journal.
3. Endings stand, as in Phase 2.
4. The `_catch_up` adapter is pinned to Phase 2's wording (TS-27).
5. Accepted consequence: until Phase 2 reconciles a gap, or the owner's D-R2 review settles it, such an
   opportunity can hold back trades at or past it. STP's own endings still apply to it meanwhile.

## Outstanding items (recorded, not decided here)

- **O-1.** 12 trade records from 20–27 Nov have no saved IG close evidence (execution-integrity
  history_check). Their figures here are the bot's records. The owner's IG statement, or approved read-only
  checks outside trading hours, would confirm them.
- **O-2.** The three historical corrections (−£23) are still not applied (not authorised). This pack uses IG's
  figures for analysis only and writes nothing.
- **O-3.** No tick data exists for November 2026, so MFE/MAE are 5-minute bounds. If tick-level sequencing is
  wanted for future reviews, IG tick capture would be a separate decision (no concurrent IG session during
  trading).
- **O-4.** Most bot losses (28 of 45) are structurally neutral, e.g. the 23 Nov hourly-bounce BUYs during the
  down-move, or level-reversal wide stops. The SCA does not address them; they are strategy questions.
- **O-5.** The STP gate is off (PD-0). D-1 to D-17 do not depend on re-activating it. If it is re-activated, §3.7
  applies. While the gate is off, Phase 2's STP duplicate protection does not apply to ungated ideas, and the SCA
  does not add one (D-16).
- **O-6.** On the Phase 2 build, how often R3 holds trades back depends on how often live gaps occur. The window
  cannot measure this, because production data carry no gap fields. The first weeks of live demo will show it.
  The journal marks such refusals *unverifiable*, so they can be counted.

## Errata to revision 1 (c7ba045)

| # | Where | Revision 1 | Correct |
|---|---|---|---|
| E-1 | README, 02, 06, 07 FS-09 | 27 Nov 12:01 BUY "a legitimate new test after re-arming (S7)" | It is the duplicate of `0300-56#t1` (Phase 2 L-2); Phase 2 refuses it. The genuine re-armed test is 26 Nov 11:40 (+14.0, `0000-37#t2`). |
| E-2 | 03 §3.3 | ended opportunities with a held break read for 24 h | withdrawn (D-17) |
| E-3 | 03 §3.6, 07 TS-13 | "> 10 min" | the gate's setting `analyser.out_of_date_after_minutes` (value 10 today) |
| E-4 | 06 §6.3, 01, 02, README | 75 deferred ideas (18%), 39 BUY / 36 SELL; Friday 37 of 94; bounce 5m 38 | 82 (19.7%), 46 BUY / 36 SELL; Friday 44 of 94; bounce 5m 41, level reversal 22 |
