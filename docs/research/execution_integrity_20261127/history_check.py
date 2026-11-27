"""Read-only: every closed trade in records/<PAIR>/trades.jsonl against IG's own records saved by the owner's
read-only IG checks (data/orders/ig_check_result*.json: IG's activity and transactions) and the order journal's
IG levels (data/orders/<PAIR>/orders.jsonl, "ig_level"). Writes nothing; prints what differs and what IG evidence is
missing (owner, 27 November 2026). Usage: .venv/bin/python -I docs/research/execution_integrity_20261127/history_check.py
"""
import glob
import json
from decimal import Decimal as D
from pathlib import Path

DATA = Path("/opt/autobot/data")


def main() -> None:
    close, tx = {}, []
    for f in sorted(glob.glob(str(DATA / "orders" / "ig_check_result*.json"))):
        d = json.loads(Path(f).read_text())
        for a in d.get("activity") if isinstance(d.get("activity"), list) else []:
            for x in (a.get("details") or {}).get("actions") or []:
                if str(x.get("actionType", "")).startswith(("POSITION_CLOSED", "POSITION_DELETED")):
                    close[x["affectedDealId"]] = (a["date"], D(str((a.get("details") or {}).get("level"))), a.get("channel"))
        tx += d.get("transactions") if isinstance(d.get("transactions"), list) else []
    pl = {}                                                  # (open time to the minute, open level) -> IG's £ (all parts)
    seen = {}
    for t in tx:                                             # each IG transaction once (the checks overlap)
        if t.get("transactionType") == "DEAL" and t.get("openLevel") not in (None, "-"):
            seen[(t.get("reference"), t.get("dateUtc"))] = t
    for t in seen.values():
        k = (t.get("openDateUtc", "")[:19], str(D(str(t.get("openLevel")))))
        pl[k] = pl.get(k, D(0)) + D(t["profitAndLoss"].replace("£", "").replace(",", ""))
    journal = {}
    for line in (DATA / "orders" / "GBPUSD" / "orders.jsonl").read_text().splitlines():
        o = json.loads(line)
        if o.get("ig_level") and o.get("deal_id"):
            journal[o["deal_id"]] = (o.get("ig_time_utc"), D(o["ig_level"]), o.get("ig_channel"))
    rows = [json.loads(x) for x in (DATA / "records" / "GBPUSD" / "trades.jsonl").read_text().splitlines()]
    closed = [r for r in rows if r["event"] == "closed" and not r.get("paper")]
    n_ev, diffs, missing = 0, [], []
    for r in closed:
        ig = close.get(r["deal_id"]) or journal.get(r["deal_id"])
        igpl = pl.get((r["opened_utc"][:19], str(D(str(r["open_price"])))))
        if ig is None and igpl is None:
            missing.append(r)
            continue
        n_ev += 1
        lvl_ok = ig is None or r.get("close_price") is None or D(str(r["close_price"])) == ig[1]
        pl_ok = igpl is None or r.get("gbp") is None or D(str(r["gbp"])) == igpl
        if not (lvl_ok and pl_ok):
            diffs.append((r["reference"], r["strategy"], r["direction"], r["closed_utc"], r.get("close_price"), r.get("gbp"),
                          None if ig is None else (ig[0], str(ig[1]), ig[2]), None if igpl is None else str(igpl)))
    print(f"closed bot records: {len(closed)}; with IG evidence: {n_ev}; differing from IG: {len(diffs)}; "
          f"without IG evidence: {len(missing)}")
    for d in diffs:
        print("DIFFERS", *d)
    for r in missing:
        print("NO IG EVIDENCE", r["reference"], r["deal_id"], r["strategy"], r["closed_utc"], r.get("close_price"), r.get("gbp"))


if __name__ == "__main__":
    main()
