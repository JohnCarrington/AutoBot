# STP on Monday 23 November 2026, against PIA First's 09:11 buy

Read only. Nothing in the bot, its settings or its data was changed. Server: the new AutoBot server, /opt/autobot
(not AutoBot 161). UK time is UTC in November, so every time below is both. Prices are GBPUSD in the bot's points
(13081 = 1.3081).

## The answer in brief

- **Code (8c139df):** every STP run on Monday used code that includes 8c139df. The dashboard process does not include it, but it never runs the code 8c139df changed.
- **STP called the day down, all day.**
  - **The planner:** 6 recommendations, all SELL.
  - **The forecaster:** 16 forecasts, 15 SELL and 1 BUY.
- **No counter-trend buy near PIA's level.**
  - **14:00:** the forecaster's only buy was at 13062.0–13071.5, about 10 pips below PIA's 13081 entry.
  - **00:00 and 13:00:** it weighed a buy at 13075–13084, but scored it 3, below its minimum of 4, so it never issued it.
- **It saw 1.3075 as a level, but used it the other way.**
  - **12:00:** the planner made "previous week low 13075" its sell target.
  - **13:00:** once price was below it, the planner sold from it, as resistance.
- **It saw the momentum signs PIA gave, but read them as a pause in a down trend.**
  - **00:00 and 13:00:** the planner recorded "exhaustion: a new extreme that momentum does not confirm" (PIA: bullish divergence).
  - **All six recommendations:** "4-hour MACD … moving towards zero for 3 candles (momentum weakening)" (PIA: weakening bearish momentum).
  - **Its reading:** a "corrective reversal", meaning "UP into resistance, then DOWN". So it sold the bounce rather than buying it.
- **The price agreed with STP, not PIA.**
  - **PIA's buy:** filled at 12:45 and never rose above 13086.3. It hit its 13029 stop at 15:50, a loss of 52 pips.
  - **The planner's 6 sells:**
    - 2 entered and reached their target (10:00, 12:00);
    - 2 were dropped because price reached the target before the entry zone (09:00, 13:00);
    - 1 was invalidated by an hourly close above its zone, after touching its intermediate target (01:00);
    - 1 was replaced (00:00).
  - **The forecaster's sells that entered:** at 07:00, 09:00 and 10:00, price reached the first target before the stop. At 08:00 the target was hit in the entry candle itself. At 00:00 and 04:00 the stop came first.

## 1. The code the running bot and the dashboard loaded

| Process | Started (UTC) | Code at /opt/autobot then | Includes 8c139df? |
|---|---|---|---|
| Price service (old process) | Sat 21 Nov 14:08:39 | 4635175 | yes |
| Price service (new process) | Mon 23 Nov 18:37:34 | e11b4af | yes |
| Dashboard | Fri 20 Nov 12:11:18 | bb085f4 | **no** |

**What matters is how STP runs.** The price service does not run STP itself. After each 5-minute candle it starts
`nice -n 10 python -m planner run` as a new process (`planner/keeper.py`, `PlannerUpdater.command`). That process
runs the planner, then the technical forecaster (`planner/__main__.py`, `technical.write`).
- **Every run loads the code fresh.** It reads the code on disk at `/opt/autobot` at that moment.
- **All day Monday, that code included 8c139df.**
  - 00:00 to 18:12: 4635175.
  - From 18:12: deploy-23nov, 6aaca7d and then e11b4af.

**The dashboard reads STP's files, and runs none of the forecaster's code.**
- **What 8c139df changed:** only `forecast()` in `planner/technical.py`, a line-break fix in the level-map call.
- **What the dashboard runs:** `planner/panel.py` and `dashboard/stp.py`, which read `current.json` and
  `technical.json`. They never call `forecast()`.
- **Its display code is up to date:** those two files are identical in bb085f4 and e11b4af.

So the dashboard shows what the 8c139df code wrote. The dashboard process itself is still the 20 Nov one, and it
hasn't been restarted.

## 2. Every STP forecast, 00:00 to 18:00 UK

Records: `data/planner/GBPUSD/recommendations.jsonl` (the planner's events), `issued.jsonl` (each recommendation in
full) and `technical.jsonl` (the forecaster, hourly). The full extracts are in `rec_events.txt` and `tech_full.txt`.

### The planner (the Structural Trade Planner)

**What the planner said all day.** Direction BEARISH at every hourly analysis.
- **Condition:**
  - EXHAUSTION at 00:00 and 13:00–15:00;
  - CORRECTION_ACTIVE from 01:00 to 12:00;
  - CONTINUATION from 16:00.
- **Kind of trade:** "corrective reversal", with expected movement "UP into resistance, then DOWN".
- **Stop:** invalidation is an hourly close 3 pips beyond the zone, not a price touch. A zone counts as reached
  within 3 pips.

| ID (created) | Trade | Entry zone | Levels in the zone | Stop: hourly close at or above | Targets: intermediate / primary / extended |
|---|---|---|---|---|---|
| …0000-9 (00:00:02) | SELL | 13119.1–13128.6 | hourly swing low 13119.1 (former support, now resistance), hourly and London high 13121.9, weekly pivot 13127.3, 4-hour swing high 13128.6, NY high 13128.6, H4 Bollinger middle 13128.6 | 13131.6 | 13100 / **13084.1** / — |
| …0100-10 (01:00:01) | SELL | 13113.2–13121.9 (13123.7 from 04:00) | daily R2 13113.2, hourly swing low 13119.1, hourly and London high 13121.9 (H4 Bollinger middle 13123.7 added) | 13124.9 | 13103.7 / **13097.1** / 13084.1 |
| …0900-11 (09:00:02) | SELL | 13127.3–13135.6 | weekly pivot 13127.3, 4-hour and hourly swing high 13128.6, NY high 13128.6, daily R3 13129.3, hourly swing low 13135.5, daily and 4-hour swing low 13135.6 | 13138.6 | 13121.9 / **13121.9** / 13103.7 |
| …1000-12 (10:00:03) | SELL | 13111.8–13121.9 | London low so far 13111.8, daily R2 13113.2, hourly swing low 13119.1, H4 Bollinger middle 13119.9, hourly and London high 13121.9 | 13124.9 | 13103.7 / **13103.7** / 13097.1 |
| …1200-13 (12:00:02) | SELL | 13087.6–13097.1 | daily pivot 13087.6, hourly swing low and London low 13093, London low 13094.5, previous day high 13097.1 | 13100.1 | 13084.1 / **13084.1** / 13071.5 |
| …1300-14 (13:00:03) | SELL | 13075–13084.1 | **previous week low 13075**, 4-hour and hourly swing low 13077, hourly swing low 13077.5, NY low 13077.6, daily S1 13078.1, historical daily swing low 13084.1 (former support, now resistance) | 13087.1 | 13071.5 / **13071.5** / — |

**Hours with no recommendation:**
- **07:00, 08:00, 11:00, 14:00:** "the primary destination … is already reached … no recommendation is issued for a destination price has already reached (D-1 correction)".
- **15:00–18:00:** "no Major support zone below the entry zone for the primary destination".

**The planner's reasons, quoted from recommendation 0000-9 (the same in each).**
- **Direction:**
  - "4-hour structure: lower highs and lower lows: swing highs 13171.9 then 13128.6, swing lows 13168 then 13077";
  - "4-hour EMA 7/13/21 stack: 7 < 13 < 21 (down)";
  - "4-hour close 13094.2 below the EMA100 13249.7";
  - "4-hour EMA100 falling 19.8 pips over 6 candles";
  - "warning: the daily structure (up) is against the 4-hour structure (down)".
- **Condition:**
  - "impulse from the 4h swing high 13128.6 (Fri 20 Nov 12:00 GMT) to the low 13071.5 (Sun 22 Nov 20:00 GMT)";
  - "new low: 13071.5 beyond the previous swing low 13077";
  - "4-hour MACD line -20.70, histogram -3.24, moving towards zero for 3 candles (momentum weakening)";
  - "4-hour RSI 53.2 (back inside its line after the impulse)";
  - "exhaustion: a new extreme that momentum does not confirm".

### The technical-opportunity forecaster

All of these are on the chart (sell) price. "Score" is the forecaster's evidence count; 4 is the minimum for a
forecast. The 4-hour direction is BEARISH at every hour.

| As of (UTC) | Set-up | Trade | Entry zone (basis) | Stop | Targets T1 / T2 | Score |
|---|---|---|---|---|---|---|
| 00:00:07 | pullback | SELL | 13090.3–13101.4 (H1 EMA20 13095.8 ± 5.5) | 13105.9 | 13084.1 / 13037.3 | 4 |
| 01:00:04 | pullback | SELL | 13091.1–13102.1 (H1 EMA20) | 13106.4 | 13084.1 / 13071.5 | 4 |
| 02:00:04 | — | none | "the best set-up (failed breakout BUY at 13087.6-13093.1) has 2 evidence points, below the minimum 4" | | | |
| 03:00:03 | pullback | SELL | 13093.2–13104.2 (H1 EMA20) | 13108.1 | 13084.1 / 13071.5 | 5 |
| 04:00:04 | pullback | SELL | 13093.9–13104.9 (H1 EMA20) | 13108.7 | 13084.1 / 13071.5 | 5 |
| 05:00:04 | pullback | SELL | 13094.6–13105.6 (H1 EMA20) | 13109.1 | 13084.1 / 13071.5 | 4 |
| 06:00:06 | — | none | "no pullback, reaction or breakout set-up with a destination beyond it" | | | |
| 07:00:05 | reversal | SELL | 13127.3–13135.6 (Major zone: weekly pivot 13127.3, 4-hour, hourly and NY high 13128.6) | 13139.2 | 13123.7 / 13103.7 | 5 |
| 08:00:04 | reversal | SELL | 13127.3–13135.6 (same) | 13139.2 | 13121.9 / 13103.7 | 5 |
| **09:00:07** | reversal | **SELL** | 13127.3–13135.6 (same) | 13146.0 | 13121.9 / 13103.7 | 5 |
| 10:00:06 | pullback | SELL | 13103.6–13114.6 (H1 EMA20 13109.1) | 13118.7 | 13097.1 / 13084.1 | 4 |
| 11:00:05 | failed breakout | SELL | 13116.4–13121.9 (back inside Major zone 13113.2–13121.9) | 13146.2 | 13103.7 / 13097.1 | 5 |
| 12:00:05 | pullback | SELL | 13102.0–13113.1 (H1 EMA20) | 13117.2 | 13084.1 / 13071.5 | 4 |
| 13:00:05 | pullback | SELL | 13099.5–13110.6 (H1 EMA20) | 13115.0 | 13071.5 / 13052.5 | 5 |
| **14:00:05** | **reversal** | **BUY (countertrend)** | **13062.0–13071.5** (daily S2 13062.0, previous day low 13071.5, 4-hour and hourly swing low 13071.5) | 13045.6 | **13075** / 13087.6 | 4 |
| 15:00:06 | pullback | SELL | 13090.7–13101.8 (H1 EMA20) | 13107.1 | 13037.3 / 13000 | 4 |
| 16:00:05 | pullback | SELL | 13083.3–13094.4 (H1 EMA20) | 13100.3 | 13015.8 / 13000 | 4 |
| 17:00:04 | — | none | "the best set-up (failed breakout SELL at 13066.0-13071.5) has 3 evidence points, below the minimum 4" | | | |
| 18:00:12 | pullback | SELL | 13070.5–13081.5 (H1 EMA20 13076.0) | 13087.6 | 13014.2 / 13000 | 6 |

**The 09:00 forecast, nearest to PIA's 09:11 call, in its own words:**
- "the 4-hour direction (existing STP) is BEARISH";
- the Major zone 13127.3–13135.6 "is Major";
- "tested 8 times before";
- "back inside the Bollinger band after touching the upper band (13133.0)";
- "H1 EMA20 flat (0.8/candle): no strong trend into the zone".

**The 14:00 counter-trend buy, in its own words:**
- "against the 4-hour direction (existing STP: BEARISH): countertrend, lower confidence" (−1);
- "Major zone 13062.0-13071.5 … is Major";
- "tested 2 times before";
- "Mon 23 Nov 13:00 GMT H1 bullish rejection (O 13081.4 H 13083.9 L 13050.4 C 13069)";
- "back inside the Bollinger band after touching the lower band (13065.0)";
- "H1 EMA20 flat (0.3/candle)".

Score 4, reward-to-risk 0.3. Its stated alternative: "If instead an H1 candle closes at or below 13059.0 and price holds below the stop 13045.6, the support has given way: look for a SELL on a retest".

**BUY set-ups the forecaster weighed but did not issue (score below 4):**

| Time | Set-up | Entry zone | Score |
|---|---|---|---|
| 00:00 | failed breakout BUY | 13075.0–13080.5 | 3 |
| 02:00 | failed breakout BUY | 13087.6–13093.1 | 2 |
| 05:00 | reversal BUY | 13100.0–13103.7 | 1 |
| **13:00** | **reversal BUY** | **13075.0–13084.1** | **3** |
| 13:00 | failed breakout BUY | 13075.0–13080.5 | 2 |
| 15:00 | reversal BUY | 13043.1–13052.5 | 2 |
| 18:00 | reversal BUY | 13009.7–13014.2 | 0 |

## 3. Against PIA First (about 09:11: BUY 1.3081, stop 1.3029, target 1.3222, support 1.3075)

**Did STP find a counter-trend buy?**
- **Not at PIA's level or time.** At 09:00 and 10:00 both parts of STP said SELL.
- **The only counter-trend buy came at 14:00,** at 13062.0–13071.5, 10–19 pips below PIA's entry. Its first target was 13075, PIA's support.
- **It nearly issued one at 13:00:** a reversal BUY at 13075.0–13084.1, around PIA's level, scored 3 against the minimum of 4.

**Did it see support near 1.3075?** Yes, as a level: 13075 appears in 13 of the forecaster's 19 Monday forecasts and in 3 of the planner's Monday events. But STP used it for selling, not buying:
- **00:00 and 12:00:** in the planner's target zone for a sell (13075–13084.1).
- **13:00:** the planner's entry zone for a SELL. It treated the zone as resistance, since price had fallen into it from above.
- **13:00:** the forecaster's 3-point buy candidate.
- **14:00:** the forecaster's target for its counter-trend buy.

**Did it see the reversal, or call the day down?** It called the day down. It saw the same momentum evidence as PIA:
- "a new extreme that momentum does not confirm", PIA's bullish divergence;
- "momentum weakening", PIA's weakening bearish momentum.

By its rules that means "EXHAUSTION" or "CORRECTION_ACTIVE" inside a BEARISH 4-hour direction: a bounce into resistance to sell, not a buy. Neither part of STP mentions "divergence" by that word.

## 4. What price did after each forecast

**The day's path:**
- **High:** 13142.1 at 08:40.
- **Low:** 13010.1 at 17:45.
- **Last:** 13021.7 at the 18:45 candle. The day had not finished when this was written (about 18:50 UTC), so "not reached" means not reached by then.

The checks use the bot's own IG 5-minute candles in `data/candles/GBPUSD`. The script is `paths.py`, and its output is `paths.txt`.

**The planner, in its own records:**

| ID | What happened |
|---|---|
| 0000-9 | **Superseded at 01:00**, before price reached it ("a zone resting on different fixed levels"). |
| 0100-10 | **Active at 01:15** ("the Mon 23 Nov 01:10 GMT 5-minute candle reached the zone", within 3 pips). Back to waiting at 05:00; active again at 05:15. **Invalidated at 07:00:** "confirmed break: the Mon 23 Nov 06:00 GMT hourly candle closed at 13127.3, 3.6 pips beyond the zone's top 13123.7". In between, its intermediate target 13103.7 was reached at 04:10, but its primary 13097.1 only at 11:35, after invalidation. |
| 0900-11 | **Invalidated at 09:10:** "destination reached before entry: price reached 13121.9 (Mon 23 Nov 09:05 GMT) without reaching the zone". The 09:00 candle touched the zone but was recorded as ambiguous, because it began before the recommendation. |
| 1000-12 | **Active at 10:10, completed at 10:20:** "price reached the primary destination 13103.7 (Mon 23 Nov 10:15 GMT) after the zone". No stop. |
| 1200-13 | **Active at 12:10, completed at 12:45:** "price reached the primary destination 13084.1 (Mon 23 Nov 12:40 GMT) after the zone". No stop. |
| 1300-14 | **Invalidated at 13:10:** "destination reached before entry: price reached 13071.5 (Mon 23 Nov 13:05 GMT) without reaching the zone". |

**The forecaster, by price: entry zone touched, then the stop or target first.** "Stop before entry" means price hit the stop before ever reaching the entry zone, so the forecast was spent.

| As of | Trade | Entry zone reached | Stop / target, first | Then |
|---|---|---|---|---|
| 00:00 | SELL | yes, in it at 00:00 | **stop** at 01:00 | T1 13084.1 only at 12:45 |
| 01:00 | SELL | at 11:10 | **stop before entry** (01:00) | (T1 and T2 at 12:45) |
| 03:00 | SELL | at 04:10 | **stop before entry** (03:05); stop again at 04:55 | (T1 and T2 at 12:45) |
| 04:00 | SELL | yes, at 04:00 | **stop** at 05:05 | (T1 and T2 at 12:45) |
| 05:00 | SELL | at 10:20 | **stop before entry** (05:05) | (T1 and T2 at 12:45) |
| 07:00 | SELL | yes, at 07:00 | **T1** 13123.7 at 07:10 | stop at 08:35; T2 at 10:20 |
| 08:00 | SELL | at 08:05 | **T1** 13121.9 in the same 08:05 candle as the entry | stop at 08:35; T2 at 10:20 |
| 09:00 | SELL | yes, in it at 09:00 | **T1** 13121.9 at 09:30 | **T2** 13103.7 at 10:20; no stop |
| 10:00 | SELL | yes, in it at 10:00 | **T1** 13097.1 at 11:35 | **T2** 13084.1 at 12:45; no stop |
| 11:00 | SELL | no | zone never reached; T1 and T2 reached without it (11:05, 11:35) | |
| 12:00 | SELL | no | zone never reached; T1 and T2 reached without it (12:45) | |
| 13:00 | SELL | no | zone never reached; T1 and T2 reached without it (13:10, 13:50) | |
| **14:00** | **BUY** | yes, in it at 14:00 | **T1** 13075 inside the 14:00 candle (high 13078.1) | **stop** 13045.6 at 14:50; T2 never |
| 15:00 | SELL | no | zone never reached; T1 at 15:05 without it | |
| 16:00 | SELL | no | zone never reached; T1 at 16:00 without it | |
| 18:00 | SELL | no | zone not reached by 18:45 | |

**PIA First's buy, on the same candles:**
- **Fill:** the 13081 buy filled at 12:45, on the buy price (that candle's buy low was 13067.1).
- **After the fill:** price never got above 13086.3.
- **Stop:** 13029 was hit at 15:50 (sell low 13028.1). That's −52 pips.
- **Target:** 13222 was never close. The day's high was 13142.1, at 08:40, before the fill.

## Limits

- **Prices:**
  - One 5-minute candle can't show what came first inside it, so I name the cases where that matters (08:00, 14:00).
  - The planner's own "reached" allows 3 pips, so its records quote that; the forecaster checks use a strict touch.
  - The checks use the chart (sell) price. The spread is about 1.5 pips, and only PIA's fill uses the buy price.
- **Day not finished:** the day ran on after this was written, so the outcomes stop at the 18:45 candle.
- **One day only:** this is one day and says nothing about STP's record in general.
- **PIA's call:** I have PIA's call only as quoted in the brief (about 09:11). There is no PIA record on this server.
