"""Three research checks for the market-phase model. RESEARCH ONLY: reads candles and trade records, writes JSON.

  compat      the fast history's V1 direction (research/stp_phase/history.py FastHistory) against the LIVE planner's
              own plan_at on a random sample of hours: they must agree for the validation to speak for the planner;
              also how often the fast and exact level maps give the same first meaningful zone;
  trades      every live AutoBot trade in the records, classified with the exact inputs at its entry time (labels
              only; nothing authorises);
  conditions  a hindsight catalogue of trading days (strong trends with corrections, ranges, false breakouts, band
              walks, structural reversals, marginal swing violations) and the model's behaviour on each kind of day.

    nice .venv/bin/python -m research.stp_phase.checks compat|trades|conditions --out <file> [--points points.jsonl]
"""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

from config.settings_loader import load_settings
from planner.assess import plan_at
from planner.phase import REVERSAL_PATTERN_STRATEGIES, assess_phase, classify_trade, summary
from prices.model import UK, parse_iso
from prices.store import CandleStore
from research.stp_phase.history import FastHistory, exact_inputs, load_tf

STORE = "/opt/autobot/data/research/stp_phase_store/GBPUSD"
TRADES = "/opt/autobot/data/records/GBPUSD/trades.jsonl"


def compat(s, out: Path, n: int = 120) -> dict:
    fh = FastHistory(s, STORE)
    st = CandleStore(Path(STORE), 10 ** 6)
    rnd = random.Random(11)
    cands = [c.end for c in fh.h1_all if c.end >= parse_iso("2024-06-01T00:00:00Z")]
    sample = sorted(rnd.sample(cands, n))
    agree = zone_same = zone_n = 0
    rows = []
    for t in sample:
        t = t + timedelta(seconds=5)
        m = fh.moment(t)
        if m is None:
            continue
        fast = assess_phase(s, m.inputs)
        live = plan_at(s, st, t, calendar=[]).direction
        ok = fast.direction.v1_direction == live
        agree += ok
        inp, _ = exact_inputs(s, st, t)
        ex = assess_phase(s, inp)
        fz = (fast.countertrend or {}).get("first_meaningful")
        ez = (ex.countertrend or {}).get("first_meaningful")
        if fz or ez:
            zone_n += 1
            same = bool(fz and ez and float(fz["low"]) <= float(ez["high"]) and float(ez["low"]) <= float(fz["high"]))
            zone_same += same
        rows.append({"t": t.isoformat(), "fast_v1": fast.direction.v1_direction, "live_planner": live, "agree": ok,
                     "fast_dir": fast.direction.direction, "exact_dir": ex.direction.direction,
                     "fast_phase": fast.phase, "exact_phase": ex.phase,
                     "fast_zone": fz and f"{fz['low']}-{fz['high']}", "exact_zone": ez and f"{ez['low']}-{ez['high']}"})
    res = {"sample": len(rows), "v1_agreement": agree, "phase_agreement": sum(r["fast_phase"] == r["exact_phase"] for r in rows),
           "direction_agreement": sum(r["fast_dir"] == r["exact_dir"] for r in rows),
           "first_meaningful_overlap": [zone_same, zone_n], "rows": rows}
    out.write_text(json.dumps(res, indent=1))
    return res


def trades(s, out: Path) -> dict:
    st = CandleStore(Path(STORE), 10 ** 6)
    lines = [json.loads(x) for x in Path(TRADES).read_text().splitlines()]
    closed = {r["reference"]: r for r in lines if r["event"] == "closed"}
    rows = []
    for r in lines:
        if r["event"] != "opened" or r.get("paper"):
            continue
        t = parse_iso(r["opened_utc"])
        inp, _ = exact_inputs(s, st, t)
        v = assess_phase(s, inp)
        label, why = classify_trade(v, r["direction"], r["strategy"] in REVERSAL_PATTERN_STRATEGIES)
        c = closed.get(r["reference"], {})
        rows.append({"opened_utc": r["opened_utc"], "strategy": r["strategy"], "direction": r["direction"],
                     "pips": c.get("pips"), "result": c.get("result") or "open", "closed_by": c.get("closed_by"),
                     "classification": label, "reason": why, "phase": v.phase, "direction_view": v.direction.direction,
                     "v1": v.direction.v1_direction, "summary": summary(v)})
    out.write_text(json.dumps(rows, indent=1))
    return {"trades": len(rows)}


def conditions(s, out: Path, points: Path) -> dict:
    side = s.chart.price
    pts = [json.loads(x) for x in points.read_text().splitlines()]
    byday = defaultdict(list)
    for r in pts:
        byday[r["t"][:10]].append(r)
    fh = FastHistory(s, STORE)
    d1 = [c for c in load_tf(Path(STORE), "1d") if c.start.astimezone(UK).weekday() < 5]
    h1 = fh.h1
    by_h1day = defaultdict(list)
    for c in h1.candles:
        by_h1day[c.start.astimezone(UK).strftime("%Y-%m-%d")].append(c)
    cats = defaultdict(list)
    prev = None
    for c in d1:
        day = c.start.astimezone(UK).strftime("%Y-%m-%d")
        if day not in byday or prev is None:
            prev = c
            continue
        rs = byday[day]
        adr = rs[0]["adr"]
        o, h, l, cl_ = (float(getattr(c, f"{side}_{x}")) for x in ("open", "high", "low", "close"))
        ph, pl = float(getattr(prev, f"{side}_high")), float(getattr(prev, f"{side}_low"))
        rng = h - l
        hs = by_h1day.get(day, [])
        labels = []
        if cl_ - o <= -0.6 * adr and rng >= 0.9 * adr:
            run_low, rally = float("inf"), 0.0
            for x in hs:
                run_low = min(run_low, float(getattr(x, f"{side}_low")))
                rally = max(rally, float(getattr(x, f"{side}_high")) - run_low)
            labels.append("strong bearish trend with a corrective rally" if rally >= 0.3 * adr else "strong bearish trend")
        if cl_ - o >= 0.6 * adr and rng >= 0.9 * adr:
            run_high, dip = float("-inf"), 0.0
            for x in hs:
                run_high = max(run_high, float(getattr(x, f"{side}_high")))
                dip = max(dip, run_high - float(getattr(x, f"{side}_low")))
            labels.append("strong bullish trend with a corrective decline" if dip >= 0.3 * adr else "strong bullish trend")
        if rng <= 0.6 * adr:
            labels.append("range-bound")
        if (h >= ph + 5 and cl_ <= ph - 0.25 * adr) or (l <= pl - 5 and cl_ >= pl + 0.25 * adr):
            labels.append("false breakout of the previous day")
        run = best = 0
        sideb = 0
        for x in hs:
            b = h1.band.get(x.start)
            if b is None:
                continue
            xc = float(getattr(x, f"{side}_close"))
            sd = 1 if xc >= float(b.upper) else -1 if xc <= float(b.lower) else 0
            run = run + 1 if sd != 0 and sd == sideb else (1 if sd != 0 else 0)
            sideb = sd
            best = max(best, run)
        if best >= 4:
            labels.append("band walk (4+ hourly closes on a band)")
        if any(r["phase"] == "STRUCTURAL_REVERSAL" for r in rs) or any(r["v1"] == "TRANSITIONAL" for r in rs):
            labels.append("structural reversal (4-hour structure broken)")
        if any(r["marginal"] and r["v1"] not in ("BEARISH", "BULLISH") for r in rs):
            labels.append("marginal swing violation (V1 neutral, tolerance directional)")
        for lab in labels:
            cats[lab].append((day, rs, cl_ - o))
        prev = c
    res = {}
    for lab, days in sorted(cats.items()):
        n = len(days)
        trad = lambda r: r["weekday"] < 5 and 6 <= r["uk_hour"] <= 20.5          # noqa: E731
        cov_v1 = cov_new = tot = 0
        agree_v1 = agree_new = dn_v1 = dn_new = 0
        ct_days = cont_days = rev_days = 0
        phases = defaultdict(int)
        for day, rs, net in days:
            tr = [r for r in rs if trad(r)]
            tot += len(tr)
            cov_v1 += sum(r["v1"] in ("BEARISH", "BULLISH") for r in tr)
            cov_new += sum(r["dir"] in ("BEARISH", "BULLISH") for r in tr)
            for r in tr:
                phases[r["phase"]] += 1
            ten = next((r for r in tr if r["uk_hour"] >= 10), None)
            if ten is not None and net != 0:
                want = "BEARISH" if net < 0 else "BULLISH"
                if ten["v1"] in ("BEARISH", "BULLISH"):
                    dn_v1 += 1
                    agree_v1 += ten["v1"] == want
                if ten["dir"] in ("BEARISH", "BULLISH"):
                    dn_new += 1
                    agree_new += ten["dir"] == want
            ct_days += any(r["opp"] == "COUNTERTREND_CORRECTION" for r in tr)
            cont_days += any(r["phase"] == "TREND_CONTINUATION" for r in tr)
            rev_days += any(r["phase"] == "STRUCTURAL_REVERSAL" for r in tr)
        res[lab] = {"days": n, "coverage_v1": round(cov_v1 / tot, 3) if tot else None,
                    "coverage_new": round(cov_new / tot, 3) if tot else None,
                    "direction_at_10_uk_matches_day": {"v1": [agree_v1, dn_v1], "new": [agree_new, dn_new]},
                    "days_with_countertrend_opportunity": ct_days, "days_with_trend_continuation": cont_days,
                    "days_with_structural_reversal_phase": rev_days,
                    "phase_mix": {k: round(v / tot, 3) for k, v in sorted(phases.items(), key=lambda x: -x[1])} if tot else {},
                    "examples": [d for d, _, _ in days[-5:]]}
    out.write_text(json.dumps(res, indent=1))
    return {k: v["days"] for k, v in res.items()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=("compat", "trades", "conditions"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--points")
    a = ap.parse_args(argv)
    s = load_settings().for_pair("GBPUSD")
    out = Path(a.out)
    r = {"compat": lambda: compat(s, out), "trades": lambda: trades(s, out),
         "conditions": lambda: conditions(s, out, Path(a.points))}[a.what]()
    print(json.dumps({k: v for k, v in r.items() if k != "rows"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
