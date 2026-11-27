"""Compact copies of what planner/migrate_lineage.py reads, for its tests (owner, 27 November 2026). Run once, offline,
on the same COPY of the production files as make_fixtures.py:

    .venv/bin/python tests/stp/fixtures/lifecycle_20261127/make_migration_fixtures.py <snapshot>

Writes migration/planner/{recommendations.jsonl, issued.jsonl, current.json}: only the events from 24 November and only
the fields the migration reads; migration/orders.jsonl: the "sending", "opened" and "adopted" records of the orders
that carried an STP key (their signal, never a price or amount); migration/trades.jsonl: the "opened" rows of those
trades, with their entry steps only."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent / "migration"
SNAP = Path(sys.argv[1])
SINCE = "2026-11-24T00:00:00Z"


def jl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


(HERE / "planner").mkdir(parents=True, exist_ok=True)
ev = [e for e in jl(SNAP / "planner" / "recommendations.jsonl") if e["time_utc"] >= SINCE and e.get("id")]
ev = [{k: e.get(k) for k in ("time_utc", "event", "id", "why")} for e in ev]
(HERE / "planner" / "recommendations.jsonl").write_text("".join(json.dumps(e) + "\n" for e in ev))
ids = {e["id"] for e in ev}
iss = []
for r in jl(SNAP / "planner" / "issued.jsonl"):
    if r["id"] in ids:
        pr = (r.get("destinations") or {}).get("primary") or {}
        iss.append({"id": r["id"], "trade": r["trade"], "created_utc": r["created_utc"], "identity": r["identity"],
                    "entry_zone": {"low": r["entry_zone"]["low"], "high": r["entry_zone"]["high"]},
                    "destinations": {"primary": {"price": pr.get("price"),
                                                 "zone": {"low": pr["zone"]["low"], "high": pr["zone"]["high"]}
                                                 if pr.get("zone") else None}}})
(HERE / "planner" / "issued.jsonl").write_text("".join(json.dumps(r) + "\n" for r in iss))
cur = json.loads((SNAP / "planner" / "current.json").read_text())
(HERE / "planner" / "current.json").write_text(json.dumps({"opportunities": [
    {"id": o["id"], "trade": o["trade"], "entry_zone": {"low": o["entry_zone"]["low"], "high": o["entry_zone"]["high"]}}
    for o in cur.get("opportunities") or []]}, indent=1))
orders = jl(SNAP / "orders.jsonl")
stp_refs = {o["reference"] for o in orders if o.get("event") == "sending" and "STP-" in (o.get("signal") or "")}
keep = [{k: o.get(k) for k in ("time_utc", "event", "reference", "strategy", "direction", "signal")}
        for o in orders if o.get("reference") in stp_refs and o.get("event") in ("sending", "opened", "adopted")]
(HERE / "orders.jsonl").write_text("".join(json.dumps(o) + "\n" for o in keep))
trades = [{"event": "opened", "reference": t["reference"], "steps": [s for s in t.get("steps") or []
                                                                   if s.startswith("STP authorised")]}
          for t in jl(SNAP / "trades.jsonl") if t.get("event") == "opened" and t["reference"] in stp_refs]
(HERE / "trades.jsonl").write_text("".join(json.dumps(t) + "\n" for t in trades))
print(len(ev), "events,", len(iss), "issued,", len(keep), "order records,", len(trades), "trades")
