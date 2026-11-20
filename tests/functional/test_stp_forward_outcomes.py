"""Read-only future-outcome tests: never infer intrabar ordering."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D

from planner.forward_outcomes import score_journey
from prices.model import Candle

T = datetime(2026, 11, 20, 12, tzinfo=timezone.utc)


def candle(n, low, high):
    a, b = D(str(low)), D(str(high))
    return Candle("5m", T + timedelta(minutes=5*n), T + timedelta(minutes=5*(n+1)),
                  a, b, a, b, a, b, a, b)


def plan(direction="SELL"):
    return {
        "as_of_utc": "2026-11-20T12:00:00Z",
        "trade": direction,
        "entry_zone": {"low": "1.3100", "high": "1.3110"} if direction == "SELL" else
                      {"low": "1.3000", "high": "1.3010"},
        "destinations": {"primary": {"zone":
                         {"low": "1.3000", "high": "1.3010"} if direction == "SELL" else
                         {"low": "1.3100", "high": "1.3110"}}},
    }


def test_sell_entry_then_target():
    assert score_journey(plan(), [candle(0, "1.3095", "1.3105"),
                                  candle(1, "1.3005", "1.3090")])["status"] == "ENTRY_THEN_DESTINATION"


def test_buy_entry_then_target():
    assert score_journey(plan("BUY"), [candle(0, "1.3005", "1.3050"),
                                        candle(1, "1.3050", "1.3105")])["status"] == "ENTRY_THEN_DESTINATION"


def test_destination_before_entry_is_not_success():
    assert score_journey(plan(), [candle(0, "1.3005", "1.3050"),
                                  candle(1, "1.3100", "1.3110")])["status"] == "DESTINATION_BEFORE_ENTRY"


def test_same_bar_is_ambiguous_not_success():
    assert score_journey(plan(), [candle(0, "1.3000", "1.3110")])["status"] == "AMBIGUOUS_SAME_CANDLE"


def test_censored_outcomes():
    assert score_journey(plan(), [candle(0, "1.3050", "1.3060")])["status"] == "NEITHER_CENSORED"
    assert score_journey(plan(), [candle(0, "1.3100", "1.3110")])["status"] == "ENTRY_ONLY_CENSORED"


def test_no_entry_plan_is_not_scorable():
    p = plan()
    p["entry_zone"] = None
    assert score_journey(p, [])["status"] == "NOT_SCORABLE"


def test_stale_candle_cannot_change_outcome():
    stale = candle(-1, "1.3000", "1.3110")
    assert score_journey(plan(), [stale, candle(0, "1.3050", "1.3060")])["status"] == "NEITHER_CENSORED"


def hourly(n, low, high):
    a, b = D(str(low)), D(str(high))
    return Candle("1h", T + timedelta(hours=n), T + timedelta(hours=n+1),
                  a, b, a, b, a, b, a, b)


def four_hour(n, low, high):
    a, b = D(str(low)), D(str(high))
    return Candle("4h", T + timedelta(hours=4*n), T + timedelta(hours=4*(n+1)),
                  a, b, a, b, a, b, a, b)


def test_zone_invalidation_before_entry_is_not_success():
    p = plan()
    p["invalidation"] = {"zone_break_close": "1.3120"}
    result = score_journey(p, [hourly(0, "1.3125", "1.3130"),
                               candle(12, "1.3100", "1.3110")])
    assert result["status"] == "STRUCTURE_INVALIDATED_BEFORE_ENTRY"


def test_zone_invalidation_after_entry_is_not_success():
    p = plan()
    p["invalidation"] = {"zone_break_close": "1.3120"}
    result = score_journey(p, [candle(0, "1.3100", "1.3110"),
                               hourly(0, "1.3120", "1.3130"),
                               candle(12, "1.3000", "1.3010")])
    assert result["status"] == "STRUCTURE_INVALIDATED_AFTER_ENTRY"


def test_target_and_invalidation_same_close_is_ambiguous():
    p = plan()
    p["invalidation"] = {"zone_break_close": "1.3120"}
    result = score_journey(p, [candle(0, "1.3100", "1.3110"),
                               hourly(0, "1.3120", "1.3130"),
                               candle(11, "1.3000", "1.3010")])
    assert result["status"] == "AMBIGUOUS_TARGET_OR_INVALIDATION"


def test_buy_invalidation_mirrors_sell():
    p = plan("BUY")
    p["invalidation"] = {"zone_break_close": "1.2990"}
    result = score_journey(p, [candle(0, "1.3000", "1.3010"),
                               hourly(0, "1.2980", "1.2985")])
    assert result["status"] == "STRUCTURE_INVALIDATED_AFTER_ENTRY"


def test_h4_structure_break_uses_h4_close_not_m5():
    p = plan()
    p["invalidation"] = {"structure_break_close": "1.3200"}
    result = score_journey(p, [candle(0, "1.3100", "1.3110"),
                               candle(1, "1.3210", "1.3220"),
                               four_hour(0, "1.3205", "1.3210")])
    assert result["status"] == "STRUCTURE_INVALIDATED_AFTER_ENTRY"


def test_m5_close_alone_does_not_falsely_invalidate_h1_rule():
    p = plan()
    p["invalidation"] = {"zone_break_close": "1.3120"}
    result = score_journey(p, [candle(0, "1.3100", "1.3110"),
                               candle(1, "1.3125", "1.3130"),
                               candle(2, "1.3000", "1.3010")])
    assert result["status"] == "ENTRY_THEN_DESTINATION"


def test_at_entry_now_counts_as_initial_touch_without_retest():
    p = plan()
    p["observations"] = {"conditional_journeys": [{
        "entry": ["1.3100", "1.3110"],
        "countermove_evidence_state": "AT_ENTRY_NOW",
    }]}
    result = score_journey(p, [candle(0, "1.3000", "1.3010")])
    assert result["status"] == "ENTRY_THEN_DESTINATION"
    assert result["entry_at"] == p["as_of_utc"].replace("Z", "+00:00")


def test_at_entry_now_does_not_override_different_candidate():
    p = plan()
    p["observations"] = {"conditional_journeys": [{
        "entry": ["1.3200", "1.3210"],
        "countermove_evidence_state": "AT_ENTRY_NOW",
    }]}
    assert score_journey(p, [candle(0, "1.3000", "1.3010")])["status"] == "DESTINATION_BEFORE_ENTRY"


def test_strict_historical_scoring_censors_missing_five_minute_candles():
    result = score_journey(plan(), [candle(0, "1.3100", "1.3110"),
                                    candle(3, "1.3000", "1.3010")],
                           require_contiguous_m5=True)
    assert result["status"] == "DATA_GAP_CENSORED"


def test_strict_historical_scoring_requires_any_future_m5_coverage():
    assert score_journey(plan(), [], require_contiguous_m5=True)["status"] == "DATA_GAP_CENSORED"


def test_gap_after_completed_journey_does_not_erase_result():
    result = score_journey(plan(), [candle(0, "1.3100", "1.3110"),
                                    candle(1, "1.3000", "1.3010"),
                                    candle(5, "1.3050", "1.3060")],
                           require_contiguous_m5=True)
    assert result["status"] == "ENTRY_THEN_DESTINATION"
