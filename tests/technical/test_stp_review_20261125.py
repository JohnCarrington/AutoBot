"""Independent review follow-up (25 November 2026), points 1 to 3: each test reproduces the case the reviewer raised
on the real tracker / authorisation code, offline (scripted planners, in-memory candle stores)."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace

from planner.keeper import COMPLETED, INVALIDATED
from planner.opportunities import ACTIVE, BROKEN
from stp.authorise import authorise, which_test
from tests.planner_helpers import FakeStore
from tests.technical.test_stp_integration import (AT, Bi, auth_settings, auth_state, ev, five, hour, idea, ok, opp,
                                                  opps, pd, src, state, store_with)
from tests.technical.test_planner import T

NOW = T(2026, 11, 17, 9, 0)


# ---- point 1: a destination reached while BROKEN, then a reclaim -----------------------------------------------------

def _broken_then_destination_then_reclaim(tmp):
    plans = Bi(SELL=[pd()])                                        # SELL zone 13240-13250, primary 13170 (13165-13170)
    ok(tmp, store_with(NOW, 13245), plans).run(NOW)                # created; price in the zone: Watch & Wait next
    h1 = hour(NOW, 13245, 13254, 13244, 13253)                     # 09:00 closes 13253: 3 pips beyond 13250, BROKEN
    t1 = NOW + timedelta(hours=1)
    ok(tmp, store_with(t1, 13245, extra1=[h1]), plans).run(t1)
    assert opps(tmp)[0]["status"] == BROKEN and opps(tmp)[0]["ever_active"]
    dest = five(NOW + timedelta(hours=1, minutes=30), 13245, 13246, 13168, 13240)   # 10:30 reaches the destination
    h2 = hour(t1, 13253, 13256, 13168, 13245)                      # 10:00 closes back inside at 13245: the reclaim
    t2 = NOW + timedelta(hours=2)
    store = store_with(t2, 13245, extra5=[dest], extra1=[h1, h2])
    ok(tmp, store, plans).run(t2)
    return store, t2


def test_R1_a_destination_reached_while_broken_ends_the_opportunity_and_it_never_authorises(tmp_path):
    store, t2 = _broken_then_destination_then_reclaim(tmp_path)
    live = [o for o in opps(tmp_path) if o["lineage"] == opps(tmp_path)[0]["lineage"]] if opps(tmp_path) else []
    ended = [e for e in ev(tmp_path) if e["event"] in ("completed", "invalidated")]
    assert ended and ended[0]["event"] == "completed" and "primary destination" in ended[0]["why"]
    assert all(o["status"] != ACTIVE or o["id"] != ended[0]["id"] for o in live)
    # and the authorisation check, reading the tracker's file, refuses a sell confirmed at the zone afterwards
    st = state(tmp_path)
    v = authorise(auth_settings(tmp_path), store, _idea_at(t2 - timedelta(minutes=5)), t2 + timedelta(minutes=1), src(st))
    assert not v.allowed


def _idea_at(rej):
    i = idea("sell", rej, price="13244")
    i.time = rej + timedelta(minutes=6)
    return i


# ---- point 2: the duplicate key of an already traded structural test ---------------------------------------------------

LINEAGE_START = T(2026, 11, 17, 4, 0)
HOURS = [hour(T(2026, 11, 17, 5), 13230, 13236.5, 13229, 13232),       # 3.5 pips under 13240; inside 13235-13250
         hour(T(2026, 11, 17, 6), 13230, 13225, 13215, 13220),         # wholly clear of both zones: re-armed
         hour(T(2026, 11, 17, 7), 13230, 13241, 13229, 13238)]         # reaches both zones: a test
REJ = T(2026, 11, 17, 7, 40)


def test_R2a_which_test_numbers_the_same_rejection_candle_differently_when_the_zone_moves():
    s = auth_settings(Path("/x"))
    store = FakeStore({"1h": HOURS, "5m": []})
    before = which_test(s, store, D(13240), D(13250), LINEAGE_START, REJ)
    after = which_test(s, store, D(13235), D(13250), LINEAGE_START, REJ)
    assert (before, after) == (1, 2)          # the recount over the past hours with the new zone renumbers the test


def test_R2b_a_traded_test_keeps_its_key_after_an_hourly_zone_adjustment(tmp_path):
    """The tracker records the test with the zone in force; the key of a rejection in the traded test is unchanged
    after the zone is widened in place ("changed") at a later re-plan."""
    plans = Bi(SELL=[pd(zone=(13240, 13250)), pd(zone=(13240, 13250)), pd(zone=(13240, 13250)), pd(zone=(13240, 13250)),
                     pd(zone=(13235, 13250))])                                       # the 09:00 re-plan widens it
    extra1 = []
    for k in range(4):                                                               # 04:00 to 08:00
        t = LINEAGE_START + timedelta(hours=k)
        if k:
            extra1 = [h for h in HOURS if h.end <= t]
        ok(tmp_path, store_with(t, 13200, extra1=extra1), plans).run(t)
    o = opps(tmp_path)[0]
    s = auth_settings(tmp_path)
    store = store_with(T(2026, 11, 17, 8, 0), 13200, extra5=[five(REJ, 13230, 13238, 13229, 13232)], extra1=HOURS)
    k1 = _key(s, store, o)
    t9 = T(2026, 11, 17, 9, 0)
    ok(tmp_path, store_with(t9, 13200, extra1=HOURS), plans).run(t9)                 # zone now 13235-13250
    o2 = opps(tmp_path)[0]
    assert o2["entry_zone"]["low"] == "13235" and o2["id"] == o["id"]
    assert _key(s, store, o2) == k1


def _key(s, store, o):
    return f"{o['lineage']}#t" + str(which_test(s, store, D(o["entry_zone"]["low"]), D(o["entry_zone"]["high"]),
                                              T(2026, 11, 17, 4, 0), REJ, tests=o.get("tests")))


# ---- point 3: written recently, but the tracker says its analysis is not current --------------------------------------

def test_R3_a_file_the_tracker_marked_not_current_refuses(tmp_path):
    st = auth_state(opp("SELL", (13240, 13250)))
    st.update(current=False, data_fresh=False, not_current_reasons=["the hourly candles are out of date"])
    from tests.technical.test_stp_integration import REJ_SELL, auth_store
    v = authorise(auth_settings(tmp_path), auth_store(), idea("sell", REJ_SELL), AT, src(st))
    assert not v.allowed and "not current" in v.reasons[0] and "hourly candles are out of date" in v.reasons[0]


def test_R2c_a_superseded_successor_keeps_the_lineages_test_count(tmp_path):
    """Design 6.1: the successor keeps its history and test count. Test 1 at the old zone (05:00); the 07:00 re-plan
    supersedes it with a zone that does not overlap; a rejection at the new zone (07:40) is test 2. Recounting every
    hour against the new zone, as before, gave test 1 again: the key of the test already traded at the old zone."""
    A, B = pd(zone=(13240, 13250)), pd(zone=(13280, 13290), levels=[("daily R3", "13285", True)])
    B["entry_zone"]["levels"] = A["entry_zone"]["levels"]           # the same identity (fixed levels): a supersession
    plans = Bi(SELL=[A, A, A, B, B])
    hrs = [hour(T(2026, 11, 17, 5), 13230, 13241, 13229, 13235),      # test 1 at A
           hour(T(2026, 11, 17, 6), 13215, 13220, 13210, 13215),      # wholly clear of A: re-armed
           hour(T(2026, 11, 17, 7), 13260, 13281, 13259, 13275)]      # reaches B
    for k in range(5):                                                 # runs 04:00 .. 08:00
        t = LINEAGE_START + timedelta(hours=k)
        ok(tmp_path, store_with(t, 13200, extra1=[h for h in hrs if h.end <= t]), plans).run(t)
    o = opps(tmp_path)[0]
    assert o.get("supersedes") and o["entry_zone"]["low"] == "13280"
    rej = T(2026, 11, 17, 7, 40)
    s, store = auth_settings(tmp_path), FakeStore({"1h": hrs, "5m": []})
    args = (s, store, D(o["entry_zone"]["low"]), D(o["entry_zone"]["high"]), LINEAGE_START, rej)
    assert which_test(*args) == 1                                       # the recount against the new zone alone
    assert which_test(*args, tests=o["tests"]) == 2                      # the lineage's own count: a new test


# ---- point 4: the dashboard's opportunities list with several opportunities ------------------------------------------

def test_R4_the_dashboard_lists_several_opportunities_with_every_field_its_script_reads():
    import json as _json
    import re
    from types import SimpleNamespace
    from dashboard.stp import opportunities
    st = {"opportunities": [opp("SELL", (13240, 13250), oid="S1", created=T(2026, 11, 17, 8, 0)),
                            opp("SELL", (13260, 13270), oid="S2", status=ACTIVE, created=T(2026, 11, 17, 9, 0)),
                            opp("SELL", (13280, 13290), oid="S3", status=BROKEN, created=T(2026, 11, 17, 10, 0)),
                            opp("BUY", (13150, 13160), oid="B1", created=T(2026, 11, 17, 11, 0))]}
    st["opportunities"][2]["broken"] = {"broken_utc": "2026-11-17T12:00:00Z", "candles": 0}
    st["opportunities"][3]["relation_to_h4"] = "against"
    shown = opportunities(_json.loads(_json.dumps(st)), SimpleNamespace(zone=lambda a, b: f"{a}-{b}", real=str))
    assert [x["id"] for x in shown] == ["B1", "S3", "S2", "S1"]                       # newest first, all four
    assert [(x["label"], x["authorises"]) for x in shown] == [
        ("Waiting", True), ("Broken", False), ("Watch & Wait", True), ("Waiting", True)]
    assert shown[0]["relation_to_h4"] == "against" and shown[1]["broken_utc"] == "2026-11-17T12:00:00Z"
    # every field renderOpportunities() in the script reads is supplied for every row
    js = (Path(__file__).resolve().parents[2] / "dashboard" / "static" / "stp" / "stp.js").read_text()
    body = js[js.index("function renderOpportunities()"):js.index("function renderPlan()")]
    used = set(re.findall(r"\bo\.([a-z_0-9]+)", body))
    assert used == {"id", "trade", "label", "authorises", "zone", "zone_class", "primary", "zone_break",
                    "relation_to_h4", "created_utc", "status",
                    "lineage", "test", "binds_first", "data_gaps"}          # Phase 2 C-7 (owner, 27 November 2026)
    assert all(used <= set(x) for x in shown)


# ---- Stage A deployment check: the planner process reads the switches ------------------------------------------------

def test_R5_the_planner_process_reads_the_stp_switches_from_env_and_runs_the_multi_opportunity_tracker(
        tmp_path, monkeypatch, pretend_switches):
    """The price service starts `python -m planner run` (planner/__main__.py). Its settings must carry the .env
    switches, or make_keeper always picks the single tracker and STP_OPPORTUNITIES can never take effect."""
    import planner.__main__ as main
    import planner.opportunities as po
    from config.env_file import ENV_PATH_VAR
    from config.settings_loader import load_settings as real
    from planner.keeper import Keeper
    from planner.opportunities import OpportunityKeeper
    from tests.technical.test_planner import with_folder
    built = []
    monkeypatch.setattr("housekeeping.logs.setup_logging", lambda *a, **k: None)
    monkeypatch.setattr("planner.technical.write", lambda *a, **k: None)
    monkeypatch.setattr(main, "load_settings", lambda **kw: _Pair(real(**kw), tmp_path, with_folder))
    real_make = po.make_keeper
    monkeypatch.setattr(po, "make_keeper", lambda s, st, *a: built.append(real_make(s, st, *a)) or _NoRun())
    for value, kind in (("on", OpportunityKeeper), ("off", Keeper)):
        env = tmp_path / f"{value}.env"
        env.write_text(pretend_switches.read_text() + f"STP_OPPORTUNITIES={value}\nSTP_BIDIRECTIONAL={value}\n"
                                                      "STP_AUTHORISES_ENTRIES=off\n")
        monkeypatch.setenv(ENV_PATH_VAR, str(env))
        assert main.main(["run"]) == 0
        assert type(built[-1]) is kind
    assert built[0].bidirectional is True and built[1].s.switches.stp_opportunities is False


class _Pair:
    def __init__(self, s, tmp, with_folder):
        self.s, self.tmp, self.wf = s, tmp, with_folder

    def for_pair(self, p):
        return self.wf(self.s.for_pair(p), self.tmp / "planner")


class _NoRun:
    def run(self, now):
        pass


# ---- rule 3 and STP authorisation (owner, 25 November 2026; OD-05, OD-29, OD-30) -------------------------------------

def _r3_settings(tmp_path, pretend_switches, authorises):
    """The real settings: rule 3 on (as built 24 November), the other entry filters off, STP's switches as given."""
    from config.settings_loader import load_settings
    from tests.functional.test_counter_trend_tiring import OTHERS
    text = "".join(l + "\n" for l in pretend_switches.read_text().splitlines()
                   if not l.startswith(tuple(k + "=" for k in OTHERS + ("STP_OPPORTUNITIES", "STP_BIDIRECTIONAL",
                                                                         "STP_AUTHORISES_ENTRIES", "ONE_SIGNAL_ONE_TRADE"))))
    text += ("HOURLY_CONTEXT=off\nENTRY_NEAR_EMA8=off\nRSI_STRETCH=off\nTREND_DAY_RSI_OFF=off\nCOUNTER_TREND_TIRING=on\n"
             "COUNTER_TREND_EMERGING=on\nCOUNTER_TREND_HOURLY_CONFIRMED=on\nSTP_OPPORTUNITIES=on\nSTP_BIDIRECTIONAL=on\n"
             f"ONE_SIGNAL_ONE_TRADE=on\nSTP_AUTHORISES_ENTRIES={'on' if authorises else 'off'}\n")
    p = tmp_path / f"r3_{authorises}.env"
    p.write_text(text)
    return load_settings(switches_from=p).for_pair("GBPUSD")


def _r3_engine(s, store, monkeypatch, authorised):
    """Trading._place, the real method, on a stub engine (as T-62): STP's check scripted, the order sender recorded."""
    from trading import engine as eng
    from stp.authorise import Verdict
    calls, sent, book = [], [], []

    def stp(settings, st, idea, now, source, partial=None, tick=None):
        calls.append(idea.strategy)
        if not authorised:
            return Verdict(False, ["no live STP BUY opportunity whose zone the rejection candle reached"])
        o = {"id": "STP-R3", "trade": "BUY"}
        return Verdict(True, [], o, "STP-R3#t1", "STP-R3#t1", frozenset(settings.stp_authorisation.bypass_filters),
                       ["STP authorised: test"])
    monkeypatch.setattr("stp.authorise.authorise", stp)
    monkeypatch.setattr(eng, "day_directions", lambda *a, **k: None)
    e = SimpleNamespace(s=s, store=store, now=lambda: AT_R3, replay=False, partial=None, _last_tick=None,
                        runner=SimpleNamespace(stp=None), calendar=None, _paused=lambda: False, _trend_on=lambda: False,
                        trend_watch=SimpleNamespace(direction_at=lambda t: None),
                        book=SimpleNamespace(decision=lambda kind, t, **k: book.append((kind, k))),
                        sender=SimpleNamespace(place=lambda idea, **k: sent.append(idea) or SimpleNamespace(ok=True, what="opened", reference="R3", reasons=[], level=None)))
    return e, calls, sent, book


def _r3_idea(strategy):
    from tests.functional.test_counter_trend_tiring import idea as ct_idea
    i = ct_idea(strategy=strategy)               # a BUY against the analyser's "trend down", slow grind
    i.steps, i.context = [], {}
    return i


from tests.functional.test_counter_trend_tiring import AT as AT_R3, GROWING_DOWN  # noqa: E402


def test_R6_rule_3_is_bypassed_only_for_an_stp_authorised_entry(tmp_path, monkeypatch, pretend_switches):
    """The hourly MACD histogram below zero and growing (rule 3's own fixture): rule 3 refuses a buy against the trend
    down. Stage B: an STP-authorised gated entry is not refused by rule 3 (OD-05/OD-30 bypass_filters); a gated entry
    STP does not authorise is refused by STP before any filter; an ungated reversal strategy (the session sweep) and
    every gated strategy with STP_AUTHORISES_ENTRIES off are refused by rule 3 as before, and STP is not consulted."""
    from trading import engine as eng
    from strategies import entry_filters as ef
    from tests.functional.test_counter_trend_tiring import store_of
    store = store_of(tmp_path, GROWING_DOWN, "growing")
    on = _r3_settings(tmp_path, pretend_switches, True)
    assert "counter_trend_tiring" in on.stp_authorisation.bypass_filters
    # Stage B, STP authorised: opens; rule 3 recorded as not applied
    e, calls, sent, book = _r3_engine(on, store, monkeypatch, authorised=True)
    i = _r3_idea("Bollinger bounce")
    r = eng.Trading._place(e, i, None)
    assert r.ok and calls == ["Bollinger bounce"] and sent == [i]
    assert any("counter trend tiring: not applied: STP authorised" in x for x in i.steps)
    # the same idea without the bypass (what a non-authorised entry would get): refused by rule 3
    v = ef.check(on, store, _r3_idea("Bollinger bounce"))
    assert not v.allowed and v.rule == ef.COUNTER_TREND_TIRING
    # Stage B, a gated entry STP does not authorise: refused by STP, never sent
    e, calls, sent, book = _r3_engine(on, store, monkeypatch, authorised=False)
    r = eng.Trading._place(e, _r3_idea("Bollinger bounce 5m"), None)
    assert not r.ok and r.what == "STP refused" and sent == []
    # Stage B, an ungated reversal strategy: STP is not consulted, rule 3 refuses
    e, calls, sent, book = _r3_engine(on, store, monkeypatch, authorised=True)
    r = eng.Trading._place(e, _r3_idea("session sweep"), None)
    assert not r.ok and r.what == "entry filter refused" and calls == [] and sent == []
    assert any(k == "entry filter refused" and d.get("rule") == ef.COUNTER_TREND_TIRING for k, d in book)
    # STP_AUTHORISES_ENTRIES off: every gated strategy is checked by rule 3 as before, and STP is not consulted
    off = _r3_settings(tmp_path, pretend_switches, False)
    for strategy in ("Bollinger bounce", "Bollinger bounce 5m", "level reversal"):
        e, calls, sent, book = _r3_engine(off, store, monkeypatch, authorised=True)
        r = eng.Trading._place(e, _r3_idea(strategy), None)
        assert not r.ok and r.what == "entry filter refused" and calls == [] and sent == []


# ---- the dashboard distinguishes Stage A observation from Stage B authorisation (owner, 25 November 2026) -------------

def test_R7_the_dashboard_says_which_stage_stp_is_in_and_only_stage_b_authorises():
    from dashboard import stp as d
    gated = ["Bollinger bounce", "Bollinger bounce 5m", "level reversal"]
    def S(o, b, a):
        return SimpleNamespace(switches=SimpleNamespace(stp_opportunities=o, stp_bidirectional=b, stp_authorises_entries=a),
                               stp_authorisation=SimpleNamespace(strategies=gated))
    assert d.mode(S(False, False, False)) == {"stage": None, "authorises_entries": False, "label": d.LABEL}
    a = d.mode(S(True, True, False))
    assert a["stage"] == "A" and not a["authorises_entries"] and a["label"].startswith("STAGE A — OBSERVE ONLY")
    b = d.mode(S(True, True, True))
    assert b["stage"] == "B" and b["authorises_entries"]
    assert b["label"] == "STAGE B — STP AUTHORISES ENTRIES: BOLLINGER BOUNCE, BOLLINGER BOUNCE 5M, LEVEL REVERSAL"
    nr = d.mode(S(False, False, True))                   # authorisation on without the tracker: every gated entry refused
    assert not nr["authorises_entries"] and "EVERY GATED ENTRY IS REFUSED" in nr["label"]
    st = {"opportunities": [opp("BUY", (13047.3, 13055.1), oid="B1"), opp("SELL", (13084.1, 13093), oid="S1", status=ACTIVE)]}
    px = SimpleNamespace(zone=lambda x, y: f"{x}-{y}", real=str)
    assert [o["authorises"] for o in d.opportunities(st, px, a["authorises_entries"])] == [False, False]   # Stage A
    assert [o["authorises"] for o in d.opportunities(st, px, b["authorises_entries"])] == [True, True]    # Stage B
    # the STP tab and the main card show the server's label (never a fixed "observe only")
    js = (Path(__file__).resolve().parents[2] / "dashboard" / "static" / "stp" / "stp.js").read_text()
    html = (Path(__file__).resolve().parents[2] / "dashboard" / "static" / "index.html").read_text()
    assert "flag.textContent = o.label" in js and "stp-authorising" in js and "Stage A: observation only" in js
    assert "c.label || p.label" in html and "stpc-authorising" in html
