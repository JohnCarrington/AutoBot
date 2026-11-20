"""Independent scoring of replayed STP technical forecasts. READ ONLY; no fills, no P&L, no spread.

  PYTHONPATH=. python -m research.stp_technical.score --store S --rows a.jsonl.gz [b ...] --out scored.json

Price basis: sell (chart) prices, 5-minute highs/lows, from the 5-minute candles that FINISHED after the decision.
Observation stops at the first missing open 5-minute slot (research/stp_validation/score.py Market.coverage_end).

For each forecast with an opportunity:
  entry     price inside the entry zone at the decision (entered at that price), else the first 5-minute candle within
            [stp_technical] validity_hours that reaches the zone (entered at the zone edge nearest the decision price).
            A target touched first means "target before entry" (no trade); neither means LAPSED.
  outcome   after entry, the first of the stop and the intermediate target. A candle touching both, or the entry candle
            touching the stop, counts as STOP (conservative: no order is invented inside a candle). Unresolved after
            HORIZON_H hours: OPEN. Extended target: reached after the intermediate one and before the stop.
  excursion the worst adverse and best favourable move (pips) from entry until the outcome (or the horizon), and the
            best favourable move in the first 12 hours (the reaction).
  random walk  with target distance d and stop distance z from the entry, a driftless walk touches the target first
            with probability z/(d+z). Edge = observed rate minus that, in percentage points. A forecast with no skill
            scores about zero; a positive edge needs its interval above zero.
  baselines the MIRROR (same time, entry, distances, opposite direction) and ENTER-NOW (same direction and distances,
            entered at the decision price without waiting for the zone).
Lifecycle view: a forecast counts as a NEW opportunity unless the previous counted one with the same trade and type
and an overlapping entry zone was still live (not yet resolved or lapsed) at its time.
Intervals: 95% weekly-block bootstrap (decisions overlap in time, so whole ISO weeks are resampled).
"""
from __future__ import annotations

import argparse
import bisect
import gzip
import json
import random
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from config.settings_loader import load_settings
from prices.store import CandleStore
from research.stp_validation.score import Market

HORIZON_H = 72
REACTION_H = 12
SPLIT = "2025-07-01"


def _ts(s: str) -> float:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def score_one(m: Market, fc: dict, validity_h: int, mirror: bool = False, enter_now: bool = False) -> dict | None:
    o = fc.get("opportunity")
    if not o:
        return None
    a = m.m5
    sell = (o["trade"] == "SELL") != mirror
    t0 = _ts(fc["as_of_utc"])
    p0 = float(fc["price"])
    zl, zh = float(o["entry_zone"]["low"]), float(o["entry_zone"]["high"])
    stop0, t10 = float(o["stop"]["price"]), float(o["intermediate_target"]["price"])
    ref0 = float(o["reference_entry"])
    d, z = abs(t10 - ref0), abs(stop0 - ref0)
    if d <= 0 or z <= 0:
        return None
    cov = m.coverage_end(t0)
    i = bisect.bisect_left(a["start"], t0)
    n = len(a["start"])
    # --- entry
    entered_at_decision = True
    if enter_now:
        entry, ei = p0, i
    elif zl <= p0 <= zh:
        entry, ei = p0, i
    else:
        entered_at_decision = False
        entry, ei = None, None
        t_lapse = min(t0 + validity_h * 3600, cov)
        tgt = t10 if not mirror else None
        j = i
        while j < n and a["end"][j] <= t_lapse:
            hi_, lo_ = a["hi"][j], a["lo"][j]
            if hi_ >= zl and lo_ <= zh:
                entry, ei = (zl if p0 < zl else zh), j
                break
            if tgt is not None and ((sell and lo_ <= tgt) or (not sell and hi_ >= tgt)):
                return {"sequence": "TARGET_BEFORE_ENTRY", "d": d, "z": z}
            j += 1
        if entry is None:
            return {"sequence": "LAPSED", "d": d, "z": z}
    # --- geometry from the actual entry (same distances; mirror flips the direction)
    if mirror or enter_now:
        target = entry - d if sell else entry + d
        stop = entry + z if sell else entry - z
    else:
        target, stop = t10, stop0
        d, z = abs(target - entry), abs(stop - entry)
        if d <= 0 or z <= 0:
            return None
    t_end = min(a["end"][ei] - 300 + HORIZON_H * 3600, cov) if ei < n else t0
    mae = mfe = mfe_early = 0.0
    out, t_out = "OPEN", None
    j = ei
    t_entry = a["start"][ei] if ei < n else t0
    while j < n and a["end"][j] <= t_end:
        hi_, lo_ = a["hi"][j], a["lo"][j]
        adverse = (hi_ - entry) if sell else (entry - lo_)
        favour = (entry - lo_) if sell else (hi_ - entry)
        hit_stop = (hi_ >= stop) if sell else (lo_ <= stop)
        hit_tgt = (lo_ <= target) if sell else (hi_ >= target)
        mae = max(mae, adverse)
        if hit_stop:
            out, t_out = "STOP", a["end"][j]
            break
        mfe = max(mfe, favour)
        if a["end"][j] <= t_entry + REACTION_H * 3600:
            mfe_early = max(mfe_early, favour)
        if hit_tgt and (j > ei or entered_at_decision):
            out, t_out = "TARGET", a["end"][j]
            break
        j += 1
    res = {"sequence": out, "d": d, "z": z, "expected": z / (d + z), "won": out == "TARGET",
           "mae_pips": mae / m.ppp, "mfe_pips": mfe / m.ppp, "reaction_pips": mfe_early / m.ppp,
           "hours_to_outcome": None if t_out is None else (t_out - t_entry) / 3600}
    ext = o.get("extended_target")
    if out == "TARGET" and ext and not (mirror or enter_now):
        e = float(ext["price"])
        k = j + 1
        res["extended"] = False
        while k < n and a["end"][k] <= t_end:
            if (a["hi"][k] >= stop) if sell else (a["lo"][k] <= stop):
                break
            if (a["lo"][k] <= e) if sell else (a["hi"][k] >= e):
                res["extended"] = True
                break
            k += 1
    return res


def week(t: str) -> str:
    y, w, _ = datetime.fromisoformat(t.replace("Z", "+00:00")).isocalendar()
    return f"{y}-W{w:02d}"


def boot(items, reps=2000, seed=20261120):
    if not items:
        return None
    by = defaultdict(list)
    for w, won, e in items:
        by[w].append(won - e)
    weeks = list(by)
    rnd = random.Random(seed)
    means = []
    for _ in range(reps):
        xs = [x for w in (rnd.choice(weeks) for _ in weeks) for x in by[w]]
        means.append(sum(xs) / len(xs))
    means.sort()
    n = len(items)
    return {"n": n, "won_pct": round(100 * sum(i[1] for i in items) / n, 1),
            "expected_pct": round(100 * sum(i[2] for i in items) / n, 1),
            "edge_pts": round(100 * sum(i[1] - i[2] for i in items) / n, 1),
            "ci95_pts": [round(100 * means[int(0.025 * reps)], 1), round(100 * means[int(0.975 * reps)], 1)]}


def _size_group(period: str, d: float) -> str:
    """Target-distance bucket. d is in price points; for GBPUSD on IG one point is one pip."""
    if d < 8:
        return f"{period}:target<8"
    if d <= 15:
        return f"{period}:target8-15"
    return f"{period}:target15-30" if d <= 30 else f"{period}:target>30"


def summarise(rows: list[dict]) -> dict:
    """rows: dicts with as_of, main/mirror/now results."""
    def resolved(key):
        return [(week(r["as_of"]), int(r[key]["won"]), r[key]["expected"]) for r in rows
                if r.get(key) and r[key]["sequence"] in ("TARGET", "STOP")]
    seq = defaultdict(int)
    for r in rows:
        seq[r["main"]["sequence"]] += 1
    entered = [r["main"] for r in rows if r["main"]["sequence"] in ("TARGET", "STOP", "OPEN")]
    med = lambda xs: round(statistics.median(xs), 1) if xs else None  # noqa: E731
    ext = [r["main"]["extended"] for r in rows if "extended" in r["main"]]
    return {"forecasts": len(rows), "sequence": dict(seq),
            "target_distance_pips_median": med([r["main"]["d"] for r in rows]),
            "stop_distance_pips_median": med([r["main"]["z"] for r in rows]),
            "main": boot(resolved("main")), "mirror": boot(resolved("mirror")), "enter_now": boot(resolved("now")),
            "mae_pips_median": med([e["mae_pips"] for e in entered]), "mfe_pips_median": med([e["mfe_pips"] for e in entered]),
            "reaction_12h_pips_median": med([e["reaction_pips"] for e in entered]),
            "extended_after_target_pct": round(100 * sum(ext) / len(ext), 1) if ext else None}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True, type=Path)
    ap.add_argument("--rows", required=True, nargs="+", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    s = load_settings().for_pair("GBPUSD")
    m = Market(s, CandleStore(a.store, s.candles.compress_after_days))
    vh = s.stp_technical.validity_hours
    fcs = [json.loads(x) for p in a.rows for x in gzip.open(p, "rt")]
    fcs.sort(key=lambda f: f["as_of_utc"])
    scored, live = [], []
    counts = defaultdict(int)
    for fc in fcs:
        counts["decisions"] += 1
        if fc.get("error"):
            counts["errors"] += 1
            continue
        if not fc.get("opportunity"):
            counts["no_opportunity"] += 1
            continue
        main_ = score_one(m, fc, vh)
        if main_ is None:
            counts["unscorable"] += 1
            continue
        o = fc["opportunity"]
        t0 = _ts(fc["as_of_utc"])
        zl, zh = float(o["entry_zone"]["low"]), float(o["entry_zone"]["high"])
        new = True
        for (tr, kind, lo_, hi_, until) in live:
            if tr == o["trade"] and kind == o["type"] and lo_ <= zh and zl <= hi_ and until > t0:
                new = False
                break
        hours = main_.get("hours_to_outcome")
        until = t0 + (vh * 3600 if main_["sequence"] in ("LAPSED", "TARGET_BEFORE_ENTRY") else
                      (hours or HORIZON_H) * 3600 + vh * 3600)
        if new:
            live = [x for x in live if x[4] > t0] + [(o["trade"], o["type"], zl, zh, until)]
        scored.append({"as_of": fc["as_of_utc"], "type": o["type"], "trade": o["trade"], "countertrend": o["countertrend"],
                       "new": new, "score": o["score"], "main": main_, "mirror": score_one(m, fc, vh, mirror=True),
                       "now": score_one(m, fc, vh, enter_now=True)})
    groups: dict[str, list] = defaultdict(list)
    for r in scored:
        period = "DEV" if r["as_of"] < SPLIT else "TEST"
        for g in ("ALL", period, f"{period}:{r['type']}", f"{period}:{r['trade']}",
                  f"{period}:countertrend" if r["countertrend"] else f"{period}:with-trend",
                  f"{period}:new-only" if r["new"] else f"{period}:repeat",
                  _size_group(period, r["main"]["d"])):
            groups[g].append(r)
    out = {"counts": dict(counts), "horizon_h": HORIZON_H, "validity_h": vh,
           "groups": {g: summarise(rs) for g, rs in sorted(groups.items())}}
    a.out.write_text(json.dumps(out, indent=1))
    with gzip.open(a.out.with_suffix(".rows.jsonl.gz"), "wt") as f:
        for r in scored:
            f.write(json.dumps(r) + "\n")
    print(json.dumps({"counts": out["counts"], "ALL": out["groups"]["ALL"]}, indent=1))


if __name__ == "__main__":
    main()
