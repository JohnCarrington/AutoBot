"""Offline: STP's approved assess() applied per direction (OD-06/OD-16/OD-17), H4 direction and condition as context only.
Read-only on the candle store. Prints one line per hour per direction."""
import json, sys
from datetime import datetime, timedelta, UTC
import planner.assess as A
from config.settings_loader import load_settings
from prices.store import CandleStore

s = load_settings().for_pair("GBPUSD")
store = CandleStore(s.candles.folder, s.candles.compress_after_days)
orig_dir, orig_cond = A.direction, A.condition
ctx = {}
def make(forced):
    def d(settings, st):
        real, ev = orig_dir(settings, st); ctx["h4"] = real
        return forced, ev
    def c(settings, snap, st, d1, h1):
        cond, ev, facts = orig_cond(settings, snap, st, d1, h1); ctx["cond"] = cond
        if cond not in A.OPPORTUNITY_CLASSES:
            cond = A.CONTINUATION if False else cond
            return A.CORRECTION_ACTIVE, ev + [f"(context only) real condition {cond}"], {k: v for k, v in facts.items() if k != "unclassified"}
        return cond, ev, facts
    return d, c
out = []
start = datetime(2026, 11, 24, 0, 0, 2, tzinfo=UTC)
for h in range(0, 21):
    t = start + timedelta(hours=h)
    for forced, trade in ((A.BEARISH, "SELL"), (A.BULLISH, "BUY")):
        A.direction, A.condition = make(forced)
        try:
            p = A.plan_at(s, store, t).as_dict()
        finally:
            A.direction, A.condition = orig_dir, orig_cond
        z = p.get("entry_zone")
        rec = {"as_of": t.isoformat()[:16], "trade": trade, "h4_real": ctx.get("h4"), "condition_real": ctx.get("cond"),
               "zone": None if not z else {k: z[k] for k in ("low", "high", "class", "levels")},
               "reachability": p.get("reachability"),
               "destinations": None if not z else {k: (v or {}).get("price") for k, v in p["destinations"].items()},
               "invalidation": None if not z else {k: p["invalidation"][k] for k in ("zone_break_close", "structure_break_close", "destination_first_applies")},
               "no_recommendation": p.get("no_recommendation")}
        out.append(rec)
        zz = rec["zone"]
        print(rec["as_of"], trade, "H4", rec["h4_real"], rec["condition_real"], "|",
              f"{zz['low']}-{zz['high']} {zz['class']} {rec['reachability']} dest {rec['destinations']} inv {rec['invalidation']['zone_break_close']}/{rec['invalidation']['structure_break_close']}" if zz else "NONE: " + (rec["no_recommendation"] or "")[:150])
json.dump(out, open(sys.argv[1], "w"), indent=1)
