"""Show every idea the four strategies would have had between two UTC times,
from the stored candles (the week is replayed from its open). Contacts nobody;
places nothing; writes nothing.

  .venv/bin/python -m strategies 2026-11-05T06:00:00Z 2026-11-06T20:30:00Z [--pair GBPUSD] [--blocked]
(--blocked also lists the candidates a check stopped, with the reason.)
"""

from __future__ import annotations

import sys

from config.pairs import choose_pair, take_pair_option
from config.settings_loader import load_or_exit
from prices.model import parse_iso
from prices.store import CandleStore
from strategies.common import BOLLINGER_BOUNCE, EMA_PULLBACK, RANGE_TRADE, SLOW_GRIND
from strategies.replay import replay


def main(argv: list[str] | None = None) -> int:
    pair, args = take_pair_option(sys.argv[1:] if argv is None else argv)
    blocked = "--blocked" in args
    args = [a for a in args if a != "--blocked"]
    if len(args) != 2:
        print(__doc__)
        return 2
    settings = choose_pair(load_or_exit(), pair)
    store = CandleStore(settings.candles.folder, settings.candles.compress_after_days)
    ideas = replay(settings, store, parse_iso(args[0]), parse_iso(args[1]))
    for name in (SLOW_GRIND, EMA_PULLBACK, BOLLINGER_BOUNCE, RANGE_TRADE):
        mine = [i for i in ideas if i.strategy == name]
        ok = [i for i in mine if i.allowed]
        print(f"\n=== {name}: {len(ok)} idea(s), {len(mine) - len(ok)} blocked ===")
        for i in (mine if blocked else ok):
            print(i.line())
            for s in i.steps:
                print(f"      - {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
