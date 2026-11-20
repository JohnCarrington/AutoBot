"""Offline multi-period replication of structural journey/momentum findings.

Runs the same frozen research methods on separate quarters, without fitting or
changing parameters. Each quarter's inputs and outputs remain inspectable.
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path


def quarter_windows(start, end):
    cursor = date(start.year, ((start.month-1)//3)*3+1, 1)
    while cursor <= end:
        y, m = cursor.year, cursor.month
        following = date(y+1, 1, 1) if m == 10 else date(y, m+3, 1)
        a, b = max(start, cursor), min(end, following-timedelta(days=1))
        if a <= b:
            yield a, b
        cursor = following


def rate(rows, key, outcome):
    chosen = [r for r in rows if r.get(key) == outcome]
    counts = Counter(r["outcome"] for r in chosen)
    n = counts["REVERSAL_DESTINATION"]+counts["CONTINUATION_DESTINATION"]
    return {"encounters":len(chosen),"resolved":n,
            "reversal":counts["REVERSAL_DESTINATION"],
            "continuation":counts["CONTINUATION_DESTINATION"],
            "reversal_rate":counts["REVERSAL_DESTINATION"]/n if n else None}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--historical-store",type=Path,required=True)
    p.add_argument("--start-date",default="2024-01-01")
    p.add_argument("--end-date",default="2026-04-10")
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    folder=a.historical_store.resolve()
    if folder.name!="GBPUSD" or not (folder/"rebuild_manifest.json").exists():
        p.error("requires isolated rebuilt GBPUSD historical store")
    if a.output_dir.resolve().is_relative_to(folder):
        p.error("output directory must be outside historical store")
    start,end=date.fromisoformat(a.start_date),date.fromisoformat(a.end_date)
    if start>end: p.error("invalid date range")
    a.output_dir.mkdir(parents=True,exist_ok=True)
    records=[]
    periods=[]
    for begin,finish in quarter_windows(start,end):
        tag=f"{begin:%Y%m%d}_{finish:%Y%m%d}"
        files={name:a.output_dir/f"{tag}_{name}.json"
               for name in ("encounters","momentum","journeys","joined")}
        stages=[
            ("research.stp_validation.confluence_encounters",
             ["--historical-store",str(folder),"--start-date",begin.isoformat(),
              "--end-date",finish.isoformat(),"--output",str(files["encounters"])]),
            ("research.stp_validation.momentum_exhaustion",
             ["--historical-store",str(folder),"--encounters",str(files["encounters"]),
              "--output",str(files["momentum"])]),
            ("research.stp_validation.structural_journeys",
             ["--historical-store",str(folder),"--encounters",str(files["encounters"]),
              "--output",str(files["journeys"])]),
            ("research.stp_validation.journey_momentum_analysis",
             ["--momentum",str(files["momentum"]),"--journeys",str(files["journeys"]),
              "--output",str(files["joined"])]),
        ]
        print(f"Processing {begin} to {finish}",flush=True)
        for module,args in stages:
            # Fail closed; never combine partial or mismatched runs.
            subprocess.run([sys.executable,"-m",module,*args],check=True,
                           stdout=subprocess.DEVNULL)
        joined=json.loads(files["joined"].read_text())
        rows=joined["encounters"]
        periods.append({"start":begin.isoformat(),"end":finish.isoformat(),
                        "encounters":len(rows),"resolved":joined["overall"]["resolved"],
                        "by_momentum_state":joined["by_momentum_state"],
                        "by_momentum_and_confluence":joined["by_momentum_and_confluence"],
                        "file":str(files["joined"])})
        records.extend(rows)
        print(f"  encounters={len(rows)} resolved={joined['overall']['resolved']}",flush=True)
    def cohort(rows):
        states=sorted({r["momentum_state"] for r in rows})
        return {state:rate(rows,"momentum_state",state) for state in states}
    def period_rows(y0,y1):
        return [r for r in records if y0<=int(r["day"][:4])<=y1]
    report={
        "method":"Frozen quarterly replication, no fitting or threshold changes",
        "periods":periods,
        "cohorts":{
            "2024_exploratory":cohort(period_rows(2024,2024)),
            "2025_validation":cohort(period_rows(2025,2025)),
            "2026_holdout":cohort(period_rows(2026,2026)),
        },
        "total_encounters":len(records),
        "caveats":[
            "2025 and 2026 are chronological checks, not pristine independent holdouts: prior Q1 2025 results informed the research direction.",
            "Overlapping 48h outcomes and repeated zones within quarters create correlated observations.",
            "Quarter-end encounters are scored using later candles available in the isolated store.",
            "Momentum module can be CPU intensive on a 2-vCPU host.",
            "No H1/H4 features, no major-zone ranking, no advance forecast accuracy.",
            "No broker calls, no production service changes, no shadow trading.",
        ],
    }
    output=a.output_dir/"replication_summary.json"
    output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"total_encounters":report["total_encounters"],
                      "cohorts":report["cohorts"]},indent=2))
    print(f"Saved {output}")


if __name__=="__main__":
    main()
