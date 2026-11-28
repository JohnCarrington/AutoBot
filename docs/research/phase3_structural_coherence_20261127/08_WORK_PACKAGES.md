# 8. Implementation work packages (not authorised; for approval)

Each is a separate commit. Failing tests come first. Base: the reviewed Phase 2 build (H-1). Branch proposal:
`structural-coherence` from the deployed Phase 2 commit.

| WP | Content | Files (expected) | Tests | Depends on |
|---|---|---|---|---|
| WP-0 | Test fixtures: the named trades' candles and STP states at the entry second, from records | `tests/structure/fixtures/` | — | Phase 2 deployed |
| WP-1 | `structure/coherence.py`: a pure `assess(settings, store, idea, stp_state, now) -> Assessment(state, verdict, findings[per opportunity], why, unverifiable, opposite_open)`. Rev 2: each opportunity judged on its own (R2); PAST at the opportunity's own `zone_break_close` (R1); ended opportunities never barriers (D-17); `UNKNOWN` via the gate's own availability checks (R5); resolution only on reconciled evidence via unchanged `stp.authorise._catch_up` and `unreconciled()`, with a pinned reason adapter (R3). No I/O beyond the inputs. | new module | TS-01…TS-14, TS-20, TS-22…TS-27, TS-30…TS-33 | WP-0 |
| WP-2 | Emit `context.rejection_candle` for all reversal-family strategies regardless of STP_AUTHORISES_ENTRIES (bounce 5m, level reversal already compute it). The confirmation logic is unchanged. | `strategies/bollinger_bounce_5m/strategy.py`, `strategies/level_reversal/strategy.py`, check others | TS-19 | — |
| WP-3 | Call in `Trading._place` after the entry filters, as a refuse-only step (R4, D-16). Switch `STRUCTURAL_COHERENCE` (default per D-10). Journal `structure refused` / `structure unknown` / `order`. A steps line with state and verdict, kept apart from `order.result`. Read STP via `FileSource` when the gate is off. | `trading/engine.py`, `config/switches`, `stp/source.py` (read only) | TS-15…TS-18, TS-28, TS-29 | WP-1, WP-2 |
| WP-4 | Reporting: dashboard trades/ideas show the SCA state and, separately, the overall admission. "Structure unknown" is shown distinctly from "Neutral" (R5), and "unverifiable" refusals are marked (R3). The daily summary counts deferrals by strategy, with UNKNOWN and unverifiable counted separately. No new trading behaviour. | `dashboard/`, `records/summary` | dashboard tests | WP-3 |
| WP-5 | Functional replays FS-01…FS-24 as tests (decisions only, no P&L; FS-15…FS-21 synthetic) | `tests/structure/test_functional_days.py` | FS-* | WP-3 |
| WP-6 | **Only if D-7 approves:** `structure/room.py`, switch `STRUCTURAL_ROOM`, its own journal kind | separate | TS-21 | WP-3 |
| WP-7 | Report and readiness pack, regression figures, independent review | `docs/research/phase3_.../implementation/` | full suite | all |

Out of scope: STP methodology, strategy signals, stops/TP, trade management, Phase 1/2 code paths, RSI
thresholds, expiry, opposite-position rule (unless D-6 says otherwise).
