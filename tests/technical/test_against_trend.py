"""Technical tests for the pace and target rule (trading/against_trend.py; owner, 11 November 2026, as tested in
docs/research/pace_and_target_20261111.md): a Bollinger bounce against open trend trades only at a significant level
in their direction (within 5 pips), and only if price has moved under 5 pips an hour over the last 2 hours.
A pretend candle store and pretend daily levels; nothing here contacts IG."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from strategies.bollinger_bounce.strategy import from_rejection, setup_context
from strategies.common import BOLLINGER_BOUNCE, BREAKOUT, BUY, EMA_PULLBACK, LEVEL_REVERSAL, SELL, SLOW_GRIND, Idea
from tests.technical.test_orders import Over
from trading import against_trend as at

U = lambda *a: datetime(*a, tzinfo=timezone.utc)  # noqa: E731
T = U(2026, 11, 11, 10, 0)            # the bounce opens in the candle starting here (a Wednesday)


@pytest.fixture
def S(pretend_switches):
    from config.settings_loader import load_settings
    return load_settings(switches_from=pretend_switches).for_pair("GBPUSD")


def c5(t, h, l, close=None, tf="5m", minutes=5):
    h, l = D(str(h)), D(str(l))
    close = D(str(close)) if close is not None else (h + l) / 2
    return SimpleNamespace(start=t, end=t + timedelta(minutes=minutes), sell_open=close, sell_high=h, sell_low=l,
                           sell_close=close, tf=tf)


class Store:
    """read_range as the real store: candles with start in [start, end), in time order."""
    def __init__(self, m5=(), d1=()):
        self.c = {"5m": sorted(m5, key=lambda c: c.start), "1d": sorted(d1, key=lambda c: c.start)}

    def read_range(self, tf, start, end):
        return [c for c in self.c.get(tf, []) if start <= c.start < end]


def flat_hours(close_now, close_2h_ago, *, extra=()):
    """5-minute candles from 4 hours before T: the close 2 hours before T is close_2h_ago, the last one close_now."""
    out = []
    for k in range(48):
        t = T - timedelta(hours=4) + timedelta(minutes=5 * k)
        close = close_2h_ago if t + timedelta(minutes=5) <= T - timedelta(hours=2) else close_now
        out.append(c5(t, close + 1, close - 1, close))
    return out + list(extra)


def day(d, high, low, close):
    """A daily candle, midnight to midnight UK (UTC in November)."""
    return c5(U(2026, 11, d, 0, 0), high, low, close, tf="1d", minutes=24 * 60)


def week(high, low, close, *, sunday=None, this_week=None):
    """The daily candles of Monday 2 to Friday 6 November (the previous Monday-to-Friday week at T): the week's high
    on Monday, its low on Tuesday, its close on Friday. `sunday`: a Sunday 1 November candle (high, low, close);
    `this_week`: candles for Monday 9 and Tuesday 10 November (before T, in the current week)."""
    h, l, c = D(high), D(low), D(close)
    mid = (h + l) / 2
    out = [day(2, h, mid - 1, mid), day(3, mid + 1, l, mid), day(4, mid + 1, mid - 1, mid),
           day(5, mid + 1, mid - 1, mid), day(6, mid + 1, mid - 1, c)]
    if sunday:
        out.append(day(1, *sunday))
    for d in ((9, 10) if this_week else ()):
        out.append(day(d, *this_week))
    return out


@pytest.fixture
def levels(monkeypatch):
    """The bot's daily levels at T (levels.current.build), as given."""
    lv = []
    monkeypatch.setattr("levels.current.build", lambda s, store, t: SimpleNamespace(levels=lv))
    return lv


def bounce(direction=BUY, *, frm=T - timedelta(minutes=20), last=T - timedelta(minutes=5), high="13310", low="13304.6"):
    ctx = {"setup_from": frm, "setup_last": last, "setup_high": D(high), "setup_low": D(low)}
    return Idea("GBPUSD", BOLLINGER_BOUNCE, direction, T, D("13308"), "trend", "down", "slow grind", "no clear direction",
                ["made up"], True, "", ctx)


def trade(strategy=EMA_PULLBACK, direction=SELL, fill="13320", ref="r1", open_=True):
    return SimpleNamespace(strategy=strategy, direction=direction, fill=D(fill), reference=ref, open=open_)


# ---- when the rule applies ----------------------------------------------------------------------------------------

def test_the_rule_is_only_for_a_bollinger_bounce(S, levels):
    i = bounce()
    i.strategy = BREAKOUT
    assert at.check(S, Store(), i, T, [trade()]) is None


def test_without_an_open_trend_trade_against_it_the_bounce_is_not_touched(S, levels):
    # a level reversal against it is not a trend trade; a trend trade the same way is not against it; nor a closed one
    trades = [trade(LEVEL_REVERSAL), trade(SLOW_GRIND, BUY), trade(BREAKOUT, open_=False)]
    assert at.check(S, Store(), bounce(), T, trades) is None


@pytest.mark.parametrize("strategy", [EMA_PULLBACK, SLOW_GRIND, BREAKOUT])
def test_each_trend_strategy_counts(S, levels, strategy):
    v = at.check(S, Store(flat_hours(13310, 13309)), bounce(), T, [trade(strategy)])
    assert v is not None and v.against == [f"{strategy} sell r1 at 13320"]


# ---- 1. at a significant level in their direction ------------------------------------------------------------------

def test_a_bounce_at_a_00_with_price_moving_slowly_is_valid(S, levels):
    v = at.check(S, Store(flat_hours(13310, 13309)), bounce(low="13304.6"), T, [trade()])
    assert v.valid and v.reason == "" and v.level == "00 13300" and v.turned_from == D("13304.6")
    assert v.pips_per_hour == D("0.5")                       # 1 pip in 2 hours


def test_more_than_5_pips_from_any_level_is_refused(S, levels):
    v = at.check(S, Store(flat_hours(13310, 13309)), bounce(low="13305.5"), T, [trade()])
    assert not v.valid and v.reason == at.NOT_AT_LEVEL and v.level is None
    assert v.near[0] == "00 13300 (5.5 pips)"


def test_exactly_5_pips_counts_as_at_the_level(S, levels):
    assert at.check(S, Store(flat_hours(13310, 13309)), bounce(low="13305.0"), T, [trade()]).valid


def test_the_low_is_the_lowest_of_all_the_setups_candles_in_the_store(S, levels):
    # the setup's own candles say 13306 (6 pips away), but a candle between them went to 13304 (4 pips)
    between = c5(T - timedelta(minutes=15), 13309, 13304)
    after = c5(T, 13301, 13299)                               # the candle it opens in: not part of the setup
    v = at.check(S, Store(flat_hours(13310, 13309, extra=[between, after])), bounce(low="13306"), T, [trade()])
    assert v.valid and v.turned_from == D("13304")


def test_a_bounce_sell_uses_the_high_it_turned_from(S, levels):
    v = at.check(S, Store(flat_hours(13390, 13389)), bounce(SELL, high="13397"), T, [trade(direction=BUY, fill="13380")])
    assert v.valid and v.level == "00 13400" and v.turned_from == D("13397")


def test_a_level_not_in_the_trend_trades_direction_does_not_count(S, levels):
    # sells opened at 13298: 13300 is above them, not in their direction (down); the next is 13200
    v = at.check(S, Store(flat_hours(13310, 13309)), bounce(low="13302"), T, [trade(fill="13298")])
    assert not v.valid and v.reason == at.NOT_AT_LEVEL
    # with one sell opened above 13300 it counts again
    v = at.check(S, Store(flat_hours(13310, 13309)), bounce(low="13302"), T, [trade(fill="13298"), trade(fill="13310", ref="r2")])
    assert v.valid and v.level == "00 13300"


def test_the_weekly_pivot_is_from_the_previous_monday_to_friday_week(S, levels):
    st = Store(flat_hours(13346, 13345), week("13503.1", "13341.4", "13346.9"))      # pivot 13397.1
    v = at.check(S, st, bounce(SELL, high="13394"), T, [trade(direction=BUY, fill="13380")])
    assert v.valid and v.level == "weekly pivot 13397.1"


def test_the_weekly_pivot_leaves_out_sundays_prices_and_the_current_week(S):
    """Owner, 13 November 2026: "the standard weekly pivot from the previous Monday-to-Friday week", not including
    Sunday's prices."""
    days = week("13503.1", "13341.4", "13346.9", sunday=("13600", "13200", "13400"), this_week=("13700", "13100", "13650"))
    assert at.weekly_pivot(S, Store(d1=days), T) == D("13397.1")


def test_on_a_sunday_evening_the_previous_week_is_the_one_just_ended(S):
    days = week("13503.1", "13341.4", "13346.9")
    sunday_evening = U(2026, 11, 8, 23, 0)
    assert at.weekly_pivot(S, Store(d1=days), sunday_evening) == D("13397.1")
    assert at.weekly_pivot(S, Store(d1=days), U(2026, 11, 6, 21, 0)) is None     # that week not finished yet


@pytest.mark.parametrize("kind", ["S2", "S3", "R2", "R3"])
def test_s2_s3_r2_and_r3_count(S, levels, kind):
    levels.append(SimpleNamespace(type=kind, price=D("13352")))
    v = at.check(S, Store(flat_hours(13356, 13355)), bounce(low="13350.5"), T, [trade(fill="13370")])
    assert v.valid and v.level == f"{kind} 13352"


@pytest.mark.parametrize("kind", ["S1", "R1", "pivot", "previous_day_low", "round_number"])
def test_other_levels_do_not_count(S, levels, kind):
    levels.append(SimpleNamespace(type=kind, price=D("13352")))
    v = at.check(S, Store(flat_hours(13356, 13355)), bounce(low="13350.5"), T, [trade(fill="13370")])
    assert not v.valid and v.reason == at.NOT_AT_LEVEL


# ---- 2. only if price has been moving slowly ---------------------------------------------------------------------

def test_at_the_level_but_moving_fast_is_refused_and_the_trend_trades_held(S, levels):
    v = at.check(S, Store(flat_hours(13310, 13320)), bounce(), T, [trade()])        # 10 pips in 2 hours
    assert not v.valid and v.reason == at.TOO_FAST and v.level == "00 13300" and v.pips_per_hour == D("5")


def test_just_under_5_pips_an_hour_is_slow(S, levels):
    v = at.check(S, Store(flat_hours(13310, D("13319.9"))), bounce(), T, [trade()])
    assert v.valid and v.pips_per_hour == D("4.95")


def test_the_pace_is_the_net_move_not_the_way_there(S, levels):
    # up 30 and back down in between: net 1 pip in 2 hours is slow
    hs = flat_hours(13310, 13309)
    hs[30] = c5(hs[30].start, 13340, 13330, 13335)
    assert at.check(S, Store(hs), bounce(), T, [trade()]).valid


def test_with_no_candle_two_hours_before_the_pace_cannot_be_read_and_the_bounce_is_refused(S, levels):
    hs = [c for c in flat_hours(13310, 13309) if c.start >= T - timedelta(hours=1)]   # e.g. after the weekend
    v = at.check(S, Store(hs), bounce(), T, [trade()])
    assert not v.valid and v.reason == at.PACE_UNKNOWN and v.pips_per_hour is None


def test_only_finished_candles_count(S, levels):
    # the candle the bounce opens in (a big move) is not used
    hs = flat_hours(13310, 13309, extra=[c5(T, 13310, 13280, 13281)])
    assert at.check(S, Store(hs), bounce(), T, [trade()]).pips_per_hour == D("0.5")


def test_the_three_numbers_are_settings(S, levels):
    loose = Over(S, bounce={"against_trend_level_within_pips": D("8"), "against_trend_max_pips_per_hour": D("12"),
                            "against_trend_pace_hours": 3})
    hs = flat_hours(13310, 13320)                             # 10 pips in 2 hours, and in 3
    assert not at.check(S, Store(hs), bounce(low="13307"), T, [trade()]).valid           # 7 pips away
    v = at.check(loose, Store(hs), bounce(low="13307"), T, [trade()])
    assert v.valid and v.pips_per_hour == D("10") / 3


def test_the_verdict_reads_well_in_the_decision_log(S, levels):
    v = at.check(S, Store(flat_hours(13310, 13320)), bounce(), T, [trade()])
    d = v.as_dict()
    assert d["valid"] is False and d["reason"] == "price moving fast" and d["level"] == "00 13300"
    assert d["pips_per_hour"] == "5.0" and d["turned_from"] == "13304.6"
    assert v.line().startswith("refused: price moving fast (turned from 13304.6, at 00 13300; 5.0 pips an hour")


# ---- the bounce idea carries its setup ---------------------------------------------------------------------------

def setup(pierce_t, low, last_t=None):
    pierce = c5(pierce_t, low + 5, low)
    conf = c5(last_t, low + 6, low + 2) if last_t else None
    return SimpleNamespace(pierce=pierce, reversal=None, confirmation=conf, size=None, in_watch_window=True, counts=True)


def test_the_bounce_idea_carries_the_span_and_extremes_of_its_setup():
    st = setup(T - timedelta(minutes=20), 13304, T - timedelta(minutes=5))
    ctx = setup_context(st)
    assert ctx == {"setup_from": T - timedelta(minutes=20), "setup_last": T - timedelta(minutes=5),
                   "setup_high": D("13310"), "setup_low": D("13304")}


def test_setups_triggering_the_same_way_in_the_same_candle_are_one_bounce_the_first_ones():
    # as the research and the live bot (which sends only the first): every copy carries the first setup's candles
    s1, s2 = setup(T - timedelta(minutes=30), 13304), setup(T - timedelta(minutes=10), 13306)
    w = SimpleNamespace(setups=[s1, s2], events=[])
    ev = [SimpleNamespace(version="bounce", kind="trigger", setup=k, time=T, direction="buy", price=D("13308"))
          for k in (1, 2)]
    a, b = from_rejection(w, ev, "bounce", BOLLINGER_BOUNCE)
    assert a.context == b.context == setup_context(s1)
    assert a.context is not b.context
    s3 = setup(T - timedelta(minutes=10), 13390)               # the other way: its own
    w.setups.append(s3)
    sell = SimpleNamespace(version="bounce", kind="trigger", setup=3, time=T, direction="sell", price=D("13385"))
    *_, c = from_rejection(w, ev + [sell], "bounce", BOLLINGER_BOUNCE)
    assert c.direction == SELL and c.context == setup_context(s3)


def test_the_range_trade_carries_nothing_for_it():
    s1 = setup(T - timedelta(minutes=30), 13304)
    ev = [SimpleNamespace(version="range", kind="trigger", setup=1, time=T, direction="buy", price=D("13308"))]
    (x,) = from_rejection(SimpleNamespace(setups=[s1], events=[]), ev, "range", "range trade")
    assert x.context == {}
