"""The current list of levels: built from the candle store, written to one
file for the rest of the bot to read, and updated each time the price service
stores a new 5-minute candle.

Reads only the candle store. Never contacts IG. Every level uses the chart
price (settings [chart] price: the SELL (bid) price, to match the owner's chart).

The file: <levels.folder>/current.json (written with a safe write: a reader
never sees a half-written file). Read it with read_current().
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

from config.pairs import check_same_pair
from housekeeping.files import safe_write
from levels import rules
from levels.rules import Level
from prices.calendar import Boundaries, MarketHours
from prices.model import UK, Candle, iso, parse_iso, plain, uk_short
from prices.store import CandleStore

log = logging.getLogger("autobot.levels")
UTC = timezone.utc
FILE_NAME = "current.json"
SESSIONS = (("london", "London", rules.LONDON_HIGH, rules.LONDON_LOW),
            ("new_york", "New York", rules.NEW_YORK_HIGH, rules.NEW_YORK_LOW))
MAX_DAYS_BACK = 10   # how far back to look for the previous trading day / session (a calendar limit, not a level rule)


@dataclass
class LevelList:
    as_of: datetime
    day_start: datetime                  # start of today's daily candle (UTC)
    previous_day: Candle | None
    reference_price: Decimal | None      # the latest close (chart price), for round numbers
    levels: list[Level]
    groups: list[dict]
    warnings: list[str] = field(default_factory=list)
    side: str = "sell"                    # the price used: settings [chart] price

    def of_type(self, type_: str) -> list[Level]:
        return [lv for lv in self.levels if lv.type == type_]

    def group_of(self, lv: Level) -> dict:
        return self.groups[lv.group - 1]


def _uk_day(t: datetime) -> str:
    return uk_short(t)[:10]          # e.g. "Thu 05 Nov"


def previous_trading_day(b: Boundaries, day_start: datetime) -> tuple[datetime, datetime] | None:
    """The daily candle period before `day_start` in which the market was open.
    (So Monday's is the short Sunday candle, and Sunday's is Friday's.)"""
    t = day_start - timedelta(seconds=1)
    for _ in range(MAX_DAYS_BACK):
        s, e = b.regular("1d", t)
        if b.expected_parts(s, e) > 0:
            return s, e
        t = s - timedelta(seconds=1)
    return None


def build(settings: Any, store: CandleStore, as_of: datetime) -> LevelList:
    """Every level as it stood at `as_of`, using only candles that had finished by then."""
    check_same_pair(settings, store)
    lv_s, ppp = settings.levels, Decimal(settings.market.points_per_pip)
    side = settings.chart.price
    hours = MarketHours(settings.market_hours)
    b = Boundaries(settings.candles, hours)
    as_of = as_of.astimezone(UTC)
    day_start, _ = b.regular("1d", as_of)
    warnings: list[str] = []
    levels: list[Level] = []

    # ---- 1. daily pivots, and 2. the previous day's high and low ---------------
    prev = None
    period = previous_trading_day(b, day_start)
    if period is not None:
        prev = store.get("1d", period[0])
        if prev is not None and prev.end > as_of:
            prev = None
        if prev is None:
            warnings.append(f"The previous day's daily candle ({_uk_day(period[0])}) is not stored yet: "
                            "no pivots and no previous day high or low.")
    if prev is not None:
        src = f"daily candle {_uk_day(prev.start)} ({side} H {plain(rules.high(prev, side))} " \
              f"L {plain(rules.low(prev, side))} C {plain(rules.close(prev, side))})"
        if prev.parts != prev.expected_parts:
            warnings.append(f"The previous day's daily candle ({_uk_day(prev.start)}) is missing "
                            f"{prev.expected_parts - prev.parts} five-minute candle(s); pivots use it as stored.")
        levels += rules.daily_pivots(prev, side, lv_s.level_decimals, src)
        levels += rules.previous_day_high_low(prev, side, f"daily candle {_uk_day(prev.start)} ({side})")

    # ---- round numbers, around the latest close (chart price) ----------------------
    recent = [c for c in store.read_range("5m", as_of - timedelta(days=MAX_DAYS_BACK), as_of) if c.end <= as_of]
    reference = rules.close(recent[-1], side) if recent else None
    if reference is None:
        warnings.append("No 5-minute candle in the store before this time: no round numbers.")
    else:
        levels += rules.round_numbers(reference, Decimal(lv_s.round_number_every_pips) * ppp,
                                      Decimal(lv_s.round_numbers_within_pips) * ppp)

    # ---- session highs and lows (times in UTC) --------------------------------------
    today = day_start.astimezone(UK).date()
    for key, name, high_t, low_t in SESSIONS:
        frm, until = getattr(lv_s, f"{key}_session_from"), getattr(lv_s, f"{key}_session_until")
        # today's session (so far, if it is still running)
        levels += _session(recent, side, today, frm, until, as_of, name, high_t, low_t, "today")
        # the previous day that had this session
        for back in range(1, MAX_DAYS_BACK):
            found = _session(recent, side, today - timedelta(days=back), frm, until, as_of, name, high_t, low_t,
                             "previous")
            if found:
                levels += found
                break

    # ---- turning levels on the hourly chart ----------------------------------------
    since = as_of - timedelta(weeks=lv_s.turning_levels_lookback_weeks)
    margin = timedelta(days=MAX_DAYS_BACK)   # candles before `since`, needed as neighbours
    hourly = [c for c in store.read_range("1h", since - margin, as_of) if c.end <= as_of]
    levels += rules.turning_levels(
        hourly, side, since, lv_s.turning_candles_each_side, Decimal(lv_s.turning_min_move_pips) * ppp,
        lv_s.turning_move_within_candles,
        lambda c, which: f"hourly candle {uk_short(c.start)} {which} ({side})")

    # ---- 3. levels that line up -----------------------------------------------------
    grouped, groups = rules.group_levels(levels, Decimal(lv_s.line_up_within_pips) * ppp)
    return LevelList(as_of, day_start, prev, reference, grouped, groups, warnings, side)


def _session(candles: list[Candle], side: str, day: date, frm: time, until: time, as_of: datetime,
             name: str, high_t: str, low_t: str, which: str) -> list[Level]:
    start = datetime.combine(day, frm, tzinfo=UTC)
    end = datetime.combine(day, until, tzinfo=UTC)
    if start >= as_of:
        return []
    inside = [c for c in candles if start <= c.start and c.end <= min(end, as_of)]
    if not inside:
        return []
    so_far = "" if as_of >= end else f", so far (to {as_of.strftime('%H:%M')} UTC)"
    src = (f"{name} session {which} {start.strftime('%a %d %b')} "
           f"{frm.strftime('%H:%M')}-{until.strftime('%H:%M')} UTC{so_far}")
    return rules.session_high_low(inside, side, high_t, low_t, src, start)


# ---- 4. the file ---------------------------------------------------------------------

def to_json(ll: LevelList, written: datetime) -> dict:
    def level(lv: Level) -> dict:
        return {"price": plain(lv.price), "type": lv.type, "source": lv.source,
                "candle_utc": iso(lv.candle_utc) if lv.candle_utc else None,
                "important": lv.important, "group": lv.group}
    return {
        "written_utc": iso(written),
        "as_of_utc": iso(ll.as_of),
        "price_used": ll.side,
        "day_start_utc": iso(ll.day_start),
        "previous_day_candle_utc": iso(ll.previous_day.start) if ll.previous_day else None,
        "reference_price": plain(ll.reference_price) if ll.reference_price is not None else None,
        "warnings": ll.warnings,
        "levels": [level(lv) for lv in ll.levels],
        "groups": [{"group": g["group"], "low": plain(g["low"]), "high": plain(g["high"]),
                    "important": g["important"], "lined_up": g["lined_up"],
                    "levels": [f"{m.type} {plain(m.price)}" for m in g["members"]]} for g in ll.groups],
    }


def write_current(folder: Path, ll: LevelList, written: datetime) -> Path:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / FILE_NAME
    safe_write(path, (json.dumps(to_json(ll, written), indent=1) + "\n").encode())
    return path


def read_current(folder: Path) -> dict:
    """The current list of levels, as written. Prices are strings (exact)."""
    data = json.loads((Path(folder) / FILE_NAME).read_text())
    parse_iso(data["as_of_utc"])     # a quick check that it is the expected file
    return data


class LevelsUpdater:
    """Called by the price service after each new 5-minute candle is stored
    (and at start-up). It can never stop the price service: any problem is
    written as a warning and the old file is left as it was."""

    def __init__(self, settings: Any, store: CandleStore, warn: Callable[[str], None] | None = None):
        check_same_pair(settings, store)
        self.settings, self.store = settings, store
        self.warn = warn or (lambda m: log.warning(m))
        self.updates = 0
        self.last: LevelList | None = None
        self._last_warnings: list[str] = []

    def __call__(self, now: datetime) -> None:
        try:
            ll = build(self.settings, self.store, now)
            write_current(self.settings.levels.folder, ll, now)
        except Exception as e:   # never stop the price service
            self.warn(f"Levels not updated ({type(e).__name__}: {e}); the previous list is kept.")
            return
        self.updates += 1
        self.last = ll
        if ll.warnings != self._last_warnings:      # say each new warning once, not every 5 minutes
            for w in ll.warnings:
                self.warn("Levels: " + w)
            self._last_warnings = ll.warnings
        log.info("Levels updated: %d levels in %d groups (%d lined up).",
                 len(ll.levels), len(ll.groups), sum(1 for g in ll.groups if g["lined_up"]))
