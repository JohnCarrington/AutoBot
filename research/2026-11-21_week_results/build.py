"""Week 16-20 Nov 2026 results table (owner's brief, 21 Nov 2026). Read-only: reads /opt/autobot/data, writes
week_results.csv and summary.md next to this file. Never contacts IG.

Run from the repository root:
    AUTOBOT_ENV_FILE=/opt/autobot/.env .venv/bin/python research/2026-11-21_week_results/build.py

Sources, in order of preference:
  * IG: every data/orders/ig_check_result*.json (IG's activity and transactions, read by the price service's read-only
    IG check), then IG's own deal confirmations and close activity copied into data/orders/GBPUSD/orders.jsonl
    ("opened" level/stop_level/limit_level; "closed at IG" ig_level; "closed" level = IG's confirmation).
  * The bot: data/records/GBPUSD/trades.jsonl (strategy, analyser state at open, close reason).
  * Candles: the stored 5-minute, hourly and daily candles (buy and sell prices). Indicators and levels are worked out
    with the bot's own code (prices.indicators, levels.current) on the chart (sell) price, as the bot does.
UK time = UTC in November (GMT), so every time below is both.
"""
from __future__ import annotations

import csv
import glob
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from config.pairs import choose_pair  # noqa: E402
from config.settings_loader import load_or_exit  # noqa: E402
from levels.current import build as build_levels  # noqa: E402
from prices.indicators import bollinger, ema, macd, rsi  # noqa: E402
from prices.store import CandleStore  # noqa: E402

UTC = timezone.utc
DATA = Path("/opt/autobot/data")
OUT = Path(__file__).resolve().parent
FROM = datetime(2026, 11, 16, 0, 0, tzinfo=UTC)
UNTIL = datetime(2026, 11, 20, 22, 0, tzinfo=UTC)
FIVE = timedelta(minutes=5)

# Price-service starts ("Trading ON" in logs/prices.log*) and the commit checked out then (git reflog). There was no
# restart after 19 Nov 18:44, so 02f6c7e ran to the end of the week (checkouts of 26c06fc, bb085f4 and 5d7942e on
# 19-20 Nov were not loaded by the running price service).
VERSIONS = [
    ("2026-11-15T17:47:46", "9b61661"),
    ("2026-11-16T23:07:38", "e595f6e"),
    ("2026-11-16T23:47:07", "aea2275"),
    ("2026-11-17T20:24:41", "233d054"),
    ("2026-11-17T20:46:38", "cc70dc5"),
    ("2026-11-18T13:36:02", "3d50353"),
    ("2026-11-19T09:49:56", "d9e5d0e"),
    ("2026-11-19T18:44:38", "02f6c7e"),
]


def T(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "")).replace(tzinfo=UTC)


def iso(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def r1(x) -> str:
    return "" if x is None else f"{float(x):.1f}"


def version_at(t: datetime) -> str:
    v = ""
    for start, commit in VERSIONS:
        if t >= T(start):
            v = commit
    return v


def session(t: datetime) -> str:
    """UK (= GMT) clock. Asian 00:00-07:00 (the bot's Asian range), London 07:00-13:00, London/NY overlap
    13:00-17:00 (New York opens 08:00 ET = 13:00 GMT; London's FX session ends about 17:00), New York 17:00-22:00."""
    m = t.hour * 60 + t.minute
    if m < 7 * 60:
        return "Asian"
    if m < 13 * 60:
        return "London"
    if m < 17 * 60:
        return "London/NY overlap"
    if m < 22 * 60:
        return "New York"
    return "Asian"


# ---------------------------------------------------------------- IG's figures
def load_ig():
    acts, txs = {}, {}
    for f in sorted(glob.glob(str(DATA / "orders" / "ig_check_result*.json"))):
        r = json.load(open(f))
        for a in r.get("activity") if isinstance(r.get("activity"), list) else []:
            acts[(a.get("dealId"), a.get("date"), a.get("description"))] = a
        for x in r.get("transactions") if isinstance(r.get("transactions"), list) else []:
            txs[(x.get("reference"), x.get("dateUtc"), x.get("size"))] = x
    return list(acts.values()), list(txs.values())


def ig_trades():
    acts, txs = load_ig()
    opened = {a["dealId"]: a for a in acts if a.get("description", "").startswith("Position opened")}
    closes = defaultdict(list)
    for a in acts:
        for act in (a.get("details") or {}).get("actions") or []:
            if act.get("actionType") in ("POSITION_CLOSED", "POSITION_PARTIALLY_CLOSED"):
                closes[act.get("affectedDealId")].append(a)
    return opened, closes, txs


# ---------------------------------------------------------------- candles
def load_5m() -> dict[datetime, dict]:
    c = {}
    for f in sorted(glob.glob(str(DATA / "candles/GBPUSD/5m/2026-11-1[5-9].csv")) +
                    glob.glob(str(DATA / "candles/GBPUSD/5m/2026-11-2[0-1].csv"))):
        for r in csv.DictReader(open(f)):
            c[T(r["start_utc"])] = {k: float(v) for k, v in r.items() if k.startswith(("buy_", "sell_"))}
    return c


def last_finished(store, tf, as_of, count):
    out = []
    for day in reversed(store.days(tf)):
        if day > as_of.date():
            continue
        out = sorted((c for c in store.read_day(tf, day) if c.end <= as_of), key=lambda c: c.start) + out
        if len(out) >= count:
            break
    return out[-count:]


def path_stats(c5, buy, fill, opened, closed, close_price):
    """Best and worst pips (close side: a buy on the sell price, a sell on the buy price) from the 5-minute candles.
    Known points only: the fill; the entry candle in full only if the fill came within 10 s of its start, otherwise
    only its close; every candle that started and finished while the trade was open; the open of the candle the
    trade closed in; and the close price. The part of the closing candle before the close is not known (its high and
    low may have come after the close), so it is left out. Times are to the candle (5-minute resolution): a candle's
    extreme is timed at the candle's start (or the fill, if later); its close at its end."""
    pts = [(0.0, opened)]                                       # (pips in favour, time)

    def fav(p):
        return round((p - fill) if buy else (fill - p), 1)

    start = opened - timedelta(minutes=opened.minute % 5, seconds=opened.second)
    k = c5.get(start)
    entry_full = k is not None and (opened - start).total_seconds() <= 10 and start + FIVE <= closed
    notes = []
    if k is None:
        notes.append("entry 5-min candle missing")
    elif start + FIVE <= closed:
        if entry_full:
            hi, lo = (k["sell_high"], k["sell_low"]) if buy else (k["buy_low"], k["buy_high"])
            pts += [(fav(hi), opened), (fav(lo), opened), (fav(k["sell_close" if buy else "buy_close"]), start + FIVE)]
        else:
            pts.append((fav(k["sell_close" if buy else "buy_close"]), start + FIVE))
    t = start + FIVE
    while t + FIVE <= closed:
        k = c5.get(t)
        if k is None:
            notes.append(f"5-min candle {t:%d %H:%M} missing")
        else:
            hi, lo = (k["sell_high"], k["sell_low"]) if buy else (k["buy_low"], k["buy_high"])
            pts += [(fav(hi), t), (fav(lo), t), (fav(k["sell_close" if buy else "buy_close"]), t + FIVE)]
        t += FIVE
    if t < closed and t > opened:                                # the closing candle's open is a known point
        k = c5.get(t)
        if k is not None:
            pts.append((fav(k["sell_open" if buy else "buy_open"]), t))
    pts.append((fav(close_price), closed))
    return pts, notes


def best_worst(pts, opened, upto=None):
    sel = [p for p in pts if upto is None or p[1] <= upto]
    b = max(sel, key=lambda p: (p[0], -p[1].timestamp()))
    w = min(sel, key=lambda p: (p[0], p[1].timestamp()))
    mins = lambda p: int((p[1] - opened).total_seconds() // 60)  # noqa: E731
    best, worst = max(b[0], 0.0), max(-w[0], 0.0)
    return best, (mins(b) if best > 0 else 0), worst, (mins(w) if worst > 0 else 0)


# ---------------------------------------------------------------- main
def main() -> None:
    s = choose_pair(load_or_exit(), "GBPUSD")
    store = CandleStore(s.candles.folder, s.candles.compress_after_days)
    side = s.chart.price
    c5 = load_5m()
    opened_ig, closes_ig, txs = ig_trades()

    journal = defaultdict(list)
    for line in open(DATA / "orders/GBPUSD/orders.jsonl"):
        j = json.loads(line)
        if j.get("reference"):
            journal[j["reference"]].append(j)
    rec_o, rec_c = {}, {}
    for line in open(DATA / "records/GBPUSD/trades.jsonl"):
        r = json.loads(line)
        if r.get("paper"):
            continue
        (rec_o if r["event"] == "opened" else rec_c)[r["reference"]] = r

    trades = []
    for ref, o in rec_o.items():
        opened = T(o["opened_utc"])
        if not (FROM <= opened < UNTIL):
            continue
        c = rec_c.get(ref)
        deal = o["deal_id"]
        buy = o["direction"] == "buy"
        sign = 1 if buy else -1
        jo = next((j for j in journal[ref] if j["event"] == "opened"), {})
        igo = opened_ig.get(deal)
        notes = []
        if igo:
            fill = float(igo["details"]["level"])
            stop = float(igo["details"]["stopLevel"])
            limit = float(igo["details"]["limitLevel"])
            opened = T(igo["date"])
            src_open = "IG activity"
        else:
            fill, stop, limit = float(jo["level"]), float(jo["stop_level"]), float(jo["limit_level"])
            opened = T(jo["opened_utc"])
            src_open = "IG deal confirmation (orders journal)"
        # close: IG transactions (size-weighted), then IG close activity, then IG's confirmation / close activity in
        # the orders journal
        igo_date = igo["date"] if igo else None
        tx = [x for x in txs if igo_date and x.get("openDateUtc")
              and abs((T(x["openDateUtc"]) - T(igo_date)).total_seconds()) <= 3 and float(x["openLevel"]) == fill]
        igc = sorted(closes_ig.get(deal, []), key=lambda a: a["date"])
        jc = [j for j in journal[ref] if j["event"] in ("closed at IG", "closed", "closed by owner")]
        if tx:
            tot = sum(abs(float(x["size"])) for x in tx)
            close_px = sum(float(x["closeLevel"]) * abs(float(x["size"])) for x in tx) / tot
            closed = max(T(x["dateUtc"]) for x in tx)
            src_close = "IG transactions"
            ig_gbp = sum(float(x["profitAndLoss"].replace("£", "")) for x in tx)
        elif igc:
            close_px = float(igc[-1]["details"]["level"])
            closed = T(igc[-1]["date"])
            src_close, ig_gbp = "IG activity", None
        elif jc:
            j = jc[-1]
            close_px = float(j.get("ig_level") or j["level"])
            closed = T(j.get("ig_time_utc") or j["time_utc"])
            src_close = "IG close activity (orders journal)" if j.get("ig_level") else "IG deal confirmation (orders journal)"
            ig_gbp = j.get("profit")
        else:
            close_px = closed = None
            src_close, ig_gbp = "", None
        if igc:
            closed = T(igc[-1]["date"])                       # IG's own close time
        channel = igc[-1]["channel"] if igc else next((j.get("ig_channel") for j in jc if j.get("ig_channel")), "")
        if c and close_px is not None and c.get("close_price") and abs(float(c["close_price"]) - close_px) > 0.05:
            notes.append(f"bot close {c['close_price']} vs IG {close_px:.1f}: IG used")
        if c and closed and abs((T(c["closed_utc"]) - closed).total_seconds()) > 60:
            notes.append(f"bot close time {c['closed_utc'][11:19]} vs IG {closed:%H:%M:%S}: IG used")

        pips = round(sign * (close_px - fill), 1)
        how = c["how_closed"] if c else ""
        why = c["close_reason"] if c else ""
        if how == "stopped by IG":
            by = "IG stop"
            reason = "stop at IG" + (f" (trailed to {close_px:.1f})" if abs(close_px - stop) > 0.05 else "")
        elif how == "take profit hit at IG":
            by, reason = "IG limit", "take profit at IG"
        elif how == "closed by owner":
            by, reason = "Johnny by hand", "closed by hand at IG (channel SYSTEM, not at stop or limit)"
        elif how == "forced close" and "20:30" in why:
            by, reason = "20:30 close", "20:30 UK close"
        else:
            by, reason = "bot", why.replace(" (IG's level)", "")
        if how == "forced close" and "20:30" not in why:
            reason = why.replace(" (IG's level)", "")
        if by in ("IG stop", "IG limit", "Johnny by hand") and channel and channel != "SYSTEM":
            notes.append(f"IG channel {channel}")
        if by in ("bot", "20:30 close") and channel and channel != "PUBLIC_WEB_API":
            notes.append(f"IG channel {channel}")

        trades.append(dict(ref=ref, o=o, opened=opened, closed=closed, buy=buy, fill=fill, stop=stop, limit=limit,
                           close_px=close_px, pips=pips, ig_gbp=ig_gbp, by=by, reason=reason, notes=notes,
                           src=f"open: {src_open}; close: {src_close}"))
    trades.sort(key=lambda x: x["opened"])

    rows = []
    for x in trades:
        o, opened, closed, buy, fill = x["o"], x["opened"], x["closed"], x["buy"], x["fill"]
        notes = list(x["notes"])
        stop_p = round(abs(fill - x["stop"]), 1)
        tp_p = round(abs(x["limit"] - fill), 1)

        pts, pn = path_stats(c5, buy, fill, opened, closed, x["close_px"])
        notes += pn
        mfe, mfe_m, mae, mae_m = best_worst(pts, opened)
        f_b, _, f_w, _ = best_worst(pts, opened, opened + timedelta(minutes=15))
        f15_note = "trade open under 15 min: its whole life" if closed < opened + timedelta(minutes=15) else ""

        # levels as the bot had them at the entry (pivots from the previous trading day's sell candle)
        ll = build_levels(s, store, opened)
        piv = [(l.type, float(l.price)) for l in ll.levels if l.type in ("pivot", "R1", "R2", "R3", "S1", "S2", "S3")]
        above = sorted([p for p in piv if p[1] > fill], key=lambda p: p[1])
        below = sorted([p for p in piv if p[1] < fill], key=lambda p: -p[1])
        ahead, behind = (above, below) if buy else (below, above)
        lv_ahead = f"{ahead[0][0]} {ahead[0][1]:.1f}" if ahead else ""
        lv_ahead_p = r1(abs(ahead[0][1] - fill)) if ahead else ""
        lv_behind = f"{behind[0][0]} {behind[0][1]:.1f}" if behind else ""
        lv_behind_p = r1(abs(behind[0][1] - fill)) if behind else ""
        if not ahead:
            notes.append("no daily pivot level ahead (beyond R3/S3)")
        if not behind:
            notes.append("no daily pivot level behind (beyond R3/S3)")
        lv_warn = [w for w in ll.warnings if "pivot" in w]

        # 5-minute indicators at the last finished candle before the fill (what the bot could see)
        k5 = last_finished(store, "5m", opened, 2000)
        last5 = k5[-1]
        bb = bollinger(k5, side, s.indicators.bollinger_periods, s.indicators.bollinger_std_devs)[last5.start]
        e8 = float(ema(k5, side, 8)[last5.start])
        m = macd(k5, side, 35, 45, 30)[last5.start]
        rs = rsi(k5, side, 3)[last5.start]
        up, mid, lo = float(bb.upper), float(bb.middle), float(bb.lower)
        bbpos = ("outside upper" if fill > up else "upper half" if fill >= mid else
                 "lower half" if fill >= lo else "outside lower")

        k1 = last_finished(store, "1h", opened, 2000)
        last1 = k1[-1]
        h8, h13, h21 = (float(ema(k1, side, p)[last1.start]) for p in (8, 13, 21))
        stack = "stacked up" if h8 > h13 > h21 else "stacked down" if h8 < h13 < h21 else "mixed"

        # spread: IG's buy minus sell at the open of the 5-minute candle the fill came in, when the fill came within
        # 60 s of that open; otherwise only when the spread was the same at that candle's open and close
        cs = opened - timedelta(minutes=opened.minute % 5, seconds=opened.second)
        k = c5.get(cs)
        spread, spread_note = "", ""
        if k is None:
            spread_note = "entry 5-min candle missing"
        else:
            so, sc = round(k["buy_open"] - k["sell_open"], 1), round(k["buy_close"] - k["sell_close"], 1)
            if (opened - cs).total_seconds() <= 60:
                spread, spread_note = r1(so), f"at the candle open {cs:%H:%M}, fill {int((opened - cs).total_seconds())} s later"
            elif so == sc:
                spread, spread_note = r1(so), f"same at the {cs:%H:%M} candle's open and close"
            else:
                spread_note = f"fill mid-candle; spread {so:.1f} at {cs:%H:%M} open, {sc:.1f} at its close"

        # other trades open the other way at the fill
        opp = [f"{y['o']['strategy']} {y['o']['direction']} {y['opened']:%H:%M}" for y in trades
               if y is not x and y["buy"] != buy and y["opened"] <= opened and (y["closed"] is None or y["closed"] > opened)]

        # the day's range: UK day 00:00-24:00, sell price (as the chart and the bot's daily candles)
        day0 = opened.replace(hour=0, minute=0, second=0)
        dk = [v for t, v in c5.items() if day0 <= t < day0 + timedelta(days=1)]
        drange = r1(max(v["sell_high"] for v in dk) - min(v["sell_low"] for v in dk))

        rows.append({
            "date": f"{opened:%a %d %b}", "open_time_uk": f"{opened:%H:%M:%S}",
            "close_time_uk": f"{closed:%H:%M:%S}" + (f" ({closed:%a})" if closed.date() != opened.date() else ""),
            "minutes_open": int((closed - opened).total_seconds() // 60),
            "strategy": o["strategy"], "direction": o["direction"], "code_version": version_at(opened),
            "entry_ig": f"{fill:.1f}", "stop_level": f"{x['stop']:.1f}", "tp_level": f"{x['limit']:.1f}",
            "stop_pips": r1(stop_p), "tp_pips": r1(tp_p), "risk_reward": f"1:{tp_p / stop_p:.2f}",
            "close_ig": f"{x['close_px']:.1f}", "pips": r1(x["pips"]), "gbp_at_10": f"{x['pips'] * 10:.2f}",
            "ig_pnl_gbp": "" if x["ig_gbp"] is None else f"{float(x['ig_gbp']):.2f}",
            "close_reason": x["reason"], "closed_by": x["by"],
            "analyser_state_at_open": o["market_state"],
            "mfe_pips": r1(mfe), "mfe_min_after_entry": mfe_m, "mae_pips": r1(mae), "mae_min_after_entry": mae_m,
            "first15_best_pips": r1(f_b), "first15_worst_pips": r1(f_w), "first15_note": f15_note,
            "session": session(opened),
            "level_ahead": lv_ahead, "pips_to_level_ahead": lv_ahead_p,
            "level_behind": lv_behind, "pips_to_level_behind": lv_behind_p,
            "bb5_position": bbpos, "pips_from_ema8_5m": r1(fill - e8),
            "h1_ema_8_13_21": stack, "h1_vs_ema21": "above" if fill > h21 else "below",
            "rsi3_5m": r1(rs), "macd_hist_5m": f"{float(m.histogram):.2f}",
            "spread_at_entry": spread, "spread_note": spread_note,
            "opposite_trade_open": "; ".join(opp),
            "day_range_pips": drange,
            "sources": x["src"],
            "notes": "; ".join(notes + lv_warn),
            "reference": x["ref"],
        })

    with open(OUT / "week_results.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "trades written")


if __name__ == "__main__":
    main()
