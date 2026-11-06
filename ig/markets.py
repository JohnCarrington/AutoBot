"""Finding a market's IG epic. One call: GET /markets?searchTerm=...

This is only used to look the epic up once; the epic is then kept in the
settings file (market.epic). The bot does not search for markets while it runs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import quote


@dataclass(frozen=True)
class MarketFound:
    epic: str
    name: str
    instrument_type: str
    expiry: str
    status: str


def search_markets(client: Any, term: str) -> list[MarketFound]:
    """One IG market search call. Returns what IG found."""
    r = client.request("GET", f"/markets?searchTerm={quote(term)}", "1", what="searching markets")
    found = []
    for m in (r.json() or {}).get("markets") or []:
        found.append(MarketFound(
            epic=str(m.get("epic", "")),
            name=str(m.get("instrumentName", "")),
            instrument_type=str(m.get("instrumentType", "")),
            expiry=str(m.get("expiry", "")),
            status=str(m.get("marketStatus", "")),
        ))
    return found
