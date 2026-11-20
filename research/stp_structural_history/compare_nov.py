import json,sys
from datetime import datetime,timezone,timedelta
from config.settings_loader import load_settings
from prices.store import CandleStore
from prices.model import parse_iso
S=sys.argv[1]
s=load_settings().for_pair("GBPUSD")
st=CandleStore("/opt/autobot/data/candles/GBPUSD", s.candles.compress_after_days)
END=datetime(2026,11,20,9,30,tzinfo=timezone.utc)
five=[c for c in st.read_range("5m", datetime(2026,11,17,20,tzinfo=timezone.utc), END) if c.end<=END]
h1=[c for c in st.read_range("1h", datetime(2026,11,17,20,tzinfo=timezone.utc), END) if c.end<=END]
def load(v): return {p['as_of_utc'][:13]:p for p in map(json.loads,open(f"{S}/{v}/hourly_plans.jsonl"))}
P={v:load(v) for v in "ABC"}
def fwd(p):
    ez=p.get('entry_zone'); pr=(p.get('destinations') or {}).get('primary'); inv=p.get('invalidation') or {}
    if not ez or not pr: return None
    t0=parse_iso(p['as_of_utc']); sell=p['trade']=='SELL'
    lo,hi=float(ez['low']),float(ez['high']); dz=pr['zone']; dlo,dhi=float(dz['low']),float(dz['high'])
    zb=float(inv['zone_break_close'])
    te=td=ti=None
    for c in five:
        if c.end<=t0: continue
        if te is None and float(c.sell_low)<=hi and float(c.sell_high)>=lo: te=c.end
        if td is None and float(c.sell_low)<=dhi and float(c.sell_high)>=dlo: td=c.end
    for c in h1:
        if c.end<=t0: continue
        if ti is None and ((float(c.sell_close)>=zb) if sell else (float(c.sell_close)<=zb)): ti=c.end
    f=lambda t: t.strftime('%d %H:%M') if t else '-'
    if te and td and te<=td and (not ti or td<ti): o='ENTRY→DEST'
    elif te and ti and (not td or ti<=td): o='ENTRY→INVALIDATED'
    elif td and not te: o='DEST w/o ENTRY'
    elif te: o='ENTRY, open'
    else: o='no entry yet'
    return f"{o} (entry {f(te)}, dest {f(td)}, 1h break {f(ti)})"
def brief(p):
    ez=p.get('entry_zone'); pr=(p.get('destinations') or {}).get('primary')
    if not ez: return "NO: "+(p.get('no_recommendation') or '')[:60]
    return f"{p['trade']} {ez['low']}-{ez['high']} → {pr['price']} ({','.join(x for x in pr['zone']['levels'] if 'historical' in x)[:40]}) inv {p['invalidation']['zone_break_close']}"
rows=[]
for k in sorted(P['A']):
    if k<'2026-11-18T00': continue
    a,b,c=P['A'][k],P['B'][k],P['C'][k]
    assert (a['dominant_direction'],a['condition'])==(c['dominant_direction'],c['condition'])
    ba,bb,bc=brief(a),brief(b),brief(c)
    mark='' if ba==bc else ' **'
    print(k[5:], a['dominant_direction'][:4], (a['condition'] or '')[:12], '| A:',ba,'| C:',bc if ba!=bc else '=', mark)
    if ba!=bc and c.get('entry_zone'): print('       C outcome:', fwd(c))
    if ba!=bb: print('       B differs from A:', bb)
print("A plans",sum(1 for k in P['A'] if k>='2026-11-18' and P['A'][k].get('entry_zone')),"C plans",sum(1 for k in P['C'] if k>='2026-11-18' and P['C'][k].get('entry_zone')))
