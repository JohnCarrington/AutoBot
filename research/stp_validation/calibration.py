"""Random-walk calibration of STP journeys. READ ONLY.

  python -m research.stp_validation.calibration --store S --scored scored.jsonl.gz --out calibration.json

For a driftless random walk, the chance of touching a level d pips away before a level z pips away on the other side
is z / (d + z). If STP anticipates direction, the destination should be touched before the invalidation level more
often than that expectation. Tested (touches on 5-minute sell highs/lows, observation stops at the first data gap):

  at_plan      from the plan's price: destination vs the zone-break level (entry zone edge + 3 pips), and vs the
               4-hour structure-break level.
  at_confirm   from the first hourly close back out of the entry zone on the trade side after the entry was touched
               (the rejection proxy): destination vs zone-break level. This is the closest offline stand-in for
               "enter only after rejection evidence".
Also the same tests with the side flipped (a mirror plan) as a control.
"""
from __future__ import annotations

import argparse
import bisect
import gzip
import json
from decimal import Decimal
from pathlib import Path

from config.settings_loader import load_settings
from prices.model import parse_iso
from prices.store import CandleStore
from research.stp_validation.score import Market

SPLIT = "2025-07-01"


def race(m: Market, t0: float, p0: float, up_level: float, down_level: float, max_h: int = 240) -> str | None:
    """Which level is touched first after t0: 'UP', 'DOWN', 'BOTH' (same candle) or None (neither / gap)."""
    t1 = min(t0 + max_h * 3600, m.coverage_end(t0))
    for i in m.window(m.m5, t0, t1):
        u = m.m5["hi"][i] >= up_level
        d = m.m5["lo"][i] <= down_level
        if u and d:
            return "BOTH"
        if u:
            return "UP"
        if d:
            return "DOWN"
    return None


def summarise(items):
    """items: (won: bool, expected: float). Returns observed rate, expected rate, difference, and a weekly-agnostic
    binomial z (an approximation: decisions overlap, so treat z as indicative only)."""
    n = len(items)
    if not n:
        return {"n": 0}
    k = sum(1 for w, _ in items if w)
    e = sum(x for _, x in items)
    var = sum(x * (1 - x) for _, x in items)
    return {"n": n, "observed_pct": round(100 * k / n, 1), "random_walk_expected_pct": round(100 * e / n, 1),
            "difference_pts": round(100 * (k - e) / n, 1), "z_indicative": round((k - e) / var ** 0.5, 2) if var else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True, type=Path)
    ap.add_argument("--scored", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    s = load_settings().for_pair("GBPUSD")
    m = Market(s, CandleStore(a.store, s.candles.compress_after_days))
    rows = [json.loads(x) for x in gzip.open(a.scored, "rt")]
    plans = [r for r in rows if r.get("status") == "PLAN" and r.get("dest")]
    buckets: dict[str, list] = {}

    def add(name, period, item):
        buckets.setdefault(f"{name}|ALL", []).append(item)
        buckets.setdefault(f"{name}|{period}", []).append(item)

    for r in plans:
        period = "DEV" if r["as_of_utc"] < SPLIT else "TEST"
        sell = r["trade"] == "SELL"

        t0 = parse_iso(r["as_of_utc"]).timestamp()
        p0 = r["price"]
        dest_edge = r["dest"][1] if sell else r["dest"][0]
        for inv_name, inv in (("zone_break", r["zone_break"]), ("structure_break", r["structure_break"])):
            if inv is None:
                continue
            d = (p0 - dest_edge) if sell else (dest_edge - p0)
            z = (inv - p0) if sell else (p0 - inv)
            if d <= 0 or z <= 0:
                continue
            up, down = (inv, dest_edge) if sell else (dest_edge, inv)
            res = race(m, t0, p0, up, down)
            if res in ("UP", "DOWN"):
                won = (res == "DOWN") if sell else (res == "UP")
                add(f"at_plan_vs_{inv_name}", period, (won, z / (d + z)))
                add(f"at_plan_vs_{inv_name}_{r['trade']}", period, (won, z / (d + z)))
                add(f"at_plan_vs_{inv_name}_{r['condition']}", period, (won, z / (d + z)))
                # mirror control: the same distances, the other way round
                up2, down2 = (p0 + d, p0 - z) if sell else (p0 + z, p0 - d)
                res2 = race(m, t0, p0, up2, down2)
                if res2 in ("UP", "DOWN"):
                    won2 = (res2 == "UP") if sell else (res2 == "DOWN")
                    add(f"mirror_at_plan_vs_{inv_name}", period, (won2, z / (d + z)))
        tr = r["events"].get("t_reject")
        ti = r["events"].get("t_inv")
        if tr is not None and (ti is None or tr < ti) and (r["events"]["t_dest"] is None or r["events"]["t_dest"] > tr):
            i = bisect.bisect_right(m.h1["end"], tr) - 1
            pc = m.h1["cl"][i]
            d = (pc - dest_edge) if sell else (dest_edge - pc)
            z = (r["zone_break"] - pc) if sell else (pc - r["zone_break"])
            if d > 0 and z > 0:
                up, down = (r["zone_break"], dest_edge) if sell else (dest_edge, r["zone_break"])
                res = race(m, tr, pc, up, down)
                if res in ("UP", "DOWN"):
                    won = (res == "DOWN") if sell else (res == "UP")
                    add("at_confirm_vs_zone_break", period, (won, z / (d + z)))
                    add(f"at_confirm_vs_zone_break_{r['trade']}", period, (won, z / (d + z)))
    out = {k: summarise(v) for k, v in sorted(buckets.items())}
    a.out.write_text(json.dumps(out, indent=1) + "\n")
    for k, v in out.items():
        print(k, v)


if __name__ == "__main__":
    main()
