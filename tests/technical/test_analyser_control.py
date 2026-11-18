"""Technical tests for the analyser control, stages 1 to 3 (owner, 18 November 2026; design 2.10 and 6), with made-up
states, hourly reads, setups and MACD bars. Nothing here reads the candle store or contacts IG."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from analyser.hourly_read import RALLY, RANGING as H_RANGING
from analyser.states import (CONSOLIDATION, EMERGING, POSSIBLE_REVERSAL, RANGING, TREND, StateMachine, hourly_position,
                             rejection_at_edge)
from config.settings_loader import load_settings
from safety.rules import _one_signal, is_reversal
from strategies.common import (ASIAN_RANGE_BREAKOUT, BOLLINGER_BOUNCE, BREAKOUT, BUY, EMA_PULLBACK, LEVEL_REVERSAL,
                               NEW_YORK_OPEN_REVERSAL, RANGE_TRADE, SELL, SESSION_SWEEP, SLOW_GRIND, allowed,
                               governed_allowed, governs_reasons)
from strategies.replay import reversal_macd

BASE = load_settings().for_pair("GBPUSD")
T0 = datetime(2026, 11, 17, 9, 0, tzinfo=timezone.utc)


class On:
    """The real settings (no .env read) with some switches on."""
    def __init__(self, **switches):
        names = ("slow_grind", "ema_pullback", "bollinger_bounce", "range_trade", "breakout", "level_reversal",
                 "asian_range_breakout", "session_sweep", "new_york_open_reversal")
        self.switches = SimpleNamespace(**({k: True for k in names} | switches))

    def __getattr__(self, name):
        return getattr(BASE, name)


GOV = On(analyser_governs_all=True)
OFF = On()
HR = SimpleNamespace(state=H_RANGING, low=D("13168"), high=D("13204.4"))       # 17 November's hourly range
NOT_RANGING = SimpleNamespace(state=RALLY, low=D("13168"), high=D("13204.4"))


def st(state, direction="none", **kw):
    return SimpleNamespace(state=state, direction=direction, trend_type=None, **kw)


# ---- the edge of the hourly range -----------------------------------------------------------------------------------

@pytest.mark.parametrize("far,close,direction,ok", [
    ("13203.6", "13197.4", SELL, True),       # 10:05 on 17 November: within 3 pips of 13204.4, closed inside
    ("13201.4", "13197.0", SELL, True),       # exactly 3 pips short of the high
    ("13201.3", "13197.0", SELL, False),      # just further inside
    ("13220.7", "13216.7", SELL, False),      # 16:25: beyond the high but the rejection candle closed outside
    ("13220.7", "13204.4", SELL, True),       # beyond the high and closed back inside (on the high counts)
    ("13171.0", "13175.0", BUY, True),
    ("13166.0", "13167.9", BUY, False),       # closed below the low: outside
    ("13171.1", "13175.0", BUY, False),
])
def test_a_rejection_is_at_the_edge_only_near_the_right_side_and_closing_back_inside(far, close, direction, ok):
    assert rejection_at_edge(BASE, HR, D(far), D(close), direction) is ok


def test_the_edge_distance_is_the_setting():
    class Five(On):
        analyser_control = SimpleNamespace(edge_within_pips=D("5"), consolidation_breakout_beyond_pips=D("4"))
    assert not rejection_at_edge(BASE, HR, D("13199.5"), D("13195"), SELL)
    assert rejection_at_edge(Five(), HR, D("13199.5"), D("13195"), SELL)


@pytest.mark.parametrize("price,where", [("13202.0", "top edge"), ("13210.0", "top edge"), ("13170.0", "bottom edge"),
                                         ("13160.0", "bottom edge"), ("13190.0", "middle"), (None, "unknown")])
def test_where_price_is_in_the_hourly_range(price, where):
    assert hourly_position(BASE, HR, D(price) if price else None) == where


def test_a_range_so_narrow_that_both_edges_are_near_gives_the_nearer_edge():
    narrow = SimpleNamespace(state=H_RANGING, low=D("13200"), high=D("13204"))
    assert hourly_position(BASE, narrow, D("13203")) == "top edge"
    assert hourly_position(BASE, narrow, D("13201")) == "bottom edge"
    assert hourly_position(BASE, narrow, D("13202")) == "top edge"          # a tie: the top


def test_hourly_position_without_a_range_is_unknown():
    assert hourly_position(BASE, SimpleNamespace(state=H_RANGING, low=None, high=None), D("13200")) == "unknown"


# ---- stage 1 in the state machine -----------------------------------------------------------------------------------

def machine(**switches):
    m = StateMachine(On(**switches), T0)
    m.hourly = HR
    return m


def setup(far, close):
    return SimpleNamespace(furthest=D(far), reversal=SimpleNamespace(sell_close=D(close)))


def test_stage_1_a_rejection_inside_the_hourly_range_does_not_start_an_emerging_trend():
    m = machine(analyser_uses_hourly=True)
    assert not m.at_hourly_edge(setup("13197.8", "13194.0"), SELL)       # the pivot in the middle of the box
    assert m.at_hourly_edge(setup("13203.6", "13197.4"), SELL)
    assert not m.at_hourly_edge(setup("13220.7", "13216.7"), SELL)       # closed outside the range


def test_stage_1_off_or_not_ranging_or_no_range_every_rejection_counts():
    assert machine().at_hourly_edge(setup("13197.8", "13194.0"), SELL)
    m = machine(analyser_uses_hourly=True)
    m.hourly = NOT_RANGING
    assert m.at_hourly_edge(setup("13197.8", "13194.0"), SELL)
    m.hourly = SimpleNamespace(state=H_RANGING, low=None, high=None)
    assert m.at_hourly_edge(setup("13197.8", "13194.0"), SELL)


def test_stage_1_the_position_is_recorded_with_each_change_only_while_on():
    from analyser.states import StateChange
    ch = StateChange(T0, RANGING, "none", None, CONSOLIDATION, "none", "x", (), "top edge")
    assert ch.as_dict()["hourly_position"] == "top edge"
    assert "hourly_position" not in StateChange(T0, RANGING, "none", None, CONSOLIDATION, "none", "x", ()).as_dict()


# ---- stage 2: the table ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize("strategy,direction,state,ok", [
    # ranging: the trend group nothing (the Asian range breakout excepted), the reversal group either way
    (EMA_PULLBACK, SELL, st(RANGING), False), (SLOW_GRIND, BUY, st(RANGING), False), (BREAKOUT, BUY, st(RANGING), False),
    (ASIAN_RANGE_BREAKOUT, BUY, st(RANGING), True),
    (BOLLINGER_BOUNCE, SELL, st(RANGING), True), (LEVEL_REVERSAL, BUY, st(RANGING), True),
    (RANGE_TRADE, SELL, st(RANGING), True), (SESSION_SWEEP, BUY, st(RANGING), True),
    # emerging trend and trend: both groups with the trend only
    (EMA_PULLBACK, BUY, st(EMERGING, "up"), True), (EMA_PULLBACK, SELL, st(EMERGING, "up"), False),
    (BOLLINGER_BOUNCE, SELL, st(TREND, "up"), False), (BOLLINGER_BOUNCE, BUY, st(TREND, "up"), True),
    (LEVEL_REVERSAL, SELL, st(EMERGING, "down"), True), (LEVEL_REVERSAL, BUY, st(EMERGING, "down"), False),
    (ASIAN_RANGE_BREAKOUT, SELL, st(TREND, "up"), False), (ASIAN_RANGE_BREAKOUT, BUY, st(TREND, "up"), True),
    (NEW_YORK_OPEN_REVERSAL, SELL, st(TREND, "down"), True),
    # possible reversal (direction up: the old trend was down): the trend group nothing new; the reversal group with
    # the old trend freely, against it only with the MACD rule
    (EMA_PULLBACK, BUY, st(POSSIBLE_REVERSAL, "up", macd_ok=True), False),
    (ASIAN_RANGE_BREAKOUT, BUY, st(POSSIBLE_REVERSAL, "up", macd_ok=True), False),
    (BOLLINGER_BOUNCE, SELL, st(POSSIBLE_REVERSAL, "up", macd_ok=False), True),
    (BOLLINGER_BOUNCE, BUY, st(POSSIBLE_REVERSAL, "up", macd_ok=False, macd_why="growing"), False),
    (BOLLINGER_BOUNCE, BUY, st(POSSIBLE_REVERSAL, "up", macd_ok=True), True),
    # consolidation: nothing (the Asian range breakout excepted)
    (LEVEL_REVERSAL, SELL, st(CONSOLIDATION), False), (BOLLINGER_BOUNCE, BUY, st(CONSOLIDATION), False),
    (ASIAN_RANGE_BREAKOUT, SELL, st(CONSOLIDATION), True),
])
def test_stage_2_the_table(strategy, direction, state, ok):
    got = governs_reasons(GOV, strategy, direction, state, None, None)
    assert (got == []) is ok, got
    assert all(r.startswith("ANALYSER_GOVERNS_ALL: ") for r in got)


def test_stage_2_off_nothing_is_checked():
    assert governs_reasons(OFF, BOLLINGER_BOUNCE, SELL, st(CONSOLIDATION), HR, None) == []


CTX_EDGE = {"furthest": D("13203.6"), "rejection_close": D("13197.4")}
CTX_MIDDLE = {"furthest": D("13197.8"), "rejection_close": D("13194.0")}


@pytest.mark.parametrize("strategy,direction,ctx,ok", [
    (EMA_PULLBACK, SELL, None, False),                       # the trend group opens nothing while the hourly ranges
    (ASIAN_RANGE_BREAKOUT, SELL, None, True),                # ... except the Asian range breakout
    (BOLLINGER_BOUNCE, SELL, CTX_EDGE, True),                # a sell at the top edge
    (BOLLINGER_BOUNCE, SELL, CTX_MIDDLE, False),             # in the middle
    (BOLLINGER_BOUNCE, BUY, CTX_EDGE, False),                # a buy is judged at the bottom edge
    (LEVEL_REVERSAL, SELL, {"furthest": D("13220.7"), "rejection_close": D("13216.7")}, False),   # closed outside
    (SESSION_SWEEP, SELL, None, False),                      # its furthest point not known
])
def test_stage_2_while_the_hourly_ranges(strategy, direction, ctx, ok):
    state = st(EMERGING, "down" if direction == SELL else "up")
    got = governs_reasons(GOV, strategy, direction, state, HR, ctx)
    assert (got == []) is ok, got


def test_stage_2_replaces_the_level_reversals_and_the_bounces_own_state_rules_but_not_the_others():
    args = (D("13190"), None, None, None)
    lr, _ = allowed(GOV, LEVEL_REVERSAL, SELL, D("13190"), st(CONSOLIDATION), None, None, None)
    assert not any("which does not allow level reversal" in r for r in lr) and any("ANALYSER_GOVERNS_ALL" in r for r in lr)
    lr_off, _ = allowed(OFF, LEVEL_REVERSAL, SELL, *args[:1], st(CONSOLIDATION), None, None, None)
    assert any("which does not allow level reversal" in r for r in lr_off)
    sg, _ = allowed(GOV, SLOW_GRIND, BUY, D("13190"), st(EMERGING, "up"), None, None, None)
    assert any("which does not allow slow grind" in r for r in sg)          # its own rule still applies
    rt, _ = allowed(GOV, RANGE_TRADE, SELL, D("13190"), st(TREND, "down"), None, None, None)
    assert any("which does not allow range trade" in r for r in rt)
    bb, _ = allowed(OFF, BOLLINGER_BOUNCE, SELL, D("13190"), st(CONSOLIDATION), None, None, None)
    assert bb == []                                                          # without hindrance while off


def test_the_dashboard_list_of_strategies_allowed_follows_the_table():
    assert governed_allowed(CONSOLIDATION) == [ASIAN_RANGE_BREAKOUT]
    assert set(governed_allowed(RANGING)) == {ASIAN_RANGE_BREAKOUT, BOLLINGER_BOUNCE, LEVEL_REVERSAL, SESSION_SWEEP,
                                              NEW_YORK_OPEN_REVERSAL, RANGE_TRADE}
    assert SLOW_GRIND not in governed_allowed(EMERGING) and SLOW_GRIND in governed_allowed(TREND)
    assert set(governed_allowed(POSSIBLE_REVERSAL)) == {BOLLINGER_BOUNCE, LEVEL_REVERSAL, SESSION_SWEEP,
                                                        NEW_YORK_OPEN_REVERSAL}


# ---- stage 2: the MACD rule in a possible reversal ------------------------------------------------------------------

def tracker(bars, start_index=0):
    """A pretend tracker: one candle a bar, 5 minutes apart; the old trend started at bar `start_index`."""
    hist, extras = [], []
    start = T0 + timedelta(minutes=5 * start_index)
    for k, b in enumerate(bars):
        f = SimpleNamespace(candle=SimpleNamespace(start=T0 + timedelta(minutes=5 * k)),
                            macd_hist=None if b is None else D(b))
        hist.append((f,))
        extras.append({"trend_start": start})
    return SimpleNamespace(history=hist, extras=extras)


@pytest.mark.parametrize("bars,ok", [
    (["-1", "-3", "-5"], True),             # the old trend down: at its biggest bar now
    (["-1", "-5", "-4"], True),             # past its biggest and shrinking
    (["-1", "-5", "-3", "-4"], False),      # past its biggest but growing again
    (["-1", "-5", "-3", "0.5"], True),      # crossed zero: past its biggest
    (["-1", "-5", "-2", "0"], True),        # at zero
    ([None, None], False),                  # not known
])
def test_the_macd_rule_against_an_old_down_trend(bars, ok):
    got, why = reversal_macd(tracker(bars), len(bars) - 1, "up")
    assert got is ok, why


def test_the_macd_rule_counts_only_bars_since_the_old_trend_started():
    bars = ["-9", "-1", "-3", "-2"]                       # -9 is before the old trend started
    assert reversal_macd(tracker(bars, start_index=1), 3, "up")[0] is True     # -2 smaller than -3 and the bar before
    assert reversal_macd(tracker(["1", "4", "3"]), 2, "down")[0] is True       # an old up trend: mirror


# ---- stage 3 ------------------------------------------------------------------------------------------------------

def idea(strategy, direction, state=EMERGING, state_direction="up", context=None):
    return SimpleNamespace(strategy=strategy, direction=direction, state=state, state_direction=state_direction,
                           trend_type=None, context=context or {})


def test_one_signal_one_trade():
    on, off = On(one_signal_one_trade=True), On()
    i = idea(LEVEL_REVERSAL, SELL, context={"signal": "sell 2026-11-17T09:55:00Z"})
    used = {"sell 2026-11-17T09:55:00Z": BOLLINGER_BOUNCE}
    assert _one_signal(on, i, used) == ["same signal already traded by Bollinger bounce"]
    assert _one_signal(off, i, used) == []
    assert _one_signal(on, i, {"buy 2026-11-17T09:55:00Z": BOLLINGER_BOUNCE}) == []   # the other way: another signal
    assert _one_signal(on, idea(EMA_PULLBACK, SELL), used) == []                       # no rejection candle


@pytest.mark.parametrize("strategy,counts_when_on", [(SESSION_SWEEP, True), (NEW_YORK_OPEN_REVERSAL, True),
                                                     (ASIAN_RANGE_BREAKOUT, False), (BOLLINGER_BOUNCE, False),
                                                     (LEVEL_REVERSAL, True)])
def test_stage_3_the_sweep_and_new_york_reversal_come_under_one_view_at_a_time(strategy, counts_when_on):
    against = idea(strategy, SELL)                          # a sell in an emerging trend up
    assert is_reversal(against, On(one_signal_one_trade=True)) is counts_when_on
    assert is_reversal(against, On()) is (strategy == LEVEL_REVERSAL)
    assert is_reversal(idea(strategy, BUY), On(one_signal_one_trade=True)) is False     # with the trend
