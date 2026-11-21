"""Examples for Johnny's chart, the known days, and checks (final measure: trendday.py)."""
import pickle, random, csv
from datetime import date
S = pickle.load(open("step2.pkl", "rb")); TD = pickle.load(open("trenddays.pkl", "rb"))
trend, sig, best, days, out = S["trend"], S["sig0"], S["best"], S["days"], S["out"]
f = lambda d: f"{d:%a %d %b %Y}"
bb = lambda v: "-" if v is None else f"{v:+.1f}"
def desc(d):
    x = TD[d]; b = best[d]
    tr = f"trend {x['dir']}: {x['run']} band hours in a row from {x['run_start']:02d}:00, {x['run_move']} pips in the run" if x["trend"] else \
         f"not a trend day (best: {x['dir']}, {x['run']} band hours in a row, {x['run_move']} pips in the run, other band in run {x['run_other']})"
    return f"{f(d)}: {tr} | signal {sig[d]} (best buy {bb(b['buy'])}, best sell {bb(b['sell'])})"
print("Johnny's days:")
for d in (date(2026,10,5), date(2026,10,6), date(2026,11,9), date(2026,11,11), date(2026,11,12), date(2026,11,18)): print("  ", desc(d))
rnd = random.Random(20261121)
print("\n10 trend days at random (seed 20261121):")
for d in sorted(rnd.sample(sorted(trend), 10)): print("  ", desc(d))
L = out[0]["lists"]
for lab, key, n in (("misses, no signal", "miss_none", 6), ("misses, signal the wrong way", "miss_opp", 6), ("false alarms, signal on but not a trend day", "not_trend", 6)):
    print(f"\n{lab} ({len(L[key])} in all), {n} at random:")
    for d in sorted(rnd.sample(L[key], min(n, len(L[key])))): print("  ", desc(d))
print("\nOct-Nov 2026, every signal day and every trend day (for Johnny's recent charts):")
for d in days:
    if d >= date(2026, 10, 1) and (d in trend or sig[d] in ("up", "down")): print("  ", desc(d))
# overlap: the catch when the trend run starts at 09:00 or later (after the signal's window)
caught = L["caught"]; late = [d for d in trend if TD[d]["run_start"] >= 9]
print(f"\ncaught trend days whose run started before 09:00: {sum(TD[d]['run_start'] < 9 for d in caught)} of {len(caught)}")
print(f"trend days whose run started at 09:00 or later: {len(late)}; caught {sum(sig[d] == trend[d] for d in late)} ({100*sum(sig[d] == trend[d] for d in late)/len(late):.0f}%), wrong way {sum(sig[d] in ('up','down') and sig[d] != trend[d] for d in late)}, no signal {sum(sig[d] == 'none' for d in late)}")
on = [d for d in days if sig[d] in ("up", "down")]
print(f"chance: with {len(trend)} trend days of {len(days)} ({100*len(trend)/len(days):.0f}%), a signal with no link would hit a trend day its way on about half of that: {50*len(trend)/len(days):.0f}% of signal days; it hit {100*out[0]['right']/out[0]['on']:.0f}%")
for lab, ok in (("stricter: 10+ band hours in a row, 50+ pips in the run", lambda x: x["run"] >= 10 and x["run_other"] == 0 and x["run_move"] >= 50),
                ("looser: 6+ band hours in a row, 40+ pips in the run", lambda x: x["run"] >= 6 and x["run_other"] == 0 and x["run_move"] >= 40)):
    tr = {d: TD[d]["dir"] for d in days if ok(TD[d])}
    right = sum(1 for d in on if tr.get(d) == sig[d]); caught_ = sum(1 for d in tr if sig[d] == tr[d])
    print(f"{lab}: {len(tr)} trend days | signal on {len(on)}: trend day its way {right} ({100*right/len(on):.0f}%) | caught {caught_} of {len(tr)} ({100*caught_/len(tr):.0f}%)")
with open("days_trend_measure.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["day", "trend_day", "direction", "band_hours_in_a_row", "run_starts_uk", "pips_in_run", "other_band_hours_in_run", "signal", "best_buy_0609", "best_sell_0609"])
    for d in days:
        x = TD[d]; b = best[d]
        w.writerow([d, x["trend"], x["dir"], x["run"], f"{x['run_start']:02d}:00" if x["run_start"] is not None else "", x["run_move"], x["run_other"], sig[d],
                    "" if b["buy"] is None else round(b["buy"], 1), "" if b["sell"] is None else round(b["sell"], 1)])
