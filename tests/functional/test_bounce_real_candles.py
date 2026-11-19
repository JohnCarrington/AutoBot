"""Functional test for the Bollinger bounce off the hourly band (design 3.3; owner, 15 November 2026), using the REAL
candles in the candle store (stored candles are never overwritten, so the answers do not change). Reads the store
only; contacts nobody.

  * The bot's hourly chart (prices/hourly_chart.py), built from the stored IG 5-minute candles, equals IG's own
    hourly candles wherever both exist (25 October to 6 November 2026, from the long history fill's holding folder).
  * Friday 13 November 2026, 12:00 to 17:00 UK: the hourly candles and bands the owner checked against his IG chart.
  * The owner's example: the sell after the 14:50 pierce. Rejection candle 14:50 (high 13250.9, 6.9 pips above the
    forming hour's upper band 13244.0, red), confirmation 15:00 (close 13242.4 below the low 13243.9), sell at the
    15:05 open 13242.3, stop 13254.3; the trail starts at 15:25 and the stop at 13224.4 is reached at 16:20: +17.9.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from config.settings_loader import load_settings
from prices.hourly_chart import HourlyChart
from prices.store import CandleStore
from strategies.common import BOLLINGER_BOUNCE, SELL
from trade_manager.manager import STOPPED_BY_IG, Bar, TradeManager, plan

UTC = timezone.utc
T = lambda *a: datetime(*a, tzinfo=UTC)   # noqa: E731   (UK time = UTC in November)
BASE = load_settings().for_pair("GBPUSD")

pytestmark = pytest.mark.skipif(not (BASE.candles.folder / "5m").is_dir(),
                                reason="the real candle store is only on the server")


def store():
    return CandleStore(BASE.candles.folder, BASE.candles.compress_after_days)


def chart_over(start, end):
    ch = HourlyChart(BASE)
    for c in store().read_range("5m", start, end):
        ch.add(c)
    return ch


def test_the_hourly_chart_equals_igs_own_hourly_candles():
    ig_folder = BASE.candles.folder / "ig_history"
    if not (ig_folder / "1h").is_dir():
        pytest.skip("IG's own hourly candles are only on the server")
    ig = {c.start: c for c in CandleStore(ig_folder, BASE.candles.compress_after_days)
          .read_range("1h", T(2026, 10, 25, 21), T(2026, 11, 6, 22))}
    ch = HourlyChart(BASE)
    compared = 0
    for c in store().read_range("5m", T(2026, 10, 25, 21), T(2026, 11, 6, 22)):
        done = ch.hours[-1] if ch.hours else None
        ch.add(c)
        if done is None or ch.hours[-1].start == done.start or done.start not in ig:
            continue
        i = ig[done.start]                                  # an hour just finished: IG's own candle for it
        assert (done.open, done.high, done.low, done.close) == (i.sell_open, i.sell_high, i.sell_low,
                                                                i.sell_close), done.start
        compared += 1
    assert compared >= 240


def test_friday_13_november_hourly_candles_and_bands():
    ch = chart_over(T(2026, 11, 11), T(2026, 11, 13, 18))
    want = {  # hour: open, high, low, close, upper, middle, lower (at the hour's close)
        12: ("13231.9", "13234.3", "13217.4", "13225.2", "13239.5", "13231.5", "13223.4"),
        13: ("13225.0", "13250.3", "13223.8", "13231.3", "13239.3", "13231.8", "13224.2"),
        14: ("13230.8", "13250.9", "13223.7", "13245.6", "13242.2", "13232.6", "13223.0"),
        15: ("13245.4", "13246.4", "13217.5", "13220.3", "13242.6", "13231.8", "13221.0"),
        16: ("13220.4", "13223.2", "13206.1", "13211.3", "13244.2", "13230.5", "13216.8"),
        17: ("13211.2", "13213.9", "13204.3", "13206.7", "13246.5", "13229.4", "13212.2"),
    }
    by_start = {h.start: h for h in ch.hours}
    q = D("0.1")
    for hour, w in want.items():
        h = by_start[T(2026, 11, 13, hour)]
        assert (h.open, h.high, h.low, h.close) == tuple(D(x) for x in w[:4]), hour
        b = ch.band_at(T(2026, 11, 13, hour, 55), h.close)
        assert (b.upper.quantize(q), b.middle.quantize(q), b.lower.quantize(q)) == tuple(D(x) for x in w[4:]), hour
    # live, during the forming 14:00 hour: the band at the moment of the 14:50 candle's high
    assert ch.band_at(T(2026, 11, 13, 14, 50), D("13250.9")).upper.quantize(q) == D("13244.0")


def test_the_sell_after_the_1450_pierce(pretend_switches):
    from strategies.replay import run
    s = load_settings(switches_from=pretend_switches).for_pair("GBPUSD")
    r = run(s, store(), T(2026, 11, 13, 6), T(2026, 11, 13, 21))
    sells = [i for i in r.ideas if i.strategy == BOLLINGER_BOUNCE and i.direction == SELL]
    assert [(i.time, i.entry_price) for i in sells] == [(T(2026, 11, 13, 13, 45), D("13240.3")),
                                                        (T(2026, 11, 13, 15, 5), D("13242.3"))]
    it = sells[1]
    assert it.allowed, it.blocked_by                      # an emerging trend down: not a hindrance any more
    text = " | ".join(it.steps)
    assert "14:50 GMT pierce and rejection candle" in text and "6.9 pips above the upper hourly" in text
    assert "15:00 GMT confirmation candle: closed at 13242.4, below the rejection candle's low (13243.9)" in text
    notes = [n for t, d, n in r.notes[BOLLINGER_BOUNCE] if T(2026, 11, 13, 14, 45) <= t <= T(2026, 11, 13, 15, 0)]
    assert not any("14:45" in n for n in notes)            # 14:45 pierced but was green: not a rejection candle


class _Sender:
    def close(self, reference, half=False, why="", price=None):
        return SimpleNamespace(ok=True, what="closed")

    def move_stop(self, reference, level, why=""):
        return SimpleNamespace(ok=True, what="stop moved", level=level)


def test_the_friday_sell_trails_and_closes_at_1620_for_17_9_pips(tmp_path, pretend_switches):
    from tests.technical.test_trade_manager import Over
    S = Over(load_settings(switches_from=pretend_switches).for_pair("GBPUSD"), trade_manager={"folder": tmp_path / "tm"})
    candles = store().read_range("5m", T(2026, 11, 13, 14, 30), T(2026, 11, 13, 20))
    m = TradeManager(S, _Sender())
    entry = T(2026, 11, 13, 15, 5)
    for c in [c for c in candles if c.start < entry]:
        m.candle_finished(Bar.of(c))
    tr = plan(S, "FRI", BOLLINGER_BOUNCE, SELL, entry, D("13242.3"), D("13242.3"), D(12))
    assert tr.take_profit_pips == D(100) and tr.trail_from == D(12)
    m.add(tr)
    for c in [c for c in candles if c.start >= entry]:
        m.on_bar(Bar.of(c), finished=True)
        if not tr.open:
            break
    last = tr.decisions[-1]
    assert (last.kind, last.at, last.price, last.pips) == (STOPPED_BY_IG, T(2026, 11, 13, 16, 20), D("13224.4"),
                                                           D("17.9"))
    journal = (tmp_path / "tm" / "GBPUSD" / "decisions.jsonl").read_text()
    assert journal.count('"decision": "stop moved"') == 8
    assert '"price": "13244.6"' in journal and '"price": "13224.4"' in journal
