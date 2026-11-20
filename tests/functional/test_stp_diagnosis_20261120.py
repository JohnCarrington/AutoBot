"""STP diagnosis, 20 November 2026: the regression tests for what the diagnosis found.

1. The live STP was not stuck: it re-planned every hour, wrote current.json and recommendations.jsonl and the dashboard
   served it, but every hour since 18 November 03:00 ended without a recommendation for a stated reason. From 19
   November 16:00 the reason was "no Major support zone below the entry zone": price had made its lowest level in more
   than 48 weeks, so no retained daily swing lay below it (planner.daily_swing_lookback_weeks = 48, approved P-B9).
   These tests pin that this situation is REPORTED every hour (fresh analysis, direction, reason, structural map) and
   delivered to the dashboard as a current "no recommendation" with the planner's reason, never a silent stop and never
   an invented recommendation.
2. A real dashboard defect: in the planner's sentences the second price of a range written with a hyphen
   ("13135.5-13139.9") was left in IG points, so the STP tab showed "1.31355-13139.9". Both ends are now converted.
"""
import json
from datetime import timedelta
from pathlib import Path

from dashboard import stp
from planner.keeper import Keeper
from tests.functional.test_planner_scenarios import START, S, at_end
from tests.planner_helpers import market, with_folder
from tests.stp_fixtures import NOW, Scenario, plan_dict, settings

# The live planner's own sentence from the 19 November 2026 15:00 UTC analysis (current.json, read only).
LIVE_D1 = ("the primary destination 13139.9 is already reached (the Thu 19 Nov 14:55 GMT 5-minute candle reached 13137.4, "
           "within 3 pips of the destination zone 13135.5-13139.9); no recommendation is issued for a destination price "
           "has already reached (D-1 correction), so the zone 13148-13158.5 is not recommended")


# ---- 2. the dashboard's price notation --------------------------------------------------------------------------

def test_both_ends_of_a_hyphenated_price_range_are_written_in_gbpusd_notation(tmp_path):
    p = stp.Prices(settings(tmp_path))
    out = p.text(LIVE_D1)
    assert "1.31355-1.31399" in out and "1.31480-1.31585" in out
    assert "13139.9" not in out and "13158.5" not in out                       # no IG points left anywhere
    assert "1.31399 is already reached" in out and "reached 1.31374" in out and "14:55 GMT" in out


def test_minus_signs_dates_times_and_counts_are_still_left_alone(tmp_path):
    p = stp.Prices(settings(tmp_path))
    s = "slope -19.8 pips, MACD -20.15, 2026-11-20T08:00:00Z, 466 of 592 candles, 13:05, -13100 stays"
    assert p.text(s) == s
    assert p.text("zone 13193.2–13202.5") == "zone 1.31932–1.32025"            # the en dash, as before


def test_the_overview_shows_the_live_d1_reason_with_both_prices_converted(tmp_path):
    sc = Scenario(tmp_path)
    sc.run(NOW, [plan_dict(no_rec=LIVE_D1)])
    reason = stp.overview(sc.s, sc.now)["explanation"]["planner_reason"]
    assert "zone 1.31355-1.31399" in reason and "the zone 1.31480-1.31585 is not recommended" in reason


# ---- 1. a fresh extreme with no Major zone beyond it: reported every hour, never a silent stop ---------------------

def _fresh_low_market():
    """test_13b's market: only a downtrend, so price ends at a fresh low with nothing retained below it."""
    w, h, p = [(0, 13900)], 0, 13900
    for _ in range(18):
        h += 22; p -= 110; w.append((h, p)); h += 14; p += 55; w.append((h, p))   # noqa: E702
    return market(S, START, w + [(h + 14, p - 70), (h + 28, p - 140)])


def test_at_a_fresh_low_the_planner_still_forecasts_direction_and_structure_and_states_why_there_is_no_recommendation():
    store = _fresh_low_market()
    _, plan = at_end(store)
    assert plan["dominant_direction"] == "BEARISH" and plan["trade"] == "SELL"            # the forecast is kept
    assert plan["entry_zone"] is None and plan["destinations"] == {}                       # nothing invented
    assert plan["no_recommendation"].startswith("no Major support zone below the entry zone")
    assert plan["direction_evidence"] and plan["condition_evidence"]
    zones = plan["structure"]["zones"]                                                     # structural context kept
    assert zones and all(z["class"] != "Major" for z in zones if float(z["high"]) < float(plan["candidates"][0]["low"]))


def test_hour_after_hour_the_keeper_rewrites_the_analysis_and_the_dashboard_shows_it_as_current(tmp_path):
    store = _fresh_low_market()
    end = store.by_tf["1h"][-1].end
    s = with_folder(S, tmp_path / "planner")
    s_dash = settings(tmp_path)                       # the dashboard's settings, on the same planner folder
    s_dash.planner = s.planner
    hours = [end - timedelta(hours=2), end - timedelta(hours=1), end]
    for t in hours:
        Keeper(s, store, calendar=[]).run(t + timedelta(seconds=4))
        st = json.loads((Path(s.planner.folder) / "GBPUSD" / "current.json").read_text())
        assert st["last_analysis_utc"].startswith(t.strftime("%Y-%m-%dT%H:%M"))        # re-analysed, not stuck
        assert st["recommendation"] is None and st["data_fresh"] is True
        assert st["last_plan"]["dominant_direction"] == "BEARISH" and st["last_plan"]["no_recommendation"]
    analyses = [json.loads(x) for x in (Path(s.planner.folder) / "GBPUSD" / "recommendations.jsonl").read_text().splitlines()]
    assert [a["time_utc"][:16] for a in analyses if a["event"] == "analysis"] == [t.strftime("%Y-%m-%dT%H:%M") for t in hours]
    o = stp.overview(s_dash, end + timedelta(minutes=5))
    assert o["freshness"]["state"] in ("CURRENT", "MARKET_CLOSED") and o["freshness"]["last_analysis_utc"] == st["last_analysis_utc"]
    assert o["status"]["label"] == "NO RECOMMENDATION" and o["forecast"]["dominant_direction"] == "BEARISH"
    assert o["explanation"]["scenario"] == "A"
    assert o["explanation"]["planner_reason"].startswith("no Major support zone below the entry zone")
    assert o["overlays"]["zones"]                                                         # the structure is still drawn
