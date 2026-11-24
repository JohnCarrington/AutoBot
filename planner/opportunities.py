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
  * no time expiry anywhere (H16).
Statuses: WAITING and ACTIVE ("Watch & Wait") authorise; BROKEN is tracked but does not; COMPLETED, INVALIDATED and
SUPERSEDED end it.

Files: the tracker's own, in planner.folder/<PAIR>/. current.json gains "opportunities" (the tracked list) and keeps
"recommendation" as a copy of the newest live opportunity, so the dashboard and, after a switch-off, the single
tracker read it as before. recommendations.jsonl and issued.jsonl as before (every event carries its id).
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from planner.keeper import (ACTIVE, BEFORE, COMPLETED, EVENT_BASIS, INVALIDATED, LIVE, SUPERSEDED, UTC, WAITING,
                            Keeper, _d, _iso, identity, overlaps, summary)
from planner.measure import cl, freshness, hi, lo, ppp, side_of
from planner.zones import interacts
from prices.model import UK, parse_iso, plain, uk_short

BROKEN = "BROKEN"
TRACKED = (WAITING, ACTIVE, BROKEN)
AUTHORISING = LIVE                      # WAITING and ACTIVE (Watch & Wait)
WATCH_AND_WAIT = "Watch & Wait"         # the label shown for ACTIVE (OD-11)


def label(status: str) -> str:
    return WATCH_AND_WAIT if status == ACTIVE else status.capitalize() if status else status


def _key(ident: list) -> str:
    return json.dumps(ident)


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
        return st

    @property
    def opportunities(self) -> list[dict]:
        return self.state["opportunities"]

    def _save(self, now: datetime) -> None:
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
        self.state["opportunities"] = [r for r in self.opportunities if r is not rec]
        self.state["recommendation"] = None

    def _end(self, rec: dict, t: datetime, status: str, why: str, evidence: dict | None = None) -> None:
        with self._slot(rec):
            self._retire(t, status, why, evidence)

    def _note(self, rec: dict, t: datetime, kind: str, why: str, **more: Any) -> None:
        with self._slot(rec):
            self._event(t, kind, why, **more)

    def _duplicate_of(self, p: dict) -> str | None:
        """The single tracker's duplicate rule (FC-05, D-1), per identity: the most recently ended opportunity with
        this identity was COMPLETED with this primary destination."""
        le = self.state["ended_by_identity"].get(_key(identity(p)))
        if not le or le.get("status") != COMPLETED or le.get("primary") is None:
            return None
        primary = ((p.get("destinations") or {}).get("primary") or {}).get("price")
        if primary is not None and _d(primary) == _d(le["primary"]):
            return le["id"]
        return None

    def _new_opp(self, t: datetime, plan: dict, why: str, inherit: dict | None = None) -> dict:
        with self._slot(None):
            self._new(t, plan, why)
            rec = self.state["recommendation"]
        rec["lineage"] = inherit["lineage"] if inherit else rec["id"]
        rec["lineage_created_utc"] = inherit["lineage_created_utc"] if inherit else rec["created_utc"]
        if inherit:
            rec["ever_active"] = bool(inherit.get("ever_active"))
            rec["supersedes"] = inherit["id"]
        if plan.get("relation_to_h4") is not None:
            rec["relation_to_h4"] = plan["relation_to_h4"]
        self.opportunities.append(rec)
        return rec

    # ---- the checks ---------------------------------------------------------------------------------------------------

    def five_minute(self, c: Any, at: datetime | None = None) -> None:
        """The single tracker's 5-minute checks, on each opportunity that authorises (a BROKEN one waits for the
        hourly closes)."""
        for rec in list(self.opportunities):
            if rec["status"] in AUTHORISING:
                with self._slot(rec):
                    Keeper.five_minute(self, c, at)

    def hourly(self, c: Any) -> None:
        side = side_of(self.s)
        beyond = Decimal(self.s.planner.break_beyond_pips) * ppp(self.s)
        window = self.s.planner.failed_breakout_within_candles
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
                        if rec["ever_active"]:
                            self._end(rec, now, COMPLETED, f"price reached the primary destination "
                                      f"{rec['destinations']['primary']['price']} after the zone (found at the hourly "
                                      f"re-check: {hit['how']})")
                        else:
                            self._end(rec, now, INVALIDATED, f"destination reached before entry: {hit['how']}, without "
                                      f"reaching the zone (found at the hourly re-check)")
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
            self._note(rec, now, "in zone at creation", f"the {uk_short(c.start)} 5-minute candle, finished before the "
                       f"opportunity was created, was already at the zone: not an activation (recorded only)",
                       candle_start_utc=_iso(c.start), candle_end_utc=_iso(c.end), candle_timing=BEFORE,
                       event_time_basis=EVENT_BASIS)

    # ---- one run ------------------------------------------------------------------------------------------------------

    def run(self, now: datetime) -> None:
        from analyser.indicators import last_candles
        now = now.astimezone(UTC)
        h1 = last_candles(self.store, "1h", now, 1)
        h1_end = h1[-1].end if h1 else None
        fives_since = parse_iso(self.state["m5_checked_until"]) if self.state.get("m5_checked_until") else None
        if fives_since is not None and self.opportunities:
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
