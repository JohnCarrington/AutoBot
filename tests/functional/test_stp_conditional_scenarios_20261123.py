"""Read-only directional scenario projection: no broker, no changes to legacy winner."""
from decimal import Decimal
from types import SimpleNamespace

from planner.technical import BUY, SELL, REVERSAL, BREAKOUT, Opportunity, conditional_scenarios


def _candidate(direction, score):
    o = Opportunity(REVERSAL, direction, Decimal("13075"), Decimal("13084"),
                    "previous week low", Decimal("13020"), "below support",
                    Decimal("13017"), "H1 close below structural invalidation")
    o.evidence = [(1, f"evidence {i}") for i in range(score)]
    o.target1 = (Decimal("13100") if direction == BUY else Decimal("13040"), "next zone")
    return o


def test_both_directions_are_retained_without_requiring_h4_agreement():
    settings = SimpleNamespace(market=SimpleNamespace())
    # _opp_dict needs the real pip settings, so use an isolated projection stub.
    import planner.technical as technical
    original = technical._opp_dict
    technical._opp_dict = lambda s, o, p, a: {"trade": o.trade, "entry_zone": {"basis": o.entry_basis}}
    try:
        scenarios = conditional_scenarios(settings, [_candidate(SELL, 5), _candidate(BUY, 3)],
                                          Decimal("13080"), Decimal("100"), 4)
    finally:
        technical._opp_dict = original
    assert scenarios[SELL]["state"] == "WAITING_FOR_CONFIRMATION"
    assert scenarios[BUY]["state"] == "INSUFFICIENT_EVIDENCE"
    assert scenarios[BUY]["score"] == 3
    assert scenarios[BUY]["candidate"]["entry_zone"]["basis"] == "previous week low"
    assert scenarios[BUY]["observe_only"] is True


def test_no_candidate_never_invents_a_trade():
    scenarios = conditional_scenarios(None, [], Decimal("13080"), Decimal("100"), 4)
    assert all(scenarios[d]["state"] == "INSUFFICIENT_EVIDENCE" for d in (BUY, SELL))
    assert all(scenarios[d]["candidate"] is None for d in (BUY, SELL))
