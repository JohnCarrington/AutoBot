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
