# Read-only check replay (owner, 19 November 2026): Thursday 19 November 2026, 06:00-09:30 UK, through this branch's code,
# switch on and off, live switches otherwise; nothing sent. Run from the repo root with PYTHONPATH=. ; output in replay_2026-11-19.txt
import sys
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo
from research.analyser_control_days import ideas_day
UK=ZoneInfo("Europe/London")
f=lambda t: t.astimezone(UK).strftime("%H:%M")
a=datetime(2026,11,19,6,0,tzinfo=timezone.utc); b=datetime(2026,11,19,9,30,tzinfo=timezone.utc)
for sw in ("on","off"):
    ch, ideas, r = ideas_day(date(2026,11,19), True, SCALE_OUT_REVERSAL="on", TRAIL_NO_LOSS="on", LR_ENTRY_NEAR_LEVEL="on", LEVEL_STOPS="on", TREND_IGNORES_HOURLY_READ=sw)
    print(f"===== TREND_IGNORES_HOURLY_READ={sw} (switch read back: {r.s.switches.trend_ignores_hourly_read})")
    for i in ideas:
        if a<=i.time<=b and i.strategy in ("slow grind","EMA pullback","breakout"):
            print(f(i.time), i.strategy, i.direction, i.entry_price, "| state:", i.state, i.direction if False else "", "|", "ALLOWED" if i.allowed else "BLOCKED: "+i.blocked_by)
            if i.allowed: print("     ", [s for s in i.steps if s.startswith("allowed at entry")][0][:400])
    print("-- EMA pullback notes 06:00-09:30")
    for n in r.pullback.notes:
        if a<=n[0]<=b: print(f(n[0]), n[1], n[2][:250])
