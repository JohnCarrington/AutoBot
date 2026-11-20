"""Research-only preferred destination: no arbitrary ADR exclusion."""
from planner.destination_hierarchy import research_target_forecast


def test_preferred_can_be_beyond_one_and_half_adr():
    zones = [
        {"low": "13060", "high": "13062", "class": "Moderate", "evidence": ["pivot", "session"]},
        {"low": "12910", "high": "12912", "class": "Major", "evidence": ["pivot", "higher-timeframe structure", "session"]},
        {"low": "12840", "high": "12842", "class": "Major", "evidence": ["pivot", "higher-timeframe structure", "psychological"]},
    ]
    result = research_target_forecast(
        "13110", zones, "SELL",
        {"adr_pips": "65", "today_range_pips": "45", "h4_ema_stack": "down"},
        condition="CORRECTION_ACTIVE",
    )
    assert result["research_status"] == "candidate_generated"
    assert result["immediate"]["high"] == "13062"
    assert result["preferred"]["high"] == "12912"  # 198 pips away, > 1.5 * 65
    assert result["extended"]["high"] == "12842"
    assert result["preferred"]["status"] == "uncalibrated_research_hypothesis"
    assert result["execution_authorised"] is False


def test_no_preferred_without_multifamily_major():
    zones = [
        {"low": "13080", "high": "13082", "class": "Minor", "evidence": ["pivot"]},
        {"low": "12900", "high": "12902", "class": "Moderate", "evidence": ["pivot", "session"]},
    ]
    result = research_target_forecast(
        "13110", zones, "SELL", {"adr_pips": "65"}, condition="CORRECTION_ACTIVE"
    )
    assert result["preferred"] is None
    assert result["execution_authorised"] is False
