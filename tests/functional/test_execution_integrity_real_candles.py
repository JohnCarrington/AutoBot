"""Functional test on the REAL candles of Wednesday 18 November 2026 of the live-check fix of 19 November 2026
(StrategyRunner.waiting_for_finished_candle), as kept in first-build-plus (owner, 19 November 2026).

At each candle's turn IG's live prices arrive before its finished candle is stored (18 November, 15:45:00). The live
check must give nothing until the candle before the forming one has been taken, and then check as usual. (On main this
file also checks the 19:50 level reversal of 18 November; that trade came from main's analyser, which first-build-plus
does not have, so those checks are not here.) Reads the candle store only; never contacts IG."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal as D

import pytest

from analyser.market_state import MemoStore, StateTracker
from config.settings_loader import load_settings
from prices.model import Candle
from prices.store import CandleStore
from strategies.replay import StrategyRunner

SETTINGS = load_settings().for_pair("GBPUSD")
UTC = timezone.utc
FIVE = timedelta(minutes=5)
pytestmark = pytest.mark.skipif(not (SETTINGS.candles.folder / "5m").is_dir(),
                                reason="the real candle store is only on the server")
T1540 = datetime(2026, 11, 18, 15, 40, tzinfo=UTC)


def first_price(t, price):
    p = D(str(price))
    return Candle("5m", t, t + FIVE, p + D("1.5"), p + D("1.5"), p + D("1.5"), p + D("1.5"), p, p, p, p)


def test_18_november_the_live_check_waits_for_the_finished_candle_at_the_candle_turn(pretend_switches):
    s = load_settings(switches_from=pretend_switches).for_pair("GBPUSD")
    store = CandleStore(s.candles.folder, s.candles.compress_after_days)
    memo = MemoStore(store)
    tracker = StateTracker(s, memo)
    tracker.replay(T1540)                                   # the finished candles up to 15:35
    runner = StrategyRunner(s, memo, tracker)
    runner.step()
    real = {c.start: c for c in store.read_range("5m", T1540, T1540 + 2 * FIVE)}
    first = first_price(T1540 + FIVE, real[T1540 + FIVE].sell_open)
    assert runner.waiting_for_finished_candle(first.start)
    assert runner.peek(first) == []                         # 15:45:00: the 15:40 candle not stored yet
    tracker.advance(T1540 + FIVE)                           # IG's 15:40 candle stored and taken
    runner.step()
    assert not runner.waiting_for_finished_candle(first.start)
    runner.peek(first)                                      # checks as usual now (whatever it finds)
