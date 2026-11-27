# STP lifecycle states and structural levels: inventory for a Phase 3 "structural coherence assessment"

Read-only research, 27 Nov 2026. Commits:
- **P** = production `fadf228` (worktree `/home/autobot/worktrees/autobot-phase3-research`)
- **F** = frozen Phase 2 `9e0ffd5` (branch `stp-lifecycle-integrity`, worktree `/home/autobot/worktrees/autobot-stp-lifecycle-impl`)
- **D** = design rev 3.2 `dbcffef` (`/home/autobot/worktrees/autobot-stp-integration/docs/design/STP_STRATEGY_INTEGRATION_20261124.md`)

Paths are repo-relative. Line numbers are P unless marked F. Sections marked **[fact]** come from the code or docs. Sections marked **[interp]** are my interpretation.

---

## 1. Lifecycle states and transitions

### 1.1 State constants [fact]

| Value | Defined | Authorises? | Label |
|---|---|---|---|
| CANDIDATE | `planner/keeper.py:69-70` | no. It is transient: `_new` sets CANDIDATE, writes issued.jsonl, then sets WAITING in the same call (`keeper.py:200-210`) | – |
| WAITING | same | yes (`LIVE = (WAITING, ACTIVE)`, `keeper.py:71`; `AUTHORISING = LIVE`, `planner/opportunities.py:51`) | "Waiting" |
| ACTIVE | same | yes | **"Watch & Wait"** (`opportunities.py:52-56`, OD-11) |
| BROKEN | `opportunities.py:49` (opportunities mode only) | **no**, in either direction | "Broken" |
| COMPLETED | `keeper.py:69` | no (terminal) | |
| INVALIDATED | same | no (terminal; the reason is in `status_reason`) | |
| SUPERSEDED | same | no (terminal; the successor inherits lineage and tests) | |

These states do **not** exist as statuses: "failed breakout", "retest", "reclaim", "wick sweep", "closed beyond", "in zone at creation", "ambiguous", "kept" and "duplicate". They are **event kinds** in recommendations.jsonl only. D §16 (line 712) explicitly rejected the status names WATCH_AND_WAIT, BREAK_PENDING, CONTINUATION and CANCELLED_DESTINATION_FIRST.
`TRACKED = (WAITING, ACTIVE, BROKEN)` (`opportunities.py:50`). Other readers hard-code `("WAITING","ACTIVE")`: `stp/authorise.py:43`, `stp/levels.py:109`.

### 1.2 Primitive price rules (shared by the tracker and the gate) [fact]

| Rule | Code | Definition (sell price, `near` = `rejection.near_level_within_pips` = 3, `settings.toml:535`) |
|---|---|---|
| **interacts** (approach/touch/enter) | `planner/zones.py:291-300` | SELL zone (`from_below=True`): `high >= low_edge − 3 pips` AND `low <= high_edge`. BUY zone: mirror. The candle reaching within 3 pips counts as "at the zone": there is no separate "approaching" state. |
| **wholly_clear** (re-arm) | `zones.py:325-329` | `low > zone_high + 3 pips` OR `high < zone_low − 3 pips` |
| **reached** (destination) | `zones.py:310-322` and `interacts` on the destination zone, from the trade's side | |
| **D-25 test count** | `zones.py:332-341` `count_tests`; tracker copy `opportunities.py:231-247` `_count_test` | an hourly candle interacting (either side) while armed = a new test; then wholly clear = re-arm |
| **zone break price** | `planner/assess.py:487-490` | `zone_break_close = zone.high + 3 pips` (SELL) / `zone.low − 3 pips` (BUY), 1h; `structure_break_close = last opposing H4 swing ± 3 pips`, 4h |
| `break_beyond_pips` = 3, `failed_breakout_within_candles` = 3 (P-F7) | `config/settings.toml:720,726` | |

### 1.3 Transitions in opportunities mode (STP_OPPORTUNITIES on), P [fact]

| From | Trigger | Where (P) | To / event |
|---|---|---|---|
| – | hourly re-plan proposal, identity not live, not a duplicate | `opportunities.py:334-346` → `keeper.py:193-210` | CANDIDATE→WAITING ("created", "waiting") |
| WAITING | a 5m candle **after creation** interacts with the entry zone | `keeper.py:285,305-309` (called via `opportunities.py:168-171`) | ACTIVE, `ever_active=True`, `activation` evidence ("active") |
| WAITING | a 5m candle that started before creation touched the zone or destination | `keeper.py:288-295` | no change; "ambiguous" event |
| new opp | the last 5m candle before creation was at the zone | `opportunities.py:349-357` | no change; "in zone at creation" |
| WAITING | the primary destination is reached first, and `destination_first_applies` | `keeper.py:296-303`; at the re-plan `opportunities.py:304-315` | INVALIDATED "destination reached before entry" |
| ACTIVE (`ever_active`) | the primary destination is reached (5m, or found at the re-plan) | same | COMPLETED |
| ACTIVE | price moves wholly clear | **no demotion** in opps mode (H18; only the single tracker demotes, `keeper.py:350-352`) | – |
| WAITING/ACTIVE | **hourly close ≥ 3 pips beyond the far edge** (= `zone_break_close`; D-20) | `opportunities.py:208-217` | **BROKEN**, `broken={broken_utc,candles:0}`, `zone_broken_at` ("broken") |
| WAITING/ACTIVE | hourly close beyond the far edge by less than 3 pips | `opportunities.py:218-222` | "closed beyond" (recorded only) |
| WAITING/ACTIVE | after a closed-beyond, a close back inside | `:223-226` | "reclaim" (recorded only) |
| WAITING/ACTIVE | hourly wick beyond the edge, close inside | `:227-229` | "wick sweep" (recorded only) |
| BROKEN | hourly close back inside the far edge within 3 candles (**failed breakout**) | `:191-200` | **ACTIVE (Watch & Wait)** at that close ("failed breakout"; OD-07/OD-31). Note it becomes ACTIVE even if it was WAITING before the break. |
| BROKEN | 3 hourly closes with no reclaim | `:201-204` | INVALIDATED "confirmed break held" |
| BROKEN | the primary destination is reached on 5m | `:172-179` (runs the keeper's check with the status temporarily set to ACTIVE) | COMPLETED / INVALIDATED as above |
| any tracked | **4h close at or beyond `structure_break_close`** | `:249-260` | INVALIDATED "structure break" |
| any tracked | 00:00 UK re-plan: a fixed daily/weekly level of the zone is gone from the level map | `:262-277` | INVALIDATED "structural levels changed" (D-21, OD-13) |
| live | re-plan: same identity, overlapping zone | `:319-327`, `keeper.py:231-259` `_update_from` | in place: "supported" / "changed". Zone, destinations and **invalidation** are overwritten from the new plan. |
| live | re-plan: same identity, non-overlapping zone | `:328-333` | old SUPERSEDED; new one inherits lineage, `ever_active` and tests |
| live | re-plan chooses another zone, recommends nothing, or the H4 direction/condition changes | not coded (OD-02/OD-06) | no change |
| – | proposal whose identity's last ending was COMPLETED with the same primary price | `:132-141`, `:335-344` | not issued; "duplicate" event (once per dup id) |

**Retest of a broken zone** [fact]: no tracker state. D §7.3 (lines 287-291): continuation comes **only** from STP's own later bidirectional proposal (e.g. a BUY at broken resistance). "A broken opportunity never authorises the opposite direction" (D §6.3).
**Rejection-candle rule** [fact]: STP has **no** rejection rule of its own. The rejection is the strategy's watcher setup: pierce → reversal → confirmation → trigger, expiry or cancel (`rejection/watch.py:55-56, 211-306`; windows `settings.toml` `reversal_candle_within_candles_of_pierce=3`, `confirmation_candle_within_candles_of_reversal=3`). The gate takes the setup's **pierce candle** as `context["rejection_candle"]` (`strategies/bollinger_bounce_5m/strategy.py:52`, `strategies/level_reversal/strategy.py:129`, hourly bounce `strategies/common.py:447`) and only requires `interacts(rejection_candle, zone)`. A failed rejection is not a tracker event: the opportunity stays Watch & Wait (D line 228, H19; T-18).
**No time expiry anywhere** (H16; `opportunities.py:22`).

### 1.4 F changes to these transitions [fact]

| Item | F location | Change |
|---|---|---|
| **Completion (PD-1 C, C-1)** | `planner/keeper.py:76-107` (F) `executed_before`, `destination_end`; used at `keeper.py:334` (F) and `opportunities.py:742-745` (F) | destination reached → COMPLETED `after_trade` if an IG-confirmed execution from the opportunity happened **before the destination candle's end**. Otherwise COMPLETED `after_zone` if `ever_active`. Otherwise INVALIDATED `after_zone_at_or_before_creation` (if `zone_before_creation`) or `before_zone`. Each ending records `destination_case`. The destination check also applies if an execution exists even when `destination_first_applies` is false. |
| zone_before_creation | `keeper.py` 5m OVERLAPPED branch (F, ~line 323); `opportunities.py:779-790` (F); `_new_opp` (F ~:318) when a D-25 test is already in progress | recorded only; never activates |
| Late acknowledgement | `opportunities.py:502-548` (F) `_take_acks` | an ack arriving after the ending: the member's `effective_status` becomes COMPLETED and a "classification corrected" event is written. **The opportunity is never reopened.** |
| **Lineage** (C-2/PD-3) | `planner/lineage.py` (F, new); `opportunities.py:216-334` (F) | a new proposal joins the lineage of a live same-direction opp with the same identity, or a zone strictly overlapping both that member and the lineage **home zone** (edge-only contact does not count, `lineage.py:57-65`). Otherwise the most recently ended such opp. Otherwise a new lineage. The lineage owns `tests`. |
| Test seeding | `lineage.py:131-147` (F) `seed_tests` | a new lineage counts from the last **complete** wholly-clear hour before creation (it walks back). A test in progress before publication is #t1. `test_number` returns 0 for a rejection before the seeded history (`lineage.py:167-190`). |
| Re-arm needs a complete hour | `lineage.py:83-101` (F) `count_hour` | an incomplete clear hour is "uncertain"; it neither tests nor re-arms |
| **Duplicate rule (PD-2 + re-arm)** | `opportunities.py:242-275` (F) `_duplicate_of` | withhold when the most recently ended same-direction member with the same identity **or an overlapping zone** has `effective_status == COMPLETED` AND the destination price is equal or the **destination zones overlap**. **Not withheld once the zone has re-armed since that completion** (`rearmed_since`, `lineage.py:123-128`; REVIEW_R3_2.md:52-56). |
| Data gaps (PD-5 A/B/C, D-R1/D-R2) | `opportunities.py:336-500` (F); `planner/gaps.py`; `planner/review.py` | `data_gaps[]` on an opp (`status` open/reconciled/review). Lineage `tests.uncertain[]` and `tests.review_hours[]`. These block authorisation (fail closed), with no override. |
| Lineage map (PD-4) | `opportunities.py:560-614` (F); `planner/migrate_lineage.py` | applied once by sha256; alias keys per test |
| Run order | `opportunities.py:793-841` (F) | `_apply_lineage_map` → `_take_acks` → `_reconcile_gaps` → record gaps → 5m → 1h (`_count_lineages` first) → 4h → replan |
| **Unchanged** | | the BROKEN / failed-breakout / break-held / structure-break / rollover / supersede / no-demotion rules (`opportunities.py:634-713` F are byte-identical in logic to P `:181-277`) |

---

## 2. Persistence and order-time readability

### 2.1 Files [fact]

| File | Writer | Contents | Read at order time? |
|---|---|---|---|
| `data/planner/GBPUSD/current.json` | tracker (`keeper.py:154-158` safe_write; opps `_save` `opportunities.py:90-97`) | full state | **yes**: `stp/source.py FileSource` (mtime+size cache), only while STP_AUTHORISES_ENTRIES is on (`source.py:70-74`). The strategies' level copy also reads it (`stp/levels.py`, `strategies/replay.py:109-110`). |
| `recommendations.jsonl` | `_append`/`_event` (`keeper.py:149-167`) | every event `{time_utc, event, id, why, status?, ...evidence}` and every hourly `analysis` `{plan: summary}` | no (audit) |
| `issued.jsonl` | `_issued` (`keeper.py:212-229`) | each opp in full at creation plus `analysis_as_of_utc`, `structural_snapshot`, `candidates`, `h4_last_swing` | no. **It has no `lineage` field** in P or F: `_issued` runs inside `_new` before `_new_opp` sets the lineage. In F the link is the "lineage" event in recommendations.jsonl. |
| `technical.json` / `.jsonl` | `planner/technical.py:793-806`, `[stp_technical] enabled=true` | the observe-only H1/H4 forecaster (PULLBACK, REVERSAL, RANGE_REVERSAL, BREAKOUT, FAILED_BREAKOUT). **Never feeds the lifecycle.** | no |
| F: `data/orders/GBPUSD/stp_executions.jsonl` (**orders** folder, not planner) | `orders/executions.py:61-98` (F), written by `orders/sender.py:226-227,316` (F) | `reference, deal_id, strategy, direction, opportunity, lineage, test, key, keys[], executed_utc, recorded_utc, source` | by the tracker only (`_take_acks`). The gate reads state via current.json. |
| F: `data/planner/GBPUSD/lineage_map.json` | `planner/migrate_lineage.py --apply` | lineages, aliases, consumed, opportunity_lineage | tracker, once |

### 2.2 current.json top level [fact; live keys observed in /opt/autobot/data at P]
`pair, counter, mode="opportunities", opportunities[], recommendation (newest live copy), ended_by_identity{identity_json: {id,status,identity,primary}}, last_ended, recent[], not_issued, duplicate_noted, last_plan, last_plans{SELL,BUY}, validated_h1_end, m5_checked_until, h4_checked_until, last_replan_uk_day, current, data_fresh, not_current_reasons[], last_analysis_utc, last_run_utc, written_utc, observe_only, watch_after_break` (a single-tracker leftover).
F adds: `lineages{lid: {id, trade, home_zone{low,high}, created_utc, tests{events[[utc,"test"|"rearm"]], through_utc, since_utc, uncertain[], review_hours?, reconciled?, seed?}, members[{id, identity, zone, primary, primary_zone, created_utc, ended_utc, status, effective_status, destination_case, destination_candle_end_utc, data_gaps?, corrected?}], aliases{n:[keys]}, consumed{n:[refs]}, map_evidence?, merged_into?}}`, `acks_seen[]`, `lineage_map_applied`.

### 2.3 Opportunity record [fact; `keeper.py:198-205`, `_update_from` 252-258]
- `id` `STP-GBPUSD-YYYYMMDD-HHMM-n`, `instrument`, `created_utc`, `market_data_utc`, `status`, `status_reason`, `label`, `ended_utc`
- `trade` "BUY"/"SELL" (**trade direction**), `identity` `[trade, [[name, price] of the fixed levels]]` (FC-05, `keeper.py:101-105`), `far_edge`, `ever_active`, `activation{candle_start_utc,...}`, `history[]`
- `entry_zone{low, high, class (Major|Moderate|Minor), families[], daily_or_weekly_level, tests, reference{}, levels[{price, name, role, family, timeframe, origin_utc, daily_or_weekly, fixed, note}]}` (`zones.py:264-268`)
- `destinations{intermediate, primary, extended}` each `{price, zone{low, high, class, families, levels...}}` (`assess.py:481-485`)
- `invalidation{zone_break_close, zone_break_timeframe:"1h", structure_break_close, structure_break_timeframe:"4h", destination_first, destination_first_applies, conditions[]}` (`assess.py:488-500`)
- `dominant_direction, condition, opportunity, expected_movement, reference_entry, reachability, selection_reason, observations, direction_evidence, condition_evidence, alternative, six_factors, relation_to_h4`
- opps mode: `lineage, lineage_created_utc, supersedes, tests{events, through_utc}, broken{broken_utc, candles}, zone_broken_at, beyond_close_utc`
- F adds: `executions[{reference, strategy, executed_utc, test, key, source}]`, `zone_before_creation{basis, candle_start_utc}`, `data_gaps[{from_utc, to_utc, found_utc, status, reconciled_utc}]`

---

## 3. STP entry gate (STP_AUTHORISES_ENTRIES)

[fact] Gated set: `config/settings.toml:669-676` `strategies = ["Bollinger bounce", "Bollinger bounce 5m", "level reversal"]` (OD-03). `stp/gate.py:9-17`. Called once in `trading/engine.py:325-345` `_place`, after the try is recorded and **before** the entry filters.
Bypass list (`settings.toml:676`): `analyser_state` (`strategies/common.py:390,409-413`), `hourly_context` (rule 1), `rsi_stretch` (2b), `counter_trend_tiring` (rule 3) (`strategies/entry_filters.py:251-338`), `one_view` (safety rule 9, `safety/rules.py:196-199`, reads `context.stp.bypass`). Everything else is unchanged.

Checks (`stp/authorise.py:144-217`, P), with fail-closed refusals:
1. STP_OPPORTUNITIES, STP_BIDIRECTIONAL and ONE_SIGNAL_ONE_TRADE are all on (`:151-154`).
2. The file is readable, `written_utc` ≤ 10 min old, `current is True`, and the live tick / latest 5m is ≤ 10 min old (`:155-173`).
3. `context.rejection_candle` exists and is in the store (or is the partial candle) (`:174-182`).
4. A live (WAITING/ACTIVE) opp of the **same direction** whose entry zone the rejection candle `interacts` with (`:183-190`). The entry price may lie outside the zone.
5. Ordering: oldest lineage, then strongest class, then nearest edge (`:191-194`).
6. Per candidate, `_catch_up` (`:96-141`) applies the tracker's rules to what it has not seen yet: a destination touch on 5m / partial / tick, an hourly close ≥ `zone_break_close` since `validated_h1_end`, a 4h close ≥ `structure_break_close` since `h4_checked_until`. Then the entry must not be at or beyond `zone_break_close` (FC-07) (`:198-201`).
7. First pass → key `<lineage>#t<n>` (`which_test` `:66-93`). `signal = existing|key`, and rule 11 refuses a used part.

**OD-33** [fact]: D line 186 says "Simultaneous BUY and SELL opportunities at the same zone are permitted; the existing strategy confirmation decides which materialises; no additional directional filter". D §9.4 says "each authorises only its own direction at its own zone". In code, the `want` direction filter (`authorise.py:183-186`) is the only coupling. An opposite-direction lineage has its own key (D line 389).
**OD-18 A** [fact]: no rule against an ungated trade opposite an STP opportunity (D line 285). Ungated strategies never consult STP.

F changes (`git diff fadf228 9e0ffd5 -- stp/authorise.py`) [fact]:
- `unreconciled()` (`authorise.py:86-98` F) is prepended to each candidate's reasons: open/review data gaps, lineage `uncertain`, `review_hours` (PD-5 B, D-R1/D-R2).
- `_catch_up` also refuses when any expected 5m candle since `m5_checked_until` is not stored (`missing_fives`; the R3/R3.2 fix).
- The key is counted on the **lineage** tests (`_keys` `:104-111`, `planner/lineage.test_number`). It adds the alias keys for test n, plus the keys of **every other live same-direction lineage** the rejection candle reached (`:242-247`).
- The Verdict gains `lineage, test, keys`. The engine stores them in `context.stp` (`trading/engine.py:338-341` F), and the sender's ack carries them.
- **Unchanged**: the gated list, the bypass list, `gate.py`, `levels.py`, the same-direction filter, OD-33 behaviour. `git diff --stat` shows nothing in `stp/gate.py`, `stp/levels.py`, `config/settings.toml`, `strategies/` or `safety/`.
- Production status: STP_AUTHORISES_ENTRIES has been **off** since 27 Nov 14:58 (effective from the 16:26:57 restart; IMPLEMENTATION_REPORT §11).

---

## 4. Structural levels outside STP

[fact]
| Source | Code | Levels | Persisted |
|---|---|---|---|
| Bot level list | `levels/current.py:72-137` `build`; `levels/rules.py:75-160` | daily pivot, R1-R3, S1-S3 (classic floor, `rules.py:75-93`), previous day high/low, round numbers (every N pips within 150), London/NY session high/low (today so far + previous), hourly turning highs/lows; grouping by `line_up_within_pips` = 5; `IMPORTANT_TYPES = {pivot, R2, S2, round_number, turning_high/low}` (`rules.py:40`) | `data/levels/GBPUSD/current.json` (`levels/current.py:177-190`) |
| STP level map (superset) | `planner/zones.py:96-255` | the bot list + weekly pivot/R/S, previous week high/low, recent week extremes, 4h swings (8 wk), daily swings (48 wk) + historical daily swings (156 wk), EMA levels (H1 EMA100/200, H4 EMA100/200, H4 BB mid), "flipped" swing roles | only inside plans (`issued.jsonl structural_snapshot`, `last_plan.structure.levels`) |
| STP zones in the strategies' level copy | `stp/levels.py:32-61` `with_stp` | edges + fixed levels of live opps as `stp_zone` levels, one group each | not persisted; built per call |
| Analyser | `analyser/market_state.py` (5 states: ranging, emerging, trend, possible reversal, consolidation), `analyser/direction.py`, `day_direction.py`; gating via `strategies/common.py:78-96 ALLOWED_IN` | no levels; state + direction | `data/analyser/GBPUSD/current.json`, `state_changes.jsonl` |
| Technical forecaster | `planner/technical.py` | own H1 range boundaries, EMA20, swing evidence | `technical.json` |

**ROOM_TO_LEVEL** [fact]: it exists **only** on branch `room-to-level` at `1f4038d` (not an ancestor of `fadf228`, and `git branch --contains 1f4038d` shows only room-to-level). Not in P or F. `strategies/common.py` @1f4038d lines 419-461:
- `ROOM_TO_LEVEL_STRATEGIES = (BREAKOUT, ASIAN_RANGE_BREAKOUT)`, `ROOM_LEVEL_TYPES = (pivot, R1-R3, S1-S3)`.
- `room_to_level_context` takes the nearest such level **ahead** of the entry (a buy ≥ entry, a sell ≤ entry, with a 0-pip level counting) from the bot's level list.
- `room_reasons` refuses when `room_pips < stop_loss_pips` (breakout 6, Asian 12).
- Switch ROOM_TO_LEVEL, on if left out.

---

## 5. What the design / Phase 2 already says on conflict, Watch & Wait, fresh confirmation [fact, quoted]

- **OD-33** (D:186): BUY and SELL at the same zone are both permitted; "the existing strategy confirmation decides which materialises; no additional directional filter."
- **OD-18 A** (D:177, 285, 709): "no new rule against an ungated trade opposite an STP opportunity". Conflict reporting was withdrawn (D:81: "the conflicts are listed in this design for the owner (§7.2)").
- **§7.2** (D:273-285): filter conflicts resolved by **bypass** for the gated three (OD-05 A, OD-30).
- **OD-02 / H11** (D:142, 224): a new forecast, an H4 change or "evidence changed" never ends an opportunity. **OD-06**: H4 is context only.
- **OD-07 / OD-31** (D:147, 184, 230-235): a failed breakout returns the opportunity to Watch & Wait at the reclaim close. "A broken opportunity never authorises the opposite direction."
- **OD-08 / §7.3** (D:287-291): continuation only from STP's own opposite proposal. "Never: an opposite-direction authorisation because a reversal failed, a wick went through, or a close went beyond by less than 3 pips."
- **OD-11 / H18** (D:83, 151): once touched, an opportunity stays in Watch & Wait until it ends; there is no demotion.
- **H19 / T-18** (D:228, 451): a failed rejection is no tracker event; the opportunity is unchanged and there is no opposite authorisation.
- **Fresh confirmation, §9.5** (D:356-370): a setup triggered **before** publication and refused stays refused ("its confirmation was consumed at the trigger"). A setup in progress at publication may be authorised at its own trigger. "A **new** setup after publication at the newly published zone: Yes, normally. A fresh confirmation." There are no retries, queues or delayed execution.
- **D line 62**: "no mandatory hourly entry confirmation, no new confirmation algorithm".
- **OD-09 / OD-32 / H13, §10** (D:372-390): one trade per D-25 test. A new test (leave and return, D-25) gives one more trade. T-41: a new confirmation on the same test is refused. T-42: a new test is authorised `#t2`.
- **OD-12** (D:152): hourly forecasting, live monitoring, strategy confirmation (the live part is done by the gate catch-up, §9.3).
- **Phase 2**: PD-1 C (trade-linked completion), PD-2 (destination-zone duplicate) plus the REVIEW_R3_2 correction ("withholds a republication only while its zone has **not re-armed** since the completion"), PD-3 (shared lineage, edge-only excluded), PD-5 / D-R1 / D-R2 (fail closed, no override). IMPLEMENTATION_REPORT:299 says "Nothing from Phase 3 is included."
- **[interp]** Nothing in D or Phase 2 specifies cross-strategy conflict handling for **ungated** strategies, a "Watch & Wait" applied to anything other than an STP opportunity, or a requirement for fresh confirmation *after a wait*. Waiting is purely the tracker's ACTIVE state, and confirmation is always the strategy's own trigger.

---

## 6. P vs F differences a Phase 3 check must target

| Aspect | P (`fadf228`) | F (`9e0ffd5`) | Phase 3 implication [interp] |
|---|---|---|---|
| Test identity | per-opportunity `tests`, key `<opp lineage id>#t<n>` (lineage = id or supersede chain) | per **structural lineage** `state.lineages[lid].tests`; aliases; multi-lineage keys | read `lineages` when present; fall back to `opp.tests` |
| Completion | COMPLETED iff `ever_active` | plus `after_trade` via acks; `destination_case` on member; `effective_status` may differ from `status` | use `effective_status` / `destination_case` from lineage members |
| Duplicate withholding | same identity + exact primary price | same identity or overlapping zone + destination-zone overlap, released by re-arm | "no live opp" may mean withheld-as-duplicate; check `not_issued` |
| Eligibility | status ∈ {WAITING, ACTIVE} + catch-up | also `data_gaps`, `uncertain`, `review_hours`, missing stored 5m → refuse | a coherence check that reuses states must also reuse `unreconciled()` or it will disagree with the gate |
| Seeding | test count from creation | walk-back to the last complete clear hour; test 0 possible | |
| Ack file | none | `data/orders/GBPUSD/stp_executions.jsonl` | |
| Unchanged | statuses, BROKEN/failed-breakout window, structure break, rollover, supersede, gated list, bypass list, OD-33, `stp/levels.py` | same | the state vocabulary is stable across both builds |

[interp] Caveats:
- `zone_break_close` and `invalidation` are overwritten at each "changed" re-plan (`keeper.py:252-255`), so break levels move with the zone. Read them at decision time, not from issued.jsonl.
- `recommendation` in current.json is the **newest** live opp, while the gate binds the **oldest** (REPORT L-6). Use `opportunities[]`.
- BROKEN → ACTIVE on reclaim even if it was never touched (`ever_active` stays as it was).
