"""The shared rejection part (docs/DESIGN.md 3.3, 3.4 and 4; rules in plain
English in docs/REJECTION.md). One watcher, used by the analyser, the
strategies and the trade manager, so all three read the same answer.

It never places, changes or closes a trade, and never contacts IG. Every
price is the chart price (settings [chart] price: SELL, as on the owner's
chart). Every number comes from the settings.

Two versions, each in both directions (written here for a SELL; a BUY is the
mirror image: pierce downwards, green candles, lows and highs swapped):

  bounce  1. a candle pierces a level or the upper Bollinger band. For a level,
             coming within rejection.near_level_within_pips of it counts the
             same as a pierce; the band needs a real pierce.
          2. reversal: the first red candle after the pierce, within
             bounce.reversal_candle_within_candles_of_pierce candles (else expired)
          3. confirmation: a later candle CLOSES below the reversal candle's low,
             within bounce.confirmation_candle_within_candles_of_reversal candles
             of it (else expired). A wick below does not count.
          4. trigger: the live price goes below the confirmation candle's low
          5. cancelled if price goes above the reversal candle's high at any
             point after the reversal candle
  range   1. a candle pierces the upper Bollinger band
          2. the next candle (range_trade.rejection_candle_within_candles) is red:
             the rejection candle (else expired)
          3. trigger: during the candle after that (range_trade.trigger_within_candles),
             the live price goes below the rejection candle's low (else expired)
          4. cancelled if price goes above the rejection candle's high first

When IG's spread on a candle is abnormally wide (over rejection.max_spread_pips:
the 22:00 rollover, news), that candle's highs and lows cannot start a setup
(a pierce, first or again) or cancel one. An "ignored" event records it.

Each step is a separate, timestamped Event. Nothing is filtered on the size
of the reversal candle or on which levels lined up: both are only recorded.
The reversal watch window, and whether the pierced levels line up, decide only
the `counts` mark on a setup (docs/REJECTION.md).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any, Iterable

from levels.rules import to_decimals
from prices.indicators import Band
from prices.model import UK, Candle, plain, uk_short

UTC = timezone.utc
BOUNCE, RANGE = "bounce", "range"
SELL, BUY = "sell", "buy"

PIERCE, REVERSAL, CONFIRMATION, TRIGGER, CANCELLED, EXPIRED, IGNORED = (
    "pierce", "reversal", "confirmation", "trigger", "cancelled", "expired", "ignored")


# ---- the reversal watch windows ---------------------------------------------------

def watch_windows(settings: Any, day: date) -> list[tuple[datetime, datetime]]:
    """The reversal watch windows on one UK day, as UTC (start, end), both ends
    included: each reversal_watch time, from minutes_before to minutes_after."""
    rw = settings.reversal_watch
    out = []
    for t in rw.times:
        at = datetime.combine(day, t, tzinfo=UK).astimezone(UTC)
        out.append((at - timedelta(minutes=rw.minutes_before), at + timedelta(minutes=rw.minutes_after)))
    return out


def in_watch_window(settings: Any, t: datetime) -> bool:
    day = t.astimezone(UK).date()
    return any(a <= t <= b for a, b in watch_windows(settings, day))


# ---- what the watcher reports --------------------------------------------------------

@dataclass(frozen=True)
class Event:
    setup: int
    version: str          # bounce or range
    direction: str        # sell (rejected from above) or buy (rejected from below)
    kind: str             # pierce, reversal, confirmation, trigger, cancelled, expired
    time: datetime        # the candle's start (UTC); for a live trigger or cancel, the tick time
    price: Decimal | None
    note: str
    from_live_price: bool = False

    def describe(self) -> str:
        p = f" {plain(self.price)}" if self.price is not None else ""
        live = " (live price)" if self.from_live_price else ""
        return f"{uk_short(self.time)}  #{self.setup} {self.version} {self.direction} {self.kind}{p}{live}: {self.note}"


@dataclass
class Setup:
    id: int
    version: str
    direction: str
    pierce: Candle
    pierced: list[dict]                 # what was pierced: {"what": "band" | level type, "price": ...}
    lined_up: list[dict] = field(default_factory=list)   # the groups of the pierced levels
    in_watch_window: bool = False
    counts: bool = True                 # see docs/REJECTION.md
    stage: str = "reversal"             # reversal, confirmation, trigger, done
    waited: int = 0                     # candles waited at this stage
    reversal: Candle | None = None
    confirmation: Candle | None = None
    trigger_price: Decimal | None = None
    status: str = "running"             # running, triggered, cancelled, expired
    size: dict = field(default_factory=dict)   # reversal candle size compared with the piercing candle


def _red(c: Candle, side: str) -> bool:
    return getattr(c, f"{side}_close") < getattr(c, f"{side}_open")


def _green(c: Candle, side: str) -> bool:
    return getattr(c, f"{side}_close") > getattr(c, f"{side}_open")


class RejectionWatcher:
    """Feed it each finished candle in order with on_candle(), and, when live,
    each price with on_price(). It returns the new events each time."""

    def __init__(self, settings: Any, design_only: bool = False):
        """design_only=True: the strategies' own watcher, with only the rules written
        in design 3.3 and 3.4 (owner, 7 November 2026): every pierce starts its own
        setup (no limit per version and direction), a pierce while a setup waits for
        its reversal candle does not start that setup's count again, and a level is
        reached when the candle touches it or comes within near_level_within_pips
        of it (no rule about the side the candle opened on). The analyser's watcher
        (False) keeps the rules described in docs/REJECTION.md."""
        self.s = settings
        self.side = settings.chart.price
        self.design_only = design_only
        self.events: list[Event] = []
        self.setups: list[Setup] = []
        self._active: dict[int, Setup] = {}

    # -- helpers on the chart price
    def _o(self, c): return getattr(c, f"{self.side}_open")
    def _h(self, c): return getattr(c, f"{self.side}_high")
    def _l(self, c): return getattr(c, f"{self.side}_low")
    def _c(self, c): return getattr(c, f"{self.side}_close")

    def spread(self, c: Candle) -> Decimal:
        """The candle's spread: the widest of its four buy-minus-sell gaps (open, high, low, close)."""
        return max(c.buy_open - c.sell_open, c.buy_high - c.sell_high,
                   c.buy_low - c.sell_low, c.buy_close - c.sell_close)

    def max_spread(self) -> Decimal:
        return Decimal(self.s.rejection.max_spread_pips) * Decimal(self.s.market.points_per_pip)

    def spike(self, c: Candle) -> bool:
        """IG's spread on this candle is abnormally wide (rollover, news): its chart-price
        highs and lows must not start a setup or cancel one."""
        return self.spread(c) > self.max_spread()

    def _ignored(self, st_id: int, version: str, direction: str, c: Candle, what: str) -> None:
        self.events.append(Event(st_id, version, direction, IGNORED, c.start, None,
                                 f"{what} ignored: IG's spread on this candle was {plain(self.spread(c))} points, "
                                 f"over the limit of {plain(self.max_spread())}"))

    def _emit(self, st: Setup, kind: str, t: datetime, price, note: str, live=False) -> Event:
        ev = Event(st.id, st.version, st.direction, kind, t, price, note, live)
        self.events.append(ev)
        return ev

    def _end(self, st: Setup, status: str) -> None:
        st.status, st.stage = status, "done"
        self._active.pop(st.id, None)

    # ---- one finished candle ----------------------------------------------------------

    def on_candle(self, c: Candle, band: Band | None, levels: Any = None) -> list[Event]:
        """`band`: the Bollinger band at this candle (None before there are enough
        candles). `levels`: the levels.current.LevelList as it stood at this
        candle's start (None: no levels)."""
        before = len(self.events)
        for st in list(self._active.values()):
            self._advance(st, c, band, levels)
        for version in (BOUNCE, RANGE):
            for direction in (SELL, BUY):
                if not self.design_only and any(st.version == version and st.direction == direction
                                                for st in self._active.values()):
                    continue
                pierced = self._pierced(version, direction, c, band, levels)
                if pierced and self.spike(c):
                    self._ignored(0, version, direction, c, "a new pierce")
                elif pierced:
                    self._start(version, direction, c, pierced, levels)
        return self.events[before:]

    def _pierced(self, version, direction, c, band, levels) -> list[dict]:
        out = []
        if band is not None:
            if direction == SELL and self._h(c) > band.upper:
                out.append({"what": "upper Bollinger band", "price": band.upper, "level": None})
            if direction == BUY and self._l(c) < band.lower:
                out.append({"what": "lower Bollinger band", "price": band.lower, "level": None})
        if version == BOUNCE and levels is not None:
            near = Decimal(self.s.rejection.near_level_within_pips) * Decimal(self.s.market.points_per_pip)
            for lv in levels.levels:
                # A level counts when the candle comes up to it from at or below it (sell) and
                # either goes through it or gets within `near` of it; a buy is the mirror image.
                from_side = self.design_only or (self._o(c) <= lv.price if direction == SELL else self._o(c) >= lv.price)
                if direction == SELL and from_side and self._h(c) >= lv.price - near and self._l(c) <= lv.price:
                    gap = lv.price - self._h(c)
                    out.append({"what": lv.type, "price": lv.price, "level": lv,
                                "how": _how(gap)})
                if direction == BUY and from_side and self._l(c) <= lv.price + near and self._h(c) >= lv.price:
                    gap = self._l(c) - lv.price
                    out.append({"what": lv.type, "price": lv.price, "level": lv,
                                "how": _how(gap)})
        return out

    def _start(self, version, direction, c, pierced, levels) -> None:
        st = Setup(len(self.setups) + 1, version, direction, c, [])
        self.setups.append(st)
        self._active[st.id] = st
        self._set_pierce(st, c, pierced, levels, first=True)

    def _set_pierce(self, st: Setup, c: Candle, pierced, levels, first: bool) -> None:
        st.pierce, st.waited = c, 0
        d = self.s.levels.level_decimals          # band prices are shown like levels (exact ones are compared)
        shown = [{"what": p["what"], "price": to_decimals(p["price"], d) if p["level"] is None else p["price"],
                  "level": p["level"], "how": p.get("how", "through")} for p in pierced]
        st.pierced = [{"what": p["what"], "price": p["price"], "how": p["how"]} for p in shown]
        groups = {}
        for p in pierced:
            lv = p["level"]
            if lv is not None and levels is not None:
                g = levels.group_of(lv)
                groups[g["group"]] = {"group": g["group"], "lined_up": g["lined_up"],
                                      "levels": [f"{m.type} {plain(m.price)}" for m in g["members"]]}
        st.lined_up = list(groups.values())
        st.in_watch_window = in_watch_window(self.s, c.start)
        has_band = any(p["level"] is None for p in pierced)
        st.counts = has_band or st.in_watch_window or any(g["lined_up"] for g in st.lined_up)
        edge = self._h(c) if st.direction == SELL else self._l(c)
        what = ", ".join(f"{p['what']} {plain(p['price'])}" + ("" if p["how"] == "through" else f" ({p['how']})")
                         for p in shown)
        window = "in a reversal watch window" if st.in_watch_window else "outside the watch windows"
        lined = "; levels line up" if any(g["lined_up"] for g in st.lined_up) else ""
        again = "" if first else " (pierced again: the reversal count starts again)"
        self._emit(st, PIERCE, c.start, edge,
                   f"{'high' if st.direction == SELL else 'low'} {plain(edge)} reached {what}; {window}{lined}; "
                   f"{'counts' if st.counts else 'does not count (outside the windows, no levels line up)'}{again}")

    def _sizes(self, st: Setup) -> None:
        p, r = st.pierce, st.reversal
        pb, rb = abs(self._c(p) - self._o(p)), abs(self._c(r) - self._o(r))
        pr, rr = self._h(p) - self._l(p), self._h(r) - self._l(r)
        st.size = {"piercing_body": pb, "reversal_body": rb, "piercing_range": pr, "reversal_range": rr,
                   "body_ratio": (rb / pb) if pb else None, "range_ratio": (rr / pr) if pr else None}

    # ---- moving a setup on by one candle ---------------------------------------------------

    def _advance(self, st: Setup, c: Candle, band, levels) -> None:
        sell = st.direction == SELL
        turn = _red if sell else _green
        if st.stage == "reversal":
            limit = (self.s.bounce.reversal_candle_within_candles_of_pierce if st.version == BOUNCE
                     else self.s.range_trade.rejection_candle_within_candles)
            if turn(c, self.side):
                st.reversal, st.stage, st.waited = c, ("confirmation" if st.version == BOUNCE else "trigger"), 0
                self._sizes(st)
                name = "reversal candle" if st.version == BOUNCE else "rejection candle"
                self._emit(st, REVERSAL, c.start, self._c(c),
                           f"{name} O {plain(self._o(c))} H {plain(self._h(c))} L {plain(self._l(c))} "
                           f"C {plain(self._c(c))}; size against the piercing candle: body "
                           f"{_ratio(st.size['body_ratio'])}, high-low {_ratio(st.size['range_ratio'])}")
                return
            again = [] if self.design_only else self._pierced(st.version, st.direction, c, band, levels)
            if st.version == BOUNCE and again and self.spike(c):
                self._ignored(st.id, st.version, st.direction, c, "a pierce again")
                again = []
            if st.version == BOUNCE and again:
                self._set_pierce(st, c, again, levels, first=False)
                return
            st.waited += 1
            if st.waited >= limit:
                self._emit(st, EXPIRED, c.start, None,
                           f"no {'red' if sell else 'green'} candle within {limit} candle(s) of the pierce")
                self._end(st, "expired")
            return

        r = st.reversal
        beyond_reversal = self._h(c) > self._h(r) if sell else self._l(c) < self._l(r)
        if beyond_reversal and self.spike(c):
            self._ignored(st.id, st.version, st.direction, c, "a cancel")
            beyond_reversal = False
        if st.stage == "confirmation":
            if beyond_reversal:
                self._cancel(st, c)
                return
            if (self._c(c) < self._l(r)) if sell else (self._c(c) > self._h(r)):
                st.confirmation, st.stage, st.waited = c, "trigger", 0
                st.trigger_price = self._l(c) if sell else self._h(c)
                self._emit(st, CONFIRMATION, c.start, self._c(c),
                           f"closed {plain(self._c(c))} {'below the reversal low' if sell else 'above the reversal high'} "
                           f"{plain(self._l(r) if sell else self._h(r))}; trigger at "
                           f"{'below' if sell else 'above'} {plain(st.trigger_price)}")
                return
            st.waited += 1
            limit = self.s.bounce.confirmation_candle_within_candles_of_reversal
            if st.waited >= limit:
                self._emit(st, EXPIRED, c.start, None,
                           f"no close {'below the reversal low' if sell else 'above the reversal high'} within "
                           f"{limit} candle(s) of the reversal candle")
                self._end(st, "expired")
            return

        if st.stage == "trigger":
            if st.version == RANGE and st.trigger_price is None:
                st.trigger_price = self._l(r) if sell else self._h(r)
            through = self._l(c) < st.trigger_price if sell else self._h(c) > st.trigger_price
            if through and beyond_reversal:
                # Both in one candle: from candles alone the order is unknown.
                o = self._o(c)
                first_through = (o < st.trigger_price) if sell else (o > st.trigger_price)
                if first_through:
                    self._trigger(st, c.start, st.trigger_price, "the candle opened past the trigger price", False)
                else:
                    self._cancel(st, c, "this candle went both ways; from candles alone the order is unknown, "
                                        "so it is treated as cancelled")
                return
            if beyond_reversal:
                self._cancel(st, c)
                return
            if through:
                self._trigger(st, c.start, st.trigger_price, "during this candle", False)
                return
            if st.version == RANGE:
                st.waited += 1
                if st.waited >= self.s.range_trade.trigger_within_candles:
                    self._emit(st, EXPIRED, c.start, None,
                               f"price did not go {'below' if sell else 'above'} {plain(st.trigger_price)} during "
                               f"the candle after the rejection candle")
                    self._end(st, "expired")

    def _cancel(self, st: Setup, c: Candle, why: str = "") -> None:
        r = st.reversal
        edge = self._h(r) if st.direction == SELL else self._l(r)
        self._emit(st, CANCELLED, c.start, edge,
                   f"price went {'above' if st.direction == SELL else 'below'} the "
                   f"{'reversal' if st.version == BOUNCE else 'rejection'} candle's "
                   f"{'high' if st.direction == SELL else 'low'} {plain(edge)}" + (f" ({why})" if why else ""))
        self._end(st, "cancelled")

    def _trigger(self, st: Setup, t: datetime, price: Decimal, how: str, live: bool) -> None:
        self._emit(st, TRIGGER, t, price,
                   f"price went {'below' if st.direction == SELL else 'above'} {plain(price)} ({how})", live)
        self._end(st, "triggered")

    # ---- a live price (between candle closes) -----------------------------------------------

    def on_price(self, t: datetime, price: Decimal, spread: Decimal | None = None) -> list[Event]:
        """A live chart price (sell). Triggers or cancels a waiting setup at the
        exact moment. Candle steps (pierce, reversal, confirmation, expiry) only
        happen at a candle's close, in on_candle(). `spread` is IG's buy-minus-sell
        at that moment: when it is over rejection.max_spread_pips, the price
        cannot cancel a setup."""
        wide = spread is not None and spread > self.max_spread()
        before = len(self.events)
        for st in list(self._active.values()):
            if st.stage not in ("confirmation", "trigger"):
                continue
            sell, r = st.direction == SELL, st.reversal
            if ((price > self._h(r)) if sell else (price < self._l(r))) and not wide:
                edge = self._h(r) if sell else self._l(r)
                self._emit(st, CANCELLED, t, price,
                           f"price {plain(price)} went {'above' if sell else 'below'} the "
                           f"{'reversal' if st.version == BOUNCE else 'rejection'} candle's "
                           f"{'high' if sell else 'low'} {plain(edge)}", live=True)
                self._end(st, "cancelled")
                continue
            if st.stage == "trigger":
                tp = st.trigger_price if st.trigger_price is not None else (self._l(r) if sell else self._h(r))
                st.trigger_price = tp
                if (price < tp) if sell else (price > tp):
                    self._trigger(st, t, price, f"live price {plain(price)}", True)
        return self.events[before:]


def _how(gap: Decimal) -> str:
    """How close a candle came to a level: through it, exactly to it, or within some pips."""
    if gap < 0:
        return "through"
    return "touched" if gap == 0 else f"within {plain(gap)} pips"


def _ratio(x: Decimal | None) -> str:
    return "n/a (piercing candle had none)" if x is None else f"{x.quantize(Decimal('0.01'))}x"
