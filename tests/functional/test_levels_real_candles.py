"""Functional tests for the levels, using the REAL candles in the candle store
(/opt/autobot/data/candles). Stored candles are never overwritten, so these
results do not change. Reads the store only; never contacts IG.

Each test works out the levels as they stood at a fixed time, so it gives the
same answer whenever it runs. "About" a price means within 2 pips of it.
Prices are in IG's points (13450 means 1.3450). Every level uses the chart
price: the SELL (bid) price, midnight to midnight UK, as on the owner's IG chart.
"""

from datetime import datetime, timezone
from decimal import Decimal as D

import pytest

from config.settings_loader import load_settings
from levels.current import build
from levels.rules import PIVOT, R1, R2, R3, ROUND_NUMBER, S1, S2, S3
from prices.model import UK, plain, uk_short
from prices.store import CandleStore

SETTINGS = load_settings()
UTC = timezone.utc
ABOUT_PIPS = D(2)

pytestmark = pytest.mark.skipif(not (SETTINGS.candles.folder / "1d").is_dir(),
                                reason="the real candle store is only on the server")


@pytest.fixture(scope="module")
def store():
    return CandleStore(SETTINGS.candles.folder, SETTINGS.candles.compress_after_days)


def about(price, target):
    return abs(price - D(str(target))) <= ABOUT_PIPS * SETTINGS.market.points_per_pip


def test_a_friday_6_november_pivots_from_thursday_5_novembers_daily_candle(store):
    ll = build(SETTINGS, store, datetime(2026, 11, 6, 0, 5, tzinfo=UTC))
    thu = ll.previous_day
    assert thu.start == datetime(2026, 11, 5, 0, 0, tzinfo=UTC)          # Thu 05 Nov 00:00 UK
    assert ll.side == "sell"
    assert (thu.sell_high, thu.sell_low, thu.sell_close) == (D("13500.4"), D("13435.7"), D("13455.2"))
    piv = {lv.type: lv.price for lv in ll.levels if lv.type in (PIVOT, R1, R2, R3, S1, S2, S3)}
    print(f"\nPivots for Fri 06 Nov from the daily candle {uk_short(thu.start)} "
          f"(sell H {plain(thu.sell_high)} L {plain(thu.sell_low)} C {plain(thu.sell_close)}):")
    for t in (R3, R2, R1, PIVOT, S1, S2, S3):
        print(f"  {t:<6} {plain(piv[t])}   (1.{plain(piv[t]).replace('.', '')[1:]})")
    # The owner's IG chart shows P 13463.4 and S2 13398.3 for this day. The stored
    # candles (which match IG's own daily candle on all 8 prices) give 13463.8 and
    # 13399.1: a difference not yet explained (docs/LEVELS.md).
    assert piv == {R3: D("13556.5"), R2: D("13528.5"), R1: D("13491.8"), PIVOT: D("13463.8"),
                   S1: D("13427.1"), S2: D("13399.1"), S3: D("13362.4")}


def test_b_the_hourly_low_at_about_1_3380_from_30_october_is_a_turning_level(store):
    ll = build(SETTINGS, store, datetime(2026, 11, 6, 21, 0, tzinfo=UTC))
    near = [lv for lv in ll.of_type("turning_low") if about(lv.price, 13380)]
    print("\nTurning lows within 2 pips of 13380:")
    for lv in near:
        print(f"  {plain(lv.price)}  {lv.source}  (group {lv.group})")
    on_30_oct = [lv for lv in near if lv.candle_utc.astimezone(UK).date().isoformat() == "2026-10-30"]
    assert on_30_oct, "no turning low at about 13380 from an hourly candle on 30 October"


def test_c_on_thursday_5_november_the_fall_stopped_at_1_3450_next_to_an_earlier_level(store):
    # docs/DESIGN.md, section 5: "on 5 November 2026 the fall from 07:00 stopped at
    # about 1.3446 to 1.3450, a round number next to an earlier level, and price
    # shot back up at 12:00." The levels as they stood at 12:00 UTC on Thursday.
    at = datetime(2026, 11, 5, 12, 0, tzinfo=UTC)
    ll = build(SETTINGS, store, at)
    fall = store.read_range("5m", datetime(2026, 11, 5, 7, 0, tzinfo=UTC), at)
    stop = min(fall, key=lambda c: c.sell_low)              # where the fall from 07:00 stopped
    r = [lv for lv in ll.of_type(ROUND_NUMBER) if lv.price == 13450]
    assert r, "13450 is not a round number level on Thursday"
    group = ll.group_of(r[0])
    earlier = [m for m in group["members"] if m.type in ("turning_high", "turning_low")
               and m.candle_utc < ll.day_start and D(13446) <= m.price <= D(13450)]
    detail = "; ".join(f"{m.type} {plain(m.price)}" for m in group["members"])
    print(f"\nThe fall from 07:00 stopped at {uk_short(stop.start)}: sell low {plain(stop.sell_low)}")
    print(f"Thursday's group holding 13450 (G{group['group']}), {plain(group['low'])}-{plain(group['high'])}: {detail}")
    for m in earlier:
        print(f"  earlier level: {m.type} {plain(m.price)}  [{m.source}]")
    assert D(13446) <= stop.sell_low <= D(13450)                    # stopped at about 1.3446 to 1.3450
    assert earlier, "no earlier level between 13446 and 13450 in the group holding 13450"
    assert group["low"] <= stop.sell_low <= group["high"]          # the stop is in that same group
    assert group["important"] and group["lined_up"]
