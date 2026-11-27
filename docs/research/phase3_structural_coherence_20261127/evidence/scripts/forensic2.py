"""Phase 3 extended forensic dataset 18-27 Nov 2026 (derived from the Phase 1 forensic.py) (read-only; reads production records, writes only to the scratchpad)."""
import json
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, '/home/autobot/worktrees/autobot-phase3-research')
from config.settings_loader import load_settings
from prices.store import CandleStore
from analyser.indicators import work_out, last_candles

S = Path(sys.argv[1])
ROOT = S / 'data'
UTC = timezone.utc
st_set = load_settings(switches_from=S / 'switches.env').for_pair('GBPUSD')
store = CandleStore(S / 'store' / 'GBPUSD', 10**6, warn=lambda m: None)
PIP = D('10')          # points per pip (prices are in points, 1 pip = 10 points? no: 13124.3 = 1.31243 -> 1 pip = 1 point)
PIP = D('1')
NEAR = D(st_set.rejection.near_level_within_pips)


def P(s):
    return datetime.fromisoformat(s.replace('Z', '+00:00')).astimezone(UTC)


def iso(t):
    return t.astimezone(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')


# ---------------- trades ----------------
trades = {}
for l in open(ROOT / 'records/GBPUSD/trades.jsonl'):
    r = json.loads(l)
    if not ('2026-11-18' <= r['opened_utc'][:10] <= '2026-11-27'):
        continue
    t = trades.setdefault(r['reference'], {})
    if r['event'] == 'opened':
        t.update(open=r)
    else:
        t.update(close=r)
orders = [json.loads(l) for l in open(ROOT / 'orders/GBPUSD/orders.jsonl')]
for ref, t in trades.items():
    t['orders'] = [o for o in orders if o.get('reference') == ref]

# ---------------- STP timeline ----------------
recs = [json.loads(l) for l in open(ROOT / 'planner/GBPUSD/recommendations.jsonl')]
issued = {}
for l in open(ROOT / 'planner/GBPUSD/issued.jsonl'):
    r = json.loads(l)
    issued[r['id']] = r
STATUS = {'created': 'CANDIDATE', 'waiting': 'WAITING', 'active': 'ACTIVE', 'broken': 'BROKEN', 'failed breakout': 'ACTIVE',
          'invalidated': 'INVALIDATED', 'completed': 'COMPLETED', 'superseded': 'SUPERSEDED'}


def stp_at(T):
    """Every opportunity known at time T (events with time <= T), with its status and zone in force."""
    opps = {}
    for r in recs:
        if P(r['time_utc']) > T:
            break
        i = r.get('id')
        if not i:
            continue
        o = opps.setdefault(i, {'id': i, 'status': None, 'events': []})
        ev = r['event']
        if r.get('status') or ev in ('created',):
            o['status'] = r.get('status') or 'CANDIDATE'
            o['status_utc'] = r['time_utc']
            if ev in ('invalidated', 'completed', 'superseded'):
                o['ended_why'] = r.get('why')
            if ev == 'broken':
                o['broken_utc'] = r['time_utc']
        p = r.get('plan')
        if p and p.get('zone') and p['zone'].get('low'):
            o['zone'] = (D(p['zone']['low']), D(p['zone']['high']))
            o['class'] = p['zone']['class']
            o['trade'] = p['trade']
            o['primary'] = D(p['primary']) if p.get('primary') else None
        o['events'].append((r['time_utc'], ev))
    for i, o in opps.items():
        if i in issued:
            o['invalidation'] = issued[i]['invalidation']
            o['primary_zone'] = issued[i]['destinations']['primary']['zone']
            o.setdefault('trade', issued[i]['trade'])
    return opps


def analyses_at(T):
    """The latest hourly analysis per direction at or before T (what STP proposed, opportunity or not)."""
    out = {}
    for r in recs:
        if P(r['time_utc']) > T:
            break
        if r['event'] == 'analysis':
            out[r['plan'].get('trade')] = (r['time_utc'], r['plan'])
    return out


# ---------------- analyser ----------------
states = []
for l in open(ROOT / 'records/GBPUSD/decisions.jsonl'):
    r = json.loads(l)
    if r['kind'] == 'analyser state change' and '2026-11-17' <= r['time_utc'][:10] <= '2026-11-27':
        states.append(r)


def state_at(T):
    s = None
    for r in states:
        if P(r['time_utc']) <= T:
            s = r
    return s


# ---------------- pivots ----------------
def pivots(day):
    prev = day - timedelta(days=1)
    c = store.read_day('1d', prev)[0]
    h, l, cl = c.sell_high, c.sell_low, c.sell_close
    p = (h + l + cl) / 3
    q = lambda x: x.quantize(D('0.1'))
    return {'pivot': q(p), 'R1': q(2 * p - l), 'S1': q(2 * p - h), 'R2': q(p + (h - l)), 'S2': q(p - (h - l)),
            'R3': q(h + 2 * (p - l)), 'S3': q(l - 2 * (h - p))}


def five(start, end):
    return [c for c in store.read_range('5m', start - timedelta(minutes=5), end + timedelta(minutes=5))
            if c.end > start and c.start < end]


def excursion(direction, fill, t_open, t_close):
    """MFE/MAE in pips from 5m bid/ask candles. A buy exits at the sell (bid) price, a sell at the buy (offer) price.
    strict: candles that begin after the entry and end before the close; wide: also the entry and exit candles
    (whose moves may be before the entry / after the exit: candle data cannot tell)."""
    cs = five(t_open, t_close)
    def ex(c):
        if direction == 'buy':
            return c.sell_high - fill, fill - c.sell_low
        return fill - c.buy_low, c.buy_high - fill
    strict = [ex(c) for c in cs if c.start >= t_open and c.end <= t_close]
    wide = [ex(c) for c in cs]
    f = lambda xs, k: (max(x[k] for x in xs) if xs else None)
    return {'mfe_strict': f(strict, 0), 'mae_strict': f(strict, 1), 'mfe_wide': f(wide, 0), 'mae_wide': f(wide, 1),
            'candles': len(cs)}


def ind(T):
    out = {}
    for tf in ('5m', '1h'):
        w = work_out(st_set, store, tf, T)
        v = w.values
        out[tf] = {k: (None if v.get(k) is None else float(v[k])) for k in
                   ('ema_7', 'ema_13', 'ema_21', 'ema_100', 'ema_200', 'bb_upper', 'bb_middle', 'bb_lower', 'macd_histogram', 'rsi')}
        out[tf]['candle'] = iso(w.candle.start) if w.candle else None
        out[tf]['close'] = float(w.candle.sell_close) if w.candle else None
        # previous histogram for momentum direction
        hs = w.series.get('macd') or {}
        keys = sorted(hs)
        if len(keys) >= 2 and hs[keys[-2]] is not None:
            out[tf]['macd_histogram_prev'] = float(hs[keys[-2]].histogram)
    return out


def ema_order(e):
    a, b, c = e['ema_7'], e['ema_13'], e['ema_21']
    if a > b > c:
        return 'up (7>13>21)'
    if a < b < c:
        return 'down (7<13<21)'
    return 'mixed'


def prior_move(direction, T, entry, n=24):
    """Pips already travelled in the trade's direction from the opposite extreme of the last n finished 5m candles
    (2 hours) and from today's opposite extreme (00:00 UTC)."""
    cs = [c for c in last_candles(store, '5m', T, n)]
    day0 = T.replace(hour=0, minute=0, second=0, microsecond=0)
    dc = [c for c in store.read_range('5m', day0, T) if c.end <= T]
    if direction == 'buy':
        lo2 = min(c.sell_low for c in cs)
        lod = min(c.sell_low for c in dc) if dc else None
        return float(entry - lo2), (float(entry - lod) if lod else None)
    hi2 = max(c.sell_high for c in cs)
    hid = max(c.sell_high for c in dc) if dc else None
    return float(hi2 - entry), (float(hid - entry) if hid else None)


rows = []
for ref, t in sorted(trades.items(), key=lambda kv: kv[1]['open']['opened_utc']):
    o, c = t['open'], t.get('close')
    T = P(o['opened_utc'])
    fill = D(o['open_price'])
    direction = o['direction']
    stop = D(o['stop_pips'])
    opps = stp_at(T)
    live = {i: x for i, x in opps.items() if x['status'] in ('WAITING', 'ACTIVE', 'BROKEN')}
    an = analyses_at(T)
    stt = state_at(T)
    ii = ind(T)
    pv = pivots(T.date())
    # STP opportunities by relation to this trade
    want = 'BUY' if direction == 'buy' else 'SELL'
    rel = []
    for i, x in live.items():
        if 'zone' not in x:
            continue
        lo_, hi_ = x['zone']
        side = 'agrees' if x['trade'] == want else 'opposes'
        if direction == 'buy':
            where = 'below' if fill > hi_ else ('inside' if fill >= lo_ else 'above')
            gap = (lo_ - fill) if where == 'above' else ((fill - hi_) if where == 'below' else D(0))
        else:
            where = 'above' if fill < lo_ else ('inside' if fill <= hi_ else 'below')
            gap = (fill - hi_) if where == 'below' else ((lo_ - fill) if where == 'above' else D(0))
        rel.append({'id': x['id'], 'trade': x['trade'], 'status': x['status'], 'zone': [float(lo_), float(hi_)], 'class': x['class'],
                    'primary': None if x.get('primary') is None else float(x['primary']), 'relation': side,
                    'zone_vs_entry': where, 'gap_pips': float(gap), 'broken_utc': x.get('broken_utc'),
                    'zone_break_close': (x.get('invalidation') or {}).get('zone_break_close'),
                    'structure_break_close': (x.get('invalidation') or {}).get('structure_break_close'),
                    'status_utc': x.get('status_utc')})
    # pivot levels ahead (ROOM_TO_LEVEL's set)
    ahead = [(k, v) for k, v in pv.items() if (v >= fill if direction == 'buy' else v <= fill)]
    nearest_pivot = min(ahead, key=lambda kv: abs(kv[1] - fill)) if ahead else None
    exc = excursion(direction, fill, T, P(c['closed_utc']) if c else T + timedelta(hours=2))
    pm2, pmd = prior_move(direction, T, fill)
    e5, e1 = ii['5m'], ii['1h']
    bbw5 = e5['bb_upper'] - e5['bb_lower']
    pctb5 = (float(fill) - e5['bb_lower']) / bbw5 if bbw5 else None
    bbw1 = e1['bb_upper'] - e1['bb_lower']
    pctb1 = (float(fill) - e1['bb_lower']) / bbw1 if bbw1 else None
    stp_steps = [s for s in o.get('steps', []) if s.startswith('STP authorised')]
    rows.append({
        'reference': ref, 'deal_id': o['deal_id'], 'strategy': o['strategy'], 'direction': direction,
        'opened_utc': o['opened_utc'], 'idea_entry': o['entry_price'], 'fill': o['open_price'], 'stop_pips': o['stop_pips'],
        'stop_price': o['stop_price'], 'tp_pips': o['take_profit_pips'], 'reason': o['reason'],
        'closed_utc': c and c['closed_utc'], 'close_price': c and c['close_price'], 'how_closed': c and c['how_closed'],
        'close_reason': c and c['close_reason'], 'pips': c and c['pips'], 'gbp': c and c['gbp'], 'best_pips_record': c and c['best_pips'],
        'closed_by': c and c['closed_by'],
        'ig_close': [{k: x.get(k) for k in ('time_utc', 'event', 'level', 'ig_time_utc', 'ig_channel', 'ig_close_deal_id', 'how')}
                     for x in t['orders'] if x['event'] in ('closed at IG', 'closed')],
        'stop_moves': [(x['time_utc'], x['stop_level']) for x in t['orders'] if x['event'] == 'stop moved'],
        'ig_open': [{k: x.get(k) for k in ('time_utc', 'level', 'stop_level', 'limit_level')} for x in t['orders'] if x['event'] == 'opened'],
        'excursion': {k: (None if v is None else float(v)) for k, v in exc.items()},
        'analyser': stt and {'since': stt['time_utc'], 'state': stt['state'], 'direction': stt['direction'], 'trend_type': stt['trend_type']},
        'market_state_record': o['market_state'],
        'ind5': e5, 'ind1': e1, 'ema5_order': ema_order(e5), 'ema1_order': ema_order(e1),
        'pctb5': pctb5, 'pctb1': pctb1,
        'pivots': {k: float(v) for k, v in pv.items()},
        'nearest_pivot_ahead': nearest_pivot and {'level': nearest_pivot[0], 'price': float(nearest_pivot[1]),
                                                   'pips': float(abs(nearest_pivot[1] - fill))},
        'stp_live': rel,
        'stp_analysis': {k: {'at': v[0], 'zone': (v[1].get('zone') or {}), 'primary': v[1].get('primary'),
                             'condition': v[1].get('condition'), 'no_rec': v[1].get('no_recommendation')} for k, v in an.items()},
        'stp_authorised': stp_steps,
        'prior_move_2h': pm2, 'prior_move_day': pmd,
    })

json.dump(rows, open(S / 'forensic.json', 'w'), indent=1, default=str)
print(len(rows))
