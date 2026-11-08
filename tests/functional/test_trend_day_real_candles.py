"""Functional test for the trend-day check, using the REAL daily candles in the candle store
(stored candles are never overwritten, so the answer does not change). Reads the store only.

The check must flag exactly the 16 days of rank 1 in docs/research/trend_day_conditions_v2_20261108.md
(the owner's decision of 8 November 2026), every weekday from the store's first daily candle to
Friday 6 November 2026, each with its direction (a stretch above the monthly R2 is a trend day
downwards, below the monthly S2 upwards)."""

from datetime import date, timedelta

import pytest

from analyser.trend_day import check
from config.settings_loader import load_settings
from prices.store import CandleStore

SETTINGS = load_settings().for_pair("GBPUSD")

pytestmark = pytest.mark.skipif(not (SETTINGS.candles.folder / "1d").is_dir(),
                                reason="the real candle store is only on the server")

RESEARCH_RANK_1 = {
    date(2025, 1, 13): "up", date(2025, 1, 15): "up", date(2025, 1, 20): "up",
    date(2025, 3, 19): "down", date(2025, 3, 20): "down", date(2025, 4, 22): "down",
    date(2025, 12, 24): "down", date(2025, 12, 25): "down", date(2025, 12, 26): "down",
    date(2026, 1, 28): "down", date(2026, 1, 29): "down", date(2026, 1, 30): "down",
    date(2026, 9, 24): "up", date(2026, 9, 25): "up", date(2026, 9, 28): "up", date(2026, 9, 30): "up",
}


def test_the_check_flags_exactly_the_16_days_of_the_research():
    store = CandleStore(SETTINGS.candles.folder, SETTINGS.candles.compress_after_days)
    d, last, found = store.days("1d")[0], date(2026, 11, 6), {}
    while d <= last:
        r = check(SETTINGS, store, d)
        if r.direction:
            found[d] = r.direction
        d += timedelta(days=1)
    assert found == RESEARCH_RANK_1


def test_friday_30_january_2026_is_a_trend_day_downwards_with_its_reason():
    store = CandleStore(SETTINGS.candles.folder, SETTINGS.candles.compress_after_days)
    r = check(SETTINGS, store, date(2026, 1, 30))
    assert r.direction == "down" and str(r.open_price) == "13807.0"
    assert "monthly R2 13747" in r.reason and "daily RSI(14) 75.6 above 70" in r.reason
