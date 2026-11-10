"""Markdown tables for a research replay (research.long_replay): each strategy and the whole bot, by year and by
month (trades, won, lost, pips, biggest loss, worst losing run), and how complete the candles were each month.
Read only.

    .venv/bin/python -m research.long_report RUN_FOLDER STORE_FOLDER
    .venv/bin/python -m research.long_report compare RUN_A RUN_B NAME_A NAME_B
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from prices.calendar import MarketHours
from prices.model import UK, parse_iso
from prices.store import CandleStore
from research.long_replay import Trade, by, load_trades, month_of, stats, year_of

STRATEGIES = ("slow grind", "EMA pullback", "Bollinger bounce", "range trade", "breakout", "level reversal")


def p1(x: Decimal) -> str:
    return f"{x.quantize(Decimal('0.1')):+}"


def row(name: str, s: dict) -> str:
    rate = f"{100 * s['won'] / s['trades']:.0f}%" if s["trades"] else "-"
    return (f"| {name} | {s['trades']} | {s['won']} | {s['lost']} | {rate} | **{p1(s['pips'])}** | "
            f"{p1(s['biggest_loss']) if s['trades'] else '-'} | {s['worst_run']} |")


HEAD = ("| {} | Trades | Won | Lost | Won % | Pips | Biggest loss | Worst losing run |\n"
        "|---|---:|---:|---:|---:|---:|---:|---:|")


def table(title: str, groups: dict) -> str:
    return "\n".join([HEAD.format(title)] + [row(k, v) for k, v in groups.items()])


def by_strategy(trades: list[Trade]) -> dict:
    out = {k: stats([t for t in trades if t.strategy == k]) for k in STRATEGIES}
    out["**Whole bot**"] = stats(trades)
    return out


def coverage(store_folder: Path, hours: MarketHours, months: list[str]) -> dict[str, tuple[int, int]]:
    """{month: (5-minute candles in the store, candles the market hours expect)} in UK months."""
    st = CandleStore(store_folder, 10 ** 6)
    have: dict = defaultdict(int)
    for d in st.days("5m"):
        for c in st.read_day("5m", d):
            have[c.start.astimezone(UK).strftime("%Y-%m")] += 1
    out = {}
    for m in months:
        y, mo = (int(x) for x in m.split("-"))
        a = datetime(y, mo, 1, tzinfo=UK)
        b = datetime(y + (mo == 12), mo % 12 + 1, 1, tzinfo=UK)
        out[m] = (have[m], sum(1 for _ in hours.open_slots(a, b)))
    return out


def report(run: Path, store: Path, hours: MarketHours) -> str:
    trades = load_trades(run)
    meta = json.loads((Path(run) / "run.json").read_text())
    years = sorted({year_of(t) for t in trades})
    months = sorted({month_of(t) for t in trades})
    out = [f"Period: {meta['from']} to {meta['to']} (UTC), {meta['weeks']} trading weeks. "
           + ("News rules ON (the calendar given)." if meta["news_rules"] else "**NO NEWS RULES: no calendar.**"), ""]
    out += ["### The whole period, by strategy", "", table("Strategy", by_strategy(trades)), ""]
    out += ["### By year, the whole bot", "", table("Year", by(trades, year_of)), ""]
    for y in years:
        out += [f"### {y}, by strategy", "", table("Strategy", by_strategy([t for t in trades if year_of(t) == y])), ""]
    cov = coverage(store, hours, months)
    out += ["### By month, the whole bot (with how complete the candles were)", "",
            "| Month | Candles | Trades | Won | Lost | Won % | Pips | Biggest loss | Worst losing run |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for m, s in by(trades, month_of).items():
        h, e = cov[m]
        flag = "" if h >= 0.97 * e else " ⚠"
        out.append(row(m, s).replace(f"| {m} |", f"| {m} | {100 * h / e:.0f}%{flag} |", 1))
    out += ["", "### By month and strategy: pips (trades)", "",
            "| Month | " + " | ".join(STRATEGIES) + " | Whole bot |", "|---|" + "---:|" * (len(STRATEGIES) + 1)]
    for m in months:
        mt = [t for t in trades if month_of(t) == m]
        cells = []
        for k in STRATEGIES + ("*",):
            s = stats(mt if k == "*" else [t for t in mt if t.strategy == k])
            cells.append(f"{p1(s['pips'])} ({s['trades']})" if s["trades"] else "-")
        out.append(f"| {m} | " + " | ".join(cells) + " |")
    return "\n".join(out)


def monthly_by_strategy(run: Path) -> str:
    """The appendix: every strategy's full row for every month."""
    trades = load_trades(run)
    out = []
    for k in STRATEGIES:
        ts = [t for t in trades if t.strategy == k]
        out += [f"#### {k}", "", table("Month", by(ts, month_of)), ""]
    return "\n".join(out)


def side_by_side(run_a: Path, run_b: Path, name_a: str, name_b: str) -> str:
    """Two runs of the same period with different rules: each strategy and the whole bot, whole period and by
    year (trades, won %, pips, biggest loss, worst losing run, and the change in pips)."""
    ta, tb = load_trades(run_a), load_trades(run_b)
    years = sorted({year_of(t) for t in ta + tb})

    def cell(s: dict) -> str:
        rate = f"{100 * s['won'] / s['trades']:.0f}%" if s["trades"] else "-"
        return f"{s['trades']} | {rate} | {p1(s['pips'])} | {p1(s['biggest_loss']) if s['trades'] else '-'} | {s['worst_run']}"

    out = []
    for label, pick in [("The whole period", lambda t: True)] + [(y, (lambda y: lambda t: year_of(t) == y)(y))
                                                                  for y in years]:
        sa, sb = by_strategy([t for t in ta if pick(t)]), by_strategy([t for t in tb if pick(t)])
        out += [f"#### {label}", "",
                f"| Strategy | {name_a}: trades | won % | pips | biggest loss | worst run | {name_b}: trades | won % | "
                "pips | biggest loss | worst run | Change in pips |",
                "|---|" + "---:|" * 11]
        for k in sa:
            out.append(f"| {k} | {cell(sa[k])} | {cell(sb[k])} | **{p1(sb[k]['pips'] - sa[k]['pips'])}** |")
        out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    import tempfile
    from research.long_replay import settings_for
    a = argv or sys.argv[1:]
    if a and a[0] == "compare":
        print(side_by_side(Path(a[1]), Path(a[2]), a[3], a[4]))
        return 0
    hours = MarketHours(settings_for(Path(tempfile.mkdtemp())).market_hours)
    print(report(Path(a[0]), Path(a[1]), hours))
    print()
    print(monthly_by_strategy(Path(a[0])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
