# Currency pairs

The bot works for any currency pair. Only **GBPUSD** is switched on.

## How a part knows its pair

Every part works on **one pair, given to it**: `settings.for_pair("GBPUSD")` (`config/pairs.py`). That gives the same settings plus the pair's own:

| | GBPUSD |
| --- | --- |
| `market.pair`, `market.epic` | `GBPUSD`, `CS.D.GBPUSD.TODAY.IP` |
| `market.pip_size` | 0.0001 (a JPY pair: 0.01) |
| `market.price_scale` | 10000: IG's `13354.4` is 1.33544 |
| `market.points_per_pip` | pip size x price scale = 1 point |
| `candles.folder` | `/opt/autobot/data/candles/GBPUSD/` (candles and `gaps.csv`) |
| `levels.folder` | `/opt/autobot/data/levels/GBPUSD/` (`current.json`) |
| `history.pair_folder` | `/opt/autobot/data/history/GBPUSD/` (this pair's one-off fill records) |

The plain settings have no `market` at all, so nothing can run without being told its pair. Every part that is given a candle store (the price feed, the levels and their updater, the rejection replay, the analyser, the history fill) checks the store is the pair's own (its folder is named after the pair). If not, it stops at once with "Pair mix-up".

## What is shared by all pairs

- **One IG login and one price stream connection.** The price service subscribes to each switched-on pair's tick and 5-minute items on the same connection. Each update carries its epic and goes to that pair's feed and store only.
- **One history door** (`ig/history.py`): IG's history allowance belongs to the account, so the weekly budget (`history.weekly_budget_points`), IG's allowance floor and the block marker are shared. Each request records its epic in the ledger. These files stay in `/opt/autobot/data/history/`.
- **Market hours** (`[market_hours]`): the same for every currency pair.

## Switching a new pair on

1. Find its epic with the one market search: `.venv/bin/python -m ig.find_market EURUSD`.
2. Add `[pairs.EURUSD]` to `config/settings.toml` (epic, pip size, price scale, checked against IG's prices) and a row of evidence for it.
3. Add it to `PAIRS_ON` in `.env` (for example `PAIRS_ON=GBPUSD,EURUSD`) and restart the price service.
4. The new pair starts with an **empty store**. It is **never filled from IG's history automatically**. Its one-off fill needs Johnny's go-ahead: `.venv/bin/python -m prices.history_fill plan --pair EURUSD` shows the plan (contacts nobody); `... go --pair EURUSD` runs it, once, against the shared budget.

## Command-line tools

`levels`, `rejection`, `analyser` and `prices.run` take `--pair`. It can be left out while only one pair is switched on. `prices.status` shows every switched-on pair. `prices.history_fill` always needs `--pair`.

## Limits

Limits will be per pair plus a total across all pairs (design section 6). Nothing is built for this yet.

## The move of the existing GBPUSD data

Before this change, the GBPUSD candles were in `data/candles/` directly. `.venv/bin/python -m prices.move_to_pairs plan` shows the one-off move into `data/candles/GBPUSD/` (with the gap records, the archive, the levels file and the GBPUSD fill records). `... go` does it, only while the price service is stopped, and proves nothing was lost: every candle counted, every file fingerprinted, and the store checks run, before and after. The record is kept in `data/moved_to_pair_folders.json`.

**Done on 7 November 2026.** The price service was restarted on the new code once before the move: it started with an empty `data/candles/GBPUSD/` and wrote IG's last Friday candle (21:55, identical to the one already stored) and four bigger candles built from it alone, plus a levels file. Those were moved aside, not deleted, to `data/accidental_restart_2026-11-07/` (fingerprints recorded before and after). Then the move ran with the service stopped: 3,505 candle rows (3,197 in the store and 308 in the archive) and 92 files, the same before and after, the store checks the same (0 problems).

