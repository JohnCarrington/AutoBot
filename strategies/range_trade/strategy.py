"""Range trade (design 3.4; owner, 13 November 2026: open right at the band).
A sell opens as soon as price reaches the upper Bollinger band; a buy as soon as price reaches the lower
band. No turn candle and no trigger. "Reaching the band" is as before: the price comes within
rejection.near_level_within_pips (3) of the band, or goes past it. The band is the one as it stood at
the last finished 5-minute candle (the only band known while a candle forms, as for the close at the
opposite band). The entry price: the band minus 3 pips for a sell (plus 3 for a buy), or the candle's
open if it opened already that close to the band or past it. A candle with a spread spike (over
rejection.max_spread_pips) cannot count, as before. Everything else about when it may trade (the
ranging state, its switch, hours, news, one at a time) is the shared checks in strategies/common.py
and the safety rules. It closes only at the opposite band (in full), its stop, 20:30 and before big
news: no close on a rejection at a level (owner, 13 November 2026). Ideas only.
"""

from __future__ import annotations

from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from typing import Any

from prices.model import Candle, plain, uk_short
from strategies.common import BUY, RANGE_TRADE, SELL, Candidate


def candidates(settings: Any, watcher: Any, c: Candle, band: Any) -> list[Candidate]:
    """A candidate for each band this candle reached (the band of the last finished candle), as soon as it
    reached it. `watcher` is the strategies' rejection watcher, used only for its spread-spike check."""
    if band is None or watcher.spike(c):
        return []
    side = settings.chart.price
    near = Decimal(settings.rejection.near_level_within_pips) * Decimal(settings.market.points_per_pip)
    o, h, l = (getattr(c, f"{side}_{k}") for k in ("open", "high", "low"))
    q = Decimal("0.1")
    out = []
    reach = band.upper - near
    if h >= reach:
        price = max(o, reach.quantize(q, ROUND_FLOOR))     # never above the candle's high
        out.append(Candidate(RANGE_TRADE, SELL, c.start, price, [
            f"{uk_short(c.start)}  high {plain(h)} reached the upper Bollinger band {plain(band.upper.quantize(q))} "
            f"(within {settings.rejection.near_level_within_pips} pips counts; the band at the last finished candle): "
            f"sell at {plain(price)}"], {"band_upper": band.upper, "band_lower": band.lower}))
    reach = band.lower + near
    if l <= reach:
        price = min(o, reach.quantize(q, ROUND_CEILING))   # never below the candle's low
        out.append(Candidate(RANGE_TRADE, BUY, c.start, price, [
            f"{uk_short(c.start)}  low {plain(l)} reached the lower Bollinger band {plain(band.lower.quantize(q))} "
            f"(within {settings.rejection.near_level_within_pips} pips counts; the band at the last finished candle): "
            f"buy at {plain(price)}"], {"band_upper": band.upper, "band_lower": band.lower}))
    return out
