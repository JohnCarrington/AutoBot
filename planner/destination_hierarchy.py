"""Experimental destination hierarchy, isolated from production STP decisions.

A structural level is an obstacle, not automatically a forecast endpoint.
This module ranks *eligible* levels and makes no probability claim. It is
intended for offline walk-forward comparison before changing plan_at.
"""
from __future__ import annotations

from decimal import Decimal


def destination_hierarchy(price, zones, direction, *, minimum_reward_pips=Decimal("0")):
    """Return ordered structural obstacles and an unconfirmed forecast candidate.

    Zones: mappings with low, high, class, optionally evidence and probability.
    Values are IG points (one point = one GBPUSD pip). No future prices accepted.
    No destination is promoted to a *forecast* without independently supplied,
    calibrated evidence; Major status alone is insufficient.
    """
    if direction not in ("BUY", "SELL"):
        return {"obstacles": [], "forecast": None, "reason": "no directional thesis"}
    p = Decimal(str(price))
    minimum = Decimal(str(minimum_reward_pips))
    ordered = []
    for z in zones:
        lo, hi = Decimal(str(z["low"])), Decimal(str(z["high"]))
        if lo > hi:
            raise ValueError("inverted zone")
        distance = p - hi if direction == "SELL" else lo - p
        if distance <= 0:
            continue
        ordered.append({
            "low": str(lo), "high": str(hi), "class": z.get("class"),
            "distance_pips": str(distance),
            "evidence": z.get("evidence"),
            "forecast_probability": z.get("forecast_probability"),
        })
    ordered.sort(key=lambda z: Decimal(z["distance_pips"]))
    # Do not manufacture a long-range destination from the list of obstacles.
    # A calibrated forecast model must explicitly supply the probability.
    eligible = [z for z in ordered if
                Decimal(z["distance_pips"]) >= minimum and
                z["forecast_probability"] is not None]
    return {
        "obstacles": ordered,
        "forecast": max(eligible, key=lambda z: (
            Decimal(str(z["forecast_probability"])),
            Decimal(z["distance_pips"]))) if eligible else None,
        "reason": ("independent probability supplied; verify calibration before use"
                   if eligible else
                   "structural levels alone do not establish a likely destination"),
    }
