# Saturday 28 November 2026: maintenance report and Phase 2 deployment readiness

**Status: maintenance complete; Phase 2 ready for independent review. Nothing deployed.**

- The price service is **still stopped**, as the owner instructed (stopped 06:18:35 UTC). The owner restarts it.
- No Phase 2 deployment. STP stays de-activated (`STP_AUTHORISES_ENTRIES=off`).
- No historical financial correction. No Phase 3 work.
- Phase 2 is under feature freeze. The code is unchanged since `695cfed`, and this commit adds documents and evidence only.

Followed: `implementation/SATURDAY_MAINTENANCE_READINESS.md`, with the recovery extended to all 7 recorded gaps (the owner, 28 Nov).

## 1. Pre-maintenance checks

| Check | Result |
|---|---|
| Market | closed: the last 5-minute candle was stored Fri 27 Nov 21:55; no IG prices since 22:00 |
| Had any maintenance started before the overnight SSH drop? | **No.** No backup after 27 Nov 14:58; `gaps.csv` unchanged since 27 Nov 12:20; no `history_fill` run; the IG history ledger had no entry since 7 Nov |
| Price service at 05:45 | **running** (PID 1406204, since the owner's 27 Nov 16:26:57 restart), so recovery was held. The owner stopped it at **06:18:35**, with "Logged out of IG: confirmed" |
| Dashboard | running; it holds no IG client, so no IG session was open during the fill |
| IG positions (05:46:57, read-only, through the running service's own login, so no second session) | **0 open positions**; balance and available £96,879.61; IG's only activity since 16:00 is the two SYSTEM closes at 16:20 (`data/orders/ig_check_result.2026-11-28_premaint.json`) |
| AutoBot | 0 open trades (`open_trades.json` = `{}`); **0 unresolved orders**: the only "unclear" order (25 Nov 18:02) was settled "gone at IG" on 27 Nov 12:15; since the restart, the only order event is 1 breakout refused outside trading hours |
| Production | `/opt/autobot` = `fadf228`, no tracked change; `.env` byte-identical to the backup |
| Backups | `/home/autobot/backups/saturday-recovery-20261128_061908` (candle store, data state, env, settings, commit). `sha256sum -c`: all OK. The archive unpacks byte-identical to the live store (`diff -r`). All 1,952 candle files checksummed (`candle_store_sha256_prefill.txt`) |
| Fresh `gap-plan` (contacts nobody) | **7 requests, 11 candles, 11 points**, the same as the pack. Budget 7,000 a week, 0 used in 7 days; IG last reported 4,157 of 10,000; no block marker |

## 2. Recovery (`prices.history_fill gap-go`, 06:19:22 to 06:19:28 UTC; `gap_go.log`)

There was one IG session: `POST /session` ×1, `GET /accounts` ×1, `PUT /session → 412` ×1 (the account was already active, which is normal), 7 price requests, then `DELETE /session → 204`.

| Gap (UTC) | Asked | IG supplied | Stored |
|---|---|---|---|
| Mon 16 Nov 22:55, 23:00 | 2 | 2 | 2 |
| Thu 19 Nov 18:35 | 1 | 1 | 1 |
| Fri 20 Nov 11:20 | 1 | 1 | 1 |
| Sun 22 Nov 21:05 | 1 | **0** | 0 |
| Sun 22 Nov 21:25 | 1 | **0** | 0 |
| Sun 22 Nov 21:45, 21:50 | 2 | **0** | 0 |
| Fri 27 Nov 12:00, 12:05, 12:10 (OP-1) | 3 | 3 | 3 |
| **Total** | **11** | **7** | **7** |

**Candles IG cannot supply:** the 4 Sunday-open candles of 22 Nov (21:05, 21:25, 21:45, 21:50). IG answered each request with no candle, as it did for the 1, 8 and 15 Nov Sunday opens. They stay recorded gaps. Nothing was interpolated or made up.

**API consumption:**
- Bot's ledger: 7 requests, 11 points counted. It counts each request by its asked size before sending.
- IG: 10,000 → **9,993**, so **7 points**. IG charged only for the candles it returned; the 4 empty replies cost nothing.
- IG's weekly allowance had reset. The next reset is 5 Dec 06:19 UTC.

### The 7 recovered candles (IG's own; buy = ask, sell = bid)

| Start (UTC) | Buy O / H / L / C | Sell O / H / L / C |
|---|---|---|
| 16 Nov 22:55 | 13195.0 / 13196.5 / 13192.8 / 13196.5 | 13178.1 / 13180.9 / 13177.3 / 13179.6 |
| 16 Nov 23:00 | 13194.3 / 13194.3 / 13185.5 / 13186.1 | 13179.9 / 13187.0 / 13179.1 / 13181.7 |
| 19 Nov 18:35 | 13104.9 / 13108.4 / 13104.3 / 13108.3 | 13103.4 / 13106.9 / 13102.8 / 13106.8 |
| 20 Nov 11:20 | 13111.5 / 13114.5 / 13109.5 / 13113.3 | 13110.0 / 13113.0 / 13108.0 / 13111.1 |
| 27 Nov 12:00 | 13131.3 / 13133.6 / 13130.1 / 13132.3 | 13129.8 / 13132.1 / 13128.6 / 13130.8 |
| 27 Nov 12:05 | 13132.4 / 13133.4 / 13131.7 / 13132.8 | 13130.9 / 13131.9 / 13130.2 / 13131.3 |
| 27 Nov 12:10 | 13132.9 / 13136.1 / 13131.7 / 13135.8 | 13131.4 / 13134.6 / 13130.2 / 13134.3 |

## 3. Store verification (`verify_fill.txt`, `fill_diff.json`: every row of the pre-fill copy compared with the post-fill store)

- **5-minute candles:**
  - exactly the 7 expected timestamps were added;
  - **0 existing 5-minute rows changed, 0 removed**;
  - the four affected day files are in order, with no duplicate, all on 5-minute boundaries, each recovered candle `parts 1/1`.
- **Bigger candles:** they changed only where the tool rebuilt them from a now-complete set. Each old one is archived in `archive_rebuilt/`.
  - 1h: 16 Nov 22:00 and 23:00, 19 Nov 18:00, 20 Nov 11:00, 27 Nov 12:00. **27 Nov 12:00 is now 12/12**, with its open corrected to 13131.3 / 13129.8 from the 12:15 stand-in.
  - 4h: 16 Nov 20:00, 19 Nov 16:00, 20 Nov 08:00, 27 Nov 12:00. **27 Nov 12:00 is now 48/48.**
  - 1d: 16, 19, 20 Nov (parts only).
  - 1w: 15 Nov (1442 → 1446 of 1452; the 6 missing are the 15 Nov Sunday-open candles).
  - **New:** 1d 27 Nov (264/264) and 1w 22 Nov (1448/1452; the 4 missing are listed above). The service had not yet built these; the fill tool built them from the complete store.
- **No file removed.** No row removed in any timeframe.
- **Store check after the fill:** 0 problems; 14 gaps (all recorded, 0 unrecorded), against 18 before.
- `gaps.csv` keeps its history (it is a record of what was found). A filled gap is simply no longer missing.
- The live store has been unchanged since the fill (`candle_store_sha256_postfill.txt`, re-checked at the end).

## 4. Production records: nothing rewritten, no retrospective trade

- `data/planner`, `data/orders`, `data/records`, `data/trade_manager`, `data/trading`: **byte-identical** to the 06:19 backup.
- The jsonl/csv journals are **append-only** against the 27 Nov 14:58 baseline (7 files; each old file is an exact prefix of the current one).
- `data/history/ledger.json`: the old entries are unchanged, with 7 new gap-fill entries. `ig_allowance.json` and `daily_record.csv` were updated by the tool.
- All the reconciliation, replay and migration work below ran on **copies**, in temporary folders, never against `/opt/autobot/data`. It placed no order and wrote no record.

## 5. Offline lifecycle reconciliation (pack §6; `offline_reconciliation.json`)

This was run on the pre-fill and post-fill copies with `implementation/saturday_offline_reconciliation.py`, from STP-GBPUSD-20261127-1200-57 exactly as it was published at 12:00:03.

- **On the pre-fill store:** the gap 12:00–12:15 is recorded on 1200-57, which ends at 12:20 as `invalidated`, `after_zone_at_or_before_creation`.
- **On the post-fill store, one tracker run:**
  - event `classification corrected`, `after_zone_at_or_before_creation` → **`after_zone`**. IG's 12:05 candle (sell low 13130.2, inside the zone 13121.3–13130.3) reached the zone after creation and before the destination;
  - the gap is `reconciled`;
  - `status` stays **INVALIDATED** (not reopened), with `effective_status` COMPLETED and `activated: false`.
- **Lineage 0300-56, test 1:** consumed by AB261127065505 and AB261127120127, with the alias `1200-57#t1`. It is unchanged.

## 6. Extended production replay on the recovered data (25 Nov 09:15 to 27 Nov 18:30; `replay_saturday.txt/.json.gz`, `scripts/saturday_replay.py`)

There are three runs, all on the branch code (`695cfed` code; `9e0ffd5` tree):

| Run | Candles | STP's plans |
|---|---|---|
| **As lived** | the 18:29 production fixture (the 27 Nov gap as production saw it) | production's recorded plans |
| **As lived + Saturday run** | the as-lived state, then one tracker run at 18:30:03 on the recovered store | as above |
| **Recovered** | the fixture with IG's recovered candles. Only the 20 Nov 11:20 and 27 Nov 12:00–12:10 candles and the 4 bigger candles rebuilt from them change; see `recovered_fixture_candles/` and `scripts/make_recovered_fixture.py` | computed on demand with `planner.assess.plan_at` on the post-fill store copy. That code is unchanged from production `fadf228`, and the settings.toml is identical |

The production outage (12:01:58 to 12:20, no tracker run) is kept in every run.

**Validity of the recovered run:**
- `plan_at` on the pre-fill copy reproduces **all 123 recorded plans with 0 differences** (`scripts/validate_plans.py`).
- **Control:** the as-lived replay with computed plans is **byte-identical** (events sha256) to the replay with recorded plans.
- With complete candles, the 27 Nov 12:00 hour becomes visible at 13:00 instead of 13:05. The only re-plan production never recorded is therefore **13:00:03**.
- On the recovered store, plans differ from production's recorded ones at 16 of 123 points:
  - 26 Nov 23:00, by 0.1 in H1 EMA200, which reaches back into the rebuilt 16–20 Nov hours;
  - 27 Nov 13:05 to 18:00, in observation text only.
- **Determinism:** each run was repeated, and the events sha256 is identical every time (as lived `867b3cb6…`, recovered `bec0ca46…`).

### The 10 STP-authorised trades

| Trade | Production | Branch, as lived | Branch, recovered |
|---|---|---|---|
| AB261125170604 25 Nov 17:06 | opened | **opened** (1700-34 t1) | **opened** (1700-34 t1) |
| AB261125200515 25 Nov 20:05 | opened | **opened** (1800-35 t1) | **opened** (1800-35 t1) |
| AB261126060101 26 Nov 06:01 | opened | **opened** (0000-37 t1) | **opened** (0000-37 t1) |
| AB261126063004 26 Nov 06:30 | opened | **opened** (0400-38 t1) | **opened** (0400-38 t1) |
| AB261126114004 26 Nov 11:40 | opened | **opened** (0000-37 t2) | **opened** (0000-37 t2) |
| AB261126125133 26 Nov 12:51 | opened | **opened** (0400-38 t2) | **opened** (0400-38 t2) |
| AB261126142255 26 Nov 14:22 | opened | **opened** (1800-35 t5) | **opened** (1800-35 t5) |
| AB261127065505 27 Nov 06:55 | opened | **opened** (0300-56 t1) | **opened** (0300-56 t1) |
| **AB261127120127 27 Nov 12:01 (the duplicate BUY)** | opened | **refused**: no live BUY opportunity (the reissue is withheld; test 1 never re-armed) | **refused**: same reason |
| **AB261127151117 27 Nov 15:11 (SELL)** | opened | refused under D-R2 (uncertain hour 27 Nov 12:00 in its lineage's count) | **eligible and opened**, on lineage 1800-35 **test 8**, a genuinely new structural test after re-arms, distinct from 20:05's t1 and 14:22's t5 |

Lineage ids in the replay are the replay's own. It starts on 25 Nov 09:15 without the 24 Nov history. The historical map (§7) relates them to production's keys.

**The recovered evidence supports the 15:11 SELL.** The 27 Nov 12:00 hour, complete with IG's candles, changes nothing in the D-25 count of any lineage ("no change for the D-25 count"). The fail-closed refusal was only because the hour was unknown.

**As lived + Saturday run:** the tracker records 4 × `uncertain hour reconciled` (lineages 1800-35, 0000-37, 0400-38, 0200-54; hour 27 Nov 12:00; "no change for the D-25 count"). That is all. **No `created`, no `trade executed`, nothing reopened and no retrospective trade.** The 15:11 decision belongs to its own time and is not re-taken. The real trade AB261127151117 already exists in production's records and is left as recorded.

### Before and after: production's opportunities (`compare_opportunities.txt`; matched by creation time, direction and zone)

| | Production | Branch, as lived | Branch, recovered |
|---|---|---|---|
| Opportunities issued in the window | 35 | 33 | 33 |
| Not issued by the branch | – | 1200-57, 1305-58 (reissues of the un-re-armed 0300-56 test 1) | the same two |
| Issued by the branch only | – | none | **none** |
| End (time, event) different from production | – | 1700-34 only (invalidated → **completed**, after its 17:06 trade) | the same |
| Same end (time, event) in all three | – | – | **32 of 33** |
| Recovered vs as lived | – | – | the same lifecycles; one destination case renamed: 1500-59 `after_zone` → `after_trade`, since the 15:11 trade is entered from it |

## 7. Fresh production lineage migration dry run (`migration_dryrun_*.txt`, `lineage_map_dryrun_*fill_20261128.json`)

How it ran:
- `planner.migrate_lineage.build`, the dry run's own code, run on **copies**: the 06:19 backup of planner/orders/records, and the pre-fill and post-fill candle copies.
- `--as-of` was 2026-11-28T06:00:00Z, after the weekly close (no candle can arrive before Sunday's open).
- Each was built twice.

| | Pre-fill store | Post-fill store |
|---|---|---|
| Deterministic (two builds byte-identical) | yes, sha256 `99da2094…` | yes, sha256 `4d79e0cc…` |
| Ambiguous keys | none | none |
| Uncertain hours | 27 Nov 12:00 (lineage 0400-38) | **none** |
| Consumed keys, aliases, live map | identical in both | |

**All 10 historically consumed STP keys are protected:**

| Trade | Consumed key | Lineage key | As |
|---|---|---|---|
| AB261125170604 | 1700-34#t1 | 1700-34#t1 | own |
| AB261125200515 | 1800-35#t1 | 1700-23#t2 | alias |
| AB261126060101 | 0000-37#t1 | 0000-37#t1 | own |
| AB261126063004 | 0400-38#t1 | 0400-38#t1 | own |
| AB261126114004 | 0000-37#t2 | 0000-37#t2 | own |
| AB261126125133 | 0400-38#t2 | 0400-38#t2 | own |
| AB261126142255 | 1400-44#t1 | 1700-23#t6 | alias |
| AB261127065505 | 0300-56#t1 | 0300-56#t1 | own |
| AB261127120127 | 1200-57#t1 | 0300-56#t1 | alias (the same test as 06:55) |
| AB261127151117 | 1500-59#t1 | 1700-23#t9 | alias |

This is the same as the 27 Nov 18:30 dry run.

**Live opportunities now:**
- 1700-61 → lineage 0400-38;
- 2200-63 (created at 22:00 on Fri) → lineage 0000-17.

The 18:30 run's 1500-60 has since ended. The map must still be rebuilt with `--as-of` at deployment time.

## 8. Tests

| Run | Result |
|---|---|
| Full suite on `9e0ffd5` (code `695cfed`), 28 Nov | **2924 passed, 3 skipped** (968 s) |
| Targeted lifecycle tests (`targeted_tests.txt`): replay FL_*, the gap tests, WP1 re-arm/lineage/alias/migration and WP3 reconciliation | **39 passed**, including 9 re-arm tests. Among them: FL_E1 (a genuinely new test after many re-arms is published), TW1_03 (a re-arm gives the next test), TW1_08 (an incomplete hour cannot re-arm), FL_A4 (no republication authorises another trade on a consumed test) |
| This commit's pre-commit hook | the suite runs again (documents only) |

## 9. Remaining uncertainties

1. **The 4 Sunday-open candles of 22 Nov are permanently unavailable from IG.** So are the earlier ones on 1, 8 and 15 Nov (14 recorded 5-minute gaps remain, all at Sunday opens). The 1w candles of 15 and 22 Nov stay incomplete (1446 and 1448 of 1452). None falls in the 25–27 Nov lifecycle window.
2. **The recovered replay is a counterfactual.** It shows the 15:11 SELL would have been eligible had the candles been there. It is evidence, not a trade, and nothing is re-taken. After deployment, the tracker's first run will do what the "as lived + Saturday run" shows.
3. **The 1200-57 correction is offline only.** In production it happens on the Phase 2 tracker's first run after deployment, as a new event. `fadf228` (now in production) does no reconciliation.
4. **The live lineage mapping will change again.** It must be rebuilt at deployment (`--as-of <deployment time>`), as the pack says. The Sunday 22:00 open will re-plan.
5. **gap-go log wording.** After the REBUILT lines, it prints "built 1d 27 Nov (261 of 264)" and "built 1w 22 Nov (1445 of 1452)". The stored files are verified complete (264/264, 1448/1452). The line order looks like buffered messages from the store's first build, before the rebuild, but I did not trace it in the code. It is cosmetic; the store is correct.
6. **The dashboard** has still not been restarted since 27 Nov 12:13:51, so its STP tab keeps the stale Stage B label.
7. **The two 27 Nov 16:20 closes** (SYSTEM channel) are the owner's hand closes and stay out of the bot's results. The Phase 1 −£23 corrections are still not applied.

## 10. State left for the owner

- `autobot-prices`: **stopped** since 06:18:35 UTC. It needs the owner's restart before the Sunday 22:00 UTC open: `sudo systemctl start autobot-prices.service`. It runs `fadf228`, which reads the now-complete store; STP authorisation stays off.
- Production code `fadf228`, `.env` and settings are unchanged.
- **Phase 2 deployment** (pack §9) and **STP re-activation** each wait for separate approval after the independent review.
- Rollback for the candle store, if ever wanted: restore `candles-GBPUSD.tgz` from `/home/autobot/backups/saturday-recovery-20261128_061908`, with the service stopped.
