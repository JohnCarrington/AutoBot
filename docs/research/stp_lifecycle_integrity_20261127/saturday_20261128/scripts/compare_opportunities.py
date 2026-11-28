"""Production's journal vs the branch replay as lived vs the branch replay on IG's recovered candles, 25 Nov 09:15 to
27 Nov 18:30, matched by (creation time, direction, entry zone) since ids are numbered in order of issue."""
import sys, json
from pathlib import Path
fix, res = Path(sys.argv[1]), json.load(open(sys.argv[2]))
def opps(events, iss):
    out = {}
    for e in events:
        i = e.get("id")
        if not i: continue
        o = out.setdefault(i, {"id": i})
        if e["event"] == "created": o["created"] = e["time_utc"]
        if e["event"] in ("completed", "invalidated", "superseded"):
            o["end"] = (e["time_utc"][5:16], e["event"], e.get("destination_case") or (e.get("why") or "")[:60])
    return {(o["created"], *iss.get(o["id"], ["?", "?", "?"])): o for o in out.values() if o.get("created")}
ip = {}
for l in (fix / "migration" / "planner" / "issued.jsonl").read_text().splitlines():
    x = json.loads(l); ip[x["id"]] = [x["trade"], x["entry_zone"]["low"], x["entry_zone"]["high"]]
prod_ev = [e for e in json.loads((fix / "journal_opportunities.json").read_text()) if "2026-11-25T09:15" <= e["time_utc"] <= "2026-11-27T18:30:59"]
def iss_of(name): return {c[1]: list(c[2:5]) for c in res[name]["created"]}
P = opps(prod_ev, ip)
L = opps(res["lived_events"], iss_of("lived"))
Rv = opps(res["recovered_events"], iss_of("recovered"))
keys = sorted(set(P) | set(L) | set(Rv))
te = lambda o: (o or {}).get("end", (None, None))[:2] if o else None
both = [k for k in keys if k in P and k in L and k in Rv]
print("SUMMARY")
print(f"  production {len(P)}; branch as lived {len(L)}; branch recovered {len(Rv)}")
print("  not issued by the branch:", [(k[0][5:16], k[1], P[k]["id"][-8:]) for k in keys if k in P and k not in L and k not in Rv])
print("  issued by the branch only:", [k for k in keys if k not in P])
print("  end (time, event) differs production -> as lived:", [(k[0][5:16], k[1], P[k]["id"][-8:], te(P[k]), te(L[k])) for k in both if te(P[k]) != te(L[k])])
print("  end (time, event) differs as lived -> recovered:", [(k[0][5:16], k[1], P[k]["id"][-8:], te(L[k]), te(Rv[k])) for k in both if te(L[k]) != te(Rv[k])])
print("  destination case differs as lived -> recovered:", [(k[0][5:16], k[1], P[k]["id"][-8:], L[k]["end"][2], Rv[k]["end"][2]) for k in both if L[k].get("end") != Rv[k].get("end")])
print(f"  same end (time, event) in all three: {sum(1 for k in both if te(P[k]) == te(L[k]) == te(Rv[k]))} of {len(both)}")
print()
rows = []; same_pl = same_lr = 0
for k in keys:
    p, l, r = P.get(k), L.get(k), Rv.get(k)
    pe, le, re_ = (p or {}).get("end"), (l or {}).get("end"), (r or {}).get("end")
    same_pl += bool(p and l and pe[:2] == le[:2]) if (pe and le) else bool(p and l and pe == le)
    same_lr += bool(l and r and le == re_)
    if not (p and l and r and pe == le == re_):
        rows.append((k, (p or {}).get("id", "-")[-8:], pe if p else "NOT ISSUED", le if l else "NOT ISSUED", re_ if r else "NOT ISSUED"))
print(f"opportunities: production {len(P)}, branch as lived {len(L)}, branch recovered {len(Rv)}")
print(f"branch as lived vs branch recovered: identical lifecycle end for {same_lr} of {len(set(L)|set(Rv))}")
print("differences (creation, direction, zone | production id | production end | as lived end | recovered end):")
for k, pid, a, b, c in rows:
    print(f"  {k[0][5:16]} {k[1]} {k[2]}-{k[3]} | {pid} | {a} | {b} | {c}")
