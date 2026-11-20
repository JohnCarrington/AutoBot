"""Score collected STP plans against the candles that came AFTER each plan. READ ONLY; no fills, no P&L.

  python -m research.stp_validation.score --store S --plans a.jsonl.gz b.jsonl.gz --out scored.jsonl.gz

Price basis: the chart price the planner uses ([chart] price = sell/bid). Touches use 5-minute highs/lows; the zone
break (planner invalidation 1) uses HOURLY closes only; the structure break (invalidation 2) uses 4-HOUR closes only,
4-hour candles built from hourly ones with the planner's own planner.measure.four_hour_from_hourly. Events with the
same closing time are treated as simultaneous (no order is invented inside a candle).

Observation stops at the FIRST missing 5-minute slot the bot's market hours say should exist (coverage_end): nothing
after a gap is used, so a gap can never hide a touch. The horizons are measurement windows, never trade expiries.
"""
from __future__ import annotations

import argparse
import bisect
import gzip
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from config.settings_loader import load_settings
from planner.measure import four_hour_from_hourly
from prices.calendar import MarketHours
from prices.model import parse_iso
from prices.store import CandleStore

UTC = timezone.utc
HORIZONS_H = (24, 72, 120, 240)
MAX_H = max(HORIZONS_H)


class Market:
    """The whole history once, as plain floats on the sell side, plus the missing open 5-minute slots."""

    def __init__(self, settings, store: CandleStore):
        self.ppp = float(Decimal(settings.market.points_per_pip))
        five = [c for d in store.days("5m") for c in store.read_day("5m", d)]
        hourly = [c for d in store.days("1h") for c in store.read_day("1h", d)]
        four = four_hour_from_hourly(settings, hourly, hourly[-1].end)
        self.m5 = self._arr(five)
        self.h1 = self._arr(hourly)
        self.h4 = self._arr(four)
        hours = MarketHours(settings.market_hours)
        have = {c.start for c in five}
        missing = [s for s in hours.open_slots(five[0].start, five[-1].end) if s not in have]
        # The 2024-26 sources open about an hour after the bot's Sunday open (vendor/IG 161 start at 17:00 New York):
        # a run of at most 13 missing slots starting AT the weekly open is that offset, not a hole inside trading,
        # and does not stop observation. Every other missing slot does (documented in the data-quality report).
        runs: list[list] = []
        for s in missing:
            if runs and s - runs[-1][-1] <= timedelta(minutes=5):
                runs[-1].append(s)
            else:
                runs.append([s])
        self.weekly_open_offsets = 0
        kept = []
        for r in runs:
            at_open = hours.session(r[0])[0] == r[0] and r[0].weekday() == 6
            if at_open and len(r) <= 13:
                self.weekly_open_offsets += 1
                continue
            kept.extend(r)
        self.missing = [s.timestamp() for s in kept]
        self.last_end = five[-1].end.timestamp()

    @staticmethod
    def _arr(cs):
        return {"start": [c.start.timestamp() for c in cs], "end": [c.end.timestamp() for c in cs],
                "hi": [float(c.sell_high) for c in cs], "lo": [float(c.sell_low) for c in cs],
                "cl": [float(c.sell_close) for c in cs]}

    def coverage_end(self, t0: float) -> float:
        """The end of contiguous 5-minute coverage after t0 (start of the first missing open slot, or the store end)."""
        i = bisect.bisect_left(self.missing, t0)
        return min(self.missing[i], self.last_end) if i < len(self.missing) else self.last_end

    def price_at(self, t0: float) -> float | None:
        i = bisect.bisect_right(self.m5["end"], t0) - 1
        return self.m5["cl"][i] if i >= 0 and self.m5["end"][i] == t0 else None

    def window(self, a: dict, t0: float, t1: float) -> range:
        i0 = bisect.bisect_left(a["start"], t0)
        i1 = bisect.bisect_right(a["end"], t1)
        return range(i0, max(i0, i1))


def _f(x) -> float:
    return float(Decimal(str(x)))


def trace(m: Market, bear: bool, t0: float, entry: tuple[float, float] | None, dest: tuple[float, float] | None,
          zone_break: float | None, struct_break: float | None, price0: float) -> dict:
    """First-event times (epoch s, candle END times) and excursions over [t0, min(t0+MAX_H, coverage_end)]."""
    cov = m.coverage_end(t0)
    t1 = min(t0 + MAX_H * 3600, cov)
    ev = {"coverage_end": cov, "observed_until": t1}
    # hourly / 4-hour invalidation closes
    def first_close(a, level):
        if level is None:
            return None
        for i in m.window(a, t0, t1):
            c = a["cl"][i]
            if (c >= level) if bear else (c <= level):
                return a["end"][i]
        return None
    ev["t_inv_h1"] = first_close(m.h1, zone_break)
    ev["t_inv_h4"] = first_close(m.h4, struct_break)
    inv = [t for t in (ev["t_inv_h1"], ev["t_inv_h4"]) if t is not None]
    ev["t_inv"] = min(inv) if inv else None
    t_entry = t_dest = t_corr50 = None
    in_entry_now = entry is not None and entry[0] <= price0 <= entry[1]
    need = None
    if entry is not None and not in_entry_now:
        need = (entry[0] - price0) if bear else (price0 - entry[1])          # countermove to the near edge (points)
    max_counter = 0.0          # max move against the trade direction, before the destination (or window end)
    max_counter_any = 0.0      # ... over the whole observed window
    max_fav = 0.0              # max move in the trade direction over the whole window
    closest_dest = None        # nearest approach to the destination's near edge (points; <=0 means touched)
    for i in m.window(m.m5, t0, t1):
        hi, lo, end = m.m5["hi"][i], m.m5["lo"][i], m.m5["end"][i]
        counter = (hi - price0) if bear else (price0 - lo)
        fav = (price0 - lo) if bear else (hi - price0)
        max_counter_any = max(max_counter_any, counter)
        max_fav = max(max_fav, fav)
        if dest is not None:
            gap = (lo - dest[1]) if bear else (dest[0] - hi)
            closest_dest = gap if closest_dest is None else min(closest_dest, gap)
        if t_dest is None:
            max_counter = max(max_counter, counter)
            if need is not None and need > 0 and t_corr50 is None and counter >= 0.5 * need:
                t_corr50 = end
        if entry is not None and t_entry is None and lo <= entry[1] and hi >= entry[0]:
            t_entry = end
        if dest is not None and t_dest is None and lo <= dest[1] and hi >= dest[0]:
            t_dest = end
    if in_entry_now:
        t_entry = t0
    # rejection proxy after the entry touch: the first HOURLY close back on the trade side of the entry zone
    t_reject = None
    if entry is not None and t_entry is not None:
        for i in m.window(m.h1, t_entry - 3600 + 1, t1):
            if m.h1["end"][i] < t_entry:
                continue
            c = m.h1["cl"][i]
            if (c < entry[0]) if bear else (c > entry[1]):
                t_reject = m.h1["end"][i]
                break
    p = m.ppp
    ev.update({
        "t_entry": t_entry, "t_dest": t_dest, "t_corr50": t_corr50, "t_reject": t_reject,
        "in_entry_at_as_of": in_entry_now,
        "need_pips": None if need is None else round(need / p, 1),
        "max_counter_before_dest_pips": round(max_counter / p, 1),
        "max_counter_pips": round(max_counter_any / p, 1), "max_fav_pips": round(max_fav / p, 1),
        "closest_dest_pips": None if closest_dest is None else round(closest_dest / p, 1),
        "overshoot_far_edge_pips": (None if entry is None else
                                    round(((price0 + max_counter) - entry[1]) / p, 1) if bear else
                                    round((entry[0] - (price0 - max_counter)) / p, 1)),
    })
    return ev


def first_passage(m: Market, t0: float, price0: float, dist_pts: float, horizon_h: int) -> str:
    """UP / DOWN / BOTH_SAME_CANDLE / NONE (within horizon) / CENSORED (gap before resolution)."""
    cov = m.coverage_end(t0)
    t1 = min(t0 + horizon_h * 3600, cov)
    for i in m.window(m.m5, t0, t1):
        up = m.m5["hi"][i] >= price0 + dist_pts
        dn = m.m5["lo"][i] <= price0 - dist_pts
        if up and dn:
            return "BOTH_SAME_CANDLE"
        if up:
            return "UP"
        if dn:
            return "DOWN"
    return "CENSORED" if cov < t0 + horizon_h * 3600 else "NONE"


def net_change(m: Market, t0: float, price0: float, horizon_h: int) -> float | None:
    t1 = t0 + horizon_h * 3600
    if m.coverage_end(t0) < t1:
        return None
    i = bisect.bisect_right(m.m5["end"], t1) - 1
    return round((m.m5["cl"][i] - price0) / m.ppp, 1) if i >= 0 else None


def sequence_class(ev: dict, t0: float, horizon_h: int) -> str:
    """The anticipated journey's outcome by horizon_h (measurement window only)."""
    t1 = t0 + horizon_h * 3600
    def by(t):
        return t is not None and t <= t1
    te, td, ti = ev["t_entry"], ev["t_dest"], ev["t_inv"]
    te = te if by(te) else None
    td = td if by(td) else None
    ti = ti if by(ti) else None
    censored = ev["observed_until"] < t1
    if te is None:
        if td is not None and (ti is None or td < ti):
            return "DESTINATION_WITHOUT_CORRECTION"
        if td is not None and ti is not None and td == ti:
            return "AMBIGUOUS"
        if ti is not None:
            return "INVALIDATED_BEFORE_ENTRY"
        return "CENSORED_NO_EVENT" if censored else "NO_EVENT"
    if td is not None and td < te:
        return "DESTINATION_WITHOUT_CORRECTION"
    if td is not None and td == te and not ev["in_entry_at_as_of"]:
        return "AMBIGUOUS"
    if ti is not None and ti < te:
        return "INVALIDATED_BEFORE_ENTRY"
    if td is not None and (ti is None or td < ti):
        return "ENTRY_THEN_DESTINATION"
    if td is not None and ti is not None and td == ti:
        return "AMBIGUOUS"
    if ti is not None:
        return "ENTRY_THEN_INVALIDATION"
    return "CENSORED_ENTRY_ONLY" if censored else "ENTRY_ONLY"


def score_plan(m: Market, p: dict, beyond_pts: float) -> dict:
    t0 = parse_iso(p["as_of_utc"]).timestamp()
    price0 = m.price_at(t0)
    out = {"as_of_utc": p["as_of_utc"], "fresh": p.get("fresh"), "direction": p.get("dominant_direction"),
           "condition": p.get("condition"), "trade": p.get("trade"), "price": price0,
           "adr_pips": (p.get("observations") or {}).get("adr_pips"),
           "no_recommendation": p.get("no_recommendation")}
    if p.get("error") or price0 is None or not p.get("fresh"):
        out["status"] = "ERROR" if p.get("error") else "STALE_OR_NO_PRICE"
        return out
    adr = _f(out["adr_pips"]) if out["adr_pips"] not in (None, "") else None
    # A. direction (every BULLISH/BEARISH decision, with or without a trade plan); the same measure is kept for every
    # decision so a base rate is available
    fp = {}
    for name, dist in (("half_adr", None if adr is None else 0.5 * adr * m.ppp), ("25p", 25 * m.ppp)):
        if dist:
            for h in (24, 72, 120):
                fp[f"{name}_{h}h"] = first_passage(m, t0, price0, dist, h)
    out["first_passage"] = fp
    out["net_pips"] = {f"{h}h": net_change(m, t0, price0, h) for h in (24, 72, 120)}
    ob = p.get("observations") or {}
    out["dir_context"] = {"daily_structure": (ob.get("daily_structure") or "").split(":")[0] or None,
                          "h4_ema_stack": ob.get("h4_ema_stack"), "impulse_adr": ob.get("impulse_adr"),
                          "distance_from_h4_ema21_adr": ob.get("distance_from_h4_ema21_adr"),
                          "h4_sweep_state": (ob.get("h4_sweep") or {}).get("state"),
                          "hours_since_last_h4_swing": (
                              None if not (p.get("h4_last_swing") or {}).get("candle_utc") else
                              round((t0 - parse_iso(p["h4_last_swing"]["candle_utc"]).timestamp()) / 3600, 1)),
                          "condition_unclassified": p.get("condition_unclassified")}
    if p.get("trade") not in ("BUY", "SELL") or not p.get("entry_zone"):
        out["status"] = "NO_PLAN"
        return out
    bear = p["trade"] == "SELL"
    ez = p["entry_zone"]
    entry = (_f(ez["low"]), _f(ez["high"]))
    prim = (p.get("destinations") or {}).get("primary") or {}
    pz = prim.get("zone") or {}
    dest = (_f(pz["low"]), _f(pz["high"])) if pz else None
    inv = p.get("invalidation") or {}
    zb = _f(inv["zone_break_close"]) if inv.get("zone_break_close") else None
    sb = _f(inv["structure_break_close"]) if inv.get("structure_break_close") else None
    ev = trace(m, bear, t0, entry, dest, zb, sb, price0)
    sel = (p.get("observations") or {}).get("destination_first_selection") or {}
    journeys = (p.get("observations") or {}).get("conditional_journeys") or []
    chosen = next((j for j in journeys if j.get("entry") == [ez["low"], ez["high"]]), {})
    out.update({
        "status": "PLAN", "entry": entry, "dest": dest,
        "dest_ahead_of_price": dest is not None and ((price0 > dest[1]) if bear else (price0 < dest[0])),
        "entry_class": ez.get("class"), "dest_class": pz.get("class"),
        "selection_mode": sel.get("mode"), "countermove_state": chosen.get("countermove_evidence_state"),
        "extended": ((p.get("destinations") or {}).get("extended") or {}).get("zone"),
        "intermediate": ((p.get("destinations") or {}).get("intermediate") or {}).get("zone"),
        "zone_break": zb, "structure_break": sb, "events": ev,
        "sequence": {f"{h}h": sequence_class(ev, t0, h) for h in HORIZONS_H},
    })
    # context already known at as_of (past candles only): was the destination / entry already touched?
    def touched_between(zone, a, b):
        if zone is None:
            return None
        return any(m.m5["lo"][i] <= zone[1] and m.m5["hi"][i] >= zone[0] for i in m.window(m.m5, a, b))
    sw = p.get("h4_last_swing") or {}
    sw_t = parse_iso(sw["candle_utc"]).timestamp() if sw.get("candle_utc") else None
    o = p.get("observations") or {}
    out["past"] = {
        "dest_touched_prior_24h": touched_between(dest, t0 - 86400, t0),
        "dest_touched_since_last_h4_swing": None if sw_t is None else touched_between(dest, sw_t, t0),
        "entry_touched_prior_24h": touched_between(entry, t0 - 86400, t0),
        "hours_since_last_h4_swing": None if sw_t is None else round((t0 - sw_t) / 3600, 1),
    }
    out["context"] = {k: o.get(k) for k in (
        "daily_structure", "distance_from_h4_ema21_adr", "distance_from_h4_ema100_adr", "today_range_adr",
        "impulse_adr", "h4_rsi", "h4_ema_stack", "vs_daily_pivot", "vs_weekly_pivot", "reward_to_invalidation")}
    out["context"]["h4_sweep_state"] = (o.get("h4_sweep") or {}).get("state")
    out["context"]["entry_reachability"] = p.get("reachability")
    out["context"]["dest_families"] = pz.get("families")
    out["context"]["dest_levels"] = [x if isinstance(x, str) else f"{x.get('name')} {x.get('price')}"
                                     for x in pz.get("levels") or []]
    out["context"]["entry_levels"] = [x if isinstance(x, str) else f"{x.get('name')} {x.get('price')}"
                                      for x in ez.get("levels") or []]
    # mirror baseline for the destination: would price have gone as far the OTHER way?
    if dest is not None:
        d_pts = (price0 - dest[1]) if bear else (dest[0] - price0)
        if d_pts > 0:
            mir = {}
            for h in HORIZONS_H:
                r = first_passage(m, t0, price0, d_pts, h)
                mir[f"{h}h"] = r
            out["dest_distance_pips"] = round(d_pts / m.ppp, 1)
            out["dest_first_passage"] = mir     # UP/DOWN: which of +-dest distance came first
    # alternatives (offline comparison only): the extended Major destination, and the entry-first choice
    alts = {}
    if out["extended"]:
        xz = out["extended"]
        alts["extended_dest"] = trace(m, bear, t0, entry, (_f(xz["low"]), _f(xz["high"])), zb, sb, price0)
    eligible = [j for j in journeys if j.get("decision") == "eligible"]
    if eligible and eligible[0].get("entry") != [ez["low"], ez["high"]]:
        j = eligible[0]
        e2 = (_f(j["entry"][0]), _f(j["entry"][1]))
        d2 = (_f(j["destination"][0]), _f(j["destination"][1]))
        zb2 = (e2[1] + beyond_pts) if bear else (e2[0] - beyond_pts)
        alts["entry_first"] = trace(m, bear, t0, e2, d2, zb2, sb, price0) | {"entry": e2, "dest": d2}
    if alts:
        out["alternatives"] = {k: v | {"sequence": {f"{h}h": sequence_class(v, t0, h) for h in HORIZONS_H}}
                               for k, v in alts.items()}
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True, type=Path)
    ap.add_argument("--plans", required=True, nargs="+", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    settings = load_settings().for_pair("GBPUSD")
    m = Market(settings, CandleStore(a.store, settings.candles.compress_after_days))
    beyond = float(Decimal(settings.planner.break_beyond_pips) * Decimal(settings.market.points_per_pip))
    n = 0
    with gzip.open(a.out, "wt") as f:
        for path in a.plans:
            with gzip.open(path, "rt") as g:
                for line in g:
                    p = json.loads(line)
                    f.write(json.dumps(score_plan(m, p, beyond)) + "\n")
                    n += 1
    print(f"scored {n} plans -> {a.out}")


if __name__ == "__main__":
    main()
