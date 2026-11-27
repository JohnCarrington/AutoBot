"""The historical lineage map (Phase 2, PD-4; owner's approval of 27 November 2026). Deterministic, read-only on
every record, restart-safe:

    .venv/bin/python -m planner.migrate_lineage --pair GBPUSD --as-of <UTC> [--out <file>]   dry run: prints, writes <file>
    .venv/bin/python -m planner.migrate_lineage --pair GBPUSD --as-of <UTC> --apply           writes
                                                    planner.folder/<PAIR>/lineage_map.json (a safe write); the tracker
                                                    applies it once per version of the file (OpportunityKeeper
                                                    _apply_lineage_map)

Why: before the lineage registry existed, every reissue of a structural place got its own id and so its own keys.
On 27 November the same structural test of BUY 13121.3-13131 was keyed 0300-56#t1 (traded at 06:55) and 1200-57#t1
(traded at 12:01), and 1305-58 is live with its own id. The new tracker counts tests per lineage, so after deployment
that test is <lineage>#t1, and the old keys must stay consumed. This builds, from the recorded history only:

  1. every opportunity since --since (default 24 November 2026): id, direction, creation, zone (as issued, then each
     recorded "zone edges A-B to C-D" change), identity, primary destination and its zone, ending; "supersedes" from
     its creation record;
  2. lineages, by exactly the tracker's own rule (planner/opportunities.py _lineage_for): a supersession keeps its
     lineage; otherwise the oldest lineage of a live opportunity of the same direction with the same identity or an
     overlapping zone (more than a shared edge); otherwise the most recently ended one; otherwise a new lineage. Zones
     are compared member by member, never through a chain;
  3. each lineage's D-25 / P-C8 count (planner/lineage.py, the tracker's own counting): seeded at its first member's
     creation, then every finished hourly candle while one of its members was tracked, and the hours it was not
     tracked counted when a member rejoins;
  4. every key already CONSUMED by a trade (the order journal: opened or adopted orders and their signal; an order
     sent and never settled counts too): for an STP key <id>#t<k>, the test m of the rejection candle under the
     lineage of <id> (planner/lineage.py test_number). If <lineage>#t<m> differs from the old key, the old key becomes
     an ALIAS of test m: the authorisation check adds it to every idea in that test, so rule 11 refuses them. The
     rejection candle is read from the trade's own entry steps (the "STP authorised: the rejection candle ..." line;
     trades.jsonl opened row, or the order's recovery steps). No financial figure is read. Without a rejection candle
     the key is reported as AMBIGUOUS and nothing is guessed;
  5. the lineage of every live opportunity (current.json).
Nothing is merged without one of those rules; the evidence for each alias (the hourly candles between, their D-25
verdicts) is written into the map. The order journal, the trade records and the planner's journal are never changed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from planner.keeper import COMPLETED
from planner.lineage import count_gap, count_hour, new_tests, seed_tests, test_number, zones_overlap
from prices.model import parse_iso

UTC = timezone.utc
KEY = re.compile(r"^(STP-[A-Z]{6}-\d{8}-\d{4}-\d+)#t(\d+)$")
RC = re.compile(r"STP authorised: the rejection candle (\w+ \d+ \w+ \d\d:\d\d)")
CHANGED = re.compile(r"zone edges ([\d.]+)-([\d.]+) to ([\d.]+)-([\d.]+)")
SUPERSEDES = re.compile(r"^supersedes (STP-\S+?):")
MONTHS = {m: i for i, m in enumerate(("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov",
                                      "Dec"), start=1)}


def _jl(p: Path) -> list[dict]:
    try:
        return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
    except FileNotFoundError:
        return []


def _iso(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def _uk_short_to_utc(text: str, year: int) -> datetime:
    """'Fri 27 Nov 11:40' (uk_short of a UTC candle start in GMT; this history is all in GMT, UTC+0)."""
    _, d, mon, hm = text.split()
    h, m = hm.split(":")
    return datetime(year, MONTHS[mon], int(d), int(h), int(m), tzinfo=UTC)


def history(planner_dir: Path, since: str) -> list[dict]:
    events = _jl(planner_dir / "recommendations.jsonl")
    issued = {r["id"]: r for r in _jl(planner_dir / "issued.jsonl")}
    try:
        cur = json.loads((planner_dir / "current.json").read_text())
    except (OSError, ValueError):
        cur = {}
    live = {o["id"]: o for o in cur.get("opportunities") or []}
    ops: dict[str, dict] = {}
    for e in events:
        oid = e.get("id")
        if not oid:
            continue
        if e["event"] == "created" and e["time_utc"] >= since and oid in issued:
            r = issued[oid]
            pr = (r.get("destinations") or {}).get("primary") or {}
            sup = SUPERSEDES.match(e.get("why") or "")
            ops[oid] = {"id": oid, "trade": r["trade"], "created_utc": r["created_utc"], "identity": r["identity"],
                        "zone": {"low": r["entry_zone"]["low"], "high": r["entry_zone"]["high"]},
                        "zones": [[r["created_utc"], r["entry_zone"]["low"], r["entry_zone"]["high"]]],
                        "primary": pr.get("price"),
                        "primary_zone": {"low": pr["zone"]["low"], "high": pr["zone"]["high"]} if pr.get("zone") else None,
                        "supersedes": sup.group(1) if sup else None, "ended_utc": None, "status": None}
        elif oid in ops:
            o = ops[oid]
            if e["event"] == "changed":
                m = CHANGED.search(e.get("why") or "")
                if m:
                    o["zone"] = {"low": m.group(3), "high": m.group(4)}
                    o["zones"].append([e["time_utc"], m.group(3), m.group(4)])
            elif e["event"] in ("completed", "invalidated", "superseded"):
                o["ended_utc"], o["status"], o["ended_why"] = e["time_utc"], e["event"].upper(), e.get("why") or ""
    for oid, o in ops.items():
        if oid in live:
            z = live[oid]["entry_zone"]
            o["zone"] = {"low": z["low"], "high": z["high"]}
            o["ended_utc"], o["status"] = None, None
    return sorted(ops.values(), key=lambda o: (o["created_utc"], o["id"]))


def zone_at(o: dict, t: str) -> dict:
    z = o["zones"][0]
    for x in o["zones"]:
        if x[0] <= t:
            z = x
    return {"low": z[1], "high": z[2]}


def assign(ops: list[dict]) -> dict[str, str]:
    """The tracker's own lineage rule (OpportunityKeeper._lineage_for and _belongs), replayed in creation order
    (retirements at a re-plan come before its creations). A recorded supersession keeps its lineage only for the same
    identity (the tracker's rule since STP_OPPORTUNITIES; before it, the single tracker superseded on ANY zone change,
    which is not the same structural place)."""
    lin: dict[str, str] = {}
    first: dict[str, str] = {}
    home: dict[str, dict] = {}
    byid = {o["id"]: o for o in ops}

    def belongs(p: dict, o: dict, pz: dict) -> bool:
        if p["identity"] == o["identity"]:
            return True
        return zones_overlap(pz, o["zone"]) and zones_overlap(home[lin[p["id"]]], o["zone"])

    for o in ops:
        t = o["created_utc"]
        sup = byid.get(o["supersedes"]) if o["supersedes"] else None
        if sup is not None and sup["id"] in lin and sup["identity"] == o["identity"]:
            lin[o["id"]] = lin[sup["id"]]
            continue
        live = [p for p in ops if p["id"] in lin and p["trade"] == o["trade"] and p["created_utc"] < t and
                (p["ended_utc"] is None or p["ended_utc"] > t) and belongs(p, o, zone_at(p, t))]
        if live:
            lin[o["id"]] = min((lin[p["id"]] for p in live), key=lambda L: (first[L], L))
            continue
        ended = [p for p in ops if p["id"] in lin and p["trade"] == o["trade"] and p["ended_utc"] and
                 p["ended_utc"] <= t and belongs(p, o, zone_at(p, p["ended_utc"]))]
        if ended:
            lin[o["id"]] = lin[max(ended, key=lambda p: (p["ended_utc"], p["id"]))["id"]]
            continue
        lin[o["id"]] = o["id"]
        first[o["id"]] = o["created_utc"]
        home[o["id"]] = zone_at(o, t)
    return lin


def tracked_at_hour_end(m: dict, te: str) -> bool:
    """Whether the tracker counted the hour ending at te for this member: its run handles the 5-minute candles first
    (a destination reached in the hour's last candle ends it before the hour is counted), then the hourly candle (a
    confirmed break held ends it after the hour is counted), then the re-plan (after)."""
    if m["ended_utc"] is None or m["ended_utc"] > te:
        return True
    return m["ended_utc"] == te and "confirmed break held" in (m.get("ended_why") or "")


def count(settings: Any, store: Any, ops: list[dict], lin: dict[str, str], as_of: datetime) -> dict[str, dict]:
    """Each lineage's D-25 count, as the tracker would hold it at as_of."""
    out: dict[str, dict] = {}
    by_l: dict[str, list[dict]] = {}
    for o in ops:
        by_l.setdefault(lin[o["id"]], []).append(o)
    for L, members in sorted(by_l.items()):
        root = members[0]
        z = zone_at(root, root["created_utc"])
        t0 = parse_iso(root["created_utc"])
        tests = seed_tests(settings, store, z["low"], z["high"], t0)
        hour = t0.replace(minute=0, second=0, microsecond=0)
        hours = [c for c in store.read_range("1h", hour, as_of) if c.start >= hour and c.end <= as_of]
        for c in hours:
            te = _iso(c.end)
            tracked = [m for m in members if m["created_utc"] < te and tracked_at_hour_end(m, te)]
            if not tracked:
                continue
            ref = min(tracked, key=lambda m: (m["created_utc"], m["id"]))
            if tests.get("through_utc") and parse_iso(tests["through_utc"]) < c.start:
                zr = zone_at(ref, ref["created_utc"])
                count_gap(settings, store, tests, zr["low"], zr["high"], c.start)       # hours nobody tracked it
            zr = zone_at(ref, te)
            count_hour(settings, tests, c, Decimal(zr["low"]), Decimal(zr["high"]))
        out[L] = tests
    return out


def consumed_keys(orders_dir: Path, records_dir: Path) -> list[dict]:
    """Every STP key part used by an order the bot opened (opened or adopted) or sent and never settled."""
    rows = _jl(orders_dir / "orders.jsonl")
    sending = {r["reference"]: r for r in rows if r.get("event") == "sending"}
    opened = {r["reference"] for r in rows if r.get("event") in ("opened", "adopted")}
    settled = {r["reference"] for r in rows if r.get("event") in ("opened", "adopted", "refused", "not placed",
                                                                  "not placed at IG", "rejected")}
    steps: dict[str, list[str]] = {}
    for t in _jl(records_dir / "trades.jsonl"):
        if t.get("event") == "opened":
            steps[t["reference"]] = list(t.get("steps") or [])
    out = []
    for ref, snd in sorted(sending.items()):
        sig = snd.get("signal") or ""
        if not sig or not (ref in opened or ref not in settled):
            continue
        st = steps.get(ref) or list((snd.get("recovery") or {}).get("steps") or [])
        rc = None
        for s in st:
            m = RC.search(s)
            if m:
                rc = _uk_short_to_utc(m.group(1), int(snd["time_utc"][:4]))
        for part in sig.split("|"):
            m = KEY.match(part)
            if m:
                out.append({"key": part, "opportunity": m.group(1), "test": int(m.group(2)), "reference": ref,
                            "state": "opened" if ref in opened else "sent, not settled",
                            "rejection_candle": _iso(rc) if rc else None})
    return out


def build(settings: Any, store: Any, planner_dir: Path, orders_dir: Path, records_dir: Path, as_of: datetime,
          since: str = "2026-11-24T00:00:00Z") -> dict:
    ops = history(planner_dir, since)
    lin = assign(ops)
    tests = count(settings, store, ops, lin, as_of)
    byid = {o["id"]: o for o in ops}
    lineages: dict[str, dict] = {}
    for o in ops:
        L = lineages.setdefault(lin[o["id"]], {"trade": o["trade"], "created_utc": byid[lin[o["id"]]]["created_utc"],
                                              "home_zone": zone_at(byid[lin[o["id"]]], byid[lin[o["id"]]]["created_utc"]),
                                              "members": [], "aliases": {}, "consumed": {}, "evidence": []})
        L["members"].append({"id": o["id"], "identity": o["identity"], "zone": o["zone"], "primary": o["primary"],
                             "primary_zone": o["primary_zone"], "created_utc": o["created_utc"],
                             "ended_utc": o["ended_utc"], "status": o["status"], "effective_status": o["status"]})
    for L, rec in lineages.items():
        rec["tests"] = tests.get(L) or new_tests()
    ambiguous = []
    for k in consumed_keys(orders_dir, records_dir):
        o = byid.get(k["opportunity"])
        if o is None:
            ambiguous.append(k | {"why": "its opportunity is not in the planner's history"})
            continue
        L = lin[o["id"]]
        if not k["rejection_candle"]:
            ambiguous.append(k | {"why": "no rejection candle in the trade's own steps: its test cannot be established"})
            continue
        z = zone_at(o, k["rejection_candle"])
        m = test_number(settings, store, z["low"], z["high"], lineages[L]["tests"], parse_iso(k["rejection_candle"]))
        lk = f"{L}#t{m}"
        rec = lineages[L]
        rec["consumed"].setdefault(str(m), [])
        if k["reference"] not in rec["consumed"][str(m)]:
            rec["consumed"][str(m)].append(k["reference"])
        if k["key"] != lk:
            have = rec["aliases"].setdefault(str(m), [])
            if k["key"] not in have:
                have.append(k["key"])
        rc_hour = parse_iso(k["rejection_candle"]).replace(minute=0)
        rec["evidence"].append({"key": k["key"], "reference": k["reference"], "state": k["state"],
                                "rejection_candle": k["rejection_candle"], "lineage_key": lk,
                                "alias": k["key"] != lk,
                                "lineage_tests_before_the_rejection_hour": [e for e in rec["tests"]["events"]
                                                                            if parse_iso(e[0]) < rc_hour]})
    for rec in lineages.values():
        for n in rec["aliases"]:
            rec["aliases"][n].sort()
        for n in rec["consumed"]:
            rec["consumed"][n].sort()
        rec["evidence"].sort(key=lambda e: (e["rejection_candle"], e["key"]))
    try:
        cur = json.loads((planner_dir / "current.json").read_text())
    except (OSError, ValueError):
        cur = {}
    live = sorted(o["id"] for o in cur.get("opportunities") or [])
    return {"version": 1, "as_of_utc": _iso(as_of), "since_utc": since,
            "rule": "planner/migrate_lineage.py (the tracker's own lineage and D-25 rules, replayed)",
            "lineages": dict(sorted(lineages.items())),
            "opportunity_lineage": {oid: lin[oid] for oid in live if oid in lin},
            "ambiguous": ambiguous}


def main(argv: list[str] | None = None) -> int:
    from config.settings_loader import load_or_exit
    from housekeeping.files import safe_write
    from prices.store import CandleStore
    ap = argparse.ArgumentParser(prog="python -m planner.migrate_lineage")
    ap.add_argument("--pair", required=True)
    ap.add_argument("--as-of", required=True, help="the UTC time the map is built for (its hourly counts end there)")
    ap.add_argument("--since", default="2026-11-24T00:00:00Z")
    ap.add_argument("--out", help="dry run: write the map here instead")
    ap.add_argument("--apply", action="store_true", help="write planner.folder/<PAIR>/lineage_map.json")
    a = ap.parse_args(argv)
    s = load_or_exit().for_pair(a.pair.upper())
    store = CandleStore(s.candles.folder, s.candles.compress_after_days)
    pdir = Path(s.planner.folder) / s.market.pair
    m = build(s, store, pdir, Path(s.orders.folder) / s.market.pair, Path(s.records.folder) / s.market.pair,
              parse_iso(a.as_of), a.since)
    text = json.dumps(m, indent=1, sort_keys=True) + "\n"
    for L, rec in m["lineages"].items():
        if rec["aliases"] or rec["consumed"] or len(rec["members"]) > 1:
            print(f"{L} {rec['trade']}: members {', '.join(x['id'][-8:] for x in rec['members'])}; consumed "
                  f"{rec['consumed'] or '-'}; aliases {rec['aliases'] or '-'}")
    print(f"live: {m['opportunity_lineage']}")
    print(f"ambiguous: {m['ambiguous'] or 'none'}")
    if a.apply:
        safe_write(pdir / "lineage_map.json", text.encode())
        print(f"written {pdir / 'lineage_map.json'}")
    elif a.out:
        Path(a.out).write_text(text)
        print(f"dry run written to {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
