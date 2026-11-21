# EMA pullback on the IG demo account, 9-20 November 2026: how it really behaved

Read-only investigation for Johnny, 21 Nov 2026. Nothing in the bot was changed, restarted or sent to IG. The sources are the bot's own records:
- `data/records/GBPUSD/trades.jsonl` and `decisions.jsonl`;
- `data/orders/GBPUSD/orders.jsonl`;
- IG's activity and transactions already saved by the bot's read-only IG checks (`data/orders/ig_check_result*.json`);
- the stored candles (`data/candles/GBPUSD`);
- the stored news calendar (`data/news/calendar.json`);
- `logs/prices.log*`;
- `git reflog`.

Everything was worked out with the bot's own code, from an exact `git archive` copy of the checked-out commit. Its EMA pullback, indicator, level and news code is identical to `02f6c7e`, the code the running service loaded. Code is quoted from `02f6c7e`.

The scripts are `build.py` (writes `results.json`) and `report.py` (writes this report's detail and the CSVs). The full lists are in `trades.csv`, `setups.csv` and `blocked.csv`. UK time = GMT = UTC in November.

The week ended Friday 20 Nov 22:00, so "up to now" means up to then.

## Summary

**The trades.** There were 24 EMA pullback trades. Johnny closed 2 by hand (−9.3 pips); they are kept apart. The bot's own 22 exits: 3 won, 19 lost, −138.0 pips. Every exit was IG's 12-pip stop or IG's take profit.

The code changed twice, so the results are split into three periods:

| Period | Code | Bot's own exits |
|---|---|---|
| A, 9–13 Nov 10:22 | first build: hourly slope checked by size only | 12 trades, 3 won, −18.0 pips |
| B, 13 Nov 10:22–19 Nov 18:44 | slope must point the trade's way, plus later gates | 10 trades, 0 won, −120.0 pips |
| C, from 19 Nov 18:44 | first-build-plus: slope by size only again | none (only the 2 owner closes) |

**1. Hourly slope direction.**
- **The problem never happened.** No trade had any of the three hourly EMAs' 3-hour slopes pointing against it, either as the bot read it or as it really was at the touch. Only 4 of the 483 setups had one (sells on 20 Nov, 09:10–09:30). None reached its entry.
- **Something the records showed instead:** from 9 Nov to 11 Nov 14:56, the live bot judged the hourly trend from hourly candles as stored at its last start. For example, the 10 Nov buys used the 9 Nov 11:00 hourly candle. This affected 7 trades and was fixed by `04b3a83`.

**2. Several trades at once.** This happened 4 times and involved 13 of the 24 trades. At most 3 were open together, always going the same way:

| When | Trades | Result |
|---|---|---|
| 10 Nov | 3 buys | −36.0 |
| 11 Nov morning | 3 sells | +90.0 |
| 11 Nov evening | 2 sells | −24.0 |
| 16 Nov | 5 sells, at most 2 at once | −60.0 |

**3. Big news.**
- No trade opened from 15 minutes before to 30 minutes after a big release.
- 1 trade was open when one came out: trade 15, through GBP Unemployment Rate on 17 Nov 07:00. It was stopped at 09:48 for −12.0. One trade is too few to say anything.

**4. Hours and overnight.**
- 5 trades opened outside 06:00–20:30 UK. All 5 lost 12.0, all in period A.
- 3 trades were held past 20:30 UK. All 3 lost 12.0.
- 5 trades were stopped between 22:00:00 and 22:04:53, the IG rollover. Spreads in the stored 22:00 candles were 7.3 to 16.9 pips.
- Trade 11 opened at 22:00:03 with an offer 16.9 above the bid and was stopped the same second. That was before the 21:55–22:15 no-trade window was added on 13 Nov.

**5. Slippage and stale prices.** The code checks neither.
- Against the setup's entry, IG's fill was between 1.8 pips worse and 0.3 pips better. The largest gaps are buys, and they include the spread, because the entry is on the bid.
- Against the same side of the live price that triggered it, the fill was between 0.9 pips worse and 0.4 pips better.
- The price was 0 to 3 seconds old (IG's own time stamp) when the order went out.

**The direction rule.**
- The bot applies it only when a setup reaches its entry price. Setups that never get there are never checked or logged, so all 483 setups were rebuilt from the candles with the bot's own code. The rebuild matches every logged idea and every trade.
- 85 setups reached their entry while the service was live: 24 traded, 14 were allowed but not sent (another one had already gone that candle), and 47 were blocked.
- Of the 47 blocked: the analyser state blocked 40 (30 on its own). The pivot blocked 2 and the 100 EMA blocked 1, never on their own. Period B's extra gates (hourly read, TREND_STILL_GOING, ANALYSER_GOVERNS_ALL) blocked 15 (7 on their own).
- Trades by state at the open: emerging trend, 11 trades, 0 won, −132.0; trend, 11 trades, 3 won, −6.0.
- **LOOK BACK, not live results:** from the entry, 17 blocked setups would have reached +30 first, 27 would have hit −12 first, 1 reached neither, and 2 could not have opened.
- Blocked setups came at all hours. 26 of the 47 were between 16:00 and 23:59 UK. The pivot blocked only 2, both buys at night, so the record can't show whether it blocks early in trend days.

**Wick past the 21 EMA.** 54 of the 86 setups that reached their entry had a candle wick beyond the 21 EMA without closing beyond it. Among the bot's 22 trades:
- with a wick: 15 trades, 2 won, −96.0;
- without: 7 trades, 1 won, −42.0.

The largest wick on a trade was 2.5 pips. With 22 trades and 3 winners, this is too small a sample to say whether wicks matter. The full list sorted by distance is in 3.4, with no cut-off.

