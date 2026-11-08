"""Technical tests for the records, the Telegram trade messages and the daily summary (design section 9), and the
engine's use of them, with the pretend analyser, strategies and IG of test_trading.py. Nothing here contacts IG or
Telegram, and everything is written to temporary folders."""

import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from alerts.trades import PartClose, TradeClosed, TradeOpened, closed_text, opened_text
from records.book import Book, daily_text
from strategies.common import BOLLINGER_BOUNCE, BREAKOUT, BUY, EMA_PULLBACK, LEVEL_REVERSAL, RANGE_TRADE, SELL, SLOW_GRIND, Idea
from tests.technical.test_trading import C, S, candle, feed, idea, make, tick  # noqa: F401  (S: the fixture)
from trading.reasons import level_note, one_line, take_profit_kind

U = lambda *a: datetime(*a, tzinfo=timezone.utc)  # noqa: E731
WED = U(2026, 11, 4, 10, 0)


def rows(path):
    return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []


# ---- the reason in one line, the level, the kind of take profit -----------------------------------------

BOUNCE_STEPS = [
    "Wed 04 Nov 10:05 GMT  #12 bounce sell pierce 13400.0: high 13400 reached S2 13398.1 (within 1.9 pips); in a reversal watch window; counts",
    "Wed 04 Nov 10:10 GMT  #12 bounce sell reversal 13399.0: the first red candle",
    "Wed 04 Nov 10:15 GMT  #12 bounce sell confirmation 13395.0: closed below the reversal candle's low",
    "Wed 04 Nov 10:20 GMT  #12 bounce sell trigger 13394.5: broke below the confirmation candle's low",
    "recorded, not used: reversal/piercing candle body 0.80x, high-low 0.90x",
    "allowed at entry: Bollinger bounce in a trend up; direction rule buy side",
]


def test_the_bounce_reason_in_one_line():
    i = Idea("GBPUSD", BOLLINGER_BOUNCE, SELL, WED, D("13394.5"), "trend", "up", None, "buy side", BOUNCE_STEPS)
    assert one_line(i) == "bounce: pierced S2 13398.1 at 10:05, reversal 10:10, confirmed 10:15, broke it 10:20"


def test_a_pierce_again_starts_the_reason_again():
    steps = BOUNCE_STEPS[:2] + [BOUNCE_STEPS[0].replace("10:05", "10:15").replace("S2 13398.1", "R2 13401.0")] + BOUNCE_STEPS[2:4]
    i = Idea("GBPUSD", BOLLINGER_BOUNCE, SELL, WED, D("13394.5"), "trend", "up", None, "buy side", steps)
    assert one_line(i).startswith("bounce: pierced R2 13401.0 at 10:15, confirmed 10:15")


def test_the_level_reversals_level_and_how_far_past_it():
    i = Idea("GBPUSD", LEVEL_REVERSAL, SELL, WED, D("13394.5"), "trend", "up", None, "buy side", BOUNCE_STEPS,
             context={"level_name": "R2 13398.1", "past_level_pips": D("4.37")})
    assert level_note(i) == "R2 13398.1; price went 4.4 pips past it"
    assert one_line(i).startswith("level reversal: pierced S2 13398.1 at 10:05")
    short = Idea("GBPUSD", LEVEL_REVERSAL, SELL, WED, D("1"), "trend", "up", None, "", [],
                 context={"level_name": "round number 13400", "past_level_pips": D("-1.2")})
    assert level_note(short) == "round number 13400; price stopped 1.2 pips short of it"
    assert level_note(Idea("GBPUSD", BREAKOUT, SELL, WED, D("1"), "", "", None, "", [])) == ""


def test_other_strategies_reasons_come_from_their_steps():
    steps = ["Wed 04 Nov 09:50 GMT: the last low made: 13350.0",
             "Wed 04 Nov 09:55 GMT to 10:00 GMT: a pause: 2 candles in a row without a new low, closing below the 21 EMA; its lowest point 13351.0",
             "Wed 04 Nov 10:05 GMT: price broke below it (during this candle)", "allowed at entry: slow grind in a trend down"]
    text = one_line(Idea("GBPUSD", SLOW_GRIND, SELL, WED, D("13351.0"), "trend", "down", None, "", steps))
    assert text.startswith("slow grind: the last low made: 13350.0; ") and "price broke below it" in text
    assert "allowed at entry" not in text


def test_the_kind_of_take_profit(S):
    i = idea(EMA_PULLBACK, WED, SELL)
    assert take_profit_kind(S, i, 30, None) == "normal"
    assert take_profit_kind(S, i, 100, "down") == "100 for a trend day"
    assert take_profit_kind(S, i, 100, None) == "100 for a big-news day"
    assert take_profit_kind(S, idea(BREAKOUT, WED), 50, "down") == "normal"


# ---- the Telegram messages ------------------------------------------------------------------------------

def opened(**kw):
    base = dict(pair="GBPUSD", direction="sell", size_gbp_per_pip=D("10"), strategy="Bollinger bounce",
                market_state="trend up", open_price=D("13394.5"), stop_loss=D("13400.5"), take_profit=D("13294.5"),
                opened_utc=U(2026, 11, 4, 10, 20, 5), price_scale=10000, reference="AB261104102005-1a2b3c4d",
                stop_pips=D("6"), take_profit_pips=D("100"), take_profit_kind="normal",
                reason="bounce: pierced S2 13398.1 at 10:05, reversal 10:10, confirmed 10:15, broke it 10:20")
    return TradeOpened(**(base | kw))


def test_the_trade_opened_message_has_everything():
    lines = opened_text(opened()).splitlines()
    assert lines == ["AutoBot TRADE OPENED: GBPUSD SELL",
                     "Time: Wed 04 Nov 10:20 GMT",
                     "Deal reference: AB261104102005-1a2b3c4d",
                     "Size: £10 per pip",
                     "Strategy: Bollinger bounce",
                     "Market state: trend up",
                     "Open price: 13394.5 (1.33945) at Wed 04 Nov 10:20 GMT",
                     "Stop loss: 6.0 pips, 13400.5 (1.34005); £60.00 at risk",
                     "Take profit: 100 pips, 13294.5 (1.32945) (normal)",
                     "Reason: bounce: pierced S2 13398.1 at 10:05, reversal 10:10, confirmed 10:15, broke it 10:20"]


def test_the_level_reversal_and_a_big_news_take_profit_in_the_message():
    text = opened_text(opened(strategy="level reversal", level_note="R2 13398.1; price went 4.4 pips past it",
                              take_profit_pips=D("20"), take_profit_kind="normal"))
    assert "Level: R2 13398.1; price went 4.4 pips past it" in text
    text = opened_text(opened(strategy="EMA pullback", take_profit_kind="100 for a big-news day"))
    assert "Take profit: 100 pips, 13294.5 (1.32945) (100 for a big-news day)" in text


def test_the_trade_closed_message_has_everything():
    c = TradeClosed(opened(), D("13383.2"), U(2026, 11, 4, 11, 55), "a confirmed rejection at a level: S2 13383.0",
                    D("113.00"), D("11.3"), D("14.2"), today_trades=3, today_pips=D("8.4"))
    text = closed_text(c)
    assert text.splitlines()[0] == "AutoBot TRADE CLOSED: GBPUSD SELL - WIN +£113.00"
    for line in ("Deal reference: AB261104102005-1a2b3c4d", "Stop loss: 6.0 pips, 13400.5 (1.34005); £60.00 at risk",
                 "Close price: 13383.2 (1.33832) at Wed 04 Nov 11:55 GMT",
                 "Reason closed: a confirmed rejection at a level: S2 13383.0",
                 "Profit or loss: +11.3 pips, +£113.00 (win)", "Open for: 1 h 34 min",
                 "Best profit before closing: +14.2 pips", "Today so far: 3 trade(s), +8.4 pips"):
        assert line in text, line


def test_the_range_trades_half_close_and_rest_are_shown_apart():
    half = PartClose(U(2026, 11, 4, 10, 40), D("13386.0"), D("8.5"), D("42.50"), "the opposite Bollinger band")
    rest = PartClose(U(2026, 11, 4, 11, 5), D("13400.5"), D("-6"), D("-30.00"), "the stop at IG")
    c = TradeClosed(opened(strategy="range trade"), D("13400.5"), U(2026, 11, 4, 11, 5), "the stop at IG", D("12.50"),
                    D("1.25"), D("9"), half, rest, 1, D("1.25"))
    text = closed_text(c)
    assert "Half closed: 13386.0 (1.3386) at Wed 04 Nov 10:40 GMT, +8.5 pips, +£42.50 (the opposite Bollinger band)" in text
    assert "Rest closed: 13400.5 (1.34005) at Wed 04 Nov 11:05 GMT, -6.0 pips, -£30.00 (the stop at IG)" in text


def test_a_long_trade_shows_days():
    c = TradeClosed(opened(), D("13383.2"), U(2026, 11, 6, 12, 30), "Friday close", D("10"), D("1"))
    assert "Open for: 2 d 2 h 9 min" in closed_text(c)


# ---- the book ------------------------------------------------------------------------------------------

def closed_row(strategy, closed, pips, gbp):
    return {"strategy": strategy, "closed_utc": closed, "pips": str(pips), "gbp": str(gbp)}


def test_the_book_keeps_every_trade_and_decision_and_never_rewrites(S):
    b = Book(S)
    b.opened({"reference": "A", "strategy": BREAKOUT})
    b.closed(closed_row(BREAKOUT, "2026-11-04T10:30:00Z", D("20"), D("200")))
    b.decision("idea", WED, strategy=BREAKOUT, allowed=False, blocked_by="the state")
    first = b.trades_file.read_text()
    b.opened({"reference": "B", "strategy": SLOW_GRIND})
    assert b.trades_file.read_text().startswith(first)                    # appended, never rewritten
    assert [r["event"] for r in rows(b.trades_file)] == ["opened", "closed", "opened"]
    assert rows(b.decisions_file)[0] | {} == {"time_utc": "2026-11-04T10:00:00Z", "kind": "idea", "paper": False,
                                              "strategy": BREAKOUT, "allowed": False, "blocked_by": "the state"}


def test_paper_records_are_kept_apart(S):
    real, paper = Book(S), Book(S, paper=True)
    assert paper.folder == real.folder / "paper"


def test_the_daily_and_weekly_summaries(S):
    b = Book(S)
    b.closed(closed_row(BREAKOUT, "2026-11-02T10:30:00Z", D("50"), D("500")))           # Monday
    b.closed(closed_row(BREAKOUT, "2026-11-04T10:30:00Z", D("-6"), D("-60")))          # Wednesday
    b.closed(closed_row(SLOW_GRIND, "2026-11-04T15:00:00Z", D("20"), D("200")))
    b.closed(closed_row(SLOW_GRIND, "2026-11-05T00:30:00Z", D("15"), D("150")))         # Thursday
    s = b.write_daily(date(2026, 11, 4))
    assert (s.trades, s.wins, s.losses, s.pips, s.gbp) == (2, 1, 1, D("14"), D("140"))
    daily = json.loads((b.folder / "summaries" / "daily" / "2026-11-04.json").read_text())
    assert daily["by_strategy"][SLOW_GRIND] == {"trades": 1, "wins": True, "losses": False, "pips": "20", "gbp": "200"} \
        or daily["by_strategy"][SLOW_GRIND]["pips"] == "20"
    weekly = json.loads((b.folder / "summaries" / "weekly" / "2026-W45.json").read_text())
    assert (weekly["trades"], weekly["pips"], weekly["from"], weekly["to"]) == (3, "64", "2026-11-02", "2026-11-04")
    text = daily_text("GBPUSD", date(2026, 11, 4), s, b.summary(date(2026, 11, 2), date(2026, 11, 4)), False)
    assert text.splitlines()[0] == "AutoBot DAILY SUMMARY GBPUSD Wed 04 Nov 2026"
    assert "Trades closed today: 2 (1 won, 1 lost)" in text and "Pips: +14.0; +£140.00" in text
    assert "This week so far: 3 trades, +64.0 pips, +£640.00" in text
    assert "(paper trades: TRADING is off)" in daily_text("GBPUSD", date(2026, 11, 4), s, s, True)


# ---- the engine: records, Telegram, the pause switch, the daily summary -------------------------------------

def test_a_real_trade_is_recorded_and_sent_on_telegram_when_it_opens_and_closes(S, monkeypatch):
    stop = candle(WED + timedelta(minutes=15), 100, 110, 99.5, 109)
    cs = C[:3] + [stop] + C[4:]
    e, ig, tracker, clock, quote = make(S, monkeypatch, cs, {C[1].start: [idea(BREAKOUT, C[1].start)]}, trading_on=True)
    real_fill = ig._fill

    def fill_at_100(ref, body, confirm=True):                                # IG fills at the made-up candles' price
        real_fill(ref, body, confirm)
        ig.positions[-1]["position"]["level"] = 100.0
        ig.confirms[ref]["level"] = 100.0
    ig._fill = fill_at_100
    e.start(WED)
    feed(e, clock, cs[:3])
    ig.positions.clear()                                                     # IG's stop closed it
    feed(e, clock, cs[3:4])
    trades = rows(e.book.trades_file)
    assert [r["event"] for r in trades] == ["opened", "closed"]
    o, c = trades
    assert (o["strategy"], o["direction"], o["stop_pips"], o["take_profit_pips"], o["take_profit_kind"]) == \
        (BREAKOUT, "sell", "6", "50", "normal")
    assert c["how_closed"] == "stopped by IG" and D(c["pips"]) == D("-6") and D(c["gbp"]) == D("-60") and c["result"] == "loss"
    assert c["minutes_open"] == 5 and c["opened_utc"] == "2026-11-04T10:10:00Z"           # live: at the market after its candle
    alerts = e.alerts
    assert len(alerts.opened) == 1 and alerts.opened[0].reference == o["reference"]
    (closed,) = alerts.closed
    assert closed.profit_gbp == D("-60") and closed.today_trades == 1 and closed.today_pips == D("-6")


def test_paper_trades_are_recorded_but_send_no_trade_messages(S, monkeypatch):
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, {C[1].start: [idea(BREAKOUT, C[1].start)]})
    e.start(WED)
    feed(e, clock, C[:3])
    assert e.book.paper and rows(e.book.trades_file)[0]["paper"] is True and e.alerts.opened == []


def test_every_decision_is_recorded(S, monkeypatch):
    ideas = {C[1].start: [idea(BREAKOUT, C[1].start), idea(SLOW_GRIND, C[1].start, allowed=False)]}
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, ideas)
    e.start(WED)
    tracker.changes.append(SimpleNamespace(time=C[1].start, state="trend", direction="down", trend_type="slow grind",
                                           line=lambda: "trend down (slow grind)"))
    feed(e, clock, C[:3])
    kinds = [r["kind"] for r in rows(e.book.decisions_file)]
    assert "analyser state change" in kinds and kinds.count("idea") == 2 and "order" in kinds
    blocked = [r for r in rows(e.book.decisions_file) if r["kind"] == "idea" and not r["allowed"]][0]
    assert blocked["blocked_by"] == "made up block"


def test_trade_manager_decisions_are_recorded(S, monkeypatch):
    t0 = U(2026, 11, 4, 20, 15)
    cs = [candle(t0 + timedelta(minutes=5 * k), 100, 100.5, 99.5, 100) for k in range(4)]
    e, ig, tracker, clock, quote = make(S, monkeypatch, cs, {cs[0].start: [idea(SLOW_GRIND, cs[0].start)]}, clock={"t": t0})
    e.start(t0)
    feed(e, clock, cs[:4])
    tm = [r for r in rows(e.book.decisions_file) if r["kind"] == "trade manager"]
    assert tm and tm[-1]["decision"] == "forced close" and tm[-1]["why"] == "20:30 UK close"


def test_the_pause_switch_stops_new_trades_and_open_trades_keep_running(S, monkeypatch):
    stop = candle(WED + timedelta(minutes=15), 100, 110, 99.5, 109)
    cs = C[:3] + [stop] + C[4:]
    ideas = {C[1].start: [idea(BREAKOUT, C[1].start)], C[2].start: [idea(SLOW_GRIND, C[2].start)]}
    e, ig, tracker, clock, quote = make(S, monkeypatch, cs, ideas, trading_on=True)
    e.start(WED)
    feed(e, clock, cs[:2])                                                   # the breakout opens
    S.trading.pause_file.parent.mkdir(parents=True, exist_ok=True)
    S.trading.pause_file.write_text("")                                      # paused
    feed(e, clock, cs[2:3])
    ig.positions.clear()                                                     # IG's stop closed the breakout
    feed(e, clock, cs[3:4])
    assert len(ig.orders_sent()) == 1                                        # the slow grind was not sent
    refused = [r for r in rows(e.sender.journal) if r["event"] == "safety refused"][0]
    assert refused["reasons"] == ["the pause switch is on: no new trades"]
    assert rows(e.book.trades_file)[-1]["event"] == "closed"                  # the open trade still ran to its stop
    assert any(r["kind"] == "pause switch" and r["paused"] for r in rows(e.book.decisions_file))


def test_the_daily_summary_at_20_35_uk_once(S, monkeypatch):
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, {})
    e.start(WED)
    e.book.closed(closed_row(BREAKOUT, "2026-11-04T10:30:00Z", D("20"), D("200")))
    e.daily_summary(U(2026, 11, 4, 20, 34))
    assert e.alerts.infos == []
    e.daily_summary(U(2026, 11, 4, 20, 35))
    e.daily_summary(U(2026, 11, 4, 20, 40))
    (text,) = e.alerts.infos
    assert text.startswith("AutoBot DAILY SUMMARY GBPUSD Wed 04 Nov 2026 (paper trades") and "+20.0" in text
    assert (e.book.folder / "summaries" / "daily" / "2026-11-04.json").exists()
    e.daily_summary(U(2026, 11, 7, 20, 40))                                  # Saturday: none
    assert len(e.alerts.infos) == 1


def test_the_daily_summary_comes_from_the_latest_price(S, monkeypatch):
    e, ig, tracker, clock, quote = make(S, monkeypatch, C, {})
    e.start(WED)
    e.on_price(tick(U(2026, 11, 4, 20, 36), 100))
    assert len(e.alerts.infos) == 1
