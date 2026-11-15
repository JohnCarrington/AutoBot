# Why both shapes lost in 2024 but made money in 2025 and 2026 (15 November 2026)

**Status: research only. Nothing in the bot or on AutoBot 161 was changed. Waiting for the owner.**

## In short

- **Nothing seen at the time of the signal separates 2024's losing trades from the winners of 2025–26.**
  - At the signal, the day's range, the hourly band's width, the time of day, the hourly read and the move since 07:00 all look almost the same in both groups.
  - The years themselves don't differ in those conditions either: 2024 and 2026 had nearly identical volatility at the signals, with opposite results.
- **No condition found on 2024 held up on 2025 and 2026.** Each of the ten best cut-offs on 2024 cost pips in 2025, in 2026, or for one of the two shapes. Two more ideas measured over weeks (Claude's: the market's trendiness over the last 20 days, and the signal's own recent record) failed the same check.
- **The likeliest answer is that 2024 isn't the odd year, 2026 is.**
  - 2024 (−143.2 on 176 trades) and 2025 (+69.0 on 149) are both within ordinary luck of zero.
  - 2025 also had 7 losing months out of 12.
  - 2026 (+336.2 on 82 trades) stands out, and 2026 is the data the hourly-read and times filters were chosen on (its first half).
  - Over 2024–25, which were not used to pick anything, the two shapes together come to **−74.2 on 325 trades**: no edge.
- **Claude's suggestion:** treat these shapes, with these filters, as **not yet shown to have an edge**. The 2026 result is most likely flattered by being where the filters were found. Ways forward are at the end.

## What was compared

- **Trades:** both shapes from `hourly_shape_vs_d_20261115.md`, with the filters and exit unchanged:
  - **Owner's shape (E):** pierce of the hourly band by more than 3 pips, a reversal candle, a confirmation close beyond it, entry at the next open.
  - **D:** Claude's.

  Both use the hourly read (ranging only), the owner's times within 60 minutes, the trail and a 12-pip stop. That gives 2024: 176 trades (−143.2); 2025: 149 (+69.0); 2026: 82 (+336.2). The trades are exactly those of that write-up, checked.
- **Data:** as before. 2026 is IG's own mid from 161's archive (118 complete weekdays). 2024–25 is built from the vendor's ticks the same way (517 complete weekdays). Both charge IG's typical spread.
- **Facts recorded for each trade, all as known at the entry:**
  - **day range:** the day's high minus low so far (from UK midnight);
  - **move7:** the move since 07:00 UK, + when the trade fades it;
  - **band_w:** the hourly band's width;
  - **hourly_range:** the hourly read's 12-hour range;
  - **ranging_hours:** how long the hourly read has been ranging;
  - **yday_range:** yesterday's full range;
  - **avg_hour_range:** the average hourly range over the last 20 hours;
  - the time window, the weekday and the side.

## 2024's losers next to 2025–26's winners

```
quartiles (25% / median / 75%)        2024 losers          2024 winners         2025-26 winners      2025-26 losers
  day_range            33.3   43.2   53.4     36.1   42.5   53.4     38.4   44.0   52.0     39.1   49.0   61.6
  move7                12.1   19.1   31.6     16.9   24.6   30.0     13.0   20.3   32.5     16.4   24.7   34.8
  band_w               26.4   34.6   42.5     28.1   35.9   45.0     30.1   37.4   46.6     30.6   39.6   49.3
  hourly_range         26.2   35.0   41.8     29.7   34.6   43.8     29.4   37.2   43.2     32.4   39.8   46.9
  ranging_hours        20.0   24.2   28.8     19.2   23.9   29.2     20.2   24.3   45.8     20.4   23.5   42.5
  yday_range           49.3   74.6   90.8     49.1   61.3   73.8     56.3   68.8   92.6     57.7   77.1   96.4
  avg_hour_range        9.4   11.6   14.4      9.5   11.4   13.1     11.2   12.9   14.5     11.4   13.0   15.1
  counts: 103 73 121 110
window | 2024 losers [(10, 29), (14, 49), (16, 25)] | 2025-26 winners [(10, 44), (14, 50), (16, 27)]
hour | 2024 losers [(9, 18), (10, 11), (13, 25), (14, 24), (15, 15), (16, 10)] | 2025-26 winners [(9, 25), (10, 19), (13, 28), (14, 21), (15, 24), (16, 4)]
weekday | 2024 losers [(0, 18), (1, 24), (2, 29), (3, 22), (4, 10)] | 2025-26 winners [(0, 18), (1, 29), (2, 23), (3, 30), (4, 21)]
side | 2024 losers [('buy', 50), ('sell', 53)] | 2025-26 winners [('buy', 72), ('sell', 49)]

by year: trades, win rate, pips, and the median day range / band width / hourly range at the signals
2024 176 41% -143.2 | day range 43.2 band 35.3 hourly range 34.6 avg hour 11.5 move7 20.8
2025 149 50% 69.0 | day range 47.3 band 40.0 hourly range 39.8 avg hour 13.5 move7 24.3
2026 82 57% 336.2 | day range 41.5 band 34.8 hourly range 34.6 avg hour 11.4 move7 20.4

day_range: pips (trades) by year
      0-30     -145.4 ( 21,  19%)      +6.8 (  1, 100%)     +42.9 ( 16,  50%)
     30-45     +109.9 ( 77,  45%)    +236.2 ( 55,  60%)    +172.6 ( 36,  61%)
     45-60      -81.2 ( 48,  44%)     -86.6 ( 55,  49%)     +64.9 ( 17,  59%)
     60-80      -61.2 ( 24,  38%)      +0.2 ( 21,  48%)     +33.3 ( 12,  50%)
     80-999     +34.7 (  6,  67%)     -87.6 ( 17,  18%)     +22.5 (  1, 100%)

band_w: pips (trades) by year
      0-20      -72.0 (  6,   0%)      +0.0 (  0,   0%)     +33.5 (  5,  40%)
     20-30      +79.2 ( 59,  42%)     +95.7 ( 27,  59%)    +108.4 ( 19,  58%)
     30-40     -115.9 ( 49,  41%)     -61.9 ( 48,  48%)      +0.5 ( 32,  56%)
     40-60      -35.8 ( 57,  44%)     +78.3 ( 53,  53%)    +177.3 ( 22,  64%)
     60-999      +1.3 (  5,  60%)     -43.1 ( 21,  33%)     +16.5 (  4,  50%)

hourly_range: pips (trades) by year
      0-20       +8.1 (  4,  50%)      +0.0 (  0,   0%)     -14.4 (  6,  33%)
     20-30     -160.9 ( 52,  35%)    +112.1 ( 20,  60%)    +158.3 ( 25,  72%)
     30-40     +119.4 ( 64,  45%)      -7.4 ( 58,  50%)    +105.3 ( 29,  62%)
     40-60      -61.5 ( 47,  45%)      +4.5 ( 59,  49%)     +82.5 ( 17,  41%)
     60-999     -48.3 (  9,  33%)     -40.2 ( 12,  33%)      +4.5 (  5,  40%)

move7: pips (trades) by year
   -999--20      +0.0 (  0,   0%)      -9.6 (  2,  50%)      +0.0 (  0,   0%)
    -20-0       -38.8 (  6,  33%)     -24.6 (  3,   0%)    +117.2 (  4,  75%)
      0-20     -140.0 ( 74,  34%)    +190.1 ( 51,  61%)    +240.9 ( 35,  63%)
     20-40       +2.1 ( 76,  49%)     -50.7 ( 67,  48%)     -94.5 ( 34,  47%)
     40-999     +33.5 ( 20,  45%)     -36.2 ( 26,  38%)     +72.6 (  9,  67%)

ranging_hours: pips (trades) by year
     -1-2        +0.0 (  0,   0%)      +0.0 (  0,   0%)      +0.0 (  0,   0%)
      2-6        +0.0 (  0,   0%)      +0.0 (  0,   0%)      +0.0 (  0,   0%)
      6-12       +0.0 (  0,   0%)      +0.0 (  0,   0%)      +0.0 (  0,   0%)
     12-999    -143.2 (176,  41%)     +69.0 (149,  50%)    +336.2 ( 82,  57%)

avg_hour_range: pips (trades) by year
      0-6        +0.0 (  0,   0%)      +0.0 (  0,   0%)      +0.0 (  0,   0%)
      6-8       -88.6 (  9,  11%)      +0.0 (  0,   0%)     -15.9 ( 11,  45%)
      8-10      -50.2 ( 48,  40%)      +8.0 (  1, 100%)     +71.8 ( 15,  67%)
     10-14     +187.2 ( 79,  52%)     +14.4 ( 90,  49%)    +122.7 ( 37,  57%)
     14-999    -191.6 ( 40,  30%)     +46.6 ( 58,  50%)    +157.6 ( 19,  58%)

yday_range: pips (trades) by year
      0-50      -13.1 ( 54,  48%)     +48.2 ( 14,  64%)     +34.3 ( 21,  57%)
     50-70      +89.9 ( 45,  58%)     +66.6 ( 40,  58%)    +221.7 ( 32,  59%)
     70-90     -175.9 ( 37,  27%)     -69.9 ( 40,  42%)    +100.7 ( 15,  60%)
     90-120    -160.9 ( 27,  26%)     -49.7 ( 35,  46%)     -51.4 (  7,  29%)
    120-999    +116.8 ( 13,  31%)     +73.8 ( 20,  45%)     +30.9 (  7,  71%)

window: pips (trades) by year
      9-11      -44.8 ( 52,  44%)    +129.4 ( 51,  59%)    +123.8 ( 22,  64%)
     11-13       +0.0 (  0,   0%)      +0.0 (  0,   0%)      +0.0 (  0,   0%)
     13-15      +44.9 ( 86,  43%)     -10.6 ( 56,  45%)    +150.2 ( 47,  53%)
     15-17     -143.3 ( 38,  34%)     -49.8 ( 42,  45%)     +62.2 ( 13,  62%)
```

**How to read it:**
- **Quartiles:** the first block shows the facts' 25%, median and 75% for each group. The groups overlap almost completely.
- **By year:** the year block shows that the signals' conditions (median day range, band width, hourly range, move since 07:00) were nearly the same in 2024 and 2026.
- **Buckets lean against 2024 in places:**
  - after a 70–120 pip day;
  - the 16:00 window;
  - a quiet last 20 hours.

  But in each case 2025 or 2026 points the other way.

## A condition found on 2024 and checked on 2025 and 2026 (Claude's suggestions)

- **What was tried:** keep a trade only if one fact is below, or at or above, a cut-off.
- **Picking on 2024:** the condition had to keep at least 40% of 2024's trades, and was chosen by its 2024 pips with both shapes together.
- **Counting:** it counts only if it also adds pips in 2025 and 2026 for each shape.

```
base: {'2024 E': (56, -50.6), '2024 D': (120, -92.6), '2025 E': (55, 37.3), '2025 D': (94, 31.7), '2026 E': (27, 93.7), '2026 D': (55, 242.5)}

the 10 best conditions on 2024 (both shapes), and what they do in 2025 and 2026 (change against no condition)
{'rule': 'yday_range below 70', '2024': (99, 76.8), '2025 E': (22, 9.7, -27.6), '2025 D': (32, 105.1, 73.4), '2026 E': (18, 76.3, -17.4), '2026 D': (35, 179.7, -62.8), 'works later': False}
{'rule': 'ranging_hours below 24', '2024': (85, 54.5), '2025 E': (23, -102.8, -140.1), '2025 D': (44, -18.3, -50.0), '2026 E': (18, 100.6, 6.9), '2026 D': (34, 286.9, 44.4), 'works later': False}
{'rule': 'hourly_range below 35', '2024': (89, 49.3), '2025 E': (19, 42.3, 5.0), '2025 D': (26, 72.6, 40.9), '2026 E': (14, 19.0, -74.7), '2026 D': (27, 136.5, -106.0), 'works later': False}
{'rule': 'avg_hour_range below 14', '2024': (136, 48.4), '2025 E': (35, -21.2, -58.5), '2025 D': (56, 43.6, 11.9), '2026 E': (22, 24.9, -68.8), '2026 D': (41, 153.7, -88.8), 'works later': False}
{'rule': 'avg_hour_range below 12', '2024': (101, 40.8), '2025 E': (13, -44.7, -82.0), '2025 D': (21, 8.5, -23.2), '2026 E': (16, 33.4, -60.3), '2026 D': (28, 144.3, -98.2), 'works later': False}
{'rule': 'move7 at or above 20', '2024': (96, 35.6), '2025 E': (27, -28.0, -65.3), '2025 D': (66, -58.9, -90.6), '2026 E': (8, -38.2, -131.9), '2026 D': (35, 16.3, -226.2), 'works later': False}
{'rule': 'avg_hour_range at or above 11', '2024': (106, 12.2), '2025 E': (53, 61.3, 24.0), '2025 D': (91, 47.7, 16.0), '2026 E': (13, 50.8, -42.9), '2026 D': (34, 72.1, -170.4), 'works later': False}
{'rule': 'hourly_range at or above 30', '2024': (120, 9.6), '2025 E': (45, -27.6, -64.9), '2025 D': (84, -15.5, -47.2), '2026 E': (15, 91.9, -1.8), '2026 D': (36, 100.4, -142.1), 'works later': False}
{'rule': 'move7 at or above 25', '2024': (75, 3.3), '2025 E': (18, 1.7, -35.6), '2025 D': (50, -62.7, -94.4), '2026 E': (5, -24.5, -118.2), '2026 D': (27, 50.5, -192.0), 'works later': False}
{'rule': 'day_range at or above 30', '2024': (155, 2.2), '2025 E': (55, 37.3, 0.0), '2025 D': (93, 24.9, -6.8), '2026 E': (19, 115.7, 22.0), '2026 D': (47, 177.6, -64.9), 'works later': False}
```

**None works later.** The best on 2024, "yesterday's range below 70 pips", turns 2024 into +76.8, but costs the owner's shape 27.6 pips in 2025 and D 62.8 in 2026.

### Measured over weeks (Claude's suggestions)

**The market's trendiness over the last 20 days** (efficiency ratio: the net move of the last 20 daily closes divided by the sum of their daily moves). Month by month, with the median ratio at the signals:

```
month: trades, pips, median ER20
  2024-01  19   -30.5  ER 0.03
  2024-02  11  +152.1  ER 0.12
  2024-03   3   +12.9  ER 0.46
  2024-04  17   -17.9  ER 0.17
  2024-05  13    -8.6  ER 0.43
  2024-06  12    +7.3  ER 0.14
  2024-07  20   -20.2  ER 0.16
  2024-08  20   -94.5  ER 0.15
  2024-09   9   -34.3  ER 0.47
  2024-10  17  -114.2  ER 0.02
  2024-11  14   -44.3  ER 0.28
  2024-12  21   +49.0  ER 0.13
  2025-01  12   -19.9  ER 0.22
  2025-02   9   -28.7  ER 0.28
  2025-03   5   +20.1  ER 0.50
  2025-04   1   -12.0  ER 0.18
  2025-05   4   +63.2  ER 0.47
  2025-06  13   -23.5  ER 0.23
  2025-07  12   -31.8  ER 0.37
  2025-08  16   -11.7  ER 0.35
  2025-09  22   +31.1  ER 0.06
  2025-10  18   -15.9  ER 0.07
  2025-11  17   +47.0  ER 0.32
  2025-12  20   +51.1  ER 0.43
  2026-03   2    +6.0  ER 0.18
  2026-04   1   -12.0  ER 0.38
  2026-05   7   +14.7  ER 0.17
  2026-06  29  +111.4  ER 0.34
  2026-07   7   +60.7  ER 0.28
  2026-08  20   +25.1  ER 0.29
  2026-09  10   +50.7  ER 0.14
  2026-10   6   +79.6  ER 0.09
```

2024's worst months (August −94.5, October −114.2) had low ratios, a sideways market, and so did good months elsewhere (February 2024, September 2025, October 2026). Keeping trades only below a cut-off:

```
ER20 cut-offs (keep a trade only if ER20 is below the cut-off): pips by year and shape
  < 0.15: 2024E  25   +52.1 | 2024D  46   -65.3 | 2025E  19    -1.6 | 2025D  32  +127.0 | 2026E   8   +50.3 | 2026D  18  +101.0
  < 0.20: 2024E  28   +43.3 | 2024D  57  -103.9 | 2025E  23   -49.6 | 2025D  43   +74.6 | 2026E  10   +26.3 | 2026D  24   +97.2
  < 0.25: 2024E  32   +17.5 | 2024D  70   -95.8 | 2025E  28   -68.9 | 2025D  50   +87.4 | 2026E  10   +26.3 | 2026D  24   +97.2
  < 0.30: 2024E  36    -6.6 | 2024D  76   -26.4 | 2025E  33   -26.5 | 2025D  56   +86.8 | 2026E  15   +58.4 | 2026D  32  +171.0
  < 0.35: 2024E  42   +10.5 | 2024D  90   -82.1 | 2025E  37    +4.9 | 2025D  64   +86.0 | 2026E  17   +34.4 | 2026D  36  +217.0
  < 0.40: 2024E  44   -13.5 | 2024D  95   -97.3 | 2025E  46   -52.5 | 2025D  78   +13.1 | 2026E  22   +62.0 | 2026D  47  +222.8
  < 1.01: 2024E  52   -28.8 | 2024D 108   -54.7 | 2025E  55   +37.3 | 2025D  94   +31.7 | 2026E  27   +93.7 | 2026D  55  +242.5
```

No cut-off helps all three years for both shapes.

**The signal's own recent record:** trade only while the last N signals, counted as if all were traded and **only those already closed at the time**, are in profit.

```
own record: trade only if the last N signals (as if all traded) made money in total
  N= 5: 2024E  21  +111.5 | 2025E  20    +2.0 | 2024D  57   -72.1 | 2025D  46   +17.2 | 2026E  11   +61.5 | 2026D  28   +88.7
  N=10: 2024E  23   +98.0 | 2025E  25   -29.9 | 2024D  62  -114.8 | 2025D  51   -66.0 | 2026E  10   +26.3 | 2026D  31  +119.7
  N=20: 2024E  17    -4.4 | 2025E  32   -45.8 | 2024D  57   -31.1 | 2025D  58   -15.4 | 2026E   8   +46.5 | 2026D  27  +129.1
```

With N = 5 (the best on 2024) it turns the owner's shape positive in 2024 (+111.5 against −50.6). D improves a little but stays negative (−72.1 against −92.6). It costs pips for both shapes in 2025 and 2026. A first version counted signals that hadn't closed yet. That lookahead made it look good, and it was fixed before these results.

## Is 2024 different at all?

```
2024                                     trades  176  total  -143.2  per trade -0.81  spread per trade 15.8  total's usual luck +-  209  t -0.68
2025                                     trades  149  total   +69.0  per trade +0.46  spread per trade 14.5  total's usual luck +-  177  t +0.39
2026                                     trades   82  total  +336.2  per trade +4.10  spread per trade 18.2  total's usual luck +-  164  t +2.05
2024-25 (not used to pick the filters)   trades  325  total   -74.2  per trade -0.23  spread per trade 15.2  total's usual luck +-  274  t -0.27
all three years                          trades  407  total  +262.0  per trade +0.64  spread per trade 16.0  total's usual luck +-  322  t +0.81
2024 losing months 8 of 12
2025 losing months 7 of 12
2026 losing months 1 of 8
```

- **"Total's usual luck"** is how far a year's total typically moves by chance alone, given how much single trades vary (about 15 pips per trade): one standard deviation.
- **2024 and 2025:** −143 is within the usual ±209, and +69 within ±177. Both are consistent with no edge, and the gap between them is within luck too.
- **2026:** +336 is about two standard deviations above zero, and it's the year the filters were picked on (the first half, 23 March to 30 June; the second half also held up).
- **Over the two years not used for picking** (2024–25): −0.23 pips a trade.

## What Claude suggests

1. **Don't build on the 2026 result alone.** Over three years, the hourly-read and times filters on these shapes look like no edge, with 2026 the lucky stretch where they were found.
2. **A cleaner test would set the rules before looking at the days they're tested on.** For example, pick on 2024, check on 2025, then look at 2026 last, with the rules fixed in advance.
3. **More of IG's own prices would settle the data question.** 2024–25 is the vendor's data, and the owner's shape depends on candle closes, where the vendor matched IG's candle colour 92% of the time on the one week checked. The bot's live candles will add IG's own days from here on. A paper or demo run of a shape forward in time is the cleanest test there is.
4. **If the owner wants a filter to look into further,** the facts to look at are those whose buckets leaned the same way in two of the three years:
   - yesterday's range of 70 to 120 pips (worse in 2024 and 2025);
   - the 16:00 window (worse in 2024 and 2025).

   Neither passed the check, so they are leads, not rules.

## Files

`data/research/year_regime_20261115/` (not in git):
- `feats.py` and `trades.pkl`: every trade with its facts;
- `compare.py` and `compare.txt`;
- `search.py`, `search.txt` and `search.json`;
- `regime.py`, `regime.txt` and `regime_own.txt`;
- `noise.txt`.
