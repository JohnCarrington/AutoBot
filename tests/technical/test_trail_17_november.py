"""The 17 November 2026 Bollinger bounce sell (AB261117100502-941a3fa2) replayed through the fixed trail (owner,
17 November 2026): the real trade manager and the real order sender, with the pretend IG of test_orders.py.

The trade: sold at 13189.9 at 10:05 UTC, stop 13201.9 (12 pips), take profit 13089.9; best 15.6 pips up in the 13:35
candle. Live, the trail moved the stop to 13193.2 at 13:40, then IG refused 13181.6 31 times from 13:50 to 14:06
(ATTACHED_ORDER_LEVEL_ERROR) and the trade was stopped at 13193.2 (-3.3).

The candles below are the stored IG 5-minute candles of that afternoon (data/candles/GBPUSD/5m/2026-11-17.csv), both
prices. IG's prices at each move are not stored: as live, the trail runs about 2 seconds after a candle finishes, so
IG's buy and sell prices then are taken as the next candle's open. IG's minimum stop distance that day is not known
(no record was kept); it is taken as 2 points here, which fits what happened live: at 13:50:02 IG's buy price was
about 13180.2 and IG refused 13181.6, 1.4 above it. Nothing here contacts IG."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal as D

from strategies.common import BOLLINGER_BOUNCE, SELL
from tests.technical.test_orders import S, idea, make, records  # noqa: F401  (S is the fixture)
from tests.technical.test_trade_manager import Over
from trade_manager.manager import Bar, TradeManager, plan

U = lambda *a: datetime(*a, tzinfo=timezone.utc)  # noqa: E731
FILL, STOP, LIMIT = D("13189.9"), D("13201.9"), D("13089.9")
IG_MIN_STOP = 2.0          # points (= pips for GBPUSD); see above

# start (UTC), buy open, high, low, close, sell open, high, low, close: 17 November 2026, as stored
CANDLES = [
    ("13:10", "13192.2", "13193.2", "13190.4", "13191.4", "13190.7", "13191.7", "13188.9", "13189.9"),
    ("13:15", "13191.3", "13193.7", "13187.5", "13187.5", "13189.8", "13192.2", "13186", "13186"),
    ("13:20", "13187.1", "13189.7", "13184.5", "13189.2", "13185.6", "13188.2", "13183", "13187.7"),
    ("13:25", "13188.7", "13192.4", "13188.3", "13191.6", "13187.2", "13190.9", "13186.8", "13187"),
    ("13:30", "13193.1", "13193.1", "13180.2", "13180.9", "13186.6", "13186.6", "13178.7", "13179.4"),
    ("13:35", "13181.2", "13181.2", "13174.3", "13174.8", "13179.7", "13179.7", "13172.8", "13173.3"),
    ("13:40", "13174.5", "13181.2", "13174.5", "13178.2", "13173", "13180.3", "13173", "13176.7"),
    ("13:45", "13178", "13181.5", "13177.8", "13180.5", "13176.5", "13180.1", "13176.3", "13179.6"),
    ("13:50", "13180.2", "13185", "13180.1", "13185", "13179.3", "13183.5", "13178.8", "13183.5"),
    ("13:55", "13184.7", "13189.7", "13182.5", "13188.4", "13183.2", "13188.2", "13181", "13186.9"),
    ("14:00", "13188.5", "13192.7", "13183.3", "13191.7", "13187", "13191.4", "13181.8", "13190.2"),
]


def bar(row):
    h, m = map(int, row[0].split(":"))
    return Bar(U(2026, 11, 17, h, m), *(D(x) for x in row[1:]))


def the_trade(S, tmp_path):
    """The sell open at the pretend IG with its real fill, stop and take profit, and in a trade manager that waits
    for IG's confirmations (as live)."""
    sender, ig, alerts, sleeps, clock = make(S)
    r = sender.place(idea(BOLLINGER_BOUNCE, SELL), calendar=[])
    pos = next(p for p in ig.positions if p["position"]["dealId"] == r.deal_id)
    pos["position"].update(level=float(FILL), stopLevel=float(STOP), limitLevel=float(LIMIT))
    ig.min_stop = IG_MIN_STOP
    s = Over(S, trade_manager={"folder": tmp_path / "tm"})
    m = TradeManager(s, sender, ig_confirms=True, now=lambda: clock["t"])
    m.add(plan(s, r.reference, BOLLINGER_BOUNCE, SELL, U(2026, 11, 17, 10, 5), D("13190.1"), FILL, D(12), []))
    return sender, ig, alerts, clock, m, pos, r


def igs_prices(pos, buy, sell):
    pos["market"].update(bid=float(sell), offer=float(buy))


def feed(sender, ig, clock, m, pos, rows, upto):
    """Each finished candle up to `upto`, the trail running 2 seconds after it with IG's prices at the next
    candle's open. Returns, per candle, the moves the order sender recorded."""
    shown = []
    for k, row in enumerate(rows):
        if row[0] > upto:
            break
        nxt = rows[k + 1]
        clock["t"] = bar(nxt).start + timedelta(seconds=2)
        igs_prices(pos, nxt[1], nxt[5])
        before = len(records(sender))
        m.on_bar(bar(row), finished=True)
        got = [(x["event"], x.get("rule_level"), x.get("stop_level"), x.get("ig_offer"))
               for x in records(sender)[before:] if x["event"].startswith("stop")]
        shown.append((row[0], got))
    return shown


def test_the_17_november_sell_through_the_fixed_trail(S, tmp_path):
    sender, ig, alerts, clock, m, pos, r = the_trade(S, tmp_path)
    shown = feed(sender, ig, clock, m, pos, CANDLES, upto="13:45")
    print("\nAfter each candle: the stop move the fixed code sends (rule's level, level sent, IG's buy price then)")
    for start, got in shown:
        print(f"  {start}: {got or 'nothing'}")
    assert shown == [
        ("13:10", []), ("13:15", []), ("13:20", []), ("13:25", []), ("13:30", []),     # not yet 12 pips up
        # 15.6 up: 0.1 above the 13:25/13:30/13:35 buy highs (13193.1); IG's buy price 13174.5: sent as it is
        ("13:35", [("stop move sending", "13193.2", "13193.2", "13174.5"), ("stop moved", None, "13193.2", None)]),
        ("13:40", []),                                                  # 13193.2 again: not closer than IG's stop
        # the rule gives 13181.6, inside IG's minimum of IG's buy price 13180.2: sent as 13182.2, which IG accepts
        ("13:45", [("stop move sending", "13181.6", "13182.2", "13180.2"), ("stop moved", None, "13182.2", None)]),
    ]
    tr = m.trades[r.reference]
    assert tr.stop_level == D("13182.2") and tr.open
    assert bar(CANDLES[8]).buy_high >= tr.stop_level          # the 13:50 candle's buy price reaches it (13185.0)
    assert alerts.sent == []
    sending = [x for x in records(sender) if x["event"] == "stop move sending"]
    assert all(x["ig_min_stop_pips"] == "2.0" and x["ig_bid"] is not None for x in sending)   # recorded every time


def test_the_17_november_sell_when_ig_refuses_3_times_then_the_next_candles_level(S, tmp_path):
    sender, ig, alerts, clock, m, pos, r = the_trade(S, tmp_path)
    feed(sender, ig, clock, m, pos, CANDLES, upto="13:40")            # the 13:40 move to 13193.2, as live
    ig.move_answer = "reject"                                         # from now IG refuses every move
    feed(sender, ig, clock, m, pos, CANDLES[7:], upto="13:45")        # 13:50:02: 13182.2 refused (1 of 3)
    for t in ("13:50:33", "13:51:04", "13:51:40"):                    # live prices: retries 30 seconds apart
        clock["t"] = datetime.fromisoformat(f"2026-11-17T{t}+00:00")
        m.on_bar(Bar(clock["t"], *[D("13180.2")] * 4, *[D("13179.3")] * 4))
    sent = [x["stop_level"] for x in records(sender) if x["event"] == "stop move sending"]
    assert sent == ["13193.2", "13182.2", "13182.2", "13182.2"]       # 3 attempts at the level, then no more
    (key, text), = alerts.sent                                        # one alert, when it gave up
    assert key == f"stop-move-gave-up-{r.reference}" and "13182.2" in text and "13193.2" in text
    tr = m.trades[r.reference]
    assert tr.stop_level == D("13193.2") and tr.trail_want is None
    # the next finished candle: 0.1 above the 13:40/13:45/13:50 buy highs is 13185.1, closer than IG's 13193.2
    # (the old code compared it with the refused 13182.2 and sent nothing); IG's buy price 13184.7 at 13:55:02
    feed(sender, ig, clock, m, pos, CANDLES[8:], upto="13:50")
    last = [x for x in records(sender) if x["event"] == "stop move sending"][-1]
    assert (last["rule_level"], last["stop_level"], last["ig_offer"]) == ("13185.1", "13186.7", "13184.7")
