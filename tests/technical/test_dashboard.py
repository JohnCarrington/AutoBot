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
