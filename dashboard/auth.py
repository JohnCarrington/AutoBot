"""The dashboard's login (as AutoBot 161's: a password, then a signed session cookie; owner, 8 November 2026).

  * DASHBOARD_PASSWORD and DASHBOARD_SECRET_KEY are read from .env (never printed or logged). Unlike 161, the
    dashboard refuses to start if either is missing or too short (an empty password must never open the gate).
  * The password is compared in constant time (hmac.compare_digest).
  * The cookie (COOKIE) holds {"exp": seconds, "csrf": token}, base64url, and an HMAC-SHA256 signature made with
    DASHBOARD_SECRET_KEY; it lasts dashboard.session_days (30, as 161) and is HttpOnly and SameSite=Strict. It is
    not marked Secure: the page is plain HTTP inside the owner's Tailscale network (WireGuard-encrypted).
  * The csrf token in the cookie must come back in the X-CSRF-Token header of the pause switch's request
    (another website can neither read the cookie nor this server's answers, so it cannot send it).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from pathlib import Path

from config.env_file import env_path, parse

COOKIE = "autobot_dashboard"
MIN_PASSWORD, MIN_SECRET = 12, 32


class DashboardNotSetUp(Exception):
    pass


@dataclass(frozen=True)
class DashboardSecrets:
    password: str
    secret_key: str

    def __repr__(self) -> str:                         # never show them
        return "DashboardSecrets(****)"


def load_secrets(path: str | Path | None = None) -> DashboardSecrets:
    path = Path(path or env_path())
    try:
        values = parse(path.read_text())
    except (FileNotFoundError, PermissionError):
        raise DashboardNotSetUp(f"{path} cannot be read.") from None
    pw, key = values.get("DASHBOARD_PASSWORD", ""), values.get("DASHBOARD_SECRET_KEY", "")
    problems = []
    if len(pw) < MIN_PASSWORD:
        problems.append(f"DASHBOARD_PASSWORD must be set in {path}, at least {MIN_PASSWORD} characters")
    if len(key) < MIN_SECRET:
        problems.append(f"DASHBOARD_SECRET_KEY must be set in {path}, at least {MIN_SECRET} characters")
    if problems:
        raise DashboardNotSetUp("; ".join(problems) + ". The dashboard does not start without them.")
    return DashboardSecrets(pw, key)


def password_ok(given: str, s: DashboardSecrets) -> bool:
    return hmac.compare_digest(given.encode("utf-8"), s.password.encode("utf-8"))


def _sign(payload: bytes, key: str) -> str:
    return base64.urlsafe_b64encode(hmac.new(key.encode("utf-8"), payload, hashlib.sha256).digest()).decode().rstrip("=")


def make_cookie(s: DashboardSecrets, days: int, now: float | None = None) -> tuple[str, str]:
    """A new session: (cookie value, its csrf token)."""
    csrf = secrets.token_urlsafe(24)
    payload = json.dumps({"exp": int((now or time.time()) + days * 86400), "csrf": csrf}, separators=(",", ":")).encode()
    body = base64.urlsafe_b64encode(payload).decode().rstrip("=")
    return f"{body}.{_sign(payload, s.secret_key)}", csrf


def read_cookie(value: str | None, s: DashboardSecrets, now: float | None = None) -> dict | None:
    """The session if the cookie is genuine and not expired, else None."""
    if not value or "." not in value:
        return None
    body, sig = value.rsplit(".", 1)
    try:
        payload = base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
    except Exception:                                   # noqa: BLE001
        return None
    if not hmac.compare_digest(sig, _sign(payload, s.secret_key)):
        return None
    try:
        data = json.loads(payload)
    except ValueError:
        return None
    if not isinstance(data, dict) or data.get("exp", 0) < (now or time.time()) or not data.get("csrf"):
        return None
    return data


def cookie_header(value: str, days: int) -> str:
    return f"{COOKIE}={value}; Path=/; Max-Age={days * 86400}; HttpOnly; SameSite=Strict"


def clear_cookie_header() -> str:
    return f"{COOKIE}=; Path=/; Max-Age=0; HttpOnly; SameSite=Strict"
