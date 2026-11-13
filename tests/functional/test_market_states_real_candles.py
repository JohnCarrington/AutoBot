"""Functional tests for the analyser's five market states, on the REAL stored
GBPUSD candles (/opt/autobot/data/candles/GBPUSD). Stored candles are never
overwritten, so these results do not change. Reads the store only; never
contacts IG. Sell (bid) price; times UK (GMT on these days = UTC).

What Johnny saw on his chart (design section 12), with the times allowed:
  a. the pivot rejection around midnight: an emerging trend down by Friday
     6 November 00:20, becoming a trend down by 02:00;
  b. consolidation at some point between 05:00 and 06:40;
  c. a strong push down at some point between 13:30 and 14:30. The drop at
     07:00 was a UK news spike (Finnhub's GB releases at 07:00 UK: "House Price
     Index MoM" -0.6% against +0.1% expected, "Lloyds House Price Index YoY"
     -1.2% against -0.3%), not the
     start of a real trend (owner, 12 November 2026): its 07:05 candle is both
     the failed bounce and the new low, so no trend is called on it (design
     2.5: the bounce fails first, the new low after); the trend down comes at
     09:50;
  d. no possible reversal up between 10:15 and 10:45: the trend down started
     at 08:20 (13399.0) and had moved 18.3 pips, under the 30 pips needed; the
     possible reversal up comes at 14:30, after the 13:30 news;
  e. at 13:00 the direction is sell side, so no buy is allowed;
  f. stopping and restarting the analyser at 09:00 gives exactly the same
     states afterwards as one that never stopped.
Known shortfall (design section 12): the flat spell at S2 from 11:30 to 12:45
is not yet called consolidation; it is not tested here.
"""

from datetime import datetime, timedelta, timezone

import pytest

from analyser.direction import SELL_SIDE
from analyser.market_state import StateTracker
from analyser.report import analyse
from analyser.states import CONSOLIDATION, DOWN, EMERGING, NONE, POSSIBLE_REVERSAL, RANGING, STRONG_PUSH, TREND, UP
from config.settings_loader import load_settings
from prices.model import uk_short
from prices.store import CandleStore

SETTINGS = load_settings().for_pair("GBPUSD")
UTC = timezone.utc
FIVE = timedelta(minutes=5)

pytestmark = pytest.mark.skipif(not (SETTINGS.candles.folder / "5m").is_dir(),
                                reason="the real candle store is only on the server")


def T(d, h, mi=0):
    return datetime(2026, 11, d, h, mi, tzinfo=UTC)


END = T(6, 17)


@pytest.fixture(scope="module")
def store():
    return CandleStore(SETTINGS.candles.folder, SETTINGS.candles.compress_after_days)


@pytest.fixture(scope="module")
def run(store):
    t = StateTracker(SETTINGS, store)
    t.replay(END + FIVE)
    print("\nState changes, Thu 5 Nov 20:00 to Fri 6 Nov 17:00:")
    for ch in t.changes:
        if T(5, 20) <= ch.time <= END:
            print("  " + ch.line()[:160])
    return t


def state_at(changes, t):
    """(state, direction, type of trend) after the 5-minute candle starting at t."""
    last = [ch for ch in changes if ch.time <= t]
    return (last[-1].state, last[-1].direction, last[-1].trend_type) if last else None


def candles_between(a, b):
    t = a
    while t <= b:
        yield t
        t += FIVE


def test_a_the_pivot_rejection_around_midnight_starts_the_downtrend(run):
    emerging = [ch for ch in run.changes if T(5, 23, 30) <= ch.time <= T(6, 0, 20)
                and (ch.state, ch.direction) == (EMERGING, DOWN)]
    assert emerging, "no emerging trend down between Thu 23:30 and Fri 00:20"
    start = emerging[-1]
    print(f"\n  emerging down: {start.line()[:150]}")
    assert state_at(run.changes, T(6, 0, 20))[:2] == (EMERGING, DOWN)
    trend = [ch for ch in run.changes if start.time < ch.time <= T(6, 2)
             and (ch.state, ch.direction) == (TREND, DOWN)]
    assert trend, "the emerging trend down did not become a trend down by 02:00"
    # since ranging may end an emerging trend (owner, 13 November 2026), a short range comes in between
    # (01:10, back to an emerging trend down on a level rejection at 01:15); nothing else does
    between = [(ch.state, ch.direction) for ch in run.changes if start.time < ch.time < trend[0].time]
    assert set(between) <= {(RANGING, NONE), (EMERGING, DOWN)}, between
    print(f"  trend down:    {trend[0].line()[:150]}")


def test_b_consolidation_between_05_00_and_06_40(run):
    when = [t for t in candles_between(T(6, 5), T(6, 6, 40)) if state_at(run.changes, t)[0] == CONSOLIDATION]
    assert when, "no consolidation between 05:00 and 06:40"
    print(f"\n  consolidation from {uk_short(when[0])} to {uk_short(when[-1])} ({len(when)} candles)")


@pytest.mark.parametrize("a,b", [(T(6, 13, 30), T(6, 14, 30))], ids=["13:30-14:30"])
def test_c_a_strong_push_down(run, a, b):
    when = [t for t in candles_between(a, b) if state_at(run.changes, t) == (TREND, DOWN, STRONG_PUSH)]
    assert when, f"no strong push down between {uk_short(a)} and {uk_short(b)}"
    print(f"\n  strong push down from {uk_short(when[0])} to {uk_short(when[-1])} ({len(when)} candles)")


def test_c_no_trend_on_the_07_00_uk_news_spike_the_trend_down_comes_at_09_50(run):
    """Owner, 12 November 2026: the 07:00 drop was a UK news spike, not a real trend."""
    spike = [t for t in candles_between(T(6, 6, 45), T(6, 7, 30)) if state_at(run.changes, t)[0] == TREND]
    assert spike == [], "a trend was called on the 07:00 news spike"
    trend = [ch for ch in run.changes if T(6, 6, 45) <= ch.time <= T(6, 12) and ch.state == TREND]
    assert trend and trend[0].time == T(6, 9, 50) and trend[0].direction == DOWN
    assert trend[0].reason.startswith("the rejection became a trend")
    print(f"\n  {trend[0].line()[:170]}")


def test_d_no_possible_reversal_up_between_10_15_and_10_45_it_comes_at_14_30(run):
    early = [ch for ch in run.changes if T(6, 10, 15) <= ch.time <= T(6, 10, 45)]
    assert early == [], "the analyser changed state between 10:15 and 10:45"
    assert state_at(run.changes, T(6, 10, 45))[:2] == (TREND, DOWN)
    found = [ch for ch in run.changes if T(6, 13, 30) <= ch.time <= T(6, 15)
             and (ch.state, ch.direction) == (POSSIBLE_REVERSAL, UP)]
    assert found and found[0].time == T(6, 14, 30)
    print(f"\n  {found[0].line()[:170]}")


def test_e_at_13_00_the_direction_is_sell_side_so_no_buy(store):
    d = analyse(SETTINGS, store, T(6, 13)).direction
    print(f"\n  13:00: {d.side} ({d.reason})")
    assert d.side == SELL_SIDE and not d.allows_buy


def test_f_a_restart_at_09_00_gives_exactly_the_states_of_one_that_never_stopped(store):
    never_stopped = StateTracker(SETTINGS, store)
    first_run = StateTracker(SETTINGS, store)
    never_stopped.advance(T(6, 8))
    first_run.advance(T(6, 8))
    t = T(6, 8)
    while t < T(6, 9):                       # both running, every 15 minutes
        t += 3 * FIVE
        never_stopped.advance(t)
        first_run.advance(t)
    restarted = StateTracker(SETTINGS, store)     # the first one stopped at 09:00; a new one starts
    restarted.replay(T(6, 9))
    while t < END:
        t += 3 * FIVE
        never_stopped.advance(t)
        restarted.advance(t)
    a = [ch.as_dict() for ch in never_stopped.changes]
    b = [ch.as_dict() for ch in restarted.changes]
    after = [x for x in a if x["time_utc"] >= "2026-11-06T09:00:00Z"]
    print(f"\n  {len(after)} state changes after 09:00, identical in both; now: "
          f"{never_stopped.machine.now.state} {never_stopped.machine.now.direction}")
    assert b == a and len(after) >= 4
    assert vars(restarted.machine.now) == vars(never_stopped.machine.now)
    assert [(f.candle.start, s, d) for f, s, d, *_ in restarted.history] == \
        [(f.candle.start, s, d) for f, s, d, *_ in never_stopped.history]
