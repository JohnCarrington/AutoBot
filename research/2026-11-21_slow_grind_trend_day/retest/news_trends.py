"""Johnny's idea (22-23 Nov 2026): trends that start after 09:00 UK are news-driven. Read-only research.

Trend days: the re-test's measure (retest/trendday.py, unchanged: 8+ session hours in a row working one hourly band,
no other-band touch in the run, 40+ pips in the run). Its cut-offs were set on 9, 11, 12 and 18 Nov; 6 Oct (Johnny's
known up day in place of 5 Oct) also passes them, so nothing is changed. "Run start" is the UK hour of the run's
first hourly candle.

News: the bot's own table (config/news_table.toml through news.table.classify, as the live bot reads it: only
Finnhub high-impact releases are matched; BIG / MEDIUM / SMALL) on Finnhub's past calendar
(data/research/news/finnhub_calendar.json, fetched 10 Nov 2026). From 1 Nov 2026 the bot's own calendar
(data/news/calendar.json) is used instead, because the past file has no actual figures after 10 Nov. GBP and USD only.

Direction of a release (question 3): ACTUAL against FORECAST. Higher is good for the currency, except the bot's
news.lower_is_better names. Good for GBP or bad for USD -> GBPUSD up; the reverse -> down. Releases at the same
minute: if they agree, that; if not, the bot's [[headline]] order decides (the top-ranked releases must agree).
A release with no actual or no forecast has no reading; actual = forecast is "in line".

Usage: python news_trends.py OUTDIR
"""
import csv, json, sys
from collections import Counter, defaultdict
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from statistics import median
from zoneinfo import ZoneInfo

sys.path.insert(0, "/home/autobot/worktrees/autobot-sg-trend-day")
sys.path.insert(0, str(Path(__file__).parent))
from config.settings_loader import load_settings
from news.table import BIG, MEDIUM, classify, headline_rank, load_headline, load_table
from trendday import DAYS

UK, UTC = ZoneInfo("Europe/London"), timezone.utc
OUT = Path(sys.argv[1])
s = load_settings()
ROWS, HEAD = load_table(), load_headline()
LOWER = [k.lower() for k in s.news.lower_is_better]
past = json.load(open("/opt/autobot/data/research/news/finnhub_calendar.json"))["events"]
live = json.load(open("/opt/autobot/data/news/calendar.json"))["events"]
SWITCH = "2026-11-01"
cal = [e for e in past if e["time_utc"] < SWITCH] + [e for e in live if e["time_utc"] >= SWITCH]


def cur_of(e):
    return s.news.country_currencies.get(e["country"].upper())


def num(x):
    try:
        return None if x is None or isinstance(x, bool) else Decimal(str(x))
    except Exception:
        return None


same_day = defaultdict(list)
for e in cal:
    same_day[(e["time_utc"][:10], cur_of(e))].append(e["event"])

REL = []  # GBP/USD big and medium releases
for e in cal:
    c = cur_of(e)
    if c not in ("GBP", "USD"):
        continue
    m = classify(ROWS, s, c, e["event"], e.get("impact"), same_day[(e["time_utc"][:10], c)])
    if m.tier not in (BIG, MEDIUM):
        continue
    t = datetime.strptime(e["time_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC).astimezone(UK)
    a, f = num(e.get("actual")), num(e.get("estimate"))
    if a is None or f is None:
        d = None
    elif a == f:
        d = "in line"
    else:
        good = (a < f) if any(k in e["event"].lower() for k in LOWER) else (a > f)
        d = ("up" if good else "down") if c == "GBP" else ("down" if good else "up")
    REL.append(dict(t=t, cur=c, event=e["event"], tier=m.tier, actual=e.get("actual"), forecast=e.get("estimate"),
                    dir=d, rank=headline_rank(HEAD, e["event"])[0]))
REL.sort(key=lambda r: (r["t"], r["event"]))
by_day = defaultdict(list)
for r in REL:
    if r["t"].time() < time(20, 30):
        by_day[r["t"].date()].append(r)


def time_direction(rs):
    """Direction for the releases at one minute (agree -> that; disagree -> headline order decides)."""
    read = [r for r in rs if r["dir"] in ("up", "down")]
    if not read:
        return ("in line" if any(r["dir"] == "in line" for r in rs) else None), ""
    dirs = {r["dir"] for r in read}
    if len(dirs) == 1:
        return dirs.pop(), ""
    top = min(r["rank"] for r in read)
    tdirs = {r["dir"] for r in read if r["rank"] == top}
    return (tdirs.pop() if len(tdirs) == 1 else "mixed"), "releases disagreed; headline order decides"


def label(rs):
    return "; ".join(f"{r['cur']} {r['event']} ({r['tier']}; actual {r['actual']}, forecast {r['forecast']})" for r in rs)


def fmt(d):
    return f"{d:%a} {d.day} {d:%b %Y}"


lines, rows_out = [], []
P = lines.append
late = [d for d, x in DAYS.items() if x["trend"] and x["run_start"] >= 9]
allt = [d for d, x in DAYS.items() if x["trend"]]
P(f"Measured weekdays {len(DAYS)} ({min(DAYS)} to {max(DAYS)}); trend days {len(allt)}; run started 09:00 or later: {len(late)}")
P(f"Run start hours (late trends): {sorted(Counter(DAYS[d]['run_start'] for d in late).items())}")
P(f"6 Oct 2026: {DAYS[datetime(2026,10,6).date()]}")

# ---- questions 1-4: trend days whose run started at 09:00 or later ----
q = Counter()
delays, match_list, nomatch_list, noread_list, none_days, after_only = [], [], [], [], [], []
for d in late:
    x = DAYS[d]
    rs = by_day.get(d, [])
    big = [r for r in rs if r["tier"] == BIG]
    med = [r for r in rs if r["tier"] == MEDIUM]
    q["big"] += bool(big); q["medium"] += bool(med); q["big_or_medium"] += bool(rs)
    q["medium_only"] += bool(med) and not big
    start = datetime.combine(d, time(x["run_start"]), tzinfo=UK)
    before = [r for r in rs if r["t"] < start + timedelta(hours=1)]   # before the run, or inside its first hour
    row = dict(day=d, direction=x["dir"], run_starts_uk=f"{x['run_start']:02d}:00", hours=x["run"], pips=x["run_move"],
               big_releases="; ".join(f"{r['t']:%H:%M} {r['cur']} {r['event']}" for r in big),
               medium_releases="; ".join(f"{r['t']:%H:%M} {r['cur']} {r['event']}" for r in med))
    if not rs:
        none_days.append(d); row["case"] = "no big or medium release"
    elif not before:
        after_only.append(d); row["case"] = "releases only after the run's first hour"
    else:
        lt = before[-1]["t"]
        at = [r for r in before if r["t"] == lt]
        mins = int((start - lt).total_seconds() // 60)
        tier = BIG if any(r["tier"] == BIG for r in at) else MEDIUM
        dr, why = time_direction(at)
        delays.append((mins, d, tier))
        row.update(case="release before the run", release_uk=f"{lt:%H:%M}", release_tier=tier, release=label(at),
                   minutes_release_to_run_hour=mins, release_direction=dr or "no reading", note=why)
        item = (d, x, lt, at, dr, mins, tier)
        if dr in ("up", "down"):
            (match_list if dr == x["dir"] else nomatch_list).append(item)
        else:
            noread_list.append(item)
    rows_out.append(row)

P(f"\nQ1 late trend days {len(late)}: big release that day {q['big']}, medium {q['medium']}, medium but no big "
  f"{q['medium_only']}, big or medium {q['big_or_medium']}, neither {len(none_days)}")
P(f"   release before (or in the first hour of) the run: {len(delays)}; releases only later: {len(after_only)}")
P("\nQ2 minutes from the release to the start of the run's first hour (negative = release inside that hour):")
buckets = [("release inside the run's first hour", lambda m: m < 0), ("run's first hour began 0-59 min after", lambda m: 0 <= m < 60),
           ("1-2 h after", lambda m: 60 <= m < 180), ("3-5 h after", lambda m: 180 <= m < 360), ("6 h or more after", lambda m: m >= 360)]
for name, f in buckets:
    sel = [m for m, _, _ in delays if f(m)]
    selb = [m for m, _, t in delays if f(m) and t == BIG]
    P(f"   {name}: {len(sel)} (big {len(selb)}, medium {len(sel)-len(selb)})")
P(f"   median {median(m for m,_,_ in delays)} min; all sorted: {sorted(m for m,_,_ in delays)}")
rel_hours = Counter(f"{lt:%H:%M}" for _, _, lt, *_ in match_list + nomatch_list + noread_list)
P(f"   deciding release times: {sorted(rel_hours.items())}")
P(f"\nQ3 direction (actual vs forecast): readable {len(match_list)+len(nomatch_list)}, matched {len(match_list)}, "
  f"did not {len(nomatch_list)}; no reading {len(noread_list)} ({Counter(i[4] or 'no reading' for i in noread_list)})")
for tier in (BIG, MEDIUM):
    m_ = sum(1 for i in match_list if i[6] == tier); n_ = sum(1 for i in nomatch_list if i[6] == tier)
    P(f"   {tier}: matched {m_} of {m_+n_}")
for name, f in buckets:
    m_ = sum(1 for i in match_list if f(i[5])); n_ = sum(1 for i in nomatch_list if f(i[5]))
    P(f"   {name}: matched {m_} of {m_+n_}")
P("   did not match:")
for d, x, lt, at, dr, mins, tier in nomatch_list:
    P(f"     {fmt(d)}: trend {x['dir']} from {x['run_start']:02d}:00 ({x['run']} h, {x['run_move']} pips); {lt:%H:%M} "
      f"{label(at)} -> pointed {dr}")
P("   no reading:")
for d, x, lt, at, dr, mins, tier in noread_list:
    P(f"     {fmt(d)}: trend {x['dir']} from {x['run_start']:02d}:00; {lt:%H:%M} {label(at)} -> {dr or 'no reading'}")
P("   matched:")
for d, x, lt, at, dr, mins, tier in match_list:
    P(f"     {fmt(d)}: trend {x['dir']} from {x['run_start']:02d}:00; {lt:%H:%M} {label(at)}")
P(f"\nQ4 late trend days with no big or medium GBP/USD release before 20:30 UK: {len(none_days)}")
for d in none_days:
    x = DAYS[d]; P(f"   {fmt(d)}: {x['dir']} from {x['run_start']:02d}:00, {x['run']} h, {x['run_move']} pips")
P(f"   releases only after the run's first hour: {len(after_only)}")
for d in after_only:
    x = DAYS[d]; P(f"   {fmt(d)}: {x['dir']} from {x['run_start']:02d}:00; " + "; ".join(f"{r['t']:%H:%M} {r['cur']} {r['event']} ({r['tier']})" for r in by_day[d]))

# ---- question 5: every measured day with a big release (06:00-20:30 UK) ----
P("\nQ5 days with a big GBP/USD release 06:00-20:30 UK")
c5 = Counter(); ex = defaultdict(list)
for d, x in DAYS.items():
    big = [r for r in by_day.get(d, []) if r["tier"] == BIG and r["t"].time() >= time(6)]
    if not big:
        continue
    first = big[0]["t"]
    possible = first.hour <= 13  # the measure needs 8 hours in a row ending by the 20:00 candle
    grp = "first big release by 13:59" if possible else "first big release 14:00 or later"
    if x["trend"] and x["run_start"] >= first.hour:
        k = "trend run began in or after the release's hour"
    elif x["trend"]:
        k = "trend day, run already under way before the release"
    else:
        k = "not a trend day"
    c5[(grp, k)] += 1; c5[grp] += 1
    ex[(grp, k)].append((d, x, big))
for grp in ("first big release by 13:59", "first big release 14:00 or later"):
    P(f"  {grp}: {c5[grp]}")
    for k in ("trend run began in or after the release's hour", "trend day, run already under way before the release", "not a trend day"):
        P(f"     {k}: {c5[(grp, k)]}")
# base rate: days with no big release at all that day
nob = [d for d in DAYS if not any(r["tier"] == BIG for r in by_day.get(d, []))]
P(f"  for comparison, days with no big release: {len(nob)}; trend run starting 09:00 or later "
  f"{sum(1 for d in nob if DAYS[d]['trend'] and DAYS[d]['run_start'] >= 9)}; any trend day {sum(1 for d in nob if DAYS[d]['trend'])}")
early_big = [d for d in DAYS if any(r["tier"] == BIG and time(6) <= r["t"].time() and r["t"].hour <= 13 for r in by_day.get(d, []))]
P(f"  days with a big release 06:00-13:59: {len(early_big)}; trend run starting 09:00 or later "
  f"{sum(1 for d in early_big if DAYS[d]['trend'] and DAYS[d]['run_start'] >= 9)}; any trend day {sum(1 for d in early_big if DAYS[d]['trend'])}")
# by release kind: which big releases were followed by a trend
kind = defaultdict(Counter)
for (grp, k), items in ex.items():
    for d, x, big in items:
        first = [r for r in big if r["t"] == big[0]["t"]]
        kind[first[0]["cur"] + " " + " + ".join(sorted({r["event"] for r in first}))][k] += 1
P("  first big release of the day -> outcome (counts):")
for ev, cc in sorted(kind.items(), key=lambda kv: -sum(kv[1].values())):
    P(f"     {ev}: {dict(cc)}")
for key, items in sorted(ex.items()):
    P(f"  examples, {key[0]} / {key[1]} ({len(items)}): " + "; ".join(
        f"{d} ({big[0]['t']:%H:%M} {big[0]['cur']} {big[0]['event']}" + (f", {x['dir']} from {x['run_start']:02d}:00)" if x['trend'] else ")")
        for d, x, big in items))


# ---- extra: Q5 gap between the first big release and the run's first hour ----
P("  gap from the first big release to the run's first hour (trend run began in or after the release's hour):")
g = Counter()
for d, x, big in ex[("first big release by 13:59", "trend run began in or after the release's hour")]:
    m = int((datetime.combine(d, time(x["run_start"]), tzinfo=UK) - big[0]["t"]).total_seconds() // 60)
    g[next(n for n, f in buckets if f(m))] += 1
for n, _ in buckets:
    P(f"     {n}: {g[n]}")

# ---- extra: runs whose first hour holds the release - did the move start before or after the release minute? ----
from prices.model import parse_iso
from prices.store import CandleStore
st5 = CandleStore("/opt/autobot/data/research/stp_validation_store/GBPUSD", 999999)
c5m = {c.start: c for c in st5.read_range("5m", parse_iso("2024-01-01T00:00:00Z"), parse_iso("2026-11-20T00:00:00Z"))}
P("\nQ2 extra: runs whose first hour holds the release (5-minute candles, chart price)")
pre_share = []
for m, d, tier in delays:
    if m >= 0:
        continue
    x = DAYS[d]; s0 = datetime.combine(d, time(x["run_start"]), tzinfo=UK); rt = s0 - timedelta(minutes=m)
    end = datetime.combine(d, time(20, 30), tzinfo=UK)
    k = s0.astimezone(UTC); seq = []
    while k < end.astimezone(UTC):
        if k in c5m: seq.append(c5m[k])
        k += timedelta(minutes=5)
    if not seq: continue
    sg = 1 if x["dir"] == "up" else -1
    o = float(seq[0].sell_open)
    before = [c for c in seq if c.start < rt.astimezone(UTC)]
    pre = max([sg * ((float(c.sell_high) if sg > 0 else float(c.sell_low)) - o) for c in before] or [0.0])
    tot = max(sg * ((float(c.sell_high) if sg > 0 else float(c.sell_low)) - o) for c in seq)
    pre_share.append((d, round(pre, 1), round(tot, 1)))
P(f"   {len(pre_share)} runs; best move its way before the release (pips) vs whole run: " + "; ".join(f"{d} {a}/{b}" for d, a, b in pre_share))
P(f"   before the release had made under 10 pips its way: {sum(1 for _, a, _ in pre_share if a < 10)} of {len(pre_share)}")

(OUT / "news_trends.txt").write_text("\n".join(lines) + "\n")
with open(OUT / "news_trends_late_trend_days.csv", "w", newline="") as fh:
    keys = ["day", "direction", "run_starts_uk", "hours", "pips", "case", "release_uk", "release_tier",
            "minutes_release_to_run_hour", "release", "release_direction", "note", "big_releases", "medium_releases"]
    w = csv.DictWriter(fh, keys); w.writeheader()
    for r in rows_out:
        w.writerow({k: r.get(k, "") for k in keys})
print("\n".join(lines))
