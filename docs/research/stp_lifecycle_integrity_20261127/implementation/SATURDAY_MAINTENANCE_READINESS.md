# Saturday 28 November 2026: maintenance readiness pack (historical candle recovery, OP-1)

**Status: ready, nothing done yet.** The recovery waits until the GBP/USD market has closed (Friday 22:00 UTC, the configured weekly close) and you have stopped the price service.

Phase 2 is under feature freeze. Its deployment and STP re-activation are **not** part of this window, and nothing from Phase 3 is included. The Phase 1 −£23 corrections are not applied.

## 1. Production service status and configuration (27 Nov, 18:29 UTC)

| Item | Value |
|---|---|
| `/opt/autobot` | `fadf228` (deploy-23nov), no tracked change |
| `autobot-prices` | active, PID 1406204, since 16:26:57 UTC (your restart) |
| `autobot-dashboard` | active, PID 1392498, since 12:13:51 UTC (not restarted, so its STP tab shows the stale Stage B label) |
| `.env` STP switches | `STP_OPPORTUNITIES=on`, `STP_BIDIRECTIONAL=on`, **`STP_AUTHORISES_ENTRIES=off`** (since 14:58:26; in effect since the 16:26:57 restart), `PLANNER_OBSERVE=on`, `ONE_SIGNAL_ONE_TRADE=on`, `TRADING=on` |
| `.env` sha256 | `c414e0ff…`. The only change since the 14:58 backup is that one line |
| Since the restart | Trading ON 16:27:49 with 0 open trades taken over. STP tracker current; 17:00 re-plan made. No STP decision. Gated strategies back on their pre-Stage-B filters (counter-trend tiring and RSI stretch refusals at 16:35–16:55) |

## 2. Outstanding historical candle gaps (from `gaps.csv`; `gap-plan` contacts nobody)

| Gap | Candles | Cause | Scope |
|---|---|---|---|
| **Fri 27 Nov 12:00–12:10** | 3 | the deployment restart (price service stopped 12:01:58 to 12:13:51) | **OP-1, approved** |
| Mon 16 Nov 22:55–23:00 | 2 | recorded by the store's check | older; optional |
| Thu 19 Nov 18:35 | 1 | recorded by the store's check | older; optional |
| Fri 20 Nov 11:20 | 1 | recorded by the store's check | older; optional |
| Sun 22 Nov 21:05, 21:25, 21:45–21:50 | 4 | at the Sunday open | optional; IG may have sent none (as on 1 Nov) |

- **Today's 16:26:57 restart created no gap.** The 16:25 candle was stored at 16:30.
- Your Saturday instruction is to "identify all outstanding market data gaps … recover missing candles". **Recommended:** all 7 (one request each). The 27 Nov one is the one with a lifecycle consequence (§6). If you prefer OP-1 strictly, run only the 27 Nov window.

## 3. Expected IG API consumption

| Scope | Requests | Points |
|---|---|---|
| 27 Nov only (OP-1) | 1 | 3 |
| All 7 recorded gaps | 7 | 11 |

The bot's weekly budget is 7,000 points, 0 used in the last 7 days. IG last reported 4,157 of 10,000 remaining. No block marker.

The history door counts the points before anything is sent, and refuses beyond the budget or IG's floor. Each request covers one unbroken run of missing candles, and nothing is downloaded twice: a filled gap is no longer "recorded missing".

## 4. Backups (to take at the start of the window, after the market closes)

```
TS=$(date -u +%Y%m%d_%H%M%S); B=/home/autobot/backups/saturday-recovery-$TS; mkdir -p $B
cd /opt/autobot
tar czf $B/candles-GBPUSD.tgz data/candles/GBPUSD               # the whole candle store, incl. gaps.csv
tar czf $B/data-state.tgz data/planner data/orders data/records data/trade_manager data/trading data/history
cp -p .env $B/env; chmod 600 $B/env; cp -p config/settings.toml $B/
git rev-parse HEAD > $B/PRODUCTION_COMMIT
cd $B && sha256sum * > SHA256SUMS && sha256sum -c SHA256SUMS && tar tzf candles-GBPUSD.tgz | wc -l
```

Already held:
- `/home/autobot/backups/phase2-stp-lifecycle-20261127_145802`: candle store, state, env, settings, commit;
- `/home/autobot/backups/env-before-stp-auth-off-20261127_145826`.

## 5. The approved IG historical recovery procedure (`prices/history_fill.py`, docs/PRICES_AND_CANDLES.md)

1. **After the weekly close**, confirm: IG has 0 open positions (the read-only records check), AutoBot has 0 open trades and 0 unresolved orders, and the backups in §4 have been taken and verified.
2. **You** stop the price service: `sudo systemctl stop autobot-prices.service`. That gives one IG login at a time; there is never a concurrent session.
3. Plan, which contacts nobody: `.venv/bin/python -m prices.history_fill gap-plan --pair GBPUSD --from <from> --to <to>`, and check the requests and points against §3.
4. Fill, for each window: `.venv/bin/python -m prices.history_fill gap-go --pair GBPUSD --from <from> --to <to>`.
   - It logs in, fetches only the missing 5-minute candles (IG's own: snapshotTimeUTC; ask = buy, bid = sell) and stores them without overwriting.
   - It then rebuilds every 1h/4h/daily/weekly candle that was built from an incomplete set, archiving the old one (`archive_rebuilt/`).
   - It logs out.
5. Verify:
   - the store check reports 0 problems;
   - every recovered candle is on a 5-minute boundary, in order, with no duplicate;
   - the 1h 12:00 and 4h 12:00 candles on 27 Nov are now 12/12 and 48/48;
   - IG's points used match the plan;
   - nothing was interpolated or made up: a slot IG has no candle for stays a recorded gap.
6. Report the recovered candles (their 8 prices) and the API consumption. **You** then start the price service.

## 6. Offline lifecycle reconciliation on the recovered candles (after §5, before restarting the service)

```
mkdir -p /tmp/sat && cp -a <backup>/candles-GBPUSD.tgz /tmp/sat/ && (cd /tmp/sat && tar xzf candles-GBPUSD.tgz)   # pre-fill copy
cp -a /opt/autobot/data/candles/GBPUSD /tmp/sat/post                                                              # post-fill copy
cd /home/autobot/worktrees/autobot-stp-lifecycle-impl
.venv/bin/python docs/research/stp_lifecycle_integrity_20261127/implementation/saturday_offline_reconciliation.py \
    /tmp/sat/data/candles/GBPUSD /tmp/sat/post /tmp/sat/out
```

- **Offline and on copies only.** It never contacts IG, writes no production file and places no order.
- **What it does:** it starts from STP-GBPUSD-20261127-1200-57 exactly as published at 12:00:03, the opportunity live across the outage. It runs the Phase 2 tracker on the pre-fill store, so the gap is recorded, then on the post-fill store, which reconciles it.
- **Expected:** IG's own price at 12:05:11 (the owner's close, bid 13130.6) was inside 1200-57's zone tolerance. If IG's 12:05 candle confirms that, the ending's classification is corrected from "destination reached before entry" to "after_zone", in a new event, with nothing reopened. This is only an expectation until IG's candles are in.
- **Dry run on 27 Nov** (no recovered data): the gap is recorded and the classification stands, "after_zone_at_or_before_creation".
- **Second check:** re-run the 18:30 replay (`tests/functional/test_stp_lifecycle_replay_20261127.py::FL_E1`) on the post-fill store. With the 27 Nov 12:00 hour complete, the D-R2 block on the 15:00 SELL lineage is either cleared or left for review.

## 7. Final production lineage migration dry run (27 Nov 18:30 UTC, read-only on a copy)

The two builds are identical, nothing is ambiguous, and every consumed STP key is preserved:

| Trade | Key it consumed | Under its lineage | As |
|---|---|---|---|
| AB261125170604 | 1700-34#t1 | 1700-34#t1 | own key |
| AB261125200515 | 1800-35#t1 | 1700-23#t2 | **alias** |
| AB261126060101 | 0000-37#t1 | 0000-37#t1 | own key |
| AB261126063004 | 0400-38#t1 | 0400-38#t1 | own key |
| AB261126114004 | 0000-37#t2 | 0000-37#t2 | own key |
| AB261126125133 | 0400-38#t2 | 0400-38#t2 | own key |
| AB261126142255 | 1400-44#t1 | 1700-23#t6 | **alias** |
| AB261127065505 | 0300-56#t1 | 0300-56#t1 | own key |
| AB261127120127 | **1200-57#t1** | **0300-56#t1** | **alias** (the same test as 06:55) |
| AB261127151117 | 1500-59#t1 | 1700-23#t9 | **alias** |

Live opportunities: 1500-60 → lineage 0200-54; 1700-61 → lineage 0400-38. At deployment the map is rebuilt with `--as-of` set to the deployment time, then applied.

## 8. Before and after: production's opportunities and STP-authorised decisions (replay 25 Nov 09:15 to 27 Nov 18:30)

The replay uses the 18:29 production copies, with today's outage as production lived it.
- **The replay itself is exact:** on `fadf228` it reproduces production's journal for **all 36 opportunities with 0 differences**, and authorises the 10 trades with their recorded keys.
- **On the branch**, the outcomes for the 10 trades are:

| Trade | Production | Branch |
|---|---|---|
| 8 legitimate trades, 25 Nov 17:06 to 27 Nov 06:55 | opened | **opened**, each on a distinct test |
| AB261127120127 (27 Nov 12:01, the duplicate) | opened | **refused**: no live opportunity, since its reissue is withheld (0300-56's test 1 never re-armed) |
| AB261127151117 (27 Nov 15:11) | opened (+9.0, closed by hand 16:20) | **refused under D-R2**: its lineage's count runs through the uncertain 12:00 hour. Its re-armed 15:00 publication is issued. To be re-decided offline once the 12:00 hour is recovered (§6) |

- **Publications withheld:** only 1200-57 and 1305-58, the reissues of an unre-armed completed test. **No new publication.**
- **Classification corrected:** 1700-34 (completed after its 17:06 trade). Other destination endings now name their true circumstance.

## 9. Deployment and rollback (Phase 2: NOT authorised; for after the review)

**Deploy, with STP authorisation staying off:**
1. Pre-checks: IG positions, AutoBot open and unresolved orders; nothing in flight.
2. Back up `.env`, `settings.toml`, and `data/{planner,orders,records,trade_manager,trading}` (tar + sha256).
3. Fast-forward `/opt/autobot` to the reviewed commit. No `.env` or settings change.
4. `python -m planner.migrate_lineage --pair GBPUSD --as-of <now>` as a dry run; compare it with §7; then run it with `--apply`.
5. You restart `autobot-prices` and `autobot-dashboard`.
6. Post-checks:
   - "lineage map applied" recorded once;
   - live opportunities show their lineages;
   - `python -m planner.review --pair GBPUSD` lists only what fail-closed blocks;
   - the dashboard shows Watch & Wait and Stage A.
7. STP re-activation needs a separate approval.

**Rollback:**
1. Stop both services.
2. `git -C /opt/autobot reset --hard fadf228`.
3. Start both services.

`fadf228` ignores the Phase 2 state keys and files. To return exactly, restore `data-state.tgz`.

## 10. Final regression and commit

| Item | Value |
|---|---|
| Branch | https://github.com/JohnCarrington/AutoBot/tree/stp-lifecycle-integrity |
| Code commit (feature freeze) | `695cfed5bca6414df8dd92adfe8cb4153514cd27` |
| Full suite on it (pre-commit hook) | **2924 passed, 3 skipped** (920 s); the architectural guards included |
| This pack | the documentation commit after it, on the same branch (documents only; the suite runs again in its hook) |
