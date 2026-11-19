# Structural Trade Planner — Market Phase Intelligence: research, design and validation

GBPUSD, AutoBot. Written 18 November 2026, around 22:30 UTC. **Research and offline validation only.**

The research model lives in an isolated worktree, `/home/autobot/worktrees/autobot-stp-phase`, on branch `research/stp-market-phase`. The branch adds new files only, and they are **not committed yet**. Production `/opt/autobot` was not touched: `main` is still at `3d50353`, no file was changed, no service was restarted, no setting or switch was added, no order was sent, nothing was shadow-traded and IG was not contacted. The live observe-only planner keeps running exactly as before. Nothing in production imports the new module, and a test checks that.

**Update, 19 November 2026** (the owner sent the brief again):
- The work below is now **committed on branch `research/stp-market-phase`**, with this report copied into `docs/research/stp_market_phase_20261118/`.
- The findings and numbers are unchanged; nothing was re-tuned.
- The full repository suite was run on the branch (see the commit).
- Production is still untouched by this work. The live service still runs 3d50353. The server's `main` checkout was fast-forwarded to d7d2651 (Stage 4, all switches off) during the paused Stage 4 go-live on 19 Nov, not by this work.

Supporting files are in this folder:

| File | What it is |
|---|---|
| `REPLAY_2026-11-18.md` | the 18 November replay, every 15 minutes and at each trade |
| `data/results.json` | every validation number in this report |
| `data/points.jsonl.gz` | 16,369 hourly decisions with their outcomes (gzip; the original `points.jsonl` stays in `/home/autobot/research/stp_market_phase_20261118/data/`) |
| `data/compat.json` | fast-path vs live-planner check |
| `data/conditions.json` | market-condition catalogue |
| `data/live_trades_classified.json` | all 86 live trades, labelled |
| `replay_2026-11-18/` | full JSON of every replay view |

---

## Executive summary

1. **Root cause (A).** On 18 November the live planner lost direction because of one 4-hour swing high. The 17 Nov 18:00 spike to 13227.9 was confirmed as a swing at 08:00. It sits **3.4 pips** above the previous swing high (13224.5), so the swing sequence became "mixed". In V1, `planner/assess.py` `direction()` returns NEUTRAL for any mixed sequence before any other evidence is looked at. That makes it an **absolute veto**: the EMA stack, the EMA100 and its slope were all bearish and were never weighed. The planner stayed NEUTRAL all day because no new 4-hour swing could confirm. A swing low needs a 40-pip move back up within 6 candles, and the market kept falling.

2. **Model (B, C).** I built a research model that separates three things:
   - **dominant direction**: tolerance-aware 4-hour structure plus EMA votes, where the structure can never be outvoted;
   - **market phase**: impulse, exhaustion, correction, resistance or support test, continuation, consolidation, structural reversal;
   - **opportunity class**: trend-aligned, countertrend correction or structural reversal.

   For corrections it adds the first meaningful opposing level, the corrective destination, the invalidation, the room after the spread, and the return-to-trend setup. Nothing it produces authorises anything.

3. **18 November replay (D).** The model keeps **BEARISH all day**, regaining the 12 hours V1 lost.
   - **07:30 Asian range breakout sell:** read as trend-aligned, in a continuation after the 17 Nov correction.
   - **09:30 Bollinger bounce buy:** read as a correction inside a bearish market. The trend was not flipped. It identified the resistance at entry: a Major zone 13162.2–13172.3 holding the previous day's low and the daily S1. The correction peaked at 13175.6. But the buy was entered **at** that zone (offer about 13162.9, its near edge 13162.2), so the model judges the room insufficient (−0.7 pips to the zone's near edge, 9.4 pips to its far edge, against a 10-pip minimum). Measured from the low, the opportunity had 12.7 pips of room.
   - **12:00–16:00:** a resistance test with continuation signals.
   - **16:37 slow grind sell:** flagged "trend-aligned, caution: exhaustion". Its proposed correction zone, 13148–13157.7, contained the 16:58 spike (peak 13157.5) that stopped both afternoon sells.

4. **Broader validation (E): the evidence does not support the direction fix as a forecasting improvement.** The data is 2.7 years, 16,369 hourly decisions, 10,241 of them in trading hours.
   - Neither V1 nor any new variant forecasts direction: V1 is right 51.6% of the time on first passage to ±0.5 ADR, the new default 49.4%, with weekly-bootstrap intervals spanning 50%.
   - **The hours the tolerance adds are worse than chance**: 41.0% on marginal-violation hours (bootstrap 30–51%).
   - Walk-forward selection of the tolerance is unstable, and V1 beats the chosen setting in 8 of 9 out-of-sample windows.
   - Against a random-walk baseline with symmetric stops, the phases **describe the market but barely forecast it**. Exhaustion and impulse each sit about 2 points above chance. Level tests and continuations show no edge. Countertrend destinations show a small edge (+5 points, weak evidence).
   - What does hold up: **structural zones mark where corrections stop better than indicators.** Once reached, a structural zone stopped the correction 42% of the time, against 29–31% for an EMA21, Bollinger-middle or 38.2% band of the same width.

5. **Recommendation (H).**
   - **Do not replace the V1 direction rule** with the tolerance rule, and **do not use phases for any authorisation.**
   - The evidence supports, at most, **recording the phase and opposing-level intelligence next to V1 in the observe-only planner**, as extra reporting for your review. That needs your separate approval. It is not deployed.

---

## A. Root-cause analysis: why the planner lost directional conviction on 18 November

**How V1 decides direction** (`planner/assess.py` `direction`, `planner/structure.py` `structure`):

1. 4-hour swings use the existing turning-level rule with the approved numbers:
   - 3 candles each side;
   - a move of at least 40 pips within 6 candles;
   - a swing counts only from `known_utc`.
2. Only the **last two swing highs and last two swing lows** are compared: both lower is down, both higher is up, anything else is **mixed**.
3. Mixed returns **NEUTRAL immediately** (`if st.sequence == MIXED: return NEUTRAL`).
4. The EMA stack, the EMA100 and its slope are calculated in `observations()` and appended to the evidence as "supporting". They **never change the result**.
5. A NEUTRAL direction means "no recommendation until it is BEARISH or BULLISH". No zone, condition or opportunity is worked out.

**Corrections versus reversals in V1.** Both are worked out only inside a BEARISH or BULLISH direction:
- `condition()` labels CORRECTION_ACTIVE, CORRECTION_LIKELY, EXHAUSTION and CONTINUATION from 4-hour MACD, RSI and Bollinger, plus hourly closes over the hourly Bollinger middle;
- a reversal is either a confirmed 4-hour close beyond the last opposite swing (TRANSITIONAL), or a 4-hour MACD cross against the structure (REVERSAL_RISK).

**Recommendation lifecycle (unchanged).** One live recommendation at most. Hourly re-plans create, support, change, supersede or invalidate it. 5-minute checks move WAITING→ACTIVE→COMPLETED, or invalidate when the destination is reached first. The 18 Nov corrections (D-1 and no pre-creation activation) are in place. A direction change to NEUTRAL invalidates a live recommendation.

**18 November.** Recomputed with the live code (`planner show`, read only) and reproduced by the new model's built-in V1 rule:

| Time | Last two swing highs | Last two swing lows | V1 |
|---|---|---|---|
| 07:00 | 13250.9 → 13224.5 (lower) | 13312.2 → 13168 (lower) | BEARISH |
| 08:00 | 13224.5 → **13227.9 (+3.4 higher)** | 13312.2 → 13168 (lower) | **NEUTRAL** ("mixed") |

At 08:00 the 04:00–08:00 candle fell to 13172.8, more than 40 pips below 13227.9. That completed the swing high from the 17 Nov 16:00 candle. The day's ADR was 70.3 pips, so the violation was 0.05 ADR. All three EMA signals stayed bearish:
- the 7/13/21 stack pointed down;
- the close was below the EMA100;
- the EMA100 fell 13.7 pips over 6 candles.

**Why it stayed NEUTRAL.** Leaving "mixed" needs a new confirmed swing:
- a lower high, which needs price to rally and then fall 40 pips; or
- a lower low, which needs a turn followed by a 40-pip rally.

The market fell steadily with no 40-pip bounce, so no swing could confirm. **Mixed H4 structure is an absolute directional veto in V1.** No combination of other evidence can override it.

---

## B. Proposed architecture

```
                 4-hour swings (approved rule)      4-hour EMA 7/13/21, EMA100, slope
                         │                                   │
                         ▼                                   ▼
        ┌──────────────────────────────────────────────────────────────────┐
        │ A. DOMINANT DIRECTION  BULLISH / BEARISH / NEUTRAL                │
        │   structure vote (-2..+2, tolerance + break of structure),         │
        │   EMA votes (-3..+3); the structure can never be outvoted          │
        └──────────────────────────────────────────────────────────────────┘
                         │ (NEUTRAL → CONSOLIDATION; broken → STRUCTURAL_REVERSAL)
                         ▼
        ┌──────────────────────────────────────────────────────────────────┐
        │ B. MARKET PHASE (inside the dominant direction; hourly + 5-minute) │
        │   impulse start = last 4h opposite swing; E = extreme since; C =   │
        │   counter-extreme since E                                          │
        │   TREND_IMPULSE → EXHAUSTION → COUNTERTREND_CORRECTION →           │
        │   RESISTANCE_TEST / SUPPORT_TEST → TREND_CONTINUATION → (new E)    │
        └──────────────────────────────────────────────────────────────────┘
                         │                         ▲
                         ▼                         │ planner zones (planner/zones.py)
        ┌──────────────────────────────────────────────────────────────────┐
        │ C. OPPORTUNITY  TREND_ALIGNED / COUNTERTREND_CORRECTION /          │
        │   STRUCTURAL_REVERSAL  (+ countertrend plan, continuation plan)    │
        │   authorises = False, always                                       │
        └──────────────────────────────────────────────────────────────────┘
                         │
                         ▼
        classify_trade(view, direction, reversal_trigger): a LABEL for a strategy's trade
        (TREND_ALIGNED / COUNTERTREND_CORRECTION / COUNTERTREND_UNSUPPORTED / NO_DIRECTIONAL_VIEW /
         STRUCTURAL_REVERSAL); never an authorisation, never a reversal of an open trade
```

Each layer reads only finished candles. The phase is stateless: it is worked out afresh from data at each moment. That makes look-ahead impossible to introduce through hidden state, and restarts trivially safe.

---

## C. The market-phase model and its evidence requirements

Code: `planner/phase.py`, about 700 lines. Every parameter is in `PhaseParams`. **None was fitted**: each comes from first principles or from an existing approved number, and the sensitivity is reported in E.

### A. Dominant direction

| Rule | Definition | Source of the number |
|---|---|---|
| Tolerance | two swings closer than max(5 pips, 0.15 × ADR) are "equal" | the planner's own zone width, i.e. its definition of "the same level" (`line_up_within_pips`, `zone_width_adr_share`) |
| Structure vote | −2 clean down; −1 down with one side equal (a marginal violation) or down by a break of structure; 0 mixed, range or broken; +1/+2 mirrored | — |
| Break of structure | after the most recent swing, a 4-hour close ≥ 3 pips beyond the most recent opposite swing | `hourly_read.break_beyond_pips` (3) |
| Structural break | a 4-hour close ≥ 3 pips beyond the last opposite swing against the structure: vote 0 and phase STRUCTURAL_REVERSAL (V1's TRANSITIONAL) | V1 rule |
| EMA votes | 7/13/21 stack; close vs EMA100; EMA100 slope over 6 candles ≥ 2 pips | `planner.ema_slope_candles` |
| Decision | BEARISH if the structure vote ≤ 0 and the score ≤ −3; BULLISH mirrored; otherwise NEUTRAL | — |
| Option (off by default) | a genuinely mixed structure is directional when all three EMA votes agree | evaluated as "consensus" |

### B. Phase (bearish written; bullish mirrored)

The extreme E and the corrective extreme C are located to the 5-minute candle.
- **Correction under way:** an hourly close above the hourly EMA21 or Bollinger middle since E, or C − E ≥ 0.2 × ADR.
- **Order of checks:**
  1. TREND_CONTINUATION
  2. RESISTANCE_TEST
  3. COUNTERTREND_CORRECTION (when a correction is under way)
  4. EXHAUSTION or TREND_IMPULSE (when E is under 2 hours old)
  5. EXHAUSTION, CONSOLIDATION (a stall) or TREND_IMPULSE (paused)
- **Exhaustion** needs ≥ 2 signs, at least one of them a *turn* sign:
  - turn signs: band extension then back inside, RSI3 back above 30, hourly MACD histogram rising twice below zero, a rejection candle at the low;
  - context signs: ≥ 0.25 ADR from the EMA21, at a meaningful support zone, a 4-hour low through the lower band.
- **Continuation** needs both:
  - renewed hourly alignment (EMA7 < EMA13);
  - a rejection: an hourly close back below the EMA21 after closing above it, or a close ≥ 3 pips below the corrective support (the low of the last hour before C);
  - and no hourly close through the zone C tested.
- **Resistance test:** the latest hour reached a meaningful zone above E with no close through it.

### C. Countertrend intelligence (offline evaluation only)

- **Meaningful opposing level**, defined by structural evidence:
  - meaningful: a **Major zone**, or a **Moderate zone holding a higher-timeframe level** (4-hour or daily swing, daily or weekly pivot or R/S, previous day's or week's high or low);
  - not meaningful on their own: moving averages, round numbers, hourly swings, session levels;
  - the zone the move launched from is excluded.
  - A looser alternative is evaluated in E.
- **Proposed plan:**
  - entry zone at E;
  - first obstacle (any level);
  - first meaningful zone;
  - destination at the zone's near edge (its far edge if price is already inside);
  - "maximum expected" at the far edge;
  - invalidation at an hourly close 3 pips beyond E.
- **Room** is measured from the fill price (sell price + spread for a buy). It is sufficient when it is ≥ max(10 pips, 4 × the spread). The plan is "spent" when C has already reached the zone and fallen back.
- **Return-to-trend.** The plan names the zone where a trend-aligned trade could follow a rejection. That trade still needs an independently valid strategy trigger and the existing risk approval. It is **never** a reversal of the open trade.
- **Strategy reversal patterns.** A reversal-pattern strategy's own trigger can count as the turn right after a new extreme, provided ≥ 2 context signs are present. The strategies are Bollinger bounce, level reversal, session sweep, New York open reversal and range trade. This is the only way the model "sees" an intra-hour turn before the hour closes. The bounce's entry rules are untouched.

---

## D. Historical replay — 18 November 2026

Full table: `REPLAY_2026-11-18.md`, every 15 minutes, 00:00–19:45, with the live planner's direction at each hour. The replay uses the live planner's own snapshot, existing levels and zones (`exact_inputs`), and only candles finished at each time. A test checks it is identical with later candles removed.

| Time | V1 | New direction | Phase | What the model said |
|---|---|---|---|---|
| 00:00–02:45 | BEARISH | BEARISH | COUNTERTREND_CORRECTION | the 17 Nov rally (13168 → 13227.9) is a correction in a bearish market |
| 03:00–07:45 | BEARISH | BEARISH | **TREND_CONTINUATION** | correction ended (renewed alignment, close through support); SELL setup, invalidation above 13230.9 |
| **07:30 ARB SELL** | | | | **TREND_ALIGNED**: the bearish return was recognised |
| 08:00 | **NEUTRAL** | **BEARISH** (marginal: +3.4 < 10.5 tolerance) | EXHAUSTION | new swing high confirmed; the low at 13170.1 shows a rejection candle and stretch; first meaningful resistance 13183.8–13192.9 (daily/4h swing lows) |
| 08:15–08:45 | NEUTRAL | BEARISH | TREND_IMPULSE | new lows 13163.9 → 13159.0 |
| 09:00 | NEUTRAL | BEARISH | EXHAUSTION | low 13150.6 with a rejection candle; resistance 13162.2–13172.3 (Major: daily swing low, **previous day low 13168**, 4h swing low, **daily S1 13172.3**); room from the low 10.1 |
| **09:30 BB BUY** | NEUTRAL | BEARISH | TREND_IMPULSE (low 13148, 20 min old) | **COUNTERTREND context recognised** (stretch, at support, 4h band; the bounce supplies the turn) **but room insufficient**: the fill at about 13162.9 (offer) is already at the Major zone's near edge 13162.2 (−0.7 pips); far edge 13172.3 gives 9.4 pips; the minimum is 10. Room from the low was 12.7. Invalidation: an hourly close ≤ 13145. **Not authorised; the trend is not flipped** |
| 09:45–11:45 | NEUTRAL | BEARISH | RESISTANCE_TEST | the correction tests 13162–13182; actual peak **13175.6** (10:55) |
| 12:00, 13:00, 14:30, 16:00 | NEUTRAL | BEARISH | TREND_CONTINUATION | SELL setup, invalidation hourly close ≥ 13178.6, destination 13148 |
| **12:37 EMA SELL**, **15:44 breakout SELL** | | | RESISTANCE_TEST / CONTINUATION | TREND_ALIGNED |
| 16:15–16:30 | NEUTRAL | BEARISH | TREND_IMPULSE | new lows 13143.8 → 13135.5 |
| **16:20 EMA SELL** | | | TREND_IMPULSE | TREND_ALIGNED; first meaningful resistance just 3 pips above (13148–13157.7) |
| **16:37 slow grind SELL** | | | EXHAUSTION | TREND_ALIGNED **with the caution "a correction is likely before continuation"**; correction zone 13148–13157.7. The 16:58 spike peaked at **13157.5** and stopped both sells at 13153.1, inside that zone |
| 17:00–19:15 | NEUTRAL | BEARISH | RESISTANCE_TEST | the bounce tests 13148–13157.7 |
| 19:30 | NEUTRAL | BEARISH | TREND_CONTINUATION | invalidation ≥ 13160.5 |
| **19:50 level reversal SELL** | | | TREND_CONTINUATION | TREND_ALIGNED. This 7th trade of the day opened after the earlier impact report: −11.3 pips on the bot's record |

**Answers to §6 of the brief:**

- **07:30 sell:** yes. The bearish direction and continuation were recognisable, under both V1 and the new model.
- **09:30 bounce buy:** partly.
  - The model recognised a legitimate correction context inside a bearish trend without reclassifying the trend.
  - It identified the first meaningful resistance correctly at entry time. The correction stopped 3.3 pips above the zone top.
  - By its a priori cost rule, it judged the trade as entered too close to that resistance.
  - It does not approve the trade, and it was not built to approve all winners.
- **Return of bearish pressure:**
  - it was identified at 12:00, after the resistance rejection, with an invalidation that held. Price never closed at 13178.6;
  - the destination 13148 was reached at 16:15, and the low broke at 16:20;
  - the afternoon sells were all trend-aligned. The two losing ones (16:20 and 16:37) were taken at a fresh extreme, where the model saw exhaustion or the first resistance 3–6 pips away.

---

## E. Broader historical validation

**Data.**
- Candles: the research store `data/research/stp_phase_store/GBPUSD`. It holds the replay store's 5-minute, hourly and daily candles from Jan 2024, plus the live store from 10–18 Nov and the weekly candles.
- **Jan 2024 – Feb 2026 is the vendor's price history, not IG's** (0.3–0.5 pips from IG). There is no data from early Feb to 23 Mar 2026.
- Decisions: every hourly close from 1 Mar 2024 to 18 Nov 2026, **16,369 points** (10,241 in trading hours, 06:00–20:30 UK weekdays). They were collected walk-forward with `research/stp_phase/collect.py`.

**Speed path checked against the live planner** (`data/compat.json`), on 120 random hours:

| Check | Agreement |
|---|---|
| Fast path's V1 direction = live `plan_at` | 120/120 |
| New direction, fast vs exact | 120/120 |
| Phase, fast vs exact | 117/120 |
| First meaningful zone overlaps | 17/23 (the fast path leaves out session highs and lows) |

**Uncertainty.** Hourly decisions overlap, so point counts overstate the evidence. The direction comparisons carry a **weekly block-bootstrap** 95% interval, and phase results are also counted per **episode** (one extreme). No result below is claimed as statistically significant unless its interval excludes the baseline.

### E1. Dominant direction accuracy, coverage, and quality vs frequency

"Accuracy" is whether price reached 0.5 ADR in the forecast direction before 0.5 ADR against, within 72 hours. Same-candle and unresolved cases are excluded. Coverage is the share of trading hours with a direction.

| Direction rule | Coverage | Accuracy (first passage) | Weekly-bootstrap 95% | 24 h return sign |
|---|---|---|---|---|
| **V1 (live)** | 49.2% | **51.6%** (n 4,956) | 47.3–55.7% | 52.3% |
| Structure + EMA confirmation, no tolerance, no BOS | 39.0% | 51.3% | 46.2–56.3% | 50.9% |
| Tolerance 0.15 ADR only | 47.1% | 49.1% | 44.0–54.4% | 49.4% |
| Break of structure only | 50.7% | 51.0% | 46.5–54.9% | 49.8% |
| Tolerance 5 pips + BOS | 53.1% | 50.3% | 45.7–54.3% | 49.6% |
| Tolerance 0.05 ADR + BOS | 53.0% | 50.4% | 45.9–54.4% | 49.7% |
| Tolerance 0.10 ADR + BOS | 53.3% | 50.2% | 45.6–54.3% | 49.4% |
| **Default: tolerance 0.15 ADR + BOS** | **55.0%** | **49.4%** (n 5,506) | 44.7–53.5% | 49.1% |
| Tolerance 0.25 ADR + BOS | 57.5% | 49.7% | 45.1–53.7% | 49.5% |
| Default + EMA consensus when mixed | 70.7% | 50.2% | 46.6–54.0% | 50.7% |
| Baseline: 24 h momentum | — | 50.8% | — | — |
| Baseline: share of "up first" | — | 50.2% | — | — |

**The hours the new rules add** are those where V1 was NEUTRAL and the default directional: 1,733 points on 184 days in 88 weeks.

| Subset | Accuracy | Weekly-bootstrap 95% |
|---|---|---|
| All added hours | 45.7% | 38.8–52.9% |
| Marginal violation (tolerance) | **41.0%** (1,029 points, 114 days) | **30.4–50.5%** |
| Break of structure | 53.0% | 44.6–61.0% |

When V1 is directional, the default agrees 77.4% of the time and is NEUTRAL the other 22.6%, for lack of EMA confirmation. It is never opposite.

**Walk-forward.** The tolerance was chosen on 6 months and tested on the next 3, over 9 windows. The chosen setting changed almost every window (0.25, 5 pips, 0.10, 0.05, 0.25, 0.25, none, none, 0.10). It beat V1 out of sample in **1 of 9** windows, and the fixed default in 3 of 9.

**Reading.** On this history, 4-hour structure direction, with or without the changes, **does not forecast** 24–72-hour moves better than a coin. The marginal-violation hours, the exact case that fixes 18 November, were on balance **worse** than chance. Their upper interval bound is 50.5%, so this is weak evidence of harm and certainly no evidence of help. **The tolerance rule makes 18 November look right; the history says it would not have made the planner more right in general.** Varying the tolerance only trades coverage for nothing.

### E2. Market-phase classification quality

The phases are judged against a fair baseline: on a driftless random walk, P(target before stop) = stop distance ÷ (target + stop). Stops are wick-based (symmetric) in this table. The planner's real invalidations are close-based, and they score higher because a wick does not invalidate. Those figures are in `results.json` → `geometry`.

| Phase test | Resolved | Observed | Random-walk expectation | Edge |
|---|---|---|---|---|
| TREND_IMPULSE (fresh extreme): 0.2 ADR bounce before a new extreme | 494 | 31.4% | 29.1% | +2.3 |
| EXHAUSTION (fresh extreme): the same | 559 | 39.7% | 37.6% | +2.1 |
| RESISTANCE/SUPPORT TEST: 0.2 ADR move with the trend before price goes through the zone | 3,932 | 49.4% | 47.6% | +1.8 |
| TREND_CONTINUATION: new extreme before the invalidation | 1,852 | 53.4% | 54.1% | −0.7 |
| COUNTERTREND opportunity: destination before invalidation (48 h) | 622 | 56.9% (53.0–60.8) | 51.5% | **+5.4** |

Exhaustion looks better than impulse (39.7% vs 31.4%) only because exhaustion points sit further from the extreme. Against the baseline, neither carries an edge.

With the planner's close-based invalidations:
- continuation: new extreme first in 59.6% of points; first signal per episode 56.9% (51.6–62.0%, 348 episodes); **false continuations 40.4%**;
- countertrend: first signal per episode 56.4% (299 episodes);
- level tests rejected: 60.0%.

Phase mix over trading hours:

| Phase | Share |
|---|---|
| CONSOLIDATION (mostly NEUTRAL direction) | 34.3% |
| RESISTANCE_TEST | 12.9% |
| SUPPORT_TEST | 12.8% |
| TREND_CONTINUATION | 11.6% |
| STRUCTURAL_REVERSAL | 10.8% |
| COUNTERTREND_CORRECTION | 10.5% |
| TREND_IMPULSE | 3.8% |
| EXHAUSTION | 3.4% |

Resistance and support tests are frequent because the planner's zones are dense, about one every 10 pips.

### E3. Which exhaustion evidence is useful

Measured at fresh extremes in TREND_IMPULSE or EXHAUSTION: did a 0.2 ADR bounce come before a new extreme? 1,053 resolved points; base rate 35.8%.

| Evidence | With | Without |
|---|---|---|
| RSI3 back above its line | **46.1%** | 34.1% |
| MACD histogram contracting | **43.4%** | 35.2% |
| Rejection candle | 38.0% | 34.9% |
| Band extension back inside | 36.9% | 35.5% |
| At meaningful support | 35.7% | 36.2% |
| 4-hour band extension | 34.4% | 37.0% |
| Any turn sign | 39.6% | 31.5% |

- Best pairs: RSI + 4-hour band 50.0% (n 54); RSI + stretch from EMA21 48.1% (n 129).
- **No combination makes a bounce more likely than continuation.**
- More signs did not mean better odds: 2 signs 34.7%, 3 signs 38.4%, 4 signs 36.2%.
- Only RSI recovery and MACD contraction carry information. The evidence set was **not** re-tuned to these findings, to avoid fitting.

### E4. Corrective destinations and resistance/support identification

Measured per episode: the first countertrend view of each extreme, against where the correction actually stopped before a new extreme or 72 h. 1,091 episodes. Each baseline band has the same width as the zone (about 8.7 pips).

| Level identified before the correction | n | Reached | Stopped in it | Overshot | Stopped, given reached |
|---|---|---|---|---|---|
| **Strict meaningful zone (the model)** | 938 | 53.5% | **22.5%** | 31.0% | **42.0%** (37.8–46.4) |
| Loose meaningful zone | 903 | 55.1% | 24.0% | 31.1% | 43.6% |
| Hourly EMA21 band | 987 | 28.8% | 8.8% | 20.0% | 30.6% |
| Hourly Bollinger middle band | 984 | 27.9% | 8.2% | 19.7% | 29.5% |
| 38.2% retracement band | 993 | 27.0% | 7.9% | 19.1% | 29.1% |

- **Structural zones are clearly better than indicator levels** at marking where corrections stop. Conditional on being reached, the intervals do not overlap.
- The strict definition was no better than the loose one.
- Corrections went **through** the zone 31% of the time.
- Whether resistance can be identified before the trade opens: yes, as a zone, with a 42% chance of stopping a correction that reaches it.

### E5. Market conditions

The days are labelled with hindsight, for scoring only (`data/conditions.json`). "Correct direction at 10:00" compares the direction given at 10:00 UK with the day's net move.

| Kind of day | Days | Coverage V1 → new | Correct direction at 10:00, V1 | Correct direction at 10:00, new | Days with a countertrend opportunity |
|---|---|---|---|---|---|
| Strong bearish trend with a corrective rally | 101 | 40.9% → 48.6% | 19/43 | 24/49 | 27 |
| Strong bullish trend with a corrective decline | 108 | 44.7% → 55.6% | 28/50 | 34/60 | 45 |
| Range-bound (≤ 0.6 ADR) | 90 | 56.9% → 63.8% | 27/47 | 30/53 | 6 |
| False breakout of the previous day | 137 | 44.9% → 51.2% | 27/62 | 23/74 | 29 |
| Band walk (4+ hourly closes on a band) | 147 | 45.6% → 54.2% | 42/73 | 46/81 | 46 |
| Structural reversal (4-hour structure broken) | 174 | 24.3% → 25.9% | 13/56 | 11/53 | 18 (STRUCTURAL_REVERSAL phase on 139 days) |
| Marginal swing violation | 247 | 28.4% → 47.2% | 33/72 | 62/124 | 52 |

- Neither rule reliably calls the day's direction on any kind of day (most cells are near or below half).
- Range days rarely produce countertrend opportunities (6/90), which is correct.
- Structural reversals are flagged.

### E6. The model on every live trade (9–18 Nov)

There are 86 live trades, labelled with the exact inputs at entry (`data/live_trades_classified.json`; labels only, no P&L totals):

| Label | Trades |
|---|---|
| TREND_ALIGNED | 41 |
| NO_DIRECTIONAL_VIEW | 21 |
| COUNTERTREND_UNSUPPORTED | 18 |
| STRUCTURAL_REVERSAL | 6 |
| COUNTERTREND_CORRECTION | **0** |

- Every one of the 16 Bollinger bounces was NO_VIEW, UNSUPPORTED (mostly room under 10 pips to the first meaningful level, or no exhaustion), STRUCTURAL_REVERSAL, or (three sells on 17 Nov) TREND_ALIGNED.
- Eight trading days is far too few to judge anything.

---

## F. Countertrend management proposal (no change made)

The existing trade manager stays authoritative. Proposed sequence, each step needing your separate approval:

1. **Record, don't act.** For every trade, store the model's proposed exit intelligence next to the trade manager's actual management:
   - first obstacle;
   - first meaningful zone (near and far edge);
   - corrective destination;
   - structural invalidation;
   - return-to-trend zone.
2. **Offline comparison per trade.** Where did price actually stop, against the zone and against the trade manager's exit? On 18 Nov:
   - the 09:30 bounce peaked at 13175.6, 3.3 pips beyond its identified zone top 13172.3;
   - the 16:37 slow grind's identified correction zone 13148–13157.7 contained the spike (peak 13157.5) that stopped it at 13153.1.

   Do not read single days as proof. E4's 42% "stopped, given reached" and 31% overshoot are the honest base rates.
3. **Only then, possible options for you to consider:**
   - a countertrend trade's take-profit candidate at the zone's near edge;
   - a trail that tightens on reaching the zone;
   - a trend-aligned trade's stop placed beyond the zone's far edge plus 3 pips, rather than inside it.

   None is proposed for implementation now.
4. **Return-to-trend** stays a *separate* opportunity. The model never closes a buy and opens a sell. A new trade needs its own valid strategy trigger and the existing risk approval.

---

## G. Technical and functional test results

- **New tests: 43, all passing.**
  - `tests/technical/test_stp_phase.py` (26):
    - tolerance equal to the zone width;
    - marginal vs significant violations;
    - conflicting EMA evidence;
    - the structure cannot be outvoted;
    - break of structure;
    - structural reversal;
    - consensus off by default;
    - too few swings;
    - bull/bear symmetry;
    - the V1 rule reproduced;
    - meaningful vs nearest level;
    - the launching zone excluded;
    - classification never authorises;
    - the reversal-pattern turn needs context;
    - insufficient room;
    - the exhaustion caution;
    - missing data;
    - no production module imports the model;
    - no setting or switch added.
  - `tests/functional/test_stp_phase_scenarios.py` (17), on made-up markets built like the price service's candles:
    - **a valid corrective BUY coexists with a BEARISH dominant trend**;
    - **that BUY is not authorised and no SELL is initiated** (`continuation` is None, `return_to_trend.needs` requires an independent trigger, `authorises` is False everywhere);
    - return-to-trend after rejection, with invalidation at C + 3;
    - an impulse is not a correction;
    - a genuine reversal is a structural reversal;
    - mirror-image bull/bear interpretations;
    - the V1 rule matches the live planner;
    - **no look-ahead** (identical views with later candles removed);
    - **real 18 Nov candles**: direction held at 08:00; 07:30 continuation; the 09:30 buy read as a correction, with the previous-day-low resistance identifiable at entry and no authorisation; the afternoon sells trend-aligned.
- **Existing planner and STP suites, together with the new tests: 216 passed** (`test_planner`, `test_stp_corrections`, `test_stp_dashboard`, functional planner and STP dashboard scenarios). The full repository suite was not run: the branch adds new files only and changes no existing module. Another session was running a full suite in its own worktree at the time.

**Failures found during development, all fixed before the validation run:**
- the extreme was located only to the hour;
- the order of checks made exhaustion "sticky";
- the meaningful-zone definition was too permissive and accepted the launching zone;
- continuation checked the wrong zone.

These were logic errors found on 18 Nov. **The fixes were principled, not tuned to outcomes**, but 18 Nov was the development day, so its replay is in-sample by construction. The validation (E) was run once, after the model was settled. No parameter was changed after seeing it.

**Limitations.**
- The vendor data before Feb 2026 is not IG's own, and there is a Feb–Mar 2026 gap.
- The fast path leaves out session levels.
- Zones are dense, so tests are frequent.
- Zone building (existing `planner/zones.py`) anchors from the lowest level, so zone edges are not exactly mirror-symmetric. The tests check direction and phase symmetry, not edges.
- Hourly turn signals lag intra-hour turns. Strategy reversal patterns fill this gap by design.
- The room threshold (10 pips or 4 × spread) and the destination at the near edge are a priori choices.
- Outcomes are scored on hourly candles, and same-candle double hits are excluded.

**Unresolved questions for you.**
1. Is the dominant direction meant as a **forecast** or as **context**? As a forecast, neither V1 nor any variant has an edge here. As context, the tolerance gives fewer "silent" days, at the cost of directional calls that were no better than chance.
2. Should a countertrend opportunity's room be measured to the zone's near edge (current) or its far edge?
3. May a strategy's own reversal pattern stand in for the model's turn evidence?

---

## H. Deployment recommendation

**The evidence does not support replacing the live planner's direction rule.**
- The tolerance and break-of-structure changes fix 18 November.
- Across 2.7 years they add directional hours that were no better, and on marginal violations worse, than chance.
- Out-of-sample selection of the tolerance is unstable.
- V1 should stay the planner's dominant direction.

**The evidence does not support any use of phases or opportunity classes for trade authorisation.** Against fair baselines they carry little or no forecasting edge. The exceptions are structural zones as resistance markers, and a small, weakly evidenced edge for countertrend destinations.

**What the evidence does support**, if you want it, subject to your separate approval:
- **integrating the phase layer and the countertrend/opposing-level intelligence into the observe-only STP as additional recorded output**: phase, opportunity class, first meaningful zone, destination, invalidation, and a per-trade label;
- keeping V1's direction and recommendations unchanged;
- showing the tolerance-based direction alongside, only as an observed alternative;
- building live-demo evidence, especially on structural zones (E4), the one part with a clear advantage.

Nothing has been deployed or activated. The research code is uncommitted in `/home/autobot/worktrees/autobot-stp-phase` (branch `research/stp-market-phase`), ready to commit or discard.
