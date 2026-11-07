# Prices and candles

How AutoBot receives live GBPUSD prices from IG and keeps them as candles. Every rule below is checked by a test (listed at the end).

## Historical prices: one guarded door

**Only one part of the code may ask IG for historical prices: the history door, `ig/history.py`.** Nothing else can.

- IG's historical prices are the REST calls under `/prices` (`GET /prices/{epic}` and its variants). The IG part (`ig/client.py`) refuses any `/prices` call before anything is sent, unless the history door has opened it for one request that passed every check below.
- A test reads every Python file in the project, tests included, and fails if any file other than `ig/history.py` contains an IG prices address, a "fetch historical prices" style function, the `trading_ig` library, or opens the history door.
- The live price stream never asks for history. Ticks are asked for **without** a snapshot, so IG does not send recent ticks on connecting.

### The checks, in this order

Every history request must pass all four. If one fails, the request is refused: nothing is sent, a warning is logged, and the refusal goes into the daily record.

1. **No block marker is in place** (see below).
2. **The bot's own weekly budget has room for it.** Points counted in the last 7 days, plus this request, must be no more than `history.weekly_budget_points` (4,000; IG allows 10,000 a week). One point is one candle.
3. **IG's remaining allowance stays above the safety floor.** IG's last reported remaining allowance, less this request, must stay at or above `history.min_ig_allowance_remaining` (2,000). Before IG has ever reported a figure there is nothing to check against, so the first request is allowed and its reply gives the figure.
4. **The request is no bigger than the maximum,** `history.max_points_per_request` (500).

### Counting and records

All of these live in `/opt/autobot/data/history/` (`history.folder`) and are written with safe writes.

- **Points are counted BEFORE each request is sent**, and saved to disk straight away in `ledger.json`. A crash or restart can never lose the count. A request that never got a reply stays counted. If IG charges more than was counted, IG's figure is used.
- **After every reply, IG's own figures are saved** in `ig_allowance.json`: remaining allowance, total allowance, and when it resets.
- **A daily record**, `daily_record.csv`, has one line per UTC day: requests sent, points counted, refusals by the bot and by IG, and IG's figures. It is rewritten after every request and every refusal.

### The block marker

- If IG ever refuses a history request because the allowance is used up, the bot writes `BLOCKED.json`. Its expiry is IG's reset time if given, and never less than `history.min_block_hours` (24 hours).
- **While the marker is in place, no history request is sent, even after a restart.** A marker that cannot be read counts as in place.
- This refusal is not a login problem. It never stops the bot or causes a retry.

### Filling gaps

- **Only gaps the store has recorded** (in `gaps.csv`) are filled. Only 5-minute candles, and only during market hours: **never the weekend**.
- **Only the missing candles are asked for.** Each request covers one unbroken run of missing 5-minute candles and is no bigger than the maximum size.
- **What comes back only fills missing candles.** A stored 5-minute candle is never overwritten. Anything IG sends that was not asked for is ignored and reported. If IG's times do not line up with the request, the fill stops.
- **IG's own UTC times are used** (`snapshotTimeUTC`). The buy price is IG's ask, the sell price IG's bid. A candle with a missing price is not used.

### The one-off two-week fill (6 November 2026)

Commands: `.venv/bin/python -m prices.history_fill plan --pair GBPUSD` shows the plan and contacts nobody. `... go --pair GBPUSD` runs it. The pair is always named, never assumed. The fill is recorded as started before its first request and as done at the end, for that pair only (`data/history/<PAIR>/one_off_fill_done.json`), so it can never run again by itself. A newly switched-on pair is never filled automatically: its own one-off fill needs the owner's go-ahead, and it uses the same shared weekly budget and IG allowance (`docs/PAIRS.md`).

It was planned, shown, approved, and run at 20:00 GMT on 6 November 2026:

- **Requests:** 9 in all. 1 for IG's daily candles (13 points counted, 12 charged). 1 for the 4 live Stage 4a candles, to compare only, never stored. 7 to fill (the largest 500).
- **IG's allowance:** 9,970 of 10,000 before, **7,091** after, resetting 13 November 03:00 UTC. IG charged 2,879 points; the bot counted 2,893. Nothing was refused and no block marker was written.
- **Stored:** 2,862 five-minute candles, covering 25 October 21:00 to 6 November 20:00 GMT.
- **Filled vs live candles:** the 4 live candles (19:20 to 19:35) were **identical on all 8 prices**, so the times line up.
- **IG's daily candles vs ours:** IG's daily candles run midnight to midnight UK, with a separate short Sunday candle. The bot's boundaries were then 22:00 to 22:00. Its daily boundaries were changed to match IG's (see below). Rebuilt on midnight boundaries, the bot's daily candles match **all 11 of IG's complete days on all 8 prices**, including both Sunday candles. At first the one difference was the label on the Sunday candle: IG labelled it 00:00, the start of the calendar day, while the bot's carried the 21:00 open. The bot now labels it the same way as IG, and the stored candles were relabelled (see "Labels" below). All 11 of IG's complete days now match the bot's on start label and all 8 prices.
- **The weekly close:** IG's candles also showed the Friday close follows New York time (see "Checks on the store").
- **Store checks on everything afterwards:** 3,178 candles, **0 problems**. 2 gaps, both on Sunday 1 November: 21:20, which IG sent with a price missing, and 21:35, which IG never sent.

**Archive.** The 1-hour, 4-hour, daily and weekly candles first built under the earlier 22:00 layout were moved, not deleted, to `/opt/autobot/data/candles/GBPUSD/archive_22h_layout/` (then `data/candles/archive_22h_layout/`, before each pair had its own folder). They were then rebuilt from the stored 5-minute candles on IG's boundaries, with no IG calls. The bot does not read the archive.

### Gap fill, Friday 6 November 20:00 to 20:30 (done 7 November 2026)

With the owner's go-ahead: `.venv/bin/python -m prices.history_fill gap-go --pair GBPUSD --from 2026-11-06T20:00:00Z --to 2026-11-06T20:40:00Z` (`gap-plan` shows the requests first and contacts nobody). It fills only recorded gaps inside the window, through the history door, never overwriting a stored candle, then builds the bigger candles that are due.

- 1 request, 7 points (20:00 to 20:30; 20:35 had been stored live). IG's allowance 7,091 then 7,084 of 10,000. 7 candles stored.
- Built: Friday's daily candle (264 of 264), the 4-hour 20:00 candle (24 of 24) and the week from Sun 1 Nov (1,450 of 1,452: the two Sunday 1 November candles IG never sent).
- The 1-hour 20:00 candle had already been built from the 5 candles then stored (5 of 12). At first it was kept, and the full rebuild was logged as a "DIFFERENT VALUE" warning in `logs/history.log`. With the owner's go-ahead it was then swapped for the full rebuild (12 of 12) under the rebuild rule below, with `.venv/bin/python -m prices.history_fill rebuild --pair GBPUSD --from 2026-11-06T20:00:00Z --to 2026-11-06T20:35:00Z` (no IG contact; the price service kept running). Sell open 13348.4 became 13351.4, high 13350.7 became 13353.2; low and close unchanged. The old candle is in `data/candles/GBPUSD/archive_rebuilt/1h/2026-11-06.csv`.
- Store checks after: 0 problems; 2 gaps left, both on Sunday 1 November (IG never sent them).

## Which market

- GBPUSD on the spread bet account is IG epic **`CS.D.GBPUSD.TODAY.IP`** ("GBP/USD", expiry DFB). It is in the settings file as `pairs.GBPUSD.epic`, with GBPUSD's pip size and price scale. Each pair has its own (`docs/PAIRS.md`).
- It was found with **one** IG market search (`GET /markets?searchTerm=GBPUSD`) on 6 November 2026, using `.venv/bin/python -m ig.find_market` (now `... ig.find_market GBPUSD`: the pair is always named). That command made five IG calls: log in, list accounts (which showed `IG_ACCOUNT_ID` is a SPREADBET account), switch to the account (already active), the one search, and log out. No other market call has been made. The bot itself never searches for markets: it uses the epic in the settings file.

## Live prices

- The bot connects to IG's price stream at the **streaming address IG gave at login**, as the bot's account, using the current session tokens. It uses the `lightstreamer-client-lib` library; this and every other library version is pinned in `requirements.txt`.
- It subscribes to exactly two things:
  - **Every tick** (`CHART:<epic>:TICK`): the buy price (IG's offer), the sell price (IG's bid) and the time.
  - **IG's own 5-minute candles** (`CHART:<epic>:5MINUTE`): buy open/high/low/close, sell open/high/low/close, the candle's start time, and IG's "finished" mark (`CONS_END`).
- Ticks are counted and the latest is kept in memory. They are not stored on disk at this stage.
- **IG's `BID` is always the sell price and `OFR` always the buy price**, for ticks and for candles (`BID_*` = sell, `OFR_*` = buy).
- **IG sends only the tick price that changed.** A blank `BID` or `OFR` means that price is unchanged. The bot then uses the last value received **on the same connection**:
  - Only once **both** `BID` and `OFR` have been received at least once on that connection. Until then, a tick with a blank price is skipped.
  - **Every new connection starts fresh** (the first connect, every reconnect and every re-login). A price from before a reconnect is **never** carried forward.
  - A price that is present but unreadable is not used, and that side is unknown again until IG sends a fresh one.
  - Skipped ticks are logged with exactly what IG sent, for example `IG sent: BID (sell)='' OFR (buy)='1.31010' UTM=…`. The live run's report and the service's status line give the number of ticks that used a carried-forward price, and the number skipped.
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
| 4-hour | 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UK | first of the week labelled Sunday 20:00; holds 21:00 to midnight |
| Daily | midnight to midnight UK, **like IG's** | a short Sunday candle labelled 00:00, like IG's, holding 21:00 to midnight; Friday's ends at the close |
| Weekly | labelled Sunday 00:00 UK; runs to Friday's close (17:00 New York) | holds Sunday 21:00 to the close |

**Labels.** Like IG, a candle is labelled with its normal boundary start, even when the market opens later. Its candles are always the ones during market hours between its start and its end, so `expected_parts` counts only open time: 36 for the Sunday daily candle.

On 6 November 2026, the five stored candles that carried the 21:00 open were relabelled, with prices and ends unchanged:
- the Sunday 25 October and 1 November daily candles, to 00:00
- the matching 4-hour candles, to 20:00
- the week of 25 October, to Sunday 00:00

A relabelling writes the candle under its new label first, then removes the old one, each with a safe write. It is only done when deliberately approved.

### Times

- **All times are stored in UTC**, written like `2026-11-06T19:05:00Z`.
- **Anything shown to a person is in UK time**, with GMT or BST shown: log lines, warnings and reports.

## The candle store

- **One store per pair**, kept in `/opt/autobot/data/candles/<PAIR>/` (`candles.folder`/`<PAIR>`), for example `data/candles/GBPUSD/`. The folder is not in git. A part given another pair's store stops at once (`docs/PAIRS.md`).
- **One file per day per candle size**: `5m/2026-11-06.csv`, `1h/2026-11-06.csv`, `4h/…`, `1d/…`, `1w/…`. Each file is named after the UTC date of its candles' starts.
- Each line holds: start and end (UTC), the 4 buy prices, the 4 sell prices, and `parts` / `expected_parts` (1 and 1 for a 5-minute candle).
- **A stored candle is never overwritten.** If the same candle arrives again with the same values, nothing happens. If a **different value** arrives for a stored candle, the stored one is kept and a warning is written showing both: `DIFFERENT VALUE for a stored candle, kept the stored one…`
- **The one exception, the rebuild rule (standing rule from 7 November 2026):** when a gap fill completes missing 5-minute candles, every bigger candle (1-hour, 4-hour, daily, weekly) holding one of them that was built from an incomplete set (`parts` below `expected_parts`) is rebuilt from **all** the 5-minute candles now stored, if that is a fuller set. The old candle is **archived first, never deleted**: `<store>/archive_rebuilt/<size>/<UTC date>.csv`, with its prices, parts, when it was archived, why, and how many parts its replacement has. Then the day file is rewritten with the new candle in its place (safe writes). A complete candle is never replaced, a 5-minute candle is never replaced, and running the rule again changes nothing. It runs automatically at the end of every gap fill (`gap-go`, and a pair's one-off fill). For a fill already done, `.venv/bin/python -m prices.history_fill rebuild --pair <PAIR> --from <UTC> --to <UTC>` applies it to the 5-minute candles stored in that window, without contacting IG. It can run while the price service is running: the store reads every file fresh, the service writes only when IG sends a new candle, and each file is replaced in one step.
- **Writes are safe.** A file is never changed in place. The whole new file is written to a temporary file in the same folder, flushed to disk, and then renamed over the old one in a single step, and the folder is flushed too. A crash or power cut at any moment leaves either the old file or the new one, never a damaged file. Any half-written temporary file is ignored, and removed at the next start-up.
- A file that cannot be read is reported and is never written over.
- **Candles are kept, never deleted.** Files more than 30 days old (`candles.compress_after_days`) are compressed to `.csv.gz` with the same safe-write steps. The original is removed only after the compressed copy has been read back and matches. Compressed files are still read normally.
- Every gap found is also kept in the pair's own `gaps.csv` (`/opt/autobot/data/candles/<PAIR>/gaps.csv`): candle size, from, to, number missing, when it was found and how.

## Checks on the store

The store is checked **when the bot starts** (every stored candle of every size) and **after every new candle** (that candle, its file, and the candle before it). A warning is written for each of these:

- **A gap during market hours**: a candle missing between two stored candles. Each new gap is also recorded in `gaps.csv`. Gaps already recorded are mentioned but not warned about again.
- **A duplicate candle**: two candles with the same start time.
- **A buy price below the sell price**, for open, high, low or close.
- **A high below a low**, for buy or sell.
- **Anything out of time order**: candles not in order in their file, a candle in the wrong day's file, a candle that ends before it starts, or one that does not start on its boundary.
- **A file that cannot be read.**

**The weekend is not a gap.** IG's GBPUSD market opens on **Sunday at 21:00 UK time** and closes on **Friday at 17:00 New York time**, with no daily break. In UK time the close is 22:00 most of the year, and 21:00 in the weeks when US clocks are on summer time and the UK's are not. This rule comes from IG's published hours together with IG's own candles from the history fill. Both sources, and the three rules tested against them, are in `docs/SETTINGS.md`. It is set under `[market_hours]`. No candles are expected between the close and the open, so a missing candle is a gap only if it falls inside market hours.

**Notes on gap records.** `gaps.csv` has a `note` column. A note can be added to a recorded gap, but gap records are never removed. The Friday 30 October 21:00 to 22:00 records carry a note saying the hour was a closed hour found under the old market-hours rule, not a real gap.

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

- `.venv/bin/python -m prices.run --minutes 20 [--pair GBPUSD]` runs the live price stream for one pair for 20 minutes (stop the service first: one login at a time), then logs out and reports: ticks received, the 5-minute candles stored, the store checks, and a count of every IG call (including historical price calls, which must be 0).
- `.venv/bin/python -m ig.find_market <PAIR>` is the one market search for a pair. It has been run once for GBPUSD and is only needed again for a new pair.
- `.venv/bin/python -m prices.history_fill plan --pair <PAIR>` shows a pair's one-off history fill plan (no IG contact). `... go --pair GBPUSD` ran once, on 6 November 2026, and will not run again for GBPUSD.
- `.venv/bin/python -m prices.move_to_pairs plan|go`: the one-off move of the existing GBPUSD data into the per-pair folders (`docs/PAIRS.md`).

## Running the price stream as a service

The price stream runs all the time as a systemd service, `autobot-prices`, so the candle store keeps growing.

- **Service file:** `deploy/autobot-prices.service` in the repository, installed as `/etc/systemd/system/autobot-prices.service`. It runs `/opt/autobot/.venv/bin/python -m prices.service` as the `autobot` user, from `/opt/autobot`, and starts on boot once the network is up.
- **Every pair switched on** (`PAIRS_ON` in `.env`) is streamed, with **one IG login and one stream connection**; each update goes to its own pair's store. A newly switched-on pair starts with an empty store and is never filled from history.
- **On start** it does exactly what the live run does, for each pair: it checks the store, reports the newest candle and its age, and **records any gap** since that candle. **It never asks IG for history**: the service does not use the history door at all, and a test checks that. Then it logs in and streams.
- **After a crash** (any exit other than 0 or 78) systemd restarts it **after 30 seconds** (`RestartSec=30`). It never starts more than **5 times in an hour** (`StartLimitBurst=5`, `StartLimitIntervalSec=3600`), so a crash loop can never become a login loop. After that, systemd gives up and a person must look.
- **After an IG login failure (exit code 78) it does NOT restart** (`RestartPreventExitStatus=78`). A person must find out what went wrong, then start it again.
- **On stop** (`systemctl stop`) it stops the stream, logs out of IG and exits with code 0.
- **While running** it writes a status line to the log every 60 minutes (`stream.status_log_minutes`).
- **After start-up and after every new 5-minute candle** it updates the current list of levels (`docs/LEVELS.md`). A problem with the levels is warned about and never stops the service.
- **Logs** go to the systemd journal and to `/opt/autobot/logs/prices.log`. The log file is rotated by size and age (see Housekeeping). The journal has systemd's own size limits.

### Installing it (once; needs sudo)

```
sudo cp /opt/autobot/deploy/autobot-prices.service /etc/systemd/system/autobot-prices.service
sudo systemctl daemon-reload
sudo systemctl enable autobot-prices
sudo systemctl start autobot-prices
```

After changing the service file in the repository, copy it again and run `sudo systemctl daemon-reload`, then `sudo systemctl restart autobot-prices`.

### Starting, stopping and checking it

| To | Command |
|---|---|
| Start | `sudo systemctl start autobot-prices` |
| Stop (logs out of IG cleanly) | `sudo systemctl stop autobot-prices` |
| Restart (for example after a code change) | `sudo systemctl restart autobot-prices` |
| Is it running? | `systemctl status autobot-prices` |
| Its log for the last 10 minutes | `journalctl -u autobot-prices --since "10 min ago"` |
| Follow its log live | `journalctl -u autobot-prices -f` |
| The newest candles in each switched-on pair's store, and their age | `cd /opt/autobot && .venv/bin/python -m prices.status` (contacts nobody) |
| Stop it starting on boot | `sudo systemctl disable autobot-prices` |
| After exit code 78, once the IG problem is fixed | `sudo systemctl reset-failed autobot-prices` then `sudo systemctl start autobot-prices` |
| After 5 crashes in an hour, once the cause is fixed | `sudo systemctl reset-failed autobot-prices` then `sudo systemctl start autobot-prices` |

`systemctl status` shows `active (running)` when it is running. After a login failure it shows `failed` with `status=78`.

Stop the service before running `prices.run` or `prices.history_fill` by hand, so that only one copy of the bot is logged in to IG at a time.

## The live run (6 November 2026)

`.venv/bin/python -m prices.run --minutes 20` ran from 19:20:39 to 19:40:40 GMT and exited normally (exit code 0).

- **Ticks:** 526 arrived. 518 had both a buy and a sell price. 8 had one price missing, and were counted and skipped (never guessed). The cause is not yet known: the log did not record what IG sent. A skipped tick now logs exactly what IG sent (`BID=… OFR=… UTM=…`). The service's first log on 6 November 2026 showed `BID=None OFR='13351.8'`: IG sends only the price that changed. A blank price is now carried forward from the same connection (see "Live prices").
- **5-minute candles stored:** 4 (19:20, 19:25, 19:30, 19:35). Each was stored at the exact moment IG marked it finished. The candle in progress at the end (19:40) was not stored. 328 unfinished candle updates were received and none was stored.
- **Store checks:** start-up (empty store), after each of the 4 candles, and at the end: 0 problems, 0 gaps, 0 warnings.
- **IG calls:** 7 in total: `POST /session`, `GET /accounts`, `PUT /session` (412: already active), `DELETE /session`, 1 stream connection and 2 subscriptions. No drops, no re-logins. **Historical price calls: 0.**

## Tests

None of these tests contact IG. They use a pretend price stream (`tests/technical/fake_stream.py`) and the pretend IG from Stage 3, and the network is blocked while tests run.

| File | What it checks |
|---|---|
| `test_no_historical_prices.py` | No code other than the history door can ask IG for historical prices, or open the door. The IG part refuses any `/prices` address outside the door. The stream asks for no old ticks. |
| `test_history_door.py` | The four checks, in order. **A budget that would be exceeded**, the IG floor, and **a request over the maximum size** are refused with nothing sent. **A crash just after counting** keeps the count, and it still limits the budget after a restart. A request with no reply stays counted. IG's figures are saved. **The daily record is actually written.** **A refusal writes the block marker**, with IG's reset time or the minimum. **A restart while the marker is in place** sends nothing. Expiry. An unreadable marker blocks. No exit 78. |
| `test_history_fill.py` | IG rows: UTC times, ask = buy, bid = sell, missing prices not used. Only recorded gaps are filled, never the weekend, only missing candles, never too big. Replies never overwrite. The plan's order and sizes. A gap fill asks only for the missing candles in its window. The rebuild rule: an incomplete hour is rebuilt from the full set after a fill and the old one archived with when and why; a complete candle or a set that is not fuller is never replaced; running it twice archives once and changes nothing. The one-off fill records the gaps, fills them, is recorded as done, and can never run again. It stops if IG's times do not line up. |
| `test_find_market.py` | The market search makes exactly one market call. The epic is in the settings file. |
| `test_price_stream.py` | The streaming address and account are used. Both subscriptions carry buy and sell fields and no mid. Every tick is received. BID is the sell price and OFR the buy price. A blank BID or OFR carries forward the last value from the same connection, only once both have been received on it; every reconnect and re-login starts fresh, and a late tick from an old connection cannot seed a new one; an unreadable price is never used. Only finished candles are stored. A stream that drops and comes back gets increasing waits (5, 10, 20, … 300) and never a login. The waits reset once the stream is healthy. Old connections are ignored. Re-login limits: one, then stop. Other errors reconnect with waits. The no-prices warning appears only while the market is open. No secrets appear in the logs. |
| `test_candle_store.py` | Notes on gap records; older gap files still read. One file per day per size, in UTC. Buy and sell are kept apart, with exact prices. Never overwritten. A different value is warned. **A crash part-way through a write**, and a crash before the rename, leave the old file whole. Data is flushed before the rename. Damaged files are never written over. Compression keeps every candle. Gaps are recorded. |
| `test_candles_and_checks.py` | Market hours checked against every first and last candle IG sent, through summer, winter and the March clock-change weeks. Every boundary, matching IG's midnight days and short Sunday candle (and the earlier joined layout as an option). New candles are never built over stored ones. 1h, 4h, daily and weekly candles are built from 5-minute candles, buy and sell separately. Late and missing candles. Every store check: gap, **weekend gap**, duplicate, buy below sell, high below low, out of order, wrong file, misaligned, damaged. Checks after every new candle. **Restarts after 5 minutes, after 2 hours, and on Monday morning**, plus an empty store and leftover temp files. UK time on display. |
| `test_pairs.py` | Every part with two pretend pairs switched on (EURUSD, and EURJPY at 10 points a pip): each pair's own epic, pip size and folders; one stream connection for both, each update going to its own pair's store; the service with one login, no history, the gap recorded only for its pair, a newly switched-on pair left empty; pip distances (round numbers, spread limit) per pair; the analyser per pair; one shared history budget with each request's epic recorded; a pair's one-off fill is its own and never starts by itself; every part refuses another pair's store; the one-off move of the GBPUSD data loses nothing and refuses while the service runs. |
| `test_service.py` | The service file: runs as `autobot` from `/opt/autobot`, restarts after a crash with at least 30 seconds between, never restarts after exit 78, at most 5 starts an hour. The service never uses the history door. Start-up records the gap and asks no history, then it streams, and stops cleanly with a logout. Exit 78 after the stream is refused twice. A crash still logs out. A stop request ends a reconnect wait at once. |
| `test_housekeeping.py` | Logs rotate by size and by age. Old logs are deleted. Limits come from the settings. Log lines are in UK time. Low disk space is warned. |
