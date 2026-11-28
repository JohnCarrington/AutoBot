import sys, gzip, json
sys.path.insert(0, "."); sys.path.insert(0, sys.argv[3])
from datetime import datetime
from prices.store import CandleStore
from computed_planner import reduced
fix = json.loads(gzip.decompress(open(sys.argv[1], "rb").read()))["plans"]
store = CandleStore(sys.argv[2], 10**6, warn=lambda m: None)
n = d = 0
for t, by in fix.items():
    for tr, want in by.items():
        n += 1
        got = reduced(store, datetime.fromisoformat(t.replace("Z", "+00:00")), tr)
        if json.dumps(got, sort_keys=True) != json.dumps(want, sort_keys=True):
            d += 1
            ks = [k for k in set(got) | set(want) if json.dumps(got.get(k), sort_keys=True) != json.dumps(want.get(k), sort_keys=True)]
            print("DIFF", t, tr, ks[:6])
print("plans", n, "differences", d)
