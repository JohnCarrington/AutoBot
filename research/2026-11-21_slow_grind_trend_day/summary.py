"""Phase 3: the report's figures from days.csv (usable days only). Prints Markdown tables."""
from __future__ import annotations

import csv
import statistics as st
import sys
from collections import Counter

rows = [r for r in csv.DictReader(open(sys.argv[1])) if r["usable"] == "True"]
allrows = list(csv.DictReader(open(sys.argv[1])))
f = lambda r, k: float(r[k])  # noqa: E731
T8, T21 = 0.25, 0.50   # the top 10% of all usable days (better direction), strict and loose readings


def med(xs):
    return f"{st.median(xs):+.1f}" if xs else "-"


def mean(xs):
    return f"{st.mean(xs):+.1f}" if xs else "-"


def pct(a, b):
    return f"{a} of {b} ({100 * a / b:.0f}%)" if b else "0 of 0"


def signal_dir(r):
    """Figures measured in the signal's direction (up days as they are, down days mirrored)."""
    up = r["signal"] == "up"
    net = f(r, "net_up_pips") * (1 if up else -1)
    w, a = (f(r, "max_up_pips"), f(r, "max_down_pips")) if up else (f(r, "max_down_pips"), f(r, "max_up_pips"))
    d, o = ("up", "down") if up else ("down", "up")
    return net, w, a, f(r, f"hug_share_{d}"), int(r[f"longest_hug_min_{d}"]), int(r[f"band_touches_{d}"]), \
        f(r, f"hug_share_{o}"), int(r[f"longest_hug_min_{o}"]), f(r, f"hug21_share_{d}"), f(r, f"hug21_share_{o}")


def best_dir(r):
    """No signal direction: the day's own better direction for hugging, and the size of the move."""
    hu, hd = f(r, "hug_share_up"), f(r, "hug_share_down")
    d = "up" if hu >= hd else "down"
    return abs(f(r, "net_up_pips")), max(f(r, "max_up_pips"), f(r, "max_down_pips")), \
        min(f(r, "max_up_pips"), f(r, "max_down_pips")), max(hu, hd), int(r[f"longest_hug_min_{d}"]), (hu + hd) / 2, \
        max(f(r, "hug21_share_up"), f(r, "hug21_share_down")), (hu >= T8) + (hd >= T8), \
        (f(r, "hug21_share_up") >= T21) + (f(r, "hug21_share_down") >= T21)


def block_signal(rs, title):
    n = len(rs)
    if not n:
        return [f"**{title}: no days.**", ""]
    v = [signal_dir(r) for r in rs]
    net = [x[0] for x in v]
    out = [f"**{title}** ({n} days)", "",
           "| Figure | Value |", "|---|---|",
           f"| Net pips 09:00-20:30 in the signal's direction: median / mean | {med(net)} / {mean(net)} |",
           f"| Days that ended 09:00-20:30 in the signal's direction | {pct(sum(x > 0 for x in net), n)} |",
           f"| ... by 20 pips or more | {pct(sum(x >= 20 for x in net), n)} |",
           f"| Days that ended 20 pips or more against it | {pct(sum(x <= -20 for x in net), n)} |",
           f"| Biggest move in the signal's direction: median / mean | {med([x[1] for x in v])} / {mean([x[1] for x in v])} |",
           f"| Biggest move against it: median / mean | {med([x[2] for x in v])} / {mean([x[2] for x in v])} |",
           f"| Days whose biggest move with it was larger than against it | {pct(sum(x[1] > x[2] for x in v), n)} |",
           f"| Share of 09:00-20:30 spent hugging the band in the signal's direction: median / mean | "
           f"{100 * st.median([x[3] for x in v]):.0f}% / {100 * st.mean([x[3] for x in v]):.0f}% |",
           f"| Strict top-10% hugging day (25%+ of the session) in the signal's direction | {pct(sum(x[3] >= T8 for x in v), n)} |",
           f"| ... the same the OTHER way (a one-direction baseline) | {pct(sum(x[6] >= T8 for x in v), n)} |",
           f"| Band touches in the signal's direction: median | {st.median([x[5] for x in v]):.0f} |",
           f"| Loose reading (pullback reaches the 21 EMA): share hugging in the signal's direction, median | {100 * st.median([x[8] for x in v]):.0f}% |",
           f"| Loose top-10% hugging day (50%+ of the session) in the signal's direction | {pct(sum(x[8] >= T21 for x in v), n)} |",
           f"| ... the same the OTHER way | {pct(sum(x[9] >= T21 for x in v), n)} |",
           ""]
    return out


def block_plain(rs, title):
    n = len(rs)
    if not n:
        return [f"**{title}: no days.**", ""]
    v = [best_dir(r) for r in rs]
    return [f"**{title}** ({n} days; no single direction, so the size of the move and the day's better hugging "
            f"direction)", "",
            "| Figure | Value |", "|---|---|",
            f"| Net pips 09:00-20:30, either way (size only): median / mean | {med([x[0] for x in v])} / {mean([x[0] for x in v])} |",
            f"| Days that moved 20 pips or more net, either way | {pct(sum(x[0] >= 20 for x in v), n)} |",
            f"| Larger of the two biggest moves: median / mean | {med([x[1] for x in v])} / {mean([x[1] for x in v])} |",
            f"| Smaller of the two biggest moves: median / mean | {med([x[2] for x in v])} / {mean([x[2] for x in v])} |",
            f"| Share spent hugging the band, in the day's better direction: median / mean | "
            f"{100 * st.median([x[3] for x in v]):.0f}% / {100 * st.mean([x[3] for x in v]):.0f}% |",
            f"| Strict top-10% hugging day, either direction (any one day can count once) | {pct(sum(x[7] > 0 for x in v), n)} |",
            f"| ... counted per direction (days x 2 directions; comparable to one direction on signal days) | "
            f"{sum(x[7] for x in v)} of {2 * n} ({100 * sum(x[7] for x in v) / (2 * n):.0f}%) |",
            f"| Loose reading (21 EMA): better-direction share, median | {100 * st.median([x[6] for x in v]):.0f}% |",
            f"| Loose top-10% hugging day, either direction | {pct(sum(x[8] > 0 for x in v), n)} |",
            f"| ... counted per direction | {sum(x[8] for x in v)} of {2 * n} ({100 * sum(x[8] for x in v) / (2 * n):.0f}%) |",
            ""]


def compare_line(rs):
    """Like-for-like row: size of the move and better-direction hug, any group."""
    v = [best_dir(r) for r in rs]
    n = len(rs)
    if not n:
        return "| - | 0 | - | - | - | - | - |"
    return (f"| {n} | {med([x[0] for x in v])} | {pct(sum(x[0] >= 20 for x in v), n)} | {med([x[1] for x in v])} | "
            f"{100 * st.median([x[3] for x in v]):.0f}% | {pct(sum(x[7] > 0 for x in v), n)} | "
            f"{pct(sum(x[8] > 0 for x in v), n)} |")


g = {k: [r for r in rows if r["signal"] == k] for k in ("up", "down", "both", "none")}
sig = g["up"] + g["down"]
out = []
out.append(f"Weekdays in range: {len(allrows)}; usable: {len(rows)}; left out for missing candles: {len(allrows) - len(rows)}.")
out.append("")
out.append("| Signal | Days | Share |")
out.append("|---|---|---|")
for k, name in (("up", "Up (only buys in profit)"), ("down", "Down (only sells in profit)"),
                ("both", "Both ways in profit: not a trend day"), ("none", "Did not turn on")):
    out.append(f"| {name} | {len(g[k])} | {100 * len(g[k]) / len(rows):.0f}% |")
out.append("")
times = Counter()
for r in sig:
    h, m = map(int, r["signal_time_uk"].split(":"))
    b = "06:00 (already in profit at the window's first candle)" if (h, m) == (6, 0) else \
        "06:05-06:55" if h == 6 else "07:00-07:55" if h == 7 else "08:00-08:55"
    times[b] += 1
out.append("| Signal time (UK) | Days |")
out.append("|---|---|")
for b in ("06:00 (already in profit at the window's first candle)", "06:05-06:55", "07:00-07:55", "08:00-08:55"):
    out.append(f"| {b} | {times[b]} |")
out.append("")
out.append("### Rest of the day, signal days")
out.append("")
out += block_signal(sig, "All signal days (up and down together)")
out += block_signal(g["up"], "Up signal days")
out += block_signal(g["down"], "Down signal days")
out.append("### Comparison days")
out.append("")
out += block_plain(g["none"], "Days the signal did not turn on")
out += block_plain(g["both"], "Days with slow grind buys AND sells in profit (not a trend day)")
out.append("### Like for like (size of move and better-direction hug, ignoring the signal's direction)")
out.append("")
out.append("| Group | Days | Net move size: median | Moved 20+ net either way | Larger biggest move: median | "
           "Better-direction hug share: median | Strict top-10% hugging day, either way | Loose top-10% hugging day, either way |")
out.append("|---|---|---|---|---|---|---|---|")
for name, rs in (("Signal on (up/down)", sig), ("Both ways (not trend)", g["both"]), ("Signal not on", g["none"])):
    out.append(f"| {name} " + compare_line(rs))
out.append("")
out.append("### Split by big news later that day (09:00-20:30 UK, the bot's news table)")
out.append("")
for news in (True, False):
    sel = lambda rs: [r for r in rs if bool(r["big_news_0900_2030"]) == news]  # noqa: E731
    label = "WITH big news 09:00-20:30" if news else "WITHOUT big news 09:00-20:30"
    out.append(f"#### Days {label}")
    out.append("")
    out += block_signal(sel(sig), f"Signal days, {label.lower()}")
    out += block_plain(sel(g["none"]), f"Signal not on, {label.lower()}")
    out += block_plain(sel(g["both"]), f"Both ways, {label.lower()}")
    out.append("| Group | Days | Net move size: median | Moved 20+ net either way | Larger biggest move: median | "
               "Better-direction hug share: median | Strict top-10% hugging day, either way | Loose top-10% hugging day, either way |")
    out.append("|---|---|---|---|---|---|---|---|")
    for name, rs in (("Signal on (up/down)", sel(sig)), ("Both ways (not trend)", sel(g["both"])), ("Signal not on", sel(g["none"]))):
        out.append(f"| {name} " + compare_line(rs))
    out.append("")
out.append("### By year (signal days, in the signal's direction)")
out.append("")
out.append("| Year | Usable days | Signal on | Both | Not on | Signal days ending in its direction | Median net, signal days | "
           "Signal days: strict top-10% hug its way | Not-on days: strict top-10% hug, per direction |")
out.append("|---|---|---|---|---|---|---|---|---|")
for y in ("2024", "2025", "2026"):
    ry = [r for r in rows if r["day"].startswith(y)]
    sy = [r for r in sig if r["day"].startswith(y)]
    ny = [r for r in g["none"] if r["day"].startswith(y)]
    by = [r for r in g["both"] if r["day"].startswith(y)]
    v = [signal_dir(r) for r in sy]
    out.append(f"| {y} | {len(ry)} | {len(sy)} | {len(by)} | {len(ny)} | {pct(sum(x[0] > 0 for x in v), len(sy))} | "
               f"{med([x[0] for x in v])} | {pct(sum(x[3] >= T8 for x in v), len(sy))} | "
               f"{pct(sum(best_dir(r)[7] for r in ny), 2 * len(ny))} |")
print("\n".join(out))
