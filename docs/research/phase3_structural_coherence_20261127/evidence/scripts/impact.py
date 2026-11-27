"""Phase 3 impact study (read-only): per actual trade, the SCA state (classify2), the separate room rule, opposing
open positions, and, for each trade the SCA would hold in Watch & Wait, the strategy's next fresh idea in the same
direction that the SCA would permit (no P&L is simulated for it: only what the bot's own journal recorded).

Room rule R (kept separate from the SCA, the ROOM_TO_LEVEL principle the owner approved on 19 Nov for breakouts,
applied to STP zones): room = pips from the idea entry to the near edge of the nearest live opposing STP zone
(WAITING/ACTIVE) ahead in the trade's path (AHEAD or NEAR_AHEAD); refused when room < the trade's actual stop.
R-b: an opposing zone that overlaps a live agreeing zone (OD-33 contested pair) is ignored.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path

S = Path(sys.argv[1])
sys.path.insert(0, str(S))
import classify2 as C  # noqa: E402

rows = json.load(open(S / 'forensic.json'))
dec = [json.loads(l) for l in open(S / 'data/records/GBPUSD/decisions.jsonl')]
dec = [x for x in dec if '2026-11-18' <= x['time_utc'][:10] <= '2026-11-27']
P = C.P


def room(r):
    d, e = r['direction'], D(r['idea_entry'])
    want = 'BUY' if d == 'buy' else 'SELL'
    _, zs = C.assess(r)
    best = bestb = None
    for z in zs:
        if z['pos'] not in ('AHEAD', 'NEAR_AHEAD'):
            continue
        opp = [m for m in z['members'] if m.split()[1] != want and m.split()[2] in ('WAITING', 'ACTIVE')]
        agr = [m for m in z['members'] if m.split()[1] == want and m.split()[2] in ('WAITING', 'ACTIVE')]
        if not opp:
            continue
        x = (z['dist'], f"{z['zone'][0]}-{z['zone'][1]} [{', '.join(opp)}]")
        best = min(best, x) if best else x
        if not agr:
            bestb = min(bestb, x) if bestb else x
    return best, bestb


out = []
for n, r in enumerate(rows, 1):
    st, zs = C.assess(r)
    T = P(r['opened_utc'])
    rm, rmb = room(r)
    stop = float(r['stop_pips'])
    others = [(j, x) for j, x in enumerate(rows, 1) if x['opened_utc'] < r['opened_utc'] < (x['closed_utc'] or '9')]
    opposite = [f"#{j} {x['strategy']} {x['direction']}" for j, x in others if x['direction'] != r['direction']]
    follow = []
    if st in ('S4_WITHIN_OPPOSING', 'S3_APPROACHING'):
        end = T.replace(hour=20, minute=30, second=0)
        seen = set()
        for x in dec:
            if x['kind'] != 'idea' or x['strategy'] != r['strategy'] or x['direction'] != r['direction']:
                continue
            t = P(x['time_utc'])
            if not (T < t <= end) or not x.get('allowed'):
                continue
            key = (x['time_utc'][:16], x['entry_price'])
            if key in seen:
                continue
            seen.add(key)
            st2, _ = C.assess({'opened_utc': x['time_utc'], 'direction': x['direction'], 'idea_entry': x['entry_price'],
                               'strategy': x['strategy']})
            if st2 not in ('S4_WITHIN_OPPOSING', 'S3_APPROACHING'):
                orders = [o for o in dec if o['kind'] in ('order',) and o.get('strategy') == x['strategy']
                          and o.get('direction') == x['direction'] and abs((P(o['time_utc']) - t).total_seconds()) < 90]
                follow.append({'t': x['time_utc'], 'entry': x['entry_price'], 'sca': st2,
                               'journal': [(o['time_utc'], o.get('result') or o.get('outcome') or '', (o.get('why') or o.get('reasons') or '')) for o in orders][:2]})
                break
    out.append({'n': n, 't': r['opened_utc'], 'ref': r['reference'], 'strategy': r['strategy'], 'dir': r['direction'],
                'entry': r['idea_entry'], 'fill': r['fill'], 'stop': stop, 'pips': r['pips'], 'gbp': r['gbp'], 'by': r['closed_by'],
                'how': r['how_closed'], 'auth': bool(r['stp_authorised']), 'analyser': (r['analyser'] or {}).get('state'),
                'sca': st, 'zones': zs,
                'room': rm and {'pips': rm[0], 'what': rm[1]}, 'room_refuse': bool(rm and rm[0] < stop),
                'room_b': rmb and {'pips': rmb[0], 'what': rmb[1]}, 'room_b_refuse': bool(rmb and rmb[0] < stop),
                'opposite_open': opposite, 'followup': follow,
                'mfe': r['excursion']['mfe_strict'] if r['excursion']['mfe_strict'] is not None else r['excursion']['mfe_wide'],
                'mae': r['excursion']['mae_strict'] if r['excursion']['mae_strict'] is not None else r['excursion']['mae_wide']})
json.dump(out, open(S / 'impact.json', 'w'), indent=1, default=str)
for x in out:
    print(f"{x['n']:2} {x['t'][5:16]} {x['strategy'][:14]:14} {x['dir']:4} {str(x['pips']):>6} {x['by'] or '':5} {x['sca'][:12]:12} "
          f"room {'-' if not x['room'] else round(x['room']['pips'],1)}/{x['stop']}{' REFUSE' if x['room_refuse'] else ''}{' (b:REFUSE)' if x['room_b_refuse'] else ''} "
          f"opp {len(x['opposite_open'])} follow {x['followup']}")
