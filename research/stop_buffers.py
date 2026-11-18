"""Stage 4, part A (owner, 18 November 2026): measure stops placed just beyond the nearest group of levels, read-only.

Uses only the bot's own records (data/records/<PAIR>/trades.jsonl) and its stored candles; never contacts IG (no
history allowance). Sell (bid) prices for levels, UK times. Trades the owner closed by hand (closed_by "owner", IG's
SYSTEM channel) are kept apart.

    .venv/bin/python -m research.stop_buffers <out_folder>

Writes trades.json, inside_groups.json and overshoot.json to <out_folder>. Changes nothing.

How each part is measured (the choices are in the report):
  1. Each live trade of the range trade, the level reversal and the EMA pullback since 9 November 2026: the levels as
     they stood when it opened (levels.current.build, the bot's own list and its own 5-pip grouping); the nearest group
     beyond the entry on the stop side (a sell: the lowest group whose top is above the fill; a buy: the highest group
     whose bottom is below the fill); the stop at each buffer beyond that group (a sell: the group's top + buffer + the
     spread when it opened, from the bot's own "bid, offer" record; a buy: the group's bottom - buffer). Each stop is
     replayed through the bot's own trade manager (trade_manager.manager.step) on the stored 5-minute candles from the
     opening candle with the trade's own take profit, scheduled close and (range trade) the close at the opposite band.
     The range trade's close on a level rejection is left out (it needs the analyser's live rejections).
  2. Every live trade (all strategies): whether its stop, on the chart price, sat inside a level group (from its lowest
     to its highest level) when it opened, whether it was stopped, and whether the candle that stopped it closed back
     on the trade's side of the stop (a spike that turned back), and what price did next that day.
  3. The last two weeks of 5-minute candles: every rejection setup of the bot's own rejection part at a level group
     that turned back (reached its confirmation candle), and how far its furthest point went past the group's far
     edge; and the setups at a level group that did not turn back.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from config.settings_loader import load_settings
from levels.current import build
from prices.indicators import bollinger
from prices.store import CandleStore
from analyser.market_state import MemoStore
from trade_manager.manager import STOPPED_BY_IG, TAKE_PROFIT_AT_IG, Bar, plan, step

UTC = timezone.utc
STRATS = ("range trade", "level reversal", "EMA pullback")
BUFFERS = (2, 3, 4, 5, 6)
D = Decimal


def t_(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def five(t: datetime) -> datetime:
    return t.replace(minute=t.minute - t.minute % 5, second=0, microsecond=0)


def spread_at_open(r: dict) -> Decimal | None:
    for s in r.get("steps") or []:
        m = re.search(r"\(bid ([\d.]+), offer ([\d.]+)\)", s)
        if m:
            return D(m.group(2)) - D(m.group(1))
    return None


def trades(settings) -> list[dict]:
    rows = [json.loads(x) for x in open(Path(settings.records.folder) / settings.market.pair / "trades.jsonl")]
    opened = {r["reference"]: r for r in rows if r["event"] == "opened" and not r.get("paper")}
    closed = {r["reference"]: r for r in rows if r["event"] == "closed" and not r.get("paper")}
    return [opened[k] | {"closed": closed.get(k)} for k in opened]


def nearest_group(groups: list[dict], fill: Decimal, sell: bool) -> dict | None:
    if sell:
        up = [g for g in groups if g["high"] > fill]
        return min(up, key=lambda g: g["high"]) if up else None
    down = [g for g in groups if g["low"] < fill]
    return max(down, key=lambda g: g["low"]) if down else None


def replay(settings, store, r: dict, stop_pips: Decimal, bands: dict) -> dict:
    """The trade through the bot's own trade manager with this stop: how it ends, its best pips before then."""
    opened = t_(r["opened_utc"])
    mt = plan(settings, r["reference"], r["strategy"], r["direction"], five(opened), D(r["entry_price"]),
              D(r["open_price"]), stop_pips)
    mt.take_profit_pips = D(r["take_profit_pips"])           # the trade's own, as recorded
    best = None
    for c in store.read_range("5m", five(opened), mt.close_at + timedelta(minutes=5)):
        prev = bands.get(c.start - timedelta(minutes=5))
        band = (prev.upper, prev.lower) if prev is not None and prev.upper is not None else None
        before_best = mt.best
        out = step(settings, mt, Bar.of(c), band, [])
        if mt.best is not None:
            best = mt.best
        if not mt.open:
            d = mt.decisions[-1]
            # the best before this last bar, and this bar's own best if it did not stop out first
            if d.kind != STOPPED_BY_IG:
                sell = r["direction"] == "sell"
                side = "buy" if sell else "sell"
                bar_best = ((mt.fill - getattr(c, f"{side}_low")) if sell else (getattr(c, f"{side}_high") - mt.fill)) \
                    / D(settings.market.points_per_pip)
                best = max(x for x in (before_best, bar_best) if x is not None)
            return {"how": d.kind, "why": d.why, "at": d.at.strftime("%Y-%m-%dT%H:%M:%SZ"), "pips": str(d.pips),
                    "best_before_exit": None if best is None else str(best.quantize(D("0.1"))),
                    "reached_8": best is not None and best >= 8,
                    "target": d.kind == TAKE_PROFIT_AT_IG or (d.why == "the opposite Bollinger band"),
                    "stopped": d.kind == STOPPED_BY_IG}
    return {"how": "still open in the stored candles", "best_before_exit": None if best is None else str(best),
            "reached_8": best is not None and best >= 8, "target": False, "stopped": False}


def part1(settings, store) -> list[dict]:
    ppp = D(settings.market.points_per_pip)
    week = store.read_range("5m", datetime(2026, 11, 1, tzinfo=UTC), datetime.now(UTC))
    bands = bollinger(week, settings.chart.price, settings.indicators.bollinger_periods,
                      settings.indicators.bollinger_std_devs)
    out = []
    for r in trades(settings):
        if r["strategy"] not in STRATS or t_(r["opened_utc"]) < datetime(2026, 11, 9, tzinfo=UTC):
            continue
        sell = r["direction"] == "sell"
        fill = D(r["open_price"])
        spread = spread_at_open(r) or D(0)
        ll = build(settings, store, t_(r["opened_utc"]))
        g = nearest_group(ll.groups, fill, sell)
        row = {"reference": r["reference"], "strategy": r["strategy"], "direction": r["direction"],
               "opened_utc": r["opened_utc"], "entry_price": r["entry_price"], "fill": str(fill),
               "spread": str(spread), "level": r.get("level"), "stop_price": r["stop_price"], "stop_pips": r["stop_pips"],
               "closed_by": (r["closed"] or {}).get("closed_by"), "how_closed": (r["closed"] or {}).get("how_closed"),
               "pips": (r["closed"] or {}).get("pips"), "best_pips": (r["closed"] or {}).get("best_pips"),
               "group": None if g is None else {"low": str(g["low"]), "high": str(g["high"]),
                                                 "levels": [f"{m.type} {m.price}" for m in g["members"]]},
               "actual": replay(settings, store, r, D(r["stop_pips"]), bands), "buffers": {}}
        if g is not None:
            for b in BUFFERS:
                stop = (g["high"] + b * ppp + spread) if sell else (g["low"] - b * ppp)
                dist = ((stop - fill) if sell else (fill - stop)) / ppp
                row["buffers"][b] = {"stop": str(stop), "distance": str(dist.quantize(D("0.1"))),
                                     **replay(settings, store, r, dist, bands)}
        out.append(row)
        print(r["opened_utc"], r["strategy"], r["direction"], "group", row["group"] and row["group"]["high"], flush=True)
    return out


def part2(settings, store) -> list[dict]:
    ppp = D(settings.market.points_per_pip)
    out = []
    for r in trades(settings):
        c = r["closed"] or {}
        sell = r["direction"] == "sell"
        spread = spread_at_open(r) or D(0)
        stop = D(r["stop_price"])
        chart_stop = stop - spread if sell else stop          # where the chart (sell) price is when the stop is hit
        ll = build(settings, store, t_(r["opened_utc"]))
        inside = [g for g in ll.groups if g["low"] <= chart_stop <= g["high"] and len(g["members"]) > 1]
        row = {"reference": r["reference"], "strategy": r["strategy"], "direction": r["direction"],
               "opened_utc": r["opened_utc"], "fill": r["open_price"], "stop_price": r["stop_price"],
               "chart_stop": str(chart_stop), "how_closed": c.get("how_closed"), "closed_by": c.get("closed_by"),
               "closed_utc": c.get("closed_utc"), "pips": c.get("pips"),
               "inside_group": None if not inside else {"low": str(inside[0]["low"]), "high": str(inside[0]["high"]),
                                                        "levels": [f"{m.type} {m.price}" for m in inside[0]["members"]]}}
        # the nearest level beyond the stop (a sell: above it), and how far: a stop just in front of a level
        beyond = [lv for lv in ll.levels if (lv.price > chart_stop if sell else lv.price < chart_stop)]
        if beyond:
            lv = min(beyond, key=lambda x: abs(x.price - chart_stop))
            row["next_level_beyond_stop"] = {"level": f"{lv.type} {lv.price}",
                                             "pips": str((abs(lv.price - chart_stop) / ppp).quantize(D("0.1")))}
        if c.get("how_closed") == STOPPED_BY_IG and c.get("closed_utc"):
            hit = store.get("5m", five(t_(c["closed_utc"])))
            if hit is not None:
                close_side = hit.buy_close if sell else hit.sell_close
                row["stop_candle"] = {"start": hit.start.strftime("%H:%M"), "close": str(close_side),
                                      "closed_back": (close_side < stop) if sell else (close_side > stop)}
                # what price did next that day (to 20:30 UK, or 6 hours): the best on the trade's closing side
                fill = D(r["open_price"])
                later = store.read_range("5m", hit.end, hit.end + timedelta(hours=6))
                if later:
                    best = max(((fill - x.buy_low) if sell else (x.sell_high - fill)) / ppp for x in later)
                    row["after"] = {"best_pips_from_entry_next_6h": str(best.quantize(D("0.1")))}
        out.append(row)
    return out


def part3(settings, store, frm: datetime, to: datetime) -> dict:
    """Rejection setups at a level group (not the bands only) in the stored candles from frm to to."""
    from analyser.market_state import StateTracker
    ppp = D(settings.market.points_per_pip)
    results = []
    seen = set()
    tracker = StateTracker(settings, store)
    ends = [datetime(2026, 11, 6, 21, 0, tzinfo=UTC), datetime(2026, 11, 13, 21, 0, tzinfo=UTC), to]
    for end in ends:                                     # each trading week's replay (the tracker starts each week fresh)
        tracker.replay(end)
        for st in tracker.watcher.setups:
            key = (st.pierce.start, st.direction)
            if key in seen or not (frm <= st.pierce.start < to):
                continue
            levels = [p for p in st.pierced if "Bollinger" not in str(p["what"])]
            if not levels or st.furthest is None:
                continue
            seen.add(key)
            ll = build(settings, store, st.pierce.start)
            sell = st.direction == "sell"
            near = min(levels, key=lambda p: abs(p["price"] - (st.pierce.sell_high if sell else st.pierce.sell_low)))
            g = next((g for g in ll.groups if g["low"] <= near["price"] <= g["high"]), None)
            if g is None:
                continue
            edge = g["high"] if sell else g["low"]
            past = ((st.furthest - edge) if sell else (edge - st.furthest)) / ppp
            results.append({"pierce": st.pierce.start.strftime("%Y-%m-%dT%H:%M:%SZ"), "direction": st.direction,
                            "group": f"{g['low']}-{g['high']}", "members": len(g["members"]),
                            "status": st.status, "stage": st.stage,
                            "turned_back": st.confirmation is not None,
                            "past_far_edge_pips": str(past.quantize(D("0.1")))})
    return {"from": frm.isoformat(), "to": to.isoformat(), "setups": results}


def main(argv=None) -> int:
    args = sys.argv[1:] if argv is None else argv
    out = Path(args[0])
    out.mkdir(parents=True, exist_ok=True)
    from config.settings_loader import env_path
    s = load_settings(switches_from=Path("/opt/autobot/.env")).for_pair("GBPUSD")      # the live switches, read only
    store = MemoStore(CandleStore(s.candles.folder, s.candles.compress_after_days))
    what = args[1:] or ["1", "2", "3"]
    if "1" in what:
        (out / "trades.json").write_text(json.dumps(part1(s, store), indent=1))
    if "2" in what:
        (out / "inside_groups.json").write_text(json.dumps(part2(s, store), indent=1))
    if "3" in what:
        to = datetime(2026, 11, 18, 14, 0, tzinfo=UTC)
        (out / "overshoot.json").write_text(json.dumps(part3(s, store, to - timedelta(days=14), to), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
