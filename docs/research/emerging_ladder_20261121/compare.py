"""The ladder's check replays, ladder on against off (read-only): every trade whose result changes, the emerging-trend
totals, Johnny's trend days (9 and 11 Nov), and a cross-check against the research's exit e.

The cross-check applies the research's exit e method (research/2026-11-21_emerging_trend_exit/ladder.py, on branch
research/emerging-trend-exit-20261121) to the replay's OWN ladder-off trades: their fill, direction and close, the
stored 5-minute candles, a candle first tests the stop set before it then moves it, a stop through which the trade
later closed is taken. If the code does what the research did, the replay with the ladder on gives the same results.

    python3 compare.py > compare.md
"""
import csv, glob, json
from datetime import datetime, timedelta
from decimal import Decimal as D
from pathlib import Path

HERE = Path(__file__).parent
C = {}
for f in sorted(glob.glob("/opt/autobot/data/candles/GBPUSD/5m/2026-11-*.csv")):
    for r in csv.DictReader(open(f)):
        C[r["start_utc"]] = r
T = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)  # noqa: E731
key = lambda t: t.strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: E731
EM = "emerging trend"


def load(name):
    return json.load(open(HERE / name))["trades"]


def k(t):
    return (t["time_utc"], t["strategy"], t["direction"])


def research_e(t):
    """Exit e on the stored candles for a ladder-off replay trade (pips), or None if it never reached +10."""
    buy = t["direction"] == "buy"; fill = D(t["fill"]); a = D(t["pips"])
    o, c = T(t["time_utc"]), T(t["closed_utc"])
    stop = None; best = D(-999); x = o
    path = []
    while x <= c:
        r = C.get(key(x))
        if r:
            hi = (D(r["sell_high"]) - fill) if buy else (fill - D(r["buy_low"]))
            lo = (D(r["sell_low"]) - fill) if buy else (fill - D(r["buy_high"]))
            path.append((hi, lo))
        x += timedelta(minutes=5)
    for hi, lo in path:
        if stop is not None and lo <= stop:      # as the research: also when only the close candle touches it
            return stop
        best = max(best, hi)
        new = D(10) if best >= 15 else D(5) if best >= 10 else None
        if new is not None and (stop is None or new > stop):
            stop = new
    if stop is not None and a < stop:
        return stop
    return a if stop is not None else None


def main():
    out = []
    totals = {}
    for wk, label in (("09_13", "9–13 Nov"), ("16_20", "16–20 Nov")):
        off, on = load(f"replay_{wk}_nov_off.json"), load(f"replay_{wk}_nov_on.json")
        offd, ond = {k(t): t for t in off}, {k(t): t for t in on}
        out += [f"### {label}", "",
                f"Trades: {len(off)} with the ladder off, {len(on)} with it on; opened in emerging trend: "
                f"{sum(1 for t in off if (t['market_state'] or '').startswith(EM))} off, "
                f"{sum(1 for t in on if (t['market_state'] or '').startswith(EM))} on.", "",
                "| Opened (UK) | Strategy | Dir | State at open | Best | Off: how, pips | On: how, pips | Stop moves (on) | Research e on the off trade |",
                "|---|---|---|---|---|---|---|---|---|"]
        changed_other = []
        em_off = em_on = em_e = D(0)
        for kk in sorted(set(offd) | set(ond)):
            a, b = offd.get(kk), ond.get(kk)
            st = (a or b)["market_state"] or ""
            if a and b and a["pips"] == b["pips"] and a["how"] == b["how"]:
                if st.startswith(EM) and a["pips"] is not None:
                    em_off += D(a["pips"]); em_on += D(b["pips"])
                    e = research_e(a)
                    em_e += e if e is not None else D(a["pips"])
                continue
            if not st.startswith(EM) or not (a and b):
                changed_other.append((kk, a, b))
                continue
            e = research_e(a)
            em_off += D(a["pips"]); em_on += D(b["pips"]); em_e += e if e is not None else D(a["pips"])
            moves = "; ".join(f"{m['time_utc'][11:16]} to {D(m['level']):.1f} (+{D(m['pips']):g}, {m['by']})"
                              for m in b["stop_moves"])
            out.append(f"| {b['opened_uk']} | {b['strategy']} | {b['direction']} | {st} | {a['best']} | "
                       f"{a['how']}, {a['pips']} | {b['how']}, {b['pips']} | {moves} | "
                       f"{'not +10' if e is None else f'{e:+.1f}'} |")
        out += ["", f"Emerging-trend trades in both runs: ladder off **{em_off:+.1f}**, ladder on **{em_on:+.1f}** "
                f"(change {em_on - em_off:+.1f}); the research's exit e applied to the same off trades: **{em_e:+.1f}**.", ""]
        totals[wk] = (em_off, em_on, em_e)
        if changed_other:
            out += ["Other differences between the runs (a trade in only one run, or a trade from another state):", ""]
            for kk, a, b in changed_other:
                t = a or b
                out.append(f"- {t['opened_uk']} {t['strategy']} {t['direction']} ({t['market_state']}): "
                           f"off {'—' if not a else (a['how'], a['pips'])}, on {'—' if not b else (b['how'], b['pips'])}")
        else:
            out += ["No other trade differs: every trade from another state, and every trade not in emerging trend, is "
                    "identical in both runs.", ""]
        out.append("")
    t_off = sum(v[0] for v in totals.values()); t_on = sum(v[1] for v in totals.values()); t_e = sum(v[2] for v in totals.values())
    out += [f"**Both weeks, emerging-trend trades:** ladder off {t_off:+.1f}, ladder on {t_on:+.1f}, "
            f"the research's exit e on the same trades {t_e:+.1f}.", ""]
    print("\n".join(out))


if __name__ == "__main__":
    main()
