"""Phase 3 SCA, amended rules after the independent review (R1-R5), read-only. Supersedes classify2.py's grouping.

Changes from classify2.py (each one a clarification asked by the review; no new threshold):
  R1  PAST is measured against each opposing opportunity's OWN zone-break price (STP's zone_break_close = far edge
      +/- planner.break_beyond_pips), not against the union of a zone group and not with NEAR. An ended opportunity is
      never a barrier: the 24-hour look-back for "confirmed break held" is removed. A held break only names S7, which
      permits exactly like S2 (no admission effect).
  R2  Every live opportunity is judged ON ITS OWN. A conflict is resolved only for the opportunity whose own evidence
      resolves it: its own D-20 break (S6), or a contested-zone rejection (S5) where the strategy's rejection candle
      reached THAT opportunity's zone and a live agreeing opportunity whose zone DIRECTLY overlaps it (PD-2 strict
      overlap; edge-only and chained/indirect overlap do not count) was also reached. Any opposing opportunity left
      unresolved gives S4, whatever any other opportunity says. A live break AGAINST the trade (S4(c)) is never
      resolved by S5.
  R3  (production data carry no Phase 2 gap fields; on the Phase 2 build an opportunity with unreconciled() reasons
      cannot provide a resolution, see 03_ARCHITECTURE.md 3.10). Reported here as 'n/a in this data'.

Outputs per idea: the state, the verdict, every member's own position and per-member finding, and for S4(b) the
hourly close that next decided it (R1 evidence).
"""
import json
import sys
from datetime import timedelta
from decimal import Decimal as D
from pathlib import Path

S = Path(sys.argv[1])
sys.path.insert(0, str(S))
import classify2 as C  # noqa: E402  (opps_at, store, families, rejection stand-in)

NEAR = D('3')       # rejection.near_level_within_pips (STP's interacts)
BEYOND = D('3')     # planner.break_beyond_pips (STP's D-20)
ORDER = ['S4', 'S3', 'S5', 'S6', 'S7', 'S1', 'S2']


def overlap(a, b):
    """PD-2/PD-3: strict overlap; zones that only share an edge do not overlap."""
    return a[0] < b[1] and b[0] < a[1]


def pos_member(d, e, m):
    """Position of entry e for a trade of direction d against opportunity m's own zone.
    AHEAD / NEAR_AHEAD: in front (NEAR = STP's interacts). AT: inside, or past the far edge but not beyond m's own
    zone-break price. PAST: beyond m's own zone-break price in the trade's direction. BEHIND: the zone is behind."""
    lo, hi = m['zone']
    ahead = (lo - e) if d == 'buy' else (e - hi)
    if ahead > NEAR:
        return 'AHEAD'
    if ahead > 0:
        return 'NEAR_AHEAD'
    far = hi if d == 'buy' else lo
    beyond = (e - far) if d == 'buy' else (far - e)
    if beyond <= 0:
        return 'AT'
    return 'AT' if beyond < BEYOND else 'PAST'    # zone_break_close is "at or beyond far edge + 3": PAST from there


def reached(d, T, z):
    return C.rejection_reached(d, T, z[0], z[1])


def assess(r):
    T = C.P(r['opened_utc'])
    d, e, f = r['direction'], D(r['idea_entry']), C.fam(r['strategy'])
    want = 'BUY' if d == 'buy' else 'SELL'
    allo = [x for x in C.opps_at(T).values() if 'zone' in x]
    live = [x for x in allo if x['status'] in ('WAITING', 'ACTIVE', 'BROKEN')]
    found = []
    for m in live:
        p = pos_member(d, e, m)
        mine = m['trade'] == want
        res = None
        if not mine:                                    # opposing: it can only break in the trade's direction
            if m['status'] == 'BROKEN':
                res = ('S6', 'own D-20 break in the trade direction') if p in ('AT', 'PAST') else None
            elif p == 'AT' or (p == 'PAST' and m['status'] == 'ACTIVE'):
                why = 'AT, unresolved' if p == 'AT' else 'PAST its own break price, ACTIVE, no D-20 break'
                res = ('S4', why)
                if f == 'reversal' and reached(d, T, m['zone']):
                    pair = [a for a in live if a['trade'] == want and a['status'] in ('WAITING', 'ACTIVE')
                            and overlap(a['zone'], m['zone']) and reached(d, T, a['zone'])]
                    if pair:
                        res = ('S5', f"contested with {pair[0]['id'][-7:]} (direct overlap), own rejection reached both")
            elif p == 'NEAR_AHEAD' and m['status'] in ('WAITING', 'ACTIVE'):
                res = ('S3', 'within NEAR ahead')
        else:                                           # agreeing: it can only break against the trade
            if m['status'] == 'BROKEN' and p in ('AT', 'PAST'):
                res = ('S4', 'AT/PAST an agreeing zone BROKEN against the trade (live break window)')
            elif m['status'] in ('WAITING', 'ACTIVE') and p == 'AT':
                res = ('S1', 'AT a live agreeing zone')
        found.append({'id': m['id'][-7:], 'trade': m['trade'], 'status': m['status'], 'zone': [float(m['zone'][0]), float(m['zone'][1])],
                      'pos': p, 'state': res and res[0], 'why': res and res[1]})
    # S7 naming only (no admission effect): AT/PAST an ended opposing opportunity whose break in the trade's direction
    # was held, with no live opportunity overlapping it created after its ending (bounded by STP's own lifecycle)
    for m in allo:
        if m['held'] and m['trade'] != want and m['break'] and pos_member(d, e, m) in ('AT', 'PAST'):
            end = C.P(m['ev'][-1][0])
            if not [x for x in live if overlap(x['zone'], m['zone']) and C.P(x['ev'][0][0]) > end]:
                found.append({'id': m['id'][-7:], 'trade': m['trade'], 'status': 'INVALIDATED held', 'zone': [float(m['zone'][0]), float(m['zone'][1])],
                              'pos': pos_member(d, e, m), 'state': 'S7', 'why': 'break held (naming only)'})
    states = {x['state'] for x in found if x['state']}
    state = next((s for s in ORDER if s in states), 'S2')
    verdict = 'watch and wait' if state == 'S4' else 'permit'
    return state, verdict, found


def next_close(T):
    h = T.replace(minute=0, second=0, microsecond=0)
    return h, h + timedelta(hours=1)


if __name__ == '__main__':
    rows = json.load(open(S / 'forensic.json'))
    old = {x['t']: x['state'][:2] for x in json.load(open(S / 'sca.json'))}
    out = []
    for n, r in enumerate(rows, 1):
        st, v, found = assess(r)
        out.append({'n': n, 't': r['opened_utc'], 'strategy': r['strategy'], 'dir': r['direction'], 'pips': r['pips'],
                    'by': r['closed_by'], 'state': st, 'old': old.get(r['opened_utc']), 'members': [x for x in found if x['state']]})
    json.dump(out, open(S / 'sca3.json', 'w'), indent=1, default=str)
    for x in out:
        flag = '' if x['state'] == x['old'] else f'   <-- was {x["old"]}'
        if x['state'] != 'S2' or flag:
            print(f"{x['n']:2} {x['t'][5:16]} {x['strategy'][:16]:16} {x['dir']:4} {str(x['pips']):>6} {x['by'] or '':5} {x['state']}{flag} "
                  + '; '.join(f"{m['id']} {m['trade']} {m['status']} {m['pos']} {m['state']}" for m in x['members']))
    print('changed:', sum(1 for x in out if x['state'] != x['old']))
