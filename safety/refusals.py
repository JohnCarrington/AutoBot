"""When IG refuses a trade (design section 7; owner, 8 November 2026). For the order sender (not built
yet), which calls on_refusal() with IG's reason from the deal confirmation.

  * refused because of its stop (IG's reason in safety.ig_stop_refusal_reasons): fetch IG's current
    minimum stop distance ONCE (the `read_min_stop` it is given: ig.markets.min_stop), record it in
    safety.folder/ig_min_stop_refusals.jsonl, and send a Telegram problem alert with the strategy, its
    stop and IG's minimum. The stop is never widened;
  * refused for lack of funds (IG's reason in safety.ig_funds_refusal_reasons): a Telegram problem alert;
  * any other reason: nothing here (the order sender reports it).
IG's dealing rules are never fetched before a trade.
"""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

from prices.model import uk_short

STOP, FUNDS, OTHER = "stop", "funds", "other"
RECORD = "ig_min_stop_refusals.jsonl"


def min_stop_pips(settings: Any, value: float, unit: str, price: Decimal) -> Decimal:
    """IG's minimum in pips: its points are the pair's price points; a percentage is of the price."""
    ppp = Decimal(settings.market.points_per_pip)
    v = Decimal(str(value))
    if unit == "POINTS":
        return v / ppp
    if unit == "PERCENTAGE":
        return Decimal(price) * v / Decimal(100) / ppp
    raise ValueError(f"unknown unit for IG's minimum stop distance: {unit!r}")


def kind_of(settings: Any, reason: str | None) -> str:
    if reason in settings.safety.ig_stop_refusal_reasons:
        return STOP
    if reason in settings.safety.ig_funds_refusal_reasons:
        return FUNDS
    return OTHER


def on_refusal(settings: Any, reason: str | None, strategy: str, stop_pips: Decimal, price: Decimal,
               read_min_stop: Callable[[], Any], alerts: Any, now: datetime,
               available_funds: Decimal | None = None) -> str:
    """Deal with IG refusing a trade; returns which kind of refusal it was (stop, funds or other)."""
    kind = kind_of(settings, reason)
    stop = Decimal(stop_pips).quantize(Decimal("0.1"))
    if kind == STOP:
        try:
            m = read_min_stop()                                     # once
            pips = min_stop_pips(settings, m.value, m.unit, price).quantize(Decimal("0.1"))
            got = f"{pips} pips" + ("" if m.unit == "POINTS" else f" ({m.value}% of the price)")
            row = {"time_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "strategy": strategy, "stop_pips": str(stop),
                   "ig_reason": reason, "ig_min_value": m.value, "ig_min_unit": m.unit, "ig_min_pips": str(pips)}
        except Exception as e:                                      # noqa: BLE001  (still alert, without the figure)
            got = f"not known (reading it from IG failed: {e})"
            row = {"time_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "strategy": strategy, "stop_pips": str(stop),
                   "ig_reason": reason, "ig_min_error": str(e)}
        folder = Path(settings.safety.folder)
        folder.mkdir(parents=True, exist_ok=True)
        with (folder / RECORD).open("a") as f:
            f.write(json.dumps(row) + "\n")
        alerts.problem(f"ig-stop-refused-{strategy}",
                       f"IG refused a {strategy} trade at {uk_short(now)} because of its stop ({reason}). "
                       f"The {strategy} stop is {stop} pips; IG's minimum stop distance is now {got}. "
                       "The stop was not changed.")
    elif kind == FUNDS:
        known = (f"; available funds last read £{Decimal(available_funds).quantize(Decimal('0.01')):,}"
                 if available_funds is not None else "")
        alerts.problem("ig-funds-refused",
                       f"IG refused a {strategy} trade at {uk_short(now)} for lack of funds ({reason}){known}.")
    return kind
