"""Replay check for the trade manager: over Monday 26 October to Friday 6 November 2026, through the bot's own
code (the strategies' replay, the safety rules' hours and limits, the trade manager's exits), every trade must
close at the same time and price as in docs/research/all_strategies_together_20261108.md ("Every trade").
It checks the trade manager against that earlier research, so it keeps the safety rules as they were then
(its own copy of the hours and limits): the one view at a time rules (design 6, 9 November 2026) are checked by
`python -m trading.replay_check` instead.
Reads the candle store and the calendar; contacts nobody; places nothing; writes nothing.

    .venv/bin/python -m trade_manager.replay_check
Exit code 0 when every trade matches, 1 otherwise.
"""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from analyser.market_state import MemoStore, StateTracker
from analyser.trend_day import trend_day_at
from config.settings_loader import load_or_exit
from prices.calendar import MarketHours
from prices.model import parse_iso
from prices.store import CandleStore
from strategies.common import (BOLLINGER_BOUNCE, BREAKOUT, EMA_PULLBACK, LEVEL_REVERSAL, RANGE_TRADE, SLOW_GRIND,
                               counts_towards_most_at_once, may_open, stop_loss_pips, stop_price)
from strategies.replay import run
from trade_manager.manager import Bar, Rejection, plan, step

UK = ZoneInfo("Europe/London")
RESEARCH = Path(__file__).resolve().parents[1] / "docs" / "research" / "all_strategies_together_20261108.md"
ORDER = [BREAKOUT, SLOW_GRIND, EMA_PULLBACK, BOLLINGER_BOUNCE, RANGE_TRADE, LEVEL_REVERSAL]
WEEKS = ("2026-10-27T12:00:00Z", "2026-11-03T12:00:00Z")


def research_trades() -> Counter:
    """Every trade in the report as (strategy, entry 'Mon 26 Oct 06:00', DIR, closed 'Mon 26 Oct 07:15', pips '-6.0'),
    counted (two trades may share an entry candle)."""
    out, strategy = Counter(), None
    for line in RESEARCH.read_text().splitlines():
        m = re.match(r"### (.+) \(\d+\)$", line)
        if m:
            strategy = m.group(1)
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if strategy and len(cells) == 7 and re.match(r"\w{3} \d\d \w{3} \d\d:\d\d", cells[0]):
            out[(strategy, cells[0], cells[1], cells[4], cells[6])] += 1
    return out


def main() -> int:
    s = load_or_exit().for_pair("GBPUSD")
    off = [k for k in ("slow_grind", "ema_pullback", "bollinger_bounce", "range_trade", "breakout", "level_reversal")
           if not getattr(s.switches, k)]
    if off:
        print(f"The research had all six strategies switched on; these are off in .env: {', '.join(off)}.")
        return 1
    store = CandleStore(s.candles.folder, s.candles.compress_after_days)
    hours = MarketHours(s.market_hours)
    ppp = Decimal(s.market.points_per_pip)
    candles = store.read_range("5m", parse_iso("2026-10-21T00:00:00Z"), parse_iso("2026-11-07T00:00:00Z"))
    index = {c.start: k for k, c in enumerate(candles)}
    ideas, bands, rejections = [], {}, defaultdict(list)
    for w in WEEKS:
        o, c = hours.session(parse_iso(w))
        ideas += [i for i in run(s, store, o, c).ideas if i.allowed]
        tracker = StateTracker(s, MemoStore(store))
        tracker.replay(c)
        for f, *_ in tracker.history:
            if f.upper is not None:
                bands[f.candle.start] = (f.upper, f.lower)
        for e in tracker.watcher.events:
            if e.version == "bounce" and e.kind == "trigger":
                st = tracker.watcher.setups[e.setup - 1]
                lv = [p for p in st.pierced if "Bollinger" not in p["what"]]
                if lv and st.counts:
                    rejections[e.time].append(Rejection(e.direction, e.price, ", ".join(f"{p['what']} {p['price']}" for p in lv)))
    ideas.sort(key=lambda i: (i.time, ORDER.index(i.strategy)))

    def manage(i):
        sell = i.direction == "sell"
        first = candles[index[i.time]]
        fill = i.entry_price if sell else i.entry_price + (first.buy_open - first.sell_open)
        sp = stop_price(s, i)
        stop = ((sp - fill) if sell else (fill - sp)) / ppp if sp is not None else Decimal(stop_loss_pips(s, i.strategy))
        t = plan(s, "r", i.strategy, i.direction, i.time, i.entry_price, fill, stop,
                 trend_day=trend_day_at(s, store, i.time).direction)
        for c in candles[index[i.time]:]:
            prev = candles[index[c.start] - 1]
            step(s, t, Bar.of(c), bands.get(prev.start), rejections.get(c.start, []))
            if not t.open:
                return t, c.start
        return t, candles[-1].start

    taken = []
    for i in ideas:
        if may_open(s, "GBPUSD", i.strategy, i.time):
            continue
        mine = [x for x in taken if x[0].strategy == i.strategy and x[2] > i.time]
        if i.strategy == BOLLINGER_BOUNCE:
            mine = [x for x in mine if x[0].direction == i.direction]
        if i.strategy != EMA_PULLBACK and mine:
            continue
        if counts_towards_most_at_once(i.strategy) and \
                len([x for x in taken if counts_towards_most_at_once(x[0].strategy) and x[2] > i.time]) >= s.limits.max_open_trades:
            continue
        t, closed = manage(i)
        taken.append((i, t, closed))
    want = research_trades()
    got = Counter((i.strategy, f"{i.time.astimezone(UK):%a %d %b %H:%M}", i.direction.upper(),
                   f"{closed.astimezone(UK):%a %d %b %H:%M}", f"{float(t.total_pips()):+.1f}") for i, t, closed in taken)
    same = sum((want & got).values())
    print(f"Research trades: {sum(want.values())}; the trade manager's: {sum(got.values())}; "
          f"same entry, close time and pips: {same}.")
    order = lambda k: (k[0], datetime.strptime("2026 " + k[1], "%Y %a %d %b %H:%M"))  # noqa: E731
    for k in sorted((want - got).elements(), key=order):
        print(f"  only in the research: {k}")
    for k in sorted((got - want).elements(), key=order):
        print(f"  only from the trade manager: {k}")
    return 0 if want == got else 1


if __name__ == "__main__":
    sys.exit(main())
