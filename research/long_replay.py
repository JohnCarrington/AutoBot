"""Research mode: replay any date range through the bot's own code, as the live engine runs it.

Each trading week goes through trading.engine.Trading exactly as trading.replay_check.wired_trades runs it (the
bot's own replay): the analyser's StateTracker, the strategies (StrategyRunner), the safety rules in the order
sender (paper mode, a pretend IG that only gives the funds), the trade manager, the records. The only
differences are where it reads and writes:
  * the candles come from a research store folder (research.replay_store), not the live one;
  * the economic calendar comes from a calendar file given to the run (research.news_history, or a copy of the
    bot's own), written into the run's own news folder, which is where the bot's news rules read it; or an empty
    calendar (no news rules) when there is none;
  * every folder the engine writes to (orders, trade manager, safety, records, status, the pause file, news)
    is moved into the run's folder under /opt/autobot/data/research/. Nothing else is written; IG is never
    contacted (the pretend IG fails any call); the live service is never touched.
Weeks are independent (each starts at the week's open, as the bot's replay does; trades still open at the end of
a week or of the range are counted at the last candle's close, as the bot's replay does), so they can run as
separate low-priority processes. Each week's trades are saved as soon as it finishes; a stopped run carries on
where it was.

    nice -n 19 .venv/bin/python -m research.long_replay run --store data/research/replay_stores/main/GBPUSD \
        --calendar data/research/news/finnhub_calendar.json --from 2024-02-18 --to 2026-11-07 \
        --out data/research/replay/long_20261110 --jobs 2
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from prices.calendar import MarketHours
from prices.model import UK, iso, parse_iso

UTC = timezone.utc
RESEARCH = Path("/opt/autobot/data/research")
LIVE_FOLDERS = ("/opt/autobot/data/candles", "/opt/autobot/data/orders", "/opt/autobot/data/records",
                "/opt/autobot/data/trade_manager", "/opt/autobot/data/news", "/opt/autobot/data/safety",
                "/opt/autobot/data/analyser", "/opt/autobot/data/levels", "/opt/autobot/data/trading",
                "/opt/autobot/data/alerts")


def check_research_folder(p: Path, allow: Path | None = None) -> Path:
    """Only under data/research/ (or a test folder given as `allow`); never a live folder."""
    p = Path(p).resolve()
    if any(str(p) == x or str(p).startswith(x + "/") for x in LIVE_FOLDERS):
        raise PermissionError(f"refusing a live folder: {p}")
    roots = [RESEARCH] + ([Path(allow).resolve()] if allow else [])
    if not any(p == r or r in p.parents for r in roots):
        raise PermissionError(f"research replays write only under {RESEARCH}: {p}")
    return p


class Over:
    """The real settings, with every folder the engine writes to moved into `folder`, the candle store's folder
    set to `store`, and the news folder (where the bot's news rules read the calendar) set to `folder/news`.
    Built on trading.replay_check._Over (the bot's own replay), with the news, analyser and candle folders added."""

    def __init__(self, base: Any, folder: Path, store: Path):
        from trading.replay_check import _Over
        self._inner = _Over(base, folder)
        self.news = SimpleNamespace(**(vars(base.news) | {"folder": folder / "news"}))
        self.market_states = SimpleNamespace(**(vars(base.market_states) | {"folder": folder / "market_states"}))
        self.candles = SimpleNamespace(**(vars(base.candles) | {"folder": store.parent}))

    def __getattr__(self, name):
        return getattr(self._inner, name)


def settings_for(tmp: Path, switches: Path | None = None) -> Any:
    """The bot's own settings and switches, TRADING off (trading.replay_check._settings: the secrets are never read).
    `switches`: a frozen copy of the switches (a run's own), so every week of a run uses the same rules even if
    .env changes while it runs."""
    if switches is not None:
        from config.settings_loader import load_settings
        return load_settings(switches_from=switches).for_pair("GBPUSD")
    from trading.replay_check import _settings
    return _settings(tmp)


def freeze_switches(out: Path, overrides: dict[str, str] | None = None) -> Path:
    """The run's switches, frozen once from .env (TRADING off): out/switches.env. `overrides` ({"STOP_LOSS_PIPS":
    "12"}) change only those switches in the run's copy (never .env); a run already frozen with different values
    is refused, so one run never mixes rules."""
    p = Path(out) / "switches.env"
    overrides = {k.upper(): str(v) for k, v in (overrides or {}).items()}
    if overrides.get("TRADING", "off") != "off":
        raise ValueError("a research replay always runs with TRADING off")
    if not p.exists():
        with tempfile.TemporaryDirectory() as tmp:
            settings_for(Path(tmp))
            lines = (Path(tmp) / "switches.env").read_text().splitlines()
        keys = {ln.split("=", 1)[0] for ln in lines if "=" in ln}
        unknown = set(overrides) - keys
        if unknown:
            raise ValueError(f"unknown switch(es): {', '.join(sorted(unknown))}")
        lines = [f"{k}={overrides[k]}" if (k := ln.split("=", 1)[0]) in overrides else ln for ln in lines]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("\n".join(lines) + "\n")
    frozen = dict(ln.split("=", 1) for ln in p.read_text().splitlines() if "=" in ln)
    clash = {k: v for k, v in overrides.items() if frozen.get(k) != v}
    if clash:
        raise ValueError(f"this run was frozen with other values for {', '.join(sorted(clash))}")
    return p


def write_calendar(news_folder: Path, events: list[dict] | None, start: datetime, end: datetime) -> int:
    """The calendar for one week (its releases from 2 days before to 2 days after), in the bot's own file
    format, where the bot's news rules read it. None or [] -> an empty calendar: no news rules."""
    news_folder.mkdir(parents=True, exist_ok=True)
    lo, hi = iso(start - timedelta(days=2)), iso(end + timedelta(days=2))
    week = [e for e in (events or []) if lo <= e["time_utc"] < hi]
    now = iso(start)
    (news_folder / "calendar.json").write_text(json.dumps(
        {"events": week, "last_fetch_utc": now, "last_attempt_utc": now, "last_error": None}, indent=1) + "\n")
    return len(week)


@dataclass
class Trade:
    week_open: str
    entry_utc: str
    strategy: str
    direction: str
    entry_price: str
    fill: str
    pips: str
    closed_utc: str
    how_closed: str
    why: str
    state: str

    def key(self) -> tuple:
        return (self.entry_utc, self.strategy, self.direction)


# ---- speed, without changing what the bot's code computes ----------------------------------------------

_WEEK: dict = {}          # the week being replayed: {"candles": warm + whole week, "features": compute() of it}


def install_speedups(research_store: Path) -> None:
    """Two caches for this research process only (never in the live bot):
      * the research store's day files and its list of days are read once (it never changes during a replay;
        any other store, the live one included, is never cached);
      * the analyser's features: analyser.features.compute is causal (each candle's features depend only on the
        candles up to it: the EMAs, bands, MACD and RSI run forward from the first candle and every look-back looks
        back), so the week's features are worked out once and the first n handed back when the analyser asks for
        the first n candles. Only when the candles asked for are exactly the start of the week's list; anything else
        goes to the bot's own compute. tests/technical/test_research_candles.py checks prefix == whole on real
        candles, and the check replay compares every trade with the bot's own replay."""
    import analyser.market_state as ms
    from analyser.features import compute
    from prices.store import CandleStore
    if getattr(CandleStore, "_research_cached", False):
        return
    root = str(Path(research_store).resolve())
    original_read_day, original_days = CandleStore.read_day, CandleStore.days
    files: dict = {}
    listing: dict = {}
    ours: dict = {}

    def is_ours(folder) -> bool:
        k = str(folder)
        if k not in ours:
            ours[k] = str(Path(folder).resolve()) == root
        return ours[k]

    def read_day(self, tf, day):
        if not is_ours(self.folder):
            return original_read_day(self, tf, day)
        key = (tf, day)
        if key not in files:
            files[key] = original_read_day(self, tf, day)
        return list(files[key])

    def days(self, tf):
        if not is_ours(self.folder):
            return original_days(self, tf)
        if tf not in listing:
            listing[tf] = original_days(self, tf)
        return list(listing[tf])

    def compute_fast(candles, settings):
        w = _WEEK.get("candles")
        n = len(candles)
        if w is not None and 0 < n <= len(w) and candles[0] == w[0] and candles[-1] == w[n - 1] and candles == w[:n]:
            if _WEEK.get("features") is None:
                _WEEK["features"] = compute(w, settings)
            return _WEEK["features"][:n]
        return compute(candles, settings)

    CandleStore.read_day = read_day
    CandleStore.days = days
    CandleStore._research_cached = True
    ms.compute = compute_fast


def _prepare_week(store: Any, base: Any, week_open: datetime, week_close: datetime) -> None:
    from analyser.indicators import last_candles
    warm = last_candles(store, "5m", week_open, base.market_states.indicator_warm_up_candles)
    week = [c for c in store.read_range("5m", week_open, week_close) if c.end <= week_close]
    _WEEK.clear()
    _WEEK.update({"candles": warm + week, "features": None})


def replay_week(base: Any, store_folder: Path, week_open: datetime, week_close: datetime, events: list[dict] | None,
                folder: Path, only_from: datetime | None = None, fast: bool = True) -> list[Trade]:
    """One week, exactly as trading.replay_check.wired_trades runs one (same engine, same clock, same handling of
    trades still open at the end). Trades whose entry is before `only_from` are run but not returned."""
    from prices.store import CandleStore
    from trade_manager.manager import CLOSE, Decision
    from trading.engine import Trading
    from trading.replay_check import _Alerts, _PretendIG
    folder.mkdir(parents=True, exist_ok=True)
    s = Over(base, folder, store_folder)
    write_calendar(s.news.folder, events, week_open, week_close)
    store = CandleStore(store_folder, base.candles.compress_after_days)
    if fast:
        install_speedups(store_folder)
        _prepare_week(store, base, week_open, week_close)
    ppp = Decimal(base.market.points_per_pip)
    clock = {"t": week_open}
    engine = Trading(s, store, _PretendIG(), _Alerts(), trading_on=False, now=lambda: clock["t"],
                     replay_end=week_close)
    engine.start(week_open)
    final = None
    for c in store.read_range("5m", week_open, week_close):
        if c.end > week_close:
            break
        clock["t"] = c.start
        engine.on_candle(c.end)
        final = c
    out = []
    for idea, mt in engine.opened:
        if mt.open:
            price = final.buy_close if mt.direction == "sell" else final.sell_close
            p = ((mt.fill - price) if mt.direction == "sell" else (price - mt.fill)) / ppp
            mt.decisions.append(Decision(CLOSE, price, p, "open at the end of the data",
                                         (1 - mt.half_share) if mt.half_done else Decimal(1), final.start))
            mt.state = CLOSE
        if only_from is not None and idea.time < only_from:
            continue
        last = mt.decisions[-1]
        out.append(Trade(iso(week_open), iso(idea.time), idea.strategy, idea.direction, str(idea.entry_price),
                         str(mt.fill), str(mt.total_pips()), iso(last.at) if last.at else "", last.kind, last.why,
                         f"{idea.state} {idea.state_direction}"))
    return sorted(out, key=lambda t: t.entry_utc)


def weeks(hours: MarketHours, start: datetime, end: datetime) -> list[tuple[datetime, datetime]]:
    """Every trading week touching [start, end): (open, close), the close cut at `end`."""
    out, t = [], start
    o, c = hours.session(t)
    if c <= t:                                           # start is in a weekend: the next week
        o, c = hours.session(hours.next_open(t))
    while o < end:
        out.append((o, min(c, end)))
        o, c = hours.session(hours.next_open(c + timedelta(minutes=1)))
    return out


def first_warm_week(store_folder: Path, hours: MarketHours, base: Any, after: datetime) -> tuple[datetime, dict]:
    """The first week open (at or after `after`) with every indicator's full warm-up already in the store before
    it: market_states.indicator_warm_up_candles 5-minute candles, ema_pullback.hourly_history_candles hourly
    candles, and 40 daily candles (the trend day's look-back). Returns (week open, the counts found)."""
    from analyser.indicators import last_candles
    from prices.store import CandleStore
    st = CandleStore(store_folder, 10 ** 6)
    need = {"5m": base.market_states.indicator_warm_up_candles, "1h": base.ema_pullback.hourly_history_candles,
            "1d": 40}
    o = hours.session(hours.next_open(after))[0]
    for _ in range(200):
        got = {tf: len(last_candles(st, tf, o, n)) for tf, n in need.items()}
        if all(got[tf] >= n for tf, n in need.items()):
            return o, got
        o = hours.session(hours.next_open(hours.session(o)[1] + timedelta(minutes=1)))[0]
    raise ValueError("no week with a full warm-up found")


def _job(args: tuple) -> tuple[str, int, str]:
    store, cal_path, w_open, w_close, out, only_from = args
    import os
    try:
        os.nice(19 - os.nice(0))                         # never above the lowest priority
    except OSError:
        pass
    done = Path(out) / "weeks" / f"{w_open[:10]}.json"
    if done.exists():
        return w_open, len(json.loads(done.read_text())["trades"]), "already done"
    events = json.loads(Path(cal_path).read_text())["events"] if cal_path else []
    with tempfile.TemporaryDirectory() as tmp:
        base = settings_for(Path(tmp), Path(out) / "switches.env")
        folder = Path(out) / "engine" / w_open[:10]
        if folder.exists():                              # left by an interrupted attempt: its open trades and
            shutil.rmtree(folder)                        # safety state must not carry into this one
        trades = replay_week(base, Path(store), parse_iso(w_open), parse_iso(w_close), events, folder,
                             parse_iso(only_from) if only_from else None)
    done.parent.mkdir(parents=True, exist_ok=True)
    tmpf = done.with_suffix(".tmp")
    tmpf.write_text(json.dumps({"week_open": w_open, "week_close": w_close,
                                "trades": [vars(t) for t in trades]}, indent=1) + "\n")
    tmpf.replace(done)
    return w_open, len(trades), "done"


def run(store: Path, calendar: Path | None, start: datetime, end: datetime, out: Path, jobs: int = 1,
        overrides: dict[str, str] | None = None) -> list[Trade]:
    out = check_research_folder(out)
    store = Path(store).resolve()
    if store.name != "GBPUSD":
        raise ValueError("the store must be a folder named GBPUSD")
    sw = freeze_switches(out, overrides)
    base = settings_for(Path("/nonexistent"), sw)
    hours = MarketHours(base.market_hours)
    ws = weeks(hours, start, end)
    (out / "run.json").parent.mkdir(parents=True, exist_ok=True)
    (out / "run.json").write_text(json.dumps({
        "store": str(store), "calendar": str(calendar) if calendar else None, "from": iso(start), "to": iso(end),
        "news_rules": bool(calendar), "weeks": len(ws), "overrides": overrides or {},
        "switches": {k: str(v) for k, v in vars(base.switches).items()},
        "stops_pips": {"slow grind": str(base.slow_grind.stop_loss_pips) if hasattr(base.slow_grind, "stop_loss_pips") else None,
                       "breakout": str(base.breakout.stop_loss_pips)}}, indent=1) + "\n")
    args = [(str(store), str(calendar) if calendar else None, iso(o), iso(c), str(out), iso(start) if o < start else None)
            for o, c in ws]
    if jobs > 1:
        import multiprocessing as mp
        with mp.get_context("fork").Pool(jobs, maxtasksperchild=4) as pool:
            for w, n, how in pool.imap_unordered(_job, args):
                print(f"week {w[:10]}: {n} trades ({how})", flush=True)
    else:
        for a in args:
            w, n, how = _job(a)
            print(f"week {w[:10]}: {n} trades ({how})", flush=True)
    return load_trades(out)


def load_trades(out: Path) -> list[Trade]:
    trades = []
    for p in sorted((Path(out) / "weeks").glob("*.json")):
        trades += [Trade(**t) for t in json.loads(p.read_text())["trades"]]
    return sorted(trades, key=lambda t: (t.entry_utc, t.strategy))


# ---- results ---------------------------------------------------------------------------------------

def stats(trades: list[Trade]) -> dict:
    """Trades, wins, losses, pips, biggest loss, worst losing run (in entry order)."""
    pips = [Decimal(t.pips) for t in sorted(trades, key=lambda t: t.entry_utc)]
    run = worst = 0
    for p in pips:
        run = run + 1 if p < 0 else 0
        worst = max(worst, run)
    return {"trades": len(pips), "won": sum(p > 0 for p in pips), "lost": sum(p < 0 for p in pips),
            "pips": sum(pips, Decimal(0)), "biggest_loss": min(pips) if pips else Decimal(0), "worst_run": worst}


def by(trades: list[Trade], key) -> dict:
    groups: dict = {}
    for t in trades:
        groups.setdefault(key(t), []).append(t)
    return {k: stats(v) for k, v in sorted(groups.items())}


def month_of(t: Trade) -> str:
    return parse_iso(t.entry_utc).astimezone(UK).strftime("%Y-%m")


def year_of(t: Trade) -> str:
    return parse_iso(t.entry_utc).astimezone(UK).strftime("%Y")


def keyed(trades: list[Trade]) -> dict:
    """{(entry time, strategy, direction, n): trade}; n numbers identical trades opened in the same minute
    (the bot can open two or three copies of one setup at once), in the order of their results."""
    out: dict = {}
    for t in sorted(trades, key=lambda t: (t.key(), Decimal(t.pips), t.closed_utc)):
        n = 0
        while t.key() + (n,) in out:
            n += 1
        out[t.key() + (n,)] = t
    return out


def compare(a: list[Trade], b: list[Trade]) -> dict:
    """Trade by trade: the same (entry time, strategy, direction, copy) in both, and whether the result matches."""
    ka, kb = keyed(a), keyed(b)
    same = [k for k in ka if k in kb and ka[k].pips == kb[k].pips and ka[k].fill == kb[k].fill]
    differ = [k for k in ka if k in kb and (ka[k].pips != kb[k].pips or ka[k].fill != kb[k].fill)]
    return {"same": sorted(same), "different_result": sorted(differ),
            "only_a": sorted(k for k in ka if k not in kb), "only_b": sorted(k for k in kb if k not in ka)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Research replays through the bot's own code (no IG contact).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--store", type=Path, required=True)
    r.add_argument("--calendar", type=Path, help="calendar file (events in the bot's format); none: no news rules")
    r.add_argument("--from", dest="start", required=True, help="UK date or UTC time (ISO)")
    r.add_argument("--to", dest="end", required=True, help="UK date or UTC time (ISO), not included")
    r.add_argument("--out", type=Path, required=True)
    r.add_argument("--jobs", type=int, default=1)
    r.add_argument("--set", action="append", default=[], metavar="SWITCH=VALUE",
                   help="change one of .env's switches for this run only, e.g. STOP_LOSS_PIPS=12 (never written to .env)")
    a = ap.parse_args(argv)

    def when(x: str) -> datetime:
        if "T" in x:
            return datetime.fromisoformat(x.replace("Z", "+00:00")).astimezone(UTC)
        y, m, d = (int(v) for v in x.split("-"))
        return datetime(y, m, d, tzinfo=UK).astimezone(UTC)

    overrides = dict(x.split("=", 1) for x in a.set)
    trades = run(a.store, a.calendar, when(a.start), when(a.end), a.out, a.jobs, overrides)
    s = stats(trades)
    print(f"{s['trades']} trades, {s['won']} won, {s['lost']} lost, {s['pips']:+} pips, biggest loss "
          f"{s['biggest_loss']}, worst losing run {s['worst_run']}"
          + ("" if a.calendar else "  (NO NEWS RULES: no calendar given)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
