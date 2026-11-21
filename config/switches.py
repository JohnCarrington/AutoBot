"""The switches in .env (next to the IG secrets), checked at start-up:

  PAIRS_ON                    the pairs switched on, e.g. GBPUSD or GBPUSD,EURUSD
                              (each must have a [pairs.<PAIR>] section in settings.toml)
  NEW_TRADES_FROM             trading hours, UK time "HH:MM": new trades from ...
  NEW_TRADES_UNTIL            ... until (must be earlier than hours.close_all_trades_at
                              in settings.toml, or the same)
  STRATEGY_SLOW_GRIND         on or off
  STRATEGY_EMA_PULLBACK       on or off
  STRATEGY_BOLLINGER_BOUNCE   on or off (the hourly-pierce bounce of 15 November 2026)
  STRATEGY_BOLLINGER_BOUNCE_5M  on or off (the first build's 5-minute band and level bounce, kept and renamed;
                              owner, 19 November 2026)
  PULLBACK_ENTRY              on or off (ON if left out; owner, approved 19 November 2026): the breakout and the Asian
                              range breakout wait for a pullback to the 5-minute 8 EMA and a close back beyond it,
                              within [pullback_entry] wait_candles (6), and open at the next candle's open; a close
                              beyond the 21 EMA against them cancels (strategies/pullback.py)
  HOURLY_CONTEXT              on or off (ON if left out; owner, 21 November 2026): in an hourly DOWN context no buy opens
                              within 5 pips of the daily pivot or the hourly 50 EMA; in an UP context no sell
                              ([entry_filters]; strategies/entry_filters.py, rule 1)
  ENTRY_NEAR_EMA8             on or off (ON if left out; owner, 21 November 2026): a sell opens only if its entry is no
                              more than 5 pips below the 5-minute 8 EMA, a buy no more than 5 pips above it; the slow
                              grind, breakout and Asian range breakout exempt (strategies/entry_filters.py, rule 2)
  ONE_SIGNAL_ONE_TRADE        on or off (off if left out; owner, 18 November 2026): one trade per rejection
                              candle and direction; the session sweep and New York open reversal under one view at
                              a time (safety/rules.py, rules 9 and 11)
  PLANNER_OBSERVE             on or off (off if left out): the Structural Trade Planner (planner/), OBSERVE ONLY
  BOUNCE_ONLY_NEAR_TIMES      on or off (off if left out): while on, a Bollinger bounce opens only within
                              bounce.near_times_within_minutes (60) of bounce.near_times (10:00, 14:00,
                              16:00 UK) in settings.toml
  STRATEGY_RANGE_TRADE        on or off
  STRATEGY_BREAKOUT           on or off (never on while breakout.stop_loss_pips or
                              breakout.take_profit_pips is 0)
  STRATEGY_LEVEL_REVERSAL     on or off
  STRATEGY_ASIAN_RANGE_BREAKOUT    on or off (owner, 16 November 2026)
  STRATEGY_SESSION_SWEEP           on or off (owner, 16 November 2026)
  STRATEGY_NEW_YORK_OPEN_REVERSAL  on or off (owner, 16 November 2026)
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
    "STRATEGY_BOLLINGER_BOUNCE_5M": ("bollinger_bounce_5m", _on_off),
    "BOUNCE_ONLY_NEAR_TIMES": ("bounce_only_near_times", _on_off),
    "PLANNER_OBSERVE": ("planner_observe", _on_off),
    "ONE_SIGNAL_ONE_TRADE": ("one_signal_one_trade", _on_off),
    "PULLBACK_ENTRY": ("pullback_entry", _on_off),
    "HOURLY_CONTEXT": ("hourly_context", _on_off),
    "ENTRY_NEAR_EMA8": ("entry_near_ema8", _on_off),
    "STRATEGY_RANGE_TRADE": ("range_trade", _on_off),
    "STRATEGY_BREAKOUT": ("breakout", _on_off),
    "STRATEGY_LEVEL_REVERSAL": ("level_reversal", _on_off),
    "STRATEGY_ASIAN_RANGE_BREAKOUT": ("asian_range_breakout", _on_off),
    "STRATEGY_SESSION_SWEEP": ("session_sweep", _on_off),
    "STRATEGY_NEW_YORK_OPEN_REVERSAL": ("new_york_open_reversal", _on_off),
    "TRADING": ("trading", _on_off),
    "STOP_LOSS_PIPS": ("stop_loss_pips", _pips(1, 100)),
    "STOP_LOSS_PIPS_EMA_PULLBACK": ("stop_loss_pips_ema_pullback", _pips(1, 100)),
    "TAKE_PROFIT_PIPS": ("take_profit_pips", _pips(1, 1000)),
}

# Switches that may be left out of .env, and their value then (owner, 15 November 2026: both off by default).
OPTIONAL: dict[str, str] = {"BOUNCE_ONLY_NEAR_TIMES": "off", "PLANNER_OBSERVE": "off", "ONE_SIGNAL_ONE_TRADE": "off",
                            # the breakout's and Asian range breakout's pullback entry (owner, 19 November 2026): ON
                            "PULLBACK_ENTRY": "on",
                            # the entry filters (owner, 21 November 2026): both ON
                            "HOURLY_CONTEXT": "on", "ENTRY_NEAR_EMA8": "on"}


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
