# STP historical validation — GBP/USD, March 2024 to November 2026

20 November 2026. Offline research only, on branch `stp-conditional-journeys-20261120` (PR #2), worktree
`/home/autobot/worktrees/autobot-stp-journeys`.

- No production file, service, setting or switch was touched.
- No IG call, order, shadow trade or shadow comparison was made.
- Production `/opt/autobot` stays detached at `26c06fc`, `main` at `02f6c7e`.

All numbers come from `data/` in this folder, and the scripts are in `research/stp_validation/`. Prices are in IG
points (13227.9 = 1.32279), on the sell (bid) side, the chart price the planner uses. Times are UTC.

---

## Executive summary

**STP does not demonstrate structural predictive capability on 2.7 years of GBP/USD history.** Every test that
controls for distance and chance comes out at or slightly below chance, in both the development half and the
held-out test half.

| Question | Result | Chance / baseline | Verdict |
|---|---|---|---|
| A. H4 direction: first ±½ ADR move goes the predicted way (120 h) | **51.6%** (n = 2,086; 95% CI 47.2–55.9) | 49.4% of all decisions moved up first | no edge |
| B. Destination touched before the zone-break level | **41.8%** (n = 1,377) | 45.4% expected for a random walk at the same distances | slightly **worse** than chance |
| B. Destination side reached before the same distance the other way | **48.8%** (n = 1,355) | 50% | no edge |
| C/D. After entry touch + hourly close back out of the zone (the rejection proxy): destination before zone break | **45.5%** (n = 459) | 51.1% random-walk expectation | worse than chance |
| B. Destination vs 4-hour structure break (looser invalidation) | **75.1%** (n = 1,307) | 76.4% random-walk expectation | no edge |
| Full anticipated sequence (entry → destination, no invalidation), 120 h | **36.7%** of 1,396 plans | — | 46.6% entry → invalidation |

STP's headline-looking numbers are produced by geometry, not by prediction:

- The destination is reached within 120 h in **86.5%** of plans, but the median destination is only **14 pips**
  (0.17 ADR) from price.
- The entry zone already contains price in **57%** of plans, so there is usually no "anticipated correction" at all.
- Where a correction is needed, it is a median **9 pips**, and is touched 90% of the time.
- Zones, invalidation and destination all sit inside about one ADR-sixth of each other. Touches of both are almost
  certain, and which comes first is a coin toss. The mirror plan (the same distances, the other way round) does
  exactly as well: 45.8% against 45.4% expected.

What STP is not doing: picking PIA-style S2/S3 or R2/R3 destinations. At most about 22% of primary destinations even
contain a daily or weekly S2/S3/R2/R3. Most are clusters of hourly and 4-hour swings, session highs and lows and round
numbers, with one daily level to qualify as Major. The "Major" bar is met almost everywhere, so the nearest Major zone
is usually the next zone.

Four technical defects in the audit tooling were found and fixed (section 7.1, 8). Neither changes a trading rule. No
trading-rule change is proposed on this evidence. Section 7 lists what would need a methodology decision by the
owner.

This is structural accuracy only, not trading performance. No fills, spreads, P&L or profitability were computed.
Reaching a destination is not a profitable trade.

---

## 1. Environment and code

| Item | State |
|---|---|
| Production checkout | `/opt/autobot`, detached at `26c06fc` (pullback-entry, owner's restart pending), `main` `02f6c7e`; other sessions' untracked files left alone |
| Services | `autobot-prices`, `autobot-dashboard` running, not touched |
| Development branch | fetched `origin/stp-conditional-journeys-20261120` at `032191f` (42 commits on top of `main` `02f6c7e`) into a new worktree; nothing in `/opt/autobot` was changed |
| Code under test | `planner/assess.py` (destination-first selection, conditional journeys), `planner/forward_outcomes.py`, `planner/walk_forward.py` at `032191f`, plus the audit fixes below |
| Later remote commits | 26 commits (`b4c80ce`..`2f21e58`, 02:46–03:25 UTC) arrived on the branch during this work. My commits are rebased on top of them. In `planner/assess.py` they only add research-only observations (`destination_hierarchy`, `target_ladder`); trade, entry, destination and invalidation are unchanged, so these results still describe the decision path. **The new "preferred target" ladder was not validated here** and should be judged with the same random-walk calibration. |

## 2. Data quality

Full detail: `data/data_quality.json` (from `research/stp_validation/dq.py`).

**Store.** `data/research/stp_validation_store/GBPUSD` is a research copy (not committed) made of:

- `data/research/stp_phase_store` (Jan 2024 to 17 Nov 2026);
- the live IG store for 18–19 Nov, laid over it (whole days copied).

No candle was created or edited.

**Provenance** (from `docs/research/long_replay_20261110.md` and the archive READMEs):

| Period | Source | Basis |
|---|---|---|
| Jan 2024 – Dec 2025 | AutoBot 161's 5m candles, built from a vendor tick archive (not IG's own prices; typically 0.2–0.5 pips from IG) | bid as stored; ask = bid + IG's typical half-hourly spread |
| Jan – 24 Oct 2026 | 161's IG mid candles | bid = mid − half the typical spread |
| 25 Oct 2026 on | the bot's own IG candles | IG's bid and ask |

The planner and all scoring use the **bid** side only, so the spread model does not affect any result here.

| Timeframe | Candles | Range | Duplicates | Out of order | OHLC / bid-ask problems | Notes |
|---|---|---|---|---|---|---|
| 5m | 208,685 | 2024-01-01 22:00 → 2026-11-20 00:00 | 0 | 0 | 0 | spread median 1.5 points |
| 1h | 17,429 | same | 0 | 0 | 0 | all 17,277 complete hours match their 5m candles exactly; 152 partial hours |
| 4h | none stored | — | — | — | — | built from 1h by the planner (`four_hour_from_hourly`): 4,365 complete, 304 buckets dropped for a missing hour |
| 1d | 875 | 2024-01-01 → 2026-11-19 | 0 | 0 | 0 | 210 partial (IG's short Sunday candles, holidays) |
| 1w | 209 | 2022-11-13 → 2026-11-13 | 0 | 0 | 0 | weekly buy-sell spread median 11.7 points (source artefact; bid side used) |
| Ticks | 704 days | 2024-01-01 → 2026-03-31 (`data/research/ig161/ticks_2024_2026`, 1.2 GB) | | | | vendor ticks, New York time stamps; already the source of the 2024–25 5m candles, so not used separately |

**Completeness** against the bot's market hours: 95.49% of 218,544 open 5-minute slots are present (9,859 missing).

- **1–22 March 2026: no data at all.** 161's 2026 archive has none.
- April, May and July 2026 have only 84–91% of their slots. Christmas and New Year are missing because the bot's
  hours treat them as open.
- **110 one-hour holes at the Sunday open.** The 2024–26 sources start at 17:00 New York, about an hour after the
  bot's Sunday 21:00 UK open. The scorer does not let these short weekly-open holes stop observation; every other
  missing slot does.
- No candle is time-stamped outside market hours, and every stamp is UTC.

**Is this enough?** Yes, for a structural accuracy test:

- 139 trading weeks and 4,254 four-hourly decisions;
- 1,396 fresh trade plans (1,111 distinct);
- every decision observable for 120 h except those next to gaps, which were censored, not guessed.

**Warm-up limitation.** History starts in January 2024. Daily swings (48-week look-back) and the 4-hour EMA200 are
therefore thinner in early 2024. The EMA200 is "warming up" in every plan, as the plans themselves say. The first
decision is 1 March 2024.

## 3. Method

### 3.1 Collection

`research/stp_validation/collect.py` calls `planner.assess.plan_at(settings, store, as_of)`, exactly what
`planner.walk_forward.audit` calls.

- **When:** at every 4-hour boundary of the store (UK-time boundaries, so 23/03/07… UTC in summer), from
  2024-03-01 to 2026-11-19, while the market was open. That gives **4,254 decisions**.
- **Output:** each plan is saved in full, without the bulky level map (`plans_*.jsonl.gz`, kept in
  `/home/autobot/research/stp_validation_20261120/data/`).
- **No future-data leakage.** For 12 random times (`data/leak_check.json`), the plan was rebuilt from a copy of the
  store holding only candles that had finished by then. The result was **identical to the full-store plan in 12 of
  12**.

### 3.2 Scoring

`research/stp_validation/score.py` works on later candles only.

- Touches of the entry and destination zones use 5-minute highs and lows (no tolerance).
- The **zone break** (planner invalidation 1) uses **hourly closes** only.
- The **structure break** (invalidation 2) uses **4-hour closes** only, built from hourly candles as the planner
  builds them.
- **An M5 close is never treated as an H1 or H4 confirmation.**
- Events with the same closing time count as simultaneous: no order is invented inside a candle.
- Observation stops at the first missing open slot.
- The horizons (24, 72, 120 and 240 h) are measurement windows only. **Nothing is closed at any time, and there is no
  two-hour or other expiry.**

### 3.3 Baselines

- **Direction:** the base rate of up-first moves over all decisions, plus weekly-block bootstrap intervals.
- **Destination:** a mirror test: was the destination distance reached on the destination side before the same
  distance on the other side?
- **Journey** (`calibration.py`): the random-walk ("gambler's ruin") expectation z/(d+z) for touching the destination
  (d away) before the invalidation level (z away), plus a flipped-plan control.

### 3.4 Avoiding overfitting

**DEV** = decisions before 2025-07-01; **TEST** = from 2025-07-01. Any factor that looks useful in DEV is reported
only alongside its TEST value.

### 3.5 Official audit

`planner.walk_forward` itself (with the fixes) was also run with a 24-hour horizon on three periods (section 5.8).

## 4. What the planner decided (4,254 decisions)

| | Decisions |
|---|---|
| Fresh plan with entry and destination | 1,396 (scored; 1,446 including stale-data times) |
| NEUTRAL 4-hour direction (mixed swings) | 1,423 |
| TRANSITIONAL | 379 |
| BULLISH/BEARISH but condition INDETERMINATE / REVERSAL_RISK | 285 / 53 |
| Refused: primary destination already reached | 464 |
| Refused: no Major destination beyond the entry | 75 |
| Stale data (mostly the March 2026 gap) | 172–175 |

Plans by condition: CORRECTION_ACTIVE 1,069, CONTINUATION 303, CORRECTION_LIKELY 16, EXHAUSTION 8.

Plans by side: SELL 655, BUY 741.

Destination-first selection mode: `nearest_untouched_major_ahead` in **100%** of plans.

## 5. Prediction statistics

### 5.1 A. Direction (all fresh BULLISH/BEARISH decisions)

| Measure (first passage) | BULLISH correct | BEARISH correct | All | Base rate "up first" |
|---|---|---|---|---|
| ±½ ADR within 120 h | 52.1% (n 1,108) | 51.0% (n 978) | **51.6%** (n 2,086; CI 47.2–55.9) | 49.4% |
| ±½ ADR within 24 h | 50.2% (797) | 50.8% (731) | 50.5% (CI 45.1–55.3) | 49.4% |
| ±25 pips within 24 h | 50.5% (1,074) | 50.9% (948) | 50.7% (CI 47.1–54.1) | 50.3% |
| Sign of net move after 24 h / 72 h / 120 h | | | 51.5% / 51.6% / 51.7% | up 48.4% / 48.7% / 47.3% |

| Period | Balanced accuracy (½ ADR, 120 h) | BULLISH | BEARISH | Base rate up |
|---|---|---|---|---|
| DEV (Mar 2024 – Jun 2025) | 51.4% | 56.2% (644) | 46.5% (523) | 52.9% |
| TEST (Jul 2025 – Nov 2026) | 51.3% | 46.3% (464) | 56.3% (455) | 45.4% |
| 2024 / 2025 / 2026 | 53.0% / 50.1% / 52.0% | | | 50.1% / 51.1% / 45.9% |

The bullish/bearish gaps between periods simply follow the market's drift: in DEV, BULLISH looks better because the
market rose; in TEST, BEARISH looks better because it fell. Balanced accuracy stays at about 51% throughout. This
matches the 18 Nov market-phase research (V1 51.6% on hourly decisions).

### 5.2 B. Destination (1,396 plans; 1,111 distinct)

| | 24 h | 72 h | 120 h | 240 h | 120 h, distinct plans |
|---|---|---|---|---|---|
| Destination reached (any time) | 68.2% | 81.2% | 86.5% | 92.1% | 88.3% |
| … before any invalidation | 50.4% | 54.5% | 55.9% | 56.3% | 56.8% |
| … only after an invalidation | 17.8% | 26.7% | 30.6% | 35.8% | 31.5% |
| … without the anticipated correction (before the entry was touched) | 14.3% | 15.3% | 15.8% | 15.9% | 15.1% |
| Mirror: destination side reached first | 48.0% | 48.9% | 48.8% | 48.8% | 48.7% |

- **Distance to the destination:** median 14.0 pips (IQR 9.2–23.9), 0.17 ADR (ADR median 81 pips).
- **Time to destination** (120 h, when reached): median 5.0 h (IQR 1.6–15.9).
- **When the destination was not reached in 240 h:** price got within a median 12.7 pips of it (n = 100).
- The extended (second Major) destination was reached before invalidation in 32.5% of plans, against 51.9% for the
  primary on the same 1,189 plans. That is what the extra distance alone would predict.

### 5.3 C. Corrective movement

- **No correction needed:** the entry zone contained price at plan time in **57.2%** of plans (60.1% of distinct
  plans).
- **The other 598 plans:**
  - correction needed to the near edge: median **9.1 pips** (IQR 3.4–17.8);
  - entry zone touched within 120 h: **90.5%**;
  - median time to entry touch 1.7 h; to half the correction, 0.3 h.

How far the counter-move went before the destination was reached (whole observed window):

| Correction extent | Plans |
|---|---|
| none (<10% of the way) | 10.0% |
| stopped short (10–50%) | 13.9% |
| stopped short (50–100%) | 11.4% |
| reached the zone, held inside it | 16.7% |
| **overshot the zone's far edge** | **48.0%** (median overshoot 32 pips) |

The correction invalidated the thesis (H1 zone break or H4 structure break before the destination) in **47.6%** of
plans within 120 h.

### 5.4 D. Sequence (120 h)

| Sequence | All plans | SELL | BUY | DEV | TEST |
|---|---|---|---|---|---|
| Entry → destination (anticipated sequence) | **36.7%** | 36.5% | 37.0% | 36.9% | 36.6% |
| Destination without correction | 14.5% | 14.0% | 14.8% | 14.7% | 14.3% |
| Entry → invalidation | 46.6% | 46.4% | 46.7% | 47.8% | 45.2% |
| Unresolved / censored | 2.2% | | | | |

At 24 h the split is 34.7 / 13.7 / 44.6, with 5.6% unresolved. Almost every plan resolves inside 3 days.

**Rejection proxy:** after the entry was touched, an hourly close back on the trade side of the zone, before any
invalidation.

- **With it:** the destination came before invalidation in 69.1% of plans (n 713).
- **Without it:** 4.3%.
- This split is largely mechanical: the close back out is itself most of the way to a destination 14 pips off. The
  calibration test below removes that effect.

### 5.5 Calibration against a random walk (`data/calibration.json`)

| Test | n | Observed | Random walk | Difference | DEV | TEST |
|---|---|---|---|---|---|---|
| From plan price: destination before zone-break level | 1,377 | 41.8% | 45.4% | −3.5 | −4.7 | −2.2 |
| Mirror plan (control) | 1,367 | 45.8% | 45.4% | +0.4 | +1.8 | −1.2 |
| From plan price: destination before structure-break level | 1,307 | 75.1% | 76.4% | −1.3 | −2.1 | −0.4 |
| From confirmation (rejection proxy): destination before zone break | 459 | 45.5% | 51.1% | −5.6 | −7.9 | −1.9 |
| SELL / BUY, from plan, vs zone break | 645 / 732 | 42.9 / 40.8% | 45.8 / 45.0% | −2.8 / −4.2 | | |
| CONTINUATION / CORRECTION_ACTIVE, vs zone break | 298 / 1,055 | 43.6 / 41.6% | 49.3 / 44.5% | −5.7 / −2.9 | | |

None of these is positive in both halves.

The small shortfall suggests the destination zone itself slows price before it is touched. That matches the 18 Nov
finding that structural zones stop moves better than indicators, but it does so for moves in either direction.

### 5.6 E. Timing (120 h)

| | Median | IQR |
|---|---|---|
| Plan → half the correction | 0.3 h | 0.1–1.4 |
| Plan → entry-zone touch | 1.7 h | 0.2–7.3 |
| Entry touch → destination | 2.3 h | 0.9–5.8 |
| Plan → destination | 5.0 h | 1.6–15.9 |
| Plan → invalidation | 6.0 h | 2.0–16.0 |

Nothing in this was a fixed expiry; the distributions come out short because the zones are close together.

### 5.7 F. Structural invalidation (120 h)

- Any invalidation: **83.4%** (H1 zone break 83.4%; H4 structure break 37.2%).
- 240 h: 88.4% / 48.0%.
- Median time to invalidation: 6 h.

The zone break sits 3 pips beyond a zone about 10 pips wide, close to price. It fires on ordinary noise:

- in 30.6% of plans, price went on to reach the destination after the zone break had already invalidated the plan;
- price overshot the far edge of the entry zone by a median 32 pips when it overshot.

The brief notes that pivot zones get overshot to sweep liquidity, and this is what that looks like. However, the
looser structure-break test (5.5) shows no edge either. Loosening invalidation only buys more touches, not more
foresight.

### 5.8 Official walk-forward audit (`planner.walk_forward`, 24 h, three periods)

See `data/official_audit_*_24h.json`. Run on three winter periods (UK time = UTC, so the audit's 4-hour UTC steps
are the store's 4-hour boundaries) with `--store <research store> --weekly-open-grace-minutes 65`, after all fixes.

| Period | Decisions | Market closed | No plan / stale | Entry → destination | Destination before entry | Entry → invalidation | Unresolved at 24 h |
|---|---|---|---|---|---|---|---|
| 3 Nov – 15 Dec 2024 | 252 | 72 | 120 / 2 | 26 | 2 | 28 | 2 |
| 2 Nov – 14 Dec 2025 | 252 | 72 | 118 / 0 | 11 | 8 | 38 | 5 |
| 25 Oct – 19 Nov 2026 | 150 | 42 | 65 / 0 | 22 | 4 | 10 | 7 |

- No DATA_GAP_CENSORED results remain.
- The official audit's outcome agrees with the research scorer's 24-hour sequence on **163 of 163** matching plans.

**Note:** in summer, the audit's UTC 4-hour steps fall one hour inside the UK-time 4-hour candles. The decisions are
still valid as-of plans, but they are not taken at a 4-hour close. Choose the start time accordingly.

## 6. Bullish vs bearish; market condition

**Bullish and bearish** behave alike in every journey measure:

- entry → destination 36.5% (SELL) vs 37.0% (BUY);
- calibration −2.8 vs −4.2 points.

Directional differences between periods follow the drift, not the planner (5.1).

**By market condition** (120 h):

| Condition | Plans | Entry → destination | Destination without correction | Entry → invalidation | Mirror |
|---|---|---|---|---|---|
| CORRECTION_ACTIVE | 1,069 | 39.4% | 12.1% | 46.4% | 48.7% |
| CONTINUATION | 303 | 29.7% | 22.4% | 45.2% | 49.5% |
| CORRECTION_LIKELY | 16 | 12.5% | 25.0% | 62.5% | — |
| EXHAUSTION | 8 | 0% | 12.5% | 87.5% | — |

In CONTINUATION, more plans go straight to the destination without the correction. That fits the label, but it is
not a directional edge (the mirror is 49.5%). The CORRECTION_LIKELY and EXHAUSTION groups are too small to use.

By countermove evidence state (120 h, entry → destination):

- AT_ENTRY_NOW 45.9% (798);
- CORRECTION_OBSERVED 25.5% (415, with 31.1% going straight to the destination);
- UNCONFIRMED_PULLBACK 23.8% (172, with 39.5% straight to the destination).

**"Correction observed" does not make the correction more likely to reach the entry zone.**

## 7. Failure analysis: root causes

Factor tables in `results.json` (`factors_*`) report each factor's success rate in DEV and TEST separately.

### 7.1 Technical defects (fixed; section 8)

| # | Defect | Effect |
|---|---|---|
| T1 | `walk_forward.audit` read 4-hour candles from a stored `4h` folder | research stores have none, so the **H4 structure-break invalidation was silently never scored** in any historical audit; in the live store the stored 4h candles equal those built from hourly (86 of 86 checked), so the fix changes nothing there |
| T2 | strict gap censoring treated every break between 5-minute candles as missing data | **every journey crossing a weekend was censored as DATA_GAP**, and a 24-hour window ending in the weekend was censored too |
| T3 | the audit command could not point at a research store | added `--store` (and `--weekly-open-grace-minutes` for late-opening sources) |
| T4 | the audit planned at times when the market was shut (Saturdays) | with no candles in the window, those were reported as **DATA_GAP_CENSORED**: all 12 censored results in a Sep–Oct 2024 trial run; now recorded as MARKET_CLOSED and not planned |

### 7.2 Labelling issue (no fix made; for the owner)

**L1.** A "nearest untouched Major ahead" destination is called untouched if the **latest 5-minute candle** has not
reached it (D-1 rule).

- 82% of plans' destinations had been touched in the previous 24 hours, and 88% since the last 4-hour swing.
- So they are not fresh, untested destinations in the PIA sense.
- Plans with a destination touched in the previous 24 h actually did slightly *better* (52.8% vs 44.4% reached
  before invalidation; TEST 53.3% vs 38.9%). This is a description problem, not a cause of failure.

### 7.3 Methodology weaknesses (evidence; any rule change needs the owner)

**M1. The destination is too close to mean anything (main cause).**

- The Major-zone bar (3 families incl. one daily or weekly level) is met by clusters of intraday levels almost
  everywhere. The nearest Major zone beyond the entry is typically one zone away: median 14 pips, 0.17 ADR.
- At that range, touching the destination is near certain (86–92%), and getting there before a zone break is a coin
  toss.
- The success rate falls with distance: 60.7% for destinations < 0.25 ADR, 34.9% for 0.25–0.5, 20.0% for 0.5–1 ADR.
  DEV and TEST agree.
- At most about 22% of destinations include a daily or weekly S2/S3/R2/R3 (319 S2/S3/R2/R3 mentions in 1,446 plans).

**M2. There is usually no correction to anticipate.** In 57% of plans, price is already in the entry zone. The
"journey" is then really "from here to the next zone".

**M3. The invalidation is inside normal noise.** The H1 zone break is 3 pips beyond a ~10-pip zone that price is
often already in. 83% of plans are invalidated within 120 h, and 31% of plans reach the destination after
invalidation.

**M4. The H4 direction has no forecasting value** (51.6%; 5.1).

- The same result appeared on hourly decisions in the 18 Nov research.
- No direction-failure factor holds up in both halves: daily agreement, EMA stack, time since swing, impulse size and
  distance from EMA21 all sit at 47–57%, with signs that flip between DEV and TEST.
- In particular, there is **no evidence of a specific, fixable reversal or exhaustion blind spot.** EXHAUSTION (10
  decisions, 10% correct) and REVERSAL_RISK (53, 41.5%) are worse than chance but too small to act on, and they are
  already excluded from plans.

**M5. Destination-first selection is a no-op on history.** Its entry choice equalled the old entry-first choice in
**1,446 of 1,446** plans.

- When the first candidate's destination was already touched, every other candidate shared the same or a touched
  destination, so the plan was refused (464 times) rather than re-routed.
- The comparison "destination-first vs entry-first" therefore has no differing cases to measure (0 of 1,446).

### 7.4 Factors that looked useful in one half only (not recommended)

| Factor | DEV | TEST | Note |
|---|---|---|---|
| Entry reachability PLAUSIBLE vs NEAR | 60.4% vs 46.5% | 67.7% vs 43.9% | stable, but PLAUSIBLE entries are further from price, so the destination is further beyond them and the full sequence is rarer (21.9% vs 44.1%). A distance effect, not foresight. |
| "Destination contains a pivot" | 49.9% vs 56.0% (with vs without) | 48.6% vs 55.9% | consistent, but destinations without pivots are closer (geometry again) |
| SELL vs BUY | 45.5% vs 56.5% | 55.7% vs 46.1% | flips with the drift |

### 7.5 Data problems

No result depended on stale or missing data:

- stale times (172) were excluded;
- observation stops at every genuine gap (2.2% of plans unresolved at 120 h, mostly next to the April–July 2026
  holes);
- the leak check found no use of future candles.

## 8. Code changes, tests and commits

Changes are on `stp-conditional-journeys-20261120` only (commit references in section 11).

**`planner/walk_forward.py`:**

- new `forward_candles()`: outcome 4h candles are built from hourly ones with `four_hour_from_hourly` (fixes T1);
- new `open_slots_fn()`: gaps are judged by the bot's market hours (fixes T2);
- times when the market was shut for the previous hour are recorded as MARKET_CLOSED and not planned (fixes T4);
- gap check at the end of the observation window uses the same rule;
- CLI `--store` and `--weekly-open-grace-minutes` (T3).

**`planner/forward_outcomes.py`:** `score_journey(..., open_slots=None)`. A break between 5-minute candles is a gap
only if the market was open during it. Without `open_slots` the old strict behaviour stays, so existing callers and
tests are unchanged.

**`tests/functional/test_stp_walk_forward.py`:** two existing tests now pass real settings instead of `None`, because
the audit reads market hours. Their assertions are unchanged.

**`tests/functional/test_stp_historical_validation_regressions.py`:** 8 regression tests:

- H4 built from hourly on a store with no 4h folder;
- H4 structure break scored on such a store;
- weekend not a gap (SELL and BUY mirror);
- without market hours the weekend is still treated as a gap;
- a missing open-market candle still censors;
- the weekly-open grace skips only the late-opening hour;
- no plan and no censoring while the market is shut.

**`research/stp_validation/`:** `dq.py`, `collect.py`, `score.py`, `analyse.py`, `calibration.py` (read-only
research tools).

**No trading rule, setting, threshold, planner decision path or dashboard code was changed.**

**Tests:** the CI STP set (`.github/workflows/stp-functional.yml`) plus the new file give **232 passed, 0 failed**
locally. That is the original 225 (CI shows 224 + 1 skipped, because the real-store test is skipped there) plus 7 new
ones. Full figures and command are in section 11.

## 9. Recommendations (by expected impact; none implemented)

1. **Do not treat STP's destinations or sequences as forecasts.** This includes any authorisation step. On this
   evidence they are descriptive.
2. **If the aim is PIA-style journeys, the destination definition is the first thing to revisit (M1).** This is a
   methodology decision for the owner. The evidence says the current "nearest Major" is about one zone away and
   carries no edge. Any replacement (for example, requiring daily/weekly pivots S2/S3/R2/R3, or a minimum distance in
   ADR) must be specified first and then tested on TEST-period data it was not designed on. It should be judged with
   the random-walk calibration, not by reach rates, which rise or fall with distance alone.
3. **Report the calibration with any future STP evaluation.** Use the random-walk calibration and the mirror plan,
   and never raw "destination reached" rates.
4. **Fix the wording "untouched" (L1)**, or test destinations against the whole time since the last swing. This is a
   labelling change; it should not be sold as an accuracy improvement (7.2).
5. **The H1 zone-break invalidation (M3) is a separate methodology question.** Loosening it to the H4 structure break
   showed no edge, so it should not be changed to improve the numbers.
6. **Destination-first selection (M5) adds code but changed no decision in 2.7 years.** The owner may want to know
   this before merging PR #2.
7. **Fill the data gap.** 1–22 March 2026 and the April–July 2026 holes would add about 6 weeks. This is low priority;
   it cannot change the conclusion.

## 10. Worked examples (real prices, UTC; all from the TEST period)

| # | As of | Price | H4 / condition | Trade | Entry zone | Destination | Invalidation (H1 / H4 close) | What happened | Class |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2025-11-06 20:00 | 13131.9 | BEARISH / CORRECTION_ACTIVE | SELL | 13139.0–13150.7 (needs +7.1) | 13096.5–13108.0 | 13153.7 / 13165.1 | rallied into the zone 20:15 (max +9.8); hourly close back below 21:00; destination 08:30 on 7 Nov; zone break only later (7 Nov 17:00) | **entry → destination** (success) |
| 2 | 2026-08-04 03:00 | 13426.8 | BULLISH / CORRECTION_ACTIVE | BUY | 13413.3–13423.2 (needs −3.6) | 13438.0–13449.5 | 13410.3 / 13396.1 | dipped into the zone 04:15 (max −8.1); hourly close back above 05:00; destination 07:25; no invalidation; +81 pips max | **entry → destination** (success) |
| 3 | 2026-03-24 12:00 | 13396.7 | BEARISH / CORRECTION_ACTIVE | SELL | 13433.4–13444.6 (needs +36.7) | 13384.5–13390.5 | 13447.6 / 13482.3 | no correction (max +3.4); destination touched 12:10, 10 minutes after the plan (it was 6 pips away) | **destination without correction**: direction right, anticipated sequence wrong |
| 4 | 2025-08-07 03:00 | 13351.6 | BULLISH / CONTINUATION | BUY | 13330.1–13341.2 (needs −10.4) | 13364.6–13377.0 | 13327.1 / 13278.4 | no dip (max −3.6); destination 04:10; went on +243 pips | **destination without correction** |
| 5 | 2026-03-31 19:00 | 13229.5 | BEARISH / CORRECTION_ACTIVE | SELL | 13236.0–13248.4 (needs +6.5) | 13171.6–13184.1 | 13251.4 / 13381.3 | touched the zone 19:05; hourly close back below 20:00 (rejection proxy met); then rallied 99.6 pips; hourly close above 13251.4 on 1 Apr 07:00 | **entry → invalidation** (failure; the confirmation did not hold) |
| 6 | 2026-07-15 19:00 | 13535.8 | BULLISH / CONTINUATION | BUY | 13471.4–13482.6 (needs −53.2) | 13549.6–13557.9 | 13468.4 / 13364.9 | the 13.8-pip destination was never reached (max +8.9); price fell 110 pips through the zone; hourly close below 13468.4 on 16 Jul 17:00 | **entry → invalidation** (direction wrong) |
| 7 | 2025-07-08 15:00 | 13544.4 | BEARISH / CONTINUATION | SELL | 13559.5–13572.7 (needs +15.1) | 13522.6–13534.2 | 13575.7 / 13684.1 | zone 15:20; hourly close above 13575.7 at 17:00 (invalidated); price then ran +75, but reached the destination on 10 Jul 14:30 | **entry → invalidation, destination after invalidation** (the zone overshoot the brief describes) |

## 11. Reproduction, test results and commits

**Reproduce.** Run from the worktree with `PYTHONPATH=.`, `nice`, about 40 minutes on 2 cores. Here S is
`/opt/autobot/data/research/stp_validation_store/GBPUSD` and O is the output folder.

```
python -m research.stp_validation.dq --store S --out O/data_quality.json
python -m research.stp_validation.collect --store S --leak-check 12 --out O/leak_check.json
python -m research.stp_validation.collect --store S --start 2024-03-01 --end 2025-07-01 --out O/plans_a.jsonl.gz
python -m research.stp_validation.collect --store S --start 2025-07-01 --end 2026-11-19 --out O/plans_b.jsonl.gz
python -m research.stp_validation.score --store S --plans O/plans_a.jsonl.gz O/plans_b.jsonl.gz --out O/scored.jsonl.gz
python -m research.stp_validation.analyse --scored O/scored.jsonl.gz --out O/results.json
python -m research.stp_validation.calibration --store S --scored O/scored.jsonl.gz --out O/calibration.json
python -m planner.walk_forward --store S --start 2026-10-25 --end 2026-11-19 --stride-hours 4 --horizon-hours 24 \
       --weekly-open-grace-minutes 65 --output O/official_audit_2026-10-25_24h.json
```

**Files in `data/`:**

- `data_quality.json`, `leak_check.json`;
- `scored.jsonl.gz` (every decision with its outcome events);
- `results.json`, `calibration.json`;
- `official_audit_*_24h.json`.

The raw plans (2.4 MB) and the research candle store are not committed. They are in
`/home/autobot/research/stp_validation_20261120/data/` and `/opt/autobot/data/research/stp_validation_store/`.

**Tests** (20 Nov 2026, this branch with the fixes):

| Run | Result |
|---|---|
| CI STP set + new regressions + dashboard technical tests | **260 passed, 0 failed** (225 existing STP, 8 new, 27 dashboard) |
| Full repository suite (`pytest -q`) | **2,315 passed, 0 failed** (8 min 40 s) |

**Commits:** see the commit that adds this report (and the one before it, with the code fixes) on
`stp-conditional-journeys-20261120`.
