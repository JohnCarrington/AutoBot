"""The only part of the bot that talks to IG's servers.

Logs in (IG REST API, version 2 login), chooses the bot's account without
changing IG's default account, and handles IG's errors by the rules in
docs/IG_CONNECTION.md. No prices, no candles, no orders.
"""

from __future__ import annotations

import logging
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable

import requests

from ig.errors import (
    ALREADY_ACTIVE,
    HISTORY_ALLOWANCE_EXCEEDED,
    CLIENT_TOKEN_INVALID,
    SESSION_EXPIRED,
    SLOWED_DOWN,
    STOP_AT_ONCE,
    IGLoginFailure,
    IGRequestError,
    short_code,
)
from ig.secrets import IGCredentials, last4

log = logging.getLogger("autobot.ig")


class HistoricalPricesForbidden(RuntimeError):
    """Historical prices may only be asked for through the history door
    (ig/history.py). Any other attempt is refused before anything is sent."""


def is_historical_prices_path(path: str) -> bool:
    """IG's historical prices live under /prices (GET /prices/{epic}, with or
    without a resolution and dates). The bot must never call them."""
    p = path.split("?", 1)[0].rstrip("/").lower()
    return p == "/prices" or p.startswith("/prices/")


@dataclass(frozen=True)
class IGAccount:
    account_id: str
    account_type: str
    preferred: bool

    def __repr__(self) -> str:  # never show the full account number
        return f"IGAccount({last4(self.account_id)}, {self.account_type}, preferred={self.preferred})"


@dataclass(frozen=True)
class CallRecord:
    """One IG call, for the record. Holds no secrets."""
    method: str
    path: str
    status: int | None


def error_code_of(response: Any) -> str | None:
    """The errorCode in IG's reply, or None if there isn't one."""
    try:
        body = response.json()
    except Exception:
        return None
    if isinstance(body, dict) and isinstance(body.get("errorCode"), str):
        return body["errorCode"]
    return None


class _Tries:
    """Counts the slow-down waits and re-logins for one piece of work, so
    neither can ever turn into a loop."""

    def __init__(self, client: "IGClient", what: str):
        self.client = client
        self.what = what
        self.waits_used = 0
        self.relogins_used = 0

    def slowed_down(self, code: str, status: int) -> None:
        waits = self.client.slowed_down_waits
        if not self.client.retries:
            raise IGLoginFailure(code, f"IG is slowing us down (HTTP {status}) during {self.what}. "
                                       "Retries are switched off for this run, so stopping.")
        if self.waits_used >= len(waits):
            raise IGLoginFailure(code, f"IG was still slowing us down (HTTP {status}) during {self.what} "
                                       f"after waiting {', '.join(map(str, waits))} seconds. Stopping.")
        wait = waits[self.waits_used]
        self.waits_used += 1
        log.warning("IG is slowing us down (%s) during %s. Waiting %s seconds before trying again "
                    "(wait %d of %d).", code, self.what, wait, self.waits_used, len(waits))
        self.client._sleep(wait)

    def may_relogin(self, code: str, status: int) -> None:
        """Allow one controlled re-login, or stop."""
        if not self.client.retries:
            raise IGLoginFailure(code, f"IG did not accept the session (HTTP {status}) during {self.what}. "
                                       "Retries are switched off for this run, so stopping.")
        if self.relogins_used >= 1:
            raise IGLoginFailure(code, f"IG still did not accept the session (HTTP {status}) during {self.what} "
                                       "after one re-login. Stopping.")
        self.relogins_used += 1
        log.warning("IG did not accept the session (%s) during %s. One controlled re-login.", code, self.what)


class IGClient:
    """Talks to IG's REST API. One instance per bot."""

    def __init__(
        self,
        ig_settings: Any,
        credentials: IGCredentials,
        *,
        http: Any = None,
        sleep: Callable[[float], None] = time.sleep,
        retries: bool = True,
    ):
        self.base_url = ig_settings.demo_base_url
        self.slowed_down_waits = tuple(ig_settings.slowed_down_waits_seconds)
        self.timeout = ig_settings.request_timeout_seconds
        self._creds = credentials
        self._http = http if http is not None else requests.Session()
        self._sleep = sleep
        self.retries = retries

        self._cst: str | None = None
        self._security_token: str | None = None
        self.streaming_endpoint: str | None = None
        self.account_active = False

        # Only ever one login at a time.
        self._login_lock = threading.Lock()
        self._session_number = 0  # goes up by one at every successful login
        self.calls: list[CallRecord] = []
        # Open only while ig/history.py sends one request that passed its checks.
        self._history_door = threading.local()
        self._history_door.is_open = False

    # ---- state ----------------------------------------------------------

    @property
    def logged_in(self) -> bool:
        return self._cst is not None and self._security_token is not None

    @property
    def account_id_masked(self) -> str:
        return last4(self._creds.account_id)

    # ---- sending ----------------------------------------------------------

    def _headers(self, version: str, with_session: bool) -> dict[str, str]:
        h = {
            "X-IG-API-KEY": self._creds.api_key,
            "Version": version,
            "Accept": "application/json; charset=UTF-8",
            "Content-Type": "application/json; charset=UTF-8",
        }
        if with_session:
            if not self.logged_in:
                raise RuntimeError("Not logged in to IG.")
            h["CST"] = self._cst  # type: ignore[assignment]
            h["X-SECURITY-TOKEN"] = self._security_token  # type: ignore[assignment]
        return h

    def _send(self, method: str, path: str, version: str, body: Any = None,
              with_session: bool = True) -> Any:
        """One HTTP request. Raises IGRequestError on a network problem."""
        if is_historical_prices_path(path) and not (getattr(self._history_door, "is_open", False) and method == "GET"):
            # Refused before anything is sent, and not recorded as a call.
            raise HistoricalPricesForbidden(
                f"Refused {method} {path.split('?', 1)[0]}: historical prices may only be asked for "
                "through the history door (ig/history.py).")
        try:
            response = self._http.request(
                method, self.base_url + path,
                headers=self._headers(version, with_session),
                json=body, timeout=self.timeout,
            )
        except requests.RequestException as e:
            self.calls.append(CallRecord(method, path, None))
            raise IGRequestError(f"{method} {path}", None, type(e).__name__) from None
        self.calls.append(CallRecord(method, path, response.status_code))
        return response

    def _keep_new_tokens(self, response: Any) -> None:
        # IG may send fresh tokens on any reply (for example after a switch).
        cst = response.headers.get("CST")
        token = response.headers.get("X-SECURITY-TOKEN")
        if cst:
            self._cst = cst
        if token:
            self._security_token = token

    # ---- logging in --------------------------------------------------------

    def login(self) -> None:
        """Log in once (IG version 2 login). Stops (IGLoginFailure) if it cannot."""
        with self._login_lock:
            if self.logged_in:
                raise RuntimeError("Already logged in to IG. Only one login at a time: log out first.")
            self._login_locked()

    def _login_locked(self) -> None:
        tries = _Tries(self, "login")
        while True:  # bounded: every way round the loop uses up a wait or the one re-login
            try:
                r = self._send("POST", "/session", "2",
                               {"identifier": self._creds.username, "password": self._creds.password},
                               with_session=False)
            except IGRequestError as e:
                raise IGLoginFailure("no-reply", f"IG did not reply to the login ({e.error_code}). Stopping.") from None
            if 200 <= r.status_code < 300:
                self._accept_login(r)
                return
            code = error_code_of(r)
            short = short_code(code)
            if short in SLOWED_DOWN:
                tries.slowed_down(short, r.status_code)
                continue
            if short in STOP_AT_ONCE:
                raise IGLoginFailure(short, f"IG refused the login (HTTP {r.status_code}). This will not get "
                                            "better by trying again. No retry.")
            if short == CLIENT_TOKEN_INVALID:
                tries.may_relogin(short, r.status_code)
                continue
            if r.status_code in (401, 403):
                raise IGLoginFailure(short or f"http-{r.status_code}",
                                     f"IG refused the login (HTTP {r.status_code}). No retry.")
            raise IGLoginFailure(short or f"http-{r.status_code}",
                                 f"The login failed (HTTP {r.status_code}). Stopping.")

    def _accept_login(self, r: Any) -> None:
        cst = r.headers.get("CST")
        token = r.headers.get("X-SECURITY-TOKEN")
        if not cst or not token:
            raise IGLoginFailure("missing-session-tokens",
                                 "IG's login reply did not include both session tokens. Stopping.")
        try:
            body = r.json()
        except Exception:
            body = None
        endpoint = body.get("lightstreamerEndpoint") if isinstance(body, dict) else None
        if not isinstance(endpoint, str) or not endpoint.strip():
            raise IGLoginFailure("missing-streaming-address",
                                 "IG's login reply did not include the streaming address "
                                 "(lightstreamerEndpoint). Stopping.")
        self._cst, self._security_token = cst, token
        self.streaming_endpoint = endpoint.strip()
        self.account_active = False
        self._session_number += 1
        active = body.get("currentAccountId") if isinstance(body, dict) else None
        log.info("Logged in to IG (version 2 login). Active account at login: %s. Streaming address received.",
                 last4(active) if isinstance(active, str) else "(not given)")

    def _relogin(self, session_number_seen: int) -> None:
        """Log in again after IG stopped accepting the session, then switch
        back to the bot's account. If another thread already did it, reuse its
        new session instead of logging in a second time."""
        with self._login_lock:
            if self._session_number != session_number_seen and self.logged_in:
                return
            self._cst = self._security_token = None
            self._login_locked()
            # After a new login IG's active account is the default one again.
            self._switch(allow_relogin=False)

    # ---- after login -------------------------------------------------------

    def _call(self, method: str, path: str, version: str, body: Any = None,
              *, what: str, allow_relogin: bool = True) -> Any:
        """Make one IG call after login, applying the error rules. Returns the
        reply if it is a success, or an error that is not a login problem
        (the caller decides). Raises IGLoginFailure for login problems."""
        tries = _Tries(self, what)
        while True:  # bounded: every way round the loop uses up a wait or the one re-login
            seen = self._session_number
            r = self._send(method, path, version, body)
            if 200 <= r.status_code < 300:
                self._keep_new_tokens(r)
                return r
            code = error_code_of(r)
            short = short_code(code)
            if short in SLOWED_DOWN:
                tries.slowed_down(short, r.status_code)
                continue
            if short in STOP_AT_ONCE:
                raise IGLoginFailure(short, f"IG refused {what} (HTTP {r.status_code}). "
                                            "This will not get better by trying again. No retry.")
            if r.status_code == 401 and short in SESSION_EXPIRED:
                # An expired session is treated exactly like client-token-invalid.
                if not allow_relogin:
                    raise IGLoginFailure(short, f"IG did not accept the new session during {what} "
                                                f"(HTTP {r.status_code}). Stopping.")
                tries.may_relogin(short, r.status_code)
                self._relogin(seen)
                continue
            if short in HISTORY_ALLOWANCE_EXCEEDED:
                return r  # not a login problem: the history door handles it (block marker)
            if r.status_code in (401, 403):
                raise IGLoginFailure(short or f"http-{r.status_code}",
                                     f"IG refused {what} (HTTP {r.status_code}). No retry.")
            return r

    def list_accounts(self) -> list[IGAccount]:
        """IG's list of accounts for this login. Stops if it cannot be read."""
        try:
            r = self._call("GET", "/accounts", "1", what="listing accounts")
        except IGRequestError as e:
            raise IGLoginFailure("no-reply", f"IG did not reply when listing accounts ({e.error_code}). Stopping.") from None
        if not 200 <= r.status_code < 300:
            raise IGLoginFailure(short_code(error_code_of(r)) or f"http-{r.status_code}",
                                 f"Could not list accounts (HTTP {r.status_code}). Stopping.")
        try:
            raw = r.json().get("accounts")
            accounts = [IGAccount(str(a["accountId"]), str(a.get("accountType", "?")), bool(a.get("preferred")))
                        for a in raw]
        except Exception:
            raise IGLoginFailure("bad-accounts-reply", "IG's list of accounts could not be read. Stopping.") from None
        return accounts

    def choose_account(self, accounts: list[IGAccount]) -> str:
        """Check IG_ACCOUNT_ID is in IG's list, then switch to it without
        changing the default account. Returns 'switched' or 'already active'."""
        wanted = self._creds.account_id
        if wanted not in {a.account_id for a in accounts}:
            raise IGLoginFailure(
                "account-not-found",
                f"IG_ACCOUNT_ID {last4(wanted)} is not in IG's list of accounts for this login "
                f"({', '.join(last4(a.account_id) for a in accounts) or 'none'}). Stopping.",
            )
        return self._switch(allow_relogin=True)

    def _switch(self, *, allow_relogin: bool) -> str:
        wanted = self._creds.account_id
        # defaultAccount false: other bots share this IG login, so IG's default
        # account must never be changed.
        body = {"accountId": wanted, "defaultAccount": False}
        try:
            r = self._call("PUT", "/session", "1", body, what="switching account",
                           allow_relogin=allow_relogin)
        except IGRequestError as e:
            raise IGLoginFailure("no-reply", f"IG did not reply to the account switch ({e.error_code}). Stopping.") from None
        short = short_code(error_code_of(r))
        if 200 <= r.status_code < 300:
            result = "switched"
        elif r.status_code == 412 or short == ALREADY_ACTIVE:
            result = "already active"
        else:
            raise IGLoginFailure(short or f"http-{r.status_code}",
                                 f"Could not switch to account {last4(wanted)} (HTTP {r.status_code}). Stopping.")
        self.account_active = True
        log.info("Using account %s (%s). IG's default account was not changed.", last4(wanted), result)
        return result

    def connect(self) -> None:
        """Everything the bot needs before it can use IG: log in, check the
        account is in IG's list, and switch to it."""
        self.login()
        self.choose_account(self.list_accounts())

    def request(self, method: str, path: str, version: str, body: Any = None, *, what: str) -> Any:
        """For later parts (prices, orders): one IG call with the error rules
        applied. Raises IGRequestError for failures that are not login problems."""
        if not self.account_active:
            raise RuntimeError("Not connected to the bot's IG account. Call connect() first.")
        r = self._call(method, path, version, body, what=what)
        if not 200 <= r.status_code < 300:
            raise IGRequestError(what, r.status_code, error_code_of(r))
        return r

    @contextmanager
    def _open_history_door(self):
        """Used ONLY by ig/history.py, around one request that has passed every
        check there. A test fails if any other code uses it."""
        self._history_door.is_open = True
        try:
            yield
        finally:
            self._history_door.is_open = False

    # ---- for the price stream (ig/stream.py) ---------------------------------

    def stream_login(self) -> tuple[str, str]:
        """The user and password IG's streaming server expects: the bot's
        account, and the current session tokens. Secret: never log these."""
        if not self.account_active or not self.logged_in:
            raise RuntimeError("Not connected to the bot's IG account. Call connect() first.")
        return self._creds.account_id, f"CST-{self._cst}|XST-{self._security_token}"

    def relogin_for_stream(self) -> None:
        """The one controlled re-login after IG refused the stream's login,
        then the switch back to the bot's account. Stops (IGLoginFailure) if
        that fails. The stream decides when this is allowed."""
        if not self.retries:
            raise IGLoginFailure("stream-login-refused", "IG refused the price stream's login. "
                                                         "Retries are switched off for this run, so stopping.")
        self._relogin(self._session_number)

    def logout(self) -> bool:
        """Log out (one call, no retries). Returns True if IG confirmed it."""
        if not self.logged_in:
            return False
        try:
            r = self._send("DELETE", "/session", "1")
            ok = 200 <= r.status_code < 300
        except IGRequestError:
            ok = False
        self._cst = self._security_token = None
        self.streaming_endpoint = None
        self.account_active = False
        log.info("Logged out of IG: %s.", "confirmed" if ok else "IG did not confirm")
        return ok
