"""Emerging-trend exit question (Johnny, 21 Nov 2026). Read-only: reads trades.csv from the 20 Nov losing-trades
folder and the stored 5-minute candles; writes trades_paths.csv next to this file and prints the tables.

Prices: a buy is judged on the sell price and a sell on the buy price (the side IG closes it on). "Best" is the bot's
own live best_pips where recorded (tick level, fill to close); the candles are used for timing, for the 7 trades with
no recorded best, and to tell whether price came back after reaching +10. Candles cover the fill candle from its
start and the close candle to its end, so they can show a little price from before the fill / after the close.

What-if exits keep everything else as it was (same entry, same stop, same target, same bot closes and trails):
  a  close all at +10        b  close all at +15
  c  half at +10, stop on the other half to +2      d  stop to +5 once +10
Not counted: slippage on the +2/+5 stop, IG's minimum stop distance, stake differences (results are pips per trade).
"""
import csv, glob
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE.parent / "2026-11-20_losing_trades" / "trades.csv"
C = {}
for f in sorted(glob.glob("/opt/autobot/data/candles/GBPUSD/5m/2026-11-*.csv")):
    for r in csv.DictReader(open(f)):
        C[r["start_utc"]] = r

T = lambda s: datetime.fromisoformat(s.replace("Z", ""))
def floor5(t): return t - timedelta(minutes=t.minute % 5, seconds=t.second, microseconds=t.microsecond)
def group(s):
    for g in ("emerging trend", "slow grind", "strong push", "ranging", "possible reversal", "consolidation"):
        if g in s: return {"slow grind": "trend slow grind", "strong push": "trend strong push"}.get(g, g)
    return s or "?"

rows = list(csv.DictReader(open(SRC)))
out = []
for r in rows:
    if r["closed_utc"] in ("", "OPEN"):
        continue
    buy = r["direction"] == "buy"; e = float(r["ig_open"]); o = T(r["opened_utc"]); c = T(r["closed_utc"])
    path = []  # (candle start, favourable, worst point in the candle as favourable pips i.e. low side)
    t = floor5(o)
    while t <= c:
        k = C.get(t.strftime("%Y-%m-%dT%H:%M:%SZ"))
        if k:
            hi = (float(k["sell_high"]) - e) if buy else (e - float(k["buy_low"]))
            lo = (float(k["sell_low"]) - e) if buy else (e - float(k["buy_high"]))
            path.append((t, round(hi, 1), round(lo, 1)))
        t += timedelta(minutes=5)
    expected = int((floor5(c) - floor5(o)).total_seconds() // 300) + 1
    cbest = max([p[1] for p in path] + [0.0])
    live = r["best_pips"]
    best = float(live) if live != "" else cbest
    tbest = next((p[0] for p in path if p[1] >= cbest), None)
    out.append(dict(
        opened=r["opened_utc"][:16].replace("T", " "), period=r["period"][0], strategy=r["strategy"], dir=r["direction"],
        state=r["market_state"], group=group(r["market_state"]), owner=r["closed_by"] == "owner",
        stop=float(r["ig_stop_distance"]), tp=float(r["tp_pips"]), actual=float(r["ig_pips"]), how=r["how_closed"],
        best_live=live, best_candle=cbest, best=best, mins_open=int((c - o).total_seconds() // 60),
        mins_to_best=max(0, int((tbest - o).total_seconds() // 60)) if tbest else "",
        candles=len(path), candles_expected=expected, mid_fill=(o - floor5(o)).total_seconds() > 30, _path=path))

def sim(x):
    """What-if results for one trade, plus notes on anything the candles cannot settle."""
    a = x["actual"]; path = x["_path"]; notes = []
    res = {}
    for lvl, key in ((10, "a"), (15, "b")):
        res[key] = float(lvl) if x["best"] >= lvl else a
    if x["best"] < 10:
        res["c"] = res["d"] = a
        return res, notes
    i10 = next((i for i, p in enumerate(path) if p[1] >= 10), None)
    if i10 is None:  # live best says +10, candles never show it (side / timing differences)
        i10 = max(range(len(path)), key=lambda i: path[i][1]); notes.append("+10 only in the live best, not the candles")
    if i10 == 0 and x["mid_fill"]:
        notes.append("+10 first seen in the fill candle (part of it before the fill)")
    for lvl, key, banked in ((2, "c", 0.5 * 10), (5, "d", 0.0)):
        later = any(p[2] <= lvl for p in path[i10 + 1:])
        same = path[i10][2] <= lvl
        if a < lvl:
            back = True  # it closed below the level after being +10, so it passed through it
        elif later:
            back = True
            if path[i10 + 1:] and all(p[2] > lvl for p in path[i10 + 1:-1]) and path[-1][2] <= lvl:
                notes.append(f"back to +{lvl} only in the close candle (may be after the close)")
        else:
            back = False
            if same:
                notes.append(f"+10 and +{lvl} in the same candle; order unknown, counted as not back")
        rest = float(lvl) if back else a
        res[key] = round(banked + (0.5 * rest if key == "c" else rest), 2)
    return res, notes

for x in out:
    x["sim"], x["notes"] = sim(x)

with open(HERE / "trades_paths.csv", "w", newline="") as fh:
    cols = ["opened", "period", "strategy", "dir", "state", "group", "owner", "how", "stop", "tp", "actual", "best_live",
            "best_candle", "best", "mins_to_best", "mins_open", "candles", "candles_expected", "mid_fill"]
    w = csv.writer(fh); w.writerow(cols + ["exit_a_10", "exit_b_15", "exit_c_half10_be2", "exit_d_be5", "notes"])
    for x in out:
        w.writerow([x[k] for k in cols] + [x["sim"][k] for k in "abcd"] + ["; ".join(x["notes"])])

# ---------- summaries ----------
G = ["emerging trend", "trend slow grind", "trend strong push", "ranging", "possible reversal", "consolidation"]
bot = [x for x in out if not x["owner"]]
print(f"closed trades {len(out)}, closed by the bot/IG {len(bot)}, by Johnny {len(out) - len(bot)}, missing candles:",
      [(x['opened'], x['candles'], x['candles_expected']) for x in out if x['candles'] != x['candles_expected']])
print("live best < 10 but candle >= 10:", [(x['opened'], x['best_live'], x['best_candle']) for x in out if x['best_live'] != '' and float(x['best_live']) < 10 <= x['best_candle']])
print("live best >= 10 but candle < 10:", [(x['opened'], x['best_live'], x['best_candle']) for x in out if x['best_live'] != '' and x['best_candle'] < 10 <= float(x['best_live'])])

def med(v):
    v = sorted(v); n = len(v)
    return "" if not n else (v[n // 2] if n % 2 else round((v[n // 2 - 1] + v[n // 2]) / 2, 1))

print("\n| State at entry | Trades | Won | Actual pips | Never +3 (straight against) | Reached +5 | +10 | +15 | +20 | +30 | Median best | Median minutes to best (all) | Median minutes to best (reached +10) |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for g in G:
    s = [x for x in bot if x["group"] == g]
    if not s:
        print(f"| {g} | 0 | | | | | | | | | | | |"); continue
    n = len(s); f = lambda lv: f"{sum(x['best'] >= lv for x in s)} ({100 * sum(x['best'] >= lv for x in s) // n}%)"
    print(f"| {g} | {n} | {sum(x['actual'] > 0 for x in s)} | {sum(x['actual'] for x in s):+.1f} | "
          f"{sum(x['best'] < 3 for x in s)} ({100 * sum(x['best'] < 3 for x in s) // n}%) | {f(5)} | {f(10)} | {f(15)} | {f(20)} | {f(30)} | "
          f"{med([x['best'] for x in s])} | {med([x['mins_to_best'] for x in s if x['mins_to_best'] != ''])} | "
          f"{med([x['mins_to_best'] for x in s if x['best'] >= 10 and x['mins_to_best'] != ''])} |")
alln = [x for x in bot if x["group"] != "emerging trend"]
print(f"| all other states | {len(alln)} | {sum(x['actual'] > 0 for x in alln)} | {sum(x['actual'] for x in alln):+.1f} | "
      f"{sum(x['best'] < 3 for x in alln)} ({100 * sum(x['best'] < 3 for x in alln) // len(alln)}%) | " +
      " | ".join(f"{sum(x['best'] >= lv for x in alln)} ({100 * sum(x['best'] >= lv for x in alln) // len(alln)}%)" for lv in (5, 10, 15, 20, 30)) +
      f" | {med([x['best'] for x in alln])} | {med([x['mins_to_best'] for x in alln if x['mins_to_best'] != ''])} | "
      f"{med([x['mins_to_best'] for x in alln if x['best'] >= 10 and x['mins_to_best'] != ''])} |")

print("\nfade: reached +10, then closed at or below 0 / below +5")
for g in G + ["all other"]:
    s = [x for x in bot if (x["group"] == g if g != "all other" else x["group"] != "emerging trend") and x["best"] >= 10]
    if s: print(f"| {g} | {len(s)} | {sum(x['actual'] <= 0 for x in s)} | {sum(x['actual'] < 5 for x in s)} | {med([x['best'] for x in s])} |")

print("\nwhat-if totals by group (pips, closed by bot/IG only)")
for g in G + ["all other"]:
    s = [x for x in bot if (x["group"] == g if g != "all other" else x["group"] != "emerging trend")]
    if s: print(f"| {g} | {len(s)} | {sum(x['actual'] for x in s):+.1f} | " + " | ".join(f"{sum(x['sim'][k] for x in s):+.1f}" for k in "abcd") + " |")

print("\nemerging trend, trade by trade")
print("| Opened (UTC) | Ver | Strategy | Dir | Stop / target | Best (live) | Min to best | How it closed | Actual | a +10 | b +15 | c half +10, rest +2 | d +5 once +10 | Notes |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
em = [x for x in bot if x["group"] == "emerging trend"]
for x in em:
    s = x["sim"]
    print(f"| {x['opened'][5:]} | {x['period']} | {x['strategy']} | {x['dir']} | {x['stop']:g} / {x['tp']:g} | {x['best']:g}{'' if x['best_live'] != '' else ' (candles)'} | "
          f"{x['mins_to_best']} | {x['how']} | {x['actual']:+.1f} | {s['a']:+.1f} | {s['b']:+.1f} | {s['c']:+.1f} | {s['d']:+.1f} | {'; '.join(x['notes'])} |")
tot = lambda k: sum(x["sim"][k] for x in em)
print(f"| **Total ({len(em)} trades)** | | | | | | | | **{sum(x['actual'] for x in em):+.1f}** | **{tot('a'):+.1f}** | **{tot('b'):+.1f}** | **{tot('c'):+.1f}** | **{tot('d'):+.1f}** | |")
for k in "abcd":
    d = [x["sim"][k] - x["actual"] for x in em]
    print(k, "better", sum(v > 0.05 for v in d), "worse", sum(v < -0.05 for v in d), "same", sum(abs(v) <= 0.05 for v in d))
# split by period and by strategy for emerging
for key in ("period", "strategy"):
    print(f"\nemerging by {key}")
    for v in sorted({x[key] for x in em}):
        s = [x for x in em if x[key] == v]
        print(f"| {v} | {len(s)} | {sum(x['actual'] for x in s):+.1f} | " + " | ".join(f"{sum(x['sim'][k] for x in s):+.1f}" for k in "abcd") + " |")
# without the two biggest winners
srt = sorted(em, key=lambda x: -x["actual"])
print("\nemerging excluding top trade by actual:", srt[0]["opened"], srt[0]["actual"], "| actual", round(sum(x['actual'] for x in srt[1:]), 1), [round(sum(x['sim'][k] for x in srt[1:]), 1) for k in "abcd"])
print("\nJohnny-closed emerging trades (not in totals)")
for x in out:
    if x["owner"] and x["group"] == "emerging trend":
        print(f"| {x['opened'][5:]} | {x['strategy']} | {x['dir']} | best {x['best']:g} | {x['actual']:+.1f} | " + " ".join(f"{k}={x['sim'][k]:+.1f}" for k in "abcd") + f" | {'; '.join(x['notes'])}")
print("\nJohnny-closed by group:", {g: sum(1 for x in out if x['owner'] and x['group'] == g) for g in G})
