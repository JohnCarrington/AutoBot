"""Technical tests: every setting loads with the right value, and a missing or
invalid setting stops the bot with a clear message."""

import subprocess
import sys
import tomllib
from datetime import time
from pathlib import Path
from zoneinfo import ZoneInfo

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
    "chart": {"price": "sell"},
    "levels": {
        "line_up_within_pips": 5,
        "turning_levels_lookback_weeks": 2,
        "folder": Path("/opt/autobot/data/levels"),
        "level_decimals": 1,
        "round_number_every_pips": 50,
        "round_numbers_within_pips": 150,
        "sessions_time_zone": "UTC",
        "london_session_from": time(7, 0),
        "london_session_until": time(12, 0),
        "new_york_session_from": time(12, 0),
        "new_york_session_until": time(21, 0),
        "turning_candles_each_side": 3,
        "turning_min_move_pips": 20,
        "turning_move_within_candles": 6,
    },
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
    "range_trade": {"close_percent_at_opposite_band": 50, "rejection_candle_within_candles": 1,
                    "trigger_within_candles": 1},
    "indicators": {"bollinger_periods": 20, "bollinger_std_devs": 2},
    "rejection": {"candle_timeframe": "5m", "near_level_within_pips": 3, "max_spread_pips": 3},
    "market": {"epic": "CS.D.GBPUSD.TODAY.IP", "points_per_pip": 1},
    "market_hours": {
        "opens_day": 6,              # Sunday (Monday is 0)
        "opens_at": time(21, 0),
        "opens_time_zone": ZoneInfo("Europe/London"),
        "closes_day": 4,             # Friday
        "closes_at": time(17, 0),
        "closes_time_zone": ZoneInfo("America/New_York"),
    },
    "stream": {
        "reconnect_waits_seconds": (5, 10, 20, 40, 80, 160, 300),
        "no_prices_warning_seconds": 120,
        "healthy_after_minutes": 60,
        "status_log_minutes": 60,
    },
    "candles": {
        "folder": Path("/opt/autobot/data/candles"),
        "hour_starts_at_minute": 0,
        "four_hour_starts_at": time(0, 0),
        "day_starts_at": time(0, 0),
        "week_starts_day": 6,        # Sunday
        "join_opening_stretch": False,
        "wait_for_late_candle_seconds": 300,
        "compress_after_days": 30,
    },
    "housekeeping": {
        "log_folder": Path("/opt/autobot/logs"),
        "log_max_file_mb": 10,
        "log_new_file_every_hours": 24,
        "log_keep_files": 20,
        "log_max_age_days": 30,
        "min_free_disk_mb": 2048,
    },
    "history": {
        "folder": Path("/opt/autobot/data/history"),
        "weekly_budget_points": 4000,
        "min_ig_allowance_remaining": 2000,
        "max_points_per_request": 500,
        "min_block_hours": 24,
    },
    "ig": {
        "demo_base_url": "https://demo-api.ig.com/gateway/deal",
        "slowed_down_waits_seconds": (60, 90, 120, 180),
        "request_timeout_seconds": 30,
    },
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
    ("levels", "folder", "data/levels", "must be a full folder path"),
    ("chart", "price", "mid", "must be one of 'sell', 'buy'"),
    ("levels", "sessions_time_zone", "Europe/London", "must be 'UTC'"),
    ("levels", "london_session_from", "7am", 'UTC time written "HH:MM"'),
    ("levels", "turning_candles_each_side", 0, "must be between"),
    ("levels", "turning_min_move_pips", 0, "must be between"),
    ("levels", "round_number_every_pips", 0, "must be between"),
    ("market", "points_per_pip", 0, "must be between"),
    ("reversal_watch", "times", ["11:00", "10:00"], "in order with no repeats"),
    ("reversal_watch", "times", [], "non-empty list"),
    ("reversal_watch", "minutes_before", 500, "must be between"),
    ("bounce", "reversal_candle_within_candles_of_pierce", 0, "must be between"),
    ("slow_grind", "min_pause_candles", 0, "must be between"),
    ("ema_pullback", "setup_expires_after_minutes", 0, "must be between"),
    ("possible_reversal", "min_trend_move_pips", 0, "must be between"),
    ("range_trade", "close_percent_at_opposite_band", 150, "must be between"),
    ("range_trade", "trigger_within_candles", 0, "must be between"),
    ("indicators", "bollinger_periods", 1, "must be between"),
    ("indicators", "bollinger_std_devs", 2.5, "must be a whole number"),
    ("rejection", "candle_timeframe", "1m", "must be one of"),
    ("rejection", "near_level_within_pips", -1, "must be between"),
    ("rejection", "max_spread_pips", 0, "must be between"),
    ("ig", "demo_base_url", "https://api.ig.com/gateway/deal", "must be 'https://demo-api.ig.com/gateway/deal'"),
    ("ig", "slowed_down_waits_seconds", [], "non-empty list"),
    ("ig", "slowed_down_waits_seconds", [60, 0], "must be between"),
    ("ig", "request_timeout_seconds", 0, "must be between"),
    ("market", "epic", "GBPUSD", "must be an IG epic"),
    ("market_hours", "opens_day", "Sun", "must be a day name"),
    ("market_hours", "closes_at", "21:59", "5-minute mark"),
    ("market_hours", "closes_time_zone", "UTC", "must be 'Europe/London' or 'America/New_York'"),
    ("market_hours", "opens_time_zone", "Asia/Tokyo", "must be 'Europe/London' or 'America/New_York'"),
    ("stream", "reconnect_waits_seconds", [], "non-empty list"),
    ("stream", "no_prices_warning_seconds", 0, "must be between"),
    ("candles", "folder", "data/candles", "full folder path"),
    ("candles", "hour_starts_at_minute", 7, "multiple of 5"),
    ("candles", "day_starts_at", "22:03", "5-minute mark"),
    ("candles", "week_starts_day", "Funday", "must be a day name"),
    ("candles", "compress_after_days", 0, "must be between"),
    ("housekeeping", "log_max_file_mb", 0, "must be between"),
    ("housekeeping", "log_keep_files", 0, "must be between"),
    ("housekeeping", "min_free_disk_mb", 0, "must be between"),
    ("history", "weekly_budget_points", 9000, "must be between"),
    ("history", "max_points_per_request", 0, "must be between"),
    ("history", "min_block_hours", 0, "must be between"),
    ("history", "folder", "history", "full folder path"),
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


@pytest.mark.parametrize("section,key,value,message", [
    ("stream", "reconnect_waits_seconds", [60, 5], "must go up"),
    ("candles", "four_hour_starts_at", "01:00", "must line up with day_starts_at"),
    ("candles", "day_starts_at", "00:05", "must start on an hour boundary"),
    ("market_hours", "closes_day", "Sunday", "must be different days"),
    ("history", "weekly_budget_points", 400, "must not be bigger than weekly_budget_points"),
    ("levels", "london_session_until", "07:00", "london_session_from must be earlier than london_session_until"),
    ("levels", "new_york_session_from", "21:30", "new_york_session_from must be earlier than new_york_session_until"),
])
def test_candle_and_stream_settings_must_fit_together(tmp_path, section, key, value, message):
    data = _raw()
    data[section][key] = value
    with pytest.raises(SettingsError, match=message):
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
    # Times print as HH:MM and lists print plainly, as written in settings.toml.
    assert "  [hours] new_trades_from = 06:00\n" in r.stdout
    assert "  [hours] new_trades_until = 20:30\n" in r.stdout
    assert "  [hours] close_all_trades_at = 20:30\n" in r.stdout
    assert ("  [reversal_watch] times = 10:00, 11:00, 13:00, 14:00, 16:00, 17:00\n"
            in r.stdout)
    assert "  [prices] candle_timeframes = tick, 5m, 1h, 4h, 1d, 1w\n" in r.stdout
    assert "datetime" not in r.stdout
