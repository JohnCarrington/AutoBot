"""Show the newest candles in the store and how old they are. Contacts nobody.
Run:  .venv/bin/python -m prices.status
"""

from __future__ import annotations

from datetime import datetime, timezone

from config.settings_loader import load_or_exit
from prices.calendar import MarketHours
from prices.feed import _age
from prices.model import TIMEFRAMES, uk
from prices.store import CandleStore


def main() -> int:
    s = load_or_exit()
    store = CandleStore(s.candles.folder, s.candles.compress_after_days)
    now = datetime.now(timezone.utc)
    hours = MarketHours(s.market_hours)
    print(f"Now: {uk(now)}. Market {'OPEN' if hours.is_open(now) else 'closed'}.")
    for tf in TIMEFRAMES:
        c = store.newest(tf)
        if c is None:
            print(f"  {tf:>3}: none stored")
            continue
        print(f"  {tf:>3}: newest {c.describe()}")
        print(f"       finished {uk(c.end)}, {_age(now - c.end)} ago; parts {c.parts}/{c.expected_parts}")
    print(f"  recorded gaps: {len(store.recorded_gaps())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
