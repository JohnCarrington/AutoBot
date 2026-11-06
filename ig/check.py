"""One real check of the IG demo connection. Run:  .venv/bin/python -m ig.check

It makes exactly these IG calls, once each, with retries switched off:
  1. POST   /session   log in (version 2 login)
  2. GET    /accounts  list the accounts
  3. PUT    /session   switch to IG_ACCOUNT_ID (IG's default account is not changed)
  4. DELETE /session   log out
No prices, no orders. Secrets are never shown; account numbers show only
their last 4 characters; the streaming address is never shown.
"""

from __future__ import annotations

import sys
from typing import Any, Callable

from config.settings_loader import load_or_exit
from ig.client import IGClient
from ig.errors import LOGIN_FAILURE_EXIT_CODE, IGLoginFailure, stop_bot
from ig.secrets import ENV_PATH, load_credentials, last4


def _never_wait(seconds: float) -> None:
    # With retries switched off the client never waits; this makes sure of it.
    raise RuntimeError("The check must not wait and retry.")


def run(settings: Any, credentials_loader: Callable[[], Any] = lambda: load_credentials(ENV_PATH),
        http: Any = None, out=sys.stdout) -> int:
    def say(text: str = "") -> None:
        print(text, file=out, flush=True)

    say("IG demo connection check (one login, retries switched off)")
    say(f"IG address: {settings.ig.demo_base_url}")
    client = None
    try:
        creds = credentials_loader()
        say(f"IG_ACCOUNT_ID: {last4(creds.account_id)}")
        client = IGClient(settings.ig, creds, http=http, retries=False, sleep=_never_wait)

        client.login()
        say("1. Logged in: yes (IG version 2 login)")
        say(f"   Streaming address received: {'yes' if client.streaming_endpoint else 'no'}")

        accounts = client.list_accounts()
        say(f"2. Accounts on this login: {len(accounts)}")
        for a in accounts:
            mark = "   <- IG_ACCOUNT_ID" if a.account_id == creds.account_id else ""
            say(f"   {last4(a.account_id)}  type={a.account_type:<10} preferred={'yes' if a.preferred else 'no'}{mark}")

        result = client.choose_account(accounts)
        say(f"3. Switched to {last4(creds.account_id)}: {result} (defaultAccount false: IG's default account not changed)")
    except IGLoginFailure as failure:
        _logout_and_report(client, say)
        stop_bot(failure)

    _logout_and_report(client, say)
    say("Check passed.")
    return 0


def _logout_and_report(client: IGClient | None, say: Callable[[str], None]) -> None:
    if client is None or not client.logged_in:
        if client is not None:
            _report_calls(client, say)
        return
    ok = client.logout()
    say(f"4. Logged out: {'yes' if ok else 'NO - IG did not confirm the log out'}")
    _report_calls(client, say)


def _report_calls(client: IGClient, say: Callable[[str], None]) -> None:
    say(f"IG calls made: {len(client.calls)}")
    for c in client.calls:
        say(f"   {c.method:<6} {c.path:<10} -> HTTP {c.status if c.status is not None else 'no reply'}")


def main() -> int:
    return run(load_or_exit())


if __name__ == "__main__":
    sys.exit(main())


__all__ = ["run", "main", "LOGIN_FAILURE_EXIT_CODE"]
