"""The Structural Trade Planner workspace's data (the dashboard's STP tab; owner's brief of 17 November 2026).
READ ONLY and OBSERVE ONLY: it reads the planner's own files (planner.folder/<PAIR>/current.json,
recommendations.jsonl and issued.jsonl), the candle store and the trading engine's status file. It never writes
anything, never contacts IG, never imports any trading, order or trade-management code, and never works out a
forecast, a level or a recommendation of its own: every level, zone, destination and decision shown is the one the
planner recorded. The only figures worked out here are presentation (prices in normal GBP/USD notation, plain-English
labels for the planner's own codes) and the clearly labelled retrospective evaluation (what price did after each
recommendation, from finished 5-minute candles).

    GET /api/stp/overview                    the forecast, freshness, the live recommendation (if any), chart overlays
                                             and the technical evidence
    GET /api/stp/candles?tf=4h|1h|5m&limit=N&end=<UTC time>
                                             finished candles only (oldest first), chart (sell) prices
    GET /api/stp/history?page=1&size=20&q=&sort=created|status|direction&order=desc|asc
                                             the recommendations, one row per recommendation id (never merged)
    GET /api/stp/recommendation?id=STP-...   one recommendation: the snapshot as issued, every lifecycle event, and
                                             the retrospective outcome
    GET /api/stp/evaluation                  forecast evaluation for the observation period (no fills, no P&L)
    GET /api/stp/lib/<name>                  the tab's own script and style (static/stp/) and the chart library
                                             (static/vendor/, lightweight-charts 4.2.3, Apache-2.0); a fixed list
"""

from __future__ import annotations

import json
import re
import statistics
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

UTC = timezone.utc
LABEL = "OBSERVE ONLY — DOES NOT CONTROL TRADING"
STAGE_A_LABEL = "STAGE A — OBSERVE ONLY: STP TRACKS OPPORTUNITIES, DOES NOT CONTROL TRADING"
STAGE_B_LABEL = "STAGE B — STP AUTHORISES ENTRIES: "
NOT_READY_LABEL = ("STP_AUTHORISES_ENTRIES IS ON WITHOUT STP_OPPORTUNITIES AND STP_BIDIRECTIONAL: EVERY GATED ENTRY IS "
                   "REFUSED")


def mode(settings: Any) -> dict:
    """What STP does to trading now, from the switches (owner, 25 November 2026): Stage A observes (STP_OPPORTUNITIES
    on, STP_AUTHORISES_ENTRIES off); Stage B authorises the gated strategies' entries (all three on); otherwise the
    single-tracker observation as before. Shown on the STP tab, its card and the panel."""
    sw = getattr(settings, "switches", None)
    opp, bi = bool(getattr(sw, "stp_opportunities", False)), bool(getattr(sw, "stp_bidirectional", False))
    auth = bool(getattr(sw, "stp_authorises_entries", False))
    if auth and opp and bi:
        gated = ", ".join(getattr(getattr(settings, "stp_authorisation", None), "strategies", None) or [])
        return {"stage": "B", "authorises_entries": True, "label": STAGE_B_LABEL + gated.upper()}
    if auth:
        return {"stage": "B (not ready)", "authorises_entries": False, "label": NOT_READY_LABEL}
    if opp:
        return {"stage": "A", "authorises_entries": False, "label": STAGE_A_LABEL}
    return {"stage": None, "authorises_entries": False, "label": LABEL}
_STATIC = Path(__file__).resolve().parent / "static"
LIB = _STATIC / "vendor" / "lightweight-charts.standalone.production.js"
STATIC = {"lightweight-charts.js": LIB, "stp.js": _STATIC / "stp" / "stp.js", "stp.css": _STATIC / "stp" / "stp.css"}

TIMEFRAMES = {"5m": timedelta(minutes=5), "1h": timedelta(hours=1), "4h": timedelta(hours=4)}
DEFAULT_LIMIT = {"5m": 288, "1h": 240, "4h": 180}
MAX_LIMIT = 1000
MAX_PAGE_SIZE = 50
ID_RE = re.compile(r"^STP-[A-Z]{6}-\d{8}-\d{4}-\d{1,6}$")
LEVEL_RE = re.compile(r"^(?P<name>.*?) (?P<price>\d+(?:\.\d+)?)(?: \((?P<role>[^()]*)\))?$")

# The planner's own codes, with understandable labels (meaning unchanged).
STATUS_LABEL = {"CANDIDATE": "CREATED", "WAITING": "WAITING FOR ENTRY ZONE", "ACTIVE": "WATCH & WAIT",
                "COMPLETED": "COMPLETED", "INVALIDATED": "INVALIDATED", "SUPERSEDED": "SUPERSEDED"}
CONDITION_TEXT = {
    "CONTINUATION": "the trend is extending normally (new extreme, momentum confirming)",
    "EXHAUSTION": "a new extreme without momentum confirming it: the move shows exhaustion",
    "CORRECTION_LIKELY": "exhaustion, and no new extreme for several hours: a correction is likely",
    "CORRECTION_ACTIVE": "a correction against the 4-hour trend is under way, with the 4-hour structure intact",
    "REVERSAL_RISK": "momentum or the daily structure is turning against the 4-hour trend: no opportunity",
    "INDETERMINATE": "the evidence does not fit one condition (or indicators are still warming up): no opportunity",
}
DIRECTION_TEXT = {"BEARISH": "lower highs and lower lows on the 4-hour chart",
                  "BULLISH": "higher highs and higher lows on the 4-hour chart",
                  "TRANSITIONAL": "the 4-hour structure has been broken against itself but not yet reversed",
                  "NEUTRAL": "mixed or too few 4-hour swings",
                  "INDETERMINATE": "the 4-hour direction cannot be established"}
EVENT_LABEL = {"created": "CREATED", "waiting": "WAITING FOR ZONE", "active": "ACTIVE", "completed": "COMPLETED",
               "invalidated": "INVALIDATED", "superseded": "SUPERSEDED", "supported": "RE-CHECKED: STILL SUPPORTED",
               "changed": "RE-CHECKED: CHANGED", "closed beyond": "CLOSED BEYOND EDGE (RECORDED ONLY)",
               "reclaim": "RECLAIMED (RECORDED ONLY)", "wick sweep": "WICK SWEEP (RECORDED ONLY)",
               "failed breakout": "FAILED BREAKOUT (RECORDED ONLY)",
               "ambiguous": "AMBIGUOUS CANDLE (RECORDED ONLY)", "in zone at creation": "IN ZONE AT CREATION (RECORDED ONLY)",
               "kept": "RE-CHECKED: CONDITION UNCLASSIFIED, KEPT", "duplicate": "NOT ISSUED: DUPLICATE OF A COMPLETED ONE"}
# The chart's MARKET STRUCTURE view: the planner's level kinds that are significant structure (planner/zones.py PRIORITY);
# every other recorded level (hourly swings, sessions, round numbers, moving averages) is in FULL ANALYSIS only.
STRUCTURE_KINDS = ("4-hour swing", "daily swing", "daily pivot", "weekly pivot", "daily R/S", "weekly R/S",
                   "previous day high/low", "previous week high/low")
ENDED = ("COMPLETED", "INVALIDATED", "SUPERSEDED")


# ---- small helpers ---------------------------------------------------------------------------------------------

def _unquote(text: str) -> str:
    """%XX and + decoding for a query value (no web library is imported anywhere outside ig/)."""
    raw, i, t = bytearray(), 0, text.replace("+", " ")
    while i < len(t):
        if t[i] == "%" and re.fullmatch(r"[0-9A-Fa-f]{2}", t[i + 1:i + 3]):
            raw.append(int(t[i + 1:i + 3], 16))
            i += 3
        else:
            raw.extend(t[i].encode())
            i += 1
    return raw.decode("utf-8", "replace")


def parse_qs(query: str, keep_blank_values: bool = False, max_num_fields: int = 10) -> dict[str, list[str]]:
    """name=value pairs after the "?", decoded; at most max_num_fields of them (more: the rest are ignored)."""
    out: dict[str, list[str]] = {}
    for part in query.split("&")[:max_num_fields]:
        name, eq, value = part.partition("=")
        if not name or (not value and not keep_blank_values):
            continue
        out.setdefault(_unquote(name), []).append(_unquote(value))
    return out


def _parse(t: str | None) -> datetime | None:
    if not t:
        return None
    try:
        return datetime.fromisoformat(str(t).replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def _iso(t: datetime | None) -> str | None:
    return None if t is None else t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class Prices:
    """IG's points (13213.5) to normal GBP/USD notation (1.32135), and pips."""

    def __init__(self, settings: Any):
        self.scale = Decimal(settings.market.price_scale)
        self.pip = Decimal(str(settings.market.pip_size))
        self.places = max(0, -self.pip.as_tuple().exponent) + 1           # GBPUSD: 5

    def real(self, points: Any) -> str | None:
        if points is None or points == "":
            return None
        try:
            v = Decimal(str(points)) / self.scale
        except (InvalidOperation, ValueError):
            return None
        return f"{v:.{self.places}f}"

    def num(self, points: Any) -> float | None:
        r = self.real(points)
        return None if r is None else float(r)

    def pips(self, points: Any) -> float | None:
        try:
            return float((Decimal(str(points)) / self.scale / self.pip).quantize(Decimal("0.1")))
        except (InvalidOperation, ValueError, TypeError):
            return None

    def zone(self, low: Any, high: Any) -> str:
        return f"{self.real(low)}–{self.real(high)}"

    def text(self, s: str | None) -> str | None:
        """A planner sentence with its prices (13213.5, 13200) written as 1.32135, 1.32000. Only numbers of the
        pair's points size (4-5 digits before an optional decimal) are converted; times and counts are left alone. Both
        ends of a range are converted ("13193.2-13202.5"), as well as "13193.2–13202.5"; a minus sign not preceded by a
        digit still keeps its number as it is."""
        if not s:
            return s
        lo, hi = 5000, 50000                              # GBPUSD points; years (2026) and counts are left alone
        def rep(m: re.Match) -> str:
            try:
                v = Decimal(m.group(0))
            except InvalidOperation:
                return m.group(0)
            if lo <= v < hi and self.scale == 10000:
                return self.real(v) or m.group(0)
            return m.group(0)
        return re.sub(r"(?<![\d:.])(?<!(?<!\d)-)\d{4,5}(?:\.\d+)?(?![\d:])", rep, s)


def read_state(settings: Any) -> dict | None:
    try:
        st = json.loads((Path(settings.planner.folder) / settings.market.pair / "current.json").read_text())
        return st if isinstance(st, dict) and st.get("pair") == settings.market.pair else None
    except (FileNotFoundError, ValueError, OSError):
        return None


def _jsonl(path: Path) -> list[dict]:
    try:
        lines = path.read_text().splitlines()
    except (FileNotFoundError, OSError):
        return []
    out = []
    for line in lines:
        try:
            e = json.loads(line)
        except ValueError:
            continue                                     # a damaged line is left out, never guessed
        if isinstance(e, dict):
            out.append(e)
    return out


def read_events(settings: Any) -> list[dict]:
    return _jsonl(Path(settings.planner.folder) / settings.market.pair / "recommendations.jsonl")


def read_issued(settings: Any) -> dict[str, dict]:
    return {e["id"]: e for e in _jsonl(Path(settings.planner.folder) / settings.market.pair / "issued.jsonl")
            if isinstance(e.get("id"), str)}


def _store(settings: Any):
    from prices.store import CandleStore
    return CandleStore(settings.candles.folder, settings.candles.compress_after_days)     # as planner/__main__.py


def _hours(settings: Any):
    from prices.calendar import MarketHours
    return MarketHours(settings.market_hours)


# ---- freshness -------------------------------------------------------------------------------------------------

def freshness(settings: Any, st: dict | None, now: datetime) -> dict:
    """What the planner's timestamps say, by the planner's own rules: it runs after every new 5-minute candle and
    re-plans when a new hourly candle has finished. Opening the page between hourly analyses is not stale."""
    if st is None:
        return {"state": "UNAVAILABLE", "label": "PLANNER UNAVAILABLE",
                "detail": "The planner has not written a forecast (it is off, or has not run yet)."}
    last_run, last_an = _parse(st.get("last_run_utc")), _parse(st.get("last_analysis_utc"))
    validated = _parse(st.get("validated_h1_end"))
    out = {"last_run_utc": st.get("last_run_utc"), "last_analysis_utc": st.get("last_analysis_utc"),
           "market_data_utc": (st.get("last_plan") or {}).get("market_data_utc"), "data_fresh": st.get("data_fresh"),
           "reasons": list(st.get("not_current_reasons") or []), "validated_h1_end": st.get("validated_h1_end"),
           "recommendation_current": bool(st.get("current"))}
    try:
        market_open = _hours(settings).is_open(now)
    except Exception:                                    # noqa: BLE001  no calendar: judge by the planner's own data only
        market_open = True
    run_age = (now - last_run).total_seconds() / 60 if last_run else None
    next_due = (validated + timedelta(hours=1)) if validated else None
    out["next_analysis_due_utc"] = _iso(next_due) if market_open else None
    out["market_open"] = market_open
    if not market_open:
        out |= {"state": "MARKET_CLOSED", "label": "MARKET CLOSED",
                "detail": "The market is closed: the latest analysis stands until the next candles after it reopens."}
    elif st.get("data_fresh") is False:
        out |= {"state": "STALE", "label": "STALE DATA",
                "detail": "The planner's own freshness rule says the market data is out of date"
                          + (": " + "; ".join(out["reasons"]) if out["reasons"] else ".")}
    elif run_age is not None and run_age > 20:
        out |= {"state": "STALE", "label": "PLANNER NOT RUNNING",
                "detail": f"The planner last ran {int(run_age)} minutes ago; it normally runs after every 5-minute candle."}
    elif next_due is not None and now > next_due + timedelta(minutes=10):
        out |= {"state": "AWAITING_REFRESH", "label": "ANALYSIS OVERDUE",
                "detail": "The hourly re-analysis has not happened yet for the latest finished hourly candle."}
    else:
        out |= {"state": "CURRENT", "label": "CURRENT",
                "detail": "Data is fresh. The structural analysis is re-done when each hourly candle finishes"
                          + (f"; the next is due at {next_due.strftime('%H:%M')} UTC." if next_due else ".")}
    return out


# ---- the forecast in words ---------------------------------------------------------------------------------------

def movement_text(direction: str | None, opportunity: str | None, expected: str | None) -> str | None:
    """The planner's expected movement ("UP into resistance, then DOWN") in plain words. Nothing is added that the
    planner did not say: a direction sequence only, no timing, no price path."""
    if not expected:
        return None
    pull = opportunity == "healthy-trend pullback"
    if direction == "BEARISH":
        return ("Pullback (rally) towards resistance within the downtrend, followed by potential bearish continuation."
                if pull else "Corrective rally towards resistance, followed by potential bearish continuation.")
    if direction == "BULLISH":
        return ("Pullback (dip) towards support within the uptrend, followed by potential bullish continuation."
                if pull else "Corrective dip towards support, followed by potential bullish continuation.")
    return expected


def explanation(st: dict | None, fresh: dict, prices: Prices) -> dict:
    """Why there is no recommendation, from the planner's own recorded reasons (never invented):
       A  a directional forecast, but no valid entry (the plan's no_recommendation reason);
       B  no dominant direction;
       C  unavailable or stale;
       D  the last analysis issued a recommendation that has since ended; a new one can only come at the next
          hourly analysis."""
    if st is None or fresh["state"] == "UNAVAILABLE":
        return {"scenario": "C", "text": "Structural analysis is unavailable: " + fresh.get("detail", ""), "planner_reason": None}
    if fresh["state"] == "STALE":
        return {"scenario": "C", "text": "Structural analysis is not current because the required market data is stale. "
                + fresh["detail"], "planner_reason": None}
    p = st.get("last_plan") or {}
    reason = p.get("no_recommendation")
    d = p.get("dominant_direction")
    if d not in ("BEARISH", "BULLISH"):
        return {"scenario": "B", "text": "Current structural evidence is insufficient to establish a dominant direction "
                f"(4-hour direction: {d or 'unknown'}).", "planner_reason": prices.text(reason)}
    if reason:
        return {"scenario": "A", "text": f"The dominant structure is {d.lower()}, but no structural entry currently meets "
                "the planner's requirements.", "planner_reason": prices.text(reason)}
    held = st.get("not_issued")
    if held and held.get("time_utc") == p.get("as_of_utc"):
        return {"scenario": "A", "text": f"The dominant structure is {d.lower()}; the opportunity found repeats one that "
                "has already reached its primary destination, so it was not issued again.",
                "planner_reason": prices.text(held.get("why"))}
    recent = (st.get("recent") or [None])[0]
    last_an = _parse(st.get("last_analysis_utc"))
    if recent and _parse(recent.get("ended_utc")) and last_an and _parse(recent["ended_utc"]) >= last_an - timedelta(seconds=5):
        due = fresh.get("next_analysis_due_utc")
        return {"scenario": "D", "text": (f"The {_hm(last_an)} UTC analysis issued {recent['trade']} "
                f"{prices.zone(*recent['zone'])} ({recent['id']}); it ended at {_hm(_parse(recent['ended_utc']))} UTC as "
                f"{recent['status']}. The planner only issues a new recommendation at an hourly analysis"
                + (f" (next due {_hm(_parse(due))} UTC)." if due else ".")),
                "planner_reason": prices.text(recent.get("why"))}
    return {"scenario": "A", "text": f"The dominant structure is {d.lower()}, but there is no live recommendation.",
            "planner_reason": None}


def _hm(t: datetime | None) -> str:
    return t.strftime("%H:%M") if t else "?"


# ---- chart overlays: only levels the planner recorded ----------------------------------------------------------

def level_group(name: str, kind: str | None = None) -> str:
    k = (kind or "").lower()
    if k:
        return {"daily pivot": "daily_pivot", "daily r/s": "daily_pivot", "weekly pivot": "weekly_pivot",
                "weekly r/s": "weekly_pivot", "4-hour swing": "h4_swing", "hourly swing": "h1", "daily swing": "daily_sr",
                "previous day high/low": "daily_sr", "previous week high/low": "weekly_sr", "psychological": "round",
                "session high/low": "session", "moving average": "ma"}.get(k, "other")
    n = name.lower()
    if "pivot" in n or re.search(r"\b[rs][123]\b", n):
        return "weekly_pivot" if n.startswith("weekly") else "daily_pivot"
    if n.startswith("4-hour swing"):
        return "h4_swing"
    if n.startswith("hourly") or n.startswith("h1 "):
        return "h1"
    if n.startswith("daily swing") or "previous day" in n:
        return "daily_sr"
    if "week" in n:
        return "weekly_sr"
    return "other"


def parse_level(label: str, prices: Prices, source: str) -> dict | None:
    m = LEVEL_RE.match(str(label).strip())
    if not m:
        return None
    return {"price": prices.num(m["price"]), "price_text": prices.real(m["price"]), "name": m["name"],
            "role": m["role"] or "", "group": level_group(m["name"]), "source": source}


def _zone_out(z: dict, prices: Prices, kind: str, title: str) -> dict:
    levels = z.get("levels") or []
    labels = [(f"{m['name']} {m['price']}" + (f" ({m['role']})" if m.get("role") else "")) if isinstance(m, dict) else m
              for m in levels]
    return {"kind": kind, "title": title, "low": prices.num(z.get("low")), "high": prices.num(z.get("high")),
            "text": prices.zone(z.get("low"), z.get("high")), "class": z.get("class"), "families": z.get("families", []),
            "levels": [prices.text(x) for x in labels]}


def structure_levels(structure: dict | None, prices: Prices) -> dict | None:
    """Every level and zone of a recorded structural snapshot (planner/assess.py structure_snapshot), each level tagged
    with the chart view it belongs to: "structure" (significant: 4-hour and daily swings, daily and weekly levels) or
    "full" (everything else). Values exactly as recorded; nothing recalculated."""
    if not isinstance(structure, dict) or not isinstance(structure.get("levels"), list):
        return None
    levels = []
    for m in structure["levels"]:
        if not isinstance(m, dict) or m.get("price") is None:
            continue
        kind = m.get("kind") or ""
        levels.append({"price": prices.num(m["price"]), "price_text": prices.real(m["price"]), "name": m.get("name", ""),
                       "role": m.get("role", ""), "kind": kind, "timeframe": m.get("timeframe"), "family": m.get("family"),
                       "fixed": m.get("fixed"), "group": level_group(m.get("name", ""), kind),
                       "tier": "structure" if kind in STRUCTURE_KINDS else "full", "source": "structural snapshot"})
    zones = [(_zone_out(z, prices, "zone", f"{z.get('class', '')} zone") | {"tier": "structure" if z.get("class") in ("Major", "Moderate") else "full"})
             for z in structure.get("zones") or [] if isinstance(z, dict)]
    return {"levels": sorted(levels, key=lambda x: x["price"] or 0), "zones": zones, "complete": True}


def overlays(plan: dict | None, rec: dict | None, prices: Prices) -> dict:
    """The structural levels and zones of the planner's latest analysis, and the live recommendation's plan. With the
    analysis's full structural snapshot when it has one (since 18 November 2026); otherwise only the levels inside the
    zones the analysis considered (as before)."""
    plan = plan or {}
    full = structure_levels(plan.get("structure"), prices)
    if full is not None:
        return full | {"plan": plan_lines(rec, prices) if rec else None}
    zones, levels, seen = [], [], set()

    def add_levels(z: dict, source: str):
        for m in z.get("levels") or []:
            label = (f"{m['name']} {m['price']}" + (f" ({m['role']})" if m.get("role") else "")) if isinstance(m, dict) else m
            lv = parse_level(label, prices, source)
            if lv and (lv["name"], lv["price"]) not in seen:
                seen.add((lv["name"], lv["price"]))
                levels.append(lv | {"tier": "full" if lv["group"] in ("h1", "other") else "structure"})

    for z in plan.get("candidates") or []:
        zones.append(_zone_out(z, prices, "candidate", f"{z.get('class', '')} zone") | {"tier": "structure"})
        add_levels(z, "candidate zone")
    for k, d in (plan.get("destinations") or {}).items():
        if d and d.get("zone"):
            add_levels(d["zone"], f"{k} destination zone")
    if plan.get("entry_zone"):
        add_levels(plan["entry_zone"], "entry zone")
    o = plan.get("observations") or {}
    for key, name in (("vs_daily_pivot", "daily pivot"), ("vs_weekly_pivot", "weekly pivot")):
        m = re.search(r"(\d{4,5}(?:\.\d)?)\s*$", str(o.get(key) or ""))
        if m and (name, prices.num(m[1])) not in seen:
            seen.add((name, prices.num(m[1])))
            levels.append({"price": prices.num(m[1]), "price_text": prices.real(m[1]), "name": name, "role": "",
                           "group": level_group(name), "source": "observations", "tier": "structure"})
    out = {"levels": sorted(levels, key=lambda x: x["price"] or 0), "zones": zones, "plan": None, "complete": False}
    if rec:
        out["plan"] = plan_lines(rec, prices)
    return out


def plan_lines(rec: dict, prices: Prices) -> dict:
    """The recommendation's entry zone, destinations and invalidation, exactly as recorded."""
    z, d, inv = rec.get("entry_zone") or {}, rec.get("destinations") or {}, rec.get("invalidation") or {}
    dest = {}
    for k in ("intermediate", "primary", "extended"):
        x = d.get(k)
        if x and x.get("price") is not None:
            dest[k] = {"price": prices.num(x["price"]), "text": prices.real(x["price"]),
                       "zone": _zone_out(x["zone"], prices, k, k) if x.get("zone") else None}
    lines = []
    if inv.get("zone_break_close"):
        lines.append({"price": prices.num(inv["zone_break_close"]), "text": prices.real(inv["zone_break_close"]),
                      "label": f"Invalidation: {inv.get('zone_break_timeframe', '1h')} close beyond"})
    if inv.get("structure_break_close"):
        lines.append({"price": prices.num(inv["structure_break_close"]), "text": prices.real(inv["structure_break_close"]),
                      "label": f"Structure break: {inv.get('structure_break_timeframe', '4h')} close beyond"})
    ref = rec.get("reference_entry") or {}
    return {"trade": rec.get("trade"), "entry_zone": {"low": prices.num(z.get("low")), "high": prices.num(z.get("high")),
                                                      "text": prices.zone(z.get("low"), z.get("high")), "class": z.get("class")},
            "reference": {"price": prices.num(ref.get("price")), "text": prices.real(ref.get("price")), "level": ref.get("level")},
            "destinations": dest, "invalidation": lines,
            "invalidation_conditions": [prices.text(c) for c in inv.get("conditions") or []]}


# ---- the overview ----------------------------------------------------------------------------------------------

def current_price(settings: Any, prices: Prices) -> dict | None:
    try:
        st = json.loads((Path(settings.dashboard.status_folder) / settings.market.pair / "status.json").read_text())
        p = st.get("price") or {}
        side = "bid" if settings.chart.price == "sell" else "offer"
        return {"price": prices.num(p.get(side)), "text": prices.real(p.get(side)), "side": side,
                "bid": prices.real(p.get("bid")), "offer": prices.real(p.get("offer")), "time_utc": p.get("time_utc")}
    except (FileNotFoundError, ValueError, OSError, AttributeError):
        return None


def card(settings: Any, now: datetime) -> dict:
    """The main dashboard's compact summary card."""
    prices = Prices(settings)
    st = read_state(settings)
    fresh = freshness(settings, st, now)
    if st is None:
        return {"available": False, "freshness": fresh, "label": mode(settings)["label"], "stp_mode": mode(settings)}
    p, rec = st.get("last_plan") or {}, st.get("recommendation")
    return {"available": True, "label": mode(settings)["label"], "stp_mode": mode(settings), "pair": settings.market.pair,
            "freshness": fresh,
            "dominant_direction": p.get("dominant_direction"), "condition": p.get("condition"),
            "expected_movement": movement_text(p.get("dominant_direction"), p.get("opportunity"), p.get("expected_movement")),
            "status": STATUS_LABEL.get(rec["status"], rec["status"]) if rec else "NO RECOMMENDATION",
            "trade": rec.get("trade") if rec else None,
            "zone": prices.zone(rec["entry_zone"]["low"], rec["entry_zone"]["high"]) if rec else None,
            "last_analysis_utc": st.get("last_analysis_utc")}


def overview(settings: Any, now: datetime) -> dict:
    prices = Prices(settings)
    st = read_state(settings)
    fresh = freshness(settings, st, now)
    out: dict = {"ok": True, "label": mode(settings)["label"], "stp_mode": mode(settings), "pair": settings.market.pair, "pair_text": _pair_text(settings.market.pair),
                 "served_utc": _iso(now), "freshness": fresh, "price": current_price(settings, prices),
                 "available": st is not None}
    if st is None:
        out["explanation"] = explanation(None, fresh, prices)
        return out
    p, rec = st.get("last_plan") or {}, st.get("recommendation")
    first = binds_first(st)
    if first:                       # Phase 2 C-7: with several live, the card shows the one an entry binds first
        rec = first[0]
    d = p.get("dominant_direction")
    out["forecast"] = {
        "as_of_utc": p.get("as_of_utc"), "market_data_utc": p.get("market_data_utc"),
        "dominant_direction": d, "direction_text": DIRECTION_TEXT.get(d),
        "condition": p.get("condition"), "condition_text": CONDITION_TEXT.get(p.get("condition")),
        "opportunity": p.get("opportunity"), "expected_movement": p.get("expected_movement"),
        "movement_text": movement_text(d, p.get("opportunity"), p.get("expected_movement")),
        "forecast_trade": p.get("trade"),
        "h4_last_swing": ({"kind": p["h4_last_swing"]["kind"], "price": prices.num(p["h4_last_swing"]["price"]),
                           "text": prices.real(p["h4_last_swing"]["price"]), "candle_utc": p["h4_last_swing"]["candle_utc"]}
                          if p.get("h4_last_swing") else None)}
    if rec:
        out["status"] = {"code": rec["status"], "label": STATUS_LABEL.get(rec["status"], rec["status"])}
        out["opportunity_text"] = rec["trade"]
        out["recommendation"] = recommendation_card(rec, st, prices)
        out["explanation"] = None
    else:
        out["status"] = {"code": "NONE", "label": "NO RECOMMENDATION"}
        out["opportunity_text"] = "NO CURRENT OPPORTUNITY"
        out["recommendation"] = None
        out["explanation"] = explanation(st, fresh, prices)
    out["overlays"] = overlays(p, rec, prices)
    out["technical"] = technical(st, p, prices)
    if isinstance(st.get("opportunities"), list):          # STP_OPPORTUNITIES (owner, 24 November 2026; WP-5)
        out["opportunities"] = opportunities(st, prices, mode(settings)["authorises_entries"])
        live = [o for o in st["opportunities"] if isinstance(o, dict) and o.get("status") in ("WAITING", "ACTIVE")]
        out["live_count"] = len(live)
        out["binds_first"] = {o["trade"]: o["id"] for o in reversed(first)} if first else {}
    out["recent"] = [{"id": x["id"], "trade": x["trade"], "zone": prices.zone(*x["zone"]), "status": x["status"],
                      "why": prices.text(x.get("why")), "created_utc": x.get("created_utc"), "ended_utc": x.get("ended_utc")}
                     for x in st.get("recent") or [] if isinstance(x, dict) and x.get("zone")]
    return out


def binds_first(st: dict) -> list[dict]:
    """The live opportunities an authorisation binds first, one per direction (the oldest lineage, then the oldest
    opportunity: stp/authorise.py), oldest first. Display only."""
    live = [o for o in st.get("opportunities") or [] if isinstance(o, dict) and o.get("status") in ("WAITING", "ACTIVE")]
    out = {}
    for o in sorted(live, key=lambda o: (o.get("lineage_created_utc") or o.get("created_utc") or "", o.get("created_utc") or "")):
        out.setdefault(o.get("trade"), o)
    return sorted(out.values(), key=lambda o: o.get("lineage_created_utc") or o.get("created_utc") or "")


def test_state(st: dict, o: dict) -> dict:
    """The lineage's D-25 state (planner/lineage.py): tests counted, whether armed (the next touch is a new test), and
    the tests already consumed by a confirmed trade (STP execution acknowledgements)."""
    L = (st.get("lineages") or {}).get(o.get("lineage") or "") or {}
    t = L.get("tests") or o.get("tests") or {}
    ev = t.get("events") or []
    n = sum(1 for e in ev if e[1] == "test")
    armed = not ev or ev[-1][1] == "rearm"
    consumed = sorted(int(k) for k, v in (L.get("consumed") or {}).items() if v)
    return {"tests_counted": n, "armed": armed, "test_now": n + 1 if armed else max(n, 1), "consumed": consumed,
            "uncertain_hours": len(t.get("uncertain") or [])}


def opportunities(st: dict, prices: Prices, authorising: bool = True) -> list[dict]:
    """Every opportunity STP is tracking (STP_OPPORTUNITIES; planner/opportunities.py), newest first, read only:
    WAITING and Watch & Wait authorise (while STP_AUTHORISES_ENTRIES is on); BROKEN waits for the failed-breakout
    window (OD-31) and authorises nothing. `authorising`: whether STP authorises entries now (Stage B, mode()); in
    Stage A nothing authorises a trade, so "authorises" is false for every row."""
    out = []
    for o in sorted((x for x in st.get("opportunities") or [] if isinstance(x, dict)),
                    key=lambda x: x.get("created_utc") or "", reverse=True):
        z = o.get("entry_zone") or {}
        inv = o.get("invalidation") or {}
        prim = ((o.get("destinations") or {}).get("primary") or {}).get("price")
        out.append({"id": o.get("id"), "trade": o.get("trade"), "status": o.get("status"),
                    "label": "Watch & Wait" if o.get("status") == "ACTIVE" else (o.get("status") or "").capitalize(),
                    "authorises": authorising and o.get("status") in ("WAITING", "ACTIVE"),
                    "zone": prices.zone(z.get("low"), z.get("high")), "zone_class": z.get("class"),
                    "primary": prices.real(prim) if prim is not None else None,
                    "zone_break": prices.real(inv.get("zone_break_close")) if inv.get("zone_break_close") else None,
                    "relation_to_h4": o.get("relation_to_h4"), "created_utc": o.get("created_utc"),
                    "lineage": o.get("lineage"), "broken_utc": (o.get("broken") or {}).get("broken_utc"),
                    "test": test_state(st, o), "executions": len(o.get("executions") or []),
                    "binds_first": any(x.get("id") == o.get("id") for x in binds_first(st)),
                    "data_gaps": [g for g in o.get("data_gaps") or [] if g.get("status") != "reconciled"]})
    return out


def _pair_text(pair: str) -> str:
    return f"{pair[:3]}/{pair[3:]}" if len(pair) == 6 else pair


def recommendation_card(rec: dict, st: dict | None, prices: Prices) -> dict:
    z = rec.get("entry_zone") or {}
    ref = rec.get("reference_entry") or {}
    return {"id": rec["id"], "instrument": rec.get("instrument"), "trade": rec.get("trade"),
            "dominant_direction": rec.get("dominant_direction"), "condition": rec.get("condition"),
            "opportunity": rec.get("opportunity"), "status": rec.get("status"),
            "status_label": STATUS_LABEL.get(rec.get("status"), rec.get("status")),
            "status_reason": prices.text(rec.get("status_reason")),
            "entry_zone": prices.zone(z.get("low"), z.get("high")), "zone_class": z.get("class"),
            "families": z.get("families", []), "tests": z.get("tests"),
            "reference": f"{prices.real(ref.get('price'))} ({ref.get('level')})" if ref else None,
            "reachability": rec.get("reachability"), "selection_reason": prices.text(rec.get("selection_reason")),
            "evidence": [prices.text(f"{m['name']} {m['price']}" + (f" ({m['role']})" if m.get("role") else ""))
                         for m in z.get("levels") or [] if isinstance(m, dict)],
            "plan": plan_lines(rec, prices), "created_utc": rec.get("created_utc"),
            "last_updated_utc": (st or {}).get("last_analysis_utc"), "current": bool((st or {}).get("current")),
            "not_current_reasons": (st or {}).get("not_current_reasons", [])}


def technical(st: dict, p: dict, prices: Prices) -> dict:
    o = p.get("observations") or {}
    band = o.get("h4_band") or {}
    return {
        "direction_evidence": [prices.text(x) for x in p.get("direction_evidence") or []],
        "condition_evidence": [prices.text(x) for x in p.get("condition_evidence") or []],
        "daily_structure": prices.text(o.get("daily_structure")),
        "ema": {"stack": o.get("h4_ema_stack"), "ema100": prices.real(o.get("h4_ema100")),
                "ema200": prices.real(o.get("h4_ema200")) if _isnum(o.get("h4_ema200")) else o.get("h4_ema200"),
                "ema100_slope_pips": o.get("h4_ema100_slope_pips")},
        "rsi3": o.get("h4_rsi"), "macd": o.get("h4_macd"),
        "bollinger": {"upper": prices.real(band.get("upper")), "middle": prices.real(band.get("middle")),
                      "lower": prices.real(band.get("lower")), "width_pips": band.get("width_pips"), "position": band.get("close")},
        "adr_pips": o.get("adr_pips"), "today_range_pips": o.get("today_range_pips"), "today_range_adr": o.get("today_range_adr"),
        "remaining_room_pips": o.get("remaining_room_pips"),
        "vs_daily_pivot": prices.text(o.get("vs_daily_pivot")), "vs_weekly_pivot": prices.text(o.get("vs_weekly_pivot")),
        "direction_rule_5m": {k: prices.text(v) for k, v in (o.get("direction_rule_5m") or {}).items()},
        "conflicts": [prices.text(x) for x in (p.get("direction_evidence") or []) if str(x).startswith("warning")],
        "warming_up": p.get("warming_up", []),
        "threshold_misses": [m.get("note") for m in p.get("threshold_misses", []) if isinstance(m, dict)],
        "impulse": {"pips": o.get("impulse_pips"), "adr": o.get("impulse_adr")},
        "reward_to_invalidation": o.get("reward_to_invalidation"),
        "uk_time": o.get("uk_time"), "big_news_today": o.get("big_news_today"),
        "selection_reason": prices.text(p.get("selection_reason")), "no_recommendation": prices.text(p.get("no_recommendation")),
        "alternative": _zone_out(p["alternative"], prices, "alternative", "alternative") if p.get("alternative") else None,
        "candidates": [(_zone_out(z, prices, "candidate", "candidate") | {"reachability": prices.text(z.get("reachability")),
                        "distance_pips": z.get("distance_pips"), "chosen": bool(z.get("chosen")),
                        "rejected_because": prices.text(z.get("rejected_because"))}) for z in p.get("candidates") or []],
        "freshness_reasons": st.get("not_current_reasons", []), "data_fresh": st.get("data_fresh"),
        "market_data_utc": p.get("market_data_utc"),
    }


def _isnum(x: Any) -> bool:
    try:
        Decimal(str(x))
        return True
    except (InvalidOperation, ValueError):
        return False


# ---- candles -----------------------------------------------------------------------------------------------------

def candles(settings: Any, query: str, now: datetime, store: Any = None) -> tuple[int, dict]:
    q = parse_qs(query, keep_blank_values=False, max_num_fields=10)
    tf = (q.get("tf") or ["1h"])[0]
    if tf not in TIMEFRAMES:
        return 400, {"ok": False, "error": "tf must be one of 5m, 1h, 4h"}
    try:
        limit = int((q.get("limit") or [DEFAULT_LIMIT[tf]])[0])
    except ValueError:
        return 400, {"ok": False, "error": "limit must be a whole number"}
    if not 1 <= limit <= MAX_LIMIT:
        return 400, {"ok": False, "error": f"limit must be 1 to {MAX_LIMIT}"}
    end = now
    if q.get("end"):
        end = _parse(q["end"][0])
        if end is None:
            return 400, {"ok": False, "error": "end must be a UTC time (YYYY-MM-DDTHH:MM:SSZ)"}
        end = min(end, now)
    store = store or _store(settings)
    prices = Prices(settings)
    side = settings.chart.price
    span = TIMEFRAMES[tf] * limit
    start = end - span * 2 - timedelta(days=4)            # room for weekends and gaps
    got = [c for c in store.read_range(tf, start, end) if c.end <= now and c.start < end]   # finished candles only
    got = got[-limit:]
    rows = [{"t": int(c.start.timestamp()), "o": prices.num(getattr(c, f"{side}_open")),
             "h": prices.num(getattr(c, f"{side}_high")), "l": prices.num(getattr(c, f"{side}_low")),
             "c": prices.num(getattr(c, f"{side}_close"))} | ({"partial": True} if c.parts < c.expected_parts else {})
            for c in got]
    return 200, {"ok": True, "tf": tf, "side": side, "candles": rows, "count": len(rows),
                 "first_utc": _iso(got[0].start) if got else None, "last_end_utc": _iso(got[-1].end) if got else None,
                 "note": "finished candles only; the live, unfinished candle is not drawn (the current price line shows it)"}


# ---- recommendation history ----------------------------------------------------------------------------------

def recommendations(settings: Any, st: dict | None = None, events: list | None = None) -> list[dict]:
    """One record per recommendation id, from the planner's append-only history; never merged by zone."""
    events = read_events(settings) if events is None else events
    st = read_state(settings) if st is None else st
    issued = read_issued(settings)
    live = (st or {}).get("recommendation")
    recs: dict[str, dict] = {}
    for i, e in enumerate(events):
        rid = e.get("id")
        if not rid:
            continue
        r = recs.setdefault(rid, {"id": rid, "events": [], "created": None})
        r["events"].append(e | {"seq": i})
        if e.get("event") == "created":
            r["created"] = e
    out = []
    for rid, r in recs.items():
        ev = r["events"]
        status = next((x["status"] for x in reversed(ev) if x.get("status")), None)
        if live and live.get("id") == rid:
            status = live.get("status", status)
        c = r["created"] or {}
        plan = c.get("plan") or {}
        snap = issued.get(rid)
        end = next((x for x in ev if x.get("event") in ("completed", "invalidated", "superseded")), None)
        active = next((x for x in ev if x.get("event") == "active"), None)
        out.append({"id": rid, "created_utc": c.get("time_utc") or ev[0].get("time_utc"),
                    "trade": (snap or {}).get("trade") or plan.get("trade"),
                    "direction": (snap or {}).get("dominant_direction") or plan.get("direction"),
                    "condition": (snap or {}).get("condition") or plan.get("condition"),
                    "opportunity": (snap or {}).get("opportunity") or plan.get("opportunity"),
                    "zone": (snap or {}).get("entry_zone") or plan.get("zone"),
                    "primary": (((snap or {}).get("destinations") or {}).get("primary") or {}).get("price") or plan.get("primary"),
                    "status": status, "outcome": end.get("event").upper() if end else None,
                    "outcome_reason": end.get("why") if end else None, "ended_utc": end.get("time_utc") if end else None,
                    "activated_utc": active.get("time_utc") if active else None,
                    "events": ev, "snapshot": snap, "plan_summary": plan, "created": r["created"],
                    "live": bool(live and live.get("id") == rid), "live_record": live if live and live.get("id") == rid else None})
    return out


def _row(r: dict, prices: Prices) -> dict:
    z = r.get("zone") or {}
    return {"id": r["id"], "created_utc": r["created_utc"], "trade": r["trade"], "direction": r["direction"],
            "opportunity": r["opportunity"], "zone": prices.zone(z.get("low"), z.get("high")) if z else None,
            "zone_low": prices.num(z.get("low")), "zone_high": prices.num(z.get("high")),
            "primary": prices.real(r["primary"]), "status": r["status"],
            "status_label": STATUS_LABEL.get(r["status"], r["status"]), "outcome": r["outcome"],
            "reason": prices.text(r["outcome_reason"]), "ended_utc": r["ended_utc"], "live": r["live"]}


def history(settings: Any, query: str) -> tuple[int, dict]:
    q = parse_qs(query, max_num_fields=10)
    try:
        page = int((q.get("page") or ["1"])[0])
        size = int((q.get("size") or ["20"])[0])
    except ValueError:
        return 400, {"ok": False, "error": "page and size must be whole numbers"}
    if page < 1 or not 1 <= size <= MAX_PAGE_SIZE:
        return 400, {"ok": False, "error": f"page must be 1 or more; size 1 to {MAX_PAGE_SIZE}"}
    sort = (q.get("sort") or ["created"])[0]
    order = (q.get("order") or ["desc"])[0]
    if sort not in ("created", "status", "direction", "trade") or order not in ("asc", "desc"):
        return 400, {"ok": False, "error": "sort must be created, status, direction or trade; order asc or desc"}
    text = (q.get("q") or [""])[0].strip().lower()[:60]
    prices = Prices(settings)
    rows = [_row(r, prices) for r in recommendations(settings)]
    if text:
        rows = [r for r in rows if any(text in str(r.get(k) or "").lower()
                                       for k in ("id", "trade", "direction", "opportunity", "zone", "status", "outcome", "reason"))]
    key = {"created": lambda r: r["created_utc"] or "", "status": lambda r: (r["status"] or "", r["created_utc"] or ""),
           "direction": lambda r: (r["direction"] or "", r["created_utc"] or ""),
           "trade": lambda r: (r["trade"] or "", r["created_utc"] or "")}[sort]
    rows.sort(key=key, reverse=order == "desc")
    total = len(rows)
    chunk = rows[(page - 1) * size: page * size]
    return 200, {"ok": True, "page": page, "size": size, "total": total, "pages": max(1, -(-total // size)),
                 "sort": sort, "order": order, "q": text, "rows": chunk}


def creation_card(r: dict, prices: Prices) -> dict:
    """What was known when the recommendation was created: the full snapshot (issued.jsonl) when it was kept,
    otherwise the summary in the "created" event. Never the live record's later updates, never anything later."""
    snap = r["snapshot"]
    if snap:
        return {"source": "snapshot", "note": "the full recommendation exactly as issued (issued.jsonl)",
                "card": recommendation_card(snap, None, prices) | {"status": "CANDIDATE", "status_label": "CREATED"}}
    ps = r["plan_summary"] or {}
    z = ps.get("zone") or {}
    ref = ps.get("reference") or {}
    return {"source": "summary",
            "note": "only the summary the planner kept in its history: the full snapshot (intermediate and extended "
                    "destinations, invalidation conditions) was not recorded for recommendations issued before "
                    "issued.jsonl existed",
            "card": {"id": r["id"], "trade": ps.get("trade"), "dominant_direction": ps.get("direction"),
                     "condition": ps.get("condition"), "opportunity": ps.get("opportunity"),
                     "entry_zone": prices.zone(z.get("low"), z.get("high")) if z else None,
                     "zone_class": z.get("class"), "families": z.get("families", []),
                     "evidence": [prices.text(x) for x in z.get("levels", [])],
                     "reference": f"{prices.real(ref.get('price'))} ({ref.get('level')})" if ref else None,
                     "reachability": ps.get("reachability"),
                     "selection_reason": prices.text((r["created"] or {}).get("why")),
                     "plan": {"trade": ps.get("trade"),
                              "entry_zone": {"low": prices.num(z.get("low")), "high": prices.num(z.get("high")),
                                             "text": prices.zone(z.get("low"), z.get("high")), "class": z.get("class")},
                              "reference": {"price": prices.num(ref.get("price")), "text": prices.real(ref.get("price")),
                                            "level": ref.get("level")},
                              "destinations": ({"primary": {"price": prices.num(ps.get("primary")),
                                                            "text": prices.real(ps.get("primary")), "zone": None}}
                                               if ps.get("primary") else {}),
                              "invalidation": [], "invalidation_conditions": []},
                     "created_utc": r["created_utc"]}}


def recommendation(settings: Any, query: str, now: datetime, store: Any = None) -> tuple[int, dict]:
    q = parse_qs(query, max_num_fields=5)
    rid = (q.get("id") or [""])[0]
    if not ID_RE.match(rid):
        return 400, {"ok": False, "error": "id must be a recommendation id (STP-PAIR-YYYYMMDD-HHMM-N)"}
    prices = Prices(settings)
    st = read_state(settings)
    r = next((x for x in recommendations(settings, st) if x["id"] == rid), None)
    if r is None:
        return 404, {"ok": False, "error": "no recommendation with that id"}
    snap = r["snapshot"]
    # what was known at creation: the full snapshot (issued.jsonl) when it was kept, otherwise the summary in the
    # "created" event. Never the live record's later updates, and never anything worked out afterwards.
    at_creation = creation_card(r, prices)
    latest = recommendation_card(r["live_record"], st, prices) if r["live_record"] else None
    timeline = [{"time_utc": e.get("time_utc"), "event": e.get("event"), "label": EVENT_LABEL.get(e.get("event"), str(e.get("event")).upper()),
                 "status": e.get("status"), "why": prices.text(e.get("why"))} for e in sorted(r["events"], key=lambda e: (e.get("time_utc") or "", e["seq"]))]
    stages = {k: next((e["time_utc"] for e in timeline if e["event"] == k), None)
              for k in ("created", "waiting", "active", "completed", "invalidated", "superseded")}
    retro = retrospective(settings, r, at_creation["card"], now, store)
    return 200, {"ok": True, "id": rid, "status": r["status"], "status_label": STATUS_LABEL.get(r["status"], r["status"]),
                 "outcome": r["outcome"], "outcome_reason": prices.text(r["outcome_reason"]), "ended_utc": r["ended_utc"],
                 "at_creation": at_creation, "latest": latest, "timeline": timeline, "stages": stages,
                 "observed_after": retro, "live": r["live"],
                 "overlays_at_creation": structure_levels((snap or {}).get("structural_snapshot"), prices)}


# ---- retrospective evaluation (observed afterwards; no fills, no P&L) -----------------------------------------

class _DayCache:
    """Reads each day's 5-minute file once per request."""

    def __init__(self, store: Any):
        self.store, self.cache = store, {}

    def range(self, start: datetime, end: datetime) -> list:
        key = (start, end)
        if key not in self.cache:
            self.cache[key] = self.store.read_range("5m", start, end)
        return self.cache[key]


def _floor5(t: datetime) -> datetime:
    return t.replace(minute=t.minute - t.minute % 5, second=0, microsecond=0)


def activation_review(settings: Any, r: dict, plan: dict, now: datetime, cache: Any) -> dict:
    """The recorded activation, and the activation confirmed by market evidence from after creation only (owner's
    correction, 18 November 2026). The planner's records are never changed: this is the evaluation's own reading.
    Recorded activations before the correction could rest on the candle finished before creation (the "already in its
    zone?" check) or on the candle running at creation; neither shows price reaching the zone after the recommendation
    existed. The confirmed activation is the first finished 5-minute candle that began at or after creation and reached
    the original zone by the touch rule, before the recorded end."""
    prices = Prices(settings)
    created, ended = _parse(r["created_utc"]), _parse(r["ended_utc"])
    act = next((e for e in r["events"] if e.get("event") == "active"), None)
    out = {"recorded_utc": act.get("time_utc") if act else None, "recorded_candle_start_utc": None,
           "recorded_timing": None, "confirmed_utc": None, "confirmed_candle_start_utc": None, "correction": None}
    if created is None:
        return out
    if act:
        if act.get("candle_timing"):                         # recorded by the planner since the correction
            out["recorded_candle_start_utc"], out["recorded_timing"] = act.get("candle_start_utc"), act["candle_timing"]
        else:                                                # before it: worked out from the event time
            t = _parse(act["time_utc"])
            if t is not None and abs((t - created).total_seconds()) < 1:      # same run as the creation
                start = _floor5(created) - timedelta(minutes=5)          # the creation run's "already in the zone" check
            else:
                start = t - timedelta(minutes=5) if t else None
            if start is not None:
                end = start + timedelta(minutes=5)
                out["recorded_candle_start_utc"] = _iso(start)
                out["recorded_timing"] = ("before creation" if end <= created else
                                          "overlapped creation" if start < created else "after creation")
    if out["recorded_timing"] == "after creation":
        out["confirmed_utc"], out["confirmed_candle_start_utc"] = out["recorded_utc"], out["recorded_candle_start_utc"]
        return out
    z = plan.get("entry_zone") or {}
    low, high = z.get("low"), z.get("high")
    sell = plan.get("trade") == "SELL"
    stop = min(ended or now, now)
    if low is not None and high is not None and cache is not None:
        near = float(settings.rejection.near_level_within_pips) * float(prices.pip)
        side = settings.chart.price
        for c in cache.range(created, stop + timedelta(minutes=5)):
            if c.start < created or c.end > stop:
                continue
            h, lw = float(prices.real(getattr(c, f"{side}_high"))), float(prices.real(getattr(c, f"{side}_low")))
            if (h >= low - near and lw <= high) if sell else (lw <= high + near and h >= low):
                out["confirmed_utc"], out["confirmed_candle_start_utc"] = _iso(c.end), _iso(c.start)
                break
    if act:
        rc = _parse(out["recorded_candle_start_utc"])
        what = (f"recorded ACTIVE at {_hm(_parse(out['recorded_utc']))} UTC from the {_hm(rc)} UTC candle, which "
                f"{'finished before' if out['recorded_timing'] == 'before creation' else 'began before'} the recommendation was "
                f"created ({created.strftime('%H:%M:%S')} UTC)") if rc else "recorded ACTIVE"
        out["correction"] = (what + (f"; first reached after creation by the {_hm(_parse(out['confirmed_candle_start_utc']))} UTC "
                                     f"candle (evaluation uses that)" if out["confirmed_utc"] else
                                     "; no candle after creation reached the zone before it ended, so the evaluation does not "
                                     "count it as activated") + " (retrospective correction; the planner's record is unchanged)")
    return out


def retrospective(settings: Any, r: dict, card_at_creation: dict, now: datetime, store: Any = None, cache: _DayCache | None = None) -> dict:
    """What price did after the recommendation, from finished 5-minute candles (chart price). Excursions are measured
    from the planner's own reference level, in pips: they are distances, not fills or profits."""
    prices = Prices(settings)
    side = settings.chart.price
    created, ended = _parse(r["created_utc"]), _parse(r["ended_utc"])
    plan = card_at_creation.get("plan") or {}
    plan = plan | {"trade": plan.get("trade") or card_at_creation.get("trade")}
    ref = (plan.get("reference") or {}).get("price")
    out: dict = {"label": "observed after creation (retrospective; not a trade, no fills, no P&L)",
                 "minutes_to_zone": None, "minutes_active_to_end": None, "activation": None,
                 "mfe_pips": None, "mae_pips": None, "measured_from": None, "ambiguities": []}
    if created is None:
        return out
    try:
        store = store or _store(settings)
        cache = cache or _DayCache(store)
    except Exception:                                    # noqa: BLE001
        out["note"] = "candles unavailable"
        return out
    review = activation_review(settings, r, plan, now, cache)
    out["activation"] = review
    activated = _parse(review["confirmed_utc"])           # only post-creation evidence counts
    out["minutes_to_zone"] = _mins(created, activated)
    if r["outcome"] == "COMPLETED" and activated and ended and activated <= ended:
        out["minutes_active_to_end"] = _mins(activated, ended)
    if review["correction"]:
        out["ambiguities"].append(review["correction"])
    if activated and ref is not None:
        stop = ended or now
        cs = [c for c in cache.range(activated - timedelta(minutes=5), stop) if c.end <= now]
        if cs:
            highs = [float(prices.real(getattr(c, f"{side}_high"))) for c in cs]
            lows = [float(prices.real(getattr(c, f"{side}_low"))) for c in cs]
            pip = float(prices.pip)
            sell = (card_at_creation.get("trade") or plan.get("trade")) == "SELL"
            fav = (ref - min(lows)) if sell else (max(highs) - ref)
            adv = (max(highs) - ref) if sell else (ref - min(lows))
            out["mfe_pips"] = max(0.0, round(fav / pip, 1))       # a distance: 0 if price never went that way
            out["mae_pips"] = max(0.0, round(adv / pip, 1))
            out["measured_from"] = (f"the reference level {plan['reference'].get('text')} ({plan['reference'].get('level')}), "
                                    f"{_hm(activated - timedelta(minutes=5))} UTC to {_hm(stop)} UTC")
    # issued with price already at the primary destination (the 17 November finding): the last 5-minute candle
    # finished before creation was already within the 3-pip touch allowance of the primary destination
    prim = ((plan.get("destinations") or {}).get("primary") or {}).get("price")
    if prim is not None:
        before = [c for c in cache.range(created - timedelta(minutes=30), created + timedelta(seconds=1)) if c.end <= created]
        if before:
            c = before[-1]
            near = 3 * float(prices.pip)
            sell = (card_at_creation.get("trade") or plan.get("trade")) == "SELL"
            lo_, hi_ = float(prices.real(getattr(c, f"{side}_low"))), float(prices.real(getattr(c, f"{side}_high")))
            if (lo_ <= prim + near) if sell else (hi_ >= prim - near):
                out["issued_at_destination"] = True
                out["ambiguities"].append(f"issued with price already at the primary destination: the {_hm(c.start)} UTC "
                                          f"5-minute candle (finished before creation) reached {lo_ if sell else hi_:.5f}, "
                                          f"within 3 pips of {prim:.5f}")
    # same-candle ambiguity: the deciding candle also touched the zone (or the invalidation side)
    end_ev = next((e for e in r["events"] if e.get("event") in ("completed", "invalidated")), None)
    z = plan.get("entry_zone") or {}
    if end_ev and z.get("low") is not None and end_ev.get("event") in ("completed", "invalidated") \
            and "destination" in str(end_ev.get("why")):
        t = _parse(end_ev["time_utc"])
        c = next((c for c in cache.range(t - timedelta(minutes=5), t + timedelta(minutes=5)) if c.end == t), None)
        if c is not None:
            h, low = float(prices.real(getattr(c, f"{side}_high"))), float(prices.real(getattr(c, f"{side}_low")))
            if low <= z["high"] and h >= z["low"] - 3 * float(prices.pip):
                out["ambiguities"].append("the deciding 5-minute candle touched both the destination and the entry zone: "
                                          "the order within that candle cannot be known from 5-minute candles")
    return out


def _mins(a: datetime | None, b: datetime | None) -> int | None:
    return None if a is None or b is None else int((b - a).total_seconds() // 60)


def evaluation(settings: Any, now: datetime, store: Any = None) -> dict:
    """Forecast evaluation for the observation period: counts from the persisted lifecycle, and distances from
    finished candles. No fills, no spreads, no P&L, no wins or losses."""
    prices = Prices(settings)
    st = read_state(settings)
    events = read_events(settings)
    recs = recommendations(settings, st, events)
    analyses = [e for e in events if e.get("event") == "analysis"]
    start = _parse(analyses[0]["time_utc"]) if analyses else None
    try:
        store = store or _store(settings)
        cache = _DayCache(store)
    except Exception:                                    # noqa: BLE001
        store, cache = None, None
    per = []
    for r in recs:
        card = creation_card(r, prices)["card"]
        retro = retrospective(settings, r, card, now, store, cache) if store is not None else {}
        rechecks = [e for e in r["events"] if e.get("event") in ("supported", "changed")]
        per.append({"id": r["id"], "status": r["status"], "outcome": r["outcome"], "reason": prices.text(r["outcome_reason"]),
                    "ever_active": bool((retro.get("activation") or {}).get("confirmed_utc")) if retro else r["activated_utc"] is not None,
                    "recorded_active": r["activated_utc"] is not None,
                    "activation_corrected": bool((retro.get("activation") or {}).get("correction")),
                    "dest_before_entry": "destination reached before entry" in str(r["outcome_reason"]),
                    "issued_at_destination": bool(retro.get("issued_at_destination")),
                    "supported": sum(e["event"] == "supported" for e in rechecks), "changed": sum(e["event"] == "changed" for e in rechecks),
                    **{k: retro.get(k) for k in ("minutes_to_zone", "minutes_active_to_end", "mfe_pips", "mae_pips", "ambiguities")}})
    n = len(per)
    ended = [x for x in per if x["outcome"]]
    def count(f):
        return sum(1 for x in per if f(x))
    def dist(vals, unit):
        vals = [v for v in vals if v is not None]
        if len(vals) < 3:
            return {"n": len(vals), "values": vals, "median": None, "min": None, "max": None, "unit": unit,
                    "verdict": "INSUFFICIENT DATA"}
        return {"n": len(vals), "values": vals[-50:], "median": statistics.median(vals), "min": min(vals), "max": max(vals),
                "unit": unit, "verdict": None}
    supported = sum(x["supported"] for x in per)
    changed = sum(x["changed"] for x in per)
    superseded = count(lambda x: x["outcome"] == "SUPERSEDED")
    return {"ok": True, "label": "Forecast evaluation (observation only): not trading results, no fills, no P&L",
            "period_start_utc": _iso(start), "period_end_utc": _iso(start + timedelta(weeks=4)) if start else None,
            "as_of_utc": _iso(now), "analyses": len(analyses),
            "analyses_recommending": sum(1 for a in analyses if not (a.get("plan") or {}).get("no_recommendation")),
            "counts": {"total": n, "awaiting_entry": count(lambda x: x["status"] == "WAITING" and not x["outcome"]),
                       "active_now": count(lambda x: x["status"] == "ACTIVE" and not x["outcome"]),
                       "activated": count(lambda x: x["ever_active"]),
                       "activated_as_recorded": count(lambda x: x["recorded_active"]),
                       "activation_corrected": count(lambda x: x["activation_corrected"]),
                       "completed_without_confirmed_activation": count(lambda x: x["outcome"] == "COMPLETED" and not x["ever_active"]),
                       "completed": count(lambda x: x["outcome"] == "COMPLETED"),
                       "invalidated": count(lambda x: x["outcome"] == "INVALIDATED"),
                       "superseded": superseded,
                       "never_reached_zone": count(lambda x: x["outcome"] and not x["ever_active"]),
                       "reached_primary": count(lambda x: x["outcome"] == "COMPLETED" or x["dest_before_entry"]),
                       "reached_primary_after_entry": count(lambda x: x["outcome"] == "COMPLETED" and x["ever_active"]),
                       "destination_before_entry": count(lambda x: x["dest_before_entry"]),
                       "issued_at_destination": count(lambda x: x["issued_at_destination"]),
                       "invalidated_before_primary": count(lambda x: x["outcome"] == "INVALIDATED" and not x["dest_before_entry"])},
            "ended": len(ended),
            "mfe_pips": dist([x["mfe_pips"] for x in per], "pips"),
            "mae_pips": dist([x["mae_pips"] for x in per], "pips"),
            "minutes_to_zone": dist([x["minutes_to_zone"] for x in per], "minutes"),
            "minutes_active_to_primary": dist([x["minutes_active_to_end"] for x in per], "minutes"),
            "stability": {"rechecks": supported + changed, "supported": supported, "changed": changed,
                          "superseded": superseded,
                          "verdict": "INSUFFICIENT DATA" if supported + changed < 3 else None},
            "ambiguous": [{"id": x["id"], "notes": x["ambiguities"]} for x in per if x.get("ambiguities")],
            "per_recommendation": per[-100:],
            "methodology": [
                "Counts come from the planner's own lifecycle events (recommendations.jsonl); nothing is re-decided here.",
                "Reached primary = COMPLETED, plus INVALIDATED with 'destination reached before entry' (the destination was "
                "touched, but before the zone).",
                "Excursions are distances in pips from the planner's reference level, from the 5-minute candle that reached "
                "the zone to the end (or now), on the chart (sell) price. They are not fills and not profits.",
                "Activation counts only market evidence from after creation (owner's correction, 18 November 2026): a "
                "recorded activation from a candle that finished before creation, or began before it, is replaced by the "
                "first later candle that reached the zone; if none did before the end, it is not counted as activated, and "
                "a completion without a confirmed activation is not counted as reached after the zone. The planner's own "
                "records are never changed; each correction is listed below.",
                "Times: creation to the confirmed activation; confirmed activation to COMPLETED.",
                "Stability: each hourly re-check of a live recommendation is 'supported' (unchanged) or 'changed' "
                "(same fixed levels, overlapping zone); a different zone retires it as SUPERSEDED.",
                "Where one 5-minute candle touched both the zone and the destination, the order is ambiguous and is listed.",
                "Fewer than 3 values: INSUFFICIENT DATA."]}
