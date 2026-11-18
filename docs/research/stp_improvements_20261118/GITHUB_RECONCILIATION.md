# GitHub reconciliation (18 November 2026)

Remote `origin` (GitHub `JohnCarrington/AutoBot`), branch `main`, fetched 18 November 2026.

- `origin/main` = `aea2275` (16 November 23:42 UTC, "Merge session-strategies…"). It is an ancestor of production
  `main`: **no divergence**; a plain fast-forward push needs no history rewrite.
- Production `main` was 8 commits ahead before this work (all by the `autobot` identity, 17 November):

| Commit | Time (UTC) | What | Origin |
|---|---|---|---|
| c0ede45 | 16:55 | Trail stop moves IG can accept | trail-fix session (owner-approved, merged at cc70dc5) |
| c93bbb5 | 18:47 | Structural Trade Planner V1, observe only | planner session |
| 6dc4968 | 19:04 | Planner MACD correction | planner session |
| aac51f6 | 19:23 | Planner: owner's R1–R3 | planner session |
| 233d054 | 19:40 | Merge structural-trade-planner-v1 (owner's deployment approval) | planner session |
| cc70dc5 | 20:36 | Merge trail-fix | trail-fix session |
| 106d2d4 | 23:04 | STP dashboard tab | STP dashboard deployment |
| c41ddbd | 23:15 | STP tab fixes, investigation, screenshots | STP dashboard deployment |

  Six predate the dashboard work and come from other sessions (trail-fix, planner), each already merged into
  production with the owner's approval; two belong to the dashboard deployment. This brief adds its own commits on
  top (see the completion report).
- Untracked files of other sessions in `/opt/autobot` (`research/tick_replay.py`, `research/ticks.py`,
  `tests/technical/test_tick_replay.py`, three `docs/research/hourly_range_*` files) are not committed and are not
  pushed.
- Secrets scan of everything that would be published (`git diff origin/main..main`): see the completion report.
