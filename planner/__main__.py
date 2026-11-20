"""The Structural Trade Planner from the command line (OBSERVE ONLY; never contacts IG, never touches a trade).

    .venv/bin/python -m planner run  [--pair GBPUSD]            one keeper run now: what the price service starts after
                                                               each new 5-minute candle while PLANNER_OBSERVE is on
                                                               (writes planner.folder/<PAIR>/ only)
    .venv/bin/python -m planner show [--pair GBPUSD] [--at 2026-11-17T07:32:00Z]
                                                               the plan at a moment, printed; writes nothing
    .venv/bin/python -m planner technical [--pair GBPUSD] [--at 2026-11-20T09:00:05Z]
                                                               the technical forecast (planner/technical.py, issue #3)
                                                               at a moment, printed; writes nothing

Only one run at a time: a run that finds another still going leaves at once (a lock file in planner.folder/<PAIR>/).
"""

from __future__ import annotations

import argparse
import fcntl
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from config.settings_loader import load_settings
from prices.model import parse_iso

UTC = timezone.utc
log = logging.getLogger("autobot.planner")


def describe(p: dict) -> list[str]:
    """The plan in words, for a person."""
    out = ["STRUCTURAL TRADE PLANNER - " + p["pair"] + "   (OBSERVE ONLY - DOES NOT CONTROL TRADING)",
           f"as at {p['as_of_utc']}; data to {p['market_data_utc']} ({'fresh' if p['fresh'] else 'NOT fresh'})", "",
           f"Dominant direction:  {p['dominant_direction']}"]
    out += [f"   - {e}" for e in p["direction_evidence"]]
    out += [f"Condition:           {p['condition']}"] + [f"   - {e}" for e in p["condition_evidence"]]
    if p["no_recommendation"]:
        out += ["", f"NO RECOMMENDATION: {p['no_recommendation']}"]
    else:
        z, d = p["entry_zone"], p["destinations"]
        out += ["", f"Opportunity:         {p['opportunity']}", f"Preferred trade:     {p['trade']}",
                f"Expected movement:   {p['expected_movement']}",
                f"Entry zone:          {z['low']}-{z['high']} ({z['class']}; families: {', '.join(z['families'])}; tests {z['tests']})"]
        out += [f"   - {m['name']} {m['price']}" + (f" ({m['role']})" if m.get("role") else "") for m in z["levels"]]
        out += [f"Reference entry:     {p['reference_entry']['price']} ({p['reference_entry']['level']})",
                f"Reachability:        {p['reachability']}", f"Why this zone:       {p['selection_reason']}",
                f"Destinations:        intermediate {d['intermediate']['price']}, primary {d['primary']['price']}, "
                f"extended {d['extended']['price'] if d['extended'] else '-'}",
                "Invalidation:"] + [f"   - {c}" for c in p["invalidation"]["conditions"]]
    if p["warming_up"]:
        out += ["", "Warming up (not used): " + "; ".join(p["warming_up"])]
    for m in p["threshold_misses"]:
        out.append("Threshold note: " + m["note"])
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="planner")
    ap.add_argument("what", choices=("run", "show", "technical"))
    ap.add_argument("--pair", default="GBPUSD")
    ap.add_argument("--at", default=None)
    a = ap.parse_args(argv)
    settings = load_settings().for_pair(a.pair)
    from prices.store import CandleStore
    store = CandleStore(settings.candles.folder, settings.candles.compress_after_days)
    if a.what == "show":
        from planner.assess import plan_at
        at = parse_iso(a.at) if a.at else datetime.now(UTC)
        print("\n".join(describe(plan_at(settings, store, at).as_dict())))
        return 0
    if a.what == "technical":
        from planner import technical
        at = parse_iso(a.at) if a.at else datetime.now(UTC)
        print("\n".join(technical.describe(technical.technical_at(settings, store, at))))
        return 0
    from housekeeping.logs import setup_logging
    from planner.keeper import Keeper
    setup_logging(settings.housekeeping, "planner", console=False)
    folder = Path(settings.planner.folder) / settings.market.pair
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / ".lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            log.info("Planner: another run is still going; this one leaves.")
            return 0
        try:
            Keeper(settings, store).run(datetime.now(UTC))
        except Exception:                               # noqa: BLE001  logged; trading is never affected
            log.exception("Planner run failed; the previous planner files are kept. Trading is not affected.")
            return 1
        try:                                            # observe only, after the keeper, never part of its lifecycle
            from planner import technical
            technical.write(settings, store, datetime.now(UTC))
        except Exception:                               # noqa: BLE001
            log.exception("Technical forecast failed; the recommendation files are unaffected. Trading is not affected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
