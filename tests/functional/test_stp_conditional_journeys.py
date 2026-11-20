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
    journeys = plan["observations"]["conditional_journeys"]
    assert journeys, "A classified opportunity with qualifying zones must inspect journeys"
    for journey in journeys:
        assert journey["decision"] in ("eligible", "rejected")
        assert journey["countermove_status"] in ("already in zone", "possible, not predicted")
        assert D(journey["countermove_pips"]) >= 0
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
