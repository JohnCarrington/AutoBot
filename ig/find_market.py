"""Look up a pair's epic once. Run:  .venv/bin/python -m ig.find_market GBPUSD

IG calls, once each, retries switched off:
  1. POST   /session                    log in
  2. GET    /accounts                   list accounts (to show the account type)
  3. PUT    /session                    switch to IG_ACCOUNT_ID (default account unchanged)
  4. GET    /markets?searchTerm=<PAIR>  the one market search
  5. DELETE /session                    log out
No other market calls and no prices. The epic it shows is then written into
config/settings.toml ([pairs.<PAIR>] epic) by hand, with the pair's pip size
and price scale (check them against IG's prices for the pair).
"""

from __future__ import annotations

import sys

from config.settings_loader import load_or_exit
from ig.check import _never_wait, _report_calls
from ig.client import IGClient
from ig.errors import IGLoginFailure, stop_bot
from ig.markets import search_markets
from ig.secrets import ENV_PATH, last4, load_credentials


def main(pair: str, settings=None, creds=None, http=None) -> int:
    pair = pair.upper()
    settings = settings or load_or_exit()
    creds = creds or load_credentials(ENV_PATH)
    client = IGClient(settings.ig, creds, http=http, retries=False, sleep=_never_wait)
    try:
        client.login()
        accounts = client.list_accounts()
        mine = [a for a in accounts if a.account_id == creds.account_id]
        print(f"Account {last4(creds.account_id)} type: {mine[0].account_type if mine else '(not found)'}")
        print(f"Switch: {client.choose_account(accounts)}")
        found = search_markets(client, pair)
        print(f"Market search for {pair!r}: {len(found)} result(s)")
        for m in found:
            print(f"  {m.epic:<28} {m.name:<40} type={m.instrument_type:<10} expiry={m.expiry:<6} status={m.status}")
    except IGLoginFailure as failure:
        client.logout()
        _report_calls(client, print)
        stop_bot(failure)
    ok = client.logout()
    print(f"Logged out: {'yes' if ok else 'NO'}")
    _report_calls(client, print)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
