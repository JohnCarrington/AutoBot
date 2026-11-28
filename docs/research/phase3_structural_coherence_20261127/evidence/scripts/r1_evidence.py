"""R1/R2 evidence over every confirmed idea 18-27 Nov (same 416 as breadth.py), with classify3's amended rules:
state changes vs classify2, and for every S4(b) idea (PAST an ACTIVE opposing zone) the hourly close that decided it."""
import json, sys, collections
from datetime import timedelta
from decimal import Decimal as D
from pathlib import Path
S = Path(sys.argv[1]); sys.path.insert(0, str(S))
import classify3 as K, classify2 as C
b = json.load(open(S / 'breadth.json'))
out, chg = [], []
for x in b:
    r = {'opened_utc': x['t'], 'direction': x['dir'], 'idea_entry': x['entry'], 'strategy': x['strategy']}
    st, v, found = K.assess(r)
    y = dict(x, sca3=st, members=[m for m in found if m['state']])
    out.append(y)
    if st != x['sca'][:2]:
        chg.append(y)
print('ideas', len(out), collections.Counter(o['sca3'] for o in out))
print('changed vs classify2:', len(chg))
for y in chg:
    print('  ', y['t'][:16], y['strategy'], y['dir'], y['entry'], y['sca'][:2], '->', y['sca3'], [(m['id'], m['trade'], m['status'], m['pos'], m['state']) for m in y['members']])
# R1: S4(b)
past = [y for y in out if any(m['state'] == 'S4' and m['pos'] == 'PAST' for m in y['members'])]
print('S4(b) ideas', len(past))
recs = C.recs
def decided(mid, T):
    """the first hourly close at/after T for opportunity mid and what STP recorded for it"""
    h = T.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    evs = [r for r in recs if r.get('id', '') and r['id'].endswith(mid) and r['event'] in ('broken', 'closed beyond', 'reclaim', 'wick sweep', 'completed', 'invalidated', 'superseded') and C.P(r['time_utc']) >= h]
    return h, (evs[0]['time_utc'][5:16], evs[0]['event'], (evs[0].get('why') or '')[:90]) if evs else None
rows = collections.OrderedDict()
for y in past:
    T = C.P(y['t'])
    for m in y['members']:
        if m['state'] == 'S4' and m['pos'] == 'PAST':
            k = (m['id'], T.strftime('%m-%d %H'))
            h, ev = decided(m['id'], T)
            c = [c for c in C.store.read_range('1h', h - timedelta(hours=1), h) if c.end == h]
            rows.setdefault(k, {'zone': m['zone'], 'trade': m['trade'], 'ideas': [], 'close': c and str(c[0].sell_close), 'low': c and str(c[0].sell_low), 'high': c and str(c[0].sell_high), 'ev': ev})
            rows[k]['ideas'].append(f"{y['t'][11:16]} {y['strategy'][:12]} {y['dir']} {y['entry']}")
for k, v in rows.items():
    print(k, v['trade'], v['zone'], 'hour H/L/C', v['high'], v['low'], v['close'], '| next:', v['ev'], '|', len(v['ideas']), v['ideas'][:4])
# R2: overlap structure among live members at S4/S5 ideas
ind = 0
for y in out:
    ms = [m for m in y['members'] if m['state'] in ('S4', 'S5', 'S1', 'S6')]
    zs = [m['zone'] for m in ms]
    for i, a in enumerate(zs):
        for j, c in enumerate(zs):
            if i < j and not K.overlap(a, c):
                for l, bb in enumerate(zs):
                    if l not in (i, j) and K.overlap(a, bb) and K.overlap(bb, c):
                        ind += 1
print('ideas with an indirect (chained) overlap among their members:', ind)
json.dump(out, open(S / 'breadth3.json', 'w'), indent=1, default=str)
