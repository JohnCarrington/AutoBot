"""The three STP corrections approved by the owner on 19 November 2026 (research: /home/autobot/research/
stp_targeted_20261119/):
  1. candidate C: observed swings vs the confirmed 4-hour structure (planner/structure.py dominant_structure);
  2. an unclassified condition keeps a live recommendation, but never issues a new one (planner/keeper.py);
  3. no duplicate of a completed recommendation (same FC-05 identity and primary destination) (planner/keeper.py).
Prices in points (GBPUSD: 1 point = 1 pip). Everything runs in memory or in pytest's tmp_path."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path

from dashboard import stp
from planner.assess import BEARISH, BULLISH, NEUTRAL, TRANSITIONAL, direction
from planner.keeper import ACTIVE, COMPLETED, INVALIDATED, WAITING
from planner.structure import DOWN, MIXED, UP, dominant_structure, structure, swings
from prices.model import Candle
from tests.stp_fixtures import SCENARIOS
from tests.technical.test_planner import NOW, C, K, S, Script, flat_store, history, plan_dict

UTC = timezone.utc
DATA = Path(__file__).resolve().parents[1] / "candles" / "gbpusd_4h_20261026_20261119.json"


def _legs(points, start=datetime(2026, 9, 7, tzinfo=UTC)):
    """4-hour candles walking straight between the given prices, 6 candles a leg (exact decimals)."""
    out, t = [], start
    for a, b in zip(points, points[1:]):
        a, b = D(str(a)), D(str(b))
        for k in range(6):
            o = a + (b - a) * k / 6
            c = a + (b - a) * (k + 1) / 6
            out.append(C("4h", t, 4, o, max(o, c) + 1, min(o, c) - 1, c))
            t += timedelta(hours=4)
    return out


def _then(cs, *ohlc):
    """Append 4-hour candles with the given (open, high, low, close)."""
    out, t = list(cs), cs[-1].end
    for o, h, l, c in ohlc:
        out.append(C("4h", t, 4, o, h, l, c))
        t += timedelta(hours=4)
    return out


def _mirror(cs, axis=D(27000)):
    """The same market upside down (prices reflected about `axis`): highs become lows."""
    return [C("4h", c.start, 4, axis - c.sell_open, axis - c.sell_low, axis - c.sell_high, axis - c.sell_close) for c in cs]


# A down structure: swing highs 13461 then 13401, swing lows 13339 then 13279; then a rally whose top candle's high
# is 13404 (3 pips above 13401) but which closes at 13403 (2 pips above: no confirmed close), then a 53-pip fall.
DOWN_TREND = [13500, 13400, 13460, 13340, 13400, 13280]
SWEEP = DOWN_TREND + [13403, 13350]


def _dir(cs):
    found = swings(S, cs, "4h")
    st = dominant_structure(S, cs, "4h", found)
    return direction(S, st)[0], st, structure(S, cs, "4h", found)


# ---- 1. candidate C: the structure ------------------------------------------------------------------------------

def test_an_unresolved_wick_sweep_is_neutral_with_its_reason_and_the_observed_swings_are_kept():
    cs = _legs(SWEEP)
    d, st, observed = _dir(cs)
    assert observed.sequence == MIXED and [s.price for s in observed.highs] == [D(13401), D(13404)]
    assert d == NEUTRAL and st.sequence == MIXED and st.sweep["state"] == "unresolved"
    assert st.sweep["price"] == "13404" and st.sweep["beyond"] == "13401" and st.sweep["resolve_beyond"] == "13279"
    assert "sweep unresolved" in st.why and [s.price for s in st.highs] == [D(13401), D(13404)]   # swings as found


def test_a_confirmed_close_beyond_the_last_low_before_the_sweep_rejects_it_and_restores_the_trend():
    cs = _then(_legs(SWEEP), (13350, 13351, 13300, 13310), (13310, 13311, 13270, 13276))      # close 13276 = 13279 - 3
    d, st, observed = _dir(cs)
    assert observed.sequence == MIXED                                                          # observed unchanged
    assert d == BEARISH and st.sequence == DOWN and st.sweep["state"] == "rejected"
    assert st.highs[-1].price == D(13404)                    # the sweep stays the last swing high (impulse start)
    assert "the sweep was rejected" in st.why


def test_a_rejecting_close_needs_the_full_3_pips():
    cs = _then(_legs(SWEEP), (13350, 13351, 13300, 13310), (13310, 13311, 13270, D("13276.1")))  # 2.9 pips beyond
    d, st, _ = _dir(cs)
    assert d == NEUTRAL and st.sweep["state"] == "unresolved"


def test_a_close_3_pips_above_the_previous_high_is_a_real_higher_high_and_the_mixed_structure_stands():
    exactly = _legs(DOWN_TREND + [13404, 13350])            # top candle closes 13404 = 13401 + 3: confirmed
    d, st, _ = _dir(exactly)
    assert d == NEUTRAL and st.sweep is None and st.why.startswith("mixed")
    short = _legs(DOWN_TREND + [D("13403.9"), 13350])        # closes 2.9 above: still a wick-only sweep
    assert _dir(short)[1].sweep["state"] == "unresolved"


def test_a_confirmed_close_above_the_swept_high_after_a_rejection_ends_the_restored_trend():
    rejected = _then(_legs(SWEEP), (13350, 13351, 13300, 13310), (13310, 13311, 13270, 13276))
    assert _dir(rejected)[0] == BEARISH
    back_up = _then(rejected, (13276, 13330, 13275, 13325), (13325, 13406, 13320, 13404))   # close 13404 = 13401 + 3
    d, st, _ = _dir(back_up)
    assert d == NEUTRAL and st.sweep is None                 # the direction is no longer BEARISH: FC-10 invalidates


def test_the_mirror_image_a_wick_only_lower_low_in_an_up_structure():
    cs = _mirror(_legs(SWEEP))
    d, st, observed = _dir(cs)
    assert observed.sequence == MIXED and d == NEUTRAL and st.sweep["state"] == "unresolved" and st.sweep["swing"] == "low"
    rej = _mirror(_then(_legs(SWEEP), (13350, 13351, 13300, 13310), (13310, 13311, 13270, 13276)))
    d, st, _ = _dir(rej)
    assert d == BULLISH and st.sequence == UP and st.sweep["state"] == "rejected"


def test_without_an_established_trend_before_the_sweep_the_mixed_structure_stands():
    # highs 13461 then 13471 (a real higher high), lows 13339 then 13279: mixed before the wick to 13474
    cs = _legs([13500, 13400, 13460, 13340, 13470, 13280, 13473, 13350])
    d, st, _ = _dir(cs)
    assert d == NEUTRAL and st.sweep is None


def test_a_non_mixed_structure_is_never_changed():
    for pts in (DOWN_TREND + [13330], [13000, 13100, 13040, 13160, 13100, 13220, 13170]):
        cs = _legs(pts)
        found = swings(S, cs, "4h")
        a, b = structure(S, cs, "4h", found), dominant_structure(S, cs, "4h", found)
        assert (a.sequence, a.why, a.broken, a.highs, a.lows) == (b.sequence, b.why, b.broken, b.highs, b.lows)
        assert b.sweep is None


def _real_candles(until: datetime) -> list[Candle]:
    rows = json.loads(DATA.read_text())["candles"]
    out = []
    for r in rows:
        end = datetime.fromisoformat(r["end"].replace("Z", "+00:00"))
        if end <= until:
            out.append(Candle("4h", datetime.fromisoformat(r["start"].replace("Z", "+00:00")), end,
                              *(D(r[k]) for k in ("buy_open", "buy_high", "buy_low", "buy_close",
                                                  "sell_open", "sell_high", "sell_low", "sell_close")),
                              r["parts"], r["expected_parts"]))
    return out


def test_real_18_november_unresolved_at_08_00_then_rejected_by_the_12_00_close():
    at8 = _real_candles(datetime(2026, 11, 18, 8, 0, 4, tzinfo=UTC))
    d, st, observed = _dir(at8)
    assert "swing highs 13224.5 then 13227.9" in observed.why and observed.sequence == MIXED
    assert d == NEUTRAL and st.sweep["state"] == "unresolved" and st.sweep["resolve_beyond"] == "13168"
    for h in (9, 10, 11):                                    # no new 4-hour candle until 12:00
        assert _dir(_real_candles(datetime(2026, 11, 18, h, 0, 4, tzinfo=UTC)))[0] == NEUTRAL
    at12 = _real_candles(datetime(2026, 11, 18, 12, 0, 4, tzinfo=UTC))
    d, st, _ = _dir(at12)
    assert d == BEARISH and st.sweep["state"] == "rejected" and st.sweep["rejected_by_close_utc"] == "2026-11-18T08:00:00Z"
    assert "13157" in st.why and st.highs[-1].price == D("13227.9")
    at_now = _real_candles(datetime(2026, 11, 19, 12, 0, 4, tzinfo=UTC))
    assert _dir(at_now)[0] == BEARISH


def test_real_candles_only_finished_candles_are_used():
    """A decision at 11:00 cannot see the 08:00-12:00 candle that rejects the sweep."""
    cs = _real_candles(datetime(2026, 11, 18, 11, 0, 4, tzinfo=UTC))
    assert cs[-1].end <= datetime(2026, 11, 18, 11, 0, 4, tzinfo=UTC)
    assert _dir(cs)[0] == NEUTRAL


# ---- 2. an unclassified condition: issuing vs validity -----------------------------------------------------------

def unclassified(direction="BEARISH", fresh=True):
    p = plan_dict(no_rec="condition INDETERMINATE: no opportunity", direction=direction, fresh=fresh)
    p.update(condition="INDETERMINATE", opportunity=None, trade=None, condition_unclassified=True,
             condition_evidence=["impulse ...", "the evidence does not fit one condition"])
    return p


def test_a_live_recommendation_is_kept_when_the_condition_becomes_unclassified_and_is_not_current(tmp_path):
    K(tmp_path, flat_store(NOW), Script(plan_dict())).run(NOW)
    t = NOW + timedelta(hours=1, minutes=1)
    k = K(tmp_path, flat_store(t), Script(unclassified()))
    k.run(t)
    rec = k.state["recommendation"]
    assert rec is not None and rec["status"] == WAITING and rec["condition_unclassified"] is True
    assert history(tmp_path)[-1]["event"] == "kept"
    assert k.state["current"] is False and any("unclassified" in r for r in k.state["not_current_reasons"])
    t2 = t + timedelta(hours=1)                              # classified again: supported and current
    k = K(tmp_path, flat_store(t2), Script(plan_dict()))
    k.run(t2)
    assert history(tmp_path)[-1]["event"] == "supported" and "condition_unclassified" not in k.state["recommendation"]
    assert k.state["current"] is True


def test_an_unclassified_condition_never_issues_a_new_recommendation(tmp_path):
    k = K(tmp_path, flat_store(NOW), Script(unclassified()))
    k.run(NOW)
    assert k.state["recommendation"] is None and [e["event"] for e in history(tmp_path)] == ["analysis"]


def test_indeterminate_for_missing_data_still_invalidates(tmp_path):
    K(tmp_path, flat_store(NOW), Script(plan_dict())).run(NOW)
    p = unclassified()
    p.update(condition_unclassified=False, condition_evidence=["4-hour MACD not warmed up"],
             no_recommendation="condition INDETERMINATE: no opportunity")
    t = NOW + timedelta(hours=1, minutes=1)
    k = K(tmp_path, flat_store(t), Script(p))
    k.run(t)
    assert k.state["recommendation"] is None and history(tmp_path)[-1]["event"] == "invalidated"


def test_reversal_risk_and_a_direction_change_still_invalidate(tmp_path):
    for i, p in enumerate((
            {**unclassified(), "condition": "REVERSAL_RISK", "condition_unclassified": False,
             "no_recommendation": "condition REVERSAL_RISK: no opportunity"},
            unclassified(direction="NEUTRAL"))):
        f = tmp_path / str(i)
        f.mkdir()
        K(f, flat_store(NOW), Script(plan_dict())).run(NOW)
        t = NOW + timedelta(hours=1, minutes=1)
        k = K(f, flat_store(t), Script(p))
        k.run(t)
        assert k.state["recommendation"] is None and history(f)[-1]["event"] == "invalidated"
    assert "direction changed" in history(tmp_path / "1")[-1]["why"]


def test_a_stale_unclassified_plan_does_not_keep(tmp_path):
    K(tmp_path, flat_store(NOW), Script(plan_dict())).run(NOW)
    t = NOW + timedelta(hours=1, minutes=1)
    k = K(tmp_path, flat_store(t), Script(unclassified(fresh=False)))
    k.run(t)
    assert history(tmp_path)[-1]["event"] == "invalidated"


def test_a_kept_recommendation_still_ends_on_a_zone_break_and_completes_on_its_destination(tmp_path):
    K(tmp_path, flat_store(NOW), Script(plan_dict())).run(NOW)
    t = NOW + timedelta(hours=1, minutes=1)
    K(tmp_path, flat_store(t), Script(unclassified())).run(t)
    t2 = t + timedelta(hours=1)
    brk = C("1h", NOW + timedelta(hours=1), 1, 13245, 13256, 13244, 13253)                  # 3 pips above 13250
    k = K(tmp_path, flat_store(t2, extra1=[brk]), Script(unclassified()))
    k.run(t2)
    inval = [e for e in history(tmp_path) if e["event"] == "invalidated"]
    assert inval and "confirmed break" in inval[-1]["why"] and k.state["recommendation"] is None
    other = tmp_path / "b"
    other.mkdir()
    K(other, flat_store(NOW), Script(plan_dict())).run(NOW)
    touch = C("5m", NOW, 1 / 12, 13230, 13241, 13229, 13231)
    t1 = NOW + timedelta(minutes=5)
    K(other, flat_store(t1, extra5=[touch]), Script(plan_dict())).run(t1)
    K(other, flat_store(t, extra5=[touch]), Script(unclassified())).run(t)                   # kept while ACTIVE
    drop = C("5m", t, 1 / 12, 13200, 13200, 13168, 13169)
    t3 = t + timedelta(minutes=5)
    k = K(other, flat_store(t3, extra5=[touch, drop]), Script(unclassified()))
    k.run(t3)
    assert history(other)[-1]["event"] == "completed"


# ---- 3. no duplicate of a completed recommendation ---------------------------------------------------------------

TOUCH = C("5m", NOW, 1 / 12, 13230, 13238, 13229, 13231)
DEST = C("5m", NOW + timedelta(minutes=5), 1 / 12, 13180, 13181, 13172, 13175)


def _complete(tmp_path):
    K(tmp_path, flat_store(NOW), Script(plan_dict())).run(NOW)
    K(tmp_path, flat_store(NOW + timedelta(minutes=5), extra5=[TOUCH]), Script(plan_dict())).run(NOW + timedelta(minutes=5))
    k = K(tmp_path, flat_store(NOW + timedelta(minutes=10), extra5=[TOUCH, DEST]), Script(plan_dict()))
    k.run(NOW + timedelta(minutes=10))
    assert k.state["recent"][0]["status"] == COMPLETED
    return k.state["recent"][0]["id"]


def _replan(tmp_path, hours, plan):
    t = NOW + timedelta(hours=hours, minutes=1)
    k = K(tmp_path, flat_store(t, extra5=[TOUCH, DEST]), Script(plan))
    k.run(t)
    return k


def test_the_same_identity_and_primary_after_completion_is_not_issued_and_is_recorded_once(tmp_path):
    first = _complete(tmp_path)
    k = _replan(tmp_path, 1, plan_dict())
    assert k.state["recommendation"] is None
    assert k.state["not_issued"]["duplicate_of"] == first
    k = _replan(tmp_path, 2, plan_dict())
    dups = [e for e in history(tmp_path) if e["event"] == "duplicate"]
    assert len(dups) == 1 and dups[0]["duplicate_of"] == first and k.state["recommendation"] is None


def test_moving_levels_alone_do_not_make_it_new(tmp_path):
    _complete(tmp_path)
    k = _replan(tmp_path, 1, plan_dict(moving=13235))       # the EMA moved: same identity (FC-05)
    assert k.state["recommendation"] is None


def test_a_new_primary_destination_or_new_fixed_levels_or_direction_is_a_new_opportunity(tmp_path):
    cases = {"primary": plan_dict(primary=13150),
             "levels": plan_dict(levels=[("daily R2", "13244.9", True), ("hourly swing high", "13243.2", True)]),
             "direction": plan_dict(trade="BUY", zone=(13150, 13160), primary=13230,
                                    levels=[("daily S1", "13155", True)])}
    for name, p in cases.items():
        f = tmp_path / name
        f.mkdir()
        _complete(f)
        k = _replan(f, 1, p)
        assert k.state["recommendation"] is not None, name


def test_after_an_invalidated_recommendation_the_same_plan_is_issued_again(tmp_path):
    K(tmp_path, flat_store(NOW), Script(plan_dict())).run(NOW)
    t = NOW + timedelta(hours=1, minutes=1)
    brk = C("1h", NOW, 1, 13245, 13258, 13244, 13256)
    K(tmp_path, flat_store(t, extra1=[brk]), Script(plan_dict())).run(t)
    ev = [e["event"] for e in history(tmp_path)]
    assert ev.count("invalidated") == 1 and ev.count("created") == 2 and "duplicate" not in ev   # issued again at once


def test_the_duplicate_rule_survives_a_restart(tmp_path):
    first = _complete(tmp_path)
    k = _replan(tmp_path, 1, plan_dict())                    # a new Keeper object each run: state from current.json
    assert k.state["last_ended"]["id"] == first and k.state["recommendation"] is None


# ---- the dashboard -----------------------------------------------------------------------------------------------

def test_the_dashboard_explains_a_duplicate_and_labels_the_new_events(tmp_path):
    sc = SCENARIOS["duplicate_after_completion"](tmp_path)
    o = stp.overview(sc.s, sc.now)
    assert o["recommendation"] is None
    assert "already reached its primary destination" in o["explanation"]["text"]
    assert "1.31700" in o["explanation"]["planner_reason"]
    assert stp.EVENT_LABEL["kept"].startswith("RE-CHECKED") and "DUPLICATE" in stp.EVENT_LABEL["duplicate"]
    _, h = stp.history(sc.s, "")
    assert h["total"] == 1                                   # the duplicate is not a recommendation


def test_stp_stays_observe_only(tmp_path):
    k = K(tmp_path, flat_store(NOW), Script(plan_dict()))
    k.run(NOW)
    assert k.state["observe_only"] == "OBSERVE ONLY - DOES NOT CONTROL TRADING"
    import planner.keeper as km
    import planner.structure as sm
    for mod in (km, sm):
        src = Path(mod.__file__).read_text()
        assert "import trading" not in src and "from trading" not in src and "broker" not in src.lower()
