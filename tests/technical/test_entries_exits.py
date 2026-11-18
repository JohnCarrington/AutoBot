"""Technical tests for stage 4, entries and exits (owner, 18 November 2026): SCALE_OUT_REVERSAL, TRAIL_NO_LOSS,
LR_ENTRY_NEAR_LEVEL (each off if left out of .env) and the start-up line listing every switch. Made-up trades and the
stored 17 November candles of tests/technical/test_trail_17_november.py; never contacts IG."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from strategies.common import BOLLINGER_BOUNCE, BUY, LEVEL_REVERSAL, RANGE_TRADE, SELL, allowed, near_level_reasons
from tests.technical.test_orders import S, idea, make, records  # noqa: F401  (S is the fixture)
from tests.technical.test_trade_manager import Over, bar, bars_from
from tests.technical.test_trail_17_november import CANDLES, FILL, IG_MIN_STOP, LIMIT, STOP, U, bar as bar17, feed
from trade_manager.manager import (CLOSE, HALF_CLOSE, STOP_MOVED, STOPPED_BY_IG, TradeManager, plan, scale_out, step)


def on(S, tmp_path, **switches):
    names = {k: v for k, v in vars(S.switches).items() if not k.startswith("_")}
    return Over(S, switches=names | switches, trade_manager={"folder": tmp_path / "tm"})


class Sender:
    """A paper-like order sender: closes and stop moves are done at once."""
    def __init__(self):
        self.closes, self.moves = [], []

    def close(self, reference, *, half=False, why="", price=None):
        self.closes.append((half, why))
        return SimpleNamespace(what="half closed" if half else "closed", ok=True)

    def move_stop(self, reference, level, why=""):
        self.moves.append((level, why))
        return SimpleNamespace(what="stop moved", ok=True, level=level)


T0 = U(2026, 11, 4, 10, 0)


def lr_sell(s, entry="100.0"):
    return plan(s, "R1", LEVEL_REVERSAL, SELL, T0, D(entry), D(entry), D(12), [])


# ---- SCALE_OUT_REVERSAL ---------------------------------------------------------------------------------------------

def test_scale_out_only_for_the_level_reversal_and_the_range_trade_and_only_while_on(S, tmp_path):
    s = on(S, tmp_path, scale_out_reversal=True)
    assert scale_out(s, LEVEL_REVERSAL) == (D(8), D(2)) and scale_out(s, RANGE_TRADE) == (D(8), D(2))
    assert scale_out(s, BOLLINGER_BOUNCE) is None
    assert scale_out(on(S, tmp_path), LEVEL_REVERSAL) is None


def test_half_closed_at_8_in_profit_and_the_stop_on_the_rest_moved_to_2_in_profit(S, tmp_path):
    s = on(S, tmp_path, scale_out_reversal=True)
    sender = Sender()
    m = TradeManager(s, sender, now=lambda: T0)
    t = lr_sell(s, "13200.0")
    m.add(t)
    # a sell closes on the buy price (sell + 1.5): +8 when the buy price reaches 13192.0, the sell price 13190.5
    m.on_bar(bar(T0, 13199, 13199.5, 13195, 13196), finished=True)
    assert sender.closes == [] and t.state == "hold"
    got = m.on_bar(bar(T0 + timedelta(minutes=5), 13196, 13196.5, 13190.0, 13191), finished=True)
    (tr, d), = [(x, y) for x, y in got if y.kind == HALF_CLOSE]
    assert d.price == D("13192.0") and d.pips == D(8) and d.part == D("0.5")
    assert sender.closes == [(True, d.why)] and "the scale-out" in d.why
    assert sender.moves[0][0] == D("13198.0")                 # 2 pips in profit for the sell
    assert t.stop_level == D("13198.0") and t.scaled
    # the rest: stopped at the moved stop, 2 pips in profit
    m.on_bar(bar(T0 + timedelta(minutes=10), 13192, 13197.0, 13191, 13196.9), finished=True)
    assert t.state == STOPPED_BY_IG and t.decisions[-1].pips == D(2) and t.decisions[-1].part == D("0.5")
    assert t.total_pips() == D(5)


def test_the_rest_runs_on_to_the_level_reversals_take_profit(S, tmp_path):
    s = on(S, tmp_path, scale_out_reversal=True)
    t = lr_sell(s, "13200.0")
    out = []
    for b in bars_from(T0, [(13199, 13199.5, 13190, 13191), (13191, 13191, 13175, 13176)]):
        out += step(s, t, b)
    assert [d.kind for d in out] == [HALF_CLOSE, "take profit hit at IG"]
    assert t.total_pips() == D(14)                              # half at 8, half at 20


def test_switch_off_no_scale_out(S, tmp_path):
    s = on(S, tmp_path)
    t = lr_sell(s, "13200.0")
    out = step(s, t, bar(T0, 13199, 13199.5, 13190, 13191))
    assert out == [] and not t.half_done


def range_sell(s):
    return plan(s, "R2", RANGE_TRADE, SELL, T0, D("13200.0"), D("13200.0"), D(12), [])


def test_the_range_trade_reaching_the_opposite_band_before_8_closes_in_full(S, tmp_path):
    s = on(S, tmp_path, scale_out_reversal=True)
    t = range_sell(s)
    band = (D("13210"), D("13195"))                             # the lower band 13195: 3.5 pips up on the buy price
    out = step(s, t, bar(T0 + timedelta(minutes=5), 13199, 13199.5, 13189, 13190), band)
    assert [d.kind for d in out] == [CLOSE] and not t.scaled and out[0].why == "the opposite Bollinger band"


def test_the_range_trade_after_its_scale_out_closes_the_rest_at_the_opposite_band(S, tmp_path):
    s = on(S, tmp_path, scale_out_reversal=True)
    t = range_sell(s)
    out = step(s, t, bar(T0 + timedelta(minutes=5), 13199, 13199.5, 13190, 13191), (D("13210"), D("13180")))
    assert [d.kind for d in out] == [HALF_CLOSE]
    out = step(s, t, bar(T0 + timedelta(minutes=10), 13191, 13191, 13179, 13180), (D("13210"), D("13180")))
    assert [d.kind for d in out] == [CLOSE] and out[0].part == D("0.5") and out[0].why == "the opposite Bollinger band"


def test_a_refused_scale_out_stop_move_is_tried_3_times(S, tmp_path):
    s = on(S, tmp_path, scale_out_reversal=True)
    clock = {"t": T0}

    class Refusing(Sender):
        def move_stop(self, reference, level, why=""):
            self.moves.append((level, why))
            return SimpleNamespace(what="stop not moved", ok=False, level=level, reasons=["refused"])

    sender = Refusing()
    sender.alerts = SimpleNamespace(sent=[], problem=lambda k, t: sender.alerts.sent.append(k), info=lambda t: None)
    m = TradeManager(s, sender, now=lambda: clock["t"], ig_confirms=True)
    t = lr_sell(s, "13200.0")
    m.add(t)
    sender.closed_at_ig = lambda *a: SimpleNamespace(ok=False, what="")
    m.on_bar(bar(T0, 13196, 13196.5, 13190, 13191), finished=True)
    for k in range(1, 4):
        clock["t"] = T0 + timedelta(seconds=40 * k)
        m.on_bar(bar(clock["t"], *[D("13191")] * 4))
    assert [x[0] for x in sender.moves] == [D("13198.0")] * 3
    assert len(sender.alerts.sent) == 1 and t.stop_level is None and t.trail_want is None


# ---- TRAIL_NO_LOSS --------------------------------------------------------------------------------------------------

def the_17_november_trade(S, tmp_path, **switches):
    from tests.technical.test_orders import idea as order_idea
    s = on(S, tmp_path, **switches)
    sender, ig, alerts, sleeps, clock = make(s)
    r = sender.place(order_idea(BOLLINGER_BOUNCE, SELL), calendar=[])
    pos = next(p for p in ig.positions if p["position"]["dealId"] == r.deal_id)
    pos["position"].update(level=float(FILL), stopLevel=float(STOP), limitLevel=float(LIMIT))
    ig.min_stop = IG_MIN_STOP
    m = TradeManager(s, sender, ig_confirms=True, now=lambda: clock["t"])
    m.add(plan(s, r.reference, BOLLINGER_BOUNCE, SELL, U(2026, 11, 17, 10, 5), D("13190.1"), FILL, D(12), []))
    return sender, ig, clock, m, pos, r


def test_17_november_the_first_trail_move_goes_to_the_entry_not_the_losing_side(S, tmp_path):
    """Live: 13193.2 at 13:35 (above the 13189.9 entry; the 13:30 candle had a 6.5-pip spread). With TRAIL_NO_LOSS the
    13:30 candle (6.5 at its open) and the 13:25 candle (4.6 at its close) are left out; the last 3 normal candles are
    13:15, 13:20 and 13:35, buy high 13193.7, so 13193.8, still on the losing side of the entry: the stop goes to the
    entry, 13189.9."""
    sender, ig, clock, m, pos, r = the_17_november_trade(S, tmp_path, trail_no_loss=True)
    shown = feed(sender, ig, clock, m, pos, CANDLES, upto="13:35")
    assert shown[-1] == ("13:35", [("stop move sending", "13189.9", "13189.9", "13174.5"),
                                   ("stop moved", None, "13189.9", None)])
    assert m.trades[r.reference].stop_level == FILL


def test_17_november_off_the_trail_is_as_before(S, tmp_path):
    sender, ig, clock, m, pos, r = the_17_november_trade(S, tmp_path)
    shown = feed(sender, ig, clock, m, pos, CANDLES, upto="13:35")
    assert shown[-1][1][0][1] == "13193.2"


def test_a_spread_spike_candle_is_left_out_of_the_last_3(S, tmp_path):
    s = on(S, tmp_path, trail_no_loss=True)
    m = TradeManager(s, Sender())
    assert m._spike(bar17(CANDLES[4]))                         # 13:30: buy 13193.1 / sell 13186.6 at the open
    assert m._spike(bar17(CANDLES[3]))                         # 13:25: buy 13191.6 / sell 13187.0 at the close
    assert not m._spike(bar17(CANDLES[2]))                     # 13:20: 1.5 throughout


def test_a_trail_level_on_the_winning_side_is_used_as_it_is(S, tmp_path):
    sender, ig, clock, m, pos, r = the_17_november_trade(S, tmp_path, trail_no_loss=True)
    feed(sender, ig, clock, m, pos, CANDLES, upto="13:45")
    # 13:45: the last 3 normal candles 13:35, 13:40, 13:45: buy high 13181.5, so 13181.6 (sent as IG allows)
    last = [x for x in records(sender) if x["event"] == "stop move sending"][-1]
    assert last["rule_level"] == "13181.6"


# ---- LR_ENTRY_NEAR_LEVEL --------------------------------------------------------------------------------------------

CTX = {"level": D("13202.4"), "level_name": "R2 13202.4"}


@pytest.mark.parametrize("price,ok", [("13196.4", True), ("13196.3", False), ("13208.4", True), ("13217.2", False)])
def test_a_level_reversal_opens_only_within_6_pips_of_its_level(S, tmp_path, price, ok):
    s = on(S, tmp_path, lr_entry_near_level=True)
    got = near_level_reasons(s, LEVEL_REVERSAL, D(price), CTX)
    assert (got == []) == ok
    if not ok:
        assert got[0].startswith(f"LR_ENTRY_NEAR_LEVEL: the entry {price} is ") and "R2 13202.4" in got[0]


def test_the_near_level_rule_is_off_if_left_out_and_only_for_the_level_reversal(S, tmp_path):
    assert near_level_reasons(on(S, tmp_path), LEVEL_REVERSAL, D("13217.2"), CTX) == []
    assert near_level_reasons(on(S, tmp_path, lr_entry_near_level=True), RANGE_TRADE, D("13217.2"), CTX) == []


def test_the_refusal_is_recorded_with_the_distance(S, tmp_path):
    s = on(S, tmp_path, lr_entry_near_level=True)
    state = SimpleNamespace(state="ranging", direction="none", trend_type=None)
    reasons, _ = allowed(s, LEVEL_REVERSAL, BUY, D("13217.2"), state, D("13200"), D("13200"), None,
                         context={"level": D("13202.4"), "level_name": "R2 13202.4"})
    assert "LR_ENTRY_NEAR_LEVEL: the entry 13217.2 is 14.8 pips from the level it traded (R2 13202.4), more than 6" \
        in reasons


# ---- the start-up line ----------------------------------------------------------------------------------------------

def test_one_startup_line_lists_every_switch(S, tmp_path):
    from config.switches import SWITCHES
    from prices.service import switches_line
    line = switches_line(on(S, tmp_path, trail_no_loss=True))
    assert line.startswith("Switches from .env: ") and "\n" not in line
    for name in SWITCHES:
        assert f"{name}=" in line
    assert "TRAIL_NO_LOSS=on" in line and "SCALE_OUT_REVERSAL=off" in line


# ---- LEVEL_STOPS ----------------------------------------------------------------------------------------------------

from strategies.common import EMA_PULLBACK, level_stop_context, level_stop_price  # noqa: E402


def lv(t, p):
    return SimpleNamespace(type=t, price=D(p))


# the 17 November 07:35 picture: the pivot 13194.4 on its own, round number 13200 and the New York high 13205.2
LEVELS = SimpleNamespace(groups=[
    {"low": D("13168.0"), "high": D("13172.8"), "members": [lv("previous_day_low", "13168.0"), lv("london_session_low", "13172.8")]},
    {"low": D("13194.4"), "high": D("13194.4"), "members": [lv("pivot", "13194.4")]},
    {"low": D("13200"), "high": D("13200"), "members": [lv("round_number", "13200")]},
    {"low": D("13205.2"), "high": D("13205.2"), "members": [lv("new_york_session_high", "13205.2")]},
])


def test_level_stops_find_the_nearest_group_beyond_the_entry(S, tmp_path):
    s = on(S, tmp_path, level_stops=True)
    sell = level_stop_context(s, LEVEL_REVERSAL, SELL, D("13191.7"), LEVELS)
    assert sell["level_stop_edge"] == D("13194.4") and sell["level_stop_group"] == "13194.4 to 13194.4 (pivot 13194.4)"
    buy = level_stop_context(s, EMA_PULLBACK, BUY, D("13185.0"), LEVELS)
    assert buy["level_stop_edge"] == D("13168.0")           # the far edge of 13168.0 to 13172.8
    assert level_stop_context(on(S, tmp_path), LEVEL_REVERSAL, SELL, D("13191.7"), LEVELS) == {}   # off
    assert level_stop_context(s, BOLLINGER_BOUNCE, SELL, D("13191.7"), LEVELS) == {}


def test_level_stops_no_group_within_20_pips_keeps_the_strategys_own_stop(S, tmp_path):
    s = on(S, tmp_path, level_stops=True)
    got = level_stop_context(s, RANGE_TRADE, BUY, D("13188.1"), LEVELS)      # 13168.0 is 20.1 pips below
    assert "level_stop_edge" not in got and "20.1 pips away" in got["level_stop_none"]
    assert level_stop_context(s, RANGE_TRADE, BUY, D("13188.0"), LEVELS)["level_stop_edge"] == D("13168.0")   # 20.0
    i = idea(RANGE_TRADE, BUY, price="13188.1", context=got)
    assert level_stop_price(s, i) is None                   # the fixed 12 pips stays


def test_level_stops_5_beyond_the_group(S, tmp_path):
    s = on(S, tmp_path, level_stops=True)
    i = idea(LEVEL_REVERSAL, SELL, price="13191.7", context={"stop_price": D("13205.1"), "level_stop_edge": D("13194.4"),
                                                               "level_stop_group": "13194.4 to 13194.4 (pivot 13194.4)"})
    assert level_stop_price(s, i) == D("13199.4")           # replaces the level reversal's 13205.1
    b = idea(EMA_PULLBACK, BUY, price="13190.0", context={"level_stop_edge": D("13168.0")})
    assert level_stop_price(s, b) == D("13163.0")


def test_the_order_sender_adds_the_spread_for_a_sell_and_refuses_beyond_20(S, tmp_path):
    s = on(S, tmp_path, level_stops=True)
    sender, ig, alerts, sleeps, clock = make(s, quote=(D("13191.7"), D("13193.2")))
    from safety.rules import order_for
    i = idea(LEVEL_REVERSAL, SELL, price="13191.7", context={"stop_price": D("13205.1"), "level_stop_edge": D("13194.4"),
                                                               "level_stop_group": "13194.4 to 13194.4 (pivot 13194.4)"})
    dist, why = sender._stop_distance(i, order_for(s, i))
    assert (dist, why) == (D("9.2"), "")                   # 13194.4 + 5 + 1.5 spread = 13200.9, from the bid 13191.7
    far = idea(EMA_PULLBACK, SELL, price="13180.0", context={"level_stop_edge": D("13194.4"),
                                                              "level_stop_group": "13194.4 to 13194.4 (pivot 13194.4)"})
    sender2, *_ = make(s, quote=(D("13180.0"), D("13181.5")))
    dist, why = sender2._stop_distance(far, order_for(s, far))
    assert dist is None and why == ("LEVEL_STOPS: the stop 13200.9, 5 pips beyond the level group 13194.4 to 13194.4 "
                                    "(pivot 13194.4) plus the spread (at most 3), is 20.9 pips from the entry, more than 20")
    r = sender2.place(far, calendar=[])
    assert not r.ok and r.reasons == [why]
    assert records(sender2)[-1]["event"] == "safety refused"


def test_level_stops_off_the_stops_are_as_before(S, tmp_path):
    s = on(S, tmp_path)
    sender, *_ = make(s, quote=(D("13191.7"), D("13193.2")))
    from safety.rules import order_for
    i = idea(LEVEL_REVERSAL, SELL, price="13191.7", context={"stop_price": D("13205.1"), "level_stop_edge": D("13194.4")})
    assert sender._stop_distance(i, order_for(s, i)) == (D("13.4"), "")


def test_the_spread_added_to_a_sells_level_stop_is_capped_at_3(S, tmp_path):
    """6 November 13:30: the payrolls candle opened with a 15.7-pip spread. The EMA pullback sell at 13377.5, the group
    13373.9 to 13378.4: 13378.4 + 5 + 3 (capped) = 13386.4, 8.9 pips: it opens (21.6 pips, refused, without the cap)."""
    s = on(S, tmp_path, level_stops=True)
    sender, *_ = make(s, quote=(D("13377.5"), D("13393.2")))
    from safety.rules import order_for
    i = idea(EMA_PULLBACK, SELL, price="13377.5", context={"level_stop_edge": D("13378.4"),
                                                            "level_stop_group": "13373.9 to 13378.4"})
    assert sender._stop_distance(i, order_for(s, i)) == (D("8.9"), "")


def test_ig_refusing_the_opening_order_for_its_stop_is_recorded_and_not_sent_again(S, tmp_path):
    s = on(S, tmp_path, level_stops=True)
    sender, ig, alerts, sleeps, clock = make(s, quote=(D("13191.7"), D("13193.2")))
    ig.post_open = {"dealStatus": "REJECTED", "reason": "ATTACHED_ORDER_LEVEL_ERROR"}
    i = idea(LEVEL_REVERSAL, SELL, price="13191.7", context={"stop_price": D("13205.1"), "level_stop_edge": D("13194.4"),
                                                               "level_stop_group": "13194.4 to 13194.4 (pivot 13194.4)"})
    r = sender.place(i, calendar=[])
    assert not r.ok and r.what == "refused" and "ATTACHED_ORDER_LEVEL_ERROR" in r.reasons[0]
    refused = [x for x in records(sender) if x["event"] == "refused"]
    assert len(refused) == 1 and refused[0]["reason"] == "ATTACHED_ORDER_LEVEL_ERROR"
    opens = [c for c in ig.calls if c[0] == "POST" and c[1] == "/positions/otc"]
    assert len(opens) == 1                                  # sent once, never retried
