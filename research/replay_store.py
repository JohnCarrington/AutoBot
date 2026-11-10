"""The research candle store the long replays read: one real store folder, in the bot's own format,
so the bot's own code (CandleStore, MemoStore) reads it unchanged.

Sources, by each candle's start (UK time):
  * before 1 January 2026:        AutoBot 161's IG sell candles for 2024 and 2025
                                  (data/research/candles_ig161/GBPUSD/), with the buy price made by adding IG's
                                  typical spread for that half hour of the week (bid_ask_from_sell, baked into
                                  data/research/candles_ig161_bidask/GBPUSD/ first; the hourly and daily candles
                                  are then built from those 5-minute candles exactly as the bot builds its own);
  * 1 January to the live cut:    161's 2026 mid candles turned into buy and sell
                                  (data/research/candles_ig161_2026/GBPUSD/, research.mid_to_bidask);
  * from the live cut:            the bot's own IG candles (the live store, read only; never written).
The live cut is 25 October 2026 00:00 UK (the bot's own candles start that evening). Only 5m, 1h and 1d are
used by the engine and so only they are merged.

Writes only under /opt/autobot/data/research/ (research.candles_convert refuses anything else).
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

from prices.model import UK, UTC
from prices.store import CandleStore, DamagedFile
from research.candles_convert import (RCandle, _boundaries, _check_out_folder, _write, candles_csv, convert,
                                      read_store)
from research.mid_to_bidask import read_spread_table, spread_from_table

SIZES = ("5m", "1h", "1d")
R = Path("/opt/autobot/data/research")
SELL_2024_2025 = R / "candles_ig161" / "GBPUSD"
BIDASK_2024_2025 = R / "candles_ig161_bidask" / "GBPUSD"
MID_2026 = R / "candles_ig161_2026" / "GBPUSD"
LIVE = Path("/opt/autobot/data/candles/GBPUSD")
TABLE = R / "ig_spread" / "GBPUSD_spread_by_half_hour.csv"
CUT_2026 = datetime(2026, 1, 1, tzinfo=UK).astimezone(UTC)
CUT_LIVE = datetime(2026, 10, 25, tzinfo=UK).astimezone(UTC)


def bid_ask_from_sell(fives: list[RCandle], spread_for) -> list[RCandle]:
    """buy = sell + IG's typical spread for the candle's half hour, for open, high, low and close."""
    out = []
    for c in fives:
        if c.sell is None:
            raise ValueError(f"no sell price at {c.start.isoformat()}")
        sp = spread_for(c.start)
        out.append(RCandle(c.start, c.end, tuple(p + sp for p in c.sell), c.sell, c.parts, c.expected_parts))
    return out


def bake_2024_2025(src: Path = SELL_2024_2025, out: Path = BIDASK_2024_2025, table: Path = TABLE) -> dict:
    fives = bid_ask_from_sell(read_store(src, "5m"), spread_from_table(read_spread_table(table)))
    return convert(fives, _boundaries(), out,
                   "research: 161's 2024-25 IG sell candles, buy = sell + IG's typical half-hour spread")


def source_for(start: datetime, cut_live: datetime = CUT_LIVE) -> str:
    if start < CUT_2026:
        return "2024-2025"
    if start < cut_live:
        return "2026"
    return "live"


def merge(out: Path, sources: dict[str, Path], cut_live: datetime = CUT_LIVE, until: datetime | None = None) -> dict:
    """Write the merged store into `out` (a folder named after the pair). Each source is read with the bot's
    own CandleStore (read only) and only its own candles (by source_for) are taken. `until`: leave out
    candles starting at or after it."""
    out = _check_out_folder(out)
    if out.name != "GBPUSD":
        raise ValueError("the merged store must be a folder named GBPUSD, as the bot's own stores are")
    counts: dict = defaultdict(int)
    for tf in SIZES:
        by_day: dict[date, list] = defaultdict(list)
        for name, folder in sources.items():
            st = CandleStore(folder, 10 ** 6)
            for day in st.days(tf):
                try:
                    candles = st.read_day(tf, day)
                except DamagedFile as e:
                    raise SystemExit(f"{name}: {e}")
                for c in candles:
                    if source_for(c.start, cut_live) == name and (until is None or c.start < until):
                        by_day[c.start.astimezone(UTC).date()].append(c)
                        counts[(tf, name)] += 1
        for day, cs in by_day.items():
            cs.sort(key=lambda c: c.start)
            for a, b in zip(cs, cs[1:]):
                if a.start == b.start:
                    raise ValueError(f"two {tf} candles at {a.start.isoformat()}")
            _write(out / tf / f"{day.isoformat()}.csv", candles_csv(
                RCandle(c.start, c.end, (c.buy_open, c.buy_high, c.buy_low, c.buy_close),
                        (c.sell_open, c.sell_high, c.sell_low, c.sell_close), c.parts, c.expected_parts) for c in cs))
    return dict(counts)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build the research replay store (no IG contact).")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--live-from", default="2026-10-25", help="UK date the bot's own candles are used from")
    ap.add_argument("--until", help="leave out candles starting at or after this UTC time (ISO)")
    ap.add_argument("--bake", action="store_true", help="first rebuild the 2024-25 buy and sell store")
    a = ap.parse_args(argv)
    if a.bake:
        r = bake_2024_2025()
        print(f"2024-25 buy and sell store: {r['counts']}")
    y, m, d = (int(x) for x in a.live_from.split("-"))
    cut = datetime(y, m, d, tzinfo=UK).astimezone(UTC)
    until = datetime.fromisoformat(a.until.replace("Z", "+00:00")) if a.until else None
    counts = merge(a.out, {"2024-2025": BIDASK_2024_2025, "2026": MID_2026, "live": LIVE}, cut, until)
    for k, v in sorted(counts.items()):
        print(f"  {k[0]} from {k[1]}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
