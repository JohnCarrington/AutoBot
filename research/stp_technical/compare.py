"""Extra views of the scored STP technical replay, and a head-to-head with the existing STP. READ ONLY.

  PYTHONPATH=. python -m research.stp_technical.compare --scored docs/research/stp_technical_20261120/replay/scored_rows.jsonl.gz \
      --replay docs/research/stp_technical_20261120/replay/{dev1,dev2,test1,test2}.jsonl.gz \
      --stp docs/research/stp_structural_history_20261120/evaluation_rows.jsonl.gz

Prints, for the TEST period (from 2025-07-01):
  - by type: share of forecasts whose entry zone was reached, winners' adverse excursion (p50/p75/p90), losers' best
    favourable move, hours to outcome;
  - 8-15-pip targets by type, and new-only, with the weekly-block bootstrap (DEV too);
  - the head-to-head at the 4-hour timestamps both planners assessed: who spoke, direction agreement, and the
    technical forecast's edge when it agrees or disagrees with the existing STP (version C, deployed bb085f4).
"""
from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

from research.stp_technical.score import SPLIT, boot, week

TYPES = ("PULLBACK", "REVERSAL", "FAILED_BREAKOUT", "BREAKOUT", "RANGE_REVERSAL")
RESOLVED = ("TARGET", "STOP")


def _q(xs: list[float], p: float) -> float | None:
    return round(sorted(xs)[int(p * (len(xs) - 1))], 1) if xs else None


def _items(rows: list[dict]) -> list[tuple]:
    return [(week(r["as_of"]), int(r["main"]["won"]), r["main"]["expected"]) for r in rows
            if r["main"]["sequence"] in RESOLVED]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored", required=True, type=Path)
    ap.add_argument("--replay", required=True, nargs="+", type=Path)
    ap.add_argument("--stp", required=True, type=Path)
    a = ap.parse_args()
    rows = [json.loads(x) for x in gzip.open(a.scored, "rt")]
    test = [r for r in rows if r["as_of"] >= SPLIT]

    print("TEST by type: forecasts, entry zone reached, winners' MAE p50/p75/p90, losers' MFE p50, hours p50")
    for t in TYPES + ("ALL",):
        rs = [r for r in test if t == "ALL" or r["type"] == t]
        if not rs:
            continue
        ent = sum(r["main"]["sequence"] in RESOLVED + ("OPEN",) for r in rs)
        w = [r["main"]["mae_pips"] for r in rs if r["main"]["sequence"] == "TARGET"]
        lo = [r["main"]["mfe_pips"] for r in rs if r["main"]["sequence"] == "STOP"]
        h = [r["main"]["hours_to_outcome"] for r in rs if r["main"].get("hours_to_outcome") is not None]
        print(t, len(rs), "entered", ent, f"{100 * ent / len(rs):.1f}%", "winMAE", _q(w, .5), _q(w, .75), _q(w, .9),
              "loseMFE", _q(lo, .5), "hrs", _q(h, .5))

    print("\n8-15-pip targets (weekly-block bootstrap)")
    for per, sel in (("DEV", lambda r: r["as_of"] < SPLIT), ("TEST", lambda r: r["as_of"] >= SPLIT)):
        small = [r for r in rows if sel(r) and 8 <= r["main"]["d"] <= 15]
        for t in TYPES:
            b = boot(_items([r for r in small if r["type"] == t]))
            if b:
                print(per, t, b)
        print(per, "new-only", boot(_items([r for r in small if r["new"]])))

    stp = {}
    for x in gzip.open(a.stp, "rt"):
        r = json.loads(x)
        if r.get("fresh"):
            stp[r["as_of_utc"][:16]] = r["C"]
    alltech = {}
    for p in a.replay:
        for x in gzip.open(p, "rt"):
            f = json.loads(x)
            alltech[f["as_of_utc"][:16]] = f
    scored = {r["as_of"][:16]: r for r in rows}
    c, by = Counter(), defaultdict(list)
    for ts, s in stp.items():
        if ts < SPLIT or ts not in alltech:
            continue
        c["shared"] += 1
        so = s.get("trade") if s.get("entry") else None
        tt = (alltech[ts].get("opportunity") or {}).get("trade")
        c[("stp" if so else "-") + "/" + ("tech" if tt else "-")] += 1
        if so and tt:
            k = "agree" if so == tt else "disagree"
            c[k] += 1
            r = scored.get(ts)
            if r and r["main"]["sequence"] in RESOLVED:
                by[k].append(r)
    print("\nTEST head-to-head at shared 4-hour timestamps:", dict(c))
    for k, rs in by.items():
        print(k, "technical forecast:", boot(_items(rs)))


if __name__ == "__main__":
    main()
