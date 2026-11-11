"""Technical tests for the dashboard (design 9; hosted as AutoBot 161's, on the Tailscale address only): the login
and signed cookie, the data service (run on 127.0.0.1 with a pretend status), the pause switch, the nginx and
systemd files, the page, and the trading engine's status file. Nothing here contacts IG or Telegram."""

import json
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace

import pytest

from dashboard import auth
from dashboard.server import HOST, Dashboard, handler_for
from tests.technical.test_trading import C, S, feed, idea, make, tick  # noqa: F401  (S: the fixture)

ROOT = Path(__file__).resolve().parents[2]
U = lambda *a: datetime(*a, tzinfo=timezone.utc)  # noqa: E731
SECRETS = auth.DashboardSecrets("correct horse battery", "k" * 64)


# ---- the secrets and the cookie ---------------------------------------------------------------------------

def test_the_dashboard_will_not_start_without_both_secrets(tmp_path):
    env = tmp_path / ".env"
    env.write_text("DASHBOARD_PASSWORD=\nDASHBOARD_SECRET_KEY=" + "x" * 64 + "\n")
    with pytest.raises(auth.DashboardNotSetUp, match="DASHBOARD_PASSWORD must be set"):
        auth.load_secrets(env)
    env.write_text("DASHBOARD_PASSWORD=a-long-enough-one\nDASHBOARD_SECRET_KEY=short\n")
    with pytest.raises(auth.DashboardNotSetUp, match="DASHBOARD_SECRET_KEY must be set"):
        auth.load_secrets(env)
    env.write_text("DASHBOARD_PASSWORD=a-long-enough-one\nDASHBOARD_SECRET_KEY=" + "x" * 64 + "\n")
    s = auth.load_secrets(env)
    assert "a-long-enough-one" not in repr(s) and "xxxx" not in repr(s)


def test_the_password_and_the_signed_cookie():
    assert auth.password_ok("correct horse battery", SECRETS) and not auth.password_ok("wrong", SECRETS)
    value, csrf = auth.make_cookie(SECRETS, 30, now=1_000_000)
    got = auth.read_cookie(value, SECRETS, now=1_000_000 + 29 * 86400)
    assert got["csrf"] == csrf
    assert auth.read_cookie(value, SECRETS, now=1_000_000 + 31 * 86400) is None          # expired after 30 days
    body, sig = value.rsplit(".", 1)
    assert auth.read_cookie(body + "." + sig[:-2] + "AA", SECRETS, now=1_000_000) is None  # tampered
    assert auth.read_cookie(value, auth.DashboardSecrets("x" * 12, "j" * 64), now=1_000_000) is None   # another key
    h = auth.cookie_header(value, 30)
    assert "HttpOnly" in h and "SameSite=Strict" in h and "Max-Age=2592000" in h


# ---- the data service --------------------------------------------------------------------------------------

class Alerts:
    def __init__(self):
        self.infos = []

    def info(self, text, key=None):
        self.infos.append(text)


@pytest.fixture
def svc(S, tmp_path):
    """The data service's request handler, driven in memory (the test suite never opens a network connection)."""
    clock = {"t": U(2026, 11, 4, 10, 0)}
    alerts = Alerts()
    app = Dashboard(S, SECRETS, alerts, now=lambda: clock["t"])
    return SimpleNamespace(app=app, handler=handler_for(app), clock=clock, alerts=alerts, S=S, host="100.64.0.7:3000")


def call(svc, method, path, body=None, cookie=None, headers=None):
    """One request through the real handler; returns (status, JSON body, Set-Cookie)."""
    import email.message
    import io
    data = b"" if body is None else json.dumps(body).encode()
    h = email.message.Message()
    for k, v in ({"Host": svc.host, "Content-Type": "application/json", "Content-Length": str(len(data))}
                 | ({"Cookie": cookie} if cookie else {}) | (headers or {})).items():
        h[k] = v
    req = svc.handler.__new__(svc.handler)
    req.rfile, req.wfile, req.headers = io.BytesIO(data), io.BytesIO(), h
    req.path, req.command, req.request_version = path, method, "HTTP/1.1"
    req.requestline, req.client_address, req.close_connection = f"{method} {path} HTTP/1.1", ("127.0.0.1", 0), True
    getattr(req, f"do_{method}")()
    head, _, payload = req.wfile.getvalue().partition(b"\r\n\r\n")
    lines = head.decode().split("\r\n")
    code = int(lines[0].split()[1])
    hdrs = dict(line.split(": ", 1) for line in lines[1:])
    return code, json.loads(payload or b"null"), hdrs.get("Set-Cookie")


def login(svc):
    code, data, set_cookie = call(svc, "POST", "/auth", {"password": "correct horse battery"})
    assert code == 200 and data == {"ok": True}
    return set_cookie.split(";")[0]


def write_status(svc, **over):
    f = svc.app.status_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    st = {"generated_utc": "2026-11-04T09:59:55Z", "pair": "GBPUSD", "trading_on": False,
          "analyser": {"state": "trend", "direction": "down", "trend_type": "slow grind", "since_utc": "2026-11-04T08:00:00Z"},
          "strategies_allowed": [{"name": "slow grind", "switched_on": True}], "open_trades": [],
          "today": {"trades": 2, "wins": 1, "losses": 1, "pips": "14", "gbp": "140"}, "warnings": []} | over
    f.write_text(json.dumps(st))


def test_it_listens_on_127_0_0_1_only():
    assert HOST == "127.0.0.1"
    src = (ROOT / "dashboard" / "server.py").read_text()
    assert "ThreadingHTTPServer((HOST, settings.dashboard.port)" in src and "0.0.0.0" not in src


def test_nginxs_auth_check_and_the_login(svc):
    assert call(svc, "GET", "/auth-check")[0] == 401
    assert call(svc, "POST", "/auth", {"password": "wrong"})[0] == 401
    cookie = login(svc)
    assert call(svc, "GET", "/auth-check", cookie=cookie)[0] == 200
    assert call(svc, "GET", "/auth-check", cookie=cookie[:-3] + "zzz")[0] == 401
    code, data, clear = call(svc, "POST", "/logout", cookie=cookie)
    assert code == 200 and "Max-Age=0" in clear


def test_wrong_passwords_are_limited(svc):
    for _ in range(5):
        assert call(svc, "POST", "/auth", {"password": "nope"})[0] == 401
    assert call(svc, "POST", "/auth", {"password": "correct horse battery"})[0] == 429      # even the right one, for a minute
    svc.clock["t"] += timedelta(seconds=61)
    assert call(svc, "POST", "/auth", {"password": "correct horse battery"})[0] == 200


def test_the_status_needs_a_session_and_shows_everything(svc):
    assert call(svc, "GET", "/api/status")[0] == 401
    write_status(svc)
    code, st, _ = call(svc, "GET", "/api/status", cookie=login(svc))
    assert code == 200 and st["analyser"]["state"] == "trend" and st["today"]["pips"] == "14"
    assert st["csrf"] and st["paused"] is False and st["warnings"] == [] and st["trading_on"] is False


def test_a_missing_or_old_status_is_a_warning(svc):
    cookie = login(svc)
    st = call(svc, "GET", "/api/status", cookie=cookie)[1]
    assert "no status yet" in st["warnings"][0]
    write_status(svc, generated_utc="2026-11-04T09:58:00Z", warnings=["No live price for over a minute"])
    st = call(svc, "GET", "/api/status", cookie=cookie)[1]
    assert "120 seconds old" in st["warnings"][0] and "No live price for over a minute" in st["warnings"]


def test_the_pause_switch_with_its_csrf_token(svc):
    write_status(svc)
    cookie = login(svc)
    csrf = call(svc, "GET", "/api/status", cookie=cookie)[1]["csrf"]
    pause = svc.S.trading.pause_file
    assert call(svc, "POST", "/api/pause", {"paused": True})[0] == 401                                # no session
    assert call(svc, "POST", "/api/pause", {"paused": True}, cookie=cookie)[0] == 403                 # no token
    assert call(svc, "POST", "/api/pause", {"paused": True}, cookie=cookie, headers={"X-CSRF-Token": "x"})[0] == 403
    evil = {"X-CSRF-Token": csrf, "Origin": "http://evil.example"}
    assert call(svc, "POST", "/api/pause", {"paused": True}, cookie=cookie, headers=evil)[0] == 403   # another site
    assert not pause.exists()
    ok = {"X-CSRF-Token": csrf, "Origin": f"http://{svc.host}"}
    assert call(svc, "POST", "/api/pause", {"paused": True}, cookie=cookie, headers=ok)[1] == {"ok": True, "paused": True}
    assert pause.exists() and call(svc, "GET", "/api/status", cookie=cookie)[1]["paused"] is True
    assert svc.alerts.infos == ["AutoBot: new trades PAUSED from the dashboard. Open trades are still managed."]
    assert call(svc, "POST", "/api/pause", {"paused": False}, cookie=cookie, headers=ok)[1]["paused"] is False
    assert not pause.exists() and svc.alerts.infos[-1] == "AutoBot: new trades RESUMED from the dashboard."
    rows = [json.loads(x) for x in (Path(svc.S.records.folder) / "GBPUSD" / "paper" / "decisions.jsonl").read_text().splitlines()]
    assert [(r["kind"], r["paused"], r["by"]) for r in rows] == [("pause switch", True, "the dashboard"),
                                                                  ("pause switch", False, "the dashboard")]


def test_pressing_the_switch_twice_changes_nothing_more(svc):
    cookie = login(svc)
    csrf = call(svc, "GET", "/api/status", cookie=cookie)[1]["csrf"]
    for _ in range(2):
        call(svc, "POST", "/api/pause", {"paused": True}, cookie=cookie, headers={"X-CSRF-Token": csrf})
    assert len(svc.alerts.infos) == 1


# ---- nginx and systemd --------------------------------------------------------------------------------------

def test_nginx_listens_only_on_the_tailscale_address_and_gates_the_data():
    conf = (ROOT / "deploy" / "autobot-dashboard.nginx").read_text()
    listens = re.findall(r"^\s*listen\s+([^;]+);", conf, re.M)
    assert listens == ["TAILSCALE_IP:3000"]                                     # never 0.0.0.0, never a bare port
    assert set(re.findall(r"proxy_pass\s+http://([^/;]+)", conf)) == {"127.0.0.1:8766"}
    api = conf.split("location /api/", 1)[1].split("}", 1)[0]
    assert "auth_request /_authcheck;" in api
    check = conf.split("location = /_authcheck", 1)[1].split("}", 1)[0]
    assert "internal;" in check and "/auth-check" in check
    assert "limit_req zone=autobot_dashboard_login" in conf.split("location = /auth ", 1)[1].split("}", 1)[0]
    assert 'add_header X-Frame-Options "DENY" always;' in conf and "frame-ancestors 'none'" in conf
    assert "root /opt/autobot/dashboard/static;" in conf and "return 404;" in conf
    assert "location /fonts/ {" in conf


def test_the_data_service_unit():
    unit = (ROOT / "deploy" / "autobot-dashboard.service").read_text()
    for line in ("User=autobot", "WorkingDirectory=/opt/autobot", "ExecStart=/opt/autobot/.venv/bin/python -m dashboard.server",
                 "Restart=on-failure", "RestartPreventExitStatus=78"):
        assert line in unit


def test_the_dashboards_port_matches_nginx(S):
    assert S.dashboard.port == 8766


# ---- the page ---------------------------------------------------------------------------------------------

def test_the_page_loads_nothing_from_elsewhere_and_sends_the_csrf_token():
    page = (ROOT / "dashboard" / "static" / "index.html").read_text()
    assert "<script src" not in page and "http://" not in page and "https://" not in page
    assert '"X-CSRF-Token": csrf' in page and "confirm(" in page
    for part in ("Analyser", "Strategies allowed now", "Open trades", "Today", "Warnings", "Pause new trades", "Trading"):
        assert part in page
    assert "textContent" in page and "innerHTML" not in page                    # nothing from the status is run as HTML


def test_161s_icons_and_the_home_screen_manifest():
    static = ROOT / "dashboard" / "static"
    page = (static / "index.html").read_text()
    for link in ('<link rel="icon" href="/favicon.svg" type="image/svg+xml">',
                 '<link rel="apple-touch-icon" href="/apple-touch-icon.png" sizes="180x180">',
                 '<link rel="manifest" href="/manifest.json">', '<meta name="apple-mobile-web-app-title" content="AutoBot">'):
        assert link in page
    m = json.loads((static / "manifest.json").read_text())
    assert (m["name"], m["short_name"], m["start_url"], m["display"]) == ("AutoBot", "AutoBot", "/", "standalone")
    assert [(i["src"], i["sizes"]) for i in m["icons"]] == [("/icon-192.png", "192x192"), ("/icon-512.png", "512x512")]
    def png_size(name):
        b = (static / name).read_bytes()
        assert b[:8] == b"\x89PNG\r\n\x1a\n", name
        return int.from_bytes(b[16:20], "big"), int.from_bytes(b[20:24], "big")
    assert png_size("icon-192.png") == (192, 192) and png_size("icon-512.png") == (512, 512)
    assert png_size("apple-touch-icon.png") == (180, 180)
    svg = (static / "favicon.svg").read_text()
    assert svg.lstrip().startswith("<svg") and "<script" not in svg and "#00ff88" in svg
    conf = (ROOT / "deploy" / "autobot-dashboard.nginx").read_text()
    for loc in ("location = /favicon.svg", "location = /apple-touch-icon.png", "location ~ ^/icon-(192|512)\\.png$",
                "location = /manifest.json"):
        block = conf.split(loc, 1)[1].split("}", 1)[0]
        assert "auth_request" not in block, loc                                # public, as 161
    assert "default_type application/manifest+json;" in conf


def test_the_page_has_161s_look_with_its_fonts_kept_here():
    page = (ROOT / "dashboard" / "static" / "index.html").read_text()
    for colour in ("--bg: #0a0a0f", "--surface: #111118", "--accent: #00ff88", "--red: #ff4466", "--amber: #ffaa00"):
        assert colour in page
    assert "url(fonts/jetbrains-mono-latin.woff2)" in page and "url(fonts/syne-latin.woff2)" in page
    fonts = ROOT / "dashboard" / "static" / "fonts"
    for f in ("jetbrains-mono-latin.woff2", "syne-latin.woff2", "OFL-jetbrains-mono.txt", "OFL-syne.txt"):
        assert (fonts / f).exists(), f
    assert (fonts / "jetbrains-mono-latin.woff2").read_bytes()[:4] == b"wOF2"


# ---- the trading engine's status ---------------------------------------------------------------------------

def test_the_engine_writes_the_dashboards_status(S, monkeypatch):
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, {C[1].start: [idea("EMA pullback", C[1].start)]})
    tracker.machine = SimpleNamespace(now=SimpleNamespace(state="trend", direction="down", trend_type="slow grind",
                                                          since=C[0].start))
    e.start(C[0].start)
    feed(e, clock, C[:2])
    t = C[2].start + timedelta(seconds=3)
    e.on_price(tick(t, 98.0))
    st = json.loads((Path(S.dashboard.status_folder) / "GBPUSD" / "status.json").read_text())
    assert st["trading_on"] is False and st["paused"] is False and st["analyser"]["state"] == "trend"
    (tr,) = st["open_trades"]
    assert tr["strategy"] == "EMA pullback" and tr["direction"] == "sell" and tr["live_pips"] == "0.5"   # 100 - 99.5
    names = [a["name"] for a in st["strategies_allowed"]]
    assert "EMA pullback" in names and all(a["switched_on"] for a in st["strategies_allowed"])
    assert st["price"] == {"bid": "98.0", "offer": "99.5", "time_utc": t.strftime("%Y-%m-%dT%H:%M:%SZ")}


def test_the_status_is_written_every_few_seconds_not_every_price(S, monkeypatch):
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, {})
    e.start(C[0].start)
    f = Path(S.dashboard.status_folder) / "GBPUSD" / "status.json"
    e.on_price(tick(C[2].start, 100))
    first = json.loads(f.read_text())["generated_utc"]
    e.on_price(tick(C[2].start + timedelta(seconds=2), 100.1))
    assert json.loads(f.read_text())["generated_utc"] == first
    e.on_price(tick(C[2].start + timedelta(seconds=6), 100.2))
    assert json.loads(f.read_text())["generated_utc"] != first


def test_the_status_warns_about_a_missing_price_and_unknown_funds(S, monkeypatch):
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, {})
    e.start(C[0].start)
    e.sender.funds = None
    w = e.status(C[2].start)["warnings"]
    assert "No live price for over a minute" in w and any("funds are not known" in x for x in w)


# ---- the trading history (the bot's own trade records, never IG) ------------------------------------------

def closed_row(ref, strategy, closed_utc, pips, gbp, paper=False, direction="buy", half=None):
    return {"event": "closed", "paper": paper, "reference": ref, "strategy": strategy, "direction": direction,
            "opened_utc": closed_utc, "closed_utc": closed_utc, "open_price": "13400.0",
            "close_price": "13420.0", "pips": pips, "gbp": gbp, "result": "win" if float(gbp) > 0 else "loss",
            "how_closed": "take profit hit at IG", "close_reason": "the take profit at IG", "best_pips": pips,
            "minutes_open": 30, "market_state": "trend up", "half_close": half, "steps": ["not sent to the page"]}


def write_records(svc, real, paper=()):
    base = Path(svc.S.records.folder) / "GBPUSD"
    (base / "paper").mkdir(parents=True, exist_ok=True)
    opened = {"event": "opened", "paper": False, "reference": "X", "strategy": "slow grind", "opened_utc": "2026-11-04T08:00:00Z"}
    (base / "trades.jsonl").write_text("".join(json.dumps(r) + "\n" for r in [opened, *real]) + "not json\n")
    (base / "paper" / "trades.jsonl").write_text("".join(json.dumps(r) + "\n" for r in paper))


REAL = [closed_row("A1", "slow grind", "2026-08-03T09:00:00Z", "20.0", "200.00"),          # months before: no 30-day limit
        closed_row("A2", "EMA pullback", "2026-11-02T10:00:00Z", "-12.0", "-120.00", direction="sell"),
        closed_row("A3", "slow grind", "2026-11-04T09:00:00Z", "20.0", "200.00"),
        closed_row("A4", "level reversal", "2026-11-04T23:30:00Z", "-6.5", "-65.00"),      # 23:30 UTC = 23:30 UK (GMT)
        closed_row("A5", "range trade", "2026-10-26T12:00:00Z", "5.0", "50.00", half={"pips": "8"})]
PAPER = [closed_row("P1", "breakout", "2026-11-04T12:00:00Z", "50.0", "500.00", paper=True)]


def history(svc, cookie, query=""):
    return call(svc, "GET", "/api/history" + (("?" + query) if query else ""), cookie=cookie)


def test_the_history_needs_a_session(svc):
    write_records(svc, REAL)
    assert history(svc, None)[0] == 401


def test_a_day_of_real_trades_with_totals_and_by_strategy(svc):
    write_records(svc, REAL, PAPER)
    code, h, _ = history(svc, login(svc), "from=2026-11-04&to=2026-11-04")
    assert code == 200 and (h["from"], h["to"], h["paper"]) == ("2026-11-04", "2026-11-04", False)
    assert [t["reference"] for t in h["trades"]] == ["A4", "A3"]                         # newest first, real only
    assert h["totals"] == {"trades": 2, "wins": 1, "losses": 1, "pips": "13.5", "gbp": "135.00"}
    assert h["by_strategy"] == [{"strategy": "level reversal", "trades": 1, "wins": 0, "losses": 1, "pips": "-6.5", "gbp": "-65.00"},
                                {"strategy": "slow grind", "trades": 1, "wins": 1, "losses": 0, "pips": "20.0", "gbp": "200.00"}]
    assert h["first_day"] == "2026-08-03" and h["paper_trades"] == 0
    assert "steps" not in h["trades"][0] and h["trades"][0]["paper"] is False


def test_the_paper_switch_adds_the_paper_trades_marked_as_paper(svc):
    write_records(svc, REAL, PAPER)
    h = history(svc, login(svc), "from=2026-11-04&to=2026-11-04&paper=1")[1]
    assert [(t["reference"], t["paper"]) for t in h["trades"]] == [("A4", False), ("P1", True), ("A3", False)]
    assert h["totals"]["trades"] == 3 and h["totals"]["pips"] == "63.5" and h["paper_trades"] == 1


def test_a_period_and_every_trade_back_to_the_first(svc):
    write_records(svc, REAL)
    cookie = login(svc)
    week = history(svc, cookie, "from=2026-11-02&to=2026-11-08")[1]
    assert [t["reference"] for t in week["trades"]] == ["A4", "A3", "A2"]
    every = history(svc, cookie)[1]
    assert [t["reference"] for t in every["trades"]] == ["A4", "A3", "A2", "A5", "A1"]
    assert every["totals"] == {"trades": 5, "wins": 3, "losses": 2, "pips": "26.5", "gbp": "265.00"}
    assert every["by_strategy"][0] == {"strategy": "slow grind", "trades": 2, "wins": 2, "losses": 0, "pips": "40.0", "gbp": "400.00"}
    assert [t["half_closed"] for t in every["trades"]] == [False, False, False, True, False]


def test_days_are_uk_days(svc):
    write_records(svc, [closed_row("B1", "slow grind", "2026-07-01T23:30:00Z", "20.0", "200.00")])    # 00:30 UK (BST) on 2 July
    cookie = login(svc)
    assert history(svc, cookie, "from=2026-07-01&to=2026-07-01")[1]["trades"] == []
    assert [t["reference"] for t in history(svc, cookie, "from=2026-07-02&to=2026-07-02")[1]["trades"]] == ["B1"]


def test_no_records_and_bad_dates(svc):
    cookie = login(svc)
    h = history(svc, cookie, "from=2026-11-04&to=2026-11-04")[1]
    assert h["trades"] == [] and h["first_day"] is None and h["totals"]["trades"] == 0 and h["totals"]["pips"] == "0"
    assert history(svc, cookie, "from=4-11-2026")[0] == 400
    assert history(svc, cookie, "from=2026-11-05&to=2026-11-04")[0] == 400


def test_the_history_never_contacts_ig_and_writes_nothing(svc):
    write_records(svc, REAL)
    base = Path(svc.S.records.folder) / "GBPUSD"
    before = {p: p.read_bytes() for p in base.rglob("*") if p.is_file()}
    history(svc, login(svc), "paper=1")
    assert {p: p.read_bytes() for p in base.rglob("*") if p.is_file()} == before
    src = (ROOT / "dashboard" / "server.py").read_text()
    assert "ig." not in src.split("def history", 1)[1].split("def pause", 1)[0]


def test_the_page_has_161s_date_picker_and_period_buttons():
    page = (ROOT / "dashboard" / "static" / "index.html").read_text()
    for part in ('data-period="day"', 'data-period="week"', 'data-period="month"', 'data-period="all"',
                 ".period-bar {", ".date-picker-bar {", ".dpb-display {", ".dpb-input-hidden {", ".dp-overlay {",
                 ".dp-cell.today", ".dp-cell.sel", ".dpb-today {", ".dpb-historical {", ".dpb-live {",
                 "function openCustomDatePicker(", "function renderDatePicker(", "function getWeekBounds(",
                 "(pointer: coarse)", "'● Live'", "'Historical view'", "/api/history", 'id="paperswitch"',
                 "By strategy", "Trading history"):
        assert part in page, part
    assert "Outside 30-day history window" not in page and "isOutOfRange" not in page   # no IG 30-day limit
    assert "innerHTML" not in page


def test_the_owners_closes_are_listed_marked_but_never_in_the_bots_totals(svc):
    owner = closed_row("O1", "slow grind", "2026-11-04T17:56:27Z", "37.8", "378.00", direction="sell") | {
        "closed_by": "owner", "how_closed": "closed by owner"}
    write_records(svc, REAL + [owner])
    h = history(svc, login(svc), "from=2026-11-04&to=2026-11-04")[1]
    assert [(t["reference"], t["closed_by"]) for t in h["trades"]] == [("A4", "bot"), ("O1", "owner"), ("A3", "bot")]
    assert h["totals"] == {"trades": 2, "wins": 1, "losses": 1, "pips": "13.5", "gbp": "135.00"}
    assert h["closed_by_owner"] == {"trades": 1, "wins": 1, "losses": 0, "pips": "37.8", "gbp": "378.00"}
    assert [b["trades"] for b in h["by_strategy"] if b["strategy"] == "slow grind"] == [1]
