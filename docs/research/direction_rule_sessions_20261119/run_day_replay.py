# Read-only check replay: the full paper engine (safety rules, trade manager) for one day, both new switches on; nothing sent.
# python run_day_replay.py 2026-11-18 out.json SCALE_OUT_REVERSAL=on ... DIRECTION_RULE_SESSIONS=on
import json, sys
from datetime import date
from research.analyser_control_days import run_day, UK
d = date.fromisoformat(sys.argv[1]); out = sys.argv[2]
extra = dict(a.split("=") for a in sys.argv[3:])
r = run_day(d, True, **extra)
j = {"extra": extra,
     "trades": [dict(opened=t.opened.astimezone(UK).strftime("%H:%M"), strategy=t.strategy, direction=t.direction,
                     entry=str(t.entry), pips=(None if t.pips is None else str(t.pips)), closed=t.closed) for t in r.trades],
     "blocked": [(t.astimezone(UK).strftime("%H:%M"), s, dr, b) for t, s, dr, b in r.blocked],
     "refused": [(t.astimezone(UK).strftime("%H:%M"), s, dr, rr) for t, s, dr, rr in r.refused]}
json.dump(j, open(out, "w"), indent=1, default=str); print("done", d, len(r.trades))
