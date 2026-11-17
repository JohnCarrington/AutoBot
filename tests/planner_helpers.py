"""Shared helpers for the Structural Trade Planner tests: an in-memory candle store, made-up markets built from a
price path, and settings with the planner's folder moved to a test folder. Never touches the real store or IG.

Prices are the chart (SELL) prices in points (GBPUSD: 1 point = 1 pip). A made-up market is a list of waypoints
(trading hour, price); 5-minute candles follow the straight lines between them, during market hours only, with a
small fixed wobble so candles have highs and lows; 1-hour, 4-hour, daily and weekly candles are built from them on
the bot's own boundaries (prices/calendar.py), exactly as the price service builds them.
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from prices.calendar import Boundaries, MarketHours
from prices.model import Candle, build_from

UTC = timezone.utc
SPREAD = D("1.2")


class FakeStore:
    """The parts of prices/store.py CandleStore the planner and the levels part read, from memory."""

    def __init__(self, candles: dict[str, list[Candle]], folder: str = "/nowhere/GBPUSD"):
        self.folder = Path(folder)
        self.by_tf = {tf: sorted(cs, key=lambda c: c.start) for tf, cs in candles.items()}

    def days(self, tf: str) -> list[date]:
        return sorted({c.start.date() for c in self.by_tf.get(tf, [])})

    def read_day(self, tf: str, day: date) -> list[Candle]:
        return [c for c in self.by_tf.get(tf, []) if c.start.date() == day]

    def read_range(self, tf: str, start: datetime, end: datetime) -> list[Candle]:
        return [c for c in self.by_tf.get(tf, []) if start <= c.start < end]

    def get(self, tf: str, start: datetime) -> Candle | None:
        return next((c for c in self.by_tf.get(tf, []) if c.start == start), None)

    def newest(self, tf: str) -> Candle | None:
        cs = self.by_tf.get(tf, [])
        return cs[-1] if cs else None

    def until(self, t: datetime) -> "FakeStore":
        """Only the candles that had finished by t (as a store would have held then)."""
        return FakeStore({tf: [c for c in cs if c.end <= t] for tf, cs in self.by_tf.items()}, str(self.folder))


def five_minute_path(settings: Any, start: datetime, waypoints: list[tuple[float, float]], wobble: float = 1.0) -> list[Candle]:
    """5-minute candles from `start` along straight lines between waypoints (trading hour, price), market hours only."""
    hours = MarketHours(settings.market_hours)
    total_h = waypoints[-1][0]
    slots = []
    t = start
    for s in hours.open_slots(start, start + timedelta(days=int(total_h / 24 * 7 / 5) + 30)):
        slots.append(s)
        if len(slots) >= int(total_h * 12):
            break

    def path(k: float) -> float:
        h = k / 12
        for (h0, p0), (h1, p1) in zip(waypoints, waypoints[1:]):
            if h0 <= h <= h1:
                return p0 + (p1 - p0) * (h - h0) / (h1 - h0)
        return waypoints[-1][1]

    out = []
    prev = path(0)
    for k, s in enumerate(slots):
        close = path(k + 1) + wobble * math.sin(k * 0.9)
        o = prev
        hi = max(o, close) + 0.6 + 0.4 * abs(math.sin(k * 1.7))
        lo = min(o, close) - 0.6 - 0.4 * abs(math.cos(k * 1.3))
        q = lambda x: D(str(round(x, 1)))                # noqa: E731
        so, sh, sl, sc = q(o), q(hi), q(lo), q(close)
        out.append(Candle("5m", s, s + timedelta(minutes=5), so + SPREAD, sh + SPREAD, sl + SPREAD, sc + SPREAD,
                          so, sh, sl, sc))
        prev = float(sc)
    return out


def build_all(settings: Any, fives: list[Candle]) -> dict[str, list[Candle]]:
    """1h, 4h, 1d and 1w candles built from the 5-minute candles on the bot's own boundaries."""
    b = Boundaries(settings.candles, MarketHours(settings.market_hours))
    out: dict[str, list[Candle]] = {"5m": list(fives)}
    for tf in ("1h", "4h", "1d", "1w"):
        buckets: dict = {}
        for c in fives:
            buckets.setdefault(b.bucket(tf, c.start), []).append(c)
        out[tf] = [build_from(tf, s, e, parts, b.expected_parts(s, e)) for (s, e), parts in sorted(buckets.items())]
    return out


def market(settings: Any, start: datetime, waypoints: list[tuple[float, float]], wobble: float = 1.0) -> FakeStore:
    return FakeStore(build_all(settings, five_minute_path(settings, start, waypoints, wobble)))


def mirrored(store: FakeStore, centre: D = D(13500)) -> FakeStore:
    """The same market upside down (price -> 2 x centre - price; highs and lows swapped): a bearish market becomes
    the mirror-image bullish one."""
    def flip(c: Candle) -> Candle:
        f = lambda x: 2 * centre - x                    # noqa: E731
        return Candle(c.timeframe, c.start, c.end, f(c.buy_open), f(c.buy_low), f(c.buy_high), f(c.buy_close),
                      f(c.sell_open), f(c.sell_low), f(c.sell_high), f(c.sell_close), c.parts, c.expected_parts)
    return FakeStore({tf: [flip(c) for c in cs] for tf, cs in store.by_tf.items()}, str(store.folder))


class Over:
    """Settings with some sections replaced (settings themselves cannot be changed)."""

    def __init__(self, base: Any, **sections: Any):
        object.__setattr__(self, "_b", base)
        object.__setattr__(self, "_kw", sections)

    def __getattr__(self, n: str) -> Any:
        return self._kw[n] if n in self._kw else getattr(self._b, n)


def section(base_section: Any, **changes: Any) -> SimpleNamespace:
    d = {k: v for k, v in vars(base_section).items() if not k.startswith("_")}
    d.update(changes)
    return SimpleNamespace(**d)


def with_folder(settings: Any, folder: Path, **planner_changes: Any) -> Over:
    return Over(settings, planner=section(settings.planner, folder=folder, **planner_changes))
