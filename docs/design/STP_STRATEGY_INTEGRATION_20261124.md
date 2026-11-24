# Structural Trade Planner: strategy integration (consolidated design)

**Status:** DESIGN FOR OWNER REVIEW. Nothing here is implemented, deployed or switched on. STP stays observe-only.
**Date:** 24 November 2026
**Code examined:** `/opt/autobot` at 63d9c04, the live build.
**Approved STP spec examined:** `/home/autobot/research/structural_trade_planner_v1/` (ARCHITECTURE_AND_DESIGN, DECISION_REGISTER D-01–D-38, PARAMETER_APPROVAL_REGISTER, IMPLEMENTATION_READINESS FC-01–FC-13).
**Requirements:** H01–H23, approved by the owner. Implementation details and numbers remain subject to approval.
**Fixtures:** `stp_strategy_integration_20261124/`. These are the 24 Nov R1-window candles and the rejection-watcher replay.

---

## 1. Executive summary

- **No new service is needed.**
  - Opportunity monitoring and Watch & Wait become an extension of the STP keeper (`planner/keeper.py`). The keeper already runs after every 5-minute candle inside the planner process that the price service starts.
  - Authorisation becomes one check at the single order funnel, `Trading._place` (`trading/engine.py:294-314`), immediately after the entry filters.
  - Strategies keep their own confirmation rules unchanged. Execution and the trade manager are untouched.
- **Most of the pieces already exist; they are not joined up.**

  | Existing piece | What it already does |
  |---|---|
  | The keeper's lifecycle | Zone touch, the 3-pip tolerance, the hourly close-beyond break, wick-sweep and reclaim records, the failed-breakout watch, destination reached first |
  | `zones.count_tests` | Counts distinct tests of a zone (D-25) |
  | The shared rejection watcher (`rejection/watch.py`) | Pierce → reversal → confirmation → trigger / cancelled |
  | Rule 11 (`safety/rules.py:219-226`) | "One signal, one trade" |

  The design joins them. It adds no indicator, no new number and no clock-time expiry.
- **Four approved STP decisions conflict with H01–H23 and must be reopened by the owner.**
  - **D-22**: a newer forecast supersedes the old one. This conflicts with H11.
  - **D-23**: one live recommendation per instrument. This conflicts with H11 and with several opportunities being valid at once.
  - **D-29 / D-37 scope**: the Bollinger bounce only. This conflicts with H03's "reversal strategies".
  - The **keeper's "no longer recommended → INVALIDATED"** rule (`keeper.py:397-398`). This conflicts with H11.
- **The 24 Nov R1 test exposes those conflicts in today's recorded data.**
  - SELL opportunity STP-GBPUSD-20261124-1400-21 (zone 1.31030–1.31141) was superseded at 15:00.
  - At that point it was still structurally valid. No hourly close reached its invalidation at 1.31171, and its primary destination 1.30854 was never reached.
  - Price then spent more than two hours rejecting, failing, returning to R1 and testing again.
  - Under this design the opportunity stays in WATCH AND WAIT throughout, and is still unresolved at 17:15.
- **Fifteen owner decisions are listed in §15.** The most consequential:
  - **OD-03**: which strategies count as "reversal strategies".
  - **OD-05**: whether STP replaces the existing structural filters for those strategies, or sits on top of them. Today the analyser state blocked four 5-minute bounce sells at R1.
  - **OD-08**: what a continuation trade's "appropriate structural authorisation" is.

---

## 2. Current architecture assessment (verified in code)

### 2.1 Process and data flow

1. On every new 5-minute candle, the price service runs `after_new_candle` (`prices/service.py:262-273`), which does the following in order:
   1. builds the levels;
   2. steps the analyser states;
   3. calls `engine.on_candle` (the trade manager and candle-close entries);
   4. **then** starts the planner as a detached `nice` subprocess (`planner/keeper.py:504-529`).
2. Every tick goes to `engine.on_price` (`service.py:167`). That drives live entries through `runner.peek` and `_place` (`engine.py:504-526`).
3. The planner's output therefore lags the engine by at least one finished candle. A run may also still be in progress when the engine reads.
4. **Nothing in trading reads STP today.** The only references outside `planner/` and `dashboard/` are the launcher and the switch loaders. `PLANNER_AUTHORISES_BOUNCE` does not exist (`planner/README.md:14`).

### 2.2 STP output, lifecycle and persistence

- **Files:** `data/planner/GBPUSD/`.
  - `current.json` holds the live recommendation, the last plan and the FC-08 `current` flag.
  - `recommendations.jsonl` is the event log.
  - `issued.jsonl` holds each recommendation as issued.
  - `technical.json(l)` holds the technical forecaster.
- **Each recommendation** has:
  - an id `STP-GBPUSD-YYYYMMDD-HHMM-N`;
  - trade, entry zone and far edge;
  - intermediate, primary and extended destinations, at each zone's near edge;
  - invalidation: an H1 close ≥ `planner.break_beyond_pips` (3) beyond the far edge, an H4 structure break and destination-first;
  - justification, six factors and history (`keeper.py:193-210`; `assess.py:83-133, 461-486`).
- **Statuses:** WAITING → ACTIVE → INVALIDATED / SUPERSEDED / COMPLETED. LIVE means WAITING or ACTIVE (`keeper.py:69-71`). Identity is the trade plus its sorted fixed levels (`keeper.py:101-105`).
- **At most one live recommendation per pair** (D-23 A).
- **At each hourly re-plan, the current recommendation is:**
  - INVALIDATED if the direction changes (`keeper.py:362-364`);
  - SUPERSEDED if the new plan chooses a different identity or a non-overlapping zone (`:371-378`);
  - INVALIDATED as "supporting evidence changed" if the plan no longer recommends anything (`:397-398`).

  The one exception is the 19 Nov "kept through an unclassified condition" rule (`:379-385`).
- **There is no clock-time expiry in the lifecycle** (D-21). `[stp_technical] validity_hours = 8` exists, but only research code uses it.

### 2.3 Strategies

| Strategy | Type | Confirms on | Gated by analyser state (`common.py:78-93`) | Signal key (rule 11) |
|---|---|---|---|---|
| Bollinger bounce (hourly) | reversal | next 5m open | no ("without hindrance") | yes |
| Bollinger bounce 5m | reversal | live tick, via the rejection watcher | TREND against it; POSSIBLE_REVERSAL | **no** |
| Range trade | reversal (band fade) | live tick, via the watcher's range version | RANGING only | **no** |
| Level reversal | reversal at S2 / R2 / 00 | live tick, via the watcher | all states except CONSOLIDATION | **no** |
| Session sweep | reversal at Asian / London extremes | next open | no | yes |
| New York open reversal | reversal after a 30-pip move | next open | no | yes |
| Slow grind | continuation | live tick | TREND, with the trend | – |
| EMA pullback | continuation | live tick | EMERGING / TREND, with the trend; direction rule | – |
| Breakout | continuation | next open (pullback entry) | EMERGING / TREND, with the trend | – |
| Asian range breakout | continuation | next open | no | – |

All 10 are switched on in the live `.env`.

### 2.4 Existing filters that judge structure

These could duplicate or contradict STP:
- **Analyser state gating** (`ALLOWED_IN`, `common.py:78-93`).
- **Rule 1 `HOURLY_CONTEXT`**: an hourly swing read plus the 50 EMA slope, within 5 pips of the pivot or the 50 EMA (`entry_filters.py:254-278`).
- **Rule 3 `COUNTER_TREND_TIRING`** (+ `_EMERGING`, `_HOURLY_CONFIRMED`; `entry_filters.py:325-383`).
- **Safety rule 9**, "one view" against a strong push or the day's direction (`safety/rules.py:182-206`).
- The level reversal's own level allowances.
- The EMA pullback's hourly stack and the direction rule.

Rule 2b (RSI stretch), trading hours, news and risk limits do not judge structure. Note also:
- **There is no room-to-level check on this build.**
- **`LEVEL_STOPS` and seven other `.env` keys are inert**: they are not in `config/switches.py` (side finding).

### 2.5 Duplicate-trade prevention today

- **Per strategy:** 1 open trade, or 1 each way for the bounce and session strategies (`rules.py:111-142`). The total cap is 5.
- **Per candle:** one try per (strategy, direction, candle).
- **Rule 10 (once a day)** and **rule 11 (one signal, one trade; `sender.py:452-457`)** count signal keys of every trade ever opened, or sent and unsettled.
- **Gap:** the level reversal and the 5-minute bounce read the same watcher setups and carry no signal key. Both can open on one rejection.

### 2.6 NMS and Watch & Wait capabilities

- **On AutoBot 161,** NMS was a library ensemble inside `autobot.service`, not a service (`docs/research/owner_own_words_20261106_20261111.md:137`). Here its replacement is `analyser/`, a five-state machine run in-process by `StatesUpdater`.
- **"Watch and wait" exists today only as a label**, the analyser's CONSOLIDATION ("watch and wait for a directional break", `states.py:131, 209`). On 161, `WATCH_AND_WAIT` meant a *reversal* watch.
- **What exists for watching a zone:**

  | Need | Existing code | Limitation |
  |---|---|---|
  | approach / touch with 3-pip tolerance | `zones.interacts`, `[rejection] near_level_within_pips = 3` | one-sided touch only |
  | in zone / left zone | keeper ACTIVE ↔ WAITING, `zones.wholly_clear` | – |
  | temporary overshoot | keeper "wick sweep", "closed beyond by < 3 pips", "reclaim" (D-24, recorded only) | hourly only |
  | confirmed breakout | keeper: H1 close ≥ 3 pips beyond the far edge → INVALIDATED (D-20) | ends the watch |
  | failed breakout | keeper `watch_after_break`, `planner.failed_breakout_within_candles` | after the fact; recorded only |
  | repeated tests | `zones.count_tests` (D-25 A) | a count only; not tied to rejections |
  | rejection / failed rejection | rejection watcher steps; CANCELLED is in effect a failed rejection | single-price levels, not zones; no memory of failures |
  | conditional reversal and continuation | `technical.py` `conditional_scenarios` | no memory; nothing checks them |

- **Rejection-watcher events are not stored live.** The 24 Nov watcher events in this design are a code replay (`python -m rejection`).

---

## 3. Proposed integration architecture

```
 price service (existing process)
  ├─ levels → analyser → engine.on_candle ──────────────┐
  │                                                     │ reads (no writes)
  └─ planner subprocess (existing, every 5m candle)     │
       ├─ hourly re-plan (assess)          [unchanged]  │
       ├─ OPPORTUNITY REGISTER (keeper, extended)  ───► data/planner/GBPUSD/opportunities.json (+ events in recommendations.jsonl)
       │    lifecycle + WATCH AND WAIT                  │
       │    interaction monitor (zone-aware rejection   │
       │    steps, tests, overshoot, break, reclaim)    │
       └─ technical forecaster              [unchanged] │
                                                        ▼
 engine._place(idea)  ← every live and candle-close entry
   1. entry filters (existing)
   2. STP AUTHORISATION (new check; reversal strategies only; switch, default off)
   3. day directions → OrderSender.place → safety.decide (rule 11 gets the opportunity key) → IG demo
 trade manager: unchanged; never reads STP
```

**Why this shape:**
- The keeper already owns zone interaction, so H23 points here. Adding a monitor elsewhere would create a fourth definition of a "break", alongside the analyser's band close, the keeper's close-beyond and the forecaster's.
- The analyser's own watcher and level list must **not** receive STP zones. Strong-level rejections there start or replace emerging trends, and they drive the trade manager's close on a rejection.
- The zone monitor uses **its own** watcher instance with zone-aware piercing. It reuses the watcher's step rules and the existing candle counts, and leaves the analyser's and the strategies' copies unchanged.
- `_place` is the one funnel every order passes through. It already has the refusal shape (`Result(False, …)` plus `book.decision`).

**Lag (OD-12):** the register reflects the last finished 5-minute candle the planner processed. The check therefore also tests the live price and the strategy's own rejection candle directly (§7.3). It refuses when the register is not current (FC-08: stale data stops authorisation).

---

## 4. Component responsibilities and boundaries

| Component | Responsible for | Must not |
|---|---|---|
| **STP assess (hourly)** | Direction, zones, destinations, invalidation (H01, H02); proposing new opportunities | Confirm entries; cancel other opportunities by choosing a different zone (H11) |
| **Opportunity register (keeper)** | Holding every structurally valid opportunity; its lifecycle; structural invalidation per STP's conditions (H10); destination-first (H12) | Decide entries; read strategy state; close trades |
| **Interaction monitor / Watch & Wait (inside the keeper)** | Recording approach, in-zone, overshoot, rejection attempts, failed rejections, tests, closed-beyond, confirmed break, reclaim, for reversal and continuation alike (H17–H21) | Predict the outcome; authorise a trade from a phase alone (H05) |
| **Authorisation check (`_place`)** | For reversal strategies: refuse unless a matching live opportunity authorises the idea (H03, H04) | Change or replace strategy confirmation (H06, H07) |
| **Strategies** | Their existing confirmation, at their existing timeframe, tick-level where they are now (H06, H07) | Read STP files directly |
| **Execution (`OrderSender`, safety rules)** | Opening trades; rule 11 binds the trade to the opportunity (H13) | – |
| **Trade manager** | Every open position, unchanged (H14) | React to STP status changes |

---

## 5. Opportunity lifecycle and state-transition model

### 5.1 Two layers

1. **Status** is the structural validity and what it permits. It governs authorisation.
2. **Phase** is the Watch & Wait reading of developing price action. It is recorded and shown, but **it never opens a trade on its own** (H05, H21).

### 5.2 Statuses

| Status | Meaning | Reversal entries authorised? |
|---|---|---|
| WAITING | Issued; price has not yet interacted with the zone | yes, if the strategy's rejection candle itself interacts (D-29 A), which covers a reversal just short of the zone |
| **WATCH_AND_WAIT** | Price has interacted with the zone; the outcome is unresolved (H18) | yes, with the same conditions |
| BREAK_PENDING | An hourly close beyond the far edge by at least `break_beyond_pips` (a D-20 confirmed break), still inside the failed-breakout window | **no** (see OD-07) |
| COMPLETED | The primary destination was reached after interaction, or a bound trade exists and the destination was reached | no |
| CANCELLED_DESTINATION_FIRST | The primary destination was reached before any entry (H12; existing D-1 check) | no |
| INVALIDATED | One of STP's own structural conditions failed (H10): a confirmed break not reclaimed within the window; an H4 structure-break close; a change in dominant direction (see OD-06 for NEUTRAL / TRANSITIONAL) | no |
| SUPERSEDED | The **same identity** was reissued with changed structure (D-22 history kept), or its fixed levels no longer exist (pivot rollover; D-21 "relevant structural levels change") | no; the successor takes over |

**Removed (H11):**
- "Superseded because the new plan chose a different zone".
- "Invalidated because the plan no longer recommends it".

A newer forecast adds an opportunity. It does not end an existing one unless that one fails its own structural conditions.

### 5.3 Phases (WATCH AND WAIT detail)

Every definition below is an existing rule or an existing number.

| Phase / event | Definition (reused) | Effect on status |
|---|---|---|
| APPROACHING | A 5m candle within `near_level_within_pips` (3) of the near edge, not yet inside (H08) | WAITING → WATCH_AND_WAIT on the first interaction (`zones.interacts`) |
| IN_ZONE | A 5m close inside the zone | none |
| OVERSHOOT (temporary) | A wick beyond the far edge, or an hourly close beyond by less than `break_beyond_pips` (D-24 "wick sweep" / "closed beyond") | none (H09) |
| REJECTION_ATTEMPT n | The watcher's bounce steps against the zone: pierce = `interacts`, then reversal candle, then confirmation close, then trigger, within the existing `bounce.*_within_candles` counts | none |
| REJECTION_FAILED n | That attempt was CANCELLED (price went past the reversal candle's extreme) or EXPIRED | **none: it stays WATCH_AND_WAIT (H19)**; the failure is counted |
| RETEST n | A new distinct test (D-25 A, `zones.count_tests`) | none; counted |
| STALLING | Recorded when the tests and failed rejections together reach at least 2 with no confirmed break. This describes "repeated testing / possible exhaustion"; it is not a filter | none (see OD-10) |
| RECLAIM | An hourly close back on the entry side after an overshoot (D-24) | none |
| BREAK_CONFIRMED | D-20: an H1 close at least `break_beyond_pips` beyond the far edge | → BREAK_PENDING |
| FAILED_BREAKOUT | Within `planner.failed_breakout_within_candles` hourly candles, a close back inside the zone (D-24) | BREAK_PENDING → WATCH_AND_WAIT (**OD-07**) or → INVALIDATED |
| CONTINUATION_CONFIRMED | The window passes with no reclaim | BREAK_PENDING → INVALIDATED (reversal side); the continuation reading is recorded (H21) |
| LEFT_ZONE | `wholly_clear` | Recorded. Status stays WATCH_AND_WAIT. (Today's keeper ACTIVE → WAITING demotion is replaced: once price has interacted, the opportunity stays watched.) |

The rejection attempts reuse the watcher's existing 3-candle steps, which are counted in candles. They expire **an attempt**, never the opportunity. No clock-time expiry exists anywhere (H16).

### 5.4 Transition diagram

```
            issued (hourly re-plan, new identity)
                       │
                    WAITING ──destination first──► CANCELLED_DESTINATION_FIRST
                       │ interacts (3-pip)
                       ▼
   ┌──────────► WATCH_AND_WAIT ◄───── rejection failed / retest / overshoot / reclaim (loop, counted)
   │            │      │      │
   │  failed    │      │      └─ destination first ─► CANCELLED_DESTINATION_FIRST
   │  breakout  │      └─ H4 structure break / direction change ─► INVALIDATED
   │ (OD-07)    │ H1 close ≥3 pips beyond far edge
   │            ▼
   └──────── BREAK_PENDING ── window passes, no reclaim ─► INVALIDATED (continuation recorded)
 any live status ── same identity reissued / fixed levels gone ─► SUPERSEDED
 WAITING/WATCH_AND_WAIT ── primary destination reached after interaction ─► COMPLETED
```

### 5.5 The cases the brief lists

| Case | Handling |
|---|---|
| Price approaching | WAITING; APPROACHING recorded |
| Reversal just short of the zone | Authorised if the rejection candle comes within 3 pips (H08, D-29 A); otherwise not |
| Enters the zone without reversing | WATCH_AND_WAIT; IN_ZONE; no trade (H05) |
| Repeated tests | RETEST n; STALLING recorded |
| Stalling / exhaustion | Recorded only (OD-10) |
| Initial rejection, then recovery | REJECTION_FAILED; stays WATCH_AND_WAIT (H19) |
| Overshoot / liquidity sweep | OVERSHOOT; not invalidated (H09); a close-beyond-and-back is covered by OD-07 |
| Confirmed reversal | Strategy confirmation + authorisation → trade; status unchanged until the destination is reached |
| Confirmed breakout and continuation | BREAK_PENDING → INVALIDATED; continuation recorded; §9.3 and OD-08 |
| Structural invalidation | INVALIDATED (H10) |
| Destination before entry | CANCELLED_DESTINATION_FIRST (H12) |
| Several valid opportunities at once | Held side by side (OD-01); each with its own id and binding |
| A new hourly forecast with a different zone | Added as a new opportunity; existing ones are kept (H11) |
| Duplicate entry | §8 |
| Session closure / day rollover | §9.4 |

---

## 6. Strategy integration matrix (proposed; scope is OD-03)

| Strategy | Classified | STP authorisation | Notes |
|---|---|---|---|
| Bollinger bounce (hourly) | reversal | **required** | Already approved scope (D-29 / D-37) |
| Bollinger bounce 5m | reversal | **required** | Covered by D-37's "bounce strategies"; needs a signal key (§8) |
| Level reversal | reversal | **required** (OD-03) | The rejection candle must interact with the STP zone; its own S2 / R2 / 00 levels stay as its confirmation; needs a signal key |
| Range trade | reversal / fade | **OD-03** | It fades both ways in a range, while STP authorises only the H4 direction, so about half its trades would be refused |
| Session sweep | reversal | **OD-03** | Owner decision 16 Nov: "without hindrance" |
| New York open reversal | reversal | **OD-03** | Same |
| EMA pullback | continuation | **not gated** (H15) | – |
| Slow grind / breakout / Asian range breakout | continuation | **not gated** at first (OD-08) | §9.3 |

---

## 7. Opportunity authorisation data contract

### 7.1 Record (`opportunities.json`, `opportunities[]`; events appended to `recommendations.jsonl`)

```json
{
  "id": "STP-GBPUSD-20261124-1400-21",
  "instrument": "GBPUSD",
  "direction": "SELL",
  "status": "WATCH_AND_WAIT",
  "status_reason": "...",
  "phase": "REJECTION_FAILED",
  "entry_zone": {"low": 1.31030, "high": 1.31141, "class": "Major", "families": [...], "levels": [{"name":"R1","price":1.31141,"fixed":true}, ...]},
  "near_edge": 1.31030, "far_edge": 1.31141,
  "justification": {"dominant_direction":"BEARISH","condition":"CORRECTION_ACTIVE","opportunity":"corrective reversal","six_factors":{...},"selection_reason":"..."},
  "destinations": {"intermediate":1.31013,"primary":1.30854,"extended":null},
  "invalidation": {"zone_break_close":1.31171,"structure_break_close":1.31451,"destination_first":1.30854,"conditions":["..."]},
  "identity": ["SELL", ["R1 1.31141", "..."]],
  "monitor": {"interacted_at":"...","tests":3,"rejection_attempts":7,"rejections_failed":5,"rejections_triggered":2,
              "max_overshoot":1.31176,"closed_beyond":[...],"reclaims":[...],"break":null,"last_candle":"2026-11-24T17:15Z"},
  "bindings": [{"signal":"STP-GBPUSD-20261124-1400-21#t2","strategy":"...","opened":"..."}],
  "current": true,
  "observe_only": true,
  "history": [...]
}
```

- Prices are sell prices, as everywhere in STP (D-32).
- `observe_only` stays `true` until the switch is approved and on.

### 7.2 Request, from `_place`

`strategy, direction, idea.time, entry price, the rejection candle (high/low, time), live bid/offer`.

### 7.3 Rules: authorised only if ALL of these hold

1. The strategy is in `authorised_strategies` (OD-03). Every other strategy passes straight through, and the check does not apply to it.
2. A live opportunity (WAITING or WATCH_AND_WAIT) exists with the same instrument and direction (H03, H04).
3. The register is `current` (FC-08). Its `last_candle` is the last finished 5m candle or the one before it (OD-12), and the planner's data is not stale.
4. The strategy's rejection candle interacts with that zone under `interacts` with 3 pips (D-29 A, H08). The entry price may be outside the zone.
5. The entry price is not beyond the zone-break invalidation price (FC-07). The live price has not reached the primary destination (H12).
6. No binding blocks it (§8).
7. The strategy's own confirmation has already happened. This is implicit: `_place` is only reached after it (H06).

**When several opportunities match:** choose the one whose zone the rejection candle interacted with. If more than one, choose the nearest by the existing FC-03 tie-break.

**On refusal:** `book.decision("STP refused", reasons)`, recorded like the entry-filter refusals.

---

## 8. Duplicate-trade prevention design (H13)

- **Reuse safety rule 11.**
  - An authorised idea gets `context["signal"] = "<opportunity id>#t<test n>"` before `OrderSender.place`.
  - Rule 11 already refuses a second trade with a used signal key, whether that trade is open, closed or sent and unsettled (`sender.py:452-457`).
  - This covers the 5-minute bounce and the level reversal firing on the same rejection, and it needs no new code path.
- **Choice (OD-09):**
  - **A** `#t<n>`: one trade per distinct test (D-25) of the opportunity. A new attempt after a stop-out needs price to leave and return. This uses an existing definition.
  - **B**: one trade per opportunity, ever.
  - **C**: one at a time.

  **Recommended: A.** It honours H19 without allowing repeated entries on one test.
- The existing per-strategy limits, total cap, rule 10 and per-candle tries are unchanged.
- **Rule 11's switch `ONE_SIGNAL_ONE_TRADE` must be on for this to work.** It is on today.

---

## 9. Watch & Wait integration

### 9.1 Reuse map (H23)

| Need | Reused code | Change |
|---|---|---|
| touch / approach | `planner/zones.py interacts`, `wholly_clear`, `count_tests` | none |
| break / overshoot / reclaim / failed breakout | `keeper.hourly` rules (`break_beyond_pips`, `failed_breakout_within_candles`) | recorded-only notes become phase events; the break goes to BREAK_PENDING instead of straight to INVALIDATED |
| rejection steps | `rejection/watch.py` step logic | allow a **zone** as the pierce target (a predicate or a zone "level"); a new instance owned by the keeper; the analyser's and strategies' copies unchanged |
| reversal / continuation reading | `technical.py` reaction / breakout classifiers | read-only cross-reference shown on the dashboard; **not** a second rule set |
| stale data | FC-08 `current`, `out_of_date_after_minutes = 10` | none |

### 9.2 Naming

The new state is `WATCH_AND_WAIT` on an **opportunity**. It is documented as distinct from:
- the analyser's CONSOLIDATION label ("watch and wait for a directional break");
- 161's reversal `WATCH_AND_WAIT`.

OD-11 asks whether to keep the name.

### 9.3 Continuation (H21, H22)

- **Continuation is monitored on the same opportunity.** The BREAK_PENDING / CONTINUATION_CONFIRMED events record it; nothing is assumed in advance.
- **Under the approved STP rules,** trades are always in the H4 direction and counter-trend was never specified. So STP currently has no basis to *authorise* a continuation through a reversal zone against the H4 direction, such as today's bullish break of a SELL zone under a BEARISH H4.
- **OD-08, options for what H22's "appropriate structural authorisation" means:**
  - **A**: continuation strategies keep their existing structural checks (analyser state, rule 1). STP records the continuation and does not gate or block them. Independent confirmation stays the strategy's.
  - **B**: as A, but while a live reversal opportunity is in WATCH_AND_WAIT, an opposite-direction continuation entry that interacts with the same zone is refused until BREAK_CONFIRMED. This stops simultaneous "both ways" trades at one zone.
  - **C**: STP issues explicit continuation opportunities after CONTINUATION_CONFIRMED (the broken zone becomes the entry). This needs a new STP specification, including counter-H4 rules.

  **Recommended: B for the first build, C researched separately.**

### 9.4 Sessions and rollover

- **Opportunities have no clock expiry (H16).** They are monitored around the clock, because the planner runs on every candle.
- **New entries** still obey the existing trading hours (06:00–20:30 UK; the slow grind's own hours), news windows and the rollover pause. The check adds nothing here.
- **At the 00:00 UK re-plan,** pivots roll over. An opportunity whose fixed levels no longer exist (for example, R1 changes) becomes SUPERSEDED with "structural levels changed" (D-21). An opportunity whose fixed levels survive carries over.
- **The weekly close:** no expiry (D-21 owner modification). At the weekly open, the first re-plan re-validates every opportunity (OD-13).
- **Open trades** close by the existing rules (20:30, Friday). STP status changes never close trades (H14, ARCH §13).

---

## 10. Proposed configuration changes (NOT applied)

| Item | Proposed | Default |
|---|---|---|
| `.env` `STP_AUTHORISES_REVERSALS` | Replaces the never-built `PLANNER_AUTHORISES_BOUNCE`; turns on the §7 check | **off** |
| `.env` `STP_OPPORTUNITY_REGISTER` | The register and Watch & Wait, recorded only; required by the switch above | **off** until approved (it is observe-only, but it changes planner behaviour: supersession) |
| `[stp_authorisation] strategies` | The list for OD-03 | `["bollinger_bounce", "bollinger_bounce_5m"]` (approved D-37 scope) |
| `[stp_authorisation] replaces_filters` | OD-05 | `[]` |
| `[stp_authorisation] signal_per` | OD-09: `"test"` / `"opportunity"` | `"test"` |
| `[stp_authorisation] register_lag_candles` | OD-12 | 1 (proposed; needs approval) |
| Reused, unchanged | `rejection.near_level_within_pips = 3`, `planner.break_beyond_pips = 3`, `planner.failed_breakout_within_candles`, `bounce.*_within_candles`, `out_of_date_after_minutes = 10` | – |

No new indicator, and no clock-time expiry. The only new number is `register_lag_candles`, which is subject to approval.

---

## 11. Technical test specification

All tests are offline (pytest, in `tests/planner/`, `tests/trading/`, `tests/safety/`), and IG is never contacted.

| ID | Test | Expect |
|---|---|---|
| T01 | A new plan with a different identity while opportunity X is live | X keeps its status; a new opportunity Y is added (H11) |
| T02 | A re-plan with no recommendation | Live opportunities keep their status; no "evidence changed" invalidation |
| T03 | The same identity, with an overlapping, changed zone | Updated in place or SUPERSEDED per D-22, with history kept |
| T04 | Direction change BEARISH → BULLISH | SELL opportunities INVALIDATED; the reason is recorded |
| T05 | NEUTRAL / TRANSITIONAL | Per OD-06 |
| T06 | 5m high within 3 pips of the near edge | WAITING → WATCH_AND_WAIT; high 3.1 pips short → stays WAITING |
| T07 | Wick beyond the far edge, hourly close inside | OVERSHOOT; status unchanged |
| T08 | Hourly close beyond the far edge by less than 3 pips | OVERSHOOT (closed beyond); unchanged |
| T09 | Hourly close at least 3 pips beyond | BREAK_PENDING; authorisation refused |
| T10 | T09, then a close back inside within the window | FAILED_BREAKOUT → per OD-07 |
| T11 | T09, with the window passing | INVALIDATED; CONTINUATION_CONFIRMED recorded |
| T12 | Watcher attempt CANCELLED | REJECTION_FAILED n+1; still WATCH_AND_WAIT |
| T13 | Watcher attempt EXPIRED | Same as T12 |
| T14 | Leaves and returns (D-25) | RETEST n+1; the signal key changes to `#t(n+1)` |
| T15 | Primary destination before any interaction or entry | CANCELLED_DESTINATION_FIRST |
| T16 | Destination between price and zone (IMPL note 1) | Destination-first not applied (existing behaviour) |
| T17 | H4 structure-break close | INVALIDATED |
| T18 | 00:00 rollover changes R1 | Opportunity on old R1 → SUPERSEDED, "levels changed" |
| T19 | Stale data / register not current | Authorisation refused, "not current"; status not changed |
| T20 | `_place` with the switch off | Identical to today, checked by decision-log diff on a recorded day |
| T21 | Strategy not in the list | Passes through untouched |
| T22 | Rejection candle interacts, entry outside the zone | Authorised (D-29 A) |
| T23 | Entry beyond the zone-break price | Refused (FC-07) |
| T24 | 5m bounce and level reversal on the same setup | First opens; second refused by rule 11 |
| T25 | Two live SELL opportunities; the rejection touches only the upper one | Bound to the upper one |
| T26 | Opportunity INVALIDATED while a bound trade is open | Trade-manager plan unchanged; no close sent |
| T27 | Analyser watcher and levels | Byte-identical events with the register on and off (no leakage) |
| T28 | Planner subprocess crash or lock held | Register unchanged; authorisation refused as not current; price service unaffected |
| T29 | Restart mid-opportunity | Register reloads from `opportunities.json`; monitor counters preserved |
| T30 | No clock expiry | An opportunity live for over 48h of candles is unchanged by time alone |

---

## 12. Functional test specification: 24 November 2026, R1

### 12.1 Historical observation (recorded data; sell prices, UTC = UK time)

- **Morning range:** 00:00–08:25 between 1.30271 and 1.30473. The breakout came at 08:30, with a close of 1.30478 above the upper Bollinger band and above the computed M5 EMA100 (1.30386) and EMA200 (1.30436).
- **Levels:** pivot 1.30621, R1 1.31141, R2 1.31941. The first close above the pivot was at 09:45, and price held above it from 11:10.
- **STP SELL recommendations** (all with H4 BEARISH):

  | Time | Zone | What happened |
  |---|---|---|
  | 10:00 | 1.30621–1.30715 | Invalidated 12:00 |
  | 13:00 | 1.31355–1.31421 | Destination 1.30854 reached first at 13:35 |
  | **14:00** | **1.31030–1.31141 (R1)** | Invalidation at an H1 close of 1.31171 or more; destinations 1.31013 / 1.30854. ACTIVE at 14:10. A wick sweep was recorded at 15:00. **SUPERSEDED at 15:00** by 1500-22 (1.31355–1.31421). |
  | 17:00 | 1.31176–1.31286 | – |

- **R1 interaction:**
  - 14:05: high 1.31025, within 3 pips.
  - 14:30: first close inside.
  - 14:40–14:50: overshoot to 1.31168.
  - Initial rejection to 1.30984 at 15:40.
  - 15:55: back to R1, close 1.31153.
  - 16:15: day high 1.31176.
  - Lows of 1.31082 (16:30) and 1.31044 (16:50).
  - 17:15: close 1.31117.
- **Hourly closes** of 1.31121 (14:00), 1.31153 (15:00) and 1.31117 (16:00) never reached 1.31171. The primary destination 1.30854 was not reached.
- **The zone was therefore structurally valid all afternoon, but STP had stopped tracking it at 15:00.**
- **Analyser:** emerging up at 14:30, then flipping at R1 at 15:35, 15:55, 16:30 and 17:00.
- **Decisions:** the 5-minute bounce sells at 15:15, 15:40, 16:35 and 16:50 were all refused by the analyser state (emerging).
- **Rejection watcher (replay, not a live record):** sell setups #88 expired, #97 cancelled, **#99 triggered at 15:40**, #101 cancelled, **#102 triggered at 16:35**, #105 cancelled, #107 running at 17:15.

### 12.2 Expected behaviour under this design, for the historical data

| Time | Expected register reading for 1400-21 |
|---|---|
| 14:00 | Issued WAITING |
| 14:05 | → WATCH_AND_WAIT (interacts) |
| 14:30 | IN_ZONE |
| 14:40–14:50 | OVERSHOOT (wick to 1.31168, short of 1.31171); attempt 1 starts |
| 15:00 | Hourly close 1.31121 inside: no break. **1500-22 is added; 1400-21 stays** (H11) |
| 15:05 | Attempt 1 expired → REJECTION_FAILED 1 |
| 15:25 | Attempt 2 cancelled → REJECTION_FAILED 2 |
| 15:40 | Attempt 3 triggered. A qualifying strategy that has confirmed its own entry would be authorised: the 5m bounce's 15:40 idea, if OD-05 removes state gating for authorised strategies; otherwise still refused by the analyser state. Signal key `…-21#t1` |
| 15:55 | Back at R1 → RETEST (if D-25's leave-by-zone-width condition was met; the test asserts the computed answer) |
| 16:00 | Hourly close 1.31153: closed beyond by 1.2 pips → OVERSHOOT (closed beyond), not a break |
| 16:15 | Attempt 4 cancelled |
| 16:35 | Attempt 5 triggered. Authorised only if the binding allows (OD-09 A: a new test; otherwise refused) |
| 17:00 | Hourly close 1.31117 back inside → RECLAIM; attempt 6 cancelled. 1700-23 is added; 1400-21 and 1500-22 stay |
| 17:15 | **WATCH_AND_WAIT, STALLING recorded, unresolved.** No trade was opened merely because R1 was reached |

**Pass criteria:**
- 1400-21 is never INVALIDATED, SUPERSEDED or expired on 24 Nov up to 17:15.
- No authorisation is given without a strategy's own confirmation.
- Every phase event above is present with its timestamp.

### 12.3 Constructed scenarios

Each scenario starts from the historical state at 17:15 and appends synthetic candles, labelled CONSTRUCTED in the fixture.

| # | Scenario | Synthetic continuation | Expected |
|---|---|---|---|
| F1 | Confirmed bearish reversal | Rejection at R1, confirmation close, fall to 1.30854 | Authorised SELL once (bound `#tn`); COMPLETED at the destination; trade managed by existing rules |
| F2 | Bullish breakout and continuation | Hourly close at 1.31171 or above, then no reclaim within the window | BREAK_PENDING → INVALIDATED; no STP-authorised SELL after the break; no STP-authorised BUY (H4 BEARISH); continuation strategies per OD-08 |
| F3 | Multiple unsuccessful rejections | Four more attempts cancel, with no break | WATCH_AND_WAIT; failure count rises; no automatic entry; STALLING |
| F4 | Overshoot / sweep, then reversal | Wick to 1.31200 with the hourly close inside, then confirmation | Not invalidated; authorised SELL. Variant F4b: an hourly close at 1.31175 then a close back inside within the window → per OD-07 |
| F5 | Reversal just short of the zone | Rejection candle high 1.31005 (2.5 pips short) / 1.30995 (3.5 pips short) | Authorised / refused |
| F6 | Structural invalidation | H4 close at 1.31451 or above; separately, the direction changes to BULLISH | INVALIDATED; refusals carry the reason; an open bound trade is untouched |
| F7 | Consolidation without confirmation | 48 candles inside 1.31044–1.31176 with no confirmation | WATCH_AND_WAIT throughout; no expiry; no trade |
| F8 | Newer forecast, higher zone | Historical: 1500-22 at 15:00 and 1700-23 at 17:00 | All live together; a rejection at 1.31286 binds to 1700-23, not 1400-21 |
| F9 | Several strategies confirm the same opportunity | 5m bounce and level reversal on the same setup | One trade; the second refused by rule 11 |
| F10 | Destination before entry | Historical: 1300-20 at 13:35. Constructed: a fall to 1.30854 with no entry | CANCELLED_DESTINATION_FIRST |
| F11 | Open position when the recommendation changes | Historical: the level reversal BUY open from 15:30 while SELL recommendations changed at 17:00. Constructed: a bound SELL open, then 1400-21 INVALIDATED | No trade-manager change; no close |
| F12 | Session close and rollover | Candles to 20:30 and 00:00; 25 Nov pivots from 24 Nov's candle | No new entries after 20:30; at 00:00, R1-based fixed levels → SUPERSEDED if R1 moved; other opportunities carry over; monitoring continues |

**Method:**
- Run the keeper and the register over the stored 5m and 1h candles. `planner show --at` gives the as-of views.
- Pass strategy ideas from the decision log (historical) or from the strategy runner over the constructed candles into a test double of `_place`.
- Compare against the expected tables. No P&L is evaluated: these are behaviour tests only, and the live demo remains the judge.

---

## 13. Implementation and deployment plan (after approval only)

| Stage | Content | Switch |
|---|---|---|
| 1 | Opportunity register in the keeper; H11 supersession rules; several live opportunities; BREAK_PENDING; persistence; dashboard panel. Tests T01–T19, T27–T30, F1–F12 (register side) | `STP_OPPORTUNITY_REGISTER` off |
| 2 | Zone-aware rejection steps (refactor `_pierced` to accept a zone); keeper-owned watcher instance; phase events. Analyser and strategy outputs proven unchanged (T27) | same |
| 3 | `_place` authorisation check; signal keys for the authorised strategies; refusals logged. T20–T26; F-scenarios end to end | `STP_AUTHORISES_REVERSALS` off |
| 4 | Owner review of the offline test results and decisions | – |
| 5 | With explicit approval: switch on and restart, on **IG DEMO, real demo trading** (no shadow, no parallel simulation); rollback tag first; the owner does the restart | on |

Each stage goes on its own branch, is pushed, and is not merged until approved. The existing session rules are preserved, and no automatic two-hour close is added.

---

## 14. Traceability matrix

| ID | Requirement (short) | Design | Existing code reused | Tests |
|---|---|---|---|---|
| H01 | Hourly forecasts | §3, assess unchanged | `planner/assess.py`, keeper re-plan | T01–T03 |
| H02 | Direction, zone, destinations, invalidation | §7.1 | `Plan` fields | T06, T09, T15, T17 |
| H03 | STP sole reversal authority | §6, §7.3, OD-03, OD-05 | – (new check) | T20–T22 |
| H04 | No matching rec → no reversal trade | §7.3 rule 2 | – | T21, F2, F6 |
| H05 | Zone reach ≠ trade | §5.1, §7.3 rule 7 | ARCH §13.1 | F7, §12.2 |
| H06 | Strategies keep confirmation | §4, §7.3 rule 7 | strategies unchanged | T20, F1 |
| H07 | Strategy timeframe incl. tick | §3 (check at `_place`, live and candle-close) | `engine._live_entries` | T22, F1 |
| H08 | 3-pip tolerance | §5.3, §7.3 rule 4 | `near_level_within_pips` | T06, F5 |
| H09 | Overshoot doesn't invalidate | §5.3 OVERSHOOT | D-24 records | T07, T08, F4 |
| H10 | Invalidation per STP | §5.2 | D-20, keeper hourly | T09, T11, T17, F6 |
| H11 | Newer forecast doesn't cancel | §5.2 (removed transitions), OD-01, OD-02 | – (reverses D-22/D-23 in part) | T01, T02, F8 |
| H12 | Destination before entry cancels | §5.2 | keeper D-1 | T15, T16, F10 |
| H13 | No duplicates per opportunity | §8 | rule 11 | T24, F9 |
| H14 | Trade manager controls positions | §4, §9.4 | unchanged | T26, F11 |
| H15 | EMA pullback independent | §6 | – | T21 |
| H16 | No time expiry | §5.3, §9.4 | D-21 | T30, F7, F12 |
| H17 | Every valid opportunity monitored | §5, §9 | keeper 5m step | §12.2, F8 |
| H18 | Explicit WATCH AND WAIT | §5.2, §9.2 | – | §12.2 |
| H19 | Failed rejection ≠ invalid | §5.3 REJECTION_FAILED | watcher CANCELLED/EXPIRED | T12, T13, F3 |
| H20 | Rejection / retest / overshoot / breakout distinct | §5.3 | D-24, D-25, D-20 | T07–T14 |
| H21 | Monitor both outcomes | §5.3, §9.3 | technical classifiers (reference) | F1, F2 |
| H22 | Continuation needs authorisation and confirmation | §9.3, OD-08 | – | F2 |
| H23 | Reuse; no duplicated logic | §9.1, §3 | zones, keeper, watcher, rule 11 | T27 |

---

## 15. Decision register: outstanding owner decisions

### 15.1 Conflicts with approved STP decisions

| # | Approved decision | Conflict | Proposed resolution |
|---|---|---|---|
| C1 | D-22 A: supersede on a different zone | H11 | Supersede only for the same identity or vanished levels; a different zone adds an opportunity (**OD-02**) |
| C2 | D-23 A: one live recommendation per instrument | H11; "multiple simultaneously valid" | Several live opportunities (**OD-01**) |
| C3 | D-29 / D-37: hourly bounce (D-29) / "bounce strategies" (D-37) | H03 "reversal strategies" | Scope set by **OD-03** |
| C4 | Keeper INVALIDATED on "no longer recommended" (ARCH §10.2 trigger 4, "evidence materially changes") | H11 | Re-validate against the opportunity's own structure only (**OD-02**) |
| C5 | ARCH §11.2: entries only while ACTIVE; ACTIVE → WAITING when clear | H17–H19, D-29 A | WAITING and WATCH_AND_WAIT both authorise; no demotion after interaction |
| C6 | D-20: a confirmed break invalidates | H09 / H20 sweep handling | BREAK_PENDING with the existing failed-breakout window (**OD-07**) |
| C7 | 15/16 Nov: bounce and session strategies "without hindrance" | H03 | Settled for the bounce by D-37; session strategies under **OD-03** |
| C8 | D-24 / D-25: recorded only, not filters | H20 | Still not filters: they set phases, and phases never authorise. Only BREAK_PENDING withdraws authorisation, and that is D-20's existing rule |

### 15.2 Open decisions

| OD | Question | Options | Recommended |
|---|---|---|---|
| OD-01 | Several live opportunities | A. unlimited, de-duplicated by identity; B. one per direction; C. one per zone class | A |
| OD-02 | What ends an opportunity at re-plan | A. only its own structural conditions (§5.2); B. as today | A (H11) |
| OD-03 | Which strategies need STP authorisation | Hourly bounce, 5m bounce (D-37); add level reversal, range trade, session sweep, New York open reversal? | Bounces + level reversal first; range and session strategies later, after observation |
| OD-04 | Healthy-trend pullback recommendations (D-16) authorising reversal-type strategies | Yes / no | Yes: the strategy type is the confirmation; the opportunity gives location and direction |
| OD-05 | For authorised strategies, do analyser state gating, rule 1, rule 3 and rule 9 still apply? | A. STP replaces them (sole structural authority); B. STP adds to them | A, behind the same switch; RSI stretch, hours, news and risk stay |
| OD-06 | Does NEUTRAL / TRANSITIONAL at re-plan invalidate (FC-10)? | Invalidate / keep while structure holds | Keep while structure holds, consistent with H11 |
| OD-07 | Failed breakout within the window | A. back to WATCH_AND_WAIT; B. stays INVALIDATED (D-20 as approved) | A, plus approval of `failed_breakout_within_candles` as an authorisation number |
| OD-08 | Continuation authorisation | A / B / C (§9.3) | B now; C researched |
| OD-09 | Binding | per test / per opportunity / one at a time | per test |
| OD-10 | STALLING | recorded only / used | Recorded only; "≥ 2" is a display rule needing approval or removal |
| OD-11 | Name `WATCH_AND_WAIT` | keep / rename (e.g. `MONITORING`) | Keep, documented as distinct |
| OD-12 | Register lag | A. planner subprocess, at most 1 candle behind, with live checks; B. move the 5m monitor step in-process before `engine.on_candle` | A |
| OD-13 | Weekly open | re-validate all / clear all | Re-validate |
| OD-14 | Rejection-watcher events persisted live (today they are not) | Persist zone-monitor events only / also the analyser's | Zone monitor only |
| OD-15 | Inert `.env` keys (LEVEL_STOPS and 7 others) | Remove or wire up (outside this design) | Owner to note: LEVEL_STOPS is not active on the live build |

**Numbers still to approve** before anything authorises trades: the PARAMETER_APPROVAL_REGISTER items already open for D-20, D-21, D-24 and D-29 (P-A3, P-F3, P-F7, P-C2, FC-07), plus `register_lag_candles` (OD-12) and the STALLING display count (OD-10).
