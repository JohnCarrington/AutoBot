"""Forecast coverage is not forecast accuracy."""
from planner.november_replay import target_summary


def test_preferred_absent_is_not_counted_as_miss():
    rows = [
        {"observations": {"target_ladder": {"immediate": {"low": "1", "high": "2"},
                                              "preferred": None}},
         "target_outcome_24h": {"status": "SCORED", "targets": {
             "immediate": {"status": "REACHED"}, "preferred": {"status": "NOT_FORECAST"}}}},
        {"observations": {"target_ladder": {"preferred": {"low": "0", "high": "1"}}},
         "target_outcome_24h": {"status": "SCORED", "targets": {
             "preferred": {"status": "NOT_REACHED"}}}},
    ]
    summary = target_summary(rows)
    assert summary["preferred"]["forecast"] == 1
    assert summary["preferred"]["not_forecast"] == 1
    assert summary["preferred"]["not_reached"] == 1
    assert summary["preferred"]["reached"] == 0


def test_censored_is_not_counted_as_miss():
    rows = [{"observations": {"target_ladder": {
        "preferred": {"low": "1", "high": "2"}}},
        "target_outcome_24h": {"status": "DATA_GAP_CENSORED", "targets": {
            "preferred": {"status": "DATA_GAP_CENSORED"}}}}]
    summary = target_summary(rows)
    assert summary["preferred"]["data_gap_censored"] == 1
    assert summary["preferred"]["not_reached"] == 0
