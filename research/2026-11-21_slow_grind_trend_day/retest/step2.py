"""Step 2: Johnny's slow grind signal (unchanged) against the trend-day measure (trendday.py).
The slow grind trades are the earlier study's (../2026-11-21_slow_grind_trend_day/slow_grind_trades.csv: the live
code 4635175, firing from 00:00 UK). For each trade, its best profit in 06:00-09:00 UK as IG would close it, by
the earlier study's own per-candle rules (days.py in_profit_time), now keeping the amount:
  * the candle it opened in: its close (and, if it also closed in that candle, its result);
  * the candle it closed in: its result if in profit, else that candle's open;
  * every candle in between: its best price (buy: sell high; sell: buy low).
Signal at threshold X: a side's best is above 0 (Johnny's rule) or at least X (+5, +10, +15, extra information);
both sides = no signal."""
import csv, pickle, random, sys
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "/home/autobot/worktrees/autobot-sg-trend-day")
from prices.model import parse_iso
from prices.store import CandleStore
UK, UTC = ZoneInfo("Europe/London"), timezone.utc
OLD = "/home/autobot/worktrees/autobot-sg-trend-day/research/2026-11-21_slow_grind_trend_day"
store = CandleStore("/opt/autobot/data/research/stp_validation_store/GBPUSD", 999999)
by_start = {c.start: c for c in store.read_range("5m", parse_iso("2024-01-01T00:00:00Z"), parse_iso("2026-11-20T00:00:00Z"))}
def at(d, h, m): return datetime.combine(d, time(h, m), tzinfo=UK).astimezone(UTC)
trades = defaultdict(list)
for t in csv.DictReader(open(f"{OLD}/slow_grind_trades.csv")):
    t["o"], t["cl"] = parse_iso(t["opened"]), parse_iso(t["closed_bar"])
    trades[t["o"].astimezone(UK).date()].append(t)
def best(t, w0, w1):
    fill, buy = float(t["fill"]), t["direction"] == "buy"; res = float(t["pips"]) if t["pips"] not in ("", None) else None
    b, k = None, t["o"]
    while k <= t["cl"]:
        c = by_start.get(k)
        if c is not None and w0 <= k < w1:
            if k == t["o"]:
                p = (float(c.sell_close) - fill) if buy else (fill - float(c.buy_close))
                if k == t["cl"] and res is not None and res > 0: p = max(p, res)
            elif k == t["cl"]:
                p = res if (res is not None and res > 0) else ((float(c.sell_open) - fill) if buy else (fill - float(c.buy_open)))
            else:
                p = (float(c.sell_high) - fill) if buy else (fill - float(c.buy_low))
            b = p if b is None else max(b, p)
        k += timedelta(minutes=5)
    return b
old = {r["day"]: r for r in csv.DictReader(open(f"{OLD}/days.csv"))}
TD = pickle.load(open("trenddays.pkl", "rb"))
def is_trend(x): return x["trend"]     # the measure (Step 1, trendday.py)
best_by_day = {}
for ds, r in old.items():
    d = date.fromisoformat(ds); bb = {"buy": None, "sell": None}
    for t in trades.get(d, []):
        v = best(t, at(d, 6, 0), at(d, 9, 0))
        if v is not None and (bb[t["direction"]] is None or v > bb[t["direction"]]): bb[t["direction"]] = v
    best_by_day[d] = bb
def signal(bb, x):
    ok = {s for s, v in bb.items() if v is not None and (v > 0 if x == 0 else v >= x)}
    return "both" if len(ok) == 2 else "up" if "buy" in ok else "down" if "sell" in ok else "none"
# check: threshold 0 must reproduce the earlier study's signal on every day
mism = [ds for ds, r in old.items() if signal(best_by_day[date.fromisoformat(ds)], 0) != r["signal"]]
print("days where the signal differs from the earlier study:", len(mism), mism[:5])
days = sorted(d for d in best_by_day if old[d.isoformat()]["usable"] == "True" and d in TD)
print("days used (usable in the earlier study and measured here):", len(days))
trend = {d: TD[d]["dir"] for d in days if is_trend(TD[d])}
print("trend days among them:", len(trend), "up", sum(v == "up" for v in trend.values()), "down", sum(v == "down" for v in trend.values()))
out = {}
for x in (0, 5, 10, 15):
    sig = {d: signal(best_by_day[d], x) for d in days}
    on = [d for d in days if sig[d] in ("up", "down")]
    right = [d for d in on if trend.get(d) == sig[d]]; wrong_dir = [d for d in on if d in trend and trend[d] != sig[d]]
    not_trend = [d for d in on if d not in trend]
    caught = [d for d in trend if sig[d] == trend[d]]
    miss_none = [d for d in trend if sig[d] == "none"]; miss_both = [d for d in trend if sig[d] == "both"]
    miss_opp = [d for d in trend if sig[d] in ("up", "down") and sig[d] != trend[d]]
    out[x] = dict(on=len(on), right=len(right), wrong_dir=len(wrong_dir), not_trend=len(not_trend), both=sum(s == "both" for s in sig.values()),
                  none=sum(s == "none" for s in sig.values()), trend=len(trend), caught=len(caught), miss_none=len(miss_none), miss_both=len(miss_both),
                  miss_opp=len(miss_opp), lists=dict(caught=caught, miss_none=miss_none, miss_both=miss_both, miss_opp=miss_opp, not_trend=not_trend, wrong_dir=wrong_dir))
    o = out[x]
    print(f"\nthreshold {'above 0 (Johnny)' if x == 0 else '+' + str(x)}: signal on {o['on']} days | trend day its way {o['right']} ({100*o['right']/o['on']:.0f}%) | trend day the other way {o['wrong_dir']} | not a trend day {o['not_trend']} | both {o['both']} | none {o['none']}")
    print(f"   of {o['trend']} trend days: caught {o['caught']} ({100*o['caught']/o['trend']:.0f}%) | missed: no signal {o['miss_none']}, both ways {o['miss_both']}, wrong way {o['miss_opp']}")
pickle.dump(dict(out=out, sig0={d: signal(best_by_day[d], 0) for d in days}, best=best_by_day, trend=trend, days=days), open("step2.pkl", "wb"))
