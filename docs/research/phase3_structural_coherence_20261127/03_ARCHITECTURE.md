# 3. Proposed common structural coherence architecture

Design only. Nothing here is built. "SCA" = the Structural Coherence Assessment.

## 3.1 Principles

1. **One assessment, every strategy, one place.** It sits between strategy confirmation and order execution, in
   `Trading._place`, after the entry filters have passed and before `day_directions` / `OrderSender.place`
   (trading/engine.py, after line 359 at fadf228). Every strategy passes there once per try, on the live and the
   candle-close path, and replays use the same code.
2. **No new forecasting.** The SCA reads STP's published lifecycle (`current.json`: `opportunities[]`, and
   `lineages` on the Phase 2 build), STP's own D-20 break rule (`zone_break_close`, via `stp.authorise._catch_up`
   for what the tracker has not processed yet) and STP's NEAR. It never computes zones, directions or
   destinations.
3. **Structure, not direction.** STP publishes BUY and SELL on the same zone (STP_BIDIRECTIONAL, OD-33). An
   opposing STP *label* alone is never a reason to refuse. A refusal needs the entry to sit at, inside, or
   through an opposing zone that STP still holds unresolved.
4. **Restrict only the unresolved case.** Of the seven states, only S4 (and, as an option, S3) changes anything.
   Every other state permits, so STP cannot become a blanket veto. When STP is current and has no
   opportunities, every trade is S2 and permitted. When STP is unavailable, every trade is UNKNOWN and permitted
   (§3.6). A permit is structural permission only. Admission still needs every other layer (§3.11).
5. **Watch & Wait without delayed entry.** A deferred idea is refused, as today's filters refuse. It is not
   queued, re-sent or timed. A later trade needs the strategy's own fresh setup, assessed afresh. This reuses
   rev 3.2 §9.5: a setup triggered and refused stays refused; a new setup is a fresh confirmation.
6. **Room is separate.** The room-to-level rule (§3.9) is a different module with its own switch and its own
   journal kind. It can be adopted, refused or tuned on its own evidence.
7. **Nothing else changes.** STP methodology, strategy confirmation, stops/TP, trade management, Phase 1
   execution integrity and Phase 2 lifecycle integrity are all untouched. No RSI thresholds, no expiry, no
   timers, no directional veto.

## 3.2 Position in the order path

```
strategy on_candle ──► common.check ──► Trading._place
                                          ├─ STP gate (3 gated strategies, when STP_AUTHORISES_ENTRIES on)  [unchanged]
                                          ├─ entry filters (rules 1, 2b, 3, R3/S3)                          [unchanged]
                                          ├─ ► SCA: structural coherence (STRUCTURAL_COHERENCE)             [new, WP-3]
                                          ├─ ► Room (STRUCTURAL_ROOM), only if adopted                      [new, separate, WP-6]
                                          ├─ day_directions                                                 [unchanged]
                                          └─ OrderSender.place → safety rules → IG                          [unchanged]
```

Why there and not elsewhere (from the inventory): `entry_filters.check` has no open trades and no STP access.
`safety.decide` has no prices and would put structure under "safety". `common.allowed` runs on peek copies
every tick, unjournalled. In `_place` the gate has already bound an STP-authorised idea, so the SCA can see the
binding opportunity and treat a same-zone pair correctly.

## 3.3 States (the seven the brief asks for)

*Revision 2 (review R1–R5, 28 Nov):*
- *each opportunity is judged on its own;*
- *PAST uses the opportunity's own break price;*
- *ended opportunities are never barriers (the rev 1 24-hour look-back is removed);*
- *unreconciled evidence never resolves a conflict;*
- *UNKNOWN is kept separate from S2.*

*Reasoning and evidence: [10_REVIEW_CLARIFICATIONS.md](10_REVIEW_CLARIFICATIONS.md).*

For an idea of direction *d* at entry *e* and time *T*, the SCA reads every STP opportunity that is live at *T*
(WAITING, ACTIVE, BROKEN) and **judges each one separately** (§3.3.1). Ended opportunities (COMPLETED,
INVALIDATED, SUPERSEDED) are never barriers and never resolve one. For each live opportunity *o*:

- **Opposing**: *o*'s trade label ≠ *d*. It can only break in *d*'s direction (a SELL zone breaks up, a BUY zone
  down). **Agreeing**: label = *d*. It can only break against *d*.
- **Position** of the entry against *o*'s own zone, in the trade's own direction:
  - AHEAD: the zone is more than NEAR in front of the entry (STP's `interacts`, NEAR = 3).
  - NEAR_AHEAD: the zone is within NEAR in front.
  - AT: the entry is inside the zone, or past its far edge but short of *o*'s `zone_break_close`.
  - PAST: the entry is at or beyond *o*'s own `invalidation.zone_break_close`, read at decision time. This is the
    price STP's D-20 rule uses, so no distance of the SCA's own is involved (R1).
- **Break**: *o*'s STP status BROKEN, or a pending break that `_catch_up` reports on complete data (§3.10).
  Ended "confirmed break held" opportunities only name S7.

| State | Per-opportunity rule | Verdict |
|---|---|---|
| **S1 Aligned** | AT a live (WAITING/ACTIVE) agreeing opportunity. | permit |
| **S2 Neutral** | STP is available and current, and no opportunity gives any other state. | permit |
| **S3 Approaching opposing** | A live opposing opportunity is NEAR_AHEAD. | permit and record (option D-2: Watch & Wait) |
| **S4 Within unresolved opposing** | (a) AT a live opposing opportunity that this trade's evidence does not resolve. (b) PAST an opposing opportunity STP holds ACTIVE, with no D-20 break: continuation through a barrier not yet overcome. (c) AT or PAST an agreeing opportunity STP holds BROKEN: trading against a live break, within STP's 3-candle window. (d) Any of these where the resolving evidence is unreconciled: *resolution unverifiable* (§3.10). | **Watch & Wait** |
| **S5 Confirmed rejection** | Resolves one opposing opportunity *O* that would give S4(a)/(b). Conditions: a reversal-family idea (bounces, level reversal, session sweep, NY open reversal, range) whose own rejection candle interacts with *O*'s zone; a live agreeing opportunity *A* (WAITING/ACTIVE) whose zone **directly** overlaps *O*'s (PD-2 strict, not edge-only, not via a third zone) and was reached by the same candle (an OD-33 contested pair); neither *O* nor *A* unreconciled. | permit, unless another opportunity gives S4 |
| **S6 Confirmed breakout / breakdown** | AT or PAST an opposing opportunity that STP has BROKEN (its own D-20, in *d*). Resolves that opportunity only. | permit, unless another opportunity gives S4 |
| **S7 Continuation after a break** | Naming only: AT or PAST an *ended* opposing opportunity whose break in *d* STP held, with no later live opportunity on an overlapping zone. It changes no verdict. | permit |
| **UNKNOWN** (not a structural state) | STP unavailable (§3.6). | permit (fail open), shown and counted apart from S2 |

### 3.3.1 Per-opportunity judgement and precedence (R2)

1. Each live opportunity gets its own finding: S1, S3, S4, S5, S6 or none.
2. **The verdict is Watch & Wait if any opportunity's finding is S4.** The reported state is the highest finding
   in S4 > S3 > S5 > S6 > S7 > S1 > S2. Every finding is journalled.
3. **A resolution belongs only to the opportunity it resolves.**
   - S6 resolves only the opportunity STP broke.
   - S5 resolves only the opposing opportunity the rejection reached, paired with a directly overlapping agreeing
     one.
   - Neither clears another opportunity's S4.
4. **S5 never resolves S4(c).** Only STP's failed-breakout rule restores a broken agreeing zone.
5. **Indirect overlap gives no pair.** If A overlaps B and B overlaps O, but A does not overlap O, then A and O
   are not a pair.
6. **The verdict does not depend on the order of the opportunities in `current.json`.**

The real multi-opportunity cases (26 Nov 06:01/06:30 and 11:40–11:55; 27 Nov 01:10–01:50, 15:11 and 15:47) are in
§10 R2 and FS-04/05/13/14. The synthetic overlap cases are FS-15 to FS-21.

### 3.3.2 Why an old ACTIVE zone cannot block continuation further away (R1)

S4(b) requires the entry to be at or beyond *O*'s own break price. STP judges every live opportunity at every
hourly close, with no distance or age limit. At the close of the hour in which S4(b) arises, there are two cases:

- The close is beyond the break price. *O* is BROKEN, and the SCA gives S6 through `_catch_up`, even before the
  tracker runs.
- The close is back inside. STP records a wick sweep, a "closed beyond" or a reclaim: its own evidence that the
  zone was not overcome.

After a break, a failed breakout puts price back at the zone, and a held break ends *O*, which is then never a
barrier. STP's other endings (destination reached, 4-hour structure break, rollover, supersession) also remove it.
S4(c) lasts at most STP's 3-candle break window.

**Evidence, 18–27 Nov:** 35 S4(b) ideas in 14 hour-episodes. Every one was settled at that hour's close: 7 by a
D-20 break and 7 by a close back inside the band. The longest was 1305-58, two hours on 27 Nov 13:00–15:00
(§10 R1). The only residual case is unreconciled data (§3.10).

How the brief's distinctions map to existing STP evidence:

| Brief | Existing evidence |
|---|---|
| Approaching a zone | position NEAR_AHEAD: STP's NEAR, `zones.interacts` within 3 pips; status WAITING |
| Entering a zone | position AT: STP's 5m activation; status ACTIVE (Watch & Wait) |
| Rejecting a zone | the strategy's own rejection setup (`rejection/watch.py` pierce → reversal → confirmation) reaching the zone (S5). STP's hourly "wick sweep" is recorded context. |
| Breaking through a zone | STP D-20: BROKEN (S6). "closed beyond" (< 3 pips) is *not* a break: S4 holds. |
| Successful retest of a broken zone | "confirmed break held" (S7). A "failed breakout" returns the zone to Watch & Wait, so S4 applies again. |

## 3.4 Watch & Wait

- **What happens.** The idea is refused with result `structure: watch and wait`. The journal gets a
  `structure refused` decision (strategy, direction, idea_time, entry_price, state, zone, members, why), then the
  usual `order` record. This copies engine.py:349–357 exactly.
- **No deferred execution.** The idea is consumed. The engine's one-try-per-strategy/direction/candle rule
  already prevents a retry, and a rule-11 key is not consumed because no trade opened.
- **What releases it.** Only structure, never time. Each item applies to the specific opportunity that gave S4
  (§3.3.1):
  - that opportunity's own D-20 break in the trade's direction, on reconciled data (→ S6);
  - that opportunity ending (COMPLETED, INVALIDATED, SUPERSEDED; a held break names S7);
  - price leaving it, so that a later setup is no longer AT or PAST it (→ S2/S3/S1);
  - a directly overlapping agreeing opportunity, together with a reversal rejection that reached both (→ S5).

  Each hour's close settles any S4(b) (§3.3.2). Phase 2 reconciling a gap lets normal judgement resume (§3.10).
- **Fresh confirmation.** A trade is permitted only on a *new* idea of the strategy: a new setup with its own
  trigger, assessed afresh at its own time. Observed releases: 25 Nov 12:25 sweep deferred → fresh 15:05 sweep
  (+61.4). 26 Nov 12:51 bounce SELL (S3) → fresh 14:22 SELL (S1). 27 Nov 15:47 slow grind (S4) → fresh 16:05
  slow grind (S6). 23 Nov 06:00 level reversal (S4) → fresh 10:42 (S2).

## 3.5 Inputs and the Phase 2 dependency

| Input | Production (fadf228) | Phase 2 build (9e0ffd5) | SCA use |
|---|---|---|---|
| Opportunities | `current.json opportunities[]` | same | the zone groups. Use `opportunities[]`, never `recommendation` (newest vs oldest, L-6). |
| Lineage | not present | `lineages{}`: members' `effective_status`, `destination_case` | membership. A member COMPLETED `after_trade` is ended. |
| Pending break | `_catch_up` hourly close ≥ `zone_break_close` since `validated_h1_end` | same, plus missing-5m refusals | S6 before the tracker runs; avoids a race at :00 |
| Data gaps | — | `unreconciled()`; `_catch_up`'s PD-5 missing-candle reason | an unreconciled opportunity **still counts as a barrier** and **cannot be resolved** (no S5, no S6, no pending break). An unreconciled agreeing one cannot give S5. Structure does not disappear because data is missing, and it is not declared overcome on incomplete data (§3.10). |
| Break levels | `invalidation.zone_break_close` (overwritten on "changed") | same | read at decision time |
| Strategy rejection | `context.rejection_candle` (emitted only while the gate is on) | same | S5. The build emits it always (WP-2). A context field, not a confirmation change. |

**Order of builds.** The SCA should be built on top of the Phase 2 build once it is reviewed and deployed. It
must read lineage membership as Phase 2 defines it. Building on fadf228 would mean writing the membership logic
twice.

## 3.6 Failure behaviour

**When STP is unavailable**, the SCA gives the state **UNKNOWN**, not S2, and permits (option F-1, retained).
"Unavailable" means the same checks as the gate's `authorise()` steps 1–2, with the same settings:
- the file is missing or unreadable;
- `written_utc` is older than `analyser.out_of_date_after_minutes` (rev 1's "10 min" is this setting, not a new
  number);
- `current` is not True;
- the live price or the latest 5m candle is older than that limit.

An equivalence test pins the SCA's checks to the gate's refusals (TS-30). This avoids changing Phase 2's
`stp/authorise.py` to share a helper.

| | S2 neutral | UNKNOWN |
|---|---|---|
| Meaning | STP is current; its lifecycle shows nothing in a conflicting position | there is no STP verdict to read |
| Verdict | permit | permit (fail open) |
| Journal | `idea.steps` "structure: neutral" | decision `structure unknown` with the reason in the gate's words; `idea.steps` "structure: unknown (STP unavailable: …), permitted" |
| Dashboard and daily summary | "Neutral" | "Structure unknown", shown distinctly; counted separately; never folded into S2 in any figure |

**Why fail open, and why the gate stays fail-closed.**
- The SCA only restricts; it never authorises. If it failed closed, a planner outage would stop all ten
  strategies, the blanket veto the brief rules out.
- **The STP gate keeps its fail-closed behaviour unchanged.** With the gate on and STP unavailable, the three gated
  strategies are refused at the gate, with the same journal text as today, before the SCA runs. Only the ungated
  strategies reach the SCA, where they get UNKNOWN and are permitted (TS-29).
- An UNKNOWN permit can never let a gated idea past the gate.

A per-opportunity data gap, while STP is otherwise current, is a different case. It is R3 (§3.10), not R5. These
decisions are D-9 and D-14 in the register.

## 3.7 Interaction with the STP gate (when re-activated)

The gate checks the agreeing side ("is there a live same-direction zone this rejection reached?"). The SCA
checks the opposing side ("is the entry inside or through an unresolved opposing zone?"). For an STP-authorised
idea at an OD-33 contested zone, S5 applies, so the SCA does not undo OD-33. For an STP-authorised idea whose
entry sits in a *different* opposing zone (Phase 1 C-b), S4 applies. The gate's bypass list does **not** include
the SCA: it is not a filter the gate replaces.

## 3.8 Opposite positions

Every SCA record carries `opposite_open` (the bot's open positions in the other direction). No rule acts on it
in the recommended design (D-6 option O-1). Its evidence is mixed: 4 winners and 10 losers among neutral
opposite entries. A refusal on direction alone would be a directional veto (constraint 7). Opposite entries
with a structural conflict are already caught by S4 (e.g. 26 Nov 11:45 and 11:55).

## 3.9 Room-to-level rule (separate, for independent evaluation)

- **Rule R (the ROOM_TO_LEVEL principle the owner approved on 19 Nov for breakouts, applied to STP zones).** Room
  = pips from the idea entry to the near edge of the nearest live opposing STP zone (WAITING/ACTIVE) AHEAD or
  NEAR_AHEAD. Refuse when room < the trade's actual stop distance. R-b ignores an opposing zone that overlaps a
  live agreeing zone (contested pair).
- **Independence from the SCA.** R looks only at zones *ahead*. The SCA restricts only AT/PAST (and optionally
  NEAR_AHEAD). In the window they never refused the same trade.
- **Evidence.** R refuses 4 bot trades. 2 winners: 23 Nov 01:47 slow grind +20.0, 26 Nov 14:22 bounce 5m +2.1.
  2 losers: 25 Nov 11:00 EMA pullback −12.0, 26 Nov 12:51 bounce 5m −6.4. R-b refuses 3: +20.0, +2.1, −12.0.
- **Assessment.** The evidence does not support adopting R now (D-7). The ROOM_TO_LEVEL branch (pivot levels,
  breakouts only) is a separate, already-approved item that is still not merged. Phase 1 showed that the wider
  pivot, own-primary or candidate-zone room variants refuse the +£200 and +£614 winners.

## 3.10 Unreconciled structural evidence (R3)

The SCA reuses Phase 2's data-integrity semantics unchanged. It has no interpretation of breaks of its own.

1. **Nothing is recomputed.** Lifecycle, status and breaks come from STP's `current.json` (opportunities and
   lineages). For what the tracker has not processed yet, the SCA calls `stp.authorise._catch_up` and
   `stp.authorise.unreconciled` exactly as the gate does. It reads no hourly candle itself.
2. **A resolution needs reconciled evidence.** An opposing opportunity is resolved (S6 from BROKEN, S6 from a
   pending break, or S5) only when:
   - `unreconciled(state, o)` is empty, and for S5 it is also empty for the agreeing member;
   - for a pending break, `_catch_up` reports the zone break and does **not** report the PD-5 "IG's 5-minute
     candle … is not stored yet" reason.
3. **Otherwise the conflict stays unresolved.** If the entry is AT or PAST the opportunity, the state is S4(d),
   *resolution unverifiable*, and Phase 2's reasons go word for word into the journal.
4. **A gap is not an ending.** An opportunity with an open gap is still live, so it is still a barrier when the
   entry is AT or PAST it. If it is AHEAD, it has no effect beyond S3 recording.
5. **Endings stand, as in Phase 2.** Phase 2 never reopens an ended opportunity (`_reconcile_ended` only corrects
   a classification). The SCA neither reopens an ended opportunity nor reads it as a barrier.
6. **The adapter is pinned.** `_catch_up` returns text reasons. WP-1 reads the zone-break and PD-5 lines through
   an adapter that a test pins to Phase 2's exact wording (TS-27). Tagged reasons would mean changing Phase 2 code,
   so they are not proposed.
7. **Real case.** On the Phase 2 build before OP-1, the 27 Nov 15:11 bounce SELL is S4(d). Its agreeing pair
   member 1500-59 has the uncertain 12:00 hour in its lineage, so it gives no S5. Phase 2 refuses the same idea
   under D-R2 (§10 R3).
8. **Bound.** While a gap is unreconciled, STP's own endings still run on the opportunity. A gap Phase 2 leaves
   "for review" holds until the owner's D-R2 procedure (`planner/review.py`).

## 3.11 Structural permission versus trade admission (R4)

- **Admission is every layer of `_place` in order:** STP gate → entry filters → **SCA** → (room) →
  day_directions → OrderSender → safety rules (incl. rule 11) → IG.
- **The SCA can only refuse or continue.** It has no "admit" or "bypass" outcome and is not in the gate's bypass
  list. A structural *permit* is necessary for admission but never sufficient.
- **Duplicate protection is untouched and has the last word.**
  - A gate refusal (Phase 2 PD-2: no live opportunity) returns before the SCA runs.
  - A rule-11 refusal (Phase 2 lineage keys and aliases) comes after it.
  - Either way, the SCA cannot re-admit the idea.
  - **27 Nov 12:01 BUY:** SCA S7 permit, Phase 2 refuses, overall refused (§10 R4, FS-09).
  - **26 Nov 11:40 BUY (+14.0, a genuine re-armed test, `0000-37#t2`):** SCA S6 permit, Phase 2 admits, overall
    admitted (FS-12).
- **The journal and reports keep the two apart.** The `idea.steps` structure line records the SCA's state and
  verdict. `order.result` records the overall admission, naming the layer that refused.
- **The historical impact (§6) reports both columns.**
