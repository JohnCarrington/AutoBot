"""Builds tests/technical/js/stp_chart_fixtures.json (owner, 25 November 2026): the STP tab's own API answers
(dashboard/stp.py overview, history, recommendation), made by the dashboard's real functions from the bot's records of
Wednesday 25 November 2026 at 14:05 UTC, for the chart-behaviour tests (test_stp_chart_follows_live.py). Read only.
    cd /opt/autobot && .venv/bin/python -I tests/technical/js/make_stp_chart_fixtures.py <out.json>"""
import json, sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from config.settings_loader import load_or_exit                           # noqa: E402
from dashboard import stp                                                 # noqa: E402
s = load_or_exit().for_pair("GBPUSD")
now = datetime(2026, 11, 25, 14, 5, 30, tzinfo=timezone.utc)
ids = ["STP-GBPUSD-20261125-0400-27", "STP-GBPUSD-20261125-1000-28", "STP-GBPUSD-20261125-1200-29",
       "STP-GBPUSD-20261125-1400-31"]
out = {"overview": stp.overview(s, now), "history": stp.history(s, "page=1&size=15&sort=created&order=desc&q=")[1],
       "recommendation": {i: stp.recommendation(s, "id=" + i, now)[1] for i in ids}}
for d in out["recommendation"].values():
    assert d.get("ok"), d
def trim(ov):        # the structural level maps are kept short (the tests are about which plan is drawn, not the levels)
    if ov:
        ov["levels"], ov["zones"] = ov["levels"][:12], ov["zones"][:4]
trim(out["overview"]["overlays"])
for d in out["recommendation"].values():
    trim(d["overlays_at_creation"])
out["history"]["rows"] = [r for r in out["history"]["rows"] if r["id"].startswith("STP-GBPUSD-20261125")]
json.dump(out, open(sys.argv[1], "w"), separators=(",", ":"), default=str)
print({k: len(json.dumps(v, default=str)) for k, v in out.items()}, [r["id"][-7:] for r in out["history"]["rows"]])
