"""Read-only check replay for ROOM_TO_LEVEL (PULLBACK_ENTRY on, as live) (owner, 19 November 2026): the full wired path (trading/engine.py) in
PAPER mode, a pretend IG that fails if anything is ever sent; switches as the live .env of 19 November 2026 (all ten
strategies on, STOP_LOSS_PIPS 12, ONE_SIGNAL_ONE_TRADE on, PLANNER_OBSERVE off) with ROOM_TO_LEVEL on or off.
Based on /home/autobot/research/first_build_plus_20261119/replay_9_10_nov.py.

    PYTHONPATH=<worktree> .venv/bin/python pullback_replay.py <out.json> on|off <week-noon-UTC> <end-UTC> <first day> [<last day>]
"""
import json, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo
from config.settings_loader import load_settings
from prices.calendar import MarketHours
from prices.store import CandleStore
from trading.engine import Trading
UK = ZoneInfo("Europe/London"); UTC = timezone.utc
SW = {"PAIRS_ON": "GBPUSD", "NEW_TRADES_FROM": "06:00", "NEW_TRADES_UNTIL": "20:30", "STRATEGY_SLOW_GRIND": "on",
      "STRATEGY_EMA_PULLBACK": "on", "STRATEGY_BOLLINGER_BOUNCE": "on", "STRATEGY_BOLLINGER_BOUNCE_5M": "on",
      "STRATEGY_RANGE_TRADE": "on", "STRATEGY_BREAKOUT": "on", "STRATEGY_LEVEL_REVERSAL": "on",
      "STRATEGY_ASIAN_RANGE_BREAKOUT": "on", "STRATEGY_SESSION_SWEEP": "on", "STRATEGY_NEW_YORK_OPEN_REVERSAL": "on",
      "TRADING": "off", "STOP_LOSS_PIPS": "12", "STOP_LOSS_PIPS_EMA_PULLBACK": "12", "TAKE_PROFIT_PIPS": "100",
      "BOUNCE_ONLY_NEAR_TIMES": "off", "PLANNER_OBSERVE": "off", "ONE_SIGNAL_ONE_TRADE": "on"}

class PretendIG:
    base_url, account_active = None, True

    def account_balance(self):
        return {"available": 20000.0}

    def request(self, *a, **k):
        raise AssertionError("the replay must never call IG")


class Alerts:
    def problem(self, key, text):
        pass

    def info(self, text, key=None):
        pass


class Over:
    def __init__(self, base, folder):
        self._base = base
        self.orders = SimpleNamespace(**(vars(base.orders) | {"folder": folder / "orders"}))
        self.trade_manager = SimpleNamespace(**(vars(base.trade_manager) | {"folder": folder / "trade_manager"}))
        self.records = SimpleNamespace(**(vars(base.records) | {"folder": folder / "records"})) \
            if hasattr(base, "records") else None

    def __getattr__(self, name):
        return getattr(self._base, name)



def main(out, pullback, week_noon, end, days):
    if True:
        tmp = Path(out + ".d"); tmp.mkdir(exist_ok=True)
        env = tmp / "switches.env"
        env.write_text("".join(f"{k}={v}\n" for k, v in (SW | {"PULLBACK_ENTRY": "on", "ROOM_TO_LEVEL": pullback}).items()))
        base = load_settings(switches_from=env).for_pair("GBPUSD")
        assert base.switches.room_to_level == (pullback == "on") and base.switches.pullback_entry
        s = Over(base, tmp)
        if s.records is None:
            del s.records
        store = CandleStore(base.candles.folder, base.candles.compress_after_days)
        week_open, week_close = MarketHours(base.market_hours).session(datetime.fromisoformat(week_noon))
        end = datetime.fromisoformat(end)
        clock = {"t": week_open}
        engine = Trading(s, store, PretendIG(), Alerts(), trading_on=False, now=lambda: clock["t"], replay_end=week_close)
        engine.start(week_open)
        for c in store.read_range("5m", week_open, end):
            clock["t"] = c.start
            engine.on_candle(c.end)
        rows = []
        for idea, mt in engine.opened:
            last = mt.decisions[-1] if mt.decisions else None
            closed = last.at if (last and not mt.open) else None
            rows.append({"strategy": idea.strategy, "direction": idea.direction,
                         "opened_uk": f"{idea.time.astimezone(UK):%a %d %b %H:%M}", "entry": str(idea.entry_price),
                         "closed_uk": f"{closed.astimezone(UK):%a %d %b %H:%M}" if closed else None,
                         "how": last.kind if (last and not mt.open) else None,
                         "pips": f"{float(mt.total_pips()):+.1f}" if closed else None,
                         "steps": idea.steps if idea.strategy in ("breakout", "Asian range breakout") else None})
        r = engine.runner
        notes = [(f"{t.astimezone(UK):%a %d %b %H:%M}", name, d, txt) for name, ns in
                 (("breakout", r.breakout.notes), ("Asian range breakout", r.sessions[0].notes)) for t, d, txt in ns]
    rows = [x for x in rows if x["opened_uk"][:6] in days]
    notes = sorted([n for n in notes if n[0][:6] in days], key=lambda n: datetime.strptime(n[0][4:], "%d %b %H:%M"))
    Path(out).write_text(json.dumps({"room_to_level": pullback, "trades": rows, "notes": notes}, indent=1, default=str))
    print(len(rows), "trades")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], tuple(sys.argv[5:]))
