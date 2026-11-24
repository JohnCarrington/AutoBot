"""Run the 24 Nov full-path replay with the code on sys.path (a worktree), all STP switches off unless 'on'."""
import sys, json, time, importlib.util
from datetime import datetime, UTC
from pathlib import Path
root, out, mode = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
sys.path.insert(0, root)
spec = importlib.util.spec_from_file_location("h", "/home/autobot/worktrees/stp-impl/tests/stp/harness.py")
h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
out.mkdir(parents=True, exist_ok=True)
stp = mode == "on"
kw = {"stp_opportunities": True, "stp_bidirectional": True, "stp_authorises_entries": True} if stp else {}
base = h.live_settings(out, **kw) if (stp or Path(root, "stp").exists()) else None
if base is None:      # the base commit has no STP switches: same file without them
    from config.settings_loader import load_settings
    p = out / "switches.env"; p.write_text(h.LIVE_SWITCHES_20261124)
    base = load_settings(switches_from=p).for_pair("GBPUSD")
s = h.Over(base, out)
store = h.live_store(s)
t0 = time.time()
r = h.replay_day(s, store, datetime(2026, 11, 24, 21, 0, tzinfo=UTC), stp=stp)
print("seconds", round(time.time() - t0), "opened", len(r["engine"].opened))
json.dump(h.read_records(s), open(out / "records.json", "w"), indent=0)
