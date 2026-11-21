"""Follow-up (Johnny, 21 Nov): stepped stops. Read-only; uses the same trades, candles and rules as analyse.py.
  d  stop to +5 once +10                                  (repeated as a check: must match analyse.py)
  e  stop to +5 once +10, then stop to +10 once +15        (the ladder)
  f  stop to +10 once +15                                  (second step alone)
Walks each trade's 5-minute candles in order: a candle first tests the stop armed before it, then arms any new step
it reaches. A candle that both arms a step and touches the new stop is counted as not stopped (order unknown) and
noted only when no later candle settles it. A stop touched only in the close candle is counted as hit
(as analyse.py does) and noted. If the trade really closed below an armed stop, price must have passed through it, so the stop is taken.
A step counts as reached only if the bot's live best (or the candles, where no live best) reached it.
Everything else stays as it was live. No slippage on the moved stop.
"""
from pathlib import Path
HERE = Path(__file__).parent
src = (HERE / "analyse.py").read_text().split("def sim")[0]
g = {"__file__": str(HERE / "analyse.py")}
exec(src, g)
out = g["out"]

def ladder(x, steps):
    a = x["actual"]; path = x["_path"]; notes = []
    steps = [s for s in steps if x["best"] >= s[0]]
    if not steps:
        return a, notes
    armed = None; done = set()
    for j, (t, hi, lo) in enumerate(path):
        if armed is not None and lo <= armed:
            if j == len(path) - 1 and a >= armed:
                notes.append(f"stop +{armed:g} touched only in the close candle (may be after the close); counted as hit, as in analyse.py")
            return float(armed), notes
        for trig, stop in steps:
            if trig not in done and hi >= trig:
                done.add(trig)
                if armed is None or stop > armed:
                    armed = stop
                    if lo <= stop and a >= stop and not any(p[2] <= stop for p in path[j + 1:]):
                        notes.append(f"+{trig} and +{stop} in the same candle; order unknown, counted as not hit")
    for trig, stop in steps:  # live best reached it but the candles never showed it
        if trig not in done:
            notes.append(f"+{trig} only in the live best, not the candles")
            armed = stop if armed is None else max(armed, stop)
    if armed is not None and a < armed:
        return float(armed), notes
    return a, notes

EX = {"d": [(10, 5)], "e": [(10, 5), (15, 10)], "f": [(15, 10)]}
bot = [x for x in out if not x["owner"]]
for x in out:
    x["lad"] = {k: ladder(x, v) for k, v in EX.items()}

G = ["emerging trend", "trend slow grind", "trend strong push", "ranging", "possible reversal"]
print("| State | Trades | Actual | d +5 once +10 | e ladder +5@10, +10@15 | f +10 once +15 |")
print("|---|---|---|---|---|---|")
for gname in G + ["all other"]:
    s = [x for x in bot if (x["group"] == gname if gname != "all other" else x["group"] != "emerging trend")]
    print(f"| {gname} | {len(s)} | {sum(x['actual'] for x in s):+.1f} | " + " | ".join(f"{sum(x['lad'][k][0] for x in s):+.1f}" for k in "def") + " |")

em = [x for x in bot if x["group"] == "emerging trend"]
print("\nemerging trend, trades that reached +10")
print("| Opened (UTC) | Strategy | Best | Actual | d +5 once +10 | e ladder | f +10 once +15 | Notes |")
print("|---|---|---|---|---|---|---|---|")
for x in em:
    if x["best"] >= 10:
        L = x["lad"]; notes = sorted({n for k in "def" for n in L[k][1]})
        print(f"| {x['opened'][5:]} | {x['strategy']} | {x['best']:g} | {x['actual']:+.1f} | " + " | ".join(f"{L[k][0]:+.1f}" for k in "def") + f" | {'; '.join(notes)} |")
print(f"| **All 33** | | | **{sum(x['actual'] for x in em):+.1f}** | " + " | ".join(f"**{sum(x['lad'][k][0] for x in em):+.1f}**" for k in "def") + " | |")
for k in "def":
    d = [x["lad"][k][0] - x["actual"] for x in em]
    print(k, "better", sum(v > 0.05 for v in d), "worse", sum(v < -0.05 for v in d), "same", sum(abs(v) <= 0.05 for v in d))
srt = sorted(em, key=lambda x: -x["actual"])
print("without the 50-pip trade:", round(sum(x["actual"] for x in srt[1:]), 1), [round(sum(x["lad"][k][0] for x in srt[1:]), 1) for k in "def"])
for per, lab in (("A", "first build"), ("BCDE", "since 16 Nov")):
    s = [x for x in em if x["period"] in per]
    print(lab, len(s), round(sum(x["actual"] for x in s), 1), [round(sum(x["lad"][k][0] for x in s), 1) for k in "def"])
