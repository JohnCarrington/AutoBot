"""Every part with TWO pretend pairs switched on, one of them a JPY pair, so a
mix-up between pairs fails a test. Never contacts IG (pretend IG and stream).

The pretend pairs (added to a copy of the real settings, with every folder in
a temporary folder):
  EURUSD  epic CS.D.EURUSD.TODAY.IP  pip 0.0001  scale 10000  -> 1 point a pip
  EURJPY  epic CS.D.EURJPY.TODAY.IP  pip 0.01    scale 1000   -> 10 points a pip
EURJPY's 10 points a pip is chosen on purpose (it is a pretend pair): using
the other pair's pip size anywhere gives a different number.
"""

import json
import re
import threading
import time
from datetime import timedelta
from decimal import Decimal as D
from pathlib import Path

import pytest

from analyser.direction import BUY_SIDE, SELL_SIDE
from analyser.report import analyse
from config.pairs import check_same_pair, choose_pair, take_pair_option
from config.settings_loader import DEFAULT_PATH, SettingsError, load_settings
from ig import find_market
from ig.client import IGClient, is_historical_prices_path
from ig.history import HistoryDoor, HistoryRefused
from ig.stream import PriceStream, TickUpdate
from levels.current import LevelsUpdater, build, read_current
from levels.rules import PIVOT, ROUND_NUMBER
from prices.feed import PriceFeed
from prices.history_fill import DONE_FILE, run_one_off
from prices.model import Candle
from prices.service import serve
from prices.store import CandleStore
from rejection.replay import replay
from rejection.watch import RejectionWatcher
from tests.technical.fake_ig import CREDS, FakeIG, Reply, accounts_ok, login_ok, logout_ok, switch_ok
from tests.technical.fake_stream import FakeClient, FakeTransport, T, new_transport
from tests.technical.test_history_door import hist_ok

ROOT = Path(__file__).resolve().parents[2]
FIVE = timedelta(minutes=5)
USD_EPIC, JPY_EPIC = "CS.D.EURUSD.TODAY.IP", "CS.D.EURJPY.TODAY.IP"
PRETEND_PAIRS = f"""
[pairs.EURUSD]
epic = "{USD_EPIC}"
pip_size = "0.0001"
price_scale = 10000

[pairs.EURJPY]
epic = "{JPY_EPIC}"
pip_size = "0.01"
price_scale = 1000
"""
SWITCHES = """PAIRS_ON={pairs}
NEW_TRADES_FROM=06:00
NEW_TRADES_UNTIL=20:30
STRATEGY_SLOW_GRIND=on
STRATEGY_EMA_PULLBACK=off
STRATEGY_BOLLINGER_BOUNCE=on
STRATEGY_RANGE_TRADE=on
STOP_LOSS_PIPS=6
STOP_LOSS_PIPS_EMA_PULLBACK=12
TAKE_PROFIT_PIPS=100
"""


def pretend(tmp_path, pairs_on="EURUSD,EURJPY"):
    text = DEFAULT_PATH.read_text()
    text = re.sub(r'^folder = "/opt/autobot/data/(\w+)"', lambda m: f'folder = "{tmp_path}/data/{m.group(1)}"',
                  text, flags=re.M)
    toml = tmp_path / "settings.toml"
    toml.write_text(text + PRETEND_PAIRS)
    env = tmp_path / "pretend.env"
    env.write_text(SWITCHES.format(pairs=pairs_on))
    return load_settings(toml, switches_from=env)


@pytest.fixture
def st(tmp_path):
    return pretend(tmp_path)


@pytest.fixture(autouse=True)
def fresh():
    FakeTransport.opened.clear()


def C(start, close, tf="5m", minutes=5, spread=D("1.0")):
    c = D(str(close))
    return Candle(tf, start, start + timedelta(minutes=minutes), c + spread, c + 1 + spread, c - 1 + spread,
                  c + spread, c, c + 1, c - 1, c)


def store_of(ps):
    return CandleStore(ps.candles.folder, ps.candles.compress_after_days)


# ---- settings ------------------------------------------------------------------------

def test_each_pair_has_its_own_epic_pip_size_and_folders(st, tmp_path):
    usd, jpy = st.for_pair("EURUSD"), st.for_pair("EURJPY")
    assert (usd.market.epic, usd.market.points_per_pip) == (USD_EPIC, 1)
    assert (jpy.market.epic, jpy.market.points_per_pip, jpy.market.pip_size) == (JPY_EPIC, 10, D("0.01"))
    assert usd.candles.folder == tmp_path / "data/candles/EURUSD" != jpy.candles.folder
    assert usd.levels.folder == tmp_path / "data/levels/EURUSD"
    assert jpy.history.pair_folder == tmp_path / "data/history/EURJPY"
    assert usd.history.folder == jpy.history.folder == tmp_path / "data/history"       # one shared door
    assert jpy.pair.real_price(D("162345")) == D("162.345") and usd.pair.real_price(D("11650.3")) == D("1.16503")
    assert [p.market.pair for p in st.pairs_on()] == ["EURUSD", "EURJPY"]
    assert not hasattr(st, "market")               # nothing works without being given a pair
    with pytest.raises(SettingsError, match="no \\[pairs.USDCHF\\]"):
        st.for_pair("USDCHF")


def test_the_command_line_tools_need_a_pair_when_more_than_one_is_on(st, tmp_path):
    with pytest.raises(SystemExit, match="say which with --pair"):
        choose_pair(st, None)
    assert choose_pair(st, "eurjpy").market.pair == "EURJPY"
    (tmp_path / "one").mkdir()
    assert choose_pair(pretend(tmp_path / "one", "EURJPY"), None).market.pair == "EURJPY"
    assert take_pair_option(["a", "--pair", "EURUSD", "b"]) == ("EURUSD", ["a", "b"])


def test_a_pair_mix_up_is_refused_by_every_part(st):
    usd, jpy = st.for_pair("EURUSD"), st.for_pair("EURJPY")
    wrong = store_of(jpy)
    check_same_pair(jpy, wrong)
    for part in (lambda: PriceFeed(usd, wrong), lambda: build(usd, wrong, T(2026, 11, 4, 12)),
                 lambda: LevelsUpdater(usd, wrong), lambda: replay(usd, wrong, T(2026, 11, 4), T(2026, 11, 4, 1)),
                 lambda: analyse(usd, wrong, T(2026, 11, 4, 12)),
                 lambda: run_one_off(None, wrong, usd, T(2026, 11, 7), print)):
        with pytest.raises(ValueError, match="Pair mix-up: these settings are for EURUSD"):
            part()


# ---- the candle store ------------------------------------------------------------------

def test_each_pair_keeps_its_candles_in_its_own_folder(st):
    usd, jpy = store_of(st.for_pair("EURUSD")), store_of(st.for_pair("EURJPY"))
    usd.add(C(T(2026, 11, 4, 9), "11650.3"))
    jpy.add(C(T(2026, 11, 4, 9), "16234.5"))
    assert usd.get("5m", T(2026, 11, 4, 9)).sell_close == D("11650.3")
    assert jpy.get("5m", T(2026, 11, 4, 9)).sell_close == D("16234.5")
    assert (usd.folder / "5m" / "2026-11-04.csv").exists() and (jpy.folder / "5m" / "2026-11-04.csv").exists()
    assert usd.folder.name == "EURUSD" and jpy.folder.name == "EURJPY"


# ---- the stream: one connection, every pair ---------------------------------------------

def test_one_connection_subscribes_to_every_pair_and_routes_each_update_to_its_pair(st):
    got = []
    stream = PriceStream(FakeClient(), (USD_EPIC, JPY_EPIC), st.stream, new_transport,
                         on_tick=lambda e, f: got.append(("tick", e, f["BID"])),
                         on_candle=lambda e, f: got.append(("candle", e, f["BID_CLOSE"])), wait=lambda s: None)
    stream.start()
    t = FakeTransport.opened[-1]
    assert t.args[3] == (USD_EPIC, JPY_EPIC) and stream.stats.subscriptions == 4 and len(FakeTransport.opened) == 1
    t.connect()
    t.tick(T(2026, 11, 4, 9), bid="16234.5", ofr="16236.0", epic=JPY_EPIC)
    t.tick(T(2026, 11, 4, 9), bid="11650.3", ofr="11651.0", epic=USD_EPIC)
    t.candle(T(2026, 11, 4, 9), bid=("16234", "16240", "16230", "16235"), ofr=("1", "1", "1", "1"), epic=JPY_EPIC)
    t.emit(TickUpdate("CS.D.GBPUSD.TODAY.IP", {"BID": "1", "OFR": "1", "UTM": "1"}))     # not asked for: ignored
    stream.pump()
    assert got == [("tick", JPY_EPIC, "16234.5"), ("tick", USD_EPIC, "11650.3"), ("candle", JPY_EPIC, "16235")]


def test_the_stream_needs_a_list_of_different_epics(st):
    for bad in (USD_EPIC, (), (USD_EPIC, USD_EPIC)):
        with pytest.raises(ValueError):
            PriceStream(FakeClient(), bad, st.stream, new_transport, on_tick=print, on_candle=print)


# ---- the service: both pairs, one login, no history -----------------------------------------

class Clock:
    def __init__(self, t):
        self.t, self.start = t, time.monotonic()

    def __call__(self):
        return self.t + timedelta(seconds=time.monotonic() - self.start)


def _wait_for(cond, seconds=5):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if cond():
            return True
        time.sleep(0.02)
    return False


def test_the_service_streams_every_pair_into_its_own_store_with_one_login_and_no_history(st):
    usd_s, jpy_s = st.for_pair("EURUSD"), st.for_pair("EURJPY")
    usd = store_of(usd_s)
    for i in range(12):
        usd.add(C(T(2026, 11, 4, 9) + i * FIVE, "11650.3"))      # EURUSD has candles to 10:00
    # EURJPY is newly switched on: its store is empty, and it is NOT filled from history.
    ig = FakeIG(login_ok(), accounts_ok(), switch_ok(), logout_ok())
    client = IGClient(st.ig, CREDS, http=ig, sleep=lambda x: None)
    stop, result = threading.Event(), {}
    th = threading.Thread(target=lambda: result.setdefault("code", serve(
        st, client=client, transport_factory=new_transport, stop=stop, now=Clock(T(2026, 11, 4, 12, 0, 20)),
        logs=False, signals=False)))
    th.start()
    assert _wait_for(lambda: FakeTransport.opened)
    t = FakeTransport.opened[-1]
    assert t.epics == (USD_EPIC, JPY_EPIC)
    t.connect()
    t.candle(T(2026, 11, 4, 12), bid=("11650", "11652", "11649", "11651"), ofr=("11651", "11653", "11650", "11652"),
             epic=USD_EPIC)
    t.candle(T(2026, 11, 4, 12), bid=("16234", "16240", "16230", "16235"), ofr=("16236", "16242", "16232", "16237"),
             epic=JPY_EPIC)
    jpy = store_of(jpy_s)
    assert _wait_for(lambda: jpy.get("5m", T(2026, 11, 4, 12)) is not None
                     and usd.get("5m", T(2026, 11, 4, 12)) is not None)
    stop.set()
    th.join(10)
    assert not th.is_alive() and result["code"] == 0
    assert jpy.get("5m", T(2026, 11, 4, 12)).sell_close == D("16235")      # each pair's candle in its own store
    assert usd.get("5m", T(2026, 11, 4, 12)).sell_close == D("11651")
    assert jpy.days("5m") == usd.days("5m")[-1:] and len(jpy.read_day("5m", jpy.days("5m")[0])) == 1
    # EURUSD's gap since 10:00 was recorded in EURUSD's store only; nothing filled.
    assert [(g["from_utc"], g["to_utc"]) for g in usd.recorded_gaps()] == [("2026-11-04T10:00:00Z", "2026-11-04T12:00:00Z")]
    assert jpy.recorded_gaps() == []
    assert usd.get("5m", T(2026, 11, 4, 10)) is None
    # One login for both pairs, no history, logged out; each pair's levels in its own folder.
    assert ig.calls() == [("POST", "/session"), ("GET", "/accounts"), ("PUT", "/session"), ("DELETE", "/session")]
    assert not any(is_historical_prices_path(c.path) for c in client.calls)
    assert read_current(usd_s.levels.folder)["as_of_utc"] and read_current(jpy_s.levels.folder)["as_of_utc"]


# ---- levels, rejection, analyser: each pair's own pips -------------------------------------

def test_levels_use_each_pairs_own_pip_size(st):
    out = {}
    for name, close in (("EURUSD", "11653.0"), ("EURJPY", "16234.5")):
        ps = st.for_pair(name)
        s = store_of(ps)
        s.add(C(T(2026, 11, 4, 9), close))
        out[name] = sorted(lv.price for lv in build(ps, s, T(2026, 11, 4, 9, 10)).levels if lv.type == ROUND_NUMBER)
    # every 50 pips within 150 pips: EURUSD 50 points apart, EURJPY 500 points apart
    assert out["EURUSD"] == [D(x) for x in range(11550, 11801, 50)]
    assert out["EURJPY"] == [D(x) for x in range(15000, 17501, 500)]


def test_the_rejection_spread_limit_is_in_each_pairs_own_pips(st):
    wide = C(T(2026, 11, 4, 9), "100", spread=D("20"))         # IG's spread 20 points
    assert RejectionWatcher(st.for_pair("EURUSD")).max_spread() == D(3)
    assert RejectionWatcher(st.for_pair("EURUSD")).spike(wide)          # 20 pips: a spike
    assert RejectionWatcher(st.for_pair("EURJPY")).max_spread() == D(30)
    assert not RejectionWatcher(st.for_pair("EURJPY")).spike(wide)      # 2 pips: normal


def test_the_analyser_works_out_each_pair_from_its_own_store(st):
    day = T(2026, 11, 3)
    sides = {}
    for name, base, last in (("EURUSD", 11600, 11700), ("EURJPY", 16200, 16000)):
        ps = st.for_pair(name)
        s = store_of(ps)
        for i in range(288):
            s.add(C(day + i * FIVE, base))
        for i in range(24):
            s.add(C(T(2026, 11, 4) + i * FIVE, last))
        s.add(Candle("1d", day, day + timedelta(days=1), *(D(base + 1),) * 4, *(D(base),) * 4))
        r = analyse(ps, s, T(2026, 11, 4, 2))
        assert r.direction.pivot == D(base)
        sides[name] = r.direction.side
    assert sides == {"EURUSD": BUY_SIDE, "EURJPY": SELL_SIDE}


# ---- the history door: one budget and one allowance for all pairs ------------------------

def test_the_history_budget_and_allowance_are_shared_and_each_request_records_its_pair(st, tmp_path):
    from tests.technical.test_history_door import settings as door_settings
    ig = FakeIG(login_ok(), accounts_ok(), switch_ok(), hist_ok(3, remaining=9000), hist_ok(3, remaining=8990))
    client = IGClient(st.ig, CREDS, http=ig, sleep=lambda s: None)
    client.connect()
    door = HistoryDoor(client, door_settings(tmp_path, weekly_budget_points=8), now=lambda: T(2026, 11, 6, 20))
    door.fetch(USD_EPIC, "MINUTE_5", T(2026, 11, 4, 10), T(2026, 11, 4, 10, 10), 3, "test")
    door.fetch(JPY_EPIC, "MINUTE_5", T(2026, 11, 4, 10), T(2026, 11, 4, 10, 10), 3, "test")
    assert [e["epic"] for e in door.ledger()] == [USD_EPIC, JPY_EPIC]
    assert door.points_last_7_days() == 6 and door.ig_figures()["remaining"] == 8990
    with pytest.raises(HistoryRefused, match="weekly budget"):        # 6 used by both pairs + 3 > 8
        door.fetch(USD_EPIC, "MINUTE_5", T(2026, 11, 4, 11), T(2026, 11, 4, 11, 10), 3, "test")


def test_a_pairs_one_off_fill_is_its_own_and_never_starts_by_itself(st):
    usd, jpy = st.for_pair("EURUSD"), st.for_pair("EURJPY")
    usd.history.pair_folder.mkdir(parents=True)
    (usd.history.pair_folder / DONE_FILE).write_text(json.dumps({"status": "done"}))
    with pytest.raises(RuntimeError, match="fill for EURUSD has already been run"):
        run_one_off(None, store_of(usd), usd, T(2026, 11, 7), print)
    assert not (jpy.history.pair_folder / DONE_FILE).exists()           # EURJPY's fill is still to be approved
    from prices import history_fill
    with pytest.raises(SystemExit):                                    # the pair must always be named
        history_fill.main(["plan"])
    for f in ("prices/service.py", "prices/feed.py", "prices/run.py", "levels/current.py", "analyser/report.py"):
        src = (ROOT / f).read_text()
        assert not re.search(r"^\s*(from|import)\s+(ig\.history|prices\.history_fill)", src, re.M), f


def test_the_market_search_looks_for_the_pair_it_is_given(st, capsys):
    found = Reply(200, {"markets": [{"epic": JPY_EPIC, "instrumentName": "EUR/JPY", "instrumentType": "CURRENCIES",
                                     "expiry": "DFB", "marketStatus": "TRADEABLE"}]})
    ig = FakeIG(login_ok(), accounts_ok(), switch_ok(), found, logout_ok())
    assert find_market.main("eurjpy", st, CREDS, ig) == 0
    assert ("GET", "/markets?searchTerm=EURJPY") in ig.calls()


# ---- the one-off move of the existing GBPUSD data -------------------------------------------

def _old_layout(tmp_path):
    """A pretend copy of the old (single-pair) layout, and settings pointing at it."""
    st = pretend(tmp_path, "EURUSD")
    data = tmp_path / "data"
    old = CandleStore(data / "candles", 30)
    for i in range(12):
        old.add(C(T(2026, 11, 4, 9) + i * FIVE, "13350.0"))
    old.add(Candle("1h", T(2026, 11, 4, 9), T(2026, 11, 4, 10), *(D("13351"),) * 4, *(D("13350"),) * 4, 12, 12))
    old.record_gap("5m", T(2026, 11, 4, 10), T(2026, 11, 4, 11), 12, T(2026, 11, 4, 11), "pretend")
    (data / "candles" / "archive_22h_layout" / "1d").mkdir(parents=True)
    (data / "candles" / "archive_22h_layout" / "1d" / "2026-11-03.csv").write_text("start_utc,x\nA,1\nB,2\n")
    (data / "levels").mkdir(parents=True)
    (data / "levels" / "current.json").write_text("{}\n")
    (data / "history").mkdir(parents=True)
    for n in ("ledger.json", "ig_allowance.json", "daily_record.csv", "ig_daily_candles.csv", "one_off_fill_done.json"):
        (data / "history" / n).write_text(n + "\n")
    return st, data


def test_the_move_puts_gbpusds_data_in_its_folders_and_proves_nothing_was_lost(tmp_path, monkeypatch, capsys):
    from prices import move_to_pairs as mv
    st, data = _old_layout(tmp_path)
    monkeypatch.setattr(mv, "load_settings", lambda: st)
    monkeypatch.setattr(mv, "service_state", lambda: "inactive")
    before = sorted(p.relative_to(data).as_posix() for p in data.rglob("*") if p.is_file())
    assert mv.main(["plan"]) == 0
    assert sorted(p.relative_to(data).as_posix() for p in data.rglob("*") if p.is_file()) == before   # plan: no change
    assert mv.main(["go"]) == 0
    out = capsys.readouterr().out
    assert "candle rows: SAME" in out and "every file's fingerprint: SAME" in out and "Nothing was lost." in out
    assert "5m 12" in out and "archive 1d 2" in out
    g = CandleStore(data / "candles" / "GBPUSD", 30)
    assert len(g.read_day("5m", g.days("5m")[0])) == 12 and len(g.recorded_gaps()) == 1
    assert (data / "levels/GBPUSD/current.json").exists() and (data / "history/GBPUSD/one_off_fill_done.json").exists()
    for shared in ("ledger.json", "ig_allowance.json", "daily_record.csv"):
        assert (data / "history" / shared).exists()                   # the shared door's files stay put
    assert not (data / "candles/5m").exists()
    assert json.loads((data / "moved_to_pair_folders.json").read_text())["same"]["candle rows"] is True
    assert mv.main(["go"]) == 0 and "Nothing to move" in capsys.readouterr().out     # never twice


def test_the_move_refuses_while_the_service_runs_or_anything_is_unexpected(tmp_path, monkeypatch, capsys):
    from prices import move_to_pairs as mv
    st, data = _old_layout(tmp_path)
    monkeypatch.setattr(mv, "load_settings", lambda: st)
    monkeypatch.setattr(mv, "service_state", lambda: "active")
    assert mv.main(["go"]) == 3 and "Stop it first" in capsys.readouterr().out
    assert (data / "candles/5m").exists()
    monkeypatch.setattr(mv, "service_state", lambda: "inactive")
    (data / "candles" / "mystery.txt").write_text("?")
    assert mv.main(["go"]) == 3 and "UNEXPECTED" in capsys.readouterr().out
    assert (data / "candles/5m").exists() and not (data / "candles/GBPUSD").exists()
