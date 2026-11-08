"""Technical tests for the trend-day check (design 2.4; owner, 8 November 2026), with made-up
levels, opens and RSI values. Reads nothing; contacts nobody."""

from datetime import date
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from analyser import trend_day as td
from config.settings_loader import load_settings

S = load_settings().for_pair("GBPUSD")
WED = date(2026, 11, 4)
LEVELS = {"R2": D("13500.0"), "S2": D("13300.0"), "pivot": D("13400.0")}


def run(monkeypatch, open_price, rsi_value, levels=LEVELS, day=WED, settings=S):
    monkeypatch.setattr(td, "day_open", lambda s, store, d: None if open_price is None else D(str(open_price)))
    monkeypatch.setattr(td, "monthly_levels", lambda s, store, d: levels)
    candle = SimpleNamespace(start="prev")
    monkeypatch.setattr(td, "last_candles", lambda store, tf, t, n: [candle])
    monkeypatch.setattr(td, "rsi", lambda candles, side, periods: {} if rsi_value is None else {"prev": D(str(rsi_value))})
    return td.check(settings, None, day)


@pytest.mark.parametrize("open_price,rsi,want", [
    (13500.0, 70.1, "down"),            # at R2 counts
    (13550.0, 85, "down"),
    (13499.9, 85, None),                # just below R2
    (13550.0, 70, None),                # RSI exactly 70 is not above it
    (13300.0, 29.9, "up"),              # at S2 counts
    (13250.0, 10, "up"),
    (13300.1, 10, None),
    (13250.0, 30, None),
    (13550.0, 20, None),                # above R2 but oversold: neither
    (13250.0, 80, None),
])
def test_trend_day_down_above_monthly_r2_and_rsi_over_70_up_below_s2_and_under_30(monkeypatch, open_price, rsi, want):
    r = run(monkeypatch, open_price, rsi)
    assert r.direction == want
    if want == "down":
        assert r.level == D("13500.0") and "trend day downwards" in r.reason and "monthly R2" in r.reason
    if want == "up":
        assert r.level == D("13300.0") and "trend day upwards" in r.reason and "monthly S2" in r.reason


def test_the_levels_and_rsi_are_settings(monkeypatch):
    class Over:
        def __init__(self, base, **v):
            self.base = base
            self.trend_day = SimpleNamespace(**({k: x for k, x in vars(base.trend_day).items() if not k.startswith("_")} | v))

        def __getattr__(self, name):
            return getattr(self.base, name)
    levels = dict(LEVELS, R1=D("13450.0"), S1=D("13350.0"))
    s = Over(S, level_above="R1", level_below="S1", rsi_above=60, rsi_below=40)
    assert run(monkeypatch, 13460.0, 61, levels, settings=s).direction == "down"
    assert run(monkeypatch, 13340.0, 39, levels, settings=s).direction == "up"
    assert run(monkeypatch, 13460.0, 61, levels).direction is None              # the owner's R2 / 70: not


@pytest.mark.parametrize("day", [date(2026, 11, 7), date(2026, 11, 8)])
def test_saturday_and_sunday_are_never_trend_days(monkeypatch, day):
    r = run(monkeypatch, 13600.0, 90, day=day)
    assert r.direction is None and "Saturday or Sunday" in r.reason


def test_no_answer_without_the_open_the_month_or_the_rsi(monkeypatch):
    assert "no 00:00 UK open" in run(monkeypatch, None, 90).reason
    r = run(monkeypatch, 13600.0, 90, levels=None)
    assert r.direction is None and "previous month is not complete" in r.reason
    r = run(monkeypatch, 13600.0, None)
    assert r.direction is None and "not enough daily candles" in r.reason


def test_the_owners_settings():
    t = S.trend_day
    assert (t.level_above, t.level_below, t.rsi_periods, t.rsi_above, t.rsi_below) == ("R2", "S2", 14, 70, 30)
