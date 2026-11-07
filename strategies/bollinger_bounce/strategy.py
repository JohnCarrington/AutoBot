"""Bollinger band bounce (design 3.3). The shared rejection part (rejection/)
already follows every step of 3.3 exactly: the pierce of a level (within
rejection.near_level_within_pips) or of the band (a real pierce), the first
red reversal candle within 3 candles, the confirmation close within 3 candles,
the trigger below the confirmation candle's low, the cancel above the reversal
candle's high, the spread-spike rule, and the reversal/piercing size record.
So this strategy takes the rejection part's TRIGGERS for its bounce version.
Ideas only.
"""

from __future__ import annotations

from typing import Any

from strategies.common import BOLLINGER_BOUNCE, BUY, SELL, Candidate


def from_rejection(watcher: Any, events: list, version: str, strategy: str) -> list[Candidate]:
    """A candidate for each trigger of this version, with every step of its setup as the reason."""
    out = []
    for e in events:
        if e.version != version or e.kind != "trigger":
            continue
        steps = [x.describe() for x in watcher.events if x.setup == e.setup and x.kind not in ("ignored",)]
        st = watcher.setups[e.setup - 1]
        if st.size and st.size.get("body_ratio") is not None:
            steps.append(f"recorded, not used: reversal/piercing candle body {st.size['body_ratio']:.2f}x, "
                         f"high-low {st.size.get('range_ratio') or 0:.2f}x")
        if version == "bounce":
            steps.append(f"reversal watch window: {'inside' if st.in_watch_window else 'outside'}; the setup "
                         f"{'counts' if st.counts else 'does not count'} (a mark for the trade manager, not a filter)")
        out.append(Candidate(strategy, SELL if e.direction == "sell" else BUY, e.time, e.price, steps))
    return out


def candidates(watcher: Any, events: list) -> list[Candidate]:
    return from_rejection(watcher, events, "bounce", BOLLINGER_BOUNCE)
