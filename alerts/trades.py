"""The "trade opened" and "trade closed" Telegram messages.

Built now, ready for the order sender (not built yet), which will call
Alerts.trade_opened(...) and Alerts.trade_closed(...) for every trade (design
section 9). Prices are shown as IG sends them (points) and as the real
exchange rate, using the pair's price scale.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from prices.model import plain, uk_short

DIRECTIONS = ("buy", "sell")


@dataclass(frozen=True)
class TradeOpened:
    pair: str
    direction: str                   # "buy" or "sell"
    size_gbp_per_pip: Decimal
    strategy: str
    market_state: str
    open_price: Decimal              # IG's points
    stop_loss: Decimal
    take_profit: Decimal
    opened_utc: datetime
    price_scale: int                 # IG's price = real price x this (the pair's setting)

    def __post_init__(self) -> None:
        if self.direction not in DIRECTIONS:
            raise ValueError(f"direction must be buy or sell, not {self.direction!r}")


@dataclass(frozen=True)
class TradeClosed:
    opened: TradeOpened
    close_price: Decimal
    closed_utc: datetime
    reason: str
    profit_gbp: Decimal              # profit (+) or loss (-) in pounds

    @property
    def result(self) -> str:
        return "WIN" if self.profit_gbp > 0 else "LOSS" if self.profit_gbp < 0 else "BREAK EVEN"


def _price(points: Decimal, scale: int) -> str:
    return f"{plain(points)} ({plain(Decimal(points) / scale)})"


def _money(x: Decimal) -> str:
    sign = "+" if x > 0 else "-" if x < 0 else ""
    return f"{sign}£{abs(Decimal(x)):,.2f}"


def opened_text(t: TradeOpened) -> str:
    return "\n".join([
        f"AutoBot TRADE OPENED: {t.pair} {t.direction.upper()}",
        f"Size: £{plain(t.size_gbp_per_pip)} per pip",
        f"Strategy: {t.strategy}",
        f"Market state: {t.market_state}",
        f"Open price: {_price(t.open_price, t.price_scale)} at {uk_short(t.opened_utc)}",
        f"Stop loss: {_price(t.stop_loss, t.price_scale)}",
        f"Take profit: {_price(t.take_profit, t.price_scale)}",
    ])


def closed_text(c: TradeClosed) -> str:
    t = c.opened
    return "\n".join([
        f"AutoBot TRADE CLOSED: {t.pair} {t.direction.upper()} - {c.result} {_money(c.profit_gbp)}",
        f"Size: £{plain(t.size_gbp_per_pip)} per pip",
        f"Strategy: {t.strategy}",
        f"Market state: {t.market_state}",
        f"Open price: {_price(t.open_price, t.price_scale)} at {uk_short(t.opened_utc)}",
        f"Stop loss: {_price(t.stop_loss, t.price_scale)}",
        f"Take profit: {_price(t.take_profit, t.price_scale)}",
        f"Close price: {_price(c.close_price, t.price_scale)} at {uk_short(c.closed_utc)}",
        f"Reason: {c.reason}",
        f"Profit or loss: {_money(c.profit_gbp)} ({c.result.lower()})",
    ])
