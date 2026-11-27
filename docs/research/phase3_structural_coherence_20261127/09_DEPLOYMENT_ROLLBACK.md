# 9. Deployment and rollback approach (for when implementation is approved)

## 9.1 Preconditions

1. Phase 2 (stp-lifecycle-integrity) is reviewed, deployed, and its Saturday OP-1 recovery is complete. The SCA
   reads Phase 2 lineage state.
2. The Phase 3 build is reviewed independently. The full suite is green, run alone (no concurrent pytest in the
   shared checkout).
3. IG shows 0 open positions, or the owner accepts the open ones. No other session has uncommitted bot code in
   /opt/autobot (`git status`).
4. **No concurrent IG session during trading.** The deployment needs no IG calls.

## 9.2 Steps (the owner restarts; there is no sudo here)

1. Backup: `.env`, `config/settings.toml`, the data state (tgz), a git bundle, SHA256SUMS. Path:
   `/home/autobot/backups/deploy-structural-coherence-<ts>`.
2. Rollback tag `pre-structural-coherence-<date>` on the live commit, pushed.
3. Fast-forward /opt/autobot to the reviewed commit. Add the switch line to `.env` as decided (D-10).
4. The owner stops and starts `autobot-prices`. The dashboard restart is separate and the owner's (WP-4 only).
5. Verify: the start-up journal; the first `idea` lines carry the SCA step; for the first hour, every
   `structure refused` is checked against current.json by hand.

No shadow running, no parallel comparison (constraint 7). Only the live demo decides the effect.

## 9.3 Rollback (any of these, smallest first)

| Level | Action | Effect |
|---|---|---|
| R-1 | `.env` STRUCTURAL_COHERENCE=off + owner restart | the check is skipped; `_place` behaves exactly as today (TS-16) |
| R-2 | `git -C /opt/autobot reset --hard pre-structural-coherence-<date>` + restart | the code is back to the previous commit |
| R-3 | Restore the backup files | only if data were touched (the SCA writes only journal lines, so this is not expected) |

The SCA keeps no state. Rolling back needs no data migration, and the journal lines stay as history.
