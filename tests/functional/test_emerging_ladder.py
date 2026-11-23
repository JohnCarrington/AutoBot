"""Functional tests for Johnny's exit for emerging-trend trades (owner, 21 November 2026; switch EMERGING_LADDER, on if
left out; [emerging_ladder]; trade_manager/manager.py), with the real settings.

Johnny's rules, as written:
  1. Applies only to trades opened when the market analyser said "emerging trend" (up or down), as recorded on the
     trade at open. Every strategy.
  2. Once the trade is +10 pips, move its stop at IG to +5.
  3. Once the trade is +15 pips, move its stop at IG to +10.
  4. The stop never moves backwards.
  5. If the strategy already has its own trail or stop move, use whichever stop is tighter (closer to the price, in
     the trade's favour) at each step.
  6. Measure profit as IG closes it: a buy on the sell price, a sell on the buy price.
  7. Stop moves go through the existing stop-move code, including the fix for IG refusing a stop move.
  8. Take profit unchanged. Trades opened in any other analyser state are unchanged.
  9. The numbers (10, 5, 15, 10) go in settings. Switch in .env: EMERGING_LADDER, on if left out.
 10. Record each stop move on the trade.

Prices in points (GBPUSD: 1 point = 1 pip). The made-up bars give the sell price; the buy price is 1.5 above. A buy
fills at the buy price and closes on the sell price; a sell fills at the sell price and closes on the buy price.
Nothing here contacts IG: the paper tests use a pretend order sender, the live tests the real order sender with the
pretend IG of tests/technical/test_orders.py.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from config.settings_loader import SettingsError, load_settings
from strategies.common import BOLLINGER_BOUNCE, BREAKOUT, BUY, EMA_PULLBACK, LEVEL_REVERSAL, SELL, SLOW_GRIND
from tests.technical.test_trade_manager import Over
from trade_manager.manager import (BY_LADDER, BY_TRAIL, STOP_MOVED, STOPPED_BY_IG, TAKE_PROFIT_AT_IG, Bar,
                                   TradeManager, ladder_applies, plan)

U = lambda *a: datetime(*a, tzinfo=timezone.utc)  # noqa: E731
WED = U(2026, 11, 18, 10, 0)
SPREAD = D("1.5")
UP, DOWN = "emerging trend up", "emerging trend down"


def settings(pretend_switches, tmp_path, ladder: str | None = "on", **sections):
    """The real settings with the tests' pretend switches and EMERGING_LADDER as given (None: left out)."""
    text = "".join(line + "\n" for line in pretend_switches.read_text().splitlines()
                   if not line.startswith("EMERGING_LADDER="))
    if ladder is not None:
        text += f"EMERGING_LADDER={ladder}\n"
    env = tmp_path / f"switches_{ladder}.env"
    env.write_text(text)
    return Over(load_settings(switches_from=env).for_pair("GBPUSD"),
                trade_manager={"folder": tmp_path / "tm"}, **sections)


@pytest.fixture
def ON(pretend_switches, tmp_path):
    return settings(pretend_switches, tmp_path, "on")


@pytest.fixture
def OFF(pretend_switches, tmp_path):
    return settings(pretend_switches, tmp_path, "off")


class Sender:
    """A pretend order sender (paper): every stop move is done at the level asked for, and recorded."""

    def __init__(self):
        self.moves, self.closes = [], []

    def move_stop(self, reference, level, why=""):
        self.moves.append((reference, level, why))
        return SimpleNamespace(ok=True, what="stop moved", level=level)

    def close(self, reference, half=False, why="", price=None):
        self.closes.append((reference, why, price))
        return SimpleNamespace(ok=True, what="closed")


def bar(t, o, h, l, c):
    """A 5-minute bar from sell prices; buy prices 1.5 above."""
    o, h, l, c = (D(str(x)) for x in (o, h, l, c))
    return Bar(t, o + SPREAD, h + SPREAD, l + SPREAD, c + SPREAD, o, h, l, c)


def new_trade(S, strategy=LEVEL_REVERSAL, direction=BUY, state=UP, entry="100", stop="12", ref="REF1"):
    """A trade at Wed 18 Nov 10:00: a buy fills at 101.5 (buy price), a sell at 100 (sell price)."""
    entry = D(entry)
    fill = entry + SPREAD if direction == BUY else entry
    return plan(S, ref, strategy, direction, WED, entry, fill, D(stop), [], None, market_state=state)


def manager(S, *trades):
    sender = Sender()
    m = TradeManager(S, sender, now=lambda: WED)
    for t in trades:
        m.add(t)
    return m, sender


def feed(m, rows, t0=WED, finished=True):
    """Each row (o, h, l, c, sell prices) as a finished 5-minute candle, 5 minutes apart."""
    for k, r in enumerate(rows):
        m.on_bar(bar(t0 + timedelta(minutes=5 * k), *r), finished=finished)


def moved(sender):
    return [level for _, level, _ in sender.moves]


# A buy filling at 101.5 that goes +10.5 (sell high 112), then +16 (sell high 117.5), never back near its stops.
BUY_UP = [(100, 101, 99.9, 100.5),        # the entry candle: best -0.5
          (100.5, 108, 100.4, 107.5),     # +6.5
          (107.5, 112, 107, 111.5),       # +10.5 -> stop to +5 = 106.5
          (111.5, 114, 110, 113.5),       # +12.5: nothing new
          (113.5, 117.5, 112.5, 117),     # +16 -> stop to +10 = 111.5
          (117, 118, 116, 117.5)]         # +16.5: nothing new
# A sell filling at 100 (sell price) that goes +10.5 (buy low 89.5 = sell low 88), then +16 (buy low 84 = sell low 82.5)
SELL_DOWN = [(100, 100.5, 99.2, 99.5),    # the entry candle
             (99.5, 99.8, 93, 93.5),      # buy low 94.5: +5.5
             (93.5, 94, 88, 88.5),        # buy low 89.5: +10.5 -> stop to +5 = 95
             (88.5, 90, 87, 87.5),        # +11.5
             (87.5, 88, 82.5, 83),        # buy low 84: +16 -> stop to +10 = 90
             (83, 84, 82, 83.5)]


# ---- rules 2, 3 and 6: both steps, buys and sells, measured as IG closes the trade ----------------------------------

def test_a_buy_moves_its_stop_to_plus_5_at_plus_10_then_to_plus_10_at_plus_15(ON):
    t = new_trade(ON, direction=BUY)
    m, sender = manager(ON, t)
    feed(m, BUY_UP)
    assert moved(sender) == [D("106.5"), D("111.5")]                 # fill 101.5 + 5, + 10
    assert t.stop_level == D("111.5") and t.open
    assert [(D(x["level"]), D(x["pips"]), x["by"]) for x in t.stop_moves] == [(D("106.5"), 5, BY_LADDER),
                                                                               (D("111.5"), 10, BY_LADDER)]


def test_a_sell_moves_its_stop_to_plus_5_at_plus_10_then_to_plus_10_at_plus_15(ON):
    t = new_trade(ON, direction=SELL, state=DOWN)
    m, sender = manager(ON, t)
    feed(m, SELL_DOWN)
    assert moved(sender) == [D("95"), D("90")]                       # fill 100 - 5, - 10
    assert t.stop_level == D("90") and t.open


def test_profit_is_measured_on_the_closing_price_not_the_chart_price(ON):
    # A buy: the sell price must be +10 above the fill (101.5), i.e. 111.5; the buy price reaching it is not enough.
    t = new_trade(ON, direction=BUY)
    m, sender = manager(ON, t)
    feed(m, [(100, 101, 99.9, 100.5), (100.5, 111.4, 100.4, 110)])      # sell high 111.4: +9.9 (buy high 112.9)
    assert sender.moves == [] and t.best == D("9.9")
    feed(m, [(110, 111.5, 109, 111)], t0=WED + timedelta(minutes=10))   # sell high 111.5: exactly +10
    assert moved(sender) == [D("106.5")]
    # A sell: the buy price must be 10 below the fill (100), i.e. 90; the sell price at 90 is only +8.5.
    s = new_trade(ON, direction=SELL, state=DOWN, ref="REF2")
    m2, sender2 = manager(ON, s)
    feed(m2, [(100, 100.5, 99.2, 99.5), (99.5, 99.8, 90, 90.5)])        # buy low 91.5: +8.5
    assert sender2.moves == [] and s.best == D("8.5")


def test_below_plus_10_nothing_moves(ON):
    t = new_trade(ON, direction=BUY)
    m, sender = manager(ON, t)
    feed(m, [(100, 101, 99.9, 100.5), (100.5, 111.3, 100.4, 109), (109, 111.4, 105, 106)])   # best +9.9
    assert sender.moves == [] and t.stop_level is None and t.stop_moves == []


def test_a_jump_straight_past_plus_15_moves_the_stop_once_to_plus_10(ON):
    t = new_trade(ON, direction=BUY)
    m, sender = manager(ON, t)
    feed(m, [(100, 101, 99.9, 100.5), (100.5, 118, 100.4, 117.5)])      # +16.5 in one candle
    assert moved(sender) == [D("111.5")]
    assert "+15 reached: stop to +10" in sender.moves[0][2]


def test_after_plus_10_the_trade_is_stopped_at_plus_5_when_price_comes_back(ON):
    t = new_trade(ON, direction=BUY)
    m, sender = manager(ON, t)
    feed(m, BUY_UP[:3] + [(111.5, 111.5, 104, 105)])                    # back to sell low 104: through 106.5
    assert not t.open and t.decisions[-1].kind == STOPPED_BY_IG
    assert (t.decisions[-1].price, t.decisions[-1].pips) == (D("106.5"), D("5"))
    s = new_trade(ON, direction=SELL, state=DOWN, ref="REF2")
    m2, _ = manager(ON, s)
    feed(m2, SELL_DOWN[:5] + [(83, 92, 82.5, 91)])                      # buy high 93.5: through 90
    assert not s.open and (s.decisions[-1].price, s.decisions[-1].pips) == (D("90"), D("10"))


# ---- rule 4: never backwards ----------------------------------------------------------------------------------------

def test_the_stop_never_moves_back_when_the_trade_falls_back_or_after_a_restart(ON):
    t = new_trade(ON, direction=BUY)
    m, sender = manager(ON, t)
    feed(m, BUY_UP[:5] + [(117, 117, 112, 113), (113, 114, 112, 113.5)])   # back to +10.5 then +12: stays at +10
    assert moved(sender) == [D("106.5"), D("111.5")] and t.stop_level == D("111.5")
    # after a restart: the stop IG holds (111.5) and the saved best (16) come back; nothing is sent again
    m.save_state()
    again = new_trade(ON, direction=BUY)
    again.stop_level, again.bars = D("111.5"), 1
    m2, sender2 = manager(ON)
    assert m2.restore(again, m.load_state())
    m2.add(again)
    feed(m2, [(113.5, 114, 112.5, 113)], t0=WED + timedelta(minutes=35))
    assert sender2.moves == [] and again.stop_level == D("111.5")
    assert [x["level"] for x in again.stop_moves] == ["106.5", "111.5"]   # the moves kept on the trade


# ---- rule 5: the tighter of the ladder and the strategy's own trail ---------------------------------------------------

def test_with_the_bounces_trail_the_tighter_stop_wins_at_each_step(ON):
    # The Bollinger bounce trails 0.1 below the last 3 finished candles' lowest sell price once 12 up.
    t = new_trade(ON, strategy=BOLLINGER_BOUNCE, direction=BUY)
    m, sender = manager(ON, t)
    feed(m, [(100, 101, 99.8, 100.5),       # entry
             (100.5, 108, 100.5, 107.5),    # +6.5
             (107.5, 112, 107, 111.5),      # +10.5: the ladder's +5 = 106.5
             (111.5, 115, 110, 114.5),      # +13.5: trail 100.4 (lows 100.5, 107, 110) looser than 106.5: not sent
             (114.5, 116, 113, 115.5),      # +14.5: trail 106.9 (lows 107, 110, 113) tighter than 106.5: sent
             (115.5, 117.5, 114.5, 117),    # +16: the ladder's +10 = 111.5 tighter than trail 109.9: sent
             (117, 119, 116.5, 118.5)])     # +17.5: trail 112.9 (lows 113, 114.5, 116.5) tighter than 111.5: sent
    assert [(x["level"], x["by"]) for x in t.stop_moves] == [("106.5", BY_LADDER), ("106.9", BY_TRAIL),
                                                             ("111.5", BY_LADDER), ("112.9", BY_TRAIL)]
    assert moved(sender) == [D("106.5"), D("106.9"), D("111.5"), D("112.9")]


def test_a_trail_already_tighter_than_the_ladders_step_is_kept(ON):
    t = new_trade(ON, strategy=BOLLINGER_BOUNCE, direction=BUY)
    m, sender = manager(ON, t)
    t.stop_level = D("112")                 # say the trail already holds the stop at +10.5
    feed(m, BUY_UP)                         # the ladder's +5 and +10 are both looser: nothing sent by the ladder
    assert all(by != BY_LADDER for by in [x["by"] for x in t.stop_moves])
    assert t.stop_level >= D("112")


def test_with_the_slow_grinds_lock_both_apply_and_the_tighter_closes_it(ON):
    # The slow grind's own stop move is its lock: closed by the bot back at +10 after +15 (in an earlier bar). The
    # ladder's stop at IG is +10 from +15 too; whichever is tighter at each moment counts: here both are +10.
    t = new_trade(ON, strategy=SLOW_GRIND, direction=BUY, state="emerging trend up", stop="15")
    m, sender = manager(ON, t)
    feed(m, BUY_UP[:5] + [(117, 117, 110, 110.5)])                      # back to sell low 110: below +10 (111.5)
    assert moved(sender) == [D("106.5"), D("111.5")]
    assert not t.open and t.decisions[-1].pips == D("10")


# ---- rules 1 and 8: only emerging trend; every strategy; take profit unchanged -----------------------------------------

@pytest.mark.parametrize("state", ["trend up, slow grind", "trend up, strong push", "ranging none", "possible reversal up",
                                   "consolidation up", None, ""])
def test_trades_opened_in_any_other_state_are_untouched(ON, state):
    t = new_trade(ON, direction=BUY, state=state)
    m, sender = manager(ON, t)
    feed(m, BUY_UP)
    assert sender.moves == [] and t.stop_level is None and t.stop_moves == [] and not ladder_applies(ON, t)


@pytest.mark.parametrize("strategy", [LEVEL_REVERSAL, EMA_PULLBACK, BREAKOUT, SLOW_GRIND, BOLLINGER_BOUNCE])
@pytest.mark.parametrize("state,direction,rows,first", [(UP, BUY, BUY_UP, D("106.5")), (DOWN, SELL, SELL_DOWN, D("95"))])
def test_every_strategy_opened_in_emerging_trend_up_or_down(ON, strategy, state, direction, rows, first):
    t = new_trade(ON, strategy=strategy, direction=direction, state=state, stop="15")
    m, sender = manager(ON, t)
    feed(m, rows)
    assert ladder_applies(ON, t) and moved(sender)[0] == first


def test_the_take_profit_is_unchanged(ON, OFF):
    on, off = new_trade(ON, direction=BUY), new_trade(OFF, direction=BUY)
    assert on.take_profit_pips == off.take_profit_pips == D("20")        # the level reversal's
    m, _ = manager(ON, on)
    feed(m, BUY_UP + [(117.5, 122, 117, 121.5)])                        # +20.5: its take profit
    assert not on.open and on.decisions[-1].kind == TAKE_PROFIT_AT_IG and on.decisions[-1].pips == D("20")


# ---- rule 9: settings and the switch -----------------------------------------------------------------------------------

def test_the_numbers_are_settings(pretend_switches, tmp_path):
    S = settings(pretend_switches, tmp_path, "on", emerging_ladder={"first_from_pips": D("8"), "first_stop_pips": D("2"),
                                                                    "second_from_pips": D("12"), "second_stop_pips": D("6")})
    t = new_trade(S, direction=BUY)
    m, sender = manager(S, t)
    feed(m, BUY_UP)
    assert moved(sender) == [D("103.5"), D("107.5")]                   # +2 at +8 (in the +10.5 candle), +6 at +12


def test_the_real_settings_hold_johnnys_numbers(ON):
    el = ON.emerging_ladder
    assert (el.first_from_pips, el.first_stop_pips, el.second_from_pips, el.second_stop_pips) == (10, 5, 15, 10)


def test_the_switch_is_on_if_left_out_and_off_stops_it(pretend_switches, tmp_path, OFF):
    left_out = settings(pretend_switches, tmp_path, None)
    assert left_out.switches.emerging_ladder is True
    t = new_trade(OFF, direction=BUY)
    m, sender = manager(OFF, t)
    feed(m, BUY_UP)
    assert sender.moves == [] and t.stop_level is None


@pytest.mark.parametrize("bad", ["first_stop_pips = 10", "second_from_pips = 9", "second_stop_pips = 5",
                                 "second_stop_pips = 15"])
def test_nonsense_numbers_are_refused_at_start(tmp_path, bad):
    from pathlib import Path
    text = Path("config/settings.toml").read_text()
    key = bad.split(" = ")[0]
    lines = [bad if line.startswith(key + " = ") and "emerging" in section else line
             for section, line in _with_sections(text)]
    f = tmp_path / "settings.toml"
    f.write_text("\n".join(lines) + "\n")
    with pytest.raises(SettingsError, match="emerging_ladder"):
        load_settings(f)


def _with_sections(text):
    section = ""
    for line in text.splitlines():
        if line.startswith("["):
            section = line
        yield section, line


# ---- rule 10: each stop move recorded on the trade ---------------------------------------------------------------------

def test_each_stop_move_is_recorded_on_the_trade_and_in_the_decisions(ON):
    import json
    t = new_trade(ON, direction=BUY)
    m, _ = manager(ON, t)
    feed(m, BUY_UP)
    assert [x["by"] for x in t.stop_moves] == [BY_LADDER, BY_LADDER]
    assert all(x["time_utc"] and x["why"] for x in t.stop_moves)
    assert "emerging trend up" in t.stop_moves[0]["why"] and "+10 reached: stop to +5" in t.stop_moves[0]["why"]
    rows = [json.loads(x) for x in m.journal.read_text().splitlines()]
    moves = [r for r in rows if r["decision"] == STOP_MOVED]
    assert [(D(r["price"]), D(r["pips"])) for r in moves] == [(D("106.5"), 5), (D("111.5"), 10)]
    assert all("emerging-trend ladder" in r["why"] for r in moves)
    saved = json.loads(m.state_file.read_text())["REF1"]
    assert [x["level"] for x in saved["stop_moves"]] == ["106.5", "111.5"]       # kept over a restart


# ---- rule 7: live, through the real order sender: IG's minimum, IG's confirmation, IG refusing ------------------------

@pytest.fixture
def LIVE(pretend_switches, tmp_path):
    from tests.technical.test_orders import Over as OrdersOver
    s = settings(pretend_switches, tmp_path, "on")
    return OrdersOver(s, switches=vars(s.switches) | {k: True for k in ("bollinger_bounce", "level_reversal")},
                      orders={"folder": tmp_path / "orders"}, safety={"folder": tmp_path / "safety"},
                      trade_manager={"folder": tmp_path / "tm"})


def live_trade(S, min_stop=2.0):
    """A level reversal buy at the pretend IG, filled at 13401.5 with its stop 12 below and take profit 20 above, run
    by a trade manager that waits for IG's confirmations (as live)."""
    from tests.technical.test_orders import idea, make
    sender, ig, alerts, sleeps, clock = make(S, t=WED, quote=(D("13400.0"), D("13401.5")))
    r = sender.place(idea(LEVEL_REVERSAL, BUY, t=WED, context={"stop_price": D("13389.5")}), calendar=[])
    pos = next(p for p in ig.positions if p["position"]["dealId"] == r.deal_id)
    pos["position"].update(level=13401.5, stopLevel=13389.5, limitLevel=13421.5)
    ig.min_stop = min_stop
    m = TradeManager(S, sender, ig_confirms=True, now=lambda: clock["t"])
    t = plan(S, r.reference, LEVEL_REVERSAL, BUY, clock["t"], D("13400"), D("13401.5"), D("12"), [], None,
             market_state=UP)
    t.bars = 1
    m.add(t)
    return sender, ig, alerts, clock, m, pos, t


def tick(m, pos, clock, at, sell):
    """A live price: IG's sell (bid) and buy (offer) prices, 1.5 apart."""
    clock["t"] = at
    sell = D(str(sell))
    pos["market"].update(bid=float(sell), offer=float(sell + SPREAD))
    m.on_bar(Bar(at, *[sell + SPREAD] * 4, *[sell] * 4))


def test_live_the_move_goes_to_ig_and_counts_once_ig_confirms_it(LIVE):
    from tests.technical.test_orders import records
    sender, ig, alerts, clock, m, pos, t = live_trade(LIVE)
    tick(m, pos, clock, WED + timedelta(minutes=10), 13411.4)                # +9.9
    assert t.stop_level is None
    tick(m, pos, clock, WED + timedelta(minutes=11), 13411.5)                # +10
    assert t.stop_level == D("13406.5") and pos["position"]["stopLevel"] == 13406.5
    assert pos["position"]["limitLevel"] == 13421.5                         # the take profit kept at IG
    tick(m, pos, clock, WED + timedelta(minutes=20), 13416.5)                # +15
    assert t.stop_level == D("13411.5") and pos["position"]["stopLevel"] == 13411.5
    sent = [x["stop_level"] for x in records(sender) if x["event"] == "stop move sending"]
    assert sent == ["13406.5", "13411.5"] and alerts.sent == []
    assert [x["by"] for x in t.stop_moves] == [BY_LADDER, BY_LADDER]


def test_live_inside_igs_minimum_the_nearest_level_ig_allows_is_sent(LIVE):
    from tests.technical.test_orders import records
    sender, ig, alerts, clock, m, pos, t = live_trade(LIVE, min_stop=8.0)
    tick(m, pos, clock, WED + timedelta(minutes=10), 13411.5)                # +10: +5 is 5 from IG's price, inside 8
    sending = [x for x in records(sender) if x["event"] == "stop move sending"]
    assert [(x["rule_level"], x["stop_level"]) for x in sending] == [("13406.5", "13403.5")]
    assert t.stop_level == D("13403.5")
    # not asked again on every price: worked out again after the next finished candle, as the trail
    tick(m, pos, clock, WED + timedelta(minutes=10, seconds=40), 13412)
    assert len([x for x in records(sender) if x["event"] == "stop move sending"]) == 1


def test_live_ig_refusing_3_times_gives_up_with_one_alert_then_tries_again_after_the_next_candle(LIVE):
    from tests.technical.test_orders import records
    sender, ig, alerts, clock, m, pos, t = live_trade(LIVE)
    ig.move_answer = "reject"
    t0 = WED + timedelta(minutes=10)
    for k in range(5):                                                       # live prices, 31 seconds apart
        tick(m, pos, clock, t0 + timedelta(seconds=31 * k), 13412)           # +10.5
    sent = [x["stop_level"] for x in records(sender) if x["event"] == "stop move sending"]
    assert sent == ["13406.5"] * 3                                           # 3 attempts, then no more
    (key, text), = alerts.sent
    assert key == f"stop-move-gave-up-{t.reference}" and "emerging ladder" in text and "13406.5" in text
    assert t.stop_level is None and t.trail_want is None
    ig.move_answer = "accept"
    clock["t"] = WED + timedelta(minutes=15, seconds=2)                      # the next finished candle
    m.on_bar(bar(WED + timedelta(minutes=10), 13410, 13412, 13409, 13411.5), finished=True)
    assert t.stop_level == D("13406.5") and pos["position"]["stopLevel"] == 13406.5


# ---- rule 1 in the engine: the state recorded on the trade at open, also after a restart ------------------------------

@pytest.fixture(autouse=True)
def fresh_transports():
    from tests.technical.fake_stream import FakeTransport
    FakeTransport.opened.clear()


@pytest.fixture
def ENGINE(pretend_switches, tmp_path):
    from tests.technical.test_orders import Over as OrdersOver
    s = load_settings(switches_from=pretend_switches).for_pair("GBPUSD")
    return OrdersOver(s, switches={k: True for k in ("ema_pullback", "level_reversal", "emerging_ladder")} | {"trading": False},
                      orders={"folder": tmp_path / "orders"}, trade_manager={"folder": tmp_path / "tm"},
                      safety={"folder": tmp_path / "safety"}, records={"folder": tmp_path / "records"},
                      trading={"pause_file": tmp_path / "control" / "pause_new_trades"},
                      dashboard={"status_folder": tmp_path / "status"})


def engine_idea(strategy, t, state, direction=SELL, price="100"):
    from strategies.common import Idea
    return Idea("GBPUSD", strategy, direction, t, D(price), state, "down", None, "sell side", ["made up"], True, "", {})


@pytest.mark.parametrize("state,ladder", [("emerging trend", True), ("trend", False)])
def test_the_engine_gives_the_trade_its_state_at_open_and_keeps_it_after_a_restart(ENGINE, monkeypatch, state, ladder):
    import json
    from tests.technical.test_trading import C, feed, make, tick
    e, ig, tracker, clock, quote = make(ENGINE, monkeypatch, C, {C[1].start: [engine_idea(EMA_PULLBACK, C[1].start, state)]})
    e.start(C[0].start)
    feed(e, clock, C[:2])
    (t,) = e.manager.trades.values()
    assert t.market_state == f"{state} down" and ladder_applies(ENGINE, t) is ladder
    clock["t"] = C[2].start + timedelta(seconds=5)
    e.on_price(tick(clock["t"], 88.5))                       # a sell filled at 100: buy price 90, +10
    assert (t.stop_level == D("95")) is ladder
    again, *_ = make(ENGINE, monkeypatch, C[2:], {})         # a restart
    again.start(clock["t"])
    (t2,) = again.manager.trades.values()
    assert t2.market_state == f"{state} down" and ladder_applies(ENGINE, t2) is ladder
    assert [x["by"] for x in t2.stop_moves] == ([BY_LADDER] if ladder else [])
    clock2 = {"t": C[2].start + timedelta(seconds=20)}
    again.now = lambda: clock2["t"]
    again.on_price(tick(clock2["t"], 93.5))                  # back to buy 95: its +5 stop, if it moved
    if ladder:
        assert not t2.open and t2.decisions[-1].pips == D("5")
        closed = [json.loads(x) for x in (ENGINE.records.folder / "GBPUSD" / "paper" / "trades.jsonl").read_text().splitlines()]
        row = [r for r in closed if r.get("how_closed")][-1]
        assert [(D(m["level"]), m["by"]) for m in row["stop_moves"]] == [(D("95"), BY_LADDER)]   # on the trade's record
    else:
        assert t2.open
