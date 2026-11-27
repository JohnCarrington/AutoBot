"""Phase 2 functional regression (owner's approval of 27 November 2026): STP's lifecycle and the STP-authorised trades
of 25-27 November 2026, replayed offline on the frozen production candles and STP's own recorded plans
(tests/stp/lifecycle_replay.py; the same replay on the deployed fadf228 reproduces production's journal for all 32
opportunities with no difference, and authorises all 9 trades with their recorded keys, the duplicate 12:01 included).
IG is never contacted; every file is written to tmp_path.

What the corrected code must do (FL-xx; the brief's mandatory scenarios):
  * the 8 legitimate STP-authorised trades still authorised and opened (25 Nov 17:06 and 20:05; 26 Nov 06:01, 06:30,
    11:40, 12:51, 14:22; 27 Nov 06:55), each on a distinct structural test;
  * the 27 Nov 12:01 BUY refused (test 1 of BUY 13121.3-13131 already traded at 06:55);
  * no republication of that test authorises another trade;
  * the 5-minute bounce and Level Reversal on one setup trade once;
  * the publications that change are only reissues of a place whose destination was just achieved (PD-2)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.stp.lifecycle_replay import FIX, replay, settings, trades

UTC = timezone.utc
END = datetime(2026, 11, 27, 14, 10, tzinfo=UTC)
LEGIT = ["AB261125170604-a4ec4a37", "AB261125200515-c9049665", "AB261126060101-987e099b", "AB261126063004-aaea24e1",
         "AB261126114004-bd34fb67", "AB261126125133-d1518c12", "AB261126142255-04805706", "AB261127065505-8c11a4bc"]
DUPLICATE = "AB261127120127-5755701a"
EXTRA = [
    # Level Reversal on the 5-minute bounce's own 26 Nov 11:40 setup (production: "same signal already traded")
    {"reference": "LR-20261126-1140", "strategy": "level reversal", "direction": "buy", "idea_time": "2026-11-26T11:40:05Z",
     "opened_utc": None, "entry_price": "13100.6", "rejection_candle": "2026-11-26T11:10:00Z"},
    # a later BUY confirmation in the same, still unre-armed test of BUY 13121.3-13131 after the 13:05 re-plan
    {"reference": "BUY-20261127-1320", "strategy": "Bollinger bounce 5m", "direction": "buy",
     "idea_time": "2026-11-27T13:20:15Z", "opened_utc": None, "entry_price": "13127.0",
     "rejection_candle": "2026-11-27T13:10:00Z"},
]


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    return replay(settings(tmp_path_factory.mktemp("replay")), END, ideas=trades() + EXTRA)


def by_ref(run):
    return {o["reference"]: o for o in run["outcomes"]}


def test_FL_A1_the_eight_legitimate_stp_trades_are_still_authorised_and_opened(run):
    o = by_ref(run)
    for ref in LEGIT:
        assert o[ref]["stp_allowed"] and o[ref]["opened"], (ref, o[ref])


def test_FL_A2_each_legitimate_trade_is_on_a_distinct_structural_test(run):
    o = by_ref(run)
    keys = [o[ref]["key"] for ref in LEGIT]
    assert len(set(keys)) == len(keys)
    for i, a in enumerate(LEGIT):
        for b in LEGIT[i + 1:]:
            assert not set(o[a]["signal"].split("|")) & set(o[b]["signal"].split("|")), (a, b)


def test_FL_A3_the_duplicate_12_01_buy_is_refused(run):
    d = by_ref(run)[DUPLICATE]
    assert d["opened"] is False
    assert (not d["stp_allowed"]) or d.get("rule_11")


def test_FL_A4_no_republication_authorises_another_trade_on_the_consumed_test(run):
    later = by_ref(run)["BUY-20261127-1320"]
    assert later["opened"] is False


def test_FL_A5_the_27_nov_06_55_buy_and_the_26_nov_11_40_buy_remain_valid(run):
    o = by_ref(run)
    assert o["AB261127065505-8c11a4bc"]["opened"] and o["AB261127065505-8c11a4bc"]["test"] == 1
    assert o["AB261126114004-bd34fb67"]["opened"] and o["AB261126114004-bd34fb67"]["test"] == 2


def test_FL_A6_the_5m_bounce_and_level_reversal_cannot_both_trade_one_test(run):
    lr = by_ref(run)["LR-20261126-1140"]
    assert lr["stp_allowed"] and lr["opened"] is False and lr["rule_11"]


def test_FL_A7_the_25_nov_17_06_buy_is_valid(run):
    o = by_ref(run)["AB261125170604-a4ec4a37"]
    assert o["opened"] and o["key"] == "STP-GBPUSD-20261125-1700-34#t1"


def test_FL_A8_only_reissues_of_a_place_whose_destination_was_just_achieved_are_withheld(run):
    """Against production's own journal: every opportunity production published from 25 Nov 09:15 is published again
    with the same lifecycle, except reissues that the destination-zone rule (PD-2) withholds."""
    prod_iss = {}
    for line in (FIX / "migration" / "planner" / "issued.jsonl").read_text().splitlines():
        x = json.loads(line)
        prod_iss[x["id"]] = (x["trade"], x["entry_zone"]["low"], x["entry_zone"]["high"])
    created = lambda evs: {e["id"]: e["time_utc"] for e in evs if e["event"] == "created"}    # noqa: E731
    prod = [e for e in json.loads((FIX / "journal_opportunities.json").read_text())
            if "2026-11-25T09:15:00Z" <= e["time_utc"] <= "2026-11-27T14:13:00Z"]
    key_p = {(t, *prod_iss[i][:2]) for i, t in created(prod).items() if i in prod_iss}
    key_n = {(t, *run["issued"][i][:2]) for i, t in created(run["events"]).items() if i in run["issued"]}
    assert key_n <= key_p                                              # nothing new is published
    assert sorted(key_p - key_n) == [
        ("2026-11-26T20:00:03Z", "SELL", "13115.1"), ("2026-11-26T21:00:03Z", "SELL", "13115.1"),
        ("2026-11-27T00:00:04Z", "SELL", "13108.5"), ("2026-11-27T02:00:03Z", "SELL", "13108.5"),
        ("2026-11-27T12:00:03Z", "BUY", "13121.3"), ("2026-11-27T13:05:03Z", "BUY", "13121.3")]


def test_FL_A9_the_session_sweep_and_every_ungated_strategy_never_reach_stp():
    from stp.gate import gated
    s = SimpleNamespace(switches=SimpleNamespace(stp_authorises_entries=True),
                        stp_authorisation=SimpleNamespace(strategies=["Bollinger bounce", "Bollinger bounce 5m",
                                                                      "level reversal"]))
    for strat in ("session sweep", "slow grind", "EMA pullback", "breakout", "Asian range breakout", "range trade",
                  "New York open reversal"):
        assert not gated(s, strat)
    off = SimpleNamespace(switches=SimpleNamespace(stp_authorises_entries=False), stp_authorisation=s.stp_authorisation)
    assert not gated(off, "Bollinger bounce 5m")           # STP off: the gated strategies' admission is as before


# ---- PD-4 on the real production state of 27 Nov 14:15 -----------------------------------------------------------------

def test_FL_M1_after_the_migration_the_live_1305_58_cannot_authorise_test_1_again(tmp_path):
    from orders.sender import OrderSender
    from planner.migrate_lineage import build
    from planner.opportunities import OpportunityKeeper
    from safety.rules import _one_signal
    from stp.authorise import authorise
    from tests.stp.lifecycle_replay import fixture_store
    s = settings(tmp_path)
    store = fixture_store()
    store.t = datetime(2026, 11, 27, 14, 15, tzinfo=UTC)
    m = build(s, store, FIX / "migration" / "planner", FIX / "migration", FIX / "migration", store.t)
    L = m["lineages"]["STP-GBPUSD-20261127-0300-56"]
    assert m["opportunity_lineage"] == {"STP-GBPUSD-20261127-1305-58": "STP-GBPUSD-20261127-0300-56"}
    assert L["aliases"] == {"1": ["STP-GBPUSD-20261127-1200-57#t1"]}
    assert L["consumed"] == {"1": ["AB261127065505-8c11a4bc", "AB261127120127-5755701a"]}
    d = Path(s.planner.folder) / "GBPUSD"
    d.mkdir(parents=True)
    (d / "current.json").write_text((FIX / "current_20261127_1415.json").read_text())
    (d / "lineage_map.json").write_text(json.dumps(m))
    t = datetime(2026, 11, 27, 14, 15, 3, tzinfo=UTC)
    store.t = t
    OpportunityKeeper(s, store).run(t)
    st = json.loads((d / "current.json").read_text())
    o = next(x for x in st["opportunities"] if x["id"] == "STP-GBPUSD-20261127-1305-58")
    assert o["lineage"] == "STP-GBPUSD-20261127-0300-56"
    idea = SimpleNamespace(strategy="Bollinger bounce 5m", direction="buy", time=t, entry_price=D("13127.0"),
                           context={"rejection_candle": "2026-11-27T13:10:00Z"}, steps=[])
    v = authorise(s, store, idea, t, SimpleNamespace(state_at=lambda x=None: st))
    assert v.allowed and v.stp_key == "STP-GBPUSD-20261127-0300-56#t1"
    assert "STP-GBPUSD-20261127-1200-57#t1" in v.signal.split("|")
    used = {}
    for line in (FIX / "migration" / "orders.jsonl").read_text().splitlines():
        r = json.loads(line)
        if r["event"] == "sending":
            used[r["reference"]] = SimpleNamespace(signal=r["signal"], strategy=r["strategy"])
    for old in ({"x": used["AB261127065505-8c11a4bc"]}, {"x": used["AB261127120127-5755701a"]}):
        u = OrderSender.used_signals(SimpleNamespace(unresolved={}, trades=old))
        assert _one_signal(SimpleNamespace(switches=SimpleNamespace(one_signal_one_trade=True)),
                           SimpleNamespace(context={"signal": v.signal}), u)     # either old trade alone refuses it
    OpportunityKeeper(s, store).run(t)                                          # applied once: idempotent on restart
    evs = [json.loads(x) for x in (d / "recommendations.jsonl").read_text().splitlines()]
    assert sum(e["event"] == "lineage map applied" for e in evs) == 1
