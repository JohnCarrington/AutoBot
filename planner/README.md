# planner

**What it does:** the Structural Trade Planner V1 (owner's approval of 17 November 2026). **OBSERVE ONLY: it does not control trading.** For the pair it decides:

- the dominant direction from the 4-hour structure, with daily and weekly as context;
- the condition: CONTINUATION, EXHAUSTION, CORRECTION_LIKELY, CORRECTION_ACTIVE, REVERSAL_RISK or INDETERMINATE;
- the opportunity: a corrective reversal or a healthy-trend pullback;
- the structural entry zone and its reference level;
- the intermediate, primary and extended destinations;
- the invalidation.

It writes this as one explained recommendation and keeps its full history.

It never authorises, refuses, opens, changes or closes a trade. It never contacts IG, and it reads no trading record. No strategy, safety rule, order sender or trade manager reads it. `PLANNER_AUTHORISES_BOUNCE` does not exist yet: authorisation is a later, separately approved stage.

| File | Job |
|---|---|
| `measure.py` | Finished candles only. 4-hour candles rebuilt from hourly on the store's boundaries. Indicators on H1/H4/daily/weekly with the bot's own code and the chart settings, each only once warmed up. The ADR (20 weekdays, Sunday candles left out). Freshness by the analyser's rule |
| `structure.py` | Swings by the existing turning-level rule (hourly 3/20/6; 4-hour 3/40/6; daily 3/110/6). Up/down/mixed structure. Breaks need a close at least 3 pips beyond. Turns held back only by the provisional 40/110-pip thresholds are recorded |
| `zones.py` | The existing levels plus weekly pivots, the previous week's high and low, 4-hour and daily swings, and moving-average levels. Families. Zones (the larger of 5 pips and 0.15 × ADR, built from fixed levels first). Major / Moderate / Minor classes. Tests. The one-sided 3-pip touch rule |
| `assess.py` | Direction, condition, opportunity, reachability, zone choice, destinations, invalidation, observations: one `Plan` |
| `keeper.py` | The lifecycle: CANDIDATE, WAITING, ACTIVE, INVALIDATED, SUPERSEDED, COMPLETED. The files `planner.folder/<PAIR>/current.json` and `recommendations.jsonl` (append-only). Also `issued.jsonl`: each recommendation in full as issued, for the dashboard's history (reporting only). `PlannerUpdater` for the price service |
| `panel.py` | The dashboard panel's content, from the planner's file only |
| `__main__.py` | `python -m planner run` (one keeper run) and `python -m planner show --at <UTC time>` (print a plan; writes nothing) |

**When it runs:** only while the switch `PLANNER_OBSERVE` in `.env` is on. It is off if left out, and stays off until the owner approves installation. After each new 5-minute candle, the price service starts `python -m planner run` in its own low-priority process (`nice -n 10`), after the trading engine, and never waits for it. It skips the start if the previous run is still going, and a lock file stops two runs overlapping. A planner failure is logged to `logs/planner.log` and leaves the previous planner files as they were. Prices and trading carry on unaffected.

**Rules in full:** `/home/autobot/research/structural_trade_planner_v1/` (design, decision register, parameter register, readiness), and the docstrings at the top of each file.

**Tests:** `tests/technical/test_planner.py`, `tests/functional/test_planner_scenarios.py`.
