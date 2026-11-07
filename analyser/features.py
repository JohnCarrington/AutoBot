"""What the market states look at, for each 5-minute candle (sell price).

Every value is worked out from candles up to and including that candle, so a
replay gives exactly what a live run gave. Distances are in pips (the pair's
own pip size). The words in the design become these measures (docs/ANALYSER.md):

  band width        upper minus lower Bollinger band
  flat / sloping    how far a band moved per candle over market_states.flat_slope_candles
  efficiency ratio  net move / total candle-to-candle movement over efficiency_candles
  crossings         closes crossing the middle band within crossing_candles
  EMA stack         7 < 13 < 21 (down) or 7 > 13 > 21 (up), and for how many candles
  weave             the stack order changed within weave_candles
  narrowing         for how many candles in a row the band width has got smaller
  no close outside  no candle closed outside the bands for consolidation_quiet_candles
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Sequence

from prices.indicators import bollinger, ema, macd, rsi
from prices.model import Candle

ZERO = Decimal(0)


@dataclass(frozen=True)
class Features:
    candle: Candle
    o: Decimal
    h: Decimal
    l: Decimal
    c: Decimal
    upper: Decimal | None
    middle: Decimal | None
    lower: Decimal | None
    width: Decimal | None                # pips
    narrowing_for: int                   # candles in a row the band width got smaller
    closed_outside: bool                 # this candle closed beyond a band
    no_close_outside: bool               # no candle closed beyond a band for consolidation_quiet_candles
    mid_slope: Decimal | None            # pips a candle
    upper_slope: Decimal | None
    lower_slope: Decimal | None
    ema7: Decimal | None
    ema13: Decimal | None
    ema21: Decimal | None
    ema100: Decimal | None
    stack: str | None                    # "up", "down" or None
    stacked_for: int                     # candles the current stack has held
    weave: bool                          # the EMA order changed within weave_candles
    ema100_move: Decimal | None          # pips, over ema100_flat_candles
    efficiency: Decimal | None
    crossings: int | None
    reached_upper: bool                  # this candle's high on or beyond the upper band
    reached_lower: bool
    both_bands_recently: bool            # both bands reached within ranging_both_bands_candles
    avg_body: Decimal | None             # pips, over consolidation_quiet_candles
    colour_ratio: Decimal | None         # larger of (green bodies, red bodies) / smaller
    body: Decimal                        # pips
    range_: Decimal                      # pips, high - low
    spike: bool                          # range more than spike_range_multiple x the average
    green_share: Decimal                 # green bodies / all bodies (size), over push_candles
    red_share: Decimal                   # red bodies / all bodies (size), over push_candles
    widening: Decimal | None             # band width now / width band_widening_candles ago
    fan: Decimal | None                  # pips between the 7 and 21 EMAs
    closes_on_upper: int                 # closes on or beyond the upper band, over push_candles
    closes_on_lower: int
    macd_hist: Decimal | None
    rsi: Decimal | None

    @property
    def green(self) -> bool:
        return self.c > self.o

    @property
    def red(self) -> bool:
        return self.c < self.o


def _stack(e7, e13, e21) -> str | None:
    if None in (e7, e13, e21):
        return None
    if e7 < e13 < e21:
        return "down"
    if e7 > e13 > e21:
        return "up"
    return None


def compute(candles: Sequence[Candle], settings: Any) -> list[Features]:
    """Features for every candle in order (the early ones lack what needs history)."""
    m, ind, side = settings.market_states, settings.indicators, settings.chart.price
    ppp = Decimal(settings.market.points_per_pip)
    near = Decimal(m.near_band_pips) * ppp
    g = lambda c, f: getattr(c, f"{side}_{f}")  # noqa: E731
    bands = bollinger(candles, side, ind.bollinger_periods, ind.bollinger_std_devs)
    emas = {p: ema(candles, side, p) for p in (7, 13, 21, 100)}
    hist = macd(candles, side, ind.macd_fast_periods, ind.macd_slow_periods, ind.macd_signal_periods)
    rs = rsi(candles, side, ind.rsi_periods)
    out: list[Features] = []
    closes = [g(c, "close") for c in candles]
    stacks: list[str | None] = []
    run = 0
    for i, c in enumerate(candles):
        b = bands.get(c.start)
        e7, e13, e21, e100 = (emas[p].get(c.start) for p in (7, 13, 21, 100))
        st = _stack(e7, e13, e21)
        run = run + 1 if stacks and st is not None and stacks[-1] == st else (1 if st else 0)
        stacks.append(st)

        def back(n: int):
            return out[i - n] if i - n >= 0 and i - n < len(out) else None

        def slope(attr: str, n: int) -> Decimal | None:
            prev = candles[i - n] if i - n >= 0 else None
            pb = bands.get(prev.start) if prev else None
            if b is None or pb is None:
                return None
            return (getattr(b, attr) - getattr(pb, attr)) / n / ppp

        o, h, lo, cl = g(c, "open"), g(c, "high"), g(c, "low"), g(c, "close")
        reached_up = b is not None and h >= b.upper - near
        reached_dn = b is not None and lo <= b.lower + near
        n_eff = m.efficiency_candles
        eff = None
        if i >= n_eff:
            path = sum(abs(closes[j] - closes[j - 1]) for j in range(i - n_eff + 1, i + 1))
            eff = (abs(closes[i] - closes[i - n_eff]) / path) if path else ZERO
        crossings = None
        if i >= m.crossing_candles and b is not None:
            signs = []
            for j in range(i - m.crossing_candles, i + 1):
                bj = bands.get(candles[j].start)
                if bj is None:
                    signs = []
                    break
                signs.append(closes[j] > bj.middle)
            crossings = sum(1 for a, z in zip(signs, signs[1:]) if a != z) if signs else None
        width = (b.upper - b.lower) / ppp if b else None
        prev = out[-1] if out else None
        narrowing = (prev.narrowing_for + 1 if prev is not None and prev.width is not None and width is not None
                     and width < prev.width else 0)
        outside = b is not None and (cl > b.upper or cl < b.lower)
        recent = out[max(0, i - m.ranging_both_bands_candles + 1):] if out else []
        both = (reached_up or any(f.reached_upper for f in recent)) and \
               (reached_dn or any(f.reached_lower for f in recent))
        qn = m.consolidation_quiet_candles
        window = out[i - qn + 1:] if i - qn + 1 >= 0 else []
        no_outside = len(window) == qn - 1 and b is not None and not outside and \
            not any(f.closed_outside for f in window)
        bodies = [abs(g(x, "close") - g(x, "open")) / ppp for x in candles[max(0, i - qn + 1):i + 1]]
        avg_body = sum(bodies) / len(bodies) if len(bodies) == qn else None
        greens = sum(abs(g(x, "close") - g(x, "open")) for x in candles[max(0, i - qn + 1):i + 1]
                     if g(x, "close") > g(x, "open"))
        reds = sum(abs(g(x, "close") - g(x, "open")) for x in candles[max(0, i - qn + 1):i + 1]
                   if g(x, "close") < g(x, "open"))
        lo_side, hi_side = min(greens, reds), max(greens, reds)
        colour_ratio = (hi_side / lo_side) if lo_side else (Decimal(1) if hi_side == 0 else None)
        rng = (h - lo) / ppp
        prev_ranges = [(g(x, "high") - g(x, "low")) / ppp for x in candles[max(0, i - m.spike_average_candles):i]]
        avg_range = sum(prev_ranges) / len(prev_ranges) if len(prev_ranges) == m.spike_average_candles else None
        spike = avg_range is not None and avg_range > 0 and rng > avg_range * m.spike_range_multiple
        pc = candles[max(0, i - m.push_candles + 1):i + 1]
        # by body SIZE, so a few big red candles with small green ones between still count as red
        up_bodies = sum((g(x, "close") - g(x, "open") for x in pc if g(x, "close") > g(x, "open")), ZERO)
        down_bodies = sum((g(x, "open") - g(x, "close") for x in pc if g(x, "close") < g(x, "open")), ZERO)
        all_bodies = up_bodies + down_bodies
        green_share = up_bodies / all_bodies if all_bodies else ZERO
        red_share = down_bodies / all_bodies if all_bodies else ZERO
        wb = back(m.band_widening_candles)
        widening = (width / wb.width) if (width is not None and wb is not None and wb.width) else None
        on_up = on_dn = 0
        for x in pc:
            bx = bands.get(x.start)
            if bx is not None:
                on_up += g(x, "close") >= bx.upper - near
                on_dn += g(x, "close") <= bx.lower + near
        e100b = back(m.ema100_flat_candles)
        weave_window = stacks[max(0, i - m.weave_candles):i + 1]
        weave = len(set(weave_window)) > 1
        mh = hist.get(c.start)
        out.append(Features(
            c, o, h, lo, cl, b.upper if b else None, b.middle if b else None, b.lower if b else None, width,
            narrowing, outside, no_outside,
            slope("middle", m.flat_slope_candles), slope("upper", m.flat_slope_candles),
            slope("lower", m.flat_slope_candles), e7, e13, e21, e100, st, run, weave,
            (abs(e100 - e100b.ema100) / ppp) if (e100 is not None and e100b is not None and e100b.ema100 is not None)
            else None,
            eff, crossings, reached_up, reached_dn, both, avg_body, colour_ratio,
            abs(cl - o) / ppp, rng, spike, green_share, red_share, widening,
            (abs(e7 - e21) / ppp) if (e7 is not None and e21 is not None) else None,
            on_up, on_dn, mh.histogram if mh else None, rs.get(c.start)))
    return out
