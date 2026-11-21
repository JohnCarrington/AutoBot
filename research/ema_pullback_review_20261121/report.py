"""Writes DETAIL.md, trades.csv, setups.csv and blocked.csv from results.json (build.py). Read-only on the bot.

Run: python3 report.py
"""
from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = json.load(open(HERE / "results.json"))
REPO = "/opt/autobot"
LIVE = "02f6c7e"            # the code the running price service loaded on 19 Nov 18:43 (not restarted since)
UTC = timezone.utc
DATA = Path("/opt/autobot/data")


def T(s):
    return datetime.fromisoformat(s.replace("Z", "")).replace(tzinfo=UTC)


def hm(s, sec=True):
    t = T(s)
    return t.strftime("%a %d %b %H:%M:%S" if sec else "%a %d %b %H:%M")


def show(commit, path):
    return subprocess.run(["git", "-C", REPO, "show", f"{commit}:{path}"], capture_output=True, text=True,
                          check=True).stdout.splitlines()


def quote(commit, path, start_anchor, end_anchor=None, n=None, before=0):
    """Lines of path at commit, from the line containing start_anchor to the line containing end_anchor (or n lines)."""
    lines = show(commit, path)
    i = next(k for k, l in enumerate(lines) if start_anchor in l) - before
    if end_anchor is not None:
        j = next(k for k in range(i, len(lines)) if end_anchor in lines[k])
    else:
        j = i + n - 1
    body = "\n".join(f"{k + 1:4d}  {lines[k]}" for k in range(i, j + 1))
    return f"`{path}` at `{commit}`, lines {i + 1}-{j + 1}:\n\n```python\n{body}\n```\n"


def period(commit_start):
    t = T(commit_start)
    if t < T("2026-11-13T10:22:14Z"):
        return "A"
    if t < T("2026-11-19T18:44:38Z"):
        return "B"
    return "C"


PERIODS = {
    "A": "A: 9 Nov 00:09 - 13 Nov 10:22 (f99efe1 to 79c5dcf; first-build EMA pullback, slope size only)",
    "B": "B: 13 Nov 10:22 - 19 Nov 18:44 (d96de5f to d9e5d0e; slope must point the trade's way, plus later gates)",
    "C": "C: 19 Nov 18:44 - 20 Nov 22:00 (02f6c7e first-build-plus; slope size only again)",
}

trades = R["trades"]
for x in trades:
    x["period"] = period(x["commit_start"])
    x["kind"] = "owner close" if x["owner_close"] else ("IG take profit" if x["at_limit"] else
                                                        "IG stop" if x["at_stop"] else "bot close")
bot = [x for x in trades if not x["owner_close"]]
own = [x for x in trades if x["owner_close"]]


def tot(xs):
    w = sum(1 for x in xs if x["pips"] > 0)
    return f"{len(xs)} trades, {w} won, {len(xs) - w} lost, {sum(x['pips'] for x in xs):+.1f} pips"


def short(ref):
    return ref.split("-")[0]


out = []
w = out.append

# ------------------------------------------------------------------ 0. versions
w("## 0. Which code was live, and the three periods\n")
w("Every start of the price service from 9 Nov (each `Trading ON` line in the bot's log), with the commit checked out "
  "at that moment (`git reflog` of /opt/autobot, in the order HEAD moved). \"Code as of\" is the newest commit "
  "before it that changed anything outside `research/` and `docs/`. The service ran from 19 Nov 18:44 to the end of "
  "the week without a restart, so `02f6c7e` ran to the end; the later checkouts (`26c06fc` 19 Nov 20:20, `bb085f4` "
  "20 Nov 12:11, `5d7942e` 20 Nov 21:10) were never loaded. Their EMA pullback code is the same as `02f6c7e`'s. "
  "UK time is GMT in November, so every time in this report is both UK time and UTC.\n")
w("| Start (UK) | Log line (quoted) | HEAD | Code as of | EMA pullback hourly slope check | Other EMA-related code present (switch state at the time is not recorded except in the blocked reasons) |")
w("|---|---|---|---|---|---|")
for v in R["versions"]:
    ec = v["ema_code"]
    extras = [k for k, nm in (("ema_rollover_window_in_code", "21:55-22:15 rollover window"),
                              ("hourly_read_gate_in_code", "hourly read gate"),
                              ("trend_still_going_in_code", "TREND_STILL_GOING"),
                              ("analyser_governs_all_in_code", "ANALYSER_GOVERNS_ALL"),
                              ("level_stops_in_code", "LEVEL_STOPS")) if ec.get(k)]
    names = {"ema_rollover_window_in_code": "21:55-22:15 rollover window", "hourly_read_gate_in_code": "hourly read",
             "trend_still_going_in_code": "TREND_STILL_GOING", "analyser_governs_all_in_code": "ANALYSER_GOVERNS_ALL",
             "level_stops_in_code": "LEVEL_STOPS"}
    w(f"| {hm(v['start'])} | `{v['file']}:{v['line']}` `{v['quote'][24:].strip()}` | `{v['head']}` | `{v['code_as_of'][:7]}` "
      f"{v['code_as_of'][19:80]} | {ec['slope']} | {', '.join(names[k] for k in extras) or '-'} |")
w("")
w("Counts below are kept apart by period:\n")
for k, v in PERIODS.items():
    w(f"* **Period {v}**")
w("* Inside period A, until the 11 Nov 14:56:48 start (`04b3a83` \"The strategies read the candle store afresh on "
  "every call, never a copy kept from start-up\"), the live strategies judged the hourly trend from the hourly "
  "candles as they were stored when the service started. This is shown in the logged step 0 of every trade of "
  "9-11 Nov (Part 1.1), and this report reproduces it exactly.\n")

# ------------------------------------------------------------------ trades table
w("## 1. The 24 EMA pullback trades on the IG demo account\n")
w("IG's own figures are used for every open and close (IG's activity and transactions saved by the bot's read-only "
  "IG checks in `data/orders/ig_check_result*.json`; failing that, IG's confirmations copied into "
  "`data/orders/GBPUSD/orders.jsonl`). The bot's record is `data/records/GBPUSD/trades.jsonl`. Pips are IG's fill "
  "to IG's close. A close is the owner's when IG shows channel SYSTEM and the close is not at the stop or the take "
  "profit (owner rule, 11 Nov); there are 2, listed apart and left out of every result below.\n")
w("| # | Opened (IG) | Closed (IG) | Dir | Period / commit | Analyser state at open (trades.jsonl) | IG fill | IG stop | IG limit | IG close | Pips | Closed by | Record lines | Source |")
w("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for i, x in enumerate(trades, 1):
    x["n"] = i
    w(f"| {i} | {hm(x['opened'])} | {hm(x['closed'])} | {x['direction']} | {x['period']} `{x['commit']}` | {x['state_at_open']} | "
      f"{x['fill']:.1f} | {x['stop']:.1f} | {x['limit']:.1f} | {x['close_px']:.1f} | {x['pips']:+.1f} | {x['kind']}"
      f"{' (IG channel ' + x['ig_channel'] + ')' if x['ig_channel'] else ''} | trades.jsonl:{x['trades_line_open']},{x['trades_line_close']}; "
      f"orders.jsonl:{x['sending_line']},{x['opened_line']}; decisions.jsonl:{x['idea_line']} | {x['src']} |")
w("")
for p in "ABC":
    xs = [x for x in bot if x["period"] == p]
    os_ = [x for x in own if x["period"] == p]
    w(f"* Period {p}: bot's own exits {tot(xs) if xs else 'none'}; owner closes {tot(os_) if os_ else 'none'}.")
w(f"* All periods: bot's own exits {tot(bot)}; owner closes {tot(own)} (kept apart).")
diff = [x for x in trades if x["bot_pips_record"] is not None and abs(float(x["bot_pips_record"]) - x["pips"]) > 0.05]
for x in diff:
    w(f"* Trade {x['n']}: the bot's record says {x['bot_pips_record']} pips at {x['bot_close_record']}; IG's close "
      f"{x['close_px']:.1f} gives {x['pips']:+.1f}. IG's figure is used.")
w("")
tpk = {}
for line in open(DATA / "records/GBPUSD/trades.jsonl"):
    j = json.loads(line)
    if j.get("event") == "opened" and j.get("strategy") == "EMA pullback":
        tpk[j["reference"]] = j.get("take_profit_kind")
tpc = Counter((round(abs(x["limit"] - x["fill"]), 1), tpk.get(x["ref"])) for x in trades)
stc = Counter(round(abs(x["fill"] - x["stop"]), 1) for x in trades)
w("Take profit sent (IG limit minus IG fill), with the bot's `take_profit_kind` from `trades.jsonl`: "
  + "; ".join(f"{d:.0f} pips ({k}) on {v} trades" for (d, k), v in sorted(tpc.items())) + ". Stop (IG fill to IG stop): "
  + "; ".join(f"{d:.0f} pips on {v} trades" for d, v in sorted(stc.items())) + ".\n")
w("| # | Take profit pips | take_profit_kind |")
w("|---|---|---|")
for x in trades:
    w(f"| {x['n']} | {abs(x['limit'] - x['fill']):.0f} | {tpk.get(x['ref'])} |")
w("")

# ------------------------------------------------------------------ Part 1
w("# Part 1. Do the five problems really happen?\n")

# 1.1
w("## 1.1 Hourly slope direction\n")
w("**The live code (period C, and period A):** the slope is taken as a size only (`abs`).\n")
w(quote(LIVE, "strategies/ema_pullback/strategy.py", "def at(self, t: datetime)", "return HourlyTrend(d, ok, why)"))
w("Period A ran the same lines (the file is identical at `f99efe1`). **Period B** ran `f69492c`'s version "
  "(13 Nov 08:43, first live at the 13 Nov 10:22 start), where the slope must point the trade's way:\n")
w(quote("f69492c", "strategies/ema_pullback/strategy.py", "# each EMA's slope over the last n hourly candles", n=4))
w("Line 77 (both versions) already requires each hourly EMA to be higher (buy) or lower (sell) than on the hourly "
  "candle before. The `abs` on line 85 can only let through a 3-hour slope that points the other way when an EMA has "
  "turned within the last 3 hours: one hour's move the trade's way, but a net move against it over 3 hours.\n")
w("**How often it happened live: on 0 of the 24 trades.** For each trade: the logged step 0 (quoted from "
  "`trades.jsonl`, the `steps` list), the hourly candles the live bot read, and the signed 3-hour slope of each "
  "hourly EMA in pips per hour (positive = up). A slope against the trade would be negative for a buy or positive "
  "for a sell.\n")
w("| # | Dir | Touch candle | Logged step 0 (trades.jsonl line) | Hourly candles the bot read | 8 / 13 / 20 EMA 3-hour slope as read by the bot | True 8 / 13 / 20 slope at the touch | Any against? | Pips |")
w("|---|---|---|---|---|---|---|---|---|")
for x in trades:
    hl, ht = x["hourly_live"]["emas"], x["hourly"]["emas"]
    w(f"| {x['n']} | {x['direction']} | {hm(x['touch'], False)} | `{x['steps'][0]}` ({x['trades_line_open']}) | "
      f"{x['hourly_live_how'].replace('stale: ', 'as stored at start-up: ')}; last hourly candle {hm(x['hourly_live']['hourly_candle'], False)} | "
      f"{hl['8']['slope_3h']:+.2f} / {hl['13']['slope_3h']:+.2f} / {hl['20']['slope_3h']:+.2f} | "
      f"{ht['8']['slope_3h']:+.2f} / {ht['13']['slope_3h']:+.2f} / {ht['20']['slope_3h']:+.2f} | "
      f"{'yes: ' + ','.join(x['slopes_against_live']) if x['slopes_against_live'] else 'no'}"
      f"{'; true: ' + ','.join(x['slopes_against']) if x['slopes_against'] else ''} | {x['pips']:+.1f}{' (owner)' if x['owner_close'] else ''} |")
w("")
stale_n = [x["n"] for x in trades if x["hourly_live_how"].startswith("stale")]
w(f"Trades judged on hourly candles as stored at the service's start (before 11 Nov 14:56): {len(stale_n)} "
  f"(trades {', '.join(map(str, stale_n))}). Trades 2-4 on 10 Nov used the hourly candle of Mon 09 Nov 11:00.\n")
w("Check on the method: the step 0 text worked out with the bot's own `HourlyTrendReader` from the stored hourly "
  "candles (as read at the time: as stored at start-up before 11 Nov 14:56, fresh after) is character-for-character "
  "the logged text on all 24 trades.\n")
ag = [s for s in R["setups"] if s["slopes_against_live"]]
w(f"**Setups (traded or not):** of the {len(R['setups'])} setups worked out from the candles (Part 2.2), "
  f"{len(ag)} had a 3-hour slope against the setup's direction. None reached its entry price, so none could trade:\n")
w("| Touch | Dir | Slopes 8 / 13 / 20 (pips/hour) | Against | Commit at touch | Slope check in that code | What happened |")
w("|---|---|---|---|---|---|---|")
for s in ag:
    sl = s["slopes_3h"]
    w(f"| {hm(s['touch'], False)} | {s['direction']} | {sl['8']:+.2f} / {sl['13']:+.2f} / {sl['20']:+.2f} | "
      f"{','.join(s['slopes_against_live'])} | `{s['commit_at_touch']}` | {s['slope_code_at_touch']} | "
      f"{s['outcome']}: `{s['end_note']}` |")
w("")

# 1.2
w("## 1.2 Several trades at once\n")
w("**The live code.** Every touch starts its own setup, so several can run at once:\n")
w(quote(LIVE, "strategies/ema_pullback/strategy.py", "# 1. a touch candle (0. with the hourly trend)", "self.setups.append"))
w("The per-strategy limit is skipped for the EMA pullback:\n")
w(quote(LIVE, "safety/rules.py", "def _limits(settings: Any, order: Order", "if idea.strategy != EMA_PULLBACK:"))
w("and its trades are not counted towards the most at once (5):\n")
w(quote(LIVE, "strategies/common.py", "def counts_towards_most_at_once", n=3))
w("Nothing else limits how many EMA pullback trades are open at once. The engine sends at most one idea per "
  "strategy, direction and 5-minute candle:\n")
w(quote(LIVE, "trading/engine.py", "key = (idea.strategy, idea.direction, p.start)", n=4))
cl = []
used = set()
for x in trades:
    if x["ref"] in used:
        continue
    grp = [x]
    changed = True
    while changed:
        changed = False
        for y in trades:
            if y in grp:
                continue
            if any(T(y["opened"]) < T(g["closed"]) and T(g["opened"]) < T(y["closed"]) for g in grp):
                grp.append(y)
                changed = True
    if len(grp) > 1:
        grp.sort(key=lambda q: q["opened"])
        cl.append(grp)
        used |= {g["ref"] for g in grp}


def most_at_once(grp):
    ev = sorted([(T(g["opened"]), 1) for g in grp] + [(T(g["closed"]), -1) for g in grp])
    k = m = 0
    for _, d in ev:
        k += d
        m = max(m, k)
    return m


n_in = sum(len(g) for g in cl)
w(f"**How often it happened live: {len(cl)} times, involving {n_in} of the 24 trades.** Each group is a run of "
  "trades whose open times overlapped:\n")
w("| Group | Trade # | Dir | Opened | Closed | Period / commit | Pips | Closed by | Most open at once in the group |")
w("|---|---|---|---|---|---|---|---|---|")
for gi, g in enumerate(cl, 1):
    m = most_at_once(g)
    for x in g:
        w(f"| {gi} | {x['n']} | {x['direction']} | {hm(x['opened'])} | {hm(x['closed'])} | {x['period']} `{x['commit']}` | "
          f"{x['pips']:+.1f} | {x['kind']} | {m} |")
    w(f"| {gi} | total | | | | | {sum(q['pips'] for q in g):+.1f} | | |")
w("")
w(f"All the trades in each group went the same way. The 14 allowed setups that reached their entry in the same "
  "candle as a trade and were not sent (Part 2.2) are the engine's one-per-candle rule at work; they are not in this "
  "table.\n")

# 1.3
w("## 1.3 Big news\n")
w("**The live code.** For the EMA pullback, `may_open` returns before the news check, so big-news windows do not "
  "stop it opening:\n")
w(quote(LIVE, "strategies/common.py", "    if strategy == EMA_PULLBACK:\n" if False else "if strategy == EMA_PULLBACK:", "return reasons"))
w("and its open trades are not closed before big news:\n")
w(quote(LIVE, "strategies/common.py", "def closed_before_big_news", n=4))
w(quote(LIVE, "strategies/common.py", "NEWS_ALLOWED = (", n=2, before=1))
w("Big releases are taken from the bot's own news table (`config/news_table.toml`, unchanged since `f99efe1`) applied "
  "with the bot's own `news.calendar.big_news_windows` to its stored calendar `data/news/calendar.json` (it covers "
  "31 Oct onwards). The big releases for GBP or USD in the period:\n")
rels = defaultdict(list)
for b in R["big_releases"]:
    if "2026-11-09" <= b["release"][:10] <= "2026-11-20":
        rels[b["release"]].append(f"{b['currency']} {b['event']}")
w("| Release (UK) | Events |")
w("|---|---|")
for k in sorted(rels):
    w(f"| {hm(k, False)} | {'; '.join(rels[k])} |")
w("")
op = [x for x in trades if x["news_open_window"]]
wh = [x for x in trades if x["news_while_open"]]
w(f"**Opened from 15 minutes before to 30 minutes after a big release: {len(op)} trades.**\n")
for x in op:
    w(f"* Trade {x['n']}: {x['news_open_window']} {x['pips']:+.1f}")
w(f"**Still open when a big release came out: {len(wh)} trade{'s' if len(wh) != 1 else ''}.**\n")
w("| # | Dir | Opened | Closed | Release(s) while open | Pips | Closed by | Commit |")
w("|---|---|---|---|---|---|---|---|")
for x in wh:
    w(f"| {x['n']} | {x['direction']} | {hm(x['opened'])} | {hm(x['closed'])} | {'; '.join(x['news_while_open'])} | "
      f"{x['pips']:+.1f} | {x['kind']} | `{x['commit']}` |")
w("")
w("One trade is too few to say anything about how the strategy behaves around big news.\n")

# 1.4
w("## 1.4 Hours and overnight\n")
w("**The live code.** The only hours the EMA pullback keeps are: none after 20:30 UK on Friday, and (from `d96de5f`, "
  "13 Nov 10:22, and in `02f6c7e`) none from 21:55 to 22:15 UK. The same `may_open` lines as in 1.3. It is held "
  "overnight and closed only at 20:30 UK on Friday:\n")
w(quote(LIVE, "strategies/common.py", "OWN_HOURS = (", n=3, before=2))
w(quote(LIVE, "strategies/common.py", "def forced_close_at", "raise AssertionError"))
w("Period A (before `d96de5f`) had no rollover window: `f99efe1`'s `may_open` EMA branch only has the Friday rule.\n")
w(quote("f99efe1", "strategies/common.py", "if strategy == EMA_PULLBACK:", "return reasons"))
oo = [x for x in trades if x["opened_outside_0600_2030"]]
hp = [x for x in trades if x["held_past_2030"]]


def spread_at(t):
    day = t.strftime("%Y-%m-%d")
    f = DATA / f"candles/GBPUSD/5m/{day}.csv"
    if not f.exists():
        return None
    start = t - timedelta(minutes=t.minute % 5, seconds=t.second)
    for r in csv.DictReader(open(f)):
        if T(r["start_utc"]) == start:
            return (f"{float(r['buy_open']) - float(r['sell_open']):.1f} at the {start:%H:%M} candle's open, "
                    f"{float(r['buy_close']) - float(r['sell_close']):.1f} at its close")
    return None


w(f"**Opened outside 06:00-20:30 UK: {len(oo)} trades.**\n")
w("| # | Dir | Opened | Closed | Pips | Closed by | Period / commit | Spread (buy minus sell, from the stored 5-minute candles) in the candle it closed |")
w("|---|---|---|---|---|---|---|---|")
for x in oo:
    w(f"| {x['n']} | {x['direction']} | {hm(x['opened'])} | {hm(x['closed'])} | {x['pips']:+.1f} | {x['kind']} | "
      f"{x['period']} `{x['commit']}` | {spread_at(T(x['closed'])) or 'not stored'} |")
w("")
w(f"**Held past 20:30 UK: {len(hp)} trades.**\n")
w("| # | Dir | Opened | Closed | 20:30 passed | Pips | Closed by | Period / commit | Spread in the candle it closed |")
w("|---|---|---|---|---|---|---|---|---|")
for x in hp:
    w(f"| {x['n']} | {x['direction']} | {hm(x['opened'])} | {hm(x['closed'])} | {', '.join(hm(c, False) for c in x['held_past_2030'])} | "
      f"{x['pips']:+.1f} | {x['kind']} | {x['period']} `{x['commit']}` | {spread_at(T(x['closed'])) or 'not stored'} |")
w("")
t11 = next(x for x in trades if x["opened"].startswith("2026-11-12T22:00"))
w(f"Trade {t11['n']} opened at the 22:00 rollover. Its last step, quoted from `trades.jsonl` line {t11['trades_line_open']}: "
  f"`{t11['steps'][-1]}` (offer minus bid {t11['tick_offer'] - t11['tick_bid']:.1f}). IG shows the stop filled at {t11['close_px']:.1f} at {hm(t11['closed'])}, the same second "
  "it opened. This was before the 21:55-22:15 window was added (`d96de5f`, 13 Nov).\n")
w(f"Closes between 21:55 and 22:15: "
  + ", ".join(f"trade {x['n']} at {T(x['closed']):%H:%M:%S} ({x['pips']:+.1f})" for x in trades
              if (21 * 60 + 55) <= T(x['closed']).hour * 60 + T(x['closed']).minute <= 22 * 60 + 15) + ".\n")

# 1.5
w("## 1.5 Slippage and stale prices\n")
w("**The live code.** When a live price reaches the entry, the engine sends the order at once:\n")
w(quote(LIVE, "trading/engine.py", "def _live_entries(self, tick: Any)", "log.info(\"Live entry"))
w("and the order is a market order with no price or quote attached (the stop and limit are distances from IG's fill):\n")
w(quote(LIVE, "orders/sender.py", "body = {                                                # exactly AutoBot 161's 17 fields", "\"stopLevel\": None,"))
w("Nothing in `trading/engine.py`, `orders/sender.py`, `safety/rules.py` or `strategies/common.py` compares the "
  "price's age or the fill with the entry (no match for `slippage`, `stale`, `max_age` or any age check on the tick).\n")
w("**What the records hold.** The setup's entry (step `entry ...` in `trades.jsonl`); the price the idea gave "
  "(`entry_price`; it differs from the setup's entry only when the candle opened past it); the live bid and offer "
  "when the entry was reached and that price's time, which is IG's own time stamp on the price (`UTM`, "
  "`prices/feed.py`), written to the second (last step in `trades.jsonl`); the time the order went out "
  "(`sending`, `orders.jsonl`, to the second); IG's fill and open time (IG activity). The age column is the "
  "sending time minus IG's time on the price, in whole seconds (both are cut to the second, so each is +/- 1 s).\n")
w("The gap is in the trade's disfavour when positive: a buy's fill above the entry, a sell's fill below it. The "
  "chart (and the entry) is the sell (bid) price, so a buy's gap includes the spread. The last column takes the "
  "spread out: the fill against the same side of the live price that reached the entry (a buy's offer, a sell's bid).\n")
rows = []
for x in trades:
    sg = 1 if x["buy"] else -1
    gap = round(sg * (x["fill"] - x["setup_entry"]), 1) + 0.0
    same = x["tick_offer"] if x["buy"] else x["tick_bid"]
    gap_same = round(sg * (x["fill"] - same), 1) + 0.0
    tt = T(x["tick_time"])
    age = int((T(x["sending_time"]) - tt).total_seconds())
    ig_age = int((T(x["opened"]) - tt).total_seconds())
    rows.append((gap, x, same, gap_same, age, ig_age))
rows.sort(key=lambda r: (-r[0], r[1]["opened"]))
w("| # | Dir | Setup entry | Idea price | Live bid / offer at the entry (IG time) | IG fill | Gap vs setup entry (pips) | Gap vs same-side live price (pips) | Price age when sent (s) | IG open time minus price time (s) | Pips | Closed by | Commit |")
w("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for gap, x, same, gs, age, iga in rows:
    w(f"| {x['n']} | {x['direction']} | {x['setup_entry']:.1f} | {x['wanted_entry']:.1f} | {x['tick_bid']:.1f} / {x['tick_offer']:.1f} "
      f"({T(x['tick_time']):%d %b %H:%M:%S}) | {x['fill']:.1f} | {gap:+.1f} | {gs:+.1f} | {age} | {iga} | {x['pips']:+.1f} | {x['kind']} | `{x['commit']}` |")
w("")
gaps = [r[0] for r in rows]
w(f"Gap vs the setup's entry: largest {max(gaps):+.1f}, smallest {min(gaps):+.1f}. Gap vs the same-side live price: "
  f"largest {max(r[3] for r in rows):+.1f}, smallest {min(r[3] for r in rows):+.1f}. Price age when sent: "
  f"{min(r[4] for r in rows)} to {max(r[4] for r in rows)} s.\n")

# ------------------------------------------------------------------ Part 2
w("# Part 2. How well does the direction rule work?\n")
w("## 2.1 The live code\n")
w("Which states allow the EMA pullback, and only in the trend's direction:\n")
w(quote(LIVE, "strategies/common.py", "ALLOWED_IN = {", "EMA_PULLBACK: {EMERGING"))
w("The check (state, then the direction rule; the EMA pullback is not in `NO_DIRECTION_RULE`):\n")
w(quote(LIVE, "strategies/common.py", "def allowed(settings: Any, strategy: str", "return reasons, rule"))
w("The direction rule itself (pivot and 5-minute 100 EMA must agree):\n")
w(quote(LIVE, "analyser/direction.py", "def decide(price: Decimal | None", "return d(NONE, said + \": they disagree\""))
w("The price used is the idea's entry price; the pivot is the day's pivot as at the candle in which the entry was "
  "reached; the 100 EMA is the one at the candle before it (`strategies/replay.py`):\n")
w(quote(LIVE, "strategies/replay.py", "if cands:", "out.append((c, check(s, s.market.pair, cand, st, self.pivot_at(c.start), e100)))"))
w("`NO_DIRECTION_RULE` (EMA pullback not listed):\n")
w(quote(LIVE, "strategies/common.py", "NO_DIRECTION_RULE = (", n=1))
w("In period B, extra checks were added on some commits (the hourly read, TREND_STILL_GOING, ANALYSER_GOVERNS_ALL; "
  "table in section 0). They are not part of the direction rule; where they blocked a setup they are listed as "
  "\"other\" below.\n")

S = R["setups"]
oc = Counter(s["outcome"] for s in S)
reached = [s for s in S if s["outcome"] == "reached"]
pre = [s for s in reached if s["commit_at_touch"].startswith("(before")]
w("## 2.2 Which setups the bot logged\n")
w("**The bot logs an EMA pullback idea, allowed or blocked, only when a setup reaches its entry price.** The state "
  "and direction rule are checked only at that moment (`check()` is called on a candidate, and the strategy makes a "
  "candidate only when price reaches the entry, `strategy.py` lines 133-141). A setup (a touch of the 8 EMA) that is "
  "cancelled or expires before price reaches its entry is not logged anywhere and is never checked against the rule. "
  "Blocked ideas are logged on the finished candle (`decisions.jsonl`, `\"kind\": \"idea\"`, `\"allowed\": false`, "
  "with `blocked_by`); the live price path logs only allowed ideas.\n")
w(f"So every setup was worked out from the stored 5-minute and hourly candles, by running the bot's own "
  f"`EmaPullback` class (exact copy of the live code) candle by candle, exactly as the live runner feeds it: the "
  f"5-minute 8 and 21 EMAs over the 2,000 warm-up candles plus the week; the hourly trend reader rebuilt for every "
  f"candle (as stored at start-up before 11 Nov 14:56, see section 0). Each setup's start, entry and end comes "
  f"from the class's own notes. Method checks:\n")
fin = [(n, j) for n, j in R["ideas_lines"] if not j.get("live")]
w(f"* all {len(fin)} finished-candle EMA pullback idea lines in `decisions.jsonl` (allowed and blocked) match a "
  f"worked-out setup that reached its entry in the same candle, same direction, same price;")
w("* all 24 trades match a worked-out setup (same touch candle, direction and entry);")
w("* the step 0 text and the pivot and 100 EMA in each trade's `allowed at entry` step are reproduced exactly on "
  "all 24 trades (23 with the step; trade-level check in `results.json` `pivot_e100_check`).\n")
w(f"**Setups 8 Nov 22:00 - 20 Nov 22:00: {len(S)}.** Reached their entry {oc['reached']}; cancelled by a close "
  f"beyond the 21 EMA {oc['cancelled']}; expired after 20 minutes {oc['expired']}; still waiting at the week's end "
  f"{oc['open at week end']}. Not setups (the bot's notes): {R['nonsetup_counts']['hourly_not_qualified']} touches "
  f"with the hourly trend the right way but not qualified, and {R['nonsetup_counts']['touch_candle_closed_past_21']} "
  f"touch candles that closed beyond the 21 EMA (both counted per direction and candle).\n")
w(f"Of the {oc['reached']} that reached their entry, {len(pre)} did so before the service started on 9 Nov 00:09 "
  f"(8 Nov 22:55, not live). The other {oc['reached'] - len(pre)}: 24 traded; 14 were allowed but not sent "
  f"because another EMA pullback setup the same way had already been sent in that candle (each of their lines has "
  f"`\"already_sent_live\": true`); 47 were blocked.\n")
per = Counter((period(s["touch"]), s["outcome"]) for s in S)          # period by the time of the touch
w("| Period | Setups | Reached entry | Cancelled | Expired | Waiting at week end |")
w("|---|---|---|---|---|---|")
for p in "ABC":
    w(f"| {p} | {sum(v for (pp, o), v in per.items() if pp == p)} | {per[(p, 'reached')]} | {per[(p, 'cancelled')]} | "
      f"{per[(p, 'expired')]} | {per[(p, 'open at week end')]} |")
w("")

B = R["blocked"]
for b in B:
    b["period"] = period(b["time"])
w("## 2.3 Each logged setup: which checks passed and which blocked it\n")
w("The 38 allowed ideas (24 traded, 14 not sent, above) passed all three. The 47 blocked ones are below, each with "
  "its raw line. \"State\" is blocked when `blocked_by` says the state does not allow the EMA pullback or the "
  "trend goes the other way. Pivot and 100 EMA are read from the bot's own `blocked_by` text where the direction "
  "rule blocked (2 lines); where the direction rule does not appear in `blocked_by` it passed, and the pivot and "
  "100 EMA values shown are worked out with the bot's code (the same calculation reproduces all 23 trades' logged "
  "values).\n")
w("| decisions.jsonl line | Entry candle | Dir | Entry | Period / commit | State logged | State | Pivot (value) | 100 EMA (value) | Other checks that blocked |")
w("|---|---|---|---|---|---|---|---|---|---|")
for b in B:
    w(f"| {b['line']} | {hm(b['time'], False)} | {b['direction']} | {b['entry']:.1f} | {b['period']} `{b['commit']}` | {b['state']} | "
      f"{b['state_check']} | {b['pivot_check']} ({b['pivot']:.1f}) | {b['e100_check']} ({b['e100']:.1f}) | "
      f"{'; '.join(b['other_checks']) or '-'} |")
w("")
w("<details><summary>The 47 raw lines, exactly as in data/records/GBPUSD/decisions.jsonl</summary>\n")
w("```")
for b in B:
    w(f"{b['line']}: {b['raw']}")
w("```\n</details>\n")

w("## 2.4 Trades that went ahead, by analyser state at the open\n")
w("Bot's own exits only (owner closes listed apart). \"Trend\" includes the trend's sub-types written in "
  "`trades.jsonl` (`slow grind`, `strong push`).\n")
w("| Period | Emerging trend | Trend |")
w("|---|---|---|")
for p in list("ABC") + ["all"]:
    xs = [x for x in bot if p == "all" or x["period"] == p]
    em = [x for x in xs if x["state_at_open"].startswith("emerging")]
    tr = [x for x in xs if x["state_at_open"].startswith("trend")]
    w(f"| {p} | {tot(em) if em else 'none'} | {tot(tr) if tr else 'none'} |")
w("")
w("Owner closes: " + "; ".join(f"trade {x['n']} ({x['state_at_open']}, {x['pips']:+.1f})" for x in own) + ".\n")
w("Per trade (bot's own exits):\n")
w("| # | State at open | Dir | Opened | Pips | Closed by | Period |")
w("|---|---|---|---|---|---|---|")
for x in bot:
    w(f"| {x['n']} | {x['state_at_open']} | {x['direction']} | {hm(x['opened'], False)} | {x['pips']:+.1f} | {x['kind']} | {x['period']} |")
w("")
w("22 trades split 11 and 11 is a small sample; it shows what happened, not how the states would behave over time.\n")

w("## 2.5 Blocked setups: what blocked them, and a LOOK BACK at what price did next\n")
parts = Counter()
for b in B:
    k = tuple(p for p, ok in (("state", b["state_check"] == "blocked"), ("pivot", b["pivot_check"] == "blocked"),
                              ("100 EMA", b["e100_check"] == "blocked"), ("other", bool(b["other_checks"]))) if ok)
    parts[k] += 1
w("| What blocked it | Setups |")
w("|---|---|")
for k, v in parts.most_common():
    w(f"| {' + '.join(k)}{' (alone)' if len(k) == 1 else ''} | {v} |")
w("")
sb = sum(v for k, v in parts.items() if "state" in k)
pb = sum(v for k, v in parts.items() if "pivot" in k)
eb = sum(v for k, v in parts.items() if "100 EMA" in k)
ob = sum(v for k, v in parts.items() if "other" in k)
w(f"Each part, counted wherever it appears: state {sb} ({parts[('state',)]} alone); pivot {pb} "
  f"({parts[('pivot',)]} alone); 100 EMA {eb} ({parts[('100 EMA',)]} alone); other checks {ob} "
  f"({parts[('other',)]} alone).\n")
cand = Counter((b["time"], b["direction"]) for b in B)
w(f"Several blocked setups often reached their entry in the same candle: the 47 lines are {len(cand)} different "
  "candles and directions.\n")
w("> **LOOK BACK - not live results.** Nothing below was traded. Every blocked setup reached its entry (the bot logs "
  "a blocked setup only at that moment), so \"reached the entry within the 20-minute expiry\" is yes for all 47. "
  "From the entry: fill as the bot's engine sets it on a finished candle (a sell at the entry price; a buy at the "
  "entry plus that candle's opening spread), then the stored 5-minute candles on the price a trade would close on "
  "(a buy on the sell price, a sell on the buy price), looking for 12 pips against (the stop) or 30 pips in favour "
  "(the brief's take profit) first, up to the EMA pullback's Friday 20:30 close. Where both fall in one candle the "
  "order is unknown and it says so; a hit in the entry candle itself is marked, because the part of that candle "
  "after the entry is unknown. Setups at or after Friday 20:30 UK could not have opened (`may_open`).\n")
w("| decisions.jsonl line | Entry candle | Dir | What blocked it | LOOK BACK fill | LOOK BACK result | LOOK BACK when |")
w("|---|---|---|---|---|---|---|")
lbc = Counter()
for b in B:
    k = " + ".join(p for p, ok in (("state", b["state_check"] == "blocked"), ("pivot", b["pivot_check"] == "blocked"),
                                   ("100 EMA", b["e100_check"] == "blocked"), ("other", bool(b["other_checks"]))) if ok)
    t = T(b["time"])
    if t.weekday() == 4 and t.hour * 60 + t.minute >= 20 * 60 + 30:
        res, when = "could not have opened: Friday after 20:30 UK", ""
        lbc["could not have opened"] += 1
    else:
        res, when = b["lookback"]["result"], hm(b["lookback"]["at"], False) if b["lookback"].get("at") else ""
        lbc[res.split(" - ")[0].split(" by ")[0]] += 1
    w(f"| {b['line']} | {hm(b['time'], False)} | {b['direction']} | {k} | {b['lookback']['fill']:.1f} | {res} | {when} |")
w("")
w("LOOK BACK totals (setups, not trades; same-candle duplicates each counted):\n")
for k, v in lbc.most_common():
    w(f"* {k}: {v}")
w("")
w("LOOK BACK by what blocked it:\n")
w("| What blocked it | Take profit first | Stop first | Both in one candle | Neither | Could not have opened |")
w("|---|---|---|---|---|---|")
g = defaultdict(Counter)
for b in B:
    k = " + ".join(p for p, ok in (("state", b["state_check"] == "blocked"), ("pivot", b["pivot_check"] == "blocked"),
                                   ("100 EMA", b["e100_check"] == "blocked"), ("other", bool(b["other_checks"]))) if ok)
    t = T(b["time"])
    r = b["lookback"]["result"]
    if t.weekday() == 4 and t.hour * 60 + t.minute >= 20 * 60 + 30:
        g[k]["no"] += 1
    elif r.startswith("take profit"):
        g[k]["tp"] += 1
    elif r.startswith("stop and"):
        g[k]["both"] += 1
    elif r.startswith("stop"):
        g[k]["stop"] += 1
    else:
        g[k]["neither"] += 1
for k, c in sorted(g.items(), key=lambda kv: -sum(kv[1].values())):
    w(f"| {k} | {c['tp']} | {c['stop']} | {c['both']} | {c['neither']} | {c['no']} |")
w("")

w("## 2.6 When the blocked setups came\n")
w("By UK hour of the entry candle (all 47; the state that blocked is the logged state):\n")
hh = Counter(T(b["time"]).hour for b in B)
w("| UK hour | Blocked setups | Of which state consolidation / ranging / emerging or trend the other way / passed state | Dates |")
w("|---|---|---|---|")
for h in sorted(hh):
    bs = [b for b in B if T(b["time"]).hour == h]
    c1 = sum(1 for b in bs if b["state_check"] == "blocked" and b["state"] == "consolidation")
    c2 = sum(1 for b in bs if b["state_check"] == "blocked" and b["state"] == "ranging")
    c3 = sum(1 for b in bs if b["state_check"] == "blocked" and b["state"] not in ("consolidation", "ranging"))
    c4 = sum(1 for b in bs if b["state_check"] == "passed")
    w(f"| {h:02d} | {len(bs)} | {c1} / {c2} / {c3} / {c4} | {', '.join(sorted({T(b['time']).strftime('%d %b') for b in bs}))} |")
w("")
buckets = Counter("00:00-06:59" if T(b["time"]).hour < 7 else "07:00-15:59" if T(b["time"]).hour < 16 else "16:00-23:59"
                  for b in B)
w("In three blocks: " + "; ".join(f"{k}: {buckets[k]}" for k in ("00:00-06:59", "07:00-15:59", "16:00-23:59")) + ".\n")
w("By day:\n")
dd = Counter(T(b["time"]).strftime("%a %d %b") for b in B)
w("| Day | Blocked setups | Traded setups that day |")
w("|---|---|---|")
for d in sorted(dd, key=lambda s: datetime.strptime(s + " 2026", "%a %d %b %Y")):
    w(f"| {d} | {dd[d]} | {sum(1 for x in trades if hm(x['opened'], False).startswith(d))} |")
w("")
w(f"The pivot blocked 2 setups (both also blocked by the state), both buys in the night: decisions.jsonl lines 617 "
  f"(Tue 10 Nov 23:05) and 658 (Wed 11 Nov 03:05). There is no case in the record of the pivot blocking a setup "
  f"early in a trend day, so the record cannot show whether that happens.\n")

# ------------------------------------------------------------------ Part 3
w("# Part 3. Wick past the 21 EMA vs close past it\n")
w("## 3.1 The live cancel code\n")
w(quote(LIVE, "strategies/ema_pullback/strategy.py", "for st in list(self.setups):", "f\"{self.e.slow_ema_periods} EMA {q(slow)}: cancelled\"))", before=0))
w("The touch candle itself is also refused if it closes beyond the 21 EMA:\n")
w(quote(LIVE, "strategies/ema_pullback/strategy.py", "if (self._c(c) < slow) if buy else (self._c(c) > slow):", n=5))
w("The 21 EMA compared is the one at that candle's own close (`slow.get(c.start)` in `strategies/replay.py`), on the "
  "sell (chart) price.\n")
w("## 3.2 Every setup: a wick beyond the 21 EMA without a close beyond it\n")
w("For each setup, every 5-minute candle from the touch candle up to the candle before the entry candle (or up to "
  "the candle before the cancel or expiry): a buy's low below that candle's 21 EMA while its close stayed at or "
  "above it (a sell: high above, close at or below). Distance = how far the wick went beyond the 21 EMA, in pips, "
  "sell price. The entry candle is listed apart: within it the order of the wick and the entry is unknown. The full "
  "list of all setups, with every wick, is `setups.csv`.\n")
wc = Counter((s["outcome"], s["max_wick"] > 0) for s in S)
w("| Outcome | Setups | With a wick beyond the 21 EMA | Without |")
w("|---|---|---|---|")
for o in ("reached", "cancelled", "expired", "open at week end"):
    w(f"| {o} | {wc[(o, True)] + wc[(o, False)]} | {wc[(o, True)]} | {wc[(o, False)]} |")
w("")
w("## 3.3 Trades: with a wick vs without\n")
wb = [x for x in bot if x["max_wick"] > 0]
nb = [x for x in bot if x["max_wick"] == 0]
w(f"Bot's own exits: with a wick before the entry candle {tot(wb)}; without {tot(nb)}. Owner closes: "
  + "; ".join(f"trade {x['n']} wick {x['max_wick']:.1f} ({x['pips']:+.1f})" for x in own) + ".\n")
for p in "ABC":
    a = [x for x in wb if x["period"] == p]
    c = [x for x in nb if x["period"] == p]
    w(f"* Period {p}: with a wick {tot(a) if a else 'none'}; without {tot(c) if c else 'none'}.")
w("")
w(f"With {len(bot)} trades and {sum(1 for x in bot if x['pips'] > 0)} winners this is too small a sample to say "
  "whether a wick past the 21 EMA matters.\n")
w("## 3.4 How far past the 21 EMA the wicks went (trades)\n")
w("Every trade, sorted by its largest wick beyond the 21 EMA before the entry candle, largest first. Each wick "
  "candle is listed. No cut-off is applied.\n")
w("| # | Dir | Opened | Largest wick (pips) | Every wick candle: time, 21 EMA, low/high, close, pips beyond | Entry candle wick (order unknown) | Pips | Closed by | Period |")
w("|---|---|---|---|---|---|---|---|---|")
for x in sorted(trades, key=lambda q: (-q["max_wick"], q["opened"])):
    wl = "; ".join(f"{T(q['candle']):%H:%M} 21 EMA {q['ema21']:.1f}, {'low ' + format(q['low'], '.1f') if 'low' in q else 'high ' + format(q['high'], '.1f')}, close {q['close']:.1f}: {q['pips']:.1f}" for q in x["wicks"]) or "-"
    ec = f"{T(x['entry_candle_wick']['candle']):%H:%M} {x['entry_candle_wick']['pips']:.1f}" if x["entry_candle_wick"] else "-"
    w(f"| {x['n']} | {x['direction']} | {hm(x['opened'], False)} | {x['max_wick']:.1f} | {wl} | {ec} | {x['pips']:+.1f} | {x['kind']} | {x['period']} |")
w("")
w("For comparison, the same measure on the setups that reached their entry but were blocked (LOOK BACK result "
  "beside it, not a live result):\n")
w("| decisions.jsonl line | Dir | Entry candle | Largest wick (pips) | LOOK BACK result |")
w("|---|---|---|---|---|")
for b in sorted(B, key=lambda q: (-(q["max_wick"] or 0), q["time"])):
    t = T(b["time"])
    res = ("could not have opened: Friday after 20:30 UK" if t.weekday() == 4 and t.hour * 60 + t.minute >= 20 * 60 + 30
           else "LOOK BACK: " + b["lookback"]["result"])
    w(f"| {b['line']} | {b['direction']} | {hm(b['time'], False)} | {b['max_wick']:.1f} | {res} |")
w("")

(HERE / "DETAIL.md").write_text("\n".join(out) + "\n")

# CSVs
with open(HERE / "trades.csv", "w", newline="") as fh:
    cols = ["n", "ref", "deal", "direction", "period", "commit", "state_at_open", "touch", "setup_entry", "wanted_entry",
            "tick_time", "tick_bid", "tick_offer", "sending_time", "opened", "fill", "stop", "limit", "closed",
            "close_px", "pips", "kind", "ig_channel", "slopes_against", "slopes_against_live", "news_open_window",
            "news_while_open", "opened_outside_0600_2030", "held_past_2030", "max_wick", "src"]
    wr = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    wr.writeheader()
    for x in trades:
        wr.writerow({k: (json.dumps(x[k]) if isinstance(x.get(k), (list, dict)) else x.get(k)) for k in cols})
with open(HERE / "setups.csv", "w", newline="") as fh:
    cols = ["touch", "direction", "entry", "outcome", "end_candle", "end_note", "commit_at_touch", "slope_code_at_touch",
            "slopes_3h", "slopes_against_live", "max_wick", "wicks", "entry_candle_wick", "logged_lines", "trade_refs"]
    wr = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    wr.writeheader()
    for s in S:
        wr.writerow({k: (json.dumps(s.get(k)) if isinstance(s.get(k), (list, dict)) else s.get(k)) for k in cols})
with open(HERE / "blocked.csv", "w", newline="") as fh:
    cols = ["line", "time", "direction", "entry", "period", "commit", "state", "state_check", "pivot_check", "pivot",
            "e100_check", "e100", "other_checks", "max_wick", "lookback"]
    wr = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    wr.writeheader()
    for b in B:
        wr.writerow({k: (json.dumps(b.get(k)) if isinstance(b.get(k), (list, dict)) else b.get(k)) for k in cols})
(HERE / "REPORT.md").write_text((HERE / "_head.md").read_text() + "\n" + (HERE / "DETAIL.md").read_text()
                                + (HERE / "_tail.md").read_text())
print("written")
