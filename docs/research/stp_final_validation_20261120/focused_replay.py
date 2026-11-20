"""Focused replay: re-assess B and C (current branch code) at every stored decision where any variant had a plan or a
'no Major' refusal, and write them out for comparison with the stored 20 Nov evaluation rows. READ ONLY."""
import gzip
import json
import sys
from datetime import datetime
from pathlib import Path

from config.settings_loader import load_settings
from levels.current import build
from planner.measure import snapshot
from prices.store import CandleStore
from research.stp_structural_history.evaluate import summary, variant_plans
from tests.planner_helpers import Over, section

ROWS, OUT = sys.argv[1], sys.argv[2]
base = load_settings().for_pair("GBPUSD")
store = CandleStore(Path("/opt/autobot/data/research/stp_validation_store/GBPUSD"), base.candles.compress_after_days)
sA = Over(base, planner=section(base.planner, historical_daily_swing_lookback_weeks=0))
variants = {"B": (sA, False), "C": (base, False)}
rows = [json.loads(line) for line in gzip.open(ROWS, "rt")]
pick = [r["as_of_utc"] for r in rows if r.get("fresh") and any(
    r[k]["entry"] or (r[k]["no_rec"] or "").startswith("no Major") for k in "ABC")]
print("timestamps", len(pick), flush=True)
with open(OUT, "w") as f:
    for i, ts in enumerate(pick):
        t = datetime.fromisoformat(ts)
        snap = snapshot(base, store, t)
        ex = build(base, store, t)
        out = {}
        for k, p in variant_plans(variants, snap, ex).items():
            out[k] = summary(p) | {"obs": {x: p["observations"].get(x)
                                           for x in ("primary_distance_pips", "primary_distance_adr")}}
        f.write(json.dumps({"as_of_utc": ts, **out}, default=str) + "\n")
        f.flush()
        if i % 100 == 0:
            print(i, flush=True)
print("done")
