"""Deterministic fixtures for the Structural Trade Planner tab's tests (dashboard/stp.py, the STP tab). Every lifecycle
here is made by the real planner keeper (planner/keeper.py) driven by a scripted planner and an in-memory candle store,
exactly as the planner's own tests do, so the files the dashboard reads are genuine keeper output. Never touches the
real planner folder, the real candle store or IG."""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

from planner.keeper import Keeper
from tests.planner_helpers import Over, section
from tests.technical.test_planner import NOW, C, S as PS, Script, T, flat_store, plan_dict  # noqa: F401

__all__ = ["NOW", "C", "T", "Script", "flat_store", "plan_dict", "settings", "keeper", "Scenario", "SCENARIOS", "write_status"]


def settings(tmp: Path, observe: bool = True) -> Over:
    return Over(PS, planner=section(PS.planner, folder=tmp / "planner"),
                dashboard=section(PS.dashboard, status_folder=tmp / "status"),
                trading=section(PS.trading, pause_file=tmp / "control" / "pause_new_trades"),
                switches=SimpleNamespace(planner_observe=observe))


def keeper(s, store, *plans) -> Keeper:
    return Keeper(s, store, planner=Script(*plans))


def write_status(s, bid="13201.8", offer="13203.0", t="2026-11-17T09:00:00Z") -> None:
    f = Path(s.dashboard.status_folder) / "GBPUSD" / "status.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"generated_utc": t, "price": {"bid": bid, "offer": offer, "time_utc": t}, "pair": "GBPUSD"}))


class Scenario:
    """Builds one planner folder; .store is the candle store that went with it, .now the moment after the last run."""

    def __init__(self, tmp: Path):
        self.s = settings(tmp)
        self.store = flat_store(NOW)
        self.now = NOW

    def run(self, at, plans, extra5=(), extra1=(), price=13200):
        for p in plans:                                  # as the real planner: the analysis time and data time
            p["as_of_utc"] = at.strftime("%Y-%m-%dT%H:%M:%SZ")
            p["market_data_utc"] = at.replace(minute=at.minute - at.minute % 5, second=0).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.store = flat_store(at, price=price, extra5=extra5, extra1=extra1)
        k = keeper(self.s, self.store, *plans)
        k.run(at)
        self.now = at
        return k


TOUCH = lambda t: C("5m", t, 1 / 12, 13230, 13238, 13229, 13231)          # noqa: E731  within 3 pips of 13240
DEST = lambda t: C("5m", t, 1 / 12, 13180, 13181, 13172, 13175)          # noqa: E731  within 3 pips of 13170


def waiting(tmp):
    sc = Scenario(tmp)
    sc.run(NOW, [plan_dict()])
    return sc


def active(tmp):
    sc = waiting(tmp)
    t1 = NOW + timedelta(minutes=5)
    sc.run(t1, [plan_dict()], extra5=[TOUCH(NOW)])
    return sc


def completed(tmp):
    sc = active(tmp)
    t2 = NOW + timedelta(minutes=10)
    sc.run(t2, [plan_dict()], extra5=[TOUCH(NOW), DEST(NOW + timedelta(minutes=5))])
    return sc


def destination_first(tmp):
    sc = waiting(tmp)
    t1 = NOW + timedelta(minutes=5)
    sc.run(t1, [plan_dict()], extra5=[DEST(NOW)])
    return sc


def invalidated_break(tmp):
    sc = waiting(tmp)
    t = NOW + timedelta(hours=1, minutes=1)
    sc.run(t, [plan_dict()], extra1=[C("1h", NOW, 1, 13245, 13258, 13244, 13256)])
    return sc


def superseded(tmp):
    sc = waiting(tmp)
    t = NOW + timedelta(hours=1, minutes=1)
    sc.run(t, [plan_dict(zone=(13280, 13290), levels=[("daily R3", "13284", True)])])
    return sc


def identical_zones(tmp):
    """The 17 November shape: one completes, the next hourly analysis issues the same zone again under a new id."""
    sc = completed(tmp)
    t = NOW + timedelta(hours=1, minutes=1)
    sc.run(t, [plan_dict()], extra5=[TOUCH(NOW), DEST(NOW + timedelta(minutes=5))])
    return sc


def continued(tmp):
    sc = waiting(tmp)
    for h in (1, 2):
        sc.run(NOW + timedelta(hours=h, minutes=1), [plan_dict(moving=13238 - h)])
    return sc


def no_rec_directional(tmp):
    sc = Scenario(tmp)
    sc.run(NOW, [plan_dict(no_rec="no defensible entry zone: no resistance zone of at least Moderate class that is NEAR "
                                  "or PLAUSIBLE before the last 4-hour swing high 13300")])
    return sc


def no_rec_indeterminate(tmp):
    sc = Scenario(tmp)
    p = plan_dict(direction="NEUTRAL", no_rec="the 4-hour direction is NEUTRAL: no recommendation until it is BEARISH or BULLISH")
    p.update(trade=None, opportunity=None, expected_movement=None, condition="INDETERMINATE", entry_zone=None)
    sc.run(NOW, [p])
    return sc


def bullish(tmp):
    sc = Scenario(tmp)
    sc.run(NOW, [plan_dict(trade="BUY", zone=(13150, 13160), primary=13230)])
    return sc


def stale(tmp):
    sc = waiting(tmp)
    late = NOW + timedelta(hours=3)                      # no candles after NOW: the planner's own rule says not fresh
    k = keeper(sc.s, flat_store(NOW), plan_dict())
    k.run(late)
    sc.now = late
    return sc


SCENARIOS = {"waiting": waiting, "active": active, "completed": completed, "destination_first": destination_first,
             "invalidated_break": invalidated_break, "superseded": superseded, "identical_zones": identical_zones,
             "continued": continued, "no_rec_directional": no_rec_directional, "no_rec_indeterminate": no_rec_indeterminate,
             "bullish": bullish, "stale": stale}
