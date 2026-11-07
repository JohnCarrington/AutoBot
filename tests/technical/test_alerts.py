"""The Telegram alerts part: the sender and its limit, keeping the secrets
secret, the Sunday and daily "ready" messages (or a problem alert instead),
the problem alerts, and the trade messages. Uses a pretend Telegram: no test
ever sends a real message (and tests/conftest.py blocks the network anyway)."""

import json
import logging
import threading
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from alerts.ready import ReadyAlerts, ReadyContext, run_checks
from alerts.telegram import Alerts, Telegram, TelegramCredentials, TelegramNotSetUp, load_telegram
from alerts.trades import TradeClosed, TradeOpened, closed_text, opened_text
from ig.allowance_status import HistoryStatus
from prices.model import Candle
from prices.store import CandleStore
from tests.technical.test_pairs import pretend

UTC = timezone.utc
TOKEN, CHAT = "123456:SECRET-TOKEN-abc", "-1009876543"


def T(*a):
    return datetime(*a, tzinfo=UTC)


class Reply:
    def __init__(self, status=200, body=None):
        self.status_code, self._body = status, body if body is not None else {"ok": True, "result": {"message_id": 7}}

    def json(self):
        return self._body


class PretendTelegram:
    """Stands in for Telegram's HTTP API. Records every message."""

    def __init__(self, *replies):
        self.posts, self.replies = [], list(replies)

    def post(self, url, json=None, timeout=None):
        self.posts.append((url, json, timeout))
        r = self.replies.pop(0) if self.replies else Reply()
        if isinstance(r, Exception):
            raise r
        return r

    @property
    def texts(self):
        return [j["text"] for _, j, _ in self.posts]


class Clock:
    def __init__(self, t):
        self.t = t

    def __call__(self):
        return self.t


@pytest.fixture
def st(tmp_path):
    return pretend(tmp_path)                       # EURUSD and EURJPY switched on; folders in tmp_path


def tg(st, http, clock=None):
    return Telegram(TelegramCredentials(TOKEN, CHAT), st.alerts, http=http, now=clock or Clock(T(2026, 11, 9, 6)))


# ---- the sender -------------------------------------------------------------------------

def test_a_message_goes_to_telegrams_send_message_for_the_chat(st):
    http = PretendTelegram()
    r = tg(st, http).send("hello")
    (url, body, timeout), = http.posts
    assert url == f"https://api.telegram.org/bot{TOKEN}/sendMessage" and body == {"chat_id": CHAT, "text": "hello"}
    assert timeout == st.alerts.request_timeout_seconds == 15
    assert (r.sent, r.message_id) == (True, 7)


def test_the_same_problem_sends_at_most_one_message_every_10_minutes(st):
    http, clock = PretendTelegram(), Clock(T(2026, 11, 9, 6))
    t = tg(st, http, clock)
    assert t.send("stream quiet", "stream-quiet").sent
    clock.t += timedelta(minutes=3)
    assert t.send("stream quiet", "stream-quiet").why == "held back by the limit"
    assert t.send("stream quiet", "stream-quiet").why == "held back by the limit"
    assert t.send("store problem", "store-problem").sent                       # another problem is not held back
    clock.t += timedelta(minutes=8)                                             # 11 minutes after the first
    assert t.send("stream quiet", "stream-quiet").sent
    assert http.texts[-1].startswith("stream quiet\n(2 more like this held back since 2026-11-09 06:00 UTC)")
    assert len(http.posts) == 3 and st.alerts.same_problem_every_minutes == 10


def test_the_limit_holds_across_a_restart(st):
    clock = Clock(T(2026, 11, 9, 6))
    tg(st, PretendTelegram(), clock).send("x", "login-failure")
    http = PretendTelegram()
    clock.t += timedelta(minutes=2)
    assert not tg(st, http, clock).send("x", "login-failure").sent and http.posts == []


def test_the_token_and_chat_id_are_never_logged_or_shown(st, caplog, tmp_path):
    caplog.set_level(logging.DEBUG)
    err = ConnectionError(f"HTTPSConnectionPool: /bot{TOKEN}/sendMessage failed")    # library errors hold the address
    t = tg(st, PretendTelegram(err, Reply(401, {"ok": False, "description": "Unauthorized"})))
    a = t.send("one")
    b = t.send("two")
    assert (a.sent, a.why) == (False, "no reply from Telegram (ConnectionError)")
    assert (b.sent, b.why) == (False, "Telegram refused it: HTTP 401 (Unauthorized)")
    shown = caplog.text + a.why + b.why + repr(t._creds) + str(t._creds)
    assert TOKEN not in shown and CHAT not in shown and "SECRET" not in shown
    env = tmp_path / "x.env"
    env.write_text("TELEGRAM_BOT_TOKEN=\nTELEGRAM_CHAT_ID=-100123\n")
    with pytest.raises(TelegramNotSetUp) as e:
        load_telegram(env)
    assert "TELEGRAM_BOT_TOKEN" in str(e.value) and "-100123" not in str(e.value)


def test_without_telegram_set_up_alerts_go_to_the_log_and_the_bot_carries_on(st, caplog):
    caplog.set_level(logging.INFO)
    a = Alerts.from_env(st)                        # the pretend switches file has no Telegram secrets
    assert a.telegram is None
    assert a.problem("stream-quiet", "NO PRICES").why == "Telegram not set up"
    assert "ALERT stream-quiet: NO PRICES" in caplog.text


# ---- the ready messages ------------------------------------------------------------------

def C(start, close="11650.0"):
    c = D(close)
    return Candle("5m", start, start + timedelta(minutes=5), c + 1, c + 2, c, c + 1, c, c + 1, c - 1, c)


def ctx_for(st, stores, *, logged_in=True, connected=True, remaining=4157, blocked=False, now=None):
    hist = st.history.folder
    hist.mkdir(parents=True, exist_ok=True)
    (hist / "ig_allowance.json").write_text(json.dumps({"remaining": remaining, "total": 10000,
                                                        "resets_utc": "2026-11-13T03:00:03Z",
                                                        "seen_utc": "2026-11-07T09:14:30Z"}))
    if blocked:
        (hist / "BLOCKED.json").write_text(json.dumps({"expires_utc": "2026-11-20T00:00:00Z", "reason": "IG refused"}))
    stream = SimpleNamespace(connected_since=T(2026, 11, 8, 21, 0, 2) if connected else None, stopped=False)
    feeds = {p: SimpleNamespace(pair=p, store=s, settings=st.for_pair(p)) for p, s in stores.items()}
    return ReadyContext(st, SimpleNamespace(account_active=logged_in), stream, feeds,
                        HistoryStatus(hist, now or (lambda: T(2026, 11, 9, 6))))


def stores(st):
    return {p: CandleStore(st.for_pair(p).candles.folder, 30) for p in ("EURUSD", "EURJPY")}


def sent_alerts(st, http, clock):
    return Alerts(Telegram(TelegramCredentials(TOKEN, CHAT), st.alerts, http=http, now=clock))


def test_sunday_ready_is_sent_once_every_pair_has_its_first_candle_of_the_week(st):
    s = stores(st)
    http, clock = PretendTelegram(), Clock(T(2026, 11, 8, 21, 3))
    ready = ReadyAlerts(st, sent_alerts(st, http, clock), lambda: ctx_for(st, s, now=clock), now=clock)
    s["EURUSD"].add(C(T(2026, 11, 6, 21, 55)))              # last week's
    ready.tick()
    assert http.posts == []                                 # waiting for this week's first candles
    s["EURUSD"].add(C(T(2026, 11, 8, 21, 0)))
    clock.t = T(2026, 11, 8, 21, 5, 2)
    ready.tick()
    assert http.posts == []                                 # EURJPY has none yet
    s["EURJPY"].add(C(T(2026, 11, 8, 21, 0), "16234.5"))
    ready.tick()
    (text,) = http.texts
    assert text.startswith("AutoBot READY for the week (Sunday reopen Sun 08 Nov 21:00 GMT)")
    for line in ("OK   Logged in to IG", "OK   Price stream connected", "OK   EURUSD candles arriving",
                 "OK   EURJPY candles arriving", "OK   EURUSD candle store checks", "OK   EURJPY candle store checks",
                 "OK   IG history allowance: 4157 of 10000 left (floor 2000"):
        assert line in text
    clock.t += timedelta(minutes=10)
    ready.tick()
    assert len(http.posts) == 1                             # once a week


def test_a_pair_with_no_candle_by_the_deadline_sends_a_problem_alert_instead(st):
    s = stores(st)
    s["EURUSD"].add(C(T(2026, 11, 8, 21, 0)))
    http, clock = PretendTelegram(), Clock(T(2026, 11, 8, 21, 31))
    ReadyAlerts(st, sent_alerts(st, http, clock), lambda: ctx_for(st, s, now=clock), now=clock).tick()
    (text,) = http.texts
    assert text.startswith("AutoBot PROBLEM: Sunday ready checks FAILED")
    assert "EURJPY candles arriving: no 5-minute candle stored" in text
    assert "FAIL EURJPY candles arriving" in text and "OK   EURUSD candle store checks" in text


@pytest.mark.parametrize("change,failed", [
    ({"logged_in": False}, "Logged in to IG: not logged in"),
    ({"connected": False}, "Price stream connected: not connected"),
    ({"remaining": 1500}, "IG history allowance: 1500 of 10000 left"),
    ({"blocked": True}, "IG history allowance: BLOCKED: blocked until 2026-11-20T00:00:00Z"),
])
def test_any_failed_check_is_named_in_a_problem_alert(st, change, failed):
    s = stores(st)
    for p, close in (("EURUSD", "11650.0"), ("EURJPY", "16234.5")):
        s[p].add(C(T(2026, 11, 8, 21, 0), close))
    http, clock = PretendTelegram(), Clock(T(2026, 11, 8, 21, 5, 2))
    ReadyAlerts(st, sent_alerts(st, http, clock), lambda: ctx_for(st, s, now=clock, **change), now=clock).tick()
    (text,) = http.texts
    assert text.startswith("AutoBot PROBLEM: Sunday ready checks FAILED") and failed in text


def test_a_store_problem_fails_the_store_check(st):
    s = stores(st)
    for p in s:
        s[p].add(C(T(2026, 11, 9, 5, 50)))
        s[p].add(C(T(2026, 11, 9, 5, 40)))              # 05:45 missing and not recorded
    checks = run_checks(ctx_for(st, s), T(2026, 11, 9, 6, 0, 30))
    bad = [c for c in checks if not c.ok]
    assert [c.name for c in bad] == ["EURUSD candle store checks", "EURJPY candle store checks"]
    assert "1 gap(s) not recorded" in bad[0].detail


def _day_stores(st):
    s = stores(st)
    sun = T(2026, 11, 8)                       # Monday's pivots come from the short Sunday candle, as on IG's chart
    for p, base in (("EURUSD", 11650), ("EURJPY", 16200)):
        sell = (D(base), D(base + 30), D(base - 30), D(base))
        s[p].add(Candle("1d", sun, T(2026, 11, 9), *(x + 1 for x in sell), *sell, 36, 36))
        for i in range(4):
            s[p].add(C(T(2026, 11, 9, 5, 40) + i * timedelta(minutes=5), str(base)))
    return s


def test_daily_ready_at_06_00_on_a_weekday_with_pivots_and_direction(st, monkeypatch):
    import analyser.report as report
    s = _day_stores(st)

    def analysed(ps, store, now):
        return SimpleNamespace(direction=SimpleNamespace(side="sell side", reason="price below both"),
                               data=SimpleNamespace(state="ready", describe=lambda: "ready"))
    monkeypatch.setattr(report, "analyse", analysed)
    http, clock = PretendTelegram(), Clock(T(2026, 11, 9, 5, 59, 59))           # Monday, GMT
    ready = ReadyAlerts(st, sent_alerts(st, http, clock), lambda: ctx_for(st, s, now=clock), now=clock)
    ready.tick()
    assert http.posts == []
    clock.t = T(2026, 11, 9, 6, 0, 1)
    ready.tick()
    (text,) = http.texts
    assert text.startswith("AutoBot READY for the day (Mon 09 Nov 2026)")
    # pivot (H + L + C) / 3 from Sunday's sell candle; EURUSD 11650, EURJPY 16200
    assert "EURUSD levels: R3 11740.0, R2 11710.0, R1 11680.0, Pivot 11650.0, S1 11620.0, S2 11590.0, S3 11560.0" in text
    assert "EURJPY levels: R3 16290.0" in text and "Pivot 16200.0" in text
    assert "EURUSD direction: sell side (price below both)" in text and "OK   EURJPY analyser data: ready" in text
    clock.t += timedelta(hours=1)
    ready.tick()
    assert len(http.posts) == 1                                                  # once a day


def test_daily_ready_with_the_analyser_not_ready_is_a_problem_alert(st):
    s = _day_stores(st)
    http, clock = PretendTelegram(), Clock(T(2026, 11, 9, 6, 0, 1))
    ReadyAlerts(st, sent_alerts(st, http, clock), lambda: ctx_for(st, s, now=clock), now=clock).tick()
    (text,) = http.texts
    assert text.startswith("AutoBot PROBLEM: Daily ready checks FAILED (Mon 09 Nov 2026)")
    assert "EURUSD analyser data: out of date: 1h: newest candle ends none stored" in text


def test_no_daily_message_at_the_weekend_or_when_the_service_starts_too_late(st):
    s = _day_stores(st)
    for when in (T(2026, 11, 7, 6, 1), T(2026, 11, 8, 6, 1), T(2026, 11, 10, 7, 1)):   # Sat, Sun, Tue 07:01
        http, clock = PretendTelegram(), Clock(when)
        ReadyAlerts(st, sent_alerts(st, http, clock), lambda: ctx_for(st, s, now=clock), now=clock).tick()
        assert http.posts == [], when


def test_the_daily_message_follows_uk_time_in_summer(st):
    s = _day_stores(st)
    http, clock = PretendTelegram(), Clock(T(2026, 7, 6, 4, 59))                # Mon 6 Jul 05:59 BST
    ready = ReadyAlerts(st, sent_alerts(st, http, clock), lambda: ctx_for(st, s, now=clock), now=clock)
    ready.tick()
    assert http.posts == []
    clock.t = T(2026, 7, 6, 5, 0, 1)                                             # 06:00 BST
    ready.tick()
    assert len(http.posts) == 1


def test_a_ready_check_that_breaks_never_stops_the_service(st):
    def broken():
        raise RuntimeError("pretend")
    ReadyAlerts(st, Alerts(None), broken, now=Clock(T(2026, 11, 9, 6, 1))).tick()


# ---- problem alerts --------------------------------------------------------------------------

def test_the_stream_going_quiet_while_open_is_alerted(st):
    from ig.stream import PriceStream
    from tests.technical.fake_stream import FakeClient, FakeTransport, new_transport
    quiet, clock = [], Clock(T(2026, 11, 9, 10))
    stream = PriceStream(FakeClient(), ("CS.D.EURUSD.TODAY.IP",), st.stream, new_transport, on_tick=print,
                         on_candle=print, now=clock, market_open_since=lambda now: T(2026, 11, 8, 21),
                         wait=lambda s: None, on_quiet=quiet.append)
    stream.start()
    FakeTransport.opened[-1].connect()
    stream.pump()
    clock.t += timedelta(seconds=st.stream.no_prices_warning_seconds)
    stream.check()
    assert len(quiet) == 1 and quiet[0].startswith("NO PRICES from IG for 120 seconds while the market is open")
    stream.check()
    assert len(quiet) == 1                                   # once, until prices come back


def test_a_candle_store_problem_is_alerted(st):
    from prices.feed import PriceFeed
    ps = st.for_pair("EURUSD")
    store = CandleStore(ps.candles.folder, 30)
    store.add(C(T(2026, 11, 9, 10)))
    problems = []
    feed = PriceFeed(ps, store, now=Clock(T(2026, 11, 9, 10, 20)), on_store_problem=problems.append)
    feed.add_five_minute(C(T(2026, 11, 9, 10, 10)))          # 10:05 is missing
    assert problems and problems[0].startswith("EURUSD: GAP in 5m candles during market hours: 1 candle(s) missing")


def test_a_history_block_marker_being_written_is_alerted(st, tmp_path):
    from ig.client import IGClient
    from ig.history import HistoryBlocked, HistoryDoor
    from tests.technical.fake_ig import CREDS, FakeIG, accounts_ok, error, login_ok, switch_ok
    from tests.technical.test_history_door import settings as door_settings
    ig = FakeIG(login_ok(), accounts_ok(), switch_ok(), error(403, "error.public-api.exceeded-account-historical-data-allowance"))
    client = IGClient(st.ig, CREDS, http=ig, sleep=lambda s: None)
    client.connect()
    blocks = []
    door = HistoryDoor(client, door_settings(tmp_path), now=lambda: T(2026, 11, 9, 10), on_block=blocks.append)
    with pytest.raises(HistoryBlocked):
        door.fetch("CS.D.EURUSD.TODAY.IP", "MINUTE_5", T(2026, 11, 4, 10), T(2026, 11, 4, 10, 10), 3, "test")
    assert len(blocks) == 1 and blocks[0].startswith("History block marker written: IG refused")


def test_a_login_failure_that_stops_the_service_is_alerted(st):
    from ig.client import IGClient
    from prices.service import serve
    from tests.technical.fake_ig import CREDS, FakeIG, accounts_ok, login_ok, logout_ok, switch_ok
    from tests.technical.fake_stream import FakeTransport, new_transport
    FakeTransport.opened.clear()
    ig = FakeIG(login_ok(1), accounts_ok(), switch_ok(), login_ok(2), switch_ok(), logout_ok())
    client = IGClient(st.ig, CREDS, http=ig, sleep=lambda x: None)
    http = PretendTelegram()
    alerts = sent_alerts(st, http, lambda: datetime.now(UTC))
    result = {}

    def run():
        try:
            serve(st, client=client, transport_factory=new_transport, stop=threading.Event(),
                  now=lambda: T(2026, 11, 9, 10), logs=False, signals=False, alerts=alerts)
        except SystemExit as e:
            result["code"] = e.code
    th = threading.Thread(target=run)
    th.start()
    import time
    end = time.monotonic() + 5
    while not FakeTransport.opened and time.monotonic() < end:
        time.sleep(0.02)
    FakeTransport.opened[-1].refuse()
    while len(FakeTransport.opened) < 2 and time.monotonic() < end:
        time.sleep(0.02)
    FakeTransport.opened[-1].refuse()
    th.join(10)
    assert result["code"] == 78
    login = [t for t in http.texts if "IG login failure" in t]
    assert len(login) == 1 and login[0].startswith("AutoBot PROBLEM: IG login failure")
    assert "will not restart by itself" in login[0]


# ---- trade messages (for the order sender, when it is built) ------------------------------

def trade(pair="GBPUSD", direction="sell", scale=10000, open_=D("13388.2"), sl=D("13394.2"), tp=D("13288.2")):
    return TradeOpened(pair, direction, D("10"), "slow grind", "trend (slow grind)", open_, sl, tp,
                       T(2026, 11, 6, 13, 5), scale)


def test_the_trade_opened_message_shows_everything():
    text = opened_text(trade())
    assert text.splitlines() == [
        "AutoBot TRADE OPENED: GBPUSD SELL",
        "Size: £10 per pip",
        "Strategy: slow grind",
        "Market state: trend (slow grind)",
        "Open price: 13388.2 (1.33882) at Fri 06 Nov 13:05 GMT",
        "Stop loss: 13394.2 (1.33942)",
        "Take profit: 13288.2 (1.32882)"]


def test_the_trade_closed_message_shows_the_result_profit_or_loss_and_win_or_loss():
    win = TradeClosed(trade(), D("13348.2"), T(2026, 11, 6, 15, 40), "take profit moved to S3; closed at 20:30 rule",
                      D("400"))
    text = closed_text(win)
    assert text.splitlines()[0] == "AutoBot TRADE CLOSED: GBPUSD SELL - WIN +£400.00"
    for line in ("Close price: 13348.2 (1.33482) at Fri 06 Nov 15:40 GMT",
                 "Reason: take profit moved to S3; closed at 20:30 rule", "Profit or loss: +£400.00 (win)",
                 "Open price: 13388.2 (1.33882) at Fri 06 Nov 13:05 GMT", "Stop loss: 13394.2 (1.33942)"):
        assert line in text
    loss = TradeClosed(trade(direction="buy"), D("13382.2"), T(2026, 11, 6, 13, 20), "stop loss", D("-60"))
    assert closed_text(loss).splitlines()[0] == "AutoBot TRADE CLOSED: GBPUSD BUY - LOSS -£60.00"
    assert "Profit or loss: -£60.00 (loss)" in closed_text(loss)
    even = TradeClosed(trade(), D("13388.2"), T(2026, 11, 6, 13, 20), "closed by hand", D("0"))
    assert even.result == "BREAK EVEN"


def test_trade_prices_use_each_pairs_own_scale():
    jpy = trade(pair="EURJPY", scale=1000, open_=D("162345"), sl=D("162405"), tp=D("161345"))
    assert "Open price: 162345 (162.345)" in opened_text(jpy)
    with pytest.raises(ValueError, match="buy or sell"):
        trade(direction="long")


def test_trade_alerts_go_through_telegram(st):
    http = PretendTelegram()
    a = sent_alerts(st, http, Clock(T(2026, 11, 6, 13, 5)))
    a.trade_opened(trade())
    a.trade_closed(TradeClosed(trade(), D("13348.2"), T(2026, 11, 6, 15, 40), "take profit", D("400")))
    assert [t.splitlines()[0] for t in http.texts] == ["AutoBot TRADE OPENED: GBPUSD SELL",
                                                       "AutoBot TRADE CLOSED: GBPUSD SELL - WIN +£400.00"]
