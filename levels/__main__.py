"""Show the levels, and write the current list. Contacts nobody (reads the candle store only).

  .venv/bin/python -m levels                       levels now: writes <levels.folder>/current.json and prints it
  .venv/bin/python -m levels --at 2026-11-06T00:00:00Z
                                                   levels as they stood at that UTC time: prints only, never writes
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from config.settings_loader import load_or_exit
from levels.current import LevelList, build, write_current
from levels.rules import PIVOT, R1, R2, R3, S1, S2, S3, close, high, low
from prices.model import parse_iso, plain, uk, uk_short
from prices.store import CandleStore


def show(ll: LevelList) -> list[str]:
    out = [f"Levels as of {uk(ll.as_of)} ({ll.side.upper()} prices, in points; 13450 means 1.3450)",
           f"Day: daily candle starting {uk_short(ll.day_start)}"]
    if ll.previous_day:
        p = ll.previous_day
        out.append(f"Pivots from the daily candle {uk_short(p.start)}: {ll.side} H {plain(high(p, ll.side))} "
                   f"L {plain(low(p, ll.side))} C {plain(close(p, ll.side))}")
        piv = {lv.type: lv for lv in ll.levels if lv.type in (PIVOT, R1, R2, R3, S1, S2, S3)}
        out.append("  " + "  ".join(f"{t} {plain(piv[t].price)}" for t in (R3, R2, R1, PIVOT, S1, S2, S3)))
    if ll.reference_price is not None:
        out.append(f"Latest {ll.side} close (for round numbers): {plain(ll.reference_price)}")
    for w in ll.warnings:
        out.append("WARNING: " + w)
    out.append("")
    out.append(f"{len(ll.levels)} levels in {len(ll.groups)} groups "
               f"({sum(1 for g in ll.groups if g['lined_up'])} groups where levels line up). "
               "* = the group holds a level that matters most (S2, R2, pivot, round number, turning level).")
    for g in reversed(ll.groups):           # highest price first, like a chart
        rng = plain(g["low"]) if g["low"] == g["high"] else f"{plain(g['low'])}-{plain(g['high'])}"
        out.append(f"  G{g['group']:<3}{'*' if g['important'] else ' '} {rng}")
        for m in reversed(g["members"]):
            out.append(f"         {plain(m.price):>9}  {m.type:<22} {m.source}")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--at", help="a UTC time like 2026-11-06T00:00:00Z: show levels as they stood then (no file written)")
    args = ap.parse_args(argv)
    settings = load_or_exit()
    store = CandleStore(settings.candles.folder, settings.candles.compress_after_days)
    now = datetime.now(timezone.utc)
    at = parse_iso(args.at) if args.at else now
    ll = build(settings, store, at)
    print("\n".join(show(ll)))
    if not args.at:
        path = write_current(settings.levels.folder, ll, now)
        print(f"\nWritten: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
