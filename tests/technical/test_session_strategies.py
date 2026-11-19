"""Technical tests for the three session strategies (design 3.7 to 3.9; owner, 16 November 2026, with the owner's
answers 1 to 15 of that day): the Asian range breakout, the session sweep and the New York open reversal; what
they share with the Bollinger bounce (no analyser, the trail, one at a time each way, not held back by the most at
once); and the once-a-day safety rule. Made-up candles on Wednesday 4 November 2026 (GMT: UK time is UTC); GBPUSD in
the tests: 1 point = 1 pip. Nothing here contacts IG."""

from datetime import datetime, time, timedelta, timezone
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from config.settings_loader import SettingsError, load_settings
from prices.model import Candle
from safety.rules import AccountFunds, OpenTrade, decide, order_for
from strategies.asian_range_breakout.strategy import AsianRangeBreakout
from strategies.common import (ASIAN_RANGE_BREAKOUT, BUY, EMA_PULLBACK, NEW_YORK_OPEN_REVERSAL, SELL, SESSION_STRATEGIES,
                               SESSION_SWEEP, Candidate, Idea, check, closed_before_big_news, closed_on_level_rejection,
                               counts_towards_most_at_once, forced_close_at, may_open, stop_loss_pips, stop_price,
                               take_profit_pips, trail)
from strategies.new_york_open_reversal.strategy import NewYorkOpenReversal
from strategies.session_sweep.strategy import SessionSweep
from trade_manager.manager import plan

U = lambda *a: datetime(*a, tzinfo=timezone.utc)  # noqa: E731
WED = U(2026, 11, 4)
SPREAD = D("1.5")


class Over:
    """The settings with some sections changed."""
    def __init__(self, base, **sections):
        self.base, self.sections = base, {}
        for name, values in sections.items():
            items = {k: v for k, v in vars(getattr(base, name)).items() if not k.startswith("_")}
            self.sections[name] = SimpleNamespace(**(items | values))

    def __getattr__(self, name):
        return self.sections[name] if name in self.sections else getattr(self.base, name)


@pytest.fixture
def S(pretend_switches):
    s = load_settings(switches_from=pretend_switches).for_pair("GBPUSD")
    return Over(s, switches={"asian_range_breakout": True, "session_sweep": True, "new_york_open_reversal": True})


def at(hh, mm, day=WED):
    return day + timedelta(hours=hh, minutes=mm)


def C(t, o, h, l, c):
    o, h, l, c = (D(str(x)) for x in (o, h, l, c))
    return Candle("5m", t, t + timedelta(minutes=5), o + SPREAD, h + SPREAD, l + SPREAD, c + SPREAD, o, h, l, c)


def run(strategy, candles):
    """Every candidate, with the candle it opened at."""
    out = []
    for c in candles:
        out += [(c.start, x) for x in strategy.on_candle(c)]
    return out


def asian(high=105, low=95, day=WED):
    """00:00 to 06:55 UK: 84 candles between `low` and `high`."""
    out = [C(at(0, 5 * k, day), 100, 101, 99, 100) for k in range(84)]
    out[10] = C(out[10].start, 100, high, 99, 100)
    out[20] = C(out[20].start, 100, 101, low, 100)
    return out


# ---- 3.7 the Asian range breakout -----------------------------------------------------------------------------

def test_asian_breakout_buy_at_the_next_candles_open(S):
    cs = asian() + [C(at(7, 0), 100, 106, 100, 105.5), C(at(7, 5), 105.6, 107, 105, 106)]
    ((t, x),) = run(AsianRangeBreakout(S), cs)
    assert (t, x.strategy, x.direction, x.entry_price) == (at(7, 5), ASIAN_RANGE_BREAKOUT, BUY, D("105.6"))
    assert x.context["once_a_day"] == "Asian range breakout buy 2026-11-04"
    assert "above the Asian high" in x.steps[0] and "high 105, low 95" in x.steps[0]


def test_asian_breakout_sell_below_the_low(S):
    cs = asian() + [C(at(8, 0), 100, 100, 94, 94.9), C(at(8, 5), 94.8, 95, 93, 94)]
    (t, x), *_ = run(AsianRangeBreakout(S), cs)
    assert (t, x.direction, x.entry_price, x.context["once_a_day"]) == (at(8, 5), SELL, D("94.8"),
                                                                        "Asian range breakout sell 2026-11-04")


def test_asian_breakout_needs_a_close_beyond_not_a_wick_nor_a_close_on_the_line(S):
    cs = asian() + [C(at(7, 0), 100, 110, 100, 105), C(at(7, 5), 100, 100, 90, 95), C(at(7, 10), 100, 101, 99, 100)]
    assert run(AsianRangeBreakout(S), cs) == []


def test_asian_breakout_only_from_7_to_10_and_the_range_until_7(S):
    cs = asian()
    cs[-1] = C(at(6, 55), 100, 110, 100, 109)                   # 06:55 is still the range: its high is the range's
    cs += [C(at(7, 0), 109, 109.5, 108, 109.4)]                 # below the new high 110: nothing
    assert run(AsianRangeBreakout(S), cs + [C(at(7, 5), 100, 101, 99, 100)]) == []
    late = asian() + [C(at(10, 0), 100, 106, 100, 105.5), C(at(10, 5), 105, 106, 104, 105)]
    assert run(AsianRangeBreakout(S), late) == []
    last = asian() + [C(at(9, 55), 100, 106, 100, 105.5), C(at(10, 0), 105.4, 106, 104, 105)]
    assert [t for t, _ in run(AsianRangeBreakout(S), last)] == [at(10, 0)]   # a 09:55 close opens at 10:00


def test_asian_breakout_every_close_beyond_gives_an_idea_the_safety_rules_keep_one_a_day(S):
    cs = asian() + [C(at(7, 0), 100, 106, 100, 105.5), C(at(7, 5), 105.6, 107, 105, 106),
                    C(at(7, 10), 106, 107, 105, 106.5)]
    got = run(AsianRangeBreakout(S), cs)
    assert [t for t, _ in got] == [at(7, 5), at(7, 10)]
    assert {x.context["once_a_day"] for _, x in got} == {"Asian range breakout buy 2026-11-04"}


def test_asian_breakout_a_new_day_has_a_new_range(S):
    thu = WED + timedelta(days=1)
    cs = asian() + asian(high=120, low=110, day=thu) + [C(at(7, 0, thu), 115, 116, 114, 115)]
    assert run(AsianRangeBreakout(S), cs) == []                 # inside Thursday's range (above Wednesday's)


def test_asian_breakout_times_are_settings(S):
    s = Over(S, asian_range_breakout={"breakout_until": time(7, 5)})
    cs = asian() + [C(at(7, 5), 100, 106, 100, 105.5), C(at(7, 10), 105, 106, 104, 105)]
    assert run(AsianRangeBreakout(s), cs) == []


# ---- 3.8 the session sweep ------------------------------------------------------------------------------------

def test_sweep_sell_at_the_asian_high_with_its_stop(S):
    cs = asian() + [C(at(8, 0), 104, 108, 103, 104),            # 3 pips above 105, closes back below: rejection
                    C(at(8, 5), 104, 104.5, 101, 102),          # closes below its low 103: confirmation
                    C(at(8, 10), 102.2, 103, 101, 102)]
    ((t, x),) = run(SessionSweep(S), cs)
    assert (t, x.strategy, x.direction, x.entry_price) == (at(8, 10), SESSION_SWEEP, SELL, D("102.2"))
    assert x.context["furthest"] == D(108) and x.context["level_name"] == "Asian high"
    assert x.context["stop_price"] == D("114.2")                # 108 + 1 = 109 is under 12 pips: entry + 12
    assert x.context["once_a_day"] == "session sweep Asian high 2026-11-04"


def test_sweep_stop_one_pip_beyond_the_furthest_point_when_that_is_further(S):
    cs = asian() + [C(at(8, 0), 104, 120, 103, 104), C(at(8, 5), 104, 104.5, 101, 102), C(at(8, 10), 102, 103, 101, 102)]
    ((_, x),) = run(SessionSweep(S), cs)
    assert x.context["stop_price"] == D(121)


def test_sweep_needs_at_least_3_pips_beyond(S):
    near = asian() + [C(at(8, 0), 104, D("107.9"), 103, 104), C(at(8, 5), 104, 104.5, 101, 102),
                      C(at(8, 10), 102, 103, 101, 102)]
    assert run(SessionSweep(S), near) == []
    exact = asian() + [C(at(8, 0), 104, 108, 103, 104), C(at(8, 5), 104, 104.5, 101, 102), C(at(8, 10), 102, 103, 101, 102)]
    assert len(run(SessionSweep(S), exact)) == 1


def test_sweep_price_may_stay_beyond_for_a_while(S):
    cs = asian() + [C(at(8, 0), 104, 106, 104, 106), C(at(9, 0), 106, 110, 106, 109),   # closes above, twice
                    C(at(11, 0), 109, 109, 103, 104),           # back below: the rejection candle
                    C(at(11, 5), 104, 104, 102, 102.5), C(at(11, 10), 102.4, 103, 102, 102)]
    ((t, x),) = run(SessionSweep(S), cs)
    assert t == at(11, 10) and x.context["furthest"] == D(110)


def test_sweep_cancelled_above_the_rejection_candles_high_and_expires_after_3_candles(S):
    base = asian() + [C(at(8, 0), 104, 108, 103, 104)]
    cancel = base + [C(at(8, 5), 104, D("108.1"), 101, 102), C(at(8, 10), 102, 103, 101, 102)]
    assert run(SessionSweep(S), cancel) == []
    slow = base + [C(at(8, 5), 104, 105, 103.5, 104), C(at(8, 10), 104, 105, 103.5, 104),
                   C(at(8, 15), 104, 105, 103.5, 104), C(at(8, 20), 104, 104, 101, 102), C(at(8, 25), 102, 103, 101, 102)]
    assert run(SessionSweep(S), slow) == []


def test_sweep_buy_at_the_asian_low_mirror(S):
    cs = asian() + [C(at(8, 0), 96, 97, 92, 96), C(at(8, 5), 96, 99, 95.5, 98), C(at(8, 10), 97.8, 99, 97, 98)]
    ((_, x),) = run(SessionSweep(S), cs)
    assert (x.direction, x.entry_price, x.context["stop_price"]) == (BUY, D("97.8"), D("85.8"))


def test_sweep_london_levels_from_12_from_the_7_to_12_range(S):
    london = [C(at(7, 0) + timedelta(minutes=5 * k), 100, 101, 99, 100) for k in range(60)]   # 07:00 to 11:55
    london[30] = C(london[30].start, 100, 112, 99, 100)         # the London high 112 (also above the Asian high)
    sweep = [C(at(12, 0), 111, 115, 110, 111), C(at(12, 5), 111, 111, 108, 109), C(at(12, 10), 109, 110, 108, 109)]
    names = [x.context["level_name"] for _, x in run(SessionSweep(S), asian() + london + sweep)]
    assert names == ["London high"]
    before = asian() + london[:20] + [C(at(8, 40), 104, 108, 103, 104), C(at(8, 45), 104, 104.5, 101, 102),
                                      C(at(8, 50), 102, 103, 101, 102)]
    assert [x.context["level_name"] for _, x in run(SessionSweep(S), before)] == ["Asian high"]


def test_sweep_settings_change_it(S):
    s = Over(S, session_sweep={"beyond_pips": D(4), "min_stop_pips": 5})
    cs = asian() + [C(at(8, 0), 104, 108, 103, 104), C(at(8, 5), 104, 104.5, 101, 102), C(at(8, 10), 102, 103, 101, 102)]
    assert run(SessionSweep(s), cs) == []
    s = Over(S, session_sweep={"min_stop_pips": 5})
    ((_, x),) = run(SessionSweep(s), cs)
    assert x.context["stop_price"] == D(109)


# ---- 3.9 the New York open reversal -----------------------------------------------------------------------------

def ny_day(move_to=131, day=WED):
    """07:00 opens at 100; price walks to `move_to` by the 13:25 close."""
    n = 78                                                       # 07:00 to 13:25
    out = []
    for k in range(n):
        a = D(100) + (D(move_to) - 100) * k / n
        b = D(100) + (D(move_to) - 100) * (k + 1) / n
        out.append(C(at(7, 5 * k, day), a, max(a, b) + D("0.5"), min(a, b) - D("0.5"), b))
    return out


def test_ny_reversal_sell_after_a_rise(S):
    cs = ny_day() + [C(at(13, 30), 131, 132, 130.5, 131.5),     # green: not a rejection
                     C(at(13, 35), 131.5, 132, 129, 130),       # red: the rejection candle (low 129)
                     C(at(13, 40), 130, 131, 127, 128),         # closes below 129: confirmation
                     C(at(13, 45), D("127.9"), 128, 126, 127)]
    ((t, x),) = run(NewYorkOpenReversal(S), cs)
    assert (t, x.strategy, x.direction, x.entry_price) == (at(13, 45), NEW_YORK_OPEN_REVERSAL, SELL, D("127.9"))
    assert x.context["once_a_day"] == "New York open reversal 2026-11-04"
    assert "31.0 pips (up, at least 30)" in x.steps[0]


def test_ny_reversal_buy_after_a_fall(S):
    cs = ny_day(69) + [C(at(13, 30), 69, 71, 68.5, 70), C(at(13, 35), 70, 72, 69.5, 71.5), C(at(13, 40), 71.6, 72, 71, 72)]
    ((_, x),) = run(NewYorkOpenReversal(S), cs)
    assert (x.direction, x.entry_price) == (BUY, D("71.6"))


def test_ny_reversal_needs_30_pips(S):
    cs = ny_day(D("129.9")) + [C(at(13, 35), 129.9, 130, 129, 129.5), C(at(13, 40), 129.5, 130, 127, 128),
                               C(at(13, 45), 128, 128, 126, 127)]
    assert run(NewYorkOpenReversal(S), cs) == []


def test_ny_reversal_both_candles_in_the_window(S):
    early = ny_day()[:-1] + [C(at(13, 25), 131, 131.5, 129, 130), C(at(13, 30), 130, 130, 127, 128),
                             C(at(13, 35), 128, 128, 126, 127)]       # the 13:25 red candle is before the window
    assert run(NewYorkOpenReversal(S), early) == []
    late = ny_day() + [C(at(13, 30) + timedelta(minutes=5 * k), 131, 131.5, 130.8, 131.2) for k in range(17)] + \
        [C(at(14, 55), 131.5, 132, 129, 130), C(at(15, 0), 130, 131, 127, 128), C(at(15, 5), 128, 128, 126, 127)]
    assert run(NewYorkOpenReversal(S), late) == []
    last = ny_day() + [C(at(14, 50), 131.5, 132, 129, 130), C(at(14, 55), 130, 131, 127, 128),
                       C(at(15, 0), 128, 128, 126, 127)]
    assert [t for t, _ in run(NewYorkOpenReversal(S), last)] == [at(15, 0)]


def test_ny_reversal_cancelled_above_the_rejection_candles_high(S):
    cs = ny_day() + [C(at(13, 35), 131.5, 132, 129, 130), C(at(13, 40), 130, D("132.1"), 127, 128),
                     C(at(13, 45), 128, 128, 126, 127)]
    got = run(NewYorkOpenReversal(S), cs)
    assert got == []                                             # 13:40 is red too, but nothing confirms it


def test_ny_reversal_not_on_a_day_with_big_news_at_13_30(S):
    ev = lambda t, c, e: {"time_utc": t, "country": c, "event": e, "estimate": 1, "prev": 1, "actual": None,  # noqa: E731
                          "impact": "high", "unit": ""}
    nfp = ev("2026-11-04T13:30:00Z", "US", "Non Farm Payrolls")
    t = U(2026, 11, 4, 14, 0)
    assert any("big news is released at 13:30 UK today" in r
               for r in may_open(S, "GBPUSD", NEW_YORK_OPEN_REVERSAL, t, [nfp]))
    noon = ev("2026-11-04T12:00:00Z", "GB", "BoE Interest Rate Decision")
    assert not any("13:30" in r for r in may_open(S, "GBPUSD", NEW_YORK_OPEN_REVERSAL, t, [noon]))
    assert not any("13:30 UK today" in r for r in may_open(S, "GBPUSD", SESSION_SWEEP, t, [nfp]))


# ---- what the three share ------------------------------------------------------------------------------------

def _state(st, d="none"):
    return SimpleNamespace(state=st, direction=d, trend_type=None)


@pytest.mark.parametrize("name", SESSION_STRATEGIES)
def test_no_analyser_state_no_direction_rule(S, name):
    for st, d in (("consolidation", "none"), ("ranging", "none"), ("trend", "up"), ("emerging trend", "down"),
                  ("possible reversal", "up")):
        for direction in (BUY, SELL):
            ctx = {"stop_price": D(200) if direction == SELL else D(0)} if name == SESSION_SWEEP else {}
            i = check(S, "GBPUSD", Candidate(name, direction, at(8, 0), D(100), ["made up"], ctx), _state(st, d),
                      D(150) if direction == BUY else D(50), D(150) if direction == BUY else D(50))
            assert i.allowed, (name, st, d, direction, i.blocked_by)


@pytest.mark.parametrize("name,switch", [(ASIAN_RANGE_BREAKOUT, "asian_range_breakout"),
                                         (SESSION_SWEEP, "session_sweep"),
                                         (NEW_YORK_OPEN_REVERSAL, "new_york_open_reversal")])
def test_each_has_its_own_switch(S, name, switch):
    off = Over(S, switches={switch: False})
    i = check(off, "GBPUSD", Candidate(name, SELL, at(8, 0), D(100), [], {"stop_price": D(112)}), _state("ranging"),
              None, None)
    assert not i.allowed and f"STRATEGY_{switch.upper()} is off" in i.blocked_by


@pytest.mark.parametrize("name", SESSION_STRATEGIES)
def test_exits_hours_and_news(S, name):
    assert take_profit_pips(S, name) == 100
    assert trail(S, name) == (D(12), 3)
    assert forced_close_at(S, name, U(2026, 11, 4, 10, 0)) == U(2026, 11, 4, 20, 30)
    assert closed_before_big_news(name) and not closed_on_level_rejection(name)
    assert counts_towards_most_at_once(name)
    assert "outside the trading hours 06:00 to 20:30 UK" in may_open(S, "GBPUSD", name, U(2026, 11, 4, 20, 30), [])
    assert may_open(S, "GBPUSD", name, U(2026, 11, 4, 6, 0), []) == []


def test_stops(S):
    assert stop_loss_pips(S, ASIAN_RANGE_BREAKOUT) == 12 and stop_loss_pips(S, NEW_YORK_OPEN_REVERSAL) == 12
    assert stop_loss_pips(S, SESSION_SWEEP) == 12
    sweep = SimpleNamespace(strategy=SESSION_SWEEP, context={"stop_price": D("114.2")})
    assert stop_price(S, sweep) == D("114.2")
    assert stop_price(S, SimpleNamespace(strategy=ASIAN_RANGE_BREAKOUT, context={})) is None
    s = Over(S, asian_range_breakout={"stop_loss_pips": 15}, new_york_open_reversal={"stop_loss_pips": 9})
    assert (stop_loss_pips(s, ASIAN_RANGE_BREAKOUT), stop_loss_pips(s, NEW_YORK_OPEN_REVERSAL)) == (15, 9)


@pytest.mark.parametrize("name,section", [(ASIAN_RANGE_BREAKOUT, "asian_range_breakout"), (SESSION_SWEEP, "session_sweep"),
                                          (NEW_YORK_OPEN_REVERSAL, "new_york_open_reversal")])
def test_the_trail_is_each_strategys_own(S, name, section):
    tr = plan(S, "T", name, SELL, U(2026, 11, 4, 9, 0), D(100), D(100), D(12), [])
    assert (tr.trail_from, tr.trail_candles) == (D(12), 3)
    s = Over(S, **{section: {"trail_from_pips": D(15), "trail_candles": 4}})
    tr = plan(s, "T", name, SELL, U(2026, 11, 4, 9, 0), D(100), D(100), D(12), [])
    assert (tr.trail_from, tr.trail_candles) == (D(15), 4)


# ---- the safety rules: one at a time each way, not held back by the most at once, once a day --------------------

def _idea(name, direction=SELL, once="", stop=None):
    ctx = {"once_a_day": once} if once else {}
    if name == SESSION_SWEEP:
        ctx["stop_price"] = stop or (D("13412.0") if direction == SELL else D("13388.0"))
    return Idea("GBPUSD", name, direction, U(2026, 11, 4, 9, 0), D("13400.0"), "trend", "down", None, "sell side",
                ["made up"], True, "", ctx)


def _go(S, i, open_trades=(), used=None):
    funds = AccountFunds(D(20000), i.time - timedelta(minutes=30))
    return decide(S, order_for(S, i), list(open_trades), funds, i.time, False, [], used_once_a_day=used)   # no "day" (one view at a time is not in first-build-plus)


@pytest.mark.parametrize("name", SESSION_STRATEGIES)
def test_one_at_a_time_in_each_direction(S, name):
    sell = OpenTrade(name, SELL, U(2026, 11, 4, 8, 0), D(12), D(10))
    assert _go(S, _idea(name, BUY), [sell]).allowed
    d = _go(S, _idea(name, SELL), [sell])
    assert not d.allowed and "already has 1 sell trade(s) open (at most 1 each way)" in d.reasons[0]


@pytest.mark.parametrize("name", SESSION_STRATEGIES)
def test_not_held_back_by_the_most_at_once(S, name):
    five = [OpenTrade(s, BUY, U(2026, 11, 4, 8, 0), D(6), D(10))
            for s in ("range trade", "breakout", "slow grind", "level reversal", "Bollinger bounce")]
    assert _go(S, _idea(name), five).allowed


def test_once_a_day(S):
    key = "Asian range breakout sell 2026-11-04"
    d = _go(S, _idea(ASIAN_RANGE_BREAKOUT, once=key), used={key})
    assert not d.allowed and d.reasons == ["once a day: a Asian range breakout trade has already opened for "
                                           "sell 2026-11-04"]
    assert _go(S, _idea(ASIAN_RANGE_BREAKOUT, once=key), used={"Asian range breakout buy 2026-11-04"}).allowed
    assert _go(S, _idea(ASIAN_RANGE_BREAKOUT, once=key)).allowed
    assert _go(S, _idea(EMA_PULLBACK), used={key}).allowed


def test_the_sweeps_order_uses_its_stop_price(S):
    o = order_for(S, _idea(SESSION_SWEEP, SELL, stop=D("13415.0")))
    assert o.stop_pips == D(15)


# ---- the settings -------------------------------------------------------------------------------------------

def test_the_owners_numbers_are_the_settings(S):
    a, w, n = S.asian_range_breakout, S.session_sweep, S.new_york_open_reversal
    assert (a.range_from, a.range_until, a.breakout_from, a.breakout_until, a.stop_loss_pips) == \
        (time(0), time(7), time(7), time(10), 12)
    assert (w.asian_range_from, w.asian_range_until, w.london_range_from, w.london_range_until) == \
        (time(0), time(7), time(7), time(12))
    assert (w.beyond_pips, w.confirmation_within_candles, w.stop_beyond_furthest_pips, w.min_stop_pips) == (3, 3, 1, 12)
    assert (n.move_from, n.move_until, n.min_move_pips, n.window_from, n.window_until, n.confirmation_within_candles,
            n.no_trade_if_big_news_at, n.stop_loss_pips) == (time(7), time(13, 30), 30, time(13, 30), time(15), 3,
                                                             time(13, 30), 12)
    for sec in (a, w, n):
        assert (sec.trail_from_pips, sec.trail_candles) == (12, 3)


def test_a_from_after_its_until_is_refused(tmp_path):
    import tomllib
    from config.settings_loader import DEFAULT_PATH
    raw = DEFAULT_PATH.read_text().replace('breakout_from = "07:00"', 'breakout_from = "10:30"')
    assert tomllib.loads(raw)["asian_range_breakout"]["breakout_from"] == "10:30"
    p = tmp_path / "settings.toml"
    p.write_text(raw)
    with pytest.raises(SettingsError, match=r"\[asian_range_breakout\] breakout_from must be earlier than breakout_until"):
        load_settings(p)
