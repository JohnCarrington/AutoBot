"""The structural-history correction (20 November 2026).

Daily swings older than planner.daily_swing_lookback_weeks (48, unchanged) are now also kept as levels, as
"historical daily swing low/high", back to planner.historical_daily_swing_lookback_weeks. They are only used when they
were confirmed by the assessment time, never decide the direction, and leave the Major-destination and
already-reached rules unchanged. Together with 9210ca5 (zones no longer clipped to the 150-pip window) this lets
the planner see support below a fresh 48-week low, which is what stopped every recommendation from 19 November 16:00.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D

import pytest

from planner.structure import Swing
from planner.zones import HTF_STRUCTURE, historical_swing_levels, swing_levels
from tests.functional.test_planner_scenarios import S
from tests.planner_helpers import Over, section

UTC = timezone.utc
AS_OF = datetime(2026, 11, 20, 8, 0, 4, tzinfo=UTC)


def sw(price, candle, known=None, kind="low", tf="1d"):
    return Swing(kind, D(str(price)), tf, candle, known or candle + timedelta(days=4), 0)


OLD = sw(13084.1, datetime(2025, 11, 12, tzinfo=UTC))             # 53 weeks before AS_OF
RECENT = sw(13135.6, datetime(2026, 10, 13, tzinfo=UTC))
ANCIENT = sw(12099.0, datetime(2023, 1, 13, tzinfo=UTC))           # older than 156 weeks


def test_a_daily_swing_older_than_48_weeks_becomes_a_historical_daily_level():
    out = historical_swing_levels([OLD, RECENT, ANCIENT], AS_OF, 48, 156)
    assert [(lv.price, lv.name) for lv in out] == [(D("13084.1"), "historical daily swing low")]
    lv = out[0]
    assert lv.family == HTF_STRUCTURE and lv.daily_or_weekly and lv.fixed and lv.kind == "daily swing"
    assert lv.origin_utc == OLD.candle_utc


def test_recent_daily_swings_are_unchanged_and_never_counted_twice():
    recent = swing_levels([OLD, RECENT], AS_OF, 48)
    hist = historical_swing_levels([OLD, RECENT], AS_OF, 48, 156)
    assert [lv.price for lv in recent] == [D("13135.6")] and [lv.price for lv in hist] == [D("13084.1")]


def test_only_swings_confirmed_by_the_assessment_time_are_used():
    unknown_yet = sw(13050, datetime(2025, 10, 1, tzinfo=UTC), known=AS_OF + timedelta(seconds=1))
    assert historical_swing_levels([unknown_yet], AS_OF, 48, 156) == []
    known = sw(13050, datetime(2025, 10, 1, tzinfo=UTC), known=AS_OF)
    assert len(historical_swing_levels([known], AS_OF, 48, 156)) == 1


def test_switched_off_or_not_beyond_the_recent_window_gives_nothing():
    assert historical_swing_levels([OLD], AS_OF, 48, 0) == []
    assert historical_swing_levels([OLD], AS_OF, 48, 48) == []
    assert historical_swing_levels([sw(13000, OLD.candle_utc, tf="4h")], AS_OF, 48, 156) == []   # daily swings only


# ---- the live failure of 20 November 2026, on the real store (server only; read only) -----------------------------

def _real_store():
    from prices.store import CandleStore
    if not (S.candles.folder / "1d").is_dir():
        pytest.skip("the real candle store is only on the server")
    return CandleStore(S.candles.folder, S.candles.compress_after_days)


def test_real_20_november_0800_without_history_there_is_no_major_support_and_with_it_a_plan():
    from planner.assess import plan_at
    st = _real_store()
    off = Over(S, planner=section(S.planner, historical_daily_swing_lookback_weeks=0))
    before = plan_at(off, st, AS_OF, calendar=[]).as_dict()
    after = plan_at(S, st, AS_OF, calendar=[]).as_dict()
    # the direction and condition are untouched by the extra history
    assert (before["dominant_direction"], before["condition"]) == (after["dominant_direction"], after["condition"])
    assert before["dominant_direction"] == "BEARISH"
    assert before["no_recommendation"].startswith("no Major support zone below the entry zone")
    assert after["no_recommendation"] is None and after["trade"] == "SELL"
    prim = after["destinations"]["primary"]["zone"]
    assert prim["class"] == "Major" and any("historical daily swing low 13084.1" in x for x in prim["levels"])
    assert D(prim["high"]) < D(after["entry_zone"]["low"])                              # beyond the entry zone
    assert after["invalidation"]["zone_break_close"] and after["invalidation"]["structure_break_close"]
