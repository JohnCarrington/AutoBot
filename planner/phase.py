"""Market Phase Intelligence for the Structural Trade Planner. RESEARCH MODEL, OBSERVE ONLY.

Owner's brief "Market Phase Intelligence - Research, Design and Validation" (18 November 2026). Nothing in production
imports this module: the live planner (planner/assess.py, planner/keeper.py) is unchanged and keeps running as it is.
Nothing here authorises, refuses, opens, changes or closes a trade; every opportunity it describes carries
`authorises = False`, and it never proposes reversing one trade into another.

It separates three things the V1 planner folds into one:

A. DOMINANT DIRECTION (BULLISH / BEARISH / NEUTRAL), from 4-hour evidence:
   * the 4-hour swing structure (planner/structure.py swings, the approved 40-pip rule), compared with a
     VOLATILITY-ADJUSTED TOLERANCE: two swings closer than the tolerance are "equal", not higher or lower. The default
     tolerance is the planner's own definition of "the same level": the zone width, the larger of
     levels.line_up_within_pips (5) and planner.zone_width_adr_share (0.15) x ADR. It was chosen because the planner
     already uses it to decide that two prices are one level, not by fitting any day; validation tests 0, 5 pips and
     0.10 / 0.15 / 0.25 x ADR;
   * a BREAK OF STRUCTURE resolves a mixed sequence: after the most recent swing, a 4-hour close at least
     hourly_read.break_beyond_pips (3) beyond the most recent opposite swing (a lower low after a higher high is
     bearish; the mirror is bullish);
   * a confirmed 4-hour close beyond the last opposite swing against a down (up) structure is a STRUCTURAL break
     (the V1 TRANSITIONAL rule): the structure vote becomes 0 and the phase STRUCTURAL_REVERSAL;
   * supporting votes: 4-hour EMA 7/13/21 stack, the close against the EMA100, the EMA100 slope over
     planner.ema_slope_candles (at least `ema_slope_min_pips`).
   Structure vote: -2 clean down, -1 down with one side "equal" (a marginal violation) or down by a break of
   structure, 0 mixed / range / broken, +1 / +2 the mirror. Score = structure vote + the three EMA votes.
   BEARISH when the structure vote is not up and the score is at most -min_score (3); BULLISH the mirror. So the
   structure stays the authority (it can never be outvoted), but a marginal violation no longer erases otherwise
   consistent evidence. `mixed_allows_ema_consensus` (off by default) also lets a genuinely mixed structure (vote 0)
   be directional when all three EMA votes agree; it is evaluated as an alternative, not the default.

B. MARKET PHASE, inside the dominant direction, mainly from the hourly chart (written for BEARISH; BULLISH mirrors):
   the impulse starts at the most recent confirmed 4-hour swing high; E = the lowest price since (finished hourly
   candles, plus finished 5-minute candles after the last hourly one); C = the highest price since E.
     STRUCTURAL_REVERSAL     a confirmed 4-hour close beyond the last 4-hour swing high (structure broken);
     CONSOLIDATION           no dominant direction; or price stalled within `stall_adr` x ADR of E for
                             `stall_hours` hours with no correction;
     TREND_IMPULSE           a new low within the last `impulse_recent_h1` hourly candles, without exhaustion;
     EXHAUSTION              a recent new low (within `exhaustion_window_h1` hours, no correction yet) with at least
                             `exhaustion_min_evidence` of the exhaustion evidence below;
     COUNTERTREND_CORRECTION a correction is under way (an hourly close above the hourly EMA21 or Bollinger middle
                             since E, or C - E at least `correction_min_adr` x ADR) and neither of the next two holds;
     RESISTANCE_TEST         the correction reaches the first meaningful resistance zone (SUPPORT_TEST for a bullish
                             market's correction);
     TREND_CONTINUATION      after a correction: renewed bearish alignment (hourly EMA7 < EMA13) AND a rejection (an
                             hourly close back below the hourly EMA21 after closing above it, or a close at least 3 pips
                             below the corrective support), with no hourly close above the tested resistance.
   Exhaustion evidence (no single indicator required): band extension (an hourly close below the lower band, or a
   low more than bounce.pierce_beyond_pips through it, then a close back inside); RSI 3 below its lower line then back
   above; hourly MACD histogram below zero and rising for 2 candles; a rejection candle at the low (hourly or 5-minute:
   lower wick at least half the range, close in the upper half); stretched from the hourly EMA21 by at least
   `extension_adr` x ADR at the low; the low at a meaningful support zone; a 4-hour low through the 4-hour lower band.

C. OPPORTUNITY CLASSIFICATION (never an authorisation): TREND_ALIGNED, COUNTERTREND_CORRECTION, STRUCTURAL_REVERSAL
   (and, for a trade that fits none, COUNTERTREND_UNSUPPORTED or NO_DIRECTIONAL_VIEW).

COUNTERTREND INTELLIGENCE (offline evaluation only; existing trade management stays authoritative): for EXHAUSTION or
COUNTERTREND_CORRECTION, the proposed entry zone (around E), the first obstacle of any kind, the FIRST MEANINGFUL
opposing level (the nearest zone of at least Moderate class, or one containing a structural level: an hourly, 4-hour
or daily swing, a daily or weekly pivot or R/S, the previous day's or week's high or low, a finished session's high or
low; a lone moving average or round number is not meaningful), the corrective destination (that zone's near edge),
the structural invalidation (an hourly close 3 pips beyond E), the room after the spread, and the potential return-to-
trend opportunity (which still needs an independently valid strategy trigger and the existing risk approval).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Sequence

from planner.measure import cl, hi, lo, op, ppp
from planner.structure import Swing
from planner.zones import CLASS_RANK, MAJOR, MODERATE, MapLevel, Zone
from prices.model import plain, uk_short

BULLISH, BEARISH, NEUTRAL = "BULLISH", "BEARISH", "NEUTRAL"
TREND_IMPULSE, EXHAUSTION, COUNTERTREND_CORRECTION = "TREND_IMPULSE", "EXHAUSTION", "COUNTERTREND_CORRECTION"
RESISTANCE_TEST, SUPPORT_TEST, TREND_CONTINUATION = "RESISTANCE_TEST", "SUPPORT_TEST", "TREND_CONTINUATION"
CONSOLIDATION, STRUCTURAL_REVERSAL = "CONSOLIDATION", "STRUCTURAL_REVERSAL"
PHASES = (TREND_IMPULSE, EXHAUSTION, COUNTERTREND_CORRECTION, RESISTANCE_TEST, SUPPORT_TEST, TREND_CONTINUATION,
          CONSOLIDATION, STRUCTURAL_REVERSAL)
TREND_ALIGNED, COUNTERTREND, REVERSAL = "TREND_ALIGNED", "COUNTERTREND_CORRECTION", "STRUCTURAL_REVERSAL"
UNSUPPORTED, NO_VIEW = "COUNTERTREND_UNSUPPORTED", "NO_DIRECTIONAL_VIEW"

STRUCTURAL_KINDS = frozenset({"hourly swing", "4-hour swing", "daily swing", "daily pivot", "weekly pivot", "daily R/S",
                              "weekly R/S", "previous day high/low", "previous week high/low"})
HTF_KINDS = frozenset({"4-hour swing", "daily swing", "daily pivot", "weekly pivot", "daily R/S", "weekly R/S",
                       "previous day high/low", "previous week high/low"})
TURN = ("band_extension", "rsi_recovery", "macd_contraction", "rejection_candle")     # the move is turning
EVIDENCE = ("band_extension", "rsi_recovery", "macd_contraction", "rejection_candle", "extension_from_ema21",
            "at_support", "h4_band_extension")


@dataclass(frozen=True)
class PhaseParams:
    """Research parameters. Defaults are set from first principles or existing approved numbers, never fitted to a
    day; the validation reports their sensitivity."""
    tolerance_adr_share: Decimal = Decimal("0.15")    # = planner.zone_width_adr_share (the planner's "same level")
    tolerance_floor_pips: Decimal = Decimal("5")      # = levels.line_up_within_pips
    use_tolerance: bool = True
    break_of_structure: bool = True
    mixed_allows_ema_consensus: bool = False
    ema_slope_min_pips: Decimal = Decimal("2")
    min_score: int = 3
    impulse_recent_h1: int = 1                        # a new extreme in the latest or the one before
    exhaustion_window_h1: int = 3
    exhaustion_min_evidence: int = 2
    extension_adr: Decimal = Decimal("0.25")
    correction_min_adr: Decimal = Decimal("0.2")
    stall_adr: Decimal = Decimal("0.15")
    stall_hours: int = 4
    room_min_pips: Decimal = Decimal("10")
    room_spread_multiple: Decimal = Decimal("4")
    strict_meaningful: bool = True
    require_turn: bool = True                         # exhaustion needs at least one TURN sign

    def tolerance(self, settings: Any, adr: Decimal | None) -> Decimal:
        if not self.use_tolerance:
            return Decimal(0)
        floor = self.tolerance_floor_pips * ppp(settings)
        return max(floor, (self.tolerance_adr_share * adr) if adr else floor)


DEFAULT = PhaseParams()


def _iso(t: datetime | None) -> str | None:
    return None if t is None else t.strftime("%Y-%m-%dT%H:%M:%SZ")


def _pips(settings: Any, points: Decimal) -> Decimal:
    return (Decimal(points) / ppp(settings)).quantize(Decimal("0.1"))


# ======================================================================================================================
# A. dominant direction
# ======================================================================================================================

@dataclass
class DirectionView:
    direction: str
    score: int
    structure_vote: int
    ema_votes: dict
    evidence: list[str]
    tolerance_pips: Decimal
    highs: list[Swing]
    lows: list[Swing]
    marginal: dict | None = None          # a raw higher/lower that the tolerance treats as equal
    break_of_structure: dict | None = None
    broken_against: dict | None = None    # the V1 TRANSITIONAL break
    v1_direction: str = NEUTRAL           # what the V1 rule (planner/assess.py direction) says on the same swings

    def as_dict(self) -> dict:
        sw = lambda s: {"kind": s.kind, "price": plain(s.price), "candle_utc": _iso(s.candle_utc),  # noqa: E731
                        "known_utc": _iso(s.known_utc)}
        return {"direction": self.direction, "score": self.score, "structure_vote": self.structure_vote,
                "ema_votes": self.ema_votes, "evidence": self.evidence, "tolerance_pips": plain(self.tolerance_pips),
                "highs": [sw(s) for s in self.highs], "lows": [sw(s) for s in self.lows], "marginal": self.marginal,
                "break_of_structure": self.break_of_structure, "broken_against": self.broken_against,
                "v1_direction": self.v1_direction}


def _compare(new: Decimal, old: Decimal, tol: Decimal) -> str:
    d = new - old
    return "higher" if d > tol else "lower" if d < -tol else "equal"


_VOTE = {("lower", "lower"): -2, ("equal", "lower"): -1, ("lower", "equal"): -1,
         ("higher", "higher"): 2, ("equal", "higher"): 1, ("higher", "equal"): 1}


def v1_direction(highs: list[Swing], lows: list[Swing], broken: bool) -> str:
    """The V1 rule exactly (planner/assess.py direction with planner/structure.py structure): mixed or too few is
    NEUTRAL; a confirmed break is TRANSITIONAL."""
    if len(highs) < 2 or len(lows) < 2:
        return NEUTRAL
    dn = highs[1].price < highs[0].price and lows[1].price < lows[0].price
    up = highs[1].price > highs[0].price and lows[1].price > lows[0].price
    if not (dn or up):
        return NEUTRAL
    if broken:
        return "TRANSITIONAL"
    return BEARISH if dn else BULLISH


def _closes_after(h4: Sequence[Any], t: datetime) -> list:
    return [c for c in h4 if c.start > t]


def dominant(settings: Any, h4_frame: Any, h4_swings: Sequence[Swing], adr: Decimal | None,
             params: PhaseParams = DEFAULT) -> DirectionView:
    """The dominant direction from finished 4-hour candles and the swings known by then (oldest first)."""
    side = settings.chart.price
    cs = h4_frame.candles
    beyond = Decimal(settings.hourly_read.break_beyond_pips) * ppp(settings)
    tol = params.tolerance(settings, adr)
    highs = [s for s in h4_swings if s.kind == "high"][-2:]
    lows = [s for s in h4_swings if s.kind == "low"][-2:]
    ev: list[str] = []
    marginal = bos = broken_against = None
    vote = 0
    v1_broken = False
    if len(highs) < 2 or len(lows) < 2:
        ev.append(f"4-hour structure: too few confirmed swings ({len(highs)} highs, {len(lows)} lows)")
    else:
        raw = (_compare(highs[1].price, highs[0].price, Decimal(0)), _compare(lows[1].price, lows[0].price, Decimal(0)))
        tolerant = (_compare(highs[1].price, highs[0].price, tol), _compare(lows[1].price, lows[0].price, tol))
        said = (f"swing highs {plain(highs[0].price)} then {plain(highs[1].price)}, swing lows {plain(lows[0].price)} "
                f"then {plain(lows[1].price)}")
        vote = _VOTE.get(tolerant, 0)
        if raw != tolerant:
            which = [("highs", raw[0], tolerant[0], highs), ("lows", raw[1], tolerant[1], lows)]
            m = [w for w in which if w[1] != w[2]]
            marginal = {w[0]: {"raw": w[1], "with_tolerance": w[2],
                               "difference_pips": plain(_pips(settings, w[3][1].price - w[3][0].price))} for w in m}
            ev.append(f"4-hour structure {said}: the {', '.join(w[0] for w in m)} differ by less than the tolerance "
                      f"{plain(_pips(settings, tol))} pips, so count as equal (a marginal violation, not a reversal)")
        else:
            ev.append(f"4-hour structure {said}")
        # the V1 break (TRANSITIONAL) on the raw sequence, for comparison and for the structural break below
        if raw == ("lower", "lower"):
            v1_broken = any(cl(c, side) >= highs[1].price + beyond for c in _closes_after(cs, highs[1].candle_utc))
        elif raw == ("higher", "higher"):
            v1_broken = any(cl(c, side) <= lows[1].price - beyond for c in _closes_after(cs, lows[1].candle_utc))
        # a structural break against a directional (tolerant) structure
        if vote < 0:
            br = [c for c in _closes_after(cs, highs[1].candle_utc) if cl(c, side) >= highs[1].price + beyond]
            if br:
                broken_against = {"way": "up", "close": plain(cl(br[0], side)), "candle_utc": _iso(br[0].start),
                                  "swing": plain(highs[1].price)}
        elif vote > 0:
            br = [c for c in _closes_after(cs, lows[1].candle_utc) if cl(c, side) <= lows[1].price - beyond]
            if br:
                broken_against = {"way": "down", "close": plain(cl(br[0], side)), "candle_utc": _iso(br[0].start),
                                  "swing": plain(lows[1].price)}
        if broken_against:
            ev.append(f"confirmed 4-hour close {broken_against['close']} {'above' if vote < 0 else 'below'} the last "
                      f"swing {'high' if vote < 0 else 'low'} {broken_against['swing']}: structure broken")
            vote = 0
        elif vote == 0 and params.break_of_structure:
            latest = max(highs[1], lows[1], key=lambda s: s.candle_utc)
            if latest.kind == "high":       # after the latest swing high, a close through the latest swing low
                br = [c for c in _closes_after(cs, latest.candle_utc) if cl(c, side) <= lows[1].price - beyond]
                if br:
                    bos = {"way": "down", "close": plain(cl(br[0], side)), "candle_utc": _iso(br[0].start),
                           "swing": plain(lows[1].price)}
                    vote = -1
            else:
                br = [c for c in _closes_after(cs, latest.candle_utc) if cl(c, side) >= highs[1].price + beyond]
                if br:
                    bos = {"way": "up", "close": plain(cl(br[0], side)), "candle_utc": _iso(br[0].start),
                           "swing": plain(highs[1].price)}
                    vote = 1
            if bos:
                ev.append(f"break of structure {bos['way']}: 4-hour close {bos['close']} ({uk_short(br[0].start)}) "
                          f"{'below the swing low' if bos['way'] == 'down' else 'above the swing high'} {bos['swing']} "
                          f"after the latest swing {latest.kind}")
    v1 = v1_direction(highs, lows, v1_broken)
    # supporting EMA votes
    votes = {"stack": 0, "vs_ema100": 0, "ema100_slope": 0}
    last = cs[-1] if cs else None
    if last is not None:
        e7, e13, e21 = (h4_frame.ema_now(p) for p in (7, 13, 21))
        if None not in (e7, e13, e21):
            votes["stack"] = -1 if e7 < e13 < e21 else 1 if e7 > e13 > e21 else 0
            ev.append(f"4-hour EMA 7/13/21: {'down' if votes['stack'] < 0 else 'up' if votes['stack'] > 0 else 'mixed'}")
        e100 = h4_frame.ema_now(100)
        if e100 is not None:
            c = cl(last, side)
            votes["vs_ema100"] = -1 if c < e100 else 1 if c > e100 else 0
            ev.append(f"4-hour close {plain(c)} {'below' if c < e100 else 'above'} the EMA100 {plain(e100.quantize(Decimal('0.1')))}")
            n = settings.planner.ema_slope_candles
            s100 = h4_frame.ema.get(100, {})
            if len(cs) > n and cs[-1 - n].start in s100:
                slope = s100[last.start] - s100[cs[-1 - n].start]
                minimum = params.ema_slope_min_pips * ppp(settings)
                votes["ema100_slope"] = -1 if slope <= -minimum else 1 if slope >= minimum else 0
                ev.append(f"4-hour EMA100 slope {plain(_pips(settings, slope))} pips over {n} candles")
    ema_sum = sum(votes.values())
    score = vote + ema_sum
    effective_vote = vote
    if vote == 0 and params.mixed_allows_ema_consensus and abs(ema_sum) == 3 and not broken_against:
        ev.append("mixed structure, but all three 4-hour EMA votes agree (consensus option)")
    elif vote == 0:
        score = 0 if not broken_against else ema_sum      # mixed without consensus: no direction
    dirn = NEUTRAL
    if effective_vote <= 0 and score <= -params.min_score:
        dirn = BEARISH
    elif effective_vote >= 0 and score >= params.min_score:
        dirn = BULLISH
    if broken_against and dirn != NEUTRAL and not params.mixed_allows_ema_consensus:
        dirn = NEUTRAL                                    # a broken structure is never directional by default
    ev.append(f"score {score} (structure {vote}, EMAs {ema_sum}): {dirn}")
    return DirectionView(dirn, score, vote, votes, ev, _pips(settings, tol), highs, lows, marginal, bos,
                         broken_against, v1)


# ======================================================================================================================
# B. market phase, C. opportunity
# ======================================================================================================================

@dataclass
class PhaseView:
    as_of: datetime
    direction: DirectionView
    phase: str
    evidence: list[str]
    exhaustion: dict = field(default_factory=dict)          # each evidence name -> True/False
    facts: dict = field(default_factory=dict)
    opportunity: str | None = None                          # TREND_ALIGNED / COUNTERTREND_CORRECTION / STRUCTURAL_REVERSAL
    opportunity_trade: str | None = None                    # BUY / SELL
    countertrend: dict | None = None
    continuation: dict | None = None
    expected_next: str | None = None
    authorises: bool = False                                # always False: research, observe only

    def as_dict(self) -> dict:
        return {"as_of_utc": _iso(self.as_of), "direction": self.direction.as_dict(), "phase": self.phase,
                "evidence": self.evidence, "exhaustion": self.exhaustion, "facts": self.facts,
                "opportunity": self.opportunity, "opportunity_trade": self.opportunity_trade,
                "countertrend": self.countertrend, "continuation": self.continuation,
                "expected_next": self.expected_next, "authorises": False}


def _rejection_candle(c: Any, side: str, bear: bool, extreme: Decimal, near: Decimal, need_colour: bool) -> bool:
    h, l_, o, c_ = hi(c, side), lo(c, side), op(c, side), cl(c, side)
    rng = h - l_
    if rng <= 0:
        return False
    if bear:      # rejection of lower prices (a buy-side rejection) at the low
        ok = l_ <= extreme + near and (min(o, c_) - l_) >= rng / 2 and c_ >= l_ + rng / 2
        return ok and (c_ > o if need_colour else True)
    ok = h >= extreme - near and (h - max(o, c_)) >= rng / 2 and c_ <= h - rng / 2
    return ok and (c_ < o if need_colour else True)


def meaningful(z: Zone, strict: bool = True) -> bool:
    """A zone is meaningful by structural evidence, not because it is near. Strict (the default): a Major zone, or a
    Moderate zone holding a higher-timeframe level (a 4-hour or daily swing, a daily or weekly pivot or R/S, the
    previous day's or week's high or low). Hourly swings, round numbers, session highs and lows and moving averages
    alone are intraday detail. Loose (evaluated as the alternative): at least Moderate, or any structural level."""
    if strict:
        return z.klass == MAJOR or (CLASS_RANK[z.klass] >= CLASS_RANK[MODERATE] and any(m.kind in HTF_KINDS for m in z.members))
    if CLASS_RANK[z.klass] >= CLASS_RANK[MODERATE]:
        return True
    return any(m.kind in STRUCTURAL_KINDS or (m.kind == "session high/low" and m.fixed) for m in z.members)


def opposing(settings: Any, zones: Sequence[Zone] | None, levels: Sequence[MapLevel] | None, price: Decimal,
             upward: bool, min_gap: Decimal, extreme: Decimal | None = None, strict: bool = True) -> tuple[Zone | None, MapLevel | None]:
    """(first meaningful opposing zone, first obstacle of any kind) in the countertrend direction (upward: above
    price): a zone whose far edge is at least `min_gap` beyond price (a zone containing price is the one being entered)
    and which is clear of the extreme the move started from (the launching support is not the opposing level)."""
    near = Decimal(settings.rejection.near_level_within_pips) * ppp(settings)
    zs = list(zones or [])
    if upward:
        ahead = sorted([z for z in zs if z.high >= price + min_gap and (extreme is None or z.low - near > extreme)],
                       key=lambda z: z.low)
    else:
        ahead = sorted([z for z in zs if z.low <= price - min_gap and (extreme is None or z.high + near < extreme)],
                       key=lambda z: -z.high)
    first = next((z for z in ahead if meaningful(z, strict)), None)
    obs = None
    if levels:
        cands = [m for m in levels if (m.price >= price + min_gap if upward else m.price <= price - min_gap)]
        if cands:
            obs = min(cands, key=lambda m: abs(m.price - price))
    return first, obs


@dataclass
class PhaseInputs:
    """What the phase model reads at one moment. Every candle in it had finished by `as_of`."""
    as_of: datetime
    h4: Any                          # planner.measure.Frame (finished 4-hour candles and indicators)
    h1: Any                          # planner.measure.Frame (finished hourly candles and indicators)
    h4_swings: list[Swing]           # 4-hour swings known by as_of (known_utc <= as_of), oldest first
    fives: list[Any]                 # finished 5-minute candles (at least those after the last hourly candle)
    adr: Decimal | None
    zones: list[Zone] | None = None  # the planner's zones at as_of (planner/zones.py), for opposing levels
    levels: list[MapLevel] | None = None
    spread: Decimal | None = None    # the latest 5-minute close's buy-sell spread (points)


def assess_phase(settings: Any, inp: PhaseInputs, params: PhaseParams = DEFAULT) -> PhaseView:
    side = settings.chart.price
    P = ppp(settings)
    near = Decimal(settings.rejection.near_level_within_pips) * P
    beyond = Decimal(settings.hourly_read.break_beyond_pips) * P
    dv = dominant(settings, inp.h4, inp.h4_swings, inp.adr, params)
    h1 = inp.h1.candles
    view = PhaseView(inp.as_of, dv, CONSOLIDATION, [])
    if not h1 or not inp.fives:
        view.evidence.append("no finished hourly or 5-minute candles")
        return view
    after = [c for c in inp.fives if c.start >= h1[-1].end]
    price = cl(inp.fives[-1], side)
    spread = inp.spread if inp.spread is not None else Decimal("1.5") * P
    adr = inp.adr
    view.facts["price"] = plain(price)
    if dv.broken_against:
        view.phase = STRUCTURAL_REVERSAL
        view.opportunity = REVERSAL
        view.opportunity_trade = "BUY" if dv.broken_against["way"] == "up" else "SELL"
        view.evidence.append("the 4-hour structure is broken against its direction")
        view.expected_next = "a new structure must form; no trend-aligned or countertrend plan until it does"
        return view
    if dv.direction == NEUTRAL or adr is None:
        view.phase = CONSOLIDATION
        band = inp.h1.band.get(h1[-1].start)
        if band is not None and adr:
            view.facts["h1_band_width_adr"] = plain(((band.upper - band.lower) / adr).quantize(Decimal("0.01")))
        view.evidence.append("no dominant direction" if adr else "no ADR yet")
        return view
    bear = dv.direction == BEARISH
    start = dv.highs[-1] if bear else dv.lows[-1]
    pool = [c for c in h1 if c.start >= start.candle_utc]
    if not pool:
        view.phase = TREND_IMPULSE
        view.evidence.append("no hourly candle since the impulse began")
        return view
    ext_fn = (lambda c: lo(c, side)) if bear else (lambda c: hi(c, side))
    cext_fn = (lambda c: hi(c, side)) if bear else (lambda c: lo(c, side))
    further = (lambda a, b: a < b) if bear else (lambda a, b: a > b)
    i_e = 0                                        # the first hourly candle that made the extreme
    for i, c in enumerate(pool):
        if further(ext_fn(c), ext_fn(pool[i_e])):
            i_e = i
    E = ext_fn(pool[i_e])
    e_hour = pool[i_e]
    fives = inp.fives
    e_five = None
    in_hour = [c for c in fives if e_hour.start <= c.start < e_hour.end]
    if in_hour:                                    # the 5-minute candle inside that hour that made it
        best = min(in_hour, key=lambda c: lo(c, side)) if bear else max(in_hour, key=lambda c: hi(c, side))
        e_five = next(c for c in in_hour if ext_fn(c) == ext_fn(best))
    five_new = [c for c in after if further(ext_fn(c), E)]
    if five_new:                                   # a new extreme in the 5-minute candles of the running hour
        best = min(five_new, key=lambda c: lo(c, side)) if bear else max(five_new, key=lambda c: hi(c, side))
        e_five = next(c for c in five_new if ext_fn(c) == ext_fn(best))
        E = ext_fn(e_five)
    e_time = e_five.start if e_five else e_hour.start
    e_end = e_five.end if e_five else e_hour.end
    covered_from = fives[0].start
    later5 = [c for c in fives if c.start >= e_end]
    later1 = [c for c in h1 if c.start >= e_end and c.end <= covered_from]
    cands = later1 + later5
    bars_since = sum(1 for c in h1 if c.start >= e_end) + len([c for c in after if c.start >= e_end]) / 12
    bars_since = round(bars_since, 2)
    post = [c for c in h1 if c.start >= e_hour.end]
    if cands:
        c_candle = max(cands, key=lambda c: cext_fn(c)) if bear else min(cands, key=lambda c: cext_fn(c))
        C = cext_fn(c_candle)
    else:
        c_candle, C = None, E
    impulse_points = abs(start.price - E)
    view.facts.update({"impulse_start": start.describe(), "impulse_extreme": plain(E), "impulse_extreme_utc": _iso(e_time),
                       "hours_since_extreme": bars_since, "corrective_extreme": plain(C),
                       "correction_pips": plain(_pips(settings, abs(C - E))),
                       "impulse_pips": plain(_pips(settings, impulse_points)),
                       "retracement": plain((abs(C - E) / impulse_points).quantize(Decimal("0.01"))) if impulse_points else None,
                       "spread_pips": plain(_pips(settings, spread))})
    # ---- exhaustion evidence ----------------------------------------------------------------------------------------
    W = params.exhaustion_window_h1
    recent = h1[-W:]
    lower_line = Decimal(settings.indicators.rsi_lower_line)
    upper_line = Decimal(settings.indicators.rsi_upper_line)
    pierce = Decimal(settings.bounce.pierce_beyond_pips) * P
    ex: dict[str, bool] = {k: False for k in EVIDENCE}
    band_now = inp.h1.band.get(h1[-1].start)
    last_close = price
    if band_now is not None:
        outside = [c for c in recent if c.start in inp.h1.band and (
            (cl(c, side) < inp.h1.band[c.start].lower or lo(c, side) < inp.h1.band[c.start].lower - pierce) if bear else
            (cl(c, side) > inp.h1.band[c.start].upper or hi(c, side) > inp.h1.band[c.start].upper + pierce))]
        back = (last_close >= band_now.lower) if bear else (last_close <= band_now.upper)
        ex["band_extension"] = bool(outside) and back
    rs = [inp.h1.rsi[c.start] for c in recent if c.start in inp.h1.rsi]
    if rs:
        ex["rsi_recovery"] = (any(r < lower_line for r in rs) and rs[-1] >= lower_line) if bear else \
            (any(r > upper_line for r in rs) and rs[-1] <= upper_line)
    hist = [inp.h1.macd[c.start].histogram for c in h1[-3:] if c.start in inp.h1.macd]
    if len(hist) == 3:
        ex["macd_contraction"] = (hist[-1] < 0 and hist[-1] > hist[-2] > hist[-3]) if bear else \
            (hist[-1] > 0 and hist[-1] < hist[-2] < hist[-3])
    rej = any(_rejection_candle(c, side, bear, E, near, False) for c in h1[-2:]) or \
        any(_rejection_candle(c, side, bear, E, near, True) for c in inp.fives[-3:])
    ex["rejection_candle"] = rej
    e21 = inp.h1.ema.get(21, {})
    e_candle = e_hour
    if adr and e_candle.start in e21:
        gap = (e21[e_candle.start] - E) if bear else (E - e21[e_candle.start])
        ex["extension_from_ema21"] = gap >= params.extension_adr * adr
        view.facts["extension_from_ema21_adr"] = plain((gap / adr).quantize(Decimal("0.01")))
    if inp.zones:
        sup = [z for z in inp.zones if meaningful(z, params.strict_meaningful) and z.low - near <= E <= z.high + near]
        ex["at_support"] = bool(sup)
        if sup:
            view.facts["extreme_at_zone"] = f"{plain(sup[0].low)}-{plain(sup[0].high)} ({sup[0].klass})"
    h4c = inp.h4.candles[-2:]
    ex["h4_band_extension"] = any(c.start in inp.h4.band and (
        lo(c, side) < inp.h4.band[c.start].lower if bear else hi(c, side) > inp.h4.band[c.start].upper) for c in h4c)
    view.exhaustion = ex
    n_ex = sum(ex.values())
    view.facts["exhaustion_count"] = n_ex
    # ---- correction ---------------------------------------------------------------------------------------------
    mids = [c for c in post if (c.start in e21 and (cl(c, side) > e21[c.start] if bear else cl(c, side) < e21[c.start]))
            or (c.start in inp.h1.band and (cl(c, side) > inp.h1.band[c.start].middle if bear else
                                            cl(c, side) < inp.h1.band[c.start].middle))]
    corr = bool(mids) or abs(C - E) >= params.correction_min_adr * adr
    min_gap = max(2 * spread, near)
    mzones = [z for z in (inp.zones or []) if meaningful(z, params.strict_meaningful)]

    def closed_beyond(z: Zone) -> bool:          # an hourly close since the extreme through the zone's far edge
        return any((cl(c, side) >= z.high + beyond) if bear else (cl(c, side) <= z.low - beyond) for c in post)

    # the zone the correction is testing NOW: the latest hour (and the 5-minute candles after it) reached it, and no
    # hourly close has gone through it
    testing = None
    if corr:
        latest = (max([hi(c, side) for c in h1[-1:]] + [hi(c, side) for c in after]) if bear else
                  min([lo(c, side) for c in h1[-1:]] + [lo(c, side) for c in after]))
        hit = [z for z in mzones if ((z.low - near <= latest <= z.high + near) if bear else (z.low - near <= latest <= z.high + near))
               and ((z.low - near) > E if bear else (z.high + near) < E) and not closed_beyond(z)]
        if hit:
            testing = max(hit, key=lambda z: z.low) if bear else min(hit, key=lambda z: z.high)
            view.facts["testing_zone"] = f"{plain(testing.low)}-{plain(testing.high)} ({testing.klass})"
    # the zone the correction's extreme C reached (the resistance it tested)
    tested = None
    hit_c = [z for z in mzones if z.low - near <= C <= z.high + near and ((z.low - near) > E if bear else (z.high + near) < E)]
    if hit_c and corr:
        tested = max(hit_c, key=lambda z: z.low) if bear else min(hit_c, key=lambda z: z.high)
        view.facts["tested_zone"] = f"{plain(tested.low)}-{plain(tested.high)} ({tested.klass})"
    # continuation: renewed alignment + a rejection after the corrective extreme C
    cont = None
    if corr and c_candle is not None:
        after_c5 = [c for c in later5 if c.start > c_candle.start]
        after_c1 = [c for c in post if c.start >= c_candle.end]
        e7, e13 = inp.h1.ema_now(7), inp.h1.ema_now(13)
        aligned = e7 is not None and e13 is not None and (e7 < e13 if bear else e7 > e13)
        was_beyond = bool(mids)
        back = h1[-1].start in e21 and h1[-1].start >= c_candle.start and (
            cl(h1[-1], side) < e21[h1[-1].start] if bear else cl(h1[-1], side) > e21[h1[-1].start])
        seg = [c for c in cands if c_candle.start - timedelta(hours=1) <= c.start < c_candle.start]   # the last leg's base
        support = (min(lo(c, side) for c in seg) if bear else max(hi(c, side) for c in seg)) if seg else None
        broke_support = support is not None and ((price <= support - beyond) if bear else (price >= support + beyond))
        rejected = (was_beyond and back) or broke_support
        not_through = tested is None or not closed_beyond(tested)
        if aligned and rejected and (after_c1 or len(after_c5) >= 3) and not_through:
            cont = {"trade": "SELL" if bear else "BUY", "corrective_extreme": plain(C),
                    "invalidation": f"an hourly close at or {'above' if bear else 'below'} {plain(C + beyond if bear else C - beyond)}",
                    "invalidation_price": plain(C + beyond if bear else C - beyond),
                    "destination": plain(E), "corrective_support": plain(support) if support is not None else None,
                    "why": ("renewed hourly EMA7/13 alignment; " +
                            ("close back through the hourly EMA21 after the correction" if (was_beyond and back) else
                             f"close through the corrective support {plain(support)}")),
                    "needs": "an independently valid strategy entry trigger and the existing risk approval",
                    "authorises": False}
    # ---- the phase -----------------------------------------------------------------------------------------------
    word = "low" if bear else "high"
    turning = any(ex[k] for k in TURN)
    exhausted = n_ex >= params.exhaustion_min_evidence and (turning or not params.require_turn)
    recent = bars_since <= params.impulse_recent_h1 + 1
    signs = ", ".join(k for k, v in ex.items() if v) or "none"
    if corr and cont is not None:
        view.phase = TREND_CONTINUATION
        view.evidence.append("correction ended: " + cont["why"])
    elif corr and testing is not None:
        view.phase = RESISTANCE_TEST if bear else SUPPORT_TEST
        view.evidence.append(f"the correction reached the meaningful {'resistance' if bear else 'support'} "
                             f"{plain(testing.low)}-{plain(testing.high)} ({testing.klass})")
    elif corr:
        view.phase = COUNTERTREND_CORRECTION
        view.evidence.append(f"correction under way: {plain(_pips(settings, abs(C - E)))} pips from the {word}"
                             + (", an hourly close beyond the hourly EMA21 / Bollinger middle" if mids else ""))
    elif recent:
        view.phase = EXHAUSTION if exhausted else TREND_IMPULSE
        view.evidence.append(f"new {word} {plain(E)} {bars_since} hours ago; exhaustion signs: {signs}")
    elif exhausted and bars_since <= W:
        view.phase = EXHAUSTION
        view.evidence.append(f"exhaustion signs within {bars_since} hours of the {word}, no correction yet: {signs}")
    elif abs(price - E) <= params.stall_adr * adr and bars_since >= params.stall_hours:
        view.phase = CONSOLIDATION
        view.evidence.append(f"price within {plain(params.stall_adr)} x ADR of the {word} for {bars_since} hours, no correction")
    else:
        view.phase = TREND_IMPULSE
        view.evidence.append(f"impulse pausing: no new {word} for {bars_since} hours, no correction")
    # ---- opportunities ---------------------------------------------------------------------------------------------
    trend_trade, counter_trade = ("SELL", "BUY") if bear else ("BUY", "SELL")
    context = [k for k in ("extension_from_ema21", "at_support", "h4_band_extension") if ex.get(k)]
    view.facts["exhaustion_context"] = context
    view.facts["recent_extreme"] = recent
    if view.phase in (EXHAUSTION, COUNTERTREND_CORRECTION) or (view.phase == TREND_IMPULSE and recent):
        first_m, obs = opposing(settings, inp.zones, inp.levels, price, upward=bear, min_gap=min_gap, extreme=E,
                                 strict=params.strict_meaningful)
        entry_ref = price + spread if bear else price - spread       # a buy fills at the offer (sell + spread)
        inval = E - beyond if bear else E + beyond
        ct = {"trade": counter_trade, "authorises": False,
              "entry_zone": [plain(E), plain(E + near * 2)] if bear else [plain(E - near * 2), plain(E)],
              "structural_invalidation": f"an hourly close at or {'below' if bear else 'above'} {plain(inval)} "
                                         f"({settings.hourly_read.break_beyond_pips} pips beyond the {word} {plain(E)})",
              "invalidation_price": plain(inval),
              "first_obstacle": None if obs is None else {"name": obs.name, "price": plain(obs.price), "family": obs.family},
              "first_meaningful": None if first_m is None else {
                  "low": plain(first_m.low), "high": plain(first_m.high), "class": first_m.klass,
                  "families": first_m.families, "levels": [f"{m.name} {plain(m.price)}" for m in first_m.members]},
              "exhaustion_evidence": [k for k, v in ex.items() if v]}
        if first_m is not None:
            inside = first_m.low <= price <= first_m.high
            # price already inside the zone: the trade buys into resistance (sells into support), and the zone's far
            # edge is the most it can expect; otherwise the zone's near edge (price reaching the level)
            dest = (first_m.high if inside else first_m.low) if bear else (first_m.low if inside else first_m.high)
            ct["inside_opposing_zone"] = inside
            room = (dest - entry_ref) if bear else (entry_ref - dest)
            from_low = (dest - (E + spread)) if bear else ((E - spread) - dest)
            ct["room_pips_from_extreme"] = plain(_pips(settings, from_low))
            risk = (entry_ref - inval) if bear else (inval - entry_ref)
            ct["corrective_destination"] = plain(dest)
            ct["room_pips_after_spread"] = plain(_pips(settings, room))
            ct["risk_pips_to_invalidation"] = plain(_pips(settings, risk))
            ct["room_to_risk"] = plain((room / risk).quantize(Decimal("0.01"))) if risk > 0 else None
            need = max(params.room_min_pips * P, params.room_spread_multiple * spread)
            ct["room_sufficient"] = room >= need
            ct["room_needed_pips"] = plain(_pips(settings, need))
            ct["maximum_expected"] = plain(first_m.high if bear else first_m.low)
            # a correction that has already reached this zone and fallen back has spent its opportunity
            if (C >= first_m.low - near) if bear else (C <= first_m.high + near):
                if abs(price - C) > near * 2:
                    ct["spent"] = True
                    ct["room_sufficient"] = False
            ct["return_to_trend"] = {"trade": trend_trade, "at": f"{plain(first_m.low)}-{plain(first_m.high)}",
                                     "needs": "rejection of that level, then an independently valid strategy "
                                              f"{trend_trade} trigger and the existing risk approval (never a reversal "
                                              "of the open trade)", "authorises": False}
        else:
            ct["corrective_destination"] = None
            ct["room_sufficient"] = False
            ct["note"] = "no meaningful opposing level identified within the zone window"
        view.countertrend = ct
        if view.phase == TREND_IMPULSE:          # kept for a strategy's own reversal trigger (classify_trade)
            ct["needs_turn"] = "no turn sign yet: only a strategy's own reversal pattern could supply it"
            view.opportunity, view.opportunity_trade = TREND_ALIGNED, trend_trade
            view.expected_next = f"exhaustion signs would open a countertrend {counter_trade}"
            return view
        view.opportunity = COUNTERTREND if ct["room_sufficient"] else None
        view.opportunity_trade = counter_trade if ct["room_sufficient"] else None
        view.expected_next = (f"{trend_trade} after a confirmed rejection at "
                              + (f"{plain(first_m.low)}-{plain(first_m.high)}" if first_m else "the first meaningful level"))
        if view.opportunity is None:
            view.opportunity = TREND_ALIGNED if view.phase == COUNTERTREND_CORRECTION else None
            view.opportunity_trade = trend_trade if view.opportunity else None
    elif view.phase in (TREND_IMPULSE, RESISTANCE_TEST, SUPPORT_TEST, TREND_CONTINUATION):
        view.opportunity, view.opportunity_trade = TREND_ALIGNED, trend_trade
        if view.phase == TREND_CONTINUATION:
            view.continuation = cont
            view.expected_next = f"{trend_trade}s toward {plain(E)} and beyond; a new {word} returns the phase to TREND_IMPULSE"
        elif view.phase in (RESISTANCE_TEST, SUPPORT_TEST):
            view.expected_next = f"a rejection here would open a return-to-trend {trend_trade}"
        else:
            view.expected_next = f"exhaustion signs would open a countertrend {counter_trade}"
    return view


REVERSAL_PATTERN_STRATEGIES = frozenset({"Bollinger bounce", "level reversal", "session sweep", "New York open reversal",
                                         "range trade"})


def classify_trade(view: PhaseView, trade_direction: str, reversal_trigger: bool = False) -> tuple[str, str]:
    """How a trade in `trade_direction` ("buy"/"sell") relates to the phase view: a label and a reason. It never
    authorises anything (view.authorises is always False). `reversal_trigger`: the trade comes from a strategy's own
    reversal pattern (REVERSAL_PATTERN_STRATEGIES); right after a new extreme that pattern can supply the turn the
    phase model has not yet seen on the hourly chart, provided at least 2 exhaustion-context signs are present."""
    d = view.direction.direction
    t = trade_direction.upper()
    if view.phase == STRUCTURAL_REVERSAL:
        return REVERSAL, "the 4-hour structure is broken against its direction"
    if d == NEUTRAL:
        return NO_VIEW, "no dominant direction"
    trend = "SELL" if d == BEARISH else "BUY"
    if t == trend:
        caution = ""
        if view.phase == EXHAUSTION:
            caution = "; caution: exhaustion evidence at the extreme, a correction is likely before continuation"
        elif view.phase == COUNTERTREND_CORRECTION:
            caution = "; caution: a correction is under way and has not been rejected yet"
        return TREND_ALIGNED, f"{t} with the {d} dominant direction (phase {view.phase}){caution}"
    ct = view.countertrend or {}
    context = view.facts.get("exhaustion_context") or []
    candidate = view.phase in (EXHAUSTION, COUNTERTREND_CORRECTION) or (
        reversal_trigger and view.phase == TREND_IMPULSE and view.facts.get("recent_extreme") and len(context) >= 2)
    if not candidate:
        return UNSUPPORTED, f"{t} against the {d} direction in phase {view.phase}: no exhaustion or correction evidence"
    how = (f"phase {view.phase}" if view.phase != TREND_IMPULSE else
           f"a new extreme with exhaustion context ({', '.join(context)}) and the strategy's reversal pattern as the turn")
    if ct.get("room_sufficient"):
        return COUNTERTREND, (f"{t} against the {d} direction, {how}: first meaningful level {ct['first_meaningful']['low']}-"
                              f"{ct['first_meaningful']['high']}, destination {ct['corrective_destination']} "
                              f"({ct['room_pips_after_spread']} pips after the spread)")
    if ct.get("spent"):
        return UNSUPPORTED, f"{t} against the {d} direction, {how}: the correction has already reached the first meaningful level"
    if ct.get("corrective_destination"):
        return UNSUPPORTED, (f"{t} against the {d} direction, {how}: recognised as a correction, but only "
                             f"{ct['room_pips_after_spread']} pips to the first meaningful level "
                             f"{ct['first_meaningful']['low']}-{ct['first_meaningful']['high']} after the spread "
                             f"(needs {ct['room_needed_pips']})")
    return UNSUPPORTED, f"{t} against the {d} direction, {how}: no meaningful opposing level identified"


def summary(view: PhaseView) -> dict:
    """A compact record for tables."""
    ct = view.countertrend or {}
    fm = ct.get("first_meaningful") or {}
    return {"as_of_utc": _iso(view.as_of), "direction": view.direction.direction, "v1_direction": view.direction.v1_direction,
            "score": view.direction.score, "structure_vote": view.direction.structure_vote, "phase": view.phase,
            "opportunity": view.opportunity, "opportunity_trade": view.opportunity_trade,
            "exhaustion": [k for k, v in view.exhaustion.items() if v],
            "impulse_extreme": view.facts.get("impulse_extreme"), "corrective_extreme": view.facts.get("corrective_extreme"),
            "first_meaningful": f"{fm.get('low')}-{fm.get('high')} {fm.get('class')}" if fm else None,
            "corrective_destination": ct.get("corrective_destination"), "room_pips": ct.get("room_pips_after_spread"),
            "room_sufficient": ct.get("room_sufficient"),
            "continuation_invalidation": (view.continuation or {}).get("invalidation_price"),
            "authorises": False}


__all__ = [n for n in dir() if n.isupper() or n in ("PhaseParams", "DEFAULT", "dominant", "assess_phase", "classify_trade",
                                                     "PhaseInputs", "PhaseView", "DirectionView", "meaningful", "opposing",
                                                     "summary", "v1_direction", "asdict")]
