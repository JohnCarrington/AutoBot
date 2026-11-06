"""The price stream as a service: the systemd file, start-up without history,
recording the gap, stopping cleanly, and exit code 78 on a login failure.
Uses the pretend IG and pretend stream; never contacts IG."""

import re
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from ig.client import IGClient, is_historical_prices_path
from prices.service import serve
from prices.store import CandleStore
from tests.technical.fake_ig import CREDS, FakeIG, accounts_ok, login_ok, logout_ok, switch_ok
from tests.technical.fake_stream import SETTINGS, FakeTransport, T, five, new_transport

ROOT = Path(__file__).resolve().parents[2]
UNIT = ROOT / "deploy" / "autobot-prices.service"


def unit():
    out = {}
    for line in UNIT.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            out.setdefault(k.strip(), []).append(v.strip())
    return out


# ---- the service file -------------------------------------------------------------

def test_service_runs_as_autobot_from_opt_autobot():
    u = unit()
    assert u["User"] == ["autobot"] and u["Group"] == ["autobot"]
    assert u["WorkingDirectory"] == ["/opt/autobot"]
    assert u["ExecStart"] == ["/opt/autobot/.venv/bin/python -m prices.service"]


def test_service_restarts_after_a_crash_waiting_at_least_30_seconds():
    u = unit()
    assert u["Restart"] == ["on-failure"]
    assert int(u["RestartSec"][0]) >= 30


def test_service_never_restarts_after_a_login_failure():
    assert unit()["RestartPreventExitStatus"] == ["78"]


def test_a_crash_loop_cannot_become_a_login_loop():
    u = unit()
    assert int(u["StartLimitBurst"][0]) <= 5 and int(u["StartLimitIntervalSec"][0]) >= 3600


def test_service_starts_on_boot_after_the_network():
    u = unit()
    assert u["WantedBy"] == ["multi-user.target"] and "network-online.target" in u["After"][0]


def test_the_service_never_uses_the_history_door():
    src = (ROOT / "prices" / "service.py").read_text()
    code = "\n".join(l.split("#")[0] for l in src.splitlines() if not l.strip().startswith(('"', "'")))
    assert not re.search(r"^\s*(from|import)\s+(ig\.history|prices\.history_fill)", src, re.M)
    assert "HistoryDoor" not in code


# ---- running it ---------------------------------------------------------------------

def _settings(tmp_path):
    def copy(section, **over):
        d = {k: v for k, v in vars(section).items() if not k.startswith("_")}
        d.update(over)
        return SimpleNamespace(**d)
    return SimpleNamespace(market=SETTINGS.market, chart=SETTINGS.chart, market_hours=SETTINGS.market_hours,
                           stream=SETTINGS.stream,
                           candles=copy(SETTINGS.candles, folder=tmp_path / "candles"),
                           housekeeping=copy(SETTINGS.housekeeping), ig=SETTINGS.ig,
                           levels=copy(SETTINGS.levels, folder=tmp_path / "levels"))


class Clock:
    def __init__(self, t):
        self.t, self.start = t, time.monotonic()

    def __call__(self):  # moves with real time, from a fixed starting point
        return self.t + timedelta(seconds=time.monotonic() - self.start)


def _wait_for(cond, seconds=5):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if cond():
            return True
        time.sleep(0.02)
    return False


@pytest.fixture(autouse=True)
def fresh():
    FakeTransport.opened.clear()


def test_service_start_records_the_gap_asks_no_history_streams_and_stops_cleanly(tmp_path):
    s = _settings(tmp_path)
    store = CandleStore(s.candles.folder, 30)
    for i in range(12):
        store.add(five(T(2026, 11, 4, 9) + i * timedelta(minutes=5)))      # newest ends 10:00
    clock = Clock(T(2026, 11, 4, 12, 0, 20))                                # started 2 hours later
    ig = FakeIG(login_ok(), accounts_ok(), switch_ok(), logout_ok())
    client = IGClient(SETTINGS.ig, CREDS, http=ig, sleep=lambda x: None)
    stop = threading.Event()
    result = {}
    th = threading.Thread(target=lambda: result.setdefault(
        "code", serve(s, client=client, transport_factory=new_transport, stop=stop, now=clock,
                      logs=False, signals=False)))
    th.start()
    assert _wait_for(lambda: FakeTransport.opened)
    t = FakeTransport.opened[-1]
    t.connect()
    t.tick(T(2026, 11, 4, 12, 0, 30))
    t.candle(T(2026, 11, 4, 12, 0), finished=True)
    assert _wait_for(lambda: store.newest("5m").start == T(2026, 11, 4, 12, 0))
    stop.set()
    th.join(10)
    assert not th.is_alive() and result["code"] == 0
    # The gap since the last candle was recorded at start-up, and not filled.
    gaps = store.recorded_gaps()
    assert (gaps[0]["from_utc"], gaps[0]["to_utc"], gaps[0]["missing_candles"]) == \
        ("2026-11-04T10:00:00Z", "2026-11-04T12:00:00Z", "24")
    assert store.get("5m", T(2026, 11, 4, 10, 0)) is None
    # No history asked for; logged out at the end.
    assert not any(is_historical_prices_path(c.path) for c in client.calls)
    assert ig.calls() == [("POST", "/session"), ("GET", "/accounts"), ("PUT", "/session"), ("DELETE", "/session")]
    assert t.closed


def test_service_exits_78_when_ig_refuses_the_stream_after_the_one_relogin(tmp_path):
    s = _settings(tmp_path)
    ig = FakeIG(login_ok(1), accounts_ok(), switch_ok(), login_ok(2), switch_ok(), logout_ok())
    client = IGClient(SETTINGS.ig, CREDS, http=ig, sleep=lambda x: None)
    result = {}

    def run():
        try:
            serve(s, client=client, transport_factory=new_transport, stop=threading.Event(),
                  now=Clock(T(2026, 11, 4, 12)), logs=False, signals=False)
        except SystemExit as e:
            result["code"] = e.code
    th = threading.Thread(target=run)
    th.start()
    assert _wait_for(lambda: FakeTransport.opened)
    FakeTransport.opened[-1].refuse()
    assert _wait_for(lambda: len(FakeTransport.opened) == 2)
    FakeTransport.opened[-1].refuse()
    th.join(10)
    assert result["code"] == 78
    assert ig.calls()[-1] == ("DELETE", "/session")             # still logged out


def test_service_logs_out_and_exits_with_an_error_after_a_crash(tmp_path):
    s = _settings(tmp_path)
    ig = FakeIG(login_ok(), accounts_ok(), switch_ok(), logout_ok())
    client = IGClient(SETTINGS.ig, CREDS, http=ig, sleep=lambda x: None)

    def broken_transport():
        raise RuntimeError("pretend crash")
    with pytest.raises(RuntimeError):
        serve(s, client=client, transport_factory=broken_transport, stop=threading.Event(),
              now=Clock(T(2026, 11, 4, 12)), logs=False, signals=False)
    assert ig.calls()[-1] == ("DELETE", "/session")


def test_a_stop_request_ends_a_reconnect_wait_at_once(tmp_path):
    from ig.stream import PriceStream
    stream = PriceStream(SimpleNamespace(streaming_endpoint="x", stream_login=lambda: ("u", "p")),
                         "EPIC", SETTINGS.stream, new_transport, on_tick=lambda f: None, on_candle=lambda f: None)
    stream.start()
    FakeTransport.opened[-1].drop()
    th = threading.Thread(target=stream.pump)
    th.start()
    time.sleep(0.2)
    stream.request_stop()
    th.join(2)
    assert not th.is_alive()
