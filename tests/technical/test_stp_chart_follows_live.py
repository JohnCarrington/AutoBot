"""The STP tab's chart follows the current market and the live STP recommendation (owner, 25 November 2026).

Defect (25 November 2026): the page selected the live recommendation itself when it opened; once that one completed
or was replaced, the chart counted it as a "historical review" (dashboard/static/stp/stp.js isHist), stopped
reloading candles and kept drawing the old plan without the historical banner. Historical review now starts only
when the owner chooses a past recommendation in the history table, and lasts until "Back to current".

The real stp.js runs under node (tests/technical/js/stp_chart_harness.js) against a minimal DOM, a stand-in chart
library and the STP API answers the dashboard's own functions gave for 25 November 2026
(tests/technical/js/stp_chart_fixtures.json, made by make_stp_chart_fixtures.py). Read only."""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
JS = ROOT / "dashboard" / "static" / "stp" / "stp.js"
HARNESS = ROOT / "tests" / "technical" / "js" / "stp_chart_harness.js"
F = json.loads((ROOT / "tests" / "technical" / "js" / "stp_chart_fixtures.json").read_text())
NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="node is not installed")

A, B, C, D = (f"STP-GBPUSD-20261125-{x}" for x in ("0400-27", "1000-28", "1200-29", "1400-31"))
PRIMARY = {i: "PRIMARY " + F["recommendation"][i]["at_creation"]["card"]["plan"]["destinations"]["primary"]["text"]
           for i in (A, B, C, D)}


def card(i, status="ACTIVE"):
    c = copy.deepcopy(F["recommendation"][i]["at_creation"]["card"])
    return c | {"status": status, "status_label": status}


def opp_row(i, status="WAITING"):
    c = F["recommendation"][i]["at_creation"]["card"]
    return F["overview"]["opportunities"][0] | {"id": i, "trade": c["trade"], "status": status, "label": status.title(),
                                                "zone": c["entry_zone"], "created_utc": c["created_utc"], "lineage": i}


def ov(live=None, opps=(), price=1.30652, now="2026-11-25T11:40:30Z"):
    o = copy.deepcopy(F["overview"])
    o["price"] = o["price"] | {"price": price, "text": f"{price:.5f}", "time_utc": now}
    o["served_utc"] = now
    o["opportunities"] = [opp_row(i) for i in opps]
    if live:
        o["recommendation"] = card(live)
        o["status"] = {"code": "ACTIVE", "label": "ACTIVE"}
        o["overlays"]["plan"] = o["recommendation"]["plan"]
        o["explanation"] = None
    else:
        o["recommendation"], o["overlays"]["plan"] = None, None
        o["status"] = {"code": "NONE", "label": "NO RECOMMENDATION"}
        o["opportunity_text"] = "NO CURRENT OPPORTUNITY"
        o["explanation"] = {"text": "No live recommendation."}
    return o


def hist(upto, live=()):
    """The history table as the API gives it at a moment: the recommendations created up to `upto` (an id)."""
    order = [A, "STP-GBPUSD-20261125-0000-26", B, C, "STP-GBPUSD-20261125-1200-30", D]
    keep = {i for i in order[:order.index(upto) + 1]} | {"STP-GBPUSD-20261125-0000-26"}
    rows = [r | {"live": r["id"] in live} for r in F["history"]["rows"] if r["id"] in keep]
    return F["history"] | {"rows": rows, "total": len(rows), "pages": 1}


def serve(overview, history, now):
    return {"serve": {"overview": overview, "history": history, "recommendation": F["recommendation"], "now": now}}


def run(steps, js=JS):
    p = Path(__import__("tempfile").mkdtemp()) / "scenario.json"
    p.write_text(json.dumps({"steps": steps}))
    r = subprocess.run([NODE, str(HARNESS), str(js), str(p)], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    snaps = json.loads(r.stdout)
    for s in snaps:
        assert s["errors"] == [], (s["step"], s["errors"])
    return snaps


def live_view(s, rid):
    """The chart shows the current market with `rid`'s plan (or no plan): never a historical review."""
    assert s["banner"] is None and s["review"] is False
    assert "ORIGINAL ENTRY ZONE" not in s["layer_text"]                 # the historical review's label
    if rid:
        assert PRIMARY[rid] in s["plan_labels"], s["plan_labels"]
        assert s["selected"] == rid
        assert [x for x in PRIMARY.values() if x in s["plan_labels"]] == [PRIMARY[rid]]
    else:
        assert s["plan_labels"] == [] and "No live recommendation" in s["legend"]
    assert s["last_candles_url"] and "end=" not in s["last_candles_url"]


def test_C1_a_recommendation_completing_without_a_replacement_leaves_the_live_chart_updating():
    s = run([serve(ov(A, [A]), hist(A, [A]), "2026-11-25T11:40:30Z") | {"name": "open"}, {"mount": True},
             serve(ov(None, (), 1.30610, "2026-11-25T12:50:30Z"), hist(A), "2026-11-25T12:50:30Z"), {"tick": True},
             serve(ov(None, (), 1.30621, "2026-11-25T13:50:30Z"), hist(A), "2026-11-25T13:50:30Z"), {"tick": True}])
    opened, done1, done2 = s[1], s[3], s[5]
    live_view(opened, A)
    live_view(done1, None)
    live_view(done2, None)
    assert done1["selected"] is None and done1["auto_id"] == A          # shown quietly in the lifecycle panel only
    assert opened["last_candle_t"] < done1["last_candle_t"] < done2["last_candle_t"]   # candles keep coming
    assert done1["price_lines"] == [1.3061] and done2["price_lines"] == [1.30621]       # and the price


def test_C2_a_recommendation_replaced_by_a_new_one_moves_the_chart_to_the_new_plan():
    s = run([serve(ov(B, [B]), hist(B, [B]), "2026-11-25T11:00:30Z"), {"mount": True},
             serve(ov(C, [C]), hist(C, [C]), "2026-11-25T12:05:30Z"), {"tick": True}])
    live_view(s[1], B)
    live_view(s[3], C)
    assert s[3]["last_candle_t"] > s[1]["last_candle_t"]


def test_C3_simultaneous_buy_and_sell_opportunities_the_chart_follows_the_live_recommendation():
    s = run([serve(ov(C, [C, B]), hist(C, [C, B]), "2026-11-25T12:10:30Z"), {"mount": True},
             serve(ov(D, [D, C]), hist(D, [D, C]), "2026-11-25T14:00:30Z"), {"tick": True},
             serve(ov(C, [C]), hist(D, [C]), "2026-11-25T14:30:30Z"), {"tick": True}])
    live_view(s[1], C)
    assert sorted(r[1] for r in s[1]["opportunity_rows"]) == ["BUY", "SELL"]
    live_view(s[3], D)                                                    # the newest live one (planner's slot)
    assert sorted(r[1] for r in s[3]["opportunity_rows"]) == ["BUY", "SELL"]
    live_view(s[5], C)                                                    # D gone, C still live: back to C


def test_C4_a_new_recommendation_after_a_period_with_none_is_drawn_at_the_next_refresh():
    s = run([serve(ov(None), hist(C), "2026-11-25T12:50:30Z"), {"mount": True},
             serve(ov(None, (), 1.30621, "2026-11-25T13:50:30Z"), hist(C), "2026-11-25T13:50:30Z"), {"tick": True},
             serve(ov(D, [D], 1.30630, "2026-11-25T14:00:30Z"), hist(D, [D]), "2026-11-25T14:00:30Z"), {"tick": True}])
    live_view(s[1], None)
    live_view(s[3], None)
    assert s[3]["last_candle_t"] > s[1]["last_candle_t"] and s[3]["price_lines"] == [1.30621]
    live_view(s[5], D)
    assert s[5]["price_lines"] == [1.3063]


def test_C5_a_chosen_historical_review_stays_until_back_to_current():
    s = run([serve(ov(D, [D]), hist(D, [D]), "2026-11-25T14:05:30Z"), {"mount": True},
             {"click_row": A},
             serve(ov(None, (), 1.30700, "2026-11-25T14:15:30Z"), hist(D), "2026-11-25T14:15:30Z"), {"tick": True},
             {"tick": True},
             {"click": "Back to current"}])
    live_view(s[1], D)
    rev = s[2]
    assert rev["review"] is True and rev["selected"] == A
    assert rev["banner"].startswith("Historical review: " + A) and "Back to current" in rev["banner"]
    assert PRIMARY[A] in rev["plan_labels"] and "ORIGINAL ENTRY ZONE 1.30841–1.30930 · SELL" in rev["plan_labels"]
    assert rev["price_lines"] == []                                      # no live price line on a past plan
    assert "end=" in rev["last_candles_url"]                             # the review's own candle range
    for kept in (s[4], s[5]):                                            # refreshes never leave the review
        assert kept["review"] is True and kept["banner"] == rev["banner"] and PRIMARY[A] in kept["plan_labels"]
        assert kept["candle_fetches"] == rev["candle_fetches"]
    back = s[6]
    live_view(back, None)                                                # the current view: no live rec now
    assert back["candle_fetches"] > rev["candle_fetches"] and back["price_lines"] == [1.307]   # live candles again


def test_C6_past_recs_reset_view_and_back_to_current():
    s = run([serve(ov(None), hist(D), "2026-11-25T13:50:30Z"), {"mount": True},
             {"click": "Past recs"}, {"click": "Past recs"},
             {"click": "Reset view"},
             {"click_row": C}, {"click": "Reset view"}, {"click": "Past recs"},
             {"click": "Back to current"}, {"click": "Past recs"}])
    n = len(hist(D)["rows"])
    live_view(s[1], None)
    assert len(s[1]["markers"]) == n                                     # past recommendations marked (on by default)
    assert s[2]["markers"] == [] and len(s[3]["markers"]) == n           # off, on
    reset = s[4]                                                         # Reset view with no live recommendation:
    live_view(reset, None)                                               # re-fits the live chart, no review
    assert reset["fit_calls"] > s[3]["fit_calls"]
    rev = s[5]
    assert rev["review"] and rev["banner"].startswith("Historical review: " + C)
    assert set(rev["markers"]) >= {"created", "completed"}               # the chosen one's lifecycle
    assert s[6]["review"] and s[6]["banner"] == rev["banner"] and "end=" in s[6]["last_candles_url"]
    assert s[7]["review"] and set(s[7]["markers"]) >= {"created", "completed"}   # Past recs does not end a review
    live_view(s[8], None)
    assert s[8]["markers"] == []                                         # Past recs stays as last chosen (off)
    assert len(s[9]["markers"]) == n


def test_C7_the_old_script_froze_the_chart_on_the_ended_recommendation(tmp_path):
    """The defect itself, on the script as deployed at b2d4123 (kept here as text so the test needs no git)."""
    import subprocess as sp
    old = sp.run(["git", "-C", str(ROOT), "show", "b2d4123:dashboard/static/stp/stp.js"], capture_output=True, text=True)
    if old.returncode != 0:
        pytest.skip("b2d4123 is not in this checkout")
    p = tmp_path / "stp_b2d4123.js"
    p.write_text(old.stdout)
    s = run([serve(ov(A, [A]), hist(A, [A]), "2026-11-25T11:40:30Z"), {"mount": True},
             serve(ov(None, (), 1.30621, "2026-11-25T13:50:30Z"), hist(A), "2026-11-25T13:50:30Z"), {"tick": True}], js=p)
    frozen = s[3]
    assert PRIMARY[A] in frozen["plan_labels"] and frozen["banner"] is None           # old plan, no banner
    assert frozen["candle_fetches"] == s[1]["candle_fetches"]                         # candles no longer reloaded
