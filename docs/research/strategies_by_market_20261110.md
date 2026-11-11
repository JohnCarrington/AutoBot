# Each strategy by the market it traded in: replay and live, 25 October to 10 November 2026

Tuesday 10 November 2026, about 22:00 UK. Read-only: **nothing in the bot was changed**, no IG calls, no restart, nothing written outside `data/research/`.


> **Correction, 11 November 2026.** Four of the live trades here were **closed by the owner by hand**: Monday's
> breakout, level reversal and slow grind buys at 15:21 (+11.7, -11.2, -12.7), and Tuesday's 16:26 level reversal
> sell at 17:56 (-14.6, not stopped by IG as the bot recorded). The two trades in "First" below were also closed by the
> owner (17:12 at 13324.3, +0.6; 17:56 at 13335.2, +37.8), so neither was still open, and IG refused the 20:30 closes
> because both positions were already closed. The owner closed these trades by hand (owner, 11 November 2026). IG shows the owner's closes on channel SYSTEM, the same channel as its stops and limits, which is why this report took them for IG's own system. Without the owner's closes, the live result is **21 trades:
> 5 won, 16 lost, -40.2 pips** at IG's prices, instead of 25 trades and -67.0. The splits below still include the four.

## First: two live trades may still be open at IG

At 20:30 UK tonight the bot sent its 20:30 closes for two trades, and **IG refused both** (`error.service.marketdata.position.notional.details.null.error`, in `data/orders/GBPUSD/orders.jsonl`). The bot's trade manager still recorded both as closed ("forced close", order sender "close refused"). It now holds no open trades, and its status shows none.

| Entry (UK) | Trade | IG open | IG stop | IG limit | The bot's record (not IG's) |
|---|---|---:|---:|---:|---|
| Tue 10 Nov 15:19 | slow grind sell | 13373.0 | 13388.0 | 13273.0 | forced close 20:30 at 13346.3, +26.7 |
| Tue 10 Nov 17:04 | Bollinger bounce buy | 13323.7 | 13317.7 | 13423.7 | forced close 20:30 at 13344.2, +20.5 |

Unless IG closed them some other way, both are still open at IG with their stops and limits, and the bot is no longer watching them. Checking needs IG, so it was not done here. **These two are left out of the live results below**, because their IG close is not known.

## Summary

| | Trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|
| **Replay**: the bot's code on its own IG candles, Sun 25 Oct 21:00 UK to the candle ending Tue 10 Nov 22:00 UTC | 169 | 78 | 90 | **+1,133.2** |
| the replay without Friday 6 November (+676.0 in 16 trades) | 153 | 65 | 87 | +457.3 |
| the replay on the live days only (9 and 10 November) | 24 | 9 | 15 | +169.0 |
| **Live**: every live trade since trading went on, with IG's prices | 25 | 6 | 19 | **−67.0** |

**Even on the same two days the replay and the live trades disagree** (+169.0 against −67.0). The live trades are 25 trades over two days, so every live split below is a handful of trades.

**Made money in both the replay and the live trades:**
- **A slow-grind trend in the Asian session (before 07:00 UK):** replay 15 trades, 13 won, **+526.6**. Live: 1 trade, +20.0 (the slow grind). Most of it is the EMA pullback (7 of 7, +368.6 in the replay) and the slow grind (6 of 6, +170.0).
- **The Asian session as a whole:** replay +695.8 in 35, live +16.0 in 4.
- **A strong-push trend:** replay +14.7 in 5, live +16.9 in 3. Few trades either way.

**Lost in both:**
- **Ranging, mostly the range trade from 12:00 to 17:00:** replay −11.2 in 5, live −18.0 in 3 (all three stopped).
- **After 20:30 UK:** replay −25.1 in 4, live −12.0 in 1.
- **A slow-grind trend in the London morning (07:00 to 12:00):** replay −44.0 in 40 (12 won), live −7.9 in 5. That is the most-traded pairing of all, and it loses. In the replay, the Bollinger bounce (−31.7 in 16) and the EMA pullback (−53.1 in 16) both lose there.
- **An emerging trend from 12:00 to 17:00:** replay −53.6 in 12 (2 won), live −6.0 in 1. In the replay, the EMA pullback is 0 of 6 there (−72.0).
- **A slow-grind trend late (17:00 to 20:30) and after 20:30:** replay −3.0 and −13.1, live −2.5 and −12.0.

**Made money in the replay but lost live:**
- **An emerging trend in the London morning:** replay **+350.7** in 18 (13 won), live −23.5 in 5.
- **A slow-grind trend from 12:00 to 17:00:** replay +125.3 in 25, live −30.0 in 2.
- **An emerging trend in the Asian session:** replay +152.0 in 18, live −4.0 in 3.
- **Big-news days:** replay +853.2 in 56 (of which Friday 6 November alone made +676.0), live −41.3 in 13. On days without big news: replay +280.0 in 113, live −25.7 in 12.

The marks are ✅ for a pairing that made money, ❌ for one that lost, and · for exactly 0. They are marked separately for the replay and the live trades.

## How it was done

- **Replay.** The research mode (`research/long_replay.py`, checked trade for trade against the bot's own replay in `long_replay_20261110.md`) ran the bot's analyser, strategies, safety rules and trade manager:
  - Candles: a read-only copy of the bot's own IG candle store, taken at 22:00 UTC tonight. Nothing else.
  - Period: Sunday 25 October 21:00 UK to the last stored candle (ending Tuesday 10 November 22:00 UTC).
  - Rules: today's code and switches, so the Bollinger bounce and range trade stop is 6 pips. All six strategies are on, paper only.
  - News rules: Finnhub's past calendar. The bot's own calendar file only goes back to 31 October. From then on the two calendars give the same big-news days. Before that, Finnhub's also has the Fed (28 October) and US GDP (29 October), which the bot would have had on the day.
- **Prices, no spread added.**
  - Replay entries are filled at IG's buy or sell price from the bot's candles. Exits are at the IG stop or limit level, or at an IG candle's price.
  - The one exception is six range-trade half closes. Paper mode booked those at the Bollinger band's own unrounded value, for example 13345.13. They were re-priced at the IG close of that candle, on the side the trade closes on: −7.4 pips in all, from +1,140.6 to +1,133.2.
- **Live trades: all 27** opened from Monday 9 November 05:25 UK to Tuesday 10 November 17:04 UK.
  - Entry: IG's deal confirmation level.
  - Exit, in order of preference:
    1. IG's own transactions (10 November up to 13:10 UTC).
    2. IG's activity for the three trades IG's system closed on Monday at 15:21 (`live_investigation_20261110.md`).
    3. IG's deal confirmation of the bot's own closes.
    4. For the other stops and take profits, IG's stop or limit level. Every stop and take profit in IG's records closed exactly at its level.
  - The first 20 trades add up to −62.9, IG's booked total in the live investigation.
  - IG's funds readings confirm two of the later ones to the penny, because no other trade was open either side of them: the 13:11 breakout (−£60.00, −6.0) and the 13:30 slow grind (−£150.00, −15.0).
  - The 13:30 slow grind sell opened at 13:30:04 UK, the second US CPI came out, and IG stopped it within the same second. The bot recorded −22.3 for it, from its own price; IG's funds show −15.0. That trade opened inside the big-news window (13:15 to 14:00) on purpose: in the current code (`strategies/common.py`) the slow grind, EMA pullback and breakout are not covered by the big-news no-new-trades window.
  - The bot's own trade records often differ from IG's prices (by 0.1 to 7.3 pips on stops), so they were not used for prices. The bot's "closed at IG" price is its own price at that moment, not IG's.
- **State at entry:** the analyser's state recorded with each trade (`market_state`), the same label for replay and live. No strategy entered in consolidation, so that row is always empty.
- **Session:** the UK time of entry. Asian is before 07:00, London 07:00 to 12:00, London and New York 12:00 to 17:00, late 17:00 to 20:30, overnight after 20:30 (the Sunday open included).
- **Big-news day:** the bot's own rule (`strategies.common.big_news_day`: a big GBP or USD release that UK day). For the replay it uses Finnhub's calendar. For the live trades it uses the bot's own calendar, copied tonight. That makes Tuesday 10 November a big-news day and Monday 9 November not.
- **Won and lost:** above or below 0 pips. Pips are per trade, with a half close counted as half.

## Every live trade

| Entry (UK) | Strategy | State at entry | Session | Big-news day | IG open | IG close | Closed (UK) | Pips | Close price from |
|---|---|---|---|---|---:|---:|---|---:|---|
| Mon 09 Nov 05:25 | slow grind buy | trend up, slow grind | Asian | no | 13380.2 | 13400.2 | Mon 08:13 | **+20.0** | IG's limit level |
| Mon 09 Nov 06:12 | level reversal buy | emerging trend up | Asian | no | 13385.4 | 13405.4 | Mon 08:18 | **+20.0** | IG's limit level |
| Mon 09 Nov 07:55 | breakout buy | emerging trend up | London | no | 13392.5 | 13404.2 | Mon 15:21 | **+11.7** | IG's activity (closed by IG's system) |
| Mon 09 Nov 08:25 | level reversal buy | emerging trend up | London | no | 13414.9 | 13403.7 | Mon 15:21 | **-11.2** | IG's activity (closed by IG's system) |
| Mon 09 Nov 09:00 | Bollinger bounce sell | trend up, slow grind | London | no | 13408.0 | 13414.0 | Mon 09:29 | **-6.0** | IG's stop level |
| Mon 09 Nov 09:39 | slow grind buy | trend up, slow grind | London | no | 13416.8 | 13404.1 | Mon 15:21 | **-12.7** | IG's activity (closed by IG's system) |
| Mon 09 Nov 13:55 | range trade buy | ranging none | London and New York | no | 13418.6 | 13412.6 | Mon 14:43 | **-6.0** | IG's stop level |
| Mon 09 Nov 14:55 | range trade buy | ranging none | London and New York | no | 13415.3 | 13409.3 | Mon 14:58 | **-6.0** | IG's stop level |
| Mon 09 Nov 15:16 | range trade buy | ranging none | London and New York | no | 13410.9 | 13404.9 | Mon 15:20 | **-6.0** | IG's stop level |
| Mon 09 Nov 15:45 | slow grind sell | trend down, slow grind | London and New York | no | 13401.6 | 13416.6 | Mon 16:17 | **-15.0** | IG's stop level |
| Mon 09 Nov 19:55 | slow grind buy | trend up, slow grind | late | no | 13438.6 | 13436.1 | Mon 20:30 | **-2.5** | IG's deal confirmation of the bot's close |
| Mon 09 Nov 21:02 | EMA pullback buy | trend up, slow grind | overnight | no | 13443.6 | 13431.6 | Mon 22:00 | **-12.0** | IG's stop level |
| Tue 10 Nov 05:01 | EMA pullback buy | emerging trend up | Asian | yes | 13451.0 | 13439 | Tue 09:00 | **-12.0** | IG's transactions |
| Tue 10 Nov 06:12 | EMA pullback buy | emerging trend up | Asian | yes | 13452.8 | 13440.8 | Tue 09:00 | **-12.0** | IG's transactions |
| Tue 10 Nov 07:21 | EMA pullback buy | emerging trend up | London | yes | 13456.1 | 13444.1 | Tue 09:00 | **-12.0** | IG's transactions |
| Tue 10 Nov 07:55 | Bollinger bounce sell | trend up, slow grind | London | yes | 13449.6 | 13455.6 | Tue 08:01 | **-6.0** | IG's transactions |
| Tue 10 Nov 08:20 | Bollinger bounce sell | trend up, slow grind | London | yes | 13448.9 | 13454.9 | Tue 08:24 | **-6.0** | IG's transactions |
| Tue 10 Nov 08:45 | Bollinger bounce sell | trend up, slow grind | London | yes | 13453.7 | 13430.9 | Tue 10:45 | **+22.8** | IG's transactions |
| Tue 10 Nov 09:10 | breakout sell | emerging trend down | London | yes | 13432.7 | 13438.7 | Tue 09:24 | **-6.0** | IG's transactions |
| Tue 10 Nov 11:50 | breakout sell | emerging trend down | London | yes | 13422.7 | 13428.7 | Tue 12:02 | **-6.0** | IG's transactions |
| Tue 10 Nov 13:11 | breakout sell | emerging trend down | London and New York | yes | 13419.6 | 13425.6 | Tue 13:29 | **-6.0** | IG's stop level |
| Tue 10 Nov 13:30 | slow grind sell | trend down, slow grind | London and New York | yes | 13396.5 | 13411.5 | Tue 13:30 | **-15.0** | IG's stop level |
| Tue 10 Nov 13:56 | slow grind sell | trend down, strong push | London and New York | yes | 13392.2 | 13375.1 | Tue 15:00 | **+17.1** | IG's deal confirmation of the bot's close |
| Tue 10 Nov 14:06 | level reversal sell | trend down, strong push | London and New York | yes | 13388.9 | 13368.9 | Tue 15:29 | **+20.0** | IG's limit level |
| Tue 10 Nov 16:26 | level reversal sell | trend down, strong push | London and New York | yes | 13321.0 | 13341.2 | Tue 18:35 | **-20.2** | IG's stop level |

## By strategy (the whole bot first)

### The whole bot

Replay: 169 trades, 78 won, 90 lost, **+1133.2** pips. Live: 25 trades, 6 won, 19 lost, **-67.0** pips.

**By the analyser's state at entry**

| State | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ranging | 10 | 6 | 4 | **-2.2** ❌ | 3 | 0 | 3 | **-18.0** ❌ |
| consolidation | – | – | – | – | – | – | – | – |
| emerging trend | 59 | 25 | 34 | **+488.2** ✅ | 9 | 2 | 7 | **-33.5** ❌ |
| trend: slow grind | 91 | 41 | 49 | **+591.8** ✅ | 10 | 2 | 8 | **-32.4** ❌ |
| trend: strong push | 5 | 3 | 2 | **+14.7** ✅ | 3 | 2 | 1 | **+16.9** ✅ |
| possible reversal | 4 | 3 | 1 | **+40.8** ✅ | – | – | – | – |
| **All** | 169 | 78 | 90 | **+1133.2** ✅ | 25 | 6 | 19 | **-67.0** ❌ |

**By session (UK time of entry)**

| Session | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Asian (before 07:00) | 35 | 20 | 15 | **+695.8** ✅ | 4 | 2 | 2 | **+16.0** ✅ |
| London (07:00-12:00) | 63 | 30 | 33 | **+343.0** ✅ | 10 | 2 | 8 | **-31.4** ❌ |
| London and New York (12:00-17:00) | 46 | 16 | 29 | **+39.4** ✅ | 9 | 2 | 7 | **-37.1** ❌ |
| late (17:00-20:30) | 21 | 11 | 10 | **+80.2** ✅ | 1 | 0 | 1 | **-2.5** ❌ |
| overnight (after 20:30) | 4 | 1 | 3 | **-25.1** ❌ | 1 | 0 | 1 | **-12.0** ❌ |
| **All** | 169 | 78 | 90 | **+1133.2** ✅ | 25 | 6 | 19 | **-67.0** ❌ |

**Big-news day or not**

| Day | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| big-news day | 56 | 30 | 26 | **+853.2** ✅ | 13 | 3 | 10 | **-41.3** ❌ |
| no big news | 113 | 48 | 64 | **+280.0** ✅ | 12 | 3 | 9 | **-25.7** ❌ |
| **All** | 169 | 78 | 90 | **+1133.2** ✅ | 25 | 6 | 19 | **-67.0** ❌ |

**State and session together** (only the pairings with trades)

| State · session | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ranging · Asian (before 07:00) | 1 | 0 | 1 | **-2.8** ❌ | – | – | – | – |
| ranging · London (07:00-12:00) | 2 | 2 | 0 | **+1.0** ✅ | – | – | – | – |
| ranging · London and New York (12:00-17:00) | 5 | 2 | 3 | **-11.2** ❌ | 3 | 0 | 3 | **-18.0** ❌ |
| ranging · late (17:00-20:30) | 2 | 2 | 0 | **+10.8** ✅ | – | – | – | – |
| emerging trend · Asian (before 07:00) | 18 | 6 | 12 | **+152.0** ✅ | 3 | 1 | 2 | **-4.0** ❌ |
| emerging trend · London (07:00-12:00) | 18 | 13 | 5 | **+350.7** ✅ | 5 | 1 | 4 | **-23.5** ❌ |
| emerging trend · London and New York (12:00-17:00) | 12 | 2 | 10 | **-53.6** ❌ | 1 | 0 | 1 | **-6.0** ❌ |
| emerging trend · late (17:00-20:30) | 10 | 4 | 6 | **+51.1** ✅ | – | – | – | – |
| emerging trend · overnight (after 20:30) | 1 | 0 | 1 | **-12.0** ❌ | – | – | – | – |
| trend: slow grind · Asian (before 07:00) | 15 | 13 | 2 | **+526.6** ✅ | 1 | 1 | 0 | **+20.0** ✅ |
| trend: slow grind · London (07:00-12:00) | 40 | 12 | 28 | **-44.0** ❌ | 5 | 1 | 4 | **-7.9** ❌ |
| trend: slow grind · London and New York (12:00-17:00) | 25 | 11 | 13 | **+125.3** ✅ | 2 | 0 | 2 | **-30.0** ❌ |
| trend: slow grind · late (17:00-20:30) | 8 | 4 | 4 | **-3.0** ❌ | 1 | 0 | 1 | **-2.5** ❌ |
| trend: slow grind · overnight (after 20:30) | 3 | 1 | 2 | **-13.1** ❌ | 1 | 0 | 1 | **-12.0** ❌ |
| trend: strong push · Asian (before 07:00) | 1 | 1 | 0 | **+20.0** ✅ | – | – | – | – |
| trend: strong push · London (07:00-12:00) | 1 | 1 | 0 | **+9.7** ✅ | – | – | – | – |
| trend: strong push · London and New York (12:00-17:00) | 3 | 1 | 2 | **-15.0** ❌ | 3 | 2 | 1 | **+16.9** ✅ |
| possible reversal · London (07:00-12:00) | 2 | 2 | 0 | **+25.5** ✅ | – | – | – | – |
| possible reversal · London and New York (12:00-17:00) | 1 | 0 | 1 | **-6.0** ❌ | – | – | – | – |
| possible reversal · late (17:00-20:30) | 1 | 1 | 0 | **+21.3** ✅ | – | – | – | – |
| **All** | 169 | 78 | 90 | **+1133.2** ✅ | 25 | 6 | 19 | **-67.0** ❌ |

### slow grind

Replay: 23 trades, 14 won, 8 lost, **+285.8** pips. Live: 6 trades, 2 won, 4 lost, **-8.1** pips.

**By the analyser's state at entry**

| State | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ranging | – | – | – | – | – | – | – | – |
| consolidation | – | – | – | – | – | – | – | – |
| emerging trend | – | – | – | – | – | – | – | – |
| trend: slow grind | 20 | 12 | 7 | **+271.1** ✅ | 5 | 1 | 4 | **-25.2** ❌ |
| trend: strong push | 3 | 2 | 1 | **+14.7** ✅ | 1 | 1 | 0 | **+17.1** ✅ |
| possible reversal | – | – | – | – | – | – | – | – |
| **All** | 23 | 14 | 8 | **+285.8** ✅ | 6 | 2 | 4 | **-8.1** ❌ |

**By session (UK time of entry)**

| Session | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Asian (before 07:00) | 7 | 7 | 0 | **+190.0** ✅ | 1 | 1 | 0 | **+20.0** ✅ |
| London (07:00-12:00) | 7 | 4 | 3 | **+24.7** ✅ | 1 | 0 | 1 | **-12.7** ❌ |
| London and New York (12:00-17:00) | 6 | 3 | 2 | **+90.0** ✅ | 3 | 1 | 2 | **-12.9** ❌ |
| late (17:00-20:30) | 3 | 0 | 3 | **-18.9** ❌ | 1 | 0 | 1 | **-2.5** ❌ |
| overnight (after 20:30) | – | – | – | – | – | – | – | – |
| **All** | 23 | 14 | 8 | **+285.8** ✅ | 6 | 2 | 4 | **-8.1** ❌ |

**Big-news day or not**

| Day | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| big-news day | 8 | 6 | 2 | **+209.7** ✅ | 2 | 1 | 1 | **+2.1** ✅ |
| no big news | 15 | 8 | 6 | **+76.1** ✅ | 4 | 1 | 3 | **-10.2** ❌ |
| **All** | 23 | 14 | 8 | **+285.8** ✅ | 6 | 2 | 4 | **-8.1** ❌ |

**State and session together** (only the pairings with trades)

| State · session | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| trend: slow grind · Asian (before 07:00) | 6 | 6 | 0 | **+170.0** ✅ | 1 | 1 | 0 | **+20.0** ✅ |
| trend: slow grind · London (07:00-12:00) | 6 | 3 | 3 | **+15.0** ✅ | 1 | 0 | 1 | **-12.7** ❌ |
| trend: slow grind · London and New York (12:00-17:00) | 5 | 3 | 1 | **+105.0** ✅ | 2 | 0 | 2 | **-30.0** ❌ |
| trend: slow grind · late (17:00-20:30) | 3 | 0 | 3 | **-18.9** ❌ | 1 | 0 | 1 | **-2.5** ❌ |
| trend: strong push · Asian (before 07:00) | 1 | 1 | 0 | **+20.0** ✅ | – | – | – | – |
| trend: strong push · London (07:00-12:00) | 1 | 1 | 0 | **+9.7** ✅ | – | – | – | – |
| trend: strong push · London and New York (12:00-17:00) | 1 | 0 | 1 | **-15.0** ❌ | 1 | 1 | 0 | **+17.1** ✅ |
| **All** | 23 | 14 | 8 | **+285.8** ✅ | 6 | 2 | 4 | **-8.1** ❌ |

### EMA pullback

Replay: 65 trades, 26 won, 39 lost, **+595.3** pips. Live: 4 trades, 0 won, 4 lost, **-48.0** pips.

**By the analyser's state at entry**

| State | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ranging | – | – | – | – | – | – | – | – |
| consolidation | – | – | – | – | – | – | – | – |
| emerging trend | 35 | 12 | 23 | **+226.6** ✅ | 3 | 0 | 3 | **-36.0** ❌ |
| trend: slow grind | 30 | 14 | 16 | **+368.7** ✅ | 1 | 0 | 1 | **-12.0** ❌ |
| trend: strong push | – | – | – | – | – | – | – | – |
| possible reversal | – | – | – | – | – | – | – | – |
| **All** | 65 | 26 | 39 | **+595.3** ✅ | 4 | 0 | 4 | **-48.0** ❌ |

**By session (UK time of entry)**

| Session | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Asian (before 07:00) | 21 | 12 | 9 | **+543.9** ✅ | 2 | 0 | 2 | **-24.0** ❌ |
| London (07:00-12:00) | 24 | 8 | 16 | **+60.9** ✅ | 1 | 0 | 1 | **-12.0** ❌ |
| London and New York (12:00-17:00) | 10 | 3 | 7 | **-5.7** ❌ | – | – | – | – |
| late (17:00-20:30) | 6 | 2 | 4 | **+21.3** ✅ | – | – | – | – |
| overnight (after 20:30) | 4 | 1 | 3 | **-25.1** ❌ | 1 | 0 | 1 | **-12.0** ❌ |
| **All** | 65 | 26 | 39 | **+595.3** ✅ | 4 | 0 | 4 | **-48.0** ❌ |

**Big-news day or not**

| Day | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| big-news day | 22 | 11 | 11 | **+481.3** ✅ | 3 | 0 | 3 | **-36.0** ❌ |
| no big news | 43 | 15 | 28 | **+114.0** ✅ | 1 | 0 | 1 | **-12.0** ❌ |
| **All** | 65 | 26 | 39 | **+595.3** ✅ | 4 | 0 | 4 | **-48.0** ❌ |

**State and session together** (only the pairings with trades)

| State · session | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| emerging trend · Asian (before 07:00) | 14 | 5 | 9 | **+175.3** ✅ | 2 | 0 | 2 | **-24.0** ❌ |
| emerging trend · London (07:00-12:00) | 8 | 5 | 3 | **+114.0** ✅ | 1 | 0 | 1 | **-12.0** ❌ |
| emerging trend · London and New York (12:00-17:00) | 6 | 0 | 6 | **-72.0** ❌ | – | – | – | – |
| emerging trend · late (17:00-20:30) | 6 | 2 | 4 | **+21.3** ✅ | – | – | – | – |
| emerging trend · overnight (after 20:30) | 1 | 0 | 1 | **-12.0** ❌ | – | – | – | – |
| trend: slow grind · Asian (before 07:00) | 7 | 7 | 0 | **+368.6** ✅ | – | – | – | – |
| trend: slow grind · London (07:00-12:00) | 16 | 3 | 13 | **-53.1** ❌ | – | – | – | – |
| trend: slow grind · London and New York (12:00-17:00) | 4 | 3 | 1 | **+66.3** ✅ | – | – | – | – |
| trend: slow grind · overnight (after 20:30) | 3 | 1 | 2 | **-13.1** ❌ | 1 | 0 | 1 | **-12.0** ❌ |
| **All** | 65 | 26 | 39 | **+595.3** ✅ | 4 | 0 | 4 | **-48.0** ❌ |

### Bollinger bounce

Replay: 38 trades, 15 won, 23 lost, **-10.3** pips. Live: 4 trades, 1 won, 3 lost, **+4.8** pips.

**By the analyser's state at entry**

| State | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ranging | – | – | – | – | – | – | – | – |
| consolidation | – | – | – | – | – | – | – | – |
| emerging trend | – | – | – | – | – | – | – | – |
| trend: slow grind | 34 | 12 | 22 | **-51.1** ❌ | 4 | 1 | 3 | **+4.8** ✅ |
| trend: strong push | – | – | – | – | – | – | – | – |
| possible reversal | 4 | 3 | 1 | **+40.8** ✅ | – | – | – | – |
| **All** | 38 | 15 | 23 | **-10.3** ❌ | 4 | 1 | 3 | **+4.8** ✅ |

**By session (UK time of entry)**

| Session | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Asian (before 07:00) | 2 | 0 | 2 | **-12.0** ❌ | – | – | – | – |
| London (07:00-12:00) | 18 | 6 | 12 | **-6.2** ❌ | 4 | 1 | 3 | **+4.8** ✅ |
| London and New York (12:00-17:00) | 13 | 5 | 8 | **-26.1** ❌ | – | – | – | – |
| late (17:00-20:30) | 5 | 4 | 1 | **+34.0** ✅ | – | – | – | – |
| overnight (after 20:30) | – | – | – | – | – | – | – | – |
| **All** | 38 | 15 | 23 | **-10.3** ❌ | 4 | 1 | 3 | **+4.8** ✅ |

**Big-news day or not**

| Day | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| big-news day | 14 | 6 | 8 | **+17.5** ✅ | 3 | 1 | 2 | **+10.8** ✅ |
| no big news | 24 | 9 | 15 | **-27.8** ❌ | 1 | 0 | 1 | **-6.0** ❌ |
| **All** | 38 | 15 | 23 | **-10.3** ❌ | 4 | 1 | 3 | **+4.8** ✅ |

**State and session together** (only the pairings with trades)

| State · session | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| trend: slow grind · Asian (before 07:00) | 2 | 0 | 2 | **-12.0** ❌ | – | – | – | – |
| trend: slow grind · London (07:00-12:00) | 16 | 4 | 12 | **-31.7** ❌ | 4 | 1 | 3 | **+4.8** ✅ |
| trend: slow grind · London and New York (12:00-17:00) | 12 | 5 | 7 | **-20.1** ❌ | – | – | – | – |
| trend: slow grind · late (17:00-20:30) | 4 | 3 | 1 | **+12.7** ✅ | – | – | – | – |
| possible reversal · London (07:00-12:00) | 2 | 2 | 0 | **+25.5** ✅ | – | – | – | – |
| possible reversal · London and New York (12:00-17:00) | 1 | 0 | 1 | **-6.0** ❌ | – | – | – | – |
| possible reversal · late (17:00-20:30) | 1 | 1 | 0 | **+21.3** ✅ | – | – | – | – |
| **All** | 38 | 15 | 23 | **-10.3** ❌ | 4 | 1 | 3 | **+4.8** ✅ |

### range trade

Replay: 10 trades, 6 won, 4 lost, **-2.2** pips. Live: 3 trades, 0 won, 3 lost, **-18.0** pips.

**By the analyser's state at entry**

| State | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ranging | 10 | 6 | 4 | **-2.2** ❌ | 3 | 0 | 3 | **-18.0** ❌ |
| consolidation | – | – | – | – | – | – | – | – |
| emerging trend | – | – | – | – | – | – | – | – |
| trend: slow grind | – | – | – | – | – | – | – | – |
| trend: strong push | – | – | – | – | – | – | – | – |
| possible reversal | – | – | – | – | – | – | – | – |
| **All** | 10 | 6 | 4 | **-2.2** ❌ | 3 | 0 | 3 | **-18.0** ❌ |

**By session (UK time of entry)**

| Session | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Asian (before 07:00) | 1 | 0 | 1 | **-2.8** ❌ | – | – | – | – |
| London (07:00-12:00) | 2 | 2 | 0 | **+1.0** ✅ | – | – | – | – |
| London and New York (12:00-17:00) | 5 | 2 | 3 | **-11.2** ❌ | 3 | 0 | 3 | **-18.0** ❌ |
| late (17:00-20:30) | 2 | 2 | 0 | **+10.8** ✅ | – | – | – | – |
| overnight (after 20:30) | – | – | – | – | – | – | – | – |
| **All** | 10 | 6 | 4 | **-2.2** ❌ | 3 | 0 | 3 | **-18.0** ❌ |

**Big-news day or not**

| Day | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| big-news day | 1 | 0 | 1 | **-2.8** ❌ | – | – | – | – |
| no big news | 9 | 6 | 3 | **+0.6** ✅ | 3 | 0 | 3 | **-18.0** ❌ |
| **All** | 10 | 6 | 4 | **-2.2** ❌ | 3 | 0 | 3 | **-18.0** ❌ |

**State and session together** (only the pairings with trades)

| State · session | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ranging · Asian (before 07:00) | 1 | 0 | 1 | **-2.8** ❌ | – | – | – | – |
| ranging · London (07:00-12:00) | 2 | 2 | 0 | **+1.0** ✅ | – | – | – | – |
| ranging · London and New York (12:00-17:00) | 5 | 2 | 3 | **-11.2** ❌ | 3 | 0 | 3 | **-18.0** ❌ |
| ranging · late (17:00-20:30) | 2 | 2 | 0 | **+10.8** ✅ | – | – | – | – |
| **All** | 10 | 6 | 4 | **-2.2** ❌ | 3 | 0 | 3 | **-18.0** ❌ |

### breakout

Replay: 11 trades, 6 won, 5 lost, **+193.8** pips. Live: 4 trades, 1 won, 3 lost, **-6.3** pips.

**By the analyser's state at entry**

| State | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ranging | – | – | – | – | – | – | – | – |
| consolidation | – | – | – | – | – | – | – | – |
| emerging trend | 11 | 6 | 5 | **+193.8** ✅ | 4 | 1 | 3 | **-6.3** ❌ |
| trend: slow grind | – | – | – | – | – | – | – | – |
| trend: strong push | – | – | – | – | – | – | – | – |
| possible reversal | – | – | – | – | – | – | – | – |
| **All** | 11 | 6 | 5 | **+193.8** ✅ | 4 | 1 | 3 | **-6.3** ❌ |

**By session (UK time of entry)**

| Session | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Asian (before 07:00) | – | – | – | – | – | – | – | – |
| London (07:00-12:00) | 4 | 3 | 1 | **+138.0** ✅ | 3 | 1 | 2 | **-0.3** ❌ |
| London and New York (12:00-17:00) | 3 | 1 | 2 | **+26.0** ✅ | 1 | 0 | 1 | **-6.0** ❌ |
| late (17:00-20:30) | 4 | 2 | 2 | **+29.8** ✅ | – | – | – | – |
| overnight (after 20:30) | – | – | – | – | – | – | – | – |
| **All** | 11 | 6 | 5 | **+193.8** ✅ | 4 | 1 | 3 | **-6.3** ❌ |

**Big-news day or not**

| Day | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| big-news day | 4 | 4 | 0 | **+153.8** ✅ | 3 | 0 | 3 | **-18.0** ❌ |
| no big news | 7 | 2 | 5 | **+40.0** ✅ | 1 | 1 | 0 | **+11.7** ✅ |
| **All** | 11 | 6 | 5 | **+193.8** ✅ | 4 | 1 | 3 | **-6.3** ❌ |

**State and session together** (only the pairings with trades)

| State · session | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| emerging trend · London (07:00-12:00) | 4 | 3 | 1 | **+138.0** ✅ | 3 | 1 | 2 | **-0.3** ❌ |
| emerging trend · London and New York (12:00-17:00) | 3 | 1 | 2 | **+26.0** ✅ | 1 | 0 | 1 | **-6.0** ❌ |
| emerging trend · late (17:00-20:30) | 4 | 2 | 2 | **+29.8** ✅ | – | – | – | – |
| **All** | 11 | 6 | 5 | **+193.8** ✅ | 4 | 1 | 3 | **-6.3** ❌ |

### level reversal

Replay: 22 trades, 11 won, 11 lost, **+70.9** pips. Live: 4 trades, 2 won, 2 lost, **+8.6** pips.

**By the analyser's state at entry**

| State | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ranging | – | – | – | – | – | – | – | – |
| consolidation | – | – | – | – | – | – | – | – |
| emerging trend | 13 | 7 | 6 | **+67.8** ✅ | 2 | 1 | 1 | **+8.8** ✅ |
| trend: slow grind | 7 | 3 | 4 | **+3.1** ✅ | – | – | – | – |
| trend: strong push | 2 | 1 | 1 | **+0.0** · | 2 | 1 | 1 | **-0.2** ❌ |
| possible reversal | – | – | – | – | – | – | – | – |
| **All** | 22 | 11 | 11 | **+70.9** ✅ | 4 | 2 | 2 | **+8.6** ✅ |

**By session (UK time of entry)**

| Session | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Asian (before 07:00) | 4 | 1 | 3 | **-23.3** ❌ | 1 | 1 | 0 | **+20.0** ✅ |
| London (07:00-12:00) | 8 | 7 | 1 | **+124.5** ✅ | 1 | 0 | 1 | **-11.2** ❌ |
| London and New York (12:00-17:00) | 9 | 2 | 7 | **-33.5** ❌ | 2 | 1 | 1 | **-0.2** ❌ |
| late (17:00-20:30) | 1 | 1 | 0 | **+3.2** ✅ | – | – | – | – |
| overnight (after 20:30) | – | – | – | – | – | – | – | – |
| **All** | 22 | 11 | 11 | **+70.9** ✅ | 4 | 2 | 2 | **+8.6** ✅ |

**Big-news day or not**

| Day | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| big-news day | 7 | 3 | 4 | **-6.3** ❌ | 2 | 1 | 1 | **-0.2** ❌ |
| no big news | 15 | 8 | 7 | **+77.2** ✅ | 2 | 1 | 1 | **+8.8** ✅ |
| **All** | 22 | 11 | 11 | **+70.9** ✅ | 4 | 2 | 2 | **+8.6** ✅ |

**State and session together** (only the pairings with trades)

| State · session | Replay trades | Won | Lost | Pips | Live trades | Won | Lost | Pips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| emerging trend · Asian (before 07:00) | 4 | 1 | 3 | **-23.3** ❌ | 1 | 1 | 0 | **+20.0** ✅ |
| emerging trend · London (07:00-12:00) | 6 | 5 | 1 | **+98.7** ✅ | 1 | 0 | 1 | **-11.2** ❌ |
| emerging trend · London and New York (12:00-17:00) | 3 | 1 | 2 | **-7.6** ❌ | – | – | – | – |
| trend: slow grind · London (07:00-12:00) | 2 | 2 | 0 | **+25.8** ✅ | – | – | – | – |
| trend: slow grind · London and New York (12:00-17:00) | 4 | 0 | 4 | **-25.9** ❌ | – | – | – | – |
| trend: slow grind · late (17:00-20:30) | 1 | 1 | 0 | **+3.2** ✅ | – | – | – | – |
| trend: strong push · London and New York (12:00-17:00) | 2 | 1 | 1 | **+0.0** · | 2 | 1 | 1 | **-0.2** ❌ |
| **All** | 22 | 11 | 11 | **+70.9** ✅ | 4 | 2 | 2 | **+8.6** ✅ |
