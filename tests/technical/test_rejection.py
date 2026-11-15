"""Technical tests for the shared rejection part, with made-up candles. Never
contacts IG. Prices are the chart (SELL) prices; the made-up candles' buy
prices are a normal spread (1.5) above them, and a test that needs to catch the
buy price being used sets them far apart."""

import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace

import pytest

from levels import rules
from prices.indicators import Band, bollinger
from prices.model import Candle
from rejection.watch import (BOUNCE, BUY, CANCELLED, CONFIRMATION, EXPIRED, PIERCE, RANGE, REVERSAL, SELL,
                             TRIGGER, RejectionWatcher, in_watch_window, watch_windows)
from tests.technical.fake_stream import SETTINGS, T

ROOT = Path(__file__).resolve().parents[2]
SPREAD = D("1.5")       # a normal spread
START = T(2026, 11, 4, 9, 0)    # Wednesday 09:00 UK (GMT): outside every watch window


def C(i, o, h, l, c, start=START, spread=SPREAD, low_spread=None):
    """Made-up 5-minute candle number i, with these SELL prices. The buy prices
    are `spread` above (the low: `low_spread`, to make a spike like IG's)."""
    o, h, l, c = (D(str(x)) for x in (o, h, l, c))
    spread = D(str(spread))
    ls = D(str(low_spread)) if low_spread is not None else spread
    t = start + timedelta(minutes=5 * i)
    return Candle("5m", t, t + timedelta(minutes=5), o + spread, h + spread, l + ls, c + spread, o, h, l, c)


def band(c, upper=110, lower=90):
    return Band(c.start, D(100), D(upper), D(lower))


class Levels:
    """Stands in for levels.current.LevelList: levels and their groups."""
    def __init__(self, *pairs):
        lv = [rules.make(D(str(p)), t, "made up", None) for p, t in pairs]
        self.levels, self.groups = rules.group_levels(lv, D(5))

    def group_of(self, lv):
        return self.groups[lv.group - 1]


def settings(**over):
    """The real settings, with some sections changed for a test."""
    out = {name: getattr(SETTINGS, name) for name in ("chart", "bounce", "range_trade", "reversal_watch", "levels",
                                                     "rejection", "market")}
    for section, values in over.items():
        base = {k: v for k, v in vars(getattr(SETTINGS, section)).items() if not k.startswith("_")}
        base.update(values)
        out[section] = SimpleNamespace(**base)
    return SimpleNamespace(**out)


def run(candles, bands=None, levels=None, s=None, only=None):
    w = RejectionWatcher(s or settings())
    for c in candles:
        w.on_candle(c, (bands or {}).get(c.start, band(c)), levels)
    evs = [e for e in w.events if only is None or (e.version, e.direction) == only]
    return w, evs


def kinds(evs):
    return [(e.kind, e.time, e.price) for e in evs]


# ---- the Bollinger band ---------------------------------------------------------------

def test_bollinger_is_20_closes_and_2_population_standard_deviations_on_the_sell_price():
    closes = [100 + (i % 2) * 2 for i in range(20)]           # 100, 102, 100, ... : mean 101, sd 1
    cs = [C(i, x, x + 1, x - 1, x) for i, x in enumerate(closes)]
    b = bollinger(cs, "sell", 20, 2)
    assert list(b) == [cs[19].start]                           # none until there are 20 closes
    assert (b[cs[19].start].middle, b[cs[19].start].upper, b[cs[19].start].lower) == (D(101), D(103), D(99))
    assert bollinger(cs, "buy", 20, 2)[cs[19].start].middle == D("102.5")    # the buy side is 1.5 higher


def test_bollinger_settings_are_as_on_the_chart():
    assert (SETTINGS.indicators.bollinger_periods, SETTINGS.indicators.bollinger_std_devs) == (20, 2)
    assert SETTINGS.rejection.candle_timeframe == "5m"


# ---- the reversal watch windows ---------------------------------------------------------

def test_watch_windows_are_each_time_from_20_minutes_before_to_20_after_in_uk_time():
    w = watch_windows(SETTINGS, date(2026, 11, 4))              # winter: UK = UTC
    assert w[0] == (T(2026, 11, 4, 9, 40), T(2026, 11, 4, 10, 20))
    assert [a.strftime("%H:%M") for a, _ in w] == ["09:40", "10:40", "12:40", "13:40", "15:40", "16:40"]
    summer = watch_windows(SETTINGS, date(2026, 7, 1))          # BST: 10:00 UK is 09:00 UTC
    assert summer[0] == (datetime(2026, 7, 1, 8, 40, tzinfo=timezone.utc), datetime(2026, 7, 1, 9, 20, tzinfo=timezone.utc))
    assert in_watch_window(SETTINGS, T(2026, 11, 4, 9, 40)) and in_watch_window(SETTINGS, T(2026, 11, 4, 10, 20))
    assert not in_watch_window(SETTINGS, T(2026, 11, 4, 10, 25)) and not in_watch_window(SETTINGS, T(2026, 11, 4, 9, 35))
    s = settings(reversal_watch={"minutes_before": 5, "minutes_after": 5})
    assert not in_watch_window(s, T(2026, 11, 4, 9, 50))


# ---- the bounce, step by step --------------------------------------------------------------

def test_a_sell_bounce_pierce_reversal_confirmation_and_live_trigger_each_timestamped():
    cs = [C(0, 105, 112, 104, 109),     # pierces the upper band (110)
          C(1, 109, 111, 106, 107),     # first red candle: the reversal (low 106)
          C(2, 107, 108, 104, 105),     # closes 105, below the reversal low 106: confirmation (low 104)
          C(3, 105, 106, 103, 104)]     # goes below 104: trigger
    w, evs = run(cs, only=(BOUNCE, SELL))
    assert kinds(evs) == [(PIERCE, cs[0].start, D(112)), (REVERSAL, cs[1].start, D(107)),
                          (CONFIRMATION, cs[2].start, D(105)), (TRIGGER, cs[3].start, D(104))]
    st = w.setups[0]
    assert st.status == "triggered" and st.pierced == [{"what": "upper Bollinger band", "price": D("110.0"), "how": "through"}]


def test_the_reversal_candle_is_the_first_red_candle_after_the_pierce_with_no_size_rule():
    cs = [C(0, 105, 112, 104, 109), C(1, 109, 113, 108, 112), C(2, 112, 113, 111, 111.9),
          C(3, 111.9, 112, 100, 101), C(4, 101, 102, 99, 100)]
    _, evs = run(cs, bands={c.start: band(c, upper=200) for c in cs[1:]}, only=(BOUNCE, SELL))
    assert [(e.kind, e.time) for e in evs][:2] == [(PIERCE, cs[0].start), (REVERSAL, cs[2].start)]   # a 0.1 red body


def test_no_red_candle_within_3_candles_of_the_pierce_expires():
    cs = [C(0, 105, 112, 104, 109)] + [C(i, 109, 109.5, 108, 109.2) for i in (1, 2, 3)]
    _, evs = run(cs, bands={c.start: band(c, upper=200) for c in cs[1:]}, only=(BOUNCE, SELL))
    assert [(e.kind, e.time) for e in evs] == [(PIERCE, cs[0].start), (EXPIRED, cs[3].start)]
    s = settings(bounce={"reversal_candle_within_candles_of_pierce": 4})
    cs.append(C(4, 109, 109.5, 107, 108))
    _, evs = run(cs, bands={c.start: band(c, upper=200) for c in cs[1:]}, s=s, only=(BOUNCE, SELL))
    assert [e.kind for e in evs] == [PIERCE, REVERSAL]


def test_a_new_pierce_while_waiting_for_the_reversal_starts_the_count_again():
    cs = [C(0, 105, 112, 104, 109), C(1, 109, 111, 108, 109.5), C(2, 109.5, 114, 109, 113),
          C(3, 113, 113.5, 112, 113.2), C(4, 113.2, 113.4, 112, 113.3), C(5, 113.3, 113.5, 111, 112)]
    _, evs = run(cs, only=(BOUNCE, SELL))
    assert [(e.kind, e.time) for e in evs] == [(PIERCE, cs[0].start), (PIERCE, cs[1].start), (PIERCE, cs[2].start),
                                               (PIERCE, cs[3].start), (PIERCE, cs[4].start), (REVERSAL, cs[5].start)]


def test_confirmation_needs_a_close_below_the_reversal_low_a_wick_does_not_count():
    cs = [C(0, 105, 112, 104, 109), C(1, 109, 111, 106, 107),
          C(2, 107, 108, 104, 106.5),      # wick to 104 but closes 106.5, above 106
          C(3, 106.5, 107, 105, 106.1),
          C(4, 106.1, 107, 106, 106.2)]    # three candles with no close below 106
    _, evs = run(cs, bands={c.start: band(c, upper=200) for c in cs[1:]}, only=(BOUNCE, SELL))
    assert [(e.kind, e.time) for e in evs] == [(PIERCE, cs[0].start), (REVERSAL, cs[1].start), (EXPIRED, cs[4].start)]


def test_going_above_the_reversal_high_cancels_while_waiting_for_confirmation_or_trigger():
    cs = [C(0, 105, 112, 104, 109), C(1, 109, 111, 106, 107), C(2, 107, 111.5, 106.5, 107)]
    _, evs = run(cs, bands={c.start: band(c, upper=200) for c in cs[1:]}, only=(BOUNCE, SELL))
    assert [(e.kind, e.time, e.price) for e in evs][-1] == (CANCELLED, cs[2].start, D(111))
    cs = [C(0, 105, 112, 104, 109), C(1, 109, 111, 106, 107), C(2, 107, 108, 104, 105), C(3, 105, 111.2, 104.5, 110)]
    _, evs = run(cs, bands={c.start: band(c, upper=200) for c in cs[1:]}, only=(BOUNCE, SELL))
    assert [e.kind for e in evs] == [PIERCE, REVERSAL, CONFIRMATION, CANCELLED]


def test_a_candle_going_both_ways_is_a_trigger_only_if_it_opened_past_the_trigger_price():
    base = [C(0, 105, 112, 104, 109), C(1, 109, 111, 106, 107), C(2, 107, 108, 104, 105)]
    bands = {c.start: band(c, upper=200) for c in base[1:] + [C(3, 0, 0, 0, 0)]}
    _, evs = run(base + [C(3, 103.5, 111.5, 103, 105)], bands=bands, only=(BOUNCE, SELL))
    assert evs[-1].kind == TRIGGER and evs[-1].price == D(104)
    _, evs = run(base + [C(3, 105, 111.5, 103, 105)], bands=bands, only=(BOUNCE, SELL))
    assert evs[-1].kind == CANCELLED and "order is unknown" in evs[-1].note


def test_a_buy_bounce_is_the_mirror_image():
    cs = [C(0, 95, 96, 88, 91),        # pierces the lower band (90)
          C(1, 91, 94, 89, 93),        # first green candle: reversal (high 94)
          C(2, 93, 96, 92, 95),        # closes above 94: confirmation (high 96)
          C(3, 95, 97, 94, 96)]        # goes above 96: trigger
    w, evs = run(cs, only=(BOUNCE, BUY))
    assert kinds(evs) == [(PIERCE, cs[0].start, D(88)), (REVERSAL, cs[1].start, D(93)),
                          (CONFIRMATION, cs[2].start, D(95)), (TRIGGER, cs[3].start, D(96))]
    cs2 = cs[:3] + [C(3, 95, 96, 88.5, 89)]           # below the reversal low 89: cancelled
    _, evs = run(cs2, bands={c.start: band(c, lower=0) for c in cs2[1:]}, only=(BOUNCE, BUY))
    assert (evs[-1].kind, evs[-1].time, evs[-1].price) == (CANCELLED, cs2[3].start, D(89))


def test_the_live_price_triggers_or_cancels_at_the_exact_moment():
    cs = [C(0, 105, 112, 104, 109), C(1, 109, 111, 106, 107), C(2, 107, 108, 104, 105)]
    w, _ = run(cs)
    t = cs[2].end + timedelta(seconds=17)
    assert w.on_price(t - timedelta(seconds=5), D("104.0")) == []     # not below 104 yet
    ev = [e for e in w.on_price(t, D("103.9")) if e.version == BOUNCE]
    assert (ev[0].kind, ev[0].time, ev[0].price, ev[0].from_live_price) == (TRIGGER, t, D("103.9"), True)
    w, _ = run(cs[:2])
    ev = [e for e in w.on_price(cs[1].end + timedelta(seconds=3), D("111.1")) if e.version == BOUNCE]
    assert ev[0].kind == CANCELLED and ev[0].from_live_price


# ---- levels, lining up, the watch windows, sizes ------------------------------------------------

def test_a_level_is_pierced_when_the_candle_goes_through_it_and_the_lined_up_levels_are_recorded():
    lv = Levels((103, "pivot"), (104.5, "round_number"), (130, "R1"))
    cs = [C(0, 102, 105, 101, 104)]                  # from 102 up to 105: through 103 and 104.5, not 130
    w, evs = run(cs, bands={cs[0].start: band(cs[0], upper=200)}, levels=lv, only=(BOUNCE, SELL))
    st = w.setups[0]
    assert [p["what"] for p in st.pierced] == ["pivot", "round_number"]
    assert st.lined_up == [{"group": 1, "lined_up": True, "levels": ["pivot 103", "round_number 104.5"]}]
    assert st.counts and "levels line up" in evs[0].note
    # A candle that opens above a level has not pierced it on the way up.
    w, evs = run([C(0, 103.5, 105, 103.2, 104)], bands={T(2026, 11, 4, 9): band(cs[0], upper=200)},
                 levels=Levels((103, "pivot")), only=(BOUNCE, SELL))
    assert evs == []


def test_outside_the_watch_windows_only_levels_that_line_up_count_inside_any_level_counts():
    alone = Levels((103, "S1"))
    cs = [C(0, 102, 105, 101, 104)]
    w, _ = run(cs, bands={cs[0].start: band(cs[0], upper=200)}, levels=alone)
    assert not w.setups[0].in_watch_window and not w.setups[0].counts       # 09:00: outside, on its own
    inside = [C(0, 102, 105, 101, 104, start=T(2026, 11, 4, 10, 0))]          # 10:00: inside a window
    w, _ = run(inside, bands={inside[0].start: band(inside[0], upper=200)}, levels=alone)
    assert w.setups[0].in_watch_window and w.setups[0].counts
    w, _ = run(cs, bands={cs[0].start: band(cs[0], upper=104)}, levels=alone)  # the band was pierced too: counts
    assert w.setups[0].counts


def test_the_setup_runs_on_whether_or_not_it_counts_nothing_is_filtered():
    alone = Levels((110.5, "S1"))
    cs = [C(0, 105, 112, 104, 109), C(1, 109, 109.05, 108.9, 108.95), C(2, 108.95, 109, 107, 108), C(3, 108, 108.5, 106, 107)]
    w, evs = run(cs, bands={c.start: band(c, upper=200) for c in cs}, levels=alone, only=(BOUNCE, SELL))
    assert not w.setups[0].counts
    assert [e.kind for e in evs if e.setup == 1] == [PIERCE, REVERSAL, CONFIRMATION, TRIGGER]   # a tiny reversal still runs


def test_the_reversal_size_against_the_piercing_candle_is_recorded():
    cs = [C(0, 105, 112, 104, 109), C(1, 109, 111, 107, 107)]
    w, evs = run(cs, only=(BOUNCE, SELL))
    sz = w.setups[0].size
    assert (sz["piercing_body"], sz["reversal_body"], sz["piercing_range"], sz["reversal_range"]) == (D(4), D(2), D(8), D(4))
    assert sz["body_ratio"] == D("0.5") and sz["range_ratio"] == D("0.5")
    assert "body 0.50x, high-low 0.50x" in evs[1].note


def test_a_candle_within_3_pips_of_a_level_counts_the_same_as_a_pierce():
    assert SETTINGS.rejection.near_level_within_pips == 3
    lv = Levels((108, "pivot"))
    bands = {START: band(C(0, 0, 0, 0, 0), upper=200)}
    for high, counts in ((105, True), (104.9, False), (107.9, True), (108.5, True)):
        w, evs = run([C(0, 102, high, 101, 103)], bands=bands, levels=lv, only=(BOUNCE, SELL))
        assert bool(evs) is counts, high
    w, evs = run([C(0, 102, 106.5, 101, 103)], bands=bands, levels=lv, only=(BOUNCE, SELL))
    assert w.setups[0].pierced == [{"what": "pivot", "price": D(108), "how": "within 1.5 pips"}]
    assert "pivot 108 (within 1.5 pips)" in evs[0].note
    # It must come up to the level from at or below it: a candle that opens above it has not.
    assert run([C(0, 108.5, 109, 107, 108.2)], bands=bands, levels=lv, only=(BOUNCE, SELL))[1] == []
    # The buy side is the mirror image.
    w, evs = run([C(0, 115, 116, 110.5, 114)], bands=bands, levels=lv, only=(BOUNCE, BUY))
    assert w.setups[0].pierced[0]["how"] == "within 2.5 pips"
    # The distance is a setting.
    s = settings(rejection={"near_level_within_pips": 1})
    assert run([C(0, 102, 106.5, 101, 103)], bands=bands, levels=lv, s=s, only=(BOUNCE, SELL))[1] == []


def test_the_bollinger_band_still_needs_a_real_pierce():
    cs = [C(0, 105, 109.9, 104, 108)]                  # 0.1 below the upper band (110): not a pierce
    _, evs = run(cs)
    assert evs == []


# ---- the range-trade version ------------------------------------------------------------------

def test_range_version_pierce_next_candle_rejects_the_candle_after_breaks_its_low():
    cs = [C(0, 105, 112, 104, 109),     # pierces the upper band
          C(1, 109, 110, 106, 107),     # next candle red: rejection (low 106)
          C(2, 107, 108, 105, 105.5)]   # during it, below 106: trigger
    w, evs = run(cs, only=(RANGE, SELL))
    assert kinds(evs) == [(PIERCE, cs[0].start, D(112)), (REVERSAL, cs[1].start, D(107)), (TRIGGER, cs[2].start, D(106))]


def test_range_version_expires_if_the_next_candle_is_not_red_or_the_candle_after_does_not_break():
    _, evs = run([C(0, 105, 112, 104, 109), C(1, 109, 109.5, 108, 109.4)], only=(RANGE, SELL))
    assert [e.kind for e in evs] == [PIERCE, EXPIRED]
    cs = [C(0, 105, 112, 104, 109), C(1, 109, 110, 106, 107), C(2, 107, 108, 106.5, 107), C(3, 107, 107, 100, 101)]
    _, evs = run(cs, bands={c.start: band(c, upper=200) for c in cs[1:]}, only=(RANGE, SELL))
    assert [(e.kind, e.time) for e in evs] == [(PIERCE, cs[0].start), (REVERSAL, cs[1].start), (EXPIRED, cs[2].start)]


def test_range_version_is_cancelled_if_price_goes_above_the_rejection_high_first():
    cs = [C(0, 105, 112, 104, 109), C(1, 109, 110, 106, 107), C(2, 107, 110.5, 106.5, 110)]
    _, evs = run(cs, bands={c.start: band(c, upper=200) for c in cs[1:]}, only=(RANGE, SELL))
    assert [e.kind for e in evs] == [PIERCE, REVERSAL, CANCELLED]


def test_range_version_uses_only_the_band_not_levels():
    cs = [C(0, 102, 105, 101, 104)]
    w, evs = run(cs, bands={cs[0].start: band(cs[0], upper=200)}, levels=Levels((103, "pivot")))
    assert [(e.version, e.kind) for e in evs] == [(BOUNCE, PIERCE)]


def test_range_numbers_are_settings():
    s = settings(range_trade={"trigger_within_candles": 2})
    cs = [C(0, 105, 112, 104, 109), C(1, 109, 110, 106, 107), C(2, 107, 108, 106.5, 107), C(3, 107, 107, 105, 105.5)]
    _, evs = run(cs, bands={c.start: band(c, upper=200) for c in cs[1:]}, s=s, only=(RANGE, SELL))
    assert [e.kind for e in evs] == [PIERCE, REVERSAL, TRIGGER]


# ---- spread spikes ------------------------------------------------------------------------------

def test_the_spread_limit_is_a_setting_of_3_pips():
    assert SETTINGS.rejection.max_spread_pips == 3
    w = RejectionWatcher(settings())
    assert w.spread(C(0, 100, 101, 99, 100, low_spread=4)) == D(4)       # the widest of the four gaps
    assert not w.spike(C(0, 100, 101, 99, 100, spread=3)) and w.spike(C(0, 100, 101, 99, 100, spread="3.1"))


def test_a_candle_with_a_spread_spike_cannot_start_a_setup():
    cs = [C(0, 105, 112, 104, 109, spread=17)]               # would pierce the band, but the spread is 17
    w, evs = run(cs)
    assert w.setups == [] and {e.kind for e in evs} == {"ignored"}
    assert "spread on this candle was 17 points" in evs[0].note
    w, evs = run([C(0, 95, 96, 88, 91, low_spread=12)])          # a spike at the low, like IG's at 22:00
    assert w.setups == [] and {e.kind for e in evs} == {"ignored"}


def test_a_candle_with_a_spread_spike_cannot_pierce_again():
    cs = [C(0, 105, 112, 104, 109), C(1, 109, 111, 108, 109.5), C(2, 109.5, 114, 109, 113, spread=10)]
    w, evs = run(cs, only=(BOUNCE, SELL))
    assert [(e.kind, e.time) for e in evs] == [(PIERCE, cs[0].start), (PIERCE, cs[1].start), ("ignored", cs[2].start)]


def test_a_candle_with_a_spread_spike_cannot_cancel_but_the_other_steps_go_on():
    # Like 5 November 12:00: a buy bounce, then a spike dips the sell price below the reversal low.
    cs = [C(0, 95, 96, 88, 91),        # pierces the lower band
          C(1, 91, 94, 89, 93),        # reversal (green, low 89)
          C(2, 93, 95, 85, 95, low_spread="12.5"),   # dips to 85 only because the spread spiked; closes above 94
          C(3, 95, 97, 94, 96)]        # goes above the confirmation high 95: trigger
    w, evs = run(cs, bands={c.start: band(c, lower=0) for c in cs[1:]}, only=(BOUNCE, BUY))
    assert [e.kind for e in evs] == [PIERCE, REVERSAL, "ignored", CONFIRMATION, TRIGGER]
    # Without the spike the same dip cancels.
    cs[2] = C(2, 93, 95, 85, 95)
    _, evs = run(cs, bands={c.start: band(c, lower=0) for c in cs[1:]}, only=(BOUNCE, BUY))
    assert [e.kind for e in evs] == [PIERCE, REVERSAL, CANCELLED]


def test_a_live_price_during_a_spread_spike_cannot_cancel():
    cs = [C(0, 105, 112, 104, 109), C(1, 109, 111, 106, 107)]
    w, _ = run(cs)
    t = cs[1].end + timedelta(seconds=3)
    assert [e for e in w.on_price(t, D("111.5"), spread=D(17)) if e.version == BOUNCE] == []
    assert [e.kind for e in w.on_price(t, D("111.5"), spread=D("1.5")) if e.version == BOUNCE] == [CANCELLED]


# ---- the chart price, and no IG ------------------------------------------------------------------

def test_everything_uses_the_sell_price():
    # The buy prices are 30 higher here: with the buy price, 109 + 30 would pierce a band at 130.
    s = settings(rejection={"max_spread_pips": 50})
    cs = [C(0, 105, 109, 104, 108, spread=30)]
    _, evs = run(cs, bands={cs[0].start: band(cs[0], upper=130)}, s=s)
    assert evs == []
    assert RejectionWatcher(settings()).side == "sell"


def test_the_rejection_part_never_contacts_ig_or_places_trades():
    for f in (ROOT / "rejection").glob("*.py"):
        src = f.read_text()
        assert not re.search(r"^\s*(from|import)\s+(ig|orders)\b", src, re.M), f.name
        assert "requests" not in src and "lightstreamer" not in src, f.name
