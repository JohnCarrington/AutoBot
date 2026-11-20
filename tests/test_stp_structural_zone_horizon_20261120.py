"""Regression: structural destinations must not be clipped by the round-number radius."""
from decimal import Decimal
from types import SimpleNamespace

from planner.zones import MAJOR, MapLevel, zones


def test_major_support_outside_150_pips_is_retained():
    settings = SimpleNamespace(
        market=SimpleNamespace(points_per_pip=1),
        levels=SimpleNamespace(line_up_within_pips=5, round_numbers_within_pips=150),
        planner=SimpleNamespace(zone_width_adr_share=0.15, major_min_families=3, moderate_min_families=2),
    )
    # Spot 13110; support 12940 is 170 pips away. Three distinct
    # families, including a daily level, make this a Major zone.
    support = [
        MapLevel(Decimal("12940"), "daily S2", "pivot", "daily", "daily R/S", None, True, True),
        MapLevel(Decimal("12941"), "prior session low", "session", "intraday", "session high/low", None, False, True),
        MapLevel(Decimal("12942"), "daily swing low", "higher-timeframe structure", "daily", "daily swing", None, True, True),
    ]
    found = zones(settings, support, Decimal("60"), [], Decimal("13110"))
    assert len(found) == 1
    assert found[0].klass == MAJOR
    assert found[0].low == Decimal("12940")
    assert found[0].high == Decimal("12942")


def test_nearby_zone_still_retained():
    settings = SimpleNamespace(
        market=SimpleNamespace(points_per_pip=1),
        levels=SimpleNamespace(line_up_within_pips=5, round_numbers_within_pips=150),
        planner=SimpleNamespace(zone_width_adr_share=0.15, major_min_families=3, moderate_min_families=2),
    )
    level = MapLevel(Decimal("13100"), "daily pivot", "pivot", "daily", "daily pivot", None, True, True)
    found = zones(settings, [level], Decimal("20"), [], Decimal("13110"))
    assert len(found) == 1
    assert found[0].low == Decimal("13100")
