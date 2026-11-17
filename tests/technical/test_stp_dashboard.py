"""Technical tests for the Structural Trade Planner tab (dashboard/stp.py, dashboard/static/stp/, the tab in
index.html; owner's brief of 17 November 2026): candles, overlays, history, events, timestamps, authentication,
parameter checks, pagination, speed, failure isolation, the page, and that nothing here reaches IG, trading code or a
planner authorisation. Read only; never contacts IG; deterministic fixtures (tests/stp_fixtures.py)."""

import ast
import hashlib
import io
import email.message
import json
import re
import subprocess
import sys
import time
from datetime import timedelta
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace

import pytest

from dashboard import auth, stp
from dashboard.server import Dashboard, handler_for
from planner.keeper import Keeper
from prices.model import Candle
from tests.planner_helpers import FakeStore
from tests.stp_fixtures import NOW, SCENARIOS, C, T, flat_store, keeper, plan_dict, settings, write_status

ROOT = Path(__file__).resolve().parents[2]
SECRETS = auth.DashboardSecrets("correct horse battery", "k" * 64)


# ---- the HTTP handler, driven in memory (as tests/technical/test_dashboard.py) ------------------------------

class App:
    def __init__(self, s, now):
        self.app = Dashboard(s, SECRETS, SimpleNamespace(info=lambda *a, **k: None), now=lambda: now)
        self.handler = handler_for(self.app)
        value, _ = auth.make_cookie(SECRETS, 30, now.timestamp())
        self.cookie = f"{auth.COOKIE}={value}"

    def get(self, path, cookie=True):
        h = email.message.Message()
        h["Host"] = "100.64.0.7:3000"
        if cookie:
            h["Cookie"] = self.cookie
        req = self.handler.__new__(self.handler)
        req.rfile, req.wfile, req.headers = io.BytesIO(b""), io.BytesIO(), h
        req.path, req.command, req.request_version, req.requestline = path, "GET", "HTTP/1.1", "GET " + path
        req.client_address = ("127.0.0.1", 1)
        req.close_connection = True
        req.do_GET()
        raw = req.wfile.getvalue()
        head, _, body = raw.partition(b"\r\n\r\n")
        code = int(head.split(b" ")[1])
        ctype = re.search(rb"Content-Type: ([^\r]+)", head).group(1).decode()
        return code, (json.loads(body) if ctype.startswith("application/json") and body else body), ctype


@pytest.fixture
def waiting(tmp_path):
    sc = SCENARIOS["waiting"](tmp_path)
    write_status(sc.s)
    return sc


def candle(tf, start, hours, o, h, l, c, parts=1, expected=1):
    o, h, l, c = (D(str(x)) for x in (o, h, l, c))
    return Candle(tf, start, start + timedelta(hours=hours), o + 1, h + 1, l + 1, c + 1, o, h, l, c, parts, expected)


# 1-4: candles ------------------------------------------------------------------------------------------------

def test_1_to_4_candles_are_retrieved_in_order_aligned_and_never_unfinished(tmp_path):
    s = settings(tmp_path)
    now = T(2026, 11, 17, 10, 30)
    hours = [candle("1h", T(2026, 11, 17, h), 1, 13200 + h, 13205 + h, 13195 + h, 13201 + h) for h in range(0, 11)]
    fours = [candle("4h", T(2026, 11, 17, h), 4, 13200, 13210, 13190, 13205) for h in (0, 4, 8)]   # 08:00 runs to 12:00
    fives = [candle("5m", T(2026, 11, 17, 10, m), 1 / 12, 13200, 13201, 13199, 13200) for m in range(0, 35, 5)]
    store = FakeStore({"1h": list(reversed(hours)), "4h": fours, "5m": fives})
    code, d = stp.candles(s, "tf=1h&limit=500", now, store)
    assert code == 200 and d["side"] == "sell"
    ts = [c["t"] for c in d["candles"]]
    assert ts == sorted(ts) and len(ts) == len(set(ts))                                  # ordered, no duplicates
    assert ts[-1] == int(T(2026, 11, 17, 9).timestamp())                                # 10:00-11:00 unfinished: left out
    assert all(t % 3600 == 0 for t in ts)                                               # hourly alignment
    assert d["candles"][-1] == {"t": ts[-1], "o": 1.32090, "h": 1.32140, "l": 1.32040, "c": 1.32100}   # sell, real prices
    code, d4 = stp.candles(s, "tf=4h", now, store)
    assert [c["t"] for c in d4["candles"]] == [int(T(2026, 11, 17, 0).timestamp()), int(T(2026, 11, 17, 4).timestamp())]
    code, d5 = stp.candles(s, "tf=5m", now, store)
    assert d5["candles"][-1]["t"] == int(T(2026, 11, 17, 10, 25).timestamp())           # 10:30 candle not finished yet
    code, dl = stp.candles(s, "tf=1h&limit=3", now, store)
    assert len(dl["candles"]) == 3 and dl["candles"][-1]["t"] == ts[-1]                 # the newest N
    code, de = stp.candles(s, "tf=1h&end=2026-11-17T05:00:00Z", now, store)
    assert de["candles"][-1]["t"] == int(T(2026, 11, 17, 4).timestamp())                # strictly before `end`


def test_4_a_built_candle_missing_parts_is_marked_partial_not_hidden(tmp_path):
    s = settings(tmp_path)
    store = FakeStore({"1h": [candle("1h", T(2026, 11, 17, 8), 1, 1, 2, 0, 1, parts=10, expected=12)]})
    _, d = stp.candles(s, "tf=1h", T(2026, 11, 17, 12), store)
    assert d["candles"][0]["partial"] is True


# 5-7: overlays -----------------------------------------------------------------------------------------------

def test_5_structural_overlays_are_the_planners_own_recorded_levels(tmp_path):
    s = settings(tmp_path)
    p = plan_dict()
    p["candidates"] = [{"low": "13213.5", "high": "13219.9", "class": "Major", "families": ["pivot"],
                        "levels": ["daily R1 13213.5", "daily swing low 13215.5 (former support, now resistance)",
                                   "4-hour swing high 13224.5", "hourly swing low 13217.4", "weekly pivot 13286.6",
                                   "previous week low 13199.9"]}]
    p["observations"] = {"vs_daily_pivot": "above the daily pivot 13194.4", "vs_weekly_pivot": "below the weekly pivot 13286.6"}
    keeper(s, flat_store(NOW), p).run(NOW)
    o = stp.overview(s, NOW)
    got = {(lv["name"], lv["price_text"], lv["group"]) for lv in o["overlays"]["levels"]}
    assert ("daily R1", "1.32135", "daily_pivot") in got and ("4-hour swing high", "1.32245", "h4_swing") in got
    assert ("daily swing low", "1.32155", "daily_sr") in got and ("hourly swing low", "1.32174", "h1") in got
    assert ("weekly pivot", "1.32866", "weekly_pivot") in got and ("previous week low", "1.31999", "weekly_sr") in got
    assert ("daily pivot", "1.31944", "daily_pivot") in got
    assert sum(1 for lv in o["overlays"]["levels"] if lv["name"] == "weekly pivot") == 1      # not drawn twice
    recorded = {D(stp.LEVEL_RE.match(x)["price"]) for x in p["candidates"][0]["levels"]}
    for lv in o["overlays"]["levels"]:                                                       # nothing invented
        pts = D(lv["price_text"]) * 10000
        assert pts in recorded or lv["source"] in ("entry zone", "observations") or "destination" in lv["source"]


def test_6_7_entry_zone_targets_and_invalidation_are_drawn_exactly_as_recorded(waiting):
    o = stp.overview(waiting.s, waiting.now)
    pl = o["overlays"]["plan"]
    assert pl["entry_zone"] == {"low": 1.3240, "high": 1.3250, "text": "1.32400–1.32500", "class": "Major"}
    assert pl["destinations"]["primary"]["text"] == "1.31700" and pl["destinations"]["intermediate"]["text"] == "1.32100"
    assert "extended" not in pl["destinations"]                                               # none recorded: none drawn
    assert pl["invalidation_conditions"] == ["an hourly close at or above 1.32530"]
    assert o["recommendation"]["entry_zone"] == "1.32400–1.32500"
    assert "13240" not in json.dumps(o["recommendation"]["plan"])                            # no internal points shown


def test_6_no_plan_overlays_without_a_recommendation(tmp_path):
    sc = SCENARIOS["no_rec_directional"](tmp_path)
    o = stp.overview(sc.s, sc.now)
    assert o["recommendation"] is None and o["overlays"]["plan"] is None


# 8-10: history, events, timestamps ------------------------------------------------------------------------------

def test_8_9_history_is_one_row_per_id_and_events_are_in_recorded_order(tmp_path):
    sc = SCENARIOS["identical_zones"](tmp_path)
    _, h = stp.history(sc.s, "")
    ids = [r["id"] for r in h["rows"]]
    assert len(ids) == 2 and len(set(ids)) == 2
    assert {r["zone"] for r in h["rows"]} == {"1.32400–1.32500"}                             # same zone, kept apart
    first = [r for r in h["rows"] if r["outcome"] == "COMPLETED"][0]
    code, d = stp.recommendation(sc.s, "id=" + first["id"], sc.now, sc.store)
    assert code == 200
    assert [e["event"] for e in d["timeline"]] == ["created", "waiting", "active", "completed"]
    times = [e["time_utc"] for e in d["timeline"]]
    assert times == sorted(times)


def test_10_timestamps_are_utc_iso_and_kept_as_recorded(tmp_path):
    sc = SCENARIOS["completed"](tmp_path)
    rid = stp.history(sc.s, "")[1]["rows"][0]["id"]
    _, d = stp.recommendation(sc.s, "id=" + rid, sc.now, sc.store)
    raw = [json.loads(x) for x in (Path(sc.s.planner.folder) / "GBPUSD" / "recommendations.jsonl").read_text().splitlines()]
    for e in d["timeline"]:
        assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", e["time_utc"])
        assert any(r["time_utc"] == e["time_utc"] and r.get("event") == e["event"] for r in raw)
    assert d["stages"]["created"] == "2026-11-17T09:00:00Z" and d["stages"]["active"] == "2026-11-17T09:05:00Z"


# 11-13: authentication, validation, pagination --------------------------------------------------------------

@pytest.mark.parametrize("path", ["/api/stp/overview", "/api/stp/candles?tf=1h", "/api/stp/history",
                                  "/api/stp/recommendation?id=STP-GBPUSD-20261117-0900-1", "/api/stp/evaluation",
                                  "/api/stp/lib/stp.js", "/api/stp/lib/lightweight-charts.js"])
def test_11_every_stp_address_needs_the_session(waiting, path):
    a = App(waiting.s, waiting.now)
    code, body, _ = a.get(path, cookie=False)
    assert code == 401
    code, body, _ = a.get(path)
    assert code == 200


@pytest.mark.parametrize("query,error", [("tf=1d", "tf must be"), ("tf=1h&limit=0", "limit must be"),
                                         ("tf=1h&limit=1001", "limit must be"), ("tf=1h&limit=x", "whole number"),
                                         ("tf=1h&end=yesterday", "end must be")])
def test_12_candle_parameters_are_checked(waiting, query, error):
    code, d, _ = App(waiting.s, waiting.now).get("/api/stp/candles?" + query)
    assert code == 400 and error in d["error"]


@pytest.mark.parametrize("path", ["/api/stp/recommendation?id=../../etc/passwd", "/api/stp/recommendation",
                                  "/api/stp/history?size=51", "/api/stp/history?page=0", "/api/stp/history?sort=evil",
                                  "/api/stp/history?order=sideways"])
def test_12_other_parameters_are_checked(waiting, path):
    code, d, _ = App(waiting.s, waiting.now).get(path)
    assert code == 400


def test_12_only_the_listed_files_are_served(waiting):
    a = App(waiting.s, waiting.now)
    for bad in ("../server.py", "..%2Fserver.py", "index.html", "vendor/LICENSE-lightweight-charts.txt", "stp/stp.js"):
        assert a.get("/api/stp/lib/" + bad)[0] == 404
    code, body, ctype = a.get("/api/stp/lib/stp.css")
    assert code == 200 and ctype.startswith("text/css")
    assert a.get("/api/stp/nothing")[0] == 404
    assert a.get("/api/stp/recommendation?id=STP-GBPUSD-20261117-0900-9")[0] == 404


def test_13_history_pages_sorts_and_searches(tmp_path):
    sc = SCENARIOS["waiting"](tmp_path)
    for h in range(1, 6):                                   # five supersessions: six recommendations
        sc.run(NOW + timedelta(hours=h, minutes=1), [plan_dict(zone=(13240 + 50 * h, 13250 + 50 * h),
                                                                levels=[("daily R3", str(13244 + 50 * h), True)])])
    _, p1 = stp.history(sc.s, "page=1&size=4")
    _, p2 = stp.history(sc.s, "page=2&size=4")
    assert p1["total"] == 6 and p1["pages"] == 2 and len(p1["rows"]) == 4 and len(p2["rows"]) == 2
    assert not {r["id"] for r in p1["rows"]} & {r["id"] for r in p2["rows"]}
    assert p1["rows"][0]["created_utc"] >= p1["rows"][-1]["created_utc"]                   # newest first
    _, asc = stp.history(sc.s, "order=asc")
    assert asc["rows"][0]["id"].endswith("-1")
    _, q = stp.history(sc.s, "q=superseded")
    assert q["total"] == 5
    _, q = stp.history(sc.s, "q=1.32900")
    assert any(r["zone"].startswith("1.32900") for r in q["rows"])               # by zone (and reasons quoting it)
    _, q = stp.history(sc.s, "q=1001-2")
    assert q["total"] == 1 and q["rows"][0]["id"].endswith("-1001-2")


# 14: speed ------------------------------------------------------------------------------------------------------

def test_14_the_tab_answers_quickly_on_a_months_history(tmp_path):
    sc = SCENARIOS["waiting"](tmp_path)
    f = Path(sc.s.planner.folder) / "GBPUSD" / "recommendations.jsonl"
    lines = f.read_text().splitlines()
    f.write_text("\n".join(lines[:1] * 720 + lines[1:]) + "\n")                             # a month of hourly analyses
    t = time.perf_counter()
    stp.overview(sc.s, sc.now)
    stp.history(sc.s, "")
    stp.evaluation(sc.s, sc.now, sc.store)
    assert time.perf_counter() - t < 2.0


# 15: page responsiveness (the layout rules exist; screenshots check the look) ---------------------------------

def test_15_the_layout_stacks_on_small_screens_and_the_chart_takes_touch():
    css = (ROOT / "dashboard/static/stp/stp.css").read_text()
    assert "@media (max-width: 860px)" in css and "@media (max-width: 600px)" in css
    assert re.search(r"\.stp-main \{ grid-template-columns: minmax\(0, 1fr\); \}", css)
    assert ".stp-planbox { order: 1; } .stp-chartcard { order: 2; }" in css           # plan before chart on a phone
    js = (ROOT / "dashboard/static/stp/stp.js").read_text()
    assert "pinch: true" in js and "horzTouchDrag: true" in js


# 16-17: failure isolation and the existing controls --------------------------------------------------------------

def test_16_a_planner_failure_never_breaks_the_status_or_the_pause_switch(waiting, monkeypatch):
    a = App(waiting.s, waiting.now)
    def boom(*x, **y):
        raise RuntimeError("broken")
    monkeypatch.setattr(stp, "overview", boom)
    monkeypatch.setattr(stp, "card", boom)
    code, d, _ = a.get("/api/stp/overview")
    assert code == 500 and d["ok"] is False and "RuntimeError" in d["error"]
    code, st, _ = a.get("/api/status")
    assert code == 200 and "csrf" in st and st["planner"]["available"] is True                 # panel still there


def test_16_a_damaged_planner_file_shows_unavailable_not_an_error(tmp_path):
    s = settings(tmp_path)
    f = Path(s.planner.folder) / "GBPUSD"
    f.mkdir(parents=True)
    (f / "current.json").write_text("{not json")
    (f / "recommendations.jsonl").write_text('{"id": "STP-GBPUSD-20261117-0900-1", "event": "created"}\nnot json\n')
    o = stp.overview(s, NOW)
    assert o["available"] is False and o["freshness"]["state"] == "UNAVAILABLE" and o["explanation"]["scenario"] == "C"
    assert stp.history(s, "")[0] == 200


def test_17_the_existing_dashboard_addresses_are_unchanged(waiting):
    a = App(waiting.s, waiting.now)
    assert a.get("/api/status")[0] == 200 and a.get("/api/history")[0] == 200 and a.get("/auth-check")[0] == 200
    assert a.get("/api/status", cookie=False)[0] == 401


def test_17_with_the_planner_switch_off_the_tab_has_nothing(tmp_path):
    sc = SCENARIOS["waiting"](tmp_path)
    off = settings(tmp_path, observe=False)
    a = App(off, sc.now)
    assert a.get("/api/stp/overview")[0] == 404
    code, st, _ = a.get("/api/status")
    assert code == 200 and "planner" not in st


# 18-20: no broker, no trading code, no authorisation ---------------------------------------------------------

FORBIDDEN = ("ig", "orders", "trading", "trade_manager", "strategies", "safety", "rejection", "analyser.engine")


def test_18_19_the_stp_module_imports_no_broker_or_trading_code():
    tree = ast.parse((ROOT / "dashboard/stp.py").read_text())
    mods = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module} | \
           {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    assert not [m for m in mods if m.split(".")[0] in FORBIDDEN or m == "requests"], mods
    out = subprocess.run([sys.executable, "-c", "import sys, dashboard.stp as s; print(sorted(m for m in sys.modules "
                          "if m.split('.')[0] in ('ig','orders','trading','trade_manager','strategies','safety','requests')))"],
                         cwd=ROOT, capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "[]"


def test_18_the_page_code_talks_only_to_its_own_read_only_addresses():
    js = (ROOT / "dashboard/static/stp/stp.js").read_text()
    assert "/api/stp/" in js and not re.search(r"https?://(?!www\.w3\.org/2000/svg)", js)
    assert not re.search(r"method\s*:", js) and "POST" not in js and "/api/pause" not in js                # GET only
    assert "innerHTML" not in js and "insertAdjacentHTML" not in js                          # nothing run as HTML


def test_20_no_planner_authorisation_exists_or_is_switched_on():
    for f in ["dashboard/stp.py", "dashboard/server.py", "dashboard/static/stp/stp.js", "dashboard/static/index.html",
              "planner/keeper.py"]:
        text = (ROOT / f).read_text()
        assert "PLANNER_AUTHORISES_BOUNCE" not in text and "authorises_bounce" not in text


def test_20_the_issued_snapshot_is_reporting_only_and_cannot_stop_the_planner(tmp_path, monkeypatch):
    s = settings(tmp_path)
    k = keeper(s, flat_store(NOW), plan_dict())
    k.run(NOW)
    snap = [json.loads(x) for x in (Path(s.planner.folder) / "GBPUSD" / "issued.jsonl").read_text().splitlines()]
    assert len(snap) == 1 and snap[0]["id"] == k.state["recommendation"]["id"] and "history" not in snap[0]
    assert snap[0]["destinations"]["intermediate"]["price"] == "13210" and snap[0]["invalidation"]["conditions"]
    events = [json.loads(x)["event"] for x in (Path(s.planner.folder) / "GBPUSD" / "recommendations.jsonl").read_text().splitlines()]
    assert events == ["analysis", "created", "waiting"]                                       # the lifecycle file unchanged
    s2 = settings(tmp_path / "b")
    monkeypatch.setattr(Keeper, "issued_path", property(lambda self: Path("/proc/forbidden/issued.jsonl")))
    k2 = keeper(s2, flat_store(NOW), plan_dict())
    k2.run(NOW)                                                                               # the write fails...
    assert k2.state["recommendation"]["status"] == "WAITING"                                  # ...and nothing changes


# the page itself ----------------------------------------------------------------------------------------------

def test_the_page_has_the_tab_and_the_compact_card_and_loads_the_tab_only_through_the_session():
    html = (ROOT / "dashboard/static/index.html").read_text()
    assert 'href="#stp"' in html and ">Structural Trade Planner<" in html and 'id="view-stp"' in html
    assert "Open Structural Trade Planner" in html
    assert "/api/stp/lib/stp.js" in html and "/api/stp/lib/lightweight-charts.js" in html
    assert "Observed now" not in html                                     # the big diagnostic panel has gone
    nginx = (ROOT / "deploy/autobot-dashboard.nginx").read_text()
    assert "location /api/" in nginx and "auth_request /_authcheck" in nginx                  # unchanged gate


def test_the_vendored_chart_library_is_the_published_4_2_3():
    lib = (ROOT / "dashboard/static/vendor/lightweight-charts.standalone.production.js").read_bytes()
    # dist/lightweight-charts.standalone.production.js from the npm tarball 4.2.3 (tarball sha1 0a0174793fc2...)
    assert hashlib.sha256(lib).hexdigest() == "c7dda807d662a95b3d257119ed315cec669e3bdf5aaece75c480a39307f23540"
    assert b"Lightweight Charts\xe2\x84\xa2 v4.2.3" in lib[:200]
    assert (ROOT / "dashboard/static/vendor/LICENSE-lightweight-charts.txt").exists()


def test_12_query_values_are_decoded_without_any_web_library():
    q = stp.parse_qs("q=1.32%20sell&end=2026-11-17T05%3A00%3A00Z&x=&q=a+b&bad=%zz&" + "&".join(f"k{i}=1" for i in range(20)))
    assert q["q"] == ["1.32 sell", "a b"] and q["end"] == ["2026-11-17T05:00:00Z"] and q["bad"] == ["%zz"]
    assert "x" not in q and len(q) <= 10                                                    # bounded
