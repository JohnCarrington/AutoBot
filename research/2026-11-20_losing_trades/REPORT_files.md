## Files in this folder

- `reconcile.py`: matches every live trade (records + journal) to IG's records in `data/orders/ig_check_result*.json`; writes `trades.csv`.
- `trades.csv`: one row per live trade since 9 Nov, with the bot's and IG's figures side by side.
- `tables.py`, `stats.py`, `assemble.py`: the Step 1 and Step 2 tables and this report.
- `replay_live_code.py`: the Step 4 replay through an exact copy of 02f6c7e, in paper mode (it never contacts IG and writes no live file).
- `replay_week_16_20.json`, `replay_week_09_13.json`, `replay_restart_19nov1844.json`, `replay_d9e5d0e_19nov.json`: the replays' paper trades and paper safety refusals.
- `week_paths.py`, `week_paths.csv`, `week_review.py`: the week review (what price did after each entry, and the one-line verdicts).

IG was read twice in this investigation (18:43 and 18:53 UTC), and an earlier session had read it at 16:12. All
three reads went through the price service's read-only check, and their results are kept as
`data/orders/ig_check_result.2026-11-20_*.json`.
