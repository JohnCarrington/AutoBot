"""Per UK weekday, 06:00-20:25 UK 5-minute candles (chart / sell price), the facts a trend-day measure can use.
Bollinger (20, 2) and the 8/13/21 EMAs with the bot's own indicator code on the continuous 5-minute series."""
import sys, json, pickle
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo
sys.path.insert(0, "/home/autobot/worktrees/autobot-sg-trend-day")
from prices.indicators import bollinger, ema
from prices.model import parse_iso
from prices.store import CandleStore
UK, UTC = ZoneInfo("Europe/London"), timezone.utc
store = CandleStore("/opt/autobot/data/research/stp_validation_store/GBPUSD", 999999)
cs = store.read_range("5m", parse_iso("2023-12-28T00:00:00Z"), parse_iso("2026-11-20T00:00:00Z"))
bb = bollinger(cs, "sell", 20, 2); e8 = ema(cs, "sell", 8); e21 = ema(cs, "sell", 21)
by = defaultdict(list)
for c in cs:
    u = c.start.astimezone(UK)
    if u.weekday() < 5 and time(6, 0) <= u.time() < time(20, 30): by[u.date()].append(c)
out = {}
for d, v in sorted(by.items()):
    if d < date(2024, 1, 2): continue
    rows = []
    for c in v:
        b = bb.get(c.start)
        if b is None: continue
        rows.append(dict(t=c.start, o=float(c.sell_open), h=float(c.sell_high), l=float(c.sell_low), c=float(c.sell_close),
                         up=float(b.upper), mid=float(b.middle), lo=float(b.lower), e8=float(e8[c.start]), e21=float(e21[c.start])))
    out[d] = rows
pickle.dump(out, open("daystats.pkl", "wb"))
print(len(out), "weekdays")
