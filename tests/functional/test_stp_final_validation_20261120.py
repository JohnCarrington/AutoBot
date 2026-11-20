"""STP final correction and validation (owner's brief, 20 November 2026), items 1-10.

Discovery and destination selection are separate. Historical daily swings are discovered at any distance from price
(9210ca5 plus the structural-history levels). The primary destination is still the first Major zone beyond the entry
zone (D-18/D-19). No distance or ADR limit applies to it ("ADR never rules a zone out", FC-03). Its distance is now
recorded as context only. The "no Major zone" reason no longer mentions a 150-pip window, which stopped applying with
9210ca5.

The five Version B recommendations (12 May 2025 12:00, 16:00 and 20:00; 18 May 2026 16:00 and 20:00, destinations
162-214 pips away) are reproduced on the research store. The real keeper is replayed on the 18 May 2026 one to show
what the lifecycle did with it. Tests on the real stores skip where those stores are absent.
"""
import ast
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path

import pytest

from planner.measure import pips, ppp
from planner.zones import HTF_STRUCTURE, MAJOR, MODERATE, classify
from tests.functional.test_planner_scenarios import S
from tests.planner_helpers import Over, section

UTC = timezone.utc
ROOT = Path(__file__).resolve().parents[2]
RESEARCH = Path("/opt/autobot/data/research/stp_validation_store/GBPUSD")
OFF = Over(S, planner=section(S.planner, historical_daily_swing_lookback_weeks=0))   # Version B (retention only)

# as_of -> (entry low, entry high, primary low, primary high), from the 20 Nov evaluation rows (B and C agree)
FIVE = {
    datetime(2025, 5, 12, 12, 0, 4, tzinfo=UTC): ("13200", "13211.7", "13009.6", "13014.4"),
    datetime(2025, 5, 12, 16, 0, 4, tzinfo=UTC): ("13200", "13214.9", "13009.6", "13014.4"),
    datetime(2025, 5, 12, 20, 0, 4, tzinfo=UTC): ("13200", "13214.9", "13009.6", "13014.4"),
    datetime(2026, 5, 18, 16, 0, 4, tzinfo=UTC): ("13426.6", "13438.0", "13206.1", "13215.7"),
    datetime(2026, 5, 18, 20, 0, 4, tzinfo=UTC): ("13429.4", "13438.0", "13206.1", "13215.7"),
}


def _store(folder):
    from prices.store import CandleStore
    if not (Path(folder) / "1d").is_dir():
        pytest.skip("this candle store is only on the server")
    return CandleStore(folder, S.candles.compress_after_days)


def _plan(settings, store, t):
    from planner.assess import plan_at
    return plan_at(settings, store, t, calendar=[]).as_dict()


def _between_entry_and_primary(p):
    lo, hi = D(p["destinations"]["primary"]["zone"]["high"]), D(p["entry_zone"]["low"])
    return [z for z in p["structure"]["zones"] if D(z["low"]) > lo and D(z["high"]) < hi]


@pytest.fixture(scope="module")
def research():
    return _store(RESEARCH)


@pytest.fixture(scope="module")
def five_plans(research):
    return {t: (_plan(OFF, research, t), _plan(S, research, t)) for t in FIVE}


# ---- 1. historical levels are discovered, also beyond the old 150-pip window ----------------------------------------

def test_1_historical_daily_swings_are_discovered_beyond_the_old_150_pip_window(five_plans):
    t = datetime(2026, 5, 18, 16, 0, 4, tzinfo=UTC)
    off, on = five_plans[t]
    prim = on["destinations"]["primary"]["zone"]["levels"]
    assert any(x.startswith("historical daily swing high 13207.3") for x in prim)
    assert not any("historical" in x for x in off["destinations"]["primary"]["zone"]["levels"])
    assert D(on["observations"]["primary_distance_pips"]) > 150                    # outside the old window


# ---- 2. direction and condition are unchanged by the historical levels -----------------------------------------------

def test_2_direction_and_condition_are_identical_with_and_without_history(five_plans):
    for t, (off, on) in five_plans.items():
        assert (off["dominant_direction"], off["condition"]) == (on["dominant_direction"], on["condition"]), t
        assert on["dominant_direction"] == "BEARISH"


# ---- 3. Major-zone confluence is still required ----------------------------------------------------------------------

def test_3_major_needs_enough_families_and_a_daily_or_weekly_level():
    p = S.planner
    many = {f"family{i}" for i in range(p.major_min_families)}
    assert classify(S, many, daily_or_weekly=True) == MAJOR
    assert classify(S, many, daily_or_weekly=False) != MAJOR                     # confluence without HTF: not Major
    assert classify(S, set(sorted(many)[1:]), daily_or_weekly=True) != MAJOR     # one family short: not Major
    assert classify(S, {HTF_STRUCTURE}, daily_or_weekly=True) != MAJOR          # a historical swing alone


def test_3b_the_moderate_zones_on_the_way_are_never_taken_as_the_primary(five_plans):
    for t, (off, on) in five_plans.items():
        for p in (off, on):
            assert p["destinations"]["primary"]["zone"]["class"] == MAJOR
            inside = _between_entry_and_primary(p)
            assert inside and all(z["class"] != MAJOR for z in inside), t
            assert any(z["class"] == MODERATE for z in inside)


# ---- 4. the primary destination is structurally valid ----------------------------------------------------------------

def test_4_the_primary_is_major_beyond_the_entry_zone_ahead_of_price_and_not_reached(five_plans):
    for t, (_, on) in five_plans.items():
        prim, ez = on["destinations"]["primary"], on["entry_zone"]
        assert prim["zone"]["class"] == MAJOR
        assert D(prim["zone"]["high"]) < D(ez["low"])                              # a sell's target is below the zone
        assert on["invalidation"]["destination_first_applies"] is True            # wholly beyond price, not touched
        assert on["destination_reached"] is None and on["no_recommendation"] is None


# ---- 5. an already-reached destination is refused (D-1) --------------------------------------------------------------

def test_5_an_already_reached_primary_is_refused_on_18_november_0600():
    st = _store(S.candles.folder)
    p = _plan(S, st, datetime(2026, 11, 18, 6, 0, 3, tzinfo=UTC))
    assert p["entry_zone"] is None and p["destination_reached"] is not None
    assert p["no_recommendation"].startswith("the primary destination 13189.7 is already reached")


# ---- 6. the lifecycle handles a far destination by the existing rules ------------------------------------------------

def test_6_the_keeper_updates_then_supersedes_the_18_may_2026_far_destination(research, tmp_path):
    from planner.keeper import Keeper
    s = Over(OFF, planner=section(OFF.planner, folder=tmp_path))
    t = datetime(2026, 5, 18, 16, 0, 3, tzinfo=UTC)
    while t <= datetime(2026, 5, 19, 0, 5, tzinfo=UTC):
        Keeper(s, research).run(t)
        t += timedelta(minutes=5)
    import json
    ev = [json.loads(x) for x in (tmp_path / "GBPUSD" / "recommendations.jsonl").read_text().splitlines()]
    first = [e for e in ev if e.get("id") == "STP-GBPUSD-20260518-1600-1"]
    kinds = [e["event"] for e in first]
    assert kinds[0] == "created" and "active" in kinds
    assert any(e["event"] == "changed" and "primary destination 13215.7 to 13401.6" in e["why"] for e in first)
    assert kinds[-1] == "superseded" and "invalidated" not in kinds and "completed" not in kinds
    assert sum(1 for e in ev if e["event"] == "created") == 2                      # one successor, no duplicates


# ---- 7. the five Version B recommendations -------------------------------------------------------------------------

def test_7_the_five_are_reproduced_and_their_distance_is_recorded_as_context_only(five_plans):
    for t, want in FIVE.items():
        for p in five_plans[t]:
            got = (p["entry_zone"]["low"], p["entry_zone"]["high"],
                   p["destinations"]["primary"]["zone"]["low"], p["destinations"]["primary"]["zone"]["high"])
            assert got == want, t
            o = p["observations"]
            assert 160 <= D(o["primary_distance_pips"]) <= 215 and D(o["primary_distance_adr"]) > 1
            assert len(p["invalidation"]["conditions"]) == 4


def test_7b_the_no_major_reason_no_longer_mentions_the_removed_150_pip_window():
    src = (ROOT / "planner/assess.py").read_text()
    assert "pip window for the primary destination" not in src
    assert "the entry zone for the primary destination" in src


# ---- 8. the successful November recommendations are unchanged ---------------------------------------------------------

@pytest.mark.parametrize("t, entry, primary", [
    (datetime(2026, 11, 18, 21, 0, 3, tzinfo=UTC), ("13148", "13158.5"), "13140.2"),
    (datetime(2026, 11, 19, 12, 0, 3, tzinfo=UTC), ("13148", "13158.5"), "13139.9"),
    (datetime(2026, 11, 19, 14, 0, 3, tzinfo=UTC), ("13148", "13158.5"), "13143.7"),
])
def test_8_november_recommendations_that_reached_their_destination_are_still_issued_the_same(t, entry, primary):
    st = _store(S.candles.folder)
    for s in (OFF, S):
        p = _plan(s, st, t)
        assert p["trade"] == "SELL" and p["no_recommendation"] is None
        assert (p["entry_zone"]["low"], p["entry_zone"]["high"]) == entry
        assert p["destinations"]["primary"]["price"] == primary


def test_8b_the_20_november_0800_missing_recommendation_stays_resolved():
    st = _store(S.candles.folder)
    p = _plan(S, st, datetime(2026, 11, 20, 8, 0, 4, tzinfo=UTC))
    assert p["trade"] == "SELL" and p["no_recommendation"] is None
    assert p["destinations"]["primary"]["price"] == "13084.1"


# ---- 9. GBP/USD pip and price conversions ---------------------------------------------------------------------------

def test_9_one_point_is_one_pip_and_the_recorded_distance_is_price_minus_primary(five_plans):
    assert ppp(S) == 1 and pips(S, D("176.6")) == D("176.6")
    off, _ = five_plans[datetime(2026, 5, 18, 16, 0, 4, tzinfo=UTC)]
    o = off["observations"]
    assert D(o["primary_distance_pips"]) == D("13417.1") - D("13215.7")            # 201.4
    assert D(o["primary_distance_adr"]) == (D("201.4") / D(o["adr_pips"])).quantize(D("0.01"))


# ---- 10. STP stays observational ------------------------------------------------------------------------------------

FORBIDDEN = ("ig", "orders", "trading", "trade_manager", "strategies", "safety", "requests")


def test_10_the_planner_imports_no_broker_or_trading_code_and_plans_carry_no_order():
    for f in sorted((ROOT / "planner").glob("*.py")):
        tree = ast.parse(f.read_text())
        mods = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module} | \
               {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        assert not [m for m in mods if m.split(".")[0] in FORBIDDEN], (f.name, mods)


def test_10b_a_plan_has_no_order_size_or_stop_fields(five_plans):
    _, on = next(iter(five_plans.values()))
    assert not {"size", "stake", "stop", "limit", "order", "deal_id"} & set(on)
