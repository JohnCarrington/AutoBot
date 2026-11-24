# Structural Trade Planner: strategy integration (minimum viable design, revision 3.2: final)

**Status:** DESIGN CLOSED, for independent review. Every decision is approved (§5). Nothing here is implemented, deployed or switched on. STP stays observe-only. Implementation awaits the owner's approval after the independent review.

| | |
|---|---|
| **Revision** | 3.2 (final), 24 November 2026. Records the owner's approval of OD-30 to OD-33 and adds the hourly-publication race (§9.5, FT-R1) and full technical and functional coverage (§15). 3.1: Records the owner's approval of OD-26 to OD-29 and the closure of OD-02, OD-16 and OD-17; applies the duplicate-key findings (§10); adds the computed 24 Nov two-direction results (§14). Readiness assessment: `STP_INTEGRATION_READINESS_20261124.md`. Revision 3: 58fc591. Revision 2: fc06361. Revision 1: c373280. |
| **Code examined** | `/opt/autobot` at 63d9c04, the live build |
| **Approved STP spec examined** | `/home/autobot/research/structural_trade_planner_v1/` (D-01 to D-38, FC-01 to FC-13, PARAMETER_APPROVAL_REGISTER) |
| **Requirements** | H01 to H23, approved. All remain covered (§12). |
| **Fixtures** | `stp_strategy_integration_20261124/`: the 24 Nov 5-minute R1-window candles, the hourly candles, and a rejection-watcher code replay from 00:00 to 18:30 |

**The governing principle (owner):**

> STP identifies the entry zone and the permitted direction. Existing AutoBot strategies confirm and execute the trading opportunity. No additional trading intelligence or confirmation engine is required.

**Contents**
1. Summary
2. What revision 3 removes from revision 2
3. Verified facts the design depends on
4. Architecture
5. Decision register
6. Opportunity lifecycle
7. Strategy integration matrix
8. Making STP zones visible to the strategies (Option A)
9. The authorisation check
10. Duplicate prevention
11. Bidirectional STP forecasting: mandatory prerequisite
12. Sessions, rollover, weekly open, restarts
13. Technical test specification
14. Functional test specification: 24 November 2026
15. Traceability
16. Amendments (approved STP items and revision-2 decisions)
17. Work packages
18. Deployment and rollback
19. Open items and investigations

---

## 1. Summary

The integration has three parts. Nothing else changes.

| Part | What it is | Where |
|---|---|---|
| **Opportunity monitor** | STP's existing recommendation tracker (`planner/keeper.py`), changed to hold several opportunities and to end each one only by its own conditions | the existing planner subprocess, run after each 5-minute candle (no new process, no new service) |
| **Zones visible to strategies** | Each live STP zone is added to the **strategies'** copy of the level list (Option A) | the strategies' rejection-watcher copy only |
| **Authorisation check** | One read-only function called from the single order funnel | `Trading._place`, for the three gated strategies |

**Monitor responsibilities (owner's list) and where each lives:**

| Responsibility | Implementation | Reused code |
|---|---|---|
| Receive the hourly recommendations | the tracker's hourly re-plan, unchanged cadence | `keeper.replan`, `assess` |
| Maintain valid opportunities | a list instead of one; a new forecast adds, never cancels | the tracker's identity and update logic |
| Monitor zone interaction | the tracker's 5-minute zone touch, 3-pip tolerance | `zones.interacts` |
| Make opportunities available to strategies | live zones added to the strategies' level copy | `levels.build`, the strategies' watcher |
| Check authorisation when a strategy confirms | §9 | new (one function), using the tracker's own rules |
| Prevent duplicates | signal key `<opportunity id>#t<test>` through safety rule 11 | rule 11, `zones.count_tests` |
| Manage invalidation | the tracker's existing rules, plus the H4 structure-break close it does not yet check | `keeper.hourly`, `watch_after_break`, the plan's own `invalidation` |

**Unchanged:** every strategy's confirmation method; execution; stop placement; take profit; risk; position limits; the trade manager; exits; trading hours, news windows, the rollover pause and the 20:30 close. EMA pullback is independent. There is no mandatory hourly entry confirmation, no new confirmation algorithm, no new indicator, no new numerical parameter, no time-based expiry and no two-hour closure.

**Gated strategies (OD-03):** the hourly Bollinger bounce, the 5-minute Bollinger bounce and Level Reversal, BUY and SELL.

**Activation prerequisite:** STP must propose opportunities in both directions before any entry is authorised (§11).

---

## 2. What revision 3 removes from revision 2

| Removed | Reason | Replaced by |
|---|---|---|
| A new opportunity-monitor module inside the price service, with hooks on every candle and every price | a second lifecycle engine; moves STP code | the existing tracker in its existing subprocess. The tracker's lag of up to one candle is covered by the authorisation check, which re-applies the tracker's own rules to everything since its last step (§9.3). |
| A new `opportunities.json` and `opportunity_events.jsonl` with a new single writer | new files and ownership | the tracker's existing `current.json` (now holding a list) and `recommendations.jsonl` |
| The zone-aware rejection watcher and per-attempt records | a second confirmation layer | none. Strategies confirm with their own watcher copy. |
| Phases (approaching, in zone, overshoot depth, rejection attempt / failed, reclaim, left zone) | analysis, not coordination | the tracker's existing recorded events, unchanged: closed beyond, reclaim, wick sweep, failed breakout |
| The continuation hypothesis inside each opportunity (dormant / active, destinations at activation, `#c` keys; OD-19, OD-21) | extra machinery | STP's own next proposal. Once a zone is broken, STP's bidirectional re-plan proposes the opposite-direction opportunity from its zone map, or it does not. The bot never infers one. |
| BREAK_PENDING and CONTINUATION statuses | too many states | one status, **BROKEN**, which authorises nothing (§6) |
| The dual forecaster's output copied into each opportunity | not needed | nothing. It stays observe-only on the STP tab as today. |
| Conflict reporting on the dashboard and daily summary (OD-18 reporting) | adds reporting | the conflicts are listed in this design for the owner (§7.2) |
| Dashboard phases, counters and continuation panel | not needed | the STP tab lists the live opportunities and each one's status |
| The tracker's demotion from ACTIVE back to WAITING when price stays clear | contradicts Watch & Wait (H18) | none: once touched, an opportunity stays in Watch & Wait until it ends |

**Not removed, despite the smaller implementation:** functional test coverage. Every applicable H01 to H23 requirement keeps at least one technical test and one 24 Nov functional test (§12, §15). Tests of removed mechanisms are replaced by tests of the same requirement against the minimum mechanism.

---

## 3. Verified facts the design depends on

- **Timing.** After each 5-minute candle the price service runs, in order: levels, analyser states, `engine.on_candle`, then the planner as a detached subprocess (`prices/service.py:262-273`, `planner/keeper.py:504-529`). The planner therefore sees a candle seconds after the engine. Re-planning happens only at the hourly close.
- **The tracker today** (`planner/keeper.py`):
  - holds one recommendation (D-23 A); statuses WAITING, ACTIVE, INVALIDATED, SUPERSEDED, COMPLETED;
  - 5-minute checks (`five_minute`, `:267-309`): the zone touch (WAITING to ACTIVE) and the primary destination (COMPLETED after the zone, INVALIDATED "destination reached before entry" before it). A candle that began before the recommendation was created is recorded AMBIGUOUS and changes nothing;
  - hourly checks (`hourly`, `:311-352`): a close at least `break_beyond_pips` (3) beyond the far edge invalidates (D-20). Closes beyond by less, reclaims and wick sweeps are recorded only. `watch_after_break` records a failed breakout within `failed_breakout_within_candles` (3, P-F7) and is recorded only. ACTIVE goes back to WAITING when an hourly candle stays wholly clear of the zone;
  - re-plan (`replan`, `:354-419`): invalidates on an H4 direction change; supersedes on a different zone; invalidates on "supporting evidence changed" when nothing is recommended.
- **The plan's invalidation** (`assess.py:462-475`) already carries `zone_break_close` (1h), `structure_break_close` (4h), `destination_first` and `destination_first_applies`. The tracker does not check the 4-hour close itself today; it relies on the re-plan.
- **Recommendations only in the H4 direction** (`assess.py:376-383`) and only for the approved condition classes (`:391-393`).
- **The engine knows the forming candle.** `Trading.partial` is the 5-minute candle forming now, built from every live price (`trading/engine.py:122, 491-501`).
- **Strategies' watcher copy.** `StrategyRunner` runs a `RejectionWatcher(design_only=True)` (`strategies/replay.py:113`) and gives it `levels.current.build(...)` (`:168, :213`). The analyser has its own copy. A candle reaches a level when its range comes within `near_level_within_pips` (3) of it and touches or passes it (`rejection/watch.py:211-232`).
- **Level Reversal** keeps setups only at the level types in `level_reversal.level_types` (S2, R2, round numbers on the 00s), each with its own allowance past the level (12, 12, 5 pips); stop 6 pips beyond the furthest point; take profit 20 (`strategies/level_reversal/strategy.py:5-23, 55-112`).
- **Order funnel.** All entries go through `Trading._place` (`engine.py:294-314`), then `OrderSender.place` and `safety.rules.decide`. Rule 11 (one signal, one trade; `rules.py:219-226`) counts trades opened, open or closed, and orders sent but not yet settled (`orders/sender.py:452-457`). The hourly bounce, session sweep and New York open reversal already carry `signal_context` (`strategies/common.py:426-433`): a signal key "direction + rejection-candle start" and the rejection candle's start time. **Level Reversal and the 5-minute bounce carry neither** (`level_reversal/strategy.py:110-112`, `bollinger_bounce_5m/strategy.py:50`), and they share the same watcher setups.
- **No trading code reads STP today.** `PLANNER_AUTHORISES_BOUNCE` was never built.

---

## 4. Architecture

```
price service process (existing, unchanged order)
 ├─ every live price ─► engine.on_price → strategies' peek (their watcher copy, levels incl. STP zones*) → _place
 └─ after each 5m candle: levels → analyser → engine.on_candle → _place
                          → planner subprocess (existing):
                               tracker 5m checks for EVERY live opportunity
                               at the H1 close: hourly checks; re-plan; new proposals ADDED (both directions)
                               at the H4 close: structure-break check
                               writes data/planner/GBPUSD/current.json (list of opportunities) + recommendations.jsonl

Trading._place(idea):
   existing entry filters (OD-05 bypasses for gated strategies only*)
   → STP AUTHORISATION CHECK* (gated strategies only; reads current.json + the store + live price; read only)
   → existing day directions → OrderSender.place → safety.decide (rule 11, signal key <id>#t<n>*) → IG DEMO

trade manager, stops, exits: unchanged; never read STP
* only when STP_AUTHORISES_ENTRIES is on
```

- **One writer.** Only the tracker writes STP's files. The authorisation check and the strategies' level copy only read them.
- **Fail closed.** If `current.json` cannot be read, is not current (§9.2), or fails to parse, gated ideas are refused. Ungated strategies are never affected.
- **No leakage.** STP zones never enter the analyser's level list or watcher, so analyser states and the trade manager's close-on-rejection are unchanged.
- **Price basis:** sell (bid) prices, as STP uses today (D-32).

---

## 5. Decision register

### 5.1 Owner decisions in force

| OD | Decision | Status in revision 3 |
|---|---|---|
| OD-01 | Several structurally valid opportunities coexist | Approved (A). Implemented as a list in the tracker. |
| OD-02 | A new forecast does not end a valid opportunity | **Closed** (A): new forecasts do not invalidate existing structurally valid opportunities; H11 overrides ARCH §10.2's "supporting evidence materially changes" trigger. |
| OD-03 | STP authorises the hourly bounce, the 5-minute bounce and Level Reversal, BUY and SELL | Explicitly approved (modified C). Unchanged. |
| OD-04 | Healthy-pullback and corrective-reversal opportunities both authorise | Approved. Unchanged. |
| OD-05 | For the gated strategies STP replaces the conflicting structural and directional filters | Approved (A). Bypass list in §7.2, including RSI stretch (OD-30). |
| OD-06 | H4 direction is context, not a restriction | Explicitly approved (revised). Delivered by the STP bidirectional work package (§11). |
| OD-07 | A failed breakout returns the opportunity to Watch & Wait | Approved (A), with the approved P-F7 = 3 hourly candles (OD-31). |
| OD-08 | Reversal and continuation at significant structural levels | Explicitly approved (modified C). Mechanism per revision 3 (accepted with the revision-3 architecture): continuation is authorised only by STP's own proposal in that direction. Shown on 24 Nov data (§14.2, 12:00 and 19:00). |
| OD-09 | One trade per distinct test | Approved (A). Unchanged. |
| OD-10 | Record tests; no thresholds | Approved (A). Tests are counted for duplicate keys and shown; no threshold. |
| OD-11 | Keep the name Watch & Wait | Approved. Shown as the label for a touched opportunity. |
| OD-12 | Hourly forecasting, live monitoring, strategy confirmation | Explicitly approved (modified B). Mechanism per revision 3 (accepted): the live-price part is done by the authorisation check at the moment of entry (§9.3). |
| OD-13 | Re-validate at the weekly open; no expiry | Approved (A). Unchanged. |
| OD-14 | Record structural monitoring events | Approved (A). Scope per revision 3 (accepted): the tracker's existing events plus status changes and authorisation decisions. |
| OD-15 | Inert `.env` switches: separate investigation; nothing restored or removed here | Approved. Unchanged. |

### 5.2 Decided by the owner's revision-3 clarifications

| OD | Decision |
|---|---|
| OD-22 | **Option A** for both the 5-minute Bollinger bounce and Level Reversal: live STP zones are added to the strategies' level copy so both can operate at STP-authorised zones with their existing price-action confirmation (§8). |
| OD-23 | The hourly Bollinger bounce keeps its hourly-band confirmation; it is not given STP levels. |
| OD-24 | Bidirectional STP forecasting is a mandatory prerequisite for activation (§11). |
| OD-25 | The authorisation check must cover intrabar destination touches, structural invalidation, stale data and duplicate entries, not the current price alone (§9). |

### 5.3 Closed in revision 3.1 (owner, 24 November 2026)

| OD | Approved resolution |
|---|---|
| OD-16 | A: apply the existing structural credibility criteria (D-14, D-16, D-18, D-1) independently in both directions; H4 recorded as context. |
| OD-17 | A: one new opportunity per direction per hourly forecast; existing valid opportunities are retained. |
| OD-26 | A: both STP zone edges and the fixed structural levels within the zone are made available to the applicable strategies. |
| OD-27 | A: Level Reversal may penetrate up to the far edge of the STP zone plus the existing 3-pip tolerance. Stop and take profit unchanged. |
| OD-28 | A: Level Reversal's existing levels are retained alongside STP levels; all gated entries need a matching STP authorisation when enabled. |
| OD-29 | The switches, dependency checks and fail-safe behaviour of §18.3 are approved. |

**Withdrawn with the removed mechanisms:** OD-18 reporting (OD-18 A, "no new exposure rule", stands), OD-19, OD-20 (replaced by OD-29), OD-21.

### 5.4 Closed at design closure (owner, 24 November 2026)

| OD | Approved resolution |
|---|---|
| OD-30 | RSI stretch is bypassed for STP-authorised entries of the three gated strategies only (`rsi_stretch` in `bypass_filters`). Existing behaviour for every other strategy, and for gated ideas while STP authorisation is off. (INV-1) |
| OD-31 | The existing 3-hourly-candle failed-breakout window (P-F7 = 3) is retained; the opportunity returns to Watch & Wait immediately at the qualifying reclaim close. (INV-2) |
| OD-32 | Both the existing strategy signal key and the STP opportunity/test key are kept; an entry is refused if either has been used; protection holds across restarts, unsettled orders and superseded opportunities (§10). |
| OD-33 | Simultaneous BUY and SELL opportunities at the same zone are permitted; the existing strategy confirmation decides which materialises; no additional directional filter. |

**No decision is open.** The design is closed unless the independent review finds a material defect.

---|---|---|
| OD-30 (INV-1) | RSI stretch for STP-authorised ideas of the gated strategies: bypass or retain | **Bypass** (add `rsi_stretch` to `bypass_filters`); retaining it is a valid conservative choice |
| OD-31 (INV-2) | Use the approved P-F7 = 3 hourly candles for the OD-07 failed-breakout return | **Yes** (BROKEN state as §6) |
| OD-32 | Rule 11 key: keep each strategy's existing signal key and add the STP key, both checked (§10) | **Yes**: needed so the hourly bounce's protection is not weakened |
| OD-33 | Acknowledge that when STP proposes both directions at one zone (price inside a Major zone), either direction is authorised there and the strategy's confirmation decides | **Acknowledge** (follows from OD-06 and OD-16; no rule added) |

---|---|---|---|
| OD-16 | What makes an opportunity against the H4 direction credible | A. the same approved criteria as with-H4 (D-14, D-16, D-18, D-1), H4 recorded as context. B. A plus the dual forecaster's evidence score (unapproved numbers). C. new criteria | **A**: no new numbers |
| OD-17 | New proposals per direction per re-plan | A. one per direction (D-16 applied on each side). B. every qualifying zone | **A**: opportunities build up anyway (OD-01, OD-02) |
| OD-26 | How a zone becomes levels in the strategies' copy | A. the zone's two edges plus the fixed levels STP lists inside it. B. edges only. C. a "zone pierce" in the watcher | **A**. B misses a candle that rejects inside a wide zone at its reference level (e.g. the weekly pivot 1.31273). C changes the watcher's confirmation logic, which the owner excluded. |
| OD-27 | Level Reversal's allowance at an STP-zone level (its rule 2 "how far past the level") | A. up to the zone's far edge: past = beyond the far edge by more than `near_level_within_pips`. B. a new allowance number. C. borrow the round-number allowance (5) | **A**: uses STP's own structure and an approved number; B is a new parameter; C has no structural basis. Stop (6 beyond the furthest point) and take profit (20) are unchanged. |
| OD-28 | Level Reversal's own level types (S2, R2, 00) once STP zones are added | A. keep them alongside STP-zone levels (they still need an STP authorisation to trade). B. STP-zone levels only | **A**: no removal of existing behaviour; every gated entry still needs an STP opportunity |
| OD-29 | Switch names and defaults | §18.3 | as listed |

**Withdrawn with the removed mechanisms:** OD-18 reporting (OD-18 A, "no new exposure rule", stays), OD-19, OD-20 (replaced by OD-29), OD-21.

---

## 6. Opportunity lifecycle

### 6.1 States

| State (record value) | Label shown | Meaning | Authorises its direction |
|---|---|---|---|
| WAITING | Waiting | issued; zone not yet reached | yes |
| ACTIVE | **Watch & Wait** | the zone has been reached; no resolution yet | yes |
| BROKEN *(new; OD-31)* | Broken | a confirmed hourly break (D-20); inside the 3-hourly-candle failed-breakout window | **no** (neither direction) |
| COMPLETED | Completed | the primary destination was reached after the zone | no |
| INVALIDATED | Invalidated (with reason) | its own conditions failed: the break held; an H4 structure-break close against it; the destination was reached before the zone (H12); its fixed levels disappeared with no successor | no |
| SUPERSEDED | Superseded | the same identity was reissued with changed structure | no; the successor keeps its history and test count |

WAITING and Watch & Wait both authorise (D-29 A: the rejection candle must interact with the zone, so a WAITING opportunity is only ever used by a candle that reaches it). Every authorisation also needs the §9 checks.

There is no expiry state. No status changes because time passes, a session ends or a week ends.

### 6.2 Transitions

| From | Trigger (existing rule) | Checked | To |
|---|---|---|---|
| – | a proposal whose identity is not live | hourly re-plan | WAITING (added to the list) |
| live | a proposal with the same identity, structure changed | hourly re-plan | old SUPERSEDED, new inherits history and tests (D-22, narrowed) |
| live | the same identity, edges moved by non-fixed levels | hourly re-plan | updated in place ("changed") |
| WAITING | a 5m candle comes within 3 pips of the zone | 5m | ACTIVE (Watch & Wait) |
| WAITING | the primary destination is reached first (D-1, `destination_first_applies`) | 5m, and at the re-plan | INVALIDATED "destination reached before entry" |
| ACTIVE | the primary destination is reached | 5m, re-plan | COMPLETED |
| ACTIVE / WAITING | an hourly close at or beyond `zone_break_close` | H1 close | BROKEN |
| BROKEN | an hourly close back inside the far edge within P-F7 (3) closes (the qualifying reclaim) | H1 close | ACTIVE (Watch & Wait) **immediately at that close**, using the existing `watch_after_break` |
| BROKEN | P-F7 closes pass with no close back inside | H1 close | INVALIDATED "confirmed break held" |
| live | a 4-hour close at or beyond `structure_break_close` | H4 close | INVALIDATED |
| live | the fixed levels disappear at the 00:00 pivot rollover with no successor | 00:00 re-plan | INVALIDATED "structural levels changed" |
| live | **the re-plan chooses another zone, recommends nothing, or the H4 direction or condition changes** | – | **no change** (H11, OD-02, OD-06) |
| ACTIVE | **price moves wholly clear of the zone** | – | **no change** (the current demotion to WAITING is removed) |
| live | **time, session end, weekend** | – | **no change**; re-validated at the weekly open (OD-13) |

Closes beyond by less than 3 pips, reclaims and wick sweeps stay "recorded only" (H09). A failed rejection is not a tracker event at all: the opportunity simply stays in Watch & Wait (H19).

### 6.3 The failed-breakout window (OD-31)

- A confirmed break (D-20) moves the opportunity to BROKEN, which authorises nothing in either direction.
- The first hourly close back inside the far edge within P-F7 = 3 closes restores Watch & Wait at that close: its id, test count and duplicate keys are kept.
- If three closes pass without a reclaim, the opportunity is INVALIDATED "confirmed break held".
- A broken opportunity never authorises the opposite direction. That comes only from an STP proposal in that direction (§7.3).

### 6.4 Diagram

```
 hourly proposal (either direction) ──► WAITING ── destination first ──► INVALIDATED (destination before entry)
                                          │ 5m candle within 3 pips
                                          ▼
                                    WATCH & WAIT (ACTIVE) ── primary destination ──► COMPLETED
                                     ▲    │ hourly close ≥ zone_break_close
           close back inside within  │    ▼
           P-F7 (OD-31)              └─ BROKEN ── P-F7 closes, no reclaim ──► INVALIDATED (break held)
   any live: 4h close ≥ structure_break_close · fixed levels gone ──► INVALIDATED
   same identity reissued ──► SUPERSEDED
   another zone chosen · nothing recommended · H4 change · price leaves zone · time · session · weekend ──► no change
```

---

## 7. Strategy integration matrix

### 7.1 Strategies

"Reversal" in this code means a rejection at a level or band, in either direction. It does not mean "against the trend".

| Strategy | What the code does (unchanged) | After integration |
|---|---|---|
| **Bollinger bounce (hourly)** | a 5m pierce of the *hourly* band by more than 3 pips that closes back, a confirmation close within 3 candles, entry at the next open | **Gated, BUY and SELL.** Keeps its band confirmation (OD-23). Authorised only when its rejection candle interacts with a live opportunity of its direction, so it trades only where the hourly band and an STP zone coincide. |
| **Bollinger bounce 5m** | watcher bounce at a level or the 5m band: pierce, opposite-coloured candle, confirmation close, live trigger | **Gated, BUY and SELL.** Sees STP zone levels (OD-22, OD-26). Analyser-state gating bypassed (OD-05). |
| **Level Reversal** | the same watcher setups as the 5m bounce, kept at S2, R2, 00 with per-type allowances; stop 6 beyond the furthest point; TP 20 | **Gated, BUY and SELL.** Also sees STP zone levels with the OD-27 allowance (OD-22, OD-28). State gating and rule 9 bypassed (OD-05). Stop and take profit unchanged. |
| Range trade | 5m band pierce, opposite candle, break within 1 candle; RANGING only | not gated |
| Session sweep | 3+ pips past the Asian or London high/low, close back inside, confirmation | not gated |
| New York open reversal | 30+ pip move 07:00 to 13:30, then a rejection 13:30 to 15:00 | not gated |
| Slow grind | pause and break on the trend side of the 21 EMA | not gated |
| EMA pullback | hourly EMA stack, 8 EMA touch, entry beyond the last 5 candles; direction rule | **independent** (H15) |
| Breakout | pullback entry after an analyser breakout | not gated |
| Asian range breakout | first close outside the Asian range 07:00 to 10:00, then a pullback | not gated |

### 7.2 Filter conflicts (identified, not added to)

| Existing filter | Conflict with STP | Resolution for the gated three |
|---|---|---|
| Analyser-state gating (`ALLOWED_IN`; 5m bounce and Level Reversal) | a second market-direction judgement; refused the R1-zone sells at 15:40 and 16:35 today | bypassed (OD-05 A) |
| Rule 1 `HOURLY_CONTEXT` | a second hourly structure read | bypassed (OD-05 A) |
| Rule 3 `COUNTER_TREND_TIRING` and variants | a second counter-trend judgement | bypassed (OD-05 A) |
| Safety rule 9 "one view" (Level Reversal) | day direction versus STP direction | bypassed (OD-05 A) |
| RSI stretch (rule 2b) | a momentum filter; RSI 3 is driven under 30 (over 70) by the rejection's own confirmation, so it refused the STP-zone sells at 10:35 and 18:20 | **bypassed for STP-authorised gated ideas (OD-30)**; unchanged for all other strategies |
| Level Reversal's level types | without STP levels it cannot fire at most STP zones | resolved by OD-22 / OD-26 / OD-27 / OD-28 |
| Trading hours, news, rollover pause, 20:30 close, risk, position limits, rules 10 and 11, the direction rule (EMA pullback only) | none | unchanged (rule 11 extended by OD-32) |

Ungated strategies keep every filter. OD-18 A stands: no new rule against an ungated trade opposite an STP opportunity.

### 7.3 Reversal and continuation, in the minimum design

- **Reversal:** a gated strategy confirms a rejection at a live opportunity's zone in that opportunity's direction.
- **Continuation:** after a zone breaks, the only source of an opposite-direction authorisation is STP's own bidirectional proposal at a later re-plan, for example a BUY at the broken resistance now below the price. It is then an ordinary opportunity confirmed by the same strategies, such as a rejection of the retest from above.
- **Never:** an opposite-direction authorisation because a reversal failed, a wick went through, or a close went beyond by less than 3 pips.
- The existing breakout and continuation strategies (breakout, Asian range breakout, slow grind) are not gated and do not fire at STP zones. Gating them would extend OD-03; it is not proposed.

---

## 8. Making STP zones visible to the strategies (Option A)

- **Where.** A small wrapper around `levels.current.build` used only by `StrategyRunner` (both `peek` and `on_candle`). It returns the normal levels plus one level per entry for each live opportunity (WAITING, ACTIVE; not BROKEN or ended), per OD-26:
  - the zone's near edge and far edge;
  - each fixed level STP lists inside the zone (for example the weekly pivot 1.31273 in 1700-23), unless the same price is already a bot level.
- **Level type.** `stp_zone`, carrying the opportunity id. Added to `level_reversal.level_types` (OD-28 A) with the OD-27 allowance rule.
- **Level groups.** The watcher asks the level list for each pierced level's group (`levels/current.py:52`, `rejection/watch.py:246-256`). Each STP zone's levels form one group of their own with `lined_up` false, so the setup's "counts" mark for the trade manager is unchanged by STP levels.
- **The 5-minute bounce** treats an `stp_zone` level like any other level. Its pierce, reversal, confirmation and trigger steps are unchanged.
- **Untouched:** the analyser's level list and watcher, the trade manager, the dashboard's level display, and every other strategy. Range trade and the hourly bounce use bands, not levels.
- **Switch.** Levels are added only while `STP_AUTHORISES_ENTRIES` is on. In Stage A (observe-only) the strategies see exactly today's levels, so trading is unchanged.
- **Read path.** The wrapper reads `current.json` once per candle and on each `peek` only if the file changed (modification time). The engine caches the forming candle's level list per candle (`trading/engine.py:507-508`); that cache is also renewed when the STP file changes, so a zone published at the hourly close is visible to the strategies from the next price, not from the next candle. An unreadable file adds no levels.
- **A level is a place to look, not an authorisation.** Every idea from an `stp_zone` level still goes through the §9 check, which may refuse it (for example a BUY setup at a SELL zone's edge).

---

## 9. The authorisation check

### 9.1 Request
Built in `_place` from the idea: strategy, direction, idea time, entry price, the **rejection candle**, the live bid and offer with their time, and the engine's forming candle (`Trading.partial`).

- **Rejection candle** = the setup's pierce candle: the candle that reached the level or band and rejected (D-29 A). The hourly bounce already passes its start in `context["rejection_candle"]`. The 5-minute bounce and Level Reversal will add the same field from their watcher setup (`st.pierce.start`). This is a context field only: it changes no idea, stop or decision (T-57). The candle's high and low are read from the store by that start time.

### 9.2 Checks (all must pass; any failure refuses)

| # | Check | Covers |
|---|---|---|
| 1 | The strategy is gated. Otherwise the check does not run. | OD-03 |
| 2 | **Fresh data.** The live price is no older than `out_of_date_after_minutes` (10, D-21 b), and `current.json` was written by a tracker step no older than `out_of_date_after_minutes`. A missing, unreadable or older file refuses "STP not current". | stale data (FC-08) |
| 3 | **A live opportunity in the idea's direction** (WAITING or ACTIVE). | H03, H04 |
| 4 | **Interaction.** The rejection candle's range interacts with that zone within 3 pips (`zones.interacts`, D-29 A). The entry itself may be outside the zone. | H05, H08 |
| 5 | **Catch-up over the tracker's lag (§9.3).** None of the opportunity's own invalidation or destination conditions has occurred since the tracker's last step. | intrabar destination, structural invalidation |
| 6 | **Not beyond the zone break.** The entry price is not at or beyond `zone_break_close` (FC-07). | H10 |
| 7 | **Duplicate.** The signal key `<id>#t<n>` is attached; rule 11 then refuses it if already used (§10). `ONE_SIGNAL_ONE_TRADE` must be on, or gated ideas are refused. | H13 |
| 8 | The strategy's own confirmation has happened (implicit: `_place` is reached only after it). | H06, H07 |

### 9.3 Catch-up over the tracker's lag (OD-25)

The tracker runs after each completed 5-minute candle, seconds behind the engine. Between its steps, the check re-applies the tracker's **own** rule functions to the price data it has not yet seen, read-only:

| Data | Rule applied | Refuses if |
|---|---|---|
| every completed 5m candle after the tracker's last step (from the store), the **forming candle's high and low** (`Trading.partial`, built from every live price), and the current tick | the tracker's destination rule: `interacts` with the primary destination zone, with `destination_first_applies` and the AMBIGUOUS creation-candle rule exactly as `five_minute` | the primary destination was touched, including a touch earlier in the current candle that has since reversed |
| every completed hourly candle after the tracker's last hourly step | `zone_break_close` (D-20) | a confirmed break the tracker has not yet recorded |
| every completed 4-hour candle after the tracker's last 4-hour step | `structure_break_close` | a structural invalidation not yet recorded |

- This is the same rule set, called on more data, not a second one (H23). The check never writes: the tracker records the status on its next step.
- Because the forming candle carries every price since the candle opened, a destination touch between ticks inside the current candle is caught. A touch between two prices the service never received cannot be seen; IG's stream is the source of truth.

### 9.4 Choosing and refusing
- **Several matches:** the opportunity whose zone the rejection candle interacted with; if still several, FC-03's tie-break (strongest class, then nearest).
- **Opposite directions live at once:** each authorises only its own direction at its own zone.
- **A refusal** is recorded with `book.decision("STP refused", reasons)`, as other refusals are.
- **With the switch off**, the check does not run and nothing "would-have-authorised" is logged. There is no shadow trading.

---

### 9.5 The hourly publication race (24 Nov 18:00)

**The race.** STP publishes new opportunities a few seconds after the hourly close: the planner subprocess runs after the engine (§3). A strategy trigger in those seconds is checked against the opportunities live *before* publication. On 24 Nov, BUY B1800 (1.31191–1.31286) was published at 18:00:03. The 5m bounce BUY on the R1 retest triggered in the 18:00 candle. The record shows only the trigger candle's start (18:00:00), not the trigger tick, so it is not known whether it came before or after 18:00:03.

**What the existing code does (unchanged):**
- A watcher setup triggers once and then ends (`rejection/watch.py:367-371`).
- The engine tries each strategy, direction and candle once, on both the live and candle-close paths (`trading/engine.py:239-251, 504-512`).
- A refused idea is not retried, queued or sent later.
- This is why the check sits in `_place`, after the engine has recorded the try (`trading/engine.py:510-513`), and not in the strategies' own `allowed()`. An idea blocked inside the strategy is not recorded as tried, so the live path would evaluate it again on every price while the forming candle still shows the trigger. That includes after price has moved back, which would be a stale signal.

**Can the existing strategy reconsider the opportunity?**

| Case | Answer | Why |
|---|---|---|
| The setup **triggered before** publication and was refused ("no STP opportunity") | **No.** The refusal stands. | Its confirmation was consumed at the trigger. Trying it again later would execute a signal from an earlier moment, which the owner excluded. |
| A setup **in progress** at publication (pierce, reversal or confirmation stage) whose trigger comes after publication | **Yes**, at its own trigger, if its rejection candle interacts with the new opportunity's zone | The check runs at the moment of entry against the opportunities live then (§10 binding), so the confirmation is the strategy's own and current |
| A **new** setup after publication at the newly published zone | **Yes**, normally | A fresh confirmation; on 24 Nov the 18:35 5m bounce BUY was authorised by B1800 this way |

**Not added:** delayed execution, queued or pending orders, retries of refused ideas, automatic execution of stale signals, or any timer around the hourly close. The only design change is the binding rule (§10): an opportunity published after the rejection candle may be bound if its zone interacts with that candle. This replaces revision 3.1's "live at the rejection candle's start", which would have refused the in-progress case. The level cache renewal (§8) makes a newly published zone's levels available to setups from the next price.

## 10. Duplicate prevention (H13, OD-09, OD-32)

**The STP key.** An authorised idea is keyed `<root id>#t<n>`:
- **root id** = the first id of the opportunity's identity lineage, so a SUPERSEDED reissue of the same identity keeps the same key;
- **n** = the D-25 test that **contains the rejection candle**, from `zones.count_tests` over the hourly candles before the rejection candle's hour (plus one if the count is armed at that point). It is a function of the rejection candle alone, so the tracker's lag, a later re-plan or a stop-out cannot change it;
- **binding** = among the opportunities live at the moment of the check whose zone the rejection candle interacts with, the **oldest** (earliest lineage root); then FC-03's tie-break. Oldest-first means a newly published opportunity never displaces a binding an existing opportunity already gives, so the key stays stable as forecasts are published (§9.5). An opportunity published after the rejection candle may still be bound (§9.5); the hourly bounce's existing key part covers any re-binding after the first opportunity ends.

**Both keys are checked (OD-32).** The hourly bounce, session sweep and New York open reversal already carry a rule-11 key, "direction + rejection-candle start" (`strategies/common.py:426-433`), which also stops one of them trading a rejection another has already traded. Replacing it with the STP key would lose that cross-strategy protection. So:
- `context["signal"]` = the existing key, unchanged, then `|`, then the STP key (the 5m bounce and Level Reversal have no existing key, so only the STP key);
- `used_signals()` (`orders/sender.py:452-457`) splits each stored key on `|`; rule 11 (`safety/rules.py:219-226`) refuses if **any** part of the idea's key is already used;
- the key is already journaled and restored on restart through the existing `signal` field (`orders/sender.py:215, 430, 547-553`), so no record format changes. Keys without `|` behave exactly as today (T-48).

**What this covers (verified on the code, readiness §4):**
- one candle reaching several levels of a zone → one watcher setup per direction (`rejection/watch.py:198-208`);
- several setups from consecutive candles of one rejection, or the 5m bounce and Level Reversal on one setup → at most one try per strategy, direction and candle (`trading/engine.py:239-251, 504-512`), and then the shared STP key → one trade per test, including while the first order is sent but not settled (`orders/sender.py:552` records it before sending);
- a re-entry on the same test after a stop-out → refused;
- a new test (price leaves the zone and returns, D-25) → one more trade (H19);
- an opposite-direction opportunity at the same zone has its own lineage, so its trades are keyed separately.
- `ONE_SIGNAL_ONE_TRADE` must stay on; if it is off, gated ideas are refused.

---

## 11. Bidirectional STP forecasting: mandatory prerequisite (OD-06, OD-24)

- **Why mandatory.** Without it STP proposes only in the H4 direction, so the gated strategies could never buy during a bearish H4 (or sell in a bullish one), and continuation after a break could never be authorised. The R1 day showed exactly this.
- **Scope (an STP work package, not part of the integration logic):**
  - in `assess.py`, apply D-16 separately to the zones above the price (SELL) and below it (BUY), with the approved reachability (D-14), destinations (D-18, D-19: primary must be a Major zone), invalidation (D-20 and the H4 structure break) and destination-first (D-1);
  - remove the H4-direction and condition gates (`assess.py:376-383, 391-393`) behind `STP_BIDIRECTIONAL`; record the H4 direction, condition and six factors as context with `relation_to_h4` (with / against);
  - zone construction, grading, widths, reachability and the re-plan cadence are unchanged.
- **The dual conditional-scenario forecaster is not the source.** Assessed in revision 2: on 24 Nov it had no BUY scenario with sufficient evidence at any hour, it has no identity, lifecycle or primary destination, and its numbers have no approval record. It stays observe-only.
- **Gate.** `STP_AUTHORISES_ENTRIES` refuses every gated idea ("STP not bidirectional") unless `STP_BIDIRECTIONAL` and `STP_OPPORTUNITIES` are both on. Stage B cannot start until the bidirectional tests (T-01 to T-03, FT-01) have passed and the owner has reviewed their output.

---

## 12. Sessions, rollover, weekly open, restarts

- **No opportunity expires on time** (H16). The tracker runs whenever candles arrive.
- **New entries** keep every existing session rule: 06:00 to 20:30 UK, news windows, the rollover pause and the 20:30 close. No two-hour close.
- **00:00 pivot rollover:** an opportunity whose fixed levels survive carries over; one reissued with the same identity and changed structure is SUPERSEDED; one whose fixed levels are gone with no successor is INVALIDATED.
- **Weekly open:** the first re-plan re-validates every opportunity against its own conditions (OD-13). The catch-up (§9.3) covers the gap candles.
- **Restart:** the tracker reloads `current.json` as today. Until a fresh tracker step has written it, check 2 refuses.
- **Open trades** are never touched by STP status changes (H14).

---

## 13. Technical test specification (offline; IG never contacted)

| Acceptance area | Tests |
|---|---|
| Independent BUY and SELL proposals | T-01 to T-03 |
| Several opportunities; kept across re-plans | T-04 to T-08 |
| Structural invalidation | T-09 to T-15 |
| Watch & Wait, failed rejection, repeated tests | T-16 to T-21 |
| Zones visible to strategies (Option A) | T-22 to T-27 |
| Authorisation, including intrabar, structure, stale data, publication race | T-28 to T-39, T-62 to T-66 |
| Duplicates | T-40 to T-43, T-58 to T-61 |
| Sessions, restarts, rollover | T-44 to T-47 |
| No regression; boundaries | T-48 to T-55, T-57 |
| Complete journey | T-56 |

| ID | Test | Expect |
|---|---|---|
| T-01 | Zone map with qualifying zones above and below the price, switch on | one SELL and one BUY proposal, each with destinations and invalidation |
| T-02 | H4 BEARISH, a qualifying zone below | a BUY proposal, `relation_to_h4 = against` |
| T-03 | `STP_BIDIRECTIONAL` off | proposals identical to today |
| T-04 | Three live SELL opportunities and one BUY | all held in `current.json` |
| T-05 | A BUY at support and a SELL at resistance live | each authorises only its own direction and zone |
| T-06 | A re-plan picks a different zone | the existing one keeps its status; the new one is added |
| T-07 | A re-plan recommends nothing; H4 direction changes; condition changes | no status change; recorded as context |
| T-08 | Same identity, non-fixed edge moved; same identity, structure changed | updated in place; SUPERSEDED with history and test count carried |
| T-09 | Hourly close beyond the far edge by less than 3 pips | "closed beyond" recorded; status unchanged |
| T-10 | Hourly close ≥ `zone_break_close` | BROKEN; refuses both directions |
| T-11 | T-10, then a close back inside at the 1st, 2nd or 3rd hourly close | ACTIVE (Watch & Wait) at that close; id, tests and keys kept |
| T-12 | T-10, three closes pass without return | INVALIDATED "break held" |
| T-13 | 4-hour close ≥ `structure_break_close` | INVALIDATED |
| T-14 | Destination reached before the zone / after the zone | INVALIDATED (destination before entry) / COMPLETED |
| T-15 | 00:00 rollover removes the fixed levels with no successor | INVALIDATED "structural levels changed" |
| T-16 | 5m candle within 3.0 pips of the near edge / 3.1 pips short | ACTIVE / stays WAITING |
| T-17 | ACTIVE; price moves wholly clear for many hours | stays ACTIVE (no demotion) |
| T-18 | A strategy setup at the zone is cancelled or expires (failed rejection) | opportunity unchanged; no opposite authorisation |
| T-19 | Price leaves and returns (D-25) | test count n+1 |
| T-20 | Five failed setups, no break | ACTIVE; tests shown; no threshold applied |
| T-21 | 500 candles inside the zone with no confirmation | no expiry; no order |
| T-22 | Live opportunity; strategies' level copy | contains the edges and the in-zone fixed levels as `stp_zone`; analyser's copy byte-identical to off |
| T-23 | Opportunity BROKEN or ended | its levels removed from the strategies' copy at the next candle |
| T-24 | 5m bounce SELL setup that pierces only the zone's far edge | idea raised; passes to §9 |
| T-25 | Level Reversal at an `stp_zone` level; furthest point inside the zone / beyond the far edge by more than 3 pips | kept / dropped (OD-27); stop and TP unchanged |
| T-26 | Level Reversal at S2 inside no STP zone, switch on | idea raised; refused by §9 (no opportunity) |
| T-27 | `STP_AUTHORISES_ENTRIES` off | strategies' levels identical to today |
| T-28 | Gated strategy confirms; rejection candle interacts; entry outside the zone | authorised |
| T-29 | No matching opportunity / wrong direction | refused |
| T-30 | Rejection candle 3.1 pips short of the zone | refused |
| T-31 | Destination touched by an earlier completed candle the tracker has not processed | refused (catch-up) |
| T-32 | Destination touched earlier in the **forming** candle, price now back | refused (intrabar) |
| T-33 | Destination touched by the current tick | refused |
| T-34 | Destination touch only in the AMBIGUOUS creation candle | treated as the tracker does (not used) |
| T-35 | Hourly close beyond `zone_break_close` not yet processed | refused |
| T-36 | 4-hour close beyond `structure_break_close` not yet processed | refused |
| T-37 | Entry price at or beyond `zone_break_close` | refused |
| T-38 | Live price older than 10 minutes; `current.json` older than 10 minutes; file missing or corrupt | refused "stale" / "STP not current"; status unchanged |
| T-39 | `STP_BIDIRECTIONAL` or `STP_OPPORTUNITIES` off with authorisation on | all gated ideas refused |
| T-40 | 5m bounce and Level Reversal on one setup | one order; the second refused by rule 11 |
| T-41 | Stopped out; same test; new confirmation | refused (`#t1` used) |
| T-42 | New test; new confirmation | authorised `#t2` |
| T-43 | `ONE_SIGNAL_ONE_TRADE` off | gated ideas refused |
| T-44 | 20:30 to 06:00 | no new gated entries (existing hours); tracker continues |
| T-45 | Restart mid-opportunity | reloaded; refused until a fresh tracker step |
| T-46 | 00:00 rollover with surviving / changed fixed levels | carried over / SUPERSEDED |
| T-47 | Weekly open after a gap | re-validated; catch-up covers the gap; no time expiry |
| T-48 | All switches off: a recorded day through engine, sender (stub IG), safety, trade manager | decisions and orders byte-identical to today |
| T-49 | Switches on: analyser states, analyser levels, trade-manager plans and closes | byte-identical to off |
| T-50 | Ungated strategies with switches on | identical decisions |
| T-51 | EMA pullback with switches on | identical decisions |
| T-52 | Gated strategy stop, take profit and size | identical to off for the same idea |
| T-53 | Retained filters (RSI stretch, hours, news, risk, limits, rules 10, 11) still refuse gated ideas | refused as today |
| T-54 | Bypassed filters (state gating, rules 1, 3, 9) apply to ungated strategies | unchanged |
| T-55 | Bound trade's opportunity becomes INVALIDATED, SUPERSEDED or COMPLETED | trade manager unchanged; no close sent |
| T-58 | Hourly bounce authorised; a session sweep with the same direction and rejection-candle start | refused by rule 11 (existing key part), as today |
| T-59 | Same identity superseded between two ideas of one test | same root id; second refused |
| T-60 | One candle reaching three `stp_zone` levels; two consecutive candles reaching two levels; both triggering | one setup per direction for the single candle; at most one order per test |
| T-61 | Keys with and without `|`; restart with a composite key in the journal | parts restored; rule 11 behaviour unchanged for keys without `|` |
| T-62 | A trigger tick before an STP publication, refused "no STP opportunity"; publication 2 s later; later ticks in the same candle | no retry, no queued order, no later send; setup ended |
| T-63 | A setup pierced before publication, triggering after it; rejection candle interacts with the new zone | authorised against the new opportunity |
| T-64 | Same as T-63 with an older opportunity also interacting | bound to the older one (oldest-first); key stable when the newer is published |
| T-65 | STP file changes mid-candle | the strategies' level list renewed at the next price; analyser levels unchanged |
| T-66 | RSI 3 under 30 for an STP-authorised gated SELL; the same for an ungated strategy and for a gated SELL with authorisation off | allowed / refused as today / refused as today (OD-30) |
| T-57 | The rejection-candle context field added to the 5m bounce and Level Reversal | ideas, stops and decisions byte-identical with it present |
| T-56 | Journey: proposal → tracker → strategy level → idea → `_place` → §9 → OrderSender (stub) → open → trade manager → exit by existing rules | each step recorded with opportunity id and signal key |

---

## 14. Functional test specification: 24 November 2026

**Rule:** every expectation is evaluated **as of** its time, using only candles and STP records up to that moment. No future price information is used. [R] = recorded, [E] = expected design behaviour, [C] = constructed. Sell prices, UTC.

### 14.1 Recorded journey [R]

| Time | Observation | Source |
|---|---|---|
| 00:00–08:25 | Range 1.30271–1.30473 | 5m |
| 00:00 | STP SELL 0000-17, zone 1.30750–1.30841; invalidated 08:00 (destination reached first) | STP |
| 08:30 | Bullish breakout: close 1.30478 above the upper band and above the computed M5 EMA100 (1.30386) and EMA200 (1.30436) | 5m |
| 09:00 | STP SELL 0900-18, same zone, invalidation ≥ 1.30871; superseded 10:00 | STP |
| 09:45 | First close above the daily pivot 1.30621 | 5m |
| 10:00 | STP SELL 1000-19 at the pivot, 1.30621–1.30715, invalidation ≥ 1.30745; ACTIVE 10:10 | STP |
| 12:00 | 11:00 hourly close 1.30891: bullish continuation through the pivot zone; 1000-19 invalidated | 1h, STP |
| 13:00 | STP SELL 1300-20, 1.31355–1.31421; destination 1.30854 reached 13:35 | STP |
| 14:00 | **STP SELL 1400-21 at R1, 1.31030–1.31141**: invalidation ≥ 1.31171; intermediate 1.31013; primary 1.30854 | STP |
| 14:05 | High 1.31025, within 3 pips: zone reached (ACTIVE 14:10) | 5m, STP |
| 14:40–14:50 | Overshoot above R1 to 1.31168 (short of 1.31171) | 5m |
| 15:00 | Hourly close 1.31121; STP **superseded 1400-21** with 1500-22 (1.31355–1.31421) while it was still valid | STP |
| 15:30 | Level Reversal BUY opened 1.31142 (buy price) after a dip to 1.31000 | trades |
| 15:40 | Low 1.30984: initial rejection | 5m |
| 15:40, 16:35 | 5m bounce SELL setups at R1 refused by the analyser state | decisions, replay |
| 16:00 | Hourly close 1.31153 (beyond the far edge by 1.2 pips) | 1h |
| 16:15 | High 1.31176 | 5m |
| 17:00 | Hourly close 1.31117. **STP SELL 1700-23 at the weekly pivot, 1.31176–1.31286**: weekly pivot 1.31273; intermediate 1.31141; primary 1.30841; extended 1.30373; hourly invalidation 1.31316; H4 1.31451 | STP |
| 17:05 | High 1.31172: 1700-23 reached (ACTIVE 17:10) | 5m, STP |
| 18:00 | 17:00 hourly close **1.31204** ≥ 1.31171: confirmed break of the R1 zone. 1700-23 updated to 1.31191–1.31286 | 1h, STP |
| 18:00 | 5m bounce BUY at 1.31207 on the R1 retest refused by the analyser state | decisions |
| 18:05–18:20 | Watcher sell setup: pierce 18:05 (high 1.31239), reversal 18:10, confirmation 18:15, trigger 18:20 | replay |
| 18:20:35 | 5m bounce SELL refused by RSI stretch | decisions |
| all day | Dual forecaster: no sufficient BUY scenario | technical.jsonl |

Rejection-watcher events are a code replay, not a live record.

### 14.2 Expected behaviour on the historical data [E]

| As of | Expected |
|---|---|
| 00:00–09:00 | 0000-17 SELL WAITING. **No BUY proposal** (FT-01, computed): price was below the last 4-hour swing low 1.30715, so every support zone was beyond it (D-14 mirrored: UNLIKELY). |
| 08:00 | 0000-17 INVALIDATED (destination before entry) — same as today |
| 10:00 | 1000-19 added; **0900-18 kept** (different zone, H11) |
| 10:00 | **BUY B1000 at 1.30621–1.30715** (the same Major zone as SELL 1000-19; price inside, NEAR both ways); primary 1.30750; COMPLETED at 11:00. The 10:05, 10:50 and 11:00 5m bounce BUY ideas interact with it (authorised by STP; today refused by the analyser state) |
| 12:00 | 11:00 close 1.30891 beyond both pivot-area SELL zones by ≥ 3 pips → both BROKEN. **STP's 12:00 re-plan proposes BUY B1200 at 1.30750–1.30854** — the broken 0000-17/0900-18 resistance, now support — primary 1.31355 (FT-02, computed): continuation authorised only by STP's own proposal. The 12:35, 12:50 and 13:05 5m bounce BUYs interact with it |
| 15:00 | no close back inside at 12:00, 13:00, 14:00 → both INVALIDATED "break held" |
| 13:35 | 1300-20 INVALIDATED (destination before entry) |
| 14:00–14:05 | 1400-21 WAITING → Watch & Wait |
| 14:40–14:50 | overshoot to 1.31168: no status change (H09) |
| 15:00 | **1500-22 added; 1400-21 kept** |
| 14:05 | B1200 COMPLETED: the 14:00 re-plan moved its primary to 1.31030 (same identity, updated in place) and the 14:05 high 1.31025 reached it |
| 14:35–14:45 | Level Reversal BUYs at 1.31059–1.31151: **no live BUY opportunity there → refused by STP** (today refused by RSI stretch) |
| 15:30 | Level Reversal BUY (opened today): the only live BUY is B1500 at 1.30750–1.30854; its rejection candle (low 1.31023) is 17 pips away → **refused by STP** (FT-05, computed) |
| 15:40, 16:35 | the R1 SELL zone levels are in the strategies' copy; a gated SELL confirmed there is **authorised by STP** (`1400-21#t<n>`), still subject to RSI stretch, hours, news and risk. FT-03 records which retained filter, if any, refuses |
| 16:00 | close beyond by 1.2 pips: "closed beyond" recorded; no break |
| 17:00 | close 1.31117: reclaim recorded. 1700-23 added; 1400-21 and 1500-22 kept |
| 17:05 | 1700-23 → Watch & Wait |
| 18:00 | 17:00 close 1.31204 ≥ 1.31171 → 1400-21 BROKEN (window: the 18:00, 19:00 and 20:00 candles' closes). The 5m bounce BUY on the R1 retest triggered in the 18:00 candle (exact tick not stored). It is **refused** if it triggered before B1800 (1.31191–1.31286) was published at 18:00:03 and is **not retried**. It is authorised if it triggered after, since its rejection candle interacts with B1800 (§9.5, FT-R1). The bot does not create one because the reversal failed. The 18:35 BUY interacts with B1800 and is authorised. |
| 19:00 | 18:00 close 1.31132 back below 1.31141 → 1400-21 back to Watch & Wait at that close (OD-31). STP proposes SELL 1900-24 and BUY B1900 both at R1 1.31026–1.31141 (B1900 ends at 19:05, destination 1.31191 reached in the same candle as the zone) |
| 18:20 | 5m bounce SELL from 1700-23: rejection candle (18:10, high 1.31231) interacts; SELL; entry 1.31156 short of 1.31316; destination 1.30841 not touched in any candle or the forming candle; data fresh → **authorised** (`1700-23#t1`); RSI stretch (23.6) bypassed for it (OD-30), so it goes on to the retained checks (hours, news, risk, rule 11) |
| 18:25 | 1400-21 BROKEN or INVALIDATED; 1500-22 WAITING; 1700-23 Watch & Wait; Level Reversal BUY untouched (H14); nothing expired |

**Pass criteria:** no opportunity ends except by its own condition; no order without a gated strategy's own confirmation; no opposite-direction authorisation that STP did not propose; every status change and authorisation decision recorded with its time; no future data used.

### 14.3 Alternative resolutions [C]
Built from the 18:25 state, or 17:00 where noted, by appending synthetic candles and ticks labelled CONSTRUCTED.

| FT | Scenario | Construction | Expected |
|---|---|---|---|
| FT-A1 | Confirmed bearish reversal at R1 (from 17:00) | rejection at R1, confirmation, fall to 1.30854 | one authorised SELL `#tn`; COMPLETED at the destination; exit by existing rules |
| FT-A2 | Confirmed bullish breakout and continuation (from 18:00) | P-F7 closes stay above 1.31171; a constructed map where STP proposes a BUY at R1 with a Major zone above, not reached | 1400-21 INVALIDATED "break held"; the BUY proposal authorises a gated retest BUY; SELLs at R1 refused |
| FT-A2b | Breakout with no STP BUY proposal (historical 18:00) | as recorded | BUY refused |
| FT-A3 | Several unsuccessful rejections | four more cancelled setups at 1700-23, no break | Watch & Wait; tests shown; no entry without confirmation |
| FT-A4 | Temporary sweep, then reversal | wick to 1.31330 (beyond 1.31316), hourly close inside, then confirmation | not invalidated; SELL authorised |
| FT-A4b | Close beyond and back | hourly close 1.31320, next close inside | BROKEN → Watch & Wait at that close (OD-31) |
| FT-A4c | Break held | three hourly closes above 1.31316 | BROKEN → INVALIDATED "break held" at the third close |
| FT-A5 | Reversal just short | rejection candle high 1.31150 / 1.31140 against 1.31176 | authorised / refused |
| FT-A6 | Structural invalidation | 4-hour close ≥ 1.31451 | SELL opportunities INVALIDATED; open trade untouched |
| FT-A7 | Consolidation without confirmation | 60 candles inside 1.31141–1.31239 | Watch & Wait throughout; no expiry; no trade |
| FT-A8 | A newer, higher zone | historical 15:00 and 17:00 proposals | all held; binding by interaction |
| FT-A9 | Several strategies on one opportunity | 5m bounce and Level Reversal on one setup | one trade; second refused (rule 11) |
| FT-A10 | Destination before entry | historical 1300-20; constructed fall to 1.30841 with no entry; constructed intrabar touch of 1.30841 that reverses within the candle, then a SELL idea | INVALIDATED; the intrabar case refused by the catch-up |
| FT-A11 | Open position when the recommendation changes | historical Level Reversal BUY through 17:00 and 18:00; constructed bound SELL then INVALIDATED | no trade-manager change |
| FT-A12 | Session close and rollover | ticks to 20:30 and 00:00 25 Nov | no gated entries after 20:30; at 00:00 carry over, supersede or invalidate per §12 |
| FT-A13 | Stale data mid-interaction | 12-minute tick gap; tracker not run for 12 minutes | refused; resumes on fresh data |
| FT-A14 | Restart mid-test | restart at 16:00 | reloaded; refused until a fresh tracker step; test count kept |
| FT-A15 | EMA pullback independent | the 24 Nov EMA pullback ideas (12:41, 14:38, 17:06) with every STP switch on | decisions identical to the recorded ones |
| FT-A16 | Reuse, no second rule set | 24 Nov with every switch off; then with them on | switches off: orders and decisions byte-identical to the recorded build; switches on: analyser states, analyser levels and trade-manager actions identical |
| FT-A17 | Watch & Wait label | the STP tab and `current.json` at 14:05 and 17:05 | the touched opportunities shown as "Watch & Wait" (OD-11) |
| FT-A18 | RSI stretch bypass (OD-30) | the 10:35 and 18:20 SELLs | authorised by STP and not refused by RSI stretch; the 05:55 SELL still refused (no opportunity); EMA pullback RSI refusals unchanged |

**FT-R1. The hourly publication race (18:00, 24 Nov).** It starts from the recorded state at 17:55 and replays the 18:00 candle as constructed tick streams with the recorded OHLC. B1800 is published at 18:00:03.

| Case | Construction | Expected |
|---|---|---|
| R1-a | the 5m bounce BUY trigger tick at 18:00:01 | refused "no STP opportunity"; no retry on the later ticks of the 18:00 candle; no queued order; nothing sent at 18:05 |
| R1-b | the same trigger tick at 18:00:05 | authorised against B1800 (rejection candle interacts); key `B1800#t1` plus none (5m bounce has no existing key) |
| R1-c | a setup pierced at 17:50, confirmed at 17:55, triggering at 18:00:05 | as R1-b: in-progress setups are considered at their own trigger |
| R1-d | the recorded 18:35 BUY (a new setup) | authorised against B1800 |
| R1-e | B1800's levels | in the strategies' level list from the first price after 18:00:03, not from 18:05 |
| R1-f | in R1-a, the analyser and trade manager | unchanged |

**Functional tests that compute rather than assert.** FT-01, FT-02, FT-05 and FT-07 were computed offline on 24 Nov for revision 3.1 (readiness §3; harness and output in `stp_strategy_integration_20261124/`); the candle-window approximation of interaction is replaced by the exact pierce candle in WP-6. FT-03 (which retained filter, if any, refuses the 15:15, 15:40, 16:35 and 16:50 sells at R1): computed in WP-6. None is tuned.

**Method.** The tracker and planner run over the stored candles (`show --at` for as-of views). Strategy ideas come from the strategy runner with the Option A level copy. `_place`, `OrderSender` and the trade manager run with a stub IG client. Historical tick behaviour is approximated at candle level because ticks are not stored; tick and forming-candle cases use constructed streams. **No profit and loss is evaluated**; the live IG demo remains the judge.

---

## 15. Traceability

### 15.1 H01 to H23

| ID | Design | Reused code | Technical | Functional |
|---|---|---|---|---|
| H01 Hourly forecasts | §4, §11 | re-plan cadence, `assess` | T-01, T-03 | FT-01 |
| H02 Direction, zone, destinations, invalidation | §11, §9 | `Plan` | T-01, T-02 | §14.2 |
| H03 STP sole authority for the gated strategies | §7, §9 | – | T-28, T-29, T-54 | §14.2 15:40 |
| H04 No matching opportunity, no trade | §9.2 (3) | – | T-26, T-29 | FT-A2b |
| H05 Reaching the zone is not a trade | §9.2 (8) | – | T-21 | FT-A7 |
| H06 Strategies keep their confirmation | §7, §8 | strategies unchanged | T-24, T-25, T-52, T-57 | FT-A1 |
| H07 Strategy timeframe, tick level | §9.1, §9.5 | `_live_entries`, `peek` | T-32, T-33, T-62, T-63 | FT-A10, FT-R1 |
| H08 3-pip tolerance | §6.2, §9.2 (4) | `near_level_within_pips` | T-16, T-30 | FT-A5 |
| H09 Overshoot does not invalidate | §6.2 | D-24 | T-09 | FT-A4 |
| H10 Invalidation per STP | §6.2, §9.3 | D-20, plan invalidation | T-10 to T-15, T-35, T-36 | FT-A4b, FT-A6 |
| H11 A newer forecast does not cancel | §6.2 | – | T-06, T-07 | §14.2 10:00, 15:00 |
| H12 Destination before entry | §6.2, §9.3 | D-1 | T-14, T-31 to T-34 | FT-A10 |
| H13 No duplicates | §10 | rule 11 | T-40 to T-43, T-58 to T-61 | FT-A9 |
| H14 Trade manager owns positions | §12 | unchanged | T-55 | FT-A11 |
| H15 EMA pullback independent | §7 | – | T-51 | FT-A15 |
| H16 No time expiry | §6, §12 | D-21 | T-21, T-47 | FT-A7, FT-A12 |
| H17 Every opportunity monitored | §4, §6 | tracker | T-04 | §14.2 |
| H18 Watch & Wait | §6 | tracker ACTIVE | T-16, T-17 | §14.2 14:05, 17:05 |
| H19 Failed rejection not invalid | §6.2 | – | T-18, T-20 | FT-A3 |
| H20 Rejection / test / overshoot / breakout distinct | §6.2 | D-20, D-24, D-25 | T-09, T-10, T-18, T-19 | FT-A4, FT-A4b |
| H21 Both outcomes monitored | §7.3, §11 | – | T-05, T-10 | FT-A1, FT-A2 |
| H22 Continuation needs authorisation and confirmation | §7.3 | STP proposal | T-10, T-29 | FT-A2, FT-A2b |
| H23 Reuse, no duplication | §2, §9.3 | tracker, zones, watcher, rule 11 | T-48, T-49 | FT-A16 |

### 15.2 Decisions

| OD | Where | Tests |
|---|---|---|
| OD-01 | §6 | T-04, T-05 |
| OD-02 | §6.2 | T-06, T-07 |
| OD-03 | §7 | T-28, T-50 |
| OD-04 | §11 | T-01 |
| OD-05 | §7.2 | T-53, T-54, FT-03 |
| OD-06 | §11 | T-02, T-07 |
| OD-07 | §6.3 | T-11, FT-A4b |
| OD-08 | §7.3 | FT-A2, FT-A2b |
| OD-09 | §10 | T-40 to T-42 |
| OD-32 | §10 | T-58 to T-61 |
| OD-10 | §6.2 | T-20 |
| OD-11 | §6.1 | FT-A17 |
| OD-12 | §9.3 | T-31 to T-36 |
| OD-13 | §12 | T-47 |
| OD-14 | §9.4 | T-56 |
| OD-15 | §19 | n/a: separate investigation; nothing in this design changes those switches |
| OD-16, OD-17 | §11 | T-01, T-02 |
| OD-22, OD-26, OD-27, OD-28 | §8 | T-22 to T-27 |
| OD-23 | §7.1 | T-28 |
| OD-24 | §11 | T-39 |
| OD-25 | §9 | T-31 to T-38 |
| OD-30 | §7.2 | T-66, FT-A18 |
| OD-31 | §6.3 | T-10 to T-12, FT-A4b, FT-A4c |
| OD-33 | §7.3 | T-05, §14.2 10:00, 18:00, 19:00 |
| Publication race | §9.5 | T-62 to T-65, FT-R1 |

---

## 16. Amendments

### 16.1 To approved STP items

| Item | Approved | Amendment | Source |
|---|---|---|---|
| D-03 | H4 direction decides the direction | H4 is context; proposals in both directions | OD-06 |
| D-10 | Condition classes gate a recommendation | They describe with-H4 proposals; no gate | OD-06, OD-16 |
| D-16 | One preferred zone in the H4 direction | Applied per direction | OD-17 |
| D-20 | A confirmed break invalidates | BROKEN for up to P-F7 = 3 hourly closes first; invalidates if the break holds | OD-07, OD-31 |
| D-22 A | Supersede on a different zone | Supersede only for the same identity | OD-02 |
| D-23 A | One live recommendation | Several, de-duplicated by identity | OD-01 |
| D-24 A | Failed breakouts recorded only | The failed breakout (P-F7) now restores Watch & Wait | OD-07, OD-31 |
| D-25 A | Tests recorded only | Still not a filter; the test number keys duplicates | OD-09 |
| D-29 A | Hourly bounce; check 7 in `common.allowed` | Three strategies, both directions; the check in `Trading._place`; "rejection candle interacts" unchanged | OD-03 |
| D-33 | `PLANNER_AUTHORISES_BOUNCE` | Three switches (§18.3) | OD-29 |
| D-37 | "Bounce strategies" | Plus Level Reversal; EMA pullback still independent | OD-03 |
| FC-10 | NEUTRAL / TRANSITIONAL invalidates | Context only | OD-06 |
| ARCH §10.2 | Triggers include a direction change and "evidence materially changes" | Both become context; the 4-hour structure-break close is checked explicitly | OD-02, OD-06 |
| ARCH §11.2 | ACTIVE returns to WAITING when price stays clear | Removed | H18 |
| ARCH §13 | Bounce-only authorisation; no effect on other filters | Three strategies; OD-05 and OD-30 bypasses; zones in the strategies' level copy | OD-03, OD-05, OD-22, OD-30 |
| Rule 11 (18 Nov) | One signal key per idea | Composite key (`|`), refused if any part used; unchanged for existing keys | OD-32 |
| Entry filter rule 2b (21 Nov) | RSI stretch for all non-exempt strategies | Bypassed for STP-authorised gated ideas only | OD-30 |

Unchanged: D-01, D-02, D-04 to D-09, D-11 to D-15, D-17 to D-19, D-21, D-26 to D-28, D-30 to D-32, D-34 to D-36 (D-36 cadence unchanged: the lifecycle stays in the tracker), D-38.

### 16.2 To revision-2 decisions (owner confirmation requested)

| Item | Revision 2 | Revision 3 |
|---|---|---|
| OD-02 | H11 overrides "evidence changes" | unchanged; **still needs confirmation** |
| OD-07 | P-F7 used for authorisation | approved (OD-31) |
| OD-08 | continuation hypothesis inside each opportunity | continuation only via STP's own proposal in that direction |
| OD-12 | in-process monitor on every price | tracker after each candle plus the catch-up at entry (§9.3) |
| OD-14 | per-attempt and phase records | existing tracker events, status changes and authorisation decisions |
| OD-18 | dashboard and summary conflict reporting | no reporting; A (no new rule) stands |
| OD-19, OD-21 | continuation timing and merge | withdrawn |
| OD-20 | `STP_OPPORTUNITY_MONITOR`, `STP_BIDIRECTIONAL`, `STP_AUTHORISES_ENTRIES` | OD-29: `STP_OPPORTUNITIES`, `STP_BIDIRECTIONAL`, `STP_AUTHORISES_ENTRIES` |
| Statuses | WAITING, WATCH_AND_WAIT, BREAK_PENDING, CONTINUATION, CANCELLED_DESTINATION_FIRST, … | the tracker's existing statuses plus BROKEN (OD-31); "destination before entry" stays an INVALIDATED reason |

---

## 17. Work packages

| WP | Content | Depends on | Switch |
|---|---|---|---|
| WP-1 | Tracker: list of opportunities in `current.json` (old single-record format read on load); new proposals added; supersede only for the same identity; no invalidation on "evidence changed" or H4 change; no demotion; 4-hour structure-break check; BROKEN via `watch_after_break` (if INV-2 confirmed) | – | `STP_OPPORTUNITIES` |
| WP-2 | STP bidirectional proposals in `assess` | – | `STP_BIDIRECTIONAL` |
| WP-3 | Strategies' level wrapper (OD-26); `stp_zone` in Level Reversal with the OD-27 allowance; rejection-candle context field in the 5m bounce and Level Reversal | WP-1 | `STP_AUTHORISES_ENTRIES` |
| WP-4 | Authorisation check in `_place` with catch-up, freshness, composite signal key (rule 11 split on `|`), OD-05 bypasses, refusal records, prerequisite gate | WP-1 | `STP_AUTHORISES_ENTRIES` |
| WP-5 | STP tab: list of opportunities with status (read only) | WP-1 | – |
| WP-6 | Tests T-01 to T-61 and the FT fixtures, extended with recorded data after 18:25 | all | – |
| WP-7 | Readiness pack: test results, the computed FT outputs, the switches-off byte-identical diff | WP-6 | – |

Order: WP-1 and WP-2 in parallel → WP-3, WP-4 → WP-5 alongside → WP-6 → WP-7. Each on its own branch, pushed, not merged until approved.

---

## 18. Deployment and rollback

### 18.1 Gates
1. Independent review of this closed design, then the owner's implementation approval.
2. WP-1 to WP-6 built, all switches off by default.
3. Offline tests pass, including T-48 (byte-identical with switches off). Owner reviews WP-7.
4. **Stage A**, only with explicit approval: `STP_OPPORTUNITIES=on`, `STP_BIDIRECTIONAL=on`, `STP_AUTHORISES_ENTRIES=off`. STP stays observe-only: its tab and records change, trading does not, and no "would-have" decisions are logged.
5. **Stage B**, only with separate explicit approval (D-33, D-37) and only after the bidirectional output has been reviewed (§11): `STP_AUTHORISES_ENTRIES=on`. Real demo trading on IG DEMO. No shadow or parallel execution.

### 18.2 Mechanics
- Before each stage: tag `pre-stp-integration-<stage>-<date>` and record the `.env` diff.
- Check out the approved commit in `/opt/autobot`. The owner restarts `autobot-prices` (and the dashboard).
- Rollback: set the stage's switch off and the owner restarts (with all off, behaviour equals today, T-48); or check out the tag. `current.json` in the list format is read back as the newest live opportunity when `STP_OPPORTUNITIES` is off.
- Open trades are unaffected by deployment or rollback (H14). Every existing trading and session rule is kept. No two-hour close.

### 18.3 Proposed switches and settings (OD-29; not applied)

| Item | Default |
|---|---|
| `STP_OPPORTUNITIES` | off |
| `STP_BIDIRECTIONAL` | off |
| `STP_AUTHORISES_ENTRIES` (replaces the never-built `PLANNER_AUTHORISES_BOUNCE`; refuses everything unless the other two are on) | off |
| `[stp_authorisation] strategies` | `["bollinger_bounce", "bollinger_bounce_5m", "level_reversal"]` |
| `[stp_authorisation] bypass_filters` | `["analyser_state", "hourly_context", "counter_trend_tiring", "one_view", "rsi_stretch"]` (OD-30) |
| `level_reversal.level_types` | adds `stp_zone` (read only while `STP_AUTHORISES_ENTRIES` is on) |

No new numbers. Reused: `near_level_within_pips` 3, `break_beyond_pips` 3, `failed_breakout_within_candles` 3 (OD-31), `out_of_date_after_minutes` 10, and the strategies' own settings.

---

## 19. Open items and investigations

1. **No decision is open** (§5). INV-1 and INV-2 are complete and decided (OD-30, OD-31).
2. **Two-direction validation: computed** (readiness §3).
3. **The 18:00 trigger tick is not stored**, so FT-R1 uses constructed tick streams for both orderings.
4. **Implementation** awaits the owner's approval after the independent review.
5. **No tick history is stored.** Intrabar behaviour is tested with constructed streams; historical replays are candle-level.
6. **Watcher events are not stored live.** The fixture is a code replay.
7. **The hourly bounce trades only where the hourly band and an STP zone coincide.** This follows from OD-23. It may rarely trade.
8. **Breakout-type strategies are not gated** and do not fire at zones (§7.3). Gating them would extend OD-03.
9. **Conflicting exposure (OD-18 A).** An STP-authorised SELL and an ungated BUY can both be open.
10. **OD-15 inert `.env` switches** (`LEVEL_STOPS` and seven others) go to a separate investigation; nothing restored or removed here.
11. **Fixture extension.** Data after 18:25 now exists (for example STP SELL 1900-24, invalidated 20:00 because its destination was already reached). It will be appended before WP-6 without changing any expectation already written.
