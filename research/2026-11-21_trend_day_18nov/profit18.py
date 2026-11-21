"""Each slow grind sell setup (from replay18.json) checked on IG's buy price (the price a sell closes at): in profit
between 06:00 and 09:00 UK on 18 Nov? Two views: (A) no exits at all; (B) the slow grind's own exits in the live
settings (stop 15, take profit 20, profit lock: once 15 up in an earlier candle, closed if price comes back to 10 up).
Within a candle the stop is checked first (the cautious order). Read-only."""
import json, sys
from datetime import datetime
from decimal import Decimal as D
from zoneinfo import ZoneInfo
UK = ZoneInfo("Europe/London")
r = json.load(open(sys.argv[1]))
C = [(datetime.fromisoformat(c[0]), *map(D, c[1:])) for c in r["candles"]]  # t, sO,sH,sL,sC, bO,bH,bL,bC
W0, W1 = datetime.fromisoformat("2026-11-18T06:00:00+00:00"), datetime.fromisoformat("2026-11-18T09:00:00+00:00")
f = lambda t: t.astimezone(UK).strftime("%a %H:%M")
for i in r["grind_ideas"]:
    if i["dir"] != "sell": continue
    t0, e = datetime.fromisoformat(i["t"]), D(i["entry"])
    later = [c for c in C if c[0] > t0]
    ent = [c for c in C if c[0] == t0][0]
    # A: no exits
    win = [c for c in C if W0 <= c[0] < W1 and c[0] >= t0]
    bestA = max((e - c[7] for c in win), default=None); worstA = min((e - c[6] for c in win), default=None)
    at9 = [c for c in C if c[0] == datetime.fromisoformat("2026-11-18T08:55:00+00:00")][0]
    A = f"best {bestA:+.1f}, worst {worstA:+.1f}, at 09:00 {e - at9[8]:+.1f}" if win else "n/a"
    # B: own exits
    best, end = D(-99), None
    seq = later
    for c in seq:
        if c[6] >= e + 15: end = (c[0], "stop", D(-15)); break
        if e - c[7] >= 20: end = (c[0], "take profit", D(20)); break
        if best >= 15 and e - c[6] <= 10: end = (c[0], "profit lock", D(10)); break
        best = max(best, e - c[7])
    status = []
    if end and end[0] < W0: status.append(f"closed before 06:00 ({end[1]} {f(end[0])}, {end[2]:+})")
    else:
        w = [c for c in C if max(W0, t0) <= c[0] < W1 and (end is None or c[0] <= end[0])]
        b = max(e - c[7] for c in w); b = min(b, D(20))
        status.append(f"open in the window; best {b:+.1f}")
        if end and end[0] < W1: status.append(f"closed {end[1]} {f(end[0])} {end[2]:+}")
        else: status.append(f"at 09:00 {e - at9[8]:+.1f}" + (f"; later {end[1]} {f(end[0])} {end[2]:+}" if end else ""))
    entc = f"entry candle buy H {ent[6]} L {ent[7]}"
    print(f"{f(t0)} sell {e} | A (no exits): {A} | B (own exits): {'; '.join(status)} | {entc}")
