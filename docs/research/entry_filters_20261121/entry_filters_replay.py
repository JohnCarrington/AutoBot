"""Read-only check replay for the entry filters (owner, 21 November 2026): the full wired path (trading/engine.py) in
PAPER mode with a pretend IG that fails if anything is ever sent. Switches: the live .env's switch lines as they
stand (only the keys config/switches.py reads; TRADING forced off), with the entry filters as the mode says:
  on    HOURLY_CONTEXT and ENTRY_NEAR_EMA8 on (the first check, rule 2)
  2b    HOURLY_CONTEXT, RSI_STRETCH and TREND_DAY_RSI_OFF on, ENTRY_NEAR_EMA8 off (owner, 21 November 2026)
  off   all four off
EMERGING_LADDER (on this branch from another build) is held off in every mode, so only the filters differ. Writes the trades opened and every entry-filter refusal. Based on
docs/research/pullback_entry_20261119/pullback_replay.py.

    AUTOBOT_ENV_FILE=/opt/autobot/.env PYTHONPATH=<worktree> .venv/bin/python entry_filters_replay.py \
        <out.json> on|off <week-noon-UTC> <end-UTC>
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


MODES = {"on": {"HOURLY_CONTEXT": "on", "ENTRY_NEAR_EMA8": "on", "RSI_STRETCH": "off", "TREND_DAY_RSI_OFF": "off"},
         "2b": {"HOURLY_CONTEXT": "on", "ENTRY_NEAR_EMA8": "off", "RSI_STRETCH": "on", "TREND_DAY_RSI_OFF": "on"},
         "off": {"HOURLY_CONTEXT": "off", "ENTRY_NEAR_EMA8": "off", "RSI_STRETCH": "off", "TREND_DAY_RSI_OFF": "off"}}


def main(out, filters, week_noon, end):
    sw = live_switches() | MODES[filters] | {"EMERGING_LADDER": "off"}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        env = tmp / "switches.env"
        env.write_text("".join(f"{k}={v}\n" for k, v in sw.items()))
        base = load_settings(switches_from=env).for_pair("GBPUSD")
        assert base.switches.hourly_context == (filters != "off") and base.switches.rsi_stretch == (filters == "2b")
        assert base.switches.trading is False
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
                           "how": last.kind if closed else None,
                           "pips": f"{float(mt.total_pips()):+.1f}" if closed else None,
                           "filters": [x for x in idea.steps if x.startswith("entry filters:")]})
        refused = [json.loads(l) for dec in sorted((tmp / "records").rglob("decisions.jsonl"))
                   for l in dec.read_text().splitlines()]
        trend_days = [r for r in refused if r["kind"].startswith("trend day")]
        refused = [r for r in refused if r["kind"] == "entry filter refused"]
    Path(out).write_text(json.dumps({"filters": filters, "switches": {k: v for k, v in sw.items()},
                                     "trades": trades, "refused": refused, "trend_days": trend_days},
                                    indent=1, default=str))
    print(len(trades), "trades;", len(refused), "refused by the entry filters;", len(trend_days), "trend-day records")


if __name__ == "__main__":
    main(*sys.argv[1:5])
