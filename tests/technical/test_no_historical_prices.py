"""ONE GUARDED DOOR: only ig/history.py may ask IG for historical prices.

IG's historical prices are the REST calls under /prices (GET /prices/{epic},
/prices/{epic}/{resolution}, ... in every version). This test fails if any
code in the project other than the history door could call them."""

import re
from pathlib import Path

import pytest

from ig.client import HistoricalPricesForbidden, IGClient, is_historical_prices_path
from tests.technical.fake_ig import CREDS, FakeIG, accounts_ok, login_ok, switch_ok
from tests.technical.fake_stream import SETTINGS

ROOT = Path(__file__).resolve().parents[2]
THIS = Path(__file__).resolve()

# Built in pieces so this file does not match its own patterns.
# A string that is an IG URL path for prices: "/prices...", f"/prices/{epic}", ".../deal/prices"
PRICES_PATH = re.compile(r"""["']/""" + "pri" + r"""ces(?=[/?{"'])|/deal/""" + "pri" + "ces")
# A function name for fetching history, e.g. fetch_historical_prices_by_epic
HISTORY_WORDS = re.compile("histor" + r"(ic|ical)_" + "pri" + "ces", re.I)
TRADING_IG = re.compile(r"\btrading_" + "ig\b")
# The history door is the only file allowed to ask for them.
DOOR = "ig/history.py"
DOOR_KEY = "_open_" + "history_door"
# The guard in ig/client.py that refuses these calls may name them.
ALLOWED_NAMES = ("is_" + "historical_" + "prices_path", "Historical" + "PricesForbidden")
GUARD_LINE = 'return p == "/' + 'prices" or p.startswith("/' + 'prices/")'


def _project_python_files():
    for p in ROOT.rglob("*.py"):
        if ".venv" in p.parts or p.resolve() == THIS:
            continue
        yield p


def test_no_code_outside_the_history_door_calls_igs_historical_prices():
    offenders = []
    for p in _project_python_files():
        rel = p.relative_to(ROOT).as_posix()
        if rel == DOOR:
            continue
        for n, line in enumerate(p.read_text().splitlines(), start=1):
            if DOOR_KEY in line and not (rel == "ig/client.py" and "def " + DOOR_KEY in line):
                offenders.append(f"{rel}:{n}: opens the history door: {line.strip()}")
            code = line.split("#", 1)[0]
            if p.relative_to(ROOT).as_posix() == "ig/client.py" and code.strip() == GUARD_LINE:
                continue
            for name in ALLOWED_NAMES:
                code = code.replace(name, "")
            if PRICES_PATH.search(code) or TRADING_IG.search(code) or HISTORY_WORDS.search(code):
                offenders.append(f"{p.relative_to(ROOT)}:{n}: {line.strip()}")
    assert not offenders, "Code that could ask IG for historical prices:\n" + "\n".join(offenders)


def test_the_scan_would_catch_a_historical_prices_call():
    bad = ['client.request("GET", f"/' + 'prices/{epic}/MINUTE_5/10", "2", what="x")',
           "r = self._send('GET', '/" + "prices/CS.D.GBPUSD.TODAY.IP', '3')",
           "ig_service.fetch_" + "historical_" + "prices_by_epic(epic)"]
    for line in bad:
        assert PRICES_PATH.search(line) or HISTORY_WORDS.search(line), line


@pytest.mark.parametrize("path", ["/prices/CS.D.GBPUSD.TODAY.IP", "/prices/CS.D.GBPUSD.TODAY.IP/MINUTE_5/10",
                                  "/prices/CS.D.GBPUSD.TODAY.IP?resolution=DAY&max=10", "/PRICES/X", "/prices"])
def test_the_ig_client_refuses_historical_price_paths_outside_the_door_without_sending(path):
    assert is_historical_prices_path(path)
    ig = FakeIG(login_ok(), accounts_ok(), switch_ok())  # no reply queued for a prices call
    client = IGClient(SETTINGS.ig, CREDS, http=ig, sleep=lambda s: None)
    client.connect()
    with pytest.raises(HistoricalPricesForbidden):
        client.request("GET", path, "3", what="prices")
    assert ig.calls() == [("POST", "/session"), ("GET", "/accounts"), ("PUT", "/session")]
    assert not any(is_historical_prices_path(c.path) for c in client.calls)


@pytest.mark.parametrize("path", ["/markets?searchTerm=GBPUSD", "/session", "/accounts", "/positions"])
def test_other_paths_are_not_mistaken_for_historical_prices(path):
    assert not is_historical_prices_path(path)


def test_the_history_door_really_is_where_the_history_call_is():
    text = (ROOT / DOOR).read_text()
    assert PRICES_PATH.search(text) and DOOR_KEY in text


def test_the_stream_asks_only_for_live_items_without_old_ticks():
    src = (ROOT / "ig" / "stream.py").read_text()
    assert 'ticks.setRequestedSnapshot("no")' in src
    items = set(re.findall(r'f"CHART:\{epic\}:([A-Z0-9]+)"', src))
    assert items == {"TICK", "5MINUTE"}
