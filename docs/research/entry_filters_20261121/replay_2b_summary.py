"""Summarise a rule 1 + 2b + trend day replay against the all-off replay.

Usage: python replay_2b_summary.py replay2b_9_13_nov   (reads _2b.json and _off.json)

For each refusal it looks up the trade the all-off replay took at that time
(same strategy, direction, open time) and shows its result.  Code check only:
replay totals are not a verdict (the live demo is the judge).
"""
import collections, json, sys
from datetime import datetime
from zoneinfo import ZoneInfo

UK = ZoneInfo("Europe/London")


def uk(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(UK)


def main(stem, days=()):
    on = json.load(open(f"{stem}_2b.json"))
    off = json.load(open(f"{stem}_off.json"))
    out = [f"## {stem}", ""]
    out.append("Trend days (replay):")
    for t in on["trend_days"]:
        if t["kind"] == "trend day started":
            out.append(f"- {uk(t['time_utc']):%a %d %b %H:%M} {t['direction']} (slow grind opened "
                       f"{uk(t['slow_grind_opened_utc']):%H:%M} at {t['slow_grind_fill']}, "
                       f"{t['pips_in_profit']} pips in profit)")
        else:
            out.append(f"- {uk(t['time_utc']):%a %d %b %H:%M} CANCELLED")
    if not on["trend_days"]:
        out.append("- none")
    offt = {(t["strategy"], t["direction"], uk(t["time_utc"])): t for t in off["trades"]}
    out += ["", "Every refusal, with the trade the all-off replay took at that time:", ""]
    out.append("| UK time | strategy | dir | rule | RSI 3 | trend day | all-off trade |")
    out.append("|---|---|---|---|---|---|---|")
    per = collections.defaultdict(lambda: [0, 0, 0.0, 0.0])
    for r in on["refused"]:
        t = uk(r["time_utc"])
        if days and t.strftime("%d") not in days:
            continue
        d = r.get("details") or {}
        m = offt.get((r["strategy"], r["direction"], t))
        res = m["pips"] if m else "no trade"
        if m:
            p = per[(r["strategy"], r["rule"])]
            p[0] += 1
            v = float(m["pips"])
            p[2 if v < 0 else 3] += abs(v)
        per[(r["strategy"], r["rule"])][1] += 1
        out.append(f"| {t:%a %d %H:%M} | {r['strategy']} | {r['direction']} | {r['rule']} | "
                   f"{d.get('rsi3_5m', '')} | {d.get('trend_day') or ''} | {res} |")
    out += ["", "| strategy | rule | refusals | matched off-trades | losses avoided | wins given up | net |",
            "|---|---|---|---|---|---|---|"]
    for (s, rule), (n, k, saved, cost) in sorted(per.items()):
        out.append(f"| {s} | {rule} | {k} | {n} | {saved:.1f} | {cost:.1f} | {saved - cost:+.1f} |")
    ta = collections.defaultdict(lambda: [0, 0.0])
    tb = collections.defaultdict(lambda: [0, 0.0])
    for t in on["trades"]:
        ta[t["strategy"]][0] += 1; ta[t["strategy"]][1] += float(t["pips"])
    for t in off["trades"]:
        tb[t["strategy"]][0] += 1; tb[t["strategy"]][1] += float(t["pips"])
    out += ["", "| strategy | trades on | pips on | trades off | pips off |", "|---|---|---|---|---|"]
    for s in sorted(set(ta) | set(tb)):
        out.append(f"| {s} | {ta[s][0]} | {ta[s][1]:+.1f} | {tb[s][0]} | {tb[s][1]:+.1f} |")
    out.append(f"| all | {len(on['trades'])} | {sum(v[1] for v in ta.values()):+.1f} | "
               f"{len(off['trades'])} | {sum(v[1] for v in tb.values()):+.1f} |")
    return "\n".join(out)


if __name__ == "__main__":
    print(main(sys.argv[1], tuple(sys.argv[2:])))
