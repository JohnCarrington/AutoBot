"""Trade by trade comparison of two research replays (research.long_replay), with the cause of each difference,
from the runs' own records and their candle stores. Read only.

    .venv/bin/python -m research.replay_compare RUN_A STORE_A RUN_B STORE_B
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from prices.model import UK, parse_iso
from prices.store import CandleStore
from research.long_replay import compare, keyed, load_trades


def records(run: Path) -> dict:
    """Every decision line the engine recorded in a run, by kind."""
    out: dict = {"analyser state change": [], "idea": [], "order": [], "trade manager": []}
    for p in sorted(Path(run).glob("engine/*/records/*/paper/decisions.jsonl")):
        for line in p.read_text().splitlines():
            d = json.loads(line)
            if d.get("kind") in out:
                out[d["kind"]].append(d)
    for v in out.values():
        v.sort(key=lambda d: d["time_utc"])
    return out


def state_at(rec: dict, t: str) -> str:
    """The analyser's state after the last change at or before t (UTC ISO)."""
    last = None
    for d in rec["analyser state change"]:
        if d["time_utc"] > t:
            break
        last = d
    return f"{last['state']} {last['direction']}" if last else "consolidation none"


def _candle(store: CandleStore, t: str):
    tt = parse_iso(t)
    got = [c for c in store.read_range("5m", tt, tt + timedelta(minutes=5)) if c.start == tt]
    return got[0] if got else None


def candle_diff(sa: CandleStore, sb: CandleStore, t: str) -> str:
    a, b = _candle(sa, t), _candle(sb, t)
    if a is None or b is None:
        return "missing in " + ("A" if a is None else "B")
    if a.prices() == b.prices():
        return ""
    sell = [b.sell_open - a.sell_open, b.sell_high - a.sell_high, b.sell_low - a.sell_low, b.sell_close - a.sell_close]
    buy = [b.buy_open - a.buy_open, b.buy_high - a.buy_high, b.buy_low - a.buy_low, b.buy_close - a.buy_close]
    return ("sell O/H/L/C " + "/".join(f"{x:+}" for x in sell) + ", buy " + "/".join(f"{x:+}" for x in buy))


def recent_diffs(sa: CandleStore, sb: CandleStore, t: str, n: int = 12) -> int:
    tt = parse_iso(t)
    a = {c.start: c.prices() for c in sa.read_range("5m", tt - timedelta(minutes=5 * n), tt)}
    b = {c.start: c.prices() for c in sb.read_range("5m", tt - timedelta(minutes=5 * n), tt)}
    return sum(1 for k in a.keys() | b.keys() if a.get(k) != b.get(k))


def why_missing(k: tuple, here: str, other: dict, sa: CandleStore, sb: CandleStore, rec_here: dict) -> str:
    """Why the trade with key k (taken in run `here`) is not in the other run."""
    t, strategy, direction = k[:3]
    if k[3] > 0:
        return "a further copy of a trade opened in the same minute: the other run opened fewer copies"
    ideas = [d for d in other["idea"] if d["time_utc"] == t and d["strategy"] == strategy and d["direction"] == direction]
    if ideas:
        d = ideas[0]
        if not d["allowed"]:
            return f"the other run had the idea but it was blocked: {d['blocked_by']}"
        orders = [o for o in other["order"] if o["time_utc"] == t and o["strategy"] == strategy
                  and o["direction"] == direction]
        if orders and orders[0]["result"] not in ("opened", "sent"):
            return f"the other run's safety rules refused it: {'; '.join(orders[0].get('reasons') or [orders[0]['result']])}"
        return "the other run had the idea and sent it, at a different moment or price"
    st_here, st_other = state_at(rec_here, t), state_at(other, t)
    cd = candle_diff(sa, sb, t)
    rd = recent_diffs(sa, sb, t)
    if st_here != st_other:
        return f"the analyser's state differed: {st_here} here, {st_other} in the other run" + (
            f" ({rd} of the 12 candles before differ)" if rd else " (the 12 candles before are the same)")
    if cd:
        return f"no idea in the other run: the entry candle differs ({cd})"
    if rd:
        return f"no idea in the other run: {rd} of the 12 candles before it differ"
    return "same candles and state at that moment: an earlier difference (an open trade, a setup or a level) decided it"


def explain(run_a: Path, store_a: Path, run_b: Path, store_b: Path) -> dict:
    ta, tb = load_trades(run_a), load_trades(run_b)
    ra, rb = records(run_a), records(run_b)
    sa, sb = CandleStore(store_a, 10 ** 6), CandleStore(store_b, 10 ** 6)
    c = compare(ta, tb)
    A, B = keyed(ta), keyed(tb)
    rows = []
    for k in c["only_a"]:
        rows.append({"key": k, "a": A[k].pips, "b": None, "cause": why_missing(k, "A", rb, sa, sb, ra)})
    for k in c["only_b"]:
        rows.append({"key": k, "a": None, "b": B[k].pips, "cause": why_missing(k, "B", ra, sb, sa, rb)})
    for k in c["different_result"]:
        a, b = A[k], B[k]
        bits = []
        if a.fill != b.fill:
            bits.append(f"filled at {a.fill} and {b.fill}")
        if (a.how_closed, a.closed_utc) != (b.how_closed, b.closed_utc):
            bits.append(f"closed {a.how_closed} at {_uk(a.closed_utc)} ({a.why}) and {b.how_closed} at "
                        f"{_uk(b.closed_utc)} ({b.why})")
        n = sum(1 for x in sa.read_range("5m", parse_iso(k[0]), parse_iso(max(a.closed_utc, b.closed_utc) or k[0]))
                if (_candle(sb, x.start.strftime("%Y-%m-%dT%H:%M:%SZ")) or x).prices() != x.prices())
        rows.append({"key": k, "a": a.pips, "b": b.pips, "cause": "; ".join(bits) + (
            f" ({n} candles differ while it was open)" if n else " (the candles while it was open are the same)")})
    rows.sort(key=lambda r: r["key"])
    return {"compare": c, "rows": rows, "a": ta, "b": tb}


def _uk(t: str) -> str:
    return parse_iso(t).astimezone(UK).strftime("%a %d %b %H:%M") if t else "?"


def cause_kind(cause: str) -> str:
    """A short label for a cause, for counting."""
    for k, label in (("in a big-news window", "news: big-news window"),
                     ("big-news day", "news: a big-news day's direction"),
                     ("before big news", "news: closed before big news"),
                     ("further copy", "fewer or more copies in the same minute"),
                     ("analyser's state differed", "analyser's state differed"),
                     ("entry candle differs", "entry candle differs"),
                     ("candles before it differ", "candles before it differ"),
                     ("earlier difference", "an earlier difference"),
                     ("already has", "safety: a trade of that strategy already open"),
                     ("refused", "safety rules (other)"),
                     ("does not allow", "analyser's state did not allow it"),
                     ("blocked", "blocked by another rule"),
                     ("sent it, at a different", "opened at a different moment"),
                     ("closed", "closed differently"), ("filled", "filled differently")):
        if k in cause:
            return label
    return "other"


def main(argv: list[str] | None = None) -> int:
    a = argv or sys.argv[1:]
    r = explain(Path(a[0]), Path(a[1]), Path(a[2]), Path(a[3]))
    c = r["compare"]
    print(f"same: {len(c['same'])}; different result: {len(c['different_result'])}; only in A: {len(c['only_a'])}; "
          f"only in B: {len(c['only_b'])}")
    print(Counter(cause_kind(x["cause"]) for x in r["rows"]))
    for x in r["rows"]:
        t, s, d, n = x["key"]
        print(f"{_uk(t)}  {s:17} {d:4}{' #' + str(n + 1) if n else '   '}  A {x['a'] or '-':>7}  B {x['b'] or '-':>7}  {x['cause']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
