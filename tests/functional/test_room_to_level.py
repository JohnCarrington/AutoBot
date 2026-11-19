"""Functional tests for ROOM_TO_LEVEL (owner, approved 19 November 2026, with the owner's answer that a level exactly at
the entry price counts as ahead), with the real settings (config/settings.toml) and the switch on unless a test says
otherwise.

The owner's rules:
  1. Only the breakout and the Asian range breakout; every other strategy is unchanged.
  2. Levels: the daily pivot, R1, R2, R3, S1, S2, S3, as the bot already works them out (levels/rules.py).
  3. At the moment the trade would open, the nearest of those levels ahead of the entry price in the trade's direction
     (a buy: above; a sell: below; one exactly at the entry counts), sell price.
  4. Nearer than the strategy's own stop (breakout 6, Asian range breakout 12, as in settings): it does not open, and
     the reason names the level and the distance.
  5. No such level ahead: the trade goes ahead as normal.
  6. ROOM_TO_LEVEL in .env, on if left out.
These tests check only that the code does what the owner said; they judge nothing on profit.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace

import pytest

from analyser.states import DOWN, EMERGING, UP
from config.settings_loader import load_settings
from strategies.common import (ASIAN_RANGE_BREAKOUT, BOLLINGER_BOUNCE, BREAKOUT, BUY, EMA_PULLBACK, LEVEL_REVERSAL,
                               NEW_YORK_OPEN_REVERSAL, RANGE_TRADE, SELL, SESSION_SWEEP, SLOW_GRIND, Candidate, check,
                               room_to_level_context, stop_loss_pips)

UTC = timezone.utc
T = datetime(2026, 11, 19, 7, 55, tzinfo=UTC)


def settings(tmp_path: Path, pretend_switches: Path, room: str | None):
    text = "".join(line + "\n" for line in pretend_switches.read_text().splitlines()
                   if not line.startswith("ROOM_TO_LEVEL="))
    text = text.replace("STRATEGY_BREAKOUT=off", "STRATEGY_BREAKOUT=on").replace(
        "STRATEGY_ASIAN_RANGE_BREAKOUT=off", "STRATEGY_ASIAN_RANGE_BREAKOUT=on")
    if room is not None:
        text += f"ROOM_TO_LEVEL={room}\n"
    env = tmp_path / f"switches_{room}.env"
    env.write_text(text)
    return load_settings(switches_from=env).for_pair("GBPUSD")


@pytest.fixture
def ON(tmp_path, pretend_switches):
    return settings(tmp_path, pretend_switches, "on")


@pytest.fixture
def OFF(tmp_path, pretend_switches):
    return settings(tmp_path, pretend_switches, "off")


def levels(*pairs):
    """A level list like levels.current.LevelList: (type, price) pairs."""
    return SimpleNamespace(levels=[SimpleNamespace(type=t, price=D(str(p))) for t, p in pairs])


DAY = levels(("S3", 13080), ("S2", 13100), ("S1", 13119.1), ("pivot", 13162.5), ("R1", 13180), ("R2", 13200),
             ("R3", 13230), ("round_number", 13160), ("previous_day_high", 13157.5), ("london_session_high", 13158))


def idea(s, strategy, direction, entry, lv=DAY):
    """The candidate as the strategy runner gives it (strategies/replay.py with_room_to_level), checked at entry."""
    ppp = D(s.market.points_per_pip)
    state = SimpleNamespace(state=EMERGING, direction=UP if direction == BUY else DOWN, trend_type=None)
    c = Candidate(strategy, direction, T, D(str(entry)), ["made up"], {})
    c.context.update(room_to_level_context(strategy, direction, c.entry_price, lv, ppp))
    return check(s, "GBPUSD", c, state, None, None)


# ---- rules 2 and 3: which level -----------------------------------------------------------------------------------

@pytest.mark.parametrize("strategy", [BREAKOUT, ASIAN_RANGE_BREAKOUT])
def test_rules_2_and_3_a_buy_takes_the_nearest_pivot_level_above_and_ignores_other_kinds(ON, strategy):
    i = idea(ON, strategy, BUY, 13152.2)        # round number 13160, previous day high 13157.5, London high nearer
    assert i.context["room_level"] == "pivot 13162.5" and i.context["room_pips"] == D("103") / D("10")


@pytest.mark.parametrize("strategy", [BREAKOUT, ASIAN_RANGE_BREAKOUT])
def test_rules_2_and_3_a_sell_takes_the_nearest_pivot_level_below(ON, strategy):
    i = idea(ON, strategy, SELL, 13125)
    assert i.context["room_level"] == "S1 13119.1" and i.context["room_pips"] == D("59") / D("10")


def test_rule_3_a_level_exactly_at_the_entry_counts_at_0_pips(ON):
    i = idea(ON, BREAKOUT, BUY, 13162.5)
    assert i.context["room_level"] == "pivot 13162.5" and i.context["room_pips"] == 0
    assert not i.allowed and "pivot 13162.5 is 0.0 pips above the entry 13162.5" in i.blocked_by


# ---- rule 4: nearer than the strategy's own stop ------------------------------------------------------------------

def test_rule_4_the_stops_are_the_settings_6_and_12(ON):
    assert stop_loss_pips(ON, BREAKOUT) == 6 and stop_loss_pips(ON, ASIAN_RANGE_BREAKOUT) == 12


def test_rule_4_the_asian_range_breakout_buy_with_a_level_10_3_pips_above_is_refused(ON):
    i = idea(ON, ASIAN_RANGE_BREAKOUT, BUY, 13152.2)
    assert not i.allowed
    assert i.blocked_by == "ROOM_TO_LEVEL: pivot 13162.5 is 10.3 pips above the entry 13152.2, less than its 12-pip stop"


def test_rule_4_the_same_distance_is_room_enough_for_the_breakout_with_its_6_pip_stop(ON):
    assert idea(ON, BREAKOUT, BUY, 13152.2).allowed


@pytest.mark.parametrize("strategy,entry,allowed", [(BREAKOUT, 13125.2, True), (BREAKOUT, 13125.1, True),
                                                    (BREAKOUT, 13125.0, False), (ASIAN_RANGE_BREAKOUT, 13131.1, True),
                                                    (ASIAN_RANGE_BREAKOUT, 13131.0, False)])
def test_rule_4_less_than_the_stop_refuses_exactly_the_stop_does_not(ON, strategy, entry, allowed):
    i = idea(ON, strategy, SELL, entry)                       # S1 13119.1 below
    assert i.allowed is allowed, i.blocked_by
    if not allowed:
        assert i.blocked_by.startswith("ROOM_TO_LEVEL: S1 13119.1 is ") and "below the entry" in i.blocked_by


# ---- rule 5: no level ahead -------------------------------------------------------------------------------------

@pytest.mark.parametrize("strategy,direction,entry", [(BREAKOUT, BUY, 13240), (ASIAN_RANGE_BREAKOUT, SELL, 13070)])
def test_rule_5_no_level_ahead_opens_as_normal(ON, strategy, direction, entry):
    i = idea(ON, strategy, direction, entry)
    assert i.context["room_level"] is None and i.allowed


def test_rule_5_no_levels_at_all_opens_as_normal(ON):
    i = idea(ON, ASIAN_RANGE_BREAKOUT, BUY, 13152.2, lv=levels())
    assert i.context == {"room_level": None} and i.allowed


# ---- rule 6: the switch -------------------------------------------------------------------------------------------

def test_rule_6_on_if_left_out_and_off_refuses_nothing(tmp_path, pretend_switches, OFF):
    assert settings(tmp_path, pretend_switches, None).switches.room_to_level is True
    assert OFF.switches.room_to_level is False
    i = idea(OFF, ASIAN_RANGE_BREAKOUT, BUY, 13152.2)
    assert i.allowed and i.context["room_level"] == "pivot 13162.5"          # still recorded


# ---- rule 1: every other strategy unchanged -----------------------------------------------------------------------

@pytest.mark.parametrize("strategy", [SLOW_GRIND, EMA_PULLBACK, BOLLINGER_BOUNCE, RANGE_TRADE, LEVEL_REVERSAL,
                                      SESSION_SWEEP, NEW_YORK_OPEN_REVERSAL])
def test_rule_1_other_strategies_get_no_room_check(ON, strategy):
    assert room_to_level_context(strategy, BUY, D("13162.5"), DAY, D(ON.market.points_per_pip)) == {}


def test_rule_1_every_other_strategy_makes_exactly_the_same_ideas_on_9_and_10_november(tmp_path, pretend_switches):
    from prices.store import CandleStore
    from strategies.replay import run
    text = pretend_switches.read_text()
    for name in ("BREAKOUT", "ASIAN_RANGE_BREAKOUT", "SESSION_SWEEP", "NEW_YORK_OPEN_REVERSAL"):
        text = text.replace(f"STRATEGY_{name}=off", f"STRATEGY_{name}=on")
    text = text.replace("PULLBACK_ENTRY=off", "PULLBACK_ENTRY=on")
    got = {}
    for sw in ("on", "off"):
        env = tmp_path / f"all_{sw}.env"
        env.write_text(text.replace("ROOM_TO_LEVEL=off", f"ROOM_TO_LEVEL={sw}"))
        s = load_settings(switches_from=env).for_pair("GBPUSD")
        if not (s.candles.folder / "5m").is_dir():
            pytest.skip("the real candle store is only on the server")
        store = CandleStore(s.candles.folder, s.candles.compress_after_days)
        start = datetime(2026, 11, 9, 0, 0, tzinfo=UTC)
        got[sw] = run(s, store, start, start + timedelta(days=2)).ideas
    other = lambda ideas: [(i.time, i.strategy, i.direction, i.entry_price, i.allowed, i.blocked_by)   # noqa: E731
                           for i in ideas if i.strategy not in (BREAKOUT, ASIAN_RANGE_BREAKOUT)]
    assert other(got["on"]) and other(got["on"]) == other(got["off"])
    room = [i for i in got["on"] if i.strategy in (BREAKOUT, ASIAN_RANGE_BREAKOUT)]
    assert room and all("room_level" in i.context for i in room)
