"""Show every rejection event between two UTC times, from the stored candles.
Contacts nobody.

  .venv/bin/python -m rejection 2026-11-05T21:00:00Z 2026-11-06T01:00:00Z [--pair GBPUSD]
(--pair may be left out when only one pair is switched on in .env.)
"""

from __future__ import annotations

import sys

from config.pairs import choose_pair, take_pair_option
from config.settings_loader import load_or_exit
from prices.model import parse_iso, plain, uk_short
from prices.store import CandleStore
from rejection.replay import replay


def show(w) -> list[str]:
    out = [e.describe() for e in w.events]
    out.append("")
    for st in w.setups:
        lined = "; ".join(f"G{g['group']}{' (lined up)' if g['lined_up'] else ''}: {', '.join(g['levels'])}"
                          for g in st.lined_up) or "no levels"
        size = (f"; reversal/pierce body {st.size['body_ratio']:.2f}x, high-low {st.size['range_ratio']:.2f}x"
                if st.size and st.size.get("body_ratio") is not None and st.size.get("range_ratio") is not None else "")
        out.append(f"#{st.id} {st.version} {st.direction}: {st.status}; pierce {uk_short(st.pierce.start)}; "
                   f"{'counts' if st.counts else 'does not count'}; levels: {lined}{size}")
    return out


def main(argv: list[str] | None = None) -> int:
    pair, args = take_pair_option(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        print(__doc__)
        return 2
    settings = choose_pair(load_or_exit(), pair)
    store = CandleStore(settings.candles.folder, settings.candles.compress_after_days)
    w = replay(settings, store, parse_iso(args[0]), parse_iso(args[1]))
    print("\n".join(show(w)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
