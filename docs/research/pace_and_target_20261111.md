# Pace and target: the owner's rule replayed, 25 October to 11 November 2026

Wednesday 11 November 2026, UK. Read-only research: **nothing in the bot was changed**. There were no IG calls and no restart, and nothing was written outside `data/research/`.

The owner's words: *"I decide by looking at how quickly the price is moving. It is moving slowly this morning so it is not unreasonable to think it is grinding to a halt and will take a couple of hours to hit that level. If it was moving faster all morning I might expect it to break through and continue."*

The rule tested:

1. While the bot has open trend trades (EMA pullback, slow grind, breakout), no Bollinger bounce may open against them until price reaches the next significant level in their direction: a 00, the weekly pivot, S2, S3, R2 or R3.
2. At that level, the bounce is valid only if price has been moving slowly. It then opens and closes the opposite trades. If price has been moving fast, the bounce is refused and the trend trades are held.

## Summary

**Data and code.** The bot's own code (the current rules, commit `04b3a83`) was replayed on its own IG candles. The replay runs from the week's open on Sunday 25 October (21:00 UTC) to the last stored candle, which ends at 15:10 UTC today. Prices are IG's real buy and sell prices with no spread added. **No candle in any of the 40 runs reached both a trade's stop and its target**, so counting the stop first or the target first gives the same result.

**The current rules make +1,329.2 pips in 176 trades** (90 won, 85 lost, 1 at 0):

- 25 to 30 October: +224.9
- 1 to 6 November: +811.0
- 8 to 11 November 15:10: +293.2

**The owner's rule, all 39 versions** (13 ways of measuring "how quickly" × 3 meanings of "at the level"):

| "Slowly" means | Within 3 pips | Within 5 pips | Within 8 pips |
|---|---:|---:|---:|
| Analyser's trend type is slow grind | **+26.3** | **−34.4** | **−24.2** |
| Last 6 candles average under 3 pips | +22.0 | +22.0 | +22.0 |
| Last 6 candles average under 4 pips | +22.0 | −1.0 | −1.0 |
| Last 6 candles average under 6 pips | +35.8 | −37.9 | −40.8 |
| Last 12 candles average under 3 pips | +22.0 | +22.0 | +22.0 |
| Last 12 candles average under 4 pips | +22.0 | −1.0 | −1.0 |
| Last 12 candles average under 6 pips | +26.3 | −34.4 | −32.3 |
| Last 2 hours under 5 pips an hour | +43.8 | **+50.3** | +29.3 |
| Last 2 hours under 8 pips an hour | +43.8 | +6.8 | +17.1 |
| Last 2 hours under 12 pips an hour | +43.8 | −37.0 | −26.7 |
| Last 3 hours under 5 pips an hour | +43.8 | +21.6 | +18.8 |
| Last 3 hours under 8 pips an hour | +26.3 | −34.4 | −24.2 |
| Last 3 hours under 12 pips an hour | +26.3 | −34.4 | −24.2 |

Each figure is against the current rules (+1,329.2). The full figures are in the tables below.

- **Most of the gain comes from part 1 alone: refusing the bounces.**
  - Under the current rules, 23 bounces opened while trend trades were open against them. **They won 10, lost 13 and made −20.5 pips.** None of them closed anything.
  - The 8 versions where "slowly" is under 3 pips a candle (and, within 3 pips, under 4) never find price slow at a level. They refuse every one of those bounces and make **+22.0**.
  - In those 8 versions **the trend trades are exactly the same as now**, trade for trade (25 slow grinds +286.5, 70 EMA pullbacks +703.3, 12 breakouts +220.6). Holding them changed nothing, because no bounce ever closed them under the current rules. The +22.0 is simply the losing bounces not taken.
- **Part 2, using a bounce at the level to close the trend trades, mostly loses.**
  - **Within 3 pips** it is better than refusing everything: +26.3 to +43.8 against +22.0. Almost all of that comes from one bounce, the **Monday 26 October 14:10 buy at S3 (13328.6)**. It closed two EMA pullback sells at +12.0 each, two at −4.8 and a level reversal at −1.0 (+13.4 in all), and the bounce itself made +7.2.
  - **Within 5 and 8 pips**, the looser measures (6 pips a candle, 12 pips an hour, the trend type) let through bounces that lost. Examples:
    - the R2 bounce buys on **Wednesday 4 November**: 15:40 made −12.0 and closed a slow grind sell at −7.5; 17:20 made −5.3 and closed a slow grind sell at −9.2;
    - the **Wednesday 4 November 10:40** bounce sell at 13500, which closed an EMA pullback buy at −6.7;
    - the **Monday 26 October 09:05** bounce buy at S2 (−7.9). It closed three sells at −1.9, and the 14:10 bounce at S3 then closed three sells at −10.6 instead of five at +13.4.
  - **Best:** within 5 pips, last 2 hours under 5 pips an hour: **+50.3**. It used three bounces (26 October 14:10, 4 November 10:40 and 17:20) and refused 10 at a level as fast.
  - **Worst:** within 8 pips, last 6 candles under 6 pips: **−40.8**.
- **The analyser's trend type is not a useful "how quickly".**
  - At 86 of the 89 bounces that met trend trades against them, the analyser's type was **slow grind**: on the idea, or, in a possible reversal, the last type it gave. It was **strong push** at only 3: 30 October 01:30, 2 November 09:25 and 6 November 14:35. Only the first was near a level (13400, 6.5 pips), and the within-8-pips version refused it.
  - So "slow grind = slow" lets almost every bounce at a level through, much like having no pace check. That is +26.3 within 3 pips, and −34.4 and −24.2 within 5 and 8.
- **Pips an hour separates best.**
  - Over the last 2 hours, under 5 pips an hour is the best or close to it at every distance: +43.8, +50.3 and +29.3.
  - Average candle size (high to low) does not separate well. At a bounce it is nearly always 3.5 to 6 pips: under 3 or 4 almost never counts as slow, and under 6 almost always does.
- **Today, Wednesday 11 November: every version is the same, +158.4 in 10 trades against +147.6 in 12 under the current rules (+10.8).**
  - The bounce buys at 08:35, 09:50, 09:55 and 10:00 turned from 13313.5 to 13316.4. The next significant level below the four sells was **13300, 13.5 to 16.4 pips away**, so under every version they were refused and the sells were held.
  - Under the current rules two of those bounces opened: 08:35 lost 12.0 (the stop) and 09:50 made +1.2. Without them, the sells were already being held either way. They went on to their take profits (+30 three times at 13:20 to 13:55) and the slow grind's profit lock (+10).
  - **The morning was slow on every measure**: 3.3 to 4.9 pips a candle, and mostly 1 to 8 pips an hour. Price did not reach 13300 until the 13:20 candle, about four hours later. When it did, it was moving faster: 8 to 11 pips an hour, a strong push at 13:40, and 12 to 22 pips an hour from 14:00. It broke through to 13267. This is the owner's picture: slow all morning, so it took hours to reach the level, and when it got there fast, it continued.
  - No bounce came against the sells at 13300 or after. The rule's "fast at the level, refuse" never had to act today.
- **How far to trust it:**
  - The replay covers 2½ weeks. The differences between versions come from a handful of bounces, most of them in the week of 25 October and on 4 November. Part 2's gain within 3 pips rests on one trade.
  - The owner gave no numbers. All 39 versions are shown and none is picked.
  - The 1 to 6 November week matters little here (−21 to +16), and 8 to 11 November is +5.1 for every version: the 10 November bounces (−6.8, +12.5) and today's (−12.0, +1.2) are refused in all of them.

## How it was done

- **Candles:** a read-only copy of the bot's own IG candle store, taken at 15:12 UTC today (`data/research/replay_stores/live_copy_20261111_1512/`). It holds IG's real buy and sell prices, ending with the candle that finished at 15:10 UTC.
- **Code:** a frozen copy of the committed code, `04b3a83` (the strategies read the candle store afresh on every call). The replay is the research mode (`research.long_replay`: the same engine, strategies, safety rules, paper order sender and trade manager as the bot's own replay), run week by week, exactly as in `owner_rules_20261111.md`.
- **Switches:** today's `.env` switches (`STOP_LOSS_PIPS=12`, every strategy on), with `TRADING` off for the replay. **News rules:** Finnhub's past calendar, as in the earlier reports.
- **The patch.** The rule is a patch in the research process only, applied to the engine's `_send` while the replay runs. Nothing else changes.
  - With the rule off, the patch only records, and calls the bot's own `_send` untouched. That is the "current rules" run.
  - The scripts and every run's trades and bounce records are in `data/research/replay/pace_20261111/`. The scripts are kept out of the repository, which commits only this file.
- **When the rule applies.** It is checked when a Bollinger bounce idea passes all of the bot's own rules and is about to be sent, if at that moment the bot has at least one open slow grind, EMA pullback or breakout trade in the other direction. With no such trade open, the bounce is sent exactly as now and closes nothing.
- **"At the level"** is checked at the price the bounce turned from: the lowest sell-price low of its setup's candles for a bounce buy (the highest high for a sell). That is the same reading as the significant-level section of `owner_rules_20261111.md`. The levels:
  - **00:** the round 100-pip numbers either side, such as 13300 and 13400;
  - **the weekly pivot:** the standard one from the previous week's candle, (high + low + close) ÷ 3, sell price;
  - **S2, S3, R2, R3:** the bot's own daily levels at that moment.
- **"In their direction":** the level must be beyond the entry of at least one of the open trend trades. For a bounce buy against sells, it must be below a sell's entry; for a bounce sell against buys, above a buy's entry. "At the level" means within 3, 5 or 8 pips of such a level.
- **"How quickly"** is measured on the candles finished when the bounce's 5-minute candle began, sell price:
  - **Trend type:** the analyser's own type for the trend, as on the idea. In a possible reversal the idea carries none, so the last trend type the analyser gave in the previous 12 hours is used. Slow grind is slow and strong push is fast; with no type at all, it is not slow.
  - **Candle size:** the average of high minus low over the last 6 or 12 finished 5-minute candles. "Slowly" is under 3, 4 or 6 pips.
  - **Pips an hour:** the net move from the close 2 (or 3) hours earlier to the last close, divided by 2 (or 3). "Slowly" is under 5, 8 or 12.
- **What happens:**
  - **Not at a level:** the bounce is refused.
  - **At a level, not slow:** refused, and the trend trades are left to run.
  - **At a level and slow:** the bounce is sent as now. If the order sender and safety limits open it, every trade then open in the other direction is closed at that moment, whatever its strategy.
  - **The close prices** are as in the earlier rule 1. A bounce sell opens at the sell price, where a buy closes; a bounce buy opens at the buy price, where a sell closes.
- **Prices:**
  - Entries are at IG's buy price (buys) or sell price (sells), from the candles.
  - Stops and take profits fill at their level, or at the candle's open if it opened past them.
  - The 20:30 and news closes are at the candle's open. Closes on a rejection are at its trigger price.
- **Stop first and target first.** Each run notes every bar where one candle reached both a trade's stop and its take profit or opposite band. There were none in any of the 40 runs, so the target-first run takes exactly the same path and was not run again.
- **Trades still open at the last candle** are counted at that candle's close (15:10). Under every version these are today's 13:10 breakout sell (+26.8) and 14:45 slow grind sell (−9.3).
- **Repeated ideas.** The strategy often sends the same bounce idea up to three times in one candle. Each bounce is counted once in the lists below.
- **Win and loss:** a trade with more than 0 pips is a win, below 0 a loss.

## What the analyser said from 09:00 UK today

From the bot's live record (`data/analyser/GBPUSD/state_changes.jsonl`). The replay's own analyser gives exactly the same changes at the same times. UK time is UTC in November.

- **At 09:00: trend down, slow grind**, since 06:10. "The rejection became a trend: a bounce failed under the 21 EMA and middle band, then a new low 13338.7 on the lower band 13338.5; EMAs 7/13/21 stacked down for 7 candles, close 13338.9 below them and the 100 EMA 13347.3; band sloping −0.7 pips/candle."
- **11:05 ranging.** "The down trend turned into a range: bands 15.7 pips wide (close together: 6 to 18) and flat, both bands reached, EMAs weaving, 100 EMA moved 2.7 pips."
- **11:40 emerging trend up.** Rejected at the previous day's low 13312.2: closed 13312.2 above the reversal high 13310.6.
- **11:50 emerging trend down.** Rejected at a level against the emerging up trend: closed 13308.9 below the reversal low 13311.7.
- **12:25 consolidation.** The emerging down trend was cancelled: 2 closes back above the previous day's low 13312.2.
- **12:30 emerging trend down.** Closed 13310.8 below the reversal low 13311.3, at the previous day's low.
- **12:40 consolidation.** Cancelled again: 2 closes back above 13312.2. Bands 9.1 pips wide, average body 1.6 pips.
- **13:05 emerging trend down.** Broke out of the consolidation: close 13305.8 below the lower band 13306.7.
- **13:30 trend down, slow grind.** A bounce failed under the 21 EMA and middle band, then a new low 13296.0 on the lower band 13297.6; close 13298.5 below the EMAs and the 100 EMA 13321.4; band sloping −1.7 pips/candle.
- **13:40 trend down, strong push.** "83% of the body size red, bands 2.9x as wide as 12 candles ago, 7/21 EMAs 6.3 pips apart, 5 closes on the band."
- **14:30 trend down, slow grind.** "76% of the body size red, bands 2.4x as wide as 12 candles ago, 7/21 EMAs 12.0 pips apart, 1 close on the band."
- **15:05 possible reversal up.** Rejection at the New York session low 13267.8, confirmed after a down move of 40.2 pips: closed 13277.4 above the reversal high 13271.6. "MACD histogram −1.2 still shows the down move."

### How quickly price moved today (sell price, at each half hour)

| UK | Close | Avg size, last 6 | Avg size, last 12 | Pips/h, last 2 h | Pips/h, last 3 h |
|---|---:|---:|---:|---:|---:|
| 09:00 | 13322.1 | 4.9 | 5.2 | 7.1 | 6.9 |
| 09:30 | 13315.6 | 4.2 | 4.5 | 10.4 | 6.9 |
| 10:00 | 13324.0 | 4.7 | 4.4 | 2.4 | 4.1 |
| 10:30 | 13329.0 | 3.7 | 4.2 | 5.9 | 2.5 |
| 11:00 | 13319.5 | 3.8 | 3.7 | 1.3 | 3.1 |
| 11:30 | 13313.3 | 3.9 | 3.8 | 1.2 | 1.3 |
| 12:00 | 13309.4 | 3.4 | 3.7 | 7.3 | 4.2 |
| 12:30 | 13312.7 | 3.3 | 3.4 | 8.1 | 1.0 |
| 13:00 | 13313.1 | 2.4 | 2.8 | 3.2 | 3.6 |
| 13:30 | 13297.0 | 4.1 | 3.2 | 8.1 | 10.7 |
| 14:00 | 13284.5 | 5.3 | 4.7 | 12.4 | 11.7 |
| 14:30 | 13273.8 | 6.1 | 5.7 | 19.5 | 13.2 |
| 15:00 | 13269.2 | 4.6 | 5.4 | 21.9 | 13.4 |

## Results

### All versions: trades, won, lost, pips

| At the level | Slowly = | Trades | Won | Lost | Pips | Against current | Same trades as |
|---|---|---:|---:|---:|---:|---:|:---:|
| — | current rules | 176 | 90 | 85 | +1,329.2 |  | A |
| within 3 | trend type (slow grind) | 159 | 84 | 74 | +1,355.5 | +26.3 | B |
| within 3 | last 6 candles under 3 pips | 156 | 82 | 73 | +1,351.2 | +22.0 | C |
| within 3 | last 6 candles under 4 pips | 156 | 82 | 73 | +1,351.2 | +22.0 | C |
| within 3 | last 6 candles under 6 pips | 158 | 84 | 73 | +1,365.0 | +35.8 | D |
| within 3 | last 12 candles under 3 pips | 156 | 82 | 73 | +1,351.2 | +22.0 | C |
| within 3 | last 12 candles under 4 pips | 156 | 82 | 73 | +1,351.2 | +22.0 | C |
| within 3 | last 12 candles under 6 pips | 159 | 84 | 74 | +1,355.5 | +26.3 | B |
| within 3 | last 2 h under 5 pips/h | 157 | 84 | 72 | +1,373.0 | +43.8 | E |
| within 3 | last 2 h under 8 pips/h | 157 | 84 | 72 | +1,373.0 | +43.8 | E |
| within 3 | last 2 h under 12 pips/h | 157 | 84 | 72 | +1,373.0 | +43.8 | E |
| within 3 | last 3 h under 5 pips/h | 157 | 84 | 72 | +1,373.0 | +43.8 | E |
| within 3 | last 3 h under 8 pips/h | 159 | 84 | 74 | +1,355.5 | +26.3 | B |
| within 3 | last 3 h under 12 pips/h | 159 | 84 | 74 | +1,355.5 | +26.3 | B |
| within 5 | trend type (slow grind) | 163 | 84 | 79 | +1,294.8 | -34.4 | F |
| within 5 | last 6 candles under 3 pips | 156 | 82 | 73 | +1,351.2 | +22.0 | C |
| within 5 | last 6 candles under 4 pips | 157 | 83 | 74 | +1,328.2 | -1.0 | G |
| within 5 | last 6 candles under 6 pips | 163 | 84 | 79 | +1,291.3 | -37.9 | H |
| within 5 | last 12 candles under 3 pips | 156 | 82 | 73 | +1,351.2 | +22.0 | C |
| within 5 | last 12 candles under 4 pips | 157 | 83 | 74 | +1,328.2 | -1.0 | G |
| within 5 | last 12 candles under 6 pips | 163 | 84 | 79 | +1,294.8 | -34.4 | F |
| within 5 | last 2 h under 5 pips/h | 158 | 84 | 73 | +1,379.5 | +50.3 | I |
| within 5 | last 2 h under 8 pips/h | 161 | 85 | 76 | +1,336.0 | +6.8 | J |
| within 5 | last 2 h under 12 pips/h | 163 | 84 | 79 | +1,292.2 | -37.0 | K |
| within 5 | last 3 h under 5 pips/h | 159 | 85 | 74 | +1,350.8 | +21.6 | L |
| within 5 | last 3 h under 8 pips/h | 163 | 84 | 79 | +1,294.8 | -34.4 | F |
| within 5 | last 3 h under 12 pips/h | 163 | 84 | 79 | +1,294.8 | -34.4 | F |
| within 8 | trend type (slow grind) | 165 | 86 | 79 | +1,305.0 | -24.2 | M |
| within 8 | last 6 candles under 3 pips | 156 | 82 | 73 | +1,351.2 | +22.0 | C |
| within 8 | last 6 candles under 4 pips | 157 | 83 | 74 | +1,328.2 | -1.0 | G |
| within 8 | last 6 candles under 6 pips | 165 | 85 | 80 | +1,288.4 | -40.8 | N |
| within 8 | last 12 candles under 3 pips | 156 | 82 | 73 | +1,351.2 | +22.0 | C |
| within 8 | last 12 candles under 4 pips | 157 | 83 | 74 | +1,328.2 | -1.0 | G |
| within 8 | last 12 candles under 6 pips | 164 | 85 | 79 | +1,296.9 | -32.3 | O |
| within 8 | last 2 h under 5 pips/h | 159 | 86 | 73 | +1,358.5 | +29.3 | P |
| within 8 | last 2 h under 8 pips/h | 163 | 87 | 76 | +1,346.3 | +17.1 | Q |
| within 8 | last 2 h under 12 pips/h | 165 | 86 | 79 | +1,302.5 | -26.7 | R |
| within 8 | last 3 h under 5 pips/h | 161 | 86 | 75 | +1,348.0 | +18.8 | S |
| within 8 | last 3 h under 8 pips/h | 165 | 86 | 79 | +1,305.0 | -24.2 | M |
| within 8 | last 3 h under 12 pips/h | 165 | 86 | 79 | +1,305.0 | -24.2 | M |

### By week: trades (won–lost) and pips

| At the level | Slowly = | 25 to 30 Oct | 1 to 6 Nov | 8 to 11 Nov 15:10 |
|---|---|---:|---:|---:|
| — | current rules | 59 (30–28) +224.9 | 82 (42–40) +811.0 | 35 (18–17) +293.2 |
| within 3 | trend type (slow grind) | 49 (28–20) +267.1 | 79 (40–39) +790.1 | 31 (16–15) +298.3 |
| within 3 | last 6 candles under 3 pips | 48 (26–21) +245.2 | 77 (40–37) +807.6 | 31 (16–15) +298.3 |
| within 3 | last 6 candles under 4 pips | 48 (26–21) +245.2 | 77 (40–37) +807.6 | 31 (16–15) +298.3 |
| within 3 | last 6 candles under 6 pips | 49 (28–20) +267.1 | 78 (40–38) +799.6 | 31 (16–15) +298.3 |
| within 3 | last 12 candles under 3 pips | 48 (26–21) +245.2 | 77 (40–37) +807.6 | 31 (16–15) +298.3 |
| within 3 | last 12 candles under 4 pips | 48 (26–21) +245.2 | 77 (40–37) +807.6 | 31 (16–15) +298.3 |
| within 3 | last 12 candles under 6 pips | 49 (28–20) +267.1 | 79 (40–39) +790.1 | 31 (16–15) +298.3 |
| within 3 | last 2 h under 5 pips/h | 49 (28–20) +267.1 | 77 (40–37) +807.6 | 31 (16–15) +298.3 |
| within 3 | last 2 h under 8 pips/h | 49 (28–20) +267.1 | 77 (40–37) +807.6 | 31 (16–15) +298.3 |
| within 3 | last 2 h under 12 pips/h | 49 (28–20) +267.1 | 77 (40–37) +807.6 | 31 (16–15) +298.3 |
| within 3 | last 3 h under 5 pips/h | 49 (28–20) +267.1 | 77 (40–37) +807.6 | 31 (16–15) +298.3 |
| within 3 | last 3 h under 8 pips/h | 49 (28–20) +267.1 | 79 (40–39) +790.1 | 31 (16–15) +298.3 |
| within 3 | last 3 h under 12 pips/h | 49 (28–20) +267.1 | 79 (40–39) +790.1 | 31 (16–15) +298.3 |
| within 5 | trend type (slow grind) | 52 (28–24) +200.4 | 80 (40–40) +796.1 | 31 (16–15) +298.3 |
| within 5 | last 6 candles under 3 pips | 48 (26–21) +245.2 | 77 (40–37) +807.6 | 31 (16–15) +298.3 |
| within 5 | last 6 candles under 4 pips | 49 (27–22) +222.3 | 77 (40–37) +807.6 | 31 (16–15) +298.3 |
| within 5 | last 6 candles under 6 pips | 52 (28–24) +200.4 | 80 (40–40) +792.6 | 31 (16–15) +298.3 |
| within 5 | last 12 candles under 3 pips | 48 (26–21) +245.2 | 77 (40–37) +807.6 | 31 (16–15) +298.3 |
| within 5 | last 12 candles under 4 pips | 49 (27–22) +222.3 | 77 (40–37) +807.6 | 31 (16–15) +298.3 |
| within 5 | last 12 candles under 6 pips | 52 (28–24) +200.4 | 80 (40–40) +796.1 | 31 (16–15) +298.3 |
| within 5 | last 2 h under 5 pips/h | 49 (28–20) +267.1 | 78 (40–38) +814.1 | 31 (16–15) +298.3 |
| within 5 | last 2 h under 8 pips/h | 50 (29–21) +244.2 | 80 (40–40) +793.6 | 31 (16–15) +298.3 |
| within 5 | last 2 h under 12 pips/h | 52 (28–24) +200.4 | 80 (40–40) +793.6 | 31 (16–15) +298.3 |
| within 5 | last 3 h under 5 pips/h | 50 (29–21) +244.2 | 78 (40–38) +808.4 | 31 (16–15) +298.3 |
| within 5 | last 3 h under 8 pips/h | 52 (28–24) +200.4 | 80 (40–40) +796.1 | 31 (16–15) +298.3 |
| within 5 | last 3 h under 12 pips/h | 52 (28–24) +200.4 | 80 (40–40) +796.1 | 31 (16–15) +298.3 |
| within 8 | trend type (slow grind) | 54 (29–25) +197.4 | 80 (41–39) +809.2 | 31 (16–15) +298.3 |
| within 8 | last 6 candles under 3 pips | 48 (26–21) +245.2 | 77 (40–37) +807.6 | 31 (16–15) +298.3 |
| within 8 | last 6 candles under 4 pips | 49 (27–22) +222.3 | 77 (40–37) +807.6 | 31 (16–15) +298.3 |
| within 8 | last 6 candles under 6 pips | 54 (29–25) +197.4 | 80 (40–40) +792.6 | 31 (16–15) +298.3 |
| within 8 | last 12 candles under 3 pips | 48 (26–21) +245.2 | 77 (40–37) +807.6 | 31 (16–15) +298.3 |
| within 8 | last 12 candles under 4 pips | 49 (27–22) +222.3 | 77 (40–37) +807.6 | 31 (16–15) +298.3 |
| within 8 | last 12 candles under 6 pips | 53 (28–25) +189.4 | 80 (41–39) +809.2 | 31 (16–15) +298.3 |
| within 8 | last 2 h under 5 pips/h | 50 (29–21) +233.0 | 78 (41–37) +827.2 | 31 (16–15) +298.3 |
| within 8 | last 2 h under 8 pips/h | 52 (30–22) +241.2 | 80 (41–39) +806.8 | 31 (16–15) +298.3 |
| within 8 | last 2 h under 12 pips/h | 54 (29–25) +197.4 | 80 (41–39) +806.8 | 31 (16–15) +298.3 |
| within 8 | last 3 h under 5 pips/h | 52 (30–22) +241.2 | 78 (40–38) +808.4 | 31 (16–15) +298.3 |
| within 8 | last 3 h under 8 pips/h | 54 (29–25) +197.4 | 80 (41–39) +809.2 | 31 (16–15) +298.3 |
| within 8 | last 3 h under 12 pips/h | 54 (29–25) +197.4 | 80 (41–39) +809.2 | 31 (16–15) +298.3 |

### Every Bollinger bounce that met open trend trades against it (89 in all runs)

Pace is measured on the candles finished when the bounce's candle began (sell price). Levels are those ahead of the trend trades, nearest first, measured from the high (bounce sell) or low (bounce buy) the bounce turned from.

| Bounce (UK) | Against | Turned from | Nearest significant levels ahead | Analyser | Trend type | Avg 6 | Avg 12 | Pips/h 2 h | Pips/h 3 h |
|---|---|---:|---|---|---|---:|---:|---:|---:|
| Mon 26 Oct 09:05 buy | 3: slow grind sell 26 Oct 08:25; EMA pullback sell 26 Oct 08:35; EMA pullback sell 26 Oct 08:35 | 13343.6 | S2 13338.6 (5.0 pips), S3 13328.6 (15.0 pips) | trend down | slow grind | 4.6 | 4.7 | 11.0 | 7.4 |
| Mon 26 Oct 14:10 buy | 4: EMA pullback sell 26 Oct 08:35; EMA pullback sell 26 Oct 08:35; EMA pullback sell 26 Oct 13:55; EMA pullback sell 26 Oct 13:55 | 13327.1 | S3 13328.6 (1.5 pips), S2 13338.6 (11.5 pips) | trend down | slow grind | 5.4 | 5.3 | 4.8 | 3.9 |
| Mon 26 Oct 14:15 buy | 4: EMA pullback sell 26 Oct 08:35; EMA pullback sell 26 Oct 08:35; EMA pullback sell 26 Oct 13:55; EMA pullback sell 26 Oct 13:55 | 13328.9 | S3 13328.6 (0.3 pips), S2 13338.6 (9.7 pips) | trend down | slow grind | 5.3 | 5.2 | 6.0 | 3.0 |
| Mon 26 Oct 14:20 buy | 4: EMA pullback sell 26 Oct 08:35; EMA pullback sell 26 Oct 08:35; EMA pullback sell 26 Oct 13:55; EMA pullback sell 26 Oct 13:55 | 13332.7 | S3 13328.6 (4.1 pips), S2 13338.6 (5.9 pips) | trend down | slow grind | 5.4 | 5.3 | 6.1 | 1.9 |
| Mon 26 Oct 14:45 buy | 2: EMA pullback sell 26 Oct 08:35; EMA pullback sell 26 Oct 08:35 | 13337.2 | S2 13338.6 (1.4 pips), S3 13328.6 (8.6 pips) | trend down | slow grind | 4.8 | 5.1 | 2.9 | 3.5 |
| Mon 26 Oct 15:15 buy | 2: EMA pullback sell 26 Oct 08:35; EMA pullback sell 26 Oct 08:35 | 13338.5 | S2 13338.6 (0.1 pips), S3 13328.6 (9.9 pips) | trend down | slow grind | 4.4 | 4.6 | 1.4 | 1.1 |
| Mon 26 Oct 15:20 buy | 2: EMA pullback sell 26 Oct 08:35; EMA pullback sell 26 Oct 08:35 | 13340.3 | S2 13338.6 (1.7 pips), S3 13328.6 (11.7 pips) | trend down | slow grind | 4.2 | 4.6 | 3.2 | 1.4 |
| Mon 26 Oct 15:40 buy | 2: EMA pullback sell 26 Oct 08:35; EMA pullback sell 26 Oct 08:35 | 13341.6 | S2 13338.6 (3.0 pips), S3 13328.6 (13.0 pips) | trend down | slow grind | 4.2 | 4.3 | 3.6 | 0.9 |
| Tue 27 Oct 07:20 buy | 2: slow grind sell 27 Oct 05:45; breakout sell 27 Oct 07:00 | 13315.8 | 00 13300 (15.8 pips), S2 13292.6 (23.2 pips) | trend down | slow grind | 4.1 | 3.7 | 4.6 | 6.0 |
| Tue 27 Oct 07:25 buy | 2: slow grind sell 27 Oct 05:45; breakout sell 27 Oct 07:00 | 13318.8 | 00 13300 (18.8 pips), S2 13292.6 (26.2 pips) | trend down | slow grind | 4.1 | 3.7 | 2.6 | 5.3 |
| Tue 27 Oct 07:45 buy | 2: slow grind sell 27 Oct 05:45; breakout sell 27 Oct 07:00 | 13321.6 | 00 13300 (21.6 pips), S2 13292.6 (29.0 pips) | trend down | slow grind | 4.3 | 4.3 | 2.9 | 4.4 |
| Tue 27 Oct 09:55 buy | 1: breakout sell 27 Oct 07:00 | 13307.2 | 00 13300 (7.2 pips), S2 13292.6 (14.6 pips) | trend down | slow grind | 4.4 | 4.2 | 6.0 | 4.3 |
| Tue 27 Oct 10:05 buy | 1: breakout sell 27 Oct 07:00 | 13309.6 | 00 13300 (9.6 pips), S2 13292.6 (17.0 pips) | trend down | slow grind | 4.2 | 4.2 | 2.8 | 1.4 |
| Tue 27 Oct 16:40 buy | 3: breakout sell 27 Oct 07:00; slow grind sell 27 Oct 16:05; EMA pullback sell 27 Oct 16:15 | 13304.6 | 00 13300 (4.6 pips), S2 13292.6 (12.0 pips) | trend down | slow grind | 3.4 | 3.7 | 7.6 | 2.2 |
| Tue 27 Oct 16:45 buy | 3: breakout sell 27 Oct 07:00; slow grind sell 27 Oct 16:05; EMA pullback sell 27 Oct 16:15 | 13305.9 | 00 13300 (5.9 pips), S2 13292.6 (13.3 pips) | trend down | slow grind | 3.5 | 3.7 | 4.7 | 2.1 |
| Tue 27 Oct 16:55 buy | 3: breakout sell 27 Oct 07:00; slow grind sell 27 Oct 16:05; EMA pullback sell 27 Oct 16:15 | 13306.2 | 00 13300 (6.2 pips), S2 13292.6 (13.6 pips) | trend down | slow grind | 3.2 | 3.5 | 5.2 | 2.2 |
| Tue 27 Oct 17:00 buy | 2: breakout sell 27 Oct 07:00; slow grind sell 27 Oct 16:05 | 13308.1 | 00 13300 (8.1 pips), S2 13292.6 (15.5 pips) | trend down | slow grind | 3.2 | 3.5 | 4.2 | 1.8 |
| Tue 27 Oct 17:10 buy | 2: breakout sell 27 Oct 07:00; slow grind sell 27 Oct 16:05 | 13310.9 | 00 13300 (10.9 pips), S2 13292.6 (18.3 pips) | trend down | slow grind | 3.4 | 3.4 | 0.0 | 3.8 |
| Tue 27 Oct 21:15 buy | 3: breakout sell 27 Oct 07:00; EMA pullback sell 27 Oct 17:55; EMA pullback sell 27 Oct 19:55 | 13296.4 | 00 13300 (3.6 pips), S2 13292.6 (3.8 pips) | trend down | slow grind | 3.6 | 2.8 | 8.5 | 3.6 |
| Wed 28 Oct 07:25 buy | 1: slow grind sell 28 Oct 04:45 | 13272.5 | S2 13263.6 (8.9 pips), S3 13231.6 (40.9 pips) | trend down | slow grind | 4.0 | 3.8 | 7.7 | 5.8 |
| Wed 28 Oct 10:35 buy | 1: slow grind sell 28 Oct 10:20 | 13279.8 | S2 13263.6 (16.2 pips), S3 13231.6 (48.2 pips) | trend down | slow grind | 3.9 | 3.8 | 3.1 | 0.7 |
| Wed 28 Oct 11:15 buy | 3: slow grind sell 28 Oct 10:20; EMA pullback sell 28 Oct 10:45; EMA pullback sell 28 Oct 10:45 | 13273.9 | S2 13263.6 (10.3 pips), S3 13231.6 (42.3 pips) | trend down | slow grind | 3.3 | 3.8 | 5.8 | 2.3 |
| Wed 28 Oct 11:25 buy | 3: slow grind sell 28 Oct 10:20; EMA pullback sell 28 Oct 10:45; EMA pullback sell 28 Oct 10:45 | 13273.9 | S2 13263.6 (10.3 pips), S3 13231.6 (42.3 pips) | trend down | slow grind | 3.4 | 3.9 | 4.8 | 3.5 |
| Wed 28 Oct 11:30 buy | 3: slow grind sell 28 Oct 10:20; EMA pullback sell 28 Oct 10:45; EMA pullback sell 28 Oct 10:45 | 13278.5 | S2 13263.6 (14.9 pips), S3 13231.6 (46.9 pips) | trend down | slow grind | 3.6 | 3.8 | 4.1 | 2.8 |
| Wed 28 Oct 11:35 buy | 1: slow grind sell 28 Oct 10:20 | 13279.5 | S2 13263.6 (15.9 pips), S3 13231.6 (47.9 pips) | trend down | slow grind | 3.8 | 3.7 | 2.4 | 1.8 |
| Wed 28 Oct 11:45 buy | 1: slow grind sell 28 Oct 10:20 | 13281.8 | S2 13263.6 (18.2 pips), S3 13231.6 (50.2 pips) | trend down | slow grind | 3.2 | 3.3 | 1.3 | 1.2 |
| Wed 28 Oct 15:50 sell | 1: slow grind buy 28 Oct 15:30 | 13305.1 | weekly pivot 13359.7 (54.6 pips), R2 13368.8 (63.7 pips) | trend up | slow grind | 4.0 | 4.0 | 1.4 | 1.7 |
| Thu 29 Oct 06:30 buy | 1: slow grind sell 29 Oct 05:05 | 13304.3 | 00 13300 (4.3 pips), S2 13246.9 (57.4 pips) | trend down | slow grind | 3.4 | 3.5 | 4.4 | 4.8 |
| Thu 29 Oct 09:35 buy | 1: slow grind sell 29 Oct 05:05 | 13296.0 | 00 13300 (4.0 pips), S2 13246.9 (49.1 pips) | trend down | slow grind | 5.5 | 5.6 | 7.8 | 2.7 |
| Thu 29 Oct 20:50 sell | 1: breakout buy 29 Oct 14:45 | 13384.4 | R2 13377.1 (7.3 pips), 00 13400 (15.6 pips) | trend up | slow grind | 3.5 | 4.1 | 10.6 | 4.2 |
| Thu 29 Oct 20:55 sell | 1: breakout buy 29 Oct 14:45 | 13384.4 | R2 13377.1 (7.3 pips), 00 13400 (15.6 pips) | trend up | slow grind | 3.0 | 4.2 | 8.2 | 3.9 |
| Thu 29 Oct 21:00 sell | 1: breakout buy 29 Oct 14:45 | 13383.2 | R2 13377.1 (6.1 pips), 00 13400 (16.8 pips) | trend up | slow grind | 4.0 | 4.7 | 5.0 | 1.0 |
| Thu 29 Oct 21:05 sell | 1: breakout buy 29 Oct 14:45 | 13382.1 | R2 13377.1 (5.0 pips), 00 13400 (17.9 pips) | trend up | slow grind | 3.6 | 4.2 | 2.2 | 0.2 |
| Thu 29 Oct 22:30 sell | 2: breakout buy 29 Oct 14:45; EMA pullback buy 29 Oct 22:05 | 13389.0 | 00 13400 (11.0 pips), R2 13377.1 (11.9 pips) | trend up | slow grind | 4.6 | 3.6 | 0.6 | 4.5 |
| Thu 29 Oct 23:10 sell | 2: breakout buy 29 Oct 14:45; EMA pullback buy 29 Oct 22:05 | 13387.8 | R2 13377.1 (10.7 pips), 00 13400 (12.2 pips) | trend up | slow grind | 2.8 | 2.7 | 8.5 | 2.6 |
| Thu 29 Oct 23:20 sell | 2: breakout buy 29 Oct 14:45; EMA pullback buy 29 Oct 22:05 | 13387.8 | R2 13377.1 (10.7 pips), 00 13400 (12.2 pips) | trend up | slow grind | 2.5 | 2.6 | 7.4 | 2.1 |
| Thu 29 Oct 23:30 sell | 2: breakout buy 29 Oct 14:45; EMA pullback buy 29 Oct 22:05 | 13385.9 | R2 13377.1 (8.8 pips), 00 13400 (14.1 pips) | trend up | slow grind | 2.1 | 2.4 | 6.7 | 0.2 |
| Thu 29 Oct 23:40 sell | 2: breakout buy 29 Oct 14:45; EMA pullback buy 29 Oct 22:05 | 13384.9 | R2 13377.1 (7.8 pips), 00 13400 (15.1 pips) | trend up | slow grind | 2.2 | 2.5 | 6.7 | 0.6 |
| Thu 29 Oct 23:45 sell | 2: breakout buy 29 Oct 14:45; EMA pullback buy 29 Oct 22:05 | 13383.4 | R2 13377.1 (6.3 pips), 00 13400 (16.6 pips) | trend up | slow grind | 2.3 | 2.5 | 4.0 | 1.5 |
| Fri 30 Oct 01:30 sell | 2: EMA pullback buy 29 Oct 22:05; EMA pullback buy 30 Oct 00:40 | 13406.5 | 00 13400 (6.5 pips), R2 13447.3 (40.8 pips) | trend up | strong push | 5.9 | 5.2 | 9.3 | 6.1 |
| Fri 30 Oct 01:35 sell | 2: EMA pullback buy 29 Oct 22:05; EMA pullback buy 30 Oct 00:40 | 13406.4 | 00 13400 (6.4 pips), R2 13447.3 (40.9 pips) | trend up | slow grind | 5.8 | 5.2 | 7.0 | 4.4 |
| Fri 30 Oct 01:40 sell | 2: EMA pullback buy 29 Oct 22:05; EMA pullback buy 30 Oct 00:40 | 13406.4 | 00 13400 (6.4 pips), R2 13447.3 (40.9 pips) | trend up | slow grind | 5.2 | 5.4 | 7.0 | 4.3 |
| Fri 30 Oct 01:45 sell | 2: EMA pullback buy 29 Oct 22:05; EMA pullback buy 30 Oct 00:40 | 13400.6 | 00 13400 (0.6 pips), R2 13447.3 (46.7 pips) | trend up | slow grind | 4.8 | 5.1 | 6.2 | 2.3 |
| Fri 30 Oct 07:45 sell | 3: EMA pullback buy 29 Oct 22:05; EMA pullback buy 30 Oct 00:40; EMA pullback buy 30 Oct 07:10 | 13412.1 | 00 13400 (12.1 pips), R2 13447.3 (35.2 pips) | trend up | slow grind | 6.0 | 5.0 | 8.4 | 4.2 |
| Fri 30 Oct 10:40 sell | 4: EMA pullback buy 29 Oct 22:05; slow grind buy 30 Oct 08:15; EMA pullback buy 30 Oct 09:15; EMA pullback buy 30 Oct 09:15 | 13430.6 | R2 13447.3 (16.7 pips), 00 13400 (30.6 pips) | trend up | slow grind | 3.2 | 3.1 | 7.3 | 6.8 |
| Fri 30 Oct 11:20 sell | 4: EMA pullback buy 29 Oct 22:05; EMA pullback buy 30 Oct 09:15; EMA pullback buy 30 Oct 09:15; EMA pullback buy 30 Oct 11:10 | 13433.7 | R2 13447.3 (13.6 pips), 00 13400 (33.7 pips) | possible reversal down | slow grind (last given) | 3.8 | 3.6 | 3.4 | 5.4 |
| Fri 30 Oct 16:25 sell | 1: EMA pullback buy 29 Oct 22:05 | 13406.0 | 00 13400 (6.0 pips), R2 13447.3 (41.3 pips) | trend up | slow grind | 5.9 | 6.2 | 7.0 | 1.7 |
| Mon 02 Nov 09:25 sell | 2: EMA pullback buy 02 Nov 08:30; EMA pullback buy 02 Nov 08:30 | 13448.0 | 00 13500 (52.0 pips) | possible reversal down | strong push (last given) | 6.4 | 5.6 | 14.5 | 13.8 |
| Tue 03 Nov 08:20 sell | 1: EMA pullback buy 03 Nov 08:05 | 13426.4 | R2 13480.5 (54.1 pips), 00 13500 (73.6 pips) | trend up | slow grind | 5.4 | 5.0 | 3.2 | 3.3 |
| Tue 03 Nov 08:25 sell | 1: EMA pullback buy 03 Nov 08:05 | 13426.3 | R2 13480.5 (54.2 pips), 00 13500 (73.7 pips) | trend up | slow grind | 5.4 | 4.7 | 1.7 | 2.7 |
| Wed 04 Nov 00:40 sell | 1: slow grind buy 04 Nov 00:15 | 13443.3 | R2 13458.8 (15.5 pips), R3 13483.8 (40.5 pips) | trend up | slow grind | 6.6 | 6.7 | 14.8 | 7.1 |
| Wed 04 Nov 00:50 sell | 1: slow grind buy 04 Nov 00:15 | 13443.3 | R2 13458.8 (15.5 pips), R3 13483.8 (40.5 pips) | trend up | slow grind | 5.5 | 6.1 | 12.6 | 5.7 |
| Wed 04 Nov 01:50 sell | 3: EMA pullback buy 04 Nov 01:00; EMA pullback buy 04 Nov 01:00; EMA pullback buy 04 Nov 01:00 | 13473.9 | R3 13483.8 (9.9 pips), R2 13458.8 (15.1 pips) | trend up | slow grind | 8.0 | 8.3 | 19.9 | 20.2 |
| Wed 04 Nov 02:15 sell | 3: EMA pullback buy 04 Nov 01:00; EMA pullback buy 04 Nov 01:00; EMA pullback buy 04 Nov 01:00 | 13467.0 | R2 13458.8 (8.2 pips), R3 13483.8 (16.8 pips) | possible reversal down | slow grind (last given) | 9.1 | 8.3 | 11.8 | 15.2 |
| Wed 04 Nov 10:40 sell | 1: slow grind buy 04 Nov 08:30 | 13496.0 | 00 13500 (4.0 pips) | trend up | slow grind | 6.3 | 5.6 | 0.7 | 0.1 |
| Wed 04 Nov 11:00 sell | 1: slow grind buy 04 Nov 08:30 | 13496.0 | 00 13500 (4.0 pips) | possible reversal down | slow grind (last given) | 5.5 | 5.5 | 0.0 | 1.0 |
| Wed 04 Nov 15:40 buy | 1: slow grind sell 04 Nov 15:35 | 13461.1 | R2 13458.8 (2.3 pips), 00 13400 (61.1 pips) | trend down | slow grind | 5.9 | 5.4 | 15.8 | 7.9 |
| Wed 04 Nov 16:00 buy | 1: slow grind sell 04 Nov 15:35 | 13462.4 | R2 13458.8 (3.6 pips), 00 13400 (62.4 pips) | trend down | slow grind | 5.4 | 5.6 | 8.0 | 8.5 |
| Wed 04 Nov 16:05 buy | 1: slow grind sell 04 Nov 15:35 | 13464.3 | R2 13458.8 (5.5 pips), 00 13400 (64.3 pips) | trend down | slow grind | 4.9 | 5.4 | 7.0 | 9.0 |
| Wed 04 Nov 17:10 buy | 1: slow grind sell 04 Nov 15:35 | 13453.3 | R2 13458.8 (5.5 pips), 00 13400 (53.3 pips) | trend down | slow grind | 6.6 | 5.8 | 1.2 | 6.2 |
| Wed 04 Nov 17:20 buy | 1: slow grind sell 04 Nov 15:35 | 13454.1 | R2 13458.8 (4.7 pips), 00 13400 (54.1 pips) | trend down | slow grind | 5.6 | 5.5 | 3.0 | 6.5 |
| Wed 04 Nov 17:25 buy | 1: slow grind sell 04 Nov 16:10 | 13456.7 | R2 13458.8 (2.1 pips), 00 13400 (56.7 pips) | trend down | slow grind | 6.1 | 5.5 | 4.6 | 3.7 |
| Thu 05 Nov 08:15 buy | 1: slow grind sell 05 Nov 08:00 | 13464.4 | 00 13400 (64.4 pips), S2 13390.4 (74.0 pips) | trend down | slow grind | 5.3 | 5.7 | 5.5 | 4.6 |
| Thu 05 Nov 08:20 buy | 1: slow grind sell 05 Nov 08:00 | 13467.2 | 00 13400 (67.2 pips), S2 13390.4 (76.8 pips) | trend down | slow grind | 5.4 | 5.6 | 5.2 | 3.9 |
| Thu 05 Nov 08:50 buy | 1: slow grind sell 05 Nov 08:00 | 13468.6 | 00 13400 (68.6 pips), S2 13390.4 (78.2 pips) | trend down | slow grind | 4.8 | 5.1 | 8.6 | 4.6 |
| Thu 05 Nov 18:00 sell | 1: slow grind buy 05 Nov 17:45 | 13486.0 | 00 13500 (14.0 pips), R2 13545.6 (59.6 pips) | trend up | slow grind | 3.7 | 4.4 | 3.1 | 6.9 |
| Thu 05 Nov 18:10 sell | 1: slow grind buy 05 Nov 17:45 | 13485.3 | 00 13500 (14.7 pips), R2 13545.6 (60.3 pips) | trend up | slow grind | 4.1 | 4.0 | 9.2 | 6.3 |
| Thu 05 Nov 18:15 sell | 1: slow grind buy 05 Nov 17:45 | 13485.3 | 00 13500 (14.7 pips), R2 13545.6 (60.3 pips) | trend up | slow grind | 3.8 | 4.0 | 5.8 | 5.0 |
| Fri 06 Nov 03:55 buy | 4: breakout sell 05 Nov 18:35; slow grind sell 06 Nov 01:55; EMA pullback sell 06 Nov 02:00; EMA pullback sell 06 Nov 02:55 | 13428.7 | 00 13400 (28.7 pips), S2 13399.1 (29.6 pips) | trend down | slow grind | 2.8 | 3.0 | 7.6 | 7.0 |
| Fri 06 Nov 04:35 buy | 6: breakout sell 05 Nov 18:35; slow grind sell 06 Nov 01:55; EMA pullback sell 06 Nov 02:00; EMA pullback sell 06 Nov 02:55; EMA pullback sell 06 Nov 04:10; EMA pullback sell 06 Nov 04:10 | 13425.2 | 00 13400 (25.2 pips), S2 13399.1 (26.1 pips) | trend down | slow grind | 3.2 | 3.2 | 8.3 | 6.0 |
| Fri 06 Nov 04:50 buy | 6: breakout sell 05 Nov 18:35; slow grind sell 06 Nov 01:55; EMA pullback sell 06 Nov 02:00; EMA pullback sell 06 Nov 02:55; EMA pullback sell 06 Nov 04:10; EMA pullback sell 06 Nov 04:10 | 13425.8 | 00 13400 (25.8 pips), S2 13399.1 (26.7 pips) | trend down | slow grind | 2.6 | 2.8 | 6.6 | 5.6 |
| Fri 06 Nov 07:50 buy | 7: slow grind sell 06 Nov 01:55; EMA pullback sell 06 Nov 02:00; EMA pullback sell 06 Nov 02:55; EMA pullback sell 06 Nov 04:10; EMA pullback sell 06 Nov 04:10; EMA pullback sell 06 Nov 06:45; EMA pullback sell 06 Nov 06:45 | 13394.1 | S2 13399.1 (5.0 pips), 00 13400 (5.9 pips) | trend down | slow grind | 6.7 | 6.8 | 12.4 | 10.1 |
| Fri 06 Nov 08:05 buy | 7: slow grind sell 06 Nov 01:55; EMA pullback sell 06 Nov 02:00; EMA pullback sell 06 Nov 02:55; EMA pullback sell 06 Nov 04:10; EMA pullback sell 06 Nov 04:10; EMA pullback sell 06 Nov 06:45; EMA pullback sell 06 Nov 06:45 | 13395.6 | S2 13399.1 (3.5 pips), 00 13400 (4.4 pips) | trend down | slow grind | 6.2 | 6.5 | 10.2 | 9.7 |
| Fri 06 Nov 08:15 buy | 7: slow grind sell 06 Nov 01:55; EMA pullback sell 06 Nov 02:00; EMA pullback sell 06 Nov 02:55; EMA pullback sell 06 Nov 04:10; EMA pullback sell 06 Nov 04:10; EMA pullback sell 06 Nov 06:45; EMA pullback sell 06 Nov 06:45 | 13395.8 | S2 13399.1 (3.3 pips), 00 13400 (4.2 pips) | trend down | slow grind | 6.4 | 6.3 | 7.9 | 6.5 |
| Fri 06 Nov 10:35 buy | 10: slow grind sell 06 Nov 01:55; EMA pullback sell 06 Nov 02:00; EMA pullback sell 06 Nov 02:55; EMA pullback sell 06 Nov 04:10; EMA pullback sell 06 Nov 04:10; EMA pullback sell 06 Nov 06:45; EMA pullback sell 06 Nov 06:45; EMA pullback sell 06 Nov 08:40; EMA pullback sell 06 Nov 08:40; EMA pullback sell 06 Nov 09:00 | 13380.7 | weekly pivot 13364.2 (16.5 pips), S3 13362.4 (18.3 pips) | possible reversal up | slow grind (last given) | 4.4 | 4.5 | 7.0 | 3.2 |
| Fri 06 Nov 13:20 buy | 8: slow grind sell 06 Nov 01:55; EMA pullback sell 06 Nov 02:00; EMA pullback sell 06 Nov 02:55; EMA pullback sell 06 Nov 04:10; EMA pullback sell 06 Nov 04:10; EMA pullback sell 06 Nov 06:45; EMA pullback sell 06 Nov 06:45; EMA pullback sell 06 Nov 08:40 | 13380.5 | weekly pivot 13364.2 (16.3 pips), S3 13362.4 (18.1 pips) | trend down | slow grind | 5.0 | 5.4 | 4.5 | 1.9 |
| Fri 06 Nov 14:35 buy | 9: EMA pullback sell 06 Nov 02:55; EMA pullback sell 06 Nov 04:10; EMA pullback sell 06 Nov 04:10; EMA pullback sell 06 Nov 06:45; EMA pullback sell 06 Nov 06:45; EMA pullback sell 06 Nov 08:40; EMA pullback sell 06 Nov 13:30; EMA pullback sell 06 Nov 13:30; EMA pullback sell 06 Nov 13:30 | 13341.4 | S3 13362.4 (21.0 pips), weekly pivot 13364.2 (22.8 pips) | possible reversal up | strong push (last given) | 7.5 | 8.2 | 20.9 | 13.7 |
| Mon 09 Nov 09:00 sell | 1: breakout buy 09 Nov 07:55 | 13415.5 | 00 13400 (15.5 pips), R3 13397.1 (18.4 pips) | trend up | slow grind | 4.6 | 5.4 | 11.2 | 9.5 |
| Mon 09 Nov 09:20 sell | 1: breakout buy 09 Nov 07:55 | 13411.7 | 00 13400 (11.7 pips), R3 13397.1 (14.6 pips) | trend up | slow grind | 3.7 | 4.6 | 11.2 | 7.2 |
| Mon 09 Nov 10:55 sell | 3: breakout buy 09 Nov 07:55; slow grind buy 09 Nov 09:35; EMA pullback buy 09 Nov 10:30 | 13422.9 | 00 13400 (22.9 pips), R3 13397.1 (25.8 pips) | possible reversal down | slow grind (last given) | 3.0 | 2.9 | 3.8 | 9.3 |
| Mon 09 Nov 20:30 sell | 1: breakout buy 09 Nov 07:55 | 13440.6 | 00 13400 (40.6 pips), R3 13397.1 (43.5 pips) | trend up | slow grind | 3.1 | 4.7 | 5.6 | 3.7 |
| Tue 10 Nov 07:55 sell | 3: EMA pullback buy 10 Nov 05:00; EMA pullback buy 10 Nov 06:10; EMA pullback buy 10 Nov 07:20 | 13457.9 | R2 13498.9 (41.0 pips), 00 13500 (42.1 pips) | trend up | slow grind | 4.1 | 3.8 | 3.4 | 1.7 |
| Tue 10 Nov 08:20 sell | 3: EMA pullback buy 10 Nov 05:00; EMA pullback buy 10 Nov 06:10; EMA pullback buy 10 Nov 07:20 | 13457.1 | R2 13498.9 (41.8 pips), 00 13500 (42.9 pips) | trend up | slow grind | 5.3 | 4.4 | 0.0 | 1.1 |
| Tue 10 Nov 08:45 sell | 3: EMA pullback buy 10 Nov 05:00; EMA pullback buy 10 Nov 06:10; EMA pullback buy 10 Nov 07:20 | 13458.6 | R2 13498.9 (40.3 pips), 00 13500 (41.4 pips) | trend up | slow grind | 4.0 | 4.6 | 2.8 | 3.2 |
| Tue 10 Nov 08:55 sell | 3: EMA pullback buy 10 Nov 05:00; EMA pullback buy 10 Nov 06:10; EMA pullback buy 10 Nov 07:20 | 13457.5 | R2 13498.9 (41.4 pips), 00 13500 (42.5 pips) | trend up | slow grind | 3.6 | 4.3 | 2.8 | 2.3 |
| Wed 11 Nov 08:35 buy | 4: EMA pullback sell 11 Nov 07:30; slow grind sell 11 Nov 08:10; EMA pullback sell 11 Nov 08:15; EMA pullback sell 11 Nov 08:15 | 13314.2 | 00 13300 (14.2 pips), S2 13226.1 (88.1 pips) | trend down | slow grind | 5.8 | 5.1 | 5.9 | 8.4 |
| Wed 11 Nov 09:50 buy | 4: EMA pullback sell 11 Nov 07:30; slow grind sell 11 Nov 08:10; EMA pullback sell 11 Nov 08:15; EMA pullback sell 11 Nov 08:15 | 13313.5 | 00 13300 (13.5 pips), S2 13226.1 (87.4 pips) | trend down | slow grind | 3.9 | 4.2 | 3.4 | 4.3 |
| Wed 11 Nov 09:55 buy | 4: EMA pullback sell 11 Nov 07:30; slow grind sell 11 Nov 08:10; EMA pullback sell 11 Nov 08:15; EMA pullback sell 11 Nov 08:15 | 13314.9 | 00 13300 (14.9 pips), S2 13226.1 (88.8 pips) | trend down | slow grind | 4.2 | 4.3 | 4.0 | 4.4 |
| Wed 11 Nov 10:00 buy | 4: EMA pullback sell 11 Nov 07:30; slow grind sell 11 Nov 08:10; EMA pullback sell 11 Nov 08:15; EMA pullback sell 11 Nov 08:15 | 13316.4 | 00 13300 (16.4 pips), S2 13226.1 (90.3 pips) | trend down | slow grind | 4.7 | 4.4 | 2.4 | 4.1 |

### What each version did with them

**A: +1,329.2 in 176 trades** — current rules

- Mon 26 Oct 09:05 bounce buy: opened, nothing closed; the bounce itself made -7.9
- Mon 26 Oct 14:10 bounce buy: opened, nothing closed; the bounce itself made +7.2
- Tue 27 Oct 07:20 bounce buy: opened, nothing closed; the bounce itself made -5.0
- Tue 27 Oct 09:55 bounce buy: opened, nothing closed; the bounce itself made -4.6
- Tue 27 Oct 16:40 bounce buy: opened, nothing closed; the bounce itself made +5.8
- Wed 28 Oct 07:25 bounce buy: opened, nothing closed; the bounce itself made +11.4
- Wed 28 Oct 10:35 bounce buy: opened, nothing closed; the bounce itself made -12.0
- Wed 28 Oct 11:15 bounce buy: opened, nothing closed; the bounce itself made +7.4
- Wed 28 Oct 15:50 bounce sell: opened, nothing closed; the bounce itself made -7.7
- Fri 30 Oct 07:45 bounce sell: opened, nothing closed; the bounce itself made -12.0
- Fri 30 Oct 10:40 bounce sell: opened, nothing closed; the bounce itself made -1.8
- Fri 30 Oct 16:25 bounce sell: opened, nothing closed; the bounce itself made +6.4
- Mon 02 Nov 09:25 bounce sell: opened, nothing closed; the bounce itself made +25.8
- Tue 03 Nov 08:20 bounce sell: opened, nothing closed; the bounce itself made +3.8
- Wed 04 Nov 10:40 bounce sell: opened, nothing closed; the bounce itself made -7.5
- Wed 04 Nov 15:40 bounce buy: opened, nothing closed; the bounce itself made -12.0
- Wed 04 Nov 17:10 bounce buy: opened, nothing closed; the bounce itself made +4.2
- Thu 05 Nov 08:15 bounce buy: opened, nothing closed; the bounce itself made -12.0
- Thu 05 Nov 08:50 bounce buy: opened, nothing closed; the bounce itself made -4.8
- Tue 10 Nov 07:55 bounce sell: opened, nothing closed; the bounce itself made -6.8
- Tue 10 Nov 08:45 bounce sell: opened, nothing closed; the bounce itself made +12.5
- Wed 11 Nov 08:35 bounce buy: opened, nothing closed; the bounce itself made -12.0
- Wed 11 Nov 09:50 bounce buy: opened, nothing closed; the bounce itself made +1.2
- Sent but not opened by the bot's own order sender and safety limits, as now (65): 26 Oct 14:15 buy, 26 Oct 14:20 buy, 26 Oct 14:45 buy, 26 Oct 15:15 buy, 26 Oct 15:20 buy, 26 Oct 15:40 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 27 Oct 10:05 buy, 27 Oct 16:45 buy, 27 Oct 16:55 buy, 27 Oct 17:00 buy, 27 Oct 17:10 buy, 27 Oct 21:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 29 Oct 06:30 buy, 29 Oct 09:35 buy, 29 Oct 20:50 sell, 29 Oct 20:55 sell, 29 Oct 21:00 sell, 29 Oct 21:05 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 29 Oct 23:40 sell, 29 Oct 23:45 sell, 30 Oct 01:30 sell, 30 Oct 01:35 sell, 30 Oct 01:40 sell, 30 Oct 01:45 sell, 30 Oct 11:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 04 Nov 11:00 sell, 04 Nov 16:00 buy, 04 Nov 16:05 buy, 04 Nov 17:20 buy, 05 Nov 08:20 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 07:50 buy, 06 Nov 08:05 buy, 06 Nov 08:15 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 08:20 sell, 10 Nov 08:55 sell, 11 Nov 09:55 buy, 11 Nov 10:00 buy

**B: +1,355.5 in 159 trades** — within 3, trend type (slow grind); within 3, last 12 candles under 6 pips; within 3, last 3 h under 8 pips/h; within 3, last 3 h under 12 pips/h

- Mon 26 Oct 14:10 bounce buy: **used at S3 13328.6**, slow: opened and closed 5 trade(s), +13.4 on the part closed (EMA pullback sell 26 Oct 08:35 +12.0; EMA pullback sell 26 Oct 08:35 +12.0; EMA pullback sell 26 Oct 13:55 -4.8; EMA pullback sell 26 Oct 13:55 -4.8; level reversal sell 26 Oct 13:55 -1.0); the bounce itself made +7.2
- Fri 30 Oct 01:45 bounce sell: valid at 00 13400, slow, but the order sender did not open it
- Wed 04 Nov 15:40 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -7.5 on the part closed (slow grind sell 04 Nov 15:35 -7.5); the bounce itself made -12.0
- Wed 04 Nov 17:25 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -13.0 on the part closed (slow grind sell 04 Nov 16:10 -13.0); the bounce itself made -6.6
- Refused, not at a significant level (77): 26 Oct 09:05 buy, 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 27 Oct 09:55 buy, 27 Oct 10:05 buy, 27 Oct 16:40 buy, 27 Oct 16:45 buy, 27 Oct 16:55 buy, 27 Oct 17:00 buy, 27 Oct 17:10 buy, 27 Oct 21:15 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 06:30 buy, 29 Oct 09:35 buy, 29 Oct 20:50 sell, 29 Oct 20:55 sell, 29 Oct 21:00 sell, 29 Oct 21:05 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 29 Oct 23:40 sell, 29 Oct 23:45 sell, 30 Oct 01:30 sell, 30 Oct 01:35 sell, 30 Oct 01:40 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 30 Oct 16:25 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 04 Nov 10:40 sell, 04 Nov 11:00 sell, 04 Nov 17:10 buy, 04 Nov 17:20 buy, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 07:50 buy, 06 Nov 08:05 buy, 06 Nov 08:15 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy

**C: +1,351.2 in 156 trades** — within 3, last 6 candles under 3 pips; within 3, last 6 candles under 4 pips; within 3, last 12 candles under 3 pips; within 3, last 12 candles under 4 pips; within 5, last 6 candles under 3 pips; within 5, last 12 candles under 3 pips; within 8, last 6 candles under 3 pips; within 8, last 12 candles under 3 pips

- *within 3, last 6 candles under 3 pips; within 3, last 6 candles under 4 pips; within 3, last 12 candles under 3 pips; within 3, last 12 candles under 4 pips:*
  - Mon 26 Oct 14:10 bounce buy: **refused, moving fast**, at S3 13328.6: trend trades held
  - Mon 26 Oct 14:15 bounce buy: **refused, moving fast**, at S3 13328.6: trend trades held
  - Mon 26 Oct 14:45 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:15 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:20 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:40 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Fri 30 Oct 01:45 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Wed 04 Nov 15:40 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Refused, not at a significant level (80): 26 Oct 09:05 buy, 26 Oct 14:20 buy, 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 27 Oct 09:55 buy, 27 Oct 10:05 buy, 27 Oct 16:40 buy, 27 Oct 16:45 buy, 27 Oct 16:55 buy, 27 Oct 17:00 buy, 27 Oct 17:10 buy, 27 Oct 21:15 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 06:30 buy, 29 Oct 09:35 buy, 29 Oct 20:50 sell, 29 Oct 20:55 sell, 29 Oct 21:00 sell, 29 Oct 21:05 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 29 Oct 23:40 sell, 29 Oct 23:45 sell, 30 Oct 01:30 sell, 30 Oct 01:35 sell, 30 Oct 01:40 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 30 Oct 16:25 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 04 Nov 10:40 sell, 04 Nov 11:00 sell, 04 Nov 16:00 buy, 04 Nov 16:05 buy, 04 Nov 17:10 buy, 04 Nov 17:20 buy, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 07:50 buy, 06 Nov 08:05 buy, 06 Nov 08:15 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy
- *within 5, last 6 candles under 3 pips:*
  - Mon 26 Oct 09:05 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 14:10 bounce buy: **refused, moving fast**, at S3 13328.6: trend trades held
  - Mon 26 Oct 14:15 bounce buy: **refused, moving fast**, at S3 13328.6: trend trades held
  - Mon 26 Oct 14:20 bounce buy: **refused, moving fast**, at S3 13328.6: trend trades held
  - Mon 26 Oct 14:45 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:15 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:20 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:40 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Tue 27 Oct 16:40 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
  - Tue 27 Oct 21:15 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
  - Thu 29 Oct 06:30 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
  - Thu 29 Oct 09:35 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
  - Thu 29 Oct 21:05 bounce sell: **refused, moving fast**, at R2 13377.1: trend trades held
  - Fri 30 Oct 01:45 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Wed 04 Nov 10:40 bounce sell: **refused, moving fast**, at 00 13500: trend trades held
  - Wed 04 Nov 11:00 bounce sell: **refused, moving fast**, at 00 13500: trend trades held
  - Wed 04 Nov 15:40 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Wed 04 Nov 16:00 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Wed 04 Nov 17:20 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Fri 06 Nov 07:50 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Fri 06 Nov 08:05 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Fri 06 Nov 08:15 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Refused, not at a significant level (66): 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 27 Oct 09:55 buy, 27 Oct 10:05 buy, 27 Oct 16:45 buy, 27 Oct 16:55 buy, 27 Oct 17:00 buy, 27 Oct 17:10 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 20:50 sell, 29 Oct 20:55 sell, 29 Oct 21:00 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 29 Oct 23:40 sell, 29 Oct 23:45 sell, 30 Oct 01:30 sell, 30 Oct 01:35 sell, 30 Oct 01:40 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 30 Oct 16:25 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 04 Nov 16:05 buy, 04 Nov 17:10 buy, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy
- *within 5, last 12 candles under 3 pips:*
  - Mon 26 Oct 09:05 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 14:10 bounce buy: **refused, moving fast**, at S3 13328.6: trend trades held
  - Mon 26 Oct 14:15 bounce buy: **refused, moving fast**, at S3 13328.6: trend trades held
  - Mon 26 Oct 14:20 bounce buy: **refused, moving fast**, at S3 13328.6: trend trades held
  - Mon 26 Oct 14:45 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:15 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:20 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:40 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Tue 27 Oct 16:40 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
  - Tue 27 Oct 21:15 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 06:30 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
  - Thu 29 Oct 09:35 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
  - Thu 29 Oct 21:05 bounce sell: **refused, moving fast**, at R2 13377.1: trend trades held
  - Fri 30 Oct 01:45 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Wed 04 Nov 10:40 bounce sell: **refused, moving fast**, at 00 13500: trend trades held
  - Wed 04 Nov 11:00 bounce sell: **refused, moving fast**, at 00 13500: trend trades held
  - Wed 04 Nov 15:40 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Wed 04 Nov 16:00 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Wed 04 Nov 17:20 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Fri 06 Nov 07:50 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Fri 06 Nov 08:05 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Fri 06 Nov 08:15 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Refused, not at a significant level (66): 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 27 Oct 09:55 buy, 27 Oct 10:05 buy, 27 Oct 16:45 buy, 27 Oct 16:55 buy, 27 Oct 17:00 buy, 27 Oct 17:10 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 20:50 sell, 29 Oct 20:55 sell, 29 Oct 21:00 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 29 Oct 23:40 sell, 29 Oct 23:45 sell, 30 Oct 01:30 sell, 30 Oct 01:35 sell, 30 Oct 01:40 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 30 Oct 16:25 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 04 Nov 16:05 buy, 04 Nov 17:10 buy, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy
- *within 8, last 6 candles under 3 pips:*
  - Mon 26 Oct 09:05 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 14:10 bounce buy: **refused, moving fast**, at S3 13328.6: trend trades held
  - Mon 26 Oct 14:15 bounce buy: **refused, moving fast**, at S3 13328.6: trend trades held
  - Mon 26 Oct 14:20 bounce buy: **refused, moving fast**, at S3 13328.6: trend trades held
  - Mon 26 Oct 14:45 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:15 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:20 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:40 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Tue 27 Oct 09:55 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
  - Tue 27 Oct 16:40 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
  - Tue 27 Oct 16:45 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
  - Tue 27 Oct 16:55 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
  - Tue 27 Oct 21:15 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
  - Thu 29 Oct 06:30 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
  - Thu 29 Oct 09:35 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
  - Thu 29 Oct 20:50 bounce sell: **refused, moving fast**, at R2 13377.1: trend trades held
  - Thu 29 Oct 20:55 bounce sell: **refused, moving fast**, at R2 13377.1: trend trades held
  - Thu 29 Oct 21:00 bounce sell: **refused, moving fast**, at R2 13377.1: trend trades held
  - Thu 29 Oct 21:05 bounce sell: **refused, moving fast**, at R2 13377.1: trend trades held
  - Thu 29 Oct 23:40 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Thu 29 Oct 23:45 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Fri 30 Oct 01:30 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Fri 30 Oct 01:35 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Fri 30 Oct 01:40 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Fri 30 Oct 01:45 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Fri 30 Oct 16:25 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Wed 04 Nov 10:40 bounce sell: **refused, moving fast**, at 00 13500: trend trades held
  - Wed 04 Nov 11:00 bounce sell: **refused, moving fast**, at 00 13500: trend trades held
  - Wed 04 Nov 15:40 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Wed 04 Nov 16:00 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Wed 04 Nov 16:05 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Wed 04 Nov 17:10 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Wed 04 Nov 17:20 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Fri 06 Nov 07:50 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Fri 06 Nov 08:05 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Fri 06 Nov 08:15 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Refused, not at a significant level (52): 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 27 Oct 10:05 buy, 27 Oct 17:00 buy, 27 Oct 17:10 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy
- *within 8, last 12 candles under 3 pips:*
  - Mon 26 Oct 09:05 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 14:10 bounce buy: **refused, moving fast**, at S3 13328.6: trend trades held
  - Mon 26 Oct 14:15 bounce buy: **refused, moving fast**, at S3 13328.6: trend trades held
  - Mon 26 Oct 14:20 bounce buy: **refused, moving fast**, at S3 13328.6: trend trades held
  - Mon 26 Oct 14:45 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:15 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:20 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:40 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Tue 27 Oct 09:55 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
  - Tue 27 Oct 16:40 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
  - Tue 27 Oct 16:45 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
  - Tue 27 Oct 16:55 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
  - Tue 27 Oct 21:15 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 06:30 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
  - Thu 29 Oct 09:35 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
  - Thu 29 Oct 20:50 bounce sell: **refused, moving fast**, at R2 13377.1: trend trades held
  - Thu 29 Oct 20:55 bounce sell: **refused, moving fast**, at R2 13377.1: trend trades held
  - Thu 29 Oct 21:00 bounce sell: **refused, moving fast**, at R2 13377.1: trend trades held
  - Thu 29 Oct 21:05 bounce sell: **refused, moving fast**, at R2 13377.1: trend trades held
  - Thu 29 Oct 23:40 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Thu 29 Oct 23:45 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Fri 30 Oct 01:30 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Fri 30 Oct 01:35 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Fri 30 Oct 01:40 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Fri 30 Oct 01:45 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Fri 30 Oct 16:25 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Wed 04 Nov 10:40 bounce sell: **refused, moving fast**, at 00 13500: trend trades held
  - Wed 04 Nov 11:00 bounce sell: **refused, moving fast**, at 00 13500: trend trades held
  - Wed 04 Nov 15:40 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Wed 04 Nov 16:00 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Wed 04 Nov 16:05 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Wed 04 Nov 17:10 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Wed 04 Nov 17:20 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Fri 06 Nov 07:50 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Fri 06 Nov 08:05 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Fri 06 Nov 08:15 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Refused, not at a significant level (52): 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 27 Oct 10:05 buy, 27 Oct 17:00 buy, 27 Oct 17:10 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy

**D: +1,365.0 in 158 trades** — within 3, last 6 candles under 6 pips

- Mon 26 Oct 14:10 bounce buy: **used at S3 13328.6**, slow: opened and closed 5 trade(s), +13.4 on the part closed (EMA pullback sell 26 Oct 08:35 +12.0; EMA pullback sell 26 Oct 08:35 +12.0; EMA pullback sell 26 Oct 13:55 -4.8; EMA pullback sell 26 Oct 13:55 -4.8; level reversal sell 26 Oct 13:55 -1.0); the bounce itself made +7.2
- Fri 30 Oct 01:45 bounce sell: valid at 00 13400, slow, but the order sender did not open it
- Wed 04 Nov 15:40 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -7.5 on the part closed (slow grind sell 04 Nov 15:35 -7.5); the bounce itself made -12.0
- Wed 04 Nov 17:25 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
- Refused, not at a significant level (77): 26 Oct 09:05 buy, 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 27 Oct 09:55 buy, 27 Oct 10:05 buy, 27 Oct 16:40 buy, 27 Oct 16:45 buy, 27 Oct 16:55 buy, 27 Oct 17:00 buy, 27 Oct 17:10 buy, 27 Oct 21:15 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 06:30 buy, 29 Oct 09:35 buy, 29 Oct 20:50 sell, 29 Oct 20:55 sell, 29 Oct 21:00 sell, 29 Oct 21:05 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 29 Oct 23:40 sell, 29 Oct 23:45 sell, 30 Oct 01:30 sell, 30 Oct 01:35 sell, 30 Oct 01:40 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 30 Oct 16:25 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 04 Nov 10:40 sell, 04 Nov 11:00 sell, 04 Nov 17:10 buy, 04 Nov 17:20 buy, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 07:50 buy, 06 Nov 08:05 buy, 06 Nov 08:15 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy

**E: +1,373.0 in 157 trades** — within 3, last 2 h under 5 pips/h; within 3, last 2 h under 8 pips/h; within 3, last 2 h under 12 pips/h; within 3, last 3 h under 5 pips/h

- *within 3, last 2 h under 5 pips/h:*
  - Mon 26 Oct 14:10 bounce buy: **used at S3 13328.6**, slow: opened and closed 5 trade(s), +13.4 on the part closed (EMA pullback sell 26 Oct 08:35 +12.0; EMA pullback sell 26 Oct 08:35 +12.0; EMA pullback sell 26 Oct 13:55 -4.8; EMA pullback sell 26 Oct 13:55 -4.8; level reversal sell 26 Oct 13:55 -1.0); the bounce itself made +7.2
  - Fri 30 Oct 01:45 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Wed 04 Nov 15:40 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Refused, not at a significant level (79): 26 Oct 09:05 buy, 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 27 Oct 09:55 buy, 27 Oct 10:05 buy, 27 Oct 16:40 buy, 27 Oct 16:45 buy, 27 Oct 16:55 buy, 27 Oct 17:00 buy, 27 Oct 17:10 buy, 27 Oct 21:15 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 06:30 buy, 29 Oct 09:35 buy, 29 Oct 20:50 sell, 29 Oct 20:55 sell, 29 Oct 21:00 sell, 29 Oct 21:05 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 29 Oct 23:40 sell, 29 Oct 23:45 sell, 30 Oct 01:30 sell, 30 Oct 01:35 sell, 30 Oct 01:40 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 30 Oct 16:25 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 04 Nov 10:40 sell, 04 Nov 11:00 sell, 04 Nov 16:00 buy, 04 Nov 16:05 buy, 04 Nov 17:10 buy, 04 Nov 17:20 buy, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 07:50 buy, 06 Nov 08:05 buy, 06 Nov 08:15 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy
- *within 3, last 2 h under 8 pips/h; within 3, last 2 h under 12 pips/h; within 3, last 3 h under 5 pips/h:*
  - Mon 26 Oct 14:10 bounce buy: **used at S3 13328.6**, slow: opened and closed 5 trade(s), +13.4 on the part closed (EMA pullback sell 26 Oct 08:35 +12.0; EMA pullback sell 26 Oct 08:35 +12.0; EMA pullback sell 26 Oct 13:55 -4.8; EMA pullback sell 26 Oct 13:55 -4.8; level reversal sell 26 Oct 13:55 -1.0); the bounce itself made +7.2
  - Fri 30 Oct 01:45 bounce sell: valid at 00 13400, slow, but the order sender did not open it
  - Wed 04 Nov 15:40 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Refused, not at a significant level (79): 26 Oct 09:05 buy, 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 27 Oct 09:55 buy, 27 Oct 10:05 buy, 27 Oct 16:40 buy, 27 Oct 16:45 buy, 27 Oct 16:55 buy, 27 Oct 17:00 buy, 27 Oct 17:10 buy, 27 Oct 21:15 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 06:30 buy, 29 Oct 09:35 buy, 29 Oct 20:50 sell, 29 Oct 20:55 sell, 29 Oct 21:00 sell, 29 Oct 21:05 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 29 Oct 23:40 sell, 29 Oct 23:45 sell, 30 Oct 01:30 sell, 30 Oct 01:35 sell, 30 Oct 01:40 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 30 Oct 16:25 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 04 Nov 10:40 sell, 04 Nov 11:00 sell, 04 Nov 16:00 buy, 04 Nov 16:05 buy, 04 Nov 17:10 buy, 04 Nov 17:20 buy, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 07:50 buy, 06 Nov 08:05 buy, 06 Nov 08:15 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy

**F: +1,294.8 in 163 trades** — within 5, trend type (slow grind); within 5, last 12 candles under 6 pips; within 5, last 3 h under 8 pips/h; within 5, last 3 h under 12 pips/h

- *within 5, trend type (slow grind); within 5, last 3 h under 12 pips/h:*
  - Mon 26 Oct 09:05 bounce buy: **used at S2 13338.6**, slow: opened and closed 3 trade(s), -1.9 on the part closed (slow grind sell 26 Oct 08:25 +3.5; EMA pullback sell 26 Oct 08:35 -2.7; EMA pullback sell 26 Oct 08:35 -2.7); the bounce itself made -7.9
  - Mon 26 Oct 14:10 bounce buy: **used at S3 13328.6**, slow: opened and closed 3 trade(s), -10.6 on the part closed (EMA pullback sell 26 Oct 13:55 -4.8; EMA pullback sell 26 Oct 13:55 -4.8; level reversal sell 26 Oct 13:55 -1.0); the bounce itself made +7.2
  - Tue 27 Oct 16:40 bounce buy: **used at 00 13300**, slow: opened and closed 3 trade(s), +9.3 on the part closed (breakout sell 27 Oct 07:00 +15.2; slow grind sell 27 Oct 16:05 -0.6; EMA pullback sell 27 Oct 16:15 -5.3); the bounce itself made +5.8
  - Tue 27 Oct 21:15 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 06:30 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 09:35 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 21:05 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Fri 30 Oct 01:45 bounce sell: valid at 00 13400, slow, but the order sender did not open it
  - Wed 04 Nov 10:40 bounce sell: **used at 00 13500**, slow: opened and closed 1 trade(s), -6.7 on the part closed (slow grind buy 04 Nov 08:30 -6.7); the bounce itself made -7.5
  - Wed 04 Nov 15:40 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -7.5 on the part closed (slow grind sell 04 Nov 15:35 -7.5); the bounce itself made -12.0
  - Wed 04 Nov 17:20 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -9.2 on the part closed (slow grind sell 04 Nov 16:10 -9.2); the bounce itself made -5.2
  - Fri 06 Nov 07:50 bounce buy: valid at S2 13399.1, slow, but the order sender did not open it
  - Fri 06 Nov 08:05 bounce buy: valid at S2 13399.1, slow, but the order sender did not open it
  - Fri 06 Nov 08:15 bounce buy: valid at S2 13399.1, slow, but the order sender did not open it
  - Refused, not at a significant level (61): 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 27 Oct 09:55 buy, 27 Oct 10:05 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 20:50 sell, 29 Oct 20:55 sell, 29 Oct 21:00 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 29 Oct 23:40 sell, 29 Oct 23:45 sell, 30 Oct 01:30 sell, 30 Oct 01:35 sell, 30 Oct 01:40 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 30 Oct 16:25 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 04 Nov 17:10 buy, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy
- *within 5, last 12 candles under 6 pips:*
  - Mon 26 Oct 09:05 bounce buy: **used at S2 13338.6**, slow: opened and closed 3 trade(s), -1.9 on the part closed (slow grind sell 26 Oct 08:25 +3.5; EMA pullback sell 26 Oct 08:35 -2.7; EMA pullback sell 26 Oct 08:35 -2.7); the bounce itself made -7.9
  - Mon 26 Oct 14:10 bounce buy: **used at S3 13328.6**, slow: opened and closed 3 trade(s), -10.6 on the part closed (EMA pullback sell 26 Oct 13:55 -4.8; EMA pullback sell 26 Oct 13:55 -4.8; level reversal sell 26 Oct 13:55 -1.0); the bounce itself made +7.2
  - Tue 27 Oct 16:40 bounce buy: **used at 00 13300**, slow: opened and closed 3 trade(s), +9.3 on the part closed (breakout sell 27 Oct 07:00 +15.2; slow grind sell 27 Oct 16:05 -0.6; EMA pullback sell 27 Oct 16:15 -5.3); the bounce itself made +5.8
  - Tue 27 Oct 21:15 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 06:30 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 09:35 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 21:05 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Fri 30 Oct 01:45 bounce sell: valid at 00 13400, slow, but the order sender did not open it
  - Wed 04 Nov 10:40 bounce sell: **used at 00 13500**, slow: opened and closed 1 trade(s), -6.7 on the part closed (slow grind buy 04 Nov 08:30 -6.7); the bounce itself made -7.5
  - Wed 04 Nov 15:40 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -7.5 on the part closed (slow grind sell 04 Nov 15:35 -7.5); the bounce itself made -12.0
  - Wed 04 Nov 17:20 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -9.2 on the part closed (slow grind sell 04 Nov 16:10 -9.2); the bounce itself made -5.2
  - Fri 06 Nov 07:50 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Fri 06 Nov 08:05 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Fri 06 Nov 08:15 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Refused, not at a significant level (61): 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 27 Oct 09:55 buy, 27 Oct 10:05 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 20:50 sell, 29 Oct 20:55 sell, 29 Oct 21:00 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 29 Oct 23:40 sell, 29 Oct 23:45 sell, 30 Oct 01:30 sell, 30 Oct 01:35 sell, 30 Oct 01:40 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 30 Oct 16:25 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 04 Nov 17:10 buy, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy
- *within 5, last 3 h under 8 pips/h:*
  - Mon 26 Oct 09:05 bounce buy: **used at S2 13338.6**, slow: opened and closed 3 trade(s), -1.9 on the part closed (slow grind sell 26 Oct 08:25 +3.5; EMA pullback sell 26 Oct 08:35 -2.7; EMA pullback sell 26 Oct 08:35 -2.7); the bounce itself made -7.9
  - Mon 26 Oct 14:10 bounce buy: **used at S3 13328.6**, slow: opened and closed 3 trade(s), -10.6 on the part closed (EMA pullback sell 26 Oct 13:55 -4.8; EMA pullback sell 26 Oct 13:55 -4.8; level reversal sell 26 Oct 13:55 -1.0); the bounce itself made +7.2
  - Tue 27 Oct 16:40 bounce buy: **used at 00 13300**, slow: opened and closed 3 trade(s), +9.3 on the part closed (breakout sell 27 Oct 07:00 +15.2; slow grind sell 27 Oct 16:05 -0.6; EMA pullback sell 27 Oct 16:15 -5.3); the bounce itself made +5.8
  - Tue 27 Oct 21:15 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 06:30 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 09:35 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 21:05 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Fri 30 Oct 01:45 bounce sell: valid at 00 13400, slow, but the order sender did not open it
  - Wed 04 Nov 10:40 bounce sell: **used at 00 13500**, slow: opened and closed 1 trade(s), -6.7 on the part closed (slow grind buy 04 Nov 08:30 -6.7); the bounce itself made -7.5
  - Wed 04 Nov 15:40 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -7.5 on the part closed (slow grind sell 04 Nov 15:35 -7.5); the bounce itself made -12.0
  - Wed 04 Nov 17:20 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -9.2 on the part closed (slow grind sell 04 Nov 16:10 -9.2); the bounce itself made -5.2
  - Fri 06 Nov 07:50 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Fri 06 Nov 08:05 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Fri 06 Nov 08:15 bounce buy: valid at S2 13399.1, slow, but the order sender did not open it
  - Refused, not at a significant level (61): 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 27 Oct 09:55 buy, 27 Oct 10:05 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 20:50 sell, 29 Oct 20:55 sell, 29 Oct 21:00 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 29 Oct 23:40 sell, 29 Oct 23:45 sell, 30 Oct 01:30 sell, 30 Oct 01:35 sell, 30 Oct 01:40 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 30 Oct 16:25 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 04 Nov 17:10 buy, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy

**G: +1,328.2 in 157 trades** — within 5, last 6 candles under 4 pips; within 5, last 12 candles under 4 pips; within 8, last 6 candles under 4 pips; within 8, last 12 candles under 4 pips

- *within 5, last 6 candles under 4 pips:*
  - Mon 26 Oct 09:05 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 14:10 bounce buy: **refused, moving fast**, at S3 13328.6: trend trades held
  - Mon 26 Oct 14:15 bounce buy: **refused, moving fast**, at S3 13328.6: trend trades held
  - Mon 26 Oct 14:20 bounce buy: **refused, moving fast**, at S3 13328.6: trend trades held
  - Mon 26 Oct 14:45 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:15 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:20 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:40 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Tue 27 Oct 16:40 bounce buy: **used at 00 13300**, slow: opened and closed 3 trade(s), +9.3 on the part closed (breakout sell 27 Oct 07:00 +15.2; slow grind sell 27 Oct 16:05 -0.6; EMA pullback sell 27 Oct 16:15 -5.3); the bounce itself made +5.8
  - Tue 27 Oct 21:15 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 06:30 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 09:35 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
  - Thu 29 Oct 21:05 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Fri 30 Oct 01:45 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Wed 04 Nov 10:40 bounce sell: **refused, moving fast**, at 00 13500: trend trades held
  - Wed 04 Nov 11:00 bounce sell: **refused, moving fast**, at 00 13500: trend trades held
  - Wed 04 Nov 15:40 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Wed 04 Nov 16:00 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Wed 04 Nov 17:20 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Fri 06 Nov 07:50 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Fri 06 Nov 08:05 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Fri 06 Nov 08:15 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Refused, not at a significant level (62): 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 27 Oct 09:55 buy, 27 Oct 10:05 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 20:50 sell, 29 Oct 20:55 sell, 29 Oct 21:00 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 29 Oct 23:40 sell, 29 Oct 23:45 sell, 30 Oct 01:30 sell, 30 Oct 01:35 sell, 30 Oct 01:40 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 30 Oct 16:25 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 04 Nov 16:05 buy, 04 Nov 17:10 buy, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy
- *within 5, last 12 candles under 4 pips:*
  - Mon 26 Oct 09:05 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 14:10 bounce buy: **refused, moving fast**, at S3 13328.6: trend trades held
  - Mon 26 Oct 14:15 bounce buy: **refused, moving fast**, at S3 13328.6: trend trades held
  - Mon 26 Oct 14:20 bounce buy: **refused, moving fast**, at S3 13328.6: trend trades held
  - Mon 26 Oct 14:45 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:15 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:20 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:40 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Tue 27 Oct 16:40 bounce buy: **used at 00 13300**, slow: opened and closed 3 trade(s), +9.3 on the part closed (breakout sell 27 Oct 07:00 +15.2; slow grind sell 27 Oct 16:05 -0.6; EMA pullback sell 27 Oct 16:15 -5.3); the bounce itself made +5.8
  - Tue 27 Oct 21:15 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 06:30 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 09:35 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
  - Thu 29 Oct 21:05 bounce sell: **refused, moving fast**, at R2 13377.1: trend trades held
  - Fri 30 Oct 01:45 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Wed 04 Nov 10:40 bounce sell: **refused, moving fast**, at 00 13500: trend trades held
  - Wed 04 Nov 11:00 bounce sell: **refused, moving fast**, at 00 13500: trend trades held
  - Wed 04 Nov 15:40 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Wed 04 Nov 16:00 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Wed 04 Nov 17:20 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Fri 06 Nov 07:50 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Fri 06 Nov 08:05 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Fri 06 Nov 08:15 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Refused, not at a significant level (62): 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 27 Oct 09:55 buy, 27 Oct 10:05 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 20:50 sell, 29 Oct 20:55 sell, 29 Oct 21:00 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 29 Oct 23:40 sell, 29 Oct 23:45 sell, 30 Oct 01:30 sell, 30 Oct 01:35 sell, 30 Oct 01:40 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 30 Oct 16:25 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 04 Nov 16:05 buy, 04 Nov 17:10 buy, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy
- *within 8, last 6 candles under 4 pips:*
  - Mon 26 Oct 09:05 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 14:10 bounce buy: **refused, moving fast**, at S3 13328.6: trend trades held
  - Mon 26 Oct 14:15 bounce buy: **refused, moving fast**, at S3 13328.6: trend trades held
  - Mon 26 Oct 14:20 bounce buy: **refused, moving fast**, at S3 13328.6: trend trades held
  - Mon 26 Oct 14:45 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:15 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:20 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:40 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Tue 27 Oct 09:55 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
  - Tue 27 Oct 16:40 bounce buy: **used at 00 13300**, slow: opened and closed 3 trade(s), +9.3 on the part closed (breakout sell 27 Oct 07:00 +15.2; slow grind sell 27 Oct 16:05 -0.6; EMA pullback sell 27 Oct 16:15 -5.3); the bounce itself made +5.8
  - Tue 27 Oct 21:15 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 06:30 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 09:35 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
  - Thu 29 Oct 20:50 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Thu 29 Oct 20:55 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Thu 29 Oct 21:00 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Thu 29 Oct 21:05 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Thu 29 Oct 23:40 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Thu 29 Oct 23:45 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Fri 30 Oct 01:30 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Fri 30 Oct 01:35 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Fri 30 Oct 01:40 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Fri 30 Oct 01:45 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Fri 30 Oct 16:25 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Wed 04 Nov 10:40 bounce sell: **refused, moving fast**, at 00 13500: trend trades held
  - Wed 04 Nov 11:00 bounce sell: **refused, moving fast**, at 00 13500: trend trades held
  - Wed 04 Nov 15:40 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Wed 04 Nov 16:00 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Wed 04 Nov 16:05 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Wed 04 Nov 17:10 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Wed 04 Nov 17:20 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Fri 06 Nov 07:50 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Fri 06 Nov 08:05 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Fri 06 Nov 08:15 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Refused, not at a significant level (50): 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 27 Oct 10:05 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy
- *within 8, last 12 candles under 4 pips:*
  - Mon 26 Oct 09:05 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 14:10 bounce buy: **refused, moving fast**, at S3 13328.6: trend trades held
  - Mon 26 Oct 14:15 bounce buy: **refused, moving fast**, at S3 13328.6: trend trades held
  - Mon 26 Oct 14:20 bounce buy: **refused, moving fast**, at S3 13328.6: trend trades held
  - Mon 26 Oct 14:45 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:15 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:20 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Mon 26 Oct 15:40 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
  - Tue 27 Oct 09:55 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
  - Tue 27 Oct 16:40 bounce buy: **used at 00 13300**, slow: opened and closed 3 trade(s), +9.3 on the part closed (breakout sell 27 Oct 07:00 +15.2; slow grind sell 27 Oct 16:05 -0.6; EMA pullback sell 27 Oct 16:15 -5.3); the bounce itself made +5.8
  - Tue 27 Oct 21:15 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 06:30 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 09:35 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
  - Thu 29 Oct 20:50 bounce sell: **refused, moving fast**, at R2 13377.1: trend trades held
  - Thu 29 Oct 20:55 bounce sell: **refused, moving fast**, at R2 13377.1: trend trades held
  - Thu 29 Oct 21:00 bounce sell: **refused, moving fast**, at R2 13377.1: trend trades held
  - Thu 29 Oct 21:05 bounce sell: **refused, moving fast**, at R2 13377.1: trend trades held
  - Thu 29 Oct 23:40 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Thu 29 Oct 23:45 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Fri 30 Oct 01:30 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Fri 30 Oct 01:35 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Fri 30 Oct 01:40 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Fri 30 Oct 01:45 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Fri 30 Oct 16:25 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Wed 04 Nov 10:40 bounce sell: **refused, moving fast**, at 00 13500: trend trades held
  - Wed 04 Nov 11:00 bounce sell: **refused, moving fast**, at 00 13500: trend trades held
  - Wed 04 Nov 15:40 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Wed 04 Nov 16:00 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Wed 04 Nov 16:05 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Wed 04 Nov 17:10 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Wed 04 Nov 17:20 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
  - Fri 06 Nov 07:50 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Fri 06 Nov 08:05 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Fri 06 Nov 08:15 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Refused, not at a significant level (50): 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 27 Oct 10:05 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy

**H: +1,291.3 in 163 trades** — within 5, last 6 candles under 6 pips

- Mon 26 Oct 09:05 bounce buy: **used at S2 13338.6**, slow: opened and closed 3 trade(s), -1.9 on the part closed (slow grind sell 26 Oct 08:25 +3.5; EMA pullback sell 26 Oct 08:35 -2.7; EMA pullback sell 26 Oct 08:35 -2.7); the bounce itself made -7.9
- Mon 26 Oct 14:10 bounce buy: **used at S3 13328.6**, slow: opened and closed 3 trade(s), -10.6 on the part closed (EMA pullback sell 26 Oct 13:55 -4.8; EMA pullback sell 26 Oct 13:55 -4.8; level reversal sell 26 Oct 13:55 -1.0); the bounce itself made +7.2
- Tue 27 Oct 16:40 bounce buy: **used at 00 13300**, slow: opened and closed 3 trade(s), +9.3 on the part closed (breakout sell 27 Oct 07:00 +15.2; slow grind sell 27 Oct 16:05 -0.6; EMA pullback sell 27 Oct 16:15 -5.3); the bounce itself made +5.8
- Tue 27 Oct 21:15 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 06:30 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 09:35 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 21:05 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Fri 30 Oct 01:45 bounce sell: valid at 00 13400, slow, but the order sender did not open it
- Wed 04 Nov 10:40 bounce sell: **refused, moving fast**, at 00 13500: trend trades held
- Wed 04 Nov 11:00 bounce sell: **used at 00 13500**, slow: opened and closed 1 trade(s), -10.3 on the part closed (slow grind buy 04 Nov 08:30 -10.3); the bounce itself made -7.4
- Wed 04 Nov 15:40 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -7.5 on the part closed (slow grind sell 04 Nov 15:35 -7.5); the bounce itself made -12.0
- Wed 04 Nov 17:20 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -9.2 on the part closed (slow grind sell 04 Nov 16:10 -9.2); the bounce itself made -5.2
- Fri 06 Nov 07:50 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Fri 06 Nov 08:05 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Fri 06 Nov 08:15 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Refused, not at a significant level (61): 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 27 Oct 09:55 buy, 27 Oct 10:05 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 20:50 sell, 29 Oct 20:55 sell, 29 Oct 21:00 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 29 Oct 23:40 sell, 29 Oct 23:45 sell, 30 Oct 01:30 sell, 30 Oct 01:35 sell, 30 Oct 01:40 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 30 Oct 16:25 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 04 Nov 17:10 buy, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy

**I: +1,379.5 in 158 trades** — within 5, last 2 h under 5 pips/h

- Mon 26 Oct 09:05 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
- Mon 26 Oct 14:10 bounce buy: **used at S3 13328.6**, slow: opened and closed 5 trade(s), +13.4 on the part closed (EMA pullback sell 26 Oct 08:35 +12.0; EMA pullback sell 26 Oct 08:35 +12.0; EMA pullback sell 26 Oct 13:55 -4.8; EMA pullback sell 26 Oct 13:55 -4.8; level reversal sell 26 Oct 13:55 -1.0); the bounce itself made +7.2
- Tue 27 Oct 16:40 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
- Tue 27 Oct 21:15 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
- Thu 29 Oct 06:30 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 09:35 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
- Thu 29 Oct 21:05 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Fri 30 Oct 01:45 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
- Wed 04 Nov 10:40 bounce sell: **used at 00 13500**, slow: opened and closed 1 trade(s), -6.7 on the part closed (slow grind buy 04 Nov 08:30 -6.7); the bounce itself made -7.5
- Wed 04 Nov 15:40 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
- Wed 04 Nov 16:00 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
- Wed 04 Nov 17:20 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -10.7 on the part closed (slow grind sell 04 Nov 15:35 -10.7); the bounce itself made -5.2
- Fri 06 Nov 07:50 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Fri 06 Nov 08:05 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Fri 06 Nov 08:15 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Refused, not at a significant level (66): 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 27 Oct 09:55 buy, 27 Oct 10:05 buy, 27 Oct 16:45 buy, 27 Oct 16:55 buy, 27 Oct 17:00 buy, 27 Oct 17:10 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 20:50 sell, 29 Oct 20:55 sell, 29 Oct 21:00 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 29 Oct 23:40 sell, 29 Oct 23:45 sell, 30 Oct 01:30 sell, 30 Oct 01:35 sell, 30 Oct 01:40 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 30 Oct 16:25 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 04 Nov 16:05 buy, 04 Nov 17:10 buy, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy

**J: +1,336.0 in 161 trades** — within 5, last 2 h under 8 pips/h

- Mon 26 Oct 09:05 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
- Mon 26 Oct 14:10 bounce buy: **used at S3 13328.6**, slow: opened and closed 5 trade(s), +13.4 on the part closed (EMA pullback sell 26 Oct 08:35 +12.0; EMA pullback sell 26 Oct 08:35 +12.0; EMA pullback sell 26 Oct 13:55 -4.8; EMA pullback sell 26 Oct 13:55 -4.8; level reversal sell 26 Oct 13:55 -1.0); the bounce itself made +7.2
- Tue 27 Oct 16:40 bounce buy: **used at 00 13300**, slow: opened and closed 3 trade(s), +9.3 on the part closed (breakout sell 27 Oct 07:00 +15.2; slow grind sell 27 Oct 16:05 -0.6; EMA pullback sell 27 Oct 16:15 -5.3); the bounce itself made +5.8
- Tue 27 Oct 21:15 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
- Thu 29 Oct 06:30 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 09:35 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 21:05 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Fri 30 Oct 01:45 bounce sell: valid at 00 13400, slow, but the order sender did not open it
- Wed 04 Nov 10:40 bounce sell: **used at 00 13500**, slow: opened and closed 1 trade(s), -6.7 on the part closed (slow grind buy 04 Nov 08:30 -6.7); the bounce itself made -7.5
- Wed 04 Nov 15:40 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
- Wed 04 Nov 16:00 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -10.0 on the part closed (slow grind sell 04 Nov 15:35 -10.0); the bounce itself made -12.0
- Wed 04 Nov 17:20 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -9.2 on the part closed (slow grind sell 04 Nov 16:10 -9.2); the bounce itself made -5.2
- Fri 06 Nov 07:50 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Fri 06 Nov 08:05 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Fri 06 Nov 08:15 bounce buy: valid at S2 13399.1, slow, but the order sender did not open it
- Refused, not at a significant level (61): 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 27 Oct 09:55 buy, 27 Oct 10:05 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 20:50 sell, 29 Oct 20:55 sell, 29 Oct 21:00 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 29 Oct 23:40 sell, 29 Oct 23:45 sell, 30 Oct 01:30 sell, 30 Oct 01:35 sell, 30 Oct 01:40 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 30 Oct 16:25 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 04 Nov 17:10 buy, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy

**K: +1,292.2 in 163 trades** — within 5, last 2 h under 12 pips/h

- Mon 26 Oct 09:05 bounce buy: **used at S2 13338.6**, slow: opened and closed 3 trade(s), -1.9 on the part closed (slow grind sell 26 Oct 08:25 +3.5; EMA pullback sell 26 Oct 08:35 -2.7; EMA pullback sell 26 Oct 08:35 -2.7); the bounce itself made -7.9
- Mon 26 Oct 14:10 bounce buy: **used at S3 13328.6**, slow: opened and closed 3 trade(s), -10.6 on the part closed (EMA pullback sell 26 Oct 13:55 -4.8; EMA pullback sell 26 Oct 13:55 -4.8; level reversal sell 26 Oct 13:55 -1.0); the bounce itself made +7.2
- Tue 27 Oct 16:40 bounce buy: **used at 00 13300**, slow: opened and closed 3 trade(s), +9.3 on the part closed (breakout sell 27 Oct 07:00 +15.2; slow grind sell 27 Oct 16:05 -0.6; EMA pullback sell 27 Oct 16:15 -5.3); the bounce itself made +5.8
- Tue 27 Oct 21:15 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 06:30 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 09:35 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 21:05 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Fri 30 Oct 01:45 bounce sell: valid at 00 13400, slow, but the order sender did not open it
- Wed 04 Nov 10:40 bounce sell: **used at 00 13500**, slow: opened and closed 1 trade(s), -6.7 on the part closed (slow grind buy 04 Nov 08:30 -6.7); the bounce itself made -7.5
- Wed 04 Nov 15:40 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
- Wed 04 Nov 16:00 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -10.0 on the part closed (slow grind sell 04 Nov 15:35 -10.0); the bounce itself made -12.0
- Wed 04 Nov 17:20 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -9.2 on the part closed (slow grind sell 04 Nov 16:10 -9.2); the bounce itself made -5.2
- Fri 06 Nov 07:50 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Fri 06 Nov 08:05 bounce buy: valid at S2 13399.1, slow, but the order sender did not open it
- Fri 06 Nov 08:15 bounce buy: valid at S2 13399.1, slow, but the order sender did not open it
- Refused, not at a significant level (61): 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 27 Oct 09:55 buy, 27 Oct 10:05 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 20:50 sell, 29 Oct 20:55 sell, 29 Oct 21:00 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 29 Oct 23:40 sell, 29 Oct 23:45 sell, 30 Oct 01:30 sell, 30 Oct 01:35 sell, 30 Oct 01:40 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 30 Oct 16:25 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 04 Nov 17:10 buy, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy

**L: +1,350.8 in 159 trades** — within 5, last 3 h under 5 pips/h

- Mon 26 Oct 09:05 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
- Mon 26 Oct 14:10 bounce buy: **used at S3 13328.6**, slow: opened and closed 5 trade(s), +13.4 on the part closed (EMA pullback sell 26 Oct 08:35 +12.0; EMA pullback sell 26 Oct 08:35 +12.0; EMA pullback sell 26 Oct 13:55 -4.8; EMA pullback sell 26 Oct 13:55 -4.8; level reversal sell 26 Oct 13:55 -1.0); the bounce itself made +7.2
- Tue 27 Oct 16:40 bounce buy: **used at 00 13300**, slow: opened and closed 3 trade(s), +9.3 on the part closed (breakout sell 27 Oct 07:00 +15.2; slow grind sell 27 Oct 16:05 -0.6; EMA pullback sell 27 Oct 16:15 -5.3); the bounce itself made +5.8
- Tue 27 Oct 21:15 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 06:30 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 09:35 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 21:05 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Fri 30 Oct 01:45 bounce sell: valid at 00 13400, slow, but the order sender did not open it
- Wed 04 Nov 10:40 bounce sell: **used at 00 13500**, slow: opened and closed 1 trade(s), -6.7 on the part closed (slow grind buy 04 Nov 08:30 -6.7); the bounce itself made -7.5
- Wed 04 Nov 15:40 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
- Wed 04 Nov 16:00 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
- Wed 04 Nov 17:20 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
- Fri 06 Nov 07:50 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Fri 06 Nov 08:05 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Fri 06 Nov 08:15 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Refused, not at a significant level (62): 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 27 Oct 09:55 buy, 27 Oct 10:05 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 20:50 sell, 29 Oct 20:55 sell, 29 Oct 21:00 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 29 Oct 23:40 sell, 29 Oct 23:45 sell, 30 Oct 01:30 sell, 30 Oct 01:35 sell, 30 Oct 01:40 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 30 Oct 16:25 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 04 Nov 16:05 buy, 04 Nov 17:10 buy, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy

**M: +1,305.0 in 165 trades** — within 8, trend type (slow grind); within 8, last 3 h under 8 pips/h; within 8, last 3 h under 12 pips/h

- *within 8, trend type (slow grind):*
  - Mon 26 Oct 09:05 bounce buy: **used at S2 13338.6**, slow: opened and closed 3 trade(s), -1.9 on the part closed (slow grind sell 26 Oct 08:25 +3.5; EMA pullback sell 26 Oct 08:35 -2.7; EMA pullback sell 26 Oct 08:35 -2.7); the bounce itself made -7.9
  - Mon 26 Oct 14:10 bounce buy: **used at S3 13328.6**, slow: opened and closed 3 trade(s), -10.6 on the part closed (EMA pullback sell 26 Oct 13:55 -4.8; EMA pullback sell 26 Oct 13:55 -4.8; level reversal sell 26 Oct 13:55 -1.0); the bounce itself made +7.2
  - Tue 27 Oct 09:55 bounce buy: **used at 00 13300**, slow: opened and closed 1 trade(s), +8.8 on the part closed (breakout sell 27 Oct 07:00 +8.8); the bounce itself made -4.6
  - Tue 27 Oct 16:40 bounce buy: **used at 00 13300**, slow: opened and closed 2 trade(s), -5.9 on the part closed (slow grind sell 27 Oct 16:05 -0.6; EMA pullback sell 27 Oct 16:15 -5.3); the bounce itself made +5.8
  - Tue 27 Oct 21:15 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 06:30 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 09:35 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 20:50 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Thu 29 Oct 20:55 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Thu 29 Oct 21:00 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Thu 29 Oct 21:05 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Thu 29 Oct 23:40 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Thu 29 Oct 23:45 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Fri 30 Oct 01:30 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
  - Fri 30 Oct 01:35 bounce sell: valid at 00 13400, slow, but the order sender did not open it
  - Fri 30 Oct 01:40 bounce sell: valid at 00 13400, slow, but the order sender did not open it
  - Fri 30 Oct 01:45 bounce sell: valid at 00 13400, slow, but the order sender did not open it
  - Fri 30 Oct 16:25 bounce sell: **used at 00 13400**, slow: opened and closed 1 trade(s), +12.6 on the part closed (EMA pullback buy 29 Oct 22:05 +12.6); the bounce itself made +6.4
  - Wed 04 Nov 10:40 bounce sell: **used at 00 13500**, slow: opened and closed 1 trade(s), -6.7 on the part closed (slow grind buy 04 Nov 08:30 -6.7); the bounce itself made -7.5
  - Wed 04 Nov 15:40 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -7.5 on the part closed (slow grind sell 04 Nov 15:35 -7.5); the bounce itself made -12.0
  - Wed 04 Nov 17:10 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -5.5 on the part closed (slow grind sell 04 Nov 16:10 -5.5); the bounce itself made +4.2
  - Fri 06 Nov 07:50 bounce buy: valid at S2 13399.1, slow, but the order sender did not open it
  - Fri 06 Nov 08:05 bounce buy: valid at S2 13399.1, slow, but the order sender did not open it
  - Fri 06 Nov 08:15 bounce buy: valid at S2 13399.1, slow, but the order sender did not open it
  - Refused, not at a significant level (49): 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy
- *within 8, last 3 h under 8 pips/h:*
  - Mon 26 Oct 09:05 bounce buy: **used at S2 13338.6**, slow: opened and closed 3 trade(s), -1.9 on the part closed (slow grind sell 26 Oct 08:25 +3.5; EMA pullback sell 26 Oct 08:35 -2.7; EMA pullback sell 26 Oct 08:35 -2.7); the bounce itself made -7.9
  - Mon 26 Oct 14:10 bounce buy: **used at S3 13328.6**, slow: opened and closed 3 trade(s), -10.6 on the part closed (EMA pullback sell 26 Oct 13:55 -4.8; EMA pullback sell 26 Oct 13:55 -4.8; level reversal sell 26 Oct 13:55 -1.0); the bounce itself made +7.2
  - Tue 27 Oct 09:55 bounce buy: **used at 00 13300**, slow: opened and closed 1 trade(s), +8.8 on the part closed (breakout sell 27 Oct 07:00 +8.8); the bounce itself made -4.6
  - Tue 27 Oct 16:40 bounce buy: **used at 00 13300**, slow: opened and closed 2 trade(s), -5.9 on the part closed (slow grind sell 27 Oct 16:05 -0.6; EMA pullback sell 27 Oct 16:15 -5.3); the bounce itself made +5.8
  - Tue 27 Oct 21:15 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 06:30 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 09:35 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 20:50 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Thu 29 Oct 20:55 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Thu 29 Oct 21:00 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Thu 29 Oct 21:05 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Thu 29 Oct 23:40 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Thu 29 Oct 23:45 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Fri 30 Oct 01:30 bounce sell: valid at 00 13400, slow, but the order sender did not open it
  - Fri 30 Oct 01:35 bounce sell: valid at 00 13400, slow, but the order sender did not open it
  - Fri 30 Oct 01:40 bounce sell: valid at 00 13400, slow, but the order sender did not open it
  - Fri 30 Oct 01:45 bounce sell: valid at 00 13400, slow, but the order sender did not open it
  - Fri 30 Oct 16:25 bounce sell: **used at 00 13400**, slow: opened and closed 1 trade(s), +12.6 on the part closed (EMA pullback buy 29 Oct 22:05 +12.6); the bounce itself made +6.4
  - Wed 04 Nov 10:40 bounce sell: **used at 00 13500**, slow: opened and closed 1 trade(s), -6.7 on the part closed (slow grind buy 04 Nov 08:30 -6.7); the bounce itself made -7.5
  - Wed 04 Nov 15:40 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -7.5 on the part closed (slow grind sell 04 Nov 15:35 -7.5); the bounce itself made -12.0
  - Wed 04 Nov 17:10 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -5.5 on the part closed (slow grind sell 04 Nov 16:10 -5.5); the bounce itself made +4.2
  - Fri 06 Nov 07:50 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Fri 06 Nov 08:05 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
  - Fri 06 Nov 08:15 bounce buy: valid at S2 13399.1, slow, but the order sender did not open it
  - Refused, not at a significant level (49): 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy
- *within 8, last 3 h under 12 pips/h:*
  - Mon 26 Oct 09:05 bounce buy: **used at S2 13338.6**, slow: opened and closed 3 trade(s), -1.9 on the part closed (slow grind sell 26 Oct 08:25 +3.5; EMA pullback sell 26 Oct 08:35 -2.7; EMA pullback sell 26 Oct 08:35 -2.7); the bounce itself made -7.9
  - Mon 26 Oct 14:10 bounce buy: **used at S3 13328.6**, slow: opened and closed 3 trade(s), -10.6 on the part closed (EMA pullback sell 26 Oct 13:55 -4.8; EMA pullback sell 26 Oct 13:55 -4.8; level reversal sell 26 Oct 13:55 -1.0); the bounce itself made +7.2
  - Tue 27 Oct 09:55 bounce buy: **used at 00 13300**, slow: opened and closed 1 trade(s), +8.8 on the part closed (breakout sell 27 Oct 07:00 +8.8); the bounce itself made -4.6
  - Tue 27 Oct 16:40 bounce buy: **used at 00 13300**, slow: opened and closed 2 trade(s), -5.9 on the part closed (slow grind sell 27 Oct 16:05 -0.6; EMA pullback sell 27 Oct 16:15 -5.3); the bounce itself made +5.8
  - Tue 27 Oct 21:15 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 06:30 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 09:35 bounce buy: valid at 00 13300, slow, but the order sender did not open it
  - Thu 29 Oct 20:50 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Thu 29 Oct 20:55 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Thu 29 Oct 21:00 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Thu 29 Oct 21:05 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Thu 29 Oct 23:40 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Thu 29 Oct 23:45 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
  - Fri 30 Oct 01:30 bounce sell: valid at 00 13400, slow, but the order sender did not open it
  - Fri 30 Oct 01:35 bounce sell: valid at 00 13400, slow, but the order sender did not open it
  - Fri 30 Oct 01:40 bounce sell: valid at 00 13400, slow, but the order sender did not open it
  - Fri 30 Oct 01:45 bounce sell: valid at 00 13400, slow, but the order sender did not open it
  - Fri 30 Oct 16:25 bounce sell: **used at 00 13400**, slow: opened and closed 1 trade(s), +12.6 on the part closed (EMA pullback buy 29 Oct 22:05 +12.6); the bounce itself made +6.4
  - Wed 04 Nov 10:40 bounce sell: **used at 00 13500**, slow: opened and closed 1 trade(s), -6.7 on the part closed (slow grind buy 04 Nov 08:30 -6.7); the bounce itself made -7.5
  - Wed 04 Nov 15:40 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -7.5 on the part closed (slow grind sell 04 Nov 15:35 -7.5); the bounce itself made -12.0
  - Wed 04 Nov 17:10 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -5.5 on the part closed (slow grind sell 04 Nov 16:10 -5.5); the bounce itself made +4.2
  - Fri 06 Nov 07:50 bounce buy: valid at S2 13399.1, slow, but the order sender did not open it
  - Fri 06 Nov 08:05 bounce buy: valid at S2 13399.1, slow, but the order sender did not open it
  - Fri 06 Nov 08:15 bounce buy: valid at S2 13399.1, slow, but the order sender did not open it
  - Refused, not at a significant level (49): 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy

**N: +1,288.4 in 165 trades** — within 8, last 6 candles under 6 pips

- Mon 26 Oct 09:05 bounce buy: **used at S2 13338.6**, slow: opened and closed 3 trade(s), -1.9 on the part closed (slow grind sell 26 Oct 08:25 +3.5; EMA pullback sell 26 Oct 08:35 -2.7; EMA pullback sell 26 Oct 08:35 -2.7); the bounce itself made -7.9
- Mon 26 Oct 14:10 bounce buy: **used at S3 13328.6**, slow: opened and closed 3 trade(s), -10.6 on the part closed (EMA pullback sell 26 Oct 13:55 -4.8; EMA pullback sell 26 Oct 13:55 -4.8; level reversal sell 26 Oct 13:55 -1.0); the bounce itself made +7.2
- Tue 27 Oct 09:55 bounce buy: **used at 00 13300**, slow: opened and closed 1 trade(s), +8.8 on the part closed (breakout sell 27 Oct 07:00 +8.8); the bounce itself made -4.6
- Tue 27 Oct 16:40 bounce buy: **used at 00 13300**, slow: opened and closed 2 trade(s), -5.9 on the part closed (slow grind sell 27 Oct 16:05 -0.6; EMA pullback sell 27 Oct 16:15 -5.3); the bounce itself made +5.8
- Tue 27 Oct 21:15 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 06:30 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 09:35 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 20:50 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Thu 29 Oct 20:55 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Thu 29 Oct 21:00 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Thu 29 Oct 21:05 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Thu 29 Oct 23:40 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Thu 29 Oct 23:45 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Fri 30 Oct 01:30 bounce sell: valid at 00 13400, slow, but the order sender did not open it
- Fri 30 Oct 01:35 bounce sell: valid at 00 13400, slow, but the order sender did not open it
- Fri 30 Oct 01:40 bounce sell: valid at 00 13400, slow, but the order sender did not open it
- Fri 30 Oct 01:45 bounce sell: valid at 00 13400, slow, but the order sender did not open it
- Fri 30 Oct 16:25 bounce sell: **used at 00 13400**, slow: opened and closed 1 trade(s), +12.6 on the part closed (EMA pullback buy 29 Oct 22:05 +12.6); the bounce itself made +6.4
- Wed 04 Nov 10:40 bounce sell: **refused, moving fast**, at 00 13500: trend trades held
- Wed 04 Nov 11:00 bounce sell: **used at 00 13500**, slow: opened and closed 1 trade(s), -10.3 on the part closed (slow grind buy 04 Nov 08:30 -10.3); the bounce itself made -7.4
- Wed 04 Nov 15:40 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -7.5 on the part closed (slow grind sell 04 Nov 15:35 -7.5); the bounce itself made -12.0
- Wed 04 Nov 17:10 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
- Wed 04 Nov 17:20 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -9.2 on the part closed (slow grind sell 04 Nov 16:10 -9.2); the bounce itself made -5.2
- Fri 06 Nov 07:50 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Fri 06 Nov 08:05 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Fri 06 Nov 08:15 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Refused, not at a significant level (49): 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy

**O: +1,296.9 in 164 trades** — within 8, last 12 candles under 6 pips

- Mon 26 Oct 09:05 bounce buy: **used at S2 13338.6**, slow: opened and closed 3 trade(s), -1.9 on the part closed (slow grind sell 26 Oct 08:25 +3.5; EMA pullback sell 26 Oct 08:35 -2.7; EMA pullback sell 26 Oct 08:35 -2.7); the bounce itself made -7.9
- Mon 26 Oct 14:10 bounce buy: **used at S3 13328.6**, slow: opened and closed 3 trade(s), -10.6 on the part closed (EMA pullback sell 26 Oct 13:55 -4.8; EMA pullback sell 26 Oct 13:55 -4.8; level reversal sell 26 Oct 13:55 -1.0); the bounce itself made +7.2
- Tue 27 Oct 09:55 bounce buy: **used at 00 13300**, slow: opened and closed 1 trade(s), +8.8 on the part closed (breakout sell 27 Oct 07:00 +8.8); the bounce itself made -4.6
- Tue 27 Oct 16:40 bounce buy: **used at 00 13300**, slow: opened and closed 2 trade(s), -5.9 on the part closed (slow grind sell 27 Oct 16:05 -0.6; EMA pullback sell 27 Oct 16:15 -5.3); the bounce itself made +5.8
- Tue 27 Oct 21:15 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 06:30 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 09:35 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 20:50 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Thu 29 Oct 20:55 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Thu 29 Oct 21:00 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Thu 29 Oct 21:05 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Thu 29 Oct 23:40 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Thu 29 Oct 23:45 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Fri 30 Oct 01:30 bounce sell: valid at 00 13400, slow, but the order sender did not open it
- Fri 30 Oct 01:35 bounce sell: valid at 00 13400, slow, but the order sender did not open it
- Fri 30 Oct 01:40 bounce sell: valid at 00 13400, slow, but the order sender did not open it
- Fri 30 Oct 01:45 bounce sell: valid at 00 13400, slow, but the order sender did not open it
- Fri 30 Oct 16:25 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
- Wed 04 Nov 10:40 bounce sell: **used at 00 13500**, slow: opened and closed 1 trade(s), -6.7 on the part closed (slow grind buy 04 Nov 08:30 -6.7); the bounce itself made -7.5
- Wed 04 Nov 15:40 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -7.5 on the part closed (slow grind sell 04 Nov 15:35 -7.5); the bounce itself made -12.0
- Wed 04 Nov 17:10 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -5.5 on the part closed (slow grind sell 04 Nov 16:10 -5.5); the bounce itself made +4.2
- Fri 06 Nov 07:50 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Fri 06 Nov 08:05 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Fri 06 Nov 08:15 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Refused, not at a significant level (49): 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy

**P: +1,358.5 in 159 trades** — within 8, last 2 h under 5 pips/h

- Mon 26 Oct 09:05 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
- Mon 26 Oct 14:10 bounce buy: **used at S3 13328.6**, slow: opened and closed 5 trade(s), +13.4 on the part closed (EMA pullback sell 26 Oct 08:35 +12.0; EMA pullback sell 26 Oct 08:35 +12.0; EMA pullback sell 26 Oct 13:55 -4.8; EMA pullback sell 26 Oct 13:55 -4.8; level reversal sell 26 Oct 13:55 -1.0); the bounce itself made +7.2
- Tue 27 Oct 09:55 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
- Tue 27 Oct 16:40 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
- Tue 27 Oct 16:45 bounce buy: **used at 00 13300**, slow: opened and closed 3 trade(s), +0.9 on the part closed (breakout sell 27 Oct 07:00 +12.4; slow grind sell 27 Oct 16:05 -3.4; EMA pullback sell 27 Oct 16:15 -8.1); the bounce itself made +3.0
- Tue 27 Oct 21:15 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
- Thu 29 Oct 06:30 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 09:35 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
- Thu 29 Oct 20:50 bounce sell: **refused, moving fast**, at R2 13377.1: trend trades held
- Thu 29 Oct 20:55 bounce sell: **refused, moving fast**, at R2 13377.1: trend trades held
- Thu 29 Oct 21:00 bounce sell: **refused, moving fast**, at R2 13377.1: trend trades held
- Thu 29 Oct 21:05 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Thu 29 Oct 23:40 bounce sell: **refused, moving fast**, at R2 13377.1: trend trades held
- Thu 29 Oct 23:45 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Fri 30 Oct 01:30 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
- Fri 30 Oct 01:35 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
- Fri 30 Oct 01:40 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
- Fri 30 Oct 01:45 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
- Fri 30 Oct 16:25 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
- Wed 04 Nov 10:40 bounce sell: **used at 00 13500**, slow: opened and closed 1 trade(s), -6.7 on the part closed (slow grind buy 04 Nov 08:30 -6.7); the bounce itself made -7.5
- Wed 04 Nov 15:40 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
- Wed 04 Nov 16:00 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
- Wed 04 Nov 16:05 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
- Wed 04 Nov 17:10 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -7.0 on the part closed (slow grind sell 04 Nov 15:35 -7.0); the bounce itself made +4.2
- Fri 06 Nov 07:50 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Fri 06 Nov 08:05 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Fri 06 Nov 08:15 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Refused, not at a significant level (50): 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 27 Oct 10:05 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy

**Q: +1,346.3 in 163 trades** — within 8, last 2 h under 8 pips/h

- Mon 26 Oct 09:05 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
- Mon 26 Oct 14:10 bounce buy: **used at S3 13328.6**, slow: opened and closed 5 trade(s), +13.4 on the part closed (EMA pullback sell 26 Oct 08:35 +12.0; EMA pullback sell 26 Oct 08:35 +12.0; EMA pullback sell 26 Oct 13:55 -4.8; EMA pullback sell 26 Oct 13:55 -4.8; level reversal sell 26 Oct 13:55 -1.0); the bounce itself made +7.2
- Tue 27 Oct 09:55 bounce buy: **used at 00 13300**, slow: opened and closed 1 trade(s), +8.8 on the part closed (breakout sell 27 Oct 07:00 +8.8); the bounce itself made -4.6
- Tue 27 Oct 16:40 bounce buy: **used at 00 13300**, slow: opened and closed 2 trade(s), -5.9 on the part closed (slow grind sell 27 Oct 16:05 -0.6; EMA pullback sell 27 Oct 16:15 -5.3); the bounce itself made +5.8
- Tue 27 Oct 21:15 bounce buy: **refused, moving fast**, at 00 13300: trend trades held
- Thu 29 Oct 06:30 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 09:35 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 20:50 bounce sell: **refused, moving fast**, at R2 13377.1: trend trades held
- Thu 29 Oct 20:55 bounce sell: **refused, moving fast**, at R2 13377.1: trend trades held
- Thu 29 Oct 21:00 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Thu 29 Oct 21:05 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Thu 29 Oct 23:40 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Thu 29 Oct 23:45 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Fri 30 Oct 01:30 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
- Fri 30 Oct 01:35 bounce sell: valid at 00 13400, slow, but the order sender did not open it
- Fri 30 Oct 01:40 bounce sell: valid at 00 13400, slow, but the order sender did not open it
- Fri 30 Oct 01:45 bounce sell: valid at 00 13400, slow, but the order sender did not open it
- Fri 30 Oct 16:25 bounce sell: **used at 00 13400**, slow: opened and closed 1 trade(s), +12.6 on the part closed (EMA pullback buy 29 Oct 22:05 +12.6); the bounce itself made +6.4
- Wed 04 Nov 10:40 bounce sell: **used at 00 13500**, slow: opened and closed 1 trade(s), -6.7 on the part closed (slow grind buy 04 Nov 08:30 -6.7); the bounce itself made -7.5
- Wed 04 Nov 15:40 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
- Wed 04 Nov 16:00 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -10.0 on the part closed (slow grind sell 04 Nov 15:35 -10.0); the bounce itself made -12.0
- Wed 04 Nov 17:10 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -5.5 on the part closed (slow grind sell 04 Nov 16:10 -5.5); the bounce itself made +4.2
- Fri 06 Nov 07:50 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Fri 06 Nov 08:05 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Fri 06 Nov 08:15 bounce buy: valid at S2 13399.1, slow, but the order sender did not open it
- Refused, not at a significant level (49): 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy

**R: +1,302.5 in 165 trades** — within 8, last 2 h under 12 pips/h

- Mon 26 Oct 09:05 bounce buy: **used at S2 13338.6**, slow: opened and closed 3 trade(s), -1.9 on the part closed (slow grind sell 26 Oct 08:25 +3.5; EMA pullback sell 26 Oct 08:35 -2.7; EMA pullback sell 26 Oct 08:35 -2.7); the bounce itself made -7.9
- Mon 26 Oct 14:10 bounce buy: **used at S3 13328.6**, slow: opened and closed 3 trade(s), -10.6 on the part closed (EMA pullback sell 26 Oct 13:55 -4.8; EMA pullback sell 26 Oct 13:55 -4.8; level reversal sell 26 Oct 13:55 -1.0); the bounce itself made +7.2
- Tue 27 Oct 09:55 bounce buy: **used at 00 13300**, slow: opened and closed 1 trade(s), +8.8 on the part closed (breakout sell 27 Oct 07:00 +8.8); the bounce itself made -4.6
- Tue 27 Oct 16:40 bounce buy: **used at 00 13300**, slow: opened and closed 2 trade(s), -5.9 on the part closed (slow grind sell 27 Oct 16:05 -0.6; EMA pullback sell 27 Oct 16:15 -5.3); the bounce itself made +5.8
- Tue 27 Oct 21:15 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 06:30 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 09:35 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 20:50 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Thu 29 Oct 20:55 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Thu 29 Oct 21:00 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Thu 29 Oct 21:05 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Thu 29 Oct 23:40 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Thu 29 Oct 23:45 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Fri 30 Oct 01:30 bounce sell: valid at 00 13400, slow, but the order sender did not open it
- Fri 30 Oct 01:35 bounce sell: valid at 00 13400, slow, but the order sender did not open it
- Fri 30 Oct 01:40 bounce sell: valid at 00 13400, slow, but the order sender did not open it
- Fri 30 Oct 01:45 bounce sell: valid at 00 13400, slow, but the order sender did not open it
- Fri 30 Oct 16:25 bounce sell: **used at 00 13400**, slow: opened and closed 1 trade(s), +12.6 on the part closed (EMA pullback buy 29 Oct 22:05 +12.6); the bounce itself made +6.4
- Wed 04 Nov 10:40 bounce sell: **used at 00 13500**, slow: opened and closed 1 trade(s), -6.7 on the part closed (slow grind buy 04 Nov 08:30 -6.7); the bounce itself made -7.5
- Wed 04 Nov 15:40 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
- Wed 04 Nov 16:00 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -10.0 on the part closed (slow grind sell 04 Nov 15:35 -10.0); the bounce itself made -12.0
- Wed 04 Nov 17:10 bounce buy: **used at R2 13458.8**, slow: opened and closed 1 trade(s), -5.5 on the part closed (slow grind sell 04 Nov 16:10 -5.5); the bounce itself made +4.2
- Fri 06 Nov 07:50 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Fri 06 Nov 08:05 bounce buy: valid at S2 13399.1, slow, but the order sender did not open it
- Fri 06 Nov 08:15 bounce buy: valid at S2 13399.1, slow, but the order sender did not open it
- Refused, not at a significant level (49): 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy

**S: +1,348.0 in 161 trades** — within 8, last 3 h under 5 pips/h

- Mon 26 Oct 09:05 bounce buy: **refused, moving fast**, at S2 13338.6: trend trades held
- Mon 26 Oct 14:10 bounce buy: **used at S3 13328.6**, slow: opened and closed 5 trade(s), +13.4 on the part closed (EMA pullback sell 26 Oct 08:35 +12.0; EMA pullback sell 26 Oct 08:35 +12.0; EMA pullback sell 26 Oct 13:55 -4.8; EMA pullback sell 26 Oct 13:55 -4.8; level reversal sell 26 Oct 13:55 -1.0); the bounce itself made +7.2
- Tue 27 Oct 09:55 bounce buy: **used at 00 13300**, slow: opened and closed 1 trade(s), +8.8 on the part closed (breakout sell 27 Oct 07:00 +8.8); the bounce itself made -4.6
- Tue 27 Oct 16:40 bounce buy: **used at 00 13300**, slow: opened and closed 2 trade(s), -5.9 on the part closed (slow grind sell 27 Oct 16:05 -0.6; EMA pullback sell 27 Oct 16:15 -5.3); the bounce itself made +5.8
- Tue 27 Oct 21:15 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 06:30 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 09:35 bounce buy: valid at 00 13300, slow, but the order sender did not open it
- Thu 29 Oct 20:50 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Thu 29 Oct 20:55 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Thu 29 Oct 21:00 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Thu 29 Oct 21:05 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Thu 29 Oct 23:40 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Thu 29 Oct 23:45 bounce sell: valid at R2 13377.1, slow, but the order sender did not open it
- Fri 30 Oct 01:30 bounce sell: **refused, moving fast**, at 00 13400: trend trades held
- Fri 30 Oct 01:35 bounce sell: valid at 00 13400, slow, but the order sender did not open it
- Fri 30 Oct 01:40 bounce sell: valid at 00 13400, slow, but the order sender did not open it
- Fri 30 Oct 01:45 bounce sell: valid at 00 13400, slow, but the order sender did not open it
- Fri 30 Oct 16:25 bounce sell: **used at 00 13400**, slow: opened and closed 1 trade(s), +12.6 on the part closed (EMA pullback buy 29 Oct 22:05 +12.6); the bounce itself made +6.4
- Wed 04 Nov 10:40 bounce sell: **used at 00 13500**, slow: opened and closed 1 trade(s), -6.7 on the part closed (slow grind buy 04 Nov 08:30 -6.7); the bounce itself made -7.5
- Wed 04 Nov 15:40 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
- Wed 04 Nov 16:00 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
- Wed 04 Nov 16:05 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
- Wed 04 Nov 17:10 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
- Wed 04 Nov 17:20 bounce buy: **refused, moving fast**, at R2 13458.8: trend trades held
- Fri 06 Nov 07:50 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Fri 06 Nov 08:05 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Fri 06 Nov 08:15 bounce buy: **refused, moving fast**, at S2 13399.1: trend trades held
- Refused, not at a significant level (49): 27 Oct 07:20 buy, 27 Oct 07:25 buy, 27 Oct 07:45 buy, 28 Oct 07:25 buy, 28 Oct 10:35 buy, 28 Oct 11:15 buy, 28 Oct 11:25 buy, 28 Oct 11:30 buy, 28 Oct 11:35 buy, 28 Oct 11:45 buy, 28 Oct 15:50 sell, 29 Oct 22:30 sell, 29 Oct 23:10 sell, 29 Oct 23:20 sell, 29 Oct 23:30 sell, 30 Oct 07:45 sell, 30 Oct 10:40 sell, 30 Oct 11:20 sell, 02 Nov 09:25 sell, 03 Nov 08:20 sell, 03 Nov 08:25 sell, 04 Nov 00:40 sell, 04 Nov 00:50 sell, 04 Nov 01:50 sell, 04 Nov 02:15 sell, 05 Nov 08:15 buy, 05 Nov 08:20 buy, 05 Nov 08:50 buy, 05 Nov 18:00 sell, 05 Nov 18:10 sell, 05 Nov 18:15 sell, 06 Nov 03:55 buy, 06 Nov 04:35 buy, 06 Nov 04:50 buy, 06 Nov 10:35 buy, 06 Nov 13:20 buy, 06 Nov 14:35 buy, 09 Nov 09:00 sell, 09 Nov 09:20 sell, 09 Nov 10:55 sell, 09 Nov 20:30 sell, 10 Nov 07:55 sell, 10 Nov 08:20 sell, 10 Nov 08:45 sell, 10 Nov 08:55 sell, 11 Nov 08:35 buy, 11 Nov 09:50 buy, 11 Nov 09:55 buy, 11 Nov 10:00 buy

### Today, Wednesday 11 November, trade by trade

**current rules**: 12 trades, 9 won, 3 lost, +147.6

| Opened (UK) | Strategy | Dir | Fill | Closed | How | Pips |
|---|---|---|---:|---|---|---:|
| 06:55 | Bollinger bounce | buy | 13335.8 | 07:30 | a confirmed rejection at a level: london_session_high 13341, turning_low 13341.4 | +0.4 |
| 07:30 | EMA pullback | sell | 13330.9 | 13:20 | the take profit at IG (30 pips) | +30.0 |
| 08:10 | slow grind | sell | 13326.7 | 12:45 | the profit lock: back to 10 pips up after 15 up | +10.0 |
| 08:15 | EMA pullback | sell | 13323.1 | 13:50 | the take profit at IG (30 pips) | +30.0 |
| 08:15 | EMA pullback | sell | 13323.1 | 13:50 | the take profit at IG (30 pips) | +30.0 |
| 08:35 | Bollinger bounce | buy | 13326.0 | 09:30 | the stop at IG | -12.0 |
| 09:50 | Bollinger bounce | buy | 13321.5 | 10:45 | a confirmed rejection at a level: turning_low 13327.5 (half at 09:55, +2.0) | +1.2 |
| 10:50 | EMA pullback | sell | 13317.4 | 13:55 | the take profit at IG (30 pips) | +30.0 |
| 11:10 | range trade | buy | 13318.2 | 11:55 | a confirmed rejection at a level: previous_day_low 13312.2, new_york_session_low 13312.2, turning_low 13312.2 | -9.5 |
| 13:10 | breakout | sell | 13305.7 | 15:05 | still open at 15:10 (counted at the close) | +26.8 |
| 13:40 | level reversal | sell | 13294.3 | 14:20 | the take profit at IG (20 pips) | +20.0 |
| 14:45 | slow grind | sell | 13269.6 | 15:05 | still open at 15:10 (counted at the close) | -9.3 |

**all 39 versions of the owner's rule**: 10 trades, 8 won, 2 lost, +158.4

| Opened (UK) | Strategy | Dir | Fill | Closed | How | Pips |
|---|---|---|---:|---|---|---:|
| 06:55 | Bollinger bounce | buy | 13335.8 | 07:30 | a confirmed rejection at a level: london_session_high 13341, turning_low 13341.4 | +0.4 |
| 07:30 | EMA pullback | sell | 13330.9 | 13:20 | the take profit at IG (30 pips) | +30.0 |
| 08:10 | slow grind | sell | 13326.7 | 12:45 | the profit lock: back to 10 pips up after 15 up | +10.0 |
| 08:15 | EMA pullback | sell | 13323.1 | 13:50 | the take profit at IG (30 pips) | +30.0 |
| 08:15 | EMA pullback | sell | 13323.1 | 13:50 | the take profit at IG (30 pips) | +30.0 |
| 10:50 | EMA pullback | sell | 13317.4 | 13:55 | the take profit at IG (30 pips) | +30.0 |
| 11:10 | range trade | buy | 13318.2 | 11:55 | a confirmed rejection at a level: previous_day_low 13312.2, new_york_session_low 13312.2, turning_low 13312.2 | -9.5 |
| 13:10 | breakout | sell | 13305.7 | 15:05 | still open at 15:10 (counted at the close) | +26.8 |
| 13:40 | level reversal | sell | 13294.3 | 14:20 | the take profit at IG (20 pips) | +20.0 |
| 14:45 | slow grind | sell | 13269.6 | 15:05 | still open at 15:10 (counted at the close) | -9.3 |


## More significant levels: previous days' highs and lows, and turning levels (added in the evening)

The rule as built (commit `6ffa36f`: within 5 pips, under 5 pips an hour over the last 2 hours) was replayed again, adding any previous high or low from the last week as a significant level. There are two versions:

- **Daily highs and lows:** the high and the low of each of the previous 5 trading days. These are the bot's own daily candles (midnight to midnight UK, sell price), counted back with its own "previous trading day", so a Monday's previous day is the short Sunday candle.
- **Turning levels:** the bot's own turning highs and lows (`levels.current.build`: hourly candles, 3 each side, a 20-pip move within 6 hours, sell price) whose hourly candle started in the last 5 trading days, today's included.

Everything else is the rule exactly as built, including "in their direction", within 5 pips, and under 5 pips an hour over 2 hours. Read-only again: nothing in the bot was changed.

### Summary

- **Both are worse than the rule as built.** Daily highs and lows lose **30.6 pips** and turning levels lose **94.9 pips** (25 October to 17:35 today).
- **Today costs both versions 80.9 pips.**
  - The 09:50 bounce buy turned from 13313.5. That is 1.3 pips from Tuesday's low, 13312.2, which is both Tuesday's daily low and a turning low at Tuesday 16:00. Price had moved 3.4 pips an hour, so the bounce was valid.
  - It opened and closed the four sells: two EMA pullbacks at +1.6 each, one at +9.4, and the slow grind at +5.2 (+17.8 in all). As built, the four were held and went on to +30, +30, +30 and the slow grind's lock at +10 (+100 in all). The bounce itself made +1.2.
  - The morning was slow, as the owner said. Price paused at Tuesday's low, then ground on down through 13300 in the afternoon.
- **Tuesday 10 November is better in both** (+50.3 with daily highs and lows, +33.3 with turning levels).
  - Three EMA pullback buys from 05:00, 06:10 and 07:20 all hit their stops at 09:00 (−36.0) as built.
  - With daily highs and lows, the 08:45 bounce sell at Friday 6 November's high (13463.3) closed them at +3.0, +1.1 and −2.3. The bounce made +12.5.
  - With turning levels, the 07:55 bounce sell at the turning low of 4 November 16:00 (13453.3) closed them at −0.4, −2.3 and −5.7. That bounce made −6.8, and the 08:45 bounce sell then made +12.5.
- **Turning levels also lose 54.7 pips in the week of 25 October.** They are far more common, and they let through bounces that closed trend trades on their way to their targets:
  - the 27 October 07:00 breakout sell closed at +12.4 at 16:45 instead of reaching its +50 take profit;
  - the 28 October 11:25 bounce closed a slow grind and two EMA pullback sells at −4.1, −7.6 and −7.6.
  
  Those trades did worse still as built (−15.0, −12.0, −12.0), so the 28 October closes were a gain. The 27 October one was the big loss.
- **The first two weeks are unchanged with daily highs and lows.**
  - In those weeks the daily levels put 16 more bounces "at a level", but 13 of them were refused as moving fast.
  - The 3 that were valid (29 October 22:30 and 23:45, 6 November 13:20) were not opened by the order sender and its safety limits, so nothing closed.
  - Across the whole period, 21 bounces are decided differently. Only 2 of them opened and closed trades: Tuesday 08:45 and today 09:50.
- **How far to trust it:** the whole difference comes from the bounces that opened and closed trades: 2 with daily highs and lows, and 6 with turning levels (27 and 28 October twice, 3 November, 10 November, and today), plus what followed from them. Today alone is −80.9 in both.

### How it was done

- **Candles:** a new read-only copy of the bot's own IG candle store, taken at 17:38 UTC (`data/research/replay_stores/live_copy_20261111_1738/`). It ends with the candle that finished at 17:35 UTC.
  - The run goes from Sunday 25 October 21:00 UTC to 17:35 UTC today.
  - The rule as built was run again on the same candles, so all three are compared over the same period. It gives the same 158 trades as at 15:10, but the trades still open then are now counted later. Today's 14:45 slow grind sell was stopped at 15:10 (−15.0 instead of −9.3), and the 13:10 breakout sell is at +30.8 instead of +26.8. That makes +1,377.8 instead of +1,379.5.
- **Code:** a frozen copy of the committed code, `6ffa36f`, run with `research.long_replay.replay_week`: the bot's own engine, strategies, safety rules, paper order sender and trade manager.
  - The one change is a research-only patch, made in the research process: `trading.against_trend.levels_at` also returns the extra levels.
  - Every bounce decision below is the bot's own decision log ("bounce refused" or "bounce against trend trades"). Every close is the trade manager's own record.
  - The script and the runs are in `data/research/replay/pace_levels_20261111/`.
- **Settings, prices and news rules:** as in the rest of this report. No candle reached both a trade's stop and its target.

### Results

#### Trades, wins, losses and pips

| Version | Trades | Won | Lost | Pips | Against as built |
|---|---:|---:|---:|---:|---:|
| As built | 158 | 84 | 73 | +1,377.8 |  |
| + daily highs and lows, previous 5 days | 160 | 88 | 71 | +1,347.2 | -30.6 |
| + turning levels, last 5 days | 164 | 86 | 78 | +1,282.9 | -94.9 |

#### By week: trades (won–lost) and pips

| Version | 25 to 30 Oct | 1 to 6 Nov | 8 to 11 Nov 17:35 |
|---|---:|---:|---:|
| As built | 49 (28–20) +267.1 | 78 (40–38) +814.1 | 31 (16–15) +296.6 |
| + daily highs and lows, previous 5 days | 49 (28–20) +267.1 | 78 (40–38) +814.1 | 33 (20–13) +266.0 |
| + turning levels, last 5 days | 52 (28–24) +212.4 | 78 (40–38) +821.5 | 34 (18–16) +249.0 |

#### Every bounce that changes: + daily highs and lows, previous 5 days, 24 bounces decided differently

| Bounce (UK) | Turned from | As built | + daily highs and lows, previous 5 days |
|---|---:|---|---|
| Thu 29 Oct 20:50 sell | 13384.4 | refused, not at a significant level (nearest R2 13377.1 (7.3 pips)) | refused, moving fast at daily high Mon 26 Oct 13387.3 (10.6 pips/h) |
| Thu 29 Oct 20:55 sell | 13384.4 | refused, not at a significant level (nearest R2 13377.1 (7.3 pips)) | refused, moving fast at daily high Mon 26 Oct 13387.3 (8.2 pips/h) |
| Thu 29 Oct 21:00 sell | 13383.2 | refused, not at a significant level (nearest R2 13377.1 (6.1 pips)) | refused, moving fast at daily high Mon 26 Oct 13387.3 (5.0 pips/h) |
| Thu 29 Oct 22:30 sell | 13389.0 | refused, not at a significant level (nearest 00 13400 (11.0 pips)) | **valid at daily high Mon 26 Oct 13387.3** (0.6 pips/h); not opened by the order sender (its safety limits), so nothing closed |
| Thu 29 Oct 23:10 sell | 13387.8 | refused, not at a significant level (nearest R2 13377.1 (10.7 pips)) | refused, moving fast at daily high Mon 26 Oct 13387.3 (8.5 pips/h) |
| Thu 29 Oct 23:20 sell | 13387.8 | refused, not at a significant level (nearest R2 13377.1 (10.7 pips)) | refused, moving fast at daily high Mon 26 Oct 13387.3 (7.4 pips/h) |
| Thu 29 Oct 23:30 sell | 13385.9 | refused, not at a significant level (nearest R2 13377.1 (8.8 pips)) | refused, moving fast at daily high Mon 26 Oct 13387.3 (6.7 pips/h) |
| Thu 29 Oct 23:40 sell | 13384.9 | refused, not at a significant level (nearest R2 13377.1 (7.8 pips)) | refused, moving fast at daily high Mon 26 Oct 13387.3 (6.7 pips/h) |
| Thu 29 Oct 23:45 sell | 13383.4 | refused, not at a significant level (nearest R2 13377.1 (6.3 pips)) | **valid at daily high Mon 26 Oct 13387.3** (4.0 pips/h); not opened by the order sender (its safety limits), so nothing closed |
| Wed 04 Nov 00:40 sell | 13443.3 | refused, not at a significant level (nearest R2 13458.8 (15.5 pips)) | refused, moving fast at daily high Mon 02 Nov 13448.0 (14.8 pips/h) |
| Wed 04 Nov 00:50 sell | 13443.3 | refused, not at a significant level (nearest R2 13458.8 (15.5 pips)) | refused, moving fast at daily high Mon 02 Nov 13448.0 (12.6 pips/h) |
| Fri 06 Nov 03:55 buy | 13428.7 | refused, not at a significant level (nearest 00 13400 (28.7 pips)) | refused, moving fast at daily low Wed 04 Nov 13425.5 (7.6 pips/h) |
| Fri 06 Nov 04:35 buy | 13425.2 | refused, not at a significant level (nearest 00 13400 (25.2 pips)) | refused, moving fast at daily low Wed 04 Nov 13425.5 (8.3 pips/h) |
| Fri 06 Nov 04:50 buy | 13425.8 | refused, not at a significant level (nearest 00 13400 (25.8 pips)) | refused, moving fast at daily low Wed 04 Nov 13425.5 (6.6 pips/h) |
| Fri 06 Nov 10:35 buy | 13380.7 | refused, not at a significant level (nearest weekly pivot 13364.2 (16.5 pips)) | refused, moving fast at daily low Mon 02 Nov 13379.1 (7.0 pips/h) |
| Fri 06 Nov 13:20 buy | 13380.5 | refused, not at a significant level (nearest weekly pivot 13364.2 (16.3 pips)) | **valid at daily low Mon 02 Nov 13379.1** (4.5 pips/h); not opened by the order sender (its safety limits), so nothing closed |
| Mon 09 Nov 10:55 sell | 13422.9 | refused, not at a significant level (nearest 00 13400 (22.9 pips)) | **valid at daily low Wed 04 Nov 13425.5** (3.8 pips/h); not opened by the order sender (its safety limits), so nothing closed |
| Mon 09 Nov 20:30 sell | 13440.6 | refused, not at a significant level (nearest 00 13400 (40.6 pips)) | refused, moving fast at daily low Thu 05 Nov 13435.7 (5.6 pips/h) |
| Tue 10 Nov 08:45 sell | 13458.6 | refused, not at a significant level (nearest R2 13498.9 (40.3 pips)) | **valid at daily high Fri 06 Nov 13463.3** (2.8 pips/h); the bounce made +12.5; closed 3: EMA pullback +3.0, EMA pullback +1.1, EMA pullback -2.3 |
| Tue 10 Nov 08:55 sell | 13457.5 | refused, not at a significant level (nearest R2 13498.9 (41.4 pips)) | no such bounce (the trades before it differ) |
| Wed 11 Nov 08:35 buy | 13314.2 | refused, not at a significant level (nearest 00 13300 (14.2 pips)) | refused, moving fast at daily low Tue 10 Nov 13312.2 (5.9 pips/h) |
| Wed 11 Nov 09:50 buy | 13313.5 | refused, not at a significant level (nearest 00 13300 (13.5 pips)) | **valid at daily low Tue 10 Nov 13312.2** (3.4 pips/h); the bounce made +1.2; closed 4: EMA pullback +9.4, slow grind +5.2, EMA pullback +1.6, EMA pullback +1.6 |
| Wed 11 Nov 09:55 buy | 13314.9 | refused, not at a significant level (nearest 00 13300 (14.9 pips)) | no such bounce (the trades before it differ) |
| Wed 11 Nov 10:00 buy | 13316.4 | refused, not at a significant level (nearest 00 13300 (16.4 pips)) | no such bounce (the trades before it differ) |

Trades that differ (7 only as built, 9 only in this version):

| | Opened (UK) | Strategy | Dir | Closed | Pips |
|---|---|---|---|---|---:|
| as built | Tue 10 Nov 05:00 | EMA pullback | buy | Tue 09:00 | -12.0 |
| as built | Tue 10 Nov 06:10 | EMA pullback | buy | Tue 09:00 | -12.0 |
| as built | Tue 10 Nov 07:20 | EMA pullback | buy | Tue 09:00 | -12.0 |
| as built | Wed 11 Nov 07:30 | EMA pullback | sell | Wed 13:20 | +30.0 |
| as built | Wed 11 Nov 08:10 | slow grind | sell | Wed 12:45 | +10.0 |
| as built | Wed 11 Nov 08:15 | EMA pullback | sell | Wed 13:50 | +30.0 |
| as built | Wed 11 Nov 08:15 | EMA pullback | sell | Wed 13:50 | +30.0 |
| this version | Tue 10 Nov 05:00 | EMA pullback | buy | Tue 08:45 | +3.0 |
| this version | Tue 10 Nov 06:10 | EMA pullback | buy | Tue 08:45 | +1.1 |
| this version | Tue 10 Nov 07:20 | EMA pullback | buy | Tue 08:45 | -2.3 |
| this version | Tue 10 Nov 08:45 | Bollinger bounce | sell | Tue 10:40 | +12.5 |
| this version | Wed 11 Nov 07:30 | EMA pullback | sell | Wed 09:50 | +9.4 |
| this version | Wed 11 Nov 08:10 | slow grind | sell | Wed 09:50 | +5.2 |
| this version | Wed 11 Nov 08:15 | EMA pullback | sell | Wed 09:50 | +1.6 |
| this version | Wed 11 Nov 08:15 | EMA pullback | sell | Wed 09:50 | +1.6 |
| this version | Wed 11 Nov 09:50 | Bollinger bounce | buy | Wed 10:45 | +1.2 |
| | | | | **Net** | **-30.6** |

#### Every bounce that changes: + turning levels, last 5 days, 47 bounces decided differently

| Bounce (UK) | Turned from | As built | + turning levels, last 5 days |
|---|---:|---|---|
| Tue 27 Oct 16:45 buy | 13305.9 | refused, not at a significant level (nearest 00 13300 (5.9 pips)) | **valid at turning low Tue 27 Oct 09:00 13307.2** (4.7 pips/h); the bounce made +3.0; closed 3: breakout +12.4, slow grind -3.4, EMA pullback -8.1 |
| Tue 27 Oct 16:55 buy | 13306.2 | refused, not at a significant level (nearest 00 13300 (6.2 pips)) | no such bounce (the trades before it differ) |
| Tue 27 Oct 17:00 buy | 13308.1 | refused, not at a significant level (nearest 00 13300 (8.1 pips)) | no such bounce (the trades before it differ) |
| Tue 27 Oct 17:10 buy | 13310.9 | refused, not at a significant level (nearest 00 13300 (10.9 pips)) | no such bounce (the trades before it differ) |
| Wed 28 Oct 11:15 buy | 13273.9 | refused, not at a significant level (nearest S2 13263.6 (10.3 pips)) | refused, moving fast at turning low Wed 28 Oct 07:00 13272.5 (5.8 pips/h) |
| Wed 28 Oct 11:25 buy | 13273.9 | refused, not at a significant level (nearest S2 13263.6 (10.3 pips)) | **valid at turning low Wed 28 Oct 07:00 13272.5** (4.8 pips/h); the bounce made +5.6; closed 3: slow grind -4.1, EMA pullback -7.6, EMA pullback -7.6 |
| Wed 28 Oct 11:30 buy | 13278.5 | refused, not at a significant level (nearest S2 13263.6 (14.9 pips)) | no such bounce (the trades before it differ) |
| Wed 28 Oct 11:35 buy | 13279.5 | refused, not at a significant level (nearest S2 13263.6 (15.9 pips)) | no such bounce (the trades before it differ) |
| Wed 28 Oct 11:45 buy | 13281.8 | refused, not at a significant level (nearest S2 13263.6 (18.2 pips)) | no such bounce (the trades before it differ) |
| Wed 28 Oct 15:50 sell | 13305.1 | refused, not at a significant level (nearest weekly pivot 13359.7 (54.6 pips)) | **valid at turning low Tue 27 Oct 09:00 13307.2** (1.4 pips/h); the bounce made -7.7; closed 1: slow grind -8.8 |
| Wed 28 Oct 17:05 sell | 13321.1 | no such bounce (the trades before it differ) | refused, not at a significant level (nearest turning low Mon 26 Oct 13:00 13327.1 (6.0 pips)) |
| Wed 28 Oct 17:20 sell | 13321.1 | no such bounce (the trades before it differ) | refused, not at a significant level (nearest turning low Mon 26 Oct 13:00 13327.1 (6.0 pips)) |
| Wed 28 Oct 17:25 sell | 13315.2 | no such bounce (the trades before it differ) | refused, not at a significant level (nearest turning low Mon 26 Oct 13:00 13327.1 (11.9 pips)) |
| Wed 28 Oct 17:35 sell | 13313.8 | no such bounce (the trades before it differ) | refused, not at a significant level (nearest turning low Mon 26 Oct 13:00 13327.1 (13.3 pips)) |
| Wed 28 Oct 17:45 sell | 13312.7 | no such bounce (the trades before it differ) | refused, not at a significant level (nearest turning low Mon 26 Oct 13:00 13327.1 (14.4 pips)) |
| Thu 29 Oct 20:50 sell | 13384.4 | refused, not at a significant level (nearest R2 13377.1 (7.3 pips)) | refused, moving fast at turning high Mon 26 Oct 01:00 13387.3 (10.6 pips/h) |
| Thu 29 Oct 20:55 sell | 13384.4 | refused, not at a significant level (nearest R2 13377.1 (7.3 pips)) | refused, moving fast at turning high Mon 26 Oct 01:00 13387.3 (8.2 pips/h) |
| Thu 29 Oct 21:00 sell | 13383.2 | refused, not at a significant level (nearest R2 13377.1 (6.1 pips)) | refused, moving fast at turning high Mon 26 Oct 01:00 13387.3 (5.0 pips/h) |
| Thu 29 Oct 22:30 sell | 13389.0 | refused, not at a significant level (nearest 00 13400 (11.0 pips)) | **valid at turning high Fri 23 Oct 16:00 13388.0** (0.6 pips/h); not opened by the order sender (its safety limits), so nothing closed |
| Thu 29 Oct 23:10 sell | 13387.8 | refused, not at a significant level (nearest R2 13377.1 (10.7 pips)) | refused, moving fast at turning high Fri 23 Oct 16:00 13388.0 (8.5 pips/h) |
| Thu 29 Oct 23:20 sell | 13387.8 | refused, not at a significant level (nearest R2 13377.1 (10.7 pips)) | refused, moving fast at turning high Fri 23 Oct 16:00 13388.0 (7.4 pips/h) |
| Thu 29 Oct 23:30 sell | 13385.9 | refused, not at a significant level (nearest R2 13377.1 (8.8 pips)) | refused, moving fast at turning high Mon 26 Oct 01:00 13387.3 (6.7 pips/h) |
| Thu 29 Oct 23:40 sell | 13384.9 | refused, not at a significant level (nearest R2 13377.1 (7.8 pips)) | refused, moving fast at turning high Mon 26 Oct 01:00 13387.3 (6.7 pips/h) |
| Thu 29 Oct 23:45 sell | 13383.4 | refused, not at a significant level (nearest R2 13377.1 (6.3 pips)) | **valid at turning high Mon 26 Oct 01:00 13387.3** (4.0 pips/h); not opened by the order sender (its safety limits), so nothing closed |
| Fri 30 Oct 16:25 sell | 13406.0 | refused, not at a significant level (nearest 00 13400 (6.0 pips)) | refused, moving fast at turning high Fri 30 Oct 01:00 13406.5 (7.0 pips/h) |
| Tue 03 Nov 08:20 sell | 13426.4 | refused, not at a significant level (nearest R2 13480.5 (54.1 pips)) | **valid at turning high Mon 02 Nov 13:00 13430.3** (3.2 pips/h); the bounce made +3.8; closed 1: EMA pullback -7.8 |
| Tue 03 Nov 08:25 sell | 13426.3 | refused, not at a significant level (nearest R2 13480.5 (54.2 pips)) | no such bounce (the trades before it differ) |
| Wed 04 Nov 00:40 sell | 13443.3 | refused, not at a significant level (nearest R2 13458.8 (15.5 pips)) | refused, moving fast at turning high Mon 02 Nov 09:00 13448.0 (14.8 pips/h) |
| Wed 04 Nov 00:50 sell | 13443.3 | refused, not at a significant level (nearest R2 13458.8 (15.5 pips)) | refused, moving fast at turning high Mon 02 Nov 09:00 13448.0 (12.6 pips/h) |
| Thu 05 Nov 08:15 buy | 13464.4 | refused, not at a significant level (nearest 00 13400 (64.4 pips)) | refused, moving fast at turning low Wed 04 Nov 11:00 13468.2 (5.5 pips/h) |
| Thu 05 Nov 08:20 buy | 13467.2 | refused, not at a significant level (nearest 00 13400 (67.2 pips)) | refused, moving fast at turning low Wed 04 Nov 11:00 13468.2 (5.2 pips/h) |
| Thu 05 Nov 08:50 buy | 13468.6 | refused, not at a significant level (nearest 00 13400 (68.6 pips)) | refused, moving fast at turning low Wed 04 Nov 11:00 13468.2 (8.6 pips/h) |
| Fri 06 Nov 03:55 buy | 13428.7 | refused, not at a significant level (nearest 00 13400 (28.7 pips)) | refused, moving fast at turning high Mon 02 Nov 13:00 13430.3 (7.6 pips/h) |
| Fri 06 Nov 04:35 buy | 13425.2 | refused, not at a significant level (nearest 00 13400 (25.2 pips)) | refused, moving fast at turning high Tue 03 Nov 08:00 13426.4 (8.3 pips/h) |
| Fri 06 Nov 04:50 buy | 13425.8 | refused, not at a significant level (nearest 00 13400 (25.8 pips)) | refused, moving fast at turning high Tue 03 Nov 08:00 13426.4 (6.6 pips/h) |
| Fri 06 Nov 10:35 buy | 13380.7 | refused, not at a significant level (nearest weekly pivot 13364.2 (16.5 pips)) | refused, moving fast at turning low Sun 01 Nov 23:00 13378.4 (7.0 pips/h) |
| Fri 06 Nov 13:20 buy | 13380.5 | refused, not at a significant level (nearest weekly pivot 13364.2 (16.3 pips)) | **valid at turning low Sun 01 Nov 23:00 13378.4** (4.5 pips/h); not opened by the order sender (its safety limits), so nothing closed |
| Mon 09 Nov 10:55 sell | 13422.9 | refused, not at a significant level (nearest 00 13400 (22.9 pips)) | **valid at turning high Tue 03 Nov 08:00 13426.4** (3.8 pips/h); not opened by the order sender (its safety limits), so nothing closed |
| Mon 09 Nov 20:30 sell | 13440.6 | refused, not at a significant level (nearest 00 13400 (40.6 pips)) | refused, moving fast at turning low Thu 05 Nov 12:00 13445.2 (5.6 pips/h) |
| Tue 10 Nov 07:55 sell | 13457.9 | refused, not at a significant level (nearest R2 13498.9 (41.0 pips)) | **valid at turning low Wed 04 Nov 16:00 13453.3** (3.4 pips/h); the bounce made -6.8; closed 3: EMA pullback -0.4, EMA pullback -2.3, EMA pullback -5.7 |
| Tue 10 Nov 08:20 sell | 13457.1 | refused, not at a significant level (nearest R2 13498.9 (41.8 pips)) | no such bounce (the trades before it differ) |
| Tue 10 Nov 08:45 sell | 13458.6 | refused, not at a significant level (nearest R2 13498.9 (40.3 pips)) | no such bounce (the trades before it differ) |
| Tue 10 Nov 08:55 sell | 13457.5 | refused, not at a significant level (nearest R2 13498.9 (41.4 pips)) | no such bounce (the trades before it differ) |
| Wed 11 Nov 08:35 buy | 13314.2 | refused, not at a significant level (nearest 00 13300 (14.2 pips)) | refused, moving fast at turning low Tue 10 Nov 16:00 13312.2 (5.9 pips/h) |
| Wed 11 Nov 09:50 buy | 13313.5 | refused, not at a significant level (nearest 00 13300 (13.5 pips)) | **valid at turning low Tue 10 Nov 16:00 13312.2** (3.4 pips/h); the bounce made +1.2; closed 4: EMA pullback +9.4, slow grind +5.2, EMA pullback +1.6, EMA pullback +1.6 |
| Wed 11 Nov 09:55 buy | 13314.9 | refused, not at a significant level (nearest 00 13300 (14.9 pips)) | no such bounce (the trades before it differ) |
| Wed 11 Nov 10:00 buy | 13316.4 | refused, not at a significant level (nearest 00 13300 (16.4 pips)) | no such bounce (the trades before it differ) |

Trades that differ (17 only as built, 23 only in this version):

| | Opened (UK) | Strategy | Dir | Closed | Pips |
|---|---|---|---|---|---:|
| as built | Tue 27 Oct 07:00 | breakout | sell | Wed 07:10 | +50.0 |
| as built | Tue 27 Oct 16:05 | slow grind | sell | Tue 20:30 | +0.0 |
| as built | Tue 27 Oct 16:15 | EMA pullback | sell | Tue 17:00 | -12.0 |
| as built | Wed 28 Oct 10:20 | slow grind | sell | Wed 13:30 | -15.0 |
| as built | Wed 28 Oct 10:45 | EMA pullback | sell | Wed 11:35 | -12.0 |
| as built | Wed 28 Oct 10:45 | EMA pullback | sell | Wed 11:35 | -12.0 |
| as built | Wed 28 Oct 15:30 | slow grind | buy | Wed 17:00 | +10.0 |
| as built | Wed 28 Oct 17:05 | Bollinger bounce | sell | Wed 17:45 | +4.3 |
| as built | Tue 03 Nov 08:05 | EMA pullback | buy | Tue 08:30 | -12.0 |
| as built | Tue 03 Nov 08:30 | Bollinger bounce | sell | Tue 09:25 | +0.6 |
| as built | Tue 10 Nov 05:00 | EMA pullback | buy | Tue 09:00 | -12.0 |
| as built | Tue 10 Nov 06:10 | EMA pullback | buy | Tue 09:00 | -12.0 |
| as built | Tue 10 Nov 07:20 | EMA pullback | buy | Tue 09:00 | -12.0 |
| as built | Wed 11 Nov 07:30 | EMA pullback | sell | Wed 13:20 | +30.0 |
| as built | Wed 11 Nov 08:10 | slow grind | sell | Wed 12:45 | +10.0 |
| as built | Wed 11 Nov 08:15 | EMA pullback | sell | Wed 13:50 | +30.0 |
| as built | Wed 11 Nov 08:15 | EMA pullback | sell | Wed 13:50 | +30.0 |
| this version | Tue 27 Oct 07:00 | breakout | sell | Tue 16:45 | +12.4 |
| this version | Tue 27 Oct 16:05 | slow grind | sell | Tue 16:45 | -3.4 |
| this version | Tue 27 Oct 16:15 | EMA pullback | sell | Tue 16:45 | -8.1 |
| this version | Tue 27 Oct 16:45 | Bollinger bounce | buy | Tue 17:35 | +3.0 |
| this version | Wed 28 Oct 10:20 | slow grind | sell | Wed 11:25 | -4.1 |
| this version | Wed 28 Oct 10:45 | EMA pullback | sell | Wed 11:25 | -7.6 |
| this version | Wed 28 Oct 10:45 | EMA pullback | sell | Wed 11:25 | -7.6 |
| this version | Wed 28 Oct 11:25 | Bollinger bounce | buy | Wed 12:30 | +5.6 |
| this version | Wed 28 Oct 15:30 | slow grind | buy | Wed 15:50 | -8.8 |
| this version | Wed 28 Oct 15:50 | Bollinger bounce | sell | Wed 16:00 | -7.7 |
| this version | Wed 28 Oct 16:50 | slow grind | buy | Wed 17:50 | -15.0 |
| this version | Tue 03 Nov 08:05 | EMA pullback | buy | Tue 08:20 | -7.8 |
| this version | Tue 03 Nov 08:20 | Bollinger bounce | sell | Tue 09:25 | +3.8 |
| this version | Tue 10 Nov 05:00 | EMA pullback | buy | Tue 07:55 | -0.4 |
| this version | Tue 10 Nov 06:10 | EMA pullback | buy | Tue 07:55 | -2.3 |
| this version | Tue 10 Nov 07:20 | EMA pullback | buy | Tue 07:55 | -5.7 |
| this version | Tue 10 Nov 07:55 | Bollinger bounce | sell | Tue 08:30 | -6.8 |
| this version | Tue 10 Nov 08:45 | Bollinger bounce | sell | Tue 10:40 | +12.5 |
| this version | Wed 11 Nov 07:30 | EMA pullback | sell | Wed 09:50 | +9.4 |
| this version | Wed 11 Nov 08:10 | slow grind | sell | Wed 09:50 | +5.2 |
| this version | Wed 11 Nov 08:15 | EMA pullback | sell | Wed 09:50 | +1.6 |
| this version | Wed 11 Nov 08:15 | EMA pullback | sell | Wed 09:50 | +1.6 |
| this version | Wed 11 Nov 09:50 | Bollinger bounce | buy | Wed 10:45 | +1.2 |
| | | | | **Net** | **-94.9** |

#### Today, Wednesday 11 November

**As built:** 10 trades, 8 won, 2 lost, +156.7

| Opened (UK) | Strategy | Dir | Fill | Closed | How | Pips |
|---|---|---|---:|---|---|---:|
| 06:55 | Bollinger bounce | buy | 13335.8 | 07:30 | a confirmed rejection at a level: london_session_high 13341, turning_low 13341.4 | +0.4 |
| 07:30 | EMA pullback | sell | 13330.9 | 13:20 | the take profit at IG (30 pips) | +30.0 |
| 08:10 | slow grind | sell | 13326.7 | 12:45 | the profit lock: back to 10 pips up after 15 up | +10.0 |
| 08:15 | EMA pullback | sell | 13323.1 | 13:50 | the take profit at IG (30 pips) | +30.0 |
| 08:15 | EMA pullback | sell | 13323.1 | 13:50 | the take profit at IG (30 pips) | +30.0 |
| 10:50 | EMA pullback | sell | 13317.4 | 13:55 | the take profit at IG (30 pips) | +30.0 |
| 11:10 | range trade | buy | 13318.2 | 11:55 | a confirmed rejection at a level: previous_day_low 13312.2, new_york_session_low 13312.2, turning_low 13312.2 | -9.5 |
| 13:10 | breakout | sell | 13305.7 | 17:30 | still open at 17:35 (counted at the close) | +30.8 |
| 13:40 | level reversal | sell | 13294.3 | 14:20 | the take profit at IG (20 pips) | +20.0 |
| 14:45 | slow grind | sell | 13269.6 | 15:10 | the stop at IG | -15.0 |

**+ daily highs and lows, previous 5 days:** 11 trades, 9 won, 2 lost, +75.8

| Opened (UK) | Strategy | Dir | Fill | Closed | How | Pips |
|---|---|---|---:|---|---|---:|
| 06:55 | Bollinger bounce | buy | 13335.8 | 07:30 | a confirmed rejection at a level: london_session_high 13341, turning_low 13341.4 | +0.4 |
| 07:30 | EMA pullback | sell | 13330.9 | 09:50 | a Bollinger bounce buy opened at daily low Tue 10 Nov 13312.2, price moving slowly (3.4 pips an hour) | +9.4 |
| 08:10 | slow grind | sell | 13326.7 | 09:50 | a Bollinger bounce buy opened at daily low Tue 10 Nov 13312.2, price moving slowly (3.4 pips an hour) | +5.2 |
| 08:15 | EMA pullback | sell | 13323.1 | 09:50 | a Bollinger bounce buy opened at daily low Tue 10 Nov 13312.2, price moving slowly (3.4 pips an hour) | +1.6 |
| 08:15 | EMA pullback | sell | 13323.1 | 09:50 | a Bollinger bounce buy opened at daily low Tue 10 Nov 13312.2, price moving slowly (3.4 pips an hour) | +1.6 |
| 09:50 | Bollinger bounce | buy | 13321.5 | 10:45 | a confirmed rejection at a level: turning_low 13327.5 | +1.2 |
| 10:50 | EMA pullback | sell | 13317.4 | 13:55 | the take profit at IG (30 pips) | +30.0 |
| 11:10 | range trade | buy | 13318.2 | 11:55 | a confirmed rejection at a level: previous_day_low 13312.2, new_york_session_low 13312.2, turning_low 13312.2 | -9.5 |
| 13:10 | breakout | sell | 13305.7 | 17:30 | still open at 17:35 (counted at the close) | +30.8 |
| 13:40 | level reversal | sell | 13294.3 | 14:20 | the take profit at IG (20 pips) | +20.0 |
| 14:45 | slow grind | sell | 13269.6 | 15:10 | the stop at IG | -15.0 |

**+ turning levels, last 5 days:** 11 trades, 9 won, 2 lost, +75.8

| Opened (UK) | Strategy | Dir | Fill | Closed | How | Pips |
|---|---|---|---:|---|---|---:|
| 06:55 | Bollinger bounce | buy | 13335.8 | 07:30 | a confirmed rejection at a level: london_session_high 13341, turning_low 13341.4 | +0.4 |
| 07:30 | EMA pullback | sell | 13330.9 | 09:50 | a Bollinger bounce buy opened at turning low Tue 10 Nov 16:00 13312.2, price moving slowly (3.4 pips an hour) | +9.4 |
| 08:10 | slow grind | sell | 13326.7 | 09:50 | a Bollinger bounce buy opened at turning low Tue 10 Nov 16:00 13312.2, price moving slowly (3.4 pips an hour) | +5.2 |
| 08:15 | EMA pullback | sell | 13323.1 | 09:50 | a Bollinger bounce buy opened at turning low Tue 10 Nov 16:00 13312.2, price moving slowly (3.4 pips an hour) | +1.6 |
| 08:15 | EMA pullback | sell | 13323.1 | 09:50 | a Bollinger bounce buy opened at turning low Tue 10 Nov 16:00 13312.2, price moving slowly (3.4 pips an hour) | +1.6 |
| 09:50 | Bollinger bounce | buy | 13321.5 | 10:45 | a confirmed rejection at a level: turning_low 13327.5 | +1.2 |
| 10:50 | EMA pullback | sell | 13317.4 | 13:55 | the take profit at IG (30 pips) | +30.0 |
| 11:10 | range trade | buy | 13318.2 | 11:55 | a confirmed rejection at a level: previous_day_low 13312.2, new_york_session_low 13312.2, turning_low 13312.2 | -9.5 |
| 13:10 | breakout | sell | 13305.7 | 17:30 | still open at 17:35 (counted at the close) | +30.8 |
| 13:40 | level reversal | sell | 13294.3 | 14:20 | the take profit at IG (20 pips) | +20.0 |
| 14:45 | slow grind | sell | 13269.6 | 15:10 | the stop at IG | -15.0 |

Today's bounces against trend trades, as built: 08:35 buy refused, not at a significant level (nearest 00 13300 (14.2 pips)); 09:50 buy refused, not at a significant level (nearest 00 13300 (13.5 pips)); 09:55 buy refused, not at a significant level (nearest 00 13300 (14.9 pips)); 10:00 buy refused, not at a significant level (nearest 00 13300 (16.4 pips)); 15:10 buy refused, not at a significant level (nearest 00 13300 (34.4 pips))

Today's bounces against trend trades, + daily highs and lows, previous 5 days: 08:35 buy refused, moving fast at daily low Tue 10 Nov 13312.2 (5.9 pips/h); 09:50 buy **valid at daily low Tue 10 Nov 13312.2** (3.4 pips/h); the bounce made +1.2; closed 4: EMA pullback +9.4, slow grind +5.2, EMA pullback +1.6, EMA pullback +1.6; 15:10 buy refused, not at a significant level (nearest 00 13300 (34.4 pips))

Today's bounces against trend trades, + turning levels, last 5 days: 08:35 buy refused, moving fast at turning low Tue 10 Nov 16:00 13312.2 (5.9 pips/h); 09:50 buy **valid at turning low Tue 10 Nov 16:00 13312.2** (3.4 pips/h); the bounce made +1.2; closed 4: EMA pullback +9.4, slow grind +5.2, EMA pullback +1.6, EMA pullback +1.6; 15:10 buy refused, not at a significant level (nearest 00 13300 (34.4 pips))

