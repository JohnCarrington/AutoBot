"""The "trade opened" and "trade closed" Telegram messages (design section 9), sent for every real trade by the
trading engine (trading/engine.py). Prices are shown as IG sends them (points) and as the real exchange rate, using
the pair's price scale.

Trade opened: the time; IG's deal reference; pair, direction, size, strategy and market state; the open price; the
stop and take profit in pips, as prices, and the £ at risk; whether the take profit is the normal one or the 100 for
a big-news day or a trend day; the reason in one line; for the level reversal, the level and how far past it price
went. Trade closed: all of that, plus the close price and time, the reason it closed, pips and £, win or loss, how
long it was open, the best profit it reached, for the range trade the half close and the rest, and today's running
total of trades and pips.
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
    stop_loss: Decimal               # as a price
    take_profit: Decimal             # as a price
    opened_utc: datetime
    price_scale: int                 # IG's price = real price x this (the pair's setting)
    reference: str = ""              # IG's deal reference (the bot's own)
    stop_pips: Decimal | None = None
    take_profit_pips: Decimal | None = None
    take_profit_kind: str = "normal"  # normal, or 100 for a big-news day / a trend day
    reason: str = ""                 # in one line
    level_note: str = ""             # the level reversal: the level and how far past it price went

    def __post_init__(self) -> None:
        if self.direction not in DIRECTIONS:
            raise ValueError(f"direction must be buy or sell, not {self.direction!r}")

    @property
    def risk_gbp(self) -> Decimal | None:
        return None if self.stop_pips is None else Decimal(self.stop_pips) * Decimal(self.size_gbp_per_pip)


@dataclass(frozen=True)
class PartClose:
    """The range trade's half close, or its rest."""
    closed_utc: datetime
    price: Decimal
    pips: Decimal
    gbp: Decimal
    reason: str = ""


@dataclass(frozen=True)
class TradeClosed:
    opened: TradeOpened
    close_price: Decimal
    closed_utc: datetime
    reason: str
    profit_gbp: Decimal              # profit (+) or loss (-) in pounds
    pips: Decimal | None = None
    best_pips: Decimal | None = None
    half: PartClose | None = None    # the range trade's half close
    rest: PartClose | None = None    # and its rest
    today_trades: int | None = None
    today_pips: Decimal | None = None

    @property
    def result(self) -> str:
        return "WIN" if self.profit_gbp > 0 else "LOSS" if self.profit_gbp < 0 else "BREAK EVEN"


def _price(points: Decimal, scale: int) -> str:
    return f"{plain(points)} ({plain(Decimal(points) / scale)})"


def _money(x: Decimal) -> str:
    sign = "+" if x > 0 else "-" if x < 0 else ""
    return f"{sign}£{abs(Decimal(x)):,.2f}"


def _pips(x: Decimal) -> str:
    return f"{Decimal(x):+.1f} pips"


def _duration(a: datetime, b: datetime) -> str:
    m = int((b - a).total_seconds() // 60)
    return f"{m // 1440} d {m % 1440 // 60} h {m % 60} min" if m >= 1440 else f"{m // 60} h {m % 60} min"


def _opened_lines(t: TradeOpened) -> list[str]:
    stop = f"Stop loss: {_price(t.stop_loss, t.price_scale)}"
    if t.stop_pips is not None:
        stop = f"Stop loss: {Decimal(t.stop_pips):.1f} pips, {_price(t.stop_loss, t.price_scale)}; {_money(t.risk_gbp)} at risk"
        stop = stop.replace("+£", "£")
    tp = f"Take profit: {_price(t.take_profit, t.price_scale)}"
    if t.take_profit_pips is not None:
        tp = f"Take profit: {Decimal(t.take_profit_pips):.0f} pips, {_price(t.take_profit, t.price_scale)} ({t.take_profit_kind})"
    lines = [f"Time: {uk_short(t.opened_utc)}"] + ([f"Deal reference: {t.reference}"] if t.reference else []) + [
        f"Size: £{plain(t.size_gbp_per_pip)} per pip",
        f"Strategy: {t.strategy}",
        f"Market state: {t.market_state}",
        f"Open price: {_price(t.open_price, t.price_scale)} at {uk_short(t.opened_utc)}",
        stop,
        tp]
    if t.reason:
        lines.append(f"Reason: {t.reason}")
    if t.level_note:
        lines.append(f"Level: {t.level_note}")
    return lines


def opened_text(t: TradeOpened) -> str:
    return "\n".join([f"AutoBot TRADE OPENED: {t.pair} {t.direction.upper()}"] + _opened_lines(t))


def closed_text(c: TradeClosed) -> str:
    t = c.opened
    lines = [f"AutoBot TRADE CLOSED: {t.pair} {t.direction.upper()} - {c.result} {_money(c.profit_gbp)}"]
    lines += _opened_lines(t)
    lines += [f"Close price: {_price(c.close_price, t.price_scale)} at {uk_short(c.closed_utc)}",
              f"Reason: {c.reason}" if not t.reason else f"Reason closed: {c.reason}"]
    if c.half is not None:
        lines.append(f"Half closed: {_price(c.half.price, t.price_scale)} at {uk_short(c.half.closed_utc)}, "
                     f"{_pips(c.half.pips)}, {_money(c.half.gbp)}" + (f" ({c.half.reason})" if c.half.reason else ""))
    if c.rest is not None:
        lines.append(f"Rest closed: {_price(c.rest.price, t.price_scale)} at {uk_short(c.rest.closed_utc)}, "
                     f"{_pips(c.rest.pips)}, {_money(c.rest.gbp)}" + (f" ({c.rest.reason})" if c.rest.reason else ""))
    result = f"Profit or loss: {_money(c.profit_gbp)} ({c.result.lower()})"
    if c.pips is not None:
        result = f"Profit or loss: {_pips(c.pips)}, {_money(c.profit_gbp)} ({c.result.lower()})"
    lines.append(result)
    lines.append(f"Open for: {_duration(t.opened_utc, c.closed_utc)}")
    if c.best_pips is not None:
        lines.append(f"Best profit before closing: {_pips(c.best_pips)}")
    if c.today_trades is not None:
        lines.append(f"Today so far: {c.today_trades} trade(s), {_pips(c.today_pips or 0)}")
    return "\n".join(lines)
