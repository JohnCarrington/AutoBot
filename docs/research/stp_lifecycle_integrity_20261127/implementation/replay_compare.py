"""Compares a replay_run.py output with production's journal by (creation time, direction, zone): lifecycles that differ,
publications withheld or added. New record-only events (lineage, trade executed, classification corrected, data gap)
are left out of the comparison."""
import sys, json
from pathlib import Path
sys.path.insert(0, '.')
from tests.stp.lifecycle_replay import FIX
def opps(events):
    out = {}
    for e in events:
        i = e.get("id")
        if not i: continue
        o = out.setdefault(i, {"id": i, "events": []})
        o["events"].append((e["time_utc"], e["event"]))
        if e["event"] == "created": o["created"] = e["time_utc"]
        if e["event"] in ("completed","invalidated","superseded"): o["end"] = (e["time_utc"], e["event"], (e.get("why") or "")[:70])
        if e["event"] == "lineage": o["lineage"] = e.get("lineage")
    return out
R = json.load(open(sys.argv[1])); a = R["events"]; ia = R["issued"]
ip = {}
for l in (FIX / "migration" / "planner" / "issued.jsonl").read_text().splitlines():
    x = json.loads(l); ip[x["id"]] = [x["trade"], x["entry_zone"]["low"], x["entry_zone"]["high"]]
prod = [e for e in json.loads((FIX / "journal_opportunities.json").read_text()) if "2026-11-25T09:15" <= e["time_utc"] <= "2026-11-27T14:13"]
A, P = opps(a), opps(prod)
def keyed(D, iss):
    return {(o["created"], *iss.get(o["id"], ["?", "?", "?"])): o for o in D.values() if o.get("created")}
pa, pp = keyed(A, ia), keyed(P, ip)
for k in sorted(set(pa) | set(pp)):
    x, y = pa.get(k), pp.get(k)
    if x and y:
        ex = [ev for ev in x["events"] if ev[1] not in ("lineage", "trade executed", "classification corrected", "data gap", "data gap reconciled")]
        if ex != y["events"]:
            print("CHANGED", k[1], k[2], k[3], y["id"][-8:], "->", x["id"][-8:], "| prod end", y.get("end"), "| new end", x.get("end"))
    elif y:
        print("NOT ISSUED (new code)", k[1], k[2], k[3], y["id"][-8:], y.get("end"))
    else:
        print("ONLY NEW", k[1], k[2], k[3], x["id"][-8:], x.get("end"))
print("same lifecycle (ids aside):", sum(1 for k in pa if k in pp and [e for e in pa[k]["events"] if e[1] not in ("lineage", "trade executed", "classification corrected", "data gap", "data gap reconciled")] == pp[k]["events"]), "of", len(pp))
