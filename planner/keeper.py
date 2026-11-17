"""The planner's recommendation lifecycle and records (D-21 modified, D-22, D-23, D-36; FC-05 to FC-10, FC-13;
owner's adjustment 1, 17 November 2026). OBSERVE ONLY: nothing here authorises, refuses, opens, changes or closes a
trade, and nothing reads or writes any trading record.

One live recommendation per pair at most. Each run (after a new 5-minute candle):
  1. the 5-minute checks, on every 5-minute candle finished since the last run (P-F2), in time order:
       WAITING -> ACTIVE          the candle interacts with the zone (planner/zones.py interacts; FC-01);
       WAITING -> INVALIDATED     it reaches the primary destination first ("destination reached before entry");
       ACTIVE (or once ACTIVE) -> COMPLETED   it reaches the primary destination;
  2. on each hourly candle finished since the last re-plan:
       -> INVALIDATED             it closes at least hourly_read.break_beyond_pips beyond the zone's far edge (FC-02);
       ACTIVE -> WAITING          it stays wholly more than rejection.near_level_within_pips clear of the zone (P-F6);
       recorded only (D-24): wick sweeps beyond the far edge, closes beyond it by less than 3 pips, reclaims, and
       failed breakouts (a confirmed break closed back within planner.failed_breakout_within_candles);
  3. a full re-plan whenever a new hourly candle has finished (also at the 00:00 UK rollover) (D-21, D-36):
       no live recommendation and the plan recommends -> a new one, at once (adjustment 1: no confirming hour);
       live and the direction changed (or became NEUTRAL/TRANSITIONAL) -> INVALIDATED (FC-10);
       live and the same direction and fixed levels, AND the new zone overlaps the previous one -> it continues:
         "supported" or "changed" (moving levels, edges, destinations), recorded (FC-05; owner's R2, 17 November 2026);
       live and different fixed levels, or a zone that does not overlap the previous one -> SUPERSEDED (D-22). (A
         zone of moving levels only, such as an hourly EMA and today's still-running session high, has no fixed
         levels: the overlap test is what tells a different zone from the same one moving.)
       live and no longer recommended -> INVALIDATED, with the plan's reason ("supporting evidence changed").
CURRENT (FC-08): a recommendation is current only when it was re-checked at the latest finished hourly candle, the
5-minute checks reached the latest finished 5-minute candle, and the data is fresh (P-A3). Stale data never
invalidates; it makes the recommendation not current (D-21: no new authorisation from it, when that exists).

Files, in planner.folder/<PAIR>/: current.json (the recommendation, the last plan and the state; a safe write) and
recommendations.jsonl (every event and every hourly analysis; append-only, kept for good, P-F8); issued.jsonl (each
recommendation in full as issued, for the dashboard's history: reporting only, append-only).
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

from analyser.indicators import last_candles
from housekeeping.files import safe_write
from planner.measure import cl, freshness, hi, lo, ppp, side_of
from planner.zones import interacts, wholly_clear
from prices.model import UK, Candle, parse_iso, plain, uk_short

log = logging.getLogger("autobot.planner")
UTC = timezone.utc
CANDIDATE, WAITING, ACTIVE, INVALIDATED, SUPERSEDED, COMPLETED = (
    "CANDIDATE", "WAITING", "ACTIVE", "INVALIDATED", "SUPERSEDED", "COMPLETED")
LIVE = (WAITING, ACTIVE)
OBSERVE_ONLY = "OBSERVE ONLY - DOES NOT CONTROL TRADING"


def _iso(t: datetime | None) -> str | None:
    return None if t is None else t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _d(x: Any) -> Decimal:
    return Decimal(str(x))


def overlaps(a: dict, b: dict) -> bool:
    """Two zones ({"low", "high"}) share at least one price."""
    return _d(a["low"]) <= _d(b["high"]) and _d(b["low"]) <= _d(a["high"])


def identity(plan_dict: dict) -> list:
    """FC-05: direction plus the zone's fixed levels (moving averages left out)."""
    z = plan_dict["entry_zone"]
    fixed = sorted([m["name"], m["price"]] for m in z["levels"] if m["fixed"])
    return [plan_dict["trade"], fixed]


class Keeper:
    def __init__(self, settings: Any, store: Any, planner: Callable | None = None, calendar: list | None = None):
        from planner.assess import plan_at
        self.s, self.store = settings, store
        self.planner = planner or plan_at
        self.calendar = calendar
        self.folder = Path(settings.planner.folder) / settings.market.pair
        self.state = self._load()

    # ---- files ---------------------------------------------------------------------------------------------------

    @property
    def current_path(self) -> Path:
        return self.folder / "current.json"

    @property
    def history_path(self) -> Path:
        return self.folder / "recommendations.jsonl"

    @property
    def issued_path(self) -> Path:
        return self.folder / "issued.jsonl"

    def _load(self) -> dict:
        try:
            st = json.loads(self.current_path.read_text())
            if not isinstance(st, dict) or st.get("pair") != self.s.market.pair:
                raise ValueError("not this pair's planner file")
            return st
        except FileNotFoundError:
            pass
        except (ValueError, OSError) as e:                  # a damaged file: kept aside, never lost
            aside = self.current_path.with_suffix(f".damaged-{datetime.now(UTC):%Y%m%d%H%M%S}.json")
            try:
                self.current_path.rename(aside)
            except OSError:
                pass
            log.warning("Planner file unreadable (%s); kept as %s, starting afresh.", e, aside.name)
        return {"pair": self.s.market.pair, "recommendation": None, "validated_h1_end": None, "m5_checked_until": None,
                "last_plan": None, "recent": [], "counter": 0}

    def _append(self, event: dict) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        with self.history_path.open("a") as f:
            f.write(json.dumps(event) + "\n")

    def _save(self, now: datetime) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        self.state["written_utc"] = _iso(now)
        self.state["observe_only"] = OBSERVE_ONLY
        safe_write(self.current_path, (json.dumps(self.state, indent=1) + "\n").encode())

    # ---- events --------------------------------------------------------------------------------------------------

    def _event(self, t: datetime, kind: str, why: str, **more: Any) -> None:
        rec = self.state["recommendation"]
        e = {"time_utc": _iso(t), "event": kind, "id": rec["id"] if rec else None, "why": why} | more
        if rec is not None:
            rec.setdefault("history", []).append({k: v for k, v in e.items() if k != "id"})
        self._append(e)

    def _retire(self, t: datetime, status: str, why: str) -> None:
        rec = self.state["recommendation"]
        rec["status"], rec["status_reason"], rec["ended_utc"] = status, why, _iso(t)
        self._event(t, status.lower(), why, status=status)
        self.state["recent"] = ([{"id": rec["id"], "trade": rec["trade"], "zone": [rec["entry_zone"]["low"], rec["entry_zone"]["high"]],
                                  "status": status, "why": why, "created_utc": rec["created_utc"], "ended_utc": rec["ended_utc"]}]
                                + self.state.get("recent", []))[: self.s.planner.panel_history]
        if status == INVALIDATED and rec.get("zone_broken_at"):
            self.state["watch_after_break"] = {"id": rec["id"], "far_edge": rec["far_edge"], "trade": rec["trade"],
                                               "broken_utc": rec["zone_broken_at"], "candles": 0}
        self.state["recommendation"] = None

    def _new(self, t: datetime, plan: dict, why: str) -> None:
        self.state["counter"] = self.state.get("counter", 0) + 1
        rid = f"STP-{self.s.market.pair}-{t.astimezone(UTC):%Y%m%d-%H%M}-{self.state['counter']}"
        z = plan["entry_zone"]
        bear = plan["trade"] == "SELL"
        rec = {
            "id": rid, "instrument": self.s.market.pair, "created_utc": _iso(t), "market_data_utc": plan["market_data_utc"],
            "status": CANDIDATE, "status_reason": why, "trade": plan["trade"], "identity": identity(plan),
            "far_edge": z["high"] if bear else z["low"], "ever_active": False, "history": [],
        } | {k: plan[k] for k in ("dominant_direction", "condition", "opportunity", "expected_movement", "entry_zone",
                                  "reference_entry", "reachability", "selection_reason", "destinations", "invalidation",
                                  "observations", "direction_evidence", "condition_evidence", "alternative")}
        rec["six_factors"] = six_factors(plan)
        self.state["recommendation"] = rec
        self._event(t, "created", why, status=CANDIDATE, plan=summary(plan))
        self._issued(rec)
        rec["status"] = WAITING
        self._event(t, "waiting", "issued on the first analysis with all the evidence (adjustment 1)", status=WAITING)

    def _issued(self, rec: dict) -> None:
        """Reporting only (the dashboard's history; owner's brief of 17 November 2026): the full recommendation exactly
        as issued, one line per recommendation in issued.jsonl (append-only), so its original destinations and
        invalidation stay available after it ends. Decides nothing; a failure here is logged and changes nothing."""
        try:
            self.folder.mkdir(parents=True, exist_ok=True)
            with self.issued_path.open("a") as f:
                f.write(json.dumps({k: v for k, v in rec.items() if k != "history"}) + "\n")
        except Exception as e:                                  # noqa: BLE001  never stops the planner
            log.warning("Planner: issued.jsonl not written (%s); the recommendation is unaffected.", e)

    def _update_from(self, plan: dict) -> list[str]:
        """Update the live recommendation from a re-plan with the same identity; what changed, in words (moving
        averages drifting and test counts are not called a change)."""
        rec = self.state["recommendation"]
        changed = []
        oz, nz = rec["entry_zone"], plan["entry_zone"]
        if (oz["low"], oz["high"]) != (nz["low"], nz["high"]):
            changed.append(f"zone edges {oz['low']}-{oz['high']} to {nz['low']}-{nz['high']}")
        if oz["class"] != nz["class"]:
            changed.append(f"class {oz['class']} to {nz['class']}")
        if set(oz["families"]) != set(nz["families"]):
            changed.append(f"families {', '.join(oz['families'])} to {', '.join(nz['families'])}")
        if rec.get("reference_entry") != plan.get("reference_entry"):
            changed.append(f"reference entry to {plan['reference_entry']['price']} ({plan['reference_entry']['level']})")
        for k in ("intermediate", "primary", "extended"):
            a, b = (rec["destinations"].get(k) or {}).get("price"), (plan["destinations"].get(k) or {}).get("price")
            if a != b:
                changed.append(f"{k} destination {a} to {b}")
        for k in ("condition", "opportunity", "reachability"):
            if rec.get(k) != plan.get(k):
                changed.append(f"{k} {rec.get(k)} to {plan.get(k)}")
        for k in ("condition", "opportunity", "expected_movement", "entry_zone", "reference_entry", "reachability",
                  "selection_reason", "destinations", "invalidation", "observations", "direction_evidence",
                  "condition_evidence", "alternative", "market_data_utc"):
            rec[k] = plan.get(k)
        bear = rec["trade"] == "SELL"
        rec["far_edge"] = rec["entry_zone"]["high"] if bear else rec["entry_zone"]["low"]
        rec["six_factors"] = six_factors(plan)
        return changed

    # ---- the checks -------------------------------------------------------------------------------------------------

    def _zone(self) -> tuple[Decimal, Decimal, bool]:
        rec = self.state["recommendation"]
        return _d(rec["entry_zone"]["low"]), _d(rec["entry_zone"]["high"]), rec["trade"] == "SELL"

    def five_minute(self, c: Candle, at: datetime | None = None, entry_only: bool = False) -> None:
        rec = self.state["recommendation"]
        if rec is None or rec["status"] not in LIVE:
            return
        low, high, bear = self._zone()
        dz = rec["destinations"]["primary"]["zone"]
        dlow, dhigh = _d(dz["low"]), _d(dz["high"])
        at = at or c.end
        applies = rec["invalidation"].get("destination_first_applies", True)
        if not entry_only and interacts(self.s, c, dlow, dhigh, from_below=not bear) and (applies or rec["ever_active"]):
            if rec["ever_active"]:
                self._retire(at, COMPLETED, f"price reached the primary destination {rec['destinations']['primary']['price']} "
                             f"({uk_short(c.start)}) after the zone")
            else:
                self._retire(at, INVALIDATED, f"destination reached before entry: price reached "
                             f"{rec['destinations']['primary']['price']} ({uk_short(c.start)}) without reaching the zone")
            return
        if rec["status"] == WAITING and interacts(self.s, c, low, high, from_below=bear):
            rec["status"], rec["ever_active"] = ACTIVE, True
            self._event(at, "active", f"the {uk_short(c.start)} 5-minute candle reached the zone "
                        f"{plain(low)}-{plain(high)}", status=ACTIVE)

    def hourly(self, c: Candle) -> None:
        side = side_of(self.s)
        beyond = Decimal(self.s.hourly_read.break_beyond_pips) * ppp(self.s)
        w = self.state.get("watch_after_break")
        if w:
            w["candles"] += 1
            edge, sell = _d(w["far_edge"]), w["trade"] == "SELL"
            back = cl(c, side) < edge if sell else cl(c, side) > edge
            if back:
                self._append({"time_utc": _iso(c.end), "event": "failed breakout", "id": w["id"],
                              "why": f"after the zone break, the {uk_short(c.start)} hourly candle closed back "
                                     f"{'below' if sell else 'above'} {plain(edge)} within {w['candles']} candle(s) (recorded only)"})
                self.state["watch_after_break"] = None
            elif w["candles"] >= self.s.planner.failed_breakout_within_candles:
                self.state["watch_after_break"] = None
        rec = self.state["recommendation"]
        if rec is None or rec["status"] not in LIVE:
            return
        low, high, bear = self._zone()
        edge = high if bear else low
        close, ext = cl(c, side), (hi(c, side) if bear else lo(c, side))
        past = (close - edge) if bear else (edge - close)
        if past >= beyond:
            rec["zone_broken_at"] = _iso(c.end)
            self._retire(c.end, INVALIDATED, f"confirmed break: the {uk_short(c.start)} hourly candle closed at {plain(close)}, "
                         f"{plain((past / ppp(self.s)).quantize(Decimal('0.1')))} pips beyond the zone's "
                         f"{'top' if bear else 'bottom'} {plain(edge)}")
            return
        if past > 0:
            rec["beyond_close_utc"] = _iso(c.end)
            self._event(c.end, "closed beyond", f"the {uk_short(c.start)} hourly candle closed {plain(close)}, beyond the "
                        f"zone edge {plain(edge)} by less than {self.s.hourly_read.break_beyond_pips} pips (recorded only)")
        elif rec.get("beyond_close_utc"):
            rec["beyond_close_utc"] = None
            self._event(c.end, "reclaim", f"the {uk_short(c.start)} hourly candle closed back inside the zone edge "
                        f"{plain(edge)} (recorded only)")
        elif (ext > edge) if bear else (ext < edge):
            self._event(c.end, "wick sweep", f"the {uk_short(c.start)} hourly candle went to {plain(ext)}, beyond the zone "
                        f"edge {plain(edge)}, and closed back at {plain(close)} (recorded only)")
        if rec["status"] == ACTIVE and wholly_clear(self.s, c, low, high) and ((hi(c, side) < low) if bear else (lo(c, side) > high)):
            rec["status"] = WAITING
            self._event(c.end, "waiting", f"the {uk_short(c.start)} hourly candle stayed wholly clear of the zone", status=WAITING)

    def replan(self, now: datetime) -> dict:
        plan = self.planner(self.s, self.store, now, self.calendar) if self.calendar is not None else \
            self.planner(self.s, self.store, now)
        p = plan.as_dict()
        self.state["last_plan"] = p
        self._append({"time_utc": _iso(now), "event": "analysis", "id": None, "plan": summary(p)})
        rec = self.state["recommendation"]
        if rec is not None and rec["status"] in LIVE:
            if p["dominant_direction"] != rec["dominant_direction"]:
                self._retire(now, INVALIDATED, f"the 4-hour direction changed from {rec['dominant_direction']} to "
                             f"{p['dominant_direction']}")
            elif p["no_recommendation"] is None and p["entry_zone"] is not None:
                if identity(p) == rec["identity"] and overlaps(p["entry_zone"], rec["entry_zone"]):
                    changed = self._update_from(p)
                    self._event(now, "changed" if changed else "supported",
                                ("re-checked, still supported; changed: " + "; ".join(changed)) if changed else
                                "re-checked: the structural basis still holds", plan=summary(p))
                else:
                    old = rec["id"]
                    nz, oz = p["entry_zone"], rec["entry_zone"]
                    what = ("a zone that does not overlap the previous one" if not overlaps(nz, oz)
                            else "a zone resting on different fixed levels")
                    self._retire(now, SUPERSEDED, f"{what} ({oz['low']}-{oz['high']} to {nz['low']}-{nz['high']}): "
                                 + p["selection_reason"])
                    self._new(now, p, f"supersedes {old}: {p['selection_reason']}")
            else:
                self._retire(now, INVALIDATED, f"supporting evidence changed: {p['no_recommendation']}")
        if self.state["recommendation"] is None and p["no_recommendation"] is None and p["entry_zone"] is not None:
            self._new(now, p, p["selection_reason"])
        return p

    # ---- one run ---------------------------------------------------------------------------------------------------

    def run(self, now: datetime) -> None:
        now = now.astimezone(UTC)
        h1 = last_candles(self.store, "1h", now, 1)
        h1_end = h1[-1].end if h1 else None
        fives_since = parse_iso(self.state["m5_checked_until"]) if self.state.get("m5_checked_until") else None
        rec = self.state["recommendation"]
        if fives_since is not None and rec is not None:
            for c in self.store.read_range("5m", fives_since, now):
                if c.end <= now and c.start >= fives_since:
                    self.five_minute(c)
        validated = parse_iso(self.state["validated_h1_end"]) if self.state.get("validated_h1_end") else None
        rollover = self.state.get("last_replan_uk_day") != now.astimezone(UK).date().isoformat()
        if h1_end is not None and (validated is None or h1_end > validated or rollover):
            if validated is not None:
                for c in self.store.read_range("1h", validated, h1_end):
                    if c.start >= validated and c.end <= h1_end:
                        self.hourly(c)
            before = (self.state["recommendation"] or {}).get("id")
            self.replan(now)
            new = self.state["recommendation"]
            if new is not None and new["id"] != before:         # a new one: is price already in its zone?
                last5 = [c for c in self.store.read_range("5m", now - timedelta(hours=1), now) if c.end <= now]
                if last5:
                    self.five_minute(last5[-1], at=now, entry_only=True)
            self.state["validated_h1_end"] = _iso(h1_end)
            self.state["last_replan_uk_day"] = now.astimezone(UK).date().isoformat()
        five = [c for c in self.store.read_range("5m", now - timedelta(days=4), now) if c.end <= now]
        if five:
            self.state["m5_checked_until"] = _iso(five[-1].end)
        fresh, why = freshness(self.s, five[-1] if five else None, h1[-1] if h1 else None, now)
        reasons = list(why)
        rec = self.state["recommendation"]
        if rec is not None and self.state.get("validated_h1_end") != _iso(h1_end):
            reasons.append("not re-checked at the latest finished hourly candle")
        self.state["data_fresh"] = fresh
        self.state["current"] = rec is not None and fresh and not reasons
        self.state["not_current_reasons"] = reasons
        self.state["last_analysis_utc"] = (self.state.get("last_plan") or {}).get("as_of_utc")
        self.state["last_run_utc"] = _iso(now)
        self._save(now)


def _lab(m: dict) -> str:
    return f"{m['name']} {m['price']}" + (f" ({m['role']})" if m.get("role") else "")


def summary(p: dict) -> dict:
    """A compact copy of a plan for the history file."""
    z = p.get("entry_zone")
    d = p.get("destinations") or {}
    return {"direction": p["dominant_direction"], "condition": p["condition"], "opportunity": p.get("opportunity"),
            "trade": p.get("trade"), "zone": None if z is None else {"low": z["low"], "high": z["high"], "class": z["class"],
                                                                      "families": z["families"],
                                                                      "levels": [_lab(m) for m in z["levels"]]},
            "reference": p.get("reference_entry"), "reachability": p.get("reachability"),
            "primary": (d.get("primary") or {}).get("price"), "no_recommendation": p.get("no_recommendation"),
            "fresh": p.get("fresh"), "market_data_utc": p.get("market_data_utc"),
            "threshold_misses": p.get("threshold_misses", []), "warming_up": p.get("warming_up", [])}


def six_factors(p: dict) -> dict:
    """The six contextual bounce factors (design section 12), recorded with the recommendation; none is a filter."""
    o = p.get("observations") or {}
    z = p.get("entry_zone") or {}
    return {"1_structural_level": {"zone": [z.get("low"), z.get("high")], "families": z.get("families"),
                                   "levels": [_lab(m) for m in z.get("levels", [])]},
            "2_higher_timeframe_direction": p.get("dominant_direction"),
            "3_daily_extension": {"today_range_adr": o.get("today_range_adr"), "adr_pips": o.get("adr_pips")},
            "4_sweep_and_rejection": "recorded in the history as wick sweep / closed beyond / reclaim / confirmed break",
            "5_tests": z.get("tests"),
            "6_time_of_day": {"uk_time": o.get("uk_time"), "minutes_from": o.get("minutes_from")}}


# ---- inside the price service: start the planner in its own process, never wait for it -------------------------

class PlannerUpdater:
    """Called by the price service after each new 5-minute candle, LAST (after the trading engine), only while the
    switch PLANNER_OBSERVE is on. It starts `python -m planner run` as a separate, low-priority process and returns at
    once: the planner never runs on the price feed's thread, never holds the trading engine up, and a planner problem
    (or crash) cannot reach the price service. If the previous run is still going, it does not start another."""

    def __init__(self, settings: Any, warn: Callable[[str], None] | None = None, popen: Callable = subprocess.Popen):
        self.s = settings
        self.warn = warn or (lambda m: log.warning(m))
        self.popen = popen
        self.proc = None
        self.started = 0

    def command(self) -> list[str]:
        return ["nice", "-n", "10", sys.executable, "-m", "planner", "run", "--pair", self.s.market.pair]

    def __call__(self, now: datetime) -> None:
        try:
            if self.proc is not None and self.proc.poll() is None:
                return
            root = Path(__file__).resolve().parents[1]
            self.proc = self.popen(self.command(), cwd=str(root), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   stdin=subprocess.DEVNULL, start_new_session=True, env=os.environ.copy())
            self.started += 1
        except Exception as e:                                  # noqa: BLE001  never stop the price service
            self.warn(f"Planner not started ({type(e).__name__}: {e}); trading is not affected.")
