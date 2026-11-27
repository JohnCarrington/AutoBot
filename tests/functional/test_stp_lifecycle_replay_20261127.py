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
  * the publications that change are only reissues of a place whose destination was just achieved (PD-2);
  * WP2: each STP-authorised trade is acknowledged once IG confirms it (orders/executions.py), and an opportunity whose
    destination is reached after its trade ends COMPLETED "after a confirmed trade entry" (25 Nov 1700-34: production
    recorded "destination reached before entry"); each other destination ending says which circumstance applied."""

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
    # review of fec364b: a completed place's republication is withheld only until its zone re-arms (D-25 / P-C8); the
    # only ones left are the reissues of 0300-56's test 1, which never re-armed (12:00 and 13:05 on 27 Nov)
    assert sorted(key_p - key_n) == [("2026-11-27T12:00:03Z", "BUY", "13121.3"), ("2026-11-27T13:05:03Z", "BUY", "13121.3")]


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


# ---- WP2: lifecycle accuracy on the real days ---------------------------------------------------------------------------

def _ends(run):
    return {e["id"]: e for e in run["events"] if e.get("id") and e["event"] in ("completed", "invalidated")}


def test_FL_B1_the_25_nov_1700_34_with_its_17_06_trade_ends_completed_after_a_confirmed_trade_entry(run):
    e = _ends(run)["STP-GBPUSD-20261125-1700-34"]
    assert e["event"] == "completed" and e["destination_case"] == "after_trade"
    assert "AB261125170604-a4ec4a37" in e["why"] and e["time_utc"] == "2026-11-25T18:20:00Z"


def test_FL_B2_every_destination_ending_names_its_circumstance_truthfully(run):
    cases = {}
    for e in _ends(run).values():
        if e.get("destination_case"):
            cases.setdefault(e["destination_case"], []).append(e)
    assert set(cases) <= {"before_zone", "after_zone_at_or_before_creation", "after_zone", "after_trade"}
    for e in cases.get("after_zone_at_or_before_creation", []):
        assert "without reaching the zone" not in e["why"] and e["event"] == "invalidated"
    traded = {o["opportunity"] for o in run["outcomes"] if o["opened"]}
    for e in _ends(run).values():
        if e["id"] in traded and e.get("destination_case"):
            assert e["destination_case"] == "after_trade", e        # never "before entry" once a trade was entered


def test_FL_B3_every_opened_trade_is_acknowledged_once_and_its_test_recorded_as_consumed(run):
    snap = run["snapshots"][-1]
    consumed = {ref for L in snap["lineages"].values() for refs in (L.get("consumed") or {}).values() for ref in refs}
    opened = {o["reference"] for o in run["outcomes"] if o["opened"]}
    assert opened == consumed and len(snap.get("acks_seen") or []) == len(opened)


# ---- review R2 on the real days: destinations revised while live -----------------------------------------------------

def test_FL_D1_the_lineage_keeps_the_destination_each_opportunity_actually_reached(run):
    """25 Nov: 0400-27 was published toward 13050 and revised to 13053.7, then completed at 11:45; 1200-29 toward
    13053.7, revised to 13058.1, completed at 13:10. The lineage records the achieved ones (review R2)."""
    snap = run["snapshots"][-1]
    m = {x["id"]: x for L in snap["lineages"].values() for x in L["members"]}
    assert m["STP-GBPUSD-20261125-0400-27"]["primary"] == "13053.7"
    assert m["STP-GBPUSD-20261125-1200-29"]["primary"] == "13058.1"


def test_FL_D2_the_migration_takes_the_revised_destinations_from_the_record():
    from planner.migrate_lineage import history
    h = {o["id"]: o for o in history(FIX / "migration" / "planner", "2026-11-24T00:00:00Z")}
    assert h["STP-GBPUSD-20261125-0400-27"]["primary"] == "13053.7"
    assert h["STP-GBPUSD-20261125-1200-29"]["primary"] == "13058.1"


# ---- review of fec364b: a genuinely new structural test after a completion stays tradable ------------------------------

@pytest.fixture(scope="module")
def run1830(tmp_path_factory):
    """The replay to 18:30 on the 18:29 production copies (fixtures/lifecycle_20261127_1830), the outage as lived."""
    from tests.stp import lifecycle_replay as R
    old = R.use_fixtures(R.FIX.parent / "lifecycle_20261127_1830")
    try:
        return R.replay(R.settings(tmp_path_factory.mktemp("r1830")), datetime(2026, 11, 27, 18, 30, tzinfo=UTC),
                        down=(datetime(2026, 11, 27, 12, 1, 58, tzinfo=UTC), datetime(2026, 11, 27, 12, 20, tzinfo=UTC)))
    finally:
        R.use_fixtures(old)


def test_FL_E1_the_27_nov_15_00_sell_on_a_new_test_after_many_re_arms_is_published_and_fails_closed_on_the_gap(run1830):
    """SELL 13108.5-13119.1 toward 13103 at 15:00 on 27 Nov: the place's last completion toward 13103 was on 26 Nov at
    14:45, and the zone re-armed many times since: a genuinely new structural test, which the duplicate rule must not
    withhold (brief, section 2), so it is PUBLISHED. Its lineage's D-25 count, though, passes through the 27 Nov 12:00
    hour, built from 9 of 12 candles with its stored part clear of the zone: the missing candles could hide a test or
    a re-arm, so the 15:11 idea is refused (D-R2, fail closed) until IG's candles are recovered (Saturday, OP-1)."""
    pub = [e for e in run1830["events"] if e["event"] == "created" and e["time_utc"] == "2026-11-27T15:00:02Z"
           and run1830["issued"].get(e["id"], ("",))[0] == "SELL"]
    assert pub, "the 15:00 SELL is published"
    o = {x["reference"]: x for x in run1830["outcomes"]}["AB261127151117-d13449c1"]
    assert not o["opened"] and "uncertain hour(s) 2026-11-27T12:00:00Z" in " ".join(o["reasons"]), o


def test_FL_E2_the_republications_of_the_still_unre_armed_test_1_stay_withheld(run1830):
    o = {x["reference"]: x for x in run1830["outcomes"]}
    assert o["AB261127120127-5755701a"]["opened"] is False
    created = [(e["time_utc"], run1830["issued"].get(e["id"])) for e in run1830["events"] if e["event"] == "created"]
    assert not [c for c in created if c[0] in ("2026-11-27T12:00:03Z", "2026-11-27T13:05:03Z") and c[1] and c[1][0] == "BUY"]
