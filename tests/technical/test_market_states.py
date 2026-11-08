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
from rejection.watch import BOUNCE, BUY, CONFIRMATION, EXPIRED, REVERSAL, SELL, TRIGGER, Event
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
    base = dict(candle=candle, o=o, h=h, l=lo, c=c, upper=c + 6, middle=c, lower=c - 6, width=D(16),
                narrowing_for=0, closed_outside=False, no_close_outside=False,
                mid_slope=D(1), upper_slope=D(1), lower_slope=D(1), ema7=c, ema13=c, ema21=c, ema100=c,
                stack=None, stacked_for=0, weave=True, ema100_move=D(5),
                reached_upper=False, reached_lower=False, both_bands_recently=False,
                avg_body=D(4), colour_ratio=D(3), body=D(1), range_=D(2), spike=False, green_share=D("0.5"),
                red_share=D("0.5"), widening=D(1), fan=D(1), closes_on_upper=0, closes_on_lower=0,
                macd_hist=D("-0.5"), rsi=D(40))
    whole = ("stacked_for", "closes_on_upper", "closes_on_lower", "narrowing_for")
    base.update({k: (D(str(v)) if isinstance(v, (int, float, str)) and not isinstance(v, bool)
                     and k not in whole and k != "stack" else v) for k, v in kw.items()})
    return Features(**base)


# Ranging (design 2.2, owner's values): bands 6 to 18 pips wide, upper and lower band flat
# (under 0.2 pips a candle), both bands reached, EMAs weaving, 100 EMA flat.
RANGING_OK = dict(width=10, mid_slope="0.05", upper_slope="0.1", lower_slope="-0.1", both_bands_recently=True,
                  weave=True, ema100_move=1)


def ev(n, kind, direction, t, note="note"):
    return Event(n, BOUNCE, direction, kind, t, None, note)


def setups(**by_id):
    return lambda i: by_id.get(str(i)) or SimpleNamespace(pierced=[{"what": "lower Bollinger band"}])


def at_level(what="pivot", price=11660, edge=11660):
    """A rejection setup that pierced a level (its piercing candle's high and low at `edge`)."""
    pierce = F(0, c=edge, h=edge, l=edge).candle
    return SimpleNamespace(pierced=[{"what": what, "price": D(str(price))}], pierce=pierce)


PIVOT = at_level()
BAND = SimpleNamespace(pierced=[{"what": "upper Bollinger band", "price": D(11660)}], pierce=F(0).candle)


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
    """A machine in an emerging down trend started at `start`, from a sell rejection at the pivot
    11660 (so it is cancelled only by closes back above 11660)."""
    m = machine(st)
    run(m, [(0, F(0, c=start))], {0: [ev(1, CONFIRMATION, SELL, OPEN)]}, setups(**{"1": PIVOT}))
    assert (m.now.state, m.now.direction) == (EMERGING, DOWN)
    return m


def breakout_downtrend(st, start=11650):
    """An emerging down trend from a close below the lower band."""
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
    assert m.now.strategies_allowed[0] == "EMA pullback"


def test_a_level_rejection_starts_an_emerging_trend_but_a_band_only_rejection_does_not(st):
    m = machine(st)
    t = OPEN
    assert run(m, [(0, F(0))], {0: [ev(1, CONFIRMATION, SELL, t)]}, setups(**{"1": BAND})) == []
    (ch,) = run(m, [(1, F(1))], {1: [ev(2, CONFIRMATION, SELL, t, "closed below the reversal low")]},
                setups(**{"2": PIVOT}))
    assert (ch.state, ch.direction) == (EMERGING, DOWN)
    assert ch.reason == "rejected at a level: closed below the reversal low"


# ---- emerging trend --------------------------------------------------------------------

def test_a_breakout_trend_is_cancelled_only_by_2_closes_in_a_row_back_inside_the_bands(st):
    m = breakout_downtrend(st, 11650)                          # broke out below the lower band
    inside = dict(lower=11640, upper=11660)
    assert run(m, [(1, F(1, c=11655, **inside)), (2, F(2, c=11639, l=11648, **inside)),   # in, out again
                   (3, F(3, c=11655, **inside))]) == []
    (ch,) = run(m, [(4, F(4, c=11656, **inside))])
    assert (ch.state, ch.direction) == (CONSOLIDATION, NONE)
    assert "2 closes in a row back inside the Bollinger bands after the breakout" in ch.reason


def level_downtrend(st):
    """An emerging down trend from a sell rejection at the pivot 11660."""
    m = machine(st)
    run(m, [(0, F(0, c=11655))], {0: [ev(1, CONFIRMATION, SELL, OPEN)]}, setups(**{"1": PIVOT}))
    assert (m.now.state, m.now.direction) == (EMERGING, DOWN)
    return m


def test_a_level_trend_is_cancelled_only_by_2_closes_in_a_row_back_beyond_the_level(st):
    m = level_downtrend(st)
    assert run(m, [(1, F(1, c=11661)), (2, F(2, c=11659)), (3, F(3, c=11661))]) == []
    (ch,) = run(m, [(4, F(4, c=11662))])
    assert ch.state == CONSOLIDATION
    assert "2 closes in a row back above the pivot 11660.0 it was rejected at" in ch.reason


def test_an_emerging_trend_is_not_cancelled_by_3_pips_or_the_100_ema(st):
    m = level_downtrend(st)
    # 4 pips back past where it started, and closes above the 100 EMA, but not above the level
    assert run(m, [(i, F(i, c=11659, ema100=11650)) for i in range(1, 6)]) == []
    assert m.now.state == EMERGING


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


def test_the_push_colour_is_measured_by_body_size_not_by_count(st):
    from analyser.features import compute
    t0 = datetime(2026, 11, 4, 10, tzinfo=UTC)
    # 6 candles: 2 big red (10 pips each), 4 small green (1 pip each): 2 of 6 red by count, 83% red by size
    spec = [(-10), 1, 1, (-10), 1, 1]
    candles, p = [], D(11650)
    for i, body in enumerate(spec):
        o, c = p, p + D(body)
        candles.append(Candle("5m", t0 + i * FIVE, t0 + (i + 1) * FIVE, o + 1, max(o, c) + 2, min(o, c), c + 1,
                              o, max(o, c) + 1, min(o, c) - 1, c))
        p = c
    f = compute(candles, st)[-1]
    assert f.red_share == D(20) / D(24) and f.green_share == D(4) / D(24)
    assert st.market_states.push_colour_body_percent == 70


def test_a_strong_push_needs_its_signs_for_2_candles_in_a_row(st):
    m = trend(st)
    assert run(m, [(3, push(3, 11636))]) == []
    (ch,) = run(m, [(4, push(4, 11635))])
    assert (ch.state, ch.trend_type) == (TREND, STRONG_PUSH) and ch.reason.startswith("strong push: 80% of the body size red")


def test_a_trend_ends_after_2_closes_back_past_the_100_ema(st):
    m = trend(st)
    assert run(m, [(3, F(3, c=11660, ema100=11655))]) == []
    (ch,) = run(m, [(4, F(4, c=11661, ema100=11655))])
    assert ch.state == CONSOLIDATION and "back above the 100 EMA" in ch.reason


def test_ranging_and_consolidation_need_2_candles_in_a_row(st):
    m = machine(st)
    ranging = dict(RANGING_OK)
    assert run(m, [(0, F(0, **ranging)), (1, F(1)), (2, F(2, **ranging))]) == []     # broken by candle 1
    (ch,) = run(m, [(3, F(3, **ranging))])
    assert ch.state == RANGING
    narrow = dict(width=6, mid_slope="0.1", no_close_outside=True, avg_body=2, colour_ratio="1.5")
    assert run(m, [(4, F(4, **narrow))]) == []
    (ch,) = run(m, [(5, F(5, **narrow))])
    assert ch.state == CONSOLIDATION


def test_a_range_breaks_out_only_after_2_closes_beyond_the_same_band(st):
    m = machine(st)
    ranging = dict(RANGING_OK)
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


S2 = at_level("S2", 11610, 11610)


def possible(m, i=4):
    return run(m, [(i, F(i, c=11615, ema100=11640))], {i: [ev(7, CONFIRMATION, BUY, OPEN, "closed above")]},
               setups(**{"7": S2}))


def test_a_confirmed_level_rejection_after_a_30_pip_move_is_a_possible_reversal(st):
    m = far_down(st)
    (ch,) = possible(m)
    assert (ch.state, ch.direction, ch.previous_state) == (POSSIBLE_REVERSAL, UP, TREND)
    assert ch.reason.startswith("rejection at a level (S2 11610) confirmed after a down move of 40.0 pips")
    assert m.now.strategies_allowed == ("Bollinger band bounce",)
    assert any("MACD histogram" in e for e in ch.evidence)                  # section 2.6 signs recorded


def test_a_single_opposite_candle_or_a_band_only_rejection_is_not_enough(st):
    m = far_down(st)
    assert run(m, [(4, F(4, c=11615, ema100=11640))], {4: [ev(7, REVERSAL, BUY, OPEN)]},
               setups(**{"7": S2})) == []                                   # a reversal candle alone
    assert run(m, [(5, F(5, c=11615, ema100=11640))], {5: [ev(8, CONFIRMATION, BUY, OPEN)]},
               setups(**{"8": BAND})) == []                                 # confirmed, but at the band only
    assert m.now.state == TREND


def test_no_possible_reversal_before_the_trend_has_moved_30_pips(st):
    m = trend(st)                                                          # moved 4 pips
    assert run(m, [(3, F(3, c=11640, ema100=11660))], {3: [ev(7, CONFIRMATION, BUY, OPEN)]},
               setups(**{"7": S2})) == []
    assert m.now.state == TREND


def test_a_possible_reversal_goes_back_to_the_trend_on_a_new_low(st):
    m = far_down(st)
    possible(m)
    (ch,) = run(m, [(5, F(5, c=11609, l=11608, ema100=11640))])
    assert (ch.state, ch.direction, ch.trend_type) == (TREND, DOWN, SLOW_GRIND)
    assert ch.reason == "the down trend carried on: new low 11608.0"


def test_a_possible_reversal_that_triggers_becomes_an_emerging_trend_the_other_way(st):
    m = far_down(st)
    possible(m)
    (ch,) = run(m, [(5, F(5, c=11620, ema100=11640))], {5: [ev(7, TRIGGER, BUY, OPEN, "price went above")]},
                setups(**{"7": S2}))
    assert (ch.state, ch.direction) == (EMERGING, UP) and ch.reason == "the reversal triggered: price went above"
    assert any("rejected at the S2 11610.0" in e for e in ch.evidence)      # cancelled only back below S2


def test_a_possible_reversal_whose_setup_expires_goes_back_to_the_trend(st):
    m = far_down(st)
    possible(m)
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


# ---- 7 November changes: consolidation width or narrowing, no close outside; an emerging trend replaced ----

CONSOL = dict(mid_slope="0.1", no_close_outside=True, avg_body=2, colour_ratio="1.5")


@pytest.mark.parametrize("width,narrowing,ok", [
    (14, 0, True),             # 14 pips or less
    (14.1, 5, False),          # wider, narrowing for only 5 candles
    (20, 6, True),             # wider, but narrowing for 6 candles in a row
])
def test_consolidation_bands_are_14_pips_or_less_or_narrowing_for_6_candles(st, width, narrowing, ok):
    m = machine(st)
    f = F(0, width=width, narrowing_for=narrowing, **CONSOL)
    assert m.consolidation(f)[0] is ok
    assert (st.market_states.narrow_band_max_pips, st.market_states.narrowing_candles) == (14, 6)


def test_consolidation_needs_no_close_outside_the_bands_for_6_candles(st):
    m = machine(st)
    assert m.consolidation(F(0, width=10, **CONSOL))[0]
    assert not m.consolidation(F(0, width=10, **{**CONSOL, "no_close_outside": False}))[0]


def test_a_trend_runs_out_of_steam_into_consolidation_after_2_candles(st):
    m = trend(st)
    calm = dict(width=10, ema100=11700, **CONSOL)
    assert run(m, [(3, F(3, c=11650, **calm))]) == []
    (ch,) = run(m, [(4, F(4, c=11650, **calm))])
    assert ch.state == CONSOLIDATION and "ran out of steam" in ch.reason


def test_an_opposite_important_level_rejection_replaces_an_emerging_trend(st):
    m = level_downtrend(st)                                       # emerging down from the pivot 11660
    r2 = at_level("round_number", 11650, 11650)
    (ch,) = run(m, [(1, F(1, c=11656))], {1: [ev(2, CONFIRMATION, BUY, OPEN, "closed above")]},
                setups(**{"2": r2}))
    assert (ch.state, ch.direction, ch.previous_direction) == (EMERGING, UP, DOWN)
    assert ch.reason == "rejected at a level against the emerging down trend: closed above"
    assert any("rejected at the round_number 11650.0" in e for e in ch.evidence)


def test_an_opposite_rejection_at_a_band_or_minor_level_does_not_replace_it(st):
    m = level_downtrend(st)
    minor = at_level("london_session_low", 11650, 11650)
    assert run(m, [(1, F(1, c=11656))], {1: [ev(2, CONFIRMATION, BUY, OPEN)]}, setups(**{"2": minor})) == []
    assert run(m, [(2, F(2, c=11656))], {2: [ev(3, CONFIRMATION, BUY, OPEN)]}, setups(**{"3": BAND})) == []
    assert (m.now.state, m.now.direction) == (EMERGING, DOWN)


def test_a_trend_is_not_replaced_by_one_opposite_level_rejection_before_30_pips(st):
    m = trend(st)
    r2 = at_level("round_number", 11650, 11650)
    assert run(m, [(3, F(3, c=11640, ema100=11660))], {3: [ev(2, CONFIRMATION, BUY, OPEN)]},
               setups(**{"2": r2})) == []
    assert m.now.state == TREND


def test_consolidation_ends_an_emerging_trend_after_2_candles_but_ranging_does_not(st):
    m = level_downtrend(st)
    calm = dict(width=10, **CONSOL)
    assert run(m, [(1, F(1, c=11655, **calm))]) == []
    (ch,) = run(m, [(2, F(2, c=11655, **calm))])
    assert ch.state == CONSOLIDATION and ch.reason.startswith("the emerging down trend settled into consolidation")
    m = level_downtrend(st)
    ranging = dict(RANGING_OK)
    assert run(m, [(i, F(i, c=11655, **ranging)) for i in range(1, 5)]) == [] and m.now.state == EMERGING


# ---- in the price service --------------------------------------------------------------------

def test_the_price_service_replays_the_states_at_start_up_and_records_each_change(st, caplog):
    import logging
    from analyser.market_state import StatesUpdater
    caplog.set_level(logging.INFO)
    store, end = _make_store(st)
    u = StatesUpdater(st, store)
    u(OPEN + timedelta(hours=20))                          # start-up: replays the week so far
    assert "Market states replayed from the week's open" in caplog.text
    n = len(u.tracker.recorded())
    u(end)                                                 # later candles: each change recorded and logged
    rows = u.tracker.recorded()
    assert len(rows) > n and [r["time_utc"] for r in rows] == [c.as_dict()["time_utc"] for c in u.tracker.changes]
    assert "Market state: " in caplog.text
    replayed = StateTracker(st, store)
    replayed.replay(end)
    assert vars(replayed.machine.now) == vars(u.tracker.machine.now)     # the same as a fresh replay


def test_a_market_state_problem_never_stops_the_price_service(st):
    from analyser.market_state import StatesUpdater
    warned = []
    broken = SimpleNamespace(market=st.market, candles=st.candles)        # no market_states settings
    StatesUpdater(broken, CandleStore(st.candles.folder, 30), warn=warned.append)(OPEN)
    assert warned and warned[0].startswith("[EURUSD] Market state not updated")


# ---- 7 November: only a strong level starts or replaces an emerging trend ------------------------

def turning(price, group_levels, lined_up):
    """A rejection setup at a turning level, whose lined-up group holds `group_levels`."""
    pierce = F(0, c=price, h=price, l=price).candle
    name = f"turning_high {price}"
    return SimpleNamespace(pierced=[{"what": "turning_high", "price": D(str(price))}], pierce=pierce,
                           lined_up=[{"group": 1, "lined_up": lined_up, "levels": [name, *group_levels]}])


def test_a_turning_level_on_its_own_does_not_start_an_emerging_trend(st):
    m = machine(st)
    alone = turning(11660, ["turning_low 11658.0"], True)            # lines up with another turning level only
    assert run(m, [(0, F(0))], {0: [ev(1, CONFIRMATION, SELL, OPEN)]}, setups(**{"1": alone})) == []
    assert m.now.state == CONSOLIDATION


def test_a_turning_level_lined_up_with_a_strong_level_starts_one(st):
    m = machine(st)
    with_pivot = turning(11660, ["pivot 11662.0"], True)
    (ch,) = run(m, [(0, F(0, c=11655))], {0: [ev(1, CONFIRMATION, SELL, OPEN, "closed below")]},
                setups(**{"1": with_pivot}))
    assert (ch.state, ch.direction) == (EMERGING, DOWN)
    assert any("rejected at the turning_high 11660.0" in e for e in ch.evidence)


def test_a_turning_level_on_its_own_does_not_replace_an_emerging_trend_but_a_lined_up_one_does(st):
    m = level_downtrend(st)                                           # emerging down from the pivot 11660
    alone = turning(11650, ["london_session_low 11649.0"], True)
    assert run(m, [(1, F(1, c=11656))], {1: [ev(2, CONFIRMATION, BUY, OPEN)]}, setups(**{"2": alone})) == []
    assert (m.now.state, m.now.direction) == (EMERGING, DOWN)
    with_s1 = turning(11650, ["S1 11648.0"], True)
    (ch,) = run(m, [(2, F(2, c=11656))], {2: [ev(3, CONFIRMATION, BUY, OPEN, "closed above")]},
                setups(**{"3": with_s1}))
    assert (ch.state, ch.direction, ch.previous_direction) == (EMERGING, UP, DOWN)


@pytest.mark.parametrize("what,price", [("pivot", 11660), ("R2", 11660), ("S3", 11660), ("round_number", 11650),
                                        ("round_number", 11700), ("previous_day_high", 11660),
                                        ("previous_day_low", 11660)])
def test_each_strong_level_type_starts_an_emerging_trend(st, what, price):
    m = machine(st)
    (ch,) = run(m, [(0, F(0, c=11640))], {0: [ev(1, CONFIRMATION, SELL, OPEN)]},
                setups(**{"1": at_level(what, price, price)}))
    assert ch.state == EMERGING


def test_a_session_high_or_low_alone_does_not_start_one(st):
    m = machine(st)
    assert run(m, [(0, F(0))], {0: [ev(1, CONFIRMATION, SELL, OPEN)]},
               setups(**{"1": at_level("london_session_high", 11660, 11660)})) == []



# ---- the ranging check, design 2.2 (owner's values, 7 November 2026) ----------------------------

@pytest.mark.parametrize("width,ok", [("5.9", False), (6, True), (12, True), (18, True), ("18.1", False), (25, False)])
def test_ranging_bands_close_together_from_6_to_18_pips(st, width, ok):
    assert machine(st).ranging(F(0, **{**RANGING_OK, "width": width}))[0] is ok


@pytest.mark.parametrize("band", ["upper_slope", "lower_slope"])
@pytest.mark.parametrize("slope,ok", [("0.19", True), ("-0.19", True), ("0.2", False), ("-0.2", False), ("0.5", False)])
def test_ranging_both_outer_bands_flat_under_0_2_pips_a_candle(st, band, slope, ok):
    assert machine(st).ranging(F(0, **{**RANGING_OK, band: slope}))[0] is ok


def test_ranging_the_middle_band_alone_is_not_the_test(st):
    m = machine(st)
    assert m.ranging(F(0, **{**RANGING_OK, "mid_slope": "0.05", "upper_slope": "0.3", "lower_slope": "-0.2"}))[0] is False
    assert m.ranging(F(0, **{**RANGING_OK, "mid_slope": "0.18", "upper_slope": "0.17", "lower_slope": "0.19"}))[0] is True


@pytest.mark.parametrize("change", [dict(both_bands_recently=False), dict(weave=False), dict(ema100_move=3)])
def test_ranging_keeps_both_bands_reached_the_weave_and_the_flat_100_ema(st, change):
    assert machine(st).ranging(F(0, **{**RANGING_OK, **change}))[0] is False


def test_ranging_no_efficiency_or_crossings_check(st):
    import dataclasses
    names = {f.name for f in dataclasses.fields(F(0))}
    assert not {"efficiency", "crossings"} & names
    assert not {"ranging_max_efficiency_ratio", "efficiency_candles", "ranging_min_crossings",
                "crossing_candles"} & set(vars(st.market_states))


def test_ranging_reason_names_the_numbers(st):
    ok, why = machine(st).ranging(F(0, **RANGING_OK))
    assert ok and "close together: 6 to 18" in why and "upper 0.1, lower -0.1 pips/candle" in why
