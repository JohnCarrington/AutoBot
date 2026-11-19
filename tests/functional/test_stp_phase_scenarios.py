"""Functional tests for the market-phase RESEARCH model (planner/phase.py; owner's brief "Market Phase Intelligence",
18 November 2026): the trading interpretation it gives, on made-up markets built exactly as the price service builds
candles (tests/planner_helpers.py, the same markets as the V1 planner's scenarios), and on the REAL candles of
18 November 2026 (read only; skipped away from the server). Observe only: nothing authorises, opens or reverses a trade.

Made-up endings after the V1 scenarios' downtrend (110-pip falls, 55-pip rallies):
  drop_bounce       a new low that overshoots (120 pips in 8 hours), then a 25-pip bounce;
  drop_bounce_cont  the same, the bounce rejected and price falling again;
  impulse           the overshooting new low, still falling;
  reversal          a rally that closes well above the last lower high.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal as D
from functools import lru_cache

import pytest

from config.settings_loader import load_settings
from planner.assess import plan_at
from planner.phase import (BEARISH, BULLISH, COUNTERTREND, COUNTERTREND_CORRECTION, EXHAUSTION, NEUTRAL,
                           RESISTANCE_TEST, STRUCTURAL_REVERSAL, TREND_ALIGNED, TREND_CONTINUATION, TREND_IMPULSE,
                           UNSUPPORTED, assess_phase, classify_trade)
from prices.store import CandleStore
from research.stp_phase.history import exact_inputs
from tests.functional.test_planner_scenarios import START, S, waypoints
from tests.planner_helpers import market, mirrored

UTC = timezone.utc
ENDS = {"drop_bounce": ((22, -110), (36, -55), (44, -175), (47, -150)),
        "drop_bounce_cont": ((22, -110), (36, -55), (44, -175), (48, -140), (54, -165)),
        "impulse": ((22, -110), (36, -55), (44, -175)),
        "reversal": ((22, -110), (50, 60), (60, 40))}
MIRROR = {BEARISH: BULLISH, BULLISH: BEARISH, NEUTRAL: NEUTRAL}


@lru_cache(maxsize=None)
def store(name, bull=False):
    st = market(S, START, waypoints(list(ENDS[name])))
    return mirrored(st) if bull else st


def at_end(name, bull=False, t=None):
    st = store(name, bull)
    t = t or st.by_tf["5m"][-1].end
    inp, _ = exact_inputs(S, st, t)
    return assess_phase(S, inp)


# ---- the brief's sequence: impulse -> exhaustion/correction -> continuation -----------------------------------------------

def test_a_valid_corrective_buy_coexists_with_a_bearish_dominant_trend():
    v = at_end("drop_bounce")
    assert v.direction.direction == BEARISH                              # the dominant trend is NOT reclassified
    assert v.phase in (EXHAUSTION, COUNTERTREND_CORRECTION)
    assert v.opportunity == COUNTERTREND and v.opportunity_trade == "BUY"
    label, why = classify_trade(v, "buy", reversal_trigger=True)
    assert label == COUNTERTREND and "BEARISH" in why
    ct = v.countertrend
    assert ct["first_meaningful"] and D(ct["corrective_destination"]) > D(v.facts["price"])
    assert D(ct["invalidation_price"]) < D(v.facts["impulse_extreme"])  # invalidation beyond the low
    assert ct["room_sufficient"] and D(ct["room_pips_after_spread"]) >= D(ct["room_needed_pips"])


def test_the_corrective_buy_is_never_authorised_and_no_sell_is_initiated():
    v = at_end("drop_bounce")
    d = v.as_dict()
    assert d["authorises"] is False and v.countertrend["authorises"] is False
    assert v.countertrend["return_to_trend"]["authorises"] is False
    assert "independently valid strategy SELL trigger" in v.countertrend["return_to_trend"]["needs"]
    assert "never a reversal" in v.countertrend["return_to_trend"]["needs"]
    assert v.continuation is None                                        # no SELL while the correction runs


def test_return_to_trend_after_the_correction_is_rejected():
    v = at_end("drop_bounce_cont")
    assert v.direction.direction == BEARISH and v.phase == TREND_CONTINUATION
    assert v.opportunity == TREND_ALIGNED and v.opportunity_trade == "SELL"
    assert D(v.continuation["invalidation_price"]) == D(v.facts["corrective_extreme"]) + 3   # 3 pips beyond C
    assert v.continuation["authorises"] is False and "independently valid" in v.continuation["needs"]
    assert classify_trade(v, "buy", True)[0] == UNSUPPORTED             # the correction is over: no corrective buy


def test_an_impulse_still_extending_is_not_a_correction():
    v = at_end("impulse")
    assert v.direction.direction == BEARISH and v.phase == TREND_IMPULSE and v.opportunity == TREND_ALIGNED
    assert classify_trade(v, "buy", reversal_trigger=False)[0] == UNSUPPORTED   # a non-reversal buy: no


def test_a_genuine_reversal_is_a_structural_reversal_not_a_correction():
    v = at_end("reversal")
    assert v.phase == STRUCTURAL_REVERSAL and v.direction.direction == NEUTRAL
    assert v.direction.v1_direction == "TRANSITIONAL"                    # the same event V1 already recognises


@pytest.mark.parametrize("name", ["drop_bounce", "drop_bounce_cont", "impulse", "reversal"])
def test_bullish_and_bearish_interpretations_are_mirror_images(name):
    bear, bull = at_end(name), at_end(name, bull=True)
    assert bull.direction.direction == MIRROR[bear.direction.direction]
    assert bull.phase == bear.phase.replace("RESISTANCE_TEST", "SUPPORT_TEST")
    assert (bull.opportunity, {"BUY": "SELL", "SELL": "BUY", None: None}[bull.opportunity_trade]) == \
        (bear.opportunity, bear.opportunity_trade)


@pytest.mark.parametrize("name", ["drop_bounce", "drop_bounce_cont", "reversal"])
def test_the_v1_rule_inside_the_model_matches_the_live_planner(name):
    st = store(name)
    t = st.by_tf["5m"][-1].end
    assert at_end(name).direction.v1_direction == plan_at(S, st, t, calendar=[]).direction


def test_no_look_ahead_the_view_at_a_time_is_the_same_with_or_without_later_candles():
    st = store("drop_bounce_cont")
    t = st.by_tf["5m"][-1].end - (st.by_tf["5m"][-1].end - st.by_tf["5m"][-80].end)     # 80 candles before the end
    full, _ = exact_inputs(S, st, t)
    cut, _ = exact_inputs(S, st.until(t), t)
    a, b = assess_phase(S, full).as_dict(), assess_phase(S, cut).as_dict()
    assert a == b
    assert all(c.end <= t for c in full.h1.candles + full.h4.candles + full.fives)


# ---- REAL candles, Wednesday 18 November 2026 --------------------------------------------------------------------------

BASE = load_settings().for_pair("GBPUSD")
real = pytest.mark.skipif(not (BASE.candles.folder / "5m").is_dir(), reason="the real candle store is only on the server")
T = lambda h, m, s=0: datetime(2026, 11, 18, h, m, s, tzinfo=UTC)          # noqa: E731  (UK time = UTC in November)


@lru_cache(maxsize=None)
def real_view(h, m, s=0):
    st = CandleStore(BASE.candles.folder, BASE.candles.compress_after_days)
    inp, _ = exact_inputs(BASE, st, T(h, m, s))
    return assess_phase(BASE, inp)


@real
def test_18_november_the_marginal_swing_no_longer_erases_the_bearish_direction():
    v = real_view(8, 0, 4)
    assert v.direction.v1_direction == NEUTRAL                           # what the live planner said
    assert v.direction.direction == BEARISH and v.direction.marginal["highs"]["difference_pips"] == "3.4"
    for h, m in ((9, 30), (12, 37), (16, 20)):
        assert real_view(h, m).direction.direction == BEARISH


@real
def test_18_november_the_0730_asian_range_breakout_sell_is_trend_aligned_continuation():
    v = real_view(7, 30, 2)
    assert v.direction.direction == BEARISH and v.phase == TREND_CONTINUATION
    assert classify_trade(v, "sell")[0] == TREND_ALIGNED


@real
def test_18_november_the_0930_bounce_buy_is_read_as_a_correction_not_a_trend_change_and_not_authorised():
    v = real_view(9, 30, 1)
    assert v.direction.direction == BEARISH                              # the buy does not flip the trend
    label, why = classify_trade(v, "buy", reversal_trigger=True)
    assert label != TREND_ALIGNED and "recognised as a correction" in why   # context recognised; room judged
    fm = v.countertrend["first_meaningful"]
    assert any("previous day low 13168" in x for x in fm["levels"])      # the resistance was identifiable at entry
    assert v.as_dict()["authorises"] is False


@real
def test_18_november_afternoon_sells_are_trend_aligned_and_the_correction_tested_resistance():
    assert real_view(12, 37, 37).phase in (RESISTANCE_TEST, TREND_CONTINUATION)
    assert classify_trade(real_view(12, 37, 37), "sell")[0] == TREND_ALIGNED
    assert classify_trade(real_view(15, 44, 6), "sell")[0] == TREND_ALIGNED
