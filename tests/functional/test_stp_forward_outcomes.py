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
