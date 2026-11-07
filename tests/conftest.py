import socket
import sys
from pathlib import Path

import pytest

# Let tests import the project's parts (config, ig, prices, ...) from the project folder.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class RealNetworkUsed(RuntimeError):
    pass


@pytest.fixture(autouse=True)
def no_real_network(monkeypatch):
    """Tests must never call the real IG (or anything else on the network).
    Any attempt to open an internet connection fails the test."""
    real_connect = socket.socket.connect

    def guarded_connect(self, address):
        if self.family in (socket.AF_INET, socket.AF_INET6):
            raise RealNetworkUsed(f"Test tried to open a network connection to {address!r}")
        return real_connect(self, address)

    def guarded_create_connection(address, *args, **kwargs):
        raise RealNetworkUsed(f"Test tried to open a network connection to {address!r}")

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket, "create_connection", guarded_create_connection)

    import requests.adapters

    def guarded_send(self, request, *args, **kwargs):
        raise RealNetworkUsed(f"Test tried to send a real HTTP request to {request.url}")

    monkeypatch.setattr(requests.adapters.HTTPAdapter, "send", guarded_send)


# The switches normally come from the real .env, next to the IG secrets. Tests
# never read the real .env: every test uses this pretend file instead
# (GBPUSD only, 06:00 to 20:30, every strategy on, stop 6 pips, take profit 100), unless it sets its own.
PRETEND_SWITCHES = """\
PAIRS_ON=GBPUSD
NEW_TRADES_FROM=06:00
NEW_TRADES_UNTIL=20:30
STRATEGY_SLOW_GRIND=on
STRATEGY_EMA_PULLBACK=on
STRATEGY_BOLLINGER_BOUNCE=on
STRATEGY_RANGE_TRADE=on
STOP_LOSS_PIPS=6
TAKE_PROFIT_PIPS=100
"""


@pytest.fixture(autouse=True)
def pretend_switches(tmp_path_factory, monkeypatch):
    from config.env_file import ENV_PATH_VAR
    path = tmp_path_factory.getbasetemp() / "pretend_switches.env"
    if not path.exists():
        path.write_text(PRETEND_SWITCHES)
    monkeypatch.setenv(ENV_PATH_VAR, str(path))
    return path
