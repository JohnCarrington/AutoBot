"""Loads and checks config/settings.toml, and (for the programs) the switches
in .env (config/switches.py).

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

from config.env_file import env_path
from config.pairs import PAIR_NAME, Pair, PairSettings, pip_size
from config.switches import SWITCHES_SECTION, read_switches

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


def _decimal_number(minimum: str, maximum: str) -> Callable[[Any], "Decimal"]:
    from decimal import Decimal, InvalidOperation
    lo, hi = Decimal(minimum), Decimal(maximum)

    def check(v: Any) -> Decimal:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError(f"must be a number, got {v!r}")
        try:
            d = Decimal(str(v))
        except InvalidOperation:
            raise ValueError(f"must be a number, got {v!r}") from None
        if not lo <= d <= hi:
            raise ValueError(f"must be between {minimum} and {maximum}, got {v}")
        return d
    return check


_LEVEL_TYPES = ("pivot", "R1", "R2", "R3", "S1", "S2", "S3", "round_number", "previous_day_high",
                "previous_day_low", "london_session_high", "london_session_low", "new_york_session_high",
                "new_york_session_low", "turning_high", "turning_low")


def _level_types(v: Any) -> tuple[str, ...]:
    if not isinstance(v, list) or not v:
        raise ValueError(f"must be a non-empty list of level types, got {v!r}")
    for t in v:
        if t not in _LEVEL_TYPES:
            raise ValueError(f"{t!r} is not a level type; allowed: {', '.join(_LEVEL_TYPES)}")
    return tuple(v)


def _names(v: Any) -> tuple[str, ...]:
    if not isinstance(v, list) or not v or not all(isinstance(x, str) and x.strip() for x in v):
        raise ValueError(f"must be a non-empty list of names, got {v!r}")
    return tuple(x.strip() for x in v)


def _impacts(v: Any) -> tuple[str, ...]:
    if not isinstance(v, list) or not v or any(x not in ("high", "medium", "low") for x in v):
        raise ValueError(f"must be a non-empty list of Finnhub impacts (high, medium, low), got {v!r}")
    return tuple(v)


def _country_currencies(v: Any) -> dict[str, str]:
    if not isinstance(v, list) or not v:
        raise ValueError(f"must be a non-empty list like [\"GB=GBP\"], got {v!r}")
    out = {}
    for x in v:
        if not isinstance(x, str) or not re.fullmatch(r"[A-Z]{2,3}=[A-Z]{3}", x):
            raise ValueError(f"each item must look like \"GB=GBP\", got {x!r}")
        k, c = x.split("=")
        out[k] = c
    return out


def _exactly(expected: str) -> Callable[[Any], str]:
    def check(v: Any) -> str:
        if v != expected:
            raise ValueError(f"must be {expected!r}, got {v!r}")
        return v
    return check


def _one_of(*allowed: str) -> Callable[[Any], str]:
    def check(v: Any) -> str:
        if v not in allowed:
            raise ValueError(f"must be one of {', '.join(repr(x) for x in allowed)}, got {v!r}")
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


def _utc_time(v: Any) -> time:
    """A time of day in UTC, written "HH:MM" (used where a setting says so)."""
    if not isinstance(v, str) or not _TIME_RE.match(v):
        raise ValueError(f'must be a UTC time written "HH:MM", got {v!r}')
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


_WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


class Weekday(int):
    """A day of the week: works as a number (Monday 0 ... Sunday 6, as in
    Python's datetime.weekday()) and prints as its name."""

    def __str__(self) -> str:
        return _WEEKDAYS[self]

    __repr__ = __str__


def _weekday(v: Any) -> Weekday:
    if v not in _WEEKDAYS:
        raise ValueError(f"must be a day name ({', '.join(_WEEKDAYS)}), got {v!r}")
    return Weekday(_WEEKDAYS.index(v))


def _clock_time_on_5_minutes(v: Any) -> time:
    t = _clock_time(v)
    if t.minute % 5:
        raise ValueError(f"must be on a 5-minute mark (candles are built from 5-minute candles), got {v!r}")
    return t


def _minute_on_5(v: Any) -> int:
    m = _whole_number(0, 55)(v)
    if m % 5:
        raise ValueError(f"must be a multiple of 5 (candles are built from 5-minute candles), got {m}")
    return m


_EPIC_RE = re.compile(r"^[A-Z0-9]+(\.[A-Z0-9]+)+$")


def _epic(v: Any) -> str:
    if not isinstance(v, str) or not _EPIC_RE.match(v):
        raise ValueError(f"must be an IG epic like 'CS.D.GBPUSD.TODAY.IP', got {v!r}")
    return v


def _market_time_zone(v: Any) -> ZoneInfo:
    if v not in ("Europe/London", "America/New_York"):
        raise ValueError(f"must be 'Europe/London' or 'America/New_York', got {v!r}")
    return ZoneInfo(v)


def _absolute_folder(v: Any) -> Path:
    if not isinstance(v, str) or not v.startswith("/"):
        raise ValueError(f"must be a full folder path starting with '/', got {v!r}")
    return Path(v)


# ---- the full list of settings ---------------------------------------------
# section -> setting -> check.  Every setting in settings.toml must be listed
# here and nothing else is allowed.

SCHEMA: dict[str, dict[str, Callable[[Any], Any]]] = {
    "account": {
        "account_type": _exactly("demo"),
    },
    "prices": {
        "candle_timeframes": _timeframes,
    },
    "trade": {
        "size_gbp_per_pip": _whole_number(1, 1000),
    },
    "hours": {
        "timezone": _timezone,
        "close_all_trades_at": _clock_time,
        "hold_overnight": _must_be(False),
    },
    "news": {
        "big_news_no_new_trades_before_minutes": _whole_number(0, 240),
        "big_news_no_new_trades_after_minutes": _whole_number(0, 240),
        "big_news_close_trades_before_minutes": _whole_number(0, 240),
        "ignore_medium_and_small_news": _yes_no,
        "finnhub_url": _exactly("https://finnhub.io/api/v1"),
        "request_timeout_seconds": _whole_number(1, 120),
        "refresh_hours": _whole_number(1, 48),
        "retry_minutes": _whole_number(5, 1440),
        "fetch_days_back": _whole_number(0, 60),
        "fetch_days_ahead": _whole_number(1, 60),
        "keep_days": _whole_number(7, 3650),
        "out_of_date_hours": _whole_number(1, 168),
        "check_minutes": _whole_number(1, 120),
        "alert_every_hours": _whole_number(1, 72),
        "folder": _absolute_folder,
        "lower_is_better": _names,
        "country_currencies": _country_currencies,
        "table_impacts": _impacts,
    },
    "limits": {
        "max_open_trades_per_strategy": _whole_number(1, 10),
        "bollinger_bounce_extra_opposite_direction_trades": _whole_number(0, 10),
    },
    "chart": {
        "price": _one_of("sell", "buy"),
    },
    "levels": {
        "line_up_within_pips": _whole_number(0, 100),
        "turning_levels_lookback_weeks": _whole_number(1, 52),
        "folder": _absolute_folder,
        "level_decimals": _whole_number(0, 4),
        "round_number_every_pips": _whole_number(1, 1000),
        "round_numbers_within_pips": _whole_number(0, 2000),
        "sessions_time_zone": _exactly("UTC"),
        "london_session_from": _utc_time,
        "london_session_until": _utc_time,
        "new_york_session_from": _utc_time,
        "new_york_session_until": _utc_time,
        "turning_candles_each_side": _whole_number(1, 24),
        "turning_min_move_pips": _whole_number(1, 1000),
        "turning_move_within_candles": _whole_number(1, 200),
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
        "ema_periods": _whole_number(2, 200),
    },
    "ema_pullback": {
        "setup_expires_after_minutes": _whole_number(1, 1440),
        "entry_beyond_pips": _whole_number(0, 100),
        "entry_lookback_candles": _whole_number(1, 100),
        "take_profit_pips": _whole_number(1, 1000),
        "fast_ema_periods": _whole_number(2, 200),
        "mid_ema_periods": _whole_number(2, 200),
        "slow_ema_periods": _whole_number(2, 200),
        "hourly_fast_ema_periods": _whole_number(2, 200),
        "hourly_mid_ema_periods": _whole_number(2, 200),
        "hourly_slow_ema_periods": _whole_number(2, 200),
        "hourly_slope_candles": _whole_number(1, 50),
        "hourly_min_slope_pips_per_hour": _decimal_number("0", "100"),
        "hourly_min_gap_fast_mid_pips": _decimal_number("0", "100"),
        "hourly_min_gap_mid_slow_pips": _decimal_number("0", "100"),
        "hourly_history_candles": _whole_number(50, 5000),
    },
    "possible_reversal": {
        "min_trend_move_pips": _whole_number(1, 1000),
    },
    "breakout": {
        "trigger_within_candles": _whole_number(1, 50),
        "stop_loss_pips": _whole_number(0, 100),
        "take_profit_pips": _whole_number(0, 1000),
    },
    "range_trade": {
        "close_percent_at_opposite_band": _whole_number(1, 100),
        "rejection_candle_within_candles": _whole_number(1, 10),
        "trigger_within_candles": _whole_number(1, 10),
    },
    "indicators": {
        "bollinger_periods": _whole_number(2, 200),
        "bollinger_std_devs": _whole_number(1, 5),
        "ema_periods": _whole_numbers(2, 500),
        "macd_fast_periods": _whole_number(2, 500),
        "macd_slow_periods": _whole_number(2, 500),
        "macd_signal_periods": _whole_number(2, 500),
        "rsi_periods": _whole_number(2, 100),
        "rsi_upper_line": _whole_number(51, 100),
        "rsi_lower_line": _whole_number(0, 49),
        "timeframes": _timeframes,
        "history_candles": _whole_number(100, 20000),
        "warm_up_seed_weight_percent": _whole_number(1, 50),
    },
    "analyser": {
        "direction_ema_timeframe": _one_of("5m", "1h", "4h"),
        "direction_ema_periods": _whole_number(2, 500),
        "out_of_date_after_minutes": _whole_number(1, 1440),
    },
    "market_states": {
        "narrow_band_max_pips": _whole_number(1, 100),
        "narrowing_candles": _whole_number(2, 100),
        "flat_max_pips_per_candle": _decimal_number("0.01", "100"),
        "flat_slope_candles": _whole_number(2, 100),
        "ranging_min_band_pips": _whole_number(1, 200),
        "ranging_max_band_pips": _whole_number(1, 200),
        "ranging_band_flat_max_pips_per_candle": _decimal_number("0.01", "100"),
        "ranging_both_bands_candles": _whole_number(2, 200),
        "weave_candles": _whole_number(2, 100),
        "ema100_flat_max_pips": _whole_number(1, 100),
        "ema100_flat_candles": _whole_number(2, 200),
        "consolidation_quiet_candles": _whole_number(2, 100),
        "consolidation_max_body_pips": _whole_number(1, 50),
        "consolidation_colour_max_ratio": _whole_number(1, 20),
        "near_band_pips": _whole_number(0, 20),
        "persistence_candles": _whole_number(1, 20),
        "evidence_fades_after_candles": _whole_number(2, 500),
        "ema_stacked_candles": _whole_number(1, 50),
        "failed_bounce_within_pips": _whole_number(0, 20),
        "push_candles": _whole_number(2, 50),
        "push_colour_body_percent": _whole_number(1, 100),
        "push_band_widening_percent": _whole_number(100, 1000),
        "band_widening_candles": _whole_number(2, 100),
        "push_ema_fan_pips": _whole_number(1, 100),
        "push_riding_band_closes": _whole_number(1, 50),
        "spike_range_multiple": _whole_number(2, 20),
        "spike_average_candles": _whole_number(2, 200),
        "indicator_warm_up_candles": _whole_number(100, 20000),
        "folder": _absolute_folder,
        "strong_level_types": _level_types,
    },
    "rejection": {
        "candle_timeframe": _one_of("5m", "1h", "4h"),
        "near_level_within_pips": _whole_number(0, 50),
        "max_spread_pips": _whole_number(1, 100),
    },
    "market_hours": {
        "opens_day": _weekday,
        "opens_at": _clock_time_on_5_minutes,
        "opens_time_zone": _market_time_zone,
        "closes_day": _weekday,
        "closes_at": _clock_time_on_5_minutes,
        "closes_time_zone": _market_time_zone,
    },
    "stream": {
        "reconnect_waits_seconds": _whole_numbers(1, 600),
        "no_prices_warning_seconds": _whole_number(10, 3600),
        "healthy_after_minutes": _whole_number(1, 1440),
        "status_log_minutes": _whole_number(1, 1440),
    },
    "candles": {
        "folder": _absolute_folder,
        "hour_starts_at_minute": _minute_on_5,
        "four_hour_starts_at": _clock_time_on_5_minutes,
        "day_starts_at": _clock_time_on_5_minutes,
        "week_starts_day": _weekday,
        "join_opening_stretch": _yes_no,
        "wait_for_late_candle_seconds": _whole_number(0, 3600),
        "compress_after_days": _whole_number(8, 3650),
    },
    "housekeeping": {
        "log_folder": _absolute_folder,
        "log_max_file_mb": _whole_number(1, 1000),
        "log_new_file_every_hours": _whole_number(1, 168),
        "log_keep_files": _whole_number(1, 1000),
        "log_max_age_days": _whole_number(1, 3650),
        "min_free_disk_mb": _whole_number(100, 1_000_000),
    },
    "history": {
        "folder": _absolute_folder,
        # "well below IG's 10,000"
        # At most IG's 10,000 a week less the 2,000 safety floor (docs/SETTINGS.md).
        "weekly_budget_points": _whole_number(1, 8000),
        "min_ig_allowance_remaining": _whole_number(0, 10000),
        "max_points_per_request": _whole_number(1, 1000),
        "min_block_hours": _whole_number(1, 24 * 14),
    },
    "alerts": {
        "telegram_url": _exactly("https://api.telegram.org"),
        "request_timeout_seconds": _whole_number(1, 120),
        "same_problem_every_minutes": _whole_number(1, 1440),
        "folder": _absolute_folder,
        "daily_ready_at": _clock_time,
        "daily_ready_late_by_minutes": _whole_number(1, 720),
        "sunday_ready_within_minutes": _whole_number(5, 720),
        "candles_arriving_within_minutes": _whole_number(5, 120),
    },
    "ig": {
        # Demo only: the bot refuses to start with any other address.
        "demo_base_url": _exactly("https://demo-api.ig.com/gateway/deal"),
        "slowed_down_waits_seconds": _whole_numbers(1, 600),
        "request_timeout_seconds": _whole_number(1, 120),
    },
}


class Settings:
    """Checked settings. Read them as settings.section.name, e.g. settings.trade.size_gbp_per_pip.
    settings.pairs: every [pairs.<PAIR>]; settings.for_pair(name): the settings for one
    pair (config/pairs.py). settings.switches: the .env switches, when loaded."""

    def __init__(self, values: dict[str, dict[str, Any]], pairs: dict[str, Pair] | None = None,
                 switches: dict[str, Any] | None = None):
        self._values = values
        for section, items in values.items():
            setattr(self, section, _Section(section, items))
        self.pairs = dict(pairs or {})
        if switches is not None:
            self.switches = _Section(SWITCHES_SECTION, switches)

    def for_pair(self, name: str) -> PairSettings:
        if name not in self.pairs:
            raise SettingsError(f"There is no [pairs.{name}] section in the settings.")
        return PairSettings(self, self.pairs[name])

    def pairs_on(self) -> list[PairSettings]:
        """The settings for each pair switched on in .env."""
        return [self.for_pair(p) for p in self.switches.pairs_on]

    def __setattr__(self, name: str, value: Any) -> None:
        if hasattr(self, name):
            raise AttributeError("settings cannot be changed while the bot is running")
        super().__setattr__(name, value)

    def as_dict(self) -> dict[str, dict[str, Any]]:
        out = {s: dict(items) for s, items in self._values.items()}
        for name, p in self.pairs.items():
            out[f"pairs.{name}"] = {"epic": p.epic, "pip_size": p.pip_size, "price_scale": p.price_scale,
                                    "points_per_pip": p.points_per_pip}
        if hasattr(self, "switches"):
            out[".env switches"] = {k: v for k, v in vars(self.switches).items() if not k.startswith("_")}
        return out


class _Section:
    def __init__(self, name: str, items: dict[str, Any]):
        object.__setattr__(self, "_name", name)
        for key, value in items.items():
            object.__setattr__(self, key, value)

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("settings cannot be changed while the bot is running")

    def __repr__(self) -> str:
        return f"<settings [{self._name}]>"


# Each pair: [pairs.<PAIR>] (config/pairs.py)
PAIR_SCHEMA: dict[str, Callable[[Any], Any]] = {
    "epic": _epic,
    "pip_size": pip_size,
    "price_scale": _whole_number(1, 1_000_000),
}


def _check_pairs(raw: Any, problems: list[str]) -> dict[str, Pair]:
    pairs: dict[str, Pair] = {}
    if raw is None:
        problems.append("Missing section [pairs] (at least one [pairs.<PAIR>]).")
        return pairs
    if not isinstance(raw, dict) or not raw:
        problems.append("[pairs] must hold at least one [pairs.<PAIR>] section.")
        return pairs
    for name, given in raw.items():
        if not PAIR_NAME.match(name):
            problems.append(f"[pairs.{name}]: the pair name must be 6 capital letters, like GBPUSD.")
            continue
        if not isinstance(given, dict):
            problems.append(f"[pairs.{name}] must be a section.")
            continue
        for key in given:
            if key not in PAIR_SCHEMA:
                problems.append(f"Unknown setting [pairs.{name}] {key}.")
        got: dict[str, Any] = {}
        for key, check in PAIR_SCHEMA.items():
            if key not in given:
                problems.append(f"Missing setting [pairs.{name}] {key}.")
                continue
            try:
                got[key] = check(given[key])
            except ValueError as e:
                problems.append(f"Invalid setting [pairs.{name}] {key}: {e}.")
        if len(got) == len(PAIR_SCHEMA):
            pair = Pair(name, got["epic"], got["pip_size"], got["price_scale"])
            if pair.points_per_pip <= 0:
                problems.append(f"[pairs.{name}]: pip_size x price_scale must be above 0.")
            pairs[name] = pair
    epics = [p.epic for p in pairs.values()]
    if len(set(epics)) != len(epics):
        problems.append("Two [pairs.*] sections have the same epic.")
    return pairs


def _check_switches(sw: dict[str, Any], v: dict[str, dict[str, Any]], pairs: dict[str, Pair], where: Path) -> None:
    unknown = [p for p in sw["pairs_on"] if p not in pairs]
    if unknown:
        raise SettingsError(f"Switch PAIRS_ON in {where} names {', '.join(unknown)}, which has no "
                            "[pairs.<PAIR>] section in settings.toml.")
    if sw["new_trades_from"] >= sw["new_trades_until"]:
        raise SettingsError(f"Switch NEW_TRADES_FROM in {where} must be earlier than NEW_TRADES_UNTIL.")
    if v["hours"]["close_all_trades_at"] < sw["new_trades_until"]:
        raise SettingsError(f"Setting [hours] close_all_trades_at must not be earlier than the switch "
                            f"NEW_TRADES_UNTIL in {where}.")
    if sw["breakout"] and not (v["breakout"]["stop_loss_pips"] and v["breakout"]["take_profit_pips"]):
        raise SettingsError(f"Switch STRATEGY_BREAKOUT in {where} is on, but breakout.stop_loss_pips and "
                            "breakout.take_profit_pips are not both chosen (0 means not chosen) in settings.toml.")


def _check_together(v: dict[str, dict[str, Any]]) -> None:
    """Checks that involve more than one setting (the hours checks are with the switches)."""


def _check_levels_together(v: dict[str, dict[str, Any]]) -> None:
    lv = v["levels"]
    for name in ("london", "new_york"):
        if lv[f"{name}_session_from"] >= lv[f"{name}_session_until"]:
            raise SettingsError(
                f"Setting [levels] {name}_session_from must be earlier than {name}_session_until."
            )


def _check_indicators_together(v: dict[str, dict[str, Any]]) -> None:
    ind, an = v["indicators"], v["analyser"]
    e = ind["ema_periods"]
    if list(e) != sorted(set(e)):
        raise SettingsError("Setting [indicators] ema_periods must go up with no repeats.")
    if "tick" in ind["timeframes"]:
        raise SettingsError("Setting [indicators] timeframes cannot include 'tick': indicators need candles.")
    if ind["macd_fast_periods"] >= ind["macd_slow_periods"]:
        raise SettingsError("Setting [indicators] macd_fast_periods must be smaller than macd_slow_periods.")
    longest = max(max(e), ind["macd_slow_periods"] + ind["macd_signal_periods"], ind["bollinger_periods"],
                  ind["rsi_periods"] + 1)
    if ind["history_candles"] < longest:
        raise SettingsError(f"Setting [indicators] history_candles must be at least {longest} "
                            "(the longest indicator).")
    if an["direction_ema_timeframe"] not in ind["timeframes"]:
        raise SettingsError("Setting [analyser] direction_ema_timeframe must be one of [indicators] timeframes.")
    if an["direction_ema_periods"] not in e:
        raise SettingsError("Setting [analyser] direction_ema_periods must be one of [indicators] ema_periods.")


def _check_candles_together(v: dict[str, dict[str, Any]]) -> None:
    c, mh = v["candles"], v["market_hours"]
    w = v["stream"]["reconnect_waits_seconds"]
    if list(w) != sorted(w):
        raise SettingsError("Setting [stream] reconnect_waits_seconds must go up (never get shorter).")
    if c["day_starts_at"].minute != c["hour_starts_at_minute"]:
        raise SettingsError("Setting [candles] day_starts_at must start on an hour boundary "
                            "(its minutes must equal hour_starts_at_minute).")
    four = c["four_hour_starts_at"]
    day = c["day_starts_at"]
    if four.minute != day.minute or (four.hour - day.hour) % 4:
        raise SettingsError("Setting [candles] four_hour_starts_at must line up with day_starts_at, "
                            "so that 4-hour candles fit exactly into each day.")
    h = v["history"]
    if h["max_points_per_request"] > h["weekly_budget_points"]:
        raise SettingsError("Setting [history] max_points_per_request must not be bigger than weekly_budget_points.")
    if mh["opens_day"] == mh["closes_day"]:
        raise SettingsError("Settings [market_hours] opens_day and closes_day must be different days.")


def load_settings(path: str | Path | None = None, *, switches_from: str | Path | None = None) -> Settings:
    """Load and check the settings file. Raises SettingsError if anything is wrong.
    switches_from: also read and check the switches in this .env file."""
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

    pairs = _check_pairs(raw.get("pairs"), problems)
    for section in raw:
        if section != "pairs" and section not in SCHEMA:
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
    _check_candles_together(checked)
    _check_levels_together(checked)
    _check_indicators_together(checked)
    switches = None
    if switches_from is not None:
        switches, sw_problems = read_switches(Path(switches_from))
        if sw_problems:
            raise SettingsError(f"The switches have {len(sw_problems)} problem(s):\n  - " + "\n  - ".join(sw_problems))
        _check_switches(switches, checked, pairs, Path(switches_from))
    return Settings(checked, pairs, switches)


def load_or_exit(path: str | Path | None = None) -> Settings:
    """Load the settings AND the .env switches, or stop the program with a clear
    message (exit code 1). This is what every program uses at start-up."""
    try:
        return load_settings(path, switches_from=env_path())
    except SettingsError as e:
        raise SystemExit(f"AutoBot cannot start: {e}") from None
