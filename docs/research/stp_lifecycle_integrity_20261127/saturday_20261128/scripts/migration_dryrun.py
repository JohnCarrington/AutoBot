"""Deterministic lineage migration dry run on COPIES (planner.migrate_lineage.build, the --as-of dry run's own code)."""
import sys, json, hashlib, tempfile
sys.path.insert(0, ".")
from pathlib import Path
from prices.store import CandleStore
from prices.model import parse_iso
from planner.migrate_lineage import build
from tests.stp import lifecycle_replay as R
state, store_path, as_of, out = Path(sys.argv[1]), sys.argv[2], sys.argv[3], Path(sys.argv[4])
s = R.settings(Path(tempfile.mkdtemp(prefix="mig-")))
texts = []
for _ in range(2):
    store = CandleStore(store_path, 10**6, warn=lambda m: None)
    m = build(s, store, state / "planner" / "GBPUSD", state / "orders" / "GBPUSD", state / "records" / "GBPUSD", parse_iso(as_of))
    texts.append(json.dumps(m, indent=1, sort_keys=True) + "\n")
out.write_text(texts[0])
print("deterministic (two builds identical):", texts[0] == texts[1], "sha256", hashlib.sha256(texts[0].encode()).hexdigest())
for L, rec in m["lineages"].items():
    if rec["aliases"] or rec["consumed"]:
        print(f"{L[-13:]} {rec['trade']}: consumed {rec['consumed']}; aliases {rec['aliases'] or '-'}; uncertain {rec['tests'].get('uncertain')}")
for L, rec in m["lineages"].items():
    for e in rec["evidence"]:
        print(f"  {e['reference'][:14]} key {e['key'][-13:]:>13} -> {e['lineage_key'][-13:]} alias {e['alias']}")
print("live:", m["opportunity_lineage"]); print("ambiguous:", m["ambiguous"] or "none")
print("uncertain hours (all lineages):", sorted({h for r in m["lineages"].values() for h in (r["tests"].get("uncertain") or [])}))
