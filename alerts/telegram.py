"""Sends Telegram messages to the owner.

Secrets: the bot token and chat ID come from .env (TELEGRAM_BOT_TOKEN,
TELEGRAM_CHAT_ID). They are never printed, logged, put in a message or in an
error. The token is part of Telegram's address, so:
  * an error is reported by its kind and Telegram's own description only,
    never by the address or the library's own error text;
  * the HTTP library's request logging is kept quiet (urllib3 logs addresses).

The limit: the same problem (the same `key`) never sends more than one message
every alerts.same_problem_every_minutes. Messages held back are counted and
mentioned in the next one. The record is kept in <alerts folder>/sent.json, so
it holds across restarts too.

Telegram being unavailable never stops the bot: a failed send is written to
the log and the bot carries on.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from config.env_file import env_path, parse
from housekeeping.files import safe_write

log = logging.getLogger("autobot.alerts")
logging.getLogger("urllib3").setLevel(logging.WARNING)   # it would log Telegram's address, token included
UTC = timezone.utc
REQUIRED = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")
STATE_FILE = "sent.json"
MAX_LENGTH = 4000          # Telegram's limit is 4096 characters a message


class TelegramNotSetUp(Exception):
    pass


@dataclass(frozen=True)
class TelegramCredentials:
    token: str = field(repr=False)
    chat_id: str = field(repr=False)

    def __repr__(self) -> str:
        return "TelegramCredentials(secrets hidden)"

    __str__ = __repr__


def load_telegram(path: str | Path | None = None) -> TelegramCredentials:
    """Read the token and chat ID from .env. Names what is missing, never a value."""
    path = Path(path or env_path())
    try:
        values = parse(path.read_text())
    except (FileNotFoundError, PermissionError):
        raise TelegramNotSetUp(f"{path} cannot be read.") from None
    missing = [k for k in REQUIRED if not values.get(k)]
    if missing:
        raise TelegramNotSetUp(f"These must be set in {path}: {', '.join(missing)}.")
    return TelegramCredentials(values["TELEGRAM_BOT_TOKEN"], values["TELEGRAM_CHAT_ID"])


@dataclass
class SendResult:
    sent: bool
    why: str = ""
    message_id: int | None = None


class Telegram:
    def __init__(self, credentials: TelegramCredentials, alert_settings: Any, *, http: Any = None,
                 now: Callable[[], datetime] = lambda: datetime.now(UTC)):
        self._creds = credentials
        self.s = alert_settings
        self.now = now
        self.every = timedelta(minutes=alert_settings.same_problem_every_minutes)
        self.state_path = Path(alert_settings.folder) / STATE_FILE
        if http is None:
            import requests
            http = requests.Session()
        self._http = http

    # ---- the limit --------------------------------------------------------------

    def _state(self) -> dict:
        try:
            return json.loads(self.state_path.read_text())
        except (FileNotFoundError, ValueError):
            return {}

    def _save(self, state: dict) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        safe_write(self.state_path, (json.dumps(state, indent=1, sort_keys=True) + "\n").encode())

    # ---- sending -------------------------------------------------------------------

    def send(self, text: str, key: str | None = None) -> SendResult:
        """Send one message. With a key, at most one message per key every
        alerts.same_problem_every_minutes; the rest are held back and counted."""
        now = self.now()
        state = self._state()
        if key is not None:
            entry = state.get(key) or {}
            last = entry.get("last_sent_utc")
            if last and now - datetime.fromisoformat(last) < self.every:
                entry["held_back"] = entry.get("held_back", 0) + 1
                state[key] = entry
                self._save(state)
                log.info("Telegram message held back (the same problem was sent less than %s ago): %s",
                         self.every, text.splitlines()[0])
                return SendResult(False, "held back by the limit")
            held = entry.get("held_back", 0)
            if held:
                text += f"\n({held} more like this held back since {last[:16].replace('T', ' ')} UTC)"
        result = self._post(text[:MAX_LENGTH])
        if key is not None and result.sent:
            state[key] = {"last_sent_utc": now.isoformat(), "held_back": 0}
            self._save(state)
        return result

    def _post(self, text: str) -> SendResult:
        url = f"{self.s.telegram_url}/bot{self._creds.token}/sendMessage"
        try:
            r = self._http.post(url, json={"chat_id": self._creds.chat_id, "text": text},
                                timeout=self.s.request_timeout_seconds)
        except Exception as e:      # the error text may hold the address (and so the token): kind only
            why = f"no reply from Telegram ({type(e).__name__})"
            log.warning("Telegram message NOT sent: %s.", why)
            return SendResult(False, why)
        try:
            body = r.json()
        except Exception:
            body = {}
        if r.status_code == 200 and body.get("ok"):
            mid = (body.get("result") or {}).get("message_id")
            log.info("Telegram message sent (message %s): %s", mid, text.splitlines()[0])
            return SendResult(True, "accepted by Telegram", mid)
        desc = str(body.get("description") or "")[:200]
        why = f"Telegram refused it: HTTP {r.status_code}" + (f" ({desc})" if desc else "")
        log.warning("Telegram message NOT sent: %s.", why)
        return SendResult(False, why)


class Alerts:
    """What the rest of the bot uses. Every alert is also written to the log.
    With Telegram not set up, alerts go to the log only (the bot carries on)."""

    def __init__(self, telegram: Telegram | None):
        self.telegram = telegram

    @classmethod
    def from_env(cls, settings: Any, path: str | Path | None = None) -> "Alerts":
        try:
            return cls(Telegram(load_telegram(path), settings.alerts))
        except TelegramNotSetUp as e:
            log.warning("Telegram is not set up (%s) Alerts are written to the log only.", e)
            return cls(None)

    def problem(self, key: str, text: str) -> SendResult:
        log.warning("ALERT %s: %s", key, text)
        msg = f"AutoBot PROBLEM: {text}"
        return self.telegram.send(msg, key) if self.telegram else SendResult(False, "Telegram not set up")

    def info(self, text: str, key: str | None = None) -> SendResult:
        log.info("ALERT: %s", text.splitlines()[0])
        return self.telegram.send(text, key) if self.telegram else SendResult(False, "Telegram not set up")

    def trade_opened(self, trade: Any) -> SendResult:
        """For the order sender (not built yet): every trade opened (alerts/trades.py)."""
        from alerts.trades import opened_text
        return self.info(opened_text(trade))

    def trade_closed(self, closed: Any) -> SendResult:
        """For the order sender (not built yet): every trade closed (alerts/trades.py)."""
        from alerts.trades import closed_text
        return self.info(closed_text(closed))

