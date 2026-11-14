"""Functional test for the hourly read (analyser/hourly_read.py; owner, 14 November 2026), using the REAL hourly
candles in the candle store (stored candles are never overwritten, so the answer does not change). Reads the store
only. Friday 13 November 2026 from 08:40 to 13:00 UK was a textbook range (the owner's example): it must read as
ranging, with the hourly range the 5-minute had to break."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal as D

import pytest

from analyser.hourly_read import RALLY, RANGING, SELL_OFF, HourlyReader
from analyser.indicators import last_candles
from config.settings_loader import load_settings
from prices.store import CandleStore

SETTINGS = load_settings().for_pair("GBPUSD")
UTC = timezone.utc
T = lambda *a: datetime(*a, tzinfo=UTC)   # noqa: E731   (UK time = UTC in November)

pytestmark = pytest.mark.skipif(not (SETTINGS.candles.folder / "1h").is_dir(),
                                reason="the real candle store is only on the server")


def read(t):
    store = CandleStore(SETTINGS.candles.folder, SETTINGS.candles.compress_after_days)
    return HourlyReader(SETTINGS, last_candles(store, "1h", t, SETTINGS.hourly_read.history_candles)).at(t)


def test_friday_13_november_08_40_to_13_00_is_ranging():
    t = T(2026, 11, 13, 8, 40)
    while t <= T(2026, 11, 13, 13, 0):
        r = read(t)
        assert r.state == RANGING, (t, r.why)
        assert D("13217.4") <= r.low <= D("13222.0") and D("13240.0") <= r.high <= D("13251.0"), (t, r.low, r.high)
        t += timedelta(minutes=20)
    assert read(T(2026, 11, 13, 4, 0)).state == RANGING        # from the 03:00 candle's close
    assert read(T(2026, 11, 13, 3, 59)).state == SELL_OFF      # Thursday's fall below 1.3249 and 1.3245


def test_the_friday_afternoon_drop_and_the_trend_days():
    r = read(T(2026, 11, 13, 17, 0))                           # the 16:00 candle closed 6.1 pips below 13217.4
    assert r.state == SELL_OFF and "6.1 pips below the low 13217.4" in r.why
    assert read(T(2026, 11, 6, 9, 0)).state == SELL_OFF        # Friday 6 November
    assert read(T(2026, 11, 9, 12, 0)).state == RALLY          # Monday 9 November
