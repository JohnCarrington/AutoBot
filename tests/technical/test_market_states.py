"""Technical tests for the analyser's five market states (analyser/states.py,
analyser/market_state.py): each way of moving between states, the flip-flop
protection, evidence fading, the records, and the start-up replay reaching
exactly the state a run that never stopped reaches. Made-up features and
candles; never contacts IG. (The functional tests on real days come later.)"""

import dataclasses
import json
import math
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from analyser.features import Features
from analyser.market_state import StateTracker
from analyser.states import (CONSOLIDATION, DOWN, EMERGING, NONE, POSSIBLE_REVERSAL, RANGING, SLOW_GRIND,
                             STRONG_PUSH, TREND, UP, StateMachine)
from prices.model import Candle
from prices.store import CandleStore
from rejection.watch import BOUNCE, BUY, CONFIRMATION, EXPIRED, REVERSAL, SELL, Event
from tests.technical.test_pairs import pretend

UTC = timezone.utc
OPEN = datetime(2026, 11, 1, 21, 0, tzinfo=UTC)          # Sunday reopen
FIVE = timedelta(minutes=5)


@pytest.fixture
def st(tmp_path):
    return pretend(tmp_path, "EURUSD").for_pair("EURUSD")     # 1 point a pip


def F(i, **kw):
    """Neutral features for candle i: neither ranging nor consolidating nor trending."""
    t = OPEN + i * FIVE
    c = D(str(kw.pop("c", 11650)))
    o = D(str(kw.pop("o", c)))
    h = D(str(kw.pop("h", max(o, c) + 1)))
    lo = D(str(kw.pop("l", min(o, c) - 1)))
    candle = Candle("5m", t, t + FIVE, o + 1, h + 1, lo + 1, c + 1, o, h, lo, c)
    base = dict(candle=candle, o=o, h=h, l=lo, c=c, upper=c + 6, middle=c, lower=c - 6, width=D(12),
                mid_slope=D(1), upper_slope=D(1), lower_slope=D(1), ema7=c, ema13=c, ema21=c, ema100=c,
                stack=None, stacked_for=0, weave=True, ema100_move=D(5), efficiency=D("0.6"), crossings=1,
                reached_upper=False, reached_lower=False, both_bands_recently=False, quiet=False,
                avg_body=D(4), colour_ratio=D(3), body=D(1), range_=D(2), spike=False, green_share=D("0.5"),
                red_share=D("0.5"), widening=D(1), fan=D(1), closes_on_upper=0, closes_on_lower=0,
                macd_hist=D("-0.5"), rsi=D(40))
    whole = ("crossings", "stacked_for", "closes_on_upper", "closes_on_lower")
    base.update({k: (D(str(v)) if isinstance(v, (int, float, str)) and not isinstance(v, bool)
                     and k not in whole and k != "stack" else v) for k, v in kw.items()})
    return Features(**base)


def ev(n, kind, direction, t, note="note"):
    return Event(n, BOUNCE, direction, kind, t, None, note)


def setups(**by_id):
    return lambda i: by_id.get(str(i)) or SimpleNamespace(pierced=[{"what": "lower Bollinger band"}])


PIVOT = SimpleNamespace(pierced=[{"what": "pivot"}])
BAND = SimpleNamespace(pierced=[{"what": "upper Bollinger band"}])


def machine(st):
    return StateMachine(st, OPEN)


def run(m, feats, events=None, setup_of=None):
    events = events or {}
    out = []
    for i, f in feats:
        ch = m.step(f, events.get(i, []), setup_of or setups())
        if ch:
            out.append(ch)
    return out


def downtrend(st, start=11650):
    """A machine in an emerging down trend started at `start` (broke out of consolidation)."""
    m = machine(st)
    run(m, [(0, F(0, c=start, lower=start + 1, upper=start + 13))])
    assert (m.now.state, m.now.direction) == (EMERGING, DOWN)
    return m


# ---- starting, and leaving consolidation -------------------------------------------------

def test_the_week_starts_in_consolidation_with_no_direction(st):
    m = machine(st)
    assert (m.now.state, m.now.direction, m.now.trend_type, m.now.since) == (CONSOLIDATION, NONE, None, OPEN)
    assert m.now.strategies_allowed == ()


def test_a_close_beyond_a_band_breaks_out_of_consolidation_at_once(st):
    m = machine(st)
    (ch,) = run(m, [(0, F(0, c=11640, lower=11645))])
    assert (ch.state, ch.direction, ch.previous_state) == (EMERGING, DOWN, CONSOLIDATION)
    assert ch.reason.startswith("broke out of the consolidation: close 11640.0 below the lower band 11645.0")
    assert m.now.strategies_allowed[0] == "slow grind"


def test_a_level_rejection_starts_an_emerging_trend_but_a_band_only_rejection_does_not(st):
    m = machine(st)
    t = OPEN
    assert run(m, [(0, F(0))], {0: [ev(1, CONFIRMATION, SELL, t)]}, setups(**{"1": BAND})) == []
    (ch,) = run(m, [(1, F(1))], {1: [ev(2, CONFIRMATION, SELL, t, "closed below the reversal low")]},
                setups(**{"2": PIVOT}))
    assert (ch.state, ch.direction) == (EMERGING, DOWN)
    assert ch.reason == "rejected at a level: closed below the reversal low"


# ---- emerging trend --------------------------------------------------------------------

def test_an_emerging_trend_is_cancelled_3_pips_back_past_its_start(st):
    m = downtrend(st, 11650)
    assert run(m, [(1, F(1, c=11653))]) == []                  # 3 pips back: not more than 3
    (ch,) = run(m, [(2, F(2, c=11653.1))])
    assert (ch.state, ch.direction) == (CONSOLIDATION, NONE) and "cancelled" in ch.reason


def proof_candles(i, low):
    """A failed bounce (staying above the trend's last low, `low`), then a new low on a falling
    lower band, under stacked EMAs and the 100 EMA."""
    bounce = F(i, o=low + 1, c=low + 3, h=low + 4, l=low, ema21=low + 5, middle=low + 6, ema100=low + 20)
    drop = F(i + 1, o=low + 1, c=low - 1, h=low + 1, l=low - 3, lower=low - 3, reached_lower=True,
             lower_slope=-1, stack="down", stacked_for=4, ema7=low + 1, ema13=low + 2, ema21=low + 3,
             ema100=low + 20)
    return [(i, bounce), (i + 1, drop)]


def test_the_trend_proof_turns_an_emerging_trend_into_a_trend(st):
    m = downtrend(st, 11650)
    (ch,) = run(m, proof_candles(1, 11649))
    assert (ch.state, ch.direction, ch.trend_type) == (TREND, DOWN, SLOW_GRIND)
    assert ch.reason.startswith("the rejection became a trend: a bounce failed under the 21 EMA and middle band, "
                                "then a new low 11646.0 on the lower band")


@pytest.mark.parametrize("spoil", [
    {"stack": None},                         # EMAs not stacked
    {"stacked_for": 2},                      # not stacked for 3 candles yet
    {"ema100": D(11630)},                    # price above the 100 EMA
    {"lower_slope": D(0)},                   # band not sloping down
    {"reached_lower": False},                # not on the lower band
])
def test_no_trend_without_every_part_of_the_proof(st, spoil):
    m = downtrend(st, 11650)
    (b, bounce), (d, drop) = proof_candles(1, 11649)
    assert run(m, [(b, bounce), (d, dataclasses.replace(drop, **spoil))]) == []
    assert m.now.state == EMERGING


def test_no_trend_without_a_failed_bounce_first(st):
    m = downtrend(st, 11650)
    _, (d, drop) = proof_candles(1, 11649)
    assert run(m, [(d, drop)]) == [] and m.now.state == EMERGING


def test_evidence_fades_after_24_candles_with_nothing_new(st):
    m = downtrend(st, 11650)
    quiet = [(i, F(i, c=11650, l=11649)) for i in range(1, 24)]       # no new low (the low is 11649)
    assert run(m, quiet) == []
    (ch,) = run(m, [(24, F(24, c=11650, l=11649))])
    assert ch.state == CONSOLIDATION and "faded: no new low for 24 candles" in ch.reason


# ---- trend, type of trend, the end of a trend ----------------------------------------------

def trend(st):
    m = downtrend(st, 11650)
    run(m, proof_candles(1, 11649))
    assert m.now.state == TREND
    return m


def push(i, low):
    return F(i, c=low, l=low - 1, h=low + 1, red_share="0.8", widening="1.6", fan=7, closes_on_lower=4,
             ema100=low + 30)


def test_a_strong_push_needs_its_signs_for_2_candles_in_a_row(st):
    m = trend(st)
    assert run(m, [(3, push(3, 11636))]) == []
    (ch,) = run(m, [(4, push(4, 11635))])
    assert (ch.state, ch.trend_type) == (TREND, STRONG_PUSH) and ch.reason.startswith("strong push: 80% red")


def test_a_trend_ends_after_2_closes_back_past_the_100_ema(st):
    m = trend(st)
    assert run(m, [(3, F(3, c=11660, ema100=11655))]) == []
    (ch,) = run(m, [(4, F(4, c=11661, ema100=11655))])
    assert ch.state == CONSOLIDATION and "back above the 100 EMA" in ch.reason


def test_ranging_and_consolidation_need_2_candles_in_a_row(st):
    m = machine(st)
    ranging = dict(width=10, mid_slope="0.1", efficiency="0.3", crossings=3, both_bands_recently=True,
                   weave=True, ema100_move=1)
    assert run(m, [(0, F(0, **ranging)), (1, F(1)), (2, F(2, **ranging))]) == []     # broken by candle 1
    (ch,) = run(m, [(3, F(3, **ranging))])
    assert ch.state == RANGING
    narrow = dict(width=6, mid_slope="0.1", quiet=True, avg_body=2, colour_ratio="1.5")
    assert run(m, [(4, F(4, **narrow))]) == []
    (ch,) = run(m, [(5, F(5, **narrow))])
    assert ch.state == CONSOLIDATION


def test_a_range_breaks_out_only_after_2_closes_beyond_the_same_band(st):
    m = machine(st)
    ranging = dict(width=10, mid_slope="0.1", efficiency="0.3", crossings=3, both_bands_recently=True,
                   weave=True, ema100_move=1)
    run(m, [(0, F(0, **ranging)), (1, F(1, **ranging))])
    assert m.now.state == RANGING
    assert run(m, [(2, F(2, c=11660, upper=11656))]) == []
    (ch,) = run(m, [(3, F(3, c=11661, upper=11656))])
    assert (ch.state, ch.direction) == (EMERGING, UP) and "2 closes above the band" in ch.reason


# ---- possible reversal ------------------------------------------------------------------------

def far_down(st):
    """A down trend that has moved more than 30 pips since it started."""
    m = trend(st)
    run(m, [(3, F(3, c=11612, l=11610, ema100=11640))])
    return m


def test_a_reversal_candle_after_a_30_pip_move_is_a_possible_reversal(st):
    m = far_down(st)
    (ch,) = run(m, [(4, F(4, c=11615, ema100=11640))], {4: [ev(7, REVERSAL, BUY, OPEN, "reversal candle O ...")]})
    assert (ch.state, ch.direction, ch.previous_state) == (POSSIBLE_REVERSAL, UP, TREND)
    assert ch.reason.startswith("reversal candle after a down move of 40.0 pips")
    assert m.now.strategies_allowed == ("Bollinger band bounce",)
    assert any("MACD histogram" in e for e in ch.evidence)                  # section 2.6 signs recorded


def test_no_possible_reversal_before_the_trend_has_moved_30_pips(st):
    m = trend(st)                                                          # moved 13 pips
    assert run(m, [(3, F(3, c=11640, ema100=11660))], {3: [ev(7, REVERSAL, BUY, OPEN)]}) == []
    assert m.now.state == TREND


def test_a_possible_reversal_goes_back_to_the_trend_on_a_new_low(st):
    m = far_down(st)
    run(m, [(4, F(4, c=11615, ema100=11640))], {4: [ev(7, REVERSAL, BUY, OPEN)]})
    (ch,) = run(m, [(5, F(5, c=11609, l=11608, ema100=11640))])
    assert (ch.state, ch.direction, ch.trend_type) == (TREND, DOWN, SLOW_GRIND)
    assert ch.reason == "the down trend carried on: new low 11608.0"


def test_a_possible_reversal_confirmed_becomes_an_emerging_trend_the_other_way(st):
    m = far_down(st)
    run(m, [(4, F(4, c=11615, ema100=11640))], {4: [ev(7, REVERSAL, BUY, OPEN)]})
    (ch,) = run(m, [(5, F(5, c=11620, ema100=11640))], {5: [ev(7, CONFIRMATION, BUY, OPEN, "closed above")]})
    assert (ch.state, ch.direction) == (EMERGING, UP) and ch.reason == "the reversal was confirmed: closed above"


def test_a_possible_reversal_whose_setup_expires_goes_back_to_the_trend(st):
    m = far_down(st)
    run(m, [(4, F(4, c=11615, ema100=11640))], {4: [ev(7, REVERSAL, BUY, OPEN)]})
    (ch,) = run(m, [(5, F(5, c=11614, ema100=11640))], {5: [ev(7, EXPIRED, BUY, OPEN)]})
    assert (ch.state, ch.direction) == (TREND, DOWN)


# ---- the tracker: start-up replay and records ---------------------------------------------------

def _make_store(st, days=2):
    """Made-up candles: a quiet stretch, a range, a fall and a bounce, from the previous Friday."""
    store = CandleStore(st.candles.folder, 30)
    rnd = random.Random(7)
    t, price = datetime(2026, 10, 30, 12, 0, tzinfo=UTC), 11650.0
    end = OPEN + timedelta(days=days)
    i = 0
    while t < end:
        if datetime(2026, 10, 30, 21, tzinfo=UTC) <= t < OPEN:          # closed
            t += FIVE
            continue
        drift = -0.6 if 300 < i < 420 else (0.5 if 500 < i < 560 else 0)
        price += drift + 3 * math.sin(i / 9) * 0.3 + rnd.uniform(-1.2, 1.2)
        o = price - rnd.uniform(-1, 1)
        h, lo = max(o, price) + rnd.uniform(0, 1.5), min(o, price) - rnd.uniform(0, 1.5)
        q = lambda x: D(str(round(x, 1)))  # noqa: E731
        store.add(Candle("5m", t, t + FIVE, q(o) + 1, q(h) + 1, q(lo) + 1, q(price) + 1,
                         q(o), q(h), q(lo), q(price)))
        t += FIVE
        i += 1
    return store, end


def test_the_start_up_replay_reaches_exactly_the_state_of_a_run_that_never_stopped(st):
    store, end = _make_store(st)
    never_stopped = StateTracker(st, store)
    t = OPEN
    while t <= end:
        never_stopped.advance(t)                 # live: every 15 minutes, taking the new candles
        t += 3 * FIVE
    replayed = StateTracker(st, store)
    replayed.replay(end)                         # start-up after a stop: replay the week
    restarted = StateTracker(st, store)
    restarted.replay(OPEN + timedelta(hours=20))     # stopped part-way, started again, carried on
    restarted.advance(end)
    want = [c.as_dict() for c in never_stopped.changes]
    assert len(want) >= 3                        # the made-up week has state changes to compare
    for other in (replayed, restarted):
        assert [c.as_dict() for c in other.changes] == want
        assert vars(other.machine.now) == vars(never_stopped.machine.now)


def test_every_state_change_is_recorded_once_even_after_a_restart(st):
    store, end = _make_store(st)
    a = StateTracker(st, store, record=True)
    a.replay(end)
    rows = a.recorded()
    assert [r["time_utc"] for r in rows] == [c.as_dict()["time_utc"] for c in a.changes]
    assert set(rows[0]) == {"time_utc", "state", "direction", "trend_type", "previous_state",
                            "previous_direction", "reason", "evidence"}
    StateTracker(st, store, record=True).replay(end)          # a restart replays the week again
    assert a.recorded() == rows                               # nothing recorded twice
    current = json.loads((a.folder / "current.json").read_text())
    assert current["state"] == a.machine.now.state and "strategies_allowed" in current


def test_a_new_week_starts_fresh(st):
    store, end = _make_store(st)
    t = StateTracker(st, store)
    t.replay(end)
    t.advance(datetime(2026, 11, 8, 20, tzinfo=UTC))          # still last week's (closed) session
    assert t.week_open == OPEN
    t.advance(datetime(2026, 11, 8, 21, 2, tzinfo=UTC))       # this week's open
    assert t.week_open == datetime(2026, 11, 8, 21, tzinfo=UTC)
    assert (t.machine.now.state, t.changes) == (CONSOLIDATION, [])


def test_the_tracker_refuses_another_pairs_store(st, tmp_path):
    other = CandleStore(tmp_path / "x" / "EURJPY", 30)
    with pytest.raises(ValueError, match="Pair mix-up"):
        StateTracker(st, other)
