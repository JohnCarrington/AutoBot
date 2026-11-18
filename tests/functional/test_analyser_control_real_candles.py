"""Functional tests for the analyser control, stages 1 to 3 (owner, 18 November 2026; design 2.10 and 6), on the REAL
candles in the candle store (stored candles are never overwritten, so the answers do not change), with all three
switches on unless a test says otherwise. They check only that the code does what the owner's rules say; they judge
nothing on profit. The week of each day is replayed through the analyser and the strategies exactly as the live
service runs them (research/analyser_control_days.py, ideas_day), every candidate checked at entry.

  a. Trend days, Friday 6 and Tuesday 10 November 2026: the trend group takes the same trades with the switches on as
     off, except the 6 November breakout sell, which moves from 17:50 (13355.2) to 17:55 (13350.9) because of the
     4-pip consolidation breakout (accepted by the owner, 18 November 2026).
  b. Friday 13 November 2026 (the textbook range): the rules hold for every idea allowed (the states and trades are in
     docs/research/analyser_control_20261118/).
  c. Tuesday 17 November 2026: no emerging trend at 06:35, 08:55 or 14:45; no consolidation breakout at 07:50 or 12:40;
     the 16:35 bounce sell does not open; the 10:05 bounce and level reversal give one trade.

Stage 1b (owner, 18 November 2026): the trend proof from ranging and consolidation, the 5-minute break of the hourly
range and no possible reversal from a strong push. On 10 November the slow grind sell of 13:55 (13392.5) is new with the
switches on (the 13:45 and 13:50 5-minute closes broke below the hourly range; reported to the owner, who asked to be
stopped only if a trend trade is lost). On 17 November the rallies are called trend up at 03:30 and 16:10, the proof never
fires in the morning box (07:00 to 13:00), the possible reversal comes at 18:30 (not 16:30, in the strong push), and the
16:35 and 17:45 bounce sells do not open.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from functools import lru_cache

import pytest

from analyser.hourly_read import RANGING as HOURLY_RANGING
from analyser.states import EMERGING, POSSIBLE_REVERSAL, TREND, rejection_at_edge
from config.settings_loader import load_settings
from research.analyser_control_days import UK, ideas_day
from safety.rules import _one_signal
from strategies.common import (ASIAN_RANGE_BREAKOUT, BOLLINGER_BOUNCE, BREAKOUT, LEVEL_REVERSAL, REVERSAL_GROUP,
                               TREND_GROUP, may_open)

BASE = load_settings().for_pair("GBPUSD")
pytestmark = pytest.mark.skipif(not (BASE.candles.folder / "5m").is_dir(),
                                reason="the real candle store is only on the server")


@lru_cache(maxsize=None)
def day(d: date, on: bool):
    return ideas_day(d, on)


def hm(t: datetime) -> str:
    return t.astimezone(UK).strftime("%H:%M")


def trend_trades(d: date, on: bool) -> set:
    """The trend group's ideas allowed at entry that the hours and news rules would let open (UK time, strategy,
    direction, entry price)."""
    _, ideas, runner = day(d, on)
    return {(hm(i.time), i.strategy, i.direction, str(i.entry_price)) for i in ideas
            if i.allowed and i.strategy in TREND_GROUP and not may_open(runner.s, "GBPUSD", i.strategy, i.time)}


def first_each_way(trades: set, strategy: str) -> dict:
    """The first idea each way of a once-a-day strategy (the Asian range breakout): the one that opens."""
    out = {}
    for t in sorted(trades):
        if t[1] == strategy and t[2] not in out:
            out[t[2]] = t
    return out


# ---- a. trend days ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("d,only_off,only_on", [
    (date(2026, 11, 6), {("17:50", BREAKOUT, "sell", "13355.2")}, {("17:55", BREAKOUT, "sell", "13350.9")}),
    (date(2026, 11, 10), set(), {("13:55", "slow grind", "sell", "13392.5")}),
])
def test_a_trend_days_the_trend_group_takes_the_same_trades(d, only_off, only_on):
    off, on = trend_trades(d, False), trend_trades(d, True)
    not_arb = lambda s: {t for t in s if t[1] != ASIAN_RANGE_BREAKOUT}   # noqa: E731
    assert not_arb(off) - not_arb(on) == only_off
    assert not_arb(on) - not_arb(off) == only_on
    # the Asian range breakout opens once each way a day: the same first idea each way
    assert first_each_way(off, ASIAN_RANGE_BREAKOUT) == first_each_way(on, ASIAN_RANGE_BREAKOUT)


def test_a_the_asian_range_breakout_is_not_held_back_by_ranging_on_10_november():
    """Owner, 18 November 2026: ranging, consolidation and the hourly-ranging rule do not block it. On 10 November the
    07:25 buy (analyser ranging) and the 09:40 sell (consolidation, hourly ranging) are allowed."""
    _, ideas, _ = day(date(2026, 11, 10), True)
    got = {(hm(i.time), i.direction): i for i in ideas if i.strategy == ASIAN_RANGE_BREAKOUT}
    assert got[("07:25", "buy")].allowed and got[("07:25", "buy")].state == "ranging"
    assert got[("09:40", "sell")].allowed and got[("09:40", "sell")].state == "consolidation"


# ---- b and c: the rules hold for every idea allowed ------------------------------------------------------------------

@pytest.mark.parametrize("d", [date(2026, 11, 13), date(2026, 11, 17)])
def test_b_c_every_idea_allowed_follows_the_hourly_ranging_rule(d):
    """While the hourly read says ranging (as the analyser and the trend group see it: no 5-minute break standing after
    the last finished candle): no trend-group idea except the Asian range breakout; reversal-group ideas only at the
    edge (furthest point within the edge distance, rejection candle closing back inside the range)."""
    _, ideas, runner = day(d, True)
    starts = {c.start: k for k, c in enumerate(runner.week)}
    for i in ideas:
        if not i.allowed:
            continue
        candle = i.time.replace(minute=i.time.minute - i.time.minute % 5, second=0, microsecond=0)
        hr = runner.trend_hourly(starts[candle] - 1, runner.hourly_read.at(candle))
        if hr.state != HOURLY_RANGING or hr.high is None:
            continue
        if i.strategy in TREND_GROUP:
            assert i.strategy == ASIAN_RANGE_BREAKOUT, (hm(i.time), i.strategy)
        else:
            assert i.strategy in REVERSAL_GROUP
            assert rejection_at_edge(runner.s, hr, Decimal(i.context["furthest"]), Decimal(i.context["rejection_close"]),
                                     i.direction), (hm(i.time), i.strategy, i.direction)


# ---- c. Tuesday 17 November 2026 -----------------------------------------------------------------------------------

def test_c_no_emerging_trend_from_rejections_inside_the_hourly_range():
    changes, _, _ = day(date(2026, 11, 17), True)
    assert not [ch for ch in changes if hm(ch.time) in ("06:35", "08:55", "14:45") and ch.state == EMERGING]
    off, _, _ = day(date(2026, 11, 17), False)              # they happen with the switches off
    assert {hm(ch.time) for ch in off if ch.state == EMERGING} >= {"06:35", "08:55", "14:45"}


def test_c_no_small_consolidation_breakouts_at_07_50_and_12_40():
    changes, _, _ = day(date(2026, 11, 17), True)
    assert not [ch for ch in changes if hm(ch.time) in ("07:50", "12:40") and "broke out of the consolidation" in ch.reason]


def test_c_the_16_35_and_17_45_bounce_sells_do_not_open():
    _, ideas, _ = day(date(2026, 11, 17), True)
    for t in ("16:35", "17:45"):        # 16:35 in the strong push up, 17:45 in the slow grind up: against the trend
        got = [i for i in ideas if i.strategy == BOLLINGER_BOUNCE and i.direction == "sell" and hm(i.time) == t]
        assert got and not any(i.allowed for i in got), t
    _, off, _ = day(date(2026, 11, 17), False)
    assert any(i.allowed for i in off if i.strategy == BOLLINGER_BOUNCE and hm(i.time) == "16:35")


def test_c_the_10_05_bounce_and_level_reversal_give_one_trade():
    _, ideas, runner = day(date(2026, 11, 17), True)
    at = {i.strategy: i for i in ideas if hm(i.time) == "10:05" and i.direction == "sell"
          and i.strategy in (BOLLINGER_BOUNCE, LEVEL_REVERSAL)}
    bounce, lr = at[BOLLINGER_BOUNCE], at[LEVEL_REVERSAL]
    assert bounce.allowed and lr.allowed                    # both pass the analyser's checks
    assert bounce.context["signal"] == lr.context["signal"] == "sell 2026-11-17T09:55:00Z"
    used = {bounce.context["signal"]: BOLLINGER_BOUNCE}     # the bounce triggers first (as live at 10:05:01)
    assert _one_signal(runner.s, lr, used) == ["same signal already traded by Bollinger bounce"]
    _, off, off_runner = day(date(2026, 11, 17), False)     # with ONE_SIGNAL_ONE_TRADE off: two trades
    lr_off = next(i for i in off if i.strategy == LEVEL_REVERSAL and hm(i.time) == "10:05")
    assert _one_signal(off_runner.s, lr_off, used) == []


# ---- stage 1b on 17 November ---------------------------------------------------------------------------------------

def test_1b_the_trend_proof_calls_both_rallies_from_consolidation():
    changes, _, _ = day(date(2026, 11, 17), True)
    trends = [(hm(ch.time), ch.direction, ch.previous_state) for ch in changes
              if ch.state == TREND and ch.reason.startswith("the trend proof held in")]
    assert trends == [("03:30", "up", "consolidation"), ("16:10", "up", "consolidation")]
    # never inside the morning box
    assert not [ch for ch in changes if ch.state == TREND and "07:00" <= hm(ch.time) < "13:00"]


def test_1b_no_possible_reversal_in_the_strong_push_it_comes_at_18_30():
    changes, _, _ = day(date(2026, 11, 17), True)
    afternoon = [(hm(ch.time), ch.state, ch.trend_type) for ch in changes if "16:00" <= hm(ch.time) <= "18:35"]
    assert afternoon == [("16:10", TREND, "slow grind"), ("16:25", TREND, "strong push"),
                         ("16:45", TREND, "slow grind"), ("18:30", POSSIBLE_REVERSAL, None),
                         ("18:35", EMERGING, None)]


def test_1b_the_trend_group_is_first_allowed_at_16_45_in_the_afternoon():
    _, ideas, runner = day(date(2026, 11, 17), True)
    first = min((hm(i.time), i.strategy, i.direction) for i in ideas if i.allowed and i.strategy in TREND_GROUP
                and "13:00" <= hm(i.time) and not may_open(runner.s, "GBPUSD", i.strategy, i.time))
    assert first == ("16:45", "slow grind", "buy")
