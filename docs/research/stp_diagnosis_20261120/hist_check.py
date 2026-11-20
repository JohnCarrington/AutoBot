"""Can the production planner (worktree copy) produce assessments at historical timestamps? READ ONLY.
Daily 12:00 UTC on weekdays, Jun 2024 - Apr 2026, on the existing historical store. Leak check: 12 timestamps re-run on a
store clipped at the timestamp must give the identical plan."""
import collections, json, random, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config.settings_loader import load_settings
from prices.store import CandleStore
from planner.assess import plan_at

STORE = Path("/home/autobot/stp-research/historical/GBPUSD")
OUT = Path(sys.argv[1])
s = load_settings().for_pair("GBPUSD")
store = CandleStore(STORE, s.candles.compress_after_days)


class Clipped:
    def __init__(self, base, t):
        self.b, self.t = base, t

    def __getattr__(self, n):
        return getattr(self.b, n)

    def read_range(self, tf, start, end):
        return [c for c in self.b.read_range(tf, start, min(end, self.t)) if c.end <= self.t]


def category(p):
    if not p.get("fresh"):
        return "data not fresh (reported)"
    n = p.get("no_recommendation") or ""
    if p.get("entry_zone"):
        return "PLAN"
    for pat, lab in (("NEUTRAL", "direction NEUTRAL"), ("TRANSITIONAL", "direction TRANSITIONAL"), ("already reached", "D-1"),
                     ("INDETERMINATE", "condition INDETERMINATE"), ("REVERSAL_RISK", "condition REVERSAL_RISK"),
                     ("no Major", "no Major destination"), ("defensible", "no defensible entry zone")):
        if pat in n:
            return lab
    return "other: " + n[:80]


times, t = [], datetime(2024, 6, 3, 12, tzinfo=timezone.utc)
while t < datetime(2026, 4, 10, tzinfo=timezone.utc):
    if t.weekday() < 5:
        times.append(t)
    t += timedelta(days=1)
rows, errors = [], 0
for t in times:
    try:
        p = plan_at(s, store, t, calendar=[]).as_dict()
        rows.append({"t": t.isoformat(), "cat": category(p), "dir": p.get("dominant_direction"), "cond": p.get("condition"),
                     "reason": p.get("no_recommendation"), "zones": len((p.get("structure") or {}).get("zones") or []),
                     "data_utc": p.get("market_data_utc")})
    except Exception as e:                                # noqa: BLE001
        errors += 1
        rows.append({"t": t.isoformat(), "cat": f"EXCEPTION {type(e).__name__}: {e}"})
random.seed(20261120)
leak = []
for t in random.sample([r for r in times], 12):
    a = plan_at(s, store, t, calendar=[]).as_dict()
    b = plan_at(s, Clipped(store, t), t, calendar=[]).as_dict()
    leak.append({"t": t.isoformat(), "identical": json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str)})
c = collections.Counter(r["cat"] for r in rows)
summary = {"n": len(rows), "errors": errors, "categories": c.most_common(),
           "with_direction": sum(1 for r in rows if r.get("dir") in ("BEARISH", "BULLISH")),
           "with_structure_zones": sum(1 for r in rows if r.get("zones")),
           "leak_check": leak}
OUT.write_text(json.dumps({"summary": summary, "rows": rows}, indent=1))
print(json.dumps(summary, indent=1))
