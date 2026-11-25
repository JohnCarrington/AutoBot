"""Functional regression on the bot's own IG candles of Wednesday 25 November 2026 (owner, 25 November 2026): the two
BUY bounces at 10:10 UTC against STP's 10:00 BUY opportunity, zone 1.30473-1.30551 (production id
STP-GBPUSD-20261125-1000-28). Live (Stage A, STP_AUTHORISES_ENTRIES off) both were refused by rule 3. Under Stage B:
  * the hourly Bollinger bounce (rejection candle 10:00, low 1.30537, inside the zone; entry 1.30628 at 10:10) is
    authorised by STP (key "buy 2026-11-25T10:00:00Z|<id>#t1"), and rule 3 is not applied to it (OD-05, OD-30);
  * the Bollinger bounce 5m (rejection candle 09:55; entry 1.30639) is authorised against the same opportunity and test
    (key "<id>#t1") and then refused by rule 11 as a duplicate of the hourly bounce's trade (OD-32).
The STP file is the tracker's own as written at 10:05:03 (tests/stp/fixtures/stp_current_20261125_1005.json), the
one an entry at 10:10 reads; the check's catch-up covers the 10:05 candle. Read only; IG is never contacted."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace

import pytest

UTC = timezone.utc
CANDLES = Path("/opt/autobot/data/candles/GBPUSD/5m/2026-11-25.csv")
FIXTURE = Path(__file__).resolve().parents[1] / "stp" / "fixtures" / "stp_current_20261125_1005.json"
pytestmark = pytest.mark.skipif(not CANDLES.exists(), reason="the recorded 25 November candles are not on this machine")
OPP = "STP-GBPUSD-20261125-1000-30"


def _setup(tmp_path):
    from tests.stp.harness import live_settings, live_store
    s = live_settings(tmp_path, stp_opportunities=True, stp_bidirectional=True, stp_authorises_entries=True)
    st = json.loads(FIXTURE.read_text())
    src = SimpleNamespace(state_at=lambda t=None: st, version=lambda t=None: st["written_utc"])
    return s, live_store(s), src


def _idea(strategy, at, price, ctx):
    return SimpleNamespace(strategy=strategy, direction="buy", time=at, entry_price=D(price), context=dict(ctx), steps=[],
                           state="trend", state_direction="down", trend_type="slow grind",
                           state_since=datetime(2026, 11, 25, 10, 5, tzinfo=UTC))


HOURLY = ("Bollinger bounce", datetime(2026, 11, 25, 10, 10, 2, tzinfo=UTC), "13062.8",
          {"furthest": "13053.7", "rejection_close": "13060.2", "rejection_candle": "2026-11-25T10:00:00Z",
           "signal": "buy 2026-11-25T10:00:00Z"})
FIVE = ("Bollinger bounce 5m", datetime(2026, 11, 25, 10, 10, 15, tzinfo=UTC), "13063.9",
        {"rejection_candle": "2026-11-25T09:55:00Z"})


def test_FT_B1_the_hourly_bounce_buy_is_authorised_by_stp_and_rule_3_does_not_veto_it(tmp_path):
    from analyser.market_state import MemoStore
    from stp.authorise import authorise
    from strategies import entry_filters as ef
    s, store, src = _setup(tmp_path)
    i = _idea(*HOURLY)
    v = authorise(s, store, i, i.time, src)
    assert v.allowed, v.reasons
    assert v.opportunity["id"] == OPP and v.opportunity["trade"] == "BUY"
    assert (v.opportunity["entry_zone"]["low"], v.opportunity["entry_zone"]["high"]) == ("13047.3", "13055.1")
    assert v.signal == f"buy 2026-11-25T10:00:00Z|{OPP}#t1" and "counter_trend_tiring" in v.bypass
    plain = ef.check(s, MemoStore(store), _idea(*HOURLY))                  # as live today (Stage A): rule 3 refuses
    assert not plain.allowed and plain.rule == ef.COUNTER_TREND_TIRING
    stp = ef.check(s, MemoStore(store), i, bypass=v.bypass)                # Stage B: STP authorised, rule 3 not applied
    assert stp.allowed and any("counter trend tiring: not applied: STP authorised" in x for x in stp.checked)


def test_FT_B2_the_duplicate_bounce_5m_buy_on_the_same_test_is_refused_by_rule_11(tmp_path):
    from orders.sender import OrderSender
    from safety.rules import _one_signal
    from stp.authorise import authorise
    s, store, src = _setup(tmp_path)
    h, f = _idea(*HOURLY), _idea(*FIVE)
    vh, vf = authorise(s, store, h, h.time, src), authorise(s, store, f, f.time, src)
    assert vh.allowed and vf.allowed and vf.opportunity["id"] == OPP and vf.signal == f"{OPP}#t1"
    # the hourly bounce's trade opened first (its key, both parts counted as used: orders/sender.py used_signals)
    sender = SimpleNamespace(unresolved={}, trades={"AB1": SimpleNamespace(signal=vh.signal, strategy="Bollinger bounce")})
    used = OrderSender.used_signals(sender)
    f.context["signal"] = vf.signal
    assert _one_signal(s, f, used) == ["same signal already traded by Bollinger bounce"]
    h.context["signal"] = vh.signal                                         # and the hourly bounce itself was not a duplicate
    assert _one_signal(s, h, {}) == []
