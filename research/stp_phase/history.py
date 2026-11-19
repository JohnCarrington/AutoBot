"""Inputs for the market-phase research model (planner/phase.py), from a candle store. RESEARCH ONLY; reads candles,
writes nothing, never contacts IG.

Two ways to build the same PhaseInputs at a moment `as_of`, both from candles that had FINISHED by then:

  exact_inputs   the live planner's own code: planner/measure.py snapshot (the last 2000 hourly candles, 4-hour
                 candles rebuilt from them, the bot's indicators), levels/current.py build (the existing levels,
                 session highs and lows included) and planner/zones.py level_map / zones. About 1 second a moment.
                 Used for the 18 November replay, the trade-entry checks and the compatibility test.
  FastHistory    the whole hourly history loaded once; indicators computed once over it (causal recursions and
                 rolling windows, so the value at a candle depends only on candles up to it); swings found once and
                 used only from their `known_utc`; at each moment every list is cut at `as_of`. The level map is the
                 same, built from the bot's own level rules, except that London / New York session highs and lows
                 are left out (they need 5-minute candles). Used for the multi-year validation. Its 4-hour V1
                 direction is checked against the live planner on a random sample (research/stp_phase/validate.py).
"""

from __future__ import annotations

import bisect
import csv
import gzip
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any

from levels import rules
from planner.measure import Frame, adr as adr_of, cl, four_hour_from_hourly, frame, is_sunday_candle, snapshot
from planner.phase import PhaseInputs
from planner.structure import swings
from planner.zones import (_FROM_LEVELS, MOVING_AVERAGE, PIVOT, SESSION, MapLevel, average_levels, flipped,
                           level_map, swing_levels, zones)
from prices.model import Candle, parse_iso

UTC = timezone.utc


def indicator_levels(h1: Frame) -> list[MapLevel]:
    """The hourly indicator levels the countertrend analysis also looks at: EMA21 and the Bollinger middle, upper and
    lower bands. A moving family (never "meaningful" on its own)."""
    if not h1.candles:
        return []
    t = h1.candles[-1].start
    out = []
    e21 = h1.ema.get(21, {}).get(t)
    if e21 is not None:
        out.append(MapLevel(e21.quantize(Decimal("0.1")), "H1 EMA21", MOVING_AVERAGE, "1h", "moving average", t, False, False))
    b = h1.band.get(t)
    if b is not None:
        for name, v in (("H1 Bollinger middle", b.middle), ("H1 Bollinger upper", b.upper), ("H1 Bollinger lower", b.lower)):
            out.append(MapLevel(v.quantize(Decimal("0.1")), name, MOVING_AVERAGE, "1h", "moving average", t, False, False))
    return out


def _spread(c: Candle | None) -> Decimal | None:
    return None if c is None else (c.buy_close - c.sell_close)


# ---- exact: the live planner's own code ----------------------------------------------------------------------------

def exact_inputs(settings: Any, store: Any, as_of: datetime) -> tuple[PhaseInputs, Any]:
    """(PhaseInputs, snapshot) at as_of with the planner's own snapshot, existing levels, level map and zones."""
    from levels.current import build
    snap = snapshot(settings, store, as_of)
    h4_found = swings(settings, snap.h4.candles, "4h")
    d1_found = swings(settings, snap.d1.candles, "1d")
    zs = lm = None
    if snap.price is not None and snap.adr is not None:
        existing = build(settings, store, as_of)
        lm = level_map(settings, snap, existing, h4_found, d1_found) + indicator_levels(snap.h1)
        zs = zones(settings, lm, snap.adr, snap.h1.candles[-300:], snap.price)
    inp = PhaseInputs(as_of, snap.h4, snap.h1, h4_found, snap.fives, snap.adr, zs, lm, _spread(snap.five))
    return inp, snap


# ---- fast: whole history once ----------------------------------------------------------------------------------------

def _read(path: Path, tf: str) -> list[Candle]:
    data = gzip.decompress(path.read_bytes()).decode() if path.suffix == ".gz" else path.read_text()
    out = []
    for r in csv.DictReader(data.splitlines()):
        D = Decimal
        out.append(Candle(tf, parse_iso(r["start_utc"]), parse_iso(r["end_utc"]), D(r["buy_open"]), D(r["buy_high"]),
                          D(r["buy_low"]), D(r["buy_close"]), D(r["sell_open"]), D(r["sell_high"]), D(r["sell_low"]),
                          D(r["sell_close"]), int(r["parts"]), int(r["expected_parts"])))
    return out


def load_tf(folder: Path, tf: str) -> list[Candle]:
    seen: dict[datetime, Candle] = {}
    names = {}
    for p in sorted((folder / tf).iterdir()):
        day = p.name.split(".")[0]
        if p.suffix == ".csv" or day not in names:          # a plain file wins over its .gz
            names[day] = p
    for day in sorted(names):
        for c in _read(names[day], tf):
            seen[c.start] = c
    return [seen[k] for k in sorted(seen)]


def _cut(f: Frame, k: int) -> Frame:
    return Frame(f.timeframe, f.candles[:k], f.ema, f.band, f.macd, f.rsi, [])


@dataclass
class Moment:
    inputs: PhaseInputs
    price: Decimal
    h1_index: int                 # number of finished hourly candles


class FastHistory:
    def __init__(self, settings: Any, folder: str | Path, until: datetime | None = None):
        self.s = settings
        self.folder = Path(folder)
        h1 = load_tf(self.folder, "1h")
        if until is not None:
            h1 = [c for c in h1 if c.end <= until]
        self.h1_all = h1
        self.h1 = frame(settings, "1h", h1)
        self.h1_ends = [c.end for c in h1]
        four = four_hour_from_hourly(settings, h1, h1[-1].end)
        self.h4 = frame(settings, "4h", four)
        self.h4.ema.pop(200, None)                          # warming up in the live planner (2000 hourly candles)
        self.h4_ends = [c.end for c in four]
        self.d1_all = load_tf(self.folder, "1d")
        self.d1_ends = [c.end for c in self.d1_all]
        self.w1_all = load_tf(self.folder, "1w") if (self.folder / "1w").is_dir() else []
        self.w1_ends = [c.end for c in self.w1_all]
        self.h4_sw = swings(settings, four, "4h")
        self.d1_sw = swings(settings, self.d1_all, "1d")
        self.h1_sw = swings(settings, h1, "1h")

    # ---- 5-minute candles, one day at a time ----
    @lru_cache(maxsize=8)
    def fives_day(self, day: str) -> tuple:
        for name in (f"{day}.csv", f"{day}.csv.gz"):
            p = self.folder / "5m" / name
            if p.exists():
                return tuple(_read(p, "5m"))
        return ()

    def fives_until(self, as_of: datetime, n: int = 864) -> list[Candle]:
        days = [(as_of - timedelta(days=k)).strftime("%Y-%m-%d") for k in (3, 2, 1, 0)]
        cs = [c for d in days for c in self.fives_day(d) if c.end <= as_of]
        return cs[-n:]

    def adr_at(self, as_of: datetime) -> Decimal | None:
        k = bisect.bisect_right(self.d1_ends, as_of)
        return adr_of(self.s, self.d1_all[max(0, k - 60):k])

    def levels_at(self, as_of: datetime, h1: Frame, h4: Frame, price: Decimal) -> list[MapLevel]:
        s, side = self.s, self.s.chart.price
        dec = s.levels.level_decimals
        out: list[MapLevel] = []
        k = bisect.bisect_right(self.d1_ends, as_of)
        prev = next((c for c in reversed(self.d1_all[max(0, k - 5):k]) if not is_sunday_candle(c)), None)
        conv = lambda lv: MapLevel(lv.price, *(_FROM_LEVELS[lv.type][:2]), _FROM_LEVELS[lv.type][2],  # noqa: E731
                                   _FROM_LEVELS[lv.type][3], lv.candle_utc, _FROM_LEVELS[lv.type][4],
                                   lv.type not in (rules.ROUND_NUMBER,), lv.source)
        if prev is not None:
            out += [conv(lv) for lv in rules.daily_pivots(prev, side, dec, "daily")]
            out += [conv(lv) for lv in rules.previous_day_high_low(prev, side, "daily")]
        ppp = Decimal(s.market.points_per_pip)
        out += [conv(lv) for lv in rules.round_numbers(price, Decimal(s.levels.round_number_every_pips) * ppp,
                                                        Decimal(s.levels.round_numbers_within_pips) * ppp)]
        since = as_of - timedelta(weeks=s.levels.turning_levels_lookback_weeks)
        for sw in self.h1_sw:
            if sw.known_utc <= as_of and sw.candle_utc >= since:
                out.append(MapLevel(sw.price, f"hourly swing {sw.kind}", "structure", "1h", "hourly swing", sw.candle_utc,
                                    False, True))
        kw = bisect.bisect_right(self.w1_ends, as_of)
        if kw:
            wk = self.w1_all[kw - 1]
            for lv in rules.daily_pivots(wk, side, dec, "weekly"):
                name = "weekly pivot" if lv.type == rules.PIVOT else f"weekly {lv.type}"
                out.append(MapLevel(lv.price, name, PIVOT, "weekly", "weekly pivot" if lv.type == rules.PIVOT else "weekly R/S",
                                    wk.start, True, True))
            out.append(MapLevel(wk.sell_high if side == "sell" else wk.buy_high, "previous week high", SESSION, "weekly",
                                "previous week high/low", wk.start, True, True))
            out.append(MapLevel(wk.sell_low if side == "sell" else wk.buy_low, "previous week low", SESSION, "weekly",
                                "previous week high/low", wk.start, True, True))
        out += swing_levels([x for x in self.h4_sw if x.known_utc <= as_of], as_of, s.planner.h4_swing_lookback_weeks)
        out += swing_levels([x for x in self.d1_sw if x.known_utc <= as_of], as_of, s.planner.daily_swing_lookback_weeks)
        snap_like = type("S", (), {"h1": h1, "h4": h4})()
        out += average_levels(snap_like, dec)
        out += indicator_levels(h1)
        out = flipped(s, out, h1.candles[-300:], price)
        return out

    def moment(self, as_of: datetime, with_zones: bool = True) -> Moment | None:
        k1 = bisect.bisect_right(self.h1_ends, as_of)
        k4 = bisect.bisect_right(self.h4_ends, as_of)
        if k1 < 300 or k4 < 60:
            return None
        h1, h4 = _cut(self.h1, k1), _cut(self.h4, k4)
        fives = self.fives_until(as_of)
        if not fives:
            return None
        price = cl(fives[-1], self.s.chart.price)
        adr = self.adr_at(as_of)
        h4_sw = [x for x in self.h4_sw if x.known_utc <= as_of]
        zs = lm = None
        if with_zones and adr is not None:
            lm = self.levels_at(as_of, h1, h4, price)
            zs = zones(self.s, lm, adr, h1.candles[-200:], price)
        inp = PhaseInputs(as_of, h4, h1, h4_sw, fives, adr, zs, lm, _spread(fives[-1]))
        return Moment(inp, price, k1)
