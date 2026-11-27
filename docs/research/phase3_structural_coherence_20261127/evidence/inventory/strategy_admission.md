# AutoBot strategy admission inventory: from idea to order

Code: worktree `/home/autobot/worktrees/autobot-phase3-research` at **fadf228**, the commit in production (`/opt/autobot` HEAD = fadf228).
Read-only study. All paths are relative to the worktree. Prices are chart (SELL/bid) prices unless stated. GBPUSD has 10 points per pip (`points_per_pip`), so `13106.8` = 1.31068.

---

## 0. Production switches that affect admission (`/opt/autobot/.env`, switch keys only)

| Switch | Value | Effect on admission |
|---|---|---|
| TRADING | on | live orders |
| NEW_TRADES_FROM / NEW_TRADES_UNTIL | 06:00 / 20:30 UK | trading hours, `common.trading_hours_reasons` (common.py:211) |
| STRATEGY_* (all 10) | **all on** | — |
| STOP_LOSS_PIPS / STOP_LOSS_PIPS_EMA_PULLBACK / TAKE_PROFIT_PIPS | 12 / 12 / 100 | default stop and take profit |
| **STP_AUTHORISES_ENTRIES** | **off** | STP gate inactive, STP zones not added to levels, `current.json` never read by trading |
| STP_OPPORTUNITIES / STP_BIDIRECTIONAL / PLANNER_OBSERVE | on / on / on | planner runs and writes `current.json` (observe only) |
| ONE_SIGNAL_ONE_TRADE | on | safety rule 11; rule 9 also counts sweep and NYOR |
| PULLBACK_ENTRY | on | breakout and ARB wait for an 8-EMA pullback; breakout then opens at the next candle's open |
| HOURLY_CONTEXT | on | entry filter rule 1 |
| ENTRY_NEAR_EMA8 | off | rule 2 not applied |
| RSI_STRETCH / TREND_DAY_RSI_OFF | on / on | rule 2b, with the slow-grind trend-day exemption |
| COUNTER_TREND_TIRING / _EMERGING / _HOURLY_CONFIRMED | on / on / on | rule 3 |
| EMA_PULLBACK_TRADING_HOURS / _ONE_AT_A_TIME / _TREND_ONLY / _SLOPE_DIRECTION / _RECHECK_AT_OPEN / _NO_R3_S3 / _ENTRY_PULLBACK_CANDLE / _NO_HOURLY_GAP_MIN | **all on** | EMA pullback rules (below) |
| ANALYSER_TREND_HOLDS_TO_100EMA / TREND_ENDS_IN_CONSOLIDATION | on / on | analyser state behaviour, which feeds the gating |
| EMERGING_LADDER | on | after entry only (stop ladder) |
| BOUNCE_ONLY_NEAR_TIMES | absent → off | — |

**ROOM_TO_LEVEL does not exist in fadf228.** It is not in any `.py` or `.toml` file in the worktree; it lives only on the unmerged branch `room-to-level`. **No strategy checks the room to the next level or opposing structure.**

Relevant settings (`config/settings.toml`):
- `[limits]` (64–69): `max_open_trades_per_strategy=1`, `bollinger_bounce_extra_opposite_direction_trades=1`, `max_open_trades=5`.
- `[stp_authorisation]` (669–677):
  - `strategies = ["Bollinger bounce","Bollinger bounce 5m","level reversal"]`
  - `bypass_filters = ["analyser_state","hourly_context","rsi_stretch","counter_trend_tiring","one_view"]`
- `[rejection]` `near_level_within_pips=3`, `max_spread_pips=3`.

---

## 1. The shared path, in order (who checks what, and where)

```
StrategyRunner.step (candle close)  /  StrategyRunner.peek (live, forked copies)      strategies/replay.py:209 / :161
  └ each strategy's on_candle -> Candidate(strategy, direction, time, entry_price, steps, context)
  └ common.check -> allowed()                                                       strategies/common.py:451 / :377
       1 switch STRATEGY_x on                                                       common.py:383
       2 analyser state (ALLOWED_IN; skipped for WITHOUT_HINDRANCE; skipped if STP bypass)   common.py:385-401
       3 direction rule (pivot + 5m 100 EMA) unless in NO_DIRECTION_RULE             common.py:402-404
       4 BOUNCE_ONLY_NEAR_TIMES (off)                                                 common.py:416
     -> Idea(allowed / blocked_by)
Trading (trading/engine.py)
  live:  _live_entries  :648  — skips blocked ideas silently; dedupe key (strategy,dir,candle start) in self.fired :660-663;
         decision "idea" live=True :667; then _place :670
  close: _take_new_candles :248 — decision "idea" for EVERY idea (allowed or blocked) :270;
         skip already_sent_live; "idea not sent again" (one try per strategy/dir/candle) :273-277;
         opens-at-next-candle strategies never sent late ("bounce not sent"/"not sent late") :280-288; else _send -> _place :290/:301
  _place :321
     a STP gate (only if stp.gate.gated: switch on AND strategy in list)  :325-344  -> "STP refused" + "order"
     b entry_filters.check(settings, MemoStore(store), idea, trend, bypass)  :346-359 -> "entry filter refused" + "order"
     c day_directions(...) (for safety rule 9)                             :360
     d OrderSender.place(...)                                              :361 -> "order" decision :363
OrderSender.place  orders/sender.py:851
     ready? :857 ; order_for (stop pips / stop price distance) :861 (safety/rules.py:93)
     safety.decide :862 (safety/rules.py:237): pause; idea.allowed; switch again; may_open (hours/news/Friday/rollover/NYOR news);
        _limits (per strategy / each way / max 5); size; total risk; funds; rule 9 one view; rule 10 once a day; rule 11 one signal
        -> "safety refused" in orders.jsonl, Result("safety refused")
     _stop_distance :870 (stop price -> distance from the live bid/offer, refused if already past)
     take_profit_pips :875 ; body forceOpen=True :882 ; record "sending" :903 ; POST /positions/otc :910
```

Important properties:
- **Blocked ideas (common.check) never reach `_place`.** They are journalled only at candle close (`kind:"idea", allowed:false, blocked_by`). On the live path they are skipped without a record (engine.py:661).
- **The dedupe key is added before `_place`.** A live idea refused in `_place` (by STP, an entry filter or a safety rule) is NOT retried at candle close, because `already_sent_live` is true (engine.py:269/278). One try per (strategy, direction, candle).
- **Order of refusal: STP gate → entry filters → safety rules.** The pause switch and the limits are checked AFTER the entry filters, so an entry-filter refusal is journalled even while paused or when a limit would have refused it anyway.
- `idea.time` is the tick time on the live path (engine.py:664) and the candle start at candle close. `entry_price` is the strategy's own entry (sell price, for buys too).
- The replay check (`trading/replay_check.py`) drives the same `Trading` class, so anything added in `_place` is replayable.

### Data available inside `Trading._place` (engine.py:321)
| Object | What it gives |
|---|---|
| `idea` | strategy, direction, time, entry_price, state / state_direction / trend_type / state_since, direction_rule, steps; context: `signal`, `rejection_candle`, `furthest`, `rejection_close`, `level`, `level_name`, `stop_price`, `once_a_day`, breakout `base_low` / `base_high` / `base_since` / `breakout_candle` / `day_open`, `past_level_pips` |
| `self.store` | candle store, 5m / 1h / 4h etc. (`MemoStore(self.store)` used for filters) |
| `self.tracker` | analyser StateTracker: `machine.now` (state), `history` (5m features incl. Bollinger upper/middle/lower), `changes`, `watcher` (the analyser's rejection setups at levels) |
| `self.runner` | `levels_at(t)` → `levels.current.LevelList` (pivot, R1–R3, S1–S3, round numbers 00/50, previous day H/L, London/NY session H/L, hourly turning H/L, groups / lined_up); `pivot_at`; `pullback.hourly` (hourly 8/13/20 reader); strategy objects; `runner.stp` = STP FileSource **only while STP_AUTHORISES_ENTRIES is on, else None** (replay.py:101-102, stp/source.py:348) |
| `self.manager.trades` | open managed trades (strategy, direction, fill, stop_pips, stop_level, best, opened_at) |
| `self.sender` | `open_trades()` (incl. unresolved sent orders), `used_signals()`, `used_once_a_day()`, `funds`, `unresolved` |
| other | `self.trend_watch` (slow-grind trend day); `td` = trend_day_at; `self.calendar` (news); `self.partial` (forming 5m candle), `self._last_tick` (live bid/offer); `self.s` (all settings) |

With the gate off, STP's opportunities are NOT loaded in the trading process. A new check that needs them must build `stp.source.FileSource(settings)`, which reads `planner.folder/GBPUSD/current.json`. The live file has `opportunities[*]` with `trade`, `status` (WAITING / ACTIVE = "Watch & Wait"), `entry_zone{low,high,class,levels[]}`, `invalidation{zone_break_close,structure_break_close}`, `destinations`, `written_utc`, `current`, etc. A check could reuse `stp.authorise.authorise`'s freshness and zone logic (stp/authorise.py:144-217).

### How `decisions.jsonl` is written
`Book.decision(kind, t, **data)` (records/book.py:131) appends `{"time_utc", "kind", "paper"} | data` as one JSON line to `records.folder/GBPUSD/decisions.jsonl`.

Patterns used in `_place`:
- `"idea"` (engine.py:270 / 667): strategy, direction, entry_price, allowed, blocked_by, state, plus already_sent_live or live.
- `"STP refused"` (engine.py:330): strategy, direction, idea_time, entry_price, why. Then `"order"` with result "STP refused".
- `"entry filter refused"` (engine.py:349): strategy, direction, idea_time, entry_price, rule, why, details. Then `"order"` (engine.py:355) with `result: "entry filter refused"`, `reference: ""`, `reasons: ["<rule>: <why>"]`, `level: null`, returning `Result(False, "entry filter refused", reasons=[...])`.
- `"order"` (engine.py:363): result = opened / safety refused / refused / not found, plus reference, reasons, level.
- Safety refusals also go to `orders.jsonl` (`OrderSender._record`, sender.py:227) as `event:"safety refused"`.

Live example (27 Nov 17:34:36): `entry filter refused` level reversal BUY, rule "RSI stretch", details {rsi3_5m 89.0, ...}, then `order` with result "entry filter refused".

**A new check's refusals journalled the same way:** `self.book.decision("<name> refused", self.now(), strategy=, direction=, idea_time=idea.time, entry_price=, rule=, why=, details=)`, then `r = Result(False, "<name> refused", reasons=[...])` and `self.book.decision("order", ...)` exactly as engine.py:354-357. When allowed, append a line to `idea.steps` (it goes to trades.jsonl "steps").

### Best insertion point for a common "structural coherence" check
**`Trading._place`, after the entry-filter verdict is allowed (after engine.py:359) and before `day_directions` / `self.sender.place` (engine.py:360-361).**
- Every strategy passes here, once per try, on both the live path and the candle-close path, and in replays.
- Everything listed above is in reach: open trades in both directions via `self.sender.open_trades()` / `self.manager.trades`, analyser state, levels, candles, live tick, and STP via FileSource.
- Refusals inherit the "one try per candle" semantics.

Alternatives considered:
- (i) A new rule inside `strategies/entry_filters.check`. You get automatic "entry filter refused" journalling, the STP `bypass` plumbing and the `checked` steps. But `check()` receives only settings, store, idea and trend: no open trades, no tracker, no STP. You would have to widen its signature.
- (ii) Inside `safety.rules.decide`. It does see `open_trades`, but only as (strategy, direction, opened_at, stop_pips, size), with no prices. It would mix structure into the "safety" category. Its refusals show as "safety refused".
- (iii) `common.allowed`. Too early: it runs on peek copies on every tick, and refusals there are not journalled live.
- Caveat for an insertion before `sender.place`: the pause, limit and funds checks come after it, so the new check's refusals will also appear for ideas the safety rules would have refused anyway. The same is true of the entry filters today.

---

## 2. Per-strategy inventory

Legend: **St** = analyser-state gating (common.py:78-96, `ALLOWED_IN`); **DR** = direction rule (pivot + 5m 100 EMA, only strategies NOT in `NO_DIRECTION_RULE`, common.py:74); **R1** = hourly context, **R2b** = RSI stretch, **R3** = counter-trend tiring (entry_filters.py:96-103 exemption lists); **Hours / news** = `common.may_open` (common.py:147); **Lim** = safety `_limits` (safety/rules.py:111); **R9 / R10 / R11** = one view / once a day / one signal.

### 2.1 Summary table: admission after the signal (production values)

| Strategy | St | DR | R1 | R2b | R3 | R3/S3 | Hours | Big-news window | Per-strategy limit | In "max 5"? | R9 | R10 | R11 key in prod | STP gated (if switch on) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EMA pullback | **TREND only, trend dir** (TREND_ONLY on) | **yes** | yes | yes | no | **yes** | 06:00–20:30 (TRADING_HOURS on) + no 21:55–22:15; Fri ≥20:30 | allowed | 1 (ONE_AT_A_TIME on) | not counted | no | no | none | no |
| Slow grind | TREND, trend dir | no | **yes** | exempt | no | no | own: not 20:30–24:00, not first 15 min of week, not 21:55–22:15 (**not 06:00 start**) | allowed | 1 | yes | no | no | none | no |
| Bollinger bounce (hourly) | none (WITHOUT_HINDRANCE) | no | yes | yes | yes | no | 06:00–20:30 | refused | 1 each way | not held back | no | no | **yes** (signal_context) | yes |
| Bollinger bounce 5m | TREND against dir; POSSIBLE_REVERSAL any | no | yes | yes | yes | no | 06:00–20:30 | refused | 1 each way, 2 total | yes | no | no | **none** | yes |
| Level reversal | any except CONSOLIDATION | no | yes | yes | yes | no | 06:00–20:30 | refused | 1 | yes | **yes** (vs trend dir) | no | **none** | yes |
| Range trade | RANGING any | no | yes | yes | no | no | 06:00–20:30 | refused | 1 | yes | no | no | none | no |
| Breakout | EMERGING/TREND, trend dir | no | **exempt** | exempt | no | no | 06:00–20:30 | allowed | 1 | yes | no | no | none | no |
| Asian range breakout | none | no | exempt | exempt | no | no | 06:00–20:30 (+ own 07–10 window) | refused | 1 each way | not held back | never | 1 each way/day | none | no |
| Session sweep | none | no | yes | exempt | yes | no | 06:00–20:30 | refused | 1 each way | not held back | **yes** (switch on) | 1 per level/day | **yes** | no |
| NY open reversal | none | no | yes | yes | yes | no | 06:00–20:30 (+ 13:30–15:00 window); no trade if big news at 13:30 | refused | 1 each way | not held back | **yes** (switch on) | 1/day | **yes** | no |

Notes:
- R1 refuses only an entry within 5 pips (inclusive) of the **daily pivot or the hourly 50 EMA** against an hourly DOWN/UP context. Context = last two hourly swing highs (lows) lower (higher), 2 candles each side, AND the last hourly close below (above) the 50 EMA, AND the 50 EMA falling (rising) over 6 hours (entry_filters.py:141-171, 266-291). Far from those two lines, a counter-context trade passes.
- R2b: 5m RSI(3), Wilder, at the last finished candle; no SELL <30, no BUY >70; not applied in the slow-grind trend-day direction (entry_filters.py:314-335).
- R3: applies only when the idea's analyser state is TREND or EMERGING (COUNTER_TREND_EMERGING on) and the trade is against it. Allowed if the hourly MACD 35/45/30 histogram has crossed zero (only if it was on the trend's side since the state began, HOURLY_CONFIRMED) or is shrinking while on the trend's side, or the 5m histogram is across zero onto the bounce's side (entry_filters.py:337-398).
- R9 (safety/rules.py:196-209): only "reversal" trades, i.e. level reversal (+ sweep and NYOR while ONE_SIGNAL_ONE_TRADE is on) **against the analyser's trend direction**. Refused against a strong-push TREND, or against the day's direction (big-news expected direction, analyser trend day, Monday after a ≥80-pip Friday; analyser/day_direction.py).
- R11 key: `context["signal"]` = "<dir> <rejection candle start>". Only the hourly bounce, session sweep and NYOR set it (via `common.signal_context`). **Level reversal and BB 5m set no `signal`.** They set `rejection_candle` only when STP_AUTHORISES_ENTRIES is on (bollinger_bounce_5m/strategy.py:52, level_reversal/strategy.py:129), and STP's authorise then adds `signal` (engine.py:338). So in production, rule 11 does not cover them.
- `opens_at_next_candle` (common.py:57-65): hourly bounce, the 3 session strategies, and breakout (PULLBACK_ENTRY on). These open on the next candle's first live price and are never sent late.

### 2.2 Signal, entry, stop, take profit, structure used / ignored

**EMA pullback** (`strategies/ema_pullback/strategy.py`)
- Signal:
  - Step 0, hourly trend (`HourlyTrendReader.at` :79): hourly 8/13/20 EMAs in order and each moving one way since the previous hour; slope over 3 h ≥0.16 pips/h; gap minimums NOT checked (NO_HOURLY_GAP_MIN on, :101); each EMA higher (lower) than 3 h before (SLOPE_DIRECTION on, :111).
  - Touch: a 5m candle's low (high) reaches the previous 5m 8 EMA, and the touch candle closes on the right side of the 21 EMA (:197-212).
  - Entry with ENTRY_PULLBACK_CANDLE on: a later candle trades strictly beyond the touch candle's high (low), or opens beyond it (:213-220, :162-183).
  - Cancelled by a close beyond the 21 EMA; expires after 20 min.
  - RECHECK_AT_OPEN on: step 0 is re-run at entry and cancels the setup on failure (:168-178).
- Direction: the hourly trend's.
- Stop: STOP_LOSS_PIPS_EMA_PULLBACK = 12 pips from entry (common.py:362).
- Take profit: `ema_pullback.take_profit_pips` 30; becomes 100 on a big-news day or in the analyser trend-day direction (common.py:310-332).
- Admission: see table. EMA pullback is the only strategy under the direction rule (needs buy side = price above the daily pivot AND the 5m 100 EMA). Also R3/S3: no BUY at or above the day's R3, no SELL at or below S3 (entry_filters.py:400-416).
- Structure used: hourly 8/13/20 and 5m 8/21 EMAs; in the filters, daily pivot, 5m 100 EMA, hourly 50 EMA and swings (R1), R3/S3.
- Ignored: every other level (R1/R2, S1/S2, round numbers, previous day H/L, session H/L, turning levels), Bollinger, STP zones, distance to the next opposing level.

**Slow grind** (`strategies/slow_grind/strategy.py`)
- Signal: a "pause" of ≥2 consecutive candles without a new low (high), each closing below (above) the 5m 21 EMA. Entry when price breaks the pause's lowest low (highest high), at that price or the candle's open (:85-101). A close beyond the 21 EMA cancels. No time limit.
- Direction: both are watched; admission keeps only the TREND direction.
- Stop: `slow_grind.stop_loss_pips` 15.
- Take profit: 20 (100 on a big-news or trend day in its direction). Profit lock 15/10 (after entry).
- Admission: TREND in its direction; R1 applies (not exempt); RSI exempt; own hours (common.py:171-185). The trades also drive Johnny's trend day (entry_filters.py:420+).
- Structure used: 21 EMA and local lows/highs only; pivot and hourly 50 EMA via R1.
- Ignored: all levels, Bollinger, STP.

**Bollinger bounce, hourly** (`strategies/bollinger_bounce/strategy.py`)
- Signal: a 5m candle's high (low) goes >3 pips beyond the forming hourly Bollinger(20,2) upper (lower) band (`HourlyChart.band_at` with the high as close), and the same candle is red (green): the rejection candle. Confirmation: a later close below (above) the rejection low (high) within 3 candles. A break of the rejection high (low) cancels. Spread spikes >3 pips are ignored (:84-148).
- Entry: the next candle's open, sell price (:88-95).
- Stop: STOP_LOSS_PIPS 12.
- Take profit: TAKE_PROFIT_PIPS 100. Trail 12/3 candles (after entry).
- Context: `signal`, `rejection_candle`, `furthest`, `rejection_close`.
- Admission: no state or direction check (WITHOUT_HINDRANCE, common.py:54, 388); R1, R2b, R3; big-news windows refused; 1 per direction; not held back by max 5; R11 applies.
- Structure used: hourly Bollinger only; pivot and hourly 50 EMA via R1.
- Ignored: levels module, pivots S/R, STP zones (the gate is off), 5m band.

**Bollinger bounce 5m** (`strategies/bollinger_bounce_5m/strategy.py` + `rejection/watch.py`, design_only watcher)
- Signal ("bounce" version):
  - A pierce of the 5m Bollinger band (real pierce) or a **level** from `levels.current.build` (any type; within 3 pips counts, watch.py:211-232).
  - The reversal candle is the first red (green) candle within 3 candles.
  - Confirmation: a close beyond the reversal candle's low (high) within 3 candles.
  - Trigger: price breaks the confirmation candle's low (high); the trigger price is the entry.
  - Price beyond the reversal candle's high (low) cancels.
- Stop: STOP_LOSS_PIPS 12. Take profit: 100.
- Admission: state TREND against its direction, or POSSIBLE_REVERSAL either way (common.py:89). With TREND_ENDS_IN_CONSOLIDATION on, POSSIBLE_REVERSAL can only come from EMERGING (analyser/states.py:319-336). R1, R2b, R3. Limit 1 per direction / 2 total (safety/rules.py:124-131). **No R11 key in prod.**
- Structure used: the 5m band and all bot levels (pivot, R/S 1–3, round 00/50, previous day H/L, London/NY session H/L in UTC, hourly turning levels).
- Ignored: STP zones (only added while the gate is on, stp/levels.py), hourly structure, room to the next level.

**Level reversal** (`strategies/level_reversal/strategy.py`)
- Signal: the same watcher bounce trigger, kept only if the setup pierced an **S2, R2 or round number on a 100-pip multiple** (STP zone levels too, only with the gate on, :56-68). The furthest price past the level, from the pierce to the confirmation candle, must be ≤ the allowance: R2/S2 12 pips, round number 5 (:88-115). S2/R2 are taken before round numbers.
- Entry: the watcher's trigger price (confirmation candle low/high, or the open if it opened past it).
- Stop: a **price**, furthest ± 6 pips (:116-117). `order_for` converts it to pips from the entry (safety/rules.py:97-101). At send it becomes a distance from the live bid/offer, refused if price is already past it (sender.py:833-849). Not capped.
- Take profit: `level_reversal.take_profit_pips` 20.
- Context: `level`, `level_name`, `furthest`, `past_level_pips`, `stop_price` (+ `rejection_candle` only with STP on).
- Admission: any state except CONSOLIDATION; R1, R2b, R3; R9 when against the analyser trend direction; **no R11 key in prod**.
- Structure used: S2, R2, 00-round numbers; the furthest excursion.
- Ignored: other levels as triggers (other levels may appear in its pierced list, but they do not qualify it), STP zones, hourly structure, room to the next level.

**Range trade** (`strategies/range_trade/strategy.py`, watcher "range" version)
- Signal: a 5m candle pierces the 5m Bollinger band; the next candle is red (green), the rejection candle; trigger during the candle after it, through the rejection low (high); cancelled through the high (low) first. **Levels are not used in the range version** (watch.py:218 `if version == BOUNCE`).
- Stop: 12. Take profit: 100. After entry: half close at the opposite band; closed on a confirmed level rejection (common.py:282; the only strategy with that).
- Admission: RANGING only; R1, R2b.
- Structure used: 5m Bollinger band and the analyser's ranging state.
- Ignored: levels, STP.

**Breakout** (`strategies/breakout/strategy.py`, PULLBACK_ENTRY on → `strategies/pullback.py`)
- Signal: the analyser change into EMERGING with reason "broke out of the range/consolidation" (:236-238); that candle is the breakout candle.
- Entry with the pullback on: wait up to 6 candles for a low (high) touching the 5m 8 EMA and then a close back beyond it. A close beyond the 21 EMA against it cancels. Opens at the next candle's open, only if the entry is beyond the day's 00:00 UK open in its direction (:264-278).
- Stop: `breakout.stop_loss_pips` 6. Take profit: 50.
- Context: `broke_out_of`, `base_low`, `base_high`, `base_since`, `breakout_candle`, `day_open` (recorded only).
- Admission: EMERGING/TREND in the trend direction (checked at entry); exempt from R1 and R2b; news allowed.
- Structure used: analyser state change, 5m 8/21 EMA, the day open.
- Ignored: levels, Bollinger, STP, room to the next level. The base range is recorded only.

**Asian range breakout** (`strategies/asian_range_breakout/strategy.py`)
- Signal: Asian range H/L, 00:00–07:00 UK. A 5m close beyond it between 07:00 and 10:00. With PULLBACK_ENTRY on, only the first close each way per day starts a wait (8-EMA pullback and close back, within 6 candles, 21-EMA cancel). Opens at the next candle's open (:70-106).
- Stop: 12. Take profit: 100. Trail 12/3.
- Context: `once_a_day` = "Asian range breakout <dir> <day>".
- Admission: no state or direction check; exempt from R1 and R2b; not under R3; never counted by R9; R10 one each way per day; 1 per direction. **It has the fewest admission checks of all ten strategies.**
- Structure used: the Asian range, 8/21 EMA.
- Ignored: everything else.

**Session sweep** (`strategies/session_sweep/strategy.py`)
- Signal: own UK-time levels, Asian H/L (00–07, used from 07:00) and London H/L (07–12, used from 12:00). Price goes ≥3 pips beyond a level; a candle closes back inside (the rejection candle); confirmation through the rejection low (high) within 3 candles; a break of the rejection high (low) cancels (`strategies/sessions.py` confirm_step). Opens at the next candle's open (:209-258).
- Stop: a price, max(furthest + 1 pip, entry + 12 pips) for a sell (mirror for a buy) (:201-207). Converted to a distance from the live price at send.
- Take profit: 100. Trail 12/3.
- Context: `stop_price`, `furthest`, `level_name`, `level`, `once_a_day` per level per day, `signal`.
- Admission: no state or direction check; R1; RSI exempt; R3; R9 (switch on); R10; R11.
- Structure used: its own session H/L (not the levels module's UTC sessions).
- Ignored: pivots, other levels, STP.

**New York open reversal** (`strategies/new_york_open_reversal/strategy.py`)
- Signal: the move from the 07:00 open to the close before 13:30 UK is ≥30 pips. Between 13:30 and 15:00, a candle against the move (red after a rise), then confirmation through its low (high) within 3 candles, inside the window. Opens at the next candle's open (:341-381).
- Stop: 12. Take profit: 100. Trail 12/3.
- Context: `once_a_day` per day, `signal`.
- Admission: no state or direction check; R1, R2b, R3; no trade if big news is released at 13:30 that day (common.py:204-207); R9 (switch on); R10; R11.
- Structure used: the session move only.
- Ignored: levels, STP.

### 2.3 STP gate (inactive in production: STP_AUTHORISES_ENTRIES=off)
- `stp.gate.gated` (stp/gate.py:9) = switch on AND strategy in `[stp_authorisation].strategies` (hourly bounce, BB 5m, level reversal).
- When gated:
  - `common.allowed` skips the analyser-state check (common.py:390).
  - Their candidates carry `rejection_candle`.
  - The live STP zones (WAITING/ACTIVE opportunities: zone edges + fixed levels inside) are added to the **strategies' copy** of the levels (stp/levels.py; replay.py:104-111). So BB 5m and level reversal can trigger off STP zones (level reversal allowance up to the zone's far edge + 3 pips, level_reversal/strategy.py:103-111).
- `stp.authorise.authorise` (engine.py:325-344; stp/authorise.py:144) refuses unless ALL of these hold:
  1. STP_OPPORTUNITIES, STP_BIDIRECTIONAL and ONE_SIGNAL_ONE_TRADE are on.
  2. `current.json` is readable, `written_utc` ≤10 min old, `current` is true, and the live tick (or the last 5m candle) ≤10 min old.
  3. The idea's rejection candle `interacts` with the `entry_zone` of a live opportunity (status WAITING or ACTIVE) **in the same direction**.
  4. Catch-up: no primary-destination touch, hourly zone-break close or 4h structure-break close since the tracker last looked.
  5. The entry is not at or beyond `zone_break_close`.
- Binding: the oldest lineage, then the strongest zone class, then the nearest.
- Adds `signal` = existing|`<lineage>#t<n>`, so rule 11 applies per lineage and test. Bypasses R1, R2b, R3 (entry_filters.py:261-266) and R9 (safety/rules.py:199).
- Not gated, so never checked against STP even with the switch on: EMA pullback, slow grind, range, breakout, ARB, sweep, NYOR. **No strategy refuses an entry INTO an opposite-direction STP zone.**

---

## 3. Opposing positions (BUY while a SELL is open)

- **Permitted across strategies.** Nothing in the path compares a new idea's direction with open positions of other strategies:
  - `safety._limits` counts only same-strategy trades (and the total of 5).
  - `_risk` sums stop × size regardless of direction.
  - Rule 9 compares with the analyser trend and the day's direction, not with positions.
  - The orders are sent with `"forceOpen": True` (sender.py:882), so IG opens a separate opposite position rather than netting. (Assumption: the IG account is in hedging mode. Not verified here.)
  - The trade manager closes nothing when a new trade opens (engine.py:25 docstring).
- **Same strategy, both ways at once.** Permitted for the hourly bounce and the 3 session strategies (1 per direction, safety/rules.py:119-123) and BB 5m (1 per direction, 2 total, :124-131). Not permitted for the others (1 total per strategy). EMA pullback is limited to 1 only because EMA_PULLBACK_ONE_AT_A_TIME is on.
- Only indirect brakes: the analyser-state gating (e.g. EMA pullback, slow grind and breakout only in the trend direction; BB 5m only against a TREND), R1 near pivot / hourly 50 EMA, R3 for reversal types against the analyser trend. None of these looks at open trades.
- Example: during a TREND down, an EMA pullback SELL can be open while a level reversal BUY (allowed in TREND, R3 permitting) or an hourly-bounce BUY (no state check) opens beside it.

---

## 4. Points flagged as uncertain or notable
1. Rule 11 coverage in production: level reversal and BB 5m carry no `signal` key, so "one signal, one trade" does not apply to them while STP is off. Their de-duplication is the per-strategy limit plus the watcher's "same candle and direction gives one idea" (level_reversal/strategy.py:78-86).
2. Live blocked ideas (common.check) are not journalled until candle close; live refused ideas (STP, filters, safety) are journalled.
3. The analyser-state check uses the state after the **previous** finished candle (replay.py:193, 241). The entry filters use the last candle finished by `idea.time`.
4. Session H/L differ by module: `levels.current` uses UTC 07–12 and 12–21, while the session sweep uses its own UK-time 00–07 and 07–12 ranges.
5. The level reversal's stop has no maximum distance. The session sweep's has a 12-pip minimum and no maximum.
6. With `STP_AUTHORISES_ENTRIES` off, `self.runner.stp` is None. A new structural check that wants STP must read `current.json` itself (FileSource), and should copy authorise's freshness checks (`written_utc`, `current`).
7. IG hedging vs netting mode is not checked in code; `forceOpen=True` is assumed to open independent positions.
