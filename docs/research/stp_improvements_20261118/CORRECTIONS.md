# Structural Trade Planner — corrections of 18 November 2026

Owner's brief "Consolidated Improvements, Defect Corrections and Autonomous Deployment" (18 November 2026). Observe
only throughout: nothing here authorises, opens or manages a trade; planner-based trading authorisation does not exist
and was not added.

## 1. D-1 — destination reachability

### Root cause

Admission (`planner/assess.py`, `destination_first_applies`) asked whether the primary destination's edge was more
than 3 pips beyond the **last close**. The lifecycle (`planner/keeper.py`, "destination reached before entry")
asks whether a 5-minute candle's **extreme** came within 3 pips of the destination zone (`planner/zones.py`
`interacts`). The two disagree whenever the close is more than 3 pips away but the candle's low (sell) or high (buy)
is within 3 pips: the recommendation is issued, and the next touch ends it.

17 November, real sell-price candles:

| Analysis | Last candle before it | Primary destination | Old admission | Result |
|---|---|---|---|---|
| 20:24:13 (rec 1) | 20:15 low 1.32083 | 1.32000 | issued | correct |
| 22:00:02 (rec 2) | 21:55 low **1.32013**, close 1.32035 | 1.32000 | close 3.5 pips away → issued with the check on | invalidated 22:05 "destination reached before entry" |
| 23:00:03 (rec 3) | 22:55 low **1.31989**, close 1.32016 | 1.32000 | close inside 3 pips → issued with the check **off** | superseded 00:00 |

### Correction

`planner/zones.py` `reached`: a destination is already reached when the latest finished 5-minute candle reaches it
by the lifecycle's own touch rule (same zone edges, same one-sided 3-pip allowance, same sell price). In
`assess.py`, a plan whose primary destination is already reached is **not issued**:
`no_recommendation` says so with the candle and its extreme, and the plan carries `destination_reached`.
`destination_first_applies` now uses the same zone edges (the destination wholly beyond price); a destination price
has gone well past (the whole candle beyond it, untouched) is still "on the way", as before.

At the hourly re-check of a live recommendation (`keeper.py` `replan`), a plan refused because the recommendation's
**own** primary destination is reached ends it with the before/after distinction kept: COMPLETED "after the zone" if
it had been ACTIVE, INVALIDATED "destination reached before entry" if not. (Before, any refused plan ended it as
"supporting evidence changed".) No time-based expiry was added.

### Change in admission behaviour

- No recommendation is issued with its primary destination already touched by the latest finished candle.
- Replayed on the real 17 November data with the new code: 20:24 rec 1 **issued** (unchanged); 22:00 rec 2 and 23:00
  rec 3 **not issued** ("the primary destination 13200 is already reached (the Tue 17 Nov 21:55 GMT 5-minute candle
  reached 13201.3, within 3 pips of the destination zone 13189.7-13200)").
- The overnight records show the same pattern: recs 4 (00:00) and 6 (02:00) were issued with the 23:55 / 01:55
  candle already within 3 pips of the primary destination 1.32025, and completed five minutes later.
- One existing functional test (`test_15…`, the mirrored lagging-MACD market) ends with price 0.4 pip under its
  primary destination and the last candle's high 1.7 pips inside the destination zone, so its final plan is now
  refused. The test's subject (a negative MACD line is not a veto) is unchanged and is now checked on the candle
  before (issued) and at the end (still not a MACD veto); it additionally asserts the D-1 refusal. No assertion was
  removed.

## 2. Pre-creation activation

### Investigation

Event-processing semantics before the correction (`keeper.py` `run`):

1. 5-minute checks on every candle finished since `m5_checked_until` (the end of the last candle seen by the previous
   run). The candle running when a recommendation is created is therefore checked in the next run, although it began
   before creation.
2. On creation, `five_minute(last_finished_candle, entry_only=True)` asked "is price already in its zone?" using the
   candle that **finished before the recommendation existed**, and set ACTIVE.

Only 5-minute candles are stored (`prices/model.py` TIMEFRAMES: 5m, 1h, 4h, 1d, 1w; no ticks), so the moment inside a
candle cannot be known.

Production records 17–18 November:

| Recommendation | Created (UTC) | Recorded ACTIVE | From candle | Timing |
|---|---|---|---|---|
| …20261117-2024-1 | 20:24:13 | 20:25:00 | 20:20–20:25 | overlapped creation |
| …20261118-0000-4 | 00:00:03 | 00:00:03 | 23:55–00:00 | **finished before creation** |
| …20261118-0100-5 | 01:00:02 | 01:00:02 | 00:55–01:00 | **finished before creation** |
| …20261118-0200-6 | 02:00:02 | 02:00:02 | 01:55–02:00 | **finished before creation** |
| …20261118-0300-7 | 03:00:02 | 03:00:02 | 02:55–03:00 | **finished before creation** |

So the look-ahead was real and frequent: 5 of 7 activations rested on price movement from before the recommendation
existed, 4 of them entirely before it.

### Correction

`keeper.py` `five_minute` classifies each candle against `created_utc` (`candle_timing`):

- **before creation** (ended at or before it): never used;
- **overlapped creation** (began before, ended after — every hourly analysis creates a few seconds after the hour,
  so this is the first candle of every recommendation): what it shows (zone and/or destination reached) is recorded
  as an `ambiguous` event; no transition. The next candle decides;
- **after creation**: the lifecycle rules as before.

The creation-time "already in its zone?" check now records `in zone at creation` (recorded only, "not an
activation"). Several interactions inside one post-creation candle follow the existing order (destination first).
Restart and recovery are unchanged in principle: candles are still processed from `m5_checked_until`, in order, and
the same classification applies whether the planner ran every 5 minutes or caught up (tested). A live recommendation
created before the correction keeps its recorded rules until its next hourly re-check.

Consequence: a recommendation issued with price in its zone becomes ACTIVE at the end of the first full candle after
creation that reaches the zone (about 10 minutes after an hourly analysis), never at creation.

### Retrospective evaluation

The dashboard (`dashboard/stp.py` `activation_review`) re-reads each recorded activation: if its candle was not
after creation, the confirmed activation is the first finished candle that began after creation and reached the
original zone by the touch rule, before the recorded end; otherwise none. Counts, times and excursions use the
confirmed activation; completions without one are not counted as "reached after the zone". The planner's files are
never changed; each correction is listed on the page. On the production data (7 recommendations): 5 activations
corrected; rec 1 moves to the 20:25 candle; recs 5 and 7 to the 01:05 and 03:05 candles; recs 4 and 6 have no
confirmed activation (their completions rested on the candle running at creation).

## 3. Reporting

- **A. Candle timing.** Every `active`, `completed` and `invalidated` 5-minute event carries `candle_start_utc`,
  `candle_end_utc`, `candle_timing` (after / overlapped / before creation), `qualifying_event_utc` (null: not knowable
  from 5-minute candles) and `event_time_basis`. The recommendation keeps `activation`. `ambiguous` and
  `in zone at creation` events carry the same fields. Nothing is inferred from OHLC order.
- **B. Structural snapshot.** Every plan carries `structure` (`assess.py` `structure_snapshot`): every level of the
  level map (price, name, kind, family, timeframe, origin, fixed), every zone (edges, class, families, members) and
  the last 24 four-hour, 12 daily and 24 hourly swings with the time each became known. It is built from the same
  objects the plan used, at the plan's time (tested: identical when the store is cut at that time; no origin or
  swing after it). `issued.jsonl` gains `structural_snapshot`, `candidates`, `h4_last_swing` and
  `analysis_as_of_utc`; existing lines and identifiers are untouched. Both are reporting only, inside try/except;
  about 30–60 KB per recommendation.

## 4. Files changed

`planner/assess.py`, `planner/zones.py`, `planner/keeper.py`, `dashboard/stp.py`, `dashboard/static/stp/stp.js`,
`dashboard/static/stp/stp.css`, docs, tests (`tests/technical/test_stp_corrections.py` new; one functional test
extended as described in section 1). Not changed: strategies, orders, trade management, risk, the price service,
settings, `.env`, the 3-pip and break parameters.
