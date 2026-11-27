"""Technical tests T-01 to T-66 for the STP strategy integration (owner, 24 November 2026;
docs/design/STP_STRATEGY_INTEGRATION_20261124.md section 13). Each test name starts with its id. Offline: scripted
planners and in-memory candle stores, except T-01 to T-03, which run STP's real planner on the recorded 24 November
candles (skipped where that store is absent). IG is never contacted; nothing is written outside tmp_path."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace

import pytest

from planner.opportunities import ACTIVE, BROKEN, OpportunityKeeper, make_keeper
from planner.keeper import COMPLETED, INVALIDATED, SUPERSEDED, WAITING, Keeper
from stp.authorise import authorise, which_test
from stp.levels import STP_ZONE, StpLevel, with_stp
from tests.planner_helpers import FakeStore, Over, section
from tests.technical.test_planner import C, FakePlan, S as PS, T, flat_store, plan_dict

UTC = timezone.utc
NOW = T(2026, 11, 17, 9, 0)
LIVE = Path("/opt/autobot/data/candles/GBPUSD/5m/2026-11-24.csv")
needs_live = pytest.mark.skipif(not LIVE.exists(), reason="the recorded 24 November candles are not on this machine")


# ---- helpers ----------------------------------------------------------------------------------------------------------

def SW(**kw):
    d = dict(stp_opportunities=True, stp_bidirectional=True, stp_authorises_entries=False, one_signal_one_trade=True,
             planner_observe=True)
    d.update(kw)
    return SimpleNamespace(**d)


def KS(tmp, **sw):
    return Over(PS, planner=section(PS.planner, folder=tmp / "planner"), switches=SW(**sw))


def pd(trade="SELL", zone=(13240, 13250), primary=None, levels=None, no_rec=None, applies=True, structure=None,
       direction=None):
    sell = trade == "SELL"
    primary = primary if primary is not None else (13170 if sell else 13320)
    if levels is None:
        levels = ([("daily R2", "13243.7", True), ("hourly swing high", "13243.2", True)] if sell else
                  [("daily S2", "13156.3", True), ("hourly swing low", "13156.8", True)])
    p = plan_dict(trade=trade, zone=zone, levels=levels, primary=primary, no_rec=no_rec, applies=applies,
                  direction=direction)
    if not no_rec:
        zb = zone[1] + 3 if sell else zone[0] - 3
        sb = zone[1] + 40 if sell else zone[0] - 40
        p["invalidation"].update(zone_break_close=str(zb), zone_break_timeframe="1h", structure_break_close=str(sb),
                                 structure_break_timeframe="4h", destination_first=str(primary))
    if structure is not None:
        p["structure"] = structure
    return p


class Bi:
    """A planner giving scripted plans per direction (trade "SELL"/"BUY"), or for the 4-hour direction (None)."""

    def __init__(self, **plans):
        self.plans = {k if k != "H4" else None: list(v) for k, v in plans.items()}
        self.calls = {}

    def __call__(self, settings, store, now, *a, trade=None):
        seq = self.plans.get(trade) or [pd(trade or "SELL", no_rec="nothing here")]
        n = self.calls.get(trade, 0)
        self.calls[trade] = n + 1
        return FakePlan(seq[min(n, len(seq) - 1)])


def ok(tmp, store, planner, **sw):
    return OpportunityKeeper(KS(tmp, **sw), store, planner=planner)


def state(tmp):
    return json.loads((tmp / "planner" / "GBPUSD" / "current.json").read_text())


def opps(tmp):
    return state(tmp)["opportunities"]


def ev(tmp):
    return [json.loads(x) for x in (tmp / "planner" / "GBPUSD" / "recommendations.jsonl").read_text().splitlines()]


def five(t, o, h, l, c):
    return C("5m", t, 1 / 12, o, h, l, c)


def hour(t, o, h, l, c):
    return C("1h", t, 1, o, h, l, c)


def store_with(until, price=13200, extra5=(), extra1=(), h4=()):
    st = flat_store(until, price, extra5, extra1)
    st.by_tf["4h"] = sorted(h4, key=lambda c: c.start)
    return st


# ---- T-01 to T-03: STP proposes in both directions (WP-2; the real planner on the recorded 24 November) --------------

@needs_live
def test_T01_both_directions_get_a_proposal_from_one_zone_map():
    from planner.assess import plan_at
    from tests.stp.harness import live_settings, live_store
    s = live_settings()
    store = live_store(s)
    at = T(2026, 11, 24, 18, 0) + timedelta(seconds=3)
    sell, buy = plan_at(s, store, at, trade="SELL").as_dict(), plan_at(s, store, at, trade="BUY").as_dict()
    assert sell["trade"] == "SELL" and buy["trade"] == "BUY"
    assert (sell["entry_zone"]["low"], sell["entry_zone"]["high"]) == ("13119.1", "13128.6")
    assert (buy["entry_zone"]["low"], buy["entry_zone"]["high"]) == ("13119.1", "13128.6")     # OD-33: one zone
    assert sell["destinations"]["primary"]["price"] == "13084.1" and buy["destinations"]["primary"]["price"] == "13135.5"
    assert sell["invalidation"]["zone_break_close"] == "13131.6" and buy["invalidation"]["zone_break_close"] == "13116.1"


@needs_live
def test_T02_a_buy_against_a_bearish_4_hour_direction_is_proposed_and_says_so():
    from planner.assess import plan_at
    from tests.stp.harness import live_settings, live_store
    s = live_settings()
    p = plan_at(s, live_store(s), T(2026, 11, 24, 12, 0) + timedelta(seconds=2), trade="BUY").as_dict()
    assert p["dominant_direction"] == "BEARISH" and p["trade"] == "BUY" and p["relation_to_h4"] == "against"
    assert p["opportunity"] == "countertrend reversal" and p["no_recommendation"] is None
    assert (p["entry_zone"]["low"], p["entry_zone"]["high"]) == ("13075", "13085.4")


@needs_live
def test_T03_with_the_switch_off_the_plan_is_the_4_hour_direction_plan_as_before():
    from planner.assess import plan_at
    from tests.stp.harness import live_settings, live_store
    s = live_settings()
    store = live_store(s)
    at = T(2026, 11, 24, 14, 0) + timedelta(seconds=2)
    p = plan_at(s, store, at).as_dict()
    assert "relation_to_h4" not in p and p["trade"] == "SELL"
    assert (p["entry_zone"]["low"], p["entry_zone"]["high"]) == ("13103", "13114.1")      # as recorded (1400-21)
    k = make_keeper(KS(Path("/nonexistent"), stp_opportunities=False), store)
    assert type(k) is Keeper                            # STP_OPPORTUNITIES off: the single tracker, unchanged


# ---- T-04 to T-08: several opportunities, kept across re-plans (WP-1) ---------------------------------------------------

def test_T04_several_sell_opportunities_and_a_buy_are_all_held(tmp_path):
    plans = Bi(SELL=[pd(zone=(13240, 13250)), pd(zone=(13260, 13270), levels=[("daily R3", "13265", True)]),
                     pd(zone=(13280, 13290), levels=[("weekly R1", "13285", True)])],
               BUY=[pd("BUY", zone=(13150, 13160))])
    for h in range(3):
        t = NOW + timedelta(hours=h)
        ok(tmp_path, store_with(t), plans).run(t)
    o = opps(tmp_path)
    assert sorted((x["trade"], x["entry_zone"]["low"]) for x in o) == [
        ("BUY", "13150"), ("SELL", "13240"), ("SELL", "13260"), ("SELL", "13280")]
    assert all(x["status"] == WAITING for x in o)


def test_T05_a_buy_at_support_and_a_sell_at_resistance_each_authorise_only_their_own(tmp_path):
    st = auth_state(opp("SELL", (13240, 13250)), opp("BUY", (13150, 13160), oid="B1"))
    s, store = auth_settings(tmp_path), auth_store()
    assert authorise(s, store, idea("sell", REJ_SELL), AT, src(st)).allowed
    assert not authorise(s, store, idea("buy", REJ_SELL), AT, src(st)).allowed    # no BUY opportunity at the SELL zone
    assert authorise(s, store, idea("buy", REJ_BUY), AT, src(st)).allowed
    assert not authorise(s, store, idea("sell", REJ_BUY), AT, src(st)).allowed


def test_T06_a_re_plan_that_picks_another_zone_adds_it_and_keeps_the_first(tmp_path):
    plans = Bi(SELL=[pd(zone=(13240, 13250)), pd(zone=(13260, 13270), levels=[("daily R3", "13265", True)])])
    ok(tmp_path, store_with(NOW), plans).run(NOW)
    t = NOW + timedelta(hours=1)
    ok(tmp_path, store_with(t), plans).run(t)
    lows = sorted(x["entry_zone"]["low"] for x in opps(tmp_path))
    assert lows == ["13240", "13260"] and not any(e["event"] in ("superseded", "invalidated") for e in ev(tmp_path))


def test_T07_no_recommendation_or_a_4_hour_direction_change_ends_nothing(tmp_path):
    plans = Bi(SELL=[pd(), pd(no_rec="the condition is not a class"), pd(direction="BULLISH")])
    for h in range(3):
        t = NOW + timedelta(hours=h)
        ok(tmp_path, store_with(t), plans).run(t)
    o = opps(tmp_path)
    assert len(o) == 1 and o[0]["status"] == WAITING
    assert not any(e["event"] == "invalidated" for e in ev(tmp_path))


def test_T08_same_identity_moved_is_updated_and_moved_away_is_superseded_with_its_lineage(tmp_path):
    plans = Bi(SELL=[pd(zone=(13240, 13250)), pd(zone=(13241, 13250)), pd(zone=(13262, 13270))])
    ok(tmp_path, store_with(NOW), plans).run(NOW)
    first = opps(tmp_path)[0]
    t = NOW + timedelta(hours=1)
    ok(tmp_path, store_with(t), plans).run(t)
    assert opps(tmp_path)[0]["id"] == first["id"] and opps(tmp_path)[0]["entry_zone"]["low"] == "13241"
    t2 = NOW + timedelta(hours=2)
    ok(tmp_path, store_with(t2), plans).run(t2)
    o = opps(tmp_path)
    assert len(o) == 1 and o[0]["id"] != first["id"] and o[0]["lineage"] == first["id"]
    assert any(e["event"] == "superseded" and e["id"] == first["id"] for e in ev(tmp_path))


# ---- T-09 to T-15: invalidation by the opportunity's own conditions (WP-1) ----------------------------------------------

def _hourly_run(tmp, plans, closes, start=NOW):
    """A first run at `start`, then one run per hourly close in `closes` (the hourly candle that just finished)."""
    ok(tmp, store_with(start), plans).run(start)
    extra = []
    for k, close in enumerate(closes, start=1):
        t = start + timedelta(hours=k)
        extra.append(hour(t - timedelta(hours=1), 13245, max(13245, close) + 1, min(13245, close) - 1, close))
        ok(tmp, store_with(t, 13245, extra1=extra), plans).run(t)


def test_T09_an_hourly_close_beyond_by_less_than_3_pips_is_recorded_only(tmp_path):
    _hourly_run(tmp_path, Bi(SELL=[pd()]), [13252.9])
    assert opps(tmp_path)[0]["status"] in (WAITING, ACTIVE)
    assert any(e["event"] == "closed beyond" for e in ev(tmp_path))


def test_T10_a_confirmed_break_makes_it_broken_and_it_authorises_nothing(tmp_path):
    _hourly_run(tmp_path, Bi(SELL=[pd()]), [13253])
    o = opps(tmp_path)[0]
    assert o["status"] == BROKEN and o["broken"]["candles"] == 0
    st = auth_state(o)
    assert not authorise(auth_settings(tmp_path), auth_store(), idea("sell", REJ_SELL), AT, src(st)).allowed
    assert not authorise(auth_settings(tmp_path), auth_store(), idea("buy", REJ_SELL), AT, src(st)).allowed


@pytest.mark.parametrize("n", [1, 2, 3])
def test_T11_a_close_back_inside_at_the_nth_close_restores_watch_and_wait_keeping_its_id(tmp_path, n):
    _hourly_run(tmp_path, Bi(SELL=[pd()]), [13253] + [13256] * (n - 1) + [13249])
    o = opps(tmp_path)
    assert len(o) == 1 and o[0]["status"] == ACTIVE and o[0]["label"] == "Watch & Wait"
    fb = [e for e in ev(tmp_path) if e["event"] == "failed breakout"]
    assert fb and f"within {n} candle(s)" in fb[-1]["why"]


def test_T12_a_break_held_for_three_closes_invalidates(tmp_path):
    _hourly_run(tmp_path, Bi(SELL=[pd()]), [13253, 13256, 13257, 13258])
    first = next(e["id"] for e in ev(tmp_path) if e["event"] == "created")
    held = [e for e in ev(tmp_path) if e["id"] == first and "confirmed break held" in (e.get("why") or "")]
    assert held and held[0]["event"] == "invalidated" and first not in [o["id"] for o in opps(tmp_path)]
    # the scripted planner proposes the same zone again at the next re-plan: that is STP's own new proposal, a new
    # opportunity (never the broken one coming back: a new id, starting as WAITING). Phase 2 C-2 (owner, 27 November
    # 2026): it continues the same structural LINEAGE, so its duplicate keys and D-25 test count carry on
    new = opps(tmp_path)
    assert new and all(o["id"] != first and o["status"] == WAITING and o["lineage"] == first for o in new)


def test_T13_a_4_hour_close_beyond_the_structure_break_invalidates(tmp_path):
    h4a = C("4h", NOW - timedelta(hours=4), 4, 13245, 13250, 13240, 13245)
    ok(tmp_path, store_with(NOW, h4=[h4a]), Bi(SELL=[pd()])).run(NOW)
    t = NOW + timedelta(hours=4)
    h4b = C("4h", NOW, 4, 13245, 13295, 13240, 13290)                    # closes at 13290, above 13290 (13250 + 40)
    ok(tmp_path, store_with(t, h4=[h4a, h4b]), Bi(SELL=[pd(no_rec="x")])).run(t)
    assert opps(tmp_path) == [] and any("structure break" in (e.get("why") or "") for e in ev(tmp_path))


def test_T14_destination_before_the_zone_invalidates_after_the_zone_completes(tmp_path):
    ok(tmp_path, store_with(NOW), Bi(SELL=[pd()])).run(NOW)
    t = NOW + timedelta(minutes=10)
    down = [five(NOW + timedelta(minutes=5), 13200, 13200, 13169, 13170)]
    ok(tmp_path, store_with(t, extra5=down), Bi(SELL=[pd()])).run(t)
    assert opps(tmp_path) == [] and any("destination reached before entry" in (e.get("why") or "") for e in ev(tmp_path))
    tmp2 = tmp_path / "b"
    ok(tmp2, store_with(NOW), Bi(SELL=[pd()])).run(NOW)
    up_then_down = [five(NOW + timedelta(minutes=5), 13200, 13241, 13200, 13238),
                    five(NOW + timedelta(minutes=10), 13238, 13238, 13169, 13170)]
    t2 = NOW + timedelta(minutes=15)
    ok(tmp2, store_with(t2, extra5=up_then_down), Bi(SELL=[pd()])).run(t2)
    assert opps(tmp2) == [] and any(e["event"] == "completed" for e in ev(tmp2))


def test_T15_the_pivot_rollover_ends_an_opportunity_whose_daily_levels_are_gone(tmp_path):
    late = T(2026, 11, 17, 23, 0)
    keep = {"levels": [{"name": "daily R2", "price": "13243.7"}, {"name": "hourly swing high", "price": "13243.2"}]}
    ok(tmp_path, store_with(late), Bi(SELL=[pd(structure=keep)])).run(late)
    t = T(2026, 11, 18, 0, 0)
    rolled = {"levels": [{"name": "daily R2", "price": "13262.0"}, {"name": "hourly swing high", "price": "13243.2"}]}
    ok(tmp_path, store_with(t), Bi(SELL=[pd(no_rec="x", structure=rolled)])).run(t)
    assert opps(tmp_path) == [] and any("structural levels changed" in (e.get("why") or "") for e in ev(tmp_path))


# ---- T-16 to T-21: Watch & Wait, failed rejections, tests (WP-1) --------------------------------------------------------

@pytest.mark.parametrize("high,status", [(13237.0, ACTIVE), (13236.9, WAITING)])
def test_T16_a_candle_within_3_pips_starts_watch_and_wait_3_1_does_not(tmp_path, high, status):
    ok(tmp_path, store_with(NOW), Bi(SELL=[pd()])).run(NOW)
    t = NOW + timedelta(minutes=10)
    c = [five(NOW + timedelta(minutes=5), 13230, high, 13229, 13232)]
    ok(tmp_path, store_with(t, extra5=c), Bi(SELL=[pd()])).run(t)
    assert opps(tmp_path)[0]["status"] == status


def _active(tmp):
    ok(tmp, store_with(NOW), Bi(SELL=[pd()])).run(NOW)
    t = NOW + timedelta(minutes=10)
    ok(tmp, store_with(t, extra5=[five(NOW + timedelta(minutes=5), 13230, 13241, 13229, 13238)]), Bi(SELL=[pd()])).run(t)
    assert opps(tmp)[0]["status"] == ACTIVE
    return t


def test_T17_watch_and_wait_is_never_demoted_when_price_moves_clear(tmp_path):
    _active(tmp_path)
    for h in range(1, 6):
        t = NOW + timedelta(hours=h)
        ok(tmp_path, store_with(t), Bi(SELL=[pd()])).run(t)        # quiet hours at 13200, wholly clear of the zone
    assert opps(tmp_path)[0]["status"] == ACTIVE and not any(e["event"] == "waiting" and e.get("status") == WAITING
                                                             and "wholly clear" in e["why"] for e in ev(tmp_path))


def test_T18_a_failed_rejection_changes_nothing_and_gives_no_opposite_authorisation(tmp_path):
    _active(tmp_path)
    t = NOW + timedelta(minutes=30)
    wobble = [five(NOW + timedelta(minutes=5 * k), 13238, 13249, 13237, 13246) for k in range(2, 6)]
    ok(tmp_path, store_with(t, extra5=wobble), Bi(SELL=[pd()])).run(t)
    o = opps(tmp_path)
    assert len(o) == 1 and o[0]["status"] == ACTIVE and o[0]["trade"] == "SELL"
    assert not authorise(auth_settings(tmp_path), auth_store(), idea("buy", REJ_SELL), AT, src(auth_state(*o))).allowed


def test_T19_leaving_and_returning_is_a_new_test():
    hours = [hour(T(2026, 11, 17, 6), 13230, 13242, 13229, 13235),      # test 1
             hour(T(2026, 11, 17, 7), 13235, 13236, 13220, 13222),      # wholly clear: re-armed
             hour(T(2026, 11, 17, 8), 13222, 13241, 13220, 13238)]      # test 2
    store = FakeStore({"1h": hours, "5m": []})
    s = auth_settings(Path("/x"))
    assert which_test(s, store, D(13240), D(13250), T(2026, 11, 17, 5), T(2026, 11, 17, 8, 30)) == 2
    assert which_test(s, store, D(13240), D(13250), T(2026, 11, 17, 5), T(2026, 11, 17, 6, 30)) == 1
    assert which_test(s, store, D(13240), D(13250), T(2026, 11, 17, 5), T(2026, 11, 17, 9, 10)) == 2


def test_T20_five_failed_setups_and_no_break_leave_it_in_watch_and_wait(tmp_path):
    _active(tmp_path)
    t = NOW + timedelta(hours=1)
    fails = [five(NOW + timedelta(minutes=5 * k), 13238, 13249, 13236, 13240) for k in range(2, 12)]
    ok(tmp_path, store_with(t, 13238, extra5=fails), Bi(SELL=[pd()])).run(t)
    assert opps(tmp_path)[0]["status"] == ACTIVE


def test_T21_500_candles_inside_the_zone_neither_expire_it_nor_trade(tmp_path):
    ok(tmp_path, store_with(NOW), Bi(SELL=[pd()])).run(NOW)
    t = NOW + timedelta(hours=42)
    ok(tmp_path, store_with(t, 13245), Bi(SELL=[pd()])).run(t)
    o = opps(tmp_path)
    assert len(o) == 1 and o[0]["status"] in (WAITING, ACTIVE) and not any(e["event"] == "invalidated" for e in ev(tmp_path))


# ---- T-22 to T-27: the zones in the strategies' level list (WP-3) -----------------------------------------------------

def base_levels():
    from levels.current import LevelList
    from levels.rules import Level
    lv = [Level(D("13300"), "pivot", "daily pivot", None, True, 1)]
    return LevelList(NOW, NOW, None, None, lv, [{"group": 1, "low": D("13300"), "high": D("13300"), "members": lv,
                                                  "important": True, "lined_up": False}])


def test_T22_a_live_opportunity_adds_its_edges_and_in_zone_fixed_levels_to_the_strategies_copy_only():
    base = base_levels()
    o = opp("SELL", (13240, 13250))
    got = with_stp(base, {"opportunities": [o]})
    stp = [lv for lv in got.levels if lv.type == STP_ZONE]
    assert sorted(lv.price for lv in stp) == [D("13240"), D("13243.2"), D("13243.7"), D("13250")]   # not the moving one
    assert all(isinstance(lv, StpLevel) and lv.zone_low == D(13240) and lv.zone_high == D(13250) for lv in stp)
    assert got.group_of(stp[0])["lined_up"] is False and got.group_of(stp[0])["stp"] is True
    assert [lv.price for lv in base.levels] == [D("13300")] and len(base.groups) == 1      # the input is unchanged


def test_T23_a_broken_or_ended_opportunity_adds_no_levels():
    for status in (BROKEN, INVALIDATED, COMPLETED, SUPERSEDED):
        got = with_stp(base_levels(), {"opportunities": [opp("SELL", (13240, 13250), status=status)]})
        assert [lv.type for lv in got.levels] == ["pivot"]


def _watch(levels, candles):
    from rejection.watch import RejectionWatcher
    w = RejectionWatcher(PS, design_only=True)
    events = []
    for c in candles:
        events += w.on_candle(c, None, levels)
    return w, events


REJECTION_CANDLES = [five(T(2026, 11, 24, 18, 0), "13114", "13118", "13113", "13117"),
                     five(T(2026, 11, 24, 18, 5), "13117", "13127.5", "13116", "13126"),
                     five(T(2026, 11, 24, 18, 10), "13126", "13127", "13119", "13120"),
                     five(T(2026, 11, 24, 18, 15), "13120", "13121", "13114", "13115"),
                     five(T(2026, 11, 24, 18, 20), "13115", "13116", "13110", "13111")]


def test_T24_the_5m_bounce_gets_a_sell_from_an_stp_zone_level_alone():
    from strategies.bollinger_bounce_5m.strategy import candidates
    from levels.current import LevelList
    empty = LevelList(NOW, NOW, None, None, [], [])
    lv = with_stp(empty, {"opportunities": [opp("SELL", (13117.6, 13128.6), levels=[("weekly pivot", "13127.3", True)])]})
    w, events = _watch(lv, REJECTION_CANDLES)
    sells = [c for c in candidates(w, events, True) if c.direction == "sell"]
    assert sells and all("rejection_candle" in c.context for c in sells)
    w0, e0 = _watch(empty, REJECTION_CANDLES)
    assert [c for c in candidates(w0, e0) if c.direction == "sell"] == []      # without STP's level: nothing


@pytest.mark.parametrize("zone,kept", [((13117.6, 13128.6), True), ((13110.0, 13118.0), False)])
def test_T25_level_reversal_at_an_stp_level_is_kept_up_to_the_far_edge_plus_3_pips_with_its_own_stop(zone, kept):
    from levels.current import LevelList
    from strategies.level_reversal.strategy import LevelReversal
    s = Over(PS, switches=SW(stp_authorises_entries=True, level_reversal=True))
    lv = with_stp(LevelList(NOW, NOW, None, None, [], []), {"opportunities": [opp("SELL", zone, levels=[])]})
    lr = LevelReversal(s)
    from rejection.watch import RejectionWatcher
    w = RejectionWatcher(s, design_only=True)
    got = []
    for c in REJECTION_CANDLES:
        got += lr.on_candle(c, w, w.on_candle(c, None, lv))
    sells = [c for c in got if c.direction == "sell"]
    assert bool(sells) == kept
    for c in sells:
        assert c.context["stop_price"] == c.context["furthest"] + D(PS.level_reversal.stop_beyond_furthest_pips)
        assert "rejection_candle" in c.context


def test_T26_level_reversal_at_s2_outside_every_stp_zone_is_refused_by_stp(tmp_path):
    st = auth_state(opp("SELL", (13240, 13250)))
    v = authorise(auth_settings(tmp_path), auth_store(), idea("buy", REJ_BUY, strategy="level reversal"), AT, src(st))
    assert not v.allowed and "no live STP BUY opportunity" in v.reasons[0]


def test_T27_with_authorisation_off_the_strategies_levels_are_exactly_the_bots(monkeypatch):
    from strategies import replay as rp
    sentinel = object()
    monkeypatch.setattr(rp, "build", lambda s, memo, t: sentinel)
    runner = rp.StrategyRunner.__new__(rp.StrategyRunner)
    runner.s, runner.memo = Over(PS, switches=SW(stp_authorises_entries=False)), None
    from stp.source import source_for
    runner.stp = source_for(runner.s)
    assert runner.stp is None and runner.levels_at(NOW) is sentinel and runner.stp_version() is None


# ---- T-28 to T-39: the authorisation check (WP-4) -----------------------------------------------------------------------

AT = T(2026, 11, 17, 10, 2)
REJ_SELL = T(2026, 11, 17, 9, 40)
REJ_BUY = T(2026, 11, 17, 9, 45)


def opp(trade, zone, oid=None, status=WAITING, created=T(2026, 11, 17, 8, 0), levels=None, lineage=None, primary=None):
    sell = trade == "SELL"
    p = pd(trade, zone, primary=primary, levels=levels)
    oid = oid or f"STP-GBPUSD-{trade}-{zone[0]}"
    return {"id": oid, "trade": trade, "status": status, "entry_zone": p["entry_zone"],
            "destinations": p["destinations"], "invalidation": p["invalidation"],
            "created_utc": created.strftime("%Y-%m-%dT%H:%M:%SZ"), "lineage": lineage or oid,
            "lineage_created_utc": created.strftime("%Y-%m-%dT%H:%M:%SZ"), "ever_active": False,
            "label": "Watch & Wait" if status == ACTIVE else status, "far_edge": str(zone[1] if sell else zone[0])}


def auth_state(*os_, written=AT - timedelta(minutes=1), m5=T(2026, 11, 17, 10, 0), h1=T(2026, 11, 17, 10, 0),
               h4=T(2026, 11, 17, 8, 0)):
    f = lambda t: t.strftime("%Y-%m-%dT%H:%M:%SZ")      # noqa: E731
    return {"opportunities": list(os_), "written_utc": f(written), "m5_checked_until": f(m5),
            "validated_h1_end": f(h1), "h4_checked_until": f(h4), "current": True, "data_fresh": True,
            "not_current_reasons": []}


def src(st):
    return SimpleNamespace(state_at=lambda t=None: st, version=lambda t=None: st.get("written_utc") if st else None)


def auth_settings(tmp, **sw):
    return Over(PS, switches=SW(**({"stp_authorises_entries": True} | sw)))


def auth_store(extra5=(), extra1=(), h4=(), until=AT):
    rej = [five(REJ_SELL, 13230, 13238, 13229, 13232),                   # reaches the SELL zone 13240 within 3 pips
           five(REJ_BUY, 13170, 13171, 13162, 13166)]                    # reaches the BUY zone 13160 within 3 pips
    fives = {c.start: c for c in rej}
    t = T(2026, 11, 17, 0, 0)
    while t + timedelta(minutes=5) <= until:
        fives.setdefault(t, five(t, 13200, 13201, 13199, 13200))
        t += timedelta(minutes=5)
    for c in extra5:
        fives[c.start] = c
    hours = {}
    t = T(2026, 11, 17, 0, 0)
    while t + timedelta(hours=1) <= until:
        hours[t] = hour(t, 13200, 13201, 13199, 13200)
        t += timedelta(hours=1)
    for c in extra1:
        hours[c.start] = c
    return FakeStore({"5m": list(fives.values()), "1h": list(hours.values()), "4h": list(h4)})


def idea(direction, rej, price=None, strategy="Bollinger bounce 5m", signal=None):
    ctx = {"rejection_candle": rej.strftime("%Y-%m-%dT%H:%M:%SZ")} | ({"signal": signal} if signal else {})
    return SimpleNamespace(strategy=strategy, direction=direction, time=AT,
                           entry_price=D(price or ("13231" if direction == "sell" else "13167")), context=ctx)


def test_T28_a_confirmation_whose_rejection_candle_reached_the_zone_is_authorised_even_entered_outside_it(tmp_path):
    v = authorise(auth_settings(tmp_path), auth_store(), idea("sell", REJ_SELL, price="13231"), AT,
                  src(auth_state(opp("SELL", (13240, 13250)))))
    assert v.allowed and v.opportunity["id"] == "STP-GBPUSD-SELL-13240" and v.signal == "STP-GBPUSD-SELL-13240#t1"
    assert set(v.bypass) == {"analyser_state", "hourly_context", "rsi_stretch", "counter_trend_tiring", "one_view"}


def test_T29_no_matching_opportunity_or_the_wrong_direction_is_refused(tmp_path):
    s, store = auth_settings(tmp_path), auth_store()
    assert not authorise(s, store, idea("sell", REJ_SELL), AT, src(auth_state())).allowed
    assert not authorise(s, store, idea("buy", REJ_SELL), AT, src(auth_state(opp("SELL", (13240, 13250))))).allowed


def test_T30_a_rejection_candle_3_1_pips_short_is_refused(tmp_path):
    store = auth_store(extra5=[five(REJ_SELL, 13230, 13236.9, 13229, 13232)])
    assert not authorise(auth_settings(tmp_path), store, idea("sell", REJ_SELL), AT,
                         src(auth_state(opp("SELL", (13240, 13250))))).allowed


def test_T31_a_destination_touch_in_a_candle_the_tracker_has_not_seen_refuses(tmp_path):
    store = auth_store(extra5=[five(T(2026, 11, 17, 10, 0), 13200, 13200, 13169, 13185)], until=T(2026, 11, 17, 10, 5))
    v = authorise(auth_settings(tmp_path), store, idea("sell", REJ_SELL), T(2026, 11, 17, 10, 5),
                  src(auth_state(opp("SELL", (13240, 13250)), written=T(2026, 11, 17, 10, 0, 3))))
    assert not v.allowed and "primary destination 13170 was reached" in v.reasons[0]


def test_T32_a_destination_touch_earlier_in_the_forming_candle_refuses_though_price_is_back(tmp_path):
    partial = five(T(2026, 11, 17, 10, 0), 13200, 13201, 13169, 13199)
    v = authorise(auth_settings(tmp_path), auth_store(), idea("sell", REJ_SELL), AT,
                  src(auth_state(opp("SELL", (13240, 13250)))), partial=partial)
    assert not v.allowed and "the forming 5-minute candle" in v.reasons[0]


def test_T33_a_destination_touch_by_the_live_price_refuses(tmp_path):
    tick = SimpleNamespace(time=AT, sell=D("13170"), buy=D("13171.2"))
    v = authorise(auth_settings(tmp_path), auth_store(), idea("sell", REJ_SELL), AT,
                  src(auth_state(opp("SELL", (13240, 13250)))), tick=tick)
    assert not v.allowed and "the live price" in v.reasons[0]


def test_T34_a_touch_only_in_the_candle_running_at_creation_is_not_used(tmp_path):
    created = T(2026, 11, 17, 10, 0, 3)
    store = auth_store(extra5=[five(T(2026, 11, 17, 10, 0), 13200, 13200, 13169, 13185)], until=T(2026, 11, 17, 10, 5))
    v = authorise(auth_settings(tmp_path), store, idea("sell", REJ_SELL), T(2026, 11, 17, 10, 5),
                  src(auth_state(opp("SELL", (13240, 13250), created=created), written=T(2026, 11, 17, 10, 0, 3))))
    assert v.allowed


def test_T35_an_hourly_zone_break_the_tracker_has_not_seen_refuses(tmp_path):
    store = auth_store(extra1=[hour(T(2026, 11, 17, 10, 0), 13240, 13256, 13239, 13253)], until=T(2026, 11, 17, 11, 0))
    v = authorise(auth_settings(tmp_path), store, idea("sell", REJ_SELL), T(2026, 11, 17, 11, 0),
                  src(auth_state(opp("SELL", (13240, 13250)), written=T(2026, 11, 17, 10, 58))))
    assert not v.allowed and "zone break 13253" in v.reasons[0]


def test_T36_a_4_hour_structure_break_the_tracker_has_not_seen_refuses(tmp_path):
    store = auth_store(h4=[C("4h", T(2026, 11, 17, 8), 4, 13240, 13295, 13239, 13291)], until=T(2026, 11, 17, 12, 0))
    v = authorise(auth_settings(tmp_path), store, idea("sell", REJ_SELL), T(2026, 11, 17, 12, 0),
                  src(auth_state(opp("SELL", (13240, 13250)), written=T(2026, 11, 17, 11, 58))))
    assert not v.allowed and "structure break 13290" in v.reasons[0]


def test_T37_an_entry_at_or_beyond_the_zone_break_is_refused(tmp_path):
    v = authorise(auth_settings(tmp_path), auth_store(), idea("sell", REJ_SELL, price="13253"), AT,
                  src(auth_state(opp("SELL", (13240, 13250)))))
    assert not v.allowed and "FC-07" in v.reasons[0]


def test_T38_stale_or_missing_data_refuses(tmp_path):
    s, store, o = auth_settings(tmp_path), auth_store(), opp("SELL", (13240, 13250))
    old = auth_state(o, written=AT - timedelta(minutes=11))
    assert "not current" in authorise(s, store, idea("sell", REJ_SELL), AT, src(old)).reasons[0]
    tick = SimpleNamespace(time=AT - timedelta(minutes=11), sell=D("13200"), buy=D("13201"))
    assert "stale price" in authorise(s, store, idea("sell", REJ_SELL), AT, src(auth_state(o)), tick=tick).reasons[0]
    assert "missing or unreadable" in authorise(s, store, idea("sell", REJ_SELL), AT, src(None)).reasons[0]
    from stp.source import FileSource
    bad = tmp_path / "planner" / "GBPUSD"
    bad.mkdir(parents=True)
    (bad / "current.json").write_text("{not json")
    fs = FileSource(Over(PS, planner=section(PS.planner, folder=tmp_path / "planner")))
    assert fs.state_at(AT) is None
    assert "missing or unreadable" in authorise(s, store, idea("sell", REJ_SELL), AT, fs).reasons[0]


@pytest.mark.parametrize("sw", [dict(stp_opportunities=False), dict(stp_bidirectional=False)])
def test_T39_authorisation_refuses_everything_unless_the_other_two_switches_are_on(tmp_path, sw):
    v = authorise(auth_settings(tmp_path, **sw), auth_store(), idea("sell", REJ_SELL), AT,
                  src(auth_state(opp("SELL", (13240, 13250)))))
    assert not v.allowed and "STP_OPPORTUNITIES and STP_BIDIRECTIONAL" in v.reasons[0]


# ---- T-40 to T-43, T-58 to T-61: duplicates (WP-4, rule 11) -------------------------------------------------------------

def _rule11(used):
    from safety.rules import _one_signal
    return lambda key: _one_signal(SimpleNamespace(switches=SimpleNamespace(one_signal_one_trade=True)),
                                   SimpleNamespace(context={"signal": key}), used)


def test_T40_the_5m_bounce_and_level_reversal_on_one_setup_share_one_key(tmp_path):
    s, store, st = auth_settings(tmp_path), auth_store(), auth_state(opp("SELL", (13240, 13250)))
    a = authorise(s, store, idea("sell", REJ_SELL), AT, src(st))
    b = authorise(s, store, idea("sell", REJ_SELL, strategy="level reversal"), AT, src(st))
    assert a.signal == b.signal
    assert _rule11({a.signal: "Bollinger bounce 5m"})(b.signal) == ["same signal already traded by Bollinger bounce 5m"]


def test_T41_a_new_confirmation_in_the_same_test_after_a_stop_out_is_refused(tmp_path):
    s, st = auth_settings(tmp_path), auth_state(opp("SELL", (13240, 13250)))
    later = T(2026, 11, 17, 9, 50)
    store = auth_store(extra5=[five(later, 13230, 13239, 13229, 13233)])
    a = authorise(s, store, idea("sell", REJ_SELL), AT, src(st))
    b = authorise(s, store, idea("sell", later), AT, src(st))
    assert a.stp_key == b.stp_key == "STP-GBPUSD-SELL-13240#t1" and _rule11({a.signal: "x"})(b.signal)


def test_T42_a_new_test_allows_one_more_trade(tmp_path):
    s, st = auth_settings(tmp_path), auth_state(opp("SELL", (13240, 13250), created=T(2026, 11, 17, 6, 0)))
    later = T(2026, 11, 17, 9, 40)
    hours = [hour(T(2026, 11, 17, 7), 13230, 13242, 13229, 13235), hour(T(2026, 11, 17, 8), 13235, 13236, 13220, 13222)]
    store = auth_store(extra1=hours)
    v = authorise(s, store, idea("sell", later), AT, src(st))
    assert v.allowed and v.stp_key.endswith("#t2") and not _rule11({"STP-GBPUSD-SELL-13240#t1": "x"})(v.signal)


def test_T43_with_one_signal_one_trade_off_gated_ideas_are_refused(tmp_path):
    v = authorise(auth_settings(tmp_path, one_signal_one_trade=False), auth_store(), idea("sell", REJ_SELL), AT,
                  src(auth_state(opp("SELL", (13240, 13250)))))
    assert not v.allowed and "ONE_SIGNAL_ONE_TRADE" in v.reasons[0]


def test_T58_the_hourly_bounce_keeps_its_own_key_so_a_session_sweep_on_its_rejection_is_still_refused(tmp_path):
    own = "sell " + REJ_SELL.strftime("%Y-%m-%dT%H:%M:%SZ")
    v = authorise(auth_settings(tmp_path), auth_store(), idea("sell", REJ_SELL, strategy="Bollinger bounce", signal=own),
                  AT, src(auth_state(opp("SELL", (13240, 13250)))))
    assert v.signal == f"{own}|STP-GBPUSD-SELL-13240#t1"
    from orders.sender import OrderSender
    fake = SimpleNamespace(unresolved={}, trades={"r1": SimpleNamespace(signal=v.signal, strategy="Bollinger bounce")})
    used = OrderSender.used_signals(fake)
    assert used[own] == used["STP-GBPUSD-SELL-13240#t1"] == "Bollinger bounce"
    assert _rule11(used)(own) == ["same signal already traded by Bollinger bounce"]       # the session sweep's key


def test_T59_a_supersede_between_two_ideas_of_one_test_keeps_the_key(tmp_path):
    s, store = auth_settings(tmp_path), auth_store()
    a = authorise(s, store, idea("sell", REJ_SELL), AT, src(auth_state(opp("SELL", (13240, 13250), oid="A"))))
    b = authorise(s, store, idea("sell", REJ_SELL), AT, src(auth_state(opp("SELL", (13240, 13250), oid="A2", lineage="A"))))
    assert a.stp_key == b.stp_key == "A#t1"


def test_T60_one_candle_on_several_zone_levels_is_one_setup_per_direction_and_one_key(tmp_path):
    from levels.current import LevelList
    lv = with_stp(LevelList(NOW, NOW, None, None, [], []),
                  {"opportunities": [opp("SELL", (13117.6, 13128.6), levels=[("weekly pivot", "13127.3", True)])]})
    w, _ = _watch(lv, [five(T(2026, 11, 24, 18, 0), "13115", "13130", "13114", "13126")])
    sells = [st for st in w.setups if st.direction == "sell"]
    assert len(sells) == 1 and len(sells[0].pierced) == 3
    s, st = auth_settings(tmp_path), auth_state(opp("SELL", (13240, 13250)))
    store = auth_store(extra5=[five(T(2026, 11, 17, 9, 45), 13232, 13241, 13231, 13236)])
    k1 = authorise(s, store, idea("sell", REJ_SELL), AT, src(st)).stp_key
    k2 = authorise(s, store, idea("sell", T(2026, 11, 17, 9, 45)), AT, src(st)).stp_key
    assert k1 == k2


def test_T61_keys_are_restored_from_the_journal_after_a_restart_and_plain_keys_are_unchanged(tmp_path):
    from orders.sender import OrderSender
    fake = SimpleNamespace(unresolved={"u": {"signal": "a|b", "strategy": "x"}},
                           trades={"t": SimpleNamespace(signal="sell 2026-11-17T09:40:00Z", strategy="y")})
    assert OrderSender.used_signals(fake) == {"a|b": "x", "a": "x", "b": "x", "sell 2026-11-17T09:40:00Z": "y"}
    plain_only = SimpleNamespace(unresolved={}, trades={"t": SimpleNamespace(signal="sell 1", strategy="y")})
    assert OrderSender.used_signals(plain_only) == {"sell 1": "y"}
    assert _rule11({"sell 1": "y"})("sell 1") == ["same signal already traded by y"]
    assert _rule11({"sell 1": "y"})("sell 2") == []


# ---- T-44 to T-47: sessions, restarts, rollover, weekly open ----------------------------------------------------------

def test_T44_overnight_no_gated_entry_opens_but_the_tracker_keeps_running(tmp_path):
    from safety.rules import decide  # noqa: F401  (the hours rule is the order sender's, unchanged: see T-53)
    night = T(2026, 11, 17, 22, 0)
    ok(tmp_path, store_with(night), Bi(SELL=[pd()])).run(night)
    assert opps(tmp_path) and state(tmp_path)["last_run_utc"] == "2026-11-17T22:00:00Z"


def test_T45_a_restart_reloads_the_opportunities_and_refuses_until_a_fresh_step(tmp_path):
    ok(tmp_path, store_with(NOW), Bi(SELL=[pd()])).run(NOW)
    again = OpportunityKeeper(KS(tmp_path), store_with(NOW), planner=Bi(SELL=[pd()]))
    assert [o["id"] for o in again.opportunities] == [o["id"] for o in opps(tmp_path)]
    late = NOW + timedelta(minutes=20)
    from stp.source import FileSource
    fs = FileSource(KS(tmp_path))
    v = authorise(auth_settings(tmp_path), store_with(late), idea("sell", REJ_SELL), late, fs)
    assert not v.allowed and "not current" in v.reasons[0]


def test_T46_the_rollover_carries_over_an_opportunity_whose_levels_survive(tmp_path):
    late = T(2026, 11, 17, 23, 0)
    keep = {"levels": [{"name": "daily R2", "price": "13243.7"}, {"name": "hourly swing high", "price": "13243.2"}]}
    ok(tmp_path, store_with(late), Bi(SELL=[pd(structure=keep)])).run(late)
    t = T(2026, 11, 18, 0, 0)
    ok(tmp_path, store_with(t), Bi(SELL=[pd(no_rec="x", structure=keep)])).run(t)
    assert len(opps(tmp_path)) == 1


def test_T47_after_a_weekend_gap_nothing_expires_on_time(tmp_path):
    fri = T(2026, 11, 20, 21, 0)
    ok(tmp_path, store_with(fri), Bi(SELL=[pd()])).run(fri)
    sun = T(2026, 11, 22, 23, 0)
    ok(tmp_path, store_with(sun), Bi(SELL=[pd()])).run(sun)
    assert len(opps(tmp_path)) == 1 and not any(e["event"] == "invalidated" for e in ev(tmp_path))


# ---- T-49, T-50 to T-55, T-57, T-62 to T-66: boundaries and the engine path ----------------------------------------

def test_T49_the_analyser_never_sees_stp_levels():
    import inspect
    from analyser import market_state
    assert "stp" not in inspect.getsource(market_state)
    import trade_manager.manager as tm
    assert "stp" not in inspect.getsource(tm).lower().replace("stop", "")


def test_T50_T51_T54_bypasses_apply_only_to_the_gated_strategies(tmp_path):
    from strategies.common import BOLLINGER_BOUNCE_5M, EMA_PULLBACK, allowed
    from analyser.states import CONSOLIDATION
    s = Over(PS, switches=SW(stp_authorises_entries=True, bollinger_bounce_5m=True, ema_pullback=True))
    st = SimpleNamespace(state=CONSOLIDATION, direction="none")
    r5, _ = allowed(s, BOLLINGER_BOUNCE_5M, "sell", D(13230), st, None, None)
    rep, _ = allowed(s, EMA_PULLBACK, "sell", D(13230), st, None, None)
    assert not any("analyser's state" in x for x in r5) and any("analyser's state" in x for x in rep)
    off = Over(PS, switches=SW(stp_authorises_entries=False, bollinger_bounce_5m=True))
    r_off, _ = allowed(off, BOLLINGER_BOUNCE_5M, "sell", D(13230), st, None, None)
    assert any("analyser's state" in x for x in r_off)
    from safety.rules import _one_view
    ctx = SimpleNamespace(context={"stp": {"bypass": ["one_view"]}}, strategy="level reversal", direction="sell")
    assert _one_view(ctx, None, s) == []


def _filters(sw, strategy, bypass, monkeypatch, r3=25):
    from strategies import entry_filters as ef
    monkeypatch.setattr(ef, "rsi3_at", lambda s, store, at: (D(r3), SimpleNamespace(start=NOW)))
    s = Over(PS, switches=SimpleNamespace(**(vars(PS.switches) if hasattr(PS, "switches") else {})
                                          | {"hourly_context": False, "rsi_stretch": True, "counter_trend_tiring": False,
                                             "entry_near_ema8": False} | sw))
    i = SimpleNamespace(strategy=strategy, direction="sell", time=NOW, entry_price=D(13230), state="trend",
                        state_direction="up", trend_type=None)
    return ef.check(s, None, i, bypass=bypass)


def test_T53_T66_rsi_stretch_is_bypassed_only_for_an_stp_authorised_gated_entry(monkeypatch):
    from strategies.entry_filters import RSI_STRETCH
    gated = _filters({}, "Bollinger bounce 5m", frozenset({"rsi_stretch"}), monkeypatch)
    assert gated.allowed and any("not applied: STP authorised" in x for x in gated.checked)
    plain = _filters({}, "Bollinger bounce 5m", frozenset(), monkeypatch)
    assert not plain.allowed and plain.rule == RSI_STRETCH              # authorisation off: refused as today
    other = _filters({}, "EMA pullback", frozenset(), monkeypatch)
    assert not other.allowed and other.rule == RSI_STRETCH              # every other strategy: as today


def test_T52_T57_the_strategies_own_stop_take_profit_and_ideas_are_unchanged_by_the_context_field():
    from strategies.bollinger_bounce_5m.strategy import candidates
    from levels.current import LevelList
    lv = with_stp(LevelList(NOW, NOW, None, None, [], []),
                  {"opportunities": [opp("SELL", (13117.6, 13128.6), levels=[("weekly pivot", "13127.3", True)])]})
    w, events = _watch(lv, REJECTION_CANDLES)
    a, b = candidates(w, events, True), candidates(w, events, False)
    assert [(c.strategy, c.direction, c.time, c.entry_price, c.steps) for c in a] == \
        [(c.strategy, c.direction, c.time, c.entry_price, c.steps) for c in b]
    assert all(set(c.context) == {"rejection_candle"} for c in a) and all(c.context == {} for c in b)


def test_T55_the_trade_manager_and_order_sender_never_read_stp():
    import inspect
    import orders.sender
    import trade_manager.manager
    for m in (trade_manager.manager,):
        assert "planner" not in inspect.getsource(m) and "stp." not in inspect.getsource(m)
    assert "stp/authorise" not in inspect.getsource(orders.sender)


def test_T62_a_refused_trigger_is_not_retried_queued_or_sent_later(monkeypatch, tmp_path):
    from trading import engine as eng
    tried = []
    monkeypatch.setattr("stp.authorise.authorise", lambda *a, **k: (tried.append(a[2]), SimpleNamespace(
        allowed=False, reasons=["no live STP opportunity"]))[1])
    src_ = SimpleNamespace(state_at=lambda t=None: None, version=lambda t=None: None)
    e = SimpleNamespace(s=auth_settings(tmp_path), runner=SimpleNamespace(stp=src_, stp_version=lambda: None),
                        store=None, now=lambda: AT, replay=False, partial=None, _last_tick=None,
                        book=SimpleNamespace(decision=lambda *a, **k: None))
    i = SimpleNamespace(strategy="Bollinger bounce 5m", direction="sell", time=AT, entry_price=D(13231), context={},
                        steps=[])
    r = eng.Trading._place(e, i, None)
    assert r.what == "STP refused" and len(tried) == 1
    # the engine records the try before _place (engine.fired), so the same strategy, direction and candle are never
    # sent again on that candle, live or at its close (trading/engine.py _live_entries and _take_new_candles)
    import inspect
    src = inspect.getsource(eng.Trading._live_entries)
    assert src.index("self.fired.add(key)") < src.index("self._place(idea, td)")


def test_T63_T64_an_in_progress_setup_binds_to_an_opportunity_published_after_its_rejection_candle_oldest_first(tmp_path):
    s, store = auth_settings(tmp_path), auth_store()
    new = opp("SELL", (13240, 13250), oid="NEW", created=T(2026, 11, 17, 10, 0, 3))      # after REJ_SELL (09:40)
    assert authorise(s, store, idea("sell", REJ_SELL), AT, src(auth_state(new))).opportunity["id"] == "NEW"
    old = opp("SELL", (13238, 13248), oid="OLD", created=T(2026, 11, 17, 6, 0), levels=[("daily R1", "13240", True)])
    v = authorise(s, store, idea("sell", REJ_SELL), AT, src(auth_state(new, old)))
    assert v.opportunity["id"] == "OLD" and v.stp_key.startswith("OLD#")


def test_T65_the_engine_renews_the_strategies_levels_when_stps_file_changes(monkeypatch, tmp_path):
    from trading import engine as eng
    calls = []
    version = {"v": 1}
    runner = SimpleNamespace(stp=object(), stp_version=lambda: version["v"],
                             levels_at=lambda t, memo=None: calls.append((t, version["v"])) or f"levels {version['v']}",
                             peek=lambda p, levels=None: [])
    monkeypatch.setattr(eng, "MemoStore", lambda store: None)
    e = SimpleNamespace(runner=runner, store=None, partial=None, _levels=None, s=None, fired=set(),
                        _forming=lambda tick: SimpleNamespace(start=NOW))
    tick = SimpleNamespace(time=NOW, sell=D(1), buy=D(1))
    eng.Trading._live_entries(e, tick)
    eng.Trading._live_entries(e, tick)
    version["v"] = 2
    eng.Trading._live_entries(e, tick)
    assert calls == [(NOW, 1), (NOW, 2)] and e._levels[1] == "levels 2"
