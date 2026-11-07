"""What every strategy shares: a candidate (a strategy's entry price was
reached), the idea it becomes, and the checks that must all allow it.

A setup only STARTS, and only becomes an IDEA when its entry price is
reached, if at each of those moments all of these allow it (design sections
2.2 and 2.3; owner, 7 November 2026: checked when a setup starts and again at
entry; a setup that would start when the strategy is not allowed is not started):
  1. its switch in .env is on (STRATEGY_SLOW_GRIND, ...);
  2. the analyser's current state allows the strategy (section 2.2): ranging ->
     range trade; emerging trend and trend -> slow grind, EMA pullback,
     Bollinger bounce IN THE TREND'S DIRECTION ONLY; possible reversal ->
     Bollinger bounce; consolidation -> none;
  3. the direction rule allows that direction (section 2.3): a buy needs buy
     side (price above the daily pivot and the 5-minute 100 EMA), a sell needs
     sell side.
"The current state" is the analyser's state after the last finished 5-minute
candle. A setup that starts at a candle's close (a slow grind pause, a pierce)
is checked with the state after that candle and that candle's close; one that
starts while a candle forms (the EMA pullback's touch) with the state after the
candle before and the touch price (the 8 EMA). At entry: the state after the
candle before and the entry price. A candidate that
fails a check is kept as BLOCKED with the reason, never as an idea.

Ideas only: nothing here places, changes or closes a trade, or contacts IG.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from analyser.direction import BUY_SIDE, SELL_SIDE, decide
from analyser.states import DOWN, EMERGING, POSSIBLE_REVERSAL, RANGING, TREND, UP

SLOW_GRIND, EMA_PULLBACK, BOLLINGER_BOUNCE, RANGE_TRADE = (
    "slow grind", "EMA pullback", "Bollinger bounce", "range trade")
SWITCH = {SLOW_GRIND: "slow_grind", EMA_PULLBACK: "ema_pullback", BOLLINGER_BOUNCE: "bollinger_bounce",
          RANGE_TRADE: "range_trade"}
BUY, SELL = "buy", "sell"
# Section 2.2: which states allow which strategy, and whether only in the trend's direction.
ALLOWED_IN = {
    SLOW_GRIND: {EMERGING: "trend", TREND: "trend"},
    EMA_PULLBACK: {EMERGING: "trend", TREND: "trend"},
    BOLLINGER_BOUNCE: {EMERGING: "trend", TREND: "trend", POSSIBLE_REVERSAL: "any"},
    RANGE_TRADE: {RANGING: "any"},
}


@dataclass
class Candidate:
    """A strategy's entry price was reached (before the checks)."""
    strategy: str
    direction: str                      # buy or sell
    time: datetime                      # the moment the entry price was reached (replay: the candle's start)
    entry_price: Decimal
    steps: list[str]                    # the reason, step by step


@dataclass
class Idea:
    pair: str
    strategy: str
    direction: str
    time: datetime
    entry_price: Decimal
    state: str                          # the analyser's state at that moment
    state_direction: str
    trend_type: str | None
    direction_rule: str                 # buy side, sell side or no clear direction
    steps: list[str]
    allowed: bool = True
    blocked_by: str = ""

    def as_dict(self) -> dict:
        return {"pair": self.pair, "strategy": self.strategy, "direction": self.direction,
                "time_utc": self.time.strftime("%Y-%m-%dT%H:%M:%SZ"), "entry_price": str(self.entry_price),
                "state": self.state, "state_direction": self.state_direction, "trend_type": self.trend_type,
                "direction_rule": self.direction_rule, "steps": list(self.steps), "allowed": self.allowed,
                "blocked_by": self.blocked_by}

    def line(self) -> str:
        from prices.model import plain, uk_short
        kind = f", {self.trend_type}" if self.trend_type else ""
        head = (f"{uk_short(self.time)}  {self.strategy} {self.direction.upper()} at {plain(self.entry_price)}  "
                f"[{self.state} {self.state_direction}{kind}; {self.direction_rule}]")
        return head + ("" if self.allowed else f"  BLOCKED: {self.blocked_by}")


def allowed(settings: Any, strategy: str, direction: str, price: Decimal, state: Any, pivot: Decimal | None,
            ema100: Decimal | None) -> tuple[list[str], Any]:
    """Every reason the switch, the state (2.2) or the direction rule (2.3) does not allow
    this strategy in this direction at this price (empty: allowed), and the direction rule."""
    rule = decide(price, "the price", pivot, ema100, "5m 100 EMA", ema100 is not None)
    reasons = []
    if not getattr(settings.switches, SWITCH[strategy]):
        reasons.append(f"its switch STRATEGY_{SWITCH[strategy].upper()} is off")
    ok_in = ALLOWED_IN[strategy]
    if state.state not in ok_in:
        reasons.append(f"the analyser's state is {state.state}, which does not allow {strategy}")
    elif ok_in[state.state] == "trend":
        want = SELL if state.direction == DOWN else BUY if state.direction == UP else None
        if direction != want:
            reasons.append(f"the {state.state} is {state.direction}: {strategy} only in the trend's direction")
    need = BUY_SIDE if direction == BUY else SELL_SIDE
    if rule.side != need:
        reasons.append(f"the direction rule says {rule.side} ({rule.reason})")
    return reasons, rule


def start_note(strategy: str, direction: str, state: Any, rule: Any) -> str:
    return (f"setup start allowed: {strategy} {direction} in a {state.state} {state.direction}; direction rule "
            f"{rule.side} ({rule.reason})")


def check(settings: Any, pair: str, c: Candidate, state: Any, pivot: Decimal | None,
          ema100: Decimal | None) -> Idea:
    """At entry: turn a candidate into an idea, or a blocked one with every reason."""
    reasons, rule = allowed(settings, c.strategy, c.direction, c.entry_price, state, pivot, ema100)
    idea = Idea(pair, c.strategy, c.direction, c.time, c.entry_price, state.state, state.direction,
                state.trend_type, rule.side, list(c.steps))
    if reasons:
        idea.allowed, idea.blocked_by = False, "; ".join(reasons)
    else:
        idea.steps.append(f"allowed at entry: {c.strategy} in a {state.state} {state.direction}; direction rule "
                          f"{rule.side} ({rule.reason.replace('the price', 'the entry price')})")
    return idea
