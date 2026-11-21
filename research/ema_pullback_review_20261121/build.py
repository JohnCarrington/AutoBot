"""EMA pullback live review, 9-20 Nov 2026 (Johnny's brief, 21 Nov 2026). READ-ONLY.

Reads /opt/autobot/data (records, orders journal, IG check results, candles, news calendar) and the bot's own code
from an exact `git archive` copy of the live commit 5d7942e (EMA pullback code identical to 02f6c7e and f99efe1).
Writes only results.json next to this file. Never contacts IG. Prints nothing secret.

Run:  AUTOBOT_ENV_FILE=/opt/autobot/.env /opt/autobot/.venv/bin/python -I build.py <code-copy-dir>
"""
from __future__ import annotations

import csv
import glob
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

CODE = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(CODE))
os.chdir(CODE)

from config.pairs import choose_pair  # noqa: E402
from config.settings_loader import load_or_exit  # noqa: E402
from analyser.indicators import last_candles  # noqa: E402
from analyser.market_state import MemoStore  # noqa: E402
from levels.current import build as build_levels  # noqa: E402
from levels.rules import PIVOT  # noqa: E402
from prices.calendar import MarketHours  # noqa: E402
from prices.indicators import ema  # noqa: E402
from prices.store import CandleStore  # noqa: E402
from strategies.common import forced_close_at, EMA_PULLBACK  # noqa: E402
from strategies.ema_pullback.strategy import EmaPullback, HourlyTrendReader  # noqa: E402
import news.calendar as ncal  # noqa: E402


class _NoWrite:                       # big_news_windows notes unmatched events to a file: never write it here
    def __init__(self, *a, **k): pass
    def note(self, *a, **k): return False


ncal.UnmatchedLog = _NoWrite

UTC = timezone.utc
DATA = Path("/opt/autobot/data")
OUT = Path(__file__).resolve().parent
REPO = "/opt/autobot"
FROM = datetime(2026, 11, 9, 0, 9, 52, tzinfo=UTC)
UNTIL = datetime(2026, 11, 20, 22, 0, tzinfo=UTC)
FIVE = timedelta(minutes=5)


def T(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "")).replace(tzinfo=UTC)


def iso(t):
    return None if t is None else t.strftime("%Y-%m-%dT%H:%M:%SZ")


def f1(x):
    return None if x is None else round(float(x), 1)


# ------------------------------------------------------------------ which commit was live
def trading_on_lines():
    """Every 'Trading ON' line in logs/prices.log* with file and line number."""
    out = []
    for f in sorted(glob.glob(f"{REPO}/logs/prices.log*")):
        if f.endswith(".started"):
            continue
        for n, line in enumerate(open(f, errors="replace"), 1):
            if "autobot.trading: Trading ON" in line:
                out.append((line[:19], os.path.basename(f), n, line.rstrip("\n")))
    return sorted(out)


def reflog():
    r = subprocess.run(["git", "-C", REPO, "reflog", "--date=iso-strict", "--format=%h|%gd|%gs"],
                       capture_output=True, text=True, check=True).stdout.splitlines()
    out = []
    for line in r:
        h, gd, gs = line.split("|", 2)
        m = re.search(r"\{(.+)\}", gd)
        out.append((datetime.fromisoformat(m.group(1)).astimezone(UTC), h, gs))
    return list(reversed(out))                 # oldest first, in the order HEAD moved


def head_at(t, rl):
    h = None
    for when, commit, _ in rl:
        if when <= t:
            h = commit
    return h


def git_show(commit, path):
    r = subprocess.run(["git", "-C", REPO, "show", f"{commit}:{path}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def ema_code_facts(commit):
    strat = git_show(commit, "strategies/ema_pullback/strategy.py")
    common = git_show(commit, "strategies/common.py")
    return {
        "slope": "signed (must point the trade's way)" if "sign = 1 if d == BUY" in strat else "size only (abs)",
        "hourly_read_gate_in_code": "TREND_STRATEGIES" in common and "hourly_read" in common,
        "trend_still_going_in_code": "trend_still_going" in common,
        "analyser_governs_all_in_code": "TREND_GROUP" in common,
        "level_stops_in_code": "LEVEL_STOP_STRATEGIES" in common,
        "ema_rollover_window_in_code": "ep.rollover_no_new_trades_from" in common,
    }


# ------------------------------------------------------------------ IG
def load_ig():
    acts, txs = {}, {}
    for f in sorted(glob.glob(str(DATA / "orders" / "ig_check_result*.json"))):
        r = json.load(open(f))
        for a in r.get("activity") if isinstance(r.get("activity"), list) else []:
            acts[(a.get("dealId"), a.get("date"), a.get("description"))] = (a, os.path.basename(f))
        for x in r.get("transactions") if isinstance(r.get("transactions"), list) else []:
            txs[(x.get("reference"), x.get("dateUtc"), x.get("size"))] = (x, os.path.basename(f))
    opened = {a["dealId"]: (a, f) for a, f in acts.values() if a.get("description", "").startswith("Position opened")}
    closes = defaultdict(list)
    for a, f in acts.values():
        for act in (a.get("details") or {}).get("actions") or []:
            if act.get("actionType") in ("POSITION_CLOSED", "POSITION_PARTIALLY_CLOSED"):
                closes[act.get("affectedDealId")].append((a, f))
    return opened, closes, list(txs.values())


# ------------------------------------------------------------------ main
def main():
    s = choose_pair(load_or_exit(), "GBPUSD")
    store = CandleStore(s.candles.folder, s.candles.compress_after_days)
    memo = MemoStore(store)
    side = s.chart.price
    ppp = Decimal(s.market.points_per_pip)
    hours = MarketHours(s.market_hours)
    e = s.ema_pullback
    res = {"settings": {"points_per_pip": str(ppp), "chart_price": side, "slow_ema": e.slow_ema_periods,
                        "fast_ema": e.fast_ema_periods, "expire_min": e.setup_expires_after_minutes,
                        "stop_pips_env": s.switches.stop_loss_pips_ema_pullback, "tp_pips": e.take_profit_pips}}

    # ---- versions
    rl = reflog()
    starts = []
    for stamp, fname, n, line in trading_on_lines():
        t = datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)   # GMT = UTC in November
        if t < datetime(2026, 11, 9, tzinfo=UTC):
            continue
        c = head_at(t, rl)
        code_as_of = subprocess.run(["git", "-C", REPO, "log", "-1", "--format=%h %cs %s", c, "--", ".",
                                     ":!research", ":!docs"], capture_output=True, text=True).stdout.strip()
        starts.append({"start": iso(t), "file": f"logs/{fname}", "line": n, "quote": line, "head": c,
                       "code_as_of": code_as_of, "ema_code": ema_code_facts(c)})
    res["versions"] = starts

    def version_at(t):
        v = None
        for x in starts:
            if T(x["start"]) <= t:
                v = x
        return v

    # ---- records
    dec_path = DATA / "records/GBPUSD/decisions.jsonl"
    ideas = []
    for n, line in enumerate(open(dec_path), 1):
        j = json.loads(line)
        if j.get("kind") == "idea" and j.get("strategy") == EMA_PULLBACK and not j.get("paper"):
            ideas.append((n, j, line.rstrip("\n")))
    trades_path = DATA / "records/GBPUSD/trades.jsonl"
    rec_o, rec_c = {}, {}
    for n, line in enumerate(open(trades_path), 1):
        j = json.loads(line)
        if j.get("strategy") == EMA_PULLBACK and not j.get("paper"):
            (rec_o if j["event"] == "opened" else rec_c)[j["reference"]] = (n, j)
    journal = defaultdict(list)
    for n, line in enumerate(open(DATA / "orders/GBPUSD/orders.jsonl"), 1):
        j = json.loads(line)
        if j.get("reference"):
            journal[j["reference"]].append((n, j, line.rstrip("\n")))
    ig_open, ig_closes, ig_txs = load_ig()

    trades = []
    for ref, (on, o) in rec_o.items():
        opened_bot = T(o["opened_utc"])
        if not (FROM <= opened_bot < UNTIL):
            continue
        cn, c = rec_c.get(ref, (None, None))
        deal = o["deal_id"]
        buy = o["direction"] == "buy"
        js = next(((n, j) for n, j, _ in journal[ref] if j["event"] == "sending"), (None, {}))
        jo = next(((n, j) for n, j, _ in journal[ref] if j["event"] == "opened"), (None, {}))
        igo = ig_open.get(deal)
        if igo:
            fill, stop, limit, opened = (float(igo[0]["details"]["level"]), float(igo[0]["details"]["stopLevel"]),
                                         float(igo[0]["details"]["limitLevel"]), T(igo[0]["date"]))
            src_open = f"IG activity ({igo[1]}, dealId {deal})"
        else:
            j = jo[1]
            fill, stop, limit, opened = float(j["level"]), float(j["stop_level"]), float(j["limit_level"]), T(j["opened_utc"])
            src_open = f"IG deal confirmation in orders.jsonl line {jo[0]}"
        tx = [x for x, f in ig_txs if igo and x.get("openDateUtc")
              and abs((T(x["openDateUtc"]) - T(igo[0]["date"])).total_seconds()) <= 3 and float(x["openLevel"]) == fill]
        igc = sorted(ig_closes.get(deal, []), key=lambda af: af[0]["date"])
        jc = [(n, j) for n, j, _ in journal[ref] if j["event"] in ("closed at IG", "closed", "closed by owner", "gone at IG")]
        channel = igc[-1][0].get("channel") if igc else next((j.get("ig_channel") for n, j in jc if j.get("ig_channel")), None)
        if tx:
            tot = sum(abs(float(x["size"])) for x in tx)
            close_px = sum(float(x["closeLevel"]) * abs(float(x["size"])) for x in tx) / tot
            closed = max(T(x["dateUtc"]) for x in tx)
            src_close = "IG transactions"
        elif igc:
            close_px, closed = float(igc[-1][0]["details"]["level"]), T(igc[-1][0]["date"])
            src_close = f"IG activity ({igc[-1][1]})"
        elif jc:
            n, j = jc[-1]
            close_px = float(j.get("ig_level") or j["level"])
            closed = T(j.get("ig_time_utc") or j["time_utc"])
            src_close = f"orders.jsonl line {n} ({'IG close activity' if j.get('ig_level') else 'IG deal confirmation'})"
        else:
            close_px = closed = None
            src_close = "none"
        if igc:
            closed = T(igc[-1][0]["date"])
        pips = round((close_px - fill) if buy else (fill - close_px), 1)
        how = c["how_closed"] if c else None
        owner = how == "closed by owner"
        at_stop = abs(close_px - stop) <= 0.05
        at_limit = abs(close_px - limit) <= 0.05
        steps = o.get("steps") or []
        touch = None
        for st in steps:
            m = re.match(r"\w{3} (\d\d) Nov (\d\d):(\d\d) GMT: price (dropped|rose) to the 5-minute", st)
            if m:
                touch = datetime(2026, 11, int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=UTC)
        setup_entry = next((float(re.match(r"entry ([\d.]+):", st).group(1)) for st in steps
                            if re.match(r"entry [\d.]+:", st)), None)
        live_tick = next((st for st in steps if st.startswith("reached on the live price")), None)
        m = re.search(r"at (\d\d:\d\d:\d\d) UTC \(bid ([\d.]+), offer ([\d.]+)\)", live_tick or "")
        tick_time = (datetime.combine(opened_bot.date(), datetime.strptime(m.group(1), "%H:%M:%S").time(), UTC)
                     if m else None)
        idea_line = next(((n, j) for n, j, _ in ideas if j.get("live") and j["time_utc"] == o["opened_utc"]
                          and j["direction"] == o["direction"]), (None, None))
        v = version_at(opened)
        trades.append({
            "ref": ref, "deal": deal, "direction": o["direction"], "buy": buy,
            "trades_line_open": on, "trades_line_close": cn, "idea_line": idea_line[0],
            "sending_line": js[0], "opened_line": jo[0],
            "commit": v["head"], "commit_start": v["start"], "slope_code": v["ema_code"]["slope"],
            "state_at_open": o["market_state"], "steps": steps, "touch": iso(touch),
            "setup_entry": setup_entry, "wanted_entry": float(o["entry_price"]),
            "idea_price_journal": js[1].get("idea_price"),
            "tick_time": iso(tick_time), "tick_bid": float(m.group(2)) if m else None,
            "tick_offer": float(m.group(3)) if m else None,
            "sending_time": js[1].get("time_utc"), "journal_opened_time": jo[1].get("time_utc"),
            "opened": iso(opened), "fill": fill, "stop": stop, "limit": limit,
            "closed": iso(closed), "close_px": close_px, "pips": pips, "how_closed_bot": how,
            "close_reason_bot": c["close_reason"] if c else None, "ig_channel": channel,
            "owner_close": owner, "at_stop": at_stop, "at_limit": at_limit,
            "src": f"open: {src_open}; close: {src_close}",
            "bot_pips_record": c.get("pips") if c else None, "bot_close_record": c.get("close_price") if c else None,
        })
    trades.sort(key=lambda x: x["opened"])
    res["trades"] = trades

    # ---- hourly slopes at each trade's touch (problem 1)
    def hourly_at(t_end):
        return HourlyTrendReader(s, last_candles(memo, "1h", t_end, e.hourly_history_candles))

    # Until the 11 Nov 14:56:48 start (04b3a83, "The strategies read the candle store afresh on every call"), the live
    # strategies read the hourly candles as stored when the service started. Emulated: the hourly reader as of the
    # start of the run that was live when the candle finished (checked below against every logged step 0).
    FRESH_FROM = datetime(2026, 11, 11, 14, 56, 48, tzinfo=UTC)
    stale_runs = [T(x["start"]) for x in starts if T(x["start"]) < FRESH_FROM]

    def live_hourly_at(t_end):
        if t_end >= FRESH_FROM:
            return hourly_at(t_end), "fresh"
        run = max([r for r in stale_runs if r <= t_end], default=stale_runs[0])
        return hourly_at(run), f"stale: hourly candles as stored at the {run:%d %b %H:%M:%S} start"

    def signed_slopes(reader, t):
        done = [k for k in reader.candles if k.end <= t]
        n = e.hourly_slope_candles
        now, prev, back = done[-1].start, done[-2].start, done[-1 - n].start
        vals = {}
        for name, d in (("8", reader.f), ("13", reader.m), ("20", reader.sl)):
            vals[name] = {"now": float(d[now]), "prev": float(d[prev]), "back3": float(d[back]),
                          "slope_3h": round(float((d[now] - d[back]) / n / ppp), 3),
                          "change_1h": round(float((d[now] - d[prev]) / ppp), 3)}
        return {"hourly_candle": iso(now), "back3_candle": iso(back), "emas": vals}

    for x in trades:
        if x["touch"]:
            t = T(x["touch"])
            sign = 1 if x["buy"] else -1
            rd = hourly_at(t + FIVE)                        # the true hourly EMAs at the touch
            x["hourly"] = signed_slopes(rd, t)
            x["slopes_against"] = [k for k, v in x["hourly"]["emas"].items() if sign * v["slope_3h"] < 0]
            lrd, how = live_hourly_at(t + FIVE)             # what the live bot read
            x["hourly_live"] = signed_slopes(lrd, t)
            x["hourly_live_how"] = how
            x["hourly_why_recomputed"] = lrd.at(t).why
            x["slopes_against_live"] = [k for k, v in x["hourly_live"]["emas"].items() if sign * v["slope_3h"] < 0]

    # ---- news (problem 3)
    cal = json.load(open(DATA / "news/calendar.json"))["events"]
    wins = ncal.big_news_windows(s, "GBPUSD", FROM - timedelta(days=1), UNTIL + timedelta(days=1), cal)
    res["big_releases"] = [{"release": iso(w.release_utc), "currency": w.currency, "event": w.event} for w in wins]
    for x in trades:
        o_, c_ = T(x["opened"]), T(x["closed"])
        x["news_open_window"] = [f"{w.currency} {w.event} {w.release_utc:%a %d %b %H:%M}" for w in wins
                                 if w.release_utc - timedelta(minutes=15) <= o_ <= w.release_utc + timedelta(minutes=30)]
        x["news_while_open"] = [f"{w.currency} {w.event} {w.release_utc:%a %d %b %H:%M}" for w in wins
                                if o_ < w.release_utc < c_]

    # ---- hours (problem 4); UK = UTC in November
    for x in trades:
        o_, c_ = T(x["opened"]), T(x["closed"])
        m = o_.hour * 60 + o_.minute + o_.second / 60
        x["opened_outside_0600_2030"] = not (6 * 60 <= m < 20 * 60 + 30)
        cuts = []
        d = o_.date()
        while d <= c_.date():
            cut = datetime(d.year, d.month, d.day, 20, 30, tzinfo=UTC)
            if o_ < cut < c_:
                cuts.append(iso(cut))
            d += timedelta(days=1)
        x["held_past_2030"] = cuts
        x["overnight"] = c_.date() != o_.date()

    # ---- overlaps (problem 2)
    ov = []
    for i, a in enumerate(trades):
        for b in trades[i + 1:]:
            if T(b["opened"]) < T(a["closed"]) and T(a["opened"]) < T(b["closed"]):
                ov.append((a["ref"], b["ref"]))
    res["overlap_pairs"] = ov

    # ---- reconstruct every setup from the stored candles with the bot's own class (Parts 2 and 3)
    weeks = []
    for probe in (datetime(2026, 11, 10, 12, tzinfo=UTC), datetime(2026, 11, 17, 12, tzinfo=UTC)):
        op, cl = hours.session(probe)
        weeks.append((op, min(cl, UNTIL)))
    setups, nonsetups = [], []
    c5 = {}
    for op, cl in weeks:
        warm = last_candles(memo, "5m", op, s.market_states.indicator_warm_up_candles)
        week = [k for k in memo.read_range("5m", op, cl) if k.end <= cl]
        allc = warm + week
        fast, slow = ema(allc, side, e.fast_ema_periods), ema(allc, side, e.slow_ema_periods)
        e100 = ema(allc, side, s.analyser.direction_ema_periods)
        for k in week:
            c5[k.start] = {"c": k, "slow": slow.get(k.start), "fast": fast.get(k.start), "e100": e100.get(k.start)}
        pb = EmaPullback(s, hourly_at(op))
        live = {}
        prev_e100 = None
        for k in week:
            pb.hourly = live_hourly_at(k.end)[0]
            before = {id(st): st for st in pb.setups}
            nb = len(pb.notes)
            pb.on_candle(k, fast.get(k.start), slow.get(k.start))
            new_notes = pb.notes[nb:]
            after = {id(st) for st in pb.setups}
            for sid, st in before.items():
                if sid not in after:
                    tag = f"setup from {st.touch.start.strftime('%H:%M')} GMT"
                    note = next((t for (tm, d, t) in new_notes if d == st.direction and t.startswith(tag)), "")
                    r = live.pop(sid)
                    r["end_candle"], r["end_note"] = iso(k.start), note
                    r["outcome"] = ("reached" if "reached the entry" in note else "cancelled" if "cancelled" in note
                                    else "expired" if "expired" in note else "?")
                    if r["outcome"] == "reached":
                        r["entry_fill_candle_price"] = re.search(r": entry ([\d.]+)$", note).group(1)
                        r["pivot"] = next((float(lv.price) for lv in build_levels(s, memo, k.start).levels
                                           if lv.type == PIVOT), None)
                        r["e100_prev"] = f1(prev_e100)
                    setups.append(r)
            for st in pb.setups:
                if id(st) not in before:
                    live[id(st)] = {"direction": st.direction, "touch": iso(st.touch.start), "entry": float(st.entry),
                                    "steps": list(st.steps)}
            for (tm, d, t) in new_notes:
                if t.startswith("touched the 8 EMA"):
                    nonsetups.append({"time": iso(tm), "direction": d, "note": t})
            prev_e100 = e100.get(k.start)
        for sid, r in live.items():
            r["outcome"], r["end_candle"], r["end_note"] = "open at week end", None, ""
            setups.append(r)
    setups.sort(key=lambda r: (r["touch"], r["direction"], r["entry"]))
    res["nonsetup_counts"] = {
        "hourly_not_qualified": sum("hourly trend is not qualified" in n["note"] for n in nonsetups),
        "touch_candle_closed_past_21": sum("touch candle closed" in n["note"] for n in nonsetups),
    }

    # signed slope at each setup's touch, and the commit live then
    for r in setups:
        t = T(r["touch"])
        rd = hourly_at(t + FIVE)
        ss = signed_slopes(rd, t)
        sign = 1 if r["direction"] == "buy" else -1
        r["slopes_against"] = [kk for kk, vv in ss["emas"].items() if sign * vv["slope_3h"] < 0]
        lrd, how = live_hourly_at(t + FIVE)
        lss = signed_slopes(lrd, t)
        r["slopes_against_live"] = [kk for kk, vv in lss["emas"].items() if sign * vv["slope_3h"] < 0]
        r["hourly_live_how"] = how
        r["slopes_3h"] = {kk: vv["slope_3h"] for kk, vv in ss["emas"].items()}
        v = version_at(t)
        r["commit_at_touch"] = v["head"] if v else "(before 9 Nov 00:09 start)"
        r["slope_code_at_touch"] = v["ema_code"]["slope"] if v else ""

    # ---- wick past the 21 EMA without a close past it (Part 3)
    for r in setups:
        buy = r["direction"] == "buy"
        t0 = T(r["touch"])
        end = T(r["end_candle"]) if r["end_candle"] else None
        wicks, entry_candle_wick = [], None
        t = t0
        while end is None or t <= end:
            if t not in c5:
                if end is None or t > end:
                    break
                t += FIVE
                continue
            k, sl = c5[t]["c"], c5[t]["slow"]
            lo, hi, cl = (float(getattr(k, f"{side}_low")), float(getattr(k, f"{side}_high")),
                          float(getattr(k, f"{side}_close")))
            slf = float(sl)
            beyond = round(((slf - lo) if buy else (hi - slf)) / float(ppp), 1)
            closed_past = (cl < slf) if buy else (cl > slf)
            if end is not None and t == end and r["outcome"] == "reached":
                if beyond > 0 and not closed_past:
                    entry_candle_wick = {"candle": iso(t), "pips": beyond}
                break
            if end is not None and t == end and r["outcome"] == "cancelled":
                break
            if end is not None and t == end and r["outcome"] == "expired":
                break                                     # the expiry candle is not part of the setup
            if beyond > 0 and not closed_past:
                wicks.append({"candle": iso(t), "pips": beyond, "ema21": round(slf, 1),
                              "low" if buy else "high": lo if buy else hi, "close": cl})
            t += FIVE
            if end is None and t > UNTIL:
                break
        r["wicks"] = wicks
        r["max_wick"] = max((w["pips"] for w in wicks), default=0.0)
        r["entry_candle_wick"] = entry_candle_wick

    # ---- match logged ideas and trades to reconstructed setups
    reached = defaultdict(list)
    for r in setups:
        if r["outcome"] == "reached":
            reached[(r["end_candle"], r["direction"], float(r["entry_fill_candle_price"]))].append(r)
    for n, j, _ in ideas:
        if j.get("live"):
            continue
        key = (j["time_utc"], j["direction"], float(j["entry_price"]))
        got = reached.get(key)
        if got:
            for r in got:
                r.setdefault("logged_lines", []).append(n)
    for x in trades:
        m = [r for r in setups if r["outcome"] == "reached" and r["touch"] == x["touch"]
             and r["direction"] == x["direction"] and x["setup_entry"] is not None
             and abs(r["entry"] - x["setup_entry"]) < 0.05]
        x["setup_match"] = bool(m)
        if m:
            m[0].setdefault("trade_refs", []).append(x["ref"])
            x["wicks"], x["max_wick"], x["entry_candle_wick"] = m[0]["wicks"], m[0]["max_wick"], m[0]["entry_candle_wick"]
        else:
            x["wicks"], x["max_wick"], x["entry_candle_wick"] = None, None, None

    # ---- blocked ideas: parts, values, look back
    blocked = []
    for n, j, raw in ideas:
        if j["allowed"]:
            continue
        b = j["blocked_by"]
        parts = [p.strip() for p in b.split("; ")]
        state_fail = [p for p in parts if p.startswith("the analyser's state is") or
                      re.match(r"the (emerging trend|trend) is (up|down): EMA pullback only in the trend's direction", p)]
        dr = next((p for p in parts if p.startswith("the direction rule says")), None)
        other = [p for p in parts if p not in state_fail and p != dr]
        t = T(j["time_utc"])
        key = (j["time_utc"], j["direction"], float(j["entry_price"]))
        rs = reached.get(key, [])
        r0 = rs[0] if rs else None
        pivot = r0["pivot"] if r0 else next((float(lv.price) for lv in build_levels(s, memo, t).levels
                                             if lv.type == PIVOT), None)
        e100v = r0["e100_prev"] if r0 else (f1(c5[t - FIVE]["e100"]) if (t - FIVE) in c5 else None)
        ent = float(j["entry_price"])
        buy = j["direction"] == "buy"
        piv_ok = None if pivot is None else ((ent > pivot) if buy else (ent < pivot))
        e_ok = None if e100v is None else ((ent > e100v) if buy else (ent < e100v))
        if dr:
            m = re.search(r"price [\d.]+ is (above|below) the pivot ([\d.]+) and (above|below) the 5m 100 EMA ([\d.]+)", dr)
            if m:
                piv_ok = (m.group(1) == "above") if buy else (m.group(1) == "below")
                e_ok = (m.group(3) == "above") if buy else (m.group(3) == "below")
                pivot_logged, e100_logged = float(m.group(2)), float(m.group(4))
            else:
                pivot_logged = e100_logged = None
        else:
            pivot_logged = e100_logged = None
        v = version_at(t)
        # look back from the entry candle: fill as the bot's engine sets it on a finished candle (a buy at the entry
        # plus that candle's open spread; a sell at the entry), stop 12 and take profit 30 on the closing price side
        k = c5.get(t, {}).get("c")
        lb = None
        if k is not None:
            fill = ent + (float(k.buy_open) - float(k.sell_open)) if buy else ent
            stop_px = fill - 12 * float(ppp) if buy else fill + 12 * float(ppp)
            tp_px = fill + 30 * float(ppp) if buy else fill - 30 * float(ppp)
            cut = forced_close_at(s, EMA_PULLBACK, t)
            tt = t
            lb = {"fill": round(fill, 1), "stop": round(stop_px, 1), "tp": round(tp_px, 1), "result": None,
                  "until": iso(min(cut, UNTIL))}
            while tt < min(cut, UNTIL):
                kk = c5.get(tt, {}).get("c")
                if kk is not None:
                    if buy:
                        hs, ht = float(kk.sell_low) <= stop_px, float(kk.sell_high) >= tp_px
                    else:
                        hs, ht = float(kk.buy_high) >= stop_px, float(kk.buy_low) <= tp_px
                    first = tt == t
                    if hs or ht:
                        what = ("stop and take profit in the same candle (order unknown)" if hs and ht else
                                "stop (12 against) first" if hs else "take profit (30 for) first")
                        lb["result"] = what + (" - in the entry candle itself, where the order of prices after the "
                                               "entry is unknown" if first else "")
                        lb["at"] = iso(tt)
                        break
                tt += FIVE
            if lb["result"] is None:
                lb["result"] = f"neither by {lb['until']} (the EMA pullback's Friday 20:30 UK close or the data end)"
        blocked.append({"line": n, "raw": raw, "time": j["time_utc"], "direction": j["direction"], "entry": ent,
                        "state": j["state"], "state_check": "blocked" if state_fail else "passed",
                        "state_text": state_fail, "direction_rule_text": dr,
                        "pivot_check": "blocked" if piv_ok is False else "passed" if piv_ok else "unknown",
                        "e100_check": "blocked" if e_ok is False else "passed" if e_ok else "unknown",
                        "pivot": pivot_logged if pivot_logged is not None else pivot,
                        "e100": e100_logged if e100_logged is not None else e100v,
                        "values_from": "the bot's own blocked_by text" if dr else "worked out with the bot's code",
                        "other_checks": other, "commit": v["head"], "slope_code": v["ema_code"]["slope"],
                        "matched_setup": bool(r0), "lookback": lb,
                        "max_wick": r0["max_wick"] if r0 else None, "wicks": r0["wicks"] if r0 else None})
    res["blocked"] = blocked
    res["setups"] = setups
    res["ideas_lines"] = [(n, j) for n, j, _ in ideas]

    # values on allowed trades for checking the worked-out pivot / 100 EMA against the bot's own step text
    chk = []
    for x in trades:
        st = next((q for q in x["steps"] if q.startswith("allowed at entry")), "")
        m = re.search(r"the pivot ([\d.]+) and (above|below) the 5m 100 EMA ([\d.]+)", st)
        r = next((r for r in setups if x["ref"] in r.get("trade_refs", [])), None)
        if m and r:
            chk.append({"ref": x["ref"], "pivot_logged": float(m.group(1)), "pivot_worked": r.get("pivot"),
                        "e100_logged": float(m.group(3)), "e100_worked": r.get("e100_prev")})
    res["pivot_e100_check"] = chk

    json.dump(res, open(OUT / "results.json", "w"), indent=1, default=str)
    print("trades", len(trades), "ideas", len(ideas), "blocked", len(blocked), "setups", len(setups))


if __name__ == "__main__":
    main()
