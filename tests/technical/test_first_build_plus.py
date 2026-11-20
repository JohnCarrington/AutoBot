"""first-build-plus (owner, 19 November 2026): the first build (f99efe1) with the dashboard, the Structural Trade Planner
and the hourly-pierce Bollinger bounce of 15 November kept as on main, and the first build's own bounce kept, renamed
"Bollinger bounce 5m", alongside it. These tests hold the two bounces apart, each with its own rules, and the planner
on its own "close beyond" setting. Made-up values; never contacts IG."""

from datetime import datetime, timezone
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from analyser.states import ALLOWED, POSSIBLE_REVERSAL, RANGING, TREND
from config.settings_loader import load_settings
from strategies.common import (BOLLINGER_BOUNCE, BOLLINGER_BOUNCE_5M, BUY, SELL, SWITCH, Candidate, check,
                               closed_on_level_rejection)
from trade_manager.manager import plan

WED = datetime(2026, 11, 4, 10, 0, tzinfo=timezone.utc)


@pytest.fixture
def S(pretend_switches):
    return load_settings(switches_from=pretend_switches).for_pair("GBPUSD")


def idea(S, strategy, direction, state, state_dir):
    st = SimpleNamespace(state=state, direction=state_dir, trend_type=None)
    return check(S, "GBPUSD", Candidate(strategy, direction, WED, D("13400"), ["x"]), st, None, None)


def test_the_two_bounces_have_their_own_names_and_switches():
    assert BOLLINGER_BOUNCE == "Bollinger bounce" and BOLLINGER_BOUNCE_5M == "Bollinger bounce 5m"
    assert SWITCH[BOLLINGER_BOUNCE] == "bollinger_bounce" and SWITCH[BOLLINGER_BOUNCE_5M] == "bollinger_bounce_5m"


def test_the_first_builds_bounce_gives_its_ideas_under_its_new_name():
    from strategies.bollinger_bounce_5m.strategy import candidates
    st = SimpleNamespace(size=None, in_watch_window=False, counts=True)
    watcher = SimpleNamespace(events=[], setups=[st])
    trig = SimpleNamespace(version="bounce", kind="trigger", setup=1, direction="sell", time=WED, price=D("13400"))
    (c,) = candidates(watcher, [trig])
    assert c.strategy == BOLLINGER_BOUNCE_5M and c.direction == SELL


@pytest.mark.parametrize("state,state_dir,direction,ok", [
    (TREND, "up", SELL, True), (TREND, "up", BUY, False),                 # in a trend: against it only
    (POSSIBLE_REVERSAL, "up", BUY, True), (POSSIBLE_REVERSAL, "up", SELL, True),
    (RANGING, "none", SELL, False)])                                       # not in ranging (as on 9 November)
def test_the_first_builds_bounce_keeps_its_9_november_states(S, state, state_dir, direction, ok):
    assert idea(S, BOLLINGER_BOUNCE_5M, direction, state, state_dir).allowed is ok


@pytest.mark.parametrize("state,state_dir", [(TREND, "up"), (RANGING, "none"), ("consolidation", "none")])
def test_the_hourly_pierce_bounce_opens_in_every_state(S, state, state_dir):
    assert idea(S, BOLLINGER_BOUNCE, BUY, state, state_dir).allowed


def test_the_analysers_list_shows_the_first_builds_bounce_under_its_new_name():
    assert "Bollinger bounce 5m (against the trend's direction only)" in ALLOWED[TREND]
    assert "Bollinger bounce 5m" in ALLOWED[POSSIBLE_REVERSAL] and "Bollinger bounce 5m" not in ALLOWED[RANGING]


def test_each_bounces_switch_turns_only_that_bounce_off(S):
    from tests.technical.test_trade_manager import Over
    off = Over(S, switches={"bollinger_bounce_5m": False})
    assert not idea(off, BOLLINGER_BOUNCE_5M, SELL, TREND, "up").allowed
    assert idea(off, BOLLINGER_BOUNCE, SELL, TREND, "up").allowed


def test_only_the_hourly_pierce_bounce_trails_and_only_the_first_builds_closes_on_a_level_rejection(S):
    new = plan(S, "N", BOLLINGER_BOUNCE, SELL, WED, D(100), D(100), D(12), [])
    old = plan(S, "O", BOLLINGER_BOUNCE_5M, SELL, WED, D(100), D(100), D(12), [])
    assert new.trail_from == D("12") and old.trail_from is None
    assert not closed_on_level_rejection(BOLLINGER_BOUNCE) and closed_on_level_rejection(BOLLINGER_BOUNCE_5M)


def test_the_limits_of_each_bounce(S):
    from safety.rules import OpenTrade, _limits
    order = lambda strategy, d: SimpleNamespace(idea=SimpleNamespace(strategy=strategy, direction=d))  # noqa: E731
    t = lambda strategy, d: OpenTrade(strategy, d, WED, D(12), D(10))                                  # noqa: E731
    # the first build's: 1 each way, and 1 more in the opposite direction (2 in all), as on 9 November 2026
    assert _limits(S, order(BOLLINGER_BOUNCE_5M, SELL), [t(BOLLINGER_BOUNCE_5M, BUY)]) == []
    assert "each way" in _limits(S, order(BOLLINGER_BOUNCE_5M, SELL), [t(BOLLINGER_BOUNCE_5M, SELL)])[0]
    # the two bounces never count against each other's own limit
    assert _limits(S, order(BOLLINGER_BOUNCE, SELL), [t(BOLLINGER_BOUNCE_5M, SELL)]) == []
    assert _limits(S, order(BOLLINGER_BOUNCE_5M, SELL), [t(BOLLINGER_BOUNCE, SELL)]) == []


def test_the_trade_reason_names_the_first_builds_bounce():
    from trading.reasons import one_line
    steps = ["Wed 04 Nov 10:05 GMT  #1 bounce sell pierce 13410: high 13410 reached S2 13409; counts",
             "Wed 04 Nov 10:10 GMT  #1 bounce sell reversal 13405: reversal candle",
             "Wed 04 Nov 10:15 GMT  #1 bounce sell confirmation 13403: closed",
             "Wed 04 Nov 10:20 GMT  #1 bounce sell trigger 13402: price went below"]
    line = one_line(SimpleNamespace(strategy=BOLLINGER_BOUNCE_5M, steps=steps))
    assert line.startswith("bounce 5m: pierced S2 13409 at 10:05")


def test_the_planner_uses_its_own_close_beyond_setting_and_there_is_no_hourly_read(S):
    assert S.planner.break_beyond_pips == D("3")
    assert not hasattr(S, "hourly_read")                                      # the hourly read is not in this build
    import pathlib
    for f in pathlib.Path("planner").glob("*.py"):
        assert "hourly_read" not in f.read_text(), f


# ---- the three session strategies, added the same day (owner, 19 November 2026) ----------------------------------

def test_each_session_strategy_has_its_own_name_and_switch_and_shows_by_name():
    from strategies.common import ASIAN_RANGE_BREAKOUT, NEW_YORK_OPEN_REVERSAL, SESSION_STRATEGIES, SESSION_SWEEP
    from trading.reasons import one_line
    assert SESSION_STRATEGIES == ("Asian range breakout", "session sweep", "New York open reversal")
    names = {BOLLINGER_BOUNCE, BOLLINGER_BOUNCE_5M, *SESSION_STRATEGIES}
    assert len(names) == 5 and len({SWITCH[n] for n in names}) == 5           # every one apart, in records too
    for name in (ASIAN_RANGE_BREAKOUT, SESSION_SWEEP, NEW_YORK_OPEN_REVERSAL):
        assert one_line(SimpleNamespace(strategy=name, steps=["broke the range"])).startswith(name + ":")


def test_the_session_strategies_open_in_every_state_like_the_hourly_bounce(S):
    from strategies.common import SESSION_STRATEGIES
    from tests.technical.test_trade_manager import Over
    on = Over(S, switches={"asian_range_breakout": True, "session_sweep": True, "new_york_open_reversal": True})
    for name in SESSION_STRATEGIES:
        for state, d in ((TREND, "up"), (RANGING, "none"), ("consolidation", "none")):
            assert idea(on, name, SELL, state, d).allowed, (name, state)
