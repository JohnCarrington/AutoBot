"""Functional test for check 6, the trend still going (owner, 16 November 2026; design 2.2), using the REAL candles in
the candle store (stored candles are never overwritten, so the answers do not change). Reads the store only.

  * Monday 16 November 2026: the EMA pullback sells of 10:50 and 14:57 are refused (the most: 2.7 and 3.4 pips below
    the previous swing low within the last 12 five-minute candles; 5 are needed).
  * Tuesday 10 November 2026: the breakout sell of 09:10 and the slow grind sells of 13:56 (+17.1) and 15:19 (+37.8)
    are still taken; the slow grind sell of 13:30 (-15) and the three EMA pullback buys of 05:01, 06:12, 07:21 (each
    -12) are refused.
Each is judged on the finished 5-minute candles before the entry's candle, as the strategy runner gives them."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from config.settings_loader import load_settings
from prices.store import CandleStore
from strategies.common import BREAKOUT, BUY, EMA_PULLBACK, SELL, SLOW_GRIND, still_going_reasons

UTC = timezone.utc
T = lambda *a: datetime(*a, tzinfo=UTC)   # noqa: E731   (UK time = UTC in November)
BASE = load_settings().for_pair("GBPUSD")


class _On:
    """The real settings (no .env read) with the switch TREND_STILL_GOING on."""
    switches = SimpleNamespace(trend_still_going=True)

    def __getattr__(self, name):
        return getattr(BASE, name)


ON = _On()

pytestmark = pytest.mark.skipif(not (BASE.candles.folder / "5m").is_dir(),
                                reason="the real candle store is only on the server")


def before(t):
    """The finished 5-minute candles before the candle in which t falls (12 hours of them)."""
    start = t.replace(minute=t.minute - t.minute % 5, second=0)
    st = CandleStore(BASE.candles.folder, BASE.candles.compress_after_days)
    return [c for c in st.read_range("5m", start - timedelta(hours=12), start) if c.end <= start]


@pytest.mark.parametrize("t,most", [(T(2026, 11, 16, 10, 50, 10), "2.7"), (T(2026, 11, 16, 14, 57, 56), "3.4")])
def test_todays_ema_pullback_sells_are_refused(t, most):
    (why,) = still_going_reasons(ON, EMA_PULLBACK, SELL, before(t))
    assert f"(the most: {most} pips below the swing low" in why


@pytest.mark.parametrize("strategy,t", [(BREAKOUT, T(2026, 11, 10, 9, 10, 19)), (SLOW_GRIND, T(2026, 11, 10, 13, 56, 31)),
                                        (SLOW_GRIND, T(2026, 11, 10, 15, 19, 23))])
def test_tuesday_10_novembers_trend_sells_are_still_taken(strategy, t):
    assert still_going_reasons(ON, strategy, SELL, before(t)) == []


@pytest.mark.parametrize("strategy,direction,t", [(SLOW_GRIND, SELL, T(2026, 11, 10, 13, 30, 2)),
                                                  (EMA_PULLBACK, BUY, T(2026, 11, 10, 5, 1, 31)),
                                                  (EMA_PULLBACK, BUY, T(2026, 11, 10, 6, 12, 3)),
                                                  (EMA_PULLBACK, BUY, T(2026, 11, 10, 7, 21, 3))])
def test_tuesday_10_novembers_other_trend_trades_are_refused(strategy, direction, t):
    assert still_going_reasons(ON, strategy, direction, before(t)) != []
