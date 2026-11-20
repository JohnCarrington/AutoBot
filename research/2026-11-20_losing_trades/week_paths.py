"""Week 16-20 Nov: what price did after each entry, from the stored 5-minute candles (a buy is judged on the sell
price, as IG closes it; a sell on the buy price). Writes week_paths.csv. The entry candle is counted from its start,
so its part before the fill can only make the first-15-minute numbers look slightly bigger than they were."""
import csv, glob
from datetime import datetime, timedelta
from pathlib import Path
D = Path(__file__).parent
C = {}
for f in sorted(glob.glob("/opt/autobot/data/candles/GBPUSD/5m/2026-11-1[5-9].csv") + glob.glob("/opt/autobot/data/candles/GBPUSD/5m/2026-11-2*.csv")):
    for r in csv.DictReader(open(f)): C[r["start_utc"]] = r
def T(s): return datetime.fromisoformat(s.replace("Z", ""))
def key(t): return (t - timedelta(minutes=t.minute % 5, seconds=t.second, microseconds=t.microsecond)).strftime("%Y-%m-%dT%H:%M:%SZ")
rows = [r for r in csv.DictReader(open(D / "trades.csv")) if r["opened_utc"] >= "2026-11-16"]
out = []
for r in rows:
    buy = r["direction"] == "buy"; e = float(r["ig_open"]); o = T(r["opened_utc"])
    c_end = T(r["closed_utc"]) if r["closed_utc"] != "OPEN" else datetime(2026, 11, 20, 19, 0)
    t = T(key(o)); best = worst = 0.0; best_at = None; f15b = f15w = 0.0
    while t <= c_end:
        k = C.get(t.strftime("%Y-%m-%dT%H:%M:%SZ"))
        if k:
            fav = (float(k["sell_high"]) - e) if buy else (e - float(k["buy_low"]))
            adv = (e - float(k["sell_low"])) if buy else (float(k["buy_high"]) - e)
            if fav > best: best, best_at = fav, t
            worst = max(worst, adv)
            if t < T(key(o)) + timedelta(minutes=15): f15b, f15w = max(f15b, fav), max(f15w, adv)
        t += timedelta(minutes=5)
    mins = int((c_end - o).total_seconds() // 60)
    out.append({**{k: r[k] for k in ("period", "opened_utc", "closed_utc", "strategy", "direction", "ig_open", "ig_stop_distance",
                                     "tp_pips", "close_price_ig", "ig_pips", "how_closed", "closed_by", "market_state", "best_pips")},
                "first15_best": round(f15b, 1), "first15_worst": round(f15w, 1), "best_candle": round(best, 1),
                "best_after_min": int((best_at - o).total_seconds() // 60) if best_at else "", "worst_candle": round(worst, 1), "minutes_open": mins})
with open(D / "week_paths.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
for x in out:
    print(x["opened_utc"][5:16], x["strategy"][:14].ljust(14), x["direction"][0], x["ig_stop_distance"], x["tp_pips"], "|15m +%s/-%s" % (x["first15_best"], x["first15_worst"]),
          "| best", x["best_pips"], "(candle", x["best_candle"], "at", x["best_after_min"], "min) | worst", x["worst_candle"], "|", x["ig_pips"], x["how_closed"], x["minutes_open"], "min |", x["market_state"])
