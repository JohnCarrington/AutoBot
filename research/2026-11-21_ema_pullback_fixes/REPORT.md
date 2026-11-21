# EMA pullback: trading hours and one trade at a time (build only)

Johnny's brief, 21 November 2026. Branch `ema-pullback-hours-one-trade`, built from the live commit `02f6c7e`. Not merged into main, no service restarted, the live bot and every other branch left alone. Both fixes are off unless switched on in `.env`.

## 1. Branch and commits

Branch: `ema-pullback-hours-one-trade` (from `02f6c7e`).

| Fix | Commit | One-line message |
|---|---|---|
| 1 | `e5eb882` | EMA pullback: trading hours 06:00-20:30 UK and closed at 20:30 every day, behind EMA_PULLBACK_TRADING_HOURS (off) |
| 2 | `57a1a9f` | EMA pullback: one trade open at a time, behind EMA_PULLBACK_ONE_AT_A_TIME (off) |

This report is a third commit on the same branch (documentation only).

## 2. Fix 1: trading hours and no overnight trades

**New .env setting:** `EMA_PULLBACK_TRADING_HOURS` (`on` or `off`; off if left out).

**What it does while on:**
- **Opening:** a new EMA pullback trade opens only from 06:00 to 20:30 UK. This is the same check every other strategy uses: `NEW_TRADES_FROM`/`NEW_TRADES_UNTIL` in `.env`, read on the UK clock (`hours.timezone = "Europe/London"`, so GMT in winter, BST in summer). I moved that check into one shared function, `trading_hours_reasons`. The other strategies now call that function too, with no change in what they do.
- **Closing:** every open EMA pullback trade is closed at `hours.close_all_trades_at` (20:30) UK every day, by the same scheduled close the other strategies use (`forced_close_at`). Until now the EMA pullback was closed only on Friday.
- **Unchanged:** the 21:55–22:15 rollover pause stays as it is. Nothing about stops, take profits or other trade management changes.

**Files changed:**

```
 .env.example                                       |   3 +
 config/switches.py                                 |   8 +-
 docs/SETTINGS.md                                   |   1 +
 strategies/common.py                               |  31 +++-
 tests/functional/README.md                         |   1 +
 .../functional/test_ema_pullback_trading_hours.py  | 164 +++++++++++++++++++++
 6 files changed, 199 insertions(+), 9 deletions(-)
```

**Code diff (whole commit):**

```diff
diff --git a/.env.example b/.env.example
index 87c9319..81bbfa1 100644
--- a/.env.example
+++ b/.env.example
@@ -54,3 +54,6 @@ PLANNER_OBSERVE=off
 # One signal, one trade (safety rule 11), off if left out: two strategies opening the same way from the same
 # rejection candle give one trade; also the session sweep and New York open reversal under one view at a time.
 ONE_SIGNAL_ONE_TRADE=off
+# The EMA pullback's hours, off if left out: on = new EMA pullback trades only from NEW_TRADES_FROM to
+# NEW_TRADES_UNTIL UK, and every open EMA pullback trade closed at 20:30 UK every day (nothing held overnight).
+EMA_PULLBACK_TRADING_HOURS=off
diff --git a/config/switches.py b/config/switches.py
index b13d490..f587eae 100644
--- a/config/switches.py
+++ b/config/switches.py
@@ -14,6 +14,10 @@
                               candle and direction; the session sweep and New York open reversal under one view at
                               a time (safety/rules.py, rules 9 and 11)
   PLANNER_OBSERVE             on or off (off if left out): the Structural Trade Planner (planner/), OBSERVE ONLY
+  EMA_PULLBACK_TRADING_HOURS  on or off (off if left out; owner, 21 November 2026): new EMA pullback trades only
+                              within the trading hours NEW_TRADES_FROM to NEW_TRADES_UNTIL (UK clock), as the other
+                              strategies, and every open EMA pullback trade closed at hours.close_all_trades_at (20:30)
+                              UK every day, not only on Friday; the 21:55-22:15 rollover pause stays as it is
   BOUNCE_ONLY_NEAR_TIMES      on or off (off if left out): while on, a Bollinger bounce opens only within
                               bounce.near_times_within_minutes (60) of bounce.near_times (10:00, 14:00,
                               16:00 UK) in settings.toml
@@ -97,6 +101,7 @@ SWITCHES: dict[str, tuple[str, Callable[[str], Any]]] = {
     "BOUNCE_ONLY_NEAR_TIMES": ("bounce_only_near_times", _on_off),
     "PLANNER_OBSERVE": ("planner_observe", _on_off),
     "ONE_SIGNAL_ONE_TRADE": ("one_signal_one_trade", _on_off),
+    "EMA_PULLBACK_TRADING_HOURS": ("ema_pullback_trading_hours", _on_off),
     "STRATEGY_RANGE_TRADE": ("range_trade", _on_off),
     "STRATEGY_BREAKOUT": ("breakout", _on_off),
     "STRATEGY_LEVEL_REVERSAL": ("level_reversal", _on_off),
@@ -110,7 +115,8 @@ SWITCHES: dict[str, tuple[str, Callable[[str], Any]]] = {
 }
 
 # Switches that may be left out of .env, and their value then (owner, 15 November 2026: both off by default).
-OPTIONAL: dict[str, str] = {"BOUNCE_ONLY_NEAR_TIMES": "off", "PLANNER_OBSERVE": "off", "ONE_SIGNAL_ONE_TRADE": "off"}
+OPTIONAL: dict[str, str] = {"BOUNCE_ONLY_NEAR_TIMES": "off", "PLANNER_OBSERVE": "off", "ONE_SIGNAL_ONE_TRADE": "off",
+                            "EMA_PULLBACK_TRADING_HOURS": "off"}
 
 
 def read_switches(path: Path) -> tuple[dict[str, Any], list[str]]:
diff --git a/docs/SETTINGS.md b/docs/SETTINGS.md
index 0032b55..ba8fd5e 100644
--- a/docs/SETTINGS.md
+++ b/docs/SETTINGS.md
@@ -467,6 +467,7 @@ These live in `.env` (not in `config/settings.toml`), next to the IG secrets, so
 | `STRATEGY_BOLLINGER_BOUNCE` | The hourly-pierce Bollinger band bounce (15 November 2026; `strategies/bollinger_bounce`), `on` or `off`. | on |
 | `STRATEGY_BOLLINGER_BOUNCE_5M` | The first build's Bollinger band bounce (5-minute band and levels; `strategies/bollinger_bounce_5m`, recorded as "Bollinger bounce 5m"), `on` or `off`. Kept and renamed alongside the hourly-pierce bounce (owner, 19 November 2026). Required. | on |
 | `ONE_SIGNAL_ONE_TRADE` | Stage 3 of the analyser control (design 6), `on` or `off`. On: two strategies opening the same way from the same rejection candle give one trade, the first to trigger (the others refused: "same signal already traded by ..."); the session sweep and the New York open reversal come under one view at a time. Off if left out of `.env`. **Owner's switch, off, 18 November 2026.** | off |
+| `EMA_PULLBACK_TRADING_HOURS` | The EMA pullback's hours, `on` or `off`. On: a new EMA pullback trade opens only within the trading hours `NEW_TRADES_FROM` to `NEW_TRADES_UNTIL` (UK clock: GMT in winter, BST in summer), the same check as every other strategy, and every open EMA pullback trade is closed at `hours.close_all_trades_at` (20:30) UK every day, not only on Friday, so none is held overnight. The 21:55-22:15 rollover pause (`ema_pullback.rollover_no_new_trades_*`) stays as it is. Off (the EMA pullback's own hours: any time except Friday after 20:30 and the rollover; closed 20:30 UK on Friday only) if left out of `.env`. **Owner, 21 November 2026.** | off |
 | `PLANNER_OBSERVE` | The Structural Trade Planner (`planner/`), `on` or `off`. On: after each new 5-minute candle the price service starts the planner in a separate, low-priority process (never on the price feed's thread): it re-plans on each completed hourly candle and checks its zone on each 5-minute candle, writing `planner.folder`. **Observe only:** it never authorises, refuses, opens, changes or closes a trade, and the dashboard panel says so. Off if left out of `.env`. **Off until the owner approves installation.** | off |
 | `STRATEGY_RANGE_TRADE` | The range trade strategy, `on` or `off`. | on |
 | `STRATEGY_BREAKOUT` | The breakout strategy (design 3.5), `on` or `off`. The bot refuses to start with it on while `breakout.stop_loss_pips` or `breakout.take_profit_pips` is 0. Switched on by the owner, 7 November 2026. | on |
diff --git a/strategies/common.py b/strategies/common.py
index 835d275..68d7f97 100644
--- a/strategies/common.py
+++ b/strategies/common.py
@@ -33,7 +33,7 @@ from decimal import Decimal
 from typing import Any
 
 from analyser.direction import BUY_SIDE, SELL_SIDE, decide
-from analyser.states import CONSOLIDATION, DOWN, EMERGING, POSSIBLE_REVERSAL, RANGING, TREND, UP
+from analyser.states import CONSOLIDATION, DOWN, EMERGING, POSSIBLE_REVERSAL, RANGING, TREND, UP, switch_on
 
 SLOW_GRIND, EMA_PULLBACK, BOLLINGER_BOUNCE, RANGE_TRADE, BREAKOUT, LEVEL_REVERSAL = (
     "slow grind", "EMA pullback", "Bollinger bounce", "range trade", "breakout", "level reversal")
@@ -135,7 +135,9 @@ def may_open(settings: Any, pair: str, strategy: str, t: datetime, calendar: lis
     EMA pullback: any time the market is open, big-news windows included, except after
     hours.close_all_trades_at (20:30) UK on Friday, so none is held over the weekend (owner,
     7 November 2026), and from ema_pullback.rollover_no_new_trades_from (21:55) to
-    ema_pullback.rollover_no_new_trades_until (22:15) UK, the rollover (owner, 13 November 2026).
+    ema_pullback.rollover_no_new_trades_until (22:15) UK, the rollover (owner, 13 November 2026); while
+    EMA_PULLBACK_TRADING_HOURS is on, also only within the trading hours NEW_TRADES_FROM to NEW_TRADES_UNTIL UK
+    (trading_hours_reasons, as every other strategy; owner, 21 November 2026).
     Slow grind (owner, 8 November 2026): any time the market is open, big-news windows included,
     except from hours.close_all_trades_at (20:30) to midnight UK every day, in the first
     slow_grind.week_open_no_new_trades_minutes (15) after the week opens, and from
@@ -176,11 +178,10 @@ def may_open(settings: Any, pair: str, strategy: str, t: datetime, calendar: lis
         if ep.rollover_no_new_trades_from <= lt.time() < ep.rollover_no_new_trades_until:
             reasons.append(f"from {ep.rollover_no_new_trades_from:%H:%M} to {ep.rollover_no_new_trades_until:%H:%M} UK "
                            f"(the rollover): no new {strategy} trade")
+        if switch_on(settings, "ema_pullback_trading_hours"):     # the other strategies' trading hours (21 Nov 2026)
+            reasons += trading_hours_reasons(settings, t)
         return reasons
-    lt = t.astimezone(ZoneInfo(tz) if isinstance(tz, str) else tz).time()
-    sw = settings.switches
-    if not (sw.new_trades_from <= lt < sw.new_trades_until):
-        reasons.append(f"outside the trading hours {sw.new_trades_from:%H:%M} to {sw.new_trades_until:%H:%M} UK")
+    reasons += trading_hours_reasons(settings, t)
     if strategy == BREAKOUT:
         return reasons
     windows = no_new_trades(settings, pair, t, calendar)
@@ -193,20 +194,34 @@ def may_open(settings: Any, pair: str, strategy: str, t: datetime, calendar: lis
     return reasons
 
 
+def trading_hours_reasons(settings: Any, t: datetime) -> list[str]:
+    """The trading hours: a new trade only from NEW_TRADES_FROM up to NEW_TRADES_UNTIL (.env), UK clock (GMT in
+    winter, BST in summer). Shared by every strategy that keeps them (may_open)."""
+    from zoneinfo import ZoneInfo
+    tz = settings.hours.timezone
+    lt = t.astimezone(ZoneInfo(tz) if isinstance(tz, str) else tz).time()
+    sw = settings.switches
+    if not (sw.new_trades_from <= lt < sw.new_trades_until):
+        return [f"outside the trading hours {sw.new_trades_from:%H:%M} to {sw.new_trades_until:%H:%M} UK"]
+    return []
+
+
 def forced_close_at(settings: Any, strategy: str, opened: datetime) -> datetime:
     """When a trade opened at `opened` is closed by the clock: hours.close_all_trades_at (20:30) UK,
     the first one after it opened; for the EMA pullback and the breakout, the first FRIDAY 20:30 UK
     after it opened. (A slow grind trade never opens between 20:30 and midnight UK, so it is
-    always closed at 20:30 the day it opened.)"""
+    always closed at 20:30 the day it opened.) While EMA_PULLBACK_TRADING_HOURS is on (owner, 21 November 2026), the
+    EMA pullback is closed at 20:30 UK every day, as every other strategy."""
     from datetime import datetime as dt, timedelta, timezone
     from zoneinfo import ZoneInfo
     tz = settings.hours.timezone
     uk = ZoneInfo(tz) if isinstance(tz, str) else tz
     lt = opened.astimezone(uk)
+    own = strategy in OWN_HOURS and not (strategy == EMA_PULLBACK and switch_on(settings, "ema_pullback_trading_hours"))
     for k in range(0, 8):
         day = lt.date() + timedelta(days=k)
         cut = dt.combine(day, settings.hours.close_all_trades_at, tzinfo=uk)
-        if cut > lt and (strategy not in OWN_HOURS or day.weekday() == 4):
+        if cut > lt and (not own or day.weekday() == 4):
             return cut.astimezone(timezone.utc)
     raise AssertionError("no close found within a week")
 
diff --git a/tests/functional/README.md b/tests/functional/README.md
index 8621409..65a98da 100644
--- a/tests/functional/README.md
+++ b/tests/functional/README.md
@@ -6,3 +6,4 @@ Tests that check the bot behaves the way a trader expects (for example, "no new
 - `test_rejection_real_candles.py`: the rejection at the daily pivot around midnight on 5 November, and the turn at 1.3446 to 1.3450 around 12:00 (`docs/REJECTION.md`).
 - `test_analyser_real_candles.py`: the direction is sell side at 13:00 on 6 November, and the 5-minute 100 EMA, pivot and direction at 06:00, 09:00, 13:00 and 16:00 that day (`docs/ANALYSER.md`).
 - `test_market_states_real_candles.py`: the five market states on 5 and 6 November: the midnight pivot rejection starting the downtrend, consolidation before 06:40, the two strong pushes, the possible reversal around 10:15, sell side at 13:00, and a restart at 09:00 giving exactly the same states (`docs/ANALYSER.md`). The S2 flat spell (11:30 to 12:45) is a known shortfall, not tested (design section 12).
+- `test_ema_pullback_trading_hours.py`: `EMA_PULLBACK_TRADING_HOURS` (owner, 21 November 2026), through the live engine with a pretend IG: an EMA pullback trade open at 20:29 UK is closed at 20:30 UK (GMT and BST), every day; new EMA pullback trades only from 06:00 to 20:30 UK; the 21:55-22:15 rollover pause kept; off, the EMA pullback as before; no other strategy changes.
diff --git a/tests/functional/test_ema_pullback_trading_hours.py b/tests/functional/test_ema_pullback_trading_hours.py
new file mode 100644
index 0000000..e6c6b5d
--- /dev/null
+++ b/tests/functional/test_ema_pullback_trading_hours.py
@@ -0,0 +1,164 @@
+"""Functional tests for EMA_PULLBACK_TRADING_HOURS (owner, 21 November 2026), through the live engine with the real
+order sender, safety rules and trade manager and a pretend IG (the harness of tests/technical/test_trading.py):
+
+  * new EMA pullback trades only between 06:00 and 20:30 UK time, following UK clocks (GMT in winter, BST in summer);
+  * any open EMA pullback trade closed at 20:30 UK every day, not just Friday; nothing held overnight;
+  * the 21:55-22:15 rollover pause kept as it is;
+  * off (the default): the EMA pullback exactly as before; no other strategy changes either way.
+Contacts nobody."""
+
+from datetime import timedelta
+from decimal import Decimal as D
+
+import pytest
+
+from strategies.common import (ASIAN_RANGE_BREAKOUT, BOLLINGER_BOUNCE, BOLLINGER_BOUNCE_5M, BREAKOUT, EMA_PULLBACK,
+                               LEVEL_REVERSAL, NEW_YORK_OPEN_REVERSAL, RANGE_TRADE, SELL, SESSION_SWEEP, SLOW_GRIND,
+                               forced_close_at, may_open)
+from tests.technical.test_orders import Over
+from tests.technical.test_trading import U, candle, feed, idea, journal, make, tick, trades_rows
+
+
+def settings(pretend_switches, tmp_path, on):
+    from config.settings_loader import load_settings
+    s = load_settings(switches_from=pretend_switches).for_pair("GBPUSD")
+    return Over(s, switches={k: True for k in ("slow_grind", "ema_pullback", "bollinger_bounce", "range_trade",
+                                                 "breakout", "level_reversal")}
+                | {"trading": False, "ema_pullback_trading_hours": on},
+                orders={"folder": tmp_path / "orders"}, trade_manager={"folder": tmp_path / "tm"},
+                safety={"folder": tmp_path / "safety"}, records={"folder": tmp_path / "records"},
+                trading={"pause_file": tmp_path / "control" / "pause_new_trades"},
+                dashboard={"status_folder": tmp_path / "status"})
+
+
+@pytest.fixture
+def ON(pretend_switches, tmp_path):
+    return settings(pretend_switches, tmp_path, True)
+
+
+@pytest.fixture
+def OFF(pretend_switches, tmp_path):
+    return settings(pretend_switches, tmp_path, False)
+
+
+def test_the_switch_is_off_if_left_out_of_env(pretend_switches):
+    from config.settings_loader import load_settings
+    assert load_settings(switches_from=pretend_switches).switches.ema_pullback_trading_hours is False
+
+
+# ---- the 20:30 close ------------------------------------------------------------------------------------------
+
+def open_at(S, monkeypatch, t0):
+    """An EMA pullback sell opened on the candle starting at t0 (sent when it finishes, t0 + 5 minutes)."""
+    cs = [candle(t0 + timedelta(minutes=5 * k), 13400, 13400.5, 13399.5, 13400) for k in range(4)]
+    e, ig, tracker, clock, quote = make(S, monkeypatch, cs, {cs[0].start: [idea(EMA_PULLBACK, cs[0].start,
+                                                                                price="13400")]},
+                                        trading_on=True, clock={"t": t0})
+    e.start(t0)
+    feed(e, clock, cs[:1])
+    (t,) = e.manager.trades.values()
+    assert t.strategy == EMA_PULLBACK and t.open
+    return e, clock, t
+
+
+def price_at(e, clock, when):
+    clock["t"] = when
+    e.on_price(tick(when, 13399.5))
+
+
+def test_on_a_trade_open_at_20_29_is_closed_at_20_30_uk_on_a_wednesday_gmt(ON, monkeypatch):
+    e, clock, t = open_at(ON, monkeypatch, U(2026, 11, 4, 20, 15))           # Wed 4 Nov: GMT, UK time = UTC
+    price_at(e, clock, U(2026, 11, 4, 20, 29, 0))
+    assert t.open                                                             # 20:29: still open
+    price_at(e, clock, U(2026, 11, 4, 20, 30, 0))
+    assert not t.open and t.state == "forced close"                           # 20:30: closed
+    (closed,) = [r for r in trades_rows(e) if r["event"] == "closed"]
+    assert closed["how_closed"] == "forced close" and "20:30 UK close" in closed["close_reason"]
+    assert closed["closed_utc"] == "2026-11-04T20:30:00Z"
+
+
+def test_on_a_trade_open_at_20_29_bst_is_closed_at_20_30_bst(ON, monkeypatch):
+    e, clock, t = open_at(ON, monkeypatch, U(2026, 10, 21, 19, 15))          # Wed 21 Oct: BST, 20:15 UK
+    price_at(e, clock, U(2026, 10, 21, 19, 29, 0))                            # 20:29 UK
+    assert t.open
+    price_at(e, clock, U(2026, 10, 21, 19, 30, 0))                            # 20:30 UK
+    assert not t.open and t.state == "forced close"
+
+
+@pytest.mark.parametrize("day", [2, 3, 4, 5, 6])                              # Monday 2 to Friday 6 November
+def test_on_the_close_is_every_day_not_just_friday(ON, day):
+    assert forced_close_at(ON, EMA_PULLBACK, U(2026, 11, day, 10, 0)) == U(2026, 11, day, 20, 30)
+
+
+def test_off_the_ema_pullback_is_still_held_past_20_30_until_friday(OFF, monkeypatch):
+    e, clock, t = open_at(OFF, monkeypatch, U(2026, 11, 4, 20, 15))
+    price_at(e, clock, U(2026, 11, 4, 20, 30, 0))
+    assert t.open                                                             # as before: no daily close
+    assert forced_close_at(OFF, EMA_PULLBACK, U(2026, 11, 4, 10, 0)) == U(2026, 11, 6, 20, 30)
+
+
+# ---- new trades only from 06:00 to 20:30 UK --------------------------------------------------------------------
+
+def live_ema_at(S, monkeypatch, when):
+    """An EMA pullback sell reaching its entry on the live price at `when` (the engine's live entry)."""
+    forming = when - timedelta(minutes=when.minute % 5, seconds=when.second)
+    cs = [candle(forming + timedelta(minutes=5 * k), 100, 100.5, 99.5, 100) for k in (-2, -1, 0)]
+    e, ig, tracker, clock, quote = make(S, monkeypatch, cs, {}, trading_on=True, clock={"t": cs[0].start},
+                                        live={forming: [(EMA_PULLBACK, SELL, D("100.5"))]})
+    e.start(cs[0].start)
+    feed(e, clock, cs[:2])
+    clock["t"] = when
+    e.on_price(tick(when, 100.4))
+    return e, ig
+
+
+def refusals(e):
+    return [r["reasons"] for r in journal(e) if r["event"] == "safety refused"]
+
+
+@pytest.mark.parametrize("when,opens", [
+    (U(2026, 11, 4, 5, 59, 59), False),                                       # GMT: 05:59:59 UK
+    (U(2026, 11, 4, 6, 0, 0), True),                                          # 06:00 UK
+    (U(2026, 11, 4, 20, 29, 59), True),                                       # 20:29:59 UK
+    (U(2026, 11, 4, 20, 30, 0), False),                                       # 20:30 UK
+    (U(2026, 10, 21, 4, 59, 59), False),                                      # BST: 05:59:59 UK
+    (U(2026, 10, 21, 5, 0, 0), True),                                         # BST: 06:00 UK
+    (U(2026, 10, 21, 19, 29, 59), True),                                      # BST: 20:29:59 UK
+    (U(2026, 10, 21, 19, 30, 0), False),                                      # BST: 20:30 UK
+])
+def test_on_new_ema_pullback_trades_only_from_06_00_to_20_30_uk(ON, monkeypatch, when, opens):
+    e, ig = live_ema_at(ON, monkeypatch, when)
+    assert (len(ig.orders_sent()) == 1) is opens
+    if not opens:
+        assert refusals(e) == [["outside the trading hours 06:00 to 20:30 UK"]]
+
+
+@pytest.mark.parametrize("when", [U(2026, 11, 4, 5, 59, 59), U(2026, 11, 4, 20, 30, 0), U(2026, 11, 4, 23, 0)])
+def test_off_the_ema_pullback_still_opens_outside_those_hours(OFF, monkeypatch, when):
+    e, ig = live_ema_at(OFF, monkeypatch, when)
+    assert len(ig.orders_sent()) == 1
+
+
+# ---- the rollover pause stays as it is ---------------------------------------------------------------------------
+
+@pytest.mark.parametrize("hh,mm", [(21, 55), (22, 0), (22, 14)])
+def test_the_rollover_pause_is_kept_as_it_is(ON, OFF, hh, mm):
+    t = U(2026, 11, 4, hh, mm)
+    rollover = "from 21:55 to 22:15 UK (the rollover): no new EMA pullback trade"
+    assert may_open(OFF, "GBPUSD", EMA_PULLBACK, t, []) == [rollover]
+    assert may_open(ON, "GBPUSD", EMA_PULLBACK, t, []) == [rollover, "outside the trading hours 06:00 to 20:30 UK"]
+
+
+# ---- no other strategy changes -----------------------------------------------------------------------------------
+
+OTHERS = (SLOW_GRIND, BOLLINGER_BOUNCE, BOLLINGER_BOUNCE_5M, RANGE_TRADE, BREAKOUT, LEVEL_REVERSAL,
+          ASIAN_RANGE_BREAKOUT, SESSION_SWEEP, NEW_YORK_OPEN_REVERSAL)
+
+
+@pytest.mark.parametrize("strategy", OTHERS)
+def test_no_other_strategys_hours_or_close_change(ON, OFF, strategy):
+    for day in (2, 4, 6):
+        for hh, mm in ((5, 59), (6, 0), (12, 0), (20, 29), (20, 30), (21, 55), (23, 0)):
+            t = U(2026, 11, day, hh, mm)
+            assert may_open(ON, "GBPUSD", strategy, t, []) == may_open(OFF, "GBPUSD", strategy, t, []), (strategy, t)
+            assert forced_close_at(ON, strategy, t) == forced_close_at(OFF, strategy, t), (strategy, t)
```

**The test that proves it:** `tests/functional/test_ema_pullback_trading_hours.py`. It runs through the live engine with the real order sender, safety rules and trade manager, and a pretend IG. It shows:
- a trade open at 20:29 UK is still open at 20:29 and closed at 20:30 UK, on a GMT day (Wed 4 Nov) and a BST day (Wed 21 Oct);
- the close happens Monday to Friday, not just Friday;
- the live entry is refused at 05:59:59 and opens at 06:00:00, opens at 20:29:59 and is refused at 20:30:00, in both GMT and BST;
- the rollover reason is unchanged;
- with the switch off, behaviour is as before;
- no other strategy's opening hours or close time change.

Run on its own, verbose, exactly as printed:

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0 -- /home/autobot/worktrees/autobot-ema-fixes/.venv/bin/python
rootdir: /home/autobot/worktrees/autobot-ema-fixes
configfile: pytest.ini
collecting ... collected 32 items

tests/functional/test_ema_pullback_trading_hours.py::test_the_switch_is_off_if_left_out_of_env PASSED [  3%]
tests/functional/test_ema_pullback_trading_hours.py::test_on_a_trade_open_at_20_29_is_closed_at_20_30_uk_on_a_wednesday_gmt PASSED [  6%]
tests/functional/test_ema_pullback_trading_hours.py::test_on_a_trade_open_at_20_29_bst_is_closed_at_20_30_bst PASSED [  9%]
tests/functional/test_ema_pullback_trading_hours.py::test_on_the_close_is_every_day_not_just_friday[2] PASSED [ 12%]
tests/functional/test_ema_pullback_trading_hours.py::test_on_the_close_is_every_day_not_just_friday[3] PASSED [ 15%]
tests/functional/test_ema_pullback_trading_hours.py::test_on_the_close_is_every_day_not_just_friday[4] PASSED [ 18%]
tests/functional/test_ema_pullback_trading_hours.py::test_on_the_close_is_every_day_not_just_friday[5] PASSED [ 21%]
tests/functional/test_ema_pullback_trading_hours.py::test_on_the_close_is_every_day_not_just_friday[6] PASSED [ 25%]
tests/functional/test_ema_pullback_trading_hours.py::test_off_the_ema_pullback_is_still_held_past_20_30_until_friday PASSED [ 28%]
tests/functional/test_ema_pullback_trading_hours.py::test_on_new_ema_pullback_trades_only_from_06_00_to_20_30_uk[when0-False] PASSED [ 31%]
tests/functional/test_ema_pullback_trading_hours.py::test_on_new_ema_pullback_trades_only_from_06_00_to_20_30_uk[when1-True] PASSED [ 34%]
tests/functional/test_ema_pullback_trading_hours.py::test_on_new_ema_pullback_trades_only_from_06_00_to_20_30_uk[when2-True] PASSED [ 37%]
tests/functional/test_ema_pullback_trading_hours.py::test_on_new_ema_pullback_trades_only_from_06_00_to_20_30_uk[when3-False] PASSED [ 40%]
tests/functional/test_ema_pullback_trading_hours.py::test_on_new_ema_pullback_trades_only_from_06_00_to_20_30_uk[when4-False] PASSED [ 43%]
tests/functional/test_ema_pullback_trading_hours.py::test_on_new_ema_pullback_trades_only_from_06_00_to_20_30_uk[when5-True] PASSED [ 46%]
tests/functional/test_ema_pullback_trading_hours.py::test_on_new_ema_pullback_trades_only_from_06_00_to_20_30_uk[when6-True] PASSED [ 50%]
tests/functional/test_ema_pullback_trading_hours.py::test_on_new_ema_pullback_trades_only_from_06_00_to_20_30_uk[when7-False] PASSED [ 53%]
tests/functional/test_ema_pullback_trading_hours.py::test_off_the_ema_pullback_still_opens_outside_those_hours[when0] PASSED [ 56%]
tests/functional/test_ema_pullback_trading_hours.py::test_off_the_ema_pullback_still_opens_outside_those_hours[when1] PASSED [ 59%]
tests/functional/test_ema_pullback_trading_hours.py::test_off_the_ema_pullback_still_opens_outside_those_hours[when2] PASSED [ 62%]
tests/functional/test_ema_pullback_trading_hours.py::test_the_rollover_pause_is_kept_as_it_is[21-55] PASSED [ 65%]
tests/functional/test_ema_pullback_trading_hours.py::test_the_rollover_pause_is_kept_as_it_is[22-0] PASSED [ 68%]
tests/functional/test_ema_pullback_trading_hours.py::test_the_rollover_pause_is_kept_as_it_is[22-14] PASSED [ 71%]
tests/functional/test_ema_pullback_trading_hours.py::test_no_other_strategys_hours_or_close_change[slow grind] PASSED [ 75%]
tests/functional/test_ema_pullback_trading_hours.py::test_no_other_strategys_hours_or_close_change[Bollinger bounce] PASSED [ 78%]
tests/functional/test_ema_pullback_trading_hours.py::test_no_other_strategys_hours_or_close_change[Bollinger bounce 5m] PASSED [ 81%]
tests/functional/test_ema_pullback_trading_hours.py::test_no_other_strategys_hours_or_close_change[range trade] PASSED [ 84%]
tests/functional/test_ema_pullback_trading_hours.py::test_no_other_strategys_hours_or_close_change[breakout] PASSED [ 87%]
tests/functional/test_ema_pullback_trading_hours.py::test_no_other_strategys_hours_or_close_change[level reversal] PASSED [ 90%]
tests/functional/test_ema_pullback_trading_hours.py::test_no_other_strategys_hours_or_close_change[Asian range breakout] PASSED [ 93%]
tests/functional/test_ema_pullback_trading_hours.py::test_no_other_strategys_hours_or_close_change[session sweep] PASSED [ 96%]
tests/functional/test_ema_pullback_trading_hours.py::test_no_other_strategys_hours_or_close_change[New York open reversal] PASSED [100%]

============================== 32 passed in 1.12s ==============================
```

All existing tests, run by the pre-commit hook when `e5eb882` was committed, exactly as printed:

```
pre-commit: running all tests...
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
rootdir: /home/autobot/worktrees/autobot-ema-fixes
configfile: pytest.ini
testpaths: tests
collected 2310 items

tests/functional/test_analyser_real_candles.py ..                        [  0%]
tests/functional/test_bounce_real_candles.py ....                        [  0%]
tests/functional/test_ema_pullback_trading_hours.py .................... [  1%]
............                                                             [  1%]
tests/functional/test_execution_integrity_real_candles.py .              [  1%]
tests/functional/test_levels_real_candles.py ...                         [  1%]
tests/functional/test_live_entries_real_candles.py .                     [  1%]
tests/functional/test_market_states_real_candles.py .......              [  2%]
tests/functional/test_news_real_calendar.py ..                           [  2%]
tests/functional/test_planner_scenarios.py ........................      [  3%]
tests/functional/test_rejection_real_candles.py ..                       [  3%]
tests/functional/test_safety_real_calendar.py ...............            [  4%]
tests/functional/test_stp_dashboard_scenarios.py ....................... [  5%]
.                                                                        [  5%]
tests/functional/test_trend_day_real_candles.py ..                       [  5%]
tests/technical/test_alerts.py ...........................               [  6%]
tests/technical/test_analyser.py .......................                 [  7%]
tests/technical/test_bounce.py .....................................     [  8%]
tests/technical/test_candle_store.py ................                    [  9%]
tests/technical/test_candles_and_checks.py ............................. [ 10%]
...............................                                          [ 12%]
tests/technical/test_dashboard.py ...........................            [ 13%]
tests/technical/test_execution_integrity.py ...............              [ 14%]
tests/technical/test_find_market.py ..                                   [ 14%]
tests/technical/test_first_build_plus.py ..................              [ 14%]
tests/technical/test_history_door.py ........................            [ 15%]
tests/technical/test_history_fill.py ..............                      [ 16%]
tests/technical/test_housekeeping.py ......                              [ 16%]
tests/technical/test_ig_connection.py .................................. [ 18%]
.....................................................................    [ 21%]
tests/technical/test_levels.py ....................................      [ 22%]
tests/technical/test_long_history.py .........                           [ 23%]
tests/technical/test_market_states.py .................................. [ 24%]
..........................................                               [ 26%]
tests/technical/test_news.py ..................                          [ 27%]
tests/technical/test_news_table.py ..................................... [ 28%]
........................................................................ [ 31%]
.........................                                                [ 33%]
tests/technical/test_no_historical_prices.py .............               [ 33%]
tests/technical/test_orders.py ......................................... [ 35%]
.................................                                        [ 36%]
tests/technical/test_pairs.py ...............                            [ 37%]
tests/technical/test_planner.py ........................................ [ 39%]
................                                                         [ 39%]
tests/technical/test_price_stream.py .................................   [ 41%]
tests/technical/test_records.py .....................                    [ 42%]
tests/technical/test_rejection.py ..............................         [ 43%]
tests/technical/test_rules_9_and_11.py ......                            [ 43%]
tests/technical/test_safety.py ......................................... [ 45%]
........................................................................ [ 48%]
......                                                                   [ 48%]
tests/technical/test_service.py ...........                              [ 49%]
tests/technical/test_session_strategies.py ............................. [ 50%]
...............                                                          [ 51%]
tests/technical/test_settings.py ....................................... [ 53%]
........................................................................ [ 56%]
........................................................................ [ 59%]
........................................................................ [ 62%]
........................................................................ [ 65%]
........................................................................ [ 68%]
........................................................................ [ 71%]
........................................................................ [ 74%]
........................................................................ [ 77%]
........................................................................ [ 81%]
.................................................                        [ 83%]
tests/technical/test_settings_documented.py .....                        [ 83%]
tests/technical/test_stp_corrections.py ............................     [ 84%]
tests/technical/test_stp_dashboard.py .................................. [ 86%]
.......                                                                  [ 86%]
tests/technical/test_stp_targeted.py .......................             [ 87%]
tests/technical/test_strategies.py ..................................... [ 89%]
........................................................................ [ 92%]
.............................................                            [ 94%]
tests/technical/test_strategies_see_latest_candles.py ...                [ 94%]
tests/technical/test_test_order.py .............................         [ 95%]
tests/technical/test_trade_manager.py .................................. [ 96%]
...................                                                      [ 97%]
tests/technical/test_trading.py ...................................      [ 99%]
tests/technical/test_trail_17_november.py ..                             [ 99%]
tests/technical/test_trend_day.py ...............                        [100%]

======================= 2310 passed in 850.65s (0:14:10) =======================
pre-commit: all tests passed.
[ema-pullback-hours-one-trade e5eb882] EMA pullback: trading hours 06:00-20:30 UK and closed at 20:30 every day, behind EMA_PULLBACK_TRADING_HOURS (off)
 6 files changed, 199 insertions(+), 9 deletions(-)
 create mode 100644 tests/functional/test_ema_pullback_trading_hours.py
exit 0
```

## 3. Fix 2: only one EMA pullback trade open at a time

**New .env setting:** `EMA_PULLBACK_ONE_AT_A_TIME` (`on` or `off`; off if left out).

**What it does while on:**
- The EMA pullback is no longer exempt from the per-strategy limit every other strategy already has: safety rule 5, `limits.max_open_trades_per_strategy = 1`.
- While an EMA pullback trade is open, in either direction, another one is refused by the safety rules. A new one can open once the first has closed.
- Setups still form, and their ideas are logged as now. A skipped one is recorded with its reason in the orders journal (`"event": "safety refused"`) and the decisions (`"kind": "order", "result": "safety refused"`). The reason reads `EMA pullback already has 1 trade(s) open (at most 1)`.
- EMA pullback trades still don't count towards the most at once (5).

**Files changed:**

```
 .env.example                                       |   2 +
 config/switches.py                                 |   6 +-
 docs/SETTINGS.md                                   |   1 +
 safety/rules.py                                    |   8 +-
 tests/functional/README.md                         |   1 +
 .../functional/test_ema_pullback_one_at_a_time.py  | 128 +++++++++++++++++++++
 6 files changed, 143 insertions(+), 3 deletions(-)
```

**Code diff (whole commit):**

```diff
diff --git a/.env.example b/.env.example
index 81bbfa1..f63378e 100644
--- a/.env.example
+++ b/.env.example
@@ -57,3 +57,5 @@ ONE_SIGNAL_ONE_TRADE=off
 # The EMA pullback's hours, off if left out: on = new EMA pullback trades only from NEW_TRADES_FROM to
 # NEW_TRADES_UNTIL UK, and every open EMA pullback trade closed at 20:30 UK every day (nothing held overnight).
 EMA_PULLBACK_TRADING_HOURS=off
+# Only one EMA pullback trade open at a time, off if left out: on = while one is open, no other opens.
+EMA_PULLBACK_ONE_AT_A_TIME=off
diff --git a/config/switches.py b/config/switches.py
index f587eae..7c7fc9a 100644
--- a/config/switches.py
+++ b/config/switches.py
@@ -18,6 +18,9 @@
                               within the trading hours NEW_TRADES_FROM to NEW_TRADES_UNTIL (UK clock), as the other
                               strategies, and every open EMA pullback trade closed at hours.close_all_trades_at (20:30)
                               UK every day, not only on Friday; the 21:55-22:15 rollover pause stays as it is
+  EMA_PULLBACK_ONE_AT_A_TIME  on or off (off if left out; owner, 21 November 2026): while an EMA pullback trade is
+                              open, no other EMA pullback trade opens (limits.max_open_trades_per_strategy, 1, as the
+                              other strategies); setups still form and are logged; a skipped one is logged as refused
   BOUNCE_ONLY_NEAR_TIMES      on or off (off if left out): while on, a Bollinger bounce opens only within
                               bounce.near_times_within_minutes (60) of bounce.near_times (10:00, 14:00,
                               16:00 UK) in settings.toml
@@ -102,6 +105,7 @@ SWITCHES: dict[str, tuple[str, Callable[[str], Any]]] = {
     "PLANNER_OBSERVE": ("planner_observe", _on_off),
     "ONE_SIGNAL_ONE_TRADE": ("one_signal_one_trade", _on_off),
     "EMA_PULLBACK_TRADING_HOURS": ("ema_pullback_trading_hours", _on_off),
+    "EMA_PULLBACK_ONE_AT_A_TIME": ("ema_pullback_one_at_a_time", _on_off),
     "STRATEGY_RANGE_TRADE": ("range_trade", _on_off),
     "STRATEGY_BREAKOUT": ("breakout", _on_off),
     "STRATEGY_LEVEL_REVERSAL": ("level_reversal", _on_off),
@@ -116,7 +120,7 @@ SWITCHES: dict[str, tuple[str, Callable[[str], Any]]] = {
 
 # Switches that may be left out of .env, and their value then (owner, 15 November 2026: both off by default).
 OPTIONAL: dict[str, str] = {"BOUNCE_ONLY_NEAR_TIMES": "off", "PLANNER_OBSERVE": "off", "ONE_SIGNAL_ONE_TRADE": "off",
-                            "EMA_PULLBACK_TRADING_HOURS": "off"}
+                            "EMA_PULLBACK_TRADING_HOURS": "off", "EMA_PULLBACK_ONE_AT_A_TIME": "off"}
 
 
 def read_switches(path: Path) -> tuple[dict[str, Any], list[str]]:
diff --git a/docs/SETTINGS.md b/docs/SETTINGS.md
index ba8fd5e..c48c642 100644
--- a/docs/SETTINGS.md
+++ b/docs/SETTINGS.md
@@ -468,6 +468,7 @@ These live in `.env` (not in `config/settings.toml`), next to the IG secrets, so
 | `STRATEGY_BOLLINGER_BOUNCE_5M` | The first build's Bollinger band bounce (5-minute band and levels; `strategies/bollinger_bounce_5m`, recorded as "Bollinger bounce 5m"), `on` or `off`. Kept and renamed alongside the hourly-pierce bounce (owner, 19 November 2026). Required. | on |
 | `ONE_SIGNAL_ONE_TRADE` | Stage 3 of the analyser control (design 6), `on` or `off`. On: two strategies opening the same way from the same rejection candle give one trade, the first to trigger (the others refused: "same signal already traded by ..."); the session sweep and the New York open reversal come under one view at a time. Off if left out of `.env`. **Owner's switch, off, 18 November 2026.** | off |
 | `EMA_PULLBACK_TRADING_HOURS` | The EMA pullback's hours, `on` or `off`. On: a new EMA pullback trade opens only within the trading hours `NEW_TRADES_FROM` to `NEW_TRADES_UNTIL` (UK clock: GMT in winter, BST in summer), the same check as every other strategy, and every open EMA pullback trade is closed at `hours.close_all_trades_at` (20:30) UK every day, not only on Friday, so none is held overnight. The 21:55-22:15 rollover pause (`ema_pullback.rollover_no_new_trades_*`) stays as it is. Off (the EMA pullback's own hours: any time except Friday after 20:30 and the rollover; closed 20:30 UK on Friday only) if left out of `.env`. **Owner, 21 November 2026.** | off |
+| `EMA_PULLBACK_ONE_AT_A_TIME` | Only one EMA pullback trade open at a time, `on` or `off`. On: while an EMA pullback trade is open (either direction), no other EMA pullback trade opens; a new one can open once it has closed. This is the per-strategy limit the other strategies already have (`limits.max_open_trades_per_strategy`, 1). Setups still form and are logged as before; a skipped one is recorded as refused by the safety rules, with the reason ("EMA pullback already has 1 trade(s) open (at most 1)"), in the orders journal and the decisions. EMA pullback trades still do not count towards `limits.max_open_trades`. Off (no limit, as before) if left out of `.env`. **Owner, 21 November 2026.** | off |
 | `PLANNER_OBSERVE` | The Structural Trade Planner (`planner/`), `on` or `off`. On: after each new 5-minute candle the price service starts the planner in a separate, low-priority process (never on the price feed's thread): it re-plans on each completed hourly candle and checks its zone on each 5-minute candle, writing `planner.folder`. **Observe only:** it never authorises, refuses, opens, changes or closes a trade, and the dashboard panel says so. Off if left out of `.env`. **Off until the owner approves installation.** | off |
 | `STRATEGY_RANGE_TRADE` | The range trade strategy, `on` or `off`. | on |
 | `STRATEGY_BREAKOUT` | The breakout strategy (design 3.5), `on` or `off`. The bot refuses to start with it on while `breakout.stop_loss_pips` or `breakout.take_profit_pips` is 0. Switched on by the owner, 7 November 2026. | on |
diff --git a/safety/rules.py b/safety/rules.py
index 9dbded9..ab6240f 100644
--- a/safety/rules.py
+++ b/safety/rules.py
@@ -10,7 +10,8 @@ It gives EVERY reason it refuses (an empty list: the order may go out):
   3. the strategy's switch in .env is off (checked again here: a strategy cannot bypass it);
   4. the strategy's own hours, news rules and Friday rules (strategies.common.may_open);
   5. trades open at once: the strategy's own limit (limits.max_open_trades_per_strategy, 1; the
-     Bollinger bounce 1 in each direction, owner, 15 November 2026; the EMA pullback no limit), and at
+     Bollinger bounce 1 in each direction, owner, 15 November 2026; the EMA pullback no limit, or the same
+     limit while EMA_PULLBACK_ONE_AT_A_TIME is on, owner, 21 November 2026), and at
      most limits.max_open_trades (5) in total not counting the EMA pullback's
      (strategies.common.counts_towards_most_at_once); the Bollinger bounce is not held back by that total;
      the three session strategies (owner, 16 November 2026) as the bounce: 1 in each direction, not held back;
@@ -108,9 +109,12 @@ class Decision:
 
 
 def _limits(settings: Any, order: Order, open_trades: list[OpenTrade]) -> list[str]:
+    from analyser.states import switch_on
     lim, idea = settings.limits, order.idea
     out = []
-    if idea.strategy != EMA_PULLBACK:
+    # the EMA pullback has no limit of its own, unless EMA_PULLBACK_ONE_AT_A_TIME is on: then the same per-strategy
+    # limit as the others, one open at a time (owner, 21 November 2026)
+    if idea.strategy != EMA_PULLBACK or switch_on(settings, "ema_pullback_one_at_a_time"):
         mine = [t for t in open_trades if t.strategy == idea.strategy]
         if idea.strategy in WITHOUT_HINDRANCE:           # one at a time in each direction (owner, 15 and 16 November 2026)
             same = [t for t in mine if t.direction == idea.direction]
diff --git a/tests/functional/README.md b/tests/functional/README.md
index 65a98da..7d41596 100644
--- a/tests/functional/README.md
+++ b/tests/functional/README.md
@@ -7,3 +7,4 @@ Tests that check the bot behaves the way a trader expects (for example, "no new
 - `test_analyser_real_candles.py`: the direction is sell side at 13:00 on 6 November, and the 5-minute 100 EMA, pivot and direction at 06:00, 09:00, 13:00 and 16:00 that day (`docs/ANALYSER.md`).
 - `test_market_states_real_candles.py`: the five market states on 5 and 6 November: the midnight pivot rejection starting the downtrend, consolidation before 06:40, the two strong pushes, the possible reversal around 10:15, sell side at 13:00, and a restart at 09:00 giving exactly the same states (`docs/ANALYSER.md`). The S2 flat spell (11:30 to 12:45) is a known shortfall, not tested (design section 12).
 - `test_ema_pullback_trading_hours.py`: `EMA_PULLBACK_TRADING_HOURS` (owner, 21 November 2026), through the live engine with a pretend IG: an EMA pullback trade open at 20:29 UK is closed at 20:30 UK (GMT and BST), every day; new EMA pullback trades only from 06:00 to 20:30 UK; the 21:55-22:15 rollover pause kept; off, the EMA pullback as before; no other strategy changes.
+- `test_ema_pullback_one_at_a_time.py`: `EMA_PULLBACK_ONE_AT_A_TIME` (owner, 21 November 2026), through the live engine with a pretend IG: a second EMA pullback setup reaching its entry while one trade is open (either direction) does not open, is logged as an idea and its refusal recorded with the reason; a new one opens once the first has closed; off, as before; no other strategy changes.
diff --git a/tests/functional/test_ema_pullback_one_at_a_time.py b/tests/functional/test_ema_pullback_one_at_a_time.py
new file mode 100644
index 0000000..0c528e0
--- /dev/null
+++ b/tests/functional/test_ema_pullback_one_at_a_time.py
@@ -0,0 +1,128 @@
+"""Functional tests for EMA_PULLBACK_ONE_AT_A_TIME (owner, 21 November 2026), through the live engine with the real
+order sender, safety rules and trade manager and a pretend IG (the harness of tests/technical/test_trading.py):
+
+  * while an EMA pullback trade is open, no other EMA pullback trade opens; a new one can open once that trade has
+    closed;
+  * setups still form and are logged as now; only the opening of the second trade is stopped, and the reason is
+    logged when one is skipped;
+  * off (the default): the EMA pullback exactly as before; no other strategy changes either way.
+Contacts nobody."""
+
+from datetime import timedelta
+
+import pytest
+
+from strategies.common import BUY, EMA_PULLBACK, SELL, SLOW_GRIND
+from tests.technical.test_orders import Over
+from tests.technical.test_trading import U, candle, decisions, feed, idea, journal, make, trades_rows
+
+T0 = U(2026, 11, 4, 10, 0)                                                     # a Wednesday, GMT
+CS = [candle(T0 + timedelta(minutes=5 * k), 13400, 13400.5, 13399.5, 13400) for k in range(8)]
+SKIPPED = "EMA pullback already has 1 trade(s) open (at most 1)"
+
+
+def settings(pretend_switches, tmp_path, on):
+    from config.settings_loader import load_settings
+    s = load_settings(switches_from=pretend_switches).for_pair("GBPUSD")
+    return Over(s, switches={k: True for k in ("slow_grind", "ema_pullback", "bollinger_bounce", "range_trade",
+                                                 "breakout", "level_reversal")}
+                | {"trading": False, "ema_pullback_one_at_a_time": on},
+                orders={"folder": tmp_path / "orders"}, trade_manager={"folder": tmp_path / "tm"},
+                safety={"folder": tmp_path / "safety"}, records={"folder": tmp_path / "records"},
+                trading={"pause_file": tmp_path / "control" / "pause_new_trades"},
+                dashboard={"status_folder": tmp_path / "status"})
+
+
+@pytest.fixture
+def ON(pretend_switches, tmp_path):
+    return settings(pretend_switches, tmp_path, True)
+
+
+@pytest.fixture
+def OFF(pretend_switches, tmp_path):
+    return settings(pretend_switches, tmp_path, False)
+
+
+def ema(k, direction=SELL):
+    return idea(EMA_PULLBACK, CS[k].start, direction, price="13400")
+
+
+def run(S, monkeypatch, ideas, upto):
+    e, ig, tracker, clock, quote = make(S, monkeypatch, CS, ideas, trading_on=True, clock={"t": T0})
+    e.start(T0)
+    feed(e, clock, CS[:upto])
+    return e, ig, clock
+
+
+def ema_trades(e):
+    return [t for t in e.manager.trades.values() if t.strategy == EMA_PULLBACK]
+
+
+def test_the_switch_is_off_if_left_out_of_env(pretend_switches):
+    from config.settings_loader import load_settings
+    assert load_settings(switches_from=pretend_switches).switches.ema_pullback_one_at_a_time is False
+
+
+def test_on_a_second_setup_reaching_its_entry_while_one_trade_is_open_does_not_open(ON, monkeypatch):
+    e, ig, clock = run(ON, monkeypatch, {CS[1].start: [ema(1)], CS[3].start: [ema(3)]}, 5)
+    assert len(ig.orders_sent()) == 1 and len(ema_trades(e)) == 1                # only the first opened
+    (first,) = ema_trades(e)
+    assert first.open and first.opened_at == CS[1].end
+    # the second setup is logged as now: its idea, allowed by the strategy's rules, at its candle
+    ideas = [d for d in decisions(e) if d["kind"] == "idea" and d["strategy"] == EMA_PULLBACK]
+    assert [d["time_utc"] for d in ideas] == ["2026-11-04T10:05:00Z", "2026-11-04T10:15:00Z"]
+    assert all(d["allowed"] for d in ideas)
+    # and the reason it was skipped is logged, in the orders journal and the decisions
+    (refused,) = [r for r in journal(e) if r["event"] == "safety refused"]
+    assert refused["strategy"] == EMA_PULLBACK and refused["reasons"] == [SKIPPED]
+    (order,) = [d for d in decisions(e) if d["kind"] == "order" and d["result"] == "safety refused"]
+    assert order["strategy"] == EMA_PULLBACK and order["reasons"] == [SKIPPED]
+
+
+def test_on_the_other_direction_does_not_open_either(ON, monkeypatch):
+    e, ig, clock = run(ON, monkeypatch, {CS[1].start: [ema(1, SELL)], CS[3].start: [ema(3, BUY)]}, 5)
+    assert len(ig.orders_sent()) == 1 and [t.direction for t in ema_trades(e)] == [SELL]
+    assert [r["reasons"] for r in journal(e) if r["event"] == "safety refused"] == [[SKIPPED]]
+
+
+def test_on_a_new_one_opens_once_the_open_trade_has_closed(ON, monkeypatch):
+    e, ig, clock = run(ON, monkeypatch, {CS[1].start: [ema(1)], CS[3].start: [ema(3)], CS[6].start: [ema(6)]}, 5)
+    (first,) = ema_trades(e)
+    ig.system_close(e.sender.trades[first.reference].deal_id, 13412.5, "2026-11-04T10:26:00",
+                    stop=float(first.fill) + 12)                                  # IG's stop: the trade closes
+    feed(e, clock, CS[5:6])                                                       # found closed after the candle
+    assert not first.open and first.state == "closed at IG"
+    feed(e, clock, CS[6:7])                                                       # a later setup reaches its entry
+    assert len(ig.orders_sent()) == 2
+    second = [t for t in ema_trades(e) if t.reference != first.reference]
+    assert len(second) == 1 and second[0].open and second[0].opened_at == CS[6].end
+    assert [r["reasons"] for r in journal(e) if r["event"] == "safety refused"] == [[SKIPPED]]   # only the 10:15 one
+
+
+def test_off_a_second_ema_pullback_trade_still_opens(OFF, monkeypatch):
+    e, ig, clock = run(OFF, monkeypatch, {CS[1].start: [ema(1)], CS[3].start: [ema(3)]}, 5)
+    assert len(ig.orders_sent()) == 2 and all(t.open for t in ema_trades(e))
+    assert not [r for r in journal(e) if r["event"] == "safety refused"]
+
+
+def test_on_an_ema_pullback_trade_still_does_not_count_towards_another_strategys_limits(ON, monkeypatch):
+    e, ig, clock = run(ON, monkeypatch, {CS[1].start: [ema(1)], CS[3].start: [idea(SLOW_GRIND, CS[3].start,
+                                                                                     price="13400")]}, 5)
+    assert sorted(t.strategy for t in e.manager.trades.values()) == [EMA_PULLBACK, SLOW_GRIND]
+    assert not [r for r in journal(e) if r["event"] == "safety refused"]
+
+
+def test_no_other_strategys_limit_changes(ON, OFF):
+    from datetime import timedelta as td
+    from decimal import Decimal as D
+    from safety.rules import AccountFunds, OpenTrade, decide, order_for
+    from strategies.common import BOLLINGER_BOUNCE, BREAKOUT, LEVEL_REVERSAL, RANGE_TRADE, Idea
+    t = U(2026, 11, 4, 10, 0)
+    for strategy in (SLOW_GRIND, BOLLINGER_BOUNCE, RANGE_TRADE, BREAKOUT, LEVEL_REVERSAL):
+        ctx = {"stop_price": D("13410.0")} if strategy == LEVEL_REVERSAL else {}
+        i = Idea("GBPUSD", strategy, SELL, t, D("13400.0"), "trend", "down", None, "sell side", ["made up"], True, "", ctx)
+        for open_trades in ([], [OpenTrade(strategy, SELL, t - td(hours=1), D("12"), D("10"))],
+                            [OpenTrade(EMA_PULLBACK, SELL, t - td(hours=1), D("12"), D("10"))]):
+            a = decide(ON, order_for(ON, i), list(open_trades), AccountFunds(D("20000"), t - td(minutes=30)), t, False, [])
+            b = decide(OFF, order_for(OFF, i), list(open_trades), AccountFunds(D("20000"), t - td(minutes=30)), t, False, [])
+            assert (a.allowed, a.reasons) == (b.allowed, b.reasons), (strategy, open_trades)
```

**The test that proves it:** `tests/functional/test_ema_pullback_one_at_a_time.py`. It runs through the live engine with a pretend IG. It shows:
- a second setup reaching its entry while one trade is open does not open, in the same or the other direction;
- the second setup's idea is still logged, and its refusal is recorded with the reason in both the orders journal and the decisions;
- once the first trade is closed (by IG's stop), a later setup opens;
- with the switch off, a second trade opens as before;
- an open EMA pullback trade still doesn't hold back another strategy, and no other strategy's limits change.

Run on its own, verbose, exactly as printed:

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0 -- /home/autobot/worktrees/autobot-ema-fixes/.venv/bin/python
rootdir: /home/autobot/worktrees/autobot-ema-fixes
configfile: pytest.ini
collecting ... collected 7 items

tests/functional/test_ema_pullback_one_at_a_time.py::test_the_switch_is_off_if_left_out_of_env PASSED [ 14%]
tests/functional/test_ema_pullback_one_at_a_time.py::test_on_a_second_setup_reaching_its_entry_while_one_trade_is_open_does_not_open PASSED [ 28%]
tests/functional/test_ema_pullback_one_at_a_time.py::test_on_the_other_direction_does_not_open_either PASSED [ 42%]
tests/functional/test_ema_pullback_one_at_a_time.py::test_on_a_new_one_opens_once_the_open_trade_has_closed PASSED [ 57%]
tests/functional/test_ema_pullback_one_at_a_time.py::test_off_a_second_ema_pullback_trade_still_opens PASSED [ 71%]
tests/functional/test_ema_pullback_one_at_a_time.py::test_on_an_ema_pullback_trade_still_does_not_count_towards_another_strategys_limits PASSED [ 85%]
tests/functional/test_ema_pullback_one_at_a_time.py::test_no_other_strategys_limit_changes PASSED [100%]

============================== 7 passed in 0.32s ===============================
```

All existing tests, run by the pre-commit hook when `57a1a9f` was committed, exactly as printed:

```
pre-commit: running all tests...
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
rootdir: /home/autobot/worktrees/autobot-ema-fixes
configfile: pytest.ini
testpaths: tests
collected 2317 items

tests/functional/test_analyser_real_candles.py ..                        [  0%]
tests/functional/test_bounce_real_candles.py ....                        [  0%]
tests/functional/test_ema_pullback_one_at_a_time.py .......              [  0%]
tests/functional/test_ema_pullback_trading_hours.py .................... [  1%]
............                                                             [  1%]
tests/functional/test_execution_integrity_real_candles.py .              [  1%]
tests/functional/test_levels_real_candles.py ...                         [  2%]
tests/functional/test_live_entries_real_candles.py .                     [  2%]
tests/functional/test_market_states_real_candles.py .......              [  2%]
tests/functional/test_news_real_calendar.py ..                           [  2%]
tests/functional/test_planner_scenarios.py ........................      [  3%]
tests/functional/test_rejection_real_candles.py ..                       [  3%]
tests/functional/test_safety_real_calendar.py ...............            [  4%]
tests/functional/test_stp_dashboard_scenarios.py ....................... [  5%]
.                                                                        [  5%]
tests/functional/test_trend_day_real_candles.py ..                       [  5%]
tests/technical/test_alerts.py ...........................               [  6%]
tests/technical/test_analyser.py .......................                 [  7%]
tests/technical/test_bounce.py .....................................     [  9%]
tests/technical/test_candle_store.py ................                    [  9%]
tests/technical/test_candles_and_checks.py ............................. [ 11%]
...............................                                          [ 12%]
tests/technical/test_dashboard.py ...........................            [ 13%]
tests/technical/test_execution_integrity.py ...............              [ 14%]
tests/technical/test_find_market.py ..                                   [ 14%]
tests/technical/test_first_build_plus.py ..................              [ 15%]
tests/technical/test_history_door.py ........................            [ 16%]
tests/technical/test_history_fill.py ..............                      [ 16%]
tests/technical/test_housekeeping.py ......                              [ 17%]
tests/technical/test_ig_connection.py .................................. [ 18%]
.....................................................................    [ 21%]
tests/technical/test_levels.py ....................................      [ 23%]
tests/technical/test_long_history.py .........                           [ 23%]
tests/technical/test_market_states.py .................................. [ 24%]
..........................................                               [ 26%]
tests/technical/test_news.py ..................                          [ 27%]
tests/technical/test_news_table.py ..................................... [ 29%]
........................................................................ [ 32%]
.........................                                                [ 33%]
tests/technical/test_no_historical_prices.py .............               [ 33%]
tests/technical/test_orders.py ......................................... [ 35%]
.................................                                        [ 37%]
tests/technical/test_pairs.py ...............                            [ 37%]
tests/technical/test_planner.py ........................................ [ 39%]
................                                                         [ 40%]
tests/technical/test_price_stream.py .................................   [ 41%]
tests/technical/test_records.py .....................                    [ 42%]
tests/technical/test_rejection.py ..............................         [ 43%]
tests/technical/test_rules_9_and_11.py ......                            [ 43%]
tests/technical/test_safety.py ......................................... [ 45%]
........................................................................ [ 48%]
......                                                                   [ 49%]
tests/technical/test_service.py ...........                              [ 49%]
tests/technical/test_session_strategies.py ............................. [ 50%]
...............                                                          [ 51%]
tests/technical/test_settings.py ....................................... [ 53%]
........................................................................ [ 56%]
........................................................................ [ 59%]
........................................................................ [ 62%]
........................................................................ [ 65%]
........................................................................ [ 68%]
........................................................................ [ 71%]
........................................................................ [ 74%]
........................................................................ [ 78%]
........................................................................ [ 81%]
.................................................                        [ 83%]
tests/technical/test_settings_documented.py .....                        [ 83%]
tests/technical/test_stp_corrections.py ............................     [ 84%]
tests/technical/test_stp_dashboard.py .................................. [ 86%]
.......                                                                  [ 86%]
tests/technical/test_stp_targeted.py .......................             [ 87%]
tests/technical/test_strategies.py ..................................... [ 89%]
........................................................................ [ 92%]
.............................................                            [ 94%]
tests/technical/test_strategies_see_latest_candles.py ...                [ 94%]
tests/technical/test_test_order.py .............................         [ 95%]
tests/technical/test_trade_manager.py .................................. [ 96%]
...................                                                      [ 97%]
tests/technical/test_trading.py ...................................      [ 99%]
tests/technical/test_trail_17_november.py ..                             [ 99%]
tests/technical/test_trend_day.py ...............                        [100%]

======================= 2317 passed in 823.47s (0:13:43) =======================
pre-commit: all tests passed.
[ema-pullback-hours-one-trade 57a1a9f] EMA pullback: one trade open at a time, behind EMA_PULLBACK_ONE_AT_A_TIME (off)
 6 files changed, 143 insertions(+), 3 deletions(-)
 create mode 100644 tests/functional/test_ema_pullback_one_at_a_time.py
exit 0
```

## 4. The .env lines to switch each fix on

Add either line or both to `/opt/autobot/.env`. Each takes effect only after the branch is installed and the price service restarted.

```
EMA_PULLBACK_TRADING_HOURS=on
EMA_PULLBACK_ONE_AT_A_TIME=on
```

Left out, or set to `off`, each fix does nothing.

## 5. What I couldn't do, or wasn't sure about

1. **The hours come from `NEW_TRADES_FROM` and `NEW_TRADES_UNTIL`.** This reuses the shared trading hours, as the brief asks. Today they are 06:00 and 20:30, exactly the hours in the brief. If Johnny changes them later, the EMA pullback's hours change with every other strategy's.
2. **"One at a time" comes from `limits.max_open_trades_per_strategy`.** This also reuses the shared part. It is 1 today. If it is ever raised, the EMA pullback would allow that many too.
3. **A trade open when the switch is first turned on.** After the restart, the trade manager works out each open trade's close time again. An EMA pullback trade opened before 20:30 that is still open after a restart past 20:30 would be closed on the first price after the restart. No test covers this.
4. **The old Friday rule stays.** The EMA pullback's "no new trade after 20:30 UK on Friday" rule is still there. With Fix 1 on it overlaps the new hours and changes nothing. I left it, because the brief says not to change anything else.
5. **A trade IG closes on its own.** With Fix 2 on, the bot learns this at its regular check after the next 5-minute candle, the same as for every strategy. Until then it still counts that trade as open. In the test, the new trade opened after that check.
6. **Not built on main.** The branch is built on `02f6c7e`, the code the live bot runs, not on main. Main has other changes (the analyser control, the hourly read) that this branch doesn't have.
7. **The live bot is untouched.** Nothing was installed or restarted. `/opt/autobot` is still on `5d7942e` (detached), and the price service is still running `02f6c7e`. Installing this branch and restarting are Johnny's to do.
