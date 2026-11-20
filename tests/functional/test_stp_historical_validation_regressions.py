"""Regression tests for defects found by the STP historical validation (20 November 2026).

1. The walk-forward audit read 4-hour candles from a stored "4h" folder. Research stores (2024-26 history) have none,
   so the 4-hour structure-break invalidation was silently never scored. Outcome 4-hour candles are now built from
   hourly ones with the planner's own four_hour_from_hourly.
2. Strict gap censoring treated every break between 5-minute candles as missing data, including the weekend closure,
   so any journey crossing a weekend was censored. A break is now a gap only if the market was open during it.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D

from planner.forward_outcomes import score_journey
from planner.walk_forward import forward_candles, open_slots_fn
from prices.model import Candle
from tests.functional.test_planner_scenarios import S

UTC = timezone.utc
# Friday 13 November 2026: the market closes at 17:00 New York = 22:00 UTC; it reopens Sunday 21:00 UK = 21:00 UTC.
FRI = datetime(2026, 11, 13, 20, tzinfo=UTC)
SUN_OPEN = datetime(2026, 11, 15, 21, tzinfo=UTC)


def c(tf, start, low, high, close=None, minutes=5):
    a, b = D(str(low)), D(str(high))
    cl = D(str(close)) if close is not None else a
    return Candle(tf, start, start + timedelta(minutes=minutes), a, b, a, cl, a, b, a, cl)


def plan(direction="SELL", as_of=FRI, structure_break=None):
    sell = direction == "SELL"
    return {
        "as_of_utc": as_of.isoformat().replace("+00:00", "Z"),
        "trade": direction,
        "entry_zone": {"low": "13100", "high": "13110"} if sell else {"low": "13000", "high": "13010"},
        "destinations": {"primary": {"zone": {"low": "13000", "high": "13010"} if sell else
                                     {"low": "13100", "high": "13110"}}},
        "invalidation": {"structure_break_close": structure_break} if structure_break else {},
    }


class HourlyOnlyStore:
    """A research store: 5m and 1h candles, no 4h folder (read_range('4h') is empty)."""

    def __init__(self, five, hourly):
        self.data = {"5m": five, "1h": hourly, "4h": []}

    def read_range(self, tf, start, end):
        return [x for x in self.data[tf] if x.start < end and x.end > start]


def _filled_week_hours(start, closes, low=13050, high=13060):
    return [c("1h", start + timedelta(hours=i), low, high, close=cl, minutes=60) for i, cl in enumerate(closes)]


def test_outcome_four_hour_candles_are_built_from_hourly_when_the_store_has_no_4h_folder():
    t0 = datetime(2026, 11, 17, 0, tzinfo=UTC)          # a Tuesday, 00:00 UK = a 4-hour boundary
    hourly = _filled_week_hours(t0, [13050, 13055, 13058, 13125] + [13050] * 4, low=13040, high=13130)
    store = HourlyOnlyStore([], hourly)
    got = forward_candles(S, store, t0, t0 + timedelta(hours=8))
    fours = [x for x in got if x.timeframe == "4h"]
    assert [f.start for f in fours] == [t0, t0 + timedelta(hours=4)]
    assert fours[0].sell_close == D("13125")              # the close of its last hour


def test_h4_structure_break_is_scored_on_a_store_without_stored_4h_candles():
    t0 = datetime(2026, 11, 17, 0, tzinfo=UTC)
    hourly = _filled_week_hours(t0, [13050, 13055, 13058, 13125], low=13040, high=13130)
    # 5-minute candles inside the zone gap: no touch of entry (13100-13110) or destination (13000-13010)
    five = [c("5m", t0 + timedelta(minutes=5 * i), 13040, 13060) for i in range(48)]
    store = HourlyOnlyStore(five, hourly)
    p = plan(as_of=t0, structure_break="13120")
    p["entry_zone"] = {"low": "13200", "high": "13210"}
    p["invalidation"]["structure_break_close"] = "13120"
    result = score_journey(p, forward_candles(S, store, t0, t0 + timedelta(hours=4)),
                           require_contiguous_m5=True, open_slots=open_slots_fn(S))
    assert result["status"] == "STRUCTURE_INVALIDATED_BEFORE_ENTRY"
    assert result["at"] == (t0 + timedelta(hours=4)).isoformat()


def test_weekend_closure_is_not_a_data_gap():
    # Friday 20:00-22:00 touches the entry; Sunday after the open reaches the destination.
    fri = [c("5m", FRI + timedelta(minutes=5 * i), 13095, 13105) for i in range(24)]
    sun = [c("5m", SUN_OPEN + timedelta(minutes=5 * i), 13005, 13050) for i in range(3)]
    out = score_journey(plan(), fri + sun, require_contiguous_m5=True, open_slots=open_slots_fn(S))
    assert out["status"] == "ENTRY_THEN_DESTINATION"


def test_without_market_hours_the_weekend_is_still_treated_as_a_gap():
    fri = [c("5m", FRI + timedelta(minutes=5 * i), 13095, 13105) for i in range(24)]
    sun = [c("5m", SUN_OPEN + timedelta(minutes=5 * i), 13005, 13050) for i in range(3)]
    assert score_journey(plan(), fri + sun, require_contiguous_m5=True)["status"] == "DATA_GAP_CENSORED"


def test_a_missing_candle_while_the_market_is_open_still_censors():
    tue = datetime(2026, 11, 17, 10, tzinfo=UTC)
    first = [c("5m", tue + timedelta(minutes=5 * i), 13095, 13105) for i in range(3)]
    after_gap = [c("5m", tue + timedelta(minutes=30), 13005, 13050)]
    out = score_journey(plan(as_of=tue), first + after_gap, require_contiguous_m5=True, open_slots=open_slots_fn(S))
    assert out["status"] == "DATA_GAP_CENSORED"


def test_weekly_open_grace_skips_only_the_late_source_opening_hour():
    slots = open_slots_fn(S, timedelta(minutes=65))
    assert list(slots(SUN_OPEN, SUN_OPEN + timedelta(minutes=65))) == []
    assert next(iter(slots(SUN_OPEN, SUN_OPEN + timedelta(hours=2)))) == SUN_OPEN + timedelta(minutes=65)
    strict = open_slots_fn(S)
    assert next(iter(strict(SUN_OPEN, SUN_OPEN + timedelta(hours=2)))) == SUN_OPEN


def test_buy_mirror_of_weekend_continuity():
    fri = [c("5m", FRI + timedelta(minutes=5 * i), 13005, 13015) for i in range(24)]
    sun = [c("5m", SUN_OPEN + timedelta(minutes=5 * i), 13060, 13105) for i in range(3)]
    out = score_journey(plan("BUY"), fri + sun, require_contiguous_m5=True, open_slots=open_slots_fn(S))
    assert out["status"] == "ENTRY_THEN_DESTINATION"


def test_audit_does_not_plan_or_censor_while_the_market_is_shut():
    from types import SimpleNamespace
    from unittest.mock import patch

    from planner.walk_forward import audit

    sat = datetime(2026, 11, 14, 8, tzinfo=UTC)          # Saturday: shut since Friday 22:00 UTC

    class Store:
        def newest(self, tf):
            return SimpleNamespace(end=sat + timedelta(days=7))

        def read_range(self, tf, start, end):
            raise AssertionError("no candles should be read for a closed-market time")

    with patch("planner.walk_forward.plan_at", side_effect=AssertionError("should not plan")):
        result = audit(S, Store(), sat, sat + timedelta(hours=4), timedelta(hours=4), timedelta(hours=24))
    assert result["counts"] == {"MARKET_CLOSED": 1}
