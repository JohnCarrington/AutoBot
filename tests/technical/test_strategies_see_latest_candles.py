"""The strategies always see the latest candles and levels, exactly as the analyser does (owner, 11 November 2026).

The live service runs for days. The strategies (StrategyRunner, given the engine's candle store) used to keep one
MemoStore made at start-up: a day's file stayed as it was when first read, and a day's file that did not exist yet
was never seen. After the restart at 12:26 on Monday 9 November the EMA pullback's hourly trend stayed frozen at
Monday 11:00 for all of Tuesday, and the levels the bounce, range trade and level reversal are built on stopped
changing. These tests write new candles to a real store on disk after the strategies have started, as the price
service does, and check that the very next step sees them."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from analyser.market_state import MemoStore
from config.settings_loader import load_settings
from levels.current import build
from prices.model import Candle
from prices.store import CandleStore
import strategies.replay as SR
from strategies.replay import StrategyRunner

UTC = timezone.utc
WEEK_OPEN = datetime(2026, 11, 8, 22, 0, tzinfo=UTC)      # Sunday 8 November 22:00 UTC
TUE = datetime(2026, 11, 10, 0, 0, tzinfo=UTC)
WED = datetime(2026, 11, 11, 0, 0, tzinfo=UTC)


def candle(tf, start, minutes, price="13300.0", parts=1, expected=1):
    p = D(price)
    return Candle(tf, start, start + timedelta(minutes=minutes), p + D("1.5"), p + D("3.5"), p + D("0.5"), p + D("2.0"),
                  p, p + D("2"), p - D("1"), p + D("0.5"), parts, expected)


class Tracker:
    """The analyser's side as the runner reads it: the week's candles taken so far, each with its band."""

    def __init__(self):
        self.week_open, self.history, self.changes = WEEK_OPEN, [], []

    def take(self, c):
        self.history.append((SimpleNamespace(candle=c, middle=D("13300"), upper=D("13310"), lower=D("13290")),))


@pytest.fixture
def setup(pretend_switches, tmp_path):
    s = load_settings(switches_from=pretend_switches).for_pair("GBPUSD")
    store = CandleStore(tmp_path / "GBPUSD", s.candles.compress_after_days)
    # Tuesday's hourly candles: enough for the EMA pullback's hourly EMAs
    for h in range(24):
        store.add(candle("1h", TUE + timedelta(hours=h), 60, price=str(13250 + 2 * h), parts=12, expected=12))
    return s, store


def runner_as_the_engine_made_it(s, store, tracker):
    """Before the fix the engine gave the runner ONE MemoStore made at start-up; the runner must not keep it."""
    return StrategyRunner(s, MemoStore(store), tracker)


def test_the_hourly_trend_sees_a_new_days_hourly_candle_written_after_start_up(setup):
    s, store = setup
    tracker = Tracker()
    runner = runner_as_the_engine_made_it(s, store, tracker)
    first = candle("5m", WED, 5)                             # Wednesday 00:00: no Wednesday hourly file yet
    store.add(first)
    tracker.take(first)
    runner.step()
    assert runner.pullback.hourly.candles[-1].start == TUE + timedelta(hours=23)
    # the price service writes Wednesday's first hourly candle (a new day file) and the next 5-minute candles
    store.add(candle("1h", WED, 60, price="13300", parts=12, expected=12))
    for k in range(1, 13):
        c = candle("5m", WED + timedelta(minutes=5 * k), 5)
        store.add(c)
        tracker.take(c)
    runner.step()
    assert runner.pullback.hourly.candles[-1].start == WED, "the hourly trend did not see Wednesday's hourly candle"


def test_the_levels_see_a_daily_candle_stored_after_they_were_first_read(setup, monkeypatch):
    s, store = setup
    tracker = Tracker()
    runner = runner_as_the_engine_made_it(s, store, tracker)
    given = []
    real = SR.build

    def watch(settings, memo, t):
        got = real(settings, memo, t)
        given.append((t, got))
        return got
    monkeypatch.setattr(SR, "build", watch)
    first = candle("5m", WED, 5)
    store.add(first)
    tracker.take(first)
    runner.step()                                            # Tuesday's daily candle is not stored yet
    assert not [lv for lv in given[-1][1].levels if lv.type == "pivot"]
    # the price service stores Tuesday's daily candle, then the next 5-minute candle
    store.add(candle("1d", TUE, 24 * 60, price="13260", parts=288, expected=288))
    nxt = candle("5m", WED + timedelta(minutes=5), 5)
    store.add(nxt)
    tracker.take(nxt)
    runner.step()
    t, levels = given[-1]
    assert t == nxt.start
    assert [lv for lv in levels.levels if lv.type == "pivot"], "the levels did not see Tuesday's daily candle"
    assert runner.pivot_at(nxt.start) is not None
    # exactly what the analyser builds: the store read afresh at that moment
    fresh = build(s, CandleStore(store.folder, store.compress_after_days), nxt.start)
    assert [(lv.type, lv.price) for lv in levels.levels] == [(lv.type, lv.price) for lv in fresh.levels]


def test_the_live_check_never_keeps_a_pivot_worked_out_before_the_candle_finished(setup):
    s, store = setup
    tracker = Tracker()
    runner = runner_as_the_engine_made_it(s, store, tracker)
    first = candle("5m", WED, 5)
    store.add(first)
    tracker.take(first)
    runner.step()
    forming = candle("5m", WED + timedelta(minutes=5), 5)
    runner.peek(forming)                                     # Tuesday's daily candle not stored yet: no pivot
    store.add(candle("1d", TUE, 24 * 60, price="13260", parts=288, expected=288))
    store.add(forming)
    tracker.take(forming)
    runner.step()
    assert runner.pivot_at(forming.start) is not None
