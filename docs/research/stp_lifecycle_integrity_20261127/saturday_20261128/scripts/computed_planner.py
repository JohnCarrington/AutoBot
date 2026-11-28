"""STP's own plan (planner.assess.plan_at, unchanged production code) computed on a given candle-store copy, reduced to
the fields the replay's tracker reads exactly as make_fixtures.py reduces them."""
import json
from datetime import datetime
from prices.store import CandleStore
from planner.assess import plan_at
KEEP = ("trade", "dominant_direction", "condition", "opportunity", "expected_movement", "entry_zone", "reference_entry",
        "reachability", "selection_reason", "destinations", "invalidation", "observations", "direction_evidence",
        "condition_evidence", "alternative", "market_data_utc", "no_recommendation", "destination_reached",
        "relation_to_h4", "condition_unclassified", "fresh", "as_of_utc", "threshold_misses", "warming_up",
        "h4_last_swing")
_S = None
def reduced(store, t, trade):
    global _S
    if _S is None:
        import tempfile
        from pathlib import Path
        from tests.stp import lifecycle_replay as R
        _S = R.settings(Path(tempfile.mkdtemp(prefix="plan-settings-")))
    p = plan_at(_S, store, t, None, trade=trade).as_dict()
    keep = {k: p.get(k) for k in KEEP}
    keep["structure"] = {"levels": [{"name": m.get("name"), "price": m.get("price")}
                                    for m in ((p.get("structure") or {}).get("levels") or [])]}
    return json.loads(json.dumps(keep, default=str))
def make(store_path, log):
    store = CandleStore(store_path, 10**6, warn=lambda m: None)
    class ComputedPlanner:
        def __init__(self):
            from tests.stp import lifecycle_replay as R
            self.p = R.plans()          # production's recorded analysis times: the replay runs the tracker at them
        def __call__(self, settings, st, now, *a, trade=None):
            from tests.technical.test_planner import FakePlan
            k = now.strftime("%Y-%m-%dT%H:%M:%SZ")
            log.append((k, trade))
            return FakePlan(reduced(store, now, trade))
    return ComputedPlanner
