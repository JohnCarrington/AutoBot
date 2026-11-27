"""Saturday maintenance: offline lifecycle reconciliation on IG's recovered candles (Phase 2, PD-5 C). Offline and read
only on production; run AFTER the approved recovery (prices.history_fill gap-go) and its checks:

    .venv/bin/python docs/research/stp_lifecycle_integrity_20261127/implementation/saturday_offline_reconciliation.py \
        <pre-fill candle store copy: .../candles/GBPUSD> <post-fill candle store copy: .../candles/GBPUSD> <out folder>

It never reads or writes /opt/autobot/data directly: give it COPIES. It never contacts IG, never places or records an
order, and changes no production record. What it shows is what the Phase 2 tracker would conclude once deployed.

  1. From STP-GBPUSD-20261127-1200-57 exactly as production published it at 12:00:03 on 27 Nov (the opportunity live
     across the outage; tests/stp/fixtures/lifecycle_20261127/state_20261127_1200.json), with its lineage from the
     historical map, the Phase 2 tracker runs on the PRE-fill store as production saw it (the price service stopped
     12:01:58 to 12:20): the gap 12:00-12:15 is recorded on 1200-57, which then ends at its destination (12:15).
  2. The SAME state then meets the POST-fill store (IG's own 12:00, 12:05, 12:10 candles): one tracker run reconciles
     it. If IG's candles show the zone reached after creation and before the destination, the ending's classification
     is corrected to "after_zone" in a new event (it is not reopened); otherwise the classification stands.
  3. The reconciliation events, the gaps and every lineage's consumed tests and alias keys are written to <out>.
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

UTC = timezone.utc
PRE, POST, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])


def main() -> int:
    from planner.migrate_lineage import build
    from planner.opportunities import OpportunityKeeper
    from prices.store import CandleStore
    from tests.stp import lifecycle_replay as R
    OUT.mkdir(parents=True, exist_ok=True)
    s = R.settings(OUT / "run")
    pre = R.AvailStore(CandleStore(PRE, 10**6, warn=lambda m: None))
    post = R.AvailStore(CandleStore(POST, 10**6, warn=lambda m: None))
    pre.t = datetime(2026, 11, 27, 12, 0, 3, tzinfo=UTC)
    m = build(s, pre, R.FIX / "migration" / "planner", R.FIX / "migration", R.FIX / "migration", pre.t)
    d = Path(s.planner.folder) / "GBPUSD"
    d.mkdir(parents=True, exist_ok=True)
    (d / "lineage_map.json").write_text(json.dumps(m))
    st = json.loads((R.FIX / "state_20261127_1200.json").read_text())
    out = R.replay(s, datetime(2026, 11, 27, 12, 20, tzinfo=UTC), store=pre, ideas=[],
                   start=datetime(2026, 11, 27, 12, 0, tzinfo=UTC), initial=st,
                   down=(datetime(2026, 11, 27, 12, 1, 58, tzinfo=UTC), datetime(2026, 11, 27, 12, 20, tzinfo=UTC)))
    before = json.loads((d / "current.json").read_text())
    t = datetime(2026, 11, 27, 12, 25, 3, tzinfo=UTC)
    post.t = t
    OpportunityKeeper(s, post, planner=R.RecordedPlanner()).run(t)
    after = json.loads((d / "current.json").read_text())
    events = [json.loads(x) for x in (d / "recommendations.jsonl").read_text().splitlines()]
    pick = [e for e in events if e["event"] in ("data gap", "data gap reconciled", "data gap review",
                                                "classification corrected", "invalidated", "completed")
            and e.get("id", "").startswith("STP-GBPUSD-20261127-1200")]
    m57 = lambda st_: next((x for L in st_.get("lineages", {}).values() for x in L.get("members", [])   # noqa: E731
                            if x["id"] == "STP-GBPUSD-20261127-1200-57"), None)
    report = {"events": pick, "member_before": m57(before), "member_after": m57(after),
              "lineage_0300_56": {k: (after.get("lineages", {}).get("STP-GBPUSD-20261127-0300-56") or {}).get(k)
                                  for k in ("consumed", "aliases", "tests")},
              "recovered_candles": [c.__dict__ | {"start": c.start.isoformat(), "end": c.end.isoformat()}
                                    for c in post.base.read_range("5m", datetime(2026, 11, 27, 12, 0, tzinfo=UTC),
                                                                  datetime(2026, 11, 27, 12, 15, tzinfo=UTC))]}
    (OUT / "offline_reconciliation.json").write_text(json.dumps(report, indent=1, default=str))
    for e in pick:
        print(e["time_utc"], e["event"], e.get("destination_case", ""), (e.get("why") or "")[:160])
    print("1200-57 classification:", (report["member_before"] or {}).get("destination_case"), "->",
          (report["member_after"] or {}).get("destination_case"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
