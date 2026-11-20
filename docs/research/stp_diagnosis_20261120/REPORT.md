# STP urgent diagnosis — 20 November 2026

Read-only investigation of production, plus isolated development on branch `stp-diagnosis-20261120`, built from
production's checkout `26c06fc`. Nothing in production was changed, restarted or deployed. IG was never contacted.

## A. Current operational status

| Question | Answer | Evidence |
|---|---|---|
| Is STP running? | **Yes.** `autobot-prices` starts `python -m planner run` after every 5-minute candle (planner/keeper.py `PlannerUpdater`); PLANNER_OBSERVE=on. | current.json `last_run_utc` 08:10:03Z, written 08:10:03 |
| Last assessment | **20 Nov 08:00:04 UTC**, from fresh data (market data 08:00:00Z, `data_fresh` true). | current.json `last_analysis_utc` |
| Missed hourly analyses since 17 Nov 20:00 | **None.** 61 analyses, one every hour. | recommendations.jsonl |
| Last directional forecast | **08:00 today: BEARISH, CORRECTION_ACTIVE, SELL, "UP into resistance, then DOWN".** Every hour since 19 Nov 15:00 has a direction. | recommendations.jsonl |
| Last recommendation issued | **18 Nov 03:00 UTC** (STP-GBPUSD-20261118-0300-7, completed 07:10). | issued.jsonl, last written 18 Nov 03:00 |
| Dashboard | **Current.** The STP overview, computed in-process from the production files, gives freshness CURRENT, last analysis 08:00:04, BEARISH, "NO RECOMMENDATION" and the planner's reason. | `dashboard.stp.overview` |
| Errors | None. planner.log is empty; no planner or STP lines in prices.log or dashboard.log. | logs/ |
| Locks / waits | The `.lock` is taken per run and released (fresh every 5 minutes). No state is waiting on anything. | data/planner/GBPUSD |

All seven stages work: market data, structure, scenario, destination selection, prediction, persistence and dashboard.
Re-running `plan_at` in memory on the production store for 04:00, 06:00, 07:00 and 08:00 today reproduces the live
outputs exactly, so there is no stale cache or hidden state.

## B. Root cause: why there have been no recommendations since 18 Nov 03:00

STP is not stuck. Each hour it completes the analysis and then **declines to issue a recommendation under an
approved rule**, with the reason written down:

| Hours | Reason (the planner's own words, abridged) | Rule |
|---|---|---|
| 18 Nov 08:00 – 19 Nov 14:00 (31 h) | direction NEUTRAL: mixed 4-hour swings (a 3.4-pip wick higher high) | design 6.3; corrected and deployed 19 Nov 14:57 (candidate C) |
| 19 Nov 15:00, 18:00, 19:05 | the primary destination is already reached (D-1) | D-1 correction, 18 Nov |
| 19 Nov 16:00–17:00, 20:00 – 20 Nov 03:00, 07:00 – 08:00 (14 h) | **no Major support zone below the entry zone within the 150-pip window** | D-18/D-19: primary = first Major zone |
| 20 Nov 04:00 – 06:00 | condition INDETERMINATE: "the evidence does not fit one condition" | D-10 |

**The current blocker.** On 19 Nov GBP/USD fell to 1.30770. That is its lowest level since 21 Nov 2025 (about 52 weeks), and below every daily swing inside the planner's 48-week look-back (`[planner] daily_swing_lookback_weeks
= 48`, owner-approved P-B9). Below price there are only pivots, round numbers and session levels:

| Zone | Class | Families |
|---|---|---|
| 1.30922–1.31000 | Moderate | session, psychological |
| 1.30770–1.30775 | Moderate | session, structure |
| 1.30500–1.30513 | Moderate | pivot, psychological |
| 1.30172–1.30279 | Minor | pivot |
| 1.30000 | Minor | psychological |

A Major zone needs three families including a daily-or-weekly level (P-C7), so none qualifies. The code behaves
exactly as specified (planner/assess.py, lines 425–433).

**Why it happens.** The supports a chartist would mark here are a year old:

- the daily swing lows of 12 Nov 2025 (1.30841), 4 Nov 2025 (1.30097) and 20 Nov 2025 (1.30373);
- the March 2025 daily swing highs at 1.29918 and 1.30142.

The 48-week window drops them just as price returns to them. The register warned about exactly this ("too short
forgets levels price may return to"). In my historical validation this reason stopped 1.8% of 4-hourly decisions
(75 of 4,254), always at fresh multi-month extremes.

**Evidence that this is the trigger** (in-memory replay of the 08:00 plan, nothing saved or deployed):

| Look-back | Result |
|---|---|
| 48 weeks (live) | no recommendation (the reason above) |
| 56 weeks | SELL 1.31112–1.31219; primary 1.30841 (zone 1.30770–1.30841 becomes Major with the 12 Nov 2025 daily swing low); intermediate 1.31000 |
| 104 weeks | the same primary |

**This was not changed.** The look-back is an owner-approved parameter. Lengthening it would issue more
recommendations, and the brief forbids loosening rules just to produce forecasts. My 20 November historical validation
also found no predictive edge in STP's destinations, so a 56-week setting would not by itself make the forecasts more
useful. **This is the owner's decision.**

## C. Correction made (a demonstrated defect)

**The dashboard showed a mix of prices and IG points.** `dashboard/stp.py` `Prices.text` converted IG points to
1.xxxxx notation. Its regex skipped any number preceded by "-", so in the range "13135.5-13139.9" the second number
stayed in points. The STP tab showed the 19 Nov 15:00 reason as "zone 1.31355-13139.9 … the zone 1.31480-13158.5".

- **Fix:** one regex change. A "-" that follows a digit (a range) is converted; a minus sign is still left alone.
- **Files:** dashboard/stp.py, plus the new tests/functional/test_stp_diagnosis_20261120.py.
- **Why it works:** the two regression tests use the live 19 Nov sentence and fail on `26c06fc`; they pass with the fix.
  The existing notation test and the other dashboard tests still pass.

The planner (forecasting) code is unchanged: no defect was found in it.

## D. Tests

New file: tests/functional/test_stp_diagnosis_20261120.py, 5 tests.
- 2 are regressions for the dashboard notation; they fail without the fix.
- 3 pin the live situation end to end:
  - at a fresh low the planner still reports direction, evidence and the structural map;
  - it gives no destination and invents none;
  - the real keeper re-analyses every hour and appends an analysis event;
  - the dashboard shows the analysis as current, with the planner's reason.

The brief's scenarios map to existing tests as follows. Uptrend, downtrend, range, exhaustion, insufficient evidence
and stale data are in tests/functional/test_planner_scenarios.py (1, 2, 3, 4, 13, 13b, 12) and
tests/functional/test_stp_dashboard_scenarios.py (11, 12, 13). Approaching resistance or support is covered by the
zone-reachability and invalidation tests (7, 8, 9).

**Full suite on the branch: 2,305 passed, 0 failed** (production's 2,300 plus the 5 new tests).

## D2. Historical check (section 7 of the brief)

- **Data and code:** the production planner code (unchanged) on `/home/autobot/stp-research/historical/GBPUSD`, read
  only.
- **Timestamps:** every weekday at 12:00 UTC from 3 Jun 2024 to 9 Apr 2026, 484 in total.

| Outcome | Count |
|---|---|
| assessment produced | 484 of 484 (0 exceptions) |
| recommendation-grade plan | 160 (33%) |
| direction NEUTRAL | 161 |
| direction TRANSITIONAL | 60 |
| D-1 destination already reached | 42 |
| condition INDETERMINATE | 41 |
| no Major destination | 8 |
| condition REVERSAL_RISK | 7 |
| data not fresh (reported as such, no forecast) | 4 |
| no defensible entry zone | 1 |

- **Leak check:** 12 random timestamps re-run on a store clipped at the timestamp gave identical plans (12 of 12).
- **Finding:** a structural map was written in only 214 of 484 assessments. When the direction is NEUTRAL or
  TRANSITIONAL (46% of hours), the planner stops before building zones, so those WAIT assessments carry no
  support/resistance context. That is how it was specified (design: no direction, no plan), so it is a gap for the
  owner to decide on, not a defect. The dashboard still draws its levels from the snapshot when there is one.
- The script and its output are in this folder (`hist_check.py`, `hist_check_summary.json`).

## E. Demonstration: an assessment from the isolated code on current production data (read only)

Assessment at 20 Nov 2026 08:17:06 UTC, on market data up to 08:15 UTC (fresh). Price 1.3108 (bid).

**Market**
- **Direction: BEARISH.** The 4-hour chart has lower highs (1.32279 → 1.31719) and lower lows (1.33122 → 1.31680).
  The 4-hour EMAs stack 7 < 13 < 21. The close (1.31133) is 2.1 ADR below the EMA100 (1.32664), which is falling
  19.8 pips over 6 candles.
- **Warning:** the daily structure (higher highs and higher lows) is against the 4-hour structure.
- **Condition: CORRECTION_ACTIVE.** The impulse ran from 1.31719 (19 Nov 08:00) to a new low of 1.30770 (20 Nov
  00:00). Since then the 4-hour candle has closed back inside its Bollinger band, the RSI is 54.9, and the MACD is
  -20.15 with histogram -3.92. An hourly close above the hourly Bollinger middle (06:00) marks a correction under way.
- **Momentum:** the downside momentum is no longer expanding, but the 4-hour structure is intact. Exhaustion is not
  treated as a reversal.

**Forecast**
- Expected movement: "UP into resistance, then DOWN".
- **Nearest resistance (reversal) zone:** 1.31116–1.31219, Major. It contains price and combines the daily pivot,
  weekly S1, a former hourly swing low and the London high.
- **Next resistance zones:** 1.31355–1.31457 (Major: daily and 4-hour swing lows, R1) and 1.31637–1.31728 (Major:
  H1 EMA100, the New York high, the former 4-hour swing low 1.31680).
- **Invalidation of the bearish view:** a 4-hour close at or above 1.31749 (3 pips beyond the last lower high,
  1.31719).
- **Support below:**
  - 1.30922–1.31000 (Moderate);
  - 1.30770 (Moderate: today's low and the previous-day low);
  - 1.30500 (Moderate: daily S1 and the round number);
  - 1.30172–1.30279 (daily and weekly S2);
  - 1.30000.
- **Immediate, preferred and extended destinations: none qualify.** No Major support lies below. **Recommendation:
  WAIT.** "No Major support zone below the entry zone within the 150-pip window for the primary destination."
- **Confidence:** STP computes no confidence or probability measure (none was ever specified). The 20 November
  historical validation found its directional calls at chance (51.6%, base rate 49.4%).

## F. What exists and what is missing (against the brief's section 4)

| Feature | Status |
|---|---|
| Price, 4-hour direction, higher-timeframe (daily) context | exists |
| Momentum: MACD, RSI, same-colour candles, impulse size | exists |
| Exhaustion and continuation: condition classes | exists |
| EMA direction and separation: 7/13/21 stack, EMA100/200, distance in ADR | exists |
| Bollinger: 4-hour band, hourly middle | exists |
| Previous day and week high/low, daily and weekly pivots, R1–R3, S1–S3 | exist |
| H1 and H4 swings; daily swings | exist; daily swings limited to 48 weeks |
| Support and resistance zones with confluence families | exist (always written) |
| Intermediate, primary and extended destinations; invalidation | exist, **only when a recommendation is issued** |
| Historical support and resistance older than 48 weeks; weekly swings | **missing** |
| Structural zones in NEUTRAL or TRANSITIONAL hours | **missing** (zones are built only with a direction) |
| "Ranging" as its own label | missing (NEUTRAL or TRANSITIONAL instead) |
| An alternative scenario | partial: an alternative entry zone only |
| Confidence or probability | **missing** (never specified) |

Adding any of the missing items is a methodology change for the owner, not a repair.

## G. Deployment readiness

- **The dashboard fix** is ready and tested, but optional and cosmetic. It needs only a dashboard restart, which is the
  owner's to authorise. Not deployed.
- **Nothing to deploy for the planner:** it runs correctly.
- **Restoring recommendations at fresh extremes** needs the owner's decision on P-B9: a longer look-back, or retaining
  older daily swings that lie beyond the recent range. Evidence is in section B.
