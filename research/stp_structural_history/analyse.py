"""Summarise evaluate.py's output. READ ONLY.

  python -m research.stp_structural_history.analyse --rows eval.jsonl.gz --out results.json

Edge = observed rate minus the random-walk expectation z/(d+z), in percentage points, with a 95% interval from a
weekly-block bootstrap (decisions overlap, so whole ISO weeks are resampled). DEV < 2025-07-01 <= TEST, as in the
20 November validation.
"""
from __future__ import annotations

import argparse
import gzip
import json
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path

SPLIT = "2025-07-01"


def boot(items, reps=2000, seed=20261120):
    """items: (week, won, expected). Mean edge (pts) and 95% weekly-block interval."""
    if not items:
        return None
    by = defaultdict(list)
    for w, won, e in items:
        by[w].append(won - e)
    weeks = list(by)
    rnd = random.Random(seed)
    means = []
    for _ in range(reps):
        xs = [x for w in (rnd.choice(weeks) for _ in weeks) for x in by[w]]
        means.append(sum(xs) / len(xs))
    means.sort()
    n = len(items)
    return {"n": n, "observed_pct": round(100 * sum(i[1] for i in items) / n, 1),
            "expected_pct": round(100 * sum(i[2] for i in items) / n, 1),
            "edge_pts": round(100 * sum(i[1] - i[2] for i in items) / n, 1),
            "ci95_pts": [round(100 * means[int(0.025 * reps)], 1), round(100 * means[int(0.975 * reps)], 1)]}


def week(t):
    from datetime import datetime
    y, w, _ = datetime.fromisoformat(t).isocalendar()
    return f"{y}-W{w:02d}"


def has_plan(v):
    return bool(v and v.get("entry") and v.get("primary"))


def group_stats(entries):
    """entries: (as_of, variant summary)."""
    out = {}
    for period in ("ALL", "DEV", "TEST"):
        sel = [(t, v) for t, v in entries if period == "ALL" or (period == "DEV") == (t < SPLIT)]
        o = {"plans": len(sel)}
        for k in ("rw_zone", "rw_struct"):
            items = [(week(t), int(v["outcome"][k]["won"]), v["outcome"][k]["expected"]) for t, v in sel
                     if v.get("outcome") and k in v["outcome"]]
            o[k] = boot(items)
        seq = Counter(v["outcome"]["sequence"] for t, v in sel if v.get("outcome"))
        done = sum(c for s, c in seq.items() if s != "CENSORED")
        o["sequence"] = dict(seq)
        o["entry_then_destination_pct"] = round(100 * seq["ENTRY_THEN_DESTINATION"] / done, 1) if done else None
        o["entry_then_invalidated_pct"] = round(100 * seq["ENTRY_THEN_INVALIDATED"] / done, 1) if done else None
        dists = [v["outcome"]["dest_distance_pips"] for t, v in sel if v.get("outcome")]
        o["median_destination_pips"] = statistics.median(dists) if dists else None
        out[period] = o
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    rows = []
    try:
        for x in gzip.open(a.rows, "rt"):
            rows.append(json.loads(x))
    except (EOFError, json.JSONDecodeError):            # a run still being written: use the complete rows
        pass
    scored = [r for r in rows if "A" in r]
    res = {"decisions": len(rows), "scored_decisions": len(scored), "not_fresh": len(rows) - len(scored)}
    # direction and condition must not change: the history only adds levels
    res["direction_or_condition_differs"] = sum(1 for r in scored if len({(r[k]["direction"], r[k]["condition"])
                                                                            for k in "ABC"}) > 1)
    for k in "ABC":
        res[f"plans_{k}"] = sum(1 for r in scored if has_plan(r[k]))
        res[f"reasons_{k}"] = Counter((r[k]["no_rec"] or "PLAN")[:70] for r in scored).most_common(8)
    groups = defaultdict(list)
    for r in scored:
        t = r["as_of_utc"]
        a_, c_ = r["A"], r["C"]
        for k in "ABC":
            if has_plan(r[k]):
                groups[f"all_{k}"].append((t, r[k]))
        if has_plan(a_) and has_plan(c_):
            if a_["entry"] == c_["entry"] and a_["primary"] == c_["primary"]:
                groups["same_in_A_and_C"].append((t, c_))
            else:
                groups["changed_A_version"].append((t, a_))
                groups["changed_C_version"].append((t, c_))
        elif has_plan(c_):
            groups["new_in_C"].append((t, c_))
        elif has_plan(a_):
            groups["dropped_in_C_A_version"].append((t, a_))
        if has_plan(r["B"]) and not has_plan(a_):
            groups["new_in_B"].append((t, r["B"]))
    res["groups"] = {g: group_stats(e) for g, e in sorted(groups.items())}
    a.out.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k != "groups"}, indent=1))
    for g, s in res["groups"].items():
        x = s["ALL"]
        print(f"{g:28s} plans {x['plans']:5d}  rw_zone {x['rw_zone']}  E->D {x['entry_then_destination_pct']}%  "
              f"med dest {x['median_destination_pips']}")


if __name__ == "__main__":
    main()
