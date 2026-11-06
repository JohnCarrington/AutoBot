# The IG connection

The `ig/` part is the only part of the bot that talks to IG's servers. It logs in, chooses the bot's account and handles IG's errors. It does not fetch prices or place orders; the price feed and the order sender will use it for that later.

- Code: `ig/client.py` (talking to IG), `ig/errors.py` (the error rules and the exit code), `ig/secrets.py` (reading `.env`), `ig/check.py` (the one real check).
- It talks to IG's REST API directly with the `requests` library (version pinned in `requirements.txt`). It does not use the `trading_ig` library.
- IG's demo address comes from the settings file (`ig.demo_base_url`). Only the demo address is allowed.
- Every call has a time limit (`ig.request_timeout_seconds`, 30 seconds).

## Secrets

- The IG login details are in `/opt/autobot/.env`: `IG_USERNAME`, `IG_PASSWORD`, `IG_API_KEY` and `IG_ACCOUNT_ID`. Git ignores this file, so it is never committed.
- The bot reads `.env` itself. Lines starting with `#` are comments. A `#` inside a value is kept as part of the value, because a password may contain one.
- Passwords, API keys, session tokens and account numbers are never printed, logged, or put in an error message. Wherever an account number has to be shown, only its last 4 characters appear, like `****AB12`.
- If `.env` is missing, or any of the four values is missing or empty, the bot stops before making any IG call.

## Logging in

1. The bot logs in with IG's **version 2** login: `POST /session`, sending the username and password, with the API key in a header.
2. It keeps the **two session tokens** IG sends back (`CST` and `X-SECURITY-TOKEN`) and the **streaming address** (`lightstreamerEndpoint`) from IG's reply. The price feed will need the streaming address later.
3. If the streaming address is missing or blank, the bot **stops**. It also stops if either session token is missing.
4. **Only ever one login at a time.**
   - The bot refuses to log in while it is already logged in.
   - A re-login can only happen while no other login is running. If two parts of the bot find the session has expired at the same moment, only one logs in again and the other uses the new session.
5. **Never log in in a loop.** The only times the bot logs in again are the waits after a slow-down (at most 4 waits) and the single controlled re-login described below. Each has a fixed limit, and after that the bot stops.
6. When IG sends fresh tokens on any reply (for example, after switching account), the bot keeps them.

## Choosing the account

1. `IG_ACCOUNT_ID` must be set in `.env`. If it is not set, the bot stops before calling IG.
2. After logging in, the bot fetches IG's list of accounts (`GET /accounts`). If `IG_ACCOUNT_ID` is **not in that list**, the bot **stops**. It never falls back to a different account.
3. The bot switches to `IG_ACCOUNT_ID` with `PUT /session`, sending **`defaultAccount: false`**. This makes the account active for this session only, and **does not change IG's default account**, because other bots share this IG login.
4. A **412** reply, or the error `accountId-must-be-different`, means the account is already the active one. **That is fine**, and the bot carries on.
5. **Any other failure to switch** (any other error, or no reply): the bot **stops**.
6. After any re-login, IG's active account is back to the default, so the bot switches to `IG_ACCOUNT_ID` again in the same way.

## Errors

These rules apply to every IG call: the login, the account list, the switch, and every call the price feed and order sender make later. The bot reads both the **HTTP status code** and the **`errorCode`** in IG's reply. Only the last part of the code matters: `error.security.client-token-invalid` counts as `client-token-invalid`.

| What IG says | What the bot does |
|---|---|
| **Slowed down:** `exceeded-api-key-allowance`, `exceeded-account-allowance`, `exceeded-account-trading-allowance` | Waits **60** seconds and tries again. If still slowed down, it waits **90**, then **120**, then **180** seconds between tries (`ig.slowed_down_waits_seconds`). If IG is **still** slowing it down after the 180-second wait, it **stops**. That is 5 tries and 4 waits at most. A slow-down never causes a new login. |
| **`client-token-invalid`** | **One controlled re-login**, then the same call is tried again. If the re-login fails, or IG still does not accept the session afterwards, the bot **stops**. |
| **Session expired:** a **401** on any call after login with `client-token-invalid`, `client-token-missing`, `account-token-invalid` or `account-token-missing` | Treated exactly like `client-token-invalid`: one controlled re-login (and switch back to the account), then stop if that fails. |
| `client-suspended`, `account-suspended`, `account-locked`, `api-key-invalid`, `api-key-disabled`, `api-key-revoked`, `invalid-details` | **Stops at once. No retry.** |
| **Any other 401 or 403**, including one with no `errorCode` or an unknown one | **Stops at once. No retry.** |
| Any other failure **while logging in or choosing the account** (for example HTTP 500 or no reply) | **Stops.** No retry. |
| Any other failure on a **later** call (for example HTTP 500 or no reply on a price request) | That is not a login problem. The error goes back to the part that made the call, which decides what to do. This part does not log in again. |

### What "stop" means

When the bot stops because of a login problem, it:

1. writes a clear message saying which error it was, for example
   `AutoBot STOPPED. IG login failure [account-suspended]: IG refused the login (HTTP 403). This will not get better by trying again. No retry.`
2. then exits with **exit code 78**.

**Exit code 78 is reserved for login failures.** Nothing else in the bot uses it. (78 is the standard "configuration problem" exit code.) When the bot runs as a service, the service file must contain:

```
RestartPreventExitStatus=78
```

so that a login failure does **not** restart the bot automatically. Restarting would mean logging in again and again, which can get the IG login suspended. A person must find out what went wrong and start the bot again.

(A problem in the settings file stops the bot with exit code 1 instead, before IG is ever contacted.)

## The one real check

```
.venv/bin/python -m ig.check
```

This is the only command that contacts the real IG. It makes exactly these four calls, once each, with **retries switched off**, so a slow-down or token problem stops it straight away instead of waiting or logging in again:

1. `POST /session`: log in to the IG demo account (version 2 login)
2. `GET /accounts`: list the accounts, showing only the last 4 characters of each number
3. `PUT /session`: switch to `IG_ACCOUNT_ID`, without changing the default account
4. `DELETE /session`: log out

It shows **whether** the streaming address was received, never the address itself. It prints every IG call it made, with IG's status code. If anything fails after logging in, it still logs out, then stops with exit code 78.

### Result

The real check **passed on 6 November 2026** (exit code 0), after the other bots on the IG login had been stopped. It made four IG calls:

| Call | IG's reply | Meaning |
|---|---|---|
| `POST /session` | HTTP 200 | Logged in (version 2); streaming address received |
| `GET /accounts` | HTTP 200 | 2 accounts listed; `IG_ACCOUNT_ID` (`****G4CJ`) was in the list |
| `PUT /session` | HTTP 412 | Account already active, which is fine; IG's default account not changed |
| `DELETE /session` | HTTP 204 | Logged out |

(The first run, before the other bots were stopped, was refused by IG with `exceeded-api-key-allowance`.)

## Tests

`tests/technical/test_ig_connection.py` checks every rule above against a **pretend IG** (`tests/technical/fake_ig.py`) that plays back scripted replies. While the tests run, every network connection is blocked (`tests/conftest.py`), so the tests can never reach the real IG.
