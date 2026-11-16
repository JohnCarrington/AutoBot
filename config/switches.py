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
  STRATEGY_BREAKOUT           on or off (never on while breakout.stop_loss_pips or
                              breakout.take_profit_pips is 0)
  STRATEGY_LEVEL_REVERSAL     on or off
  STRATEGY_ASIAN_RANGE_BREAKOUT    on or off (owner, 16 November 2026)
  STRATEGY_SESSION_SWEEP           on or off (owner, 16 November 2026)
  STRATEGY_NEW_YORK_OPEN_REVERSAL  on or off (owner, 16 November 2026)
  HOURLY_READ                 on or off: while off the hourly read (analyser/hourly_read.py) does not
                              gate the trend strategies (strategies/common.py, check 4)
  BOUNCE_ONLY_WHEN_HOURLY_RANGING  on or off (off if left out): while on, a Bollinger bounce opens only
                              while the hourly read (analyser/hourly_read.py) says ranging
  BOUNCE_ONLY_NEAR_TIMES      on or off (off if left out): while on, a Bollinger bounce opens only within
                              bounce.near_times_within_minutes (60) of bounce.near_times (10:00, 14:00,
                              16:00 UK) in settings.toml
  TREND_STILL_GOING           on or off (off if left out): while on, the EMA pullback, slow grind and breakout
                              open only while the trend is still going ([trend_still_going] in settings.toml;
                              strategies/common.py, check 6)
  TRADING                     the master switch, on or off: while off everything runs and is
                              recorded, but no order is ever sent to IG
  STOP_LOSS_PIPS              the stop loss sent with every trade, in pips (whole, 1 to 100),
                              for every strategy except the EMA pullback
  STOP_LOSS_PIPS_EMA_PULLBACK the EMA pullback's stop loss, in pips (whole, 1 to 100)
  TAKE_PROFIT_PIPS            the take profit sent to IG with every trade, in pips
                              (whole, 1 to 1000); the bot may close earlier itself

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


def _pips(minimum: int, maximum: int) -> Callable[[str], int]:
    def check(v: str) -> int:
        if not re.fullmatch(r"\d+", v.strip()):
            raise ValueError(f"must be a whole number of pips, got {v!r}")
        n = int(v.strip())
        if not minimum <= n <= maximum:
            raise ValueError(f"must be between {minimum} and {maximum} pips, got {n}")
        return n
    return check


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
    "STRATEGY_BREAKOUT": ("breakout", _on_off),
    "STRATEGY_LEVEL_REVERSAL": ("level_reversal", _on_off),
    "STRATEGY_ASIAN_RANGE_BREAKOUT": ("asian_range_breakout", _on_off),
    "STRATEGY_SESSION_SWEEP": ("session_sweep", _on_off),
    "STRATEGY_NEW_YORK_OPEN_REVERSAL": ("new_york_open_reversal", _on_off),
    "HOURLY_READ": ("hourly_read", _on_off),
    "BOUNCE_ONLY_WHEN_HOURLY_RANGING": ("bounce_only_when_hourly_ranging", _on_off),
    "BOUNCE_ONLY_NEAR_TIMES": ("bounce_only_near_times", _on_off),
    "TREND_STILL_GOING": ("trend_still_going", _on_off),
    "TRADING": ("trading", _on_off),
    "STOP_LOSS_PIPS": ("stop_loss_pips", _pips(1, 100)),
    "STOP_LOSS_PIPS_EMA_PULLBACK": ("stop_loss_pips_ema_pullback", _pips(1, 100)),
    "TAKE_PROFIT_PIPS": ("take_profit_pips", _pips(1, 1000)),
}

# Switches that may be left out of .env, and their value then (owner, 15 November 2026: both off by default).
# TREND_STILL_GOING (owner, 16 November 2026): off if left out too.
OPTIONAL: dict[str, str] = {"BOUNCE_ONLY_WHEN_HOURLY_RANGING": "off", "BOUNCE_ONLY_NEAR_TIMES": "off",
                            "TREND_STILL_GOING": "off"}


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
        if key not in values and key in OPTIONAL:
            out[name] = check(OPTIONAL[key])
            continue
        if key not in values:
            problems.append(f"Missing switch {key} in {path}.")
            continue
        try:
            out[name] = check(values[key])
        except ValueError as e:
            problems.append(f"Invalid switch {key} in {path}: {e}.")
    return out, problems
