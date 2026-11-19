"""Technical tests for the market-phase RESEARCH model (planner/phase.py; owner's brief "Market Phase Intelligence",
18 November 2026). Observe only: nothing here is wired into the live planner, and these tests also check that it is
not. Built from hand-made 4-hour swings and indicator values, so each rule is checked on its own."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace

import pytest

from config.settings_loader import load_settings
from planner.measure import Frame
from planner.phase import (BEARISH, BULLISH, CONSOLIDATION, COUNTERTREND, DEFAULT, NEUTRAL, NO_VIEW, TREND_ALIGNED,
                           UNSUPPORTED, PhaseInputs, PhaseView, assess_phase, classify_trade, dominant, meaningful,
                           opposing, v1_direction)
from planner.structure import Swing
from planner.zones import MAJOR, MINOR, MODERATE, MOVING_AVERAGE, PIVOT, PSYCHOLOGICAL, STRUCTURE, MapLevel, Zone
from prices.model import Candle

UTC = timezone.utc
S = load_settings().for_pair("GBPUSD")
T0 = datetime(2026, 10, 5, 0, 0, tzinfo=UTC)
ROOT = Path(__file__).resolve().parents[2]


def c4(i, o, h, l, c):
    t = T0 + timedelta(hours=4 * i)
    o, h, l, c = (D(str(x)) for x in (o, h, l, c))
    return Candle("4h", t, t + timedelta(hours=4), o + 1, h + 1, l + 1, c + 1, o, h, l, c)


def sw(kind, price, i):
    t = T0 + timedelta(hours=4 * i)
    return Swing(kind, D(str(price)), "4h", t, t + timedelta(hours=16), i)


def h4_frame(closes, emas=None):
    """A 4-hour frame: candles with the given closes, and EMA values for the LAST candle: emas = {period: value} or
    a dict period -> list (for the EMA100 slope)."""
    cs = [c4(i, x, x + 2, x - 2, x) for i, x in enumerate(closes)]
    ema = {}
    for p, v in (emas or {}).items():
        vals = v if isinstance(v, list) else [v] * len(cs)
        ema[p] = {c.start: D(str(vals[k])) for k, c in enumerate(cs[-len(vals):])} if isinstance(v, list) else {c.start: D(str(v)) for c in cs}
    return Frame("4h", cs, ema)


BEAR_EMAS = {7: 13150, 13: 13160, 21: 13170, 100: [13320, 13316, 13312, 13308, 13304, 13300, 13296]}
BULL_EMAS = {7: 13250, 13: 13240, 21: 13230, 100: [13080, 13084, 13088, 13092, 13096, 13100, 13104]}
ADR = D("70.3")                                       # 18 November's ADR: tolerance max(5, 0.15 x 70.3) = 10.5 pips


def swings_18_nov(high_new="13227.9"):
    """The 18 November 08:00 swings: highs 13224.5 then 13227.9 (3.4 pips higher), lows 13312.2 then 13168."""
    return [sw("high", "13224.5", 2), sw("low", "13312.2", 0), sw("low", "13168", 6), sw("high", high_new, 10)]


# ---- A. dominant direction ----------------------------------------------------------------------------------------------

def test_tolerance_is_the_planners_own_zone_width():
    assert DEFAULT.tolerance(S, ADR) == D("0.15") * ADR                  # 10.545 points
    assert DEFAULT.tolerance(S, D(20)) == D(5)                            # the 5-pip floor (line_up_within_pips)
    assert replace(DEFAULT, use_tolerance=False).tolerance(S, ADR) == 0


def test_a_marginal_higher_high_does_not_erase_consistent_bearish_evidence():
    f = h4_frame([13200] * 14, BEAR_EMAS)
    dv = dominant(S, f, swings_18_nov(), ADR)
    assert dv.v1_direction == NEUTRAL                                     # V1: "mixed" is an absolute veto
    assert dv.direction == BEARISH and dv.structure_vote == -1            # tolerant: equal highs, lower lows
    assert dv.marginal["highs"] == {"raw": "higher", "with_tolerance": "equal", "difference_pips": "3.4"}
    assert any("marginal violation" in e for e in dv.evidence)


def test_a_significant_higher_high_is_a_real_conflict_and_stays_neutral():
    f = h4_frame([13200] * 14, BEAR_EMAS)
    dv = dominant(S, f, swings_18_nov(high_new="13250.0"), ADR)          # 25.5 pips higher: beyond the tolerance
    assert dv.marginal is None and dv.structure_vote == 0 and dv.direction == NEUTRAL


def test_conflicting_ema_evidence_keeps_a_marginal_structure_neutral():
    f = h4_frame([13200] * 14, {7: 13250, 13: 13240, 21: 13230, 100: [13300] * 7})   # EMAs up, flat EMA100, close below it
    dv = dominant(S, f, swings_18_nov(), ADR)
    assert dv.structure_vote == -1 and dv.direction == NEUTRAL           # -1 +1 -1 +0 = -1: not enough


def test_the_structure_can_never_be_outvoted_by_the_emas():
    up = [sw("low", "13100", 0), sw("high", "13200", 2), sw("low", "13150", 6), sw("high", "13260", 10)]
    f = h4_frame([13200] * 14, BEAR_EMAS)                                 # every EMA vote bearish, structure intact
    dv = dominant(S, f, up, ADR)
    assert dv.structure_vote == 2 and dv.direction != BEARISH


def test_a_break_of_structure_resolves_a_mixed_sequence():
    # higher high (by 25.5, beyond the tolerance) then a 4-hour close 3 pips below the latest swing low 13168
    closes = [13200] * 11 + [13190, 13170, 13164]
    f = h4_frame(closes, BEAR_EMAS)
    dv = dominant(S, f, swings_18_nov(high_new="13250.0"), ADR)
    assert dv.break_of_structure["way"] == "down" and dv.structure_vote == -1 and dv.direction == BEARISH
    off = dominant(S, f, swings_18_nov(high_new="13250.0"), ADR, replace(DEFAULT, break_of_structure=False))
    assert off.direction == NEUTRAL


def test_a_confirmed_close_beyond_the_last_lower_high_is_a_structural_reversal_not_a_direction():
    down = [sw("high", "13300", 2), sw("low", "13200", 6), sw("high", "13260", 10), sw("low", "13150", 12)]
    f = h4_frame([13200] * 13 + [13264], BEAR_EMAS)                      # close 4 pips above 13260
    dv = dominant(S, f, down, ADR)
    assert dv.broken_against["way"] == "up" and dv.direction == NEUTRAL and dv.v1_direction == "TRANSITIONAL"


def test_the_mixed_structure_consensus_option_is_off_by_default():
    f = h4_frame([13200] * 14, BEAR_EMAS)
    sws = swings_18_nov(high_new="13250.0")
    assert dominant(S, f, sws, ADR, replace(DEFAULT, break_of_structure=False)).direction == NEUTRAL
    assert dominant(S, f, sws, ADR, replace(DEFAULT, break_of_structure=False, mixed_allows_ema_consensus=True)).direction == BEARISH


def test_too_few_swings_is_neutral():
    f = h4_frame([13200] * 14, BEAR_EMAS)
    assert dominant(S, f, [sw("high", "13300", 2)], ADR).direction == NEUTRAL


def mirror_swing(s):
    return Swing("low" if s.kind == "high" else "high", D(26400) - s.price, s.timeframe, s.candle_utc, s.known_utc, s.index)


def test_direction_is_symmetrical():
    f_bear = h4_frame([13200] * 14, BEAR_EMAS)
    f_bull = h4_frame([13200] * 14, BULL_EMAS)
    bear = dominant(S, f_bear, swings_18_nov(), ADR)
    bull = dominant(S, f_bull, [mirror_swing(s) for s in swings_18_nov()], ADR)
    assert (bear.direction, bear.structure_vote, bear.score) == (BEARISH, -1, -4)
    assert (bull.direction, bull.structure_vote, bull.score) == (BULLISH, 1, 4)


@pytest.mark.parametrize("hs,ls,expected", [
    (("13300", "13260"), ("13200", "13150"), BEARISH), (("13260", "13300"), ("13150", "13200"), BULLISH),
    (("13260", "13300"), ("13200", "13150"), NEUTRAL), (("13300", "13260"), ("13150", "13200"), NEUTRAL)])
def test_v1_direction_reproduces_the_live_rule(hs, ls, expected):
    highs = [sw("high", hs[0], 2), sw("high", hs[1], 10)]
    lows = [sw("low", ls[0], 6), sw("low", ls[1], 12)]
    assert v1_direction(highs, lows, False) == expected


# ---- opposing levels ------------------------------------------------------------------------------------------------------

def L(price, name, fam, kind, dw=False, fixed=True):
    return MapLevel(D(str(price)), name, fam, "1h", kind, T0, dw, fixed)


def Z(low, high, klass, members):
    fams = sorted({m.family for m in members})
    return Zone(D(str(low)), D(str(high)), members, fams, klass, any(m.daily_or_weekly for m in members))


EMA_ONLY = Z(13155, 13156, MINOR, [L(13155.5, "H1 EMA21", MOVING_AVERAGE, "moving average", fixed=False)])
ROUND_AND_HOURLY = Z(13150, 13152, MODERATE, [L(13150, "round number", PSYCHOLOGICAL, "psychological", fixed=False),
                                               L(13151, "hourly swing low", STRUCTURE, "hourly swing")])
DAILY = Z(13162.2, 13172.3, MAJOR, [L(13168, "previous day low", "session", "previous day high/low", True),
                                     L(13172.3, "daily S1", PIVOT, "daily R/S", True),
                                     L(13168, "4-hour swing low", STRUCTURE, "4-hour swing")])


def test_a_lone_moving_average_or_intraday_detail_is_not_meaningful_but_a_daily_level_is():
    assert not meaningful(EMA_ONLY) and not meaningful(ROUND_AND_HOURLY) and meaningful(DAILY)
    assert meaningful(ROUND_AND_HOURLY, strict=False)                     # the loose alternative would accept it


def test_the_first_meaningful_level_is_structural_not_the_nearest_indicator():
    first, obstacle = opposing(S, [ROUND_AND_HOURLY, EMA_ONLY, DAILY], [m for z in (EMA_ONLY, DAILY) for m in z.members],
                               D("13149"), upward=True, min_gap=D(3), extreme=D("13148"))
    assert first is DAILY and obstacle.name == "H1 EMA21"


def test_the_zone_the_move_launched_from_is_not_the_opposing_level():
    launch = Z(13146, 13152, MAJOR, DAILY.members)
    first, _ = opposing(S, [launch, DAILY], None, D("13150"), upward=True, min_gap=D(3), extreme=D("13148"))
    assert first is DAILY


def test_opposing_levels_are_symmetrical_for_a_sell_correction():
    sup = Z(13228, 13238, MAJOR, DAILY.members)
    first, _ = opposing(S, [sup], None, D("13251"), upward=False, min_gap=D(3), extreme=D("13252"))
    assert first is sup


# ---- classification never authorises ------------------------------------------------------------------------------------

def view(direction, phase, countertrend=None, context=(), recent=False):
    dv = SimpleNamespace(direction=direction)
    v = PhaseView(T0, dv, phase, [])
    v.countertrend = countertrend
    v.facts = {"exhaustion_context": list(context), "recent_extreme": recent}
    return v


CT_OK = {"room_sufficient": True, "first_meaningful": {"low": "13162.2", "high": "13172.3"},
         "corrective_destination": "13162.2", "room_pips_after_spread": "12.0"}


def test_a_corrective_buy_coexists_with_a_bearish_direction_and_authorises_nothing():
    v = view(BEARISH, "EXHAUSTION", CT_OK)
    label, why = classify_trade(v, "buy")
    assert label == COUNTERTREND and "BEARISH" in why
    assert v.direction.direction == BEARISH and v.authorises is False


def test_a_buy_with_no_exhaustion_is_unsupported_and_neutral_has_no_view():
    assert classify_trade(view(BEARISH, "TREND_IMPULSE", CT_OK), "buy")[0] == UNSUPPORTED
    assert classify_trade(view(NEUTRAL, CONSOLIDATION), "buy")[0] == NO_VIEW


def test_a_reversal_pattern_can_supply_the_turn_only_with_exhaustion_context():
    assert classify_trade(view(BEARISH, "TREND_IMPULSE", CT_OK, ("extension_from_ema21", "at_support"), True), "buy", True)[0] == COUNTERTREND
    assert classify_trade(view(BEARISH, "TREND_IMPULSE", CT_OK, ("extension_from_ema21",), True), "buy", True)[0] == UNSUPPORTED
    assert classify_trade(view(BEARISH, "TREND_IMPULSE", CT_OK, ("extension_from_ema21", "at_support"), True), "buy", False)[0] == UNSUPPORTED


def test_insufficient_room_is_recognised_but_unsupported():
    ct = dict(CT_OK, room_sufficient=False, room_pips_after_spread="-0.7", room_needed_pips="10.0")
    label, why = classify_trade(view(BEARISH, "EXHAUSTION", ct), "buy")
    assert label == UNSUPPORTED and "recognised as a correction" in why


def test_a_trend_aligned_trade_in_exhaustion_carries_a_caution():
    label, why = classify_trade(view(BEARISH, "EXHAUSTION"), "sell")
    assert label == TREND_ALIGNED and "caution" in why


# ---- missing or stale data ---------------------------------------------------------------------------------------------

def test_missing_candles_or_adr_give_consolidation_with_the_reason():
    f = h4_frame([13200] * 14, BEAR_EMAS)
    empty = Frame("1h", [], {})
    v = assess_phase(S, PhaseInputs(T0, f, empty, swings_18_nov(), [], ADR))
    assert v.phase == CONSOLIDATION and "no finished hourly or 5-minute candles" in v.evidence[0]
    one = [Candle("1h", T0, T0 + timedelta(hours=1), *(D(x) for x in ("13201", "13203", "13199", "13201", "13200", "13202", "13198", "13200")))]
    five = [Candle("5m", T0 + timedelta(hours=1), T0 + timedelta(hours=1, minutes=5),
                   *(D(x) for x in ("13201", "13203", "13199", "13201", "13200", "13202", "13198", "13200")))]
    v = assess_phase(S, PhaseInputs(T0, f, Frame("1h", one, {}), swings_18_nov(), five, None))
    assert v.phase == CONSOLIDATION and v.evidence == ["no ADR yet"] and v.authorises is False


# ---- the live planner is untouched ---------------------------------------------------------------------------------------

def test_nothing_in_production_imports_the_research_model():
    for path in list((ROOT / "planner").glob("*.py")) + list((ROOT / "dashboard").glob("*.py")) + \
            list((ROOT / "trading").glob("*.py")) + list((ROOT / "strategies").rglob("*.py")) + list((ROOT / "prices").glob("*.py")):
        if path.name == "phase.py":
            continue
        assert "planner.phase" not in path.read_text() and "from planner import phase" not in path.read_text(), path


def test_no_setting_or_switch_was_added():
    assert "phase" not in (ROOT / "config" / "settings.toml").read_text().lower().replace("trend_phase", "")
    assert "PHASE" not in (ROOT / "config" / "switches.py").read_text()
