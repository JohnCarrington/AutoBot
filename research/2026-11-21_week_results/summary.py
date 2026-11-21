"""Summary tables from week_results.csv (per strategy, analyser state, session). Writes summary.md."""
import csv
from collections import OrderedDict
from pathlib import Path

D = Path(__file__).parent
rows = list(csv.DictReader(open(D / "week_results.csv")))


def table(key, title):
    g = OrderedDict()
    for r in sorted(rows, key=lambda r: r[key]):
        g.setdefault(r[key], []).append(r)
    out = [f"### {title}", "",
           "| " + title.split(" per ")[-1].capitalize() + " | Trades | Wins | Losses | Flat | Total pips | Avg MFE | Avg MAE "
           "| Closed by Johnny | Pips without Johnny's closes |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    tot = []
    for k, rs in sorted(g.items(), key=lambda kv: sum(float(r["pips"]) for r in kv[1])):
        out.append(line(k, rs))
        tot += rs
    out.append(line("**All**", tot))
    return "\n".join(out) + "\n"


def line(k, rs):
    p = [float(r["pips"]) for r in rs]
    bot = [float(r["pips"]) for r in rs if r["closed_by"] != "Johnny by hand"]
    mfe = sum(float(r["mfe_pips"]) for r in rs) / len(rs)
    mae = sum(float(r["mae_pips"]) for r in rs) / len(rs)
    return (f"| {k} | {len(rs)} | {sum(x > 0 for x in p)} | {sum(x < 0 for x in p)} | {sum(x == 0 for x in p)} | "
            f"{sum(p):+.1f} | {mfe:.1f} | {mae:.1f} | {len(rs) - len(bot)} | {sum(bot):+.1f} |")


md = table("strategy", "Results per strategy") + "\n" + table("analyser_state_at_open", "Results per analyser state") \
    + "\n" + table("session", "Results per session")
open(D / "summary.md", "w").write(md)
print(md)
