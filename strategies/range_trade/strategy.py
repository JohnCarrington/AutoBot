"""Range trade (design 3.4). The shared rejection part's range version follows
3.4 exactly: one candle pierces the upper Bollinger band, the next candle is a
red rejection candle, the trigger below its low during the candle after that,
cancelled if price goes above its high first, and spread spikes ignored. So
this strategy takes the rejection part's TRIGGERS for its range version.
("Half the trade closes when price reaches the other band" is for the trade
manager, not built yet.) Ideas only.
"""

from __future__ import annotations

from typing import Any

from strategies.bollinger_bounce.strategy import from_rejection
from strategies.common import RANGE_TRADE, Candidate


def candidates(watcher: Any, events: list) -> list[Candidate]:
    return from_rejection(watcher, events, "range", RANGE_TRADE)
