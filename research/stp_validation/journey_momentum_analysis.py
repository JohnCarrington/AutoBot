"""Offline join: pre-encounter momentum/exhaustion vs 48h structural journeys.

No broker access, no fitted classifier, no strategy changes. Input files must
come from the SAME confluence-encounter run; joins use encounter identity.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def identity(row):
    return (row["day"], row["as_of"], row["side"],
            str(row["zone_low"]) if "zone_low" in row else str(row["origin_zone"][0]),
            str(row["zone_high"]) if "zone_high" in row else str(row["origin_zone"][1]))


def summary(rows):
    counts = Counter(x["outcome"] for x in rows)
    resolved = counts["REVERSAL_DESTINATION"] + counts["CONTINUATION_DESTINATION"]
    return {
        "encounters": len(rows), "outcomes": dict(counts),
        "resolved": resolved,
        "reversal_destination_first_rate": counts["REVERSAL_DESTINATION"] / resolved if resolved else None,
        "continuation_destination_first_rate": counts["CONTINUATION_DESTINATION"] / resolved if resolved else None,
    }


def analyse(momentum_data, journeys_data):
    momentum = momentum_data["encounters"]
    journeys = journeys_data["journeys"]
    by_key = {}
    for m in momentum:
        key = identity(m)
        if key in by_key:
            raise ValueError(f"Duplicate momentum encounter: {key}")
        by_key[key] = m
    seen = set()
    joined = []
    for j in journeys:
        key = identity(j)
        if key in seen:
            raise ValueError(f"Duplicate journey encounter: {key}")
        seen.add(key)
        if key not in by_key:
            raise ValueError(f"Missing momentum encounter for journey: {key}")
        m = by_key[key]
        if m["levels"] != j["levels"] or m["family_count"] != j["family_count"]:
            raise ValueError(f"Different structural inputs for encounter: {key}")
        state = m["momentum_exhaustion"]["state"]
        joined.append({
            "day": j["day"], "as_of": j["as_of"], "side": j["side"],
            "momentum_state": state, "family_count": j["family_count"],
            "families": m["families"], "outcome": j["outcome"],
            "reversal_destination": j["reversal_destination"],
            "continuation_destination": j["continuation_destination"],
            "reached_at": j["reached_at"],
            "momentum_features": m["momentum_exhaustion"],
        })
    if set(by_key) != seen:
        raise ValueError(f"Unmatched momentum encounters: {len(set(by_key)-seen)}")
    by_state = defaultdict(list)
    by_families = defaultdict(list)
    by_joint = defaultdict(list)
    by_side = defaultdict(list)
    for row in joined:
        state = row["momentum_state"]
        families = row["family_count"]
        by_state[state].append(row)
        by_families[str(families)].append(row)
        by_joint[f"{state}__{families}_families"].append(row)
        by_side[row["side"]].append(row)
    return {
        "method": "exact-encounter join of pre-encounter momentum and 48h structural destinations",
        "overall": summary(joined),
        "by_momentum_state": {k: summary(v) for k,v in sorted(by_state.items())},
        "by_independent_confluence_families": {k: summary(v) for k,v in sorted(by_families.items())},
        "by_momentum_and_confluence": {k: summary(v) for k,v in sorted(by_joint.items())},
        "by_side": {k: summary(v) for k,v in sorted(by_side.items())},
        "caveats": [
            "Descriptive retrospective stratification, not advance STP predictions or a trained model.",
            "Exhaustion features are M5-only, not confirmed H1/H4 exhaustion.",
            "Structural destinations are nearest prior-session levels, not confluence-ranked major zones.",
            "The source journey study has a 48-hour wall-clock horizon including weekends.",
            "One or both targets may be unavailable; censored and missing-target events are not wins.",
            "Small correlated samples; no statistical edge or trend-day accuracy claim.",
            "No production modifications, orders, or shadow trading.",
        ],
        "encounters": joined,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--momentum", type=Path, required=True)
    p.add_argument("--journeys", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    for source in (a.momentum, a.journeys):
        if not source.is_file():
            p.error(f"missing input file: {source}")
    result = analyse(json.loads(a.momentum.read_text()),
                     json.loads(a.journeys.read_text()))
    a.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k != "encounters"}, indent=2))
    print(f"Saved {len(result['encounters'])} joined encounters to {a.output}")


if __name__ == "__main__":
    main()
