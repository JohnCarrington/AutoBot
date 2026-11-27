"""Phase 3: structural interaction of every actual trade (18-27 Nov 2026) with the STP zones live at its entry.

Read-only. Uses only what was known at the entry time: STP's recorded lifecycle events (recommendations.jsonl,
time <= entry) and the finished 5-minute candles before the entry.

Zones are treated as structural levels, independent of STP's forecast label: STP issues BUY and SELL opportunities
on the same zone (STP_BIDIRECTIONAL), so the label alone cannot say whether the zone is resistance or support for a
given trade. The role comes from the side price approached the zone from on its current visit:
    approached from below  -> resistance (a barrier for a BUY, the reversal level for a SELL)
    approached from above  -> support    (a barrier for a SELL, the reversal level for a BUY)
Existing thresholds only: NEAR = rejection.near_level_within_pips (3, STP's own NEAR), BREAK = STP's D-20 status
BROKEN (hourly close >= planner.break_beyond_pips 3 beyond), "confirmed break held" = STP's own invalidation text.

Interaction states (per trade, per zone group):
    APPROACHING   entry outside the zone, within NEAR of its near edge, on the approach side
    WITHIN        entry inside the zone (or within NEAR beyond the far edge) and no D-20 break
    BEYOND_UNCONF entry beyond the far edge by more than NEAR, but STP has no BROKEN / break-held for the zone
    BROKEN        STP BROKEN at T (break confirmed, inside the 3-candle hold window)
    BREAK_HELD    STP invalidated the zone with "confirmed break held" before T (the level is crossed and kept)
    FAILED_BREAK  STP returned the zone to Watch & Wait after a break ("failed breakout") and no new break since
    CLEAR         none of the above (zone further than NEAR, on either side)
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, '/home/autobot/worktrees/autobot-phase3-research')
from prices.store import CandleStore

S = Path(sys.argv[1])
UTC = timezone.utc
NEAR = D('3')
store = CandleStore(S / 'store' / 'GBPUSD', 10**6, warn=lambda m: None)
rows = json.load(open(S / 'forensic.json'))
recs = [json.loads(l) for l in open(S / 'data/planner/GBPUSD/recommendations.jsonl')]


def P(s):
    return datetime.fromisoformat(s.replace('Z', '+00:00')).astimezone(UTC)


def opps_at(T):
    o = {}
    for r in recs:
        if P(r['time_utc']) > T:
            break
        i = r.get('id')
        if not i:
            continue
        x = o.setdefault(i, {'id': i, 'status': None, 'ev': []})
        p = r.get('plan') or {}
        z = p.get('zone') or {}
        if z.get('low'):
            x['zone'] = (D(z['low']), D(z['high']))
            x['trade'] = p.get('trade')
            x['class'] = z.get('class')
        if r.get('status'):
            x['status'] = r['status']
        x['ev'].append((r['time_utc'], r['event'], (r.get('why') or '')[:200]))
    return o


def groups(opps, T):
    """Opportunities whose zones overlap (PD-2 overlap, not exact price), merged into one structural level."""
    keep = []
    for x in opps.values():
        if 'zone' not in x:
            continue
        held = x['status'] == 'INVALIDATED' and any('confirmed break held' in w for _, e, w in x['ev'] if e == 'invalidated')
        last = P(x['ev'][-1][0])
        if x['status'] in ('WAITING', 'ACTIVE', 'BROKEN') or (held and T - last <= timedelta(hours=24)):
            x['held'] = held
            keep.append(x)
    gs = []
    for x in sorted(keep, key=lambda x: x['zone']):
        for g in gs:
            if x['zone'][0] < g['hi'] and g['lo'] < x['zone'][1]:   # strict overlap: shared edge only is not the same
                g['m'].append(x); g['lo'] = min(g['lo'], x['zone'][0]); g['hi'] = max(g['hi'], x['zone'][1])
                break
        else:
            gs.append({'lo': x['zone'][0], 'hi': x['zone'][1], 'm': [x]})
    return gs


def approach_side(lo, hi, T, break_times):
    """Role of the zone for price at T, from finished 5m candles of the last 3 days (bid/ask mid closes).
    Visits are unbroken runs of candles whose range reaches the band [lo-NEAR, hi+NEAR]. The first visit's
    approach side sets the role (approached from below = resistance, from above = support). A later visit that
    leaves on the other side (a 5m crossing) flips the role only when STP recorded a D-20 break of the zone
    (event 'broken') between that visit's start and T; a sweep or an unconfirmed crossing does not.
    Returns (side, last_visit_start, last_visit_end, crossings) where crossings lists (start, confirmed)."""
    cs = [c for c in store.read_range('5m', T - timedelta(days=5), T) if c.end <= T]
    band_lo, band_hi = lo - NEAR, hi + NEAR

    def touches(c):
        return min(c.buy_high, c.sell_high) >= band_lo and max(c.buy_low, c.sell_low) <= band_hi

    def side(c):
        m = (c.buy_close + c.sell_close) / 2
        return 'below' if m < band_lo else ('above' if m > band_hi else 'inside')
    visits, i = [], 0
    while i < len(cs):
        if touches(cs[i]):
            j = i
            while j + 1 < len(cs) and touches(cs[j + 1]):
                j += 1
            before = side(cs[i - 1]) if i > 0 else None
            after = side(cs[j + 1]) if j + 1 < len(cs) else None
            visits.append((cs[i].start, cs[j].start, before, after))
            i = j + 1
        else:
            i += 1
    if not visits:
        return None, None, None, []
    role_side = visits[0][2] or (side(cs[0]) if side(cs[0]) != 'inside' else None)
    crossings = []
    for k, (vs, ve, before, after) in enumerate(visits):
        if before and after and before != after and 'inside' not in (before, after):
            until = visits[k + 1][0] if k + 1 < len(visits) else T
            want = 'up' if after == 'above' else 'down'
            confirmed = any(vs <= bt <= until and bd == want for bt, bd in break_times)
            crossings.append((vs.isoformat(), after, confirmed))
            if confirmed:
                role_side = 'above' if after == 'above' else 'below'   # price now beyond: zone approached from that side
    return role_side, visits[-1][0], visits[-1][1], crossings


out = []
for n, r in enumerate(rows, 1):
    T = P(r['opened_utc'])
    e = D(r['idea_entry'])
    d = r['direction']
    gs = groups(opps_at(T), T)
    zs = []
    for g in gs:
        lo, hi = g['lo'], g['hi']
        bts = [(P(t), 'up' if "zone's top" in w else 'down') for t, ev, w in sorted(sum((x['ev'] for x in g['m']), [])) if ev == 'broken']
        side, since, vend, crossings = approach_side(lo, hi, T, bts)
        st = [x['status'] for x in g['m']]
        evs = sorted(sum((x['ev'] for x in g['m']), []))
        broken = 'BROKEN' in st
        held = any(x.get('held') for x in g['m'])
        failed = any(ev == 'failed breakout' for _, ev, _ in evs) and not broken
        if side is None:     # no approach seen in 5 days: STP's own label, when the group has one direction only
            labels = {x['trade'] for x in g['m']}
            side = {'SELL': 'below', 'BUY': 'above'}.get(labels.pop()) if len(labels) == 1 else None
        role = {'below': 'resistance', 'above': 'support'}.get(side)
        # barrier for this trade: resistance for a buy, support for a sell
        barrier = (role == 'resistance' and d == 'buy') or (role == 'support' and d == 'sell')
        # position of the entry relative to the zone, in the trade's direction
        if d == 'buy':
            ahead = lo - e          # >0: zone above (ahead)
            past = e - hi           # >0: entry above the zone top
        else:
            ahead = e - hi
            past = lo - e
        if ahead > NEAR:
            pos = 'CLEAR_AHEAD'
        elif ahead > 0:
            pos = 'APPROACHING'
        elif past <= 0:
            pos = 'INSIDE'
        elif past <= NEAR:
            pos = 'JUST_BEYOND'
        else:
            pos = 'BEYOND'
        if broken:
            state = 'BROKEN'
        elif held:
            state = 'BREAK_HELD'
        elif failed:
            state = 'FAILED_BREAK'
        else:
            state = {'CLEAR_AHEAD': 'CLEAR', 'APPROACHING': 'APPROACHING', 'INSIDE': 'WITHIN', 'JUST_BEYOND': 'WITHIN',
                     'BEYOND': 'BEYOND_UNCONF'}[pos]
        recent = [f"{t[5:16]} {ev}" for t, ev, _ in evs if ev in ('active', 'wick sweep', 'closed beyond', 'broken', 'failed breakout',
                                                                   'reclaim', 'invalidated', 'completed')][-4:]
        zs.append({'zone': [float(lo), float(hi)], 'labels': sorted({f"{x['trade']}:{x['status']}{'(held)' if x.get('held') else ''}" for x in g['m']}),
                   'ids': [x['id'][-7:] for x in g['m']], 'approach': side, 'visit_start': since and since.isoformat(), 'visit_end': vend and vend.isoformat(), 'crossings': crossings,
                   'role': role, 'barrier_for_trade': barrier, 'position': pos, 'state': state,
                   'ahead_pips': float(ahead), 'past_pips': float(past), 'recent': recent})
    out.append({'n': n, 't': r['opened_utc'], 'strategy': r['strategy'], 'dir': d, 'entry': float(e), 'fill': r['fill'],
                'stop': float(r['stop_pips']), 'pips': r['pips'], 'gbp': r['gbp'], 'by': r['closed_by'],
                'auth': bool(r['stp_authorised']), 'state': (r['analyser'] or {}).get('state'), 'zones': zs,
                'mfe': r['excursion']['mfe_strict'] if r['excursion']['mfe_strict'] is not None else r['excursion']['mfe_wide'],
                'mae': r['excursion']['mae_strict'] if r['excursion']['mae_strict'] is not None else r['excursion']['mae_wide']})
json.dump(out, open(S / 'classify.json', 'w'), indent=1, default=str)
for x in out:
    z = '; '.join(f"{a['zone'][0]:.1f}-{a['zone'][1]:.1f} {a['role'] or '?'}{'*' if a['barrier_for_trade'] else ''} {a['position']}/{a['state']} {','.join(a['labels'])}"
                  for a in x['zones'] if a['position'] != 'CLEAR_AHEAD' or a['state'] not in ('CLEAR',))
    print(f"{x['n']:2} {x['t'][5:16]} {x['strategy'][:14]:14} {x['dir']:4} {x['entry']:.1f} st{x['stop']:>5} {str(x['pips']):>6} {x['by'] or '':5} | {z}")
