# 24 November 2026 fixtures (recorded data, unmodified copies)

- `m5_r1_window.csv`: 5-minute candles 13:30 to 18:35 UTC, copied as stored from `data/candles/GBPUSD/5m/2026-11-24.csv` (store format: price x 10000, buy and sell OHLC).
- `h1_2026-11-24.csv`: the hourly candles, copied as stored from `data/candles/GBPUSD/1h/2026-11-24.csv`.
- `rejection_replay_today.txt`: `python -m rejection 2026-11-24T00:00:00Z 2026-11-24T18:30:00Z --pair GBPUSD` at 63d9c04. This is a CODE REPLAY over the stored candles, not a live record; the live watcher stores no events.

STP records (`recommendations.jsonl`, `issued.jsonl`, `technical.jsonl`) stay in `data/planner/GBPUSD/` and are read as-of by the tests.
