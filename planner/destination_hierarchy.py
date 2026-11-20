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
    """As-of structural destination hypothesis; NEVER a calibrated probability.

    Direction is determined upstream by confirmed H4 swings. An EMA stack is
    supporting evidence, not a veto: a lagging EMA must not erase an otherwise
    valid directional structure. ADR is a reference, not a maximum move.
    """
    base = target_ladder(price, zones, direction)
    ladder = destination_hierarchy(price, zones, direction)["obstacles"]
    diagnostic = {"zone_count_ahead": len(ladder), "major_count_ahead": 0,
                  "multifamily_major_count": 0, "ema_alignment": "unknown",
                  "adr_remaining_pips": None, "rejections": []}
    if not ladder:
        return dict(base, research_status="no_ahead_zones", diagnostic=diagnostic)
    stack = str(observations.get("h4_ema_stack") or "")
    aligned = ("down" in stack) if direction == "SELL" else ("up" in stack)
    diagnostic["ema_alignment"] = "aligned" if aligned else ("mixed_or_opposed" if stack else "unavailable")
    adr = observations.get("adr_pips")
    used = observations.get("today_range_pips")
    if adr is not None and used is not None:
        adr, used = Decimal(str(adr)), Decimal(str(used))
        if adr.is_finite() and used.is_finite() and adr > 0 and used >= 0:
            diagnostic["adr_remaining_pips"] = str(max(Decimal("0"), adr - used))
        else:
            adr = None
    else:
        adr = None
    # Use families supplied by the structural-zone builder; do not mistake
    # the absence of a separately computed probability for absent structure.
    major = [z for z in ladder if str(z.get("class") or "").lower() == "major"]
    diagnostic["major_count_ahead"] = len(major)
    multifamily = [z for z in major if len(set(z.get("evidence") or [])) >= 2]
    diagnostic["multifamily_major_count"] = len(multifamily)
    if len(ladder) < 2:
        diagnostic["rejections"].append("only one structural obstacle ahead")
    if len(multifamily) < 1:
        diagnostic["rejections"].append("no multi-family Major destination")
    if condition is None:
        diagnostic["rejections"].append("no classified market condition")
    if diagnostic["rejections"]:
        return dict(base, research_status="insufficient_structural_evidence",
                    diagnostic=diagnostic)
    # Candidate must be BEYOND the immediate obstacle, and preferably beyond
    # a meaningful fraction of ADR. Avoid picking the first zone by default.
    first_distance = Decimal(ladder[0]["distance_pips"])
    candidates = [z for z in multifamily
                  if Decimal(z["distance_pips"]) > first_distance]
    if not candidates:
        diagnostic["rejections"].append("no deeper multi-family Major zone")
        return dict(base, research_status="no_deeper_major", diagnostic=diagnostic)
    # ADR describes typical movement, not a structural-zone discovery boundary.
    # Preserve a deeper Major destination as an explicit multi-session hypothesis
    # even when it is farther than 1.5 ADR. Do not imply it will be reached today.
    feasible = candidates
    # Select the nearest deeper Major destination as the preferred hypothesis.
    # More distant zones remain conditional extensions, not today's prediction.
    preferred = feasible[0]
    further = [z for z in multifamily if Decimal(z["distance_pips"]) >
               Decimal(preferred["distance_pips"])]
    extension = further[0] if further else None
    def hypothesis(z, why):
        return dict(z, rationale=why, status="uncalibrated_research_hypothesis")
    diagnostic["selected_distance_pips"] = preferred["distance_pips"]
    diagnostic["candidate_count"] = len(feasible)
    return dict(base,
        preferred=hypothesis(preferred, "confirmed H4 structural direction; next deeper multi-family Major zone; timeframe uncalibrated"),
        extended=(hypothesis(extension, "conditional continuation beyond preferred structural destination")
                  if extension else None),
        intermediate_obstacles=[z for z in ladder if
            Decimal(z["distance_pips"]) < Decimal(preferred["distance_pips"])],
        preferred_selection_status="uncalibrated_research_hypothesis",
        research_status="candidate_generated", diagnostic=diagnostic,
        evidence=["confirmed structural direction", "multi-family Major destination",
                  "EMA alignment: " + diagnostic["ema_alignment"],
                  "ADR is contextual, not a hard veto"],
        execution_authorised=False)
