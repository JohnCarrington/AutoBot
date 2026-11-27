"""Markdown tables for the Phase 3 pack from forensic.json + impact.json (read-only)."""
import json, sys
from pathlib import Path
S = Path(sys.argv[1])
F = {r['reference']: r for r in json.load(open(S / 'forensic.json'))}
X = json.load(open(S / 'impact.json'))
NO_IG = {'AB261120184504-582cfcb9','AB261123104201-f64c4f56','AB261124085513-52cc5ffb','AB261124085502-5093fa5b','AB261124133222-f9ca1a29',
         'AB261124153026-da74a808','AB261125170604-a4ec4a37','AB261126063004-aaea24e1','AB261126125133-d1518c12','AB261126114004-bd34fb67',
         'AB261126142255-04805706','AB261127065505-8c11a4bc'}
CORR = {'AB261118123737-487acb12': 'IG 13168.4, -12.0 (record -12.6, R6)', 'AB261126060101-987e099b': 'IG 09:35:01 13108.9, +5.0 (record +4.5, R5)',
        'AB261125180203-7c0f9742': 'IG activity (orphan, booked at start-up 27 Nov)'}
LBL = {'S1': 'S1 aligned', 'S2': 'S2 neutral', 'S3': 'S3 approaching opposing', 'S4': 'S4 within unresolved opposing',
       'S5': 'S5 confirmed rejection', 'S6': 'S6 confirmed break', 'S7': 'S7 continuation after break'}
def evid(ref, f):
    if ref in CORR: return CORR[ref]
    if ref in NO_IG: return 'open IG (deal id); close: bot record, no saved IG evidence'
    return 'IG'
def pipsf(t):
    return t['ig_pips']
def A(rows):
    o = ['| # | Opened UTC | Strategy | Dir | Fill | Stop pips | Closed UTC | How closed | Pips | By | MFE / MAE | Evidence |', '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for t in rows:
        f = F[t['ref']]
        mf = '—' if t['mfe'] is None else f"{float(t['mfe']):.1f} / {float(t['mae']):.1f}"
        o.append(f"| {t['n']} | {t['t'][5:16].replace('T',' ')} | {t['strategy']} | {t['dir'].upper()} | {t['fill']} | {t['stop']:g} | {(f['closed_utc'] or '')[5:16].replace('T',' ')} | {f['how_closed']} | {pipsf(t)} | {'owner' if t['by']=='owner' else 'bot'} | {mf} | {evid(t['ref'], f)} |")
    return '\n'.join(o)
def B(rows):
    o = ['| # | Opened | Strategy | Dir | Analyser | SCA state | Zones at/near the entry (members: id, label, status) | Room R (pips vs stop) | Opposite bot position open |', '|---|---|---|---|---|---|---|---|---|']
    for t in rows:
        zs = [z for z in t['zones'] if z['pos'] != 'AHEAD' or z['dist'] < 15]
        zt = '<br>'.join(f"{z['zone'][0]:.1f}–{z['zone'][1]:.1f} {z['pos'].lower().replace('_',' ')}{'' if z['pos']=='AT' else ' ' + format(abs(z['dist']),'.1f')}: {z['state'] or '—'} ({'; '.join(z['members'])})" for z in zs) or '—'
        rm = '—' if not t['room'] else f"{t['room']['pips']:.1f} vs {t['stop']:g}{' **refuse**' if t['room_refuse'] else ''}{' (R-b: refuse)' if t['room_b_refuse'] else (' (R-b: permit)' if t['room_refuse'] else '')}"
        o.append(f"| {t['n']} | {t['t'][5:16].replace('T',' ')} | {t['strategy']} | {t['dir'].upper()} | {t['analyser']} | **{LBL[t['sca'][:2]]}** | {zt} | {rm} | {', '.join(t['opposite_open']) or '—'} |")
    return '\n'.join(o)
late = [t for t in X if t['t'] >= '2026-11-25']
early = [t for t in X if t['t'] < '2026-11-25']
open(S / 'tables.md', 'w').write('## A1\n' + A(late) + '\n\n## B1\n' + B(late) + '\n\n## A2\n' + A(early) + '\n\n## B2\n' + B(early) + '\n')
print('ok')
