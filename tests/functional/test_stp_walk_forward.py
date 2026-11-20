"""Offline audit boundaries: no future data, no false historical results."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from planner.walk_forward import audit

T = datetime(2026, 11, 20, 12, tzinfo=timezone.utc)


class FakeStore:
    def __init__(self, latest):
        self.latest = latest
        self.future_reads = []

    def newest(self, tf):
        assert tf == "5m"
        return SimpleNamespace(end=self.latest)

    def read_range(self, tf, start, end):
        self.future_reads.append((tf, start, end))
        return []


def test_insufficient_future_data_never_calls_planner():
    store = FakeStore(T + timedelta(hours=1))
    with patch("planner.walk_forward.plan_at", side_effect=AssertionError("should not plan")):
        result = audit(None, store, T, T + timedelta(hours=4),
                       timedelta(hours=4), timedelta(hours=24))
    assert result["counts"] == {"INSUFFICIENT_FUTURE_DATA": 1}
    assert not store.future_reads


def test_no_plan_is_not_scored():
    store = FakeStore(T + timedelta(hours=48))
    plan = {"fresh": True, "entry_zone": None, "no_recommendation": "no Major destination"}
    with patch("planner.walk_forward.plan_at", return_value=SimpleNamespace(as_dict=lambda: plan)):
        result = audit(None, store, T, T + timedelta(hours=4),
                       timedelta(hours=4), timedelta(hours=24))
    assert result["counts"] == {"NO_PLAN": 1}
    assert not store.future_reads


def test_stale_plan_is_not_scored():
    store = FakeStore(T + timedelta(hours=48))
    plan = {"fresh": False, "entry_zone": None}
    with patch("planner.walk_forward.plan_at", return_value=SimpleNamespace(as_dict=lambda: plan)):
        result = audit(None, store, T, T + timedelta(hours=4),
                       timedelta(hours=4), timedelta(hours=24))
    assert result["counts"] == {"STALE_DATA": 1}
    assert not store.future_reads


def test_invalid_audit_windows_rejected():
    store = FakeStore(T + timedelta(hours=48))
    with pytest.raises(ValueError):
        audit(None, store, T, T, timedelta(hours=4), timedelta(hours=24))
    with pytest.raises(ValueError):
        audit(None, store, T, T + timedelta(hours=4), timedelta(0), timedelta(hours=24))


def test_walk_forward_runs_end_to_end_on_candle_built_synthetic_market():
    from tests.functional.test_planner_scenarios import S, corrective_market
    store = corrective_market()
    end = store.newest("5m").end
    at = end - timedelta(hours=1)
    result = audit(S, store, at, at + timedelta(hours=1),
                   timedelta(hours=1), timedelta(hours=1))
    assert len(result["samples"]) == 1
    assert sum(result["counts"].values()) == 1
    assert result["samples"][0]["status"] in {
        "NO_PLAN", "STALE_DATA", "ENTRY_THEN_DESTINATION",
        "DESTINATION_BEFORE_ENTRY", "AMBIGUOUS_SAME_CANDLE",
        "AMBIGUOUS_ENTRY_OR_INVALIDATION", "AMBIGUOUS_TARGET_OR_INVALIDATION",
        "STRUCTURE_INVALIDATED_BEFORE_ENTRY", "STRUCTURE_INVALIDATED_AFTER_ENTRY",
        "ENTRY_ONLY_CENSORED", "NEITHER_CENSORED", "DATA_GAP_CENSORED",
    }
