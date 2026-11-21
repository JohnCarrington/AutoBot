"""A trend-day measure in trader's terms (Claude's reading of Johnny's definition), on the hourly chart, chart (sell)
price, Bollinger (20, 2) with the bot's own indicator code, hourly candles starting 06:00 to 20:00 UK (the trading
hours 06:00-20:30):
  * an hour WORKS THE BAND (up) if its candle touches the upper hourly band or closes in the top quarter of the band
    (down: the mirror);
  * an hour TOUCHES THE OTHER BAND (up) if its low reaches the lower hourly band;
  * the MOVE (up) is the biggest rise in the session from a low to a later high (down: the mirror).
A trend day, in the direction with more band hours:
  1. RUN: at least MIN_RUN (8) of the 15 session hours in a row work the band;
  2. no hour in that run touches the other band;
  3. MOVE IN THE RUN: from the run's first open to its furthest point its way, at least MIN_RUN_MOVE (40) pips."""
import sys, pickle
from collections import defaultdict
from datetime import date, time
from zoneinfo import ZoneInfo
sys.path.insert(0, "/home/autobot/worktrees/autobot-sg-trend-day")
from prices.indicators import bollinger
from prices.model import parse_iso
from prices.store import CandleStore
UK = ZoneInfo("Europe/London")
MIN_RUN, MIN_RUN_MOVE = 8, 40
st = CandleStore("/opt/autobot/data/research/stp_validation_store/GBPUSD", 999999)
H = st.read_range("1h", parse_iso("2023-12-20T00:00:00Z"), parse_iso("2026-11-20T00:00:00Z"))
bb = bollinger(H, "sell", 20, 2)
by = defaultdict(list)
for c in H:
    u = c.start.astimezone(UK)
    if u.weekday() < 5 and 6 <= u.hour <= 20 and c.start in bb: by[u.date()].append(c)
def day_facts(v):
    f = {}
    for s, name in ((1, "up"), (-1, "down")):
        work = other = 0
        for c in v:
            b = bb[c.start]; up, lo = float(b.upper), float(b.lower); hi, low, cl = float(c.sell_high), float(c.sell_low), float(c.sell_close)
            pos = (cl - lo) / (up - lo) if up > lo else 0.5
            if s > 0: work += hi >= up or pos >= 0.75; other += low <= lo
            else: work += low <= lo or pos <= 0.25; other += hi >= up
        best, ext = 0.0, None
        for c in v:
            hi, low = float(c.sell_high), float(c.sell_low)
            if s > 0:
                ext = low if ext is None else min(ext, low); best = max(best, hi - ext)
            else:
                ext = hi if ext is None else max(ext, hi); best = max(best, ext - low)
        # the longest unbroken run of band hours, and the move made inside it (from the run's first open to its
        # furthest point its way)
        flags = []
        for c in v:
            b = bb[c.start]; up, lo = float(b.upper), float(b.lower); hi, low, cl = float(c.sell_high), float(c.sell_low), float(c.sell_close)
            pos = (cl - lo) / (up - lo) if up > lo else 0.5
            flags.append((hi >= up or pos >= 0.75) if s > 0 else (low <= lo or pos <= 0.25))
        run = rmove = rother = 0; rstart = None; k = 0
        while k < len(v):
            if not flags[k]: k += 1; continue
            j = k
            while j + 1 < len(v) and flags[j + 1]: j += 1
            seg = v[k:j + 1]; o = float(seg[0].sell_open)
            mv = (max(float(c.sell_high) for c in seg) - o) if s > 0 else (o - min(float(c.sell_low) for c in seg))
            oth = sum(1 for c in seg if ((float(c.sell_low) <= float(bb[c.start].lower)) if s > 0 else (float(c.sell_high) >= float(bb[c.start].upper))))
            if j - k + 1 > run or (j - k + 1 == run and mv > rmove): run, rmove, rother, rstart = j - k + 1, mv, oth, seg[0].start.astimezone(UK).hour
            k = j + 1
        f[name] = dict(work=work, other=other, move=round(best, 1), run=run, run_move=round(rmove, 1), run_other=rother, run_start=rstart)
    d = "up" if f["up"]["work"] >= f["down"]["work"] else "down"
    x = f[d]
    parts = dict(run=x["run"] >= MIN_RUN, other_band_in_run=x["run_other"] == 0, move_in_run=x["run_move"] >= MIN_RUN_MOVE)
    return dict(dir=d, hours_n=len(v), **{k: x[k] for k in ("work", "other", "move", "run", "run_move", "run_other", "run_start")}, parts=parts, trend=all(parts.values()))
DAYS = {d: day_facts(v) for d, v in sorted(by.items()) if len(v) >= 14 and date(2024, 1, 8) <= d <= date(2026, 11, 19)}
if __name__ == "__main__":
    known = {date(2026, 10, 5): "up", date(2026, 11, 9): "up", date(2026, 11, 11): "down", date(2026, 11, 12): "down", date(2026, 11, 18): "down", date(2026, 10, 6): "(6 Oct, for comparison)"}
    for d, w in known.items(): print(d, "Johnny:", w, "| measure:", DAYS[d])
    n = len(DAYS); t = [d for d, x in DAYS.items() if x["trend"]]
    print(f"\n{len(t)} trend days of {n} weekdays ({100*len(t)/n:.1f}%): up {sum(DAYS[d]['dir']=='up' for d in t)}, down {sum(DAYS[d]['dir']=='down' for d in t)}")
    pickle.dump(DAYS, open("trenddays.pkl", "wb"))
