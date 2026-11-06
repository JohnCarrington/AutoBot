# Prices and candles

How AutoBot receives live GBPUSD prices from IG and keeps them as candles. Every rule below is checked by a test (listed at the end).

## The one absolute rule: no historical prices

**The bot never asks IG for historical prices, for any reason.**

- IG's historical prices are the REST calls under `/prices` (`GET /prices/{epic}` and its variants). The IG part (`ig/client.py`) refuses any call to a `/prices` address before anything is sent, so even a mistake in the code cannot make one.
- A test reads every Python file in the project and fails if any of them contains an IG prices address, a "fetch historical prices" style function, or the `trading_ig` library.
- The price stream gives live prices only. Ticks are asked for **without** a snapshot, so IG does not send recent ticks on connecting.
- Gaps are recorded, never filled.

## Which market

- GBPUSD on the spread bet account is IG epic **`CS.D.GBPUSD.TODAY.IP`** ("GBP/USD", expiry DFB). It is in the settings file as `market.epic`.
- It was found with **one** IG market search (`GET /markets?searchTerm=GBPUSD`) on 6 November 2026, using `.venv/bin/python -m ig.find_market`. That command made five IG calls: log in, list accounts (which showed `IG_ACCOUNT_ID` is a SPREADBET account), switch to the account (already active), the one search, and log out. No other market call has been made. The bot itself never searches for markets: it uses the epic in the settings file.

## Live prices

- The bot connects to IG's price stream at the **streaming address IG gave at login**, as the bot's account, using the current session tokens. It uses the `lightstreamer-client-lib` library; this and every other library version is pinned in `requirements.txt`.
- It subscribes to exactly two things:
  - **Every tick** (`CHART:<epic>:TICK`): the buy price (IG's offer), the sell price (IG's bid) and the time.
  - **IG's own 5-minute candles** (`CHART:<epic>:5MINUTE`): buy open/high/low/close, sell open/high/low/close, the candle's start time, and IG's "finished" mark (`CONS_END`).
- Ticks are counted and the latest is kept in memory. They are not stored on disk at this stage.
- Only the `ig/` part talks to IG's streaming server (`ig/stream.py`). The `prices/` part gets the values from it.

### If the stream drops

- The bot waits, then reconnects. The waits go up each time: **5, 10, 20, 40, 80, 160, 300 seconds**, then 300 seconds for every further try (`stream.reconnect_waits_seconds`). It never reconnects in a fast loop.
- The streaming library's own automatic retrying is cut off, so only these waits apply.
- Once the stream has stayed connected for 60 minutes (`stream.healthy_after_minutes`), the waits start again from 5 seconds.
- **A drop never causes a login.** The reconnect uses the same session tokens.
- If IG **refuses the stream's login** (its session tokens are no longer accepted), the bot makes **one controlled re-login**, following the Stage 3 rules in `docs/IG_CONNECTION.md` (log in, then switch back to the bot's account without changing IG's default account). If IG refuses the stream again before it has been healthy for 60 minutes, or the re-login fails, the bot **stops with exit code 78**.
- Any other refusal from the streaming server (for example a subscription refused) is treated as a drop: wait, then reconnect.

### If no prices arrive

If no ticks or candle updates arrive for **120 seconds** (`stream.no_prices_warning_seconds`) **while the market is open**, the bot writes a warning such as `NO PRICES from IG for 120 seconds while the market is open`. It warns once, and writes another line when prices come back. While the market is closed there is no warning, and after the weekend the 120 seconds count from the Sunday open.

## Candles

- **Every candle keeps the buy price and the sell price separately**: open, high, low and close for each, eight prices in all. They are never mixed, and no mid price is stored anywhere.
- Prices are stored exactly as IG sends them (no rounding). On the spread bet account IG sends GBPUSD prices **in points**: `13354.4` means 1.33544. They are stored like that, unchanged.
- **IG's 5-minute candles are stored only once IG marks them finished.** Updates for a candle still in progress are counted but never stored. A finished candle with a missing or unreadable price, or a start time not on a 5-minute mark, is not stored, and a warning is written.
- When the stream connects, IG sends the current 5-minute candle's values so far. If that candle is already marked finished, it is stored like any other. This is IG's live stream, not a request for history, and nothing older than that one candle is ever sent.
- **1-hour, 4-hour, daily and weekly candles are built only from the stored 5-minute candles.** Buy and sell are each built on their own: the open of the first, the highest high, the lowest low and the close of the last.
- A bigger candle is built when its time is over and either all its 5-minute candles are stored, a later 5-minute candle has arrived, or 5 minutes (`candles.wait_for_late_candle_seconds`) have passed since its end. If some 5-minute candles are missing, it is still built from those that are stored. It records how many it used, for example `parts 11, expected_parts 12`, and a warning is written.

### Where the boundaries go (all settings; full reasons in `docs/SETTINGS.md`)

| Candle | Runs | Note |
|---|---|---|
| 5-minute | every 5 minutes | IG's own candles |
| 1-hour | on the hour | |
| 4-hour | 22:00, 02:00, 06:00, 10:00, 14:00, 18:00 UK | first of the week: Sunday 21:00 to Monday 02:00 |
| Daily | 22:00 to 22:00 UK | Monday's runs from Sunday 21:00 to Monday 22:00 |
| Weekly | Sunday 21:00 to Friday 22:00 UK | |

### Times

- **All times are stored in UTC**, written like `2026-11-06T19:05:00Z`.
- **Anything shown to a person is in UK time**, with GMT or BST shown: log lines, warnings and reports.

## The candle store

- Kept in `/opt/autobot/data/candles/` (`candles.folder`). The folder is not in git.
- **One file per day per candle size**: `5m/2026-11-06.csv`, `1h/2026-11-06.csv`, `4h/…`, `1d/…`, `1w/…`. Each file is named after the UTC date of its candles' starts.
- Each line holds: start and end (UTC), the 4 buy prices, the 4 sell prices, and `parts` / `expected_parts` (1 and 1 for a 5-minute candle).
- **A stored candle is never overwritten.** If the same candle arrives again with the same values, nothing happens. If a **different value** arrives for a stored candle, the stored one is kept and a warning is written showing both: `DIFFERENT VALUE for a stored candle, kept the stored one…`
- **Writes are safe.** A file is never changed in place. The whole new file is written to a temporary file in the same folder, flushed to disk, and then renamed over the old one in a single step, and the folder is flushed too. A crash or power cut at any moment leaves either the old file or the new one, never a damaged file. Any half-written temporary file is ignored, and removed at the next start-up.
- A file that cannot be read is reported and is never written over.
- **Candles are kept, never deleted.** Files more than 30 days old (`candles.compress_after_days`) are compressed to `.csv.gz` with the same safe-write steps. The original is removed only after the compressed copy has been read back and matches. Compressed files are still read normally.
- Every gap found is also kept in `/opt/autobot/data/candles/gaps.csv`: candle size, from, to, number missing, when it was found and how.

## Checks on the store

The store is checked **when the bot starts** (every stored candle of every size) and **after every new candle** (that candle, its file, and the candle before it). A warning is written for each of these:

- **A gap during market hours**: a candle missing between two stored candles. Each new gap is also recorded in `gaps.csv`. Gaps already recorded are mentioned but not warned about again.
- **A duplicate candle**: two candles with the same start time.
- **A buy price below the sell price**, for open, high, low or close.
- **A high below a low**, for buy or sell.
- **Anything out of time order**: candles not in order in their file, a candle in the wrong day's file, a candle that ends before it starts, or one that does not start on its boundary.
- **A file that cannot be read.**

**The weekend is not a gap.** IG's GBPUSD market is open from **Sunday 21:00 to Friday 21:59 UK time**, with no daily break. That is stated on IG's own page (source quoted in `docs/SETTINGS.md`) and set in the settings file under `[market_hours]`. No candles are expected between Friday 22:00 and Sunday 21:00, so a missing candle is a gap only if it falls inside market hours.

## Restarts

On start-up the bot:

1. removes any half-written temporary files,
2. compresses old files,
3. checks the whole store,
4. reports the **newest 5-minute candle** and **how long ago it finished**,
5. if 5-minute candles are missing between that candle and now, during market hours, writes a warning and **records the gap**, then carries on. **It does not try to fill it.** For example:
   - restart 5 minutes after the last candle: the one candle that finished while the bot was stopped is recorded as a 1-candle gap,
   - restart 2 hours later: a 24-candle gap,
   - restart Monday at 07:00 after stopping at Friday's close: only Sunday 21:00 to Monday 07:00 counts (120 candles); the weekend does not,
6. builds any bigger candles that are due from the 5-minute candles already stored.

When IG's candles start arriving again, the gap already recorded is not warned about a second time.

## Housekeeping

- **Logs** go to `/opt/autobot/logs/<name>.log`. A new file is started when the current one reaches 10 MB or is 24 hours old. At most 20 old files are kept, and any older than 30 days are deleted. All of these are settings under `[housekeeping]`. So each log can never use more than about 10 MB × 21 = 210 MB.
- **Disk space** is checked at start-up and after every new 5-minute candle. If less than 2048 MB is free (`housekeeping.min_free_disk_mb`), a `LOW DISK SPACE` warning is written.

## Commands

- `.venv/bin/python -m prices.run --minutes 20` runs the live price stream for 20 minutes, then logs out and reports: ticks received, the 5-minute candles stored, the store checks, and a count of every IG call (including historical price calls, which must be 0).
- `.venv/bin/python -m ig.find_market` is the one market search. It has been run once already and should not be needed again.

## The live run (6 November 2026)

`.venv/bin/python -m prices.run --minutes 20` ran from 19:20:39 to 19:40:40 GMT and exited normally (exit code 0).

- **Ticks:** 526 arrived. 518 had both a buy and a sell price. 8 had one price missing, and were counted and skipped (never guessed).
- **5-minute candles stored:** 4 (19:20, 19:25, 19:30, 19:35). Each was stored at the exact moment IG marked it finished. The candle in progress at the end (19:40) was not stored. 328 unfinished candle updates were received and none was stored.
- **Store checks:** start-up (empty store), after each of the 4 candles, and at the end: 0 problems, 0 gaps, 0 warnings.
- **IG calls:** 7 in total: `POST /session`, `GET /accounts`, `PUT /session` (412: already active), `DELETE /session`, 1 stream connection and 2 subscriptions. No drops, no re-logins. **Historical price calls: 0.**

## Tests

None of these tests contact IG. They use a pretend price stream (`tests/technical/fake_stream.py`) and the pretend IG from Stage 3, and the network is blocked while tests run.

| File | What it checks |
|---|---|
| `test_no_historical_prices.py` | No code can ask IG for historical prices. The IG part refuses any `/prices` address. The stream asks for no old ticks. |
| `test_find_market.py` | The market search makes exactly one market call. The epic is in the settings file. |
| `test_price_stream.py` | The streaming address and account are used. Both subscriptions carry buy and sell fields and no mid. Every tick is received. Only finished candles are stored. A stream that drops and comes back gets increasing waits (5, 10, 20, … 300) and never a login. The waits reset once the stream is healthy. Old connections are ignored. Re-login limits: one, then stop. Other errors reconnect with waits. The no-prices warning appears only while the market is open. No secrets appear in the logs. |
| `test_candle_store.py` | One file per day per size, in UTC. Buy and sell are kept apart, with exact prices. Never overwritten. A different value is warned. **A crash part-way through a write**, and a crash before the rename, leave the old file whole. Data is flushed before the rename. Damaged files are never written over. Compression keeps every candle. Gaps are recorded. |
| `test_candles_and_checks.py` | Market hours in summer and winter. Every boundary, including the joined Sunday hour. 1h, 4h, daily and weekly candles are built from 5-minute candles, buy and sell separately. Late and missing candles. Every store check: gap, **weekend gap**, duplicate, buy below sell, high below low, out of order, wrong file, misaligned, damaged. Checks after every new candle. **Restarts after 5 minutes, after 2 hours, and on Monday morning**, plus an empty store and leftover temp files. UK time on display. |
| `test_housekeeping.py` | Logs rotate by size and by age. Old logs are deleted. Limits come from the settings. Log lines are in UK time. Low disk space is warned. |
