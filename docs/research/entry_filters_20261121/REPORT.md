# Entry filters: build and check (Johnny's two rules, 21 Nov 2026)

Branch `entry-filters`, built from 5d7942e (the code checked out in /opt/autobot, which runs at the next restart).
Not merged, not deployed, nothing restarted, nothing sent to IG.

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
  - rule 2: sells and buys, exactly 5 against 5.1, the three exemptions and that no other strategy is exempt, and the
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
| Thu 19 Nov 12:10 session sweep sell, entry 13150.9 | **refused**, rule 2 | still trades ✘ |

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

#### Thu 19 Nov 12:10 session sweep sell: refused by rule 2, the exact numbers

- **Rule 2 (a sell no more than 5 pips below the 8 EMA):** entry 13150.9, 5-minute 8 EMA 13156.7 (the 12:05 candle).
  The entry was **5.8 pips below**. That is more than 5, so it is refused. In the replay the entry was 13151.1, 5.6
  below. Live, this trade made +28.9 pips (closed at IG's trailed stop).
- **Rule 1 does not refuse it.** The context was DOWN, which leaves sells alone:
  - the latest swing high was 13153.3 (Thu 00:00), lower than 13157.5 (Wed 18:00);
  - the last hourly close was 13154.7 (11:00 candle), below the 50 EMA of 13165.9;
  - the 50 EMA was falling: 13169.3 six candles before;
  - entry to pivot 13162.5: 11.6 pips; entry to 50 EMA: 15.0 pips.
- In the switches-on replay the session sweep tried again and sold at 13:10 instead.

Johnny decides. Nothing here was changed to make these two come out as the brief expected.

### Mon 16 – Fri 20 Nov

There were 83 replay trades with both switches off and 58 with both on, from 62 refusals. The full list, with each
refusal's numbers and what the bot did live, is in `compare_16_20_nov.md`. Twenty live trades line up with a refused
idea:

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
| Thu 19 12:10 session sweep sell | 2 | 13151.1 vs 13156.7, 5.6 below | +28.9 (IG stop, trailed) |
| Thu 19 19:51 EMA pullback sell | 2 | 13094.8 vs 13100.2, 5.4 below | −7.9 (Johnny by hand) |
| Fri 20 06:07 level reversal buy | 1 | DOWN; 2.0 from the pivot 13111.6 | −17.3 (IG stop) |
| Fri 20 13:10 level reversal buy | 1 | DOWN; 0.6 from the 50 EMA | −26.1 (Johnny by hand) |
| Fri 20 13:25 slow grind buy | 1 | DOWN; 0.1 from the 50 EMA | −15.0 (IG stop) |
| Fri 20 18:45 level reversal sell | 2 | 13089.7 vs 13095.2, 5.5 below | +3.7 (20:30 close) |

The other 38 refusals did not trade live. Some were repeat tries of the same setup. Others were ideas from code that
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

There were 47 replay trades with both switches off and 37 with both on, from 19 refusals. The full list is in
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
- 09:05 session sweep sell (not live);
- 14:05 level reversal sell (live +20.0);
- 14:35 level reversal sell (not live);
- 16:25 / 16:35 level reversal sell (live −14.6, Johnny closed it);
- 22:00 EMA pullback sell (not live).

All of these were rule 2.

## Files

- `entry_filters_replay.py`: the check replay.
- `replay_*_on.json`, `replay_*_off.json`: the replay results.
- `compare.py`, `compare_*.md`: the refusals next to the live trades.
- `named_trades.py`, `named_trades.txt`: the four named trades, checked one by one.
