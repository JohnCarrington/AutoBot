"""Show every market state change between two UTC times, from the stored
candles (the week is replayed from its open). Contacts nobody; writes nothing.

  .venv/bin/python -m analyser.states_timeline 2026-11-05T20:00:00Z 2026-11-06T17:00:00Z [--pair GBPUSD]
  .venv/bin/python -m analyser.states_timeline --measure 2026-11-06T06:00:00Z 2026-11-06T06:45:00Z
      (every 5-minute candle in between: the consolidation checks, which failed and by how much)
"""

from __future__ import annotations

import sys
from datetime import timedelta

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


def measure(settings, store, start, end) -> list[str]:
    """For every 5-minute candle from start to end (both included): each consolidation check."""
    from decimal import Decimal
    m = settings.market_states
    side = settings.chart.price
    t = StateTracker(settings, store)
    t.replay(end + timedelta(minutes=5))
    q = lambda x: "-" if x is None else str(x.quantize(Decimal("0.01")))  # noqa: E731
    out = [f"Consolidation checks (all must pass): band width <= {m.narrow_band_max_pips} pips; middle band slope "
           f"under {m.flat_max_pips_per_candle} pips a candle (over {m.flat_slope_candles}); neither band reached "
           f"(within {m.near_band_pips} pip) for {m.consolidation_quiet_candles} candles; average body over those "
           f"candles <= {m.consolidation_max_body_pips} pips; green and red bodies within "
           f"{m.consolidation_colour_max_ratio}x of each other.",
           f"{'candle (UK)':<21}{'state':<24}{'width':>7}{'slope':>7}{'avg body':>9}{'green':>6}{'red':>5}"
           f"{'g/r body':>9}{'band last':>10}  failed checks (by how much)"]
    hist = t.history
    for k, (f, state, direction) in enumerate(hist):
        if not start <= f.candle.start <= end:
            continue
        win = hist[max(0, k - m.consolidation_quiet_candles + 1):k + 1]
        greens = sum(1 for x, _, _ in win if x.green)
        reds = sum(1 for x, _, _ in win if x.red)
        last = next((j for j, (x, _, _) in enumerate(reversed(hist[:k + 1])) if x.reached_upper or x.reached_lower),
                    None)
        failed = []
        if f.width is None or f.width > m.narrow_band_max_pips:
            failed.append(f"width {q(f.width)} > {m.narrow_band_max_pips} by {q(f.width - m.narrow_band_max_pips)}")
        if f.mid_slope is None or abs(f.mid_slope) >= m.flat_max_pips_per_candle:
            failed.append(f"slope |{q(f.mid_slope)}| >= {m.flat_max_pips_per_candle} by "
                          f"{q(abs(f.mid_slope) - m.flat_max_pips_per_candle)}")
        if not f.quiet:
            failed.append(f"a band was reached {last} candle(s) ago (needs {m.consolidation_quiet_candles} clear)"
                          if last is not None else "quiet window not full yet")
        if f.avg_body is None or f.avg_body > m.consolidation_max_body_pips:
            failed.append(f"avg body {q(f.avg_body)} > {m.consolidation_max_body_pips} by "
                          f"{q(f.avg_body - m.consolidation_max_body_pips)}")
        if f.colour_ratio is None or f.colour_ratio > m.consolidation_colour_max_ratio:
            failed.append(f"green/red bodies {q(f.colour_ratio) if f.colour_ratio is not None else 'one side only'}"
                          + (f" > {m.consolidation_colour_max_ratio} by {q(f.colour_ratio - m.consolidation_colour_max_ratio)}"
                             if f.colour_ratio is not None else ""))
        when = uk_short(f.candle.start)
        out.append(f"{when:<21}{(state + ' ' + direction)[:23]:<24}{q(f.width):>7}{q(f.mid_slope):>7}"
                   f"{q(f.avg_body):>9}{greens:>6}{reds:>5}{q(f.colour_ratio):>9}"
                   f"{('now' if last == 0 else str(last)) if last is not None else '-':>10}  "
                   + ("; ".join(failed) if failed else "ALL PASS"))
    return out


def main(argv: list[str] | None = None) -> int:
    pair, args = take_pair_option(sys.argv[1:] if argv is None else argv)
    do_measure = "--measure" in args
    args = [a for a in args if a != "--measure"]
    if len(args) != 2:
        print(__doc__)
        return 2
    settings = choose_pair(load_or_exit(), pair)
    store = CandleStore(settings.candles.folder, settings.candles.compress_after_days)
    fn = measure if do_measure else timeline
    print("\n".join(fn(settings, store, parse_iso(args[0]), parse_iso(args[1]))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
