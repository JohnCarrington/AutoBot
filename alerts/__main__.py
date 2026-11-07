"""Send one Telegram message by hand, to check Telegram is set up:

  .venv/bin/python -m alerts test "AutoBot test message"

Prints whether Telegram accepted it and its message number. Never prints the
bot token or the chat ID. Contacts Telegram only (not IG).
"""

from __future__ import annotations

import sys

from alerts.telegram import Telegram, TelegramNotSetUp, load_telegram
from config.settings_loader import load_settings


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2 or args[0] != "test":
        print(__doc__)
        return 2
    settings = load_settings()
    try:
        tg = Telegram(load_telegram(), settings.alerts)
    except TelegramNotSetUp as e:
        print(f"Telegram is not set up: {e}")
        return 3
    r = tg.send(args[1])
    print(f"Sent: {args[1]!r}")
    print(f"Telegram: {'ACCEPTED' if r.sent else 'NOT accepted'} ({r.why})"
          + (f", message number {r.message_id}" if r.message_id is not None else ""))
    return 0 if r.sent else 1


if __name__ == "__main__":
    sys.exit(main())
