"""Functional invariants for destination-aware STP candidate assessment.

These tests use the existing synthetic candle-market fixtures. No IG or trading
orders are involved. They check the actual plan and its candidate diagnostics.
"""
from decimal import Decimal as D

from planner.assess import plan_at
from tests.functional.test_planner_scenarios import (
    S, corrective_market, mirrored, at_end,
)


def _check_journeys(plan):
    outlook = plan["observations"]["destination_first_outlook"]
    assert isinstance(outlook, list)
    for destination in outlook:
        assert destination["class"] == "Major"
        assert destination["destination_forecast"] == "not established by structural eligibility alone"
        assert destination["countermove_forecast"] == "not established by structural eligibility alone"
        assert isinstance(destination["candidate_entries"], list)
    journeys = plan["observations"]["conditional_journeys"]
    assert journeys, "A classified opportunity with qualifying zones must inspect journeys"
    for journey in journeys:
        assert journey["decision"] in ("eligible", "rejected")
        assert journey["countermove_status"] in ("already in zone", "possible, not predicted")
        assert D(journey["countermove_pips"]) >= 0
        assert journey["countermove_probability"] is None
        assert journey["countermove_evidence_state"] in {
            "AT_ENTRY_NOW", "CORRECTION_OBSERVED", "CORRECTION_INDICATED",
            "EXHAUSTION_ONLY", "UNCONFIRMED_PULLBACK",
        }
        assert journey["countermove_evidence"]
        if journey["countermove_evidence_state"] == "AT_ENTRY_NOW":
            assert journey["countermove_status"] == "already in zone"
        if journey["decision"] == "eligible":
            assert journey["destination"] is not None
            assert journey["reason"] == "structurally eligible; countermove remains unconfirmed"
        else:
            assert journey["reason"]
    if plan["entry_zone"] is not None:
        chosen = plan["entry_zone"]
        assert any(
            j["decision"] == "eligible"
            and j["entry"] == [chosen["low"], chosen["high"]]
            for j in journeys
        ), "Published zone must correspond to a fully assessed eligible journey"
        assert journeys[0]["decision"] in ("eligible", "rejected")
    else:
        assert all(j["decision"] == "rejected" for j in journeys)


def test_bearish_conditional_journey_is_supported_by_full_candidate_diagnostics():
    _, plan = at_end(corrective_market())
    assert plan["trade"] == "SELL"
    _check_journeys(plan)


def test_bullish_conditional_journey_is_supported_by_full_candidate_diagnostics():
    _, plan = at_end(mirrored(corrective_market()))
    assert plan["trade"] == "BUY"
    _check_journeys(plan)


def test_no_major_destination_is_reported_per_candidate_without_issuing_plan():
    from tests.functional.test_planner_scenarios import market, START
    w, h, p = [(0, 13900)], 0, 13900
    for _ in range(18):
        h += 22
        p -= 110
        w.append((h, p))
        h += 14
        p += 55
        w.append((h, p))
    store = market(S, START, w + [(h + 14, p - 70), (h + 28, p - 140)])
    _, plan = at_end(store)
    assert plan["entry_zone"] is None
    assert "no Major support zone" in plan["no_recommendation"]
    assert plan["observations"]["conditional_journeys"]
    assert all(
        j["decision"] == "rejected" and j["reason"] == "no Major destination beyond this entry"
        for j in plan["observations"]["conditional_journeys"]
    )


def test_destination_already_touched_is_reported_without_false_entry():
    from datetime import timedelta
    from tests.functional.test_planner_scenarios import _lagging, LAG_CORRECTION
    store = mirrored(_lagging(LAG_CORRECTION))
    _, plan = at_end(store)
    assert plan["entry_zone"] is None
    assert "already reached" in plan["no_recommendation"]
    assert plan["destination_reached"] is not None
    assert any(
        j["decision"] == "rejected" and "already touched" in j["reason"]
        for j in plan["observations"]["conditional_journeys"]
    )


def test_continuation_does_not_claim_an_observed_countermove():
    from tests.functional.test_planner_scenarios import _market, PULLBACK_END
    _, plan = at_end(_market(tuple(PULLBACK_END)))
    assert plan["condition"] == "CONTINUATION"
    assert plan["observations"]["conditional_journeys"]
    for j in plan["observations"]["conditional_journeys"]:
        if j["countermove_evidence_state"] != "AT_ENTRY_NOW":
            assert j["countermove_evidence_state"] == "UNCONFIRMED_PULLBACK"
            assert j["countermove_probability"] is None
