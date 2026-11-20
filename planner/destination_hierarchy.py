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
    eligible = []
    for z in ordered:
        probability = z["forecast_probability"]
        if probability is None:
            continue
        probability = Decimal(str(probability))
        if not probability.is_finite() or not Decimal("0") <= probability <= Decimal("1"):
            raise ValueError("forecast_probability must be finite and between 0 and 1")
        if Decimal(z["distance_pips"]) >= minimum:
            eligible.append(z)
    return {
        "obstacles": ordered,
        "forecast": max(eligible, key=lambda z: (
            Decimal(str(z["forecast_probability"])),
            Decimal(z["distance_pips"]))) if eligible else None,
        "reason": ("independent probability supplied; verify calibration before use"
                   if eligible else
                   "structural levels alone do not establish a likely destination"),
    }


def target_ladder(price, zones, direction, *, preferred=None, extended=None):
    """Three-tier *research* destination model, no implied probability.

    Immediate = nearest untouched structural obstacle.
    Preferred/extended require independently justified, explicit zone selection.
    Passing a zone identifier is a scenario hypothesis, not a calibrated forecast.
    All levels are expressed in IG points and must be ahead of the as-of price.
    """
    hierarchy = destination_hierarchy(price, zones, direction)
    obstacles = hierarchy["obstacles"]
    immediate = obstacles[0] if obstacles else None

    def resolve(choice, label):
        if choice is None:
            return None
        if not isinstance(choice, dict) or not choice.get("rationale"):
            raise ValueError(label + " requires an explicit evidence rationale")
        matches = [o for o in obstacles
                   if o["low"] == str(Decimal(str(choice["low"])))
                   and o["high"] == str(Decimal(str(choice["high"])))]
        if len(matches) != 1:
            raise ValueError(label + " must match one ahead-of-price structural zone")
        return dict(matches[0], rationale=choice["rationale"],
                    status="hypothesis_not_calibrated")

    primary = resolve(preferred, "preferred")
    extension = resolve(extended, "extended")
    if primary and immediate and Decimal(primary["distance_pips"]) < Decimal(immediate["distance_pips"]):
        raise ValueError("preferred must not precede immediate")
    if extension and not primary:
        raise ValueError("extended requires a preferred target")
    if extension and Decimal(extension["distance_pips"]) <= Decimal(primary["distance_pips"]):
        raise ValueError("extended must be beyond preferred")
    return {
        "immediate": immediate,
        "preferred": primary,
        "extended": extension,
        "intermediate_obstacles": [
            o for o in obstacles
            if primary is not None and Decimal(o["distance_pips"]) < Decimal(primary["distance_pips"])
        ],
        "preferred_selection_status": (
            "explicit_unvalidated_hypothesis" if primary else "not_established"
        ),
        "execution_authorised": False,
    }


def research_target_forecast(price, zones, direction, observations, *, condition=None):
    """As-of, uncalibrated destination hypothesis for walk-forward evaluation.

    Uses only contemporaneous ADR/range, H4 EMA stack and structural confluence.
    Does NOT assert a likelihood or override execution/legacy destinations.
    """
    base = target_ladder(price, zones, direction)
    obstacles = base["immediate"]
    ladder = destination_hierarchy(price, zones, direction)["obstacles"]
    if not ladder:
        return dict(base, research_status="no_ahead_zones", evidence=[])
    adr = observations.get("adr_pips")
    used = observations.get("today_range_pips")
    if adr is None or used is None:
        return dict(base, research_status="insufficient_as_of_adr", evidence=[])
    adr, used = Decimal(str(adr)), Decimal(str(used))
    if adr <= 0 or used < 0:
        return dict(base, research_status="invalid_as_of_adr", evidence=[])
    # ADR is a *soft* feasibility reference, not a hard ceiling on trend days.
    room = max(Decimal("0"), adr - used)
    stack = observations.get("h4_ema_stack", "")
    aligned = ("down" in stack) if direction == "SELL" else ("up" in stack)
    if not aligned:
        return dict(base, research_status="directional_momentum_not_confirmed",
                    evidence=["H4 EMA 7/13/21 stack does not align with directional thesis"])
    if condition not in ("CONTINUATION", "CONTINUATION_CONFIRMED", "CORRECTION_ACTIVE",
                         "CORRECTION_LIKELY", "EMERGING_TREND", "STRONG_TREND"):
        return dict(base, research_status="condition_not_confirmed", evidence=[])
    # Conservative feasibility gate: the hypothesis cannot assume an extension
    # exceeding remaining normal daily range. Evaluate its missed-trend rate offline.
    feasible = [z for z in ladder if Decimal(z["distance_pips"]) <= room]
    if len(feasible) < 2:
        return dict(base, research_status="no_supported_beyond_immediate", evidence=[
            "normal ADR remaining does not support a deeper target"])
    # Among feasible destinations prefer the farthest multi-family Major zone;
    # intermediate levels remain obstacles rather than automatic final targets.
    ranked = [z for z in feasible[1:] if str(z["class"]).lower() == "major"
              and len(z.get("evidence") or []) >= 2]
    if not ranked:
        return dict(base, research_status="no_multifamily_preferred", evidence=[])
    preferred = ranked[-1]
    extension = next((z for z in ladder if Decimal(z["distance_pips"]) >
                      Decimal(preferred["distance_pips"]) and
                      str(z["class"]).lower() == "major"), None)
    def hypothesis(z, rationale):
        return dict(z, rationale=rationale, status="uncalibrated_research_hypothesis")
    return dict(base,
        preferred=hypothesis(preferred, "H4 EMA aligned; multi-family Major zone; within remaining ADR"),
        extended=(hypothesis(extension, "conditional extension beyond ADR feasibility")
                  if extension else None),
        intermediate_obstacles=[z for z in ladder
            if Decimal(z["distance_pips"]) < Decimal(preferred["distance_pips"])],
        preferred_selection_status="uncalibrated_research_hypothesis",
        research_status="candidate_generated",
        evidence=["H4 EMA stack aligned", "multi-family Major structural confluence",
                  "remaining ADR feasibility"],
        adr_remaining_pips=str(room),
        execution_authorised=False)
