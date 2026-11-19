# Execution integrity: the 19:50 level reversal and the analyser journal (18 November 2026)

Owner's investigation brief, 19 November 2026, from the 18 November trade review (`docs/research/trade_review_2026-11-18/REPORT.md`, branch `research/trade-review-2026-11-18`, 2c42722). Sell (bid) prices; times UTC (the UK is on GMT).

**What this work changed:**
- Nothing in production: no service restarted, no IG contact, no settings or .env change, no strategy rule changed.
- The fixes are on branch `fix/live-check-and-journal-provenance`, made from main 3d50353, the code the live service runs.

## Summary

| | Finding | Verdict | Fixed on the branch |
|---|---|---|---|
| 1 | The 19:50 level reversal sell | **A: a legitimate intrabar entry** under the written specification. The finished candle and the replay can't see the order of events inside a candle; that is documented, not a fault. | No change needed |
| 1b | Found while tracing 1: the live check runs on the new candle's first price before IG's finished candle is stored | **D: a market-data timing defect** (confirmed) | Yes: the live check waits for the finished candle |
| 2 | Journal lines for 09:30–13:15 on 18 Nov | **Confirmed:** written by the 13:35 restart's replay, appended as if live, with nothing to mark them | Yes: provenance and a recording time on every new line; old lines untouched |

## 1. The 19:50 level reversal sell

### The specification
- **Entry:** docs/DESIGN.md 3.6 rule 3: "The sell opens as soon as price breaks below the confirmation candle's low". docs/REJECTION.md, bounce step 4: "Trigger: the live price goes below the confirmation candle's low."
  - So an entry during the candle is intended.
- **Confirmation:** needs a finished candle. Step 3: "a later candle CLOSES below the reversal candle's low ... A wick below does not count."
- **Cancel:** step 5: "cancelled if price goes above the reversal candle's high at any point after the reversal candle".
- **Stored candles:** docs/REJECTION.md, "With stored candles instead of live prices": "If one candle goes both past the trigger price and past the cancel price, the order inside it is unknown. It counts as a trigger only if it opened past the trigger price; otherwise it counts as cancelled. Live, the watcher gets every price ... and triggers or cancels at the exact moment."

### The evidence (raw)
- **The setup:** setup #1465, with every step taken from finished candles. These are the trade's own steps in `data/records/GBPUSD/trades.jsonl`; the replay gives the same.
  - 19:30, the pierce: high 13140.9 reached S2 13140.2. The candle opened at 13139.7, below S2: price rose into it.
  - 19:35, the reversal candle: O 13138.3 H **13139.2** L 13136.7 C 13137.3. That makes **13139.2 the cancel price**.
  - 19:45, the confirmation: "closed 13135.9 below the reversal low 13136.7; trigger at below **13135.7**".
- **The live entry:** `reached on the live price at 19:50:58 UTC (bid 13135.6, offer 13137.1)`.
  - The order was sent at 19:50:58 and opened at 19:50:59, level 13135.8, deal DIAAAAYV2E3USBM.
- **The finished 19:50 candle:** O 13136.5 H 13139.9 L 13135.6 C 13138.3.
  - It went through the trigger (13135.6 < 13135.7) and above the cancel price (13139.9 > 13139.2).
  - It opened at 13136.5, not past the trigger.
  - So it counts as cancelled. The replay gives: `#1465 cancelled 13139.2: price went above the reversal candle's high 13139.2 (this candle went both ways; from candles alone the order is unknown, so it is treated as cancelled)`.

### Why live and the candle close differ
- **The live path:**
  - `prices/feed.py` `on_tick` sets the latest price, and `prices/service.py` `every_second` calls `engine.on_price`.
  - `trading/engine.py` `_live_entries`: `_forming` builds the candle so far ("as far as the live prices have gone"), then `StrategyRunner.peek`.
  - Each idea then goes through `check` (state, hours, switches), then `_place` (safety rules, then the order sender), and on to IG.
- **What peek does:** it gives the forming candle to copies of the same watcher and strategies (`fork`). These are the same rules as at the candle close (`step`).
  - At 19:50:58 the candle so far had gone through 13135.7. It had **not yet** gone above 13139.2: if it had, the same both-ways rule (`rejection/watch.py:341–355`) would have cancelled it, because it opened at 13136.5.
  - So the trigger came first. The rise to 13139.9 came later in the candle.
- **Was there a valid signal at the moment of entry?** Yes. Shown by the functional test, which uses the real candles and the live switches.
- **Should the trade have been admitted?** Yes. The decision line reads `allowed: true, state: trend`.

### Your band and levels questions
- **Does peek use the previous candle's Bollinger band?** Yes: `f = self.tracker.history[-1][0]  # the band as it stood at the last finished candle` (`strategies/replay.py`, `peek`). `step` uses each candle's own band.
- **But it made no difference here.** The band is read only in `_pierced`, when a new setup starts. The strategies' watcher (`design_only=True`) never checks a running setup for a pierce again (`again = [] if self.design_only else ...`). This setup's pierce was S2, a level.
  - The trigger and cancel steps don't read the band at all. A test gives the same trigger with no band, the right band or a wrong one.
- **Levels: no difference.** Both paths use `build(..., candle start)`, "using only candles that had finished by then" (`levels/current.py:73`).

### Verdict
**A: a legitimate intrabar entry.** The replay can't reproduce it, by its documented design.

**The same split has happened before.** 11 Nov 06:20:12 Bollinger bounce buy (the bounce's design before 15 Nov):
- confirmed at 06:15, trigger above 13340.7, cancel below 13338.7;
- the finished 06:20 candle: O 13340.6 H 13340.9 L 13337.7, so both ways, cancelled at the close;
- the live price: bid 13340.8 at 06:20:12, first.

Any replay total can show these trades differently from live. That is a known limit of the replays, not a fault in trading.

**Inference, not checked:** the stored 5-minute candles can't show which came first. The bot's own live-price record is the only proof of the order. No ticks are stored.

## 1b. Confirmed defect: the live check runs on the new candle's first price before the finished candle is stored

- **The evidence:** `logs/prices.log.1`:
  ```
  2026-11-18 15:45:00 GMT INFO autobot.orders: Order record: safety refused
  2026-11-18 15:45:00 GMT INFO autobot.prices: [GBPUSD] Stored 5m Wed 18 Nov 15:40 GMT: ...
  ```
  - The refused idea was a second live breakout sell (decisions: `15:45:00 idea breakout sell live` and then `order ... safety refused ['breakout already has 1 trade(s) open (at most 1)']`). The first, opened at 15:44:06, was still open.
- **The cause:** `every_second` calls `on_price` on the new candle's first price. IG's finished candle (`CONS_END`) can arrive after that. `peek` only checked `partial.start <= self.week[-1].start`.
  - So the copies were given the 15:45 candle straight after 15:35. They never saw the 15:40 candle, in which the breakout had already triggered. The analyser state and band were also a candle old.
- **What it can do:**
  - give a setup that already triggered a second time;
  - trigger a setup that was cancelled in the missing candle. Inference: there is no record of this happening.
- **Seen in the records:**
  - 16 Nov 09:20:00 level reversal sell;
  - 16 Nov 13:35:00 level reversal buy;
  - 17 Nov 18:45:00 Bollinger bounce sell;
  - 18 Nov 15:45:00 breakout sell.
  
  The one-trade-at-a-time rules refused all four.
- **What didn't happen:** every order sent in a candle's first 5 seconds within the logged span (16 Nov 21:20 to now) went out after the previous candle was stored (`Stored ... hh:mm:00`, then `sending` at :02 to :04).
  - Before 16 Nov 21:20 there are no logs, so it is **not proven** for older trades.
  - Every older opened trade either has a candle-close record, or (11 Nov 06:20) is the both-ways case above.
- **The fix** (`strategies/replay.py`): `peek` returns nothing while the candle before the forming one is in market hours and not yet taken (`waiting_for_finished_candle`). Normally that is a second or two; the next price after the store is checked as usual.
  - No strategy rule changes.
  - A candle IG never sends pauses the live check for one candle. The candle-close step still sends what it finds, as for any gap in the live prices.

## 2. Analyser journal provenance

### The evidence (raw)
- **The live log** shows the last change before the restart, and then nothing until 13:35, though the service was running:
  ```
  2026-11-18 08:40:01 GMT INFO autobot.analyser: [GBPUSD] Market state: Wed 18 Nov 08:35 GMT  trend (down, slow grind): ...
  2026-11-18 10:00:00 GMT INFO autobot.prices: [GBPUSD] Stored 5m Wed 18 Nov 09:55 GMT: ...
  ```
- **The restart's log lines:**
  ```
  2026-11-18 13:35:28 GMT WARNING autobot.analyser: [GBPUSD] The week's replay differs from the live record in 55 state change(s) at or before 2026-11-18T08:35:00Z (a rule changed?); not added to state_changes.jsonl, written to .../replay_differences_2026-11-18.jsonl.
  2026-11-18 13:35:28 GMT INFO autobot.analyser: [GBPUSD] Market states replayed from the week's open (767 candles): emerging trend (down) since 2026-11-18 13:15 UTC; ...
  ```
- **The independent live record:** the engine writes every live change to `data/records/GBPUSD/decisions.jsonl` (`analyser state change`), not the start-up replay's (`_changes_seen` is set at start-up). That gives 346 lines since 9 Nov 00:15.
  - All 346 are in the journal.
  - The journal has **7 lines since then that have no live record**: lines 539–545, 18 Nov 09:30, 09:35, 10:15, 10:25, 11:25, 12:55 and 13:15. All seven are listed with the evidence in `journal_annotations_2026-11-18.jsonl`; the journal itself is not changed.

### The cause
- **Not a write failure.** The live analyser wrote nothing between 08:35 and 13:35 because, under the old rules, the state didn't change.
- **Where the lines came from:** at 13:35 the new rules' replay of the week found changes at 09:30–13:15.
- **Why they were appended:** `analyser/market_state.py` `_write` appends every change with `time_utc > last`, where `last` is the journal's last line (08:35). It treats "newer than the last line" as "never decided". It does not know how far the last run had covered live (until about 13:30).
- **Why they look live:** the lines carry only the event time. There is no time of writing and nothing to say how they were made.

### Other dates
- **9 to 19 Nov:** the cross-check above shows **only 18 Nov** is affected.
- **Before 9 Nov:** there is no independent live record, so this is **unproven**. Those lines read as UNKNOWN_LEGACY.
  - The folder also has `state_changes_mixed_2026-11-07*.jsonl` and `state_changes_mixed_2026-11-12.jsonl`, earlier mixed journals put aside by hand.

### The fix (`analyser/market_state.py`)
- **Every new line gets:**
  - `provenance`;
  - `recorded_utc`, the moment it was written; `time_utc` stays the event time, the candle;
  - `run_started_utc`.
- **The four labels:**
  - `LIVE_DECISION`: made by the running analyser from a newly finished candle, not the start-up replay.
  - `HISTORICAL_REPLAY`: made by a start-up replay for a time the last run was covering live, or whenever that can't be ruled out.
  - `RECONSTRUCTED`: made by a start-up replay for a time after the last run's last live candle. `current.json` now carries `live_through_utc`.
  - `UNKNOWN_LEGACY`: `provenance_of()` returns it for any line without a known label. A line is never assumed live.
- **What doesn't change:**
  - Old lines are never rewritten or relabelled.
  - The duplicate check and the replay-differences file are unchanged.
  - The trading engine's own tracker writes nothing (`record=False`).

## 3. Tests

**New technical tests** (`tests/technical/test_execution_integrity.py`, 15):
- the live check waits for an unstored candle and goes on once it is taken;
- missing or delayed candles; no wait across the market's closed hours;
- a trigger is the same whatever band it is given;
- a forming candle through the trigger first triggers;
- one past the cancel price first is cancelled, and never triggers later;
- the finished-candle rule (both ways counts as cancelled unless it opened past the trigger);
- the fork never changes the watcher;
- journal: the 18 Nov case gives HISTORICAL_REPLAY, with the old lines byte-for-byte unchanged and read as UNKNOWN_LEGACY;
- journal: LIVE_DECISION while running; RECONSTRUCTED after a stop; no duplicate lines after another restart;
- journal: event time and recording time kept apart; a new week while running counts as live; a tracker that doesn't record writes nothing.

**New functional tests** (`tests/functional/test_execution_integrity_real_candles.py`, 2, on the real candles of 18 Nov with the live switches):
- **15:45:00:** the live check waits for the finished candle. With the wait bypassed, the 15:40 breakout sell is given again, which proves the test catches the defect. After the store, it is given once.
- **19:45:** the forming confirmation candle gives no entry.
- **19:50, the forming candle at 19:50:58:** gives the level reversal sell at 13135.7, **allowed**. It still does at the reversal high, 13139.2. Above 13139.2 first, or both ways, it gives nothing. The finished candle and the candle-close step give nothing.
- **A restart during the 19:50 candle:** gives the same live entry.

**Unchanged behaviour:**
- the existing live-entries functional test (the live check gives exactly the finished candle's ideas, all morning of 2 Nov);
- the trading and market-state tests;
- the full suite: see the commit (the pre-commit hook runs it).

## 4. Risks
- **The live check waits a second or two at each candle's turn.**
  - The bounce and session strategies open on the next candle's first price. They now open after IG's finished candle is stored, normally within a second or two. In the logged span they already did: :02 to :04.
  - If IG is late with a candle, those entries come later. If IG never sends it, they are missed for that candle; their rule is "never sent late".
- **The journal lines are bigger** (three fields). Only the analyser reads the journal.
- **Inference:** the trade manager's live run (`on_price`) still uses the band of the last finished candle during those seconds. This was not changed.

## 5. Ready to deploy?
- **Code and tests:** ready, once the full suite passes on the branch.
- **Recommendation:** deploy both together at a quiet time, with no trade open.
  - Not urgent: the timing defect has only produced refused duplicates.
  - The journal fix only adds fields.
- **Merging with Stage 4:** the fix is made from 3d50353. `strategies/replay.py` and `trading/engine.py` also change on feature/entries-exits (d7d2651), so it must be merged or rebased onto that. See the commit notes.
- **Never done here:** deploy, restart, or switch anything on.
