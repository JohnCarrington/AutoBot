"""Functional test for the news part, on the REAL economic calendar kept on
disk (/opt/autobot/data/news/calendar.json, fetched from Finnhub). Contacts
nobody.

  On Thursday 5 November 2026 the 12:00 UK Bank of England rate decision is big
  news, so no new trades from 11:45 to 12:30 (design section 12).
"""

from datetime import datetime, timezone

import pytest

from config.settings_loader import load_settings
from news.calendar import BIG, big_news_windows, currency_of, events, no_new_trades, tier_of
from news.finnhub import store_path

SETTINGS = load_settings()
UTC = timezone.utc

pytestmark = pytest.mark.skipif(not store_path(SETTINGS).exists(),
                                reason="the economic calendar is only on the server, once fetched")


def T(h, mi, s=0):
    return datetime(2026, 11, 5, h, mi, s, tzinfo=UTC)          # GMT on 5 November: UK time = UTC


def test_the_boe_rate_decision_on_5_november_is_big_news_no_new_trades_11_45_to_12_30():
    boe = [e for e in events(SETTINGS) if e["time_utc"].startswith("2026-11-05")
           and currency_of(SETTINGS, e["country"]) == "GBP" and "BoE" in e["event"]]
    print("\nGBP Bank of England releases on 5 November in the calendar:")
    for e in boe:
        print(f"  {e['time_utc']}  {e['event']}  ({tier_of(SETTINGS, 'GBP', e['event'])}; estimate {e['estimate']}, "
              f"previous {e['prev']}, actual {e['actual']})")
    decision = [e for e in boe if e["event"] == "BoE Interest Rate Decision"]
    assert decision and decision[0]["time_utc"] == "2026-11-05T12:00:00Z"
    assert tier_of(SETTINGS, "GBP", "BoE Interest Rate Decision") == BIG
    windows = [w for w in big_news_windows(SETTINGS, "GBPUSD", T(0, 0), T(23, 59))
               if w.event == "BoE Interest Rate Decision"]
    (w,) = windows
    print(f"  no new trades {w.no_new_trades_from:%H:%M} to {w.no_new_trades_until:%H:%M}; open trades closed "
          f"{w.close_open_trades_at:%H:%M}; expected {w.direction} ({w.direction_reason})")
    assert (w.no_new_trades_from, w.no_new_trades_until) == (T(11, 45), T(12, 30))
    assert not no_new_trades(SETTINGS, "GBPUSD", T(11, 44, 59))
    assert any(x.event == "BoE Interest Rate Decision" for x in no_new_trades(SETTINGS, "GBPUSD", T(11, 45)))
    assert any(x.event == "BoE Interest Rate Decision" for x in no_new_trades(SETTINGS, "GBPUSD", T(12, 29, 59)))
    assert not any(x.event == "BoE Interest Rate Decision" for x in no_new_trades(SETTINGS, "GBPUSD", T(12, 30)))
