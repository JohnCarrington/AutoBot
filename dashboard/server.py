"""The dashboard's data service (design section 9; hosted as AutoBot 161's, owner, 8 November 2026): it listens on
127.0.0.1 only (dashboard.port), behind nginx, which listens on this server's Tailscale address only (port 3000,
deploy/autobot-dashboard.nginx) and serves the page (dashboard/static/index.html).

    .venv/bin/python -m dashboard.server        (systemd: deploy/autobot-dashboard.service)

  POST /auth          {"password": "..."}: a signed session cookie (dashboard/auth.py); 401 if wrong; 429 after
                      dashboard.login_failures_per_minute wrong ones in a minute.
  POST /logout        ends the session.
  GET  /auth-check    200 with a genuine session, else 401 (nginx's auth_request for every gated address).
  GET  /api/status    the trading engine's status (data/trading/<PAIR>/status.json, written by the price service
                      every few seconds): the analyser's state and direction, the strategies allowed now, the open
                      trades with live pips, today's trades and pips, warnings, whether TRADING is on, the pause
                      switch, and this session's csrf token. A status older than dashboard.status_stale_seconds
                      (or none) is a warning.
  POST /api/pause     {"paused": true|false}: the pause switch (the file trading.pause_file). Needs the session, its
                      csrf token in X-CSRF-Token, and no Origin from another site. Each change is recorded
                      (records/book.py) and sent on Telegram.
It never contacts IG and never places, changes or closes a trade.
"""

from __future__ import annotations

import json
import logging
import sys
import threading
import time
from collections import deque
from datetime import datetime, timezone
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from dashboard.auth import COOKIE, clear_cookie_header, cookie_header, load_secrets, make_cookie, password_ok, read_cookie

log = logging.getLogger("autobot.dashboard")
UTC = timezone.utc
HOST = "127.0.0.1"                                       # never anything else: nginx is the only way in


class Dashboard:
    """Everything the handler needs; separate so tests can drive it."""

    def __init__(self, settings: Any, secrets: Any, alerts: Any, now: Any = lambda: datetime.now(UTC)):
        self.s, self.secrets, self.alerts, self.now = settings, secrets, alerts, now
        self.d = settings.dashboard
        self.failures: deque = deque()
        self._lock = threading.Lock()

    # ---- sessions -------------------------------------------------------------------------------

    def session(self, cookie_text: str | None) -> dict | None:
        if not cookie_text:
            return None
        c = SimpleCookie()
        try:
            c.load(cookie_text)
        except Exception:                                   # noqa: BLE001
            return None
        m = c.get(COOKIE)
        return read_cookie(m.value if m else None, self.secrets, self.now().timestamp())

    def login(self, password: str) -> tuple[int, dict, str | None]:
        with self._lock:
            t = self.now().timestamp()
            while self.failures and self.failures[0] < t - 60:
                self.failures.popleft()
            if len(self.failures) >= self.d.login_failures_per_minute:
                return 429, {"ok": False, "error": "too many wrong passwords: wait a minute"}, None
            if not password_ok(password, self.secrets):
                self.failures.append(t)
                log.warning("Dashboard: a wrong password.")
                return 401, {"ok": False}, None
        value, _csrf = make_cookie(self.secrets, self.d.session_days, self.now().timestamp())
        log.info("Dashboard: logged in.")
        return 200, {"ok": True}, cookie_header(value, self.d.session_days)

    # ---- the status ---------------------------------------------------------------------------------

    def status_file(self) -> Path:
        return Path(self.d.status_folder) / self.s.market.pair / "status.json"

    def status(self, session: dict) -> dict:
        warnings = []
        try:
            st = json.loads(self.status_file().read_text())
        except (FileNotFoundError, ValueError):
            st = {}
            warnings.append("The trading engine has not reported: no status yet (is the price service running?)")
        if st.get("generated_utc"):
            age = (self.now() - datetime.fromisoformat(st["generated_utc"].replace("Z", "+00:00"))).total_seconds()
            if age > self.d.status_stale_seconds:
                warnings.append(f"The trading engine's status is {int(age)} seconds old (is the price service running?)")
        paused = Path(self.s.trading.pause_file).exists()
        return st | {"paused": paused, "warnings": warnings + list(st.get("warnings", [])),
                     "csrf": session["csrf"], "served_utc": self.now().strftime("%Y-%m-%dT%H:%M:%SZ")}

    # ---- the pause switch -------------------------------------------------------------------------------

    def pause(self, session: dict, headers: Any, body: dict) -> tuple[int, dict]:
        if headers.get("X-CSRF-Token") != session.get("csrf"):
            return 403, {"ok": False, "error": "missing or wrong csrf token"}
        origin = headers.get("Origin")
        if origin and origin.split("://", 1)[-1] != headers.get("Host", ""):
            return 403, {"ok": False, "error": "another site may not press the switch"}
        if not isinstance(body.get("paused"), bool):
            return 400, {"ok": False, "error": "paused must be true or false"}
        want = body["paused"]
        f = Path(self.s.trading.pause_file)
        was = f.exists()
        if want != was:
            if want:
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(f"paused from the dashboard at {self.now().strftime('%Y-%m-%dT%H:%M:%SZ')}\n")
            else:
                f.unlink()
            self._record(want)
        return 200, {"ok": True, "paused": want}

    def _record(self, paused: bool) -> None:
        from records.book import Book
        try:
            trading_on = bool(json.loads(self.status_file().read_text()).get("trading_on"))
        except (FileNotFoundError, ValueError):
            trading_on = False
        Book(self.s, paper=not trading_on).decision("pause switch", self.now(), paused=paused, by="the dashboard")
        text = ("AutoBot: new trades PAUSED from the dashboard. Open trades are still managed." if paused
                else "AutoBot: new trades RESUMED from the dashboard.")
        log.info(text)
        self.alerts.info(text)


def handler_for(app: Dashboard):
    class Handler(BaseHTTPRequestHandler):
        server_version = "AutoBotDashboard"

        def log_message(self, fmt, *args):              # no request lines in the log (no secrets either way)
            pass

        def _send(self, code: int, data: dict | None = None, cookie: str | None = None) -> None:
            body = b"" if data is None else json.dumps(data).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            if cookie:
                self.send_header("Set-Cookie", cookie)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _body(self) -> dict:
            n = int(self.headers.get("Content-Length") or 0)
            if n > 10_000:
                return {}
            try:
                data = json.loads(self.rfile.read(n) or b"{}")
            except ValueError:
                return {}
            return data if isinstance(data, dict) else {}

        def do_GET(self):
            sess = app.session(self.headers.get("Cookie"))
            if self.path == "/auth-check":
                return self._send(200 if sess else 401)
            if self.path == "/api/status":
                return self._send(200, app.status(sess)) if sess else self._send(401, {"ok": False})
            return self._send(404, {"ok": False})

        def do_POST(self):
            if self.path == "/auth":
                code, data, cookie = app.login(str(self._body().get("password", "")))
                return self._send(code, data, cookie)
            if self.path == "/logout":
                return self._send(200, {"ok": True}, clear_cookie_header())
            sess = app.session(self.headers.get("Cookie"))
            if self.path == "/api/pause":
                if not sess:
                    return self._send(401, {"ok": False})
                code, data = app.pause(sess, self.headers, self._body())
                return self._send(code, data)
            return self._send(404, {"ok": False})

    return Handler


def serve(settings: Any = None, secrets: Any = None, alerts: Any = None) -> ThreadingHTTPServer:
    """The server, listening on 127.0.0.1:dashboard.port (not yet serving)."""
    from alerts.telegram import Alerts
    from config.settings_loader import load_or_exit
    settings = settings or load_or_exit().pairs_on()[0]
    secrets = secrets or load_secrets()
    alerts = alerts if alerts is not None else Alerts.from_env(settings)
    return ThreadingHTTPServer((HOST, settings.dashboard.port), handler_for(Dashboard(settings, secrets, alerts)))


def main() -> int:
    from dashboard.auth import DashboardNotSetUp
    from housekeeping.logs import setup_logging
    from config.settings_loader import load_or_exit
    settings = load_or_exit().pairs_on()[0]
    setup_logging(settings.housekeeping, "dashboard")
    try:
        server = serve(settings)
    except DashboardNotSetUp as e:
        log.error("%s", e)
        print(f"AutoBot dashboard cannot start: {e}", file=sys.stderr)
        return 78                                       # systemd: do not restart (RestartPreventExitStatus)
    log.info("Dashboard data service listening on %s:%d (nginx is the way in).", HOST, settings.dashboard.port)
    try:
        server.serve_forever()
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
