"""STP opportunities (switch STP_OPPORTUNITIES; owner, 24 November 2026; docs/design/STP_STRATEGY_INTEGRATION_20261124.md
sections 6 and 11; OD-01, OD-02, OD-06, OD-13, OD-16, OD-17, OD-31). OBSERVE ONLY by itself: nothing here opens,
refuses, changes or closes a trade. The authorisation check (stp/authorise.py) only reads what is written here.

The planner's tracker (planner/keeper.py) with several opportunities instead of one. Every rule is the tracker's
own, reused; only these change:
  * several opportunities may be live at once (OD-01, D-23 amended): each hourly re-plan's proposal (one per
    direction while STP_BIDIRECTIONAL is on, OD-17) is ADDED unless an opportunity with the same identity (trade +
    fixed levels, FC-05) is already live; then it is updated in place when the zones overlap ("supported"/"changed"),
    or SUPERSEDED by the new one (which keeps its lineage and so its duplicate keys) when they no longer overlap;
  * a new forecast never ends an opportunity (OD-02, H11): no invalidation because the re-plan chose another zone,
    recommended nothing, or because the 4-hour direction or condition changed (OD-06);
  * Watch & Wait (the tracker's ACTIVE) is never demoted back to WAITING when price moves clear (H18);
  * a confirmed break (D-20: an hourly close at least planner.break_beyond_pips beyond the far edge) makes it BROKEN,
    which authorises nothing; the first hourly close back inside the far edge within
    planner.failed_breakout_within_candles (P-F7, 3) closes restores Watch & Wait at that close (OD-07, OD-31); if the
    break holds through them it is INVALIDATED;
  * a 4-hour close at or beyond the plan's own structure_break_close invalidates it (ARCH 10.2; the single tracker
    relied on the direction change for this);
  * at the 00:00 UK re-plan (also the week's first), an opportunity whose daily or weekly fixed levels are no longer in
    the level map is INVALIDATED "structural levels changed" (OD-13, D-21);
  * no time expiry anywhere (H16);
  * review, 25 November 2026: while BROKEN the single tracker's destination check still runs on every 5-minute candle
    (not its zone activation), so a destination reached while BROKEN ends it before any reclaim; and the tracker keeps
    each opportunity's D-25 tests ("tests": every finished hourly candle counted once, against the zone in force at
    that hour; a successor inherits them), which stp.authorise.which_test reads for the duplicate key.
Statuses: WAITING and ACTIVE ("Watch & Wait") authorise; BROKEN is tracked but does not; COMPLETED, INVALIDATED and
SUPERSEDED end it.

Files: the tracker's own, in planner.folder/<PAIR>/. current.json gains "opportunities" (the tracked list) and keeps
"recommendation" as a copy of the newest live opportunity, so the dashboard and, after a switch-off, the single
tracker read it as before. recommendations.jsonl and issued.jsonl as before (every event carries its id).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from planner.keeper import (ACTIVE, AFTER_TRADE, BEFORE, COMPLETED, EVENT_BASIS, INVALIDATED, LIVE, SUPERSEDED, UTC,
                            WAITING, Keeper, _d, _iso, destination_end, identity, overlaps, summary)
from planner.gaps import filled, missing_fives
from planner.lineage import complete, count_gap, count_hour, new_tests, seed_tests, zones_overlap
from planner.measure import cl, freshness, hi, lo, ppp, side_of
from planner.zones import interacts, wholly_clear
from prices.model import UK, parse_iso, plain, uk_short

BROKEN = "BROKEN"
TRACKED = (WAITING, ACTIVE, BROKEN)
AUTHORISING = LIVE                      # WAITING and ACTIVE (Watch & Wait)
WATCH_AND_WAIT = "Watch & Wait"         # the label shown for ACTIVE (OD-11)


def label(status: str) -> str:
    return WATCH_AND_WAIT if status == ACTIVE else status.capitalize() if status else status


def _key(ident: list) -> str:
    return json.dumps(ident)


def _copy(x: Any) -> Any:
    return json.loads(json.dumps(x))


def _primary(rec: dict) -> tuple[Any, dict | None]:
    pr = (rec.get("destinations") or {}).get("primary") or {}
    return pr.get("price"), pr.get("zone")


def member(rec: dict) -> dict:
    """What a lineage keeps of each of its opportunities (Phase 2 WP1): enough to match a later proposal against it
    (identity, entry zone) and to apply the completed-opportunity duplicate rule (primary destination and its zone)."""
    price, zone = _primary(rec)
    return {"id": rec["id"], "identity": rec.get("identity"),
            "zone": {"low": rec["entry_zone"]["low"], "high": rec["entry_zone"]["high"]},
            "primary": price, "primary_zone": {"low": zone["low"], "high": zone["high"]} if zone else None,
            "created_utc": rec.get("created_utc"), "ended_utc": None, "status": None, "effective_status": None}


LINEAGE_MAP = "lineage_map.json"
# The execution side's acknowledgement file (orders/executions.py FILE; the file format is the one-way interface: STP
# reads it here and never imports execution code, tests/functional/test_stp_final_validation_20261120.py test_10)
ACKS_FILE = "stp_executions.jsonl"


def read_acks(path: Path) -> list[dict]:
    """Every acknowledgement, once per reference, in file order; a damaged (torn) last line is skipped."""
    out, seen = [], set()
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return []
    for x in lines:
        try:
            a = json.loads(x)
        except ValueError:
            continue
        if isinstance(a, dict) and a.get("reference") and a["reference"] not in seen:
            seen.add(a["reference"])
            out.append(a)
    return out


class OpportunityKeeper(Keeper):
    """The tracker with several opportunities (see the module text). The single tracker's per-recommendation methods
    (five_minute, _new, _update_from, _event) are reused unchanged: each is called with the opportunity in hand put in
    the tracker's one slot, state["recommendation"], for the length of the call."""

    def __init__(self, settings: Any, store: Any, planner: Any = None, calendar: list | None = None):
        super().__init__(settings, store, planner, calendar)
        self.bidirectional = bool(getattr(getattr(settings, "switches", None), "stp_bidirectional", False))

    # ---- state ------------------------------------------------------------------------------------------------------

    def _load(self) -> dict:
        st = super()._load()
        if "opportunities" not in st:                   # first run after the switch-on: the single tracker's one
            rec = st.get("recommendation")
            st["opportunities"] = [rec] if rec is not None and rec.get("status") in LIVE else []
            for r in st["opportunities"]:
                r.setdefault("lineage", r["id"])
                r.setdefault("lineage_created_utc", r.get("created_utc"))
        st["recommendation"] = None                     # the slot; the saved copy is only for other readers
        st.setdefault("ended_by_identity", {})
        # Phase 2 WP1: the lineage registry. A file written before it existed: one lineage per live lineage id, with
        # the tests its opportunities already carried
        lins = st.setdefault("lineages", {})
        for r in st["opportunities"]:
            lid = r.setdefault("lineage", r["id"])
            L = lins.setdefault(lid, {"id": lid, "trade": r["trade"],
                                      "home_zone": {"low": r["entry_zone"]["low"], "high": r["entry_zone"]["high"]},
                                      "created_utc": r.get("lineage_created_utc") or r.get("created_utc"),
                                      "tests": _copy(r.get("tests")) if r.get("tests") else new_tests(),
                                      "members": [], "aliases": {}, "consumed": {}})
            if r["id"] not in {m["id"] for m in L["members"]}:
                L["members"].append(member(r))
        return st

    @property
    def opportunities(self) -> list[dict]:
        return self.state["opportunities"]

    @property
    def lineages(self) -> dict:
        return self.state["lineages"]

    def _save(self, now: datetime) -> None:
        for r in self.opportunities:                    # each opportunity shows its lineage's tests (readers of old)
            L = self.lineages.get(r.get("lineage"))
            if L is not None:
                r["tests"] = _copy(L["tests"])
                r["lineage_created_utc"] = L["created_utc"]
        live = [r for r in self.opportunities if r["status"] in AUTHORISING]
        self.state["recommendation"] = max(live, key=lambda r: r["created_utc"]) if live else None
        self.state["mode"] = "opportunities"
        try:
            super()._save(now)
        finally:
            self.state["recommendation"] = None

    @contextmanager
    def _slot(self, rec: dict | None):
        before = self.state["recommendation"]
        self.state["recommendation"] = rec
        try:
            yield
        finally:
            self.state["recommendation"] = before

    # ---- ending and duplicates (the single tracker's, per opportunity) ----------------------------------------------

    def _retire(self, t: datetime, status: str, why: str, evidence: dict | None = None) -> None:
        rec = self.state["recommendation"]
        rec["status"], rec["status_reason"], rec["ended_utc"] = status, why, _iso(t)
        self._event(t, status.lower(), why, status=status, **(evidence or {}))
        self.state["recent"] = ([{"id": rec["id"], "trade": rec["trade"], "zone": [rec["entry_zone"]["low"], rec["entry_zone"]["high"]],
                                  "status": status, "why": why, "created_utc": rec["created_utc"], "ended_utc": rec["ended_utc"]}]
                                + self.state.get("recent", []))[: self.s.planner.panel_history]
        ended = {"id": rec["id"], "status": status, "identity": rec["identity"],
                 "primary": (rec.get("destinations") or {}).get("primary", {}).get("price")}
        self.state["last_ended"] = ended
        self.state["ended_by_identity"][_key(rec["identity"])] = ended
        L = self.lineages.get(rec.get("lineage"))
        if L is not None:
            for m in L["members"]:
                if m["id"] == rec["id"]:
                    if rec.get("data_gaps"):
                        m["data_gaps"] = _copy([g for g in rec["data_gaps"] if g.get("status") != "reconciled"])
                        m["activated"] = bool(rec.get("ever_active"))
                        m["trade"], m["entry_zone_full"] = rec["trade"], _copy(rec["entry_zone"])
                    price, pzone = _primary(rec)        # review R2: the destination as it stood at the end
                    m.update(primary=price, primary_zone={"low": pzone["low"], "high": pzone["high"]} if pzone else None)
                    m.update(ended_utc=rec["ended_utc"], status=status, effective_status=status,
                             zone={"low": rec["entry_zone"]["low"], "high": rec["entry_zone"]["high"]},
                             destination_case=(evidence or {}).get("destination_case"),
                             destination_candle_end_utc=(evidence or {}).get("candle_end_utc") or rec["ended_utc"]
                             if (evidence or {}).get("destination_case") else None)
        self.state["opportunities"] = [r for r in self.opportunities if r is not rec]
        self.state["recommendation"] = None

    def _end(self, rec: dict, t: datetime, status: str, why: str, evidence: dict | None = None) -> None:
        with self._slot(rec):
            self._retire(t, status, why, evidence)

    def _note(self, rec: dict, t: datetime, kind: str, why: str, **more: Any) -> None:
        with self._slot(rec):
            self._event(t, kind, why, **more)

    @staticmethod
    def _belongs(L: dict, ident: Any, z: dict, m_ident: Any, m_zone: dict | None) -> bool:
        """A proposal (identity, zone) matches a lineage member: the same identity (the same fixed levels, FC-05), or
        a zone overlapping BOTH that member's zone and the lineage's home zone (the zone of its first opportunity), so a
        chain of overlaps can never carry a lineage to a place its first opportunity did not overlap (PD-3)."""
        if m_ident == ident:
            return True
        home = L.get("home_zone") or m_zone
        return zones_overlap(m_zone, z) and zones_overlap(home, z)

    def _ended_match(self, p: dict, lineage_rule: bool = True) -> tuple[dict | None, dict | None]:
        """The most recently ended opportunity of the same direction whose identity is the proposal's or whose entry
        zone overlaps it directly (never through a chain of zones), and its lineage. lineage_rule: also the lineage's
        home zone (for joining a lineage); without it, the member alone (the duplicate rule compares pairwise)."""
        ident, z = identity(p), p.get("entry_zone")
        best, best_l = None, None
        for L in self.lineages.values():
            if L.get("trade") != p.get("trade"):
                continue
            for m in L.get("members", []):
                ok_ = self._belongs(L, ident, z, m.get("identity"), m.get("zone")) if lineage_rule else \
                    (m.get("identity") == ident or zones_overlap(m.get("zone"), z))
                if m.get("ended_utc") and ok_:
                    if best is None or m["ended_utc"] > best["ended_utc"]:
                        best, best_l = m, L
        return best, best_l

    def _duplicate_of(self, p: dict) -> str | None:
        """The completed-opportunity duplicate rule (FC-05, D-1; owner 19 November 2026), with PD-2 (owner 27 November
        2026): the most recently ended opportunity of the same direction with the proposal's identity or an entry zone
        overlapping it COMPLETED (or reached its destination after a confirmed trade entry), and the proposal's primary
        destination is the same price or its zone overlaps the ACHIEVED one's zone (compared with that zone only, so a
        progressively shifting destination never chains). Without such a record, the single tracker's rule per identity."""
        price, pzone = _primary(p)
        m, _ = self._ended_match(p, lineage_rule=False)
        if m is not None:
            if m.get("effective_status") != COMPLETED:
                return None
            if (price is not None and m.get("primary") is not None and _d(price) == _d(m["primary"])) or \
                    zones_overlap(m.get("primary_zone"), pzone):
                return m["id"]
            # review R2: an achieved destination whose zone was not recorded (a revision in the historical map):
            # the proposal's destination zone containing the achieved price
            if m.get("primary_zone") is None and m.get("primary") is not None and pzone and \
                    _d(pzone["low"]) <= _d(m["primary"]) <= _d(pzone["high"]):
                return m["id"]
            return None
        le = self.state["ended_by_identity"].get(_key(identity(p)))
        if not le or le.get("status") != COMPLETED or le.get("primary") is None:
            return None
        primary = ((p.get("destinations") or {}).get("primary") or {}).get("price")
        if primary is not None and _d(primary) == _d(le["primary"]):
            return le["id"]
        return None

    def _lineage_for(self, p: dict) -> tuple[dict | None, str, list[str]]:
        """Phase 2 WP1 (C-2, C-4, PD-3): the lineage a new proposal joins. A LIVE (tracked) opportunity of the same
        direction with its identity or an overlapping zone (more than a shared edge): the oldest such lineage. Else the
        most recently ENDED one (completion, invalidation, a confirmed break held, the rollover). Else none (a new
        lineage). Returns (lineage, how, the other lineages that also matched)."""
        ident, z = identity(p), p["entry_zone"]
        live = [r for r in self.opportunities if r["trade"] == p["trade"] and r["status"] in TRACKED and
                self._belongs(self.lineages.get(r["lineage"], {}), ident, z, r["identity"], r["entry_zone"])]
        lids = []
        for r in sorted(live, key=lambda r: (self.lineages.get(r["lineage"], {}).get("created_utc") or "", r["id"])):
            if r["lineage"] not in lids:
                lids.append(r["lineage"])
        if lids and lids[0] in self.lineages:
            return self.lineages[lids[0]], "live", lids[1:]
        m, L = self._ended_match(p)
        if L is not None:
            return L, f"ended ({m['id']}, {m.get('status')})", []
        return None, "new", []

    def _new_opp(self, t: datetime, plan: dict, why: str, inherit: dict | None = None) -> dict:
        with self._slot(None):
            self._new(t, plan, why)
            rec = self.state["recommendation"]
        low, high = rec["entry_zone"]["low"], rec["entry_zone"]["high"]
        how, others, gap = "supersedes", [], []
        if inherit:
            L = self.lineages.get(inherit["lineage"])
            rec["ever_active"] = bool(inherit.get("ever_active"))
            rec["supersedes"] = inherit["id"]
        else:
            L, how, others = self._lineage_for(plan)
        if L is None:                                   # a new structural place: its D-25 count seeded (C-2)
            L = {"id": rec["id"], "trade": rec["trade"], "created_utc": rec["created_utc"],
                 "home_zone": {"low": low, "high": high},
                 "tests": seed_tests(self.s, self.store, low, high, t), "members": [], "aliases": {}, "consumed": {}}
            self.lineages[L["id"]] = L
        elif not any(m.get("ended_utc") is None for m in L["members"]):
            gap = count_gap(self.s, self.store, L["tests"], low, high, t)   # the hours nobody tracked it
        rec["lineage"], rec["lineage_created_utc"] = L["id"], L["created_utc"]
        rec["tests"] = _copy(L["tests"])
        ev_ = L["tests"].get("events") or []
        hour = t.replace(minute=0, second=0, microsecond=0)
        if ev_ and ev_[-1][1] == "test" and parse_iso(ev_[-1][0]) < hour:     # a D-25 test already in progress
            rec["zone_before_creation"] = {"basis": f"the D-25 test in progress since the {ev_[-1][0]} hourly candle"}
        L["members"].append(member(rec))
        if L["id"] != rec["id"] and not inherit:
            with self._slot(rec):
                self._event(t, "lineage", f"continues the structural lineage {L['id']} ({how}): the same place in the "
                            f"same direction, so its duplicate keys and D-25 test count carry on (Phase 2, C-2/PD-3)"
                            + (f"; hours counted since it was last tracked: {', '.join(gap)}" if gap else "")
                            + (f"; also overlaps {', '.join(others)}" if others else ""),
                            lineage=L["id"], how=how)
        if plan.get("relation_to_h4") is not None:
            rec["relation_to_h4"] = plan["relation_to_h4"]
        self.opportunities.append(rec)
        return rec

    # ---- missing market data (WP3, PD-5 A+B+C; planner/gaps.py) -------------------------------------------------------

    def _record_gaps(self, since: datetime, now: datetime) -> None:
        """A: the expected 5-minute candles (market hours only) from the last step to now that the store does not
        hold, recorded on every tracked opportunity that existed during them."""
        from prices.calendar import floor_5m
        for a, b in missing_fives(self.s, self.store, since, floor_5m(now)):
            for rec in self.opportunities:
                if rec["status"] not in TRACKED or parse_iso(rec["created_utc"]) >= b:
                    continue
                gaps = rec.setdefault("data_gaps", [])
                if any(g["from_utc"] == _iso(a) and g["to_utc"] == _iso(b) for g in gaps):
                    continue
                run_on = next((g for g in gaps if g["status"] == "open" and g["to_utc"] == _iso(a)), None)
                if run_on is not None:                  # the same outage, seen over several steps: one interval
                    run_on["to_utc"] = _iso(b)
                    continue
                gaps.append({"from_utc": _iso(a), "to_utc": _iso(b), "found_utc": _iso(now), "status": "open"})
                self._note(rec, now, "data gap", f"no 5-minute candles stored from {uk_short(a)} to {uk_short(b)} while "
                           f"the market was open: what price did then is unknown to STP, so this opportunity "
                           f"authorises nothing until the candles are recovered from IG and re-checked (PD-5)",
                           from_utc=_iso(a), to_utc=_iso(b))

    def _reconcile_gaps(self, now: datetime) -> None:
        """C: a recorded gap whose candles the store now holds (IG's own, by the approved recovery) is re-checked on
        them, in time order, by the tracker's own rules, for that opportunity only. A missed zone touch activates it at
        that candle; a missed destination ends it (four-way rule, the trade's own time deciding); the rebuilt hourly
        candles are checked for its D-25 count and its zone break. What cannot be placed without changing a decision
        already taken (a test already numbered, a break window already passed) is left for review and keeps it
        ineligible. Never an order, never a reopened opportunity, never a rewritten event."""
        side = side_of(self.s)
        self._reconcile_ended(now)
        for rec in list(self.opportunities):
            for g in list(rec.get("data_gaps") or []):
                if g.get("status") != "open" or not filled(self.s, self.store, g):
                    continue
                a, b = parse_iso(g["from_utc"]), parse_iso(g["to_utc"])
                before = rec["status"]
                for c in self.store.read_range("5m", a, b):
                    if rec not in self.opportunities:
                        break
                    with self._slot(rec):
                        if rec["status"] in AUTHORISING:
                            Keeper.five_minute(self, c, now)
                        elif rec["status"] == BROKEN:
                            rec["status"] = ACTIVE
                            try:
                                Keeper.five_minute(self, c, now)
                            finally:
                                if rec["status"] == ACTIVE:
                                    rec["status"] = BROKEN
                review = []
                L = self.lineages.get(rec.get("lineage"))
                hour0 = a.replace(minute=0, second=0, microsecond=0)
                for h in self.store.read_range("1h", hour0, b):
                    if not complete(h):
                        review.append(f"the {uk_short(h.start)} hourly candle is still incomplete")
                        continue
                    zb = (rec.get("invalidation") or {}).get("zone_break_close")
                    if zb is not None and rec in self.opportunities and rec["status"] in AUTHORISING:
                        close = cl(h, side)
                        if (close >= _d(zb)) if rec["trade"] == "SELL" else (close <= _d(zb)):
                            review.append(f"the rebuilt {uk_short(h.start)} hourly candle closed at {plain(close)}, "
                                          f"beyond the zone break {zb}: its break window cannot be replayed")
                    if L is not None and _iso(h.start) in (L["tests"].get("uncertain") or []):
                        z = rec["entry_zone"]
                        low, high = _d(z["low"]), _d(z["high"])
                        later = [e for e in L["tests"].get("events", []) if parse_iso(e[0]) > h.start]
                        probe = {"events": [e for e in L["tests"].get("events", []) if parse_iso(e[0]) < h.start],
                                 "through_utc": None, "uncertain": []}
                        what = count_hour(self.s, probe, h, low, high)
                        if what in ("test", "rearm") and later:
                            review.append(f"the rebuilt {uk_short(h.start)} hourly candle is a {what} for the D-25 "
                                          f"count, but later tests are already numbered: not renumbered")
                        elif what in ("test", "rearm"):
                            L["tests"]["events"].append([_iso(h.start), what])
                        L["tests"]["uncertain"] = [x for x in L["tests"]["uncertain"] if x != _iso(h.start)]
                        L["tests"].setdefault("reconciled", []).append([_iso(h.start), what or "no change"])
                g["status"] = "review" if review else "reconciled"
                g["reconciled_utc"] = _iso(now)
                after = rec["status"] if rec in self.opportunities else rec.get("status")
                self._append({"time_utc": _iso(now), "event": "data gap reconciled" if not review else "data gap review",
                              "id": rec["id"], "from_utc": g["from_utc"], "to_utc": g["to_utc"],
                              "why": (f"the candles from {uk_short(a)} to {uk_short(b)} are now stored (IG's own) and "
                                      f"were re-checked in time order: status {before} -> {after}"
                                      + (f"; left for review: {'; '.join(review)}" if review else
                                         "; eligible again for authorisation" if rec in self.opportunities else ""))})

    def _reconcile_ended(self, now: datetime) -> None:
        """C, for an opportunity that ENDED with a gap still open: once the gap's candles are stored, the zone touch
        they show before its destination (after its creation, by the tracker's own touch rule) corrects the ending's
        classification to "after_zone" in a recorded event (it is then a completed opportunity for the duplicate rule);
        the ending, its time and every recorded event stand; nothing is reopened."""
        from planner.keeper import AFTER_ZONE, AT_CREATION, BEFORE_ZONE, OVERLAPPED, candle_timing
        for L in self.lineages.values():
            for m in L.get("members", []):
                for g in m.get("data_gaps") or []:
                    if g.get("status") != "open" or not filled(self.s, self.store, g):
                        continue
                    a, b = parse_iso(g["from_utc"]), parse_iso(g["to_utc"])
                    z = m.get("entry_zone_full") or {"low": m["zone"]["low"], "high": m["zone"]["high"]}
                    end = parse_iso(m["destination_candle_end_utc"]) if m.get("destination_candle_end_utc") else None
                    touched = None
                    for c in self.store.read_range("5m", a, b):
                        if end is not None and c.end > end:
                            break
                        if candle_timing(c, m.get("created_utc")) in (BEFORE, OVERLAPPED):
                            continue
                        if interacts(self.s, c, _d(z["low"]), _d(z["high"]), from_below=m.get("trade") == "SELL"):
                            touched = c
                            break
                    g["status"], g["reconciled_utc"] = "reconciled", _iso(now)
                    note = f"the candles from {uk_short(a)} to {uk_short(b)} are now stored (IG's own) and were re-checked"
                    if touched is not None and m.get("destination_case") in (BEFORE_ZONE, AT_CREATION):
                        was = m["destination_case"]
                        m.update(destination_case=AFTER_ZONE, effective_status=COMPLETED,
                                 corrected={"time_utc": _iso(now), "was": was, "basis": "data recovery",
                                            "candle_start_utc": _iso(touched.start)})
                        self._append({"time_utc": _iso(now), "event": "classification corrected", "id": m["id"],
                                      "why": f"{note}: the {uk_short(touched.start)} candle reached the zone after "
                                             f"creation and before the destination, so the destination was reached "
                                             f"after the zone, not {was}; the ending stands, nothing reopened (PD-5)",
                                      "destination_case": AFTER_ZONE, "was": was,
                                      "candle_start_utc": _iso(touched.start)})
                    else:
                        self._append({"time_utc": _iso(now), "event": "data gap reconciled", "id": m["id"],
                                      "from_utc": g["from_utc"], "to_utc": g["to_utc"],
                                      "why": f"{note}: the ending's classification stands"})

    def _take_acks(self, now: datetime) -> None:
        """PD-1 C (owner 27 November 2026): the order sender's acknowledgements of trades IG confirmed open from an STP
        opportunity (orders/executions.py; one-way, read only here, no financial figure). Each is taken once (by its
        deal reference, persisted in acks_seen): the opportunity records the execution (it then ends COMPLETED if its
        destination is reached after it), the lineage records the test as consumed. An acknowledgement that arrives
        after its opportunity ended at its destination, for an execution before that destination, corrects the
        ending's classification in a recorded event; the opportunity is never reopened."""
        seen = self.state.setdefault("acks_seen", [])
        orders = getattr(self.s, "orders", None)
        if orders is None:
            return
        for a in read_acks(Path(orders.folder) / self.s.market.pair / ACKS_FILE):
            if a["reference"] in seen:
                continue
            seen.append(a["reference"])
            x = {k: a.get(k) for k in ("reference", "strategy", "executed_utc", "test", "key", "source")}
            lid = a.get("lineage")
            rec = next((r for r in self.opportunities if r["id"] == a.get("opportunity")), None)
            if rec is not None:
                lid = lid or rec.get("lineage")
                rec.setdefault("executions", []).append(x)
                self._note(rec, now, "trade executed", f"IG confirmed the trade {a['reference']} ({a.get('strategy')}) "
                           f"opened from this opportunity at {a.get('executed_utc')}, on test {a.get('test')} "
                           f"({a.get('key')}): recorded (PD-1)", reference=a["reference"],
                           executed_utc=a.get("executed_utc"), test=a.get("test"))
            L = self.lineages.get(lid) if lid else None
            if L is None:
                L = next((M for M in self.lineages.values()
                          if any(m["id"] == a.get("opportunity") for m in M.get("members", []))), None)
            if L is not None and a.get("test") is not None:
                refs = L.setdefault("consumed", {}).setdefault(str(a["test"]), [])
                if a["reference"] not in refs:
                    refs.append(a["reference"])
            if rec is None and L is not None:
                m = next((m for m in L["members"] if m["id"] == a.get("opportunity")), None)
                end = m and m.get("destination_candle_end_utc")
                if m and end and m.get("destination_case") not in (None, AFTER_TRADE) and \
                        parse_iso(a["executed_utc"]) < parse_iso(end):
                    before = m["destination_case"]
                    m.update(destination_case=AFTER_TRADE, effective_status=COMPLETED,
                             corrected={"time_utc": _iso(now), "was": before, "reference": a["reference"]})
                    self._append({"time_utc": _iso(now), "event": "classification corrected", "id": m["id"],
                                  "why": f"a confirmed trade entry ({a['reference']}, executed {a['executed_utc']}) "
                                         f"came before the destination ({end}): destination reached after a "
                                         f"confirmed trade entry, not {before}; the ending stands, nothing reopened "
                                         f"(PD-1)", "destination_case": AFTER_TRADE, "was": before,
                                  "reference": a["reference"]})

    def _count_lineages(self, c: Any) -> None:
        """D-25 / P-C8, once per finished hourly candle per lineage with a tracked opportunity, against the zone of its
        oldest tracked opportunity (the one an authorisation binds first)."""
        for L in self.lineages.values():
            tracked = sorted((r for r in self.opportunities if r.get("lineage") == L["id"] and r["status"] in TRACKED),
                             key=lambda r: (r["created_utc"], r["id"]))
            if tracked:
                z = tracked[0]["entry_zone"]
                count_hour(self.s, L["tests"], c, _d(z["low"]), _d(z["high"]))

    def _apply_lineage_map(self, now: datetime) -> None:
        """PD-4 (owner 27 November 2026): the auditable historical lineage map (planner/migrate_lineage.py), applied
        once per version of the file, idempotently: its lineages (members, tests, alias keys of tests already traded
        under another lineage id) are taken in, and a live opportunity it maps is moved to its lineage. The order
        journal and the trade records are never changed."""
        path = self.folder / LINEAGE_MAP
        try:
            raw = path.read_bytes()
        except OSError:
            return
        digest = hashlib.sha256(raw).hexdigest()
        if self.state.get("lineage_map_applied") == digest:
            return
        try:
            m = json.loads(raw)
        except ValueError:
            return
        for lid, Lm in sorted((m.get("lineages") or {}).items()):
            L = self.lineages.setdefault(lid, {"id": lid, "trade": Lm.get("trade"), "created_utc": Lm.get("created_utc"),
                                               "tests": new_tests(), "members": [], "aliases": {}, "consumed": {}})
            for k in ("trade", "created_utc", "home_zone"):
                if Lm.get(k):
                    L[k] = Lm[k]
            if Lm.get("tests"):
                L["tests"] = _copy(Lm["tests"])
            for n, keys in (Lm.get("aliases") or {}).items():
                have = L.setdefault("aliases", {}).setdefault(str(n), [])
                have.extend(k for k in keys if k not in have)
            for n, refs in (Lm.get("consumed") or {}).items():
                have = L.setdefault("consumed", {}).setdefault(str(n), [])
                have.extend(r for r in refs if r not in have)
            known = {x["id"] for x in L["members"]}
            L["members"].extend(_copy(x) for x in Lm.get("members") or [] if x["id"] not in known)
            L["map_evidence"] = Lm.get("evidence")
        for r in self.opportunities:
            lid = (m.get("opportunity_lineage") or {}).get(r["id"])
            if lid and lid in self.lineages and r.get("lineage") != lid:
                old = r.get("lineage")
                r["lineage"], r["lineage_created_utc"] = lid, self.lineages[lid]["created_utc"]
                L = self.lineages[lid]
                if r["id"] not in {x["id"] for x in L["members"]}:
                    L["members"].append(member(r))
                z = r["entry_zone"]
                count_gap(self.s, self.store, L["tests"], z["low"], z["high"], now)
                if old in self.lineages and old != lid:
                    self.lineages[old]["members"] = [x for x in self.lineages[old]["members"] if x["id"] != r["id"]]
                    if not self.lineages[old]["members"]:
                        self.lineages[old]["merged_into"] = lid
                self._note(r, now, "lineage reconciled", f"historical lineage map applied: lineage {old} -> {lid} "
                           f"(PD-4); keys already traded under the old ids stay protected as aliases", lineage=lid)
        self.state["lineage_map_applied"] = digest
        self._append({"time_utc": _iso(now), "event": "lineage map applied", "id": None, "sha256": digest,
                      "lineages": sorted((m.get("lineages") or {}).keys())})

    # ---- the checks ---------------------------------------------------------------------------------------------------

    def five_minute(self, c: Any, at: datetime | None = None) -> None:
        """The single tracker's 5-minute checks, on each opportunity that authorises. A BROKEN one gets the single
        tracker's destination check only (review, 25 November 2026): a primary destination reached while BROKEN ends
        it, COMPLETED or INVALIDATED by the same rule, so a later reclaim cannot restore an opportunity whose
        destination was already reached. It is never activated while BROKEN (its zone test applies only to WAITING)."""
        for rec in list(self.opportunities):
            if rec["status"] in AUTHORISING:
                with self._slot(rec):
                    Keeper.five_minute(self, c, at)
            elif rec["status"] == BROKEN:
                with self._slot(rec):
                    rec["status"] = ACTIVE          # the single tracker's checks run on a live record: as ACTIVE, only
                    try:                            # its destination rule applies (the zone test needs WAITING)
                        Keeper.five_minute(self, c, at)
                    finally:
                        if rec["status"] == ACTIVE:
                            rec["status"] = BROKEN

    def hourly(self, c: Any) -> None:
        side = side_of(self.s)
        beyond = Decimal(self.s.planner.break_beyond_pips) * ppp(self.s)
        window = self.s.planner.failed_breakout_within_candles
        self._count_lineages(c)
        for rec in list(self.opportunities):
            low, high = _d(rec["entry_zone"]["low"]), _d(rec["entry_zone"]["high"])
            bear = rec["trade"] == "SELL"
            edge = high if bear else low
            close = cl(c, side)
            if rec["status"] == BROKEN:
                b = rec["broken"]
                b["candles"] += 1
                back = close < edge if bear else close > edge
                if back:
                    rec["status"] = ACTIVE
                    rec.pop("broken", None)
                    self._note(rec, c.end, "failed breakout", f"after the zone break, the {uk_short(c.start)} hourly "
                               f"candle closed back {'below' if bear else 'above'} {plain(edge)} within {b['candles']} "
                               f"candle(s): back to Watch & Wait (OD-07, OD-31)", status=ACTIVE)
                elif b["candles"] >= window:
                    self._end(rec, c.end, INVALIDATED, f"confirmed break held: no hourly close back "
                              f"{'below' if bear else 'above'} {plain(edge)} within {window} candles of the break "
                              f"({b['broken_utc']})")
                continue
            if rec["status"] not in AUTHORISING:
                continue
            ext = hi(c, side) if bear else lo(c, side)
            past = (close - edge) if bear else (edge - close)
            if past >= beyond:
                rec["status"], rec["zone_broken_at"] = BROKEN, _iso(c.end)
                rec["broken"] = {"broken_utc": _iso(c.end), "candles": 0}
                self._note(rec, c.end, "broken", f"confirmed break: the {uk_short(c.start)} hourly candle closed at "
                           f"{plain(close)}, {plain((past / ppp(self.s)).quantize(Decimal('0.1')))} pips beyond the zone's "
                           f"{'top' if bear else 'bottom'} {plain(edge)}: BROKEN, authorises nothing; a close back inside "
                           f"within {window} hourly candles restores Watch & Wait (OD-31)", status=BROKEN)
                continue
            if past > 0:
                rec["beyond_close_utc"] = _iso(c.end)
                self._note(rec, c.end, "closed beyond", f"the {uk_short(c.start)} hourly candle closed {plain(close)}, "
                           f"beyond the zone edge {plain(edge)} by less than {self.s.planner.break_beyond_pips} pips "
                           f"(recorded only)")
            elif rec.get("beyond_close_utc"):
                rec["beyond_close_utc"] = None
                self._note(rec, c.end, "reclaim", f"the {uk_short(c.start)} hourly candle closed back inside the zone "
                           f"edge {plain(edge)} (recorded only)")
            elif (ext > edge) if bear else (ext < edge):
                self._note(rec, c.end, "wick sweep", f"the {uk_short(c.start)} hourly candle went to {plain(ext)}, "
                           f"beyond the zone edge {plain(edge)}, and closed back at {plain(close)} (recorded only)")

    def four_hour(self, c: Any) -> None:
        """ARCH 10.2: a 4-hour close at or beyond the opportunity's own structure-break price invalidates it."""
        side = side_of(self.s)
        for rec in list(self.opportunities):
            sb = (rec.get("invalidation") or {}).get("structure_break_close")
            if sb is None:
                continue
            bear = rec["trade"] == "SELL"
            close = cl(c, side)
            if (close >= _d(sb)) if bear else (close <= _d(sb)):
                self._end(rec, c.end, INVALIDATED, f"structure break: the {uk_short(c.start)} 4-hour candle closed at "
                          f"{plain(close)}, at or {'above' if bear else 'below'} {sb}")

    def rollover(self, now: datetime, plans: list[dict]) -> None:
        """At the 00:00 UK re-plan: an opportunity whose daily or weekly fixed levels are gone from the level map."""
        levels = None
        for p in plans:
            got = (p.get("structure") or {}).get("levels")
            if got is not None:
                levels = {(m.get("name"), m.get("price")) for m in got}
                break
        if levels is None:
            return                                      # no level map to judge by: nothing is ended
        for rec in list(self.opportunities):
            gone = [f"{m['name']} {m['price']}" for m in rec["entry_zone"]["levels"]
                    if m.get("fixed") and m.get("daily_or_weekly") is True and (m["name"], m["price"]) not in levels]
            if gone:
                self._end(rec, now, INVALIDATED, "structural levels changed at the pivot rollover: "
                          + ", ".join(gone) + " no longer in the level map (D-21, OD-13)")

    # ---- the hourly re-plan -----------------------------------------------------------------------------------------

    def _plans(self, now: datetime) -> list[dict]:
        trades = ("SELL", "BUY") if self.bidirectional else (None,)
        out = []
        for t in trades:
            if t is None:
                plan = self.planner(self.s, self.store, now, self.calendar) if self.calendar is not None else \
                    self.planner(self.s, self.store, now)
            else:
                plan = self.planner(self.s, self.store, now, self.calendar, trade=t)
            out.append(plan.as_dict())
        return out

    def replan(self, now: datetime, rollover: bool = False) -> list[dict]:
        plans = self._plans(now)
        self.state["last_plan"] = plans[0]
        self.state["last_plans"] = {p.get("trade") or "4-hour direction": summary(p) for p in plans}
        for p in plans:
            self._append({"time_utc": _iso(now), "event": "analysis", "id": None, "plan": summary(p)}
                         | ({"relation_to_h4": p["relation_to_h4"]} if p.get("relation_to_h4") else {}))
        if rollover:
            self.rollover(now, plans)
        self.state.pop("not_issued", None)
        for p in plans:
            hit = p.get("destination_reached")
            if hit:                                     # D-1: an opportunity's own primary found already reached
                for rec in list(self.opportunities):
                    if rec["status"] in AUTHORISING and rec["trade"] == p.get("trade") and \
                            _d(hit["primary"]) == _d(rec["destinations"]["primary"]["price"]):
                        status, case, why = destination_end(rec, f"found at the hourly re-check: {hit['how']}", now)
                        self._end(rec, now, status, why, {"destination_case": case})
            if p.get("no_recommendation") is not None or p.get("entry_zone") is None:
                continue
            ident = identity(p)
            same = [r for r in self.opportunities if r["identity"] == ident]
            match = next((r for r in same if overlaps(p["entry_zone"], r["entry_zone"])), None)
            if match is not None:
                with self._slot(match):
                    changed = self._update_from(p)
                    self._event(now, "changed" if changed else "supported",
                                ("re-checked, still supported; changed: " + "; ".join(changed)) if changed else
                                "re-checked: the structural basis still holds", plan=summary(p))
                continue
            if same:                                    # D-22 narrowed: the same identity, a zone that moved away
                old = same[0]
                oz, nz = old["entry_zone"], p["entry_zone"]
                self._end(old, now, SUPERSEDED, f"the same identity in a zone that does not overlap the previous one "
                          f"({oz['low']}-{oz['high']} to {nz['low']}-{nz['high']}): " + (p.get("selection_reason") or ""))
                new = self._new_opp(now, p, f"supersedes {old['id']}: {p.get('selection_reason')}", inherit=old)
            else:
                dup = self._duplicate_of(p)
                if dup is not None:
                    why = (f"not issued: the same identity and primary destination {p['destinations']['primary']['price']} "
                           f"as {dup}, which already reached it")
                    self.state["not_issued"] = {"time_utc": _iso(now), "why": why, "duplicate_of": dup}
                    if self.state.get("duplicate_noted") != dup:
                        self.state["duplicate_noted"] = dup
                        self._append({"time_utc": _iso(now), "event": "duplicate", "id": None, "why": why,
                                      "duplicate_of": dup})
                    continue
                new = self._new_opp(now, p, p.get("selection_reason") or "")
            self._in_zone_at_creation(new, now)
        return plans

    def _in_zone_at_creation(self, rec: dict, now: datetime) -> None:
        last5 = [c for c in self.store.read_range("5m", now - timedelta(hours=1), now) if c.end <= now]
        low, high = _d(rec["entry_zone"]["low"]), _d(rec["entry_zone"]["high"])
        if last5 and interacts(self.s, last5[-1], low, high, from_below=rec["trade"] == "SELL"):
            c = last5[-1]
            rec.setdefault("zone_before_creation", {"basis": f"the {uk_short(c.start)} 5-minute candle before "
                                                             f"creation was at the zone", "candle_start_utc": _iso(c.start)})
            self._note(rec, now, "in zone at creation", f"the {uk_short(c.start)} 5-minute candle, finished before the "
                       f"opportunity was created, was already at the zone: not an activation (recorded only)",
                       candle_start_utc=_iso(c.start), candle_end_utc=_iso(c.end), candle_timing=BEFORE,
                       event_time_basis=EVENT_BASIS)

    # ---- one run ------------------------------------------------------------------------------------------------------

    def run(self, now: datetime) -> None:
        from analyser.indicators import last_candles
        now = now.astimezone(UTC)
        self._apply_lineage_map(now)
        self._take_acks(now)
        self._reconcile_gaps(now)
        h1 = last_candles(self.store, "1h", now, 1)
        h1_end = h1[-1].end if h1 else None
        fives_since = parse_iso(self.state["m5_checked_until"]) if self.state.get("m5_checked_until") else None
        if fives_since is not None and self.opportunities:
            self._record_gaps(fives_since, now)          # before the candles after it: the gap came first
            for c in self.store.read_range("5m", fives_since, now):
                if c.end <= now and c.start >= fives_since:
                    self.five_minute(c)
        validated = parse_iso(self.state["validated_h1_end"]) if self.state.get("validated_h1_end") else None
        uk_day = now.astimezone(UK).date().isoformat()
        rollover = self.state.get("last_replan_uk_day") not in (None, uk_day)
        if h1_end is not None and (validated is None or h1_end > validated or rollover):
            if validated is not None:
                for c in self.store.read_range("1h", validated, h1_end):
                    if c.start >= validated and c.end <= h1_end:
                        self.hourly(c)
            h4_since = parse_iso(self.state["h4_checked_until"]) if self.state.get("h4_checked_until") else None
            h4 = last_candles(self.store, "4h", now, 1)
            if h4_since is not None:
                for c in self.store.read_range("4h", h4_since, now):
                    if c.start >= h4_since and c.end <= now:
                        self.four_hour(c)
            if h4:
                self.state["h4_checked_until"] = _iso(h4[-1].end)
            self.replan(now, rollover=rollover)
            self.state["validated_h1_end"] = _iso(h1_end)
            self.state["last_replan_uk_day"] = uk_day
        five = [c for c in self.store.read_range("5m", now - timedelta(days=4), now) if c.end <= now]
        if five:
            self.state["m5_checked_until"] = _iso(five[-1].end)
        fresh, why = freshness(self.s, five[-1] if five else None, h1[-1] if h1 else None, now)
        reasons = list(why)
        if self.state.get("validated_h1_end") != _iso(h1_end):
            reasons.append("not re-checked at the latest finished hourly candle")
        self.state["data_fresh"] = fresh
        self.state["current"] = fresh and not reasons
        self.state["not_current_reasons"] = reasons
        self.state["last_analysis_utc"] = (self.state.get("last_plan") or {}).get("as_of_utc")
        self.state["last_run_utc"] = _iso(now)
        for rec in self.opportunities:
            rec["label"] = label(rec["status"])
        self._save(now)


def make_keeper(settings: Any, store: Any, planner: Any = None, calendar: list | None = None) -> Keeper:
    """The tracker the switches ask for: OpportunityKeeper while STP_OPPORTUNITIES is on, else the single tracker."""
    if getattr(getattr(settings, "switches", None), "stp_opportunities", False):
        return OpportunityKeeper(settings, store, planner, calendar)
    return Keeper(settings, store, planner, calendar)
