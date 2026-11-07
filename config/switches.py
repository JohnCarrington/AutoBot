"""The switches in .env (next to the IG secrets), checked at start-up:

  PAIRS_ON                    the pairs switched on, e.g. GBPUSD or GBPUSD,EURUSD
                              (each must have a [pairs.<PAIR>] section in settings.toml)
  NEW_TRADES_FROM             trading hours, UK time "HH:MM": new trades from ...
  NEW_TRADES_UNTIL            ... until (must be earlier than hours.close_all_trades_at
                              in settings.toml, or the same)
  STRATEGY_SLOW_GRIND         on or off
  STRATEGY_EMA_PULLBACK       on or off
  STRATEGY_BOLLINGER_BOUNCE   on or off
  STRATEGY_RANGE_TRADE        on or off

Everything else is in config/settings.toml. Only these keys are read here:
the secrets in the same file are never looked at, printed or put in a message.
Each switch is documented in docs/SETTINGS.md (a test checks that).
"""

from __future__ import annotations

import re
from datetime import time
from pathlib import Path
from typing import Any, Callable

from config.env_file import parse

SWITCHES_SECTION = "switches"


def _pairs(v: str) -> tuple[str, ...]:
    names = [x.strip() for x in v.split(",")] if v.strip() else []
    if not names:
        raise ValueError("must name at least one pair, e.g. GBPUSD")
    for n in names:
        if not re.fullmatch(r"[A-Z]{6}", n):
            raise ValueError(f"{n!r} is not a pair name like GBPUSD")
    if len(set(names)) != len(names):
        raise ValueError("pairs must not repeat")
    return tuple(names)


def _time(v: str) -> time:
    m = re.fullmatch(r"(\d\d):(\d\d)", v.strip())
    if not m or int(m.group(1)) > 23 or int(m.group(2)) > 59:
        raise ValueError(f'must be a UK time written "HH:MM", got {v!r}')
    return time(int(m.group(1)), int(m.group(2)))


def _on_off(v: str) -> bool:
    if v.strip().lower() not in ("on", "off"):
        raise ValueError(f"must be on or off, got {v!r}")
    return v.strip().lower() == "on"


# .env key -> (name in settings.switches, check)
SWITCHES: dict[str, tuple[str, Callable[[str], Any]]] = {
    "PAIRS_ON": ("pairs_on", _pairs),
    "NEW_TRADES_FROM": ("new_trades_from", _time),
    "NEW_TRADES_UNTIL": ("new_trades_until", _time),
    "STRATEGY_SLOW_GRIND": ("slow_grind", _on_off),
    "STRATEGY_EMA_PULLBACK": ("ema_pullback", _on_off),
    "STRATEGY_BOLLINGER_BOUNCE": ("bollinger_bounce", _on_off),
    "STRATEGY_RANGE_TRADE": ("range_trade", _on_off),
}


def read_switches(path: Path) -> tuple[dict[str, Any], list[str]]:
    """The checked switches, and a list of problems (empty if all is well)."""
    try:
        values = parse(Path(path).read_text())
    except FileNotFoundError:
        return {}, [f"The file {path} does not exist (it holds the switches)."]
    except PermissionError:
        return {}, [f"The file {path} cannot be read (it holds the switches)."]
    out: dict[str, Any] = {}
    problems: list[str] = []
    for key, (name, check) in SWITCHES.items():
        if key not in values:
            problems.append(f"Missing switch {key} in {path}.")
            continue
        try:
            out[name] = check(values[key])
        except ValueError as e:
            problems.append(f"Invalid switch {key} in {path}: {e}.")
    return out, problems
