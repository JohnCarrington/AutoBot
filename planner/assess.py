"""The planner's assessment at one moment: direction, condition, opportunity, zone, destinations, invalidation
(Structural Trade Planner V1; approved 17 November 2026; OBSERVE ONLY: it decides nothing about any trade).

Written for a BEARISH market; BULLISH is the mirror image throughout.

DIRECTION (D-03, P-B10/B11): the 4-hour structure decides.
  BEARISH       lower highs and lower lows, and no confirmed 4-hour close above the last lower high since;
  BULLISH       the mirror image;
  TRANSITIONAL  the structure is still down (up) but a confirmed 4-hour close went beyond the last opposite swing;
  NEUTRAL       mixed swings, or too few.
  The structure used is planner/structure.py dominant_structure (candidate C, owner's approval of 19 November 2026):
  the observed swings, except that a wick-only sweep of an established trend is "unresolved" (NEUTRAL) until a
  confirmed 4-hour close beyond the last swing on the other side rejects it (the trend is restored); a confirmed
  close beyond the swept swing makes the higher high (lower low) real and the observed mixed sequence stands.
  Daily and weekly are context (shown, never deciding). The 4-hour EMA100 slope (P-D1) and EMA stack support.

CONDITION (D-10; FC-12; P-D6, P-D9), from the 4-hour RSI 3, MACD 35/45/30 and Bollinger (P-D7: the 4-hour decides).
The current impulse runs from the last confirmed 4-hour swing high to now (P-D8); its extreme includes the hourly
candles finished since the last 4-hour candle.
  REVERSAL_RISK      the 4-hour MACD line CROSSING above zero during the current 4-hour structure (it was below zero
                     at some 4-hour close since the structure's first swing and is above it now), or a confirmed
                     daily break upwards. A MACD line still above zero from before the downtrend (it has not yet
                     fallen below zero since the structure began) is recorded as momentum not yet confirming the
                     structure: supporting evidence only, never a veto (correction of 17 November 2026: the approved
                     D-10 wording is "crossing", and the 4-hour structure is the directional authority);
  CORRECTION_ACTIVE  after the impulse low: an hourly close above the hourly Bollinger middle, or an hourly swing low
                     above the impulse low (structure still bearish);
  CORRECTION_LIKELY  EXHAUSTION, and none of the last planner.no_new_extreme_hourly_candles (3) hourly candles made a
                     new low;
  EXHAUSTION         a new low in the impulse (below the swing low before it), and momentum not confirming it (the
                     4-hour histogram rising towards zero for planner.macd_weakening_candles (3) candles in a row while
                     below zero, or a higher MACD line at the new low than at the previous swing low), and at least one
                     of: RSI 3 back above its lower line after being below it in the impulse; a 4-hour close back inside
                     the lower band after a close below it in the impulse;
  CONTINUATION       a new low in the impulse, the histogram below zero and falling, the close below the middle band;
  INDETERMINATE      otherwise, or the 4-hour MACD, RSI or Bollinger not warmed up. "Otherwise" (data ready, no recipe
                     matched) is marked condition_unclassified: it stops a NEW recommendation, but a live one keeps
                     its structural basis and is kept (planner/keeper.py; owner's approval of 19 November 2026).
OPPORTUNITY TYPE (D-16, modified; FC-04 exactly, owner's R1 of 17 November 2026): a label only, by condition class:
"healthy-trend pullback" for CONTINUATION; "corrective reversal" for EXHAUSTION, CORRECTION_LIKELY or
CORRECTION_ACTIVE. Zone choice, invalidation and everything else are the same for both. No
opportunity in REVERSAL_RISK or INDETERMINATE, or when the direction is not BEARISH or BULLISH.

REACHABILITY (D-14 modified, D-15; FC-03): for each resistance zone above price (or containing it):
  UNLIKELY  wholly above the last 4-hour lower high (reaching it would break the structure);
  NEAR      price inside it, or no more than rejection.near_level_within_pips (3) below it;
  EXTENDED  a Major zone lies in between;
  PLAUSIBLE otherwise.
  Distance (pips and ADR) and today's remaining room are recorded as context only; ADR never rules a zone out.
ENTRY ZONE (D-16, FC-03): among NEAR or PLAUSIBLE zones of at least planner.min_entry_class: the strongest class;
if tied, the nearer. Reference entry: the zone's most significant level (D-17).
DESTINATIONS (D-18, D-19): the support zones below the entry zone, nearest first: intermediate = the first; primary =
the first Major; extended = the next Major. Each at the zone's near edge (its top, for a sell). No primary: no
recommendation.
INVALIDATION (D-20, FC-02): an hourly close at least planner.break_beyond_pips (3) above the zone top; a 4-hour
close at least 3 pips above the last lower high; the 4-hour direction no longer BEARISH; price reaching the primary
destination before the zone.
Missing data or indicators: no recommendation, with the reason (D-27). Nothing is guessed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from planner.measure import Snapshot, cl, hi, lo, op, pips, ppp, side_of, snapshot
from planner.structure import DOWN, MIXED, UP, Structure, dominant_structure, structure, swings, threshold_misses
from planner.zones import CLASS_RANK, MAJOR, Zone, ahead, interacts, label, level_map, reached, zones
from prices.model import UK, plain, uk_short

BULLISH, BEARISH, NEUTRAL, TRANSITIONAL, INDETERMINATE_DIR = "BULLISH", "BEARISH", "NEUTRAL", "TRANSITIONAL", "INDETERMINATE"
CONTINUATION, EXHAUSTION, CORRECTION_LIKELY, CORRECTION_ACTIVE, REVERSAL_RISK, INDETERMINATE = (
    "CONTINUATION", "EXHAUSTION", "CORRECTION_LIKELY", "CORRECTION_ACTIVE", "REVERSAL_RISK", "INDETERMINATE")
NEAR, PLAUSIBLE, EXTENDED, UNLIKELY = "NEAR", "PLAUSIBLE", "EXTENDED", "UNLIKELY"
CORRECTIVE, PULLBACK = "corrective reversal", "healthy-trend pullback"
OPPORTUNITY_CLASSES = (CONTINUATION, EXHAUSTION, CORRECTION_LIKELY, CORRECTION_ACTIVE)


@dataclass
class Plan:
    """Everything the planner concluded at one moment (as_of), with the evidence."""
    pair: str
    as_of: datetime
    market_data_utc: datetime | None
    fresh: bool
    direction: str
    direction_evidence: list[str]
    condition: str
    condition_evidence: list[str]
    opportunity: str | None = None
    trade: str | None = None                    # "SELL" or "BUY"
    expected_movement: str | None = None
    zone: Zone | None = None
    reachability: str | None = None
    selection_reason: str = ""
    destinations: dict = field(default_factory=dict)        # intermediate / primary / extended
    invalidation: dict = field(default_factory=dict)
    observations: dict = field(default_factory=dict)
    candidates: list[dict] = field(default_factory=list)    # every zone looked at, and why it won or lost
    alternative: dict | None = None
    no_recommendation: str | None = None
    warming_up: list[str] = field(default_factory=list)
    threshold_misses: list[dict] = field(default_factory=list)
    h4_last_swing: dict | None = None
    destination_reached: dict | None = None     # D-1 correction: the primary destination was already reached
    condition_unclassified: bool = False        # INDETERMINATE only because no class recipe matched (data ready)
    structure: dict | None = None               # reporting only: every level, zone and swing the plan saw

    @property
    def recommends(self) -> bool:
        return self.no_recommendation is None and self.zone is not None

    def as_dict(self) -> dict:
        z = self.zone
        return {
            "pair": self.pair, "as_of_utc": _iso(self.as_of), "market_data_utc": _iso(self.market_data_utc),
            "fresh": self.fresh, "dominant_direction": self.direction, "direction_evidence": self.direction_evidence,
            "condition": self.condition, "condition_evidence": self.condition_evidence,
            "opportunity": self.opportunity, "trade": self.trade, "expected_movement": self.expected_movement,
            "entry_zone": None if z is None else z.as_dict(),
            "reference_entry": None if z is None or z.reference is None else
            {"price": plain(z.reference.price), "level": z.reference.name},
            "reachability": self.reachability, "selection_reason": self.selection_reason,
            "destinations": self.destinations, "invalidation": self.invalidation, "observations": self.observations,
            "candidates": self.candidates, "alternative": self.alternative,
            "no_recommendation": self.no_recommendation, "warming_up": self.warming_up,
            "threshold_misses": self.threshold_misses, "h4_last_swing": self.h4_last_swing,
            "destination_reached": self.destination_reached, "structure": self.structure,
            "condition_unclassified": self.condition_unclassified,
        }


def _iso(t: datetime | None) -> str | None:
    return None if t is None else t.strftime("%Y-%m-%dT%H:%M:%SZ")


# ---- direction -----------------------------------------------------------------------------------------------------

def direction(settings: Any, st: Structure) -> tuple[str, list[str]]:
    ev = [f"4-hour structure: {st.why}"]
    if st.sequence == MIXED:
        return NEUTRAL, ev
    if st.broken is not None:
        way, c, sw = st.broken
        ev.append(f"confirmed 4-hour close {plain(cl(c, side_of(settings)))} ({uk_short(c.start)}) "
                  f"{'above' if way == UP else 'below'} the last swing {sw.kind} {plain(sw.price)}: structure broken")
        return TRANSITIONAL, ev
    return (BEARISH if st.sequence == DOWN else BULLISH), ev


# ---- helpers in the dominant direction -------------------------------------------------------------------------------
# For a BEARISH market "further" means lower; the code below works in that orientation via these helpers.

def _further(bear: bool, a: Decimal, b: Decimal) -> bool:
    """a is further in the dominant direction than b (lower for bearish, higher for bullish)."""
    return a < b if bear else a > b


def _extreme(bear: bool, c: Any, side: str) -> Decimal:
    return lo(c, side) if bear else hi(c, side)


def _counter_extreme(bear: bool, c: Any, side: str) -> Decimal:
    return hi(c, side) if bear else lo(c, side)


# ---- condition -----------------------------------------------------------------------------------------------------

def condition(settings: Any, snap: Snapshot, st: Structure, d1: Structure, h1_swings: list) -> tuple[str, list[str], dict]:
    side = side_of(settings)
    h4, h1 = snap.h4, snap.h1
    missing = [n for n in ("MACD", "RSI", "Bollinger") if not h4.ready(n)]
    if missing:
        return INDETERMINATE, [f"4-hour {', '.join(missing)} not warmed up"], {}
    bear = st.sequence == DOWN
    lower_line, upper_line = Decimal(settings.indicators.rsi_lower_line), Decimal(settings.indicators.rsi_upper_line)
    cs = h4.candles
    start = (st.highs if bear else st.lows)[-1]                 # the last confirmed opposite swing: impulse start
    impulse = cs[start.index + 1:]
    if not impulse:
        return INDETERMINATE, ["no 4-hour candle since the last confirmed opposite swing"], {}
    later_h1 = [c for c in h1.candles if c.start >= cs[-1].end]
    pool = list(impulse) + later_h1
    ext_c = min(pool, key=lambda c: lo(c, side)) if bear else max(pool, key=lambda c: hi(c, side))
    if ext_c.timeframe == "4h":                                 # the hourly candle inside it that made the extreme
        inner = [c for c in h1.candles if ext_c.start <= c.start < ext_c.end]
        if inner:
            ext_h1 = min(inner, key=lambda c: lo(c, side)) if bear else max(inner, key=lambda c: hi(c, side))
        else:
            ext_h1 = ext_c
    else:
        ext_h1 = ext_c
    ext = _extreme(bear, ext_c, side)
    before = [s for s in (st.lows if bear else st.highs) if s.candle_utc < start.candle_utc]
    prev = before[-1] if before else None
    new_extreme = prev is not None and _further(bear, ext, prev.price)
    hist = [h4.macd[c.start].histogram for c in cs if c.start in h4.macd]
    line_now = h4.macd[cs[-1].start].line
    n = settings.planner.macd_weakening_candles
    toward = len(hist) > n and all((hist[-k] > hist[-k - 1]) if bear else (hist[-k] < hist[-k - 1]) for k in range(1, n + 1))
    weakening = toward and (hist[-1] < 0 if bear else hist[-1] > 0)
    away = len(hist) >= 2 and ((hist[-1] < hist[-2] and hist[-1] < 0) if bear else (hist[-1] > hist[-2] and hist[-1] > 0))
    divergence = False
    if new_extreme and ext_c.start in h4.macd and prev is not None and prev.candle_utc in h4.macd:
        a, b = h4.macd[ext_c.start].line, h4.macd[prev.candle_utc].line
        divergence = (a > b) if bear else (a < b)
    rsi_imp = [h4.rsi[c.start] for c in impulse if c.start in h4.rsi]
    rsi_now = h4.rsi.get(cs[-1].start)
    rsi_back = bool(rsi_imp) and rsi_now is not None and (
        (any(r < lower_line for r in rsi_imp) and rsi_now >= lower_line) if bear else
        (any(r > upper_line for r in rsi_imp) and rsi_now <= upper_line))
    band_now = h4.band.get(cs[-1].start)
    outside = [c for c in impulse if c.start in h4.band and (
        cl(c, side) < h4.band[c.start].lower if bear else cl(c, side) > h4.band[c.start].upper)]
    band_back = bool(outside) and band_now is not None and (
        cl(cs[-1], side) >= band_now.lower if bear else cl(cs[-1], side) <= band_now.upper)
    beyond_mid = band_now is not None and (cl(cs[-1], side) < band_now.middle if bear else cl(cs[-1], side) > band_now.middle)
    k = settings.planner.no_new_extreme_hourly_candles
    lastk = h1.candles[-k:]
    no_new = len(lastk) == k and all(_further(bear, ext, _extreme(bear, c, side)) for c in lastk)
    after_ext = [c for c in h1.candles if c.start > ext_h1.start]
    h1_mid_cross = [c for c in after_ext if c.start in h1.band and (
        cl(c, side) > h1.band[c.start].middle if bear else cl(c, side) < h1.band[c.start].middle)]
    h1_turn = [s for s in h1_swings if s.kind == ("low" if bear else "high") and s.candle_utc >= (after_ext[0].start if after_ext else snap.as_of)
               and _further(bear, ext, s.price)]
    daily_against = d1.broken is not None and d1.broken[0] == (UP if bear else DOWN)
    word = "low" if bear else "high"
    facts = {"impulse_start": start.describe(), "impulse_extreme": plain(ext), "impulse_extreme_utc": _iso(ext_c.start),
             "new_extreme": new_extreme, "histogram_weakening": weakening, "histogram_moving_away": away,
             "divergence": divergence, "rsi_back_inside": rsi_back, "band_back_inside": band_back,
             "close_beyond_middle": beyond_mid, "no_new_extreme_hourly": no_new,
             "impulse_size_points": abs(start.price - ext)}
    ev = [f"impulse from the {start.describe()} to the {word} {plain(ext)} ({uk_short(ext_c.start)})",
          (f"new {word}: {plain(ext)} beyond the previous swing {word} {plain(prev.price)}" if new_extreme else
           f"no new {word} beyond the previous swing {word}" + (f" {plain(prev.price)}" if prev else " (none)")),
          f"4-hour MACD line {plain(line_now.quantize(Decimal('0.01')))}, histogram {plain(hist[-1].quantize(Decimal('0.01')))}"
          + (f", moving towards zero for {n} candles (momentum weakening)" if weakening else
             ", moving away from zero" if away else ""),
          f"4-hour RSI {plain(rsi_now.quantize(Decimal('0.1')))}" + (" (back inside its line after the impulse)" if rsi_back else "")]
    if divergence:
        ev.append(f"divergence: MACD line higher at the new {word} than at the previous swing {word}" if bear else
                  f"divergence: MACD line lower at the new {word} than at the previous swing {word}")
    if band_back:
        ev.append("4-hour close back inside the Bollinger band after closing outside it in the impulse")
    exhausted_momentum = new_extreme and (weakening or divergence)
    exhaustion = exhausted_momentum and (rsi_back or band_back)
    facts["momentum_not_confirming"] = exhausted_momentum
    crossed, not_yet = macd_against(h4, st, bear)
    facts["macd_crossed_against"], facts["macd_not_yet_confirming"] = crossed, not_yet
    if not_yet:
        ev.append(f"4-hour MACD line still {'above' if bear else 'below'} zero: momentum has not yet confirmed the new "
                  f"4-hour {'down' if bear else 'up'}trend (supporting evidence only, not a veto)")
    if crossed or daily_against:
        why = []
        if crossed:
            why.append(f"the 4-hour MACD line crossed {'above' if bear else 'below'} zero during this 4-hour "
                       f"{'down' if bear else 'up'}trend")
        if daily_against:
            why.append(f"a confirmed daily close {'above' if bear else 'below'} the last daily swing")
        return REVERSAL_RISK, ev + ["reversal risk: " + "; ".join(why)], facts
    if h1_mid_cross or h1_turn:
        what = (f"an hourly close {'above' if bear else 'below'} the hourly Bollinger middle "
                f"({uk_short(h1_mid_cross[0].start)})" if h1_mid_cross else f"an hourly swing {h1_turn[0].kind} {plain(h1_turn[0].price)}")
        return CORRECTION_ACTIVE, ev + [f"correction under way: {what} after the impulse {word}, 4-hour structure intact"], facts
    if exhaustion and no_new:
        return CORRECTION_LIKELY, ev + [f"exhaustion, and no new {word} in the last {k} hourly candles"], facts
    if exhaustion:
        return EXHAUSTION, ev + ["exhaustion: a new extreme that momentum does not confirm"], facts
    if new_extreme and away and beyond_mid:
        return CONTINUATION, ev + [f"continuation: new {word}s, momentum building, close {'below' if bear else 'above'} the middle band"], facts
    facts["unclassified"] = True     # data ready, no class recipe matched (not "data not ready"): 19 November 2026
    return INDETERMINATE, ev + ["the evidence does not fit one condition"], facts


def choose_zone(settings: Any, zs: list[Zone], price: Decimal, bear: bool, last_opp: Any, adr: Decimal) -> tuple[list, list]:
    """Reachability of every candidate entry zone and which qualify (D-14 modified, D-15, D-16; FC-03).
    Returns (looked, good): each (zone, reachability, distance in points, info), nearest first; `good` sorted best
    first: the strongest class, then the nearer. Distance and ADR are recorded only."""
    near = Decimal(settings.rejection.near_level_within_pips) * ppp(settings)
    cands = [z for z in zs if z.low >= price - near or z.low <= price <= z.high] if bear else \
        [z for z in zs if z.high <= price + near or z.low <= price <= z.high]
    cands = sorted(cands, key=lambda z: abs((z.low if bear else z.high) - price))
    min_rank = CLASS_RANK[settings.planner.min_entry_class]
    looked, good = [], []
    for z in cands:
        inside = z.low <= price <= z.high
        dist = Decimal(0) if inside else max(Decimal(0), (z.low - price) if bear else (price - z.high))
        if (bear and z.low > last_opp.price) or (not bear and z.high < last_opp.price):
            reach = UNLIKELY
        elif inside or dist <= near:
            reach = NEAR
        elif any(o.klass == MAJOR and o is not z and ((price < o.low and o.high < z.low) if bear else (z.high < o.low and o.high < price))
                 for o in zs):
            reach = EXTENDED
        else:
            reach = PLAUSIBLE
        why = []
        if CLASS_RANK[z.klass] < min_rank:
            why.append(f"{z.klass} is below the minimum class {settings.planner.min_entry_class}")
        if reach not in (NEAR, PLAUSIBLE):
            why.append({UNLIKELY: f"beyond the last 4-hour swing {last_opp.kind} {plain(last_opp.price)}",
                        EXTENDED: "a Major zone lies in between"}[reach])
        info = {"reachability": reach, "distance_pips": plain(pips(settings, dist)),
                "distance_adr": plain((dist / adr).quantize(Decimal("0.01"))), "tests": z.tests,
                "rejected_because": "; ".join(why) or None}
        looked.append((z, reach, dist, info))
        if not why:
            good.append((z, reach, dist, info))
    good.sort(key=lambda x: (-CLASS_RANK[x[0].klass], x[2]))
    return looked, good


def opportunity_of(cond: str) -> str | None:
    """FC-04: the opportunity label from the condition class (owner's R1, 17 November 2026)."""
    if cond == CONTINUATION:
        return PULLBACK
    if cond in (EXHAUSTION, CORRECTION_LIKELY, CORRECTION_ACTIVE):
        return CORRECTIVE
    return None


def macd_against(h4: Any, st: Structure, bear: bool) -> tuple[bool, bool]:
    """(crossed, not_yet) for the 4-hour MACD line against the dominant direction (D-10, D-13):
    crossed  the line is on the opposite side of zero now, and was on the dominant side at some 4-hour close since
             the current structure's first swing (a cross during the structure: REVERSAL_RISK, as approved);
    not_yet  the line is on the opposite side now and has NOT been on the dominant side since the structure began
             (momentum lagging a structure that is already established: supporting evidence only)."""
    cs = h4.candles
    if not cs or cs[-1].start not in h4.macd:
        return False, False
    line_now = h4.macd[cs[-1].start].line
    against = line_now > 0 if bear else line_now < 0
    if not against:
        return False, False
    began = min(s.candle_utc for s in st.highs + st.lows)
    since = [h4.macd[c.start].line for c in cs if c.start >= began and c.start in h4.macd]
    confirmed = any((x < 0) if bear else (x > 0) for x in since)
    return confirmed, not confirmed


# ---- the whole plan ------------------------------------------------------------------------------------------------

def _zone_dict(z: Zone, extra: dict) -> dict:
    return {"low": plain(z.low), "high": plain(z.high), "class": z.klass, "families": z.families,
            "levels": [label(m) for m in z.members]} | extra


def assess(settings: Any, snap: Snapshot, existing_levels: Any, calendar: list | None = None,
           five_minute_rule: dict | None = None) -> Plan:
    """The plan from a snapshot (planner/measure.py) and the existing levels list (levels/current.py) at its time."""
    side = side_of(settings)
    pair = settings.market.pair
    near = Decimal(settings.rejection.near_level_within_pips) * ppp(settings)
    beyond = Decimal(settings.planner.break_beyond_pips) * ppp(settings)
    warming = [f"{f.timeframe} {w}" for f in (snap.h1, snap.h4, snap.d1, snap.w1) for w in f.warming]
    data_utc = snap.five.end if snap.five else None
    h4_found = swings(settings, snap.h4.candles, "4h")
    d1_found = swings(settings, snap.d1.candles, "1d")
    h1_found = swings(settings, snap.h1.candles[-400:], "1h")
    st = dominant_structure(settings, snap.h4.candles, "4h", h4_found)    # candidate C (19 November 2026)
    d1 = structure(settings, snap.d1.candles, "1d", d1_found)
    dirn, dir_ev = direction(settings, st)
    misses = threshold_misses(settings, snap.h4.candles, "4h", h4_found) + \
        threshold_misses(settings, snap.d1.candles, "1d", d1_found)
    plan = Plan(pair, snap.as_of, data_utc, snap.fresh, dirn, dir_ev, INDETERMINATE, [], warming_up=warming,
                threshold_misses=misses)
    plan.observations = observations(settings, snap, st, d1, existing_levels, calendar, five_minute_rule)
    if st.sweep is not None:
        plan.observations["h4_sweep"] = st.sweep
    dir_ev += plan.observations.get("supporting", [])
    if snap.price is None or snap.h4.last is None:
        plan.no_recommendation = "no finished candles to work from"
        return plan
    if dirn not in (BEARISH, BULLISH):
        unresolved = st.sweep is not None and st.sweep["state"] == "unresolved"
        plan.no_recommendation = (f"the 4-hour direction is {dirn}"
                                  + (f" (the wick-only sweep of {st.sweep['beyond']} by {st.sweep['price']} is unresolved)"
                                     if unresolved else "")
                                  + ": no recommendation until it is BEARISH or BULLISH")
        return plan
    bear = dirn == BEARISH
    last_opp = (st.highs if bear else st.lows)[-1]
    plan.h4_last_swing = {"kind": last_opp.kind, "price": plain(last_opp.price), "candle_utc": _iso(last_opp.candle_utc)}
    cond, cond_ev, facts = condition(settings, snap, st, d1, h1_found)
    plan.condition, plan.condition_evidence = cond, cond_ev
    plan.condition_unclassified = cond == INDETERMINATE and bool(facts.get("unclassified"))
    if facts.get("impulse_size_points") is not None and snap.adr:
        plan.observations["impulse_pips"] = plain(pips(settings, facts["impulse_size_points"]))
        plan.observations["impulse_adr"] = plain((facts["impulse_size_points"] / snap.adr).quantize(Decimal("0.01")))
    if cond not in OPPORTUNITY_CLASSES:
        plan.no_recommendation = f"condition {cond}: no opportunity"
        return plan
    plan.opportunity = opportunity_of(cond)
    plan.trade = "SELL" if bear else "BUY"
    plan.expected_movement = "UP into resistance, then DOWN" if bear else "DOWN into support, then UP"
    if snap.adr is None:
        plan.no_recommendation = f"no ADR yet (fewer than {settings.planner.adr_weekdays} weekday daily candles)"
        return plan
    lmap = level_map(settings, snap, existing_levels, h4_found, d1_found)
    zs = zones(settings, lmap, snap.adr, snap.h1.candles, snap.price)
    plan.structure = structure_snapshot(lmap, zs, h4_found, d1_found, h1_found)
    price = snap.price
    # candidate entry zones: above price (or containing it) for a sell; below (or containing) for a buy
    looked, good = choose_zone(settings, zs, price, bear, last_opp, snap.adr)
    if not good:
        plan.candidates = [_zone_dict(z, i) for z, _, _, i in looked]
        plan.no_recommendation = ("no defensible entry zone: no " + ("resistance" if bear else "support")
                                  + f" zone of at least {settings.planner.min_entry_class} class that is NEAR or PLAUSIBLE"
                                  + f" before the last 4-hour swing {last_opp.kind} {plain(last_opp.price)}")
        return plan
    # Destination-first view: enumerate structural destinations independently of
    # the entry ranking. This is diagnostic, not an unsupported probability forecast.
    # A destination is not an actionable prediction merely because it is Major.
    destination_outlooks = []
    for target in sorted(
        (o for o in zs if o.klass == MAJOR),
        key=lambda o: (-o.high if bear else o.low),
    ):
        potential_entries = [
            entry for entry, _, _, _ in good
            if (target.high < entry.low if bear else target.low > entry.high)
        ]
        destination_outlooks.append({
            "zone": [plain(target.low), plain(target.high)],
            "class": target.klass,
            "relative_to_price": (
                "ahead" if ahead(price, target.low, target.high, toward_low=bear)
                else "behind_or_containing_price"
            ),
            "candidate_entries": [
                [plain(entry.low), plain(entry.high)] for entry in potential_entries
            ],
            # Explicitly record the sequence PIA-style analysis would require.
            # This is a conditional scenario, not a prediction that each leg occurs.
            "journeys": [
                {
                    "sequence": (
                        ["current_price", "corrective_rally_to_entry", "sell_toward_destination"]
                        if bear else
                        ["current_price", "corrective_decline_to_entry", "buy_toward_destination"]
                    ),
                    "entry": [plain(entry.low), plain(entry.high)],
                    "destination": [plain(target.low), plain(target.high)],
                    "countermove_pips": plain(pips(
                        settings, max(Decimal(0), entry.low - price) if bear
                        else max(Decimal(0), price - entry.high)
                    )),
                    "directional_distance_pips": plain(pips(
                        settings, entry.low - target.high if bear else target.low - entry.high
                    )),
                    "conditional_only": True,
                    "invalidation_reference": plain(last_opp.price),
                }
                for entry in potential_entries
            ],
            "destination_forecast": "not established by structural eligibility alone",
            "countermove_forecast": "not established by structural eligibility alone",
        })
    plan.observations["destination_first_outlook"] = destination_outlooks
    # Research-only horizon: preserve the complete ahead-of-price support/resistance
    # ladder separately from the nearest primary target. A Major level is an
    # obstacle, NOT proof of the ultimate destination. No order or trade decision
    # is changed by this diagnostic.
    from planner.destination_hierarchy import destination_hierarchy
    plan.observations["destination_hierarchy"] = destination_hierarchy(
        price,
        [
            {"low": plain(z.low), "high": plain(z.high),
             "class": z.klass, "evidence": list(z.families)}
            for z in zs
        ],
        "SELL" if bear else "BUY",
    )
    # Assess the COMPLETE journey for each eligible entry, not only the strongest/nearest entry.
    # This does not predict that the countermove will happen. It preserves the existing Major
    # destination and D-1 touch rules, and records why each proposed journey is unsupported.
    journeys = []
    selected = None
    for candidate, candidate_reach, candidate_dist, candidate_info in good:
        destinations = sorted(
            [o for o in zs if o.high < candidate.low], key=lambda o: -o.high
        ) if bear else sorted(
            [o for o in zs if o.low > candidate.high], key=lambda o: o.low
        )
        major_destinations = [o for o in destinations if o.klass == MAJOR]
        inside = candidate.low <= price <= candidate.high
        counter_pips = pips(settings, candidate_dist)
        # Evidence-based, qualitative countermove assessment. An active hourly
        # correction is stronger evidence of movement toward an entry than a
        # 4-hour exhaustion signal; continuation alone supplies no such evidence.
        # Never present this as a calibrated probability.
        if inside:
            counter_state = "AT_ENTRY_NOW"
            counter_evidence = ["current price is already inside the proposed entry zone"]
        elif cond == CORRECTION_ACTIVE:
            counter_state = "CORRECTION_OBSERVED"
            counter_evidence = list(cond_ev)
        elif cond == CORRECTION_LIKELY:
            counter_state = "CORRECTION_INDICATED"
            counter_evidence = list(cond_ev)
        elif cond == EXHAUSTION:
            counter_state = "EXHAUSTION_ONLY"
            counter_evidence = list(cond_ev)
        else:
            counter_state = "UNCONFIRMED_PULLBACK"
            counter_evidence = ["4-hour continuation does not establish a corrective move toward the entry"]
        record = {
            "entry": [plain(candidate.low), plain(candidate.high)],
            "entry_class": candidate.klass,
            "reachability": candidate_reach,
            "countermove_pips": plain(counter_pips),
            "countermove_status": "already in zone" if inside else "possible, not predicted",
            "countermove_evidence_state": counter_state,
            "countermove_evidence": counter_evidence,
            "countermove_probability": None,
            "destination": None,
            "decision": "rejected",
            "reason": None,
        }
        if not major_destinations:
            record["reason"] = "no Major destination beyond this entry"
        else:
            primary = major_destinations[0]
            record["destination"] = [plain(primary.low), plain(primary.high)]
            touched = reached(settings, snap.five, price, primary.low, primary.high, toward_low=bear)
            if touched:
                record["reason"] = f"primary destination already touched: {touched}"
                if plan.destination_reached is None:
                    plan.destination_reached = {
                        "primary": plain(primary.high if bear else primary.low),
                        "zone": [plain(primary.low), plain(primary.high)],
                        "zone_candidate": [plain(candidate.low), plain(candidate.high)],
                        "how": touched,
                        "candle_utc": _iso(snap.five.start) if snap.five else None,
                    }
            else:
                record["decision"] = "eligible"
                record["reason"] = "structurally eligible; countermove remains unconfirmed"
                if selected is None:
                    selected = (candidate, candidate_reach, candidate_dist, candidate_info,
                                destinations, major_destinations)
        journeys.append(record)
    plan.observations["conditional_journeys"] = journeys
    plan.candidates = [_zone_dict(zz, i) for zz, _, _, i in looked]
    if selected is None:
        # Retain the established public reason contract for existing dashboards,
        # functional tests, and Keeper while exposing all candidate failures above.
        if plan.destination_reached is not None:
            plan.no_recommendation = (
                f"the primary destination {plan.destination_reached['primary']} is already reached "
                f"({plan.destination_reached['how']}); no recommendation is issued"
            )
        elif all(r["reason"] == "no Major destination beyond this entry" for r in journeys):
            plan.no_recommendation = (
                f"no Major {'support' if bear else 'resistance'} zone "
                "below the entry zone" if bear else
                "no Major resistance zone above the entry zone"
            )
        else:
            plan.no_recommendation = "no complete eligible entry-to-destination journey: " + "; ".join(
                f"{r['entry'][0]}-{r['entry'][1]}: {r['reason']}" for r in journeys
            )
        return plan

    # Destination-first decision: prefer a complete, untouched Major target that
    # lies ahead of current price in the trend direction. Rank its associated
    # conditional entries by the existing approved class/distance order.
    # Preserve the established entry-first choice when no ahead target exists.
    # This does not assert that the corrective leg will occur.
    eligible_by_target = []
    for candidate, candidate_reach, candidate_dist, candidate_info in good:
        destinations = sorted(
            [o for o in zs if o.high < candidate.low], key=lambda o: -o.high
        ) if bear else sorted(
            [o for o in zs if o.low > candidate.high], key=lambda o: o.low
        )
        majors_for_entry = [o for o in destinations if o.klass == MAJOR]
        if not majors_for_entry:
            continue
        primary = majors_for_entry[0]
        if reached(settings, snap.five, price, primary.low, primary.high, toward_low=bear):
            continue
        if ahead(price, primary.low, primary.high, toward_low=bear):
            eligible_by_target.append((
                primary, candidate, candidate_reach, candidate_dist,
                candidate_info, destinations, majors_for_entry,
            ))
    if eligible_by_target:
        # Nearest untapped Major target first, then the already-approved
        # ranking of qualifying entries for that target.
        eligible_by_target.sort(key=lambda item: (
            (price - item[0].high) if bear else (item[0].low - price),
            -CLASS_RANK[item[1].klass],
            item[3],
        ))
        _, cz, cr, cd, ci, ds, ms = eligible_by_target[0]
        selected = (cz, cr, cd, ci, ds, ms)
        plan.observations["destination_first_selection"] = {
            "mode": "nearest_untouched_major_ahead",
            "target": [plain(ms[0].low), plain(ms[0].high)],
            "entry": [plain(cz.low), plain(cz.high)],
            "conditional_only": True,
            "entry_confirmation": "not assessed by structural planner",
            "execution_authorised": False,
        }
    else:
        plan.observations["destination_first_selection"] = {
            "mode": "legacy_entry_rank_fallback",
            "reason": "no untouched Major destination wholly ahead of current price",
            "conditional_only": True,
            "entry_confirmation": "not assessed by structural planner",
            "execution_authorised": False,
        }
    # A rejected alternative must not retire an otherwise eligible plan.
    plan.destination_reached = None
    z, reach, dist, info, dests, majors = selected
    for zz, r, d, i in looked:
        if zz is z:
            i["chosen"] = True
        elif zz in [g[0] for g in good]:
            i["rejected_because"] = (
                "another complete eligible journey ranked higher" if any(
                    j["entry"] == [plain(zz.low), plain(zz.high)] and j["decision"] == "eligible"
                    for j in journeys
                ) else "no eligible destination for this entry"
            )
    plan.candidates = [_zone_dict(zz, i) for zz, _, _, i in looked]
    other = next((g for g in good if g[0] is not z), None)
    if other is not None:
        plan.alternative = _zone_dict(other[0], {"reachability": other[1]})
    edge = (lambda o: o.high) if bear else (lambda o: o.low)
    plan.zone, plan.reachability = z, reach
    families = ", ".join(z.families)
    plan.selection_reason = (
        f"{z.klass} zone ({len(z.families)} families: {families}) "
        f"{'containing price' if dist == 0 else plain(pips(settings, dist)) + ' pips away'}, {reach}; "
        + ("destination-first: nearest untouched Major target ahead, then entry class/distance; "
         if plan.observations["destination_first_selection"]["mode"] == "nearest_untouched_major_ahead"
         else "entry-class/distance fallback: no untouched Major target ahead; ")
        + "the countermove is conditional, not a forecast of certainty"
    )
    plan.destinations = {
        "intermediate": {"price": plain(edge(dests[0])), "zone": _zone_dict(dests[0], {})},
        "primary": {"price": plain(edge(majors[0])), "zone": _zone_dict(majors[0], {})},
        "extended": None if len(majors) < 2 else {"price": plain(edge(majors[1])), "zone": _zone_dict(majors[1], {})},
    }
    zone_break = (z.high + beyond) if bear else (z.low - beyond)
    struct_break = (last_opp.price + beyond) if bear else (last_opp.price - beyond)
    plan.invalidation = {
        "zone_break_close": plain(zone_break), "zone_break_timeframe": "1h",
        "structure_break_close": plain(struct_break), "structure_break_timeframe": "4h",
        "destination_first": plain(edge(majors[0])),
        # "destination reached before entry" applies to a destination wholly beyond price (D-1 correction: decided
        # with the same zone edges and touch rule as the lifecycle; one that is ahead and already touched was refused
        # above). One between price and the zone, or containing price, is simply on the way.
        "destination_first_applies": ahead(price, majors[0].low, majors[0].high, toward_low=bear),
        "conditions": [
            f"an hourly close at or {'above' if bear else 'below'} {plain(zone_break)} "
            f"({settings.planner.break_beyond_pips} pips beyond the zone {'top' if bear else 'bottom'})",
            f"a 4-hour close at or {'above' if bear else 'below'} {plain(struct_break)} "
            f"(beyond the last 4-hour swing {last_opp.kind} {plain(last_opp.price)})",
            f"the 4-hour direction no longer {dirn}",
            (f"price reaching the primary destination {plain(edge(majors[0]))} before the zone" if
             ahead(price, majors[0].low, majors[0].high, toward_low=bear) else
             f"(the primary destination {plain(edge(majors[0]))} lies between price and the zone: no 'reached first' check)")],
    }
    ref = z.reference.price
    risk = abs(zone_break - ref)
    if risk > 0:
        plan.observations["reward_to_invalidation"] = plain((abs(ref - edge(majors[0])) / risk).quantize(Decimal("0.1")))
    return plan


def structure_snapshot(lmap: list, zs: list, h4: list, d1: list, h1: list) -> dict | None:
    """Reporting only (owner's brief, 18 November 2026): every level of the level map, every zone and the swings the
    plan was built from, exactly as they stood at its time, so that a recommendation can be replayed later without
    recalculating anything from later data. Decides nothing; a problem here leaves the plan as it is."""
    try:
        sw = lambda s: {"kind": s.kind, "price": plain(s.price), "timeframe": s.timeframe,      # noqa: E731
                        "candle_utc": _iso(s.candle_utc), "known_utc": _iso(s.known_utc)}
        lv = lambda m: {k: v for k, v in (m.as_dict() | {"kind": m.kind}).items() if k != "note" and v != ""}  # noqa: E731
        return {"levels": [lv(m) for m in lmap],
                "zones": [{"low": plain(z.low), "high": plain(z.high), "class": z.klass, "families": z.families,
                           "tests": z.tests, "levels": [label(m) for m in z.members]} for z in zs],
                "swings": {"4h": [sw(s) for s in h4[-24:]], "1d": [sw(s) for s in d1[-12:]], "1h": [sw(s) for s in h1[-24:]]}}
    except Exception:                                    # noqa: BLE001  (reporting only)
        return None


# ---- observations ----------------------------------------------------------------------------------------------------

def observations(settings: Any, snap: Snapshot, st: Structure, d1: Structure, existing: Any, calendar: list | None,
                 five_minute_rule: dict | None) -> dict:
    """What the market is doing now (observed, not forecast). Context only: none of it decides anything here."""
    side = side_of(settings)
    o: dict = {"supporting": []}
    h4 = snap.h4
    if h4.last is not None:
        e7, e13, e21 = (h4.ema_now(p) for p in (7, 13, 21))
        if None not in (e7, e13, e21):
            order = ("7 < 13 < 21 (down)" if e7 < e13 < e21 else "7 > 13 > 21 (up)" if e7 > e13 > e21 else "mixed")
            o["h4_ema_stack"] = order
            o["supporting"].append(f"4-hour EMA 7/13/21 stack: {order}")
        c = cl(h4.last, side)
        for p in (100, 200):
            v = h4.ema_now(p)
            if v is None:
                o[f"h4_ema{p}"] = "warming up"
                o["supporting"].append(f"4-hour EMA{p}: warming up (not used)")
            else:
                o[f"h4_ema{p}"] = plain(v.quantize(Decimal("0.1")))
                o["supporting"].append(f"4-hour close {plain(c)} {'above' if c > v else 'below'} the EMA{p} {plain(v.quantize(Decimal('0.1')))}")
        n = settings.planner.ema_slope_candles
        s100 = h4.ema.get(100)
        if s100 and len(h4.candles) > n and h4.candles[-1 - n].start in s100:
            slope = s100[h4.last.start] - s100[h4.candles[-1 - n].start]
            o["h4_ema100_slope_pips"] = plain(pips(settings, slope))
            o["supporting"].append(f"4-hour EMA100 {'rising' if slope > 0 else 'falling' if slope < 0 else 'unchanged'} "
                                   f"{plain(pips(settings, abs(slope)))} pips over {n} candles")
        m = h4.macd.get(h4.last.start)
        if m:
            o["h4_macd"] = {"line": plain(m.line.quantize(Decimal("0.01"))), "signal": plain(m.signal.quantize(Decimal("0.01"))),
                            "histogram": plain(m.histogram.quantize(Decimal("0.01")))}
        r = h4.rsi.get(h4.last.start)
        if r is not None:
            o["h4_rsi"] = plain(r.quantize(Decimal("0.1")))
        b = h4.band.get(h4.last.start)
        if b:
            o["h4_band"] = {"upper": plain(b.upper.quantize(Decimal("0.1"))), "middle": plain(b.middle.quantize(Decimal("0.1"))),
                            "lower": plain(b.lower.quantize(Decimal("0.1"))),
                            "width_pips": plain(pips(settings, b.upper - b.lower)),
                            "close": "above the upper band" if c > b.upper else "below the lower band" if c < b.lower else "inside the bands"}
        run, sign = 0, None
        for x in reversed(h4.candles):
            s = (cl(x, side) > op(x, side)) - (cl(x, side) < op(x, side))
            if s == 0 or (sign is not None and s != sign):
                break
            sign, run = s, run + 1
        o["h4_same_colour_candles"] = f"{run} {'up' if sign == 1 else 'down' if sign == -1 else ''}".strip()
        if snap.adr:
            for p in (21, 100):
                v = h4.ema_now(p)
                if v is not None:
                    o[f"distance_from_h4_ema{p}_adr"] = plain(((c - v) / snap.adr).quantize(Decimal("0.01")))
    o["daily_structure"] = d1.why + (f"; broken {d1.broken[0]}" if d1.broken else "")
    if d1.sequence != MIXED and st.sequence != MIXED and d1.sequence != st.sequence:
        o["supporting"].append(f"warning: the daily structure ({d1.sequence}) is against the 4-hour structure ({st.sequence})")
    if snap.adr is not None:
        o["adr_pips"] = plain(pips(settings, snap.adr))
        rng = None
        today = [c for c in snap.fives if c.start >= snap.day_start]
        if today:
            rng = max(hi(c, side) for c in today) - min(lo(c, side) for c in today)
            o["today_range_pips"] = plain(pips(settings, rng))
            o["today_range_adr"] = plain((rng / snap.adr).quantize(Decimal("0.01")))
            o["remaining_room_pips"] = plain(pips(settings, snap.adr - rng))
    if snap.price is not None and existing is not None:
        piv = [lv.price for lv in existing.levels if lv.type == "pivot"]
        if piv:
            o["vs_daily_pivot"] = f"{'above' if snap.price > piv[0] else 'below' if snap.price < piv[0] else 'on'} the daily pivot {plain(piv[0])}"
        wk = snap.w1.last
        if wk is not None:
            from levels.rules import daily_pivots
            wp = [lv for lv in daily_pivots(wk, side, settings.levels.level_decimals, "") if lv.type == "pivot"][0].price
            o["vs_weekly_pivot"] = f"{'above' if snap.price > wp else 'below' if snap.price < wp else 'on'} the weekly pivot {plain(wp)}"
    if five_minute_rule:
        o["direction_rule_5m"] = five_minute_rule
    lt = snap.as_of.astimezone(UK)
    o["uk_time"] = lt.strftime("%H:%M")
    o["minutes_from"] = {f"{x:%H:%M}": int((lt.replace(tzinfo=None) - datetime.combine(lt.date(), x)).total_seconds() // 60)
                         for x in settings.bounce.near_times}
    try:
        from news.calendar import big_news_windows
        until = datetime.combine(lt.date(), settings.hours.close_all_trades_at, tzinfo=UK)
        if until > lt:
            ws = big_news_windows(settings, settings.market.pair, snap.as_of, until, calendar)
            o["big_news_today"] = sorted({f"{w.release_utc.astimezone(UK):%H:%M} UK {w.event}" for w in ws if w.release_utc >= snap.as_of})
    except Exception:                                    # noqa: BLE001  (context only; never stops the plan)
        o["big_news_today"] = "calendar not available"
    return o


def plan_at(settings: Any, store: Any, as_of: datetime, calendar: list | None = None) -> Plan:
    """The plan at `as_of`, from the candle store and the existing levels as they stood then."""
    from analyser.direction import decide
    from analyser.indicators import last_candles
    from levels.current import build
    from prices.indicators import ema
    snap = snapshot(settings, store, as_of)
    existing = build(settings, store, as_of)
    rule = None
    try:
        fives = last_candles(store, "5m", as_of, settings.indicators.history_candles)
        e = ema(fives, side_of(settings), settings.analyser.direction_ema_periods) if fives else {}
        piv = [lv.price for lv in existing.levels if lv.type == "pivot"]
        d = decide(snap.price, "the latest 5-minute close", piv[0] if piv else None,
                   e.get(fives[-1].start) if fives else None, "5m 100 EMA", bool(e))
        rule = {"side": d.side, "reason": d.reason}
    except Exception:                                    # noqa: BLE001  (context only)
        rule = None
    return assess(settings, snap, existing, calendar, rule)
