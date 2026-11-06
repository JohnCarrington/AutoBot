"""Technical tests: every setting loads with the right value, and a missing or
invalid setting stops the bot with a clear message."""

import subprocess
import sys
import tomllib
from datetime import time
from pathlib import Path

import pytest

from config.settings_loader import (
    DEFAULT_PATH,
    SCHEMA,
    SettingsError,
    load_or_exit,
    load_settings,
)

ROOT = Path(__file__).resolve().parents[2]

# The values the owner asked for. If a value in settings.toml changes, this
# table must be changed on purpose too.
EXPECTED = {
    "account": {"pair": "GBPUSD", "account_type": "demo"},
    "prices": {"candle_timeframes": ("tick", "5m", "1h", "4h", "1d", "1w")},
    "trade": {"size_gbp_per_pip": 10, "stop_loss_pips": 6, "take_profit_pips": 100},
    "hours": {
        "new_trades_from": time(6, 0),
        "new_trades_until": time(20, 30),
        "close_all_trades_at": time(20, 30),
        "hold_overnight": False,
    },
    "news": {
        "big_news_no_new_trades_before_minutes": 15,
        "big_news_no_new_trades_after_minutes": 30,
        "big_news_close_trades_before_minutes": 15,
        "ignore_medium_and_small_news": True,
    },
    "limits": {
        "max_open_trades_per_strategy": 1,
        "bollinger_bounce_extra_opposite_direction_trades": 1,
    },
    "levels": {"line_up_within_pips": 5, "turning_levels_lookback_weeks": 2},
    "reversal_watch": {
        "times": (time(10), time(11), time(13), time(14), time(16), time(17)),
        "minutes_before": 20,
        "minutes_after": 20,
    },
    "bounce": {
        "reversal_candle_within_candles_of_pierce": 3,
        "confirmation_candle_within_candles_of_reversal": 3,
    },
    "slow_grind": {"min_pause_candles": 3},
    "ema_pullback": {
        "setup_expires_after_minutes": 20,
        "entry_beyond_pips": 3,
        "entry_lookback_candles": 5,
    },
    "possible_reversal": {"min_trend_move_pips": 30},
    "range_trade": {"close_percent_at_opposite_band": 50},
}

ALL_VALUES = [
    (section, key, value)
    for section, items in EXPECTED.items()
    for key, value in items.items()
]


@pytest.fixture(scope="module")
def settings():
    return load_settings()


# ---- every setting loads with the right value -------------------------------

@pytest.mark.parametrize("section,key,expected", ALL_VALUES,
                         ids=[f"{s}.{k}" for s, k, _ in ALL_VALUES])
def test_setting_has_the_right_value(settings, section, key, expected):
    assert getattr(getattr(settings, section), key) == expected


def test_timezone_is_uk_time(settings):
    tz = settings.hours.timezone
    assert str(tz) == "Europe/London"
    from datetime import datetime
    # GMT in winter, BST in summer.
    assert datetime(2026, 1, 15, 12, tzinfo=tz).utcoffset().total_seconds() == 0
    assert datetime(2026, 7, 15, 12, tzinfo=tz).utcoffset().total_seconds() == 3600


def test_every_setting_in_the_file_is_tested():
    """Nothing in settings.toml escapes the value checks above."""
    with DEFAULT_PATH.open("rb") as f:
        raw = tomllib.load(f)
    in_file = {(s, k) for s, items in raw.items() for k in items}
    tested = {(s, k) for s, k, _ in ALL_VALUES} | {("hours", "timezone")}
    assert in_file == tested


def test_settings_cannot_be_changed_while_running(settings):
    with pytest.raises(AttributeError):
        settings.trade.stop_loss_pips = 50
    with pytest.raises(AttributeError):
        settings.trade = None


# ---- missing or invalid settings stop the bot -------------------------------

def _raw():
    with DEFAULT_PATH.open("rb") as f:
        return tomllib.load(f)


def _to_toml(data):
    def val(v):
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, str):
            return f'"{v}"'
        if isinstance(v, list):
            return "[" + ", ".join(val(x) for x in v) + "]"
        return str(v)
    lines = []
    for section, items in data.items():
        if not isinstance(items, dict):
            lines.append(f"{section} = {val(items)}")
    for section, items in data.items():
        if isinstance(items, dict):
            lines.append(f"[{section}]")
            lines += [f"{k} = {val(v)}" for k, v in items.items()]
    return "\n".join(lines) + "\n"


def _write(tmp_path, data):
    p = tmp_path / "settings.toml"
    p.write_text(_to_toml(data))
    return p


def test_round_trip_helper_gives_a_valid_file(tmp_path):
    load_settings(_write(tmp_path, _raw()))


ALL_KEYS = [(s, k) for s, fields in SCHEMA.items() for k in fields]


@pytest.mark.parametrize("section,key", ALL_KEYS, ids=[f"{s}.{k}" for s, k in ALL_KEYS])
def test_missing_setting_is_named(tmp_path, section, key):
    data = _raw()
    del data[section][key]
    with pytest.raises(SettingsError, match=rf"Missing setting \[{section}\] {key}\."):
        load_settings(_write(tmp_path, data))


@pytest.mark.parametrize("section", list(SCHEMA))
def test_missing_section_is_named(tmp_path, section):
    data = _raw()
    del data[section]
    with pytest.raises(SettingsError, match=rf"Missing section \[{section}\]\."):
        load_settings(_write(tmp_path, data))


INVALID = [
    ("account", "pair", "EURUSD", "must be 'GBPUSD'"),
    ("account", "account_type", "live", "must be 'demo'"),
    ("prices", "candle_timeframes", ["5m", "2h"], "not a known candle size"),
    ("trade", "size_gbp_per_pip", "ten", "must be a whole number"),
    ("trade", "size_gbp_per_pip", 0, "must be between"),
    ("trade", "stop_loss_pips", -6, "must be between"),
    ("trade", "stop_loss_pips", 6.5, "must be a whole number"),
    ("trade", "take_profit_pips", True, "must be a whole number"),
    ("hours", "timezone", "UTC", "must be 'Europe/London'"),
    ("hours", "new_trades_from", "6am", 'written "HH:MM"'),
    ("hours", "new_trades_until", "24:00", 'written "HH:MM"'),
    ("hours", "close_all_trades_at", 2030, 'written "HH:MM"'),
    ("hours", "hold_overnight", True, "must be false"),
    ("news", "big_news_no_new_trades_before_minutes", -1, "must be between"),
    ("news", "ignore_medium_and_small_news", "yes", "must be true or false"),
    ("limits", "max_open_trades_per_strategy", 0, "must be between"),
    ("levels", "line_up_within_pips", "5", "must be a whole number"),
    ("levels", "turning_levels_lookback_weeks", 0, "must be between"),
    ("reversal_watch", "times", ["11:00", "10:00"], "in order with no repeats"),
    ("reversal_watch", "times", [], "non-empty list"),
    ("reversal_watch", "minutes_before", 500, "must be between"),
    ("bounce", "reversal_candle_within_candles_of_pierce", 0, "must be between"),
    ("slow_grind", "min_pause_candles", 0, "must be between"),
    ("ema_pullback", "setup_expires_after_minutes", 0, "must be between"),
    ("possible_reversal", "min_trend_move_pips", 0, "must be between"),
    ("range_trade", "close_percent_at_opposite_band", 150, "must be between"),
]


@pytest.mark.parametrize("section,key,bad,reason", INVALID,
                         ids=[f"{s}.{k}={b!r}" for s, k, b, _ in INVALID])
def test_invalid_setting_is_named_with_reason(tmp_path, section, key, bad, reason):
    data = _raw()
    data[section][key] = bad
    with pytest.raises(SettingsError) as e:
        load_settings(_write(tmp_path, data))
    msg = str(e.value)
    assert f"Invalid setting [{section}] {key}:" in msg
    assert reason in msg


def test_unknown_setting_is_rejected(tmp_path):
    data = _raw()
    data["trade"]["stop_loss_pip"] = 6  # typo
    with pytest.raises(SettingsError, match=r"Unknown setting \[trade\] stop_loss_pip\."):
        load_settings(_write(tmp_path, data))


def test_unknown_section_is_rejected(tmp_path):
    data = _raw()
    data["extras"] = {"x": 1}
    with pytest.raises(SettingsError, match=r"Unknown section \[extras\]\."):
        load_settings(_write(tmp_path, data))


def test_all_problems_reported_together(tmp_path):
    data = _raw()
    del data["trade"]["stop_loss_pips"]
    data["levels"]["line_up_within_pips"] = "five"
    with pytest.raises(SettingsError) as e:
        load_settings(_write(tmp_path, data))
    msg = str(e.value)
    assert "has 2 problem(s)" in msg
    assert "Missing setting [trade] stop_loss_pips." in msg
    assert "Invalid setting [levels] line_up_within_pips" in msg


def test_trading_hours_must_be_in_order(tmp_path):
    data = _raw()
    data["hours"]["new_trades_from"] = "21:00"
    with pytest.raises(SettingsError, match="new_trades_from must be earlier than new_trades_until"):
        load_settings(_write(tmp_path, data))


def test_close_time_not_before_last_new_trade(tmp_path):
    data = _raw()
    data["hours"]["close_all_trades_at"] = "20:00"
    with pytest.raises(SettingsError, match="close_all_trades_at must not be earlier"):
        load_settings(_write(tmp_path, data))


def test_missing_file_is_named(tmp_path):
    with pytest.raises(SettingsError, match="Settings file not found"):
        load_settings(tmp_path / "nope.toml")


def test_broken_file_is_named(tmp_path):
    p = tmp_path / "settings.toml"
    p.write_text("[trade\nstop_loss_pips = 6\n")
    with pytest.raises(SettingsError, match="is not valid TOML"):
        load_settings(p)


def test_load_or_exit_stops_with_message(tmp_path):
    data = _raw()
    del data["trade"]["stop_loss_pips"]
    with pytest.raises(SystemExit) as e:
        load_or_exit(_write(tmp_path, data))
    assert str(e.value).startswith("AutoBot cannot start: ")
    assert "Missing setting [trade] stop_loss_pips." in str(e.value)


def test_bot_process_stops_with_clear_message(tmp_path):
    """Run the settings check as a real program with a bad file: it must exit
    with an error code and print the reason."""
    data = _raw()
    data["trade"]["stop_loss_pips"] = "six"
    bad = _write(tmp_path, data)
    r = subprocess.run(
        [sys.executable, "-m", "config"],
        cwd=ROOT, env={"AUTOBOT_SETTINGS": str(bad), "PATH": "/usr/bin:/bin"},
        capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 1
    assert "AutoBot cannot start" in r.stderr
    assert "Invalid setting [trade] stop_loss_pips: must be a whole number" in r.stderr
    assert "Settings OK" not in r.stdout


def test_bot_process_starts_with_good_settings():
    r = subprocess.run(
        [sys.executable, "-m", "config"],
        cwd=ROOT, env={"PATH": "/usr/bin:/bin"},
        capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0, r.stderr
    assert "Settings OK." in r.stdout
