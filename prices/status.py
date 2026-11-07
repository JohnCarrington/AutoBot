"""Show the newest candles in each switched-on pair's store and how old they
are. Contacts nobody.
Run:  .venv/bin/python -m prices.status [--pair EURUSD]
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

from config.settings_loader import load_or_exit
from prices.calendar import MarketHours
from prices.feed import _age
from prices.model import TIMEFRAMES, uk
from prices.store import CandleStore


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", help="one pair (switched on or not); default: every pair switched on")
    args = ap.parse_args(argv)
    s = load_or_exit()
    now = datetime.now(timezone.utc)
    hours = MarketHours(s.market_hours)
    print(f"Now: {uk(now)}. Market {'OPEN' if hours.is_open(now) else 'closed'}.")
    pairs = [s.for_pair(args.pair.upper())] if args.pair else s.pairs_on()
    for ps in pairs:
        store = CandleStore(ps.candles.folder, ps.candles.compress_after_days)
        print(f"{ps.market.pair} ({ps.market.epic}), store {ps.candles.folder}:")
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
