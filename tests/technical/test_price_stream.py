"""The live price stream, against a pretend stream: what it subscribes to,
ticks, finished-only candles, reconnecting with increasing waits, the
re-login limit, and the no-prices warning."""

import logging

import pytest

from ig.errors import IGLoginFailure
from ig.stream import CANDLE_FIELDS, TICK_FIELDS, PriceStream
from prices.feed import PriceFeed
from prices.store import CandleStore
from tests.technical.fake_stream import (EPIC, SETTINGS, STREAMING, Clock, FakeClient,
                                         FakeTransport, T, new_transport)

OPEN_TIME = T(2026, 11, 4, 10, 0, 0)       # a Wednesday morning: market open
CLOSED_TIME = T(2026, 11, 7, 12, 0, 0)     # a Saturday: market closed


@pytest.fixture(autouse=True)
def fresh_transports():
    FakeTransport.opened.clear()


def make(tmp_path, at=OPEN_TIME):
    clock = Clock(at)
    waits = []
    store = CandleStore(tmp_path / "candles", 30)
    feed = PriceFeed(SETTINGS, store, now=clock)
    client = FakeClient()
    stream = PriceStream(client, EPIC, SETTINGS.stream, new_transport,
                         on_tick=feed.on_tick, on_candle=feed.on_candle,
                         market_open_since=feed.market_open_since, now=clock,
                         wait=lambda s: (waits.append(s), clock.advance(seconds=s)), warn=feed.warn)
    return stream, feed, client, clock, waits, store


def current():
    return FakeTransport.opened[-1]


def test_connects_to_the_streaming_address_as_the_bots_account(tmp_path):
    stream, *_ = make(tmp_path)
    stream.start()
    endpoint, user, password, epic = current().args
    assert endpoint == STREAMING
    assert user == "ACC-SECRET-1234"
    assert password == "CST-secret1|XST-secret1"
    assert epic == "CS.D.GBPUSD.TODAY.IP" == SETTINGS.market.epic
    assert stream.stats.connects == 1 and stream.stats.subscriptions == 2


def test_subscribes_to_ticks_and_igs_5_minute_candles_with_buy_and_sell_fields():
    assert set(TICK_FIELDS) == {"BID", "OFR", "UTM"}
    for side in ("BID", "OFR"):
        for part in ("OPEN", "HIGH", "LOW", "CLOSE"):
            assert f"{side}_{part}" in CANDLE_FIELDS
    assert "CONS_END" in CANDLE_FIELDS and "UTM" in CANDLE_FIELDS
    assert not any("MID" in f for f in CANDLE_FIELDS + TICK_FIELDS)


def test_streaming_library_version_is_pinned():
    from pathlib import Path
    reqs = (Path(__file__).resolve().parents[2] / "requirements.txt").read_text().split()
    assert "lightstreamer-client-lib==2.2.3" in reqs
    assert all("==" in r for r in reqs if r and not r.startswith("#"))


def test_every_tick_is_received_with_buy_and_sell_and_time(tmp_path):
    stream, feed, *_ = make(tmp_path)
    stream.start()
    current().connect()
    for i in range(5):
        current().tick(T(2026, 11, 4, 10, 0, i), bid=f"1.3100{i}", ofr=f"1.3101{i}")
    stream.pump()
    assert feed.ticks == stream.stats.ticks == 5
    assert str(feed.last_tick.sell) == "1.31004" and str(feed.last_tick.buy) == "1.31014"
    assert feed.last_tick.time == T(2026, 11, 4, 10, 0, 4)


def test_unfinished_candles_are_never_stored_finished_ones_are(tmp_path):
    stream, feed, _, _, _, store = make(tmp_path)
    stream.start()
    current().connect()
    start = T(2026, 11, 4, 9, 55)
    current().candle(start, finished=False)
    stream.pump()
    assert store.newest("5m") is None and feed.unfinished_seen == 1
    current().candle(start, finished=True)
    stream.pump()
    c = store.newest("5m")
    assert c.start == start
    assert str(c.buy_open) == "1.31010" and str(c.sell_open) == "1.31000"
    assert str(c.buy_close) == "1.31030" and str(c.sell_close) == "1.31020"


def test_a_finished_candle_with_a_missing_price_is_not_stored(tmp_path):
    stream, feed, _, _, _, store = make(tmp_path)
    stream.start()
    current().candle(T(2026, 11, 4, 9, 55), bid=("1.31", None, "1.30", "1.31"))
    stream.pump()
    assert store.newest("5m") is None
    assert any("not stored" in w for w in feed.warnings)


def test_stream_drops_and_comes_back_with_increasing_waits_and_no_login(tmp_path):
    stream, feed, client, clock, waits, store = make(tmp_path)
    stream.start()
    current().connect()
    current().tick(clock())
    stream.pump()
    for _ in range(9):           # drops, and each reconnect attempt fails again
        current().drop()
        stream.pump()
    assert waits == [5, 10, 20, 40, 80, 160, 300, 300, 300]   # increasing, then the last value, never a fast loop
    assert client.relogins == 0                               # dropping never causes a login
    assert stream.stats.connects == 10
    assert all(t.closed for t in FakeTransport.opened[:-1])   # library retrying is cut off each time
    current().connect()                                       # ... and it comes back
    current().tick(clock(), bid="1.32000", ofr="1.32010")
    current().candle(T(2026, 11, 4, 10, 30))
    stream.pump()
    assert str(feed.last_tick.sell) == "1.32000"
    assert store.newest("5m").start == T(2026, 11, 4, 10, 30)
    assert any("Price stream dropped" in w for w in feed.warnings)


def test_reconnect_waits_start_again_after_the_stream_has_been_healthy(tmp_path):
    stream, feed, client, clock, waits, _ = make(tmp_path)
    stream.start()
    for _ in range(3):
        current().drop()
        stream.pump()
    assert waits == [5, 10, 20]
    current().connect()
    stream.pump()
    clock.advance(minutes=SETTINGS.stream.healthy_after_minutes)
    stream.check()
    current().drop()
    stream.pump()
    assert waits == [5, 10, 20, 5]


def test_events_from_a_closed_connection_are_ignored(tmp_path):
    stream, feed, *_ = make(tmp_path)
    stream.start()
    old = current()
    old.drop()
    stream.pump()
    old.tick(OPEN_TIME)
    old.drop()
    stream.pump()
    assert feed.ticks == 0 and stream.stats.drops == 1


def test_refused_stream_login_gets_one_controlled_relogin_then_stops(tmp_path):
    stream, feed, client, clock, waits, _ = make(tmp_path)
    stream.start()
    current().refuse()
    stream.pump()
    assert client.relogins == 1
    assert current().args[2] == "CST-secret2|XST-secret2"    # new tokens used
    current().refuse()
    with pytest.raises(IGLoginFailure) as e:
        stream.pump()
    assert e.value.error == "stream-login-refused"
    assert client.relogins == 1


def test_a_second_relogin_is_allowed_only_after_the_stream_was_healthy(tmp_path):
    stream, feed, client, clock, *_ = make(tmp_path)
    stream.start()
    current().refuse()
    stream.pump()
    current().connect()
    stream.pump()
    clock.advance(minutes=SETTINGS.stream.healthy_after_minutes)
    stream.check()
    current().refuse()
    stream.pump()
    assert client.relogins == 2


def test_a_failed_relogin_stops(tmp_path):
    stream, feed, client, *_ = make(tmp_path)
    client.fail_relogin = True
    stream.start()
    current().refuse()
    with pytest.raises(IGLoginFailure):
        stream.pump()


def test_other_server_errors_reconnect_with_waits_not_a_login(tmp_path):
    stream, feed, client, clock, waits, _ = make(tmp_path)
    stream.start()
    current().refuse(code=8)
    current_before = current()
    stream.pump()
    current().sub_fail()
    stream.pump()
    assert client.relogins == 0 and waits == [5, 10] and current() is not current_before


def test_no_prices_warning_while_the_market_is_open(tmp_path):
    stream, feed, client, clock, *_ = make(tmp_path)
    stream.start()
    current().connect()
    current().tick(clock())
    stream.pump()
    clock.advance(seconds=SETTINGS.stream.no_prices_warning_seconds - 1)
    stream.check()
    assert not any("NO PRICES" in w for w in feed.warnings)
    clock.advance(seconds=1)
    stream.check()
    stream.check()
    assert sum("NO PRICES" in w for w in feed.warnings) == 1     # once, not every second
    current().tick(clock())
    stream.pump()
    clock.advance(seconds=SETTINGS.stream.no_prices_warning_seconds)
    stream.check()
    assert sum("NO PRICES" in w for w in feed.warnings) == 2


def test_no_prices_warning_not_given_while_the_market_is_closed(tmp_path):
    stream, feed, client, clock, *_ = make(tmp_path, at=CLOSED_TIME)
    stream.start()
    current().connect()
    stream.pump()
    clock.advance(hours=10)
    stream.check()
    assert not any("NO PRICES" in w for w in feed.warnings)


def test_no_prices_wait_counts_from_the_weekly_open_not_from_friday(tmp_path):
    sunday_open = T(2026, 11, 8, 21, 0)
    stream, feed, client, clock, *_ = make(tmp_path, at=T(2026, 11, 6, 21, 59))
    stream.start()
    current().connect()
    current().tick(clock())
    stream.pump()
    clock.t = sunday_open + __import__("datetime").timedelta(seconds=30)
    stream.check()
    assert not any("NO PRICES" in w for w in feed.warnings)


def test_stream_secrets_are_never_logged(tmp_path, caplog):
    caplog.set_level(logging.DEBUG)
    stream, feed, *_ = make(tmp_path)
    stream.start()
    current().refuse()
    stream.pump()
    current().drop()
    stream.pump()
    text = caplog.text + " ".join(feed.warnings)
    for secret in ("ACC-SECRET-1234", "secret1", "secret2", STREAMING):
        assert secret not in text


def test_with_the_real_ig_client_a_refused_stream_relogs_in_once_and_switches_back(tmp_path):
    from ig.client import IGClient
    from tests.technical.fake_ig import CREDS, FakeIG, accounts_ok, login_ok, switch_ok
    ig = FakeIG(login_ok(1), accounts_ok(), switch_ok("XST-switched"), login_ok(2), switch_ok("XST-again"))
    client = IGClient(SETTINGS.ig, CREDS, http=ig, sleep=lambda s: None)
    client.connect()
    stream = PriceStream(client, EPIC, SETTINGS.stream, new_transport, on_tick=lambda f: None,
                         on_candle=lambda f: None, wait=lambda s: None)
    stream.start()
    assert current().args[1] == CREDS.account_id
    assert current().args[2] == "CST-CST-token-1|XST-XST-switched"
    current().refuse()
    stream.pump()
    assert ig.calls() == [("POST", "/session"), ("GET", "/accounts"), ("PUT", "/session"),
                          ("POST", "/session"), ("PUT", "/session")]
    assert ig.sent[-1].json == {"accountId": CREDS.account_id, "defaultAccount": False}
    assert current().args[2] == "CST-CST-token-2|XST-XST-again"
