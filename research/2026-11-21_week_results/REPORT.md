# Week results, Mon 16 Nov 00:00 to Fri 20 Nov 22:00 UK

Johnny's brief, 21 Nov 2026. Read-only: nothing in the code, settings or the live bot was changed.

- `week_results.csv`: one row per trade, 52 trades. Every time is UK time (GMT in November, so the same as UTC).
- `build.py` builds the CSV and `summary.py` builds the tables below. To rebuild:
  `AUTOBOT_ENV_FILE=/opt/autobot/.env .venv/bin/python research/2026-11-21_week_results/build.py && python3 research/2026-11-21_week_results/summary.py`

## The week in one line

52 trades, 15 wins, 36 losses and 1 flat: **−312.1 pips, −£3,121 at £10 a point**. Johnny closed 6 of those
trades by hand (−35.6 pips). The bot's own 46 trades made **−276.5 pips (−£2,765)**.

| Day | Trades | Pips |
|---|---:|---:|
| Mon 16 Nov | 13 | −109.2 |
| Tue 17 Nov | 11 | −74.8 |
| Wed 18 Nov | 7 | −33.4 |
| Thu 19 Nov | 7 | −21.1 |
| Fri 20 Nov | 14 | −73.6 |

Who closed the trades: IG's stop 36 (8 of them at a trailed stop, 7 of those in profit), the 20:30 close 6, Johnny by hand 6,
and the bot itself 4 (a range trade at the opposite band, a close before big news, and two 5-minute bounces closed at
a level). No trade reached its take profit. 15 trades opened while another trade was open in the opposite
direction.

## Where the figures come from

- **IG's prices win.** Entry, stop, take profit, close price and close time come from IG's own records (IG's activity
  and transactions, saved by the price service's read-only IG check). 50 trades have both. The last two on Fri 20 Nov
  (18:45 level reversal and 19:31 breakout) came after IG's last check (18:53). For those two, the figures come from
  IG's deal confirmations and close activity, which the order journal copies. IG's £ result for the 19:31 breakout is
  blank because IG's transaction for it was never fetched. Its pips come from IG's levels. Where IG's £ is given, it
  matches pips × £10 on every trade. One close price differed from the bot's own record (18 Nov 12:37 EMA pullback:
  bot 13169.0, IG 13168.4), and the table uses IG's.
- **Strategy, analyser state and close reason** come from the bot's trade records. The analyser state is the label
  the bot saved when the trade opened, word for word. "ranging none" is the bot's own label for ranging with no
  direction.
- **Code version** is the commit loaded at each price-service start (the "Trading ON" lines in the log, matched to
  git reflog). The service was not restarted after Thu 19 Nov 18:44, so 02f6c7e (first-build-plus) ran to the end of
  the week. The checkouts of 26c06fc, bb085f4 and 5d7942e on 19–20 Nov were never loaded by the running service.
- **Candles**: the stored 5-minute, hourly and daily candles, which hold both buy and sell prices.

## How each column is worked out

- **Stop and take-profit pips**: the distance from IG's fill to IG's stop and limit levels at the open.
  Risk-to-reward = take-profit pips ÷ stop pips.
- **Pips and £**: IG's close minus IG's fill (sign flipped for sells), × £10.
- **Who closed it**: "IG stop" or "IG limit" come from the bot's record of how it closed, checked against IG's
  channel. "Johnny by hand" means IG's channel SYSTEM but not at the stop or limit. "20:30 close" is the bot's
  scheduled close. "bot" is any other close the bot sent. A stop at a trailed level says "trailed to …".
- **MFE and MAE** (best and worst pips): a buy is measured on the sell price and a sell on the buy price, as IG
  closes them. Only prices known to fall inside the trade's life are used:
  - the fill;
  - the entry candle's high and low only if the fill came within 10 seconds of the candle's start, otherwise just
    its close;
  - every 5-minute candle that started and finished while the trade was open;
  - the open of the candle the trade closed in;
  - the close price.

  The high and low of the closing candle are left out because they may have come after the close. So MFE and MAE
  are exact at the close but can **understate** a move inside the entry candle or the closing candle. Times are to
  the 5-minute candle: a candle's extreme is timed at its start, or at the fill if that is later. "0 min" means in
  the entry candle, or that price never went that way (MFE or MAE of 0.0).
- **First 15 minutes**: the same known prices, up to 15 minutes after the fill. For a trade open under 15 minutes,
  this covers its whole life, and the row says so.
- **Session** (UK clock): Asian 00:00–07:00 (the bot's Asian range), London 07:00–13:00, London/NY overlap
  13:00–17:00 (New York opens at 08:00 ET, which is 13:00 GMT), New York 17:00–22:00. The bot has no setting that
  defines an overlap, so these hours are the report's own choice.
- **Daily levels**: pivot, R1–R3 and S1–S3 exactly as the bot had them at the fill. They come from the bot's own
  level code: classic floor pivots from the previous trading day's sell-price candle, so Monday's come from the short
  Sunday candle. "Ahead" means above the fill for a buy and below it for a sell. Pips are measured from IG's fill.
  The bot's levels file warned that the day before had missing 5-minute candles (Sun 15: 6, Mon 16: 2, Thu 19: 1).
  The notes column repeats that warning. Seven Monday sells opened below S3, so they had no daily level ahead, and
  those cells are blank.
- **5-minute position, 8 EMA, RSI 3, MACD (35,45,30) histogram, hourly 8/13/21 EMAs**: all on the sell (chart)
  price, worked out with the bot's own indicator code at the last 5-minute (or hourly) candle that had finished
  before the fill, so they show what the bot could see. IG's fill is compared against the bands and EMAs. A buy fills
  at the buy price, so its "pips from 8 EMA" and band position include the spread (usually 1.5).
  "Stacked up" = 8 > 13 > 21, "stacked down" = 8 < 13 < 21, anything else "mixed".
- **Spread at entry**: IG's buy minus sell price, taken from the 5-minute candle the fill came in:
  - 33 trades filled within 60 seconds of the candle's open, so the spread is the one at that open;
  - the other 19 filled mid-candle, but the spread was the same at that candle's open and close, so the spread is
    that value.

  `spread_note` says which applies. No live quote at the fill is stored, so a spread change for a few seconds
  mid-candle can't be ruled out. Every trade showed 1.5.
- **Opposite trade open**: any other trade in the opposite direction that was open at the moment of the fill.
- **Day's range**: the high and low of the sell price over the UK day, 00:00–24:00.

## Blank values

- `ig_pnl_gbp` for Fri 20 Nov 19:31 breakout: IG's transaction was not fetched (see above). Pips and £ at £10 are
  filled in from IG's levels.
- `level_ahead` and `pips_to_level_ahead` for seven Mon 16 Nov sells (09:50, 10:50, 14:57, 15:47, 15:50, 16:53,
  20:00): the fill was already below S3, so the classic pivots had no level ahead.
- Two 5-minute candles are missing from the store on the night of Mon 16 Nov (22:55 and 23:00) and one on Fri 20 Nov
  (11:20). The notes column of the trades open at those times says so. MFE and MAE for those trades simply lack
  those candles.

## Summary tables

All 52 trades. "Avg MFE" and "Avg MAE" are means of the per-trade figures, which can understate (see above). The
last two columns separate out Johnny's hand closes, so the bot can be judged on its own exits.

### Results per strategy

| Strategy | Trades | Wins | Losses | Flat | Total pips | Avg MFE | Avg MAE | Closed by Johnny | Pips without Johnny's closes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| level reversal | 14 | 4 | 10 | 0 | -129.4 | 6.5 | 13.7 | 3 | -102.7 |
| EMA pullback | 11 | 0 | 11 | 0 | -117.3 | 4.1 | 10.7 | 2 | -108.0 |
| slow grind | 5 | 1 | 4 | 0 | -54.8 | 3.3 | 13.8 | 0 | -54.8 |
| Bollinger bounce | 8 | 4 | 4 | 0 | -18.6 | 8.3 | 7.8 | 1 | -19.0 |
| breakout | 2 | 0 | 2 | 0 | -18.0 | 8.1 | 9.0 | 0 | -18.0 |
| Bollinger bounce 5m | 3 | 0 | 2 | 1 | -13.7 | 5.4 | 7.7 | 0 | -13.7 |
| Asian range breakout | 3 | 1 | 2 | 0 | -2.3 | 11.6 | 9.0 | 0 | -2.3 |
| range trade | 2 | 1 | 1 | 0 | -0.4 | 6.4 | 7.5 | 0 | -0.4 |
| session sweep | 4 | 4 | 0 | 0 | +42.4 | 20.0 | 9.5 | 0 | +42.4 |
| **All** | 52 | 15 | 36 | 1 | -312.1 | 7.3 | 10.8 | 6 | -276.5 |

### Results per analyser state

| Analyser state | Trades | Wins | Losses | Flat | Total pips | Avg MFE | Avg MAE | Closed by Johnny | Pips without Johnny's closes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| emerging trend down | 18 | 5 | 13 | 0 | -90.8 | 9.5 | 11.2 | 3 | -84.4 |
| trend down, slow grind | 7 | 2 | 5 | 0 | -51.5 | 3.9 | 10.5 | 0 | -51.5 |
| trend up, strong push | 4 | 0 | 4 | 0 | -49.4 | 3.5 | 12.7 | 0 | -49.4 |
| trend up, slow grind | 10 | 4 | 5 | 1 | -43.2 | 7.0 | 8.6 | 0 | -43.2 |
| emerging trend up | 7 | 3 | 4 | 0 | -36.1 | 10.5 | 12.9 | 3 | -6.9 |
| trend down, strong push | 2 | 0 | 2 | 0 | -27.0 | 2.0 | 13.5 | 0 | -27.0 |
| possible reversal up | 1 | 0 | 1 | 0 | -12.0 | 5.3 | 12.0 | 0 | -12.0 |
| possible reversal down | 1 | 0 | 1 | 0 | -1.7 | 2.0 | 6.3 | 0 | -1.7 |
| ranging none | 2 | 1 | 1 | 0 | -0.4 | 6.4 | 7.5 | 0 | -0.4 |
| **All** | 52 | 15 | 36 | 1 | -312.1 | 7.3 | 10.8 | 6 | -276.5 |

### Results per session

| Session | Trades | Wins | Losses | Flat | Total pips | Avg MFE | Avg MAE | Closed by Johnny | Pips without Johnny's closes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| London/NY overlap | 19 | 4 | 14 | 1 | -174.2 | 6.7 | 11.9 | 1 | -148.1 |
| London | 18 | 5 | 13 | 0 | -86.8 | 10.4 | 11.8 | 0 | -86.8 |
| Asian | 3 | 1 | 2 | 0 | -25.8 | 6.2 | 9.9 | 0 | -25.8 |
| New York | 12 | 5 | 7 | 0 | -25.3 | 3.8 | 7.8 | 5 | -15.8 |
| **All** | 52 | 15 | 36 | 1 | -312.1 | 7.3 | 10.8 | 6 | -276.5 |
