"""Functional safeguards for the offline destination hierarchy."""
from decimal import Decimal
from planner.destination_hierarchy import destination_hierarchy


def test_bearish_hierarchy_preserves_distant_support_without_predicting_it():
    zones = [
        {"low": "13441.9", "high": "13452.9", "class": "Major"},
        {"low": "13328.7", "high": "13337.6", "class": "Major"},
        {"low": "13468.2", "high": "13479.0", "class": "Major"},
    ]
    result = destination_hierarchy("13454.4", zones, "SELL")
    assert [z["low"] for z in result["obstacles"]] == ["13441.9", "13328.7"]
    assert result["forecast"] is None
    assert "do not establish" in result["reason"]


def test_bullish_mirror_and_no_direction():
    zones = [{"low": "13300", "high": "13310", "class": "Major"},
             {"low": "13400", "high": "13410", "class": "Major"}]
    assert [z["low"] for z in destination_hierarchy("13350", zones, "BUY")["obstacles"]] == ["13400"]
    assert destination_hierarchy("13350", zones, "WAIT")["obstacles"] == []


def test_forecast_requires_explicit_independent_probability():
    zones = [
        {"low": "13300", "high": "13310", "class": "Major"},
        {"low": "13330", "high": "13340", "class": "Major", "forecast_probability": Decimal("0.7")},
    ]
    result = destination_hierarchy("13400", zones, "SELL", minimum_reward_pips=Decimal("30"))
    assert result["forecast"]["low"] == "13330"


def test_inverted_zone_rejected():
    import pytest
    with pytest.raises(ValueError, match="inverted"):
        destination_hierarchy("13400", [{"low": "13410", "high": "13400"}], "SELL")
