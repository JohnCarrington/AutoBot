"""Phase 3 structural coherence assessment (SCA) applied, read-only, to every actual trade 18-27 Nov 2026.

Only what was known at the entry time: STP's recorded lifecycle (recommendations.jsonl, events <= entry) and the
finished 5-minute candles before the entry. Only existing thresholds: NEAR = rejection.near_level_within_pips (3,
STP's own "interacts"); a break = STP's D-20 event 'broken' (hourly close >= planner.break_beyond_pips beyond the
far edge); a held break = STP's own 'confirmed break held' invalidation.

Per trade (direction d, idea entry e), every STP opportunity live at T (WAITING, ACTIVE, BROKEN) or ended by
'confirmed break held' in the last 24 h, grouped by zone overlap (PD-2), is read as:
    opposing  = an opportunity whose trade is the other direction
    agreeing  = an opportunity whose trade is d
and the entry's position against the zone in the trade's own direction:
    AHEAD (beyond NEAR, in the trade's path)   NEAR_AHEAD (<= NEAR before the near edge)   AT (inside, or <= NEAR
    past the far edge)   PAST (more than NEAR past the far edge: the trade's direction has gone through it)   BEHIND
State of the trade (first match):
    S6 CONFIRMED_BREAK     an opposing zone at/past which the entry sits has a D-20 break in the trade's direction
                           (BROKEN now) -> the barrier is overcome
    S7 CONTINUATION        ... or the break was held (STP invalidated 'confirmed break held') and the entry is past it
                           or retesting it (AT) from the broken side
    S4 WITHIN_OPPOSING     the entry is AT an opposing live zone (WAITING/ACTIVE) without such a break, or PAST one
                           that STP holds ACTIVE (touched, unresolved) without a break; a zone BROKEN against the
                           trade's direction with the entry AT/PAST it counts the same (trading against a confirmed break)
        S5 CONFIRMED_REJECTION  exception to S4: a reversal-family idea whose own rejection reached the zone, where the
                           zone also carries a live opportunity in the trade's direction (OD-33 contested zone: STP
                           recognises both outcomes; the strategy's rejection decides)
    S3 APPROACHING         an opposing live zone NEAR_AHEAD
    S1 ALIGNED             an agreeing live zone the entry is AT, or PAST-by-break in the trade's direction
    S2 NEUTRAL             otherwise
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
REVERSAL = {'Bollinger bounce', 'Bollinger bounce 5m', 'level reversal', 'New York open reversal', 'session sweep', 'range trade'}
CONTINUATION = {'EMA pullback', 'slow grind'}
BREAKOUT = {'breakout', 'Asian range breakout'}


def fam(s):
    return 'reversal' if s in REVERSAL else ('continuation' if s in CONTINUATION else 'breakout')


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
        x = o.setdefault(i, {'id': i, 'status': None, 'ev': [], 'ever_active': False, 'break': None})
        p = r.get('plan') or {}
        z = p.get('zone') or {}
        if z.get('low'):
            x['zone'] = (D(z['low']), D(z['high']))
            x['trade'] = p.get('trade')
        if r.get('status'):
            x['status'] = r['status']
        if r['event'] == 'active' or r['event'] == 'failed breakout':
            x['ever_active'] = True
        if r['event'] == 'broken':
            w = r.get('why') or ''
            x['break'] = ('up' if "zone's top" in w else 'down', r['time_utc'])
        if r['event'] == 'failed breakout':
            x['break'] = None
        x['ev'].append((r['time_utc'], r['event'], r.get('why') or ''))
    for x in o.values():
        x['held'] = x['status'] == 'INVALIDATED' and any('confirmed break held' in w for _, e, w in x['ev'] if e == 'invalidated')
        if x['held'] and not x['break']:
            # the held break's direction is the last 'broken' event's
            for t, e, w in reversed(x['ev']):
                if e == 'broken':
                    x['break'] = ('up' if "zone's top" in w else 'down', t)
                    break
    return o


def position(d, e, lo, hi):
    ahead = (lo - e) if d == 'buy' else (e - hi)     # >0: the zone is in the trade's path
    past = (e - hi) if d == 'buy' else (lo - e)      # >0: the entry is beyond the zone in the trade's direction
    if ahead > NEAR:
        return 'AHEAD', ahead
    if ahead > 0:
        return 'NEAR_AHEAD', ahead
    if past <= NEAR:
        return 'AT', D(0)
    return 'PAST', -past


def rejection_reached(d, T, lo, hi):
    """Forensic stand-in for the strategy's rejection candle (production: context.rejection_candle): the last two
    finished 5m candles before the entry reached the zone band (a BUY's low / a SELL's high)."""
    cs = [c for c in store.read_range('5m', T - timedelta(minutes=30), T) if c.end <= T][-2:]
    if d == 'buy':
        return any(c.sell_low <= hi + NEAR for c in cs)
    return any(c.buy_high >= lo - NEAR for c in cs)


def assess(r):
    T = P(r['opened_utc'])
    d, e, f = r['direction'], D(r['idea_entry']), fam(r['strategy'])
    want = 'BUY' if d == 'buy' else 'SELL'
    brk_dir = 'up' if d == 'buy' else 'down'
    live = [x for x in opps_at(T).values() if 'zone' in x and (
        x['status'] in ('WAITING', 'ACTIVE', 'BROKEN') or (x['held'] and T - P(x['ev'][-1][0]) <= timedelta(hours=24)))]
    groups = []
    for x in sorted(live, key=lambda x: x['zone']):
        for g in groups:
            if x['zone'][0] < g['hi'] and g['lo'] < x['zone'][1]:
                g['m'].append(x); g['lo'] = min(g['lo'], x['zone'][0]); g['hi'] = max(g['hi'], x['zone'][1]); break
        else:
            groups.append({'lo': x['zone'][0], 'hi': x['zone'][1], 'm': [x]})
    zs, cands = [], []
    for g in groups:
        pos, dist = position(d, e, g['lo'], g['hi'])
        opp = [x for x in g['m'] if x['trade'] != want]
        agr = [x for x in g['m'] if x['trade'] == want]
        live_opp = [x for x in opp if x['status'] in ('WAITING', 'ACTIVE')]
        live_agr = [x for x in agr if x['status'] in ('WAITING', 'ACTIVE')]
        brk_with = [x for x in g['m'] if x['break'] and x['break'][0] == brk_dir and (x['status'] == 'BROKEN' or x['held'])]
        brk_against = [x for x in g['m'] if x['break'] and x['break'][0] != brk_dir and x['status'] == 'BROKEN']
        held_with = [x for x in brk_with if x['held']]
        state = None
        if pos in ('AT', 'PAST') and brk_with and not brk_against:
            state = 'S7_CONTINUATION' if held_with else 'S6_CONFIRMED_BREAK'
        elif pos in ('AT', 'PAST') and brk_against:
            state = 'S4_WITHIN_OPPOSING'          # against a confirmed break
        elif pos == 'AT' and live_opp:
            state = 'S4_WITHIN_OPPOSING'
        elif pos == 'PAST' and [x for x in live_opp if x['status'] == 'ACTIVE' or x['ever_active']]:
            state = 'S4_WITHIN_OPPOSING'          # through a touched opposing zone without a D-20 break
        elif pos == 'NEAR_AHEAD' and live_opp:
            state = 'S3_APPROACHING'
        elif pos in ('AT',) and live_agr:
            state = 'S1_ALIGNED'
        if state == 'S4_WITHIN_OPPOSING' and f == 'reversal' and live_agr and not brk_against and rejection_reached(d, T, g['lo'], g['hi']):
            state = 'S5_CONFIRMED_REJECTION'
        if state:
            cands.append(state)
        zs.append({'zone': [float(g['lo']), float(g['hi'])], 'pos': pos, 'dist': float(dist), 'state': state,
                   'members': [f"{x['id'][-7:]} {x['trade']} {x['status']}{' held' if x['held'] else ''}{' brk-' + x['break'][0] if x['break'] else ''}" for x in g['m']]})
    order = ['S4_WITHIN_OPPOSING', 'S3_APPROACHING', 'S5_CONFIRMED_REJECTION', 'S6_CONFIRMED_BREAK', 'S7_CONTINUATION', 'S1_ALIGNED']
    state = next((s for s in order if s in cands), 'S2_NEUTRAL')
    return state, zs


def main():
  out = []
  for n, r in enumerate(rows, 1):
      state, zs = assess(r)
      out.append({'n': n, 't': r['opened_utc'], 'ref': r['reference'], 'strategy': r['strategy'], 'family': fam(r['strategy']),
                  'dir': r['direction'], 'entry': float(r['idea_entry']), 'fill': r['fill'], 'stop': float(r['stop_pips']),
                  'pips': r['pips'], 'gbp': r['gbp'], 'by': r['closed_by'], 'auth': bool(r['stp_authorised']),
                  'analyser': (r['analyser'] or {}).get('state'), 'state': state, 'zones': zs,
                  'mfe': r['excursion']['mfe_strict'] if r['excursion']['mfe_strict'] is not None else r['excursion']['mfe_wide'],
                  'mae': r['excursion']['mae_strict'] if r['excursion']['mae_strict'] is not None else r['excursion']['mae_wide']})
  json.dump(out, open(S / 'sca.json', 'w'), indent=1, default=str)
  for x in out:
      z = '; '.join(f"{a['zone'][0]:.1f}-{a['zone'][1]:.1f} {a['pos']}{'' if a['pos'] in ('AT',) else ' ' + format(a['dist'], '.1f')} {a['state'] or '-'} [{', '.join(a['members'])}]"
                    for a in x['zones'] if a['pos'] != 'AHEAD' or a['dist'] < 15)
      print(f"{x['n']:2} {x['t'][5:16]} {x['strategy'][:14]:14} {x['dir']:4} {x['entry']:.1f} {str(x['pips']):>6} {x['by'] or '':5} {x['state']:24} | {z}")


if __name__ == '__main__':
    main()
