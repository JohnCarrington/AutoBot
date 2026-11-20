"""Step 4: replay stored 5-minute candles through the LIVE code (02f6c7e, the code the price service loaded at
19 Nov 2026 18:43:54 UTC) in paper mode, and list every trade it opens. Nothing is sent: the order sender is in
paper mode and the pretend IG raises if anything calls it. Every data folder except the candle store (read only)
is redirected to a temporary copy, so no live file is written.

Run from an exact copy of 02f6c7e (git archive 02f6c7e | tar -x -C <dir>), so the imports are the live code:
    cd <dir> && nice -n 15 .venv/bin/python /opt/autobot/research/2026-11-20_losing_trades/replay_live_code.py \
        2026-11-16T12:00:00Z out.json
The first argument is any time inside the week to replay (from the week's open to its close, or to now). An
optional third argument ("-" for none) starts the engine at that moment instead, as the price service starts (19 Nov 18:44:38).
An optional fourth argument ends the replay there. The paper safety refusals (e.g. "already has 1 trade(s) open") are kept in the output.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path.cwd()))

from prices.calendar import MarketHours          # noqa: E402
from prices.model import parse_iso               # noqa: E402
from prices.store import CandleStore             # noqa: E402
from trading.engine import Trading               # noqa: E402
from trading.replay_check import _Alerts, _PretendIG, _settings   # noqa: E402

UTC = timezone.utc
COPY = ("news", "levels", "analyser", "history", "alerts", "planner")


class Over:
    """The real settings with every section's folder moved into a temporary folder (the candle store excepted)."""
    def __init__(self, base, tmp: Path):
        self._base, self._tmp = base, tmp
        self._cache = {}

    def __getattr__(self, name):
        if name in self._cache:
            return self._cache[name]
        v = getattr(self._base, name)
        if name != "candles" and hasattr(v, "__dict__"):
            d = dict(vars(v))
            changed = False
            for k, x in list(d.items()):
                if isinstance(x, (str, Path)) and str(x).startswith("/opt/autobot/data"):
                    d[k] = self._tmp / Path(str(x)).relative_to("/opt/autobot/data")
                    changed = True
            if changed:
                v = SimpleNamespace(**d)
        self._cache[name] = v
        return v


def main() -> int:
    at, out = parse_iso(sys.argv[1]), Path(sys.argv[2])
    holder = tempfile.TemporaryDirectory()
    tmp = Path(holder.name)
    for f in COPY:
        src = Path("/opt/autobot/data") / f
        if src.exists():
            shutil.copytree(src, tmp / f)
    base = _settings(tmp)
    s = Over(base, tmp)
    store = CandleStore(base.candles.folder, base.candles.compress_after_days)
    hours = MarketHours(base.market_hours)
    week_open, week_close = hours.session(at)
    end = min(week_close, datetime.now(UTC))
    if len(sys.argv) > 4:                    # an optional end (e.g. the next restart)
        end = min(end, parse_iso(sys.argv[4]))
    restart = parse_iso(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] != "-" else None
    if restart is None:                      # the live code's own replay mode, from the week's open
        clock = {"t": week_open}
        engine = Trading(s, store, _PretendIG(), _Alerts(), trading_on=False, now=lambda: clock["t"], replay_end=end)
        engine.start(week_open)
        candles = store.read_range("5m", week_open, end)
    else:                                    # as the price service starts: the week so far read, nothing sent for it
        clock = {"t": restart}
        engine = Trading(s, store, _PretendIG(), _Alerts(), trading_on=False, now=lambda: clock["t"])
        engine.start(restart)
        candles = [c for c in store.read_range("5m", restart, end) if c.end > restart]
    for c in candles:
        clock["t"] = c.start
        engine.on_candle(c.end)
    trades = []
    for idea, mt in engine.opened:
        last = mt.decisions[-1] if mt.decisions else None
        trades.append({
            "strategy": idea.strategy, "direction": idea.direction,
            "idea_time": idea.time.astimezone(UTC).isoformat(), "entry": str(idea.entry_price),
            "stop_pips": str(mt.stop_pips), "closed": last.at.astimezone(UTC).isoformat() if (last and not mt.open) else None,
            "close_kind": last.kind if last else None,
            "pips": str(mt.total_pips()) if (last and not mt.open) else None,
            "steps": list(getattr(idea, "steps", []) or [])[-4:],
        })
    refused = []
    for j in (tmp / "orders").rglob("*.jsonl"):
        for line in j.read_text().splitlines():
            r = json.loads(line)
            if r.get("event") == "safety refused":
                refused.append(r)
    out.write_text(json.dumps({"week_open": week_open.isoformat(), "restart": sys.argv[3] if restart else None,
                               "end": end.isoformat(), "trades": trades, "safety_refused": refused}, indent=1))
    print(f"{len(trades)} paper trades from {week_open} to {end}; written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
