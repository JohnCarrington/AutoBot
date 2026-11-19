"""The Structural Trade Planner corrections approved by the owner on 18 November 2026:

  D-1   recommendation admission uses the lifecycle's own "destination reached" test (planner/zones.py reached);
  P-C   only market evidence from after a recommendation's creation can activate it (planner/keeper.py five_minute):
        a candle that finished before creation never counts, one that overlapped it is recorded as AMBIGUOUS;
  R-A   the activation's candle timing is recorded; R-B the full structural snapshot is kept in issued.jsonl;
  EVAL  the dashboard's evaluation counts only post-creation activations and lists each correction.

Every lifecycle is made by the real keeper with a scripted planner (as tests/technical/test_planner.py)."""

from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal as D

import pytest

from planner.keeper import ACTIVE, COMPLETED, INVALIDATED, WAITING, Keeper, candle_timing
from planner.zones import reached
from tests.planner_helpers import with_folder
from tests.technical.test_planner import NOW, C, S, Script, T, flat_store, plan_dict

SEC = timedelta(seconds=2)


def K(tmp, store, *plans):
    return Keeper(with_folder(S, tmp / "planner"), store, planner=Script(*plans))


def events(tmp):
    return [json.loads(x) for x in (tmp / "planner" / "GBPUSD" / "recommendations.jsonl").read_text().splitlines()]


def five(t, o, h, low, c):
    return C("5m", t, 1 / 12, o, h, low, c)


def mirror(x):
    """Prices mirrored about 13200 (SELL <-> BUY)."""
    return 26400 - x


# ---- D-1: admission and the destination-reached rule agree ---------------------------------------------------------

@pytest.mark.parametrize("low,expected", [(D("13203.0"), True), (D("13203.1"), False), (D("13201.3"), True)])
def test_d1_the_admission_test_is_the_touch_rule_with_its_3_pip_allowance(low, expected):
    c = five(NOW, 13206, 13207, low, low + 1)                          # a sell's destination zone 13189.7-13200 below
    assert bool(reached(S, c, c.sell_close, D("13189.7"), D("13200"), toward_low=True)) is expected


@pytest.mark.parametrize("high,expected", [(D("13197.0"), True), (D("13196.9"), False)])
def test_d1_is_symmetrical_for_a_buy(high, expected):
    c = five(NOW, 13190, high, 13189, high - 1)                         # a buy's destination zone 13200-13210.3 above
    assert bool(reached(S, c, c.sell_close, D("13200"), D("13210.3"), toward_low=False)) is expected


def test_d1_the_17_november_22_00_and_23_00_candles_count_as_reached_and_20_24_does_not():
    # the real sell-price candles (data/candles GBPUSD): 21:55 low 1.32013 and 22:55 low 1.31989, destination 1.32000
    for o, h, low, c in ((D("13206.5"), D("13207.3"), D("13201.3"), D("13203.5")), (D("13203.4"), D("13208.2"), D("13198.9"), D("13201.6"))):
        assert reached(S, five(NOW, o, h, low, c), c, D("13189.7"), D("13200"), toward_low=True)
    c = five(NOW, D("13209.6"), D("13210.2"), D("13208.3"), D("13209.4"))       # the 20:15 candle before rec 1
    assert reached(S, c, c.sell_close, D("13189.7"), D("13200"), toward_low=True) is None


def test_d1_a_destination_price_has_gone_well_past_stays_on_the_way():
    c = five(NOW, 13180, 13182, 13178, 13180)                           # sell; the whole candle 9 pips below the zone
    assert reached(S, c, c.sell_close, D("13189.7"), D("13200"), toward_low=True) is None


def _plan_with_dest_reached(trade="SELL", primary=13170):
    p = plan_dict(trade=trade, no_rec="the primary destination is already reached", primary=primary)
    p["destination_reached"] = {"primary": str(primary), "how": "the 09:55 candle reached it"}
    return p


@pytest.mark.parametrize("trade", ["SELL", "BUY"])
def test_d1_at_the_hourly_recheck_a_reached_destination_keeps_before_and_after_entry_apart(tmp_path, trade):
    zone, primary = ((13240, 13250), 13170) if trade == "SELL" else ((13150, 13160), 13230)
    touch = five(NOW, 13230, 13238, 13229, 13231) if trade == "SELL" else five(NOW, 13170, 13171, 13162, 13169)
    for active, want, words in ((False, INVALIDATED, "destination reached before entry"), (True, COMPLETED, "after the zone")):
        tmp = tmp_path / f"{trade}{active}"
        K(tmp, flat_store(NOW), plan_dict(trade=trade, zone=zone, primary=primary)).run(NOW)
        if active:
            K(tmp, flat_store(NOW + timedelta(minutes=5), extra5=[touch]), plan_dict(trade=trade, zone=zone, primary=primary)).run(NOW + timedelta(minutes=5))
        later = NOW + timedelta(hours=1, minutes=1)
        k = K(tmp, flat_store(later, extra5=[touch] if active else []), _plan_with_dest_reached(trade, primary))
        k.run(later)
        end = [e for e in events(tmp) if e.get("status") in (COMPLETED, INVALIDATED)][-1]
        assert end["status"] == want and words in end["why"] and "hourly re-check" in end["why"]
        assert k.state["recommendation"] is None                       # and nothing new is issued at the destination


def test_d1_a_different_destination_reached_is_still_supporting_evidence_changed(tmp_path):
    K(tmp_path, flat_store(NOW), plan_dict()).run(NOW)
    later = NOW + timedelta(hours=1, minutes=1)
    K(tmp_path, flat_store(later), _plan_with_dest_reached(primary=13100)).run(later)
    assert "supporting evidence changed" in events(tmp_path)[-1]["why"]


def test_d1_a_valid_recommendation_is_issued_and_its_destination_first_check_still_works(tmp_path):
    K(tmp_path, flat_store(NOW), plan_dict()).run(NOW)                 # quiet market at 13200, destination 13170
    t = NOW + timedelta(minutes=5)
    k = K(tmp_path, flat_store(t, extra5=[five(NOW, 13200, 13200, 13168, 13169)]), plan_dict())
    k.run(t)
    assert events(tmp_path)[-1]["event"] == "invalidated" and "destination reached before entry" in events(tmp_path)[-1]["why"]


# ---- pre-creation activation ----------------------------------------------------------------------------------------

def test_candle_timing_against_creation():
    created = "2026-11-17T09:00:02Z"
    assert candle_timing(five(NOW - timedelta(minutes=5), 1, 1, 1, 1), created) == "before creation"
    assert candle_timing(five(NOW, 1, 1, 1, 1), created) == "overlapped creation"
    assert candle_timing(five(NOW + timedelta(minutes=5), 1, 1, 1, 1), created) == "after creation"
    assert candle_timing(five(NOW, 1, 1, 1, 1), "2026-11-17T09:00:00Z") == "after creation"


def test_price_in_the_zone_before_creation_never_activates_it(tmp_path):
    inzone = five(NOW - timedelta(minutes=5), 13240, 13245, 13238, 13242)          # finished before creation
    k = K(tmp_path, flat_store(NOW, extra5=[inzone]), plan_dict())
    k.run(NOW)
    assert k.state["recommendation"]["status"] == WAITING
    e = events(tmp_path)[-1]
    assert e["event"] == "in zone at creation" and e["candle_timing"] == "before creation" and "not an activation" in e["why"]


def test_created_before_the_interaction_activates_with_its_candle_recorded(tmp_path):
    K(tmp_path, flat_store(NOW), plan_dict()).run(NOW)
    t = NOW + timedelta(minutes=10)
    touch = five(NOW + timedelta(minutes=5), 13230, 13238, 13229, 13231)
    k = K(tmp_path, flat_store(t, extra5=[touch]), plan_dict())
    k.run(t)
    rec = k.state["recommendation"]
    assert rec["status"] == ACTIVE
    act = [e for e in events(tmp_path) if e["event"] == "active"][0]
    assert act["candle_timing"] == "after creation" and act["candle_start_utc"] == "2026-11-17T09:05:00Z"
    assert act["candle_end_utc"] == "2026-11-17T09:10:00Z" and act["qualifying_event_utc"] is None
    assert "5-minute candle" in act["event_time_basis"] and rec["activation"]["candle_timing"] == "after creation"


def test_a_candle_running_at_creation_is_ambiguous_and_the_next_one_decides(tmp_path):
    created = NOW + SEC                                                  # as every hourly analysis: a few seconds late
    K(tmp_path, flat_store(NOW), plan_dict()).run(created)
    running = five(NOW, 13230, 13238, 13229, 13231)                      # 09:00-09:05, touches the zone
    t1 = NOW + timedelta(minutes=5)
    k = K(tmp_path, flat_store(t1, extra5=[running]), plan_dict())
    k.run(t1)
    assert k.state["recommendation"]["status"] == WAITING
    amb = events(tmp_path)[-1]
    assert amb["event"] == "ambiguous" and amb["candle_timing"] == "overlapped creation" and "not used" in amb["why"]
    t2 = t1 + timedelta(minutes=5)
    k = K(tmp_path, flat_store(t2, extra5=[running, five(t1, 13230, 13238, 13229, 13231)]), plan_dict())
    k.run(t2)
    assert k.state["recommendation"]["status"] == ACTIVE
    assert k.state["recommendation"]["activation"]["candle_start_utc"] == "2026-11-17T09:05:00Z"


def test_zone_and_destination_in_the_same_overlapping_candle_change_nothing(tmp_path):
    K(tmp_path, flat_store(NOW), plan_dict()).run(NOW + SEC)
    both = five(NOW, 13200, 13241, 13168, 13200)                         # reaches the zone AND the destination
    k = K(tmp_path, flat_store(NOW + timedelta(minutes=5), extra5=[both]), plan_dict())
    k.run(NOW + timedelta(minutes=5))
    assert k.state["recommendation"]["status"] == WAITING
    why = events(tmp_path)[-1]["why"]
    assert "reached the primary destination" in why and "reached the zone" in why


def test_multiple_interactions_in_one_candle_after_creation_follow_the_existing_order(tmp_path):
    K(tmp_path, flat_store(NOW), plan_dict()).run(NOW)
    both = five(NOW + timedelta(minutes=5), 13200, 13241, 13168, 13200)
    K(tmp_path, flat_store(NOW + timedelta(minutes=10), extra5=[both]), plan_dict()).run(NOW + timedelta(minutes=10))
    assert events(tmp_path)[-1]["event"] == "invalidated"               # destination first, as before the correction


@pytest.mark.parametrize("trade", ["SELL", "BUY"])
def test_pre_creation_rules_are_symmetrical(tmp_path, trade):
    zone, primary = ((13240, 13250), 13170) if trade == "SELL" else ((13150, 13160), 13230)
    touch = (lambda t: five(t, 13230, 13238, 13229, 13231)) if trade == "SELL" else (lambda t: five(t, 13170, 13171, 13162, 13169))
    before = touch(NOW - timedelta(minutes=5))
    k = K(tmp_path, flat_store(NOW, extra5=[before]), plan_dict(trade=trade, zone=zone, primary=primary))
    k.run(NOW + SEC)
    assert k.state["recommendation"]["status"] == WAITING and events(tmp_path)[-1]["event"] == "in zone at creation"
    t = NOW + timedelta(minutes=5)
    k = K(tmp_path, flat_store(t, extra5=[before, touch(NOW)]), plan_dict(trade=trade, zone=zone, primary=primary))
    k.run(t)
    assert k.state["recommendation"]["status"] == WAITING and events(tmp_path)[-1]["event"] == "ambiguous"
    t2 = t + timedelta(minutes=5)
    k = K(tmp_path, flat_store(t2, extra5=[before, touch(NOW), touch(t)]), plan_dict(trade=trade, zone=zone, primary=primary))
    k.run(t2)
    assert k.state["recommendation"]["status"] == ACTIVE


def test_restart_and_recovery_give_the_same_lifecycle_as_running_throughout(tmp_path):
    touch = lambda t: five(t, 13230, 13238, 13229, 13231)              # noqa: E731
    candles = [touch(NOW), touch(NOW + timedelta(minutes=5))]
    end = NOW + timedelta(minutes=15)
    a = tmp_path / "a"                                                   # every 5 minutes
    K(a, flat_store(NOW), plan_dict()).run(NOW + SEC)
    for m in (5, 10, 15):
        K(a, flat_store(NOW + timedelta(minutes=m), extra5=candles), plan_dict()).run(NOW + timedelta(minutes=m))
    b = tmp_path / "b"                                                   # the planner down for 15 minutes, then catches up
    K(b, flat_store(NOW), plan_dict()).run(NOW + SEC)
    K(b, flat_store(end, extra5=candles), plan_dict()).run(end)
    strip = lambda es: [(e["event"], e.get("candle_start_utc")) for e in es if e["event"] != "analysis"]  # noqa: E731
    assert strip(events(a)) == strip(events(b))
    assert ("ambiguous", "2026-11-17T09:00:00Z") in strip(events(b)) and ("active", "2026-11-17T09:05:00Z") in strip(events(b))


def test_a_live_recommendation_from_before_the_correction_still_works_after_a_restart(tmp_path):
    K(tmp_path, flat_store(NOW), plan_dict()).run(NOW)
    f = tmp_path / "planner" / "GBPUSD" / "current.json"
    st = json.loads(f.read_text())
    st["recommendation"].pop("activation", None)
    st["recommendation"]["invalidation"]["destination_first_applies"] = False      # as the 23:00 recommendation
    f.write_text(json.dumps(st))
    t = NOW + timedelta(minutes=5)
    k = K(tmp_path, flat_store(t, extra5=[five(NOW, 13200, 13200, 13168, 13169)]), plan_dict())
    k.run(t)
    assert k.state["recommendation"]["status"] == WAITING                # its recorded rule is honoured until re-checked


# ---- reporting ------------------------------------------------------------------------------------------------------

def test_issued_jsonl_keeps_the_full_structural_snapshot_and_never_later_data(tmp_path):
    p = plan_dict()
    p["as_of_utc"] = "2026-11-17T09:00:00Z"
    p["structure"] = {"levels": [{"price": "13243.7", "name": "daily R2", "kind": "daily R/S", "origin_utc": "2026-11-17T00:00:00Z"}],
                      "zones": [{"low": "13240", "high": "13250", "class": "Major", "levels": ["daily R2 13243.7"]}],
                      "swings": {"4h": [], "1d": [], "1h": []}}
    p["candidates"] = [{"low": "13240", "high": "13250", "chosen": True}]
    K(tmp_path, flat_store(NOW), p).run(NOW)
    line = json.loads((tmp_path / "planner" / "GBPUSD" / "issued.jsonl").read_text().splitlines()[0])
    assert line["structural_snapshot"] == p["structure"] and line["candidates"] == p["candidates"]
    assert line["analysis_as_of_utc"] == "2026-11-17T09:00:00Z" and "history" not in line
    later = NOW + timedelta(hours=1, minutes=1)
    p2 = dict(p, structure={"levels": [], "zones": [], "swings": {}})
    K(tmp_path, flat_store(later), p2).run(later)
    again = json.loads((tmp_path / "planner" / "GBPUSD" / "issued.jsonl").read_text().splitlines()[0])
    assert again == line                                                 # the snapshot is never rewritten later


def test_the_real_planner_snapshot_holds_every_level_and_nothing_from_after_its_time():
    from planner.assess import plan_at
    from tests.functional.test_planner_scenarios import _lagging, LAG_CORRECTION
    st = _lagging(LAG_CORRECTION)
    t = st.by_tf["5m"][-1].end - timedelta(hours=6)
    p = plan_at(S, st, t, calendar=[]).as_dict()
    snap = p["structure"]
    assert snap["levels"] and snap["zones"] and set(snap["swings"]) == {"4h", "1d", "1h"}
    iso = t.strftime("%Y-%m-%dT%H:%M:%SZ")
    assert all((lv.get("origin_utc") or "") <= iso for lv in snap["levels"])
    assert all(s["known_utc"] <= iso for tf in snap["swings"].values() for s in tf)
    for z in [p["entry_zone"]] + [d["zone"] for d in p["destinations"].values() if d]:
        assert any(x["low"] == z["low"] and x["high"] == z["high"] for x in snap["zones"])
    assert plan_at(S, st.until(t), t, calendar=[]).as_dict()["structure"] == snap          # no future data


def test_a_broken_snapshot_never_stops_the_plan():
    from planner.assess import structure_snapshot
    assert structure_snapshot([object()], [], [], [], []) is None


# ---- the dashboard's evaluation -------------------------------------------------------------------------------------

def _dash(tmp):
    from tests.stp_fixtures import settings
    return settings(tmp)


def test_evaluation_never_counts_a_pre_creation_activation(tmp_path):
    from dashboard import stp
    from tests.stp_fixtures import keeper
    s = _dash(tmp_path)
    keeper(s, flat_store(NOW), plan_dict()).run(NOW + SEC)
    # an old-style record: ACTIVE at creation from the candle before, as the planner did before the correction
    f = tmp_path / "planner" / "GBPUSD" / "recommendations.jsonl"
    rows = [json.loads(x) for x in f.read_text().splitlines()]
    rid = rows[1]["id"]
    rows.append({"time_utc": "2026-11-17T09:00:02Z", "event": "active", "id": rid, "why": "the 08:55 candle reached the zone", "status": "ACTIVE"})
    rows.append({"time_utc": "2026-11-17T09:05:00Z", "event": "completed", "id": rid, "why": "price reached the primary destination 13170", "status": "COMPLETED"})
    f.write_text("".join(json.dumps(r) + "\n" for r in rows))
    store = flat_store(NOW + timedelta(minutes=5), extra5=[five(NOW, 13200, 13200, 13168, 13169)])
    e = stp.evaluation(s, NOW + timedelta(minutes=30), store=store)
    c = e["counts"]
    assert c["activated_as_recorded"] == 1 and c["activated"] == 0 and c["activation_corrected"] == 1
    assert c["completed"] == 1 and c["reached_primary_after_entry"] == 0 and c["completed_without_confirmed_activation"] == 1
    note = e["ambiguous"][0]["notes"][0]
    assert "finished before" in note and "planner's record is unchanged" in note
    assert any(r["event"] == "active" for r in (json.loads(x) for x in f.read_text().splitlines()))   # original kept


def test_evaluation_moves_an_overlapping_activation_to_the_first_candle_after_creation(tmp_path):
    from dashboard import stp
    from tests.stp_fixtures import keeper
    s = _dash(tmp_path)
    keeper(s, flat_store(NOW), plan_dict()).run(NOW + SEC)
    f = tmp_path / "planner" / "GBPUSD" / "recommendations.jsonl"
    rows = [json.loads(x) for x in f.read_text().splitlines()]
    rid = rows[1]["id"]
    rows.append({"time_utc": "2026-11-17T09:05:00Z", "event": "active", "id": rid, "why": "the 09:00 candle", "status": "ACTIVE"})
    f.write_text("".join(json.dumps(r) + "\n" for r in rows))
    touch = lambda t: five(t, 13230, 13238, 13229, 13231)              # noqa: E731
    store = flat_store(NOW + timedelta(minutes=20), extra5=[touch(NOW), touch(NOW + timedelta(minutes=10))])
    code, d = stp.recommendation(s, "id=" + rid, NOW + timedelta(minutes=20), store=store)
    act = d["observed_after"]["activation"]
    assert act["recorded_timing"] == "overlapped creation" and act["confirmed_candle_start_utc"] == "2026-11-17T09:10:00Z"
    assert d["observed_after"]["minutes_to_zone"] == 14


def test_the_detail_carries_the_snapshot_levels_for_the_chart_views(tmp_path):
    from dashboard import stp
    from tests.stp_fixtures import keeper
    s = _dash(tmp_path)
    p = plan_dict()
    p["structure"] = {"levels": [{"price": "13243.7", "name": "daily R2", "kind": "daily R/S", "timeframe": "daily"},
                                 {"price": "13222.0", "name": "hourly swing high", "kind": "hourly swing", "timeframe": "1h"}],
                      "zones": [{"low": "13240", "high": "13250", "class": "Major", "families": [], "levels": []},
                                {"low": "13221", "high": "13223", "class": "Minor", "families": [], "levels": []}],
                      "swings": {}}
    keeper(s, flat_store(NOW), p).run(NOW)
    rid = json.loads((tmp_path / "planner" / "GBPUSD" / "issued.jsonl").read_text().splitlines()[0])["id"]
    code, d = stp.recommendation(s, "id=" + rid, NOW + timedelta(minutes=5), store=flat_store(NOW))
    ov = d["overlays_at_creation"]
    tiers = {lv["name"]: lv["tier"] for lv in ov["levels"]}
    assert tiers == {"daily R2": "structure", "hourly swing high": "full"}
    assert [z["tier"] for z in ov["zones"]] == ["structure", "full"]
    assert [lv["price_text"] for lv in ov["levels"]] == ["1.32220", "1.32437"]       # values as recorded


def test_the_overview_uses_the_full_snapshot_and_the_three_views_exist(tmp_path):
    from pathlib import Path
    from dashboard import stp
    from tests.stp_fixtures import keeper
    s = _dash(tmp_path)
    p = plan_dict()
    p["structure"] = {"levels": [{"price": "13300", "name": "weekly R1", "kind": "weekly R/S"}], "zones": [], "swings": {}}
    keeper(s, flat_store(NOW), p).run(NOW)
    ov = stp.overview(s, NOW + timedelta(minutes=1))["overlays"]
    assert ov["complete"] is True and ov["levels"][0]["tier"] == "structure" and ov["plan"]["trade"] == "SELL"
    js = (Path(__file__).resolve().parents[2] / "dashboard/static/stp/stp.js").read_text()
    for m in ('["plan", "Trade plan"', '["structure", "Market structure"', '["full", "Full analysis"', 'mode: "plan"',
              'tf: "1h"', '"1h": 60', "placeLabels", "axisLabelVisible: true"):
        assert m in js
    assert js.count("createPriceLine(") == 1                             # only the current price has an axis label
    css = (Path(__file__).resolve().parents[2] / "dashboard/static/stp/stp.css").read_text()
    assert "line-through" not in css and ".stp-rows .v.price" in css
