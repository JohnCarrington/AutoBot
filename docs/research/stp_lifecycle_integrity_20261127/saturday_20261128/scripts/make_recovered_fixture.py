"""Recovered fixture = the 18:29 fixture's candle files, each replaced by the post-fill store's rows up to the fixture
file's own last row (so nothing later than production's 18:29 copy is added; only IG's recovered candles and the
bigger candles rebuilt from them change)."""
import csv, sys, io
from pathlib import Path
fix, post, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
for f in sorted((fix/"candles"/"GBPUSD").rglob("*.csv")):
    rel = f.relative_to(fix/"candles"/"GBPUSD")
    if rel.name == "gaps.csv": continue
    a = list(csv.DictReader(open(f))); hdr = open(f).readline()
    last = max(r["start_utc"] for r in a)
    b = [r for r in csv.DictReader(open(post/rel)) if r["start_utc"] <= last]
    pre_rows = {r["start_utc"]: r for r in a}
    added = [r["start_utc"] for r in b if r["start_utc"] not in pre_rows]
    changed = [r["start_utc"] for r in b if r["start_utc"] in pre_rows and r != pre_rows[r["start_utc"]]]
    missing = [k for k in pre_rows if k not in {r["start_utc"] for r in b}]
    assert not missing, (rel, missing)
    buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=hdr.strip().split(","), lineterminator="\n")
    w.writeheader(); [w.writerow(r) for r in b]
    (out/"candles"/"GBPUSD"/rel).write_text(buf.getvalue())
    if added or changed: print(rel, "added", added, "changed", changed)
