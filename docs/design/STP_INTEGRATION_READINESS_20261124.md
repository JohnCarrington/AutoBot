# STP strategy integration: investigation findings and implementation readiness assessment

**Status:** FOR INDEPENDENT REVIEW AND IMPLEMENTATION APPROVAL. Nothing is implemented, deployed, configured or restarted. STP stays observe-only.

| | |
|---|---|
| **Date** | 24 November 2026 |
| **Design** | `STP_STRATEGY_INTEGRATION_20261124.md`, revision 3.1 (same commit) |
| **Code examined** | `/opt/autobot` at 63d9c04, the live build |
| **Data** | 24 Nov 5-minute and hourly candles to 20:55 UTC; `data/records/GBPUSD/decisions.jsonl`; `data/planner/GBPUSD/recommendations.jsonl` (15 to 24 Nov) |
| **Method** | Code reading plus offline, read-only harnesses (in `stp_strategy_integration_20261124/`). No profit or loss is computed; no verdict is drawn from outcomes. The live IG demo remains the judge. |

Sell prices, UTC.

---

## Summary

| # | Action | Result |
|---|---|---|
| 1 | INV-1 RSI stretch | Complete. With STP on, it would have changed only three 24 Nov ideas: SELLs that STP authorises and RSI stretch refuses. In each, the RSI 3 reading came from the rejection's own fall. **Recommend bypassing it for STP-authorised ideas of the gated strategies (OD-30).** |
| 2 | INV-2 P-F7 window | Complete. 4 confirmed breaks of STP zones on record; 3 failed breakouts, every one back inside at the **first** hourly close. **Recommend confirming P-F7 = 3 for OD-07 (OD-31).** |
| 3 | Two-direction validation, 24 Nov | Complete. The harness reproduces every SELL STP actually issued. BUY opportunities exist at 10:00, 12:00–17:00, 18:00 and 19:00, including two continuation BUYs at broken resistance. None from 00:00 to 09:00. |
| 4 | Several levels in one zone, one rejection | Verified: at most one trade per test. One candle reaching several levels gives one setup per direction. Several setups from consecutive candles, and the second strategy, are stopped by the engine's one-try rule and the shared STP key. |
| 5 | Hourly bounce signal key | **Replacing it would weaken protection** in two ways. Fix: keep the existing key and add the STP key, with rule 11 checking both (OD-32). |
| 6 | Decisions and amendments | Consolidated (§6). Four genuinely unresolved items: OD-30 to OD-33. |
| 7 | Readiness | **Ready for implementation approval once OD-30 to OD-33 are decided.** No design blocker. Residual limits in §7. |

---

## 1. INV-1: RSI stretch

**The rule** (`strategies/entry_filters.py:23-26, 300-321`; switch `RSI_STRETCH`, on): no SELL when the 5-minute RSI 3 (sell price, Wilder) at the last finished candle is under 30; no BUY when over 70. Exempt: slow grind, breakout, Asian range breakout, session sweep. Live since 23 Nov 18:37.

**Every refusal of a gated-strategy idea so far** (all on 24 Nov), and what the design would do with STP on:

| Time | Strategy | Idea | RSI 3 | Live STP opportunity in that direction interacting with its rejection | With STP on |
|---|---|---|---|---|---|
| 05:55 | 5m bounce | SELL 1.30394 | 25.7 | none (nearest SELL zone 1.30750) | refused by STP anyway |
| 10:35 | hourly bounce | SELL 1.30610 | 25.8 | SELL 1000-19, 1.30621–1.30715 (pierce 10:05–10:10, high 1.30711) | **STP authorises; RSI stretch refuses** |
| 10:35 | 5m bounce | SELL 1.30608 | 25.8 | SELL 1000-19 | **STP authorises; RSI stretch refuses** (same rejection: rule 11 would allow only one of the two) |
| 14:35 | Level Reversal | BUY 1.31059 | 78.7 | none (the only BUY, B1200 at 1.30750–1.30854, is 20 pips below) | refused by STP anyway |
| 14:40 | Level Reversal | BUY 1.31133 | 89.7 | none | refused by STP anyway |
| 14:45 | Level Reversal | BUY 1.31151 | 90.6 | none | refused by STP anyway |
| 18:20 | 5m bounce | SELL 1.31156 | 23.6 | SELL 1700-23, 1.31176–1.31286 (18:10 high 1.31231) | **STP authorises; RSI stretch refuses** |

The 12:41, 14:38 and 17:06 EMA pullback and the 14:15 New York open reversal refusals are ungated strategies and out of scope.

**Why it refuses these.** RSI 3 is dominated by the last three closes. A confirmed rejection at resistance is, by construction, a red reversal candle and then a lower confirmation close, so it pushes RSI 3 down:
- 10:10 to 10:30 closes: 1.30684 → 1.30632 → 1.30637 → 1.30647 → 1.30612 (RSI 3 25.8);
- 18:05 to 18:15 closes: 1.31229 → 1.31203 → 1.31159 (RSI 3 23.6).

So the rule refuses a rejection-confirmed entry in proportion to how decisively the rejection confirmed. That conflicts with the governing principle that the strategy's own confirmation decides *when* (H06). The owner exempted the session sweep, a rejection strategy, from rule 2 for the same class of reason on 21 Nov (7118412).

**It is not a structural filter,** so OD-05's wording does not cover it automatically. That is why it needs its own decision.

**Options (OD-30):**
- **A (recommended).** Add `rsi_stretch` to `[stp_authorisation] bypass_filters`, for STP-authorised ideas of the three gated strategies only. It stays on for every other strategy and for gated ideas while STP authorisation is off. This is a configuration list, not a new number.
- **B.** Retain it. This is valid and conservative: STP-authorised SELLs at resistance and BUYs at support remain subject to it.

The evidence is one live day. No outcome of the refused ideas is assessed.

---

## 2. INV-2: the three-hourly-candle failed-breakout window (P-F7)

**Approved:** P-F7 = 3 hourly candles, "recorded only" (PARAMETER_APPROVAL_REGISTER group F, 17 Nov). OD-07 A (approved) wants a failed breakout to return the opportunity to Watch & Wait. That is a new use of an approved number, not a new number.

**Every confirmed break of an STP zone on record:**

| Opportunity | Confirmed break (hourly close) | Next hourly closes | Failed breakout? | What STP did next (recorded) |
|---|---|---|---|---|
| 0100-5, 18 Nov | 01:00 close 1.32059, 3.4 pips above 1.32025 | 02:00 close back below 1.32025 | **yes, 1st close** | re-proposed SELL at 02:00 (zone just above) and 03:00 (Major zone with top 1.32025) |
| 0100-10, 23 Nov | 06:00 close 1.31273, 3.6 pips above 1.31237 | 07:00 close back below | **yes, 1st close** | no SELL at 07:00 or 08:00 (destination already reached); SELL again from 09:00 |
| 1000-19, 24 Nov | 11:00 close 1.30891, 17.6 pips above 1.30715 | 12:00 1.30964, 13:00 1.30967, 14:00 1.31121 | no | — |
| 1400-21, 24 Nov (computed: STP had superseded it at 15:00) | 17:00 close 1.31204, 6.3 pips above 1.31141 | 18:00 close 1.31132 | **yes, 1st close** | re-proposed SELL at R1 at 19:00 (1900-24) |

**Findings:**
- Every failed breakout returned at the first close. The window of 3 was never needed beyond 1. There is no evidence for changing the approved number, and none is proposed.
- BROKEN authorises nothing, in either direction, so the window adds no entries while it is open. It matters only after a return.
- **With P-F7 (OD-31 yes):** the opportunity keeps its id, test count and duplicate keys, and resumes Watch & Wait at the closing return.
- **Without it (D-20 as approved):** the opportunity ends at the break. A return needs STP to re-propose the zone at a later re-plan. That happened on 18 and 24 Nov, but not on 23 Nov, where STP made no proposal for two hours.

**Recommendation (OD-31): confirm P-F7 = 3 for the OD-07 use.** It delivers the already approved OD-07 with an already approved number. The alternative is simpler, but it would contradict OD-07 A and depend on a re-proposal that does not always come.

---

## 3. Two-direction forecasting validation: 24 November

**Harness:** `bidir.py` runs STP's approved `assess()` at each hourly re-plan, once per direction (OD-16 A, OD-17 A). The H4 direction and condition are recorded but do not gate. Zone construction, grading, reachability (D-14), the primary destination (D-18), invalidation (D-20 and the H4 structure break) and destination-first (D-1) are all unchanged.

**Check:** the SELL side reproduces every recommendation STP actually made that day: the zones at 00:00, 09:00, 10:00, 13:00, 14:00, 15:00, 17:00 and 19:00, and the no-recommendations at 08:00, 12:00 and 20:00.

**BUY proposals** (H4 BEARISH all day; condition CONTINUATION, then CORRECTION_ACTIVE):

| Re-plan | BUY zone | Class, reachability | Primary destination | Zone break / H4 break | Notes |
|---|---|---|---|---|---|
| 00:00–09:00 | none | – | – | – | Price was below the last 4-hour swing low 1.30715, so every support zone was beyond it (D-14 mirrored: UNLIKELY) |
| 10:00–11:00 | 1.30621–1.30715 | Major, NEAR | 1.30750 | 1.30591 / 1.30685 | **Same zone as SELL 1000-19** (price inside). Completed 11:00. The mirrored H4 break (1.30685) lies inside the zone. |
| 12:00–17:00 | 1.30750–1.30854 | Major, PLAUSIBLE | 1.31355 (14:00: 1.31030; 17:00: 1.31176) | 1.30720 / 1.30071 | **The broken 0000-17/0900-18 resistance, now support: an STP continuation BUY.** Completed 14:05 after the 14:00 re-plan moved its primary to 1.31030. Reissued 15:00; ended 17:05 (destination 1.31176 before the zone). |
| 18:00 | 1.31191–1.31286 | Major, NEAR | 1.31355 | 1.31161 / 1.30071 | **Same zone as SELL 1700-23** (price inside) |
| 19:00 | 1.31026–1.31141 (R1) | Major, NEAR | 1.31191 | 1.30996 / 1.30071 | **Same zone as SELL 1900-24.** The broken R1, now support. Ended 19:05 (destination and zone in the same candle) |
| 20:00 | none | – | – | – | primary already reached (D-1) |

**Effect on the recorded gated ideas** (`ideas_vs_opps_output.txt`; interaction approximated over the 30 minutes before each idea):
- **BUY ideas interacting with a STP BUY opportunity, so STP authorises:** the 5m bounce at 10:05, 10:50 and 11:00 (B1000), at 12:35, 12:50 and 13:05 (B1200), and at 18:35 (B1800). All were refused today by the analyser state, which OD-05 removes for gated strategies. The retained filters (hours, news, risk, RSI stretch subject to OD-30) and rule 11 still apply.
- **BUY ideas with no matching opportunity, so STP refuses:** the Level Reversal BUYs at 14:35, 14:40, 14:45, **15:30 (opened today)** and 16:15, and the 5m bounce BUYs from 14:05 to 17:25. Also the 18:00:00 R1-retest BUY: B1800 was issued at 18:00:03, three seconds after it.
- **SELL ideas STP authorises:** 10:35 (S1000-19); 15:15, 15:40, 16:35 and 16:50 (S1400-21, which revision 3 keeps live); 18:20, 18:45, 18:55, 19:00, 20:40, 20:45 and 20:50 (S1700-23 and, from 19:00, S1400-21 again).
- **SELL ideas STP refuses:** 05:50–05:55, 08:00, 13:20 and 13:30–13:32. The 13:32 Level Reversal SELL at 1.31000 was opened today.

**Observations for the owner (no rule proposed):**
- **B-1. Both directions at one zone.** Three of the five BUY zones were the concurrent SELL zone, with price inside a Major zone and NEAR either way. With both live, STP authorises either direction there, and the strategy's confirmation decides which. This follows from OD-06 and OD-16, and it is consistent with "STP decides where; strategies decide when". But at such zones STP gives no directional filter. **Acknowledgement requested (OD-33).**
- **B-2. Hourly boundary.** A strategy trigger at the exact hourly close is checked a few seconds before that hour's new proposals exist (18:00:00 against 18:00:03). It is inherent to hourly forecasting, and no change is proposed.
- **B-3. In-place destination updates** (the existing tracker behaviour, kept) can complete an opportunity early when a re-plan moves its primary destination nearer (B1200 at 14:05).
- **B-4.** No BUY existed during the 08:30 to 10:00 breakout from the range, because of the mirrored D-14 bound. This is approved logic applied in the other direction (OD-16 A), and it is reported, not tuned.

**Prerequisite status:** two-direction forecasting is shown to produce BUY opportunities, including continuation, on 24 Nov. It still gates activation until WP-2 is built and tested (T-01 to T-03).

---

## 4. Several levels in one STP zone cannot give duplicate trades from one rejection

Checked on the code and with `multi_level.py`: the strategies' watcher (`design_only=True`) with three `stp_zone` levels in the 1700-23 zone (1.31176, 1.31273, 1.31286).

| Layer | Behaviour | Code |
|---|---|---|
| Watcher | One candle reaching several levels starts **one** setup per direction with all of them in its `pierced` list (case A: 3 levels, 1 setup, 1 SELL trigger) | `rejection/watch.py:198-208` |
| Watcher (by design) | Consecutive candles each reaching a level start separate setups. One rejection can then give several triggers (case B: two SELL triggers at 18:20, a third confirmed at 18:20). The same happens today with single bot levels. | `watch.py:130-137` (design 3.3/3.4) |
| Engine | At most one try per strategy, direction and candle, on both the live and the candle-close path | `trading/engine.py:239-251, 504-512` |
| Level Reversal | At most one candidate per setup (the first level within its allowance) | `level_reversal/strategy.py:91-113` |
| Rule 11, STP key | Every setup of the same test, from either strategy and in any later candle, carries the same `<root id>#t<n>`. A second order is refused even while the first is sent but not settled (registered before sending). | `orders/sender.py:452-457, 552`; design §10 |

**Result:** at most one trade per opportunity per test, as H13 requires. The key must be a function of the rejection candle (test containing it, binding as of it, lineage root id); design §10 specifies that.

**One implementation detail found:** the watcher asks each pierced level for its group (`levels/current.py:52`). STP levels therefore need a group of their own with `lined_up` false. That keeps the trade manager's "counts" mark unchanged (design §8).

---

## 5. The hourly bounce's signal key

**Today** (`strategies/common.py:426-433`): the hourly bounce, session sweep and New York open reversal carry `signal = "<direction> <rejection-candle start>"`. Rule 11 refuses any idea whose key a trade already used, whichever strategy used it (`safety/rules.py:219-226`).

**Replacing it with the STP key would weaken protection in two cases:**
1. **Cross-strategy.** Today an hourly bounce and a session sweep (or New York open reversal) on the same rejection candle and direction share a key, so only one trades. With the hourly bounce re-keyed, both could trade.
2. **Re-binding.** If the STP key depended on the moment of the check, one rejection could map to two keys. That happens when a superseded reissue has a new id, a test count has moved on, or another opportunity is added between two ideas of one rejection.

**Fix (OD-32), within rule 11, no new intelligence:**
- `signal` = the existing key, then `|`, then the STP key;
- `used_signals()` splits stored keys on `|`; rule 11 refuses if any part is used;
- the STP key uses the lineage root id, the test containing the rejection candle, and the binding as of the rejection candle (design §10).

The key already travels in the existing `signal` field and is journaled and restored on restart (`orders/sender.py:215, 430, 547-553`), so no record format changes. A key without `|` behaves exactly as today.

**Result:** the hourly bounce keeps every protection it has today and adds one trade per test. The 5m bounce and Level Reversal, which have no key today, gain one. Tests T-58 to T-61.

---

## 6. Consolidated decisions and amendments

### 6.1 Closed

| OD | Resolution | When |
|---|---|---|
| OD-01 | Several opportunities coexist | rev 2 |
| OD-02 | New forecasts do not invalidate existing structurally valid opportunities (H11 over ARCH §10.2 "evidence changes") | closed 24 Nov |
| OD-03 | Hourly bounce, 5m bounce, Level Reversal; BUY and SELL | rev 2 |
| OD-04 | Healthy-pullback and corrective-reversal opportunities authorise | rev 2 |
| OD-05 | Structural and directional filter conflicts bypassed for gated strategies (state gating, rules 1, 3, 9) | rev 2; RSI stretch → OD-30 |
| OD-06 | H4 is context | rev 2 |
| OD-07 | Failed breakout returns to Watch & Wait | rev 2; window → OD-31 |
| OD-08 | Continuation, via STP's own proposal in that direction | rev 2; mechanism accepted with rev 3 |
| OD-09 | One trade per distinct test | rev 2; key → OD-32 |
| OD-10, OD-11, OD-13 | Record tests, no thresholds; name Watch & Wait; weekly re-validation, no expiry | rev 2 |
| OD-12 | Hourly forecasting; live checks at entry; strategy confirmation | rev 2; mechanism accepted with rev 3 |
| OD-14 | Records: tracker events, status changes, authorisation decisions | rev 2; scope accepted with rev 3 |
| OD-15 | Inert `.env` switches: separate investigation | rev 2 |
| OD-16 | Existing credibility criteria in both directions | closed 24 Nov |
| OD-17 | One new opportunity per direction per forecast; existing ones kept | closed 24 Nov |
| OD-18 | No new exposure rule (A); reporting withdrawn | rev 3 |
| OD-22 to OD-25 | Option A for the 5m bounce and Level Reversal; hourly bounce keeps its band; two-direction forecasting mandatory; robust authorisation check | rev 3 |
| OD-26 to OD-29 | Zone edges + in-zone fixed levels; LR to the far edge + 3 pips; LR levels kept; switches and fail-safes | closed 24 Nov |
| OD-19, OD-20, OD-21 | Withdrawn (removed mechanisms; OD-20 replaced by OD-29) | rev 3 |

### 6.2 Genuinely unresolved

| OD | Question | Recommendation | Changes if not approved |
|---|---|---|---|
| OD-30 | RSI stretch for STP-authorised gated ideas | bypass | none to the design: it is one entry in `bypass_filters` |
| OD-31 | P-F7 = 3 for the OD-07 return | confirm | no BROKEN state; D-20 invalidates at the break (designed, §6.3) |
| OD-32 | Composite rule-11 key | approve | the hourly bounce would lose cross-strategy protection; not recommended |
| OD-33 | Both directions at one zone | acknowledge | any restriction would be a new rule, which the owner excluded |

### 6.3 Amendments to approved STP items
These follow directly from closed decisions. Design §16.1 lists them: D-03, D-10, D-16, D-20 (subject to OD-31), D-22 A, D-23 A, D-24 A (subject to OD-31), D-25 A, D-29 A, D-33, D-37, FC-10, ARCH §10.2, §11.2 and §13. Apart from the two OD-31 items, none is unresolved.

**Also an amendment, needing OD-32:** rule 11 (18 Nov) gains the `|` split. Its behaviour for every existing key is unchanged.

---

## 7. Implementation readiness assessment

| Area | Status | Evidence |
|---|---|---|
| Requirements H01–H23 | covered, each with technical and/or functional tests | design §15.1 |
| Architecture | minimum: tracker, level wrapper, one check; no new service, module or engine | design §1, §4 |
| Decisions | all closed except OD-30 to OD-33 | §6 |
| New numerical parameters | **none**. Reused: `near_level_within_pips` 3, `break_beyond_pips` 3, P-F7 3 (OD-31), `out_of_date_after_minutes` 10, strategies' own settings | design §18.3 |
| Strategy confirmation, execution, stops, risk, positions, exits | unchanged; byte-identical tests T-48 to T-52, T-55 | design §13 |
| Two-direction prerequisite | shown on 24 Nov (§3); enforced by a switch dependency | design §11 |
| Duplicates | verified (§4, §5) given OD-32 | design §10 |
| Stale data, intrabar, structural invalidation | specified with tests T-31 to T-39 | design §9 |
| Shadow trading, expiry, two-hour close | none | design §9.4, §6, §12 |
| Test specification | T-01 to T-61; FT 24 Nov plus FT-A1 to FT-A14 | design §13, §14 |
| Rollback | per-stage switch off, or tag checkout; the owner restarts | design §18 |
| Work packages | WP-1 to WP-7, each on its own branch | design §17 |

**Residual limits** (not blockers):
1. No tick history is stored. Intrabar and tick cases are tested with constructed streams.
2. Watcher events are not recorded live. The 24 Nov replay is a code replay, and the idea-to-opportunity matching above approximates the pierce candle. WP-6 computes it exactly.
3. The evidence for INV-1 and INV-2 is small: one live day for RSI stretch, four breaks for P-F7. It describes mechanisms, not outcomes.
4. The hourly bounce will trade only where the hourly band meets an STP zone (OD-23).
5. Breakout-type strategies are not gated (OD-03 as approved), and an STP-authorised trade can coexist with an opposite ungated one (OD-18 A).
6. OD-15 inert switches remain a separate investigation.

**Verdict:** the design is ready for implementation approval once OD-30 to OD-33 are decided. Implementation would follow WP-1 to WP-7 with every switch off. Then the offline tests and the WP-7 readiness pack. Then Stage A (observe-only), then Stage B on IG DEMO, each only with the owner's explicit approval.
