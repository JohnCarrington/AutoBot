"""Johnny's week review (16-20 Nov): one line per trade, from week_paths.csv (the stored candles) and trades.csv."""
import csv, collections
from pathlib import Path
D = Path(__file__).parent
rows = list(csv.DictReader(open(D / "week_paths.csv")))
NOTE = {  # trade-specific facts checked by hand in the records
 "2026-11-16T12:37": "held all afternoon and closed at 20:30 at +8.3 (best +15.6, never reached the 20-pip target)",
 "2026-11-16T14:26": "the EMA pullback is held overnight; it was +22.6 in the night and came all the way back to the stop next day: management (no lock or trail for the EMA pullback)",
 "2026-11-17T10:05|Bollinger bounce": "+15.6; the trail moved its stop to 13193.2 (13:40), but IG refused the next move to 13181.6 about 30 times (13:50–14:06, ATTACHED_ORDER_LEVEL_ERROR) and it was stopped at 13193.2 for −3.3: a mechanical fault of that version's trail (changed by the trail fix cc70dc5, 17 Nov 20:36)",
 "2026-11-17T10:05|level reversal": "same move as the bounce: +15.2, then back to a 20.8-pip stop, wider than its 20-pip target; no break-even in this version: management and stop size",
 "2026-11-17T16:22": "its 22.5-pip stop was wider than its 20-pip target; best +9.1, closed at 20:30 at −9.2: stop size and the daily close",
 "2026-11-17T16:46": "best +7.9, then down; closed at 20:30 at −10.4 before the stop: entry late in a strong push",
 "2026-11-18T15:44": "went +16.1 in 35 minutes, toward its 50-pip target, then all the way back to the 12-pip stop over 7 hours; the breakout has no trail: management",
 "2026-11-20T06:07": "+10.5 an hour in, then fell back for 5 hours to the 17.3-pip stop; no break-even in this version: management and stop size",
 "2026-11-20T13:10": "bought 26.6 pips above the level after one 15-pip candle, with a 34.3-pip stop for a 20-pip target; never more than +0.9; Johnny closed it at −26.1: entry and stop size",
 "2026-11-20T13:25": "bought the break of a pause 1.7 pips under the day's high at the same candle the hourly bounce read as a rejection; never in profit, stopped in 16 minutes: entry",
 "2026-11-20T13:32": "+11.0 (the 5m bounce has no trail in this build), then closed at 0.0 by its level-close rule at the pivot: management (the level close)",
 "2026-11-20T07:25": "+2.0 at best, then closed at −1.7 by the 5m bounce's level-close rule (London low and pivot): the rule cut a small loss",
 "2026-11-18T19:50": "never in profit; stopped in 28 minutes (this trade came from the forming-candle check, 18 Nov review)",
}
def note(r):
    k = r["opened_utc"][:16]
    return NOTE.get(f"{k}|{r['strategy']}") or NOTE.get(k)
lines = ["| Opened (UTC) | Version | Strategy | Dir | Stop / target | IG pips | Who closed | What price did after the entry, and what was at fault |",
         "|---|---|---|---|---|---|---|---|"]
for r in rows:
    p = r["ig_pips"]; b = float(r["best_pips"] or 0); f = (r["first15_best"], r["first15_worst"]); m = r["minutes_open"]
    who = {"stopped by IG": "IG stop", "take profit hit at IG": "IG limit", "close": "bot", "forced close": "bot (20:30)",
           "closed by owner": "Johnny"}.get(r["how_closed"], r["how_closed"] or "open")
    n = note(r)
    if r["closed_utc"] == "OPEN":
        s = "still open at 19:00 (stop 13103.3 at IG)."
    elif n:
        s = n[0].upper() + n[1:] + "."
    elif r["closed_by"] == "owner":
        s = f"First 15 min +{f[0]}/−{f[1]}; best {b:+.1f}; Johnny closed it after {m} min at {float(p):+.1f} (not the bot's result)."
    elif float(p) > 0:
        how = "the trail took it" if (r["how_closed"] == "stopped by IG" and float(p) < float(r["ig_stop_distance"])) else \
              "the 20:30 close took it" if r["how_closed"] == "forced close" else "the bot's level close took it" if r["how_closed"] == "close" else "stopped in profit"
        s = f"Worked: first 15 min +{f[0]}/−{f[1]}, best +{b}; {how} at {float(p):+.1f}."
    elif b < 3:
        s = f"Went against it at once (first 15 min +{f[0]}/−{f[1]}), never 3 pips its way (best {b:+.1f}), full stop after {m} min: the entry/signal was wrong; stop and management did their job."
    elif b < 8:
        s = f"Only {b:+.1f} its way (first 15 min +{f[0]}/−{f[1]}), then back to the full stop after {m} min: a weak signal; the move was too small for its {r['ig_stop_distance']}-pip stop."
    else:
        s = f"Was {b:+.1f} in profit, then all the way back to the full stop after {m} min: management (nothing locked the gain)."
    lines.append(f"| {r['opened_utc'][5:16].replace('T',' ')} | {r['period'][0]} | {r['strategy']} | {r['direction']} | {r['ig_stop_distance']} / {r['tp_pips']} | "
                 f"{p or '–'} | {who} | {s} |")
print("\n".join(lines))
