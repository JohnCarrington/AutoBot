"""Bollinger band bounce (design 3.3; owner, 15 November 2026). Written for a sell; a buy is the mirror image.

  1. The pierce, on the hourly chart: a 5-minute candle's high goes more than bounce.pierce_beyond_pips (3) above
     the hourly upper Bollinger band (20, 2), the band as the owner's IG hourly chart showed it at that moment: the
     forming hour's band with the high as its close (prices/hourly_chart.py).
  2. The rejection candle is that same 5-minute candle, and it is red (closes below its open), whatever its size
     (owner's choices A and C, 15 November 2026).
  3. The confirmation candle: a later 5-minute candle closes below the rejection candle's low, within
     bounce.confirmation_within_candles (3) candles of it, or the setup expires (choice D). A wick does not count.
  4. The sell opens at the next candle's open (live: its first price).
  5. Price going above the rejection candle's high before the confirmation cancels the setup (choice E). A candle
     that goes above it and also closes below the low counts as the cancel (the order inside a candle is unknown).
Spread spikes (over rejection.max_spread_pips, the widest buy-minus-sell gap of the candle's open, high, low and
close): that candle's high or low cannot make a pierce or cancel a setup (owner, 15 November 2026, G5); its close
still counts for the confirmation.
Every rejection candle starts its own setup; setups that confirm the same way in the same candle are one bounce.
If the hourly band is not known (an hour missing from the hourly chart while the market was open), nothing starts.
Nothing else in the strategies decides whether it opens: not the analyser's state, not the direction rule, not the
hourly read (strategies/common.py). Ideas only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from prices.hourly_chart import HourlyChart
from prices.model import Candle, plain, uk_short
from strategies.common import BOLLINGER_BOUNCE, BUY, SELL, Candidate


def spread(c: Candle) -> Decimal:
    """The candle's spread: the widest of its four buy-minus-sell gaps (as the shared rejection part)."""
    return max(c.buy_open - c.sell_open, c.buy_high - c.sell_high, c.buy_low - c.sell_low, c.buy_close - c.sell_close)


@dataclass
class Setup:
    direction: str
    rejection: Candle
    band: Decimal                       # the hourly band at the rejection candle's high (sell) or low (buy)
    beyond_pips: Decimal
    candles: int = 0                    # candles since the rejection candle
    steps: list = field(default_factory=list)


class BollingerBounce:
    def __init__(self, settings: Any):
        self.s = settings
        b = settings.bounce
        self.ppp = Decimal(settings.market.points_per_pip)
        self.beyond = Decimal(str(b.pierce_beyond_pips)) * self.ppp
        self.within = int(b.confirmation_within_candles)
        self.max_spread = Decimal(settings.rejection.max_spread_pips) * self.ppp
        self.chart = HourlyChart(settings)
        self.waiting: list[Setup] = []
        self.due: list[Setup] = []           # confirmed: they open at the next candle's open
        self.notes: list[tuple] = []         # (time, direction, text): every step, for the replay and the records

    def fork(self) -> "BollingerBounce":
        new = BollingerBounce.__new__(BollingerBounce)
        new.__dict__.update(self.__dict__)
        new.chart = self.chart.copy()
        new.waiting = [Setup(x.direction, x.rejection, x.band, x.beyond_pips, x.candles, list(x.steps))
                       for x in self.waiting]
        new.due = list(self.due)
        new.notes = []
        return new

    def warm(self, candles: list) -> None:
        """The finished 5-minute candles before the replay starts: the hourly chart only."""
        for c in candles:
            self.chart.add(c)

    def _note(self, c: Candle, direction: str, text: str, st: Setup | None = None) -> None:
        self.notes.append((c.start, direction, text))
        if st is not None:
            st.steps.append(text)

    def on_candle(self, c: Candle) -> list[Candidate]:
        """One 5-minute candle (finished; live, the one forming so far): the bounces that open at its open."""
        out: list[Candidate] = []
        seen = set()
        for st in self.due:                                         # 4. open at this candle's open
            if st.direction in seen:
                continue
            seen.add(st.direction)
            steps = st.steps + [f"{uk_short(c.start)} opens at this candle's open, {plain(c.sell_open)} (sell price)"]
            out.append(Candidate(BOLLINGER_BOUNCE, st.direction, c.start, c.sell_open, steps, {}))
        self.due = []
        spike = spread(c) > self.max_spread
        for st in list(self.waiting):                               # 5. cancel, 3. confirm, or expire
            st.candles += 1
            sell = st.direction == SELL
            r = st.rejection
            beyond_cancel = (c.sell_high > r.sell_high) if sell else (c.sell_low < r.sell_low)
            if beyond_cancel and not spike:
                self._note(c, st.direction, f"{uk_short(c.start)} cancelled: price went "
                           f"{'above' if sell else 'below'} the rejection candle's {'high' if sell else 'low'} "
                           f"({plain(r.sell_high if sell else r.sell_low)})", st)
                self.waiting.remove(st)
                continue
            if beyond_cancel:
                self._note(c, st.direction, f"{uk_short(c.start)} went past the rejection candle's "
                           f"{'high' if sell else 'low'} but IG's spread was {plain(spread(c))} points: ignored", st)
            confirmed = (c.sell_close < r.sell_low) if sell else (c.sell_close > r.sell_high)
            if confirmed:
                self._note(c, st.direction, f"{uk_short(c.start)} confirmation candle: closed at {plain(c.sell_close)}, "
                           f"{'below' if sell else 'above'} the rejection candle's {'low' if sell else 'high'} "
                           f"({plain(r.sell_low if sell else r.sell_high)})", st)
                self.waiting.remove(st)
                self.due.append(st)
            elif st.candles >= self.within:
                self._note(c, st.direction, f"{uk_short(c.start)} expired: no confirmation within {self.within} "
                           f"candles of the rejection candle", st)
                self.waiting.remove(st)
        for direction in (SELL, BUY):                               # 1. and 2. a new rejection candle
            sell = direction == SELL
            if (c.sell_close >= c.sell_open) if sell else (c.sell_close <= c.sell_open):
                continue                                            # not red (sell) / not green (buy)
            extreme = c.sell_high if sell else c.sell_low
            band = self.chart.band_at(c.start, extreme)
            if band is None:
                continue
            edge = band.upper if sell else band.lower
            past = (extreme - edge) if sell else (edge - extreme)
            if past <= self.beyond:
                continue
            what = (f"{uk_short(c.start)} pierce and rejection candle: its {'high' if sell else 'low'} {plain(extreme)} "
                    f"went {plain((past / self.ppp).quantize(Decimal('0.1')))} pips "
                    f"{'above the upper' if sell else 'below the lower'} hourly Bollinger band "
                    f"({plain(edge.quantize(Decimal('0.1')))} at that moment), and it closed "
                    f"{'red' if sell else 'green'} ({plain(c.sell_open)} to {plain(c.sell_close)})")
            if spike:
                self._note(c, direction, what + f"; IG's spread was {plain(spread(c))} points: ignored")
                continue
            st = Setup(direction, c, edge, past / self.ppp)
            self._note(c, direction, what, st)
            self.waiting.append(st)
        self.chart.add(c)
        return out
