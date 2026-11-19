"""Score the collected decisions (research/stp_phase/collect.py) against what happened next. RESEARCH ONLY.

Every score uses the future fields only to SCORE a decision; the decisions themselves were made from finished
candles. Hourly decisions overlap (one episode spans many hours), so counts are given both as decision points and
as independent episodes or weeks, and the headline comparisons carry a weekly block-bootstrap interval.

    .venv/bin/python -m research.stp_phase.analyse --points points.jsonl --out results.json
"""
from __future__ import annotations

import argparse
import json
import math
import random
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

DIRVARS = ["tol0_bos0", "tol15_bos0", "tol0_bos1", "fixed5", "tol05", "tol10", "tol15", "tol25", "consensus"]
LABEL = {"v1": "V1 (live rule)", "tol0_bos0": "no tolerance, no break of structure, EMA confirmation required",
         "tol15_bos0": "tolerance 0.15 ADR only", "tol0_bos1": "break of structure only", "fixed5": "tolerance 5 pips + BOS",
         "tol05": "tolerance 0.05 ADR + BOS", "tol10": "tolerance 0.10 ADR + BOS", "tol15": "DEFAULT: tolerance 0.15 ADR + BOS",
         "tol25": "tolerance 0.25 ADR + BOS", "consensus": "default + EMA consensus when mixed"}


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(p, 3), round(c - h, 3), round(c + h, 3)]


def trading(r):
    return r["weekday"] < 5 and 6 <= r["uk_hour"] <= 20.5


def week(r):
    t = datetime.fromisoformat(r["t"].replace("Z", "+00:00"))
    return (t - timedelta(days=t.weekday())).strftime("%Y-%m-%d")


def sgn(x):
    return (x > 0) - (x < 0)


def dir_hit(d, r, field):
    """True/False whether the direction d was right on `field` (ret24 sign or first passage), None if unresolved."""
    want = -1 if d == "BEARISH" else 1
    if field == "fp":
        fp = r.get("fp_half_adr")
        if fp not in ("up", "down"):
            return None
        return (fp == "up") == (want == 1)
    x = r.get(field)
    if x is None or x == 0:
        return None
    return sgn(x) == want


def boot_ci(groups, n_boot=1000, seed=7):
    """groups: list of (k, n) per week. Percentile CI of sum(k)/sum(n) over weeks resampled with replacement."""
    rnd = random.Random(seed)
    if not groups:
        return None
    vals = []
    for _ in range(n_boot):
        s = [groups[rnd.randrange(len(groups))] for _ in groups]
        k, n = sum(a for a, _ in s), sum(b for _, b in s)
        if n:
            vals.append(k / n)
    vals.sort()
    return [round(vals[int(0.025 * len(vals))], 3), round(vals[int(0.975 * len(vals)) - 1], 3)]


def direction_table(pts, getter, name):
    tp = [r for r in pts if trading(r)]
    cov = sum(1 for r in tp if getter(r) in ("BEARISH", "BULLISH"))
    out = {"variant": name, "label": LABEL.get(name, name), "trading_points": len(tp), "coverage": round(cov / len(tp), 3)}
    for field in ("fp", "ret24", "ret48"):
        k = n = 0
        wk = defaultdict(lambda: [0, 0])
        for r in tp:
            d = getter(r)
            if d not in ("BEARISH", "BULLISH"):
                continue
            h = dir_hit(d, r, field)
            if h is None:
                continue
            n += 1
            k += h
            wk[week(r)][0] += h
            wk[week(r)][1] += 1
        out[field] = {"n": n, "acc": wilson(k, n), "weekly_boot_ci": boot_ci([tuple(v) for v in wk.values()]),
                      "weeks": len(wk)}
    return out


def zone_of(s):
    if not s:
        return None
    m = re.match(r"([\d.]+)-([\d.]+)", s)
    return (float(m.group(1)), float(m.group(2))) if m else None


def first_passage(r, bear, target_counter, stop_trend_extreme, close_stop=None, horizon=72):
    """Walk the future hourly candles: 'counter' if price reaches target_counter (against the trend) first, 'trend' if
    it goes beyond stop_trend_extreme (with the trend) first, 'close_stop' if an hourly close beyond close_stop
    comes first; 'both' when one candle does two; None if neither within the horizon."""
    his, los, cls = r["fut_hi"][:horizon], r["fut_lo"][:horizon], r["fut_cl"][:horizon]
    for h, l, c in zip(his, los, cls):
        counter = (h >= target_counter) if bear else (l <= target_counter)
        trend = stop_trend_extreme is not None and ((l <= stop_trend_extreme) if bear else (h >= stop_trend_extreme))
        cstop = close_stop is not None and ((c >= close_stop) if bear else (c <= close_stop))
        hits = [x for x, ok in (("counter", counter), ("trend", trend), ("close_stop", cstop)) if ok]
        if len(hits) > 1:
            return "both"
        if hits:
            return hits[0]
    return None


def rate(outs, good):
    res = [o for o in outs if o in good or (o not in (None, "both"))]
    k = sum(1 for o in res if o in good)
    return {"resolved": len(res), "unresolved": len(outs) - len(res), "rate": wilson(k, len(res))}


def phase_quality(pts):
    by = defaultdict(list)
    for r in pts:
        if r["dir"] not in ("BEARISH", "BULLISH") or r["E"] is None:
            continue
        bear = r["dir"] == "BEARISH"
        a, E, p = r["adr"], r["E"], r["price"]
        # bounce first: a counter move of 0.2 ADR from price before a new extreme 3 pips beyond E
        o = first_passage(r, bear, p + 0.2 * a if bear else p - 0.2 * a, E - 3 if bear else E + 3)
        by[("bounce", r["phase"], bool(r.get("recent")))].append((o, r))
    out = {}
    for (kind, ph, rec), lst in sorted(by.items()):
        outs = [o for o, _ in lst]
        eps = len({(r["dir"], r["e_utc"]) for _, r in lst})
        out[f"{ph}{' (recent extreme)' if rec else ''}"] = {"points": len(lst), "episodes": eps,
                                                            "counter_move_first": rate(outs, {"counter"})}
    return out


def specific_outcomes(pts):
    res = {}
    # RESISTANCE / SUPPORT TEST: a 0.2 ADR move with the trend before an hourly close 3 pips through the tested zone
    rt, cont, ct, ctx = [], [], [], []
    for r in pts:
        if r["dir"] not in ("BEARISH", "BULLISH"):
            continue
        bear = r["dir"] == "BEARISH"
        a, p = r["adr"], r["price"]
        if r["phase"] in ("RESISTANCE_TEST", "SUPPORT_TEST"):
            z = zone_of(r.get("testing"))
            if z:
                stop = z[1] + 3 if bear else z[0] - 3
                o = _walk(r, lambda h, l, c: (l <= p - 0.2 * a) if bear else (h >= p + 0.2 * a),
                          lambda h, l, c: (c >= stop) if bear else (c <= stop))
                rt.append((o, r))
        if r["phase"] == "TREND_CONTINUATION" and r.get("cont_inval") is not None:
            E, inv = r["E"], r["cont_inval"]
            o = _walk(r, lambda h, l, c: (l <= E - 3) if bear else (h >= E + 3),
                      lambda h, l, c: (c >= inv) if bear else (c <= inv))
            cont.append((o, r))
        if r["opp"] == "COUNTERTREND_CORRECTION" and r.get("dest") is not None and r.get("inval") is not None:
            dest, inv = r["dest"], r["inval"]
            o = _walk(r, lambda h, l, c: (h >= dest) if bear else (l <= dest),
                      lambda h, l, c: (c <= inv) if bear else (c >= inv), horizon=48)
            ct.append((o, r))
        if r["phase"] in ("EXHAUSTION", "TREND_IMPULSE") and r.get("recent") and r.get("dest") is not None and r.get("inval") is not None \
                and r["opp"] != "COUNTERTREND_CORRECTION":
            dest, inv = r["dest"], r["inval"]
            o = _walk(r, lambda h, l, c: (h >= dest) if bear else (l <= dest),
                      lambda h, l, c: (c <= inv) if bear else (c >= inv), horizon=48)
            ctx.append((o, r))
    for name, lst in (("resistance_or_support_test_rejected", rt), ("trend_continuation_new_extreme_before_invalidation", cont),
                      ("countertrend_opportunity_destination_before_invalidation", ct),
                      ("baseline_recent_extreme_without_countertrend_opportunity_destination_before_invalidation", ctx)):
        outs = [o for o, _ in lst]
        res[name] = {"points": len(lst), "episodes": len({(r["dir"], r["e_utc"]) for _, r in lst}),
                     **rate(outs, {"first"})}
    # false continuations = continuation signals whose invalidation came first
    c = [o for o, _ in cont]
    res["false_continuation_share"] = wilson(sum(1 for o in c if o == "second"), sum(1 for o in c if o in ("first", "second")))
    # by episode: the first continuation signal of each episode only
    seen, first_c = set(), []
    for o, r in cont:
        key = (r["dir"], r["e_utc"])
        if key not in seen:
            seen.add(key)
            first_c.append(o)
    res["trend_continuation_first_signal_per_episode"] = rate(first_c, {"first"})
    seen, first_ct = set(), []
    for o, r in ct:
        key = (r["dir"], r["e_utc"])
        if key not in seen:
            seen.add(key)
            first_ct.append(o)
    res["countertrend_first_signal_per_episode"] = rate(first_ct, {"first"})
    return res


def _walk(r, first, second, horizon=72):
    for h, l, c in zip(r["fut_hi"][:horizon], r["fut_lo"][:horizon], r["fut_cl"][:horizon]):
        a, b = first(h, l, c), second(h, l, c)
        if a and b:
            return "both"
        if a:
            return "first"
        if b:
            return "second"
    return None


def evidence_usefulness(pts):
    rows = []
    for r in pts:
        if r["dir"] in ("BEARISH", "BULLISH") and r.get("recent") and r["phase"] in ("TREND_IMPULSE", "EXHAUSTION") and r["E"] is not None:
            bear = r["dir"] == "BEARISH"
            a, E, p = r["adr"], r["E"], r["price"]
            o = first_passage(r, bear, p + 0.2 * a if bear else p - 0.2 * a, E - 3 if bear else E + 3)
            if o in ("counter", "trend"):
                rows.append((set(r["ex"]), o == "counter"))
    base = wilson(sum(1 for _, g in rows if g), len(rows))
    names = ["band_extension", "rsi_recovery", "macd_contraction", "rejection_candle", "extension_from_ema21", "at_support",
             "h4_band_extension"]
    single = {}
    for nm in names:
        w = [g for e, g in rows if nm in e]
        wo = [g for e, g in rows if nm not in e]
        single[nm] = {"with": wilson(sum(w), len(w)), "without": wilson(sum(wo), len(wo))}
    pairs = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            w = [g for e, g in rows if a in e and b in e]
            if len(w) >= 40:
                pairs.append({"pair": [a, b], "n": len(w), "rate": wilson(sum(w), len(w))})
    pairs.sort(key=lambda x: -x["rate"][0])
    counts = {}
    for k in range(0, 6):
        w = [g for e, g in rows if len(e) == k]
        counts[k] = wilson(sum(w), len(w)) if w else None
    turn = [g for e, g in rows if e & {"band_extension", "rsi_recovery", "macd_contraction", "rejection_candle"}]
    noturn = [g for e, g in rows if not e & {"band_extension", "rsi_recovery", "macd_contraction", "rejection_candle"}]
    return {"resolved_points": len(rows), "base_rate_counter_move_first": base, "single": single,
            "pairs_top": pairs[:8], "pairs_bottom": pairs[-5:], "by_count": counts,
            "any_turn_sign": wilson(sum(turn), len(turn)), "no_turn_sign": wilson(sum(noturn), len(noturn))}


def resistance_quality(pts):
    """Episode level: the first countertrend view of each episode vs where the correction actually stopped."""
    seen, rows = set(), []
    for r in pts:
        if r["dir"] not in ("BEARISH", "BULLISH") or r.get("fm_low") is None or r["E"] is None:
            continue
        key = (r["dir"], r["e_utc"])
        if key in seen:
            continue
        seen.add(key)
        bear = r["dir"] == "BEARISH"
        E = r["E"]
        cfin = None
        ext = r["price"]
        for h, l, c in zip(r["fut_hi"], r["fut_lo"], r["fut_cl"]):
            if (l <= E - 3) if bear else (h >= E + 3):
                break
            ext = max(ext, h) if bear else min(ext, l)
        cfin = ext
        st = re.search(r"([\d.]+) \(", r.get("impulse_start") or "")
        start = float(st.group(1)) if st else None
        w = r["fm_high"] - r["fm_low"]
        bands = {"strict_meaningful_zone": (r["fm_low"], r["fm_high"])}
        if r.get("fm_low_loose") is not None:
            bands["loose_meaningful_zone"] = (r["fm_low_loose"], r["fm_high_loose"])
        if r.get("e21") is not None:
            bands["h1_ema21_band"] = (r["e21"] - w / 2, r["e21"] + w / 2)
        if r.get("bmid") is not None:
            bands["h1_bollinger_middle_band"] = (r["bmid"] - w / 2, r["bmid"] + w / 2)
        if start is not None:
            f382 = E + 0.382 * (start - E)
            bands["fib_38_2_band"] = (f382 - w / 2, f382 + w / 2)
        rows.append({"bear": bear, "cfin": cfin, "bands": bands, "price": r["price"]})
    out = {"episodes": len(rows)}
    names = sorted({k for x in rows for k in x["bands"]})
    for nm in names:
        reached = stopped = over = under = n = 0
        widths = []
        for x in rows:
            if nm not in x["bands"]:
                continue
            lo_, hi_ = sorted(x["bands"][nm])
            bear, c = x["bear"], x["cfin"]
            near_edge, far_edge = (lo_, hi_) if bear else (hi_, lo_)
            if (bear and near_edge < x["price"]) or (not bear and near_edge > x["price"]):
                continue                                   # band behind price: not an opposing level
            n += 1
            widths.append(hi_ - lo_)
            r_ = (c >= near_edge - 3) if bear else (c <= near_edge + 3)
            o_ = (c > far_edge + 3) if bear else (c < far_edge - 3)
            reached += r_
            over += o_
            under += not r_
            stopped += r_ and not o_
        out[nm] = {"n": n, "reached": wilson(reached, n), "stopped_in_band": wilson(stopped, n),
                   "overshot": wilson(over, n), "fell_short": wilson(under, n),
                   "stopped_given_reached": wilson(stopped, reached),
                   "mean_width_pips": round(sum(widths) / len(widths), 1) if widths else None}
    return out


def coverage_and_opps(pts):
    tp = [r for r in pts if trading(r)]
    ph = Counter(r["phase"] for r in tp)
    opp = Counter(r["opp"] for r in tp)
    return {"trading_points": len(tp), "phases": {k: round(v / len(tp), 3) for k, v in ph.most_common()},
            "opportunities": {str(k): round(v / len(tp), 3) for k, v in opp.most_common()},
            "v1_recommendable_direction": round(sum(1 for r in tp if r["v1"] in ("BEARISH", "BULLISH")) / len(tp), 3),
            "default_direction": round(sum(1 for r in tp if r["dir"] in ("BEARISH", "BULLISH")) / len(tp), 3)}


def walk_forward(pts):
    """Choose the tolerance (with break of structure) on the previous 6 months by first-passage accuracy among
    choices covering at least as many hours as V1; test on the next 3 months."""
    choices = ["tol0_bos1", "fixed5", "tol05", "tol10", "tol15", "tol25"]
    tp = [r for r in pts if trading(r)]
    months = sorted({r["t"][:7] for r in tp})
    out = []

    def score(rs, var):
        g = (lambda r: r["v1"]) if var == "v1" else (lambda r: r["dirs"][var])
        k = n = cov = 0
        for r in rs:
            d = g(r)
            if d in ("BEARISH", "BULLISH"):
                cov += 1
                h = dir_hit(d, r, "fp")
                if h is not None:
                    n += 1
                    k += h
        return (k / n if n else 0), (cov / len(rs) if rs else 0), k, n

    for i in range(6, len(months) - 2, 3):
        train = [r for r in tp if r["t"][:7] in months[i - 6:i]]
        test = [r for r in tp if r["t"][:7] in months[i:i + 3]]
        v1acc, v1cov, *_ = score(train, "v1")
        cands = [(score(train, c), c) for c in choices]
        ok = [x for x in cands if x[0][1] >= v1cov] or cands
        best = max(ok, key=lambda x: x[0][0])[1]
        ta, tc, tk, tn = score(test, best)
        da, dc, dk, dn = score(test, "tol15")
        va, vc, vk, vn = score(test, "v1")
        out.append({"train": f"{months[i - 6]}..{months[i - 1]}", "test": f"{months[i]}..{months[min(i + 2, len(months) - 1)]}",
                    "chosen": best, "chosen_test_acc": round(ta, 3), "chosen_test_cov": round(tc, 3), "chosen_n": tn,
                    "default_test_acc": round(da, 3), "default_test_cov": round(dc, 3), "default_n": dn,
                    "v1_test_acc": round(va, 3), "v1_test_cov": round(vc, 3), "v1_n": vn})
    return out


def newly_covered(pts):
    """Hours where V1 was NEUTRAL and the default model directional: is the added conviction any good?"""
    groups = {"marginal (tolerance)": lambda r: r["marginal"], "break of structure": lambda r: r["bos"] and not r["marginal"]}
    out = {}
    tp = [r for r in pts if trading(r) and r["v1"] not in ("BEARISH", "BULLISH") and r["dir"] in ("BEARISH", "BULLISH")]
    for name, g in [("all", lambda r: True)] + list(groups.items()):
        sub = [r for r in tp if g(r)]
        for field in ("fp", "ret24"):
            k = n = 0
            wk = defaultdict(lambda: [0, 0])
            for r in sub:
                h = dir_hit(r["dir"], r, field)
                if h is None:
                    continue
                n += 1
                k += h
                wk[week(r)][0] += h
                wk[week(r)][1] += 1
            out.setdefault(name, {"points": len(sub), "weeks": len({week(r) for r in sub}),
                                  "days": len({r["t"][:10] for r in sub})})[field] = {
                "n": n, "acc": wilson(k, n), "weekly_boot_ci": boot_ci([tuple(v) for v in wk.values()])}
    both = [r for r in pts if trading(r) and r["v1"] in ("BEARISH", "BULLISH")]
    out["agreement_when_v1_directional"] = round(sum(1 for r in both if r["dir"] == r["v1"]) / len(both), 3) if both else None
    out["default_neutral_when_v1_directional"] = round(sum(1 for r in both if r["dir"] == "NEUTRAL") / len(both), 3) if both else None
    return out


def momentum_baseline(pts):
    tp = sorted(pts, key=lambda r: r["t"])
    k = n = 0
    for i in range(24, len(tp)):
        r = tp[i]
        if not trading(r):
            continue
        d = sgn(r["price"] - tp[i - 24]["price"])
        if d == 0:
            continue
        h = dir_hit("BEARISH" if d < 0 else "BULLISH", r, "fp")
        if h is None:
            continue
        n += 1
        k += h
    ups = [r for r in pts if trading(r) and r.get("fp_half_adr") in ("up", "down")]
    return {"momentum_24h_fp": wilson(k, n), "share_up_first": wilson(sum(1 for r in ups if r["fp_half_adr"] == "up"), len(ups))}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--points", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    pts = [json.loads(x) for x in Path(a.points).read_text().splitlines()]
    res = {"points": len(pts), "first": pts[0]["t"], "last": pts[-1]["t"]}
    res["direction"] = [direction_table(pts, lambda r: r["v1"], "v1")] + \
        [direction_table(pts, (lambda v: lambda r: r["dirs"][v])(v), v) for v in DIRVARS]
    res["baselines"] = momentum_baseline(pts)
    res["newly_covered"] = newly_covered(pts)
    res["coverage"] = coverage_and_opps(pts)
    res["phase_quality"] = phase_quality(pts)
    res["specific"] = specific_outcomes(pts)
    res["evidence"] = evidence_usefulness(pts)
    res["resistance"] = resistance_quality(pts)
    res["walk_forward"] = walk_forward(pts)
    res["geometry"] = geometry(pts)
    res["geometry_touch_stops"] = geometry(pts, touch_stops=True)
    Path(a.out).write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ("points", "first", "last")}))
    return 0



def geometry(pts, touch_stops=False):
    """Random-walk expectation for each first-passage test: with no edge, P(target first) = d_stop / (d_target + d_stop)
    (distances from the decision price). Observed above that expectation is evidence of an edge; at it, none."""
    out = {}
    tests = defaultdict(list)
    for r in pts:
        if r["dir"] not in ("BEARISH", "BULLISH"):
            continue
        bear = r["dir"] == "BEARISH"
        p, a = r["price"], r["adr"]
        if r["phase"] == "TREND_CONTINUATION" and r.get("cont_inval") is not None:
            tgt, stop = (r["E"] - 3, r["cont_inval"]) if bear else (r["E"] + 3, r["cont_inval"])
            o = _walk(r, lambda h, l, c: (l <= tgt) if bear else (h >= tgt), lambda h, l, c: ((h if touch_stops else c) >= stop) if bear else ((l if touch_stops else c) <= stop))
            tests["trend_continuation"].append((o, abs(p - tgt), abs(stop - p)))
        if r["opp"] == "COUNTERTREND_CORRECTION" and r.get("dest") is not None and r.get("inval") is not None:
            tgt, stop = r["dest"], r["inval"]
            o = _walk(r, lambda h, l, c: (h >= tgt) if bear else (l <= tgt), lambda h, l, c: ((l if touch_stops else c) <= stop) if bear else ((h if touch_stops else c) >= stop), 48)
            tests["countertrend_opportunity"].append((o, abs(tgt - p), abs(p - stop)))
        if r["phase"] in ("RESISTANCE_TEST", "SUPPORT_TEST"):
            z = zone_of(r.get("testing"))
            if z:
                stop = z[1] + 3 if bear else z[0] - 3
                tgt = p - 0.2 * a if bear else p + 0.2 * a
                o = _walk(r, lambda h, l, c: (l <= tgt) if bear else (h >= tgt), lambda h, l, c: ((h if touch_stops else c) >= stop) if bear else ((l if touch_stops else c) <= stop))
                tests["level_test_rejection"].append((o, abs(p - tgt), abs(stop - p)))
        if r["phase"] in ("EXHAUSTION", "TREND_IMPULSE") and r.get("recent") and r["E"] is not None:
            tgt, stop = (p + 0.2 * a, r["E"] - 3) if bear else (p - 0.2 * a, r["E"] + 3)
            o = _walk(r, lambda h, l, c: (h >= tgt) if bear else (l <= tgt), lambda h, l, c: (l <= stop) if bear else (h >= stop))
            tests[f"bounce_first_{r['phase'].lower()}"].append((o, abs(tgt - p), abs(p - stop)))
    for name, lst in tests.items():
        res = [(o, dt, ds) for o, dt, ds in lst if o in ("first", "second") and dt + ds > 0]
        k = sum(1 for o, _, _ in res if o == "first")
        exp = sum(ds / (dt + ds) for _, dt, ds in res) / len(res) if res else None
        out[name] = {"resolved": len(res), "observed": wilson(k, len(res)), "random_walk_expectation": round(exp, 3) if exp else None,
                     "mean_target_pips": round(sum(dt for _, dt, _ in res) / len(res), 1) if res else None,
                     "mean_stop_pips": round(sum(ds for _, _, ds in res) / len(res), 1) if res else None}
    return out


if __name__ == "__main__":
    raise SystemExit(main())
