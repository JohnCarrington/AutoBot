"""Which strategies STP authorises and which filters it replaces for them (owner, 24 November 2026; OD-03, OD-05,
OD-30). No planner import here: with STP_AUTHORISES_ENTRIES off the trading process never imports the planner."""

from __future__ import annotations

from typing import Any


def gated(settings: Any, strategy: str) -> bool:
    """True while STP_AUTHORISES_ENTRIES is on and the strategy is one STP authorises (OD-03)."""
    return bool(getattr(getattr(settings, "switches", None), "stp_authorises_entries", False)) and \
        strategy in tuple(settings.stp_authorisation.strategies)


def bypassed(settings: Any, strategy: str, name: str) -> bool:
    """A filter in stp_authorisation.bypass_filters, for a gated strategy (OD-05, OD-30)."""
    return gated(settings, strategy) and name in tuple(settings.stp_authorisation.bypass_filters)
