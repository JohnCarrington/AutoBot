# Structural Trade Planner: strategy integration (consolidated design, revision 2)

**Status:** DESIGN FOR FINAL REVIEW. Nothing here is implemented, deployed or switched on. STP stays observe-only.

| | |
|---|---|
| **Revision** | 2, 24 November 2026. Incorporates the owner's decisions on OD-01 to OD-15 and the mandatory clarifications: both directions, reversal and continuation, monitoring frequency. Revision 1: c373280. |
| **Code examined** | `/opt/autobot` at 63d9c04, the live build |
| **Approved STP spec examined** | `/home/autobot/research/structural_trade_planner_v1/`: ARCHITECTURE_AND_DESIGN, DECISION_REGISTER (D-01 to D-38), PARAMETER_APPROVAL_REGISTER, IMPLEMENTATION_READINESS (FC-01 to FC-13) |
| **Requirements** | H01 to H23, approved |
| **Fixtures** | `stp_strategy_integration_20261124/`: the 24 Nov 5-minute R1-window candles, and a rejection-watcher replay from 00:00 to 18:30 (a code replay, not a live record) |

**Contents**
1. Executive summary
2. Current architecture: verified facts
3. Revised architecture
4. Consolidated decision register
5. Opportunity lifecycle and state-transition model
6. Revised strategy integration matrix
7. Bidirectional opportunity authorisation contract
8. Reversal and continuation monitoring design
9. Technical test specification
10. Functional test specification (24 November, extended)
11. Traceability (H01 to H23, OD-01 to OD-21)
12. Implementation work packages and dependencies
13. Deployment and rollback plan
14. Amendments required to D-01 to D-38
15. Remaining gaps and unresolved decisions

---

## 1. Executive summary

**Where the work sits (no new service):**

| Job | Where it runs | When |
|---|---|---|
| Structural forecasting | The planner subprocess, unchanged | Re-plans at each completed hourly candle |
| Opportunity lifecycle and Watch & Wait | A new **opportunity monitor** module inside the existing price-service process, alongside the levels and analyser updaters | Every completed 5-minute candle and every incoming price |
| Authorisation | One check in the single order funnel, `Trading._place` | Every entry |
| Entry confirmation | Strategies, unchanged | Their own timeframes, tick level where they are now |
| Execution and trade management | Unchanged | – |

**What changes in STP:**
- STP becomes bidirectional (OD-06 revised).
  - For each direction, it proposes opportunities from its existing, approved zone map: the same zone grading, reachability, destinations and invalidation.
  - The H4 direction becomes recorded context instead of a gate.
  - The forecasting method is otherwise unchanged.
- Every opportunity carries an STP-specified **continuation hypothesis** (OD-08 modified C).
  - It activates only on STP's own confirmed-break rule (D-20).
  - It is never activated by a failed rejection, so the bot never invents an opposite-direction authorisation.
- The existing dual conditional-scenario forecaster (`planner/technical.py`) **cannot** serve as the authorisation source (§8.1).
  - During today's 08:30 to 18:00 bullish correction it never proposed a BUY with enough evidence.
  - Its only BUY candidates were counter-trend failed breakouts scoring 2, against a minimum of 4.
  - It has no identity, no lifecycle and no primary destination. It has an 8-hour validity setting, which would be a time expiry.
  - It stays observe-only and is shown as context.

**Gating and duplicates:**
- Gated strategies: the hourly Bollinger bounce, the 5-minute Bollinger bounce and Level Reversal, in both directions (OD-03).
- For these three, STP replaces the analyser-state gating, rule 1, rule 3 and safety rule 9 (OD-05).
- Kept for them: entry confirmation, hours, news, risk, limits, rules 10 and 11, and, subject to the explicit confirmation in §4.2, the RSI stretch and Level Reversal's own level set.
- Duplicate entries are stopped by reusing safety rule 11, with the signal key "opportunity id + distinct test number" (OD-09).

**No new numbers:**
- No new numerical parameter, no indicator and no time-based expiry.
- Every rule reuses an approved value:

  | Value | Approved where |
  |---|---|
  | `near_level_within_pips` 3 | D-06 |
  | `break_beyond_pips` 3 | D-20 |
  | `failed_breakout_within_candles` 3 | P-F7 |
  | the watcher's 3-candle steps | existing watcher settings |
  | `out_of_date_after_minutes` 10 | D-21 b |

- The revision-1 lag number (`register_lag_candles`) and the STALLING count are withdrawn.

**What today's data shows (verified):**
- STP's records ended the R1 SELL opportunity (1.31030–1.31141) at 15:00 while it was still structurally valid.
- Price then tested R1 repeatedly.
- The 17:00 hourly candle closed 1.31204, a confirmed break, at 18:00.
- Price entered STP's 17:00 SELL zone at the weekly pivot (1.31176–1.31286).

Under this design:
- The R1 opportunity stays in WATCH AND WAIT until 18:00, then moves to BREAK_PENDING.
- The 17:00 zone is monitored at the same time.
- The 18:20 5-minute bounce sell from that zone would be **authorised by STP**, but it would still be refused by the retained RSI stretch.
- The 18:00 5-minute bounce buy on the R1 retest would be refused because STP had no valid BUY authorisation there. Today the analyser state refused it.

  The continuation's destination is inside a Major resistance zone that price has already reached. This is expected from the rules; test FT-07 confirms it from the zone map as it stood at that time.
- So a credible location alone never trades.

---

## 2. Current architecture: verified facts (63d9c04)

### 2.1 Process and timing
- **Per 5-minute candle,** the price service's `after_new_candle` runs in this order (`prices/service.py:262-273`):
  1. levels;
  2. analyser states;
  3. `engine.on_candle` (the trade manager and candle-close entries);
  4. the planner, launched as a detached `nice` subprocess (`planner/keeper.py:504-529`).
- **Per tick,** `engine.on_price` runs (`service.py:167`). Live entries go through `runner.peek` and then `_place` (`engine.py:504-526`).
- **Today the planner lags the engine by at least one candle.** Its 5-minute lifecycle checks use completed candles only. No finer prices are stored, per the keeper's own `event_time_basis`.
- **No trading code reads STP.** `PLANNER_AUTHORISES_BOUNCE` was never built.

### 2.2 STP output and lifecycle
- **Files** in `data/planner/GBPUSD/`:
  - `current.json`, `recommendations.jsonl`, `issued.jsonl`;
  - `technical.json(l)` for the dual forecaster.
- **One live recommendation per pair** (D-23 A).
- **Statuses:** CANDIDATE → WAITING → ACTIVE → INVALIDATED, SUPERSEDED or COMPLETED.
- **Identity:** the trade plus its fixed levels.
- **Recommendations are made only in the H4 direction** (`assess.py:376-383`), and only for the four approved condition classes (`:391-393`).
- **A re-plan supersedes on a different zone** (`keeper.py:371-378`) and invalidates on "no longer recommended" (`:397-398`).

### 2.3 Watch & Wait capability today
These pieces exist but are not joined up:
- the keeper's touch, break, sweep, reclaim and failed-breakout records (hourly, recorded only);
- `zones.count_tests` (D-25, recorded only);
- the shared rejection watcher (5-minute, single-price levels; nothing records its events);
- the dual forecaster's per-direction scenarios (hourly snapshot, no memory);
- the analyser's CONSOLIDATION "watch and wait" label, a market-wide state, not per-zone.

On AutoBot 161, NMS was an in-process library ensemble, not a service. This codebase's equivalent is `analyser/`.

### 2.4 Strategies, filters and duplicates
These are unchanged from revision 1 §2.3 to §2.5 and are summarised in §6.

Facts that matter for this design:
- Level Reversal, the 5-minute bounce and the range trade carry no rule-11 signal key. The first two share the same watcher setups, so both can open on one rejection.
- Rule 11 counts every trade opened (open or closed) and every order sent but not yet settled (`orders/sender.py:452-457`).

---

## 3. Revised architecture

### 3.1 Components

```
price service process (existing)
 ├─ on every tick ──────────► OPPORTUNITY MONITOR.on_price  (new module; zone interaction, destination reached, overshoot extreme)
 │                           then engine.on_price → live entries → _place
 ├─ after each 5m candle:
 │    levels → analyser → OPPORTUNITY MONITOR.on_candle (M5 lifecycle; zone-aware rejection attempts;
 │                         at H1 close: each opportunity's own H1 conditions)
 │          → engine.on_candle → _place
 │          → planner subprocess (hourly re-plan at H1 close; unchanged cadence, D-36 A)
 │                 writes PROPOSALS (both directions, each with its continuation hypothesis)
 │                 ── picked up by the monitor on its next step (candle or tick)
 └─ the monitor is the ONLY writer of data/planner/GBPUSD/opportunities.json (+ opportunity_events.jsonl)

Trading._place(idea): entry filters (existing; OD-05 bypass list for the gated strategies)
                      → STP AUTHORISATION (gated strategies only) → day directions → OrderSender.place
                      → safety.decide (rule 11 with the opportunity signal key) → IG DEMO
trade manager: unchanged; never reads STP
dashboard: reads opportunities.json (read only)
```

### 3.2 Why this shape (OD-12 modified B, H23)

- **Monitoring frequency** (the owner's table):

  | Item | Where | Frequency |
  |---|---|---|
  | Structural forecasting | planner subprocess | hourly |
  | Opportunity lifecycle | monitor `on_candle` | M5, plus live events from `on_price` |
  | Zone interaction | monitor `on_price` | every incoming price |
  | Candle-based rejection assessment | the zone-aware watcher in the monitor (M5); each strategy's own watcher | strategy-specific completed candles |
  | Live entry triggers | strategies (`peek`) | tick, where applicable |
  | Continuation assessment | monitor | M5 and live price; activation at the H1 close per D-20 |
  | Structural invalidation | monitor | on each opportunity's own stated conditions: H1 close, H4 close, destination |
  | Trade management | unchanged | – |

- **No new service:**
  - The monitor is a module in the price service, like `LevelsUpdater` and `StatesUpdater`.
  - It is wrapped in the same "never stop the price service" protection. If it fails, the register is marked not current and authorisation is refused.
- **One writer:**
  - The planner proposes; the monitor owns the lifecycle.
  - The keeper's existing 5-minute and hourly checks (`keeper.five_minute`, `keeper.hourly`, `zones.interacts`, `wholly_clear`, `count_tests`) are refactored into pure functions that the monitor calls. This is reuse, not a second copy.
  - The keeper's own lifecycle is retired when the monitor's switch is on, which avoids two contradictory lifecycles.
- **No lag:** the lifecycle is up to date before the engine acts on a candle or a tick. Only a *new* hourly proposal arrives seconds after the hourly close, which is acceptable because forecasting is hourly by definition.
- **No leakage:**
  - STP zones are never fed into the analyser's watcher or level list. Doing so would change analyser states and the trade manager's close on rejection.
  - The monitor uses its own zone-aware watcher instance (§8.3).
- **Price basis:** zones and monitoring use the sell (bid) price (D-32). Ticks carry bid and offer, and the monitor reads the bid.

---

## 4. Consolidated decision register

### 4.1 Owner decisions

| OD | Decision | Status |
|---|---|---|
| OD-01 | Several structurally valid opportunities may coexist. | Approved (A) |
| OD-02 | A new forecast does not end a valid opportunity; it ends only on its own conditions. | Approved (A); **confirm the H10/H11 reading** (§4.2) |
| OD-03 | STP authorises the hourly bounce, the 5-minute bounce and Level Reversal, in BUY and SELL. | **Explicitly approved** (modified C) |
| OD-04 | Both healthy-pullback and corrective-reversal opportunities authorise. | Approved |
| OD-05 | For the gated strategies, STP replaces the conflicting structural and directional filters. Entry confirmation, execution safety and risk are kept. | Approved (A); **confirm the filter list** (§4.2) |
| OD-06 | The H4 direction is context, not a restriction. | **Explicitly approved** (revised) |
| OD-07 | A failed breakout returns to Watch & Wait while the opportunity is otherwise valid. | Approved (A); **confirm the new use of P-F7** (§4.2) |
| OD-08 | Reversal and continuation at significant structural levels. | **Explicitly approved** (modified C) |
| OD-09 | One trade per distinct test; duplicate prevention. | Approved (A) |
| OD-10 | Record tests and failed rejections; no thresholds. | Approved (A) |
| OD-11 | Keep the name Watch & Wait. | Approved |
| OD-12 | Hourly forecasting, live monitoring, strategy confirmation. | **Explicitly approved** (modified B) |
| OD-13 | Re-validate at the weekly open; no expiry. | Approved (A) |
| OD-14 | Record structural monitoring events. | Approved (A) |
| OD-15 | Inert switches go to a separate investigation; nothing restored or removed here. | Approved |

### 4.2 Points needing further explicit owner approval

**OD-02: precedence of H11 over one approved invalidation trigger.**
- H10 says "invalidation follows STP's conditions". ARCH §10.2 lists "supporting evidence materially changes on re-plan" as one of those conditions.
- This design treats H11 as overriding that one trigger. An opportunity is not invalidated because a re-plan's evidence changed; it is invalidated only by its own stated conditions.
- **Please confirm.**

**OD-05: exactly which filters are bypassed.**
- Bypassed for the three gated strategies only:
  - analyser-state gating (`ALLOWED_IN`; affects the 5-minute bounce and Level Reversal);
  - rule 1 `HOURLY_CONTEXT`;
  - rule 3 `COUNTER_TREND_TIRING` and its variants;
  - safety rule 9 "one view" (affects Level Reversal).
- Kept as non-structural, **pending your confirmation:**
  - **RSI stretch (rule 2b).** It is a momentum filter, not a structural one. Today it refused the 18:20 sell from the weekly-pivot zone, which STP would have authorised.
  - **Level Reversal's own level set and allowances** (S2, R2, 00; 12/12/5 pips). These are treated as Level Reversal's *entry confirmation*. With them kept, Level Reversal trades only where one of its levels lies inside an STP zone.
- Not affected: the direction rule (EMA pullback only), trading hours, news, the 20:30 close, the risk and position limits, and rules 10 and 11.

**OD-07: P-F7 for authorisation.**
- P-F7 (3 hourly candles) was approved "recorded only".
- Here it decides two things:
  - whether a broken opportunity returns to Watch & Wait (reversal re-authorised);
  - when a continuation hypothesis lapses back.
- That is a new job for an approved number. **Please confirm** that P-F7 = 3 applies.

**OD-01: reverses D-23 A.**
- This is recorded in §14. No further question unless you want a cap on the number of opportunities. A cap would be a new number, so none is proposed.

### 4.3 New decisions arising in revision 2

| OD | Question | Options | Recommended |
|---|---|---|---|
| OD-16 | What makes a counter-H4 opportunity credible | A. the same approved criteria as with-H4: zone class at least Moderate (D-16), NEAR or PLAUSIBLE reachability (D-14), a Major zone for the primary destination (D-18), destination not already reached (D-1); H4 direction recorded as context. B. A plus the dual forecaster's evidence score (`min_evidence` 4 and its point weights, which include a −1 countertrend penalty; I found no approval record for these numbers). C. A plus new criteria | **A.** No new numbers. The 20 Nov historical validation found no measurable edge in STP's direction rule (51.6%), which supports treating H4 as context. B would have rejected every BUY today. |
| OD-17 | How many new proposals per direction per re-plan | A. one per direction: D-16's choice (strongest class, then nearest) applied on each side. B. every qualifying zone | **A.** Existing opportunities are kept anyway (OD-01/OD-02), so several build up naturally. |
| OD-18 | Conflicting exposure between STP-authorised trades and ungated strategies (slow grind, breakout, Asian range breakout, EMA pullback, range trade, session strategies) | A. no new rule; the existing per-strategy limits, total cap and rule 9 (for those it covers) stay. B. refuse an ungated entry against a live STP opportunity at the same zone (revision 1's OD-08 B; not approved) | **A** for this build. Report the conflicts in the dashboard and the daily summary. B is open for later. |
| OD-19 | When a continuation's destinations are worked out | A. at activation: STP's re-plan at the hourly close that confirms the break, from the zone map as it stands then. B. at issue | **A.** The map above a zone changes during the day: today the 1.31176–1.31286 zone only formed during the afternoon. |
| OD-20 | Proposed switch names and defaults (§13.3) | as listed | as listed |
| OD-21 | A BUY proposal and a continuation BUY on the same zone (same fixed levels) | A. one opportunity, one identity (merged). B. two | **A.** This stops one zone producing two bindings. |

---

## 5. Opportunity lifecycle and state-transition model

### 5.1 Two layers, two hypotheses
- **Status** is structural validity, and it alone governs authorisation.
- **Phase** is the Watch & Wait reading. It is recorded and never authorises a trade on its own (H05, H21).
- **Each opportunity has two hypotheses** at one zone:
  - **REVERSAL** in its own direction;
  - **CONTINUATION** in the opposite direction, which starts DORMANT.

### 5.2 Statuses

| Status | Meaning | Authorises |
|---|---|---|
| WAITING | Issued; no interaction yet | The reversal direction, if the strategy's rejection candle interacts (D-29 A, 3 pips: H08) |
| WATCH_AND_WAIT | The zone has been interacted with; unresolved | Same as WAITING |
| BREAK_PENDING | A D-20 confirmed break; inside the P-F7 window | The **continuation** direction only, if the continuation is ACTIVE (§8.4) |
| CONTINUATION | The P-F7 window passed with no reclaim; the reversal has ended | The continuation direction only, if ACTIVE |
| COMPLETED | The destination of the authorised hypothesis was reached after interaction | Nothing |
| CANCELLED_DESTINATION_FIRST | The primary destination was reached before interaction or entry (H12) | Nothing |
| INVALIDATED | The opportunity's own conditions failed: an H4 structure-break close against it; the continuation's own invalidation after the reversal has ended; its fixed levels gone without a successor | Nothing |
| SUPERSEDED | The same identity was reissued with changed structure (D-22, narrowed) | Nothing; the successor takes over with its history |

**Every authorisation also needs** the register to be current and the prices fresh (`out_of_date_after_minutes`, D-21 b).

### 5.3 Transitions

| From | Trigger | Checked | To | Source |
|---|---|---|---|---|
| (new) | A proposal with an identity that is not already live | at the hourly re-plan | WAITING (continuation DORMANT) | D-21, OD-16, OD-17 |
| (new) | A proposal with a live identity, structure changed | at the hourly re-plan | the old one SUPERSEDED, the new one inherits its counters | D-22 |
| (new) | A proposal with a live identity, zone edges moved by non-fixed levels | at the hourly re-plan | updated in place ("changed") | existing, FC-05 |
| WAITING | The price comes within 3 pips of the zone | tick / M5 | WATCH_AND_WAIT | `interacts`, H08 |
| WAITING | The primary destination is reached first | tick / M5 | CANCELLED_DESTINATION_FIRST | D-1, H12 |
| WATCH_AND_WAIT | An hourly close at least 3 pips beyond the far edge | H1 close | BREAK_PENDING; continuation → ACTIVE if STP's re-plan gives it valid destinations (§8.4) | D-20, OD-08, OD-19 |
| WATCH_AND_WAIT | The reversal's primary destination is reached after interaction | tick / M5 | COMPLETED | keeper |
| BREAK_PENDING | An hourly close back inside the zone within P-F7 (3) candles | H1 close | WATCH_AND_WAIT; continuation → ENDED | D-24, OD-07 |
| BREAK_PENDING | P-F7 candles pass with no reclaim | H1 close | CONTINUATION (reversal ended) | D-20 |
| BREAK_PENDING / CONTINUATION | The continuation's destination reached before entry | tick / M5 | continuation → ENDED (destination first); status → INVALIDATED if the reversal has already ended | H12 |
| CONTINUATION | An hourly close back inside the zone by at least 3 pips | H1 close | INVALIDATED | D-20, mirrored |
| any live status | An H4 close beyond the structure-break price, against the live hypothesis | H4 close | INVALIDATED | ARCH §10.2 |
| any live status | The fixed levels disappear at the 00:00 pivot rollover with no successor | 00:00 re-plan | INVALIDATED ("structural levels changed") | D-21 |
| any live status | **The re-plan chooses another zone, recommends nothing, or the H4 direction or condition changes** | – | **no change** (recorded as context) | H11, OD-02, OD-06 |
| any live status | **Time passes; a session ends; the week ends** | – | **no change**; re-validated at the weekly open | H16, D-21, OD-13 |

### 5.4 Phases (recorded; existing definitions only)

| Phase / event | Definition | Status effect |
|---|---|---|
| APPROACHING | Price within 3 pips of the near edge (tick) | Starts WATCH_AND_WAIT on the first interaction |
| IN_ZONE | Price inside the zone (tick); a 5-minute close inside (M5) | none |
| OVERSHOOT | Price beyond the far edge (tick, deepest point kept); an hourly close beyond by less than 3 pips | none (H09); a temporary penetration never activates the continuation |
| REJECTION_ATTEMPT n | Zone-aware watcher steps (§8.3) | none |
| REJECTION_FAILED n | The attempt was CANCELLED or EXPIRED (watcher step counts) | **none**: stays WATCH_AND_WAIT (H19); never activates the continuation |
| REJECTION_TRIGGERED n | The attempt reached its trigger | none (strategies confirm on their own) |
| TEST n | A distinct test (D-25 A, `count_tests`) | none; the signal key becomes `#t(n)` |
| RECLAIM | An hourly close back on the entry side after an overshoot | none |
| LEFT_ZONE | `wholly_clear` | none (no demotion) |
| BREAK_CONFIRMED / FAILED_BREAKOUT / CONTINUATION_CONFIRMED | §5.3 | as §5.3 |

Tests and failed attempts are **counted and shown** (repeated testing, stalling). No threshold is applied (OD-10).

### 5.5 Diagram

```
                          proposal (hourly, either direction)
                                      │
                                   WAITING ───────── primary destination first ──► CANCELLED_DESTINATION_FIRST
                                      │ price within 3 pips (tick/M5)
                                      ▼
     ┌─────────────────────────► WATCH_AND_WAIT ◄── failed rejection / test / overshoot / reclaim / left zone
     │ H1 close back inside       │   [REVERSAL authorised]            (recorded loop)
     │ within P-F7 (failed        │──── reversal destination reached ──► COMPLETED
     │ breakout; continuation     │ H1 close ≥ 3 pips beyond far edge (D-20)
     │ ENDED)                     ▼
     └────────────────────── BREAK_PENDING  [continuation ACTIVE only if STP gave it valid destinations]
                                  │ P-F7 hourly closes, no reclaim
                                  ▼
                              CONTINUATION [continuation authorised] ── its destination reached ──► COMPLETED
                                  │ H1 close back inside ≥ 3 pips / continuation destination first
                                  ▼
                              INVALIDATED
   any live status: H4 structure break against the live hypothesis, or fixed levels gone ──► INVALIDATED
   same identity reissued with changed structure ──► SUPERSEDED
   another zone chosen · no recommendation · H4 change · time · session · weekend ──► no change
```

---

## 6. Revised strategy integration matrix

The names do not describe the behaviour. "Reversal" in this code means **a rejection at a level or band, in either direction**. It does not mean "against the trend".

| Strategy | What the code actually does | In practice | STP after integration |
|---|---|---|---|
| **Bollinger bounce (hourly)** | A 5m high more than 3 pips beyond the *hourly* Bollinger band, the same candle closes back, then a confirmation close within 3 candles; opens at the next candle. Not checked against the analyser state. | Fades the move that pierced the band, either way. | **Gated, BUY and SELL.** The rejection candle must interact with a live zone that authorises that direction. |
| **Bollinger bounce 5m** | Watcher bounce: pierce a level or the 5m band, opposite-coloured candle, confirmation close, live trigger. Today limited to TREND (against it) and POSSIBLE REVERSAL. | Counter-trend or either way, depending on the analyser state. | **Gated, BUY and SELL.** The analyser-state gating is removed (OD-05). |
| **Level Reversal** | The same watcher setups as the 5m bounce, kept only at S2, R2 or 00 (12/12/5-pip allowances, up to 3 pips short); stop 6 pips beyond the furthest point; take profit 20. All states except CONSOLIDATION; rule 9 applies. | **Either way, from either side of a level.** Today: 13:32 SELL at 1.31000 from below, a counter-trend fade (stopped, −16.6). 15:30 BUY at 1.31000 from above, in an "emerging trend up" — a with-trend dip-buy, in effect a continuation entry, opened at 1.31142 at the top of STP's SELL zone. | **Gated, BUY and SELL.** State gating and rule 9 are removed. Its level set is kept as confirmation (subject to the §4.2 confirmation). Its with-trend retests become authorised **only** through an active STP continuation, or an STP opportunity in that direction. |
| Range trade | Watcher range version: 5m band pierce, the next candle the opposite colour, a break within 1 candle; RANGING only. | Mean reversion both ways. | Not gated (OD-03). |
| Session sweep | 3 or more pips past the Asian or London high or low, a close back inside, then confirmation. | False-break reversal, either way. | Not gated. |
| New York open reversal | A 30-pip or larger move from 07:00 to 13:30, then a rejection between 13:30 and 15:00. | Against the day's move. | Not gated. |
| Slow grind | Pause and break on the trend side of the 21 EMA. | Continuation. | Not gated (OD-18 A). |
| EMA pullback | Hourly EMA stack, a 5m 8 EMA touch, entry 3 pips beyond the last 5 candles; the direction rule. | Continuation. | **Independent** (H15). |
| Breakout | When the analyser reports a breakout from a range or consolidation, a pullback entry. | Continuation. | Not gated. |
| Asian range breakout | The first close outside the Asian range from 07:00 to 10:00, then a pullback entry. | Continuation. | Not gated. |

**Consequence for the gated three:**
- Their direction now comes from STP's live opportunities, either way.
- A gated idea with no matching opportunity is refused, whatever its name suggests.
- Today's Level Reversal 15:30 BUY would have needed a live BUY authorisation whose zone its rejection candle (low 1.31023) reached. Whether one existed at 15:30 depends on the bidirectional proposals from the zone map as it stood then. Test FT-05 computes this; it is not asserted here.

---

## 7. Bidirectional opportunity authorisation contract

### 7.1 Opportunity record (`opportunities.json`; events in `opportunity_events.jsonl`)

```json
{
  "id": "STP-GBPUSD-20261124-1700-23",
  "instrument": "GBPUSD",
  "direction": "SELL",
  "status": "WATCH_AND_WAIT",
  "status_reason": "...",
  "phase": "REJECTION_TRIGGERED",
  "entry_zone": {"low": 1.31176, "high": 1.31286, "near_edge": 1.31176, "far_edge": 1.31286,
                 "class": "Major", "families": ["pivot","session","structure"],
                 "reference": {"name": "weekly pivot", "price": 1.31273},
                 "levels": [{"name": "weekly pivot", "price": 1.31273, "fixed": true}, "..."]},
  "identity": ["SELL", [["4-hour swing high","1.31286"],["hourly swing high","1.31219"],["hourly swing high","1.31286"],["hourly swing low","1.31191"],["weekly pivot","1.31273"]]],
  "justification": {"h4_direction": "BEARISH", "relation_to_h4": "with", "condition": "CORRECTION_ACTIVE",
                    "opportunity": "corrective reversal", "six_factors": {}, "selection_reason": "...",
                    "technical_context": {"SELL": "INSUFFICIENT_EVIDENCE (score ...)", "BUY": "..."}},
  "reversal": {"direction": "SELL", "state": "AUTHORISABLE",
               "destinations": {"intermediate": 1.31141, "primary": 1.30841, "extended": 1.30373},
               "invalidation": {"zone_break_close_1h": 1.31316, "structure_break_close_4h": 1.31451,
                                "destination_first": 1.30841, "conditions": ["..."]}},
  "continuation": {"direction": "BUY", "state": "DORMANT",
                   "activation": "an hourly close at or above 1.31316 (D-20), assessed by STP's re-plan at that close",
                   "destinations": null,
                   "invalidation": {"close_back_inside_1h": "set at activation", "destination_first": "set at activation"}},
  "monitor": {"interacted_at": "2026-11-24T17:05Z", "tests": 1, "rejection_attempts": [], "max_overshoot": null,
              "closed_beyond": [], "reclaims": [], "break": null, "last_price_utc": "...", "last_candle_utc": "..."},
  "bindings": [{"signal": "STP-GBPUSD-20261124-1700-23#t1", "strategy": "...", "direction": "SELL", "opened_utc": "..."}],
  "current": true,
  "observe_only": true,
  "history": []
}
```

The 17:00 values shown are recorded values, sell prices:
- zone 1.31176–1.31286, with a weekly pivot reference at 1.31273;
- destinations: intermediate 1.31141, primary 1.30841, extended 1.30373;
- invalidation: hourly 1.31316, H4 1.31451.

At 18:00 the zone was updated in place to 1.31191–1.31286 as the non-fixed New York-session-high level moved.

### 7.2 Request from `_place`
`strategy, direction, idea time, entry price, rejection candle (time, high, low) from the idea's context, live bid/offer`

### 7.3 An idea is authorised only if ALL of these hold
1. The strategy is gated (OD-03). Every other strategy passes through, and the check does not apply to it.
2. A live opportunity has a hypothesis in the idea's direction that is authorisable now:
   - the **reversal**, in WAITING or WATCH_AND_WAIT; or
   - the **continuation**, ACTIVE in BREAK_PENDING or CONTINUATION.
3. The rejection candle interacts with that opportunity's zone, within 3 pips (D-29 A, H08). The entry itself may be outside the zone.
4. The entry price is not beyond that hypothesis's zone-break price (FC-07). The live price has not reached its primary destination (H12).
5. The register is current (the monitor stepped on the latest candle and tick), and the prices are fresh (D-21 b, FC-08).
6. Rule 11 has not already used the signal key `<id>#t<n>` (§7.5).
7. The strategy's own confirmation has happened (implicit: `_place` is only reached after it; H06, H07).

### 7.4 Choosing among several opportunities, and refusals
- **If more than one opportunity matches:** use the one whose zone the rejection candle interacted with. If still more than one, use FC-03's tie-break (strongest class, then nearest).
- **Opposite directions at once:** BUY and SELL opportunities may both be live. Each authorises only its own direction at its own zone. A SELL at resistance and a BUY at support are independent.
- **A refusal** is recorded as `book.decision("STP refused", reasons)`.
- **With the switch off,** the check does not run and nothing "would-have-authorised" is logged. There is no shadow trading.

### 7.5 Duplicate prevention (H13, OD-09)
- An authorised idea gets `context["signal"] = "<id>#t<n>"`, where n is the opportunity's current D-25 test number.
- Rule 11 then refuses a second trade with that key, whether the first is open, closed or sent but unsettled. This covers:
  - the 5-minute bounce and Level Reversal on the same rejection;
  - a re-entry on the same test after a stop-out.
- A new test (price leaves the zone and returns) allows one more trade (H19).
- Continuation trades use `#c<n>`, numbered from the continuation's own retests.
- `ONE_SIGNAL_ONE_TRADE` must stay on. If it is off, the STP check refuses gated ideas rather than leave duplicates possible.

---

## 8. Reversal and continuation monitoring design

### 8.1 The existing dual conditional-scenario forecaster: assessment

| Requirement | `planner/technical.py` today | Verdict |
|---|---|---|
| Proposes BUY and SELL independently | Yes, one candidate per direction per hour (`technical.py:615-659`) | ✓ |
| Credible opportunities against the H4 direction | Scores evidence with a **−1 countertrend penalty** and needs `min_evidence = 4`. On 24 Nov (06:00 to 17:00 candles) every BUY scenario was INSUFFICIENT_EVIDENCE; the only BUY candidates were FAILED_BREAKOUT, countertrend, score 2 (14:00 and 17:00 candles). The 08:30 to 18:00 bullish correction was never proposed. | ✗ |
| Identifies location in advance | Reacts to the last 3 hourly candles ("no reaction yet: watch, do not forecast") | ✗ (reactive) |
| Identity, persistence, lifecycle | None; a new snapshot each hour | ✗ |
| Contract: intermediate, primary and extended destinations | Intermediate and extended targets only; no primary | ✗ |
| No time expiry | `validity_hours = 8` (used only by research code today) | ✗ (H16) if used |
| Approved numbers | `min_evidence`, the point weights, `stop_buffer_range_share`, `range_*`: I found no approval record in PARAMETER_APPROVAL_REGISTER | ✗ |
| Validated | The 20 Nov out-of-sample check found no edge (memory: STP technical opportunities) | ✗ |
| Stop and trade invalidation | It sets a trade stop, which is the strategies' and trade manager's job | ✗ (boundary) |

**Conclusion:** not suitable as the authorisation source. It is kept as observe-only **context**, copied into `justification.technical_context`. It is not a second rule set (H23).

### 8.2 Bidirectional proposals (OD-06, OD-16, OD-17)

STP's approved zone map (`planner/zones.py`) is already direction-neutral: it has zones above and below the price. The change is confined to `assess.py`'s gates:

- **SELL proposal:** among zones at or above the price (including one the price is in), apply D-16: at least Moderate, NEAR or PLAUSIBLE (D-14), strongest class then nearest.
  - Destinations are below, per D-18 and D-19: intermediate is the first zone beyond; primary is the first Major zone; extended is the next Major zone.
  - Invalidation per D-20: an hourly close at least 3 pips beyond the far edge, and the H4 swing break above.
  - The destination-first rule (D-1) applies.
- **BUY proposal:** the mirror image, below the price.
- **The H4 direction, condition and six factors** are recorded as `justification`, with `relation_to_h4` set to with or against.
  - The condition classes (D-10) keep their meaning for proposals with the H4 direction.
  - Proposals against the H4 direction get `opportunity = "countertrend reversal"`. This is a label, not a gate.
- **Unchanged:** zone construction, grading, reachability, destinations, invalidation, re-plan cadence and the 5-pip / 0.15 × ADR width.
- **Removed, behind a switch:** the H4-direction and condition gates (`assess.py:376-383, 391-393`).

### 8.3 Zone-aware rejection monitoring (H17, H19, H20)
- **The monitor owns a `RejectionWatcher` instance** that uses the existing step logic and settings:
  - reversal within 3 candles;
  - a confirmation close within 3 candles;
  - a trigger;
  - cancel past the reversal candle;
  - the spread guard.
- **One generalisation:** "pierce" accepts a zone, using `zones.interacts` with the 3-pip tolerance. That needs a small refactor of `_pierced`.
- **Other copies are unchanged:** the analyser's and the strategies' watcher copies keep single-price levels and produce byte-identical events (T-27).
- **Each attempt** is recorded against the opportunity: started, reversal, confirmation, triggered, cancelled or expired.
  - The 3-candle limits end an **attempt**, never the opportunity.
  - A failed attempt leaves the opportunity in WATCH_AND_WAIT.
- **The attempts are monitoring evidence, not entries.** Strategies still confirm with their own watcher copies. This keeps H06 intact and avoids a second confirmation rule.

### 8.4 Continuation (OD-08 modified C)
- **When STP proposes an opportunity,** it also specifies the continuation hypothesis:
  - direction opposite;
  - entry location: the same zone, retested from the far side;
  - activation: D-20's confirmed break of that zone (an hourly close at least 3 pips beyond the far edge).
- **Activation is decided by STP's own re-plan at that hourly close** (OD-19 A).
  1. From the zone map as it stands then, it computes the continuation's destinations: D-18 in the continuation direction, which needs a Major zone for the primary destination.
  2. It also computes the continuation's invalidation: an hourly close back inside the zone by at least 3 pips, the mirror of D-20, plus destination first.
  3. If there is no valid primary destination, or the price has already reached it, **the continuation does not activate.**
- **What never activates a continuation:**
  - a failed rejection (H19);
  - a wick or a close beyond by less than 3 pips (H09);
  - any judgement by the bot.

  So the bot never invents an opposite-direction authorisation.
- **While the P-F7 window is open (BREAK_PENDING),** a close back inside reinstates the reversal and ends the continuation (OD-07).
- **Confirmation:** the gated strategies confirm continuation entries the same way they confirm reversals. For example, Level Reversal or the 5-minute bounce buying a rejection off the broken resistance from above. That is exactly what Level Reversal did at 15:30 today at 1.31000.
- **Ungated continuation strategies** (slow grind, breakout, Asian range breakout, EMA pullback) keep their own rules (OD-18 A).

### 8.5 Sessions, rollover, weekly open, restarts
- **No opportunity expires on time** (H16). Monitoring runs whenever prices arrive.
- **New entries** keep every existing session rule: 06:00 to 20:30 UK, the slow grind's own hours, news windows, the rollover pause and the 20:30 close.
- **00:00 UK re-plan (the pivots roll over):**
  - An opportunity whose fixed levels survive carries over.
  - One whose identity changes is handled per §5.3: SUPERSEDED if reissued, INVALIDATED if its levels are gone with no successor.
- **Weekly open:** the first re-plan re-validates every opportunity against its own conditions (OD-13).
- **Restart:** the monitor reloads `opportunities.json`. Until it has stepped on a fresh candle and tick, `current` is false and authorisation is refused.
- **Open trades** are never touched by STP status changes (H14).

---

## 9. Technical test specification (offline; IG never contacted)

**Acceptance criteria and their tests:**

| Acceptance criterion | Tests |
|---|---|
| Independent BUY and SELL opportunities | T-01, T-02, T-03 |
| Several valid at once | T-04, T-05 |
| Kept across hourly updates | T-06, T-07, T-08 |
| Correct structural invalidation | T-09 to T-14 |
| Repeated tests, stalling, failed rejection | T-15 to T-18 |
| Watch & Wait behaviour | T-19 to T-21 |
| Reversal confirmed by existing strategy rules | T-22, T-23 |
| Continuation with valid structural authorisation | T-24 to T-28 |
| No premature or duplicate entries | T-29 to T-32 |
| Tick-level confirmation | T-33, T-34 |
| Stale data | T-35, T-36 |
| Restarts and sessions | T-37 to T-40 |
| No regression | T-41 to T-45 |
| EMA pullback independent | T-46 |
| Complete journey | T-47 |

**Tests:**

| ID | Test | Expect |
|---|---|---|
| T-01 | A zone map with a qualifying zone above and below the price | One SELL and one BUY proposal, each with its own destinations and invalidation |
| T-02 | H4 BEARISH, qualifying zone below | A BUY proposal, `relation_to_h4 = against`, `opportunity = countertrend reversal` |
| T-03 | Gate switch off | Identical to today: H4 direction only |
| T-04 | Three live SELL opportunities and one BUY | All held; authorisation picks by interaction (§7.4) |
| T-05 | BUY at support and SELL at resistance at once | Each authorises only its own direction and zone |
| T-06 | A re-plan picks a different zone | The existing opportunity keeps its status; the new one is added |
| T-07 | A re-plan recommends nothing; the H4 direction changes; the condition changes | No status change; recorded as context |
| T-08 | Same identity, edges moved by non-fixed levels | Updated in place, history kept |
| T-09 | An hourly close beyond the far edge by less than 3 pips | OVERSHOOT; status unchanged |
| T-10 | An hourly close at least 3 pips beyond | BREAK_PENDING; reversal refused |
| T-11 | T-10, then a close back inside within 3 hourly candles | WATCH_AND_WAIT; continuation ENDED |
| T-12 | T-10, the window passes | CONTINUATION |
| T-13 | An H4 close beyond the structure-break price against the live hypothesis | INVALIDATED |
| T-14 | Rollover removes the fixed levels with no successor | INVALIDATED ("structural levels changed") |
| T-15 | Watcher attempt CANCELLED / EXPIRED | REJECTION_FAILED n+1; still WATCH_AND_WAIT |
| T-16 | Leaves and returns (D-25) | TEST n+1 |
| T-17 | 5 failed attempts, no break | WATCH_AND_WAIT; counts shown; no threshold applied |
| T-18 | A wick beyond the far edge, closed back | OVERSHOOT; deepest point recorded; continuation still DORMANT |
| T-19 | Tick within 3 pips of the near edge | WATCH_AND_WAIT at that tick's time, not the candle's |
| T-20 | 3.1 pips short | stays WAITING |
| T-21 | 500 candles inside the zone | no expiry, no trade without strategy confirmation |
| T-22 | A gated strategy confirms; rejection candle interacts; entry outside the zone | authorised (D-29 A) |
| T-23 | The same with no matching opportunity | refused "no STP opportunity" |
| T-24 | Confirmed break; the re-plan finds a Major zone beyond for the primary destination | continuation ACTIVE; destinations set at activation |
| T-25 | Confirmed break; no Major zone beyond, or price already past the primary destination | continuation stays DORMANT; opposite idea refused |
| T-26 | A failed rejection only | continuation stays DORMANT |
| T-27 | A wick through, or a close beyond by less than 3 pips | continuation stays DORMANT |
| T-28 | Continuation ACTIVE; a gated strategy confirms a retest from the far side | authorised `#c1` |
| T-29 | Price reaches the zone; no strategy idea | no order |
| T-30 | 5m bounce and Level Reversal on one setup | one order; the second refused by rule 11 |
| T-31 | Stopped out, same test, new confirmation | refused (`#t1` used) |
| T-32 | New test, new confirmation | authorised `#t2` |
| T-33 | A live trigger tick reaches the primary destination within the same candle | refused |
| T-34 | Tick-trigger strategies (5m bounce, Level Reversal) and next-open strategies (hourly bounce) | each checked at its own entry moment |
| T-35 | Prices older than `out_of_date_after_minutes` | refused "stale"; status unchanged |
| T-36 | Monitor exception | price service keeps running; `current=false`; refused |
| T-37 | Restart mid-opportunity | reloaded; refused until the first fresh step; counters preserved |
| T-38 | 20:30 to 06:00 | no new gated entries (existing hours); monitoring continues |
| T-39 | 00:00 rollover | carry over or supersede per §8.5 |
| T-40 | Weekly open | re-validated; no time expiry |
| T-41 | All switches off: a full recorded day replayed through engine, sender (stubbed IG), safety and trade manager | decisions and orders byte-identical to today's build |
| T-42 | Analyser, levels and strategy watcher outputs with the monitor on vs off | byte-identical |
| T-43 | Trade manager plans and closes for a trade bound to an opportunity that is then INVALIDATED or SUPERSEDED | unchanged; no close sent |
| T-44 | Ungated strategies with the switches on | unchanged decisions |
| T-45 | Risk and limit rules (rules 1 to 11) | unchanged except the OD-05 bypasses, which apply only to gated strategies |
| T-46 | EMA pullback with the switches on | identical decisions |
| T-47 | Journey: proposal → monitor → strategy idea → `_place` → OrderSender (IG stub) → opened → trade manager plan → close by existing rules | each step recorded with the opportunity id and signal key |

---

## 10. Functional test specification: 24 November 2026 (extended)

**Rule for this section:** every expectation is evaluated **as of** its time, using only candles, ticks and STP records up to that moment. Recorded observations are marked **[R]**. Expected design behaviour is marked **[E]**. Constructed alternatives are marked **[C]**.

All prices are sell prices, UTC (= UK time).

### 10.1 Recorded journey [R]

| Time (UTC) | Observation | Source |
|---|---|---|
| 00:00–08:25 | Range 1.30271–1.30473 (87 of 102 closes within 1.3035–1.3045) | 5m candles |
| 00:00 | STP SELL 0000-17, zone 1.30750–1.30841 (above the pivot); invalidated 08:00 (destination already reached) | `recommendations.jsonl` |
| 08:30 | Bullish breakout: close 1.30478 above the upper Bollinger band and above the M5 EMA100 (1.30386) and EMA200 (1.30436). EMAs were computed from sell closes; they are not recorded. | 5m candles |
| 09:00 | STP SELL 0900-18, zone 1.30750–1.30841; superseded 10:00 | STP |
| 09:45 | First close above the daily pivot 1.30621; held above it from 11:10 | 5m |
| 10:00 | **STP SELL 1000-19 at the daily pivot, 1.30621–1.30715** (invalidation at an hourly close ≥ 1.30745); ACTIVE 10:10 | STP |
| 12:00 | The 11:00 hourly candle closed 1.30891: **bullish continuation through the pivot zone**; 1000-19 invalidated | 1h, STP |
| 13:00 | STP SELL 1300-20, zone 1.31355–1.31421; destination 1.30854 reached 13:35 | STP |
| 14:00 | **STP SELL 1400-21 at R1, 1.31030–1.31141** (R1 1.31141; invalidation at an hourly close ≥ 1.31171; intermediate 1.31013; primary 1.30854) | STP |
| 14:05 | High 1.31025, within 3 pips: zone reached (ACTIVE 14:10) | 5m, STP |
| 14:30 | First close inside the zone, 1.31048 | 5m |
| 14:40–14:50 | Overshoot above R1 to 1.31168 | 5m |
| 15:00 | Hourly close 1.31121 (inside). STP **superseded 1400-21** with 1500-22 (1.31355–1.31421) | 1h, STP |
| 15:05–15:40 | Initial rejection: low 1.30984 at 15:40 | 5m |
| 15:30 | Level Reversal **BUY** opened at 1.31142 (buy price), after a dip to 1.31000; still open at 18:25 | trades |
| 15:55 | Recovery to R1: close 1.31153 | 5m |
| 16:00 | Hourly close 1.31153 (beyond the far edge by 1.2 pips: less than 3) | 1h |
| 16:15 | Day high to that point, 1.31176 | 5m |
| 16:30–16:50 | Lows 1.31082 and 1.31044: **no sustained bearish reversal** | 5m |
| 17:00 | Hourly close 1.31117 (inside). **STP SELL 1700-23 at the weekly pivot, 1.31176–1.31286**: reference weekly pivot 1.31273; intermediate 1.31141; **primary 1.30841**; **extended 1.30373**; **hourly invalidation 1.31316**; H4 1.31451. 1500-22 superseded. | 1h, `issued.jsonl` |
| 17:05 | High 1.31172, within 3 pips of 1.31176: 1700-23 reached (ACTIVE 17:10) | 5m, STP |
| 17:25 onward | Closes above R1 (1.31157 at 17:25) | 5m |
| 18:00 | The 17:00 hourly closed **1.31204**, at least 3 pips above 1.31141 (≥ 1.31171): **confirmed bullish break of the R1 zone (D-20)**. STP updated 1700-23 to 1.31191–1.31286 (non-fixed level moved). | 1h, STP |
| 18:00 | 5m bounce **BUY** idea at 1.31207 (retest of R1 from above; watcher #113): refused by the analyser state ("trend up: only against the trend") | `decisions.jsonl`, replay |
| 18:05 | High 1.31239, inside 1700-23 | 5m |
| 18:05–18:20 | Watcher sell setup #118: pierce 18:05, reversal 18:10, confirmation 18:15 (close 1.31159), trigger 18:20 below 1.31156 | replay |
| 18:20:35 | 5m bounce **SELL** idea: **refused by the RSI stretch** (RSI 3 23.6 < 30) | `decisions.jsonl` |
| 18:25 | Latest candle, close 1.31167 | 5m |
| all day | Dual forecaster: no sufficient BUY scenario at any hour | `technical.jsonl` |

Rejection-watcher events are a code replay over the stored candles, not a live record (OD-14 adds live recording).

### 10.2 Expected register behaviour on the historical data [E]

| As of | Expected |
|---|---|
| 00:00 | 0000-17 SELL WAITING; continuation BUY DORMANT. Bidirectional BUY proposal: computed from the 00:00 map (FT-01); not asserted here. |
| 08:00 | 0000-17 → CANCELLED_DESTINATION_FIRST (same outcome as today) |
| 10:00 | 1000-19 SELL added at the pivot. **0900-18 is not superseded** (different zone; H11). Both live. |
| 12:00 | The 11:00 close 1.30891 is beyond both pivot-area zones by at least 3 pips (≥ 1.30871 and ≥ 1.30745) → **both BREAK_PENDING**. Each continuation BUY activates only if STP's 12:00 re-plan finds a valid BUY primary destination (a Major zone above) not yet reached (FT-02 computes this). The same re-plan made no SELL recommendation because the destination had already been reached. |
| 13:35 | 1300-20 → CANCELLED_DESTINATION_FIRST |
| 15:00 | No hourly close back inside either zone at the 12:00, 13:00 or 14:00 closes (1.30964, 1.30967, 1.31121) → both → CONTINUATION (if active) or INVALIDATED (if the continuation was dormant) |
| 14:00 | 1400-21 SELL WAITING |
| 14:05 | → WATCH_AND_WAIT (tick-level: the first tick within 3 pips; in replay, at the candle level) |
| 14:40–14:50 | OVERSHOOT, deepest 1.31168 (short of 1.31171) |
| 15:00 | Hourly close 1.31121: no break. **1500-22 added; 1400-21 kept** (H11) |
| 15:05–17:00 | Zone-aware attempts recorded: failures leave it in WATCH_AND_WAIT (H19). Triggered attempts (around 15:40 and 16:35 in the level replay; recomputed against the zone) are evidence only. A gated strategy's confirmed SELL here is **authorised by STP**, bound to `#t<n>`, and still subject to the retained filters (RSI stretch, hours, news, risk). The 15:40 and 16:35 5m bounce sells were refused today by the analyser state, which OD-05 removes; the FT-03 test records which retained filter, if any, refuses them. |
| 16:00 | Hourly close 1.31153: OVERSHOOT (closed beyond by less than 3 pips); not a break; continuation DORMANT |
| 17:00 | Hourly close 1.31117: RECLAIM. 1700-23 SELL added; **1400-21 and 1500-22 kept** |
| 17:05 | 1700-23 → WATCH_AND_WAIT |
| 18:00 | 17:00 close 1.31204 ≥ 1.31171 → **1400-21 BREAK_PENDING** (P-F7 window: the 19:00, 20:00 and 21:00 closes). Continuation BUY: STP's 18:00 re-plan works out the destinations. The next zone above, 1700-23 (Major, 1.31191–1.31286), is one the price (1.31204) is **already inside** → the primary destination is already reached → **the continuation does not activate** (expected; FT-07 confirms from the as-of map). |
| 18:00 | 5m bounce BUY at the R1 retest → **refused by STP**: no authorisable BUY at that zone. The bot does not create one because the reversal failed. |
| 18:20 | 5m bounce SELL from 1700-23: rejection candle (18:10, high 1.31231) interacts; SELL; entry 1.31156 not beyond 1.31316; 1.30841 not reached; current → **STP authorises**, then **refused by the retained RSI stretch** (as recorded). A credible location plus STP authorisation still does not trade without every independent condition. |
| 18:25 (end) | 1400-21 BREAK_PENDING (unresolved), 1500-22 WAITING, 1700-23 WATCH_AND_WAIT, Level Reversal BUY untouched by STP (H14). Nothing expired. |

**Pass criteria:**
- No opportunity ends except by its own condition.
- No order is placed without a gated strategy's own confirmation.
- No opposite-direction authorisation exists that STP did not specify.
- Every event above is recorded with its time.
- No future data is used.

### 10.3 Alternative resolutions [C]
Each is constructed from the 18:25 state, or from 17:00 where noted, by appending synthetic ticks and candles labelled CONSTRUCTED.

| FT | Scenario | Construction | Expected |
|---|---|---|---|
| FT-A1 | Confirmed bearish reversal at R1 (from 17:00) | A rejection at R1, confirmation, a fall to 1.30854 | One authorised SELL (`#tn`); COMPLETED at the destination; existing trade management |
| FT-A2 | Confirmed bullish breakout and continuation (from 18:00) | P-F7 hourly closes stay above 1.31171; a constructed map gives a Major zone above as primary, not yet reached | 1400-21 → CONTINUATION; BUY continuation ACTIVE (`#c1`); a gated strategy's retest BUY authorised; the reversal SELL refused |
| FT-A2b | Breakout with no valid continuation destination (historical 18:00) | as recorded | continuation DORMANT; BUY refused (§10.2) |
| FT-A3 | Several unsuccessful rejections | Four more cancelled attempts at 1700-23, no break | WATCH_AND_WAIT; failure count rises; no automatic entry |
| FT-A4 | Temporary sweep, then reversal | A wick to 1.31330 (beyond 1.31316) with the hourly close inside, then confirmation | not invalidated; continuation DORMANT; SELL authorised |
| FT-A4b | Close beyond and back | An hourly close at 1.31320, the next close back inside | BREAK_PENDING → WATCH_AND_WAIT (OD-07) |
| FT-A5 | Reversal just short | Rejection candle high 1.31150 (2.6 pips short of 1.31176) / 1.31140 (3.6 pips short) | authorised / refused |
| FT-A6 | Structural invalidation | An H4 close ≥ 1.31451 | SELL opportunities INVALIDATED; the open bound trade untouched |
| FT-A7 | Consolidation without confirmation | 60 candles inside 1.31141–1.31239 with no confirmation | WATCH_AND_WAIT throughout; no expiry; no trade |
| FT-A8 | A newer, higher zone | Historical 15:00 and 17:00 proposals | all held; binding by interaction |
| FT-A9 | Several strategies on one opportunity | 5m bounce and Level Reversal on one setup | one trade; the second refused (rule 11) |
| FT-A10 | Destination before entry | Historical 1300-20 at 13:35; constructed: a fall to 1.30841 with no entry | CANCELLED_DESTINATION_FIRST |
| FT-A11 | Open position when the recommendation changes | Historical: the Level Reversal BUY (15:30) through the 17:00 and 18:00 changes; constructed: a bound SELL, then INVALIDATED | no trade-manager change |
| FT-A12 | Session close and rollover | Constructed ticks to 20:30 and 00:00 25 Nov; 25 Nov pivots from 24 Nov's candle | no gated entries after 20:30; at 00:00 the R1-based identity is superseded or invalidated per §8.5 |
| FT-A13 | Stale data mid-interaction | A 12-minute gap in ticks | refused "stale"; resumes on fresh data |
| FT-A14 | Restart mid-test | restart at 16:00 | state reloaded; refused until the first fresh step |

**Method:**
- The monitor and the planner run over the stored candles. The planner gives its as-of views with `show --at`.
- Strategy ideas come from `decisions.jsonl` (historical) or from the strategy runner (constructed).
- `_place`, `OrderSender` and the trade manager run with a stub IG client.
- Tick-level behaviour in the historical replay is approximated at the candle level, because no ticks are stored. Tick-level tests use constructed tick streams.
- **No profit-and-loss is evaluated.** These are behaviour tests; the live IG demo remains the judge.

**Functional tests that compute rather than assert:**

| FT | Computes |
|---|---|
| FT-01 | The bidirectional proposals at each hour |
| FT-02 | The pivot-zone continuations at 12:00 |
| FT-03 | Which retained filter refuses the 15:40 and 16:35 sells |
| FT-05 | Whether the 15:30 Level Reversal BUY would have been authorised |
| FT-07 | The 18:00 continuation |

Their results are reported to the owner before any approval. They are not tuned.

---

## 11. Traceability

### 11.1 H01 to H23

| ID | Design | Reused code | Tests |
|---|---|---|---|
| H01 Hourly forecasts | §3, §8.2 | `assess`, re-plan cadence | T-01, T-03 |
| H02 Direction, zone, destinations, invalidation | §7.1, §8.2, §8.4 | `Plan`, D-18, D-20 | T-01, T-24 |
| H03 STP sole reversal authority | §6, §7.3, OD-03, OD-05 | – | T-22, T-23, T-45 |
| H04 No matching opportunity, no trade | §7.3 (2) | – | T-23, T-25 |
| H05 Reaching the zone is not a trade | §5.1, §7.3 (7) | ARCH §13.1 | T-29, FT-A7, §10.2 18:20 |
| H06 Strategies keep confirmation | §6, §8.3 | strategies unchanged | T-22, T-44 |
| H07 Strategy timeframe, tick level | §3.2, §7.2 | `engine._live_entries` | T-33, T-34 |
| H08 3-pip tolerance | §5.3, §7.3 (3) | `near_level_within_pips` | T-19, T-20, FT-A5 |
| H09 Overshoot does not invalidate | §5.4 | D-24 | T-09, T-18, FT-A4 |
| H10 Invalidation per STP | §5.3 | D-20, ARCH §10.2 (amended §14) | T-10 to T-14 |
| H11 A newer forecast does not cancel | §5.3 | – | T-06, T-07, §10.2 |
| H12 Destination before entry cancels | §5.3, §7.3 (4) | D-1 | T-33, FT-A10 |
| H13 No duplicates | §7.5 | rule 11 | T-30 to T-32 |
| H14 Trade manager owns positions | §8.5 | unchanged | T-43, FT-A11 |
| H15 EMA pullback independent | §6 | – | T-46 |
| H16 No time expiry | §5.3, §8.5 | D-21 | T-21, T-40, FT-A7 |
| H17 Every opportunity monitored | §3, §5 | keeper checks | T-04, §10.2 |
| H18 Watch & Wait | §5.2 | – | T-19 to T-21 |
| H19 Failed rejection is not invalid | §5.4, §8.3 | watcher CANCELLED / EXPIRED | T-15, T-26, FT-A3 |
| H20 Rejection / test / overshoot / breakout distinct | §5.4 | D-20, D-24, D-25 | T-09 to T-18 |
| H21 Both outcomes monitored | §5.1, §8.4 | – | FT-A1, FT-A2 |
| H22 Continuation needs authorisation and confirmation | §8.4 | D-20 | T-24 to T-28, FT-A2b |
| H23 Reuse, no duplication | §3.2, §8.1, §8.3 | zones, keeper, watcher, rule 11 | T-42 |

### 11.2 Decisions

| OD | Where | Tests |
|---|---|---|
| OD-01 | §5.3 | T-04, T-05 |
| OD-02 | §5.3 | T-06, T-07 |
| OD-03 | §6, §7.3 | T-23, T-44 |
| OD-04 | §8.2 | T-01 |
| OD-05 | §4.2, §6 | T-45, FT-03 |
| OD-06 | §8.2 | T-02, T-07 |
| OD-07 | §5.3 | T-11, FT-A4b |
| OD-08 | §8.4 | T-24 to T-28 |
| OD-09 | §7.5 | T-30 to T-32 |
| OD-10 | §5.4 | T-17 |
| OD-11 | §5.2 | – |
| OD-12 | §3 | T-19, T-33, T-36 |
| OD-13 | §8.5 | T-40 |
| OD-14 | §7.1 | T-47 |
| OD-15 | §15 | – |
| OD-16 | §8.2 | T-02 |
| OD-17 | §8.2 | T-01 |
| OD-18 | §6 | T-44 |
| OD-19 | §8.4 | T-24, T-25 |
| OD-20 | §13.3 | – |
| OD-21 | §4.3 | T-08 |

---

## 12. Implementation work packages and dependencies

| WP | Content | Depends on | Switch |
|---|---|---|---|
| WP-1 | Opportunity data model, `opportunities.json` and `opportunity_events.jsonl`, single writer, migration from today's `current.json` (history kept) | – | `STP_OPPORTUNITY_MONITOR` |
| WP-2 | Refactor the keeper's 5-minute and hourly checks into pure functions; keeper lifecycle retired when the monitor is on | WP-1 | same |
| WP-3 | In-process monitor: hooks in `after_new_candle` (before `engine.on_candle`) and `on_price` (before `engine.on_price`); "never stop the price service" protection; restart reload | WP-1, WP-2 | same |
| WP-4 | Zone-aware watcher instance (generalise `_pierced`); attempt recording (OD-14) | WP-3 | same |
| WP-5 | Bidirectional proposals in `assess` (per-direction D-16; H4 gate removed); `justification` with H4 context and technical context | WP-1 | `STP_BIDIRECTIONAL` |
| WP-6 | Continuation hypotheses: specification at issue; activation and destinations at the confirming hourly re-plan; the P-F7 window | WP-3, WP-5 | same |
| WP-7 | Authorisation in `_place`; signal keys `#t` / `#c`; OD-05 bypass list for the gated strategies; refusal records | WP-3 | `STP_AUTHORISES_ENTRIES` |
| WP-8 | Dashboard STP tab: opportunities, phases, counters, continuations, conflicts (OD-18) | WP-1 | – (read only) |
| WP-9 | Tests T-01 to T-47 and FT fixtures (24 Nov, extended through the latest recorded candle) | all | – |
| WP-10 | Readiness pack: test results, the computed FT outputs (FT-01, 02, 03, 05, 07), and a diff of decisions with the switches off | WP-9 | – |

**Order:** WP-1 → WP-2 → WP-3 → (WP-4, WP-5) → WP-6 → WP-7. WP-8 and WP-9 run alongside, and WP-10 comes last.

Each work package goes on its own branch, is pushed, and is not merged until approved.

---

## 13. Deployment and rollback plan

### 13.1 Gates
1. **Owner approval** of this design and of the §4.2 and §4.3 points.
2. **Implementation of WP-1 to WP-9.** All switches off by default.
3. **Offline technical and functional tests pass** (T-41: byte-identical with the switches off). Owner review of WP-10.
4. **Stage A**, only with explicit approval:
   - Deploy with `STP_OPPORTUNITY_MONITOR=on` and `STP_BIDIRECTIONAL=on`, and `STP_AUTHORISES_ENTRIES=off`.
   - STP stays observe-only: the register and dashboard are live; trading is unchanged.
   - This is not shadow trading: no simulated orders, and no "would-have" decisions are logged.
5. **Stage B**, only with separate explicit approval (D-33, D-37):
   - `STP_AUTHORISES_ENTRIES=on`. Real demo trading on **IG DEMO**.
   - No shadow or parallel execution.

### 13.2 Mechanics
- **Before each stage:** tag `pre-stp-integration-<stage>-<date>` on the deployed commit, and record the `.env` diff.
- **Code:** check out the approved commit in `/opt/autobot`.
- **Restart:** done by the owner (`autobot-prices`). The dashboard restart is the owner's too.
- **Rollback, at any stage:**
  - **Fastest:** set the stage's switch off and have the owner restart. With every switch off, behaviour is identical to today (T-41).
  - **Full:** check out the tag and have the owner restart.
  - `opportunities.json` is left on disk for audit. The keeper's legacy lifecycle resumes when the monitor switch is off.
- **Open trades** are unaffected by deployment or rollback (H14).
- **Kept as they are:** every existing trading and session rule, and the 20:30 close. No two-hour close is added.

### 13.3 Proposed switches and settings (OD-20; not applied)

| Item | Default |
|---|---|
| `STP_OPPORTUNITY_MONITOR` | off |
| `STP_BIDIRECTIONAL` | off |
| `STP_AUTHORISES_ENTRIES` (replaces the never-built `PLANNER_AUTHORISES_BOUNCE`) | off |
| `[stp_authorisation] strategies` | `["bollinger_bounce", "bollinger_bounce_5m", "level_reversal"]` |
| `[stp_authorisation] bypass_filters` | `["analyser_state", "hourly_context", "counter_trend_tiring", "one_view"]` |

**No new numbers:** reused values only (§1).

---

## 14. Amendments required to D-01 to D-38 (and FC / ARCH items)

| Item | Approved | Amendment | Source |
|---|---|---|---|
| D-03 | The H4 direction decides the direction | H4 is context; opportunities in both directions | OD-06 |
| D-10 | Condition classes gate a recommendation | They describe with-H4 proposals only; no gate | OD-06, OD-16 |
| D-16 | One preferred zone in the H4 direction | Applied per direction | OD-17 |
| D-20 | A confirmed break invalidates | It moves to BREAK_PENDING; reinstated by a failed breakout; activates the continuation; final after P-F7 | OD-07, OD-08 |
| D-22 A | Supersede on a different zone | Supersede only for the same identity; a different zone adds an opportunity | OD-02 |
| D-23 A | One live per instrument | Many, de-duplicated by identity | OD-01 |
| D-24 A | Sweeps, reclaims and failed breakouts recorded only | Sweeps and reclaims still recorded only; the failed breakout (P-F7) now affects authorisation | OD-07 |
| D-25 A | Tests recorded only | Still not a filter; the test number keys duplicate prevention | OD-09 |
| D-29 A | The hourly bounce; check 7 in `common.allowed` | Three strategies, both directions; the check in `Trading._place` (it needs the live price and the register; the single funnel); the "rejection candle interacts" rule unchanged | OD-03 |
| D-33 | `PLANNER_AUTHORISES_BOUNCE` | Three switches (§13.3); activation still separate and explicit | OD-20 |
| D-36 A | The re-plan cadence | Unchanged for forecasting; the lifecycle moves in-process | OD-12 |
| D-37 | "Bounce strategies"; the EMA pullback independent | Plus Level Reversal; the EMA pullback still independent | OD-03 |
| FC-10 | NEUTRAL / TRANSITIONAL invalidates | Context only | OD-06 |
| ARCH §10.2 | Invalidation triggers include a direction change and "evidence materially changes" | Both removed as triggers (recorded as context) | OD-02, OD-06 |
| ARCH §11.2 | CANDIDATE / WAITING / ACTIVE lifecycle; entries only while ACTIVE | Replaced by §5 | H17 to H19 |
| ARCH §13 | Bounce-only authorisation; no effect on other filters | Three strategies; OD-05 bypasses | OD-03, OD-05 |
| 15–16 Nov "without hindrance" (bounce) | – | Ended for both bounces (already settled by D-37); session strategies unchanged | D-37 |

**Unchanged:** D-01, D-02 (the direction rule stays EMA-pullback only), D-04 to D-09, D-11 to D-15, D-17 to D-19, D-21 (strengthened: weekly re-validation), D-26 to D-28, D-30 to D-32, D-34, D-35 and D-38.

---

## 15. Remaining gaps and unresolved decisions

1. **Owner confirmations from §4.2:**
   - OD-02: H11 takes precedence over the "evidence changes" trigger.
   - OD-05: the bypass list; RSI stretch and Level Reversal's levels kept.
   - OD-07: P-F7 = 3 used for authorisation.
2. **OD-16 to OD-21**, in §4.3.
3. **Unknown until the WP-10 test run.** Whether the bidirectional zone map would have produced BUY opportunities during today's correction, and where. This is computed by FT-01, FT-02 and FT-05 and not asserted in advance. If it produces none, the both-directions requirement is met in mechanism but not demonstrated on 24 Nov. That would be reported, not tuned.
4. **No tick history is stored.** Tick-level behaviour can only be tested with constructed tick streams. Historical replays are candle-level.
5. **Rejection-watcher events are not stored live today.** The 24 Nov fixture is a code replay and may differ from what ran live.
6. **The dual forecaster's numbers** (`min_evidence`, the point weights, `validity_hours`) have no approval record I could find. They stay observe-only context. Making them authoritative would need approval.
7. **Conflicting exposure (OD-18).** Without a new rule, an STP-authorised SELL and an ungated BUY (for example the slow grind) can both be open.
8. **OD-15: inert `.env` switches** (`LEVEL_STOPS` and seven others) are referenced nowhere in the live code. This goes to a separate investigation and is not touched here.
9. **The keeper lifecycle migration (WP-1, WP-2)** changes STP's own records and dashboard during Stage A. It needs owner sign-off as part of Stage A, even though trading is unaffected.
10. **The fixture ends at 18:25.** The R1 breakout's P-F7 window (the 19:00 to 21:00 closes) and 1700-23's outcome were unresolved at the time of writing. They will be appended from recorded data before WP-10, without changing any expectation already written.
