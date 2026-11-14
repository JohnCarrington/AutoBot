# The hourly read: replay, 25 October to 13 November 2026

**What was replayed.** The bot's own research replay (`research.long_replay`), on a copy of the bot's IG candle store taken on 14 November (`data/research/replay_stores/live_copy_20261114`), from the week's open on 25 October to 21:55 UK on 13 November. It used the live `.env` switches with TRADING forced off (all six strategies on, the range trade included; stops 12) and the Finnhub history calendar. It ran twice:

- **Current rules:** the committed code before the change (`714d1c6`).
- **With the hourly read:** the committed change (`89b5514`, design 2.9). Trend strategies open nothing while the hourly is ranging, only sell in an hourly sell-off and only buy in an hourly rally. A sell-off or rally starts on an hourly close at least 3 pips beyond the last 12 hourly candles. It turns to ranging after 12 more hourly candles with no new break.

The scripts and both runs are in `data/research/replay/hourly_read_20261114/`.

**Trend days** are 6, 9, 10 and 11 November, as in the earlier reports (`bounce_changes_20261113.md`, `hourly_range_replay_20261113.md`). The bot's own trend-day check (design 2.4) flags none of these days in this span. Pips are per trade, on the bot's own fills.

## Totals

| | Current rules | With the hourly read | Change |
|---|---|---|---|
| All days | 333 trades, 148 won / 185 lost, **+910.4** | 314 trades, 136 / 178, **+521.8** | **−388.6** |
| Trend days (6, 9, 10, 11 Nov) | 74 trades, 47 / 27, +1,325.7 | 70 trades, 41 / 29, +1,074.1 | −251.6 |
| Other days | 259 trades, 101 / 158, −415.3 | 244 trades, 95 / 149, −552.3 | −137.0 |

By strategy (trades, pips), current rules → with the hourly read:

- EMA pullback: 64, +876.2 → 51, +723.8
- Slow grind: 13, +216.1 → 9, +119.0
- Breakout: 15, +177.9 → 4, +90.0
- Bollinger bounce: 111, −98.6 → 120, −144.3
- Level reversal: 75, −177.5 → 75, −183.0
- Range trade: 55, −83.7 → 55, −83.7

By day (pips), current rules → with the hourly read:

| Day | Current | Hourly read | Change |
|---|---:|---:|---:|
| Mon 26 Oct | +80.7 | +90.3 | +9.6 |
| Tue 27 Oct | +34.7 | −39.0 | −73.7 |
| Wed 28 Oct | −102.4 | −102.4 | 0 |
| Thu 29 Oct | −109.1 | −113.8 | −4.7 |
| Fri 30 Oct | −113.9 | −123.9 | −10.0 |
| Mon 2 Nov | −23.0 | −21.2 | +1.8 |
| Tue 3 Nov | −166.3 | −94.8 | +71.5 |
| Wed 4 Nov | +109.6 | +11.6 | −98.0 |
| Thu 5 Nov | −118.3 | −103.3 | +15.0 |
| **Fri 6 Nov (trend)** | +854.1 | +854.1 | 0 |
| **Mon 9 Nov (trend)** | +228.2 | +228.2 | 0 |
| **Tue 10 Nov (trend)** | +80.7 | −43.9 | −124.6 |
| **Wed 11 Nov (trend)** | +162.7 | +35.6 | −127.0 |
| Thu 12 Nov | −43.2 | −88.1 | −44.9 |
| Fri 13 Nov | +36.0 | +32.2 | −3.7 |

## Every trend-day trade that changes

Nothing changes on 6 or 9 November: every trend trade on those days was with the hourly read.

| Entry (UK) | Trade | Current | Hourly read | Why |
|---|---|---:|---:|---|
| Tue 10 Nov 09:10 | breakout sell | +50.0 (take profit) | not opened | Hourly ranging, range 13425.8 to 13458.6. Monday evening's rally had turned to ranging at 08:00 (12 hourly candles with no new break of 3 pips or more). |
| Tue 10 Nov 13:30 | slow grind sell | +100.0 (take profit) | not opened | Hourly ranging, range 13420.2 to 13458.6. The 09:00 candle closed only 0.1 pips below the 12-candle low, short of 3, so the sell-off started only at the 13:00 candle's close, at 14:00. |
| Tue 10 Nov 14:30 | slow grind sell | not opened | +41.1 (20:30 close) | Knock-on: the 13:30 slow grind wasn't open, so this one could open, now in the hourly sell-off. |
| Tue 10 Nov 17:00 | Bollinger bounce buy | +15.7 (20:30 close) | not opened | Knock-on: refused by the pace and target rule against the 14:30 slow grind sell that was now open. |
| Wed 11 Nov 07:30 | EMA pullback sell | +30.0 (take profit) | not opened | Hourly ranging, range 13327.5 to 13355.7. Tuesday's sell-off had run 12 hours without a new break. |
| Wed 11 Nov 08:10 | slow grind sell | +10.0 | not opened | Hourly ranging, as above. |
| Wed 11 Nov 08:15 | EMA pullback sell | +30.0 (take profit) | not opened | Hourly ranging, as above. |
| Wed 11 Nov 08:35 | Bollinger bounce buy | not opened | −12.0 (stopped) | Knock-on: no trend sells were open, so the pace and target rule no longer refused it. |
| Wed 11 Nov 09:05 | slow grind sell | not opened | −15.0 (stopped) | Knock-on: the slow grind's one-at-a-time slot was free. Allowed: the 08:00 candle closed 4.0 pips below the 12-candle low, so the read was a sell-off. |

## Other days, in short

- **The biggest gain, Tue 3 Nov (+71.5):** the read was ranging all day (range about 13396 to 13432). It blocked three breakout buys and two EMA pullback buys that were all stopped at −12, plus a breakout sell at −6.9.
- **The biggest losses:**
  - **Wed 4 Nov (−98.0):** the 01:00 EMA pullback buys (+30, +30) and slow grind buy (+20) were blocked. The read was still ranging: Wednesday's rally began only at the 01:00 candle's close.
  - **Tue 27 Oct (−73.7):** blocked: the 07:00 breakout sell (+50) and the 19:55 EMA pullback sell (+30). Also blocked: the 16:15 EMA pullback sell (−12). Three bounce buys were added (−5.7 between them).
  - **Thu 12 Nov (−44.9):** blocked the 11:30 breakout sell (+50) and the 10:20 breakout buy (−12), inside the morning range 13249 to 13282.
- **Fri 13 Nov (−3.7):** with the current code the trend strategies opened nothing inside the box anyway. The two Thursday evening EMA pullback sells (19:00 and 23:45, −12 each) still opened, because the read was a sell-off then (Thursday's 14:00 and 15:00 closes broke below the 12-candle low). The 12:50 breakout sell was blocked by the hourly range but had not opened under the current rules either. Three bounce buys were added (11:00 +3.8, 12:35 −12.0, 13:05 +4.5), a knock-on: under the current rules, the pace and target rule refused them against Thursday's 11:30 breakout sell, which was still open.

## Limits

- Three weeks, 333 trades, and the change rests on a handful of take profits.
- On the trend days, the read was ranging in the hours just before 10 and 11 November's moves took off. The losses there are trades the old rules caught early.
