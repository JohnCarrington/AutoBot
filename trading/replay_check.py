"""Replay check of the full wired path: the stored candles go one at a time through the bot as the price service
runs it (trading/engine.py: the analyser, the strategies, the safety rules in the order sender, the order sender
in paper mode, the trade manager), and the result must be the one the research found for the rules the bot now
has: docs/research/one_view_20261109.md, "The 10 best combinations", rank 1 (no reversal trade against a strong
push; no reversal trade against the day's direction on an exception day). The same period: Sunday 25 October
21:00 UK to the candle starting Monday 9 November 10:00 UTC; trades still open after it are counted at its close
price, as in the research. Checked: the trades, won, lost, total pips, biggest loss, worst losing run, the pips of
each week, and every trade the research lists as left out by those two changes is not taken.
Reads the candle store and the calendar; never contacts IG (a pretend IG gives the funds); writes only to a
temporary folder.

    .venv/bin/python -m trading.replay_check
Exit code 0 when everything matches, 1 otherwise.
"""

from __future__ import annotations

import re
import sys
import tempfile
from collections import Counter
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from prices.calendar import MarketHours
from prices.model import parse_iso
from prices.store import CandleStore
from trade_manager.manager import CLOSE, Decision
from trading.engine import Trading

UK = ZoneInfo("Europe/London")
WEEKS = ("2026-10-27T12:00:00Z", "2026-11-03T12:00:00Z", "2026-11-09T12:00:00Z")


class _Over:
    """The real settings with the order sender's and trade manager's folders moved to a temporary folder."""
    def __init__(self, base, folder: Path):
        self._base = base
        self.orders = SimpleNamespace(**(vars(base.orders) | {"folder": folder / "orders"}))
        self.trade_manager = SimpleNamespace(**(vars(base.trade_manager) | {"folder": folder / "trade_manager"}))
        self.safety = SimpleNamespace(**(vars(base.safety) | {"folder": folder / "safety"}))
        self.records = SimpleNamespace(**(vars(base.records) | {"folder": folder / "records"}))
        self.trading = SimpleNamespace(**(vars(base.trading) | {"pause_file": folder / "control" / "pause"}))
        self.dashboard = SimpleNamespace(**(vars(base.dashboard) | {"status_folder": folder / "status"}))

    def __getattr__(self, name):
        return getattr(self._base, name)


class _PretendIG:
    """Never sends anything: the order sender is in paper mode. It only gives the account's funds."""
    base_url, account_active = None, True

    def account_balance(self):
        return {"available": 20000.0}

    def request(self, *a, **k):
        raise AssertionError("the replay check must never call IG")


class _Alerts:
    def problem(self, key, text):
        print(f"  alert {key}: {text}")

    def info(self, text, key=None):
        pass


def _settings(folder: Path):
    """The real settings and the .env switch values, with TRADING off (the check always runs in paper mode; the
    real .env may not have the switch yet). The secrets are never read."""
    from datetime import time as tm
    from config.env_file import env_path
    from config.settings_loader import load_settings
    from config.switches import SWITCHES, read_switches
    values, problems = read_switches(env_path())
    if [p for p in problems if "TRADING" not in p]:
        raise SystemExit("Switch problems in .env: " + "; ".join(problems))
    lines = []
    for key, (name, _) in SWITCHES.items():
        v = False if key == "TRADING" else values.get(name)
        v = ",".join(v) if isinstance(v, tuple) else ("on" if v else "off") if isinstance(v, bool) else \
            v.strftime("%H:%M") if isinstance(v, tm) else v
        lines.append(f"{key}={v}")
    p = folder / "switches.env"
    p.write_text("\n".join(lines) + "\n")
    return load_settings(switches_from=p).for_pair("GBPUSD")


RESEARCH = Path(__file__).resolve().parents[1] / "docs" / "research" / "one_view_20261109.md"
LAST_CANDLE = "2026-11-09T10:00:00Z"                # the last candle the research had
CHANGES = ("Strong push: reversals against a strong push refused", "Exceptions: no reversals against the day's direction")


def research_expected() -> tuple[dict, Counter, Counter]:
    """From the research: rank 1's row (trades, won, lost, total, biggest loss, worst run, the three weeks), the
    trades its two changes left out and the ones they added, as (entry 'Thu 05 Nov 07:50', strategy, DIR)."""
    text = RESEARCH.read_text().splitlines()
    row = next(line for line in text if line.startswith("| 1 | " + "; ".join(CHANGES) + " |"))
    c = [x.strip().strip("*") for x in row.strip().strip("|").split("|")]
    want = {"trades": int(c[2]), "won": int(c[3]), "lost": int(c[4]), "total": c[5], "biggest loss": c[6],
            "worst run": int(c[7]), "weeks": (c[8], c[9], c[10])}
    left_out, added, section = Counter(), Counter(), None
    for line in text:
        if line.startswith("#### "):
            section = line[5:].strip()
            continue
        cells = [x.strip() for x in line.strip().strip("|").split("|")]
        if section in CHANGES and len(cells) == 6 and re.match(r"\w{3} \d\d \w{3} \d\d:\d\d$", cells[0]):
            if cells[4] == "-":
                left_out[(cells[0], cells[1], cells[2])] += 1
            elif cells[3] == "-":
                added[(cells[0], cells[1], cells[2], cells[4])] += 1
    return want, left_out, added


def _pips(x) -> str:
    return f"{x:+.1f}"


def wired_trades(base) -> list:
    """Every trade of the full wired path over the research's period: (idea, trade manager's trade, pips, week open)."""
    store = CandleStore(base.candles.folder, base.candles.compress_after_days)
    hours = MarketHours(base.market_hours)
    last = parse_iso(LAST_CANDLE)
    ppp = Decimal(base.market.points_per_pip)
    trades = []
    with tempfile.TemporaryDirectory() as tmp:
        s = _Over(base, Path(tmp))
        for w in WEEKS:
            week_open, week_close = hours.session(parse_iso(w))
            week_close = min(week_close, last + timedelta(minutes=5))
            clock = {"t": week_open}
            engine = Trading(s, store, _PretendIG(), _Alerts(), trading_on=False, now=lambda: clock["t"],
                             replay_end=week_close)
            engine.start(week_open)
            final = None
            for c in store.read_range("5m", week_open, week_close):
                if c.end > week_close:
                    break
                clock["t"] = c.start                    # the order goes when the candle reached its entry
                engine.on_candle(c.end)
                final = c
            for idea, mt in engine.opened:
                if mt.open:                             # still open: counted at the last candle's close
                    price = final.buy_close if mt.direction == "sell" else final.sell_close
                    p = ((mt.fill - price) if mt.direction == "sell" else (price - mt.fill)) / ppp
                    mt.decisions.append(Decision(CLOSE, price, p, "open at the end of the data",
                                                 (1 - mt.half_share) if mt.half_done else Decimal(1), final.start))
                    mt.state = CLOSE
                trades.append((idea, mt, mt.total_pips(), week_open))
    return sorted(trades, key=lambda x: x[0].time)


def main() -> int:
    tmp_holder = tempfile.TemporaryDirectory()
    base = _settings(Path(tmp_holder.name))
    off = [k for k in ("slow_grind", "ema_pullback", "bollinger_bounce", "range_trade", "breakout", "level_reversal")
           if not getattr(base.switches, k)]
    if off:
        print(f"The research had all six strategies switched on; these are off in .env: {', '.join(off)}.")
        return 1
    hours = MarketHours(base.market_hours)
    trades = wired_trades(base)
    want, left_out, added = research_expected()
    pips = [p for _, _, p, _ in trades]
    run = worst = 0
    for p in pips:
        run = run + 1 if p < 0 else 0
        worst = max(worst, run)
    weeks = []
    for w in WEEKS:
        o = hours.session(parse_iso(w))[0]
        weeks.append(_pips(sum((p for _, _, p, wo in trades if wo == o), Decimal(0))))
    got = {"trades": len(trades), "won": sum(p > 0 for p in pips), "lost": sum(p < 0 for p in pips),
           "total": _pips(sum(pips, Decimal(0))), "biggest loss": _pips(min(pips)), "worst run": worst,
           "weeks": tuple(weeks)}
    ok = True
    for k in want:
        same = want[k] == got[k]
        ok &= same
        print(f"  {k}: research {want[k]}, the full wired path {got[k]}{'' if same else '   <- DIFFERENT'}")
    taken = Counter((f"{i.time.astimezone(UK):%a %d %b %H:%M}", i.strategy, i.direction.upper()) for i, _, _, _ in trades)
    for k in left_out:
        if taken[k]:
            ok = False
            print(f"  taken, but the research left it out: {k}")
    full = Counter((f"{i.time.astimezone(UK):%a %d %b %H:%M}", i.strategy, i.direction.upper(), _pips(p))
                   for i, _, p, _ in trades)
    for k in added:
        if not full[k]:
            ok = False
            print(f"  not taken as in the research: {k}")
    print(f"Trades left out by the two changes: {sum(left_out.values())}; added: {sum(added.values())}. "
          f"{'Everything matches the research.' if ok else 'NOT the same as the research.'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
