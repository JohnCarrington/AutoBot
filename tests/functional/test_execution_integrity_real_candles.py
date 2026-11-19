"""Functional test on the REAL candles of Wednesday 18 November 2026 (owner's investigation brief, 19 November 2026),
with the switches the live service ran with after 13:35 (research/analyser_control_days.settings_with: the live
.env's switches, analyser control on):

  * 19:50 level reversal sell (live, 13135.7 at 19:50:58, bid 13135.6): the specification (docs/DESIGN.md 3.6
    rule 3, docs/REJECTION.md bounce step 4) opens the sell as soon as the live price breaks the confirmation
    candle's low. The forming 19:50 candle as it stood at 19:50:58 (through 13135.7, not yet above the reversal
    candle's high 13139.2) gives the idea, allowed; the same candle once it had also gone above 13139.2 does
    not; the finished candle (O 13136.5 H 13139.9 L 13135.6) counts as cancelled (docs/REJECTION.md, "With
    stored candles"), as live and in the replay. The confirmation needs a finished candle: the forming 19:45
    candle gives no entry.
  * 15:45:00: the 15:45 candle's first live price came before IG's finished 15:40 candle was stored. The live
    check waits for it (strategies/replay.py waiting_for_finished_candle); without the wait the copies, given
    15:45 straight after 15:35, give the 15:40 breakout sell again (live: refused only because the first was open).
  * A restart during the 19:50 candle (the week replayed to 19:50 from the store) gives the same live check.
Reads the candle store only; never contacts IG."""

import tempfile
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path

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
T1945 = datetime(2026, 11, 18, 19, 45, tzinfo=UTC)
T1950 = datetime(2026, 11, 18, 19, 50, tzinfo=UTC)


def live_settings():
    from research.analyser_control_days import settings_with
    with tempfile.TemporaryDirectory() as tmp:
        return settings_with(True, Path(tmp))


def forming(t, o, h, lo, c, spread="1.5"):
    """The 5-minute candle forming at `t` as far as the live prices had gone (sell prices given)."""
    o, h, lo, c = (D(x) for x in (o, h, lo, c))
    sp = D(spread)
    return Candle("5m", t, t + FIVE, o + sp, h + sp, lo + sp, c + sp, o, h, lo, c)


def lr(ideas):
    return [(i.direction, i.entry_price, i.allowed) for i in ideas if i.strategy == "level reversal"]


@pytest.fixture(scope="module")
def day():
    s = live_settings()
    store = CandleStore(s.candles.folder, s.candles.compress_after_days)
    memo = MemoStore(store)
    tracker = StateTracker(s, memo)
    tracker.replay(T1540)                                   # the finished candles up to 15:35
    runner = StrategyRunner(s, memo, tracker)               # live: the hourly read again for each candle
    runner.step()
    return s, store, memo, tracker, runner


def test_18_november_the_live_check_at_the_candle_turn_and_the_1950_level_reversal(day, monkeypatch):
    s, store, memo, tracker, runner = day
    real = {c.start: c for c in store.read_range("5m", T1540, T1950 + 2 * FIVE)}

    # ---- 15:45:00: the 15:40 candle not stored yet ----------------------------------------------------------
    o = str(real[T1540 + FIVE].sell_open)
    first_price = forming(T1540 + FIVE, o, o, o, o)
    assert runner.peek(first_price) == []                   # waits for the finished 15:40 candle
    with monkeypatch.context() as m:                        # the defect, without the wait
        m.setattr(StrategyRunner, "waiting_for_finished_candle", lambda self, start: False)
        stale = [(i.strategy, i.direction) for i in runner.peek(first_price)]
    assert ("breakout", "sell") in stale                    # the 15:40 breakout given again at 15:45:00
    tracker.advance(T1540 + FIVE)                           # IG's 15:40 candle stored and taken
    done = [(i.strategy, i.direction) for c, i in runner.step() if c.start == T1540]
    assert ("breakout", "sell") in done                     # the breakout belongs to the 15:40 candle ...
    assert ("breakout", "sell") not in [(i.strategy, i.direction) for i in runner.peek(first_price)]  # ... only

    # ---- up to 19:45; the confirmation candle needs to finish ---------------------------------------------------
    tracker.advance(T1945)
    runner.step()
    c45 = real[T1945]
    assert (c45.sell_open, c45.sell_high, c45.sell_low, c45.sell_close) == (
        D("13137.8"), D("13138.5"), D("13135.7"), D("13135.9"))
    assert lr(runner.peek(c45)) == []                       # confirmed at its close; the entry comes after
    tracker.advance(T1950)
    runner.step()

    # ---- 19:50: the live entry and the finished candle ------------------------------------------------------
    at_195058 = forming(T1950, "13136.5", "13136.5", "13135.6", "13135.6")   # bid 13135.6 at 19:50:58
    assert lr(runner.peek(at_195058)) == [("sell", D("13135.7"), True)]
    highest_still = forming(T1950, "13136.5", "13139.2", "13135.6", "13135.6")  # up to the reversal high, not above
    assert lr(runner.peek(highest_still)) == [("sell", D("13135.7"), True)]
    above_first = forming(T1950, "13136.5", "13139.9", "13136.0", "13139.5")   # above 13139.2 before the break
    assert lr(runner.peek(above_first)) == []
    above_first_then_down = forming(T1950, "13136.5", "13139.9", "13135.6", "13135.6")
    assert lr(runner.peek(above_first_then_down)) == []    # both: the order unknown from the candle, cancelled
    finished = real[T1950]
    assert (finished.sell_open, finished.sell_high, finished.sell_low) == (D("13136.5"), D("13139.9"), D("13135.6"))
    assert lr(runner.peek(finished)) == []
    tracker.advance(T1950 + FIVE)
    assert lr([i for c, i in runner.step() if c.start == T1950]) == []   # the candle close: no idea, as live


def test_a_restart_during_the_1950_candle_gives_the_same_live_check():
    s = live_settings()
    store = CandleStore(s.candles.folder, s.candles.compress_after_days)
    memo = MemoStore(store)
    tracker = StateTracker(s, memo)
    tracker.replay(T1950)                                   # started again at 19:50:30: the week from the store
    runner = StrategyRunner(s, memo, tracker)
    runner.step()
    at_195058 = forming(T1950, "13136.5", "13136.5", "13135.6", "13135.6")
    assert lr(runner.peek(at_195058)) == [("sell", D("13135.7"), True)]
    ideas = runner.peek(at_195058)
    lr_idea = next(i for i in ideas if i.strategy == "level reversal")
    assert "S2 13140.2" in " ".join(lr_idea.steps)
