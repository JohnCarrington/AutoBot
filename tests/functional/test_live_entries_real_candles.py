"""Functional test of the live entries on the REAL candles: the live check (StrategyRunner.peek, the strategies'
copies given the forming candle) gives exactly the ideas the strategies give when that candle finishes, and never
changes the strategies. Reads the candle store only."""

from datetime import datetime, timedelta, timezone

import pytest

from analyser.market_state import MemoStore, StateTracker
from config.settings_loader import load_settings
from prices.store import CandleStore
from strategies.replay import StrategyRunner

SETTINGS = load_settings().for_pair("GBPUSD")
UTC = timezone.utc
pytestmark = pytest.mark.skipif(not (SETTINGS.candles.folder / "5m").is_dir(),
                                reason="the real candle store is only on the server")


def key(i):
    return (i.strategy, i.direction, i.entry_price, i.allowed)


def test_the_live_check_gives_the_same_ideas_as_the_finished_candle_and_changes_nothing(pretend_switches):
    s = load_settings(switches_from=pretend_switches).for_pair("GBPUSD")
    store = CandleStore(s.candles.folder, s.candles.compress_after_days)
    memo = MemoStore(store)
    start = datetime(2026, 11, 2, 6, 0, tzinfo=UTC)
    end = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)
    tracker = StateTracker(s, memo)
    tracker.replay(start)
    runner = StrategyRunner(s, memo, tracker, hourly_end=end)
    runner.step()
    seen = 0
    for c in store.read_range("5m", start, end):
        live = sorted(key(i) for i in runner.peek(c))           # the whole candle, before the strategies take it
        again = sorted(key(i) for i in runner.peek(c))          # peeking twice changes nothing
        tracker.advance(c.end)
        done = sorted(key(i) for cc, i in runner.step() if cc.start == c.start)
        assert live == again == done, c.start
        seen += len(done)
    assert seen > 0                                             # the morning has ideas to compare
