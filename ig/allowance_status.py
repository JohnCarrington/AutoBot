"""Read-only look at the history door's files, for the ready checks.

It never asks IG for anything and never changes a file (only the door,
ig/history.py, writes or removes them). The price service uses this, not the
door: the service never uses the history door (a test checks that).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

UTC = timezone.utc
ALLOWANCE_FILE = "ig_allowance.json"
MARKER_FILE = "BLOCKED.json"


def ig_figures(folder: str | Path) -> dict | None:
    """IG's last reported history allowance (remaining, total, resets_utc, seen_utc), or None."""
    p = Path(folder) / ALLOWANCE_FILE
    return json.loads(p.read_text()) if p.exists() else None


def block_reason(folder: str | Path, now: datetime) -> str | None:
    """Why history is blocked, or None. An unreadable marker counts as in place;
    an expired one counts as gone (the door removes it on its next use)."""
    p = Path(folder) / MARKER_FILE
    if not p.exists():
        return None
    try:
        m = json.loads(p.read_text())
        until = datetime.strptime(m["expires_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except Exception:
        return f"a block marker is in place ({p}) and cannot be read; remove it by hand once checked"
    if now >= until:
        return None
    return f"blocked until {m['expires_utc']} ({m.get('reason', '')})"


class HistoryStatus:
    """The same two questions the door answers (ig_figures, block_in_place), read-only."""

    def __init__(self, folder: str | Path, now=lambda: datetime.now(UTC)):
        self.folder, self.now = Path(folder), now

    def ig_figures(self) -> dict | None:
        return ig_figures(self.folder)

    def block_in_place(self) -> str | None:
        return block_reason(self.folder, self.now())
