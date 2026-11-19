"""Collect the market-phase model's decisions at every hourly close over the research store (walk-forward in time:
each decision uses only candles finished by then), with the V1 rule and the direction variants alongside, and
the FUTURE outcomes needed to score them (computed from later candles, kept in separate fields, never fed back).
RESEARCH ONLY: reads candles, writes one JSONL file.

    nice -n 19 .venv/bin/python -m research.stp_phase.collect --from 2024-03-01 --to 2026-11-18 --out points.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from config.settings_loader import load_settings
from planner.measure import cl, hi, lo
from planner.phase import DEFAULT, assess_phase, dominant
from prices.model import UK, parse_iso
from research.stp_phase.history import FastHistory

STORE = "/opt/autobot/data/research/stp_phase_store/GBPUSD"
VARIANTS = {
    "tol0_bos0": replace(DEFAULT, use_tolerance=False, break_of_structure=False),
    "tol15_bos0": replace(DEFAULT, break_of_structure=False),
    "tol0_bos1": replace(DEFAULT, use_tolerance=False),
    "tol05": replace(DEFAULT, tolerance_adr_share=Decimal("0.05")),
    "tol10": replace(DEFAULT, tolerance_adr_share=Decimal("0.10")),
    "tol15": DEFAULT,
    "tol25": replace(DEFAULT, tolerance_adr_share=Decimal("0.25")),
    "fixed5": replace(DEFAULT, tolerance_adr_share=Decimal("0")),
    "consensus": replace(DEFAULT, mixed_allows_ema_consensus=True),
}


def f(x):
    return None if x is None else float(x)


def outcomes(h1, k: int, price: Decimal, adr: Decimal, side: str) -> dict:
    """Future facts from the hourly candles after index k (the first not finished at the decision)."""
    fut = h1[k:k + 72]
    o = {}
    if len(fut) >= 24:
        o["ret24"] = float(cl(fut[23], side) - price)
    if len(fut) >= 48:
        o["ret48"] = float(cl(fut[47], side) - price)
    half = adr / 2
    first = None
    for c in fut:
        up, dn = hi(c, side) >= price + half, lo(c, side) <= price - half
        if up and dn:
            first = "both"
            break
        if up or dn:
            first = "up" if up else "down"
            break
    o["fp_half_adr"] = first
    o["fut_hi"] = [float(hi(c, side)) for c in fut]
    o["fut_lo"] = [float(lo(c, side)) for c in fut]
    o["fut_cl"] = [float(cl(c, side)) for c in fut]
    return o


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", required=True)
    ap.add_argument("--to", dest="end", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args(argv)
    s = load_settings().for_pair("GBPUSD")
    side = s.chart.price
    t0 = time.time()
    fh = FastHistory(s, STORE)
    print(f"loaded in {time.time() - t0:.1f}s: {len(fh.h1_all)} hourly candles", file=sys.stderr)
    start, end = parse_iso(a.start + "T00:00:00Z"), parse_iso(a.end + "T23:59:59Z")
    out = Path(a.out).open("w")
    n = 0
    t0 = time.time()
    for k, c in enumerate(fh.h1_all):
        if not (start <= c.end <= end):
            continue
        as_of = c.end + timedelta(seconds=5)
        m = fh.moment(as_of)
        if m is None or m.inputs.adr is None:
            continue
        v = assess_phase(s, m.inputs)
        dirs = {name: dominant(s, m.inputs.h4, m.inputs.h4_swings, m.inputs.adr, p).direction for name, p in VARIANTS.items()}
        ct = v.countertrend or {}
        fm = ct.get("first_meaningful") or {}
        tz = v.facts.get("testing_zone")
        rec = {"t": as_of.strftime("%Y-%m-%dT%H:%M:%SZ"), "uk_hour": as_of.astimezone(UK).hour + as_of.astimezone(UK).minute / 60,
               "weekday": as_of.astimezone(UK).weekday(), "price": float(m.price), "adr": float(m.inputs.adr),
               "v1": v.direction.v1_direction, "dir": v.direction.direction, "dirs": dirs, "score": v.direction.score,
               "svote": v.direction.structure_vote, "marginal": bool(v.direction.marginal), "bos": bool(v.direction.break_of_structure),
               "phase": v.phase, "opp": v.opportunity, "opp_trade": v.opportunity_trade,
               "ex": [k2 for k2, x in v.exhaustion.items() if x], "E": f(v.facts.get("impulse_extreme") and Decimal(v.facts["impulse_extreme"])),
               "C": f(v.facts.get("corrective_extreme") and Decimal(v.facts["corrective_extreme"])),
               "e_utc": v.facts.get("impulse_extreme_utc"), "hours_since": v.facts.get("hours_since_extreme"),
               "recent": v.facts.get("recent_extreme"), "context": v.facts.get("exhaustion_context"),
               "impulse_start": v.facts.get("impulse_start"),
               "fm_low": f(fm.get("low") and Decimal(fm["low"])), "fm_high": f(fm.get("high") and Decimal(fm["high"])),
               "dest": f(ct.get("corrective_destination") and Decimal(ct["corrective_destination"])),
               "room": f(ct.get("room_pips_after_spread") and Decimal(ct["room_pips_after_spread"])),
               "room_ok": ct.get("room_sufficient"), "spent": ct.get("spent", False),
               "inval": f(ct.get("invalidation_price") and Decimal(ct["invalidation_price"])),
               "testing": tz, "cont_inval": f((v.continuation or {}).get("invalidation_price") and Decimal(v.continuation["invalidation_price"])),
               "obstacle": f(((ct.get("first_obstacle") or {}).get("price")) and Decimal(ct["first_obstacle"]["price"])),
               "e21": f(m.inputs.h1.ema_now(21)),
               "bmid": f(m.inputs.h1.band[m.inputs.h1.candles[-1].start].middle) if m.inputs.h1.candles[-1].start in m.inputs.h1.band else None,
               "spread": f(m.inputs.spread)}
        # loose-meaningful alternative for the countertrend destination (resistance identification baseline)
        if v.phase in ("EXHAUSTION", "COUNTERTREND_CORRECTION", "TREND_IMPULSE") and v.countertrend:
            vl = assess_phase(s, m.inputs, replace(DEFAULT, strict_meaningful=False))
            ctl = vl.countertrend or {}
            fml = ctl.get("first_meaningful") or {}
            rec["fm_low_loose"] = f(fml.get("low") and Decimal(fml["low"]))
            rec["fm_high_loose"] = f(fml.get("high") and Decimal(fml["high"]))
        rec.update(outcomes(fh.h1_all, k + 1, m.price, m.inputs.adr, side))
        out.write(json.dumps(rec) + "\n")
        n += 1
        if n % 500 == 0:
            print(f"{n} points, {as_of:%Y-%m-%d}, {(time.time() - t0) / n:.3f}s each", file=sys.stderr)
            out.flush()
        if a.limit and n >= a.limit:
            break
    out.close()
    print(f"done: {n} points in {time.time() - t0:.0f}s", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
