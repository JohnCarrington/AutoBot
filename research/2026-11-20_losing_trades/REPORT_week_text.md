## Week review, Mon 16 – Fri 20 Nov (Johnny's added request: Claude Code's own review)

Every trade the bot opened from Mon 16 Nov 00:00 to Fri 20 Nov 19:00 UTC: 51 trades. 44 were closed by the bot
or by IG, 6 by Johnny, and 1 is still open. Pips are IG's. "What price did" is measured on the stored 5-minute
candles: a buy on the sell price, a sell on the buy price, from the fill to the close (`week_paths.py`,
`week_paths.csv`). "Best" is the bot's own recorded best (`best_pips` in the trade record). The entry candle is
counted from its start, so the first-15-minute figures may include a little price action from before the fill.
Code versions: B = 15–18 Nov 13:35, C = 18 Nov 13:36–19 Nov 09:49, D = 19 Nov 09:49–18:43, E = since 19 Nov 18:44
(the current first-build-plus).

### W1. Every trade, one line each

WEEK_TABLE

### W2. The losers grouped by cause (bot and IG exits only, Johnny's closes apart)

| Cause | What it means | Trades | Pips | Which strategies |
|---|---|---|---|---|
| **A. Wrong from the start** | never 3 pips its way, then the full stop: the entry signal was wrong; stop and management did their job | 14 | **−181.6** | EMA pullback 4, level reversal 3, slow grind 3, Bollinger bounce 2, range trade 1, Asian range breakout 1 |
| **B. Too small a move** | 3–8 pips its way, then the full stop: a weak signal; the move never paid for a 12-pip stop | 8 | **−97.4** | EMA pullback 4, level reversal 1, Asian range breakout 1, Bollinger bounce 1, Bollinger bounce 5m 1 |
| **C. Gave back a real gain** | 8 pips or more its way (+10.5 to +22.6), then the full stop: management (nothing locked the gain) | 6 | **−81.8** | level reversal 3 (−54.5), EMA pullback 1, Bollinger bounce 1 (the 17 Nov trail refusal), breakout 1 |
| **E. The bot's own close at a loss** | closed at 20:30 or by the level-close rule before its stop | 3 | **−21.3** | level reversal 1, slow grind 1, Bollinger bounce 5m 1 |
| *Johnny's closes* | *not the bot's result* | *6* | *−35.6* | *level reversal 3, EMA pullback 2, Bollinger bounce 1* |

Two causes overlap the groups above:
- **Stop wider than the target** (level reversal only): 17 Nov 10:05 (stop 20.8, target 20, −20.8), 17 Nov 16:22
  (22.5 / 20, −9.2), 20 Nov 13:10 (34.3 / 20, −26.1, Johnny's close).
- **Opened against a trade already open in the other direction:** 15 of the week's trades. Of the 14 closed by the
  bot or IG: 5 won, 8 lost and 1 was flat, −57.5 pips net.

Wins: 12 trades, +107.9 pips. Session sweep 4 (+42.4), Bollinger bounce 3 (+20.3), level reversal 2 (+11.3),
Asian range breakout 1 (+21.7), range trade 1 (+11.6), slow grind 1 (+0.6). Only two wins reached more than half
their target: the 18 Nov Asian range breakout (+21.7, trailed from +30.7) and the 19 Nov session sweep (+28.9,
trailed from +42.2). Most wins were trails or the 20:30 close taking a small gain.

### W3. Each strategy this week

| Strategy | Trades | Wins | Losses | Pips | Johnny's closes | Broken, or rules that don't suit this market? |
|---|---|---|---|---|---|---|
| EMA pullback | 9 | 0 | 9 | **−108.0** | −9.3 (2) | **Rules.** All 9 were full 12-pip stops; 8 never got more than +6.2 (causes A and B). No mechanical fault: every stop was sent, accepted, exactly 12, and hit for real. 3 wins in 22 since 9 Nov. |
| level reversal | 10 | 2 | 8 | **−106.4** | −26.7 (3) | **Mostly the rule's risk shape** (no cap on the stop, fixed 20-pip target, a trigger that never expires, no break-even in B, C or E), plus wrong signals (3 of cause A). Three trades were +10.5 to +15.2 and lost their full stop (−54.5). |
| slow grind | 5 | 1 | 4 | **−54.8** | – | **Rules.** 3 of 4 losses never went 3 pips its way; it buys or sells the break of a pause at the end of a move. |
| Bollinger bounce (hourly) | 7 | 3 | 4 | −19.0 | +0.4 (1) | Rules, with **one mechanical fault in B**: the 17 Nov 10:05 trail refused by IG 31 times (fixed since). Otherwise the full 12 on losers and small trailed wins. |
| Bollinger bounce 5m | 3 | 0 | 2 (1 flat) | −13.7 | – | Too few to say. The level-close rule cut one at −1.7 and one at 0.0 (after +11.0; it has no trail). |
| breakout | 1 | 0 | 1 | −12.0 | – | Too few. The 18 Nov sell was +16.1, then lost 12 over 7 hours: no trail (management). Its live stop is now 6. |
| Asian range breakout | 3 | 1 | 2 | −2.3 | – | Too few. One good trailed win (+21.7), two signals that failed at once. |
| range trade | 2 | 1 | 1 | −0.4 | – | Too few. |
| session sweep | 4 | 4 | 0 | **+42.4** | – | Working so far (small sample). |
| **All** | **44** | **12** | **31** (1 flat) | **−274.2** (−£2,742) | **−35.6 (6)** | |

### W4. My recommendations, most important first (nothing built or changed)

1. **Switch the EMA pullback off.** Evidence: 0 wins in 9 this week (−108.0), 3 in 22 since 9 Nov (−138.0), and it
   lost in every code version (A −30.0, B −96.0, C −12.0). Every loss was a clean full stop with no mechanical
   fault, so this is the rule, not the plumbing. It is the biggest single drain.
2. **Fix the level reversal's risk before trading it again, or switch it off until then.** Evidence: −106.4 this
   week and −26.7 more on Johnny's closes. Three stops were at least as wide as the 20-pip target, and 34.3 pips was
   risked to make 20. Three trades gave back +10.5 to +15.2. The fix, in order of value:
   - refuse a trade whose stop is wider than its target (or bring back the 20-pip cap);
   - bring back entry within 6 pips of the level;
   - make the trigger expire 1–2 candles after confirmation;
   - break-even at +10.
3. **Switch the slow grind off.** Evidence: 1 win in 5 this week (−54.8), 4 in 15 since 9 Nov (−92.4). Three of
   this week's 4 losses never went 3 pips its way: its entries are late.
4. **Add a "don't give back a real gain" rule to every strategy:** for example, move the stop to break-even
   once a trade is +10. Evidence: cause C, 6 trades that were +10.5 to +22.6 and ended at −81.8 pips in total.
   In the live code only the hourly bounce and the three session strategies trail (from +12); the slow grind
   closes at +10 once it has been +15; the EMA pullback, level reversal, breakout, range trade and bounce 5m have
   nothing.
5. **Stop strategies trading against each other:** no new trade against the direction of a trade that is already
   open. Evidence: 15 trades this week opened against an open opposite trade (bot exits 5 won, 8 lost, 1 flat,
   −57.5). On 20 Nov 13:10–13:35, five trades opened both ways off one move.
6. **Make `.env` honest and set the breakout stop on purpose.** Remove the eight switches the live code ignores
   (`LEVEL_STOPS`, `LR_ENTRY_NEAR_LEVEL`, `TRAIL_NO_LOSS` and others). Choose 6 or 12 for `[breakout]
   stop_loss_pips` (it is 6 now, Johnny chose 12 on 10 Nov).
7. **Keep:**
   - the session sweep (4 from 4, +42.4);
   - the Asian range breakout and the hourly Bollinger bounce, on watch (near flat; their trails produced the
     week's best wins);
   - the breakout, range trade and Bollinger bounce 5m, on watch (too few trades to judge).

These are judgments from one week of live demo trades (plus 9–13 Nov for context), and every sample is small. The
live demo stays the judge.
