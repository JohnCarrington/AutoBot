"""A trade's reason in one line, the level reversal's level, and the kind of take profit, for the records and the
Telegram messages (design section 9)."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

from strategies.common import BOLLINGER_BOUNCE, BUY, EMA_PULLBACK, LEVEL_REVERSAL, RANGE_TRADE, SELL, SLOW_GRIND, take_profit_pips

_EVENT = re.compile(r"^\w{3} \d\d \w{3} (\d\d:\d\d) \w+\s+#\d+ (bounce|range) (buy|sell) "
                    r"(pierce|reversal|confirmation|trigger)[^:]*: ?(.*)$")
_SKIP = ("allowed at entry", "reached on the live price", "recorded, not used", "reversal watch window", "stop ",
         "a test order")


def one_line(idea: Any) -> str:
    """For example "bounce: pierced S2 13398.1 at 10:05, reversal 10:10, confirmed 10:15, broke it 10:20"."""
    events = [m.groups() for m in (_EVENT.match(s) for s in idea.steps) if m]
    if events and idea.strategy in (BOLLINGER_BOUNCE, RANGE_TRADE, LEVEL_REVERSAL):
        name = {BOLLINGER_BOUNCE: "bounce", RANGE_TRADE: "range trade", LEVEL_REVERSAL: "level reversal"}[idea.strategy]
        parts = []
        for hhmm, _version, _d, kind, note in events:
            if kind == "pierce":
                what = note.split("reached ", 1)[1].split(";")[0].split(" (")[0] if "reached " in note else "a level"
                parts = [f"pierced {what} at {hhmm}"]                       # a pierce again starts it again
            elif kind == "reversal":
                parts.append(f"reversal {hhmm}")
            elif kind == "confirmation":
                parts.append(f"confirmed {hhmm}")
            elif kind == "trigger":
                parts.append(f"broke it {hhmm}")
        return f"{name}: " + ", ".join(parts)
    steps = [s for s in idea.steps if not s.startswith(_SKIP) and not _EVENT.match(s)]
    text = "; ".join(s.split(": ", 1)[-1] if re.match(r"^\w{3} \d\d \w{3}", s) else s for s in steps[:3])
    return f"{idea.strategy}: {text}"[:240]


def level_note(idea: Any) -> str:
    """The level reversal: the level and how far past it price went."""
    if idea.strategy != LEVEL_REVERSAL or "level_name" not in idea.context:
        return ""
    past = Decimal(idea.context["past_level_pips"]).quantize(Decimal("0.1"))
    return (f"{idea.context['level_name']}; price went {past} pips past it" if past >= 0
            else f"{idea.context['level_name']}; price stopped {-past} pips short of it")


def take_profit_kind(settings: Any, idea: Any, tp: Any, trend_day: str | None) -> str:
    """normal, or the 100 for a big-news day or a trend day (the EMA pullback and the slow grind)."""
    normal = take_profit_pips(settings, idea.strategy)
    if Decimal(tp) == Decimal(normal) or idea.strategy not in (EMA_PULLBACK, SLOW_GRIND):
        return "normal"
    if trend_day is not None and idea.direction == {"down": SELL, "up": BUY}.get(trend_day):
        return f"{tp} for a trend day"
    return f"{tp} for a big-news day"
