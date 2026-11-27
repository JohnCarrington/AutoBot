"""The controlled reconciliation review (owner's approval of 27 November 2026: D-R1 and D-R2, fail closed). Read only.

    .venv/bin/python -m planner.review --pair GBPUSD          prints every opportunity STP's tracker holds blocked by
                                                              missing or uncertain evidence, with its evidence

An opportunity is BLOCKED (authorises nothing; every other rule still applies; nothing expires) while either:
  * D-R1, unavailable evidence: a recorded data gap in its life is still open, because IG's history has not supplied
    every missing candle; or
  * D-R2, uncertain test identity: a gap was re-checked but a recovered hourly candle would change a test already
    numbered, or a zone break the tracker can no longer place ("review"); or its lineage's D-25 count holds an
    uncertain hour (an incomplete hourly candle whose stored parts are clear of the zone).

The procedure (docs/research/stp_lifecycle_integrity_20261127/implementation/REVIEW_R1_R4.md, section R4):
  1. run this report;
  2. for D-R1, the approved IG recovery (prices/history_fill.py gap-plan, then gap-go in a maintenance window with
     the price service stopped); the tracker re-checks the opportunity on the recovered candles at its next run;
  3. what is still blocked stays blocked until it ends by its own rules. There is no manual override: the owner's
     decision is fail closed.
Guarantees (tests TW3-xx, TR4-xx): uncertainty never renumbers or frees a consumed test (a numbered test is never
renumbered; consumed tests and alias keys stay in the lineage); unrelated opportunities stay eligible; nothing here or
in the reconciliation places an order, delays an entry or rewrites a trading record; every change is a new event.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def blocked(state: dict) -> list[dict]:
    out = []
    lins = state.get("lineages") or {}
    for o in state.get("opportunities") or []:
        L = lins.get(o.get("lineage") or o.get("id")) or {}
        gaps = [g for g in o.get("data_gaps") or [] if g.get("status") != "reconciled"]
        unc = list((L.get("tests") or {}).get("uncertain") or [])
        if gaps or unc:
            out.append({"id": o["id"], "trade": o.get("trade"), "status": o.get("status"), "lineage": o.get("lineage"),
                        "gaps": gaps, "uncertain_hours": unc, "consumed": L.get("consumed") or {},
                        "aliases": L.get("aliases") or {},
                        "rule": "D-R1 (evidence unavailable)" if any(g.get("status") == "open" for g in gaps)
                        else "D-R2 (test identity uncertain)"})
    return out


def main(argv: list[str] | None = None) -> int:
    from config.settings_loader import load_or_exit
    ap = argparse.ArgumentParser(prog="python -m planner.review")
    ap.add_argument("--pair", required=True)
    a = ap.parse_args(argv)
    s = load_or_exit().for_pair(a.pair.upper())
    path = Path(s.planner.folder) / s.market.pair / "current.json"
    try:
        state = json.loads(path.read_text())
    except (OSError, ValueError) as e:
        print(f"cannot read {path}: {e}")
        return 2
    rows = blocked(state)
    print(json.dumps(rows, indent=1) if rows else "No opportunity is blocked by missing or uncertain evidence.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
