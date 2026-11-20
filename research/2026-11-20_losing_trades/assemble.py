"""Builds REPORT.md from the hand-written parts and the tables generated from trades.csv."""
import csv, collections, subprocess
from pathlib import Path
D = Path(__file__).parent
rows = list(csv.DictReader(open(D / "trades.csv")))
def pips(r): return float(r["ig_pips"]) if r["ig_pips"] != "" else None
lr = ["| Opened | Code | Dir | Rule stop pips | IG stop pips | TP pips | Stop ≥ TP? | IG pips | Closed by |", "|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    if r["strategy"] != "level reversal": continue
    sd = float(r["ig_stop_distance"])
    lr.append(f"| {r['opened_utc'][5:16].replace('T',' ')} | {r['commit']} | {r['direction']} | {r['rule_stop_pips']} | {sd} | {r['tp_pips']} | "
              f"{'**yes**' if sd >= float(r['tp_pips']) else 'no'} | {r['ig_pips'] or 'open'} | {r['how_closed'] or 'still open'} |")
tot = ["| Strategy | Bot trades | Wins | Losses | Total IG pips | £ | Johnny's closes (pips) |", "|---|---|---|---|---|---|---|"]
g, o = collections.defaultdict(list), collections.defaultdict(list)
for r in rows:
    if r["closed_utc"] == "OPEN" or pips(r) is None: continue
    (o if r["closed_by"] == "owner" else g)[r["strategy"]].append(pips(r))
for st, v in sorted(g.items(), key=lambda kv: sum(kv[1])):
    ow = o.get(st, [])
    tot.append(f"| {st} | {len(v)} | {len([x for x in v if x>0])} | {len([x for x in v if x<0])} | {sum(v):+.1f} | {sum(v)*10:+.0f} | "
               f"{(f'{sum(ow):+.1f} ({len(ow)})') if ow else '–'} |")
allv = [x for v in g.values() for x in v]; allo = [x for v in o.values() for x in v]
tot.append(f"| **all** | **{len(allv)}** | **{len([x for x in allv if x>0])}** | **{len([x for x in allv if x<0])}** | **{sum(allv):+.1f}** | **{sum(allv)*10:+.0f}** | **{sum(allo):+.1f} ({len(allo)})** |")
step3 = (D / "REPORT_step3.md").read_text().replace("LR_TABLE", "\n".join(lr))
step5 = (D / "REPORT_step5.md").read_text().replace("STRATEGY_TOTALS", "\n".join(tot))
tables = subprocess.run(["python3", str(D / "tables.py")], capture_output=True, text=True).stdout
stats = subprocess.run(["python3", str(D / "stats.py")], capture_output=True, text=True).stdout
E = tables.split("## E\n", 1)[1].split("## OLDER", 1)[0].strip()
OLD = tables.split("## OLDER\n", 1)[1].split("## OVERLAPS", 1)[0].strip()
parts = [(D / "REPORT_head.md").read_text(), (D / "REPORT_step0_1.md").read_text().replace("E_TABLE", E).replace("OLDER_TABLES", OLD),
         "## Step 2. Per strategy, per version period\n\nIG pips (IG's open and close levels); a trade is a win above 0. "
         "Johnny's hand closes are kept apart and are not the bot's result.\n" + stats,
         step3, (D / "REPORT_step4.md").read_text(), step5,
         (D / "REPORT_week_text.md").read_text().replace("WEEK_TABLE", subprocess.run(["python3", str(D / "week_review.py")], capture_output=True, text=True).stdout.strip()),
         (D / "REPORT_files.md").read_text()]
(D / "REPORT.md").write_text("\n\n".join(p.strip() for p in parts) + "\n")
print("REPORT.md written,", len((D / "REPORT.md").read_text().splitlines()), "lines")
