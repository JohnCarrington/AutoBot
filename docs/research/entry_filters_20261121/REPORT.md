# Entry filters: build and check (Johnny's two rules, 21 Nov 2026)

Branch `entry-filters`, built from 5d7942e (the code checked out in /opt/autobot, which runs at the next restart).
Not merged, not deployed, nothing restarted, nothing sent to IG.

**Update, 21 Nov 2026 (Johnny's decision):** the session sweep is now exempt from rule 2, as are the slow grind, the
breakout and the Asian range breakout. Nothing else changed. The replays below were re-run with the exemption. The
per-strategy tables for rule 1, rule 2 and an RSI 3 alternative to rule 2 are at the end.

## What was built

- **`strategies/entry_filters.py` (new).** It holds both rules. `check()` is called once per trade from one place:
  `trading/engine.py` `_place`, just before the order sender's safety rules. Every trade passes through `_place`,
  whether it comes from the live price or a finished candle. No strategy's own code changed.
- **Switches.** `HOURLY_CONTEXT` (rule 1) and `ENTRY_NEAR_EMA8` (rule 2) are both on if left out of `.env`. The live
  `.env` doesn't list them, so both would be on at the next restart.
- **Numbers** are in `[entry_filters]` in `config/settings.toml`:
  - swing candles each side: 2
  - hourly EMA: 50
  - slope candles: 6
  - near: 5 pips
  - 5-minute EMA: 8
  - most distance from the 8 EMA: 5 pips

  They are documented in `docs/SETTINGS.md` and `docs/DESIGN.md` 3.10.
- **Refusals.** Each refusal is written to `decisions.jsonl` (kind `entry filter refused`) with the rule, a one-line
  reason and the numbers:
  - rule 1: the context, its swings, the last hourly close, the 50 EMA now and 6 candles before, the line it was near,
    the line's price and the distance;
  - rule 2: the entry price, the 8 EMA, the candle it was taken at and the distance.

  The "order" decision then shows `entry filter refused`. When a trade is allowed, what was checked is added to the
  trade's steps.

Johnny's answers, built in:
- "Last two swing highs are lower highs" means the latest swing high is lower than the one before it.
- "Price below/above the 50 EMA" means the last finished hourly close against the 50 EMA at that candle.
- The entry price is the strategy's own entry price (the sell / chart price), for buys too.

Everything is on the sell price. "Within 5" includes exactly 5. "No more than 5" allows exactly 5.

Three cases nobody specified (all should be rare):
- **No pivot.** If the daily pivot can't be worked out (the previous day's candle isn't stored), rule 1 checks the
  50 EMA only.
- **Not enough candles.** If there are too few hourly candles for the 50 EMA and its slope, there is no context.
- **8 EMA not ready.** If the 8 EMA isn't worked out yet, rule 2 doesn't check.

Each case is recorded in the trade's steps. Johnny may want a different choice for any of them.

Unchanged: a refused setup can come back on a later candle, if the strategy's own rules give it again. That is how
the safety rules' refusals already behave. Both replays below show it happening.

## Tests

- **`tests/functional/test_entry_filters.py`: 22 tests**, using the real settings and a real candle store of made-up
  candles. They cover:
  - rule 1: DOWN and UP, buys and sells, the pivot and the 50 EMA, exactly 5 against 5.1 pips, every strategy;
  - no context when the latest swing high isn't lower, when the close is on the wrong side, or when the 50 EMA isn't
    falling;
  - the swing definition, and that only finished hours are used;
  - rule 2: sells and buys, exactly 5 against 5.1, the four exemptions and that no other strategy is exempt, and the
    last finished 5-minute candle;
  - each switch on and off, both left out (on), and which rule is named when both refuse;
  - the engine: one call per trade, a refused trade never sent and its refusal recorded, and an allowed trade sent
    with exactly the same order as with both switches off.
- **The existing tests** run with both switches off (`tests/conftest.py`), as was done for `PULLBACK_ENTRY`.
- **Full suite: 2421 passed** (21 Nov 2026, this branch), and again by the pre-commit hook.

## Check replay

The full engine in paper mode, with a pretend IG that fails if called. The switches are the live `.env`'s with
TRADING off, run with both filter switches on and with both off (`entry_filters_replay.py`). The replay runs 5d7942e,
pullback entry included, on every day. The live bot ran other versions on 16–19 Nov, so the replay's trades are not
the live trades. "Live" below is what the bot actually did at IG, matched by strategy, direction and a time within
10 minutes. Replay profits are not totalled: the replays only check the code.

### The trades named in the brief (checked at the live time and live entry price, `named_trades.txt`)

| Trade | Result | Brief expected |
|---|---|---|
| Fri 20 Nov 13:10 level reversal buy, entry 13126.2 | **refused**, rule 1: 0.6 pips from the hourly 50 EMA 13126.8 | refused ✔ |
| Fri 20 Nov 13:25 slow grind buy, entry 13126.9 | **refused**, rule 1: 0.1 pips from the hourly 50 EMA 13126.8 | refused ✔ |
| Thu 19 Nov 07:35 Asian range breakout buy, entry 13155.0 | **allowed** | refused ✘ |
| Thu 19 Nov 12:10 session sweep sell, entry 13150.9 | **allowed**: the session sweep is now exempt from rule 2 (it was refused by rule 2 before the exemption) | still trades ✔ |

The context on Fri 20 Nov 13:10 and 13:25 was DOWN:
- the latest swing high was 13121.9 (Fri 07:00), lower than 13164.4 (Thu 14:00);
- the last hourly close was 13112 (12:00 candle), below the 50 EMA of 13126.8;
- the 50 EMA was falling: 13133.1 six candles before.

#### Thu 19 Nov 07:35 Asian range breakout buy: allowed by rule 1, the exact numbers

- **Hourly context at 07:35: DOWN.**
  - The latest swing high was 13153.3 (Thu 00:00), lower than 13157.5 (Wed 18:00).
  - The last finished hourly close was 13138.7 (06:00 candle), below the 50 EMA of 13168.1.
  - The 50 EMA was falling: 13177.4 six candles before.
- **Rule 1 (a buy in a DOWN context, within 5 pips of the pivot or the 50 EMA):**
  - entry 13155.0, daily pivot 13162.5: **7.5 pips** away;
  - entry 13155.0, hourly 50 EMA 13168.1: **13.1 pips** away.

  Neither is within 5, so rule 1 allows it. IG's buy fill was 13156.5, which would still be 6.0 pips from the
  pivot.
- **Rule 2:** entry 13155.0, 5-minute 8 EMA 13149.0, so **6.0 pips above**. That is more than 5, but the Asian range
  breakout is exempt from rule 2.
- **With pullback entry on** (as on this branch), the replay's Asian range breakout buy came at 07:55, entry 13152.2.
  The context was the same DOWN. It was 10.3 pips from the pivot, 15.9 from the 50 EMA and 2.7 above the 8 EMA, so it
  was allowed and traded in both replays.

#### Thu 19 Nov 12:10 session sweep sell: refused by rule 2 before the exemption, the exact numbers

- **Rule 2 (a sell no more than 5 pips below the 8 EMA):** entry 13150.9, 5-minute 8 EMA 13156.7 (the 12:05 candle).
  The entry was **5.8 pips below**. That is more than 5, so it is refused. In the replay the entry was 13151.1, 5.6
  below. Live, this trade made +28.9 pips (closed at IG's trailed stop).
- **Rule 1 does not refuse it.** The context was DOWN, which leaves sells alone:
  - the latest swing high was 13153.3 (Thu 00:00), lower than 13157.5 (Wed 18:00);
  - the last hourly close was 13154.7 (11:00 candle), below the 50 EMA of 13165.9;
  - the 50 EMA was falling: 13169.3 six candles before;
  - entry to pivot 13162.5: 11.6 pips; entry to 50 EMA: 15.0 pips.
- Before the exemption, the switches-on replay's session sweep tried again and sold at 13:10 instead.
- **Now:** the session sweep is exempt from rule 2 (Johnny's decision, 21 Nov), so this sell is allowed. Rule 1
  leaves it alone as above.
- In the re-run replay, the Thu 19 Nov session sweep sold at 09:30 instead, in both runs (switches on and off).
  The replay runs this branch's code, not what ran live that morning, and the sweep trades once per level per day,
  so the replay never reaches the 12:10 sell. The live 12:10 trade itself passes the direct check above.

The Thu 19 Nov 07:35 Asian range breakout buy is still allowed. Nothing was changed to alter that; Johnny decides.

### Mon 16 – Fri 20 Nov

There were 83 replay trades with both switches off and 59 with both on, from 56 refusals (session sweep exempt). The
full list, with each refusal's numbers and what the bot did live, is in `compare_16_20_nov.md`. Nineteen live trades
line up with a refused idea:

| Live trade (UK) | Rule | Numbers | Live |
|---|---|---|---|
| Mon 16 06:50 level reversal sell | 2 | entry 13197.8, 8 EMA 13203.3, 5.5 below | −11.5 (IG stop) |
| Mon 16 08:40 level reversal buy | 1 | DOWN; 2.9 from the pivot 13211.7 | −16.4 (IG stop) |
| Mon 16 09:50 level reversal sell | 2 | 13186.7 vs 13196.1, 9.4 below | −17.8 (IG stop) |
| Mon 16 10:50 EMA pullback sell | 2 | 13186.8 vs 13192.7, 5.9 below | −12.0 (IG stop) |
| Mon 16 14:26 EMA pullback sell | 2 | 13192.1 vs 13197.7, 5.6 below | −12.0 (IG stop) |
| Mon 16 14:57 EMA pullback sell | 2 | 13187.1 vs 13194.2, 7.1 below | −12.0 (IG stop) |
| Mon 16 15:50 EMA pullback sell | 2 | 13183.1 vs 13189.1, 6.0 below | −12.0 (IG stop) |
| Tue 17 10:05 Bollinger bounce sell | 2 | 13190.3 vs 13195.5, 5.2 below | −3.3 (IG stop) |
| Tue 17 10:05 level reversal sell | 2 | 13189.8 vs 13195.5, 5.7 below | −20.8 (IG stop) |
| Tue 17 16:22 level reversal buy | 2 | 13217.2 vs 13206.9, 10.3 above | −9.2 (20:30 close) |
| Tue 17 17:16 EMA pullback buy | 2 | 13223.3 vs 13216.6, 6.7 above | −12.0 (IG stop) |
| Wed 18 09:30 Bollinger bounce buy | 2 | 13161.8 vs 13156.4, 5.4 above | +7.2 (IG stop, trailed) |
| Wed 18 12:37 EMA pullback sell | 2 | 13156.2 vs 13162.8, 6.6 below | −12.0 (IG stop) |
| Wed 18 16:20 EMA pullback sell | 2 | 13140.8 vs 13149.8, 9.0 below | −12.0 (IG stop) |
| Thu 19 19:51 EMA pullback sell | 2 | 13094.8 vs 13100.2, 5.4 below | −7.9 (Johnny by hand) |
| Fri 20 06:07 level reversal buy | 1 | DOWN; 2.0 from the pivot 13111.6 | −17.3 (IG stop) |
| Fri 20 13:10 level reversal buy | 1 | DOWN; 0.6 from the 50 EMA | −26.1 (Johnny by hand) |
| Fri 20 13:25 slow grind buy | 1 | DOWN; 0.1 from the 50 EMA | −15.0 (IG stop) |
| Fri 20 18:45 level reversal sell | 2 | 13089.7 vs 13095.2, 5.5 below | +3.7 (20:30 close) |

The other 33 refusals did not trade live. Some were repeat tries of the same setup. Others were ideas from code that
wasn't running live on those days.

### Mon 9 – Wed 11 Nov, and Johnny's trend days

Johnny's definition of a trend day: the slow grind opened a trade, and that trade was in profit between 06:00 and
09:00 UK. On the 5-minute candles that means a slow grind trade opened before 09:00 whose closing price (sell price
for a buy, buy price for a sell) went beyond its entry at some point between 06:00 and 09:00.

| Day | Slow grind | Trend day? |
|---|---|---|
| Mon 9 Nov | live buy 05:25 at 13380.2, up to +18.2 by 09:00, take profit at 08:13 (replay: the same trade) | **yes** |
| Tue 10 Nov | the first slow grind trade came at 13:30 (live and replay) | no |
| Wed 11 Nov | live sell 08:13 at 13326.6, up to +11.1 by 09:00 (replay: 08:10) | **yes** |

There were 47 replay trades with both switches off and 38 with both on, from 18 refusals (session sweep exempt). The full list is in
`compare_9_11_nov.md`.

**Refusals on the trend days:**

| Idea (UK) | Rule | Numbers | Live |
|---|---|---|---|
| Mon 9 08:05 breakout buy | 1 | DOWN context; 4.1 pips from the hourly 50 EMA 13398.5 | the live breakout bought at 07:55 (on the break, without pullback entry): +11.7, Johnny closed it |
| Mon 9 08:25 level reversal buy | 2 | 13413.2 vs 8 EMA 13400.4, 12.8 above | −11.2, Johnny closed it |
| Mon 9 15:45 slow grind sell | 1 | UP context; 1.1 pips from the 50 EMA 13402.5 | −15.0 (IG stop) |
| Wed 11 07:30 EMA pullback sell | 2 | 13330.9 vs 13338.7, 7.8 below | +30.0 (take profit) |
| Wed 11 08:15 EMA pullback sell | 2 | 13323.1 vs 13329.0, 5.9 below | +30.0 (take profit) |
| Wed 11 10:00 Bollinger bounce 5m buy | 2 | 13325.3 vs 13319.8, 5.5 above | not traded live |
| Wed 11 10:50 EMA pullback sell | 2 | 13317.4 vs 13323.0, 5.6 below | +30.0 (take profit) |
| Wed 11 13:40 level reversal sell | 2 | 13294.3 vs 13300.9, 6.6 below | +20.0 (take profit) |
| Wed 11 13:50 / 13:55 / 14:00 level reversal sell | 2 | 6.0 / 9.3 / 9.0 below | repeats of the 13:40 setup; not traded again live |
| Wed 11 15:15 Bollinger bounce buy | 2 | 13283.4 vs 13275.4, 8.0 above | +0.1 (bot close) |

On Mon 9 Nov at 08:05 the hourly context was DOWN on a day that counts as an up trend day:
- the latest swing high was lower than the one before;
- the last hourly close was below a falling 50 EMA;
- the breakout's entry was within 5 pips of that EMA.

On Wed 11 Nov, rule 2 refused the EMA pullback sells and the level reversal sell that took profit live.

**Refusals on Tue 10 Nov (not a trend day):**
- 07:20 EMA pullback buy (live −12.0);
- 14:05 level reversal sell (live +20.0);
- 14:35 level reversal sell (not live);
- 16:25 / 16:35 level reversal sell (live −14.6, Johnny closed it);
- 22:00 EMA pullback sell (not live).

All of these were rule 2.

## Per strategy: rule 1, rule 2 and an RSI 3 alternative to rule 2, on the live trades

**How it was worked out** (`rule_tables.py`):
- Every live trade of 9–13 Nov (55) and 16–20 Nov (52) is put through each rule on its own. The check uses the live
  open time and the strategy's own entry price, as the bot would check it just before opening. It uses the stored
  candles and this branch's code, so the session sweep is exempt from rule 2.
- "Their live pips" is what the refused trades made at IG. **Saved** = the pips of the refused losers. **Cost** = the
  pips of the refused winners. Net = saved − cost.
- A refusal here only removes that one trade. Trades that might have opened instead (a setup trying again later, or
  a slot freed up) are not counted.
- Johnny's hand closes are included at the price he closed them, and counted in their own column.
- Trend days are Johnny's: Mon 9 and Wed 11 Nov. ★ marks them in the trade list.
- **The RSI 3 alternative** is a check only and is not in the bot or on the branch's code path. No SELL when the
  5-minute RSI 3 (sell price, at the last finished 5-minute candle before the entry) is under 30; no BUY when it is
  over 70. It has the same exemptions as rule 2: slow grind, breakout, Asian range breakout, session sweep.

**What the numbers say:**

| | 9–13 Nov | 16–20 Nov |
|---|---|---|
| Rule 1 | 2 refused, both losers: saved 21.0, cost 0 (net +21.0). 1 on a trend day (Mon 9 15:45 slow grind sell, −15.0). | 4 refused, all losers: saved 74.8, cost 0 (net +74.8). |
| Rule 2 | 8 refused, 5 of them winners: saved 37.8, cost 130.0 (net −92.2). 5 on trend days, together +98.8 live: the three Wed 11 EMA pullback sells (+30 each), the Wed 11 13:40 level reversal (+20) and the Mon 9 08:25 level reversal (−11.2, Johnny closed it). | 16 refused, 2 of them winners: saved 180.6, cost 10.9 (net +169.7). |
| RSI 3 alternative | 19 refused, 7 of them winners: saved 133.8, cost 123.6 (net +10.2). 8 on trend days, together +64.9 live. | 24 refused, 3 of them winners: saved 263.0, cost 13.8 (net +249.2). Every one of the 11 EMA pullback trades was refused. |

#### 9-13 Nov: 55 live trades (trend days: Mon 9 and Wed 11 Nov)

**Rule 1, hourly context**

| Strategy | Live trades | Refused | Their live pips | Winners | Saved (losers) | Cost (winners) | Net | On trend days: refused, their live pips | Of them closed by Johnny |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| Bollinger bounce | 11 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | 0, +0.0 | 0 |
| EMA pullback | 13 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | 0, +0.0 | 0 |
| breakout | 9 | 1 | -6.0 | 0 | 6.0 | 0.0 | +6.0 | 0, +0.0 | 0 |
| level reversal | 5 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | 0, +0.0 | 0 |
| range trade | 5 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | 0, +0.0 | 0 |
| slow grind | 12 | 1 | -15.0 | 0 | 15.0 | 0.0 | +15.0 | 1, -15.0 | 0 |
| **All** | 55 | 2 | -21.0 | 0 | 21.0 | 0.0 | +21.0 | 1, -15.0 | 0 |

**Rule 2, entry near the 8 EMA (session sweep exempt)**

| Strategy | Live trades | Refused | Their live pips | Winners | Saved (losers) | Cost (winners) | Net | On trend days: refused, their live pips | Of them closed by Johnny |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| Bollinger bounce | 11 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | 0, +0.0 | 0 |
| EMA pullback | 13 | 4 | +78.0 | 3 | 12.0 | 90.0 | -78.0 | 3, +90.0 | 0 |
| breakout | 9 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | 0, +0.0 | 0 |
| level reversal | 5 | 4 | +14.2 | 2 | 25.8 | 40.0 | -14.2 | 2, +8.8 | 2 |
| range trade | 5 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | 0, +0.0 | 0 |
| slow grind | 12 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | 0, +0.0 | 0 |
| **All** | 55 | 8 | +92.2 | 5 | 37.8 | 130.0 | -92.2 | 5, +98.8 | 2 |

**Alternative to rule 2: RSI 3 (sell under 30, buy over 70; same exemptions)**

| Strategy | Live trades | Refused | Their live pips | Winners | Saved (losers) | Cost (winners) | Net | On trend days: refused, their live pips | Of them closed by Johnny |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| Bollinger bounce | 11 | 4 | -8.4 | 2 | 12.0 | 3.6 | +8.4 | 1, +0.1 | 0 |
| EMA pullback | 13 | 10 | -36.0 | 2 | 96.0 | 60.0 | +36.0 | 4, +36.0 | 0 |
| breakout | 9 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | 0, +0.0 | 0 |
| level reversal | 5 | 5 | +34.2 | 3 | 25.8 | 60.0 | -34.2 | 3, +28.8 | 2 |
| range trade | 5 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | 0, +0.0 | 0 |
| slow grind | 12 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | 0, +0.0 | 0 |
| **All** | 55 | 19 | -10.2 | 7 | 133.8 | 123.6 | +10.2 | 8, +64.9 | 2 |

#### 16-20 Nov: 52 live trades (no trend days by Johnny's definition were given for this week)

**Rule 1, hourly context**

| Strategy | Live trades | Refused | Their live pips | Winners | Saved (losers) | Cost (winners) | Net | On trend days: refused, their live pips | Of them closed by Johnny |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| Asian range breakout | 3 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | – | 0 |
| Bollinger bounce | 8 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | – | 0 |
| Bollinger bounce 5m | 3 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | – | 0 |
| EMA pullback | 11 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | – | 0 |
| breakout | 2 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | – | 0 |
| level reversal | 14 | 3 | -59.8 | 0 | 59.8 | 0.0 | +59.8 | – | 1 |
| range trade | 2 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | – | 0 |
| session sweep | 4 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | – | 0 |
| slow grind | 5 | 1 | -15.0 | 0 | 15.0 | 0.0 | +15.0 | – | 0 |
| **All** | 52 | 4 | -74.8 | 0 | 74.8 | 0.0 | +74.8 | – | 1 |

**Rule 2, entry near the 8 EMA (session sweep exempt)**

| Strategy | Live trades | Refused | Their live pips | Winners | Saved (losers) | Cost (winners) | Net | On trend days: refused, their live pips | Of them closed by Johnny |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| Asian range breakout | 3 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | – | 0 |
| Bollinger bounce | 8 | 2 | +3.9 | 1 | 3.3 | 7.2 | -3.9 | – | 0 |
| Bollinger bounce 5m | 3 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | – | 0 |
| EMA pullback | 11 | 8 | -91.9 | 0 | 91.9 | 0.0 | +91.9 | – | 1 |
| breakout | 2 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | – | 0 |
| level reversal | 14 | 6 | -81.7 | 1 | 85.4 | 3.7 | +81.7 | – | 1 |
| range trade | 2 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | – | 0 |
| session sweep | 4 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | – | 0 |
| slow grind | 5 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | – | 0 |
| **All** | 52 | 16 | -169.7 | 2 | 180.6 | 10.9 | +169.7 | – | 2 |

**Alternative to rule 2: RSI 3 (sell under 30, buy over 70; same exemptions)**

| Strategy | Live trades | Refused | Their live pips | Winners | Saved (losers) | Cost (winners) | Net | On trend days: refused, their live pips | Of them closed by Johnny |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| Asian range breakout | 3 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | – | 0 |
| Bollinger bounce | 8 | 3 | -8.1 | 1 | 15.3 | 7.2 | +8.1 | – | 0 |
| Bollinger bounce 5m | 3 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | – | 0 |
| EMA pullback | 11 | 11 | -117.3 | 0 | 117.3 | 0.0 | +117.3 | – | 2 |
| breakout | 2 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | – | 0 |
| level reversal | 14 | 10 | -123.8 | 2 | 130.4 | 6.6 | +123.8 | – | 2 |
| range trade | 2 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | – | 0 |
| session sweep | 4 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | – | 0 |
| slow grind | 5 | 0 | +0.0 | 0 | 0.0 | 0.0 | +0.0 | – | 0 |
| **All** | 52 | 24 | -249.2 | 3 | 263.0 | 13.8 | +249.2 | – | 4 |

#### Every refused live trade

★ = Johnny's trend day. R1 / R2 / RSI = refused by that rule (each checked on its own).

| Opened (UK) | Strategy | Dir | Entry | Live pips | R1 | R2 | RSI 3 | RSI | Rule 1 or 2 numbers |
|---|---|---|---:|---:|:-:|:-:|:-:|---:|---|
| ★ Mon 09 Nov 06:12 | level reversal | buy | 13383.6 | +20.0 |  |  | ✓ | 92.3 |  |
| ★ Mon 09 Nov 08:25 | level reversal | buy | 13413.2 | -11.2 (Johnny) |  | ✓ | ✓ | 99.0 | a BUY more than 5 pips above the 5-minute 8 EMA: entry 13413.2, 5-minute 8 EMA 13400.4 (at the 08:20 candle), 12.8 pips above it: refused |
| ★ Mon 09 Nov 15:45 | slow grind | sell | 13401.4 | -15.0 | ✓ |  |  | 35.7 | SELL at 13401.4 is 1.1 pips from the hourly 50 EMA 13402.5 (within 5): refused |
| ★ Mon 09 Nov 21:02 | EMA pullback | buy | 13442.7 | -12.0 |  |  | ✓ | 83.4 |  |
| Tue 10 Nov 05:01 | EMA pullback | buy | 13449.2 | -12.0 |  |  | ✓ | 94.9 |  |
| Tue 10 Nov 06:12 | EMA pullback | buy | 13451.1 | -12.0 |  |  | ✓ | 85.3 |  |
| Tue 10 Nov 07:21 | EMA pullback | buy | 13454.5 | -12.0 |  | ✓ | ✓ | 76.5 | a BUY more than 5 pips above the 5-minute 8 EMA: entry 13454.5, 5-minute 8 EMA 13449.2 (at the 07:15 candle), 5.3 pips above it: refused |
| Tue 10 Nov 07:55 | Bollinger bounce | sell | 13450.3 | -6.0 |  |  | ✓ | 22.7 |  |
| Tue 10 Nov 08:20 | Bollinger bounce | sell | 13449.2 | -6.0 |  |  | ✓ | 28.2 |  |
| Tue 10 Nov 11:50 | breakout | sell | 13422.8 | -6.0 | ✓ |  |  | 19.9 | SELL at 13422.8 is 1.1 pips from the hourly 50 EMA 13421.7 (within 5): refused |
| Tue 10 Nov 14:06 | level reversal | sell | 13389.1 | +20.0 |  | ✓ | ✓ | 12.5 | a SELL more than 5 pips below the 5-minute 8 EMA: entry 13389.1, 5-minute 8 EMA 13399.0 (at the 14:00 candle), 9.9 pips below it: refused |
| Tue 10 Nov 16:26 | level reversal | sell | 13321.5 | -14.6 (Johnny) |  | ✓ | ✓ | 12.5 | a SELL more than 5 pips below the 5-minute 8 EMA: entry 13321.5, 5-minute 8 EMA 13334.6 (at the 16:20 candle), 13.1 pips below it: refused |
| ★ Wed 11 Nov 07:32 | EMA pullback | sell | 13330.9 | +30.0 |  | ✓ |  | 30.2 | a SELL more than 5 pips below the 5-minute 8 EMA: entry 13330.9, 5-minute 8 EMA 13338.7 (at the 07:25 candle), 7.8 pips below it: refused |
| ★ Wed 11 Nov 08:16 | EMA pullback | sell | 13323.1 | +30.0 |  | ✓ | ✓ | 15.7 | a SELL more than 5 pips below the 5-minute 8 EMA: entry 13323.1, 5-minute 8 EMA 13329.0 (at the 08:10 candle), 5.9 pips below it: refused |
| ★ Wed 11 Nov 10:51 | EMA pullback | sell | 13317.4 | +30.0 |  | ✓ | ✓ | 18.1 | a SELL more than 5 pips below the 5-minute 8 EMA: entry 13317.4, 5-minute 8 EMA 13323.0 (at the 10:45 candle), 5.6 pips below it: refused |
| ★ Wed 11 Nov 13:40 | level reversal | sell | 13294.3 | +20.0 |  | ✓ | ✓ | 15.5 | a SELL more than 5 pips below the 5-minute 8 EMA: entry 13294.3, 5-minute 8 EMA 13300.9 (at the 13:35 candle), 6.6 pips below it: refused |
| ★ Wed 11 Nov 15:10 | Bollinger bounce | buy | 13277.4 | +0.1 |  |  | ✓ | 86.7 |  |
| ★ Wed 11 Nov 21:06 | EMA pullback | sell | 13271.9 | -12.0 |  |  | ✓ | 6.3 |  |
| Thu 12 Nov 22:00 | EMA pullback | sell | 13230.7 | -12.0 |  |  | ✓ | 5.2 |  |
| Thu 12 Nov 23:47 | EMA pullback | sell | 13229.6 | -12.0 |  |  | ✓ | 13.8 |  |
| Fri 13 Nov 10:28 | EMA pullback | sell | 13225.2 | -12.0 |  |  | ✓ | 17.0 |  |
| Fri 13 Nov 18:06 | Bollinger bounce | buy | 13207.8 | +3.5 |  |  | ✓ | 70.4 |  |
| Mon 16 Nov 06:50 | level reversal | sell | 13197.8 | -11.5 |  | ✓ | ✓ | 3.0 | a SELL more than 5 pips below the 5-minute 8 EMA: entry 13197.8, 5-minute 8 EMA 13203.3 (at the 06:45 candle), 5.5 pips below it: refused |
| Mon 16 Nov 08:40 | level reversal | buy | 13208.8 | -16.4 | ✓ |  | ✓ | 85.2 | BUY at 13208.8 is 2.9 pips from the daily pivot 13211.7 (within 5): refused |
| Mon 16 Nov 09:50 | level reversal | sell | 13186.7 | -17.8 |  | ✓ | ✓ | 2.0 | a SELL more than 5 pips below the 5-minute 8 EMA: entry 13186.7, 5-minute 8 EMA 13196.1 (at the 09:45 candle), 9.4 pips below it: refused |
| Mon 16 Nov 10:25 | Bollinger bounce | buy | 13196.9 | -12.0 |  |  | ✓ | 80.1 |  |
| Mon 16 Nov 10:50 | EMA pullback | sell | 13186.8 | -12.0 |  | ✓ | ✓ | 15.0 | a SELL more than 5 pips below the 5-minute 8 EMA: entry 13186.8, 5-minute 8 EMA 13192.7 (at the 10:45 candle), 5.9 pips below it: refused |
| Mon 16 Nov 14:26 | EMA pullback | sell | 13192.1 | -12.0 |  | ✓ | ✓ | 13.8 | a SELL more than 5 pips below the 5-minute 8 EMA: entry 13192.1, 5-minute 8 EMA 13197.7 (at the 14:20 candle), 5.6 pips below it: refused |
| Mon 16 Nov 14:57 | EMA pullback | sell | 13187.1 | -12.0 |  | ✓ | ✓ | 25.2 | a SELL more than 5 pips below the 5-minute 8 EMA: entry 13187.1, 5-minute 8 EMA 13194.2 (at the 14:50 candle), 7.1 pips below it: refused |
| Mon 16 Nov 15:50 | EMA pullback | sell | 13183.1 | -12.0 |  | ✓ | ✓ | 28.0 | a SELL more than 5 pips below the 5-minute 8 EMA: entry 13183.1, 5-minute 8 EMA 13189.1 (at the 15:45 candle), 6.0 pips below it: refused |
| Mon 16 Nov 16:53 | EMA pullback | sell | 13182.6 | -12.0 |  |  | ✓ | 28.3 |  |
| Mon 16 Nov 20:00 | EMA pullback | sell | 13184.7 | -12.0 |  |  | ✓ | 14.6 |  |
| Tue 17 Nov 10:05 | Bollinger bounce | sell | 13190.1 | -3.3 |  | ✓ | ✓ | 23.0 | a SELL more than 5 pips below the 5-minute 8 EMA: entry 13190.1, 5-minute 8 EMA 13195.5 (at the 10:00 candle), 5.4 pips below it: refused |
| Tue 17 Nov 10:05 | level reversal | sell | 13189.8 | -20.8 |  | ✓ | ✓ | 23.0 | a SELL more than 5 pips below the 5-minute 8 EMA: entry 13189.8, 5-minute 8 EMA 13195.5 (at the 10:00 candle), 5.7 pips below it: refused |
| Tue 17 Nov 16:22 | level reversal | buy | 13217.2 | -9.2 |  | ✓ | ✓ | 91.1 | a BUY more than 5 pips above the 5-minute 8 EMA: entry 13217.2, 5-minute 8 EMA 13206.9 (at the 16:15 candle), 10.3 pips above it: refused |
| Tue 17 Nov 17:16 | EMA pullback | buy | 13223.3 | -12.0 |  | ✓ | ✓ | 78.0 | a BUY more than 5 pips above the 5-minute 8 EMA: entry 13223.3, 5-minute 8 EMA 13216.6 (at the 17:10 candle), 6.7 pips above it: refused |
| Wed 18 Nov 09:30 | Bollinger bounce | buy | 13161.5 | +7.2 |  | ✓ | ✓ | 82.2 | a BUY more than 5 pips above the 5-minute 8 EMA: entry 13161.5, 5-minute 8 EMA 13156.4 (at the 09:25 candle), 5.1 pips above it: refused |
| Wed 18 Nov 12:37 | EMA pullback | sell | 13156.2 | -12.0 |  | ✓ | ✓ | 28.4 | a SELL more than 5 pips below the 5-minute 8 EMA: entry 13156.2, 5-minute 8 EMA 13162.8 (at the 12:30 candle), 6.6 pips below it: refused |
| Wed 18 Nov 16:20 | EMA pullback | sell | 13140.8 | -12.0 |  | ✓ | ✓ | 23.1 | a SELL more than 5 pips below the 5-minute 8 EMA: entry 13140.8, 5-minute 8 EMA 13149.8 (at the 16:15 candle), 9.0 pips below it: refused |
| Wed 18 Nov 19:50 | level reversal | sell | 13135.7 | -11.3 |  |  | ✓ | 12.0 |  |
| Thu 19 Nov 19:51 | EMA pullback | sell | 13094.8 | -7.9 (Johnny) |  | ✓ | ✓ | 17.0 | a SELL more than 5 pips below the 5-minute 8 EMA: entry 13094.8, 5-minute 8 EMA 13100.2 (at the 19:45 candle), 5.4 pips below it: refused |
| Fri 20 Nov 06:07 | level reversal | buy | 13109.6 | -17.3 | ✓ |  | ✓ | 91.7 | BUY at 13109.6 is 2.0 pips from the daily pivot 13111.6 (within 5): refused |
| Fri 20 Nov 13:10 | level reversal | buy | 13126.2 | -26.1 (Johnny) | ✓ | ✓ | ✓ | 85.4 | BUY at 13126.2 is 0.6 pips from the hourly 50 EMA 13126.8 (within 5): refused |
| Fri 20 Nov 13:25 | slow grind | buy | 13126.9 | -15.0 | ✓ |  |  | 81.0 | BUY at 13126.9 is 0.1 pips from the hourly 50 EMA 13126.8 (within 5): refused |
| Fri 20 Nov 17:55 | level reversal | sell | 13096.1 | +2.9 (Johnny) |  |  | ✓ | 22.1 |  |
| Fri 20 Nov 18:42 | EMA pullback | sell | 13092.3 | -1.4 (Johnny) |  |  | ✓ | 27.1 |  |
| Fri 20 Nov 18:45 | level reversal | sell | 13089.7 | +3.7 |  | ✓ | ✓ | 13.6 | a SELL more than 5 pips below the 5-minute 8 EMA: entry 13089.7, 5-minute 8 EMA 13095.2 (at the 18:40 candle), 5.5 pips below it: refused |

## Files

- `entry_filters_replay.py`: the check replay.
- `replay_*_on.json`, `replay_*_off.json`: the replay results.
- `compare.py`, `compare_*.md`: the refusals next to the live trades.
- `named_trades.py`, `named_trades.txt`: the four named trades, checked one by one.
- `rule_tables.py`, `rule_tables.md`: the per-strategy tables and every refused live trade.
