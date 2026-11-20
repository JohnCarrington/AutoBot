"""Compare the focused replay (current code) with the stored 20 Nov evaluation rows, variant by variant."""
import gzip
import json
import sys
from collections import Counter

stored = {r["as_of_utc"]: r for r in map(json.loads, gzip.open(sys.argv[1], "rt")) if r.get("fresh")}
new = {r["as_of_utc"]: r for r in map(json.loads, open(sys.argv[2]))}
OLD_TAIL = lambda s: (s or "").replace(" within the 150-pip window for the primary destination",  # noqa: E731
                                       " for the primary destination")
KEYS = ("direction", "condition", "trade", "entry", "primary", "zone_break", "structure_break")
diff, msg_changed, dist = Counter(), Counter(), []
for ts, n in new.items():
    s = stored[ts]
    for v in "BC":
        a, b = s[v], n[v]
        for k in KEYS:
            if a[k] != b[k]:
                diff[(v, k)] += 1
                print("DIFF", ts, v, k, a[k], b[k])
        if OLD_TAIL(a["no_rec"]) != (b["no_rec"] or ""):
            diff[(v, "no_rec")] += 1
            print("DIFF", ts, v, "no_rec", a["no_rec"], "|", b["no_rec"])
        elif a["no_rec"] != b["no_rec"]:
            msg_changed[v] += 1
        if b["entry"] and b["primary"]:
            dist.append((v, float(b["obs"]["primary_distance_pips"]), float(b["obs"]["primary_distance_adr"])))
print("timestamps compared", len(new), "of", sum(1 for r in stored.values()))
print("decision differences", dict(diff) or "none")
print("reason text changed only by the 150-pip wording", dict(msg_changed))
for v in "BC":
    d = sorted(x[1] for x in dist if x[0] == v)
    a = sorted(x[2] for x in dist if x[0] == v)
    q = lambda xs, p: xs[int(p * (len(xs) - 1))]  # noqa: E731
    print(v, "plans", len(d), "primary distance pips median", q(d, .5), "p90", q(d, .9), "max", d[-1],
          "| ADR median", q(a, .5), "p90", q(a, .9), "max", a[-1], "| >150 pips", sum(x > 150 for x in d))
