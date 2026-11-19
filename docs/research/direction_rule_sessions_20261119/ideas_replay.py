# Read-only check replay (owner, 19 November 2026): the strategies only, Thu 19 Nov 06:00-10:30 and Wed 18 Nov 06:00-20:30 UK,
# DIRECTION_RULE_SESSIONS on and off, the live switches and TREND_IGNORES_HOURLY_READ on; nothing sent. Run from the repo root with PYTHONPATH=.
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from research.analyser_control_days import ideas_day
UK=ZoneInfo("Europe/London")
SESS=("Asian range breakout","session sweep","New York open reversal")
ST4={"SCALE_OUT_REVERSAL":"on","TRAIL_NO_LOSS":"on","LR_ENTRY_NEAR_LEVEL":"on","LEVEL_STOPS":"on","TREND_IGNORES_HOURLY_READ":"on"}
f=lambda t: t.astimezone(UK).strftime("%H:%M")
for d,(h0,h1) in ((date(2026,11,19),((6,0),(10,30))),(date(2026,11,18),((6,0),(20,30)))):
    a=datetime.combine(d,time(*h0),tzinfo=UK); b=datetime.combine(d,time(*h1),tzinfo=UK)
    res={}
    for sw in ("on","off"):
        _, ideas, r = ideas_day(d, True, **ST4, DIRECTION_RULE_SESSIONS=sw)
        res[sw]=[i for i in ideas if a<=i.time<=b]
        print(f"===== {d} DIRECTION_RULE_SESSIONS={sw} (read back {r.s.switches.direction_rule_sessions})")
        for i in res[sw]:
            if i.strategy in SESS:
                print(f(i.time), i.strategy, i.direction, i.entry_price, "| rule:", i.direction_rule, "|", "ALLOWED" if i.allowed else "BLOCKED: "+i.blocked_by)
    key=lambda i:(i.time,i.strategy,i.direction,str(i.entry_price),i.allowed,i.blocked_by)
    oth=lambda L:[key(i) for i in L if i.strategy not in SESS]
    print(f"== {d}: other strategies' ideas identical on/off: {oth(res['on'])==oth(res['off'])} ({len(oth(res['on']))} ideas)")
