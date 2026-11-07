"""The one market search: exactly one market call, and the epic it found is in the settings file."""

from ig import find_market
from tests.technical.fake_ig import CREDS, FakeIG, Reply, accounts_ok, login_ok, logout_ok, switch_ok
from tests.technical.fake_stream import SETTINGS


def test_find_market_makes_one_market_search_and_no_other_market_call(capsys):
    found = Reply(200, {"markets": [
        {"epic": "CS.D.GBPUSD.TODAY.IP", "instrumentName": "GBP/USD", "instrumentType": "CURRENCIES",
         "expiry": "DFB", "marketStatus": "TRADEABLE"},
        {"epic": "CF.D.GBPUSD.DEC.IP", "instrumentName": "GBP/USD Forward", "instrumentType": "CURRENCIES",
         "expiry": "DEC-26", "marketStatus": "TRADEABLE"}]})
    ig = FakeIG(login_ok(), accounts_ok(), switch_ok(), found, logout_ok())
    assert find_market.main("GBPUSD", SETTINGS, CREDS, ig) == 0
    assert ig.calls() == [("POST", "/session"), ("GET", "/accounts"), ("PUT", "/session"),
                          ("GET", "/markets?searchTerm=GBPUSD"), ("DELETE", "/session")]
    out = capsys.readouterr().out
    assert "CS.D.GBPUSD.TODAY.IP" in out and "SPREADBET" in out


def test_the_spread_bet_epic_is_in_the_settings_file():
    assert SETTINGS.market.epic == "CS.D.GBPUSD.TODAY.IP"
