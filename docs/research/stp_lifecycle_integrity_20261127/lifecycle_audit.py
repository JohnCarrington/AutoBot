"""Phase 2, STP lifecycle integrity: read-only audit of every STP opportunity against the market and the trading records.

    .venv/bin/python docs/research/stp_lifecycle_integrity_20261127/lifecycle_audit.py <snapshot folder> <output folder>

<snapshot folder> holds COPIES of the production files (nothing in /opt/autobot/data is opened):
    store/                      the GBPUSD candle store (data/candles/GBPUSD)
    planner/                    data/planner/GBPUSD (recommendations.jsonl, issued.jsonl, current.json)
    decisions.jsonl, trades.jsonl, orders.jsonl   data/records/GBPUSD and data/orders/GBPUSD

It uses STP's own rule functions (planner.zones.interacts / wholly_clear, stp.authorise.which_test) and writes only to
<output folder>: lifecycle_audit.json and lifecycle_audit.txt. It never contacts IG and changes nothing.

For each opportunity: creation, identity, zone, primary destination, every lifecycle event, how it ended, whether price
was at the zone at or before creation (the tracker's own "in zone at creation" / "ambiguous" records), the gated ideas
STP authorised against it and the trades that opened from them (with the rejection candle from the trade's own steps),
and, for an ending at the primary destination, which of the four circumstances applied:
    1 destination reached before creation                    (never issued: planner/assess.py D-1; counted from analyses)
    2 after creation, before any zone interaction            ("destination reached before entry" is right)
    3 after a zone interaction, before any trade entry       (interaction counted by the tracker, or only at/before creation)
    4 after a valid trade entry                              (an STP-authorised trade opened from it before the ending)
For each opportunity created with the identity of one that had already ended (a reissue): the predecessor, its ending,
whether the primary destination and its zone are the same, and whether the zone was re-armed (D-25: an hourly candle
wholly clear of it) between the predecessor's creation and the reissue's first authorised rejection candle; a reissue
without a re-arm is the same structural test under a new duplicate key.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, "/opt/autobot")

from config.settings_loader import load_or_exit            # noqa: E402
from planner.zones import interacts, wholly_clear          # noqa: E402
from prices.model import parse_iso                         # noqa: E402
from prices.store import CandleStore                       # noqa: E402
from stp.authorise import which_test                       # noqa: E402

SNAP, OUT = Path(sys.argv[1]), Path(sys.argv[2])
STAGE_B = "2026-11-25T13:10:00Z"           # STP_AUTHORISES_ENTRIES on (deploy-25nov / stp-stage-a-deploy records)
s = load_or_exit().for_pair("GBPUSD")
store = CandleStore(SNAP / "store", 10**6, warn=lambda m: None)


def jl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


events = jl(SNAP / "planner" / "recommendations.jsonl")
issued = {e["id"]: e for e in jl(SNAP / "planner" / "issued.jsonl")}
current = json.loads((SNAP / "planner" / "current.json").read_text())
for o in current.get("opportunities", []):
    issued.setdefault(o["id"], o)
decisions = jl(SNAP / "decisions.jsonl")
trades = jl(SNAP / "trades.jsonl")

by_id: dict[str, list[dict]] = defaultdict(list)
for e in events:
    if e.get("id"):
        by_id[e["id"]].append(e)

ENDS = ("completed", "invalidated", "superseded")
RC = re.compile(r"STP authorised: the rejection candle (.+?) reached the live (BUY|SELL) opportunity (\S+) \((.+?), zone "
                r"([\d.]+)-([\d.]+)\); test (\d+); duplicate key (\S+);")

opened = {t["reference"]: t for t in trades if t.get("event") == "opened"}
closed = {t["reference"]: t for t in trades if t.get("event") == "closed"}
bound_trades: dict[str, list[dict]] = defaultdict(list)
for ref, t in opened.items():
    for step in t.get("steps") or []:
        m = RC.search(step)
        if m:
            c = closed.get(ref) or {}
            bound_trades[m.group(3).rstrip(",")].append({
                "reference": ref, "strategy": t["strategy"], "direction": t["direction"], "opened_utc": t["opened_utc"],
                "rejection_candle": m.group(1), "status_at_authorisation": m.group(4), "test": int(m.group(7)),
                "key": m.group(8), "pips": c.get("pips"), "gbp": c.get("gbp"), "how_closed": c.get("how_closed"),
                "closed_by": c.get("closed_by")})

auths: dict[str, list[dict]] = defaultdict(list)
for d in decisions:
    if d.get("kind") == "STP authorised":
        auths[d["opportunity"]].append({"time_utc": d["time_utc"], "strategy": d["strategy"], "direction": d["direction"],
                                        "signal": d.get("signal")})


def first(evs: list[dict], kind: str) -> dict | None:
    return next((e for e in evs if e["event"] == kind), None)


def rearmed(low: D, high: D, a: str, b: str) -> list[str]:
    out = []
    for c in store.read_range("1h", parse_iso(a), parse_iso(b)):
        if c.start >= parse_iso(a) and c.end <= parse_iso(b) and wholly_clear(s, c, low, high):
            out.append(c.start.strftime("%Y-%m-%dT%H:%MZ"))
    return out


rows = []
for oid, evs in by_id.items():
    cr = first(evs, "created")
    if cr is None or cr["time_utc"] < "2026-11-24T00:00:00Z":
        continue
    rec = issued.get(oid, {})
    z = rec.get("entry_zone") or {}
    end = next((e for e in evs if e["event"] in ENDS), None)
    pre = [e["event"] for e in evs if e["event"] in ("in zone at creation", "ambiguous") and
           ("reached the zone" in e.get("why", "") or e["event"] == "in zone at creation")]
    active = first(evs, "active")
    bt = sorted(bound_trades.get(oid, []), key=lambda x: x["opened_utc"])
    case = None
    if end and ("primary destination" in end.get("why", "") or "destination reached before entry" in end.get("why", "")):
        if bt and bt[0]["opened_utc"] <= end["time_utc"]:
            case = 4
        elif active and active["time_utc"] <= end["time_utc"]:
            case = 3
        elif pre:
            case = 3
        else:
            case = 2
    rows.append({
        "id": oid, "trade": rec.get("trade"), "created_utc": cr["time_utc"], "stage_b": cr["time_utc"] >= STAGE_B,
        "zone": [z.get("low"), z.get("high")], "identity": rec.get("identity"),
        "primary": ((rec.get("destinations") or {}).get("primary") or {}).get("price"),
        "primary_zone": [((rec.get("destinations") or {}).get("primary") or {}).get("zone", {}).get(k) for k in ("low", "high")],
        "zone_at_or_before_creation": pre, "activated_utc": active["time_utc"] if active else None,
        "end": {"status": end["event"].upper(), "time_utc": end["time_utc"], "why": end.get("why")} if end else None,
        "authorisations": auths.get(oid, []), "trades": bt, "destination_case": case,
        "label_says_before_entry": bool(end and "destination reached before entry" in end.get("why", "")),
        "events": [(e["time_utc"], e["event"]) for e in evs]})
rows.sort(key=lambda r: r["created_utc"])

# reissues: the most recent opportunity with the same identity that had ENDED before this one was created
reissues = []
for r in rows:
    prev = [p for p in rows if p["identity"] == r["identity"] and p["end"] and p["end"]["time_utc"] <= r["created_utc"]
            and p["id"] != r["id"]]
    if not prev:
        continue
    p = max(prev, key=lambda x: x["end"]["time_utc"])
    if p["end"]["status"] == "SUPERSEDED":
        continue
    low, high = D(r["zone"][0]), D(r["zone"][1])
    re_arms = rearmed(low, high, p["created_utc"], r["created_utc"])
    pz, rz = p["primary_zone"], r["primary_zone"]
    zone_overlap = None not in (pz + rz) and D(pz[0]) <= D(rz[1]) and D(rz[0]) <= D(pz[1])
    reissues.append({
        "reissue": r["id"], "predecessor": p["id"], "predecessor_end": p["end"],
        "predecessor_trades": [t["reference"] for t in p["trades"]],
        "same_primary_price": p["primary"] == r["primary"], "primary_zones_overlap": zone_overlap,
        "primary": [p["primary"], r["primary"]], "hours_after_end": round(
            (parse_iso(r["created_utc"]) - parse_iso(p["end"]["time_utc"])).total_seconds() / 3600, 2),
        "zone_rearmed_between": re_arms, "reissue_trades": [t["reference"] for t in r["trades"]],
        "duplicate_rule_blocked_it": False})

# parallel lineages: live same-direction opportunities with overlapping zones at each authorisation
def live_at(t: str) -> list[dict]:
    return [r for r in rows if r["created_utc"] <= t and (not r["end"] or r["end"]["time_utc"] > t)]


parallel = []
for r in rows:
    for a in r["authorisations"]:
        others = [o["id"] for o in live_at(a["time_utc"]) if o["id"] != r["id"] and o["trade"] == r["trade"] and
                  D(o["zone"][0]) <= D(r["zone"][1]) and D(r["zone"][0]) <= D(o["zone"][1])]
        if others:
            parallel.append({"time_utc": a["time_utc"], "bound": r["id"], "also_live_same_zone": others})

# D-1 at issue (circumstance 1): analyses whose own primary was already reached, so nothing was issued
c1 = [e["time_utc"] for e in events if e["event"] == "analysis" and e["time_utc"] >= "2026-11-24T00:00:00Z"
      and "already reached" in ((e.get("plan") or {}).get("no_recommendation") or "")]

# the trades' own D-25 test, recomputed with STP's rule, under the bound lineage and under the identity's first lineage
retest = []
for r in rows:
    for t in r["trades"]:
        rc = t["rejection_candle"]
        m = re.match(r"\w+ (\d+) (\w+) (\d\d):(\d\d)", rc)
        rcu = f"2026-11-{int(m.group(1)):02d}T{m.group(3)}:{m.group(4)}:00Z"
        roots = [p for p in rows if p["identity"] == r["identity"] and p["created_utc"] <= r["created_utc"]]
        root = min(roots, key=lambda x: x["created_utc"])
        low, high = D(r["zone"][0]), D(r["zone"][1])
        retest.append({"trade": t["reference"], "bound": r["id"], "key": t["key"], "rejection_candle_utc": rcu,
                       "test_under_bound_lineage": which_test(s, store, low, high, parse_iso(r["created_utc"]), parse_iso(rcu)),
                       "identity_first_lineage": root["id"],
                       "test_under_identity_first_lineage": which_test(s, store, low, high, parse_iso(root["created_utc"]),
                                                                       parse_iso(rcu)),
                       "pips": t["pips"], "how_closed": t["how_closed"]})

out = {"opportunities": rows, "reissues": reissues, "parallel_lineages_at_authorisation": parallel,
       "circumstance_1_not_issued": c1, "trade_tests": retest}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "lifecycle_audit.json").write_text(json.dumps(out, indent=1, default=str))

L = []
L.append(f"STP lifecycle audit: {len(rows)} opportunities created from 24 Nov 2026 (Stage B from {STAGE_B})\n")
L.append("id | trade | created | zone | primary | zone at/before creation | activated | end | case | auths | trades")
for r in rows:
    e = r["end"] or {}
    L.append(f"{r['id'][-13:]} | {r['trade']} | {r['created_utc'][5:16]} | {r['zone'][0]}-{r['zone'][1]} | {r['primary']} | "
             f"{','.join(r['zone_at_or_before_creation']) or '-'} | {(r['activated_utc'] or '-')[5:16]} | "
             f"{e.get('status', 'LIVE')} {e.get('time_utc', '')[5:16]} {(e.get('why') or '')[:60]} | {r['destination_case'] or '-'} | "
             f"{len(r['authorisations'])} | {', '.join(t['reference'] for t in r['trades']) or '-'}")
L.append("\nEndings at the primary destination, by circumstance:")
for k in (2, 3, 4):
    xs = [r for r in rows if r["destination_case"] == k]
    L.append(f"  case {k}: {len(xs)}; of which labelled 'destination reached before entry': "
             f"{sum(r['label_says_before_entry'] for r in xs)}  {[r['id'][-13:] for r in xs]}")
L.append(f"  case 1 (not issued, D-1 at the analysis): {len(c1)} analyses")
L.append("\nReissues of an ended identity:")
for x in reissues:
    L.append(f"  {x['predecessor'][-13:]} ({x['predecessor_end']['status']} {x['predecessor_end']['time_utc'][5:16]}) -> "
             f"{x['reissue'][-13:]} +{x['hours_after_end']}h; primary {x['primary'][0]} -> {x['primary'][1]} "
             f"(same price {x['same_primary_price']}, zones overlap {x['primary_zones_overlap']}); re-armed between: "
             f"{x['zone_rearmed_between'] or 'NO'}; predecessor trades {x['predecessor_trades'] or '-'}; reissue trades "
             f"{x['reissue_trades'] or '-'}")
L.append("\nSTP-authorised trades, D-25 test of the rejection candle:")
for x in retest:
    L.append(f"  {x['trade']} key {x['key']}: rejection {x['rejection_candle_utc'][5:16]}; test under bound lineage "
             f"{x['test_under_bound_lineage']}, under the identity's first lineage {x['identity_first_lineage'][-13:]} "
             f"{x['test_under_identity_first_lineage']}; {x['pips']} pips, {x['how_closed']}")
L.append(f"\nAuthorisations with another live same-direction opportunity at an overlapping zone: {len(parallel)}")
for x in parallel[:40]:
    L.append(f"  {x['time_utc'][5:16]} bound {x['bound'][-13:]}; also live {[i[-13:] for i in x['also_live_same_zone']]}")
(OUT / "lifecycle_audit.txt").write_text("\n".join(L) + "\n")
print("\n".join(L))
