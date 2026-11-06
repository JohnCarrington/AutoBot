"""IG error codes, how each one is handled, and the login-failure exit code."""

from __future__ import annotations

import sys
from typing import NoReturn

# The bot exits with this code, and only this code, when it cannot log in to IG
# or cannot use the account. When the bot runs as a service, the service file
# must say RestartPreventExitStatus=78 so it is NOT restarted automatically.
# (78 is the standard "configuration problem" code, EX_CONFIG.)
LOGIN_FAILURE_EXIT_CODE = 78

# IG is slowing us down: wait and try again (60, 90, 120, 180 seconds).
SLOWED_DOWN = frozenset({
    "exceeded-api-key-allowance",
    "exceeded-account-allowance",
    "exceeded-account-trading-allowance",
})

# The session tokens are no longer accepted: one controlled re-login.
CLIENT_TOKEN_INVALID = "client-token-invalid"

# A 401 with one of these on a call AFTER login means the session has expired.
# It is treated exactly like client-token-invalid.
SESSION_EXPIRED = frozenset({
    CLIENT_TOKEN_INVALID,
    "client-token-missing",
    "account-token-invalid",
    "account-token-missing",
})

# These never get better by trying again: stop at once.
STOP_AT_ONCE = frozenset({
    "client-suspended",
    "account-suspended",
    "account-locked",
    "api-key-invalid",
    "api-key-disabled",
    "api-key-revoked",
    "invalid-details",
})

# IG refused a historical prices request because the weekly historical data
# allowance is used up. Not a login problem: it goes back to the history door
# (ig/history.py), which writes the block marker. Never a reason to stop or retry.
HISTORY_ALLOWANCE_EXCEEDED = frozenset({
    "exceeded-account-historical-data-allowance",
    "exceeded-historical-data-allowance",
})

# Reply to a switch when the account is already the active one. Not an error.
ALREADY_ACTIVE = "accountid-must-be-different"


def short_code(error_code: str | None) -> str | None:
    """'error.security.client-token-invalid' -> 'client-token-invalid' (lower case)."""
    if not error_code:
        return None
    return error_code.strip().rsplit(".", 1)[-1].lower()


class IGLoginFailure(Exception):
    """The bot cannot log in to IG or use its account. The bot must stop
    (exit code 78) and must NOT be restarted automatically."""

    def __init__(self, error: str, detail: str):
        self.error = error
        self.detail = detail
        super().__init__(f"IG login failure [{error}]: {detail}")


class IGRequestError(Exception):
    """An IG call failed for a reason that is not a login problem (for example
    a 500 from IG, or a network error). The part that made the call decides
    what to do. Never contains secrets."""

    def __init__(self, what: str, status: int | None, error_code: str | None):
        self.what = what
        self.status = status
        self.error_code = error_code
        details = [f"HTTP {status}" if status is not None else "no reply"]
        if error_code:
            details.append(error_code)
        super().__init__(f"{what} failed ({', '.join(details)})")


def stop_bot(failure: IGLoginFailure) -> NoReturn:
    """Write a clear message and exit with the login-failure exit code."""
    print(
        f"AutoBot STOPPED. {failure}\n"
        f"Exit code {LOGIN_FAILURE_EXIT_CODE}: login failure. The bot will not restart by itself; "
        "a person must check IG and start it again.",
        file=sys.stderr,
    )
    raise SystemExit(LOGIN_FAILURE_EXIT_CODE)
