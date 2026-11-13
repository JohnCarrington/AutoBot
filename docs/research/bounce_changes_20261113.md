# Four changes to the Bollinger bounce (13 November 2026)

Read-only research: nothing in the bot was changed for it. The owner asked for four changes to the Bollinger bounce,
each on its own and the best combination. **Owner's decision (13 November 2026): change 4, break-even, built**
(section 4 of `docs/DESIGN.md`, `bounce.break_even_after_pips` 6).

## How it was run

- The bot's own research replay (`research.long_replay`) from the week's open on 25 October 2026 (21:00 UTC) to the
  end of the last stored candle, 16:05 UTC on 13 November 2026, on a copy of the bot's own IG candle store
  (`data/research/replay_stores/live_copy_20261113_1606`), against the committed code `d96de5f`.
- The switches are the live `.env`'s: the range trade had been switched off at 15:57 UTC that day, so no run has a
  range trade.
- Each change was a research-only switch in a frozen copy of the code (`git archive d96de5f`). With every switch off
  the copy gave the bot's trades byte for byte (three times).
- Runs, scripts and the explanation of every changed trade: `data/research/replay/bb_changes_20261113/`, the frozen
  code in its `code.tar.gz`.

## The changes as tested

1. **Second touch only:** a bounce opens only if an earlier bounce setup the same way, at the same band or the same
   level type within 5 pips of it, failed (cancelled or expired) or its trade was stopped, in the 60 minutes before
   the trigger. As worded it never blocks a bounce: the strategies' watcher starts a setup on every candle that
   pierces the band, so each push leaves expired and cancelled setups at the same band minutes earlier. Also run
   strictly: the earlier failure must have ended before this setup's pierce began (a separate, earlier touch).
2. **Not in a new state:** no bounce in the first 10 or 20 minutes of the analyser's current state (counted from the
   end of the candle that made it; a new trend type is not a new state).
3. **No bounce against an hourly band walk:** no sell while the last finished hourly candle closed at or above the
   upper hourly Bollinger band (20, 2), no buy while it closed at or below the lower.
4. **Protect profit:** once a bounce has been 6 pips up (in an earlier bar), its stop moves to break-even, or to
   2 pips in profit.

## Results (pips)

| Run | Trades | Won / lost | Pips | Change | Trend days | Other days | Bounces |
|---|---|---|---|---|---|---|---|
| The bot as it is | 141 | 71 / 70 | +1,514.8 | | +1,360.0 | +154.8 | 10, +17.1 |
| 1 as worded | 141 | 71 / 70 | +1,514.8 | 0 | +1,360.0 | +154.8 | 10, +17.1 |
| 1 strict | 139 | 70 / 69 | +1,511.1 | −3.7 | +1,344.3 | +166.8 | 8, +13.4 |
| 2, first 10 minutes | 137 | 68 / 69 | +1,501.0 | −13.8 | +1,344.3 | +156.8 | 6, +3.4 |
| 2, first 20 minutes | 136 | 66 / 70 | +1,425.8 | −89.0 | +1,344.3 | +81.5 | 5, −3.8 |
| 3, hourly band walk | 139 | 65 / 74 | +1,405.0 | −109.8 | +1,344.3 | +60.7 | 8, −17.9 |
| **4, break-even** | 141 | 70 / 69 | **+1,520.9** | **+6.1** | +1,359.6 | +161.3 | 10, +23.2 |
| 4, stop to +2 | 142 | 72 / 70 | +1,506.5 | −8.3 | +1,347.9 | +158.6 | 11, +8.8 |
| 1 strict + 4 break-even (best combination) | 139 | 69 / 68 | +1,517.2 | +2.4 | +1,343.9 | +173.3 | 8, +19.5 |
| 2 (10) + 4 | 137 | 67 / 68 | +1,507.2 | −7.6 | | | |
| Any combination with 3 | | | | −91.8 to −103.8 | | | |

Trend days: 6, 9, 10 and 11 November.

Break-even changed four bounces: 29 October 08:15 sell −2.8 to +3.2; 2 November 18:55 buy +5.5 to 0;
4 November 10:40 sell −7.5 to −1.5; 11 November 06:55 buy +0.4 to 0.

Most of the loss in change 2 (20 minutes) and change 3 is one bounce, at 14:10 on 26 October: under the pace and
target rule it closed the sells open against it (two EMA pullbacks from 08:35 at +12, two EMA pullbacks and a level
reversal from 13:55 at −4.8, −4.8 and −1.0). Without it those ran to their stops or closed lower, and the level
reversal still open blocked a +20 level reversal buy.

Applied to the 9 live bounces since 9 November (−15.95 pips at IG), break-even gives −11.9: 11 November 06:55
−3.3 to 0, 09:50 +0.45 to +1.3, 15:10 +0.1 to 0.
