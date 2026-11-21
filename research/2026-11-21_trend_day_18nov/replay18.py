"""Read-only replay for research/2026-11-21_trend_day_18nov: the week of 16 Nov 2026 through the code that was live
on the night of 17-18 Nov (cc70dc5, running since the 17 Nov 20:46 UTC restart), with the live .env switches of
17 Nov 20:36 (TRADING off here). It reads the candle store only; never contacts IG; places nothing.
Run from a worktree at cc70dc5:  .venv/bin/python replay18.py > out.txt"""
import json, sys, tempfile
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo
sys.path.insert(0, ".")
from config.settings_loader import load_settings
from analyser.market_state import MemoStore, StateTracker
from prices.store import CandleStore
from strategies.replay import StrategyRunner
from strategies.common import check

UK = ZoneInfo("Europe/London")
SW = {"PAIRS_ON": "GBPUSD", "NEW_TRADES_FROM": "06:00", "NEW_TRADES_UNTIL": "20:30", "STRATEGY_SLOW_GRIND": "on",
      "STRATEGY_BREAKOUT": "on", "STRATEGY_EMA_PULLBACK": "on", "STRATEGY_BOLLINGER_BOUNCE": "on",
      "STRATEGY_LEVEL_REVERSAL": "on", "STRATEGY_RANGE_TRADE": "on", "STRATEGY_ASIAN_RANGE_BREAKOUT": "on",
      "STRATEGY_SESSION_SWEEP": "on", "STRATEGY_NEW_YORK_OPEN_REVERSAL": "on", "HOURLY_READ": "on",
      "TREND_STILL_GOING": "on", "STOP_LOSS_PIPS": "12", "STOP_LOSS_PIPS_EMA_PULLBACK": "12",
      "TAKE_PROFIT_PIPS": "100", "PLANNER_OBSERVE": "on", "TRADING": "off", "IG_ACC_TYPE": "DEMO"}
tmp = Path(tempfile.mkdtemp()); p = tmp / "sw.env"; p.write_text("".join(f"{k}={v}\n" for k, v in SW.items()))
s = load_settings(switches_from=p).for_pair("GBPUSD")
store = MemoStore(CandleStore(s.candles.folder, s.candles.compress_after_days))
END = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)
T0 = datetime(2026, 11, 17, 22, 0, tzinfo=timezone.utc)
tracker = StateTracker(s, store); tracker.replay(END)
runner = StrategyRunner(s, store, tracker, hourly_end=None)   # live mode: hourly read rebuilt per candle
steps = runner.step()
f = lambda t: t.astimezone(UK).strftime("%a %H:%M")
week = runner.week
idx = {c.start: i for i, c in enumerate(week)}
out = {"changes": [], "grind_ideas": [], "grind_notes": [], "per_candle": [], "candles": []}
print("== ANALYSER STATE CHANGES (replay), 17 Nov 20:00 to 18 Nov 12:00 UK")
for ch in tracker.changes:
    if ch.time >= T0 - timedelta(hours=2):
        print(f(ch.time), ch.state, ch.direction, ch.trend_type or "", "|", ch.reason[:260])
        out["changes"].append([ch.time.isoformat(), ch.state, ch.direction, ch.trend_type, ch.reason])
print("== SLOW GRIND notes")
for t, d, txt in runner.grind.notes:
    if t >= T0 - timedelta(hours=1):
        print(f(t), d, txt); out["grind_notes"].append([t.isoformat(), d, txt])
print("== SLOW GRIND setups (every one, with every check the live code ran)")
for c, idea in steps:
    if idea.strategy != "slow grind" or c.start < T0: continue
    print(f(c.start), idea.direction, idea.entry_price, "ALLOWED" if idea.allowed else "BLOCKED: " + idea.blocked_by)
    out["grind_ideas"].append({"t": c.start.isoformat(), "dir": idea.direction, "entry": str(idea.entry_price),
                               "allowed": idea.allowed, "blocked_by": idea.blocked_by,
                               "steps": list(getattr(idea, "steps", []) or [])})
print("== OTHER IDEAS 06:00-09:30 (ARB, EMA pullback, breakout)")
for c, idea in steps:
    if idea.strategy in ("Asian range breakout", "EMA pullback", "breakout") and datetime(2026,11,18,6,tzinfo=timezone.utc) <= c.start <= datetime(2026,11,18,9,30,tzinfo=timezone.utc):
        print(f(c.start), idea.strategy, idea.direction, idea.entry_price, "ALLOWED" if idea.allowed else "BLOCKED: " + idea.blocked_by[:200])
print("== PER 5m CANDLE 05:30-09:30: state seen while the candle forms (after the previous candle) | state after it | hourly read")
from strategies.common import SLOW_GRIND
for i, c in enumerate(week):
    if not (datetime(2026,11,18,5,30,tzinfo=timezone.utc) <= c.start <= datetime(2026,11,18,9,30,tzinfo=timezone.utc)): continue
    seen, after = runner.state_after(i - 1), runner.state_after(i)
    hr = runner._hourly_read(c.start).at(c.start)
    row = [c.start.isoformat(), seen.state, seen.direction, seen.trend_type, after.state, after.direction, after.trend_type,
           str(c.sell_open), str(c.sell_high), str(c.sell_low), str(c.sell_close), str(c.buy_close), hr.line()]
    out["per_candle"].append(row)
    print(f(c.start), f"seen: {seen.state} ({seen.direction}{', '+seen.trend_type if seen.trend_type else ''})",
          f"| after: {after.state} ({after.direction}{', '+after.trend_type if after.trend_type else ''})",
          f"| sell O {c.sell_open} H {c.sell_high} L {c.sell_low} C {c.sell_close}", "|", hr.line()[:160])
for c in week:
    if c.start >= T0 - timedelta(hours=1):
        out["candles"].append([c.start.isoformat(), str(c.sell_open), str(c.sell_high), str(c.sell_low), str(c.sell_close),
                               str(c.buy_open), str(c.buy_high), str(c.buy_low), str(c.buy_close)])
Path(sys.argv[1] if len(sys.argv) > 1 else "replay18.json").write_text(json.dumps(out, indent=1, default=str))
print("== SLOW GRIND sell watch, candle by candle, 06:00-12:00 (a fresh SlowGrind fed the same week candles and 21 EMA)")
from strategies.slow_grind.strategy import SlowGrind
from prices.indicators import ema as _ema
g = SlowGrind(s); allc = runner.warm + week; e21 = _ema(allc, "sell", s.slow_grind.ema_periods)
for c in week:
    g.on_candle(c, e21.get(c.start))
    if datetime(2026,11,18,6,tzinfo=timezone.utc) <= c.start < END:
        w = g.watch["sell"]
        print(f(c.start), f"sell L {c.sell_low} C {c.sell_close} EMA21 {e21.get(c.start):.1f}",
              "| ref", (f(w.ref.start) + " low " + str(w.ref.sell_low)) if w.ref else "none (reset)", "| row", len(w.row))
