"""Functional tests for the Structural Trade Planner tab (owner's brief of 17 November 2026, part 14): what the owner
sees in each planner situation. Every lifecycle is made by the real planner keeper (tests/stp_fixtures.py); the tab
only reads it. Observe only; never contacts IG."""

import json
from datetime import timedelta
from pathlib import Path

import pytest

from dashboard import stp
from tests.stp_fixtures import NOW, SCENARIOS, Scenario, T, flat_store, keeper, plan_dict, settings, write_status
from tests.technical.test_stp_dashboard import App


def ov(sc):
    return stp.overview(sc.s, sc.now)


def detail(sc, rid):
    code, d = stp.recommendation(sc.s, "id=" + rid, sc.now, sc.store)
    assert code == 200
    return d


def rows(sc):
    return stp.history(sc.s, "size=50")[1]["rows"]


# 1-5: the forecast ---------------------------------------------------------------------------------------------

def test_1_3_established_bearish_structure_with_a_corrective_reversal(tmp_path):
    o = ov(SCENARIOS["waiting"](tmp_path))
    f = o["forecast"]
    assert f["dominant_direction"] == "BEARISH" and f["direction_text"].startswith("lower highs and lower lows")
    assert f["opportunity"] == "corrective reversal"
    assert f["movement_text"] == "Corrective rally towards resistance, followed by potential bearish continuation."
    assert o["opportunity_text"] == "SELL" and o["recommendation"]["trade"] == "SELL"


def test_2_established_bullish_structure(tmp_path):
    o = ov(SCENARIOS["bullish"](tmp_path))
    assert o["forecast"]["dominant_direction"] == "BULLISH"
    assert o["forecast"]["movement_text"] == "Corrective dip towards support, followed by potential bullish continuation."
    assert o["recommendation"]["trade"] == "BUY" and o["recommendation"]["entry_zone"] == "1.31500–1.31600"
    assert o["overlays"]["plan"]["destinations"]["primary"]["text"] == "1.32300"


def test_4_healthy_trend_pullback(tmp_path):
    sc = Scenario(tmp_path)
    sc.run(NOW, [plan_dict() | {"condition": "CONTINUATION", "opportunity": "healthy-trend pullback"}])
    o = ov(sc)
    assert o["forecast"]["condition"] == "CONTINUATION" and o["recommendation"]["opportunity"] == "healthy-trend pullback"
    assert o["forecast"]["movement_text"].startswith("Pullback (rally) towards resistance within the downtrend")


def test_5_an_h4_daily_conflict_is_shown_as_a_directional_conflict(tmp_path):
    sc = Scenario(tmp_path)
    sc.run(NOW, [plan_dict() | {"direction_evidence": ["4-hour structure: lower highs and lower lows",
                                                       "warning: the daily structure (up) is against the 4-hour structure (down)"]}])
    t = ov(sc)["technical"]
    assert t["conflicts"] == ["warning: the daily structure (up) is against the 4-hour structure (down)"]


# 6-10: lifecycle states ------------------------------------------------------------------------------------------

def test_6_waiting_for_the_entry_zone(tmp_path):
    o = ov(SCENARIOS["waiting"](tmp_path))
    assert o["status"] == {"code": "WAITING", "label": "WAITING FOR ENTRY ZONE"} and o["explanation"] is None


def test_7_active(tmp_path):
    sc = SCENARIOS["active"](tmp_path)
    o = ov(sc)
    assert o["status"]["code"] == "ACTIVE"
    d = detail(sc, o["recommendation"]["id"])
    assert d["stages"]["active"] == "2026-11-17T09:05:00Z" and d["live"] is True
    assert d["observed_after"]["mfe_pips"] is not None                                       # measured since activation


def test_8_completed(tmp_path):
    sc = SCENARIOS["completed"](tmp_path)
    r = rows(sc)[0]
    assert r["status"] == "COMPLETED" and "primary destination 1.31700" in r["reason"]
    d = detail(sc, r["id"])
    assert [s for s in ("created", "waiting", "active", "completed") if d["stages"][s]] == ["created", "waiting", "active", "completed"]
    assert d["stages"]["invalidated"] is None and d["stages"]["superseded"] is None          # not invented
    assert d["observed_after"]["minutes_active_to_end"] == 5


def test_9_invalidated_by_a_confirmed_break(tmp_path):
    sc = SCENARIOS["invalidated_break"](tmp_path)
    old = [r for r in rows(sc) if r["status"] == "INVALIDATED"][0]
    assert "confirmed break" in old["reason"] and "1.32560" in old["reason"]
    assert detail(sc, old["id"])["stages"]["active"] is None


def test_10_superseded(tmp_path):
    sc = SCENARIOS["superseded"](tmp_path)
    r = {x["status"]: x for x in rows(sc)}
    assert set(r) == {"SUPERSEDED", "WAITING"}
    assert "does not overlap" in r["SUPERSEDED"]["reason"] and r["WAITING"]["zone"] == "1.32800–1.32900"
    assert stp.evaluation(sc.s, sc.now, sc.store)["counts"]["superseded"] == 1


# 11-15: no recommendation, stale, missing and warming indicators ------------------------------------------------

def test_11_no_recommendation_despite_a_directional_forecast(tmp_path):
    o = ov(SCENARIOS["no_rec_directional"](tmp_path))
    assert o["status"]["label"] == "NO RECOMMENDATION" and o["opportunity_text"] == "NO CURRENT OPPORTUNITY"
    e = o["explanation"]
    assert e["scenario"] == "A" and e["text"].startswith("The dominant structure is bearish, but no structural entry")
    assert e["planner_reason"].startswith("no defensible entry zone") and "1.33000" in e["planner_reason"]


def test_12_no_recommendation_because_the_direction_is_indeterminate(tmp_path):
    o = ov(SCENARIOS["no_rec_indeterminate"](tmp_path))
    e = o["explanation"]
    assert e["scenario"] == "B" and "insufficient to establish a dominant direction" in e["text"] and "NEUTRAL" in e["text"]
    assert o["forecast"]["movement_text"] is None                                          # no movement invented


def test_13_stale_market_data(tmp_path):
    sc = SCENARIOS["stale"](tmp_path)
    o = ov(sc)
    assert o["freshness"]["state"] == "STALE" and o["freshness"]["label"] == "STALE DATA"
    assert o["recommendation"]["current"] is False                                          # the planner's own rule
    sc2 = Scenario(tmp_path / "b")
    sc2.run(NOW, [plan_dict(no_rec="no ADR yet")])
    keeper(sc2.s, flat_store(NOW), plan_dict(no_rec="no ADR yet")).run(NOW + timedelta(hours=3))
    e = stp.overview(sc2.s, NOW + timedelta(hours=3))["explanation"]
    assert e["scenario"] == "C" and "stale" in e["text"]


def test_13_opening_between_hourly_analyses_is_current_not_stale(tmp_path):
    sc = SCENARIOS["waiting"](tmp_path)
    sc.run(NOW + timedelta(minutes=35), [plan_dict()])                          # the 5-minute runs carry on
    f = stp.overview(sc.s, NOW + timedelta(minutes=37))["freshness"]
    assert f["state"] == "CURRENT" and f["next_analysis_due_utc"] == "2026-11-17T10:00:00Z"
    assert f["last_analysis_utc"] == "2026-11-17T09:00:00Z"


def test_14_missing_indicators_show_as_missing_never_guessed(tmp_path):
    sc = Scenario(tmp_path)
    sc.run(NOW, [plan_dict() | {"observations": {}}])
    t = ov(sc)["technical"]
    assert t["macd"] is None and t["rsi3"] is None and t["bollinger"]["upper"] is None and t["adr_pips"] is None


def test_15_h4_ema200_warming_up(tmp_path):
    sc = Scenario(tmp_path)
    sc.run(NOW, [plan_dict() | {"warming_up": ["4h EMA200 (451 of 592 candles)"],
                                "observations": {"h4_ema200": "warming up", "h4_ema100": "13311.1"}}])
    t = ov(sc)["technical"]
    assert t["warming_up"] == ["4h EMA200 (451 of 592 candles)"]
    assert t["ema"]["ema200"] == "warming up" and t["ema"]["ema100"] == "1.33111"


# 16-20 -------------------------------------------------------------------------------------------------------------

def test_16_recommendations_with_identical_zones_stay_separate(tmp_path):
    sc = SCENARIOS["identical_zones"](tmp_path)
    r = rows(sc)
    assert len(r) == 2 and r[0]["zone"] == r[1]["zone"] and r[0]["id"] != r[1]["id"]
    assert {x["status"] for x in r} == {"COMPLETED", "WAITING"}
    ev = stp.evaluation(sc.s, sc.now, sc.store)
    assert ev["counts"]["total"] == 2 and ev["counts"]["completed"] == 1 and ev["counts"]["awaiting_entry"] == 1


def test_17_a_historical_recommendation_shows_what_was_known_at_creation_and_what_happened_after(tmp_path):
    sc = SCENARIOS["completed"](tmp_path)
    rid = rows(sc)[0]["id"]
    d = detail(sc, rid)
    c = d["at_creation"]
    assert c["source"] == "snapshot"
    assert c["card"]["plan"]["destinations"]["intermediate"]["text"] == "1.32100"
    assert c["card"]["plan"]["invalidation_conditions"] == ["an hourly close at or above 1.32530"]
    assert c["card"]["created_utc"] == "2026-11-17T09:00:00Z"
    oa = d["observed_after"]
    assert oa["label"].startswith("observed after creation") and oa["mfe_pips"] > 0 and oa["measured_from"].startswith("the reference level")


def test_17_a_record_from_before_snapshots_shows_only_its_summary(tmp_path):
    sc = SCENARIOS["completed"](tmp_path)
    (Path(sc.s.planner.folder) / "GBPUSD" / "issued.jsonl").unlink()            # as the two 17 November records
    d = detail(sc, rows(sc)[0]["id"])
    c = d["at_creation"]
    assert c["source"] == "summary" and "not recorded" in c["note"]
    assert c["card"]["entry_zone"] == "1.32400–1.32500" and c["card"]["plan"]["destinations"]["primary"]["text"] == "1.31700"
    assert c["card"]["plan"]["invalidation_conditions"] == []                     # unavailable, not reconstructed


def test_18_destination_reached_before_entry(tmp_path):
    sc = SCENARIOS["destination_first"](tmp_path)
    r = rows(sc)[0]
    assert r["status"] == "INVALIDATED" and r["reason"].startswith("destination reached before entry")
    o = ov(sc)
    assert o["explanation"]["scenario"] == "D" and "ended at 09:05 UTC as INVALIDATED" in o["explanation"]["text"]
    c = stp.evaluation(sc.s, sc.now, sc.store)["counts"]
    assert c["destination_before_entry"] == 1 and c["never_reached_zone"] == 1 and c["reached_primary_after_entry"] == 0


def test_18_issued_with_price_already_at_the_destination_is_flagged(tmp_path):
    """The 17 November shape: the recommendation is issued while the last finished 5-minute candle is already within
    3 pips of its primary destination."""
    sc = Scenario(tmp_path)
    near = flat_store(NOW, price=13172)
    k = keeper(sc.s, near, plan_dict())
    k.run(NOW)
    sc.store, sc.now = near, NOW
    ev = stp.evaluation(sc.s, NOW, near)
    assert ev["counts"]["issued_at_destination"] == 1
    assert any("issued with price already at the primary destination" in n for a in ev["ambiguous"] for n in a["notes"])


def test_19_a_recommendation_continues_across_hourly_analyses(tmp_path):
    sc = SCENARIOS["continued"](tmp_path)
    r = rows(sc)
    assert len(r) == 1
    d = detail(sc, r[0]["id"])
    assert [e["event"] for e in d["timeline"]].count("supported") + [e["event"] for e in d["timeline"]].count("changed") == 2
    st = stp.evaluation(sc.s, sc.now, sc.store)["stability"]
    assert st["rechecks"] == 2 and st["verdict"] == "INSUFFICIENT DATA"


def test_20_planner_unavailable_while_the_rest_of_the_dashboard_works(tmp_path):
    s = settings(tmp_path)                                                       # no planner folder at all
    write_status(s)
    a = App(s, NOW)
    code, o, _ = a.get("/api/stp/overview")
    assert code == 200 and o["available"] is False and o["freshness"]["label"] == "PLANNER UNAVAILABLE"
    code, st, _ = a.get("/api/status")
    assert code == 200 and st["planner"]["available"] is False and st["planner"]["card"]["available"] is False
    assert a.get("/api/history")[0] == 200


def test_evaluation_never_reports_trading_results(tmp_path):
    sc = SCENARIOS["completed"](tmp_path)
    keys = set()
    def walk(x):
        if isinstance(x, dict):
            keys.update(k.lower() for k in x)
            [walk(v) for v in x.values()]
        elif isinstance(x, list):
            [walk(v) for v in x]
    e = stp.evaluation(sc.s, sc.now, sc.store)
    walk(e)
    assert not [k for k in keys if any(w in k for w in ("gbp", "pnl", "profit", "win", "loss", "fill", "spread", "commission"))]
    assert "no fills, no P&L" in e["label"]


def test_the_main_dashboard_card_summarises_without_trading_controls(tmp_path):
    sc = SCENARIOS["waiting"](tmp_path)
    c = stp.card(sc.s, sc.now)
    assert c["dominant_direction"] == "BEARISH" and c["status"] == "WAITING FOR ENTRY ZONE" and c["zone"] == "1.32400–1.32500"
    assert c["freshness"]["label"] == "CURRENT" and c["last_analysis_utc"] == "2026-11-17T09:00:00Z"
    assert c["expected_movement"].startswith("Corrective rally")
