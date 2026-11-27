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
   Every other state permits, so STP cannot become a blanket veto. With STP silent, every trade is S2 and
   permitted.
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

For an idea of direction *d* at entry *e* and time *T*, the SCA reads every STP opportunity that is live at *T*
(WAITING, ACTIVE, BROKEN), plus any ended in the last 24 h with STP's "confirmed break held". It groups them by
zone overlap (PD-2 overlap, edge-only contact excluded, as PD-3). For each group:

- **Opposing** members: trade label ≠ *d*. **Agreeing** members: trade label = *d*.
- **Position**, measured in the trade's own direction:
  - AHEAD: the zone is more than NEAR in front of the entry.
  - NEAR_AHEAD: the zone is within NEAR in front.
  - AT: the entry is inside the zone, or within NEAR past its far edge.
  - PAST: the entry is more than NEAR past the far edge.
- **Break**: STP's D-20 status BROKEN, or "confirmed break held", with STP's break direction (zone top = up,
  bottom = down). A pending break still counts: an hourly close ≥ `zone_break_close` that the tracker has not
  processed yet, through `_catch_up`.

| State | Rule (first match wins: S4 > S3 > S5 > S6 > S7 > S1 > S2) | Verdict |
|---|---|---|
| **S1 Aligned** | The entry is AT a live agreeing zone, and no opposing state applies. | permit |
| **S2 Neutral** | No live zone AT, PAST-unresolved or NEAR_AHEAD. Also the state when STP is unavailable (§3.6). | permit |
| **S3 Approaching opposing** | A live opposing zone is NEAR_AHEAD (within 3 pips in front). | permit and record (option S3-WW: Watch & Wait) |
| **S4 Within unresolved opposing** | Any of: (a) AT a live opposing zone with no break in *d*; (b) PAST an opposing zone that STP holds ACTIVE (touched, unresolved) with no D-20 break in *d*, i.e. continuation through a barrier not yet overcome; (c) AT or PAST a zone STP has BROKEN *against* *d* (trading against a confirmed break). | **Watch & Wait** |
| **S5 Confirmed rejection** | An exception to S4(a): a reversal-family idea (bounces, level reversal, session sweep, NY open reversal, range) whose own rejection candle reached the zone, where the zone also carries a live opportunity in *d* (an OD-33 contested zone, where STP recognises both outcomes). The strategy's rejection is the resolving evidence. | permit |
| **S6 Confirmed breakout / breakdown** | AT or PAST an opposing zone whose D-20 break is in *d* (BROKEN). | permit |
| **S7 Continuation after a break** | AT or PAST a zone whose break in *d* STP has held (3 hourly closes, no reclaim), including a retest from the broken side. | permit |

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
- **What releases it.** Only structure, never time. STP's D-20 break in the trade's direction (→ S6). A held
  break (→ S7). The opposing opportunity ending (COMPLETED, INVALIDATED, SUPERSEDED). Price leaving the zone so
  that a later setup is no longer AT/PAST (→ S2/S3/S1). An agreeing opportunity appearing on the zone together
  with a reversal rejection (→ S5).
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
| Data gaps | — | `unreconciled()` | an unreconciled opposing opportunity **still counts as a barrier**. An unreconciled agreeing one **cannot** give S5. Structure does not disappear because data is missing. |
| Break levels | `invalidation.zone_break_close` (overwritten on "changed") | same | read at decision time |
| Strategy rejection | `context.rejection_candle` (emitted only while the gate is on) | same | S5. The build emits it always (WP-2). A context field, not a confirmation change. |

**Order of builds.** The SCA should be built on top of the Phase 2 build once it is reviewed and deployed. It
must read lineage membership as Phase 2 defines it. Building on fadf228 would mean writing the membership logic
twice.

## 3.6 Failure behaviour

STP unavailable, `current` false, `written_utc` > 10 min old, or the file unreadable: **SCA = S2 (unknown) and
permit, journalled as `structure unknown`.** This is option F-1, recommended. The SCA restricts trades; it does
not authorise them. If it failed closed, a planner outage would stop all ten strategies, the blanket veto the
brief rules out. The STP gate keeps its own fail-closed behaviour for the three gated strategies. The decision
is D-9 in the register.

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
