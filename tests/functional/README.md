# tests/functional

Tests that check the bot behaves the way a trader expects (for example, "no new trade 10 minutes before big news"). Added as each part is built. They use real past days, with the real stored candles where needed.

- `test_levels_real_candles.py`: 6 November's pivots, the turning low at about 1.3380 from 30 October, and 5 November's stop at 1.3446 to 1.3450 (`docs/LEVELS.md`).
