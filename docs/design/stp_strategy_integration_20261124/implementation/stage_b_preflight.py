"""Stage B pre-flight and post-check (read only; owner, 25 November 2026). Prints each check and OK / CHECK; changes
nothing, sends nothing, never contacts IG itself (IG connectivity is read from the running price service's own log).
    cd /opt/autobot && .venv/bin/python -I docs/design/stp_strategy_integration_20261124/implementation/stage_b_preflight.py [expect-on|expect-off]
expect-off (default): before activation (STP_AUTHORISES_ENTRIES must be off). expect-on: after the restart."""
import json, os, subprocess, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
ROOT = Path("/opt/autobot"); sys.path.insert(0, str(ROOT))
from config.settings_loader import load_or_exit                       # noqa: E402
want_on = len(sys.argv) > 1 and sys.argv[1] == "expect-on"
UTC = timezone.utc; now = datetime.now(UTC); bad = []
def say(ok, what):
    print(("OK    " if ok else "CHECK ") + what)
    if not ok: bad.append(what)
def sh(*a):
    return subprocess.run(a, capture_output=True, text=True, cwd=ROOT).stdout.strip()
def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))
# code
head = sh("git", "rev-parse", "--short", "HEAD"); tracked = [l for l in sh("git", "status", "--short").splitlines() if not l.startswith("??")]
say(not tracked, f"code: HEAD {head}, no uncommitted changes to tracked files" + (f" ({len(tracked)} changed)" if tracked else ""))
# services: running and started after the code and .env they should be using
for svc in ("autobot-prices", "autobot-dashboard"):
    st = sh("systemctl", "show", svc, "-p", "ActiveState", "--value"); since = sh("systemctl", "show", svc, "-p", "ActiveEnterTimestamp", "--value")
    started = datetime.strptime(since, "%a %Y-%m-%d %H:%M:%S %Z").replace(tzinfo=UTC) if since else None
    env_t = datetime.fromtimestamp((ROOT / ".env").stat().st_mtime, UTC)
    code_t = datetime.fromtimestamp(int(sh("git", "log", "-1", "--format=%ct")), UTC)
    fresh = started is not None and started >= env_t and started >= code_t
    say(st == "active" and (fresh or not want_on), f"{svc}: {st} since {since}" + ("" if fresh else
        f" (before the last .env change {env_t:%H:%M:%S} or commit {code_t:%H:%M:%S} UTC: a restart loads them)"))
# effective switches, as the bot reads them at start-up
w = load_or_exit().switches
say(w.stp_opportunities and w.stp_bidirectional, f"STP_OPPORTUNITIES={w.stp_opportunities} STP_BIDIRECTIONAL={w.stp_bidirectional}")
say(w.stp_authorises_entries == want_on, f"STP_AUTHORISES_ENTRIES={w.stp_authorises_entries} (expected {'on' if want_on else 'off'})")
say(w.one_signal_one_trade, f"ONE_SIGNAL_ONE_TRADE={w.one_signal_one_trade} (required for STP authorisation, OD-32)")
say(w.trading, f"TRADING={w.trading} (IG DEMO orders)")
env = dict(l.split("=", 1) for l in (ROOT / ".env").read_text().splitlines() if "=" in l and l.split("=", 1)[0] in ("IG_ACC_TYPE",))
s = load_or_exit().for_pair("GBPUSD")
say(env.get("IG_ACC_TYPE", "").upper() == "DEMO" and "demo-api" in s.ig.demo_base_url, f"IG account type {env.get('IG_ACC_TYPE')}, address {s.ig.demo_base_url}")
# IG connectivity, from the running price service's own log since its start
log = sh("journalctl", "-u", "autobot-prices", "--since", "-6 hours", "--no-pager", "-q")
last_start = log.rfind("price service starting"); part = log[last_start:] if last_start >= 0 else log
say("Logged in to IG" in part and "Price stream connected" in part, "IG DEMO: logged in and price stream connected since the last start")
errors = [l for l in part.splitlines() if any(k in l.lower() for k in ("error", "traceback", "critical"))]
say(not errors, f"price service log since its start: {len(errors)} error lines")
# open positions and pending submissions (the bot's own records, reconciled with IG at start-up and every candle)
opn = json.loads((ROOT / "data/trade_manager/GBPUSD/open_trades.json").read_text())
say(True, f"open trades held by the bot: {len(opn)} {list(opn)}")
ev = [json.loads(l) for l in (ROOT / "data/orders/GBPUSD/orders.jsonl").read_text().splitlines() if l.strip()]
done = {"opened", "safety refused", "refused", "rejected", "not opened", "send failed"}
pending = [e for e in ev if e.get("event") == "sending" and e["time_utc"] >= (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
           and not any(x.get("reference") == e.get("reference") and x.get("event") in done for x in ev)]
say(not pending, f"order submissions sent without an outcome (last 2 days): {len(pending)} {[p.get('reference') for p in pending]}")
recent = [e for e in ev if e["time_utc"] >= (now - timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")]
say(not [e for e in recent if e.get("event") in ("gone at IG", "found at IG", "not checked at IG")],
    "no unexpected IG position events (gone / found / not checked) in the last 6 hours")
# STP
cur = json.loads((ROOT / "data/planner/GBPUSD/current.json").read_text())
age = (now - ts(cur["written_utc"])).total_seconds() / 60
say(cur.get("current") is True and age <= 10, f"STP file current={cur.get('current')}, written {age:.1f} min ago, reasons {cur.get('not_current_reasons')}")
say(isinstance(cur.get("opportunities"), list), "STP tracks the opportunity list: " +
    "; ".join(f"{o['id']} {o['trade']} {o['status']} {o['entry_zone']['low']}-{o['entry_zone']['high']}" for o in cur.get("opportunities") or []))
print("\nRESULT:", "ALL OK" if not bad else f"{len(bad)} CHECK(S): see above")
