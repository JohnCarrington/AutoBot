"""Runs the four strategies over stored candles, as they would have run live,
and turns what they find into ideas (or blocked candidates, with the reason).
Reads the candle store only; never contacts IG; places nothing.

The week is replayed from its open, exactly as the analyser does (so the
market state at each moment is the one the service would have had). At each
5-minute candle:
  * "the current state" is the analyser's state after the previous finished
    candle (the state the strategy would see while this candle forms);
  * each strategy is given the candle; when its entry price is reached, the
    candidate is checked (strategies/common.py: switch, state, direction rule).
With stored candles there are no ticks, so an entry is shown at the start of
the candle it was reached in.
"""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from typing import Any

from analyser.indicators import last_candles
from analyser.market_state import MemoStore, StateTracker
from analyser.states import CONSOLIDATION, NONE
from config.pairs import check_same_pair
from levels.current import build
from levels.rules import PIVOT
from prices.indicators import ema
from prices.store import CandleStore
from strategies.bollinger_bounce.strategy import candidates as bounce_candidates
from strategies.common import Idea, check
from strategies.ema_pullback.strategy import EmaPullback, HourlyTrendReader
from strategies.range_trade.strategy import candidates as range_candidates
from strategies.slow_grind.strategy import SlowGrind


def replay(settings: Any, store: CandleStore, start: datetime, end: datetime) -> list[Idea]:
    check_same_pair(settings, store)
    memo = MemoStore(store)
    tracker = StateTracker(settings, memo)
    tracker.replay(end)
    hist = tracker.history
    if not hist:
        return []
    side = settings.chart.price
    week = [h[0].candle for h in hist]
    warm = last_candles(memo, "5m", tracker.week_open, settings.market_states.indicator_warm_up_candles)
    allc = warm + week
    sg, ep = settings.slow_grind, settings.ema_pullback
    sg_ema = ema(allc, side, sg.ema_periods)
    fast, slow = ema(allc, side, ep.fast_ema_periods), ema(allc, side, ep.slow_ema_periods)
    ema100 = ema(allc, side, settings.analyser.direction_ema_periods)
    hourly = HourlyTrendReader(settings, last_candles(memo, "1h", end, ep.hourly_history_candles))
    grind, pullback = SlowGrind(settings), EmaPullback(settings, hourly)
    changes = tracker.changes
    ideas: list[Idea] = []
    prev = None
    for f, _state, _direction, events, _moved, _sp in hist:
        c = f.candle
        cands = (grind.on_candle(c, sg_ema.get(c.start))
                 + pullback.on_candle(c, fast.get(c.start), slow.get(c.start))
                 + bounce_candidates(tracker.watcher, events) + range_candidates(tracker.watcher, events))
        if cands and start <= c.start < end:
            before = [ch for ch in changes if prev is not None and ch.time <= prev.start]
            st = (SimpleNamespace(state=before[-1].state, direction=before[-1].direction,
                                  trend_type=before[-1].trend_type) if before
                  else SimpleNamespace(state=CONSOLIDATION, direction=NONE, trend_type=None))
            pivots = [lv.price for lv in build(settings, memo, c.start).levels if lv.type == PIVOT]
            e100 = ema100.get(prev.start) if prev is not None else None
            for cand in cands:
                ideas.append(check(settings, settings.market.pair, cand, st, pivots[0] if pivots else None, e100))
        prev = c
    return ideas
