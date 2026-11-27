"""Builds the frozen fixtures for the Phase 2 lifecycle tests (owner, 27 November 2026). Run once, offline, on a COPY
of the production files (never /opt/autobot/data itself):

    .venv/bin/python tests/stp/fixtures/lifecycle_20261127/make_fixtures.py <snapshot>

<snapshot> holds candles/GBPUSD (the candle store), planner/ (recommendations.jsonl), trades.jsonl and orders.jsonl, as
copied from production at 14:15 UTC on 27 November 2026 (before the OP-1 gap fill: the 27 Nov 12:00-12:10 5-minute
candles are missing, exactly as production saw them).

Writes, next to this file:
  candles/GBPUSD/{5m,1h,4h}/<day>.csv   the stored candles from 20 to 27 November (and gaps.csv), byte for byte
  plans.json                             STP's own plan (planner.assess.plan_at, unchanged code) for each direction at
                                         every hourly analysis time the production journal records from 24 Nov 23:00,
                                         reduced to the fields the tracker reads; each checked against the journal's
                                         own analysis summary (zone, primary, no-recommendation reason)
  stp_trades.json                        the STP-authorised trades: reference, strategy, direction, idea and open time,
                                         entry price, rejection candle and the key and opportunity production recorded
                                         (from the trades' own entry steps and the order journal; no financial figure)
  journal_opportunities.json             each opportunity's production events (id, time, event, why), for comparison
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/opt/autobot")

from config.settings_loader import load_or_exit          # noqa: E402
from planner.assess import plan_at                       # noqa: E402
from prices.store import CandleStore                     # noqa: E402

HERE = Path(__file__).resolve().parent
SNAP = Path(sys.argv[1])
DAYS = [f"2026-11-{d:02d}" for d in range(20, 28)]
KEEP = ("trade", "dominant_direction", "condition", "opportunity", "expected_movement", "entry_zone", "reference_entry",
        "reachability", "selection_reason", "destinations", "invalidation", "observations", "direction_evidence",
        "condition_evidence", "alternative", "market_data_utc", "no_recommendation", "destination_reached",
        "relation_to_h4", "condition_unclassified", "fresh", "as_of_utc", "threshold_misses", "warming_up",
        "h4_last_swing")

# 1. candles
src = SNAP / "candles" / "GBPUSD"
dst = HERE / "candles" / "GBPUSD"
for tf in ("5m", "1h", "4h"):
    (dst / tf).mkdir(parents=True, exist_ok=True)
    for d in DAYS:
        f = src / tf / f"{d}.csv"
        if f.exists():
            shutil.copyfile(f, dst / tf / f.name)
shutil.copyfile(src / "gaps.csv", dst / "gaps.csv")

# 2. plans at every recorded analysis time
s = load_or_exit().for_pair("GBPUSD")
store = CandleStore(src, 10**6, warn=lambda m: None)
events = [json.loads(x) for x in (SNAP / "planner" / "recommendations.jsonl").read_text().splitlines() if x.strip()]
analyses = [e for e in events if e["event"] == "analysis" and e["time_utc"] >= "2026-11-24T23:00:00Z"]
plans, mismatches = {}, []
for e in analyses:
    t, tr = e["time_utc"], e["plan"].get("trade")
    if tr is None:
        continue
    p = plan_at(s, store, datetime.fromisoformat(t.replace("Z", "+00:00")), None, trade=tr).as_dict()
    keep = {k: p.get(k) for k in KEEP}
    keep["structure"] = {"levels": [{"name": m.get("name"), "price": m.get("price")}
                                    for m in ((p.get("structure") or {}).get("levels") or [])]}
    plans.setdefault(t, {})[tr] = keep
    rec, z = e["plan"], p.get("entry_zone") or {}
    got = (z.get("low"), z.get("high"), ((p.get("destinations") or {}).get("primary") or {}).get("price"),
           bool(p.get("no_recommendation")))
    want = ((rec.get("zone") or {}).get("low"), (rec.get("zone") or {}).get("high"), rec.get("primary"),
            bool(rec.get("no_recommendation")))
    if got != want:
        mismatches.append({"time_utc": t, "trade": tr, "recomputed": got, "journal": want})
(HERE / "plans.json").write_text(json.dumps({"plans": plans, "mismatches_with_the_journal": mismatches}, indent=0))

# 3. the STP-authorised trades
RC = re.compile(r"STP authorised: the rejection candle (.+?) reached the live (BUY|SELL) opportunity (\S+) \(.+?\); "
                r"test (\d+); duplicate key (\S+);")
orders = [json.loads(x) for x in (SNAP / "orders.jsonl").read_text().splitlines() if x.strip()]
sending = {o["reference"]: o for o in orders if o.get("event") == "sending"}
out = []
for t in (json.loads(x) for x in (SNAP / "trades.jsonl").read_text().splitlines() if x.strip()):
    if t.get("event") != "opened":
        continue
    for step in t.get("steps") or []:
        m = RC.search(step)
        if m:
            d, mon, hm = re.match(r"\w+ (\d+) (\w+) (\d\d:\d\d)", m.group(1)).groups()
            snd = sending.get(t["reference"], {})
            out.append({"reference": t["reference"], "strategy": t["strategy"], "direction": t["direction"],
                        "idea_time": snd.get("idea_time"), "opened_utc": t["opened_utc"],
                        "entry_price": t["entry_price"], "rejection_candle": f"2026-11-{int(d):02d}T{hm}:00Z",
                        "recorded_opportunity": m.group(3).rstrip(","), "recorded_test": int(m.group(4)),
                        "recorded_signal": snd.get("signal") or m.group(5)})
(HERE / "stp_trades.json").write_text(json.dumps(sorted(out, key=lambda x: x["opened_utc"]), indent=1))

# 4. production's own lifecycle events, for comparison
ops = [{k: e.get(k) for k in ("time_utc", "event", "id", "why")} for e in events
       if e.get("id") and e["time_utc"] >= "2026-11-24T23:00:00Z"]
(HERE / "journal_opportunities.json").write_text(json.dumps(ops, indent=0))
print(f"{len(analyses)} analyses, {sum(len(v) for v in plans.values())} plans, {len(mismatches)} mismatches, "
      f"{len(out)} STP trades, {len(ops)} opportunity events")
