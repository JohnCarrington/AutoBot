"""Functional tests for the entry filters (owner, 21 November 2026; strategies/entry_filters.py), with the real
settings (config/settings.toml) and a real candle store holding made-up hourly, 5-minute and daily candles.

The owner's rules:
  RULE 1 (HOURLY_CONTEXT, on if left out). DOWN context: the last two hourly swing highs are lower highs, the price
  is below the hourly 50 EMA and the 50 EMA is falling (lower than 6 hourly candles before). UP: the mirror. In a
  DOWN context no strategy opens a BUY with its entry price within 5 pips of the daily pivot or the hourly 50 EMA; in
  an UP context no SELL. Every strategy. A swing high: an hourly candle whose high has 2 lower highs on each side.
  RULE 2 (ENTRY_NEAR_EMA8, on if left out). A SELL only if its entry price is no more than 5 pips below the
  5-minute 8 EMA; a BUY only if no more than 5 pips above it. The 8 EMA on the sell price at the last finished
  5-minute candle before the entry. Exempt: slow grind, breakout, Asian range breakout, session sweep (the session
  sweep added by the owner, 21 November 2026).
  Both: one check for every trade, just before it opens; nothing else changes; every refusal recorded with the rule
  and why.
The owner's answers (21 November 2026): "the last two swing highs are lower highs" = the latest swing high is lower
than the one before it; "price below the 50 EMA" = the last finished hourly close against the 50 EMA at that candle;
the entry price is the strategy's own entry price (sell / chart price), for buys too.
"""

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

UTC = timezone.utc
MON = datetime(2026, 11, 16, 0, 0, tzinfo=UTC)          # UK time is UTC in November
WED = datetime(2026, 11, 18, 0, 0, tzinfo=UTC)
AT = WED + timedelta(hours=12)                           # every test trade opens at Wed 18 Nov 12:00 unless it says
EMA8 = D("13175")                                        # the 5-minute candles are flat here, so the 8 EMA is exactly this


def settings(tmp_path: Path, pretend_switches: Path, hourly: str | None, ema8: str | None):
    """The real settings with the tests' pretend switches and the two switches as given (None: left out)."""
    text = "".join(line + "\n" for line in pretend_switches.read_text().splitlines()
                   if not line.startswith(("HOURLY_CONTEXT=", "ENTRY_NEAR_EMA8=")))
    if hourly is not None:
        text += f"HOURLY_CONTEXT={hourly}\n"
    if ema8 is not None:
        text += f"ENTRY_NEAR_EMA8={ema8}\n"
    env = tmp_path / f"switches_{hourly}_{ema8}.env"
    env.write_text(text)
    return load_settings(switches_from=env).for_pair("GBPUSD")


@pytest.fixture
def BOTH(tmp_path, pretend_switches):
    return settings(tmp_path, pretend_switches, "on", "on")


@pytest.fixture
def R1(tmp_path, pretend_switches):                     # rule 1 only
    return settings(tmp_path, pretend_switches, "on", "off")


@pytest.fixture
def R2(tmp_path, pretend_switches):                     # rule 2 only
    return settings(tmp_path, pretend_switches, "off", "on")


@pytest.fixture
def NONE(tmp_path, pretend_switches):
    return settings(tmp_path, pretend_switches, "off", "off")


def c(tf: str, start: datetime, minutes: int, o, h, l, cl, parts=1) -> Candle:
    """A candle; sell prices as given, buy 1.5 pips above."""
    s = [D(str(x)) for x in (o, h, l, cl)]
    return Candle(tf, start, start + timedelta(minutes=minutes), *[x + D("1.5") for x in s], *s, parts, parts)


def down_hours(last_peak_high=None):
    """60 hourly candles, Mon 16 00:00 to Wed 18 11:00: falling 2 pips an hour, a peak every 6 hours (10 pips above
    the close, the rest 3), so each swing high is lower than the one before: the last two 13208 (Wed 03:00) and
    13196 (Wed 09:00). Close 13182 at the end, below a falling 50 EMA."""
    out = []
    for i in range(60):
        cl = 13300 - 2 * i
        hi = cl + (10 if i % 6 == 3 else 3)
        if i == 57 and last_peak_high is not None:
            hi = last_peak_high
        out.append(c("1h", MON + timedelta(hours=i), 60, cl + 1, hi, cl - 3, cl, 12))
    return out


def up_hours():
    """The mirror: rising 2 pips an hour, a trough every 6 hours, each swing low higher than the one before."""
    out = []
    for i in range(60):
        cl = 13000 + 2 * i
        lo = cl - (10 if i % 6 == 3 else 3)
        out.append(c("1h", MON + timedelta(hours=i), 60, cl - 1, cl + 3, lo, cl, 12))
    return out


def flat_5m(price=EMA8, upto=AT):
    return [c("5m", t, 5, price, price, price, price) for t in
            (WED + timedelta(hours=10, minutes=5 * k) for k in range(24)) if t + timedelta(minutes=5) <= upto]


def store_with(tmp_path, hours, day, five=None, name="s"):
    """A real candle store: the hourly candles, Tuesday's daily candle (the pivot for Wednesday) and the 5-minute
    candles."""
    st = CandleStore(tmp_path / name / "candles" / "GBPUSD", 30)
    for x in hours + [day] + (flat_5m() if five is None else five):
        st.add(x)
    return st


TUE_DOWN = c("1d", WED - timedelta(days=1), 1440, 13200, 13240, 13100, 13150, 288)   # pivot (13240+13100+13150)/3 = 13163.3
TUE_UP = c("1d", WED - timedelta(days=1), 1440, 13080, 13150, 13050, 13100, 288)     # pivot 13100.0
PIVOT_DOWN, PIVOT_UP = D("13163.3"), D("13100.0")


@pytest.fixture
def DOWN_STORE(tmp_path):
    return store_with(tmp_path, down_hours(), TUE_DOWN, name="down")


@pytest.fixture
def UP_STORE(tmp_path):
    return store_with(tmp_path, up_hours(), TUE_UP, five=flat_5m(D("13110")), name="up")


def idea(strategy, direction, price, t=AT) -> Idea:
    return Idea("GBPUSD", strategy, direction, t, D(str(price)), "trend", "down", None, "sell side", ["made up"])


def ema50(s, store) -> D:
    return ef.hourly_context(s, store, AT).ema50


# ---- the setup itself ----------------------------------------------------------------------------------------------

def test_the_made_up_candles_give_the_contexts_the_tests_rely_on(BOTH, DOWN_STORE, UP_STORE):
    down = ef.hourly_context(BOTH, DOWN_STORE, AT)
    assert down.kind == ef.DOWN and down.close == D("13182") and down.ema50 > down.close
    assert down.ema50 < down.ema50_before
    assert [p for _, p in down.swings] == [D("13208"), D("13196")]
    up = ef.hourly_context(BOTH, UP_STORE, AT)
    assert up.kind == ef.UP and up.close > up.ema50 and up.ema50 > up.ema50_before
    assert ef.daily_pivot(BOTH, DOWN_STORE, AT) == PIVOT_DOWN and ef.daily_pivot(BOTH, UP_STORE, AT) == PIVOT_UP
    assert ef.ema8_at(BOTH, DOWN_STORE, AT)[0] == EMA8
    assert abs(ema50(BOTH, DOWN_STORE) - PIVOT_DOWN) > 20             # far apart: each line is tested on its own


# ---- rule 1: the hourly context -------------------------------------------------------------------------------------

def test_rule_1_down_context_refuses_a_buy_within_5_pips_of_the_daily_pivot(BOTH, DOWN_STORE):
    v = ef.check(BOTH, DOWN_STORE, idea(LEVEL_REVERSAL, BUY, PIVOT_DOWN + D("3")))
    assert not v.allowed and v.rule == ef.HOURLY_CONTEXT
    assert v.details["context"] == ef.DOWN and v.details["line"] == "the daily pivot"
    assert v.details["line_price"] == "13163.3" and v.details["pips_from_line"] == "3.0"
    assert "DOWN context: lower high 13196" in v.why and "after 13208" in v.why and "refused" in v.why


def test_rule_1_down_context_refuses_a_buy_within_5_pips_of_the_hourly_50_ema_above_or_below_it(R1, DOWN_STORE):
    e = ema50(R1, DOWN_STORE)
    for price in (e - D("4.9"), e, e + D("4.9")):
        v = ef.check(R1, DOWN_STORE, idea(EMA_PULLBACK, BUY, price.quantize(D("0.1"))))
        assert not v.allowed and v.details["line"] == "the hourly 50 EMA", price


def test_rule_1_exactly_5_pips_is_within_and_more_is_not(R1, DOWN_STORE):
    assert not ef.check(R1, DOWN_STORE, idea(LEVEL_REVERSAL, BUY, PIVOT_DOWN - D("5"))).allowed
    assert not ef.check(R1, DOWN_STORE, idea(LEVEL_REVERSAL, BUY, PIVOT_DOWN + D("5"))).allowed
    assert ef.check(R1, DOWN_STORE, idea(LEVEL_REVERSAL, BUY, PIVOT_DOWN + D("5.1"))).allowed
    assert ef.check(R1, DOWN_STORE, idea(LEVEL_REVERSAL, BUY, PIVOT_DOWN - D("5.1"))).allowed


def test_rule_1_down_context_leaves_sells_alone_even_at_the_pivot_and_the_50_ema(R1, DOWN_STORE):
    for price in (PIVOT_DOWN, ema50(R1, DOWN_STORE).quantize(D("0.1"))):
        v = ef.check(R1, DOWN_STORE, idea(LEVEL_REVERSAL, SELL, price))
        assert v.allowed and "DOWN context" in v.checked[0]


def test_rule_1_up_context_refuses_a_sell_near_the_pivot_or_the_50_ema_and_leaves_buys_alone(R1, UP_STORE):
    e = ema50(R1, UP_STORE).quantize(D("0.1"))
    v = ef.check(R1, UP_STORE, idea(SESSION_SWEEP, SELL, PIVOT_UP - D("2")))
    assert not v.allowed and v.details["context"] == ef.UP and v.details["line"] == "the daily pivot"
    assert "UP context: higher low" in v.why
    v = ef.check(R1, UP_STORE, idea(SESSION_SWEEP, SELL, e + D("1")))
    assert not v.allowed and v.details["line"] == "the hourly 50 EMA"
    assert ef.check(R1, UP_STORE, idea(SESSION_SWEEP, BUY, PIVOT_UP)).allowed
    assert ef.check(R1, UP_STORE, idea(SESSION_SWEEP, SELL, PIVOT_UP - D("5.1"))).allowed


def test_rule_1_applies_to_every_strategy_including_those_exempt_from_rule_2(R1, DOWN_STORE):
    for strategy in (SLOW_GRIND, EMA_PULLBACK, BOLLINGER_BOUNCE, BOLLINGER_BOUNCE_5M, RANGE_TRADE, BREAKOUT,
                     LEVEL_REVERSAL, ASIAN_RANGE_BREAKOUT, SESSION_SWEEP, NEW_YORK_OPEN_REVERSAL):
        v = ef.check(R1, DOWN_STORE, idea(strategy, BUY, PIVOT_DOWN))
        assert not v.allowed and v.rule == ef.HOURLY_CONTEXT, strategy


def test_rule_1_no_context_when_the_latest_swing_high_is_not_lower(R1, tmp_path):
    st = store_with(tmp_path, down_hours(last_peak_high=13220), TUE_DOWN, name="higher")     # 13220 above 13208
    ctx = ef.hourly_context(R1, st, AT)
    assert ctx.kind is None and "swing highs 13208 then 13220" in ctx.why
    assert ef.check(R1, st, idea(LEVEL_REVERSAL, BUY, PIVOT_DOWN)).allowed


def test_rule_1_no_context_when_the_last_hourly_close_is_above_the_50_ema(R1, tmp_path):
    hours = down_hours()
    e = ef.hourly_context(R1, store_with(tmp_path, hours, TUE_DOWN, name="first"), AT).ema50
    jump = (e + 5).quantize(D("1"))                                   # the last hour closes above the 50 EMA
    last = hours[-1]
    hours[-1] = c("1h", last.start, 60, 13183, jump + 1, 13179, jump, 12)
    st = store_with(tmp_path, hours, TUE_DOWN, name="jump")
    ctx = ef.hourly_context(R1, st, AT)
    assert ctx.close > ctx.ema50 and ctx.kind is None
    assert ef.check(R1, st, idea(LEVEL_REVERSAL, BUY, PIVOT_DOWN)).allowed


def test_rule_1_no_context_when_the_50_ema_is_not_falling(R1, tmp_path):
    """Lower swing highs and a close below the 50 EMA, but the 50 EMA higher than 6 hours before: no DOWN."""
    out = []
    for i in range(60):                       # rising for 52 hours, then a dip with lower highs in the last 8
        cl = 13000 + 3 * i if i < 52 else 13153 - 12 * (i - 52)
        hi = cl + 3
        if i in (53, 57):
            hi = {53: 13170, 57: 13160}[i]
        out.append(c("1h", MON + timedelta(hours=i), 60, cl, hi, cl - 3, cl, 12))
    st = store_with(tmp_path, out, TUE_DOWN, name="rising")
    ctx = ef.hourly_context(R1, st, AT)
    assert ctx.close < ctx.ema50 and ctx.ema50 > ctx.ema50_before and ctx.kind is None
    assert "swing highs 13170 then 13160" in ctx.why
    assert ef.check(R1, st, idea(LEVEL_REVERSAL, BUY, ctx.ema50.quantize(D("0.1")))).allowed


def test_a_swing_high_needs_2_strictly_lower_highs_on_each_side_of_finished_candles():
    t = [MON + timedelta(hours=i) for i in range(9)]
    highs = [10, 11, 15, 12, 11, 13, 13, 12, 16]        # 15: a swing; 13, 13: equal, neither; 16: no 2 after it
    cs = [c("1h", t[i], 60, h - 1, h, h - 2, h - 1) for i, h in enumerate(highs)]
    assert [p for _, p in ef.swings(cs, "sell", 2, True)] == [D("15")]
    lows = [20, 19, 15, 18, 19, 16, 16, 18, 14]
    cs = [c("1h", t[i], 60, lo + 1, lo + 2, lo, lo + 1) for i, lo in enumerate(lows)]
    assert [p for _, p in ef.swings(cs, "sell", 2, False)] == [D("15")]


def test_rule_1_uses_only_hourly_candles_finished_before_the_entry(R1, DOWN_STORE):
    """At 11:59 the 11:00 hour has not finished: its candle (the 59th) is not used, so the 13196 swing high (09:00)
    is not yet confirmed (it needs 2 finished hours after it) and the last two swing highs are 13220 and 13208."""
    ctx = ef.hourly_context(R1, DOWN_STORE, AT - timedelta(minutes=1))
    assert [p for _, p in ctx.swings] == [D("13220"), D("13208")] and ctx.close == D("13184")


# ---- rule 2: entry near the 8 EMA ----------------------------------------------------------------------------------

def test_rule_2_a_sell_may_be_up_to_5_pips_below_the_8_ema_and_no_further(R2, DOWN_STORE):
    for price in (EMA8 + D("20"), EMA8, EMA8 - D("5")):
        assert ef.check(R2, DOWN_STORE, idea(LEVEL_REVERSAL, SELL, price)).allowed, price
    v = ef.check(R2, DOWN_STORE, idea(LEVEL_REVERSAL, SELL, EMA8 - D("5.1")))
    assert not v.allowed and v.rule == ef.ENTRY_NEAR_EMA8
    assert v.details == {"entry_price": "13169.9", "ema8_5m": "13175.0", "ema8_candle": "2026-11-18T11:55Z",
                         "pips_beyond_ema8": "5.1", "limit_pips": "5"}
    assert "5.1 pips below it" in v.why


def test_rule_2_a_buy_may_be_up_to_5_pips_above_the_8_ema_and_no_further(R2, DOWN_STORE):
    for price in (EMA8 - D("20"), EMA8, EMA8 + D("5")):
        assert ef.check(R2, DOWN_STORE, idea(EMA_PULLBACK, BUY, price)).allowed, price
    v = ef.check(R2, DOWN_STORE, idea(EMA_PULLBACK, BUY, EMA8 + D("5.1")))
    assert not v.allowed and v.details["pips_beyond_ema8"] == "5.1" and "5.1 pips above it" in v.why


def test_rule_2_exempts_the_slow_grind_the_breakout_the_asian_range_breakout_and_the_session_sweep_only(R2, DOWN_STORE):
    for strategy in (SLOW_GRIND, BREAKOUT, ASIAN_RANGE_BREAKOUT, SESSION_SWEEP):
        for direction, price in ((SELL, EMA8 - 20), (BUY, EMA8 + 20)):
            v = ef.check(R2, DOWN_STORE, idea(strategy, direction, price))
            assert v.allowed and v.checked == [f"entry near the 8 EMA: {strategy} is exempt"]
    for strategy in (EMA_PULLBACK, BOLLINGER_BOUNCE, BOLLINGER_BOUNCE_5M, RANGE_TRADE, LEVEL_REVERSAL,
                     NEW_YORK_OPEN_REVERSAL):
        assert not ef.check(R2, DOWN_STORE, idea(strategy, SELL, EMA8 - 20)).allowed, strategy
        assert not ef.check(R2, DOWN_STORE, idea(strategy, BUY, EMA8 + 20)).allowed, strategy


def test_rule_2_uses_the_8_ema_at_the_last_finished_5_minute_candle_before_the_entry(R2, tmp_path):
    five = flat_5m() + [c("5m", AT, 5, 13100, 13100, 13100, 13100)]          # the 12:00 candle, far below
    st = store_with(tmp_path, down_hours(), TUE_DOWN, five=five, name="later")
    buy = D("13170")                                                          # 5 below 13175
    assert ef.check(R2, st, idea(LEVEL_REVERSAL, BUY, buy, t=AT + timedelta(minutes=3))).allowed   # 12:00 not finished
    e8, cndl = ef.ema8_at(R2, st, AT + timedelta(minutes=5))
    assert cndl.start == AT and e8 == EMA8 + (D("13100") - EMA8) * 2 / 9   # the 12:00 candle counts once finished
    v = ef.check(R2, st, idea(LEVEL_REVERSAL, BUY, buy, t=AT + timedelta(minutes=5)))
    assert not v.allowed and v.details["ema8_5m"] == "13158.3" and v.details["ema8_candle"] == "2026-11-18T12:00Z"


# ---- both rules and the switches -----------------------------------------------------------------------------------

def test_left_out_rule_1_is_on_and_rule_2_is_off_since_21_november(tmp_path, pretend_switches):
    s = settings(tmp_path, pretend_switches, None, None)
    assert s.switches.hourly_context is True and s.switches.entry_near_ema8 is False   # rule 2 replaced by 2b
    f = s.entry_filters
    assert (f.hourly_swing_candles_each_side, f.hourly_ema_periods, f.hourly_ema_slope_candles,
            f.hourly_context_near_pips, f.ema8_periods, f.ema8_max_distance_pips) == (2, 50, 6, D("5"), 8, D("5"))


def test_each_switch_off_turns_off_only_its_own_rule(BOTH, R1, R2, NONE, DOWN_STORE):
    near_pivot_buy = idea(LEVEL_REVERSAL, BUY, PIVOT_DOWN)                 # rule 1 refuses; 11.7 below the 8 EMA
    far_sell = idea(LEVEL_REVERSAL, SELL, EMA8 - 10)                       # rule 2 refuses; DOWN leaves sells alone
    assert ef.check(BOTH, DOWN_STORE, near_pivot_buy).rule == ef.HOURLY_CONTEXT
    assert ef.check(BOTH, DOWN_STORE, far_sell).rule == ef.ENTRY_NEAR_EMA8
    assert ef.check(R1, DOWN_STORE, near_pivot_buy).rule == ef.HOURLY_CONTEXT
    assert ef.check(R1, DOWN_STORE, far_sell).allowed
    assert ef.check(R2, DOWN_STORE, near_pivot_buy).allowed
    assert ef.check(R2, DOWN_STORE, far_sell).rule == ef.ENTRY_NEAR_EMA8
    for i in (near_pivot_buy, far_sell):
        v = ef.check(NONE, DOWN_STORE, i)
        assert v.allowed and v.checked == []


def test_when_both_would_refuse_rule_1_is_given(BOTH, DOWN_STORE):
    v = ef.check(BOTH, DOWN_STORE, idea(LEVEL_REVERSAL, BUY, ema50(BOTH, DOWN_STORE).quantize(D("0.1"))))
    assert not v.allowed and v.rule == ef.HOURLY_CONTEXT                    # also far above the 8 EMA


def test_a_trade_outside_both_rules_is_allowed_with_what_was_checked(BOTH, DOWN_STORE):
    v = ef.check(BOTH, DOWN_STORE, idea(LEVEL_REVERSAL, SELL, EMA8 - 2))
    assert v.allowed and v.rule == "" and len(v.checked) == 2
    assert v.checked[0].startswith("hourly context: DOWN context") and "allowed" in v.checked[1]


# ---- the single check point in the trading engine -------------------------------------------------------------------

from tests.technical import test_trading as tt  # noqa: E402

REAL_CHECK = ef.check


@pytest.fixture
def S_ON(tmp_path, pretend_switches):
    from tests.technical.test_orders import Over
    s = load_settings(switches_from=pretend_switches).for_pair("GBPUSD")
    return Over(s, switches={k: True for k in ("slow_grind", "ema_pullback", "bollinger_bounce", "range_trade",
                                                 "breakout", "level_reversal", "hourly_context", "entry_near_ema8")}
                | {"trading": True},
                orders={"folder": tmp_path / "orders"}, trade_manager={"folder": tmp_path / "tm"},
                safety={"folder": tmp_path / "safety"}, records={"folder": tmp_path / "records"},
                trading={"pause_file": tmp_path / "control" / "pause_new_trades"},
                dashboard={"status_folder": tmp_path / "status"})


def _engine(S, monkeypatch, verdict):
    from trading import engine as eng
    calls = []

    def check(s, store, i, trend=None):
        calls.append((i.strategy, i.direction, i.entry_price))
        return verdict
    monkeypatch.setattr(eng.entry_filters, "check", check)
    ideas = {tt.C[1].start: [tt.idea(RANGE_TRADE, tt.C[1].start)]}
    e, ig, tracker, clock, quote = tt.make(S, monkeypatch, tt.C, ideas, trading_on=True)
    e.start(tt.WED)
    tt.feed(e, clock, tt.C[:3])
    return e, ig, calls


def _decisions(e, S):
    import json
    files = sorted(Path(S.records.folder).rglob("decisions.jsonl"))
    return [json.loads(x) for f in files for x in f.read_text().splitlines()]


def test_engine_a_refused_trade_is_never_sent_and_the_refusal_is_recorded(S_ON, monkeypatch):
    v = ef.Verdict(False, ef.ENTRY_NEAR_EMA8, "a SELL more than 5 pips below the 5-minute 8 EMA: made up",
                   {"entry_price": "100", "ema8_5m": "106.0", "pips_beyond_ema8": "6.0"})
    e, ig, calls = _engine(S_ON, monkeypatch, v)
    assert calls == [(RANGE_TRADE, SELL, D("100"))]                         # once, for the one trade
    assert ig.orders_sent() == [] and e.manager.trades == {}
    (r,) = [d for d in _decisions(e, S_ON) if d["kind"] == "entry filter refused"]
    assert r["rule"] == ef.ENTRY_NEAR_EMA8 and r["details"]["pips_beyond_ema8"] == "6.0" and "made up" in r["why"]
    (o,) = [d for d in _decisions(e, S_ON) if d["kind"] == "order"]
    assert o["result"] == "entry filter refused" and o["reasons"][0].startswith(ef.ENTRY_NEAR_EMA8)


def test_engine_an_allowed_trade_is_sent_exactly_as_without_the_filters(S_ON, monkeypatch, tmp_path):
    e, ig, calls = _engine(S_ON, monkeypatch, ef.Verdict(True, checked=["hourly context: none", "entry near: ok"]))
    (o,) = ig.orders_sent()
    assert calls == [(RANGE_TRADE, SELL, D("100"))]
    (t,) = e.manager.trades.values()
    rec = e.meta[t.reference]
    assert "entry filters: hourly context: none; entry near: ok" in rec["steps"]
    # the same trade with both switches off (the real check): the same order to IG (apart from its reference)
    monkeypatch.setattr(ef, "check", REAL_CHECK)
    from tests.technical.test_orders import Over
    off = Over(S_ON, switches={"hourly_context": False, "entry_near_ema8": False},
               orders={"folder": tmp_path / "o2"}, trade_manager={"folder": tmp_path / "tm2"},
               safety={"folder": tmp_path / "s2"}, records={"folder": tmp_path / "r2"})
    ideas = {tt.C[1].start: [tt.idea(RANGE_TRADE, tt.C[1].start)]}
    e2, ig2, _, clock2, _ = tt.make(off, monkeypatch, tt.C, ideas, trading_on=True)
    e2.start(tt.WED)
    tt.feed(e2, clock2, tt.C[:3])
    (o2,) = ig2.orders_sent()
    strip = lambda b: {k: v for k, v in b.items() if k != "dealReference"}  # noqa: E731
    assert strip(o[3]) == strip(o2[3])
