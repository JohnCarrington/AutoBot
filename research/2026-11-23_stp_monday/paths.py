"""Read-only: what GBPUSD did after each STP forecast on Mon 23 Nov 2026, on the bot's own IG 5-minute candles
(chart / sell price), until the 20:30 UK close. UK = UTC in November."""
import json, sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
sys.path.insert(0, "/opt/autobot")
from prices.store import CandleStore
from prices.model import parse_iso
UTC = timezone.utc
st = CandleStore("/opt/autobot/data/candles/GBPUSD", 999999)
END = parse_iso("2026-11-23T20:30:00Z")
c5 = st.read_range("5m", parse_iso("2026-11-23T00:00:00Z"), END)
h1 = st.read_range("1h", parse_iso("2026-11-23T00:00:00Z"), END)
F = "/opt/autobot/data/planner/GBPUSD/"
hm = lambda t: t.strftime("%H:%M")

def first(cands, test):
    for c in cands:
        if test(c): return c
    return None

def walk(trade, t0, lo, hi, stop, targets, stop_close=False):
    """Candles starting at or after t0 (finished after the forecast). Entry: first candle touching [lo, hi] (or price
    already in it). Then the first of the stop and each target, from the entry candle on."""
    after = [c for c in c5 if c.start >= t0]
    sell = trade == "SELL"
    e = first(after, lambda c: c.sell_low <= hi and c.sell_high >= lo)
    out = {"entry": None, "stop": None, "targets": {}}
    # before the entry: did a target come first?
    pre_end = e.start if e else END
    pre = [c for c in after if c.start < pre_end]
    for name, p in targets:
        if p is None: continue
        hit = first(pre, (lambda c, p=p: c.sell_low <= p) if sell else (lambda c, p=p: c.sell_high >= p))
        if hit: out.setdefault("target_before_entry", []).append(f"{name} {p} at {hm(hit.start)}")
    if not stop_close:
        sb = first(pre, (lambda c: c.sell_high >= stop) if sell else (lambda c: c.sell_low <= stop))
        if sb:
            out["stop_before_entry"] = hm(sb.start)
    if not e:
        hi_ = max(c.sell_high for c in after); lo_ = min(c.sell_low for c in after)
        out["no_entry"] = f"zone never reached (price {lo_}-{hi_} from {hm(t0)} to 20:30)"
        return out
    out["entry"] = hm(e.start)
    rest = [c for c in after if c.start >= e.start]
    if stop_close:
        hs = [c for c in h1 if c.start >= e.start.replace(minute=0) and c.end <= END]
        s = first(hs, (lambda c: c.sell_close >= stop) if sell else (lambda c: c.sell_close <= stop))
        out["stop"] = f"hourly close {s.sell_close} in the {hm(s.start)} hour (closes {hm(s.end)})" if s else None
        touch = first(rest, (lambda c: c.sell_high >= stop) if sell else (lambda c: c.sell_low <= stop))
        out["stop_touch"] = hm(touch.start) if touch else None
        s_t = s.end if s else None
    else:
        s = first(rest, (lambda c: c.sell_high >= stop) if sell else (lambda c: c.sell_low <= stop))
        out["stop"] = hm(s.start) if s else None
        s_t = s.start if s else None
    for name, p in targets:
        if p is None: continue
        t = first(rest, (lambda c, p=p: c.sell_low <= p) if sell else (lambda c, p=p: c.sell_high >= p))
        out["targets"][f"{name} {p}"] = hm(t.start) if t else None
    hit = [(v, k) for k, v in out["targets"].items() if v]
    if hit:
        v, k = min(hit)
        if s_t is None or v < hm(s_t) or (not stop_close and v == hm(s_t) and False):
            out["first"] = f"target {k} first ({v})"
        elif not stop_close and v == hm(s_t):
            out["first"] = f"stop and {k} in the same 5-minute candle ({v}): order unknown"
        else:
            out["first"] = f"stop first ({out['stop']})"
    else:
        out["first"] = f"stop ({out['stop']})" if out["stop"] else "neither by 20:30"
    return out

print("PLANNER")
for l in open(F + "issued.jsonl"):
    r = json.loads(l)
    if not r["id"].startswith("STP-GBPUSD-20261123"): continue
    d, inv = r["destinations"], r["invalidation"]
    t0 = parse_iso(r["created_utc"]).replace(second=0)
    t0 = t0 - timedelta(minutes=t0.minute % 5)               # the candle in progress at creation counts
    tg = [("T1", D(d["intermediate"]["price"]) if d.get("intermediate") else None),
          ("primary", D(d["primary"]["price"])), ("extended", D(d["extended"]["price"]) if d.get("extended") else None)]
    o = walk(r["trade"], t0, D(r["entry_zone"]["low"]), D(r["entry_zone"]["high"]), D(inv["zone_break_close"]), tg, True)
    print(r["id"], r["created_utc"][11:16], json.dumps(o))
print("\nTECHNICAL")
for l in open(F + "technical.jsonl"):
    r = json.loads(l)
    if not ("2026-11-23T00" <= r["as_of_utc"] < "2026-11-23T18:01"): continue
    o = r.get("opportunity")
    if not o:
        print(r["as_of_utc"][11:16], "no opportunity"); continue
    t0 = parse_iso(r["as_of_utc"]).replace(second=0, microsecond=0)
    t0 = t0 - timedelta(minutes=t0.minute % 5)
    tg = [("T1", D(o["intermediate_target"]["price"]) if o.get("intermediate_target") else None),
          ("T2", D(o["extended_target"]["price"]) if o.get("extended_target") else None)]
    res = walk(o["trade"], t0, D(o["entry_zone"]["low"]), D(o["entry_zone"]["high"]), D(o["stop"]["price"]), tg)
    print(r["as_of_utc"][11:16], o["type"], o["trade"], json.dumps(res))
print("\nPIA 09:11 BUY 13081 stop 13029 target 13222")
res = walk("BUY", parse_iso("2026-11-23T09:10:00Z"), D("13081"), D("13081"), D("13029"), [("target", D("13222"))])
print(json.dumps(res))
day = [c for c in c5]
lo = min(day, key=lambda c: c.sell_low); hi = max(day, key=lambda c: c.sell_high)
print("day 00:00-20:30: high", hi.sell_high, hm(hi.start), "low", lo.sell_low, hm(lo.start), "| 20:25 close", day[-1].sell_close, hm(day[-1].start))
for t in ("09:10","12:00","13:00","14:00","15:00","16:00","17:00","18:00"):
    c = next(c for c in c5 if hm(c.start) == t); print("  ", t, "open", c.sell_open)
