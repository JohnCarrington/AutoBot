"""EMA pullback (design 3.2), written for a buy; a sell is the mirror image.
Sell (bid) price for every indicator. Ideas only.

  0. The trend must be established on the hourly chart: on the last finished
     hourly candle, the hourly 8, 13 and 20 EMAs in order (8 > 13 > 20) and all
     rising since the hourly candle before; each one's slope over the last
     ema_pullback.hourly_slope_candles (3) hourly candles at least
     hourly_min_slope_pips_per_hour (0.16 pips an hour); the 8 and 13 at least
     hourly_min_gap_fast_mid_pips (0.25) apart and the 13 and 20 at least
     hourly_min_gap_mid_slow_pips (0.20) apart. (AutoBot 161's service.)
  1. While a 5-minute candle is forming, the live price drops to the 5-minute
     8 EMA (it may cross the 8 and even the 13 EMA). The live 8 EMA moves with
     the price, and price is at or below it exactly when price is at or below
     the 8 EMA of the last finished candle; so with stored candles: a candle
     whose low reaches the last finished candle's 8 EMA.
  2. A 5-minute candle closing below the 21 EMA cancels the setup (the touch
     candle included).
  3. The entry price is entry_beyond_pips (3) above the highest high of the
     entry_lookback_candles (5) finished 5-minute candles before the pullback.
  4. The buy idea comes as soon as price reaches the entry price.
  5. Not reached within setup_expires_after_minutes (20) of the touch: expired.
With stored candles the entry is looked for from the candle after the touch
(inside the touch candle the order is unknown, and the entry is above the last
five highs), in candles starting less than 20 minutes after the touch candle
started; a candle that opened past the entry fills at its open.
One setup at a time in each direction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Sequence

from prices.indicators import ema
from prices.model import Candle, plain, uk_short
from strategies.common import BUY, EMA_PULLBACK, SELL, Candidate


@dataclass
class HourlyTrend:
    direction: str | None               # buy, sell or None
    qualified: bool
    why: str


class HourlyTrendReader:
    """Step 0 from the stored hourly candles: the trend as of the last hourly candle finished by a time."""

    def __init__(self, settings: Any, hourly: Sequence[Candle]):
        e = settings.ema_pullback
        self.s, self.e = settings, e
        side = settings.chart.price
        self.ppp = Decimal(settings.market.points_per_pip)
        self.candles = list(hourly)
        self.f = ema(self.candles, side, e.hourly_fast_ema_periods)
        self.m = ema(self.candles, side, e.hourly_mid_ema_periods)
        self.sl = ema(self.candles, side, e.hourly_slow_ema_periods)

    def at(self, t: datetime) -> HourlyTrend:
        done = [c for c in self.candles if c.end <= t]
        n = self.e.hourly_slope_candles
        if len(done) < n + 1:
            return HourlyTrend(None, False, "not enough hourly candles")
        now, prev, back = done[-1].start, done[-2].start, done[-1 - n].start
        try:
            f, m, s = self.f[now], self.m[now], self.sl[now]
            fp, mp, sp = self.f[prev], self.m[prev], self.sl[prev]
            fb, mb, sb = self.f[back], self.m[back], self.sl[back]
        except KeyError:
            return HourlyTrend(None, False, "hourly EMAs not ready")
        if f > m > s and f > fp and m > mp and s > sp:
            d = BUY
        elif f < m < s and f < fp and m < mp and s < sp:
            d = SELL
        else:
            return HourlyTrend(None, False, f"hourly EMAs not in order and all moving one way "
                                            f"(8 {plain(f.quantize(Decimal('0.1')))}, 13 {plain(m.quantize(Decimal('0.1')))}, "
                                            f"20 {plain(s.quantize(Decimal('0.1')))})")
        slopes = [abs(x - y) / n / self.ppp for x, y in ((f, fb), (m, mb), (s, sb))]
        gaps = (abs(f - m) / self.ppp, abs(m - s) / self.ppp)
        ok = (min(slopes) >= self.e.hourly_min_slope_pips_per_hour
              and gaps[0] >= self.e.hourly_min_gap_fast_mid_pips and gaps[1] >= self.e.hourly_min_gap_mid_slow_pips)
        why = (f"hourly 8/13/20 EMAs in order, {'rising' if d == BUY else 'falling'}; slopes "
               + ", ".join(plain(x.quantize(Decimal('0.01'))) for x in slopes) + " pips/hour (min "
               f"{self.e.hourly_min_slope_pips_per_hour}); gaps {plain(gaps[0].quantize(Decimal('0.01')))} and "
               f"{plain(gaps[1].quantize(Decimal('0.01')))} pips (min {self.e.hourly_min_gap_fast_mid_pips} and "
               f"{self.e.hourly_min_gap_mid_slow_pips})")
        return HourlyTrend(d, ok, why)


@dataclass
class _Setup:
    direction: str
    touch: Candle
    entry: Decimal
    steps: list = field(default_factory=list)


class EmaPullback:
    def __init__(self, settings: Any, hourly: HourlyTrendReader):
        self.s, self.e = settings, settings.ema_pullback
        self.side = settings.chart.price
        self.ppp = Decimal(settings.market.points_per_pip)
        self.hourly = hourly
        self.done: list[Candle] = []                    # finished 5-minute candles so far
        self.prev_fast: Decimal | None = None
        self.setup: dict[str, _Setup | None] = {SELL: None, BUY: None}

    def _o(self, c): return getattr(c, f"{self.side}_open")
    def _h(self, c): return getattr(c, f"{self.side}_high")
    def _l(self, c): return getattr(c, f"{self.side}_low")
    def _c(self, c): return getattr(c, f"{self.side}_close")

    def on_candle(self, c: Candle, fast: Decimal | None, slow: Decimal | None) -> list[Candidate]:
        out: list[Candidate] = []
        q = lambda x: plain(x.quantize(Decimal("0.1")))  # noqa: E731
        expire = timedelta(minutes=self.e.setup_expires_after_minutes)
        for d in (BUY, SELL):
            st = self.setup[d]
            if st is None or slow is None:
                continue
            buy = d == BUY
            if c.start >= st.touch.start + expire:
                self.setup[d] = None                    # 5. expired
                continue
            reached = self._h(c) >= st.entry if buy else self._l(c) <= st.entry
            if reached:
                opened = self._o(c) >= st.entry if buy else self._o(c) <= st.entry
                price = self._o(c) if opened else st.entry
                self.setup[d] = None
                out.append(Candidate(EMA_PULLBACK, d, c.start, price, st.steps + [
                    f"{uk_short(c.start)}: price reached the entry {plain(st.entry)}"
                    + (f" (the candle opened past it, at {plain(price)})" if opened else " (during this candle)")]))
                continue
            if (self._c(c) < slow) if buy else (self._c(c) > slow):
                self.setup[d] = None                    # 2. closed beyond the 21 EMA
        # 1. a new touch (only with no setup running in that direction)
        if self.prev_fast is not None and len(self.done) >= self.e.entry_lookback_candles and slow is not None:
            trend = self.hourly.at(c.start)
            for d in (BUY, SELL):
                if self.setup[d] is not None or trend.direction != d or not trend.qualified:
                    continue
                buy = d == BUY
                touched = self._l(c) <= self.prev_fast if buy else self._h(c) >= self.prev_fast
                if not touched:
                    continue
                if (self._c(c) < slow) if buy else (self._c(c) > slow):
                    continue                            # the touch candle closed beyond the 21 EMA: cancelled at once
                before = self.done[-self.e.entry_lookback_candles:]
                beyond = Decimal(self.e.entry_beyond_pips) * self.ppp
                entry = (max(self._h(x) for x in before) + beyond) if buy else (min(self._l(x) for x in before) - beyond)
                self.setup[d] = _Setup(d, c, entry, [
                    f"step 0, {trend.why}",
                    f"{uk_short(c.start)}: price {'dropped' if buy else 'rose'} to the 5-minute "
                    f"{self.e.fast_ema_periods} EMA {q(self.prev_fast)} ({'low' if buy else 'high'} "
                    f"{plain(self._l(c) if buy else self._h(c))}); closed {q(self._c(c))}, "
                    f"{'above' if buy else 'below'} the {self.e.slow_ema_periods} EMA {q(slow)}",
                    f"entry {plain(entry)}: {self.e.entry_beyond_pips} pips {'above the highest high' if buy else 'below the lowest low'} "
                    f"of the {self.e.entry_lookback_candles} candles before ({uk_short(before[0].start)[-9:]} to "
                    f"{uk_short(before[-1].start)[-9:]}); expires {self.e.setup_expires_after_minutes} minutes after the touch"])
        self.done.append(c)
        self.prev_fast = fast
        return out
