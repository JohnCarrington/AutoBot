"""Technical tests for the wiring (trading/engine.py and the price service): the analyser and strategies are
pretend ones giving scripted candles and ideas; the order sender and trade manager are the real ones, with a
pretend IG. Nothing here contacts IG."""

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from strategies.common import BOLLINGER_BOUNCE, BREAKOUT, BUY, EMA_PULLBACK, RANGE_TRADE, SELL, SLOW_GRIND, Idea
from tests.technical.test_orders import Over, PretendIG  # noqa: F401
from trading import engine as eng

U = lambda *a: datetime(*a, tzinfo=timezone.utc)  # noqa: E731
WED = U(2026, 11, 4, 10, 0)
SPREAD = D("1.5")


@pytest.fixture(autouse=True)
def fresh_transports():
    from tests.technical.fake_stream import FakeTransport
    FakeTransport.opened.clear()


@pytest.fixture
def S(pretend_switches, tmp_path):
    from config.settings_loader import load_settings
    s = load_settings(switches_from=pretend_switches).for_pair("GBPUSD")
    return Over(s, switches={k: True for k in ("slow_grind", "ema_pullback", "bollinger_bounce", "range_trade",
                                                 "breakout", "level_reversal")} | {"trading": False},
                orders={"folder": tmp_path / "orders"}, trade_manager={"folder": tmp_path / "tm"},
                safety={"folder": tmp_path / "safety"}, records={"folder": tmp_path / "records"},
                trading={"pause_file": tmp_path / "control" / "pause_new_trades"},
                dashboard={"status_folder": tmp_path / "status"})


def candle(t, o, h, l, c):
    o, h, l, c = (D(str(x)) for x in (o, h, l, c))
    return SimpleNamespace(start=t, end=t + timedelta(minutes=5), buy_open=o + SPREAD, buy_high=h + SPREAD,
                           buy_low=l + SPREAD, buy_close=c + SPREAD, sell_open=o, sell_high=h, sell_low=l, sell_close=c)


class PretendTracker:
    """Gives one scripted candle per advance (the analyser's history), with the analyser's watcher."""
    def __init__(self, script):
        self.script, self.history, self.changes = list(script), [], []
        self.week_open = U(2026, 11, 1, 21, 0)
        self.watcher = SimpleNamespace(events=[], setups=[])

    def replay(self, now):
        pass

    def advance(self, now):
        while self.script and self.script[0].end <= now:
            c = self.script.pop(0)
            self.history.append((SimpleNamespace(candle=c, upper=D("130"), lower=D("70")),))


class PretendRunner:
    """The strategies: scripted ideas per candle start; `live`: (strategy, direction, trigger) per forming candle
    start, an idea once the forming candle's sell price has gone past the trigger (below it for a sell)."""
    def __init__(self, tracker, ideas, live=None):
        self.tracker, self.ideas, self.done, self.week_open = tracker, ideas, 0, tracker.week_open
        self.live = live or {}
        self.peeked = []

    def peek(self, partial, levels=None):
        self.peeked.append(partial)
        out = []
        for strategy, direction, trigger in self.live.get(partial.start, []):
            past = partial.sell_low <= trigger if direction == SELL else partial.sell_high >= trigger
            if past:
                out.append(idea(strategy, partial.start, direction, str(trigger)))
        return out

    def step(self):
        out = []
        for h in self.tracker.history[self.done:]:
            out += [(h[0].candle, i) for i in self.ideas.get(h[0].candle.start, [])]
        self.done = len(self.tracker.history)
        return out


def idea(strategy, t, direction=SELL, price="100", allowed=True):
    return Idea("GBPUSD", strategy, direction, t, D(price), "trend", "down", None, "sell side", ["made up"], allowed,
                "" if allowed else "made up block", {})


def make(S, monkeypatch, candles, ideas, trading_on=False, ig=None, clock=None, live=None):
    tracker = PretendTracker(candles)
    monkeypatch.setattr(eng, "StateTracker", lambda s, memo: tracker)
    monkeypatch.setattr(eng, "MemoStore", lambda store: None)
    monkeypatch.setattr(eng, "build", lambda s, memo, t: None)
    monkeypatch.setattr(eng, "StrategyRunner", lambda s, memo, tr, hourly_end=None: PretendRunner(tr, ideas, live))
    monkeypatch.setattr(eng, "trend_day_at", lambda s, store, t: SimpleNamespace(direction=None))
    ig = ig or PretendIG()
    clock = clock or {"t": WED}
    quote = {"q": (D("100.0"), D("101.5"))}
    alerts = SimpleNamespace(sent=[], infos=[], opened=[], closed=[], problem=lambda k, t: alerts.sent.append((k, t)),
                             info=lambda t, key=None, html=False: alerts.infos.append(t),
                             trade_opened=lambda t: alerts.opened.append(t), trade_closed=lambda c: alerts.closed.append(c))
    e_alerts = alerts
    e = eng.Trading(S, None, ig, alerts, trading_on=trading_on, now=lambda: clock["t"], quote=lambda: quote["q"],
                    calendar=[], sleep=lambda s: None)
    e._clock = clock
    ig.journal = e.sender.journal
    return e, ig, tracker, clock, quote


def feed(e, clock, candles):
    for c in candles:
        clock["t"] = c.end
        e.on_candle(c.end)


def journal(e):
    return [json.loads(x) for x in e.sender.journal.read_text().splitlines()] if e.sender.journal.exists() else []


C = [candle(WED + timedelta(minutes=5 * k), 100, 100.5, 99.5, 100) for k in range(6)]


# ---- the master switch -------------------------------------------------------------------------------

def test_trading_off_runs_everything_and_records_but_sends_nothing_to_ig(S, monkeypatch):
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, {C[1].start: [idea(BREAKOUT, C[1].start)]})
    e.start(WED)
    feed(e, clock, C[:3])
    assert ig.orders_sent() == [] and not any(c[0] == "POST" for c in ig.calls if len(c) > 1)
    assert e.sender.paper and e.sender.journal.name == "paper_orders.jsonl"
    assert [r["event"] for r in journal(e) if r["event"] in ("sending", "opened")] == ["sending", "opened"]
    assert all(r.get("paper") for r in journal(e))
    (t,) = [t for t in e.manager.trades.values()]
    assert t.strategy == BREAKOUT and t.open and t.fill == D("100.0")                  # a sell at the bid


def test_trading_on_sends_the_order_through_the_order_sender(S, monkeypatch):
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, {C[1].start: [idea(BREAKOUT, C[1].start)]}, trading_on=True)
    e.start(WED)
    feed(e, clock, C[:3])
    (o,) = ig.orders_sent()
    assert o[3]["direction"] == "SELL" and o[3]["forceOpen"] is True and o[3]["stopDistance"] == 12.0
    assert e.sender.journal.name == "orders.jsonl" and [t.strategy for t in e.manager.trades.values()] == [BREAKOUT]


def test_a_blocked_idea_is_never_sent(S, monkeypatch):
    e, ig, *_ = make(S, monkeypatch, C, {C[1].start: [idea(BREAKOUT, C[1].start, allowed=False)]}, trading_on=True)
    e.start(WED)
    feed(e, e._clock, C[:3])
    assert ig.orders_sent() == [] and e.manager.trades == {}


def test_the_safety_rules_decide_before_anything_is_sent(S, monkeypatch):
    two = {C[1].start: [idea(BOLLINGER_BOUNCE, C[1].start)], C[2].start: [idea(BOLLINGER_BOUNCE, C[2].start)]}
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, two, trading_on=True)
    e.start(WED)
    feed(e, clock, C[:4])
    assert len(ig.orders_sent()) == 1                                  # the second sell bounce: its own limit
    assert any(r["event"] == "safety refused" and "already has 1 sell" in r["reasons"][0] for r in journal(e))


def test_nothing_happens_before_the_start_up(S, monkeypatch):
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, {C[1].start: [idea(BREAKOUT, C[1].start)]})
    feed(e, clock, C[:3])
    assert e.manager.trades == {} and ig.calls == []


# ---- the trade manager on each candle and each price -------------------------------------------------------

def test_open_trades_are_run_on_each_candle_before_new_ideas(S, monkeypatch):
    stop = candle(WED + timedelta(minutes=15), 100, 113, 99.5, 112)          # stops the first sell (12 pips)
    cs = C[:3] + [stop] + C[4:]
    ideas = {C[1].start: [idea(BREAKOUT, C[1].start)], stop.start: [idea(BREAKOUT, stop.start)]}
    e, ig, tracker, clock, quote = make(S, monkeypatch, cs, ideas)
    e.start(WED)
    feed(e, clock, cs[:5])
    states = [t.state for t in e.manager.trades.values()]
    assert states == ["stopped by IG", "hold"]                            # closed first, so the next could open
    assert [r["event"] for r in journal(e)].count("opened") == 2 and "closed at IG" in [r["event"] for r in journal(e)]


def test_the_latest_price_runs_the_open_trades(S, monkeypatch):
    t0 = U(2026, 11, 4, 20, 15)
    cs = [candle(t0 + timedelta(minutes=5 * k), 100, 100.5, 99.5, 100) for k in range(3)]
    e, ig, tracker, clock, quote = make(S, monkeypatch, cs, {cs[0].start: [idea(SLOW_GRIND, cs[0].start)]}, clock={"t": t0})
    e.start(t0)
    feed(e, clock, cs[:1])
    (t,) = e.manager.trades.values()
    assert t.open
    tick = SimpleNamespace(time=U(2026, 11, 4, 20, 30, 1), buy=D("101.0"), sell=D("99.5"))
    clock["t"] = tick.time
    e.on_price(tick)                                                       # 20:30: the slow grind's daily close
    assert not t.open and t.state == "forced close"
    assert [r["event"] for r in journal(e)][-2:] == ["close sending", "closed"]


def test_the_same_price_is_not_taken_twice(S, monkeypatch):
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, {C[1].start: [idea(EMA_PULLBACK, C[1].start)]})
    e.start(WED)
    feed(e, clock, C[:2])
    (t,) = e.manager.trades.values()
    tick = SimpleNamespace(time=WED + timedelta(minutes=11), buy=D("101.0"), sell=D("99.5"))
    e.on_price(tick)
    e.on_price(tick)
    assert t.bars == 2                                                     # the entry candle and one price


def test_watching_a_level_comes_from_the_analysers_rejection_part(S, monkeypatch):
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, {C[1].start: [idea(BOLLINGER_BOUNCE, C[1].start)]})
    e.start(WED)
    feed(e, clock, C[:2])
    (t,) = e.manager.trades.values()
    tracker.watcher.setups.append(SimpleNamespace(version="bounce", status="running", counts=True, direction=BUY,
                                                  pierced=[{"what": "S2", "price": D("97")}]))
    feed(e, clock, C[2:3])
    assert t.decision == "watching a level"
    tracker.watcher.setups[0].status = "cancelled"
    feed(e, clock, C[3:4])
    assert t.decision == "hold"


def test_a_rejection_at_a_level_from_the_analyser_closes_a_bounce(S, monkeypatch):
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, {C[1].start: [idea(BOLLINGER_BOUNCE, C[1].start)]})
    e.start(WED)
    feed(e, clock, C[:2])
    tracker.watcher.setups.append(SimpleNamespace(version="bounce", status="triggered", counts=True, direction=BUY,
                                                  pierced=[{"what": "S2", "price": D("99")}]))
    tracker.watcher.events.append(SimpleNamespace(version="bounce", kind="trigger", time=C[2].start, setup=1,
                                                  direction=BUY, price=D("99.6")))
    feed(e, clock, C[2:3])
    (t,) = e.manager.trades.values()
    assert t.state == "close" and "S2 99" in t.decisions[-1].why


# ---- start-up --------------------------------------------------------------------------------------------

def test_after_a_restart_the_open_trades_are_taken_over(S, monkeypatch):
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, {C[1].start: [idea(EMA_PULLBACK, C[1].start)]})
    e.start(WED)
    feed(e, clock, C[:2])
    again, *_ = make(S, monkeypatch, C[2:], {})
    again.start(WED + timedelta(minutes=10))
    (t,) = again.manager.trades.values()
    assert t.strategy == EMA_PULLBACK and t.open and t.take_profit_pips == 30


# ---- the price service ------------------------------------------------------------------------------------

def test_the_test_order_does_not_run_while_trading_is_on(S, tmp_path):
    from orders.test_order import RESULT, TestOrder
    folder = S.orders.folder
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "test_request.json").write_text(json.dumps({"approved_by": "owner", "not_before_utc": "2026-11-04T09:00:00Z",
                                                          "direction": "buy", "hold_seconds": 60}))
    ig = PretendIG()
    t = TestOrder(S, ig, SimpleNamespace(info=lambda *a, **k: None, problem=lambda *a: None),
                  lambda: (D("100"), D("101.5")), now=lambda: WED, threaded=False, trading_on=True)
    t.tick()
    assert ig.calls == [] and "TRADING is on" in json.loads((folder / RESULT).read_text())["refused"]


def test_the_price_service_calls_trading_after_each_candle_and_every_second(tmp_path, monkeypatch):
    import threading
    from ig.client import IGClient
    from prices import service
    from prices.store import CandleStore
    from tests.technical import test_service as ts
    from tests.technical.fake_ig import CREDS, FakeIG, accounts_ok, login_ok, logout_ok, switch_ok
    calls = {"candle": [], "price": []}

    class PretendEngine:
        def on_candle(self, now):
            calls["candle"].append(now)

        def on_price(self, tick):
            calls["price"].append(tick)
    started = []
    monkeypatch.setattr(service, "_start_trading", lambda ps, feed, client, alerts, now, on: started.append(on) or PretendEngine())
    s = ts._settings(tmp_path)
    s.trade_manager = SimpleNamespace(folder=tmp_path / "tm")
    s.switches = SimpleNamespace(trading=False)
    store = CandleStore(s.candles.folder, 30)
    clock = ts.Clock(ts.T(2026, 11, 4, 12, 0, 20))
    ig = FakeIG(login_ok(), accounts_ok(), switch_ok(), logout_ok())
    client = IGClient(ts.SETTINGS.ig, CREDS, http=ig, sleep=lambda x: None)
    stop = threading.Event()
    th = threading.Thread(target=lambda: service.serve(s, client=client, transport_factory=ts.new_transport, stop=stop,
                                                       now=clock, logs=False, signals=False, alerts=SimpleNamespace(
                                                           problem=lambda *a: None, info=lambda *a, **k: None)))
    th.start()
    assert ts._wait_for(lambda: ts.FakeTransport.opened)
    t = ts.FakeTransport.opened[-1]
    t.connect()
    t.tick(ts.T(2026, 11, 4, 12, 0, 30))
    t.candle(ts.T(2026, 11, 4, 12, 0), finished=True)
    assert ts._wait_for(lambda: calls["candle"] and calls["price"], 5)
    stop.set()
    th.join(10)
    assert started == [False] and not th.is_alive()


def test_a_trading_problem_never_stops_the_price_service(tmp_path, monkeypatch):
    import threading
    from ig.client import IGClient
    from prices import service
    from prices.store import CandleStore
    from tests.technical import test_service as ts
    from tests.technical.fake_ig import CREDS, FakeIG, accounts_ok, login_ok, logout_ok, switch_ok
    sent = []

    class Broken:
        def on_candle(self, now):
            raise RuntimeError("made up")

        def on_price(self, tick):
            raise RuntimeError("made up")
    monkeypatch.setattr(service, "_start_trading", lambda *a: Broken())
    s = ts._settings(tmp_path)
    s.trade_manager = SimpleNamespace(folder=tmp_path / "tm")
    s.switches = SimpleNamespace(trading=False)
    store = CandleStore(s.candles.folder, 30)
    clock = ts.Clock(ts.T(2026, 11, 4, 12, 0, 20))
    client = IGClient(ts.SETTINGS.ig, CREDS, http=FakeIG(login_ok(), accounts_ok(), switch_ok(), logout_ok()),
                      sleep=lambda x: None)
    stop = threading.Event()
    result = {}
    th = threading.Thread(target=lambda: result.setdefault("code", service.serve(
        s, client=client, transport_factory=ts.new_transport, stop=stop, now=clock, logs=False, signals=False,
        alerts=SimpleNamespace(problem=lambda k, t: sent.append(k), info=lambda *a, **k: None))))
    th.start()
    assert ts._wait_for(lambda: ts.FakeTransport.opened)
    t = ts.FakeTransport.opened[-1]
    t.connect()
    t.tick(ts.T(2026, 11, 4, 12, 0, 30))
    t.candle(ts.T(2026, 11, 4, 12, 0), finished=True)
    assert ts._wait_for(lambda: store.newest("5m") is not None and "trading-stopped" in sent, 5)
    stop.set()
    th.join(10)
    assert result["code"] == 0 and "trading-stopped" in sent


# ---- live entries (design 3: as soon as the live price reaches the trigger) ---------------------------------

def tick(t, sell, spread="1.5"):
    return SimpleNamespace(time=t, sell=D(str(sell)), buy=D(str(sell)) + D(spread))


def test_a_trigger_reached_on_the_live_price_is_sent_at_once_not_when_the_candle_finishes(S, monkeypatch):
    forming = C[2].start                                       # 10:10
    live = {forming: [(BREAKOUT, SELL, D("99.0"))]}
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, {forming: [idea(BREAKOUT, forming, price="99.0")]},
                                        trading_on=True, live=live)
    e.start(WED)
    feed(e, clock, C[:2])                                      # up to 10:10
    for k, p in enumerate((99.6, 99.3)):                       # not past 99.0 yet
        clock["t"] = forming + timedelta(seconds=10 + k)
        e.on_price(tick(clock["t"], p))
    assert ig.orders_sent() == []
    clock["t"] = forming + timedelta(seconds=40)
    e.on_price(tick(clock["t"], 98.9))                         # past it: sent now, at 10:10:40
    (o,) = ig.orders_sent()
    assert o[3]["direction"] == "SELL"
    sending = [r for r in journal(e) if r["event"] == "sending"][0]
    assert sending["time_utc"] == "2026-11-04T10:10:40Z"
    feed(e, clock, C[2:3])                                     # the candle finishes: its idea is not sent again
    assert len(ig.orders_sent()) == 1


def test_the_forming_candle_is_built_from_the_live_prices(S, monkeypatch):
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, {})
    e.start(WED)
    feed(e, clock, C[:2])
    for k, p in enumerate((100.0, 101.0, 99.0, 100.5)):
        e.on_price(tick(C[2].start + timedelta(seconds=k), p))
    p = e.runner.peeked[-1]
    assert (p.start, p.sell_open, p.sell_high, p.sell_low, p.sell_close) == (C[2].start, D("100.0"), D("101.0"), D("99.0"), D("100.5"))
    assert p.buy_high == D("102.5")
    e.on_price(tick(C[3].start + timedelta(seconds=1), 98.0))  # a new 5 minutes: a new forming candle
    assert e.runner.peeked[-1].start == C[3].start and e.runner.peeked[-1].sell_high == D("98.0")


def test_a_trigger_the_live_prices_did_not_show_is_still_sent_when_the_candle_finishes(S, monkeypatch):
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, {C[2].start: [idea(BREAKOUT, C[2].start)]}, trading_on=True)
    e.start(WED)
    feed(e, clock, C[:3])
    assert len(ig.orders_sent()) == 1


def test_a_trade_opened_during_a_candle_is_not_run_on_that_candles_earlier_prices(S, monkeypatch):
    forming = C[2].start
    spike = candle(forming, 100, 107, 98.5, 99)                 # the high (107) came before the entry
    cs = C[:2] + [spike] + C[3:]
    e, ig, tracker, clock, quote = make(S, monkeypatch, cs, {}, live={forming: [(BREAKOUT, SELL, D("99.0"))]})
    e.start(WED)
    feed(e, clock, cs[:2])
    e.on_price(tick(forming + timedelta(seconds=30), 106.0))
    e.on_price(tick(forming + timedelta(seconds=200), 98.9))   # the entry, after the spike
    (t,) = e.manager.trades.values()
    feed(e, clock, cs[2:3])
    assert t.open and t.state == "hold"                         # the spike did not stop it


def test_a_blocked_live_idea_is_not_sent(S, monkeypatch):
    forming = C[2].start
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, {}, trading_on=True, live={forming: [(BREAKOUT, SELL, D("99"))]})
    e.start(WED)
    feed(e, clock, C[:2])
    e.runner.live = {}
    real_peek = e.runner.peek
    e.runner.peek = lambda p, levels=None: [idea(BREAKOUT, forming, allowed=False)]
    e.on_price(tick(forming + timedelta(seconds=5), 98))
    assert ig.orders_sent() == []
    e.runner.peek = real_peek


# ---- the trade manager's saved state after a restart --------------------------------------------------------

def test_the_best_pips_so_far_are_restored_after_a_restart_so_the_lock_carries_on(S, monkeypatch):
    t0 = C[0].start
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, {C[1].start: [idea(SLOW_GRIND, C[1].start, price="100")]})
    e.start(WED)
    feed(e, clock, C[:2])
    (t,) = e.manager.trades.values()
    clock["t"] = C[2].start + timedelta(seconds=5)
    e.on_price(tick(clock["t"], 83.0))                          # 15.5 up (the buy price 84.5 against the bid fill 100)
    assert t.best == D("15.5")
    saved = json.loads(e.manager.state_file.read_text())[t.reference]
    assert saved["best"] == "15.5"
    again, ig2, *_ = make(S, monkeypatch, C[2:], {})            # a restart
    again.start(clock["t"])
    (t2,) = again.manager.trades.values()
    assert t2.best == D("15.5")
    clock2 = {"t": C[2].start + timedelta(seconds=20)}
    again.now = lambda: clock2["t"]
    again.on_price(tick(clock2["t"], 88.6))                     # back to 10 up (buy 90.1 -> 9.9 up): the lock
    assert not t2.open and t2.state == "close" and "profit lock" in t2.decisions[-1].why


def test_a_bounces_stop_moved_to_break_even_at_ig_is_known_after_a_restart(S, monkeypatch):
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, {C[1].start: [idea(BOLLINGER_BOUNCE, C[1].start)]},
                                        trading_on=True)
    e.start(WED)
    feed(e, clock, C[:2])
    (t,) = e.manager.trades.values()                            # IG filled the sell at 13400.5
    for k in (5, 6):                                            # 7 up on one price (buy 13393.5), the move on the next
        clock["t"] = C[2].start + timedelta(seconds=k)
        e.on_price(tick(clock["t"], 13392.0))
    (put,) = [c for c in ig.calls if c[0] == "PUT"]
    assert put[3]["stopLevel"] == float(t.fill) and t.stop_moved
    again, *_ = make(S, monkeypatch, C[2:], {}, trading_on=True, ig=ig)    # a restart
    again.start(clock["t"])
    (t2,) = again.manager.trades.values()
    assert t2.stop_moved
    clock2 = {"t": C[2].start + timedelta(seconds=20)}
    again.now = lambda: clock2["t"]
    again.on_price(tick(clock2["t"], 13392.0))
    assert len([c for c in ig.calls if c[0] == "PUT"]) == 1      # not moved again


def test_without_saved_state_a_trade_starts_from_nothing(S, monkeypatch):
    from trade_manager.manager import TradeManager, plan
    m = TradeManager(S, None)
    tr = plan(S, "X", SLOW_GRIND, SELL, WED, D(100), D(100), D(15), [])
    assert m.restore(tr) is False and tr.best is None


def test_the_half_close_is_restored_too(S, monkeypatch):
    from trade_manager.manager import TradeManager, plan
    from strategies.common import RANGE_TRADE
    m = TradeManager(S, None)
    tr = plan(S, "R1", RANGE_TRADE, SELL, WED, D(100), D(100), D(6), [])
    tr.best, tr.half_done, tr.half_pips, tr.state, tr.bars = D("9"), True, D("8.5"), "half close", 3
    m.trades["R1"] = tr
    m.save_state()
    back = plan(S, "R1", RANGE_TRADE, SELL, WED, D(100), D(100), D(6), [])
    assert m.restore(back, m.load_state())
    assert (back.best, back.half_done, back.half_pips, back.state) == (D("9"), True, D("8.5"), "half close")


# ---- one view at a time (design 6; owner, 9 November 2026) -------------------------------------------------

def test_the_engine_gives_the_safety_rules_the_days_direction(S, monkeypatch):
    ideas = {C[1].start: [idea(BOLLINGER_BOUNCE, C[1].start), idea(BREAKOUT, C[1].start)]}
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, ideas, trading_on=True)
    monkeypatch.setattr(eng, "trend_day_at", lambda s, store, t: SimpleNamespace(direction="up"))
    e.start(WED)
    feed(e, clock, C[:3])
    assert [t.strategy for t in e.manager.trades.values()] == [BREAKOUT]       # not a reversal: unchanged
    (r,) = [r for r in journal(e) if r["event"] == "safety refused"]
    assert r["strategy"] == BOLLINGER_BOUNCE and r["reasons"] == [
        "a reversal trade against the day's direction: a trend day, direction buy"]


def test_a_live_reversal_against_a_strong_push_is_not_sent(S, monkeypatch):
    t0 = C[1].start
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, {}, trading_on=True,
                                        live={t0: [(BOLLINGER_BOUNCE, BUY, D("100.4"))]})
    pushed = idea(BOLLINGER_BOUNCE, t0, BUY, "100.4")
    pushed.trend_type = "strong push"
    monkeypatch.setattr(e.runner, "peek", lambda partial, levels=None: [pushed] if partial.start == t0 else [])
    e.start(WED)
    feed(e, clock, C[:1])
    clock["t"] = t0 + timedelta(seconds=30)
    e.on_price(SimpleNamespace(time=clock["t"], sell=D("100.5"), buy=D("102.0")))
    assert ig.orders_sent() == [] and e.manager.trades == {}
    assert any(r["event"] == "safety refused" and r["reasons"] == ["a reversal trade against a strong push (down)"]
               for r in journal(e))


# ---- a close only once IG confirms it, and the bot's trades against IG's positions (10 November 2026) ----

def trades_rows(e):
    f = e.book.trades_file
    return [json.loads(x) for x in f.read_text().splitlines()] if f.exists() else []


def at_2015(S, monkeypatch, ig=None):
    t0 = U(2026, 11, 4, 20, 15)
    cs = [candle(t0 + timedelta(minutes=5 * k), 13400, 13400.5, 13399.5, 13400) for k in range(4)]
    e, ig, tracker, clock, quote = make(S, monkeypatch, cs, {cs[0].start: [idea(SLOW_GRIND, cs[0].start, price="13400")]},
                                        trading_on=True, ig=ig, clock={"t": t0})
    e.start(t0)
    feed(e, clock, cs[:1])
    return e, ig, clock, cs


def test_tonights_refused_20_30_close_keeps_the_trade_open_alerts_and_is_tried_again(S, monkeypatch):
    e, ig, clock, cs = at_2015(S, monkeypatch)
    (t,) = e.manager.trades.values()
    deal = e.sender.trades[t.reference].deal_id
    ig.close_answer = "notional"                                            # IG refuses; the position is still open
    tick = SimpleNamespace(time=U(2026, 11, 4, 20, 30, 2), buy=D("13401.0"), sell=D("13399.5"))
    clock["t"] = tick.time
    e.on_price(tick)
    assert t.open and [r["event"] for r in trades_rows(e)] == ["opened"]   # never recorded closed
    assert e.alerts.closed == []                                            # no "TRADE CLOSED" message
    assert e.alerts.sent[-1][0] == f"close-refused-{deal}"
    assert "error.service.marketdata.position.notional.details.null.error" in e.alerts.sent[-1][1]
    ig.close_answer = "accept"
    tick2 = SimpleNamespace(time=U(2026, 11, 4, 20, 30, 33), buy=D("13401.0"), sell=D("13399.5"))
    clock["t"] = tick2.time
    e.on_price(tick2)                                                       # tried again after 30 seconds
    assert not t.open and [r["event"] for r in trades_rows(e)] == ["opened", "closed"] and len(e.alerts.closed) == 1


def test_a_trade_ig_closed_by_itself_is_found_after_the_next_candle_and_recorded_at_igs_level(S, monkeypatch):
    e, ig, clock, cs = at_2015(S, monkeypatch)
    (t,) = e.manager.trades.values()
    deal = e.sender.trades[t.reference].deal_id
    ig.system_close(deal, 13398.7, "2026-11-04T20:22:10", "WEB")
    feed(e, clock, cs[1:2])                                                 # the next candle: the regular check
    assert not t.open and t.state == "closed at IG"
    closed = [r for r in trades_rows(e) if r["event"] == "closed"]
    assert len(closed) == 1 and closed[0]["close_price"] == "13398.7" and closed[0]["how_closed"] == "closed at IG"
    assert closed[0]["closed_utc"] == "2026-11-04T20:22:10Z" and closed[0]["pips"] == "1.8"   # a sell from 13400.5
    assert any(k == f"gone-at-ig-{deal}" for k, _ in e.alerts.sent) and len(e.alerts.closed) == 1


def test_after_a_restart_a_trade_ig_closed_meanwhile_is_recorded_once(S, monkeypatch):
    e, ig, clock, cs = at_2015(S, monkeypatch)
    (t,) = e.manager.trades.values()
    ig.system_close(e.sender.trades[t.reference].deal_id, 13399.0, "2026-11-04T20:21:00", "WEB")
    again, *_ = make(S, monkeypatch, cs[1:], {}, trading_on=True, ig=ig, clock=clock)
    again.start(U(2026, 11, 4, 20, 22))
    closed = [r for r in trades_rows(again) if r["event"] == "closed"]
    assert len(closed) == 1 and closed[0]["close_price"] == "13399.0" and closed[0]["how_closed"] == "closed at IG"
    third, *_ = make(S, monkeypatch, cs[1:], {}, trading_on=True, ig=ig, clock=clock)
    third.start(U(2026, 11, 4, 20, 23))
    assert len([r for r in trades_rows(third) if r["event"] == "closed"]) == 1      # never twice


def test_after_a_restart_a_trade_taken_over_gets_its_close_recorded(S, monkeypatch):
    e, ig, clock, cs = at_2015(S, monkeypatch)
    (t,) = e.manager.trades.values()
    again, *_ = make(S, monkeypatch, cs[1:], {}, trading_on=True, ig=ig, clock=clock)
    again.start(U(2026, 11, 4, 20, 22))
    tick = SimpleNamespace(time=U(2026, 11, 4, 20, 30, 2), buy=D("13401.0"), sell=D("13399.5"))
    clock["t"] = tick.time
    again.on_price(tick)                                                    # the 20:30 close, confirmed by IG
    closed = [r for r in trades_rows(again) if r["event"] == "closed"]
    assert len(closed) == 1 and closed[0]["reference"] == t.reference and closed[0]["how_closed"] == "forced close"


def test_a_trade_the_owner_closed_by_hand_is_recorded_apart_and_never_counted_for_the_bot(S, monkeypatch):
    e, ig, clock, cs = at_2015(S, monkeypatch)
    (t,) = e.manager.trades.values()
    deal = e.sender.trades[t.reference].deal_id
    ig.system_close(deal, 13398.7, "2026-11-04T20:22:10")                  # SYSTEM, not at the stop or limit
    feed(e, clock, cs[1:2])
    assert not t.open and t.state == "closed by owner"
    (closed,) = [r for r in trades_rows(e) if r["event"] == "closed"]
    assert closed["closed_by"] == "owner" and closed["how_closed"] == "closed by owner"
    assert closed["close_price"] == "13398.7" and closed["closed_utc"] == "2026-11-04T20:22:10Z"
    assert e.alerts.closed == [] and e.alerts.sent == []                    # no trade-closed message, no warning
    assert any("you closed" in m for m in e.alerts.infos)
    today = e.book.today(U(2026, 11, 4, 20, 25))
    assert (today.trades, today.pips) == (0, D(0)) and (today.owner_trades, today.owner_pips) == (1, D("1.8"))


def test_the_bots_own_close_is_recorded_at_igs_confirmed_price_and_time(S, monkeypatch):
    e, ig, clock, cs = at_2015(S, monkeypatch)
    (t,) = e.manager.trades.values()                                        # a sell from 13400.5
    tick = SimpleNamespace(time=U(2026, 11, 4, 20, 30, 2), buy=D("13401.0"), sell=D("13399.5"))
    clock["t"] = tick.time
    e.on_price(tick)                                                        # the 20:30 close: IG confirms 13390.0
    (closed,) = [r for r in trades_rows(e) if r["event"] == "closed"]
    assert closed["close_price"] == "13390.0" and closed["pips"] == "10.5" and closed["gbp"] == "105.00"
    assert closed["closed_utc"] == "2026-11-04T20:30:02Z" and closed["closed_by"] == "bot"


# ---- the pace and target rule (trading/against_trend.py; owner, 11 November 2026) -----------------------------------

def decisions(e):
    f = e.book.decisions_file
    return [json.loads(x) for x in f.read_text().splitlines()] if f.exists() else []


def verdict(valid, reason="", level="00 13300", rate="1.2"):
    from trading.against_trend import Verdict
    return Verdict(valid, reason, ["EMA pullback sell r at 100.0"], D("99.4"), level if valid or reason != "not at a significant level" else None,
                   ["00 100 (0.6 pips)"], D(rate))


def against_trend(monkeypatch, v):
    """The rule's verdict, scripted (the real check with a candle store is in test_against_trend.py); `seen`: what it
    was asked about."""
    import trading.against_trend as at
    seen = []
    def check(s, store, i, t, trades):
        if i.strategy != BOLLINGER_BOUNCE or not at.trend_trades_against(trades, i.direction):
            return None
        seen.append((i.strategy, i.direction, t))
        return v
    monkeypatch.setattr(at, "check", check)
    return seen


def trend_then_bounce(S, monkeypatch, v, trading_on=False, extra=()):
    ideas = {C[1].start: [idea(EMA_PULLBACK, C[1].start)] + list(extra),
             C[2].start: [idea(BOLLINGER_BOUNCE, C[2].start, direction=BUY, price="100.5")]}
    seen = against_trend(monkeypatch, v)
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, ideas, trading_on=trading_on)
    e.start(WED)
    return e, ig, clock, seen


def test_a_bounce_against_open_trend_trades_not_at_a_level_is_refused_and_logged_with_its_reason(S, monkeypatch):
    e, ig, clock, seen = trend_then_bounce(S, monkeypatch, verdict(False, "not at a significant level"))
    feed(e, clock, C[:4])
    assert [(t.strategy, t.open) for t in e.manager.trades.values()] == [(EMA_PULLBACK, True)]   # held, no bounce
    assert seen == [(BOLLINGER_BOUNCE, BUY, C[2].start)]                 # asked as at the start of its candle
    (d,) = [d for d in decisions(e) if d["kind"] == "bounce refused"]
    assert d["reason"] == "not at a significant level" and d["valid"] is False and d["rule"] == "pace and target"
    assert d["direction"] == BUY and d["time_utc"] == "2026-11-04T10:10:00Z" and d["against"]
    assert d["line"].startswith("refused: not at a significant level")
    assert not any(r["event"] == "sending" and r.get("strategy") == BOLLINGER_BOUNCE for r in journal(e))


def test_a_bounce_at_the_level_but_moving_fast_is_refused_and_the_trend_trades_are_held(S, monkeypatch):
    e, ig, clock, seen = trend_then_bounce(S, monkeypatch, verdict(False, "price moving fast", rate="7.5"),
                                           trading_on=True)
    feed(e, clock, C[:4])
    assert len(ig.orders_sent()) == 1 and all(t.open for t in e.manager.trades.values())
    (d,) = [d for d in decisions(e) if d["kind"] == "bounce refused"]
    assert d["reason"] == "price moving fast" and d["level"] == "00 13300" and d["pips_per_hour"] == "7.5"


def test_a_valid_bounce_opens_and_closes_every_trade_open_the_other_way(S, monkeypatch):
    lr = idea(RANGE_TRADE, C[1].start)                                  # not a trend trade, closed too
    e, ig, clock, seen = trend_then_bounce(S, monkeypatch, verdict(True), extra=[lr])
    feed(e, clock, C[:4])
    by = {t.strategy: t for t in e.manager.trades.values()}
    assert set(by) == {EMA_PULLBACK, RANGE_TRADE, BOLLINGER_BOUNCE}
    b = by[BOLLINGER_BOUNCE]
    assert b.open and b.fill == D("101.5")                              # a paper buy at the offer
    for s in (EMA_PULLBACK, RANGE_TRADE):
        t = by[s]
        assert not t.open and t.state == "close" and t.decisions[-1].price == b.fill   # a sell closes at the offer
        assert t.decisions[-1].why == "a Bollinger bounce buy opened at 00 13300, price moving slowly (1.2 pips an hour)"
        assert t.decisions[-1].at == WED + timedelta(minutes=15) and t.decisions[-1].pips == D("-1.5")  # 100.0 -> 101.5
    assert [d["kind"] for d in decisions(e)].count("bounce against trend trades") == 1
    closed = [r for r in trades_rows(e) if r["event"] == "closed"]
    assert sorted(r["strategy"] for r in closed) == [EMA_PULLBACK, RANGE_TRADE]


def test_a_bounce_sell_closes_the_buys_at_its_own_sell_price(S, monkeypatch):
    ideas = {C[1].start: [idea(SLOW_GRIND, C[1].start, direction=BUY, price="100.0")],
             C[2].start: [idea(BOLLINGER_BOUNCE, C[2].start, direction=SELL, price="99.8")]}
    against_trend(monkeypatch, verdict(True))
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, ideas)
    e.start(WED)
    feed(e, clock, C[:3])
    g = [t for t in e.manager.trades.values() if t.strategy == SLOW_GRIND][0]
    assert not g.open and g.decisions[-1].price == D("99.8")             # the bounce's entry, the sell price


def test_without_an_open_trend_trade_against_it_a_bounce_is_sent_as_now_and_closes_nothing(S, monkeypatch):
    ideas = {C[1].start: [idea(RANGE_TRADE, C[1].start)],
             C[2].start: [idea(BOLLINGER_BOUNCE, C[2].start, direction=BUY, price="100.5")]}
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, ideas)        # the real rule: nothing to read (no store)
    e.start(WED)
    feed(e, clock, C[:4])
    assert sorted((t.strategy, t.open) for t in e.manager.trades.values()) == [(BOLLINGER_BOUNCE, True), (RANGE_TRADE, True)]
    assert not any(d["kind"].startswith("bounce") for d in decisions(e))


def test_a_bounce_the_rule_cannot_check_is_refused_while_trend_trades_are_open(S, monkeypatch):
    import trading.against_trend as at

    def broken(s, store, i, t, trades):
        raise KeyError("setup_from")
    monkeypatch.setattr(at, "check", broken)
    ideas = {C[1].start: [idea(EMA_PULLBACK, C[1].start)],
             C[2].start: [idea(BOLLINGER_BOUNCE, C[2].start, direction=BUY, price="100.5")]}
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, ideas)
    e.start(WED)
    feed(e, clock, C[:4])
    assert [t.strategy for t in e.manager.trades.values()] == [EMA_PULLBACK]
    (d,) = [d for d in decisions(e) if d["kind"] == "bounce refused"]
    assert d["reason"].startswith("the rule could not be checked")


def test_the_rule_applies_to_a_live_bounce_too_and_a_refused_one_is_not_sent_when_the_candle_finishes(S, monkeypatch):
    forming = C[2].start
    seen = against_trend(monkeypatch, verdict(False, "price moving fast"))
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, {C[1].start: [idea(EMA_PULLBACK, C[1].start)],
                                                            forming: [idea(BOLLINGER_BOUNCE, forming, BUY, "101.0")]},
                                        trading_on=True, live={forming: [(BOLLINGER_BOUNCE, BUY, D("101.0"))]})
    e.start(WED)
    feed(e, clock, C[:2])
    clock["t"] = forming + timedelta(seconds=40)
    e.on_price(tick(clock["t"], 101.2))
    assert len(ig.orders_sent()) == 1 and seen == [(BOLLINGER_BOUNCE, BUY, forming)]   # the forming candle's start
    feed(e, clock, C[2:3])
    assert len(ig.orders_sent()) == 1                                    # not sent then either
    assert [d["kind"] for d in decisions(e)].count("bounce refused") == 1


def test_a_valid_live_bounce_closes_the_trades_against_it_at_once(S, monkeypatch):
    forming = C[2].start
    against_trend(monkeypatch, verdict(True))
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, {C[1].start: [idea(EMA_PULLBACK, C[1].start)]},
                                        trading_on=True, live={forming: [(BOLLINGER_BOUNCE, BUY, D("101.0"))]})
    e.start(WED)
    feed(e, clock, C[:2])
    clock["t"] = forming + timedelta(seconds=40)
    e.on_price(tick(clock["t"], 101.2))
    by = {t.strategy: t for t in e.manager.trades.values()}
    assert by[BOLLINGER_BOUNCE].open and not by[EMA_PULLBACK].open
    assert by[EMA_PULLBACK].decisions[-1].at == clock["t"]
    assert [r["event"] for r in trades_rows(e)].count("closed") == 1 and len(e.alerts.closed) == 1


def test_a_close_ig_does_not_confirm_keeps_the_trade_open_and_is_tried_again(S, monkeypatch):
    e, ig, clock, seen = trend_then_bounce(S, monkeypatch, verdict(True), trading_on=True)
    ig.close_answer = "notional"                                         # IG refuses the close
    feed(e, clock, C[:3])
    by = {t.strategy: t for t in e.manager.trades.values()}
    p = by[EMA_PULLBACK]
    assert by[BOLLINGER_BOUNCE].open and p.open and "closed" not in [r["event"] for r in trades_rows(e)]
    rows = [json.loads(x) for x in e.manager.journal.read_text().splitlines()]
    assert rows[-1]["decision"] == "close not done" and "IG did not confirm it" in rows[-1]["why"]
    ig.close_answer = "accept"
    clock["t"] = C[3].start + timedelta(seconds=35)                      # past orders.close_retry_seconds (30)
    e.on_price(tick(clock["t"], 100.2))
    assert not p.open and "a Bollinger bounce buy opened at 00 13300" in p.decisions[-1].why
    assert [r["event"] for r in trades_rows(e)].count("closed") == 1
