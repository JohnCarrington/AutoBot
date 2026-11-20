# STP structural-history correction — 20 November 2026

Branch `stp-structural-history-20261120`, built on `stp-diagnosis-20261120`. That branch is production `26c06fc` plus the
dashboard notation fix. Isolated work only: production was not modified, no service was restarted and IG was not
contacted.

## Summary

- **Built:** the researched zone-retention fix (9210ca5, unchanged) and historical daily-swing discovery that is
  independent of the 48-week window.
- **Unchanged:** direction, the deployed `dominant_structure()` (candidate C), the recommendation lifecycle, the Major
  destination requirement and the already-reached (D-1) rule.
- **18–20 Nov:**
  - The correction turns 3 of production's 17 "no Major support" hours into plans: 19 Nov 21:00 and 20 Nov 07:00 and
    08:00.
  - The 19 Nov 21:00 plan ended "destination reached before entry". The 20 Nov 08:00 plan is still open (see the
    replay section).
- **History** (2,778 four-hourly decisions, Jan 2025 – Nov 2026):
  - **Accuracy:** not demonstrably improved. The edge against the random-walk expectation moves from −1.6 to −1.0
    points; the paired difference is **+0.6 points (95% interval −1.0 to +2.4)**.
  - **Frequency:** the number of plans falls slightly, from 919 to 906.
  - **New plans:** the 31 plans the history adds score +10 points (−4.9 to +23.9). That is too few to conclude
    anything.
- **Deployment:** not recommended as a forecasting improvement. It is technically ready and safe, and could be
  deployed as a map-completeness change if the owner wants destinations at fresh extremes (see the readiness section).

## Exact changes

| Commit | File | Change |
|---|---|---|
| 1a7bdde (cherry-pick of 9210ca5, the owner's) | planner/zones.py | `zones()` no longer clips zones to 150 pips from price. The 150 pips now limits only round-number discovery. |
| 1b039eb (cherry-pick of 8ddcabd) | tests/test_stp_structural_zone_horizon_20261120.py | Its 2 tests. |
| this commit | planner/zones.py | New `historical_swing_levels()`; `level_map()` adds its levels (see below). |
| this commit | config/settings.toml, config/settings_loader.py | New `[planner] historical_daily_swing_lookback_weeks = 156` (0 turns it off; validated range 0–1040). |
| this commit | tests/technical/test_settings.py | The new key. |
| this commit | tests/functional/test_stp_structural_history_20261120.py | 5 tests (below). |
| this commit | research/stp_structural_history/ | replay_nov.py (keeper replay), compare_nov.py, evaluate.py (A/B/C on history), analyse.py. |
| this commit | research/stp_validation/ | score.py and calibration.py, copied unchanged from stp-conditional-journeys-20261120 (the 20 Nov validation's scorer). |

**How historical discovery works:**
- It takes daily swings found by the existing rule (3 candles each side, 110 pips within 6) that started more than 48
  weeks and at most 156 weeks before the assessment.
- Only swings whose `known_utc` is at or before the assessment time count, so nothing from the future leaks in.
- Each becomes a level named "historical daily swing low/high", with the same family (higher-timeframe structure) and
  daily-or-weekly status as recent daily swings.
- It never feeds the direction. The 48-week recent window (P-B9) is unchanged.

**Not included:**
- bb9d1fd (destination_hierarchy.py ADR horizon): that module is not in production and was not part of this brief.
- c629228 (rejection audit): it is superseded here by the keeper replay, which also covers the lifecycle.

## Replay of 18–20 November (production candle store, read only)

The real keeper ran every 5 minutes from 17 Nov 20:25 to 20 Nov 09:00, three times:
- **A:** production code.
- **B:** the retention fix only.
- **C:** retention plus historical swings.

**Check of A against the live log:** 17 of the 18 comparable hours since the 19 Nov 15:00 deployment are identical. The
19:00 difference is timing: live analysed at 19:05 because the hourly candle arrived late. Before 15:00 the live log
differs because live still ran the older code.

**Results:**
- **B equals A in every hour.**
- **Direction and condition are identical in every hour across A, B and C.**

C differs from A in two ways (the full hourly table is in november_replay_hourly.txt).

**1. Hours where A had no Major support and C issues a plan**

| Hour | C plan | What price did next |
|---|---|---|
| 19 Nov 21:00 | SELL 1.31355–1.31399, primary 1.30922 | destination reached before entry (21:10) |
| 20 Nov 07:00 | SELL 1.31355–1.31457, primary 1.30841 | superseded at 08:00 |
| 20 Nov 08:00 | SELL 1.31112–1.31219, primary 1.30841 (historical daily swing low, 12 Nov 2025); invalidation: hourly close at or above 1.31249, or 4-hour close at or above 1.31749 | entered at 08:05; low 1.30979 by 10:23, 14 pips short; no break; **open** |

The other 14 hours stay "no Major support" in C (19 Nov 16:00–17:00 and 22:00–20 Nov 03:00, plus 18 Nov 20:00 and
19 Nov 04:00–07:00). The older lows added below price (1.30373, 1.30097) only form Moderate zones (two families).
At 19 Nov 19:00 both A and C issue a plan (C's primary is nearer, 1.30948 against 1.31000); both end "destination
reached before entry". At 19 Nov 20:00 C's nearer primary is already reached (D-1).

**2. Hours where an old swing near price changes an existing plan**

The Dec 2025 swing low 1.31796 and the May and July 2025 swing lows 1.31394 and 1.31397 change several plans. On 18 Nov 01:00–07:00 the
primary moves from 1.31728 to 1.31897, a nearer target. That target was reached sooner (rec completed 04:15 instead of
07:10), and the later hours become D-1 refusals.

**Keeper output:**
Recommendations issued from 18 Nov:
- **A, 8:** 5 completed, 2 invalidated (a confirmed break, changed evidence), 1 ended "destination reached before
  entry".
- **C, 11:**
  - 5 completed (the 18 Nov 03:00 one with the nearer 1.31897, earlier);
  - 2 invalidated (the same two);
  - 2 ended "destination reached before entry" (19 Nov 19:00 and 21:00);
  - 1 superseded (20 Nov 07:00);
  - 1 open (20 Nov 08:00).
- The completed count is equal; C's extra recommendations so far add two "destination reached before entry" endings
  and one open position.

## Historical test: accuracy versus frequency

- **Data:** the validated research store (2024–Nov 2026), so that a 48-week window plus older history exists for every
  decision.
- **Decisions:** 4-hour UTC boundaries from 1 Jan 2025 to 19 Nov 2026. 2,946 were taken and 2,778 had fresh data.
- **Method:** each snapshot is assessed by A, B and C before any outcome is looked at.
- **Check of A:** it equals production `plan_at` at the sampled timestamps (2025-03-12 08:00, 2025-08-05 20:00 and
  2025-11-20 16:00).

**Outcome measure** (as in the 20 Nov validation):
- From the plan's price, is the primary destination touched before the zone-break level?
- Edge = observed rate minus the random-walk expectation z/(d+z).
- 95% intervals come from a weekly-block bootstrap.

| Group | Plans | Destination before zone break | Expected | Edge (pts, 95%) | Entry → destination | Median destination (pips) |
|---|---|---|---|---|---|---|
| A, all | 919 | 43.9% | 45.5% | −1.6 (−4.7, +1.7) | 39.7% | 13.9 |
| B, all | 924 | 43.6% | 45.3% | −1.7 (−4.7, +1.6) | 39.4% | 13.9 |
| C, all | 906 | 44.2% | 45.2% | −1.0 (−4.2, +2.2) | 41.3% | 13.3 |
| same in A and C | 684 | 44.5% | 45.2% | −0.7 (−4.5, +3.0) | 40.1% | 14.0 |
| changed: A's version | 191 | 40.9% | 45.4% | −4.5 (−11.6, +2.2) | 35.6% | 14.5 |
| changed: C's version | 191 | 43.1% | 46.8% | −3.7 (−10.7, +3.1) | 43.6% | 10.7 |
| new in C | 31 | 43.3% | 33.3% | +10.0 (−4.9, +23.9) | 59.1% | 15.6 |
| dropped by C (A's plan) | 44 | 46.5% | 49.8% | −3.3 (−17.6, +11.5) | 50.0% | 12.4 |
| new in B (retention only) | 5 | 0 of 5 | 13.5% | −13.5 | 0% | 177 |

**Paired difference, C minus A:** +0.6 points (−1.0, +2.4). Against the 4-hour structure-break level: A −0.7, C −0.1
(both inside ±5). Results by period:
- A's edge is −4.3 in DEV (Jan–Jun 2025) and −0.5 in TEST.
- C's edge is −3.8 in DEV and +0.3 in TEST.
- New-in-C plans score +13.2 in DEV (n 6) and +9.2 in TEST (n 25).

**What the numbers mean:**
1. **Frequency did not rise.** C makes 31 new plans but drops 44: older swings near price make nearer primaries that
   are already reached (the D-1 rule, unchanged). "No Major destination" refusals fall from 63 to 54.
2. **Accuracy did not measurably improve.** The whole-system edge stays at chance in both periods, and the paired
   difference interval includes zero.
3. **The only positive sign is the 31 new plans:** +10 points, with an interval that includes zero, and the same sign
   in both periods. It is too small a sample to act on.
4. **Retention alone (9210ca5)** adds 5 plans with distant destinations (median 177 pips). All 5 were invalidated after
   entry. It changed no 18–20 Nov hour. It is harmless but adds nothing measurable.
5. **Changed plans get nearer destinations** (median 10.7 against 14.5 pips). The 20 Nov validation found that near
   destinations are the main weakness, and these are no better than chance either.

## Tests

- New: 5 structural-history tests and the 2 cherry-picked retention tests. The real-store test reproduces the live
  20 Nov 08:00 failure: without history, "no Major support"; with it, a SELL whose primary is Major and contains
  "historical daily swing low 13084.1". Direction and condition stay identical.
- STP-related suites: 944 passed before the new file, plus the 5 new tests.
- Full suite: the first run gave 2,313 passed and 1 failed, because the new setting was not yet in docs/SETTINGS.md.
  After documenting it, the pre-commit hook ran the full suite again and every test passed (2,314) before this
  commit was accepted.

## Deployment readiness

- **Technically ready:**
  - one parameter, which can be set to 0 to turn it off;
  - no change to direction, lifecycle, Major or D-1;
  - the full suite passes;
  - it needs a planner run only (the planner is a fresh subprocess every 5 minutes), plus a dashboard restart for the
    included notation fix.
- **Not recommended as a forecasting improvement.** The evidence shows no measurable gain in accuracy, and frequency
  does not rise.
- **What it does deliver:** a structural map at fresh 48-week extremes. On 20 Nov it yields a destination where
  production yields none.
- **Owner decisions:**
  - (a) whether the new parameter (156 weeks, provisional) and the end of the 150-pip clip are approved as a
    map-completeness change;
  - (b) whether to wait for the 31 new-plan cases to grow (live observation) before judging them.
