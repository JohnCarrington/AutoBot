"""TREND_ENDS_IN_CONSOLIDATION (owner, 24 November 2026; analyser/states.py), on if left out.

Johnny: "Once the analyser has called a trend, it should stay in trend and be done with it. Even when a trend does
reverse after a move like that, it goes into consolidation first, not a sharp bounce."
  1. while the analyser is in "trend" (slow grind or strong push) it cannot go to "possible reversal" (and so cannot
     flip to an emerging trend the other way: the possible reversal was the only route);
  2. a trend ends only in consolidation; a break out of consolidation decides the next state, as before;
  3. the owner's answers: the 100 EMA exit always goes to consolidation; the 24-candle fade always goes to
     consolidation; the ranging reading counts as consolidation;
  4. nothing else changes: an emerging trend can still go to a possible reversal.
The other analyser tests run with the switch off (tests/conftest.py, test_pairs.py) and check the old behaviour."""

from types import SimpleNamespace

from analyser.states import CONSOLIDATION, DOWN, EMERGING, POSSIBLE_REVERSAL, RANGING, TREND, UP
from config.settings_loader import load_settings
from tests.technical.test_market_states import (F, OPEN, RANGING_OK, S2, BUY, CONFIRMATION, downtrend, ev, far_down,
                                                possible, run, setups, st, trend)  # noqa: F401  (st is a fixture)


class on:
    """The test settings with TREND_ENDS_IN_CONSOLIDATION on (everything else as given)."""

    def __init__(self, st):
        self._st = st
        self.switches = SimpleNamespace(**(vars(st.switches) | {"trend_ends_in_consolidation": True}))

    def __getattr__(self, name):
        return getattr(self._st, name)


def test_the_switch_is_on_if_left_out(tmp_path, pretend_switches):
    text = "".join(l + "\n" for l in pretend_switches.read_text().splitlines()
                   if not l.startswith("TREND_ENDS_IN_CONSOLIDATION="))
    p = tmp_path / "s.env"
    p.write_text(text)
    assert load_settings(switches_from=p).switches.trend_ends_in_consolidation is True
    p.write_text(text + "TREND_ENDS_IN_CONSOLIDATION=off\n")
    assert load_settings(switches_from=p).switches.trend_ends_in_consolidation is False


def test_a_trend_does_not_go_to_a_possible_reversal(st):
    m = far_down(on(st))
    assert possible(m) == []
    assert (m.now.state, m.now.direction) == (TREND, DOWN)
    old = far_down(st)                                   # switch off: the possible reversal, as before
    (ch,) = possible(old)
    assert (ch.state, ch.direction) == (POSSIBLE_REVERSAL, UP)


def test_an_emerging_trend_is_unchanged(st):
    """Only the trend state is changed: an emerging trend reacts to the same rejection the same way, switch on or
    off (here the rejection at S2 starts an emerging trend the other way, as built)."""
    got = []
    for settings in (on(st), st):
        m = downtrend(settings, 11650)
        run(m, [(1, F(1, c=11612, l=11610, ema100=11640))])          # 40 pips down, still emerging
        assert m.now.state == EMERGING
        got.append([(c.state, c.direction, c.reason) for c in possible(m, 2)])
    assert got[0] == got[1] and got[0]


def test_the_100_ema_exit_always_goes_to_consolidation(st):
    m = trend(on(st))
    assert run(m, [(3, F(3, c=11660, ema100=11655, **RANGING_OK))]) == []
    (ch,) = run(m, [(4, F(4, c=11661, ema100=11655, **RANGING_OK))])
    assert ch.state == CONSOLIDATION and "back above the 100 EMA" in ch.reason
    old = trend(st)                                      # switch off: ranging, as before
    run(old, [(3, F(3, c=11660, ema100=11655, **RANGING_OK))])
    (ch,) = run(old, [(4, F(4, c=11661, ema100=11655, **RANGING_OK))])
    assert ch.state == RANGING


def test_the_ranging_reading_counts_as_consolidation(st):
    m = trend(on(st))
    assert run(m, [(3, F(3, c=11640, ema100=11660, **RANGING_OK))]) == []
    (ch,) = run(m, [(4, F(4, c=11640, ema100=11660, **RANGING_OK))])
    assert ch.state == CONSOLIDATION and "the ranging reading, counted as consolidation" in ch.reason
    old = trend(st)
    run(old, [(3, F(3, c=11640, ema100=11660, **RANGING_OK))])
    (ch,) = run(old, [(4, F(4, c=11640, ema100=11660, **RANGING_OK))])
    assert ch.state == RANGING


def test_the_24_candle_fade_always_goes_to_consolidation(st):
    for settings, want in ((on(st), CONSOLIDATION), (st, RANGING)):
        m = trend(settings)
        m.base = lambda f: (RANGING, "the ranging reading")         # what the fade would fall back to
        out = run(m, [(i, F(i, c=11650, l=11650, ema100=11660)) for i in range(3, 3 + 24)])
        assert out and out[-1].state == want and "faded" in out[-1].reason


def test_a_trend_still_ends_in_consolidation_and_a_break_out_decides_next(st):
    m = trend(on(st))
    narrow = dict(width=6, mid_slope="0.1", no_close_outside=True, avg_body=2, colour_ratio="1.5")
    run(m, [(3, F(3, c=11640, ema100=11660, **narrow))])
    (ch,) = run(m, [(4, F(4, c=11640, ema100=11660, **narrow))])
    assert ch.state == CONSOLIDATION and "ran out of steam" in ch.reason
    (ch,) = run(m, [(5, F(5, c=11660, upper=11655, lower=11630))])
    assert (ch.state, ch.direction) == (EMERGING, UP) and "broke out of the consolidation" in ch.reason
