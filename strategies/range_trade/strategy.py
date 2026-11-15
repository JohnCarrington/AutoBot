"""Range trade (design 3.4). Its ideas are the triggers of the strategies' own
rejection watcher (rejection/watch.py, design_only=True), which has only the
rules written in 3.4: one candle pierces the upper Bollinger band; the next
candle is a red rejection candle; the sell opens as soon as price, during the
candle after that, goes below the rejection candle's low; cancelled if price
goes above its high first; spread spikes ignored as for the bounce. A buy is
the mirror image at the lower band. "Half the trade closes when price reaches
the other band" is for the trade manager (not built yet).
Choices section 3.4 does not make (listed for the owner): every pierce starts
its own setup; a candle going both past the trigger and the cancel price counts
as a trigger only if it opened past the trigger price. Ideas only.
"""

from __future__ import annotations

from typing import Any

from strategies.bollinger_bounce.strategy import from_rejection
from strategies.common import RANGE_TRADE, Candidate


def candidates(watcher: Any, events: list) -> list[Candidate]:
    return from_rejection(watcher, events, "range", RANGE_TRADE)
