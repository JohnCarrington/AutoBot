## Step 5. Conclusions

### 5.1 What is mechanically broken, most serious first

1. **The level reversal has no cap on its stop, and its take profit is fixed at 20.** This isn't a code fault
   against its spec: the rule is the first build's, line for line. But it lets one trade risk 34.3 pips to make 20,
   which is what produced today's −£261. The approved fixes (20-pip widest stop, entry within 6 pips of the level)
   were lost in the rollback.
2. **The live `.env` claims protections the live code doesn't have.** `LEVEL_STOPS=on`, `LR_ENTRY_NEAR_LEVEL=on`,
   `TRAIL_NO_LOSS=on`, `SCALE_OUT_REVERSAL=on`, `ANALYSER_USES_HOURLY=on`, `ANALYSER_GOVERNS_ALL=on`,
   `HOURLY_READ`, `TREND_STILL_GOING`: none of these is read by 02f6c7e. Anyone reading `.env` will believe the
   bot has caps and break-even exits it doesn't have.
3. **The breakout's stop silently went back from 12 to 6** in the rollback, against Johnny's 10 Nov instruction,
   and two reports said otherwise. No live breakout has traded since, so no money has been lost to it yet.
4. **A bounce setup's trigger never expires after confirmation.** The level reversal (and the 5m bounce, which
   uses the same watcher) can enter several candles late, far from the level. This is a gap in the written rule
   rather than a coding error, and it is how the 13:10 entry ended up 26.6 pips above the level.
5. **Small price-basis effects on stop prices** (level reversal, session sweep): a sell's stop cushion is about
   1.5 pips smaller than a buy's, and the stop shifts by the entry slippage (up to 0.7 pips seen) because a
   distance is sent rather than the level. Small, but not exactly the rule.

6. **Fixed, older:** on 17 Nov (version B) IG refused the hourly bounce's trail move 31 times
   (`ATTACHED_ORDER_LEVEL_ERROR`, 13:50–14:06), and a +15.6 trade ended at −3.3. The trail fix cc70dc5 (17 Nov
   20:36) sends the nearest level IG allows. No refusal has happened since (the journal has all 31 on 17 Nov).

**Not broken** (checked with IG's records): stops always sent, accepted and correctly placed; stops triggered only
when the price really reached them, with no slippage; normal spreads; entries on time and at the right price;
correct direction for each rule; no duplicate or stale entries; trails and level closes worked as specified.

### 5.2 Which strategies are losing, how much, and why

Bot's own exits only, IG pips, 9–20 Nov (Johnny's hand closes apart; £ at £10 a pip):

STRATEGY_TOTALS

| Strategy | Real reason (from the evidence) |
|---|---|
| **EMA pullback** (−138.0, 3 wins in 22; 0 in 8 in the 15–18 Nov version) | The rules losing in this market. Every loss was a full 12-pip stop against a 30-pip target, which needs 29% wins to break even; it got 14%. Today's 18:42 sell passed step 0 with slopes 1.01/0.60/0.57 pips an hour and a 0.38-pip gap (minimums 0.16 and 0.25): a trend barely there. No mechanical fault found in any of its trades (all 22 stops exactly 12, all stopped at the stop). |
| **slow grind** (−92.4, 4 in 15) | The rules losing in this market. A 15-pip stop against a 20-pip target. Today's 13:25 buy broke a 2-candle pause at 13126.9, 1.7 pips under the day's high 13128.6, at the same moment the hourly bounce was reading that high as a rejection. It never went into profit (best −1.1). |
| **level reversal** (−46.4 bot, and −52.5 on Johnny's closes) | Mostly the rule's risk shape: no cap on the stop, fixed 20-pip target, a trigger with no expiry, and no break-even. Today's 06:07 buy was +10.5 at best and then lost 17.3; the 13:10 buy risked 34.3 for 20. |
| **range trade** (−39.5, 1 in 7) | The rules losing. No trades in the current version. |
| **Bollinger bounce (hourly)** (−31.5, 7 in 17) | The rules losing slightly. Its wins are small trailed gains (+2.9 today); its losses are full 12s. |
| **Bollinger bounce 5m** (−13.7, 0 in 3, current version only) | Too few trades to judge. Two of three were closed near flat by the level-close rule; one was a full 12. All three were sells against "trend up, slow grind", which the rule allows ("against" the trend). |
| **Asian range breakout** (−2.3, 1 in 3) | Too few to judge. Today's 07:15 buy never went into profit (best −0.9) and was stopped at 12. |
| breakout (+17.1, 2 in 8) | Positive, small sample. Stop now 6, not 12 (see 5.1). |
| session sweep (+42.4, 4 in 4) | Positive, small sample. |

Two things cut across strategies:
- **Opposite trades at once.** The strategies read the same candles in opposite ways and nothing stops them
  opening against each other. In this version 12 such pairs were open together. When that happens, at least one
  side must lose, and both pay the spread.
- **The market has narrowed.** The 07:00–20:30 UK range (stored candles, sell price) was 47 pips on 16 Nov, 55,
  57, 80 on 19 Nov, and 41 today, mostly between 13090 and 13128. Several strategies have fixed 12–15 pip stops
  against 20–30 pip (or 100-pip) targets, which suits moves, not chop.

### 5.3 Suggestions (nothing built or changed)

- **Level reversal:**
  - Bring back a stop cap: either the 18 Nov `LEVEL_STOPS` widest 20, or simply refuse when the stop is wider than
    the take profit.
  - Bring back `LR_ENTRY_NEAR_LEVEL` (entry within 6 pips of the level).
  - Make the trigger expire one or two candles after the confirmation.
  - Consider a break-even once +10, as `TRAIL_NO_LOSS` did.
  - Or set the take profit from the stop (for example 1:1 or better).
- **`.env`:** remove or comment out the eight switches the live code ignores, so `.env` describes the live bot.
- **Breakout:** decide 6 or 12, and set `[breakout] stop_loss_pips` to match. Correct the two earlier reports.
- **Cross-strategy conflicts:** for example, no new trade against the direction of a trade another strategy has
  open, or extend rule 11 (one signal, one trade) to the level reversal and the bounce 5m. Today's 13:05–13:10
  candles alone opened five trades both ways.
- **EMA pullback:**
  - Raise step 0's minimum slope and gap, so it needs a real hourly trend (today's 18:42 trade had slopes just above
    the minimum).
  - Or test it only on days the analyser calls a trend from the morning.
  - Its 30-pip target on a 12-pip stop needs a trend that runs.
- **Slow grind:**
  - Avoid buying a pause break within a few pips of the day's high when a reversal setup (bounce, level reversal)
    is live on the same candle.
  - Or require the pause to come back toward the 21 EMA.
- **Bounces and the Asian range breakout:** keep observing; three trades each is not enough to judge.
- **Stop price basis (small):** send the level reversal's and session sweep's stop as a level (`stopLevel`), or
  add the spread on sells, so the stop sits exactly where the rule puts it.
- As always, the live demo is the judge. These are ideas for Johnny to choose from, not tested changes.
