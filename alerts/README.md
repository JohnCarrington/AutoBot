# alerts

**What it does:** Sends Telegram messages to the owner (design section 9). Rules in full: `docs/ALERTS.md`.

Files: `telegram.py` (the sender, its limit on repeats, and `Alerts`, which the rest of the bot uses), `ready.py` (the Sunday and daily "ready" checks and messages), `trades.py` (the trade opened and trade closed messages, in AutoBot 161's format; sent as Telegram HTML), `__main__.py` (`python -m alerts test "..."`: one message by hand).

**What it must never do:** Never place, change or close a trade. Never print, log or send the bot token, the chat ID or any other secret. Never stop the bot from working if Telegram is unavailable. Never contact IG.
