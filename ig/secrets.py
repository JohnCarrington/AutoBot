"""Reads the IG login details from /opt/autobot/.env.

The values are secret: they are never printed, logged or put in an error
message. Account numbers are only ever shown as their last 4 characters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ig.errors import IGLoginFailure

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
REQUIRED = ("IG_USERNAME", "IG_PASSWORD", "IG_API_KEY", "IG_ACCOUNT_ID")


def last4(value: str | None) -> str:
    """Show only the last 4 characters of an account number: '****AB12'."""
    if not value:
        return "(none)"
    return "****" + value[-4:]


@dataclass(frozen=True)
class IGCredentials:
    # repr=False: printing the object can never show a secret.
    username: str = field(repr=False)
    password: str = field(repr=False)
    api_key: str = field(repr=False)
    account_id: str = field(repr=False)

    def __repr__(self) -> str:
        return f"IGCredentials(account={last4(self.account_id)}, secrets hidden)"

    __str__ = __repr__


def _parse(text: str) -> dict[str, str]:
    """KEY=value lines. Lines starting with # are comments. Values may be in
    quotes. A # inside a value is kept (passwords may contain #)."""
    values: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        values[key] = value
    return values


def load_credentials(path: str | Path = ENV_PATH) -> IGCredentials:
    """Read the IG login details. Stops (IGLoginFailure) if any is missing."""
    path = Path(path)
    try:
        text = path.read_text()
    except FileNotFoundError:
        raise IGLoginFailure("missing-env-file", f"The secrets file {path} does not exist.") from None
    except PermissionError:
        raise IGLoginFailure("missing-env-file", f"The secrets file {path} cannot be read.") from None
    values = _parse(text)
    missing = [k for k in REQUIRED if not values.get(k)]
    if missing:
        raise IGLoginFailure(
            "missing-secret",
            f"These must be set in {path}: {', '.join(missing)}. No IG call was made.",
        )
    return IGCredentials(
        username=values["IG_USERNAME"],
        password=values["IG_PASSWORD"],
        api_key=values["IG_API_KEY"],
        account_id=values["IG_ACCOUNT_ID"],
    )
