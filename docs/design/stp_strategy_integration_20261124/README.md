# 24 November 2026 fixtures (recorded data, unmodified copies)

- `m5_r1_window.csv`: 5-minute candles 13:30 to 18:35 UTC, copied as stored from `data/candles/GBPUSD/5m/2026-11-24.csv` (store format: price x 10000, buy and sell OHLC).
- `h1_2026-11-24.csv`: the hourly candles, copied as stored from `data/candles/GBPUSD/1h/2026-11-24.csv`.
- `rejection_replay_today.txt`: `python -m rejection 2026-11-24T00:00:00Z 2026-11-24T18:30:00Z --pair GBPUSD` at 63d9c04. This is a CODE REPLAY over the stored candles, not a live record; the live watcher stores no events.

STP records (`recommendations.jsonl`, `issued.jsonl`, `technical.jsonl`) stay in `data/planner/GBPUSD/` and are read as-of by the tests.

## Added for revision 3.1 and the readiness assessment (offline, read-only on the candle store and records)

| File | What |
|---|---|
| `bidir.py` | STP's approved `assess()` run per direction for each hour of 24 Nov (OD-16 A, OD-17 A): the H4 direction and condition are recorded as context and do not gate. Run from `/opt/autobot` with `PYTHONPATH=/opt/autobot`. It reproduces every SELL zone STP actually issued that day. |
| `bidir_20261124.json` | Its output: one proposal (or the reason for none) per hour per direction |
| `ideas_vs_opps.py`, `ideas_vs_opps_output.txt` | Each gated-strategy idea of 24 Nov against the opportunities the design would hold at that moment (interaction approximated over the 30 minutes before the idea; exact pierce candle in WP-6) |
| `multi_level.py`, `multi_level_output.txt` | The strategies' watcher with three `stp_zone` levels in one zone: setups and triggers from one rejection (readiness §4) |

No profit or loss is computed anywhere. These are behaviour checks only.
