"""STP technical opportunities (GitHub issue #3, 20 November 2026). OBSERVE ONLY: never contacts IG, never places or
changes an order, never feeds the planner's recommendation lifecycle (planner/keeper.py is untouched).

It reads the H1 and H4 charts the way a chart reader does, not as a single 4-hour direction gate, and names the
nearest credible next opportunity in either direction:
  PULLBACK          trend continuation: price pulls back into the H1 EMA (and any resistance/support there);
  REVERSAL          a reaction at a support/resistance zone of the existing map, even against the 4-hour trend;
  RANGE_REVERSAL    the same at a range boundary found from the H1 candles themselves (the "grey box");
  BREAKOUT          a confirmed close through a zone or range boundary that is still holding: trade the retest;
  FAILED_BREAKOUT   a close or wick through a zone or boundary, then a close back inside: trade the other way.
Each candidate collects evidence for and against (each item one point, every one written out with its value). The
nearest credible candidate wins: entry within one zone width of price first, then the most evidence, then
the nearer entry. Below [stp_technical] min_evidence nothing is
forced: the result is "no credible opportunity", with the best candidate shown and the reason.

What it reuses (no new indicator code, no new service): the planner snapshot (planner/measure.py: finished candles
only, sell price, the bot's own EMA/Bollinger/RSI code), the existing level map and zones (planner/zones.py,
including the approved 156-week historical map and no distance cut-off), the existing swing rule
(planner/structure.py), the existing STP plan for the 4-hour direction and condition (planner/assess.py, unchanged),
the ADR, the zone width (P-C3), the 3-pip touch/near rule and the 3-pip confirmed-break rule.

New numbers ([stp_technical], all PROVISIONAL, for the owner to approve): the H1 EMA period (20, as in the issue), the
RSI period (14) for RSI direction, the trend look-back (12 H1 candles), the H1 average-range window (14), the stop
buffer (0.3 of the H1 average range, at least the 3-pip break rule), the range look-back (48 H1 candles), the range's
minimum tests (2) and drift limit (the EMA moved less than 0.25 of the range height), the minimum evidence (4) and
how long a forecast waits for its entry (8 hours, used by the lifecycle replay).

Demonstrated by the PIA First example of 20 November 2026 (08:57): a SELL entered at the H1 EMA20 in a bearish
structure, after a doji from the pullback high, with RSI declining; nearby support at the cluster of recent hourly lows;
resistance at the pullback high; an extended target at an older level. Hypothesised (not shown by the example, so
each is a setting): the stop buffer as a share of the H1 average range, the range rules, the breakout rules and the
evidence threshold. No price from the example is used anywhere.

Two invalidations are kept apart: the TRADE invalidation is the stop (price touches it); the STRUCTURAL invalidation
(the forecast map is wrong) needs a confirmed H1 close beyond a structural level (the last H1 swing, or the stop
for a reaction), so a normal 3-pip overshoot of a zone does not end the forecast.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Sequence

from planner.measure import Snapshot, cl, hi, lo, op, pips, ppp, side_of
from planner.structure import Swing, structure, swings
from planner.zones import CLASS_RANK, MAJOR, MOVING_AVERAGE, Zone, label, level_map, zone_width, zones
from prices.indicators import ema, rsi
from prices.model import plain, uk_short

PULLBACK, REVERSAL, RANGE_REVERSAL, BREAKOUT, FAILED_BREAKOUT = (
    "PULLBACK", "REVERSAL", "RANGE_REVERSAL", "BREAKOUT", "FAILED_BREAKOUT")
KIND_TEXT = {PULLBACK: "trend-continuation pullback", REVERSAL: "reversal at support/resistance",
             RANGE_REVERSAL: "reversal at a range boundary", BREAKOUT: "breakout continuation (retest)",
             FAILED_BREAKOUT: "failed breakout"}
BUY, SELL = "BUY", "SELL"
OBSERVE_ONLY = "OBSERVE ONLY - DOES NOT CONTROL TRADING"
Q = Decimal("0.1")


def _q(x: Decimal) -> Decimal:
    return Decimal(x).quantize(Q)


# ---- the chart read --------------------------------------------------------------------------------------------------

@dataclass
class CandleShape:
    start: datetime
    kind: str               # doji, bearish rejection, bullish rejection, bearish body, bullish body, plain
    high: Decimal
    low: Decimal
    open: Decimal
    close: Decimal

    def text(self) -> str:
        return (f"{uk_short(self.start)} H1 {self.kind} (O {plain(self.open)} H {plain(self.high)} "
                f"L {plain(self.low)} C {plain(self.close)})")


def shape(c, side: str) -> CandleShape:
    """A candle's shape: doji when the body is at most a quarter of the range; a rejection when one wick is at least half
    of the range; otherwise a body candle when the body is at least half of the range."""
    o, h, l, c_ = op(c, side), hi(c, side), lo(c, side), cl(c, side)
    rng = h - l
    body = abs(c_ - o)
    up_wick, down_wick = h - max(o, c_), min(o, c_) - l
    if rng <= 0:
        kind = "doji"
    elif up_wick * 2 >= rng and up_wick > down_wick:
        kind = "bearish rejection"
    elif down_wick * 2 >= rng and down_wick > up_wick:
        kind = "bullish rejection"
    elif body * 4 <= rng:
        kind = "doji"
    elif body * 2 >= rng:
        kind = "bearish body" if c_ < o else "bullish body"
    else:
        kind = "plain"
    return CandleShape(c.start, kind, h, l, o, c_)


@dataclass
class ChartRead:
    """What the H1 chart shows at the last finished candle (all prices sell, in points)."""
    close: Decimal
    ema: Decimal                      # the H1 EMA ([stp_technical] h1_ema_period)
    ema_period: int
    ema_slope: Decimal                # points per candle over the trend look-back
    ema_prev_trend: Decimal           # the EMA trend_candles ago
    ema21: Decimal | None
    ema100: Decimal | None
    ema100_slope: Decimal | None
    bb_lower: Decimal | None
    bb_mid: Decimal | None
    bb_upper: Decimal | None
    bb_mid_slope: Decimal | None
    bb_width: Decimal | None
    bb_width_before: Decimal | None   # three candles earlier
    rsi: Decimal | None
    rsi_prev: Decimal | None
    rsi_min3: Decimal | None          # lowest RSI over the last three candles
    rsi_max3: Decimal | None
    avg_range: Decimal                # H1 average high-low range
    last: list[CandleShape]           # the last two finished H1 candles, oldest first
    structure: str                    # existing swing rule on H1: up, down, mixed
    structure_why: str
    swings: list[Swing] = field(default_factory=list)

    @property
    def flat(self) -> bool:
        return abs(self.ema_slope) * 10 < self.avg_range      # moves less than 0.1 of an average hour per candle


def read_h1(settings: Any, snap: Snapshot) -> ChartRead | None:
    t = settings.stp_technical
    side = side_of(settings)
    cs = snap.h1.candles
    need = max(t.h1_ema_period * 3, t.range_lookback_candles, t.trend_candles + 2, t.avg_range_candles)
    if len(cs) < need:
        return None
    e = ema(cs, side, t.h1_ema_period)
    r = rsi(cs, side, t.rsi_periods)
    last = cs[-1]
    k = t.trend_candles
    e_now, e_then = e.get(last.start), e.get(cs[-1 - k].start)
    if e_now is None or e_then is None:
        return None
    e100 = snap.h1.ema.get(100)
    band = snap.h1.band

    def b(i, attr):
        v = band.get(cs[i].start)
        return getattr(v, attr) if v is not None else None
    width = lambda i: (b(i, "upper") - b(i, "lower")) if b(i, "upper") is not None else None   # noqa: E731
    rs = [r.get(c.start) for c in cs[-3:]]
    found = swings(settings, cs[-400:], "1h")
    st = structure(settings, cs[-400:], "1h", found)
    rngs = [hi(c, side) - lo(c, side) for c in cs[-t.avg_range_candles:]]
    e100_now = e100.get(last.start) if e100 else None
    e100_then = e100.get(cs[-7].start) if e100 else None
    mid_now, mid_then = b(-1, "middle"), b(-4, "middle")
    return ChartRead(
        close=cl(last, side), ema=e_now, ema_period=t.h1_ema_period, ema_slope=(e_now - e_then) / k, ema_prev_trend=e_then,
        ema21=snap.h1.ema_now(21), ema100=e100_now,
        ema100_slope=(e100_now - e100_then) / 6 if e100_now is not None and e100_then is not None else None,
        bb_lower=b(-1, "lower"), bb_mid=mid_now, bb_upper=b(-1, "upper"),
        bb_mid_slope=(mid_now - mid_then) / 3 if mid_now is not None and mid_then is not None else None,
        bb_width=width(-1), bb_width_before=width(-4),
        rsi=rs[-1], rsi_prev=rs[-2], rsi_min3=min((x for x in rs if x is not None), default=None),
        rsi_max3=max((x for x in rs if x is not None), default=None),
        avg_range=sum(rngs, Decimal(0)) / len(rngs), last=[shape(c, side) for c in cs[-2:]],
        structure=st.sequence, structure_why=st.why, swings=found)


# ---- range from the candles (the "grey box") ------------------------------------------------------------------------

@dataclass
class Range:
    low: Decimal
    high: Decimal
    band: Decimal                 # each boundary is a band this deep inside the range
    tests_low: int
    tests_high: int
    since: datetime

    def text(self) -> str:
        return (f"H1 range {plain(_q(self.low))}-{plain(_q(self.high))} since {uk_short(self.since)} "
                f"(top tested {self.tests_high}x, bottom {self.tests_low}x)")


def _tests(prices: Sequence[Decimal], level: Decimal, band: Decimal, upper: bool, gap: int = 3) -> int:
    """Distinct touches of a boundary band: candles reaching into it, counted again only after `gap` candles away."""
    n, last = 0, -10 ** 6
    for i, p in enumerate(prices):
        inside = p >= level - band if upper else p <= level + band
        if inside and i - last > gap:
            n += 1
        if inside:
            last = i
    return n


def find_range(settings: Any, snap: Snapshot, read: ChartRead, band: Decimal) -> Range | None:
    """A range: over range_lookback_candles H1 candles ending just before the most recent
    planner.failed_breakout_within_candles (so that a breakout or a false break of it can still be judged), both the
    highest high and the lowest low were reached at least range_min_tests separate times (within `band`, the zone
    half-width), the H1 EMA drifted less than range_max_ema_drift_share of the range height, and the close at its end
    was inside. Derived from the candles only."""
    t = settings.stp_technical
    side = side_of(settings)
    k = settings.planner.failed_breakout_within_candles
    cs = snap.h1.candles[-t.range_lookback_candles - k:-k]
    highs, lows = [hi(c, side) for c in cs], [lo(c, side) for c in cs]
    top, bottom = max(highs), min(lows)
    if top - bottom <= 2 * band:
        return None
    e = ema(snap.h1.candles, side, t.h1_ema_period)
    drift = abs(e[cs[-1].start] - e[cs[0].start])
    if drift > Decimal(str(t.range_max_ema_drift_share)) * (top - bottom):
        return None
    th, tl = _tests(highs, top, band, True), _tests(lows, bottom, band, False)
    if th < t.range_min_tests or tl < t.range_min_tests or not (bottom < cl(cs[-1], side) < top):
        return None
    return Range(bottom, top, band, tl, th, cs[0].start)


# ---- opportunities ---------------------------------------------------------------------------------------------------

@dataclass
class Opportunity:
    kind: str
    trade: str
    entry_low: Decimal
    entry_high: Decimal
    entry_basis: str
    stop: Decimal
    stop_basis: str
    structural_level: Decimal
    structural_text: str
    evidence: list[tuple[int, str]] = field(default_factory=list)
    countertrend: bool = False
    target1: tuple[Decimal, str] | None = None
    target2: tuple[Decimal, str] | None = None
    alternative: str = ""
    confluence: list[str] = field(default_factory=list)

    @property
    def score(self) -> int:
        return sum(p for p, _ in self.evidence)

    def distance(self, price: Decimal) -> Decimal:
        if self.entry_low <= price <= self.entry_high:
            return Decimal(0)
        return min(abs(price - self.entry_low), abs(price - self.entry_high))

    def add(self, ok: bool, text: str, points: int = 1) -> None:
        if ok:
            self.evidence.append((points, text))


@dataclass
class Context:
    settings: Any
    snap: Snapshot
    read: ChartRead
    plan: dict
    zones: list[Zone]
    rng: Range | None
    half: Decimal                 # half the zone width (P-C3)
    near: Decimal                 # the 3-pip touch rule
    beyond: Decimal               # the 3-pip confirmed-break rule
    buffer: Decimal               # the stop buffer

    @property
    def price(self) -> Decimal:
        return self.snap.price

    @property
    def h4(self) -> str:
        return self.plan.get("dominant_direction") or "UNKNOWN"


def _fixed_levels_in(ctx: Context, low: Decimal, high: Decimal) -> list[str]:
    out = []
    for z in ctx.zones:
        for m in z.members:
            if low <= m.price <= high and m.family != MOVING_AVERAGE:
                out.append(label(m))
    return out


def targets(ctx: Context, trade: str, entry_low: Decimal, entry_high: Decimal, dynamic: Sequence[tuple[Decimal, str]] = ()):
    """The nearest intermediate destination beyond the entry zone in the trade's direction (any zone of the existing map,
    or a dynamic level such as the H1 EMA or Bollinger middle for a reaction), and an extended target: the next zone of
    at least Moderate class beyond it. No minimum distance. A target must also lie wholly beyond the current price: one
    price is inside or has already passed is not a destination (the D-1 principle of the existing STP)."""
    sell = trade == SELL
    p0 = ctx.price
    cands = []
    for z in ctx.zones:
        if sell and z.high < entry_low and z.high < p0:
            cands.append((z.high, f"{z.klass} zone {plain(z.low)}-{plain(z.high)} ({', '.join(label(m) for m in z.members[:4])})", z))
        elif not sell and z.low > entry_high and z.low > p0:
            cands.append((z.low, f"{z.klass} zone {plain(z.low)}-{plain(z.high)} ({', '.join(label(m) for m in z.members[:4])})", z))
    for p, why in dynamic:
        if p is not None and ((sell and p < entry_low and p < p0) or (not sell and p > entry_high and p > p0)):
            cands.append((_q(p), why, None))
    if not cands:
        return None, None
    cands.sort(key=lambda x: -x[0] if sell else x[0])
    t1 = cands[0]
    ext = [c for c in cands[1:] if c[2] is not None and CLASS_RANK[c[2].klass] >= CLASS_RANK["Moderate"]
           and ((c[0] < t1[0]) if sell else (c[0] > t1[0]))]
    return (t1[0], t1[1]), ((ext[0][0], ext[0][1]) if ext else None)


def _opposite_zone(ctx: Context, trade: str, low: Decimal, high: Decimal) -> str:
    beyond = [z for z in ctx.zones if (z.low > high if trade == SELL else z.high < low)]
    if not beyond:
        return "no mapped zone beyond it"
    z = min(beyond, key=lambda z: z.low) if trade == SELL else max(beyond, key=lambda z: z.high)
    return f"{z.klass} zone {plain(z.low)}-{plain(z.high)}"


def _alternative(ctx: Context, o: Opportunity) -> str:
    if o.trade == SELL:
        lvl = o.entry_high + ctx.beyond
        return (f"If instead an H1 candle closes at or above {plain(_q(lvl))} and price holds above the stop "
                f"{plain(_q(o.stop))}, the resistance has given way: look for a BUY on a retest, towards the "
                f"{_opposite_zone(ctx, SELL, o.entry_low, o.entry_high)}.")
    lvl = o.entry_low - ctx.beyond
    return (f"If instead an H1 candle closes at or below {plain(_q(lvl))} and price holds below the stop "
            f"{plain(_q(o.stop))}, the support has given way: look for a SELL on a retest, towards the "
            f"{_opposite_zone(ctx, BUY, o.entry_low, o.entry_high)}.")


def _h4_points(o: Opportunity, ctx: Context, sell: bool) -> None:
    want, against = ("BEARISH", "BULLISH") if sell else ("BULLISH", "BEARISH")
    if ctx.h4 == want:
        o.add(True, f"the 4-hour direction (existing STP) is {want}")
    elif ctx.h4 == against:
        o.countertrend = True
        o.evidence.append((-1, f"against the 4-hour direction (existing STP: {against}): countertrend, lower confidence"))


def _rejection(ctx: Context, sell: bool, low: Decimal, high: Decimal) -> CandleShape | None:
    """A rejection or doji in the last two H1 candles that reached the zone (from below for a sell, above for a buy)."""
    for s in reversed(ctx.read.last):
        reached = s.high >= low - ctx.near if sell else s.low <= high + ctx.near
        if reached and (s.kind == "doji" or s.kind == ("bearish rejection" if sell else "bullish rejection")):
            return s
    return None


def _rsi_turn(ctx: Context, sell: bool) -> str | None:
    r = ctx.read
    if r.rsi is None or r.rsi_prev is None:
        return None
    if sell and r.rsi < r.rsi_prev:
        return f"RSI({ctx.settings.stp_technical.rsi_periods}) declining ({plain(_q(r.rsi_prev))} to {plain(_q(r.rsi))})"
    if not sell and r.rsi > r.rsi_prev:
        return f"RSI({ctx.settings.stp_technical.rsi_periods}) rising ({plain(_q(r.rsi_prev))} to {plain(_q(r.rsi))})"
    return None


def pullback(ctx: Context, sell: bool) -> Opportunity | None:
    """Trend continuation: price pulls back into the H1 EMA in a trend. The trend context needs at least two of: the
    4-hour direction, a falling (rising) H1 EMA over the trend look-back, the H1 EMA21 below (above) a falling (rising)
    EMA100. The entry zone is the EMA plus/minus half the zone width; the price must not already be beyond it."""
    r, s = ctx.read, ctx.settings
    sign = -1 if sell else 1
    trend_ema = r.ema_slope * sign > 0 and not r.flat
    stack = (r.ema21 is not None and r.ema100 is not None and r.ema100_slope is not None
             and (r.ema21 < r.ema100 if sell else r.ema21 > r.ema100) and r.ema100_slope * sign > 0)
    h4 = ctx.h4 == ("BEARISH" if sell else "BULLISH")
    if sum((trend_ema, stack, h4)) < 2:
        return None
    low, high = _q(r.ema - ctx.half), _q(r.ema + ctx.half)
    if (sell and ctx.price > high + ctx.beyond) or (not sell and ctx.price < low - ctx.beyond):
        return None                                    # already through the EMA: not a pullback any more
    last_swing = [w for w in r.swings if w.kind == ("high" if sell else "low")]
    beyond_zone = [w for w in reversed(last_swing) if (w.price > high if sell else w.price < low)]
    stop = (high + ctx.buffer) if sell else (low - ctx.buffer)
    if beyond_zone:
        sl = beyond_zone[0].price
        structural = (sl + ctx.beyond) if sell else (sl - ctx.beyond)
        stext = (f"an H1 close at or {'above' if sell else 'below'} {plain(_q(structural))} (beyond the last H1 swing "
                 f"{'high' if sell else 'low'} {plain(sl)}): the {'down' if sell else 'up'}trend structure is broken")
    else:
        structural = (stop + ctx.beyond) if sell else (stop - ctx.beyond)
        stext = f"an H1 close at or {'above' if sell else 'below'} {plain(_q(structural))} (beyond the stop by the break rule)"
    o = Opportunity(PULLBACK, SELL if sell else BUY, low, high,
                    f"H1 EMA{r.ema_period} {plain(_q(r.ema))} +/- {plain(_q(ctx.half))} (half the zone width)",
                    _q(stop), f"{plain(_q(ctx.buffer))} beyond the entry zone (0.3 x H1 average range "
                    f"{plain(_q(r.avg_range))}, at least the break rule)", _q(structural), stext)
    _h4_points(o, ctx, sell)
    o.add(trend_ema, f"H1 EMA{r.ema_period} {'falling' if sell else 'rising'}: {plain(_q(r.ema_prev_trend))} to "
          f"{plain(_q(r.ema))} over {s.stp_technical.trend_candles} candles")
    o.add(stack, f"H1 EMA21 {plain(_q(r.ema21))} {'below' if sell else 'above'} a {'falling' if sell else 'rising'} "
          f"EMA100 {plain(_q(r.ema100))}" if stack else "")
    tested = any((sh.high >= low - ctx.near) if sell else (sh.low <= high + ctx.near) for sh in r.last)
    o.add(tested, f"the pullback has reached the EMA zone (last H1 {'high' if sell else 'low'} "
          f"{plain(max(x.high for x in r.last) if sell else min(x.low for x in r.last))})")
    rej = _rejection(ctx, sell, low, high)
    o.add(rej is not None, f"{rej.text()} at the zone" if rej else "")
    turn = _rsi_turn(ctx, sell)
    o.add(turn is not None, turn or "")
    conf = _fixed_levels_in(ctx, low, high + ctx.half) if sell else _fixed_levels_in(ctx, low - ctx.half, high)
    o.confluence = conf
    o.add(bool(conf), f"{'resistance' if sell else 'support'} at the EMA zone: {', '.join(conf[:3])}")
    o.add(r.bb_mid_slope is not None and r.bb_mid_slope * sign > 0,
          f"Bollinger middle {'falling' if sell else 'rising'} ({plain(_q(r.bb_mid))})" if r.bb_mid is not None else "")
    o.add(r.structure == ("down" if sell else "up"), f"H1 structure {r.structure}: {r.structure_why}")
    if r.flat:
        o.evidence.append((-1, f"H1 EMA{r.ema_period} flat ({plain(_q(r.ema_slope))}/candle): no H1 trend to continue"))
    return o


def reaction(ctx: Context, sell: bool, z_low: Decimal, z_high: Decimal, what: str, kind: str, major: bool,
             tests: int) -> Opportunity | None:
    """A reversal at resistance (SELL) or support (BUY): price at or within the 3-pip touch rule of the zone, and a
    reaction already showing (a rejection/doji there, or RSI turning from beyond its line, or a close back inside the
    Bollinger band). Allowed against the 4-hour direction (marked countertrend)."""
    r, s = ctx.read, ctx.settings
    p = ctx.price
    at = (z_low - ctx.half <= p <= z_high + ctx.near) if sell else (z_low - ctx.near <= p <= z_high + ctx.half)
    touched = any((sh.high >= z_low - ctx.near) if sell else (sh.low <= z_high + ctx.near) for sh in r.last)
    # price must have come INTO the zone from the trade's far side: below a resistance (above a support) at the close
    # planner.failed_breakout_within_candles H1 candles ago, so one zone is never support and resistance at once
    k = s.planner.failed_breakout_within_candles
    before = cl(ctx.snap.h1.candles[-k - 1], side_of(s))
    approached = before < z_low if sell else before > z_high
    if not (at and touched and approached):
        return None
    rej = _rejection(ctx, sell, z_low, z_high)
    ind = s.indicators
    rsi_turn = (r.rsi is not None and r.rsi_prev is not None and
                ((r.rsi_max3 is not None and r.rsi_max3 >= ind.rsi_upper_line and r.rsi < r.rsi_prev) if sell else
                 (r.rsi_min3 is not None and r.rsi_min3 <= ind.rsi_lower_line and r.rsi > r.rsi_prev)))
    band_back = (r.bb_upper is not None and any(sh.high >= r.bb_upper for sh in r.last) and r.close < r.bb_upper) if sell else \
        (r.bb_lower is not None and any(sh.low <= r.bb_lower for sh in r.last) and r.close > r.bb_lower)
    if not (rej or rsi_turn or band_back):
        return None                                    # no reaction yet: watch, do not forecast
    ext = max(sh.high for sh in r.last) if sell else min(sh.low for sh in r.last)
    stop = (max(z_high, ext) + ctx.buffer) if sell else (min(z_low, ext) - ctx.buffer)
    structural = (stop + ctx.beyond) if sell else (stop - ctx.beyond)
    o = Opportunity(kind, SELL if sell else BUY, _q(z_low), _q(z_high), what, _q(stop),
                    f"{plain(_q(ctx.buffer))} beyond the zone and the reaction {'high' if sell else 'low'} {plain(ext)}",
                    _q(structural), f"an H1 close at or {'above' if sell else 'below'} {plain(_q(structural))} (beyond the "
                    f"stop by the break rule): the {'resistance' if sell else 'support'} has failed; a smaller overshoot "
                    f"does not end the forecast")
    _h4_points(o, ctx, sell)
    o.add(major, f"{what} is Major" if kind == REVERSAL else what)
    o.add(tests >= 2, f"tested {tests} times before")
    o.add(rej is not None, f"{rej.text()}" if rej else "")
    o.add(rsi_turn, f"RSI({s.stp_technical.rsi_periods}) turning from {'above' if sell else 'below'} "
          f"{ind.rsi_upper_line if sell else ind.rsi_lower_line} ({plain(_q(r.rsi_prev))} to {plain(_q(r.rsi))})"
          if rsi_turn else "")
    o.add(band_back, f"back inside the Bollinger band after touching the {'upper' if sell else 'lower'} band "
          f"({plain(_q(r.bb_upper if sell else r.bb_lower))})" if band_back else "")
    o.add(r.flat or (r.ema_slope < 0 if sell else r.ema_slope > 0),
          f"H1 EMA{r.ema_period} {'flat' if r.flat else ('rising' if r.ema_slope > 0 else 'falling')} "
          f"({plain(_q(r.ema_slope))}/candle): no strong trend into the zone")
    return o


def breakouts(ctx: Context, sell: bool, z_low: Decimal, z_high: Decimal, what: str, strong: bool) -> list[Opportunity]:
    """Breakout continuation and failed breakout at one zone/boundary, from the last failed_breakout_within_candles H1
    candles (existing setting, 3). An upside break: a close at least the break rule above the zone top. Still holding at
    the last close: BREAKOUT, BUY the retest. Back inside after a close or a wick through: FAILED_BREAKOUT, SELL. The
    `sell` flag here is the side of the zone: True for a resistance (upside break), False for a support."""
    s, r = ctx.settings, ctx.read
    side = side_of(s)
    k = s.planner.failed_breakout_within_candles
    recent = ctx.snap.h1.candles[-k:]
    before = ctx.snap.h1.candles[-k - 1]
    out = []
    up = sell
    edge = z_high if up else z_low
    started_inside = (cl(before, side) < edge + ctx.beyond) if up else (cl(before, side) > edge - ctx.beyond)
    if not started_inside:
        return out
    closes_beyond = [c for c in recent if (cl(c, side) >= edge + ctx.beyond if up else cl(c, side) <= edge - ctx.beyond)]
    wicks_beyond = [c for c in recent if (hi(c, side) >= edge + ctx.beyond if up else lo(c, side) <= edge - ctx.beyond)]
    last_close = cl(recent[-1], side)
    holding = last_close >= edge + ctx.beyond if up else last_close <= edge - ctx.beyond
    back_inside = last_close < edge if up else last_close > edge
    if closes_beyond and holding:
        low, high = (_q(max(z_low, edge - ctx.half)), _q(edge + ctx.near)) if up else (_q(edge - ctx.near), _q(min(z_high, edge + ctx.half)))
        stop = (low - ctx.buffer) if up else (high + ctx.buffer)
        # back through the whole zone, and never nearer than the break rule beyond the stop
        structural = min(z_low, stop) - ctx.beyond if up else max(z_high, stop) + ctx.beyond
        o = Opportunity(BREAKOUT, BUY if up else SELL, low, high, f"retest of the broken {what}", _q(stop),
                        f"{plain(_q(ctx.buffer))} back inside the broken zone", _q(structural),
                        f"an H1 close at or {'below' if up else 'above'} {plain(_q(structural))}: back through the whole "
                        f"zone, the breakout has failed")
        _h4_points(o, ctx, not up)
        o.add(True, f"confirmed H1 close {plain(cl(closes_beyond[0], side))} {'above' if up else 'below'} {plain(edge)} "
                    f"(at least {plain(ctx.beyond)} beyond) and still holding at {plain(last_close)}")
        o.add(strong, f"the broken level is {what}")
        o.add(r.bb_width is not None and r.bb_width_before is not None and r.bb_width > r.bb_width_before,
              f"Bollinger band widening ({plain(_q(r.bb_width_before or 0))} to {plain(_q(r.bb_width or 0))})")
        o.add(r.rsi is not None and (r.rsi > 50 if up else r.rsi < 50),
              f"RSI({s.stp_technical.rsi_periods}) {plain(_q(r.rsi or 0))} on the breakout side of 50")
        o.add(r.ema_slope * (1 if up else -1) > 0 and not r.flat, f"H1 EMA{r.ema_period} sloping with the breakout")
        bs = shape(closes_beyond[-1], side)
        o.add(bs.kind == ("bullish body" if up else "bearish body"), f"breakout candle {bs.text()}")
        out.append(o)
    elif (closes_beyond or wicks_beyond) and back_inside:
        ext = max(hi(c, side) for c in recent) if up else min(lo(c, side) for c in recent)
        low, high = (_q(max(z_low, edge - ctx.half)), _q(edge)) if up else (_q(edge), _q(min(z_high, edge + ctx.half)))
        stop = (ext + ctx.buffer) if up else (ext - ctx.buffer)
        structural = (stop + ctx.beyond) if up else (stop - ctx.beyond)
        o = Opportunity(FAILED_BREAKOUT, SELL if up else BUY, low, high, f"back inside the {what}", _q(stop),
                        f"{plain(_q(ctx.buffer))} beyond the false-break {'high' if up else 'low'} {plain(ext)}",
                        _q(structural), f"an H1 close at or {'above' if up else 'below'} {plain(_q(structural))} (beyond "
                        f"the stop by the break rule): a real breakout after all")
        _h4_points(o, ctx, up)
        o.add(True, f"{'a close' if closes_beyond else 'a wick'} through {plain(edge)} to {plain(ext)}, then an H1 close "
                    f"back inside at {plain(last_close)}")
        o.add(strong, f"the level is {what}")
        rej = _rejection(ctx, up, z_low, z_high)
        o.add(rej is not None, rej.text() if rej else "")
        turn = _rsi_turn(ctx, up)
        o.add(turn is not None, turn or "")
        band = r.bb_upper if up else r.bb_lower
        o.add(band is not None and ((ext >= band and last_close < band) if up else (ext <= band and last_close > band)),
              f"pierced the {'upper' if up else 'lower'} Bollinger band ({plain(_q(band or 0))}) and closed back inside")
        out.append(o)
    return out


# ---- the forecast ----------------------------------------------------------------------------------------------------

def candidates(ctx: Context) -> list[Opportunity]:
    s = ctx.settings
    min_rank = CLASS_RANK[s.planner.min_entry_class]
    out: list[Opportunity] = []
    for sell in (True, False):
        o = pullback(ctx, sell)
        if o:
            out.append(o)
    for z in ctx.zones:
        if CLASS_RANK[z.klass] < min_rank:
            continue
        what = f"{z.klass} zone {plain(z.low)}-{plain(z.high)} ({', '.join(label(m) for m in z.members[:4])})"
        major = z.klass == MAJOR
        if z.low >= ctx.price - ctx.near or z.low <= ctx.price <= z.high:            # resistance above (or here)
            o = reaction(ctx, True, z.low, z.high, what, REVERSAL, major, z.tests)
            if o:
                out.append(o)
            out += breakouts(ctx, True, z.low, z.high, what, major)
        if z.high <= ctx.price + ctx.near or z.low <= ctx.price <= z.high:           # support below (or here)
            o = reaction(ctx, False, z.low, z.high, what, REVERSAL, major, z.tests)
            if o:
                out.append(o)
            out += breakouts(ctx, False, z.low, z.high, what, major)
    if ctx.rng:
        g = ctx.rng
        top = (g.high - g.band, g.high)
        bottom = (g.low, g.low + g.band)
        for sell, (a, b) in ((True, top), (False, bottom)):
            what = f"{'top' if sell else 'bottom'} of the {g.text()}"
            o = reaction(ctx, sell, a, b, what, RANGE_REVERSAL, True, g.tests_high if sell else g.tests_low)
            if o:
                out.append(o)
            out += breakouts(ctx, sell, a, b, what, True)
    final = []
    for o in out:
        dyn = [] if o.kind in (PULLBACK, BREAKOUT) else [
            (ctx.read.ema, f"H1 EMA{ctx.read.ema_period} {plain(_q(ctx.read.ema))}"),
            (ctx.read.bb_mid, f"Bollinger middle {plain(_q(ctx.read.bb_mid))}" if ctx.read.bb_mid is not None else "")]
        if ctx.rng and o.kind in (RANGE_REVERSAL, FAILED_BREAKOUT):
            dyn.append((ctx.rng.low if o.trade == SELL else ctx.rng.high, f"the opposite side of the {ctx.rng.text()}"))
        o.target1, o.target2 = targets(ctx, o.trade, o.entry_low, o.entry_high, dyn)
        if o.target1 is None:
            continue                                    # nowhere to go: not an opportunity
        o.alternative = _alternative(ctx, o)
        final.append(o)
    # the nearest credible opportunity: set-ups whose entry zone is within one zone width of price come first (a
    # distant pullback is a conditional forecast), then the most evidence, then the nearer entry
    final.sort(key=lambda o: (o.distance(ctx.price) > 2 * ctx.half, -o.score, o.distance(ctx.price), o.kind))
    return final


def _opp_dict(settings: Any, o: Opportunity, price: Decimal, adr: Decimal | None) -> dict:
    ref = price if o.entry_low <= price <= o.entry_high else (o.entry_low if price < o.entry_low else o.entry_high)
    if o.trade == SELL and price > o.entry_high:
        ref = o.entry_high
    if o.trade == BUY and price < o.entry_low:
        ref = o.entry_low
    risk = abs(o.stop - ref)
    d = {"type": o.kind, "type_text": KIND_TEXT[o.kind], "trade": o.trade, "countertrend": o.countertrend,
         "entry_zone": {"low": plain(o.entry_low), "high": plain(o.entry_high), "basis": o.entry_basis},
         "status": "price is in the entry zone" if o.entry_low <= price <= o.entry_high else
                   f"waiting for price to reach the entry zone ({plain(pips(settings, o.distance(price)))} pips away)",
         "reference_entry": plain(_q(ref)),
         "stop": {"price": plain(o.stop), "basis": o.stop_basis, "pips_from_entry": plain(pips(settings, risk))},
         "trade_invalidation": f"price touches the stop {plain(o.stop)}",
         "structural_invalidation": {"price": plain(o.structural_level), "text": o.structural_text},
         "intermediate_target": {"price": plain(o.target1[0]), "basis": o.target1[1],
                                 "pips_from_entry": plain(pips(settings, abs(o.target1[0] - ref)))},
         "extended_target": None if o.target2 is None else {
             "price": plain(o.target2[0]), "basis": o.target2[1], "pips_from_entry": plain(pips(settings, abs(o.target2[0] - ref)))},
         "evidence": [{"points": p, "text": t} for p, t in o.evidence], "score": o.score,
         "alternative": o.alternative, "confluence": o.confluence}
    if risk > 0:
        d["reward_to_risk"] = plain((abs(o.target1[0] - ref) / risk).quantize(Decimal("0.1")))
    if adr:
        d["intermediate_target"]["adr"] = plain((abs(o.target1[0] - ref) / adr).quantize(Decimal("0.01")))
    return d


def forecast(settings: Any, snap: Snapshot, existing: Any, plan: dict) -> dict:
    """The technical forecast at the snapshot's time. `plan` is the existing STP plan at the same time (context only:
    its 4-hour direction and condition are used as evidence, never changed)."""
    t = settings.stp_technical
    out = {"pair": settings.market.pair, "as_of_utc": snap.as_of.strftime("%Y-%m-%dT%H:%M:%SZ"),
           "h1_candle_utc": snap.h1.last.start.strftime("%Y-%m-%dT%H:%M:%SZ") if snap.h1.last else None,
           "observe_only": OBSERVE_ONLY, "fresh": snap.fresh, "price": plain(snap.price) if snap.price is not None else None,
           "h4_direction": plan.get("dominant_direction"), "condition": plan.get("condition"),
           "existing_stp": {"trade": plan.get("trade"), "no_recommendation": plan.get("no_recommendation")},
           "opportunity": None, "no_opportunity": None, "candidates": [], "chart": None}
    if not snap.fresh:
        out["no_opportunity"] = "the data is not fresh: no forecast (" + "; ".join(snap.stale_reasons) + ")"
        return out
    if snap.price is None or snap.adr is None:
        out["no_opportunity"] = "not enough finished candles (price or ADR missing)"
        return out
    read = read_h1(settings, snap)
    if read is None:
        out["no_opportunity"] = "not enough finished H1 candles for the chart read"
        return out
    h4_found = swings(settings, snap.h4.candles, "4h")
    d1_found = swings(settings, snap.d1.candles, "1d")
    lmap = level_map(settings, snap, existing, h4_found, d1_found,
                     include_intraday_opportunity_levels=True)
    zs = zones(settings, lmap, snap.adr, snap.h1.candles, snap.price)
    half = zone_width(settings, snap.adr) / 2
    near = Decimal(settings.rejection.near_level_within_pips) * ppp(settings)
    beyond = Decimal(settings.planner.break_beyond_pips) * ppp(settings)
    buffer = max(beyond, Decimal(str(t.stop_buffer_range_share)) * read.avg_range)
    rng = find_range(settings, snap, read, half)
    ctx = Context(settings, snap, read, plan, zs, rng, half, near, beyond, buffer)
    h1_trend = "flat" if read.flat else ("falling" if read.ema_slope < 0 else "rising")
    out["chart"] = {
        "h1_close": plain(read.close), f"h1_ema{read.ema_period}": plain(_q(read.ema)), "h1_ema_slope_per_candle": plain(_q(read.ema_slope)),
        "h1_ema_trend": h1_trend, "h1_ema21": plain(_q(read.ema21)) if read.ema21 is not None else None,
        "h1_ema100": plain(_q(read.ema100)) if read.ema100 is not None else None,
        "bollinger": None if read.bb_mid is None else {"lower": plain(_q(read.bb_lower)), "middle": plain(_q(read.bb_mid)),
                                                       "upper": plain(_q(read.bb_upper)), "width": plain(_q(read.bb_width)),
                                                       "widening": bool(read.bb_width_before is not None and read.bb_width > read.bb_width_before)},
        f"rsi{t.rsi_periods}": plain(_q(read.rsi)) if read.rsi is not None else None,
        "rsi_direction": None if read.rsi is None or read.rsi_prev is None else
        ("declining" if read.rsi < read.rsi_prev else "rising" if read.rsi > read.rsi_prev else "flat"),
        "last_h1_candles": [s.text() for s in read.last], "h1_structure": read.structure, "h1_structure_why": read.structure_why,
        "h1_average_range_pips": plain(pips(settings, read.avg_range)), "adr_pips": plain(pips(settings, snap.adr)),
        "range": rng.text() if rng else None, "stop_buffer_pips": plain(pips(settings, buffer)),
        "zone_half_width_pips": plain(pips(settings, half))}
    cands = candidates(ctx)
    out["bias"] = _bias(plan, read, rng)
    out["candidates"] = [{"type": o.kind, "trade": o.trade, "score": o.score,
                          "entry_zone": f"{plain(o.entry_low)}-{plain(o.entry_high)}"} for o in cands[:6]]
    if not cands:
        out["no_opportunity"] = ("no credible opportunity: no pullback, reaction or breakout set-up with a destination "
                                 "beyond it")
        return out
    credible = [o for o in cands if o.score >= t.min_evidence]
    best = credible[0] if credible else cands[0]
    if best.score < t.min_evidence:
        out["no_opportunity"] = (f"no credible opportunity: the best set-up ({KIND_TEXT[best.kind]} {best.trade} at "
                                 f"{plain(best.entry_low)}-{plain(best.entry_high)}) has {best.score} evidence points, "
                                 f"below the minimum {t.min_evidence}")
        out["best_candidate"] = _opp_dict(settings, best, snap.price, snap.adr)
        return out
    out["opportunity"] = _opp_dict(settings, best, snap.price, snap.adr)
    others = [o for o in credible if o is not best and o.trade != best.trade]
    if others:
        out["opposite_candidate"] = _opp_dict(settings, others[0], snap.price, snap.adr)
    return out


def _bias(plan: dict, read: ChartRead, rng: Range | None) -> str:
    h4 = plan.get("dominant_direction") or "UNKNOWN"
    h1 = "flat" if read.flat else ("down" if read.ema_slope < 0 else "up")
    cond = "ranging (" + rng.text() + ")" if rng else ("trending " + h1 if h1 != "flat" else "no clear H1 trend")
    return f"4-hour {h4}; H1 EMA{read.ema_period} {h1}; H1 structure {read.structure}; {cond}"


def technical_at(settings: Any, store: Any, as_of: datetime, calendar: list | None = None) -> dict:
    """The technical forecast at `as_of` from the candle store (finished candles only). Writes nothing."""
    from levels.current import build
    from planner.assess import assess
    from planner.measure import snapshot
    snap = snapshot(settings, store, as_of)
    existing = build(settings, store, as_of)
    plan = assess(settings, snap, existing, calendar or [], None).as_dict()
    return forecast(settings, snap, existing, plan)


def describe(f: dict) -> list[str]:
    """The forecast in words, for a person."""
    out = [f"STP TECHNICAL FORECAST - {f['pair']}   ({OBSERVE_ONLY})",
           f"as at {f['as_of_utc']} (last H1 candle {f['h1_candle_utc']}); price {f['price']}"]
    if f.get("bias"):
        out.append(f"Bias:      {f['bias']}")
    out.append(f"Existing STP: 4-hour {f['h4_direction']}, condition {f['condition']}; "
               f"{f['existing_stp']['trade'] or '-'}{' (no recommendation: ' + f['existing_stp']['no_recommendation'] + ')' if f['existing_stp']['no_recommendation'] else ''}")
    ch = f.get("chart")
    if ch:
        ema_key = [k for k in ch if k.startswith("h1_ema") and k[6:].isdigit()][0]
        rsi_key = [k for k in ch if k.startswith("rsi") and k[3:].isdigit()][0]
        out.append(f"Chart:     H1 close {ch['h1_close']}; {ema_key.upper()} {ch[ema_key]} ({ch['h1_ema_trend']}, "
                   f"{ch['h1_ema_slope_per_candle']}/candle); EMA21 {ch['h1_ema21']}, EMA100 {ch['h1_ema100']}; "
                   f"{rsi_key.upper()} {ch[rsi_key]} {ch['rsi_direction']}")
        if ch["bollinger"]:
            b = ch["bollinger"]
            out.append(f"           Bollinger {b['lower']} / {b['middle']} / {b['upper']} ({'widening' if b['widening'] else 'not widening'}); "
                       f"H1 average range {ch['h1_average_range_pips']} pips, ADR {ch['adr_pips']} pips")
        out += [f"           {c}" for c in ch["last_h1_candles"]]
        if ch["range"]:
            out.append(f"           {ch['range']}")
    o = f.get("opportunity")
    if not o:
        out += ["", f"NO OPPORTUNITY: {f['no_opportunity']}"]
        return out
    z, s = o["entry_zone"], o["stop"]
    out += ["", f"Opportunity: {o['type_text']} - {o['trade']}" + ("  (COUNTERTREND)" if o["countertrend"] else ""),
            f"Entry zone:  {z['low']}-{z['high']} ({z['basis']}); {o['status']}; reference entry {o['reference_entry']}",
            f"Stop:        {s['price']} ({s['pips_from_entry']} pips; {s['basis']})",
            f"Target:      {o['intermediate_target']['price']} ({o['intermediate_target']['pips_from_entry']} pips; "
            f"{o['intermediate_target']['basis']})"]
    if o["extended_target"]:
        out.append(f"Extended:    {o['extended_target']['price']} ({o['extended_target']['pips_from_entry']} pips; "
                   f"{o['extended_target']['basis']})")
    out += [f"Trade invalidation:      {o['trade_invalidation']}",
            f"Structural invalidation: {o['structural_invalidation']['text']}",
            f"Why ({o['score']} evidence points):"] + [f"   {'+' if e['points'] > 0 else ''}{e['points']} {e['text']}" for e in o["evidence"]]
    out.append(f"Alternative: {o['alternative']}")
    return out


def write(settings: Any, store: Any, now: datetime) -> dict | None:
    """Only when [stp_technical] enabled: the forecast now, to planner.folder/<PAIR>/technical.json (replaced each run)
    and once per new H1 candle to technical.jsonl (the history). Separate files: the recommendation lifecycle's own files
    (current.json, recommendations.jsonl, issued.jsonl) are never touched."""
    import json
    from pathlib import Path

    from housekeeping.files import safe_write
    if not settings.stp_technical.enabled:
        return None
    f = technical_at(settings, store, now)
    folder = Path(settings.planner.folder) / settings.market.pair
    safe_write(folder / "technical.json", (json.dumps(f, indent=1, default=str) + "\n").encode())
    hist = folder / "technical.jsonl"
    last = None
    if hist.exists():
        with hist.open("rb") as h:
            lines = h.read().splitlines()
        if lines:
            try:
                last = json.loads(lines[-1]).get("h1_candle_utc")
            except ValueError:
                last = None
    if f.get("h1_candle_utc") and f["h1_candle_utc"] != last:
        with hist.open("a") as h:
            h.write(json.dumps(f, default=str) + "\n")
    return f
