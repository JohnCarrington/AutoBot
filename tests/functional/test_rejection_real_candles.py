"""Functional tests for the shared rejection part, using the REAL stored
candles (/opt/autobot/data/candles). Reads the store only; never contacts IG.

Each test replays a stretch of 5 November 2026 (sell prices, as on the
owner's chart), prints every event with its time and price, and checks what
docs/DESIGN.md says happened:
  a. section 2.5 / 12: "the rejection at the daily pivot just before midnight
     on 5 November", starting the downtrend into 6 November
  b. section 5 / 12: "the fall from 07:00 stopped at about 1.3446 to 1.3450 ...
     and price shot back up at 12:00"
"""

from datetime import datetime, timezone
from decimal import Decimal as D

import pytest

from config.settings_loader import load_settings
from prices.model import plain, uk_short
from prices.store import CandleStore
from rejection.replay import replay
from rejection.watch import BUY, SELL, TRIGGER

SETTINGS = load_settings()
UTC = timezone.utc

pytestmark = pytest.mark.skipif(not (SETTINGS.candles.folder / "5m").is_dir(),
                                reason="the real candle store is only on the server")


@pytest.fixture(scope="module")
def store():
    return CandleStore(SETTINGS.candles.folder, SETTINGS.candles.compress_after_days)


def show(w, title):
    print(f"\n{title}")
    for e in w.events:
        print("  " + e.describe())


def trigger_time(w, st):
    return next((e.time for e in w.events if e.setup == st.id and e.kind == TRIGGER), None)


def test_a_the_rejection_at_the_daily_pivot_just_before_midnight_on_5_november(store):
    w = replay(SETTINGS, store, datetime(2026, 11, 5, 21, 0, tzinfo=UTC), datetime(2026, 11, 6, 0, 30, tzinfo=UTC))
    show(w, "Every rejection event, Thu 05 Nov 21:00 to Fri 06 Nov 00:30 UK (sell prices):")
    at_pivot = [st for st in w.setups if st.direction == SELL and any(p["what"] == "pivot" for p in st.pierced)
                and datetime(2026, 11, 5, 22, 0, tzinfo=UTC) <= st.pierce.start < datetime(2026, 11, 6, 0, 30, tzinfo=UTC)]
    print("Sell setups that pierced the daily pivot: "
          + (", ".join(f"#{st.id} {st.version} {st.status}" for st in at_pivot) or "none"))
    assert any(st.status == "triggered" for st in at_pivot), \
        "no sell rejection that pierced the daily pivot and triggered, between 22:00 and 00:30"


def test_b_the_turn_at_1_3446_to_1_3450_around_12_00_on_5_november(store):
    w = replay(SETTINGS, store, datetime(2026, 11, 5, 11, 0, tzinfo=UTC), datetime(2026, 11, 5, 12, 30, tzinfo=UTC))
    show(w, "Every rejection event, Thu 05 Nov 11:00 to 12:30 UK (sell prices):")
    turns = [st for st in w.setups if st.direction == BUY and D(13446) <= st.pierce.sell_low <= D(13450)]
    for st in turns:
        print(f"Buy setup #{st.id} ({st.version}): pierce {uk_short(st.pierce.start)} low {plain(st.pierce.sell_low)}; "
              f"{st.status}" + (f" at {uk_short(trigger_time(w, st))}" if trigger_time(w, st) else ""))
    triggered = [st for st in turns if st.status == "triggered"
                 and datetime(2026, 11, 5, 11, 45, tzinfo=UTC) <= trigger_time(w, st) <= datetime(2026, 11, 5, 12, 15, tzinfo=UTC)]
    assert triggered, "no buy rejection from 1.3446-1.3450 that triggered between 11:45 and 12:15"
