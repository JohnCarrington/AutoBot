"""Step 1 tables (markdown) and the overlap check, from trades.csv."""
import csv
from datetime import datetime
from pathlib import Path
rows = list(csv.DictReader(open(Path(__file__).parent / "trades.csv")))
def who(r):
    if r["closed_utc"] == "OPEN": return "still open"
    if r["closed_by"] == "owner": return "Johnny by hand"
    h = r["how_closed"]
    return {"stopped by IG": "IG stop", "take profit hit at IG": "IG limit", "close": "bot",
            "forced close": "bot (forced)", "closed at IG": "IG (stop)"}.get(h, h)
def sh(t): return t[5:16].replace("T", " ") if t and t != "OPEN" else t
def table(sel, with_ver):
    hdr = ["Opened UTC", "Closed UTC", "Strategy", "Dir", "Entry (IG fill)", "Rule stop pips", "Stop sent", "IG stop level (dist)",
           "TP pips (IG limit)", "Close (IG)", "IG pips", "How closed", "Who"]
    if with_ver: hdr = ["Code"] + hdr
    out = ["| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    for r in sel:
        cp = f"{float(r['close_price_ig']):.1f}" if r["close_price_ig"] else (r["close_price_bot"] or "")
        cells = [sh(r["opened_utc"]), sh(r["closed_utc"]), r["strategy"], r["direction"], str(r["ig_open"]),
                 r["rule_stop_pips"], r["sent_stop_distance"],
                 f"{r['ig_stop_level']} ({r['ig_stop_distance']})" if r["ig_stop_level"] else "(IG read pending)",
                 f"{r['tp_pips']} ({r['ig_limit_level']})", cp, r["ig_pips"] or r["bot_pips"], r["how_closed"], who(r)]
        if with_ver: cells = [r["commit"]] + cells
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)
E = [r for r in rows if r["period"].startswith("E")]
O = [r for r in rows if not r["period"].startswith("E")]
print("## E\n"); print(table(E, False))
print("\n## OLDER\n")
cur = None
for r in O:
    if r["period"] != cur:
        cur = r["period"]
        print(f"\n#### {cur}\n")
        print(table([x for x in O if x["period"] == cur], True))
print("\n## OVERLAPS\n")
def T(s): return datetime.fromisoformat(s.replace("Z", ""))
for i, a in enumerate(rows):
    for b in rows[i+1:]:
        if b["opened_utc"] >= (a["closed_utc"] if a["closed_utc"] != "OPEN" else "9999"): continue
        kind = "SAME STRATEGY" if a["strategy"] == b["strategy"] else ("OPPOSITE" if a["direction"] != b["direction"] else None)
        if kind: print(kind, a["period"][0], sh(a["opened_utc"]), a["strategy"], a["direction"], "|", sh(b["opened_utc"]), b["strategy"], b["direction"])
