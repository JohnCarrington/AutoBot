"""Johnny's trend-day rule (owner's decision, 21 Nov 2026), checked on the replays of 5d7942e: a slow grind trade,
including one opened before 06:00, makes the day a trend day if it is in profit, as IG would close it, at any point
between 06:00 and 09:00 UK while it is open. As IG would close it: a sell at the buy price, a buy at the sell price,
from the paper fill level. Prints the first 5-minute candle where that happens, and the trade's position at every
candle from 06:00 to 09:00. Reads the candle store and a replay JSON (replay_next.py / replay_day.py output).

    cd <worktree at 5d7942e> && .venv/bin/python trend_day_check.py <replay.json> <day YYYY-MM-DD>
"""
import json, sys
from datetime import datetime, time, timedelta
from decimal import Decimal as D
from zoneinfo import ZoneInfo
sys.path.insert(0, ".")
from prices.store import CandleStore
UK = ZoneInfo("Europe/London")
r = json.load(open(sys.argv[1])); day = datetime.fromisoformat(sys.argv[2]).date()
W0 = datetime.combine(day, time(6, 0), tzinfo=UK); W1 = datetime.combine(day, time(9, 0), tzinfo=UK)
fills = {(o["strategy"], o["direction"], o["opened_utc"]): D(o["level"]) for o in r["orders"] if o.get("event") == "opened"}
import tomllib, pathlib
cfg = tomllib.loads(pathlib.Path("config/settings.toml").read_text())
store = CandleStore(pathlib.Path(cfg["candles"]["folder"]) / "GBPUSD", cfg["candles"]["compress_after_days"])   # the pair's folder
candles = list(store.read_range("5m", W0 - timedelta(hours=10), W1 + timedelta(hours=1)))
on = None
for o in r["opened"]:
    if o["strategy"] != "slow grind": continue
    t = datetime.fromisoformat(o["time"]); closed = datetime.fromisoformat(o["closed"]) if o["closed"] else None
    if t >= W1 or (closed and closed < W0): continue
    fill = [v for (s, d, ou), v in fills.items() if s == "slow grind" and d == o["direction"] and ou[:16] == o["time"][:16]][0]
    sell = o["direction"] == "sell"
    end = f"closed {closed.astimezone(UK):%H:%M} ({o['how'][:60]}, {o['pips']})" if closed else "still open at the replay's end"
    print(f"slow grind {o['direction']} opened {t.astimezone(UK):%a %d %b %H:%M} UK, fill {fill}; {end}")
    for c in candles:
        if not (max(W0, t) <= c.start < W1) or (closed and c.start > closed): continue
        best = (fill - c.buy_low) if sell else (c.sell_high - fill)
        worst = (fill - c.buy_high) if sell else (c.sell_low - fill)
        cl = (fill - c.buy_close) if sell else (c.sell_close - fill)
        flag = ""
        if best > 0 and on is None:
            on = c.start; flag = "  <= TREND DAY ON (first candle in profit)"
        print(f"  {c.start.astimezone(UK):%H:%M}  best {best:+.1f}  worst {worst:+.1f}  close {cl:+.1f}{flag}")
print("RESULT:", f"{day} trend day ON from the {on.astimezone(UK):%H:%M} UK candle" if on else f"{day} trend day NOT on")
