"""Lists the check replays' entry-filter refusals next to what the live bot actually did (read-only). Live trades:
research/2026-11-21_week_results/week_results.csv (16-20 Nov, IG prices) and research/2026-11-20_losing_trades/
trades.csv (9-11 Nov, IG prices), from the branches research/week-results-20261121 and
research/losing-trades-20261120-cc. A refused idea is matched to a live trade of the same strategy and direction
opened within 10 minutes of it. Replay results are not totalled: the replays only check the code."""
import csv, json, subprocess, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
D = Path(__file__).parent
UTC = timezone.utc


def git_show(ref, path):
    return subprocess.run(["git", "-C", "/opt/autobot", "show", f"{ref}:{path}"], capture_output=True, text=True,
                          check=True).stdout


def live_trades():
    out = []
    for r in csv.DictReader(git_show("origin/research/week-results-20261121",
                                     "research/2026-11-21_week_results/week_results.csv").splitlines()):
        t = datetime.strptime(f"2026 {r['date'][4:]} {r['open_time_uk']}", "%Y %d %b %H:%M:%S").replace(tzinfo=UTC)
        out.append((t, r["strategy"], r["direction"], r["pips"], r["closed_by"], r["analyser_state_at_open"]))
    for r in csv.DictReader(git_show("origin/research/losing-trades-20261120-cc",
                                     "research/2026-11-20_losing_trades/trades.csv").splitlines()):
        if "2026-11-09" <= r["opened_utc"] < "2026-11-12":
            out.append((datetime.fromisoformat(r["opened_utc"].replace("Z", "+00:00")), r["strategy"], r["direction"],
                        r["ig_pips"], r["closed_by"], r["market_state"]))
    return out


def main(on_file, off_file, out_md):
    on, off = json.load(open(D / on_file)), json.load(open(D / off_file))
    live = live_trades()
    rows = ["| Idea (UK) | Strategy | Dir | Entry | Rule | Why | Live |", "|---|---|---|---:|---|---|---|"]
    for r in on["refused"]:
        t = datetime.fromisoformat(r["idea_time"].replace("Z", "+00:00"))
        m = [x for x in live if x[1] == r["strategy"] and x[2] == r["direction"] and abs(x[0] - t) <= timedelta(minutes=10)]
        lv = "; ".join(f"opened {x[0]:%H:%M}, {float(x[3]):+.1f} pips ({x[4]})" for x in m) if m else "not traded live"
        why = r["why"].replace("|", "/")
        if r["rule"] == "hourly context":
            d = r["details"]
            why = (f"{d['context'].upper()} context; {d['pips_from_line']} pips from {d['line']} {d['line_price']} "
                   f"(swings {' then '.join(p for _, p in d['swings'])}; last hourly close {d['last_hourly_close']}, "
                   f"50 EMA {d['hourly_ema50']}, 6 before {d['hourly_ema50_before']})")
        else:
            d = r["details"]
            why = f"entry {d['entry_price']}, 8 EMA {d['ema8_5m']} ({d['ema8_candle'][11:16]}), {d['pips_beyond_ema8']} pips beyond"
        rows.append(f"| {t:%a %d %b %H:%M} | {r['strategy']} | {r['direction']} | {r['entry_price']} | {r['rule']} | {why} | {lv} |")
    key = lambda x: (x["opened_uk"], x["strategy"], x["direction"])  # noqa: E731
    gone = sorted(set(map(key, off["trades"])) - set(map(key, on["trades"])))
    new = sorted(set(map(key, on["trades"])) - set(map(key, off["trades"])))
    md = [f"Replay trades: {len(off['trades'])} with both switches off, {len(on['trades'])} with both on; "
          f"{len(on['refused'])} refusals (one setup can be refused on more than one candle).", "",
          "#### Every refusal", ""] + rows + ["",
          "#### Trades in the switches-off replay missing from the switches-on replay", ""] + \
         [f"- {a} {b} {c}" for a, b, c in gone] + ["", "#### Trades only in the switches-on replay (a setup that "
          "opened later, after an earlier try was refused, or a slot freed by a refused trade)", ""] + \
         [f"- {a} {b} {c}" for a, b, c in new]
    Path(D / out_md).write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main(*sys.argv[1:4])
