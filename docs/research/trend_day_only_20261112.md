# Trading only on days that are trending by 09:00, 2024 to 2026

Thursday 12 November 2026, UK. This is read-only research: **nothing in the bot was changed**. There were no IG calls and no restart, and nothing was written outside `data/research/`.

## Summary

**The owner's idea.** The bot makes money on trend days and loses it on normal days. So if a day isn't trending by 09:00, stop trading for the rest of that day.

**The versions:**

1. The current rules on every day.
2. On a day that has not moved far enough by 09:00 UK, no new trades from 09:00. Trades already open run to their normal exits.
3. The same, and also no new trades at all before 09:00, on any day.

"Moved far enough" is the net move from the 06:00 (owner) or 07:00 (the earlier research) open to the last close before 09:00 UK, either way, of at least 20 or 30 pips. That makes four versions of each.

**The data:**

- **The bot's own IG candles, 25 October to 12 November 10:55 UTC.** These are real replays of each version through the bot's own code.
- **The tick replay weeks:** January to March 2026 (13 weeks), and four random weeks from 2024 and 2025. Each version is the current rules' tick trades with the rule applied afterwards. A full tick replay of every version would take days. On the candle data that shortcut is within 16 pips of a real replay for version 2, and within 62 pips for version 3 (table below).
- Every run uses the rules as they stood before today's trend proof change (`9aa9c19`).

**The kinds of day,** as in the earlier day-type research, midnight to midnight UK, on IG's bid:

- trended: closed 60+ pips from its open;
- came back: moved 30 to 40 one way, then gave back at least half;
- other: everything else.

"Normal days" below are came back plus other.

### What switching off saves on normal days, and what it misses on trend days

Each cell gives the change against the current rules on normal days, then on trend days, then in all. A plus is better than the current rules. The candle data leaves out today, which isn't finished.

| Version | Bot's IG candles, 26 Oct – 11 Nov (real replays) | Tick weeks, Jan–Mar 2026 (current rules' trades, filtered) | Tick weeks, random weeks (current rules' trades, filtered) |
|---|---|---|---|
| 2. from 06:00, 20+ pips | normal days -17.9 · trend days -153.7 · in all -171.6 | normal days +714.7 · trend days -505.5 · in all +209.2 | normal days +233.0 · trend days +62.1 · in all +295.2 |
| 2. from 06:00, 30+ pips | normal days +7.2 · trend days -110.4 · in all -103.2 | normal days +952.4 · trend days -495.4 · in all +457.0 | normal days +233.0 · trend days +84.9 · in all +318.0 |
| 2. from 07:00, 20+ pips | normal days -17.9 · trend days -198.2 · in all -216.1 | normal days +831.1 · trend days -392.4 · in all +438.6 | normal days +224.4 · trend days +75.4 · in all +299.8 |
| 2. from 07:00, 30+ pips | normal days +7.2 · trend days -177.8 · in all -170.6 | normal days +1,008.4 · trend days -495.4 · in all +513.0 | normal days +224.4 · trend days +142.8 · in all +367.2 |
| 3. from 06:00, 20+ pips | normal days -436.4 · trend days -1,003.0 · in all -1,439.4 | normal days +1,213.7 · trend days -273.0 · in all +940.8 | normal days +612.0 · trend days -313.6 · in all +298.4 |
| 3. from 06:00, 30+ pips | normal days -399.2 · trend days -932.7 · in all -1,331.8 | normal days +1,451.4 · trend days -262.8 · in all +1,188.6 | normal days +612.0 · trend days -290.8 · in all +321.2 |
| 3. from 07:00, 20+ pips | normal days -436.4 · trend days -1,032.5 · in all -1,468.9 | normal days +1,330.1 · trend days -159.9 · in all +1,170.2 | normal days +603.4 · trend days -300.4 · in all +303.0 |
| 3. from 07:00, 30+ pips | normal days -399.2 · trend days -960.8 · in all -1,360.0 | normal days +1,507.4 · trend days -262.8 · in all +1,244.6 | normal days +603.4 · trend days -232.9 · in all +370.4 |

**On the bot's own IG candles since 25 October, every version is worse.**

- **Version 2 loses 102 to 215 pips.**
  - On normal days it saves almost nothing (−17.9 to +7.2). The current rules made +405 on normal days here (+433.6 on "other" days, −28.4 on the one came-back day), not a loss.
  - On trend days it misses 110 to 198 pips, because the test often failed on them:
    - 10 November never passed (+9.5 from 06:00, +6.6 from 07:00);
    - 11 November passed only from 06:00 at 20 pips (−20.7; −14.0 from 07:00);
    - 6 November passed at 30 pips only from 06:00 (−31.7; −21.4 from 07:00);
    - 9 November passed only at 20 pips (+28.8 from 06:00, +22.3 from 07:00).

    On a day that failed, its trades from 09:00 were lost.
  - The least bad is from 06:00, 30+ pips: +1,251.0 against +1,353.3 (−102.4).
- **Version 3 loses 1,319 to 1,456 pips.** Here the bot made **+1,188 of its +1,353 before 09:00**:
  - +783 on trend days;
  - +399 on other days;
  - +17.5 on the came-back day;
  - −11.8 on today's unfinished morning.

  Stopping all trading before 09:00 throws that away.

**On the tick weeks, every version comes out better, but only because the bot was losing there.**

- The current rules lose −1,607.2 in January to March 2026 (754 trades) and −594.7 in the random weeks (220 trades), on vendor ticks priced with IG's typical spread.
- **The 09:00 test doesn't pick better trades.** In January to March, the trades each version keeps are **worse** per trade than the current rules' (−3.06 to −5.76 pips, against −2.13). The gain comes only from trading less.
  - Version 2 cuts the trades by half to two thirds and saves 209 to 513.
  - Version 3 cuts them by 78 to 92% and saves 941 to 1,245.
  - Removing the same number of trades at random would save more, about 790 to 1,470 pips, because the trades kept are worse than average.
- **In the random weeks, version 2 picks slightly better trades:** −1.96 to −2.69 per trade, against −2.70. There, version 2 saves 224 to 233 pips on normal days, all on "other" days: it removes 67 to 76 of their 122 trades. Version 3 saves 603 to 612 on them.
  - On trend days version 2 also gains 62 to 143, because the trend days that failed the test lost money after 09:00.
  - Version 3 misses 233 to 314 there on trend days.
  - Only 20 days, so this is thin.
- **The 09:00 test catches few of the trend days in 2026.** Of 23 trend days in January to March, from 06:00 it passed 6 at 20+ pips and 2 at 30+. From 07:00 it passed 4 and 2. On the days that passed, 25 to 38% turned out to be trend days (6 of 16, 2 of 7, 4 of 16 and 2 of 6).
  - In the random weeks it was right on 16 of 18 passes, but there are only 20 days.
  - Since 25 October: 3 of 7 (06:00, 20+), 1 of 2 (06:00, 30+), 2 of 6 (07:00, 20+), and 0 of 1 (07:00, 30+).

**In short:**

- **Version 3 is harmful:** the bot's best trades since 25 October came before 09:00.
- **Version 2 also costs money on the bot's own candles since 25 October** (−103 to −216), where the bot is profitable. It saves money in 2024–2026 only because the bot loses on that data, and in January to March 2026 it keeps worse trades, not better ones.
- The early move alone does not tell trend days apart well enough. It caught 2 to 6 of 23 trend days in early 2026 and missed 10 and 11 November.
- Of version 2's four settings, from 06:00 30+ pips loses least on the bot's own candles (−102.4), and from 07:00 30+ saves most on the tick weeks (+513.0 and +367.2). No version does well on both.

## How it was done

- **Candle replays (the bot's own IG candles).**
  - **Candles:** a read-only copy of the bot's candle store, taken at 10:57 UTC today (`data/research/replay_stores/live_copy_20261112_1057/`). It ends with the candle that finished at 10:55 UTC.
  - **Code:** a frozen copy of `9aa9c19`, the rules before today's trend proof change, run in the research mode (`research.long_replay`). It has the same engine, strategies, safety rules, paper order sender and trade manager as the bot's own replay.
  - **The rule:** a research-only patch refuses a new trade (any strategy) at the moment it would be sent, using the 5-minute candle in which the entry was reached. Open trades are never closed by it.
  - **Check:** with no rule switched on, the research version gives the same 164 trades as the bot's own code, trade for trade. No candle reached both a trade's stop and its target in any run.
- **Tick weeks.**
  - The current rules' trades from the tick replay (`data/research/replay/tick_q1_2026/` and `tick_days_9aa9c19/`), with each version's rule applied by the entry time.
  - January to March 2026 ran on the same code as the candle replays. The four random weeks (2 June 2024, 4 August 2024, 20 April 2025, 31 August 2025) were re-run on that code too. An earlier run of them had picked up today's trend proof change part-way through.
  - **The shortcut against a real replay.** A real replay can differ from the filtered trades, because a trade that is refused can free the slot for another one (one trade per strategy at a time). On the candle data:
    - version 2: within 6 to 16 pips;
    - version 3: 14 to 62 pips, where refusing the morning trades lets more afternoon trades open.

    The table is below. The tick results for version 3 are therefore rougher.
- **The day test.**
  - **Prices:** the 5-minute candles at IG's bid (the sell price): the bot's own candles, or the tick replay's candles (the tick mid less half of IG's typical spread).
  - **The move:** the open of the 06:00 or 07:00 UK candle to the close of the candle ending at 09:00 UK, either way.
  - **The trading day** is the UK date. A trade from Sunday night's open counts as before Monday's 09:00.
  - **A day with no candles in the window** (a holiday) does not pass.
- **Day types:** the same rules as `early_day_type_20261111.md`, on the same candles. Trades are put in the day they opened.
- **Win and loss:** a trade with more than 0 pips is a win, below 0 a loss. **Times** are UK times.
- **Where things are:** the scripts and every run's trades are in `data/research/replay/trend_day_only_20261112/`. The repository commits only this file.

## Results

### The bot's own IG candles, 25 October to 12 November 10:55 UTC (real replays)

#### Totals

| Version | Trades | Won | Lost | Pips | Against current |
|---|---:|---:|---:|---:|---:|
| **1. Current rules** | 164 | 85 | 78 | **+1,353.3** |  |
| 2. from 06:00, 20+ pips | 127 | 69 | 58 | **+1,182.6** | -170.7 |
| 2. from 06:00, 30+ pips | 89 | 56 | 33 | **+1,251.0** | -102.4 |
| 2. from 07:00, 20+ pips | 119 | 66 | 53 | **+1,138.1** | -215.2 |
| 2. from 07:00, 30+ pips | 83 | 52 | 31 | **+1,183.6** | -169.8 |
| 3. from 06:00, 20+ pips | 65 | 23 | 42 | **-73.4** | -1,426.7 |
| 3. from 06:00, 30+ pips | 20 | 9 | 11 | **+34.2** | -1,319.2 |
| 3. from 07:00, 20+ pips | 56 | 20 | 36 | **-102.9** | -1,456.2 |
| 3. from 07:00, 30+ pips | 9 | 4 | 5 | **+6.0** | -1,347.2 |

#### By week: trades (won–lost) and pips

| Week from | **1. Current rules** | 2. from 06:00, 20+ pips | 2. from 06:00, 30+ pips | 2. from 07:00, 20+ pips | 2. from 07:00, 30+ pips |
|---|---:|---:|---:|---:|---:|
| 25 Oct – 30 Oct | 49 (28–20) +267.1 | 32 (20–12) +214.5 | 17 (13–4) +251.2 | 32 (20–12) +214.5 | 17 (13–4) +251.2 |
| 1 – 6 Nov | 78 (40–38) +814.1 | 65 (36–29) +848.8 | 58 (33–25) +837.2 | 65 (36–29) +848.8 | 52 (29–23) +769.8 |
| 8 – 12 Nov 10:55 UTC | 37 (17–20) +272.1 | 30 (13–17) +119.3 | 14 (10–4) +162.6 | 22 (10–12) +74.8 | 14 (10–4) +162.6 |
| **All** | **164 (85–78) +1,353.3** | **127 (69–58) +1,182.6** | **89 (56–33) +1,251.0** | **119 (66–53) +1,138.1** | **83 (52–31) +1,183.6** |

| Week from | **1. Current rules** | 3. from 06:00, 20+ pips | 3. from 06:00, 30+ pips | 3. from 07:00, 20+ pips | 3. from 07:00, 30+ pips |
|---|---:|---:|---:|---:|---:|
| 25 Oct – 30 Oct | 49 (28–20) +267.1 | 18 (8–10) -13.6 | 0 (0–0) +0.0 | 18 (8–10) -13.6 | 0 (0–0) +0.0 |
| 1 – 6 Nov | 78 (40–38) +814.1 | 29 (12–17) +10.5 | 20 (9–11) +34.2 | 29 (12–17) +10.5 | 9 (4–5) +6.0 |
| 8 – 12 Nov 10:55 UTC | 37 (17–20) +272.1 | 18 (3–15) -70.3 | 0 (0–0) +0.0 | 9 (0–9) -99.8 | 0 (0–0) +0.0 |
| **All** | **164 (85–78) +1,353.3** | **65 (23–42) -73.4** | **20 (9–11) +34.2** | **56 (20–36) -102.9** | **9 (4–5) +6.0** |

#### By the kind of day it turned out to be (in brackets: against the current rules)

| Version | trended | came back | other |
|---|---:|---:|---:|
| **1. Current rules** | 50 (29–21) +960.8 | 11 (5–6) -28.4 | 100 (50–49) +433.6 |
| 2. from 06:00, 20+ pips | 44 (25–19) +807.1 (-153.7) | 2 (2–0) +17.5 (+45.9) | 79 (41–38) +369.8 (-63.8) |
| 2. from 06:00, 30+ pips | 28 (22–6) +850.4 (-110.4) | 2 (2–0) +17.5 (+45.9) | 57 (31–26) +394.8 (-38.8) |
| 2. from 07:00, 20+ pips | 36 (22–14) +762.6 (-198.2) | 2 (2–0) +17.5 (+45.9) | 79 (41–38) +369.8 (-63.8) |
| 2. from 07:00, 30+ pips | 22 (18–4) +783.0 (-177.8) | 2 (2–0) +17.5 (+45.9) | 57 (31–26) +394.8 (-38.8) |
| 3. from 06:00, 20+ pips | 29 (8–21) -42.2 (-1,003.0) | 0 (0–0) +0.0 (+28.4) | 36 (15–21) -31.2 (-464.8) |
| 3. from 06:00, 30+ pips | 11 (5–6) +28.1 (-932.7) | 0 (0–0) +0.0 (+28.4) | 9 (4–5) +6.0 (-427.6) |
| 3. from 07:00, 20+ pips | 20 (5–15) -71.7 (-1,032.5) | 0 (0–0) +0.0 (+28.4) | 36 (15–21) -31.2 (-464.8) |
| 3. from 07:00, 30+ pips | 0 (0–0) +0.0 (-960.8) | 0 (0–0) +0.0 (+28.4) | 9 (4–5) +6.0 (-427.6) |

Today, Thursday 12 November, is not finished, so it has no type: the current rules made 3 (1–2) -12.7 on it up to 10:55 UTC (counted in the totals and by week, not in the table by kind of day).

### Pips per trade kept

| Version | Bot's IG candles, 25 Oct – 12 Nov | Tick weeks, Jan–Mar 2026 | Tick weeks, random weeks |
|---|---:|---:|---:|
| **1. Current rules** | +8.25 (164 trades) | -2.13 (754 trades) | -2.70 (220 trades) |
| 2. from 06:00, 20+ pips | +9.31 (127 trades) | -3.60 (388 trades) | -2.27 (132 trades) |
| 2. from 06:00, 30+ pips | +14.06 (89 trades) | -3.85 (299 trades) | -2.69 (103 trades) |
| 2. from 07:00, 20+ pips | +9.56 (119 trades) | -3.18 (368 trades) | -2.15 (137 trades) |
| 2. from 07:00, 30+ pips | +14.26 (83 trades) | -3.80 (288 trades) | -1.96 (116 trades) |
| 3. from 06:00, 20+ pips | -1.13 (65 trades) | -4.09 (163 trades) | -5.59 (53 trades) |
| 3. from 06:00, 30+ pips | +1.71 (20 trades) | -5.66 (74 trades) | -11.40 (24 trades) |
| 3. from 07:00, 20+ pips | -1.84 (56 trades) | -3.06 (143 trades) | -5.03 (58 trades) |
| 3. from 07:00, 30+ pips | +0.67 (9 trades) | -5.76 (63 trades) | -6.06 (37 trades) |

### The tick weeks (the current rules' tick trades, with each version's rule applied)

#### Jan–Mar 2026: totals

| Version | Trades | Won | Lost | Pips | Against current |
|---|---:|---:|---:|---:|---:|
| **1. Current rules** | 754 | 257 | 497 | **-1,607.2** |  |
| 2. from 06:00, 20+ pips | 388 | 116 | 272 | **-1,398.0** | +209.2 |
| 2. from 06:00, 30+ pips | 299 | 87 | 212 | **-1,150.2** | +457.0 |
| 2. from 07:00, 20+ pips | 368 | 114 | 254 | **-1,168.6** | +438.6 |
| 2. from 07:00, 30+ pips | 288 | 84 | 204 | **-1,094.2** | +513.0 |
| 3. from 06:00, 20+ pips | 163 | 49 | 114 | **-666.5** | +940.8 |
| 3. from 06:00, 30+ pips | 74 | 20 | 54 | **-418.6** | +1,188.6 |
| 3. from 07:00, 20+ pips | 143 | 47 | 96 | **-437.0** | +1,170.2 |
| 3. from 07:00, 30+ pips | 63 | 17 | 46 | **-362.6** | +1,244.6 |

#### Jan–Mar 2026: by week, trades (won–lost) and pips

| Week from | **1. Current rules** | 2. from 06:00, 20+ pips | 2. from 06:00, 30+ pips | 2. from 07:00, 20+ pips | 2. from 07:00, 30+ pips |
|---|---:|---:|---:|---:|---:|
| 04 Jan 2026 | 47 (20–27) +38.1 | 20 (7–13) -41.0 | 20 (7–13) -41.0 | 24 (7–17) -89.1 | 20 (7–13) -41.0 |
| 11 Jan 2026 | 52 (17–35) -120.9 | 26 (7–19) -119.9 | 16 (7–9) -5.9 | 16 (7–9) -5.9 | 16 (7–9) -5.9 |
| 18 Jan 2026 | 54 (19–35) -155.6 | 22 (3–19) -247.6 | 22 (3–19) -247.6 | 22 (3–19) -247.6 | 22 (3–19) -247.6 |
| 25 Jan 2026 | 65 (20–45) -242.4 | 21 (3–18) -183.2 | 21 (3–18) -183.2 | 21 (3–18) -183.2 | 21 (3–18) -183.2 |
| 01 Feb 2026 | 67 (21–46) -157.6 | 32 (10–22) -22.4 | 22 (9–13) +111.6 | 22 (9–13) +111.6 | 22 (9–13) +111.6 |
| 08 Feb 2026 | 52 (17–35) -171.9 | 26 (7–19) -150.2 | 20 (4–16) -154.9 | 33 (9–24) -155.4 | 20 (4–16) -154.9 |
| 15 Feb 2026 | 49 (19–30) +192.2 | 27 (11–16) +135.4 | 14 (3–11) -12.3 | 27 (11–16) +135.4 | 14 (3–11) -12.3 |
| 22 Feb 2026 | 47 (23–24) -14.6 | 18 (10–8) +62.2 | 18 (10–8) +62.2 | 26 (12–14) +22.3 | 18 (10–8) +62.2 |
| 01 Mar 2026 | 71 (21–50) -304.6 | 60 (20–40) -203.3 | 50 (18–32) -128.5 | 50 (18–32) -128.5 | 50 (18–32) -128.5 |
| 08 Mar 2026 | 86 (26–60) -224.6 | 56 (18–38) -172.6 | 36 (11–25) -138.8 | 44 (15–29) -108.0 | 36 (11–25) -138.8 |
| 15 Mar 2026 | 60 (18–42) -185.4 | 32 (6–26) -242.8 | 26 (3–23) -243.8 | 26 (3–23) -243.8 | 26 (3–23) -243.8 |
| 22 Mar 2026 | 73 (24–49) -291.6 | 41 (13–28) -160.4 | 27 (8–19) -115.6 | 50 (16–34) -224.2 | 16 (5–11) -59.6 |
| 29 Mar 2026 | 31 (12–19) +31.7 | 7 (1–6) -52.4 | 7 (1–6) -52.4 | 7 (1–6) -52.4 | 7 (1–6) -52.4 |
| **All** | **754 (257–497) -1,607.2** | **388 (116–272) -1,398.0** | **299 (87–212) -1,150.2** | **368 (114–254) -1,168.6** | **288 (84–204) -1,094.2** |

| Week from | **1. Current rules** | 3. from 06:00, 20+ pips | 3. from 06:00, 30+ pips | 3. from 07:00, 20+ pips | 3. from 07:00, 30+ pips |
|---|---:|---:|---:|---:|---:|
| 04 Jan 2026 | 47 (20–27) +38.1 | 0 (0–0) +0.0 | 0 (0–0) +0.0 | 4 (0–4) -48.1 | 0 (0–0) +0.0 |
| 11 Jan 2026 | 52 (17–35) -120.9 | 10 (0–10) -114.0 | 0 (0–0) +0.0 | 0 (0–0) +0.0 | 0 (0–0) +0.0 |
| 18 Jan 2026 | 54 (19–35) -155.6 | 8 (1–7) -105.1 | 8 (1–7) -105.1 | 8 (1–7) -105.1 | 8 (1–7) -105.1 |
| 25 Jan 2026 | 65 (20–45) -242.4 | 0 (0–0) +0.0 | 0 (0–0) +0.0 | 0 (0–0) +0.0 | 0 (0–0) +0.0 |
| 01 Feb 2026 | 67 (21–46) -157.6 | 10 (1–9) -133.9 | 0 (0–0) +0.0 | 0 (0–0) +0.0 | 0 (0–0) +0.0 |
| 08 Feb 2026 | 52 (17–35) -171.9 | 6 (3–3) +4.8 | 0 (0–0) +0.0 | 13 (5–8) -0.4 | 0 (0–0) +0.0 |
| 15 Feb 2026 | 49 (19–30) +192.2 | 13 (8–5) +147.7 | 0 (0–0) +0.0 | 13 (8–5) +147.7 | 0 (0–0) +0.0 |
| 22 Feb 2026 | 47 (23–24) -14.6 | 7 (4–3) +45.2 | 7 (4–3) +45.2 | 15 (6–9) +5.4 | 7 (4–3) +45.2 |
| 01 Mar 2026 | 71 (21–50) -304.6 | 42 (11–31) -290.0 | 32 (9–23) -215.2 | 32 (9–23) -215.2 | 32 (9–23) -215.2 |
| 08 Mar 2026 | 86 (26–60) -224.6 | 29 (9–20) -57.8 | 9 (2–7) -24.0 | 17 (6–11) +7.0 | 9 (2–7) -24.0 |
| 15 Mar 2026 | 60 (18–42) -185.4 | 13 (4–9) -62.8 | 7 (1–6) -63.7 | 7 (1–6) -63.7 | 7 (1–6) -63.7 |
| 22 Mar 2026 | 73 (24–49) -291.6 | 25 (8–17) -100.8 | 11 (3–8) -56.0 | 34 (11–23) -164.6 | 0 (0–0) +0.0 |
| 29 Mar 2026 | 31 (12–19) +31.7 | 0 (0–0) +0.0 | 0 (0–0) +0.0 | 0 (0–0) +0.0 | 0 (0–0) +0.0 |
| **All** | **754 (257–497) -1,607.2** | **163 (49–114) -666.5** | **74 (20–54) -418.6** | **143 (47–96) -437.0** | **63 (17–46) -362.6** |

#### Jan–Mar 2026: by the kind of day (in brackets: against the current rules)

| Version | trended | came back | other |
|---|---:|---:|---:|
| **1. Current rules** | 314 (122–192) +284.2 | 19 (5–14) -84.6 | 421 (130–291) -1,806.8 |
| 2. from 06:00, 20+ pips | 149 (47–102) -221.4 (-505.5) | 4 (2–2) -8.5 (+76.2) | 235 (67–168) -1,168.2 (+638.6) |
| 2. from 06:00, 30+ pips | 106 (31–75) -211.2 (-495.4) | 4 (2–2) -8.5 (+76.2) | 189 (54–135) -930.4 (+876.3) |
| 2. from 07:00, 20+ pips | 133 (44–89) -108.3 (-392.4) | 4 (2–2) -8.5 (+76.2) | 231 (68–163) -1,051.8 (+755.0) |
| 2. from 07:00, 30+ pips | 106 (31–75) -211.2 (-495.4) | 4 (2–2) -8.5 (+76.2) | 178 (51–127) -874.4 (+932.3) |
| 3. from 06:00, 20+ pips | 59 (22–37) +11.2 (-273.0) | 0 (0–0) +0.0 (+84.6) | 104 (27–77) -677.7 (+1,129.0) |
| 3. from 06:00, 30+ pips | 16 (6–10) +21.3 (-262.8) | 0 (0–0) +0.0 (+84.6) | 58 (14–44) -440.0 (+1,366.8) |
| 3. from 07:00, 20+ pips | 43 (19–24) +124.2 (-159.9) | 0 (0–0) +0.0 (+84.6) | 100 (28–72) -561.3 (+1,245.4) |
| 3. from 07:00, 30+ pips | 16 (6–10) +21.3 (-262.8) | 0 (0–0) +0.0 (+84.6) | 47 (11–36) -384.0 (+1,422.8) |

#### random weeks: totals

| Version | Trades | Won | Lost | Pips | Against current |
|---|---:|---:|---:|---:|---:|
| **1. Current rules** | 220 | 72 | 148 | **-594.7** |  |
| 2. from 06:00, 20+ pips | 132 | 40 | 92 | **-299.6** | +295.2 |
| 2. from 06:00, 30+ pips | 103 | 31 | 72 | **-276.8** | +318.0 |
| 2. from 07:00, 20+ pips | 137 | 43 | 94 | **-295.0** | +299.8 |
| 2. from 07:00, 30+ pips | 116 | 36 | 80 | **-227.5** | +367.2 |
| 3. from 06:00, 20+ pips | 53 | 11 | 42 | **-296.3** | +298.4 |
| 3. from 06:00, 30+ pips | 24 | 2 | 22 | **-273.5** | +321.2 |
| 3. from 07:00, 20+ pips | 58 | 14 | 44 | **-291.7** | +303.0 |
| 3. from 07:00, 30+ pips | 37 | 7 | 30 | **-224.2** | +370.4 |

#### random weeks: by week, trades (won–lost) and pips

| Week from | **1. Current rules** | 2. from 06:00, 20+ pips | 2. from 06:00, 30+ pips | 2. from 07:00, 20+ pips | 2. from 07:00, 30+ pips |
|---|---:|---:|---:|---:|---:|
| 02 Jun 2024 | 44 (16–28) -96.5 | 22 (8–14) -13.6 | 14 (4–10) -42.0 | 22 (8–14) -13.6 | 14 (4–10) -42.0 |
| 04 Aug 2024 | 64 (17–47) -402.3 | 35 (6–29) -361.8 | 35 (6–29) -361.8 | 44 (10–34) -370.4 | 44 (10–34) -370.4 |
| 20 Apr 2025 | 60 (22–38) -32.4 | 43 (16–27) +23.6 | 22 (11–11) +74.8 | 39 (15–24) +36.8 | 26 (12–14) +132.7 |
| 31 Aug 2025 | 52 (17–35) -63.6 | 32 (10–22) +52.3 | 32 (10–22) +52.3 | 32 (10–22) +52.3 | 32 (10–22) +52.3 |
| **All** | **220 (72–148) -594.7** | **132 (40–92) -299.6** | **103 (31–72) -276.8** | **137 (43–94) -295.0** | **116 (36–80) -227.5** |

| Week from | **1. Current rules** | 3. from 06:00, 20+ pips | 3. from 06:00, 30+ pips | 3. from 07:00, 20+ pips | 3. from 07:00, 30+ pips |
|---|---:|---:|---:|---:|---:|
| 02 Jun 2024 | 44 (16–28) -96.5 | 8 (4–4) +28.4 | 0 (0–0) +0.0 | 8 (4–4) +28.4 | 0 (0–0) +0.0 |
| 04 Aug 2024 | 64 (17–47) -402.3 | 13 (1–12) -170.3 | 13 (1–12) -170.3 | 22 (5–17) -179.0 | 22 (5–17) -179.0 |
| 20 Apr 2025 | 60 (22–38) -32.4 | 21 (5–16) -51.2 | 0 (0–0) +0.0 | 17 (4–13) -38.0 | 4 (1–3) +57.9 |
| 31 Aug 2025 | 52 (17–35) -63.6 | 11 (1–10) -103.2 | 11 (1–10) -103.2 | 11 (1–10) -103.2 | 11 (1–10) -103.2 |
| **All** | **220 (72–148) -594.7** | **53 (11–42) -296.3** | **24 (2–22) -273.5** | **58 (14–44) -291.7** | **37 (7–30) -224.2** |

#### random weeks: by the kind of day (in brackets: against the current rules)

| Version | trended | came back | other |
|---|---:|---:|---:|
| **1. Current rules** | 98 (37–61) +17.3 | 0 (0–0) +0.0 | 122 (35–87) -612.0 |
| 2. from 06:00, 20+ pips | 86 (32–54) +79.4 (+62.1) | 0 (0–0) +0.0 (+0.0) | 46 (8–38) -379.0 (+233.0) |
| 2. from 06:00, 30+ pips | 57 (23–34) +102.2 (+84.9) | 0 (0–0) +0.0 (+0.0) | 46 (8–38) -379.0 (+233.0) |
| 2. from 07:00, 20+ pips | 82 (31–51) +92.6 (+75.4) | 0 (0–0) +0.0 (+0.0) | 55 (12–43) -387.6 (+224.4) |
| 2. from 07:00, 30+ pips | 61 (24–37) +160.1 (+142.8) | 0 (0–0) +0.0 (+0.0) | 55 (12–43) -387.6 (+224.4) |
| 3. from 06:00, 20+ pips | 53 (11–42) -296.3 (-313.6) | 0 (0–0) +0.0 (+0.0) | 0 (0–0) +0.0 (+612.0) |
| 3. from 06:00, 30+ pips | 24 (2–22) -273.5 (-290.8) | 0 (0–0) +0.0 (+0.0) | 0 (0–0) +0.0 (+612.0) |
| 3. from 07:00, 20+ pips | 49 (10–39) -283.0 (-300.4) | 0 (0–0) +0.0 (+0.0) | 9 (4–5) -8.6 (+603.4) |
| 3. from 07:00, 30+ pips | 28 (3–25) -215.6 (-232.9) | 0 (0–0) +0.0 (+0.0) | 9 (4–5) -8.6 (+603.4) |

### How often the 09:00 test passed, by the kind of day it turned out to be

Bot's own IG candles, 26 October to 12 November 2026:

| Kind of day | Days | from 06:00, 20+ | from 06:00, 30+ | from 07:00, 20+ | from 07:00, 30+ |
|---|---:|---:|---:|---:|---:|
| trended | 4 | 3 (75%) | 1 (25%) | 2 (50%) | 0 (0%) |
| came back | 1 | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) |
| other | 8 | 4 (50%) | 1 (12%) | 4 (50%) | 1 (12%) |
| not finished | 1 | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) |
| **passed the test** | 13 | 7 days, 3 trended | 2 days, 1 trended | 6 days, 2 trended | 1 days, 0 trended |

Tick weeks, January to March 2026 (every weekday of the weeks replayed):

| Kind of day | Days | from 06:00, 20+ | from 06:00, 30+ | from 07:00, 20+ | from 07:00, 30+ |
|---|---:|---:|---:|---:|---:|
| trended | 23 | 6 (26%) | 2 (8%) | 4 (17%) | 2 (8%) |
| came back | 2 | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) |
| other | 38 | 10 (26%) | 5 (13%) | 12 (31%) | 4 (10%) |
| **passed the test** | 63 | 16 days, 6 trended | 7 days, 2 trended | 16 days, 4 trended | 6 days, 2 trended |

Tick weeks, the four random weeks of 2024 and 2025:

| Kind of day | Days | from 06:00, 20+ | from 06:00, 30+ | from 07:00, 20+ | from 07:00, 30+ |
|---|---:|---:|---:|---:|---:|
| trended | 8 | 6 (75%) | 2 (25%) | 5 (62%) | 3 (37%) |
| other | 12 | 0 (0%) | 0 (0%) | 1 (8%) | 1 (8%) |
| **passed the test** | 20 | 6 days, 6 trended | 2 days, 2 trended | 6 days, 5 trended | 4 days, 3 trended |

### The shortcut used for the tick weeks, checked on the candle data

| Version | Real replay | Shortcut (current rules' trades, filtered) | Difference | Trades only in the replay | Trades only in the shortcut |
|---|---:|---:|---:|---:|---:|
| 2. from 06:00, 20+ pips | 127 (69–58) +1,182.6 | 126 (68–58) +1,176.2 | +6.4 | 1 | 0 |
| 2. from 06:00, 30+ pips | 89 (56–33) +1,251.0 | 88 (56–32) +1,235.2 | +15.7 | 3 | 2 |
| 2. from 07:00, 20+ pips | 119 (66–53) +1,138.1 | 118 (65–53) +1,131.7 | +6.4 | 1 | 0 |
| 2. from 07:00, 30+ pips | 83 (52–31) +1,183.6 | 82 (52–30) +1,167.8 | +15.7 | 3 | 2 |
| 3. from 06:00, 20+ pips | 65 (23–42) -73.4 | 52 (19–33) -11.4 | -62.0 | 13 | 0 |
| 3. from 06:00, 30+ pips | 20 (9–11) +34.2 | 14 (7–7) +47.7 | -13.6 | 6 | 0 |
| 3. from 07:00, 20+ pips | 56 (20–36) -102.9 | 44 (16–28) -55.8 | -47.0 | 12 | 0 |
| 3. from 07:00, 30+ pips | 9 (4–5) +6.0 | 8 (3–5) -19.7 | +25.8 | 1 | 0 |
