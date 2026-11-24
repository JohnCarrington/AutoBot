# STP strategy integration: implementation readiness pack (WP-7)

**Status:** IMPLEMENTED ON ISOLATED DEVELOPMENT BRANCHES, for independent review. **Not merged, not deployed, nothing
switched on.** No production configuration was changed, no service was restarted, no IG order was sent. Deployment and
IG DEMO activation need the owner's separate explicit approval.

| | |
|---|---|
| **Design** | `docs/design/STP_STRATEGY_INTEGRATION_20261124.md` revision 3.2 (design branch, review corrections dbcffef) |
| **Base** | `63d9c04`, the live build |
| **Branches** | stacked, one commit each, from 63d9c04: `stp-integration/wp1-tracker` 1c4a37d → `wp2-bidirectional` 5f1f7a0 → `wp3-levels` c5a184c → `wp4-authorisation` 8792e5b → `wp5-dashboard` 6792d83 → `wp6-tests` 187965d → `wp7-readiness` (this pack; its SHA is in the hand-over message). Each commit's pre-commit hook ran the full suite on that branch's own files and passed. |
| **Governing principle** | STP determines WHERE to trade; the existing strategies determine WHEN |

---

## 1. What was built

| WP | Files | What |
|---|---|---|
| WP-1 tracker | `planner/opportunities.py` (new), `planner/__main__.py`, `config/switches.py`, `config/settings_loader.py`, `config/settings.toml`, `.env.example`, `docs/SETTINGS.md`, `tests/technical/test_settings.py` | `OpportunityKeeper`, a subclass of the existing tracker that reuses its 5-minute checks, creation, update and duplicate rules unchanged. It holds a list of opportunities. A new forecast adds and never ends (OD-01, OD-02). Supersede only for the same identity, keeping the lineage. No demotion. BROKEN on a confirmed break; Watch & Wait back at the first close inside within P-F7 = 3 (OD-31). 4-hour structure-break check. Pivot rollover: daily or weekly fixed levels gone → INVALIDATED. Picked by `STP_OPPORTUNITIES`; off → the single tracker, untouched. The three switches and `[stp_authorisation]` are added, all OFF. |
| WP-2 bidirectional | `planner/assess.py` | `assess(..., trade="SELL"/"BUY")`: every approved criterion unchanged; the 4-hour direction and condition recorded as context (`relation_to_h4`). With `trade=None` (the switch off), the plan is exactly as before (T-03). |
| WP-3 levels | `stp/__init__.py`, `stp/source.py`, `stp/levels.py` (new), `strategies/replay.py`, `strategies/bollinger_bounce_5m/strategy.py`, `strategies/level_reversal/strategy.py`, `rejection/watch.py` | Live zones (edges and in-zone fixed levels, OD-26) in the strategies' level copy only. Each zone is its own group, not lined up. Level Reversal: STP-zone levels alongside S2/R2/00 (OD-28), allowance to the far edge + 3 pips (OD-27), stop and TP unchanged. The rejection-candle context field (5m bounce, LR) only while on. The watcher keeps an STP level's zone edges on its pierce (only STP levels carry them). |
| WP-4 authorisation | `stp/gate.py`, `stp/authorise.py` (new), `trading/engine.py`, `strategies/common.py`, `strategies/entry_filters.py`, `safety/rules.py`, `orders/sender.py` | The check in `_place` after the try is recorded: switch dependencies, freshness, interaction, catch-up (unseen 5m candles, the forming candle, the tick, unseen hourly and 4-hour closes), zone-break entry, oldest-first binding, key `<lineage>#t<n>`. The bypasses for STP-authorised gated ideas only: analyser state, rules 1, 2b (RSI stretch, OD-30), 3 and 9. Rule 11 two-part key (OD-32). The level cache is renewed on an STP file change. The trading process imports no planner code while the switch is off (the existing isolation test). |
| WP-5 dashboard | `dashboard/stp.py`, `dashboard/static/stp/stp.js` | STP tab: the list of tracked opportunities with status (Watch & Wait label), zone, class, primary, zone break, 4-hour relation. Read only; shown only when the file has the list. |
| WP-6 tests | `tests/stp/harness.py`, `tests/technical/test_stp_integration.py`, `tests/functional/test_stp_integration_20261124.py` | T-01 to T-66; the 24 Nov journey; FT-A1 to FT-A18; FT-R1 (below) |
| WP-7 | this folder | test results, regression comparison, functional evidence |

**New numerical parameters: none.** Reused: `rejection.near_level_within_pips` 3, `planner.break_beyond_pips` 3,
`planner.failed_breakout_within_candles` 3, `analyser.out_of_date_after_minutes` 10, and the strategies' own settings.
The new settings are two name lists (`stp_authorisation.strategies`, `bypass_filters`).

**Switches (OD-29), all OFF if left out:** `STP_OPPORTUNITIES`, `STP_BIDIRECTIONAL`, `STP_AUTHORISES_ENTRIES`.
- `STP_AUTHORISES_ENTRIES` refuses every gated idea unless the other two and `ONE_SIGNAL_ONE_TRADE` are on (T-39, T-43).
- A missing or damaged STP file refuses (T-38). The STP code never stops the price service: it runs in the planner subprocess, and the check only reads.

---

## 2. Test results

| Run | Result |
|---|---|
| Full suite, integration branch (`pytest -q`) | first run 2,723 passed, 1 failed, 3 skipped; the failure (a settings object without switches reaching the new tracker selector) was fixed. Then **every WP commit's pre-commit hook ran the whole suite on that branch's own files and passed** (WP-6: the complete code and all STP tests). |
| STP technical tests T-01 to T-66 (`tests/technical/test_stp_integration.py`) | 64 test cases, **all passed** (`stp_tests_verbose.txt`) |
| STP functional tests (`tests/functional/test_stp_integration_20261124.py`) | 30 test cases **passed**; the 3 opt-in full-path cases (FT-A15, FT-A16, FT-A18; `STP_FULL_REPLAY=1`) **passed** (`full_replay_tests.txt`, 16 min) |

**Coverage of the design's test list:**

| Ids | Where |
|---|---|
| T-01 to T-47, T-58 to T-65 | one test (or a parametrised test) each |
| T-50/T-51/T-54, T-52/T-57, T-53/T-66 | combined tests, named with all their ids |
| T-48 (all off, byte-identical) | the cross-commit regression replay (§3); it cannot run inside one commit's suite |
| T-49, T-55 (analyser and trade manager never read STP) | source checks, plus FT-A16 (identical analyser states) |
| T-56 (journey to an order) | FT-R1-b: idea → `_place` → STP → filters → order sender (paper) → opened, plus the switches-on full replay (§4) |

---

## 3. Regression: all switches off is byte-identical to the live build

**Method:** the whole bot in candle mode over the week to 24 Nov 21:00 (Sunday 22:00 open; analyser, every strategy, entry filters, safety rules, order sender in paper mode with a pretend IG, trade manager).
- **Settings:** the live `settings.toml`, and the 24 Nov `.env` switch values with TRADING off.
- **Builds compared:** the live build 63d9c04 (`/home/autobot/worktrees/stp-base`, detached) and the integration branch with every STP switch off.
- **Scripts:** `replay_day.py`, `compare_records.py`.

**Result** (`regression_switches_off_vs_live_build_63d9c04.txt`):

| File | Lines | |
|---|---|---|
| `records/GBPUSD/paper/decisions.jsonl` | 683 | identical |
| `records/GBPUSD/paper/trades.jsonl` | 46 | identical |
| `orders/GBPUSD/paper_orders.jsonl` | 150 | identical |
| `trade_manager/GBPUSD/decisions.jsonl` | 47 | identical |
| `trade_manager/GBPUSD/open_trades.json` | 1 | identical |

**BYTE-IDENTICAL.** The order sender's deal references contain a random part by design (`secrets.token_hex`). They are replaced by their order of first appearance; nothing else is changed. 23 paper trades in each.

---

## 4. Functional evidence: 24 November 2026

### 4.1 STP's tracker on the recorded candles (`tracker_journey_20261124.txt`)
Both directions on, run after every 5-minute candle from 23 Nov 23:55 to 24 Nov 20:55 (82 s offline). Checked by the journey tests:

| As of | Result |
|---|---|
| 00:00 | the zone on 23 Nov's pivots INVALIDATED "structural levels changed: daily S2 13062.0, previous day low 13071.5 no longer in the level map" |
| 08:00 | the 00:00 SELL 1.30750–1.30841 **kept** (§5, finding 1) |
| 10:00 | SELL **and** BUY at 1.30621–1.30715 (OD-33); the BUY completed at 11:05 |
| 12:00 | the pivot-area SELLs BROKEN; INVALIDATED "confirmed break held" at 15:00. STP's BUY at the broken resistance 1.30750–1.30854 proposed (continuation by STP's own proposal, `relation_to_h4` against) |
| 14:00 | R1 SELL 1.31030–1.31141: Watch & Wait from 14:10; kept at 15:00 and 17:00 (H11, which the live single tracker superseded) |
| 18:00 | R1 BROKEN; 19:00 **back to Watch & Wait, same id** (OD-31) |
| 17:00 / 18:00 | weekly-pivot SELL 1.31176–1.31286; BUY 1.31191–1.31286 published 18:00:03 |
| all day | no opportunity ended for a new forecast, a 4-hour direction change or time |

### 4.2 The full wired path with all three switches on (`switches_on_decisions_20261124.txt`)
The same candle-mode replay with the tracker running 3 s after each candle (its file read as it stood at each moment).

**Refused by STP: 36 gated ideas with no matching opportunity, including:**
- every 5m bounce BUY in the 00:00–09:50 range;
- the Level Reversal BUYs at 14:35–14:45 and 15:30 (the 15:30 one opened live);
- the 13:20–13:32 SELLs (the 13:32 Level Reversal SELL opened live).

**Authorised by STP: 25 ideas, of which 6 opened (paper) and the rest were refused by rule 11, a position limit or the trading hours:**

| Time | Ideas | Opportunity |
|---|---|---|
| 10:05 | BUY | the pivot BUY |
| 10:35 | hourly bounce and 5m bounce SELL; RSI stretch not applied (OD-30); one trade, the second refused by rule 11 | the pivot SELL |
| 12:35 | BUYs | the continuation BUY at the broken resistance |
| 15:15 | R1 SELL | R1 SELL |
| 18:00 | BUY | B1800 (§5, finding 3) |
| 18:20 | SELL | the weekly-pivot SELL |

**Duplicate keys:** every later confirmation in the same test was refused by rule 11, for example 10:50, 11:00, 12:45, 15:40, 16:35, 16:50 and 18:35–19:00.

**Unchanged:**
- **Analyser:** all 69 state changes identical, STP off against on.
- **Ungated strategies:** all 147 records identical, deal references aside. That includes every EMA pullback record (H15).
- **RSI stretch:** still refuses ungated ideas, for example the 14:15 New York open reversal.
- **Trading hours:** still refuse, for example the 20:40–20:50 SELLs.

28 paper trades against 23 with STP off. **No profit or loss is computed or claimed: the live IG demo is the judge.**

### 4.3 FT-R1: the hourly publication race (the real engine's live path, constructed ticks)
- **R1-a:** a trigger at 18:00:01, before the 18:00:03 publication, is **STP refused** once. The later ticks of the same candle make **no second try**, nothing is queued, and nothing is sent at the close.
- **R1-b/c:** the same setup triggering at 18:00:05 is **authorised** against B1800 and opened (paper), key `…1800-11#t1`.
- **R1-d:** a new setup after publication (18:35) is authorised.
- **R1-e:** the level-cache renewal is covered by T-65.

---

## 5. Findings, corrections and deviations

1. **Design §14.2, 08:00 expectation corrected.**
   - The design expected the 00:00 SELL "INVALIDATED (destination before entry), same as today". The live single tracker in fact ended it with "supporting evidence changed": the 08:00 re-plan found a nearer Major zone, 1.30266–1.30373, already reached.
   - Its own primary destination, 1.30169, was never reached. Under OD-02 it is therefore **kept**, and the implementation keeps it.
   - It then broke at 12:00 and ended at 15:00 "break held". The test asserts the corrected expectation.
2. **Watcher pierce record.**
   - Level Reversal needs the STP zone's edges for OD-27, but the watcher keeps only name and price for each pierced level. An STP level's pierce now also carries `zone`. Every other pierce is unchanged: the analyser's watcher never sees STP levels (byte-identical regression, FT-A16).
   - The first switches-on replay hit this as a `KeyError` before the fix.
3. **Candle mode cannot order a trigger against the publication.**
   - In the candle-mode replay, the 18:00 5m bounce BUY is processed at the 18:05 close, after the 18:00:03 publication, so it is authorised.
   - Live, it depends on the trigger tick. FT-R1 tests both orderings with the real live path; the live record has no tick.
4. **Pivot rollover:** `daily_or_weekly` in a zone's levels is a flag (true/false). The first implementation compared it with words and missed the rollover; caught on the 24 Nov run and fixed.
5. **Settings without switches** (existing technical tests) reached the new tracker selector; every new switch read is now tolerant (treated as off).

---

## 6. Remaining limitations

1. **No tick history is stored.** Intrabar and tick behaviour are tested with constructed ticks (T-32, T-33, FT-R1). The day replays are candle-level.
2. **The full wired-path functional tests take several minutes,** so they are opt-in (`STP_FULL_REPLAY=1`) and are not part of the pre-commit run. The regression comparison runs across two commits and is a script, not a suite test.
3. **The dashboard script could not be syntax-checked by machine** (no JavaScript runtime on this host). It was reviewed by hand; the server side is tested (FT-A17).
4. **Pre-commit coverage:** each WP branch's hook ran the full existing suite on that branch's own files. The STP tests exist from WP-6 on, so WP-1 to WP-5 were checked against the existing suite only.
5. **Evidence is one recorded day.** Behaviour is shown, not outcome. The hourly bounce trades only where its band meets a zone (OD-23). Breakout-type strategies are not gated (OD-03 as approved).
6. **Not done, by instruction:** merge, deployment, production configuration, service restarts, IG orders, and the OD-15 inert-switch investigation.
