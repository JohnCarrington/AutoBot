"""Statistics over scored STP plans. READ ONLY; writes results.json.

  python -m research.stp_validation.analyse --scored scored.jsonl.gz --out results.json

Every rate is reported with its numerator and denominator. Confidence intervals are 95% weekly-block bootstrap
intervals (decisions in the same week are not independent). "Unique" counts keep only the first decision of a run
of consecutive decisions with the same trade, entry zone and primary destination (one issued plan, many re-reads).
DEV = decisions before 2025-07-01, TEST = from 2025-07-01: anything proposed from DEV must be checked on TEST.
"""
from __future__ import annotations

import argparse
import gzip
import json
import random
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SPLIT = "2025-07-01"
HS = ("24h", "72h", "120h", "240h")


def load(path):
    return [json.loads(x) for x in gzip.open(path, "rt")]


def t(r):
    return datetime.fromisoformat(r["as_of_utc"].replace("Z", "+00:00")).timestamp()


def week(r):
    d = datetime.fromtimestamp(t(r), timezone.utc).isocalendar()
    return f"{d[0]}-{d[1]:02d}"


def rate(rows, ok, valid=lambda r: True, boot=True, seed=7):
    v = [r for r in rows if valid(r)]
    k = sum(1 for r in v if ok(r))
    out = {"n": len(v), "k": k, "pct": None if not v else round(100 * k / len(v), 1)}
    if boot and len(v) >= 20:
        by = defaultdict(list)
        for r in v:
            by[week(r)].append(1 if ok(r) else 0)
        weeks = list(by.values())
        rng = random.Random(seed)
        sims = []
        for _ in range(1000):
            s = [rng.choice(weeks) for _ in weeks]
            n = sum(len(w) for w in s)
            sims.append(100 * sum(sum(w) for w in s) / n if n else 0)
        sims.sort()
        out["ci95"] = [round(sims[25], 1), round(sims[974], 1)]
        out["weeks"] = len(weeks)
    return out


def q(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return {"n": 0}
    return {"n": len(xs), "p25": round(xs[len(xs) // 4], 1), "median": round(statistics.median(xs), 1),
            "p75": round(xs[(3 * len(xs)) // 4], 1), "mean": round(statistics.mean(xs), 1)}


def unique(rows):
    out, last = [], None
    for r in sorted(rows, key=t):
        key = (r["trade"], tuple(r["entry"]), tuple(r["dest"] or ()))
        if key != last:
            out.append(r)
        last = key
    return out


def hrs(a, b):
    return None if a is None or b is None else (a - b) / 3600


# ---- A. direction ------------------------------------------------------------------------------------------------
def direction_block(rows, base_rows):
    res = {}
    for measure in ("half_adr_24h", "half_adr_72h", "half_adr_120h", "25p_24h", "25p_72h"):
        resolved = lambda r: (r.get("first_passage") or {}).get(measure) in ("UP", "DOWN")
        base_up = rate(base_rows, lambda r: r["first_passage"][measure] == "UP", resolved, boot=False)
        block = {"base_rate_up_all_fresh_decisions": base_up}
        for d, want in (("BULLISH", "UP"), ("BEARISH", "DOWN")):
            sub = [r for r in rows if r["direction"] == d]
            block[d] = rate(sub, lambda r, w=want: r["first_passage"][measure] == w, resolved)
            block[d]["unresolved_or_censored"] = dict(Counter(
                (r.get("first_passage") or {}).get(measure) for r in sub if not resolved(r)))
        both = [r for r in rows if r["direction"] in ("BULLISH", "BEARISH")]
        block["ALL"] = rate(both, lambda r: r["first_passage"][measure] ==
                            ("UP" if r["direction"] == "BULLISH" else "DOWN"), resolved)
        b = base_up["pct"] or 50
        if block["BULLISH"]["pct"] is not None and block["BEARISH"]["pct"] is not None:
            block["balanced_accuracy"] = round((block["BULLISH"]["pct"] + block["BEARISH"]["pct"]) / 2, 1)
            block["bull_minus_base_up"] = round(block["BULLISH"]["pct"] - b, 1)
            block["bear_minus_base_down"] = round(block["BEARISH"]["pct"] - (100 - b), 1)
        res[measure] = block
    for h in ("24h", "72h", "120h"):
        v = lambda r, h=h: (r.get("net_pips") or {}).get(h) not in (None, 0)
        both = [r for r in rows if r["direction"] in ("BULLISH", "BEARISH")]
        res[f"net_sign_{h}"] = {
            "ALL": rate(both, lambda r, h=h: (r["net_pips"][h] > 0) == (r["direction"] == "BULLISH"), v),
            "base_rate_up": rate(base_rows, lambda r, h=h: r["net_pips"][h] > 0, v, boot=False),
            "BULLISH_mean_net_pips": q([r["net_pips"][h] for r in rows if r["direction"] == "BULLISH" and v(r)]),
            "BEARISH_mean_net_pips": q([r["net_pips"][h] for r in rows if r["direction"] == "BEARISH" and v(r)]),
        }
    return res


# ---- B-F. plans --------------------------------------------------------------------------------------------------
def plan_block(rows, H="120h"):
    hsec = int(H[:-1]) * 3600
    by = lambda r, key: (r["events"][key] is not None and r["events"][key] <= t(r) + hsec)
    covered = lambda r: r["events"]["observed_until"] >= t(r) + hsec
    resolved_dest = lambda r: by(r, "t_dest") or covered(r)
    res = {"n_decisions": len(rows), "n_fully_observed": sum(1 for r in rows if covered(r))}
    seq = Counter(r["sequence"][H] for r in rows)
    res["sequence"] = {k: {"n": v, "pct": round(100 * v / len(rows), 1)} for k, v in seq.most_common()}
    # B destination
    res["destination_reached"] = rate(rows, lambda r: by(r, "t_dest"), resolved_dest)
    res["destination_reached_before_invalidation"] = rate(
        rows, lambda r: by(r, "t_dest") and (r["events"]["t_inv"] is None or r["events"]["t_dest"] < r["events"]["t_inv"]),
        resolved_dest)
    res["destination_reached_after_invalidation"] = rate(
        rows, lambda r: by(r, "t_dest") and r["events"]["t_inv"] is not None and r["events"]["t_dest"] > r["events"]["t_inv"],
        resolved_dest)
    res["destination_without_correction"] = rate(
        rows, lambda r: by(r, "t_dest") and not r["events"]["in_entry_at_as_of"]
        and (r["events"]["t_entry"] is None or r["events"]["t_entry"] > r["events"]["t_dest"]), resolved_dest)
    mir_ok = lambda r: (r.get("dest_first_passage") or {}).get(H) in ("UP", "DOWN")
    res["mirror_baseline_dest_side_first"] = rate(
        rows, lambda r: r["dest_first_passage"][H] == ("DOWN" if r["trade"] == "SELL" else "UP"), mir_ok)
    res["hours_to_destination"] = q([hrs(r["events"]["t_dest"], t(r)) for r in rows if by(r, "t_dest")])
    res["destination_distance_pips"] = q([r.get("dest_distance_pips") for r in rows])
    res["closest_approach_when_not_reached_pips"] = q(
        [r["events"]["closest_dest_pips"] for r in rows if covered(r) and not by(r, "t_dest")])
    res["destination_ahead_of_price"] = rate(rows, lambda r: r["dest_ahead_of_price"])
    # C correction (entry not containing price at as_of)
    away = [r for r in rows if not r["events"]["in_entry_at_as_of"]]
    res["entry_contains_price_at_as_of"] = rate(rows, lambda r: r["events"]["in_entry_at_as_of"])
    res["correction_needed_pips"] = q([r["events"]["need_pips"] for r in away])
    res["entry_zone_touched"] = rate(away, lambda r: by(r, "t_entry"), lambda r: by(r, "t_entry") or covered(r))

    def frac(r):
        need = r["events"]["need_pips"]
        return None if not need else r["events"]["max_counter_before_dest_pips"] / need
    buckets = Counter()
    for r in away:
        f = frac(r)
        if f is None:
            continue
        b = ("none(<10%)" if f < .1 else "small(10-50%)" if f < .5 else "most(50-100%)" if f < 1
             else "reached_zone" if r["events"]["overshoot_far_edge_pips"] <= 0 else "overshot_far_edge")
        buckets[b] += 1
    tot = sum(buckets.values())
    res["correction_extent_before_destination_whole_window"] = {
        k: {"n": v, "pct": round(100 * v / tot, 1)} for k, v in sorted(buckets.items())}
    res["overshoot_beyond_far_edge_pips_when_overshot"] = q(
        [r["events"]["overshoot_far_edge_pips"] for r in away if r["events"]["overshoot_far_edge_pips"] > 0])
    res["correction_invalidated_thesis_before_destination"] = rate(
        rows, lambda r: by(r, "t_inv") and (r["events"]["t_dest"] is None or r["events"]["t_inv"] < r["events"]["t_dest"]),
        lambda r: by(r, "t_inv") or by(r, "t_dest") or covered(r))
    # D sequence and rejection proxy
    touched = [r for r in rows if by(r, "t_entry")]
    after = lambda r: (r["events"]["t_dest"] is not None and r["events"]["t_dest"] >= r["events"]["t_entry"]
                       and r["events"]["t_dest"] <= t(r) + hsec
                       and (r["events"]["t_inv"] is None or r["events"]["t_dest"] < r["events"]["t_inv"]))
    first_dest = lambda r: not (r["events"]["t_dest"] is not None and r["events"]["t_dest"] < r["events"]["t_entry"])
    rej = lambda r: (r["events"]["t_reject"] is not None
                     and (r["events"]["t_inv"] is None or r["events"]["t_reject"] < r["events"]["t_inv"]))
    tt = [r for r in touched if first_dest(r)]
    res["after_entry_touch_destination_before_invalidation"] = rate(tt, after)
    res["after_entry_touch_with_rejection_proxy"] = rate([r for r in tt if rej(r)], after)
    res["after_entry_touch_without_rejection_proxy"] = rate([r for r in tt if not rej(r)], after)
    # E timing
    res["hours_to_50pct_correction"] = q([hrs(r["events"]["t_corr50"], t(r)) for r in away
                                          if by(r, "t_corr50")])
    res["hours_to_entry_touch"] = q([hrs(r["events"]["t_entry"], t(r)) for r in away if by(r, "t_entry")])
    res["hours_entry_to_destination"] = q([hrs(r["events"]["t_dest"], r["events"]["t_entry"]) for r in tt if after(r)])
    # F invalidation
    res["invalidated_any"] = rate(rows, lambda r: by(r, "t_inv"), lambda r: by(r, "t_inv") or covered(r))
    res["invalidated_by_h1_zone_break"] = rate(rows, lambda r: by(r, "t_inv_h1"), lambda r: by(r, "t_inv") or covered(r))
    res["invalidated_by_h4_structure_break"] = rate(rows, lambda r: by(r, "t_inv_h4"),
                                                    lambda r: by(r, "t_inv") or covered(r))
    res["hours_to_invalidation"] = q([hrs(r["events"]["t_inv"], t(r)) for r in rows if by(r, "t_inv")])
    return res


def factor_table(rows, H, ok, factors):
    """Success rate of `ok` by each factor's value (for failure / root-cause analysis)."""
    out = {}
    for name, f in factors.items():
        groups = defaultdict(list)
        for r in rows:
            try:
                groups[f(r)].append(r)
            except Exception:                              # noqa: BLE001
                groups["n/a"].append(r)
        out[name] = {str(k): rate(v, ok, boot=len(v) >= 40) for k, v in sorted(groups.items(), key=lambda kv: str(kv[0]))}
    return out


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def band(x, cuts, labels):
    if x is None:
        return "n/a"
    for c, lab in zip(cuts, labels):
        if x < c:
            return lab
    return labels[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    rows = load(a.scored)
    fresh = [r for r in rows if r.get("status") in ("PLAN", "NO_PLAN")]
    R: dict = {"population": {
        "decisions": len(rows), "status": dict(Counter(r.get("status") for r in rows)),
        "fresh_by_direction": dict(Counter(r["direction"] for r in fresh)),
        "fresh_by_condition": {f"{d}/{c}": n for (d, c), n in Counter((r["direction"], r["condition"]) for r in fresh).most_common()},
        "no_recommendation_reasons": dict(Counter((r.get("no_recommendation") or "")[:70]
                                                  for r in fresh if r["status"] == "NO_PLAN").most_common(15)),
        "first": rows[0]["as_of_utc"], "last": rows[-1]["as_of_utc"]}}
    periods = {"ALL": fresh, "DEV": [r for r in fresh if r["as_of_utc"] < SPLIT],
               "TEST": [r for r in fresh if r["as_of_utc"] >= SPLIT]}
    for y in ("2024", "2025", "2026"):
        periods[y] = [r for r in fresh if r["as_of_utc"].startswith(y)]
    R["A_direction"] = {k: direction_block(v, v) for k, v in periods.items()}
    R["A_direction_by_condition"] = {}
    for cond in sorted({r["condition"] for r in fresh if r["direction"] in ("BULLISH", "BEARISH")}):
        sub = [r for r in fresh if r["condition"] == cond and r["direction"] in ("BULLISH", "BEARISH")]
        R["A_direction_by_condition"][cond] = direction_block(sub, fresh)["half_adr_120h"]
    plans = [r for r in fresh if r["status"] == "PLAN" and r.get("dest")]
    R["plans"] = {}
    for pname, sub in (("ALL", plans), ("DEV", [r for r in plans if r["as_of_utc"] < SPLIT]),
                       ("TEST", [r for r in plans if r["as_of_utc"] >= SPLIT])):
        R["plans"][pname] = {}
        for H in ("24h", "72h", "120h", "240h"):
            R["plans"][pname][H] = plan_block(sub, H)
        R["plans"][pname]["unique_120h"] = plan_block(unique(sub), "120h")
        for side in ("SELL", "BUY"):
            R["plans"][pname][f"{side}_120h"] = plan_block([r for r in sub if r["trade"] == side], "120h")
            R["plans"][pname][f"{side}_unique_120h"] = plan_block(unique([r for r in sub if r["trade"] == side]), "120h")
    R["plans_by_condition_120h"] = {c: plan_block([r for r in plans if r["condition"] == c], "120h")
                                    for c in sorted({r["condition"] for r in plans})}
    R["plans_by_countermove_state_120h"] = {c: plan_block([r for r in plans if r["countermove_state"] == c], "120h")
                                            for c in sorted({str(r["countermove_state"]) for r in plans})
                                            if any(str(r["countermove_state"]) == c for r in plans)}
    R["plans_by_selection_mode_120h"] = {c: plan_block([r for r in plans if r["selection_mode"] == c], "120h")
                                         for c in sorted({str(r["selection_mode"]) for r in plans})}
    # failure / root-cause factors on the 120h journey (destination before invalidation)
    H = "120h"
    hsec = 120 * 3600
    good = lambda r: (r["events"]["t_dest"] is not None and r["events"]["t_dest"] <= t(r) + hsec
                      and (r["events"]["t_inv"] is None or r["events"]["t_dest"] < r["events"]["t_inv"]))
    seq_ok = lambda r: r["sequence"][H] == "ENTRY_THEN_DESTINATION"
    factors = {
        "dest_touched_prior_24h": lambda r: r["past"]["dest_touched_prior_24h"],
        "dest_touched_since_last_h4_swing": lambda r: r["past"]["dest_touched_since_last_h4_swing"],
        "entry_touched_prior_24h": lambda r: r["past"]["entry_touched_prior_24h"],
        "dest_ahead_of_price": lambda r: r["dest_ahead_of_price"],
        "dest_distance_adr": lambda r: band((r.get("dest_distance_pips") or 0) / fnum(r["adr_pips"]),
                                            [0.25, 0.5, 1.0, 9e9], ["<0.25", "0.25-0.5", "0.5-1", ">=1"]),
        "need_adr": lambda r: band((r["events"]["need_pips"] or 0) / fnum(r["adr_pips"]),
                                   [0.001, 0.15, 0.35, 9e9], ["in zone", "<0.15", "0.15-0.35", ">=0.35"]),
        "daily_structure": lambda r: (r["context"]["daily_structure"] or "").split(":")[0],
        "daily_agrees": lambda r: (lambda d: "agrees" if (d == "down" and r["trade"] == "SELL") or
                                   (d == "up" and r["trade"] == "BUY") else d if d == "mixed" else "disagrees")(
            (r["context"]["daily_structure"] or "").split(":")[0]),
        "impulse_adr": lambda r: band(fnum(r["context"]["impulse_adr"]), [0.75, 1.25, 2.0, 9e9],
                                      ["<0.75", "0.75-1.25", "1.25-2", ">=2"]),
        "hours_since_last_h4_swing": lambda r: band(r["past"]["hours_since_last_h4_swing"], [24, 48, 96, 9e9],
                                                    ["<24", "24-48", "48-96", ">=96"]),
        "h4_sweep_state": lambda r: r["context"]["h4_sweep_state"],
        "entry_reachability": lambda r: r["context"]["entry_reachability"],
        "entry_class": lambda r: r["entry_class"],
        "condition": lambda r: r["condition"],
        "countermove_state": lambda r: r["countermove_state"],
        "selection_mode": lambda r: r["selection_mode"],
        "trade": lambda r: r["trade"],
        "dest_has_pivot": lambda r: "pivot" in (r["context"]["dest_families"] or []),
        "uk_hour_band": lambda r: band(int((datetime.fromtimestamp(t(r), timezone.utc).hour)), [6, 12, 18, 24],
                                       ["00-06", "06-12", "12-18", "18-24"]),
    }
    R["factors_dest_before_invalidation_120h"] = {
        p: factor_table(sub, H, good, factors)
        for p, sub in (("DEV", [r for r in plans if r["as_of_utc"] < SPLIT]),
                       ("TEST", [r for r in plans if r["as_of_utc"] >= SPLIT]), ("ALL", plans))}
    R["factors_full_sequence_120h"] = {"ALL": factor_table(plans, H, seq_ok, factors)}
    dir_rows = [r for r in fresh if r["direction"] in ("BULLISH", "BEARISH")]
    resolved = lambda r: r["first_passage"].get("half_adr_120h") in ("UP", "DOWN")
    dir_ok = lambda r: r["first_passage"]["half_adr_120h"] == ("UP" if r["direction"] == "BULLISH" else "DOWN")
    dfac = {
        "daily_structure": lambda r: r["dir_context"]["daily_structure"],
        "daily_agrees": lambda r: (lambda d: "agrees" if (d == "down" and r["direction"] == "BEARISH") or
                                   (d == "up" and r["direction"] == "BULLISH") else d if d == "mixed" else "disagrees")(
            r["dir_context"]["daily_structure"]),
        "h4_ema_stack_agrees": lambda r: (lambda s: "n/a" if not s else "agrees" if ("down" in s) == (
            r["direction"] == "BEARISH") and "mixed" not in s else "mixed" if "mixed" in s else "disagrees")(
            r["dir_context"]["h4_ema_stack"]),
        "condition": lambda r: r["condition"],
        "hours_since_last_h4_swing": lambda r: band(r["dir_context"]["hours_since_last_h4_swing"], [24, 48, 96, 9e9],
                                                    ["<24", "24-48", "48-96", ">=96"]),
        "impulse_adr": lambda r: band(fnum(r["dir_context"]["impulse_adr"]), [0.75, 1.25, 2.0, 9e9],
                                      ["<0.75", "0.75-1.25", "1.25-2", ">=2"]),
        "dist_from_h4_ema21_adr": lambda r: band(abs(fnum(r["dir_context"]["distance_from_h4_ema21_adr"]) or 0),
                                                 [0.25, 0.5, 1.0, 9e9], ["<0.25", "0.25-0.5", "0.5-1", ">=1"]),
        "has_plan": lambda r: r["status"] == "PLAN",
    }
    R["factors_direction_half_adr_120h"] = {
        p: factor_table([r for r in sub if resolved(r)], "120h", dir_ok, dfac)
        for p, sub in (("DEV", [r for r in dir_rows if r["as_of_utc"] < SPLIT]),
                       ("TEST", [r for r in dir_rows if r["as_of_utc"] >= SPLIT]), ("ALL", dir_rows))}
    # alternatives: extended vs primary destination; entry-first vs destination-first on the same decisions
    alt = {}
    ext = [r for r in plans if (r.get("alternatives") or {}).get("extended_dest")]
    for H in ("120h", "240h"):
        hs = int(H[:-1]) * 3600
        reach = lambda ev, r: ev["t_dest"] is not None and ev["t_dest"] <= t(r) + hs and (
            ev["t_inv"] is None or ev["t_dest"] < ev["t_inv"])
        alt[f"primary_vs_extended_{H}"] = {
            "n": len(ext),
            "primary_before_invalidation": rate(ext, lambda r: reach(r["events"], r)),
            "extended_before_invalidation": rate(ext, lambda r: reach(r["alternatives"]["extended_dest"], r)),
            "primary_sequence_entry_then_dest": rate(ext, lambda r: r["sequence"][H] == "ENTRY_THEN_DESTINATION"),
            "extended_sequence_entry_then_dest": rate(
                ext, lambda r: r["alternatives"]["extended_dest"]["sequence"][H] == "ENTRY_THEN_DESTINATION"),
        }
        ef = [r for r in plans if (r.get("alternatives") or {}).get("entry_first")]
        alt[f"destination_first_vs_entry_first_{H}"] = {
            "n_decisions_where_they_differ": len(ef),
            "destination_first_dest_before_inv": rate(ef, lambda r: reach(r["events"], r)),
            "entry_first_dest_before_inv": rate(ef, lambda r: reach(r["alternatives"]["entry_first"], r)),
            "destination_first_full_sequence": rate(ef, lambda r: r["sequence"][H] == "ENTRY_THEN_DESTINATION"),
            "entry_first_full_sequence": rate(
                ef, lambda r: r["alternatives"]["entry_first"]["sequence"][H] == "ENTRY_THEN_DESTINATION"),
            "destination_first_entry_touched": rate(
                ef, lambda r: r["events"]["t_entry"] is not None and r["events"]["t_entry"] <= t(r) + hs),
            "entry_first_entry_touched": rate(
                ef, lambda r: r["alternatives"]["entry_first"]["t_entry"] is not None
                and r["alternatives"]["entry_first"]["t_entry"] <= t(r) + hs),
        }
    R["alternatives"] = alt
    a.out.write_text(json.dumps(R, indent=1, default=str) + "\n")
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
