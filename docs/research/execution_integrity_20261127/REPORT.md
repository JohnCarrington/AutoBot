# Execution Integrity Remediation — Phase 1 (27 November 2026)

Branch `exec-integrity`, built from production `fc127e1` (deploy-23nov). **Not deployed.** Nothing in strategies,
STP, entry criteria, market-state assessment or trade-management methodology was changed. Commit references are in
section 9.

## 1. Summary

The 25 November 18:02 slow grind BUY was the bot's own trade at IG for four hours, unmanaged and unrecorded. It
lost £150.00 at IG's stop, and it let a second slow grind BUY open at 18:45. Three defects in the order sender caused
this. Two further defects meant some closes were recorded at the bot's own price instead of IG's. All five are
fixed on this branch. Each one is reproduced first by a functional test that fails on the production code and
passes after the fix.

IG's own records confirm the incident (read-only IG records check, 27 Nov 09:02 UTC, `ig_evidence_orphan_20261127.json`):

| | IG |
|---|---|
| Opened | 25 Nov 18:02:03 UTC, channel PUBLIC_WEB_API, deal reference **AB261125180203-7c0f9742** (the bot's), deal DIAAAAYXVXWHCBR |
| Fill / stop / limit | BUY 13120.5 / 13105.5 / 13140.5 |
| Closed | 25 Nov 22:00:00 UTC, SYSTEM (its stop), 13105.5 |
| Realised | **−£150.00** (IG transaction DIAAAAYXVX4K5A9) |
| Open positions now | none; funds £96,820.61 |

The brief's reference AB261125180204 is the order's sending second plus one: the full reference is AB261125180203-7c0f9742.

## 2. Preservation steps taken first

- Production: `/opt/autobot` on deploy-23nov at **fc127e1**, services started 27 Nov 06:38:50/51 UTC (dashboard PID 1374343, prices PID 1374370). No uncommitted bot-code changes in the working tree.
- Backup: `/home/autobot/backups/execution-integrity-20261127/`: a git bundle of fc127e1, `.env` (mode 600), a tarball of data/orders, data/records, data/trade_manager and data/trading, and SHA256SUMS.
- Branch: `exec-integrity` in its own worktree (`/home/autobot/worktrees/autobot-exec-integrity`); /opt/autobot was not touched.
- Baseline: full suite on a clean fc127e1 checkout (section 7).
- IG DEMO positions: **none open** (IG check above). Unresolved submissions: one, AB261125180203-7c0f9742, still held in the production sender's memory as unresolved ("still unresolved" at the 27 Nov 06:39 start-up).
- The only production touch: one read-only IG records check (the owner's existing request-file mechanism, four GETs, no order, no change). Its result is kept as `data/orders/ig_check_result.2026-11-27_orphan.json`; the previous request and result were kept under dated names.

## 3. Confirmed root causes

| # | Root cause | Evidence | Code path (fc127e1) |
|---|---|---|---|
| R1 | **IG accepted the order at once, but the bot looked for only about 9 seconds.** `GET /confirms/{ref}` was asked 5 times, 1 s apart, then 3 checks 2 s apart (confirmation, then open positions). IG answered 404 and its list of positions did not yet show the deal. The order was recorded "not found". No single check's answer was recorded, and an IG error was treated the same as "not there". | orders.jsonl 18:02:03 sending, 18:02:08 unclear "no confirmation", 18:02:12 not found; IG activity: opened 18:02:03 | `place` 577–580; `_settle_unclear` 627–650; `_confirmation` 478–492 (non-404 error returns None like 404) |
| R2 | **The regular check never looked at unresolved orders.** At 18:05:02 IG's open positions showed DIAAAAYXVXWHCBR carrying the bot's own deal reference. Only the start-up path compares positions with `unresolved`; the regular check called it "not ours … left alone". | orders.jsonl 18:05:02 "not ours", `deal_reference` AB261125180203-7c0f9742 | `reconcile` 391–418 (no `unresolved` lookup) vs `_recover` 267–271 |
| R3 | **Unmanaged as a result.** It was never in `self.trades`, so the trade manager never had it and the records never had it. The 20:30 UK close did not include it, and no stop or trail applied except IG's own attached stop. | trades.jsonl has no row; IG closed it at its stop at 22:00:00 | follows from R2 |
| R4 | **Unresolved orders were not counted by the safety rules.** `open_trades()` returned confirmed trades only, so "slow grind already has 1 trade open" did not apply, and the 18:45 slow grind BUY opened. Signal keys did include unresolved orders, but the 18:45 trade had a different signal. | orders.jsonl 18:45:04 opened DIAAAAYXV2V4GBW | `open_trades` 449–450; `safety/rules.py _limits` and `_risk` |
| R5 | **A delayed IG stop was recorded at the bot's reading.** When the trade manager expects IG's stop but IG has not closed yet, the later IG close (with IG's level and time) was discarded: `Trading._sync_ig` called `manager.closed_at_ig(ref)` without the order sender's answer. | 26 Nov 06:01 bounce: booked 09:20:00 / 13108.4 / +£45; IG 09:35:01 / 13108.9 / +£50 | `trading/engine.py _sync_ig`; `trade_manager/manager.py closed_at_ig` |
| R6 | **A close whose IG level was not yet in IG's activity was recorded at the bot's price as if it were IG's, and never looked for again.** | 18 Nov 12:37 EMA pullback SELL: booked 13169.0 / −£126; IG 13168.4 / −£120 | `closed_at_ig` 671–683; `_gone` 335–359; the unclear-close path in `_closed` |

**Other trades with the same failure.** The whole order journal (8–27 Nov, 162 orders) has exactly one "unclear", one "not found", one "not ours" and one "still unresolved", all for this order. No other order was lost. R5 and R6 affected the records of three trades (section 6).

## 4. Corrections implemented

| Requirement | Implementation |
|---|---|
| Persist enough before contacting IG | The "sending" record (written and fsynced before the POST, as before) now also carries `recovery`: the idea's entry price, market state, reason, steps and trend day (`Trading._recovery`). The take-profit and stop distance were already in it. |
| Confirmed rejection vs uncertain outcome | `_confirmation_state` returns accepted / rejected / absent (404) / error. An error is never taken as an answer. IG's activity is read by `details.dealReference`, and a REJECTED activity also counts as a refusal. |
| Reconcile uncertain submissions against positions, confirmations and IG's records | `_settle_unresolved`, at every regular check (after each candle) **and** at start-up, in this order: an open position carrying the reference; the confirmation; IG's activity. The deal ID then comes from the confirmation or the activity, and the position is checked by deal ID, so a lagging positions list cannot hide it. |
| Ownership of AutoBot's positions | Ownership is the deal reference the bot recorded before sending. A position carrying it is the bot's: it is adopted, never "not ours". A position with an AutoBot-format reference found in none of the records is **escalated and not adopted**. A position opened by hand keeps IG's own reference and is left alone, as before. |
| Recover the strategy and management context | The adopted trade gets IG's deal ID, fill and **IG's open time** (the position's `createdDateUTC` or the activity date) and the recorded `recovery` context. `Trading._take_recovered` puts it into the trade manager with the strategy's own plan (`plan(...)`, unchanged) and records it as opened once, with "recovered: …" in its reason. It is alerted. |
| Resume management safely | The recovered trade's stop and take profit are IG's, as sent; the trade manager runs it like any other open trade, including the 20:30 UK close (tested). If IG has no fill level, it is escalated and not managed. |
| Unresolved orders in duplicate and exposure protection | `open_trades()` includes every unresolved order (strategy, direction, actual stop distance, size), so every limit and the risk rule count it. A refusal names the order being counted. |
| Never resubmit an uncertain order | Unchanged: an order is sent once. Every new test asserts exactly one POST. |
| Settle an order IG never placed | It is recorded "not placed at IG" only when there is no position, the confirmation answers 404, and IG's activity (read without error, and not a full page) shows nothing for the reference `orders.unresolved_no_record_after_minutes` (30) after sending. Until then it is held and escalated. |
| Restarts and connection failures | Unresolved orders, recovery context, pending IG closes and adoptions are all rebuilt from the journal. A failed positions read changes nothing. Settlement at start-up uses the same rules as the regular check. |
| IG as the authority for realised results | R5: `manager.closed_at_ig(ref, found)` applies IG's level and time (the existing `_at_igs_level`). R6: every close records `level_source`, and the book row carries `price_source`. A close at the bot's price is looked for again at IG for `orders.ig_close_level_checks` (12) checks; found, a **"close corrected"** line is appended (never a rewrite); not found, it is escalated (IG statement needed). `apply_corrections` is used by `Book.closed_trades` (and so the daily and weekly summaries) and by the dashboard's history. Half-closed trades keep the half and correct the rest. |
| IG's activity paging | `_ig_close_of` reads IG's activity in 3-hour windows, newest first, then forwards from the open. A trade with more than 50 activities, or a close found days later, is no longer missed. |

Files: `orders/sender.py`, `trading/engine.py`, `trade_manager/manager.py` (one method), `records/book.py`,
`dashboard/server.py` (the history reader), `config/settings.toml` and `config/settings_loader.py` (two settings),
`docs/SETTINGS.md`, `docs/DESIGN.md`. The strategies, STP, the entry filters, the analyser, the safety rules and
the trade manager's methodology are unchanged.

## 5. Tests: before and after

New: `tests/functional/test_order_reconciliation_20261127.py`, 17 tests.

| Brief item | Test |
|---|---|
| The 25 Nov defect (reproduced) | `test_the_25_november_order_ig_accepted_late_is_adopted_by_the_regular_check_not_called_not_ours` |
| Duplicate entry while unresolved (the 18:45 trade) | `test_while_an_order_is_unresolved_the_same_strategy_cannot_open_another` |
| IG stop while disconnected / restart during an uncertain submission | `test_an_unresolved_order_ig_opened_and_stopped_while_unknown_is_recorded_from_igs_activity_at_start_up`, `test_after_a_restart_an_order_ig_opened_and_stopped_meanwhile_is_recorded_opened_and_closed_once`, `test_an_order_settled_days_later_is_recorded_from_igs_own_open_and_close` |
| Delayed confirmation / confirmation temporarily not found | `test_a_confirmation_that_answers_404_then_accepted_is_adopted_even_while_igs_position_list_lags` (plus the existing `test_no_confirmation_yet_then_accepted`) |
| Accepted despite a network timeout | existing `test_a_timeout_is_checked_by_its_reference_and_never_sent_again`, `test_a_timeout_found_only_among_the_open_positions` |
| An order IG never placed | `test_an_order_ig_has_no_record_of_is_held_until_igs_own_records_settle_it`, `test_a_full_page_of_igs_activity_never_counts_as_ig_having_no_record` |
| Recovery of an orphaned position, management resumed | `test_a_recovered_order_is_managed_by_the_trade_manager_and_recorded_with_its_strategy` |
| Manual positions / unknown AutoBot reference | `test_a_position_with_an_autobot_reference_not_in_the_records_is_escalated_not_adopted` (plus the existing not-ours tests) |
| Idempotent reconciliation | `test_reconciliation_is_idempotent_one_adoption_one_trade_across_checks_and_restarts` |
| Context persisted before IG is contacted | `test_the_recovery_context_is_recorded_before_ig_is_contacted` |
| Requested, calculated and actual prices | `test_the_requested_calculated_and_actual_prices_are_all_kept` |
| Delayed IG stop at IG's level (26 Nov) | `test_a_stop_ig_fills_after_the_bot_expected_it_is_recorded_at_igs_level_and_time` |
| IG level known only later; summaries | `test_a_close_whose_igs_level_is_not_known_yet_is_corrected_from_igs_activity_later` |
| Partial closes | `test_a_correction_of_a_half_closed_trade_keeps_the_half_and_corrects_the_rest` |
| Dashboard history | `test_the_dashboard_history_reads_the_corrected_figures` |
| Existing trade-management behaviour | the full existing suite (section 7) |

**Before the fix** (`tests_before_fix.txt`, run on the production code with the recovery argument stripped where
the old code lacks it), the defects reproduce exactly:

- the late position recorded "not ours";
- a second slow grind **sent** while the first was unresolved;
- "still unresolved" at the restart, although IG had opened and closed it;
- no opened row for the recovered order;
- the delayed stop booked at 13415.5 (the bot's) instead of IG's 13416.3;
- no `price_source` and no correction.

**After the fix:** all 17 pass.

## 6. Historical reconciliation (nothing rewritten)

`history_check.py` (read-only; output in `history_check_output.txt`) compares every closed record with IG's own records from the owner's saved IG checks and the journal's IG levels:

- **160 closed bot records; 148 with IG evidence; 3 differ from IG:**

| Trade | Recorded | IG | Cause |
|---|---|---|---|
| AB261111065505-6d002d16, Bollinger bounce BUY, 11 Nov | 07:30:00, 13336.2, +£1.00 | 07:35:01, 13332.8, **−£33.00** (IG transaction) | bot close booked at the manager's price; an early build, missed by the 11 Nov correction |
| AB261118123737-487acb12, EMA pullback SELL, 18 Nov | 13:07:56, 13169.0, −£126.00 | 13:07:56, 13168.4, **−£120.00** | R6 |
| AB261126060101-987e099b, Bollinger bounce 5m BUY, 26 Nov | 09:20:00, 13108.4, +£45.00 | 09:35:01, 13108.9, **+£50.00** | R5 |

- **Missing entirely:** AB261125180203-7c0f9742, slow grind BUY, 25 Nov, **−£150.00** (IG-confirmed, section 1).
- **No IG evidence saved (12 records, 20–24 Nov):** listed in `history_check_output.txt`. They need the owner's IG statement, or approved read-only IG checks for those dates.

**On the first start-up of this branch**, the order sender will settle AB261125180203-7c0f9742 from IG's activity by itself. It will adopt it, record its IG open and close, and the engine will book it as opened at 13120.5 and closed at 13105.5 (25 Nov 22:00:00, −£150.00, `price_source` IG's activity). That brings the 25 Nov and week figures in line with IG. The owner will get the "order recovered", "gone at IG", trade-opened and trade-closed messages for it. The three differing records are **not** changed automatically. Correcting them (append-only "close corrected" lines at IG's figures, with backups) is an owner decision.

## 7. Regression results

| Run | Result |
|---|---|
| Baseline: production fc127e1, clean checkout, full suite | **2783 passed, 3 skipped** (15 min 05 s) |
| Branch, first full run (pre-commit hook) | 2803 passed, **1 failed**: `test_stp_review_20261125.py::test_R6_rule_3_is_bypassed_only_for_an_stp_authorised_entry` calls `Trading._place` on a stand-in object; the recovery context became a module function (`recovery_of`). The commit was blocked as intended. |
| Branch, final full run (pre-commit hook of this commit) | all tests passed (2807 collected: 2783 existing + 17 new + 7 others counted from the branch, 3 skipped); the hook blocks a commit on any failure |

An earlier full run during this work showed 85 failed and 919 errors. That was not the code: two pytest runs shared
pytest's default temporary folders, and the second one cleared the first's (the clash recorded on 13 Nov). Every run
above used its own temporary folder.

## 8. Remaining risks and open items

- IG's activity is assumed complete within 30 minutes of an order (IG writes every API order as ACCEPTED or REJECTED activity). A full page never counts as absence.
- A position with an AutoBot-format reference in none of the records is left unmanaged by design (escalated). It would need the owner's decision.
- An unclear **half** close whose level IG did not give is not yet looked for again (the full-close path is). Only the range trade half-closes.
- An unresolved order blocks its strategy for up to 30 minutes when IG has no record of it. This is intended.
- The 12 records without IG evidence and the three differing records above are unchanged.
- The deployment start-up sends Telegram messages for the 25 Nov recovery (expected, once).

## 9. Deployment and rollback (owner's approval needed; not done)

Deploy:

1. Owner stops both services.
2. Back up `.env`, `data/orders`, `data/records` and `data/trade_manager`.
3. `git -C /opt/autobot merge --ff-only exec-integrity` (deploy-23nov is fc127e1, the branch's base).
4. No `.env` change; the two new settings are in settings.toml.
5. Owner starts both services.

Post-checks:

- orders.jsonl at start-up: "adopted" and "gone at IG" for AB261125180203-7c0f9742, with ig_level 13105.5 and `level_source` IG's activity.
- trades.jsonl: one opened and one closed row for it (−£150.00).
- No "still unresolved" and no "not ours".
- 0 open positions.

Rollback: stop, `git -C /opt/autobot reset --hard fc127e1` (tag `pre-exec-integrity-20261127`), start. The old code reads the new journal and records safely: it ignores "close corrected" lines, `level_source`, `price_source` and "not placed at IG"; it understands "adopted" and "gone at IG". The backup above restores the data if wanted.
