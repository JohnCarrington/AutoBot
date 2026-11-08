"""Replay check of the full wired path: over Monday 26 October to Friday 6 November 2026, the stored candles go one
at a time through the bot as the price service runs it (trading/engine.py: the analyser, the strategies, the
safety rules in the order sender, the order sender in paper mode, the trade manager), and every trade must open
and close at the same time and price as in docs/research/all_strategies_together_20261108.md ("Every trade").
Reads the candle store and the calendar; never contacts IG (a pretend IG gives the funds); writes only to a
temporary folder.

    .venv/bin/python -m trading.replay_check
Exit code 0 when every trade matches, 1 otherwise.
"""

from __future__ import annotations

import sys
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from prices.calendar import MarketHours
from prices.model import parse_iso
from prices.store import CandleStore
from trade_manager.replay_check import research_trades
from trading.engine import Trading

UK = ZoneInfo("Europe/London")
WEEKS = ("2026-10-27T12:00:00Z", "2026-11-03T12:00:00Z")


class _Over:
    """The real settings with the order sender's and trade manager's folders moved to a temporary folder."""
    def __init__(self, base, folder: Path):
        self._base = base
        self.orders = SimpleNamespace(**(vars(base.orders) | {"folder": folder / "orders"}))
        self.trade_manager = SimpleNamespace(**(vars(base.trade_manager) | {"folder": folder / "trade_manager"}))
        self.safety = SimpleNamespace(**(vars(base.safety) | {"folder": folder / "safety"}))
        self.records = SimpleNamespace(**(vars(base.records) | {"folder": folder / "records"}))
        self.trading = SimpleNamespace(**(vars(base.trading) | {"pause_file": folder / "control" / "pause"}))

    def __getattr__(self, name):
        return getattr(self._base, name)


class _PretendIG:
    """Never sends anything: the order sender is in paper mode. It only gives the account's funds."""
    base_url, account_active = None, True

    def account_balance(self):
        return {"available": 20000.0}

    def request(self, *a, **k):
        raise AssertionError("the replay check must never call IG")


class _Alerts:
    def problem(self, key, text):
        print(f"  alert {key}: {text}")

    def info(self, text, key=None):
        pass


def _settings(folder: Path):
    """The real settings and the .env switch values, with TRADING off (the check always runs in paper mode; the
    real .env may not have the switch yet). The secrets are never read."""
    from datetime import time as tm
    from config.env_file import env_path
    from config.settings_loader import load_settings
    from config.switches import SWITCHES, read_switches
    values, problems = read_switches(env_path())
    if [p for p in problems if "TRADING" not in p]:
        raise SystemExit("Switch problems in .env: " + "; ".join(problems))
    lines = []
    for key, (name, _) in SWITCHES.items():
        v = False if key == "TRADING" else values.get(name)
        v = ",".join(v) if isinstance(v, tuple) else ("on" if v else "off") if isinstance(v, bool) else \
            v.strftime("%H:%M") if isinstance(v, tm) else v
        lines.append(f"{key}={v}")
    p = folder / "switches.env"
    p.write_text("\n".join(lines) + "\n")
    return load_settings(switches_from=p).for_pair("GBPUSD")


def main() -> int:
    tmp_holder = tempfile.TemporaryDirectory()
    base = _settings(Path(tmp_holder.name))
    off = [k for k in ("slow_grind", "ema_pullback", "bollinger_bounce", "range_trade", "breakout", "level_reversal")
           if not getattr(base.switches, k)]
    if off:
        print(f"The research had all six strategies switched on; these are off in .env: {', '.join(off)}.")
        return 1
    store = CandleStore(base.candles.folder, base.candles.compress_after_days)
    hours = MarketHours(base.market_hours)
    got = Counter()
    with tempfile.TemporaryDirectory() as tmp:
        s = _Over(base, Path(tmp))
        for w in WEEKS:
            week_open, week_close = hours.session(parse_iso(w))
            clock = {"t": week_open}
            engine = Trading(s, store, _PretendIG(), _Alerts(), trading_on=False, now=lambda: clock["t"],
                             replay_end=week_close)
            engine.start(week_open)
            for c in store.read_range("5m", week_open, week_close):
                clock["t"] = c.start                        # the order goes when the candle reached its entry
                engine.on_candle(c.end)
            for idea, mt in engine.opened:
                last = mt.decisions[-1] if mt.decisions else None
                closed = last.at if (last and not mt.open) else None
                got[(idea.strategy, f"{idea.time.astimezone(UK):%a %d %b %H:%M}", idea.direction.upper(),
                     f"{closed.astimezone(UK):%a %d %b %H:%M}" if closed else "still open",
                     f"{float(mt.total_pips()):+.1f}" if closed else "-")] += 1
    want = research_trades()
    same = sum((want & got).values())
    print(f"Research trades: {sum(want.values())}; the full wired path's: {sum(got.values())}; "
          f"same entry, close time and pips: {same}.")
    order = lambda k: (k[0], datetime.strptime("2026 " + k[1], "%Y %a %d %b %H:%M"))  # noqa: E731
    for k in sorted((want - got).elements(), key=order):
        print(f"  only in the research: {k}")
    for k in sorted((got - want).elements(), key=order):
        print(f"  only from the wired path: {k}")
    return 0 if want == got else 1


if __name__ == "__main__":
    sys.exit(main())
