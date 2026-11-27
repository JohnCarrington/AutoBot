"""Breadth of the SCA over every confirmed idea (allowed by common.check) 18-27 Nov: how often it would defer."""
import json, sys, collections
from pathlib import Path
S = Path(sys.argv[1]); sys.path.insert(0, str(S))
import classify2 as C
dec = [json.loads(l) for l in open(S / 'data/records/GBPUSD/decisions.jsonl')]
seen, out = set(), []
for x in dec:
    if x['kind'] != 'idea' or not x.get('allowed') or not ('2026-11-18' <= x['time_utc'][:10] <= '2026-11-27'):
        continue
    t = x['time_utc'][:16]
    k = (x['strategy'], x['direction'], t[:15])          # one per strategy/direction/10-minute bucket
    if k in seen:
        continue
    seen.add(k)
    st, _ = C.assess({'opened_utc': x['time_utc'], 'direction': x['direction'], 'idea_entry': x['entry_price'], 'strategy': x['strategy']})
    out.append({'t': x['time_utc'], 'strategy': x['strategy'], 'dir': x['direction'], 'entry': x['entry_price'], 'sca': st})
json.dump(out, open(S / 'breadth.json', 'w'), indent=1)
by = collections.Counter(o['sca'] for o in out)
print(len(out), by)
fam = collections.defaultdict(collections.Counter)
for o in out:
    fam[o['strategy']][o['sca'][:2]] += 1
for k, v in sorted(fam.items()):
    print(f"{k:24} {dict(v)}")
day = collections.defaultdict(collections.Counter)
for o in out:
    day[o['t'][:10]][o['sca'][:2]] += 1
for k, v in sorted(day.items()):
    print(k, dict(v))
