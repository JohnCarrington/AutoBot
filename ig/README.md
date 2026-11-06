# ig

**What it does:** The only part of the bot that talks to IG's servers. It logs in to the IG demo account (IG's version 2 login), keeps the two session tokens and the streaming address, checks that the bot's account (`IG_ACCOUNT_ID`) is in IG's list of accounts, and switches to it without changing IG's default account. It handles IG's errors by fixed rules: it waits when IG slows it down, logs in again once if the session stops being accepted, and stops for anything else. The price feed and the order sender will make their IG calls through this part.

**What it must never do:**
- Never print, log or save a password, API key, session token or full account number. Account numbers are shown as their last 4 characters only.
- Never change IG's default account (other bots share this login).
- Never log in in a loop, or have more than one login going at a time.
- Never carry on with an account other than `IG_ACCOUNT_ID`.
- Never place, change or close a trade by itself.

Rules in full: `docs/IG_CONNECTION.md`. One real check: `.venv/bin/python -m ig.check`.
