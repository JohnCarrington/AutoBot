"""What the dashboard's planner panel shows (design section 14; D-28). Built from the planner's own file
(planner.folder/<PAIR>/current.json); reads nothing else and changes nothing. Observations (what the market is doing)
are kept apart from the forecast (what the planner expects) and the recommendation (the structural opportunity).
Always labelled OBSERVE ONLY - DOES NOT CONTROL TRADING.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

LABEL = "OBSERVE ONLY — DOES NOT CONTROL TRADING"


def read_state(settings: Any) -> dict | None:
    try:
        st = json.loads((Path(settings.planner.folder) / settings.market.pair / "current.json").read_text())
        return st if isinstance(st, dict) else None
    except (FileNotFoundError, ValueError, OSError):
        return None


def panel(settings: Any, now: datetime) -> dict:
    st = read_state(settings)
    if st is None:
        return {"label": LABEL, "available": False,
                "message": "The planner has not written a forecast (it is off, or has not run yet)."}
    p = st.get("last_plan") or {}
    rec = st.get("recommendation")
    o = p.get("observations") or {}
    out: dict = {"label": LABEL, "available": True, "last_analysis_utc": st.get("last_analysis_utc"),
                 "last_run_utc": st.get("last_run_utc"), "data_fresh": st.get("data_fresh"),
                 "current": st.get("current"), "not_current_reasons": st.get("not_current_reasons", [])}
    out["observed"] = {
        "h4_structure": (p.get("direction_evidence") or [None])[0],
        "h4_macd": o.get("h4_macd"), "h4_rsi": o.get("h4_rsi"), "h4_band": (o.get("h4_band") or {}).get("close"),
        "ema_stack": o.get("h4_ema_stack"), "ema100_slope_pips": o.get("h4_ema100_slope_pips"),
        "adr_pips": o.get("adr_pips"), "today_range_pips": o.get("today_range_pips"), "today_range_adr": o.get("today_range_adr"),
        "vs_daily_pivot": o.get("vs_daily_pivot"), "vs_weekly_pivot": o.get("vs_weekly_pivot"),
        "daily_structure": o.get("daily_structure"),
        "direction_rule_5m": (o.get("direction_rule_5m") or {}).get("side"),
        "big_news_today": o.get("big_news_today"), "warming_up": p.get("warming_up", []),
    }
    out["forecast"] = {"dominant_direction": p.get("dominant_direction"), "condition": p.get("condition"),
                       "expected_movement": p.get("expected_movement"), "opportunity": p.get("opportunity"),
                       "condition_evidence": p.get("condition_evidence", [])}
    if rec is not None:
        z, d = rec["entry_zone"], rec["destinations"]
        out["recommendation"] = {
            "id": rec["id"], "status": rec["status"], "status_reason": rec.get("status_reason"), "trade": rec["trade"],
            "zone": f"{z['low']}–{z['high']}", "class": z["class"], "families": z["families"],
            "evidence": [f"{m['name']} {m['price']}" + (f" ({m['role']})" if m.get("role") else "") for m in z["levels"]],
            "reference_entry": rec["reference_entry"], "reachability": rec.get("reachability"),
            "why": rec.get("selection_reason"),
            "next_obstacle": (d.get("intermediate") or {}).get("price"),
            "primary_destination": (d.get("primary") or {}).get("price"),
            "extended_destination": (d.get("extended") or {}).get("price"),
            "created_utc": rec["created_utc"]}
        out["invalidation"] = rec["invalidation"]["conditions"]
    else:
        out["recommendation"] = None
        out["no_recommendation"] = p.get("no_recommendation") or "no recommendation"
        out["invalidation"] = []
    out["recent"] = st.get("recent", [])[: settings.planner.panel_history]
    return out
