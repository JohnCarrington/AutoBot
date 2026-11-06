"""Loads and checks config/settings.toml.

Every setting must be present, of the right kind and within sensible limits.
Anything missing, unknown or invalid raises SettingsError with a clear message,
and the bot must not start.

Check the settings from the command line with:  .venv/bin/python -m config
"""

from __future__ import annotations

import os
import re
import tomllib
from datetime import time
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_PATH = Path(__file__).resolve().parent / "settings.toml"
PATH_ENV_VAR = "AUTOBOT_SETTINGS"


class SettingsError(Exception):
    """A setting is missing, unknown or invalid. The bot must not start."""


# ---- value checks -----------------------------------------------------------
# Each check takes the raw value and returns the checked (possibly converted)
# value, or raises ValueError with a plain-English reason.

def _whole_number(minimum: int, maximum: int) -> Callable[[Any], int]:
    def check(v: Any) -> int:
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError(f"must be a whole number, got {v!r}")
        if not minimum <= v <= maximum:
            raise ValueError(f"must be between {minimum} and {maximum}, got {v}")
        return v
    return check


def _whole_numbers(minimum: int, maximum: int) -> Callable[[Any], tuple[int, ...]]:
    one = _whole_number(minimum, maximum)

    def check(v: Any) -> tuple[int, ...]:
        if not isinstance(v, list) or not v:
            raise ValueError(f"must be a non-empty list of whole numbers, got {v!r}")
        return tuple(one(x) for x in v)
    return check


def _exactly(expected: str) -> Callable[[Any], str]:
    def check(v: Any) -> str:
        if v != expected:
            raise ValueError(f"must be {expected!r}, got {v!r}")
        return v
    return check


def _yes_no(v: Any) -> bool:
    if not isinstance(v, bool):
        raise ValueError(f"must be true or false, got {v!r}")
    return v


def _must_be(expected: bool) -> Callable[[Any], bool]:
    def check(v: Any) -> bool:
        if _yes_no(v) is not expected:
            raise ValueError(f"must be {str(expected).lower()}, got {str(v).lower()}")
        return v
    return check


_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def _clock_time(v: Any) -> time:
    if not isinstance(v, str) or not _TIME_RE.match(v):
        raise ValueError(f'must be a UK time written "HH:MM", got {v!r}')
    hours, minutes = v.split(":")
    return time(int(hours), int(minutes))


def _clock_times(v: Any) -> tuple[time, ...]:
    if not isinstance(v, list) or not v:
        raise ValueError(f"must be a non-empty list of times, got {v!r}")
    times = tuple(_clock_time(t) for t in v)
    if list(times) != sorted(set(times)):
        raise ValueError("times must be in order with no repeats")
    return times


def _timezone(v: Any) -> ZoneInfo:
    if v != "Europe/London":
        raise ValueError(f"must be 'Europe/London' (UK time), got {v!r}")
    try:
        return ZoneInfo(v)
    except ZoneInfoNotFoundError as e:  # pragma: no cover - system problem
        raise ValueError(f"time zone {v!r} is not installed on this server") from e


_TIMEFRAMES = ("tick", "5m", "1h", "4h", "1d", "1w")


def _timeframes(v: Any) -> tuple[str, ...]:
    if not isinstance(v, list) or not v:
        raise ValueError(f"must be a non-empty list, got {v!r}")
    for tf in v:
        if tf not in _TIMEFRAMES:
            raise ValueError(f"{tf!r} is not a known candle size; allowed: {', '.join(_TIMEFRAMES)}")
    if len(set(v)) != len(v):
        raise ValueError("candle sizes must not repeat")
    return tuple(v)


# ---- the full list of settings ---------------------------------------------
# section -> setting -> check.  Every setting in settings.toml must be listed
# here and nothing else is allowed.

SCHEMA: dict[str, dict[str, Callable[[Any], Any]]] = {
    "account": {
        "pair": _exactly("GBPUSD"),
        "account_type": _exactly("demo"),
    },
    "prices": {
        "candle_timeframes": _timeframes,
    },
    "trade": {
        "size_gbp_per_pip": _whole_number(1, 1000),
        "stop_loss_pips": _whole_number(1, 100),
        "take_profit_pips": _whole_number(1, 1000),
    },
    "hours": {
        "timezone": _timezone,
        "new_trades_from": _clock_time,
        "new_trades_until": _clock_time,
        "close_all_trades_at": _clock_time,
        "hold_overnight": _must_be(False),
    },
    "news": {
        "big_news_no_new_trades_before_minutes": _whole_number(0, 240),
        "big_news_no_new_trades_after_minutes": _whole_number(0, 240),
        "big_news_close_trades_before_minutes": _whole_number(0, 240),
        "ignore_medium_and_small_news": _yes_no,
    },
    "limits": {
        "max_open_trades_per_strategy": _whole_number(1, 10),
        "bollinger_bounce_extra_opposite_direction_trades": _whole_number(0, 10),
    },
    "levels": {
        "line_up_within_pips": _whole_number(0, 100),
        "turning_levels_lookback_weeks": _whole_number(1, 52),
    },
    "reversal_watch": {
        "times": _clock_times,
        "minutes_before": _whole_number(0, 120),
        "minutes_after": _whole_number(0, 120),
    },
    "bounce": {
        "reversal_candle_within_candles_of_pierce": _whole_number(1, 50),
        "confirmation_candle_within_candles_of_reversal": _whole_number(1, 50),
    },
    "slow_grind": {
        "min_pause_candles": _whole_number(1, 100),
    },
    "ema_pullback": {
        "setup_expires_after_minutes": _whole_number(1, 1440),
        "entry_beyond_pips": _whole_number(0, 100),
        "entry_lookback_candles": _whole_number(1, 100),
    },
    "possible_reversal": {
        "min_trend_move_pips": _whole_number(1, 1000),
    },
    "range_trade": {
        "close_percent_at_opposite_band": _whole_number(1, 100),
    },
    "ig": {
        # Demo only: the bot refuses to start with any other address.
        "demo_base_url": _exactly("https://demo-api.ig.com/gateway/deal"),
        "slowed_down_waits_seconds": _whole_numbers(1, 600),
        "request_timeout_seconds": _whole_number(1, 120),
    },
}


class Settings:
    """Checked settings. Read them as settings.section.name, e.g. settings.trade.stop_loss_pips."""

    def __init__(self, values: dict[str, dict[str, Any]]):
        self._values = values
        for section, items in values.items():
            setattr(self, section, _Section(section, items))

    def __setattr__(self, name: str, value: Any) -> None:
        if hasattr(self, name):
            raise AttributeError("settings cannot be changed while the bot is running")
        super().__setattr__(name, value)

    def as_dict(self) -> dict[str, dict[str, Any]]:
        return {s: dict(items) for s, items in self._values.items()}


class _Section:
    def __init__(self, name: str, items: dict[str, Any]):
        object.__setattr__(self, "_name", name)
        for key, value in items.items():
            object.__setattr__(self, key, value)

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("settings cannot be changed while the bot is running")

    def __repr__(self) -> str:
        return f"<settings [{self._name}]>"


def _check_together(v: dict[str, dict[str, Any]]) -> None:
    """Checks that involve more than one setting."""
    h = v["hours"]
    if h["new_trades_from"] >= h["new_trades_until"]:
        raise SettingsError(
            "Setting [hours] new_trades_from must be earlier than new_trades_until."
        )
    if h["close_all_trades_at"] < h["new_trades_until"]:
        raise SettingsError(
            "Setting [hours] close_all_trades_at must not be earlier than new_trades_until."
        )


def load_settings(path: str | Path | None = None) -> Settings:
    """Load and check the settings file. Raises SettingsError if anything is wrong."""
    if path is None:
        path = os.environ.get(PATH_ENV_VAR) or DEFAULT_PATH
    path = Path(path)

    try:
        with path.open("rb") as f:
            raw = tomllib.load(f)
    except FileNotFoundError:
        raise SettingsError(f"Settings file not found: {path}") from None
    except tomllib.TOMLDecodeError as e:
        raise SettingsError(f"Settings file {path} is not valid TOML: {e}") from None

    problems: list[str] = []
    checked: dict[str, dict[str, Any]] = {}

    for section in raw:
        if section not in SCHEMA:
            problems.append(f"Unknown section [{section}].")
    for section, fields in SCHEMA.items():
        given = raw.get(section)
        if given is None:
            problems.append(f"Missing section [{section}].")
            continue
        if not isinstance(given, dict):
            problems.append(f"[{section}] must be a section, not a single value.")
            continue
        for key in given:
            if key not in fields:
                problems.append(f"Unknown setting [{section}] {key}.")
        checked[section] = {}
        for key, check in fields.items():
            if key not in given:
                problems.append(f"Missing setting [{section}] {key}.")
                continue
            try:
                checked[section][key] = check(given[key])
            except ValueError as e:
                problems.append(f"Invalid setting [{section}] {key}: {e}.")

    if problems:
        raise SettingsError(
            f"Settings file {path} has {len(problems)} problem(s):\n  - "
            + "\n  - ".join(problems)
        )

    _check_together(checked)
    return Settings(checked)


def load_or_exit(path: str | Path | None = None) -> Settings:
    """Load settings, or stop the program with a clear message (exit code 1)."""
    try:
        return load_settings(path)
    except SettingsError as e:
        raise SystemExit(f"AutoBot cannot start: {e}") from None
