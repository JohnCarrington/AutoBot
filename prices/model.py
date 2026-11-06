"""Ticks and candles. Prices are kept exactly as IG sends them (Decimal), and
every candle keeps the buy price and the sell price separately: open, high,
low and close for each. There is no mid price anywhere.

In IG's terms the buy price is the offer (OFR) and the sell price is the bid
(BID). All times are UTC.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

UTC = timezone.utc
UK = ZoneInfo("Europe/London")

FIVE_MIN = timedelta(minutes=5)
TIMEFRAMES = ("5m", "1h", "4h", "1d", "1w")   # stored candle sizes
BUILT = ("1h", "4h", "1d", "1w")              # built from the stored 5-minute candles

PRICE_FIELDS = ("buy_open", "buy_high", "buy_low", "buy_close",
                "sell_open", "sell_high", "sell_low", "sell_close")


def utc_ms(ms: int | str) -> datetime:
    return datetime.fromtimestamp(int(ms) / 1000, tz=UTC)


def iso(t: datetime) -> str:
    """How a time is stored: '2026-11-06T19:05:00Z' (UTC)."""
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(text: str) -> datetime:
    if not text.endswith("Z"):
        raise ValueError(f"time {text!r} is not UTC")
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def uk(t: datetime) -> str:
    """How a time is shown to a person: UK time, with GMT or BST."""
    return t.astimezone(UK).strftime("%a %d %b %Y %H:%M:%S %Z")


def uk_short(t: datetime) -> str:
    return t.astimezone(UK).strftime("%a %d %b %H:%M %Z")


def price(text: object) -> Decimal:
    """A price from IG, exactly as sent. Raises ValueError if it is not a number."""
    if text is None or str(text).strip() == "":
        raise ValueError("missing price")
    try:
        d = Decimal(str(text).strip())
    except InvalidOperation:
        raise ValueError(f"not a price: {text!r}") from None
    if not d.is_finite() or d <= 0:
        raise ValueError(f"not a price: {text!r}")
    return d


def plain(d: Decimal) -> str:
    """A price written plainly (no exponent), e.g. '1.31245'."""
    return format(d, "f")


@dataclass(frozen=True)
class Tick:
    time: datetime
    buy: Decimal    # IG offer
    sell: Decimal   # IG bid


@dataclass(frozen=True)
class Candle:
    timeframe: str
    start: datetime
    end: datetime
    buy_open: Decimal
    buy_high: Decimal
    buy_low: Decimal
    buy_close: Decimal
    sell_open: Decimal
    sell_high: Decimal
    sell_low: Decimal
    sell_close: Decimal
    # For built candles: how many 5-minute candles went into it, and how many
    # the market hours say there should have been. A 5-minute candle is 1 of 1.
    parts: int = 1
    expected_parts: int = 1

    def prices(self) -> tuple[Decimal, ...]:
        return tuple(getattr(self, f) for f in PRICE_FIELDS)

    def same_values(self, other: "Candle") -> bool:
        return (self.timeframe, self.start, self.end, self.prices(), self.parts, self.expected_parts) == \
               (other.timeframe, other.start, other.end, other.prices(), other.parts, other.expected_parts)

    def describe(self) -> str:
        return (f"{self.timeframe} {uk_short(self.start)}: "
                f"buy O {plain(self.buy_open)} H {plain(self.buy_high)} L {plain(self.buy_low)} C {plain(self.buy_close)} | "
                f"sell O {plain(self.sell_open)} H {plain(self.sell_high)} L {plain(self.sell_low)} C {plain(self.sell_close)}")


def build_from(timeframe: str, start: datetime, end: datetime, parts: list[Candle], expected: int) -> Candle:
    """One bigger candle from smaller ones (in time order). Buy and sell are
    each built on their own: open of the first, highest high, lowest low,
    close of the last."""
    first, last = parts[0], parts[-1]
    return Candle(
        timeframe, start, end,
        buy_open=first.buy_open, buy_high=max(p.buy_high for p in parts),
        buy_low=min(p.buy_low for p in parts), buy_close=last.buy_close,
        sell_open=first.sell_open, sell_high=max(p.sell_high for p in parts),
        sell_low=min(p.sell_low for p in parts), sell_close=last.sell_close,
        parts=len(parts), expected_parts=expected,
    )
