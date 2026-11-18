# Review of Tuesday 17 November 2026's trades (read-only)

AutoBot on 167.99.95.19, GBPUSD, IG demo. Written 18 November 2026. Nothing was changed, switched or restarted. No IG call was made, and IG's history allowance was not used. Everything here comes from the bot's own trade records, decision records, logs and its own 5-minute, hourly and daily candles. A few of the bot's own read-only commands were also run. Each of those commands states that it writes nothing (listed at the end).

---

## Summary

**What happened.** The bot closed 12 trades on the day: 3 won, 9 lost, **−86.8 pips (−£868)**. None was closed by you. This is the bot's own daily summary (`daily_summary_2026-11-17.json`: `"trades": 12, "wins": 3, "losses": 9, "pips": "-86.8"`, `"closed_by_owner": {"trades": 0 ...}`). Eleven of the trades opened on the 17th. One was an EMA pullback sell left open from Monday.

**What the market did.** For nine hours (about 06:00 to 15:25 UK) price moved sideways in a 23-pip box. The box ran from **13181.3 to 13204.4** and sat exactly between two levels already on the bot's list: Monday's London low 13182.1 and Monday's New York high 13205.2. The 13:30 US retail sales then pushed price below the box to 13172.8. Price turned at once and rose 55 pips to **13227.9 at 18:00**, just past the previous day's high (13224.5). After that it faded back to 13208 by 20:30.

**What went wrong, in order of how much it cost:**

1. **Exits that ignore structure (5 trades, cause D).** One 4-pip spike above the box top at 09:45 stopped three sells in 26 seconds. Their stops sat between the round number 13200 and the 13205.2 level, which is exactly where a range's stops get run. Price then fell 20 pips. Three other trades were 15 to 23 pips in profit and ended as losses or small gains, because their exits had no way to keep any of that profit.
2. **Afternoon entries with no sense of where they were (3 trades, cause C), plus one bounce sold into a breakout (cause B).** Two buys were taken 1 to 6 pips under the previous day's high, after 45 to 50 pips of rally, with 100-pip targets. A level reversal buy was entered 15 pips away from its level. From 16:35 the bot also held buys and sells at the same time.
3. **The market analyser misread the box.** It changed state 25 times between 06:00 and 20:30 and called "ranging" for only 50 of those 870 minutes. Every rejection at the pivot or at 13200 inside the box made it declare an "emerging trend" one way or the other. It was also late at both tops of the day (05:45 and 18:00). However, **8 of the 11 trades opened on the day came from strategies the analyser's state barely controls**: three bounces and one session sweep, which ignore it completely, and four level reversals, which open in every state except consolidation, in either direction. So the analyser was **not** the main cause of the losses. Its misreads mainly **blocked** range trades at the edges of the box (missed trades, step 4).
4. **One code fault (cause E).** When IG refused a trail move on the 10:05 bounce sell, the code kept re-sending the refused level 31 times and never sent the newer levels. The rule at the time said a later candle's level should replace it. This was fixed yesterday evening (commit c0ede45, live from the 20:46 restart).

**Main cause, in one sentence:** the bot's stops, targets and entries take no account of where the obvious levels are. Stops sat inside the stop-run zone above the box. Trades in profit had no way to bank it. Afternoon buys were taken right under the previous day's high. Meanwhile the analyser, which could have helped, controls only a minority of the strategies and misread the sideways session.

**Top 3 improvements (details and ranges in step 6; all three change your rules):**

1. **Place stops beyond the level group, not at a fixed distance** (exits). For the range trade, the level reversal and the EMA pullback, put the stop a set buffer beyond the nearest important level group. Today the stop is a fixed 12 pips, or 6 pips beyond the furthest point, wherever that happens to land. Yesterday, three stops at buy 13202.4, 13204.1 and 13205.1 sat between 13200 and 13205.2 and were taken by one candle whose buy high was 13205.9.
2. **Give the trades with fixed exits a way to bank profit, and stop the bounce trail's first move from locking in a loss** (exits). The level reversal, the EMA pullback and the range trade have no stage between the stop and the target. The bounce and session trail's first step can land on the losing side of the entry, and it can use a news candle's widened buy price. Yesterday the 10:05 bounce sell was 15.6 pips up when its first trail move locked a 3.3-pip loss.
3. **Let the analyser remember the range it is in** (analyser). While the hourly read says "ranging", a rejection at a level inside the hourly range should not start or flip an emerging trend; only the edges should. Ranging conditions should also be allowed to end an emerging trend. The hourly read said "ranging" correctly all through the session (range 13168 to 13204.4). The 5-minute state machine has no link to it.

---

## How to read this report

- **Times** are UK. In November UK time is GMT, which is the same as the UTC the bot stores, so no conversion was needed.
- **Prices** are the sell (bid) price, as on your chart, unless a field says "buy" or "offer". GBPUSD 13194.4 means 1.31944; one pip is 1.0 in these numbers.
- **Stops and take profits at IG** for a sell are on the buy price. A sell stop at 13202.4 is hit when the sell price is about 1.5 pips lower (13200.9), because the normal spread was 1.5. For a buy, the stop is on the sell price.
- **"Pierce", "rejection candle", "confirmation"** are the bot's own words from its records.
- **Most in my favour / most against me:** the bot records `best_pips` itself, from the live price it would close at. I also give the most for and against on the chart (sell) price, from the 5-minute candles **after** the opening candle up to the closing candle. The bot does not store the order of prices inside a candle. Each trade's opening candle is quoted separately, so you can see what may have happened before and after the entry within that candle.
- Raw files are beside this report. `trades_2026-11-17.csv` is the step 3 table. The other files are listed at the end.

---

## Checking the context you gave me

**1. HOURLY_READ was off for every trade.** It was off from 15 November. `docs/SETTINGS.md` says `| HOURLY_READ | ... **Owner's switch, off, 15 November 2026.** | off |`. The `.env` backup taken on 16 Nov at 23:00:20 (`/home/autobot/backups/planner-deploy-20261117/env.backup`) holds `HOURLY_READ=off`. The live `.env` was last written at **2026-11-17 20:36:29** and now holds `HOURLY_READ=on`. The service then restarted: `2026-11-17 20:46:05 GMT INFO autobot.prices.service: Received SIGTERM: stopping.` and `2026-11-17 20:46:38 GMT INFO autobot.trading: Trading ON: 0 open trade(s) taken over`.

Two facts show it was really off during the day. First, the 16:46:09 slow grind buy was **allowed** while the hourly read was "ranging", and the rules say "ranging" blocks the slow grind when the switch is on. Second, no decision record on the 17th mentions the hourly read until **21:00:00** (`"blocked_by": "the analyser's state is consolidation, which does not allow slow grind; the hourly chart is in a rally: slow grind only buys"`). **All 12 trades ran with it off.** (There was also a restart at 20:24:05. No trade opened between 20:24 and 20:46.)

**2. "A run of trades in consolidation" in the morning.** On the chart the morning was a consolidation or range. **No trade opened while the analyser itself said "consolidation"**, because the code blocks the level reversal and the range trade in that state. For example: `07:40:00 idea level reversal sell ... "blocked_by": "the analyser's state is consolidation, which does not allow level reversal"`. The morning trades opened while the analyser said "emerging trend down" (07:35 level reversal) and "ranging" (08:59 range trade). The bounce and the level reversal at 10:05 opened in "emerging trend down". Step 2 explains why the analyser kept saying "emerging trend" in a range.

**3. IG refused the trail moves on the 10:05 bounce sell.** Confirmed: 31 attempts between 13:50:02 and 14:06:00, all `ATTACHED_ORDER_LEVEL_ERROR`, all at 13181.6 (log and `orders.jsonl`). The fix was merged at 20:36:23 (`cc70dc5 Merge trail-fix ... nearest allowed level, 3 attempts`) and went live with the 20:46:05 restart. No bounce or session trade has opened since, so the fix has not yet run on a live trade.

**4. The new bounce rule.** All three bounce trades followed it exactly: a pierce of more than 3 pips, a red rejection candle, a confirmation close within 3 candles, and the open at the next candle's open. Step 3 quotes each one.

**5. The Structural Trade Planner** only began observing at 20:24, so it made no live recommendation during yesterday's trades. I ran its read-only `show` command (today's code, dd9d36d) at the three bounce moments. It would **not** have changed the 10:05 or 16:35 bounce sells, both losers: it recommended SELL with entry zones that both rejection candles reached. At 17:40 it gave **no recommendation**, so if it had been authorising bounces it would have refused the 17:45 sell, the only bounce winner. It covers bounces only, so it says nothing about the other nine trades. (Caveat: `show` prints the plan at a moment. It does not run the WAITING/ACTIVE lifecycle, and the authorisation step is not built.) Output: `planner_show_2026-11-17.txt`.

---

## Step 1: What the market did

### Levels for the day (the bot's own list, `levels_2026-11-17_0600.txt`)

The pivots come from Monday's daily candle, built by the bot from its own 5-minute candles, midnight to midnight UK, sell price: `Pivots from the daily candle Mon 16 Nov 00:00 GMT: sell H 13224.5 L 13175.2 C 13183.4`.

| Level | Price | Notes from the bot's level list |
|---|---|---|
| R3 | 13262.8 | |
| R2 | 13243.7 | grouped with turning highs 13243.2, 13240 |
| **Previous day high** | **13224.5** | same price as Monday's London high and an hourly turning high; group 13219.8–13224.5 |
| R1 | 13213.5 | group 13213.5–13218.5 (turning levels 13217.4, 13218.5) |
| Monday NY high / turning high | 13205.2 | **top of the morning box** |
| Round number | 13200 | |
| **Pivot** | **13194.4** | in the middle of the morning box |
| Monday London low / turning low | 13182.1 | **bottom of the morning box** |
| **Previous day low** | **13175.2** | with Monday NY low 13177.4 |
| S1 | 13164.2 | with the 01:00 turning low 13168 |
| S2 / S3 | 13145.1 / 13114.9 | not reached |

The day's range: `Built 1d Tue 17 Nov 00:00 GMT: ... sell O 13183.3 H 13227.9 L 13168 C 13204.4`. Price never reached R2 or S1.

**A data warning on the pivots.** The log says `Levels: The previous day's daily candle (Mon 16 Nov) is missing 2 five-minute candle(s); pivots use it as stored.` The missing candles are 22:55 and 23:00 on Monday, lost to Monday night's restarts (`Gap recorded: 5m Mon 16 Nov 22:55 GMT to Mon 16 Nov 23:05 GMT (2 candle(s))`). The close (23:55) and the high (13224.5) are not affected. The low would be wrong only if those 10 minutes went below 13175.2: the candle before closed at 13177.7 and the one after opened at 13182.2. I cannot check this against IG's own daily bar without using IG's history allowance, so I have not. If IG's low differs, the pivot would differ by a third of that difference.

### Hour by hour (the bot's hourly candles, sell price, `candles_1h_2026-11-17.csv`)

| Hour | O | H | L | C | What price did |
|---|---|---|---|---|---|
| 00:00 | 13183.3 | 13188.2 | 13178.5 | 13183.8 | Quiet. |
| 01:00 | 13183.9 | 13184.5 | **13168** | 13177.5 | **Swept the previous day's low** (13175.2) by 7.2 pips. The 01:25/01:30 candles made the low 13168. |
| 02:00 | 13177.1 | 13187.1 | 13174.6 | 13187.1 | Turned up from the sweep. |
| 03:00 | 13186.8 | 13196.7 | 13185.9 | 13194.1 | Steady climb. |
| 04:00 | 13193.6 | 13196 | 13189.1 | 13190.8 | Pause just under 13200. |
| 05:00 | 13190.9 | **13202.5** | 13190.1 | 13200.2 | Pushed into 13200; **Asian high 13202.5** (05:40 and 05:45 candles). **Top 1.** |
| 06:00 | 13200 | 13201.2 | 13187.5 | 13187.5 | Turned down; lost the pivot at 06:15–06:20. |
| 07:00 | 13188 | 13199.9 | 13181.3 | 13186 | **07:00 UK jobs data**: the 07:00 candle went both ways (13181.3 to 13199.9), then faded. |
| 08:00 | 13185.8 | 13199.3 | 13183.2 | 13190.8 | Inside the box; touched 13199.3 at 08:45. |
| 09:00 | 13191 | **13204.4** | 13187.7 | 13197.4 | 09:45 **spike to 13204.4** (just under Monday's NY high 13205.2), straight back down. |
| 10:00 | 13197.5 | 13197.5 | 13184.4 | 13186.5 | Fell 20 pips from the spike (09:55 to 10:15). |
| 11:00 | 13186.3 | 13193.4 | 13185.2 | 13190 | Narrow (8.2 pips). |
| 12:00 | 13189.9 | 13198.4 | 13187.4 | 13195.1 | Narrow. |
| 13:00 | 13195.5 | 13198.5 | **13172.8** | 13186.9 | **13:30 US retail sales**: fell to 13172.8 at 13:35, below the London low 13181.3 and 2.4 below the previous day's low. Reclaimed by 13:50. **Low 2.** |
| 14:00 | 13187 | 13201 | 13181.8 | 13191 | Back up to the top of the box (13201). |
| 15:00 | 13190.7 | 13210.4 | 13188.3 | 13203.4 | **Broke out of the box** from 15:25; first close above it 15:40 (13204.4). |
| 16:00 | 13203.6 | 13220.7 | 13202.3 | 13215.3 | Strong push through R1 (13213.5) to 13220.7 (16:20/16:25). |
| 17:00 | 13216.1 | 13226.3 | 13213.7 | 13224 | Higher, into the previous day's high zone; 17:15 high 13226.3. |
| 18:00 | 13224.1 | **13227.9** | 13218.2 | 13218.3 | **Top 2**: 3.4 pips past the previous day's high, then turned down. |
| 19:00 | 13218.2 | 13219.6 | 13212.6 | 13213.9 | Fading. |
| 20:00 | 13213.8 | 13215.3 | 13208.3 | 13209.5 | Back under R1. |
| 21:00–23:00 | | 13211.1 | 13198.5 | 13204.4 | Drifted to 13198.5 at 22:00–22:20 (around the rollover), closed 13204.4. |

**In short:**

- **Trended:** 01:30–05:45 up (34 pips from a previous-day-low sweep); 09:55–10:15 down (20 pips); 13:50–18:00 up (55 pips, from a sweep of the London low and the previous day's low after the US news).
- **Ranged / consolidated:** about 06:00 to 15:25, inside 13181.3–13204.4. Inside that, 10:15–13:25 was very narrow (13184.4–13198.5).
- **Turned:** 01:30 (13168, previous day's low swept), 05:45 (13202.5, round number and Asian high), 07:00 (news spike low 13181.3), 09:45 (13204.4, the box top), 13:35 (13172.8, London low and previous day's low swept), 18:00 (13227.9, previous day's high swept).

### Big news (bot's calendar `data/news/calendar.json`; "big" means big in your news table `config/news_table.toml`)

- **07:00 UK labour data.** Unemployment Rate `act 4.6 est 4.7 prev 4.7` (big in your table: rule `gbp_unemployment_rate`); Employment Change `act 156 est 136`. The 07:00 candle: `07:00 O 13188 H 13199.9 L 13181.3 C 13195.9`, spread 5.8 pips. Price spiked both ways, closed up, then faded back to 13184.9 by 07:50. No lasting move. The bot's expected news direction for the day was **none**, because the forecast equalled the previous figure (`day_directions` → `news=None`).
- **13:30 US retail sales.** `Retail Sales MoM act 0.2 est 0.2`, `Ex Autos act 0.6 est 0.4`, `Control Group act 0.6 est 0.4`. **Retail sales is "middle" in your table** (`[[middle]] rule = "retail_sales"`), so the bot did not treat it as big news: no no-trade window, and no closing 15 minutes before. Price: `13:30 O 13186.6 H 13186.6 L 13178.7 C 13179.4` (spread 6.5), `13:35 ... L 13172.8`, then up from 13:50.
- Smaller US releases followed (14:15 industrial production `act -0.4 est 0.1`; 15:00 NAHB `act 25 est 29`). The bot counts neither as big. Price was rising through both, and the break out of the box began at 15:25. I make no claim that they caused it.

---

## Step 2: What the analyser thought

Source: `analyser_state_changes_2026-11-17.jsonl` (each line has the old state, new state, direction and evidence) and the matching `autobot.analyser: ... Market state:` log lines. Each change is decided on a finished 5-minute candle; the time below is that candle's start, and the log line comes 5 minutes later. On the 17th there were **39 state changes; 25 of them between 06:00 and 20:30.**

Time spent in each state, 06:00–20:30 (870 minutes): **emerging trend down 320 min, trend up 230, emerging trend up 140, consolidation 130, ranging 50.**

The verdicts compare each change with step 1. **Right** = price did what the state says. **Late** = right, but after the move had happened. **Wrong** = price did not do it.

| Time | Old → new | Evidence the analyser gave (quoted) | Verdict |
|---|---|---|---|
| 00:05 | consolidation → ranging | `bands 10.3 pips wide ... both bands reached, EMAs weaving` | Right (quiet Asia range) |
| 00:45 | ranging → consolidation | `bands 7.2 pips wide ... average body 1.3 pips` | Right |
| 01:05 | consolidation → emerging down | `broke out of the consolidation: close 13178.3 below the lower band 13178.4` | Right (to 13168) |
| 01:35 | emerging down → consolidation | `2 closes in a row back inside the Bollinger bands ... (last 13172.4)` | Right (the low was in at 01:30) |
| 02:10 | consolidation → emerging up | `rejected at a level: closed 13180.8 above the reversal high 13177.5` / `rejected at the previous_day_low 13175.2` | **Right**: the previous-day-low sweep |
| 03:30 | emerging up → trend up (slow grind) | `a bounce failed under the 21 EMA and middle band, then a new high 13196.7 on the upper band 13196.1; EMAs 7/13/21 stacked up for 13 candles` | Right |
| 06:25 | trend up → ranging | `the up trend turned into a range: bands 13.6 pips wide` | **Late**: the top was 05:40/05:45 (13202.5); price was already below the pivot at 06:20 |
| 06:35 | ranging → emerging up | `rejected at a level: closed 13193.5 above the reversal high 13193.1` / `rejected at the pivot 13194.4` | **Wrong**: middle of the box |
| 06:45 | emerging up → ranging | `2 closes in a row back below the pivot 13194.4 ... (last 13190.7)` | Right (undoing 06:35) |
| 06:55 | ranging → emerging down | `rejected at a level: closed 13187.5 below the reversal low 13189.7` / `rejected at the pivot 13194.4` | Mixed: the 07:00 news candle went to 13181.3, then back to 13199.9 |
| 07:35 | emerging down → consolidation | `bands 9.6 pips wide ... average body 2.6 pips` | Right |
| 07:50 | consolidation → emerging down | `broke out of the consolidation: close 13184.9 below the lower band 13186.4` | **Wrong**: low 13183.2 at 08:00, then back up to 13199.3 |
| 08:10 | emerging down → consolidation | `2 closes in a row back inside the Bollinger bands after the breakout (last 13188.4)` | Right (undoing 07:50) |
| 08:35 | consolidation → ranging | `bands 14.6 pips wide ... both bands reached, EMAs weaving, 100 EMA moved 0.0 pips` | **Right** |
| 08:55 | ranging → emerging down | `rejected at a level: closed 13190.8 below the reversal low 13193.6` / `rejected at the pivot 13194.4` | **Wrong**: sideways 13187.7–13199, then the spike to 13204.4 |
| 09:30 | emerging down → emerging up | `rejected at a level against the emerging down trend: closed 13194.9 above the reversal high 13194.7` / `rejected at the pivot 13194.4` | **Wrong**: one spike to 13204.4, then 20 pips down |
| 10:00 | emerging up → emerging down | `rejected at a level against the emerging up trend: closed 13190.5 below the reversal low 13195.2` / `rejected at the turning_high 13202.5` | Right for 15 minutes (to 13184.4 at 10:15), then out of date until 11:35 |
| 11:35 | emerging down → consolidation | `bands 9.0 pips wide ... average body 1.3 pips` | Right |
| 12:25 / 12:35 | consolidation → ranging → consolidation | `bands 8.0 pips wide ...` / `bands 6.9 pips wide ...` | Right (both fit the quiet spell) |
| 12:40 | consolidation → emerging up | `broke out of the consolidation: close 13196.1 above the upper band 13194.9` | **Wrong**: peaked at 13198.5, then down |
| 12:55 | emerging up → consolidation | `2 closes in a row back inside the Bollinger bands after the breakout (last 13195.1)` | Right (undoing 12:40) |
| 13:10 | consolidation → emerging down | `rejected at a level: closed 13189.9 below the reversal low 13190.6` / `rejected at the round_number 13200.0` | Right in outcome (13172.8 after the 13:30 news), on thin evidence (the high was 13198.5) |
| 13:50 | emerging down → emerging up | `rejected at a level against the emerging down trend: closed 13183.5 above the reversal high 13180.3` / `rejected at the previous_day_low 13175.2` | **Right**: the start of the 55-pip rally |
| 14:45 | emerging up → emerging down | `rejected at a level against the emerging up trend: closed 13192.5 below the reversal low 13194` / `rejected at the round_number 13200.0` | **Wrong**: dipped only to 13188.3, then broke out upwards |
| 15:40 | emerging down → emerging up | `rejected at a level against the emerging down trend: closed 13204.4 above the reversal high 13203.2` / `rejected at the pivot 13194.4` | Right (the break out of the box) |
| 16:10 | emerging up → trend up (slow grind) | `the rejection became a trend: ... a new high 13212.0 on the upper band 13210.6; EMAs 7/13/21 stacked up for 10 candles` | Right |
| 16:25 | trend up → strong push | `strong push: 83% of the body size green, bands 2.3x as wide as 12 candles ago, 7/21 EMAs 8.3 pips apart, 3 closes on the band` | Right |
| 16:45 | strong push → slow grind | `slow grind: 51% of the body size green ...` | Right |
| 19:35 | trend up → consolidation | `the up trend ran out of steam: bands 11.4 pips wide` | **Late**: the top was 18:00 (13227.9) at the previous day's high; lower highs from 18:00 |
| 19:55 | consolidation → emerging down | `rejected at a level: closed 13213.9 below the reversal low 13215.6` / `rejected at the turning_low 13219.8` | Right (13208.3 by 20:15) |
| 20:55 → 23:50 | 7 more changes | consolidation / emerging up / emerging down / consolidation / emerging up / emerging down / ranging / emerging up | Outside trading hours; the same flip-flopping in a 10-pip drift |

**Overall:** the analyser read the Asian session and the afternoon breakout well. **It misread the 9-hour box.** Between 06:25 and 15:40 it changed state 20 times and called "emerging trend" (down or up) for most of it. **It was late at both tops** (05:45 and 18:00). The 07:50 and 12:40 changes were false breakouts out of narrow consolidations.

### Why, from the code (`analyser/states.py`, settings in `config/settings.toml [market_states]`)

**W1. Any rejection at a "strong" level starts an emerging trend, even in the middle of a range** (06:35, 06:55, 08:55, 13:10). From ranging or consolidation, the first confirmed rejection at a strong level starts an emerging trend at once:

```python
# analyser/states.py:373-374
for e, stp in important_rejection(CONFIRMATION):
    return self._start_emerging(f, _move(e.direction), f"rejected at a level: {e.note}", stp)
```

`strong_level_types = ["pivot", "R1", ..., "round_number", "previous_day_high", "previous_day_low"]`. Yesterday the pivot 13194.4 sat in the **middle** of the box and 13200 near its top, so price "rejected" them again and again. Nothing in the code asks whether price is inside an established range, or how much room there is to the range edge. This follows your design (2.5: "moves to emerging trend at the moment the level is rejected"); it was built for a trend starting from a level, not for a level in the middle of a range.

**W2. In an emerging trend, a rejection the other way flips the direction at once** (09:30, 10:00, 13:50, 14:45, 15:40):

```python
# analyser/states.py:309-314
if st == EMERGING:
    for e, stp in important_rejection(CONFIRMATION):
        if _move(e.direction) == _opposite(d):
            return self._start_emerging(f, _move(e.direction), f"rejected at a level against the emerging {d} trend: {e.note}", stp)
```

In a box, the top and bottom keep rejecting price, so the direction flips with each swing.

**W3. An emerging trend cannot end in "ranging"** (10:00 to 11:35: called "emerging down" while price went sideways 13184.4–13195.8). By your rule of 7 November, an emerging trend that is not cancelled, proven or replaced ends only in consolidation, or by fading after 24 candles (2 hours):

```python
# analyser/states.py:345-350
if st == EMERGING:
    # ... an emerging trend ends only in consolidation (owner's rule, 7 November 2026)
    c_ok, c_why = self.consolidation(f)
    return self._persist(f, (CONSOLIDATION, NONE, ...) if c_ok else None)
```

**W4. Late at the tops: a "possible reversal" needs a 30-pip trend first** (06:25 and 19:35). A trend ends on two closes past the 5-minute 100 EMA, on ranging or consolidation holding for 2 candles, or on fading after 24 candles with no new high. A rejection at a level can only make it a "possible reversal" if the trend has moved at least `possible_reversal.min_trend_move_pips = 30` (`analyser/states.py:319`). The morning trend started at 13180.8 (02:10) and peaked at 13202.5: 21.7 pips. The afternoon trend started at 13204.4 (15:40) and peaked at 13227.9: 23.5 pips. Neither could become a possible reversal, however clear the rejection at 13200 / the Asian high, or at the previous day's high.

**W5. False breakouts from narrow consolidations** (07:50, 12:40). From consolidation, **one** close beyond a band is a breakout (`analyser/states.py:375-381`). In a quiet box the bands are narrow ("bands 9.6 pips wide" at 07:35; "6.9 pips wide" at 12:35), so a 1–2 pip poke is enough.

**W6. What it cannot see.** The state machine uses only 5-minute candles. It is not told about:

- **The hourly read.** It said "ranging" from Monday 21:00 until 17:00 on the 17th, with the hourly range 13168 (later 13172.8) to 13204.4 (`hourly_read_and_ema_pullback_step0_2026-11-17.txt`). That is exactly the box. HOURLY_READ was off, and when on it only gates three trend strategies; it never changes the analyser's own state.
- **The higher timeframes.** At 06:03 the hourly 100 EMA was 13242.0 and the 200 EMA 13290.5 (`python -m analyser 2026-11-17T06:03:00Z`), about 40 and 90 pips above price. The planner read the 4-hour chart as `BEARISH ... lower highs and lower lows`, with the warning `the daily structure (up) is against the 4-hour structure (down)`.
- **Exhaustion at levels outside its "strong" list.** Monday's session highs and lows and the hourly turning levels can start a trend only if they line up with a strong level (`strong_levels`, `analyser/states.py:412-426`).

**The hourly read itself (switched off):** right about the box all session. It turned to "rally" at 17:00, after the 16:00 hour closed at 13215.3 (`4.9 pips above the high 13210.4 of the 12 hourly candles before it`). That was about 90 minutes after the break began at 15:25 and 40 pips into the 55-pip rally, as its design (an hourly close) means. It then **stayed "rally" through the whole 18:00–22:00 fade**, because only an hourly close 3 pips below 13172.8, or 12 hours without a new break, can change it.

---

## Step 3: Every trade

Common facts: size £10 a pip; no trade was closed by you (`"closed_by": "bot"` on all 12 closes). **HOURLY_READ was off for all 12**; the "hourly read at open" column shows what it **would** have said, from `analyser/hourly_read.py` on the bot's own hourly candles. The pivot and 100 EMA position is quoted from each trade's own `"allowed at entry: ..."` step. Full table: `trades_2026-11-17.csv`.

| # | Open → close (UK) | Strategy, direction | Open (IG) | Stop | Take profit | Close | Pips | How it closed | Analyser at open | Hourly read at open (off) | vs pivot / 5m 100 EMA | Bot's best | Chart most for / against | Cause |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 | **Mon 16** 14:26:00 → 09:48:55 | EMA pullback sell | 13192.1 | 13204.1 | 13162.1 (30) | 13204.1 | −12.0 | stop at IG | emerging trend down | sell-off | below 13211.7 (Mon pivot) / below 13198.9 | 22.6 | 24.1 / 12.3 | **D** |
| T2 | 06:03:34 → 06:45:01 | Level reversal sell | 13198.7 | 13208.5 | 13178.7 (20) | 13195.7 | +3.0 | forced: 15 min before big news | trend up, slow grind | ranging | above 13194.4 / above 13188.5 | 7.4 | 9.0 / −0.6 | **F** |
| T3 | 07:35:11 → 09:49:00 | Level reversal sell | 13191.7 | 13205.1 | 13171.7 (20) | 13205.1 | −13.4 | stop at IG | emerging trend down | ranging | below / above 13190.0 | 7.0 | 8.3 / 12.9 | **D** |
| T4 | 08:59:02 → 09:48:34 | Range trade sell | 13190.4 | 13202.4 | 13090.4 (100, safety net) | 13202.4 | −12.0 | stop at IG | ranging | ranging | below / above 13190.2 | 1.2 | 2.7 / 14.0 | **D** |
| T5 | 10:05:01 → 14:06:00 | Bollinger bounce sell | 13189.9 | 13201.9, trailed to 13193.2 | 13089.9 (100) | 13193.2 | −3.3 | trailed stop at IG | emerging trend down | ranging | below / below 13191.2 | 15.6 | 17.3 / 8.4 | **E** |
| T6 | 10:05:02 → 15:45:18 | Level reversal sell | 13189.5 | 13210.3 (20.8) | 13169.5 (20) | 13210.3 | −20.8 | stop at IG | emerging trend down | ranging | below / below 13191.2 | 15.2 | 16.8 / 20.8 | **D** |
| T7 | 14:00:02 → 14:37:44 | Session sweep buy | 13188.8 | 13171.7 (17.1), trailed to 13193.9 | 13288.8 (100) | 13193.9 | +5.1 | trailed stop at IG | emerging trend up | ranging | below / below 13189.7 | 12.2 | 13.6 / −2.3 | **D** |
| T8 | 16:22:53 → 20:30:03 | Level reversal buy | 13218.8 | 13196.3 (22.5) | 13238.8 (20) | 13209.6 | −9.2 | forced: 20:30 close | trend up, slow grind | ranging | above / above 13193.5 | 9.1 | 10.6 / 9.0 | **C** |
| T9 | 16:35:01 → 17:16:22 | Bollinger bounce sell | 13215.1 | 13227.1 | 13115.1 (100) | 13227.1 | −12.0 | stop at IG | **trend up, strong push** | ranging | above / above 13194.9 | 1.7 | 3.2 / 11.2 | **B** |
| T10 | 16:46:09 → 20:30:04 | Slow grind buy | 13220.0 | 13205.0 (15) | 13320.0 (100, big-news day) | 13209.6 | −10.4 | forced: 20:30 close | trend up, strong push | **ranging (would have blocked it)** | above / above 13195.8 | 7.9 | 9.4 / 10.2 | **C** |
| T11 | 17:16:00 → 19:59:26 | EMA pullback buy | 13225.1 | 13213.1 | 13325.1 (100, big-news day) | 13213.1 | −12.0 | stop at IG | trend up, slow grind | rally (would allow) | above / above 13198.1 | 2.8 | 4.3 / 11.0 | **C** |
| T12 | 17:45:03 → 20:30:05 | Bollinger bounce sell | 13221.1 | 13233.1 | 13121.1 (100) | 13210.9 | +10.2 | forced: 20:30 close | trend up, slow grind | rally | above / above 13200.9 | 11.3 | 12.9 / 6.7 | **F** |

**Causes:** A analyser wrong: 0. B strategy wrong for the market: 1. C entry wrong: 3. D exit wrong: 5. E code broke its rule: 1. F fine: 2.

### T1. EMA pullback sell, opened Monday 16 Nov 14:26 (carried over), −12.0. Cause D (exit)

- Opened during Monday's hourly sell-off: `"step 0, hourly 8/13/20 EMAs in order, falling ..."`, `"direction rule sell side (price 13192.1 is below the pivot 13211.7 and below the 5m 100 EMA 13198.9)"`. Take profit 30 pips (13162.1).
- It was **22.6 pips up** at best (`"best_pips": "22.6"`). The 01:25/01:30 candles reached 13168 sell, about 13169.5 buy, 7.4 pips short of the target. It was then held through the Asian rally, as the EMA pullback rules allow (held overnight, no trail). It was stopped at `"closed_utc": "2026-11-17T09:48:55Z", "close_price": "13204.1"` by the 09:45 spike (`09:45 O 13194.9 H 13204.4 L 13193.7 C 13199.9`, buy high about 13205.9).
- **Hour after the close:** `09:50-10:50: H 13204.3 L 13184.4`, so the sell idea came good again within 25 minutes.
- **Why D:** a good trade that was over 20 pips up and had no exit that could keep any of it. It was then stopped by a spike into the level group above the box, where its stop sat (buy 13204.1, about 13202.6 on the chart, under 13205.2).

### T2. Level reversal sell 06:03, +3.0. Cause F (fine)

- Rule steps quoted: `"05:35 ... pierce 13198.9: high 13198.9 reached upper Bollinger band 13197.6, round_number 13200 (within 1.1 pips)"`, `"05:50 ... reversal candle O 13202.3 H 13202.4 L 13200.9 C 13201.3"`, `"05:55 ... confirmation 13200.2"`, `"06:00 ... trigger 13198.8"`. Side check: `"the piercing candle opened at 13197.7, below it: price rose into it"`. Allowance: `"furthest high 13202.5 ... 2.5 pips past the level (allowance 5)"`. Stop `"6 pips above the furthest point"`. **The code followed the rules.**
- The analyser said "trend up, slow grind" (it was late; see W4). The level reversal may trade against it by your rule.
- Closed by the news rule: `"closed 15 minutes before big news (IG's level)"`, +3.0, best 7.4. Price did fall later (`06:50-07:50: H 13199.9 L 13181.3`), but the take profit (13178.7 on the buy price) was not reached: the lowest buy price in that hour was 13187.2 (07:00 candle).
- **Why F:** right place (13200 and the Asian high, the day's first top), right direction, closed by a rule doing its job before the 07:00 release.

### T3. Level reversal sell 07:35, −13.4. Cause D (exit)

- Steps: `"07:20 ... pierce 13197.3: high 13197.3 reached pivot 13194.4, london_session_high 13199.9 (within 2.6 pips), round_number 13200 (within 2.7 pips) ... levels line up; counts"`, `"07:25 ... reversal candle O 13197 H 13198.9 L 13193.5 C 13193.5"`, `"07:30 ... confirmation 13192.2"`, `"07:35 ... trigger 13192"`, `"stop 13204.9: 6 pips above the furthest point"`. Rules followed. Opened 35 minutes after the 07:00 release, outside the 30-minute window.
- Best +7.0. Stopped at `13205.1` at 09:49:00 by the same 09:45 candle (sell high 13204.4, buy about 13205.9: **0.8 pips** past the stop).
- **Hour after:** `09:50-10:50: H 13204.3 L 13184.4`.
- **Why D:** right idea (selling the top of the box) and the move came. The stop, 6 pips beyond the furthest point, landed between 13200 and Monday's New York high 13205.2. That is the stop-run zone of the box.

### T4. Range trade sell 08:59, −12.0. Cause D (exit)

- Steps: `"08:45 ... range sell pierce 13199.3: high 13199.3 reached upper Bollinger band 13198.4"`, `"08:50 ... rejection candle O 13193.8 H 13195.4 L 13190.8 C 13193.7"` (red by 0.1 pip), `"08:55 ... trigger 13190.8"`. Rules 3.4 followed. Analyser: ranging. **Right strategy for that market.**
- Exit check: the rule closes in full at the opposite band. The 5-minute lower band was 13183.7–13183.9 between 09:05 and 09:30 (`python -m analyser`: `Bollinger 13183.9 / 13190.8 / 13197.8` at 09:00, `13183.7 / 13191.3 / 13198.8` at 09:25), and the lowest price after the entry was 13187.7. The band was never reached, so the code was right not to close.
- Stopped at 13202.4 (buy) at 09:48:34, with best +1.2. **Hour after:** down to 13184.4.
- **Why D:** the fixed 12-pip stop at buy 13202.4 is **about 13200.9 on the chart, 0.9 pips above 13200 and under both the Asian high 13202.5 and 13205.2**. The trade's own target, the opposite band about 6.7 pips away, was smaller than its 12-pip risk. Both come from fixed distances that ignore where the box edges were.

### T5. Bollinger bounce sell 10:05, −3.3. Cause E (the code broke its own rule), with an exit design point

- Entry, rules followed: `"09:55 pierce and rejection candle: its high 13203.6 went 3.6 pips above the upper hourly Bollinger band (13200.0 at that moment), and it closed red (13202.8 to 13197.4)"`, `"10:00 confirmation candle: closed at 13190.5, below the rejection candle's low (13195.2)"`, `"10:05 opens at this candle's open, 13190.1"`.
- Best **+15.6** (13:35, after the 13:30 news). The trail started at 13:40:02: `"15.6 pips up at best (the trail from 12): the stop moves to 13193.2, beyond the last 3 candles"`. **That level is 3.3 pips on the losing side of the 13189.9 entry.** The last three candles were `13:25:13192.4 13:30:13193.1 13:35:13181.2` (buy highs, `trail_refusal_20261117/attempts.csv`). The 13:30 candle's buy high of 13193.1 is its sell high 13186.6 plus a **6.5-pip news spread**. Even without that candle, 13:25's buy high of 13192.4 would also have put the first step above the entry.
- 13:50:02 onwards: the trail asked for 13181.6 and IG refused it 31 times (`ATTACHED_ORDER_LEVEL_ERROR`) until the trade was stopped at 13193.2 at 14:06:00. The buy price at 13:50:02 was 13180.2, only 1.4 pips below 13181.6 (`attempts.csv`: `dist_from_buy_open 1.4`).
- **The rule at the time** (`git show 233d054:docs/DESIGN.md`, section 4): *"the move is tried again every `orders.close_retry_seconds` until IG confirms it **or a later candle gives a newer one**."* **The code at the time** compared each newer level with the refused one, not with the stop IG held:

  ```python
  # trade_manager/manager.py before c0ede45
  now = t.trail_want if t.trail_want is not None else t.stop_level
  if (want < now) if sell else (want > now):
      t.trail_want = want
  ```

  The newer levels (13185.1 after the 13:50 candle, 13189.8 after 13:55, 13192.8 after 14:00; the "rule level" column in `trail_refusal_20261117/table.md`) were all higher than the refused 13181.6, so none of them replaced it. **That broke the rule.** It was fixed in c0ede45 (`now = t.stop_level`, "a newer level replaces one still waiting"), live from 20:46:05.
- Would the newer levels have been accepted? I can't tell. Each was within 0.4 to 1.3 pips of the buy price at that candle's open, and IG's minimum stop distance was not recorded that day (reading it before a move only came in with the fix). With the fix's "nearest level IG allows", the stop would have gone to the buy price plus IG's minimum. The 13:50 candle's buy price rose from 13180.2 to 13185.0, so that stop would have been hit in the 13:50 candle unless IG's minimum was more than 4.8 pips. I cannot give the exact result without that minimum.
- **Why E and not D:** the refused-level code is a proven rule break. The design point (the first trail step can land on the losing side, and news-spread candles count) is suggestion X3 in step 6.

### T6. Level reversal sell 10:05, −20.8. Cause D (exit)

- Same rejection as T5, from a different strategy: `"09:40 ... pierce 13197.8: high 13197.8 reached pivot 13194.4, london_session_high 13199.9 (within 2.1 pips), round_number 13200 (within 2.2 pips); in a reversal watch window"`, `"09:55 ... reversal candle O 13202.8 H 13203.6 L 13195.2 C 13197.4"`, `"10:00 ... confirmation 13190.5"`, `"10:05 ... trigger 13189.8"`, `"round number 13200: furthest high 13204.4 ... 4.4 pips past the level (allowance 5)"`, `"stop 13210.4: 6 pips above the furthest point"`. Rules followed.
- So the bot had **two sells on one signal** (T5 and T6), 1 second apart.
- The risk was **20.8 pips against a 20-pip target**, because the entry came 14.6 pips below the furthest point.
- Best **+15.2**. The low of 13172.8 (13:35) was 4.8 pips short of the target on the sell price (the target needed about 13168.0 sell for a 13169.5 buy). It was not closed before the 13:30 release, which is "middle" in your table. With no trail or break-even, it rode the 55-pip rally back up and was stopped at 15:45:18 (`15:45 O 13204.5 H 13210.4`).
- **Hour after:** `15:50-16:50: H 13220.7 L 13202.1`, so the stop was right to go at that point.
- **Why D:** a trade 15 pips up turned into a 20.8-pip loss. Its exits are a fixed 20-pip target and a stop that never moves.

### T7. Session sweep buy 14:00, +5.1. Cause D (exit too early)

- Steps: `"13:50 swept the London low 13181.3, price went 8.5 pips below it (furthest 13172.8), and this candle closed back above it at 13183.5"`, `"13:55 confirmation candle, closed at 13186.9, above the rejection candle's high (13183.5)"`, `"14:00 opens at this candle's open, 13187.4 (sell price); stop 13171.8, 15.6 pips (at least 12; 1 beyond the furthest point 13172.8)"`. Rules followed.
- This was the **right trade at the right place**: it bought the second turning point of the day, which also swept the previous day's low.
- The trail started at 14:35:02 (`"12.2 pips up at best ... the stop moves to 13193.9"`). The 14:35 candle dipped to 13192.6 and the trade was stopped at 14:37:44, +5.1.
- **After:** `14:40-15:40: H 13203.2`, and price reached 13220.7 by 16:25 and 13227.9 by 18:00.
- The opening candle `14:00 O 13187 H 13191.4 L 13181.8` went 5.6 pips below the entry. The bot does not store whether that came before or after 14:00:02.
- **Why D:** the three-candle trail closed the trade 37 minutes into a 40-pip move. It behaves like a 5-minute scalp while the setup is a session-level reversal.

### T8. Level reversal buy 16:22, −9.2. Cause C (entry)

- Steps: `"16:05 ... pierce 13202.3: low 13202.3 reached round_number 13200 (within 2.3 pips), turning_high 13202.5, london_session_high 13204.4, turning_high 13204.4, new_york_session_high 13205.2"`, `"16:10 ... reversal candle O 13207.6 H 13212 L 13207.1 C 13210.6"`, `"16:15 ... confirmation 13214.7"`, `"16:20 ... trigger 13217.2"`, `"stop 13196.3: 6 pips below the furthest point"`. Rules followed.
- **The entry was 15 pips above the level it traded** (13202.3 to 13217.2), after the move away from the level had happened. The stop was 22.5 pips and the target 20, so the bot risked more than it could win. Best +9.1 (18:00). Closed at the 20:30 close, −9.2.
- It was a buy while T9 (a sell) opened 12 minutes later.
- **Why C:** right idea (the old box top 13200–13205 turning into support), bad timing and place: the confirm-then-break sequence put the entry 15 pips from the level.

### T9. Bollinger bounce sell 16:35, −12.0. Cause B (strategy wrong for the market)

- Steps, rules followed: `"16:25 pierce and rejection candle: its high 13220.7 went 11.0 pips above the upper hourly Bollinger band (13209.7 at that moment), and it closed red (13219.9 to 13216.7)"`, `"16:30 confirmation candle: closed at 13215.1, below the rejection candle's low (13216.1)"`, `"16:35 opens at this candle's open"`.
- **The analyser was right:** `"market_state": "trend up, strong push"` (16:25: `83% of the body size green, bands 2.3x as wide as 12 candles ago`). The bounce opens "without hindrance" by your rule of 15 November, so the state did not matter.
- An 11-pip pierce of the hourly band in a strong push was the breakout of the 9-hour box (hourly range top 13210.4), not an overstretch. Stopped at 17:16:22 (`17:15 ... H 13226.3`). **Hour after:** `17:20-18:20: H 13227.9`.
- **Why B:** this kind of trade (fading the hourly band) does not work as a box breaks out in a strong push.

### T10. Slow grind buy 16:46, −10.4. Cause C (entry)

- Steps: `"16:25: the last high made: 13220.7"`, `"16:30 to 16:40: a pause: 3 candles in a row without a new high, closing above the 21 EMA; its highest point 13218.4"`, `"16:45: price broke above it"`. Rules followed. Take profit 100 (`"take_profit_kind": "100 for a big-news day"`, from the 07:00 UK release nearly 10 hours earlier).
- **The entry was 6.1 pips under the previous day's high (13224.5)**, about 46 pips above the 13:35 low, with a 100-pip target. Best +7.9 at 18:00 (13227.9), then the fade. The 15/10 profit lock never started. Closed at 20:30, −10.4.
- **The hourly read would have blocked it:** at 16:46 it said `hourly ranging ... the hourly range 13172.8 to 13210.4`. This is the only trade yesterday that HOURLY_READ would have changed.
- **Why C:** a late trend entry into a known level group, with no allowance for that level.

### T11. EMA pullback buy 17:16, −12.0. Cause C (entry; close to F)

- Steps: `"step 0, hourly 8/13/20 EMAs in order, rising; slopes 2.66, 1.80, 1.18 pips/hour"`, `"17:00: price dropped to the 5-minute 8 EMA 13214.6 (low 13213.7); closed 13217.5, above the 21 EMA 13209.8"`, `"entry 13223.3: 3 pips above the highest high of the 5 candles before the touch candle"`, `"17:15: price reached the entry 13223.3"`. Rules followed. The hourly read said "rally", so it would have been allowed.
- **The entry, 13223.3, was 1.2 pips under the previous day's high.** Best +2.8. The top came at 18:00 (13227.9) and the stop was hit at 19:59:26 (the `19:55 ... L 13212.6` candle). **Hour after:** `20:00-21:00: L 13208.3`.
- **Why C:** a reasonable trend pullback, but bought just under the day's biggest overhead level after a 50-pip run, with a 100-pip target that ignored it.

### T12. Bollinger bounce sell 17:45, +10.2. Cause F (fine)

- Steps, rules followed: `"17:35 pierce and rejection candle: its high 13224.1 went 9.3 pips above the upper hourly Bollinger band (13214.8 at that moment), and it closed red (13222.8 to 13222)"`, `"17:40 confirmation candle: closed at 13221.3, below the rejection candle's low (13221.9)"`, `"17:45 opens at this candle's open, 13221.2"`.
- Sold the previous-day-high zone. Best +11.3 (just short of the 12-pip trail start), closed at 20:30 at +10.2. Four later bounce sells (18:30–18:45) were refused: `"Bollinger bounce already has 1 sell trade(s) open (at most 1 each way)"`.

### The bot held both directions at once

From 16:35 to 17:16 it held one sell (T9) and two buys (T8, T10). From 17:45 to 19:59 it held one sell (T12) and three buys (T8, T10, T11). This follows your rule (`"When it opens it closes nothing else: trades open the other way, whatever their strategy, run on their own exits"`). But while both sides are open, the account's net position is close to flat and each side pays the spread.

---

## Step 4: Missed trades

| Move (step 1) | What the bot did | Why it missed it (evidence) |
|---|---|---|
| **Edges of the 9-hour box**: sells at 13199–13204, buys at 13181–13186 | Took the 08:59 range sell (T4). Nothing else from the range trade. | **The analyser was not in "ranging"**, so range trade ideas were blocked: `08:10 buy 13186.6 "the analyser's state is emerging trend, which does not allow range trade"`, `08:15 buy 13189.4 "... consolidation ..."`, `10:00 sell 13195.2 "... emerging trend ..."`, `10:05 sell 13189.8 "... emerging trend ..."`, `10:25 buy 13190.3 "... emerging trend ..."`, `13:25 buy 13188.2 "... emerging trend ..."`. Cause: W1–W3. |
| **13:50–16:20 rally, first 45 pips** (13172.8 → 13217) | T7 bought at 14:00 and was trailed out at +5.1 by 14:37. Nothing else until 16:22. | (a) `13:50 range trade buy 13180.1 "... emerging trend, which does not allow range trade"`. (b) **EMA pullback:** hourly step 0 failed all day until 16:05: `15:05 ... 'hourly EMAs not in order and all moving one way (8 13190.4, 13 13190.1, 20 13190.5)'`. The three hourly EMAs sat within 2 pips of each other. (c) **Breakout:** it only looks when the analyser moves into an emerging trend from a range or consolidation breakout. At 15:40 the analyser moved from "emerging down" to "emerging up" by a rejection, so no breakout setup started. (d) **Slow grind:** `16:10 buy 13209.9 "the analyser's state is emerging trend, which does not allow slow grind"`. (e) **14:45 analyser flip** to "emerging down" (`rejected at the round_number 13200.0`) until 15:40, in the middle of the rally (W2). |
| **18:00 top at the previous day's high → 20:15** (13227.9 → 13208.3) | T12 (bounce sell, +10.2) took part of it. The bot was long 3 trades into it. | (a) **Level reversal cannot trade the previous day's high:** `level_types = ["S2", "R2", "round_number"]`. (b) **Analyser stayed "trend up" until 19:35** (W4), so `19:25 slow grind sell 13216.6 "the trend is up: slow grind only in the trend's direction"`, then `19:50 ... consolidation ...`. (c) Bounce sells 18:30–18:45 refused (one bounce each way). |
| **05:45 top → 07:00** (13202.5 → 13181.3) | T2 took part (+3.0, closed for the news). | The rest of the move was the news candle itself; no trade is allowed then (15 minutes before to 30 minutes after). |
| **01:30 previous-day-low sweep → 05:45** (13168 → 13202.5) | Nothing | Before 06:00, so only the slow grind and EMA pullback could trade. `02:50 slow grind buy "... emerging trend, which does not allow slow grind"`; `05:15 slow grind buy "TREND_STILL_GOING ... the most: 2.9 pips above the swing high"`; EMA pullback step 0 failed (hourly EMAs not in order). |

---

## Step 5: Why, at the root

There are several reasons, not one. In order of what they cost yesterday:

**1. The exits ignore structure (5 trades D, plus the exit side of T5).** −37.4 pips came from one candle: T1, T3 and T4 were stopped between 09:48:34 and 09:49:00 by a spike to 13204.4 (sell). All three had stops between 13200 and Monday's NY high 13205.2, a level group already on the bot's list. The box's stops sat there, and that is where a spike goes before reversing. Then T1 (+22.6 at best), T6 (+15.2) and T5 (+15.6) ended at −12.0, −20.8 and −3.3. Three strategies (EMA pullback, level reversal, range trade) have no exit between a fixed stop and a fixed target. The bounce/session trail can make its first move to the losing side of the entry, and it trails behind three 5-minute candles whatever the setup (T7 out at +5.1 at the start of a 40-pip move).

**2. Entries with no sense of the levels, and strategies that ignore the market read (3 trades C, 1 trade B).** In the afternoon the bot bought 1–6 pips under the previous day's high (T10, T11) and 15 pips away from its level (T8). Most of what it trades is exempt from the analyser: the bounce and the three session strategies "open without hindrance", and the level reversal opens in any state except consolidation, either way. So T9 sold into a strong push the analyser had correctly named, and the bot held buys and sells at once.

**3. The analyser misread the session, but that was not the main cause of losses.** It saw the 9-hour box as a run of emerging trends (W1–W3) and was late at both tops (W4). Of the 11 trades opened on the day, only 3 were gated by its state (T4 range trade, T10 slow grind, T11 EMA pullback), and it read all three states correctly at the time. Its misreads mainly **blocked** range trades at the box edges (step 4) and left the analyser no part in governing the trades that lost most. **The analyser is the main cause of the missed range trades. It is not the main cause of the losing trades.**

**4. One code fault (T5).** The trail retry kept the refused level and never sent the newer ones, against the rule at the time. Already fixed.

**5. HOURLY_READ off.** It would have changed exactly one trade (T10, blocked). It would not have changed T11 (hourly rally) or T1 (hourly sell-off), and it does not apply to the level reversal, bounce, range trade or session sweep.

**What was fine:** every strategy's entry steps matched its rules on every trade. The news close (T2), the 20:30 close and the one-bounce-each-way limit all worked as written. The analyser read the Asian session, the 13:50 turn and the 15:40–16:45 breakout correctly.

---

## Step 6: Suggested improvements

**Every suggestion below changes your rules. Each is for you to decide.** The numbers are ranges for you to choose from. None was tuned to make yesterday's losers disappear: each says which of yesterday's trades it would have changed, including winners it would have cost.

### Market analyser

**AN-1. Remember the range: a rejection inside the hourly range does not start or flip an emerging trend.** (W1, W2)

- **What:** while the hourly read is "ranging", a level rejection starts or flips an emerging trend only if it happens at the **edge** of the hourly range (within a set distance of its high or low) or after a close outside it. Rejections at levels inside the range (yesterday, the pivot in the middle and 13200 near the top) leave the state as ranging or consolidation. The hourly read already exists; this connects it to the 5-minute state machine.
- **Yesterday:** the 06:35, 08:55 and 14:45 calls (rejections at the pivot and at 13200 inside the 13168/13172.8–13204.4 hourly range) would not have happened. 09:30 and 10:00 (near the top edge) depend on the distance chosen. The range trade ideas at 08:10, 10:00, 10:05, 10:25, 13:25 and 13:50 would then have passed the state check. I am not judging whether they would have won. Two calls that were right would depend on the distance chosen: 13:50 (a rejection at the previous day's low, 13175.2, which is 7.2 pips above that hour's range low of 13168) and 15:40 (a close at 13204.4, exactly the range high).
- **Trend days:** on a trend day the hourly read is normally a sell-off or a rally, so this does not apply. The risk is the **first** move of a trend that starts from a level inside a quiet hourly range (your 5 November pivot example). It would be recognised later, at the range edge rather than at the level. Worth checking on your known days before deciding.
- **Numbers:** "at the edge" = within **3 to 8 pips** of the hourly range high or low.

**AN-2. Let ranging end an emerging trend.** (W3)

- **What:** when the ranging conditions (flat, close bands, both bands reached, EMAs weaving, flat 100 EMA) hold for the persistence candles, an emerging trend becomes ranging. Today it can only end in consolidation, by a cancel, by proof, by a flip or after 2 hours.
- **Yesterday:** 10:00–11:35 would have turned to ranging sooner. No trade opened in that spell, so no trade changes.
- **Trend days:** ranging needs both bands touched within 24 candles and flat bands, which a real early trend rarely shows. Low risk.
- **Numbers:** persistence of **2 to 6 candles** (today 2).

**AN-3. Let a rejection at a major level group end a trend that is younger than 30 pips.** (W4)

- **What:** today a possible reversal needs the trend to have moved 30 pips first. Allow it, at the levels that matter most (the previous day's high or low, R2/S2, and a session high or low that lines up with them), after a smaller move. Alternatively, measure the move from the session's extreme rather than from the start of the emerging trend.
- **Yesterday:** the 05:45 top (13202.5, 21.7 pips into the trend) and the 18:00 top (13227.9, 23.5 pips) could have become possible reversals. That would have **blocked** the trend strategies while it lasted: possible reversal allows only the level reversal. When it would have started depends on when the shared rejection part confirms a rejection at those levels, and I have not replayed that. So I cannot say whether T11 (17:16) would have been affected. The slow grind buy ideas at 18:02 and 18:21 (already refused because one slow grind was open) are the kind it would block.
- **Trend days:** **real risk**. On trend days price pauses at levels and carries on, and a possible reversal stops the trend strategies while it lasts. Exempting trend days and the expected-news-direction day (both already worked out by the bot) would limit this.
- **Numbers:** minimum move **15 to 30 pips** at the major groups only.

**AN-4. A breakout from consolidation needs a real close outside, not a 1–2 pip poke.** (W5)

- **What:** from consolidation, need two closes beyond the band (as from ranging), or a close beyond it by a minimum distance.
- **Yesterday:** the 07:50 (close 1.5 pips below the band) and 12:40 (1.2 above) false breakouts would not have happened. No trade came from either.
- **Trend days:** a real breakout is recognised one candle later. On your 6 November example the 09:50 trend came from proof, not from a consolidation breakout, so it would not be affected.
- **Numbers:** **2 closes**, or a close **2 to 4 pips** beyond the band.

### Strategies

**ST-1. Let the analyser govern the bounce again in a strong push the other way.**

- **What:** the bounce keeps all its own steps, but does not open against a **strong push** the analyser has named. Today it opens "without hindrance" (your rule of 15 November). This is not a new filter tuned to one trade; it puts the bounce back under the part built to read the market. It also fits your approved planner direction (D-37: the planner to become the bounce's authority).
- **Yesterday:** T9 (16:35, state "trend up, strong push") would not have opened. T5 (emerging down) and T12 (slow grind) would still have opened. For comparison, your existing switch `BOUNCE_ONLY_WHEN_HOURLY_RANGING` would have **allowed T5 and T9** (both while the hourly read said ranging) and **blocked T12** (hourly rally): the opposite of this suggestion on yesterday's trades.
- **Trend days:** this protects them. A strong push is exactly where a counter-trend bounce is most dangerous.
- **Numbers:** none needed (it uses the existing strong-push test). If you want it wider: also block against a slow-grind trend, which would also have stopped T12, a winner.

**ST-2. One view at a time for the whole bot: don't hold both directions.**

- **What:** when a new trade would go the opposite way to an open trade, choose one: refuse the new trade, or close the older one if the new trade's strategy outranks it. Today the bounce and the session strategies are exempt from "one view at a time", and "a bounce opening the other way closes nothing".
- **Yesterday:** with "refuse": T9 (LR buy T8 open) and T12 (three buys open) would not have opened, so it costs the +10.2 winner. With "close the older" and the bounce outranking: T8 and T10 would have closed at 16:35 and T11 would not have opened, and so on. **Your choice of order decides the outcome.** I am not totalling it.
- **Trend days:** "refuse" protects trend trades from counter-trend bounces. "Close the older" could close good trend trades on a counter-trend signal, so on trend days the trend strategies should rank first.
- **Numbers:** none.

**ST-3. Level reversal: add the previous day's high and low (and the session highs and lows that line up with them) as level types.**

- **What:** today `level_types = ["S2", "R2", "round_number"]`. Yesterday's two turning points in the afternoon were the previous day's low (13:35 sweep) and high (18:00 sweep). The level reversal could see neither, unless near 13200.
- **Yesterday:** a level reversal sell at the 18:00 previous-day-high rejection might have been set up (the step 4 miss). The 13:50 buy was already taken by the session sweep. Not judged on profit.
- **Trend days:** more counter-trend chances. The existing one-view rule (no reversal against a trend day or the expected news direction) still applies.
- **Numbers:** allowance past the level **3 to 12 pips** (today 5 for round numbers, 12 for R2/S2).

**ST-4. Range trade: target and stop from the box, not fixed.**

- **What:** the range trade's target is the opposite 5-minute band, and its stop a fixed 12 pips. Yesterday the bands were 14.1 pips apart (13183.7–13197.8), so the target was **6.7 pips** away and the risk 12. Either require the distance to the opposite band to be at least the stop, or place the stop beyond the box edge (see EX-1) and size the target from the box.
- **Yesterday:** T4. With a minimum reward-to-risk, it would not have opened. With a structure stop, it would not have been stopped by the 09:45 spike (buy high 13205.9 against a stop beyond 13205.2 plus a buffer). I am not claiming its final result.
- **Trend days:** the range trade only opens in "ranging", so trend days are unaffected.
- **Numbers:** reward-to-risk at least **0.8 to 1.5**.

### Entries

**EN-1. Level reversal: enter close to the level, not after the move has gone.**

- **What:** today the entry is the break of the confirmation candle, which can be far from the level. T8's entry was 15 pips away (stop 22.5, target 20), and T6 had 20.8 risk for 20 target. Change the entry so it happens within a set distance of the level, or require the stop distance to be no bigger than the target. This changes where the entry is; it is not a new condition on whether to trade.
- **Yesterday:** T8 would not have opened at 13217.2. T6 (14.6 pips from its furthest point) depends on the distance chosen. T2 and T3 (within about 4–7 pips) would not change.
- **Trend days:** none. The level reversal is a reversal strategy.
- **Numbers:** entry within **6 to 12 pips** of the level, or stop no more than **1.0 to 1.3 times** the target.

**EN-2. Trend entries next to a major level group: wait for the level to break and hold, rather than buying just under it.**

- **What:** when a slow grind or EMA pullback entry would come within a set distance **under** (for a buy) the previous day's high, R2 or an equivalent group, enter instead on a close beyond that group, or on a retest of it. Again this changes where the entry is, not whether a trend is traded.
- **Yesterday:** T10 (6.1 pips under 13224.5) and T11 (1.2 pips under) would have waited. Between 16:45 and 20:30 only two 5-minute candles closed above 13224.5: `17:50 ... C 13224.6` (0.1 above) and `18:00 ... C 13225.4` (0.9 above). With "beyond" set at 1 pip or more, neither trade would have opened before the fade.
- **Trend days:** **real risk**. On a trend day price runs through levels, and waiting for a close beyond each group costs some pips on each continuation entry. Your 6 November example ran through S1, S2 and S3. Applying it only to the previous day's high/low and R2/S2 groups, or not on trend days or the expected-news-direction day, limits it.
- **Numbers:** "next to" = within **3 to 10 pips** of the group. "Beyond" = a 5-minute close **1 to 4 pips** past it.

### Exits

**EX-1. Stops beyond the level group, not a fixed distance.** (T1, T3, T4)

- **What:** for the range trade, the level reversal and the EMA pullback, the stop goes a buffer **beyond the nearest important level group** past the entry, using the bot's level list. Today it is a fixed 12 pips or 6 beyond the furthest point. When that group is too far, the trade's size or its eligibility needs a rule, which is your decision.
- **Yesterday:** T1, T3 and T4 had stops at buy 13204.1, 13205.1 and 13202.4, all below the 13205.2 group. The 09:45 spike's buy high was 13205.9. A stop beyond 13205.2 plus the spread and a buffer of 2 pips or more would not have been reached by that candle, nor by the rest of the hour (`09:50-10:50: H 13204.3`). The cost: wider stops, so bigger losses on the trades that are wrong.
- **Trend days:** EMA pullback stops would sometimes be wider than 12 pips. At a fixed £10 a pip, that means more risk per trade. The 100-pip trend-day targets keep the balance, but the losses when wrong are bigger.
- **Numbers:** buffer **2 to 6 pips** beyond the group (plus the spread for a sell); a maximum stop of **15 to 25 pips** before the trade is skipped or handled another way.

**EX-2. A profit stage for the strategies with fixed exits.** (T1, T6)

- **What:** the level reversal, EMA pullback and range trade get one stage between stop and target. Once the trade has been a set amount in profit, its stop moves to break-even plus a little, or behind the last swing. You removed the bounce's break-even on 15 November, so how this behaved then is relevant.
- **Yesterday:** T1 (+22.6) and T6 (+15.2) would have been protected, if the stage starts at or below those amounts. T3 (+7.0) and T8 (+9.1) only if it starts lower.
- **Trend days:** the risk is mostly on the **EMA pullback** with its 100-pip trend-day target: a stop at break-even can be taken by a normal pullback before the big move. Applying it to the level reversal and range trade only (the counter-trend trades), or trailing the EMA pullback behind hourly swings rather than 5-minute candles, avoids that.
- **Numbers:** start at **10 to 20 pips** in profit; stop to break-even plus **0 to 3 pips**, or behind the last 5-minute swing.

**EX-3. The bounce and session trail: never move the first step to the losing side of the entry, and ignore news-spread candles.** (T5)

- **What:** (a) when the trail starts, its level must not be on the losing side of the entry (floor it at break-even); (b) a candle whose spread was more than `rejection.max_spread_pips` (3) is left out of the trail's "last 3 candles", as the rejection part already does for pierces.
- **Yesterday:** T5's first step went to 13193.2 (3.3 pips loss) using the 13:30 news candle's buy high of 13193.1 (spread 6.5). With (a), the first step would have been at break-even or better. The 31 refusals were a separate fault, now fixed. T7's first step (13193.9) was already above its entry, so no change.
- **Trend days:** none negative. It only stops the first move locking in a loss.
- **Numbers:** break-even floor plus **0 to 2 pips**.

**EX-4. The session sweep's trail sized to the setup.** (T7)

- **What:** the session sweep is a session-level reversal, but it trails behind three 5-minute candles from +12 pips, like the bounce. Trail it behind 5-minute **swing lows formed after the entry** (or hourly lows) instead.
- **Yesterday:** T7 was closed at +5.1 at 14:37 by the 14:35 candle's dip to 13192.6, then price rose to 13227.9. Whether a swing trail would have held depends on the swing definition. The 14:45–15:20 dips went to 13188.3, just above the 13187.4 entry.
- **Trend days:** a swing trail gives back more on fast spikes than a 3-candle trail.
- **Numbers:** swing = a low with **1 to 3** higher lows each side; or keep the 3-candle trail but start it at **15 to 25 pips**.

### Not suggested, and why

- **Treating US retail sales as big news:** it is "middle" in your 161-based table. T5 and T6 were in profit through it, so changing that would not have helped yesterday, and it is your table.
- **Switching HOURLY_READ on or off:** it is back on since 20:46. On yesterday's trades it would have changed only T10.
- **Any daily loss limit, strategy switch-off or single-number tightening:** not suggested, as you asked.

---

## What I ran and what I read

Read-only commands (each states in its own help text that it writes nothing or contacts nobody):

- `.venv/bin/python -m analyser 2026-11-17T06:03:00Z` and the same at 09:05, 09:15, 09:25, 09:30, 09:45 (5-minute Bollinger bands during T4).
- `.venv/bin/python -m levels --pair GBPUSD --at 2026-11-17T06:00:00Z` → `levels_2026-11-17_0600.txt`.
- `.venv/bin/python -m planner show --pair GBPUSD --at <10:00, 16:30, 17:40>` → `planner_show_2026-11-17.txt`.
- Small Python scripts calling `analyser.hourly_read.HourlyReader`, `strategies.ema_pullback.strategy.HourlyTrendReader` and `analyser.day_direction.day_directions` on the stored candles → `hourly_read_and_ema_pullback_step0_2026-11-17.txt`.

No replay or backtest was run.

Files beside this report:

| File | What it is |
|---|---|
| `trades_2026-11-17.csv` | Step 3 table, one row per trade |
| `trades_context.json` | The same with the raw opening and closing candles and the hour after |
| `trade_records_2026-11-17.jsonl` | The bot's own open and close records for the 12 trades (from `data/records/GBPUSD/trades.jsonl`) |
| `decisions_2026-11-17.jsonl` | Every idea, refusal, order and trade-manager decision on the day |
| `analyser_state_changes_2026-11-17.jsonl` | Every analyser state change, 16 Nov 20:25 to 17 Nov 23:50 |
| `prices_log_2026-11-17.txt` | The price service log for the day (with Monday 22:00–24:00) |
| `candles_5m_2026-11-17.csv`, `candles_1h_2026-11-17.csv`, `candles_1d_2026-11-16_17.csv` | The bot's own candles, buy and sell |
| `daily_summary_2026-11-17.json` | The bot's own daily summary |
| `levels_2026-11-17_0600.txt`, `planner_show_2026-11-17.txt`, `hourly_read_and_ema_pullback_step0_2026-11-17.txt` | Read-only tool outputs |

Also used: `/home/autobot/research/trail_refusal_20261117/` (yesterday's trail-refusal table), `docs/DESIGN.md` (current, and the 233d054 version for the old trail rule), `analyser/states.py`, `strategies/common.py`, `trade_manager/manager.py` (current, and the c0ede45 diff), `config/settings.toml`, `config/news_table.toml`, `/home/autobot/backups/planner-deploy-20261117/env.backup`.

**Limits of the evidence:**

- IG's minimum stop distance on the 17th was not recorded, so what the evening fix would have done on T5 can only be given as a condition.
- The order of prices inside a 5-minute candle is not stored, so moves within each trade's opening candle are shown, not assumed.
- Monday's daily candle is missing two 5-minute candles; the pivots could differ from IG's chart only if those 10 minutes held Monday's low.
- I relied on the bot's records for owner closes (they apply your SYSTEM rule) and made no IG call to check IG's activity.
