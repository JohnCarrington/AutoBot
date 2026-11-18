# Stage 4: entries and exits

Branch `feature/entries-exits`, built 18 November 2026 from main 3d50353 (the code live on the demo). **Nothing is merged, deployed or switched on.** The live checkout, the live `.env` and the running service were not touched, and nothing was restarted. The three new switches are **off** if left out of `.env`, and the live `.env` doesn't have them.

Only the bot's own records (`data/records/GBPUSD/trades.jsonl`) and its stored candles were used. No IG call was made, and IG's history allowance was not used. Sell (bid) prices, UK times. The two trades you closed by hand (IG's SYSTEM channel) are kept apart. Replays only check that the code does what your rules say. The pips shown are only so you can see how each trade ended; they are not a verdict.

## Summary

- **Part A:** the tables below give, for every live range trade, level reversal and EMA pullback since 9 November, the stop each buffer (2 to 6 pips beyond the nearest level group) would have given, whether it would have been hit, and whether the trade reached +8 or its target. They also give how many trades each widest stop (15, 20, 25) would skip, how often a stop in a level group was taken by a spike, and how far price goes past a level group before turning back. I haven't chosen the numbers.
- **Part B:** `SCALE_OUT_REVERSAL`, `TRAIL_NO_LOSS` and `LR_ENTRY_NEAR_LEVEL` are built as written, plus the start-up line listing every switch. They are documented in `docs/DESIGN.md` (marked "(owner, 18 November 2026)") and `docs/SETTINGS.md`. Settings: `scale_out.at_profit_pips` 8, `scale_out.stop_profit_pips` 2, `level_reversal.entry_within_pips_of_level` 6.
- **Trend days, 6 and 10 November:** the trend group's trades are unchanged with all three switches on (same trades, same results).
- **17 November:**
  - The bounce's first trail move goes to the entry instead of 13193.2.
  - The 16:20 level reversal buy is refused: its level is the round number 13200, 17.2 pips away.
  - With only `SCALE_OUT_REVERSAL` on, that trade instead closes half at +8 and the rest at +2.
- **LEVEL_STOPS** (added after your answers): the stop 5 pips beyond the nearest level group (the spread for a sell capped at 3), widest 20. Trend days unchanged. On 17 November the 17:15 EMA pullback buy changes, −12.0 becomes −10.0 (its 10-pip level stop).
- **Full test suite:** 2,484 passed.

## Part A: the stop numbers (measured, not chosen)

**How it was measured** (my choices where your brief left the method open; tell me if you want any done differently):
- **Levels and groups:** the bot's own level list and its own 5-pip grouping, as they stood when each trade opened (`levels.current.build`). A single level is a group of one.
- **Nearest group beyond the entry on the stop side:** for a sell, the lowest group whose top is above the fill; for a buy, the highest group whose bottom is below the fill.
- **The stop at each buffer:**
  - A sell: the group's top + buffer + the spread when the trade opened (the bot's own "bid, offer" record).
  - A buy: the group's bottom − buffer.
  - Its distance is measured from IG's fill.
- **Hit / +8 / target:** each stop was replayed through the bot's own trade manager on the stored 5-minute candles, with the trade's own take profit, its scheduled close (20:30, Friday 20:30 for the EMA pullback, before big news) and the range trade's close at the opposite band.
  - The range trade's close on a level rejection is left out (it needs the live rejection events). That changes one trade: 11 November 11:13, which really closed at −9.1 on a rejection.
  - The replay with the stop each trade actually had matches the real result on every bot-closed trade except that one.
- **A2 and A3:** defined in their sections.
- **Tools:** `research/stop_buffers.py` (read-only). Raw results: `partA_trades.json`, `partA_inside_groups.json`, `partA_overshoot.json`.

### A1. Every live trade of the three strategies, and its stop at each buffer

41 live trades since 9 November 2026: 39 closed by the bot, 2 closed by you by hand (kept apart at the end). For each: the stop it had, the nearest level group beyond the entry on the stop side, then the stop at each buffer beyond that group. Each column gives the stop's distance from the entry in pips, then **S** if that stop would have been hit, **8** if the trade reached +8 before its exit, **T** if it reached its target (the level reversal's 20 pips, the EMA pullback's 30 or 100, the range trade's opposite band). A dash: none of these.


**Level reversal**

| Opened (UK) | Way | Entry (fill) | Stop it had | Nearest group beyond (levels) | Actual | +2 | +3 | +4 | +5 | +6 |
|---|---|---|---|---|---|---|---|---|---|---|
| Mon 09 Nov 06:12 | buy | 13385.4 | 13372.5 (12.9) | 13378.4-13380.7 (turning low 13378.4, R2 13379.4, turning low 13380.2, london session low 13380.7) | 12.9 8T | 9.0 8T | 10.0 8T | 11.0 8T | 12.0 8T | 13.0 8T |
| Tue 10 Nov 14:06 | sell | 13388.9 | 13407.4 (18.5) | 13389.1 (new york session low 13389.1) | 18.5 8T | 3.7 S | 4.7 S | 5.7 S | 6.7 S | 7.7 S |
| Wed 11 Nov 13:40 | sell | 13294.2 | 13307.3 (13.1) | 13294.3-13296.0 (new york session low 13294.3, turning low 13296.0) | 13.1 8T | 5.3 S | 6.3 8T | 7.3 8T | 8.3 8T | 9.3 8T |
| Mon 16 Nov 06:50 | sell | 13197.5 | 13209.0 (11.5) | 13196.3-13200 (S2 13196.3, round number 13200) | 11.5 S | 6.0 S | 7.0 S | 8.0 S | 9.0 S | 10.0 S |
| Mon 16 Nov 08:40 | buy | 13210.4 | 13194.0 (16.4) | 13209.3-13211.7 (london session high 13209.3, pivot 13211.7) | 16.4 S8 | 3.1 S8 | 4.1 S8 | 5.1 S8 | 6.1 S8 | 7.1 S8 |
| Mon 16 Nov 09:50 | sell | 13186.5 | 13204.3 (17.8) | 13186.7-13190.5 (london session low 13186.7, S3 13190.5) | 17.8 S | 7.5 S | 8.5 S | 9.5 S | 10.5 S | 11.5 S |
| Mon 16 Nov 12:37 | sell | 13194.5 | 13208.9 (14.4) | 13196.3-13200 (S2 13196.3, round number 13200) | 14.4 8 | 9.0 S | 10.0 S | 11.0 S | 12.0 S | 13.0 8 |
| Tue 17 Nov 06:03 | sell | 13198.7 | 13208.5 (9.8) | 13200 (round number 13200) | 9.8 - | 4.8 - | 5.8 - | 6.8 - | 7.8 - | 8.8 - |
| Tue 17 Nov 07:35 | sell | 13191.7 | 13205.1 (13.4) | 13194.4 (pivot 13194.4) | 13.4 S | 6.2 S | 7.2 S | 8.2 S | 9.2 S | 10.2 S |
| Tue 17 Nov 10:05 | sell | 13189.5 | 13210.3 (20.8) | 13194.4 (pivot 13194.4) | 20.8 S8 | 8.4 S | 9.4 S | 10.4 S | 11.4 S8 | 12.4 S8 |
| Tue 17 Nov 16:22 | buy | 13218.8 | 13196.3 (22.5) | 13213.5-13218.5 (R1 13213.5, new york session high 13217.2, turning low 13217.4, turning high 13218.5) | 22.5 8 | 7.3 S8 | 8.3 S8 | 9.3 S8 | 10.3 S8 | 11.3 8 |

**Range trade**

| Opened (UK) | Way | Entry (fill) | Stop it had | Nearest group beyond (levels) | Actual | +2 | +3 | +4 | +5 | +6 |
|---|---|---|---|---|---|---|---|---|---|---|
| Mon 09 Nov 13:55 | buy | 13418.6 | 13412.6 (6) | 13416.1 (london session high 13416.1) | 6 S | 4.5 S | 5.5 S | 6.5 S | 7.5 S | 8.5 S |
| Mon 09 Nov 14:55 | buy | 13415.3 | 13409.3 (6) | 13408 (new york session low 13408) | 6 S | 9.3 S | 10.3 S | 11.3 S | 12.3 S | 13.3 S |
| Mon 09 Nov 15:16 | buy | 13410.9 | 13404.9 (6) | 13401.7-13406.5 (turning low 13401.7, turning low 13402.7, new york session high 13404.1, turning high 13404.1, new york session low 13404.5, turning high 13406.0, turning high 13406.5) | 6 S | 11.2 S | 12.2 S | 13.2 S | 14.2 T | 15.2 T |
| Wed 11 Nov 11:13 | buy | 13318.4 | 13306.4 (12) | 13312.2-13313 (previous day low 13312.2, new york session low 13312.2, turning low 13312.2, london session low 13313) | 12 S | 8.2 S | 9.2 S | 10.2 S | 11.2 S | 12.2 S |
| Fri 13 Nov 09:55 | buy | 13235.0 | 13223.0 (12) | 13227.1 (london session low 13227.1) | 12 S | 9.9 S | 10.9 S | 11.9 S | 12.9 S | 13.9 S |
| Mon 16 Nov 17:27 | sell | 13193.7 | 13205.7 (12) | 13196.3-13200 (S2 13196.3, round number 13200) | 12 8T | 9.8 8T | 10.8 8T | 11.8 8T | 12.8 8T | 13.8 8T |
| Tue 17 Nov 08:59 | sell | 13190.4 | 13202.4 (12) | 13194.4 (pivot 13194.4) | 12 S | 7.5 S | 8.5 S | 9.5 S | 10.5 S | 11.5 S |

**Ema pullback**

| Opened (UK) | Way | Entry (fill) | Stop it had | Nearest group beyond (levels) | Actual | +2 | +3 | +4 | +5 | +6 |
|---|---|---|---|---|---|---|---|---|---|---|
| Mon 09 Nov 21:02 | buy | 13443.6 | 13431.6 (12) | 13441.9-13445.2 (new york session high 13441.9, turning low 13445.2) | 12 S | 3.7 S | 4.7 S | 5.7 S | 6.7 S | 7.7 S |
| Tue 10 Nov 05:01 | buy | 13451.0 | 13439.0 (12) | 13447.2-13450 (turning low 13447.2, turning high 13448.0, round number 13450) | 12 S | 5.8 S | 6.8 S | 7.8 S | 8.8 S | 9.8 S |
| Tue 10 Nov 06:12 | buy | 13452.8 | 13440.8 (12) | 13447.2-13450 (turning low 13447.2, turning high 13448.0, round number 13450) | 12 S | 7.6 S | 8.6 S | 9.6 S | 10.6 S | 11.6 S |
| Tue 10 Nov 07:21 | buy | 13456.1 | 13444.1 (12) | 13453.3-13453.7 (turning low 13453.3, london session high 13453.7) | 12 S | 4.8 S | 5.8 S | 6.8 S | 7.8 S | 8.8 S |
| Wed 11 Nov 07:32 | sell | 13330.9 | 13342.9 (12) | 13333.9-13337.6 (london session low 13333.9, turning low 13334, turning high 13336.0, turning high 13337.6) | 12 8T | 10.2 8T | 11.2 8T | 12.2 8T | 13.2 8T | 14.2 8T |
| Wed 11 Nov 08:16 | sell | 13323.1 | 13335.1 (12) | 13323.6-13327.5 (london session low 13323.6, turning low 13327.5) | 12 8T | 7.9 S8 | 8.9 8T | 9.9 8T | 10.9 8T | 11.9 8T |
| Wed 11 Nov 10:51 | sell | 13317.0 | 13329.0 (12) | 13327.5 (turning low 13327.5) | 12 8T | 14.0 8T | 15.0 8T | 16.0 8T | 17.0 8T | 18.0 8T |
| Wed 11 Nov 18:48 | sell | 13273.5 | 13285.5 (12) | 13286.4 (S1 13286.4) | 12 S | 16.4 S | 17.4 8T | 18.4 8T | 19.4 8T | 20.4 8T |
| Wed 11 Nov 21:06 | sell | 13270.7 | 13282.7 (12) | 13286.4 (S1 13286.4) | 12 S | 19.2 S | 20.2 8T | 21.2 8T | 22.2 8T | 23.2 8T |
| Thu 12 Nov 19:02 | sell | 13225.6 | 13237.6 (12) | 13234.1 (S1 13234.1) | 12 S | 12.0 S | 13.0 S | 14.0 S | 15.0 S | 16.0 S |
| Thu 12 Nov 22:00 | sell | 13230.7 | 13242.7 (12) | 13234.1 (S1 13234.1) | 12 S | 22.3 8 | 23.3 8 | 24.3 8 | 25.3 8 | 26.3 8 |
| Thu 12 Nov 23:47 | sell | 13229.2 | 13241.2 (12) | 13234.1 (S1 13234.1) | 12 S | 8.4 S | 9.4 S | 10.4 S | 11.4 S | 12.4 S |
| Fri 13 Nov 10:28 | sell | 13225.1 | 13237.1 (12) | 13225.3 (london session low 13225.3) | 12 S | 3.7 S | 4.7 S | 5.7 S | 6.7 S | 7.7 S |
| Mon 16 Nov 10:50 | sell | 13187.1 | 13199.1 (12) | 13190.5 (S3 13190.5) | 12 S | 6.9 S | 7.9 S | 8.9 S | 9.9 S | 10.9 S |
| Mon 16 Nov 14:26 | sell | 13192.1 | 13204.1 (12) | 13196.3-13200 (S2 13196.3, round number 13200) | 12 S8 | 11.4 S8 | 12.4 S8 | 13.4 S8 | 14.4 S8 | 15.4 S8 |
| Mon 16 Nov 14:57 | sell | 13187.3 | 13199.3 (12) | 13188.4-13190.5 (new york session low 13188.4, S3 13190.5) | 12 S | 6.7 S | 7.7 S | 8.7 S | 9.7 S | 10.7 S |
| Mon 16 Nov 15:50 | sell | 13183.2 | 13195.2 (12) | 13182.1-13184.6 (london session low 13182.1, turning low 13182.1, new york session low 13184.6) | 12 S | 4.9 S | 5.9 S | 6.9 S | 7.9 S | 8.9 S |
| Mon 16 Nov 16:53 | sell | 13182.5 | 13194.5 (12) | 13190.5 (S3 13190.5) | 12 S | 11.5 S | 12.5 S | 13.5 S | 14.5 S | 15.5 S |
| Mon 16 Nov 20:00 | sell | 13184.7 | 13196.7 (12) | 13190.5 (S3 13190.5) | 12 S | 9.3 S | 10.3 S | 11.3 S | 12.3 S | 13.3 S |
| Tue 17 Nov 17:16 | buy | 13225.1 | 13213.1 (12) | 13219.8-13224.5 (turning low 13219.8, turning low 13219.9, new york session high 13221.4, previous day high 13224.5, london session high 13224.5, turning high 13224.5) | 12 S | 7.3 S | 8.3 S | 9.3 S | 10.3 S | 11.3 S |
| Wed 18 Nov 12:37 | sell | 13156.4 | 13168.4 (12) | 13166.9-13168 (new york session high 13166.9, previous day low 13168, turning low 13168) | 12 S | 15.1 S | 16.1 S | 17.1 S | 18.1 - | 19.1 - |

The stop prices at each buffer (a sell: the group's top + buffer + the spread when it opened; a buy: the group's bottom − buffer):

| Opened (UK) | Strategy | Way | Spread | +2 | +3 | +4 | +5 | +6 |
|---|---|---|---|---|---|---|---|---|
| Mon 09 Nov 06:12 | level reversal | buy | 1.5 | 13376.4 | 13375.4 | 13374.4 | 13373.4 | 13372.4 |
| Mon 09 Nov 13:55 | range trade | buy | 1.5 | 13414.1 | 13413.1 | 13412.1 | 13411.1 | 13410.1 |
| Mon 09 Nov 14:55 | range trade | buy | 0.9 | 13406 | 13405 | 13404 | 13403 | 13402 |
| Mon 09 Nov 15:16 | range trade | buy | 0.9 | 13399.7 | 13398.7 | 13397.7 | 13396.7 | 13395.7 |
| Mon 09 Nov 21:02 | EMA pullback | buy | 0.9 | 13439.9 | 13438.9 | 13437.9 | 13436.9 | 13435.9 |
| Tue 10 Nov 05:01 | EMA pullback | buy | 1.5 | 13445.2 | 13444.2 | 13443.2 | 13442.2 | 13441.2 |
| Tue 10 Nov 06:12 | EMA pullback | buy | 1.5 | 13445.2 | 13444.2 | 13443.2 | 13442.2 | 13441.2 |
| Tue 10 Nov 07:21 | EMA pullback | buy | 1.5 | 13451.3 | 13450.3 | 13449.3 | 13448.3 | 13447.3 |
| Tue 10 Nov 14:06 | level reversal | sell | 1.5 | 13392.6 | 13393.6 | 13394.6 | 13395.6 | 13396.6 |
| Wed 11 Nov 07:32 | EMA pullback | sell | 1.5 | 13341.1 | 13342.1 | 13343.1 | 13344.1 | 13345.1 |
| Wed 11 Nov 08:16 | EMA pullback | sell | 1.5 | 13331.0 | 13332.0 | 13333.0 | 13334.0 | 13335.0 |
| Wed 11 Nov 10:51 | EMA pullback | sell | 1.5 | 13331.0 | 13332.0 | 13333.0 | 13334.0 | 13335.0 |
| Wed 11 Nov 11:13 | range trade | buy | 1.5 | 13310.2 | 13309.2 | 13308.2 | 13307.2 | 13306.2 |
| Wed 11 Nov 13:40 | level reversal | sell | 1.5 | 13299.5 | 13300.5 | 13301.5 | 13302.5 | 13303.5 |
| Wed 11 Nov 18:48 | EMA pullback | sell | 1.5 | 13289.9 | 13290.9 | 13291.9 | 13292.9 | 13293.9 |
| Wed 11 Nov 21:06 | EMA pullback | sell | 1.5 | 13289.9 | 13290.9 | 13291.9 | 13292.9 | 13293.9 |
| Thu 12 Nov 19:02 | EMA pullback | sell | 1.5 | 13237.6 | 13238.6 | 13239.6 | 13240.6 | 13241.6 |
| Thu 12 Nov 22:00 | EMA pullback | sell | 16.9 | 13253.0 | 13254.0 | 13255.0 | 13256.0 | 13257.0 |
| Thu 12 Nov 23:47 | EMA pullback | sell | 1.5 | 13237.6 | 13238.6 | 13239.6 | 13240.6 | 13241.6 |
| Fri 13 Nov 09:55 | range trade | buy | 1.5 | 13225.1 | 13224.1 | 13223.1 | 13222.1 | 13221.1 |
| Fri 13 Nov 10:28 | EMA pullback | sell | 1.5 | 13228.8 | 13229.8 | 13230.8 | 13231.8 | 13232.8 |
| Mon 16 Nov 06:50 | level reversal | sell | 1.5 | 13203.5 | 13204.5 | 13205.5 | 13206.5 | 13207.5 |
| Mon 16 Nov 08:40 | level reversal | buy | 1.5 | 13207.3 | 13206.3 | 13205.3 | 13204.3 | 13203.3 |
| Mon 16 Nov 09:50 | level reversal | sell | 1.5 | 13194.0 | 13195.0 | 13196.0 | 13197.0 | 13198.0 |
| Mon 16 Nov 10:50 | EMA pullback | sell | 1.5 | 13194.0 | 13195.0 | 13196.0 | 13197.0 | 13198.0 |
| Mon 16 Nov 12:37 | level reversal | sell | 1.5 | 13203.5 | 13204.5 | 13205.5 | 13206.5 | 13207.5 |
| Mon 16 Nov 14:26 | EMA pullback | sell | 1.5 | 13203.5 | 13204.5 | 13205.5 | 13206.5 | 13207.5 |
| Mon 16 Nov 14:57 | EMA pullback | sell | 1.5 | 13194.0 | 13195.0 | 13196.0 | 13197.0 | 13198.0 |
| Mon 16 Nov 15:50 | EMA pullback | sell | 1.5 | 13188.1 | 13189.1 | 13190.1 | 13191.1 | 13192.1 |
| Mon 16 Nov 16:53 | EMA pullback | sell | 1.5 | 13194.0 | 13195.0 | 13196.0 | 13197.0 | 13198.0 |
| Mon 16 Nov 17:27 | range trade | sell | 1.5 | 13203.5 | 13204.5 | 13205.5 | 13206.5 | 13207.5 |
| Mon 16 Nov 20:00 | EMA pullback | sell | 1.5 | 13194.0 | 13195.0 | 13196.0 | 13197.0 | 13198.0 |
| Tue 17 Nov 06:03 | level reversal | sell | 1.5 | 13203.5 | 13204.5 | 13205.5 | 13206.5 | 13207.5 |
| Tue 17 Nov 07:35 | level reversal | sell | 1.5 | 13197.9 | 13198.9 | 13199.9 | 13200.9 | 13201.9 |
| Tue 17 Nov 08:59 | range trade | sell | 1.5 | 13197.9 | 13198.9 | 13199.9 | 13200.9 | 13201.9 |
| Tue 17 Nov 10:05 | level reversal | sell | 1.5 | 13197.9 | 13198.9 | 13199.9 | 13200.9 | 13201.9 |
| Tue 17 Nov 16:22 | level reversal | buy | 1.5 | 13211.5 | 13210.5 | 13209.5 | 13208.5 | 13207.5 |
| Tue 17 Nov 17:16 | EMA pullback | buy | 1.5 | 13217.8 | 13216.8 | 13215.8 | 13214.8 | 13213.8 |
| Wed 18 Nov 12:37 | EMA pullback | sell | 1.5 | 13171.5 | 13172.5 | 13173.5 | 13174.5 | 13175.5 |

**Totals** (bot trades only; counts, not profit):

| Strategy | Trades | Stop | Stopped | Reached +8 | Reached target | Stop distance (min / median / max) |
|---|---|---|---|---|---|---|
| all three | 39 | actual | 29 | 12 | 7 | 6 / 12 / 22.5 |
| | | +2 | 33 | 9 | 4 | 3.1 / 7.9 / 22.3 |
| | | +3 | 29 | 12 | 8 | 4.1 / 8.9 / 23.3 |
| | | +4 | 29 | 12 | 8 | 5.1 / 9.9 / 24.3 |
| | | +5 | 27 | 13 | 9 | 6.1 / 10.9 / 25.3 |
| | | +6 | 25 | 14 | 9 | 7.1 / 11.9 / 26.3 |
| level reversal | 11 | actual | 5 | 7 | 3 | 9.8 / 14.4 / 22.5 |
| | | +2 | 9 | 3 | 1 | 3.1 / 6.2 / 9.0 |
| | | +3 | 8 | 4 | 2 | 4.1 / 7.2 / 10.0 |
| | | +4 | 8 | 4 | 2 | 5.1 / 8.2 / 11.0 |
| | | +5 | 8 | 5 | 2 | 6.1 / 9.2 / 12.0 |
| | | +6 | 6 | 6 | 2 | 7.1 / 10.2 / 13.0 |
| range trade | 7 | actual | 6 | 1 | 1 | 6 / 12 / 12 |
| | | +2 | 6 | 1 | 1 | 4.5 / 9.3 / 11.2 |
| | | +3 | 6 | 1 | 1 | 5.5 / 10.3 / 12.2 |
| | | +4 | 6 | 1 | 1 | 6.5 / 11.3 / 13.2 |
| | | +5 | 5 | 1 | 2 | 7.5 / 12.3 / 14.2 |
| | | +6 | 5 | 1 | 2 | 8.5 / 13.3 / 15.2 |
| EMA pullback | 21 | actual | 18 | 4 | 3 | 12 / 12 / 12 |
| | | +2 | 18 | 5 | 2 | 3.7 / 8.4 / 22.3 |
| | | +3 | 15 | 7 | 5 | 4.7 / 9.4 / 23.3 |
| | | +4 | 15 | 7 | 5 | 5.7 / 10.4 / 24.3 |
| | | +5 | 14 | 7 | 5 | 6.7 / 11.4 / 25.3 |
| | | +6 | 14 | 7 | 5 | 7.7 / 12.4 / 26.3 |

**Closed by you by hand** (IG's SYSTEM channel; kept apart, not in the totals):

| Opened (UK) | Strategy | Way | Entry | Stop it had | Nearest group beyond | +2 | +3 | +4 | +5 | +6 |
|---|---|---|---|---|---|---|---|---|---|---|
| Mon 09 Nov 08:25 | level reversal | buy | 13414.9 | 13389.6 (25.3) | 13413.2-13416.1 | 3.7 S | 4.7 S | 5.7 S | 6.7 S | 7.7 S |
| Tue 10 Nov 16:26 | level reversal | sell | 13321.0 | 13341.2 (20.2) | 13321.5-13321.5 | 4.0 S | 5.0 S | 6.0 S | 7.0 S | 8.0 S |

### A4. Trades skipped at each widest stop

A trade is skipped when its stop at that buffer would be further from the entry than the widest stop. Bot trades of the three strategies; the column header is the buffer.

| Widest stop | Strategy | +2 | +3 | +4 | +5 | +6 |
|---|---|---|---|---|---|---|
| 15 | all three | 4 | 4 | 5 | 5 | 9 |
|  | level reversal | 0 | 0 | 0 | 0 | 0 |
|  | range trade | 0 | 0 | 0 | 0 | 1 |
|  | EMA pullback | 4 | 4 | 5 | 5 | 8 |
| 20 | all three | 1 | 2 | 2 | 2 | 3 |
|  | level reversal | 0 | 0 | 0 | 0 | 0 |
|  | range trade | 0 | 0 | 0 | 0 | 0 |
|  | EMA pullback | 1 | 2 | 2 | 2 | 3 |
| 25 | all three | 0 | 0 | 0 | 1 | 1 |
|  | level reversal | 0 | 0 | 0 | 0 | 0 |
|  | range trade | 0 | 0 | 0 | 0 | 0 |
|  | EMA pullback | 0 | 0 | 0 | 1 | 1 |

Which trades those are:

| Opened (UK) | Strategy | Way | Stop distance at +2 / +3 / +4 / +5 / +6 |
|---|---|---|---|
| Mon 09 Nov 15:16 | range trade | buy | 11.2 / 12.2 / 13.2 / 14.2 / 15.2 |
| Wed 11 Nov 10:51 | EMA pullback | sell | 14.0 / 15.0 / 16.0 / 17.0 / 18.0 |
| Wed 11 Nov 18:48 | EMA pullback | sell | 16.4 / 17.4 / 18.4 / 19.4 / 20.4 |
| Wed 11 Nov 21:06 | EMA pullback | sell | 19.2 / 20.2 / 21.2 / 22.2 / 23.2 |
| Thu 12 Nov 19:02 | EMA pullback | sell | 12.0 / 13.0 / 14.0 / 15.0 / 16.0 |
| Thu 12 Nov 22:00 | EMA pullback | sell | 22.3 / 23.3 / 24.3 / 25.3 / 26.3 |
| Mon 16 Nov 14:26 | EMA pullback | sell | 11.4 / 12.4 / 13.4 / 14.4 / 15.4 |

The 12 November 22:00 sell opened at the 22:00 rollover, and the bot recorded a 16.9-pip spread then. A sell's stop includes the spread at entry, which is why its distances are the widest.
| Mon 16 Nov 16:53 | EMA pullback | sell | 11.5 / 12.5 / 13.5 / 14.5 / 15.5 |
| Wed 18 Nov 12:37 | EMA pullback | sell | 15.1 / 16.1 / 17.1 / 18.1 / 19.1 |

### A2. Stops inside a level group, hit by a spike that turned back

Every live trade the bot closed since 9 November (72, all strategies; the 10 you closed by hand left out). "Inside a level group": the stop, on the chart (sell) price (a sell's stop minus the spread at entry), between the lowest and highest level of a group of two or more levels as the bot grouped them when the trade opened. "A spike that turned back": the 5-minute candle that stopped it closed back on the trade's side of the stop. Trades whose stop had been moved by the bounce's or a session strategy's trail are counted only where noted, since their stop at the end was no longer the stop they opened with.

| | Trades | Stopped | Stop candle closed back (spike) |
|---|---|---|---|
| All bot trades | 72 | 43 | 25 |
| Stop inside a level group | 16 | 11 | 7 |
| A level within 1 pip beyond the stop | 10 | 3 | 1 |
| A level within 2 pips beyond the stop | 28 | 16 | 10 |
| A level within 3 pips beyond the stop | 34 | 21 | 12 |
| A level within 5 pips beyond the stop | 56 | 35 | 20 |

The trades whose stop sat inside a level group:

| Opened (UK) | Strategy | Way | Stop (chart price) | Group | How it closed | Stop candle | Closed back | Best from entry in the 6 hours after |
|---|---|---|---|---|---|---|---|---|
| Mon 09 Nov 06:12 | level reversal | buy | 13372.5 (13372.5) | 13369.4-13373.9 (R1 13369.4, turning low 13373.9) | take profit hit at IG |  |  |  |
| Mon 09 Nov 15:16 | range trade | buy | 13404.9 (13404.9) | 13401.7-13406.5 (turning low 13401.7, turning low 13402.7, new york session high 13404.1, turning high 13404.1, new york session low 13404.5, turning high 13406.0, turning high 13406.5) | stopped by IG | 15:20 | no | 31.9 |
| Tue 10 Nov 07:21 | EMA pullback | buy | 13444.1 (13444.1) | 13441.9-13446.6 (new york session high 13441.9, previous day high 13443.2, turning low 13445.2, london session low 13446.6) | stopped by IG | 09:00 | no | -15.3 |
| Tue 10 Nov 07:55 | Bollinger bounce | sell | 13455.6 (13454.1) | 13453.3-13457.9 (turning low 13453.3, london session high 13457.9) | stopped by IG | 08:00 | yes | 59.0 |
| Tue 10 Nov 08:20 | Bollinger bounce | sell | 13454.9 (13454.0) | 13453.3-13457.9 (turning low 13453.3, london session high 13457.9) | stopped by IG | 08:20 | yes | 62.8 |
| Tue 10 Nov 13:56 | slow grind | sell | 13407.2 (13405.7) | 13401.7-13406.5 (turning low 13401.7, turning low 13402.7, turning high 13404.1, turning high 13406.0, turning high 13406.5) | close |  |  |  |
| Tue 10 Nov 14:06 | level reversal | sell | 13407.4 (13405.9) | 13401.7-13406.5 (turning low 13401.7, turning low 13402.7, turning high 13404.1, turning high 13406.0, turning high 13406.5) | take profit hit at IG |  |  |  |
| Wed 11 Nov 07:32 | EMA pullback | sell | 13342.9 (13341.4) | 13341.4-13344.9 (turning low 13341.4, london session high 13344.9) | take profit hit at IG |  |  |  |
| Wed 11 Nov 08:36 | Bollinger bounce | buy | 13314.1 (13314.1) | 13312.2-13314.2 (previous day low 13312.2, new york session low 13312.2, turning low 13312.2, london session low 13314.2) | stopped by IG | 09:30 | yes | 3.5 |
| Mon 16 Nov 09:50 | level reversal | sell | 13204.3 (13202.8) | 13202-13205.9 (previous day low 13202, new york session low 13204.3, S1 13205.9) | stopped by IG | 12:20 | yes | 6.6 |
| Mon 16 Nov 10:50 | EMA pullback | sell | 13199.1 (13197.6) | 13196.3-13200 (S2 13196.3, round number 13200) | stopped by IG | 12:10 | no | 6.8 |
| Mon 16 Nov 14:26 | EMA pullback | sell | 13204.1 (13202.6) | 13202-13205.9 (previous day low 13202, new york session low 13204.3, new york session high 13205.2, S1 13205.9) | stopped by IG | 09:45 | yes | 17.8 |
| Mon 16 Nov 14:57 | EMA pullback | sell | 13199.3 (13197.8) | 13196.3-13200 (S2 13196.3, round number 13200) | stopped by IG | 15:15 | yes | 8.8 |
| Mon 16 Nov 17:27 | range trade | sell | 13205.7 (13204.2) | 13202-13205.9 (previous day low 13202, new york session low 13204.3, new york session high 13205.2, turning high 13205.2, S1 13205.9) | close |  |  |  |
| Tue 17 Nov 10:05 | Bollinger bounce | sell | 13201.9 (13200.4) | 13200-13204.4 (round number 13200, turning high 13202.5, london session high 13204.4) | stopped by IG | 14:05 | yes | 0.1 |
| Wed 18 Nov 12:37 | EMA pullback | sell | 13168.4 (13166.9) | 13166.9-13168 (new york session high 13166.9, previous day low 13168, turning low 13168) | stopped by IG | 13:05 | no | -4.5 |

The stops with a level within 2 pips beyond them (the 17 November 09:45 kind: just in front of a level):

| Opened (UK) | Strategy | Way | Stop (chart price) | Next level beyond, pips | How it closed | Stop candle | Closed back |
|---|---|---|---|---|---|---|---|
| Mon 09 Nov 14:55 | range trade | buy | 13409.3 (13409.3) | new york session low 13408, 1.3 | stopped by IG | 14:55 | yes |
| Mon 09 Nov 15:16 | range trade | buy | 13404.9 (13404.9) | new york session low 13404.5, 0.4 | stopped by IG | 15:20 | no |
| Mon 09 Nov 21:02 | EMA pullback | buy | 13431.6 (13431.6) | turning high 13430.3, 1.3 | stopped by IG | 22:00 | no |
| Tue 10 Nov 07:21 | EMA pullback | buy | 13444.1 (13444.1) | previous day high 13443.2, 0.9 | stopped by IG | 09:00 | no |
| Tue 10 Nov 08:45 | Bollinger bounce | sell | 13459.7 (13458.2) | london session high 13458.6, 0.4 | close |  |  |
| Tue 10 Nov 13:11 | breakout | sell | 13425.6 (13424.1) | london session high 13426, 1.9 | stopped by IG | 13:25 | no |
| Tue 10 Nov 13:30 | slow grind | sell | 13411.5 (13395.5) | turning low 13396.1, 0.6 | stopped by IG | 13:30 | yes |
| Tue 10 Nov 13:56 | slow grind | sell | 13407.2 (13405.7) | turning high 13406.0, 0.3 | close |  |  |
| Tue 10 Nov 14:06 | level reversal | sell | 13407.4 (13405.9) | turning high 13406.0, 0.1 | take profit hit at IG |  |  |
| Wed 11 Nov 08:13 | slow grind | sell | 13341.6 (13340.1) | turning low 13341.4, 1.3 | close |  |  |
| Wed 11 Nov 08:16 | EMA pullback | sell | 13335.1 (13333.6) | turning low 13334, 0.4 | take profit hit at IG |  |  |
| Wed 11 Nov 08:36 | Bollinger bounce | buy | 13314.1 (13314.1) | previous day low 13312.2, 1.9 | stopped by IG | 09:30 | yes |
| Wed 11 Nov 13:40 | level reversal | sell | 13307.3 (13305.8) | london session low 13307.4, 1.6 | take profit hit at IG |  |  |
| Wed 11 Nov 15:10 | Bollinger bounce | buy | 13267.3 (13267.3) | new york session low 13265.6, 1.7 | close |  |  |
| Wed 11 Nov 17:37 | slow grind | sell | 13286.8 (13285.9) | S1 13286.4, 0.5 | forced close |  |  |
| Thu 12 Nov 10:20 | breakout | buy | 13267.1 (13267.1) | new york session low 13265.6, 1.5 | stopped by IG | 11:20 | yes |
| Mon 16 Nov 09:50 | level reversal | sell | 13204.3 (13202.8) | new york session low 13204.3, 1.5 | stopped by IG | 12:20 | yes |
| Mon 16 Nov 10:25 | Bollinger bounce | buy | 13186.3 (13186.3) | london session low 13184.6, 1.7 | stopped by IG | 10:50 | no |
| Mon 16 Nov 14:26 | EMA pullback | sell | 13204.1 (13202.6) | new york session low 13204.3, 1.7 | stopped by IG | 09:45 | yes |
| Mon 16 Nov 15:47 | slow grind | sell | 13202.1 (13200.6) | previous day low 13202, 1.4 | forced close |  |  |
| Mon 16 Nov 17:27 | range trade | sell | 13205.7 (13204.2) | new york session low 13204.3, 0.1 | close |  |  |
| Mon 16 Nov 20:00 | EMA pullback | sell | 13196.7 (13195.2) | S2 13196.3, 1.1 | stopped by IG | 22:00 | yes |
| Tue 17 Nov 07:35 | level reversal | sell | 13205.1 (13203.6) | new york session high 13205.2, 1.6 | stopped by IG | 09:45 | yes |
| Tue 17 Nov 16:22 | level reversal | buy | 13196.3 (13196.3) | pivot 13194.4, 1.9 | forced close |  |  |
| Tue 17 Nov 16:46 | slow grind | buy | 13205.0 (13205.0) | london session high 13204.4, 0.6 | forced close |  |  |
| Wed 18 Nov 07:30 | Asian range breakout | sell | 13192.2 (13190.7) | london session high 13192.7, 2.0 | stopped by IG | 09:25 | yes |
| Wed 18 Nov 09:30 | Bollinger bounce | buy | 13151.1 (13151.1) | round number 13150, 1.1 | stopped by IG | 11:00 | yes |
| Wed 18 Nov 12:37 | EMA pullback | sell | 13168.4 (13166.9) | previous day low 13168, 1.1 | stopped by IG | 13:05 | no |

### A3. How far price goes past a level group before turning back

The stored 5-minute candles from Wed 04 Nov 14:00 to Wed 18 Nov 14:00 UK (the last two weeks). Every rejection setup of the bot's own rejection part at a level (not the Bollinger bands only): 864 setups. **Turned back** = it reached its confirmation candle (391). The distance is the setup's furthest point (piercing candle to confirmation candle, as the level reversal measures it) past the far edge of the level group it was at (a sell: past the group's highest level). Negative: it turned before the far edge.

| Setups | How many | 10% | 25% | Median | 75% | 90% | 95% | Most |
|---|---|---|---|---|---|---|---|---|
| Turned back, all | 391 | -4.7 | -2.8 | -0.9 | 1.2 | 2.9 | 4.4 | 11.3 |
| Turned back, groups of 2+ levels | 304 | -5.1 | -3.4 | -1.3 | 0.7 | 2.8 | 4.4 | 11.3 |
| Turned back, single levels | 87 | -2.4 | -1.2 | 0.3 | 1.6 | 3.0 | 4.4 | 8.2 |
| Turned back after going past the far edge | 148 | 0.4 | 0.9 | 1.5 | 3.0 | 4.7 | 6.5 | 11.3 |

How many went how far past the far edge before turning back:

| Past the far edge | Turned back | Share | Share so far |
|---|---|---|---|
| not past it | 243 | 62% | 62% |
| 0 to 1 pip | 48 | 12% | 74% |
| 1 to 2 | 41 | 10% | 85% |
| 2 to 3 | 24 | 6% | 91% |
| 3 to 4 | 11 | 3% | 94% |
| 4 to 5 | 11 | 3% | 97% |
| 5 to 6 | 4 | 1% | 98% |
| 6 to 8 | 5 | 1% | 99% |
| over 8 | 4 | 1% | 100% |

For comparison, the 473 setups that did not turn back (cancelled: price went on past the rejection candle; or expired) had gone past the far edge by: median 0.1, 75% 2.3, 90% 5.0, 95% 7.2 pips by the time they ended (measured only to their rejection candle).


## Part B: what was built

| Switch (`.env`, off if left out) | What it does while on | Where |
|---|---|---|
| `SCALE_OUT_REVERSAL` | Level reversal and range trade only. At 8 pips in profit (on the price it would close at, as the trail measures), half is closed and the stop on the rest is moved at IG to 2 pips in profit. The rest runs on its existing exits: the level reversal's 20-pip take profit, the range trade's close at the opposite band, the 20:30 and pre-news closes. If the range trade reaches the opposite band before +8, it closes in full as now. The stop move uses the trail fix's handling: the nearest level IG allows, a refused move tried 3 times, then one alert. | `trade_manager/manager.py` (`step`, `on_bar`), `trading/engine.py` (after a restart) |
| `TRAIL_NO_LOSS` | The bounce's and the three session strategies' trail never moves the stop to the losing side of the entry (IG's fill, your answer). A trail level worse than the entry puts the stop at the entry. A candle with a spread over `rejection.max_spread_pips` (3) is left out of the last 3 candles, and the last 3 normal candles are used (your answer). | `trade_manager/manager.py` (`_trail`, `_spike`) |
| `LR_ENTRY_NEAR_LEVEL` | A level reversal opens only if its entry is within 6 pips of the level its rules 2, 7 and 8 picked. Otherwise it is recorded as refused with the distance: "LR_ENTRY_NEAR_LEVEL: the entry 13217.2 is 17.2 pips from the level it traded (round number 13200), more than 6". | `strategies/common.py` (`near_level_reasons`) |
| (no switch) | At start-up, one log line: "Switches from .env: PAIRS_ON=GBPUSD, NEW_TRADES_FROM=06:00, … TAKE_PROFIT_PIPS=100", every switch and its setting. | `prices/service.py` (`switches_line`) |

**Filled in by me, for you to confirm:**
1. **A replayed candle that reaches both +8 and the opposite band:** the bot only sees whole 5-minute candles, so it can't tell which came first. Live, it decides on each price as it comes. I take the band as first if it is nearer the entry than +8.
2. **The price of the half:** +8 from the fill, or the candle's open if it opened beyond +8. This is the same way the take profit is priced.
3. **Order of events:**
   - The half close counts only once IG confirms it, and only then is the stop moved.
   - A candle that hits the stop and reaches +8 is a stop, as for the take profit today: the stop is checked first.
4. **After a restart:**
   - A trade whose half was closed keeps its half.
   - If its stop move had not been confirmed, the move is sent again.
5. **Give-up message:** if IG refuses the +2 move 3 times, the alert says the move is not tried again (the trail's message says the trail is worked out again, which doesn't apply here).

**Tests:** `tests/technical/test_entries_exits.py`, 18 tests:
- the scale-out on a sell, its +2 stop and the rest stopped there;
- the rest running on to the take profit;
- switch off;
- the range trade at the band before +8, and after its scale-out;
- 3 refused moves;
- the 17 November trail on the stored candles, on and off;
- spike candles;
- the 6-pip rule and its refusal text;
- the start-up line.

Settings tests cover the new values and switches. The full suite: 2,484 passed (with LEVEL_STOPS).

## Part B: the days

Full wired path: the engine in paper mode, a pretend IG, the stored candles (`research/analyser_control_days.py`). Today's live switches, including the three analyser-control switches, plus the new switch(es) as stated. Paper trades open at the strategy's entry price, so a fill can differ from live by the spread or slippage. For example, the 10:05 bounce was filled at 13189.9 live and 13190.3 here.

### Tuesday 17 November

| Trade | All new switches off | `SCALE_OUT_REVERSAL` only | `TRAIL_NO_LOSS` only | `LR_ENTRY_NEAR_LEVEL` only | All three on |
|---|---|---|---|---|---|
| 06:00 level reversal sell at 13198.8 | +3.2 (forced close) | +3.2 (forced close) | +3.2 (forced close) | +3.2 (forced close) | +3.2 (forced close) |
| 10:05 Bollinger bounce sell at 13190.3 | +8.7 (stopped by IG) | +8.7 (stopped by IG) | +8.7 (stopped by IG) | +8.7 (stopped by IG) | +8.7 (stopped by IG) |
| 16:20 level reversal buy at 13217.2 | -9.1 (forced close) | +5.0 (stopped by IG) | -9.1 (forced close) | not opened | not opened |
| 16:45 slow grind buy at 13218.4 | -10.3 (forced close) | -10.3 (forced close) | -10.3 (forced close) | -10.3 (forced close) | -10.3 (forced close) |
| 17:15 EMA pullback buy at 13223.3 | -12.0 (stopped by IG) | -12.0 (stopped by IG) | -12.0 (stopped by IG) | -12.0 (stopped by IG) | -12.0 (stopped by IG) |
| 18:35 Bollinger bounce sell at 13219.7 | +8.6 (forced close) | +8.6 (forced close) | +8.6 (forced close) | +8.6 (forced close) | +8.6 (forced close) |

**The 10:05 bounce sell's first trail move:**
- **Switch off:** at 13:35 the stop moved to 13193.2, 2.9 pips on the losing side (live: 13193.2 against the 13189.9 entry).
- **`TRAIL_NO_LOSS` on:**
  - The 13:30 candle (spread 6.5 at its open) and the 13:25 candle (spread 4.6 at its close) are left out.
  - The last 3 normal candles are 13:15, 13:20 and 13:35, giving 13193.8: still on the losing side.
  - So the stop goes to the entry: 13190.3 in the replay (13189.9 with the live fill; the technical test checks this on the stored candles).
  - Then 13189.8 at 13:40 and 13181.6 at 13:45. The trade ends the same in this paper replay, at +8.7, because paper has no IG refusals. Live, IG refused the 13:45 level.

**The 16:20 level reversal buy (entry 13217.2):**
- **Its level:** the level the strategy picked is the round number 13200, 17.2 pips from the entry. (You estimated about 15; the record's "level" is 13200.)
- **`LR_ENTRY_NEAR_LEVEL` on:** it does not open, and is recorded as refused with that distance.
- **`SCALE_OUT_REVERSAL` only:** it opens and reaches +8 at 18:00. Half closes at 13226.7 (+8.0) and the stop moves to 13220.7 (+2.0). The rest is stopped there at 19:55: +5.0 in all, against −9.1 with the switch off (closed at 20:30).

**Level reversals and range trades that reached +8 on 17 November:** only the 16:20 buy (above). The 06:00 level reversal sell reached +7.5 at best and was closed before the news at +3.2. No range trade opened that day with today's live switches.

**Other level reversals the 6-pip rule refuses that day** (already refused by the analyser control before; the replay records both reasons):

- 06:15 level reversal sell: LR_ENTRY_NEAR_LEVEL: the entry 13193.4 is 6.6 pips from the level it traded (round number 13200), more than 6
- 06:20 level reversal sell: LR_ENTRY_NEAR_LEVEL: the entry 13192.7 is 7.3 pips from the level it traded (round number 13200), more than 6
- 07:35 level reversal sell: LR_ENTRY_NEAR_LEVEL: the entry 13192 is 8.0 pips from the level it traded (round number 13200), more than 6
- 07:40 level reversal sell: LR_ENTRY_NEAR_LEVEL: the entry 13189.3 is 10.7 pips from the level it traded (round number 13200), more than 6
- 09:00 level reversal sell: LR_ENTRY_NEAR_LEVEL: the entry 13189.5 is 10.5 pips from the level it traded (round number 13200), more than 6
- 10:05 level reversal sell: LR_ENTRY_NEAR_LEVEL: the entry 13189.8 is 10.2 pips from the level it traded (round number 13200), more than 6
- 13:15 level reversal sell: LR_ENTRY_NEAR_LEVEL: the entry 13188.9 is 11.1 pips from the level it traded (round number 13200), more than 6
- 14:55 level reversal sell: LR_ENTRY_NEAR_LEVEL: the entry 13191.3 is 8.7 pips from the level it traded (round number 13200), more than 6
- 15:00 level reversal sell: LR_ENTRY_NEAR_LEVEL: the entry 13190.4 is 9.6 pips from the level it traded (round number 13200), more than 6

### Trend days (the gate): Friday 6 and Tuesday 10 November

Today's live switches, all three new switches off vs on. **The trend group's trades are unchanged on both days, with the same entries and the same results.**

**Friday 6 November**: trend group unchanged (7 trades). The only change is the 12:40 level reversal sell, which scales out: half at 13389.6 (+8.0) at 12:45, the stop on the rest moved to 13395.6 (+2.0), and the rest closed before the news at +10.3, so +9.2 in all against +10.3.

| Trade | All new switches off | All three on |
|---|---|---|
| 04:10 EMA pullback sell at 13425.7 | +74.3 (forced close) | +74.3 (forced close) |
| 07:05 Asian range breakout sell at 13402.2 | +7.6 (stopped by IG) | +7.6 (stopped by IG) |
| 07:25 Bollinger bounce buy at 13411.3 | -12.0 (stopped by IG) | -12.0 (stopped by IG) |
| 07:50 Bollinger bounce buy at 13402.8 | -12.0 (stopped by IG) | -12.0 (stopped by IG) |
| 08:05 level reversal buy at 13403.4 | -15.1 (stopped by IG) | -15.1 (stopped by IG) |
| 12:40 level reversal sell at 13397.6 | +10.3 (forced close) | +9.2 (forced close) |
| 12:45 EMA pullback sell at 13394.6 | +43.2 (forced close) | +43.2 (forced close) |
| 13:00 slow grind sell at 13385.1 | -0.6 (close) | -0.6 (close) |
| 13:30 EMA pullback sell at 13377.5 | +26.1 (forced close) | +26.1 (forced close) |
| 13:45 slow grind sell at 13366.7 | +10.0 (close) | +10.0 (close) |
| 17:55 breakout sell at 13350.9 | -0.5 (forced close) | -0.5 (forced close) |

Refused by `LR_ENTRY_NEAR_LEVEL` that day: 08:15 buy (the entry 13407.7 is 8.6 pips from the level it traded (S2 13399.1), more than 6); 08:55 sell (the entry 13393.1 is 6.9 pips from the level it traded (round number 13400), more than 6); 13:10 sell (the entry 13383.3 is 16.7 pips from the level it traded (round number 13400), more than 6).

Scale-outs: 12:40 level reversal half closed at 13389.6 (+8.0) at 12:45 UTC.

**Tuesday 10 November**: trend group unchanged (3 trades). The two level reversals (14:05 and 16:35) are refused by `LR_ENTRY_NEAR_LEVEL`. Nothing else changes.

| Trade | All new switches off | All three on |
|---|---|---|
| 07:25 Asian range breakout buy at 13452.6 | -12.0 (stopped by IG) | -12.0 (stopped by IG) |
| 07:45 range trade sell at 13454.7 | -2.4 (close) | -2.4 (close) |
| 08:40 range trade sell at 13454.7 | +4.2 (close) | +4.2 (close) |
| 09:05 session sweep sell at 13435.8 | +5.6 (stopped by IG) | +5.6 (stopped by IG) |
| 09:40 Asian range breakout sell at 13430.3 | +11.2 (forced close) | +11.2 (forced close) |
| 13:55 slow grind sell at 13392.5 | +46.3 (forced close) | +46.3 (forced close) |
| 14:05 level reversal sell at 13389.1 | +20.0 (take profit hit at IG) | not opened |
| 16:35 level reversal sell at 13316.4 | -19.4 (stopped by IG) | not opened |
| 16:55 Bollinger bounce buy at 13319.8 | +19.2 (stopped by IG) | +19.2 (stopped by IG) |

Refused by `LR_ENTRY_NEAR_LEVEL` that day: 14:05 sell (the entry 13389.1 is 10.9 pips from the level it traded (round number 13400), more than 6); 14:35 sell (the entry 13384.6 is 15.4 pips from the level it traded (round number 13400), more than 6); 16:35 sell (the entry 13316.4 is 12.3 pips from the level it traded (S2 13328.7), more than 6); 18:15 buy (the entry 13335.7 is 7.0 pips from the level it traded (S2 13328.7), more than 6).

### Friday 13 November

**Friday 13 November**: trend group unchanged (1 trade).

| Trade | All new switches off | All three on |
|---|---|---|
| 08:20 Asian range breakout buy at 13241.8 | -12.0 (stopped by IG) | -12.0 (stopped by IG) |
| 08:40 session sweep sell at 13235.1 | +9.4 (stopped by IG) | +9.4 (stopped by IG) |
| 11:00 Bollinger bounce buy at 13223.7 | +9.3 (stopped by IG) | +9.3 (stopped by IG) |
| 15:05 Bollinger bounce sell at 13242.3 | +17.9 (stopped by IG) | +17.9 (stopped by IG) |
| 15:10 session sweep sell at 13235.8 | +11.4 (stopped by IG) | +11.4 (stopped by IG) |

**No trade changes on 13 November.** The same five trades open, with the same results. Trail moves change under `TRAIL_NO_LOSS`, and in both cases the trade still ended at the same trailed stop:
- **11:00 bounce buy (filled at 13225.2 in the replay):** at 13:30 the stop went to the entry, 13225.2, instead of 13224.8 (0.4 on the losing side). The off run then moved it to 13225.9 (13:35) and 13229.9 (13:40). With the switch on, those two moves did not happen. With the wide-spread candles of that time left out, the last 3 normal candles reached further back, and their level was below the entry, so the stop stayed at the entry. At 13:45 both runs moved it to 13234.5, and both were stopped there at 13:50 (+9.3).
- **15:05 bounce sell (filled at 13242.3):** at 15:25 the stop went to the entry, 13242.3, instead of 13244.6 (2.3 on the losing side).

## LEVEL_STOPS: the level-based stop (your answers of 18 November 2026)

**Built** (switch `LEVEL_STOPS`, off if left out; `docs/DESIGN.md` section 4 "Level-based stops"; `docs/SETTINGS.md`):
- **Which trades:** the range trade, the level reversal and the EMA pullback.
- **Where the stop goes:** 5 pips (`level_stops.beyond_group_pips`) beyond the far edge of the nearest level group beyond the entry on the stop side, using the bot's own level list and grouping on the candle the trade is checked on.
  - A sell: 5 pips above the group's highest level, plus IG's spread when the order is sent, **capped at 3 pips** (`level_stops.max_spread_pips`, your answer).
  - A buy: 5 pips below the group's lowest level.
- **What it replaces:** the fixed 12 pips, and the level reversal's 6 beyond the furthest point.
- **Widest stop 20 pips** (`level_stops.widest_stop_pips`): a wider level-based stop means the trade does not open. It is recorded as refused with the distance ("LEVEL_STOPS: the stop ... is ... pips from the entry, more than 20").
- **No group within 20 pips:** a group counts only if its far edge is within 20 pips of the entry. With none, the strategy keeps its own stop (your answers).
- **IG refuses the opening order because of its stop** (e.g. the level too close to IG's price in a news spread spike): it is recorded as refused with IG's reason and you get one alert with IG's minimum stop distance. It is not sent again. This was already the order sender's behaviour for every opening order; a new test holds the level stop to it.
- **Where in the code:** `strategies/common.py` (`level_stop_context`, `level_stop_price`), `strategies/replay.py` (the group attached to each candidate), `orders/sender.py` (`_stop_distance`: the spread, the cap, the widest stop).
- **Replay harness change:** paper replays now give the order sender the candle's real buy and sell prices, so a sell's spread is known (it was 0 before). Fills and the other stops are unchanged.

**Before the cap**, the 6 November 13:30 EMA pullback sell was refused. It triggered in the payrolls candle, whose open spread was 15.7 pips: 13378.4 + 5 + 15.7 = 13399.1, 21.6 pips from the 13377.5 entry. **With the 3-pip cap it opens again:** 13378.4 + 5 + 3 = 13386.4, 8.9 pips, and it ends as with the switch off (+26.1).

**The days** (today's live switches; `LEVEL_STOPS` off vs on, the other new switches off):

| Day | Trade | Off | `LEVEL_STOPS` on | The level-based stop |
|---|---|---|---|---|
| Fri 6 Nov | 04:10 EMA pullback sell (trend group) | +74.3 | +74.3 | 13436.8, 11.1 pips (group 13426.4 to 13430.3) |
| Fri 6 Nov | 08:05 level reversal buy | −15.1 (stopped) | −9.9 (stopped) | 13395.0, 9.9 pips (group 13400 to 13402.7) |
| Fri 6 Nov | 08:55 level reversal sell | not opened | **new**, −9.5 (stopped) | 13402.6, 9.5 pips. It opens because the 08:05 one closed sooner (one level reversal at a time) |
| Fri 6 Nov | 12:40 level reversal sell | +10.3 | +10.3 | 13406.5, 8.9 pips |
| Fri 6 Nov | 12:45 EMA pullback sell (trend group) | +43.2 | +43.2 | 13406.5, 11.9 pips |
| Fri 6 Nov | 13:30 EMA pullback sell (trend group) | +26.1 | +26.1 | 13386.4, 8.9 pips (the spread capped at 3) |
| Tue 10 Nov | 07:45 range trade sell | −2.4 | −2.4 | 13464.4, 9.7 pips |
| Tue 10 Nov | 08:40 range trade sell | +4.2 | +4.2 | 13469.8, 15.1 pips |
| Tue 10 Nov | 14:05 level reversal sell | +20.0 | +20.0 | 13406.5, 17.4 pips |
| Tue 10 Nov | 16:35 level reversal sell | −19.4 (stopped) | −18.8 (stopped) | 13335.2, 18.8 pips (S2 13328.7) |
| Fri 13 Nov | none of the three strategies opened | | | |
| Tue 17 Nov | 06:00 level reversal sell | +3.2 | +3.2 | 13206.5, 7.7 pips (round number 13200) |
| Tue 17 Nov | 16:20 level reversal buy | −9.1 (closed at 20:30) | −10.2 (stopped) | 13208.5, 10.2 pips (group 13213.5 to 13218.5) |
| Tue 17 Nov | 17:15 EMA pullback buy (trend group) | −12.0 (stopped) | −10.0 (stopped) | 13214.8, 10.0 pips (group 13219.8 to 13224.5) |

- **Trend days (the gate):** on 6 and 10 November no trend trade is lost or changed with the cap. Every trend-group trade opens, with the same result.
- **17 November trend group:** the 17:15 EMA pullback buy changes, −12.0 becomes −10.0, stopped at its 10-pip level-based stop instead of the fixed 12.
- **13 November:** nothing changes. No range trade, level reversal or EMA pullback opened that day.
- **Raw data:** `day_<date>_levels.json` beside this report, and the stops in `level_stops_used.json`. The stops in the last column are worked out again from each trade's candle (the spread from the candle's open, capped at 3), as the bot does.

**Tests:** in `tests/technical/test_entries_exits.py`:
- the nearest group either way;
- no group within 20 (the strategy's own stop);
- 5 beyond the group;
- the order sender adding the spread, the 3-pip cap (the 6 November 13:30 case) and the 20-pip refusal;
- IG's refusal recorded once and not resent;
- off as before.

Settings tests cover `level_stops`.

## Questions

Your answers of 18 November 2026 are built:
- buffer 5, widest stop 20;
- the five filled-in details accepted;
- 13200 as the 16:20 trade's level;
- with no group within 20 pips, the strategy's own stop;
- "within 20" measured to the group's far edge;
- the spread for a sell capped at 3 pips;
- IG's refusal recorded, not retried.

No open questions.

## Files

- Code: listed in "Part B: what was built". Docs: `docs/DESIGN.md` (3.6 rule 9; section 4 "Trail never at a loss", "Scale-out", "Holding"; 13 switches), `docs/SETTINGS.md`, `.env.example`.
- Tools: `research/stop_buffers.py` (Part A, read-only), `research/analyser_control_days.py` (now also keeps the trade manager's decisions and each trade's reference).
- Raw results beside this report: `partA_*.json`; `day_<date>_<switches>.json` for each replay.
