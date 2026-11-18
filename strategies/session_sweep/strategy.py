"""Session sweep (design 3.8; owner, 16 November 2026). UK times, sell prices as on the chart. Written for a sell at
a high; a buy at a low is the mirror image.

  The levels: the Asian high and low (the 5-minute candles from session_sweep.asian_range_from, 00:00, up to
  session_sweep.asian_range_until, 07:00), used from 07:00; the London high and low (from
  session_sweep.london_range_from, 07:00, up to session_sweep.london_range_until, 12:00), fixed then and used from
  12:00 (the owner's answer 5). Each level for the rest of its UK day.
  1. The sweep: price goes at least session_sweep.beyond_pips (3) above the level.
  2. Then a 5-minute candle closes back inside the level (below it); it may be the same candle that went beyond
     (answer 6), and price may stay beyond for any time that day (answer 7). Exactly: a candle that closes below the
     level, where the candles since the last close below it, this one included, went at least beyond_pips above it.
     That candle is the rejection candle.
  3. The confirmation candle closes below the rejection candle's low within session_sweep.confirmation_within_candles
     (3) candles of it; price going above the rejection candle's high first cancels it (strategies/sessions.py, as
     the bounce: answer 8). While a setup waits at a level, that level starts no other.
  4. The trade opens at the next candle's open (live: its first price; never sent late).
  The stop: session_sweep.stop_beyond_furthest_pips (1) above the sweep's furthest point (the highest price from the
  first move beyond the level to the entry), and at least session_sweep.min_stop_pips (12) from the entry (answer 9):
  the idea's context "stop_price", as the level reversal's.
Each of the four levels at most once a day for a trade: the safety rules refuse it once a trade at that level has
opened that day (the idea's context "once_a_day"; answer 10). Nothing else in the strategies decides whether it
opens (like the bounce). Ideas only.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from prices.model import Candle, plain, uk_short
from strategies.common import BUY, SELL, SESSION_SWEEP, Candidate, signal_context
from strategies.sessions import Setup, confirm_step, uk_day_and_time, uk_zone


@dataclass
class Level:
    name: str                           # e.g. "Asian high"
    direction: str                      # a high gives sells, a low buys
    price: Decimal
    run: Decimal | None = None          # the furthest beyond it since the last close back inside (None: no run)
    setup: Setup | None = None

    def copy(self) -> "Level":
        return Level(self.name, self.direction, self.price, self.run, self.setup.copy() if self.setup else None)


class SessionSweep:
    def __init__(self, settings: Any):
        self.s = settings
        self.w = settings.session_sweep
        self.uk = uk_zone(settings)
        self.ppp = Decimal(settings.market.points_per_pip)
        self.beyond = Decimal(str(self.w.beyond_pips)) * self.ppp
        self.day = None
        self.ranges: dict[str, list] = {}   # "Asian" / "London" -> [high, low] while it forms
        self.levels: list[Level] = []
        self.due: list[tuple[Level, Setup]] = []
        self.notes: list[tuple] = []

    def fork(self) -> "SessionSweep":
        new = SessionSweep.__new__(SessionSweep)
        new.__dict__.update(self.__dict__)
        new.ranges = {k: list(v) for k, v in self.ranges.items()}
        new.levels = [lv.copy() for lv in self.levels]
        new.due = [(lv.copy(), st.copy()) for lv, st in self.due]
        new.notes = []
        return new

    def warm(self, candles: list) -> None:
        for c in candles:
            self._day(c)
            self._ranges(c)

    def _day(self, c: Candle) -> None:
        d, _ = uk_day_and_time(c, self.uk)
        if d != self.day:
            self.day, self.ranges, self.levels = d, {}, []

    def _ranges(self, c: Candle) -> None:
        """Build the Asian and London ranges; each becomes two levels at its end."""
        t = c.start.astimezone(self.uk).time()
        w = self.w
        for name, frm, until in (("Asian", w.asian_range_from, w.asian_range_until),
                                 ("London", w.london_range_from, w.london_range_until)):
            if frm <= t < until:
                hl = self.ranges.setdefault(name, [c.sell_high, c.sell_low])
                hl[0], hl[1] = max(hl[0], c.sell_high), min(hl[1], c.sell_low)
            elif t >= until and name in self.ranges and not any(lv.name.startswith(name) for lv in self.levels):
                hi, lo = self.ranges[name]
                self.levels += [Level(f"{name} high", SELL, hi), Level(f"{name} low", BUY, lo)]
                self.notes.append((c.start, "", f"{uk_short(c.start)} the {name} range {frm:%H:%M} to {until:%H:%M}: "
                                                f"high {plain(hi)}, low {plain(lo)}; levels from now"))

    def _stop(self, lv: Level, st: Setup, entry: Decimal) -> Decimal:
        far = st.context["furthest"]
        gap = Decimal(str(self.w.stop_beyond_furthest_pips)) * self.ppp
        least = Decimal(self.w.min_stop_pips) * self.ppp
        if lv.direction == SELL:
            return max(far + gap, entry + least)
        return min(far - gap, entry - least)

    def on_candle(self, c: Candle) -> list[Candidate]:
        """One 5-minute candle (finished; live, the one forming so far): the trades that open at its open."""
        out: list[Candidate] = []
        seen = set()
        for lv, st in self.due:                                         # 4. open at this candle's open
            if st.direction in seen:
                continue
            seen.add(st.direction)
            entry = c.sell_open
            stop = self._stop(lv, st, entry)
            pips = abs(stop - entry) / self.ppp
            steps = st.steps + [f"{uk_short(c.start)} opens at this candle's open, {plain(entry)} (sell price); stop "
                                f"{plain(stop)}, {plain(pips.quantize(Decimal('0.1')))} pips (at least "
                                f"{self.w.min_stop_pips}; {plain(self.w.stop_beyond_furthest_pips)} beyond the furthest "
                                f"point {plain(st.context['furthest'])})"]
            out.append(Candidate(SESSION_SWEEP, st.direction, c.start, entry, steps,
                                 {"stop_price": stop, "furthest": st.context["furthest"], "level_name": lv.name,
                                  "level": lv.price, "once_a_day": f"{SESSION_SWEEP} {lv.name} {self.day}",
                                  **signal_context(st.direction, st.rejection.start, st.context["furthest"],
                                                  st.rejection.sell_close)}))
        self.due = []
        self._day(c)
        self._ranges(c)                                                 # a range that ends now: its levels count from this candle
        for lv in self.levels:
            sell = lv.direction == SELL
            if lv.setup is not None:                                    # 3. confirm, cancel or expire
                what, text = confirm_step(lv.setup, c, int(self.w.confirmation_within_candles))
                if what != "waiting":
                    lv.setup.steps.append(text)
                    self.notes.append((c.start, lv.direction, text))
                    if what == "confirmed":
                        self.due.append((lv, lv.setup))
                    lv.setup = None
            extreme = c.sell_high if sell else c.sell_low
            far = extreme if lv.run is None else (max(lv.run, extreme) if sell else min(lv.run, extreme))
            inside = (c.sell_close < lv.price) if sell else (c.sell_close > lv.price)
            if not inside:
                lv.run = far                                            # 1. still beyond (or at) the level
                continue
            lv.run = None
            went = (far - lv.price) if sell else (lv.price - far)
            if went < self.beyond or lv.setup is not None:
                continue
            text = (f"{uk_short(c.start)} swept the {lv.name} {plain(lv.price)}, price went "
                    f"{plain((went / self.ppp).quantize(Decimal('0.1')))} pips {'above' if sell else 'below'} it "
                    f"(furthest {plain(far)}), and this candle closed back {'below' if sell else 'above'} it at "
                    f"{plain(c.sell_close)}, the rejection candle (high {plain(c.sell_high)}, low {plain(c.sell_low)})")
            self.notes.append((c.start, lv.direction, text))
            lv.setup = Setup(lv.direction, c, steps=[text], context={"furthest": far})
        return out
