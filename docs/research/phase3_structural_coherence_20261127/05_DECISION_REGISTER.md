# 5. Decision register (awaiting the owner)

Research and design only. Nothing is built. Each decision lists the options (§4), the evidence (§6) and a
recommendation. Implementation waits for approval.

| ID | Decision | Options | Recommendation | Evidence / reason |
|---|---|---|---|---|
| **D-1** | Adopt a common structural coherence assessment (SCA) in `Trading._place`, for all ten strategies | adopt / do not adopt | **Adopt** | 11 bot losers, 0 bot winners in the S4 state (§6.2). Every strategy passes the same point. Reuses STP only. |
| **D-2** | **Partly supersede OD-18 A** ("no new rule against an ungated trade opposite an STP opportunity", approved 24 Nov) | keep OD-18 A / supersede it for S4 only | **Supersede for S4 only** | OD-18 A is why the 25 Nov 18:45/19:10 BUYs opened (coherence review 25 Nov). The SCA still never refuses on an opposing label alone (S1/S2/S5–S7 permit). |
| **D-3** | Source of a zone's role | A-1 STP labels + lifecycle / A-2 price-path inference / A-3 all levels | **A-1** | A-2 was unstable when tested and is a new algorithm. A-3 refuses the +£614 sweep and the +£200 slow grind (Phase 1). |
| **D-4** | Scope of S4 | B-1 AT only / B-2 AT + past-unconfirmed / B-3 + untouched WAITING | **B-2** | B-2 adds 3 bot losers (20 Nov 13:25, 23 Nov 06:45, 25 Nov 18:45) and no winners. Cost: continuations wait for D-20 (27 Nov 13:20–15:00). |
| **D-5** | Contested zones (OD-33) | C-1 reversal-family exemption with own rejection / C-2 none / C-3 all families | **C-1** | Keeps OD-33. C-2 defers all 34 S5 ideas and three trades (26 Nov 06:01 +5.0, 06:30 −7.3, 27 Nov 15:11 owner +9.0). |
| **D-6** | Opposite open positions | G-1 record only / G-2 require a justifying state | **G-1** | G-2 refuses 4 bot winners (+30.0, +20.0, +12.2, +7.5) with 10 losers. It is a directional rule (constraint 7). |
| **D-7** | Room to an opposing zone (separate rule) | I-1 not now / I-2 R / I-3 R-b | **I-1 not now** | 2 bot winners (+20.0, +2.1) vs 2 losers (−12.0, −6.4). Kept separate so it can be decided on its own evidence later. |
| **D-8** | Approaching (S3) | D-1 record only / D-2 Watch & Wait | **D-1** | One trade (−6.4). Distance is the room rule's question. |
| **D-9** | STP unavailable | F-1 fail open to S2 / F-2 fail closed | **F-1** | F-2 lets an outage stop all strategies. The gate keeps its own fail-closed behaviour. |
| **D-10** | Switch default | `STRUCTURAL_COHERENCE` on if left out / off if left out | **off if left out, on in .env at deployment** | Rollback is one line plus a restart (R-1). The tests' pretend switches stay off. |
| **D-11** | Breakouts into an unresolved zone | E-1 same rule / E-2 accept the 5m break | **E-1** | E-2 would be a new threshold mixing timeframes. Breakouts with no opposing zone (24 Nov +50) are unaffected. |
| **D-12** | Build base and order | H-1 on reviewed Phase 2 / H-2 on fadf228 now | **H-1** | Single lineage reader; Phase 2 data-gap semantics. Do not interfere with the Phase 2 freeze. |
| **D-13** | Emit the rejection candle always (WP-2) | yes / limit S5 to strategies that already emit it | **yes** | Needed for S5 with the gate off. It is a context field; the confirmation is unchanged (TS-19). |
| **D-14** | Unreconciled STP data (Phase 2 PD-5) | opposing still a barrier, agreeing no S5 / ignore unreconciled opps | **still a barrier; no S5** | Structure does not vanish with a data gap. Leaves the gate's fail-closed rule alone. |
| **D-15** | Approve implementation WP-0…WP-5, WP-7 (WP-6 only with D-7) | approve / amend / defer | **Approve after an independent review of this pack** | — |

## Outstanding items (recorded, not decided here)

- **O-1.** 12 trade records from 20–27 Nov have no saved IG close evidence (execution-integrity
  history_check). Their figures here are the bot's records. The owner's IG statement, or approved read-only
  checks outside trading hours, would confirm them.
- **O-2.** The three historical corrections (−£23) are still not applied (not authorised). This pack uses IG's
  figures for analysis only and writes nothing.
- **O-3.** No tick data exists for November 2026, so MFE/MAE are 5-minute bounds. If tick-level sequencing is
  wanted for future reviews, IG tick capture would be a separate decision (no concurrent IG session during
  trading).
- **O-4.** Most bot losses (28 of 45) are structurally neutral (e.g. 23 Nov hourly-bounce BUYs during the
  down-move, level-reversal wide stops). The SCA does not address them; they are strategy questions.
- **O-5.** The STP gate is off (PD-0). D-1 to D-14 do not depend on re-activating it. If it is re-activated, §3.7
  applies.
