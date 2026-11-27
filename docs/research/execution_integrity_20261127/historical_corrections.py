"""The three historical closes that differ from IG's own records (REPORT.md section 6), as append-only "close
corrected" lines for records/GBPUSD/trades.jsonl. PREPARED, NOT APPLIED: historical amendments need the owner's
authorisation (27 November 2026).

  dry run (default, writes nothing):  .venv/bin/python -I docs/research/execution_integrity_20261127/historical_corrections.py
  apply (owner-authorised only):      ... historical_corrections.py --apply --i-have-the-owners-authorisation

--apply backs trades.jsonl up first (trades.jsonl.before-<UTC time>-ig-corrections), refuses if any of the three
already has a "close corrected" line, and appends one line each. Every figure is IG's (its activity and transactions,
saved by the owner's read-only IG checks); pips, £ and result are worked out by records.book.corrected_figures, the
code every reader uses."""
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from records.book import apply_corrections, corrected_figures  # noqa: E402

TRADES = Path("/opt/autobot/data/records/GBPUSD/trades.jsonl")
IG = [  # reference, IG's close level, IG's close time (UTC), IG's evidence
    ("AB261111065505-6d002d16", "13332.8", "2026-11-11T07:35:01Z",
     "IG activity: closed 07:35:01 at 13332.8 (PUBLIC_WEB_API); IG transaction £-33.00 (ig_check_result.2026-11-11_rest.json)"),
    ("AB261118123737-487acb12", "13168.4", "2026-11-18T13:07:56Z",
     "IG activity: closed 13:07:56 at 13168.4 (SYSTEM, stop); IG transaction £-120.00 (ig_check_result.2026-11-18_1230_to_now.json)"),
    ("AB261126060101-987e099b", "13108.9", "2026-11-26T09:35:01Z",
     "IG activity: closed 09:35:01 at 13108.9 (SYSTEM, moved stop); orders.jsonl closed at IG ig_level 13108.9"),
]


def lines(rows: list[dict]) -> list[dict]:
    out = []
    for ref, level, when, evidence in IG:
        row = next(r for r in rows if r.get("event") == "closed" and r.get("reference") == ref)
        fig = corrected_figures(row, level)
        out.append({"event": "close corrected", "paper": False, "reference": ref, "closed_utc": when,
                    "price_source": "IG's activity (historical reconciliation)"} | fig |
                   {"before": {k: row.get(k) for k in ("close_price", "closed_utc", "pips", "gbp")}, "evidence": evidence})
    return out


def main() -> None:
    rows = [json.loads(x) for x in TRADES.read_text().splitlines()]
    new = lines(rows)
    for n in new:
        b = n["before"]
        print(f"{n['reference']}: {b['close_price']} {b['closed_utc']} {b['pips']} pips £{b['gbp']}  ->  "
              f"{n['close_price']} {n['closed_utc']} {n['pips']} pips £{n['gbp']}  ({n['evidence']})")
    before = sum(float(r["gbp"]) for r in apply_corrections(rows) if r.get("closed_by") != "owner" and r.get("gbp"))
    after = sum(float(r["gbp"]) for r in apply_corrections(rows + new) if r.get("closed_by") != "owner" and r.get("gbp"))
    print(f"bot total in the records: £{before:.2f} -> £{after:.2f} ({after - before:+.2f})")
    if "--apply" not in sys.argv:
        print("dry run: nothing written")
        return
    if "--i-have-the-owners-authorisation" not in sys.argv:
        sys.exit("refused: --apply needs --i-have-the-owners-authorisation")
    done = {r["reference"] for r in rows if r.get("event") == "close corrected"}
    if done & {n["reference"] for n in new}:
        sys.exit(f"refused: already corrected: {sorted(done & {n['reference'] for n in new})}")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    shutil.copy2(TRADES, TRADES.with_name(f"trades.jsonl.before-{stamp}-ig-corrections"))
    with TRADES.open("a") as f:
        for n in new:
            f.write(json.dumps(n) + "\n")
    print(f"applied: {len(new)} lines appended; backup trades.jsonl.before-{stamp}-ig-corrections")


if __name__ == "__main__":
    main()
