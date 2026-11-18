# STP improvements — test results (18 November 2026)

Branch `stp-improvements` (worktree `/home/autobot/worktrees/autobot-stp-improvements`), `nice -n 15`, one full
suite at a time.

| Run | Result |
|---|---|
| Planner + STP suites after the planner changes (first run) | 1 failed: `test_15…` (mirrored lagging-MACD market) — investigated: its last candle is at the primary destination, so D-1 correctly refuses the final plan. Test extended, nothing removed (CORRECTIONS.md section 1) |
| New tests `tests/technical/test_stp_corrections.py` | **28 passed** |
| Full suite #1 | **2324 passed, 0 failed** (7 min 44 s) — `stp-improvements-work/full_regression_1.log` |
| Pre-commit hook on the commit | see the commit (the hook refuses a commit with any failing test) |
| Browser chart checks (`chart_check.py`, dev harness) | **34 passed, 0 failed** (desktop and phone) |
| The same through the proposed nginx with its CSP enforced | **34 passed, 0 failed**, no CSP violation |

## Planner tests (technical and functional; real keeper, scripted planner)

D-1: touch rule at exactly 3.0 pips (reached) and 3.1 (not); BUY mirror; the real 17 November 21:55 / 22:55 candles
reached and 20:15 not; a destination price has gone well past stays "on the way"; at the hourly re-check the
recommendation's own reached destination ends it as INVALIDATED "destination reached before entry" (never active) or
COMPLETED (active), BUY and SELL, nothing new issued; a different destination still "supporting evidence changed";
a valid recommendation is issued and its destination-first rule still works.
Pre-creation: candle timing before / overlapped / after; price in the zone before creation never activates ("in zone
at creation"); created before the interaction → ACTIVE with candle, timing and basis recorded; a candle running at
creation → "ambiguous", the next candle activates; zone and destination in one overlapping candle → nothing changes;
several interactions in one post-creation candle keep the existing order; BUY/SELL symmetry; restart/recovery
(running every 5 minutes and catching up after 15 minutes give the same events); a live recommendation from before the
correction keeps its recorded rule after a restart.
Reporting: `issued.jsonl` keeps the snapshot, candidates and analysis time, never rewritten later; the real planner's
snapshot holds levels, zones and swings, contains the entry and destination zones, nothing after the plan's time and
is identical when the store is cut at that time (no future data); a broken snapshot never stops the plan.
Evaluation: a pre-creation activation is not counted (and its completion not counted as after the zone), the
original record is kept and the correction listed; an overlapping activation moves to the first candle after creation;
the detail carries the snapshot's levels with their view tier, values as recorded; the overview uses the full snapshot;
the three views, the H1 / 60-candle default, the label placement and the single axis label exist in the page code; no
line-through style.

## Chart checks (browser)

Default TRADE PLAN on H1 with 48–72 candles (even with an old remembered timeframe in browser storage) · three modes ·
entry zone shaded exactly between its recorded edges (pixel-compared with the chart's own price-to-pixel conversion) ·
destination and invalidation lines at their recorded prices · one price-axis label · no overlapping labels in each
view · trade plan draws far fewer lines than full analysis · hover details · level list · H4/M5/H1 switching loads
the right candles · historical replay draws the original plan · no horizontal overflow · Operations tab and compact
card still work · no script errors. Desktop 1440×900 and phone 390×844.
