# Read-only replay used for REPORT.md: today's stored candles through the live code (no orders). Run from /opt/autobot with PYTHONPATH=/opt/autobot.
from datetime import date, datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from research.analyser_control_days import ideas_day
UK=ZoneInfo("Europe/London")
ch, ideas, r = ideas_day(date(2026,11,19), True, SCALE_OUT_REVERSAL="on", TRAIL_NO_LOSS="on", LR_ENTRY_NEAR_LEVEL="on", LEVEL_STOPS="on")
t0=datetime(2026,11,19,6,0,tzinfo=timezone.utc)
f=lambda t: t.astimezone(UK).strftime("%H:%M")
print("== STATE CHANGES (replay)")
for c in ch:
    if c.time>=t0-timedelta(hours=1): print(f(c.time), c.state, c.direction, c.trend_type, "|", c.reason[:250])
print("== EMA PULLBACK step 0 (hourly trend) per hour")
last=None
for k in range(0, 60):
    t=t0+timedelta(minutes=5*k)
    if t> datetime.now(timezone.utc): break
    h=r.pullback.hourly.at(t); s=(h.direction,h.qualified,h.why)
    if s!=last: print(f(t), h.direction, "qualified" if h.qualified else "not qualified", "|", h.why); last=s
print("== EMA PULLBACK notes since 06:00")
for n in r.pullback.notes:
    if n[0]>=t0: print(f(n[0]), n[1], n[2][:300])
print("== SLOW GRIND notes since 06:00")
for n in r.grind.notes:
    if n[0]>=t0: print(f(n[0]), n[1], n[2][:300])
print("== HOURLY READ and analyser's view (trend_hourly) per 5m candle, changes only")
lastr=lastt=None
for i,c in enumerate(r.week):
    if c.start<t0: continue
    hr=r.hourly_read.at(c.start); th=r.trend_hourly(i-1, hr)
    a=hr.line(); b=th.line() if th is not None else None
    if a!=lastr: print(f(c.start), "HOURLY READ:", a[:300]); lastr=a
    if b!=lastt: print(f(c.start), "ANALYSER VIEW:", (b or "None")[:300]); lastt=b
print("== IDEAS since 06:00 (replay)")
for i in ideas:
    if i.time>=t0 and i.strategy in ("EMA pullback","slow grind"): print(f(i.time), i.strategy, i.direction, i.entry_price, "allowed" if i.allowed else "BLOCKED: "+i.blocked_by[:300])
print("last week candle", f(r.week[-1].start))
