"""Technical tests for the Bollinger bounce off the hourly band (design 3.3; owner, 15 November 2026): the bot's hourly
chart (prices/hourly_chart.py), the strategy (strategies/bollinger_bounce/strategy.py), its trail in the trade manager,
and what no longer holds it back. Made-up candles; nothing here contacts IG. GBPUSD: 1 point = 1 pip.

With 19 finished hourly closes all at 100 and the forming hour at price p = 100 + d, the upper band is
100 + 0.4859 d, so p is 0.5141 d above it: more than 3 pips once d is over 5.84 (a high of 106 is 3.08 above, a high
of 105.8 is 2.98 above)."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from config.settings_loader import load_settings
from prices.hourly_chart import HourlyChart
from prices.model import Candle
from strategies.bollinger_bounce.strategy import BollingerBounce
from strategies.common import BOLLINGER_BOUNCE, BUY, EMA_PULLBACK, LEVEL_REVERSAL, RANGE_TRADE, SELL
from trade_manager.manager import STOP_MOVED, STOP_NOT_MOVED, STOPPED_BY_IG, Bar, TradeManager, plan

U = lambda *a: datetime(*a, tzinfo=timezone.utc)  # noqa: E731
WED = U(2026, 11, 4)                               # Wednesday: the market is open all day
SPREAD = D("1.5")


@pytest.fixture
def S(pretend_switches):
    return load_settings(switches_from=pretend_switches).for_pair("GBPUSD")


def C(t, o, h, l, c, spread=SPREAD):
    o, h, l, c = (D(str(x)) for x in (o, h, l, c))
    return Candle("5m", t, t + timedelta(minutes=5), o + spread, h + spread, l + spread, c + spread, o, h, l, c)


def flat(start, hours, price=100):
    """Flat 5-minute candles at `price` for whole hours from `start`."""
    return [C(start + timedelta(minutes=5 * k), price, price, price, price) for k in range(12 * hours)]


def at(minutes):
    return WED + timedelta(hours=20, minutes=minutes)


# ---- the hourly chart -----------------------------------------------------------------------------

def test_an_hour_is_its_5_minute_candles(S):
    ch = HourlyChart(S)
    for k, (o, h, l, c) in enumerate([(100, 103, 99, 101), (101, 105, 100, 104), (104, 104, 98, 99)]):
        ch.add(C(WED + timedelta(minutes=5 * k), o, h, l, c))
    (hr,) = ch.hours
    assert (hr.start, hr.end, hr.open, hr.high, hr.low, hr.close) == (WED, WED + timedelta(hours=1), 100, 105, 98, 99)


def test_the_band_moves_with_the_price_in_the_forming_hour(S):
    ch = HourlyChart(S)
    for c in flat(WED, 20):
        ch.add(c)
    b = ch.band_at(at(0), D(106))
    assert (b.upper.quantize(D("0.01")), b.middle) == (D("102.92"), D("100.3"))
    assert ch.band_at(at(0), D(100)).upper == D(100)          # every close 100: no width
    assert ch.band_at(at(30), D(106)) == b                     # anywhere in the same hour


def test_a_missing_hour_while_the_market_is_open_leaves_the_band_unknown(S):
    ch = HourlyChart(S)
    for c in flat(WED, 10) + flat(WED + timedelta(hours=11), 9):   # 10:00 to 11:00 missing
        ch.add(c)
    assert ch.band_at(at(0), D(106)) is None
    ch2 = HourlyChart(S)
    for c in flat(WED, 10) + flat(WED + timedelta(hours=11), 9):
        ch2.add(c)
    assert len(ch2.hours) == 19


def test_the_weekend_does_not_count_as_missing(S):
    from prices.calendar import MarketHours
    hours = MarketHours(S.market_hours)
    ch = HourlyChart(S)
    sunday_open = hours.next_open(U(2026, 11, 7, 12))
    friday = U(2026, 11, 6, 0)
    for t in list(hours.open_slots(friday, sunday_open + timedelta(hours=3))):
        ch.add(C(t, 100, 100, 100, 100))
    assert ch.band_at(sunday_open + timedelta(hours=3), D(106)) is not None


# ---- the strategy -----------------------------------------------------------------------------------

def bounce(S, candles):
    b = BollingerBounce(S)
    b.warm(flat(WED, 20))
    out = []
    for c in candles:
        out += b.on_candle(c)
    return b, out


REJECTION = C(at(0), 104, 106.5, 101, 102)        # red; high 106.5 is 3.34 above the band at that moment
SELL_SETUP = [REJECTION,
              C(at(5), 102, 103, 101.5, 102),     # closes 102, not below the low 101: not yet
              C(at(10), 102, 102.5, 100, 100.5),  # closes below 101: the confirmation
              C(at(15), 100.4, 101, 99, 99.5)]    # opens at 100.4: the sell


def test_the_sell_opens_at_the_open_of_the_candle_after_the_confirmation(S):
    _, (x,) = bounce(S, SELL_SETUP)
    assert (x.strategy, x.direction, x.time, x.entry_price) == (BOLLINGER_BOUNCE, SELL, at(15), D("100.4"))
    text = " | ".join(x.steps)
    assert "pierce and rejection candle: its high 106.5 went 3.3 pips above the upper hourly Bollinger band" in text
    assert "confirmation candle: closed at 100.5, below the rejection candle's low (101)" in text
    assert "opens at this candle's open, 100.4" in text


def test_more_than_3_pips_is_needed(S):
    _, out = bounce(S, [C(at(0), 104, 105.8, 101, 102)] + SELL_SETUP[1:])    # 2.98 above: no
    assert out == []
    _, out = bounce(S, [C(at(0), 104, 106, 101, 102)] + SELL_SETUP[1:])      # 3.08 above: yes
    assert len(out) == 1


def test_the_pierce_candle_must_be_red(S):
    _, out = bounce(S, [C(at(0), 101, 106.5, 100.8, 104)] + SELL_SETUP[1:])  # green
    assert out == []


def test_the_confirmation_must_come_within_3_candles(S):
    wait = [C(at(5 * k), 102, 103, 101.5, 102) for k in (1, 2, 3)]
    b, out = bounce(S, [REJECTION] + wait + [C(at(20), 102, 102, 100, 100.5), C(at(25), 100.4, 101, 99, 99.5)])
    assert out == [] and any("expired" in n for _, _, n in b.notes)
    _, out = bounce(S, [REJECTION] + wait[:2] + [C(at(15), 102, 102, 100, 100.5), C(at(20), 100.4, 101, 99, 99.5)])
    assert len(out) == 1                                       # the 3rd candle: in time


def test_a_wick_below_the_low_is_not_a_confirmation(S):
    _, out = bounce(S, [REJECTION, C(at(5), 102, 103, 99, 101.5), C(at(10), 101.5, 102, 101, 101.2)])
    assert out == []


def test_price_above_the_rejection_high_cancels(S):
    b, out = bounce(S, [REJECTION, C(at(5), 102, 106.6, 101.5, 102)] + SELL_SETUP[2:])
    assert out == [] and any("cancelled" in n for _, _, n in b.notes)
    b, out = bounce(S, [REJECTION, C(at(5), 102, 106.6, 99, 100)])      # above the high AND closes below the low
    assert out == [] and b.due == []                                    # counts as the cancel


def test_a_spread_spike_cannot_start_or_cancel(S):
    spike = C(at(0), 104, 106.5, 101, 102, spread=D(4))
    _, out = bounce(S, [spike] + SELL_SETUP[1:])
    assert out == []
    _, out = bounce(S, [REJECTION, C(at(5), 102, 106.6, 101.5, 102, spread=D(4))] + SELL_SETUP[2:])
    assert len(out) == 1                                       # the spike's high did not cancel


def test_the_buy_is_the_mirror_image(S):
    _, (x,) = bounce(S, [C(at(0), 96, 99, 93.5, 98),           # green; low 93.5 is 3.34 below the lower band
                         C(at(5), 98, 99.5, 97.5, 99.5),       # closes above the high 99: the confirmation
                         C(at(10), 99.6, 100, 99, 99.8)])
    assert (x.direction, x.time, x.entry_price) == (BUY, at(10), D("99.6"))


def test_setups_confirming_together_are_one_bounce(S):
    second = C(at(5), 103, 106.4, 101.8, 102)                 # red, pierces again (its own setup)
    _, out = bounce(S, [REJECTION, second, C(at(10), 102.5, 102.5, 100, 100.5), C(at(15), 100.4, 101, 99, 99.5)])
    assert [(x.direction, x.time) for x in out] == [(SELL, at(15))]


def test_no_band_no_setup(S):
    b = BollingerBounce(S)
    b.warm(flat(WED + timedelta(hours=10), 10))               # only 10 hours: the band is not known
    assert [x for c in SELL_SETUP for x in b.on_candle(c)] == []


def test_the_live_copy_changes_nothing(S):
    b, _ = bounce(S, SELL_SETUP[:3])
    f = b.fork()
    (x,) = f.on_candle(C(at(15), 100.4, 100.4, 100.4, 100.4))   # the forming candle's first price
    assert x.entry_price == D("100.4")
    assert len(b.due) == 1 and len(b.chart.hours) == len(f.chart.hours) and b.chart.hours[-1].close == D("100.5")


# ---- the shared checks and the safety rules: nothing else holds it back -------------------------------

def test_the_bounce_is_not_held_back_by_one_view_or_the_most_at_once(S):
    from safety.rules import OpenTrade, is_reversal
    from safety.rules import _limits
    idea = SimpleNamespace(strategy=BOLLINGER_BOUNCE, direction=SELL, state="trend", state_direction="up",
                           trend_type="strong push")
    assert not is_reversal(idea)
    order = SimpleNamespace(idea=idea)
    others = [OpenTrade(s, BUY, WED, D(12), D(10)) for s in (RANGE_TRADE, LEVEL_REVERSAL, "slow grind", "breakout",
                                                              EMA_PULLBACK, EMA_PULLBACK)]
    assert _limits(S, order, others + [OpenTrade(BOLLINGER_BOUNCE, BUY, WED, D(12), D(10))]) == []
    got = _limits(S, order, [OpenTrade(BOLLINGER_BOUNCE, SELL, WED, D(12), D(10))])
    assert got and "at most 1 each way" in got[0]


def test_the_bounce_closes_nothing_at_the_band_nor_at_a_level(S):
    from strategies.common import closed_on_level_rejection
    from trade_manager.manager import band_close_share
    assert band_close_share(S, BOLLINGER_BOUNCE) == 0 and not closed_on_level_rejection(BOLLINGER_BOUNCE)
    assert closed_on_level_rejection(RANGE_TRADE)


# ---- the trail -------------------------------------------------------------------------------------

class Sender:
    def __init__(self, ok=True):
        self.ok, self.moves, self.closes = ok, [], []

    def close(self, reference, half=False, why="", price=None):
        self.closes.append(price)
        return SimpleNamespace(ok=True, what="closed")

    def move_stop(self, reference, level, why=""):
        self.moves.append(level)
        return SimpleNamespace(ok=self.ok, what="stop moved" if self.ok else "stop not moved",
                               reasons=[] if self.ok else ["IG said no"])


def manager(S, tmp_path, sender, ig_confirms=False, now=None):
    from tests.technical.test_trade_manager import Over
    s = Over(S, trade_manager={"folder": tmp_path / "tm"})
    return TradeManager(s, sender, ig_confirms=ig_confirms, **({"now": now} if now else {})), s


def B(t, o, h, l, c):
    return Bar.of(C(t, o, h, l, c))


def test_the_trail_starts_at_12_pips_and_follows_the_last_3_candles(S, tmp_path):
    snd = Sender()
    m, s = manager(S, tmp_path, snd)
    for k, row in enumerate([(100, 101, 99, 100), (100, 100.5, 99, 99.5), (99.5, 100, 98, 99)]):
        m.candle_finished(B(WED + timedelta(minutes=5 * k), *row))
    tr = plan(s, "T1", BOLLINGER_BOUNCE, SELL, WED + timedelta(minutes=15), D(100), D(100), D(12), [])
    m.add(tr)
    t = WED + timedelta(minutes=15)
    m.on_bar(B(t, 100, 100, 92, 93), finished=True)           # best: buy low 93.5, 6.5 up: no trail
    assert snd.moves == []
    m.on_bar(B(t + timedelta(minutes=5), 93, 93, 86, 87), finished=True)    # buy low 87.5: 12.5 up
    assert snd.moves == [D("101.6")]                         # buy highs 101.5, 101.5, 94.5 -> 101.5 + 0.1
    m.on_bar(B(t + timedelta(minutes=10), 87, 88, 85, 86), finished=True)    # 101.5, 94.5, 89.5: no closer
    assert snd.moves == [D("101.6")]
    m.on_bar(B(t + timedelta(minutes=15), 86, 90, 85, 89), finished=True)    # 94.5, 89.5, 91.5 -> 94.6
    assert snd.moves[-1] == D("94.6")
    m.on_bar(B(t + timedelta(minutes=20), 89, 89.5, 84, 85), finished=True)  # 89.5, 91.5, 91 -> 91.6
    assert snd.moves[-1] == D("91.6") and len(snd.moves) == 3
    (d,) = [d for _, d in m.on_bar(B(t + timedelta(minutes=25), 85, 90.5, 85, 90), finished=True)]
    assert (d.kind, d.price, d.pips) == (STOPPED_BY_IG, D("91.6"), D("8.4"))
    assert "trailed to 91.6" in d.why


def test_the_trail_never_moves_back(S, tmp_path):
    snd = Sender()
    m, s = manager(S, tmp_path, snd)
    tr = plan(s, "T2", BOLLINGER_BOUNCE, BUY, WED, D(100), D("101.5"), D(12), [])
    m.add(tr)
    rows = [(100, 115, 100, 114), (114, 116, 113, 115), (115, 117, 114, 116), (116, 116, 108, 110)]
    for k, row in enumerate(rows):
        m.on_bar(B(WED + timedelta(minutes=5 * k), *row), finished=True)
    # a buy trails below the last 3 candles' lowest sell price, only ever higher
    assert snd.moves == sorted(snd.moves) and snd.moves[0] == D("99.9")


def test_a_trail_move_ig_does_not_confirm_keeps_the_old_stop_and_is_tried_again(S, tmp_path):
    clock = {"t": WED}
    snd = Sender(ok=False)
    m, s = manager(S, tmp_path, snd, ig_confirms=True, now=lambda: clock["t"])
    for k in range(3):
        m.candle_finished(B(WED - timedelta(minutes=5 * (3 - k)), 100, 101, 99, 100))
    tr = plan(s, "T3", BOLLINGER_BOUNCE, SELL, WED, D(100), D(100), D(12), [])
    m.add(tr)
    m.on_bar(B(WED, 100, 100, 85, 86), finished=True)
    assert snd.moves == [D("102.6")] and tr.stop_level is None and tr.trail_want == D("102.6")
    m.on_bar(Bar(WED + timedelta(seconds=10), *[D(87)] * 8))   # a live price, before the retry time
    assert len(snd.moves) == 1
    clock["t"] = WED + timedelta(seconds=s.orders.close_retry_seconds + 1)
    snd.ok = True
    m.on_bar(Bar(clock["t"], *[D(87)] * 8))
    assert snd.moves[-1] == D("102.6") and tr.stop_level == D("102.6") and tr.trail_want is None
    journal = (tmp_path / "tm" / "GBPUSD" / "decisions.jsonl").read_text()
    assert f'"decision": "{STOP_NOT_MOVED}"' in journal and f'"decision": "{STOP_MOVED}"' in journal


def test_only_the_bounce_trails(S, tmp_path):
    snd = Sender()
    m, s = manager(S, tmp_path, snd)
    for k in range(3):
        m.candle_finished(B(WED - timedelta(minutes=5 * (3 - k)), 100, 101, 99, 100))
    m.add(plan(s, "T4", RANGE_TRADE, SELL, WED, D(100), D(100), D(12), []))
    m.on_bar(B(WED, 100, 100, 85, 86), finished=True)
    assert snd.moves == []


def test_no_trail_without_3_candles_known(S, tmp_path):
    snd = Sender()
    m, s = manager(S, tmp_path, snd)
    m.add(plan(s, "T5", BOLLINGER_BOUNCE, SELL, WED, D(100), D(100), D(12), []))
    m.on_bar(B(WED, 100, 100, 85, 86), finished=True)          # only 1 candle known
    assert snd.moves == []
    m.on_bar(B(WED + timedelta(minutes=5), 86, 87, 84, 85), finished=True)
    m.on_bar(B(WED + timedelta(minutes=10), 85, 86, 84, 85), finished=True)
    assert snd.moves == [D("101.6")]


# ---- the bounce's own two switches (owner, 15 November 2026), check 5 in strategies/common.py ----------------

def _switched(S, **on):
    from tests.technical.test_trade_manager import Over
    return Over(S, switches=on)


def _checked(S, t, hourly_state=None, strategy=BOLLINGER_BOUNCE):
    from analyser.hourly_read import HourlyRead
    from strategies.common import Candidate, check
    hourly = HourlyRead(hourly_state, None, None, None, None, "") if hourly_state else None
    state = SimpleNamespace(state="trend", direction="down", trend_type=None)
    return check(S, "GBPUSD", Candidate(strategy, SELL, t, D("100"), ["x"]), state, None, None, hourly)


UKT = lambda h, m: datetime(2026, 11, 11, h, m, tzinfo=timezone.utc)   # noqa: E731  (UK = UTC in November)


def test_both_bounce_switches_are_off_by_default_and_then_change_nothing(S):
    from analyser.hourly_read import RALLY
    assert not S.switches.bounce_only_when_hourly_ranging and not S.switches.bounce_only_near_times
    assert _checked(S, UKT(12, 0), RALLY).allowed


def test_only_when_hourly_ranging(S):
    from analyser.hourly_read import RALLY, RANGING, SELL_OFF
    on = _switched(S, bounce_only_when_hourly_ranging=True, hourly_read=False)
    assert _checked(on, UKT(12, 0), RANGING).allowed
    for state in (RALLY, SELL_OFF):
        idea = _checked(on, UKT(12, 0), state)
        assert not idea.allowed and f"hourly chart is in a {state}" in idea.blocked_by
    assert not _checked(on, UKT(12, 0), None).allowed                       # not known: not allowed
    assert _checked(on, UKT(12, 0), RALLY, strategy=LEVEL_REVERSAL).allowed  # the bounce only


@pytest.mark.parametrize("h,m,ok", [(8, 59, False), (9, 0, True), (10, 0, True), (11, 0, True), (11, 5, False),
                                    (12, 0, False), (12, 55, False), (13, 0, True), (15, 0, True), (17, 0, True),
                                    (17, 5, False), (6, 0, False), (20, 0, False)])
def test_only_near_10_14_and_16_uk_both_ends_included(S, h, m, ok):
    on = _switched(S, bounce_only_near_times=True)
    idea = _checked(on, UKT(h, m))
    assert idea.allowed is ok
    if not ok:
        assert "within 60 minutes of 10:00, 14:00, 16:00 UK" in idea.blocked_by


def test_near_times_are_uk_clock_times_in_summer(S):
    on = _switched(S, bounce_only_near_times=True)
    assert _checked(on, datetime(2026, 7, 15, 8, 30, tzinfo=timezone.utc)).allowed      # 09:30 BST
    assert not _checked(on, datetime(2026, 7, 15, 10, 30, tzinfo=timezone.utc)).allowed  # 11:30 BST


def test_both_switches_on_need_both(S):
    from analyser.hourly_read import RALLY, RANGING
    on = _switched(S, bounce_only_when_hourly_ranging=True, bounce_only_near_times=True)
    assert _checked(on, UKT(14, 30), RANGING).allowed
    assert not _checked(on, UKT(14, 30), RALLY).allowed
    assert not _checked(on, UKT(12, 0), RANGING).allowed
