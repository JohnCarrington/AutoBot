"""Date-window regression tests for offline STP replay."""
import pytest

from planner.november_replay import TIMES, assessment_times, daily_target_summary


def test_default_six_snapshots_unchanged():
    assert assessment_times() == TIMES


def test_weekday_checkpoints_and_weekend_skip():
    times = assessment_times("2026-11-06", "2026-11-10")
    assert len(times) == 9
    assert times[0] == "2026-11-06T07:00:00+00:00"
    assert times[-1] == "2026-11-10T12:00:00+00:00"
    assert all("2026-11-07" not in t and "2026-11-08" not in t for t in times)


@pytest.mark.parametrize("start,end", [
    ("2026-11-10", "2026-11-09"),
    ("2026-01-01", "2026-11-10"),
    ("2026-11-09", None),
])
def test_reject_invalid_windows(start, end):
    with pytest.raises(ValueError):
        assessment_times(start, end)


def test_daily_buckets_do_not_merge_separate_days():
    rows = [
        {"assessment_utc": "2026-11-09T07:00:00+00:00", "observations": {}},
        {"assessment_utc": "2026-11-09T09:00:00+00:00", "observations": {}},
        {"assessment_utc": "2026-11-10T07:00:00+00:00", "observations": {}},
    ]
    daily = daily_target_summary(rows)
    assert list(daily) == ["2026-11-09", "2026-11-10"]
    assert daily["2026-11-09"]["preferred"]["not_forecast"] == 2
    assert daily["2026-11-10"]["preferred"]["not_forecast"] == 1
