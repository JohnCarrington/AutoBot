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


def test_invalid_forecast_probability_is_rejected():
    import pytest
    for invalid in ("-0.1", "1.1", "NaN"):
        with pytest.raises(ValueError, match="forecast_probability"):
            destination_hierarchy("13400", [
                {"low": "13330", "high": "13340",
                 "forecast_probability": invalid}
            ], "SELL")


def test_touching_zone_is_not_a_future_destination():
    result = destination_hierarchy("13450", [
        {"low": "13445", "high": "13455", "class": "Major"},
        {"low": "13400", "high": "13410", "class": "Major"},
    ], "SELL")
    assert len(result["obstacles"]) == 1
    assert result["obstacles"][0]["low"] == "13400"


def test_three_tier_targets_are_separate_and_ordered():
    from planner.destination_hierarchy import target_ladder
    zones = [
        {"low": "13440", "high": "13450", "class": "Major"},
        {"low": "13390", "high": "13400", "class": "Major"},
        {"low": "13330", "high": "13340", "class": "Major"},
    ]
    result = target_ladder("13460", zones, "SELL",
        preferred={"low": "13390", "high": "13400", "rationale": "independent H4 thesis"},
        extended={"low": "13330", "high": "13340", "rationale": "conditional breakdown"})
    assert result["immediate"]["low"] == "13440"
    assert result["preferred"]["low"] == "13390"
    assert result["extended"]["low"] == "13330"
    assert len(result["intermediate_obstacles"]) == 1
    assert result["execution_authorised"] is False


def test_no_preferred_target_is_invented():
    from planner.destination_hierarchy import target_ladder
    result = target_ladder("13460", [
        {"low": "13440", "high": "13450", "class": "Major"},
        {"low": "13330", "high": "13340", "class": "Major"},
    ], "SELL")
    assert result["immediate"] is not None
    assert result["preferred"] is None
    assert result["extended"] is None


def test_extended_requires_preferred_and_explicit_rationale():
    from planner.destination_hierarchy import target_ladder
    import pytest
    zones = [{"low": "13440", "high": "13450"},
             {"low": "13330", "high": "13340"}]
    with pytest.raises(ValueError, match="requires a preferred"):
        target_ladder("13460", zones, "SELL",
            extended={"low": "13330", "high": "13340", "rationale": "conditional"})
    with pytest.raises(ValueError, match="evidence rationale"):
        target_ladder("13460", zones, "SELL",
            preferred={"low": "13330", "high": "13340"})


def test_research_preferred_target_uses_structure_without_ema_or_adr_veto():
    from planner.destination_hierarchy import research_target_forecast
    zones = [
        {"low": "13440", "high": "13450", "class": "Major", "evidence": ["H4"]},
        {"low": "13400", "high": "13410", "class": "Major", "evidence": ["H4", "pivot"]},
        {"low": "13350", "high": "13360", "class": "Major", "evidence": ["H4", "daily"]},
    ]
    observations = {"adr_pips": "120", "today_range_pips": "20",
                    "h4_ema_stack": "7 < 13 < 21 (down)"}
    result = research_target_forecast("13460", zones, "SELL", observations,
                                      condition="CORRECTION_ACTIVE")
    assert result["immediate"]["low"] == "13440"
    assert result["preferred"]["low"] == "13350"
    assert result["execution_authorised"] is False
    opposing = dict(observations, h4_ema_stack="7 > 13 > 21 (up)")
    opposed = research_target_forecast("13460", zones, "SELL", opposing,
                                       condition="CORRECTION_ACTIVE")
    assert opposed["preferred"]["low"] == "13350"
    assert opposed["diagnostic"]["ema_alignment"] == "mixed_or_opposed"
    exhausted = dict(observations, today_range_pips="115")
    exhausted_result = research_target_forecast("13460", zones, "SELL", exhausted,
                                                condition="CORRECTION_ACTIVE")
    assert exhausted_result["preferred"]["low"] == "13350"
    assert exhausted_result["diagnostic"]["adr_remaining_pips"] == "5"


def test_research_target_explains_missing_deeper_major():
    from planner.destination_hierarchy import research_target_forecast
    result = research_target_forecast(
        "13460",
        [{"low": "13440", "high": "13450", "class": "Major",
          "evidence": ["H4", "daily"]}],
        "SELL", {"adr_pips": "120", "today_range_pips": "20"},
        condition="CORRECTION_ACTIVE")
    assert result["preferred"] is None
    assert "only one structural obstacle ahead" in result["diagnostic"]["rejections"]
