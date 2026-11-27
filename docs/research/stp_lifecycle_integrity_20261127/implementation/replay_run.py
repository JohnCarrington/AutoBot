"""Runs the lifecycle replay (tests/stp/lifecycle_replay.py) from 25 Nov 09:15 to 27 Nov 14:10 and compares it with
production's journal by opportunity id; writes the outcomes, events and issued records to argv[1]. Run from the tree under test."""
import sys, json, tempfile
from pathlib import Path
sys.path.insert(0, '.')
from datetime import datetime, timezone
from tests.stp.lifecycle_replay import replay, settings, lifecycle, FIX
end = datetime(2026, 11, 27, 14, 10, tzinfo=timezone.utc)
tmp = Path(tempfile.mkdtemp())
r = replay(settings(tmp), end)
got = lifecycle(r["events"])
prod = {}
for e in json.loads((FIX / "journal_opportunities.json").read_text()):
    if e["time_utc"] >= "2026-11-25T09:15:00Z" and e["time_utc"] <= "2026-11-27T14:13:00Z":
        prod.setdefault(e["id"], []).append((e["time_utc"], e["event"]))
ids = sorted(set(got) | set(prod))
diff = 0
for i in ids:
    a, b = got.get(i, []), prod.get(i, [])
    if a != b:
        diff += 1
        print("DIFF", i[-13:], "\n   replay:", a, "\n   prod:  ", b)
print("opportunities", len(ids), "differing", diff)
for o in r["outcomes"]:
    print(o["reference"], o["idea_time"][5:16], "STP", o["stp_allowed"], o["key"], "opened", o["opened"], (o.get("rule_11") or o["reasons"] or [""])[0][:90])
iss = {}
for l in (tmp / "planner" / "GBPUSD" / "issued.jsonl").read_text().splitlines():
    x = json.loads(l); iss[x["id"]] = [x["trade"], x["entry_zone"]["low"], x["entry_zone"]["high"]]
json.dump({"outcomes": r["outcomes"], "lifecycle": got, "events": r["events"], "issued": iss}, open(sys.argv[1], "w"), indent=1)
