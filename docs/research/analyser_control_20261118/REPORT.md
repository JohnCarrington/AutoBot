# Putting every strategy back under the analyser: stages 1 to 3, and stage 1b

Branch `feature/analyser-control`, built 18 November 2026 from main (dd9d36d). **Nothing is merged, deployed or switched on.** Main, the live checkout, the running service and the live `.env` were not touched, and nothing was restarted. All three new switches are **off** if left out of `.env`, and the live `.env` doesn't have them, so the bot would behave exactly as today even with this code.

Everything below checks that the code does what your rules say, on named days. Nothing judges profit. The pips shown for paper trades come from the replay's trade manager and are given only so you can see how each trade ended.

## Stage 1b: the analyser must still call trends quickly (owner, 18 November 2026, afternoon)

**This section is the current state of the branch.** The sections further down are the earlier report on stages 1 to 3, written before stage 1b. Their switched-on results for 13 and 17 November are replaced by the ones here (13 November's states and trades did not change). All three switches are still **off** if left out of `.env`. Nothing is merged, deployed or switched on, and nothing was restarted.

### What was added (all behind `ANALYSER_USES_HOURLY`; design 2.10, stage 1, points 5 to 7)

1. **The trend proof works from any state.**
   - In ranging or consolidation, whatever the hourly read says, the existing trend proof (2.5) is watched both ways, with the same checks and settings as before.
   - The new high (or low) is measured against the highest high (or lowest low) since that ranging or consolidation began.
   - The bounce must have failed on an earlier candle, after the last new high (or low) that way.
   - When the proof holds, the analyser moves straight to **trend**, a slow grind or strong push.
   - The trend's start, used for the 30-pip possible reversal and the MACD rule, is the lowest low (an up trend) or highest high (a down trend) since that ranging or consolidation began, at that candle's time.
   - `analyser/states.py` `_proof_from_base`.
2. **A 5-minute close beyond the hourly range counts as a break.**
   - While the hourly read says ranging, a 5-minute close at least `hourly_read.break_beyond_pips` (3) beyond the hourly range counts as a rally (above) or a sell-off (below). The range is kept as it was at the break.
   - Two closes in a row back inside that range cancel the break.
   - An hourly close beyond the range lets the real sell-off or rally take over. An hourly close without a break keeps the 5-minute break.
   - The break does not change the 5-minute state. It only lifts the stage 1 edge rule, the `HOURLY_READ` hourly-ranging block (a break up means the trend strategies buy only, down sell only) and the stage 2 hourly-ranging rule.
   - The hourly read itself, the hourly position and the dashboard stay as they are.
   - `analyser/hourly_read.py` `next_break`, `with_break`; `analyser/market_state.py`; `strategies/replay.py` `trend_hourly`; `strategies/common.py` (checks 4 and 7).
3. **No possible reversal from a strong push.** While the trend is a strong push, a rejection at a level does not turn it into a possible reversal. Once the type is back to slow grind, the rule applies as normal. The trend's start is unchanged.

**Filled in by me, for you to confirm:**
- **Where the proof is checked:** it is looked at first on each ranging or consolidation candle, before a level rejection or a breakout.
- **When the high/low count restarts:** a new ranging or consolidation begins on the candle it is decided on, including one that follows the other (ranging to consolidation starts again). The week's first candle begins the week's.
- **A close beyond the other side:** a 5-minute close at least 3 pips beyond the other side of the kept range turns the break the other way, as the hourly read itself does. It did not happen on any of the four test days.
- **When the break takes effect:** it is decided on each 5-minute close. The analyser uses it from that candle; the strategies use it at entry after that candle.

### Test results (all three switches on, edge 3)

- **New tests:**
  - `tests/technical/test_analyser_stage_1b.py`: 19 tests (the proof from consolidation and ranging, its start, the 5-minute break and its cancel, the trend group and stage 2 seeing the break, no possible reversal from a strong push). All pass.
  - `tests/functional/test_analyser_control_real_candles.py`: now 12 tests on the stored candles. All pass.
- **Full suite:** 2,435 passed.

**Trend days (the gate).** The trend group's trades (ideas allowed at entry that the hours and news rules let open), switches off vs on:

| Day | Off only | On only | Lost |
|---|---|---|---|
| Fri 6 Nov | breakout sell 17:50 (13355.2) | breakout sell 17:55 (13350.9) | none (the accepted change) |
| Tue 10 Nov | none | **slow grind sell 13:55 (13392.5)** | none |

- **The new 10 November trade:**
  - The 13:45 and 13:50 5-minute closes broke below the hourly range low (13420.2), so the slow grind sell is allowed at 13:55.
  - With the switches off, it waits for the 13:00 hourly candle's close at 14:00, and the first slow grind after that is at 14:30, which opens either way.
  - The trend proof also now fires at 13:10 straight from consolidation, instead of emerging at 12:55 then trend at 13:10.
- **6 November:**
  - The strong-push rule changes the afternoon's states: there is no possible reversal at 14:30 inside the 13:50 strong push.
  - The trend runs on as a slow grind from 14:35, with a possible reversal at 15:20 (at S3, after 57.6 pips).
  - No trend trade changes.

**17 November, the morning rally (02:10 to 05:45):**
- **03:30:** trend up (slow grind), by the trend proof from consolidation (consolidation since 00:45).
- **05:55:** possible reversal down, at the New York session high (a slow grind, so the rule applies).
- **06:00:** emerging down.
- **06:25:** ranging.
- **Morning box (07:00 to 13:00):** the proof never fires there.

**17 November, the afternoon rally (13:50 to 18:00):**
- **16:10:** trend up (slow grind), by the trend proof from consolidation.
- **16:25:** strong push.
- **16:45:** slow grind again.
- **The possible reversal now comes at 18:30** (after 49.1 pips, at the New York session high), not at 16:30. The 16:30 rejection came inside the strong push.
- **18:35:** emerging down.
- **Trend group:** first allowed in the afternoon at **16:45 (slow grind buy)**.

**Your expectations, and the bounces you asked about:**
- No emerging trend at 06:35, 08:55 or 14:45: **holds**.
- No consolidation breakout at 07:50 or 12:40: **holds**.
- One trade at 10:05: **holds**. The level reversal is refused: "same signal already traded by Bollinger bounce".
- **The 16:35 bounce sell does not open:** the analyser is in the strong push up, and a sell is against the trend.
- **The 17:45 bounce sell does not open:** the analyser is in a slow grind up, so again against the trend.
- **A bounce sell opens at 18:35,** after the possible reversal.

**17 November, full engine (paper trades; pips only so you can see how each ended, not a verdict):**

| Opened | Strategy | Direction | Entry | Pips (paper) | How it closed |
|---|---|---|---|---|---|
| 06:00 | level reversal | sell | 13198.8 | +3.2 | forced close: closed 15 minutes before big news |
| 10:05 | Bollinger bounce | sell | 13190.3 | +8.7 | stopped by IG: the stop at IG (trailed to 13181.6) |
| 16:20 | level reversal | buy | 13217.2 | -9.1 | forced close: 20:30 UK close |
| 16:45 | slow grind | buy | 13218.4 | -10.3 | forced close: 20:30 UK close |
| 17:15 | EMA pullback | buy | 13223.3 | -12.0 | stopped by IG: the stop at IG |
| 18:35 | Bollinger bounce | sell | 13219.7 | +8.6 | forced close: 20:30 UK close |

Orders the safety rules refused:

| Time | Strategy | Direction | Refused because |
|---|---|---|---|
| 06:15 | level reversal | sell | level reversal already has 1 trade(s) open (at most 1) |
| 10:05 | level reversal | sell | same signal already traded by Bollinger bounce |
| 17:10 | slow grind | buy | slow grind already has 1 trade(s) open (at most 1) |
| 18:00 | slow grind | buy | slow grind already has 1 trade(s) open (at most 1) |
| 18:20 | slow grind | buy | slow grind already has 1 trade(s) open (at most 1) |
| 18:40 | Bollinger bounce | sell | Bollinger bounce already has 1 sell trade(s) open (at most 1 each way) |
| 22:05 | session sweep | sell | outside the trading hours 06:00 to 20:30 UK |

State changes (the whole UK day):

| Time | New state | Hourly position | Why (the analyser's own words) |
|---|---|---|---|
| 00:05 | ranging (none) | middle | bands 10.3 pips wide (close together: 6 to 18) and flat (upper 0.2, lower 0.2 pips/candle), both bands reached, EMAs weaving, 100 EMA moved 0.4 pips |
| 00:45 | consolidation (none) | middle | bands 7.2 pips wide (narrow: <= 14, or narrowing for 6 candles: 3), middle band 0.0 pips/candle, no close outside the bands for 6 candles, average body 1.3 pips, green/re |
| 03:30 | trend (up, slow grind) | middle | the trend proof held in consolidation: a bounce failed under the 21 EMA and middle band, then a new high 13196.7 on the upper band 13196.1; EMAs 7/13/21 stacked up for 13 |
| 05:55 | possible reversal (down) | top edge | rejection at a level (new_york_session_high 13205.2, turning_high 13205.2) confirmed after a up move of 34.5 pips: closed 13200.2 below the reversal low 13200.9; trigger  |
| 06:00 | emerging trend (down) | middle | the reversal triggered: price went below 13198.8 (during this candle) |
| 06:25 | ranging (none) | middle | the emerging down trend turned into a range: bands 13.6 pips wide (close together: 6 to 18) and flat (upper 0.0, lower 0.1 pips/candle), both bands reached, EMAs weaving, |
| 06:40 | consolidation (none) | middle | bands 12.9 pips wide (narrow: <= 14, or narrowing for 6 candles: 0), middle band 0.0 pips/candle, no close outside the bands for 6 candles, average body 1.5 pips, green/r |
| 06:50 | ranging (none) | middle | bands 13.9 pips wide (close together: 6 to 18) and flat (upper -0.0, lower -0.0 pips/candle), both bands reached, EMAs weaving, 100 EMA moved 1.2 pips |
| 07:35 | consolidation (none) | middle | bands 9.6 pips wide (narrow: <= 14, or narrowing for 6 candles: 5), middle band -0.4 pips/candle, no close outside the bands for 6 candles, average body 2.6 pips, green/r |
| 08:35 | ranging (none) | middle | bands 14.6 pips wide (close together: 6 to 18) and flat (upper 0.1, lower -0.0 pips/candle), both bands reached, EMAs weaving, 100 EMA moved 0.0 pips |
| 09:50 | emerging trend (up) | top edge | broke out of the range: 2 closes above the band (last 13202.4, band 13200.6) |
| 10:00 | emerging trend (down) | middle | rejected at a level against the emerging up trend: closed 13190.5 below the reversal low 13195.2; trigger at below 13189.8 |
| 10:50 | ranging (none) | middle | the emerging down trend turned into a range: bands 17.9 pips wide (close together: 6 to 18) and flat (upper -0.0, lower -0.1 pips/candle), both bands reached, EMAs weavin |
| 11:35 | consolidation (none) | middle | bands 9.0 pips wide (narrow: <= 14, or narrowing for 6 candles: 6), middle band -0.4 pips/candle, no close outside the bands for 6 candles, average body 1.3 pips, green/r |
| 12:25 | ranging (none) | middle | bands 8.0 pips wide (close together: 6 to 18) and flat (upper 0.1, lower 0.0 pips/candle), both bands reached, EMAs weaving, 100 EMA moved 0.1 pips |
| 12:35 | consolidation (none) | middle | bands 6.9 pips wide (narrow: <= 14, or narrowing for 6 candles: 2), middle band 0.1 pips/candle, no close outside the bands for 6 candles, average body 2.4 pips, green/re |
| 13:35 | emerging trend (down) | middle | broke out of the consolidation: close 13173.3 below the lower band 13179.0 (at least 4.0 pips beyond it) |
| 13:50 | consolidation (none) | middle | the emerging down trend was cancelled: 2 closes in a row back inside the Bollinger bands after the breakout (last 13183.5) |
| 16:10 | trend (up, slow grind) | top edge | the trend proof held in consolidation: a bounce failed under the 21 EMA and middle band, then a new high 13212.0 on the upper band 13210.6; EMAs 7/13/21 stacked up for 10 |
| 16:25 | trend (up, strong push) | top edge | strong push: 83% of the body size green, bands 2.3x as wide as 12 candles ago, 7/21 EMAs 8.3 pips apart, 3 closes on the band |
| 16:45 | trend (up, slow grind) | top edge | slow grind: 51% of the body size green, bands 2.2x as wide as 12 candles ago, 7/21 EMAs 7.0 pips apart, 1 closes on the band |
| 18:30 | possible reversal (down) | middle | rejection at a level (new_york_session_high 13227.9) confirmed after a up move of 49.1 pips: closed 13219.5 below the reversal low 13221.1; trigger at below 13219.5 |
| 18:35 | emerging trend (down) | middle | the reversal triggered: price went below 13219.5 (during this candle) |
| 18:45 | emerging trend (up) | middle | rejected at a level against the emerging down trend: closed 13221.7 above the reversal high 13221; trigger at above 13221.7 |
| 19:00 | emerging trend (down) | middle | rejected at a level against the emerging up trend: closed 13216.7 below the reversal low 13218.2; trigger at below 13216.7 |
| 19:35 | emerging trend (up) | middle | rejected at a level against the emerging down trend: closed 13218.5 above the reversal high 13218.2; trigger at above 13219.6 |
| 19:50 | consolidation (none) | middle | the emerging up trend was cancelled: 2 closes in a row back below the turning_low 13217.4 it was rejected at (last 13215.6) |
| 19:55 | emerging trend (down) | middle | rejected at a level: closed 13213.9 below the reversal low 13215.6; trigger at below 13212.6 |
| 20:55 | consolidation (none) | middle | the emerging down trend settled into consolidation: bands 13.2 pips wide (narrow: <= 14, or narrowing for 6 candles: 1), middle band -0.4 pips/candle, no close outside th |
| 21:10 | emerging trend (up) | middle | rejected at a level: closed 13209.5 above the reversal high 13209.3; trigger at above 13211.1 |
| 21:25 | emerging trend (down) | middle | rejected at a level against the emerging up trend: closed 13206.6 below the reversal low 13208.2; trigger at below 13206.5 |
| 22:55 | consolidation (none) | middle | the emerging down trend settled into consolidation: bands 12.9 pips wide (narrow: <= 14, or narrowing for 6 candles: 7), middle band -0.3 pips/candle, no close outside th |
| 23:20 | emerging trend (up) | middle | rejected at a level: closed 13207.8 above the reversal high 13207.1; trigger at above 13208.1 |
| 23:30 | emerging trend (down) | middle | rejected at a level against the emerging up trend: closed 13206.1 below the reversal low 13206.5; trigger at below 13205.5 |
| 23:40 | ranging (none) | middle | the emerging down trend was cancelled: 2 closes in a row back above the turning_high 13204.4 it was rejected at (last 13204.8) |
| 23:50 | emerging trend (up) | middle | rejected at a level: closed 13207 above the reversal high 13206.5; trigger at above 13207.2 |

**13 November** (the range day, full engine): the states and trades are the same as before stage 1b. Neither the trend proof nor a 5-minute break fires.

| Opened | Strategy | Direction | Entry | Pips (paper) | How it closed |
|---|---|---|---|---|---|
| 08:20 | Asian range breakout | buy | 13241.8 | -12.0 | stopped by IG: the stop at IG |
| 08:40 | session sweep | sell | 13235.1 | +9.4 | stopped by IG: the stop at IG (trailed to 13225.7) |
| 11:00 | Bollinger bounce | buy | 13223.7 | +9.3 | stopped by IG: the stop at IG (trailed to 13234.5) |
| 15:05 | Bollinger bounce | sell | 13242.3 | +17.9 | stopped by IG: the stop at IG (trailed to 13224.4) |
| 15:10 | session sweep | sell | 13235.8 | +11.4 | stopped by IG: the stop at IG (trailed to 13224.4) |

Orders the safety rules refused:

| Time | Strategy | Direction | Refused because |
|---|---|---|---|
| 03:25 | range trade | buy | outside the trading hours 06:00 to 20:30 UK |
| 03:45 | range trade | buy | outside the trading hours 06:00 to 20:30 UK |
| 14:00 | session sweep | sell | once a day: a session sweep trade has already opened for Asian high 2026-11-13 |

State changes:

| Time | New state | Hourly position | Why (the analyser's own words) |
|---|---|---|---|
| 00:20 | consolidation (none) | middle | the emerging down trend settled into consolidation: bands 10.4 pips wide (narrow: <= 14, or narrowing for 6 candles: 2), middle band 0.1 pips/candle, no close outside the |
| 03:10 | ranging (none) | middle | bands 6.8 pips wide (close together: 6 to 18) and flat (upper -0.0, lower -0.1 pips/candle), both bands reached, EMAs weaving, 100 EMA moved 0.0 pips |
| 04:05 | consolidation (none) | middle | bands 4.8 pips wide (narrow: <= 14, or narrowing for 6 candles: 0), middle band -0.1 pips/candle, no close outside the bands for 6 candles, average body 0.6 pips, green/r |
| 05:50 | emerging trend (up) | middle | rejected at a level: closed 13226.7 above the reversal high 13226.3; trigger at above 13227.9 |
| 06:15 | consolidation (none) | middle | the emerging up trend settled into consolidation: bands 8.1 pips wide (narrow: <= 14, or narrowing for 6 candles: 1), middle band -0.1 pips/candle, no close outside the b |
| 06:55 | ranging (none) | middle | bands 9.9 pips wide (close together: 6 to 18) and flat (upper 0.1, lower -0.2 pips/candle), both bands reached, EMAs weaving, 100 EMA moved 1.0 pips |
| 07:05 | emerging trend (up) | top edge | broke out of the range: 2 closes above the band (last 13238.5, band 13236.5) |
| 07:15 | emerging trend (down) | middle | rejected at a level against the emerging up trend: closed 13232.3 below the reversal low 13234.4; trigger at below 13231.6 |
| 08:10 | consolidation (none) | middle | the emerging down trend settled into consolidation: bands 12.4 pips wide (narrow: <= 14, or narrowing for 6 candles: 6), middle band 0.4 pips/candle, no close outside the |
| 08:35 | emerging trend (down) | middle | rejected at a level: closed 13235.2 below the reversal low 13236.2; trigger at below 13235.2 |
| 09:25 | consolidation (none) | middle | the emerging down trend settled into consolidation: bands 12.9 pips wide (narrow: <= 14, or narrowing for 6 candles: 3), middle band 0.3 pips/candle, no close outside the |
| 09:45 | ranging (none) | middle | bands 13.2 pips wide (close together: 6 to 18) and flat (upper -0.0, lower 0.0 pips/candle), both bands reached, EMAs weaving, 100 EMA moved 0.5 pips |
| 09:55 | consolidation (none) | middle | bands 12.6 pips wide (narrow: <= 14, or narrowing for 6 candles: 1), middle band -0.2 pips/candle, no close outside the bands for 6 candles, average body 2.1 pips, green/ |
| 10:55 | emerging trend (up) | middle | rejected at a level: closed 13223.9 above the reversal high 13221.7; trigger at above 13225.3 |
| 11:40 | ranging (none) | middle | the emerging up trend turned into a range: bands 16.2 pips wide (close together: 6 to 18) and flat (upper -0.0, lower -0.0 pips/candle), both bands reached, EMAs weaving, |
| 12:35 | consolidation (none) | middle | bands 13.1 pips wide (narrow: <= 14, or narrowing for 6 candles: 3), middle band 0.2 pips/candle, no close outside the bands for 6 candles, average body 2.0 pips, green/r |
| 13:00 | emerging trend (up) | middle | rejected at a level: closed 13228.5 above the reversal high 13225.9; trigger at above 13228.8 |
| 13:45 | emerging trend (down) | middle | rejected at a level against the emerging up trend: closed 13237.2 below the reversal low 13238.8; trigger at below 13234.6 |
| 17:25 | trend (down, slow grind) | bottom edge | the rejection became a trend: a bounce failed under the 21 EMA and middle band, then a new low 13205.2 on the lower band 13204.6; EMAs 7/13/21 stacked down for 23 candles |
| 18:10 | possible reversal (up) | middle | rejection at a level (new_york_session_low 13204.3, S1 13206.0) confirmed after a down move of 32.9 pips: closed 13213.1 above the reversal high 13209.5; trigger at above |
| 18:20 | emerging trend (up) | middle | the reversal triggered: price went above 13214.9 (during this candle) |
| 18:30 | emerging trend (down) | middle | rejected at a level against the emerging up trend: closed 13210 below the reversal low 13212.8; trigger at below 13209.9 |
| 18:55 | ranging (none) | middle | the emerging down trend turned into a range: bands 12.4 pips wide (close together: 6 to 18) and flat (upper -0.1, lower 0.0 pips/candle), both bands reached, EMAs weaving |
| 19:10 | consolidation (none) | middle | bands 11.5 pips wide (narrow: <= 14, or narrowing for 6 candles: 19), middle band 0.0 pips/candle, no close outside the bands for 6 candles, average body 1.4 pips, green/ |
| 19:15 | emerging trend (up) | middle | rejected at a level: closed 13211.3 above the reversal high 13210.9; trigger at above 13211.8 |
| 19:25 | consolidation (none) | middle | the emerging up trend settled into consolidation: bands 9.3 pips wide (narrow: <= 14, or narrowing for 6 candles: 22), middle band 0.2 pips/candle, no close outside the b |
| 21:30 | emerging trend (down) | middle | rejected at a level: closed 13210.7 below the reversal low 13213; trigger at below 13210.7 |
| 21:50 | ranging (none) | middle | the emerging down trend turned into a range: bands 10.7 pips wide (close together: 6 to 18) and flat (upper 0.0, lower 0.0 pips/candle), both bands reached, EMAs weaving, |

### Questions
1. **10 November, 13:55 slow grind sell:** a new trade with the switches on (the same move, 35 minutes sooner). Your gate stops only on a lost trade, so I've kept it and recorded it in the test. Tell me if you want it treated differently.
2. **Filled in by me** (above): the proof checked first; the count restarting on each ranging or consolidation; a close beyond the other side turning the break; when the break takes effect. Confirm or change.
3. The edge distance (3 or 5 pips) is still yours to choose. These runs use 3. The 5-pip runs further down are from before stage 1b.

---

# The earlier report: stages 1 to 3 (before stage 1b)

## Summary

- **Built:** the three stages exactly as written, plus your answers of 18 November (listed below). Each stage has its own switch, a setting where you gave a number, and is documented in `docs/DESIGN.md` (new section 2.10; marked "(owner, 18 November 2026)") and `docs/SETTINGS.md`.
- **Trend days (6 and 10 November): the trend group takes the same trades with the switches on as off**, except the 6 November breakout sell moving from 17:50 to 17:55, which you accepted. 10 November is now identical, once the Asian range breakout is exempt from ranging, consolidation and the hourly-ranging rule (your answer 1).
- **17 November, all four of your test expectations hold at the 3-pip setting** (confirmed by the tests and by the full engine replay): no emerging trend at 06:35, 08:55 or 14:45; no consolidation breakout at 07:50 or 12:40; the 16:35 bounce sell does not open; the 10:05 bounce and level reversal give one trade.
- **Full test suite:** all tests pass: the pre-commit hook ran the whole suite on this commit and blocks it if anything fails (the run before the last fix: 2,412 passed, 1 failed, the .env.example check for the three new switches, since fixed).
- **Your choice to make:** the edge distance at 3 or 5 pips (13 and 17 November at both are below). I have not chosen. One fact for your decision: **at 5 pips, two of your 17 November test expectations no longer hold.** The 08:55 and 14:45 emerging-trend calls come back, because both rejections are within 5 pips of an edge. At 5 pips the 13:50 rejection at the previous day's low also counts, so the start of the afternoon rally is called "emerging up" (at 3 pips the analyser stays in consolidation from 13:50 to 17:00). The tests use the setting's value, 3.

## What was built

| Switch (`.env`, off if left out) | What it does while on | Where |
|---|---|---|
| `ANALYSER_USES_HOURLY` (stage 1) | While the hourly read says ranging, a level rejection starts or flips an emerging trend only at the edge of the hourly range. Ranging can end an emerging trend. A breakout from consolidation needs a close at least 4 pips beyond the band. Every state change records where price was in the hourly range (top edge, bottom edge, middle), also shown on the dashboard beside the market state. | `analyser/states.py`, `analyser/market_state.py`, `rejection/watch.py` (each setup's furthest point), `trading/engine.py` and `dashboard/static/index.html` (the position) |
| `ANALYSER_GOVERNS_ALL` (stage 2) | Every strategy asks the analyser by your table: trend group (slow grind, EMA pullback, breakout, Asian range breakout), reversal group (bounce, level reversal, session sweep, New York open reversal, range trade). While the hourly read says ranging, the trend group opens nothing and the reversal group only at the edges (sells top, buys bottom). The Asian range breakout is held to the trend's direction only. Every refusal is recorded with a reason starting `ANALYSER_GOVERNS_ALL:`. The dashboard's "strategies allowed" list follows the table. | `strategies/common.py` (check 7), `strategies/replay.py` (the MACD rule), each reversal strategy (its rejection candle and furthest point) |
| `ONE_SIGNAL_ONE_TRADE` (stage 3) | Two or more strategies the same way from the same rejection candle give one trade, the first to trigger; the others are refused with "same signal already traded by <strategy>". The session sweep and New York open reversal come under one view at a time. | `safety/rules.py` (rules 9 and 11), `orders/sender.py` (the signal kept in the order record, so a restart remembers it) |

Settings (`config/settings.toml`, `[analyser_control]`): `edge_within_pips = 3` and `consolidation_breakout_beyond_pips = 4`.

HOURLY_READ keeps its present job for the trend strategies. Stages 1 and 2 use the hourly read whatever HOURLY_READ is set to.

## Your answers, as built

1. **Edge price:** the setup's furthest point, measured as the level reversal's allowance: pierce (or rejection) candle to confirmation candle. The range trade runs from pierce to rejection candle (it has no confirmation). The New York open reversal uses its rejection candle's extreme, since no later candle can pass it without cancelling.
2. **Edges are paired** in stage 1 as in stage 2: a sell rejection at the top edge, a buy at the bottom.
3. **And the rejection candle must close back inside the hourly range** (low to high, both included), in stages 1 and 2. A rejection candle closing outside never counts. This is what stops the 16:35 bounce sell (the 16:25 rejection candle closed at 13216.7, above the hourly high 13210.4).
4. **MACD in a possible reversal:** the 5-minute histogram, against every bar since the old trend started (its emerging-trend start). Allowed at its biggest bar in the old direction, when smaller than both the biggest and the bar before, or once it has crossed zero.
5. **Stage 2's hourly rule applies whatever HOURLY_READ is.**
6. **One view at a time:** the session sweep and New York open reversal count as reversal trades against the analyser's trend direction; the Asian range breakout never does.
7. **Same signal:** each strategy's own rejection or reversal candle, the same start time, the same direction.
8. **Position** uses the last finished 5-minute close. When the close is near both edges of a very narrow range, it takes the nearer one (top on a tie).
9. **Asian range breakout:** trend group for direction, not blocked by ranging, consolidation or the hourly-ranging rule. **One point I took literally:** you named only those three, so in a **possible reversal** the table's "nothing new" still applies to it. Tell me if you want that changed.
10. **4-pip consolidation breakout** accepted, including the 6 November breakout moving to 17:55.
11. Accepted gap fills: an unknown hourly range keeps the old behaviour; a refused first trade uses up nothing (the next strategy on the same signal may still open).

## Test results

**New tests:**

- `tests/functional/test_analyser_control_real_candles.py`: 9 tests on the stored candles, all three switches on. They replay each week through the analyser and the strategies as the live service runs them, with every entry checked. All pass.
- `tests/technical/test_analyser_control.py`: 68 tests (the edge, the position, the table, the MACD rule, stage 1 in the state machine, one signal, one view). All pass.
- Two order-sender tests in `tests/technical/test_orders.py` (the signal kept after a restart; off allows both). Both pass.
- Settings tests for the three switches and the two settings. All pass.

**a. Trend days (the gate).** The trend group's trades (ideas allowed at entry that the hours and news rules let open), switches off vs on:

| Day | Off only | On only | Verdict |
|---|---|---|---|
| Fri 6 Nov | breakout sell 17:50 at 13355.2 | breakout sell 17:55 at 13350.9 | The change you accepted (the 4-pip consolidation breakout moves the breakout candle from 17:45 to 17:50) |
| Tue 10 Nov | none | none | Identical |

Every EMA pullback and slow grind is unchanged on both days. The Asian range breakout's first trade each way is unchanged (6 Nov 07:05 sell; 10 Nov 07:25 buy and 09:40 sell). On 6 November, its repeated sell ideas from 07:25 to 08:20 are blocked with the switches on because the analyser had turned to "emerging trend up" at 07:20 (`ANALYSER_GOVERNS_ALL: the emerging trend is up: Asian range breakout only in the trend's direction`). These are repeats after the 07:05 sell, which opens either way, and the once-a-day rule would refuse them anyway.

The gate was checked with the strategy replay (entries checked at entry), not the full engine. A full-engine replay of one week takes 30 minutes or more on this server, and I kept those runs for 13 and 17 November below.

**b. 13 November** (states and trades below). The test checks that every idea allowed while the hourly read was ranging follows the edge rule.

**c. 17 November**: all four expectations hold (details below).

**Full suite:** all tests pass: the pre-commit hook ran the whole suite on this commit and blocks it if anything fails (the run before the last fix: 2,412 passed, 1 failed, the .env.example check for the three new switches, since fixed).

## Tuesday 17 November: switches off vs on

Full wired path (the engine in paper mode, a pretend IG, the stored candles; `research/analyser_control_days.py`). Baseline switches are as on the live `.env` today, including HOURLY_READ on. That's why, with the switches off, the slow grind buy comes at 17:10 rather than 16:45 as it did live (HOURLY_READ was off then). Paper trades have no IG refusals, so the 10:05 bounce's trail works here (+8.7) where live it was refused (−3.3).

**In short:** with the switches off, the replay opens the same 11 trades as yesterday's live day (apart from the slow grind and bounce-trail differences explained above). With all three switches on:

- **Edge 3 pips: 3 trades.** The 06:15 level reversal sell, the 10:05 bounce sell (the 10:05 level reversal refused: "same signal already traded by Bollinger bounce") and the 17:15 EMA pullback buy. The 07:35 level reversal, 08:55 range trade, 14:00 session sweep, 16:20 level reversal buy, 16:35 and 17:45 bounce sells and the slow grind buy do not open.
- **Edge 5 pips: 7 trades.** The same three, plus the 07:35 level reversal sell, the 08:55 range trade sell, the 14:00 session sweep buy and a 14:55 level reversal sell (new). Those setups' furthest points were within 5 pips of an hourly edge, but not within 3.

**All trades side by side** (pips of each paper trade, for reference only):

| Opened | Strategy | Direction | switches off | on, edge 3 | on, edge 5 |
|---|---|---|---|---|---|
| 06:00 | level reversal | sell | +3.2 | not opened | not opened |
| 06:15 | level reversal | sell | not opened | -2.2 | -2.2 |
| 07:35 | level reversal | sell | -12.9 | not opened | -12.9 |
| 08:55 | range trade | sell | -12.0 | not opened | -12.0 |
| 10:05 | Bollinger bounce | sell | +8.7 | +8.7 | +8.7 |
| 10:05 | level reversal | sell | -20.6 | not opened | not opened |
| 14:00 | session sweep | buy | +5.4 | not opened | +5.4 |
| 14:55 | level reversal | sell | not opened | not opened | -15.7 |
| 16:20 | level reversal | buy | -9.1 | not opened | not opened |
| 16:35 | Bollinger bounce | sell | -12.0 | not opened | not opened |
| 17:10 | slow grind | buy | -10.4 | not opened | not opened |
| 17:15 | EMA pullback | buy | -12.0 | -12.0 | -12.0 |
| 17:45 | Bollinger bounce | sell | +10.1 | not opened | not opened |

#### Switches off

**Trades that open**

| Opened | Strategy | Direction | Entry | Pips (paper) | How it closed |
|---|---|---|---|---|---|
| 06:00 | level reversal | sell | 13198.8 | +3.2 | forced close: closed 15 minutes before big news |
| 07:35 | level reversal | sell | 13192 | -12.9 | stopped by IG: the stop at IG |
| 08:55 | range trade | sell | 13190.8 | -12.0 | stopped by IG: the stop at IG |
| 10:05 | Bollinger bounce | sell | 13190.3 | +8.7 | stopped by IG: the stop at IG (trailed to 13181.6) |
| 10:05 | level reversal | sell | 13189.8 | -20.6 | stopped by IG: the stop at IG |
| 14:00 | session sweep | buy | 13187 | +5.4 | stopped by IG: the stop at IG (trailed to 13193.9) |
| 16:20 | level reversal | buy | 13217.2 | -9.1 | forced close: 20:30 UK close |
| 16:35 | Bollinger bounce | sell | 13215 | -12.0 | stopped by IG: the stop at IG |
| 17:10 | slow grind | buy | 13218.5 | -10.4 | forced close: 20:30 UK close |
| 17:15 | EMA pullback | buy | 13223.3 | -12.0 | stopped by IG: the stop at IG |
| 17:45 | Bollinger bounce | sell | 13221.2 | +10.1 | forced close: 20:30 UK close |

**Orders the safety rules refused**

| Time | Strategy | Direction | Refused because |
|---|---|---|---|
| 00:15 | range trade | sell | outside the trading hours 06:00 to 20:30 UK |
| 06:15 | level reversal | sell | level reversal already has 1 trade(s) open (at most 1) |
| 06:20 | level reversal | sell | level reversal already has 1 trade(s) open (at most 1) |
| 09:00 | level reversal | sell | level reversal already has 1 trade(s) open (at most 1) |
| 13:15 | level reversal | sell | level reversal already has 1 trade(s) open (at most 1) |
| 14:55 | level reversal | sell | level reversal already has 1 trade(s) open (at most 1) |
| 15:00 | level reversal | sell | level reversal already has 1 trade(s) open (at most 1) |
| 18:00 | slow grind | buy | slow grind already has 1 trade(s) open (at most 1) |
| 18:20 | slow grind | buy | slow grind already has 1 trade(s) open (at most 1) |
| 18:30 | Bollinger bounce | sell | Bollinger bounce already has 1 sell trade(s) open (at most 1 each way) |
| 18:35 | Bollinger bounce | sell | Bollinger bounce already has 1 sell trade(s) open (at most 1 each way) |
| 18:40 | Bollinger bounce | sell | Bollinger bounce already has 1 sell trade(s) open (at most 1 each way) |
| 22:05 | session sweep | sell | outside the trading hours 06:00 to 20:30 UK |

**State changes** (the whole UK day)

| Time | New state | Hourly position | Why (the analyser's own words) |
|---|---|---|---|
| 00:05 | ranging (none) | - | bands 10.3 pips wide (close together: 6 to 18) and flat (upper 0.2, lower 0.2 pips/candle), both bands reached, EMAs weaving, 100 EMA moved 0.4 pips |
| 00:45 | consolidation (none) | - | bands 7.2 pips wide (narrow: <= 14, or narrowing for 6 candles: 3), middle band 0.0 pips/candle, no close outside the bands for 6 candles, average body 1.3 pips, green/re |
| 01:05 | emerging trend (down) | - | broke out of the consolidation: close 13178.3 below the lower band 13178.4 |
| 01:35 | consolidation (none) | - | the emerging down trend was cancelled: 2 closes in a row back inside the Bollinger bands after the breakout (last 13172.4) |
| 02:10 | emerging trend (up) | - | rejected at a level: closed 13180.8 above the reversal high 13177.5; trigger at above 13181 |
| 03:30 | trend (up, slow grind) | - | the rejection became a trend: a bounce failed under the 21 EMA and middle band, then a new high 13196.7 on the upper band 13196.1; EMAs 7/13/21 stacked up for 13 candles, |
| 06:25 | ranging (none) | - | the up trend turned into a range: bands 13.6 pips wide (close together: 6 to 18) and flat (upper 0.0, lower 0.1 pips/candle), both bands reached, EMAs weaving, 100 EMA mo |
| 06:35 | emerging trend (up) | - | rejected at a level: closed 13193.5 above the reversal high 13193.1; trigger at above 13195.3 |
| 06:45 | ranging (none) | - | the emerging up trend was cancelled: 2 closes in a row back below the pivot 13194.4 it was rejected at (last 13190.7) |
| 06:55 | emerging trend (down) | - | rejected at a level: closed 13187.5 below the reversal low 13189.7; trigger at below 13187.5 |
| 07:35 | consolidation (none) | - | the emerging down trend settled into consolidation: bands 9.6 pips wide (narrow: <= 14, or narrowing for 6 candles: 5), middle band -0.4 pips/candle, no close outside the |
| 07:50 | emerging trend (down) | - | broke out of the consolidation: close 13184.9 below the lower band 13186.4 |
| 08:10 | consolidation (none) | - | the emerging down trend was cancelled: 2 closes in a row back inside the Bollinger bands after the breakout (last 13188.4) |
| 08:35 | ranging (none) | - | bands 14.6 pips wide (close together: 6 to 18) and flat (upper 0.1, lower -0.0 pips/candle), both bands reached, EMAs weaving, 100 EMA moved 0.0 pips |
| 08:55 | emerging trend (down) | - | rejected at a level: closed 13190.8 below the reversal low 13193.6; trigger at below 13189.5 |
| 09:30 | emerging trend (up) | - | rejected at a level against the emerging down trend: closed 13194.9 above the reversal high 13194.7; trigger at above 13195.8 |
| 10:00 | emerging trend (down) | - | rejected at a level against the emerging up trend: closed 13190.5 below the reversal low 13195.2; trigger at below 13189.8 |
| 11:35 | consolidation (none) | - | the emerging down trend settled into consolidation: bands 9.0 pips wide (narrow: <= 14, or narrowing for 6 candles: 6), middle band -0.4 pips/candle, no close outside the |
| 12:25 | ranging (none) | - | bands 8.0 pips wide (close together: 6 to 18) and flat (upper 0.1, lower 0.0 pips/candle), both bands reached, EMAs weaving, 100 EMA moved 0.1 pips |
| 12:35 | consolidation (none) | - | bands 6.9 pips wide (narrow: <= 14, or narrowing for 6 candles: 2), middle band 0.1 pips/candle, no close outside the bands for 6 candles, average body 2.4 pips, green/re |
| 12:40 | emerging trend (up) | - | broke out of the consolidation: close 13196.1 above the upper band 13194.9 |
| 12:55 | consolidation (none) | - | the emerging up trend was cancelled: 2 closes in a row back inside the Bollinger bands after the breakout (last 13195.1) |
| 13:10 | emerging trend (down) | - | rejected at a level: closed 13189.9 below the reversal low 13190.6; trigger at below 13188.9 |
| 13:50 | emerging trend (up) | - | rejected at a level against the emerging down trend: closed 13183.5 above the reversal high 13180.3; trigger at above 13183.5 |
| 14:45 | emerging trend (down) | - | rejected at a level against the emerging up trend: closed 13192.5 below the reversal low 13194; trigger at below 13191.3 |
| 15:40 | emerging trend (up) | - | rejected at a level against the emerging down trend: closed 13204.4 above the reversal high 13203.2; trigger at above 13207.9 |
| 16:10 | trend (up, slow grind) | - | the rejection became a trend: a bounce failed under the 21 EMA and middle band, then a new high 13212.0 on the upper band 13210.6; EMAs 7/13/21 stacked up for 10 candles, |
| 16:25 | trend (up, strong push) | - | strong push: 83% of the body size green, bands 2.3x as wide as 12 candles ago, 7/21 EMAs 8.3 pips apart, 3 closes on the band |
| 16:45 | trend (up, slow grind) | - | slow grind: 51% of the body size green, bands 2.2x as wide as 12 candles ago, 7/21 EMAs 7.0 pips apart, 1 closes on the band |
| 19:35 | consolidation (none) | - | the up trend ran out of steam: bands 11.4 pips wide (narrow: <= 14, or narrowing for 6 candles: 2), middle band -0.2 pips/candle, no close outside the bands for 6 candles |
| 19:55 | emerging trend (down) | - | rejected at a level: closed 13213.9 below the reversal low 13215.6; trigger at below 13212.6 |
| 20:55 | consolidation (none) | - | the emerging down trend settled into consolidation: bands 13.2 pips wide (narrow: <= 14, or narrowing for 6 candles: 1), middle band -0.4 pips/candle, no close outside th |
| 21:10 | emerging trend (up) | - | rejected at a level: closed 13209.5 above the reversal high 13209.3; trigger at above 13211.1 |
| 21:25 | emerging trend (down) | - | rejected at a level against the emerging up trend: closed 13206.6 below the reversal low 13208.2; trigger at below 13206.5 |
| 22:55 | consolidation (none) | - | the emerging down trend settled into consolidation: bands 12.9 pips wide (narrow: <= 14, or narrowing for 6 candles: 7), middle band -0.3 pips/candle, no close outside th |
| 23:20 | emerging trend (up) | - | rejected at a level: closed 13207.8 above the reversal high 13207.1; trigger at above 13208.1 |
| 23:30 | emerging trend (down) | - | rejected at a level against the emerging up trend: closed 13206.1 below the reversal low 13206.5; trigger at below 13205.5 |
| 23:40 | ranging (none) | - | the emerging down trend was cancelled: 2 closes in a row back above the turning_high 13204.4 it was rejected at (last 13204.8) |
| 23:50 | emerging trend (up) | - | rejected at a level: closed 13207 above the reversal high 13206.5; trigger at above 13207.2 |

#### All three switches on, edge 3 pips

**Trades that open**

| Opened | Strategy | Direction | Entry | Pips (paper) | How it closed |
|---|---|---|---|---|---|
| 06:15 | level reversal | sell | 13193.4 | -2.2 | forced close: closed 15 minutes before big news |
| 10:05 | Bollinger bounce | sell | 13190.3 | +8.7 | stopped by IG: the stop at IG (trailed to 13181.6) |
| 17:15 | EMA pullback | buy | 13223.3 | -12.0 | stopped by IG: the stop at IG |

**Orders the safety rules refused**

| Time | Strategy | Direction | Refused because |
|---|---|---|---|
| 10:05 | level reversal | sell | same signal already traded by Bollinger bounce |
| 22:05 | session sweep | sell | outside the trading hours 06:00 to 20:30 UK |

**State changes** (the whole UK day)

| Time | New state | Hourly position | Why (the analyser's own words) |
|---|---|---|---|
| 00:05 | ranging (none) | middle | bands 10.3 pips wide (close together: 6 to 18) and flat (upper 0.2, lower 0.2 pips/candle), both bands reached, EMAs weaving, 100 EMA moved 0.4 pips |
| 00:45 | consolidation (none) | middle | bands 7.2 pips wide (narrow: <= 14, or narrowing for 6 candles: 3), middle band 0.0 pips/candle, no close outside the bands for 6 candles, average body 1.3 pips, green/re |
| 06:10 | emerging trend (down) | middle | rejected at a level: closed 13195.5 below the reversal low 13195.6; trigger at below 13193.4 |
| 06:25 | ranging (none) | middle | the emerging down trend turned into a range: bands 13.6 pips wide (close together: 6 to 18) and flat (upper 0.0, lower 0.1 pips/candle), both bands reached, EMAs weaving, |
| 06:40 | consolidation (none) | middle | bands 12.9 pips wide (narrow: <= 14, or narrowing for 6 candles: 0), middle band 0.0 pips/candle, no close outside the bands for 6 candles, average body 1.5 pips, green/r |
| 06:50 | ranging (none) | middle | bands 13.9 pips wide (close together: 6 to 18) and flat (upper -0.0, lower -0.0 pips/candle), both bands reached, EMAs weaving, 100 EMA moved 1.2 pips |
| 07:35 | consolidation (none) | middle | bands 9.6 pips wide (narrow: <= 14, or narrowing for 6 candles: 5), middle band -0.4 pips/candle, no close outside the bands for 6 candles, average body 2.6 pips, green/r |
| 08:35 | ranging (none) | middle | bands 14.6 pips wide (close together: 6 to 18) and flat (upper 0.1, lower -0.0 pips/candle), both bands reached, EMAs weaving, 100 EMA moved 0.0 pips |
| 09:50 | emerging trend (up) | top edge | broke out of the range: 2 closes above the band (last 13202.4, band 13200.6) |
| 10:00 | emerging trend (down) | middle | rejected at a level against the emerging up trend: closed 13190.5 below the reversal low 13195.2; trigger at below 13189.8 |
| 10:50 | ranging (none) | middle | the emerging down trend turned into a range: bands 17.9 pips wide (close together: 6 to 18) and flat (upper -0.0, lower -0.1 pips/candle), both bands reached, EMAs weavin |
| 11:35 | consolidation (none) | middle | bands 9.0 pips wide (narrow: <= 14, or narrowing for 6 candles: 6), middle band -0.4 pips/candle, no close outside the bands for 6 candles, average body 1.3 pips, green/r |
| 12:25 | ranging (none) | middle | bands 8.0 pips wide (close together: 6 to 18) and flat (upper 0.1, lower 0.0 pips/candle), both bands reached, EMAs weaving, 100 EMA moved 0.1 pips |
| 12:35 | consolidation (none) | middle | bands 6.9 pips wide (narrow: <= 14, or narrowing for 6 candles: 2), middle band 0.1 pips/candle, no close outside the bands for 6 candles, average body 2.4 pips, green/re |
| 13:35 | emerging trend (down) | middle | broke out of the consolidation: close 13173.3 below the lower band 13179.0 (at least 4.0 pips beyond it) |
| 13:50 | consolidation (none) | middle | the emerging down trend was cancelled: 2 closes in a row back inside the Bollinger bands after the breakout (last 13183.5) |
| 17:00 | emerging trend (up) | middle | rejected at a level: closed 13217.5 above the reversal high 13216.5; trigger at above 13218 |
| 19:00 | emerging trend (down) | middle | rejected at a level against the emerging up trend: closed 13216.7 below the reversal low 13218.2; trigger at below 13216.7 |
| 19:35 | emerging trend (up) | middle | rejected at a level against the emerging down trend: closed 13218.5 above the reversal high 13218.2; trigger at above 13219.6 |
| 19:50 | consolidation (none) | middle | the emerging up trend was cancelled: 2 closes in a row back below the turning_low 13217.4 it was rejected at (last 13215.6) |
| 19:55 | emerging trend (down) | middle | rejected at a level: closed 13213.9 below the reversal low 13215.6; trigger at below 13212.6 |
| 20:55 | consolidation (none) | middle | the emerging down trend settled into consolidation: bands 13.2 pips wide (narrow: <= 14, or narrowing for 6 candles: 1), middle band -0.4 pips/candle, no close outside th |
| 21:10 | emerging trend (up) | middle | rejected at a level: closed 13209.5 above the reversal high 13209.3; trigger at above 13211.1 |
| 21:25 | emerging trend (down) | middle | rejected at a level against the emerging up trend: closed 13206.6 below the reversal low 13208.2; trigger at below 13206.5 |
| 22:55 | consolidation (none) | middle | the emerging down trend settled into consolidation: bands 12.9 pips wide (narrow: <= 14, or narrowing for 6 candles: 7), middle band -0.3 pips/candle, no close outside th |
| 23:20 | emerging trend (up) | middle | rejected at a level: closed 13207.8 above the reversal high 13207.1; trigger at above 13208.1 |
| 23:30 | emerging trend (down) | middle | rejected at a level against the emerging up trend: closed 13206.1 below the reversal low 13206.5; trigger at below 13205.5 |
| 23:40 | ranging (none) | middle | the emerging down trend was cancelled: 2 closes in a row back above the turning_high 13204.4 it was rejected at (last 13204.8) |
| 23:50 | emerging trend (up) | middle | rejected at a level: closed 13207 above the reversal high 13206.5; trigger at above 13207.2 |

#### All three switches on, edge 5 pips

**Trades that open**

| Opened | Strategy | Direction | Entry | Pips (paper) | How it closed |
|---|---|---|---|---|---|
| 06:15 | level reversal | sell | 13193.4 | -2.2 | forced close: closed 15 minutes before big news |
| 07:35 | level reversal | sell | 13192 | -12.9 | stopped by IG: the stop at IG |
| 08:55 | range trade | sell | 13190.8 | -12.0 | stopped by IG: the stop at IG |
| 10:05 | Bollinger bounce | sell | 13190.3 | +8.7 | stopped by IG: the stop at IG (trailed to 13181.6) |
| 14:00 | session sweep | buy | 13187 | +5.4 | stopped by IG: the stop at IG (trailed to 13193.9) |
| 14:55 | level reversal | sell | 13191.3 | -15.7 | stopped by IG: the stop at IG |
| 17:15 | EMA pullback | buy | 13223.3 | -12.0 | stopped by IG: the stop at IG |

**Orders the safety rules refused**

| Time | Strategy | Direction | Refused because |
|---|---|---|---|
| 06:20 | level reversal | sell | level reversal already has 1 trade(s) open (at most 1) |
| 09:00 | level reversal | sell | level reversal already has 1 trade(s) open (at most 1) |
| 10:05 | level reversal | sell | same signal already traded by Bollinger bounce |
| 22:05 | session sweep | sell | outside the trading hours 06:00 to 20:30 UK |

**State changes** (the whole UK day)

| Time | New state | Hourly position | Why (the analyser's own words) |
|---|---|---|---|
| 00:05 | ranging (none) | middle | bands 10.3 pips wide (close together: 6 to 18) and flat (upper 0.2, lower 0.2 pips/candle), both bands reached, EMAs weaving, 100 EMA moved 0.4 pips |
| 00:45 | consolidation (none) | middle | bands 7.2 pips wide (narrow: <= 14, or narrowing for 6 candles: 3), middle band 0.0 pips/candle, no close outside the bands for 6 candles, average body 1.3 pips, green/re |
| 03:40 | emerging trend (down) | middle | rejected at a level: closed 13191.8 below the reversal low 13191.9; trigger at below 13190.7 |
| 05:35 | consolidation (none) | top edge | the emerging down trend was cancelled: 2 closes in a row back above the pivot 13194.4 it was rejected at (last 13198.6) |
| 06:10 | emerging trend (down) | middle | rejected at a level: closed 13195.5 below the reversal low 13195.6; trigger at below 13193.4 |
| 06:25 | ranging (none) | middle | the emerging down trend turned into a range: bands 13.6 pips wide (close together: 6 to 18) and flat (upper 0.0, lower 0.1 pips/candle), both bands reached, EMAs weaving, |
| 06:40 | consolidation (none) | middle | bands 12.9 pips wide (narrow: <= 14, or narrowing for 6 candles: 0), middle band 0.0 pips/candle, no close outside the bands for 6 candles, average body 1.5 pips, green/r |
| 06:50 | ranging (none) | middle | bands 13.9 pips wide (close together: 6 to 18) and flat (upper -0.0, lower -0.0 pips/candle), both bands reached, EMAs weaving, 100 EMA moved 1.2 pips |
| 07:15 | emerging trend (down) | middle | rejected at a level: closed 13190.9 below the reversal low 13191.3; trigger at below 13189.8 |
| 07:35 | consolidation (none) | middle | the emerging down trend settled into consolidation: bands 9.6 pips wide (narrow: <= 14, or narrowing for 6 candles: 5), middle band -0.4 pips/candle, no close outside the |
| 08:35 | ranging (none) | middle | bands 14.6 pips wide (close together: 6 to 18) and flat (upper 0.1, lower -0.0 pips/candle), both bands reached, EMAs weaving, 100 EMA moved 0.0 pips |
| 08:55 | emerging trend (down) | middle | rejected at a level: closed 13190.8 below the reversal low 13193.6; trigger at below 13189.5 |
| 09:15 | ranging (none) | middle | the emerging down trend turned into a range: bands 14.8 pips wide (close together: 6 to 18) and flat (upper 0.0, lower -0.0 pips/candle), both bands reached, EMAs weaving |
| 09:50 | emerging trend (up) | top edge | broke out of the range: 2 closes above the band (last 13202.4, band 13200.6) |
| 10:00 | emerging trend (down) | middle | rejected at a level against the emerging up trend: closed 13190.5 below the reversal low 13195.2; trigger at below 13189.8 |
| 10:50 | ranging (none) | middle | the emerging down trend turned into a range: bands 17.9 pips wide (close together: 6 to 18) and flat (upper -0.0, lower -0.1 pips/candle), both bands reached, EMAs weavin |
| 11:35 | consolidation (none) | middle | bands 9.0 pips wide (narrow: <= 14, or narrowing for 6 candles: 6), middle band -0.4 pips/candle, no close outside the bands for 6 candles, average body 1.3 pips, green/r |
| 12:25 | ranging (none) | middle | bands 8.0 pips wide (close together: 6 to 18) and flat (upper 0.1, lower 0.0 pips/candle), both bands reached, EMAs weaving, 100 EMA moved 0.1 pips |
| 12:35 | consolidation (none) | middle | bands 6.9 pips wide (narrow: <= 14, or narrowing for 6 candles: 2), middle band 0.1 pips/candle, no close outside the bands for 6 candles, average body 2.4 pips, green/re |
| 13:35 | emerging trend (down) | middle | broke out of the consolidation: close 13173.3 below the lower band 13179.0 (at least 4.0 pips beyond it) |
| 13:50 | emerging trend (up) | middle | rejected at a level against the emerging down trend: closed 13183.5 above the reversal high 13180.3; trigger at above 13183.5 |
| 14:45 | emerging trend (down) | middle | rejected at a level against the emerging up trend: closed 13192.5 below the reversal low 13194; trigger at below 13191.3 |
| 15:45 | consolidation (none) | top edge | the emerging down trend was cancelled: 2 closes in a row back above the round_number 13200.0 it was rejected at (last 13202.8) |
| 17:00 | emerging trend (up) | top edge | rejected at a level: closed 13217.5 above the reversal high 13216.5; trigger at above 13218 |
| 19:00 | emerging trend (down) | middle | rejected at a level against the emerging up trend: closed 13216.7 below the reversal low 13218.2; trigger at below 13216.7 |
| 19:35 | emerging trend (up) | middle | rejected at a level against the emerging down trend: closed 13218.5 above the reversal high 13218.2; trigger at above 13219.6 |
| 19:50 | consolidation (none) | middle | the emerging up trend was cancelled: 2 closes in a row back below the turning_low 13217.4 it was rejected at (last 13215.6) |
| 19:55 | emerging trend (down) | middle | rejected at a level: closed 13213.9 below the reversal low 13215.6; trigger at below 13212.6 |
| 20:55 | consolidation (none) | middle | the emerging down trend settled into consolidation: bands 13.2 pips wide (narrow: <= 14, or narrowing for 6 candles: 1), middle band -0.4 pips/candle, no close outside th |
| 21:10 | emerging trend (up) | middle | rejected at a level: closed 13209.5 above the reversal high 13209.3; trigger at above 13211.1 |
| 21:25 | emerging trend (down) | middle | rejected at a level against the emerging up trend: closed 13206.6 below the reversal low 13208.2; trigger at below 13206.5 |
| 22:55 | consolidation (none) | middle | the emerging down trend settled into consolidation: bands 12.9 pips wide (narrow: <= 14, or narrowing for 6 candles: 7), middle band -0.3 pips/candle, no close outside th |
| 23:20 | emerging trend (up) | middle | rejected at a level: closed 13207.8 above the reversal high 13207.1; trigger at above 13208.1 |
| 23:30 | emerging trend (down) | middle | rejected at a level against the emerging up trend: closed 13206.1 below the reversal low 13206.5; trigger at below 13205.5 |
| 23:40 | ranging (none) | middle | the emerging down trend was cancelled: 2 closes in a row back above the turning_high 13204.4 it was rejected at (last 13204.8) |
| 23:50 | emerging trend (up) | middle | rejected at a level: closed 13207 above the reversal high 13206.5; trigger at above 13207.2 |


## Friday 13 November (the textbook range, 08:40 to 13:00 UK), switches on

**In short:** the same five trades at 3 and at 5 pips. The state changes differ only at 12:30: at 5 pips a short "emerging trend up" from 12:30 to 12:40. In the textbook range (08:40 to 13:00 UK) the analyser was in emerging trend down 08:35–09:25 (a rejection that confirmed at 08:35), then consolidation and ranging, then emerging up from 10:55 to 11:40 and ranging again until 12:35. The trades in that window are the 08:40 session sweep sell and the 11:00 bounce buy, both reversal-group trades at the edges. At 15:05 and 15:10 the bounce sell and the session sweep sell both open: their rejection candles differ (14:50 for the bounce, 15:00 for the sweep), so by your rule they are different signals. The 14:00 sweep sell was refused by the existing once-a-day rule.

**Trades side by side** (pips for reference only):

| Opened | Strategy | Direction | on, edge 3 | on, edge 5 |
|---|---|---|---|---|
| 08:20 | Asian range breakout | buy | -12.0 | -12.0 |
| 08:40 | session sweep | sell | +9.4 | +9.4 |
| 11:00 | Bollinger bounce | buy | +9.3 | +9.3 |
| 15:05 | Bollinger bounce | sell | +17.9 | +17.9 |
| 15:10 | session sweep | sell | +11.4 | +11.4 |

#### All three switches on, edge 3 pips

**Trades that open**

| Opened | Strategy | Direction | Entry | Pips (paper) | How it closed |
|---|---|---|---|---|---|
| 08:20 | Asian range breakout | buy | 13241.8 | -12.0 | stopped by IG: the stop at IG |
| 08:40 | session sweep | sell | 13235.1 | +9.4 | stopped by IG: the stop at IG (trailed to 13225.7) |
| 11:00 | Bollinger bounce | buy | 13223.7 | +9.3 | stopped by IG: the stop at IG (trailed to 13234.5) |
| 15:05 | Bollinger bounce | sell | 13242.3 | +17.9 | stopped by IG: the stop at IG (trailed to 13224.4) |
| 15:10 | session sweep | sell | 13235.8 | +11.4 | stopped by IG: the stop at IG (trailed to 13224.4) |

**Orders the safety rules refused**

| Time | Strategy | Direction | Refused because |
|---|---|---|---|
| 03:25 | range trade | buy | outside the trading hours 06:00 to 20:30 UK |
| 03:45 | range trade | buy | outside the trading hours 06:00 to 20:30 UK |
| 14:00 | session sweep | sell | once a day: a session sweep trade has already opened for Asian high 2026-11-13 |

**State changes** (the whole UK day)

| Time | New state | Hourly position | Why (the analyser's own words) |
|---|---|---|---|
| 00:20 | consolidation (none) | middle | the emerging down trend settled into consolidation: bands 10.4 pips wide (narrow: <= 14, or narrowing for 6 candles: 2), middle band 0.1 pips/candle, no close outside the |
| 03:10 | ranging (none) | middle | bands 6.8 pips wide (close together: 6 to 18) and flat (upper -0.0, lower -0.1 pips/candle), both bands reached, EMAs weaving, 100 EMA moved 0.0 pips |
| 04:05 | consolidation (none) | middle | bands 4.8 pips wide (narrow: <= 14, or narrowing for 6 candles: 0), middle band -0.1 pips/candle, no close outside the bands for 6 candles, average body 0.6 pips, green/r |
| 05:50 | emerging trend (up) | middle | rejected at a level: closed 13226.7 above the reversal high 13226.3; trigger at above 13227.9 |
| 06:15 | consolidation (none) | middle | the emerging up trend settled into consolidation: bands 8.1 pips wide (narrow: <= 14, or narrowing for 6 candles: 1), middle band -0.1 pips/candle, no close outside the b |
| 06:55 | ranging (none) | middle | bands 9.9 pips wide (close together: 6 to 18) and flat (upper 0.1, lower -0.2 pips/candle), both bands reached, EMAs weaving, 100 EMA moved 1.0 pips |
| 07:05 | emerging trend (up) | top edge | broke out of the range: 2 closes above the band (last 13238.5, band 13236.5) |
| 07:15 | emerging trend (down) | middle | rejected at a level against the emerging up trend: closed 13232.3 below the reversal low 13234.4; trigger at below 13231.6 |
| 08:10 | consolidation (none) | middle | the emerging down trend settled into consolidation: bands 12.4 pips wide (narrow: <= 14, or narrowing for 6 candles: 6), middle band 0.4 pips/candle, no close outside the |
| 08:35 | emerging trend (down) | middle | rejected at a level: closed 13235.2 below the reversal low 13236.2; trigger at below 13235.2 |
| 09:25 | consolidation (none) | middle | the emerging down trend settled into consolidation: bands 12.9 pips wide (narrow: <= 14, or narrowing for 6 candles: 3), middle band 0.3 pips/candle, no close outside the |
| 09:45 | ranging (none) | middle | bands 13.2 pips wide (close together: 6 to 18) and flat (upper -0.0, lower 0.0 pips/candle), both bands reached, EMAs weaving, 100 EMA moved 0.5 pips |
| 09:55 | consolidation (none) | middle | bands 12.6 pips wide (narrow: <= 14, or narrowing for 6 candles: 1), middle band -0.2 pips/candle, no close outside the bands for 6 candles, average body 2.1 pips, green/ |
| 10:55 | emerging trend (up) | middle | rejected at a level: closed 13223.9 above the reversal high 13221.7; trigger at above 13225.3 |
| 11:40 | ranging (none) | middle | the emerging up trend turned into a range: bands 16.2 pips wide (close together: 6 to 18) and flat (upper -0.0, lower -0.0 pips/candle), both bands reached, EMAs weaving, |
| 12:35 | consolidation (none) | middle | bands 13.1 pips wide (narrow: <= 14, or narrowing for 6 candles: 3), middle band 0.2 pips/candle, no close outside the bands for 6 candles, average body 2.0 pips, green/r |
| 13:00 | emerging trend (up) | middle | rejected at a level: closed 13228.5 above the reversal high 13225.9; trigger at above 13228.8 |
| 13:45 | emerging trend (down) | middle | rejected at a level against the emerging up trend: closed 13237.2 below the reversal low 13238.8; trigger at below 13234.6 |
| 17:25 | trend (down, slow grind) | bottom edge | the rejection became a trend: a bounce failed under the 21 EMA and middle band, then a new low 13205.2 on the lower band 13204.6; EMAs 7/13/21 stacked down for 23 candles |
| 18:10 | possible reversal (up) | middle | rejection at a level (new_york_session_low 13204.3, S1 13206.0) confirmed after a down move of 32.9 pips: closed 13213.1 above the reversal high 13209.5; trigger at above |
| 18:20 | emerging trend (up) | middle | the reversal triggered: price went above 13214.9 (during this candle) |
| 18:30 | emerging trend (down) | middle | rejected at a level against the emerging up trend: closed 13210 below the reversal low 13212.8; trigger at below 13209.9 |
| 18:55 | ranging (none) | middle | the emerging down trend turned into a range: bands 12.4 pips wide (close together: 6 to 18) and flat (upper -0.1, lower 0.0 pips/candle), both bands reached, EMAs weaving |
| 19:10 | consolidation (none) | middle | bands 11.5 pips wide (narrow: <= 14, or narrowing for 6 candles: 19), middle band 0.0 pips/candle, no close outside the bands for 6 candles, average body 1.4 pips, green/ |
| 19:15 | emerging trend (up) | middle | rejected at a level: closed 13211.3 above the reversal high 13210.9; trigger at above 13211.8 |
| 19:25 | consolidation (none) | middle | the emerging up trend settled into consolidation: bands 9.3 pips wide (narrow: <= 14, or narrowing for 6 candles: 22), middle band 0.2 pips/candle, no close outside the b |
| 21:30 | emerging trend (down) | middle | rejected at a level: closed 13210.7 below the reversal low 13213; trigger at below 13210.7 |
| 21:50 | ranging (none) | middle | the emerging down trend turned into a range: bands 10.7 pips wide (close together: 6 to 18) and flat (upper 0.0, lower 0.0 pips/candle), both bands reached, EMAs weaving, |

#### All three switches on, edge 5 pips

**Trades that open**

| Opened | Strategy | Direction | Entry | Pips (paper) | How it closed |
|---|---|---|---|---|---|
| 08:20 | Asian range breakout | buy | 13241.8 | -12.0 | stopped by IG: the stop at IG |
| 08:40 | session sweep | sell | 13235.1 | +9.4 | stopped by IG: the stop at IG (trailed to 13225.7) |
| 11:00 | Bollinger bounce | buy | 13223.7 | +9.3 | stopped by IG: the stop at IG (trailed to 13234.5) |
| 15:05 | Bollinger bounce | sell | 13242.3 | +17.9 | stopped by IG: the stop at IG (trailed to 13224.4) |
| 15:10 | session sweep | sell | 13235.8 | +11.4 | stopped by IG: the stop at IG (trailed to 13224.4) |

**Orders the safety rules refused**

| Time | Strategy | Direction | Refused because |
|---|---|---|---|
| 03:25 | range trade | buy | outside the trading hours 06:00 to 20:30 UK |
| 03:45 | range trade | buy | outside the trading hours 06:00 to 20:30 UK |
| 14:00 | session sweep | sell | once a day: a session sweep trade has already opened for Asian high 2026-11-13 |

**State changes** (the whole UK day)

| Time | New state | Hourly position | Why (the analyser's own words) |
|---|---|---|---|
| 00:20 | consolidation (none) | middle | the emerging down trend settled into consolidation: bands 10.4 pips wide (narrow: <= 14, or narrowing for 6 candles: 2), middle band 0.1 pips/candle, no close outside the |
| 03:10 | ranging (none) | middle | bands 6.8 pips wide (close together: 6 to 18) and flat (upper -0.0, lower -0.1 pips/candle), both bands reached, EMAs weaving, 100 EMA moved 0.0 pips |
| 04:05 | consolidation (none) | middle | bands 4.8 pips wide (narrow: <= 14, or narrowing for 6 candles: 0), middle band -0.1 pips/candle, no close outside the bands for 6 candles, average body 0.6 pips, green/r |
| 05:50 | emerging trend (up) | middle | rejected at a level: closed 13226.7 above the reversal high 13226.3; trigger at above 13227.9 |
| 06:15 | consolidation (none) | bottom edge | the emerging up trend settled into consolidation: bands 8.1 pips wide (narrow: <= 14, or narrowing for 6 candles: 1), middle band -0.1 pips/candle, no close outside the b |
| 06:55 | ranging (none) | middle | bands 9.9 pips wide (close together: 6 to 18) and flat (upper 0.1, lower -0.2 pips/candle), both bands reached, EMAs weaving, 100 EMA moved 1.0 pips |
| 07:05 | emerging trend (up) | top edge | broke out of the range: 2 closes above the band (last 13238.5, band 13236.5) |
| 07:15 | emerging trend (down) | middle | rejected at a level against the emerging up trend: closed 13232.3 below the reversal low 13234.4; trigger at below 13231.6 |
| 08:10 | consolidation (none) | top edge | the emerging down trend settled into consolidation: bands 12.4 pips wide (narrow: <= 14, or narrowing for 6 candles: 6), middle band 0.4 pips/candle, no close outside the |
| 08:35 | emerging trend (down) | middle | rejected at a level: closed 13235.2 below the reversal low 13236.2; trigger at below 13235.2 |
| 09:25 | consolidation (none) | middle | the emerging down trend settled into consolidation: bands 12.9 pips wide (narrow: <= 14, or narrowing for 6 candles: 3), middle band 0.3 pips/candle, no close outside the |
| 09:45 | ranging (none) | middle | bands 13.2 pips wide (close together: 6 to 18) and flat (upper -0.0, lower 0.0 pips/candle), both bands reached, EMAs weaving, 100 EMA moved 0.5 pips |
| 09:55 | consolidation (none) | middle | bands 12.6 pips wide (narrow: <= 14, or narrowing for 6 candles: 1), middle band -0.2 pips/candle, no close outside the bands for 6 candles, average body 2.1 pips, green/ |
| 10:55 | emerging trend (up) | bottom edge | rejected at a level: closed 13223.9 above the reversal high 13221.7; trigger at above 13225.3 |
| 11:40 | ranging (none) | middle | the emerging up trend turned into a range: bands 16.2 pips wide (close together: 6 to 18) and flat (upper -0.0, lower -0.0 pips/candle), both bands reached, EMAs weaving, |
| 12:30 | emerging trend (up) | middle | rejected at a level: closed 13228.3 above the reversal high 13227.4; trigger at above 13228.6 |
| 12:40 | consolidation (none) | middle | the emerging up trend settled into consolidation: bands 13.0 pips wide (narrow: <= 14, or narrowing for 6 candles: 4), middle band 0.2 pips/candle, no close outside the b |
| 13:00 | emerging trend (up) | middle | rejected at a level: closed 13228.5 above the reversal high 13225.9; trigger at above 13228.8 |
| 13:45 | emerging trend (down) | middle | rejected at a level against the emerging up trend: closed 13237.2 below the reversal low 13238.8; trigger at below 13234.6 |
| 17:25 | trend (down, slow grind) | bottom edge | the rejection became a trend: a bounce failed under the 21 EMA and middle band, then a new low 13205.2 on the lower band 13204.6; EMAs 7/13/21 stacked down for 23 candles |
| 18:10 | possible reversal (up) | middle | rejection at a level (new_york_session_low 13204.3, S1 13206.0) confirmed after a down move of 32.9 pips: closed 13213.1 above the reversal high 13209.5; trigger at above |
| 18:20 | emerging trend (up) | middle | the reversal triggered: price went above 13214.9 (during this candle) |
| 18:30 | emerging trend (down) | middle | rejected at a level against the emerging up trend: closed 13210 below the reversal low 13212.8; trigger at below 13209.9 |
| 18:55 | ranging (none) | bottom edge | the emerging down trend turned into a range: bands 12.4 pips wide (close together: 6 to 18) and flat (upper -0.1, lower 0.0 pips/candle), both bands reached, EMAs weaving |
| 19:10 | consolidation (none) | middle | bands 11.5 pips wide (narrow: <= 14, or narrowing for 6 candles: 19), middle band 0.0 pips/candle, no close outside the bands for 6 candles, average body 1.4 pips, green/ |
| 19:15 | emerging trend (up) | middle | rejected at a level: closed 13211.3 above the reversal high 13210.9; trigger at above 13211.8 |
| 19:25 | consolidation (none) | middle | the emerging up trend settled into consolidation: bands 9.3 pips wide (narrow: <= 14, or narrowing for 6 candles: 22), middle band 0.2 pips/candle, no close outside the b |
| 21:30 | emerging trend (down) | middle | rejected at a level: closed 13210.7 below the reversal low 13213; trigger at below 13210.7 |
| 21:50 | ranging (none) | middle | the emerging down trend turned into a range: bands 10.7 pips wide (close together: 6 to 18) and flat (upper 0.0, lower 0.0 pips/candle), both bands reached, EMAs weaving, |


## Questions and gaps

1. **Possible reversal and the Asian range breakout** (answer 9 above): built as "nothing new". Confirm or change.
2. **The edge distance:** 3 or 5 pips, your choice (above). The setting stays at 3 until you say. If you choose 5, the 06:35/08:55/14:45 test would need your new expectation for 08:55 and 14:45, since they then happen by your rule.
3. **17 November afternoon at 3 pips:** the analyser stays in consolidation from 13:50 to 17:00, through the 13:50–16:25 rally. Nothing in the rules can lift it out: the 13:50 rejection is 4.8 pips inside the hourly low; the 15:40 rejection is in the middle; and no 5-minute close went 4 pips beyond the band. It turns "emerging up" only at 17:00, once the hourly read is a rally. The trend group therefore takes no trade in the rally until the 17:15 EMA pullback. This follows your rules as written; I'm flagging it, not changing it.
4. **Speed:** the full-engine replay is slow on this server (about 7 minutes for 17 November's two-day week, 30 minutes or more for a full week), so the tests use the faster strategy replay. Both run the same checks at entry; only the full engine adds the safety rules and the trade manager.
5. No other gaps found. Nothing was added beyond your rules and answers.

## Files

- Code: listed in "What was built".
- Docs: `docs/DESIGN.md` (2.2, 2.10, 3.3, 3.6, 3.7–3.9, 6), `docs/SETTINGS.md`, `docs/ANALYSER.md`.
- Replay tool: `.venv/bin/python -m research.analyser_control_days <day> [on|off [edge_pips [result.json]]]`.
- Raw results beside this report: `day_<date>_<on|off>_edge<pips>.json` and `.txt`.
