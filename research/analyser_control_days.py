"""Replay of whole UK days through the full wired path (trading/engine.py in paper mode, a pretend IG, the stored
candles), with the analyser control switches (ANALYSER_USES_HOURLY, ANALYSER_GOVERNS_ALL, ONE_SIGNAL_ONE_TRADE; owner,
18 November 2026) on or off. It lists, for one UK day: the analyser's state changes, the trades that opened (with how
they closed), the ideas the checks blocked and the orders the safety rules refused, each with its reasons.

For checking that the code does what the owner's rules say on named days (tests/functional/
test_analyser_control_real_candles.py and docs/research/analyser_control_20261118/). It is never used to judge whether
a rule makes money: no totals.

Reads the candle store and the calendar; never contacts IG; writes only to a temporary folder. The switches are fixed
here (the values on the live .env on 18 November 2026, TRADING off), never read from .env:

    .venv/bin/python -m research.analyser_control_days 2026-11-17 [on|off [edge_pips [result.json]]]
"""

from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from prices.calendar import MarketHours
from prices.store import CandleStore
from trading.replay_check import _Alerts, _Over, _PretendIG

UK = ZoneInfo("Europe/London")
CONTROL = ("ANALYSER_USES_HOURLY", "ANALYSER_GOVERNS_ALL", "ONE_SIGNAL_ONE_TRADE")
# The live switches on 18 November 2026 (TRADING off: paper trades only).
BASE_SWITCHES = {
    "PAIRS_ON": "GBPUSD", "NEW_TRADES_FROM": "06:00", "NEW_TRADES_UNTIL": "20:30",
    "STRATEGY_SLOW_GRIND": "on", "STRATEGY_EMA_PULLBACK": "on", "STRATEGY_BOLLINGER_BOUNCE": "on",
    "STRATEGY_RANGE_TRADE": "on", "STRATEGY_BREAKOUT": "on", "STRATEGY_LEVEL_REVERSAL": "on",
    "STRATEGY_ASIAN_RANGE_BREAKOUT": "on", "STRATEGY_SESSION_SWEEP": "on", "STRATEGY_NEW_YORK_OPEN_REVERSAL": "on",
    "HOURLY_READ": "on", "BOUNCE_ONLY_WHEN_HOURLY_RANGING": "off", "BOUNCE_ONLY_NEAR_TIMES": "off",
    "TREND_STILL_GOING": "on", "PLANNER_OBSERVE": "off", "TRADING": "off",
    "STOP_LOSS_PIPS": "12", "STOP_LOSS_PIPS_EMA_PULLBACK": "12", "TAKE_PROFIT_PIPS": "100",
}
TREND_GROUP = ("slow grind", "EMA pullback", "breakout", "Asian range breakout")


@dataclass
class Trade:
    opened: datetime
    strategy: str
    direction: str
    entry: Decimal
    pips: Decimal
    closed: str                         # how it closed (the trade manager's last decision)
    reference: str = ""

    def line(self) -> str:
        return (f"{self.opened.astimezone(UK):%H:%M} {self.strategy} {self.direction} at {self.entry}: "
                f"{self.pips:+.1f} ({self.closed})")


@dataclass
class Day:
    day: date
    switches: str
    changes: list = field(default_factory=list)     # StateChange, in the UK day
    trades: list = field(default_factory=list)      # Trade
    blocked: list = field(default_factory=list)     # (time, strategy, direction, blocked_by), ideas the checks blocked
    refused: list = field(default_factory=list)     # (time, strategy, direction, reasons), orders the safety refused
    journal: list = field(default_factory=list)     # the trade manager's decisions (dicts), every trade of the day


class EdgeSettings:
    """The settings with analyser_control.edge_within_pips replaced (the owner asked for runs at 3 and 5 pips; the
    file's own value is not changed)."""
    def __init__(self, base, edge):
        from types import SimpleNamespace
        self._base = base
        self.analyser_control = SimpleNamespace(
            edge_within_pips=Decimal(str(edge)),
            consolidation_breakout_beyond_pips=base.analyser_control.consolidation_breakout_beyond_pips)

    def __getattr__(self, name):
        return getattr(self._base, name)


def settings_with(control_on: bool, folder: Path, edge=None, **extra: str):
    """The real settings.toml with BASE_SWITCHES, the three control switches all on or all off, and `extra`;
    `edge`: analyser_control.edge_within_pips instead of the file's (None: the file's)."""
    from config.settings_loader import load_settings
    values = dict(BASE_SWITCHES) | {k: ("on" if control_on else "off") for k in CONTROL} | extra
    p = folder / "switches.env"
    p.write_text("".join(f"{k}={v}\n" for k, v in values.items()))
    s = load_settings(switches_from=p).for_pair("GBPUSD")
    return s if edge is None else EdgeSettings(s, edge)


def run_day(day: date, control_on: bool, edge=None, **extra: str) -> Day:
    """Replay the week of `day` from its open to the end of that UK day through the full wired path."""
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        base = settings_with(control_on, tmpdir, edge, **extra)
        s = _Over(base, tmpdir)
        store = CandleStore(base.candles.folder, base.candles.compress_after_days)
        hours = MarketHours(base.market_hours)
        start = datetime.combine(day, time(0, 0), tzinfo=UK)
        end = start + timedelta(days=1)
        week_open, week_close = hours.session(start + timedelta(hours=12))
        end = min(end, week_close)
        from trading.engine import Trading
        clock = {"t": week_open}
        engine = Trading(s, store, _PretendIG(), _Alerts(), trading_on=False, now=lambda: clock["t"], replay_end=end)
        engine.start(week_open)
        for c in store.read_range("5m", week_open, end):
            if c.end > end:
                break
            clock["t"] = c.start
            engine.on_candle(c.end)
        out = Day(day, ("on" if control_on else "off") + (f", edge {edge} pips" if edge is not None else ""))
        out.changes = [ch for ch in engine.tracker.changes if start <= ch.time < end]
        for idea, mt in engine.opened:
            if not start <= idea.time < end:
                continue
            last = mt.decisions[-1] if mt.decisions else None
            closed = (f"{last.kind}: {last.why}" if last is not None and not mt.open else "still open at the day's end")
            out.trades.append(Trade(idea.time, idea.strategy, idea.direction, idea.entry_price, mt.total_pips(), closed,
                                    mt.reference))
        rec = Path(s.records.folder)
        for p in rec.rglob("decisions.jsonl"):
            for line in p.read_text().splitlines():
                r = json.loads(line)
                t = datetime.fromisoformat(r["time_utc"].replace("Z", "+00:00"))
                if not start <= t < end:
                    continue
                if r["kind"] == "idea" and not r.get("allowed"):
                    out.blocked.append((t, r["strategy"], r["direction"], r.get("blocked_by", "")))
        for p in Path(s.orders.folder).rglob("*orders.jsonl"):      # paper_orders.jsonl in paper mode
            for line in p.read_text().splitlines():
                r = json.loads(line)
                if r.get("event") != "safety refused":
                    continue
                t = datetime.fromisoformat(r["time_utc"].replace("Z", "+00:00"))
                if start <= t < end:
                    out.refused.append((t, r.get("strategy"), r.get("direction"), r.get("reasons", [])))
        tm = Path(s.trade_manager.folder)
        for p in tm.rglob("decisions.jsonl"):
            out.journal += [json.loads(line) for line in p.read_text().splitlines()]
        out.blocked.sort(key=lambda x: x[0])
        out.refused.sort(key=lambda x: x[0])
        return out


def ideas_day(day: date, control_on: bool, edge=None, **extra: str) -> tuple[list, list, object]:
    """The faster check (the tests): the week of `day` replayed once through the analyser and the strategies, as the
    live service runs them (strategies/replay.py), with every candidate checked at entry (switch, state, direction
    rule, hourly read, trend still going, check 7). No safety rules, no trade manager. Returns (the state changes of
    the UK day, its ideas allowed or blocked, the strategy runner)."""
    from analyser.market_state import MemoStore, StateTracker
    from strategies.replay import StrategyRunner
    with tempfile.TemporaryDirectory() as tmp:
        s = settings_with(control_on, Path(tmp), edge, **extra)
    store = MemoStore(CandleStore(s.candles.folder, s.candles.compress_after_days))
    hours = MarketHours(s.market_hours)
    start = datetime.combine(day, time(0, 0), tzinfo=UK)
    end = min(start + timedelta(days=1), hours.session(start + timedelta(hours=12))[1])
    tracker = StateTracker(s, store)
    tracker.replay(end)
    runner = StrategyRunner(s, store, tracker, hourly_end=end)
    ideas = [idea for c, idea in runner.step() if start <= c.start < end]
    changes = [ch for ch in tracker.changes if start <= ch.time < end]
    return changes, ideas, runner


def as_json(d: Day) -> dict:
    return {"day": d.day.isoformat(), "switches": d.switches,
            "changes": [{"time_uk": f"{ch.time.astimezone(UK):%H:%M}", "state": ch.state, "direction": ch.direction,
                         "trend_type": ch.trend_type, "hourly_position": getattr(ch, "hourly_position", None),
                         "reason": ch.reason} for ch in d.changes],
            "trades": [{"opened_uk": f"{t.opened.astimezone(UK):%H:%M}", "strategy": t.strategy,
                        "direction": t.direction, "entry": str(t.entry), "pips": f"{t.pips:+.1f}", "closed": t.closed,
                        "reference": t.reference}
                       for t in d.trades],
            "refused": [{"time_uk": f"{t.astimezone(UK):%H:%M}", "strategy": s, "direction": di, "reasons": r}
                        for t, s, di, r in d.refused],
            "blocked": [{"time_uk": f"{t.astimezone(UK):%H:%M}", "strategy": s, "direction": di, "blocked_by": b}
                        for t, s, di, b in d.blocked],
            "journal": d.journal}


def show(d: Day) -> list[str]:
    out = [f"{d.day:%a %d %b %Y}, analyser control switches {d.switches}", "State changes:"]
    out += [f"  {ch.time.astimezone(UK):%H:%M} {ch.state} ({ch.direction}"
            f"{', ' + ch.trend_type if ch.trend_type else ''})"
            f"{' [' + ch.hourly_position + ']' if getattr(ch, 'hourly_position', None) else ''}: {ch.reason}"
            for ch in d.changes]
    out.append("Trades opened:")
    out += [f"  {t.line()}" for t in d.trades] or ["  none"]
    out.append("Orders the safety rules refused:")
    out += [f"  {t.astimezone(UK):%H:%M} {s} {di}: {'; '.join(r)}" for t, s, di, r in d.refused] or ["  none"]
    return out


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print(__doc__)
        return 2
    day = date.fromisoformat(args[0])
    modes = [args[1] == "on"] if len(args) > 1 else [False, True]
    edge = args[2] if len(args) > 2 else None
    for on in modes:
        d = run_day(day, on, edge)
        print("\n".join(show(d)))
        print()
        if len(args) > 3:                                   # also keep the result as JSON for the report
            Path(args[3]).write_text(json.dumps(as_json(d), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
