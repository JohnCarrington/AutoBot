"""Saturday 28 Nov: the extended production replay (25 Nov 09:15 to 27 Nov 18:30) on the as-lived and the recovered
candles. Offline: temporary folders only, IG never contacted, no production file read or written except the fixtures.
Run from the tree under test:  python saturday_replay.py <as-lived fixture dir> <recovered fixture dir> <out.json>"""
import sys, json, tempfile, hashlib
sys.path.insert(0, ".")
from pathlib import Path
from datetime import datetime, timezone
UTC = timezone.utc
from tests.stp import lifecycle_replay as R
from prices.store import CandleStore
from planner.opportunities import OpportunityKeeper
LIVED, RECOV, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
PRE_STORE, POST_STORE = Path(sys.argv[4]), Path(sys.argv[5])     # full store copies, for STP's plans
sys.path.insert(0, str(Path(__file__).resolve().parent))
import computed_planner
RECORDED = R.RecordedPlanner
PLAN_LOG = {}
END = datetime(2026, 11, 27, 18, 30, tzinfo=UTC)
DOWN = (datetime(2026, 11, 27, 12, 1, 58, tzinfo=UTC), datetime(2026, 11, 27, 12, 20, tzinfo=UTC))

def run(fix, plans=None, tag=None):
    """plans=None: production's recorded plans; else STP's plan computed on that store copy at each re-plan."""
    R.RecordedPlanner = RECORDED if plans is None else computed_planner.make(plans, PLAN_LOG.setdefault(tag, []))
    old = R.use_fixtures(fix)
    try:
        tmp = Path(tempfile.mkdtemp(prefix="satreplay-"))
        s = R.settings(tmp)
        r = R.replay(s, END, down=DOWN)
        return s, tmp, r
    finally:
        R.use_fixtures(old)

def summary(r, folder):
    st = json.loads((folder / "planner" / "GBPUSD" / "current.json").read_text())
    lin = {k: {"consumed": v.get("consumed"), "aliases": v.get("aliases"),
               "uncertain": (v.get("tests") or {}).get("uncertain")} for k, v in (st.get("lineages") or {}).items()}
    created = [(e["time_utc"], e["id"], *r["issued"].get(e["id"], ("?", "?", "?"))) for e in r["events"] if e["event"] == "created"]
    ends = {e["id"]: (e["time_utc"], e["event"], e.get("destination_case"), (e.get("why") or "")[:110])
            for e in r["events"] if e["event"] in ("completed", "invalidated", "superseded")}
    outc = [{k: o.get(k) for k in ("reference", "idea_time", "stp_allowed", "opened", "key", "lineage", "test", "opportunity", "reasons", "rule_11")} for o in r["outcomes"]]
    return {"outcomes": outc, "created": created, "ends": ends, "lineages": lin,
            "event_counts": {k: sum(1 for e in r["events"] if e["event"] == k) for k in sorted({e["event"] for e in r["events"]})},
            "events_sha256": hashlib.sha256(json.dumps(r["events"], sort_keys=True).encode()).hexdigest()}

res = {}
s, tmp, r = run(LIVED);  res["lived"] = summary(r, tmp)
# Saturday: the same as-lived state meets the recovered store once (as the deployed tracker would on its first run).
n0 = len(r["events"])
old = R.use_fixtures(RECOV)
try:
    store = R.fixture_store()
finally:
    R.use_fixtures(old)
t = datetime(2026, 11, 27, 18, 30, 3, tzinfo=UTC); store.t = t
OpportunityKeeper(s, store, planner=R.RecordedPlanner()).run(t)
ev = [json.loads(x) for x in (tmp / "planner" / "GBPUSD" / "recommendations.jsonl").read_text().splitlines()]
st = json.loads((tmp / "planner" / "GBPUSD" / "current.json").read_text())
res["lived_then_reconciled"] = {
    "new_events": [{k: e.get(k) for k in ("time_utc", "event", "id", "lineage", "hour_utc", "destination_case", "why")} for e in ev[n0:]],
    "lineages": {k: {"consumed": v.get("consumed"), "aliases": v.get("aliases"), "uncertain": (v.get("tests") or {}).get("uncertain")}
                 for k, v in (st.get("lineages") or {}).items()}}
R.RecordedPlanner = RECORDED
s5, tmp5, r5 = run(LIVED, PRE_STORE, "control"); res["control_computed_plans_on_pre_equal_recorded"] = summary(r5, tmp5)["events_sha256"] == res["lived"]["events_sha256"]
s2, tmp2, r2 = run(RECOV, POST_STORE, "recovered"); res["recovered"] = summary(r2, tmp2)
res["recovered_replan_times"] = sorted({k for k, _ in PLAN_LOG["recovered"]})
res["recovered_replans_not_in_production"] = sorted({k for k, _ in PLAN_LOG["recovered"]} - set(json.loads(__import__("gzip").decompress((LIVED / "plans.json.gz").read_bytes()))["plans"].keys()))
s3, tmp3, r3 = run(RECOV, POST_STORE, "recovered2"); res["recovered_repeat_sha256_equal"] = summary(r3, tmp3)["events_sha256"] == res["recovered"]["events_sha256"]
s4, tmp4, r4 = run(LIVED); res["lived_repeat_sha256_equal"] = summary(r4, tmp4)["events_sha256"] == res["lived"]["events_sha256"]
res["lived_events"], res["recovered_events"], res["control_events"] = r["events"][:n0], r2["events"], r5["events"]
OUT.write_text(json.dumps(res, indent=1, default=str))
for name in ("lived", "recovered"):
    print("=====", name, "events sha256", res[name]["events_sha256"][:16], res[name]["event_counts"])
    for o in res[name]["outcomes"]:
        print(f'  {o["reference"][:14]} {o["idea_time"][5:16]} STP {o["stp_allowed"]!s:5} opened {o["opened"]!s:5} key {o["key"]} lineage {o["lineage"]} test {o["test"]} | {(o.get("rule_11") or o["reasons"] or [""])[0][:110]}')
print("===== lived then reconciled (Saturday run):")
for e in res["lived_then_reconciled"]["new_events"]: print("  ", e)
print("control (computed plans on pre-fill store == recorded plans):", res["control_computed_plans_on_pre_equal_recorded"])
print("re-plans the recovered run made that production did not record:", res["recovered_replans_not_in_production"])
print("deterministic: lived", res["lived_repeat_sha256_equal"], "recovered", res["recovered_repeat_sha256_equal"])
