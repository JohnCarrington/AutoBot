"""EMA pullback (design 3.2), written for a buy; a sell is the mirror image.
Sell (bid) price for every indicator. Only the rules written in 3.2:

  0. The trend must be established on the hourly chart: hourly 8, 13 and 20
     EMAs in order and all rising, with the slope and gap minimums from AutoBot
     161's service (ema_pullback.hourly_*: each EMA rising since the hourly
     candle before; slope over the last 3 hourly candles in the trend's
     direction (rising for a buy, falling for a sell) and at least 0.16 pips an
     hour; gaps at least 0.25 and 0.20 pips).
  1. While a 5-minute candle is forming, the live price drops to the 5-minute
     8 EMA. Price may cross the 8 and even the 13 EMA.
  2. If a 5-minute candle closes below the 21 EMA, the setup is cancelled.
  3. The entry price is entry_beyond_pips (3) above the highest high of the
     entry_lookback_candles (5) completed 5-minute candles immediately before
     the touch candle (AutoBot 161's rule; owner, 7 November 2026).
  4. The trade opens as soon as the live price reaches the entry price.
  5. If it has not opened within setup_expires_after_minutes (20), it expires.

Choices section 3.2 does not make (the simplest, adding no rule; listed for the owner):
  * the live 8 EMA moves with the price, and price is at or below it exactly
    when it is at or below the last finished candle's 8 EMA; so a candle whose
    low reaches that value is a touch candle;
  * every touch candle starts its own setup (several may run at once);
  * rule 0 is checked at the touch (the step before step 1), from the last
    finished hourly candle;
  * rule 2 applies from the touch candle on (its own close included);
  * with stored candles the entry is looked for from the candle after the touch
    (inside the touch candle the order of prices is unknown), in candles
    starting less than 20 minutes after the touch candle started; a candle that
    opened past the entry enters at its open.
Ideas only.
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
        # each EMA's slope over the last n hourly candles, signed in the trend's direction: AutoBot 161's rule, "the
        # right sign and absolute magnitude >= 0.16 pips/hour" (owner, 13 November 2026)
        sign = 1 if d == BUY else -1
        slopes = [sign * (x - y) / n / self.ppp for x, y in ((f, fb), (m, mb), (s, sb))]
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
        self.setups: list[_Setup] = []
        self.notes: list[tuple] = []              # (time, direction, what happened), for checking

    def _o(self, c): return getattr(c, f"{self.side}_open")
    def _h(self, c): return getattr(c, f"{self.side}_high")
    def _l(self, c): return getattr(c, f"{self.side}_low")
    def _c(self, c): return getattr(c, f"{self.side}_close")

    def on_candle(self, c: Candle, fast: Decimal | None, slow: Decimal | None) -> list[Candidate]:
        out: list[Candidate] = []
        q = lambda x: plain(x.quantize(Decimal("0.1")))  # noqa: E731
        expire = timedelta(minutes=self.e.setup_expires_after_minutes)
        for st in list(self.setups):
            d, buy = st.direction, st.direction == BUY
            tag = f"setup from {uk_short(st.touch.start)[-9:]}"
            if c.start >= st.touch.start + expire:                          # 5.
                self.setups.remove(st)
                self.notes.append((c.start, d, f"{tag}: expired, {plain(st.entry)} not reached within "
                                               f"{self.e.setup_expires_after_minutes} minutes"))
                continue
            if self._h(c) >= st.entry if buy else self._l(c) <= st.entry:   # 4.
                opened = self._o(c) >= st.entry if buy else self._o(c) <= st.entry
                price = self._o(c) if opened else st.entry
                self.setups.remove(st)
                self.notes.append((c.start, d, f"{tag}: reached the entry {plain(st.entry)}: entry {plain(price)}"))
                out.append(Candidate(EMA_PULLBACK, d, c.start, price, st.steps + [
                    f"{uk_short(c.start)}: price reached the entry {plain(st.entry)}"
                    + (f" (the candle opened past it, at {plain(price)})" if opened else " (during this candle)")]))
                continue
            if slow is not None and ((self._c(c) < slow) if buy else (self._c(c) > slow)):   # 2.
                self.setups.remove(st)
                self.notes.append((c.start, d, f"{tag}: closed {q(self._c(c))} {'below' if buy else 'above'} the "
                                               f"{self.e.slow_ema_periods} EMA {q(slow)}: cancelled"))
        # 1. a touch candle (0. with the hourly trend)
        if self.prev_fast is not None and slow is not None and len(self.done) >= self.e.entry_lookback_candles:
            trend = self.hourly.at(c.start)
            for d in (BUY, SELL):
                buy = d == BUY
                if not (self._l(c) <= self.prev_fast if buy else self._h(c) >= self.prev_fast):
                    continue
                if trend.direction != d or not trend.qualified:
                    if trend.direction == d:
                        self.notes.append((c.start, d, f"touched the 8 EMA {q(self.prev_fast)}; the hourly trend "
                                                       f"is not qualified ({trend.why})"))
                    continue
                if (self._c(c) < slow) if buy else (self._c(c) > slow):
                    self.notes.append((c.start, d, f"touched the 8 EMA {q(self.prev_fast)}; the touch candle closed "
                                                   f"{q(self._c(c))} {'below' if buy else 'above'} the "
                                                   f"{self.e.slow_ema_periods} EMA {q(slow)}: cancelled"))
                    continue
                before = self.done[-self.e.entry_lookback_candles:]
                beyond = Decimal(self.e.entry_beyond_pips) * self.ppp
                entry = (max(self._h(x) for x in before) + beyond) if buy else (min(self._l(x) for x in before) - beyond)
                self.setups.append(_Setup(d, c, entry, [
                    f"step 0, {trend.why}",
                    f"{uk_short(c.start)}: price {'dropped' if buy else 'rose'} to the 5-minute "
                    f"{self.e.fast_ema_periods} EMA {q(self.prev_fast)} ({'low' if buy else 'high'} "
                    f"{plain(self._l(c) if buy else self._h(c))}); closed {q(self._c(c))}, "
                    f"{'above' if buy else 'below'} the {self.e.slow_ema_periods} EMA {q(slow)}",
                    f"entry {plain(entry)}: {self.e.entry_beyond_pips} pips {'above the highest high' if buy else 'below the lowest low'} "
                    f"of the {self.e.entry_lookback_candles} candles before the touch candle "
                    f"({uk_short(before[0].start)[-9:]} to {uk_short(before[-1].start)[-9:]}); expires "
                    f"{self.e.setup_expires_after_minutes} minutes after the touch"]))
                self.notes.append((c.start, d, f"setup: touched the 8 EMA {q(self.prev_fast)}, entry {plain(entry)}"))
        self.done.append(c)
        self.prev_fast = fast
        return out
