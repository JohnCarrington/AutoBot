# tests/functional

Tests that check the bot behaves the way a trader expects (for example, "no new trade 10 minutes before big news"). Added as each part is built. They use real past days, with the real stored candles where needed.

- `test_levels_real_candles.py`: 6 November's pivots, the turning low at about 1.3380 from 30 October, and 5 November's stop at 1.3446 to 1.3450 (`docs/LEVELS.md`).
- `test_rejection_real_candles.py`: the rejection at the daily pivot around midnight on 5 November, and the turn at 1.3446 to 1.3450 around 12:00 (`docs/REJECTION.md`).
- `test_analyser_real_candles.py`: the direction is sell side at 13:00 on 6 November, and the 5-minute 100 EMA, pivot and direction at 06:00, 09:00, 13:00 and 16:00 that day (`docs/ANALYSER.md`).
- `test_market_states_real_candles.py`: the five market states on 5 and 6 November: the midnight pivot rejection starting the downtrend, consolidation before 06:40, the two strong pushes, the possible reversal around 10:15, sell side at 13:00, and a restart at 09:00 giving exactly the same states (`docs/ANALYSER.md`). The S2 flat spell (11:30 to 12:45) is a known shortfall, not tested (design section 12).
