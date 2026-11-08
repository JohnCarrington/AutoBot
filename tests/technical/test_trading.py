"""Technical tests for the wiring (trading/engine.py and the price service): the analyser and strategies are
pretend ones giving scripted candles and ideas; the order sender and trade manager are the real ones, with a
pretend IG. Nothing here contacts IG."""

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from strategies.common import BOLLINGER_BOUNCE, BREAKOUT, BUY, EMA_PULLBACK, SELL, SLOW_GRIND, Idea
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
                safety={"folder": tmp_path / "safety"})


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
    """The strategies: scripted ideas per candle start."""
    def __init__(self, tracker, ideas):
        self.tracker, self.ideas, self.done, self.week_open = tracker, ideas, 0, tracker.week_open

    def step(self):
        out = []
        for h in self.tracker.history[self.done:]:
            out += [(h[0].candle, i) for i in self.ideas.get(h[0].candle.start, [])]
        self.done = len(self.tracker.history)
        return out


def idea(strategy, t, direction=SELL, price="100", allowed=True):
    return Idea("GBPUSD", strategy, direction, t, D(price), "trend", "down", None, "sell side", ["made up"], allowed,
                "" if allowed else "made up block", {})


def make(S, monkeypatch, candles, ideas, trading_on=False, ig=None, clock=None):
    tracker = PretendTracker(candles)
    monkeypatch.setattr(eng, "StateTracker", lambda s, memo: tracker)
    monkeypatch.setattr(eng, "MemoStore", lambda store: None)
    monkeypatch.setattr(eng, "StrategyRunner", lambda s, memo, tr, hourly_end=None: PretendRunner(tr, ideas))
    monkeypatch.setattr(eng, "trend_day_at", lambda s, store, t: SimpleNamespace(direction=None))
    ig = ig or PretendIG()
    clock = clock or {"t": WED}
    quote = {"q": (D("100.0"), D("101.5"))}
    alerts = SimpleNamespace(sent=[], problem=lambda k, t: alerts.sent.append((k, t)), info=lambda t, key=None: None)
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
    assert o[3]["direction"] == "SELL" and o[3]["forceOpen"] is True and o[3]["stopDistance"] == 6.0
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
    stop = candle(WED + timedelta(minutes=15), 100, 110, 99.5, 109)          # stops the first sell
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
