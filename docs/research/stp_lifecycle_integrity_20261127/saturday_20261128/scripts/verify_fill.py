"""Compare the pre-fill copy of the candle store with the post-fill store, row by row."""
import csv, sys, json, re
from pathlib import Path
from datetime import datetime, timezone
pre, post = Path(sys.argv[1]), Path(sys.argv[2])
EXPECTED_5M = ["2026-11-16T22:55:00Z","2026-11-16T23:00:00Z","2026-11-19T18:35:00Z","2026-11-20T11:20:00Z",
               "2026-11-27T12:00:00Z","2026-11-27T12:05:00Z","2026-11-27T12:10:00Z"]
NOT_SUPPLIED = ["2026-11-22T21:05:00Z","2026-11-22T21:25:00Z","2026-11-22T21:45:00Z","2026-11-22T21:50:00Z"]
def rows(p):
    if not p.exists(): return {}
    with open(p) as f:
        return {r["start_utc"]: r for r in csv.DictReader(f)}
out = {"added": {}, "changed": {}, "removed": {}, "files_only_pre": [], "files_new": []}
for tf in ["5m","1h","4h","1d","1w"]:
    names = sorted({x.name for x in (pre/tf).glob("*.csv")} | {x.name for x in (post/tf).glob("*.csv")})
    for n in names:
        a, b = rows(pre/tf/n), rows(post/tf/n)
        if not (pre/tf/n).exists(): out["files_new"].append(f"{tf}/{n}")
        if not (post/tf/n).exists(): out["files_only_pre"].append(f"{tf}/{n}")
        for k in b.keys()-a.keys(): out["added"].setdefault(tf, []).append(k)
        for k in a.keys()-b.keys(): out["removed"].setdefault(tf, []).append(k)
        for k in a.keys() & b.keys():
            if a[k] != b[k]:
                diff = {c: (a[k][c], b[k][c]) for c in a[k] if a[k][c] != b[k][c]}
                out["changed"].setdefault(tf, []).append({"start": k, "diff": diff})
for d in out["added"].values(): d.sort()
# 5m checks
add5 = out["added"].get("5m", [])
ok = True
print("5m added:", add5)
print("  == expected 7 timestamps:", add5 == sorted(EXPECTED_5M)); ok &= add5 == sorted(EXPECTED_5M)
print("  5m changed rows:", len(out["changed"].get("5m", [])), " removed:", len(out["removed"].get("5m", [])))
ok &= not out["changed"].get("5m") and not out["removed"].get("5m")
for tf in ["1h","4h","1d","1w"]:
    print(tf, "added:", out["added"].get(tf, []), "removed:", out["removed"].get(tf, []))
    for c in out["changed"].get(tf, []): print("   changed", c["start"], c["diff"])
    ok &= not out["removed"].get(tf)
print("files new:", out["files_new"], " files gone:", out["files_only_pre"]); ok &= not out["files_only_pre"]
# every recovered 5m candle: on boundary, files in order, no duplicates, parts 1/1
for day in sorted({t[:10] for t in EXPECTED_5M}):
    p = post/"5m"/f"{day}.csv"; ts = [r["start_utc"] for r in csv.DictReader(open(p))]
    srt = ts == sorted(ts); dup = len(ts) != len(set(ts))
    bnd = all(datetime.fromisoformat(t.replace("Z","+00:00")).minute % 5 == 0 and t.endswith(":00Z") for t in ts)
    print(f"5m/{day}: rows {len(ts)} ordered {srt} duplicates {dup} on-5m-boundary {bnd}"); ok &= srt and not dup and bnd
for t in EXPECTED_5M:
    r = rows(post/"5m"/f"{t[:10]}.csv")[t]
    print("  recovered", t, "->", r["end_utc"], "buy", r["buy_open"], r["buy_high"], r["buy_low"], r["buy_close"],
          "sell", r["sell_open"], r["sell_high"], r["sell_low"], r["sell_close"], "parts", r["parts"], r["expected_parts"])
for t in NOT_SUPPLIED:
    print("  not supplied", t, "in store:", t in rows(post/"5m"/f"{t[:10]}.csv"))
    ok &= t not in rows(post/"5m"/f"{t[:10]}.csv")
json.dump(out, open(sys.argv[3], "w"), indent=1)
print("ALL CHECKS PASS" if ok else "CHECK FAILED")
