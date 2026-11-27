# Phase 2: STP lifecycle integrity, investigation and design (27 November 2026)

**Status: investigation and design only, for independent review.** Nothing is implemented. No production code, configuration, `.env`, service or record was changed; nothing was deployed or restarted; IG was not contacted. Production baseline: `fadf228` (Phase 1, signed off).

**Scope (owner's brief):** that STP opportunities are created, monitored, updated, invalidated, completed and retired consistently with the approved STP design. STP's forecasting, level selection, direction, entry zones, strategy confirmation, stops, take profits, trade management and the Phase 1 execution-integrity changes are out of scope and are not changed by anything proposed here.

**Approved design used as the requirement:**
- `docs/design/STP_STRATEGY_INTEGRATION_20261124.md` rev 3.2, §6 lifecycle, §9 authorisation (§9.5 publication race), §10 duplicates, §12 restarts. Committed on the design branch (dbcffef); a copy is at `/home/autobot/worktrees/autobot-stp-integration/docs/design/`.
- `/home/autobot/research/structural_trade_planner_v1/DECISION_REGISTER.md` and `PARAMETER_APPROVAL_REGISTER.md` (D-1, D-21, D-22, D-25, P-C8).
- The owner's corrections recorded in `planner/keeper.py`: 18 November 2026, only evidence from after creation counts; 19 November 2026, the duplicate rule.

**Evidence:** copies of the production files taken at 14:15 UTC on 27 Nov: `data/planner/GBPUSD/` (recommendations.jsonl, issued.jsonl, current.json), `data/records/GBPUSD/decisions.jsonl` and `trades.jsonl`, `data/orders/GBPUSD/orders.jsonl`, and the candle store. Prices are IG points (13121.3 = 1.31213) on the sell (bid) side, as STP uses them (D-32). All times are UTC.

**Reproducible audit:** `lifecycle_audit.py` (this folder) re-applies STP's own rule functions (`planner.zones.interacts`, `wholly_clear`, `stp.authorise.which_test`) to the copies. It writes `output/lifecycle_audit.txt` and `output/lifecycle_audit.json`: all 42 opportunities created since 24 Nov, with their events, endings, authorisations, trades, reissues and the D-25 test of every STP-authorised trade.

---

## 1. Summary

| # | Finding | Confirmed | Real trade affected |
|---|---|---|---|
| **L-2** | **An opportunity reissued with the identity of one that has already ended starts a new lineage, so its duplicate key restarts at `#t1`, even when it is the same structural test.** 9 reissues since 24 Nov; in 6 of them the zone was never re-armed between the two. | **Yes** | **Yes: AB261127120127 (27 Nov 12:01 BUY)** traded test 1 of the 13121.3–13131 zone a second time, as `1200-57#t1`. The first trade on that test was AB261127065505 at 06:55, keyed `0300-56#t1`, and rule 11 had refused that key 8 times since (07:47–11:00). The owner closed the 12:01 trade by hand (−1.4 pips). |
| **L-1** | **An opportunity that authorised a trade can still end "destination reached before entry".** This happens when the trade's rejection candle came before the opportunity's creation (allowed by §9.5), because the tracker never counts a touch from before creation as entry. | **Yes** | Records only: **1700-34** (trade AB261125170604, +4.7) and **1200-57** (AB261127120127). Because both ended INVALIDATED instead of COMPLETED, the duplicate rule did not stop their reissue (2100-36 and **1305-58**). |
| **L-3** | **The duplicate rule compares the primary destination by exact price.** On 27 Nov, 0300-56 COMPLETED at 13135.5. One hour later its identity was reissued (1200-57) with a primary of 13134.6, the London session high made while the first destination was being reached. | Yes (a gap between the rule's wording and its stated purpose) | Same trade as L-2 (both had to fail for it to open). |
| **L-5** | **The 12:00–12:15 gap on 27 Nov (deployment) changed a lifecycle outcome.** IG's own price at 12:05:11 (bid 13130.6, the owner's close) was inside 1200-57's zone. The tracker never saw it, so 1200-57 ended "destination reached before entry", not COMPLETED, and 1305-58 was issued at 13:05. The tracker is also "current" across a gap. | Yes | No trade. **1305-58 is live now (Watch & Wait).** |
| L-4 | Several opportunities in the same direction can be live at the same zone at once, each with its own lineage, because one more fixed level makes a different identity. Duplicate protection relies on binding the oldest; if the oldest ends first, the test count restarts. The rollover rule's "with no successor" (§12) is not implemented. | Latent | No: 31 authorisations met parallel lineages; all bound the oldest. |
| L-7 | **A test that began before creation is not counted.** A trade authorised from a pre-creation rejection candle uses `#t1`, and the first test after creation is numbered 1 again, even after a wholly clear re-arm. On 1700-34's zone, the 16:50 rejection and a rejection at 03:05 on 26 Nov (after ten wholly clear hourly candles) both give test 1. | Latent | No (1700-34 ended at 18:20). It would refuse a genuinely new test |
| L-6 | Dashboard wording: the headline card says "ACTIVE (PRICE AT THE ZONE)" where the list says "Watch & Wait" (OD-11). The headline shows the newest live opportunity, while authorisation binds the oldest. | Yes | No (display only). |

**Correct as designed (verified on code and records):**
- the four "destination reached" circumstances are recognised by the tracker and the authorisation check (apart from L-1);
- a rejection candle from before publication may bind only for a setup still in progress (§9.5, approved). Its age is bounded by the strategy's own confirmation limits (at most 9 five-minute candles for the 5-minute bounce), not by a timer;
- one strategy cannot trade the same test twice, and the 5-minute bounce and Level Reversal cannot both trade it (rule 11 refused Level Reversal 21 times as "same signal already traded by Bollinger bounce 5m");
- keys survive a restart, and an unsettled broker submission holds its key;
- a failed breakout and reclaim keeps the id and test count;
- the D-25 re-arms on 26 Nov (#t2, #t3) were genuine new tests (but see L-7 for a test that began before creation);
- Watch & Wait is never demoted, BROKEN authorises nothing, and the tracker, the authorisation check, the strategies' level copy and the dashboard's "authorises" flag all read the same statuses.

**Live exposure the owner should know about now (no action taken: not authorised).**
- 1305-58 is the third issue today of the identity BUY 13121.3–13130.3.
- No hourly candle has been wholly clear of that zone since 03:00, so it is still D-25 test 1, already traded at 06:55 and 12:01.
- While `STP_AUTHORISES_ENTRIES` is on, a gated BUY whose rejection candle reaches this zone would now be keyed `1305-58#t1`, and rule 11 would not refuse it.
- What to do in the meantime is the owner's decision (§11, PD-0).

**Smallest corrections:**
- **C-2 (lineage continuity) fixes L-2 and, on the record, changes exactly one trade: the 12:01 BUY would have been refused.** It changes no other STP-authorised trade since Stage B (§13).
- C-1 makes the record say which of the four circumstances applied, and changes no behaviour.
- The rest (C-3 to C-7) are owner decisions (§11).

---

## 2. Lifecycle state-transition model

### 2.1 States (approved §6.1; implemented in `planner/opportunities.py`)

| State | Label | Authorises (its own direction) | Ends it |
|---|---|---|---|
| WAITING | Waiting | yes (only a rejection candle that reaches the zone, D-29 A) | – |
| ACTIVE | **Watch & Wait** | yes | – |
| BROKEN | Broken | **no** (neither direction) | – |
| COMPLETED | Completed | no | yes |
| INVALIDATED | Invalidated (+ reason) | no | yes |
| SUPERSEDED | Superseded | no (the successor keeps the lineage and the tests) | yes |

The names WATCH AND WAIT and ACTIVE refer to one state: `ACTIVE` is the record value and "Watch & Wait" the label (OD-11).

### 2.2 Transitions: approved, implemented, verified

| # | From | Trigger | Checked | To | Code | Verified |
|---|---|---|---|---|---|---|
| T1 | – | hourly proposal whose identity (trade + fixed levels, FC-05) is not live | H1 re-plan | WAITING (new lineage) | `opportunities.py replan` → `_new_opp` | ✔. But see **L-2**: an identity that has already *ended* also gets a new lineage |
| T2 | live | same identity, zone no longer overlaps | H1 re-plan | old SUPERSEDED; new inherits lineage + tests | `_end(SUPERSEDED)`, `_new_opp(inherit=old)` | ✔ (unit tests; no live case since Stage B) |
| T3 | live | same identity, zones overlap | H1 re-plan | updated in place ("changed"/"supported") | `_update_from` | ✔ (e.g. 0300-56, 6 times on 27 Nov) |
| T4 | WAITING | a 5m candle **after creation** interacts with the zone (3 pips) | 5m | ACTIVE | `Keeper.five_minute` | ✔. A candle running at creation is "ambiguous"; one before it is "in zone at creation". Neither activates (owner, 18 Nov) |
| T5 | WAITING | primary destination reached first (`destination_first_applies`) | 5m, catch-up, re-plan D-1 | INVALIDATED "destination reached before entry" | `five_minute`, `replan` | ✔ for circumstance 2; **L-1** for a zone reached only before creation |
| T6 | ACTIVE (or ever ACTIVE) | primary destination reached | 5m, re-plan | COMPLETED | same | ✔ |
| T7 | WAITING/ACTIVE | hourly close ≥ 3 pips beyond the far edge (= `zone_break_close`) | H1 | BROKEN | `OpportunityKeeper.hourly` | ✔ (0300-56 04:00, 3.5 pips; `zone_break_close` 13118.3 = 13121.3 − 3.0) |
| T8 | BROKEN | hourly close back inside the far edge within P-F7 = 3 closes | H1 | ACTIVE, at that close; id, tests and keys kept | `hourly` | ✔ (0300-56 06:00; 0400-38 12:00) |
| T9 | BROKEN | 3 closes, no reclaim | H1 | INVALIDATED "confirmed break held" | `hourly` | ✔ (0400-38, 1200-42 at 16:00 on 26 Nov) |
| T10 | BROKEN | primary destination reached while BROKEN | 5m | COMPLETED / INVALIDATED (as T5/T6) | `five_minute` (review 25 Nov) | ✔ (code and tests) |
| T11 | any tracked | 4h close at/beyond `structure_break_close` | H4 | INVALIDATED | `four_hour` | ✔ (code and tests; no live case) |
| T12 | any tracked | 00:00 UK re-plan: a daily/weekly fixed level gone | rollover | INVALIDATED "structural levels changed" | `rollover` | ✔ as coded. **Design says "with no successor"; not implemented (L-4)** |
| T13 | live | re-plan chooses another zone, nothing, other H4 direction/condition | – | **no change** | (absent by design) | ✔ |
| T14 | ACTIVE | price wholly clear of the zone | – | **no change** (H18) | `OpportunityKeeper.hourly` has no demotion | ✔ |
| T15 | live | time, session end, weekend | – | **no change** (H16) | – | ✔ |
| R1 | recorded only | closes beyond by < 3 pips, reclaims, wick sweeps | H1 | – | `hourly` | ✔ |
| D1 | (not issued) | the plan's own primary already reached by the latest finished 5m candle | analysis | no opportunity (circumstance 1) | `assess.py` D-1 | ✔ (28 analyses since 24 Nov) |
| DUP | (not issued) | the last ended opportunity of this identity COMPLETED with the same primary price | analysis | no opportunity, "duplicate" recorded once | `_duplicate_of` | ✔ as coded; **L-3** |

### 2.3 Diagram (approved, with the defects marked)

```
 H1 proposal ──(identity not live)──► WAITING ──5m after creation reaches zone──► WATCH & WAIT (ACTIVE)
   │  new lineage  ◄── L-2: also when the identity      │                                 │
   │                   has only just ENDED              │ destination first               │ primary destination
   │                                                    ▼                                 ▼
   │                          INVALIDATED "destination reached before entry"        COMPLETED
   │                          ◄── L-1: also when the zone was reached at/before        │
   │                              creation and a trade was authorised from it           │ L-3: duplicate rule
   │                                                                                     ▼ blocks reissue only on the
   │                    WAITING/ACTIVE ── H1 close ≥3 pips beyond ──► BROKEN             same primary PRICE
   │                         ▲                                         │
   │                         └── H1 close back inside within 3 ────────┘── 3 closes, none back ──► INVALIDATED
   │   any tracked: H4 close beyond structure break · fixed level gone at 00:00 (L-4: "no successor" unchecked) ──► INVALIDATED
   └─ same identity, zone moved away ──► old SUPERSEDED, new keeps lineage + tests
   another zone chosen · nothing recommended · H4 change · price leaves zone · time ──► no change
```

### 2.4 Who reads the state, and whether they agree

| Reader | Live / authorising set | Agrees |
|---|---|---|
| Tracker (`planner/opportunities.py`) | `AUTHORISING = LIVE = (WAITING, ACTIVE)`; BROKEN tracked | – |
| Authorisation (`stp/authorise.py`) | `AUTHORISING = ("WAITING", "ACTIVE")`; catch-up uses the tracker's own before/overlap rule | ✔ |
| Strategies' level copy (`stp/levels.py`) | `("WAITING", "ACTIVE")` | ✔ |
| Dashboard list (`dashboard/stp.py opportunities`) | `authorises = status in (WAITING, ACTIVE)` and Stage B | ✔ |
| Dashboard headline card | `state["recommendation"]` = the **newest** live; label "ACTIVE (PRICE AT THE ZONE)" | wording and choice differ (L-6) |
| Rule 11 (`orders/sender.py used_signals`) | every opened (open or closed) and unsettled trade's key, each `|` part | ✔ (survives restarts) |

---

## 3. A. Destination reached before entry

### 3.1 The four circumstances, as the system treats them

| Circumstance | What should happen (approved) | What happens | Count since 24 Nov |
|---|---|---|---|
| 1 before creation | not issued (D-1, 18 Nov) | not issued | 28 analyses |
| 2 after creation, before any zone interaction | INVALIDATED "destination reached before entry" (H12) | as approved | 6 |
| 3 after a zone interaction, before any trade | COMPLETED if the tracker counted the interaction; the label must be true | COMPLETED when counted (7). **When the zone was reached only at or before creation, INVALIDATED "…without reaching the zone" (5: 1400-31, 1500-32, 1100-40, 0000-50, 0200-54): the words are untrue** | 12 |
| 4 after a valid trade entry | the opportunity was used: its destination was reached after the zone | COMPLETED when the tracker had activated it (1400-44, 0300-56). **INVALIDATED "destination reached before entry" when the trade's rejection candle came before creation (1700-34, 1200-57)** | 4 |

The authorisation check never authorises against an ended opportunity. In every case of circumstances 2 and 3, the catch-up (§9.3) ended authorisation at the destination touch. That part is not affected.

### 3.2 1500-32 (25 Nov): zone reached before creation, destination after; no trade

| Time | Market (sell side) | Lifecycle | Strategy / authorisation |
|---|---|---|---|
| 14:40–14:55 | lows 13046.1, 13046.8, 13050.5, 13050.6: inside the zone 13046.1–13053.7 | (not yet created) | five 5m bounce setups pierce 14:30–14:50 |
| 15:00:03 | – | **created**, WAITING; "in zone at creation" (14:55 candle) | – |
| 15:05 | 15:00 candle reached the zone | "ambiguous" (began before creation): not used | – |
| 15:05:03 | – | – | session sweep BUY opened (ungated; +61.4, the +£614 trade) |
| 15:05:11 | – | – | 5m bounce BUY: the engine tried only the oldest setup (rejection 14:30, low 13058.3, not at the zone): **STP refused**. The setups with rejection candles in the zone (14:40–14:50) were never tried: one try per strategy, direction and candle (§9.5, approved). Observation O-1, outside this phase |
| 15:10 | 15:05 candle reached 13071.5 − 3 | **INVALIDATED "destination reached before entry: … without reaching the zone"** | – |

Verdict: the destination was reached **after a zone interaction that began before creation**, which is circumstance 3, not 2. The status INVALIDATED follows the approved rule (pre-creation evidence never activates), but the stated reason is untrue. **No trade was authorised.** Confirmed records defect, L-1 (records part).

### 3.3 1700-34 (25 Nov): trade authorised from a pre-creation rejection, then "before entry"

| Time | Market | Lifecycle | Strategy / authorisation |
|---|---|---|---|
| 16:50 | low 13085.4, inside the zone 13084.1–13096.0 | – | 5m bounce **pierce** (setup #1161) |
| 16:55 | 13092.1–13104.1 | – | reversal candle |
| 17:00:03 | – | **created** WAITING; "in zone at creation" (16:55 candle) | – |
| 17:00 | 13100.8–13106.9 (not within 3 pips) | – | confirmation close 13106.7 |
| 17:06:04 | – | – | trigger. **STP authorised** "rejection candle 16:50 reached the live BUY opportunity 1700-34 (Waiting)… test 1; key 1700-34#t1". **Trade AB261125170604 opened** at 13108.9 |
| 17:15:21 | – | – | another setup authorised (#t1); refused by the one-per-direction safety rule |
| 17:40 | – | – | trade closed at 13113.6, +4.7 pips |
| 18:00 | – | "changed" (zone 13084.1–13093) | – |
| 18:20 | 18:15 candle reached 13127.3 − 3 | **INVALIDATED "destination reached before entry: … without reaching the zone"** | – |
| 21:00 | (hourly 18:00–20:00 wholly clear: re-armed) | **2100-36 issued: same identity, same primary 13127.3** | nothing authorised (outside hours) |

Verdict: **circumstance 4.**
- The authorisation itself was correct under §9.5: the setup was in progress at publication, and its rejection candle reached the zone.
- The tracker, also correctly under the 18 Nov rule, never counted that interaction. The two approved rules, taken together, leave the record saying the opposite of what happened.
- Consequence: the opportunity was not COMPLETED, so the duplicate rule did not apply and 2100-36 was published. It authorised nothing.
- **Confirmed defect L-1. Real trade: records only; the trade itself was legitimate.**

### 3.4 1200-57 (27 Nov): the same pattern, plus the outage

1200-57 was created at 12:00:03 with "in zone at creation" (the 11:55 candle). The 12:01:27 trade was bound to it from rejection candle 11:40, before creation. Its destination was reached by the 12:15 candle, and it ended INVALIDATED "destination reached before entry" at 12:20. This is circumstance 4 again (L-1). The gap also played a part (L-5, §8).

---

## 4. B. Opportunity identity and reissue

### 4.1 What the code does

- Identity = trade + the zone's fixed levels (FC-05, `planner/keeper.py identity`).
- At each re-plan (`OpportunityKeeper.replan`), a proposal falls into one of three cases:
  - same identity live, zones overlap: updated in place;
  - same identity live, zone moved away: SUPERSEDED, and the successor inherits `lineage` and `tests`;
  - **no live opportunity of that identity: a new one with `lineage = its own id`**, unless the duplicate rule stops it.
- The duplicate key is `<lineage>#t<n>`, where `n` is the D-25 test counted from the lineage's creation (`stp/authorise.py which_test`).
- **A new lineage therefore always starts at test 1**, whatever tests the same identity had already had.

**Approved requirement:** §10, "root id = the first id of the opportunity's **identity lineage**". OD-09, one trade per distinct test. OD-32, "protection holds across restarts, unsettled orders and superseded opportunities". The hourly forecast must not reset the protection (brief, B).

### 4.2 All reissues of an ended identity since 24 Nov (`lifecycle_audit.txt`)

| Predecessor (ending) | Reissue | Gap | Primary | Zone re-armed between (D-25) | Same structural test? | Trades |
|---|---|---|---|---|---|---|
| 0000-17 (INVALIDATED) | 0900-18 | 1.0 h | 13014.2 → 13037.3 | yes | new test | – |
| 1300-20 (INVALIDATED, dest. first) | 1500-22 | 1.4 h | same | yes | new test | – |
| 1900-24 (INVALIDATED) | 2100-25 | 1.0 h | same | **no** | **same** | – |
| 1400-31 (INVALIDATED, dest. first) | **1500-32** | 0.8 h | same | **no** | **same** | – |
| **1500-32** (INVALIDATED, dest. first) | **1600-33** | 0.8 h | same 13071.5 | **no** | **same** | – (1600-33 COMPLETED at 16:30:00; the 16:30:14 bounce found nothing live) |
| **1700-34** (INVALIDATED, dest. first; **had traded**) | **2100-36** | 2.7 h | same 13127.3 | yes (18:00–20:00) | new test | – |
| 0000-50 (INVALIDATED, dest. first) | 0200-53 | 1.8 h | same 13103 | **no** | **same** | – (1 authorisation, outside hours) |
| **0300-56 (COMPLETED; had traded at 06:55)** | **1200-57** | 0.9 h | 13135.5 → **13134.6** | **no** | **same** | **AB261127120127 (12:01)** |
| 1200-57 (INVALIDATED, dest. first; had traded) | **1305-58 (live)** | 0.75 h | same 13134.6 | **no** | **same** | – so far |

Verdicts:
- **1600-33 republished 1500-32.** The identity, zone and primary destination were the same, and the structural test was the same (no wholly-clear hourly candle in between). It was issued as new only because 1500-32 had ended INVALIDATED. It authorised nothing.
- **2100-36 republished 1700-34 after a genuine re-arm.** Under the approved duplicate rule it should not have been issued at all: 1700-34's destination was reached after an authorised entry, so it should have ended COMPLETED (L-1). It authorised nothing.
- **1200-57 and 1305-58 republished 0300-56.** Their test was the same one already traded at 06:55, and 1200-57 traded it again at 12:01.

**Can hourly forecasting reset the lifecycle or the duplicate protection?**
- **Duplicate protection: yes.** It resets whenever an identity ends and is proposed again (L-2).
- **The lifecycle: only through the same mechanism.** A reissue starts as WAITING with `ever_active` false and its own history, and the dashboard shows it as new. Supersession (T2) is unaffected: it keeps lineage and tests as designed.

### 4.3 The 12:01 trade on 27 Nov, test by test

All hourly candles from 03:00 to 13:00 interact with the zone 13121.3–13131.4. None is wholly clear (low > high + 3 or high < low − 3).

| | 06:55 trade AB261127065505 | 12:01 trade AB261127120127 |
|---|---|---|
| Rejection candle | 06:30 (pierce 13122.6 at R1 13121.3) | 11:40 (pierce 13123.8 at R1 13121.3) |
| Bound to | 0300-56 (Watch & Wait) | 1200-57 (Waiting; created 12:00:03) |
| Key issued | `0300-56#t1` | `1200-57#t1` |
| D-25 test under the identity's first lineage (0300-56), recomputed with `which_test` | 1 | **1** |
| Rule 11 | opened | opened. `0300-56#t1` had been refused 6 times, 07:47 to 11:00 |
| Result | −2.0 pips, closed | −1.4 pips, closed by owner (deployment) |

Confirmed defect L-2 (with L-3). The financial result is stated only as recorded. It is not a measure of the correction.

---

## 5. C. Rejection and confirmation chronology

**Approved (§9.5):** a setup that **triggered** before publication and was refused is never reconsidered. A setup **in progress** at publication (pierce, reversal or confirmation stage) may be authorised at its own trigger, if its rejection candle interacts with the new opportunity's zone. "An opportunity published after the rejection candle may be bound."

**Implemented (`stp/authorise.py authorise`):**
- Only opportunities live at the moment of the check are considered.
- The rejection candle must interact with the zone.
- The catch-up skips candles that ended before creation or overlapped it, as the tracker does.
- The engine records the try before the check (`trading/engine.py`), so a refused idea is never retried.

**How old a rejection candle can be:** this is set by the strategies' own confirmation rules, not by a timer.
- 5-minute bounce: reversal within 3 candles of the pierce, confirmation within 3 of the reversal, trigger within 3. At most 9 five-minute candles. Seen live: 16:50 → 17:06; 11:40 → 12:01; 14:55 → 15:35.
- Hourly bounce: confirmation within 3 candles, entry at the next open.

No expiry is needed or proposed.

**Legitimate inherited context vs stale confirmation:**

| Case | Allowed | Evidence |
|---|---|---|
| Pierce before publication, confirmation and trigger after | yes (§9.5) | 17:06 on 25 Nov; 12:01 on 27 Nov |
| Trigger before publication | never (refused once, not retried) | 15:05:11 on 25 Nov; 17:00:04 on 25 Nov ("live: none") |
| **Rejection candle in a structural test already traded under an earlier lineage of the same identity** | **should be refused** (OD-09). **Was allowed** because the new lineage restarts the test count | **12:01 on 27 Nov (L-2)** |
| Rejection candle in an earlier test of the same lineage | keyed to that earlier test (`which_test` is a function of the rejection candle), so refused if used | key numbers recomputed for all 9 trades: all match |

Result: the only stale-context path is L-2. It is closed by C-2, without any expiry period.

---

## 6. D. Duplicate-trade protection

| Situation | Protection | Verdict and evidence |
|---|---|---|
| Several strategies confirm the same test | shared STP key `<lineage>#t<n>`; rule 11 refuses any used part | ✔ Level Reversal refused "same signal already traded by Bollinger bounce 5m", 21 times (26–27 Nov) |
| Same strategy, same test, later setup | same key | ✔ e.g. 0000-37#t2 refused 31 times (bounce and Level Reversal, 12:08–19:57) after the 11:40 trade on 26 Nov; 0300-56#t1 refused 8 times on 27 Nov |
| **Hourly republication of an ended identity** | **none: new lineage → `#t1`** | ✘ **L-2**; real trade 27 Nov 12:01 |
| Hourly publication of a *parallel* lineage (different identity, overlapping zone, same direction) | binding takes the **oldest** live lineage | ✔ while the oldest lives (31 authorisations, all bound oldest). **Latent ✘ if the oldest ends first (L-4)** |
| Supersession | successor inherits lineage + tests | ✔ (code and tests T-58 to T-61; no live supersession since Stage B) |
| Failed breakout and reclaim | id, tests, keys kept (OD-31) | ✔ 0400-38: #t1 06:30; BROKEN; reclaimed 12:00; #t2 12:51 after the 10:00 re-arm (wholly clear, 13106.1–13114.3), so a genuine new test |
| Service restart | keys in `orders.jsonl`, rebuilt by `_read_record` (closed trades kept); tracker state in `current.json` | ✔ 27 Nov 12:13 restart: no re-trigger; `1200-57#t1` held. Check 2 refuses until a fresh tracker step |
| Unresolved broker submission | `used_signals()` includes `unresolved` (Phase 1) | ✔ (code; Phase 1 tests). No gated order was unresolved |
| Previously COMPLETED opportunity | duplicate rule: same identity + **same primary price** | ✔ when the price is identical; **✘ when a moving level shifts it (L-3)** |
| Genuinely new, independently confirmed test | D-25 re-arm → `#t(n+1)` | ✔ 0000-37 #t2 (+14.0, 26 Nov 11:40) and #t3; 0400-38 #t2. **Latent ✘ after a test that began before creation (L-7)**: the first test after creation is numbered 1 again, so it would be refused. Kept and repaired by C-2 |

---

## 7. E. Lifecycle state consistency

Each transition is verified in §2.2. Differences from the approved design:

1. **L-1.** For the ending, "entered" means only "activated by the tracker after creation". For authorisation it means "a rejection candle reached the zone, including before creation" (§9.5). The two definitions disagree in circumstance 4.
2. **L-2.** Lineage is defined by supersession only, not by identity (§10 says "identity lineage").
3. **L-4, rollover.** §12 says an opportunity whose fixed levels are gone "with no successor" is INVALIDATED. `rollover()` invalidates before the new plans are matched. A successor can never share the identity (its daily levels differ), so it always starts a new lineage. Example: 2100-36 was invalidated at 00:00 on 26 Nov and 0000-37 issued at 00:00. Their zones touched at 13093, and no trade was affected.
4. **L-6.** The dashboard headline vs the list (§2.4).
5. **Consistent:** the status sets used by the tracker, authorisation, levels and the dashboard list; the before/overlap creation rule in the tracker and the catch-up; BROKEN authorising nothing; no demotion; no time expiry.

Observations (no change proposed):
- **O-2.** The D-25 option text speaks of leaving "by at least the zone's width". The approved parameter **P-C8** fixes the re-arm at "wholly clear by more than 3 pips", and the code follows P-C8.
- **O-3.** The hourly candle in which an opportunity is created is not counted by `_count_test` (it began a few seconds before creation). On its own this is harmless, because `which_test` arms the first test implicitly. Together with L-7, it can hide a re-arm, so C-2 counts it.
- **O-5.** The rejection candle is checked against the zone's *current* edges. A zone "changed" in place can differ slightly from its edges at the rejection candle. This is as designed (§9.2: "that zone").

---

## 8. F. Missing market data, 27 Nov 12:00–12:15 (reported separately)

**Facts (`data/candles/GBPUSD/gaps.csv`, `logs/prices.log`):**
- The 5-minute candles 12:00, 12:05 and 12:10 are missing. They were recorded as a gap at 12:13:52 and 12:20:00, and not filled.
- The 1h 12:00 candle was built at **13:05** from 9 of 12 parts (its stored open is the 12:15 open). The 4h 12:00–16:00 candle will be built from 45 of 48.
- No candle was fabricated, and nothing here proposes one.

| Effect | Evidence | Integrity impact |
|---|---|---|
| **The tracker never evaluated 12:00–12:10.** STP uses sell (bid) prices. IG's records: the 12:01:27 entry, bid 13130.5; **the owner's close at 12:05:11, IG level 13130.6 (bid)**. Both are inside 1200-57's zone tolerance (13121.3–13130.3, + 3 pips) | journal "closed by owner", IG activity | Had the 12:05 candle been stored, 1200-57 would have been activated at 12:10 by the tracker's own rule, and the 12:15 destination touch would have made it **COMPLETED**. It ended INVALIDATED "destination reached before entry". So the duplicate rule (same identity + same primary 13134.6) **did not stop 1305-58** at 13:05. **Confirmed (L-5).** |
| **Gap-blind "current".** `freshness()` judges only the age of the newest 5m and 1h candles. From 12:20 the tracker was "current" although it had not seen 12:00–12:10. The authorisation catch-up reads only stored candles, so a destination touch inside a gap is invisible to both. | `planner/measure.py freshness`; `stp/authorise.py _catch_up` | Fail-open for gap content. This contradicts D-21 (approved): "stale or unavailable data stops new trade authorisation". No trade was authorised from an opportunity spanning the gap. |
| **Hourly re-plan delayed 5 minutes.** An incomplete hour is built only once a later 5m candle is stored or 300 s have passed (`prices/builder.py`). So the 13:00 re-plan ran at 13:05:03, and the tracker was "not current" from 13:00 to 13:05. | prices.log 13:05:00; decisions 13:05:04 | **Fail-closed, as designed.** One gated idea refused, "STP not current" (5m bounce SELL, 13:05:04). Not a defect. |
| **Indicators.** The analyser, strategies and STP compute over the last N *stored* candles, so the gap is bridged as if contiguous. For example, the 5m Bollinger 20 spans about 15 minutes more until about 13:55, and the hourly candle's open is the 12:15 open. | code reading | Not quantified (it would need the missing prices). IG's two prices inside the gap lie within the stored 1h range (13127.6–13134.7), so nothing contradicts the stored high and low. |

**Approved remedy available (no fabrication):** the store's existing gap fill from IG's own history. It fills only recorded gaps, never overwrites, and rebuilds the incomplete 1h/4h candles under the standing rebuild rule, archiving the old ones. It needs the owner's go-ahead. The read-only plan was run for this report (it contacts nobody):

```
.venv/bin/python -m prices.history_fill gap-plan --pair GBPUSD --from 2026-11-27T11:55:00Z --to 2026-11-27T12:20:00Z
  Fri 27 Nov 12:00 GMT to Fri 27 Nov 12:10 GMT: 3 candle(s) (12:00, 12:05, 12:10)
  Requests: 1, points: 3. Bot's weekly budget 7000, used in the last 7 days 0. IG remaining (last reported) 4157 of 10000.
```

A fill corrects the candles and the indicators from then on. **It does not correct the lifecycle:** the tracker has already moved past those candles and will not re-check them (C-6).

---

## 9. Confirmed defect register

| ID | Approved requirement | Implemented behaviour | Source | Market and journal evidence | Confirmed | Real trade | Smallest correction |
|---|---|---|---|---|---|---|---|
| **L-1** | §6.1 / H12: INVALIDATED "destination reached before entry" means the destination came **before the zone**. §9.5: an opportunity published after the rejection candle may be bound. Owner 18 Nov: pre-creation price never *activates* | `ever_active` only from a post-creation 5m touch; ending text "without reaching the zone" whenever `ever_active` is false | `planner/keeper.py:283-304` (`five_minute`), `:386-396`; `planner/opportunities.py replan` D-1 branch | 1700-34 (§3.3), 1200-57 (§3.4); 5 non-trade cases with an untrue reason (§3.1) | Yes | Records of AB261125170604 and AB261127120127; the duplicate rule bypassed for 2100-36 and 1305-58 | C-1 (true reason, no behaviour change); C-5 (owner: how circumstance 4 ends) |
| **L-2** | §10: root id = first id of the **identity lineage**; OD-09; OD-32 | Lineage inherited only on supersession; a reissue after any ending starts `lineage = id`, so `#t1` | `planner/opportunities.py _new_opp`, `replan` (else branch); `stp/authorise.py which_test` (`since = lineage_created_utc`) | §4.2 (9 reissues, 6 same test), §4.3 | Yes | **AB261127120127** | **C-2** |
| **L-3** | 19 Nov duplicate rule: no reissue after COMPLETED with the same identity and primary, "that destination was already achieved" | Exact price equality `_d(primary) == _d(le["primary"])` | `planner/opportunities.py _duplicate_of`; `planner/keeper.py:183-191` | 0300-56 13135.5 → 1200-57 13134.6 (London session high made at 11:05 while reaching 13135.5) | Yes (purpose not met; the wording is met) | Contributed to AB261127120127 | C-3 (owner, PD-2) |
| **L-4** | §10 binding oldest-first; §12 rollover "with no successor"; OD-09 | Parallel lineages per identity; rollover invalidates before successors are matched | `planner/opportunities.py replan`, `rollover` | 26 Nov: 0000-37 with 1000-39, 1100-41, 1200-43 and 1500-45 at 13093–13103; 0400-38 with 1200-42 | Latent | None | C-4 (owner, PD-3) |
| **L-5** | D-21: "stale or unavailable data stops new trade authorisation"; FC-08 | `current` from candle age only; missing 5m candles never checked; catch-up reads the store only | `planner/measure.py freshness`; `planner/opportunities.py run`; `stp/authorise.py _catch_up` | §8: 1200-57's zone reached at 12:05:11 (IG); 1305-58 issued | Yes | None (1305-58 live, no trade yet) | C-6 (owner, PD-5); OP-1 gap fill |
| **L-7** | D-25 / P-C8: a new test after a wholly clear hourly candle; §10 "n = the D-25 test that contains the rejection candle"; OD-09 | `_count_test` and `which_test` count only hourly candles that start after the lineage's creation. A rejection candle before creation is test 1 by default, and the test it belongs to is never recorded, so the first test after creation is numbered 1 too | `planner/opportunities.py _count_test` (`c.start < since`); `stp/authorise.py which_test` (`return n + 1 if armed else max(n, 1)`) | 1700-34 zone: 16:50 → 1; 26 Nov 03:05 → 1 after the 17:00–02:00 hours were all wholly clear (recomputed with `which_test`) | Latent | None. It would refuse a genuinely new test | C-2 seeding (below) |
| L-6 | OD-11 label Watch & Wait; §10 oldest binds | Headline "ACTIVE (PRICE AT THE ZONE)"; headline = newest | `dashboard/stp.py:68, 494-509` | dashboard API | Yes (cosmetic) | None | C-7 (owner, PD-6) |

---

## 10. Proposed minimal corrections (design only)

None of these changes STP's forecasting, level selection, direction, zones, destinations, invalidation levels, strategy confirmation, stops, take profits, trade management or Phase 1. There is no expiry, no directional restriction and no time-based closure.

### C-1: record which circumstance ended the opportunity (no behaviour change)
- **Where:**
  - `planner/keeper.py five_minute` and the D-1 branch of `replan`;
  - `planner/opportunities.py replan` D-1 branch;
  - `stp/authorise.py _catch_up` wording only.
- **What:** each ending at the primary destination records `destination_case`:
  - `before_zone`: no interaction at all; the text stays "destination reached before entry";
  - `after_zone_at_or_before_creation`: the tracker recorded "in zone at creation" or "ambiguous … reached the zone". The new text: "price reached the primary destination after reaching the zone at or before the opportunity's creation (not an activation, owner 18 Nov 2026)";
  - `after_zone`: the existing COMPLETED.
- **Status unchanged:** INVALIDATED stays INVALIDATED. The new text replaces the untrue "without reaching the zone".
- **Consequences:** no decision changes. Dashboard history text changes for future endings; old records are untouched (append-only).

### C-2: identity lineage continuity (fixes L-2; duplicate keys only)
- **Where:** `planner/opportunities.py`, in `_retire` and `replan` (else branch, before `_new_opp`).
- **What:**
  - When an opportunity ends, `ended_by_identity` also keeps its `lineage`, `lineage_created_utc`, `tests` and `ended_utc`.
  - A new opportunity whose identity has an ended entry **inherits** `lineage`, `lineage_created_utc` and `tests`. This is the mechanism supersession already uses (design §6.1, "the successor keeps its history and test count"), applied as §10 defines the root ("the first id of the opportunity's identity lineage").
  - The hourly candles between the predecessor's `tests.through_utc` and the creation are counted at once, by the existing `_count_test`. Otherwise a re-arm in that gap would be lost, because the tracker only counts hours while tracking.
  - `ever_active` is **not** inherited: a reissue must reach the zone again, so the destination-first rule is unchanged.
  - The history records "continues the lineage of <id>".
- **Unchanged:**
  - `stp/authorise.py` (`which_test` already uses the lineage and its tests);
  - rule 11 and key formats;
  - the duplicate rule;
  - lifecycle statuses;
  - what a strategy confirms.
- **Effect:** the same D-25 test of the same identity gets the same key across reissues. A genuinely new test (re-armed) gets `#t(n+1)` and is traded normally.
- **Unintended consequences, assessed:**
  - The dashboard's "lineage" column shows the root id for reissues.
  - An identity seen again days later continues its count. That is correct: D-25 re-arms are counted, so the number only grows, and the key is then new.
  - A `current.json` written before C-2 has `ended_by_identity` entries without lineage or tests. They fall back to the predecessor's own id (lineage) with tests counted from its creation. A live opportunity at deployment (today, 1305-58) keeps its own lineage unless the owner approves a one-off link (PD-4).
- **Seeding (closes L-7).** At creation, the last finished hourly candle before creation (the candle the plan was built on) is counted by the existing `_count_test` rule. If it interacts with the zone, test 1 is recorded as having begun then. This uses the existing D-25 rule on one existing candle: no new number and no window. A pre-creation rejection candle can only lie in that hour (trigger after creation, at most 9 five-minute candles after the pierce), so the test it belongs to is recorded. After a wholly clear hour the next test is then 2. The creation hour itself is also counted (today `_count_test` skips it because it starts a few seconds before creation, O-3). Otherwise a re-arm in that hour would be missed. `which_test` needs no change: it reads the recorded tests.
- **Risk:** low. It reuses existing code paths, and the authorisation check does not change.

### C-3: duplicate rule on the primary destination zone (owner decision PD-2)
`_duplicate_of`: "same primary destination" becomes "the new primary destination zone overlaps the completed one's primary destination zone" (the existing `overlaps()`, no new number), instead of equal prices.
- **Effect:** 1200-57 would not have been issued (13134.6–13142.1 overlaps 13135.5–13142.1).
- **Consequence:** fewer publications at a destination just achieved. Ending only at a structural change (no time limit), as approved on 19 Nov.
- With C-2 in place, C-3 affects publication and the dashboard; duplicate execution is already prevented.

### C-4: parallel and rollover successors share the lineage (owner decision PD-3)
At creation, a new opportunity whose zone overlaps a **live** opportunity in the same direction inherits that opportunity's lineage and tests, as in C-2. The same applies to an opportunity INVALIDATED at the same 00:00 rollover with an overlapping zone (implementing §12's "with no successor").
- **Lifecycles:** not merged; each keeps its own status (OD-01).
- **Effect:** closes L-4.
- **Consequence:** zones that share only an edge price (13084.1–13093 and 13093–13103) would share a lineage. Whether "overlap" should then mean more than a shared edge is part of PD-3.

### C-5: how circumstance 4 ends (owner decision PD-1)
- **A. Record only (C-1).** With C-2, duplicate execution is already safe. Recommended as the minimum.
- **B. Tracker-only.** Treat `after_zone_at_or_before_creation` as COMPLETED, for the duplicate rule only.
  - Effect: 2100-36, 1305-58, 1600-33 and 0200-53 would not have been issued; none of the 9 trades changes.
  - Consequence: fewer reissues where price was already at the zone.
- **C. Trade-linked.** The engine records "opened from <opportunity>" in a separate append-only file that the tracker reads, and an opportunity whose trade opened ends COMPLETED at its destination.
  - This is precise, but it crosses the approved "STP reads no trading record" boundary.

### C-6: missing data (owner decision PD-5)
- **A.** Record a "data gap" event on every live opportunity whose life overlaps a recorded, unfilled 5m gap (recorded only).
- **B.** Also: such an opportunity is not current for a new authorisation until the gap is filled. This is D-21's fail-closed rule applied to unavailable data, not a time limit.
- **C.** Also: after an approved fill, the tracker re-checks the filled candles for those opportunities (zone, then destination, in time order).
- Recommended: A + B, with C designed only if the owner wants lifecycles corrected after fills.
- **Consequence of B:** an opportunity live across a restart stops authorising until the owner's gap fill. Opportunities created after the gap are unaffected.

### C-7: dashboard wording (owner decision PD-6)
- The headline label becomes "Watch & Wait".
- The headline names the opportunity that would bind first (the oldest) or says "N live".

### Operational (owner, not code)
- **OP-1:** go-ahead for the existing gap fill (`gap-go`, 1 request, 3 points; §8).
- **PD-0:** the interim position on 1305-58 (§1).

---

## 11. Decision register (owner approval required)

| ID | Decision | Options | Recommendation | Affects trading |
|---|---|---|---|---|
| **PD-0** | Interim, before any correction: 1305-58 can authorise a gated BUY at 13121.3–13130.3 under a fresh key for test 1, already traded twice today | (a) accept until C-2 is deployed; (b) switch `STP_AUTHORISES_ENTRIES` off (the approved Stage B rollback; gated strategies then trade as before Stage B, under their old filters) | Owner's call; I have changed nothing. The exposure lasts until 1305-58 ends or the zone re-arms | yes |
| **PD-1** | How circumstance 4 ends (C-5) | A record only / B tracker-only COMPLETED / C trade-linked | **A** (with C-2) | A: no. B: publication only. C: publication only |
| **PD-2** | Duplicate rule on destination zones (C-3) | keep exact price / zone overlap | zone overlap | publication; and, through it, which opportunities can authorise |
| **PD-3** | Parallel and rollover lineage (C-4) | keep / inherit from a live overlapping same-direction opportunity and a same-rollover invalidated one / the same with an overlap of more than a shared edge | the third option, if the owner wants L-4 closed now; otherwise keep and watch (no occurrence yet) | duplicate keys only |
| **PD-4** | At deployment of C-2: link a live reissue to its ended identity (one-off, recorded) | yes / no | yes, if any is live then | duplicate keys only |
| **PD-5** | Missing data (C-6) | A / A+B / A+B+C | A+B | B: yes (fail-closed) |
| **PD-6** | Dashboard wording (C-7) | yes / no | yes | no |
| **OP-1** | Fill the 27 Nov gap from IG's history | go / not | go (approved routine; 3 points) | candles and indicators from then on |
| C-1, C-2 | records reason; lineage continuity with test seeding (closes L-2 and L-7) | – | approve for implementation | C-1: no. C-2: duplicate keys only |

---

## 12. Proposed regression tests

### Technical (offline; IG never contacted; tracker and authorisation with synthetic or stored candles)
| ID | Test |
|---|---|
| TL-01 | Zone reached only before creation ("in zone at creation"), then destination after creation: INVALIDATED with `destination_case = after_zone_at_or_before_creation` and the new text (C-1) |
| TL-02 | No interaction, destination first: `before_zone`, text unchanged |
| TL-03 | Activated after creation, destination reached: COMPLETED, `after_zone` (unchanged) |
| TL-04 | Same as TL-01 through the D-1 re-plan branch and through `_catch_up`: same case and words |
| TL-04b | Seeding (C-2): an opportunity created while the last finished hourly candle interacts with the zone records test 1 from that hour. A pre-creation rejection candle gives 1; after a wholly clear hour, the next interaction gives 2 (1700-34's real candles: 16:50 → 1, 26 Nov 03:05 → 2) |
| TL-05 | Identity ends (COMPLETED), reissued with no re-arm: the reissue's `lineage` = the first id; `which_test` for a rejection candle in the same test gives the same `n`; rule 11 refuses the second idea "same signal already traded" (C-2) |
| TL-06 | As TL-05, with a wholly clear hourly candle *between* the ending and the reissue (the gap hours): `n + 1`; the idea is allowed |
| TL-07 | As TL-05 after INVALIDATED "destination reached before entry", BROKEN-then-held, structure break and rollover: lineage inherited in each case; `ever_active` false on the reissue |
| TL-08 | Supersession unchanged: the successor keeps lineage and tests (existing T-58 to T-61 pass unchanged) |
| TL-09 | A `current.json` without lineage/tests in `ended_by_identity` (pre-C-2) loads, and the fallback lineage is the ended id |
| TL-10 | Duplicate rule with an overlapping primary destination zone and a different price: not issued (C-3, if approved); a non-overlapping zone: issued |
| TL-11 | Parallel publication: a younger same-direction opportunity at an overlapping zone inherits the live one's lineage; the oldest ends first; the same test keeps its key (C-4, if approved) |
| TL-12 | Rollover: a fixed level gone and an overlapping same-direction successor at the same re-plan: the lineage continues (C-4) |
| TL-13 | Recorded 5m gap inside a live opportunity's life: a "data gap" event; with C-6 B the authorisation refuses "STP not current: unfilled data gap since …"; after the gap is filled, current again |
| TL-14 | Fail-closed on an incomplete hour (13:00 → 13:05): unchanged |
| TL-15 | Observe-only and switches-off equality: with `STP_AUTHORISES_ENTRIES` off, trading decisions are byte-identical (existing T-48) |
| TL-16 | Dashboard: the headline label "Watch & Wait" and its choice of opportunity (C-7, if approved) |

### Functional (real recorded candles and journals; replay of the tracker and the authorisation check)
| ID | Day | Expected |
|---|---|---|
| FL-01 | 25 Nov 14:00–18:30 | 1500-32 ends `after_zone_at_or_before_creation`. 1600-33: under C-2 the same lineage as 1400-31, **test 1**. 1700-34: the 17:06:04 idea is authorised `1700-34#t1` exactly as recorded; the ending is `after_zone_at_or_before_creation` |
| FL-02 | 25 Nov 18:00–26 Nov 00:00 | 2100-36: under C-2 lineage 1700-34, whose seeded test 1 began at 16:00; the 17:00–20:00 re-arm makes its next test **2** (without the seeding it would wrongly be 1). With PD-1 B, not issued |
| FL-03 | 26 Nov 00:00–27 Nov 00:00 | the trades' keys unchanged: 0000-37 #t1 (06:01), #t2 (11:40); 0400-38 #t1 (06:30), #t2 (12:51); 1400-44 #t1 (14:22). All refusals unchanged |
| FL-04 | 27 Nov 03:00–14:15 | 06:55 authorised `0300-56#t1` as recorded. **12:01:27: the idea binds 1200-57 with key `0300-56#t1` and is refused by rule 11 ("same signal already traded by Bollinger bounce 5m")**. 1305-58 continues the lineage; any later idea in test 1 is refused |
| FL-05 | 27 Nov gap | the gap event on 1200-57; with C-6 B, no authorisation from 1200-57 after 12:15 until filled. 13:05:04 is still refused "not current" |
| FL-06 | 24–27 Nov, all STP-authorised ideas | every authorisation and refusal identical to the record except FL-04's 12:01 idea. Ungated strategies' decisions identical |

---

## 13. Effect on existing successful trading behaviour

Every STP-authorised trade since Stage B (25 Nov 13:10), under C-2 (and C-3 and C-4):

| Trade | Key recorded | Key under C-2 | Decision under C-2 | Under C-3 / C-4 | Result as recorded |
|---|---|---|---|---|---|
| AB261125170604 (17:06, bounce BUY) | 1700-34#t1 | 1700-34#t1 | unchanged | unchanged | +4.7 |
| AB261125200515 (20:05, bounce SELL) | 1800-35#t1 | 1800-35#t1 | unchanged | unchanged | −4.4 |
| AB261126060101 (06:01, BUY) | 0000-37#t1 | 0000-37#t1 | unchanged | unchanged | +4.5 |
| AB261126063004 (06:30, SELL) | 0400-38#t1 | 0400-38#t1 | unchanged | unchanged | −7.3 |
| **AB261126114004 (11:40, BUY)** | 0000-37#t2 | 0000-37#t2 | **unchanged** | unchanged | **+14.0** |
| AB261126125133 (12:51, SELL) | 0400-38#t2 | 0400-38#t2 | unchanged | unchanged | −6.4 |
| AB261126142255 (14:22, SELL) | 1400-44#t1 | 1400-44#t1 | unchanged | unchanged | +2.1 |
| AB261127065505 (06:55, BUY) | 0300-56#t1 | 0300-56#t1 | unchanged | unchanged | −2.0 |
| **AB261127120127 (12:01, BUY)** | 1200-57#t1 | **0300-56#t1** | **refused by rule 11** | C-3: not even published | −1.4 (closed by owner) |

- **Ungated strategies** are not touched by any correction. That includes the session sweep BUY at 15:05 on 25 Nov (+61.4), slow grind, breakout, EMA pullback, Asian range and New York reversal.
- **Strategy confirmation, stops, take profits and trade management** are unchanged.
- **STP's forecasts, zones and destinations** are unchanged. C-3 and PD-1 B change only whether an already-achieved identity is *published again*.
- **Genuinely new tests stay tradable:** the re-armed tests (0000-37 #t2 +14.0; 0400-38 #t2) are keyed exactly as today.
- No financial improvement is claimed. The one changed decision is a trade the owner closed by hand during the deployment, and its outcome says nothing about the correction's value.

---

## 14. Observations outside this phase (no change proposed)

- **O-1.** When several setups of one strategy trigger in the same candle, the engine tries only one, the first (25 Nov 15:05: five 5m bounce BUY setups; the one tried had a rejection candle outside 1500-32's zone; three later ones were inside). This is approved behaviour (§9.5 / §10, one try per strategy, direction and candle). Changing it would change strategy and engine behaviour, outside this phase.
- **O-2.** The D-25 option text versus the approved P-C8 (§7).
- **O-4.** The incomplete-hour build delay (§8): fail-closed, as designed.

---

## 15. Files on this branch

| File | What |
|---|---|
| `REPORT.md` | this report |
| `lifecycle_audit.py` | the read-only audit (STP's own rule functions on copies of the production files) |
| `output/lifecycle_audit.txt`, `output/lifecycle_audit.json` | its output on the 27 Nov 14:15 UTC snapshot |
