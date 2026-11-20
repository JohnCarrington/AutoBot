"""Forward target scoring functional tests: no trades, no hindsight."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from decimal import Decimal

from planner.target_outcomes import score_target_ladder


def candle(at, low, high):
    return SimpleNamespace(timeframe="5m", start=at, end=at + timedelta(minutes=5),
                           sell_low=Decimal(str(low)), sell_high=Decimal(str(high)))


def test_preferred_reached_after_immediate_without_claiming_trade():
    t = datetime(2026, 11, 10, 9, tzinfo=timezone.utc)
    ladder = {
        "immediate": {"low": "13420", "high": "13430"},
        "preferred": {"low": "13350", "high": "13360"},
        "extended": None,
    }
    candles = [candle(t, 13420, 13460),
               candle(t + timedelta(minutes=5), 13355, 13425)]
    result = score_target_ladder(ladder, candles, t, "SELL")
    assert result["targets"]["immediate"]["status"] == "REACHED"
    assert result["targets"]["preferred"]["status"] == "REACHED"
    assert result["targets"]["extended"]["status"] == "NOT_FORECAST"


def test_data_gap_censors_unreached_targets():
    t = datetime(2026, 11, 10, 9, tzinfo=timezone.utc)
    ladder = {"immediate": {"low": "13420", "high": "13430"}}
    result = score_target_ladder(ladder, [candle(t + timedelta(minutes=5), 13420, 13430)],
                                 t, "SELL")
    assert result["status"] == "DATA_GAP_CENSORED"
    assert result["targets"]["immediate"]["status"] == "DATA_GAP_CENSORED"
