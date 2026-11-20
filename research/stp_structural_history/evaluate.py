"""Does the structural-history correction improve STP's forecasts, or only add recommendations? READ ONLY.

  PYTHONPATH=. python -m research.stp_structural_history.evaluate --store S --start 2025-01-01 --end 2026-11-19 --out F

At every 4-hour UTC boundary (00, 04, ..., 20 UTC + 4 s) while the market is open, one snapshot is taken (only candles
finished by then) and the plan is assessed three times on it:
  A  existing: zones clipped to the 150-pip window (production's zones()), no historical daily swings;
  B  retention only: all zones kept (9210ca5), no historical daily swings;
  C  retention + historical daily swings (this branch's default settings).
Every plan is made before its outcome is looked at. Outcomes use the 20 November validation's tools unchanged
(research/stp_validation): 5-minute sell highs/lows, observation stops at the first missing open slot, 240 h at most.

For each plan with an entry zone and a primary destination:
  rw_zone    from the plan's price, is the destination touched before the zone-break level (zone edge + 3 pips)?
             Random-walk expectation z/(d+z). Edge = observed - expected.
  rw_struct  the same against the 4-hour structure-break level.
  sequence   entry touched, then destination before any confirmed invalidation (hourly zone break / 4-hour break).
Plans are grouped: same in A and C, NEW in C (A had no plan), CHANGED (both have a plan, different primary or zone),
and DROPPED (A had a plan, C has none).
"""
from __future__ import annotations

import argparse
import gzip
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from config.settings_loader import load_settings
from levels.current import build
from planner import assess as A
from planner.measure import ppp, snapshot
from prices.calendar import MarketHours
from prices.store import CandleStore
from research.stp_validation.calibration import race
from research.stp_validation.score import Market, trace
from tests.planner_helpers import Over, section

UTC = timezone.utc
_real_zones = A.zones


def clipped_zones(settings, levels, adr, hourly, price):
    """Production's zones(): the same zones, kept only within levels.round_numbers_within_pips of price."""
    out = _real_zones(settings, levels, adr, hourly, price)
    if price is None:
        return out
    w = Decimal(settings.levels.round_numbers_within_pips) * ppp(settings)
    return [z for z in out if z.low <= price + w and z.high >= price - w]


def variant_plans(settings_by, snap, existing):
    out = {}
    for name, (s, clip) in settings_by.items():
        A.zones = clipped_zones if clip else _real_zones
        try:
            out[name] = A.assess(s, snap, existing, [], None).as_dict()
        finally:
            A.zones = _real_zones
    return out


def summary(p: dict) -> dict:
    ez, prim = p.get("entry_zone"), (p.get("destinations") or {}).get("primary")
    inv = p.get("invalidation") or {}
    return {"direction": p.get("dominant_direction"), "condition": p.get("condition"), "trade": p.get("trade"),
            "no_rec": p.get("no_recommendation"),
            "entry": [ez["low"], ez["high"]] if ez else None,
            "primary": prim and [prim["zone"]["low"], prim["zone"]["high"]],
            "primary_levels": prim and prim["zone"].get("levels"),
            "zone_break": inv.get("zone_break_close"), "structure_break": inv.get("structure_break_close")}


def outcome(m: Market, t0: float, p0: float, sm: dict) -> dict | None:
    if not sm["entry"] or not sm["primary"]:
        return None
    sell = sm["trade"] == "SELL"
    entry = (float(sm["entry"][0]), float(sm["entry"][1]))
    dest = (float(sm["primary"][0]), float(sm["primary"][1]))
    zb, sb = float(sm["zone_break"]), float(sm["structure_break"])
    edge = dest[1] if sell else dest[0]
    res = {"dest_distance_pips": round(((p0 - edge) if sell else (edge - p0)) / m.ppp, 1)}
    for name, inv in (("rw_zone", zb), ("rw_struct", sb)):
        d = (p0 - edge) if sell else (edge - p0)
        z = (inv - p0) if sell else (p0 - inv)
        if d > 0 and z > 0:
            up, down = (inv, edge) if sell else (edge, inv)
            r = race(m, t0, p0, up, down)
            if r in ("UP", "DOWN"):
                res[name] = {"won": (r == "DOWN") if sell else (r == "UP"), "expected": z / (d + z)}
    ev = trace(m, sell, t0, entry, dest, zb, sb, p0)
    te, td, ti = ev["t_entry"], ev["t_dest"], ev["t_inv"]
    if ev["observed_until"] - t0 < 24 * 3600:
        seq = "CENSORED"
    elif te is None:
        seq = "NO_ENTRY_DEST_FIRST" if td is not None and (ti is None or td < ti) else "NO_ENTRY"
    elif ti is not None and (td is None or ti <= td):
        seq = "ENTRY_THEN_INVALIDATED"
    elif td is not None and td >= te:
        seq = "ENTRY_THEN_DESTINATION"
    else:
        seq = "ENTRY_OPEN"
    res["sequence"] = seq
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True, type=Path)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    base = load_settings().for_pair("GBPUSD")
    store = CandleStore(a.store, base.candles.compress_after_days)
    m = Market(base, store)
    hours = MarketHours(base.market_hours)
    sA = Over(base, planner=section(base.planner, historical_daily_swing_lookback_weeks=0))
    variants = {"A": (sA, True), "B": (sA, False), "C": (base, False)}
    t = datetime.fromisoformat(a.start).replace(tzinfo=UTC) + timedelta(seconds=4)
    end = datetime.fromisoformat(a.end).replace(tzinfo=UTC)
    with gzip.open(a.out, "wt") as f:
        while t < end:
            if hours.is_open(t) and hours.is_open(t - timedelta(hours=1)):
                snap = snapshot(base, store, t)
                existing = build(base, store, t)
                row = {"as_of_utc": t.isoformat(), "fresh": snap.fresh,
                       "price": None if snap.price is None else float(snap.price)}
                if snap.fresh and snap.price is not None:
                    for k, p in variant_plans(variants, snap, existing).items():
                        sm = summary(p)
                        sm["outcome"] = outcome(m, t.timestamp(), float(snap.price), sm)
                        row[k] = sm
                f.write(json.dumps(row, default=str) + "\n")
                f.flush()
            t += timedelta(hours=4)
    print("done", a.out)


if __name__ == "__main__":
    main()
