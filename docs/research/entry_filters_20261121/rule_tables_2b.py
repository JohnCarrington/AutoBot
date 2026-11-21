"""Per-strategy tables for rule 1 and rule 2b (the RSI stretch, with Johnny's slow-grind trend day), on the LIVE
trades of 9-13 Nov and 16-20 Nov (owner, 21 November 2026). Read-only.

Each day's trend day is worked out with the branch's own TrendDayWatch from the LIVE slow grind trades (IG's fill, its
open and close times) on the stored 5-minute candles: a candle counts for a trade if it started at or after the trade
opened and ended by its close (the live engine's finished-candle rule; live it is also checked on every price, so live
it may start a little earlier). Then every live trade is put through rule 1 and rule 2b (with that day's trend
direction at its open time) at its live open time and with the strategy's own entry price. What each refused trade
made is IG's live result. A refusal only removes that trade: trades that might have opened instead are not counted.

  saved = pips of the refused losers (as a positive number), cost = pips of the refused winners.

    AUTOBOT_ENV_FILE=/opt/autobot/.env PYTHONPATH=. .venv/bin/python docs/research/entry_filters_20261121/rule_tables_2b.py
"""
import csv
from collections import OrderedDict
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from analyser.market_state import MemoStore
from config.pairs import choose_pair
from config.settings_loader import load_or_exit
from prices.store import CandleStore
from strategies import entry_filters as ef
from strategies.common import SLOW_GRIND, Idea
from trade_manager.manager import Bar

D = Path(__file__).parent
import importlib.util  # noqa: E402
spec = importlib.util.spec_from_file_location("rt", D / "rule_tables.py")
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)


class Over:
    def __init__(self, base, **switches):
        self._b = base
        self.switches = SimpleNamespace(**(vars(base.switches) | switches))

    def __getattr__(self, n):
        return getattr(self._b, n)


def T(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def closes():
    """reference -> (IG fill, close time) for the live trades, from the two result files."""
    out = {}
    for r in csv.DictReader(rt.git_show("origin/research/losing-trades-20261120-cc",
                                        "research/2026-11-20_losing_trades/trades.csv").splitlines()):
        if r["closed_utc"] != "OPEN":
            out[r["reference"]] = (Decimal(r["ig_open"]), T(r["closed_utc"]))
    for r in csv.DictReader(rt.git_show("origin/research/week-results-20261121",
                                        "research/2026-11-21_week_results/week_results.csv").splitlines()):
        d = datetime.strptime(f"2026 {r['date'][4:]}", "%Y %d %b")
        o = d.replace(tzinfo=T("2026-01-01T00:00:00Z").tzinfo)
        hh, mm, ss = map(int, r["close_time_uk"][:8].split(":"))
        c = o + timedelta(hours=hh, minutes=mm, seconds=ss)
        if "(" in r["close_time_uk"]:
            c += timedelta(days=1)
        out[r["reference"]] = (Decimal(r["entry_ig"]), c)
    return out


def trend_days(base, store, live, info):
    """{UK date: TrendDayWatch} from the live slow grind trades."""
    watches = {}
    days = sorted({x["t"][:10] for x in live})
    for day in days:
        w = ef.TrendDayWatch(base)
        sgs = []
        for x in live:
            if x["strategy"] == SLOW_GRIND and x["t"][:10] == day and x["ref"] in info:
                fill, closed = info[x["ref"]]
                sgs.append((SimpleNamespace(strategy=SLOW_GRIND, direction=x["direction"], fill=fill,
                                            opened_at=T(x["t"]), open=True, reference=x["ref"]), closed))
        start = T(day + "T06:00:00Z")
        for c in store.read_range("5m", start, start + timedelta(hours=3)):
            open_now = [t for t, closed in sgs if t.opened_at <= c.start and c.end <= closed]
            w.on_bar(Bar.of(c), open_now)
        watches[day] = w
    return watches


def main():
    base = choose_pair(load_or_exit(), "GBPUSD")
    store = MemoStore(CandleStore(base.candles.folder, base.candles.compress_after_days))
    s1 = Over(base, hourly_context=True, entry_near_ema8=False, rsi_stretch=False)
    s2 = Over(base, hourly_context=False, entry_near_ema8=False, rsi_stretch=True)
    live = rt.live_trades()
    info = closes()
    watches = trend_days(base, store, live, info)
    rows = []
    for x in live:
        t = T(x["t"])
        w = watches[x["t"][:10]]
        trend = w.direction_at(t)
        idea = Idea("GBPUSD", x["strategy"], x["direction"], t, Decimal(str(x["entry"])), "", "", None, "", [])
        v1, v2 = ef.check(s1, store, idea), ef.check(s2, store, idea, trend=trend)
        r3 = ef.rsi3_at(base, store, t)[0]
        rows.append(x | {"time": t, "trend": trend, "rule1": not v1.allowed, "why1": v1.why,
                         "rule2b": not v2.allowed, "why2b": v2.why, "rsi": r3,
                         "lifted": v2.allowed and trend is not None and not ef.check(s2, store, idea).allowed,
                         "trend_day": x["t"][:10] in ("2026-11-09", "2026-11-11")})
    md = ["### Trend days from the live slow grind trades", "",
          "| Day | Trend day | Started (UK) | Direction | Slow grind trade | Cancelled |", "|---|---|---|---|---|---|"]
    for day, w in watches.items():
        dd = datetime.fromisoformat(day)
        sg = next((x for x in live if x["ref"] == w.reference), None)
        started = w.started.strftime("%H:%M") if w.started else ""
        sgtxt = f"{sg['strategy']} {sg['direction']} opened {T(sg['t']):%H:%M}" if sg else ""
        canc = w.cancelled.strftime("%H:%M") if w.cancelled else ""
        md.append(f"| {dd:%a %d %b} | {'yes' if w.direction else 'no'} | {started} | {w.direction or ''} | {sgtxt} | {canc} |")
    md.append("")
    for period in ("9-13 Nov", "16-20 Nov"):
        pr = [r for r in rows if r["period"] == period]
        md += [f"### {period}: {len(pr)} live trades", ""]
        for key, title in (("rule1", "Rule 1, hourly context"),
                           ("rule2b", "Rule 2b, RSI stretch (off in the trend's direction on a trend day)")):
            md += [f"**{title}**", "",
                   "| Strategy | Live trades | Refused | Their live pips | Winners | Saved (losers) | Cost (winners) | Net |"
                   " On 9 and 11 Nov: refused, their live pips | Of them closed by Johnny |",
                   "|---|---:|---:|---:|---:|---:|---:|---:|---|---:|"]
            strats = OrderedDict()
            for r in sorted(pr, key=lambda r: r["strategy"]):
                strats.setdefault(r["strategy"], []).append(r)
            for name, rs in list(strats.items()) + [("**All**", pr)]:
                ref = [r for r in rs if r[key]]
                p = [r["pips"] for r in ref]
                saved, cost = -sum(v for v in p if v < 0), sum(v for v in p if v > 0)
                td = [r["pips"] for r in ref if r["trend_day"]]
                tdtxt = f"{len(td)}, {sum(td):+.1f}" if period == "9-13 Nov" else "–"
                md.append(f"| {name} | {len(rs)} | {len(ref)} | {sum(p):+.1f} | {sum(v > 0 for v in p)} | {saved:.1f} | "
                          f"{cost:.1f} | {saved - cost:+.1f} | {tdtxt} | {sum(r['by'] == 'owner' for r in ref)} |")
            md.append("")
        lifted = [r for r in pr if r["lifted"]]
        if lifted:
            md += ["Trades the RSI stretch would have refused but for the trend day (in its direction):", ""] + \
                  [f"- {r['time']:%a %d %b %H:%M} {r['strategy']} {r['direction']} (RSI 3 {r['rsi']:.1f}): live {r['pips']:+.1f}"
                   for r in lifted] + [""]
    md += ["### Every refusal of a live trade on 9 and 11 Nov", "",
           "| Opened (UK) | Strategy | Dir | Entry | Live pips | Trend day then | Rule | Why |", "|---|---|---|---:|---:|---|---|---|"]
    for r in rows:
        if r["trend_day"] and (r["rule1"] or r["rule2b"]):
            for k, w in (("rule1", "why1"), ("rule2b", "why2b")):
                if r[k]:
                    why = r[w].split(". A ")[-1].replace("|", "/")
                    md.append(f"| {r['time']:%a %d %b %H:%M} | {r['strategy']} | {r['direction']} | {r['entry']} | "
                              f"{r['pips']:+.1f}{' (Johnny)' if r['by'] == 'owner' else ''} | {r['trend'] or 'none'} | "
                              f"{'1' if k == 'rule1' else '2b'} | {why} |")
    (D / "rule_tables_2b.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
