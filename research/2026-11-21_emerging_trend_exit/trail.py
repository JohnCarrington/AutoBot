"""Follow-up 2 (Johnny, 21 Nov): stop to +5 once +10, then a trailing stop. Read-only; same trades, candles and rules
as analyse.py / ladder.py.
  g1 / g2 / g3  the stop trails 5 / 8 / 10 pips behind the best price so far
  g4            after each finished 5-minute candle, a tenth of a pip beyond the last 3 finished candles (a buy: below
                their lowest sell price; a sell: above their highest buy price), the bounce's existing rule
                (trade_manager/manager.py _trail)
  g5            after each finished 5-minute candle, at the 5-minute 8 EMA (sell-price closes, as the bot's chart and
                indicators use, prices/indicators.py ema); if the candle already closed beyond the EMA, the trade is
                taken as closed at that candle's close (IG would not take a stop beyond the price)
  e             the ladder from ladder.py, rerun here as a check (must give -28.6)
In every case the stop goes to +5 once the trade is +10, never moves backwards and never goes below +5.
Candle order, as before: a candle first tests the stop set before it, then moves the stop. A stop touched only in
the trade's closing candle counts as hit. If the trade really closed below the stop, price passed through it, so
the stop is taken. Everything else stays as it was live (same target, same bot closes). No slippage.

g1-g3 move inside a candle (live they follow every tick), so a candle that makes a new best and then falls back
through the new stop cannot be ordered. The main figures count it as not hit; the "worst order" figures count it as
hit at the new stop.
"""
import glob, csv
from datetime import timedelta
from pathlib import Path

HERE = Path(__file__).parent
src = (HERE / "analyse.py").read_text().split("def sim")[0]
g = {"__file__": str(HERE / "analyse.py")}
exec(src, g)
out, C = g["out"], g["C"]

# 8 EMA on sell closes over every stored 5-minute candle, in time order (prices/indicators.py _ema_values)
keys = sorted(C)
EMA, k, e, closes = {}, 2 / 9, None, []
for key in keys:
    c = float(C[key]["sell_close"]); closes.append(c)
    if e is None:
        if len(closes) == 8: e = sum(closes) / 8
    else:
        e = e + (c - e) * k
    if e is not None: EMA[key] = e
IDX = {key: i for i, key in enumerate(keys)}
fmt = lambda t: t.strftime("%Y-%m-%dT%H:%M:%SZ")

def run(x, mode, worst=False):
    a = x["actual"]
    if x["best"] < 10:
        return a, []
    buy = x["dir"] == "buy"; entry = float(next(r for r in g["rows"] if r["opened_utc"][:16].replace("T", " ") == x["opened"]
                                                and r["strategy"] == x["strategy"])["ig_open"])
    path = x["_path"]; stop = None; best = None; notes = []
    for j, (t, hi, lo) in enumerate(path):
        last = j == len(path) - 1
        if stop is not None and lo <= stop:
            if last and a >= stop:
                notes.append(f"stop +{stop:.1f} touched only in the close candle; counted as hit")
            return round(stop, 1), notes
        before = stop
        if stop is None and hi >= 10:
            stop, best = 5.0, hi
        if stop is None:
            continue
        best = max(best, hi)
        if mode in ("g1", "g2", "g3"):
            stop = max(stop, best - {"g1": 5, "g2": 8, "g3": 10}[mode])
        elif mode == "e":
            stop = max(stop, 10.0 if best >= 15 else 5.0)
        # same-candle cases: the stop rose in this candle and the candle also reached it
        if lo <= stop and (before is None or stop > before):
            if worst and not last:
                return round(stop, 1), notes + ["worst order: hit in the candle that moved it"]
        key = fmt(t)
        if mode == "g4":
            i = IDX[key]; prev = [C[keys[n]] for n in range(i - 2, i + 1)]
            want = (min(float(p["sell_low"]) for p in prev) - 0.1 - entry) if buy else (entry - (max(float(p["buy_high"]) for p in prev) + 0.1))
            stop = max(stop, round(want, 1))
        elif mode == "g5":
            want = (EMA[key] - entry) if buy else (entry - EMA[key])
            close_fav = (float(C[key]["sell_close"]) - entry) if buy else (entry - float(C[key]["buy_close"]))
            if want > stop:
                if want >= close_fav and not last:
                    notes.append("closed beyond the 8 EMA: out at the candle close")
                    return round(close_fav, 1), notes
                stop = want
    if stop is not None and a < stop:
        return round(stop, 1), notes
    return a, notes

MODES = ["e", "g1", "g2", "g3", "g4", "g5"]
NAMES = {"e": "e ladder", "g1": "g1 5 behind", "g2": "g2 8 behind", "g3": "g3 10 behind", "g4": "g4 last 3 candles", "g5": "g5 8 EMA"}
bot = [x for x in out if not x["owner"]]
for x in bot:
    x["tr"] = {m: run(x, m) for m in MODES}
    x["trw"] = {m: run(x, m, worst=True) for m in MODES}
em = [x for x in bot if x["group"] == "emerging trend"]
srt = sorted(em, key=lambda x: -x["actual"])
sets = [("Emerging trend, all 33", em), ("without the 50-pip winner (32)", srt[1:]),
        ("9-13 Nov (16)", [x for x in em if x["period"] == "A"]), ("since 16 Nov (17)", [x for x in em if x["period"] != "A"]),
        ("all other states (59)", [x for x in bot if x["group"] != "emerging trend"])]
S = lambda s, m, w=False: sum((x["trw"] if w else x["tr"])[m][0] for x in s)
print("| Trades | Actual | " + " | ".join(NAMES[m] for m in MODES) + " |")
print("|---|---|" + "---|" * len(MODES))
for name, s in sets:
    print(f"| {name} | {sum(x['actual'] for x in s):+.1f} | " + " | ".join(f"{S(s, m):+.1f}" for m in MODES) + " |")
print("\nworst order inside a candle:")
for name, s in sets:
    print(f"| {name} | {sum(x['actual'] for x in s):+.1f} | " + " | ".join(f"{S(s, m, True):+.1f}" for m in MODES) + " |")
print("\nemerging trend, the 14 trades that reached +10")
print("| Opened (UTC) | Strategy | Best | Actual | " + " | ".join(NAMES[m] for m in MODES) + " |")
print("|---|---|---|---|" + "---|" * len(MODES))
for x in em:
    if x["best"] >= 10:
        print(f"| {x['opened'][5:]} | {x['strategy']} | {x['best']:g} | {x['actual']:+.1f} | " +
              " | ".join(f"{x['tr'][m][0]:+.1f}" + (f" ({x['trw'][m][0]:+.1f})" if abs(x['trw'][m][0] - x['tr'][m][0]) > 0.05 else "") for m in MODES) + " |")
print("\nnotes:")
for x in em:
    for m in MODES:
        for n in x["tr"][m][1]:
            print(x["opened"][5:], x["strategy"], m, n)
for m in MODES:
    d = [x["tr"][m][0] - x["actual"] for x in em]
    print(m, "better", sum(v > 0.05 for v in d), "worse", sum(v < -0.05 for v in d), "same", sum(abs(v) <= 0.05 for v in d))
