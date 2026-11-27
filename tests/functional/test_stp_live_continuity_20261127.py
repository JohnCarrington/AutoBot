"""Review R3.1 and its review (owner's briefs, 27 November 2026; reviews of b84d6d6 and fec364b): a finished 5-minute
candle IG has not yet published, at the moment of an STP authorisation.

IG's tick subscription is DISTINCT with filtered dispatching (ig/stream.py): neither IG nor the Lightstreamer library
guarantees that every price change reaches the bot, and lost updates are not reported in that mode. So a candle built
from the live prices cannot be shown to be complete, and it never stands in for IG's candle: until IG's completed
candle is stored, the STP check refuses (PD-5). Every scenario here, interrupted or not, therefore refuses before IG
publishes, and the check decides on IG's own candle once it is stored.

Functional: the real price stream (ig/stream.py PriceStream) and price feed (prices/feed.py) through a pretend IG
transport (tests/technical/fake_stream.py); the engine's live path as the price service runs it (once a second, the
feed's latest tick); the real Trading._place; then the real STP check (stp/authorise.py) on a store with and without
IG's candle. IG is never contacted."""

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
        self.stream = PriceStream(FakeClient(), (EPIC,), SETTINGS.stream, new_transport,
                                  on_tick=lambda e, f: self.feed.on_tick(f), on_candle=lambda e, f: self.feed.on_candle(f),
                                  on_new_connection=self.feed.new_connection, market_open_since=self.feed.market_open_since,
                                  now=self.clock, wait=lambda s: None, warn=self.feed.warn, **kw)
        self.engine = SimpleNamespace(partial=None, _last=None)
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
    """What the real Trading._place passes to the STP check (the forming candle and the live price)."""
    from trading import engine as eng
    got = {}

    def stp(*a, **k):
        got.update(k, a=a)
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
    args = got.get("a") or ()
    assert set(got) <= {"a"}, f"the engine passes the STP check more than the forming candle and tick: {set(got)}"
    return args[5] if len(args) > 5 else None


def stp_check(tmp, now, partial, published=None):
    from tests.technical.test_stp_lifecycle_review_20261127 import _sell_idea, _state, _store_until
    from tests.technical.test_stp_integration import auth_settings, src
    st = _store_until(B, drop={C0})                          # IG has not published the 10:00 candle ...
    if published is not None:
        st.by_tf["5m"].append(published)                      # ... or has
    return REAL_AUTHORISE(auth_settings(tmp), st, _sell_idea(now), now, src(_state(C0)), partial=partial)


def run_case(tmp_path, monkeypatch, script, now=B + timedelta(milliseconds=400), published=None):
    live = Live(tmp_path, datetime(2026, 11, 17, 9, 50, tzinfo=UTC))
    live.prices(datetime(2026, 11, 17, 9, 50, tzinfo=UTC), C0)          # prices flowing before the candle
    script(live)
    live.clock.t = now
    part = handed_to_stp(live, now, monkeypatch)
    return stp_check(tmp_path, now, part, published), live


def refused(v):
    return (not v.allowed) and any("PD-5" in r for r in v.reasons)


# ---- interruptions: coverage cannot be established -> refuse ---------------------------------------------------------

def test_R31_01_a_disconnection_and_reconnection_inside_the_candle_refuses(tmp_path, monkeypatch):
    def script(live):
        live.prices(C0, C0 + timedelta(minutes=2))
        live.drop()                                           # 10:02: the stream drops ...
        live.clock.t = C0 + timedelta(minutes=3)              # ... the destination (13170) is touched unseen ...
        live.reconnect()                                      # ... 10:03: back, on a new connection
        live.prices(C0 + timedelta(minutes=3), B)
    v, _ = run_case(tmp_path, monkeypatch, script)
    assert refused(v)


def test_R31_02_an_interruption_across_the_boundary_before_the_candle_refuses(tmp_path, monkeypatch):
    def script(live):
        live.drop()                                           # 09:59:59 to 10:00:30: no stream across 10:00
        live.clock.t = C0 + timedelta(seconds=30)
        live.reconnect()
        live.prices(C0 + timedelta(seconds=30), B)
    v, _ = run_case(tmp_path, monkeypatch, script)
    assert refused(v)


def test_R31_03_a_quiet_spell_inside_the_candle_refuses(tmp_path, monkeypatch):
    def script(live):                                         # no prices 10:02-10:03 (a stall or a quiet market:
        live.prices(C0, C0 + timedelta(minutes=2))            # the bot cannot tell which)
        live.prices(C0 + timedelta(minutes=3), B)
    v, _ = run_case(tmp_path, monkeypatch, script)
    assert refused(v)


def test_R31_04_a_restart_during_the_candle_refuses(tmp_path, monkeypatch):
    live = Live(tmp_path, C0 + timedelta(minutes=2))         # the service starts at 10:02
    live.prices(C0 + timedelta(minutes=2), B)
    now = B + timedelta(milliseconds=400)
    live.clock.t = now
    v = stp_check(tmp_path, now, handed_to_stp(live, now, monkeypatch))
    assert refused(v)


# ---- every price counts, not the once-a-second sample ------------------------------------------------------------------

def test_R31_05_a_destination_touch_inside_one_second_is_seen(tmp_path, monkeypatch):
    def script(live):
        live.prices(C0, C0 + timedelta(minutes=2))
        live.burst(C0 + timedelta(minutes=2), ["13169.0", "13200.0"])   # 13170 touched and gone within the second
        live.prices(C0 + timedelta(minutes=2, seconds=1), B)
    v, _ = run_case(tmp_path, monkeypatch, script)
    assert refused(v)
    from tests.technical.test_stp_integration import five
    v, _ = run_case(tmp_path / "b", monkeypatch, script, published=five(C0, 13200, 13200, 13169, 13200))
    assert not v.allowed and "primary destination 13170 was reached" in " ".join(v.reasons)   # IG's candle has it


# ---- an unbroken, clean stream: still refused until IG publishes; authorised on IG's clean candle ----------------------

def test_R31_06_a_clean_candle_is_refused_until_ig_publishes_it_and_authorised_once_it_does(tmp_path, monkeypatch):
    from tests.technical.test_stp_integration import five
    v, _ = run_case(tmp_path, monkeypatch, lambda live: live.prices(C0, B))
    assert refused(v)                                         # IG's normal publication delay: fail closed
    v, _ = run_case(tmp_path / "b", monkeypatch, lambda live: live.prices(C0, B),
                    now=B + timedelta(seconds=1), published=five(C0, 13200, 13201, 13199, 13200))
    assert v.allowed, v.reasons


def test_R31_07_a_late_first_price_after_the_boundary_is_refused_until_ig_publishes(tmp_path, monkeypatch):
    def script(live):                                         # a quiet market: no price change 10:00:00-10:00:40
        live.prices(C0 + timedelta(seconds=40), B)
    v, _ = run_case(tmp_path, monkeypatch, script)
    assert refused(v)


def test_R31_08_repeated_identical_prices_are_refused_until_ig_publishes(tmp_path, monkeypatch):
    def script(live):
        live.prices(C0, B, every=timedelta(milliseconds=500))   # the same price over and over
    v, _ = run_case(tmp_path, monkeypatch, script)
    assert refused(v)


def test_R31_09_once_ig_publishes_the_candle_the_store_decides(tmp_path, monkeypatch):
    from tests.technical.test_stp_integration import five
    v, _ = run_case(tmp_path, monkeypatch, lambda live: live.prices(C0, B), now=B + timedelta(seconds=2),
                    published=five(C0, 13200, 13200, 13169, 13185))
    assert not v.allowed and "the Tue 17 Nov 10:00 GMT 5-minute candle" in " ".join(v.reasons)   # IG's candle wins


# ---- review of fec364b: completeness of a locally built candle cannot be established -> IG's candle, or refuse ----------

C1 = datetime(2026, 11, 17, 10, 5, tzinfo=UTC)          # the candle after a whole quiet one


def test_R31_10_after_a_whole_quiet_interval_the_next_unpublished_candle_is_not_rebuilt_without_its_carried_open(
        tmp_path, monkeypatch):
    """No price change 10:00-10:05:30 on an unbroken stream: the price carried into the 10:05 candle (13169.5, at the
    destination 13170) is its open. A local candle that opens at the first NEW price (13200) omits it."""
    from tests.technical.test_stp_lifecycle_review_20261127 import _sell_idea, _store_until
    from tests.technical.test_stp_integration import auth_settings, auth_state, opp, src
    live = Live(tmp_path, datetime(2026, 11, 17, 9, 50, tzinfo=UTC))
    live.prices(datetime(2026, 11, 17, 9, 50, tzinfo=UTC), datetime(2026, 11, 17, 9, 59, 59, tzinfo=UTC))
    live.prices(datetime(2026, 11, 17, 9, 59, 59, tzinfo=UTC), C0, sell="13169.5")   # the last price before 10:00
    live.prices(C1 + timedelta(seconds=30), C1 + timedelta(minutes=5), sell="13200.0")
    now = C1 + timedelta(minutes=5, milliseconds=400)                  # IG has not yet published the 10:05 candle
    live.clock.t = now
    part = handed_to_stp(live, now, monkeypatch)
    st = _store_until(C1 + timedelta(minutes=5), drop={C1})
    s_ = auth_state(opp("SELL", (13240, 13250)), written=C1 + timedelta(seconds=3), m5=C1)
    v = REAL_AUTHORISE(auth_settings(tmp_path), st, _sell_idea(now), now, src(s_), partial=part)
    assert refused(v)


def test_R31_11_a_finished_candle_ig_has_not_published_is_never_replaced_by_a_local_one(tmp_path, monkeypatch):
    """IG's tick subscription (DISTINCT, filtered dispatching) does not guarantee every price change reaches the bot, so
    a locally built candle's completeness cannot be established: until IG's candle is stored, the check refuses."""
    v, _ = run_case(tmp_path, monkeypatch, lambda live: live.prices(C0, B))
    assert refused(v)
