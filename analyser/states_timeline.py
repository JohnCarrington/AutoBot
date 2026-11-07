"""Show every market state change between two UTC times, from the stored
candles (the week is replayed from its open). Contacts nobody; writes nothing.

  .venv/bin/python -m analyser.states_timeline 2026-11-05T20:00:00Z 2026-11-06T17:00:00Z [--pair GBPUSD]
"""

from __future__ import annotations

import sys

from analyser.market_state import StateTracker
from config.pairs import choose_pair, take_pair_option
from config.settings_loader import load_or_exit
from prices.model import parse_iso, uk_short
from prices.store import CandleStore


def timeline(settings, store, start, end) -> list[str]:
    t = StateTracker(settings, store)
    t.replay(end)
    before = [ch for ch in t.changes if ch.time < start]
    out = []
    if before:
        b = before[-1]
        kind = f", {b.trend_type}" if b.trend_type else ""
        out.append(f"At {uk_short(start)}: {b.state} ({b.direction}{kind}) since {uk_short(b.time)}: {b.reason}")
    else:
        out.append(f"At {uk_short(start)}: consolidation (none) since the week's open")
    out += [ch.line() for ch in t.changes if start <= ch.time <= end]
    return out


def main(argv: list[str] | None = None) -> int:
    pair, args = take_pair_option(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        print(__doc__)
        return 2
    settings = choose_pair(load_or_exit(), pair)
    store = CandleStore(settings.candles.folder, settings.candles.compress_after_days)
    print("\n".join(timeline(settings, store, parse_iso(args[0]), parse_iso(args[1]))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
