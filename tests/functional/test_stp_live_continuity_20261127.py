"""Review R3.1 (owner's brief, 27 November 2026; review of b84d6d6): live price continuity for the engine-built candle
that stands in for a finished 5-minute candle IG has not published yet (stp/authorise.py catch-up, review R3).

Functional: the real price stream (ig/stream.py PriceStream) and price feed (prices/feed.py) driven through a pretend
IG transport (tests/technical/fake_stream.py); the engine's live path exactly as the price service runs it (once a
second, the feed's latest tick: prices/service.py every_second -> Trading.on_price -> Trading._forming); the real
Trading._place deciding which finished candle it hands to the STP check; then the real STP check
(stp/authorise.py authorise) on a store that does not hold that candle. IG is never contacted.

The rule that must hold: the engine's own candle may stand in for a missing authoritative candle only when live price
coverage of that whole candle is established (every price, on one uninterrupted connection, from before its start);
otherwise the STP check refuses (PD-5). A clean candle seen whole still authorises during IG's normal publication
delay."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from ig.stream import PriceStream
from prices.feed import PriceFeed
from prices.store import CandleStore
from stp.authorise import authorise as REAL_AUTHORISE          # bound before any test replaces it
from tests.technical.fake_stream import SETTINGS, Clock, FakeClient, FakeTransport, new_transport

UTC = timezone.utc
EPIC = SETTINGS.market.epic
B = datetime(2026, 11, 17, 10, 5, tzinfo=UTC)          # the boundary after the 10:00 candle (a Tuesday, market open)
C0 = datetime(2026, 11, 17, 10, 0, tzinfo=UTC)         # the candle IG has not published


@pytest.fixture(autouse=True)
def fresh_transports():
    FakeTransport.opened.clear()


class Live:
    """The stream, the feed and the engine's once-a-second live path (the price service's own wiring)."""

    def __init__(self, tmp, start):
        self.clock = Clock(start)
        self.feed = PriceFeed(SETTINGS, CandleStore(tmp / "candles" / "GBPUSD", 30), now=self.clock)
        kw = {}
        import inspect
        if "on_interruption" in inspect.signature(PriceStream).parameters:          # the corrected wiring
            kw["on_interruption"] = self.feed.interrupted
        self.stream = PriceStream(FakeClient(), (EPIC,), SETTINGS.stream, new_transport,
                                  on_tick=lambda e, f: self.feed.on_tick(f), on_candle=lambda e, f: self.feed.on_candle(f),
                                  on_new_connection=self.feed.new_connection, market_open_since=self.feed.market_open_since,
                                  now=self.clock, wait=lambda s: None, warn=self.feed.warn, **kw)
        self.engine = SimpleNamespace(partial=None, previous_partial=None, partial_covered=False,
                                      previous_covered=False, _last=None)
        if hasattr(self.feed, "live"):
            self.engine.observed = self.feed.live.observed
        self.stream.start()
        self.t = FakeTransport.opened[-1]
        self.t.connect()
        self.stream.pump()

    def second(self):
        """The service's every_second: the engine sees the feed's LATEST tick only (if it is a new one)."""
        from trading.engine import Trading
        tk = self.feed.last_tick
        if tk is not None and tk is not self.engine._last:
            self.engine._last = tk
            Trading._forming(self.engine, tk)

    def prices(self, start, end, sell="13200.0", every=timedelta(seconds=1)):
        t = start
        while t < end:
            self.clock.t = t
            self.t.tick(t, bid=sell, ofr=str(D(sell) + D("1.2")))
            self.stream.pump()
            self.second()
            t += every

    def burst(self, t, sells):
        """Several prices inside one second: the engine's once-a-second sample sees only the last."""
        for k, s in enumerate(sells):
            self.clock.t = t + timedelta(milliseconds=100 * k)
            self.t.tick(self.clock.t, bid=s, ofr=str(D(s) + D("1.2")))
            self.stream.pump()
        self.second()

    def drop(self):
        self.t.drop()
        self.stream.pump()                                   # reconnects at once (wait stubbed): a new connection
        self.t = FakeTransport.opened[-1]

    def reconnect(self):
        self.t.connect()
        self.stream.pump()


def handed_to_stp(live, now, monkeypatch):
    """What the real Trading._place passes to the STP check as the finished candle IG has not published."""
    from trading import engine as eng
    got = {}

    def stp(*a, **k):
        got.update(k)
        from stp.authorise import Verdict
        return Verdict(False, ["captured"])
    monkeypatch.setattr("stp.authorise.authorise", stp)
    from tests.technical.test_stp_integration import auth_settings
    e = live.engine
    for k, v in dict(s=auth_settings(None), store=None, now=lambda: now, replay=False, _last_tick=None,
                     runner=SimpleNamespace(stp=object()),
                     book=SimpleNamespace(decision=lambda *a, **k: None)).items():
        setattr(e, k, v)
    idea = SimpleNamespace(strategy="Bollinger bounce 5m", direction="sell", time=now, entry_price=D("13231"),
                           context={}, steps=[])
    eng.Trading._place(e, idea, None)
    prev = got.get("previous")
    covered = got.get("partial_covered", False)
    part = got.get("partial") if len(got) else None
    return prev, (live.engine.partial if covered else None), covered, part


def stp_check(tmp, now, previous, partial, covered):
    authorise = REAL_AUTHORISE
    from tests.technical.test_stp_lifecycle_review_20261127 import _sell_idea, _state, _store_until
    from tests.technical.test_stp_integration import auth_settings, src
    st = _store_until(B, drop={C0})                          # IG has not published the 10:00 candle
    return authorise(auth_settings(tmp), st, _sell_idea(now), now, src(_state(C0)), partial=partial,
                     previous=previous, partial_covered=covered)


def run_case(tmp_path, monkeypatch, script, now=B + timedelta(milliseconds=400)):
    live = Live(tmp_path, datetime(2026, 11, 17, 9, 50, tzinfo=UTC))
    live.prices(datetime(2026, 11, 17, 9, 50, tzinfo=UTC), C0)          # prices flowing before the candle
    script(live)
    live.clock.t = now
    prev, part, covered, _ = handed_to_stp(live, now, monkeypatch)
    return stp_check(tmp_path, now, prev, part, covered), live


# ---- interruptions: coverage cannot be established -> refuse ---------------------------------------------------------

def test_R31_01_a_disconnection_and_reconnection_inside_the_candle_refuses(tmp_path, monkeypatch):
    def script(live):
        live.prices(C0, C0 + timedelta(minutes=2))
        live.drop()                                           # 10:02: the stream drops ...
        live.clock.t = C0 + timedelta(minutes=3)              # ... the destination (13170) is touched unseen ...
        live.reconnect()                                      # ... 10:03: back, on a new connection
        live.prices(C0 + timedelta(minutes=3), B)
    v, _ = run_case(tmp_path, monkeypatch, script)
    assert not v.allowed and any("PD-5" in r for r in v.reasons)


def test_R31_02_an_interruption_across_the_boundary_before_the_candle_refuses(tmp_path, monkeypatch):
    def script(live):
        live.drop()                                           # 09:59:59 to 10:00:30: no stream across 10:00
        live.clock.t = C0 + timedelta(seconds=30)
        live.reconnect()
        live.prices(C0 + timedelta(seconds=30), B)
    v, _ = run_case(tmp_path, monkeypatch, script)
    assert not v.allowed and any("PD-5" in r for r in v.reasons)


def test_R31_03_a_stall_inside_the_candle_refuses(tmp_path, monkeypatch):
    def script(live):
        from ig.stream import Stalled
        live.prices(C0, C0 + timedelta(minutes=2))
        live.t.emit(Stalled("STALLED"))                       # IG's library: no data for a while
        live.stream.pump()
        live.reconnect()                                      # it recovers (CONNECTED:...STREAMING again)
        live.prices(C0 + timedelta(minutes=3), B)
    v, _ = run_case(tmp_path, monkeypatch, script)
    assert not v.allowed and any("PD-5" in r for r in v.reasons)


def test_R31_04_a_restart_during_the_candle_refuses(tmp_path, monkeypatch):
    live = Live(tmp_path, C0 + timedelta(minutes=2))         # the service starts at 10:02
    live.prices(C0 + timedelta(minutes=2), B)
    now = B + timedelta(milliseconds=400)
    live.clock.t = now
    prev, part, covered, _ = handed_to_stp(live, now, monkeypatch)
    v = stp_check(tmp_path, now, prev, part, covered)
    assert not v.allowed and any("PD-5" in r for r in v.reasons)


# ---- every price counts, not the once-a-second sample ------------------------------------------------------------------

def test_R31_05_a_destination_touch_inside_one_second_is_seen(tmp_path, monkeypatch):
    def script(live):
        live.prices(C0, C0 + timedelta(minutes=2))
        live.burst(C0 + timedelta(minutes=2), ["13169.0", "13200.0"])   # 13170 touched and gone within the second
        live.prices(C0 + timedelta(minutes=2, seconds=1), B)
    v, _ = run_case(tmp_path, monkeypatch, script)
    assert not v.allowed and "primary destination 13170 was reached" in " ".join(v.reasons)


# ---- coverage established: normal publication delay keeps authorising ------------------------------------------------------

def test_R31_06_a_clean_candle_seen_whole_still_authorises_during_igs_publication_delay(tmp_path, monkeypatch):
    v, _ = run_case(tmp_path, monkeypatch, lambda live: live.prices(C0, B))
    assert v.allowed, v.reasons


def test_R31_07_a_late_first_price_after_the_boundary_on_an_unbroken_stream_is_still_whole(tmp_path, monkeypatch):
    def script(live):                                         # a quiet market: no price change 10:00:00-10:00:40
        live.prices(C0 + timedelta(seconds=40), B)
    v, _ = run_case(tmp_path, monkeypatch, script)
    assert v.allowed, v.reasons


def test_R31_08_repeated_identical_prices_do_not_break_coverage(tmp_path, monkeypatch):
    def script(live):
        live.prices(C0, B, every=timedelta(milliseconds=500))   # the same price over and over
    v, _ = run_case(tmp_path, monkeypatch, script)
    assert v.allowed, v.reasons


def test_R31_09_once_ig_publishes_the_candle_the_store_decides(tmp_path, monkeypatch):
    authorise = REAL_AUTHORISE
    from tests.technical.test_stp_lifecycle_review_20261127 import _sell_idea, _state, _store_until
    from tests.technical.test_stp_integration import auth_settings, five, src
    live = Live(tmp_path, datetime(2026, 11, 17, 9, 50, tzinfo=UTC))
    live.prices(datetime(2026, 11, 17, 9, 50, tzinfo=UTC), B)            # the engine saw a clean candle ...
    now = B + timedelta(seconds=2)
    live.clock.t = now
    prev, part, covered, _ = handed_to_stp(live, now, monkeypatch)
    st = _store_until(B)
    st.by_tf["5m"] = [c for c in st.by_tf["5m"] if c.start != C0] + [five(C0, 13200, 13200, 13169, 13185)]
    v = authorise(auth_settings(tmp_path), st, _sell_idea(now), now, src(_state(C0)), partial=part,
                  previous=prev, partial_covered=covered)
    assert not v.allowed and "the Tue 17 Nov 10:00 GMT 5-minute candle" in " ".join(v.reasons)   # IG's candle wins
