"""The planner's measurements (Structural Trade Planner V1, observe only; owner's approval of 17 November 2026).
Everything is worked out from candles that had FINISHED by the time asked about, on the chart (sell) price, with
the bot's own indicator code (prices/indicators.py) and your chart settings ([indicators]: EMA 7/13/21/100/200,
Bollinger 20/2, MACD 35/45/30, RSI 3 with 70/30). No other indicator is worked out. Reads the candle store only;
never contacts IG.

  * 4-hour candles are rebuilt from the finished hourly candles on the store's own boundaries (prices/calendar.py
    Boundaries: every 4 hours from 00:00 UK). One is used only when every hour the market was open in it is there
    and it has finished (D-31; P-A6). Checked: identical to the store's own 4-hour candles.
  * Indicators on H1, H4, daily and weekly: each one only once it has had the candles the bot's warm-up rule needs
    ([indicators] warm_up_seed_weight_percent); until then it is None and listed as warming up (D-27). Never guessed.
  * The average daily range (ADR): the average high-to-low range of the last planner.adr_weekdays finished daily
    candles, leaving out IG's short Sunday candles (D-30; P-A8). None until there are that many.
  * Weekly pivots: the classic formulas (levels/rules.py daily_pivots) on the last finished weekly candle (D-35).
  * Data freshness: the analyser's own out-of-date rule (analyser/data_status.py, P-A3) on the 5-minute and hourly
    candles.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from typing import Any, Sequence

from analyser.data_status import READY, judge
from analyser.indicators import last_candles
from prices.calendar import Boundaries, MarketHours
from prices.indicators import bollinger, ema, macd, needs_ema, needs_macd, needs_rsi, rsi
from prices.model import UK, Candle, build_from

UTC = timezone.utc


def side_of(settings: Any) -> str:
    return settings.chart.price


def ppp(settings: Any) -> Decimal:
    """Points per pip."""
    return Decimal(settings.market.points_per_pip)


def pips(settings: Any, points: Decimal) -> Decimal:
    return (Decimal(points) / ppp(settings)).quantize(Decimal("0.1"))


def hi(c: Candle, side: str) -> Decimal:
    return getattr(c, f"{side}_high")


def lo(c: Candle, side: str) -> Decimal:
    return getattr(c, f"{side}_low")


def cl(c: Candle, side: str) -> Decimal:
    return getattr(c, f"{side}_close")


def op(c: Candle, side: str) -> Decimal:
    return getattr(c, f"{side}_open")


# ---- 4-hour candles from hourly candles --------------------------------------------------------------------

def four_hour_from_hourly(settings: Any, hourly: Sequence[Candle], as_of: datetime) -> list[Candle]:
    """The 4-hour candles made from the given finished hourly candles: each on the store's own 4-hour boundary,
    used only when it has finished by `as_of` and holds every hour the market was open in it."""
    hours = MarketHours(settings.market_hours)
    b = Boundaries(settings.candles, hours)
    buckets: dict[tuple[datetime, datetime], list[Candle]] = {}
    for c in sorted(hourly, key=lambda x: x.start):
        if c.end <= as_of:
            buckets.setdefault(b.bucket("4h", c.start), []).append(c)
    out = []
    for (s, e), parts in sorted(buckets.items()):
        if e > as_of:
            continue
        expected = {slot.replace(minute=0) for slot in hours.open_slots(s, e)}
        if {p.start for p in parts} != expected:
            continue                                    # an hour is missing: not used (P-A6)
        out.append(build_from("4h", s, e, parts, len(expected)))
    return out


# ---- indicators on one timeframe ---------------------------------------------------------------------------------

@dataclass
class Frame:
    """One timeframe's finished candles and their indicators (each None until warmed up)."""
    timeframe: str
    candles: list[Candle]
    ema: dict[int, dict[datetime, Decimal]] = field(default_factory=dict)       # only the warmed-up ones
    band: dict = field(default_factory=dict)
    macd: dict = field(default_factory=dict)
    rsi: dict = field(default_factory=dict)
    warming: list[str] = field(default_factory=list)                            # e.g. "EMA200 (448 of 592)"

    @property
    def last(self) -> Candle | None:
        return self.candles[-1] if self.candles else None

    def ema_now(self, p: int) -> Decimal | None:
        s = self.ema.get(p)
        return s.get(self.last.start) if s and self.last else None

    def ready(self, name: str) -> bool:
        return not any(w.startswith(name + " ") for w in self.warming)


def frame(settings: Any, timeframe: str, candles: Sequence[Candle]) -> Frame:
    ind, side = settings.indicators, side_of(settings)
    pct = ind.warm_up_seed_weight_percent
    cs = sorted(candles, key=lambda c: c.start)
    n = len(cs)
    f = Frame(timeframe, cs)
    for p in ind.ema_periods:
        need = needs_ema(p, pct)
        if n >= need:
            f.ema[p] = ema(cs, side, p)
        else:
            f.warming.append(f"EMA{p} ({n} of {need} candles)")
    if n >= ind.bollinger_periods:
        f.band = bollinger(cs, side, ind.bollinger_periods, ind.bollinger_std_devs)
    else:
        f.warming.append(f"Bollinger ({n} of {ind.bollinger_periods} candles)")
    need = needs_macd(ind.macd_fast_periods, ind.macd_slow_periods, ind.macd_signal_periods, pct)
    if n >= need:
        f.macd = macd(cs, side, ind.macd_fast_periods, ind.macd_slow_periods, ind.macd_signal_periods)
    else:
        f.warming.append(f"MACD ({n} of {need} candles)")
    need = needs_rsi(ind.rsi_periods, pct)
    if n >= need:
        f.rsi = rsi(cs, side, ind.rsi_periods)
    else:
        f.warming.append(f"RSI ({n} of {need} candles)")
    return f


# ---- the average daily range ------------------------------------------------------------------------------------

def is_sunday_candle(c: Candle) -> bool:
    return c.start.astimezone(UK).weekday() == 6


def adr(settings: Any, daily: Sequence[Candle]) -> Decimal | None:
    """The ADR in points: the average sell high-to-low range of the last planner.adr_weekdays finished weekday
    daily candles (IG's short Sunday candles left out). None when there are fewer than that."""
    n = settings.planner.adr_weekdays
    side = side_of(settings)
    days = [c for c in sorted(daily, key=lambda c: c.start) if not is_sunday_candle(c)][-n:]
    if len(days) < n:
        return None
    return sum((hi(c, side) - lo(c, side) for c in days), Decimal(0)) / Decimal(n)


def today_range(settings: Any, fives: Sequence[Candle], day_start: datetime) -> tuple[Decimal, Decimal] | None:
    """Today's (UK day) sell high and low so far from the finished 5-minute candles."""
    side = side_of(settings)
    today = [c for c in fives if c.start >= day_start]
    if not today:
        return None
    return max(hi(c, side) for c in today), min(lo(c, side) for c in today)


# ---- freshness -----------------------------------------------------------------------------------------------------

def freshness(settings: Any, five: Candle | None, hour: Candle | None, as_of: datetime) -> tuple[bool, list[str]]:
    """(fresh, reasons): the analyser's own out-of-date rule ([analyser] out_of_date_after_minutes) on the newest
    finished 5-minute and hourly candles."""
    frames = [SimpleNamespace(timeframe=tf, candle=c, warming_up=lambda: [], needs={}, candles_used=0)
              for tf, c in (("5m", five), ("1h", hour))]
    st = judge(settings, frames, as_of)
    return st.state == READY, list(st.reasons)


# ---- everything the planner reads at one moment --------------------------------------------------------------------

@dataclass
class Snapshot:
    as_of: datetime
    fives: list[Candle]                 # the last day or so of finished 5-minute candles
    h1: Frame
    h4: Frame
    d1: Frame
    w1: Frame
    adr: Decimal | None
    day_start: datetime                 # start of today's UK daily candle
    price: Decimal | None               # the latest finished 5-minute close (sell)
    fresh: bool
    stale_reasons: list[str]

    @property
    def five(self) -> Candle | None:
        return self.fives[-1] if self.fives else None


def snapshot(settings: Any, store: Any, as_of: datetime) -> Snapshot:
    """Read the finished candles at `as_of` and work out every measurement."""
    as_of = as_of.astimezone(UTC)
    count = settings.indicators.history_candles
    hourly = last_candles(store, "1h", as_of, count)
    fives = [c for c in store.read_range("5m", as_of - timedelta(days=4), as_of) if c.end <= as_of]
    daily = last_candles(store, "1d", as_of, count)
    weekly = last_candles(store, "1w", as_of, count)
    four = four_hour_from_hourly(settings, hourly, as_of)
    b = Boundaries(settings.candles, MarketHours(settings.market_hours))
    day_start, _ = b.regular("1d", as_of)
    fresh, why = freshness(settings, fives[-1] if fives else None, hourly[-1] if hourly else None, as_of)
    side = side_of(settings)
    return Snapshot(as_of, fives, frame(settings, "1h", hourly), frame(settings, "4h", four),
                    frame(settings, "1d", daily), frame(settings, "1w", weekly), adr(settings, daily), day_start,
                    cl(fives[-1], side) if fives else None, fresh, why)
