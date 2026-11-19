"""Functional tests for TREND_IGNORES_HOURLY_READ (owner, 19 November 2026), on the REAL candles in the candle store
(stored candles are never overwritten, so the answers do not change), with the live switches of 19 November 2026
(research/analyser_control_days.py BASE_SWITCHES, the analyser control and stage 4 on).

The owner's decision: the hourly read must no longer decide anything for the slow grind and the EMA pullback; the
analyser alone decides whether and which way they trade. The EMA pullback's own hourly 8/13/20 EMA test (its step 0)
stays exactly as it is. Everything else, including the hourly read's use by the breakout and by the reversal group,
stays as it is. These tests check only that the code does what the owner said; they judge nothing on profit.

  a. The switch is on if left out of .env.
  b. Check 4 (HOURLY_READ): on Thursday 19 November 2026 at 08:05 UK the real hourly read is a sell-off; with the switch
     on, it no longer stops a slow grind or EMA pullback buy; with it off, it does (as before); the breakout still
     follows it.
  c. Check 7's hourly-ranging rule (ANALYSER_GOVERNS_ALL): on Wednesday 18 November 2026 at 07:25 UK the real hourly read
     is ranging; with the switch on, it no longer stops the slow grind or the EMA pullback; the breakout and the
     reversal group keep it.
  d. The replay of Thursday 19 November 2026, 06:00 to 09:30 UK: with the switch on, no slow grind or EMA pullback idea
     is refused by the hourly read; the 07:55 and 08:10 slow grind buys, refused live only by the hourly sell-off, are
     allowed; with the switch off they are refused as they were live.
  e. The EMA pullback's own hourly EMA test still applies: on 19 November from 07:00 the hourly 8/13/20 EMAs are not in
     order, so it makes no buy setup with the switch on either, and its notes are the same with the switch on and off.
"""

import tempfile
from datetime import date, datetime, timezone
from decimal import Decimal as D
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

import pytest

from analyser.hourly_read import RANGING as HOURLY_RANGING, SELL_OFF, HourlyReader
from analyser.indicators import last_candles
from analyser.states import DOWN, RANGING, TREND, UP
from config.settings_loader import load_settings
from prices.store import CandleStore
from research.analyser_control_days import UK, ideas_day, settings_with
from strategies.common import (BREAKOUT, BUY, EMA_PULLBACK, LEVEL_REVERSAL, SELL, SLOW_GRIND, allowed,
                               ignores_hourly_read)

BASE = load_settings().for_pair("GBPUSD")
pytestmark = pytest.mark.skipif(not (BASE.candles.folder / "5m").is_dir(),
                                reason="the real candle store is only on the server")

STAGE_4 = {"SCALE_OUT_REVERSAL": "on", "TRAIL_NO_LOSS": "on", "LR_ENTRY_NEAR_LEVEL": "on", "LEVEL_STOPS": "on"}
THURSDAY, WEDNESDAY = date(2026, 11, 19), date(2026, 11, 18)


def settings(**extra):
    with tempfile.TemporaryDirectory() as tmp:
        return settings_with(True, Path(tmp), **(STAGE_4 | extra))


ON, OFF = settings(TREND_IGNORES_HOURLY_READ="on"), settings(TREND_IGNORES_HOURLY_READ="off")


def hourly_read(t: datetime):
    """The real hourly read at `t`, as the strategies see it (strategies/replay.py)."""
    store = CandleStore(BASE.candles.folder, BASE.candles.compress_after_days)
    return HourlyReader(BASE, last_candles(store, "1h", t, BASE.hourly_read.history_candles)).at(t)


SELL_OFF_READ = hourly_read(datetime(2026, 11, 19, 8, 5, tzinfo=timezone.utc))      # Thursday 08:05 UK
RANGING_READ = hourly_read(datetime(2026, 11, 18, 7, 25, tzinfo=timezone.utc))      # Wednesday 07:25 UK
TREND_UP = SimpleNamespace(state=TREND, direction=UP, trend_type="slow grind")
TREND_DOWN = SimpleNamespace(state=TREND, direction=DOWN, trend_type="slow grind")


def hourly_reasons_in(reasons: list) -> list:
    return [r for r in reasons if "hourly chart" in r]


# ---- a. the switch ---------------------------------------------------------------------------------------------

def test_the_switch_is_on_if_left_out_and_can_be_switched_off():
    assert settings().switches.trend_ignores_hourly_read is True          # BASE_SWITCHES leave it out
    assert ON.switches.trend_ignores_hourly_read is True
    assert OFF.switches.trend_ignores_hourly_read is False
    assert ignores_hourly_read(ON, SLOW_GRIND) and ignores_hourly_read(ON, EMA_PULLBACK)
    assert not ignores_hourly_read(ON, BREAKOUT) and not ignores_hourly_read(OFF, SLOW_GRIND)


# ---- b. check 4 on the real 19 November sell-off -----------------------------------------------------------------

def test_the_real_read_on_thursday_morning_is_a_sell_off():
    assert SELL_OFF_READ.state == SELL_OFF
    assert "03:00 GMT hourly candle closed at 13125.2" in SELL_OFF_READ.why


@pytest.mark.parametrize("strategy", [SLOW_GRIND, EMA_PULLBACK])
def test_check_4_no_longer_stops_slow_grind_and_ema_pullback_buys(strategy):
    # a buy above the pivot (13162.5) and the 100 EMA, so the direction rule (EMA pullback) has nothing to say
    args = (D("13170"), TREND_UP, D("13162.5"), D("13139.2"), SELL_OFF_READ)
    on, _ = allowed(ON, strategy, BUY, *args)
    off, _ = allowed(OFF, strategy, BUY, *args)
    assert on == []
    assert off == [f"the hourly chart is in a sell-off: {strategy} only sells"]


def test_check_4_still_applies_to_the_breakout():
    args = (D("13170"), TREND_UP, D("13162.5"), D("13139.2"), SELL_OFF_READ)
    on, _ = allowed(ON, BREAKOUT, BUY, *args)
    assert on == ["the hourly chart is in a sell-off: breakout only sells"]


# ---- c. check 7's hourly-ranging rule on the real 18 November ranging read -------------------------------------------

def test_the_real_read_on_wednesday_at_07_25_is_ranging():
    assert RANGING_READ.state == HOURLY_RANGING
    assert (RANGING_READ.low, RANGING_READ.high) == (D("13186.8"), D("13219.6"))


@pytest.mark.parametrize("strategy", [SLOW_GRIND, EMA_PULLBACK])
def test_the_hourly_ranging_rules_no_longer_stop_slow_grind_and_ema_pullback(strategy):
    # a sell in a trend down, below the pivot (13200.1) and the 100 EMA (13195.4), as on 18 November at 07:30
    args = (D("13179.8"), TREND_DOWN, D("13200.1"), D("13195.4"), RANGING_READ)
    on, _ = allowed(ON, strategy, SELL, *args)
    off, _ = allowed(OFF, strategy, SELL, *args)
    assert on == []
    assert any(r.startswith("ANALYSER_GOVERNS_ALL: the hourly chart is ranging (13186.8 to 13219.6)") for r in off)
    assert any(r.startswith("the hourly chart is ranging (13186.8 to 13219.6)") for r in off)


def test_the_breakout_and_the_reversal_group_keep_the_hourly_ranging_rules():
    args = (D("13179.8"), TREND_DOWN, D("13200.1"), D("13195.4"), RANGING_READ)
    on, _ = allowed(ON, BREAKOUT, SELL, *args)
    assert any(r.startswith("ANALYSER_GOVERNS_ALL: the hourly chart is ranging") for r in on)
    assert any(r.startswith("the hourly chart is ranging") for r in on)
    ranging = SimpleNamespace(state=RANGING, direction="none", trend_type=None)
    middle = {"furthest": D("13200"), "rejection_close": D("13199")}       # the middle of the hourly range
    on, _ = allowed(ON, LEVEL_REVERSAL, SELL, D("13199"), ranging, D("13200.1"), D("13195.4"), RANGING_READ,
                    context=middle)
    assert any("a sell opens only at the top edge" in r for r in on)


# ---- d. and e. the replay of Thursday 19 November 2026, 06:00 to 09:30 UK ------------------------------------------

A, B = datetime(2026, 11, 19, 6, 0, tzinfo=timezone.utc), datetime(2026, 11, 19, 9, 30, tzinfo=timezone.utc)


@lru_cache(maxsize=None)
def thursday(switch: str):
    return ideas_day(THURSDAY, True, **STAGE_4, TREND_IGNORES_HOURLY_READ=switch)


def trend_ideas(switch: str) -> dict:
    _, ideas, _ = thursday(switch)
    return {(i.time.astimezone(UK).strftime("%H:%M"), i.strategy, i.direction): i for i in ideas
            if A <= i.time <= B and i.strategy in (SLOW_GRIND, EMA_PULLBACK)}


def test_with_the_switch_on_no_slow_grind_or_ema_pullback_idea_is_refused_by_the_hourly_read():
    ideas = trend_ideas("on")
    assert ideas, "the slow grind made ideas that morning"
    assert all("hourly chart" not in i.blocked_by for i in ideas.values())


def test_the_slow_grind_buys_refused_only_by_the_hourly_sell_off_are_now_allowed():
    on, off = trend_ideas("on"), trend_ideas("off")
    for key in (("07:55", SLOW_GRIND, BUY), ("08:10", SLOW_GRIND, BUY)):
        assert off[key].blocked_by == "the hourly chart is in a sell-off: slow grind only sells"
        assert on[key].allowed, on[key].blocked_by


def test_the_same_setups_are_found_with_the_switch_on_and_off():
    """The switch changes only the entry checks, never which setups the strategies find."""
    assert set(trend_ideas("on")) == set(trend_ideas("off"))


def test_the_ema_pullback_hourly_ema_test_still_applies():
    _, _, runner = thursday("on")
    for hour in (7, 8, 9):
        trend = runner.pullback.hourly.at(datetime(2026, 11, 19, hour, 0, tzinfo=timezone.utc))
        assert trend.direction is None and not trend.qualified
        assert trend.why.startswith("hourly EMAs not in order and all moving one way")
    assert not [k for k in trend_ideas("on") if k[1] == EMA_PULLBACK]
    on = [n for n in runner.pullback.notes if A <= n[0] <= B]
    off = [n for n in thursday("off")[2].pullback.notes if A <= n[0] <= B]
    assert on == off and on                                     # the 06:00 hour's sell touches, cancelled the same way
