"""Show every market state change between two UTC times, from the stored
candles (the week is replayed from its open). Contacts nobody; writes nothing.

  .venv/bin/python -m analyser.states_timeline 2026-11-05T20:00:00Z 2026-11-06T17:00:00Z [--pair GBPUSD]
  .venv/bin/python -m analyser.states_timeline --measure 2026-11-06T06:00:00Z 2026-11-06T06:45:00Z
      (every 5-minute candle in between: the consolidation checks, which failed and by how much)
  ... --push <from> <to>     the strong-push checks and the rejection events, per candle
  ... --events <from> <to>   every rejection event in full
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
    out = [f"Consolidation checks (all must pass): band width <= {m.narrow_band_max_pips} pips OR narrowing for "
           f"{m.narrowing_candles} candles in a row; middle band slope under {m.flat_max_pips_per_candle} pips a "
           f"candle (over {m.flat_slope_candles}); no close outside the bands for {m.consolidation_quiet_candles} "
           f"candles; average body over those candles <= {m.consolidation_max_body_pips} pips; green and red "
           f"bodies within {m.consolidation_colour_max_ratio}x of each other.",
           f"{'candle (UK)':<21}{'state':<24}{'width':>7}{'narrow':>7}{'slope':>7}{'avg body':>9}{'green':>6}{'red':>5}"
           f"{'g/r body':>9}{'out last':>9}  failed checks (by how much)"]
    hist = t.history
    for k, (f, state, direction, *_rest) in enumerate(hist):
        if not start <= f.candle.start <= end:
            continue
        win = hist[max(0, k - m.consolidation_quiet_candles + 1):k + 1]
        greens = sum(1 for x, *_ in win if x.green)
        reds = sum(1 for x, *_ in win if x.red)
        last = next((j for j, (x, *_) in enumerate(reversed(hist[:k + 1])) if x.closed_outside), None)
        failed = []
        if f.width is None or (f.width > m.narrow_band_max_pips and f.narrowing_for < m.narrowing_candles):
            failed.append(f"width {q(f.width)} > {m.narrow_band_max_pips} by {q(f.width - m.narrow_band_max_pips)} "
                          f"and narrowing for only {f.narrowing_for} of {m.narrowing_candles} candles")
        if f.mid_slope is None or abs(f.mid_slope) >= m.flat_max_pips_per_candle:
            failed.append(f"slope |{q(f.mid_slope)}| >= {m.flat_max_pips_per_candle} by "
                          f"{q(abs(f.mid_slope) - m.flat_max_pips_per_candle)}")
        if not f.no_close_outside:
            failed.append(f"a candle closed outside the bands {last} candle(s) ago (needs "
                          f"{m.consolidation_quiet_candles} without)" if last is not None else "window not full yet")
        if f.avg_body is None or f.avg_body > m.consolidation_max_body_pips:
            failed.append(f"avg body {q(f.avg_body)} > {m.consolidation_max_body_pips} by "
                          f"{q(f.avg_body - m.consolidation_max_body_pips)}")
        if f.colour_ratio is None or f.colour_ratio > m.consolidation_colour_max_ratio:
            failed.append(f"green/red bodies {q(f.colour_ratio) if f.colour_ratio is not None else 'one side only'}"
                          + (f" > {m.consolidation_colour_max_ratio} by {q(f.colour_ratio - m.consolidation_colour_max_ratio)}"
                             if f.colour_ratio is not None else ""))
        when = uk_short(f.candle.start)
        out.append(f"{when:<21}{(state + ' ' + direction)[:23]:<24}{q(f.width):>7}{f.narrowing_for:>7}{q(f.mid_slope):>7}"
                   f"{q(f.avg_body):>9}{greens:>6}{reds:>5}{q(f.colour_ratio):>9}"
                   f"{('now' if last == 0 else str(last)) if last is not None else '-':>10}  "
                   + ("; ".join(failed) if failed else "ALL PASS"))
    return out


def measure_push(settings, store, start, end) -> list[str]:
    """For every 5-minute candle from start to end: the strong-push checks for a DOWN move, the rejection
    events, the state, and the move since the trend started (for the 30-pip possible-reversal rule)."""
    from decimal import Decimal
    m = settings.market_states
    t = StateTracker(settings, store)
    t.replay(end + timedelta(minutes=5))
    q = lambda x: "-" if x is None else str(x.quantize(Decimal("0.01")))  # noqa: E731
    out = [f"Strong push down (all must pass, for {m.persistence_candles} candles in a row, in a trend): over "
           f"{m.push_candles} candles at least {m.push_same_colour_percent}% red; bands at least "
           f"{m.push_band_widening_percent}% of their width {m.band_widening_candles} candles before; 7 and 21 EMAs "
           f"at least {m.push_ema_fan_pips} pips apart; at least {m.push_riding_band_closes} closes on or beyond the "
           f"lower band (within {m.near_band_pips} pip).",
           f"{'candle (UK)':<21}{'state':<26}{'red %':>6}{'widen':>7}{'fan':>7}{'on band':>8}{'moved':>7}  "
           "push checks failed | rejection events on this candle"]
    for f, state, direction, events, moved, start_price in t.history:
        if not start <= f.candle.start <= end:
            continue
        failed = []
        red = f.red_share * 100
        if red < m.push_same_colour_percent:
            failed.append(f"red {q(red)}% < {m.push_same_colour_percent}")
        if f.widening is None or f.widening * 100 < m.push_band_widening_percent:
            failed.append(f"widening {q(f.widening * 100 if f.widening is not None else None)}% < "
                          f"{m.push_band_widening_percent}")
        if f.fan is None or f.fan < m.push_ema_fan_pips:
            failed.append(f"fan {q(f.fan)} < {m.push_ema_fan_pips}")
        if f.closes_on_lower < m.push_riding_band_closes:
            failed.append(f"on band {f.closes_on_lower} < {m.push_riding_band_closes}")
        evs = [f"#{e.setup} {e.version} {e.direction} {e.kind}" for e in events if e.kind != "ignored"]
        kind = f"{state} {direction}"
        out.append(f"{uk_short(f.candle.start):<21}{kind[:25]:<26}{q(red):>6}{q(f.widening):>7}{q(f.fan):>7}"
                   f"{f.closes_on_lower:>8}{q(moved):>7}  "
                   + ("; ".join(failed) if failed else "ALL PASS") + " | " + (", ".join(evs) if evs else "-"))
    return out


def events_detail(settings, store, start, end) -> list[str]:
    """Every rejection event from start to end, in full (which levels, which setup)."""
    t = StateTracker(settings, store)
    t.replay(end + timedelta(minutes=5))
    out = []
    for f, state, direction, events, moved, start_price in t.history:
        if start <= f.candle.start <= end:
            for e in events:
                out.append(e.describe())
    return out


def main(argv: list[str] | None = None) -> int:
    pair, args = take_pair_option(sys.argv[1:] if argv is None else argv)
    mode = next((a for a in args if a in ("--measure", "--push", "--events")), None)
    args = [a for a in args if a not in ("--measure", "--push", "--events")]
    if len(args) != 2:
        print(__doc__)
        return 2
    settings = choose_pair(load_or_exit(), pair)
    store = CandleStore(settings.candles.folder, settings.candles.compress_after_days)
    fn = {"--measure": measure, "--push": measure_push, "--events": events_detail}.get(mode, timeline)
    print("\n".join(fn(settings, store, parse_iso(args[0]), parse_iso(args[1]))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
