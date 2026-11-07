"""Bollinger band bounce (design 3.3). Its ideas are the triggers of the
strategies' own rejection watcher (rejection/watch.py, design_only=True), which
has only the rules written in 3.3:
  1. a pierce of a level (a candle that comes within rejection.near_level_within_pips,
     3, of it counts the same) or of the Bollinger band (a real pierce);
  2. the reversal candle is the first red candle after the pierce, no size
     rule; none within 3 candles: expired;
  3. a later confirmation candle closes below the reversal candle's low within
     3 candles of it, or expired; a wick does not count;
  4. the sell opens as soon as price goes below the confirmation candle's low;
  5. price above the reversal candle's high at any point cancels it.
  The reversal/piercing size is recorded, never a filter; spread spikes
  (over rejection.max_spread_pips) cannot start or cancel a setup.
Choices section 3.3 does not make (the simplest, adding no rule; listed for the owner):
  * a candle reaches a level when its high-low range touches the level or comes
    within 3 pips of it (for a sell: high at least level - 3 pips and low at or
    below the level);
  * every pierce starts its own setup (several may run at once); a pierce while
    a setup waits for its reversal candle starts a new setup, the waiting one
    goes on counting;
  * with stored candles, a candle that goes both past the trigger price and past
    the cancel price counts as a trigger only if it opened past the trigger
    price, otherwise as a cancel (the order inside a candle is unknown).
The watch-window "counts" mark (design section 4) is recorded, never used.
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
