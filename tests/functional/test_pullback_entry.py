"""Functional tests for PULLBACK_ENTRY (owner, approved 19 November 2026, with the owner's answers 1 to 8), with the real
settings (config/settings.toml) and the switch on, unless a test says otherwise.

The owner's rules, for the breakout and the Asian range breakout only (written for a buy; a sell is the mirror image,
on the sell price):
  1. Only these two; the slow grind and every other strategy are unchanged.
  2. On its break the strategy does not open: it waits.
  3. Entry: a candle's low reaches the 5-minute 8 EMA, and a candle closes above the 8 EMA (the same candle may do
     both); the trade opens at the next candle's open, as the Asian range breakout opens today.
  4. Wait: the confirming close must come within 6 candles after the break candle (the trade opens on the 7th at the
     latest); no entry by then, no trade.
  5. Cancel: a candle closing below the 21 EMA cancels: no trade.
  6. The stops stay as today (breakout 6, Asian range breakout 12); take profit and management unchanged.
  7. PULLBACK_ENTRY on if left out; pullback_entry.wait_candles 6.
  Answer 6: the Asian range breakout starts one wait each way per day, at the first close beyond the range; none after
  it expires or is cancelled. Answer 7: the breakout's day-direction rule is judged at the new entry price.
These tests check only that the code does what the owner said; they judge nothing on profit.

The strategies are driven candle by candle exactly as the strategy runner drives them (strategies/replay.py: the
finished candle, then the 8 and 21 EMAs after it); the last test replays the real candles of 9 and 10 November 2026.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace

import pytest

from analyser.states import EMERGING, RANGING, UP
from config.settings_loader import load_settings
from prices.model import Candle
from strategies.asian_range_breakout.strategy import AsianRangeBreakout
from strategies.breakout.strategy import Breakout
from strategies.common import (ASIAN_RANGE_BREAKOUT, BREAKOUT, BUY, SELL, opens_at_next_candle, stop_loss_pips)

UTC = timezone.utc
DAY = datetime(2026, 11, 18, 0, 0, tzinfo=UTC)          # a Wednesday; UK time is UTC in November


def settings(tmp_path: Path, pretend_switches: Path, pullback: str | None):
    """The real settings, with the tests' pretend switches and PULLBACK_ENTRY as given (None: left out)."""
    text = "".join(line + "\n" for line in pretend_switches.read_text().splitlines()
                   if not line.startswith("PULLBACK_ENTRY="))
    if pullback is not None:
        text += f"PULLBACK_ENTRY={pullback}\n"
    env = tmp_path / f"switches_{pullback}.env"
    env.write_text(text)
    return load_settings(switches_from=env).for_pair("GBPUSD")


@pytest.fixture
def ON(tmp_path, pretend_switches):
    return settings(tmp_path, pretend_switches, "on")


@pytest.fixture
def OFF(tmp_path, pretend_switches):
    return settings(tmp_path, pretend_switches, "off")


def candle(hh: int, mm: int, o, h, l, c) -> Candle:
    """A 5-minute candle at hh:mm UK on the test day; sell prices as given, buy 1.5 pips above."""
    t = DAY + timedelta(hours=hh, minutes=mm)
    s = [D(str(x)) for x in (o, h, l, c)]
    return Candle("5m", t, t + timedelta(minutes=5), *[x + D("1.5") for x in s], *s)


# ---- the breakout ------------------------------------------------------------------------------------------------

BREAK_UP = SimpleNamespace(previous_state=RANGING, state=EMERGING, direction=UP,
                           reason="broke out of the range: 2 closes above the band (last 13120, band 13118)")
FAST, SLOW = D("13115"), D("13105")          # the 8 and 21 EMAs, held still so each rule is seen on its own


def breakout_after_break(s, *candles, fast=FAST, slow=SLOW):
    """A breakout up from 10:00 (the day's 00:00 open 13100), then `candles` from 10:05: every idea made."""
    b = Breakout(s)
    b.on_candle(candle(0, 0, 13100, 13101, 13099, 13100))
    b.on_candle(candle(10, 0, 13110, 13122, 13109, 13120), BREAK_UP, DAY + timedelta(hours=9))
    out = []
    for c in candles:
        out += [(c.start, x) for x in b.on_candle(c, None, None, fast, slow)]
    return b, out


def test_rule_2_the_breakout_does_not_open_on_the_break(ON, OFF):
    beyond = candle(10, 5, 13120, 13125, 13119, 13124)            # price goes on above the breakout candle's high
    _, on = breakout_after_break(ON, beyond, candle(10, 10, 13124, 13126, 13121, 13125))
    _, off = breakout_after_break(OFF, beyond)
    assert on == []
    assert [x.entry_price for _, x in off] == [D("13122")]         # as today: on the break of the high


def test_rule_3_the_breakout_opens_at_the_next_open_after_a_touch_and_a_close_above_the_8_ema(ON):
    touch_and_close = candle(10, 5, 13118, 13119, 13114, 13117)   # low 13114 reaches the 8 EMA 13115; closes above
    nxt = candle(10, 10, 13117.5, 13120, 13116, 13119)
    b, out = breakout_after_break(ON, touch_and_close, nxt)
    assert [(t, i.strategy, i.direction, i.entry_price) for t, i in out] == [(nxt.start, BREAKOUT, BUY, D("13117.5"))]
    assert any("came back to the 8 EMA" in x for x in out[0][1].steps)


def test_rule_3_the_touch_and_the_close_may_be_different_candles(ON):
    touch = candle(10, 5, 13118, 13118, 13113, 13114)             # reaches the 8 EMA, closes below it (above the 21)
    close_above = candle(10, 10, 13114, 13118, 13114, 13116)
    nxt = candle(10, 15, 13116, 13118, 13115, 13117)
    _, out = breakout_after_break(ON, touch, close_above, nxt)
    assert [(t, i.entry_price) for t, i in out] == [(nxt.start, D("13116"))]


def test_rule_3_a_close_above_the_8_ema_without_a_touch_is_no_entry(ON):
    above = [candle(10, 5 * k, 13118, 13121, 13116, 13120) for k in range(1, 8)]   # lows 13116 never reach 13115
    _, out = breakout_after_break(ON, *above)
    assert out == []


def test_rule_4_the_confirming_close_may_come_on_the_6th_candle_and_opens_on_the_7th(ON):
    quiet = [candle(10, 5 * k, 13118, 13121, 13116, 13120) for k in range(1, 6)]   # candles 1 to 5: no touch
    sixth = candle(10, 30, 13118, 13119, 13114, 13117)                              # candle 6: touch and close above
    seventh = candle(10, 35, 13117, 13119, 13116, 13118)
    _, out = breakout_after_break(ON, *quiet, sixth, seventh)
    assert [t for t, _ in out] == [seventh.start]


def test_rule_4_no_confirming_close_within_6_candles_is_no_trade(ON):
    quiet = [candle(10, 5 * k, 13118, 13121, 13116, 13120) for k in range(1, 7)]   # candles 1 to 6: no touch
    late = candle(10, 35, 13118, 13119, 13114, 13117)                               # candle 7 would confirm
    b, out = breakout_after_break(ON, *quiet, late, candle(10, 40, 13117, 13119, 13116, 13118))
    assert out == []
    assert any("no entry within 6 candles" in n[2] for n in b.notes)


def test_rule_5_a_close_below_the_21_ema_cancels(ON):
    through = candle(10, 5, 13112, 13112, 13100, 13104)           # closes 13104, below the 21 EMA 13105
    later = candle(10, 10, 13104, 13117, 13104, 13116)            # would otherwise be a touch and close above
    b, out = breakout_after_break(ON, through, later, candle(10, 15, 13116, 13118, 13115, 13117))
    assert out == []
    assert any("below the 21 EMA" in n[2] and "cancelled" in n[2] for n in b.notes)


def test_answer_7_the_day_direction_rule_is_judged_at_the_new_entry_price(ON):
    b = Breakout(ON)
    b.on_candle(candle(0, 0, 13118, 13119, 13117, 13118))         # the day's 00:00 UK open: 13118
    b.on_candle(candle(10, 0, 13110, 13122, 13109, 13120), BREAK_UP, DAY + timedelta(hours=9))
    b.on_candle(candle(10, 5, 13118, 13119, 13114, 13117), None, None, FAST, SLOW)          # confirmed
    out = b.on_candle(candle(10, 10, 13117, 13119, 13116, 13118), None, None, FAST, SLOW)   # opens at 13117
    assert out == []                                               # 13117 is not above the day's open 13118
    assert any("not above the day's open 13118" in n[2] for n in b.notes)


def test_the_breakout_sell_is_the_mirror_image(ON):
    b = Breakout(ON)
    b.on_candle(candle(0, 0, 13200, 13201, 13199, 13200))
    down = SimpleNamespace(previous_state=RANGING, state=EMERGING, direction="down",
                           reason="broke out of the range: 2 closes below the band (last 13180, band 13182)")
    b.on_candle(candle(10, 0, 13190, 13191, 13178, 13180), down, DAY + timedelta(hours=9))
    fast, slow = D("13185"), D("13195")
    b.on_candle(candle(10, 5, 13182, 13186, 13181, 13183), None, None, fast, slow)  # high reaches 13185, closes below
    out = b.on_candle(candle(10, 10, 13183, 13184, 13180, 13181), None, None, fast, slow)
    assert [(i.direction, i.entry_price) for i in out] == [(SELL, D("13183"))]


# ---- the Asian range breakout --------------------------------------------------------------------------------------

def asian(s):
    """An Asian range breakout with a 00:00 to 07:00 range of 13100 to 13150."""
    a = AsianRangeBreakout(s)
    a.on_candle(candle(0, 0, 13120, 13150, 13100, 13125))
    return a


def run_asian(a, *candles, fast=D("13152"), slow=D("13140")):
    out = []
    for c in candles:
        out += [(c.start, x) for x in a.on_candle(c, fast, slow)]
    return out


def test_rule_2_the_asian_range_breakout_does_not_open_on_the_break(ON, OFF):
    brk, nxt = candle(7, 30, 13149, 13158, 13149, 13156), candle(7, 35, 13156, 13159, 13155, 13157)
    assert run_asian(asian(ON), brk, nxt) == []
    assert [(t, i.entry_price) for t, i in run_asian(asian(OFF), brk, nxt)] == [(nxt.start, D("13156"))]   # as today


def test_rule_3_the_asian_range_breakout_opens_at_the_next_open_after_the_pullback(ON):
    brk = candle(7, 30, 13149, 13158, 13149, 13156)               # the first close above 13150
    pull = candle(7, 35, 13156, 13157, 13151, 13154)              # low 13151 reaches the 8 EMA 13152; closes above
    nxt = candle(7, 40, 13154.5, 13158, 13154, 13157)
    out = run_asian(asian(ON), brk, pull, nxt)
    assert [(t, i.strategy, i.direction, i.entry_price) for t, i in out] == [
        (nxt.start, ASIAN_RANGE_BREAKOUT, BUY, D("13154.5"))]
    assert out[0][1].context == {"once_a_day": "Asian range breakout buy 2026-11-18"}     # once a day, as today


def test_answer_6_only_the_first_close_beyond_the_range_starts_a_wait(ON):
    a = asian(ON)
    first = candle(7, 30, 13149, 13158, 13149, 13156)
    run_asian(a, first, candle(7, 35, 13156, 13160, 13155, 13159), candle(7, 40, 13159, 13162, 13158, 13161))
    assert [w.break_candle.start for w in a.waits] == [first.start]          # the later closes above start nothing


def test_rule_5_and_answer_6_after_a_cancel_there_is_no_new_wait_that_day(ON):
    a = asian(ON)
    out = run_asian(a, candle(7, 30, 13149, 13158, 13149, 13156),
                    candle(7, 35, 13150, 13151, 13136, 13138),             # closes 13138, below the 21 EMA 13140
                    candle(7, 40, 13138, 13158, 13138, 13157),             # back above the range: no new wait
                    candle(7, 45, 13157, 13158, 13151, 13156), candle(7, 50, 13156, 13158, 13155, 13157))
    assert out == [] and a.waits == []
    assert any("cancelled" in n[2] for n in a.notes)


def test_rule_4_the_asian_range_breakout_waits_6_candles_at_most(ON):
    a = asian(ON)
    quiet = [candle(7, 30 + 5 * k, 13155, 13158, 13153, 13157) for k in range(1, 7)]   # lows never reach 13152
    out = run_asian(a, candle(7, 30, 13149, 13158, 13149, 13156), *quiet,
                    candle(8, 5, 13157, 13158, 13151, 13156), candle(8, 10, 13156, 13158, 13155, 13157))
    assert out == []
    assert any("no entry within 6 candles" in n[2] for n in a.notes)


def test_the_asian_range_breakout_sell_is_the_mirror_image(ON):
    a = asian(ON)
    out = run_asian(a, candle(7, 30, 13101, 13102, 13094, 13096),            # the first close below 13100
                    candle(7, 35, 13096, 13099, 13095, 13097),             # high 13099 reaches the 8 EMA 13098, closes below
                    candle(7, 40, 13097, 13098, 13093, 13094), fast=D("13098"), slow=D("13110"))
    assert [(i.direction, i.entry_price) for _, i in out] == [(SELL, D("13097"))]


# ---- rule 6 and 7: stops and settings; when it opens ------------------------------------------------------------

def test_rule_6_the_stops_are_unchanged(ON):
    assert stop_loss_pips(ON, BREAKOUT) == 6 and stop_loss_pips(ON, ASIAN_RANGE_BREAKOUT) == 12
    _, out = breakout_after_break(ON, candle(10, 5, 13118, 13119, 13114, 13117), candle(10, 10, 13117, 13120, 13116, 13119))
    assert "stop_price" not in out[0][1].context                  # no stop of its own: the strategy's pips, as today


def test_rule_7_the_switch_is_on_if_left_out_and_the_wait_is_6(tmp_path, pretend_switches, OFF):
    left_out = settings(tmp_path, pretend_switches, None)
    assert left_out.switches.pullback_entry is True and OFF.switches.pullback_entry is False
    assert left_out.pullback_entry.wait_candles == 6


def test_the_breakout_opens_at_the_next_candle_open_never_sent_late_only_with_the_switch_on(ON, OFF):
    assert opens_at_next_candle(ON, BREAKOUT) and not opens_at_next_candle(OFF, BREAKOUT)
    assert opens_at_next_candle(ON, ASIAN_RANGE_BREAKOUT) and opens_at_next_candle(OFF, ASIAN_RANGE_BREAKOUT)


# ---- rule 1: every other strategy unchanged (the real candles of 9 and 10 November 2026) -----------------------------

def test_rule_1_every_other_strategy_makes_exactly_the_same_ideas(tmp_path, pretend_switches):
    from prices.calendar import MarketHours
    from prices.store import CandleStore
    from strategies.replay import run
    text = pretend_switches.read_text().replace("STRATEGY_BREAKOUT=off", "STRATEGY_BREAKOUT=on").replace(
        "STRATEGY_ASIAN_RANGE_BREAKOUT=off", "STRATEGY_ASIAN_RANGE_BREAKOUT=on").replace(
        "STRATEGY_SESSION_SWEEP=off", "STRATEGY_SESSION_SWEEP=on").replace(
        "STRATEGY_NEW_YORK_OPEN_REVERSAL=off", "STRATEGY_NEW_YORK_OPEN_REVERSAL=on")
    got = {}
    for sw in ("on", "off"):
        env = tmp_path / f"all_{sw}.env"
        env.write_text(text.replace("PULLBACK_ENTRY=off", f"PULLBACK_ENTRY={sw}"))
        s = load_settings(switches_from=env).for_pair("GBPUSD")
        if not (s.candles.folder / "5m").is_dir():
            pytest.skip("the real candle store is only on the server")
        store = CandleStore(s.candles.folder, s.candles.compress_after_days)
        start = datetime(2026, 11, 9, 0, 0, tzinfo=UTC)
        ideas = run(s, store, start, start + timedelta(days=2)).ideas
        got[sw] = ideas
    other = lambda ideas: [(i.time, i.strategy, i.direction, i.entry_price, i.allowed, i.blocked_by)   # noqa: E731
                           for i in ideas if i.strategy not in (BREAKOUT, ASIAN_RANGE_BREAKOUT)]
    assert other(got["on"]) and other(got["on"]) == other(got["off"])
