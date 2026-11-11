"""The "trade opened" and "trade closed" Telegram messages (design section 9), sent for every real trade by the
trading engine (trading/engine.py), in AutoBot 161's format: a first line "[AutoBot] 🎯 TRADE OPENED", or
"[AutoBot] 🟢 TRADE CLOSED" (profit) / "[AutoBot] 🔴 TRADE CLOSED" (loss) / "[AutoBot] ⚪ TRADE CLOSED" (break even),
then one item per line, the label in bold followed by a colon ("Dir: BUY | Size: £10/pip"). The text is Telegram's
HTML (sent with parse_mode HTML; every value is escaped). Prices are shown as IG sends them (points) and as the real
exchange rate, using the pair's price scale.

Trade opened: the time; IG's deal reference; the epic; strategy; direction and size; market state; the entry price;
the stop and take profit in pips, as prices, and the £ at risk; whether the take profit is the normal one or the 100
for a big-news day or a trend day; the reason in one line; for the level reversal, the level and how far past it price
went. Trade closed: all of that (the entry shown as "Entry: ... → Exit: ...", with the close time after it), plus the
reason it closed, pips and £, how long it was open, the best profit it reached, for a half close at the opposite band (the Bollinger bounce) the half close and
the rest on separate lines, and today's running total of trades and pips.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from html import escape

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
    epic: str = ""                   # IG's market (the pair's epic); the pair is shown when it is not given

    def __post_init__(self) -> None:
        if self.direction not in DIRECTIONS:
            raise ValueError(f"direction must be buy or sell, not {self.direction!r}")

    @property
    def risk_gbp(self) -> Decimal | None:
        return None if self.stop_pips is None else Decimal(self.stop_pips) * Decimal(self.size_gbp_per_pip)


@dataclass(frozen=True)
class PartClose:
    """A half close at the opposite band (the Bollinger bounce), or its rest."""
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
    half: PartClose | None = None    # a half close at the opposite band (the Bollinger bounce)
    rest: PartClose | None = None    # and its rest
    today_trades: int | None = None
    today_pips: Decimal | None = None

    @property
    def result(self) -> str:
        return "WIN" if self.profit_gbp > 0 else "LOSS" if self.profit_gbp < 0 else "BREAK EVEN"


def item(label: str, value: object) -> str:
    """One line of a Telegram message: the label in bold, a colon, then the value (Telegram's HTML; text escaped)."""
    return f"<b>{escape(label)}:</b> {escape(str(value), quote=False)}"


def items(*pairs: tuple[str, object]) -> str:
    """Several items on one line, joined by " | ", e.g. "Dir: BUY | Size: £10/pip"."""
    return " | ".join(item(k, v) for k, v in pairs)


def _price(points: Decimal, scale: int) -> str:
    return f"{plain(points)} ({plain(Decimal(points) / scale)})"


def money(x: Decimal) -> str:
    sign = "+" if x > 0 else "-" if x < 0 else ""
    return f"{sign}£{abs(Decimal(x)):,.2f}"


def _short(text: str) -> str:
    return text[:-2] if text.endswith(".0") else text


def pips(x: Decimal) -> str:
    """Signed pips to one decimal place, without a trailing .0: +3 pips, -6 pips, +11.3 pips, 0 pips."""
    x = Decimal(x).quantize(Decimal("0.1"))
    return ("0" if x == 0 else _short(f"{x:+.1f}")) + " pips"


def _unsigned_pips(x: Decimal) -> str:
    return _short(f"{Decimal(x):.1f}") + " pips"


def _duration(a: datetime, b: datetime) -> str:
    m = int((b - a).total_seconds() // 60)
    return f"{m // 1440} d {m % 1440 // 60} h {m % 60} min" if m >= 1440 else f"{m // 60} h {m % 60} min"


def _head(t: TradeOpened, time_label: str) -> list[str]:
    lines = [item(time_label, uk_short(t.opened_utc))]
    if t.reference:
        lines.append(item("Deal ref", t.reference))
    lines += [item("Epic", t.epic or t.pair),
              item("Strategy", t.strategy),
              items(("Dir", t.direction.upper()), ("Size", f"£{plain(t.size_gbp_per_pip)}/pip")),
              item("Market state", t.market_state)]
    return lines


def _stops(t: TradeOpened) -> list[str]:
    if t.stop_pips is None:
        sl = item("SL", _price(t.stop_loss, t.price_scale))
    else:
        sl = items(("SL", f"{_unsigned_pips(t.stop_pips)} @ {_price(t.stop_loss, t.price_scale)}"),
                   ("Risk", f"£{abs(t.risk_gbp):,.2f}"))
    tp = (_price(t.take_profit, t.price_scale) if t.take_profit_pips is None
          else f"{_unsigned_pips(t.take_profit_pips)} @ {_price(t.take_profit, t.price_scale)}")
    return [sl, items(("TP", tp), ("TP kind", t.take_profit_kind))]


def _why(t: TradeOpened, label: str) -> list[str]:
    lines = [item(label, t.reason)] if t.reason else []
    if t.level_note:
        lines.append(item("Level", t.level_note))
    return lines


def opened_text(t: TradeOpened) -> str:
    """Telegram's HTML: send with parse_mode HTML (Alerts.trade_opened does)."""
    return "\n".join(["[AutoBot] 🎯 TRADE OPENED"] + _head(t, "Time")
                     + [item("Entry", _price(t.open_price, t.price_scale))] + _stops(t) + _why(t, "Reason"))


def _part(label: str, p: PartClose, scale: int) -> str:
    return items((label, f"{_price(p.price, scale)} at {uk_short(p.closed_utc)}"), ("PnL", f"{pips(p.pips)} / {money(p.gbp)}")) \
        + (f" ({escape(p.reason, quote=False)})" if p.reason else "")


def closed_text(c: TradeClosed) -> str:
    """Telegram's HTML: send with parse_mode HTML (Alerts.trade_closed does). 🟢 a profit, 🔴 a loss, ⚪ break even."""
    t = c.opened
    icon = "🟢" if c.profit_gbp > 0 else "🔴" if c.profit_gbp < 0 else "⚪"
    lines = [f"[AutoBot] {icon} TRADE CLOSED"] + _head(t, "Opened")
    lines.append(f"{item('Entry', _price(t.open_price, t.price_scale))} → "
                 f"{item('Exit', _price(c.close_price, t.price_scale))}")
    lines.append(item("Closed", uk_short(c.closed_utc)))
    lines += _stops(t) + _why(t, "Reason opened")
    lines.append(item("Reason" if not t.reason else "Reason closed", c.reason))
    lines.append(item("PnL", money(c.profit_gbp) if c.pips is None else f"{pips(c.pips)} | {money(c.profit_gbp)}"))
    lines.append(item("Duration", _duration(t.opened_utc, c.closed_utc)))
    if c.best_pips is not None:
        lines.append(item("Best", pips(c.best_pips)))
    if c.half is not None:
        lines.append(_part("Half close", c.half, t.price_scale))
    if c.rest is not None:
        lines.append(_part("Rest", c.rest, t.price_scale))
    if c.today_trades is not None:
        lines.append(item("Today", f"{c.today_trades} trade{'s' if c.today_trades != 1 else ''} | {pips(c.today_pips or 0)}"))
    return "\n".join(lines)
