"""Read-only replay for research/2026-11-21_trend_day_18nov, part 2: Tue 17 Nov 22:00 to Wed 18 Nov 12:00 UK through
the code for the next restart (5d7942e: first-build-plus with the pullback entry and the STP forecaster) and the
switches in the live .env of 21 Nov 2026 (TRADING off). The full wired path (trading/engine.py) in PAPER mode, from
the week's open; a pretend IG that fails if anything is ever sent. Reads the candle store; writes only to a temp folder.

    cd <worktree at 5d7942e> && .venv/bin/python replay_day.py out.json <from UTC> <to UTC> <per-candle from UTC> <per-candle to UTC>
"""
import json, sys, tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo
sys.path.insert(0, ".")
from config.settings_loader import load_settings
from prices.calendar import MarketHours
from prices.store import CandleStore
from trading.engine import Trading
UK = ZoneInfo("Europe/London"); UTC = timezone.utc
# The switches in /opt/autobot/.env on 21 Nov 2026 (only TRADING changed, to off). Switches this build does not know
# (HOURLY_READ, TREND_STILL_GOING, ANALYSER_*, Stage 4, EMA_PULLBACK_*) are not read by it; listed as in .env.
SW = {"TRADING": "off", "IG_ACC_TYPE": "DEMO", "PAIRS_ON": "GBPUSD", "NEW_TRADES_FROM": "06:00", "NEW_TRADES_UNTIL": "20:30",
      "STRATEGY_SLOW_GRIND": "on", "STRATEGY_BREAKOUT": "on", "STRATEGY_EMA_PULLBACK": "on",
      "STRATEGY_BOLLINGER_BOUNCE": "on", "STRATEGY_LEVEL_REVERSAL": "on", "STRATEGY_RANGE_TRADE": "on",
      "STRATEGY_ASIAN_RANGE_BREAKOUT": "on", "STRATEGY_SESSION_SWEEP": "on", "STRATEGY_NEW_YORK_OPEN_REVERSAL": "on",
      "HOURLY_READ": "on", "TREND_STILL_GOING": "on", "STOP_LOSS_PIPS": "12", "STOP_LOSS_PIPS_EMA_PULLBACK": "12",
      "TAKE_PROFIT_PIPS": "100", "PLANNER_OBSERVE": "on", "ANALYSER_USES_HOURLY": "on", "ANALYSER_GOVERNS_ALL": "on",
      "ONE_SIGNAL_ONE_TRADE": "on", "SCALE_OUT_REVERSAL": "on", "TRAIL_NO_LOSS": "on", "LR_ENTRY_NEAR_LEVEL": "on",
      "LEVEL_STOPS": "on", "STRATEGY_BOLLINGER_BOUNCE_5M": "on", "EMA_PULLBACK_TRADING_HOURS": "on",
      "EMA_PULLBACK_ONE_AT_A_TIME": "on"}


class PretendIG:
    base_url, account_active = None, True
    def account_balance(self): return {"available": 20000.0}
    def request(self, *a, **k): raise AssertionError("the replay must never call IG")


class Alerts:
    def problem(self, key, text): pass
    def info(self, text, key=None): pass


class Over:
    def __init__(self, base, folder):
        self._base = base
        self.orders = SimpleNamespace(**(vars(base.orders) | {"folder": folder / "orders"}))
        self.trade_manager = SimpleNamespace(**(vars(base.trade_manager) | {"folder": folder / "trade_manager"}))
        if hasattr(base, "records"):
            self.records = SimpleNamespace(**(vars(base.records) | {"folder": folder / "records"}))
    def __getattr__(self, name): return getattr(self._base, name)


T0 = datetime.fromisoformat(sys.argv[2]); END = datetime.fromisoformat(sys.argv[3])
W0 = datetime.fromisoformat(sys.argv[4]); W1 = datetime.fromisoformat(sys.argv[5])
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp); env = tmp / "switches.env"
    env.write_text("".join(f"{k}={v}\n" for k, v in SW.items()))
    base = load_settings(switches_from=env).for_pair("GBPUSD")
    print("switches read by this build:", {k: v for k, v in vars(base.switches).items()} if hasattr(base, "switches") else "?")
    s = Over(base, tmp)
    store = CandleStore(base.candles.folder, base.candles.compress_after_days)
    week_open, week_close = MarketHours(base.market_hours).session(T0)
    clock = {"t": week_open}
    engine = Trading(s, store, PretendIG(), Alerts(), trading_on=False, now=lambda: clock["t"], replay_end=week_close)
    engine.start(week_open)
    for c in store.read_range("5m", week_open, END):
        if c.end > END: break
        clock["t"] = c.start
        engine.on_candle(c.end)
    out = {"decisions": [], "orders": [], "opened": [], "changes": [], "per_candle": [], "grind_notes": []}
    for p in (tmp / "records").rglob("decisions.jsonl"):
        for line in p.read_text().splitlines():
            r = json.loads(line)
            if r["time_utc"] >= T0.isoformat()[:16]: out["decisions"].append(r)
    for p in (tmp / "orders").rglob("*.jsonl"):
        for line in p.read_text().splitlines():
            r = json.loads(line)
            if (r.get("time_utc") or "") >= T0.isoformat()[:16]: out["orders"].append(r | {"_file": p.name})
    for idea, mt in engine.opened:
        if idea.time < T0: continue
        last = mt.decisions[-1] if mt.decisions else None
        out["opened"].append({"strategy": idea.strategy, "direction": idea.direction, "time": idea.time.isoformat(),
                              "entry": str(idea.entry_price), "open": mt.open,
                              "closed": last.at.isoformat() if (last and not mt.open) else None,
                              "how": f"{last.kind}: {last.why}" if (last and not mt.open) else None,
                              "pips": str(mt.total_pips()) if not mt.open else None, "steps": idea.steps,
                              "decisions": [[d.at.isoformat(), d.kind, str(d.price), str(d.pips), d.why] for d in mt.decisions]})
    for ch in engine.tracker.changes:
        if ch.time >= T0 - timedelta(hours=1):
            out["changes"].append([ch.time.isoformat(), ch.state, ch.direction, ch.trend_type, ch.reason])
    r = engine.runner
    for i, c in enumerate(r.week):
        if W0 <= c.start <= W1:
            seen, after = r.state_after(i - 1), r.state_after(i)
            out["per_candle"].append([c.start.isoformat(), seen.state, seen.direction, seen.trend_type,
                                      after.state, after.direction, after.trend_type, str(c.sell_close), str(c.buy_close)])
    out["grind_notes"] = [[t.isoformat(), d, x] for t, d, x in r.grind.notes if t >= T0 - timedelta(hours=1)]
Path(sys.argv[1]).write_text(json.dumps(out, indent=1, default=str))
print("done", len(out["decisions"]), "decisions", len(out["opened"]), "opened")
