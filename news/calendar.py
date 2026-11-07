"""The economic calendar's rules (design sections 2.4 and 6), from the copy on
disk (news/finnhub.py). Contacts nobody.

  * tier: BIG, MEDIUM or SMALL from AutoBot's news table, config/news_table.toml
    (the owner's table from AutoBot 161; matching in news/table.py: overrides,
    then big rules, then medium rules, otherwise SMALL, logged once).
  * no-trading windows: for each BIG release in a currency of the pair (GBPUSD:
    GBP and USD), no new trades from news.big_news_no_new_trades_before_minutes
    before to news.big_news_no_new_trades_after_minutes after; open trades
    closed news.big_news_close_trades_before_minutes before. MEDIUM and SMALL
    releases are ignored (news.ignore_medium_and_small_news).
  * expected direction for a TIME with big releases (section 2.4): if they all
    agree, that direction; if they disagree, the headline release decides (the
    news table's [[headline]] order); if it has no direction, there is none.
  * expected direction of a BIG release (section 2.4): the forecast (estimate)
    against the previous figure. Higher is good for the currency, except for the
    names in news.lower_is_better. Good for the pair's first currency (GBP in
    GBPUSD) -> up; good for its second (USD) -> down. Equal figures -> in line;
    missing figures (speeches, minutes) -> no direction.
  * out of date: no good fetch within news.out_of_date_hours (or never). That is
    reported (a Telegram problem alert from the price service), and does NOT
    block trading by itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from pathlib import Path

from news.finnhub import read_store

UTC = timezone.utc
from news.table import (BIG, MEDIUM, SMALL, UnmatchedLog, classify, headline_rank,  # noqa: E402
                        load_headline, load_table)

_TABLE: dict = {}


def table(path=None) -> list:
    """The news table, read once and again whenever the file changes."""
    from news.table import TABLE_PATH
    p = Path(path or TABLE_PATH)
    stamp = p.stat().st_mtime_ns
    if _TABLE.get("stamp") != (str(p), stamp):
        _TABLE["rows"], _TABLE["stamp"] = load_table(p), (str(p), stamp)
    return _TABLE["rows"]
UP, DOWN, IN_LINE, NO_DIRECTION = "up", "down", "in line", "no direction"


def _t(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def currency_of(settings: Any, country: str) -> str | None:
    return settings.news.country_currencies.get(country.upper())


def tier_of(settings: Any, currency: str | None, event: str, impact: Any = "high",
            same_day_names: tuple = ()) -> str:
    """The tier of a release by name (a high-impact release, with no other release that day, unless given)."""
    return classify(table(), settings, currency, event, impact, same_day_names).tier


def _num(x: Any) -> Decimal | None:
    if x is None or isinstance(x, bool):
        return None
    try:
        d = Decimal(str(x))
    except InvalidOperation:
        return None
    return d if d.is_finite() else None


def expected_direction(settings: Any, pair: str, currency: str, event: str, estimate: Any, prev: Any) -> tuple[str, str]:
    """(direction for the pair, plain reason)."""
    est, pv = _num(estimate), _num(prev)
    if est is None or pv is None:
        return NO_DIRECTION, "no forecast and previous figures to compare"
    if est == pv:
        return IN_LINE, f"forecast {est} the same as previous {pv}"
    lower_good = any(k.lower() in event.lower() for k in settings.news.lower_is_better)
    good = (est < pv) if lower_good else (est > pv)
    if currency == pair[:3]:
        d = UP if good else DOWN
    elif currency == pair[3:]:
        d = DOWN if good else UP
    else:
        return NO_DIRECTION, f"{currency} is not in {pair}"
    rule = "lower is better" if lower_good else "higher is better"
    return d, (f"forecast {est} {'above' if est > pv else 'below'} previous {pv} ({rule}): "
               f"{'good' if good else 'bad'} for {currency}, so {pair} {d}")


@dataclass(frozen=True)
class NewsWindow:
    release_utc: datetime
    country: str
    currency: str
    event: str
    no_new_trades_from: datetime
    no_new_trades_until: datetime
    close_open_trades_at: datetime
    direction: str
    direction_reason: str
    estimate: Any
    prev: Any


def events(settings: Any) -> list[dict]:
    return read_store(settings)["events"]


def big_news_windows(settings: Any, pair: str, start: datetime, end: datetime,
                     calendar: list[dict] | None = None) -> list[NewsWindow]:
    """Every BIG release in a currency of `pair` whose no-trading window touches [start, end)."""
    n = settings.news
    before = timedelta(minutes=n.big_news_no_new_trades_before_minutes)
    after = timedelta(minutes=n.big_news_no_new_trades_after_minutes)
    close = timedelta(minutes=n.big_news_close_trades_before_minutes)
    currencies = {pair[:3], pair[3:]}
    cal = calendar if calendar is not None else events(settings)
    same_day: dict = {}
    for e in cal:
        same_day.setdefault((e["time_utc"][:10], currency_of(settings, e["country"])), []).append(e["event"])
    rows, unmatched = table(), UnmatchedLog(settings)
    out = []
    for e in cal:
        cur = currency_of(settings, e["country"])
        if cur not in currencies:
            continue
        m = classify(rows, settings, cur, e["event"], e.get("impact"), same_day[(e["time_utc"][:10], cur)])
        if m.rule == "default_small":
            unmatched.note(cur, e["event"], e["time_utc"])
        if m.tier != BIG:
            continue
        t = _t(e["time_utc"])
        if t - before >= end or t + after <= start:
            continue
        d, why = expected_direction(settings, pair, cur, e["event"], e.get("estimate"), e.get("prev"))
        out.append(NewsWindow(t, e["country"], cur, e["event"], t - before, t + after, t - close, d, why,
                              e.get("estimate"), e.get("prev")))
    return sorted(out, key=lambda w: (w.release_utc, w.event))


def no_new_trades(settings: Any, pair: str, t: datetime, calendar: list[dict] | None = None) -> list[NewsWindow]:
    """The BIG releases that stop new trades at time t (empty: news does not stop them)."""
    return [w for w in big_news_windows(settings, pair, t - timedelta(days=1), t + timedelta(days=1), calendar)
            if w.no_new_trades_from <= t < w.no_new_trades_until]


def close_open_trades(settings: Any, pair: str, t: datetime, calendar: list[dict] | None = None) -> list[NewsWindow]:
    """The BIG releases for which open trades must be closed at t (from close time until the release)."""
    return [w for w in big_news_windows(settings, pair, t - timedelta(days=1), t + timedelta(days=1), calendar)
            if w.close_open_trades_at <= t < w.release_utc]


def expected_directions(settings: Any, pair: str, day_start: datetime, day_end: datetime,
                        calendar: list[dict] | None = None) -> list[NewsWindow]:
    """Section 2.4: each BIG release of the day with its expected direction."""
    return [w for w in big_news_windows(settings, pair, day_start, day_end, calendar)
            if day_start <= w.release_utc < day_end]


@dataclass(frozen=True)
class TimeDirection:
    """The expected direction for one release time (design section 2.4)."""
    release_utc: datetime
    direction: str
    reason: str
    deciding: tuple[str, ...]          # the release(s) that decided
    releases: tuple[NewsWindow, ...]   # every big release at that time


def time_direction(windows: list[NewsWindow], path=None) -> TimeDirection:
    """The big releases at ONE time: if their expected directions all agree, that direction;
    if they disagree, the headline release decides (the news table's [[headline]] order: a rate
    decision over everything else, main payrolls over private payrolls, headline CPI over core
    CPI). If the headline release has no expected direction, there is none for that time; if
    several releases share the top place and do not agree, there is none either."""
    from news.table import TABLE_PATH
    t = windows[0].release_utc
    dirs = {w.direction for w in windows}
    if len(dirs) == 1:
        d = windows[0].direction
        why = (windows[0].direction_reason if len(windows) == 1
               else f"all {len(windows)} big releases agree: {d}")
        return TimeDirection(t, d, why, tuple(w.event for w in windows), tuple(windows))
    order = load_headline(path or TABLE_PATH)
    ranked = [(headline_rank(order, w.event), w) for w in windows]
    top = min(r for (r, _), _ in ranked)
    lead = [w for (r, _), w in ranked if r == top]
    lead_name = next(n for (r, n), _ in ranked if r == top)
    others = [w for (r, _), w in ranked if r != top]
    names = ", ".join(w.event for w in lead)
    rest = ", ".join(f"{w.event} ({w.direction})" for w in others) or "none"
    lead_dirs = {w.direction for w in lead}
    if len(lead_dirs) > 1:
        return TimeDirection(t, NO_DIRECTION, f"the headline releases ({lead_name}: " + ", ".join(
            f"{w.event} {w.direction}" for w in lead) + ") do not agree", tuple(w.event for w in lead), tuple(windows))
    d = lead[0].direction
    if d == NO_DIRECTION:
        return TimeDirection(t, NO_DIRECTION, f"the headline release ({lead_name}: {names}) has no expected "
                             f"direction; the others ({rest}) do not decide", tuple(w.event for w in lead), tuple(windows))
    return TimeDirection(t, d, f"the big releases disagree; the headline release decides ({lead_name}: {names}, "
                         f"{d}) over {rest}", tuple(w.event for w in lead), tuple(windows))


def time_directions(settings: Any, pair: str, start: datetime, end: datetime,
                    calendar: list[dict] | None = None) -> list[TimeDirection]:
    """Section 2.4: the expected direction for each time with big releases, from start to end."""
    groups: dict = {}
    for w in big_news_windows(settings, pair, start, end, calendar):
        if start <= w.release_utc < end:
            groups.setdefault(w.release_utc, []).append(w)
    return [time_direction(ws) for _, ws in sorted(groups.items())]


@dataclass(frozen=True)
class CalendarStatus:
    ok: bool
    why: str


def status(settings: Any, now: datetime) -> CalendarStatus:
    data = read_store(settings)
    last = data.get("last_fetch_utc")
    if not last:
        return CalendarStatus(False, "the economic calendar has never been fetched"
                              + (f" (last attempt: {data['last_error']})" if data.get("last_error") else ""))
    age = now - _t(last)
    if age > timedelta(hours=settings.news.out_of_date_hours):
        return CalendarStatus(False, f"the economic calendar is out of date: last fetched {last} "
                                     f"({int(age.total_seconds() // 3600)} hours ago)"
                              + (f"; last attempt: {data['last_error']}" if data.get("last_error") else ""))
    return CalendarStatus(True, f"fetched {last}")
