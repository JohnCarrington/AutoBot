"""The one-off long history fill (prices/long_history.py): the plan, the
holding folder, the comparison with the bot's own candles, and storing without
overwriting. Uses a pretend pair and a pretend history door; never contacts IG."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from types import SimpleNamespace

from prices import long_history as lh
from prices.calendar import Boundaries, MarketHours
from prices.model import Candle
from prices.store import CandleStore
from tests.technical.test_history_fill import row
from tests.technical.test_pairs import pretend

UTC = timezone.utc
NOW = datetime(2026, 11, 7, 9, 0, tzinfo=UTC)


def T(*a):
    return datetime(*a, tzinfo=UTC)


class Door:
    """Answers every request with one IG row per period start the bot expects
    (or with `labels(p)` if given), and remembers what was asked."""

    def __init__(self, labels=None, ledger=0, remaining=7084):
        self.asked, self.labels, self.used, self.remaining = [], labels, ledger, remaining

    def fetch(self, epic, resolution, start, end, points, purpose):
        p = SimpleNamespace(resolution=resolution, start=start, end=end, points=points)
        self.asked.append((epic, resolution, start, end, points))
        starts = self.labels(p) if self.labels else self._slots[(resolution, start)]
        self.remaining -= len(starts)
        return SimpleNamespace(rows=[row(t) for t in starts], remaining=self.remaining, total=10000, pages=1,
                               points_counted=points)

    def points_last_7_days(self, now=None):
        return self.used

    def ig_figures(self):
        return {"remaining": self.remaining, "total": 10000, "seen_utc": "x", "resets_utc": "y"}

    def block_in_place(self):
        return None


def _settings(tmp_path):
    return pretend(tmp_path, "EURUSD").for_pair("EURUSD")


def test_the_plan_is_4_years_weekly_2_years_daily_3_months_hourly_in_requests_of_at_most_500(tmp_path):
    s = _settings(tmp_path)
    reqs = lh.plan(s, NOW)
    by = {r: [p for p in reqs if p.resolution == r] for r in ("WEEK", "DAY", "HOUR")}
    assert [len(by[r]) for r in ("WEEK", "DAY", "HOUR")] == [1, 2, 4]
    assert all(p.points <= 500 and p.points == len(p.slots) for p in reqs)
    assert by["WEEK"][0].slots[0] == T(2022, 11, 13) and by["WEEK"][-1].slots[-1] == T(2026, 11, 1)
    assert by["DAY"][0].slots[0] == T(2024, 11, 7) and by["DAY"][-1].slots[-1] == T(2026, 11, 6)
    assert by["HOUR"][0].slots[0] == T(2026, 8, 7) and by["HOUR"][-1].slots[-1] == T(2026, 11, 6, 21)
    b = Boundaries(s.candles, MarketHours(s.market_hours))
    tfs = {"WEEK": "1w", "DAY": "1d", "HOUR": "1h"}
    for p in reqs:           # every period is a finished bot period, on the bot's own boundaries
        tf = tfs[p.resolution]
        # (a label in closed time, like Sunday 00:00, is cut at the close from the Sunday open)
        assert all(b.is_on_boundary(tf, t) and b.bucket(tf, max(t, b.hours.next_open(t)))[1] <= NOW for t in p.slots)
    assert sum(p.points for p in reqs) == 2427


def test_the_plan_says_no_when_the_budget_or_the_floor_would_be_broken(tmp_path):
    s = _settings(tmp_path)
    reqs = lh.plan(s, NOW)
    out = []
    assert lh.show_plan(s, Door(ledger=2900), reqs, NOW, out.append)
    assert "left after: 1673" in "\n".join(out) and "after: about 4657" in "\n".join(out)
    assert not lh.show_plan(s, Door(ledger=5000), reqs, NOW, out.append)        # 5000 + 2427 > 7000
    assert not lh.show_plan(s, Door(remaining=4000), reqs, NOW, out.append)     # 4000 - 2427 < 2000 floor


def _bot_week(store):
    """The bot's own weekly candle for the week of Sun 1 Nov (built from 5-minute candles)."""
    c = Candle("1w", T(2026, 11, 1), T(2026, 11, 6, 22), D("13401.7"), D("13505.6"), D("13342.9"), D("13363.8"),
               D("13383.3"), D("13503.1"), D("13341.4"), D("13346.9"), 1450, 1452)
    store.add(c)
    return c


def test_go_keeps_igs_candles_in_the_holding_folder_and_the_comparison_finds_label_differences(tmp_path):
    s = _settings(tmp_path)
    store = CandleStore(s.candles.folder, 30)
    _bot_week(store)
    reqs = [p for p in lh.plan(s, NOW) if p.resolution == "WEEK"]
    # IG labels its weeks Monday 00:00 UK (wall clock), as the real IG does
    monday = lambda t: (t.astimezone(lh.UK) + timedelta(days=1)).astimezone(UTC)  # noqa: E731
    door = Door(labels=lambda p: [monday(t) for r in reqs if r.start == p.start for t in r.slots])
    got = lh.fetch(door, s, reqs, print)
    assert door.asked[0][:2] == ("CS.D.EURUSD.TODAY.IP", "WEEK")
    assert len(got["1w"]) == 208 and all((c.parts, c.expected_parts) == (0, 0) for c in got["1w"])
    assert store.read_range("1w", T(2022, 1, 1), NOW) == [store.get("1w", T(2026, 11, 1))]   # store untouched
    assert len(lh.holding(s).read_range("1w", T(2022, 1, 1), NOW)) == 208
    out = []
    res = lh.compare(s, "1w", got["1w"], out.append)
    # every IG week is compared under the bot's Sunday 00:00 UK label (prices here are pretend ones: differ)
    assert res == {"tf": "1w", "compared": 1, "same_label": 1, "equal": 0, "off_boundary": 0}
    assert "208 of IG's candles labelled Monday 00:00 UK are compared under the bot's label" in "\n".join(out)
    # every reply was saved before it was checked
    assert len(list(lh.replies_folder(s).glob("01_WEEK_*.json"))) == 1


def test_the_comparison_reports_equal_prices_and_each_difference(tmp_path):
    s = _settings(tmp_path)
    store = CandleStore(s.candles.folder, 30)
    mine = _bot_week(store)
    same = Candle("1w", mine.start, mine.end, *mine.prices(), 0, 0)
    out = []
    assert lh.compare(s, "1w", [same], out.append)["equal"] == 1
    other = Candle("1w", mine.start, mine.end, *mine.prices()[:5], D("13500.0"), *mine.prices()[6:], 0, 0)
    out = []
    assert lh.compare(s, "1w", [other], out.append)["equal"] == 0
    assert "prices differ: sh IG 13500.0 / bot 13503.1" in "\n".join(out)


def test_store_never_overwrites_the_bots_own_and_never_stores_off_boundary_candles(tmp_path):
    s = _settings(tmp_path)
    store = CandleStore(s.candles.folder, 30)
    mine = _bot_week(store)
    hold = lh.holding(s)
    hold.add(Candle("1w", mine.start, mine.end, *(D("1"),) * 8, 0, 0))                     # same week: bot's kept
    hold.add(Candle("1w", T(2026, 10, 24, 23), T(2026, 10, 30, 21), *(D("2"),) * 8, 0, 0))  # Sun 25 Oct 00:00 BST
    hold.add(Candle("1w", T(2026, 10, 19), T(2026, 10, 26), *(D("3"),) * 8, 0, 0))         # Mon 01:00 BST: off
    hold.add(Candle("1w", T(2026, 10, 11, 23), T(2026, 10, 18), *(D("4"),) * 8, 0, 0))     # Mon 12 Oct 00:00 BST
    out = []
    counts = lh.store_into(s, store, NOW, out.append)
    assert counts["1w"] == {"stored": 2, "kept_bots_own": 1, "not_on_boundary": 1, "relabelled": 1}
    week = store.get("1w", T(2026, 10, 10, 23))                                            # Sun 11 Oct 00:00 BST
    assert week.buy_open == D("4") and week.end == T(2026, 10, 16, 21)                     # to Friday's close
    assert store.get("1w", mine.start) == mine                                            # not overwritten
    assert store.get("1w", T(2026, 10, 24, 23)).buy_open == D("2")
    assert store.get("1w", T(2026, 10, 19)) is None
    assert "Rebuild rule: 0 bigger candle(s) rebuilt" in "\n".join(out)


def test_go_refuses_while_the_price_service_is_logged_in(tmp_path, monkeypatch, capsys):
    import prices.move_to_pairs as mv
    from config import settings_loader
    st = pretend(tmp_path, "EURUSD")
    monkeypatch.setattr(settings_loader, "load_or_exit", lambda: st)
    monkeypatch.setattr(mv, "service_state", lambda: "active")
    assert lh.main(["go", "--pair", "EURUSD"]) == 3
    assert "Only one IG login at a time" in capsys.readouterr().out
    assert not (st.for_pair("EURUSD").history.pair_folder / lh.DONE_FILE).exists()     # nothing started


def test_a_reply_that_fails_a_check_is_kept_and_go_carries_on_without_resending(tmp_path):
    import pytest
    s = _settings(tmp_path)
    reqs = [p for p in lh.plan(s, NOW) if p.resolution in ("DAY", "HOUR")][:3]   # 2 daily, then 1 hourly
    hour = reqs[2]
    slots = lambda p: [t for r in reqs if r.start == p.start for t in r.slots]  # noqa: E731
    early = lambda p: [t - timedelta(hours=1) for t in slots(p)] if p.resolution == "HOUR" else slots(p)  # noqa: E731
    door = Door(labels=early)
    with pytest.raises(RuntimeError, match="outside the requested times .* The reply is kept in"):
        lh.fetch(door, s, reqs, print)
    assert len(door.asked) == 3 and len(list(lh.replies_folder(s).glob("*.json"))) == 3     # all three kept
    assert lh.already_held(s, reqs[0]) and lh.already_held(s, reqs[1]) and not lh.already_held(s, hour)
    door2 = Door(labels=slots)
    got = lh.fetch(door2, s, reqs, print)
    assert [a[1] for a in door2.asked] == ["HOUR"]                       # only the hourly one is sent again
    assert len(got["1h"]) == hour.points


def test_a_monday_label_becomes_the_bots_sunday_in_gmt_and_in_bst(tmp_path):
    s = _settings(tmp_path)
    b = Boundaries(s.candles, MarketHours(s.market_hours))
    for monday, sunday in ((T(2026, 11, 2), T(2026, 11, 1)),                    # GMT both
                           (T(2026, 10, 18, 23), T(2026, 10, 17, 23)),          # BST both
                           (T(2026, 10, 26), T(2026, 10, 24, 23)),              # Sun 25 Oct: clocks go back
                           (T(2026, 3, 30, 0) - timedelta(hours=1), T(2026, 3, 29))):   # Sun 29 Mar: clocks go forward
        c = lh.to_bot_label(b, "1w", Candle("1w", monday, monday + timedelta(days=5), *(D("1"),) * 8, 0, 0))
        assert c.start == sunday and b.is_on_boundary("1w", c.start) and c.prices() == (D("1"),) * 8


def test_the_plan_can_be_shown_for_the_hourly_requests_alone(tmp_path):
    s = _settings(tmp_path)
    hourly = [p for p in lh.plan(s, NOW) if p.resolution == "HOUR"]
    out = []
    assert lh.show_plan(s, Door(ledger=4234, remaining=5750), hourly, NOW, out.append)
    assert "Points in total (the most IG could charge): 1593" in "\n".join(out) and "1w:" not in "\n".join(out)

