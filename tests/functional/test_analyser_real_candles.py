"""Functional tests for the analyser's indicators and direction rule, using the
REAL stored candles (/opt/autobot/data/candles). Stored candles are never
overwritten, so these results do not change. Reads the store only; never
contacts IG. Sell (bid) prices, midnight-to-midnight UK days, as on the
owner's IG chart. Prices are in IG's points (13450 means 1.3450).

  a. design section 2.3: on Friday 6 November 2026 at 13:00 price was below the
     pivot and the 100 EMA, so the direction is SELL SIDE (no buy at 13:00).
  b. the 5-minute 100 EMA, the daily pivot and the direction at 06:00, 09:00,
     13:00 and 16:00 on Friday 6 November, printed for checking against the chart.
"""

from datetime import datetime, timezone
from decimal import Decimal as D

import pytest

from analyser.direction import SELL_SIDE
from analyser.report import analyse
from config.settings_loader import load_settings
from prices.store import CandleStore

SETTINGS = load_settings()
UTC = timezone.utc

pytestmark = pytest.mark.skipif(not (SETTINGS.candles.folder / "5m").is_dir(),
                                reason="the real candle store is only on the server")

# Friday 6 November is GMT, so UK time = UTC.
TIMES = [datetime(2026, 11, 6, h, 0, tzinfo=UTC) for h in (6, 9, 13, 16)]


@pytest.fixture(scope="module")
def store():
    return CandleStore(SETTINGS.candles.folder, SETTINGS.candles.compress_after_days)


def test_a_at_13_00_on_friday_6_november_the_direction_is_sell_side(store):
    r = analyse(SETTINGS, store, datetime(2026, 11, 6, 13, 0, tzinfo=UTC))
    d = r.direction
    print(f"\n13:00 Fri 06 Nov: {d.side} ({d.reason}); price from {d.price_from}")
    assert d.side == SELL_SIDE and not d.allows_buy
    assert d.price < d.pivot and d.price < d.ema
    assert d.ema_ready                                  # the 5-minute 100 EMA has warmed up
    assert d.pivot == D("13463.8")                      # Friday's pivot (test_levels_real_candles)


def test_b_ema_pivot_and_direction_through_friday_6_november(store):
    print("\nFri 06 Nov (sell prices; price = close of the 5-minute candle just finished)")
    print(f"  {'time':<6} {'price':>8} {'5m 100 EMA':>11} {'pivot':>8}  direction")
    rows = []
    for t in TIMES:
        d = analyse(SETTINGS, store, t).direction
        rows.append(d)
        print(f"  {t:%H:%M}  {d.price:>8} {d.ema.quantize(D('0.1')):>11} {d.pivot:>8}  {d.side}"
              f"   (price = {d.price_from})")
    assert all(d.ema_ready and d.pivot == D("13463.8") for d in rows)
    # Section 12: slow grind down from midnight, through S1 and S2, to S3: sell side all day.
    assert [d.side for d in rows] == [SELL_SIDE] * 4
