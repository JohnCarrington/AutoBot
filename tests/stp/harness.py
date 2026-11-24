"""Offline helpers for the STP integration tests (owner, 24 November 2026; docs/design/STP_STRATEGY_INTEGRATION_20261124.md
sections 13 and 14). Read-only on the candle store; every file goes to a temporary folder; IG is never contacted."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

UTC = timezone.utc
LIVE_DATA = Path("/opt/autobot/data/candles/GBPUSD/5m/2026-11-24.csv")


class Over:
    """The real settings with chosen switches and folders replaced (nothing else changes)."""

    def __init__(self, base: Any, folder: Path, switches: dict | None = None):
        self._base = base
        self.switches = SimpleNamespace(**(vars(base.switches) | (switches or {})))
        self.planner = SimpleNamespace(**(vars(base.planner) | {"folder": folder / "planner"}))
        for name in ("orders", "trade_manager", "safety", "records", "dashboard", "trading", "levels"):
            sec = getattr(base, name, None)
            if sec is None:
                continue
            extra = {"folder": folder / name} if hasattr(sec, "folder") else {}
            if name == "trading":
                extra = {"pause_file": folder / "control" / "pause"}
            if name == "dashboard":
                extra = {"status_folder": folder / "status"}
            if name == "levels":
                extra = {}
            setattr(self, name, SimpleNamespace(**(vars(sec) | extra)))

    def __getattr__(self, name: str) -> Any:
        return getattr(self._base, name)

    def for_pair(self, pair: str) -> "Over":
        return self


# The live .env switch values on 24 November 2026 (switches only; the real .env is never read by the tests), with
# TRADING off: the order sender in paper mode. The three STP switches are added by each test.
LIVE_SWITCHES_20261124 = """\
PAIRS_ON=GBPUSD
NEW_TRADES_FROM=06:00
NEW_TRADES_UNTIL=20:30
STRATEGY_SLOW_GRIND=on
STRATEGY_EMA_PULLBACK=on
STRATEGY_BOLLINGER_BOUNCE=on
STRATEGY_BOLLINGER_BOUNCE_5M=on
BOUNCE_ONLY_NEAR_TIMES=off
PLANNER_OBSERVE=on
ONE_SIGNAL_ONE_TRADE=on
PULLBACK_ENTRY=on
EMA_PULLBACK_TRADING_HOURS=on
EMA_PULLBACK_ONE_AT_A_TIME=on
HOURLY_CONTEXT=on
ENTRY_NEAR_EMA8=off
RSI_STRETCH=on
TREND_DAY_RSI_OFF=on
EMERGING_LADDER=on
COUNTER_TREND_TIRING=on
COUNTER_TREND_EMERGING=on
TREND_ENDS_IN_CONSOLIDATION=on
COUNTER_TREND_HOURLY_CONFIRMED=on
STRATEGY_RANGE_TRADE=on
STRATEGY_BREAKOUT=on
STRATEGY_LEVEL_REVERSAL=on
STRATEGY_ASIAN_RANGE_BREAKOUT=on
STRATEGY_SESSION_SWEEP=on
STRATEGY_NEW_YORK_OPEN_REVERSAL=on
TRADING=off
STOP_LOSS_PIPS=12
STOP_LOSS_PIPS_EMA_PULLBACK=12
TAKE_PROFIT_PIPS=100
"""


def live_settings(folder: Path | None = None, **stp: bool):
    """The real settings.toml with the 24 November switch values; `stp`: STP_OPPORTUNITIES=True and so on."""
    import tempfile
    from config.settings_loader import load_settings
    folder = Path(folder or tempfile.mkdtemp())
    folder.mkdir(parents=True, exist_ok=True)
    text = LIVE_SWITCHES_20261124 + "".join(f"{k.upper()}={'on' if v else 'off'}\n" for k, v in stp.items())
    p = folder / "switches.env"
    p.write_text(text)
    return load_settings(switches_from=p).for_pair("GBPUSD")


def live_store(s: Any):
    from prices.store import CandleStore
    return CandleStore(s.candles.folder, s.candles.compress_after_days)


ON = {"stp_opportunities": True, "stp_bidirectional": True}


def run_tracker(s: Any, store: Any, start: datetime, end: datetime, step_minutes: int = 5,
                seconds_after: int = 3) -> list[dict]:
    """The STP tracker as the price service runs it: after each finished 5-minute candle (plus `seconds_after`), from
    `start` to `end`. Returns a snapshot of current.json after every run."""
    from planner.opportunities import make_keeper
    snaps = []
    t = start
    while t <= end:
        now = t + timedelta(seconds=seconds_after)
        make_keeper(s, store).run(now)
        snaps.append(json.loads((Path(s.planner.folder) / s.market.pair / "current.json").read_text()))
        t += timedelta(minutes=step_minutes)
    return snaps


def events(s: Any) -> list[dict]:
    p = Path(s.planner.folder) / s.market.pair / "recommendations.jsonl"
    return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []


# ---- the full wired path over a recorded day (candle mode, as trading/replay_check.py) ------------------------------

class PretendIG:
    """Never sends anything (the order sender is in paper mode); only gives the account's funds."""
    base_url, account_active = None, True

    def account_balance(self):
        return {"available": 20000.0}

    def request(self, *a, **k):
        raise AssertionError("the STP integration tests must never call IG")


class Alerts:
    def __init__(self):
        self.sent = []

    def problem(self, key, text):
        self.sent.append((key, text))

    def info(self, text, key=None, html=False):
        pass

    def trade_opened(self, t):
        pass

    def trade_closed(self, c):
        pass


def replay_day(s: Any, store: Any, end: datetime, stp: bool = False) -> dict:
    """The bot over the week up to `end`, one stored 5-minute candle at a time, as the price service runs it: the
    engine first (analyser, strategies, the STP check while STP_AUTHORISES_ENTRIES is on, the entry filters, the
    order sender's safety rules in paper mode, the trade manager), then, while `stp`, the STP tracker 3 seconds
    after the candle (planner/opportunities.py), whose file the next candles' checks read as it stood then. Returns
    the records it wrote (read back) and the engine."""
    from prices.calendar import MarketHours
    from trading.engine import Trading
    if stp:
        from planner.opportunities import make_keeper
        from stp.source import ReplaySource
    hours = MarketHours(s.market_hours)
    week_open, week_close = hours.session(end - timedelta(minutes=1))
    clock = {"t": week_open, "processing": week_open}
    engine = Trading(s, store, PretendIG(), Alerts(), trading_on=False, now=lambda: clock["t"], replay_end=week_close)
    snaps: list[dict] = []
    if stp:
        engine.runner.stp = ReplaySource(snaps, now=lambda: clock["processing"])
    engine.start(week_open)
    folder = Path(s.planner.folder) / s.market.pair / "current.json"
    for c in store.read_range("5m", week_open, end):
        if c.end > end:
            break
        clock["t"], clock["processing"] = c.start, c.end    # the order goes when the candle reached its entry
        engine.on_candle(c.end)
        if stp:
            make_keeper(s, store).run(c.end + timedelta(seconds=3))
            x = json.loads(folder.read_text())
            snaps.append(x)
            engine.runner.stp.snaps.append((parse_written(x), x))
    return {"engine": engine, "snapshots": snaps}


def parse_written(x: dict) -> datetime:
    from prices.model import parse_iso
    return parse_iso(x["written_utc"])


def read_records(s: Any) -> dict[str, list[str]]:
    """Every record file the run wrote (decisions, paper orders, trade manager, safety), as their lines."""
    out = {}
    for name in ("records", "orders", "trade_manager", "safety"):
        root = Path(getattr(s, name).folder)
        for p in sorted(root.rglob("*")):
            if p.is_file() and p.suffix in (".jsonl", ".json", ".txt"):
                out[str(p.relative_to(root.parent))] = p.read_text().splitlines()
    return out
