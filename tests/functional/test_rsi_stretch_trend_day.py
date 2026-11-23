"""Functional tests for rule 2b, the RSI stretch, and Johnny's slow-grind trend day (owner, 21 November 2026;
strategies/entry_filters.py), with the real settings and a real candle store of made-up candles.

The owner's rules:
  RULE 2b (RSI_STRETCH, on if left out; ENTRY_NEAR_EMA8 now off if left out). No SELL when the 5-minute RSI 3 is under
  30; no BUY when it is over 70. RSI 3 on the sell price at the last finished 5-minute candle before the entry.
  Exempt: slow grind, breakout, Asian range breakout, session sweep. Each refusal records the RSI and the strategy.
  TREND DAY (TREND_DAY_RSI_OFF, on if left out). The slow grind has opened a trade and it is in profit at any point
  between 06:00 and 09:00 UK: from then until the end of the day the trend day is on, in that trade's direction. On
  a trend day rule 2b does not apply to trades in its direction; trades against it are still checked. Rule 1
  unchanged. Its start, direction and slow grind trade are recorded.
The owner's answers (21 November 2026): the day ends at 20:30 UK; a slow grind trade the other way also in profit
inside 06:00-09:00 cancels the trend day for the rest of the day; "in profit" is more than 0 pips as IG would close it
(the sell price for a buy, the buy price for a sell).
"""

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace

import pytest

from config.settings_loader import load_settings
from prices.model import Candle
from prices.store import CandleStore
from strategies import entry_filters as ef
from strategies.common import (ASIAN_RANGE_BREAKOUT, BOLLINGER_BOUNCE, BOLLINGER_BOUNCE_5M, BREAKOUT, BUY,
                               EMA_PULLBACK, LEVEL_REVERSAL, NEW_YORK_OPEN_REVERSAL, RANGE_TRADE, SELL, SESSION_SWEEP,
                               SLOW_GRIND, Idea)
from trade_manager.manager import Bar

UTC = timezone.utc
WED = datetime(2026, 11, 18, 0, 0, tzinfo=UTC)          # UK time is UTC in November
AT = WED + timedelta(hours=12)
SWITCHES = ("HOURLY_CONTEXT", "ENTRY_NEAR_EMA8", "RSI_STRETCH", "TREND_DAY_RSI_OFF")


def settings(tmp_path: Path, pretend_switches: Path, **given):
    """The real settings with the tests' pretend switches; the four entry-filter switches as given (None: left out).
    Not given: rule 1 and rule 2 off, rule 2b on, the trend day on."""
    want = {"HOURLY_CONTEXT": "off", "ENTRY_NEAR_EMA8": "off", "RSI_STRETCH": "on", "TREND_DAY_RSI_OFF": "on"} | given
    text = "".join(line + "\n" for line in pretend_switches.read_text().splitlines() if not line.startswith(
        tuple(k + "=" for k in SWITCHES)))
    text += "".join(f"{k}={v}\n" for k, v in want.items() if v is not None)
    env = tmp_path / ("switches_" + "_".join(f"{k}{v}" for k, v in sorted(want.items())) + ".env")
    env.write_text(text)
    return load_settings(switches_from=env).for_pair("GBPUSD")


@pytest.fixture
def S(tmp_path, pretend_switches):
    return settings(tmp_path, pretend_switches)


def c5(t: datetime, price) -> Candle:
    p = D(str(price))
    return Candle("5m", t, t + timedelta(minutes=5), p + D("1.5"), p + D("1.5"), p + D("1.5"), p + D("1.5"), p, p, p, p)


def store_with(tmp_path, closes, name, start=WED + timedelta(hours=10)):
    st = CandleStore(tmp_path / name / "candles" / "GBPUSD", 30)
    for k, p in enumerate(closes):
        st.add(c5(start + timedelta(minutes=5 * k), p))
    return st


@pytest.fixture
def RISING(tmp_path):            # 24 candles up 1 pip each to 11:55: RSI 3 = 100
    return store_with(tmp_path, [13100 + k for k in range(24)], "up")


@pytest.fixture
def FALLING(tmp_path):           # down 1 pip each: RSI 3 = 0
    return store_with(tmp_path, [13200 - k for k in range(24)], "down")


@pytest.fixture
def MIXED(tmp_path):             # ups and downs: an RSI 3 between 30 and 70
    return store_with(tmp_path, [13150 + (3 if k % 2 else 0) - (k % 3) for k in range(24)], "mixed")


def idea(strategy, direction, price=13150, t=AT) -> Idea:
    return Idea("GBPUSD", strategy, direction, t, D(str(price)), "trend", "down", None, "sell side", ["made up"])


class Over:
    def __init__(self, base, **f):
        self._b = base
        self.entry_filters = SimpleNamespace(**(vars(base.entry_filters) | f))

    def __getattr__(self, n):
        return getattr(self._b, n)


# ---- rule 2b: the RSI stretch --------------------------------------------------------------------------------------

def test_the_made_up_candles_give_rsi_100_0_and_between(S, RISING, FALLING, MIXED):
    assert ef.rsi3_at(S, RISING, AT)[0] == 100 and ef.rsi3_at(S, FALLING, AT)[0] == 0
    assert 30 < ef.rsi3_at(S, MIXED, AT)[0] < 70


def test_rule_2b_no_sell_with_the_rsi_3_under_30_and_the_refusal_records_the_rsi_and_the_strategy(S, FALLING):
    v = ef.check(S, FALLING, idea(LEVEL_REVERSAL, SELL))
    assert not v.allowed and v.rule == ef.RSI_STRETCH
    assert v.details["rsi3_5m"] == "0.0" and v.details["strategy"] == LEVEL_REVERSAL
    assert v.details["rsi_candle"] == "2026-11-18T11:55Z" and v.details["limit"] == "under 30"
    assert "no SELL with the 5-minute RSI 3 0.0" in v.why


def test_rule_2b_no_buy_with_the_rsi_3_over_70(S, RISING):
    v = ef.check(S, RISING, idea(EMA_PULLBACK, BUY))
    assert not v.allowed and v.details["rsi3_5m"] == "100.0" and v.details["limit"] == "over 70"


def test_rule_2b_leaves_a_sell_at_a_high_rsi_a_buy_at_a_low_rsi_and_both_in_between(S, RISING, FALLING, MIXED):
    assert ef.check(S, RISING, idea(LEVEL_REVERSAL, SELL)).allowed
    assert ef.check(S, FALLING, idea(LEVEL_REVERSAL, BUY)).allowed
    for d in (BUY, SELL):
        v = ef.check(S, MIXED, idea(LEVEL_REVERSAL, d))
        assert v.allowed and v.checked[-1].startswith("RSI stretch: 5-minute RSI 3")


def test_rule_2b_under_30_and_over_70_are_strict_and_the_numbers_come_from_the_settings(S, MIXED):
    r = ef.rsi3_at(S, MIXED, AT)[0]
    assert ef.check(Over(S, rsi_sell_below=r), MIXED, idea(LEVEL_REVERSAL, SELL)).allowed          # equal: not under
    assert not ef.check(Over(S, rsi_sell_below=r + D("0.01")), MIXED, idea(LEVEL_REVERSAL, SELL)).allowed
    assert ef.check(Over(S, rsi_buy_above=r), MIXED, idea(LEVEL_REVERSAL, BUY)).allowed            # equal: not over
    assert not ef.check(Over(S, rsi_buy_above=r - D("0.01")), MIXED, idea(LEVEL_REVERSAL, BUY)).allowed
    f = S.entry_filters
    assert (f.rsi_periods, f.rsi_sell_below, f.rsi_buy_above) == (3, D("30"), D("70"))


def test_rule_2b_exempts_the_slow_grind_breakout_asian_range_breakout_and_session_sweep_only(S, RISING, FALLING):
    for strategy in (SLOW_GRIND, BREAKOUT, ASIAN_RANGE_BREAKOUT, SESSION_SWEEP):
        assert ef.check(S, FALLING, idea(strategy, SELL)).checked == [f"RSI stretch: {strategy} is exempt"]
        assert ef.check(S, RISING, idea(strategy, BUY)).allowed
    for strategy in (EMA_PULLBACK, BOLLINGER_BOUNCE, BOLLINGER_BOUNCE_5M, RANGE_TRADE, LEVEL_REVERSAL,
                     NEW_YORK_OPEN_REVERSAL):
        assert not ef.check(S, FALLING, idea(strategy, SELL)).allowed, strategy
        assert not ef.check(S, RISING, idea(strategy, BUY)).allowed, strategy


def test_rule_2b_uses_the_last_finished_5_minute_candle_before_the_entry(S, tmp_path):
    st = store_with(tmp_path, [13200 - k for k in range(24)] + [13300], "turn")     # the 12:00 candle jumps up
    assert not ef.check(S, st, idea(LEVEL_REVERSAL, SELL, t=AT + timedelta(minutes=3))).allowed   # 12:00 unfinished
    assert ef.check(S, st, idea(LEVEL_REVERSAL, SELL, t=AT + timedelta(minutes=5))).allowed        # now it counts


def test_rule_2b_switch_off_and_the_switches_left_out(tmp_path, pretend_switches, FALLING):
    off = settings(tmp_path, pretend_switches, RSI_STRETCH="off")
    v = ef.check(off, FALLING, idea(LEVEL_REVERSAL, SELL))
    assert v.allowed and v.checked == []
    out = settings(tmp_path, pretend_switches, HOURLY_CONTEXT=None, ENTRY_NEAR_EMA8=None, RSI_STRETCH=None,
                   TREND_DAY_RSI_OFF=None)
    sw = out.switches
    assert (sw.hourly_context, sw.entry_near_ema8, sw.rsi_stretch, sw.trend_day_rsi_off) == (True, False, True, True)


def test_rule_2b_is_off_on_a_trend_day_only_in_the_trends_direction(S, RISING, FALLING):
    v = ef.check(S, RISING, idea(EMA_PULLBACK, BUY), trend=BUY)                        # with the trend: not applied
    assert v.allowed and "not applied: a buy trend day" in v.checked[-1]
    v = ef.check(S, FALLING, idea(EMA_PULLBACK, SELL), trend=BUY)                      # against it: still checked
    assert not v.allowed and v.details["trend_day"] == BUY and "against it" in v.why
    assert ef.check(S, FALLING, idea(EMA_PULLBACK, SELL), trend=SELL).allowed
    assert not ef.check(S, RISING, idea(EMA_PULLBACK, BUY), trend=SELL).allowed


def test_rule_1_is_unchanged_on_a_trend_day(tmp_path, pretend_switches):
    from tests.functional.test_entry_filters import PIVOT_DOWN, TUE_DOWN, down_hours
    from tests.functional.test_entry_filters import store_with as filters_store
    s = settings(tmp_path, pretend_switches, HOURLY_CONTEXT="on")
    st = filters_store(tmp_path, down_hours(), TUE_DOWN, name="rule1")
    v = ef.check(s, st, idea(LEVEL_REVERSAL, BUY, PIVOT_DOWN), trend=BUY)
    assert not v.allowed and v.rule == ef.HOURLY_CONTEXT


# ---- the slow-grind trend day ----------------------------------------------------------------------------------------

DAY = datetime(2026, 11, 9, 0, 0, tzinfo=UTC)


def at(hh, mm=0, day=DAY):
    return day + timedelta(hours=hh, minutes=mm)


def bar(t, sell_low, sell_high, spread="1.5"):
    lo, hi, sp = D(str(sell_low)), D(str(sell_high)), D(spread)
    return Bar(t, lo + sp, hi + sp, lo + sp, lo + sp, lo, hi, lo, lo)


def trade(direction=BUY, fill="13380.2", opened=None, strategy=SLOW_GRIND, ref="AB-sg-1"):
    return SimpleNamespace(strategy=strategy, direction=direction, fill=D(fill), opened_at=opened or at(5, 25),
                           open=True, reference=ref)


@pytest.fixture
def W(S):
    rec = []
    w = ef.TrendDayWatch(S, record=lambda kind, t, **d: rec.append((kind, t, d)))
    w.rec = rec
    return w


def test_a_slow_grind_buy_in_profit_inside_06_to_09_starts_a_buy_trend_day_and_records_it(W):
    sg = trade()                                                    # opened 05:25 at 13380.2
    W.on_bar(bar(at(6, 30), 13375, 13381), [sg])                    # sell high 13381: +0.8 as IG would close it
    assert W.direction_at(at(6, 31)) == BUY and W.direction_at(at(6, 29)) is None
    ((kind, t, d),) = W.rec
    assert kind == ef.TREND_DAY_STARTED and t == at(6, 30)
    assert d["direction"] == BUY and d["reference"] == "AB-sg-1" and d["pips_in_profit"] == D("0.8")
    assert "06:30 UK" in d["why"]


def test_a_trade_opened_before_06_00_starts_it_at_06_00_once_in_profit(W):
    sg = trade()
    W.on_bar(bar(at(5, 55), 13379, 13390), [sg])                    # in profit, but before 06:00
    assert W.direction_at(at(5, 58)) is None and W.rec == []
    W.on_bar(bar(at(6, 0), 13379, 13385), [sg])
    assert W.rec[0][1] == at(6, 0) and W.direction_at(at(6, 1)) == BUY


def test_in_profit_only_outside_06_to_09_does_not_start_it(W):
    sg = trade(opened=at(8, 0))
    W.on_bar(bar(at(9, 0), 13379, 13395), [sg])                     # 09:00 is outside (up to 09:00)
    W.on_bar(bar(at(14, 0), 13379, 13395), [sg])
    assert W.rec == [] and W.direction_at(at(15, 0)) is None
    W.on_bar(bar(at(8, 55), 13379, 13395), [sg])                    # 08:55 is inside
    assert W.direction_at(at(9, 30)) == BUY


def test_in_profit_means_more_than_0_pips_as_ig_would_close_it(W):
    buy = trade()
    W.on_bar(bar(at(7, 0), 13370, "13380.2"), [buy])               # sell high = the fill: 0, not in profit
    W.on_bar(bar(at(7, 5), 13370, 13379.9), [buy])                  # the buy price above the fill, the sell price not
    assert W.rec == []
    sell = trade(SELL, "13326.6", at(8, 13), ref="AB-sg-2")
    W.on_bar(bar(at(8, 15), "13325.2", 13330), [sell])              # buy low 13326.7: 0.1 against
    assert W.rec == []
    W.on_bar(bar(at(8, 20), 13324, 13330), [sell])                  # buy low 13325.5: +1.1
    assert W.direction_at(at(8, 25)) == SELL and W.rec[0][2]["pips_in_profit"] == D("1.1")


def test_only_the_slow_grind_and_only_from_the_bar_it_opened_in(W):
    W.on_bar(bar(at(7, 0), 13370, 13400), [trade(strategy=EMA_PULLBACK)])
    W.on_bar(bar(at(7, 0), 13370, 13400), [trade(opened=at(7, 5))])            # opened after this bar started
    closed = trade()
    closed.open = False
    W.on_bar(bar(at(7, 10), 13370, 13400), [closed])
    assert W.rec == [] and W.direction_at(at(8, 0)) is None


def test_the_trend_day_ends_at_20_30_uk_and_a_new_day_starts_afresh(W):
    W.on_bar(bar(at(6, 30), 13375, 13390), [trade()])
    assert W.direction_at(at(20, 29)) == BUY and W.direction_at(at(20, 30)) is None
    nxt = DAY + timedelta(days=1)
    assert W.direction_at(at(7, 0, nxt)) is None
    W.on_bar(bar(at(7, 0, nxt), 13300, 13305), [])
    assert W.direction is None and W.status(at(7, 1, nxt)) is None


def test_a_slow_grind_the_other_way_in_profit_inside_the_window_cancels_it_for_the_day(W):
    W.on_bar(bar(at(6, 30), 13375, 13390), [trade()])
    against = trade(SELL, "13385", at(7, 0), ref="AB-sg-2")
    W.on_bar(bar(at(7, 30), 13370, 13386), [against])                # buy low 13371.5: the sell is in profit
    assert W.direction_at(at(7, 31)) is None and W.cancelled == at(7, 30)
    assert W.direction_at(at(7, 29)) == BUY                         # it was on until the cancel
    kind, t, d = W.rec[-1]
    assert kind == ef.TREND_DAY_CANCELLED and d["reference"] == "AB-sg-2" and d["started_by"] == "AB-sg-1"
    W.on_bar(bar(at(8, 0), 13375, 13395), [trade(ref="AB-sg-3", opened=at(7, 55))])   # no new start that day
    assert W.direction_at(at(8, 1)) is None and len(W.rec) == 2
    st = W.status(at(8, 1))
    assert st["direction"] == BUY and st["active"] is False and st["cancelled_utc"] == "2026-11-09T07:30:00Z"


def test_a_slow_grind_the_other_way_in_profit_after_09_00_does_not_cancel_it(W):
    W.on_bar(bar(at(6, 30), 13375, 13390), [trade()])
    W.on_bar(bar(at(10, 0), 13300, 13386), [trade(SELL, "13385", at(9, 30), ref="AB-sg-2")])
    assert W.direction_at(at(10, 5)) == BUY and len(W.rec) == 1


def test_after_a_restart_the_days_record_is_read_back(S):
    rows = [{"time_utc": "2026-11-09T06:30:00Z", "kind": ef.TREND_DAY_STARTED, "direction": BUY,
             "reference": "AB-sg-1"},
            {"time_utc": "2026-11-08T07:00:00Z", "kind": ef.TREND_DAY_STARTED, "direction": SELL}]   # another day
    w = ef.TrendDayWatch(S)
    w.restore(rows, at(11, 0))
    assert w.direction_at(at(11, 0)) == BUY and w.reference == "AB-sg-1"
    w.restore(rows + [{"time_utc": "2026-11-09T07:00:00Z", "kind": ef.TREND_DAY_CANCELLED}], at(11, 0))
    assert w.direction_at(at(11, 0)) is None


# ---- in the trading engine -------------------------------------------------------------------------------------------

from tests.technical import test_trading as tt  # noqa: E402

REAL_CHECK = ef.check
T0 = datetime(2026, 11, 4, 7, 0, tzinfo=UTC)


@pytest.fixture
def S_ENGINE(tmp_path, pretend_switches):
    from tests.technical.test_orders import Over as O
    s = load_settings(switches_from=pretend_switches).for_pair("GBPUSD")
    return O(s, switches={k: True for k in ("slow_grind", "ema_pullback", "bollinger_bounce", "range_trade",
                                              "breakout", "level_reversal", "trend_day_rsi_off")} | {"trading": False},
             orders={"folder": tmp_path / "orders"}, trade_manager={"folder": tmp_path / "tm"},
             safety={"folder": tmp_path / "safety"}, records={"folder": tmp_path / "records"},
             trading={"pause_file": tmp_path / "control" / "pause_new_trades"},
             dashboard={"status_folder": tmp_path / "status"})


def test_engine_records_the_trend_day_start_and_passes_its_direction_to_every_later_check(S_ENGINE, monkeypatch):
    seen = []

    def check(s, store, i, trend=None):
        seen.append((i.strategy, i.time, trend))
        return ef.Verdict(True)
    monkeypatch.setattr(ef, "check", check)
    C = [tt.candle(T0 + timedelta(minutes=5 * k), 100, 100.5, 99.5, 100) for k in range(3)]
    C.append(tt.candle(T0 + timedelta(minutes=15), 100, 100, 95, 96))           # the slow grind sell goes into profit
    C += [tt.candle(T0 + timedelta(minutes=5 * k), 96, 96.5, 95.5, 96) for k in range(4, 6)]
    ideas = {C[1].start: [tt.idea(SLOW_GRIND, C[1].start)], C[4].start: [tt.idea(RANGE_TRADE, C[4].start)]}
    e, ig, tracker, clock, quote = tt.make(S_ENGINE, monkeypatch, C, ideas, clock={"t": T0})
    e.start(T0)
    tt.feed(e, clock, C)
    assert seen == [(SLOW_GRIND, C[1].start, None), (RANGE_TRADE, C[4].start, SELL)]
    rows = [json.loads(x) for f in Path(S_ENGINE.records.folder).rglob("decisions.jsonl")
            for x in f.read_text().splitlines()]
    (start,) = [r for r in rows if r["kind"] == ef.TREND_DAY_STARTED]
    assert start["time_utc"] == "2026-11-04T07:15:00Z" and start["direction"] == SELL
    assert start["strategy"] == SLOW_GRIND and start["reference"].startswith("AB")
    st = e.status(C[-1].end)["trend_day"]
    assert st["direction"] == SELL and st["active"] is True and st["started_utc"] == "2026-11-04T07:15:00Z"


def test_engine_with_the_trend_day_switch_off_records_nothing_and_passes_no_direction(S_ENGINE, monkeypatch, tmp_path):
    from tests.technical.test_orders import Over as O
    off = O(S_ENGINE, switches={"trend_day_rsi_off": False})
    seen = []
    monkeypatch.setattr(ef, "check", lambda s, store, i, trend=None: seen.append(trend) or ef.Verdict(True))
    C = [tt.candle(T0 + timedelta(minutes=5 * k), 100, 100.5, 99.5, 100) for k in range(3)]
    C.append(tt.candle(T0 + timedelta(minutes=15), 100, 100, 95, 96))
    C += [tt.candle(T0 + timedelta(minutes=5 * k), 96, 96.5, 95.5, 96) for k in range(4, 6)]
    ideas = {C[1].start: [tt.idea(SLOW_GRIND, C[1].start)], C[4].start: [tt.idea(RANGE_TRADE, C[4].start)]}
    e, ig, tracker, clock, quote = tt.make(off, monkeypatch, C, ideas, clock={"t": T0})
    e.start(T0)
    tt.feed(e, clock, C)
    assert seen == [None, None] and e.status(C[-1].end)["trend_day"] is None
    rows = [json.loads(x) for f in Path(off.records.folder).rglob("decisions.jsonl") for x in f.read_text().splitlines()]
    assert not [r for r in rows if r["kind"].startswith("trend day")]
