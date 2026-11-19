"""Technical tests for the execution-integrity investigation of 18 November 2026 (owner's brief, 19 November 2026):

  * the live check (StrategyRunner.peek) waits for the finished candle before the forming one: at each candle's
    turn IG's live prices arrive before its finished candle is stored, and the strategies' copies must never be
    given the new candle straight after the one before last;
  * a running rejection setup's trigger and cancel never depend on the Bollinger band (the band only starts setups);
  * the analyser journal's provenance: every new line says whether it is a LIVE_DECISION, a HISTORICAL_REPLAY or
    RECONSTRUCTED, with its event time and recording time apart; old lines read as UNKNOWN_LEGACY and are never
    rewritten.
Made-up candles; never contacts IG."""

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from analyser.market_state import (CURRENT, HISTORICAL_REPLAY, JOURNAL, LIVE_DECISION, RECONSTRUCTED, UNKNOWN_LEGACY,
                                   StateTracker, provenance_of)
from prices.calendar import MarketHours
from prices.indicators import Band
from prices.model import Candle
from rejection.watch import CANCELLED, TRIGGER, RejectionWatcher
from strategies.replay import StrategyRunner
from tests.technical.test_market_states import FIVE, OPEN, _make_store
from tests.technical.test_pairs import pretend

UTC = timezone.utc


@pytest.fixture
def st(tmp_path):
    return pretend(tmp_path, "EURUSD").for_pair("EURUSD")     # 1 point a pip


def C(t, o, h, lo, c):
    """A candle, sell prices as given, buy prices 1 higher."""
    o, h, lo, c = (D(str(x)) for x in (o, h, lo, c))
    return Candle("5m", t, t + FIVE, o + 1, h + 1, lo + 1, c + 1, o, h, lo, c)


# ---- the live check waits for the finished candle before the forming one --------------------------------------

def _runner(st, last_start):
    """Only what waiting_for_finished_candle reads: the strategies' last finished candle and the market hours."""
    return SimpleNamespace(week=[C(last_start, 100, 101, 99, 100)], hours=MarketHours(st.market_hours))


def test_the_live_check_goes_on_when_the_candle_before_the_forming_one_is_taken(st):
    t = datetime(2026, 11, 18, 15, 40, tzinfo=UTC)
    assert StrategyRunner.waiting_for_finished_candle(_runner(st, t), t + FIVE) is False


def test_the_live_check_waits_while_the_candle_before_the_forming_one_is_not_yet_stored(st):
    # 18 November 2026: the 15:45 candle's first live price came before IG's finished 15:40 candle was stored
    t = datetime(2026, 11, 18, 15, 35, tzinfo=UTC)
    assert StrategyRunner.waiting_for_finished_candle(_runner(st, t), t + 2 * FIVE) is True


def test_a_candle_missing_or_delayed_in_the_market_hours_pauses_the_live_check(st):
    t = datetime(2026, 11, 18, 15, 0, tzinfo=UTC)
    for gap in (2, 3, 12):                                  # one, two or eleven candles not stored (yet)
        assert StrategyRunner.waiting_for_finished_candle(_runner(st, t), t + gap * FIVE) is True


def test_no_wait_when_the_slot_before_the_forming_candle_is_outside_the_market_hours(st):
    friday_last = datetime(2026, 11, 13, 21, 55, tzinfo=UTC)            # the week's last candle
    hours = MarketHours(st.market_hours)
    first = hours.session(datetime(2026, 11, 16, 12, 0, tzinfo=UTC))[0]   # the next week's open
    assert not hours.is_open(first - FIVE)
    assert StrategyRunner.waiting_for_finished_candle(_runner(st, friday_last), first) is False


# ---- a running setup's trigger and cancel do not depend on the band ------------------------------------------

def _setup_to_trigger(st, trigger_band):
    """A sell bounce setup started by a band pierce, then its trigger candle given `trigger_band`."""
    w = RejectionWatcher(st, design_only=True)
    t = datetime(2026, 11, 18, 19, 30, tzinfo=UTC)
    band = Band(t, D("99"), D("100"), D("98"))
    w.on_candle(C(t, 99, 101, D("98.5"), 100), band)                        # pierce of the upper band 100
    w.on_candle(C(t + FIVE, 100, D("100.5"), 99, D("99.2")), band)          # red: the reversal candle
    w.on_candle(C(t + 2 * FIVE, D("99.2"), D("99.5"), 98, D("98.4")), band)  # closes below 99: trigger below 98
    events = w.on_candle(C(t + 3 * FIVE, D("98.4"), D("98.6"), D("97.5"), D("97.8")), trigger_band)
    return [(e.kind, e.time, e.price) for e in events if e.setup == 1]


def test_a_running_setups_trigger_is_the_same_whatever_band_it_is_given(st):
    t = datetime(2026, 11, 18, 19, 45, tzinfo=UTC)
    got = [_setup_to_trigger(st, b) for b in (None, Band(t, D("99"), D("100"), D("98")),
                                              Band(t, D("95"), D("90"), D("80")))]
    assert got[0] == got[1] == got[2] == [(TRIGGER, t, D("98"))]


# ---- the order inside a candle: live (a forming candle) and from the finished candle -------------------------

def _confirmed(st):
    w = RejectionWatcher(st, design_only=True)
    t = datetime(2026, 11, 18, 19, 30, tzinfo=UTC)
    band = Band(t, D("99"), D("100"), D("98"))
    for c in (C(t, 99, 101, D("98.5"), 100), C(t + FIVE, 100, D("100.5"), 99, D("99.2")),
              C(t + 2 * FIVE, D("99.2"), D("99.5"), 98, D("98.4"))):
        w.on_candle(c, band)
    return w, t + 3 * FIVE                     # trigger below 98, cancel above 100.5 (the reversal candle's high)


def test_live_a_forming_candle_through_the_trigger_before_the_cancel_price_triggers(st):
    w, t = _confirmed(st)
    events = w.fork().on_candle(C(t, D("98.3"), D("98.3"), D("97.9"), D("97.9")), None)
    assert [e.kind for e in events if e.setup == 1] == [TRIGGER]


def test_live_a_forming_candle_past_the_cancel_price_first_is_cancelled_not_triggered(st):
    w, t = _confirmed(st)
    events = w.fork().on_candle(C(t, D("98.3"), D("100.6"), D("98.1"), D("100.4")), None)
    assert [e.kind for e in events if e.setup == 1] == [CANCELLED]
    later = w.fork()                                        # once cancelled, a later fall never triggers it
    later.on_candle(C(t, D("98.3"), D("100.6"), D("98.1"), D("100.4")), None)
    later.on_candle(C(t + FIVE, D("98"), D("98.1"), D("97"), D("97.2")), None)
    assert [e.kind for e in later.events if e.setup == 1 and e.kind in (TRIGGER, CANCELLED)] == [CANCELLED]


def test_a_finished_candle_through_both_counts_as_cancelled_unless_it_opened_past_the_trigger(st):
    """docs/REJECTION.md, 'With stored candles': the order inside a finished candle is unknown."""
    w, t = _confirmed(st)
    both = w.fork().on_candle(C(t, D("98.3"), D("100.6"), D("97.9"), D("99")), None)
    assert [e.kind for e in both if e.setup == 1] == [CANCELLED]
    opened_past = w.fork().on_candle(C(t, D("97.9"), D("100.6"), D("97.5"), D("99")), None)
    assert [e.kind for e in opened_past if e.setup == 1] == [TRIGGER]


def test_the_watcher_fork_used_by_the_live_check_never_changes_the_watcher(st):
    w, t = _confirmed(st)
    before = (len(w.events), [s.status for s in w.setups])
    w.fork().on_candle(C(t, D("98.3"), D("98.3"), D("97.9"), D("97.9")), None)
    assert (len(w.events), [s.status for s in w.setups]) == before


# ---- the analyser journal's provenance -------------------------------------------------------------------------

def _clock(t):
    return lambda: t


def _times(store_end, tracker_cls=StateTracker, st=None, store=None):
    ref = tracker_cls(st, store)
    ref.replay(store_end)
    return [c.time for c in ref.changes]


def test_a_restart_after_an_older_rule_labels_the_replayed_changes_historical_replay_not_live(st):
    """The 18 November 2026 case: the journal (written before provenance, no live_through_utc) ends at an earlier
    change; the restart's replay, under a newer rule, finds changes after it that the live bot never made."""
    store, end = _make_store(st)
    ref = StateTracker(st, store)
    ref.replay(end)
    made = [c.as_dict() for c in ref.changes]
    assert len(made) >= 4
    legacy = made[:2]                                       # the older run's live record: no provenance
    folder = ref.folder
    folder.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(r) + "\n" for r in legacy)
    (folder / JOURNAL).write_text(text)
    restarted = StateTracker(st, store, record=True)
    restarted.clock = _clock(datetime(2026, 11, 3, 13, 35, 21, tzinfo=UTC))
    restarted.replay(end)
    rows = restarted.recorded()
    assert (folder / JOURNAL).read_text().startswith(text)          # the old lines are never rewritten
    assert [provenance_of(r) for r in rows[:2]] == [UNKNOWN_LEGACY, UNKNOWN_LEGACY]
    assert [provenance_of(r) for r in rows[2:]] == [HISTORICAL_REPLAY] * (len(made) - 2)
    assert all(r["recorded_utc"] == "2026-11-03T13:35:21Z" == r["run_started_utc"] for r in rows[2:])
    assert [r["time_utc"] for r in rows] == [r["time_utc"] for r in made]       # still in time order


def test_live_changes_are_live_decisions_and_a_later_start_up_marks_the_stopped_time_reconstructed(st):
    store, end = _make_store(st)
    times = _times(end, st=st, store=store)
    assert len(times) >= 5
    up = times[1] + FIVE                                    # first run: start-up just after the second change
    stop = times[-3] + FIVE                                 # ... live until just after the third last change
    a = StateTracker(st, store, record=True)
    a.clock = _clock(datetime(2026, 11, 3, 9, 0, tzinfo=UTC))
    a.replay(up)
    t = up
    while t < stop:
        t += FIVE
        a.advance(t)
    rows = a.recorded()
    assert [provenance_of(r) for r in rows] == [HISTORICAL_REPLAY] * 2 + [LIVE_DECISION] * (len(rows) - 2)
    live_through = json.loads((a.folder / CURRENT).read_text())["live_through_utc"]
    assert live_through == stop.strftime("%Y-%m-%dT%H:%M:%SZ")
    # stopped at `stop`; started again at the end: what it missed was never decided live
    b = StateTracker(st, store, record=True)
    b.clock = _clock(datetime(2026, 11, 3, 18, 0, tzinfo=UTC))
    b.replay(end)
    after = b.recorded()[len(rows):]
    assert after and [provenance_of(r) for r in after] == [RECONSTRUCTED] * len(after)
    assert all(r["time_utc"] >= live_through for r in after)
    assert b.recorded()[:len(rows)] == rows                 # the earlier lines are unchanged
    # restarting again adds nothing twice
    c = StateTracker(st, store, record=True)
    c.replay(end)
    assert c.recorded() == b.recorded()
    # the start-up keeps the last run's live_through_utc until it takes a candle live itself
    assert json.loads((c.folder / CURRENT).read_text())["live_through_utc"] == live_through


def test_the_event_time_and_the_recording_time_are_kept_apart(st):
    store, end = _make_store(st)
    a = StateTracker(st, store, record=True)
    a.clock = _clock(datetime(2026, 11, 4, 7, 1, 2, tzinfo=UTC))
    a.replay(end)
    for r, ch in zip(a.recorded(), a.changes):
        assert r["time_utc"] == ch.time.strftime("%Y-%m-%dT%H:%M:%SZ")             # the candle's start
        assert r["recorded_utc"] == "2026-11-04T07:01:02Z" != r["time_utc"]      # when it was written


def test_a_line_without_provenance_is_unknown_legacy_never_live():
    assert provenance_of({"time_utc": "2026-11-18T09:30:00Z", "state": "possible reversal"}) == UNKNOWN_LEGACY
    assert provenance_of({"provenance": "something else"}) == UNKNOWN_LEGACY
    assert provenance_of({"provenance": LIVE_DECISION}) == LIVE_DECISION


def test_a_new_week_while_running_is_live(st):
    store, end = _make_store(st)
    t = StateTracker(st, store)
    t.replay(end)
    assert t.live_from == len(t.changes)
    t.advance(datetime(2026, 11, 8, 21, 2, tzinfo=UTC))       # this week's open, while running
    assert t.week_open == datetime(2026, 11, 8, 21, tzinfo=UTC) and t.live_from == 0


def test_a_tracker_that_does_not_record_writes_nothing(st):
    store, end = _make_store(st)
    t = StateTracker(st, store)
    t.replay(end)
    assert not (t.folder / JOURNAL).exists() and not (t.folder / CURRENT).exists()
