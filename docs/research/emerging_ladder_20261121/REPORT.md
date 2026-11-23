# Emerging-trend ladder (Johnny's exit e): build and check, 21 Nov 2026

This was built on branch `entry-filters`, on the new AutoBot server (/opt/autobot), not AutoBot 161. It is **not
merged, not deployed and not restarted.** Nothing was sent to IG.

## What was built

- **Where it lives:** `trade_manager/manager.py`. It applies to every strategy.
- **Which trades:** only trades that opened while the analyser said "emerging trend", up or down. The engine
  passes the state recorded on the trade at open (`market_state`) to the trade manager. It does this when the trade
  opens and again after a restart, when the state comes from the trade's record.
- **The two steps:** once the trade is +10, its stop at IG moves to +5. Once it is +15, the stop moves to +10.
- **How profit is measured:** as IG closes the trade, from the price it opened at. A buy is measured on the sell
  price, a sell on the buy price.
- **When it is checked:** after every price, from the best pips reached so far. Live that means every tick; in a
  replay, every 5-minute candle.
- **Never backwards:** the ladder only moves the stop to a level tighter than the stop IG holds, and tighter than any
  move still waiting.
- **The strategy's own trail (rule 5):** both run, and the tighter stop wins at each step. A trail level looser than
  the ladder's is not sent.
  - The slow grind's 15/10 lock is a close made by the bot, not a stop at IG. It stays as it is, and whichever is
    tighter closes the trade.
- **The stop-move code (rule 7):** the moves go through the trail's existing code (`_move_stop` and the order
  sender's `move_stop`):
  - If the level is too close to the price, the sender uses the nearest level IG allows.
  - A move counts only once IG confirms it.
  - If IG refuses, the bot tries 3 times, sends one alert, and works the level out again after the next finished
    candle. This is the fix from 17 Nov.
  - The ladder asks for a level once. It asks again only at a new step, or after the next finished candle if IG's
    stop is not there yet. That is the same pace as the trail, so it doesn't send on every tick.
- **Unchanged:** the take profit, and trades opened in any other analyser state.
- **Settings:** `[emerging_ladder]` in `config/settings.toml` holds `first_from_pips` 10, `first_stop_pips` 5,
  `second_from_pips` 15 and `second_stop_pips` 10. The bot refuses to start if the numbers don't make sense.
- **Switch:** `EMERGING_LADDER` in `.env`, on if left out. It is documented in `docs/SETTINGS.md`, `docs/DESIGN.md`
  section 4 and `.env.example`.
- **Records (rule 10):** each confirmed stop move is kept on the trade (`stop_moves`: time, level, pips, who asked
  ("emerging ladder" or "trail"), why).
  - The list is saved with the trade's state, so it survives a restart, and is written in the trade's closing
    record.
  - Each move is also in decisions.jsonl as "stop moved", with the step that caused it.
  - Trail moves are now recorded on the trade in the same way.

## Tests

`tests/functional/test_emerging_ladder.py` has 41 tests:

| Rule | What is tested |
|---|---|
| 2, 3, 6 | Both steps, for buys and for sells. Profit is measured on the closing price. Nothing happens below +10. A jump straight past +15 gives one move, to +10. When price comes back, the trade is stopped at +5 or +10. |
| 4 | The stop never moves back when the trade falls back, or after a restart. |
| 5 | With the bounce's trail, the tighter stop wins at each step (4 moves: ladder, trail, ladder, trail). A trail that is already tighter is kept. The slow grind's lock and the ladder both apply. |
| 1, 8 | 7 other states are untouched. 5 strategies are tested, up and down. The take profit is unchanged. |
| 9 | The numbers come from settings. The switch is on if left out. Off stops it. Nonsense numbers are refused. |
| 10 | Each move is on the trade, in the decisions, and in the saved state. |
| 7 | Live, through the real order sender and the pretend IG: IG must confirm a move, the take profit is kept at IG, the nearest level IG allows is used, and IG refusing 3 times gives up with one alert and tries again after the next candle. |
| 1 in the engine | The state at open reaches the trade, and is restored after a restart from the trade's record. The move lands in the trade's closing record. |

The existing tests run with `EMERGING_LADDER=off` (`tests/conftest.py`), as was done for the entry filters.

**Full suite:** see the bottom of this file.

## Check replays (only to prove the code does what Johnny said)

**How the replays were run:**
- The full engine ran in paper mode, with a pretend IG that fails if anything is ever sent.
- Switches: the live `.env`'s switch lines, with TRADING off and both entry filters off.
- Each week was run with `EMERGING_LADDER` on and again with it off, so only the exit changes.
- The weeks were 9–13 Nov and 16–20 Nov (`ladder_replay.py`, `compare.py`, `compare.md`).

**These are not the live trades.** The replay runs this branch's code on every day, while the live bot ran other
versions. So the replay opens its own trades: 20 + 29 emerging-trend trades in the two weeks with the ladder off,
against 33 live.

### Every emerging-trend trade whose result changes

| Opened (UK) | Strategy | Dir | Best | Ladder off | Ladder on | Stop moves |
|---|---|---|---|---|---|---|
| Mon 09 Nov 08:05 | breakout | buy | 48.5 | take profit +50.0 | stopped +10.0 | +5 at 08:15, +10 at 08:20 |
| Mon 09 Nov 08:25 | level reversal | buy | 14.2 | take profit +20.0 | stopped +5.0 | +5 at 11:15 |
| Thu 12 Nov 11:40 | breakout | sell | 17.5 | stopped −6.0 | stopped +10.0 | +5 at 13:05, +10 at 13:10 |
| Thu 12 Nov 15:55 | Bollinger bounce | buy | 11.5 | 20:30 close +3.8 | stopped +5.0 | +5 at 16:40 |
| Fri 13 Nov 13:45 | Bollinger bounce | sell | 15.1 | stopped +6.2 | stopped +9.7 | +5 at 14:05, +10 at 14:20 |
| Fri 13 Nov 15:05 | Bollinger bounce | sell | 25.6 | stopped +17.9 | stopped +10.0 | +10 at 15:25 |
| Fri 13 Nov 15:10 | session sweep | sell | 19.1 | stopped +11.4 | stopped +10.0 | +5 at 15:40, +10 at 15:45 |
| Mon 16 Nov 12:35 | level reversal | sell | 15.7 | 20:30 close +8.4 | stopped +5.0 | +5 at 15:50 |
| Mon 16 Nov 14:25 | EMA pullback | sell | 22.6 | stopped −12.0 | stopped +5.0 | +5 at 15:50 |
| Tue 17 Nov 10:05 | Bollinger bounce | sell | 16.0 | stopped +8.7 | stopped +10.0 | +5 at 13:30, +10 at 13:35 |
| Tue 17 Nov 10:05 | level reversal | sell | 15.5 | stopped −20.6 | stopped +10.0 | +10 at 13:35 |
| Wed 18 Nov 07:05 | EMA pullback | sell | 98.6 | Friday close **+92.0** | stopped **+4.3** | +5 at 08:05 |
| Thu 19 Nov 16:15 | EMA pullback | sell | 29.4 | take profit +30.0 | stopped +5.0 | +5 at 17:05 |
| Thu 19 Nov 19:50 | EMA pullback | sell | 16.3 | stopped −12.0 | stopped +5.0 | +5 at 21:25 |
| Fri 20 Nov 06:05 | level reversal | buy | 10.8 | stopped −16.9 | stopped +5.0 | +5 at 07:10 |

**Trades that open only with the ladder on.** An earlier close frees a slot (one trade at a time each way, and one
signal one trade), so a later setup can open:

| Opened (UK) | Strategy | Dir | State at open | Result |
|---|---|---|---|---|
| Mon 09 Nov 19:40 | breakout | buy | emerging trend up | −6.0 |
| Thu 12 Nov 16:45 | Bollinger bounce | buy | emerging trend up | −12.0 |
| Thu 12 Nov 18:00 | Bollinger bounce | buy | emerging trend down | +9.2 |
| Tue 17 Nov 14:55 | level reversal | sell | emerging trend down | −15.7 |
| Fri 20 Nov 09:30 | level reversal | buy | emerging trend down | +20.0 |
| Mon 16 Nov 16:20 | level reversal | sell | **trend down, slow grind** | −0.1 |

The last one opened in a different state. Its exit is untouched; it simply had room to open because an
emerging-trend trade closed earlier.

**Every other trade is identical in both runs.** No trade from another state changed how it was managed.

### Totals, and the research's exit e

| | 9–13 Nov | 16–20 Nov | Both weeks |
|---|---|---|---|
| Emerging-trend trades in both runs, ladder off | +24.3 | −122.7 | −98.4 |
| The same trades, ladder on (the code) | −19.3 | −151.0 | **−170.3** |
| The same trades, the research's exit e method | −19.0 | −150.7 | **−169.7** |

**The code and the research method agree to 0.6 pips over 49 trades.** All three differences are explained:
- **Fri 13 Nov 13:45 (−0.3):** the 14:25 candle opened at a buy price of 13230.6, past the +10 stop at 13230.3. The
  existing stop code fills at the open, so the trade made +9.7.
- **Wed 18 Nov 07:05 (−0.7):** the same thing happened. The 08:10 candle opened at 13172.8, past the +5 stop at
  13172.1, so the trade made +4.3. The research method assumes an exact fill at the stop.
- **Tue 17 Nov 14:00 session sweep (+0.4):** its own trail held the stop at +5.4, which is tighter than the ladder's
  +5. Rule 5 kept the trail's stop, so the trade made +5.4. The research method has no trail.

**Why this is not the research's −28.6:**
- The research's −28.6 (against −135.9 actual) was the ladder applied to the **33 live trades** at IG prices.
- The replay opens **different trades:** this branch's code, run on every day, with candle fills.
- The big single trades differ:
  - The live 50-pip winner of 11 Nov 13:10 does not appear in the replay.
  - The replay has an 18 Nov 07:05 EMA pullback held to the Friday close for +92.0. The ladder stops it at +4.3, and
    that one trade costs 87.7 pips.
  - The replay's 9 Nov 08:05 breakout made +50. The ladder stops it at +10.
- So on the replay's trades the ladder comes out **71.9 pips worse**. On the live trades the research found it
  **107.3 pips better**.
- The cross-check above shows this is down to which trades are in the set, not the code. The ladder does in the
  engine exactly what exit e does on the candles.
- As always, the live demo is the judge. Replay totals are not a verdict.

### Johnny's trend days (9 and 11 Nov)

- **Mon 9 Nov:**
  - The 08:05 breakout buy is stopped at +10 instead of reaching its +50 target (−40.0).
  - The 08:25 level reversal buy is stopped at +5 instead of reaching its +20 target (−15.0).
  - A 19:40 breakout buy opens only with the ladder on, and loses −6.0.
- **Wed 11 Nov:** no change.

## Things for Johnny to know

- **On trend days the ladder cuts runners.** On 9 Nov two trades heading for their targets were stopped at +10
  and +5.
- **Freed slots change which trades open.** With the ladder on, 3 extra trades opened each week. One of them was
  from a different state (a slow grind trade on 16 Nov). That is a knock-on effect, not the ladder managing it.
- **Live, the move comes sooner than in the replay.** Live, the stop moves on the tick that first reaches +10 or
  +15. The replay only sees whole candles, so its moves come up to 5 minutes later.
- **IG's minimum stop distance.** The +5 stop sits only 5 pips from the price when it is set. If IG's minimum stop
  distance is more than 5, the sender uses the nearest level IG allows, as it does for the trail. The ladder then
  works its level out again after each finished candle.

## Files

- `ladder_replay.py`: the check replay.
- `compare.py` and `compare.md`: the comparison and the research cross-check.
- `replay_09_13_nov_{off,on}.json` and `replay_16_20_nov_{off,on}.json`: every trade, with its state, result and
  stop moves.

## Full suite

**2471 tests passed** (21 Nov 2026, this branch, 9 min 28 s). The pre-commit hook runs the suite again on commit.
