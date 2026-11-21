"""Phase 2 (research only): one row per UK weekday from phase 1's trades and the validated store.

Signal (Johnny's trend-day signal): a slow grind trade is in profit, measured on the price IG would close it at
(a buy on the sell price, a sell on the buy price, against its fill), at any point in 06:00-09:00 UK.
  * entry candle: counted only if the candle CLOSED in profit (a candle does not say whether its high came before
    or after the entry);
  * the candle the trade closed in: counted if it closed in profit (lock or take profit), or if that candle OPENED
    in profit;
  * every candle in between: its best price (buy: sell high; sell: buy low) beyond the fill.
up = only buys in profit in the window; down = only sells; both = buys and sells (not a trend day); none.
Signal time = the start of the first 5-minute candle in the window in which it was in profit.

Rest of the day: 5-minute candles starting 09:00 to 20:25 UK (sell / chart price). Open = the 09:00 candle's open,
close = the 20:25 candle's close; biggest move up/down = highest high / lowest low against the open.

Hugging the band (direction up; down is the mirror), on the chart price, the bot's indicators (prices.indicators):
  * Bollinger 20, 2 and the 5-minute 8 EMA (the EMA pullback's fast EMA, the near edge of the 8/13/21 cluster),
    both at each candle including its own close, computed on the continuous 5-minute series;
  * a candle TOUCHES the band if its high reaches the upper band; it REACHES THE CLUSTER if its low reaches the 8 EMA;
  * a candle is HUGGING if it does not reach the cluster, and it touches the band or the candle before was hugging.
    (So a hug starts at a band touch and lasts until a pullback reaches the 8 EMA.) Worked from 00:00 UK so a hug
    can carry into 09:00; counted only on the 09:00-20:25 candles.
Big news: the bot's own table (news.calendar.big_news_windows: config/news_table.toml) on Finnhub's past calendar.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from config.settings_loader import load_settings
from news.calendar import big_news_windows
from prices.indicators import bollinger, ema
from prices.model import parse_iso
from prices.store import CandleStore

UK, UTC = ZoneInfo("Europe/London"), timezone.utc
ENV, CAL, WEEKS, OUTCSV = sys.argv[1], sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
s = load_settings(switches_from=ENV).for_pair("GBPUSD")
store = CandleStore(s.candles.folder, 999999)
ppp = Decimal(s.market.points_per_pip)
calendar = json.load(open(CAL))["events"]

FIRST, LAST = date(2024, 1, 8), date(2026, 11, 19)
candles = store.read_range("5m", parse_iso("2024-01-01T00:00:00Z"), parse_iso("2026-11-20T00:00:00Z"))
by_start = {c.start: c for c in candles}
band = bollinger(candles, "sell", s.indicators.bollinger_periods, s.indicators.bollinger_std_devs)
e8 = ema(candles, "sell", s.ema_pullback.fast_ema_periods)
e21 = ema(candles, "sell", s.ema_pullback.slow_ema_periods)

trades = []
for line in WEEKS.read_text().splitlines():
    if line.strip():
        trades += json.loads(line)["trades"]
by_day = defaultdict(list)
for t in trades:
    t["opened_t"], t["closed_t"] = parse_iso(t["opened"]), parse_iso(t["closed_bar"])
    by_day[t["opened_t"].astimezone(UK).date()].append(t)

news = big_news_windows(s, s.market.pair, parse_iso("2024-01-01T00:00:00Z"), parse_iso("2026-11-21T00:00:00Z"), calendar)
news_by_day = defaultdict(list)
for w in news:
    lt = w.release_utc.astimezone(UK)
    news_by_day[lt.date()].append((lt.time(), f"{w.currency} {w.event}"))


def at(day, hh, mm):
    return datetime.combine(day, time(hh, mm), tzinfo=UK).astimezone(UTC)


def slots(a, b):
    out, t = [], a
    while t < b:
        out.append(t)
        t += timedelta(minutes=5)
    return out


def in_profit_time(t, w0, w1):
    """The first candle start in [w0, w1) at which trade t was in profit (IG close price), or None."""
    fill, buy = Decimal(t["fill"]), t["direction"] == "buy"
    k = t["opened_t"]
    while k <= t["closed_t"]:
        c = by_start.get(k)
        if c is not None and w0 <= k < w1:
            if k == t["opened_t"]:
                ok = (c.sell_close > fill) if buy else (c.buy_close < fill)
                if k == t["closed_t"]:
                    ok = ok or (t["pips"] is not None and Decimal(t["pips"]) > 0)
            elif k == t["closed_t"]:
                ok = (t["pips"] is not None and Decimal(t["pips"]) > 0) or \
                     ((c.sell_open > fill) if buy else (c.buy_open < fill))
            else:
                ok = (c.sell_high > fill) if buy else (c.buy_low < fill)
            if ok:
                return k
        k += timedelta(minutes=5)
    return None


def hug(day, up, emas=None):
    emas = emas or e8
    """(hugging candles, band touches, longest hug in candles, session candles present) for 09:00-20:25."""
    run = False
    hugging = touches = longest = cur = n = 0
    for k in slots(at(day, 0, 0), at(day, 20, 30)):
        c = by_start.get(k)
        b, e = band.get(k), emas.get(k)
        if c is None or b is None or e is None:
            continue
        touch = (c.sell_high >= b.upper) if up else (c.sell_low <= b.lower)
        cluster = (c.sell_low <= e) if up else (c.sell_high >= e)
        run = (not cluster) and (touch or run)
        if k >= at(day, 9, 0):
            n += 1
            touches += touch
            if run:
                hugging += 1
                cur += 1
                longest = max(longest, cur)
            else:
                cur = 0
    return hugging, touches, longest, n


rows = []
d = FIRST
while d <= LAST:
    if d.weekday() < 5:
        early = sum(by_start.get(k) is not None for k in slots(at(d, 0, 0), at(d, 6, 0)))
        win = sum(by_start.get(k) is not None for k in slots(at(d, 6, 0), at(d, 9, 0)))
        rest_c = [by_start[k] for k in slots(at(d, 9, 0), at(d, 20, 30)) if k in by_start]
        ok = early >= 65 and win >= 33 and len(rest_c) >= 124 and at(d, 9, 0) in by_start and at(d, 20, 25) in by_start
        row = {"day": d.isoformat(), "weekday": d.strftime("%a"), "candles_00_06": early, "candles_06_09": win,
               "candles_09_2030": len(rest_c), "usable": ok}
        first = {}
        for t in by_day.get(d, []):
            k = in_profit_time(t, at(d, 6, 0), at(d, 9, 0))
            if k is not None and (t["direction"] not in first or k < first[t["direction"]]):
                first[t["direction"]] = k
        row["trades_opened"] = len(by_day.get(d, []))
        row["trades_opened_before_0900"] = sum(t["opened_t"] < at(d, 9, 0) for t in by_day.get(d, []))
        row["buy_in_profit_0609"] = first["buy"].astimezone(UK).strftime("%H:%M") if "buy" in first else ""
        row["sell_in_profit_0609"] = first["sell"].astimezone(UK).strftime("%H:%M") if "sell" in first else ""
        sig = "both" if len(first) == 2 else "up" if "buy" in first else "down" if "sell" in first else "none"
        row["signal"] = sig
        row["signal_time_uk"] = (first["buy" if sig == "up" else "sell"].astimezone(UK).strftime("%H:%M")
                                 if sig in ("up", "down") else "")
        if ok:
            o, cl = rest_c[0].sell_open, rest_c[-1].sell_close
            hi, lo = max(c.sell_high for c in rest_c), min(c.sell_low for c in rest_c)
            row["net_up_pips"] = float((cl - o) / ppp)
            row["max_up_pips"] = float((hi - o) / ppp)
            row["max_down_pips"] = float((o - lo) / ppp)
            for name, up in (("up", True), ("down", False)):
                h, tch, lg, n = hug(d, up)
                row[f"hug_share_{name}"] = round(h / n, 4) if n else None
                row[f"band_touches_{name}"] = tch
                row[f"longest_hug_min_{name}"] = lg * 5
                h2, _, lg2, _ = hug(d, up, e21)
                row[f"hug21_share_{name}"] = round(h2 / n, 4) if n else None
                row[f"longest_hug21_min_{name}"] = lg2 * 5
        nl = news_by_day.get(d, [])
        row["big_news_0900_2030"] = "; ".join(f"{x:%H:%M} {e}" for x, e in nl if time(9, 0) <= x < time(20, 30))
        row["big_news_other_times"] = "; ".join(f"{x:%H:%M} {e}" for x, e in nl if not (time(9, 0) <= x < time(20, 30)))
        if sig in ("up", "down"):
            st = first["buy" if sig == "up" else "sell"].astimezone(UK).time()
            row["big_news_after_signal"] = "; ".join(f"{x:%H:%M} {e}" for x, e in nl if x > st)
        else:
            row["big_news_after_signal"] = ""
        rows.append(row)
    d += timedelta(days=1)

keys = []
for r in rows:
    for k in r:
        if k not in keys:
            keys.append(k)
with OUTCSV.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=keys)
    w.writeheader()
    w.writerows(rows)
print(len(rows), "days;", sum(r["usable"] for r in rows), "usable")
