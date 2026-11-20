# STP technical opportunities (GitHub issue #3) — 20 November 2026

Branch `stp-technical-opportunities-20261120`, from deployed `bb085f4`, isolated worktree
`/home/autobot/worktrees/autobot-stp-technical`.

**Nothing was deployed.** No service was restarted, IG was not contacted, no orders were placed, and the dormant
pullback-entry change was not touched. The production tree and data were only read.

## 1. What was built

`planner/technical.py` is an observe-only technical forecaster that reads the H1 and H4 charts. On each assessment it
names the nearest credible next opportunity, in either direction.

**Opportunity types**

| Type | When it fires |
|---|---|
| PULLBACK (trend continuation) | Trend context exists: at least 2 of the 4-hour direction, a falling or rising H1 EMA20, and EMA21 below or above a falling or rising EMA100. Price pulls back into the H1 EMA20 ± half the zone width, and must not already be through it. |
| REVERSAL | Price reaches a support or resistance zone of at least Moderate class from the existing map, arriving from the trade's far side. A reaction is already showing: a rejection or doji candle, RSI turning back from beyond 30/70, or a close back inside the Bollinger band. It is allowed against the 4-hour trend and then marked COUNTERTREND (−1). |
| RANGE_REVERSAL | The same reaction test, at the top or bottom of an H1 range (the "grey box"). The range is derived only from candles: both ends tested at least 2 separate times, a flat EMA, measured before the last 3 candles. |
| BREAKOUT | A confirmed H1 close at least 3 pips beyond a zone or range edge, still holding. The trade is the retest of the broken level. |
| FAILED_BREAKOUT | A close or wick beyond the level, then an H1 close back inside. The trade goes the other way. |

**Evidence and selection**
- Each candidate collects evidence points. Every point is written out with its exact value: 4-hour direction, EMA
  slope and stack, Bollinger position, slope and width, RSI direction or turn, candle shape, H1 structure, zone class,
  tests, and confluence.
- **Selection:** set-ups whose entry is within one zone width of price come first, then the most evidence, then the
  nearer entry.
- **Below `min_evidence` (4), nothing is forced.** The forecast says "no credible opportunity", with the best candidate
  and the reason.

**Each forecast gives:**
- bias and market condition;
- type and BUY/SELL;
- entry zone and status (in the zone, or waiting);
- stop, set beyond the zone by 0.3 × the H1 average range, at least 3 pips;
- intermediate and extended targets, taken from the existing map or from the H1 EMA, Bollinger middle or range opposite
  side. There is **no minimum distance**, but a target must lie wholly beyond price, as in the existing D-1 rule;
- trade invalidation (stop touched) and a **separate** structural invalidation (a confirmed H1 close beyond the last H1
  swing or beyond the stop), so a normal 3-pip overshoot does not end the forecast;
- the evidence list;
- a conditional alternative ("if instead an H1 candle closes beyond …, look for … towards …").

**Reused, not duplicated:**
- the planner snapshot (finished candles only, sell price);
- the bot's own EMA, Bollinger and RSI code;
- the existing level map and zones, including the approved 156-week historical map with no distance cut-off;
- the swing rule and the 3-pip touch and break rules;
- the zone width;
- the existing STP plan, used only as evidence for the 4-hour direction and condition;
- ADR.

**Integration and safety**
- **Not wired into the keeper:** the approved recommendation lifecycle and identity are untouched.
- **New `[stp_technical] enabled` setting, off by default:** when it is on, the planner run also writes `technical.json`
  and `technical.jsonl` beside the keeper's files. A failure there is logged and never affects the keeper.
- **New command:** `python -m planner technical --at <time>` prints a forecast and writes nothing.

## 2. The PIA First example (20 Nov 2026, 08:57)

**Shown by the example** (built in as rules):
- SELL at the H1 EMA20 in a bearish structure;
- after a doji or rejection from the pullback high;
- RSI declining;
- support at the recent hourly-low cluster;
- resistance at the pullback high;
- extended target at an older level.

Our own data matches every one of these:
- EMA20 is 1.31096–1.31086 on the sell price;
- the 07:00 candle is a long-upper-wick rejection from 1.31219;
- the lows are 1.31077 and 1.31077.5 (hourly swing lows and the previous-day low);
- a historical daily swing high sits at 1.29918.

**Not shown, so hypothesised and made settings:**
- the stop buffer;
- the range rules;
- the breakout rules;
- the evidence threshold.

No PIA price is used anywhere.

**What STP now says at 08:00 UTC** (real store):
- **Trade:** PULLBACK SELL, entry zone 1.31040–1.31151 around EMA20 1.31096.
- **Stop:** 1.31186, 5.3 pips.
- **Target:** 1.3100, 13.3 pips. **Extended:** 1.30841.
- **Evidence:** 7 points, listed in example_forecasts.txt.

For comparison, PIA's values were entry 1.31114, stop 1.31161 (4.7 pips), support 1.3078 and extended 1.2981.

## 3. Example forecasts (real timestamps)

Full readable forecasts are in `example_forecasts.txt`:

| Time (UTC) | Forecast |
|---|---|
| 20 Nov 08:00 | PIA-time pullback SELL |
| 18 Nov 09:00 | Range-bottom breakout SELL. The existing STP had no recommendation: 4-hour NEUTRAL. |
| 18 Nov 10:00 | Range-bottom reversal BUY |
| 17 Nov 19:00 | Failed breakout SELL |
| 20 Nov 14:00 | Resistance reversal SELL |
| 17 Nov 17:00 | Abstention |

The hourly run for 17–20 Nov is in `hourly_17_20_november.txt`.

## 4. Tests

**Full suite: 2,383 passed, 0 failed** (10 min 21 s, 20 Nov 2026). The pre-commit hook ran it again before the
commit.

**30 new tests:**

**18 technical tests** (`tests/technical/test_stp_technical.py`):
- candle shapes;
- the bot's own EMA and RSI on finished H1 candles;
- time alignment (never a running hour);
- no lookahead (full store and cut store agree);
- deterministic output;
- weekend or gap gives no forecast, with the reason;
- too little history;
- the stop buffer;
- targets beyond the zone and beyond price, with no minimum;
- a target price is already inside is not used;
- writing is off by default;
- when on, it writes only its own files, once per hour;
- a technical failure never stops the keeper;
- no broker or trading imports;
- no order fields;
- approved planner settings unchanged;
- existing plan identical;
- the real 20 Nov 08:00 pullback SELL.

**12 functional tests** (`tests/functional/test_stp_technical_scenarios.py`), one per scenario in the issue:
- bearish pullback SELL;
- bullish mirror BUY;
- support bounce under a bearish 4-hour trend (countertrend);
- range-top rejection;
- breakout retest;
- false breakout;
- two abstention cases;
- intermediate target, then reversal;
- an 8–15-pip opportunity;
- two cases of a 3-pip overshoot without structural invalidation.

`tests/technical/test_settings.py` covers the new `[stp_technical]` keys.

## 5. Chronological historical validation

**Bottom line: the technical forecasts show no measurable edge out of sample.** They are calibrated to chance
overall, by type, by direction and for 8–15-pip targets. The forecast code was frozen (last change 15:37 UTC) before
DEV was replayed, and TEST was replayed and scored once, with no tuning in between.

### Method
- **Data:** the validated research store `data/research/stp_validation_store/GBPUSD` (read only).
- **Decisions:** every 2 hours, 4 s after the hourly candle closes, while the market is open. Each snapshot uses
  finished candles only (`research/stp_technical/replay.py`).
- **Periods:** DEV is 1 Jan – 30 Jun 2025 (1,548 decisions). TEST is 1 Jul 2025 – 18 Nov 2026 (4,344 decisions). This
  is the same split as the existing STP's validation.
- **Data quality:** 0 errors and 0 unscorable forecasts.
- **Scoring:** `research/stp_technical/score.py`, run after every forecast had been written. It uses sell-price
  5-minute candles.
  - Entry is in the zone at the decision, or the first touch within the 8-hour validity.
  - After entry, the stop or the intermediate target, whichever comes first. A candle that touches both counts as a
    stop.
  - The horizon is 72 hours.
- **Edge:** the observed target rate minus the random-walk expectation z/(d+z), with 95% weekly-block bootstrap
  intervals.
- **Two simple baselines:**
  - MIRROR: the same geometry in the opposite direction;
  - ENTER-NOW: the same direction, entered at the decision price.
- **Extra views and head-to-head:** `research/stp_technical/compare.py`.
- **Evidence:** raw forecasts, scored rows and summaries are in `replay/`.

### Opportunities found (TEST, 4,344 decisions)
- **Opportunity named:** 3,030 decisions (70%). **Abstained:** 1,314 (30%), each with its reason.
- **New opportunities** (lifecycle de-duplicated): 1,610. The other 1,420 repeated a live one.
- **Countertrend:** 99 (3%).

| Type | Forecasts | Entry zone reached | Target before entry | Lapsed | Median target / stop (pips) |
|---|---|---|---|---|---|
| Pullback | 1,876 | 56.6% | 709 | 106 | 17.8 / 15.3 |
| Reversal at a zone | 606 | 81.7% | 109 | 2 | 6.4 / 14.3 |
| Failed breakout | 534 | 74.7% | 134 | 1 | 9.9 / 17.4 |
| Breakout retest | 12 | 58.3% | 3 | 2 | 17.1 / 12.8 |
| Range reversal | 2 | 2 of 2 | 0 | 0 | 15.0 / 17.4 |
| **All** | **3,030** | **64.8%** | **955 (31.5%)** | **111 (3.7%)** | **13.2 / 15.4** |

**Range and breakout set-ups are rare** (14 in TEST, 3 in DEV). The range rule (two tests of each end, flat EMA) and
the 3-pip confirmed-close rule seldom fire, so those two types cannot be judged.

### Destination achievement after entry (TEST)

| Group | Resolved | Target first | Random-walk expectation | Edge, pts (95%) | MIRROR edge | ENTER-NOW edge |
|---|---|---|---|---|---|---|
| **All** | 1,911 | 55.3% | 56.2% | **−0.9 (−3.1, +1.3)** | −2.0 | −1.1 |
| All, DEV | 742 | 54.0% | 54.2% | −0.2 (−5.6, +5.2) | −1.1 | +0.7 |
| Pullback | 1,025 | 46.2% | 48.2% | −2.0 (−5.4, +1.4) | −3.0 | −2.3 |
| Reversal | 490 | 66.7% | 66.5% | +0.3 (−3.9, +4.3) | −2.4 | +0.9 |
| Failed breakout | 387 | 65.6% | 64.9% | +0.8 (−4.2, +5.2) | +0.9 | +1.3 |
| Breakout | 7 | 2 of 7 | 41.8% | — (too few) | | |
| BUY | 984 | 53.3% | 56.4% | −3.2 (−6.2, −0.4) | −0.2 | −2.5 |
| SELL | 927 | 57.5% | 56.1% | +1.4 (−2.1, +5.0) | −3.8 | +0.2 |
| Countertrend | 53 | 54.7% | 57.4% | −2.7 (−15.7, +10.4) | +3.0 | −3.5 |
| New only | 1,018 | 60.1% | 60.1% | 0.0 (−2.9, +2.7) | −1.8 | −0.8 |

- **High target rates come from geometry, not skill.** For example, reversals hit their target 66.7% of the time, but
  the targets are short against wider stops, so a random walk gets 66.5%.
- **The two directional results flip sign between periods.** BUY is +3.3 in DEV and −3.2 in TEST; SELL is −6.2 in
  DEV and +1.4 in TEST. Read them as noise.
- **The extended target** was reached after the intermediate one in 64.1% of TEST cases. That is conditional on the
  intermediate target being hit, and is not compared with a baseline.

### Smaller opportunities (TEST)

| Target distance | Resolved | Target first | Expected | Edge, pts (95%) |
|---|---|---|---|---|
| under 8 pips | 636 | 75.2% | 76.0% | −0.8 (−4.8, +2.9) |
| **8–15 pips** | **699** | **53.9%** | **53.7%** | **+0.3 (−3.7, +4.1)** |
| 15–30 pips | 509 | 34.8% | 38.5% | −3.8 (−7.4, 0.0) |
| over 30 pips | 67 | 37.3% | 30.5% | +6.8 (−10.5, +25.0) |

**8–15-pip targets by type:**

| Type | DEV edge, pts (95%) | TEST edge, pts (95%) |
|---|---|---|
| Pullback | +1.5 (−10.9, +12.6), n 97 | −2.8 (−9.0, +3.2), n 356 |
| Reversal | −0.7 (−14.1, +11.3), n 63 | +2.1 (−6.1, +9.9), n 162 |
| Failed breakout | +13.6 (+4.9, +21.6), n 55 | +5.1 (−1.7, +11.3), n 180 |

**Failed breakouts with 8–15-pip targets** are the only group positive in both periods. The effect shrank from DEV to
TEST, and the TEST interval includes zero. This group was picked after looking at the results, so it is a lead to
watch on demo, not evidence.

### Adverse excursions (TEST, after entry)
- **Winning trades, adverse move:** median 3.7 pips, p75 7.9, p90 12.2 (pullback 3.7 / 7.8 / 11.7; reversal 2.7 / 6.8 /
  10.9; failed breakout 4.7 / 9.2 / 13.2).
- **Losing trades, best favourable move before the stop:** median 3.9 pips.
- **All entered trades:** median worst adverse move 8.5 pips, median best favourable move 7.8 pips.
- **Speed:** the median time to an outcome is 1.2 hours.
- **What this means for stops:** a stop near the median 15-pip distance survives about 90% of eventual winners' adverse
  moves. Tighter stops would cut winners sharply.

### Comparison with the existing STP (version C, deployed bb085f4)
The existing STP was scored on the same store and split in `stp_structural_history_20261120`. That scoring measured
from the plan's price whether the destination came before the zone break.

| | Existing STP, TEST | Technical forecast, TEST |
|---|---|---|
| Assessments | 4-hourly | 2-hourly |
| Plans / opportunities | 633 | 3,030 (1,610 new) |
| Median destination | 12.1 pips | 13.2 pips |
| Edge vs random walk | +0.3 (−3.5, +4.2) | −0.9 (−3.1, +1.3) |
| Edge in DEV | −3.8 | −0.2 |

**Head-to-head** at the 2,011 TEST 4-hour timestamps that both assessed:
- STP spoke at 633 and the technical forecast at 1,512. The technical forecast covered 1,011 timestamps where STP
  abstained; STP covered 132 where the technical forecast abstained.
- **When both spoke, they agreed on direction 478 times out of 501 (95%).** On agreement, the technical forecast's edge
  was +1.6 (−3.3, +6.6). On the 23 disagreements (12 resolved), it was −17.3, which is too few to judge.

**What this means:**
- The technical forecast gives about 4–5 times more opportunities, including short ones, countertrend reversals and
  failed breakouts.
- When STP has a view, the technical forecast mostly repeats its direction.
- **Neither planner beats chance.** The technical forecast meets the issue's functional brief (a nearest opportunity in
  either direction, no minimum target, explicit abstention), but the history does not show better accuracy than the
  existing STP or the simple baselines.

## 6. Unresolved decisions (for the owner)

1. **Approve or change the provisional `[stp_technical]` numbers:**
   - H1 EMA 20;
   - RSI 14 (the chart's RSI 3 is unchanged);
   - trend look-back 12;
   - H1 average range 14;
   - stop buffer 0.3 × H1 range;
   - range 48 candles, 2 tests, drift 0.25;
   - minimum evidence 4;
   - validity 8 h.
2. **Very short targets.** With no minimum, the nearest mapped zone can be only 2–3 pips away (e.g. 17 Nov 08:00:
   2.2 pips; 20 Nov 11:00: 1.9 pips). That is below the 3-pip touch rule. Options:
   - keep as is;
   - skip to the next zone when the first is within the touch rule;
   - use a minimum reward-to-risk instead of a distance.
3. **Reaction stops beyond the reaction wick** can be wide against a near target. For example, 18 Nov 10:00 has a
   26-pip stop against an 8.8-pip target. Options:
   - keep (reported as `reward_to_risk`);
   - cap the stop at the zone plus buffer;
   - require a minimum reward-to-risk.
4. **Dashboard:** the forecast is not shown on the STP tab yet (out of scope here).
5. **Enable the observational writer on demo?** That needs a deploy decision (`enabled = true`). With it off, deploying
   this branch changes nothing.
6. **Lifecycle:** technical forecasts have their own simple lifecycle (validity 8 h, then target, stop or structural
   invalidation). They are not part of the approved keeper. Merging them into it would be a separate decision.
