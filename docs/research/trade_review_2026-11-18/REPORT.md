# Review of Wednesday 18 November 2026's trades (read-only)

AutoBot on 167.99.95.19, GBPUSD, IG demo. Written on the evening of 18 November 2026. The data was taken after the 20:30 UK close, from candles up to the 20:45 candle. One trade, the 15:44 breakout sell, is still open; breakouts are held overnight except on Fridays.

Nothing was changed, switched or restarted. No IG call was made and IG's history allowance was not used. Everything here comes from the bot's own records:
- trade records;
- decision records;
- the trade manager's journal;
- the analyser's journal;
- the service log;
- the bot's own 5-minute and hourly candles;
- paper replays run on branch `feature/entries-exits`. The replays write only to a temporary folder.

Times are UK; in November UK time is GMT, the same as the UTC the bot stores. Prices are the sell (bid) price unless a field says "buy" or "fill". One pip is 1.0 in these numbers: 13152.9 means 1.31529.

**Closed by you (IG "SYSTEM"): none today.** All six closed trades have `"closed_by": "bot"` in `trade_records_2026-11-18.jsonl`.

---

## Summary

**The day.**
- **Closed trades:** seven trades opened and six closed: 2 won, 4 lost, **−22.0 pips** in all.
- **Old rules (before the 13:35 restart):** three trades, +16.3.
- **New rules (after 13:35):** four trades:
  - three have closed, all losses: −12.0, −15.0 and −11.3;
  - the breakout sell is still open, 4.4 pips in favour at the 20:45 close.
- **The market:**
  - UK CPI at 07:00 started a 45-pip fall to 13148.
  - From 09:05 to 15:15 price went sideways between 13148 and 13175.
  - Price broke down again from 15:15 to 13135.5 at 16:20, then went sideways around 13150.
  - The FOMC minutes at 19:00 pushed it to 13135.6.
  - It ended the session back at 13150.

**How the analyser did after 13:35.**
- **It calmed down a lot.** It changed state 10 times in 7 hours. The old code changed state 22 times between midnight and 08:35.
- **It flagged the 15:35 break at once.** That gave the one good trend trade, the breakout sell at 13152.9.
- **But both of its "trend" calls came late, 4 to 7 pips before the low:**
  - The 16:15 call: the trend group sold at 16:20 and 16:37 into the bottom, and both trades were stopped by the 17-pip bounce at 16:58 (−27.0).
  - The 19:25 call: the 19:50 level reversal sell opened 0.1 pip off the low and was stopped at 20:19 (−11.3).
- **It stayed "trend down" through two hours of sideways price** (16:55–18:55) and through the 20:00–20:30 bounce.
- **It flipped back and forth once:** four changes between 15:35 and 16:15, around the round number 13150.

**What the new rules blocked after 13:35.**
- **No "same signal" refusal.**
- **ANALYSER_GOVERNS_ALL alone blocked four reversal buys between 16:50 and 17:25**, all against the down trend while price went sideways after the low. Two more came at 20:30 and 20:35, after new-trade hours, so they were refused anyway.
- **What a replay with ANALYSER_GOVERNS_ALL off shows:**
  - Two of the four would have opened: the 16:50 level reversal buy and the 17:00 session sweep buy.
  - Both would have been closed at 18:45, 15 minutes before the FOMC minutes, in profit: +10.7 and +5.5.
  - Neither came within 6 pips of its stop.
  - The other two would have been refused anyway: one trade at a time, once a day, and "same signal".
- **So today the blocks stopped two winners and saved no losers.** This is one day and not a verdict on the rule.

**What Stage 4 would have changed today.** It would have changed only trades that use LEVEL_STOPS, all on the stop side:
- **The 12:35 EMA pullback sell (−12.6 live):** it gets a 16.8-pip stop above the 13166.9–13168 group. The 13:10 high came **0.4 pips** short of it, so the trade survives and is still open at the end of the replay, about 8 pips in favour.
- **The 16:20 EMA pullback sell (−12.0 live):** it gets an 8.4-pip stop above the 13140.2–13142.7 group and loses 8.4 instead of 12.0.
- **The live 19:50 level reversal sell (−11.3):** by hand (the replay doesn't produce this trade; see step 5), it gets a stop 0.4 pip tighter. That gives about −10.9, the same stop-out.
- **Nothing else changes:**
  - SCALE_OUT_REVERSAL changes nothing: no level reversal reached +8.
  - TRAIL_NO_LOSS changes nothing: no first trail move was at a loss.
  - LR_ENTRY_NEAR_LEVEL refuses only ideas that were refused anyway.

**Two things to know, neither changed:**
1. **The analyser's journal has seven entries from 09:30 to 13:15 that the live bot never used.** The 13:35 restart's replay of the morning, under the new code, wrote them. Under the old rules the live state was "trend down, slow grind" from 08:35 until the restart (step 3).
2. **The live 19:50 level reversal sell came from the live check on the forming candle.** The check at the candle's close did not find it, live or in the replay. It is the only trade today with no candle-close record. I have not found why; it needs a look at the code (step 5).

---

## 1. Every trade today

The 13:35 restart is in the log: `13:35:20 GMT INFO autobot.prices.service: Received SIGTERM: stopping.`, then `13:36:02 GMT INFO autobot.trading: Trading ON: 0 open trade(s) taken over; the strategies are up to 2026-11-18 13:35 UTC.`

| # | Rules | Opened | Closed | Strategy | Dir | Entry (signal / IG fill) | Stop at open | Close | Pips | How it closed | Analyser state at open | Hourly read at open | Hourly position at open |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | old | 07:30:02 | 09:25:12 | Asian range breakout | sell | 13179.8 / 13180.2 | 13192.2 (12) | 13158.5 | **+21.7** | IG stop, trailed to 13158.5 | emerging trend up | ranging (13186.8–13219.6) | not recorded (old code) |
| 2 | old | 09:30:01 | 11:03:23 | Bollinger bounce | buy | 13161.5 / 13163.1 | 13151.1 (12) | 13170.3 | **+7.2** | IG stop, trailed to 13170.3 | trend down, slow grind | sell-off (range 13150.6–13211.1) | not recorded (old code) |
| 3 | old | 12:37:37 | 13:07:56 | EMA pullback | sell | 13156.2 / 13156.4 | 13168.4 (12) | 13169.0 | **−12.6** | IG stop (0.6 worse than the stop) | trend down, slow grind | sell-off (range 13148–13206.9) | not recorded (old code) |
| 4 | **new** | 15:44:06 | **still open** | breakout | sell | 13153.7 / 13152.9 | 13164.9 (12); take profit 13102.9 | | open | | emerging trend down | sell-off (range 13148–13201.9) | middle |
| 5 | **new** | 16:20:25 | 16:58:30 | EMA pullback | sell | 13140.8 / 13141.1 | 13153.1 (12) | 13153.1 | **−12.0** | IG stop | trend down, strong push | sell-off (range 13148–13198.6) | bottom edge |
| 6 | **new** | 16:37:27 | 16:58:29 | slow grind | sell | 13138.2 / 13138.1 | 13153.1 (15) | 13153.1 | **−15.0** | IG stop | trend down, strong push | sell-off (range 13148–13198.6) | bottom edge |
| 7 | **new** | 19:50:58 | 20:19:50 | level reversal | sell | 13135.7 / 13135.8 | 13147.1 (11.3); take profit 13115.8 | 13147.1 | **−11.3** | IG stop | trend down, slow grind | sell-off (range 13135.5–13192.7) | middle |

Where each column comes from:
- **Analyser state:** the trade record's `market_state`, which is the state the strategies checked.
- **Hourly read:** the trade record's "allowed at entry" step, for example `hourly sell-off: the Wed 18 Nov 08:00 GMT hourly candle closed at 13153.3, 16.8 pips below the low 13170.1 of the 12 hourly candles before it`.
- **Hourly position:** the analyser's journal (the last entry before the open). The old code (dd9d36d) has no hourly position: `git grep hourly_position dd9d36d -- analyser/` finds nothing.

**Most in favour and most against**, on the chart (sell) price, from the 5-minute candles after the opening candle up to the closing candle:

| # | Most in favour | Most against | Bot's own `best_pips` |
|---|---|---|---|
| 1 | 32.2 (low 13148.0) | never against | 30.7 |
| 2 | 12.5 (high 13175.6) | never against | 12.5 |
| 3 | 6.7 (low 13149.7) | 14.0 (high 13170.4) | 5.2 |
| 4 | 17.4 so far (low 13135.5 at 16:20) | 4.6 (high 13157.5 at 18:40) | 16.1 so far (`open_trades.json`) |
| 5 | 5.0 (low 13136.1) | 11.2 (high 13152.3) | 4.3 |
| 6 | 2.0 (low 13136.1) | 14.2 (high 13152.3) | 0.5 |
| 7 | never in favour after the opening candle (lowest 13136.6 at 19:55) | 10.3 (high 13146.1, 20:15 candle) | −1.3 (never in profit at the close price) |

**Notes on each trade:**

- **1, Asian range breakout sell (+21.7).**
  - The setup: `Wed 18 Nov 07:25 GMT closed at 13179.2, below the Asian low (the Asian range 00:00 to 07:00, high 13206.9, low 13186.8)`.
  - The trail started at 08:10: `14.8 pips up at best (the trail from 12): the stop moves to 13177.0, beyond the last 3 candles`. It followed price down to 13158.5 at 09:20.
  - The trade was stopped at 09:25:12 as the 09:25 candle rose to 13161.9. The buy price reaches the stop about 1.5 pips before the chart price does.
- **2, Bollinger bounce buy (+7.2).**
  - The setup: `09:20 ... low 13150 went 9.4 pips below the lower hourly Bollinger band ... closed green; 09:25 ... closed at 13161.4, above the rejection candle's high (13156.2)`.
  - **This was the first live run of yesterday's trail fix.** At 11:00 IG would not take the move to 13171.7. The bot tried 3 times, then gave up and alerted you once: `gave up after 3 attempts: the stop stays at 13170.3` and `ALERT stop-move-gave-up-AB261118093004-63abaf9b`.
  - Yesterday the same situation produced 31 attempts. Today the stop held at 13170.3, which IG filled at 11:03:23. The fix behaved as written.
- **3, EMA pullback sell (−12.6).**
  - Entered on the pullback to the 5-minute 8 EMA: `price rose to the 5-minute 8 EMA 13163.2 (high 13164.5); closed 13161.1`.
  - Price fell to 13149.7 at 12:45, 6.7 pips in favour. It then rose 21 pips (13170.4 in the 13:05 candle) and took the stop at 13:07:56.
  - Its take profit was `"100 for a big-news day"`, because of UK CPI.
- **4, breakout sell (still open).**
  - The signal: `the analyser moved from ranging to an emerging trend down: broke out of the range: 2 closes below the band (last 13155.0, band 13155.8)`.
  - The breakout has a fixed 12-pip stop and a 50-pip take profit. It has no trail and is closed at 20:30 only on Fridays (DESIGN.md, "Breakout exits"). The trade manager has recorded no decision on it.
  - At the 20:45 close (13148.5) it was 4.4 pips in favour on the chart price.
- **5 and 6, EMA pullback and slow grind sells (−12.0 and −15.0).**
  - Both opened within 3 to 5 pips of the day's low, 13135.5 at 16:20.
  - Both were stopped at 16:58 by the same 17-pip bounce to 13152.3 (16:55; buy-price high 13153.8, above both stops at 13153.1).
  - Both stops sat 3 to 5 pips above the round number 13150 and the London low 13148. Price broke those at 15:55 and came back up to test them from below at 16:55.
- **7, level reversal sell (−11.3).**
  - The setup: `pierced S2 13140.2 at 19:30, reversal 19:35, confirmed 19:45, broke it 19:50`. It entered at 13135.7, 0.1 pip above the low of the FOMC drop (13135.6).
  - Price then rose 10 pips in the 20:15 candle (high 13146.1; buy-price high 13147.6) and took the stop at 20:19:50 (`the stop at IG (IG's level)`).
  - Step 5 has a note on how this trade opened.

---

## 2. What the market did today

The bot's hourly candles (sell price) are in `candles_1h_2026-11-18.csv`; the 20:00 hour comes from the 5-minute candles up to 20:45. Levels are from the bot's level list (`data/levels/GBPUSD/current.json`), built from Tuesday's candle `sell H 13227.9 L 13168 C 13204.4`:
- pivot 13200.1;
- S1 13172.3 and S2 13140.2;
- Tuesday's low 13168;
- today's London low 13148, with the round number 13150.

| Hour | O | H | L | C | What price did |
|---|---|---|---|---|---|
| 00–06 | 13205.2 | 13206.9 | 13186.8 | 13190.4 | **Ranged** in the Asian range 13186.8–13206.9, drifting down from the pivot. |
| 07:00 | 13189.1 | 13192.7 | 13170.1 | 13172.8 | **UK CPI** (big news: `Inflation Rate YoY act 3.6 est 3.6`, `Core Inflation Rate MoM act 0.3 est 0.3`). Fell 15 pips in the first candle (07:00 close 13176.7), **through the Asian low, Tuesday's low and S1. The trend down began.** |
| 08:00 | 13172.9 | 13175.4 | 13150.6 | 13153.3 | **Trended down** to the round number 13150. |
| 09:00 | 13153.2 | 13172.1 | 13148.0 | 13170.8 | **Turned** at the London low 13148 (09:05), then rose 24 pips to 13172.1 (09:55), back to S1. |
| 10:00 | 13170.6 | 13175.6 | 13163.6 | 13173.7 | Sideways under S1 and Tuesday's low (13168–13175). |
| 11:00 | 13173.5 | 13173.8 | 13154.4 | 13157.0 | Down again, 19 pips. |
| 12:00 | 13156.7 | 13166.9 | 13149.7 | 13160.1 | Sideways 13150–13167. A dip to 13149.7 at 12:45 held 13150. |
| 13:00 | 13159.8 | 13172.6 | 13159.4 | 13162.6 | Up to 13172.6 at 13:10, just under S1, then back down. US housing data at 13:30 caused no clear move. |
| 14:00 | 13162.9 | 13169.1 | 13157.0 | 13164.2 | **Sideways**, 12 pips. |
| 15:00 | 13165.0 | 13168.6 | 13148.1 | 13148.1 | Sideways until 15:15, then down. **Closed below the 13150/13148 floor at 15:55.** |
| 16:00 | 13147.8 | 13152.4 | 13135.5 | 13150.2 | **Low of the day, 13135.5, at 16:20**, 4.7 below S2. **Turned**: rose 17 pips to 13152.3 by 16:55, back to test the broken 13150 from below. |
| 17:00 | 13150.3 | 13155.1 | 13143.9 | 13151.6 | Sideways around 13150. |
| 18:00 | 13151.5 | 13157.5 | 13150.1 | 13151.9 | Sideways, very narrow (7 pips). |
| 19:00 | 13151.5 | 13151.9 | 13135.6 | 13138.8 | **FOMC minutes at 19:00** (big news; the 18:55 candle closed with a 6.4-pip spread). Fell 16 pips to 13135.6 by 19:50, the same as the 16:20 low. |
| 20:00 (to 20:45) | 13138.7 | 13150.1 | 13137.6 | 13148.5 | **Turned up** from the double low at 13135.5/13135.6 and rose 14 pips back to 13150 by 20:30. |

**In short:**
- **Trended down:** 07:00 to 09:05 (13192.7 to 13148, 45 pips), 11:00 to 11:55 (19 pips), 15:15 to 16:20 (13168.6 to 13135.5, 33 pips) and 19:00 to 19:50 (16 pips).
- **Ranged or went sideways:** 00:00 to 07:00, 10:00 to 11:00, 12:00 to 15:15 (13149.7 to 13172.6) and 16:55 to 18:55 (13143.9 to 13157.5).
- **Turned:** 09:05 (13148, the London low and the 13150 round number), 16:20 (13135.5, under S2 13140.2), 19:50 (13135.6, the same low again) and, smaller, 13:10 (13172.6, under S1).

---

## 3. The analyser after 13:35

### A warning about the analyser's journal for 09:30 to 13:15

The journal (`data/analyser/GBPUSD/state_changes.jsonl`) has seven entries timed 09:30 to 13:15 that **the live bot never used**:
- 09:30 possible reversal up;
- 09:35 emerging trend up;
- then a run of emerging up and emerging down.

The 13:35 restart's replay, under the new code, wrote them:
- **They carry `hourly_position`**, which only the new code writes.
- **The live decision record has no state change between 08:35 and 14:50.** Its `"kind": "analyser state change"` lines are timed 00:05 … 08:05, 08:35, then 14:50, 15:00, 15:35, 15:50, 16:00, 16:15, 16:35, 18:55 and 19:25.
- **Every idea from 08:40 to 12:55 says `"state": "trend"`.** For example: `12:00 range trade buy ... "blocked_by": "the analyser's state is trend, which does not allow range trade"`.
- **The code explains it.** `analyser/market_state.py` `_write` appends every replayed change newer than the journal's last line, and the last live line was 08:35.

So under the old rules the live state was **trend down, slow grind from 08:35 until the restart**. The restart's replay of the morning under the new rules differs from the live record only up to 08:35: 55 differences, written to `replay_differences_2026-11-18.jsonl`, not into the journal. One of them is that **the new rules would have called the morning trend at 07:00** (`replayed, not in the live record ... 07:00 trend down slow grind ... the trend proof held in consolidation`), where the old rules called it at 08:35.

This affects how the journal reads, not how the bot traded. I have changed nothing.

### Every state change after 13:35 (live), beside price

The new code took over at 13:35 in **emerging trend down**, from its replay (13:15 `rejected at a level against the emerging up trend: closed 13166.1 below the reversal low 13167.2`). A replay of the day under the new rules gives exactly the same state changes after 13:35 (`replay_stage4_off.json`).

| Time | State | The analyser's reason (shortened) | What price did |
|---|---|---|---|
| (13:15) | emerging trend down | rejected at a level (closed 13166.1) | 13:35–14:45 sideways 13157–13171.5 |
| 14:50 | consolidation | `bands 12.7 pips wide ... middle band 0.1 pips/candle` | sideways 13161.6–13169.1 |
| 15:00 | ranging | `bands 12.9 pips wide ... and flat ... both bands reached, EMAs weaving` | sideways until 15:15, then edging down |
| 15:35 | emerging trend down | `broke out of the range: 2 closes below the band (last 13155.0, band 13155.8)` | the start of the 33-pip fall |
| 15:50 | **emerging trend up** | `rejected at a level against the emerging down trend: closed 13155.9 above the reversal high 13154.7` | a one-candle pause above 13150; the next candle fell to 13148.1 |
| 16:00 | consolidation | `the emerging up trend was cancelled: 2 closes in a row back below the round_number 13150.0` | still falling, 13143.8 |
| 16:15 | **trend down, strong push** | `the trend proof held in consolidation: a bounce failed under the 21 EMA and middle band, then a new low 13142.7` | the next candle made the day's low, 13135.5 |
| 16:35 | trend down, slow grind | `slow grind: 73% of the body size red, bands 2.9x as wide ...` | the low was already in; 16:40–16:55 rose to 13152.3 |
| 18:55 | consolidation | `the down trend ran out of steam: bands 9.5 pips wide ... no close outside the bands for 6 candles` | had been sideways 13143.9–13157.5 since 16:55 |
| 19:25 | **trend down, slow grind** | `the trend proof held in consolidation: a bounce failed ... then a new low 13138.9`; `the move started at the highest high 13154.9 of ... 18:55` | the low, 13135.6, came at 19:45–19:50; then up 14 pips to 13150.1 by 20:30 |

Hourly position (journal): **middle** until 15:50, **bottom edge** 16:00 to 16:35, then **middle** from 18:55.

### Did it call trends quickly?

**The break, yes. The trend, late.**
- **15:35:** it flagged the break two candles after the slide started, with price at 13155.0, 13.6 pips under the 15:05 high (13168.6). The breakout sell opened on it at 13152.9 (trade 4), the one good trend entry of the day.
- **16:15:** "trend" was decided on the 16:15 candle's close, at 16:20, with price at 13143.4: 25 pips into a 33-pip fall and **one candle before the low**. The two trend-group sells (16:20, 16:37) opened at 13141 and 13138, 3 to 5 pips from the low, and both were stopped at 16:58.
- **19:25:** "trend" was decided at 19:30, with price at 13139.8: 15 of the 19 pips of the fall from 13154.9 (18:55) to 13135.6 were done. The level reversal sell opened in that trend at 19:50, at 13135.7, 0.1 pip from the low, and was stopped at 20:19.

### Did it stay quiet when price went sideways?

**Mixed.**
- **Quiet and right:** 14:50 to 15:35, consolidation then ranging. The trend group opened nothing: the 15:20 EMA pullback and the 15:35 slow grind were blocked.
- **Quiet, but in the wrong state:** 13:35 to 14:50, emerging trend down for 75 minutes while price went sideways in 13157–13171.5. Nothing opened, because TREND_STILL_GOING blocked the 14:10 EMA pullback and the 14:25 slow grind (`no new low at least 5 pips below the previous low`).
- **Late:**
  - 16:55 to 18:55: two hours of sideways price still called **trend down, slow grind** until 18:55.
  - 20:00 to 20:30: the 14-pip rise from the double low was still called trend down.
  - No trend trade opened in either span. But these spans are why ANALYSER_GOVERNS_ALL blocked the reversal buys (step 4).

### Did it flip back and forth?

**Once, around 13150.** In 40 minutes it went:
- 15:35 emerging down;
- 15:50 emerging up (a rejection at 13150 that lasted one candle);
- 16:00 consolidation;
- 16:15 trend down.

Otherwise there was no flipping after 13:35: 10 changes in 7 hours. Under the old code there were 22 between 00:00 and 08:35.

---

## 4. Trades the new rules refused after 13:35

**There was no "same signal" refusal today.** `same signal already traded by` appears nowhere in today's `decisions.jsonl` or `orders.jsonl`, or in the log.

**Fourteen ideas after 13:35 were blocked with an "ANALYSER_GOVERNS_ALL" reason.** For eight of them it made no difference, because an older rule blocked them too:

| Time | Idea | Also blocked by (older rule) |
|---|---|---|
| 15:20 | EMA pullback sell 13158.6 | `the analyser's state is ranging, which does not allow EMA pullback`; TREND_STILL_GOING |
| 15:35 | slow grind sell 13156.4 | `the analyser's state is ranging, which does not allow slow grind` |
| 15:50 | range trade buy 13154.7 | `the analyser's state is emerging trend, which does not allow range trade` |
| 16:15 | slow grind sell 13144.8 | `the analyser's state is consolidation, which does not allow slow grind` |
| 18:35 | slow grind buy 13156.9 | `the trend is down: slow grind only in the trend's direction`; the hourly sell-off; TREND_STILL_GOING |
| 19:00 | EMA pullback sell 13149.7 | `the analyser's state is consolidation, which does not allow EMA pullback`; TREND_STILL_GOING |
| 19:20 | range trade buy 13143.5 | `the analyser's state is consolidation, which does not allow range trade` |
| 19:25 | slow grind sell 13139.9 | `the analyser's state is consolidation, which does not allow slow grind` |

**ANALYSER_GOVERNS_ALL alone blocked the other six: reversal buys against the down trend.**

| Time | Idea (decision record) | What it would have been: replay with ANALYSER_GOVERNS_ALL off (`replay_no_aga.json`) |
|---|---|---|
| 16:50 | level reversal buy 13145.1: `ANALYSER_GOVERNS_ALL: the trend is down: level reversal only in the trend's direction` | **Opens.** Stop 13130.1 (6 beyond the furthest point), take profit 20. The lowest price afterwards was 13143.9 (17:10). **Closed at 18:45 at 13157.3, `closed 15 minutes before big news` (FOMC minutes): +10.7.** |
| 17:00 | session sweep buy 13150.3: `ANALYSER_GOVERNS_ALL: the trend is down: session sweep only in the trend's direction` | **Opens.** The lowest price afterwards was 13143.9, 6.4 pips down, inside its 12-pip minimum stop. It never got 12 pips up, so it never trailed. **Closed at 18:45 at 13157.3 before the big news: +5.5.** |
| 17:25 | level reversal buy 13152.3 | **Refused anyway:** `level reversal already has 1 trade(s) open (at most 1)`, `same signal already traded by session sweep`. |
| 17:25 | session sweep buy 13151.2 | **Refused anyway:** `session sweep already has 1 buy trade(s) open (at most 1 each way)`, `once a day: a session sweep trade has already opened for London low 2026-11-18`. |
| 20:30 | level reversal buy 13148.4 | **Refused anyway:** `outside the trading hours 06:00 to 20:30 UK`. |
| 20:35 | session sweep buy 13149.1 | After 20:30: no new trades, so refused anyway. |

**What price did afterwards.** Price went sideways at 13143.9–13157.5 until 18:55. The two trades would have been closed at 18:45, near the top of that range. Then the FOMC minutes took price down to 13135.6 by 19:50, below both entries, and it came back to 13150 by 20:30.

**Did the blocks save us from losers, or stop winners?** **Today they stopped two trades that the replay closes in profit (+10.7 and +5.5) and saved no losers.** The two were buys at the bottom of the day's range, against a "trend down" that by then had stopped making new lows (step 3). This is one day, read from a replay.

---

## 5. Stage 4 replayed on today (branch feature/entries-exits, d7d2651)

### How it was run

`research/analyser_control_days.py` `run_day` was run from the week's open to the end of 18 November. It goes through the full wired path, in paper mode, on the bot's stored candles. It used today's live switches: the three analyser control switches on, HOURLY_READ on, TREND_STILL_GOING on, stops 12, take profit 100.
- **"All off":** the four Stage 4 switches off (`replay_stage4_off.json`).
- **"All on":** SCALE_OUT_REVERSAL, TRAIL_NO_LOSS, LR_ENTRY_NEAR_LEVEL and LEVEL_STOPS on (`replay_stage4_on.json`).

The analyser's state changes are identical in the two runs.

**Check against the live day.** The replay applies the new rules all day, while live switched at 13:35, so **only the afternoon can be compared with live trades.**
- **After 13:35 the "all off" replay matches live:** the 15:40 breakout sell at 13153.7 (live 15:44:06, same price), the 16:20 EMA pullback sell −12.0 and the 16:35 slow grind sell −15.0, with the same state changes.
- **The exception is the live 19:50 level reversal sell.** The replay does not produce it. Neither does a separate check of the strategies alone (`ideas_day`), which has no level reversal idea between 19:25 and 20:30.
- **Live, it came from the check on the forming candle** (`19:50:58 ... "live": true`). It is the **only live trade today with no candle-close record**: every other trade also has a `"already_sent_live": true` line at its candle's close (07:30, 09:30, 12:35, 15:40, 16:20, 16:35), and 19:50 has none.
- **So the finished 19:50 candle did not give the idea, live or in the replay.** The forming-candle check uses the Bollinger band as it stood after the 19:45 candle (`strategies/replay.py` `peek`: "the band as it stood at the last finished candle"). That may be why, but I have not proved it. It needs a look at the code; I haven't changed anything.

**Before 13:35, for background only** (not live trades, and not caused by Stage 4), the new rules all day would have:
- called the trend at 07:00, not 08:35;
- opened three trend trades the old rules did not: EMA pullback sells at 07:05 and 08:05, and a slow grind sell at 07:25 (+10.0);
- **blocked the 09:30 bounce buy**, which was +7.2 live (`ANALYSER_GOVERNS_ALL: the trend is down: Bollinger bounce only in the trend's direction`);
- opened a 09:35 bounce buy instead, after the "possible reversal up" state change, which never trailed and was stopped at −12.0.

### Every trade that changes ("all off" against "all on")

| Trade | All off | All on | Which switch and why |
|---|---|---|---|
| **12:35 EMA pullback sell 13156.2** (live: 12:37, −12.6) | Stopped at 13:05, **−12.0** (12-pip stop) | **Not stopped; still open at the end of the replay** (20:45 close 13148.5: about +7.7 on the chart price) | **LEVEL_STOPS.** Group `13166.9 to 13168 (new_york_session_high 13166.9, previous_day_low 13168, turning_low 13168)`; stop 13168 + 5 = 13173.0, plus the 1.5 spread = 13174.5 at IG, 16.8 pips. The 13:10 candle's buy-price high was 13174.1, **0.4 pips short**. |
| **16:20 EMA pullback sell 13140.8** (live: 16:20, −12.0) | Stopped at 16:55, **−12.0** | Stopped at 16:50, **−8.4** | **LEVEL_STOPS.** Group `13140.2 to 13142.7 (S2 13140.2, new_york_session_low 13142.7)`; stop 13147.7, plus 1.5 = 13149.2, 8.4 pips. |
| **19:50 level reversal sell 13135.7** (live, −11.3; **not in the replay, worked out by hand**) | the live trade: stop 13147.1, −11.3 | about **−10.9** | **LEVEL_STOPS:** group `13135.5 to 13140.2 (new_york_session_low 13135.5, S2 13140.2)` (the bot's own grouping at 19:20); stop 13140.2 + 5 + 1.5 = 13146.7, 10.9 pips. The 20:15 candle's buy-price high, 13147.6, reaches both stops. **LR_ENTRY_NEAR_LEVEL** lets it through: the entry is 4.5 pips from S2, within 6. **SCALE_OUT_REVERSAL** never comes into play: the trade was never in profit (best −1.3). |

**Changes only in the replay** (trades the old rules did not take live): the 07:05 and 08:05 EMA pullback sells get level stops.
- **07:05:** the group is `13176.7 to 13181.3`, so the stop is 13186.3 plus the spread.
- **08:05:** the group is `13168 to 13172.8`, so the stop is 13177.8 plus the spread.

Neither stop was reached; both trades are still open in both runs.

**No change:**
- **Asian range breakout 07:30:** TRAIL_NO_LOSS changes nothing, because the first trail move, 13177.0, was already on the profit side of the 13179.3 entry.
- **Bollinger bounce 09:35:** it never trailed.
- **Slow grind 07:25 and 16:35, and breakout 15:40:** LEVEL_STOPS does not cover these strategies, and they have no scale-out.

**LR_ENTRY_NEAR_LEVEL** adds refusals only to ideas that were refused anyway:
- 02:00, 02:25 and 04:30: outside trading hours;
- 17:25 and 20:30 level reversal buys: already blocked by ANALYSER_GOVERNS_ALL. For example, `the entry 13152.3 is 12.1 pips from the level it traded (S2 13140.2), more than 6`.

**SCALE_OUT_REVERSAL** changes nothing today: no level reversal opened in the replay, and the live one never went into profit.

---

## Files beside this report

- `trade_records_2026-11-18.jsonl`: the bot's trade records for the day (opened and closed).
- `decisions_2026-11-18.jsonl`: every decision record of the day: ideas, orders, trade manager and analyser state changes.
- `analyser_state_changes_2026-11-18.jsonl`: the analyser's journal for the day. The 09:30–13:15 lines came from the restart's replay (step 3).
- `candles_5m_2026-11-18.csv` and `candles_1h_2026-11-18.csv`: the bot's own candles, to 20:45.
- `prices_log_2026-11-18.txt`: the service log for the day.
- `replay_stage4_off.json`, `replay_stage4_on.json` and `replay_no_aga.json`: the paper replays. Each holds the state changes, trades, trade manager decisions, blocked ideas and refused orders. The `journal` lists cover the whole replayed week; only today's references matter.
