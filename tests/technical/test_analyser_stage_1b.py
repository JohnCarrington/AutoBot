"""Technical tests for stage 1b of the analyser control (owner, 18 November 2026; design 2.10), both behind the switch
ANALYSER_USES_HOURLY: (1) the existing trend proof (2.5) watched both ways from ranging and consolidation, the new
extreme measured against the highest high / lowest low since that state began, the trend's start at the opposite
extreme of that state; (2) a 5-minute close at least hourly_read.break_beyond_pips beyond the hourly range counting,
for the analyser and the trend group, as the hourly range breaking that way, cancelled by two closes back inside the
range as it was at the break. Made-up features and candles; never contacts IG."""

from datetime import datetime, timezone
from decimal import Decimal as D
from types import SimpleNamespace

from analyser.hourly_read import (RALLY, RANGING as H_RANGING, SELL_OFF, FiveMinuteBreak, HourlyRead, next_break,
                                  with_break)
from analyser.states import (CONSOLIDATION, DOWN, POSSIBLE_REVERSAL, RANGING, SLOW_GRIND, STRONG_PUSH, TREND, UP,
                             StateMachine)
from strategies.common import BUY, EMA_PULLBACK, LEVEL_REVERSAL, SELL, allowed
from tests.technical.test_analyser_control import BASE, On
from tests.technical.test_market_states import FIVE, OPEN, RANGING_OK, F, proof_candles, run, st  # noqa: F401


class Hourly:
    """Settings with ANALYSER_USES_HOURLY on (or off)."""
    def __init__(self, base, on=True):
        self.base, self.switches = base, SimpleNamespace(analyser_uses_hourly=on)

    def __getattr__(self, name):
        return getattr(self.base, name)


def base_then_proof(st, on=True, state_kw=None):
    """A machine in consolidation (the week's start), a high of 11655 on candle 1, then a failed bounce (candle 2) and
    a new low under stacked EMAs on a falling lower band (candle 3): the trend proof down."""
    m = StateMachine(Hourly(st, on), OPEN)
    kw = state_kw or {}
    out = run(m, [(0, F(0, c=11650, **kw)), (1, F(1, o=11650, c=11652, h=11655, **kw))])
    return m, out + run(m, proof_candles(2, 11649))


# ---- 1. the trend proof from ranging and consolidation ----------------------------------------------------------

def test_the_trend_proof_moves_consolidation_straight_to_trend(st):
    m, (ch,) = base_then_proof(st)
    assert (ch.state, ch.direction, ch.trend_type, ch.previous_state) == (TREND, DOWN, SLOW_GRIND, CONSOLIDATION)
    assert ch.reason.startswith("the trend proof held in consolidation: a bounce failed under the 21 EMA and middle "
                                "band, then a new low 11646.0 on the lower band")
    assert ch.time == OPEN + 3 * FIVE


def test_the_trends_start_is_the_highest_high_since_the_consolidation_began(st):
    """Owner: the start (for the 30-pip possible reversal and the MACD rule) is the opposite extreme of that ranging or
    consolidation, at that candle's time, not the candle the proof holds on."""
    m, (ch,) = base_then_proof(st)
    assert m.start_price == D("11655") and m.trend_start == OPEN + 1 * FIVE
    assert m.extreme == D("11646")
    assert any("the move started at the highest high 11655.0" in e for e in ch.evidence)


def test_switch_off_the_proof_is_not_watched_from_consolidation(st):
    m, out = base_then_proof(st, on=False)
    assert out == [] and m.now.state == CONSOLIDATION


def test_the_proof_holds_whatever_the_hourly_read_says(st):
    m = StateMachine(Hourly(st), OPEN)
    m.hourly = HourlyRead(H_RANGING, None, D("11600"), D("11700"), None, "ranging")
    run(m, [(0, F(0, c=11650)), (1, F(1, o=11650, c=11652, h=11655))])
    (ch,) = run(m, proof_candles(2, 11649))
    assert (ch.state, ch.direction) == (TREND, DOWN)


def test_no_trend_from_consolidation_without_a_failed_bounce_first(st):
    m = StateMachine(Hourly(st), OPEN)
    run(m, [(0, F(0, c=11650))])
    _, (d, drop) = proof_candles(2, 11649)
    assert run(m, [(d, drop)]) == [] and m.now.state == CONSOLIDATION


def test_the_new_extreme_is_measured_since_the_state_began(st):
    """A low of 11640 earlier in the consolidation: a drop to 11646 is not a new low, so no proof."""
    m = StateMachine(Hourly(st), OPEN)
    run(m, [(0, F(0, c=11650, l=11640))])
    assert run(m, proof_candles(2, 11649)) == [] and m.now.state == CONSOLIDATION


def test_from_ranging_up_mirror(st):
    m = StateMachine(Hourly(st), OPEN)
    rng = [(i, F(i, c=11650, **RANGING_OK)) for i in range(0, 3)]
    run(m, rng)
    assert m.now.state == RANGING
    low = run(m, [(3, F(3, o=11650, c=11648, l=11645, **RANGING_OK))])        # the range's lowest low so far
    assert low == []
    dip = F(4, o=11651, c=11649, h=11651, l=11648, ema21=11646, middle=11645, ema100=11630)  # a failed bounce (red)
    rise = F(5, o=11651, c=11653, h=11656, l=11651, upper=11656, reached_upper=True, upper_slope=1, stack="up",
             stacked_for=4, ema7=11652, ema13=11651, ema21=11650, ema100=11630)
    (ch,) = run(m, [(4, dip), (5, rise)])
    assert (ch.state, ch.direction, ch.previous_state) == (TREND, UP, RANGING)
    assert m.start_price == D("11645") and m.trend_start == OPEN + 3 * FIVE


# ---- 2. a 5-minute close beyond the hourly range ---------------------------------------------------------------

S = On(analyser_uses_hourly=True)
T = datetime(2026, 11, 17, 16, 15, tzinfo=timezone.utc)
READ = HourlyRead(H_RANGING, None, D("13172.8"), D("13210.4"), None, "ranging")    # 17 November, 16:00 to 17:00


def test_a_close_3_pips_beyond_the_hourly_range_is_a_break():
    assert next_break(S, READ, None, T, D("13213.3")) is None                     # 2.9 pips above the high
    up = next_break(S, READ, None, T, D("13213.4"))
    assert (up.state, up.low, up.high, up.at) == (RALLY, D("13172.8"), D("13210.4"), T)
    assert next_break(S, READ, None, T, D("13169.8")).state == SELL_OFF


def test_two_closes_in_a_row_back_inside_the_range_at_the_break_cancel_it():
    b = next_break(S, READ, None, T, D("13214.7"))
    b = next_break(S, READ, b, T, D("13210.4"))                                    # on the high: inside, 1
    assert b is not None and b.back == 1
    b = next_break(S, READ, b, T, D("13211.0"))                                    # above the high: not inside
    assert b is not None and b.back == 0
    b = next_break(S, READ, b, T, D("13209.0"))
    assert next_break(S, READ, b, T, D("13200.0")) is None


def test_the_range_is_kept_as_it_was_at_the_break():
    b = next_break(S, READ, None, T, D("13214.7"))
    wider = HourlyRead(H_RANGING, None, D("13172.8"), D("13220.7"), None, "ranging")   # the next hour's range
    b = next_break(S, wider, b, T, D("13215.0"))                                   # inside the new range, not the old
    assert b is not None and b.back == 0 and b.high == D("13210.4")


def test_an_hourly_close_beyond_the_range_lets_the_real_read_take_over():
    b = next_break(S, READ, None, T, D("13214.7"))
    rally = HourlyRead(RALLY, None, D("13172.8"), D("13220.7"), T, "a real rally")
    assert next_break(S, rally, b, T, D("13215.0")) is None
    assert with_break(rally, b) is rally


def test_a_close_beyond_the_other_side_turns_the_break():
    b = next_break(S, READ, None, T, D("13214.7"))
    b = next_break(S, READ, b, T, D("13169.8"))
    assert b.state == SELL_OFF and b.high == D("13210.4")


def test_with_break_counts_as_a_rally_and_leaves_the_read_itself_alone():
    b = next_break(S, READ, None, T, D("13214.7"))
    seen = with_break(READ, b)
    assert seen.state == RALLY and READ.state == H_RANGING
    assert "ANALYSER_USES_HOURLY" in seen.why
    assert with_break(READ, None) is READ


def test_the_trend_group_sees_the_break():
    """HOURLY_READ gate: ranging blocks the EMA pullback; the break counts as a rally, so buys only."""
    s = On(analyser_uses_hourly=True, hourly_read=True)
    state = SimpleNamespace(state=TREND, direction=UP, trend_type=SLOW_GRIND)
    seen = with_break(READ, next_break(S, READ, None, T, D("13214.7")))
    args = (D("13215"), state, D("13190"), D("13190"), READ)
    r, _ = allowed(s, EMA_PULLBACK, BUY, *args)
    assert any("waits for a 5-minute close" in x for x in r)
    r, _ = allowed(s, EMA_PULLBACK, BUY, *args, trend_hourly=seen)
    assert r == []
    r, _ = allowed(s, EMA_PULLBACK, SELL, D("13215"), SimpleNamespace(state=TREND, direction=DOWN, trend_type=None),
                   D("13220"), D("13220"), READ, trend_hourly=seen)
    assert "the hourly chart is in a rally: EMA pullback only buys" in r


def test_the_stage_2_hourly_ranging_rule_stops_applying_after_a_break():
    s = On(analyser_uses_hourly=True, analyser_governs_all=True)
    state = SimpleNamespace(state=RANGING, direction="none", trend_type=None)
    middle = {"furthest": D("13195"), "rejection_close": D("13192")}
    seen = with_break(READ, next_break(S, READ, None, T, D("13214.7")))
    r, _ = allowed(s, LEVEL_REVERSAL, SELL, D("13192"), state, D("13190"), D("13190"), READ, context=middle)
    assert any("opens only at the" in x for x in r)
    r, _ = allowed(s, LEVEL_REVERSAL, SELL, D("13192"), state, D("13190"), D("13190"), READ, context=middle,
                   trend_hourly=seen)
    assert r == []


def test_settings_are_the_existing_ones():
    assert BASE.hourly_read.break_beyond_pips == 3 and BASE.market_states.persistence_candles == 2
    assert isinstance(FiveMinuteBreak(RALLY, D(1), D(2), T, D(3)).back, int)


# ---- 3. no possible reversal from a strong push ----------------------------------------------------------------

def strong_push_down(st, on=True):
    """A trend down from the proof in consolidation (start 11655), set to a strong push, with a low of 11620 (35 pips)."""
    m, _ = base_then_proof(st, on)
    m.now.trend_type = STRONG_PUSH
    m.extreme = D("11620")
    return m


def buy_rejection_at_pivot(m, i):
    from rejection.watch import BUY as R_BUY, CONFIRMATION
    from tests.technical.test_market_states import ev, setups
    pivot = SimpleNamespace(pierced=[{"what": "pivot", "price": D("11622")}],
                            pierce=F(0, c=11622, h=11622, l=11622).candle)
    return run(m, [(i, F(i, c=11623, l=11621, h=11624, ema100=11660))],
               {i: [ev(1, CONFIRMATION, R_BUY, OPEN + i * FIVE)]}, setups(**{"1": pivot}))


def test_a_strong_push_is_not_turned_into_a_possible_reversal(st):
    m = strong_push_down(st)
    assert buy_rejection_at_pivot(m, 10) == [] and m.now.state == TREND


def test_a_slow_grind_still_turns_into_a_possible_reversal(st):
    m = strong_push_down(st)
    m.now.trend_type = SLOW_GRIND
    (ch,) = buy_rejection_at_pivot(m, 10)
    assert (ch.state, ch.direction) == (POSSIBLE_REVERSAL, UP)
    assert m.start_price == D("11655")                         # the start stays the highest high of the consolidation


def test_switch_off_a_strong_push_turns_into_a_possible_reversal_as_before(st):
    m = strong_push_down(st)
    m.uses_hourly = False                                      # the same strong push, the switch off
    (ch,) = buy_rejection_at_pivot(m, 10)
    assert ch.state == POSSIBLE_REVERSAL
