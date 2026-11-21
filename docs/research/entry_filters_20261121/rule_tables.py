"""Per-strategy tables for rule 1, rule 2 and the RSI 3 alternative to rule 2 (owner, 21 November 2026). Read-only.

Every LIVE trade of 9-13 Nov and 16-20 Nov is put through each rule on its own, at its live open time and with the
strategy's own entry price (as the bot would have checked it just before opening), using the stored candles and the
branch's strategies/entry_filters.py (session sweep exempt from rule 2). What each refused trade made is IG's live
result. A refusal only removes that trade: the trades that might have opened later instead (a setup trying again, or
a slot freed) are not counted here.

  saved = pips of the refused losers (as a positive number), cost = pips of the refused winners.

The RSI 3 alternative (a replay check only, not in the bot): no SELL when the 5-minute RSI 3 (sell price, Wilder, the
last finished 5-minute candle before the entry) is under 30; no BUY when it is over 70. Exempt: slow grind,
breakout, Asian range breakout, session sweep (as rule 2).

Johnny's trend days (his definition: the slow grind opened a trade that was in profit between 06:00 and 09:00 UK):
Mon 9 and Wed 11 Nov.

    AUTOBOT_ENV_FILE=/opt/autobot/.env PYTHONPATH=. .venv/bin/python docs/research/entry_filters_20261121/rule_tables.py
"""
import csv, json, subprocess
from collections import OrderedDict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from analyser.indicators import last_candles
from analyser.market_state import MemoStore
from config.pairs import choose_pair
from config.settings_loader import load_or_exit
from prices.indicators import rsi
from prices.store import CandleStore
from strategies import entry_filters as ef
from strategies.common import Idea

D = Path(__file__).parent
TREND_DAYS = ("2026-11-09", "2026-11-11")
RSI_EXEMPT = ef.EMA8_EXEMPT


def git_show(ref, path):
    return subprocess.run(["git", "-C", "/opt/autobot", "show", f"{ref}:{path}"], capture_output=True, text=True,
                          check=True).stdout


class Over:
    def __init__(self, base, **switches):
        self._b = base
        self.switches = SimpleNamespace(**(vars(base.switches) | switches))

    def __getattr__(self, n):
        return getattr(self._b, n)


def live_trades():
    entry = {}
    for l in open("/opt/autobot/data/records/GBPUSD/trades.jsonl"):
        r = json.loads(l)
        if r["event"] == "opened" and not r.get("paper"):
            entry[r["reference"]] = (r["entry_price"], r["opened_utc"])
    out = []
    for r in csv.DictReader(git_show("origin/research/losing-trades-20261120-cc",
                                     "research/2026-11-20_losing_trades/trades.csv").splitlines()):
        if "2026-11-09" <= r["opened_utc"] < "2026-11-14" and r["ig_pips"] != "":
            out.append(dict(period="9-13 Nov", ref=r["reference"], t=r["opened_utc"], strategy=r["strategy"],
                            direction=r["direction"], entry=entry.get(r["reference"], (r["idea_price"],))[0],
                            pips=float(r["ig_pips"]), by=r["closed_by"]))
    for r in csv.DictReader(git_show("origin/research/week-results-20261121",
                                     "research/2026-11-21_week_results/week_results.csv").splitlines()):
        e, t = entry[r["reference"]]
        out.append(dict(period="16-20 Nov", ref=r["reference"], t=t, strategy=r["strategy"], direction=r["direction"],
                        entry=e, pips=float(r["pips"]), by="owner" if r["closed_by"] == "Johnny by hand" else "bot"))
    return out


def main():
    base = choose_pair(load_or_exit(), "GBPUSD")
    store = MemoStore(CandleStore(base.candles.folder, base.candles.compress_after_days))
    s1 = Over(base, hourly_context=True, entry_near_ema8=False)
    s2 = Over(base, hourly_context=False, entry_near_ema8=True)
    rows = []
    for x in live_trades():
        t = datetime.fromisoformat(x["t"].replace("Z", "+00:00"))
        idea = Idea("GBPUSD", x["strategy"], x["direction"], t, Decimal(str(x["entry"])), "", "", None, "", [])
        v1, v2 = ef.check(s1, store, idea), ef.check(s2, store, idea)
        c5 = last_candles(store, "5m", t, base.indicators.history_candles)
        r3 = rsi(c5, base.chart.price, 3).get(c5[-1].start)
        buy = x["direction"] == "buy"
        rsi_refused = x["strategy"] not in RSI_EXEMPT and r3 is not None and ((buy and r3 > 70) or (not buy and r3 < 30))
        rows.append(x | {"time": t, "trend_day": x["t"][:10] in TREND_DAYS,
                         "rule1": not v1.allowed, "why1": v1.why, "rule2": not v2.allowed, "why2": v2.why,
                         "rsi": float(r3) if r3 is not None else None, "rsi_refused": rsi_refused})
    md = []
    for period in ("9-13 Nov", "16-20 Nov"):
        pr = [r for r in rows if r["period"] == period]
        md += [f"### {period}: {len(pr)} live trades" + (" (trend days: Mon 9 and Wed 11 Nov)" if period == "9-13 Nov" else
               " (no trend days by Johnny's definition were given for this week)"), ""]
        for key, title in (("rule1", "Rule 1, hourly context"), ("rule2", "Rule 2, entry near the 8 EMA (session sweep exempt)"),
                           ("rsi_refused", "Alternative to rule 2: RSI 3 (sell under 30, buy over 70; same exemptions)")):
            md += [f"**{title}**", "",
                   "| Strategy | Live trades | Refused | Their live pips | Winners | Saved (losers) | Cost (winners) | Net | "
                   "On trend days: refused, their live pips | Of them closed by Johnny |",
                   "|---|---:|---:|---:|---:|---:|---:|---:|---|---:|"]
            strats = OrderedDict()
            for r in sorted(pr, key=lambda r: r["strategy"]):
                strats.setdefault(r["strategy"], []).append(r)
            tot = []
            for name, rs in list(strats.items()) + [("**All**", pr)]:
                ref = [r for r in rs if r[key]]
                p = [r["pips"] for r in ref]
                saved, cost = -sum(v for v in p if v < 0), sum(v for v in p if v > 0)
                td = [r["pips"] for r in ref if r["trend_day"]]
                tdtxt = f"{len(td)}, {sum(td):+.1f}" if period == "9-13 Nov" else "–"
                md.append(f"| {name} | {len(rs)} | {len(ref)} | {sum(p):+.1f} | {sum(v > 0 for v in p)} | {saved:.1f} | "
                          f"{cost:.1f} | {saved - cost:+.1f} | {tdtxt} | {sum(r['by'] == 'owner' for r in ref)} |")
            md.append("")
    md += ["### Every refused live trade", "",
           "★ = Johnny's trend day. R1 / R2 / RSI = refused by that rule (each checked on its own).", "",
           "| Opened (UK) | Strategy | Dir | Entry | Live pips | R1 | R2 | RSI 3 | RSI | Rule 1 or 2 numbers |",
           "|---|---|---|---:|---:|:-:|:-:|:-:|---:|---|"]
    for r in rows:
        if r["rule1"] or r["rule2"] or r["rsi_refused"]:
            why = (r["why1"] if r["rule1"] else r["why2"]).replace("|", "/")
            if r["rule1"]:
                why = why.split(". A ")[-1]
            md.append(f"| {'★ ' if r['trend_day'] else ''}{r['time']:%a %d %b %H:%M} | {r['strategy']} | {r['direction']} | "
                      f"{r['entry']} | {r['pips']:+.1f}{' (Johnny)' if r['by'] == 'owner' else ''} | {'✓' if r['rule1'] else ''} | "
                      f"{'✓' if r['rule2'] else ''} | {'✓' if r['rsi_refused'] else ''} | "
                      f"{'' if r['rsi'] is None else round(r['rsi'], 1)} | {why} |")
    (D / "rule_tables.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
