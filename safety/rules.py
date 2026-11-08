"""The safety rules (design sections 4, 6 and 7): whether a new order may go out. Decides only from
what it is given: the order (the trade idea, its size and stop), the bot's open trades, the account
balance, the market's dealing rules from IG, the time, and the pause switch. Never contacts IG, never
places, changes or closes anything; the order sender (not built yet) fetches the inputs and calls it.

It gives EVERY reason it refuses (an empty list: the order may go out):
  1. the pause switch is on (it blocks every new trade);
  2. the idea was blocked by the strategy checks (strategies/common.py: switch, state, direction rule);
  3. the strategy's switch in .env is off (checked again here: a strategy cannot bypass it);
  4. the strategy's own hours, news rules and Friday rules (strategies.common.may_open);
  5. trades open at once: the strategy's own limit (limits.max_open_trades_per_strategy, 1; the
     Bollinger bounce limits.bollinger_bounce_extra_opposite_direction_trades more in the opposite
     direction; the EMA pullback no limit), and at most limits.max_open_trades (5) in total not counting
     the EMA pullback's (strategies.common.counts_towards_most_at_once);
  6. the size is trade.size_gbp_per_pip (£10 a pip);
  7. the stop is at least IG's minimum stop distance for the market (dealingRules
     minNormalStopOrLimitDistance), from dealing rules no older than safety.dealing_rules_max_age_minutes;
     missing dealing rules refuse (never let a trade through when unsure).
NOT BUILT YET: total risk across all open trades and the available funds (section 6). The owner is to
give their figures; `balance` is taken now for those checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from strategies.common import (BOLLINGER_BOUNCE, EMA_PULLBACK, SWITCH, counts_towards_most_at_once, may_open,
                               stop_loss_pips, stop_price)

POINTS, PERCENTAGE = "POINTS", "PERCENTAGE"


@dataclass(frozen=True)
class OpenTrade:
    """One of the bot's open trades, as the trade manager knows it."""
    strategy: str
    direction: str                      # buy or sell
    opened_at: datetime
    deal_id: str = ""


@dataclass(frozen=True)
class DealingRules:
    """IG's minimum stop distance for the market (GET /markets/{epic}: dealingRules
    .minNormalStopOrLimitDistance), and when it was fetched."""
    min_stop_value: Decimal
    min_stop_unit: str                  # POINTS or PERCENTAGE
    fetched_at: datetime

    @classmethod
    def from_ig(cls, market: dict, fetched_at: datetime) -> "DealingRules":
        rule = market["dealingRules"]["minNormalStopOrLimitDistance"]
        return cls(Decimal(str(rule["value"])), rule["unit"], fetched_at)

    def min_stop_pips(self, settings: Any, price: Decimal) -> Decimal:
        """The minimum in pips at this price (IG's points are the pair's price points)."""
        ppp = Decimal(settings.market.points_per_pip)
        if self.min_stop_unit == POINTS:
            return self.min_stop_value / ppp
        if self.min_stop_unit == PERCENTAGE:
            return price * self.min_stop_value / Decimal(100) / ppp
        raise ValueError(f"unknown unit for IG's minimum stop distance: {self.min_stop_unit!r}")


@dataclass(frozen=True)
class Order:
    """The order the bot would send for an idea."""
    idea: Any                           # strategies.common.Idea
    size_gbp_per_pip: Decimal
    stop_pips: Decimal                  # the stop's distance from the entry price, in pips


def order_for(settings: Any, idea: Any) -> Order:
    """The order for an idea with the bot's own size and stop: the strategy's stop in pips
    (strategies.common.stop_loss_pips), or, for the level reversal, the distance from the entry price
    to its stop price (both chart prices)."""
    sp = stop_price(settings, idea)
    if sp is not None:
        stop = abs(Decimal(idea.entry_price) - Decimal(sp)) / Decimal(settings.market.points_per_pip)
    else:
        stop = Decimal(stop_loss_pips(settings, idea.strategy))
    return Order(idea, Decimal(settings.trade.size_gbp_per_pip), stop)


@dataclass
class Decision:
    allowed: bool
    reasons: list[str] = field(default_factory=list)


def _limits(settings: Any, order: Order, open_trades: list[OpenTrade]) -> list[str]:
    lim, idea = settings.limits, order.idea
    out = []
    if idea.strategy != EMA_PULLBACK:
        mine = [t for t in open_trades if t.strategy == idea.strategy]
        if idea.strategy == BOLLINGER_BOUNCE:
            same = [t for t in mine if t.direction == idea.direction]
            most = lim.max_open_trades_per_strategy + lim.bollinger_bounce_extra_opposite_direction_trades
            if len(same) >= lim.max_open_trades_per_strategy:
                out.append(f"{idea.strategy} already has {len(same)} {idea.direction} trade(s) open "
                           f"(at most {lim.max_open_trades_per_strategy} each way)")
            elif len(mine) >= most:
                out.append(f"{idea.strategy} already has {len(mine)} trade(s) open (at most {most})")
        elif len(mine) >= lim.max_open_trades_per_strategy:
            out.append(f"{idea.strategy} already has {len(mine)} trade(s) open "
                       f"(at most {lim.max_open_trades_per_strategy})")
    if counts_towards_most_at_once(idea.strategy):
        counted = [t for t in open_trades if counts_towards_most_at_once(t.strategy)]
        if len(counted) >= lim.max_open_trades:
            out.append(f"{len(counted)} trades open that count towards the most at once ({lim.max_open_trades}; "
                       f"EMA pullback trades not counted)")
    return out


def _stop(settings: Any, order: Order, rules: DealingRules | None, now: datetime) -> list[str]:
    if rules is None:
        return ["IG's dealing rules for the market are not known: its minimum stop distance cannot be checked"]
    age = now - rules.fetched_at
    most = timedelta(minutes=settings.safety.dealing_rules_max_age_minutes)
    if age > most:
        return [f"IG's dealing rules are out of date (fetched {int(age.total_seconds() // 60)} minutes ago; "
                f"at most {settings.safety.dealing_rules_max_age_minutes})"]
    try:
        least = rules.min_stop_pips(settings, Decimal(order.idea.entry_price))
    except ValueError as e:
        return [str(e)]
    if order.stop_pips < least:
        return [f"the stop ({order.stop_pips.quantize(Decimal('0.1'))} pips) is closer than IG's minimum stop distance "
                f"({least.quantize(Decimal('0.1'))} pips)"]
    return []


def decide(settings: Any, order: Order, open_trades: list[OpenTrade], balance: Decimal | None,
           dealing_rules: DealingRules | None, now: datetime, paused: bool,
           calendar: list | None = None) -> Decision:
    """Whether `order` may go out at `now`, with every reason it may not. `balance` is for the total-risk
    and available-funds checks, not built yet (the owner is to give their figures)."""
    idea = order.idea
    reasons: list[str] = []
    if paused:
        reasons.append("the pause switch is on: no new trades")
    if not idea.allowed:
        reasons.append(f"the idea was blocked: {idea.blocked_by}")
    if not getattr(settings.switches, SWITCH[idea.strategy]):
        reasons.append(f"its switch STRATEGY_{SWITCH[idea.strategy].upper()} is off")
    reasons += may_open(settings, settings.market.pair, idea.strategy, now, calendar)
    reasons += _limits(settings, order, open_trades)
    want = Decimal(settings.trade.size_gbp_per_pip)
    if Decimal(order.size_gbp_per_pip) != want:
        reasons.append(f"the size is £{order.size_gbp_per_pip} a pip, not £{want}")
    reasons += _stop(settings, order, dealing_rules, now)
    return Decision(not reasons, reasons)

