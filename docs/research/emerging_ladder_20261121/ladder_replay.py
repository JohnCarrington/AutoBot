"""Read-only check replay for Johnny's emerging-trend ladder (owner, 21 November 2026): the full wired path
(trading/engine.py) in PAPER mode with a pretend IG that fails if anything is ever sent. Switches: the live .env's
switch lines as they stand (only the keys config/switches.py reads; TRADING forced off), the entry filters OFF
(HOURLY_CONTEXT, ENTRY_NEAR_EMA8), and EMERGING_LADDER on or off, so only the exit changes. Writes every trade opened
with its analyser state at open, how it closed, its pips and its stop moves. Based on
docs/research/entry_filters_20261121/entry_filters_replay.py.

    PYTHONPATH=<worktree> .venv/bin/python ladder_replay.py <out.json> on|off <week-noon-UTC> <end-UTC>
"""
import json, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo
from config.settings_loader import load_settings
from config.switches import SWITCHES, OPTIONAL
from prices.calendar import MarketHours
from prices.store import CandleStore
from trading.engine import Trading
UK = ZoneInfo("Europe/London"); UTC = timezone.utc
LIVE_ENV = Path("/opt/autobot/.env")


def live_switches() -> dict:
    out = {}
    for line in LIVE_ENV.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            if k.strip() in SWITCHES:                    # never the secrets: only the switch keys
                out[k.strip()] = v.strip()
    return out | {"TRADING": "off"}


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
        self.records = SimpleNamespace(**(vars(base.records) | {"folder": folder / "records"}))
        self.trading = SimpleNamespace(**(vars(base.trading) | {"pause_file": folder / "no_pause_file"}))

    def __getattr__(self, name):
        return getattr(self._base, name)


def main(out, ladder, week_noon, end):
    sw = live_switches() | {"HOURLY_CONTEXT": "off", "ENTRY_NEAR_EMA8": "off", "EMERGING_LADDER": ladder}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        env = tmp / "switches.env"
        env.write_text("".join(f"{k}={v}\n" for k, v in sw.items()))
        base = load_settings(switches_from=env).for_pair("GBPUSD")
        assert base.switches.hourly_context is False and base.switches.entry_near_ema8 is False
        assert base.switches.emerging_ladder == (ladder == "on") and base.switches.trading is False
        s = Over(base, tmp)
        store = CandleStore(base.candles.folder, base.candles.compress_after_days)
        week_open, week_close = MarketHours(base.market_hours).session(datetime.fromisoformat(week_noon))
        end = datetime.fromisoformat(end)
        clock = {"t": week_open}
        engine = Trading(s, store, PretendIG(), Alerts(), trading_on=False, now=lambda: clock["t"], replay_end=week_close)
        engine.start(week_open)
        for c in store.read_range("5m", week_open, end):
            clock["t"] = c.start
            engine.on_candle(c.end)
        trades = []
        for idea, mt in engine.opened:
            last = mt.decisions[-1] if mt.decisions else None
            closed = last.at if (last and not mt.open) else None
            trades.append({"strategy": idea.strategy, "direction": idea.direction, "time_utc": idea.time.isoformat(),
                           "opened_uk": f"{idea.time.astimezone(UK):%a %d %b %H:%M}", "entry": str(idea.entry_price),
                           "fill": str(mt.fill), "stop_pips": str(mt.stop_pips), "take_profit_pips": str(mt.take_profit_pips),
                           "market_state": mt.market_state, "how": last.kind if closed else None,
                           "closed_utc": closed.isoformat() if closed else None,
                           "pips": f"{float(mt.total_pips()):+.1f}" if closed else None,
                           "best": None if mt.best is None else str(mt.best), "stop_moves": mt.stop_moves})
    Path(out).write_text(json.dumps({"ladder": ladder, "switches": {k: v for k, v in sw.items()}, "trades": trades},
                                    indent=1, default=str))
    print(len(trades), "trades;", sum(1 for t in trades if (t["market_state"] or "").startswith("emerging trend")),
          "opened in emerging trend")


if __name__ == "__main__":
    main(*sys.argv[1:5])
