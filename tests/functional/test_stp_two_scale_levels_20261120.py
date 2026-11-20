"""Focused regression checks for the two time-scale STP level map."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

from planner.zones import today_extremes, recent_week_extremes

UTC = timezone.utc


def candle(start, hours, high, low):
    return SimpleNamespace(
        start=start, end=start + timedelta(hours=hours),
        sell_high=Decimal(high), sell_low=Decimal(low),
    )


def settings():
    return SimpleNamespace(chart=SimpleNamespace(price="sell"))


def test_today_levels_use_finished_five_minute_candles_only():
    day = datetime(2026, 11, 20, tzinfo=UTC)
    t = day + timedelta(minutes=15)
    snap = SimpleNamespace(
        day_start=day, as_of=t,
        fives=[
            candle(day, 1 / 12, "1.3110", "1.3090"),
            candle(day + timedelta(minutes=5), 1 / 12, "1.3120", "1.3095"),
            candle(day + timedelta(minutes=10), 1 / 12, "1.3500", "1.3000"),
        ],
    )
    # At 10 minutes the third bar has not closed; do not leak its extrema.
    snap.as_of = day + timedelta(minutes=10)
    levels = today_extremes(settings(), snap)
    assert {lv.name: lv.price for lv in levels} == {
        "today high (so far)": Decimal("1.3120"),
        "today low (so far)": Decimal("1.3090"),
    }
    assert all(not lv.fixed for lv in levels)
    snap.as_of = t
    assert {lv.name: lv.price for lv in today_extremes(settings(), snap)}[
        "today high (so far)"
    ] == Decimal("1.3500")


def test_today_extremes_reset_at_day_boundary():
    day = datetime(2026, 11, 20, tzinfo=UTC)
    snap = SimpleNamespace(
        day_start=day, as_of=day + timedelta(minutes=10),
        fives=[candle(day - timedelta(minutes=5), 1 / 12, "1.4000", "1.2000"),
               candle(day, 1 / 12, "1.3110", "1.3090")],
    )
    assert {lv.price for lv in today_extremes(settings(), snap)} == {
        Decimal("1.3110"), Decimal("1.3090")
    }


def test_multiple_previous_weeks_and_no_running_week():
    monday = datetime(2026, 11, 16, tzinfo=UTC)
    weekly = [candle(monday - timedelta(weeks=i), 24 * 5,
                     str(Decimal("1.31") + Decimal(i) / 100),
                     str(Decimal("1.29") - Decimal(i) / 100))
              for i in (4, 3, 2, 1)]
    weekly.append(candle(monday, 24 * 5, "1.5000", "1.1000"))  # incomplete
    snap = SimpleNamespace(as_of=monday + timedelta(days=4),
                           w1=SimpleNamespace(candles=weekly))
    levels = recent_week_extremes(settings(), snap)
    assert len(levels) == 6  # three older weeks, high and low each
    assert all(lv.daily_or_weekly and lv.fixed for lv in levels)
    assert not any(lv.price in (Decimal("1.5000"), Decimal("1.1000")) for lv in levels)
