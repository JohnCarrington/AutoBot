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

from strategies.common import BUY, RANGE_TRADE, SELL, Candidate, signal_context


def from_rejection(watcher: Any, events: list, version: str, strategy: str) -> list[Candidate]:
    """A candidate for each trigger of this version of the strategies' rejection watcher, with every step of its
    setup as the reason (the reversal/piercing size recorded, never a filter)."""
    out = []
    for e in events:
        if e.version != version or e.kind != "trigger":
            continue
        steps = [x.describe() for x in watcher.events if x.setup == e.setup and x.kind not in ("ignored",)]
        st = watcher.setups[e.setup - 1]
        if st.size and st.size.get("body_ratio") is not None:
            steps.append(f"recorded, not used: reversal/piercing candle body {st.size['body_ratio']:.2f}x, "
                         f"high-low {st.size.get('range_ratio') or 0:.2f}x")
        out.append(Candidate(strategy, SELL if e.direction == "sell" else BUY, e.time, e.price, steps,
                             signal_context(e.direction, st.reversal.start, st.furthest,
                                            watcher._c(st.reversal))))
    return out


def candidates(watcher: Any, events: list) -> list[Candidate]:
    return from_rejection(watcher, events, "range", RANGE_TRADE)
