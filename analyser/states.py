"""The analyser's five market states (design section 2), one 5-minute candle
at a time, on the sell price. Rules in full: docs/ANALYSER.md.

States and the strategies they allow (section 2.2):
  ranging            range trade
  emerging trend     slow grind, EMA pullback, Bollinger bounce in the trend's direction only
  trend              the same; with the type of trend: slow grind or strong push
  possible reversal  Bollinger bounce
  consolidation      none: watch and wait for a break

How it moves (sections 2.5 to 2.7). Changes caused by something price DID on
this candle happen at once (they are proof in the price itself):
  * a level rejection: the shared rejection part confirms a bounce rejection at
    a STRONG level (market_states.strong_level_types: pivot, R1-R3, S1-S3,
    round numbers, the previous day's high or low; or a turning level that lines
    up with one of those): from consolidation or ranging -> emerging trend in
    the rejection's direction;
  * a breakout: from consolidation, a close beyond a Bollinger band; from
    ranging, closes beyond the same band for persistence_candles in a row ->
    emerging trend that way;
  * the trend proof (section 2.5, "it becomes clear when..."): in an emerging
    trend, a bounce failed at or below the 21 EMA and middle band, then price
    makes a new extreme on the outer band, with the 7/13/21 EMAs stacked, price
    beyond them and beyond the 100 EMA, and the outer band sloping -> trend;
  * in an emerging trend, a confirmed rejection at a strong level the other way
    replaces it with an emerging trend that way (owner's rule);
  * a possible reversal needs BOTH a move of at least
    possible_reversal.min_trend_move_pips since the trend started AND a
    confirmed rejection at a level against it (the shared rejection part's
    confirmation; a single opposite candle is not enough);
  * in a possible reversal: the rejection's trigger -> emerging trend the new
    way; the old trend making a new extreme, or the setup cancelled or expired
    -> back to the old trend.
An emerging trend is cancelled only by persistence_candles closes in a row back
beyond the level it was rejected at (if it started from a level rejection), or
back inside the Bollinger bands (if it started from a breakout).
Changes that depend on a CONDITION (ranging, consolidation, a trend ending
beyond the 100 EMA) need it to hold for persistence_candles candles in a row.
Evidence fades: an emerging trend, trend or possible reversal with nothing new
(no new extreme, no new rejection) for evidence_fades_after_candles ends.

The machine starts fresh at each weekly open, in consolidation ("watch and
wait") with no direction, so a replay of the week reaches exactly the state a
run that never stopped would have.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable

from analyser.features import Features
from prices.model import plain, uk_short
from rejection.watch import BOUNCE, CANCELLED, CONFIRMATION, EXPIRED, SELL, TRIGGER, in_watch_window

RANGING, EMERGING, TREND, POSSIBLE_REVERSAL, CONSOLIDATION = (
    "ranging", "emerging trend", "trend", "possible reversal", "consolidation")
STATES = (RANGING, EMERGING, TREND, POSSIBLE_REVERSAL, CONSOLIDATION)
UP, DOWN, NONE = "up", "down", "none"
SLOW_GRIND, STRONG_PUSH = "slow grind", "strong push"
ALLOWED = {
    RANGING: ("range trade", "Bollinger band bounce"),
    EMERGING: ("slow grind", "EMA pullback", "Bollinger band bounce (trend's direction only)"),
    TREND: ("slow grind", "EMA pullback", "Bollinger band bounce (trend's direction only)"),
    POSSIBLE_REVERSAL: ("Bollinger band bounce",),
    CONSOLIDATION: (),
}
TRENDING = (EMERGING, TREND)


@dataclass(frozen=True)
class StateChange:
    time: datetime                      # start of the 5-minute candle it was decided on (UTC)
    state: str
    direction: str
    trend_type: str | None
    previous_state: str
    previous_direction: str
    reason: str                         # one line
    evidence: tuple[str, ...]

    def as_dict(self) -> dict:
        return {"time_utc": self.time.strftime("%Y-%m-%dT%H:%M:%SZ"), "state": self.state,
                "direction": self.direction, "trend_type": self.trend_type,
                "previous_state": self.previous_state, "previous_direction": self.previous_direction,
                "reason": self.reason, "evidence": list(self.evidence)}

    def line(self) -> str:
        kind = f", {self.trend_type}" if self.trend_type else ""
        return f"{uk_short(self.time)}  {self.state} ({self.direction}{kind}): {self.reason}"


@dataclass
class MarketState:
    state: str
    direction: str
    trend_type: str | None
    since: datetime
    evidence: list[str]

    @property
    def strategies_allowed(self) -> tuple[str, ...]:
        return ALLOWED[self.state]


def _move(direction: str) -> str:
    return DOWN if direction == SELL else UP


def _opposite(d: str) -> str:
    return UP if d == DOWN else DOWN if d == UP else NONE


class StateMachine:
    def __init__(self, settings: Any, week_open: datetime):
        self.s = settings
        self.m = settings.market_states
        self.ppp = Decimal(settings.market.points_per_pip)
        self.flat = self.m.flat_max_pips_per_candle
        self.now = MarketState(CONSOLIDATION, NONE, None, week_open, ["start of the trading week: watch and wait"])
        self.changes: list[StateChange] = []
        self.n = 0                       # candles seen
        self._pending: tuple[str, str, str] | None = None   # (state, direction, reason)
        self._pending_count = 0
        self._type_pending: str | None = None
        self._type_count = 0
        # the current (or watched) trend
        self.start_price: Decimal | None = None
        self.extreme: Decimal | None = None
        self.last_news = 0               # candle number of the last new evidence
        self.failed_bounce = False       # a bounce failed since the last new extreme
        self.breakout_run = (None, 0)    # ranging: (direction, closes beyond the band in a row)
        # a possible reversal remembers the trend it interrupts
        self.reversal_setup: int | None = None
        self.before: tuple[str, str, str | None] | None = None
        # how the emerging trend started: ("level", level type, price) or ("breakout", None, None)
        self.origin: tuple[str, str | None, Decimal | None] | None = None
        self.back_count = 0              # closes in a row back beyond the level / inside the bands

    # ---- the answer -----------------------------------------------------------------------

    def _change(self, f: Features, state: str, direction: str, trend_type: str | None, reason: str,
                evidence: list[str]) -> StateChange:
        prev = self.now
        ch = StateChange(f.candle.start, state, direction, trend_type, prev.state, prev.direction, reason,
                         tuple(evidence))
        self.now = MarketState(state, direction, trend_type, f.candle.start, list(evidence))
        self.changes.append(ch)
        self._pending, self._pending_count = None, 0
        self._type_pending, self._type_count = None, 0
        self.last_news = self.n
        return ch

    def _p(self, x: Decimal | None) -> str:
        return "-" if x is None else plain(x.quantize(Decimal("0.1")))

    def _pips(self, a: Decimal, b: Decimal) -> Decimal:
        return (abs(a - b) / self.ppp).quantize(Decimal("0.1"))

    # ---- conditions --------------------------------------------------------------------------

    def consolidation(self, f: Features) -> tuple[bool, str]:
        m = self.m
        narrow = f.width is not None and (f.width <= m.narrow_band_max_pips or f.narrowing_for >= m.narrowing_candles)
        ok = (narrow and f.mid_slope is not None
              and abs(f.mid_slope) < self.flat and f.no_close_outside and f.avg_body is not None
              and f.avg_body <= m.consolidation_max_body_pips and f.colour_ratio is not None
              and f.colour_ratio <= m.consolidation_colour_max_ratio)
        why = (f"bands {self._p(f.width)} pips wide (narrow: <= {m.narrow_band_max_pips}, or narrowing for "
               f"{m.narrowing_candles} candles: {f.narrowing_for}), middle band {self._p(f.mid_slope)} pips/candle, "
               f"no close outside the bands for {m.consolidation_quiet_candles} candles, average body "
               f"{self._p(f.avg_body)} pips, green/red {self._p(f.colour_ratio)}")
        return ok, why

    def ranging(self, f: Features) -> tuple[bool, str]:
        """Design 2.2: "the Bollinger bands are flat and close together, and price bounces between the
        upper and lower band. The EMAs weave back and forth instead of staying stacked, and the 100 EMA
        is flat." Close together: the width from ranging_min_band_pips to ranging_max_band_pips. Flat:
        the upper and the lower band each move less than ranging_band_flat_max_pips_per_candle (over
        flat_slope_candles). Bounces between: both bands reached within ranging_both_bands_candles."""
        m = self.m
        flat = m.ranging_band_flat_max_pips_per_candle
        ok = (f.width is not None and m.ranging_min_band_pips <= f.width <= m.ranging_max_band_pips
              and f.upper_slope is not None and abs(f.upper_slope) < flat
              and f.lower_slope is not None and abs(f.lower_slope) < flat
              and f.both_bands_recently and f.weave
              and f.ema100_move is not None and f.ema100_move < m.ema100_flat_max_pips)
        why = (f"bands {self._p(f.width)} pips wide (close together: {m.ranging_min_band_pips} to "
               f"{m.ranging_max_band_pips}) and flat (upper {self._p(f.upper_slope)}, lower {self._p(f.lower_slope)} "
               f"pips/candle), both bands reached, EMAs weaving, 100 EMA moved {self._p(f.ema100_move)} pips")
        return ok, why

    def base(self, f: Features) -> tuple[str, str]:
        r, rwhy = self.ranging(f)
        if r:
            return RANGING, rwhy
        c, cwhy = self.consolidation(f)
        return CONSOLIDATION, (cwhy if c else "no direction any more: watch and wait")

    def proof(self, f: Features, d: str, new_extreme: bool) -> tuple[bool, str]:
        m = self.m
        beyond = (lambda a, b: a < b) if d == DOWN else (lambda a, b: a > b)
        band = f.lower if d == DOWN else f.upper
        band_slope = f.lower_slope if d == DOWN else f.upper_slope
        on_band = f.reached_lower if d == DOWN else f.reached_upper
        ok = (new_extreme and self.failed_bounce and on_band and f.stack == d
              and f.stacked_for >= m.ema_stacked_candles
              and None not in (f.ema7, f.ema13, f.ema21, f.ema100, band_slope)
              and all(beyond(f.c, e) for e in (f.ema7, f.ema13, f.ema21, f.ema100))
              and (band_slope <= -self.flat if d == DOWN else band_slope >= self.flat))
        why = (f"a bounce failed under the 21 EMA and middle band, then a new {'low' if d == DOWN else 'high'} "
               f"{self._p(f.l if d == DOWN else f.h)} on the {'lower' if d == DOWN else 'upper'} band "
               f"{self._p(band)}; EMAs 7/13/21 stacked {d} for {f.stacked_for} candles, close {self._p(f.c)} "
               f"{'below' if d == DOWN else 'above'} them and the 100 EMA {self._p(f.ema100)}; band sloping "
               f"{self._p(band_slope)} pips/candle")
        return ok, why

    def push(self, f: Features, d: str) -> bool:
        m = self.m
        share = f.red_share if d == DOWN else f.green_share
        riding = f.closes_on_lower if d == DOWN else f.closes_on_upper
        return (share * 100 >= m.push_colour_body_percent and f.widening is not None
                and f.widening * 100 >= m.push_band_widening_percent and f.fan is not None
                and f.fan >= m.push_ema_fan_pips and riding >= m.push_riding_band_closes)

    def reversal_signs(self, f: Features, d_old: str, setup: Any) -> list[str]:
        """Section 2.6: what points to a possible reversal (evidence only: none is waited for)."""
        signs = []
        if f.macd_hist is not None and ((d_old == DOWN and f.macd_hist < 0) or (d_old == UP and f.macd_hist > 0)):
            signs.append(f"MACD histogram {self._p(f.macd_hist)} still shows the {d_old} move")
        if f.rsi is not None and ((d_old == DOWN and f.rsi < self.s.indicators.rsi_lower_line + 10)
                                  or (d_old == UP and f.rsi > self.s.indicators.rsi_upper_line - 10)):
            signs.append(f"RSI {self._p(f.rsi)}")
        if in_watch_window(self.s, f.candle.start):
            signs.append("in a reversal watch window (time of day)")
        levels = [p["what"] for p in setup.pierced if p["what"] not in ("upper Bollinger band",
                                                                         "lower Bollinger band")]
        if levels:
            signs.append("at a level: " + ", ".join(levels))
        return signs

    # ---- one candle -------------------------------------------------------------------------

    def step(self, f: Features, events: list, setup_of: Callable[[int], Any]) -> StateChange | None:
        self.n += 1
        st, d = self.now.state, self.now.direction
        bounce = [e for e in events if e.version == BOUNCE]

        # the trend's extreme (also kept while a possible reversal watches it)
        new_extreme = False
        watched = d if st in TRENDING else (self.before[1] if st == POSSIBLE_REVERSAL and self.before else NONE)
        if watched in (UP, DOWN) and self.extreme is not None:
            further = f.l < self.extreme if watched == DOWN else f.h > self.extreme
            if further:
                new_extreme = True
            # a counter-coloured candle that stays at or under the 21 EMA / middle band is a failed bounce
            cap = max(x for x in (f.ema21, f.middle) if x is not None) if (f.ema21 or f.middle) else None
            tol = Decimal(self.m.failed_bounce_within_pips) * self.ppp
            if cap is not None:
                if watched == DOWN and f.green and f.h <= cap + tol:
                    self.failed_bounce = True
                if watched == UP and f.red:
                    floor_ = min(x for x in (f.ema21, f.middle) if x is not None)
                    if f.l >= floor_ - tol:
                        self.failed_bounce = True

        def important_rejection(kind: str):
            for e in bounce:
                if e.kind != kind:
                    continue
                stp = setup_of(e.setup)
                if self.strong_levels(stp):        # only a strong level may start or replace an emerging trend
                    yield e, stp

        # ---- possible reversal -----------------------------------------------------------
        if st == POSSIBLE_REVERSAL and self.before is not None:
            old_state, old_dir, old_type = self.before
            for e in bounce:
                if e.setup == self.reversal_setup and e.kind == TRIGGER:
                    return self._start_emerging(f, _move(e.direction), f"the reversal triggered: {e.note}",
                                                setup_of(e.setup))
            if new_extreme:
                ch = self._change(f, old_state, old_dir, old_type,
                                  f"the {old_dir} trend carried on: new {'low' if old_dir == DOWN else 'high'} "
                                  f"{self._p(f.l if old_dir == DOWN else f.h)}", [f"new extreme {self._p(f.l)}"])
                self._after_extreme(f, old_dir)
                return ch
            for e in bounce:
                if e.setup == self.reversal_setup and e.kind in (CANCELLED, EXPIRED):
                    return self._change(f, old_state, old_dir, old_type,
                                        f"the reversal setup was {e.kind}: back to the {old_dir} trend", [e.note])
            if self.n - self.last_news >= self.m.evidence_fades_after_candles:
                state, why = self.base(f)
                return self._change(f, state, NONE, None, f"the possible reversal faded with nothing new for "
                                    f"{self.m.evidence_fades_after_candles} candles; {why}", [why])
            return None

        # ---- emerging trend and trend ----------------------------------------------------
        if st in TRENDING:
            moved = self._pips(self.extreme, self.start_price) if self.extreme is not None else Decimal(0)
            if st == EMERGING:
                for e, stp in important_rejection(CONFIRMATION):
                    if _move(e.direction) == _opposite(d):
                        return self._start_emerging(f, _move(e.direction),
                                                    f"rejected at a level against the emerging {d} trend: {e.note}",
                                                    stp)
            for e in bounce:
                if e.kind == CONFIRMATION and _move(e.direction) == _opposite(d):
                    stp = setup_of(e.setup)
                    at = self._levels_of(stp)
                    if moved >= self.s.possible_reversal.min_trend_move_pips and at:
                        signs = self.reversal_signs(f, d, stp)
                        self.before = (st, d, self.now.trend_type)
                        self.reversal_setup = e.setup
                        return self._change(f, POSSIBLE_REVERSAL, _opposite(d), None,
                                            f"rejection at a level ({', '.join(at)}) confirmed after a {d} move of "
                                            f"{moved} pips: {e.note}", [e.note, *signs])
            for e, stp in important_rejection(CONFIRMATION):
                if _move(e.direction) == d:
                    self.last_news = self.n
                    self.now.evidence.append(f"{uk_short(f.candle.start)} level rejection with the trend: {e.note}")
            if new_extreme:
                ok, why = self.proof(f, d, True) if st == EMERGING else (False, "")
                self._after_extreme(f, d)
                if ok:
                    return self._change(f, TREND, d, STRONG_PUSH if self.push(f, d) else SLOW_GRIND,
                                        f"the rejection became a trend: {why}", [why])
            if st == EMERGING and self.origin is not None:
                ch = self._cancel_check(f, d)
                if ch is not None:
                    return ch
            if self.n - self.last_news >= self.m.evidence_fades_after_candles:
                state, why = self.base(f)
                return self._change(f, state, NONE, None,
                                    f"the {st} faded: no new {'low' if d == DOWN else 'high'} for "
                                    f"{self.m.evidence_fades_after_candles} candles; {why}", [why])
            if st == EMERGING:
                # besides its cancel rule, the proof, a replacing rejection or fading, an emerging trend
                # ends only in consolidation (owner's rule, 7 November 2026), held for persistence_candles
                c_ok, c_why = self.consolidation(f)
                return self._persist(f, (CONSOLIDATION, NONE, f"the emerging {d} trend settled into "
                                                              f"consolidation: {c_why}") if c_ok else None)
            # a trend's conditions (with persistence): price back past the 100 EMA, or ranging / consolidation
            wrong_side = f.ema100 is not None and ((d == DOWN and f.c > f.ema100) or (d == UP and f.c < f.ema100))
            r_ok, r_why = self.ranging(f)
            c_ok, c_why = self.consolidation(f)
            if wrong_side:
                target = (RANGING if r_ok else CONSOLIDATION, NONE,
                          f"price closed back {'above' if d == DOWN else 'below'} the 100 EMA "
                          f"{self._p(f.ema100)} for {self.m.persistence_candles} candles: the {d} {st} is over")
            elif c_ok:
                target = (CONSOLIDATION, NONE, f"the {d} {st} ran out of steam: {c_why}")
            elif r_ok:
                target = (RANGING, NONE, f"the {d} {st} turned into a range: {r_why}")
            else:
                target = None
            ch = self._persist(f, target)
            if ch is not None:
                return ch
            if st == TREND:
                return self._trend_type(f, d)
            return None

        # ---- consolidation and ranging ----------------------------------------------------
        for e, stp in important_rejection(CONFIRMATION):
            return self._start_emerging(f, _move(e.direction), f"rejected at a level: {e.note}", stp)
        if st == CONSOLIDATION and f.upper is not None:
            if f.c > f.upper:
                return self._start_emerging(f, UP, f"broke out of the consolidation: close {self._p(f.c)} above the "
                                                   f"upper band {self._p(f.upper)}", None)
            if f.c < f.lower:
                return self._start_emerging(f, DOWN, f"broke out of the consolidation: close {self._p(f.c)} below "
                                                     f"the lower band {self._p(f.lower)}", None)
        if st == RANGING and f.upper is not None:
            way = UP if f.c > f.upper else DOWN if f.c < f.lower else None
            run_dir, run = self.breakout_run
            self.breakout_run = (way, run + 1 if way is not None and way == run_dir else (1 if way else 0))
            if way is not None and self.breakout_run[1] >= self.m.persistence_candles:
                band = f.upper if way == UP else f.lower
                return self._start_emerging(f, way, f"broke out of the range: {self.breakout_run[1]} closes "
                                                    f"{'above' if way == UP else 'below'} the band "
                                                    f"(last {self._p(f.c)}, band {self._p(band)})", None)
        r_ok, r_why = self.ranging(f)
        c_ok, c_why = self.consolidation(f)
        target = None
        if st == CONSOLIDATION and r_ok:
            target = (RANGING, NONE, r_why)
        elif st == RANGING and c_ok:
            target = (CONSOLIDATION, NONE, c_why)
        return self._persist(f, target)

    # ---- helpers ------------------------------------------------------------------------------

    def _after_extreme(self, f: Features, d: str) -> None:
        self.extreme = f.l if d == DOWN else f.h
        self.failed_bounce = False
        self.last_news = self.n

    def _levels_of(self, setup: Any) -> list[str]:
        """The levels (not the bands) a rejection setup pierced."""
        return [f"{p['what']} {plain(p['price'])}" for p in setup.pierced
                if p["what"] not in ("upper Bollinger band", "lower Bollinger band")]

    def strong_levels(self, setup: Any) -> list[dict]:
        """The pierced levels that may START or REPLACE an emerging trend (owner's rule, 7 November
        2026): a type in market_states.strong_level_types (pivot, R1-R3, S1-S3, round numbers 00
        and 50, the previous day's high or low), or a turning level whose lined-up group holds one
        of those. A turning level on its own does not; it still counts everywhere else."""
        strong = set(self.m.strong_level_types)
        out = [p for p in setup.pierced if p["what"] in strong]
        for p in setup.pierced:
            if p["what"] in ("turning_high", "turning_low"):
                name = f"{p['what']} {plain(p['price'])}"
                for g in getattr(setup, "lined_up", []):
                    if name in g["levels"] and any(m.split(" ")[0] in strong for m in g["levels"]):
                        out.append(p)
                        break
        return out

    def _rejected_level(self, setup: Any, d: str) -> tuple[str, Decimal]:
        """The strong level a rejection was at: the one nearest the piercing candle's edge."""
        side = self.s.chart.price
        edge = getattr(setup.pierce, f"{side}_high" if d == DOWN else f"{side}_low")
        cands = self.strong_levels(setup) or \
                [p for p in setup.pierced if p["what"] not in ("upper Bollinger band", "lower Bollinger band")]
        best = min(cands, key=lambda p: abs(p["price"] - edge))
        return best["what"], best["price"]

    def _cancel_check(self, f: Features, d: str) -> StateChange | None:
        kind, what, level = self.origin
        if kind == "level":
            back = f.c > level if d == DOWN else f.c < level
            how = f"back {'above' if d == DOWN else 'below'} the {what} {self._p(level)} it was rejected at"
        else:
            back = f.lower is not None and f.lower < f.c < f.upper
            how = "back inside the Bollinger bands after the breakout"
        self.back_count = self.back_count + 1 if back else 0
        if self.back_count < self.m.persistence_candles:
            return None
        state, why = self.base(f)
        return self._change(f, state, NONE, None,
                            f"the emerging {d} trend was cancelled: {self.back_count} closes in a row {how} "
                            f"(last {self._p(f.c)})", [why])

    def _start_emerging(self, f: Features, d: str, reason: str, setup: Any) -> StateChange:
        self.start_price = f.c
        self.extreme = f.l if d == DOWN else f.h
        self.failed_bounce = False
        self.before = None
        self.reversal_setup = None
        self.breakout_run = (None, 0)
        self.back_count = 0
        ev = [reason, f"started at {self._p(f.c)}"]
        if setup is not None:
            what, level = self._rejected_level(setup, d)
            self.origin = ("level", what, level)
            ev.append(f"rejected at the {what} {self._p(level)}: cancelled only by {self.m.persistence_candles} "
                      f"closes in a row back {'above' if d == DOWN else 'below'} it")
        else:
            self.origin = ("breakout", None, None)
            ev.append(f"a breakout: cancelled only by {self.m.persistence_candles} closes in a row back inside "
                      "the Bollinger bands")
        return self._change(f, EMERGING, d, None, reason, ev)

    def _persist(self, f: Features, target: tuple[str, str, str] | None) -> StateChange | None:
        if target is None:
            self._pending, self._pending_count = None, 0
            return None
        if self._pending is not None and self._pending[:2] == target[:2]:
            self._pending_count += 1
        else:
            self._pending, self._pending_count = target, 1
        if self._pending_count >= self.m.persistence_candles:
            state, direction, why = target
            return self._change(f, state, direction, None, why, [why])
        return None

    def _trend_type(self, f: Features, d: str) -> StateChange | None:
        want = STRONG_PUSH if self.push(f, d) else SLOW_GRIND
        if want == self.now.trend_type:
            self._type_pending, self._type_count = None, 0
            return None
        self._type_count = self._type_count + 1 if self._type_pending == want else 1
        self._type_pending = want
        if self._type_count < self.m.persistence_candles:
            return None
        why = (f"{'strong push' if want == STRONG_PUSH else 'slow grind'}: "
               f"{int((f.red_share if d == DOWN else f.green_share) * 100)}% of the body size "
               f"{'red' if d == DOWN else 'green'}, bands {self._p(f.widening)}x as wide as {self.m.band_widening_candles} candles ago, "
               f"7/21 EMAs {self._p(f.fan)} pips apart, {f.closes_on_lower if d == DOWN else f.closes_on_upper} "
               f"closes on the band")
        news = self.last_news             # a change of type is not new evidence of the trend
        ch = self._change(f, TREND, d, want, why, [why])
        self.last_news = news
        return ch
