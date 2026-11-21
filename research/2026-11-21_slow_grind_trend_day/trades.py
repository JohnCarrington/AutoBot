"""Phase 1 (research only): every slow grind idea the live code (4635175, live .env switches) makes on the
validated store, and the trades they would become, managed by the live trade manager's step().

Same path as strategies.replay.StrategyRunner.step for the slow grind: the analyser's StateTracker for the week,
the week's warm-up candles, the 21 EMA on warm-up + week (sell price), SlowGrind.on_candle, then
strategies.common.check with the state after the previous candle, the pivot and the 100 EMA. The other
strategies are not run (they do not feed the slow grind).

Trades (as trade_manager/replay_check.py): may_open (hours, with the Finnhub past calendar), one slow grind trade
open at a time (limits.max_open_trades_per_strategy = 1), fill = entry for a sell, entry + the entry candle's
spread for a buy; trade_manager.manager.plan (stop 15, TP 20 / 100 on a big-news day or trend day, lock 15/10,
20:30 close) and step() bar by bar.

Writes one JSON line per week to out/weeks.jsonl (resumable).
"""
from __future__ import annotations

import json
import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from analyser.indicators import last_candles
from analyser.market_state import MemoStore, StateTracker
from analyser.trend_day import trend_day_at
from config.settings_loader import load_settings
from levels.current import build
from levels.rules import PIVOT
from prices.calendar import MarketHours
from prices.indicators import ema
from prices.model import parse_iso
from prices.store import CandleStore
from strategies.common import SLOW_GRIND, check, may_open
from strategies.replay import StrategyRunner
from strategies.slow_grind.strategy import SlowGrind
from trade_manager.manager import Bar, plan, step

ENV, CAL, OUT = sys.argv[1], sys.argv[2], Path(sys.argv[3])
FIRST, LAST = parse_iso(sys.argv[4]), parse_iso(sys.argv[5])

s = load_settings(switches_from=ENV).for_pair("GBPUSD")
store = CandleStore(s.candles.folder, 999999)
hours = MarketHours(s.market_hours)
calendar = json.load(open(CAL))["events"]
ppp = Decimal(s.market.points_per_pip)
side = s.chart.price
OUT.mkdir(parents=True, exist_ok=True)
done = set()
wf = OUT / "weeks.jsonl"
if wf.exists():
    done = {json.loads(x)["week_open"] for x in wf.read_text().splitlines() if x.strip()}

t = FIRST
weeks = []
while t < LAST:
    o, c = hours.session(t)
    if o >= FIRST - timedelta(days=7) and (not weeks or weeks[-1][0] != o):
        weeks.append((o, c))
    t += timedelta(days=7)

open_until = None          # the close bar start of the slow grind trade still open (carried across weeks: never)
for o, c in weeks:
    key = o.strftime("%Y-%m-%dT%H:%M:%SZ")
    if key in done:
        continue
    memo = MemoStore(store)
    tracker = StateTracker(s, memo)
    tracker.replay(c)
    rec = {"week_open": key, "week_close": c.strftime("%Y-%m-%dT%H:%M:%SZ"), "ideas": [], "trades": []}
    if not tracker.history:
        with wf.open("a") as f:
            f.write(json.dumps(rec) + "\n")
        continue
    runner = StrategyRunner(s, memo, tracker, hourly_end=c)
    runner._fresh()
    runner.week_open = tracker.week_open
    warm = last_candles(runner.memo, "5m", runner.week_open, s.market_states.indicator_warm_up_candles)
    week = [f.candle for f, *_ in tracker.history]
    runner.week = week
    runner.pivots = {}
    allc = warm + week
    sg_ema = ema(allc, side, s.slow_grind.ema_periods)
    ema100 = ema(allc, side, s.analyser.direction_ema_periods)
    grind = SlowGrind(s)
    ideas = []
    for i, cd in enumerate(week):
        cands = grind.on_candle(cd, sg_ema.get(cd.start))
        if cands:
            st = runner.state_after(i - 1)
            e100 = ema100.get(week[i - 1].start) if i > 0 else None
            for cand in cands:
                ideas.append(check(s, s.market.pair, cand, st, runner.pivot_at(cd.start), e100))
    index = {cd.start: k for k, cd in enumerate(week)}
    open_close = None
    for idea in ideas:
        why = []
        if not idea.allowed:
            why.append("blocked: " + idea.blocked_by)
        else:
            why += may_open(s, s.market.pair, SLOW_GRIND, idea.time, calendar)
            if open_close is not None and open_close > idea.time:
                why.append("a slow grind trade is already open")
        rec["ideas"].append({"time": idea.time.strftime("%Y-%m-%dT%H:%M:%SZ"), "direction": idea.direction,
                             "entry": str(idea.entry_price), "state": idea.state, "state_direction": idea.state_direction,
                             "trend_type": idea.trend_type, "allowed": idea.allowed, "refused": why})
        if why:
            continue
        sell = idea.direction == "sell"
        first = week[index[idea.time]]
        fill = idea.entry_price if sell else idea.entry_price + (first.buy_open - first.sell_open)
        td = trend_day_at(s, store, idea.time).direction
        tr = plan(s, "r", SLOW_GRIND, idea.direction, idea.time, idea.entry_price, fill, Decimal(s.slow_grind.stop_loss_pips),
                  calendar, trend_day=td)
        bars = []
        closed = week[-1].start
        for cd in week[index[idea.time]:]:
            ds = step(s, tr, Bar.of(cd))
            bars.append(cd.start.strftime("%Y-%m-%dT%H:%M:%SZ"))
            if not tr.open:
                closed = cd.start
                break
        open_close = closed
        d = tr.decisions[-1] if tr.decisions else None
        rec["trades"].append({"opened": idea.time.strftime("%Y-%m-%dT%H:%M:%SZ"), "direction": idea.direction,
                              "entry": str(idea.entry_price), "fill": str(fill), "tp": str(tr.take_profit_pips),
                              "trend_day": td, "closed_bar": closed.strftime("%Y-%m-%dT%H:%M:%SZ"),
                              "close_kind": d.kind if d else "still open at week end",
                              "close_price": str(d.price) if d else None,
                              "pips": str(tr.total_pips()) if d else None,
                              "why": d.why if d else None})
    with wf.open("a") as f:
        f.write(json.dumps(rec) + "\n")
    print(key, len(ideas), sum(i.allowed for i in ideas), len(rec["trades"]), flush=True)
