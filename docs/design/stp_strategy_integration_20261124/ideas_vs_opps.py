"""Approximate as-of check of 24 Nov gated ideas against the opportunities the design would hold (INV-2 on).
Interaction approximated: any 5m candle in the 30 minutes up to the idea's candle interacts within 3 pips (the exact
pierce candle is computed in WP-6). Live windows are from the lifecycle trace in the readiness pack."""
import json, csv
rows=[r for r in csv.DictReader(open('/opt/autobot/data/candles/GBPUSD/5m/2026-11-24.csv'))]
f=lambda x: float(x)/10000; P=0.0003
# id, dir, low, high, live_from, live_to (exclusive; None = still live 21:00), authorising windows only
OPPS=[("S0900-18","sell",1.30750,1.30841,"09:00","12:00"),
      ("S1000-19","sell",1.30621,1.30715,"10:00","12:00"),
      ("S1300-20","sell",1.31355,1.31421,"13:00","13:35"),
      ("S1400-21","sell",1.31030,1.31141,"14:00","18:00"),("S1400-21","sell",1.31030,1.31141,"19:00","21:00"),
      ("S1500-22","sell",1.31355,1.31421,"15:00","21:00"),
      ("S1700-23","sell",1.31176,1.31286,"17:00","21:00"),
      ("B1000","buy",1.30621,1.30715,"10:00","11:05"),
      ("B1200","buy",1.30750,1.30854,"12:00","14:10"),
      ("B1500","buy",1.30750,1.30854,"15:00","17:10"),
      ("B1800","buy",1.31191,1.31286,"18:01","21:00"),
      ("B1900","buy",1.31026,1.31141,"19:00","19:05")]
def inter(lo,hi,zl,zh,d):
    return (hi>=zl-P and lo<=zh) if d=="sell" else (lo<=zh+P and hi>=zl)
G={'Bollinger bounce','Bollinger bounce 5m','level reversal'}
seen=set()
for l in open('/opt/autobot/data/records/GBPUSD/decisions.jsonl'):
    d=json.loads(l); t=d.get('time_utc','')
    if not t.startswith('2026-11-24') or d.get('kind')!='idea' or d.get('strategy') not in G: continue
    k=(t[11:16],d['strategy'],d['direction'])
    if k in seen: continue
    seen.add(k); hm=t[11:16]; hms=t[11:19]
    cand5=hm[:4]+('0' if int(hm[4])<5 else '5')
    win=[r for r in rows if r['start_utc'][11:16]<cand5 and r['start_utc'][11:16]>= f"{int(cand5[:2])-(1 if int(cand5[3:])<30 else 0):02d}:{(int(cand5[3:])-30)%60:02d}"]
    m=[o[0] for o in OPPS if o[1]==d['direction'] and o[4]<=hms<o[5] and any(inter(f(r['sell_low']),f(r['sell_high']),o[2],o[3],o[1]) for r in win)]
    print(hms, d['strategy'], d['direction'], d.get('entry_price'), '->', ','.join(m) or 'no matching opportunity', '| today:', 'allowed' if d.get('allowed') else (d.get('blocked_by') or '')[:45])
