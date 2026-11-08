"""The safety rules (design sections 4, 6 and 7): whether a new order may go out. Decides only from
what it is given: the order (the trade idea, its size and stop), the bot's open trades, the account's
available funds (from IG's account details, read at start-up and whenever a trade opens or closes,
never before each trade), the time, and the pause switch. Never contacts IG, never places, changes or
closes anything; the order sender (not built yet) gathers the inputs and calls it.

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
  7. total risk: every open trade's risk (its stop distance x its size) plus the new trade's, at most
     safety.max_total_risk_gbp (£100,000; owner, 8 November 2026: set so it is never reached);
  8. available funds: the account's available funds at least safety.margin_per_trade_gbp (£5,000, the
     margin for one trade at £10 a pip); unknown funds refuse (never let a trade through when unsure).
IG's minimum stop distance is NOT checked before a trade (owner, 8 November 2026): the bot assumes each
strategy's own stop meets it; safety/refusals.py deals with IG refusing a trade.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from strategies.common import (BOLLINGER_BOUNCE, EMA_PULLBACK, SWITCH, counts_towards_most_at_once, may_open,
                               stop_loss_pips, stop_price)


@dataclass(frozen=True)
class OpenTrade:
    """One of the bot's open trades, as the trade manager knows it."""
    strategy: str
    direction: str                      # buy or sell
    opened_at: datetime
    stop_pips: Decimal                  # its stop's distance from its opening price, in pips
    size_gbp_per_pip: Decimal
    deal_id: str = ""

    @property
    def risk_gbp(self) -> Decimal:
        return Decimal(self.stop_pips) * Decimal(self.size_gbp_per_pip)


@dataclass(frozen=True)
class AccountFunds:
    """The account's available funds from IG's account details (ig.client.IGClient.account_balance),
    and when they were read (at start-up, and whenever a trade opens or closes)."""
    available: Decimal
    read_at: datetime

    @classmethod
    def from_ig(cls, balance: dict, read_at: datetime) -> "AccountFunds":
        return cls(Decimal(str(balance["available"])), read_at)


@dataclass(frozen=True)
class Order:
    """The order the bot would send for an idea."""
    idea: Any                           # strategies.common.Idea
    size_gbp_per_pip: Decimal
    stop_pips: Decimal                  # the stop's distance from the entry price, in pips

    @property
    def risk_gbp(self) -> Decimal:
        return Decimal(self.stop_pips) * Decimal(self.size_gbp_per_pip)


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


def _money(x: Decimal) -> str:
    return f"£{Decimal(x).quantize(Decimal('0.01')):,}"


def _risk(settings: Any, order: Order, open_trades: list[OpenTrade]) -> list[str]:
    most = Decimal(settings.safety.max_total_risk_gbp)
    total = sum((t.risk_gbp for t in open_trades), Decimal(0)) + order.risk_gbp
    if total > most:
        return [f"total risk {_money(total)} with this trade (its stop x its size, every open trade) is over "
                f"{_money(most)}"]
    return []


def _funds(settings: Any, funds: AccountFunds | None) -> list[str]:
    need = Decimal(settings.safety.margin_per_trade_gbp)
    if funds is None:
        return ["the account's available funds are not known (read from IG at start-up and whenever a trade "
                "opens or closes)"]
    if funds.available < need:
        return [f"available funds {_money(funds.available)} are less than the margin for one trade ({_money(need)})"]
    return []


def decide(settings: Any, order: Order, open_trades: list[OpenTrade], funds: AccountFunds | None,
           now: datetime, paused: bool, calendar: list | None = None) -> Decision:
    """Whether `order` may go out at `now`, with every reason it may not."""
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
    reasons += _risk(settings, order, open_trades)
    reasons += _funds(settings, funds)
    return Decision(not reasons, reasons)
