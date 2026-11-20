"""The planner's level map and confluence zones (D-06 to D-09, D-35; parameters P-C1 to P-C9). Sell price.

LEVELS: the bot's existing levels (levels/current.py build: daily pivot, R1-R3, S1-S3, the previous day's high and
low, round numbers, London and New York session highs and lows, hourly turning levels), plus:
  * weekly pivot, R1-R3, S1-S3: the classic formulas on the last finished weekly candle (D-35);
  * the previous week's high and low (that same weekly candle);
  * 4-hour swings from the last planner.h4_swing_lookback_weeks, daily swings from the last
    planner.daily_swing_lookback_weeks (planner/structure.py);
  * historical daily swings (20 November 2026): daily swings OLDER than planner.daily_swing_lookback_weeks, back to
    planner.historical_daily_swing_lookback_weeks (0 = none), named "historical daily swing low/high". Same family
    (HTF_STRUCTURE) and daily-or-weekly status as the recent daily swings. Only swings already confirmed at the
    assessment time (known_utc <= as_of) count. The direction never uses them: it is decided from the latest swings
    exactly as before (dominant_structure);
  * moving-average levels (P-C9): hourly EMA100 and EMA200, 4-hour EMA100, 4-hour EMA200 once warmed up, and the
    4-hour Bollinger middle band.
Structural zones are retained regardless of distance from spot; levels.round_numbers_within_pips only controls round-number discovery (P-C5).

FAMILIES (D-08): PIVOT, SESSION, STRUCTURE, HTF_STRUCTURE (daily swings), MOVING_AVERAGE, PSYCHOLOGICAL. Several
levels of one family in a zone count once. "Daily-or-weekly" levels: daily or weekly pivots and R/S, the previous
day's or week's high or low, daily swings.

ZONES (D-07, P-C3): going up from the lowest level, a level joins the current zone if it is within the zone width of
the zone's LOWEST level, so no zone is wider than that; the width is the larger of levels.line_up_within_pips (5)
and planner.zone_width_adr_share (0.15) x the ADR (provisional, owner 17 November 2026). Never widened otherwise.

CLASSES (D-09, P-C7), no weights:
  Major     at least planner.major_min_families (3) families, including at least one daily-or-weekly level;
  Moderate  at least planner.moderate_min_families (2) families (and not Major);
  Minor     one family.

TESTS (D-25, P-C8; recorded only): a test is an hourly candle reaching the zone by the interaction rule (P-C2); the
next one counts only after an hourly candle has been wholly more than rejection.near_level_within_pips (3) clear of
it. FLIPPED (role change): a swing low later closed below by at least planner.break_beyond_pips (3) on an hourly
candle, now above price, is former support acting as resistance; the mirror for a swing high.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Sequence

from levels import rules
from planner.measure import Snapshot, cl, hi, lo, ppp, side_of
from planner.structure import Swing
from prices.model import Candle, plain, uk_short

PIVOT, SESSION, STRUCTURE, HTF_STRUCTURE, MOVING_AVERAGE, PSYCHOLOGICAL = (
    "pivot", "session", "structure", "higher-timeframe structure", "moving average", "psychological")
MAJOR, MODERATE, MINOR = "Major", "Moderate", "Minor"
CLASS_RANK = {MAJOR: 3, MODERATE: 2, MINOR: 1}

# The most significant level in a zone (D-17): the brief's priority order (daily pivots first, EMAs last).
PRIORITY = ("daily pivot", "weekly pivot", "daily R/S", "weekly R/S", "previous day high/low", "previous week high/low",
            "psychological", "daily swing", "4-hour swing", "hourly swing", "session high/low", "moving average")


@dataclass(frozen=True)
class MapLevel:
    price: Decimal
    name: str                   # e.g. "daily R2", "4-hour swing high", "H1 EMA100"
    family: str
    timeframe: str              # weekly, daily, 4h, 1h, intraday
    kind: str                   # an entry of PRIORITY
    origin_utc: datetime | None
    daily_or_weekly: bool
    fixed: bool                 # False for moving averages and a still-running session's high or low (FC-05)
    note: str = ""
    role: str = ""               # e.g. "former support, now resistance" (a flipped level); not part of its name

    def as_dict(self) -> dict:
        return {"price": plain(self.price), "name": self.name, "role": self.role, "family": self.family,
                "timeframe": self.timeframe,
                "origin_utc": self.origin_utc.strftime("%Y-%m-%dT%H:%M:%SZ") if self.origin_utc else None,
                "daily_or_weekly": self.daily_or_weekly, "fixed": self.fixed, "note": self.note}


_FROM_LEVELS = {
    rules.PIVOT: ("daily pivot", PIVOT, "daily", "daily pivot", True),
    rules.R1: ("daily R1", PIVOT, "daily", "daily R/S", True), rules.R2: ("daily R2", PIVOT, "daily", "daily R/S", True),
    rules.R3: ("daily R3", PIVOT, "daily", "daily R/S", True), rules.S1: ("daily S1", PIVOT, "daily", "daily R/S", True),
    rules.S2: ("daily S2", PIVOT, "daily", "daily R/S", True), rules.S3: ("daily S3", PIVOT, "daily", "daily R/S", True),
    rules.PREVIOUS_DAY_HIGH: ("previous day high", SESSION, "daily", "previous day high/low", True),
    rules.PREVIOUS_DAY_LOW: ("previous day low", SESSION, "daily", "previous day high/low", True),
    rules.ROUND_NUMBER: ("round number", PSYCHOLOGICAL, "intraday", "psychological", False),
    rules.LONDON_HIGH: ("London session high", SESSION, "intraday", "session high/low", False),
    rules.LONDON_LOW: ("London session low", SESSION, "intraday", "session high/low", False),
    rules.NEW_YORK_HIGH: ("New York session high", SESSION, "intraday", "session high/low", False),
    rules.NEW_YORK_LOW: ("New York session low", SESSION, "intraday", "session high/low", False),
    rules.TURNING_HIGH: ("hourly swing high", STRUCTURE, "1h", "hourly swing", False),
    rules.TURNING_LOW: ("hourly swing low", STRUCTURE, "1h", "hourly swing", False),
}


def from_existing(level_list: Any) -> list[MapLevel]:
    """The existing levels part's levels (levels/current.py LevelList), with their families."""
    out = []
    for lv in level_list.levels:
        name, fam, tf, kind, dw = _FROM_LEVELS[lv.type]
        running = "so far" in (lv.source or "")              # today's session, still running: it moves (FC-05)
        out.append(MapLevel(lv.price, name + (" (so far)" if running else ""), fam, tf, kind, lv.candle_utc, dw,
                            not running, lv.source))
    return out


def weekly_levels(settings: Any, snap: Snapshot) -> list[MapLevel]:
    """Weekly pivots and the previous week's high and low, from the last finished weekly candle (D-35)."""
    wk = snap.w1.last
    if wk is None:
        return []
    side = side_of(settings)
    src = f"weekly candle {uk_short(wk.start)}"
    out = []
    for lv in rules.daily_pivots(wk, side, settings.levels.level_decimals, src):
        name = "weekly pivot" if lv.type == rules.PIVOT else f"weekly {lv.type}"
        out.append(MapLevel(lv.price, name, PIVOT, "weekly", "weekly pivot" if lv.type == rules.PIVOT else "weekly R/S",
                            wk.start, True, True, src))
    out.append(MapLevel(hi(wk, side), "previous week high", SESSION, "weekly", "previous week high/low", wk.start, True, True, src))
    out.append(MapLevel(lo(wk, side), "previous week low", SESSION, "weekly", "previous week high/low", wk.start, True, True, src))
    return out


def swing_levels(found: Sequence[Swing], as_of: datetime, weeks: int) -> list[MapLevel]:
    out = []
    since = as_of - timedelta(weeks=weeks)
    for s in found:
        if s.candle_utc < since:
            continue
        if s.timeframe == "4h":
            out.append(MapLevel(s.price, f"4-hour swing {s.kind}", STRUCTURE, "4h", "4-hour swing", s.candle_utc, False, True,
                                s.describe()))
        else:
            out.append(MapLevel(s.price, f"daily swing {s.kind}", HTF_STRUCTURE, "daily", "daily swing", s.candle_utc, True, True,
                                s.describe()))
    return out


def historical_swing_levels(found: Sequence[Swing], as_of: datetime, recent_weeks: int,
                            historical_weeks: int) -> list[MapLevel]:
    """Daily swings older than the recent look-back (recent_weeks) and no older than historical_weeks, confirmed by
    as_of. Empty when historical_weeks is 0 or not beyond recent_weeks."""
    if not historical_weeks or historical_weeks <= recent_weeks:
        return []
    recent, since = as_of - timedelta(weeks=recent_weeks), as_of - timedelta(weeks=historical_weeks)
    out = []
    for s in found:
        if s.timeframe != "1d" or not (since <= s.candle_utc < recent) or s.known_utc > as_of:
            continue
        out.append(MapLevel(s.price, f"historical daily swing {s.kind}", HTF_STRUCTURE, "daily", "daily swing",
                            s.candle_utc, True, True, s.describe()))
    return out


def average_levels(snap: Snapshot, decimals: int = 1) -> list[MapLevel]:
    """Moving-average levels, written to levels.level_decimals like every other level."""
    q = lambda v: rules.to_decimals(v, decimals)        # noqa: E731
    out = []
    for f, p in ((snap.h1, 100), (snap.h1, 200), (snap.h4, 100), (snap.h4, 200)):
        v = f.ema_now(p)
        if v is not None:
            tf = "1h" if f.timeframe == "1h" else "4h"
            out.append(MapLevel(q(v), f"{'H1' if tf == '1h' else 'H4'} EMA{p}", MOVING_AVERAGE, tf, "moving average",
                                f.last.start, False, False))
    band = snap.h4.band.get(snap.h4.last.start) if snap.h4.last else None
    if band is not None:
        out.append(MapLevel(q(band.middle), "H4 Bollinger middle", MOVING_AVERAGE, "4h", "moving average", snap.h4.last.start,
                            False, False))
    return out


def flipped(settings: Any, levels: list[MapLevel], hourly: Sequence[Candle], price: Decimal) -> list[MapLevel]:
    """Mark swing levels broken by an hourly close at least break_beyond_pips through them, now on the other side
    of price (support turned resistance, or the reverse)."""
    side = side_of(settings)
    beyond = Decimal(settings.planner.break_beyond_pips) * ppp(settings)
    out = []
    for lv in levels:
        if lv.family in (STRUCTURE, HTF_STRUCTURE) and lv.origin_utc is not None:
            later = [c for c in hourly if c.start > lv.origin_utc]
            low_kind = lv.name.endswith("low")
            if low_kind and lv.price > price and any(cl(c, side) <= lv.price - beyond for c in later):
                lv = MapLevel(lv.price, lv.name, lv.family, lv.timeframe, lv.kind, lv.origin_utc,
                              lv.daily_or_weekly, lv.fixed, lv.note, "former support, now resistance")
            elif not low_kind and lv.price < price and any(cl(c, side) >= lv.price + beyond for c in later):
                lv = MapLevel(lv.price, lv.name, lv.family, lv.timeframe, lv.kind, lv.origin_utc,
                              lv.daily_or_weekly, lv.fixed, lv.note, "former resistance, now support")
        out.append(lv)
    return out


def level_map(settings: Any, snap: Snapshot, existing: Any, h4_swings: Sequence[Swing],
              d1_swings: Sequence[Swing]) -> list[MapLevel]:
    """Every level within the distance window of price, sorted by price."""
    if snap.price is None:
        return []
    p = settings.planner
    levels = from_existing(existing) + weekly_levels(settings, snap)
    levels += swing_levels(h4_swings, snap.as_of, p.h4_swing_lookback_weeks)
    levels += swing_levels(d1_swings, snap.as_of, p.daily_swing_lookback_weeks)
    levels += historical_swing_levels(d1_swings, snap.as_of, p.daily_swing_lookback_weeks,
                                      getattr(p, "historical_daily_swing_lookback_weeks", 0))
    levels += average_levels(snap, settings.levels.level_decimals)
    levels = flipped(settings, levels, snap.h1.candles, snap.price)
    return sorted(levels, key=lambda lv: (lv.price, PRIORITY.index(lv.kind), lv.name))


# ---- zones -------------------------------------------------------------------------------------------------------

@dataclass
class Zone:
    low: Decimal
    high: Decimal
    members: list[MapLevel]
    families: list[str]
    klass: str
    daily_or_weekly: bool
    tests: int = 0
    reference: MapLevel | None = None
    notes: list[str] = field(default_factory=list)

    @property
    def fixed_identity(self) -> tuple:
        """The zone's fixed levels (FC-05): moving averages left out."""
        return tuple(sorted((m.name, plain(m.price)) for m in self.members if m.fixed))

    def describe(self) -> str:
        return (f"{plain(self.low)}-{plain(self.high)} ({self.klass}: "
                + ", ".join(label(m) for m in self.members) + ")")

    def as_dict(self) -> dict:
        return {"low": plain(self.low), "high": plain(self.high), "class": self.klass, "families": self.families,
                "daily_or_weekly_level": self.daily_or_weekly, "tests": self.tests,
                "reference": None if self.reference is None else self.reference.as_dict(),
                "levels": [m.as_dict() for m in self.members]}


def zone_width(settings: Any, adr: Decimal) -> Decimal:
    """The larger of levels.line_up_within_pips and planner.zone_width_adr_share x ADR, in points (P-C3)."""
    floor = Decimal(settings.levels.line_up_within_pips) * ppp(settings)
    return max(floor, Decimal(str(settings.planner.zone_width_adr_share)) * adr)


def classify(settings: Any, families: set[str], daily_or_weekly: bool) -> str:
    p = settings.planner
    if len(families) >= p.major_min_families and daily_or_weekly:
        return MAJOR
    if len(families) >= p.moderate_min_families:
        return MODERATE
    return MINOR


def reference_level(members: Sequence[MapLevel]) -> MapLevel:
    """The most significant level in the zone (D-17): the brief's priority order; then the lower price."""
    return sorted(members, key=lambda m: (PRIORITY.index(m.kind), m.price))[0]


def interacts(settings: Any, c: Candle, low: Decimal, high: Decimal, from_below: bool) -> bool:
    """The existing level-touch rule (rejection/watch.py _pierced, [rejection] near_level_within_pips; FC-01, as
    in the strategies' own watcher, with no "opened on the near side" condition), on a zone. Coming up into a zone
    from below (a sell zone): the candle's high reaches the zone bottom less 3 pips or higher, and its low is at or
    below the zone top. A buy zone (from above) is the mirror image."""
    side = side_of(settings)
    near = Decimal(settings.rejection.near_level_within_pips) * ppp(settings)
    if from_below:
        return hi(c, side) >= low - near and lo(c, side) <= high
    return lo(c, side) <= high + near and hi(c, side) >= low


def ahead(price: Decimal, low: Decimal, high: Decimal, toward_low: bool) -> bool:
    """The destination zone lies wholly beyond price in the trade's final direction (below price for a sell's
    destination, above for a buy's): only then can price reach it "before the zone". Otherwise it lies between price
    and the entry zone, or contains price, and is simply on the way."""
    return price > high if toward_low else price < low


def reached(settings: Any, c: Candle | None, price: Decimal, low: Decimal, high: Decimal, toward_low: bool) -> str | None:
    """D-1 correction (18 November 2026): is a destination zone already reached, by the lifecycle's own rule for
    "price reached the primary destination" (interacts: the existing one-sided 3-pip touch rule, coming down into it
    for a sell's destination, up into it for a buy's), on the latest finished 5-minute candle? Returns how, in words,
    or None. A destination price has gone well past (the candle wholly beyond it, untouched) is not reached: it lies
    between price and the entry zone, on the way, as before."""
    if c is None:
        return None
    if interacts(settings, c, low, high, from_below=not toward_low):
        ext = lo(c, side_of(settings)) if toward_low else hi(c, side_of(settings))
        return (f"the {uk_short(c.start)} 5-minute candle reached {plain(ext)}, within "
                f"{settings.rejection.near_level_within_pips} pips of the destination zone {plain(low)}-{plain(high)}")
    return None


def wholly_clear(settings: Any, c: Candle, low: Decimal, high: Decimal) -> bool:
    """The whole candle more than near_level_within_pips away from the zone (P-C8, P-F6)."""
    side = side_of(settings)
    near = Decimal(settings.rejection.near_level_within_pips) * ppp(settings)
    return lo(c, side) > high + near or hi(c, side) < low - near


def count_tests(settings: Any, z: Zone, hourly: Sequence[Candle], since: datetime | None) -> int:
    n, armed = 0, True
    for c in hourly:
        if since is not None and c.start < since:
            continue
        if armed and (interacts(settings, c, z.low, z.high, True) or interacts(settings, c, z.low, z.high, False)):
            n, armed = n + 1, False
        elif not armed and wholly_clear(settings, c, z.low, z.high):
            armed = True
    return n


def label(m: MapLevel) -> str:
    return f"{m.name} {plain(m.price)}" + (f" ({m.role})" if m.role else "")


def _anchored(levels: Sequence[MapLevel], width: Decimal) -> list[list[MapLevel]]:
    groups: list[list[MapLevel]] = []
    for lv in sorted(levels, key=lambda x: (x.price, PRIORITY.index(x.kind), x.name)):
        if not groups or lv.price - groups[-1][0].price > width:
            groups.append([lv])
        else:
            groups[-1].append(lv)
    return groups


def zones(settings: Any, levels: Sequence[MapLevel], adr: Decimal, hourly: Sequence[Candle],
          price: Decimal | None = None) -> list[Zone]:
    """The zones. Built from the FIXED levels first (anchored at each zone's lowest level), so that moving levels
    (moving averages, a running session's high or low) never reshape a zone (FC-05); each moving level then joins the
    nearest zone it fits in (every member still within the width of every other), and the moving levels left over make
    zones of their own. All discovered structural zones are retained; the round-number discovery radius
    does not constrain structural destinations."""
    width = zone_width(settings, adr)
    groups = _anchored([lv for lv in levels if lv.fixed], width)
    spare = []
    for lv in sorted((lv for lv in levels if not lv.fixed), key=lambda x: x.price):
        fits = [g for g in groups if max(g[-1].price, lv.price) - min(g[0].price, lv.price) <= width]
        if fits:
            g = min(fits, key=lambda g: min(abs(lv.price - g[0].price), abs(lv.price - g[-1].price)))
            g.append(lv)
            g.sort(key=lambda x: (x.price, PRIORITY.index(x.kind), x.name))
        else:
            spare.append(lv)
    groups = sorted(groups + _anchored(spare, width), key=lambda g: g[0].price)
    # Retain the complete structural map. The round-number discovery radius is
    # not a structural destination horizon; filtering here could remove valid
    # Major targets before the planner evaluates them.
    out = []
    for g in groups:
        fams = {m.family for m in g}
        dw = any(m.daily_or_weekly for m in g)
        z = Zone(g[0].price, g[-1].price, list(g), sorted(fams), classify(settings, fams, dw), dw)
        z.reference = reference_level(g)
        origins = [m.origin_utc for m in g if m.fixed and m.origin_utc is not None]
        z.tests = count_tests(settings, z, hourly, min(origins) if origins else None)
        out.append(z)
    return out
