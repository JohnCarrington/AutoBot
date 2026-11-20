"""Step 2: per strategy and version period, from trades.csv (IG pips). Bot exits and owner closes apart."""
import csv, collections, sys
from pathlib import Path
rows = list(csv.DictReader(open(Path(__file__).parent / "trades.csv")))
def pips(r):
    return float(r["ig_pips"]) if r["ig_pips"] != "" else (float(r["bot_pips"]) if r["bot_pips"] else None)
def table(sel, title):
    print(f"\n### {title}\n")
    print("| Period | Strategy | Trades | Wins | Losses | Flat | Total pips | Avg win | Avg loss |")
    print("|---|---|---|---|---|---|---|---|---|")
    g = collections.defaultdict(list)
    for r in sel:
        p = pips(r)
        if p is None: continue
        g[(r["period"], r["strategy"])].append(p)
    tot = collections.defaultdict(list)
    for (per, st), v in sorted(g.items()):
        w = [x for x in v if x > 0]; l = [x for x in v if x < 0]
        print(f"| {per} | {st} | {len(v)} | {len(w)} | {len(l)} | {len(v)-len(w)-len(l)} | {sum(v):+.1f} | "
              f"{(sum(w)/len(w)) if w else 0:+.1f} | {(sum(l)/len(l)) if l else 0:+.1f} |")
        tot[per] += v
    for per, v in sorted(tot.items()):
        w = [x for x in v if x > 0]; l = [x for x in v if x < 0]
        print(f"| **{per}** | **all** | **{len(v)}** | **{len(w)}** | **{len(l)}** | **{len(v)-len(w)-len(l)}** | **{sum(v):+.1f}** | "
              f"**{(sum(w)/len(w)) if w else 0:+.1f}** | **{(sum(l)/len(l)) if l else 0:+.1f}** |")
closed = [r for r in rows if r["closed_utc"] != "OPEN"]
table([r for r in closed if r["closed_by"] != "owner"], "Bot's own exits (IG stop, IG limit, the bot's closes)")
table([r for r in closed if r["closed_by"] == "owner"], "Johnny's hand closes (not the bot's result)")
print("\n### Whole period, bot exits, by strategy\n")
print("| Strategy | Trades | Wins | Losses | Total pips | £ at £10/pip |")
print("|---|---|---|---|---|---|")
g = collections.defaultdict(list)
for r in closed:
    if r["closed_by"] != "owner" and pips(r) is not None: g[r["strategy"]].append(pips(r))
for st, v in sorted(g.items(), key=lambda kv: sum(kv[1])):
    print(f"| {st} | {len(v)} | {len([x for x in v if x>0])} | {len([x for x in v if x<0])} | {sum(v):+.1f} | {sum(v)*10:+.0f} |")
