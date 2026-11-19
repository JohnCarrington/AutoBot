# STP targeted corrections: implementation and tests (19 November 2026)

Owner's approval of the three corrections in `/home/autobot/research/stp_targeted_20261119/REPORT.md`. Branch
`stp-targeted-corrections` (worktree `/home/autobot/worktrees/autobot-stp-targeted`), from main 141636d.
**Not deployed.** Observe only: nothing here authorises, opens or manages a trade.

## Changes
| File | Change |
|---|---|
| `planner/structure.py` | `dominant_structure()` (candidate C) and `Structure.sweep`. `structure()` (the observed swings) is unchanged |
| `planner/assess.py` | The 4-hour direction uses `dominant_structure` (the daily chart still uses `structure`). An unresolved sweep is named in the reason and recorded in `observations["h4_sweep"]`. `condition_unclassified` marks INDETERMINATE that is only "the evidence does not fit one condition" (data ready) |
| `planner/keeper.py` | Issuing and validity are separate tests. A live recommendation is KEPT on an unclassified, fresh re-plan with the same direction, and is not current meanwhile. `last_ended` and the duplicate rule (same identity and primary as the last COMPLETED recommendation: not issued, recorded once, `not_issued` in state) |
| `dashboard/stp.py` | Labels for `kept` and `duplicate`; the explanation names a suppressed duplicate |
| `tests/stp_fixtures.py` | `identical_zones` now aims at another primary destination (the old shape is a duplicate by design). New `duplicate_after_completion` |
| `tests/technical/test_stp_targeted.py` | 23 tests: structure (synthetic and real 18 November candles), keeper, duplicate, dashboard, observe-only |
| `tests/candles/gbpusd_4h_20261026_20261119.json` | Real 4-hour candles, 26 Oct to 19 Nov, for the real-candle tests |
| `planner/README.md` | Describes the changes |

## Results
- **New tests:** 23 passed. Against main's keeper, the 6 keeper and dashboard tests fail, as intended.
- **Full suite:** 2,524 passed, 0 failed (21 min 43 s, low priority).
- **Equivalence:** the implemented `dominant_structure` matches research candidate C on all 392 four-hour closes checked: 108 in the production window from 27 Oct and 284 in the 21 history windows.
- **18–19 Nov, end to end** (the implemented keeper and planner, every 5 minutes, read-only store):
  - NEUTRAL "sweep unresolved" from 08:00 to 11:00; BEARISH from 12:00;
  - recommendations at 21:00 and 08:00, both COMPLETED;
  - duplicates suppressed at 23:00 and 10:00;
  - at 11:00 on 19 Nov, a new recommendation on different fixed levels (zone 13162.5–13172.8).
- **13 Nov, end to end:** the recommendation of 08:00 was kept at 12:00 (unclassified) and completed at 12:45; under main it was cancelled at 12:00. The recommendation of 20:00 was kept from 22:00.
