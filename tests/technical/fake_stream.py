"""A pretend IG price stream and helpers for the price and candle tests.
Nothing here touches the network."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from config.settings_loader import load_settings
from ig.stream import (CandleUpdate, Connected, Dropped, Refused, Subscribed,
                       SubscriptionFailed, TickUpdate, candle_item, tick_item)
from prices.model import Candle

UTC = timezone.utc
SETTINGS = load_settings()
STREAMING = "https://pretend-streaming.example"
EPIC = SETTINGS.market.epic


def T(y, mo, d, h=0, mi=0, s=0) -> datetime:
    return datetime(y, mo, d, h, mi, s, tzinfo=UTC)


class Clock:
    def __init__(self, t: datetime):
        self.t = t

    def __call__(self) -> datetime:
        return self.t

    def advance(self, **kw) -> None:
        self.t += timedelta(**kw)


class FakeTransport:
    """One pretend connection. The test makes it send events with send()."""
    opened: list["FakeTransport"] = []

    def __init__(self):
        self.subscriptions_requested = 0
        self.closed = False
        self.emit = None
        self.args = None

    def open(self, endpoint, user, password, epic, emit):
        self.args = (endpoint, user, password, epic)
        self.emit = emit
        self.subscriptions_requested = 2
        FakeTransport.opened.append(self)

    def close(self):
        self.closed = True

    # what IG would send
    def connect(self):
        self.emit(Connected("CONNECTED:WS-STREAMING"))
        self.emit(Subscribed(tick_item(EPIC)))
        self.emit(Subscribed(candle_item(EPIC)))

    def drop(self, why="DISCONNECTED:WILL-RETRY"):
        self.emit(Dropped(why))

    def refuse(self, code=1):
        self.emit(Refused(code, "user/password check failed"))

    def sub_fail(self):
        self.emit(SubscriptionFailed(candle_item(EPIC), 21, "bad item"))

    def tick(self, t: datetime, bid="1.31000", ofr="1.31010"):
        self.emit(TickUpdate({"BID": bid, "OFR": ofr, "UTM": str(int(t.timestamp() * 1000))}))

    def candle(self, start: datetime, finished=True, bid=("1.31000", "1.31050", "1.30950", "1.31020"),
               ofr=("1.31010", "1.31060", "1.30960", "1.31030")):
        f = {"UTM": str(int(start.timestamp() * 1000)), "CONS_END": "1" if finished else "0",
             "CONS_TICK_COUNT": "42"}
        for name, v in zip(("OPEN", "HIGH", "LOW", "CLOSE"), bid):
            f[f"BID_{name}"] = v
        for name, v in zip(("OPEN", "HIGH", "LOW", "CLOSE"), ofr):
            f[f"OFR_{name}"] = v
        self.emit(CandleUpdate(f))


def new_transport():
    return FakeTransport()


class FakeClient:
    """Stands in for ig.client.IGClient as the stream uses it."""

    def __init__(self):
        self.streaming_endpoint = STREAMING
        self.relogins = 0
        self.fail_relogin = False
        self.token = 1

    def stream_login(self):
        return "ACC-SECRET-1234", f"CST-secret{self.token}|XST-secret{self.token}"

    def relogin_for_stream(self):
        self.relogins += 1
        if self.fail_relogin:
            from ig.errors import IGLoginFailure
            raise IGLoginFailure("invalid-details", "pretend failure")
        self.token += 1


def five(start: datetime, bo="1.31010", bh="1.31060", bl="1.30960", bc="1.31030",
         so="1.31000", sh="1.31050", sl="1.30950", sc="1.31020", tf="5m", minutes=5) -> Candle:
    D = Decimal
    return Candle(tf, start, start + timedelta(minutes=minutes), D(bo), D(bh), D(bl), D(bc),
                  D(so), D(sh), D(sl), D(sc))
