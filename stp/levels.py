"""The live STP zones as levels in the STRATEGIES' copy of the level list (OD-22, OD-26; design section 8), only while
STP_AUTHORISES_ENTRIES is on. The analyser's level list, its watcher, the trade manager and the dashboard never see
them. For each opportunity that authorises (WAITING or Watch & Wait): its zone's two edges and the fixed levels STP
lists inside the zone, each unless the same price is already a bot level. Each zone's levels are one group of their
own, not "lined up", so the watcher's "counts" mark for the trade manager is unchanged. A level is a place for the
strategies to look, never an authorisation: every idea still goes through stp/authorise.py."""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Any

from levels.current import LevelList
from levels.rules import Level

STP_ZONE = "stp_zone"
AUTHORISING = ("WAITING", "ACTIVE")


@dataclass(frozen=True)
class StpLevel(Level):
    zone_low: Decimal = Decimal(0)
    zone_high: Decimal = Decimal(0)
    opportunities: tuple = ()


def live(state: dict | None) -> list[dict]:
    return [o for o in ((state or {}).get("opportunities") or []) if o.get("status") in AUTHORISING]


def with_stp(base: LevelList, state: dict | None) -> LevelList:
    opps = live(state)
    if not opps:
        return base
    taken = {lv.price for lv in base.levels}
    levels, groups = list(base.levels), list(base.groups)
    by_zone: dict[tuple, list] = {}
    for o in opps:
        z = o["entry_zone"]
        lo, hi = Decimal(str(z["low"])), Decimal(str(z["high"]))
        by_zone.setdefault((lo, hi), []).append(o)
    for (lo, hi), os_ in sorted(by_zone.items()):
        prices = {lo, hi}
        for o in os_:
            for m in o["entry_zone"].get("levels", []):
                p = Decimal(str(m["price"]))
                if m.get("fixed") and lo <= p <= hi:
                    prices.add(p)
        prices = sorted(p for p in prices if p not in taken)
        if not prices:
            continue
        g = len(groups) + 1
        ids = tuple(o["id"] for o in os_)
        src = f"STP zone {lo}-{hi} ({', '.join(f'{o['trade']} {o['id']}' for o in os_)})"
        members = [StpLevel(p, STP_ZONE, src, None, False, g, lo, hi, ids) for p in prices]
        groups.append({"group": g, "low": prices[0], "high": prices[-1], "members": members, "important": False,
                       "lined_up": False, "stp": True})
        levels += members
        taken.update(prices)
    return replace(base, levels=levels, groups=groups)
