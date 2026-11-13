"""Technical tests for the safety rules (design sections 4, 6 and 7), with made-up ideas, open trades,
available funds, IG refusals and times. Nothing here contacts IG or trades."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from config.settings_loader import load_settings
from safety.rules import AccountFunds, OpenTrade, Order, decide, order_for
from strategies.common import (BOLLINGER_BOUNCE, BREAKOUT, BUY, EMA_PULLBACK, LEVEL_REVERSAL, RANGE_TRADE, SELL,
                               SLOW_GRIND, Idea)

U = lambda *a: datetime(*a, tzinfo=timezone.utc)  # noqa: E731
WED = U(2026, 11, 4, 10, 0)                         # Wednesday 10:00 UK (GMT), no news
BOE_CAL = [{"time_utc": "2026-11-05T12:00:00Z", "country": "GB", "event": "BoE Interest Rate Decision",
            "estimate": 4.0, "prev": 4.0, "actual": None, "impact": "high", "unit": "%"}]
ALL = (EMA_PULLBACK, BOLLINGER_BOUNCE, RANGE_TRADE, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL)


class Over:
    """The real settings with some values of sections changed."""
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
    return Over(s, switches={k: True for k in ("slow_grind", "ema_pullback", "bollinger_bounce", "range_trade",
                                                 "breakout", "level_reversal")})


def idea(strategy, direction=SELL, t=WED, price="13400.0", allowed=True, blocked="", context=None):
    ctx = context if context is not None else ({"stop_price": D("13410.0")} if strategy == LEVEL_REVERSAL else {})
    return Idea("GBPUSD", strategy, direction, t, D(price), "trend", "down", None, "sell side", ["made up"],
                allowed, blocked, ctx)


def funds(available="20000", t=WED):
    return AccountFunds(D(available), t - timedelta(minutes=30))


def go(S, i, open_trades=(), t=None, paused=False, money="enough", size=None, stop=None, calendar=()):
    t = t or i.time
    o = order_for(S, i)
    if size is not None or stop is not None:
        o = Order(i, D(size) if size is not None else o.size_gbp_per_pip, D(stop) if stop is not None else o.stop_pips)
    f = funds(t=t) if money == "enough" else money
    return decide(S, o, list(open_trades), f, t, paused, list(calendar))


def opened(strategy, direction=BUY, stop="6", size="10"):
    return OpenTrade(strategy, direction, WED - timedelta(hours=1), D(stop), D(size))


# ---- everything allowed ----------------------------------------------------------------------

@pytest.mark.parametrize("strategy", ALL)
def test_every_strategy_may_open_when_every_check_passes(S, strategy):
    d = go(S, idea(strategy))
    assert d.allowed and d.reasons == []


# ---- the pause switch, the idea's checks, the switch -------------------------------------------

@pytest.mark.parametrize("strategy", ALL)
def test_the_pause_switch_blocks_every_new_trade(S, strategy):
    d = go(S, idea(strategy), paused=True)
    assert not d.allowed and d.reasons == ["the pause switch is on: no new trades"]


def test_a_blocked_idea_is_refused_with_its_reason(S):
    d = go(S, idea(BOLLINGER_BOUNCE, allowed=False, blocked="the analyser's state is consolidation"))
    assert d.reasons == ["the idea was blocked: the analyser's state is consolidation"]


@pytest.mark.parametrize("strategy,switch", [(SLOW_GRIND, "slow_grind"), (EMA_PULLBACK, "ema_pullback"),
                                             (BOLLINGER_BOUNCE, "bollinger_bounce"), (RANGE_TRADE, "range_trade"),
                                             (BREAKOUT, "breakout"), (LEVEL_REVERSAL, "level_reversal")])
def test_the_switch_is_checked_again_even_for_an_allowed_idea(S, strategy, switch):
    s = Over(S, switches=vars(S.switches) | {switch: False})
    d = go(s, idea(strategy))
    assert d.reasons == [f"its switch STRATEGY_{switch.upper()} is off"]


# ---- hours, news and Friday rules (design 4 and 6) ------------------------------------------------

@pytest.mark.parametrize("strategy,t,ok", [
    (BOLLINGER_BOUNCE, U(2026, 11, 4, 5, 55), False), (BOLLINGER_BOUNCE, U(2026, 11, 4, 6, 0), True),
    (BOLLINGER_BOUNCE, U(2026, 11, 4, 20, 30), False), (RANGE_TRADE, U(2026, 11, 4, 20, 25), True),
    (RANGE_TRADE, U(2026, 11, 4, 22, 0), False), (LEVEL_REVERSAL, U(2026, 11, 4, 5, 0), False),
    (BREAKOUT, U(2026, 11, 4, 21, 0), False), (BREAKOUT, U(2026, 11, 4, 20, 25), True),
    (EMA_PULLBACK, U(2026, 11, 4, 3, 0), True), (EMA_PULLBACK, U(2026, 11, 4, 23, 0), True),
    (SLOW_GRIND, U(2026, 11, 4, 3, 0), True), (SLOW_GRIND, U(2026, 11, 4, 20, 30), False),
    (SLOW_GRIND, U(2026, 11, 4, 23, 55), False), (SLOW_GRIND, U(2026, 11, 5, 0, 0), True),
])
def test_each_strategys_hours(S, strategy, t, ok):
    d = go(S, idea(strategy, t=t))
    assert d.allowed is ok, d.reasons


def test_big_news_stops_the_bounce_range_trade_and_level_reversal_only(S):
    t = U(2026, 11, 5, 11, 50)                       # BoE at 12:00: no new trades 11:45 to 12:30
    for strategy in (BOLLINGER_BOUNCE, RANGE_TRADE, LEVEL_REVERSAL):
        d = go(S, idea(strategy, t=t), calendar=BOE_CAL)
        assert any("big-news window: BoE Interest Rate Decision" in r for r in d.reasons), strategy
    for strategy in (EMA_PULLBACK, BREAKOUT, SLOW_GRIND):
        assert go(S, idea(strategy, t=t), calendar=BOE_CAL).allowed, strategy


@pytest.mark.parametrize("t", [U(2026, 11, 6, 20, 30), U(2026, 11, 6, 21, 50), U(2026, 10, 23, 19, 30)])  # last: BST
def test_no_ema_pullback_after_20_30_uk_on_friday(S, t):
    assert any("after 20:30 UK on Friday" in r for r in go(S, idea(EMA_PULLBACK, t=t)).reasons)


def test_nothing_opens_while_the_market_is_closed(S):
    for strategy in ALL:
        assert "the market is closed" in go(S, idea(strategy, t=U(2026, 11, 7, 12, 0))).reasons


# ---- trades open at once (design 6) ----------------------------------------------------------------

@pytest.mark.parametrize("strategy", (RANGE_TRADE, BREAKOUT, SLOW_GRIND))
def test_one_trade_at_a_time_for_each_strategy(S, strategy):
    d = go(S, idea(strategy), [opened(strategy)])
    assert d.reasons == [f"{strategy} already has 1 trade(s) open (at most 1)"]
    assert go(S, idea(strategy), [opened(s) for s in (RANGE_TRADE, BREAKOUT, SLOW_GRIND, LEVEL_REVERSAL)
                                  if s != strategy]).allowed


def test_the_level_reversal_may_have_two_at_once(S):
    # owner, 13 November 2026: level_reversal.max_open_trades, 2
    assert S.level_reversal.max_open_trades == 2
    assert go(S, idea(LEVEL_REVERSAL), [opened(LEVEL_REVERSAL)]).allowed
    d = go(S, idea(LEVEL_REVERSAL), [opened(LEVEL_REVERSAL), opened(LEVEL_REVERSAL)])
    assert d.reasons == ["level reversal already has 2 trade(s) open (at most 2)"]
    assert go(S, idea(RANGE_TRADE), [opened(RANGE_TRADE)]).reasons == ["range trade already has 1 trade(s) open (at most 1)"]


def test_the_bounce_may_have_one_each_way(S):
    assert go(S, idea(BOLLINGER_BOUNCE, SELL), [opened(BOLLINGER_BOUNCE, BUY)]).allowed
    d = go(S, idea(BOLLINGER_BOUNCE, BUY), [opened(BOLLINGER_BOUNCE, BUY)])
    assert d.reasons == ["Bollinger bounce already has 1 buy trade(s) open (at most 1 each way)"]
    d = go(S, idea(BOLLINGER_BOUNCE, SELL), [opened(BOLLINGER_BOUNCE, BUY), opened(BOLLINGER_BOUNCE, SELL)])
    assert not d.allowed
    s = Over(S, limits=vars(S.limits) | {"bollinger_bounce_extra_opposite_direction_trades": 0})
    assert "Bollinger bounce already has 1 trade(s) open (at most 1)" in \
        go(s, idea(BOLLINGER_BOUNCE, SELL), [opened(BOLLINGER_BOUNCE, BUY)]).reasons


def test_the_ema_pullback_has_no_limit_of_its_own(S):
    assert go(S, idea(EMA_PULLBACK), [opened(EMA_PULLBACK) for _ in range(12)]).allowed


FIVE = [opened(BOLLINGER_BOUNCE, BUY), opened(BOLLINGER_BOUNCE, SELL), opened(RANGE_TRADE), opened(BREAKOUT),
        opened(SLOW_GRIND)]


def test_a_sixth_counted_trade_is_refused_but_an_ema_pullback_is_not(S):
    d = go(S, idea(LEVEL_REVERSAL), FIVE)
    assert d.reasons == ["5 trades open that count towards the most at once (5; EMA pullback trades not counted)"]
    assert go(S, idea(EMA_PULLBACK), FIVE).allowed


def test_ema_pullback_trades_do_not_count_towards_the_5(S):
    assert go(S, idea(LEVEL_REVERSAL), FIVE[:4] + [opened(EMA_PULLBACK) for _ in range(6)]).allowed


def test_the_most_at_once_is_a_setting(S):
    s = Over(S, limits=vars(S.limits) | {"max_open_trades": 2})
    assert "2 trades open that count towards the most at once (2; EMA pullback trades not counted)" in \
        go(s, idea(LEVEL_REVERSAL), FIVE[:2]).reasons
    assert S.limits.max_open_trades == 5


# ---- size and stop ---------------------------------------------------------------------------------

def test_the_size_is_10_pounds_a_pip(S):
    assert order_for(S, idea(BREAKOUT)).size_gbp_per_pip == D(10)
    assert go(S, idea(BREAKOUT), size="5").reasons == ["the size is £5 a pip, not £10"]
    assert go(S, idea(BREAKOUT), size="10.0").allowed


def test_each_strategys_stop_in_its_order(S):
    assert [order_for(S, idea(n)).stop_pips for n in ALL] == [D(12), D(6), D(6), D(12), D(15), D(10)]   # pretend .env STOP_LOSS_PIPS 6; breakout 12
    lr = idea(LEVEL_REVERSAL, BUY, price="13400.0", context={"stop_price": D("13387.5")})
    assert order_for(S, lr).stop_pips == D("12.5")                       # from the entry to its stop price


def test_igs_minimum_stop_is_not_checked_before_a_trade(S):
    """Owner, 8 November 2026: the bot assumes each strategy's own stop meets IG's minimum."""
    import inspect
    from safety import rules as r
    assert "dealing" not in inspect.signature(r.decide).parameters and not hasattr(r, "DealingRules")
    assert go(S, idea(BOLLINGER_BOUNCE), stop="0.5").allowed                    # any stop: IG decides


# ---- total risk (design 6) ---------------------------------------------------------------------

def test_total_risk_is_every_open_trades_stop_times_size_plus_the_new_one(S):
    s = Over(S, safety=vars(S.safety) | {"max_total_risk_gbp": 300})
    two = [opened(EMA_PULLBACK, stop="12"), opened(SLOW_GRIND, stop="15")]        # £120 + £150
    assert go(s, idea(BREAKOUT), two).allowed is False                           # + £120 (its 12-pip stop) = £390
    assert go(s, idea(BREAKOUT), two).reasons == \
        ["total risk £390.00 with this trade (its stop x its size, every open trade) is over £300.00"]
    assert go(s, idea(BREAKOUT), two[:1]).allowed                               # £240
    assert go(s, idea(BREAKOUT), [opened(EMA_PULLBACK, stop="12"), opened(SLOW_GRIND, stop="6.0")]).allowed  # £300 exactly


def test_the_owners_total_risk_limit_is_never_reached(S):
    assert S.safety.max_total_risk_gbp == 100000
    many = [opened(EMA_PULLBACK, stop="12") for _ in range(40)] + FIVE[:4]      # £5,040
    assert go(S, idea(LEVEL_REVERSAL), many).allowed


def test_the_level_reversals_risk_uses_its_own_stop_distance(S):
    s = Over(S, safety=vars(S.safety) | {"max_total_risk_gbp": 99})
    lr = idea(LEVEL_REVERSAL, context={"stop_price": D("13410.0")})            # 10 pips: £100
    assert "total risk £100.00" in go(s, lr).reasons[0]


# ---- available funds (design 6) ----------------------------------------------------------------

def test_a_new_trade_needs_the_margin_for_one_trade_available(S):
    assert S.safety.margin_per_trade_gbp == 5000
    assert go(S, idea(EMA_PULLBACK), money=funds("5000")).allowed
    d = go(S, idea(EMA_PULLBACK), money=funds("4999.99"))
    assert d.reasons == ["available funds £4,999.99 are less than the margin for one trade (£5,000.00)"]
    for name in ALL:
        assert not go(S, idea(name), money=funds("100")).allowed


def test_unknown_funds_refuse(S):
    assert go(S, idea(EMA_PULLBACK), money=None).reasons == \
        ["the account's available funds are not known (read from IG at start-up and whenever a trade opens or closes)"]


def test_the_funds_come_from_igs_account_details():
    t = U(2026, 11, 4, 9, 0)
    f = AccountFunds.from_ig({"balance": 10000.0, "deposit": 1200.0, "profitLoss": -35.5, "available": 8764.5}, t)
    assert (f.available, f.read_at) == (D("8764.5"), t)


def test_the_margin_is_a_setting(S):
    s = Over(S, safety=vars(S.safety) | {"margin_per_trade_gbp": 9000})
    assert "less than the margin for one trade (£9,000.00)" in go(s, idea(EMA_PULLBACK), money=funds("8000")).reasons[0]


# ---- every reason at once -------------------------------------------------------------------------

def test_every_reason_is_given(S):
    t = U(2026, 11, 5, 11, 50)
    d = go(S, idea(RANGE_TRADE, t=t, allowed=False, blocked="made up"), [opened(RANGE_TRADE)], paused=True,
           size="20", money=None, calendar=BOE_CAL)
    assert not d.allowed and len(d.reasons) == 6
    assert d.reasons[0] == "the pause switch is on: no new trades"
    assert "the idea was blocked: made up" in d.reasons and "the size is £20 a pip, not £10" in d.reasons


# ---- IG refusing a trade (design 7; safety/refusals.py) -------------------------------------------

import json  # noqa: E402

from ig.markets import MinStop  # noqa: E402
from safety.refusals import FUNDS, OTHER, STOP, min_stop_pips, on_refusal  # noqa: E402


class FakeAlerts:
    def __init__(self):
        self.sent = []

    def problem(self, key, text):
        self.sent.append((key, text))


def refusal(S, tmp_path, reason, read=None, funds_known=None):
    s = Over(S, safety=vars(S.safety) | {"folder": tmp_path / "safety"})
    calls = []

    def read_min_stop():
        calls.append(1)
        if isinstance(read, Exception):
            raise read
        return read or MinStop(8.0, "POINTS")
    alerts = FakeAlerts()
    kind = on_refusal(s, reason, BOLLINGER_BOUNCE, D("6"), D("13400.0"), read_min_stop, alerts, WED, funds_known)
    return kind, calls, alerts.sent, tmp_path / "safety" / "ig_min_stop_refusals.jsonl"


def test_a_stop_refusal_fetches_igs_minimum_once_records_it_and_alerts(S, tmp_path):
    kind, calls, sent, rec = refusal(S, tmp_path, "ATTACHED_ORDER_LEVEL_ERROR")
    assert kind == STOP and calls == [1]
    (key, text), = sent
    assert "IG refused a Bollinger bounce trade" in text and "stop is 6.0 pips" in text
    assert "IG's minimum stop distance is now 8.0 pips" in text and "The stop was not changed." in text
    row = json.loads(rec.read_text().splitlines()[-1])
    assert (row["strategy"], row["stop_pips"], row["ig_min_pips"], row["ig_min_unit"]) == (BOLLINGER_BOUNCE, "6.0", "8.0", "POINTS")


def test_a_stop_refusal_still_alerts_if_igs_minimum_cannot_be_read(S, tmp_path):
    kind, calls, sent, rec = refusal(S, tmp_path, "ATTACHED_ORDER_LEVEL_ERROR", read=RuntimeError("no reply"))
    assert kind == STOP and calls == [1] and "not known (reading it from IG failed: no reply)" in sent[0][1]
    assert "ig_min_error" in json.loads(rec.read_text())


def test_igs_minimum_as_a_percentage(S, tmp_path):
    assert min_stop_pips(S, 0.05, "PERCENTAGE", D("13400.0")) == D("6.7")
    kind, _, sent, _ = refusal(S, tmp_path, "ATTACHED_ORDER_LEVEL_ERROR", read=MinStop(0.05, "PERCENTAGE"))
    assert "6.7 pips (0.05% of the price)" in sent[0][1]


def test_a_funds_refusal_alerts_without_fetching_anything(S, tmp_path):
    kind, calls, sent, rec = refusal(S, tmp_path, "INSUFFICIENT_FUNDS", funds_known=D("1234.5"))
    assert kind == FUNDS and calls == [] and not rec.exists()
    assert sent == [("ig-funds-refused", "IG refused a Bollinger bounce trade at Wed 04 Nov 10:00 GMT for lack of funds "
                                         "(INSUFFICIENT_FUNDS); available funds last read £1,234.50.")]


def test_any_other_refusal_is_left_to_the_order_sender(S, tmp_path):
    kind, calls, sent, rec = refusal(S, tmp_path, "MARKET_CLOSED")
    assert (kind, calls, sent, rec.exists()) == (OTHER, [], [], False)


# ---- the two IG reads (ig/): the account's funds, and the minimum stop after a refusal -----------

class FakeReply:
    def __init__(self, body, status=200):
        self.body, self.status_code = body, status

    def json(self):
        return self.body


def test_igs_minimum_stop_read_from_the_market():
    from ig.markets import min_stop
    seen = []

    class Client:
        def request(self, method, path, version, body=None, *, what):
            seen.append((method, path, version))
            return FakeReply({"dealingRules": {"minNormalStopOrLimitDistance": {"unit": "POINTS", "value": 2.0}}})
    assert min_stop(Client(), "CS.D.GBPUSD.TODAY.IP") == MinStop(2.0, "POINTS")
    assert seen == [("GET", "/markets/CS.D.GBPUSD.TODAY.IP", "3")]


def test_the_accounts_balance_read_from_ig(monkeypatch):
    from ig.client import IGClient
    from ig.errors import IGRequestError
    c = IGClient.__new__(IGClient)
    c._creds = SimpleNamespace(account_id="ABC123")
    reply = {"accounts": [{"accountId": "XYZ999", "balance": {"available": 1.0}},
                          {"accountId": "ABC123", "balance": {"balance": 10000.0, "available": 8764.5}}]}
    monkeypatch.setattr(IGClient, "request", lambda self, m, p, v, body=None, *, what: FakeReply(reply))
    assert c.account_balance() == {"balance": 10000.0, "available": 8764.5}
    c._creds = SimpleNamespace(account_id="NOPE")
    with pytest.raises(IGRequestError, match="account-not-in-reply"):
        c.account_balance()


# ---- 9. one view at a time (owner, 9 November 2026; docs/research/one_view_20261109.md rank 1) -------------

from analyser.day_direction import DayDirections, day_directions, friday_move_pips  # noqa: E402
from safety.rules import is_reversal, trend_direction  # noqa: E402


def seen(strategy, direction, state="trend", state_direction="down", trend_type=None, t=WED):
    i = idea(strategy, direction, t)
    i.state, i.state_direction, i.trend_type = state, state_direction, trend_type
    return i


def go_day(S, i, day):
    return decide(S, order_for(S, i), [], funds(t=i.time), i.time, False, [], day)


@pytest.mark.parametrize("state,sd,want", [("trend", "down", SELL), ("trend", "up", BUY), ("emerging trend", "up", BUY),
                                           ("possible reversal", "up", SELL), ("possible reversal", "down", BUY),
                                           ("ranging", "none", None), ("consolidation", "none", None)])
def test_the_analysers_trend_direction(state, sd, want):
    assert trend_direction(seen(LEVEL_REVERSAL, BUY, state, sd)) == want


@pytest.mark.parametrize("state,sd", [("trend", "down"), ("possible reversal", "up"), ("possible reversal", "down"),
                                      ("ranging", "none")])
@pytest.mark.parametrize("direction", [BUY, SELL])
def test_every_bollinger_bounce_is_a_reversal(state, sd, direction):
    assert is_reversal(seen(BOLLINGER_BOUNCE, direction, state, sd))


@pytest.mark.parametrize("state,sd,direction,want", [
    ("trend", "down", BUY, True), ("trend", "down", SELL, False),
    ("emerging trend", "up", SELL, True), ("emerging trend", "up", BUY, False),
    ("possible reversal", "up", BUY, True),          # a possible reversal up: against the down trend being reversed
    ("possible reversal", "up", SELL, False),
    ("ranging", "none", BUY, False), ("ranging", "none", SELL, False)])
def test_a_level_reversal_is_a_reversal_only_against_the_trend(state, sd, direction, want):
    assert is_reversal(seen(LEVEL_REVERSAL, direction, state, sd)) is want


@pytest.mark.parametrize("strategy", [EMA_PULLBACK, SLOW_GRIND, BREAKOUT, RANGE_TRADE])
@pytest.mark.parametrize("direction", [BUY, SELL])
def test_the_other_strategies_are_never_reversals(strategy, direction):
    assert not is_reversal(seen(strategy, direction, "trend", "down", "strong push"))


def test_no_reversal_trade_against_a_strong_push(S):
    for strategy in (BOLLINGER_BOUNCE, LEVEL_REVERSAL):
        d = go(S, seen(strategy, BUY, "trend", "down", "strong push"))
        assert not d.allowed and d.reasons == ["a reversal trade against a strong push (down)"], strategy


def test_a_reversal_against_a_slow_grind_trend_and_trades_with_a_strong_push_are_allowed(S):
    assert go(S, seen(BOLLINGER_BOUNCE, BUY, "trend", "down", "slow grind")).allowed
    assert go(S, seen(LEVEL_REVERSAL, SELL, "trend", "down", "strong push")).allowed      # with the push
    for strategy in (EMA_PULLBACK, SLOW_GRIND, BREAKOUT):
        assert go(S, seen(strategy, SELL, "trend", "down", "strong push")).allowed, strategy


def test_a_possible_reversal_is_not_a_strong_push(S):
    assert go(S, seen(BOLLINGER_BOUNCE, BUY, "possible reversal", "up")).allowed


@pytest.mark.parametrize("day,why", [
    (DayDirections(news=SELL), "a big-news day, expected news direction sell"),
    (DayDirections(trend_day=SELL), "a trend day, direction sell"),
    (DayDirections(monday=SELL, friday_move_pips=D("85.0")),
     "the Monday after a Friday that moved +85.0 pips, direction sell")])
def test_no_reversal_trade_against_the_days_direction(S, day, why):
    for i in (seen(BOLLINGER_BOUNCE, BUY, "possible reversal", "up"), seen(LEVEL_REVERSAL, BUY, "trend", "down")):
        d = go_day(S, i, day)
        assert not d.allowed and d.reasons == [f"a reversal trade against the day's direction: {why}"], i.strategy
    assert go_day(S, seen(BOLLINGER_BOUNCE, SELL, "trend", "up"), day).allowed          # in the day's direction


def test_every_day_direction_it_goes_against_is_given(S):
    day = DayDirections(news=SELL, trend_day=SELL, monday=BUY, friday_move_pips=D("-90.0"))
    d = go_day(S, seen(BOLLINGER_BOUNCE, BUY, "trend", "down", "strong push"), day)
    assert d.reasons == ["a reversal trade against a strong push (down)",
                         "a reversal trade against the day's direction: a big-news day, expected news direction sell",
                         "a reversal trade against the day's direction: a trend day, direction sell"]
    d = go_day(S, seen(BOLLINGER_BOUNCE, SELL, "trend", "up"), day)
    assert d.reasons == ["a reversal trade against the day's direction: the Monday after a Friday that moved "
                         "-90.0 pips, direction buy"]


@pytest.mark.parametrize("strategy", [EMA_PULLBACK, SLOW_GRIND, BREAKOUT, RANGE_TRADE])
def test_the_days_direction_does_not_change_the_other_strategies(S, strategy):
    day = DayDirections(news=SELL, trend_day=SELL, monday=SELL, friday_move_pips=D("100"))
    assert go_day(S, seen(strategy, BUY, "trend", "up"), day).allowed
    assert go_day(S, seen(strategy, BUY, "ranging", "none"), day).allowed


def test_a_level_reversal_in_ranging_is_not_refused_on_an_exception_day(S):
    assert go_day(S, seen(LEVEL_REVERSAL, BUY, "ranging", "none"), DayDirections(news=SELL)).allowed


def test_no_day_directions_and_an_ordinary_day_change_nothing(S):
    i = seen(BOLLINGER_BOUNCE, BUY, "possible reversal", "up")
    assert go_day(S, i, None).allowed and go_day(S, i, DayDirections()).allowed


# ---- the day's directions (analyser/day_direction.py) -------------------------------------------------

class DailyStore:
    """Daily candles only: {UTC start: (sell open, sell close)}."""
    def __init__(self, days):
        self.days = days

    def read_range(self, tf, a, b):
        assert tf == "1d"
        return [SimpleNamespace(start=t, sell_open=D(o), sell_close=D(c), buy_open=D(o) + 1, buy_close=D(c) + 1)
                for t, (o, c) in self.days.items() if a <= t < b]


FRI_6 = U(2026, 11, 6, 0, 0)                        # Friday 6 November 00:00 UK (GMT)
MON_9 = U(2026, 11, 9, 9, 0)


def test_the_fridays_move_is_its_daily_candles_sell_open_to_close(S):
    assert friday_move_pips(S, DailyStore({FRI_6: ("13500.0", "13392.4")}), MON_9.date()) == D("-107.6")
    assert friday_move_pips(S, DailyStore({}), MON_9.date()) is None


@pytest.mark.parametrize("close,want", [("13420.0", BUY), ("13420.1", None), ("13580.0", SELL), ("13579.9", None)])
def test_the_monday_after_a_friday_that_moved_80_pips_or_more(S, close, want):
    got = day_directions(S, DailyStore({FRI_6: ("13500.0", close)}), MON_9, [], None)
    assert got.monday == want and got.news is None and got.trend_day is None


def test_the_80_pips_is_a_setting(S):
    s = Over(S, safety={"big_friday_move_pips": 120})
    store = DailyStore({FRI_6: ("13500.0", "13392.4")})
    assert day_directions(s, store, MON_9, [], None).monday is None
    assert day_directions(S, store, MON_9, [], None).monday == BUY


def test_only_a_monday_looks_at_friday(S):
    store = DailyStore({FRI_6: ("13500.0", "13300.0"), U(2026, 11, 9, 0, 0): ("13300.0", "13100.0")})
    assert day_directions(S, store, U(2026, 11, 10, 9, 0), [], None).monday is None      # Tuesday


def test_the_trend_day_gives_its_direction(S):
    store = DailyStore({})
    assert day_directions(S, store, WED, [], "down").trend_day == SELL
    assert day_directions(S, store, WED, [], "up").trend_day == BUY
    assert day_directions(S, store, WED, [], None).trend_day is None


def test_the_big_news_days_expected_direction(S):
    cal = [{"time_utc": "2026-11-05T12:00:00Z", "country": "GB", "event": "BoE Interest Rate Decision",
            "estimate": 3.75, "prev": 4.0, "actual": None, "impact": "high", "unit": "%"}]
    from trade_manager.manager import day_news_direction
    want = day_news_direction(S, "GBPUSD", U(2026, 11, 5, 8, 0), cal)
    assert want in (BUY, SELL)
    assert day_directions(S, DailyStore({}), U(2026, 11, 5, 8, 0), cal, None).news == want
    assert day_directions(S, DailyStore({}), U(2026, 11, 4, 8, 0), cal, None).news is None
